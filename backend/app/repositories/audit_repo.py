"""Audit repository for recording immutable security events."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditLog


class AuditRepository:
    """Manages audit trail creation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(
        self,
        action: str,
        actor_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        ip_address: str | None = None,
        request_id: str | None = None,
        metadata_json: str | None = None,
    ) -> AuditLog:
        """Appends an immutable audit log record."""
        log = AuditLog(
            action=action,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip_address,
            request_id=request_id,
            metadata_json=metadata_json,
        )
        self.session.add(log)
        await self.session.flush()
        return log
