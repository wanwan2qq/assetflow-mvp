import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/wealth_history.dart';
import '../models/cash_flow_item.dart';
// import '../services/api_service.dart'; // Uncomment when API is ready
// import 'auth_provider.dart';

part 'wealth_provider.g.dart';

// Mock data for Wealth History until API is ready
@riverpod
Future<List<WealthHistory>> wealthHistory(WealthHistoryRef ref) async {
  // Simulate network delay
  await Future.delayed(const Duration(seconds: 1));
  
  final now = DateTime.now();
  return List.generate(12, (index) {
    return WealthHistory(
      date: DateTime(now.year, now.month - index, 1),
      netWorth: 1000000.0 + (index * 10000), // Random growth
      totalAssets: 1500000.0 + (index * 15000),
      totalLiabilities: 500000.0 + (index * 5000),
    );
  }).reversed.toList();
}

// Mock data for Cash Flow until API is ready
@riverpod
class CashFlow extends _$CashFlow {
  @override
  Future<List<CashFlowItem>> build() async {
    // Simulate network delay
    await Future.delayed(const Duration(seconds: 1));
    
    // Initial mock data
    return [
      const CashFlowItem(
        id: '1',
        name: 'Salary',
        amount: 50000.0,
        type: CashFlowType.income,
        frequency: CashFlowFrequency.monthly,
      ),
      const CashFlowItem(
        id: '2',
        name: 'Rent Income',
        amount: 5000.0,
        type: CashFlowType.income,
        frequency: CashFlowFrequency.monthly,
        relatedAssetId: 101, // Example ID
      ),
      const CashFlowItem(
        id: '3',
        name: 'Mortgage Payment',
        amount: 12000.0,
        type: CashFlowType.expense,
        frequency: CashFlowFrequency.monthly,
        relatedAssetId: 201, // Example ID
      ),
      const CashFlowItem(
        id: '4',
        name: 'Car Loan',
        amount: 3500.0,
        type: CashFlowType.expense,
        frequency: CashFlowFrequency.monthly,
        relatedAssetId: 202,
      ),
    ];
  }

  Future<void> addCashFlow(CashFlowItem item) async {
    final currentState = state;
    if (currentState.value == null) return;
    
    // Simulate API call
    state = const AsyncValue.loading();
    await Future.delayed(const Duration(milliseconds: 500));
    
    final currentList = currentState.value!;
    state = AsyncValue.data([...currentList, item]);
  }

  Future<void> updateCashFlow(CashFlowItem item) async {
    final currentState = state;
    if (currentState.value == null) return;

    state = const AsyncValue.loading();
    await Future.delayed(const Duration(milliseconds: 500));

    final currentList = currentState.value!;
    final index = currentList.indexWhere((e) => e.id == item.id);
    if (index != -1) {
      final newList = List<CashFlowItem>.from(currentList);
      newList[index] = item;
      state = AsyncValue.data(newList);
    }
  }

  Future<void> deleteCashFlow(String id) async {
    final currentState = state;
    if (currentState.value == null) return;

    state = const AsyncValue.loading();
    await Future.delayed(const Duration(milliseconds: 500));

    final currentList = currentState.value!;
    state = AsyncValue.data(currentList.where((e) => e.id != id).toList());
  }
}

// Projected data provider
@riverpod
Future<Map<String, double>> projectedWealth(ProjectedWealthRef ref) async {
  await Future.delayed(const Duration(milliseconds: 500));
  return {
    'annual_savings': 150000.0,
    'projected_net_worth_1y': 1200000.0,
  };
}
