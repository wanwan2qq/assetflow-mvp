import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../core/models/asset.dart';
import '../../../../../core/providers/asset_provider.dart';

class LiabilityEditSheet extends ConsumerStatefulWidget {
  final UserAsset asset;

  const LiabilityEditSheet({super.key, required this.asset});

  @override
  ConsumerState<LiabilityEditSheet> createState() => _LiabilityEditSheetState();
}

class _LiabilityEditSheetState extends ConsumerState<LiabilityEditSheet> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _balanceController;
  late TextEditingController _rateController;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _balanceController = TextEditingController(text: widget.asset.value.toString());
    _rateController = TextEditingController(text: widget.asset.interestRate?.toString() ?? '');
  }

  @override
  void dispose() {
    _balanceController.dispose();
    _rateController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final newValue = double.parse(_balanceController.text);
      final newRate = double.tryParse(_rateController.text);

      // Update metadata with new rate
      final metadata = Map<String, dynamic>.from(widget.asset.metadata ?? {});
      if (newRate != null) {
        metadata['interest_rate'] = newRate;
      }
      // If user manually updates, we can consider it confirmed or higher confidence
      metadata['confidence'] = 1.0; 

      await ref.read(assetListProvider.notifier).updateAsset(
            assetId: widget.asset.id,
            value: newValue,
            metadata: metadata,
            isConfirmed: true,
          );

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('资产已更新')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('更新失败: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDefaultRate = widget.asset.interestRate == 4.2;

    return Container(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        top: 16,
        left: 16,
        right: 16,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '编辑负债: ${widget.asset.name}',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            if (isDefaultRate)
              Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.amber.withOpacity(0.1),
                  border: Border.all(color: Colors.amber),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber_rounded, color: Colors.amber),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        '当前利率 (4.2%) 为估算值，请确认您的实际利率以获得更精准的分析。',
                        style: TextStyle(fontSize: 12, color: Colors.brown),
                      ),
                    ),
                  ],
                ),
              ),

            TextFormField(
              controller: _balanceController,
              decoration: const InputDecoration(
                labelText: '当前欠款金额 (¥)',
                border: OutlineInputBorder(),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              validator: (value) {
                if (value == null || value.isEmpty) return '请输入金额';
                if (double.tryParse(value) == null) return '请输入有效的数字';
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _rateController,
              decoration: const InputDecoration(
                labelText: '年利率 (%)',
                border: OutlineInputBorder(),
                suffixText: '%',
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              validator: (value) {
                if (value != null && value.isNotEmpty && double.tryParse(value) == null) {
                  return '请输入有效的数字';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            
            // Update with AI Button (Mock)
            OutlinedButton.icon(
              onPressed: () {
                // Mock functionality
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('AI 正在分析您的最新数据... (Mock)')),
                );
              },
              icon: const Icon(Icons.auto_awesome),
              label: const Text('使用 AI 更新数据'),
            ),
            
            const SizedBox(height: 12),
            
            ElevatedButton(
              onPressed: _isLoading ? null : _save,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12),
                backgroundColor: Theme.of(context).primaryColor,
                foregroundColor: Colors.white,
              ),
              child: _isLoading 
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }
}
