param()

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$compose = Join-Path $root 'compose.hermes.yml'
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')

$dockerCli = Resolve-DockerCli
if (-not $dockerCli) {
    throw 'docker command is unavailable on this host.'
}
Add-DockerCliDirectoryToPath | Out-Null

$runtimeProfilePath = Join-Path $root 'docs\hermes-runtime.json'
$initEvidencePath = Join-Path $root 'docs\hermes-volume-init.json'
$volumeName = if ($env:HERMES_VOLUME_NAME) { $env:HERMES_VOLUME_NAME } else { 'agentbridge-hermes-data' }

if (-not $env:AGENTBRIDGE_PATH) {
    $env:AGENTBRIDGE_PATH = $root
}

if ((-not $env:HERMES_VOLUME_UID -or -not $env:HERMES_VOLUME_GID) -and (Test-Path $runtimeProfilePath)) {
    $runtimeProfile = Get-Content -Raw -Path $runtimeProfilePath | ConvertFrom-Json
    if (-not $env:HERMES_RUNTIME_IMAGE -and $runtimeProfile.runtime_image) {
        $env:HERMES_RUNTIME_IMAGE = [string]$runtimeProfile.runtime_image
    }
    if (-not $env:HERMES_VOLUME_UID -and $runtimeProfile.volume_uid) {
        $env:HERMES_VOLUME_UID = [string]$runtimeProfile.volume_uid
    }
    if (-not $env:HERMES_VOLUME_GID -and $runtimeProfile.volume_gid) {
        $env:HERMES_VOLUME_GID = [string]$runtimeProfile.volume_gid
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
    throw "Missing HERMES_RUNTIME_IMAGE. Generate docs/hermes-runtime.json first or set HERMES_RUNTIME_IMAGE in the current shell."
}

if (-not $env:HERMES_VOLUME_UID -and $env:HERMES_RUNTIME_USER -and $env:HERMES_RUNTIME_USER -match '^(?<uid>\d+):(?<gid>\d+)$') {
    $env:HERMES_VOLUME_UID = $Matches.uid
    $env:HERMES_VOLUME_GID = $Matches.gid
}

if (-not $env:HERMES_VOLUME_GID) {
    $env:HERMES_VOLUME_GID = '10001'
}

if (-not $env:HERMES_VOLUME_UID) {
    $env:HERMES_VOLUME_UID = '10001'
}

if (-not $env:HERMES_UID) {
    $env:HERMES_UID = $env:HERMES_VOLUME_UID
}

if (-not $env:HERMES_GID) {
    $env:HERMES_GID = $env:HERMES_VOLUME_GID
}

$initImage = if ($env:HERMES_INIT_IMAGE) { $env:HERMES_INIT_IMAGE } else { 'alpine:3.20' }
$bridgeMount = '{0}:/bridge:ro' -f $root
$volumeMount = '{0}:/opt/data' -f $volumeName

Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @(
    'run',
    '--rm',
    '--security-opt', 'no-new-privileges:true',
    '-e', "HERMES_VOLUME_UID=$($env:HERMES_VOLUME_UID)",
    '-e', "HERMES_VOLUME_GID=$($env:HERMES_VOLUME_GID)",
    '-v', $volumeMount,
    '-v', $bridgeMount,
    $initImage,
    '/bin/sh',
    '/bridge/scripts/init-hermes-volume.sh'
) | Out-Null

$ownerCheck = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @(
    'run',
    '--rm',
    '--security-opt', 'no-new-privileges:true',
    '-e', "HERMES_VOLUME_UID=$($env:HERMES_VOLUME_UID)",
    '-e', "HERMES_VOLUME_GID=$($env:HERMES_VOLUME_GID)",
    '-v', $volumeMount,
    '-v', $bridgeMount,
    '--entrypoint', '/bin/sh',
    $initImage,
    '-lc',
    'set -eu; stat -c "%u:%g" /opt/data; for d in cache logs profiles sessions; do test -d "/opt/data/$d"; done'
)
$verifiedOwner = ($ownerCheck.output.Trim() -split "`r?`n" | Select-Object -First 1).Trim()
$composeHash = (Get-FileHash -Algorithm SHA256 -Path $compose).Hash

$initEvidence = [ordered]@{
    initialized_at = (Get-Date).ToUniversalTime().ToString('o')
    volume_name = $volumeName
    runtime_user = $env:HERMES_RUNTIME_USER
    volume_uid = [int]$env:HERMES_VOLUME_UID
    volume_gid = [int]$env:HERMES_VOLUME_GID
    verified_owner = $verifiedOwner
    verified_directories = @('cache', 'logs', 'profiles', 'sessions')
    compose_sha256 = $composeHash
}

$initEvidenceJson = $initEvidence | ConvertTo-Json -Depth 4
Write-AgentBridgeUtf8LfFile -Path $initEvidencePath -Content $initEvidenceJson
