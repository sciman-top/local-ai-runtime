param()

$ErrorActionPreference = 'Stop'

$prereqScript = Join-Path $PSScriptRoot 'check-docker-prereqs.ps1'
$prereqs = & $prereqScript

if (-not $prereqs.meets_minimum) {
    throw "WSL version $($prereqs.wsl_version) is below the required 2.1.5 minimum."
}

$conflicts = @(
    $prereqs.distro_checks |
        Where-Object { $_.has_conflict } |
        ForEach-Object { "$($_.distro): $($_.docker_paths -join ', ')" }
)

if ($conflicts.Count -gt 0) {
    throw "Found distro-local Docker binaries that should be reviewed before installing Docker Desktop: $($conflicts -join '; ')"
}

winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --disable-interactivity
