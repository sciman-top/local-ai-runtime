param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$RunId
)

$ErrorActionPreference = 'Stop'

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
$projectRoot = Join-Path $resolvedRepoRoot 'runtime\host-orchestrator'

if (-not $RunId) {
    $RunId = 'multi-worker-sim-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

Push-Location $projectRoot
try {
    $jsonLines = & uv run python -m host_orchestrator `
        --repo-root $resolvedRepoRoot `
        --run-multi-worker-simulation `
        --multi-worker-simulation-run-id $RunId
    if ($LASTEXITCODE -ne 0) {
        throw "Multi-worker simulation runner failed (exit=$LASTEXITCODE)."
    }
}
finally {
    Pop-Location
}

$summary = (($jsonLines -join "`n") | ConvertFrom-Json)
if (-not $summary.ok) {
    foreach ($issue in @($summary.issues)) {
        Write-Error $issue
    }
    throw "Multi-worker simulation suite reported issues."
}

$summary
