import 'package:flutter/material.dart';

import 'asset_form_scaffold.dart';

class RealEstateForm extends StatefulWidget {
  const RealEstateForm({super.key});

  @override
  State<RealEstateForm> createState() => _RealEstateFormState();
}

class _RealEstateFormState extends State<RealEstateForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _locationController = TextEditingController(); // Mock selection for now
  final _purchasePriceController = TextEditingController();
  final _valuationController = TextEditingController();
  bool _tryAIValuation = false;
  
  bool get _isValid => _nameController.text.isNotEmpty && _locationController.text.isNotEmpty;

  @override
  void dispose() {
    _nameController.dispose();
    _locationController.dispose();
    _purchasePriceController.dispose();
    _valuationController.dispose();
    super.dispose();
  }

  void _onSave() {
    if (_formKey.currentState!.validate()) {
       ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('已成功添加 ${_nameController.text}')),
      );
      Navigator.pop(context); // Close form
      // TODO: Navigate to Details Page or trigger creation logic
    }
  }

  @override
  Widget build(BuildContext context) {
    return AssetFormScaffold(
      title: '新建房产',
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
              label: '房产名称',
              hint: '例如: 海淀万柳书院',
              required: true,
              prefixIcon: const Icon(Icons.home_work_outlined),
            ),
            const SizedBox(height: 24),
            _buildTextField(
              controller: _locationController,
              label: '所在位置',
              hint: '选择城市/区域',
              required: true,
              prefixIcon: const Icon(Icons.location_on_outlined),
              suffixIcon: const Icon(Icons.arrow_forward_ios, size: 16),
              readOnly: false, 
              helperText: '用于AI自动估值',
            ),
             const SizedBox(height: 24),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: _buildTextField(
                    controller: _purchasePriceController,
                    label: '购入价格',
                    hint: '0.00',
                    prefixText: '¥ ',
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildTextField(
                    controller: _valuationController,
                    label: '当前估值',
                    hint: '0.00',
                    prefixText: '¥ ',
                    keyboardType: TextInputType.number,
                    helperText: '不填则等待AI评估',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            
            // AI Valuation Switch (M3 preference over Checkbox for this context usually, but CheckboxListTile is fine too. Let's use SwitchListTile for cleaner look)
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('创建后立即尝试 AI 估值'),
              value: _tryAIValuation,
              onChanged: (val) {
                setState(() {
                  _tryAIValuation = val;
                });
              },
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
    Widget? suffixIcon,
    Widget? prefixIcon,
    String? prefixText,
    bool readOnly = false,
    String? helperText,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      readOnly: readOnly,
      decoration: InputDecoration(
        labelText: required ? '$label *' : label,
        hintText: hint,
        prefixIcon: prefixIcon,
        prefixText: prefixText,
        suffixIcon: suffixIcon,
        helperText: helperText,
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
