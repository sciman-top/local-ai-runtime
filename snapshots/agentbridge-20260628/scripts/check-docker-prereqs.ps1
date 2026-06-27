param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

function Get-WslVersion {
    $raw = wsl --version 2>&1
    $text = (($raw | Out-String) -replace "`0", '')
    $match = [regex]::Match($text, '\d+\.\d+\.\d+(?:\.\d+)?')
    if (-not $match.Success) {
        throw "Unable to parse WSL version from:`n$text"
    }
    [version]$match.Value
}

function Test-DistroDocker {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Distro
    )

    try {
        $raw = wsl -d $Distro -- sh -lc "command -v docker || true; command -v dockerd || true" 2>&1
        $text = (($raw | Out-String) -replace "`0", '').Trim()
        $lines = @($text -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
        $accessDenied = ($text -match 'E_ACCESSDENIED' -or $text -match 'Access is denied' -or $text -match '拒绝访问')

        [pscustomobject]@{
            distro = $Distro
            reachable = (-not $accessDenied)
            docker_paths = if ($accessDenied) { @() } else { $lines }
            has_conflict = ((-not $accessDenied) -and $lines.Count -gt 0)
            access_denied = $accessDenied
            note = if ($accessDenied) { 'WSL access denied in current environment; conflict check not authoritative in this run.' } else { $null }
        }
    }
    catch {
        [pscustomobject]@{
            distro = $Distro
            reachable = $false
            docker_paths = @()
            has_conflict = $false
            access_denied = $false
            note = $_.Exception.Message
        }
    }
}

$wslVersion = Get-WslVersion
$minVersion = [version]'2.1.5'
$enhancedTarget = [version]'2.6.0'
$windowsDocker = @(Get-Command docker, dockerd -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
$distroChecks = @(
    Test-DistroDocker -Distro 'Ubuntu-24.04'
    Test-DistroDocker -Distro 'Ubuntu'
)

[pscustomobject]@{
    agentbridge_root = $root
    wsl_version = $wslVersion.ToString()
    meets_minimum = ($wslVersion -ge $minVersion)
    meets_enhanced_target = ($wslVersion -ge $enhancedTarget)
    windows_docker_paths = $windowsDocker
    distro_checks = $distroChecks
}
