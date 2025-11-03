"""
Govly Sync Service - Proactive opportunity fetching and deduplication.

This service periodically fetches opportunities from Govly API and merges them
with webhook-ingested data in state.json. It provides:
- Scheduled polling (configurable interval)
- Deduplication with existing opportunities
- Federal FY routing
- Sync status reporting
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Set

from mcp.integrations.govly_client import GovlyAPIError, GovlyClient, GovlyRateLimitError

logger = logging.getLogger(__name__)


class GovlySyncService:
    """
    Background service for syncing Govly opportunities.

    Features:
    - Periodic polling of Govly API
    - Deduplication with webhook data
    - State persistence
    - Error handling and retry logic
    - Status reporting for TUI
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        state_file: str = "data/state.json",
        sync_interval: int = 300,  # 5 minutes
        fetch_hours: int = 48,  # Fetch last 48 hours
        enabled: bool = True,
    ):
        """
        Initialize Govly sync service.

        Args:
            api_key: Govly API key (or use GOVLY_API_KEY env var)
            state_file: Path to state.json
            sync_interval: Seconds between sync runs (default: 300 = 5 minutes)
            fetch_hours: Hours of history to fetch (default: 48)
            enabled: Whether service is enabled (default: True)
        """
        self.api_key = api_key or os.getenv("GOVLY_API_KEY")
        self.state_file = Path(state_file)
        self.sync_interval = sync_interval
        self.fetch_hours = fetch_hours
        self.enabled = enabled

        # Service state
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_success: bool = False
        self.last_sync_error: Optional[str] = None
        self.sync_count: int = 0
        self.opportunities_added: int = 0

        # Govly client (lazy init)
        self._client: Optional[GovlyClient] = None

        logger.info(f"Initialized Govly sync service (interval={sync_interval}s, enabled={enabled})")

    @property
    def client(self) -> GovlyClient:
        """Lazy-initialize Govly API client."""
        if self._client is None:
            self._client = GovlyClient(api_key=self.api_key)
        return self._client

    def start(self):
        """Start the sync service in background thread."""
        if not self.enabled:
            logger.info("Govly sync service disabled, not starting")
            return

        if self.running:
            logger.warning("Govly sync service already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name="GovlySync")
        self.thread.start()
        logger.info("Govly sync service started")

    def stop(self):
        """Stop the sync service."""
        if not self.running:
            return

        logger.info("Stopping Govly sync service...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=10)

        if self._client:
            self._client.close()

        logger.info("Govly sync service stopped")

    def _run_loop(self):
        """Main sync loop (runs in background thread)."""
        logger.info("Govly sync loop started")

        # Run initial sync immediately
        self._sync_opportunities()

        # Then run on schedule
        while self.running:
            try:
                time.sleep(self.sync_interval)
                if self.running:  # Check again after sleep
                    self._sync_opportunities()
            except Exception as e:
                logger.error(f"Unexpected error in sync loop: {e}", exc_info=True)
                time.sleep(60)  # Wait before retrying after fatal error

        logger.info("Govly sync loop exited")

    def _sync_opportunities(self):
        """Fetch opportunities and merge into state."""
        logger.info(f"Starting Govly sync #{self.sync_count + 1}")
        start_time = time.time()

        try:
            # Fetch opportunities from API
            opportunities = self.client.fetch_opportunities(
                limit=200,
                since_hours=self.fetch_hours,
            )

            # Load current state
            state = self._load_state()
            existing_ids = self._get_existing_ids(state)

            # Filter to new opportunities only
            new_opps = []
            for opp in opportunities:
                opp_id = self._generate_id(opp)
                if opp_id not in existing_ids:
                    # Normalize to standard format
                    normalized = self._normalize_opportunity(opp, opp_id)
                    new_opps.append(normalized)

            # Add new opportunities to state
            if new_opps:
                state.setdefault("opportunities", []).extend(new_opps)
                self._save_state(state)
                logger.info(f"Added {len(new_opps)} new Govly opportunities to state")
                self.opportunities_added += len(new_opps)
            else:
                logger.debug("No new opportunities found")

            # Update sync stats
            elapsed = time.time() - start_time
            self.last_sync_time = datetime.now(timezone.utc)
            self.last_sync_success = True
            self.last_sync_error = None
            self.sync_count += 1

            logger.info(f"Govly sync completed in {elapsed:.2f}s ({len(new_opps)} new)")

        except GovlyRateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            self.last_sync_success = False
            self.last_sync_error = f"Rate limited (retry in {e.retry_after}s)"
            # Wait for rate limit to reset
            if e.retry_after:
                time.sleep(e.retry_after)

        except GovlyAPIError as e:
            logger.error(f"Govly API error during sync: {e}")
            self.last_sync_success = False
            self.last_sync_error = str(e)

        except Exception as e:
            logger.error(f"Unexpected error during sync: {e}", exc_info=True)
            self.last_sync_success = False
            self.last_sync_error = str(e)

    def sync_now(self) -> Dict:
        """
        Trigger immediate sync (manual trigger from TUI).

        Returns:
            Sync result dictionary with status and counts
        """
        if not self.enabled:
            return {"success": False, "error": "Govly sync service is disabled"}

        logger.info("Manual sync triggered")
        initial_count = self.opportunities_added

        try:
            self._sync_opportunities()

            new_count = self.opportunities_added - initial_count
            return {
                "success": self.last_sync_success,
                "new_opportunities": new_count,
                "sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
                "error": self.last_sync_error,
            }

        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict:
        """
        Get current sync service status.

        Returns:
            Status dictionary for display in TUI
        """
        return {
            "enabled": self.enabled,
            "running": self.running,
            "state": "online" if (self.running and self.last_sync_success) else "error" if not self.last_sync_success else "offline",
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "sync_count": self.sync_count,
            "opportunities_added": self.opportunities_added,
            "last_error": self.last_sync_error,
            "next_sync_in": self.sync_interval if self.running else None,
        }

    def _load_state(self) -> Dict:
        """Load state.json with fallback."""
        if not self.state_file.exists():
            return {"opportunities": [], "recent_actions": []}

        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load state.json: {e}")
            return {"opportunities": [], "recent_actions": []}

    def _save_state(self, state: Dict):
        """Atomically save state.json."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.state_file.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                json.dump(state, f, indent=2)
            temp_file.replace(self.state_file)
        except IOError as e:
            logger.error(f"Failed to save state.json: {e}")
            raise

    def _get_existing_ids(self, state: Dict) -> Set[str]:
        """Get set of existing opportunity IDs."""
        return {opp.get("id") for opp in state.get("opportunities", []) if opp.get("id")}

    def _generate_id(self, opp: Dict) -> str:
        """Generate unique ID from opportunity data."""
        # Try various ID fields that might exist
        external_id = (
            opp.get("id")
            or opp.get("event_id")
            or opp.get("opportunity_id")
            or opp.get("govly_id")
            or str(hash(opp.get("title", "") + str(opp.get("posted_date", ""))))
        )
        return f"govly_{external_id}".lower().replace(" ", "_")

    def _normalize_opportunity(self, opp: Dict, opp_id: str) -> Dict:
        """
        Normalize API opportunity to standard format.

        Converts various API field names to our standard schema matching
        the webhook format.
        """
        return {
            "id": opp_id,
            "source": "govly",
            "title": opp.get("title") or opp.get("name") or "Untitled",
            "description": opp.get("description") or opp.get("summary"),
            "estimated_amount": (opp.get("estimated_amount") or opp.get("amount") or opp.get("value") or 0),
            "agency": opp.get("agency") or opp.get("agency_name"),
            "posted_date": opp.get("posted_date") or opp.get("created_at"),
            "close_date": opp.get("close_date") or opp.get("due_date"),
            "source_url": opp.get("source_url") or opp.get("url") or opp.get("link"),
            "triage": True,  # All API-fetched opps start in triage
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ingestion_method": "api_poll",  # vs "webhook"
        }

    def _calculate_fy(self, close_date: Optional[str]) -> Optional[str]:
        """Calculate Federal Fiscal Year from close date."""
        if not close_date:
            return None

        try:
            dt = datetime.fromisoformat(close_date.replace("Z", "+00:00"))
            if dt.month >= 10:
                return f"FY{dt.year + 1}"
            else:
                return f"FY{dt.year}"
        except (ValueError, AttributeError):
            return None


# Global service instance
_govly_sync_service: Optional[GovlySyncService] = None


def get_service() -> Optional[GovlySyncService]:
    """Get global Govly sync service instance."""
    return _govly_sync_service


def start_service(
    api_key: Optional[str] = None,
    sync_interval: int = 300,
    enabled: bool = True,
) -> GovlySyncService:
    """
    Start global Govly sync service.

    Args:
        api_key: Govly API key
        sync_interval: Seconds between syncs
        enabled: Whether to enable service

    Returns:
        GovlySyncService instance
    """
    global _govly_sync_service

    if _govly_sync_service and _govly_sync_service.running:
        logger.warning("Govly sync service already running")
        return _govly_sync_service

    _govly_sync_service = GovlySyncService(
        api_key=api_key,
        sync_interval=sync_interval,
        enabled=enabled,
    )
    _govly_sync_service.start()
    return _govly_sync_service


def stop_service():
    """Stop global Govly sync service."""
    global _govly_sync_service

    if _govly_sync_service:
        _govly_sync_service.stop()
        _govly_sync_service = None
