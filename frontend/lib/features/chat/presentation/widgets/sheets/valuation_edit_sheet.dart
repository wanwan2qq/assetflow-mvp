import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class ValuationEditSheet extends StatefulWidget {
  final double initialPrice; // In Wan (万)
  final Function(double) onConfirm;

  const ValuationEditSheet({
    super.key,
    required this.initialPrice,
    required this.onConfirm,
  });

  @override
  State<ValuationEditSheet> createState() => _ValuationEditSheetState();
}

class _ValuationEditSheetState extends State<ValuationEditSheet> {
  late TextEditingController _controller;
  
  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialPrice.toStringAsFixed(1));
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleConfirm() {
    final val = double.tryParse(_controller.text);
    if (val != null) {
      widget.onConfirm(val * 10000); // Convert back to Yuan
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
                '调整房产估值',
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
            controller: _controller,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
            ],
            decoration: const InputDecoration(
              labelText: '估值 (万元)',
              border: OutlineInputBorder(),
              suffixText: '万',
            ),
            autofocus: true,
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _handleConfirm,
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: const Text('确认修改'),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
