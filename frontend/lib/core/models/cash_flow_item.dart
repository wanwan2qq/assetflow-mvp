import 'package:freezed_annotation/freezed_annotation.dart';

part 'cash_flow_item.freezed.dart';
part 'cash_flow_item.g.dart';

enum CashFlowType {
  @JsonValue('income')
  income,
  @JsonValue('expense')
  expense,
}

enum CashFlowFrequency {
  @JsonValue('monthly')
  monthly,
  @JsonValue('yearly')
  yearly,
  @JsonValue('one_time')
  oneTime,
}

@freezed
class CashFlowItem with _$CashFlowItem {
  const factory CashFlowItem({
    required String id,
    required String name,
    required double amount,
    required CashFlowType type,
    required CashFlowFrequency frequency,
    int? relatedAssetId,
    DateTime? startDate,
    DateTime? endDate,
  }) = _CashFlowItem;

  factory CashFlowItem.fromJson(Map<String, dynamic> json) => _$CashFlowItemFromJson(json);
}
