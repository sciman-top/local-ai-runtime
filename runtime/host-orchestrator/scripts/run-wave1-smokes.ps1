param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$RunId
)

$ErrorActionPreference = 'Stop'

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
$projectRoot = Join-Path $resolvedRepoRoot 'runtime\host-orchestrator'

if (-not $RunId) {
    $RunId = 'wave1-smoke-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

Push-Location $projectRoot
try {
    $jsonLines = & uv run python -m host_orchestrator `
        --repo-root $resolvedRepoRoot `
        --run-wave1-smokes `
        --wave1-smoke-run-id $RunId
    if ($LASTEXITCODE -ne 0) {
        throw "Wave 1 smoke runner failed (exit=$LASTEXITCODE)."
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
    throw "Wave 1 smoke suite reported issues."
}

$summary
