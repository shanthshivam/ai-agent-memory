"""Agent Memory MCP - Unified memory system with ChromaDB, Tasks, and Architecture Graph."""

__version__ = "1.0.0"
__author__ = "Zeronsec"

from .chromadb_manager import ChromaDBManager, get_chromadb_manager
from .task_manager import TaskManager, get_task_manager
from .graph_manager import GraphManager, get_graph_manager
from .documentation_manager import DocumentationManager, get_documentation_manager
from .config import Config, get_project_id
from .utils import setup_logging

__all__ = [
    "ChromaDBManager",
    "get_chromadb_manager",
    "TaskManager",
    "get_task_manager",
    "GraphManager",
    "get_graph_manager",
    "DocumentationManager",
    "get_documentation_manager",
    "Config",
    "get_project_id",
    "setup_logging",
]
