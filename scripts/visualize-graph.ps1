# Agent Memory MCP - Graph Visualization Script
# Generates a Mermaid diagram from the architecture graph
# Run as: .\scripts\visualize-graph.ps1 [-Output path\to\output.md]

param(
    [string]$Output = ".\visualizations\architecture.md",
    [string]$ProjectId = ""
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Graph Visualization" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Ensure output directory exists
$outputDir = Split-Path -Parent $Output
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Generate visualization
$pythonScript = @"
from src.chromadb_manager import get_chromadb_manager
from src.graph_manager import get_graph_manager
from pathlib import Path

project_id = '$ProjectId' if '$ProjectId' else None
chromadb = get_chromadb_manager(project_id)
graph_mgr = get_graph_manager(chromadb)

# Get stats
stats = graph_mgr.get_stats()
print(f"Graph has {stats['total_nodes']} nodes and {stats['total_edges']} edges")

# Generate content
content = graph_mgr.export_architecture()

# Write to file
output_path = Path(r'$Output')
output_path.write_text(content, encoding='utf-8')
print(f"Written to: {output_path}")
"@

try {
    python -c $pythonScript 2>&1
    Write-Host ""
    Write-Host "Visualization generated successfully!" -ForegroundColor Green
    Write-Host "Open $Output to view the Mermaid diagram" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
