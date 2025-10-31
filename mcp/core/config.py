"""Configuration loader for DealCraft API."""

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self) -> None:
        """Load configuration from .env file."""
        # Load .env from project root
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)

        # API Configuration
        self.host: str = os.getenv("API_HOST", "0.0.0.0")
        self.port: int = int(os.getenv("API_PORT", "8000"))
        self.reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"

        # Environment
        self.environment: str = os.getenv("ENVIRONMENT", "development")

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __repr__(self) -> str:
        """Return string representation of config."""
        return f"Config(host={self.host}, port={self.port}, environment={self.environment})"


# Global config instance
config = Config()
