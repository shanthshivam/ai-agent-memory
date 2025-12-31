# Agent Memory MCP - Integration Test Script
# Run as: .\scripts\test-integration.ps1

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Agent Memory MCP - Integration Tests" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Test imports
Write-Host "[1/4] Testing imports..." -ForegroundColor Yellow

$imports = @(
    "from src.config import Config, get_project_id",
    "from src.chromadb_manager import ChromaDBManager",
    "from src.task_manager import TaskManager",
    "from src.graph_manager import GraphManager",
    "from src.documentation_manager import DocumentationManager",
    "from src.server import server"
)

$passed = 0
$failed = 0

foreach ($imp in $imports) {
    try {
        python -c $imp 2>&1 | Out-Null
        Write-Host "  OK: $imp" -ForegroundColor Green
        $passed++
    } catch {
        Write-Host "  FAIL: $imp" -ForegroundColor Red
        $failed++
    }
}

# Test ChromaDB
Write-Host ""
Write-Host "[2/4] Testing ChromaDB..." -ForegroundColor Yellow

$chromaTest = @"
from src.chromadb_manager import get_chromadb_manager
mgr = get_chromadb_manager('test-integration')
result = mgr.store_memory('Test memory content', {'category': 'memory'})
assert result['status'] == 'success', 'Store failed'
results = mgr.search_memory('Test memory')
assert len(results) > 0, 'Search failed'
print('  ChromaDB: OK')
"@

try {
    python -c $chromaTest 2>&1
    Write-Host "  ChromaDB tests passed!" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  ChromaDB tests failed: $_" -ForegroundColor Red
    $failed++
}

# Test Task Manager
Write-Host ""
Write-Host "[3/4] Testing Task Manager..." -ForegroundColor Yellow

$taskTest = @"
from src.chromadb_manager import get_chromadb_manager
from src.task_manager import get_task_manager
chromadb = get_chromadb_manager('test-integration')
task_mgr = get_task_manager(chromadb)
result = task_mgr.create_task('Test Task', description='Test description', priority=1)
assert result['status'] == 'created', 'Create failed'
tasks = task_mgr.list_tasks()
assert len(tasks) > 0, 'List failed'
print('  Task Manager: OK')
"@

try {
    python -c $taskTest 2>&1
    Write-Host "  Task Manager tests passed!" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  Task Manager tests failed: $_" -ForegroundColor Red
    $failed++
}

# Test Graph Manager
Write-Host ""
Write-Host "[4/4] Testing Graph Manager..." -ForegroundColor Yellow

$graphTest = @"
from src.chromadb_manager import get_chromadb_manager
from src.graph_manager import get_graph_manager
chromadb = get_chromadb_manager('test-integration')
graph_mgr = get_graph_manager(chromadb)
result = graph_mgr.add_node('test-api', 'api', 'Test API')
assert result['status'] == 'created', 'Add node failed'
result = graph_mgr.add_node('test-screen', 'screen', 'Test Screen')
assert result['status'] == 'created', 'Add node failed'
result = graph_mgr.add_edge('test-screen', 'test-api', 'calls')
assert result['status'] == 'created', 'Add edge failed'
stats = graph_mgr.get_stats()
assert stats['total_nodes'] >= 2, 'Stats failed'
print('  Graph Manager: OK')
"@

try {
    python -c $graphTest 2>&1
    Write-Host "  Graph Manager tests passed!" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  Graph Manager tests failed: $_" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Test Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failed -gt 0) {
    exit 1
}
