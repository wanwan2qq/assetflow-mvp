import 'package:flutter/material.dart';
import 'asset_form_scaffold.dart';

class InsuranceForm extends StatefulWidget {
  const InsuranceForm({super.key});

  @override
  State<InsuranceForm> createState() => _InsuranceFormState();
}

class _InsuranceFormState extends State<InsuranceForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _coverageController = TextEditingController();
  final _premiumController = TextEditingController();
  final _nextPaymentDateController = TextEditingController();
  
  String _insuranceType = '重疾险';
  final List<String> _insuranceTypes = ['重疾险', '医疗险', '寿险', '意外险', '年金险'];
  
  String _insuredPerson = '本人';
  final List<String> _insuredPersons = ['本人', '配偶', '子女', '父母'];

  bool get _isValid => _nameController.text.isNotEmpty && _coverageController.text.isNotEmpty;

  @override
  void dispose() {
    _nameController.dispose();
    _coverageController.dispose();
    _premiumController.dispose();
    _nextPaymentDateController.dispose();
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
      title: '新建保单',
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
              label: '保险名称',
              hint: '例如: 平安福重疾险',
              required: true,
              prefixIcon: const Icon(Icons.description_outlined),
            ),
            const SizedBox(height: 24),

            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _insuranceType,
                    items: _insuranceTypes.map((type) => DropdownMenuItem(value: type, child: Text(type))).toList(),
                    onChanged: (val) => setState(() => _insuranceType = val!),
                    decoration: InputDecoration(
                      labelText: '险种类型',
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
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
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _insuredPerson,
                    items: _insuredPersons.map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                    onChanged: (val) => setState(() => _insuredPerson = val!),
                    decoration: InputDecoration(
                      labelText: '被保人',
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
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
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            
            _buildTextField(
              controller: _coverageController,
              label: '核心保障额度',
              hint: '0,000',
              prefixText: '¥ ',
              required: true,
              keyboardType: TextInputType.number,
              helperText: '如重疾保额/医疗限额',
            ),
            const SizedBox(height: 24),
            
            Row(
              children: [
                Expanded(
                  child: _buildTextField(
                    controller: _premiumController,
                    label: '年交保费',
                    hint: '0.00',
                    prefixText: '¥ ',
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: GestureDetector(
                    onTap: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: DateTime.now(),
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(const Duration(days: 365 * 10)),
                      );
                      if (date != null) {
                        _nextPaymentDateController.text = "${date.year}-${date.month.toString().padLeft(2,'0')}-${date.day.toString().padLeft(2,'0')}";
                      }
                    },
                    child: AbsorbPointer(
                      child: _buildTextField(
                        controller: _nextPaymentDateController,
                        label: '下次缴费日',
                        hint: '选择日期',
                        suffixIcon: const Icon(Icons.calendar_today, size: 16),
                      ),
                    ),
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
    String? prefixText,
    Widget? prefixIcon,
    Widget? suffixIcon,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: required ? '$label *' : label,
        hintText: hint,
        helperText: helperText,
        prefixText: prefixText,
        prefixIcon: prefixIcon,
        suffixIcon: suffixIcon,
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
