"""
Audit trail service for tracking data changes
"""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.audit import AuditAction, AuditLog, UserAssetHistory
from app.models.user import UserAsset


class AuditService:
    """Service for managing audit trails"""

    @staticmethod
    async def log_change(
        db: AsyncSession,
        table_name: str,
        record_id: int,
        action: AuditAction,
        user_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log a data change to the audit trail"""

        audit_log = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            extra_metadata=extra_metadata,
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        return audit_log

    @staticmethod
    async def log_asset_change(
        db: AsyncSession,
        asset: UserAsset,
        action: AuditAction,
        user_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        change_reason: str | None = None,
        **audit_kwargs: Any,
    ) -> tuple[AuditLog, UserAssetHistory | None]:
        """Log an asset change with detailed history tracking"""

        # Log to general audit trail
        audit_log = await AuditService.log_change(
            db=db,
            table_name="userasset",
            record_id=asset.id,
            action=action,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            **audit_kwargs,
        )

        # Create detailed asset history record
        asset_history = None
        if action in [AuditAction.CREATE, AuditAction.UPDATE]:
            # Close previous history record if it exists
            if action == AuditAction.UPDATE:
                stmt = select(UserAssetHistory).where(
                    UserAssetHistory.asset_id == asset.id,
                    UserAssetHistory.is_valid_to.is_(None),
                )
                result = await db.execute(stmt)
                current_history = result.scalar_one_or_none()

                if current_history:
                    current_history.is_valid_to = datetime.utcnow()
                    db.add(current_history)

            # Create new history record
            asset_history = UserAssetHistory(
                asset_id=asset.id,
                user_id=asset.user_id,
                asset_type=asset.asset_type.value,
                name=asset.name,
                value=asset.value,
                is_confirmed=asset.is_confirmed,
                extra_data=asset.extra_data,
                change_reason=change_reason,
                changed_by=user_id,
                changed_at=datetime.utcnow(),
                is_valid_from=datetime.utcnow(),
            )

            db.add(asset_history)
            await db.commit()
            await db.refresh(asset_history)

        return audit_log, asset_history

    @staticmethod
    async def get_audit_trail(
        db: AsyncSession,
        table_name: str | None = None,
        record_id: int | None = None,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit trail records with optional filtering"""

        stmt = select(AuditLog)

        if table_name:
            stmt = stmt.where(AuditLog.table_name == table_name)
        if record_id:
            stmt = stmt.where(AuditLog.record_id == record_id)
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)

        stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_asset_history(
        db: AsyncSession,
        asset_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserAssetHistory]:
        """Get historical changes for a specific asset"""

        stmt = (
            select(UserAssetHistory)
            .where(UserAssetHistory.asset_id == asset_id)
            .order_by(UserAssetHistory.changed_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_user_activity(
        db: AsyncSession,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get all audit activity for a specific user"""

        return await AuditService.get_audit_trail(
            db=db,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
