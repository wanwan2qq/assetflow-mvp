"""
Property-based tests for authentication system
**Feature: asset-flow-mvp, Property 7: 用户数据隔离正确性**
**Feature: asset-flow-mvp, Property 8: 认证令牌验证正确性**
"""

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.auth import verify_user_access
from app.models.user import AssetType, User, UserAsset
from app.services.auth import AuthService


def get_test_session():
    """Create a fresh test database session"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


# Hypothesis strategies for generating test data
@composite
def valid_phone_numbers(draw):
    """Generate valid phone numbers"""
    return "1" + draw(st.text(alphabet="0123456789", min_size=10, max_size=10))


@composite
def valid_device_ids(draw):
    """Generate valid device IDs"""
    return draw(
        st.text(
            min_size=1,
            max_size=255,
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        )
    )


@composite
def valid_user_pairs(draw):
    """Generate pairs of different users"""
    phone1 = draw(valid_phone_numbers())
    phone2 = draw(valid_phone_numbers().filter(lambda x: x != phone1))
    device1 = draw(valid_device_ids())
    device2 = draw(valid_device_ids().filter(lambda x: x != device1))

    return {
        "user1": {"phone": phone1, "device_id": device1},
        "user2": {"phone": phone2, "device_id": device2},
    }


@composite
def valid_asset_data(draw):
    """Generate valid asset data"""
    return {
        "asset_type": draw(st.sampled_from(list(AssetType))),
        "name": draw(st.text(min_size=1, max_size=200).filter(lambda x: x.strip())),
        "value": draw(st.floats(min_value=0.01, max_value=1e11)),
        "is_confirmed": draw(st.booleans()),
        "extra_data": draw(st.one_of(st.none(), st.dictionaries(st.text(), st.text()))),
    }


class TestAuthenticationProperties:
    """
    Property-based tests for authentication system correctness
    """

    @given(user_pairs=valid_user_pairs())
    @settings(max_examples=100)
    def test_user_data_isolation_correctness(self, user_pairs):
        """
        **Feature: asset-flow-mvp, Property 7: 用户数据隔离正确性**

        Property 7: User Data Isolation Correctness
        For any database query operation, the system should enforce user_id filtering,
        ensuring users can only access their own asset data and never return other users' information.
        **Validates: Requirements 11.2**
        """
        with get_test_session() as session:
            # Create two different users
            user1 = User(**user_pairs["user1"])
            user2 = User(**user_pairs["user2"])
            session.add(user1)
            session.add(user2)
            session.commit()
            session.refresh(user1)
            session.refresh(user2)

            # Verify users are different
            assert user1.id != user2.id
            assert user1.phone != user2.phone

            # Test that verify_user_access correctly isolates users
            # User1 should be able to access their own data
            try:
                verify_user_access(user1, user1.id)
                # Should not raise exception
            except HTTPException:
                pytest.fail("User should be able to access their own data")

            # User1 should NOT be able to access user2's data
            with pytest.raises(HTTPException) as exc_info:
                verify_user_access(user1, user2.id)

            assert exc_info.value.status_code == 403
            assert "Access denied" in str(exc_info.value.detail)

            # Test database-level isolation by querying assets
            # Create assets for both users
            asset1 = UserAsset(
                user_id=user1.id,
                asset_type=AssetType.CASH,
                name="User1 Asset",
                value=1000.0,
            )
            asset2 = UserAsset(
                user_id=user2.id,
                asset_type=AssetType.CASH,
                name="User2 Asset",
                value=2000.0,
            )
            session.add(asset1)
            session.add(asset2)
            session.commit()

            # Query assets for user1 - should only return user1's assets
            user1_assets = session.exec(
                select(UserAsset).where(UserAsset.user_id == user1.id)
            ).all()

            # Verify isolation: user1's query should only return their assets
            assert len(user1_assets) == 1
            assert user1_assets[0].user_id == user1.id
            assert user1_assets[0].name == "User1 Asset"

            # Verify no cross-contamination
            for asset in user1_assets:
                assert asset.user_id == user1.id
                assert asset.user_id != user2.id

    @given(
        user_data=st.fixed_dictionaries(
            {"phone": valid_phone_numbers(), "device_id": valid_device_ids()}
        )
    )
    @settings(max_examples=100)
    def test_authentication_token_validation_correctness(self, user_data):
        """
        **Feature: asset-flow-mvp, Property 8: 认证令牌验证正确性**

        Property 8: Authentication Token Validation Correctness
        For any API endpoint access (except login/register), the system should validate JWT token validity,
        reject invalid or expired tokens, and ensure only authenticated users can access protected resources.
        **Validates: Requirements 11.1**
        """
        auth_service = AuthService()
        with get_test_session() as session:
            # Create user
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)

            # Generate valid token
            valid_token = auth_service.create_access_token(user.id)

            # Property: Valid tokens should always verify to correct user_id
            verified_user_id = auth_service.verify_token(valid_token)
            assert verified_user_id == user.id

            # Property: Invalid tokens should always return None
            invalid_tokens = [
                "invalid.token.here",
                "not.a.jwt.token",
                "",
                "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
                valid_token + "corrupted",
                valid_token[:-5],  # Truncated token
            ]

            for invalid_token in invalid_tokens:
                verified_user_id = auth_service.verify_token(invalid_token)
                assert verified_user_id is None, (
                    f"Invalid token {invalid_token} should not verify"
                )

            # Property: Tokens for different users should not cross-validate
            # Create another user and token
            other_user_data = {
                "phone": user_data["phone"] + "1",  # Make it different
                "device_id": user_data["device_id"] + "_other",
            }
            other_user = User(**other_user_data)
            session.add(other_user)
            session.commit()
            session.refresh(other_user)

            other_token = auth_service.create_access_token(other_user.id)

            # Verify tokens are user-specific
            assert auth_service.verify_token(valid_token) == user.id
            assert auth_service.verify_token(other_token) == other_user.id
            assert auth_service.verify_token(valid_token) != other_user.id
            assert auth_service.verify_token(other_token) != user.id

    @given(
        user_data=st.fixed_dictionaries(
            {"phone": valid_phone_numbers(), "device_id": valid_device_ids()}
        ),
        assets=st.lists(valid_asset_data(), min_size=1, max_size=5),
    )
    @settings(max_examples=50)  # Reduced for performance
    def test_multi_asset_user_isolation(self, user_data, assets):
        """
        **Feature: asset-flow-mvp, Property 7: 用户数据隔离正确性**

        Test that user isolation works correctly with multiple assets per user
        **Validates: Requirements 11.2**
        """
        with get_test_session() as session:
            # Create two users
            user1 = User(**user_data)
            user2_data = {
                "phone": user_data["phone"] + "1",
                "device_id": user_data["device_id"] + "_2",
            }
            user2 = User(**user2_data)

            session.add(user1)
            session.add(user2)
            session.commit()
            session.refresh(user1)
            session.refresh(user2)

            # Create assets for user1
            user1_assets = []
            for asset_data in assets:
                asset = UserAsset(user_id=user1.id, **asset_data)
                session.add(asset)
                user1_assets.append(asset)

            # Create one asset for user2
            user2_asset = UserAsset(
                user_id=user2.id,
                asset_type=AssetType.CASH,
                name="User2 Asset",
                value=5000.0,
            )
            session.add(user2_asset)
            session.commit()

            # Query user1's assets
            retrieved_assets = session.exec(
                select(UserAsset).where(UserAsset.user_id == user1.id)
            ).all()

            # Verify isolation properties
            assert len(retrieved_assets) == len(assets)

            # All retrieved assets should belong to user1
            for asset in retrieved_assets:
                assert asset.user_id == user1.id
                assert asset.user_id != user2.id

            # Query user2's assets
            user2_retrieved = session.exec(
                select(UserAsset).where(UserAsset.user_id == user2.id)
            ).all()

            # User2 should only see their own asset
            assert len(user2_retrieved) == 1
            assert user2_retrieved[0].user_id == user2.id
            assert user2_retrieved[0].name == "User2 Asset"

    @given(phone=valid_phone_numbers())
    @settings(max_examples=100)
    def test_token_user_binding_correctness(self, phone):
        """
        **Feature: asset-flow-mvp, Property 8: 认证令牌验证正确性**

        Test that tokens are correctly bound to specific users
        **Validates: Requirements 11.1**
        """
        auth_service = AuthService()
        with get_test_session() as session:
            # Create user
            user = User(phone=phone, device_id="test_device")
            session.add(user)
            session.commit()
            session.refresh(user)

            # Generate multiple tokens for the same user
            token1 = auth_service.create_access_token(user.id)
            token2 = auth_service.create_access_token(user.id)

            # Both tokens should verify to the same user
            assert auth_service.verify_token(token1) == user.id
            assert auth_service.verify_token(token2) == user.id

            # Both tokens should be valid (the important property)
            assert token1 is not None
            assert token2 is not None

    def test_phone_uniqueness_enforcement(self):
        """
        **Feature: asset-flow-mvp, Property 7: 用户数据隔离正确性**

        Test that phone number uniqueness is enforced at database level
        **Validates: Requirements 11.2**
        """
        with get_test_session() as session:
            phone = "13800138000"

            # Create first user
            user1 = User(phone=phone, device_id="device1")
            session.add(user1)
            session.commit()

            # Attempt to create second user with same phone should fail
            user2 = User(phone=phone, device_id="device2")
            session.add(user2)

            with pytest.raises(
                (IntegrityError, Exception)
            ):  # Should raise IntegrityError or similar
                session.commit()

    @given(phone1=valid_phone_numbers(), phone2=valid_phone_numbers())
    @settings(max_examples=50)
    def test_cross_user_token_rejection(self, phone1, phone2):
        """
        **Feature: asset-flow-mvp, Property 8: 认证令牌验证正确性**

        Test that tokens cannot be used to access other users' data
        **Validates: Requirements 11.1**
        """
        # Skip if phones are the same (would create same user)
        if phone1 == phone2:
            return

        auth_service = AuthService()
        with get_test_session() as session:
            # Create two different users
            user1 = User(phone=phone1, device_id="device1")
            user2 = User(phone=phone2, device_id="device2")
            session.add(user1)
            session.add(user2)
            session.commit()
            session.refresh(user1)
            session.refresh(user2)

            # Generate tokens for both users
            token1 = auth_service.create_access_token(user1.id)
            token2 = auth_service.create_access_token(user2.id)

            # Verify tokens are user-specific
            assert auth_service.verify_token(token1) == user1.id
            assert auth_service.verify_token(token2) == user2.id

            # Cross-verification should fail
            assert auth_service.verify_token(token1) != user2.id
            assert auth_service.verify_token(token2) != user1.id

            # Test access control
            with pytest.raises(HTTPException):
                verify_user_access(user1, user2.id)

            with pytest.raises(HTTPException):
                verify_user_access(user2, user1.id)
