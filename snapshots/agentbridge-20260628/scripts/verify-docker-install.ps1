param(
    [string]$ExpectedDistro = 'Ubuntu-24.04'
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')

$prereqScript = Join-Path $PSScriptRoot 'check-docker-prereqs.ps1'
$prereqs = & $prereqScript

function Invoke-DockerCli {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    & $script:DockerCliPath @Args
}

$script:DockerCliPath = Resolve-DockerCli
if (-not $script:DockerCliPath) {
    throw 'docker command is still unavailable on Windows.'
}

$dockerBinDir = Resolve-DockerCredentialHelperDirectory
if ($dockerBinDir) {
    $env:Path = "$dockerBinDir;$env:Path"
}

$helloWindows = Invoke-DockerCli run --rm hello-world 2>&1 | Out-String
$dockerInfo = Invoke-DockerCli info --format '{{json .}}' | ConvertFrom-Json

$wslDockerShim = '/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe'
$wslDockerScript = @'
if command -v docker >/dev/null 2>&1; then
  docker run --rm hello-world
elif [ -x "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" ]; then
  "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" run --rm hello-world
else
  echo "docker command unavailable in distro"
  exit 127
fi
'@

$helloWsl = wsl -d $ExpectedDistro -- sh -lc $wslDockerScript 2>&1 | Out-String
$wslDockerOk = ($helloWsl -match 'Hello from Docker!')

$integrationByInfo = $null
if ($dockerInfo.PSObject.Properties.Name.Contains('WSLIntegrations')) {
    $integrationByInfo = @($dockerInfo.WSLIntegrations | Where-Object { $_.Name -eq $ExpectedDistro }).Count -gt 0
}

$integrationNote = if ($null -ne $integrationByInfo) {
    'Detected via docker info WSLIntegrations.'
}
elseif ($wslDockerOk) {
    'Inferred from successful docker run inside the target distro.'
}
else {
    'Not exposed by docker info and not confirmed by a successful docker run inside the target distro.'
}

[pscustomobject]@{
    agentbridge_root = $prereqs.agentbridge_root
    docker_cli_path = $script:DockerCliPath
    docker_bin_dir = $dockerBinDir
    wsl_version = $prereqs.wsl_version
    windows_docker_ok = ($helloWindows -match 'Hello from Docker!')
    wsl_docker_ok = $wslDockerOk
    expected_distro = $ExpectedDistro
    expected_distro_integration_detected = if ($null -ne $integrationByInfo) { $integrationByInfo } else { $wslDockerOk }
    expected_distro_integration_note = $integrationNote
    hello_windows_excerpt = ($helloWindows.Trim() -split "`r?`n" | Select-Object -First 3)
    hello_wsl_excerpt = ($helloWsl.Trim() -split "`r?`n" | Select-Object -First 3)
}
