#!/usr/bin/env python3
"""
AssetFlow System Health Check
Comprehensive system integration verification
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthCheckResult:
    def __init__(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        self.name = name
        self.status = status  # "PASS", "FAIL", "WARN"
        self.message = message
        self.details = details or {}
        self.timestamp = time.time()

class SystemHealthChecker:
    def __init__(self):
        self.results: List[HealthCheckResult] = []
        self.backend_url = "http://localhost:8000"
        self.db_url = "postgresql+asyncpg://assetflow:assetflow123@localhost:5432/assetflow"
        self.redis_url = "redis://localhost:6379"
    
    def add_result(self, result: HealthCheckResult):
        self.results.append(result)
        status_color = {
            "PASS": "\033[92m",  # Green
            "FAIL": "\033[91m",  # Red
            "WARN": "\033[93m",  # Yellow
        }
        reset_color = "\033[0m"
        
        color = status_color.get(result.status, "")
        print(f"{color}[{result.status}]{reset_color} {result.name}: {result.message}")
    
    async def check_database_connection(self) -> HealthCheckResult:
        """Check PostgreSQL database connectivity and basic operations"""
        try:
            engine = create_async_engine(self.db_url)
            
            async with engine.begin() as conn:
                # Test basic query
                result = await conn.execute("SELECT 1 as test")
                row = result.fetchone()
                
                if row and row[0] == 1:
                    # Check if tables exist
                    table_check = await conn.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name IN ('user', 'userasset', 'userprofile')
                    """)
                    table_count = table_check.fetchone()[0]
                    
                    if table_count >= 3:
                        return HealthCheckResult(
                            "Database Connection",
                            "PASS",
                            f"Connected successfully, {table_count} core tables found",
                            {"tables_found": table_count}
                        )
                    else:
                        return HealthCheckResult(
                            "Database Connection",
                            "WARN",
                            f"Connected but only {table_count} core tables found",
                            {"tables_found": table_count}
                        )
                else:
                    return HealthCheckResult(
                        "Database Connection",
                        "FAIL",
                        "Query test failed"
                    )
            
        except Exception as e:
            return HealthCheckResult(
                "Database Connection",
                "FAIL",
                f"Connection failed: {str(e)}"
            )
    
    async def check_redis_connection(self) -> HealthCheckResult:
        """Check Redis connectivity and basic operations"""
        try:
            redis_client = redis.from_url(self.redis_url)
            
            # Test basic operations
            await redis_client.set("health_check", "test_value", ex=10)
            value = await redis_client.get("health_check")
            
            if value and value.decode() == "test_value":
                # Clean up
                await redis_client.delete("health_check")
                await redis_client.close()
                
                return HealthCheckResult(
                    "Redis Connection",
                    "PASS",
                    "Connected successfully, read/write operations working"
                )
            else:
                await redis_client.close()
                return HealthCheckResult(
                    "Redis Connection",
                    "FAIL",
                    "Read/write operations failed"
                )
                
        except Exception as e:
            return HealthCheckResult(
                "Redis Connection",
                "FAIL",
                f"Connection failed: {str(e)}"
            )
    
    async def check_backend_api(self) -> HealthCheckResult:
        """Check backend API endpoints and functionality"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check health endpoint
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status != 200:
                        return HealthCheckResult(
                            "Backend API",
                            "FAIL",
                            f"Health endpoint returned {response.status}"
                        )
                
                # Check API documentation
                async with session.get(f"{self.backend_url}/api/v1/openapi.json") as response:
                    if response.status != 200:
                        return HealthCheckResult(
                            "Backend API",
                            "WARN",
                            "OpenAPI documentation not accessible"
                        )
                    
                    openapi_spec = await response.json()
                    endpoint_count = len(openapi_spec.get("paths", {}))
                
                # Check main API endpoints exist
                required_endpoints = [
                    "/api/v1/auth/login/phone",
                    "/api/v1/auth/login/device",
                    "/api/v1/assets/{user_id}",
                    "/api/v1/profiles/{user_id}",
                    "/api/v1/chat/ws/chat/{user_id}",
                ]
                
                missing_endpoints = []
                for endpoint in required_endpoints:
                    if endpoint not in openapi_spec.get("paths", {}):
                        missing_endpoints.append(endpoint)
                
                if missing_endpoints:
                    return HealthCheckResult(
                        "Backend API",
                        "WARN",
                        f"Some endpoints missing: {missing_endpoints}",
                        {"missing_endpoints": missing_endpoints, "total_endpoints": endpoint_count}
                    )
                else:
                    return HealthCheckResult(
                        "Backend API",
                        "PASS",
                        f"All core endpoints available ({endpoint_count} total)",
                        {"total_endpoints": endpoint_count}
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                "Backend API",
                "FAIL",
                f"API check failed: {str(e)}"
            )
    
    async def check_websocket_endpoint(self) -> HealthCheckResult:
        """Check WebSocket endpoint availability"""
        try:
            import websockets
            
            # Try to connect to WebSocket (will fail auth but should connect)
            uri = f"ws://localhost:8000/api/v1/chat/ws/chat/1?token=invalid"
            
            try:
                async with websockets.connect(uri, timeout=5) as websocket:
                    # Should not reach here due to auth failure
                    pass
            except websockets.exceptions.ConnectionClosedError as e:
                # Expected - auth failure should close connection
                if e.code == 1008:  # Unauthorized
                    return HealthCheckResult(
                        "WebSocket Endpoint",
                        "PASS",
                        "WebSocket endpoint accessible (auth working)"
                    )
                else:
                    return HealthCheckResult(
                        "WebSocket Endpoint",
                        "WARN",
                        f"WebSocket closed with unexpected code: {e.code}"
                    )
            except Exception as e:
                return HealthCheckResult(
                    "WebSocket Endpoint",
                    "FAIL",
                    f"WebSocket connection failed: {str(e)}"
                )
                
        except ImportError:
            return HealthCheckResult(
                "WebSocket Endpoint",
                "WARN",
                "websockets library not available for testing"
            )
        except Exception as e:
            return HealthCheckResult(
                "WebSocket Endpoint",
                "FAIL",
                f"WebSocket check failed: {str(e)}"
            )
    
    async def check_ai_services(self) -> HealthCheckResult:
        """Check AI services integration"""
        try:
            # Check if environment variables are set
            import os
            
            required_env_vars = [
                "OPENAI_API_KEY",
                "TAVILY_API_KEY",
            ]
            
            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return HealthCheckResult(
                    "AI Services",
                    "WARN",
                    f"Missing environment variables: {missing_vars}",
                    {"missing_vars": missing_vars}
                )
            
            # Test mock mode
            use_mock = os.getenv("USE_MOCK_SEARCH", "false").lower() == "true"
            
            if use_mock:
                return HealthCheckResult(
                    "AI Services",
                    "PASS",
                    "Running in mock mode (development)",
                    {"mode": "mock"}
                )
            else:
                return HealthCheckResult(
                    "AI Services",
                    "PASS",
                    "Environment variables configured for production",
                    {"mode": "production"}
                )
                
        except Exception as e:
            return HealthCheckResult(
                "AI Services",
                "FAIL",
                f"AI services check failed: {str(e)}"
            )
    
    async def check_data_integrity(self) -> HealthCheckResult:
        """Check data integrity and relationships"""
        try:
            engine = create_async_engine(self.db_url)
            
            async with engine.begin() as conn:
                # Check for orphaned records
                orphaned_assets = await conn.execute("""
                    SELECT COUNT(*) FROM userasset ua 
                    LEFT JOIN "user" u ON ua.user_id = u.id 
                    WHERE u.id IS NULL
                """)
                orphaned_count = orphaned_assets.fetchone()[0]
                
                # Check for invalid asset types
                invalid_assets = await conn.execute("""
                    SELECT COUNT(*) FROM userasset 
                    WHERE asset_type NOT IN ('real_estate', 'cash', 'investment', 'insurance', 'liability')
                """)
                invalid_count = invalid_assets.fetchone()[0]
                
                # Check for negative values where they shouldn't be
                negative_values = await conn.execute("""
                    SELECT COUNT(*) FROM userasset 
                    WHERE value < 0 AND asset_type != 'liability'
                """)
                negative_count = negative_values.fetchone()[0]
                
                issues = []
                if orphaned_count > 0:
                    issues.append(f"{orphaned_count} orphaned assets")
                if invalid_count > 0:
                    issues.append(f"{invalid_count} invalid asset types")
                if negative_count > 0:
                    issues.append(f"{negative_count} negative non-liability values")
                
                if issues:
                    return HealthCheckResult(
                        "Data Integrity",
                        "WARN",
                        f"Data issues found: {', '.join(issues)}",
                        {"issues": issues}
                    )
                else:
                    return HealthCheckResult(
                        "Data Integrity",
                        "PASS",
                        "No data integrity issues found"
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                "Data Integrity",
                "FAIL",
                f"Data integrity check failed: {str(e)}"
            )
    
    async def check_system_performance(self) -> HealthCheckResult:
        """Check system performance metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test API response times
                start_time = time.time()
                async with session.get(f"{self.backend_url}/health") as response:
                    response_time = time.time() - start_time
                    
                    if response_time > 2.0:
                        return HealthCheckResult(
                            "System Performance",
                            "WARN",
                            f"Slow API response: {response_time:.2f}s",
                            {"response_time": response_time}
                        )
                    elif response_time > 1.0:
                        return HealthCheckResult(
                            "System Performance",
                            "PASS",
                            f"Acceptable API response: {response_time:.2f}s",
                            {"response_time": response_time}
                        )
                    else:
                        return HealthCheckResult(
                            "System Performance",
                            "PASS",
                            f"Fast API response: {response_time:.2f}s",
                            {"response_time": response_time}
                        )
                        
        except Exception as e:
            return HealthCheckResult(
                "System Performance",
                "FAIL",
                f"Performance check failed: {str(e)}"
            )
    
    async def run_all_checks(self) -> Dict:
        """Run all health checks and return summary"""
        print("🏥 AssetFlow System Health Check")
        print("=" * 40)
        
        checks = [
            self.check_database_connection(),
            self.check_redis_connection(),
            self.check_backend_api(),
            self.check_websocket_endpoint(),
            self.check_ai_services(),
            self.check_data_integrity(),
            self.check_system_performance(),
        ]
        
        # Run all checks concurrently
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.add_result(HealthCheckResult(
                    "Unknown Check",
                    "FAIL",
                    f"Check failed with exception: {str(result)}"
                ))
            else:
                self.add_result(result)
        
        # Generate summary
        total_checks = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        warnings = len([r for r in self.results if r.status == "WARN"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        
        print("\n" + "=" * 40)
        print(f"📊 Health Check Summary:")
        print(f"   Total Checks: {total_checks}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ⚠️  Warnings: {warnings}")
        print(f"   ❌ Failed: {failed}")
        
        overall_status = "HEALTHY" if failed == 0 else "UNHEALTHY"
        if warnings > 0 and failed == 0:
            overall_status = "DEGRADED"
        
        print(f"   🏥 Overall Status: {overall_status}")
        
        return {
            "overall_status": overall_status,
            "total_checks": total_checks,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }

async def main():
    """Main entry point"""
    checker = SystemHealthChecker()
    
    try:
        summary = await checker.run_all_checks()
        
        # Save detailed report
        with open("system_health_report.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: system_health_report.json")
        
        # Exit with appropriate code
        if summary["overall_status"] == "UNHEALTHY":
            sys.exit(1)
        elif summary["overall_status"] == "DEGRADED":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⏹️  Health check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Health check failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())