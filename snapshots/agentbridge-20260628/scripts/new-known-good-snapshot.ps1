param()

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$compose = Join-Path $root 'compose.hermes.yml'
$dockerfile = Join-Path $root 'Dockerfile.hermes-nonroot'
$docs = Join-Path $root 'docs'
$resolutionFile = Join-Path $docs 'hermes-image-resolution.json'
$runtimeProfilePath = Join-Path $docs 'hermes-runtime.json'
$initEvidencePath = Join-Path $docs 'hermes-volume-init.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$outFile = Join-Path $docs "known-good-$stamp.json"
$volumeBackupDir = Join-Path $docs 'volume-backups'
$volumeName = if ($env:HERMES_VOLUME_NAME) { $env:HERMES_VOLUME_NAME } else { 'agentbridge-hermes-data' }
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')

$dockerCli = Resolve-DockerCli
if (-not $dockerCli) {
    throw 'docker command is unavailable on this host.'
}
Add-DockerCliDirectoryToPath | Out-Null

if (-not (Test-Path $resolutionFile)) {
    throw "Missing image resolution file: $resolutionFile"
}

if (-not (Test-Path $runtimeProfilePath)) {
    throw "Missing runtime profile file: $runtimeProfilePath"
}

if (-not (Test-Path $initEvidencePath)) {
    throw "Missing init evidence file: $initEvidencePath"
}

$composeHash = (Get-FileHash -Algorithm SHA256 -Path $compose).Hash
$dockerfileHash = if (Test-Path $dockerfile) { (Get-FileHash -Algorithm SHA256 -Path $dockerfile).Hash } else { $null }
$providerBase = $env:HERMES_PROVIDER_BASE_URL
$primaryModel = if ($env:HERMES_MODEL_PRIMARY) { $env:HERMES_MODEL_PRIMARY } else { 'gpt-5.5' }
$fallbackModel = if ($env:HERMES_MODEL_FALLBACK) { $env:HERMES_MODEL_FALLBACK } else { 'gpt-5.4' }
$resolution = Get-Content $resolutionFile | ConvertFrom-Json
$runtimeProfile = Get-Content $runtimeProfilePath | ConvertFrom-Json
$releaseTag = if ($env:HERMES_RELEASE_TAG) { $env:HERMES_RELEASE_TAG } elseif ($resolution) { $resolution.tag } else { $null }
$imageDigest = if ($env:HERMES_IMAGE_DIGEST) { $env:HERMES_IMAGE_DIGEST } elseif ($resolution) { $resolution.repo_digest } else { $null }
$runtimeImage = if ($env:HERMES_RUNTIME_IMAGE) { $env:HERMES_RUNTIME_IMAGE } else { [string]$runtimeProfile.runtime_image }
$runtimeUser = if ($env:HERMES_RUNTIME_USER) { $env:HERMES_RUNTIME_USER } else { [string]$runtimeProfile.runtime_user }
$bootstrapModel = if ($runtimeProfile.bootstrap_model) { [string]$runtimeProfile.bootstrap_model } else { 'unknown' }
$serviceUid = if ($runtimeProfile.volume_uid -ne $null) { [int]$runtimeProfile.volume_uid } else { $null }
$serviceGid = if ($runtimeProfile.volume_gid -ne $null) { [int]$runtimeProfile.volume_gid } else { $null }

if (-not $resolution.repo_digest -or [string]$resolution.resolution_status -ne 'resolved') {
    throw 'Image resolution is not in a resolved state. Do not create a known-good snapshot from blocked or partial image metadata.'
}

if (-not [System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_API_KEY')) {
    throw 'HERMES_PROVIDER_API_KEY must be present in the current shell before creating a known-good snapshot.'
}

if (-not $providerBase) {
    throw 'HERMES_PROVIDER_BASE_URL must be present in the current shell before creating a known-good snapshot.'
}

$providerHashInput = "{0}|{1}|{2}|{3}" -f $providerBase, $primaryModel, $fallbackModel, $runtimeUser
$providerHashBytes = [System.Text.Encoding]::UTF8.GetBytes($providerHashInput)
$providerHash = [System.BitConverter]::ToString(([System.Security.Cryptography.SHA256]::Create().ComputeHash($providerHashBytes))).Replace('-', '').ToLowerInvariant()

New-Item -ItemType Directory -Force -Path $volumeBackupDir | Out-Null
$backupFileName = "hermes-data-$stamp.tgz"
$backupHostPath = Join-Path $volumeBackupDir $backupFileName

Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('run', '--rm', '-v', "${volumeName}:/source", '-v', "${volumeBackupDir}:/backup", 'alpine:3.20', 'sh', '-lc', "tar -czf /backup/$backupFileName -C /source .") | Out-Null

if (-not (Test-Path $backupHostPath)) {
    throw "Expected volume backup was not created: $backupHostPath"
}

$volumeBackupInfo = Get-Item -LiteralPath $backupHostPath
$volumeBackupHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $backupHostPath).Hash.ToLowerInvariant()

$snapshot = [ordered]@{
    created_at = (Get-Date).ToUniversalTime().ToString('o')
    hermes_release_tag = $releaseTag
    hermes_image_digest = $imageDigest
    hermes_image_resolution_status = $resolution.resolution_status
    hermes_bootstrap_model = $bootstrapModel
    hermes_runtime_image = $runtimeImage
    hermes_runtime_user = $runtimeUser
    hermes_service_uid = $serviceUid
    hermes_service_gid = $serviceGid
    compose_sha256 = $composeHash
    dockerfile_sha256 = $dockerfileHash
    provider_config_hash = $providerHash
    provider_base_url = $providerBase
    model_primary = $primaryModel
    model_fallback = $fallbackModel
    hermes_volume_name = $volumeName
    volume_backup_path = [System.IO.Path]::GetRelativePath($root, $backupHostPath).Replace('\', '/')
    volume_backup_bytes = [int64]$volumeBackupInfo.Length
    volume_backup_sha256 = $volumeBackupHash
    recommended_volume_backup = 'docker run --rm -v hermes_data:/source -v ${PWD}:/backup alpine:3.20 tar -czf /backup/hermes-data-backup.tgz -C /source .'
}

$snapshotJson = $snapshot | ConvertTo-Json -Depth 5
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
Write-AgentBridgeUtf8LfFile -Path $outFile -Content $snapshotJson
$outFile
