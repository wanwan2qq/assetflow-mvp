"""
Tests for audit trail functionality
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.audit import AuditAction, UserAssetHistory
from app.models.user import AssetType, User, UserAsset
from app.services.audit import AuditService


class TestAuditTrail:
    """Test audit trail functionality"""

    @pytest.mark.asyncio
    async def test_audit_log_creation(self, db_session: AsyncSession, test_user: User):
        """Test basic audit log creation"""

        # Log a change
        audit_log = await AuditService.log_change(
            db=db_session,
            table_name="test_table",
            record_id=123,
            action=AuditAction.CREATE,
            user_id=test_user.id,
            new_values={"field": "value"},
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        assert audit_log.id is not None
        assert audit_log.table_name == "test_table"
        assert audit_log.record_id == 123
        assert audit_log.action == AuditAction.CREATE
        assert audit_log.user_id == test_user.id
        assert audit_log.new_values == {"field": "value"}
        assert audit_log.ip_address == "127.0.0.1"
        assert audit_log.user_agent == "test-agent"

    @pytest.mark.asyncio
    async def test_asset_audit_with_history(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test asset change logging with history tracking"""

        # Create an asset
        asset = UserAsset(
            user_id=test_user.id,
            asset_type=AssetType.CASH,
            name="Test Asset",
            value=1000.0,
            is_confirmed=True,
        )

        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)

        # Log asset creation
        audit_log, asset_history = await AuditService.log_asset_change(
            db=db_session,
            asset=asset,
            action=AuditAction.CREATE,
            user_id=test_user.id,
            new_values={
                "asset_type": asset.asset_type.value,
                "name": asset.name,
                "value": asset.value,
                "is_confirmed": asset.is_confirmed,
            },
            change_reason="Asset created",
        )

        # Verify audit log
        assert audit_log.table_name == "userasset"
        assert audit_log.record_id == asset.id
        assert audit_log.action == AuditAction.CREATE

        # Verify asset history
        assert asset_history is not None
        assert asset_history.asset_id == asset.id
        assert asset_history.user_id == test_user.id
        assert asset_history.name == "Test Asset"
        assert asset_history.value == 1000.0
        assert asset_history.change_reason == "Asset created"
        assert asset_history.is_valid_to is None  # Current version

    @pytest.mark.asyncio
    async def test_asset_update_history_tracking(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that asset updates create proper history tracking"""

        # Create an asset
        asset = UserAsset(
            user_id=test_user.id,
            asset_type=AssetType.INVESTMENT,
            name="Stock Portfolio",
            value=5000.0,
            is_confirmed=True,
        )

        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)

        # Log initial creation
        await AuditService.log_asset_change(
            db=db_session,
            asset=asset,
            action=AuditAction.CREATE,
            user_id=test_user.id,
            change_reason="Initial asset creation",
        )

        # Update the asset
        old_values = {
            "asset_type": asset.asset_type.value,
            "name": asset.name,
            "value": asset.value,
        }

        asset.value = 6000.0
        asset.name = "Updated Stock Portfolio"

        new_values = {
            "asset_type": asset.asset_type.value,
            "name": asset.name,
            "value": asset.value,
        }

        # Log the update
        audit_log, asset_history = await AuditService.log_asset_change(
            db=db_session,
            asset=asset,
            action=AuditAction.UPDATE,
            user_id=test_user.id,
            old_values=old_values,
            new_values=new_values,
            change_reason="Value updated",
        )

        # Verify audit log
        assert audit_log.action == AuditAction.UPDATE
        assert audit_log.old_values["value"] == 5000.0
        assert audit_log.new_values["value"] == 6000.0

        # Verify new history record
        assert asset_history.value == 6000.0
        assert asset_history.name == "Updated Stock Portfolio"
        assert asset_history.change_reason == "Value updated"

        # Verify previous history record was closed
        stmt = select(UserAssetHistory).where(
            UserAssetHistory.asset_id == asset.id,
            UserAssetHistory.is_valid_to.is_not(None),
        )
        result = await db_session.execute(stmt)
        closed_history = result.scalar_one_or_none()

        assert closed_history is not None
        assert closed_history.value == 5000.0
        assert closed_history.name == "Stock Portfolio"

    @pytest.mark.asyncio
    async def test_get_audit_trail(self, db_session: AsyncSession, test_user: User):
        """Test retrieving audit trail records"""

        # Create multiple audit records
        for i in range(3):
            await AuditService.log_change(
                db=db_session,
                table_name="test_table",
                record_id=i,
                action=AuditAction.CREATE,
                user_id=test_user.id,
                new_values={"index": i},
            )

        # Get all audit records
        audit_records = await AuditService.get_audit_trail(db=db_session)
        assert len(audit_records) >= 3

        # Get filtered audit records
        filtered_records = await AuditService.get_audit_trail(
            db=db_session,
            table_name="test_table",
            user_id=test_user.id,
        )
        assert len(filtered_records) == 3

        # Verify ordering (newest first)
        assert filtered_records[0].new_values["index"] == 2
        assert filtered_records[1].new_values["index"] == 1
        assert filtered_records[2].new_values["index"] == 0

    @pytest.mark.asyncio
    async def test_get_user_activity(self, db_session: AsyncSession, test_user: User):
        """Test retrieving user activity"""

        # Create audit records for the user
        await AuditService.log_change(
            db=db_session,
            table_name="userprofile",
            record_id=1,
            action=AuditAction.CREATE,
            user_id=test_user.id,
        )

        await AuditService.log_change(
            db=db_session,
            table_name="userasset",
            record_id=1,
            action=AuditAction.UPDATE,
            user_id=test_user.id,
        )

        # Get user activity
        activity = await AuditService.get_user_activity(
            db=db_session, user_id=test_user.id
        )

        assert len(activity) == 2
        assert all(record.user_id == test_user.id for record in activity)

        # Verify different table names are included
        table_names = {record.table_name for record in activity}
        assert "userprofile" in table_names
        assert "userasset" in table_names
