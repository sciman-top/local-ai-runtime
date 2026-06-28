[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$EnvFilePath,
    [string[]]$TmpfsMounts = @('/run:exec', '/tmp'),
    [switch]$SkipSnapshot,
    [switch]$CleanupVolume
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')

function Resolve-ProbeEnvFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SnapshotRoot,
        [AllowNull()]
        [string]$ExplicitPath
    )

    $candidates = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        $candidates.Add($ExplicitPath)
    }

    $repoRoot = Split-Path -Parent (Split-Path -Parent $SnapshotRoot)
    $candidates.Add((Join-Path $repoRoot '.env'))

    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }

        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

function Get-TmpfsTarget {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Specification
    )

    return ($Specification -split ':', 2)[0].Trim()
}

$dockerCli = Resolve-DockerCli
if (-not $dockerCli) {
    throw 'docker command is unavailable on this host.'
}
Add-DockerCliDirectoryToPath | Out-Null

$repoRoot = Split-Path -Parent (Split-Path -Parent $Root)
$resolvedEnvFilePath = Resolve-ProbeEnvFilePath -SnapshotRoot $Root -ExplicitPath $EnvFilePath
if (-not $resolvedEnvFilePath) {
    throw 'No probe EnvFilePath was provided and no ignored repo-local .env could be found.'
}

$normalizedTmpfsMounts = @($TmpfsMounts | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() } | Select-Object -Unique)
if ($normalizedTmpfsMounts.Count -eq 0) {
    throw 'TmpfsMounts cannot be empty for the read-only rootfs probe.'
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$sessionRoot = Join-Path $repoRoot "private-local\phase0-probes\phase0-readonly-rootfs-$stamp"
$bridgeRoot = Join-Path $sessionRoot 'bridge'
$reportPath = Join-Path $sessionRoot 'phase0-readonly-rootfs-probe.json'
$volumeName = ('agentbridge-hermes-p0-2-{0}' -f ($stamp -replace '[^0-9]', '')).ToLowerInvariant()

New-Item -ItemType Directory -Force -Path $sessionRoot | Out-Null
New-Item -ItemType Directory -Force -Path $bridgeRoot | Out-Null

Get-ChildItem -LiteralPath $Root -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $bridgeRoot -Recurse -Force
}

$probeValidationScript = Join-Path $bridgeRoot 'scripts\test-phase0-readonly-probe.ps1'
$initScript = Join-Path $bridgeRoot 'scripts\init-hermes.ps1'
$bringupScript = Join-Path $bridgeRoot 'scripts\invoke-hermes-bringup-once.ps1'

$savedEnv = @{
    HERMES_VOLUME_NAME = [System.Environment]::GetEnvironmentVariable('HERMES_VOLUME_NAME', 'Process')
}

$result = [ordered]@{
    started_at = (Get-Date).ToUniversalTime().ToString('o')
    session_root = $sessionRoot
    bridge_root = $bridgeRoot
    env_file_path = $resolvedEnvFilePath
    volume_name = $volumeName
    requested_read_only_rootfs = $true
    requested_tmpfs_mounts = $normalizedTmpfsMounts
    validation = $null
    init_evidence_path = Join-Path $bridgeRoot 'docs\hermes-volume-init.json'
    bringup = $null
    checks = $null
    bringup_exception = $null
    cleanup_volume = [bool]$CleanupVolume
    cleanup_volume_performed = $false
    ok = $false
    error = $null
    finished_at = $null
}

try {
    [System.Environment]::SetEnvironmentVariable('HERMES_VOLUME_NAME', $volumeName, 'Process')

    $validation = & $probeValidationScript
    $result.validation = $validation
    if (-not $validation.ok) {
        throw "Phase 0 read-only probe validation failed: $($validation.issues -join '; ')"
    }

    & $initScript

    try {
        $bringupParams = @{
            EnvFilePath = $resolvedEnvFilePath
            ReadOnlyRootfs = $true
            TmpfsMounts = $normalizedTmpfsMounts
            SkipSnapshot = [bool]$SkipSnapshot
        }
        $bringupOutputs = @(
            & $bringupScript @bringupParams
        )
        $bringup = if ($bringupOutputs.Count -gt 0) { $bringupOutputs[-1] } else { $null }
        $result.bringup = $bringup
    }
    catch {
        $result.bringup_exception = [pscustomobject]@{
            message = $_.Exception.Message
            type = $_.Exception.GetType().FullName
            script_stack = $_.ScriptStackTrace
            position = $_.InvocationInfo.PositionMessage
        }
        throw
    }

    $boundary = $bringup.boundary
    if ($null -eq $boundary) {
        throw 'Read-only probe bring-up summary did not include boundary evidence.'
    }

    $requiredTmpfsTargets = @($normalizedTmpfsMounts | ForEach-Object { Get-TmpfsTarget -Specification $_ })
    $observedTmpfsTargets = @($boundary.tmpfs_targets)
    $missingTmpfsTargets = @($requiredTmpfsTargets | Where-Object { $_ -notin $observedTmpfsTargets })
    $missingTmpfsTargetCount = @($missingTmpfsTargets).Count

    $checks = [pscustomobject]@{
        service_uidgid_present = [bool]$boundary.service_uidgid_present
        observed_read_only_rootfs = [bool]$boundary.observed_read_only_rootfs
        rootfs_write_blocked = [bool]$boundary.rootfs_write_blocked
        observed_tmpfs_targets = $observedTmpfsTargets
        missing_tmpfs_targets = $missingTmpfsTargets
    }

    $result.checks = $checks
    $result.ok = (
        $checks.service_uidgid_present -and
        $checks.observed_read_only_rootfs -and
        $checks.rootfs_write_blocked -and
        $missingTmpfsTargetCount -eq 0
    )
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    if ($CleanupVolume) {
        try {
            Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('volume', 'rm', '-f', $volumeName) -AllowFailure | Out-Null
            $result.cleanup_volume_performed = $true
        }
        catch {
            $result.cleanup_volume_performed = $false
        }
    }

    [System.Environment]::SetEnvironmentVariable('HERMES_VOLUME_NAME', $savedEnv.HERMES_VOLUME_NAME, 'Process')
    $result.finished_at = (Get-Date).ToUniversalTime().ToString('o')
    Write-AgentBridgeUtf8LfFile -Path $reportPath -Content (($result | ConvertTo-Json -Depth 8))
}

[pscustomobject]$result
