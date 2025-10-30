"""
Pytest configuration and shared fixtures for tests.
"""

import pytest


@pytest.fixture(autouse=True)
def clear_rate_limit_buckets():
    """
    Clear rate limit buckets before each test to ensure isolation.

    This prevents rate limits from one test affecting others when running
    the full test suite.
    """
    from mcp.api.middleware import rate_limit

    # Clear buckets before test
    rate_limit._buckets.clear()

    yield

    # Clear buckets after test (cleanup)
    rate_limit._buckets.clear()
