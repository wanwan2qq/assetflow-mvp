// AssetFlow API Client - Generated from OpenAPI specification
// AssetFlow API 客户端 - 从 OpenAPI 规范生成

import 'dart:convert';
import 'package:http/http.dart' as http;

class AssetFlowApiClient {
  final String baseUrl;
  final Map<String, String> defaultHeaders;
  final Duration timeout;

  AssetFlowApiClient({
    required this.baseUrl,
    Map<String, String>? headers,
    this.timeout = const Duration(seconds: 30),
  }) : defaultHeaders = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...?headers,
        };

  // Health Check Endpoints
  Future<Map<String, dynamic>> healthCheck() async {
    final response = await _makeRequest(
      'GET',
      '/api/v1/health/',
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> databaseHealthCheck() async {
    final response = await _makeRequest(
      'GET',
      '/api/v1/health/db',
    );
    return _handleResponse(response);
  }

  // Generic HTTP request method
  Future<http.Response> _makeRequest(
    String method,
    String path, {
    Map<String, dynamic>? body,
    Map<String, String>? headers,
  }) async {
    final uri = Uri.parse('$baseUrl$path');
    final requestHeaders = {...defaultHeaders, ...?headers};

    switch (method.toUpperCase()) {
      case 'GET':
        return await http.get(uri, headers: requestHeaders).timeout(timeout);
      case 'POST':
        return await http.post(
          uri,
          headers: requestHeaders,
          body: body != null ? json.encode(body) : null,
        ).timeout(timeout);
      case 'PUT':
        return await http.put(
          uri,
          headers: requestHeaders,
          body: body != null ? json.encode(body) : null,
        ).timeout(timeout);
      case 'DELETE':
        return await http.delete(uri, headers: requestHeaders).timeout(timeout);
      default:
        throw UnsupportedError('HTTP method $method not supported');
    }
  }

  // Generic response handler
  Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) {
        return {'success': true};
      }
      return json.decode(response.body);
    } else {
      throw ApiException(
        statusCode: response.statusCode,
        message: response.body,
      );
    }
  }
}

// Exception class for API errors
class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException($statusCode): $message';
}

// Standard API Response wrapper
class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? error;
  final String? errorCode;
  final String? message;

  ApiResponse({
    required this.success,
    this.data,
    this.error,
    this.errorCode,
    this.message,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic)? fromJsonT,
  ) {
    return ApiResponse<T>(
      success: json['success'] ?? false,
      data: json['data'] != null && fromJsonT != null
          ? fromJsonT(json['data'])
          : json['data'],
      error: json['error'],
      errorCode: json['error_code'],
      message: json['message'],
    );
  }

  Map<String, dynamic> toJson(Object? Function(T)? toJsonT) {
    return {
      'success': success,
      if (data != null) 'data': toJsonT != null ? toJsonT(data as T) : data,
      if (error != null) 'error': error,
      if (errorCode != null) 'error_code': errorCode,
      if (message != null) 'message': message,
    };
  }
}

// Data Models (based on backend SQLModel definitions)

enum AssetType {
  realEstate('real_estate'),
  cash('cash'),
  investment('investment'),
  insurance('insurance'),
  liability('liability');

  const AssetType(this.value);
  final String value;
}

enum RiskLevel {
  conservative('conservative'),
  moderate('moderate'),
  aggressive('aggressive');

  const RiskLevel(this.value);
  final String value;
}

class User {
  final int? id;
  final String phone;
  final String? deviceId;
  final DateTime createdAt;

  User({
    this.id,
    required this.phone,
    this.deviceId,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      phone: json['phone'],
      deviceId: json['device_id'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'phone': phone,
      if (deviceId != null) 'device_id': deviceId,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

class UserAsset {
  final int? id;
  final int userId;
  final AssetType assetType;
  final String name;
  final double value;
  final bool isConfirmed;
  final Map<String, dynamic>? metadata;
  final DateTime createdAt;
  final DateTime updatedAt;

  UserAsset({
    this.id,
    required this.userId,
    required this.assetType,
    required this.name,
    required this.value,
    this.isConfirmed = false,
    this.metadata,
    required this.createdAt,
    required this.updatedAt,
  });

  factory UserAsset.fromJson(Map<String, dynamic> json) {
    return UserAsset(
      id: json['id'],
      userId: json['user_id'],
      assetType: AssetType.values.firstWhere(
        (e) => e.value == json['asset_type'],
      ),
      name: json['name'],
      value: json['value'].toDouble(),
      isConfirmed: json['is_confirmed'] ?? false,
      metadata: json['metadata'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'user_id': userId,
      'asset_type': assetType.value,
      'name': name,
      'value': value,
      'is_confirmed': isConfirmed,
      if (metadata != null) 'metadata': metadata,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
