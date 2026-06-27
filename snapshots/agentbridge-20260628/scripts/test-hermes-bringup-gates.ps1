param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

function New-GateResult {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [bool]$Passed,
        [string]$Evidence,
        [string]$Note
    )

    [pscustomobject]@{
        gate = $Name
        passed = $Passed
        evidence = $Evidence
        note = $Note
    }
}

$composePath = Join-Path $Root 'compose.hermes.yml'
$resolutionPath = Join-Path $Root 'docs\hermes-image-resolution.json'
$runtimeProfilePath = Join-Path $Root 'docs\hermes-runtime.json'
$volumeInitPath = Join-Path $Root 'docs\hermes-volume-init.json'
$contractScript = Join-Path $PSScriptRoot 'test-agentbridge-contract.ps1'

$composeText = if (Test-Path $composePath) { Get-Content -Raw -Path $composePath } else { '' }
$resolution = if (Test-Path $resolutionPath) { Get-Content -Raw -Path $resolutionPath | ConvertFrom-Json } else { $null }
$runtimeProfile = if (Test-Path $runtimeProfilePath) { Get-Content -Raw -Path $runtimeProfilePath | ConvertFrom-Json } else { $null }
$volumeInit = if (Test-Path $volumeInitPath) { Get-Content -Raw -Path $volumeInitPath | ConvertFrom-Json } else { $null }
$contractResult = if (Test-Path $contractScript) { & $contractScript } else { $null }

$gates = @()

$hasStableTag = ($resolution -and $resolution.source_release_tag -and $resolution.tag)
$gates += New-GateResult -Name 'fixed_release_tag' -Passed ([bool]$hasStableTag) -Evidence $resolutionPath -Note 'Requires docs/hermes-image-resolution.json with source release tag plus concrete image tag mapping.'

$hasDigest = ($resolution -and $resolution.repo_digest -and ($resolution.repo_digest -match '@sha256:'))
$resolutionIsResolved = ($resolution -and [string]$resolution.resolution_status -eq 'resolved')
$gates += New-GateResult -Name 'fixed_image_digest' -Passed ([bool]($hasDigest -and $resolutionIsResolved)) -Evidence $resolutionPath -Note 'Requires a resolved image digest plus an explicit resolved status, not just a placeholder tag.'

$hasIndependentKey = [bool][System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_API_KEY')
$gates += New-GateResult -Name 'independent_key' -Passed $hasIndependentKey -Evidence 'HERMES_PROVIDER_API_KEY (current process)' -Note 'This gate only passes when the active independent key is injected into the current shell.'

$hasIndependentBaseUrl = [bool][System.Environment]::GetEnvironmentVariable('HERMES_PROVIDER_BASE_URL')
$gates += New-GateResult -Name 'independent_base_url' -Passed $hasIndependentBaseUrl -Evidence 'HERMES_PROVIDER_BASE_URL (current process)' -Note 'This gate only passes when the active provider base URL is injected into the current shell.'

$hasNoPorts = ($composeText -notmatch '(?m)^\s*ports:\s*$')
$gates += New-GateResult -Name 'no_published_ports' -Passed $hasNoPorts -Evidence $composePath -Note 'The Compose file must not publish ports.'

$hasNoCommunitySkills = (($composeText -notmatch 'Skills Hub') -and ($composeText -notmatch 'community skills'))
$gates += New-GateResult -Name 'no_community_skills' -Passed $hasNoCommunitySkills -Evidence $composePath -Note 'v1 must not enable community skill installation.'

$hasNoDockerSocket = ($composeText -notmatch '/var/run/docker\.sock')
$gates += New-GateResult -Name 'no_docker_socket' -Passed $hasNoDockerSocket -Evidence $composePath -Note 'The Docker socket must not be mounted.'

$hasNarrowMounts = (
    ($composeText -match 'target:\s+/bridge') -and
    ($composeText -match 'hermes_data:/opt/data') -and
    ($composeText -notmatch 'target:\s+/mnt') -and
    ($composeText -notmatch 'target:\s+/workspace') -and
    ($composeText -notmatch 'target:\s+/root')
)
$gates += New-GateResult -Name 'no_broad_mounts' -Passed $hasNarrowMounts -Evidence $composePath -Note 'Only /bridge and /opt/data should be mounted for v1.'

$hasResourceLimits = (
    ($composeText -match '(?m)^\s*cpus:\s+') -and
    ($composeText -match '(?m)^\s*mem_limit:\s+') -and
    ($composeText -match '(?m)^\s*pids_limit:\s+')
)
$gates += New-GateResult -Name 'resource_limits' -Passed $hasResourceLimits -Evidence $composePath -Note 'cpus, mem_limit, and pids_limit must be present.'

$runtimeUser = if ($runtimeProfile) { [string]$runtimeProfile.runtime_user } else { $null }
$bootstrapModel = if ($runtimeProfile) { [string]$runtimeProfile.bootstrap_model } else { $null }
$runtimeUid = if ($runtimeProfile -and $runtimeProfile.volume_uid -ne $null) { [int]$runtimeProfile.volume_uid } else { $null }
$runtimeGid = if ($runtimeProfile -and $runtimeProfile.volume_gid -ne $null) { [int]$runtimeProfile.volume_gid } else { $null }
$hasServiceLevelDrop = (
    $runtimeProfile -and
    $runtimeUid -ne $null -and
    $runtimeGid -ne $null -and
    $runtimeUid -ne 0 -and
    $runtimeGid -ne 0 -and
    (
        $bootstrapModel -eq 'official_root_bootstrap' -or
        (
            -not [string]::IsNullOrWhiteSpace($runtimeUser) -and
            $bootstrapModel -eq 'direct_non_root'
        ) -or
        (
            -not [string]::IsNullOrWhiteSpace($runtimeUser) -and
            $runtimeUser -match '^\d+:\d+$'
        )
    )
)
$gates += New-GateResult -Name 'service_runtime_uidgid' -Passed $hasServiceLevelDrop -Evidence $runtimeProfilePath -Note 'Requires docs/hermes-runtime.json with either direct non-root runtime or official root-bootstrap plus non-root HERMES_UID/HERMES_GID.'

$hasVolumeInitEvidence = (
    $volumeInit -and
    [string]$volumeInit.verified_owner -eq ('{0}:{1}' -f $runtimeUid, $runtimeGid) -and
    @($volumeInit.verified_directories).Count -ge 4
)
$gates += New-GateResult -Name 'volume_init_complete' -Passed $hasVolumeInitEvidence -Evidence $volumeInitPath -Note 'Requires docs/hermes-volume-init.json produced after the one-shot init container completes.'

$contractOk = ($contractResult -and $contractResult.ok -eq $true)
$gates += New-GateResult -Name 'agentbridge_contract_clean' -Passed $contractOk -Evidence (Join-Path $Root 'scripts\test-agentbridge-contract.ps1') -Note 'A dirty bridge should fail bring-up preflight.'

[pscustomobject]@{
    root = $Root
    ready = (@($gates | Where-Object { -not $_.passed }).Count -eq 0)
    gates = $gates
}
