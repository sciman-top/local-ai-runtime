param()

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

try {
    $null = Set-Content -LiteralPath $secretFile -NoNewline -Value $env:HERMES_PROVIDER_API_KEY
    Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @(
        'run',
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
        '-v', $secretMount,
        $env:HERMES_RUNTIME_IMAGE,
        'sleep', '300'
    ) | Out-Null
    $containerResult = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('ps', '-aqf', "name=^$containerName$")
    $containerId = $containerResult.output.Trim()
    if (-not $containerId) {
        throw 'Verification container did not start.'
    }

    $processTable = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('exec', $containerId, 'sh', '-lc', 'ps -eo uid,gid,args')
    Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('exec', $containerId, 'sh', '-lc', 'test -d /opt/data && test -d /bridge && test ! -S /var/run/docker.sock') | Out-Null

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

    $serviceUid = [int]$env:HERMES_UID
    $serviceGid = [int]$env:HERMES_GID
    $processLines = @($processTable.output -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
    $hasServiceUidGid = @($processLines | Where-Object { $_ -match ("^\s*{0}\s+{1}\s+" -f $serviceUid, $serviceGid) }).Count -gt 0
    $hasRootBootstrap = @($processLines | Where-Object { $_ -match '^\s*0\s+0\s+' }).Count -gt 0

    [pscustomobject]@{
        bootstrap_model = if ($env:HERMES_RUNTIME_USER) { $env:HERMES_RUNTIME_USER } else { 'unspecified' }
        service_uid = $serviceUid
        service_gid = $serviceGid
        service_uidgid_present = $hasServiceUidGid
        root_bootstrap_present = $hasRootBootstrap
        process_lines = $processLines
        mount_targets = $mountTargets
        unexpected_mount_targets = $unexpectedTargets
        blocked_mount_sources = $blockedSources
        published_ports = $hostConfig.PortBindings
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
