[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$EnvFilePath,
    [string]$SourceVolumeName,
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

function Resolve-SourceVolumeName {
    param(
        [AllowNull()]
        [string]$RequestedVolumeName
    )

    if (-not [string]::IsNullOrWhiteSpace($RequestedVolumeName)) {
        return $RequestedVolumeName.Trim()
    }

    if (-not [string]::IsNullOrWhiteSpace($env:HERMES_VOLUME_NAME)) {
        return $env:HERMES_VOLUME_NAME.Trim()
    }

    return 'agentbridge-hermes-data'
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

$runtimeProfilePath = Join-Path $Root 'docs\hermes-runtime.json'
if (-not (Test-Path -LiteralPath $runtimeProfilePath)) {
    throw "Missing runtime profile: $runtimeProfilePath"
}
$runtimeProfile = Get-Content -Raw -LiteralPath $runtimeProfilePath | ConvertFrom-Json

$sourceVolumeNameResolved = Resolve-SourceVolumeName -RequestedVolumeName $SourceVolumeName
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$sessionRoot = Join-Path $repoRoot "private-local\phase0-probes\phase0-cap-drop-$stamp"
$reportPath = Join-Path $sessionRoot 'phase0-cap-drop-probe.json'
$clonedVolumeName = ('agentbridge-hermes-p0-1-{0}' -f ($stamp -replace '[^0-9]', '')).ToLowerInvariant()
$runtimeUser = if ($runtimeProfile.runtime_user) { [string]$runtimeProfile.runtime_user } else { $null }
$bootstrapModel = if ($runtimeProfile.bootstrap_model) { [string]$runtimeProfile.bootstrap_model } else { 'unknown' }
$runtimeImage = if ($runtimeProfile.runtime_image) { [string]$runtimeProfile.runtime_image } else { $null }
$containerStartUser = if ($runtimeProfile.PSObject.Properties.Name -contains 'container_start_user') { [string]$runtimeProfile.container_start_user } else { $null }
$serviceUid = if ($runtimeProfile.volume_uid -ne $null) { [int]$runtimeProfile.volume_uid } else { $null }
$serviceGid = if ($runtimeProfile.volume_gid -ne $null) { [int]$runtimeProfile.volume_gid } else { $null }

if ([string]::IsNullOrWhiteSpace($runtimeImage)) {
    throw "Runtime profile is missing runtime_image: $runtimeProfilePath"
}

New-Item -ItemType Directory -Force -Path $sessionRoot | Out-Null

$savedEnv = @{
    HERMES_VOLUME_NAME = [System.Environment]::GetEnvironmentVariable('HERMES_VOLUME_NAME', 'Process')
}

$result = [ordered]@{
    started_at = (Get-Date).ToUniversalTime().ToString('o')
    session_root = $sessionRoot
    snapshot_root = $Root
    env_file_path = $resolvedEnvFilePath
    requested_cap_drop_all = $true
    requested_read_only_rootfs = $false
    source_volume_name = $sourceVolumeNameResolved
    cloned_volume_name = $clonedVolumeName
    runtime_profile = [pscustomobject]@{
        runtime_image = $runtimeImage
        runtime_user = $runtimeUser
        bootstrap_model = $bootstrapModel
        container_start_user = $containerStartUser
        volume_uid = $serviceUid
        volume_gid = $serviceGid
    }
    clone = $null
    cleanup_volume = [bool]$CleanupVolume
    cleanup_volume_performed = $false
    bringup = $null
    boundary = $null
    observed = $null
    bringup_exception = $null
    ok = $false
    error = $null
    finished_at = $null
}

try {
    $cloneResult = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @(
        'run',
        '--rm',
        '-v', "${sourceVolumeNameResolved}:/source:ro",
        '-v', "${clonedVolumeName}:/target",
        'alpine:3.20',
        'sh',
        '-lc',
        'set -eu; cd /source; tar -cf - . | tar -xf - -C /target'
    )
    $result.clone = [pscustomobject]@{
        ok = ($cloneResult.exit_code -eq 0)
        output = $cloneResult.output.Trim()
    }

    [System.Environment]::SetEnvironmentVariable('HERMES_VOLUME_NAME', $clonedVolumeName, 'Process')

    try {
        $bringup = & (Join-Path $PSScriptRoot 'invoke-hermes-bringup-once.ps1') -EnvFilePath $resolvedEnvFilePath -CapDropAll -SkipSnapshot:$SkipSnapshot
        $result.bringup = $bringup
        $result.boundary = $bringup.boundary
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

    $boundary = $result.boundary
    if ($null -eq $boundary) {
        throw 'Cap-drop probe bring-up summary did not include boundary evidence.'
    }

    $result.observed = [pscustomobject]@{
        requested_cap_drop_all = [bool]$boundary.requested_cap_drop_all
        cap_drop_all_present = [bool]$boundary.cap_drop_all_present
        cap_drop = @($boundary.cap_drop)
        service_uidgid_present = [bool]$boundary.service_uidgid_present
        runtime_user = [string]$boundary.runtime_user
        requested_container_user_override = [string]$boundary.requested_container_user_override
        observed_read_only_rootfs = [bool]$boundary.observed_read_only_rootfs
        root_bootstrap_present = [bool]$boundary.root_bootstrap_present
    }

    $result.ok = (
        [bool]$boundary.requested_cap_drop_all -and
        [bool]$boundary.cap_drop_all_present -and
        [bool]$boundary.service_uidgid_present
    )
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    if ($CleanupVolume) {
        try {
            Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('volume', 'rm', '-f', $clonedVolumeName) -AllowFailure | Out-Null
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
