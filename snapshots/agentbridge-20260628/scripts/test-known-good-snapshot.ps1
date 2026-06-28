param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$SnapshotPath
)

$ErrorActionPreference = 'Stop'

function Test-IndexedVolumeBackupRecord {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [string]$BackupFileName,
        [Parameter(Mandatory = $true)]
        [int64]$ExpectedBytes,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedSha256
    )

    $indexPath = Join-Path $Root 'docs\volume-backups\README.md'
    if (-not (Test-Path -LiteralPath $indexPath)) {
        return $false
    }

    $content = Get-Content -Raw -LiteralPath $indexPath
    $escapedName = [regex]::Escape($BackupFileName)
    $escapedHash = [regex]::Escape($ExpectedSha256.ToUpperInvariant())
    $escapedBytes = [regex]::Escape([string]$ExpectedBytes)

    if ($content -notmatch $escapedName) {
        return $false
    }

    if ($content -notmatch $escapedHash) {
        return $false
    }

    return $content -match $escapedBytes
}

if (-not $SnapshotPath) {
    $latest = Get-ChildItem (Join-Path $Root 'docs') -Filter 'known-good-*.json' -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if ($latest) {
        $SnapshotPath = $latest.FullName
    }
}

if (-not $SnapshotPath) {
    [pscustomobject]@{
        snapshot_path = $null
        ok = $false
        issues = @('No known-good snapshot file found.')
    }
    return
}

$issues = @()

if (-not (Test-Path $SnapshotPath)) {
    [pscustomobject]@{
        snapshot_path = $SnapshotPath
        ok = $false
        issues = @("Snapshot path not found: $SnapshotPath")
    }
    return
}

$json = Get-Content -Raw -Path $SnapshotPath | ConvertFrom-Json

$requiredFields = @(
    'created_at',
    'hermes_release_tag',
    'hermes_image_digest',
    'hermes_image_resolution_status',
    'hermes_bootstrap_model',
    'hermes_runtime_image',
    'hermes_runtime_user',
    'hermes_service_uid',
    'hermes_service_gid',
    'compose_sha256',
    'provider_config_hash',
    'provider_base_url',
    'model_primary',
    'model_fallback',
    'hermes_volume_name',
    'volume_backup_path',
    'volume_backup_bytes',
    'volume_backup_sha256',
    'recommended_volume_backup'
)

foreach ($field in $requiredFields) {
    if (-not $json.PSObject.Properties.Name.Contains($field)) {
        $issues += "Missing snapshot field: $field"
        continue
    }

    $value = [string]$json.$field
    if (-not $value) {
        $issues += "Snapshot field is empty: $field"
    }
}

if ($json.compose_sha256 -and ([string]$json.compose_sha256 -notmatch '^[0-9A-Fa-f]{64}$')) {
    $issues += 'compose_sha256 is not a 64-character hex digest.'
}

if ($json.dockerfile_sha256 -and [string]$json.dockerfile_sha256 -ne '' -and ([string]$json.dockerfile_sha256 -notmatch '^[0-9A-Fa-f]{64}$')) {
    $issues += 'dockerfile_sha256 is present but not a 64-character hex digest.'
}

if ($json.provider_config_hash -and ([string]$json.provider_config_hash -notmatch '^[0-9A-Fa-f]{64}$')) {
    $issues += 'provider_config_hash is not a 64-character hex digest.'
}

if ($json.volume_backup_sha256 -and ([string]$json.volume_backup_sha256 -notmatch '^[0-9A-Fa-f]{64}$')) {
    $issues += 'volume_backup_sha256 is not a 64-character hex digest.'
}

if ($json.hermes_image_digest -and ([string]$json.hermes_image_digest -notmatch '@sha256:[0-9A-Fa-f]{64}$')) {
    $issues += 'hermes_image_digest does not look like an image digest reference.'
}

if ($json.hermes_image_resolution_status -and [string]$json.hermes_image_resolution_status -ne 'resolved') {
    $issues += 'hermes_image_resolution_status must be resolved in a known-good snapshot.'
}

$bootstrapModel = [string]$json.hermes_bootstrap_model
if (-not $bootstrapModel) {
    $issues += 'hermes_bootstrap_model is empty.'
}
elseif ($bootstrapModel -eq 'official_root_bootstrap') {
    if ([int]$json.hermes_service_uid -eq 0 -or [int]$json.hermes_service_gid -eq 0) {
        $issues += 'official_root_bootstrap snapshots must record non-root hermes_service_uid and hermes_service_gid.'
    }
}
elseif ($bootstrapModel -in @('direct_non_root', 'derived_non_root')) {
    if ($json.hermes_runtime_user -and ([string]$json.hermes_runtime_user -notmatch '^\d+:\d+$')) {
        $issues += 'direct/derived non-root snapshots must use a numeric hermes_runtime_user.'
    }
}

if ($json.volume_backup_path) {
    $backupPath = Join-Path $Root ([string]$json.volume_backup_path -replace '/', '\')
    if (-not (Test-Path $backupPath)) {
        $indexed = Test-IndexedVolumeBackupRecord `
            -Root $Root `
            -BackupFileName ([System.IO.Path]::GetFileName($backupPath)) `
            -ExpectedBytes ([int64]$json.volume_backup_bytes) `
            -ExpectedSha256 ([string]$json.volume_backup_sha256)

        if (-not $indexed) {
            $issues += "volume_backup_path does not exist: $backupPath"
        }
    }
    else {
        $backupInfo = Get-Item -LiteralPath $backupPath
        if ([int64]$backupInfo.Length -ne [int64]$json.volume_backup_bytes) {
            $issues += 'volume_backup_bytes does not match the current backup file length.'
        }

        $backupHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $backupPath).Hash.ToLowerInvariant()
        if ($backupHash -ne [string]$json.volume_backup_sha256) {
            $issues += 'volume_backup_sha256 does not match the current backup file hash.'
        }
    }
}

[pscustomobject]@{
    snapshot_path = $SnapshotPath
    ok = ($issues.Count -eq 0)
    issues = $issues
}
