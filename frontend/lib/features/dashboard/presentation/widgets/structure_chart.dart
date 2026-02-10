import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class StructureChart extends StatelessWidget {
  final double fixedIncome;
  final double variableIncome;
  final double fixedExpense;
  final double variableExpense;

  const StructureChart({
    super.key,
    required this.fixedIncome,
    required this.variableIncome,
    required this.fixedExpense,
    required this.variableExpense,
  });

  @override
  Widget build(BuildContext context) {
    final totalIncome = fixedIncome + variableIncome;
    final totalExpense = fixedExpense + variableExpense;
    
    // Calculate max Y for chart scaling
    final maxY = (totalIncome > totalExpense ? totalIncome : totalExpense) * 1.2;

    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // Exact Design Colors
    // Income
    final incomeFixed = const Color(0xFF00695C); // Deep Teal
    final incomeVariable = const Color(0xFF4DB6AC); // Lighter Teal
    
    // Expense
    final expenseFixed = const Color(0xFFC62828); // Deep Red
    final expenseVariable = const Color(0xFFE57373); // Lighter Red

    return Container(
      height: 280, // Increased height for legend
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E1E1E) : Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: theme.dividerColor.withOpacity(isDark ? 0.05 : 0)),
        boxShadow: isDark ? [] : [
           BoxShadow(
             color: Colors.black.withOpacity(0.05),
             blurRadius: 10,
             offset: const Offset(0, 4),
           ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
           Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '收支结构分析', 
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold, 
                )
              ),
              // Option for time period or unit could go here
            ],
          ),
          const SizedBox(height: 32),
          
          // Chart
          Expanded(
            child: BarChart(
              BarChartData(
                alignment: BarChartAlignment.spaceAround,
                maxY: maxY > 0 ? maxY : 100, 
                barTouchData: BarTouchData(
                  enabled: true,
                  touchTooltipData: BarTouchTooltipData(
                    tooltipBgColor: isDark ? Colors.grey.shade800 : Colors.blueGrey,
                    tooltipPadding: const EdgeInsets.all(8),
                    tooltipMargin: 8,
                    getTooltipItem: (group, groupIndex, rod, rodIndex) {
                      String label = '';
                      double value = 0;
                      if (group.x == 0) {
                        if (rodIndex == 0) { label = '固定收入'; value = fixedIncome; }
                        else { label = '变动收入'; value = variableIncome; }
                      } else {
                        if (rodIndex == 0) { label = '固定支出'; value = fixedExpense; }
                        else { label = '变动支出'; value = variableExpense; }
                      }
                      
                      // For stacked rods, toY returns the cumulative value.
                      // We need the delta for the specific stack item, but fl_chart tooltip gives the rod check.
                      // Actually fl_chart rodStackItems doesn't easily map to specific tooltip index unless we use `rodStackItem`
                      // Simplification: Just show total for the bar for now or use the provided value logic if possible.
                      // Let's just show the total value of the bar in a clean way.
             
                      return BarTooltipItem(
                        '¥${rod.toY.toInt()}',
                        const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      );
                    },
                  ),
                ),
                titlesData: FlTitlesData(
                  leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 32, 
                      getTitlesWidget: (value, meta) => _bottomTitles(value, meta, context),
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: maxY / 5,
                  getDrawingHorizontalLine: (value) => FlLine(
                    color: theme.dividerColor.withOpacity(0.1),
                    strokeWidth: 1,
                    dashArray: [5, 5], // Dashed lines
                  ),
                ),
                barGroups: [
                  // Income
                  _buildBarGroup(
                    0, 
                    fixedIncome, 
                    variableIncome, 
                    incomeFixed,    // Fixed (Bottom)
                    incomeVariable, // Variable (Top)
                  ),
                  // Expense
                  _buildBarGroup(
                    1, 
                    fixedExpense, 
                    variableExpense, 
                    expenseFixed,    // Fixed (Bottom)
                    expenseVariable, // Variable (Top)
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          // Legend
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
               _buildLegendItem(context, '固定 (Fixed)', Colors.grey.shade700, true), 
               const SizedBox(width: 24),
               _buildLegendItem(context, '变动 (Variable)', Colors.grey.shade400, false),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(BuildContext context, String label, Color color, bool isSolid) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color.withOpacity(isSolid ? 1.0 : 0.6), // Opacity diff key
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.textTheme.bodySmall?.color?.withOpacity(0.7),
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  BarChartGroupData _buildBarGroup(int x, double fixed, double variable, Color fixedColor, Color variableColor) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: fixed + variable,
          width: 32, // Sleeker bars
          rodStackItems: [
             // Stack: Bottom to Top
            BarChartRodStackItem(0, fixed, fixedColor), 
            BarChartRodStackItem(fixed, fixed + variable, variableColor), 
          ],
          borderRadius: BorderRadius.circular(6),
        ),
      ],
    );
  }

  static Widget _bottomTitles(double value, TitleMeta meta, BuildContext context) {
    final theme = Theme.of(context);
    final style = TextStyle(
      color: theme.textTheme.bodyMedium?.color?.withOpacity(0.6),
      fontSize: 13, 
      fontWeight: FontWeight.w600,
    );
    String text;
    switch (value.toInt()) {
      case 0:
        text = '总收入';
        break;
      case 1:
        text = '总支出';
        break;
      default:
        text = '';
    }
    return SideTitleWidget(
      axisSide: meta.axisSide,
      space: 12,
      child: Text(text, style: style),
    );
  }
}
