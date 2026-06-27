param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$HermesArgs
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$compose = Join-Path $root 'compose.hermes.yml'
$runtimeProfilePath = Join-Path $root 'docs\hermes-runtime.json'
$initEvidencePath = Join-Path $root 'docs\hermes-volume-init.json'
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')

$dockerCli = Resolve-DockerCli
if (-not $dockerCli) {
    throw 'docker command is unavailable on this host.'
}
Add-DockerCliDirectoryToPath | Out-Null

if (-not (Test-Path $initEvidencePath)) {
    throw "Missing init evidence: $initEvidencePath. Run .\\scripts\\init-hermes.ps1 before the first formal Hermes run."
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

$required = @(
    'HERMES_PROVIDER_API_KEY',
    'HERMES_PROVIDER_BASE_URL',
    'HERMES_RUNTIME_IMAGE',
    'HERMES_UID',
    'HERMES_GID'
)

$missing = foreach ($name in $required) {
    if (-not [System.Environment]::GetEnvironmentVariable($name)) { $name }
}

if ($missing) {
    throw "Missing required environment variables: $($missing -join ', ')"
}

if (-not $env:AGENTBRIDGE_PATH) {
    $env:AGENTBRIDGE_PATH = $root
}

if (-not $HermesArgs -or $HermesArgs.Count -eq 0) {
    $HermesArgs = @('chat')
}

$secretFile = Join-Path ([System.IO.Path]::GetTempPath()) ("agentbridge-provider-api-key-{0}.txt" -f ([guid]::NewGuid().ToString('N')))
$bridgeMount = '{0}:/bridge' -f $root
$volumeName = if ($env:HERMES_VOLUME_NAME) { $env:HERMES_VOLUME_NAME } else { 'agentbridge-hermes-data' }
$volumeMount = '{0}:/opt/data' -f $volumeName
$secretMount = '{0}:/run/secrets/provider_api_key:ro' -f $secretFile
$cpus = if ($env:HERMES_CPUS) { $env:HERMES_CPUS } else { '2' }
$memory = if ($env:HERMES_MEM_LIMIT) { $env:HERMES_MEM_LIMIT } else { '2g' }
$pidsLimit = if ($env:HERMES_PIDS_LIMIT) { $env:HERMES_PIDS_LIMIT } else { '256' }
$inferenceModel = if ($env:HERMES_INFERENCE_MODEL) { $env:HERMES_INFERENCE_MODEL } elseif ($env:HERMES_MODEL_PRIMARY) { $env:HERMES_MODEL_PRIMARY } else { 'gpt-5.5' }
$inferenceProvider = if ($env:HERMES_INFERENCE_PROVIDER) { $env:HERMES_INFERENCE_PROVIDER } else { 'openai-api' }
$runDay = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$runMonth = (Get-Date).ToUniversalTime().ToString('yyyy-MM')

$dockerArgs = @(
    'run',
    '--rm',
    '--security-opt', 'no-new-privileges:true',
    '--cpus', $cpus,
    '--memory', $memory,
    '--pids-limit', $pidsLimit,
    '-w', '/bridge',
    '-e', 'AGENTBRIDGE_ROOT=/bridge',
    '-e', 'HERMES_DATA_DIR=/opt/data',
    '-e', 'HERMES_APPROVALS_MODE=manual',
    '-e', "HERMES_UID=$($env:HERMES_UID)",
    '-e', "HERMES_GID=$($env:HERMES_GID)",
    '-e', "HERMES_PROVIDER_BASE_URL=$($env:HERMES_PROVIDER_BASE_URL)",
    '-e', "HERMES_MODEL_PRIMARY=$(if ($env:HERMES_MODEL_PRIMARY) { $env:HERMES_MODEL_PRIMARY } else { 'gpt-5.5' })",
    '-e', "HERMES_MODEL_FALLBACK=$(if ($env:HERMES_MODEL_FALLBACK) { $env:HERMES_MODEL_FALLBACK } else { 'gpt-5.4' })",
    '-e', "HERMES_INFERENCE_MODEL=$inferenceModel",
    '-e', "HERMES_INFERENCE_PROVIDER=$inferenceProvider",
    '-e', 'HERMES_RUN_LOG_DIR=/bridge/logs/hermes-runs',
    '-e', 'HERMES_COST_LOG_DIR=/bridge/logs/cost-rollups',
    '-v', $volumeMount,
    '-v', $bridgeMount,
    '-v', $secretMount,
    $env:HERMES_RUNTIME_IMAGE,
    'sh',
    '/bridge/scripts/run-hermes-wrapper.sh'
) + $HermesArgs

$interactiveCommand = (
    ($HermesArgs.Count -eq 0) -or
    ($HermesArgs[0] -eq 'chat') -or
    ($HermesArgs -contains '--tui') -or
    ($HermesArgs -contains '--cli')
)

try {
    $null = Set-Content -LiteralPath $secretFile -NoNewline -Value $env:HERMES_PROVIDER_API_KEY
    Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @(
        'run',
        '--rm',
        '-v', $bridgeMount,
        'alpine:3.20',
        'sh',
        '-lc',
        "set -eu; mkdir -p /bridge/logs/hermes-runs /bridge/logs/cost-rollups; touch /bridge/logs/hermes-runs/$runDay.jsonl /bridge/logs/cost-rollups/$runMonth.jsonl; chmod 666 /bridge/logs/hermes-runs/$runDay.jsonl /bridge/logs/cost-rollups/$runMonth.jsonl"
    ) | Out-Null

    if ($interactiveCommand) {
        & $dockerCli @dockerArgs
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            throw "Hermes interactive command failed with exit code $exitCode."
        }
    }
    else {
        Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments $dockerArgs | Out-Null
    }
}
finally {
    if (Test-Path -LiteralPath $secretFile) {
        Remove-Item -LiteralPath $secretFile -Force
    }
}
