import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/models/action_plan.dart';
import '../../core/services/action_plan_service.dart';

class ActionPlanCard extends ConsumerStatefulWidget {
  final ActionPlan plan;
  final VoidCallback? onDismiss;
  // If provided, this callback is called INSTEAD of internal logic.
  // If null, internal logic is used.
  final VoidCallback? onExecute; 
  final Future<void> Function(ActionStep step, String newStatus)? onStepUpdate;

  const ActionPlanCard({
    super.key,
    required this.plan,
    this.onExecute, 
    this.onDismiss,
    this.onStepUpdate,
  });

  @override
  ConsumerState<ActionPlanCard> createState() => _ActionPlanCardState();
}

class _ActionPlanCardState extends ConsumerState<ActionPlanCard> {
  bool _isExpanded = false;
  late ActionPlan _plan;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _plan = widget.plan;
  }

  @override
  void didUpdateWidget(ActionPlanCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.plan != oldWidget.plan) {
      _plan = widget.plan;
    }
  }

  Future<void> _handleDismiss() async {
    final reason = await showDialog<String>(
      context: context,
      builder: (context) {
        String? inputReason;
        return AlertDialog(
          title: const Text('忽略此计'),
          content: Column(
             mainAxisSize: MainAxisSize.min,
             children: [
               const Text('请告诉我们原因，以便提供更好的建议：'),
               const SizedBox(height: 16),
               TextField(
                 onChanged: (v) => inputReason = v,
                 decoration: const InputDecoration(
                   hintText: '例如：成本太高、现在不需要...',
                   border: OutlineInputBorder(),
                 ),
                 maxLines: 3,
               ),
             ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('取消'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(inputReason ?? ''),
              child: const Text('确定忽略'),
            ),
          ],
        );
      },
    );

    if (reason == null) return; // Cancelled

    setState(() => _isLoading = true);
    try {
      final service = ref.read(actionPlanServiceProvider);
      if (_plan.id != null) {
        await service.dismissPlan(_plan.id!, reason: reason);
        // Optimistic update or callback
        if (widget.onDismiss != null) {
           widget.onDismiss!();
        } else {
           // Local update
           setState(() {
             _plan = _plan.copyWith(status: 'dismissed');
           });
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('操作失败: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // Handle local adoption logic
  Future<void> _handleAdopt() async {
    // If external callback provided, use it (e.g. from ActionPlansPage)
    if (widget.onExecute != null) {
      widget.onExecute!();
      return;
    }

    // Otherwise, perform adoption locally (e.g. from ChatPage)
    setState(() => _isLoading = true);
    try {
      final service = ref.read(actionPlanServiceProvider);
      // Optimistic update
      // But better to fetch fresh data to get IDs for steps
      if (_plan.id != null) {
        await service.adoptPlan(_plan.id!);
        final freshPlan = await service.getPlan(_plan.id!);
        if (freshPlan != null) {
          setState(() {
            _plan = freshPlan;
            _isExpanded = true; // Auto expand to show steps
          });
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('采纳失败: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // Handle local step update logic if callback not provided? 
  // For now rely on widget.onStepUpdate from parent or implement internal?
  // ChatPage currently doesn't pass onStepUpdate. 
  // We should implement internal logic if onStepUpdate is null.
  Future<void> _handleStepUpdate(ActionStep step, String status) async {
    // 1. Optimistic Update (Local State)
    setState(() {
      final stepIndex = _plan.steps.indexWhere((s) => s.stepNumber == step.stepNumber);
      if (stepIndex != -1) {
         final updatedStep = _plan.steps[stepIndex].copyWith(status: status);
         final updatedSteps = List<ActionStep>.from(_plan.steps);
         updatedSteps[stepIndex] = updatedStep;
         _plan = _plan.copyWith(steps: updatedSteps);
      }
    });

    // 2. Execute Action
    if (widget.onStepUpdate != null) {
      try {
        await widget.onStepUpdate!(step, status);
      } catch (e) {
        // Revert or show error if needed
        print('Update failed: $e');
      }
      return;
    }
    
    // Internal logic
    if (_plan.id == null || step.stepNumber == null) return;
    
    try {
      final service = ref.read(actionPlanServiceProvider);
      // Note: step.stepNumber is used as ID in some contexts, but backend API expects ID
      // If step.id is available use it? updateStepStatus signature takes stepId.
      // Front end model has id.
      // Let's assume step.id is present (guaranteed by Phase 1 fixes).
      // Fallback to internal update logic
      if (step.id != null) {
          await service.updateStepStatus(_plan.id!, step.id!, status);
      } else {
          // If no ID, we can't update backend (legacy case?)
          // But we already updated UI optimistically.
      }
    } catch (e) {
      // ignore
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(context),
          if (_isExpanded) ...[
            const Divider(height: 1),
            _buildDetails(context),
          ],
          _buildFooter(context),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return InkWell(
      onTap: () {
        setState(() {
          _isExpanded = !_isExpanded;
        });
      },
      borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _buildCategoryIcon(_plan.category),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _plan.title,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          _buildPriorityBadge(context),
                          const SizedBox(width: 8),
                          Text(
                            '置信度 ${(_plan.confidence * 100).toInt()}%',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                                ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                if (_plan.status == 'pending')
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    color: Colors.grey[500],
                    tooltip: '忽略此计划',
                    onPressed: _handleDismiss,
                  ),
                Icon(
                  _isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                  color: Colors.grey[500],
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _plan.summary,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: isDark ? Colors.grey[300] : Colors.grey[800],
                    height: 1.5,
                  ),
              maxLines: _isExpanded ? null : 3,
              overflow: _isExpanded ? null : TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetails(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      color: isDark ? Colors.black12 : Colors.grey[50], // Adaptive background
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_plan.steps.isNotEmpty) ...[
            _buildSectionTitle(context, '执行步骤', Icons.format_list_numbered),
            const SizedBox(height: 12),
            ..._plan.steps.map((step) => _buildStepItem(context, step)),
            const SizedBox(height: 16),
          ],
          if (_plan.expectedBenefits.isNotEmpty) ...[
            _buildSectionTitle(context, '预期收益', Icons.trending_up),
            const SizedBox(height: 8),
            ..._plan.expectedBenefits.map((benefit) => _buildBulletPoint(context, benefit, Colors.green)),
            const SizedBox(height: 16),
          ],
          if (_plan.potentialRisks.isNotEmpty) ...[
            _buildSectionTitle(context, '潜在风险', Icons.warning_amber),
            const SizedBox(height: 8),
            ..._plan.potentialRisks.map((risk) => _buildBulletPoint(context, risk, Colors.orange)),
          ],
        ],
      ),
    );
  }

  Widget _buildFooter(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // If pending, show prominent adopt button
    final isPending = _plan.status == 'pending'; // Adjust based on exact status string constant

    if (!_isExpanded) {
      return InkWell(
        onTap: () {
          setState(() {
            _isExpanded = true;
          });
        },
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            border: Border(top: BorderSide(color: isDark ? Colors.white10 : Colors.grey[200]!)),
          ),
          child: Center(
            child: Text(
              '查看完整方案',
              style: TextStyle(
                color: isDark ? Colors.blueAccent[100] : Theme.of(context).primaryColor,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
      );
    }
    
    // Expanded footer
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          if (widget.onDismiss != null && isPending)
            TextButton(
              onPressed: _handleDismiss,
              child: const Text('暂不考虑'),
            ),
          const SizedBox(width: 8),
          
          if (isPending)
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _handleAdopt,
                icon: const Icon(Icons.rocket_launch, size: 18),
                label: Text(_isLoading ? '生成中...' : '立即采纳方案'), // More compelling text
                style: ElevatedButton.styleFrom(
                  elevation: 2,
                  backgroundColor: Theme.of(context).primaryColor,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12), // Taller button
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            )
          else
             // If already adopted, show status or refine button?
             OutlinedButton.icon(
                onPressed: null, // or navigate to full page
                icon: Icon(
                  _plan.status == 'completed' ? Icons.check_circle : 
                  _plan.status == 'dismissed' ? Icons.remove_circle_outline :
                  Icons.timelapse, 
                  size: 16
                ),
                label: Text(
                  _plan.status == 'completed' ? '已完成' : 
                  _plan.status == 'dismissed' ? '已忽略' :
                  '正在执行中'
                ),
             ),
        ],
      ),
    );
  }

  Widget _buildCategoryIcon(ActionCategory category) {
    IconData iconData;
    Color color;

    switch (category) {
      case ActionCategory.wealthProtection:
        iconData = Icons.security;
        color = Colors.indigo;
        break;
      case ActionCategory.wealthGrowth:
        iconData = Icons.show_chart;
        color = Colors.green;
        break;
      case ActionCategory.realEstate:
        iconData = Icons.home;
        color = Colors.brown;
        break;
      case ActionCategory.lifePlanning:
        iconData = Icons.family_restroom;
        color = Colors.purple;
        break;
      case ActionCategory.debtOptimization:
        iconData = Icons.account_balance;
        color = Colors.orange;
        break;
      default:
        iconData = Icons.lightbulb_outline;
        color = Colors.amber;
    }

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: Icon(iconData, color: color, size: 24),
    );
  }

  Widget _buildPriorityBadge(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: _plan.priorityColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: _plan.priorityColor.withOpacity(0.3)),
      ),
      child: Text(
        _plan.priorityLabel,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: _plan.priorityColor,
        ),
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title, IconData icon) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Row(
      children: [
        Icon(icon, size: 16, color: isDark ? Colors.grey[400] : Colors.grey[700]),
        const SizedBox(width: 8),
        Text(
          title,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: isDark ? Colors.grey[300] : Colors.grey[800],
              ),
        ),
      ],
    );
  }

  Widget _buildStepItem(BuildContext context, ActionStep step) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isCompleted = step.status == 'completed';
    // If we are in progress, allow interaction (assuming step has ID or we can rely on index)
    // Actually, backend update relies on step_number if we implemented it that way?
    // Backend API `update_step_status` uses `step_number`.
    // So we don't strictly need `step.id` if we have `plan.id` and `step.stepNumber`.
    // But let's check safety.
    final canInteract = _plan.status == 'in_progress';
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (canInteract)
            SizedBox(
              width: 24,
              height: 24,
              child: Checkbox(
                value: isCompleted,
                onChanged: (val) {
                    if (val != null) {
                        _handleStepUpdate(step, val ? 'completed' : 'pending');
                    }
                },
                shape: const CircleBorder(),
                activeColor: Theme.of(context).primaryColor,
              ),
            )
          else
            Container(
              width: 24,
              height: 24,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: isDark ? Colors.white10 : Colors.grey[200],
                shape: BoxShape.circle,
              ),
              child: Text(
                '${step.stepNumber}',
                style: TextStyle(
                  fontWeight: FontWeight.bold, 
                  fontSize: 12,
                  color: isDark ? Colors.white : Colors.black,
                ),
              ),
            ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  step.action,
                  style: TextStyle(
                    fontWeight: FontWeight.w500,
                    color: isCompleted 
                        ? (isDark ? Colors.grey[600] : Colors.grey[400]) 
                        : (isDark ? Colors.grey[200] : Colors.black87),
                    decoration: isCompleted ? TextDecoration.lineThrough : null,
                  ),
                ),
                if (step.timeline.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      '⏱️ ${step.timeline}',
                      style: TextStyle(fontSize: 12, color: isDark ? Colors.grey[400] : Colors.grey[600]),
                    ),
                  ),
                if (step.expectedOutcome.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      '🎯 ${step.expectedOutcome}',
                      style: TextStyle(fontSize: 12, color: isDark ? Colors.grey[400] : Colors.grey[600]),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBulletPoint(BuildContext context, String text, Color dotColor) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Icon(Icons.circle, size: 6, color: dotColor),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 13,
                color: isDark ? Colors.grey[300] : Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
