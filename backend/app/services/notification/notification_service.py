"""Core Notification Service handling multi-channel dispatch, preferences, deduplication, and admin broadcasts."""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditLog
from backend.app.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationPreference,
    NotificationType,
)
from backend.app.models.payment import PremiumEntitlement
from backend.app.models.user import User, UserRole
from backend.app.schemas.notification import (
    AdminBroadcastRequest,
    AdminBroadcastResponse,
    NotificationItem,
    NotificationListResponse,
    NotificationPreferenceItem,
    NotificationPreferencesResponse,
    UpdateNotificationPreferencesRequest,
)
from backend.app.services.notification.email_provider import get_email_provider

logger = logging.getLogger(__name__)


class NotificationService:
    """Orchestrates in-app and email delivery with preference filtering and delivery audits."""

    _TYPE_TO_FIELD = {
        NotificationType.DAILY_CHALLENGE: "daily_challenge",
        NotificationType.STREAK_REMINDER: "streak_reminders",
        NotificationType.REVISION_DUE: "revision_reminders",
        NotificationType.CONTEST_STARTING: "contest_notifications",
        NotificationType.CONTEST_RESULT: "contest_notifications",
        NotificationType.ACHIEVEMENT_UNLOCKED: "achievement_notifications",
        NotificationType.SYSTEM_NOTICE: "system_notifications",
        NotificationType.INTERVIEW_RESULT: "system_notifications",
        NotificationType.PREMIUM_EXPIRING: "system_notifications",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # PREFERENCES
    # =========================================================================

    async def get_or_create_user_preferences(
        self, user_id: str
    ) -> NotificationPreference:
        """Ensures a preferences entity exists for the user."""
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        res = await self.db.execute(stmt)
        pref = res.scalars().first()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            self.db.add(pref)
            await self.db.commit()
            await self.db.refresh(pref)
        return pref

    async def get_user_preferences(
        self, user_id: str
    ) -> NotificationPreferencesResponse:
        """Retrieves user channel/type preferences as a structured matrix."""
        pref = await self.get_or_create_user_preferences(user_id)
        preferences: list[NotificationPreferenceItem] = []

        for ch in NotificationChannel:
            ch_active = (
                pref.in_app_enabled
                if ch == NotificationChannel.IN_APP
                else pref.email_enabled
            )
            for nt in NotificationType:
                attr_name = self._TYPE_TO_FIELD.get(nt, "system_notifications")
                cat_active = getattr(pref, attr_name, True)
                preferences.append(
                    NotificationPreferenceItem(
                        channel=ch,
                        notification_type=nt,
                        is_enabled=bool(ch_active and cat_active),
                    )
                )

        return NotificationPreferencesResponse(preferences=preferences)

    async def update_user_preferences(
        self, user_id: str, request: UpdateNotificationPreferencesRequest
    ) -> NotificationPreferencesResponse:
        """Bulk updates user notification preference toggles."""
        pref = await self.get_or_create_user_preferences(user_id)
        for item in request.preferences:
            attr_name = self._TYPE_TO_FIELD.get(
                item.notification_type, "system_notifications"
            )
            if hasattr(pref, attr_name):
                setattr(pref, attr_name, item.is_enabled)
        pref.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return await self.get_user_preferences(user_id)

    async def is_channel_enabled_for_user(
        self, user_id: str, channel: NotificationChannel, ntype: NotificationType
    ) -> bool:
        """Helper checking if a user has opted into a specific channel and type."""
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        res = await self.db.execute(stmt)
        pref = res.scalars().first()
        if not pref:
            return True
        ch_active = (
            pref.in_app_enabled
            if channel == NotificationChannel.IN_APP
            else pref.email_enabled
        )
        attr_name = self._TYPE_TO_FIELD.get(ntype, "system_notifications")
        cat_active = getattr(pref, attr_name, True)
        return bool(ch_active and cat_active)

    # =========================================================================
    # DISPATCH & CREATION
    # =========================================================================

    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        data_json: str | None = None,
        deduplication_key: str | None = None,
        channels: list[NotificationChannel] | None = None,
    ) -> Notification | None:
        """Creates and dispatches an event notification according to user channel preferences."""
        if channels is None:
            channels = [NotificationChannel.IN_APP]

        # Enforce deduplication if provided
        if deduplication_key:
            dup_stmt = select(Notification).where(
                Notification.user_id == user_id,
                Notification.metadata_json.like(f'%"{deduplication_key}"%'),
            )
            dup_res = await self.db.execute(dup_stmt)
            existing = dup_res.scalars().first()
            if existing:
                logger.info(
                    f"Notification with deduplication_key '{deduplication_key}' already exists. Skipping."
                )
                return existing

        in_app_enabled = await self.is_channel_enabled_for_user(
            user_id, NotificationChannel.IN_APP, notification_type
        )
        email_enabled = await self.is_channel_enabled_for_user(
            user_id, NotificationChannel.EMAIL, notification_type
        )

        notif = None
        # In-App Creation
        if NotificationChannel.IN_APP in channels and in_app_enabled:
            notif = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                body=body,
                data_json=data_json,
                deduplication_key=deduplication_key,
                is_read=False,
            )
            self.db.add(notif)
            await self.db.flush()

            # Record In-App delivery
            in_app_delivery = NotificationDelivery(
                notification_id=notif.id,
                channel=NotificationChannel.IN_APP,
                status=DeliveryStatus.SENT,
                sent_at=datetime.now(timezone.utc),
            )
            self.db.add(in_app_delivery)

        # Email Delivery
        if NotificationChannel.EMAIL in channels and email_enabled:
            # Need recipient email
            user_stmt = select(User).where(User.id == user_id)
            user_res = await self.db.execute(user_stmt)
            user = user_res.scalars().first()

            if user and user.email:
                provider = get_email_provider()
                try:
                    success = await provider.send_email(
                        to_email=user.email,
                        subject=title,
                        html_body=f"<h3>{title}</h3><p>{body}</p>",
                        text_body=body,
                    )
                    status_val = (
                        DeliveryStatus.SENT if success else DeliveryStatus.FAILED
                    )
                    err_msg = None if success else "Email provider rejected delivery"
                except Exception as e:
                    logger.error(f"Error sending email to {user.email}: {e}")
                    status_val = DeliveryStatus.FAILED
                    err_msg = str(e)

                if notif:
                    email_delivery = NotificationDelivery(
                        notification_id=notif.id,
                        channel=NotificationChannel.EMAIL,
                        status=status_val,
                        error_message=err_msg,
                        sent_at=datetime.now(timezone.utc)
                        if status_val == DeliveryStatus.SENT
                        else None,
                    )
                    self.db.add(email_delivery)

        await self.db.commit()
        if notif:
            await self.db.refresh(notif)
        return notif

    # =========================================================================
    # USER NOTIFICATION ACCESS & MUTATIONS
    # =========================================================================

    async def list_user_notifications(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> NotificationListResponse:
        """Paginated list of user notifications with unread counter."""
        base_query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            base_query = base_query.where(Notification.is_read.is_(False))

        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Unread count
        unread_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        unread_count = (await self.db.execute(unread_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        items_stmt = (
            base_query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        res = await self.db.execute(items_stmt)
        notifications = res.scalars().all()

        items = [
            NotificationItem(
                id=n.id,
                user_id=n.user_id,
                type=n.type,
                title=n.title,
                body=n.body,
                data_json=n.data_json,
                is_read=n.is_read,
                read_at=n.read_at,
                created_at=n.created_at,
            )
            for n in notifications
        ]

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return NotificationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            unread_count=unread_count,
        )

    async def get_unread_count(self, user_id: str) -> int:
        """Returns total unread notifications for navigation badge."""
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    async def mark_as_read(
        self, user_id: str, notification_id: str
    ) -> NotificationItem:
        """Marks a specific notification as read with ownership verification."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        notif = res.scalars().first()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )

        if not notif.is_read:
            notif.is_read = True
            await self.db.commit()
            await self.db.refresh(notif)

        return NotificationItem(
            id=notif.id,
            user_id=notif.user_id,
            type=notif.type,
            title=notif.title,
            body=notif.body,
            data_json=notif.data_json,
            is_read=notif.is_read,
            read_at=notif.read_at,
            created_at=notif.created_at,
        )

    async def mark_all_as_read(self, user_id: str) -> int:
        """Marks all unread notifications for a user as read."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(read_at=now)
        )
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount

    # =========================================================================
    # ADMIN BROADCAST
    # =========================================================================

    async def broadcast_notification(
        self,
        admin_user: User,
        request: AdminBroadcastRequest,
        ip_address: str | None = None,
    ) -> AdminBroadcastResponse:
        """Sends an administrative announcement to targeted active learners."""
        broadcast_id = str(uuid.uuid4())

        # Select candidate active users
        user_query = select(User).where(User.is_active.is_(True))

        if request.target_role:
            try:
                target_role_enum = UserRole(request.target_role.upper())
                user_query = user_query.where(User.role == target_role_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid target role: {request.target_role}",
                )

        u_res = await self.db.execute(user_query)
        candidates = u_res.scalars().all()

        recipients: list[User] = []
        now = datetime.now(timezone.utc)

        if request.target_plan:
            plan_upper = request.target_plan.upper()
            cand_ids = [c.id for c in candidates]
            if cand_ids:
                prem_stmt = select(PremiumEntitlement.user_id).where(
                    PremiumEntitlement.user_id.in_(cand_ids),
                    PremiumEntitlement.is_active.is_(True),
                    PremiumEntitlement.expires_at > now,
                )
                prem_res = await self.db.execute(prem_stmt)
                prem_ids = {row[0] for row in prem_res.all()}

                for c in candidates:
                    is_prem = c.id in prem_ids
                    if (plan_upper == "PREMIUM" and is_prem) or (
                        plan_upper == "FREE" and not is_prem
                    ):
                        recipients.append(c)
        else:
            recipients = list(candidates)

        data_payload = {}
        if request.action_url:
            data_payload["action_url"] = request.action_url
        data_json = json.dumps(data_payload) if data_payload else None

        dispatched_count = 0
        for user in recipients:
            dedup_key = f"broadcast:{broadcast_id[:12]}:{user.id}"
            notif = await self.create_notification(
                user_id=user.id,
                notification_type=request.type,
                title=request.title,
                body=request.body,
                data_json=data_json,
                deduplication_key=dedup_key,
                channels=request.channels,
            )
            if notif:
                dispatched_count += 1

        # Audit log
        audit = AuditLog(
            actor_id=admin_user.id,
            action="admin.broadcast_notification",
            target_type="Broadcast",
            target_id=broadcast_id,
            ip_address=ip_address,
            metadata_json=json.dumps(
                {
                    "title": request.title,
                    "type": request.type.value,
                    "recipients_targeted": len(recipients),
                    "dispatched_count": dispatched_count,
                    "channels": [c.value for c in request.channels],
                }
            ),
        )
        self.db.add(audit)
        await self.db.commit()

        logger.info(
            f"Admin {admin_user.id} broadcast notification '{request.title}' to {dispatched_count} users."
        )

        return AdminBroadcastResponse(
            success=True,
            recipient_count=len(recipients),
            dispatched_notifications=dispatched_count,
            broadcast_id=broadcast_id,
            channels=request.channels,
        )
