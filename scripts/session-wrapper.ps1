# Agent Memory MCP - Session Wrapper
# Wraps agent sessions to capture conversation context
# Run as: .\scripts\session-wrapper.ps1

param(
    [string]$ProjectId = "",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Agent Memory MCP - Session Wrapper" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Set project ID if provided
if ($ProjectId) {
    $env:AGENT_PROJECT_ID = $ProjectId
    Write-Host "Project ID: $ProjectId" -ForegroundColor Yellow
}

# Get current project info
$pythonScript = @"
from src.config import get_project_id
from src.chromadb_manager import get_chromadb_manager
from src.task_manager import get_task_manager
from src.graph_manager import get_graph_manager

project_id = get_project_id()
print(f"Project: {project_id}")

chromadb = get_chromadb_manager(project_id)
task_mgr = get_task_manager(chromadb)
graph_mgr = get_graph_manager(chromadb)

# Get stats
mem_stats = chromadb.get_stats()
task_stats = task_mgr.get_stats()
graph_stats = graph_mgr.get_stats()

print(f"Memories: {mem_stats['total_items']}")
print(f"Tasks: {task_stats['total']} (Open: {task_stats['open_count']})")
print(f"Graph Nodes: {graph_stats['total_nodes']}")
"@

Write-Host ""
Write-Host "Session Context:" -ForegroundColor Yellow
python -c $pythonScript 2>&1

Write-Host ""
Write-Host "Session ready. Memory tools are now available." -ForegroundColor Green
Write-Host ""
Write-Host "Quick commands:" -ForegroundColor Cyan
Write-Host "  memory_search('recent decisions')" -ForegroundColor White
Write-Host "  task_list(status='open')" -ForegroundColor White
Write-Host "  graph_stats()" -ForegroundColor White
Write-Host ""
