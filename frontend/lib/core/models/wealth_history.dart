import 'package:freezed_annotation/freezed_annotation.dart';

part 'wealth_history.freezed.dart';
part 'wealth_history.g.dart';

@freezed
class WealthHistory with _$WealthHistory {
  const factory WealthHistory({
    required DateTime date,
    required double netWorth,
    required double totalAssets,
    required double totalLiabilities,
  }) = _WealthHistory;

  factory WealthHistory.fromJson(Map<String, dynamic> json) => _$WealthHistoryFromJson(json);
}
