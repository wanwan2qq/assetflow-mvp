import asyncio
import logging
from app.core.database import get_db_session
from app.models.real_estate import RealEstateAsset
from app.models.user import User
from sqlmodel import select
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_name_similar(name1: str, name2: str) -> bool:
    """Check similarity using Jaccard index on words (copied from ConversationOrchestrator)."""
    import re
    # Normalize
    n1 = name1.lower().replace(" ", "")
    n2 = name2.lower().replace(" ", "")
    
    # Substring match shortcut
    if n1 in n2 or n2 in n1:
        return True
        
    # Word tokenization
    words1 = set(re.findall(r'[\w]+', name1.lower()))
    words2 = set(re.findall(r'[\w]+', name2.lower()))
    
    # Remove short words
    words1 = {w for w in words1 if len(w) > 1}
    words2 = {w for w in words2 if len(w) > 1}
    
    if not words1 or not words2:
        return False
        
    intersection = words1 & words2
    union = words1 | words2
    
    if not union:
        return False
        
    similarity = len(intersection) / len(union)
    return similarity > 0.5

def check_similarity(asset1: RealEstateAsset, asset2: RealEstateAsset) -> bool:
    """Check if two assets are similar enough to be duplicates."""
    # Normalize data
    name1 = asset1.name
    loc1 = f"{asset1.city or ''}{asset1.district or ''}{asset1.address or ''}"
    loc1_norm = loc1.replace(" ", "").lower()
    name1_norm = name1.replace(" ", "").lower()
    
    name2 = asset2.name
    loc2 = f"{asset2.city or ''}{asset2.district or ''}{asset2.address or ''}"
    loc2_norm = loc2.replace(" ", "").lower()
    name2_norm = name2.replace(" ", "").lower()
    
    # MATCH 1: Location overlap
    if loc1_norm and loc2_norm:
        if loc1_norm in loc2_norm or loc2_norm in loc1_norm:
            return True

    # MATCH 2: Name overlap
    if name1_norm in name2_norm or name2_norm in name1_norm:
        return True
    
    # MATCH 3: Cross-field
    if loc1_norm and name2_norm:
        if loc1_norm in name2_norm or name2_norm in loc1_norm:
            return True
    if name1_norm and loc2_norm:
        if name1_norm in loc2_norm or loc2_norm in name1_norm:
            return True
            
    # MATCH 4: Area exact match
    if asset1.area and asset2.area:
        if abs(asset1.area - asset2.area) < 5:
            return True
            
    # MATCH 5: Fuzzy name
    if is_name_similar(name1, name2):
        return True
        
    return False

async def main():
    logger.info("Starting cleanup of redundant RealEstateAsset entries...")
    
    async for session in get_db_session():
        # Get all users
        users = (await session.execute(select(User))).scalars().all()
        logger.info(f"Found {len(users)} users.")
        
        total_duplicates_removed = 0
        
        for user in users:
            # Get properties for user
            stmt = select(RealEstateAsset).where(RealEstateAsset.user_id == user.id)
            properties = (await session.execute(stmt)).scalars().all()
            
            if not properties:
                continue
                
            logger.info(f"User {user.id}: Found {len(properties)} properties.")
            
            # Find clusters
            visited = set()
            clusters = []
            
            for i, p1 in enumerate(properties):
                if p1.id in visited:
                    continue
                
                cluster = [p1]
                visited.add(p1.id)
                
                for j in range(i + 1, len(properties)):
                    p2 = properties[j]
                    if p2.id in visited:
                        continue
                        
                    if check_similarity(p1, p2):
                        cluster.append(p2)
                        visited.add(p2.id)
                
                if len(cluster) > 1:
                    clusters.append(cluster)
            
            # Process clusters
            for cluster in clusters:
                logger.info(f"Found cluster of {len(cluster)} duplicates for User {user.id}: {[p.name for p in cluster]}")
                
                # Sort by info completeness (prioritize loan info, then ID)
                # Score: 100 if has loan balance, +10 if has monthly payment, +1 if newest ID (or oldest? prefer newest usually unless legacy)
                # Actually we prefer the one with most fields filled.
                
                def score_asset(a):
                    score = 0
                    if a.loan_balance > 0: score += 100
                    if a.monthly_payment > 0: score += 50
                    if a.purchase_price and a.purchase_price > 0: score += 20
                    if a.net_equity: score += 10
                    return score
                
                # Sort descending by score, then by ID (latest first)
                cluster.sort(key=lambda a: (score_asset(a), a.id), reverse=True)
                
                survivor = cluster[0]
                duplicates = cluster[1:]
                
                logger.info(f"  Survivor: {survivor.name} (ID: {survivor.id})")
                
                # Merge data from duplicates to survivor if survivor has missing data
                fields_to_merge = [
                    'city', 'district', 'address', 'year_built', 
                    'purchase_price', 'purchase_date', 
                    'loan_type', 'loan_balance', 'monthly_payment', 'loan_rate', 'loan_remaining_months',
                    'monthly_rent', 'rental_yield',
                    'mortgage_potential', 'net_equity', 'extra_data', 'legacy_asset_id'
                ]
                
                changed = False
                for dup in duplicates:
                    logger.info(f"  Removing duplicate: {dup.name} (ID: {dup.id})")
                    
                    # Merge logic
                    for field in fields_to_merge:
                        survivor_val = getattr(survivor, field)
                        dup_val = getattr(dup, field)
                        
                        # If survivor is empty/zero but duplicate has value, take it
                        is_survivor_empty = survivor_val is None or survivor_val == "" or (isinstance(survivor_val, (int, float)) and survivor_val == 0)
                        is_dup_valid = dup_val is not None and dup_val != "" and (not isinstance(dup_val, (int, float)) or dup_val != 0)
                        
                        if is_survivor_empty and is_dup_valid:
                            setattr(survivor, field, dup_val)
                            changed = True
                            logger.info(f"    Merged field {field}: {dup_val}")
                    
                    await session.delete(dup)
                    total_duplicates_removed += 1
                
                if changed:
                    survivor.update_financial_attributes()
                    session.add(survivor)
                    
        await session.commit()
        logger.info(f"Cleanup complete. Removed {total_duplicates_removed} duplicate assets.")

if __name__ == "__main__":
    asyncio.run(main())
