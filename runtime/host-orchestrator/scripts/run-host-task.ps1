param(
    [Parameter(Mandatory = $true)]
    [string]$TaskPath,
    [string]$RepoRoot = "",
    [string]$AgentBridgeRoot = "",
    [string]$WorkerProfile = "",
    [string]$RunId = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $resolvedRepoRoot = (Resolve-Path (Join-Path $projectRoot "..\..")).Path
}
else {
    $resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
}

$arguments = @(
    "run",
    "--project",
    $projectRoot,
    "python",
    "-m",
    "host_orchestrator",
    "--repo-root",
    $resolvedRepoRoot,
    "--run-task",
    $TaskPath
)

if (-not [string]::IsNullOrWhiteSpace($AgentBridgeRoot)) {
    $arguments += @("--agentbridge-root", (Resolve-Path $AgentBridgeRoot).Path)
}

if (-not [string]::IsNullOrWhiteSpace($WorkerProfile)) {
    $arguments += @("--worker-profile", $WorkerProfile)
}

if (-not [string]::IsNullOrWhiteSpace($RunId)) {
    $arguments += @("--run-id", $RunId)
}

uv @arguments
