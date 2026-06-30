param()

$ErrorActionPreference = 'Stop'

$probeScript = Join-Path $PSScriptRoot 'invoke-phase0-readonly-probe.ps1'

$result = [ordered]@{
    ok = $false
    issue = $null
}

function Invoke-ProbeValidationStub {
    param(
        [AllowNull()]
        [int]$RuntimeUid,
        [AllowNull()]
        [int]$RuntimeGid,
        [string]$RuntimeImageOverride,
        [string]$RuntimeUserOverride,
        [string]$BootstrapModelOverride,
        [string]$ContainerUserOverride,
        [string]$ContainerStartUserOverride,
        [switch]$SkipProbeConfigBootstrap
    )

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('agentbridge-p0-2-env-resolution-' + [guid]::NewGuid().ToString('N'))
    $fakeRepoRoot = Join-Path $tempRoot 'repo'
    $fakeSnapshotRoot = Join-Path $fakeRepoRoot 'snapshots\agentbridge-20260628'
    $fakeScriptsRoot = Join-Path $fakeSnapshotRoot 'scripts'
    $fakeDocsRoot = Join-Path $fakeSnapshotRoot 'docs'
    $fakeEnvPath = Join-Path $fakeRepoRoot '.env'
    $fakeValidationScript = Join-Path $fakeScriptsRoot 'test-phase0-readonly-probe.ps1'
    $fakeRuntimeProfilePath = Join-Path $fakeDocsRoot 'hermes-runtime.json'

    New-Item -ItemType Directory -Force -Path $fakeScriptsRoot, $fakeDocsRoot | Out-Null
    Set-Content -LiteralPath $fakeEnvPath -Value "primary_base_url=https://example.invalid/v1`nprimary_key=fake-key`n" -NoNewline
    Set-Content -LiteralPath $fakeValidationScript -Value "[pscustomobject]@{ ok = `$false; issues = @('stub-validation') }" -NoNewline
    Set-Content -LiteralPath $fakeRuntimeProfilePath -Value '{"runtime_image":"fake/hermes:latest","runtime_user":"root-bootstrap-with-runtime-remap","bootstrap_model":"official_root_bootstrap","volume_uid":10001,"volume_gid":10001}' -NoNewline

    try {
        $probeParams = @{
            Root = $fakeSnapshotRoot
            CleanupVolume = $true
        }
        if ($SkipProbeConfigBootstrap) {
            $probeParams.SkipProbeConfigBootstrap = $true
        }
        if ($PSBoundParameters.ContainsKey('RuntimeUid') -and $PSBoundParameters.ContainsKey('RuntimeGid')) {
            $probeParams.RuntimeUid = $RuntimeUid
            $probeParams.RuntimeGid = $RuntimeGid
        }
        if ($PSBoundParameters.ContainsKey('RuntimeImageOverride')) {
            $probeParams.RuntimeImageOverride = $RuntimeImageOverride
        }
        if ($PSBoundParameters.ContainsKey('RuntimeUserOverride')) {
            $probeParams.RuntimeUserOverride = $RuntimeUserOverride
        }
        if ($PSBoundParameters.ContainsKey('BootstrapModelOverride')) {
            $probeParams.BootstrapModelOverride = $BootstrapModelOverride
        }
        if ($PSBoundParameters.ContainsKey('ContainerUserOverride')) {
            $probeParams.ContainerUserOverride = $ContainerUserOverride
        }
        if ($PSBoundParameters.ContainsKey('ContainerStartUserOverride')) {
            $probeParams.ContainerStartUserOverride = $ContainerStartUserOverride
        }

        $probeResult = & $probeScript @probeParams
        $copiedRuntimeProfile = Get-Content -Raw -LiteralPath (Join-Path $probeResult.bridge_root 'docs\hermes-runtime.json') | ConvertFrom-Json

        return [pscustomobject]@{
            probe_result = $probeResult
            fake_env_path = $fakeEnvPath
            copied_runtime_profile = $copiedRuntimeProfile
        }
    }
    finally {
        if (Test-Path -LiteralPath $tempRoot) {
            Remove-Item -LiteralPath $tempRoot -Recurse -Force
        }
    }
}

$defaultCase = Invoke-ProbeValidationStub -SkipProbeConfigBootstrap
if ($defaultCase.probe_result.env_file_path -ne $defaultCase.fake_env_path) {
    $result.issue = 'Repo-local .env was not discovered from the snapshot root.'
}
elseif (@($defaultCase.probe_result.requested_tmpfs_mounts) -join ',' -ne '/run:exec,/tmp') {
    $result.issue = "Unexpected default tmpfs mounts: $(@($defaultCase.probe_result.requested_tmpfs_mounts) -join ',')"
}
elseif ($defaultCase.probe_result.error -notlike '*stub-validation*') {
    $result.issue = "Unexpected default probe result: $($defaultCase.probe_result | ConvertTo-Json -Depth 6 -Compress)"
}
elseif ([int]$defaultCase.copied_runtime_profile.volume_uid -ne 10001 -or [int]$defaultCase.copied_runtime_profile.volume_gid -ne 10001) {
    $result.issue = 'Default probe unexpectedly rewrote the copied runtime profile.'
}
elseif ($defaultCase.probe_result.requested_probe_config_bootstrap -ne $false) {
    $result.issue = 'SkipProbeConfigBootstrap did not disable probe config bootstrap.'
}
elseif ($defaultCase.probe_result.probe_config_bootstrap.applied -ne $false) {
    $result.issue = 'Probe config bootstrap unexpectedly applied when SkipProbeConfigBootstrap was set.'
}
else {
    $overrideCase = Invoke-ProbeValidationStub -RuntimeUid 10000 -RuntimeGid 10000 -SkipProbeConfigBootstrap
    if ($overrideCase.probe_result.error -notlike '*stub-validation*') {
        $result.issue = "Unexpected override probe result: $($overrideCase.probe_result | ConvertTo-Json -Depth 6 -Compress)"
    }
    elseif ([int]$overrideCase.copied_runtime_profile.volume_uid -ne 10000 -or [int]$overrideCase.copied_runtime_profile.volume_gid -ne 10000) {
        $result.issue = 'Runtime uid/gid override did not rewrite the copied runtime profile.'
    }
    elseif (
        [int]$overrideCase.probe_result.requested_runtime_uidgid.uid -ne 10000 -or
        [int]$overrideCase.probe_result.requested_runtime_uidgid.gid -ne 10000
    ) {
        $result.issue = 'Runtime uid/gid override was not recorded in the probe result.'
    }
    elseif (
        [int]$overrideCase.probe_result.effective_runtime_uidgid.volume_uid -ne 10000 -or
        [int]$overrideCase.probe_result.effective_runtime_uidgid.volume_gid -ne 10000
    ) {
        $result.issue = 'Effective runtime uid/gid did not match the override in the probe result.'
    }
    else {
        $runtimeProfileOverrideCase = Invoke-ProbeValidationStub `
            -RuntimeUid 10001 `
            -RuntimeGid 10001 `
            -RuntimeImageOverride 'fake/hermes-nonroot:local' `
            -RuntimeUserOverride '10001:10001' `
            -BootstrapModelOverride 'derived_non_root' `
            -SkipProbeConfigBootstrap

        if ($runtimeProfileOverrideCase.probe_result.error -notlike '*stub-validation*') {
            $result.issue = "Unexpected runtime profile override probe result: $($runtimeProfileOverrideCase.probe_result | ConvertTo-Json -Depth 6 -Compress)"
        }
        elseif ([string]$runtimeProfileOverrideCase.copied_runtime_profile.runtime_image -ne 'fake/hermes-nonroot:local') {
            $result.issue = 'Runtime image override did not rewrite the copied runtime profile.'
        }
        elseif ([string]$runtimeProfileOverrideCase.copied_runtime_profile.runtime_user -ne '10001:10001') {
            $result.issue = 'Runtime user override did not rewrite the copied runtime profile.'
        }
        elseif ([string]$runtimeProfileOverrideCase.copied_runtime_profile.bootstrap_model -ne 'derived_non_root') {
            $result.issue = 'Bootstrap model override did not rewrite the copied runtime profile.'
        }
        elseif ([string]$runtimeProfileOverrideCase.probe_result.requested_runtime_profile.runtime_image -ne 'fake/hermes-nonroot:local') {
            $result.issue = 'Requested runtime profile override was not recorded in the probe result.'
        }
        elseif ([string]$runtimeProfileOverrideCase.probe_result.effective_runtime_profile.runtime_user -ne '10001:10001') {
            $result.issue = 'Effective runtime profile override did not match the requested runtime user.'
        }
        elseif ([string]$runtimeProfileOverrideCase.probe_result.effective_runtime_profile.bootstrap_model -ne 'derived_non_root') {
            $result.issue = 'Effective runtime profile override did not match the requested bootstrap model.'
        }
        elseif ($null -ne $runtimeProfileOverrideCase.probe_result.requested_container_user_override) {
            $result.issue = 'Container user override should be empty when not requested.'
        }
        else {
            $containerUserOverrideCase = Invoke-ProbeValidationStub `
                -RuntimeUid 10001 `
                -RuntimeGid 10001 `
                -RuntimeImageOverride 'fake/hermes-nonroot:local' `
                -RuntimeUserOverride '10001:10001' `
                -BootstrapModelOverride 'derived_non_root' `
                -ContainerUserOverride '0:0' `
                -SkipProbeConfigBootstrap

            if ([string]$containerUserOverrideCase.probe_result.requested_container_user_override -ne '0:0') {
                $result.issue = 'Container user override was not recorded in the probe result.'
            }
            elseif ([string]$containerUserOverrideCase.probe_result.effective_runtime_profile.container_start_user -ne '') {
                $result.issue = 'Container user override should not silently rewrite runtime profile container_start_user.'
            }
            else {
                $containerStartUserCase = Invoke-ProbeValidationStub `
                    -RuntimeUid 10001 `
                    -RuntimeGid 10001 `
                    -RuntimeImageOverride 'fake/hermes-nonroot:local' `
                    -RuntimeUserOverride '10001:10001' `
                    -BootstrapModelOverride 'derived_non_root' `
                    -ContainerStartUserOverride '0:0' `
                    -SkipProbeConfigBootstrap

                if ([string]$containerStartUserCase.copied_runtime_profile.container_start_user -ne '0:0') {
                    $result.issue = 'Container start user override did not rewrite the copied runtime profile.'
                }
                elseif ([string]$containerStartUserCase.probe_result.effective_runtime_profile.container_start_user -ne '0:0') {
                    $result.issue = 'Effective runtime profile did not retain container_start_user override.'
                }
                else {
                    $result.ok = $true
                }
            }
        }
    }
}

[pscustomobject]$result
