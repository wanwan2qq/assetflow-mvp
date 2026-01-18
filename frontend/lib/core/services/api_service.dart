import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../providers/auth_provider.dart';

part 'api_service.g.dart';

@riverpod
Dio dio(DioRef ref) {
  final dio = Dio();
  
  // 动态配置基础URL - 支持局域网访问
  String baseUrl = _getApiBaseUrl();
  dio.options.baseUrl = baseUrl;
  
  // 添加拦截器
  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) {
        // 添加认证token（同步方式，从内存获取）
        final token = getCurrentToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        // 处理认证错误
        if (error.response?.statusCode == 401) {
          // Token过期，清除认证状态
          ref.read(authStateProvider.notifier).logout();
        }
        handler.next(error);
      },
    ),
  );
  
  return dio;
}

/// 动态获取API基础URL
String _getApiBaseUrl() {
  // 获取当前页面的host
  final currentHost = Uri.base.host;
  
  // 如果是localhost，使用localhost:8000
  if (currentHost == 'localhost' || currentHost == '127.0.0.1') {
    return 'http://localhost:8000';
  }
  
  // 如果是局域网IP，使用相同IP的8000端口
  return 'http://$currentHost:8000';
}

// 简化的API服务类
class ApiService {
  final Dio _dio;
  
  ApiService(this._dio);
  
  // 认证相关API
  Future<Response> sendSms(String phone) {
    return _dio.post('/api/v1/auth/send-sms', data: {'phone': phone});
  }
  
  Future<Response> loginWithPhone(String phone, String verificationCode) {
    return _dio.post('/api/v1/auth/login/phone', data: {
      'phone': phone,
      'verification_code': verificationCode,
    });
  }
  
  Future<Response> loginWithDevice(String deviceId) {
    return _dio.post('/api/v1/auth/login/device', data: {
      'device_id': deviceId,
    });
  }
  
  Future<Response> bindPhone(String phone, String verificationCode) {
    return _dio.post('/api/v1/auth/bind-phone', data: {
      'phone': phone,
      'verification_code': verificationCode,
    });
  }
  
  // 资产相关API
  Future<Response> getAssets(int userId) {
    return _dio.get('/api/v1/assets/$userId');
  }
  
  Future<Response> createAsset(int userId, Map<String, dynamic> assetData) {
    return _dio.post('/api/v1/assets/$userId', data: assetData);
  }
  
  Future<Response> updateAsset(int userId, int assetId, Map<String, dynamic> assetData) {
    return _dio.put('/api/v1/assets/$userId/$assetId', data: assetData);
  }
  
  Future<Response> deleteAsset(int userId, int assetId) {
    return _dio.delete('/api/v1/assets/$userId/$assetId');
  }
  
  Future<Response> getPortfolioHealth(int userId) {
    return _dio.get('/api/v1/assets/$userId/portfolio/health');
  }
  
  // 聊天相关API
  Future<Response> getChatHistory({int limit = 50}) {
    return _dio.get('/api/v1/chat/chat/history', queryParameters: {'limit': limit});
  }
}

@riverpod
ApiService apiService(ApiServiceRef ref) {
  final dio = ref.watch(dioProvider);
  return ApiService(dio);
}