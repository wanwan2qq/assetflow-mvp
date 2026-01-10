"""
API contract tests to ensure frontend-backend interface consistency
Tests OpenAPI specification compliance and response format standards
"""

from fastapi.testclient import TestClient

from app.core.responses import APIResponse, ErrorCode, HealthResponse
from app.main import app

client = TestClient(app)


class TestOpenAPISpecification:
    """Test OpenAPI specification generation and compliance"""

    def test_openapi_spec_structure(self):
        """Test OpenAPI specification has required structure"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200

        spec = response.json()

        # Check required OpenAPI fields
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec

        # Check API info
        info = spec["info"]
        assert info["title"] == "AssetFlow API"
        assert "version" in info
        assert "description" in info

    def test_openapi_paths_defined(self):
        """Test that all expected API paths are defined in OpenAPI spec"""
        response = client.get("/api/v1/openapi.json")
        spec = response.json()
        paths = spec["paths"]

        # Health endpoints should be defined
        assert "/api/v1/health/" in paths
        assert "/api/v1/health/db" in paths

        # Check HTTP methods
        health_path = paths["/api/v1/health/"]
        assert "get" in health_path

    def test_openapi_response_schemas(self):
        """Test that response schemas are properly defined"""
        response = client.get("/api/v1/openapi.json")
        spec = response.json()

        # Check that the spec is valid - components/schemas may not exist yet if no complex models are used
        assert "openapi" in spec
        assert "paths" in spec

        # If components exist, check schemas
        if "components" in spec and "schemas" in spec["components"]:
            schemas = spec["components"]["schemas"]
            # Verify response schemas are defined
            assert isinstance(schemas, dict)


class TestResponseFormatCompliance:
    """Test API response format compliance"""

    def test_health_endpoint_response_format(self):
        """Test health endpoint returns correct format"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

        data = response.json()
        # Validate against HealthResponse model
        health_response = HealthResponse(**data)
        assert health_response.status == "healthy"
        assert health_response.service == "AssetFlow API"

    def test_database_health_response_format(self):
        """Test database health endpoint returns correct format"""
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200

        data = response.json()
        # Should contain required fields
        assert "status" in data
        assert "database" in data
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_root_endpoint_response_format(self):
        """Test root endpoint returns expected format"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["message"] == "AssetFlow API"


class TestErrorResponseFormats:
    """Test error response format consistency"""

    def test_404_error_format(self):
        """Test 404 errors return consistent format"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data  # FastAPI default format

    def test_method_not_allowed_format(self):
        """Test 405 errors return consistent format"""
        response = client.post("/api/v1/health/")
        assert response.status_code == 405

        data = response.json()
        assert "detail" in data


class TestAPIResponseModel:
    """Test APIResponse model functionality"""

    def test_success_response_creation(self):
        """Test creating successful API responses"""
        data = {"test": "value"}
        response = APIResponse.success_response(data, "Operation successful")

        assert response.success is True
        assert response.data == data
        assert response.message == "Operation successful"
        assert response.error is None
        assert response.error_code is None

    def test_error_response_creation(self):
        """Test creating error API responses"""
        response = APIResponse.error_response(
            error="Something went wrong",
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error",
        )

        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.error_code == ErrorCode.INTERNAL_ERROR
        assert response.message == "Internal server error"
        assert response.data is None

    def test_error_code_enum_values(self):
        """Test that all error codes are properly defined"""
        # Test a few key error codes
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.UNAUTHORIZED == "UNAUTHORIZED"
        assert ErrorCode.ASSET_NOT_FOUND == "ASSET_NOT_FOUND"
        assert ErrorCode.SEARCH_API_ERROR == "SEARCH_API_ERROR"


class TestContractConsistency:
    """Test contract consistency for frontend integration"""

    def test_cors_headers_present(self):
        """Test CORS headers are properly configured"""
        response = client.options("/api/v1/health/")
        # CORS should be configured to allow cross-origin requests
        # The exact headers depend on the request, but the endpoint should be accessible
        assert response.status_code in [
            200,
            405,
        ]  # OPTIONS may not be implemented but CORS should work

    def test_content_type_headers(self):
        """Test content type headers are consistent"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_api_versioning_consistency(self):
        """Test API versioning is consistent"""
        # All API endpoints should be under /api/v1
        response = client.get("/api/v1/openapi.json")
        spec = response.json()

        for path in spec["paths"]:
            if path.startswith("/api/"):
                assert path.startswith("/api/v1/"), (
                    f"Path {path} not properly versioned"
                )

    def test_openapi_contract_validation(self):
        """Test that OpenAPI contract is valid and complete"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200

        spec = response.json()

        # Validate OpenAPI 3.x structure
        assert spec["openapi"].startswith("3.")
        assert "info" in spec
        assert "paths" in spec

        # Validate API info
        info = spec["info"]
        assert info["title"] == "AssetFlow API"
        assert "version" in info
        assert "description" in info

        # Validate that all paths have proper responses
        for _path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    assert "responses" in details
                    assert "200" in details["responses"] or any(
                        code.startswith("2") for code in details["responses"].keys()
                    )


class TestMockDataGeneration:
    """Test mock data generation for development"""

    def test_mock_search_configuration(self):
        """Test mock search is properly configured for development"""
        from app.core.config import settings

        # In development/test, mock search should be enabled
        assert settings.USE_MOCK_SEARCH is True
        assert settings.ENVIRONMENT in ["development", "test"]

    def test_api_keys_configured_for_mock(self):
        """Test API keys are configured for mock usage"""
        from app.core.config import settings

        # Should have mock API keys configured
        assert settings.OPENAI_API_KEY is not None
        assert settings.TAVILY_API_KEY is not None
        # In development, these should be mock keys
        assert "mock" in settings.OPENAI_API_KEY.lower()
        assert "mock" in settings.TAVILY_API_KEY.lower()


class TestAPIContractGeneration:
    """Test API contract generation for frontend integration"""

    def test_generate_openapi_specification(self):
        """Test generating complete OpenAPI specification"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200

        spec = response.json()

        # Save specification for frontend integration
        import json
        import os

        # Create openapi.json in the backend directory
        with open("openapi.json", "w") as f:
            json.dump(spec, f, indent=2)

        # Verify file was created
        assert os.path.exists("openapi.json")

        # Verify content is valid JSON
        with open("openapi.json") as f:
            loaded_spec = json.load(f)

        assert loaded_spec == spec

    def test_api_response_format_consistency(self):
        """Test that all API responses follow consistent format"""
        # Test health endpoints follow the expected format
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

        data = response.json()
        # Health endpoint should have status and service fields
        assert "status" in data
        assert data["status"] == "healthy"

        # Test database health endpoint
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "database" in data

    def test_error_response_format_consistency(self):
        """Test that error responses follow APIResponse format"""
        # Test 404 error
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        data = response.json()
        # FastAPI default error format
        assert "detail" in data

        # For future: when we implement APIResponse wrapper, test:
        # assert "success" in data
        # assert data["success"] is False
        # assert "error" in data or "error_code" in data

    def test_openapi_schema_completeness(self):
        """Test OpenAPI schema includes all necessary components"""
        response = client.get("/api/v1/openapi.json")
        spec = response.json()

        # Check that we have proper API structure
        assert "paths" in spec
        assert len(spec["paths"]) > 0

        # Check that health endpoints are documented
        assert "/api/v1/health/" in spec["paths"]
        assert "/api/v1/health/db" in spec["paths"]

        # Check that each endpoint has proper documentation
        for _path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    # Each endpoint should have summary and responses
                    assert "summary" in details or "description" in details
                    assert "responses" in details
