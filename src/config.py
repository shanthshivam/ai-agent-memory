"""Configuration for Agent Memory MCP System (Windows-compatible)."""

import os
import subprocess
from pathlib import Path
from typing import Optional


class Config:
    """Configuration settings for the memory system."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or get_project_id()

        # Base directories
        self.home_dir = Path.home()
        self.config_base = self.home_dir / ".agent-memory-mcp"

        # ChromaDB path: Check for project-local storage first
        # Priority: AGENT_MEMORY_PATH env var > .agent-memory in project > ~/.agent-chromadb
        if env_path := os.environ.get("AGENT_MEMORY_PATH"):
            self.chromadb_base = Path(env_path)
            self.chromadb_path = self.chromadb_base
        elif (local_memory := Path.cwd() / ".agent-memory").exists() or os.environ.get("AGENT_MEMORY_LOCAL"):
            self.chromadb_base = Path.cwd() / ".agent-memory"
            self.chromadb_path = self.chromadb_base
        else:
            self.chromadb_base = self.home_dir / ".agent-chromadb"
            self.chromadb_path = self.chromadb_base / self.project_id

        # Ensure directories exist
        self.chromadb_path.mkdir(parents=True, exist_ok=True)
        self.config_base.mkdir(parents=True, exist_ok=True)
        (self.config_base / "logs").mkdir(exist_ok=True)
        (self.config_base / "config").mkdir(exist_ok=True)

        # Collection name for ChromaDB
        self.collection_name = f"{self.project_id}_unified"

        # Embedding model
        self.embedding_model = "all-MiniLM-L6-v2"

        # Logging
        self.log_file = self.config_base / "logs" / f"{self.project_id}.log"


def get_project_id() -> str:
    """
    Detect project ID from various sources.

    Priority:
    1. AGENT_PROJECT_ID environment variable
    2. .agent-project file in current directory
    3. Git repository name
    4. Current folder name
    """

    # 1. Environment variable
    if env_id := os.environ.get("AGENT_PROJECT_ID"):
        return sanitize_project_id(env_id)

    cwd = Path.cwd()

    # 2. .agent-project file
    project_file = cwd / ".agent-project"
    if project_file.exists():
        project_id = project_file.read_text().strip()
        if project_id:
            return sanitize_project_id(project_id)

    # 3. Git repository name
    git_name = get_git_repo_name(cwd)
    if git_name:
        return sanitize_project_id(git_name)

    # 4. Current folder name
    return sanitize_project_id(cwd.name)


def get_git_repo_name(path: Path) -> Optional[str]:
    """Get the git repository name if we're in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            repo_path = Path(result.stdout.strip())
            return repo_path.name
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Fallback: check for .git directory
    current = path
    while current != current.parent:
        if (current / ".git").exists():
            return current.name
        current = current.parent

    return None


def sanitize_project_id(name: str) -> str:
    """Sanitize project ID to be safe for filesystem and ChromaDB."""
    # Replace problematic characters
    safe_chars = []
    for char in name.lower():
        if char.isalnum() or char in "-_":
            safe_chars.append(char)
        elif char in " ./\\":
            safe_chars.append("-")

    result = "".join(safe_chars)

    # Remove consecutive dashes
    while "--" in result:
        result = result.replace("--", "-")

    # Trim dashes from ends
    result = result.strip("-")

    # Ensure not empty
    return result or "default-project"


def get_config(project_id: Optional[str] = None) -> Config:
    """Factory function to get configuration."""
    return Config(project_id)
