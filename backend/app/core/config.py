"""
Configuration settings for AssetFlow backend
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AssetFlow"

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "assetflow"
    POSTGRES_PASSWORD: str = "assetflow123"
    POSTGRES_DB: str = "assetflow"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str | None = None  # Optional override for development

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"

    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # External APIs
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str | None = None
    TAVILY_API_KEY: str | None = None
    
    # Phase 4: Vector Memory Configuration
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-large-zh-v1.5"  # Local BGE embedding model (1024 dimensions)
    USE_LOCAL_EMBEDDING: bool = True  # Use local embedding model instead of OpenAI API

    # Environment
    ENVIRONMENT: str = "development"
    USE_MOCK_SEARCH: bool = True  # Use mock search in development

    # CORS - 支持局域网访问
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:8081,http://10.36.234.5:8080,http://10.36.234.5:3000"

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as a list"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS

    @property
    def database_url(self) -> str:
        """Construct database URL"""
        # Use DATABASE_URL if set (for SQLite in development)
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
