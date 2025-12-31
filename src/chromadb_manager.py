"""ChromaDB Manager for unified storage (memory, tasks, graph, documentation)."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from .config import Config, get_config
from .utils import generate_id, validate_metadata


logger = logging.getLogger(__name__)


# Default summary length (characters)
DEFAULT_SUMMARY_LENGTH = 200


def summarize_content(content: str, max_length: int = DEFAULT_SUMMARY_LENGTH) -> str:
    """Truncate content to a summary with ellipsis."""
    if not content:
        return ""
    content = content.strip()
    if len(content) <= max_length:
        return content
    # Try to break at word boundary
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:  # Only break at word if reasonable
        truncated = truncated[:last_space]
    return truncated.rstrip() + "..."


# Supported categories
CATEGORIES = [
    "memory",       # General knowledge and decisions
    "task",         # Task tracking
    "graph_node",   # Graph entities (APIs, screens, etc.)
    "graph_edge",   # Graph relationships
    "documentation", # Documentation sections
    "conversation"  # Session summaries
]


class ChromaDBManager:
    """Unified ChromaDB storage for all memory types."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize ChromaDB manager with project isolation."""
        self.config = config or get_config()

        # Ensure storage directory exists
        self.config.chromadb_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.config.chromadb_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create unified collection
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"description": "Unified memory collection for Agent Memory MCP"}
        )

        logger.info(
            f"ChromaDB initialized for project '{self.config.project_id}' "
            f"at {self.config.chromadb_path}"
        )

    def store_memory(
        self,
        content: str,
        metadata: Optional[Dict] = None,
        custom_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store content in ChromaDB.

        Args:
            content: The content to store
            metadata: Optional metadata (must include 'category')
            custom_id: Optional custom ID (auto-generated if not provided)

        Returns:
            Dict with id and status
        """
        if not content or not content.strip():
            return {"status": "error", "message": "Content cannot be empty"}

        # Prepare metadata
        meta = metadata.copy() if metadata else {}
        meta["created_at"] = datetime.now().isoformat()
        meta["project_id"] = self.config.project_id

        # Ensure category is set
        if "category" not in meta:
            meta["category"] = "memory"

        # Validate and clean metadata
        meta = validate_metadata(meta)

        # Generate ID
        item_id = custom_id or generate_id(meta.get("category", "item"))

        try:
            self.collection.add(
                documents=[content],
                metadatas=[meta],
                ids=[item_id]
            )

            logger.info(f"Stored item: {item_id} (category: {meta.get('category')})")

            return {
                "status": "success",
                "id": item_id,
                "category": meta.get("category")
            }

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return {"status": "error", "message": str(e)}

    def search_memory(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
        summarize: bool = True,
        summary_length: int = DEFAULT_SUMMARY_LENGTH
    ) -> List[Dict[str, Any]]:
        """
        Search memory using semantic similarity.

        Args:
            query: Search query
            n_results: Maximum number of results (default 5 to save context)
            filter_metadata: Optional metadata filters
            summarize: If True, truncate content to save context (default True)
            summary_length: Max characters for summarized content

        Returns:
            List of matching documents with metadata and scores
        """
        if not query or not query.strip():
            return []

        try:
            # Build where clause
            where = filter_metadata if filter_metadata else None

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            formatted = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0

                    # Convert distance to similarity score (0-1)
                    score = 1 / (1 + distance)

                    # Summarize content if requested
                    content = summarize_content(doc, summary_length) if summarize else doc

                    formatted.append({
                        "id": results["ids"][0][i] if results.get("ids") else None,
                        "content": content,
                        "full_content_length": len(doc),
                        "metadata": metadata,
                        "score": score
                    })

            logger.debug(f"Search found {len(formatted)} results for: {query[:50]}...")
            return formatted

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_by_metadata(
        self,
        filter_metadata: Dict,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get items by metadata filter (non-semantic).

        Args:
            filter_metadata: Metadata filters
            limit: Maximum results

        Returns:
            List of matching documents
        """
        try:
            results = self.collection.get(
                where=filter_metadata,
                limit=limit,
                include=["documents", "metadatas"]
            )

            formatted = []
            for i, doc in enumerate(results["documents"]):
                formatted.append({
                    "id": results["ids"][i],
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })

            return formatted

        except Exception as e:
            logger.error(f"Get by metadata failed: {e}")
            return []

    def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a single item by ID."""
        try:
            results = self.collection.get(
                ids=[item_id],
                include=["documents", "metadatas"]
            )

            if results["documents"]:
                return {
                    "id": item_id,
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0] if results["metadatas"] else {}
                }

            return None

        except Exception as e:
            logger.error(f"Get by ID failed: {e}")
            return None

    def update_by_id(
        self,
        item_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Update an existing item."""
        try:
            # Get existing item first
            existing = self.get_by_id(item_id)
            if not existing:
                return {"status": "error", "message": "Item not found"}

            # Merge metadata
            new_meta = existing["metadata"].copy()
            if metadata:
                new_meta.update(metadata)
            new_meta["updated_at"] = datetime.now().isoformat()
            new_meta = validate_metadata(new_meta)

            # Update content if provided
            new_content = content if content else existing["content"]

            self.collection.update(
                ids=[item_id],
                documents=[new_content],
                metadatas=[new_meta]
            )

            logger.info(f"Updated item: {item_id}")
            return {"status": "updated", "id": item_id}

        except Exception as e:
            logger.error(f"Update failed: {e}")
            return {"status": "error", "message": str(e)}

    def delete_by_id(self, item_id: str) -> Dict[str, Any]:
        """Delete an item by ID."""
        try:
            self.collection.delete(ids=[item_id])
            logger.info(f"Deleted item: {item_id}")
            return {"status": "deleted", "id": item_id}

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return {"status": "error", "message": str(e)}

    def delete_by_metadata(self, filter_metadata: Dict) -> Dict[str, Any]:
        """Delete items matching metadata filter."""
        try:
            self.collection.delete(where=filter_metadata)
            logger.info(f"Deleted items matching: {filter_metadata}")
            return {"status": "deleted", "filter": filter_metadata}

        except Exception as e:
            logger.error(f"Delete by metadata failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        try:
            total_count = self.collection.count()

            # Count by category
            category_counts = {}
            for category in CATEGORIES:
                try:
                    results = self.collection.get(
                        where={"category": category},
                        limit=1,
                        include=[]
                    )
                    # This is a hack - get doesn't return count, so we need to query all
                    all_results = self.collection.get(
                        where={"category": category},
                        limit=10000,
                        include=[]
                    )
                    category_counts[category] = len(all_results["ids"])
                except Exception:
                    category_counts[category] = 0

            return {
                "project_id": self.config.project_id,
                "total_items": total_count,
                "by_category": category_counts,
                "storage_path": str(self.config.chromadb_path)
            }

        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_recent(
        self,
        category: Optional[str] = None,
        limit: int = 5,
        summarize: bool = True,
        summary_length: int = DEFAULT_SUMMARY_LENGTH
    ) -> List[Dict[str, Any]]:
        """Get most recent items, optionally filtered by category."""
        try:
            where = {"category": category} if category else None

            results = self.collection.get(
                where=where,
                limit=limit * 2,  # Get more to sort properly
                include=["documents", "metadatas"]
            )

            # Format and sort by created_at
            items = []
            for i, doc in enumerate(results["documents"]):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                content = summarize_content(doc, summary_length) if summarize else doc
                items.append({
                    "id": results["ids"][i],
                    "content": content,
                    "full_content_length": len(doc),
                    "metadata": meta,
                    "created_at": meta.get("created_at", "")
                })

            # Sort by created_at descending
            items.sort(key=lambda x: x["created_at"], reverse=True)

            return items[:limit]

        except Exception as e:
            logger.error(f"Get recent failed: {e}")
            return []


# Factory function
def get_chromadb_manager(project_id: Optional[str] = None) -> ChromaDBManager:
    """Get ChromaDB manager instance."""
    config = get_config(project_id)
    return ChromaDBManager(config)
