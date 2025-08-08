"""
Configuration settings for the AI Journal Reflection System.
"""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    
    # Model configuration
    INGESTOR_MODEL: str = "gpt-4o-mini"
    COACH_MODEL: str = "gpt-4o-mini"
    
    # Feature flags
    LLM_ORCHESTRATOR_ENABLED: bool = False
    PHILOSOPHY_SCOUT_ENABLED: bool = False
    
    # Limits and timeouts
    MAX_PROMPTS: int = 5
    AGENT_TIMEOUT_SEC: int = 8
    GLOBAL_TIMEOUT_SEC: int = 25
    MAX_JOURNAL_LENGTH: int = 10000
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # Logging settings
    REDACT_INPUTS: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    RATE_LIMIT_BURST: int = 5
    
    # OpenAI specific limits
    MAX_TOKENS_PER_REQUEST: int = 4000
    TEMPERATURE: float = 0.2
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_openai_client():
    """Get configured OpenAI client."""
    import openai
    
    client_kwargs = {}
    
    if settings.OPENAI_API_KEY:
        client_kwargs["api_key"] = settings.OPENAI_API_KEY
    
    if settings.OPENAI_BASE_URL:
        client_kwargs["base_url"] = settings.OPENAI_BASE_URL
    
    return openai.AsyncOpenAI(**client_kwargs)


# Global settings instance
settings = Settings()


def validate_settings():
    """Validate required settings are present."""
    if not settings.OPENAI_API_KEY:
        # Check if it's available as environment variable
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY must be set either in settings or as environment variable"
            )
    
    if settings.AGENT_TIMEOUT_SEC >= settings.GLOBAL_TIMEOUT_SEC:
        raise ValueError(
            "AGENT_TIMEOUT_SEC must be less than GLOBAL_TIMEOUT_SEC"
        )
    
    if settings.MAX_PROMPTS > 10:
        raise ValueError("MAX_PROMPTS should not exceed 10 for performance reasons")
    
    return True