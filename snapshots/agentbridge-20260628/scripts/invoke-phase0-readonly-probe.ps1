[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$EnvFilePath,
    [string[]]$TmpfsMounts = @('/run:exec', '/tmp'),
    [Nullable[int]]$RuntimeUid,
    [Nullable[int]]$RuntimeGid,
    [string]$RuntimeImageOverride,
    [string]$RuntimeUserOverride,
    [string]$BootstrapModelOverride,
    [string]$ContainerUserOverride,
    [string]$ContainerStartUserOverride,
    [switch]$SkipProbeConfigBootstrap,
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

function Get-ProbeRuntimeIdentity {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BridgeRoot,
        [AllowNull()]
        [Nullable[int]]$RequestedUid,
        [AllowNull()]
        [Nullable[int]]$RequestedGid,
        [string]$RequestedRuntimeImage,
        [string]$RequestedRuntimeUser,
        [string]$RequestedBootstrapModel,
        [string]$RequestedContainerStartUser
    )

    $hasRequestedUid = $null -ne $RequestedUid
    $hasRequestedGid = $null -ne $RequestedGid
    $hasRequestedRuntimeImage = -not [string]::IsNullOrWhiteSpace($RequestedRuntimeImage)
    $hasRequestedRuntimeUser = -not [string]::IsNullOrWhiteSpace($RequestedRuntimeUser)
    $hasRequestedBootstrapModel = -not [string]::IsNullOrWhiteSpace($RequestedBootstrapModel)
    $hasRequestedContainerStartUser = -not [string]::IsNullOrWhiteSpace($RequestedContainerStartUser)

    if ($hasRequestedUid -xor $hasRequestedGid) {
        throw 'RuntimeUid and RuntimeGid must be provided together for the read-only rootfs probe override.'
    }

    $runtimeProfilePath = Join-Path $BridgeRoot 'docs\hermes-runtime.json'
    if (-not (Test-Path -LiteralPath $runtimeProfilePath)) {
        throw "Missing probe runtime profile: $runtimeProfilePath"
    }

    $runtimeProfile = Get-Content -Raw -LiteralPath $runtimeProfilePath | ConvertFrom-Json

    if ([string]::IsNullOrWhiteSpace([string]$runtimeProfile.runtime_image) -and -not $hasRequestedRuntimeImage) {
        throw "Probe runtime profile is missing runtime_image: $runtimeProfilePath"
    }

    if (($null -eq $runtimeProfile.volume_uid) -and -not $hasRequestedUid) {
        throw "Probe runtime profile is missing volume_uid: $runtimeProfilePath"
    }

    if (($null -eq $runtimeProfile.volume_gid) -and -not $hasRequestedGid) {
        throw "Probe runtime profile is missing volume_gid: $runtimeProfilePath"
    }

    $effectiveUid = if ($hasRequestedUid) { [int]$RequestedUid } else { [int]$runtimeProfile.volume_uid }
    $effectiveGid = if ($hasRequestedGid) { [int]$RequestedGid } else { [int]$runtimeProfile.volume_gid }
    $effectiveRuntimeImage = if ($hasRequestedRuntimeImage) { $RequestedRuntimeImage.Trim() } else { [string]$runtimeProfile.runtime_image }
    $effectiveRuntimeUser = if ($hasRequestedRuntimeUser) { $RequestedRuntimeUser.Trim() } else { [string]$runtimeProfile.runtime_user }
    $effectiveBootstrapModel = if ($hasRequestedBootstrapModel) { $RequestedBootstrapModel.Trim() } else { [string]$runtimeProfile.bootstrap_model }
    $profileContainerStartUser = if ($runtimeProfile.PSObject.Properties.Name -contains 'container_start_user') { [string]$runtimeProfile.container_start_user } else { $null }
    $effectiveContainerStartUser = if ($hasRequestedContainerStartUser) { $RequestedContainerStartUser.Trim() } else { $profileContainerStartUser }

    if ($effectiveUid -le 0 -or $effectiveGid -le 0) {
        throw 'Probe runtime uid/gid must be positive integers.'
    }

    if ($hasRequestedUid -or $hasRequestedRuntimeImage -or $hasRequestedRuntimeUser -or $hasRequestedBootstrapModel -or $hasRequestedContainerStartUser) {
        $runtimeProfile.runtime_image = $effectiveRuntimeImage
        $runtimeProfile.runtime_user = $effectiveRuntimeUser
        $runtimeProfile.bootstrap_model = $effectiveBootstrapModel
        if ([string]::IsNullOrWhiteSpace($effectiveContainerStartUser)) {
            if ($runtimeProfile.PSObject.Properties.Name -contains 'container_start_user') {
                $runtimeProfile.PSObject.Properties.Remove('container_start_user')
            }
        }
        else {
            if ($runtimeProfile.PSObject.Properties.Name -contains 'container_start_user') {
                $runtimeProfile.container_start_user = $effectiveContainerStartUser
            }
            else {
                $runtimeProfile | Add-Member -NotePropertyName 'container_start_user' -NotePropertyValue $effectiveContainerStartUser
            }
        }
        $runtimeProfile.volume_uid = $effectiveUid
        $runtimeProfile.volume_gid = $effectiveGid
        Write-AgentBridgeUtf8LfFile -Path $runtimeProfilePath -Content (($runtimeProfile | ConvertTo-Json -Depth 8))
    }

    return [pscustomobject]@{
        runtime_image = $effectiveRuntimeImage
        runtime_user = $effectiveRuntimeUser
        bootstrap_model = $effectiveBootstrapModel
        container_start_user = $effectiveContainerStartUser
        volume_uid = $effectiveUid
        volume_gid = $effectiveGid
        runtime_profile_path = $runtimeProfilePath
        source = if ($hasRequestedUid -or $hasRequestedRuntimeImage -or $hasRequestedRuntimeUser -or $hasRequestedBootstrapModel -or $hasRequestedContainerStartUser) { 'probe_override' } else { 'snapshot_runtime_profile' }
    }
}

function Invoke-ProbeConfigBootstrap {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BridgeRoot,
        [Parameter(Mandatory = $true)]
        [string]$SessionRoot,
        [Parameter(Mandatory = $true)]
        [string]$EnvPath,
        [Parameter(Mandatory = $true)]
        [string]$DockerCliPath,
        [Parameter(Mandatory = $true)]
        [string]$VolumeName,
        [Parameter(Mandatory = $true)]
        [int]$VolumeUid,
        [Parameter(Mandatory = $true)]
        [int]$VolumeGid
    )

    $providerSessionScript = Join-Path $BridgeRoot 'scripts\manage-hermes-provider-session.ps1'
    if (-not (Test-Path -LiteralPath $providerSessionScript)) {
        throw "Missing probe provider session script: $providerSessionScript"
    }

    $providerSession = & $providerSessionScript -Action load -EnvFilePath $EnvPath -SkipBackupPrompt
    if (-not $providerSession.gate_ready) {
        throw 'Probe config bootstrap could not resolve the primary provider session from the env file.'
    }

    $providerBaseUrl = [System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_BASE_URL', 'Process')
    if ([string]::IsNullOrWhiteSpace($providerBaseUrl)) {
        throw 'Probe config bootstrap requires HERMES_PROVIDER_BASE_URL after provider session load.'
    }

    $modelPrimary = [System.Environment]::GetEnvironmentVariable('HERMES_MODEL_PRIMARY', 'Process')
    if ([string]::IsNullOrWhiteSpace($modelPrimary)) {
        $modelPrimary = 'gpt-5.4'
    }

    $bootstrapConfigPath = Join-Path $SessionRoot 'phase0-probe-bootstrap-config.yaml'
    $bootstrapConfigContent = @(
        'model:'
        ('  default: {0}' -f (ConvertTo-YamlQuotedScalar -Value $modelPrimary))
        '  provider: "custom:primary-gateway"'
        '  default_headers:'
        '    User-Agent: "curl/8.7.1"'
        'providers:'
        '  primary-gateway:'
        '    name: "Primary Gateway"'
        ('    base_url: {0}' -f (ConvertTo-YamlQuotedScalar -Value $providerBaseUrl))
        '    key_env: "OPENAI_API_KEY"'
        ('    default_model: {0}' -f (ConvertTo-YamlQuotedScalar -Value $modelPrimary))
    ) -join "`n"
    Write-AgentBridgeUtf8LfFile -Path $bootstrapConfigPath -Content $bootstrapConfigContent

    $initImage = if ($env:HERMES_INIT_IMAGE) { $env:HERMES_INIT_IMAGE } else { 'alpine:3.20' }
    $volumeMount = '{0}:/opt/data' -f $VolumeName
    $configMount = '{0}:/probe-config.yaml:ro' -f $bootstrapConfigPath
    Invoke-AgentBridgeNativeCommand -FilePath $DockerCliPath -Arguments @(
        'run',
        '--rm',
        '--security-opt', 'no-new-privileges:true',
        '-e', "HERMES_VOLUME_UID=$VolumeUid",
        '-e', "HERMES_VOLUME_GID=$VolumeGid",
        '-v', $volumeMount,
        '-v', $configMount,
        $initImage,
        '/bin/sh',
        '-lc',
        'set -eu; cp /probe-config.yaml /opt/data/config.yaml; chown "$HERMES_VOLUME_UID:$HERMES_VOLUME_GID" /opt/data/config.yaml; chmod 640 /opt/data/config.yaml'
    ) | Out-Null

    return [pscustomobject]@{
        applied = $true
        template_path = $bootstrapConfigPath
        model_provider = 'custom:primary-gateway'
        provider_name = 'Primary Gateway'
        provider_key_env = 'OPENAI_API_KEY'
        provider_base_url = $providerBaseUrl
        model_default = $modelPrimary
        user_agent = 'curl/8.7.1'
        provider_session = $providerSession
    }
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

$hasRuntimeProfileOverride = (
    -not [string]::IsNullOrWhiteSpace($RuntimeImageOverride) -or
    -not [string]::IsNullOrWhiteSpace($RuntimeUserOverride) -or
    -not [string]::IsNullOrWhiteSpace($BootstrapModelOverride) -or
    -not [string]::IsNullOrWhiteSpace($ContainerStartUserOverride)
)
$hasRuntimeUidGidOverride = ($null -ne $RuntimeUid -and $null -ne $RuntimeGid)
$normalizedContainerUserOverride = if ([string]::IsNullOrWhiteSpace($ContainerUserOverride)) { $null } else { $ContainerUserOverride.Trim() }

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

$probeRuntimeIdentity = Get-ProbeRuntimeIdentity `
    -BridgeRoot $bridgeRoot `
    -RequestedUid $RuntimeUid `
    -RequestedGid $RuntimeGid `
    -RequestedRuntimeImage $RuntimeImageOverride `
    -RequestedRuntimeUser $RuntimeUserOverride `
    -RequestedBootstrapModel $BootstrapModelOverride `
    -RequestedContainerStartUser $ContainerStartUserOverride

$probeValidationScript = Join-Path $bridgeRoot 'scripts\test-phase0-readonly-probe.ps1'
$initScript = Join-Path $bridgeRoot 'scripts\init-hermes.ps1'
$bringupScript = Join-Path $bridgeRoot 'scripts\invoke-hermes-bringup-once.ps1'

$savedEnv = @{
    HERMES_VOLUME_NAME = [System.Environment]::GetEnvironmentVariable('HERMES_VOLUME_NAME', 'Process')
    HERMES_RUNTIME_IMAGE = [System.Environment]::GetEnvironmentVariable('HERMES_RUNTIME_IMAGE', 'Process')
    HERMES_RUNTIME_USER = [System.Environment]::GetEnvironmentVariable('HERMES_RUNTIME_USER', 'Process')
    HERMES_VOLUME_UID = [System.Environment]::GetEnvironmentVariable('HERMES_VOLUME_UID', 'Process')
    HERMES_VOLUME_GID = [System.Environment]::GetEnvironmentVariable('HERMES_VOLUME_GID', 'Process')
    HERMES_UID = [System.Environment]::GetEnvironmentVariable('HERMES_UID', 'Process')
    HERMES_GID = [System.Environment]::GetEnvironmentVariable('HERMES_GID', 'Process')
    HERMES_PROVIDER_API_KEY = [System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_API_KEY', 'Process')
    HERMES_PROVIDER_ACTIVE_SLOT = [System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_ACTIVE_SLOT', 'Process')
    HERMES_PROVIDER_BASE_URL = [System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_BASE_URL', 'Process')
    HERMES_PROVIDER_SLOT_INDEX = [System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_SLOT_INDEX', 'Process')
    HERMES_MODEL_PRIMARY = [System.Environment]::GetEnvironmentVariable('HERMES_MODEL_PRIMARY', 'Process')
    HERMES_MODEL_FALLBACK = [System.Environment]::GetEnvironmentVariable('HERMES_MODEL_FALLBACK', 'Process')
    HERMES_INFERENCE_MODEL = [System.Environment]::GetEnvironmentVariable('HERMES_INFERENCE_MODEL', 'Process')
    HERMES_INFERENCE_PROVIDER = [System.Environment]::GetEnvironmentVariable('HERMES_INFERENCE_PROVIDER', 'Process')
}

$result = [ordered]@{
    started_at = (Get-Date).ToUniversalTime().ToString('o')
    session_root = $sessionRoot
    bridge_root = $bridgeRoot
    env_file_path = $resolvedEnvFilePath
    volume_name = $volumeName
    requested_read_only_rootfs = $true
    requested_tmpfs_mounts = $normalizedTmpfsMounts
    requested_probe_config_bootstrap = (-not [bool]$SkipProbeConfigBootstrap)
    requested_runtime_uidgid = if ($null -ne $RuntimeUid -and $null -ne $RuntimeGid) {
        [pscustomobject]@{
            uid = [int]$RuntimeUid
            gid = [int]$RuntimeGid
        }
    }
    else {
        $null
    }
    requested_runtime_profile = if ($hasRuntimeProfileOverride -or $hasRuntimeUidGidOverride) {
        [pscustomobject]@{
            runtime_image = if ([string]::IsNullOrWhiteSpace($RuntimeImageOverride)) { $null } else { $RuntimeImageOverride.Trim() }
            runtime_user = if ([string]::IsNullOrWhiteSpace($RuntimeUserOverride)) { $null } else { $RuntimeUserOverride.Trim() }
            bootstrap_model = if ([string]::IsNullOrWhiteSpace($BootstrapModelOverride)) { $null } else { $BootstrapModelOverride.Trim() }
            container_start_user = if ([string]::IsNullOrWhiteSpace($ContainerStartUserOverride)) { $null } else { $ContainerStartUserOverride.Trim() }
            volume_uid = if ($null -ne $RuntimeUid) { [int]$RuntimeUid } else { $null }
            volume_gid = if ($null -ne $RuntimeGid) { [int]$RuntimeGid } else { $null }
        }
    }
    else {
        $null
    }
    requested_container_user_override = $normalizedContainerUserOverride
    effective_runtime_uidgid = $probeRuntimeIdentity
    effective_runtime_profile = $probeRuntimeIdentity
    probe_config_bootstrap = if ($SkipProbeConfigBootstrap) {
        [pscustomobject]@{
            applied = $false
            reason = 'skipped_by_switch'
        }
    }
    else {
        [pscustomobject]@{
            applied = $false
            reason = 'not_started'
        }
    }
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
    [System.Environment]::SetEnvironmentVariable('HERMES_RUNTIME_IMAGE', [string]$probeRuntimeIdentity.runtime_image, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_RUNTIME_USER', [string]$probeRuntimeIdentity.runtime_user, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_VOLUME_UID', [string]$probeRuntimeIdentity.volume_uid, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_VOLUME_GID', [string]$probeRuntimeIdentity.volume_gid, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_UID', [string]$probeRuntimeIdentity.volume_uid, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_GID', [string]$probeRuntimeIdentity.volume_gid, 'Process')

    $validation = & $probeValidationScript
    $result.validation = $validation
    if (-not $validation.ok) {
        throw "Phase 0 read-only probe validation failed: $($validation.issues -join '; ')"
    }

    & $initScript

    if ($SkipProbeConfigBootstrap) {
        $result.probe_config_bootstrap = [pscustomobject]@{
            applied = $false
            reason = 'skipped_by_switch'
        }
    }
    else {
        $result.probe_config_bootstrap = Invoke-ProbeConfigBootstrap `
            -BridgeRoot $bridgeRoot `
            -SessionRoot $sessionRoot `
            -EnvPath $resolvedEnvFilePath `
            -DockerCliPath $dockerCli `
            -VolumeName $volumeName `
            -VolumeUid $probeRuntimeIdentity.volume_uid `
            -VolumeGid $probeRuntimeIdentity.volume_gid
    }

    try {
        $bringupParams = @{
            EnvFilePath = $resolvedEnvFilePath
            ReadOnlyRootfs = $true
            TmpfsMounts = $normalizedTmpfsMounts
            SkipSnapshot = [bool]$SkipSnapshot
        }
        if ($normalizedContainerUserOverride) {
            $bringupParams.ContainerUserOverride = $normalizedContainerUserOverride
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
    [System.Environment]::SetEnvironmentVariable('HERMES_RUNTIME_IMAGE', $savedEnv.HERMES_RUNTIME_IMAGE, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_RUNTIME_USER', $savedEnv.HERMES_RUNTIME_USER, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_VOLUME_UID', $savedEnv.HERMES_VOLUME_UID, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_VOLUME_GID', $savedEnv.HERMES_VOLUME_GID, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_UID', $savedEnv.HERMES_UID, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_GID', $savedEnv.HERMES_GID, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_PROVIDER_API_KEY', $savedEnv.HERMES_PROVIDER_API_KEY, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_PROVIDER_ACTIVE_SLOT', $savedEnv.HERMES_PROVIDER_ACTIVE_SLOT, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_PROVIDER_BASE_URL', $savedEnv.HERMES_PROVIDER_BASE_URL, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_PROVIDER_SLOT_INDEX', $savedEnv.HERMES_PROVIDER_SLOT_INDEX, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_MODEL_PRIMARY', $savedEnv.HERMES_MODEL_PRIMARY, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_MODEL_FALLBACK', $savedEnv.HERMES_MODEL_FALLBACK, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_INFERENCE_MODEL', $savedEnv.HERMES_INFERENCE_MODEL, 'Process')
    [System.Environment]::SetEnvironmentVariable('HERMES_INFERENCE_PROVIDER', $savedEnv.HERMES_INFERENCE_PROVIDER, 'Process')
    $result.finished_at = (Get-Date).ToUniversalTime().ToString('o')
    Write-AgentBridgeUtf8LfFile -Path $reportPath -Content (($result | ConvertTo-Json -Depth 8))
}

[pscustomobject]$result
