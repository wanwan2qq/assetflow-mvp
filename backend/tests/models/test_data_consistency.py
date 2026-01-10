"""
Property-based tests for data model consistency
**Feature: asset-flow-mvp, Property 6: 数据存储一致性**
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.commercial import CommercialProduct
from app.models.user import AssetType, RiskLevel, User, UserAsset, UserProfile


def get_test_session():
    """Create a fresh test database session"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


# Hypothesis strategies for generating test data
@composite
def valid_phone_numbers(draw):
    """Generate valid phone numbers"""
    # Chinese mobile numbers: 11 digits starting with 1
    return "1" + draw(st.text(alphabet="0123456789", min_size=10, max_size=10))


@composite
def valid_user_data(draw):
    """Generate valid user data"""
    return {
        "phone": draw(valid_phone_numbers()),
        "device_id": draw(st.one_of(st.none(), st.text(min_size=1, max_size=255))),
    }


@composite
def valid_user_profile_data(draw):
    """Generate valid user profile data"""
    return {
        "age_range": draw(st.sampled_from(["20-30", "30-40", "40-50", "50-60", "60+"])),
        "family_structure": draw(
            st.sampled_from(
                ["single", "married", "married_with_kids", "divorced", "widowed"]
            )
        ),
        "risk_preference": draw(st.sampled_from(list(RiskLevel))),
        "monthly_expense": draw(
            st.one_of(st.none(), st.floats(min_value=0, max_value=1000000))
        ),
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


@composite
def valid_commercial_product_data(draw):
    """Generate valid commercial product data"""
    return {
        "category": draw(
            st.sampled_from(["insurance", "broker", "investment", "loan", "consulting"])
        ),
        "name": draw(st.text(min_size=1, max_size=200)),
        "description": draw(st.text(min_size=1, max_size=1000)),
        "provider": draw(st.text(min_size=1, max_size=200)),
        "contact_info": {
            "phone": draw(valid_phone_numbers()),
            "name": draw(st.text(min_size=1, max_size=100)),
            "email": draw(st.emails()),
        },
        "priority": draw(st.integers(min_value=0, max_value=100)),
        "target_tags": draw(st.lists(st.text(min_size=1, max_size=50), max_size=10)),
        "is_active": draw(st.booleans()),
    }


class TestDataStorageConsistency:
    """
    **Feature: asset-flow-mvp, Property 6: 数据存储一致性**

    Property 6: Data Storage Consistency
    For any user-confirmed asset information, data stored in the database
    should remain consistent with user input, including correct asset type
    classification, numerical precision, and relationship integrity.
    **Validates: Requirements 1.5, 2.4, 12.3**
    """

    @given(user_data=valid_user_data())
    @settings(max_examples=100)
    def test_user_data_storage_consistency(self, user_data):
        """
        **Feature: asset-flow-mvp, Property 6: 数据存储一致性**
        Test that user data is stored consistently with input
        """
        with get_test_session() as session:
            # Create user
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)

            # Retrieve user from database
            retrieved_user = session.get(User, user.id)

            # Verify data consistency
            assert retrieved_user is not None
            assert retrieved_user.phone == user_data["phone"]
            assert retrieved_user.device_id == user_data["device_id"]
            assert retrieved_user.id is not None
            assert retrieved_user.created_at is not None

    @given(user_data=valid_user_data(), profile_data=valid_user_profile_data())
    @settings(max_examples=100)
    def test_user_profile_storage_consistency(self, user_data, profile_data):
        """
        **Feature: asset-flow-mvp, Property 6: 数据存储一致性**
        Test that user profile data maintains consistency with input
        """
        with get_test_session() as session:
            # Create user first
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)

            # Create profile
            profile = UserProfile(user_id=user.id, **profile_data)
            session.add(profile)
            session.commit()
            session.refresh(profile)

            # Retrieve profile from database
            retrieved_profile = session.get(UserProfile, profile.id)

            # Verify data consistency
            assert retrieved_profile is not None
            assert retrieved_profile.user_id == user.id
            assert retrieved_profile.age_range == profile_data["age_range"]
            assert (
                retrieved_profile.family_structure == profile_data["family_structure"]
            )
            assert retrieved_profile.risk_preference == profile_data["risk_preference"]
            assert retrieved_profile.monthly_expense == profile_data["monthly_expense"]

            # Verify relationship integrity
            assert retrieved_profile.user.id == user.id
            assert user.profile.id == profile.id

    @given(user_data=valid_user_data(), asset_data=valid_asset_data())
    @settings(max_examples=100)
    def test_asset_storage_consistency(self, user_data, asset_data):
        """
        **Feature: asset-flow-mvp, Property 6: 数据存储一致性**
        Test that asset data is stored with correct type classification and numerical precision
        """
        with get_test_session() as session:
            # Create user first
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)

            # Create asset
            asset = UserAsset(user_id=user.id, **asset_data)
            session.add(asset)
            session.commit()
            session.refresh(asset)

            # Retrieve asset from database
            retrieved_asset = session.get(UserAsset, asset.id)

            # Verify data consistency
            assert retrieved_asset is not None
            assert retrieved_asset.user_id == user.id
            assert retrieved_asset.asset_type == asset_data["asset_type"]
            assert retrieved_asset.name.strip() == asset_data["name"].strip()
            assert (
                abs(retrieved_asset.value - asset_data["value"]) < 1e-10
            )  # Numerical precision
            assert retrieved_asset.is_confirmed == asset_data["is_confirmed"]
            assert retrieved_asset.extra_data == asset_data["extra_data"]

            # Verify relationship integrity
            assert retrieved_asset.user.id == user.id
            assert any(a.id == asset.id for a in user.assets)

    @given(product_data=valid_commercial_product_data())
    @settings(max_examples=100)
    def test_commercial_product_storage_consistency(self, product_data):
        """
        **Feature: asset-flow-mvp, Property 6: 数据存储一致性**
        Test that commercial product data maintains consistency
        """
        with get_test_session() as session:
            # Create commercial product
            product = CommercialProduct(**product_data)
            session.add(product)
            session.commit()
            session.refresh(product)

            # Retrieve product from database
            retrieved_product = session.get(CommercialProduct, product.id)

            # Verify data consistency
            assert retrieved_product is not None
            assert retrieved_product.category == product_data["category"]
            assert retrieved_product.name == product_data["name"]
            assert retrieved_product.description == product_data["description"]
            assert retrieved_product.provider == product_data["provider"]
            assert retrieved_product.contact_info == product_data["contact_info"]
            assert retrieved_product.priority == product_data["priority"]
            assert retrieved_product.target_tags == product_data["target_tags"]
            assert retrieved_product.is_active == product_data["is_active"]

    @given(
        user_data=valid_user_data(),
        assets=st.lists(valid_asset_data(), min_size=1, max_size=5),
    )
    @settings(max_examples=50)  # Reduced for performance
    def test_multiple_assets_relationship_integrity(self, user_data, assets):
        """
        **Feature: asset-flow-mvp, Property 6: 数据存储一致性**
        Test that multiple assets maintain correct relationship integrity
        """
        with get_test_session() as session:
            # Create user
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)

            # Create multiple assets
            created_assets = []
            for asset_data in assets:
                asset = UserAsset(user_id=user.id, **asset_data)
                session.add(asset)
                created_assets.append(asset)

            session.commit()

            # Refresh all assets
            for asset in created_assets:
                session.refresh(asset)

            # Verify all assets belong to the user
            user_assets = session.exec(
                select(UserAsset).where(UserAsset.user_id == user.id)
            ).all()
            assert len(user_assets) == len(assets)

            # Verify each asset maintains data consistency
            for i, retrieved_asset in enumerate(user_assets):
                original_data = assets[i]
                assert retrieved_asset.user_id == user.id
                assert retrieved_asset.asset_type == original_data["asset_type"]
                assert retrieved_asset.name.strip() == original_data["name"].strip()
                assert abs(retrieved_asset.value - original_data["value"]) < 1e-10

    def test_phone_uniqueness_constraint(self):
        """
        **Feature: asset-flow-mvp, Property 6: 数据存储一致性**
        Test that phone number uniqueness constraint is enforced
        """
        with get_test_session() as session:
            phone = "13800138000"

            # Create first user
            user1 = User(phone=phone, device_id="device1")
            session.add(user1)
            session.commit()

            # Try to create second user with same phone
            user2 = User(phone=phone, device_id="device2")
            session.add(user2)

            with pytest.raises(IntegrityError):
                session.commit()

    def test_user_profile_uniqueness_constraint(self):
        """
        **Feature: asset-flow-mvp, Property 6: 数据存储一致性**
        Test that user can only have one profile
        """
        with get_test_session() as session:
            # Create user
            user = User(phone="13800138000", device_id="device1")
            session.add(user)
            session.commit()
            session.refresh(user)

            # Create first profile
            profile1 = UserProfile(
                user_id=user.id,
                age_range="30-40",
                family_structure="married",
                risk_preference=RiskLevel.MODERATE,
            )
            session.add(profile1)
            session.commit()

            # Try to create second profile for same user
            profile2 = UserProfile(
                user_id=user.id,
                age_range="40-50",
                family_structure="single",
                risk_preference=RiskLevel.CONSERVATIVE,
            )
            session.add(profile2)

            with pytest.raises(IntegrityError):
                session.commit()
