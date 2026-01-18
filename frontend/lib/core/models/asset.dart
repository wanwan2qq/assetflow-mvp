import 'package:freezed_annotation/freezed_annotation.dart';

part 'asset.freezed.dart';
part 'asset.g.dart';

enum AssetType {
  @JsonValue('real_estate')
  realEstate,
  @JsonValue('cash')
  cash,
  @JsonValue('investment')
  investment,
  @JsonValue('insurance')
  insurance,
  @JsonValue('liability')
  liability,
}

@freezed
class UserAsset with _$UserAsset {
  const factory UserAsset({
    required int id,
    required int userId,
    required AssetType assetType,
    required String name,
    required double value,
    @Default(false) bool isConfirmed,
    Map<String, dynamic>? metadata,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _UserAsset;

  factory UserAsset.fromJson(Map<String, dynamic> json) {
    // 后端返回的字段名是 asset_type (snake_case)
    final assetTypeStr = json['asset_type'] as String? ?? json['assetType'] as String? ?? 'cash';
    
    // 匹配 AssetType 枚举值 (使用 @JsonValue 注解的值)
    AssetType assetType;
    switch (assetTypeStr.toLowerCase()) {
      case 'real_estate':
        assetType = AssetType.realEstate;
        break;
      case 'cash':
        assetType = AssetType.cash;
        break;
      case 'investment':
        assetType = AssetType.investment;
        break;
      case 'insurance':
        assetType = AssetType.insurance;
        break;
      case 'liability':
        assetType = AssetType.liability;
        break;
      default:
        assetType = AssetType.cash;
    }
    
    return UserAsset(
      id: _safeToInt(json['id']) ?? 0,
      userId: _safeToInt(json['user_id'] ?? json['userId']) ?? 0,
      assetType: assetType,
      name: json['name'] as String? ?? '',
      value: _safeToDouble(json['value']) ?? 0.0,
      isConfirmed: json['is_confirmed'] as bool? ?? json['isConfirmed'] as bool? ?? false,
      metadata: json['extra_data'] as Map<String, dynamic>? ?? json['metadata'] as Map<String, dynamic>?,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? json['createdAt'] as String? ?? '') ?? DateTime.now(),
      updatedAt: DateTime.tryParse(json['updated_at'] as String? ?? json['updatedAt'] as String? ?? '') ?? DateTime.now(),
    );
  }

  static int? _safeToInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) {
      final parsed = int.tryParse(value);
      return parsed;
    }
    return null;
  }

  static double? _safeToDouble(dynamic value) {
    if (value == null) return null;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) {
      final parsed = double.tryParse(value);
      return parsed;
    }
    return null;
  }
}

@freezed
class PortfolioHealth with _$PortfolioHealth {
  const factory PortfolioHealth({
    required double netWorth,
    required double realEstateRatio,
    required double liquidityRatio,
    required List<RiskWarning> riskWarnings,
    Map<String, dynamic>? quadrantAnalysis,
    Map<String, double>? quadrantAllocations,
    Map<String, double>? idealAllocations,
    Map<String, double>? allocationGaps,
  }) = _PortfolioHealth;

  factory PortfolioHealth.fromJson(Map<String, dynamic> json) {
    // 处理risk_warnings的数据转换
    final riskWarningsData = json['risk_warnings'] as List<dynamic>? ?? [];
    final riskWarnings = riskWarningsData.map((item) {
      final warning = item as Map<String, dynamic>;
      return RiskWarning(
        type: warning['type'] as String? ?? '',
        message: warning['description'] as String? ?? warning['title'] as String? ?? '',
        severity: warning['severity'] as String? ?? 'medium',
      );
    }).toList();

    return PortfolioHealth(
      netWorth: _safeToDouble(json['net_worth']) ?? 0.0,
      realEstateRatio: _safeToDouble(json['real_estate_ratio']) ?? 0.0,
      liquidityRatio: _safeToDouble(json['liquidity_ratio']) ?? 0.0,
      riskWarnings: riskWarnings,
      quadrantAnalysis: json['quadrant_analysis'] as Map<String, dynamic>?,
      quadrantAllocations: _convertToDoubleMap(json['quadrant_allocations']),
      idealAllocations: _convertToDoubleMap(json['ideal_allocations']),
      allocationGaps: _convertToDoubleMap(json['allocation_gaps']),
    );
  }

  static double? _safeToDouble(dynamic value) {
    if (value == null) return null;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) {
      final parsed = double.tryParse(value);
      return parsed;
    }
    return null;
  }

  static Map<String, double>? _convertToDoubleMap(dynamic data) {
    if (data == null) return null;
    if (data is Map<String, dynamic>) {
      return data.map((key, value) => MapEntry(key, _safeToDouble(value) ?? 0.0));
    }
    return null;
  }
}

@freezed
class RiskWarning with _$RiskWarning {
  const factory RiskWarning({
    required String type,
    required String message,
    required String severity,
  }) = _RiskWarning;

  factory RiskWarning.fromJson(Map<String, dynamic> json) => _$RiskWarningFromJson(json);
}