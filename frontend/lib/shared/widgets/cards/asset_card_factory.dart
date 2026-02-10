import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/models/asset.dart';
import '../../../features/dashboard/presentation/pages/asset_detail_page.dart';
import '../../../features/dashboard/presentation/widgets/sheets/liability_edit_sheet.dart';

final _currencyFormat = NumberFormat.simpleCurrency(locale: 'zh_CN', decimalDigits: 0);
final _dateFormat = DateFormat('yyyy-MM-dd');

class AssetCardFactory {
  static Widget build(UserAsset asset, {bool isPrivacyMode = false}) {
    switch (asset.assetType) {
      case AssetType.investment:
        return _InvestmentCard(asset: asset, isPrivacyMode: isPrivacyMode);
      case AssetType.liability:
        return _LiabilityCard(asset: asset, isPrivacyMode: isPrivacyMode);
      case AssetType.realEstate:
        return _RealEstateCard(asset: asset, isPrivacyMode: isPrivacyMode);
      case AssetType.cash:
        return _CashCard(asset: asset, isPrivacyMode: isPrivacyMode);
      case AssetType.insurance:
        return _InsuranceCard(asset: asset, isPrivacyMode: isPrivacyMode);
    }
  }
}

// A. Investment (Stock/Fund) -> "The Ticker"
class _InvestmentCard extends StatelessWidget {
  final UserAsset asset;
  final bool isPrivacyMode;

  const _InvestmentCard({required this.asset, required this.isPrivacyMode});

  @override
  Widget build(BuildContext context) {
    final pnl = asset.metadata?['pnl'] as num?;
    final pnlValue = pnl?.toDouble() ?? 0.0; // Default to 0 if null
    final isGain = pnlValue >= 0;
    
    // Calculate percentage based on (value - pnl) being the cost basis, or just treat pnl as absolute. 
    // If we only have current Value and PnL, Pnl% = PnL / (Value - PnL). 
    // Let's assume metadata might have 'pnl_percent' or we calculate roughly.
    // Use a safe calculation.
    final costBasis = asset.value - pnlValue;
    final pnlPercent = costBasis != 0 ? (pnlValue / costBasis * 100) : 0.0;

    final symbol = asset.metadata?['symbol'] ?? 'CODE';

    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).shadowColor.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: () {
             // Navigate to detail
          },
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Left: Icon
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: colorScheme.tertiaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  alignment: Alignment.center,
                  child: Icon(Icons.show_chart_rounded, color: colorScheme.onTertiaryContainer, size: 24),
                ),
                const SizedBox(width: 12),
                
                // Center: Name + Symbol
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        asset.name,
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: colorScheme.onSurface),
                      ),
                      const SizedBox(height: 2),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                        decoration: BoxDecoration(
                          color: colorScheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          symbol,
                          style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 11, fontWeight: FontWeight.w500),
                        ),
                      ),
                    ],
                  ),
                ),

                // Right: Market Value + Trend Pill
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      isPrivacyMode ? '****' : _currencyFormat.format(asset.value),
                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: colorScheme.onSurface),
                    ),
                    const SizedBox(height: 6),
                    // Trend Pill
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: isGain 
                            ? (Theme.of(context).brightness == Brightness.dark ? const Color(0xFF064E3B) : const Color(0xFFDCFCE7)) 
                            : (Theme.of(context).brightness == Brightness.dark ? const Color(0xFF450A0A) : const Color(0xFFFEE2E2)),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            isGain ? Icons.arrow_drop_up_rounded : Icons.arrow_drop_down_rounded,
                            size: 16,
                            color: isGain 
                                ? (Theme.of(context).brightness == Brightness.dark ? const Color(0xFF6EE7B7) : const Color(0xFF166534)) 
                                : (Theme.of(context).brightness == Brightness.dark ? const Color(0xFFFCA5A5) : const Color(0xFF991B1B)),
                          ),
                          Text(
                            isPrivacyMode ? '***' : '${pnlPercent.abs().toStringAsFixed(2)}%',
                            style: TextStyle(
                              color: isGain 
                                  ? (Theme.of(context).brightness == Brightness.dark ? const Color(0xFF6EE7B7) : const Color(0xFF166534)) 
                                  : (Theme.of(context).brightness == Brightness.dark ? const Color(0xFFFCA5A5) : const Color(0xFF991B1B)),
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// B. Liability (Loan/Mortgage) -> "The Progress"
class _LiabilityCard extends StatelessWidget {
  final UserAsset asset;
  final bool isPrivacyMode;

  const _LiabilityCard({required this.asset, required this.isPrivacyMode});

  @override
  Widget build(BuildContext context) {
    // Liability value is typically negative in net worth calc, but stored as positive debt amount usually.
    // Assuming asset.value is the outstanding debt.
    // originalBalance should be stored in metadata or separate field.
    final original = (asset.originalBalance != null && asset.originalBalance! > 0) 
        ? asset.originalBalance! 
        : (asset.value * 1.2); // Fallback if no original balance, just to show some progress

    final current = asset.value;
    final repaid = original - current;
    final progress = (repaid / original).clamp(0.0, 1.0);
    final progressPercent = (progress * 100).toStringAsFixed(0);
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(16),
         border: Border.all(color: Theme.of(context).dividerColor.withOpacity(0.1)), // Subtle border for "bill" feel
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).shadowColor.withOpacity(0.02),
            blurRadius: 5,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: () {
             showModalBottomSheet(
              context: context,
              isScrollControlled: true,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
              builder: (context) => LiabilityEditSheet(asset: asset),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start, // Align top
                  children: [
                    // Left: Bank Icon
                     Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: colorScheme.error.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      alignment: Alignment.center,
                      child: const Icon(Icons.account_balance_rounded, color: Color(0xFFEF4444), size: 20),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Top Right (Outstanding) moved to here? 
                          // Prompt: "Top Right: Outstanding... Middle: Name"
                          // Let's use Row for Top line.
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                asset.name,
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: colorScheme.onSurface),
                              ),
                              Text( // Top Right: Outstanding
                                isPrivacyMode ? '****' : '待还 ${_currencyFormat.format(asset.value)}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold, 
                                  fontSize: 14, 
                                  color: Color(0xFFEF4444) // Red text for liability
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          // Bottom: LinearProgressIndicator
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    '已还款进度', 
                                    style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                                  ),
                                  Text(
                                    '$progressPercent%',
                                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF10B981)),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              ClipRRect(
                                borderRadius: BorderRadius.circular(4),
                                child: LinearProgressIndicator(
                                  value: progress,
                                  minHeight: 8,
                                  backgroundColor: colorScheme.surfaceContainerHighest,
                                  valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF10B981)), // Green progress
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// C. Real Estate -> "The Valuation"
class _RealEstateCard extends StatelessWidget {
  final UserAsset asset;
  final bool isPrivacyMode;

  const _RealEstateCard({required this.asset, required this.isPrivacyMode});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8), // Slightly larger vertical margin
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(20), // More rounded
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).shadowColor.withOpacity(0.04), // Soft shadow
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          onTap: () {
             Navigator.of(context).push(
               MaterialPageRoute(builder: (context) => RealEstateDetailPage(asset: asset)),
             );
          },
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
            child: Row(
              children: [
                // Left: House Icon or Image
                Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    color: colorScheme.secondaryContainer,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  alignment: Alignment.center,
                  child: Icon(Icons.home_work_rounded, color: colorScheme.onSecondaryContainer, size: 28),
                ),
                const SizedBox(width: 14),

                // Center: Name + Location
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        asset.name,
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: colorScheme.onSurface),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(Icons.location_on_outlined, size: 12, color: colorScheme.onSurfaceVariant),
                          const SizedBox(width: 2),
                          Expanded(
                            child: Text(
                              asset.metadata?['location']?.toString() ?? '未知位置',
                              style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // Right: Valuation + Date
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      isPrivacyMode ? '****' : _currencyFormat.format(asset.value),
                      style: TextStyle(
                        fontWeight: FontWeight.w900, // Huge font weight
                        fontSize: 18, 
                        color: colorScheme.onSurface,
                        letterSpacing: -0.5
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '更新于: 2月15日', // Hardcoded as per mock or use asset.updatedAt
                      style: TextStyle(color: Colors.grey[400], fontSize: 10),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// D. Cash/Deposit -> "The Balance"
class _CashCard extends StatelessWidget {
  final UserAsset asset;
  final bool isPrivacyMode;

  const _CashCard({required this.asset, required this.isPrivacyMode});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4), // Tighter spacing
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).dividerColor.withOpacity(0.08)), // Subtle border instead of shadow
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: colorScheme.tertiaryContainer,
            shape: BoxShape.circle,
          ),
          alignment: Alignment.center,
          child: Icon(Icons.account_balance_wallet_rounded, color: colorScheme.onTertiaryContainer, size: 20),
        ),
        title: Text(
          asset.name,
          style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: colorScheme.onSurface),
        ),
        subtitle: Text(
          asset.metadata?['account_type'] ?? '储蓄账户',
          style: TextStyle(fontSize: 12, color: colorScheme.onSurfaceVariant), 
        ),
        trailing: Text(
           isPrivacyMode ? '****' : _currencyFormat.format(asset.value),
           style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: colorScheme.onSurface),
        ),
        onTap: () {
           // Detail or Edit
        },
      ),
    );
  }
}

// Fallback / Insurance Card
class _InsuranceCard extends StatelessWidget {
  final UserAsset asset;
  final bool isPrivacyMode;

  const _InsuranceCard({required this.asset, required this.isPrivacyMode});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).shadowColor.withOpacity(0.03),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: const Color(0xFFECFDF5),
            shape: BoxShape.circle,
          ),
          alignment: Alignment.center,
          child: const Icon(Icons.shield_outlined, color: Color(0xFF10B981)),
        ),
        title: Text(asset.name, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text('保障中', style: TextStyle(color: Colors.green[700], fontSize: 12)),
        trailing: Text(
          isPrivacyMode ? '****' : _currencyFormat.format(asset.value),
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
      ),
    );
  }
}
