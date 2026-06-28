[CmdletBinding(PositionalBinding = $false)]
param(
    [string[]]$Slots,
    [Alias('ActiveSlot')]
    [string]$ProviderSlot = 'primary',
    [string]$EnvFilePath,
    [string]$PrimaryBaseUrl,
    [string]$BackupBaseUrl,
    [string]$ModelPrimary = 'gpt-5.4',
    [string]$ModelFallback = 'gpt-5.4',
    [switch]$SkipBackupPrompt,
    [switch]$SkipSnapshot,
    [switch]$KeepSession,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$HermesArgs
)

$ErrorActionPreference = 'Stop'

$sessionScript = Join-Path $PSScriptRoot 'manage-hermes-provider-session.ps1'
$contractScript = Join-Path $PSScriptRoot 'test-agentbridge-contract.ps1'
$gateScript = Join-Path $PSScriptRoot 'test-hermes-bringup-gates.ps1'
$startScript = Join-Path $PSScriptRoot 'start-hermes.ps1'
$verifyScript = Join-Path $PSScriptRoot 'verify-hermes-boundary.ps1'
$snapshotScript = Join-Path $PSScriptRoot 'new-known-good-snapshot.ps1'
$snapshotTestScript = Join-Path $PSScriptRoot 'test-known-good-snapshot.ps1'

if (-not $HermesArgs -or $HermesArgs.Count -eq 0) {
    $HermesArgs = @('--oneshot', 'Reply with exactly OK.')
}

$interactiveEntryCommands = @('chat', 'auth', 'model', 'setup')
$commandName = if ($HermesArgs.Count -gt 0 -and $HermesArgs[0] -notmatch '^-') { $HermesArgs[0] } else { '' }
$hasQueryMode = (
    ($HermesArgs -contains '-q') -or
    ($HermesArgs -contains '--query') -or
    ($HermesArgs -contains '-z') -or
    ($HermesArgs -contains '--oneshot') -or
    (@($HermesArgs | Where-Object { $_ -like '--query=*' -or $_ -like '--oneshot=*' }).Count -gt 0)
)
$interactiveHermesCommand = (
    ($HermesArgs.Count -eq 0) -or
    (($commandName -eq 'chat') -and -not $hasQueryMode) -or
    (($interactiveEntryCommands -contains $commandName) -and ($commandName -ne 'chat')) -or
    (($HermesArgs -contains '--tui') -and -not $hasQueryMode) -or
    (($HermesArgs -contains '--cli') -and -not $hasQueryMode)
)

$summary = [ordered]@{
    loaded_session = $null
    contract = $null
    gates_before_start = $null
    hermes_started = $false
    boundary = $null
    snapshot = $null
    snapshot_test = $null
    session_cleared = $false
}

try {
    $loadParams = @{
        Action = 'load'
        Slot = $ProviderSlot
        ModelPrimary = $ModelPrimary
        ModelFallback = $ModelFallback
        SkipBackupPrompt = $SkipBackupPrompt
    }
    if ($EnvFilePath) {
        $loadParams.EnvFilePath = $EnvFilePath
    }
    if ($Slots -and $Slots.Count -gt 0) {
        $loadParams.Slots = $Slots
    }
    if ($PrimaryBaseUrl) {
        $loadParams.PrimaryBaseUrl = $PrimaryBaseUrl
    }
    if ($BackupBaseUrl) {
        $loadParams.BackupBaseUrl = $BackupBaseUrl
    }

    $summary.loaded_session = & $sessionScript @loadParams
    $summary.contract = & $contractScript
    if (-not $summary.contract.ok) {
        throw 'AgentBridge contract validation failed before Hermes bring-up.'
    }

    $summary.gates_before_start = & $gateScript
    if (-not $summary.gates_before_start.ready) {
        throw 'Hermes bring-up gates are not ready after session key injection.'
    }

    if ($interactiveHermesCommand) {
        & $startScript @HermesArgs
    }
    else {
        & $startScript @HermesArgs | Out-Null
    }
    $summary.hermes_started = $true

    $summary.boundary = & $verifyScript

    if (-not $SkipSnapshot) {
        $summary.snapshot = & $snapshotScript
        $summary.snapshot_test = & $snapshotTestScript -SnapshotPath $summary.snapshot
    }

}
finally {
    if (-not $KeepSession) {
        & $sessionScript -Action clear | Out-Null
        $summary.session_cleared = $true
    }
}

[pscustomobject]$summary
