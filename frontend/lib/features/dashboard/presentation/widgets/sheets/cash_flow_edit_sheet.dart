import 'package:flutter/material.dart';
import 'dart:ui';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/models/cash_flow_item.dart';
import '../../../../../core/providers/wealth_provider.dart';
import '../../../../../core/providers/asset_provider.dart';

class CashFlowEditSheet extends ConsumerStatefulWidget {
  final CashFlowItem? item;

  const CashFlowEditSheet({super.key, this.item});

  @override
  ConsumerState<CashFlowEditSheet> createState() => _CashFlowEditSheetState();
}

class _CashFlowEditSheetState extends ConsumerState<CashFlowEditSheet> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TextEditingController _amountController;
  
  CashFlowType _type = CashFlowType.income;
  bool _isRecurring = true; // Mode switcher: true = Recurring, false = One-time
  
  // Recurring Settings
  CashFlowFrequency _frequency = CashFlowFrequency.monthly;
  
  // One-time Settings (and reused for recurring execution date if needed)
  DateTime _selectedDate = DateTime.now();

  int? _selectedAssetId;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.item?.name ?? '');
    _amountController = TextEditingController(text: widget.item?.amount.toString() ?? '');
    _type = widget.item?.type ?? CashFlowType.income;
    _frequency = widget.item?.frequency ?? CashFlowFrequency.monthly;
    _isRecurring = _frequency != CashFlowFrequency.oneTime;
    _selectedAssetId = widget.item?.relatedAssetId;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final name = _nameController.text;
      final amount = double.parse(_amountController.text);
      
      final newItem = CashFlowItem(
        id: widget.item?.id ?? DateTime.now().millisecondsSinceEpoch.toString(),
        name: name,
        amount: amount,
        type: _type,
        frequency: _isRecurring ? _frequency : CashFlowFrequency.oneTime,
        relatedAssetId: _selectedAssetId,
      );

      if (widget.item == null) {
        await ref.read(cashFlowProvider.notifier).addCashFlow(newItem);
      } else {
        await ref.read(cashFlowProvider.notifier).updateCashFlow(newItem);
      }

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(widget.item == null ? 'Transaction Recorded' : 'Transaction Updated')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final assetsAsync = ref.watch(assetListProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isIncome = _type == CashFlowType.income;
    
    // Theme Colors
    final backgroundColor = isDark ? const Color(0xFF1E1E1E) : Colors.white;
    final surfaceColor = isDark ? const Color(0xFF2C2C2C) : Colors.grey[100]!;
    final textColor = isDark ? Colors.white : Colors.black;
    final hintColor = isDark ? Colors.white38 : Colors.grey;
    
    // Brand & Semantic Colors
    final incomeColor = isDark ? AppTheme.incomeColorDark : AppTheme.incomeColorLight;
    final expenseColor = isDark ? AppTheme.expenseColorDark : AppTheme.expenseColorLight;
    final brandColor = AppTheme.seedColor; // Use seed or income color as brand default
    final activeColor = isIncome ? incomeColor : expenseColor;

    return Container(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        top: 16,
        left: 20, 
        right: 20,
      ),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 1. Header with Cancel/Save
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                   TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: Text('取消', style: TextStyle(color: hintColor, fontSize: 16)),
                  ),
                  Text(
                    '记一笔',
                    style: TextStyle(
                      fontSize: 18, 
                      fontWeight: FontWeight.bold,
                      color: textColor,
                    ),
                  ),
                  TextButton(
                    onPressed: _isLoading ? null : _save,
                    child: _isLoading 
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : Text('保存', style: TextStyle(color: brandColor, fontWeight: FontWeight.bold, fontSize: 16)),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // 2. Type Segmented Control
              Container(
                height: 48,
                decoration: BoxDecoration(
                  color: surfaceColor,
                  borderRadius: BorderRadius.circular(24), // Pill shape
                ),
                padding: const EdgeInsets.all(4),
                child: Row(
                  children: [
                    Expanded(child: _buildTypeSegment('收入', CashFlowType.income, incomeColor, isDark)),
                    Expanded(child: _buildTypeSegment('支出', CashFlowType.expense, expenseColor, isDark)),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 3. Mode Switcher (Recurring vs One-time)
              Row(
                children: [
                  Expanded(
                    child: _buildModeCard(
                      label: '周期性',
                      icon: Icons.sync,
                      isSelected: _isRecurring,
                      onTap: () => setState(() => _isRecurring = true),
                      activeColor: activeColor,
                      isDark: isDark,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildModeCard(
                      label: '一次性',
                      icon: Icons.flash_on,
                      isSelected: !_isRecurring,
                      onTap: () => setState(() => _isRecurring = false),
                      activeColor: activeColor,
                      isDark: isDark,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // 4. Hero Amount Input
              Center(
                child: IntrinsicWidth(
                  child: TextFormField(
                    controller: _amountController,
                    autofocus: true,
                    textAlign: TextAlign.center,
                    cursorColor: activeColor,
                    style: TextStyle(
                      fontSize: 40, 
                      fontWeight: FontWeight.bold, 
                      color: textColor,
                      fontFeatures: const [FontFeature.tabularFigures()],
                    ),
                    decoration: InputDecoration(
                      prefixText: '¥',
                      prefixStyle: TextStyle(
                        fontSize: 40, 
                        fontWeight: FontWeight.bold, 
                        color: textColor,
                      ),
                      border: InputBorder.none,
                      hintText: '0.00',
                      hintStyle: TextStyle(color: isDark ? Colors.white12 : Colors.grey[300]),
                      contentPadding: EdgeInsets.zero,
                    ),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    validator: (value) => (value == null || value.isEmpty) ? '请输入金额' : null,
                  ),
                ),
              ),
              const SizedBox(height: 32),

              // 5. Dynamic Settings (Frequency or Date)
              _buildModernField(
                child: _isRecurring
                  ? DropdownButtonFormField<CashFlowFrequency>(
                      value: _frequency,
                      decoration: _inputDecoration(isDark, icon: Icons.repeat, hint: '频率 (Frequency)'),
                      dropdownColor: isDark ? const Color(0xFF2C2C2C) : Colors.white,
                      style: TextStyle(color: textColor, fontSize: 15),
                      items: const [
                        DropdownMenuItem(value: CashFlowFrequency.monthly, child: Text('每月 (Monthly)')),
                        DropdownMenuItem(value: CashFlowFrequency.yearly, child: Text('每年 (Yearly)')),
                      ],
                      onChanged: (val) {
                        if (val != null) setState(() => _frequency = val);
                      },
                    )
                  : InkWell(
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate: _selectedDate,
                          firstDate: DateTime(2000),
                          lastDate: DateTime(2100),
                          builder: (context, child) {
                            return Theme(
                              data: isDark ? ThemeData.dark() : ThemeData.light(), 
                              child: child!,
                            );
                          },
                        );
                        if (picked != null) setState(() => _selectedDate = picked);
                      },
                      child: IgnorePointer(
                        child: TextFormField(
                          controller: TextEditingController(
                            text: '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
                          ),
                          decoration: _inputDecoration(isDark, icon: Icons.calendar_today, hint: '日期'),
                          style: TextStyle(color: textColor),
                        ),
                      ),
                    ),
                isDark: isDark,
              ),
              const SizedBox(height: 16),

              // 6. Name Field
              _buildModernField(
                child: TextFormField(
                  controller: _nameController,
                  decoration: _inputDecoration(isDark, icon: Icons.edit_note, hint: '备注 / 名称'),
                  style: TextStyle(color: textColor),
                  validator: (value) => value == null || value.isEmpty ? '请输入名称' : null,
                ),
                isDark: isDark,
              ),
              const SizedBox(height: 16),

              // 7. Asset Linking
              assetsAsync.when(
                data: (assets) => _buildModernField(
                  child: DropdownButtonFormField<int>(
                    value: _selectedAssetId,
                    decoration: _inputDecoration(isDark, icon: Icons.link, hint: '关联资产 (可选)'),
                    dropdownColor: isDark ? const Color(0xFF2C2C2C) : Colors.white,
                    style: TextStyle(color: textColor, fontSize: 15),
                    items: [
                      DropdownMenuItem<int>(
                        value: null, 
                        child: Text('不关联资产', style: TextStyle(color: hintColor))
                      ),
                      ...assets.map((asset) => DropdownMenuItem(
                            value: asset.id,
                            child: Text(
                              asset.name.length > 24
                                  ? '${asset.name.substring(0, 24)}...' 
                                  : asset.name,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(color: textColor),
                            ),
                          )),
                    ],
                    onChanged: (val) => setState(() => _selectedAssetId = val),
                  ),
                  isDark: isDark,
                ),
                loading: () => const LinearProgressIndicator(), 
                error: (_, __) => Text('加载资产失败', style: TextStyle(color: expenseColor)),
              ),
              
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  // Helper Methods

  InputDecoration _inputDecoration(bool isDark, {required IconData icon, required String hint}) {
    final hintColor = isDark ? Colors.white38 : Colors.grey;
    final iconColor = isDark ? Colors.white54 : Colors.grey[600];
    
    return InputDecoration(
      hintText: hint,
      hintStyle: TextStyle(color: hintColor),
      prefixIcon: Icon(icon, color: iconColor, size: 20),
      border: InputBorder.none,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );
  }

  Widget _buildModernField({required Widget child, required bool isDark}) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? Colors.white.withOpacity(0.05) : Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
      ),
      child: child,
    );
  }

  Widget _buildTypeSegment(String label, CashFlowType type, Color activeColor, bool isDark) {
    final isSelected = _type == type;
    
    return GestureDetector(
      onTap: () => setState(() => _type = type),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeInOut,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? activeColor : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected 
              ? Colors.white 
              : (isDark ? Colors.white54 : Colors.grey[600]), // White text when selected
            fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildModeCard({
    required String label,
    required IconData icon,
    required bool isSelected,
    required VoidCallback onTap,
    required Color activeColor,
    required bool isDark,
  }) {
    final bgColor = isSelected 
        ? activeColor.withOpacity(0.15) 
        : (isDark ? Colors.white.withOpacity(0.05) : Colors.grey[100]!);
    
    final borderColor = isSelected ? activeColor : Colors.transparent;
    final fgColor = isSelected 
        ? activeColor 
        : (isDark ? Colors.white54 : Colors.grey[600]);

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: borderColor,
            width: 2,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: fgColor, size: 18),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: fgColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
