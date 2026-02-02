import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AssetEditSheet extends StatefulWidget {
  final Map<String, dynamic> assetData;
  final Function(Map<String, dynamic>) onConfirm;

  const AssetEditSheet({
    super.key,
    required this.assetData,
    required this.onConfirm,
  });

  @override
  State<AssetEditSheet> createState() => _AssetEditSheetState();
}

class _AssetEditSheetState extends State<AssetEditSheet> {
  late TextEditingController _nameController;
  late TextEditingController _valueController;
  
  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.assetData['name'] ?? '');
    final val = (widget.assetData['value'] as num?)?.toDouble() ?? 0;
    _valueController = TextEditingController(text: val.toString());
  }
  
  @override
  void dispose() {
    _nameController.dispose();
    _valueController.dispose();
    super.dispose();
  }

  void _handleConfirm() {
    final name = _nameController.text.trim();
    final val = double.tryParse(_valueController.text);
    
    if (name.isNotEmpty && val != null) {
      widget.onConfirm({
        ...widget.assetData,
        'name': name,
        'value': val,
      });
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16,
        right: 16,
        top: 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
           Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '编辑资产信息',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              IconButton(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.close),
              )
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(
              labelText: '资产名称',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _valueController,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
            ],
            decoration: const InputDecoration(
              labelText: '资产价值 (元)',
              border: OutlineInputBorder(),
              prefixText: '¥ ',
            ),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _handleConfirm,
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: const Text('保存修改'),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
