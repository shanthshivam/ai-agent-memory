# Agent Instructions - Agent Memory MCP

## Available Features

- **ChromaDB Memory** - Semantic search, decisions, knowledge
- **Task Management** - ChromaDB-based tracking (no external deps)
- **Architecture Graph** - Map APIs, screens, journeys, components
- **Auto-Documentation** - Generate AGENT.md from memory
- **Conversation Capture** - Never lose session context

## Quick Reference

### Session Start
```bash
# Get context from previous sessions
memory_search(query="recent decisions")
task_list(status="open", priority=1)
graph_stats()
conversation_get_recent(limit=3)
```

### During Development

**Store important decisions:**
```bash
memory_store(
    content="Decision: Use PostgreSQL for invoice data due to complex queries",
    category="decision",
    tags="database,invoices,architecture"
)
```

**Track tasks:**
```bash
# Create task
task_create(
    title="Implement invoice validation",
    priority=1,
    task_type="feature",
    graph_node="api-create-invoice"
)

# Update progress
task_update(task_id="task-abc123", status="in_progress")

# Close when done
task_close(task_id="task-abc123", reason="Validation implemented with tests")
```

**Map architecture:**
```bash
# Add an API endpoint
graph_add_node(
    node_id="api-create-invoice",
    node_type="api",
    name="POST /api/invoices/create",
    properties={"auth": "required", "version": "v2"}
)

# Add a screen
graph_add_node(
    node_id="screen-invoice-form",
    node_type="screen",
    name="Invoice Creation Form"
)

# Connect them
graph_add_edge(
    from_id="screen-invoice-form",
    to_id="api-create-invoice",
    relationship="calls"
)
```

### Before Making Changes

**Impact analysis:**
```bash
# What will break if I change this API?
graph_analyze_impact("api-create-invoice")
# Returns: risk level, affected screens, dependent services

# Find path from UI to database
graph_find_path("screen-invoice-form", "db-invoices")
```

### Session End

```bash
# Save session summary
conversation_store(
    summary="Implemented invoice validation with error handling",
    key_decisions=["Used Zod for schema validation", "Added rate limiting"],
    key_changes=["New validation middleware", "Updated API responses"],
    next_steps=["Add unit tests", "Update documentation"]
)

# Generate updated documentation
doc_generate_agent_md(output_path="AGENT.md")

# Export architecture diagram
graph_export_architecture(output_path="ARCHITECTURE.md")
```

## Tool Categories

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

## Node Types

- **api** - REST/GraphQL endpoints
- **screen** - UI pages/screens
- **journey** - User workflows
- **component** - Reusable UI components
- **service** - Backend services
- **database** - Data stores
- **queue** - Message queues
- **event** - Domain events
- **model** - Data models

## Relationship Types

- **calls** - Synchronous API call
- **uses** - Uses/imports
- **depends_on** - Has dependency
- **part_of** - Part of larger entity
- **triggers** - Triggers async action
- **reads** - Reads data from
- **writes** - Writes data to
- **emits** - Emits events
- **consumes** - Consumes events

## Best Practices

1. **Map as you build** - Add nodes/edges while implementing
2. **Link tasks to graph** - Use `graph_node` parameter
3. **Check impact first** - Before modifying shared components
4. **Store decisions** - Record why, not just what
5. **End session properly** - Save conversation summary
