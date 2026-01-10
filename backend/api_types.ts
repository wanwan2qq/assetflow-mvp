// AssetFlow API Types - Generated from OpenAPI specification
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

// API Endpoints
// Health Check
// GET /api/v1/health/
// Database Health Check
// GET /api/v1/health/db
// Root
// GET /
// Health Check
// GET /health
