"""
Portfolio analysis service based on Standard & Poor's Four Quadrant Model
"""

import logging
from enum import Enum
from typing import Any

from app.models.user import AssetType, UserAsset, UserProfile

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SPQuadrant(str, Enum):
    """Standard & Poor's Four Quadrant Model (Phase 2 升级版)"""

    SPENDING_MONEY = "spending"  # 要花的钱 (3-6个月生活费)
    LIFE_MONEY = "life"  # 保命的钱 (保险保障)
    GROWTH_MONEY = "growth"  # 生钱的钱 (高风险投资)
    PRESERVATION_MONEY = "preservation"  # 保本升值的钱 (稳健投资)
    
    # Phase 2 新增: 核心锚点资产 (自住房)
    ANCHOR_ASSET = "anchor"  # 锚点资产 (自住房产)


class AssetTaxonomy:
    """Asset classification taxonomy with normalized subtypes and risk levels"""

    # Low-risk investment subtypes (Preservation Money)
    LOW_RISK_SUBTYPES = frozenset([
        "bond",
        "money_fund",
        "债券",
        "货币基金",
        "国债",
        "定期存款",
        "银行理财",
    ])

    # Medium-risk investment subtypes
    MEDIUM_RISK_SUBTYPES = frozenset([
        "balanced_fund",
        "混合基金",
        "债券基金",
        "可转债",
    ])

    # High-risk investment subtypes (Growth Money)
    HIGH_RISK_SUBTYPES = frozenset([
        "stock",
        "equity_fund",
        "股票",
        "股票基金",
        "指数基金",
        "etf",
    ])

    # Risk level constants
    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"

    # Liquidity discount factors
    LIQUIDITY_DISCOUNT_REAL_ESTATE = 0.8  # Real estate is illiquid
    LIQUIDITY_DISCOUNT_NONE = 1.0  # Fully liquid assets

    @classmethod
    def normalize_subtype(cls, subtype: str | None) -> str:
        """Normalize asset subtype to lowercase and strip whitespace"""
        if not subtype:
            return ""
        return str(subtype).lower().strip()

    @classmethod
    def get_risk_level_from_subtype(cls, subtype: str) -> str:
        """Determine risk level from normalized subtype"""
        normalized = cls.normalize_subtype(subtype)
        if normalized in cls.LOW_RISK_SUBTYPES:
            return cls.RISK_LOW
        elif normalized in cls.MEDIUM_RISK_SUBTYPES:
            return cls.RISK_MEDIUM
        elif normalized in cls.HIGH_RISK_SUBTYPES:
            return cls.RISK_HIGH
        return cls.RISK_MEDIUM  # Default to medium risk


class AnalysisStatus(str, Enum):
    """Analysis status codes"""

    SUCCESS = "success"
    DATA_INSUFFICIENT = "data_insufficient"
    ERROR = "error"


class PortfolioAnalysis:
    """Portfolio analysis result with Standard & Poor's Four Quadrant Model"""

    def __init__(self):
        self.status: AnalysisStatus = AnalysisStatus.SUCCESS
        self.status_message: str = ""
        self.net_worth: float = 0.0
        self.real_estate_ratio: float = 0.0
        self.liquidity_ratio: float = 0.0
        self.risk_warnings: list[dict[str, Any]] = []
        self.recommendations: list[dict[str, Any]] = []
        self.overall_risk_level: RiskLevel = RiskLevel.MEDIUM

        # Standard & Poor's Four Quadrant Analysis
        self.quadrant_analysis: dict[str, Any] = {}
        self.quadrant_allocations: dict[SPQuadrant, float] = {}
        self.ideal_allocations: dict[SPQuadrant, float] = {}
        self.allocation_gaps: dict[SPQuadrant, float] = {}


class PortfolioAnalyzer:
    """Portfolio analyzer based on Standard & Poor's Four Quadrant Model (Phase 2 升级版)"""

    def __init__(self):
        # Standard risk thresholds (can be adjusted based on user profile)
        self.default_thresholds = {
            "real_estate_max": 0.75,  # 75% max real estate allocation
            "liquidity_min": 3.0,  # 3 months minimum liquidity
            "debt_to_asset_max": 0.4,  # 40% max debt to asset ratio
        }

        # Standard & Poor's Four Quadrant ideal allocations (baseline)
        self.default_sp_allocations = {
            SPQuadrant.SPENDING_MONEY: 0.10,  # 10% - 要花的钱
            SPQuadrant.LIFE_MONEY: 0.20,  # 20% - 保命的钱
            SPQuadrant.GROWTH_MONEY: 0.30,  # 30% - 生钱的钱
            SPQuadrant.PRESERVATION_MONEY: 0.40,  # 40% - 保本升值的钱
        }
        
        # Phase 2: 锚点资产配置
        self.anchor_asset_config = {
            "include_self_occupied_property": True,  # 自住房是否计入锚点
            "anchor_ratio_warning": 0.7,  # 锚点资产占比警告阈值
            "enable_leverage_suggestion": True,  # 是否启用抵押建议
        }

    def analyze_portfolio(
        self, assets: list[UserAsset], user_profile: UserProfile | None = None
    ) -> PortfolioAnalysis:
        """Analyze user's portfolio using Standard & Poor's Four Quadrant Model"""

        analysis = PortfolioAnalysis()

        try:
            # Validate input data
            if not self._validate_analysis_inputs(assets, user_profile, analysis):
                return analysis

            # Calculate basic metrics
            analysis.net_worth = self._calculate_net_worth(assets)
            analysis.real_estate_ratio = self._calculate_real_estate_ratio(
                assets, analysis.net_worth
            )
            analysis.liquidity_ratio = self._calculate_liquidity_ratio(
                assets, user_profile
            )

            # Adjust thresholds based on user profile
            thresholds = self._adjust_thresholds_for_user(user_profile)

            # Standard & Poor's Four Quadrant Analysis
            analysis.ideal_allocations = self._calculate_ideal_sp_allocations(
                user_profile
            )
            analysis.quadrant_allocations = self._classify_assets_by_quadrant(
                assets, user_profile
            )
            analysis.allocation_gaps = self._calculate_allocation_gaps(
                analysis.quadrant_allocations,
                analysis.ideal_allocations,
                analysis.net_worth,
            )
            analysis.quadrant_analysis = self._generate_quadrant_analysis(
                analysis.quadrant_allocations,
                analysis.ideal_allocations,
                analysis.net_worth,
                assets,
                user_profile,
            )

            # Generate risk warnings (enhanced with quadrant analysis)
            analysis.risk_warnings = self._generate_risk_warnings(
                analysis, assets, thresholds
            )

            # Generate recommendations (enhanced with quadrant-based suggestions)
            analysis.recommendations = self._generate_recommendations(
                analysis, assets, user_profile, thresholds
            )

            # Determine overall risk level
            analysis.overall_risk_level = self._determine_overall_risk_level(analysis)

            analysis.status = AnalysisStatus.SUCCESS

        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}", exc_info=True)
            analysis.status = AnalysisStatus.ERROR
            analysis.status_message = f"分析过程中发生错误: {str(e)}"

        return analysis

    def _validate_analysis_inputs(
        self,
        assets: list[UserAsset],
        user_profile: UserProfile | None,
        analysis: PortfolioAnalysis,
    ) -> bool:
        """Validate inputs for portfolio analysis to prevent division by zero and data issues"""
        # Check if we have any assets
        if not assets:
            analysis.status = AnalysisStatus.DATA_INSUFFICIENT
            analysis.status_message = "没有资产数据，无法进行分析"
            return False

        # Check if monthly expense is valid when provided
        if user_profile and user_profile.monthly_expense is not None:
            if user_profile.monthly_expense <= 0:
                logger.warning(
                    f"Invalid monthly_expense: {user_profile.monthly_expense}, will use estimation"
                )
                # Don't fail, just log warning - we'll estimate instead

        return True

    def _calculate_net_worth(self, assets: list[UserAsset]) -> float:
        """Calculate total net worth: assets - liabilities"""
        total_assets = 0.0
        total_liabilities = 0.0

        for asset in assets:
            if asset.asset_type == AssetType.LIABILITY:
                total_liabilities += asset.value
            else:
                total_assets += asset.value

        return total_assets - total_liabilities

    def _calculate_real_estate_ratio(
        self, assets: list[UserAsset], net_worth: float
    ) -> float:
        """Calculate real estate as percentage of net worth"""
        if net_worth <= 0:
            return 0.0

        real_estate_value = sum(
            asset.value for asset in assets if asset.asset_type == AssetType.REAL_ESTATE
        )

        return real_estate_value / net_worth

    def _calculate_liquidity_ratio(
        self, assets: list[UserAsset], user_profile: UserProfile | None
    ) -> float:
        """Calculate liquidity ratio: cash / monthly expenses"""
        cash_value = sum(
            asset.value for asset in assets if asset.asset_type == AssetType.CASH
        )

        monthly_expense = self._get_monthly_expense(assets, user_profile)

        # Avoid division by zero
        if monthly_expense <= 0:
            logger.warning("Monthly expense is zero or negative, returning 0 liquidity ratio")
            return 0.0

        return cash_value / monthly_expense

    def _get_monthly_expense(
        self, assets: list[UserAsset], user_profile: UserProfile | None
    ) -> float:
        """Get monthly expense from profile or estimate it"""
        if user_profile and user_profile.monthly_expense and user_profile.monthly_expense > 0:
            return user_profile.monthly_expense

        # Use estimated monthly expense based on net worth
        return self._estimate_monthly_expense(assets)

    def _estimate_monthly_expense(self, assets: list[UserAsset]) -> float:
        """Estimate monthly expenses based on asset level"""
        net_worth = self._calculate_net_worth(assets)

        # Avoid negative or zero net worth
        if net_worth <= 0:
            return 0.0

        # Simple estimation: 2-4% of net worth annually, divided by 12
        if net_worth > 10000000:  # > 1000万
            return net_worth * 0.04 / 12
        elif net_worth > 5000000:  # > 500万
            return net_worth * 0.03 / 12
        else:
            return net_worth * 0.02 / 12

    def _get_asset_subtype(self, asset: UserAsset) -> str:
        """
        Safely extract and normalize asset subtype from extra_data.
        Returns normalized lowercase string.
        """
        if not asset.extra_data:
            return ""

        subtype = asset.extra_data.get("subtype", "")
        return AssetTaxonomy.normalize_subtype(subtype)

    def _get_asset_risk_level(self, asset: UserAsset) -> str:
        """
        Safely extract and normalize risk level from extra_data.
        Returns normalized lowercase string.
        """
        if not asset.extra_data:
            return ""

        risk_level = asset.extra_data.get("risk_level", "")
        return AssetTaxonomy.normalize_subtype(risk_level)

    def _adjust_thresholds_for_user(
        self, user_profile: UserProfile | None
    ) -> dict[str, float]:
        """Adjust risk thresholds based on user profile"""
        thresholds = self.default_thresholds.copy()

        if not user_profile:
            return thresholds

        # Adjust based on age - this should be applied first
        # ✅ Skip adjustment if age_range is "unknown"
        if user_profile.age_range and user_profile.age_range != "unknown":
            if (
                "20-30" in user_profile.age_range
                or "25-35" in user_profile.age_range
                or "30-40" in user_profile.age_range
            ):
                # Younger users can take more risk
                thresholds["real_estate_max"] = 0.80
                thresholds["liquidity_min"] = 2.5
            elif (
                "50-60" in user_profile.age_range
                or "55-65" in user_profile.age_range
                or "60+" in user_profile.age_range
            ):
                # Older users should be more conservative
                thresholds["real_estate_max"] = 0.65
                thresholds["liquidity_min"] = 4.0

        # Adjust based on family structure - this can override age adjustments for liquidity
        # ✅ Skip adjustment if family_structure is "unknown"
        if user_profile.family_structure and user_profile.family_structure != "unknown":
            if user_profile.family_structure == "married_with_kids":
                # Families need more liquidity - increase from current threshold
                thresholds["liquidity_min"] = max(
                    thresholds["liquidity_min"], 15.0
                )  # 15 months for families with kids
            elif user_profile.family_structure == "single":
                # Singles can be slightly more aggressive with liquidity only
                thresholds["liquidity_min"] = min(thresholds["liquidity_min"], 2.5)

        # Adjust based on risk preference - more nuanced adjustments
        # ✅ Skip adjustment if risk_preference is "unknown"
        if user_profile.risk_preference and user_profile.risk_preference != "unknown":
            if user_profile.risk_preference == "conservative":
                # Conservative users: stricter thresholds, but respect family structure liquidity needs
                thresholds["real_estate_max"] = min(thresholds["real_estate_max"], 0.60)
                thresholds["liquidity_min"] = max(thresholds["liquidity_min"], 5.0)
            elif user_profile.risk_preference == "aggressive":
                # Aggressive users: more relaxed thresholds, but still respect family structure
                thresholds["real_estate_max"] = max(thresholds["real_estate_max"], 0.80)
                # For liquidity, aggressive users can be more relaxed, but families still need more
                if user_profile.family_structure != "married_with_kids":
                    thresholds["liquidity_min"] = min(thresholds["liquidity_min"], 2.0)

        return thresholds

    def _calculate_ideal_sp_allocations(
        self, user_profile: UserProfile | None
    ) -> dict[SPQuadrant, float]:
        """Calculate ideal Standard & Poor's allocations based on user profile"""
        allocations = self.default_sp_allocations.copy()

        if not user_profile:
            return allocations

        # Start with base allocations and adjust step by step
        # Adjust based on age first
        # ✅ Skip adjustment if age_range is "unknown"
        if user_profile.age_range and user_profile.age_range != "unknown":
            if "20-30" in user_profile.age_range or "25-35" in user_profile.age_range:
                # Young users: more growth, less preservation
                allocations[SPQuadrant.GROWTH_MONEY] = 0.40
                allocations[SPQuadrant.PRESERVATION_MONEY] = 0.30
            elif (
                "50-60" in user_profile.age_range
                or "55-65" in user_profile.age_range
                or "60+" in user_profile.age_range
            ):
                # Older users: more preservation, less growth
                allocations[SPQuadrant.GROWTH_MONEY] = 0.20
                allocations[SPQuadrant.PRESERVATION_MONEY] = 0.50

        # Adjust based on family structure (overrides some age adjustments)
        # ✅ Skip adjustment if family_structure is "unknown"
        if user_profile.family_structure and user_profile.family_structure != "unknown":
            if user_profile.family_structure == "married_with_kids":
                # Families need more emergency funds and life protection
                allocations[SPQuadrant.SPENDING_MONEY] = 0.15  # More emergency funds
                allocations[SPQuadrant.LIFE_MONEY] = 0.25  # More insurance
                allocations[SPQuadrant.GROWTH_MONEY] = 0.25  # Reduce growth
                allocations[SPQuadrant.PRESERVATION_MONEY] = 0.35  # Increase stability
            elif user_profile.family_structure == "single":
                # Singles can be more aggressive
                allocations[SPQuadrant.SPENDING_MONEY] = 0.08
                allocations[SPQuadrant.LIFE_MONEY] = 0.15
                # Keep age-based growth/preservation adjustments for singles

        # Adjust based on risk preference (final override with rebalancing)
        # ✅ Skip adjustment if risk_preference is "unknown"
        if user_profile.risk_preference and user_profile.risk_preference != "unknown":
            if user_profile.risk_preference == "conservative":
                # Conservative users need more safety
                spending = max(allocations[SPQuadrant.SPENDING_MONEY], 0.15)
                life = max(allocations[SPQuadrant.LIFE_MONEY], 0.25)
                growth = 0.15  # Conservative growth
                preservation = 1.0 - spending - life - growth  # Remainder

                allocations[SPQuadrant.SPENDING_MONEY] = spending
                allocations[SPQuadrant.LIFE_MONEY] = life
                allocations[SPQuadrant.GROWTH_MONEY] = growth
                allocations[SPQuadrant.PRESERVATION_MONEY] = max(preservation, 0.40)

            elif user_profile.risk_preference == "aggressive":
                # Aggressive users want more growth
                # ✅ Check family_structure is not "unknown" before using it
                if user_profile.family_structure and user_profile.family_structure != "unknown" and user_profile.family_structure == "married_with_kids":
                    # Families still need minimums
                    spending = 0.15
                    life = 0.25
                    growth = 0.35  # Reduced from 0.45 for families
                    preservation = 0.25
                else:
                    # Singles can be more aggressive
                    spending = 0.08
                    life = 0.15
                    growth = 0.45
                    preservation = 0.32

                allocations[SPQuadrant.SPENDING_MONEY] = spending
                allocations[SPQuadrant.LIFE_MONEY] = life
                allocations[SPQuadrant.GROWTH_MONEY] = growth
                allocations[SPQuadrant.PRESERVATION_MONEY] = preservation

        # Final validation and normalization to ensure sum = 1.0
        total = sum(allocations.values())
        if abs(total - 1.0) > 0.001:
            # Normalize to sum to 1.0
            for quadrant in allocations:
                allocations[quadrant] = allocations[quadrant] / total

        return allocations

    def _classify_assets_by_quadrant(
        self, assets: list[UserAsset], user_profile: UserProfile | None
    ) -> dict[SPQuadrant, float]:
        """Classify assets into Standard & Poor's quadrants (Phase 2 升级版)"""
        quadrant_values = {
            SPQuadrant.SPENDING_MONEY: 0.0,
            SPQuadrant.LIFE_MONEY: 0.0,
            SPQuadrant.GROWTH_MONEY: 0.0,
            SPQuadrant.PRESERVATION_MONEY: 0.0,
            SPQuadrant.ANCHOR_ASSET: 0.0,  # Phase 2: 锚点资产
        }

        monthly_expense = self._get_monthly_expense(assets, user_profile)

        # Calculate monthly debt payment from liabilities
        monthly_debt_payment = self._calculate_monthly_debt_payment(assets)

        # Spending money threshold includes both expenses and debt servicing
        spending_threshold = (monthly_expense + monthly_debt_payment) * 6

        for asset in assets:
            if asset.asset_type == AssetType.LIABILITY:
                continue  # Liabilities are handled separately

            # Classify based on asset type and characteristics
            if asset.asset_type == AssetType.CASH:
                # First 6 months of (expenses + debt) go to spending money
                if quadrant_values[SPQuadrant.SPENDING_MONEY] < spending_threshold:
                    spending_allocation = min(
                        asset.value,
                        spending_threshold - quadrant_values[SPQuadrant.SPENDING_MONEY],
                    )
                    quadrant_values[SPQuadrant.SPENDING_MONEY] += spending_allocation
                    remaining_cash = asset.value - spending_allocation
                    if remaining_cash > 0:
                        # Excess cash goes to preservation
                        quadrant_values[SPQuadrant.PRESERVATION_MONEY] += remaining_cash
                else:
                    # All cash beyond 6 months goes to preservation
                    quadrant_values[SPQuadrant.PRESERVATION_MONEY] += asset.value

            elif asset.asset_type == AssetType.INSURANCE:
                # All insurance goes to life money
                quadrant_values[SPQuadrant.LIFE_MONEY] += asset.value

            elif asset.asset_type == AssetType.REAL_ESTATE:
                # Phase 2: 区分自住房和投资房
                metadata = asset.extra_data if asset.extra_data else {}
                usage = metadata.get("usage", "self_occupied")  # 默认为自住
                
                # 计算净值 (扣除贷款)
                loan_balance = metadata.get("loan_balance", 0) or metadata.get("贷款余额", 0) or 0
                net_value = max(0, asset.value - float(loan_balance))
                
                # Apply liquidity discount factor for real estate
                liquid_value = net_value * AssetTaxonomy.LIQUIDITY_DISCOUNT_REAL_ESTATE
                
                if usage in ["self_occupied", "自住"] and self.anchor_asset_config["include_self_occupied_property"]:
                    # 自住房归入锚点资产
                    quadrant_values[SPQuadrant.ANCHOR_ASSET] += liquid_value
                elif usage in ["rented", "出租"]:
                    # 出租房归入生钱的钱
                    quadrant_values[SPQuadrant.GROWTH_MONEY] += liquid_value
                else:
                    # 其他房产归入保本升值
                    quadrant_values[SPQuadrant.PRESERVATION_MONEY] += liquid_value

            elif asset.asset_type == AssetType.INVESTMENT:
                # Use helper methods for safe metadata access
                risk_level = self._get_asset_risk_level(asset)
                subtype = self._get_asset_subtype(asset)

                # Determine risk level from subtype if not explicitly set
                if not risk_level and subtype:
                    risk_level = AssetTaxonomy.get_risk_level_from_subtype(subtype)

                # Low-risk investments go to preservation
                if risk_level == AssetTaxonomy.RISK_LOW or subtype in AssetTaxonomy.LOW_RISK_SUBTYPES:
                    quadrant_values[SPQuadrant.PRESERVATION_MONEY] += asset.value
                else:
                    # High/medium risk investments go to growth
                    quadrant_values[SPQuadrant.GROWTH_MONEY] += asset.value

        return quadrant_values

    def _calculate_monthly_debt_payment(self, assets: list[UserAsset]) -> float:
        """Calculate estimated monthly debt payment from liabilities"""
        total_debt = sum(
            asset.value for asset in assets if asset.asset_type == AssetType.LIABILITY
        )

        # Check if any liability has specific payment info in metadata
        monthly_payment = 0.0
        for asset in assets:
            if asset.asset_type == AssetType.LIABILITY:
                metadata = asset.extra_data if asset.extra_data else {}
                # Check for explicit monthly payment in metadata
                if "monthly_payment" in metadata:
                    monthly_payment += float(metadata["monthly_payment"])
                elif "月供" in metadata:
                    monthly_payment += float(metadata["月供"])
                else:
                    # Estimate: 0.5% of liability value as monthly payment
                    # This approximates a 30-year mortgage at ~4-5% interest
                    monthly_payment += asset.value * 0.005

        return monthly_payment

    def _calculate_allocation_gaps(
        self,
        current: dict[SPQuadrant, float],
        ideal: dict[SPQuadrant, float],
        net_worth: float,
    ) -> dict[SPQuadrant, float]:
        """Calculate gaps between current and ideal allocations"""
        gaps = {}

        for quadrant in SPQuadrant:
            # Use get() with default 0 for quadrants that may not be in ideal (e.g., ANCHOR_ASSET)
            ideal_amount = ideal.get(quadrant, 0) * net_worth
            current_amount = current.get(quadrant, 0)
            gaps[quadrant] = ideal_amount - current_amount

        return gaps

    def _generate_quadrant_analysis(
        self,
        current: dict[SPQuadrant, float],
        ideal: dict[SPQuadrant, float],
        net_worth: float,
        assets: list[UserAsset],
        user_profile: UserProfile | None,
    ) -> dict[str, Any]:
        """Generate detailed quadrant analysis"""
        analysis = {"quadrants": {}, "summary": {}, "priorities": []}

        total_current = sum(current.values())

        # Calculate expense-based spending money requirement
        monthly_expense = self._get_monthly_expense(assets, user_profile)
        monthly_debt_payment = self._calculate_monthly_debt_payment(assets)
        ideal_spending_amount = (monthly_expense + monthly_debt_payment) * 6

        for quadrant in SPQuadrant:
            current_amount = current.get(quadrant, 0)
            current_ratio = current_amount / total_current if total_current > 0 else 0
            ideal_ratio = ideal.get(quadrant, 0)

            # Override ideal amount for spending money with expense-based calculation
            if quadrant == SPQuadrant.SPENDING_MONEY:
                ideal_amount = ideal_spending_amount
                # Recalculate ideal ratio based on actual ideal amount
                ideal_ratio = ideal_amount / net_worth if net_worth > 0 else ideal_ratio
            else:
                ideal_amount = ideal_ratio * net_worth

            gap = ideal_amount - current_amount

            quadrant_name = {
                SPQuadrant.SPENDING_MONEY: "要花的钱",
                SPQuadrant.LIFE_MONEY: "保命的钱",
                SPQuadrant.GROWTH_MONEY: "生钱的钱",
                SPQuadrant.PRESERVATION_MONEY: "保本升值的钱",
                SPQuadrant.ANCHOR_ASSET: "锚点资产",
            }.get(quadrant, quadrant.value)

            analysis["quadrants"][quadrant.value] = {
                "name": quadrant_name,
                "current_amount": current_amount,
                "ideal_amount": ideal_amount,
                "current_ratio": current_ratio,
                "ideal_ratio": ideal_ratio,
                "gap": gap,
                "status": "sufficient" if gap <= 0 else "insufficient",
            }

            # Add to priorities if significant gap
            if abs(gap) > net_worth * 0.05:  # 5% of net worth threshold
                priority = "high" if abs(gap) > net_worth * 0.15 else "medium"
                analysis["priorities"].append(
                    {
                        "quadrant": quadrant.value,
                        "name": quadrant_name,
                        "gap": gap,
                        "priority": priority,
                        "action": "increase" if gap > 0 else "decrease",
                    }
                )

        # Sort priorities by gap size
        analysis["priorities"].sort(key=lambda x: abs(x["gap"]), reverse=True)

        # Generate summary with safe division
        allocation_efficiency = 0.0
        if net_worth > 0:
            allocation_efficiency = min(1.0, total_current / net_worth)

        analysis["summary"] = {
            "total_allocated": total_current,
            "allocation_efficiency": allocation_efficiency,
            "major_gaps": len(
                [p for p in analysis["priorities"] if p["priority"] == "high"]
            ),
            "overall_balance": "balanced"
            if len(analysis["priorities"]) <= 2
            else "needs_rebalancing",
        }

        return analysis

    def _generate_risk_warnings(
        self,
        analysis: PortfolioAnalysis,
        assets: list[UserAsset],
        thresholds: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Generate risk warnings based on analysis and Standard & Poor's Four Quadrant Model"""
        warnings = []

        # Traditional risk warnings
        # Real estate analysis: distinguish anchor (self-occupied) vs. investment properties
        
        # Calculate anchor asset ratio (self-occupied properties)
        anchor_ratio = 0.0
        investment_re_ratio = 0.0
        if analysis.net_worth > 0:
            anchor_value = analysis.quadrant_allocations.get(SPQuadrant.ANCHOR_ASSET, 0)
            anchor_ratio = anchor_value / analysis.net_worth
            investment_re_ratio = analysis.real_estate_ratio - anchor_ratio
        
        # Phase 2 Update: Anchor assets (自住房) are strategic foundation, NOT concentration risk
        # Only warn about INVESTMENT property concentration
        if investment_re_ratio > 0.4:  # >40% in investment properties is high
            severity = "high" if investment_re_ratio > 0.5 else "medium"
            warnings.append(
                {
                    "type": "investment_property_concentration",
                    "severity": severity,
                    "title": "投资性房产占比偏高",
                    "description": f"投资性房产占净资产{investment_re_ratio:.1%}，占比较高",
                    "recommendation": "建议适当分散投资，可考虑金融资产配置以增加流动性",
                }
            )
        
        # Add positive anchor asset insight (informational, not a warning)
        if anchor_ratio > 0.3:  # If self-occupied property is significant
            warnings.append(
                {
                    "type": "anchor_asset_strength",
                    "severity": "info",  # Informational, not a risk
                    "title": "核心锚点资产稳固",
                    "description": f"自住房产作为家庭锚点资产，占净资产{anchor_ratio:.1%}，提供居住保障和稳定基础",
                    "recommendation": "可利用房产抵押潜力进行资产配置优化",
                }
            )

        # Liquidity risk
        if analysis.liquidity_ratio < thresholds["liquidity_min"]:
            severity = "high" if analysis.liquidity_ratio < 1.0 else "medium"
            warnings.append(
                {
                    "type": "liquidity_risk",
                    "severity": severity,
                    "title": "流动性不足风险",
                    "description": f"现金储备仅够{analysis.liquidity_ratio:.1f}个月支出，低于建议的{thresholds['liquidity_min']:.1f}个月",
                    "recommendation": "建议增加现金储备或流动性较好的投资产品",
                }
            )

        # Insurance gap (if no insurance assets found)
        has_insurance = any(asset.asset_type == AssetType.INSURANCE for asset in assets)
        has_liabilities = any(
            asset.asset_type == AssetType.LIABILITY for asset in assets
        )

        if has_liabilities and not has_insurance:
            warnings.append(
                {
                    "type": "insurance_gap",
                    "severity": "medium",
                    "title": "保险保障缺口",
                    "description": "存在负债但缺乏相应的保险保障",
                    "recommendation": "建议配置重疾险、意外险等保险产品以降低风险",
                }
            )

        # Standard & Poor's Four Quadrant specific warnings
        if analysis.quadrant_analysis and analysis.quadrant_analysis.get("priorities"):
            for priority in analysis.quadrant_analysis["priorities"][
                :2
            ]:  # Top 2 priorities
                if priority["priority"] == "high":
                    quadrant_name = priority["name"]
                    gap = priority["gap"]
                    action = priority["action"]

                    if priority["quadrant"] == SPQuadrant.SPENDING_MONEY.value:
                        if action == "increase":
                            warnings.append(
                                {
                                    "type": "sp_spending_insufficient",
                                    "severity": "high",
                                    "title": f"{quadrant_name}不足",
                                    "description": f"应急资金缺口{abs(gap):,.0f}元，可能无法应对突发支出",
                                    "recommendation": "建议增加现金储备至6个月生活费用",
                                }
                            )
                    elif priority["quadrant"] == SPQuadrant.LIFE_MONEY.value:
                        if action == "increase":
                            warnings.append(
                                {
                                    "type": "sp_life_insufficient",
                                    "severity": "high",
                                    "title": f"{quadrant_name}不足",
                                    "description": f"保险保障缺口{abs(gap):,.0f}元，家庭风险保障不足",
                                    "recommendation": "建议配置重疾险、意外险等基础保障",
                                }
                            )
                    elif priority["quadrant"] == SPQuadrant.GROWTH_MONEY.value:
                        if action == "increase":
                            warnings.append(
                                {
                                    "type": "sp_growth_insufficient",
                                    "severity": "medium",
                                    "title": f"{quadrant_name}不足",
                                    "description": f"投资增值资产缺口{abs(gap):,.0f}元，财富增长能力有限",
                                    "recommendation": "建议适当配置股票基金、ETF等增值投资",
                                }
                            )
                        elif action == "decrease":
                            warnings.append(
                                {
                                    "type": "sp_growth_excessive",
                                    "severity": "medium",
                                    "title": f"{quadrant_name}过多",
                                    "description": f"高风险投资超配{abs(gap):,.0f}元，可能面临较大波动",
                                    "recommendation": "建议适当减少高风险投资，增加稳健资产",
                                }
                            )

        return warnings

    def _generate_recommendations(
        self,
        analysis: PortfolioAnalysis,
        assets: list[UserAsset],
        user_profile: UserProfile | None,
        thresholds: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Generate actionable recommendations based on Standard & Poor's Four Quadrant Model"""
        recommendations = []

        # Standard & Poor's Four Quadrant specific recommendations
        if analysis.quadrant_analysis and analysis.quadrant_analysis.get("priorities"):
            for priority in analysis.quadrant_analysis["priorities"][
                :3
            ]:  # Top 3 priorities
                quadrant_name = priority["name"]
                gap = priority["gap"]
                action = priority["action"]
                priority_level = priority["priority"]

                if (
                    priority["quadrant"] == SPQuadrant.SPENDING_MONEY.value
                    and action == "increase"
                ):
                    recommendations.append(
                        {
                            "type": "sp_spending",
                            "priority": priority_level,
                            "title": f"增加{quadrant_name}配置",
                            "description": f"建议增加{abs(gap):,.0f}元应急资金",
                            "specific_actions": [
                                "建立6个月生活费的应急基金",
                                "选择高流动性的货币基金或活期存款",
                                "设置自动转账，每月定期储蓄",
                            ],
                            "target_allocation": f"{analysis.ideal_allocations[SPQuadrant.SPENDING_MONEY]:.1%}",
                        }
                    )

                elif (
                    priority["quadrant"] == SPQuadrant.LIFE_MONEY.value
                    and action == "increase"
                ):
                    recommendations.append(
                        {
                            "type": "sp_life",
                            "priority": priority_level,
                            "title": f"增加{quadrant_name}配置",
                            "description": f"建议增加{abs(gap):,.0f}元保险保障",
                            "specific_actions": [
                                "重疾险：保额为年收入的3-5倍",
                                "意外险：保额为年收入的5-10倍",
                                "定期寿险：覆盖家庭负债和未来支出",
                            ],
                            "target_allocation": f"{analysis.ideal_allocations[SPQuadrant.LIFE_MONEY]:.1%}",
                        }
                    )

                elif priority["quadrant"] == SPQuadrant.GROWTH_MONEY.value:
                    if action == "increase":
                        recommendations.append(
                            {
                                "type": "sp_growth",
                                "priority": priority_level,
                                "title": f"增加{quadrant_name}配置",
                                "description": f"建议增加{abs(gap):,.0f}元投资增值资产",
                                "specific_actions": [
                                    "股票型基金：选择优质的主动或被动基金",
                                    "ETF投资：如沪深300、中证500等宽基指数",
                                    "定投策略：分散时间风险，降低波动影响",
                                ],
                                "target_allocation": f"{analysis.ideal_allocations[SPQuadrant.GROWTH_MONEY]:.1%}",
                            }
                        )
                    elif action == "decrease":
                        recommendations.append(
                            {
                                "type": "sp_growth_reduce",
                                "priority": priority_level,
                                "title": f"适当减少{quadrant_name}配置",
                                "description": f"建议减少{abs(gap):,.0f}元高风险投资",
                                "specific_actions": [
                                    "部分获利了结，锁定投资收益",
                                    "转移至稳健型投资产品",
                                    "保持适度的风险敞口",
                                ],
                                "target_allocation": f"{analysis.ideal_allocations[SPQuadrant.GROWTH_MONEY]:.1%}",
                            }
                        )

                elif (
                    priority["quadrant"] == SPQuadrant.PRESERVATION_MONEY.value
                    and action == "increase"
                ):
                    recommendations.append(
                        {
                            "type": "sp_preservation",
                            "priority": priority_level,
                            "title": f"增加{quadrant_name}配置",
                            "description": f"建议增加{abs(gap):,.0f}元稳健投资",
                            "specific_actions": [
                                "债券基金：选择信用等级较高的产品",
                                "银行理财：稳健型或平衡型产品",
                                "定期存款：部分资金选择定期存款保本",
                            ],
                            "target_allocation": f"{analysis.ideal_allocations[SPQuadrant.PRESERVATION_MONEY]:.1%}",
                        }
                    )

        # Traditional recommendations (fallback if no quadrant analysis)
        if not recommendations:
            # Asset allocation recommendations - focus on INVESTMENT properties
            # Calculate investment property ratio (excluding anchor/self-occupied)
            anchor_val = analysis.quadrant_allocations.get(SPQuadrant.ANCHOR_ASSET, 0)
            anchor_r = anchor_val / analysis.net_worth if analysis.net_worth > 0 else 0
            invest_re_ratio = analysis.real_estate_ratio - anchor_r
            
            if invest_re_ratio > 0.4:  # Investment properties > 40%
                target_other_assets = analysis.net_worth * 0.6  # At least 60% non-investment-RE
                current_other_assets = analysis.net_worth * (1 - invest_re_ratio)
                additional_needed = target_other_assets - current_other_assets

                recommendations.append(
                    {
                        "type": "diversification",
                        "priority": "high",
                        "title": "优化投资性房产配置",
                        "description": f"投资性房产占比较高({invest_re_ratio:.1%})，建议增加{additional_needed:,.0f}元金融资产",
                        "specific_actions": [
                            "考虑投资股票型基金或ETF增加流动性",
                            "配置部分债券基金增加稳定收益",
                            "可利用房产抵押盘活部分资产",
                        ],
                    }
                )

            # Liquidity recommendations
            if analysis.liquidity_ratio < thresholds["liquidity_min"]:
                monthly_expense = self._get_monthly_expense(assets, user_profile)
                target_cash = monthly_expense * thresholds["liquidity_min"]
                current_cash = sum(
                    asset.value
                    for asset in assets
                    if asset.asset_type == AssetType.CASH
                )
                additional_cash_needed = target_cash - current_cash

                recommendations.append(
                    {
                        "type": "liquidity",
                        "priority": "medium",
                        "title": "增加流动性储备",
                        "description": f"建议增加{additional_cash_needed:,.0f}元现金储备",
                        "specific_actions": [
                            "建立应急基金账户",
                            "考虑货币基金等流动性好的产品",
                            "定期储蓄计划",
                        ],
                    }
                )

            # Insurance recommendations
            has_insurance = any(
                asset.asset_type == AssetType.INSURANCE for asset in assets
            )
            if not has_insurance and analysis.net_worth > 1000000:  # 净资产超过100万
                recommendations.append(
                    {
                        "type": "insurance",
                        "priority": "medium",
                        "title": "完善保险保障",
                        "description": "建议配置基础保险保障",
                        "specific_actions": [
                            "重疾险：保额建议为年收入的3-5倍",
                            "意外险：保额建议为年收入的5-10倍",
                            "定期寿险：如有家庭责任",
                        ],
                    }
                )

        return recommendations

    def _determine_overall_risk_level(self, analysis: PortfolioAnalysis) -> RiskLevel:
        """Determine overall portfolio risk level"""
        high_risk_warnings = sum(
            1 for w in analysis.risk_warnings if w.get("severity") == "high"
        )
        medium_risk_warnings = sum(
            1 for w in analysis.risk_warnings if w.get("severity") == "medium"
        )

        if high_risk_warnings >= 2:
            return RiskLevel.HIGH
        elif high_risk_warnings >= 1 or medium_risk_warnings >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def generate_analysis_summary(self, analysis: PortfolioAnalysis) -> str:
        """Generate a human-readable analysis summary with Standard & Poor's Four Quadrant insights"""
        summary_parts = []

        # Basic metrics
        summary_parts.append(f"您的净资产为{analysis.net_worth:,.0f}元")
        summary_parts.append(f"房产占比{analysis.real_estate_ratio:.1%}")
        summary_parts.append(f"流动性储备够{analysis.liquidity_ratio:.1f}个月支出")

        # Standard & Poor's Four Quadrant summary
        if analysis.quadrant_analysis and analysis.quadrant_analysis.get("summary"):
            quadrant_summary = analysis.quadrant_analysis["summary"]
            balance_status = quadrant_summary.get("overall_balance", "unknown")

            if balance_status == "balanced":
                summary_parts.append("标准普尔四象限配置：整体均衡")
            elif balance_status == "needs_rebalancing":
                major_gaps = quadrant_summary.get("major_gaps", 0)
                summary_parts.append(
                    f"标准普尔四象限配置：需要调整，发现{major_gaps}个重要缺口"
                )

            # Highlight top priority quadrant
            if analysis.quadrant_analysis.get("priorities"):
                top_priority = analysis.quadrant_analysis["priorities"][0]
                action_text = "增加" if top_priority["action"] == "increase" else "减少"
                summary_parts.append(f"优先{action_text}{top_priority['name']}配置")

        # Risk assessment
        if analysis.overall_risk_level == RiskLevel.HIGH:
            summary_parts.append("整体风险水平：较高，需要重点关注")
        elif analysis.overall_risk_level == RiskLevel.MEDIUM:
            summary_parts.append("整体风险水平：中等，建议适当调整")
        else:
            summary_parts.append("整体风险水平：较低，配置相对合理")

        # Key warnings
        if analysis.risk_warnings:
            summary_parts.append(f"发现{len(analysis.risk_warnings)}个风险点需要关注")

        return "。".join(summary_parts) + "。"


# Global analyzer instance
portfolio_analyzer = PortfolioAnalyzer()
