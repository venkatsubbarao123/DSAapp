"""Audit repository for recording immutable security events."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.audit import AuditLog


class AuditRepository:
    """Manages audit trail creation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(
        self,
        action: str,
        actor_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata_json: Optional[str] = None,
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
