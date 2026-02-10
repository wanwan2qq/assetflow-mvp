import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_session
from app.services.asset_extraction_service import AssetExtractionService
from app.services.information_extraction import ExtractedAsset, AssetType
from app.services.portfolio_analyzer import PortfolioAnalyzer
from app.models.wealth import CashFlowItem, AssetValuationHistory, FlowType, Frequency
from sqlmodel import select, delete
from app.models.user import User, UserAsset

async def verify_wealth_upgrade():
    print("🚀 Starting Wealth Management Upgrade Verification...")
    
    extraction_service = AssetExtractionService()
    analyzer = PortfolioAnalyzer()
    
    async for session in get_db_session():
        try:
            # 1. Setup Test User
            print("\n1. Setting up test user...")
            # Check for existing test user
            stmt = select(User).where(User.phone == "19999999999")
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(phone="19999999999")
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(f"Created test user: {user.id}")
            else:
                print(f"Using existing test user: {user.id}")
                
            # Clean up old test data if any
            # Delete cash flows linked to this user
            stmt = select(CashFlowItem).where(CashFlowItem.user_id == user.id)
            result = await session.execute(stmt)
            existing_cfs = result.scalars().all()
            for cf in existing_cfs:
                session.delete(cf)
                
            # Delete assets linked to this user (cascade should handle valuation history if set up, but safe to delete manually if needed)
            stmt = select(UserAsset).where(UserAsset.user_id == user.id)
            result = await session.execute(stmt)
            assets = result.scalars().all()
            for asset in assets:
                # Delete valuation history for asset
                stmt_hist = select(AssetValuationHistory).where(AssetValuationHistory.asset_id == asset.id)
                res_hist = await session.execute(stmt_hist)
                histories = res_hist.scalars().all()
                for h in histories:
                    session.delete(h)
                session.delete(asset)
            
            await session.commit()
            print("Cleaned up old test data.")

            # 2. Simulate Extraction with Smart Defaults and Cash Flows
            print("\n2. Simulating Extraction...")
            
            # Case A: Real Estate with Rental Income (Cash Flow) and No Interest Rate (Smart Default will fix liability if it was liability, but here it's RE asset)
            # Wait, Smart Default for interest rate is for LIABILITY.
            # Let's test a dual extraction: One RE asset, One Liability, One Salary.
            
            # Asset 1: Rental Property
            rental_property = ExtractedAsset(
                asset_type=AssetType.REAL_ESTATE,
                name="Test Rental Apt",
                value=2000000.0,
                location="Test City",
                confidence=0.9,
                extracted_from="test_script",
                cash_flows=[{
                    "name": "Rental Income",
                    "amount": 5000,
                    "flow_type": "income",
                    "frequency": "monthly"
                }]
            )
            
            # Asset 2: Mortgage (Liability) - Testing Smart Default (Missing interest rate)
            mortgage = ExtractedAsset(
                asset_type=AssetType.LIABILITY,
                name="Apt Mortgage",
                value=1000000.0,
                confidence=0.8,
                extracted_from="test_script",
                metadata={} # Missing interest rate
            )
            
            # Apply Smart Defaults manually here to simulate what InformationExtractor would do?
            # No, InformationExtractor calls _apply_smart_defaults internally.
            # But here we are calling AssetExtractionService directly using ExtractedAsset objects.
            # If we want to test _apply_smart_defaults, we should use InformationExtractor or call the private method if possible.
            # However, `store_extracted_assets` receives `ExtractedAsset`s that are ALREADY processed by `InformationExtractor`.
            # So `AssetExtractionService` doesn't apply defaults. `InformationExtractor` does.
            # To Verify Smart Defaults logic, I should technically call `InformationExtractor`.
            # But `InformationExtractor` needs LLM or fallback.
            # I can manually apply the defaults here to simulate the "output of InformationExtractor" OR I can import InformationExtractor and use `_apply_smart_defaults`.
            
            from app.services.information_extraction import InformationExtractor
            extractor = InformationExtractor()
            extractor._apply_smart_defaults(mortgage) # Simulate the extraction step
            print(f"Smart Default Applied to Mortgage: Interest Rate = {mortgage.metadata.get('interest_rate')}")
            
            # 3. Store Assets
            print("\n3. Storing Assets...")
            stored_assets = await extraction_service.store_extracted_assets(
                user_id=user.id,
                extracted_assets=[rental_property, mortgage],
                session=session
            )
            
            await session.commit()
            
            # 4. Verify Database Records
            print("\n4. Verifying Database Records...")
            
            # Check Assets
            stmt = select(UserAsset).where(UserAsset.user_id == user.id)
            result = await session.execute(stmt)
            db_assets = result.scalars().all()
            print(f"Found {len(db_assets)} assets in DB.")
            
            rental_asset = next((a for a in db_assets if a.name == "Test Rental Apt"), None)
            mortgage_asset = next((a for a in db_assets if a.name == "Apt Mortgage"), None)
            
            assert rental_asset is not None
            assert mortgage_asset is not None
            
            # Check Cash Flows
            stmt = select(CashFlowItem).where(CashFlowItem.user_id == user.id)
            result = await session.execute(stmt)
            cash_flows = result.scalars().all()
            print(f"Found {len(cash_flows)} cash flow items.")
            
            rental_income = next((cf for cf in cash_flows if cf.name == "Rental Income"), None)
            assert rental_income is not None
            assert rental_income.related_asset_id == rental_asset.id
            assert rental_income.amount == 5000
            print("✅ Cash Flow linked correctly.")
            
            # Check Valuation History
            stmt = select(AssetValuationHistory).where(AssetValuationHistory.asset_id == rental_asset.id)
            result = await session.execute(stmt)
            history = result.scalars().all()
            print(f"Found {len(history)} valuation history entries for rental asset.")
            assert len(history) >= 1
            print("✅ Valuation History created.")
            
            # Check Smart Default Persistence
            print(f"Mortgage Extra Data: {mortgage_asset.extra_data}")
            assert mortgage_asset.extra_data.get("interest_rate") == 4.2
            print("✅ Smart Default persisted.")
            
            # 5. Verify Portfolio Analyzer
            print("\n5. Verifying Portfolio Analyzer...")
            
            # Projected Cash Flow
            projection = await analyzer.calculate_projected_cashflow(user.id, session)
            print(f"Projected Cash Flow: {projection}")
            assert projection["total_income"] == 5000 * 12
            print("✅ Projected Cash Flow correct.")
            
            print("\n🎉 ALL VERIFICATION STEPS PASSED!")
            
        except Exception as e:
            print(f"\n❌ VERIFICATION FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_wealth_upgrade())
