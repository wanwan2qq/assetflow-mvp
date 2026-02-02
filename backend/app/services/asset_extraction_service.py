"""
Service for storing extracted asset and profile information to database
Enhanced with Phase 2 state synchronization capabilities
"""

import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.core.database import get_db_session
from app.models.user import AssetType, UserAsset, UserProfile
from app.models.cognition import UserCognition
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
                logger.info(f"[DEBUG] Calling _find_similar_asset with user_id={user_id}, asset={extracted_asset.name}")
                existing_asset = await self._find_similar_asset(
                    user_id, extracted_asset, session
                )

                if existing_asset:
                    # Update existing asset if new data has higher confidence
                    current_conf = (existing_asset.extra_data or {}).get("confidence", 0)
                    if extracted_asset.confidence > current_conf:
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
        """Find similar existing asset with fine-grained matching logic"""
        logger.info(f"[DEBUG] Inside _find_similar_asset for {extracted_asset.name}")

        # Convert extracted asset type to database enum
        asset_type_mapping = {
            "real_estate": AssetType.REAL_ESTATE,
            "cash": AssetType.CASH,
            "investment": AssetType.INVESTMENT,
            "insurance": AssetType.INSURANCE,
            "liability": AssetType.LIABILITY,
            # Map extended types to available categories
            "mutual_fund": AssetType.INVESTMENT,
            "etf": AssetType.INVESTMENT,
            "stock": AssetType.INVESTMENT,
            "bond": AssetType.INVESTMENT,
            "crypto": AssetType.INVESTMENT,
            "other": AssetType.INVESTMENT, # Fallback
        }
        
        # Determine strict asset type
        # Note: extracted_asset.asset_type might be a string or Enum depending on Pydantic model
        # We try to use it as a key for mapping
        lookup_key = extracted_asset.asset_type
        if hasattr(lookup_key, "value"):
            lookup_key = lookup_key.value
            
        db_asset_type = asset_type_mapping.get(lookup_key.lower() if isinstance(lookup_key, str) else lookup_key)
        
        # Fallback if not found in specific map (e.g. if extracted_asset.asset_type is already the Enum)
        if not db_asset_type and isinstance(extracted_asset.asset_type, AssetType):
            db_asset_type = extracted_asset.asset_type

        if not db_asset_type:
            logger.warning(f"Unknown asset type: {extracted_asset.asset_type}")
            return None

        # Helper vars from extracted asset
        name = extracted_asset.name
        location = extracted_asset.location
        area = extracted_asset.area

        try:
            # Query all assets of the same type for this user
            statement = select(UserAsset).where(
                UserAsset.user_id == user_id,
                UserAsset.asset_type == db_asset_type
            )
            result = await session.execute(statement)
            existing_assets = result.scalars().all()
            
            if not existing_assets:
                return None
            
            # Special matching logic for real estate
            if db_asset_type == AssetType.REAL_ESTATE:
                for asset in existing_assets:
                    # Note: Use extra_data, not metadata which might be missing/alias
                    asset_location = (asset.extra_data or {}).get("location")
                    asset_area = (asset.extra_data or {}).get("area")
                    
                    # Normalize extracted data
                    ext_loc_norm = location.replace(" ", "").lower() if location else ""
                    ext_name_norm = name.replace(" ", "").lower()
                    
                    # Normalize asset data
                    asset_loc_norm = asset_location.replace(" ", "").lower() if asset_location else ""
                    asset_name_norm = asset.name.replace(" ", "").lower()
                    
                    # MATCH 1: Location overlap (if both exist)
                    if ext_loc_norm and asset_loc_norm:
                        if ext_loc_norm in asset_loc_norm or asset_loc_norm in ext_loc_norm:
                            logger.info(f"Matched real estate by location overlap: '{location}' ~ '{asset_location}'")
                            return asset

                    # MATCH 2: Name overlap (if substantial)
                    if ext_name_norm in asset_name_norm or asset_name_norm in ext_name_norm:
                         logger.info(f"Matched real estate by name overlap: '{name}' ~ '{asset.name}'")
                         return asset
                         
                    # MATCH 3: Cross-field overlap (Name vs Location)
                    if ext_loc_norm and asset_name_norm:
                         if ext_loc_norm in asset_name_norm or asset_name_norm in ext_loc_norm:
                             logger.info(f"Matched real estate by cross-field (Loc vs Name): '{location}' ~ '{asset.name}'")
                             return asset
                             
                    if ext_name_norm and asset_loc_norm:
                        if ext_name_norm in asset_loc_norm or asset_loc_norm in ext_name_norm:
                            logger.info(f"Matched real estate by cross-field (Name vs Loc): '{name}' ~ '{asset_location}'")
                            return asset
                    
                    # MATCH 4: Area exact match (strong signal) with tolerance
                    if area and asset_area:
                        # Ensure we are comparing numbers
                        try:
                            if abs(float(area) - float(asset_area)) < 5:
                                logger.info(f"Matched real estate by area: {area} ~ {asset_area}")
                                return asset
                        except (ValueError, TypeError):
                            pass
                    
                    # MATCH 5: Fuzzy name check (fallback)
                    if self._is_name_similar(name, asset.name):
                        logger.info(f"Matched real estate by fuzzy name: '{name}' ~ '{asset.name}'")
                        return asset
            
            # For other asset types, match by name similarity
            else:
                for asset in existing_assets:
                    if self._is_name_similar(name, asset.name):
                        logger.info(f"Matched {db_asset_type.value} by name: '{name}' ~ '{asset.name}'")
                        return asset
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding similar asset: {e}")
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
            extra_data=metadata,
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
        if not existing_asset.extra_data:
            existing_asset.extra_data = {}

        existing_asset.extra_data.update(
            {
                "confidence": max(
                    extracted_asset.confidence,
                    (existing_asset.extra_data or {}).get("confidence", 0),
                ),
                "last_extraction": extracted_asset.timestamp,
                "extraction_source": extracted_asset.extracted_from,
            }
        )

        if extracted_asset.location:
            existing_asset.extra_data["location"] = extracted_asset.location
        if extracted_asset.area:
            existing_asset.extra_data["area"] = extracted_asset.area

        # Mark as modified
        session.add(existing_asset)
        logger.info(f"Updated existing asset: {existing_asset.name}")

    async def update_asset_value(
        self, asset_id: int, new_value: float, session: Session | None = None
    ) -> UserAsset | None:
        """
        Update the value of a specific asset by ID.
        Useful when an external valuation service provides a more accurate value.
        """
        if session is None:
            async for s in get_db_session():
                return await self._update_asset_value_in_session(asset_id, new_value, s)
        else:
            return await self._update_asset_value_in_session(asset_id, new_value, session)

    async def _update_asset_value_in_session(
        self, asset_id: int, new_value: float, session: Session
    ) -> UserAsset | None:
        """Internal helper to update asset value in session"""
        try:
            statement = select(UserAsset).where(UserAsset.id == asset_id)
            result = await session.execute(statement)
            asset = result.scalar_one_or_none()

            if not asset:
                logger.warning(f"Asset with ID {asset_id} not found for update")
                return None

            old_value = asset.value
            asset.value = new_value
            asset.updated_at = datetime.now()
            
            # Update metadata to reflect source of update
            if not asset.extra_data:
                asset.extra_data = {}
            # Use extra_data for legacy compatibility if metadata not available on model
            # Note: UserAsset model has 'extra_data' (JSON), not 'metadata' field directly visible in some views
            # But the code above uses asset.metadata which might be an alias or dynamic attr?
            # Looking at UserAsset definition: extra_data: dict | None = Field(sa_type=JSON...)
            # The existing code in _update_asset_from_extracted uses asset.metadata. 
            # Wait, let's check UserAsset definition again. 
            # It has 'extra_data'. The 'metadata' access in _update_asset_from_extracted might be wrong or I missed a property.
            # Actually, looking at `_create_asset_from_extracted`, it passed `metadata=metadata` to constructor?
            # Let me check UserAsset model again.
            # UserAsset has: id, user_id, asset_type, name, value, is_confirmed, extra_data...
            # Ah, `_create_asset_from_extracted` uses 'metadata' arg... but UserAsset definition shows `extra_data`.
            # If `UserAsset` doesn't have `metadata` field, the existing code `asset.metadata` would fail unless it's a property.
            # I should use `extra_data`.
            
            if not asset.extra_data:
                asset.extra_data = {}
                
            asset.extra_data.update({
                "last_valuation_update": datetime.now().isoformat(),
                "valuation_source": "system_valuation",
                "previous_value": old_value
            })

            session.add(asset)
            await session.commit()
            await session.refresh(asset)
            
            logger.info(f"Updated asset {asset_id} value: {old_value} -> {new_value}")
            return asset
            
        except Exception as e:
            logger.error(f"Error updating asset {asset_id}: {e}")
            await session.rollback()
            return None

    async def update_user_state(self, user_id: int, extraction_result: dict) -> bool:
        """
        Phase 2: Update user state based on extraction results.
        
        Args:
            user_id: The user ID
            extraction_result: Dict from extract_information() containing assets, goals, risk_profile, completeness_update
            
        Returns:
            bool: True if update was successful
        """
        logger.info(f"🚀 UPDATE_USER_STATE: Starting update_user_state for user {user_id}")
        logger.info(f"🚀 UPDATE_USER_STATE: extraction_result = {extraction_result}")
        
        try:
            async for session in get_db_session():
                success = await self._update_user_state_in_session(user_id, extraction_result, session)
                logger.info(f"🚀 UPDATE_USER_STATE: Result = {success} for user {user_id}")
                return success
        except Exception as e:
            logger.error(f"🚀 UPDATE_USER_STATE: Error updating user state for user {user_id}: {e}")
            return False
    
    async def _update_user_state_in_session(self, user_id: int, extraction_result: dict, session: Session) -> bool:
        """Update user state within a database session"""
        try:
            # L1 Update: Process assets
            assets_data = extraction_result.get("assets", [])
            if assets_data:
                await self._update_assets_from_extraction(user_id, assets_data, session)
            
            # L2 Update: Process cognition data
            await self._update_cognition_from_extraction(user_id, extraction_result, session)
            
            # Commit after both L1 and L2 updates
            await session.commit()
            logger.info(f"🚀 UPDATE_USER_STATE: ✅ Successfully committed all updates for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"🚀 UPDATE_USER_STATE: ❌ Error in state update session for user {user_id}: {e}")
            import traceback
            logger.error(f"🚀 UPDATE_USER_STATE: Traceback: {traceback.format_exc()}")
            await session.rollback()
            return False
    
    async def _update_assets_from_extraction(self, user_id: int, assets_data: list, session: Session):
        """L1 Update: Upsert assets to UserAsset table with improved duplicate handling"""
        
        asset_type_mapping = {
            "real_estate": AssetType.REAL_ESTATE,
            "cash": AssetType.CASH,
            "investment": AssetType.INVESTMENT,
            "insurance": AssetType.INSURANCE,
            "liability": AssetType.LIABILITY,
        }
        
        for asset_data in assets_data:
            try:
                asset_type_str = asset_data.get("type")
                asset_type = asset_type_mapping.get(asset_type_str)
                
                if not asset_type:
                    logger.warning(f"Unknown asset type: {asset_type_str}")
                    continue
                
                # FIXED: Try to get 'value' first (correct field from extraction), then 'amount'
                raw_value = asset_data.get("value")
                if raw_value is None:
                    raw_value = asset_data.get("amount")
                
                name = asset_data.get("name", f"{asset_type_str}资产")
                location = asset_data.get("location")
                # Fallback to metadata if location is missing
                if not location and isinstance(asset_data.get("metadata"), dict):
                    location = asset_data.get("metadata").get("location")
                
                area = asset_data.get("area")

                # Default to 0.0 if no value provided (better than 1 placeholder)
                amount = float(raw_value) if raw_value is not None else 0.0
                if amount < 0:
                    amount = 0.0
                
                # FIXED: Auto-valuation for Real Estate if amount is 0
                valuation_source = "extraction"
                if asset_type == AssetType.REAL_ESTATE and amount <= 0:
                    try:
                        from app.services.property_valuation import get_property_valuation_service
                        valuation_service = get_property_valuation_service()
                        
                        # Generate location string for valuation
                        val_location = location or name or ""
                        if "市" not in val_location and "区" not in val_location:
                             val_location = f"{val_location} (Unknown City)"
                        
                        valuation = await valuation_service.get_market_value(
                            location=val_location,
                            area=area if area and area > 0 else 100,
                            property_type="residential"
                        )
                        if valuation.value > 0:
                            amount = valuation.value
                            valuation_source = f"auto_{valuation.source}"
                            logger.info(f"🏠 Auto-valued UserAsset '{name}': {amount} (source={valuation_source})")
                    except Exception as e:
                        logger.warning(f"Failed to auto-value UserAsset '{name}': {e}")
                
                # FIXED: Improved duplicate detection with fine-grained matching
                # Create temp ExtractedAsset for matching
                temp_extracted_asset = ExtractedAsset(
                     asset_type=asset_type_str,
                     name=name,
                     value=amount,
                     extracted_from="update_user_state",
                     location=location,
                     area=area,
                     confidence=0.9
                )
                
                existing_asset = await self._find_similar_asset(
                    user_id, temp_extracted_asset, session
                )
                
                if existing_asset:
                    # Update existing asset
                    logger.info(f"[Workflow:AssetCollection] Step 2.2: Found similar asset (id={existing_asset.id}), updating instead of creating new")
                    
                    # FIXED: Only update value if we have a valid non-zero amount
                    # This prevents background extraction (which often misses value) from overwriting 
                    # values set by synchronous extraction or user input
                    if amount > 0:
                        existing_asset.value = amount
                        logger.info(f"Updated existing asset value: {name} = {amount}")
                    else:
                        logger.info(f"Skipping value update for {name} (amount={amount}), keeping original: {existing_asset.value}")
                        
                    existing_asset.name = name
                    
                    # Update metadata
                    if not existing_asset.extra_data:
                        existing_asset.extra_data = {}
                    
                    if location:
                        existing_asset.extra_data["location"] = location
                    if area:
                        existing_asset.extra_data["area"] = area
                    
                    # Record valuation source if auto-valued
                    if valuation_source != "extraction":
                        existing_asset.extra_data["valuation_source"] = valuation_source
                        existing_asset.extra_data["last_valuation_update"] = datetime.now().isoformat()
                    
                    existing_asset.extra_data["last_updated"] = datetime.now().isoformat()
                    existing_asset.updated_at = datetime.now()
                    session.add(existing_asset)
                    
                else:
                    # Create new asset
                    extra_data = {}
                    if location:
                        extra_data["location"] = location
                    if area:
                        extra_data["area"] = area
                        
                    # Record valuation source if auto-valued
                    if valuation_source != "extraction":
                        extra_data["valuation_source"] = valuation_source
                        extra_data["last_valuation_update"] = datetime.now().isoformat()
                        
                    extra_data["created_from_extraction"] = True
                    extra_data["extraction_timestamp"] = datetime.now().isoformat()
                    
                    new_asset = UserAsset(
                        user_id=user_id,
                        asset_type=asset_type,
                        name=name,
                        value=amount,
                        is_confirmed=False,  # Needs user confirmation
                        extra_data=extra_data
                    )
                    
                    session.add(new_asset)
                    logger.info(f"[Workflow:AssetCollection] Step 2.2: Created new asset: {name} = {amount}")
                    
            except Exception as e:
                logger.error(f"Error processing asset {asset_data}: {e}")
                continue
    
    
    def _is_name_similar(self, name1: str, name2: str) -> bool:
        """
        Check if two asset names are similar.
        
        Strategy:
        - Normalize: lowercase, remove spaces
        - Check if one is substring of the other
        - Or if they share significant common words
        """
        # Normalize names
        n1 = name1.lower().replace(" ", "")
        n2 = name2.lower().replace(" ", "")
        
        # Substring match
        if n1 in n2 or n2 in n1:
            return True
        
        # Word-based similarity (for Chinese and English)
        # Split by common delimiters
        import re
        words1 = set(re.findall(r'[\w]+', name1.lower()))
        words2 = set(re.findall(r'[\w]+', name2.lower()))
        
        # Remove very short words (likely not meaningful)
        words1 = {w for w in words1 if len(w) > 1}
        words2 = {w for w in words2 if len(w) > 1}
        
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2
        
        if len(union) == 0:
            return False
        
        similarity = len(intersection) / len(union)
        
        # Consider similar if >50% overlap
        return similarity > 0.5
    
    async def _update_cognition_from_extraction(self, user_id: int, extraction_result: dict, session: Session):
        """
        L2 Update: Update UserCognition with goals, risk profile, and collection status
        
        IMPORTANT: L2 layer stores AI's psychological analysis and decision-making data.
        Basic profile fields (age_range, family_structure, etc.) are stored in L1 (UserProfile).
        L2 only stores psychological traits and sentiment analysis.
        """
        
        logger.info(f"Starting _update_cognition_from_extraction for user {user_id} with result: {extraction_result}")
        
        # Get or create UserCognition record
        cognition_statement = select(UserCognition).where(UserCognition.user_id == user_id)
        cognition_result = await session.execute(cognition_statement)
        cognition = cognition_result.scalar_one_or_none()
        
        if not cognition:
            cognition = UserCognition(user_id=user_id)
            session.add(cognition)
        
        # Update financial goals
        goals = extraction_result.get("goals", [])
        if goals:
            if not cognition.financial_goals:
                cognition.financial_goals = []
            
            # Add new goals (avoid duplicates)
            for goal in goals:
                if goal not in cognition.financial_goals:
                    cognition.financial_goals.append(goal)
            
            logger.info(f"Updated financial goals for user {user_id}: {cognition.financial_goals}")
        
        # FIXED: Update risk profile - ONLY store psychological analysis data
        # Basic profile fields (age_range, family_structure, monthly_expense, occupation, income_range)
        # are now stored in L1 (UserProfile) and should NOT be duplicated here
        risk_profile = extraction_result.get("risk_profile", {})
        if risk_profile:
            if not cognition.risk_profile:
                cognition.risk_profile = {}
            
            # ONLY store psychological/sentiment analysis fields in L2
            psychological_fields = [
                "tolerance",           # Risk tolerance (from extraction or analysis)
                "decision_style",      # Decision making style (from Phase 3 analysis)
                "confidence_level",    # User's confidence level (from Phase 3 analysis)
                "current_sentiment",   # Current emotional state (from Phase 3 analysis)
                "loss_aversion",       # Loss aversion level (from Phase 3 analysis)
                "uncertainty_tolerance", # Uncertainty tolerance (from Phase 3 analysis)
                "financial_literacy",  # Financial knowledge level (from Phase 3 analysis)
                "family_responsibility", # Family responsibility sense (from Phase 3 analysis)
                "planning_horizon",    # Planning time horizon (from Phase 3 analysis)
                "last_analysis"        # Timestamp of last analysis
            ]
            
            # Only update psychological fields, ignore basic profile fields
            for key, value in risk_profile.items():
                if key in psychological_fields and value:
                    cognition.risk_profile[key] = value
                elif key not in psychological_fields:
                    # Log that we're skipping basic profile fields (they belong in L1)
                    logger.debug(f"Skipping basic profile field '{key}' - belongs in L1 (UserProfile)")
            
            logger.info(f"Updated risk profile (L2 psychological data) for user {user_id}: {cognition.risk_profile}")
        
        # Also update UserProfile table with basic fields (L1 layer)
        await self._update_user_profile_from_extraction(user_id, risk_profile, session)
        
        # Update collection status
        completeness_update = extraction_result.get("completeness_update", {})
        logger.info(f"Processing completeness_update for user {user_id}: {completeness_update}")
        
        if completeness_update:
            if not cognition.collection_status:
                cognition.collection_status = {}
            
            logger.info(f"Current collection_status before update: {cognition.collection_status}")
            
            # Update collection status for each asset type
            # IMPORTANT: Only update items that are True, preserve existing True values
            collection_status_changed = False
            for asset_type, is_collected in completeness_update.items():
                logger.info(f"Processing {asset_type}: {is_collected} for user {user_id}")
                if is_collected:  # Only mark as collected if True
                    cognition.collection_status[asset_type] = True
                    collection_status_changed = True
                    logger.info(f"Marked {asset_type} as collected for user {user_id}")
                # Do NOT set to False if already True - preserve existing collection status
            
            # CRITICAL: Tell SQLAlchemy that the JSON field has been modified
            if collection_status_changed:
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(cognition, 'collection_status')
                logger.info(f"✅ COGNITION_UPDATE: Flagged collection_status as modified for SQLAlchemy")
                
                # ✅ FIXED: Use await for async flush
                session.add(cognition)
                await session.flush()  # Force immediate write to ensure change is recognized
                logger.info(f"✅ COGNITION_UPDATE: Flushed cognition changes to database")
            
            logger.info(f"Final collection_status after update: {cognition.collection_status}")
        else:
            logger.info(f"No completeness_update provided for user {user_id}")
        
        # Update timestamp
        cognition.updated_at = datetime.now()
        session.add(cognition)
        logger.info(f"Added cognition to session for user {user_id}")
    
    async def _update_user_profile_from_extraction(self, user_id: int, risk_profile: dict, session: Session):
        """Update UserProfile table with basic profile fields (age_range, family_structure, monthly_expense, risk_preference, occupation, income_range)"""
        
        if not risk_profile:
            return
        
        logger.info(f"Updating UserProfile for user {user_id} with risk_profile: {risk_profile}")
        
        # CRITICAL FIX: Check if user exists first to avoid foreign key constraint error
        from app.models.user import User
        user_statement = select(User).where(User.id == user_id)
        user_result = await session.execute(user_statement)
        user_exists = user_result.scalar_one_or_none()
        
        if not user_exists:
            logger.error(f"❌ PROFILE_UPDATE_BLOCKED: User {user_id} does not exist in database")
            logger.error("This is likely a test using a non-existent user ID")
            logger.error("Available users can be checked with: SELECT id, phone FROM user LIMIT 10")
            # ✅ FIX: Raise exception instead of silent return to surface the issue
            raise ValueError(f"User {user_id} does not exist - cannot update UserProfile")
        
        # Get or create UserProfile record
        profile_statement = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await session.execute(profile_statement)
        profile = profile_result.scalar_one_or_none()
        
        # Check if we have any fields to update
        has_updates = False
        
        if not profile:
            # Create profile with "unknown" for missing required fields
            # This allows profile creation even when some info is not yet extracted
            age_range = risk_profile.get("age_range")
            family_structure = risk_profile.get("family_structure")
            risk_preference = risk_profile.get("tolerance")
            occupation = risk_profile.get("occupation")
            income_range = risk_profile.get("income_range")
            monthly_expense = risk_profile.get("monthly_expense")
            
            # ✅ FIX: Use "unknown" for missing required fields instead of fake defaults
            # This is honest - we don't know the user's age/family structure yet
            # Create profile if we have at least one meaningful field
            if any([age_range, family_structure, risk_preference, occupation, income_range, monthly_expense]):
                try:
                    # Map risk_preference string to RiskLevel enum
                    from app.models.user import RiskLevel
                    risk_level_mapping = {
                        "conservative": RiskLevel.CONSERVATIVE,
                        "moderate": RiskLevel.MODERATE,
                        "aggressive": RiskLevel.AGGRESSIVE,
                        "unknown": RiskLevel.UNKNOWN,
                    }
                    mapped_risk_preference = risk_level_mapping.get(
                        risk_preference, RiskLevel.UNKNOWN
                    ) if risk_preference else RiskLevel.UNKNOWN
                    
                    profile = UserProfile(
                        user_id=user_id,
                        age_range=age_range or "unknown",  # ✅ Use "unknown" instead of "30-40"
                        family_structure=family_structure or "unknown",  # ✅ Use "unknown" instead of "single"
                        risk_preference=mapped_risk_preference,  # ✅ Use RiskLevel enum
                        monthly_expense=monthly_expense,
                        occupation=occupation,
                        income_range=income_range
                    )
                    session.add(profile)
                    has_updates = True
                    logger.info(f"Created new UserProfile for user {user_id}")
                    logger.info(f"  - age_range: {profile.age_range} {'(unknown - not yet provided)' if not age_range else ''}")
                    logger.info(f"  - family_structure: {profile.family_structure} {'(unknown - not yet provided)' if not family_structure else ''}")
                    logger.info(f"  - risk_preference: {profile.risk_preference} {'(unknown - not yet provided)' if not risk_preference else ''}")
                    logger.info(f"  - occupation: {occupation}")
                    logger.info(f"  - income_range: {income_range}")
                except Exception as e:
                    logger.error(f"Failed to create UserProfile for user {user_id}: {e}")
                    return
            else:
                logger.info(f"Skipping UserProfile creation - no useful fields provided")
        else:
            # Update existing profile fields
            # IMPORTANT: Only update if new value is provided AND is not "unknown"
            # This prevents later extraction results from overwriting meaningful values
            
            new_age_range = risk_profile.get("age_range")
            if new_age_range and new_age_range != "unknown":
                # Only update if current value is unknown or new value is different
                if profile.age_range == "unknown" or profile.age_range != new_age_range:
                    profile.age_range = new_age_range
                    has_updates = True
                    logger.info(f"Updated age_range for user {user_id}: {profile.age_range}")
            
            new_family_structure = risk_profile.get("family_structure")
            if new_family_structure and new_family_structure != "unknown":
                if profile.family_structure == "unknown" or profile.family_structure != new_family_structure:
                    profile.family_structure = new_family_structure
                    has_updates = True
                    logger.info(f"Updated family_structure for user {user_id}: {profile.family_structure}")
            
            new_tolerance = risk_profile.get("tolerance")
            if new_tolerance and new_tolerance != "unknown":
                # Map tolerance string to RiskLevel enum
                from app.models.user import RiskLevel
                risk_level_mapping = {
                    "conservative": RiskLevel.CONSERVATIVE,
                    "moderate": RiskLevel.MODERATE,
                    "aggressive": RiskLevel.AGGRESSIVE,
                    "unknown": RiskLevel.UNKNOWN,
                }
                new_risk_preference = risk_level_mapping.get(new_tolerance, RiskLevel.UNKNOWN)
                # Only update if current is UNKNOWN or new value is different
                if profile.risk_preference == RiskLevel.UNKNOWN or profile.risk_preference != new_risk_preference:
                    profile.risk_preference = new_risk_preference
                    has_updates = True
                    logger.info(f"Updated risk_preference for user {user_id}: {profile.risk_preference}")
            
            if risk_profile.get("monthly_expense") is not None:
                profile.monthly_expense = risk_profile["monthly_expense"]
                has_updates = True
            
            new_occupation = risk_profile.get("occupation")
            if new_occupation and new_occupation != "unknown":
                profile.occupation = new_occupation
                has_updates = True
                logger.info(f"Updated occupation for user {user_id}: {profile.occupation}")
            
            new_income_range = risk_profile.get("income_range")
            if new_income_range and new_income_range != "unknown":
                profile.income_range = new_income_range
                has_updates = True
                logger.info(f"Updated income_range for user {user_id}: {profile.income_range}")
            
            if has_updates:
                session.add(profile)
                logger.info(f"Updated UserProfile for user {user_id}")
        
        if has_updates:
            logger.info(f"UserProfile changes will be committed for user {user_id}")
        else:
            logger.info(f"No UserProfile updates needed for user {user_id}")

    async def get_user_assets(self, user_id: int) -> list[dict[str, Any]]:
        """
        Get all assets for a user in a format suitable for Context.
        Used to refresh context after synchronous extraction.
        
        Args:
            user_id: The user ID
            
        Returns:
            list[dict]: List of asset dictionaries
        """
        from app.core.database import get_db_session
        
        try:
            async for session in get_db_session():
                statement = select(UserAsset).where(UserAsset.user_id == user_id)
                result = await session.execute(statement)
                assets = result.scalars().all()
                
                return [
                    {
                        "id": asset.id,
                        "type": asset.asset_type.value,
                        "name": asset.name,
                        "value": asset.value,
                        "is_confirmed": asset.is_confirmed,
                        "extra_data": asset.extra_data,
                    }
                    for asset in assets
                ]
        except Exception as e:
            logger.error(f"Error getting user assets: {e}")
            return []
        return []

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
