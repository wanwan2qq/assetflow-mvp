"""
Service for storing extracted asset and profile information to database
"""

import logging
from typing import Any

from sqlmodel import Session, select

from app.core.database import get_db_session
from app.models.user import AssetType, UserAsset, UserProfile
from app.services.information_extraction import ExtractedAsset, ExtractedUserProfile

logger = logging.getLogger(__name__)


class AssetExtractionService:
    """Service for managing extracted asset and profile data"""

    async def store_extracted_assets(
        self,
        user_id: int,
        extracted_assets: list[ExtractedAsset],
        session: Session | None = None,
    ) -> list[UserAsset]:
        """Store extracted assets to database"""

        if session is None:
            async for session in get_db_session():
                return await self._store_assets_in_session(
                    user_id, extracted_assets, session
                )
        else:
            return await self._store_assets_in_session(
                user_id, extracted_assets, session
            )

    async def _store_assets_in_session(
        self, user_id: int, extracted_assets: list[ExtractedAsset], session: Session
    ) -> list[UserAsset]:
        """Store assets within a database session"""
        stored_assets = []

        for extracted_asset in extracted_assets:
            try:
                # Check if similar asset already exists
                existing_asset = await self._find_similar_asset(
                    user_id, extracted_asset, session
                )

                if existing_asset:
                    # Update existing asset if new data has higher confidence
                    if extracted_asset.confidence > existing_asset.metadata.get(
                        "confidence", 0
                    ):
                        await self._update_asset_from_extracted(
                            existing_asset, extracted_asset, session
                        )
                        stored_assets.append(existing_asset)
                else:
                    # Create new asset
                    new_asset = await self._create_asset_from_extracted(
                        user_id, extracted_asset, session
                    )
                    stored_assets.append(new_asset)

            except Exception as e:
                logger.error(
                    f"Error storing extracted asset {extracted_asset.name}: {e}"
                )
                continue

        await session.commit()
        return stored_assets

    async def store_extracted_profile(
        self,
        user_id: int,
        extracted_profile: ExtractedUserProfile,
        session: Session | None = None,
    ) -> UserProfile | None:
        """Store extracted user profile to database"""

        if session is None:
            async for session in get_db_session():
                return await self._store_profile_in_session(
                    user_id, extracted_profile, session
                )
        else:
            return await self._store_profile_in_session(
                user_id, extracted_profile, session
            )

    async def _store_profile_in_session(
        self, user_id: int, extracted_profile: ExtractedUserProfile, session: Session
    ) -> UserProfile | None:
        """Store profile within a database session"""
        try:
            # Get or create user profile
            statement = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await session.execute(statement)
            profile = result.scalar_one_or_none()

            if not profile:
                profile = UserProfile(user_id=user_id)
                session.add(profile)

            # Update profile fields with extracted data
            if extracted_profile.age_range:
                profile.age_range = extracted_profile.age_range

            if extracted_profile.family_structure:
                profile.family_structure = extracted_profile.family_structure

            if extracted_profile.monthly_expense:
                profile.monthly_expense = extracted_profile.monthly_expense

            if extracted_profile.risk_preference:
                # Map extracted risk preference to enum values
                risk_mapping = {
                    "conservative": "conservative",
                    "moderate": "moderate",
                    "aggressive": "aggressive",
                }
                if extracted_profile.risk_preference in risk_mapping:
                    profile.risk_preference = risk_mapping[
                        extracted_profile.risk_preference
                    ]

            await session.commit()
            await session.refresh(profile)

            logger.info(f"Updated user profile for user {user_id}")
            return profile

        except Exception as e:
            logger.error(f"Error storing extracted profile for user {user_id}: {e}")
            await session.rollback()
            return None

    async def _find_similar_asset(
        self, user_id: int, extracted_asset: ExtractedAsset, session: Session
    ) -> UserAsset | None:
        """Find similar existing asset"""

        # Convert extracted asset type to database enum
        asset_type_mapping = {
            "real_estate": AssetType.REAL_ESTATE,
            "cash": AssetType.CASH,
            "investment": AssetType.INVESTMENT,
            "insurance": AssetType.INSURANCE,
            "liability": AssetType.LIABILITY,
        }

        db_asset_type = asset_type_mapping.get(extracted_asset.asset_type)
        if not db_asset_type:
            return None

        # Query for similar assets
        statement = select(UserAsset).where(
            UserAsset.user_id == user_id, UserAsset.asset_type == db_asset_type
        )

        result = await session.execute(statement)
        existing_assets = result.scalars().all()

        # For real estate, match by location and area
        if db_asset_type == AssetType.REAL_ESTATE:
            for asset in existing_assets:
                asset_location = (
                    asset.metadata.get("location") if asset.metadata else None
                )
                asset_area = asset.metadata.get("area") if asset.metadata else None

                # Match by location or area similarity
                if (
                    extracted_asset.location
                    and asset_location
                    and extracted_asset.location in asset_location
                ):
                    return asset

                if (
                    extracted_asset.area
                    and asset_area
                    and abs(extracted_asset.area - asset_area) < 10
                ):  # Within 10 sqm
                    return asset

        # For other asset types, match by name similarity
        else:
            for asset in existing_assets:
                if extracted_asset.name.lower() in asset.name.lower():
                    return asset

        return None

    async def _create_asset_from_extracted(
        self, user_id: int, extracted_asset: ExtractedAsset, session: Session
    ) -> UserAsset:
        """Create new asset from extracted data"""

        # Convert asset type
        asset_type_mapping = {
            "real_estate": AssetType.REAL_ESTATE,
            "cash": AssetType.CASH,
            "investment": AssetType.INVESTMENT,
            "insurance": AssetType.INSURANCE,
            "liability": AssetType.LIABILITY,
        }

        db_asset_type = asset_type_mapping[extracted_asset.asset_type]

        # Prepare metadata
        metadata = extracted_asset.metadata.copy()
        metadata.update(
            {
                "confidence": extracted_asset.confidence,
                "extracted_from": extracted_asset.extracted_from,
                "extraction_timestamp": extracted_asset.timestamp,
            }
        )

        if extracted_asset.location:
            metadata["location"] = extracted_asset.location
        if extracted_asset.area:
            metadata["area"] = extracted_asset.area

        # Create asset
        asset = UserAsset(
            user_id=user_id,
            asset_type=db_asset_type,
            name=extracted_asset.name,
            value=extracted_asset.value or 0.0,
            is_confirmed=False,  # Extracted assets need user confirmation
            metadata=metadata,
        )

        session.add(asset)
        await session.flush()  # Ensure the asset gets an ID
        logger.info(f"Created new asset: {asset.name} for user {user_id}")

        return asset

    async def _update_asset_from_extracted(
        self,
        existing_asset: UserAsset,
        extracted_asset: ExtractedAsset,
        session: Session,
    ):
        """Update existing asset with extracted data"""

        # Update value if extracted value has higher confidence
        if extracted_asset.value and extracted_asset.confidence > 0.5:
            existing_asset.value = extracted_asset.value

        # Update metadata
        if not existing_asset.metadata:
            existing_asset.metadata = {}

        existing_asset.metadata.update(
            {
                "confidence": max(
                    extracted_asset.confidence,
                    existing_asset.metadata.get("confidence", 0),
                ),
                "last_extraction": extracted_asset.timestamp,
                "extraction_source": extracted_asset.extracted_from,
            }
        )

        if extracted_asset.location:
            existing_asset.metadata["location"] = extracted_asset.location
        if extracted_asset.area:
            existing_asset.metadata["area"] = extracted_asset.area

        # Mark as modified
        session.add(existing_asset)
        logger.info(f"Updated existing asset: {existing_asset.name}")

    async def get_extraction_summary(self, user_id: int) -> dict[str, Any]:
        """Get summary of extracted information for a user"""

        async for session in get_db_session():
            # Get user assets
            assets_statement = select(UserAsset).where(UserAsset.user_id == user_id)
            assets_result = await session.execute(assets_statement)
            assets = assets_result.scalars().all()

            # Get user profile
            profile_statement = select(UserProfile).where(
                UserProfile.user_id == user_id
            )
            profile_result = await session.execute(profile_statement)
            profile = profile_result.scalar_one_or_none()

            # Calculate completeness
            asset_types_covered = len({asset.asset_type for asset in assets})
            confirmed_assets = sum(1 for asset in assets if asset.is_confirmed)

            profile_completeness = 0
            if profile:
                profile_fields = [
                    profile.age_range,
                    profile.family_structure,
                    profile.monthly_expense,
                    profile.risk_preference,
                ]
                profile_completeness = sum(
                    1 for field in profile_fields if field is not None
                ) / len(profile_fields)

            return {
                "total_assets": len(assets),
                "confirmed_assets": confirmed_assets,
                "asset_types_covered": asset_types_covered,
                "profile_completeness": profile_completeness,
                "overall_completeness": (asset_types_covered / 5.0 * 0.6)
                + (profile_completeness * 0.4),
                "assets_by_type": {
                    asset_type.value: [
                        {
                            "name": asset.name,
                            "value": asset.value,
                            "is_confirmed": asset.is_confirmed,
                            "confidence": asset.metadata.get("confidence", 0)
                            if asset.metadata
                            else 0,
                        }
                        for asset in assets
                        if asset.asset_type == asset_type
                    ]
                    for asset_type in AssetType
                },
                "profile": {
                    "age_range": profile.age_range if profile else None,
                    "family_structure": profile.family_structure if profile else None,
                    "monthly_expense": profile.monthly_expense if profile else None,
                    "risk_preference": profile.risk_preference if profile else None,
                }
                if profile
                else None,
            }


# Global service instance
asset_extraction_service = AssetExtractionService()
