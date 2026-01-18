import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'api_client.g.dart';

/// 动态获取API基础URL
String _getApiBaseUrl() {
  final currentHost = Uri.base.host;
  
  // 如果是localhost，使用localhost:8000
  if (currentHost == 'localhost' || currentHost == '127.0.0.1') {
    return 'http://localhost:8000';
  }
  
  // 如果是局域网IP，使用相同IP的8000端口
  return 'http://$currentHost:8000';
}

@riverpod
Dio apiClient(ApiClientRef ref) {
  final dio = Dio();
  
  // Base configuration - 动态配置支持局域网访问
  dio.options.baseUrl = _getApiBaseUrl();
  dio.options.connectTimeout = const Duration(seconds: 10);
  dio.options.receiveTimeout = const Duration(seconds: 10);
  
  // Request interceptor for authentication
  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) {
        // TODO: Add JWT token from auth state
        // final token = ref.read(authTokenProvider);
        // if (token != null) {
        //   options.headers['Authorization'] = 'Bearer $token';
        // }
        handler.next(options);
      },
      onError: (error, handler) {
        // TODO: Handle authentication errors
        if (error.response?.statusCode == 401) {
          // Redirect to login
        }
        handler.next(error);
      },
    ),
  );
  
  return dio;
}

class ApiEndpoints {
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String assets = '/api/assets';
  static const String portfolioHealth = '/api/portfolio/{user_id}/health';
  static const String recommendations = '/api/recommendations/{user_id}';
  static const String chat = '/ws/chat/{user_id}';
}

class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? error;
  final String? errorCode;

  ApiResponse({
    required this.success,
    this.data,
    this.error,
    this.errorCode,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic) fromJsonT,
  ) {
    return ApiResponse<T>(
      success: json['success'] ?? false,
      data: json['data'] != null ? fromJsonT(json['data']) : null,
      error: json['error'],
      errorCode: json['error_code'],
    );
  }
}