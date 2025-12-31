"""MCP Server with 33+ tools for memory, tasks, graph, and documentation."""

import asyncio
import logging
from pathlib import Path
from typing import Any, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .chromadb_manager import ChromaDBManager, get_chromadb_manager
from .task_manager import TaskManager, get_task_manager, TASK_STATUSES, TASK_TYPES
from .graph_manager import GraphManager, get_graph_manager
from .documentation_manager import (
    DocumentationManager,
    ConversationManager,
    get_documentation_manager,
    get_conversation_manager,
    SECTION_TYPES
)
from .config import get_project_id
from .utils import setup_logging


# Setup logging
logger = setup_logging("agent_memory_mcp")

# Initialize server
server = Server("agent-memory-mcp")

# Global managers (initialized on first use)
_chromadb: Optional[ChromaDBManager] = None
_task_manager: Optional[TaskManager] = None
_graph_manager: Optional[GraphManager] = None
_doc_manager: Optional[DocumentationManager] = None
_conv_manager: Optional[ConversationManager] = None


def get_managers():
    """Get or initialize all managers."""
    global _chromadb, _task_manager, _graph_manager, _doc_manager, _conv_manager

    if _chromadb is None:
        _chromadb = get_chromadb_manager()
        _task_manager = get_task_manager(_chromadb)
        _graph_manager = get_graph_manager(_chromadb)
        _doc_manager = get_documentation_manager(_chromadb)
        _conv_manager = get_conversation_manager(_chromadb)

    return _chromadb, _task_manager, _graph_manager, _doc_manager, _conv_manager


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools."""
    return [
        # === MEMORY TOOLS (3) ===
        Tool(
            name="memory_store",
            description="Store information in persistent memory with semantic search capability",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to store"},
                    "category": {"type": "string", "description": "Category (memory, decision, note)", "default": "memory"},
                    "tags": {"type": "string", "description": "Comma-separated tags"}
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="memory_search",
            description="Search memories using semantic similarity. Returns summarized content by default to save context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "n_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                    "category": {"type": "string", "description": "Filter by category"},
                    "full_content": {"type": "boolean", "description": "Return full content instead of summary (default false)", "default": False}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="memory_get_full",
            description="Get full content of a specific memory by ID (use after searching to get complete text)",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "Memory ID from search results"}
                },
                "required": ["memory_id"]
            }
        ),
        Tool(
            name="memory_stats",
            description="Get memory system statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # === TASK TOOLS (10) ===
        Tool(
            name="task_create",
            description="Create a new task",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "priority": {"type": "integer", "description": "Priority 0-4 (0=critical)", "default": 2},
                    "task_type": {"type": "string", "enum": TASK_TYPES, "default": "task"},
                    "assignee": {"type": "string", "description": "Assignee name"},
                    "labels": {"type": "string", "description": "Comma-separated labels"},
                    "graph_node": {"type": "string", "description": "Link to graph node ID"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="task_list",
            description="List tasks with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": TASK_STATUSES},
                    "priority": {"type": "integer", "description": "Filter by priority 0-4"},
                    "assignee": {"type": "string"},
                    "task_type": {"type": "string", "enum": TASK_TYPES},
                    "graph_node": {"type": "string"},
                    "limit": {"type": "integer", "default": 50}
                }
            }
        ),
        Tool(
            name="task_get",
            description="Get task details by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="task_update",
            description="Update task status, priority, or add notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"},
                    "status": {"type": "string", "enum": TASK_STATUSES},
                    "priority": {"type": "integer", "description": "Priority 0-4"},
                    "assignee": {"type": "string"},
                    "notes": {"type": "string", "description": "Notes to append"},
                    "labels": {"type": "string", "description": "Comma-separated labels"}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="task_close",
            description="Close a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"},
                    "reason": {"type": "string", "description": "Reason for closing"}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="task_search",
            description="Semantic search for tasks",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "n_results": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="task_stats",
            description="Get task statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="task_get_open",
            description="Get all open tasks (quick access)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="task_get_my_tasks",
            description="Get tasks assigned to a person",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignee": {"type": "string", "description": "Assignee name"}
                },
                "required": ["assignee"]
            }
        ),
        Tool(
            name="task_get_by_graph_node",
            description="Get tasks linked to a graph node",
            inputSchema={
                "type": "object",
                "properties": {
                    "graph_node": {"type": "string", "description": "Graph node ID"}
                },
                "required": ["graph_node"]
            }
        ),

        # === GRAPH TOOLS (12) ===
        Tool(
            name="graph_add_node",
            description="Add a node to the architecture graph (API, screen, service, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Unique node ID (e.g., api-create-invoice)"},
                    "node_type": {"type": "string", "enum": GraphManager.NODE_TYPES, "description": "Node type"},
                    "name": {"type": "string", "description": "Display name"},
                    "properties": {"type": "object", "description": "Additional properties"}
                },
                "required": ["node_id", "node_type", "name"]
            }
        ),
        Tool(
            name="graph_add_edge",
            description="Add a relationship between nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {"type": "string", "description": "Source node ID"},
                    "to_id": {"type": "string", "description": "Target node ID"},
                    "relationship": {"type": "string", "enum": GraphManager.EDGE_TYPES},
                    "properties": {"type": "object", "description": "Additional properties"}
                },
                "required": ["from_id", "to_id", "relationship"]
            }
        ),
        Tool(
            name="graph_query_relationships",
            description="Query relationships for a node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Node ID"},
                    "direction": {"type": "string", "enum": ["incoming", "outgoing", "both"], "default": "both"},
                    "relationship": {"type": "string", "description": "Filter by relationship type"}
                },
                "required": ["node_id"]
            }
        ),
        Tool(
            name="graph_analyze_impact",
            description="Analyze impact of changing a node (shows all affected components)",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Node ID to analyze"}
                },
                "required": ["node_id"]
            }
        ),
        Tool(
            name="graph_find_path",
            description="Find path between two nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {"type": "string", "description": "Source node ID"},
                    "to_id": {"type": "string", "description": "Target node ID"}
                },
                "required": ["from_id", "to_id"]
            }
        ),
        Tool(
            name="graph_visualize",
            description="Generate Mermaid diagram for visualization",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_ids": {"type": "array", "items": {"type": "string"}, "description": "Specific nodes to include (empty = all)"}
                }
            }
        ),
        Tool(
            name="graph_get_node",
            description="Get node details",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Node ID"}
                },
                "required": ["node_id"]
            }
        ),
        Tool(
            name="graph_list_nodes",
            description="List nodes, optionally by type",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_type": {"type": "string", "enum": GraphManager.NODE_TYPES},
                    "limit": {"type": "integer", "default": 100}
                }
            }
        ),
        Tool(
            name="graph_delete_node",
            description="Delete a node and its edges",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Node ID to delete"}
                },
                "required": ["node_id"]
            }
        ),
        Tool(
            name="graph_stats",
            description="Get graph statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="graph_find_orphans",
            description="Find disconnected nodes",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="graph_export_architecture",
            description="Export graph as ARCHITECTURE.md",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "Output file path (optional)"}
                }
            }
        ),

        # === DOCUMENTATION TOOLS (5) ===
        Tool(
            name="doc_store_section",
            description="Store a documentation section",
            inputSchema={
                "type": "object",
                "properties": {
                    "section_type": {"type": "string", "enum": SECTION_TYPES},
                    "content": {"type": "string", "description": "Section content (markdown)"},
                    "title": {"type": "string", "description": "Section title"},
                    "tags": {"type": "string", "description": "Comma-separated tags"}
                },
                "required": ["section_type", "content"]
            }
        ),
        Tool(
            name="doc_search",
            description="Search documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "n_results": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="doc_generate_agent_md",
            description="Generate AGENT.md from stored documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "Output file path"}
                }
            }
        ),
        Tool(
            name="doc_import_agent_md",
            description="Import existing AGENT.md into memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to AGENT.md"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="doc_get_section",
            description="Get documentation by section type",
            inputSchema={
                "type": "object",
                "properties": {
                    "section_type": {"type": "string", "enum": SECTION_TYPES}
                },
                "required": ["section_type"]
            }
        ),

        # === CONVERSATION TOOLS (3) ===
        Tool(
            name="conversation_store",
            description="Store a conversation summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Session summary"},
                    "key_decisions": {"type": "array", "items": {"type": "string"}, "description": "Key decisions made"},
                    "key_changes": {"type": "array", "items": {"type": "string"}, "description": "Key changes made"},
                    "next_steps": {"type": "array", "items": {"type": "string"}, "description": "Next steps"}
                },
                "required": ["summary"]
            }
        ),
        Tool(
            name="conversation_search",
            description="Search past conversations",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "n_results": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="conversation_get_recent",
            description="Get recent conversation summaries",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 5}
                }
            }
        )
    ]


# ============================================================================
# TOOL HANDLERS
# ============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    chromadb, task_mgr, graph_mgr, doc_mgr, conv_mgr = get_managers()

    try:
        result = await handle_tool(name, arguments, chromadb, task_mgr, graph_mgr, doc_mgr, conv_mgr)
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Tool error: {name} - {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_tool(
    name: str,
    args: dict,
    chromadb: ChromaDBManager,
    task_mgr: TaskManager,
    graph_mgr: GraphManager,
    doc_mgr: DocumentationManager,
    conv_mgr: ConversationManager
) -> Any:
    """Route tool calls to handlers."""

    # === MEMORY TOOLS ===
    if name == "memory_store":
        metadata = {"category": args.get("category", "memory")}
        if args.get("tags"):
            metadata["tags"] = args["tags"]
        return chromadb.store_memory(args["content"], metadata)

    elif name == "memory_search":
        filter_meta = None
        if args.get("category"):
            filter_meta = {"category": args["category"]}
        return chromadb.search_memory(
            args["query"],
            args.get("n_results", 5),
            filter_meta,
            summarize=not args.get("full_content", False)
        )

    elif name == "memory_get_full":
        result = chromadb.get_by_id(args["memory_id"])
        if result:
            return result
        return {"status": "error", "message": "Memory not found"}

    elif name == "memory_stats":
        return chromadb.get_stats()

    # === TASK TOOLS ===
    elif name == "task_create":
        labels = args.get("labels", "").split(",") if args.get("labels") else None
        labels = [l.strip() for l in labels] if labels else None
        return task_mgr.create_task(
            title=args["title"],
            description=args.get("description", ""),
            priority=args.get("priority", 2),
            task_type=args.get("task_type", "task"),
            assignee=args.get("assignee", ""),
            labels=labels,
            graph_node=args.get("graph_node")
        )

    elif name == "task_list":
        return task_mgr.list_tasks(
            status=args.get("status"),
            priority=args.get("priority"),
            assignee=args.get("assignee"),
            task_type=args.get("task_type"),
            graph_node=args.get("graph_node"),
            limit=args.get("limit", 50)
        )

    elif name == "task_get":
        return task_mgr.get_task(args["task_id"])

    elif name == "task_update":
        labels = args.get("labels", "").split(",") if args.get("labels") else None
        labels = [l.strip() for l in labels] if labels else None
        return task_mgr.update_task(
            task_id=args["task_id"],
            status=args.get("status"),
            priority=args.get("priority"),
            assignee=args.get("assignee"),
            notes=args.get("notes"),
            labels=labels
        )

    elif name == "task_close":
        return task_mgr.close_task(args["task_id"], args.get("reason", ""))

    elif name == "task_search":
        return task_mgr.search_tasks(args["query"], args.get("n_results", 10))

    elif name == "task_stats":
        return task_mgr.get_stats()

    elif name == "task_get_open":
        return task_mgr.get_open_tasks()

    elif name == "task_get_my_tasks":
        return task_mgr.get_my_tasks(args["assignee"])

    elif name == "task_get_by_graph_node":
        return task_mgr.get_tasks_by_graph_node(args["graph_node"])

    # === GRAPH TOOLS ===
    elif name == "graph_add_node":
        return graph_mgr.add_node(
            node_id=args["node_id"],
            node_type=args["node_type"],
            name=args["name"],
            properties=args.get("properties")
        )

    elif name == "graph_add_edge":
        return graph_mgr.add_edge(
            from_id=args["from_id"],
            to_id=args["to_id"],
            relationship=args["relationship"],
            properties=args.get("properties")
        )

    elif name == "graph_query_relationships":
        return graph_mgr.query_relationships(
            node_id=args["node_id"],
            direction=args.get("direction", "both"),
            relationship=args.get("relationship")
        )

    elif name == "graph_analyze_impact":
        return graph_mgr.analyze_impact(args["node_id"])

    elif name == "graph_find_path":
        return graph_mgr.find_path(args["from_id"], args["to_id"])

    elif name == "graph_visualize":
        node_ids = args.get("node_ids")
        return graph_mgr.generate_mermaid(node_ids)

    elif name == "graph_get_node":
        return graph_mgr.get_node(args["node_id"])

    elif name == "graph_list_nodes":
        return graph_mgr.list_nodes(
            node_type=args.get("node_type"),
            limit=args.get("limit", 100)
        )

    elif name == "graph_delete_node":
        return graph_mgr.delete_node(args["node_id"])

    elif name == "graph_stats":
        return graph_mgr.get_stats()

    elif name == "graph_find_orphans":
        return graph_mgr.find_orphans()

    elif name == "graph_export_architecture":
        content = graph_mgr.export_architecture()
        if args.get("output_path"):
            Path(args["output_path"]).write_text(content, encoding="utf-8")
            return {"status": "exported", "path": args["output_path"]}
        return content

    # === DOCUMENTATION TOOLS ===
    elif name == "doc_store_section":
        tags = args.get("tags", "").split(",") if args.get("tags") else None
        tags = [t.strip() for t in tags] if tags else None
        return doc_mgr.store_section(
            section_type=args["section_type"],
            content=args["content"],
            title=args.get("title"),
            tags=tags
        )

    elif name == "doc_search":
        return doc_mgr.search_docs(args["query"], args.get("n_results", 10))

    elif name == "doc_generate_agent_md":
        output_path = Path(args["output_path"]) if args.get("output_path") else None
        content = doc_mgr.generate_agent_md(output_path)
        if output_path:
            return {"status": "generated", "path": str(output_path)}
        return content

    elif name == "doc_import_agent_md":
        return doc_mgr.import_agent_md(Path(args["file_path"]))

    elif name == "doc_get_section":
        return doc_mgr.get_section(args["section_type"])

    # === CONVERSATION TOOLS ===
    elif name == "conversation_store":
        return conv_mgr.store_conversation(
            summary=args["summary"],
            key_decisions=args.get("key_decisions"),
            key_changes=args.get("key_changes"),
            next_steps=args.get("next_steps")
        )

    elif name == "conversation_search":
        return conv_mgr.search_conversations(args["query"], args.get("n_results", 10))

    elif name == "conversation_get_recent":
        return conv_mgr.get_recent_conversations(args.get("limit", 5))

    else:
        return {"status": "error", "message": f"Unknown tool: {name}"}


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Run the MCP server."""
    project_id = get_project_id()
    logger.info(f"Starting Agent Memory MCP Server for project: {project_id}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run():
    """Entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
