import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const factory User({
    required int id,
    required String phone,
    String? deviceId,
    required DateTime createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}

@freezed
class UserProfile with _$UserProfile {
  const factory UserProfile({
    required int id,
    required int userId,
    required String ageRange,
    required String familyStructure,
    required String riskPreference,
    double? monthlyExpense,
  }) = _UserProfile;

  factory UserProfile.fromJson(Map<String, dynamic> json) => _$UserProfileFromJson(json);
}