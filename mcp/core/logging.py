"""JSON logging configuration for Red River Sales MCP API."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.core.config import config


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status"):
            log_data["status"] = record.status

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging() -> None:
    """Configure JSON logging for the application."""
    # Load logging configuration from file if it exists
    logging_config_path = Path(__file__).parent.parent.parent / "logging.json"

    if logging_config_path.exists():
        with open(logging_config_path) as f:
            logging_config = json.load(f)
            log_level = logging_config.get("level", config.log_level)
    else:
        log_level = config.log_level

    # Set up root logger with JSON formatter
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)


def log_request(
    request_id: str,
    method: str,
    path: str,
    status: int,
    latency_ms: float,
) -> None:
    """Log an HTTP request with structured data."""
    logger = logging.getLogger(__name__)
    logger.info(
        f"{method} {path} {status}",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status": status,
            "latency_ms": latency_ms,
        },
    )


# Configure logging on module import
configure_logging()
