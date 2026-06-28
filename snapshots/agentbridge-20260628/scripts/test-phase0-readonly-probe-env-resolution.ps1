param()

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$probeScript = Join-Path $PSScriptRoot 'invoke-phase0-readonly-probe.ps1'
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('agentbridge-p0-2-env-resolution-' + [guid]::NewGuid().ToString('N'))
$fakeRepoRoot = Join-Path $tempRoot 'repo'
$fakeSnapshotRoot = Join-Path $fakeRepoRoot 'snapshots\agentbridge-20260628'
$fakeScriptsRoot = Join-Path $fakeSnapshotRoot 'scripts'
$fakeEnvPath = Join-Path $fakeRepoRoot '.env'
$fakeValidationScript = Join-Path $fakeScriptsRoot 'test-phase0-readonly-probe.ps1'

New-Item -ItemType Directory -Force -Path $fakeScriptsRoot | Out-Null
Set-Content -LiteralPath $fakeEnvPath -Value "primary_base_url=https://example.invalid/v1`nprimary_key=fake-key`n" -NoNewline
Set-Content -LiteralPath $fakeValidationScript -Value "[pscustomobject]@{ ok = `$false; issues = @('stub-validation') }" -NoNewline

$result = [ordered]@{
    ok = $false
    issue = $null
}

try {
    $probeResult = & $probeScript -Root $fakeSnapshotRoot -CleanupVolume
    if ($probeResult.env_file_path -ne $fakeEnvPath) {
        $result.issue = 'Repo-local .env was not discovered from the snapshot root.'
    }
    elseif (@($probeResult.requested_tmpfs_mounts) -join ',' -ne '/run:exec,/tmp') {
        $result.issue = "Unexpected default tmpfs mounts: $(@($probeResult.requested_tmpfs_mounts) -join ',')"
    }
    elseif ($probeResult.error -like '*stub-validation*') {
        $result.ok = $true
    }
    else {
        $result.issue = "Unexpected probe result: $($probeResult | ConvertTo-Json -Depth 6 -Compress)"
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

[pscustomobject]$result
