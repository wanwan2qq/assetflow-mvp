"""
Infrastructure tests for AssetFlow backend
Tests database connectivity, basic API responses, and development environment configuration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db_session
from app.main import app

client = TestClient(app)


class TestBasicAPI:
    """Test basic API functionality"""

    def test_root_endpoint(self):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AssetFlow API"
        assert data["version"] == "0.1.0"
        assert "docs" in data

    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_v1_health_endpoint(self):
        """Test API v1 health endpoint"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AssetFlow API"


class TestDatabaseConnectivity:
    """Test database connectivity and configuration"""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection works"""
        async for session in get_db_session():
            # Execute a simple query to test connectivity
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row is not None
            assert row.test == 1
            break

    def test_database_health_endpoint(self):
        """Test database health check endpoint"""
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestConfiguration:
    """Test development environment configuration"""

    def test_settings_loaded(self):
        """Test that settings are loaded correctly"""
        assert settings.PROJECT_NAME == "AssetFlow"
        assert settings.API_V1_STR == "/api/v1"
        # In test environment, ENVIRONMENT should be "test"
        assert settings.ENVIRONMENT in ["development", "test"]

    def test_database_url_configuration(self):
        """Test database URL is configured correctly"""
        db_url = settings.database_url
        assert db_url is not None
        # Should be using PostgreSQL in development or SQLite in test
        assert (
            db_url.startswith("postgresql://")
            or db_url.startswith("sqlite://")
            or db_url.startswith("sqlite+aiosqlite://")
        )

    def test_cors_origins_configuration(self):
        """Test CORS origins are configured correctly"""
        cors_origins = settings.get_cors_origins()
        assert isinstance(cors_origins, list)
        assert len(cors_origins) > 0
        assert all(origin.startswith("http://") for origin in cors_origins)

    def test_mock_search_enabled(self):
        """Test that mock search is enabled in development"""
        assert settings.USE_MOCK_SEARCH is True

    def test_api_keys_configured(self):
        """Test that API keys are configured (even if mock)"""
        assert settings.OPENAI_API_KEY is not None
        assert settings.TAVILY_API_KEY is not None


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation generation"""

    def test_openapi_json_endpoint(self):
        """Test OpenAPI JSON endpoint is accessible"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert openapi_spec["info"]["title"] == "AssetFlow API"

    def test_docs_endpoint_accessible(self):
        """Test that docs endpoint is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_accessible(self):
        """Test that ReDoc endpoint is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestCodeQuality:
    """Test code quality configuration"""

    def test_ruff_configuration_exists(self):
        """Test that Ruff configuration is properly set up"""
        import os
        import subprocess

        # Change to backend directory for the test
        original_cwd = os.getcwd()
        try:
            os.chdir("backend" if "backend" not in os.getcwd() else ".")
            result = subprocess.run(
                ["uv", "run", "ruff", "check", "--quiet", "."],
                capture_output=True,
                text=True,
            )
            # Should not have any errors (exit code 0)
            assert result.returncode == 0, f"Ruff check failed: {result.stdout}"
        finally:
            os.chdir(original_cwd)
