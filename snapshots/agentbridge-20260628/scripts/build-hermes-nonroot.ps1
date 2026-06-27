param(
    [Parameter(Mandatory = $true)]
    [string]$BaseImage,
    [string]$Tag = 'agentbridge/hermes-nonroot:local',
    [int]$Uid = 10001,
    [int]$Gid = 10001,
    [switch]$PreferOfficialBootstrap,
    [string]$RuntimeProfilePath
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$dockerfile = Join-Path $root 'Dockerfile.hermes-nonroot'
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')

$dockerCli = Resolve-DockerCli
if (-not $dockerCli) {
    throw 'docker command is unavailable on this host.'
}
Add-DockerCliDirectoryToPath | Out-Null

if (-not $RuntimeProfilePath) {
    $RuntimeProfilePath = Join-Path $root 'docs\hermes-runtime.json'
}

function Get-ImageUserIds {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Image
    )

    $attempts = @(
        @('/bin/sh', '-lc', 'id -u && id -g'),
        @('sh', '-lc', 'id -u && id -g'),
        @('/bin/bash', '-lc', 'id -u && id -g')
    )

    foreach ($attempt in $attempts) {
        try {
            $result = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('run', '--rm', '--entrypoint', $attempt[0], $Image, $attempt[1], $attempt[2]) -AllowFailure
            if ($result.exit_code -ne 0) {
                continue
            }

            $lines = @($result.output.Trim() -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
            if ($lines.Count -ge 2) {
                return [pscustomobject]@{
                    uid = [int]$lines[0].Trim()
                    gid = [int]$lines[1].Trim()
                }
            }
        }
        catch {
            continue
        }
    }

    throw "Unable to determine runtime uid/gid for image: $Image"
}

$inspectConfigUser = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('image', 'inspect', $BaseImage, '--format', '{{.Config.User}}')
$configUser = $inspectConfigUser.output.Trim()
$rootLikeConfigUser = [string]::IsNullOrWhiteSpace($configUser) -or ($configUser -match '^(0(?::0)?|root(?::root)?)$')

if ($rootLikeConfigUser -and -not $PreferOfficialBootstrap) {
    Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @(
        'build',
        '--build-arg', "BASE_IMAGE=$BaseImage",
        '--build-arg', "HERMES_UID=$Uid",
        '--build-arg', "HERMES_GID=$Gid",
        '-t', $Tag,
        '-f', $dockerfile,
        $root
    ) | Out-Null

    $runtimeImage = $Tag
    $runtimeUser = "$Uid`:$Gid"
    $volumeUid = $Uid
    $volumeGid = $Gid
    $derivedImageUsed = $true
}
else {
    $runtimeImage = $BaseImage
    $volumeUid = $Uid
    $volumeGid = $Gid

    if ($rootLikeConfigUser) {
        $runtimeUser = 'root-bootstrap-with-runtime-remap'
        $derivedImageUsed = $false
        $bootstrapModel = 'official_root_bootstrap'
    }
    else {
        $ids = Get-ImageUserIds -Image $BaseImage
        if ($ids.uid -eq 0 -or $ids.gid -eq 0) {
            throw "Official image reports non-root Config.User '$configUser' but resolves to root uid/gid."
        }

        $runtimeUser = $configUser
        $volumeUid = $ids.uid
        $volumeGid = $ids.gid
        $derivedImageUsed = $false
        $bootstrapModel = 'direct_non_root'
    }
}

$runtimeProfile = [ordered]@{
    created_at = (Get-Date).ToUniversalTime().ToString('o')
    base_image = $BaseImage
    base_config_user = $configUser
    derived_image_used = $derivedImageUsed
    bootstrap_model = if ($bootstrapModel) { $bootstrapModel } else { 'derived_non_root' }
    runtime_image = $runtimeImage
    runtime_user = $runtimeUser
    volume_uid = $volumeUid
    volume_gid = $volumeGid
}

$runtimeProfileJson = $runtimeProfile | ConvertTo-Json -Depth 4
Write-AgentBridgeUtf8LfFile -Path $RuntimeProfilePath -Content $runtimeProfileJson

[pscustomobject]@{
    runtime_image = $runtimeImage
    runtime_user = $runtimeUser
    volume_uid = $volumeUid
    volume_gid = $volumeGid
    derived_image_used = $derivedImageUsed
    runtime_profile_path = $RuntimeProfilePath
}
