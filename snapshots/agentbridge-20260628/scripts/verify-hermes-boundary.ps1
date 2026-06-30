param(
    [switch]$ReadOnlyRootfs,
    [switch]$CapDropAll,
    [string[]]$TmpfsMounts = @(),
    [string]$ContainerUserOverride
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$runtimeProfilePath = Join-Path $root 'docs\hermes-runtime.json'
$allowedTargets = @('/bridge', '/opt/data', '/run/secrets/provider_api_key')
$blockedSourcePatterns = @('\.codex', '\.claude', 'AppData\\Local\\Google\\Chrome', 'AppData\\Roaming\\Mozilla', 'Documents\\Codex')
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')

$dockerCli = Resolve-DockerCli
if (-not $dockerCli) {
    throw 'docker command is unavailable on this host.'
}
Add-DockerCliDirectoryToPath | Out-Null

if (-not $env:AGENTBRIDGE_PATH) {
    $env:AGENTBRIDGE_PATH = $root
}

if (Test-Path $runtimeProfilePath) {
    $runtimeProfile = Get-Content -Raw -Path $runtimeProfilePath | ConvertFrom-Json
    if (-not $env:HERMES_RUNTIME_IMAGE -and $runtimeProfile.runtime_image) {
        $env:HERMES_RUNTIME_IMAGE = [string]$runtimeProfile.runtime_image
    }
    if (-not $env:HERMES_RUNTIME_USER -and $runtimeProfile.runtime_user) {
        $env:HERMES_RUNTIME_USER = [string]$runtimeProfile.runtime_user
    }
    $runtimeProfileContainerStartUser = if ($runtimeProfile.PSObject.Properties.Name -contains 'container_start_user') { [string]$runtimeProfile.container_start_user } else { $null }
    if (-not $env:HERMES_CONTAINER_START_USER -and $runtimeProfileContainerStartUser) {
        $env:HERMES_CONTAINER_START_USER = $runtimeProfileContainerStartUser
    }
    if (-not $env:HERMES_UID -and $runtimeProfile.volume_uid) {
        $env:HERMES_UID = [string]$runtimeProfile.volume_uid
    }
    if (-not $env:HERMES_GID -and $runtimeProfile.volume_gid) {
        $env:HERMES_GID = [string]$runtimeProfile.volume_gid
    }
}

if (-not $env:HERMES_RUNTIME_IMAGE) {
    throw 'Set HERMES_RUNTIME_IMAGE before running boundary verification.'
}

if (-not $env:HERMES_UID -or -not $env:HERMES_GID) {
    throw 'Set HERMES_UID and HERMES_GID before running boundary verification.'
}

if (-not $env:HERMES_PROVIDER_BASE_URL) {
    throw 'Set HERMES_PROVIDER_BASE_URL before running boundary verification.'
}

if (-not $env:HERMES_PROVIDER_API_KEY) {
    throw 'Set HERMES_PROVIDER_API_KEY in the current shell before running boundary verification.'
}

$containerName = 'agentbridge-hermes-verify-' + ([guid]::NewGuid().ToString('N').Substring(0, 8))
$secretFile = Join-Path ([System.IO.Path]::GetTempPath()) ("agentbridge-provider-api-key-{0}.txt" -f ([guid]::NewGuid().ToString('N')))
$bridgeMount = '{0}:/bridge' -f $root
$volumeName = if ($env:HERMES_VOLUME_NAME) { $env:HERMES_VOLUME_NAME } else { 'agentbridge-hermes-data' }
$volumeMount = '{0}:/opt/data' -f $volumeName
$secretMount = '{0}:/run/secrets/provider_api_key:ro' -f $secretFile
$cpus = if ($env:HERMES_CPUS) { $env:HERMES_CPUS } else { '2' }
$memory = if ($env:HERMES_MEM_LIMIT) { $env:HERMES_MEM_LIMIT } else { '2g' }
$pidsLimit = if ($env:HERMES_PIDS_LIMIT) { $env:HERMES_PIDS_LIMIT } else { '256' }
$normalizedTmpfsMounts = @($TmpfsMounts | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() })
$normalizedContainerUserOverride = if ([string]::IsNullOrWhiteSpace($ContainerUserOverride)) {
    if ([string]::IsNullOrWhiteSpace($env:HERMES_CONTAINER_START_USER)) { $null } else { $env:HERMES_CONTAINER_START_USER.Trim() }
}
else {
    $ContainerUserOverride.Trim()
}
$observationTimeoutSeconds = 15
$observationPollMilliseconds = 250
# 直接走真实 Hermes chat 入口，避免只观察到 sleep 占位命令。
$serviceProbeArgs = @('sh', '/bridge/scripts/run-hermes-wrapper.sh', 'chat')

try {
    $null = Set-Content -LiteralPath $secretFile -NoNewline -Value $env:HERMES_PROVIDER_API_KEY
    $dockerCommand = 'run'
    $dockerBaseArgs = @(
        '-d',
        '--name', $containerName,
        '--security-opt', 'no-new-privileges:true',
        '--cpus', $cpus,
        '--memory', $memory,
        '--pids-limit', $pidsLimit,
        '-e', "AGENTBRIDGE_ROOT=/bridge",
        '-e', "HERMES_DATA_DIR=/opt/data",
        '-e', "HERMES_APPROVALS_MODE=manual",
        '-e', "HERMES_UID=$($env:HERMES_UID)",
        '-e', "HERMES_GID=$($env:HERMES_GID)",
        '-e', "HERMES_PROVIDER_BASE_URL=$($env:HERMES_PROVIDER_BASE_URL)",
        '-e', "HERMES_MODEL_PRIMARY=$($env:HERMES_MODEL_PRIMARY ? $env:HERMES_MODEL_PRIMARY : 'gpt-5.5')",
        '-e', "HERMES_MODEL_FALLBACK=$($env:HERMES_MODEL_FALLBACK ? $env:HERMES_MODEL_FALLBACK : 'gpt-5.4')",
        '-e', "HERMES_RUN_LOG_DIR=/bridge/logs/hermes-runs",
        '-e', "HERMES_COST_LOG_DIR=/bridge/logs/cost-rollups",
        '-v', $volumeMount,
        '-v', $bridgeMount,
        '-v', $secretMount
    )
    if ($ReadOnlyRootfs) {
        $dockerBaseArgs += '--read-only'
    }

    if ($CapDropAll) {
        $dockerBaseArgs += @('--cap-drop', 'ALL')
    }

    if ($normalizedContainerUserOverride) {
        $dockerBaseArgs += @('--user', $normalizedContainerUserOverride)
    }

    if ($normalizedTmpfsMounts.Count -gt 0) {
        foreach ($tmpfsMount in $normalizedTmpfsMounts) {
            $dockerBaseArgs += @('--tmpfs', $tmpfsMount)
        }
    }
    $dockerRunArgs = @($dockerCommand) + $dockerBaseArgs + @($env:HERMES_RUNTIME_IMAGE) + $serviceProbeArgs
    Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments $dockerRunArgs | Out-Null
    $containerResult = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('ps', '-aqf', "name=^$containerName$")
    $containerId = $containerResult.output.Trim()
    if (-not $containerId) {
        throw 'Verification container did not start.'
    }

    $serviceUid = [int]$env:HERMES_UID
    $serviceGid = [int]$env:HERMES_GID
    $serviceProcessRegex = "^\s*\d+\s+{0}\s+{1}\s+.*(?:^|[\\/ ])\.?venv[\\/ ]bin[\\/ ]hermes\s+chat(?:\s|$)" -f $serviceUid, $serviceGid
    $rootBootstrapRegex = '^\s*\d+\s+0\s+0\s+'
    $processLines = @()
    $matchedServiceLines = @()
    $hasServiceUidGid = $false
    $hasRootBootstrap = $false
    $probeAttempts = 0
    $probeTimedOut = $false
    $probeStopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    while ($true) {
        $probeAttempts++
        $processTable = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('top', $containerId, '-eo', 'pid,uid,gid,args') -AllowFailure
        if ($processTable.exit_code -eq 0) {
            $processLines = @($processTable.output -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
            $matchedServiceLines = @($processLines | Where-Object { $_ -match $serviceProcessRegex })
            $hasServiceUidGid = $matchedServiceLines.Count -gt 0
            $hasRootBootstrap = @($processLines | Where-Object { $_ -match $rootBootstrapRegex }).Count -gt 0
            if ($hasServiceUidGid) {
                break
            }
        }

        if ($probeStopwatch.Elapsed.TotalSeconds -ge $observationTimeoutSeconds) {
            $probeTimedOut = $true
            break
        }

        Start-Sleep -Milliseconds $observationPollMilliseconds
    }
    $probeStopwatch.Stop()

    Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('exec', $containerId, 'sh', '-lc', 'set -eu; test -d /opt/data && test -d /bridge && test ! -S /var/run/docker.sock; touch /run/agentbridge-run-probe; rm -f /run/agentbridge-run-probe; touch /tmp/agentbridge-tmp-probe; rm -f /tmp/agentbridge-tmp-probe') | Out-Null

    $rootfsProbe = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('exec', $containerId, 'sh', '-lc', 'set +e; output=$(touch /.agentbridge-rootfs-probe 2>&1); status=$?; rm -f /.agentbridge-rootfs-probe >/dev/null 2>&1 || true; if [ "$status" -eq 0 ]; then echo writable; else echo blocked; if [ -n "$output" ]; then printf "%s\n" "$output"; fi; fi') -AllowFailure

    $mountsJson = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('inspect', $containerId, '--format', '{{json .Mounts}}')
    $hostConfigJson = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('inspect', $containerId, '--format', '{{json .HostConfig}}')
    $mounts = $mountsJson.output | ConvertFrom-Json
    $hostConfig = $hostConfigJson.output | ConvertFrom-Json

    $mountTargets = @($mounts | ForEach-Object { $_.Destination })
    $unexpectedTargets = @($mountTargets | Where-Object { $_ -notin $allowedTargets })
    $blockedSources = @(
        $mounts |
            Where-Object {
                $source = [string]$_.Source
                foreach ($pattern in $blockedSourcePatterns) {
                    if ($source -match $pattern) {
                        return $true
                    }
                }
                return $false
            } |
            ForEach-Object { $_.Source }
    )

    $tmpfsTargets = @()
    if ($hostConfig.Tmpfs) {
        $tmpfsTargets = @($hostConfig.Tmpfs.PSObject.Properties.Name)
    }

    $rootfsProbeLines = @($rootfsProbe.lines | Where-Object { $_ -and $_.Trim() })
    $rootfsWriteBlocked = ($rootfsProbeLines.Count -gt 0 -and $rootfsProbeLines[0].Trim() -eq 'blocked')

    [pscustomobject]@{
        bootstrap_model = if ($runtimeProfile -and $runtimeProfile.bootstrap_model) { [string]$runtimeProfile.bootstrap_model } else { 'unspecified' }
        runtime_user = if ($env:HERMES_RUNTIME_USER) { $env:HERMES_RUNTIME_USER } elseif ($runtimeProfile.runtime_user) { [string]$runtimeProfile.runtime_user } else { 'unspecified' }
        requested_container_user_override = $normalizedContainerUserOverride
        requested_read_only_rootfs = [bool]$ReadOnlyRootfs
        requested_cap_drop_all = [bool]$CapDropAll
        requested_tmpfs_mounts = $normalizedTmpfsMounts
        observed_read_only_rootfs = [bool]$hostConfig.ReadonlyRootfs
        service_uid = $serviceUid
        service_gid = $serviceGid
        service_uidgid_present = $hasServiceUidGid
        service_uidgid_lines = $matchedServiceLines
        root_bootstrap_present = $hasRootBootstrap
        probe_attempts = $probeAttempts
        probe_wait_seconds = [math]::Round($probeStopwatch.Elapsed.TotalSeconds, 2)
        probe_timed_out = $probeTimedOut
        process_lines = $processLines
        mount_targets = $mountTargets
        unexpected_mount_targets = $unexpectedTargets
        blocked_mount_sources = $blockedSources
        tmpfs_targets = $tmpfsTargets
        run_tmpfs_write_ok = $true
        tmp_tmpfs_write_ok = $true
        rootfs_write_blocked = $rootfsWriteBlocked
        rootfs_probe_lines = $rootfsProbeLines
        published_ports = $hostConfig.PortBindings
        cap_drop = $hostConfig.CapDrop
        cap_drop_all_present = (@($hostConfig.CapDrop) -contains 'ALL')
        nano_cpus = $hostConfig.NanoCpus
        memory_bytes = $hostConfig.Memory
        pids_limit = $hostConfig.PidsLimit
        security_opt = $hostConfig.SecurityOpt
    }
}
finally {
    Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('rm', '-f', $containerName) -AllowFailure | Out-Null
    if (Test-Path -LiteralPath $secretFile) {
        Remove-Item -LiteralPath $secretFile -Force
    }
}
