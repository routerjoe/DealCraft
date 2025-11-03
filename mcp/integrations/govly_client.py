"""
Govly API Client for proactive opportunity fetching.

This client integrates with Govly's enterprise API to fetch federal contracting
opportunities. It complements the webhook integration by enabling proactive polling.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class GovlyAPIError(Exception):
    """Base exception for Govly API errors."""

    pass


class GovlyAuthenticationError(GovlyAPIError):
    """Authentication failed."""

    pass


class GovlyRateLimitError(GovlyAPIError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class GovlyClient:
    """
    Govly API client for fetching federal contracting opportunities.

    Enterprise API access required. Get your API key from:
    https://www.govly.com/app/settings/api_settings

    Usage:
        client = GovlyClient(api_key="your_key")
        opportunities = client.fetch_opportunities(limit=100, since_hours=24)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.govly.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Govly API client.

        Args:
            api_key: Govly API key (or set GOVLY_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts for failed requests
        """
        self.api_key = api_key or os.getenv("GOVLY_API_KEY")
        if not self.api_key:
            raise GovlyAuthenticationError("Govly API key not provided. Set GOVLY_API_KEY or pass api_key parameter.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "DealCraft/2.0",
            }
        )

        logger.info(f"Initialized Govly API client (base_url={self.base_url})")

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict:
        """
        Make authenticated API request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json: JSON request body

        Returns:
            Response JSON data

        Raises:
            GovlyAuthenticationError: Authentication failed
            GovlyRateLimitError: Rate limit exceeded
            GovlyAPIError: Other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.debug(f"{method} {url} params={params}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                retry_after_int = int(retry_after) if retry_after else 60
                logger.warning(f"Rate limit hit, retry after {retry_after_int}s")
                raise GovlyRateLimitError(f"Rate limit exceeded. Retry after {retry_after_int}s", retry_after=retry_after_int)

            # Handle authentication errors
            if response.status_code == 401:
                logger.error("Govly API authentication failed")
                raise GovlyAuthenticationError("Invalid or expired API key")

            # Handle other errors
            if response.status_code >= 400:
                error_msg = f"Govly API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise GovlyAPIError(error_msg)

            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {self.timeout}s")
            raise GovlyAPIError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise GovlyAPIError(f"Request failed: {e}")

    def fetch_opportunities(
        self,
        limit: int = 100,
        offset: int = 0,
        since_hours: Optional[int] = None,
        since_date: Optional[str] = None,
        agencies: Optional[List[str]] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """
        Fetch opportunities from Govly API.

        Args:
            limit: Maximum number of opportunities to return (default: 100)
            offset: Pagination offset (default: 0)
            since_hours: Fetch opportunities posted in last N hours
            since_date: Fetch opportunities since date (ISO 8601 format)
            agencies: Filter by agency names (list)
            amount_min: Minimum estimated amount
            amount_max: Maximum estimated amount
            status: Opportunity status filter (e.g., 'open', 'closed')

        Returns:
            List of opportunity dictionaries

        Example:
            # Fetch last 24 hours of opportunities
            opps = client.fetch_opportunities(limit=50, since_hours=24)

            # Fetch by date range and agency
            opps = client.fetch_opportunities(
                since_date="2025-11-01T00:00:00Z",
                agencies=["Department of Defense", "GSA"],
                amount_min=100000
            )
        """
        params = {
            "limit": limit,
            "offset": offset,
        }

        # Time-based filtering
        if since_hours:
            since_dt = datetime.utcnow() - timedelta(hours=since_hours)
            params["since"] = since_dt.isoformat() + "Z"
        elif since_date:
            params["since"] = since_date

        # Additional filters
        if agencies:
            params["agencies"] = ",".join(agencies)
        if amount_min is not None:
            params["amount_min"] = amount_min
        if amount_max is not None:
            params["amount_max"] = amount_max
        if status:
            params["status"] = status

        try:
            # Attempt common REST endpoint patterns
            # Try /opportunities first (most common)
            try:
                data = self._request("GET", "/opportunities", params=params)
                logger.info(f"Fetched {len(data.get('opportunities', []))} opportunities from Govly")
                return data.get("opportunities", data.get("data", []))
            except GovlyAPIError as e:
                # If /opportunities doesn't work, try /contracts
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.debug("/opportunities not found, trying /contracts")
                    data = self._request("GET", "/contracts", params=params)
                    logger.info(f"Fetched {len(data.get('contracts', []))} opportunities from Govly")
                    return data.get("contracts", data.get("data", []))
                raise

        except GovlyAPIError as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            raise

    def get_opportunity(self, opportunity_id: str) -> Optional[Dict]:
        """
        Fetch single opportunity by ID.

        Args:
            opportunity_id: Govly opportunity ID

        Returns:
            Opportunity dictionary or None if not found
        """
        try:
            data = self._request("GET", f"/opportunities/{opportunity_id}")
            logger.info(f"Fetched opportunity {opportunity_id}")
            return data.get("opportunity", data)
        except GovlyAPIError as e:
            if "404" in str(e):
                logger.warning(f"Opportunity {opportunity_id} not found")
                return None
            logger.error(f"Failed to fetch opportunity {opportunity_id}: {e}")
            raise

    def search_opportunities(
        self,
        query: str,
        limit: int = 50,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Search opportunities by keyword.

        Args:
            query: Search query string
            limit: Maximum results
            filters: Additional filters (agencies, amount_range, etc.)

        Returns:
            List of matching opportunities
        """
        params = {
            "q": query,
            "limit": limit,
        }

        if filters:
            params.update(filters)

        try:
            data = self._request("GET", "/opportunities/search", params=params)
            logger.info(f"Search '{query}' returned {len(data.get('results', []))} results")
            return data.get("results", data.get("opportunities", []))
        except GovlyAPIError as e:
            logger.error(f"Search failed for '{query}': {e}")
            raise

    def get_contract_vehicles(self) -> List[Dict]:
        """
        Get list of available contract vehicles.

        Returns:
            List of contract vehicle dictionaries
        """
        try:
            data = self._request("GET", "/contract-vehicles")
            logger.info(f"Fetched {len(data.get('vehicles', []))} contract vehicles")
            return data.get("vehicles", data.get("data", []))
        except GovlyAPIError as e:
            logger.error(f"Failed to fetch contract vehicles: {e}")
            raise

    def get_agencies(self) -> List[Dict]:
        """
        Get list of federal agencies.

        Returns:
            List of agency dictionaries
        """
        try:
            data = self._request("GET", "/agencies")
            logger.info(f"Fetched {len(data.get('agencies', []))} agencies")
            return data.get("agencies", data.get("data", []))
        except GovlyAPIError as e:
            logger.error(f"Failed to fetch agencies: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if API is accessible and authenticated.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Try a lightweight endpoint
            data = self._request("GET", "/health")
            return data.get("status") == "ok"
        except GovlyAPIError:
            # If /health doesn't exist, try fetching with limit=1
            try:
                self.fetch_opportunities(limit=1)
                return True
            except GovlyAPIError:
                return False

    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.debug("Govly API client session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick usage
def create_client(api_key: Optional[str] = None) -> GovlyClient:
    """
    Create Govly API client with default settings.

    Args:
        api_key: Optional API key (uses GOVLY_API_KEY env var if not provided)

    Returns:
        GovlyClient instance
    """
    return GovlyClient(api_key=api_key)
