"""Architecture graph management using NetworkX + ChromaDB."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
import json
import hashlib

import networkx as nx

from .chromadb_manager import ChromaDBManager


logger = logging.getLogger(__name__)


class GraphManager:
    """Manage architecture graph (APIs, screens, journeys, components)."""

    # Node types
    NODE_TYPES = ["api", "screen", "journey", "component", "service", "database", "queue", "event", "model"]

    # Relationship types
    EDGE_TYPES = ["calls", "uses", "depends_on", "part_of", "triggers", "reads", "writes", "emits", "consumes"]

    def __init__(self, chromadb_manager: ChromaDBManager):
        self.chromadb = chromadb_manager
        self.graph = nx.DiGraph()  # Directed graph

        # Load existing graph from ChromaDB
        self._load_graph()

    def _load_graph(self):
        """Load graph from ChromaDB on initialization."""
        # Load nodes
        node_results = self.chromadb.get_by_metadata(
            {"category": "graph_node"},
            limit=10000
        )

        for item in node_results:
            meta = item.get("metadata", {})
            node_id = meta.get("node_id")

            if node_id:
                properties = {}
                if meta.get("properties"):
                    try:
                        properties = json.loads(meta.get("properties", "{}"))
                    except json.JSONDecodeError:
                        properties = {}

                self.graph.add_node(
                    node_id,
                    node_type=meta.get("node_type"),
                    name=meta.get("name"),
                    properties=properties,
                    created_at=meta.get("created_at")
                )

        # Load edges
        edge_results = self.chromadb.get_by_metadata(
            {"category": "graph_edge"},
            limit=10000
        )

        for item in edge_results:
            meta = item.get("metadata", {})
            from_id = meta.get("from_node")
            to_id = meta.get("to_node")

            if from_id and to_id and self.graph.has_node(from_id) and self.graph.has_node(to_id):
                properties = {}
                if meta.get("properties"):
                    try:
                        properties = json.loads(meta.get("properties", "{}"))
                    except json.JSONDecodeError:
                        properties = {}

                self.graph.add_edge(
                    from_id,
                    to_id,
                    relationship=meta.get("relationship"),
                    properties=properties,
                    created_at=meta.get("created_at")
                )

        logger.info(
            f"Loaded graph: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

    def add_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        properties: Optional[Dict] = None
    ) -> Dict:
        """
        Add a node to the graph.

        Args:
            node_id: Unique identifier (e.g., "api-create-invoice")
            node_type: Type (api, screen, journey, component, service, database, queue)
            name: Display name
            properties: Additional properties

        Returns:
            Dict with status
        """
        if not node_id or not node_id.strip():
            return {"status": "error", "message": "node_id is required"}

        if node_type not in self.NODE_TYPES:
            return {
                "status": "error",
                "message": f"Invalid node_type. Must be one of: {', '.join(self.NODE_TYPES)}"
            }

        # Check if already exists
        if self.graph.has_node(node_id):
            return {"status": "error", "message": f"Node '{node_id}' already exists"}

        props = properties or {}

        # Add to NetworkX graph
        self.graph.add_node(
            node_id,
            node_type=node_type,
            name=name,
            properties=props,
            created_at=datetime.now().isoformat()
        )

        # Store in ChromaDB for persistence and search
        content = f"# {node_type.upper()}: {name}\n\n"
        content += f"**ID:** {node_id}\n"
        content += f"**Type:** {node_type}\n\n"

        if props:
            content += "## Properties\n"
            for key, value in props.items():
                content += f"- **{key}:** {value}\n"

        metadata = {
            "category": "graph_node",
            "node_id": node_id,
            "node_type": node_type,
            "name": name,
            "properties": json.dumps(props),
            "created_at": datetime.now().isoformat()
        }

        self.chromadb.store_memory(content, metadata, custom_id=f"node-{node_id}")

        logger.info(f"Added node: {node_id} ({node_type})")

        return {
            "status": "created",
            "node_id": node_id,
            "node_type": node_type,
            "name": name
        }

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        relationship: str,
        properties: Optional[Dict] = None
    ) -> Dict:
        """
        Add an edge (relationship) between nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relationship: Relationship type (calls, uses, depends_on, etc.)
            properties: Additional properties

        Returns:
            Dict with status
        """
        if relationship not in self.EDGE_TYPES:
            return {
                "status": "error",
                "message": f"Invalid relationship. Must be one of: {', '.join(self.EDGE_TYPES)}"
            }

        if not self.graph.has_node(from_id):
            return {"status": "error", "message": f"Source node '{from_id}' not found"}

        if not self.graph.has_node(to_id):
            return {"status": "error", "message": f"Target node '{to_id}' not found"}

        props = properties or {}

        # Add to NetworkX graph
        self.graph.add_edge(
            from_id,
            to_id,
            relationship=relationship,
            properties=props,
            created_at=datetime.now().isoformat()
        )

        # Store in ChromaDB
        from_node = self.graph.nodes[from_id]
        to_node = self.graph.nodes[to_id]

        content = f"# Relationship: {from_node['name']} -> {to_node['name']}\n\n"
        content += f"**From:** {from_id} ({from_node['node_type']})\n"
        content += f"**To:** {to_id} ({to_node['node_type']})\n"
        content += f"**Relationship:** {relationship}\n\n"

        if props:
            content += "## Properties\n"
            for key, value in props.items():
                content += f"- **{key}:** {value}\n"

        edge_id = f"edge-{from_id}-{to_id}-{relationship}"
        metadata = {
            "category": "graph_edge",
            "from_node": from_id,
            "to_node": to_id,
            "relationship": relationship,
            "properties": json.dumps(props),
            "created_at": datetime.now().isoformat()
        }

        self.chromadb.store_memory(content, metadata, custom_id=edge_id)

        logger.info(f"Added edge: {from_id} --{relationship}--> {to_id}")

        return {
            "status": "created",
            "from": from_id,
            "to": to_id,
            "relationship": relationship
        }

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node details."""
        if not self.graph.has_node(node_id):
            return None

        node_data = self.graph.nodes[node_id]
        return {
            "node_id": node_id,
            "node_type": node_data.get("node_type"),
            "name": node_data.get("name"),
            "properties": node_data.get("properties", {}),
            "created_at": node_data.get("created_at")
        }

    def list_nodes(
        self,
        node_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """List nodes, optionally filtered by type."""
        nodes = []

        for node_id, data in self.graph.nodes(data=True):
            if node_type and data.get("node_type") != node_type:
                continue

            nodes.append({
                "node_id": node_id,
                "node_type": data.get("node_type"),
                "name": data.get("name"),
                "connections": self.graph.degree(node_id)
            })

        return nodes[:limit]

    def delete_node(self, node_id: str) -> Dict:
        """Delete a node and its edges."""
        if not self.graph.has_node(node_id):
            return {"status": "error", "message": "Node not found"}

        # Get connected edges before deletion
        in_edges = list(self.graph.in_edges(node_id))
        out_edges = list(self.graph.out_edges(node_id))

        # Remove from NetworkX
        self.graph.remove_node(node_id)

        # Remove from ChromaDB
        self.chromadb.delete_by_id(f"node-{node_id}")

        # Remove edges from ChromaDB
        for from_id, _ in in_edges:
            for rel in self.EDGE_TYPES:
                self.chromadb.delete_by_id(f"edge-{from_id}-{node_id}-{rel}")

        for _, to_id in out_edges:
            for rel in self.EDGE_TYPES:
                self.chromadb.delete_by_id(f"edge-{node_id}-{to_id}-{rel}")

        logger.info(f"Deleted node: {node_id}")

        return {
            "status": "deleted",
            "node_id": node_id,
            "edges_removed": len(in_edges) + len(out_edges)
        }

    def query_relationships(
        self,
        node_id: str,
        direction: str = "both",
        relationship: Optional[str] = None
    ) -> Dict:
        """
        Query relationships for a node.

        Args:
            node_id: Node to query
            direction: "incoming", "outgoing", or "both"
            relationship: Filter by relationship type

        Returns:
            Dict with node info and relationships
        """
        if not self.graph.has_node(node_id):
            return {"status": "error", "message": "Node not found"}

        node = self.graph.nodes[node_id]

        outgoing = []
        incoming = []

        # Outgoing edges (this node -> others)
        if direction in ["outgoing", "both"]:
            for _, to_id, data in self.graph.out_edges(node_id, data=True):
                if relationship is None or data.get("relationship") == relationship:
                    to_node = self.graph.nodes[to_id]
                    outgoing.append({
                        "to_id": to_id,
                        "to_name": to_node.get("name"),
                        "to_type": to_node.get("node_type"),
                        "relationship": data.get("relationship"),
                        "properties": data.get("properties", {})
                    })

        # Incoming edges (others -> this node)
        if direction in ["incoming", "both"]:
            for from_id, _, data in self.graph.in_edges(node_id, data=True):
                if relationship is None or data.get("relationship") == relationship:
                    from_node = self.graph.nodes[from_id]
                    incoming.append({
                        "from_id": from_id,
                        "from_name": from_node.get("name"),
                        "from_type": from_node.get("node_type"),
                        "relationship": data.get("relationship"),
                        "properties": data.get("properties", {})
                    })

        return {
            "node_id": node_id,
            "node_name": node.get("name"),
            "node_type": node.get("node_type"),
            "outgoing": outgoing,
            "incoming": incoming,
            "total_connections": len(outgoing) + len(incoming)
        }

    def analyze_impact(self, node_id: str) -> Dict:
        """
        Analyze impact of changing a node.

        Args:
            node_id: Node to analyze

        Returns:
            Dict with impact analysis
        """
        if not self.graph.has_node(node_id):
            return {"status": "error", "message": "Node not found"}

        node = self.graph.nodes[node_id]

        # Find all descendants (what depends on this transitively)
        try:
            descendants = nx.descendants(self.graph, node_id)
        except nx.NetworkXError:
            descendants = set()

        # Find all ancestors (what this depends on transitively)
        try:
            ancestors = nx.ancestors(self.graph, node_id)
        except nx.NetworkXError:
            ancestors = set()

        # Direct dependents (nodes that directly reference this)
        direct_dependents = list(self.graph.predecessors(node_id))

        # Group impacted by type
        impacted_by_type = {}
        for desc_id in descendants:
            desc_node = self.graph.nodes[desc_id]
            node_type = desc_node.get("node_type", "unknown")
            if node_type not in impacted_by_type:
                impacted_by_type[node_type] = []
            impacted_by_type[node_type].append({
                "id": desc_id,
                "name": desc_node.get("name")
            })

        # Risk assessment
        total_impacted = len(descendants)
        if total_impacted > 10:
            risk_level = "high"
        elif total_impacted > 3:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "node_id": node_id,
            "node_name": node.get("name"),
            "node_type": node.get("node_type"),
            "direct_dependents": len(direct_dependents),
            "total_impacted": total_impacted,
            "dependencies": len(ancestors),
            "impacted_by_type": impacted_by_type,
            "risk_level": risk_level,
            "recommendation": self._get_impact_recommendation(risk_level, total_impacted)
        }

    def _get_impact_recommendation(self, risk_level: str, impacted_count: int) -> str:
        """Get recommendation based on impact analysis."""
        if risk_level == "high":
            return f"HIGH RISK: {impacted_count} components affected. Consider phased rollout and extensive testing."
        elif risk_level == "medium":
            return f"MEDIUM RISK: {impacted_count} components affected. Test thoroughly before deployment."
        else:
            return f"LOW RISK: {impacted_count} components affected. Standard testing recommended."

    def find_path(self, from_id: str, to_id: str) -> Dict:
        """
        Find shortest path between two nodes.

        Args:
            from_id: Source node
            to_id: Target node

        Returns:
            Dict with path details
        """
        if not self.graph.has_node(from_id):
            return {"status": "error", "message": f"Source node '{from_id}' not found"}

        if not self.graph.has_node(to_id):
            return {"status": "error", "message": f"Target node '{to_id}' not found"}

        try:
            path = nx.shortest_path(self.graph, from_id, to_id)

            # Build path with details
            path_details = []
            for i in range(len(path) - 1):
                current = path[i]
                next_node = path[i + 1]

                edge_data = self.graph.get_edge_data(current, next_node)
                current_node = self.graph.nodes[current]

                path_details.append({
                    "node_id": current,
                    "node_name": current_node.get("name"),
                    "node_type": current_node.get("node_type"),
                    "relationship": edge_data.get("relationship") if edge_data else None
                })

            # Add final node
            final_node = self.graph.nodes[to_id]
            path_details.append({
                "node_id": to_id,
                "node_name": final_node.get("name"),
                "node_type": final_node.get("node_type"),
                "relationship": None
            })

            return {
                "status": "found",
                "path_length": len(path) - 1,
                "path": path_details
            }

        except nx.NetworkXNoPath:
            return {
                "status": "not_found",
                "message": f"No path exists between {from_id} and {to_id}"
            }

    def find_orphans(self) -> List[Dict]:
        """Find nodes with no connections."""
        orphans = []

        for node_id in self.graph.nodes():
            if self.graph.degree(node_id) == 0:
                node = self.graph.nodes[node_id]
                orphans.append({
                    "node_id": node_id,
                    "node_name": node.get("name"),
                    "node_type": node.get("node_type")
                })

        return orphans

    def generate_mermaid(self, node_ids: Optional[List[str]] = None) -> str:
        """
        Generate Mermaid diagram for graph visualization.

        Args:
            node_ids: Specific nodes to include (None = all)

        Returns:
            Mermaid diagram string
        """
        if node_ids is None:
            subgraph = self.graph
        else:
            # Get subgraph with specified nodes
            valid_ids = [nid for nid in node_ids if self.graph.has_node(nid)]
            subgraph = self.graph.subgraph(valid_ids)

        mermaid = "graph TD\n"

        # Add nodes with styling
        for node_id, data in subgraph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            name = data.get("name", node_id)
            # Sanitize name for Mermaid
            safe_name = name.replace('"', "'").replace("[", "(").replace("]", ")")

            # Style by type
            if node_type == "api":
                mermaid += f'    {node_id}["{safe_name}"]:::api\n'
            elif node_type == "screen":
                mermaid += f'    {node_id}("{safe_name}"):::screen\n'
            elif node_type == "database":
                mermaid += f'    {node_id}[("{safe_name}")]:::database\n'
            elif node_type == "service":
                mermaid += f'    {node_id}[["{safe_name}"]]:::service\n'
            elif node_type == "queue":
                mermaid += f'    {node_id}>{safe_name}]:::queue\n'
            else:
                mermaid += f'    {node_id}["{safe_name}"]\n'

        mermaid += "\n"

        # Add edges
        for from_id, to_id, data in subgraph.edges(data=True):
            relationship = data.get("relationship", "")
            mermaid += f"    {from_id} -->|{relationship}| {to_id}\n"

        # Add styling
        mermaid += "\n"
        mermaid += "    classDef api fill:#e1f5ff,stroke:#01579b,color:#01579b\n"
        mermaid += "    classDef screen fill:#f3e5f5,stroke:#4a148c,color:#4a148c\n"
        mermaid += "    classDef database fill:#e8f5e9,stroke:#1b5e20,color:#1b5e20\n"
        mermaid += "    classDef service fill:#fff3e0,stroke:#e65100,color:#e65100\n"
        mermaid += "    classDef queue fill:#fce4ec,stroke:#880e4f,color:#880e4f\n"

        return mermaid

    def export_architecture(self) -> str:
        """Export graph as ARCHITECTURE.md content."""
        content = "# Architecture Map\n\n"
        content += f"*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"

        stats = self.get_stats()
        content += "## Overview\n\n"
        content += f"- **Total Nodes:** {stats['total_nodes']}\n"
        content += f"- **Total Relationships:** {stats['total_edges']}\n\n"

        # Group by type
        for node_type in self.NODE_TYPES:
            nodes = self.list_nodes(node_type=node_type)
            if nodes:
                content += f"## {node_type.title()}s\n\n"
                for node in nodes:
                    content += f"### {node['name']}\n"
                    content += f"- **ID:** `{node['node_id']}`\n"
                    content += f"- **Connections:** {node['connections']}\n"

                    # Get relationships
                    rels = self.query_relationships(node['node_id'])
                    if rels.get("outgoing"):
                        content += "- **Outgoing:**\n"
                        for rel in rels["outgoing"]:
                            content += f"  - {rel['relationship']} -> {rel['to_name']}\n"
                    if rels.get("incoming"):
                        content += "- **Incoming:**\n"
                        for rel in rels["incoming"]:
                            content += f"  - {rel['from_name']} -> {rel['relationship']}\n"
                    content += "\n"

        # Add Mermaid diagram
        content += "## Visual Diagram\n\n"
        content += "```mermaid\n"
        content += self.generate_mermaid()
        content += "```\n"

        return content

    def search_nodes(self, query: str, n_results: int = 10) -> List[Dict]:
        """Semantic search for nodes."""
        results = self.chromadb.search_memory(
            query=query,
            n_results=n_results,
            filter_metadata={"category": "graph_node"}
        )

        nodes = []
        for result in results:
            meta = result.get("metadata", {})
            nodes.append({
                "node_id": meta.get("node_id"),
                "node_type": meta.get("node_type"),
                "name": meta.get("name"),
                "relevance": result.get("score", 0)
            })

        return nodes

    def get_stats(self) -> Dict:
        """Get graph statistics."""
        nodes_by_type = {}
        for node_type in self.NODE_TYPES:
            nodes_by_type[node_type] = len([
                n for n, d in self.graph.nodes(data=True)
                if d.get("node_type") == node_type
            ])

        edges_by_rel = {}
        for rel_type in self.EDGE_TYPES:
            edges_by_rel[rel_type] = len([
                1 for _, _, d in self.graph.edges(data=True)
                if d.get("relationship") == rel_type
            ])

        orphaned = len([n for n in self.graph.nodes() if self.graph.degree(n) == 0])

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "nodes_by_type": nodes_by_type,
            "edges_by_relationship": edges_by_rel,
            "orphaned_nodes": orphaned,
            "most_connected": self._get_most_connected(5)
        }

    def _get_most_connected(self, limit: int = 5) -> List[Dict]:
        """Get most connected nodes."""
        degree_dict = dict(self.graph.degree())
        sorted_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {
                "node_id": node_id,
                "node_name": self.graph.nodes[node_id].get("name", node_id),
                "connections": degree
            }
            for node_id, degree in sorted_nodes
            if degree > 0
        ]


def get_graph_manager(chromadb_manager: ChromaDBManager) -> GraphManager:
    """Factory function."""
    return GraphManager(chromadb_manager)
