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
    USE_MOCK_LLM: bool = False  # Use mock LLM provider (for testing without API key)
    
    # Phase 2: Real Estate Engine Feature Flags
    ENABLE_REAL_ESTATE_ENGINE: bool = True      # 启用房产引擎
    ENABLE_PROPERTY_VALUATION_API: bool = False  # 启用外部估值 API (贝壳/链家)
    ENABLE_SWAP_SIMULATOR: bool = True          # 启用置换模拟
    ENABLE_ANCHOR_QUADRANT: bool = True         # 启用锚点象限
    
    # Property Valuation Configuration
    PROPERTY_API_PROVIDER: str = "mock"          # mock / beike / lianjia
    PROPERTY_API_KEY: str | None = None
    PROPERTY_VALUATION_CACHE_TTL: int = 86400   # 估值缓存24小时
    
    # Phase 4: ActionReasoner Feature Flags
    ENABLE_ACTION_REASONER: bool = True         # 启用方案推理器
    ENABLE_FAMILY_PROFILE: bool = True          # 启用家庭画像
    ENABLE_MEMORY_STORAGE: bool = True          # 启用长期记忆存储
    ENABLE_ENHANCED_EXTRACTION: bool = True     # 启用增强信息提取
    ACTION_PLAN_AUTO_GENERATE: bool = True      # 自动生成行动计划 (Phase 4 启用)
    
    # Phase 4: RAG Integration
    ENABLE_RAG_AUGMENTATION: bool = True        # 启用 RAG 知识增强
    RAG_CONFIDENCE_THRESHOLD: float = 0.3       # 低于此阈值不使用 RAG 结果
    RAG_TOP_K: int = 5                          # 检索知识数量

    # CORS - 支持局域网访问
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:8081,http://10.36.234.27:8080,http://10.36.234.5:3000"

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


def get_settings() -> Settings:
    """Get the global settings instance.
    
    This function exists for compatibility with code that imports get_settings().
    It simply returns the global settings singleton.
    """
    return settings
