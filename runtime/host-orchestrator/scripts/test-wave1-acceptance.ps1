param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$SmokeRunId
)

$ErrorActionPreference = 'Stop'

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
$projectRoot = Join-Path $resolvedRepoRoot 'runtime\host-orchestrator'
$snapshotRoot = Join-Path $resolvedRepoRoot 'snapshots\agentbridge-20260628'
$contractScript = Join-Path $snapshotRoot 'scripts\test-agentbridge-contract.ps1'
$smokeScript = Join-Path $projectRoot 'scripts\run-wave1-smokes.ps1'

if (-not $SmokeRunId) {
    $SmokeRunId = 'wave1-acceptance-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

function Get-NonPrivateGitStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    $lines = @(& git -C $Root status --short --untracked-files=all)
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed for $Root."
    }

    return @(
        $lines |
            Where-Object {
                $_ -and
                $_ -notmatch '(^|\s)private-local/' -and
                $_ -notmatch '(^|\s)private-local\\'
            }
    )
}

function Assert-ContractOk {
    param(
        [Parameter(Mandatory = $true)]
        [object]$ContractResult,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not $ContractResult.ok) {
        foreach ($issue in @($ContractResult.issues)) {
            Write-Error "${Label}: $issue"
        }
        throw "$Label failed."
    }
}

$gitStatusBefore = @(Get-NonPrivateGitStatus -Root $resolvedRepoRoot)

Push-Location $projectRoot
try {
    & uv run pytest
    if ($LASTEXITCODE -ne 0) {
        throw "uv run pytest failed (exit=$LASTEXITCODE)."
    }
}
finally {
    Pop-Location
}

$snapshotContract = & $contractScript -Root $snapshotRoot
Assert-ContractOk -ContractResult $snapshotContract -Label 'Snapshot AgentBridge contract gate'

$smokeSummary = & $smokeScript -RepoRoot $resolvedRepoRoot -RunId $SmokeRunId
if (-not $smokeSummary.ok) {
    foreach ($issue in @($smokeSummary.issues)) {
        Write-Error "Wave 1 smoke suite: $issue"
    }
    throw 'Wave 1 smoke suite failed.'
}

$generatedContract = & $contractScript -Root $smokeSummary.agentbridge_root
Assert-ContractOk -ContractResult $generatedContract -Label 'Generated smoke AgentBridge contract gate'

$gitStatusAfter = @(Get-NonPrivateGitStatus -Root $resolvedRepoRoot)
$unexpectedDelta = @(
    Compare-Object -ReferenceObject $gitStatusBefore -DifferenceObject $gitStatusAfter |
        Where-Object { $_.SideIndicator -in @('<=', '=>') }
)

if ($unexpectedDelta.Count -gt 0) {
    $unexpectedDelta | ForEach-Object {
        Write-Error "Unexpected repo status drift: $($_.SideIndicator) $($_.InputObject)"
    }
    throw 'Wave 1 acceptance introduced writes outside private-local.'
}

[pscustomobject]@{
    ok = $true
    repo_root = $resolvedRepoRoot
    smoke_run_id = $SmokeRunId
    smoke_run_root = $smokeSummary.run_root
    smoke_summary_path = $smokeSummary.summary_path
    snapshot_contract_root = $snapshotRoot
    generated_contract_root = $smokeSummary.agentbridge_root
    checks = @(
        [pscustomobject]@{ name = 'pytest'; ok = $true }
        [pscustomobject]@{ name = 'snapshot_contract'; ok = $true }
        [pscustomobject]@{ name = 'wave1_smoke_suite'; ok = $true }
        [pscustomobject]@{ name = 'generated_contract'; ok = $true }
        [pscustomobject]@{ name = 'no_repo_drift_outside_private_local'; ok = $true }
    )
}
