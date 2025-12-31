"""Task management using ChromaDB (no external dependencies like Beads)."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

from .chromadb_manager import ChromaDBManager


logger = logging.getLogger(__name__)


# Task statuses
TASK_STATUSES = ["open", "in_progress", "blocked", "closed"]

# Task types
TASK_TYPES = ["task", "bug", "feature", "epic", "story"]

# Priority levels (0 = highest)
PRIORITY_LABELS = {0: "P0-Critical", 1: "P1-High", 2: "P2-Medium", 3: "P3-Low", 4: "P4-Backlog"}


class TaskManager:
    """ChromaDB-based task tracker (replaces Beads)."""

    def __init__(self, chromadb_manager: ChromaDBManager):
        self.chromadb = chromadb_manager

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: int = 2,
        task_type: str = "task",
        assignee: str = "",
        labels: Optional[List[str]] = None,
        graph_node: Optional[str] = None
    ) -> Dict:
        """
        Create a new task.

        Args:
            title: Task title
            description: Task description
            priority: Priority level (0=critical, 4=backlog)
            task_type: Type (task, bug, feature, epic, story)
            assignee: Who is assigned
            labels: List of labels/tags
            graph_node: Link to architecture graph node

        Returns:
            Dict with task_id and status
        """
        if not title or not title.strip():
            return {"status": "error", "message": "Title is required"}

        if task_type not in TASK_TYPES:
            task_type = "task"

        if priority < 0:
            priority = 0
        elif priority > 4:
            priority = 4

        task_id = self._generate_task_id()

        # Build content for semantic search
        content = f"# Task: {title}\n\n"
        if description:
            content += f"## Description\n{description}\n\n"
        content += f"**Type:** {task_type}\n"
        content += f"**Priority:** {PRIORITY_LABELS.get(priority, 'P2-Medium')}\n"
        if assignee:
            content += f"**Assignee:** {assignee}\n"
        if labels:
            content += f"**Labels:** {', '.join(labels)}\n"
        if graph_node:
            content += f"**Graph Node:** {graph_node}\n"

        # Build metadata
        metadata = {
            "category": "task",
            "task_id": task_id,
            "title": title,
            "status": "open",
            "priority": priority,
            "task_type": task_type,
            "assignee": assignee or "unassigned",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        if labels:
            metadata["labels"] = ",".join(labels)

        if graph_node:
            metadata["graph_node"] = graph_node

        # Store in ChromaDB
        result = self.chromadb.store_memory(content, metadata, custom_id=task_id)

        if result.get("status") == "success":
            logger.info(f"Created task: {task_id} - {title}")
            return {
                "status": "created",
                "task_id": task_id,
                "title": title,
                "priority": PRIORITY_LABELS.get(priority)
            }

        return result

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        assignee: Optional[str] = None,
        task_type: Optional[str] = None,
        graph_node: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        List tasks with filters.

        Args:
            status: Filter by status (open, in_progress, blocked, closed)
            priority: Filter by priority (0-4)
            assignee: Filter by assignee
            task_type: Filter by type
            graph_node: Filter by linked graph node
            limit: Maximum results

        Returns:
            List of tasks
        """
        # Build filter - start with category
        filter_meta = {"category": "task"}

        # Note: ChromaDB where clause supports only one condition at a time for equality
        # We'll filter additional conditions in Python
        primary_filter = filter_meta.copy()

        if status:
            primary_filter["status"] = status

        # Get results
        results = self.chromadb.get_by_metadata(primary_filter, limit=10000)

        tasks = []
        for item in results:
            meta = item.get("metadata", {})

            # Additional filtering in Python
            if priority is not None and meta.get("priority") != priority:
                continue
            if assignee and meta.get("assignee") != assignee:
                continue
            if task_type and meta.get("task_type") != task_type:
                continue
            if graph_node and meta.get("graph_node") != graph_node:
                continue

            tasks.append({
                "task_id": meta.get("task_id"),
                "title": meta.get("title"),
                "status": meta.get("status"),
                "priority": meta.get("priority"),
                "priority_label": PRIORITY_LABELS.get(meta.get("priority", 2)),
                "task_type": meta.get("task_type"),
                "assignee": meta.get("assignee"),
                "labels": meta.get("labels", "").split(",") if meta.get("labels") else [],
                "graph_node": meta.get("graph_node"),
                "created_at": meta.get("created_at"),
                "updated_at": meta.get("updated_at")
            })

        # Sort by priority (ascending), then created_at (descending)
        tasks.sort(key=lambda x: (x.get("priority", 2), -(hash(x.get("created_at", "")) or 0)))

        return tasks[:limit]

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task details by ID."""
        results = self.chromadb.get_by_metadata(
            {"category": "task", "task_id": task_id}
        )

        if not results:
            return None

        item = results[0]
        meta = item.get("metadata", {})

        return {
            "task_id": meta.get("task_id"),
            "title": meta.get("title"),
            "status": meta.get("status"),
            "priority": meta.get("priority"),
            "priority_label": PRIORITY_LABELS.get(meta.get("priority", 2)),
            "task_type": meta.get("task_type"),
            "assignee": meta.get("assignee"),
            "labels": meta.get("labels", "").split(",") if meta.get("labels") else [],
            "graph_node": meta.get("graph_node"),
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
            "closed_at": meta.get("closed_at"),
            "content": item.get("content", "")
        }

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        assignee: Optional[str] = None,
        notes: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict:
        """
        Update task fields.

        Args:
            task_id: Task ID to update
            status: New status
            priority: New priority
            assignee: New assignee
            notes: Notes to append
            labels: New labels (replaces existing)

        Returns:
            Dict with status
        """
        task = self.get_task(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}

        # Validate status
        if status and status not in TASK_STATUSES:
            return {"status": "error", "message": f"Invalid status. Must be one of: {', '.join(TASK_STATUSES)}"}

        # Build updated metadata
        new_meta = {
            "category": "task",
            "task_id": task_id,
            "title": task["title"],
            "status": status or task["status"],
            "priority": priority if priority is not None else task["priority"],
            "task_type": task["task_type"],
            "assignee": assignee if assignee is not None else task["assignee"],
            "created_at": task["created_at"],
            "updated_at": datetime.now().isoformat()
        }

        # Handle labels
        if labels is not None:
            new_meta["labels"] = ",".join(labels)
        elif task.get("labels"):
            new_meta["labels"] = ",".join(task["labels"])

        if task.get("graph_node"):
            new_meta["graph_node"] = task["graph_node"]

        # Update content if notes provided
        content = task["content"]
        if notes:
            content += f"\n\n## Update ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n{notes}\n"

        # Delete old and create new (ChromaDB upsert pattern)
        self.chromadb.delete_by_metadata({"category": "task", "task_id": task_id})
        self.chromadb.store_memory(content, new_meta, custom_id=task_id)

        logger.info(f"Updated task: {task_id}")

        return {
            "status": "updated",
            "task_id": task_id,
            "new_status": new_meta["status"],
            "new_priority": PRIORITY_LABELS.get(new_meta["priority"])
        }

    def close_task(self, task_id: str, reason: str = "") -> Dict:
        """
        Close a task.

        Args:
            task_id: Task ID to close
            reason: Reason for closing

        Returns:
            Dict with status
        """
        task = self.get_task(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}

        # Update content with close reason
        content = task["content"]
        if reason:
            content += f"\n\n## Closed ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n{reason}\n"

        new_meta = {
            "category": "task",
            "task_id": task_id,
            "title": task["title"],
            "status": "closed",
            "priority": task["priority"],
            "task_type": task["task_type"],
            "assignee": task["assignee"],
            "created_at": task["created_at"],
            "updated_at": datetime.now().isoformat(),
            "closed_at": datetime.now().isoformat()
        }

        if task.get("labels"):
            new_meta["labels"] = ",".join(task["labels"])
        if task.get("graph_node"):
            new_meta["graph_node"] = task["graph_node"]

        # Delete old and create new
        self.chromadb.delete_by_metadata({"category": "task", "task_id": task_id})
        self.chromadb.store_memory(content, new_meta, custom_id=task_id)

        logger.info(f"Closed task: {task_id}")

        return {"status": "closed", "task_id": task_id, "title": task["title"]}

    def delete_task(self, task_id: str) -> Dict:
        """Delete a task permanently."""
        task = self.get_task(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}

        self.chromadb.delete_by_metadata({"category": "task", "task_id": task_id})

        logger.info(f"Deleted task: {task_id}")

        return {"status": "deleted", "task_id": task_id}

    def search_tasks(self, query: str, n_results: int = 10) -> List[Dict]:
        """
        Semantic search for tasks.

        Args:
            query: Search query
            n_results: Max results

        Returns:
            List of matching tasks with relevance scores
        """
        results = self.chromadb.search_memory(
            query=query,
            n_results=n_results,
            filter_metadata={"category": "task"}
        )

        tasks = []
        for result in results:
            meta = result.get("metadata", {})
            tasks.append({
                "task_id": meta.get("task_id"),
                "title": meta.get("title"),
                "status": meta.get("status"),
                "priority_label": PRIORITY_LABELS.get(meta.get("priority", 2)),
                "relevance": result.get("score", 0)
            })

        return tasks

    def get_open_tasks(self) -> List[Dict]:
        """Get all open tasks (quick access)."""
        return self.list_tasks(status="open")

    def get_my_tasks(self, assignee: str) -> List[Dict]:
        """Get tasks assigned to a specific person."""
        return self.list_tasks(assignee=assignee)

    def get_tasks_by_graph_node(self, graph_node: str) -> List[Dict]:
        """Get tasks linked to a specific graph node."""
        return self.list_tasks(graph_node=graph_node)

    def get_stats(self) -> Dict:
        """Get task statistics."""
        all_tasks = self.list_tasks(limit=10000)

        by_status = {}
        for status in TASK_STATUSES:
            by_status[status] = len([t for t in all_tasks if t.get("status") == status])

        by_priority = {}
        for p in range(5):
            by_priority[PRIORITY_LABELS[p]] = len([t for t in all_tasks if t.get("priority") == p])

        by_type = {}
        for t in all_tasks:
            task_type = t.get("task_type", "task")
            by_type[task_type] = by_type.get(task_type, 0) + 1

        return {
            "total": len(all_tasks),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_type": by_type,
            "open_count": by_status.get("open", 0),
            "in_progress_count": by_status.get("in_progress", 0)
        }

    @staticmethod
    def _generate_task_id() -> str:
        """Generate unique task ID."""
        timestamp = datetime.now().isoformat()
        return f"task-{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"


def get_task_manager(chromadb_manager: ChromaDBManager) -> TaskManager:
    """Factory function."""
    return TaskManager(chromadb_manager)
