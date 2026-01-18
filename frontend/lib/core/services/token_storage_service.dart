import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/user.dart';

class TokenStorageService {
  static const String _tokenKey = 'auth_token';
  static const String _userKey = 'auth_user';
  
  static TokenStorageService? _instance;
  static TokenStorageService get instance {
    _instance ??= TokenStorageService._();
    return _instance!;
  }
  
  TokenStorageService._();
  
  /// 存储Token和用户信息
  Future<void> storeAuthData(String token, User user) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      
      // 存储token
      await prefs.setString(_tokenKey, token);
      
      // 存储用户信息
      final userJson = json.encode(user.toJson());
      await prefs.setString(_userKey, userJson);
      
      print('🔑 Token和用户信息已持久化存储');
      print('   Token前缀: ${token.substring(0, 20)}...');
      print('   用户ID: ${user.id}');
      print('   手机号: ${user.phone}');
    } catch (e) {
      print('❌ 存储认证数据失败: $e');
    }
  }
  
  /// 获取存储的Token
  Future<String?> getToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString(_tokenKey);
      
      if (token != null) {
        print('🔑 从存储中恢复Token: ${token.substring(0, 20)}...');
      } else {
        print('🔑 存储中没有Token');
      }
      
      return token;
    } catch (e) {
      print('❌ 获取Token失败: $e');
      return null;
    }
  }
  
  /// 获取存储的用户信息
  Future<User?> getUser() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userJson = prefs.getString(_userKey);
      
      if (userJson != null) {
        final userMap = json.decode(userJson) as Map<String, dynamic>;
        final user = User.fromJson(userMap);
        
        print('👤 从存储中恢复用户信息:');
        print('   用户ID: ${user.id}');
        print('   手机号: ${user.phone}');
        
        return user;
      } else {
        print('👤 存储中没有用户信息');
        return null;
      }
    } catch (e) {
      print('❌ 获取用户信息失败: $e');
      return null;
    }
  }
  
  /// 清除所有认证数据
  Future<void> clearAuthData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      
      await prefs.remove(_tokenKey);
      await prefs.remove(_userKey);
      
      print('🗑️ 已清除所有持久化认证数据');
    } catch (e) {
      print('❌ 清除认证数据失败: $e');
    }
  }
  
  /// 检查是否有存储的认证数据
  Future<bool> hasAuthData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final hasToken = prefs.containsKey(_tokenKey);
      final hasUser = prefs.containsKey(_userKey);
      
      print('🔍 检查存储的认证数据:');
      print('   有Token: $hasToken');
      print('   有用户信息: $hasUser');
      
      return hasToken && hasUser;
    } catch (e) {
      print('❌ 检查认证数据失败: $e');
      return false;
    }
  }
  
  /// 调试方法：显示所有存储的数据
  Future<void> debugStoredData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      
      print('=== 存储的认证数据调试 ===');
      
      final token = prefs.getString(_tokenKey);
      if (token != null) {
        print('Token: ${token.substring(0, 30)}...');
        print('Token长度: ${token.length}');
      } else {
        print('Token: null');
      }
      
      final userJson = prefs.getString(_userKey);
      if (userJson != null) {
        print('用户JSON: $userJson');
      } else {
        print('用户信息: null');
      }
      
      print('========================');
    } catch (e) {
      print('❌ 调试存储数据失败: $e');
    }
  }
}