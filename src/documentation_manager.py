"""Documentation manager for AGENT.md auto-generation."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .chromadb_manager import ChromaDBManager


logger = logging.getLogger(__name__)


# Documentation section types
SECTION_TYPES = [
    "architecture",
    "api",
    "setup",
    "workflow",
    "decisions",
    "troubleshooting",
    "conventions",
    "testing"
]


class DocumentationManager:
    """Manage project documentation with ChromaDB storage."""

    def __init__(self, chromadb_manager: ChromaDBManager):
        self.chromadb = chromadb_manager

    def store_section(
        self,
        section_type: str,
        content: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Store a documentation section.

        Args:
            section_type: Type of section (architecture, api, setup, etc.)
            content: Section content (markdown)
            title: Optional section title
            tags: Optional tags for categorization

        Returns:
            Dict with status
        """
        if section_type not in SECTION_TYPES:
            return {
                "status": "error",
                "message": f"Invalid section_type. Must be one of: {', '.join(SECTION_TYPES)}"
            }

        if not content or not content.strip():
            return {"status": "error", "message": "Content is required"}

        # Build full content
        full_content = ""
        if title:
            full_content = f"# {title}\n\n{content}"
        else:
            full_content = content

        metadata = {
            "category": "documentation",
            "section_type": section_type,
            "title": title or section_type.title(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        if tags:
            metadata["tags"] = ",".join(tags)

        result = self.chromadb.store_memory(full_content, metadata)

        if result.get("status") == "success":
            logger.info(f"Stored documentation section: {section_type}")
            return {
                "status": "stored",
                "section_type": section_type,
                "id": result.get("id")
            }

        return result

    def get_section(
        self,
        section_type: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get documentation sections by type."""
        results = self.chromadb.get_by_metadata(
            {"category": "documentation", "section_type": section_type},
            limit=limit
        )

        sections = []
        for item in results:
            meta = item.get("metadata", {})
            sections.append({
                "id": item.get("id"),
                "title": meta.get("title"),
                "section_type": meta.get("section_type"),
                "content": item.get("content"),
                "tags": meta.get("tags", "").split(",") if meta.get("tags") else [],
                "created_at": meta.get("created_at"),
                "updated_at": meta.get("updated_at")
            })

        return sections

    def search_docs(self, query: str, n_results: int = 10) -> List[Dict]:
        """Semantic search for documentation."""
        results = self.chromadb.search_memory(
            query=query,
            n_results=n_results,
            filter_metadata={"category": "documentation"}
        )

        docs = []
        for result in results:
            meta = result.get("metadata", {})
            docs.append({
                "title": meta.get("title"),
                "section_type": meta.get("section_type"),
                "content": result.get("content"),
                "relevance": result.get("score", 0)
            })

        return docs

    def generate_agent_md(self, output_path: Optional[Path] = None) -> str:
        """
        Generate AGENT.md from stored documentation.

        Args:
            output_path: Optional path to write file

        Returns:
            Generated markdown content
        """
        content = "# Project Documentation\n\n"
        content += f"*Auto-generated from ChromaDB on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        content += "To regenerate: `doc_generate_agent_md()`\n\n"
        content += "---\n\n"

        # Get all documentation sections grouped by type
        for section_type in SECTION_TYPES:
            sections = self.get_section(section_type)

            if sections:
                content += f"## {section_type.title()}\n\n"

                for section in sections:
                    # Add section content
                    section_content = section.get("content", "")

                    # If content starts with a header, use it; otherwise add title
                    if not section_content.strip().startswith("#"):
                        if section.get("title"):
                            content += f"### {section.get('title')}\n\n"

                    content += section_content.strip() + "\n\n"

                content += "---\n\n"

        # Write to file if path provided
        if output_path:
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"Generated AGENT.md at: {output_path}")

        return content

    def import_agent_md(self, file_path: Path) -> Dict:
        """
        Import existing AGENT.md into ChromaDB.

        Args:
            file_path: Path to AGENT.md

        Returns:
            Dict with import results
        """
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {file_path}"}

        content = file_path.read_text(encoding="utf-8")

        # Parse sections from markdown
        sections = self._parse_markdown_sections(content)

        imported = 0
        for section in sections:
            section_type = self._guess_section_type(section["title"])

            result = self.store_section(
                section_type=section_type,
                content=section["content"],
                title=section["title"]
            )

            if result.get("status") == "stored":
                imported += 1

        logger.info(f"Imported {imported} sections from {file_path}")

        return {
            "status": "imported",
            "sections_imported": imported,
            "file": str(file_path)
        }

    def _parse_markdown_sections(self, content: str) -> List[Dict]:
        """Parse markdown into sections by H2 headers."""
        sections = []

        # Split by ## headers
        pattern = r"^## (.+)$"
        parts = re.split(pattern, content, flags=re.MULTILINE)

        # First part is header/intro, skip
        i = 1
        while i < len(parts):
            if i + 1 < len(parts):
                title = parts[i].strip()
                section_content = parts[i + 1].strip()

                if section_content and section_content != "---":
                    sections.append({
                        "title": title,
                        "content": section_content
                    })

            i += 2

        return sections

    def _guess_section_type(self, title: str) -> str:
        """Guess section type from title."""
        title_lower = title.lower()

        if any(word in title_lower for word in ["architect", "design", "structure"]):
            return "architecture"
        elif any(word in title_lower for word in ["api", "endpoint", "route"]):
            return "api"
        elif any(word in title_lower for word in ["setup", "install", "config"]):
            return "setup"
        elif any(word in title_lower for word in ["workflow", "process", "flow"]):
            return "workflow"
        elif any(word in title_lower for word in ["decision", "choice", "why"]):
            return "decisions"
        elif any(word in title_lower for word in ["trouble", "debug", "error", "fix"]):
            return "troubleshooting"
        elif any(word in title_lower for word in ["convention", "standard", "style"]):
            return "conventions"
        elif any(word in title_lower for word in ["test", "spec", "verify"]):
            return "testing"

        return "workflow"  # Default

    def get_all_docs(self) -> List[Dict]:
        """Get all documentation sections."""
        results = self.chromadb.get_by_metadata(
            {"category": "documentation"},
            limit=1000
        )

        docs = []
        for item in results:
            meta = item.get("metadata", {})
            docs.append({
                "id": item.get("id"),
                "title": meta.get("title"),
                "section_type": meta.get("section_type"),
                "created_at": meta.get("created_at")
            })

        return docs

    def delete_section(self, section_id: str) -> Dict:
        """Delete a documentation section."""
        return self.chromadb.delete_by_id(section_id)


class ConversationManager:
    """Manage conversation summaries."""

    def __init__(self, chromadb_manager: ChromaDBManager):
        self.chromadb = chromadb_manager

    def store_conversation(
        self,
        summary: str,
        key_decisions: Optional[List[str]] = None,
        key_changes: Optional[List[str]] = None,
        next_steps: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Store a conversation summary.

        Args:
            summary: Summary of the conversation
            key_decisions: List of key decisions made
            key_changes: List of key changes made
            next_steps: List of next steps
            session_id: Optional session identifier

        Returns:
            Dict with status
        """
        content = f"# Session Summary\n\n"
        content += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        content += f"## Summary\n{summary}\n\n"

        if key_decisions:
            content += "## Key Decisions\n"
            for decision in key_decisions:
                content += f"- {decision}\n"
            content += "\n"

        if key_changes:
            content += "## Key Changes\n"
            for change in key_changes:
                content += f"- {change}\n"
            content += "\n"

        if next_steps:
            content += "## Next Steps\n"
            for step in next_steps:
                content += f"- {step}\n"
            content += "\n"

        metadata = {
            "category": "conversation",
            "session_id": session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "has_decisions": "yes" if key_decisions else "no",
            "has_next_steps": "yes" if next_steps else "no"
        }

        result = self.chromadb.store_memory(content, metadata)

        if result.get("status") == "success":
            logger.info(f"Stored conversation: {metadata['session_id']}")
            return {
                "status": "stored",
                "session_id": metadata["session_id"],
                "id": result.get("id")
            }

        return result

    def search_conversations(self, query: str, n_results: int = 10) -> List[Dict]:
        """Semantic search for conversations."""
        results = self.chromadb.search_memory(
            query=query,
            n_results=n_results,
            filter_metadata={"category": "conversation"}
        )

        conversations = []
        for result in results:
            meta = result.get("metadata", {})
            conversations.append({
                "session_id": meta.get("session_id"),
                "content": result.get("content"),
                "created_at": meta.get("created_at"),
                "relevance": result.get("score", 0)
            })

        return conversations

    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Get recent conversation summaries."""
        results = self.chromadb.get_recent(category="conversation", limit=limit)

        conversations = []
        for item in results:
            meta = item.get("metadata", {})
            conversations.append({
                "session_id": meta.get("session_id"),
                "content": item.get("content"),
                "created_at": meta.get("created_at")
            })

        return conversations


def get_documentation_manager(chromadb_manager: ChromaDBManager) -> DocumentationManager:
    """Factory function."""
    return DocumentationManager(chromadb_manager)


def get_conversation_manager(chromadb_manager: ChromaDBManager) -> ConversationManager:
    """Factory function."""
    return ConversationManager(chromadb_manager)
