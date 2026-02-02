import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/models/action_plan.dart';
import '../../../../core/services/action_plan_service.dart';
import '../../../../shared/widgets/action_plan_card.dart';

// Provider for fetching plans
final actionPlansProvider = FutureProvider.autoDispose.family<List<ActionPlan>, String?>((ref, status) async {
  final service = ref.watch(actionPlanServiceProvider);
  return service.getPlans(status: status);
});

// Provider for stats
final actionPlanStatsProvider = FutureProvider.autoDispose((ref) async {
  final service = ref.watch(actionPlanServiceProvider);
  return service.getStats();
});

class ActionPlansPage extends ConsumerStatefulWidget {
  const ActionPlansPage({super.key});

  @override
  ConsumerState<ActionPlansPage> createState() => _ActionPlansPageState();
}

class _ActionPlansPageState extends ConsumerState<ActionPlansPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('行动方案'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '执行中'),
            Tab(text: '待采纳'),
            Tab(text: '已完成'),
          ],
        ),
      ),
      body: Column(
        children: [
          _buildStatsHeader(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _PlanList(status: 'in_progress'),
                _PlanList(status: 'pending'),
                _PlanList(status: 'completed'), // Changed from All to Completed
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsHeader() {
    final statsAsync = ref.watch(actionPlanStatsProvider);

    return statsAsync.when(
      data: (stats) {
        return Container(
          padding: const EdgeInsets.all(16),
          color: Theme.of(context).cardColor,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatItem('执行中', stats['in_progress'] ?? 0, Colors.blue),
              _buildStatItem('待采纳', stats['pending'] ?? 0, Colors.orange),
              _buildStatItem('已完成', stats['completed'] ?? 0, Colors.green),
            ],
          ),
        );
      },
      loading: () => const LinearProgressIndicator(minHeight: 2),
      error: (_, __) => const SizedBox.shrink(),
    );
  }

  Widget _buildStatItem(String label, int count, Color color) {
    return Column(
      children: [
        Text(
          count.toString(),
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 12,
          ),
        ),
      ],
    );
  }
}

class _PlanList extends ConsumerWidget {
  final String? status;

  const _PlanList({this.status});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plansAsync = ref.watch(actionPlansProvider(status));

    return RefreshIndicator(
      onRefresh: () async {
         ref.invalidate(actionPlansProvider(status));
         ref.invalidate(actionPlanStatsProvider);
      },
      child: plansAsync.when(
        data: (plans) {
          if (plans.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.assignment_outlined, size: 64, color: Colors.grey[300]),
                  const SizedBox(height: 16),
                  Text(
                    '暂无${_getStatusLabel(status)}方案',
                    style: TextStyle(color: Colors.grey[500]),
                  ),
                ],
              ),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: plans.length,
            itemBuilder: (context, index) {
              final plan = plans[index];
              return ActionPlanCard(
                plan: plan,
                onExecute: plan.status == 'pending' ? () async {
                   final service = ref.read(actionPlanServiceProvider);
                   await service.adoptPlan(plan.id!);
                   ref.invalidate(actionPlansProvider); // Refresh all lists
                   ref.invalidate(actionPlanStatsProvider);
                   ScaffoldMessenger.of(context).showSnackBar(
                     const SnackBar(content: Text('已采纳方案')),
                   );
                } : null,
                onDismiss: plan.status == 'pending' ? () async {
                   // Service call is handled inside ActionPlanCard with reason
                   ref.invalidate(actionPlansProvider);
                   ref.invalidate(actionPlanStatsProvider);
                } : null,
                onStepUpdate: plan.status == 'in_progress' ? (step, newStatus) async {
                   final service = ref.read(actionPlanServiceProvider);
                   await service.updateStepStatus(plan.id!, step.id!, newStatus);
                   // Refresh to reflect changes (e.g. checkbox state, completion time)
                   ref.invalidate(actionPlansProvider);
                   ref.invalidate(actionPlanStatsProvider);
                } : null,
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('加载失败: $err')),
      ),
    );
  }
  
  String _getStatusLabel(String? status) {
      if (status == 'in_progress') return '进行中';
      if (status == 'pending') return '待处理';
      if (status == 'completed') return '已完成';
      return '相关';
  }
}
