import 'package:flutter/material.dart';
import 'asset_form_scaffold.dart';

class InvestmentForm extends StatefulWidget {
  const InvestmentForm({super.key});

  @override
  State<InvestmentForm> createState() => _InvestmentFormState();
}

class _InvestmentFormState extends State<InvestmentForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _costController = TextEditingController();
  final _marketValueController = TextEditingController();
  
  String _investmentType = '基金';
  final List<String> _investmentTypes = ['基金', '股票', '理财', '定存', '其他'];

  bool get _isValid => _nameController.text.isNotEmpty && _costController.text.isNotEmpty;

  @override
  void dispose() {
    _nameController.dispose();
    _costController.dispose();
    _marketValueController.dispose();
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
      title: '新建投资/理财',
      onCancel: () => Navigator.pop(context),
      onSave: _onSave,
      isSaveEnabled: _isValid,
      child: Form(
        key: _formKey,
        onChanged: () => setState(() {}),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
             // Type Dropdown
            DropdownButtonFormField<String>(
              value: _investmentType,
              items: _investmentTypes.map((type) => DropdownMenuItem(value: type, child: Text(type))).toList(),
              onChanged: (val) => setState(() => _investmentType = val!),
              decoration: InputDecoration(
                labelText: '投资类型',
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
              controller: _nameController,
              label: '产品名称/代码',
              hint: '例如: 易方达蓝筹 / 001234',
              required: true,
              prefixIcon: const Icon(Icons.description_outlined),
            ),
            const SizedBox(height: 24),
            
            _buildTextField(
              controller: _costController,
              label: '持仓成本/本金',
              hint: '0.00',
              prefixText: '¥ ',
              required: true,
              keyboardType: TextInputType.number,
              helperText: '用于计算盈亏',
              onChanged: (val) {
                 if (_marketValueController.text.isEmpty) {
                  _marketValueController.text = val;
                }
              }
            ),
            const SizedBox(height: 24),
            
            _buildTextField(
              controller: _marketValueController,
              label: '当前市值/估值',
              hint: '0.00',
              prefixText: '¥ ',
              keyboardType: TextInputType.number,
              helperText: '不填默认等于成本',
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
