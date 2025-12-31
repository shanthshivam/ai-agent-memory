# Architecture Map

*This file is auto-generated from the architecture graph.*

To regenerate: `graph_export_architecture(output_path="ARCHITECTURE.md")`

---

## Overview

- **Total Nodes:** 0
- **Total Relationships:** 0

---

## APIs

(No APIs mapped yet. Use `graph_add_node(node_type="api")` to add.)

---

## Screens

(No screens mapped yet. Use `graph_add_node(node_type="screen")` to add.)

---

## Services

(No services mapped yet. Use `graph_add_node(node_type="service")` to add.)

---

## Databases

(No databases mapped yet. Use `graph_add_node(node_type="database")` to add.)

---

## Visual Diagram

```mermaid
graph TD
    %% No nodes yet
    %% Use graph_add_node() to add components
```

---

## How to Map Architecture

1. **Add nodes for each component:**
```bash
graph_add_node(
    node_id="api-users",
    node_type="api",
    name="User API",
    properties={"version": "v1"}
)
```

2. **Connect with relationships:**
```bash
graph_add_edge(
    from_id="screen-login",
    to_id="api-users",
    relationship="calls"
)
```

3. **Analyze before changes:**
```bash
graph_analyze_impact("api-users")
```

4. **Export updated diagram:**
```bash
graph_export_architecture(output_path="ARCHITECTURE.md")
```
