#!/usr/bin/env python3
"""
SessionStart hook that injects memory context from ChromaDB.
This runs automatically when an agent session starts.
Compatible with Claude Code and other MCP-compatible agents.
"""
import json
import sys
import os
from pathlib import Path

def get_memory_context():
    """Query ChromaDB for recent context to inject."""
    try:
        # Add src to path for imports
        # Support both Claude Code env var and generic fallback
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("AGENT_PROJECT_DIR") or os.getcwd()

        # Try to import from installed package first, then from src
        try:
            from src.config import get_config
            from src.chromadb_manager import ChromaDBManager
        except ImportError:
            # Add project to path if not installed
            sys.path.insert(0, project_dir)
            from src.config import get_config
            from src.chromadb_manager import ChromaDBManager

        # Check if local storage exists
        local_memory = Path(project_dir) / ".agent-memory"
        if os.environ.get("AGENT_MEMORY_LOCAL") or local_memory.exists():
            os.environ["AGENT_MEMORY_LOCAL"] = "1"

        config = get_config()

        # Check if ChromaDB exists for this project
        if not config.chromadb_path.exists():
            return None

        db = ChromaDBManager(config)

        # Build context from recent items
        context_parts = []

        # Get recent conversations (last 2, summarized)
        conversations = db.get_recent(category="conversation", limit=2, summarize=True, summary_length=300)
        if conversations:
            context_parts.append("## Recent Sessions")
            for conv in conversations:
                meta = conv.get("metadata", {})
                date = meta.get("created_at", "")[:10] if meta.get("created_at") else "Unknown"
                context_parts.append(f"- [{date}] {conv.get('content', '')}")

        # Get recent decisions (last 3)
        decisions = db.search_memory(
            "decision",
            n_results=3,
            filter_metadata={"category": "decision"},
            summarize=True,
            summary_length=150
        )
        if decisions:
            context_parts.append("\n## Recent Decisions")
            for dec in decisions:
                context_parts.append(f"- {dec.get('content', '')}")

        # Get open tasks (top 3 by priority)
        tasks = db.get_by_metadata({"$and": [{"category": "task"}, {"status": "open"}]}, limit=5)
        if tasks:
            # Sort by priority
            tasks.sort(key=lambda x: x.get("metadata", {}).get("priority", 99))
            context_parts.append("\n## Open Tasks")
            for task in tasks[:3]:
                meta = task.get("metadata", {})
                title = meta.get("title", "Untitled")
                priority = meta.get("priority", 2)
                context_parts.append(f"- [P{priority}] {title}")

        if context_parts:
            return "\n".join(context_parts)

        return None

    except Exception as e:
        # Silently fail - don't break session start
        return f"(Memory context unavailable: {e})"

def main():
    # Read hook input
    try:
        input_data = json.load(sys.stdin)
    except:
        input_data = {}

    # Get memory context
    context = get_memory_context()

    if context:
        print("<memory-context>")
        print("# Project Memory Context")
        print(f"*Auto-injected from ChromaDB*\n")
        print(context)
        print("</memory-context>")

    sys.exit(0)

if __name__ == "__main__":
    main()
