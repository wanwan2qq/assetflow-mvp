import 'package:flutter/material.dart';
import 'asset_form_scaffold.dart';

class LiabilityForm extends StatefulWidget {
  const LiabilityForm({super.key});

  @override
  State<LiabilityForm> createState() => _LiabilityFormState();
}

class _LiabilityFormState extends State<LiabilityForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _originalAmountController = TextEditingController();
  final _currentPrincipalController = TextEditingController();
  final _interestRateController = TextEditingController();
  
  String _accountType = '住房按揭';
  final List<String> _accountTypes = ['住房按揭', '车贷', '消费贷', '经营贷', '个人借款'];

  bool get _isValid => _nameController.text.isNotEmpty && 
                       _originalAmountController.text.isNotEmpty && 
                       _currentPrincipalController.text.isNotEmpty;

  @override
  void dispose() {
    _nameController.dispose();
    _originalAmountController.dispose();
    _currentPrincipalController.dispose();
    _interestRateController.dispose();
    super.dispose();
  }
  
  void _onSave() {
    if (_formKey.currentState!.validate()) {
       ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('已成功添加 ${_nameController.text}')),
      );
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AssetFormScaffold(
      title: '新建贷款/负债',
      onCancel: () => Navigator.pop(context),
      onSave: _onSave,
      isSaveEnabled: _isValid,
      child: Form(
        key: _formKey,
        onChanged: () => setState(() {}),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildTextField(
              controller: _nameController,
              label: '贷款名称',
              hint: '例如: 招行房贷/车贷',
              required: true,
              prefixIcon: const Icon(Icons.description_outlined),
            ),
            const SizedBox(height: 24),
            
            // Account Type Dropdown
            DropdownButtonFormField<String>(
              value: _accountType,
              items: _accountTypes.map((type) => DropdownMenuItem(value: type, child: Text(type))).toList(),
              onChanged: (val) => setState(() => _accountType = val!),
              decoration: InputDecoration(
                labelText: '账户类型',
                prefixIcon: const Icon(Icons.category_outlined),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Theme.of(context).colorScheme.primary, width: 2),
                ),
                filled: true,
                fillColor: Theme.of(context).colorScheme.surfaceContainerHighest.withOpacity(0.3),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              ),
            ),
            
            const SizedBox(height: 24),
            
            _buildTextField(
              controller: _originalAmountController,
              label: '初始贷款总额',
              hint: '0.00',
              prefixText: '¥ ',
              required: true,
              keyboardType: TextInputType.number,
              helperText: '用于计算还款进度',
              onChanged: (val) {
                // Auto-fill current if empty
                if (_currentPrincipalController.text.isEmpty) {
                  _currentPrincipalController.text = val;
                }
              },
            ),
            
            const SizedBox(height: 24),
            
            Row(
              children: [
                Expanded(
                  child: _buildTextField(
                    controller: _currentPrincipalController,
                    label: '当前剩余本金',
                    hint: '0.00',
                    prefixText: '¥ ',
                    required: true,
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildTextField(
                    controller: _interestRateController,
                    label: '年化利率',
                    hint: '0.0',
                    keyboardType: TextInputType.number,
                    suffixText: '%',
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    String? hint,
    bool required = false,
    TextInputType? keyboardType,
    String? helperText,
    String? suffixText,
    String? prefixText,
    Widget? prefixIcon,
    Function(String)? onChanged,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      onChanged: onChanged,
      decoration: InputDecoration(
        labelText: required ? '$label *' : label,
        hintText: hint,
        helperText: helperText,
        suffixText: suffixText,
        prefixText: prefixText,
        prefixIcon: prefixIcon,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Theme.of(context).colorScheme.primary, width: 2),
        ),
        filled: true,
        fillColor: Theme.of(context).colorScheme.surfaceContainerHighest.withOpacity(0.3),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
      validator: required ? (value) {
        if (value == null || value.isEmpty) {
          return '请输入$label';
        }
        return null;
      } : null,
    );
  }
}
