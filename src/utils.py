"""Shared utilities for Agent Memory MCP System."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib


def setup_logging(
    name: str = "agent_memory_mcp",
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """Set up logging with console and optional file output."""

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if path provided)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)

    return logger


def generate_id(prefix: str = "item") -> str:
    """Generate a unique ID with timestamp-based hash."""
    timestamp = datetime.now().isoformat()
    hash_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"{prefix}-{hash_part}"


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string."""
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """Safely get nested dictionary values."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current


def merge_dicts(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def validate_metadata(metadata: Dict) -> Dict:
    """Validate and clean metadata for ChromaDB storage."""
    if not metadata:
        return {}

    cleaned = {}
    for key, value in metadata.items():
        # ChromaDB only supports str, int, float, bool
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        elif value is None:
            cleaned[key] = ""
        elif isinstance(value, list):
            # Convert lists to comma-separated strings
            cleaned[key] = ",".join(str(v) for v in value)
        else:
            # Convert other types to string
            cleaned[key] = str(value)

    return cleaned


def extract_tags_from_content(content: str) -> List[str]:
    """Extract potential tags from content (hashtags or bracketed terms)."""
    import re

    tags = []

    # Find hashtags
    hashtags = re.findall(r"#(\w+)", content)
    tags.extend(hashtags)

    # Find bracketed terms like [tag]
    bracketed = re.findall(r"\[(\w+)\]", content)
    tags.extend(bracketed)

    # Remove duplicates and normalize
    return list(set(tag.lower() for tag in tags))


def format_memory_result(result: Dict) -> str:
    """Format a memory search result for display."""
    lines = []

    content = result.get("content", "")
    metadata = result.get("metadata", {})
    score = result.get("score", 0)

    # Truncate content for display
    display_content = truncate_text(content, 200)

    lines.append(f"Content: {display_content}")

    if category := metadata.get("category"):
        lines.append(f"Category: {category}")

    if tags := metadata.get("tags"):
        lines.append(f"Tags: {tags}")

    lines.append(f"Relevance: {score:.2f}")

    return "\n".join(lines)
