import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/asset.dart';
import '../services/api_service.dart';
import 'auth_provider.dart';

part 'asset_provider.g.dart';

@riverpod
class AssetList extends _$AssetList {
  @override
  Future<List<UserAsset>> build() async {
    final authState = ref.watch(authStateProvider);
    final user = authState.value;
    if (user == null) return [];
    
    return await _fetchAssets(user.id);
  }

  Future<List<UserAsset>> _fetchAssets(int userId) async {
    try {
      final apiService = ref.read(apiServiceProvider);
      final response = await apiService.getAssets(userId);
      
      if (response.data['success'] == true) {
        final List<dynamic> assetsData = response.data['data'];
        return assetsData.map((json) => UserAsset.fromJson(json)).toList();
      } else {
        throw Exception(response.data['message'] ?? 'Failed to fetch assets');
      }
    } catch (e) {
      throw Exception('Network error: ${e.toString()}');
    }
  }

  Future<void> createAsset({
    required AssetType assetType,
    required String name,
    required double value,
    bool isConfirmed = false,
    Map<String, dynamic>? metadata,
  }) async {
    final authState = ref.read(authStateProvider);
    final user = authState.value;
    if (user == null) throw Exception('User not authenticated');

    try {
      final apiService = ref.read(apiServiceProvider);
      await apiService.createAsset(user.id, {
        'asset_type': assetType.name,
        'name': name,
        'value': value,
        'is_confirmed': isConfirmed,
        'extra_data': metadata,
      });
      
      // Refresh the asset list
      ref.invalidateSelf();
    } catch (e) {
      throw Exception('Failed to create asset: ${e.toString()}');
    }
  }

  Future<void> updateAsset({
    required int assetId,
    AssetType? assetType,
    String? name,
    double? value,
    bool? isConfirmed,
    Map<String, dynamic>? metadata,
  }) async {
    final authState = ref.read(authStateProvider);
    final user = authState.value;
    if (user == null) throw Exception('User not authenticated');

    try {
      final apiService = ref.read(apiServiceProvider);
      final updateData = <String, dynamic>{};
      
      if (assetType != null) updateData['asset_type'] = assetType.name;
      if (name != null) updateData['name'] = name;
      if (value != null) updateData['value'] = value;
      if (isConfirmed != null) updateData['is_confirmed'] = isConfirmed;
      if (metadata != null) updateData['extra_data'] = metadata;

      await apiService.updateAsset(user.id, assetId, updateData);
      
      // Refresh the asset list
      ref.invalidateSelf();
    } catch (e) {
      throw Exception('Failed to update asset: ${e.toString()}');
    }
  }

  Future<void> deleteAsset(int assetId) async {
    final authState = ref.read(authStateProvider);
    final user = authState.value;
    if (user == null) throw Exception('User not authenticated');

    try {
      final apiService = ref.read(apiServiceProvider);
      await apiService.deleteAsset(user.id, assetId);
      
      // Refresh the asset list
      ref.invalidateSelf();
    } catch (e) {
      throw Exception('Failed to delete asset: ${e.toString()}');
    }
  }
}

@riverpod
class PortfolioHealthData extends _$PortfolioHealthData {
  @override
  Future<PortfolioHealth> build() async {
    final authState = ref.watch(authStateProvider);
    final user = authState.value;
    if (user == null) {
      return const PortfolioHealth(
        netWorth: 0,
        realEstateRatio: 0,
        liquidityRatio: 0,
        riskWarnings: [],
      );
    }
    
    return await _fetchPortfolioHealth(user.id);
  }

  Future<PortfolioHealth> _fetchPortfolioHealth(int userId) async {
    try {
      final apiService = ref.read(apiServiceProvider);
      final response = await apiService.getPortfolioHealth(userId);
      
      if (response.data['success'] == true) {
        return PortfolioHealth.fromJson(response.data['data']);
      } else {
        throw Exception(response.data['message'] ?? 'Failed to fetch portfolio health');
      }
    } catch (e) {
      throw Exception('Network error: ${e.toString()}');
    }
  }

  void refresh() {
    ref.invalidateSelf();
  }
}

// Computed providers for dashboard metrics
@riverpod
Map<AssetType, double> assetDistribution(AssetDistributionRef ref) {
  final assetsAsync = ref.watch(assetListProvider);
  
  return assetsAsync.when(
    data: (assets) {
      final distribution = <AssetType, double>{};
      double totalValue = 0;
      
      // Calculate total value
      for (final asset in assets) {
        if (asset.assetType != AssetType.liability) {
          totalValue += asset.value;
        }
      }
      
      // Calculate percentages
      for (final asset in assets) {
        if (asset.assetType != AssetType.liability) {
          distribution[asset.assetType] = 
              (distribution[asset.assetType] ?? 0) + (asset.value / totalValue);
        }
      }
      
      return distribution;
    },
    loading: () => {},
    error: (_, __) => {},
  );
}

@riverpod
double totalNetWorth(TotalNetWorthRef ref) {
  final assetsAsync = ref.watch(assetListProvider);
  
  return assetsAsync.when(
    data: (assets) {
      double totalAssets = 0;
      double totalLiabilities = 0;
      
      for (final asset in assets) {
        if (asset.assetType == AssetType.liability) {
          totalLiabilities += asset.value;
        } else {
          totalAssets += asset.value;
        }
      }
      
      return totalAssets - totalLiabilities;
    },
    loading: () => 0,
    error: (_, __) => 0,
  );
}