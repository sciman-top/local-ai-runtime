param()

$ErrorActionPreference = 'Stop'

function New-TestRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prefix
    )

    $root = Join-Path ([System.IO.Path]::GetTempPath()) ("$Prefix-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    return $root
}

function Remove-TestRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Set-TestFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $directory = Split-Path -Parent $Path
    if ($directory) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }

    Set-Content -LiteralPath $Path -Value $Content -NoNewline
}

function Test-StartHermesDirectForwarding {
    $testRoot = New-TestRoot -Prefix 'agentbridge-start-hermes-arg-forwarding'
    $snapshotRoot = Join-Path $testRoot 'snapshots\agentbridge-20260628'
    $scriptsRoot = Join-Path $snapshotRoot 'scripts'
    $docsRoot = Join-Path $snapshotRoot 'docs'
    $fakeBinRoot = Join-Path $testRoot 'fake-bin'
    $dockerLogPath = Join-Path $testRoot 'docker-log.jsonl'

    try {
        New-Item -ItemType Directory -Force -Path $scriptsRoot, $docsRoot, $fakeBinRoot | Out-Null
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'start-hermes.ps1') -Destination (Join-Path $scriptsRoot 'start-hermes.ps1')
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1') -Destination (Join-Path $scriptsRoot 'AgentBridge.Common.ps1')
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1') -Destination (Join-Path $scriptsRoot 'Resolve-DockerCli.ps1')

        Set-TestFile -Path (Join-Path $docsRoot 'hermes-volume-init.json') -Content '{"accepted_at":"2026-06-28T00:00:00Z"}'
        Set-TestFile -Path (Join-Path $docsRoot 'hermes-runtime.json') -Content '{"runtime_image":"fake/hermes:latest","runtime_user":"official_root_bootstrap","volume_uid":"10001","volume_gid":"10001"}'
        Set-TestFile -Path (Join-Path $fakeBinRoot 'docker.cmd') -Content @"
@echo off
>> "%DOCKER_FAKE_LOG%" echo %*
exit /b 0
"@

        $savedPath = $env:Path
        $savedApiKey = $env:HERMES_PROVIDER_API_KEY
        $savedBaseUrl = $env:HERMES_PROVIDER_BASE_URL
        $savedRuntimeImage = $env:HERMES_RUNTIME_IMAGE
        $savedUid = $env:HERMES_UID
        $savedGid = $env:HERMES_GID
        $savedVolumeName = $env:HERMES_VOLUME_NAME
        $savedDockerFakeLog = $env:DOCKER_FAKE_LOG

        try {
            $env:Path = "$fakeBinRoot;$env:Path"
            $env:DOCKER_FAKE_LOG = $dockerLogPath
            $env:HERMES_PROVIDER_API_KEY = 'fake-key'
            $env:HERMES_PROVIDER_BASE_URL = 'https://example.invalid/v1'
            $env:HERMES_RUNTIME_IMAGE = 'fake/hermes:latest'
            $env:HERMES_UID = '10001'
            $env:HERMES_GID = '10001'
            $env:HERMES_VOLUME_NAME = 'fake-hermes-volume'

            & (Join-Path $scriptsRoot 'start-hermes.ps1') chat -Q -q 'Reply with exactly OK.' | Out-Null
        }
        finally {
            $env:Path = $savedPath
            $env:HERMES_PROVIDER_API_KEY = $savedApiKey
            $env:HERMES_PROVIDER_BASE_URL = $savedBaseUrl
            $env:HERMES_RUNTIME_IMAGE = $savedRuntimeImage
            $env:HERMES_UID = $savedUid
            $env:HERMES_GID = $savedGid
            $env:HERMES_VOLUME_NAME = $savedVolumeName
            $env:DOCKER_FAKE_LOG = $savedDockerFakeLog
        }

        $dockerCalls = @(Get-Content -LiteralPath $dockerLogPath)
        if ($dockerCalls.Count -lt 2) {
            return 'start-hermes direct call did not issue the expected docker invocations.'
        }

        $mainRunLine = [string]$dockerCalls[1]
        if ($mainRunLine -match '\s--tmpfs\s+') {
            return "start-hermes direct call unexpectedly injected tmpfs arguments: $mainRunLine"
        }

        if ($mainRunLine -notmatch 'run-hermes-wrapper\.sh') {
            return 'start-hermes direct call did not reach run-hermes-wrapper.sh.'
        }

        if ($mainRunLine -notmatch 'run-hermes-wrapper\.sh\s+chat\s+-Q\s+-q\s+"?Reply with exactly OK\."?\s*$') {
            return "start-hermes direct forwarding mismatch: $mainRunLine"
        }

        return $null
    }
    finally {
        Remove-TestRoot -Path $testRoot
    }
}

function New-StubBringupHarness {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TestRoot,
        [switch]$CaptureBoundary
    )

    $scriptsRoot = Join-Path $TestRoot 'scripts'
    $startCallPath = Join-Path $TestRoot 'start-call.json'
    $verifyCallPath = Join-Path $TestRoot 'verify-call.json'

    New-Item -ItemType Directory -Force -Path $scriptsRoot | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'invoke-hermes-bringup-once.ps1') -Destination (Join-Path $scriptsRoot 'invoke-hermes-bringup-once.ps1')

    Set-TestFile -Path (Join-Path $scriptsRoot 'manage-hermes-provider-session.ps1') -Content @'
param([string]$Action)
[pscustomobject]@{ action = $Action; ok = $true }
'@
    Set-TestFile -Path (Join-Path $scriptsRoot 'test-agentbridge-contract.ps1') -Content '[pscustomobject]@{ ok = $true }'
    Set-TestFile -Path (Join-Path $scriptsRoot 'test-hermes-bringup-gates.ps1') -Content '[pscustomobject]@{ ready = $true }'
    Set-TestFile -Path (Join-Path $scriptsRoot 'new-known-good-snapshot.ps1') -Content '"fake-snapshot"'
    Set-TestFile -Path (Join-Path $scriptsRoot 'test-known-good-snapshot.ps1') -Content '[pscustomobject]@{ ok = $true }'
    Set-TestFile -Path (Join-Path $scriptsRoot 'start-hermes.ps1') -Content @"
[CmdletBinding(PositionalBinding = `$false)]
param(
    [switch]`$ReadOnlyRootfs,
    [string[]]`$TmpfsMounts = @(),
    [Parameter(ValueFromRemainingArguments = `$true)]
    [string[]]`$HermesArgs
)
`$payload = [pscustomobject]@{
    read_only_rootfs = [bool]`$ReadOnlyRootfs
    tmpfs_mounts = @(`$TmpfsMounts)
    hermes_args = @(`$HermesArgs)
}
Set-Content -LiteralPath '$startCallPath' -Value (`$payload | ConvertTo-Json -Compress) -NoNewline
"@

    if ($CaptureBoundary) {
        Set-TestFile -Path (Join-Path $scriptsRoot 'verify-hermes-boundary.ps1') -Content @"
param(
    [switch]`$ReadOnlyRootfs,
    [string[]]`$TmpfsMounts = @()
)
`$payload = [pscustomobject]@{
    read_only_rootfs = [bool]`$ReadOnlyRootfs
    tmpfs_mounts = @(`$TmpfsMounts)
}
Set-Content -LiteralPath '$verifyCallPath' -Value (`$payload | ConvertTo-Json -Compress) -NoNewline
[pscustomobject]@{
    observed_read_only_rootfs = [bool]`$ReadOnlyRootfs
    tmpfs_targets = @()
}
"@
    }
    else {
        Set-TestFile -Path (Join-Path $scriptsRoot 'verify-hermes-boundary.ps1') -Content '[pscustomobject]@{ observed_read_only_rootfs = $true; tmpfs_targets = @() }'
    }

    return [pscustomobject]@{
        scripts_root = $scriptsRoot
        start_call_path = $startCallPath
        verify_call_path = $verifyCallPath
    }
}

function Test-InvokeBringupForwarding {
    $testRoot = New-TestRoot -Prefix 'agentbridge-invoke-bringup-arg-forwarding'

    try {
        $harness = New-StubBringupHarness -TestRoot $testRoot -CaptureBoundary
        & (Join-Path $harness.scripts_root 'invoke-hermes-bringup-once.ps1') -SkipSnapshot chat -Q -q 'Reply with exactly OK.' | Out-Null

        $startCall = Get-Content -Raw -LiteralPath $harness.start_call_path | ConvertFrom-Json
        $verifyCall = Get-Content -Raw -LiteralPath $harness.verify_call_path | ConvertFrom-Json

        if (@($startCall.tmpfs_mounts).Count -ne 0) {
            return "invoke-hermes-bringup-once unexpectedly forwarded tmpfs mounts: $(@($startCall.tmpfs_mounts) -join ' ')"
        }

        $expectedArgs = @('chat', '-Q', '-q', 'Reply with exactly OK.')
        if ((@($startCall.hermes_args) -join "`n") -ne (@($expectedArgs) -join "`n")) {
            return "invoke-hermes-bringup-once forwarded Hermes args incorrectly. Expected '$($expectedArgs -join ' ')', got '$(@($startCall.hermes_args) -join ' ')'."
        }

        if (@($verifyCall.tmpfs_mounts).Count -ne 0) {
            return "invoke-hermes-bringup-once unexpectedly passed tmpfs mounts to boundary verification: $(@($verifyCall.tmpfs_mounts) -join ' ')"
        }

        return $null
    }
    finally {
        Remove-TestRoot -Path $testRoot
    }
}

function Test-InvokeBringupArrayTmpfsForwarding {
    $testRoot = New-TestRoot -Prefix 'agentbridge-invoke-bringup-tmpfs-array-forwarding'

    try {
        $harness = New-StubBringupHarness -TestRoot $testRoot
        $tmpfsMounts = @('/run:exec', '/tmp')
        & (Join-Path $harness.scripts_root 'invoke-hermes-bringup-once.ps1') -SkipSnapshot -ReadOnlyRootfs -TmpfsMounts $tmpfsMounts chat -Q -q 'Reply with exactly OK.' | Out-Null

        $startCall = Get-Content -Raw -LiteralPath $harness.start_call_path | ConvertFrom-Json
        $observedTmpfs = @($startCall.tmpfs_mounts)
        if ((@($observedTmpfs) -join "`n") -ne (@($tmpfsMounts) -join "`n")) {
            return "invoke-hermes-bringup-once did not preserve tmpfs array forwarding. Expected '$($tmpfsMounts -join ',')', got '$($observedTmpfs -join ',')'."
        }

        return $null
    }
    finally {
        Remove-TestRoot -Path $testRoot
    }
}

$issues = @()

$directIssue = Test-StartHermesDirectForwarding
if ($directIssue) {
    $issues += $directIssue
}

$bringupIssue = Test-InvokeBringupForwarding
if ($bringupIssue) {
    $issues += $bringupIssue
}

$tmpfsForwardIssue = Test-InvokeBringupArrayTmpfsForwarding
if ($tmpfsForwardIssue) {
    $issues += $tmpfsForwardIssue
}

[pscustomobject]@{
    ok = ($issues.Count -eq 0)
    issues = $issues
}
