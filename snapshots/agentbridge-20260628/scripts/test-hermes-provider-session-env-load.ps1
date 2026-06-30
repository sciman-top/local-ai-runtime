param()

$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'manage-hermes-provider-session.ps1'
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('agentbridge-provider-session-env-load-' + [guid]::NewGuid().ToString('N'))
$envPath = Join-Path $tempRoot '.env'
$legacyEnvPath = Join-Path $tempRoot 'legacy.env'
$childScriptPath = Join-Path $tempRoot 'child-load.ps1'

New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
Set-Content -LiteralPath $envPath -Value @'
primary_base_url=https://example.invalid/v1
primary_key=fake-primary-key
backup_base_url=https://backup.example.invalid/v1
backup_key=fake-backup-key
'@ -NoNewline
Set-Content -LiteralPath $legacyEnvPath -Value @'
TEXT_MODEL_MODEL=gpt-5.4
TEXT_MODEL_PRIMARY_MODEL=gpt-5.4
TEXT_MODEL_FALLBACK_MODEL=gpt-5.4
TEXT_MODEL_API_KEY_1=fake-primary-key
TEXT_MODEL_BASE_URL_1=https://example.invalid/v1
TEXT_MODEL_API_KEY_2=fake-backup-key
TEXT_MODEL_BASE_URL_2=https://backup.example.invalid/v1
'@ -NoNewline

$childScript = @"
param([string]`$DotEnvPath)
Get-ChildItem Env:HERMES* -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -LiteralPath ('Env:' + `$_.Name) -ErrorAction SilentlyContinue
}

& '$scriptPath' -Action load -EnvFilePath `$DotEnvPath -SkipBackupPrompt | ConvertTo-Json -Compress -Depth 8
"@
Set-Content -LiteralPath $childScriptPath -Value $childScript -NoNewline

$issues = @()

try {
    $hosts = @(
        @{ name = 'pwsh'; exe = 'pwsh'; preload_agentbridge_common = $false },
        @{ name = 'powershell'; exe = 'powershell.exe'; preload_agentbridge_common = $false },
        @{ name = 'pwsh+strict'; exe = 'pwsh'; preload_agentbridge_common = $true }
    )
    $cases = @(
        @{ name = 'standard'; env_path = $envPath },
        @{ name = 'legacy-indexed'; env_path = $legacyEnvPath }
    )

    foreach ($runtime in $hosts) {
        foreach ($case in $cases) {
            if ($runtime.preload_agentbridge_common) {
                $strictChildPath = Join-Path $tempRoot ('strict-child-' + [guid]::NewGuid().ToString('N') + '.ps1')
                $strictChild = @"
. '$PSScriptRoot\AgentBridge.Common.ps1'
& '$childScriptPath' -DotEnvPath '$($case.env_path)'
"@
                Set-Content -LiteralPath $strictChildPath -Value $strictChild -NoNewline
                $resultJson = & $runtime.exe -NoProfile -NonInteractive -File $strictChildPath 2>&1
                $exitCode = $LASTEXITCODE
                Remove-Item -LiteralPath $strictChildPath -Force
            }
            else {
                $resultJson = & $runtime.exe -NoProfile -NonInteractive -File $childScriptPath -DotEnvPath $case.env_path 2>&1
                $exitCode = $LASTEXITCODE
            }
            if ($exitCode -ne 0) {
                $issues += "manage-hermes-provider-session load from .env failed under $($runtime.name) case=$($case.name) with exit code ${exitCode}: $($resultJson | Out-String)"
            }
            else {
                $rawText = ($resultJson | Out-String).Trim()
                if ([string]::IsNullOrWhiteSpace($rawText)) {
                    $issues += "manage-hermes-provider-session produced no parseable output under $($runtime.name) case=$($case.name)."
                    continue
                }

                try {
                    $result = $rawText | ConvertFrom-Json
                }
                catch {
                    $issues += "manage-hermes-provider-session did not emit JSON under $($runtime.name) case=$($case.name): $rawText"
                    continue
                }
                $loadedSlots = @($result.loaded_slots)

                if (-not $result.gate_ready) {
                    $issues += "manage-hermes-provider-session did not report gate_ready after .env load under $($runtime.name) case=$($case.name)."
                }

                if ($result.active_slot -ne 'primary') {
                    $issues += "Expected active_slot=primary after .env load under $($runtime.name) case=$($case.name), got '$($result.active_slot)'."
                }

                if ($loadedSlots.Count -ne 2 -or $loadedSlots -notcontains 'primary' -or $loadedSlots -notcontains 'backup') {
                    $issues += "Expected loaded_slots to contain primary and backup after .env load under $($runtime.name) case=$($case.name), got '$($loadedSlots -join ',')'."
                }
            }
        }
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

[pscustomobject]@{
    ok = ($issues.Count -eq 0)
    issues = $issues
}
