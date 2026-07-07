param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$RunId
)

$ErrorActionPreference = 'Stop'

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
$projectRoot = Join-Path $resolvedRepoRoot 'runtime\host-orchestrator'

if (-not $RunId) {
    $RunId = 'remote-non-gui-promotion-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

Push-Location $projectRoot
try {
    $jsonLines = & uv run python -m host_orchestrator `
        --repo-root $resolvedRepoRoot `
        --run-remote-non-gui-promotion `
        --remote-non-gui-promotion-run-id $RunId
    if ($LASTEXITCODE -ne 0) {
        throw "remote_non_gui promotion runner failed (exit=$LASTEXITCODE)."
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
    throw "remote_non_gui promotion suite reported issues."
}

$summary
