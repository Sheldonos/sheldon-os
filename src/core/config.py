"""
Sheldon OS Configuration Management

Handles system-wide configuration, environment variables, and settings.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    """Database configuration settings"""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="sheldon_os", description="Database name")
    user: str = Field(default="sheldon", description="Database user")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(
        default=20,
        description="Max connection overflow",
    )

    @property
    def url(self) -> str:
        """Generate database URL"""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class RedisConfig(BaseModel):
    """Redis configuration settings"""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    max_connections: int = Field(default=50, description="Max connections")

    @property
    def url(self) -> str:
        """Generate Redis URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class LLMConfig(BaseModel):
    """LLM provider configuration"""

    provider: str = Field(
        default="anthropic", description="LLM provider (anthropic, openai)"
    )
    model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model name",
    )
    api_key: str = Field(default="", description="API key")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature",
    )
    max_tokens: int = Field(default=4096, description="Max tokens")
    timeout: int = Field(default=60, description="Request timeout in seconds")


class AgentConfig(BaseModel):
    """Agent system configuration"""

    max_concurrent_agents: int = Field(
        default=100,
        description="Max concurrent agents",
    )
    agent_timeout: int = Field(
        default=300,
        description="Agent timeout in seconds",
    )
    retry_attempts: int = Field(
        default=3, description="Retry attempts for failed tasks"
    )
    health_check_interval: int = Field(
        default=60, description="Health check interval in seconds"
    )
    context_window_size: int = Field(
        default=10000,
        description="Context window size",
    )


class MemoryConfig(BaseModel):
    """Memory system configuration"""

    short_term_capacity: int = Field(
        default=1000, description="Short-term memory capacity"
    )
    long_term_capacity: int = Field(
        default=100000, description="Long-term memory capacity"
    )
    consolidation_interval: int = Field(
        default=3600, description="Memory consolidation interval"
    )
    retention_days: int = Field(
        default=90,
        description="Memory retention in days",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="Embedding model"
    )
    vector_backend: str = Field(
        default="zeroentropy",
        description="Vector backend (zeroentropy, pgvector, pinecone)",
    )
    reranker_enabled: bool = Field(
        default=True, description="Enable reranking after candidate retrieval"
    )
    reranker_model: str = Field(
        default="zeroentropy-reranker", description="Reranker model identifier"
    )
    graph_backend: str = Field(
        default="neo4j",
        description="Knowledge graph backend",
    )
    graph_expansion_hops: int = Field(
        default=2, description="Max graph traversal hops during retrieval"
    )
    synthesis_enabled: bool = Field(
        default=True,
        description="Enable synthesized answers from retrieved evidence",
    )
    gap_analysis_enabled: bool = Field(
        default=True,
        description="Enable missing-information detection before action",
    )


class SecurityConfig(BaseModel):
    """Security configuration"""

    secret_key: str = Field(
        default="",
        description="Secret key for encryption",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiry"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiry"
    )
    allowed_origins: List[str] = Field(
        default=["*"], description="CORS allowed origins"
    )


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration"""

    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="json",
        description="Log format (json, text)",
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection",
    )
    tracing_enabled: bool = Field(
        default=True, description="Enable distributed tracing"
    )
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")


class Config(BaseSettings):
    """Main Sheldon OS configuration

    Loads configuration from environment variables and .env file.
    """

    # Environment
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(default=False, description="Debug mode")

    # System
    system_name: str = Field(default="Sheldon OS", description="System name")
    version: str = Field(default="0.1.0", description="System version")
    base_path: Path = Field(default=Path.cwd(), description="Base path")

    # Compatibility fields used by fixtures/tests
    database_url: Optional[str] = Field(
        default=None, description="Optional flat database URL override"
    )
    redis_url: Optional[str] = Field(
        default=None, description="Optional flat redis URL override"
    )
    log_level: Optional[str] = Field(
        default=None, description="Optional flat log level override"
    )
    max_agents: Optional[int] = Field(
        default=None, description="Optional flat max agents override"
    )
    memory_retention_days: Optional[int] = Field(
        default=None, description="Optional flat memory retention override"
    )

    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="API workers")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production", "test"]
        if value not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return value

    @field_validator("base_path")
    @classmethod
    def validate_base_path(cls, value: Path) -> Path:
        """Ensure base path exists."""
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def model_post_init(  # pylint: disable=arguments-differ
        self, __context: Any
    ) -> None:
        """Apply flat compatibility overrides after model initialization."""
        if self.database_url and self.database_url.startswith("sqlite"):
            self.database = DatabaseConfig(
                host="localhost",
                port=0,
                name=self.database_url,
                user="",
                password="",
            )

        if self.redis_url and self.redis_url.startswith("redis://"):
            try:
                remainder = self.redis_url.replace("redis://", "", 1)
                host_port, _, db_part = remainder.partition("/")
                host, _, port = host_port.partition(":")
                self.redis = RedisConfig(
                    host=host or "localhost",
                    port=int(port) if port else 6379,
                    db=int(db_part) if db_part else 0,
                )
            except ValueError:
                pass

        if self.log_level:
            self.monitoring.log_level = self.log_level

        if self.max_agents is not None:
            self.agent.max_concurrent_agents = self.max_agents

        if self.memory_retention_days is not None:
            self.memory.retention_days = self.memory_retention_days

    def get_data_dir(self) -> Path:
        """Get data directory path"""
        data_dir = self.base_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def get_logs_dir(self) -> Path:
        """Get logs directory path"""
        logs_dir = self.base_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    def get_cache_dir(self) -> Path:
        """Get cache directory path"""
        cache_dir = self.base_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return self.model_dump()


class _ConfigCache:  # pylint: disable=too-few-public-methods
    """Internal cache holder for the singleton configuration."""

    current: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    if _ConfigCache.current is None:
        _ConfigCache.current = Config()
    return _ConfigCache.current


def reload_config() -> Config:
    """Reload configuration."""
    _ConfigCache.current = Config()
    return _ConfigCache.current


# Made with Bob
