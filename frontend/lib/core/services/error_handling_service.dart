import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'error_handling_service.g.dart';

/// Error codes that match the backend error handling system
class ErrorCode {
  // Authentication errors
  static const String authInvalidToken = 'AUTH_INVALID_TOKEN';
  static const String authTokenExpired = 'AUTH_TOKEN_EXPIRED';
  static const String authInsufficientPermissions = 'AUTH_INSUFFICIENT_PERMISSIONS';
  static const String authInvalidCredentials = 'AUTH_INVALID_CREDENTIALS';
  
  // Asset management errors
  static const String assetNotFound = 'ASSET_NOT_FOUND';
  static const String assetInvalidType = 'ASSET_INVALID_TYPE';
  static const String assetInvalidValue = 'ASSET_INVALID_VALUE';
  static const String assetCreationFailed = 'ASSET_CREATION_FAILED';
  
  // AI and search errors
  static const String aiServiceUnavailable = 'AI_SERVICE_UNAVAILABLE';
  static const String searchServiceTimeout = 'SEARCH_SERVICE_TIMEOUT';
  static const String searchNoResults = 'SEARCH_NO_RESULTS';
  
  // Database errors
  static const String databaseConnectionError = 'DATABASE_CONNECTION_ERROR';
  static const String databaseConstraintViolation = 'DATABASE_CONSTRAINT_VIOLATION';
  
  // WebSocket errors
  static const String websocketConnectionFailed = 'WEBSOCKET_CONNECTION_FAILED';
  static const String websocketAuthFailed = 'WEBSOCKET_AUTH_FAILED';
  
  // General errors
  static const String validationError = 'VALIDATION_ERROR';
  static const String internalServerError = 'INTERNAL_SERVER_ERROR';
  static const String serviceUnavailable = 'SERVICE_UNAVAILABLE';
  static const String rateLimitExceeded = 'RATE_LIMIT_EXCEEDED';
}

/// Standardized error response from backend
class ApiError {
  final String message;
  final String code;
  final Map<String, dynamic> details;
  final String? requestId;
  final DateTime timestamp;

  ApiError({
    required this.message,
    required this.code,
    this.details = const {},
    this.requestId,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  factory ApiError.fromJson(Map<String, dynamic> json) {
    final error = json['error'] as Map<String, dynamic>? ?? {};
    
    return ApiError(
      message: error['message'] as String? ?? 'Unknown error',
      code: error['code'] as String? ?? 'UNKNOWN_ERROR',
      details: error['details'] as Map<String, dynamic>? ?? {},
      requestId: json['request_id'] as String?,
      timestamp: DateTime.tryParse(json['timestamp'] as String? ?? '') ?? DateTime.now(),
    );
  }

  factory ApiError.fromDioError(DioException error) {
    print('🔍 处理DioException: ${error.type}');
    print('🔍 状态码: ${error.response?.statusCode}');
    
    // 优先根据HTTP状态码判断错误类型，特别是429错误
    if (error.response?.statusCode == 429) {
      print('✅ 检测到429状态码，直接映射到RATE_LIMIT_EXCEEDED');
      return ApiError(
        message: '验证码请求过于频繁，请稍后重试',
        code: ErrorCode.rateLimitExceeded,
        details: {
          'dio_error_type': error.type.toString(),
          'status_code': error.response?.statusCode,
        },
      );
    }
    
    if (error.response?.data is Map<String, dynamic>) {
      return ApiError.fromJson(error.response!.data);
    }
    
    // Fallback for non-API errors
    String code = ErrorCode.internalServerError;
    String message = 'Network error occurred';
    
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        code = ErrorCode.serviceUnavailable;
        message = '连接超时，请检查网络连接';
        break;
      case DioExceptionType.badResponse:
        if (error.response?.statusCode == 401) {
          code = ErrorCode.authInvalidToken;
          message = '登录已过期，请重新登录';
        } else if (error.response?.statusCode == 403) {
          code = ErrorCode.authInsufficientPermissions;
          message = '访问被拒绝';
        } else if (error.response?.statusCode == 404) {
          code = ErrorCode.assetNotFound;
          message = '请求的资源不存在';
        } else if (error.response?.statusCode == 422) {
          code = ErrorCode.validationError;
          message = '输入数据格式错误';
        } else if (error.response?.statusCode == 500) {
          code = ErrorCode.internalServerError;
          message = '服务器内部错误';
        } else if (error.response?.statusCode == 503) {
          code = ErrorCode.serviceUnavailable;
          message = '服务暂时不可用';
        }
        break;
      case DioExceptionType.cancel:
        code = 'REQUEST_CANCELLED';
        message = '请求已取消';
        break;
      case DioExceptionType.unknown:
      default:
        code = ErrorCode.internalServerError;
        message = '网络连接失败，请检查网络设置';
        break;
    }
    
    print('🔍 最终错误码: $code');
    
    return ApiError(
      message: message,
      code: code,
      details: {
        'dio_error_type': error.type.toString(),
        'status_code': error.response?.statusCode,
      },
    );
  }
}

/// Error handling service for the application
@riverpod
class ErrorHandlingService extends _$ErrorHandlingService {
  @override
  void build() {
    // Initialize error handling service
  }

  /// Get user-friendly message for error code
  String getUserFriendlyMessage(String errorCode, {Map<String, dynamic>? context}) {
    const messages = {
      ErrorCode.authInvalidToken: '登录已过期，请重新登录',
      ErrorCode.authInvalidCredentials: '手机号或验证码错误，请检查后重试',
      ErrorCode.assetNotFound: '找不到指定的资产信息',
      ErrorCode.assetInvalidValue: '资产价值必须为正数',
      ErrorCode.databaseConnectionError: '数据服务暂时不可用，请稍后重试',
      ErrorCode.aiServiceUnavailable: 'AI服务暂时不可用，您可以手动输入资产信息',
      ErrorCode.searchServiceTimeout: '房产搜索超时，请手动输入估值或稍后重试',
      ErrorCode.websocketConnectionFailed: '连接中断，正在尝试重新连接...',
      ErrorCode.validationError: '输入信息有误，请检查后重试',
      ErrorCode.rateLimitExceeded: '操作过于频繁，请稍后重试',
      ErrorCode.serviceUnavailable: '服务暂时不可用，请稍后重试',
      ErrorCode.internalServerError: '系统暂时不可用，请稍后重试',
    };

    return messages[errorCode] ?? '系统暂时不可用，请稍后重试';
  }

  /// Get recovery suggestions for error code
  List<String> getRecoverySuggestions(String errorCode) {
    const suggestions = {
      ErrorCode.authInvalidToken: [
        '点击重新登录',
        '检查网络连接',
        '清除应用缓存后重试'
      ],
      ErrorCode.rateLimitExceeded: [
        '请等待1-2分钟后重试',
        '避免频繁点击发送按钮',
        '如急需验证码可联系客服'
      ],
      ErrorCode.assetInvalidValue: [
        '确保输入的金额为正数',
        '检查数字格式是否正确',
        '如有疑问可联系客服'
      ],
      ErrorCode.searchServiceTimeout: [
        '手动输入房产估值',
        '稍后重试搜索功能',
        '联系客服获取帮助'
      ],
      ErrorCode.aiServiceUnavailable: [
        '使用资产管理页面手动添加',
        '稍后重试对话功能',
        '查看帮助文档'
      ],
      ErrorCode.databaseConnectionError: [
        '检查网络连接',
        '稍后重试',
        '联系技术支持'
      ],
      ErrorCode.websocketConnectionFailed: [
        '检查网络连接',
        '尝试刷新页面',
        '切换网络环境'
      ],
    };

    return suggestions[errorCode] ?? ['稍后重试', '联系客服获取帮助'];
  }

  /// Check if error should trigger automatic retry
  bool shouldRetryAutomatically(String errorCode) {
    const autoRetryErrors = {
      ErrorCode.databaseConnectionError,
      ErrorCode.searchServiceTimeout,
      ErrorCode.websocketConnectionFailed,
      ErrorCode.serviceUnavailable,
    };

    return autoRetryErrors.contains(errorCode);
  }

  /// Get retry delay with exponential backoff
  Duration getRetryDelay(String errorCode, int attempt) {
    const baseDelays = {
      ErrorCode.databaseConnectionError: 2,
      ErrorCode.searchServiceTimeout: 5,
      ErrorCode.websocketConnectionFailed: 1,
      ErrorCode.serviceUnavailable: 3,
    };

    final baseDelay = baseDelays[errorCode] ?? 5;
    final delaySeconds = (baseDelay * (1 << attempt)).clamp(1, 60);
    return Duration(seconds: delaySeconds);
  }

  /// Handle API error and show appropriate user feedback
  void handleApiError(
    BuildContext context,
    ApiError error, {
    VoidCallback? onRetry,
    VoidCallback? onDismiss,
  }) {
    final message = getUserFriendlyMessage(error.code);
    final suggestions = getRecoverySuggestions(error.code);
    final shouldRetry = shouldRetryAutomatically(error.code);

    // 调试信息
    print('🔍 处理API错误: ${error.code}');
    print('🔍 错误消息: ${error.message}');

    // 特殊处理频率限制错误 - 只使用SnackBar，不显示弹窗
    if (error.code == ErrorCode.rateLimitExceeded) {
      print('✅ 检测到429错误，显示SnackBar');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              Icon(Icons.warning, color: Colors.white, size: 20),
              const SizedBox(width: 8),
              Expanded(child: Text('验证码请求过于频繁，请稍后重试')),
            ],
          ),
          backgroundColor: Colors.orange,
          duration: const Duration(seconds: 4),
          behavior: SnackBarBehavior.floating,
          margin: const EdgeInsets.all(16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      );
      return;
    }

    print('❌ 非429错误，显示弹窗或其他处理');

    if (shouldRetry && onRetry != null) {
      // Show retry snackbar for auto-retryable errors
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          action: SnackBarAction(
            label: '重试',
            onPressed: onRetry,
          ),
          duration: const Duration(seconds: 5),
        ),
      );
    } else {
      // Show error dialog for non-retryable errors
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Row(
            children: [
              Icon(
                Icons.error_outline,
                color: Colors.red,
              ),
              const SizedBox(width: 8),
              const Text('操作失败'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(message),
              if (suggestions.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text('建议解决方案：', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                ...suggestions.map((suggestion) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('• '),
                      Expanded(child: Text(suggestion)),
                    ],
                  ),
                )),
              ],
            ],
          ),
          actions: [
            if (onRetry != null)
              TextButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  onRetry();
                },
                child: const Text('重试'),
              ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                onDismiss?.call();
              },
              child: const Text('确定'),
            ),
          ],
        ),
      );
    }
  }

  /// Handle DioException and convert to ApiError
  void handleDioError(
    BuildContext context,
    DioException error, {
    VoidCallback? onRetry,
    VoidCallback? onDismiss,
  }) {
    final apiError = ApiError.fromDioError(error);
    handleApiError(context, apiError, onRetry: onRetry, onDismiss: onDismiss);
  }

  /// Show success message
  void showSuccess(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  /// Show warning message
  void showWarning(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.orange,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  /// Show info message
  void showInfo(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.blue,
        duration: const Duration(seconds: 3),
      ),
    );
  }
}

/// Extension to add error handling to AsyncValue
extension AsyncValueErrorHandling<T> on AsyncValue<T> {
  /// Handle error state with user-friendly messages
  Widget when({
    required Widget Function(T data) data,
    required Widget Function(Object error, StackTrace stackTrace) error,
    Widget Function()? loading,
  }) {
    return when(
      data: data,
      error: error,
      loading: loading ?? () => const Center(child: CircularProgressIndicator()),
    );
  }

  /// Handle error with ErrorHandlingService
  void handleError(
    BuildContext context,
    ErrorHandlingService errorService, {
    VoidCallback? onRetry,
  }) {
    whenOrNull(
      error: (error, stackTrace) {
        if (error is DioException) {
          errorService.handleDioError(context, error, onRetry: onRetry);
        } else {
          final apiError = ApiError(
            message: error.toString(),
            code: ErrorCode.internalServerError,
          );
          errorService.handleApiError(context, apiError, onRetry: onRetry);
        }
      },
    );
  }
}

/// Mixin for widgets that need error handling
mixin ErrorHandlingMixin<T extends StatefulWidget> on State<T> {
  late final ErrorHandlingService _errorService;

  @override
  void initState() {
    super.initState();
    _errorService = ErrorHandlingService();
  }

  /// Handle API error with user feedback
  void handleApiError(ApiError error, {VoidCallback? onRetry}) {
    _errorService.handleApiError(context, error, onRetry: onRetry);
  }

  /// Handle Dio error with user feedback
  void handleDioError(DioException error, {VoidCallback? onRetry}) {
    _errorService.handleDioError(context, error, onRetry: onRetry);
  }

  /// Show success message
  void showSuccess(String message) {
    _errorService.showSuccess(context, message);
  }

  /// Show warning message
  void showWarning(String message) {
    _errorService.showWarning(context, message);
  }

  /// Show info message
  void showInfo(String message) {
    _errorService.showInfo(context, message);
  }
}