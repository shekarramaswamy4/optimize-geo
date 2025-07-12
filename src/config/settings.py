from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = "LumaRank API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="production", description="Environment (development/staging/production)")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])
    
    # Database settings
    database_url: str = Field(..., description="PostgreSQL database URL")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Maximum overflow connections")
    database_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    database_pool_recycle: int = Field(default=3600, description="Recycle connections after N seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries (debug)")
    
    # OpenAI settings
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    openai_max_tokens: int = Field(default=1000, description="Max tokens for OpenAI response")
    openai_temperature: float = Field(default=0.7, description="Temperature for OpenAI response")
    openai_timeout: int = Field(default=30, description="Timeout for OpenAI API calls in seconds")
    
    # HTTP client settings
    http_timeout: int = Field(default=30, description="HTTP client timeout in seconds")
    http_max_retries: int = Field(default=3, description="Maximum number of HTTP retries")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Feature flags
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Number of requests per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        allowed = ["json", "text"]
        if v not in allowed:
            raise ValueError(f"log_format must be one of {allowed}")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()