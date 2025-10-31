"""Partner relationship graph modeling and analytics.

This module provides graph-based partner relationship modeling with
adjacency list representation and basic analytics capabilities.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class PartnerNode:
    """Represents a partner node in the graph."""

    name: str
    tier: str
    oem: str
    program: str
    poc: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "name": self.name,
            "tier": self.tier,
            "oem": self.oem,
            "program": self.program,
            "poc": self.poc,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class PartnerRelationship:
    """Represents a relationship edge between partners or partner-OEM."""

    source: str
    target: str
    relationship_type: str  # "partner_oem", "partner_partner", "same_program"
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary representation."""
        return {
            "source": self.source,
            "target": self.target,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "metadata": self.metadata,
        }


class PartnerGraph:
    """Graph structure for partner relationships with analytics."""

    def __init__(self):
        """Initialize empty partner graph."""
        self.nodes: Dict[str, PartnerNode] = {}
        self.edges: List[PartnerRelationship] = []
        self._adjacency_list: Dict[str, List[str]] = {}
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add_node(self, node: PartnerNode) -> None:
        """Add a partner node to the graph.

        Args:
            node: PartnerNode to add
        """
        self.nodes[node.name] = node
        if node.name not in self._adjacency_list:
            self._adjacency_list[node.name] = []

    def add_edge(self, edge: PartnerRelationship) -> None:
        """Add a relationship edge to the graph.

        Args:
            edge: PartnerRelationship to add
        """
        self.edges.append(edge)

        # Update adjacency list (bidirectional for partner-partner relationships)
        if edge.source not in self._adjacency_list:
            self._adjacency_list[edge.source] = []
        if edge.target not in self._adjacency_list:
            self._adjacency_list[edge.target] = []

        if edge.target not in self._adjacency_list[edge.source]:
            self._adjacency_list[edge.source].append(edge.target)

        # Bidirectional for partner-partner relationships
        if edge.relationship_type == "partner_partner":
            if edge.source not in self._adjacency_list[edge.target]:
                self._adjacency_list[edge.target].append(edge.source)

    def get_neighbors(self, node_name: str) -> List[str]:
        """Get all neighbors of a node.

        Args:
            node_name: Name of the node

        Returns:
            List of neighbor node names
        """
        return self._adjacency_list.get(node_name, [])

    def get_degree(self, node_name: str) -> int:
        """Get degree (number of connections) for a node.

        Args:
            node_name: Name of the node

        Returns:
            Number of connections
        """
        return len(self.get_neighbors(node_name))

    def get_degree_centrality(self, node_name: str) -> float:
        """Calculate degree centrality for a node.

        Degree centrality = degree / (total_nodes - 1)

        Args:
            node_name: Name of the node

        Returns:
            Degree centrality (0.0 to 1.0)
        """
        if len(self.nodes) <= 1:
            return 0.0

        degree = self.get_degree(node_name)
        max_possible = len(self.nodes) - 1
        return degree / max_possible

    def get_clustering_coefficient(self, node_name: str) -> float:
        """Calculate clustering coefficient for a node.

        Measures how connected a node's neighbors are to each other.

        Args:
            node_name: Name of the node

        Returns:
            Clustering coefficient (0.0 to 1.0)
        """
        neighbors = self.get_neighbors(node_name)
        k = len(neighbors)

        if k < 2:
            return 0.0

        # Count edges between neighbors
        edges_between_neighbors = 0
        for i, n1 in enumerate(neighbors):
            for n2 in neighbors[i + 1 :]:
                if n2 in self.get_neighbors(n1):
                    edges_between_neighbors += 1

        # Maximum possible edges between k neighbors
        max_possible = k * (k - 1) / 2

        return edges_between_neighbors / max_possible if max_possible > 0 else 0.0

    def get_partners_by_oem(self, oem: str) -> List[PartnerNode]:
        """Get all partners for a specific OEM.

        Args:
            oem: OEM name

        Returns:
            List of partner nodes
        """
        return [node for node in self.nodes.values() if node.oem == oem]

    def get_partners_by_tier(self, tier: str) -> List[PartnerNode]:
        """Get all partners in a specific tier.

        Args:
            tier: Tier name (gold, silver, bronze)

        Returns:
            List of partner nodes
        """
        return [node for node in self.nodes.values() if node.tier.lower() == tier.lower()]

    def get_oem_distribution(self) -> Dict[str, int]:
        """Get distribution of partners across OEMs.

        Returns:
            Dictionary mapping OEM to partner count
        """
        distribution: Dict[str, int] = {}
        for node in self.nodes.values():
            distribution[node.oem] = distribution.get(node.oem, 0) + 1
        return distribution

    def get_tier_distribution(self) -> Dict[str, int]:
        """Get distribution of partners across tiers.

        Returns:
            Dictionary mapping tier to partner count
        """
        distribution: Dict[str, int] = {}
        for node in self.nodes.values():
            tier = node.tier.lower()
            distribution[tier] = distribution.get(tier, 0) + 1
        return distribution

    def get_connected_components(self) -> List[Set[str]]:
        """Find all connected components in the graph.

        Returns:
            List of sets, each containing partner names in a component
        """
        visited: Set[str] = set()
        components: List[Set[str]] = []

        def dfs(node: str, component: Set[str]):
            visited.add(node)
            component.add(node)
            for neighbor in self.get_neighbors(node):
                if neighbor not in visited:
                    dfs(neighbor, component)

        for node_name in self.nodes:
            if node_name not in visited:
                component: Set[str] = set()
                dfs(node_name, component)
                components.append(component)

        return components

    def to_adjacency_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export graph as adjacency list with metadata.

        Returns:
            Dictionary mapping node name to list of adjacent nodes with metadata
        """
        adj_list: Dict[str, List[Dict[str, Any]]] = {}

        for node_name in self.nodes:
            adj_list[node_name] = []

            for edge in self.edges:
                if edge.source == node_name:
                    adj_list[node_name].append(
                        {
                            "target": edge.target,
                            "type": edge.relationship_type,
                            "weight": edge.weight,
                        }
                    )

        return adj_list

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation.

        Returns:
            Complete graph structure as dictionary
        """
        return {
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "adjacency_list": self.to_adjacency_list(),
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "oem_distribution": self.get_oem_distribution(),
                "tier_distribution": self.get_tier_distribution(),
                "components": len(self.get_connected_components()),
            },
            "created_at": self.created_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert graph to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)


def build_partner_graph(partner_records: List[Dict[str, Any]]) -> PartnerGraph:
    """Build a partner graph from partner tier records.

    Args:
        partner_records: List of partner tier dictionaries

    Returns:
        Constructed PartnerGraph
    """
    graph = PartnerGraph()

    # Add all partners as nodes
    for record in partner_records:
        node = PartnerNode(
            name=record["name"],
            tier=record["tier"],
            oem=record["oem"],
            program=record["program"],
            poc=record.get("poc"),
            notes=record.get("notes"),
            metadata={
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at"),
            },
        )
        graph.add_node(node)

    # Build partner-to-OEM edges
    for record in partner_records:
        edge = PartnerRelationship(
            source=record["name"],
            target=record["oem"],
            relationship_type="partner_oem",
            weight=1.0,
        )
        graph.add_edge(edge)

    # Build partner-to-partner edges (same OEM)
    oem_partners: Dict[str, List[str]] = {}
    for record in partner_records:
        oem = record["oem"]
        if oem not in oem_partners:
            oem_partners[oem] = []
        oem_partners[oem].append(record["name"])

    for oem, partners in oem_partners.items():
        for i, p1 in enumerate(partners):
            for p2 in partners[i + 1 :]:
                edge = PartnerRelationship(
                    source=p1,
                    target=p2,
                    relationship_type="partner_partner",
                    weight=0.5,
                    metadata={"common_oem": oem},
                )
                graph.add_edge(edge)

    # Build same-program edges
    program_partners: Dict[str, List[str]] = {}
    for record in partner_records:
        program = record["program"]
        if program not in program_partners:
            program_partners[program] = []
        program_partners[program].append(record["name"])

    for program, partners in program_partners.items():
        if len(partners) > 1:
            for i, p1 in enumerate(partners):
                for p2 in partners[i + 1 :]:
                    # Only add if not already connected
                    existing = any(e.source == p1 and e.target == p2 or e.source == p2 and e.target == p1 for e in graph.edges)
                    if not existing:
                        edge = PartnerRelationship(
                            source=p1,
                            target=p2,
                            relationship_type="same_program",
                            weight=0.3,
                            metadata={"common_program": program},
                        )
                        graph.add_edge(edge)

    logger.info(f"Built partner graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    return graph
