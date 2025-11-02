"""Configuration loader for DealCraft API and Scoring System."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


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


class ScoringConfig:
    """Scoring configuration loader and cache."""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        """Singleton pattern to ensure config is loaded once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load scoring configuration from JSON file."""
        config_path = Path(__file__).parent.parent.parent / "data" / "config" / "scoring_weights.json"

        if not config_path.exists():
            logger.warning(f"Scoring config not found at {config_path}, using defaults")
            self._config = self._get_default_config()
            return

        try:
            with open(config_path) as f:
                self._config = json.load(f)
            logger.info(f"Loaded scoring configuration from {config_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load scoring config: {e}, using defaults")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file not found."""
        return {
            "version": "2.1",
            "oem_alignment_scores": {"Default": 50},
            "contract_vehicle_scores": {"Default": 50},
            "region_bonuses": {},
            "customer_org_bonuses": {"Default": 2.0},
            "cv_recommendation_bonuses": {"single": 5.0, "multiple": 7.0},
            "stage_multipliers": {"Default": 0.20},
            "guardrails": {
                "max_total_bonus": 15.0,
                "min_score": 0.0,
                "max_score": 100.0,
                "min_win_prob": 0.0,
                "max_win_prob": 1.0,
            },
        }

    @property
    def oem_alignment_scores(self) -> Dict[str, float]:
        """Get OEM alignment scores."""
        return self._config.get("oem_alignment_scores", {})

    @property
    def contract_vehicle_scores(self) -> Dict[str, float]:
        """Get contract vehicle scores."""
        return self._config.get("contract_vehicle_scores", {})

    @property
    def region_bonuses(self) -> Dict[str, float]:
        """Get region bonus scores."""
        return self._config.get("region_bonuses", {})

    @property
    def customer_org_bonuses(self) -> Dict[str, float]:
        """Get customer organization bonus scores."""
        return self._config.get("customer_org_bonuses", {})

    @property
    def cv_recommendation_bonuses(self) -> Dict[str, float]:
        """Get CV recommendation bonus scores."""
        return self._config.get("cv_recommendation_bonuses", {})

    @property
    def stage_multipliers(self) -> Dict[str, float]:
        """Get stage multipliers for win probability."""
        return self._config.get("stage_multipliers", {})

    @property
    def guardrails(self) -> Dict[str, float]:
        """Get guardrail limits."""
        return self._config.get("guardrails", {})

    def reload(self) -> None:
        """Reload configuration from disk."""
        self._load_config()


# Global config instances
config = Config()
scoring_config = ScoringConfig()
