"""
Configuration management for the AI Journal system.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    openai_api_key: str
    model: str = "gpt-5-nano"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()