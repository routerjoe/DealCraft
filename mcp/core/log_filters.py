"""
Log redaction filter to mask sensitive information in logs.

This module provides a logging filter that automatically redacts common
sensitive patterns like API keys, tokens, emails, and other secrets.
"""

import logging
import re
from typing import Pattern


class RedactingFilter(logging.Filter):
    """
    Logging filter that redacts sensitive information from log messages.

    Patterns matched and masked:
    - Bearer tokens (Bearer xxxx)
    - API keys starting with sk- (OpenAI style)
    - Email addresses
    - Slack tokens (xoxb-, xoxp-, xoxa-)
    - Webhook HMAC headers (x-webhook-signature, x-hub-signature)
    - Common secret patterns (token=, key=, secret=)
    """

    def __init__(self, name: str = ""):
        """Initialize the redacting filter."""
        super().__init__(name)

        # Compile patterns once for performance
        self.patterns: list[tuple[Pattern, str]] = [
            # Bearer tokens
            (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer ***"),
            # OpenAI-style API keys
            (re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE), "sk-***"),
            # Email addresses
            (
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
                "***@***.***",
            ),
            # Slack tokens
            (re.compile(r"xox[bpas]-[A-Za-z0-9\-]+", re.IGNORECASE), "xox*-***"),
            # Webhook signatures (values only, preserve header names)
            (
                re.compile(
                    r"(x-webhook-signature|x-hub-signature):\s*[A-Za-z0-9+/=]+",
                    re.IGNORECASE,
                ),
                r"\1: ***",
            ),
            # Generic secret patterns in key=value format
            (
                re.compile(r"(token|key|secret|password|apikey)=[\w\-\.]+", re.IGNORECASE),
                r"\1=***",
            ),
            # URL query strings with sensitive params
            (
                re.compile(r"([?&])(token|key|secret|password|apikey)=[^&\s]+", re.IGNORECASE),
                r"\1\2=***",
            ),
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter and redact sensitive information from log records.

        Args:
            record: The log record to filter

        Returns:
            True (always allows the record through, just modifies it)
        """
        # Redact the main message
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)

        # Redact any string arguments
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact_value(arg) for arg in record.args)

        return True

    def _redact(self, text: str) -> str:
        """
        Redact sensitive patterns from text.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        for pattern, replacement in self.patterns:
            text = pattern.sub(replacement, text)
        return text

    def _redact_value(self, value):
        """
        Redact a value if it's a string, otherwise return as-is.

        Args:
            value: Value to potentially redact

        Returns:
            Redacted value (if string) or original value
        """
        if isinstance(value, str):
            return self._redact(value)
        return value


def install_redacting_filter(logger_name: str = None):
    """
    Install the redacting filter on a logger.

    Args:
        logger_name: Name of logger to filter (None for root logger)

    Example:
        >>> install_redacting_filter()  # Install on root logger
        >>> install_redacting_filter("mcp.api")  # Install on specific logger
    """
    logger = logging.getLogger(logger_name)
    redacting_filter = RedactingFilter()
    logger.addFilter(redacting_filter)
