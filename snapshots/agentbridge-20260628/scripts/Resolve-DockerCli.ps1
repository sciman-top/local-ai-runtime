Set-StrictMode -Version Latest

function Resolve-DockerCli {
    $candidates = @(
        'docker',
        'docker.exe',
        'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }

    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    if ($machinePath) {
        foreach ($segment in ($machinePath -split ';' | Where-Object { $_ -and $_.Trim() })) {
            $pathCandidate = Join-Path $segment 'docker.exe'
            if (Test-Path $pathCandidate) {
                return $pathCandidate
            }
        }
    }

    return $null
}

function Resolve-DockerCredentialHelperDirectory {
    $default = 'C:\Program Files\Docker\Docker\resources\bin'
    if (Test-Path $default) {
        return $default
    }

    $dockerCli = Resolve-DockerCli
    if ($dockerCli) {
        return Split-Path -Parent $dockerCli
    }

    return $null
}

function Add-DockerCliDirectoryToPath {
    $dockerBinDir = Resolve-DockerCredentialHelperDirectory
    if (-not $dockerBinDir) {
        return $null
    }

    $pathSegments = @($env:Path -split ';' | Where-Object { $_ -and $_.Trim() })
    if ($pathSegments -notcontains $dockerBinDir) {
        $env:Path = "$dockerBinDir;$env:Path"
    }

    return $dockerBinDir
}
