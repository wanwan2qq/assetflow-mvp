import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../shared/widgets/money_text.dart';
import '../../../../core/providers/asset_provider.dart';

class WealthOverviewCard extends ConsumerWidget {
  final bool isPrivacyMode;

  const WealthOverviewCard({
    super.key,
    required this.isPrivacyMode,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final netWorthAsync = ref.watch(totalNetWorthProvider);
    final currencyFormat = NumberFormat.simpleCurrency(locale: 'zh_CN', decimalDigits: 0);

    // Mock data for growth
    const double yearlyGrowth = 125000;
    const double growthPercent = 12.5;
    const int healthScore = 85;

    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Container(
        height: 200, // Slightly more compact
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          // Gradient Background for Premium Look
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).brightness == Brightness.dark 
                  ? const Color(0xFF004D40) // Dark Mode Start
                  : colorScheme.primary, 
              Theme.of(context).brightness == Brightness.dark
                  ? const Color(0xFF00695C) // Dark Mode End
                  : Color.lerp(colorScheme.primary, Colors.black, 0.2)!, 
            ],
          ),
          boxShadow: [
            BoxShadow(
              color: colorScheme.primary.withOpacity(0.3),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Stack(
          children: [
            // Decorative background elements (Curved Line)
            Positioned.fill(
              child: CustomPaint(
                painter: _ConcaveCurvePainter(
                  color: Colors.white.withOpacity(0.05),
                ),
              ),
            ),
            
            // Content
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '总净资产 (Net Worth)',
                        style: theme.textTheme.labelMedium?.copyWith(
                          color: Colors.white.withOpacity(0.8),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      // Health Score Badge - Glassmorphism
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: Colors.white.withOpacity(0.1)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              '健康分 ',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: Colors.white.withOpacity(0.9),
                                fontSize: 10,
                              ),
                            ),
                            Text(
                              '$healthScore',
                              style: theme.textTheme.labelMedium?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 8),
                  
                  // Main Net Worth Value
                  MoneyText(
                    isPrivacyMode ? '****' : currencyFormat.format(netWorthAsync),
                    style: theme.textTheme.displaySmall?.copyWith( // Larger, more prominent
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -1,
                      fontSize: 36, // Bumped up slightly
                    ),
                  ),

                  const Spacer(),

                  // Bottom Row: Growth Info
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.05)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '年度净增长预测',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: Colors.white.withOpacity(0.7),
                                fontSize: 10,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Row(
                              children: [
                                MoneyText(
                                  isPrivacyMode ? '****' : currencyFormat.format(yearlyGrowth),
                                  style: theme.textTheme.titleSmall?.copyWith(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFE8F5E9).withOpacity(0.2), // Light Green translucent
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Row(
                                    children: [
                                      const Icon(Icons.arrow_outward_rounded, size: 10, color: Color(0xFFA5D6A7)), // Light Green 200
                                      const SizedBox(width: 2),
                                      Text(
                                        '+$growthPercent%',
                                        style: const TextStyle(
                                          color: Color(0xFFA5D6A7), // Light Green 200
                                          fontSize: 10,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConcaveCurvePainter extends CustomPainter {
  final Color color;

  _ConcaveCurvePainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final path = Path();
    path.moveTo(0, size.height * 0.4);
    path.quadraticBezierTo(
      size.width * 0.5, size.height * 0.2, // Control point
      size.width, size.height * 0.6, // End point
    );
    path.lineTo(size.width, 0);
    path.lineTo(0, 0);
    path.close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
