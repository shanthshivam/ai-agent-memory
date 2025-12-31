# Agent Memory MCP - Windows PowerShell Installer
# Run as: .\scripts\install.ps1

param(
    [switch]$Dev,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Agent Memory MCP - Windows Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host "[2/5] Creating directories..." -ForegroundColor Yellow

$dirs = @(
    "$env:USERPROFILE\.agent-memory-mcp\logs",
    "$env:USERPROFILE\.agent-memory-mcp\config",
    "$env:USERPROFILE\.agent-memory-mcp\registry",
    "$env:USERPROFILE\.agent-chromadb"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Exists: $dir" -ForegroundColor Gray
    }
}

# Install package
Write-Host "[3/5] Installing package..." -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir

Push-Location $projectDir

try {
    if ($Dev) {
        Write-Host "  Installing in development mode..." -ForegroundColor Cyan
        pip install -e ".[dev]" 2>&1 | ForEach-Object { Write-Host "  $_" }
    } else {
        pip install . 2>&1 | ForEach-Object { Write-Host "  $_" }
    }
    Write-Host "  Package installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Installation failed: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# Create MCP config
Write-Host "[4/5] Configuring MCP server..." -ForegroundColor Yellow

$configDir = "$env:USERPROFILE\.agent-memory-mcp"
$configFile = "$configDir\mcp-config.json"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$mcpConfig = @{
    mcpServers = @{
        "agent-memory" = @{
            command = "python"
            args = @("-m", "src.server")
        }
    }
}

if (Test-Path $configFile) {
    if ($Force) {
        Write-Host "  Overwriting existing config..." -ForegroundColor Yellow
        $mcpConfig | ConvertTo-Json -Depth 10 | Set-Content $configFile -Encoding UTF8
    } else {
        Write-Host "  Config exists. Use -Force to overwrite." -ForegroundColor Yellow
        Write-Host "  Or manually add to: $configFile" -ForegroundColor Gray
    }
} else {
    $mcpConfig | ConvertTo-Json -Depth 10 | Set-Content $configFile -Encoding UTF8
    Write-Host "  Created: $configFile" -ForegroundColor Green
}

Write-Host "  Add 'agent-memory' server to your MCP client with: python -m src.server" -ForegroundColor Gray

# Verify installation
Write-Host "[5/5] Verifying installation..." -ForegroundColor Yellow

try {
    python -c "from src import server; print('  Import OK')" 2>&1
    Write-Host "  Verification passed!" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: Import test failed. Check installation." -ForegroundColor Yellow
}

# Done
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your MCP-compatible agent" -ForegroundColor White
Write-Host "  2. Try: memory_store, task_create, graph_add_node" -ForegroundColor White
Write-Host ""
Write-Host "Available tools: 33 (memory, tasks, graph, docs, conversations)" -ForegroundColor Cyan
Write-Host "Works with any MCP-compatible agent" -ForegroundColor Cyan
Write-Host ""
