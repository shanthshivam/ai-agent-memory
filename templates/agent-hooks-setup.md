# Agent Memory Hooks Setup

This document shows how to set up automatic memory injection for different agent frameworks.

## General Concept

The hook script (`inject-memory-context.py`) queries ChromaDB and outputs recent context (conversations, decisions, tasks) that can be injected into agent sessions.

## Claude Code Integration

For Claude Code users, copy these files to your project:

```bash
# From your project root:
mkdir -p .claude/hooks

# Copy the hook script
cp /path/to/ai-agent-memory/.claude/hooks/inject-memory-context.py .claude/hooks/

# Copy the settings
cp /path/to/ai-agent-memory/.claude/settings.json .claude/

# Create local memory storage
mkdir .agent-memory
```

### .claude/settings.json
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/inject-memory-context.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Other Agent Frameworks

For other agents that support session hooks or startup scripts:

1. Run `inject-memory-context.py` at session start
2. Capture the output (XML-formatted memory context)
3. Include in the agent's initial prompt/context

Example manual usage:
```bash
echo "{}" | python .claude/hooks/inject-memory-context.py
```

## What It Does

| Event | Action |
|-------|--------|
| Session Start | Injects recent conversations, decisions, and open tasks |
| Session End | Use `conversation_store` tool to save session summary |

## Customization

Edit `inject-memory-context.py` to change:
- `limit=2` for conversations (increase for more history)
- `summary_length=300` (increase for more detail, uses more context)
- Add/remove sections (decisions, tasks, etc.)

## Troubleshooting

Test the hook manually:
```bash
echo "{}" | python .claude/hooks/inject-memory-context.py
```

If no output, either:
1. No memory stored yet - use `memory_store` first
2. `.agent-memory` folder doesn't exist - create it
