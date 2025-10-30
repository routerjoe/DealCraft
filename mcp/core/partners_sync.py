from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class PartnerTierRecord:
    oem: str
    tier_global: str
    tier_redriver: str
    source: str
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class PartnerTierSync:
    """
    Stub for Sprint 17 partner tier ingestion & sync.
    Responsibilities:
      - load_sources(...): load CSV/JSONL/MD partner tier inputs
      - validate(...): enforce unified schema keys
      - plan_updates(...): compute diffs for OEM Hubs / partners.db
      - apply_updates(...): write changes when dry_run=False
    """

    def __init__(self, vault_root: Path):
        self.vault_root = vault_root

    def load_sources(self, paths: List[Path]) -> List[PartnerTierRecord]:
        # TODO: implement
        return []

    def validate(self, records: List[PartnerTierRecord]) -> Tuple[bool, List[str]]:
        # TODO: implement schema checks
        return True, []

    def plan_updates(self, records: List[PartnerTierRecord]) -> Dict[str, Any]:
        # TODO: compute OEM hub YAML changes & DB upserts
        return {"oem_yaml_updates": [], "db_upserts": []}

    def apply_updates(self, plan: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        # TODO: write YAML + rebuild partners.db if dry_run=False
        return {"applied": not dry_run, "summary": plan}
