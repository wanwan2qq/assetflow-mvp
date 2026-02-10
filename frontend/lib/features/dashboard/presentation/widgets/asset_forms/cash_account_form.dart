import 'package:flutter/material.dart';
import 'asset_form_scaffold.dart';

class CashAccountForm extends StatefulWidget {
  const CashAccountForm({super.key});

  @override
  State<CashAccountForm> createState() => _CashAccountFormState();
}

class _CashAccountFormState extends State<CashAccountForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _balanceController = TextEditingController();
  
  String _accountType = '银行卡';
  final List<String> _accountTypes = ['银行卡', '现金', '网络账户(微信/支付宝)', '其他'];

  bool get _isValid => _nameController.text.isNotEmpty && _balanceController.text.isNotEmpty;

  @override
  void dispose() {
    _nameController.dispose();
    _balanceController.dispose();
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
      title: '新建账户',
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
              label: '账户名称',
              hint: '例如: 招行工资卡/微信零钱',
              required: true,
              prefixIcon: const Icon(Icons.account_balance_wallet_outlined),
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
              controller: _balanceController,
              label: '当前余额',
              hint: '0.00',
              prefixText: '¥ ',
              required: true,
              keyboardType: TextInputType.number,
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
    String? prefixText,
    Widget? prefixIcon,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: required ? '$label *' : label,
        hintText: hint,
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
