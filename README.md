# Agent Memory

A unified memory system for AI Agents with ChromaDB, Task Management, and Architecture Graph. Works with any MCP-compatible agent.

## Features

- **Persistent Memory** - Semantic search with ChromaDB
- **Task Management** - ChromaDB-based tracking (no external deps)
- **Architecture Graph** - Map APIs, screens, journeys with NetworkX
- **Auto-Documentation** - Generate AGENT.md from memory
- **Conversation Tracking** - Never lose session context
- **33+ MCP Tools** - Comprehensive toolkit for any AI agent
- **Agent-Agnostic** - Works with any MCP-compatible agent
- **Windows-First** - PowerShell scripts and Windows-compatible

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: AI Agents (Any MCP-compatible agent)               │
│ - Memory tools (semantic search)                            │
│ - Task management tools (ChromaDB-based)                    │
│ - Architecture graph tools (APIs, screens, journeys)        │
└─────────────────────────────────────────────────────────────┘
                        ↕ (MCP RPC)
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: MCP Server (Tool Provider)                         │
│ - ChromaDB Manager (memory storage)                         │
│ - Task Manager (ChromaDB-based tasks)                       │
│ - Graph Manager (NetworkX + ChromaDB)                       │
│ - Documentation Manager (AGENT.md generation)               │
└─────────────────────────────────────────────────────────────┘
                        ↕ (Storage)
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Storage (Project-Isolated)                         │
│ ChromaDB: ~/.agent-chromadb/{project}/                      │
│ - Memories, Tasks, Graph Nodes, Graph Edges, Documentation  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```powershell
# 1. Clone and install
git clone https://github.com/zeronsec/ai-agent-memory.git
cd ai-agent-memory
pip install .

# 2. Run installer (creates directories, configures MCP server)
.\scripts\install.ps1

# 3. Restart your agent - tools are now available!
```

## Installation

### Option 1: PowerShell Installer (Recommended for Windows)

```powershell
git clone https://github.com/zeronsec/ai-agent-memory.git

cd ai-agent-memory
.\scripts\install.ps1
```

### Option 2: Manual Installation

```bash
# Clone
git clone https://github.com/zeronsec/ai-agent-memory.git
cd ai-agent-memory

# Install
pip install .

# Or development mode
pip install -e ".[dev]"
```

### Configure Your MCP Client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "agent-memory": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

For other MCP-compatible agents, consult their documentation for MCP server configuration.

## Available Tools (33)

### Memory Tools (3)
| Tool | Description |
|------|-------------|
| `memory_store` | Store knowledge with semantic search |
| `memory_search` | Find relevant memories |
| `memory_stats` | Get memory statistics |

### Task Tools (10)
| Tool | Description |
|------|-------------|
| `task_create` | Create new task |
| `task_list` | List with filters |
| `task_get` | Get task details |
| `task_update` | Update status/priority |
| `task_close` | Close task with reason |
| `task_search` | Semantic search |
| `task_stats` | Get statistics |
| `task_get_open` | Quick open task list |
| `task_get_my_tasks` | Tasks by assignee |
| `task_get_by_graph_node` | Tasks linked to graph |

### Graph Tools (12)
| Tool | Description |
|------|-------------|
| `graph_add_node` | Add API, screen, service, etc. |
| `graph_add_edge` | Create relationship |
| `graph_query_relationships` | Find connections |
| `graph_analyze_impact` | Impact analysis |
| `graph_find_path` | Find path between nodes |
| `graph_visualize` | Generate Mermaid diagram |
| `graph_get_node` | Get node details |
| `graph_list_nodes` | List by type |
| `graph_delete_node` | Remove node |
| `graph_stats` | Graph statistics |
| `graph_find_orphans` | Find disconnected nodes |
| `graph_export_architecture` | Export ARCHITECTURE.md |

### Documentation Tools (5)
| Tool | Description |
|------|-------------|
| `doc_store_section` | Store documentation section |
| `doc_search` | Search documentation |
| `doc_generate_agent_md` | Generate AGENT.md |
| `doc_import_agent_md` | Import existing AGENT.md |
| `doc_get_section` | Get by section type |

### Conversation Tools (3)
| Tool | Description |
|------|-------------|
| `conversation_store` | Store session summary |
| `conversation_search` | Search past sessions |
| `conversation_get_recent` | Get recent summaries |

## Usage Examples

### Store Knowledge
```python
memory_store(
    content="Decision: Use PostgreSQL for invoices due to complex queries",
    category="decision",
    tags="database,invoices"
)
```

### Track Tasks
```python
# Create
task_create(
    title="Implement invoice validation",
    priority=1,
    graph_node="api-create-invoice"
)

# Update
task_update(task_id="task-abc123", status="in_progress")

# Close
task_close(task_id="task-abc123", reason="Completed with tests")
```

### Map Architecture
```python
# Add nodes
graph_add_node(
    node_id="api-invoices",
    node_type="api",
    name="Invoice API"
)

graph_add_node(
    node_id="screen-invoice-form",
    node_type="screen",
    name="Invoice Form"
)

# Connect
graph_add_edge(
    from_id="screen-invoice-form",
    to_id="api-invoices",
    relationship="calls"
)

# Analyze impact
graph_analyze_impact("api-invoices")
```

### Generate Documentation
```python
# Store sections
doc_store_section(
    section_type="architecture",
    content="The system uses a microservices architecture...",
    title="System Overview"
)

# Generate md files
doc_generate_agent_md(output_path="AGENT.md")
```

## Project Configuration

### Set Project ID

The system auto-detects project ID from:
1. `AGENT_PROJECT_ID` environment variable
2. `.agent-project` file in project root
3. Git repository name
4. Current folder name

To explicitly set:
```
echo "my-project-name" > .agent-project
```

## Data Storage

- **ChromaDB**: `~/.agent-chromadb/{project}/`
- **Config**: `~/.agent-memory-mcp/config/`
- **Logs**: `~/.agent-memory-mcp/logs/`

## Directory Structure

```
ai-agent-memory/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP server (33 tools)
│   ├── chromadb_manager.py    # ChromaDB operations
│   ├── task_manager.py        # Task tracking
│   ├── graph_manager.py       # Architecture graph
│   ├── documentation_manager.py
│   ├── config.py
│   └── utils.py
├── scripts/
│   ├── install.ps1            # Windows installer
│   ├── test-integration.ps1   # Integration tests
│   ├── visualize-graph.ps1    # Graph visualization
│   └── session-wrapper.ps1
├── config/
│   ├── mcp-server.json
│   └── graph-templates.yaml
├── templates/
│   ├── AGENTS.md
│   └── ARCHITECTURE.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Testing

```powershell
# Run integration tests
.\scripts\test-integration.ps1

# Or with pytest
pip install -e ".[dev]"
pytest tests/ -v
```

### Memory Not Persisting

1. Check project ID: `python -c "from src.config import get_project_id; print(get_project_id())"`
2. Verify ChromaDB path exists: `~/.agent-chromadb/`

## License

MIT License - see [LICENSE](LICENSE) for details.
