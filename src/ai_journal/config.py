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
    log_level: str = "DEBUG"  # Can be DEBUG, INFO, WARNING, ERROR
    
    # v2 Excavation Parameters (server-only constants)
    tau_high: float = 0.80  # confidence threshold for exit
    delta_gap: float = 0.25  # margin to second-best for exit
    n_confirmations: int = 2  # confirmation votes needed for exit
    k_budget: int = 4  # maximum probe turns
    max_hypotheses: int = 4  # maximum concurrent hypotheses
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()