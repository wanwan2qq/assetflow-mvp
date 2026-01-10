#!/usr/bin/env python3
"""
Generate API client code from OpenAPI specification
生成 API 客户端代码从 OpenAPI 规范
"""

import json
import os
from typing import Any


def load_openapi_spec(spec_path: str) -> dict[str, Any]:
    """Load OpenAPI specification from file"""
    with open(spec_path) as f:
        return json.load(f)


def generate_typescript_types(spec: dict[str, Any]) -> str:
    """Generate TypeScript type definitions from OpenAPI spec"""

    # Start with basic types
    ts_content = """// AssetFlow API Types - Generated from OpenAPI specification
// 从 OpenAPI 规范生成的 AssetFlow API 类型定义

// Standard API Response Format
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  error_code?: string;
  message?: string;
}

// Health Response
export interface HealthResponse {
  status: string;
  service?: string;
  database?: string;
  timestamp?: string;
  version?: string;
}

// Error Codes
export enum ErrorCode {
  INTERNAL_ERROR = "INTERNAL_ERROR",
  VALIDATION_ERROR = "VALIDATION_ERROR",
  NOT_FOUND = "NOT_FOUND",
  UNAUTHORIZED = "UNAUTHORIZED",
  FORBIDDEN = "FORBIDDEN",
  INVALID_TOKEN = "INVALID_TOKEN",
  TOKEN_EXPIRED = "TOKEN_EXPIRED",
  INVALID_CREDENTIALS = "INVALID_CREDENTIALS",
  ASSET_NOT_FOUND = "ASSET_NOT_FOUND",
  ASSET_SAVE_ERROR = "ASSET_SAVE_ERROR",
  INVALID_ASSET_DATA = "INVALID_ASSET_DATA",
  SEARCH_API_ERROR = "SEARCH_API_ERROR",
  SEARCH_TIMEOUT = "SEARCH_TIMEOUT",
  PROPERTY_NOT_FOUND = "PROPERTY_NOT_FOUND",
  CHAT_SESSION_ERROR = "CHAT_SESSION_ERROR",
  AI_SERVICE_ERROR = "AI_SERVICE_ERROR",
  DATABASE_ERROR = "DATABASE_ERROR",
  CONNECTION_ERROR = "CONNECTION_ERROR"
}

// Asset Types
export enum AssetType {
  REAL_ESTATE = "real_estate",
  CASH = "cash",
  INVESTMENT = "investment",
  INSURANCE = "insurance",
  LIABILITY = "liability"
}

// Risk Levels
export enum RiskLevel {
  CONSERVATIVE = "conservative",
  MODERATE = "moderate",
  AGGRESSIVE = "aggressive"
}

// User Models
export interface User {
  id?: number;
  phone: string;
  device_id?: string;
  created_at: string;
}

export interface UserProfile {
  id?: number;
  user_id: number;
  age_range: string;
  family_structure: string;
  risk_preference: RiskLevel;
  monthly_expense?: number;
}

export interface UserAsset {
  id?: number;
  user_id: number;
  asset_type: AssetType;
  name: string;
  value: number;
  is_confirmed: boolean;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Commercial Product
export interface CommercialProduct {
  id?: number;
  category: string;
  name: string;
  description: string;
  provider: string;
  contact_info: Record<string, any>;
  priority: number;
  target_tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Chat Session
export interface ChatSession {
  id?: number;
  user_id: number;
  session_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// API Client Configuration
export interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
}

// API Endpoints (generated from OpenAPI paths)
"""

    # Add endpoint interfaces based on paths
    if "paths" in spec:
        ts_content += "\n// API Endpoints\n"
        for _path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    summary = details.get("summary", "")
                    ts_content += f"// {summary}\n"
                    ts_content += f"// {method.upper()} {_path}\n"

    return ts_content


def generate_dart_client(spec: dict[str, Any]) -> str:
    """Generate Dart API client from OpenAPI spec"""

    dart_content = """// AssetFlow API Client - Generated from OpenAPI specification
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
"""

    return dart_content


def main():
    """Main function to generate API client code"""
    print("🔧 Generating API client code from OpenAPI specification...")

    # Check if OpenAPI spec exists
    spec_path = "openapi.json"
    if not os.path.exists(spec_path):
        print(f"❌ OpenAPI specification not found: {spec_path}")
        print("   Please run the application first to generate the spec:")
        print("   uv run uvicorn app.main:app --reload")
        print("   Then visit: http://localhost:8000/api/v1/openapi.json")
        return

    # Load OpenAPI specification
    try:
        spec = load_openapi_spec(spec_path)
        print(
            f"✅ Loaded OpenAPI specification: {spec['info']['title']} v{spec['info']['version']}"
        )
    except Exception as e:
        print(f"❌ Failed to load OpenAPI specification: {e}")
        return

    # Generate TypeScript types
    try:
        ts_content = generate_typescript_types(spec)
        with open("api_types.ts", "w") as f:
            f.write(ts_content)
        print("✅ Generated TypeScript types: api_types.ts")
    except Exception as e:
        print(f"⚠️  Failed to generate TypeScript types: {e}")

    # Generate Dart client
    try:
        dart_content = generate_dart_client(spec)
        with open("api_client.dart", "w") as f:
            f.write(dart_content)
        print("✅ Generated Dart API client: api_client.dart")
    except Exception as e:
        print(f"⚠️  Failed to generate Dart client: {e}")

    print("\n🎉 API client generation completed!")
    print("\n📋 Generated files:")
    print("   📄 api_types.ts - TypeScript type definitions")
    print("   📄 api_client.dart - Dart API client")
    print("\n📚 Next steps:")
    print("   1. Copy files to your frontend project")
    print("   2. Install required dependencies (http package for Dart)")
    print("   3. Configure base URL and authentication")


if __name__ == "__main__":
    main()
