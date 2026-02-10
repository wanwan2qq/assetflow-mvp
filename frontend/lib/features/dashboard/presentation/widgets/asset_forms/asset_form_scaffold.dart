import 'package:flutter/material.dart';

class AssetFormScaffold extends StatelessWidget {
  final String title;
  final Widget child;
  final VoidCallback onCancel;
  final VoidCallback onSave;
  final bool isSaveEnabled;
  final String saveLabel;

  const AssetFormScaffold({
    super.key,
    required this.title,
    required this.child,
    required this.onCancel,
    required this.onSave,
    this.isSaveEnabled = true,
    this.saveLabel = '创建',
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Column(
      children: [
        // M3 Header
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Title Centered
              Align(
                alignment: Alignment.center,
                child: Text(
                  title,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              // Left: Cancel
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(
                  onPressed: onCancel,
                  style: TextButton.styleFrom(
                    foregroundColor: colorScheme.onSurfaceVariant,
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                  ),
                  child: const Text('取消'),
                ),
              ),
              // Right: Save Action
              Align(
                alignment: Alignment.centerRight,
                child: FilledButton(
                  onPressed: isSaveEnabled ? onSave : null,
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                  ),
                  child: Text(saveLabel),
                ),
              ),
            ],
          ),
        ),
        Divider(height: 1, color: colorScheme.outlineVariant),
        // Content
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: child,
          ),
        ),
      ],
    );
  }
}
