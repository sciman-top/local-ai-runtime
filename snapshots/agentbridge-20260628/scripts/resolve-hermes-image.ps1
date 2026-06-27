param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,
    [string]$Repository = 'nousresearch/hermes-agent',
    [string]$SourceReleaseTag,
    [string]$SourceReleaseName,
    [string]$ResolutionStatus = 'pending_validation',
    [string]$ResolutionNote,
    [switch]$RegistryOnly,
    [string]$OutFile
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')
. (Join-Path $PSScriptRoot 'Resolve-DockerCli.ps1')
if (-not $OutFile) {
    $OutFile = Join-Path $root 'docs\hermes-image-resolution.json'
}

$dockerCli = Resolve-DockerCli
if (-not $dockerCli) {
    throw 'docker command is unavailable on this host.'
}
Add-DockerCliDirectoryToPath | Out-Null

$imageTag = "{0}:{1}" -f $Repository, $Tag

if (-not $SourceReleaseTag) {
    $SourceReleaseTag = $Tag
}

function Get-DockerRegistryManifestDigest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ImageRepository,
        [Parameter(Mandatory = $true)]
        [string]$ImageTag
    )

    $pythonCommand = @'
import json, re, sys
import requests

repo = sys.argv[1]
tag = sys.argv[2]
accept = 'application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json'
uri = f'https://registry-1.docker.io/v2/{repo}/manifests/{tag}'

initial = requests.get(uri, headers={'Accept': accept}, timeout=30)
challenge = initial.headers.get('www-authenticate', '')
m = re.search(r'Bearer realm=\"([^\"]+)\",service=\"([^\"]+)\",scope=\"([^\"]+)\"', challenge)
if not m:
    raise SystemExit(f'unable to parse bearer challenge: {challenge}')

realm, service, scope = m.groups()
token_response = requests.get(realm, params={'service': service, 'scope': scope}, timeout=30)
token_response.raise_for_status()
token_payload = token_response.json()
token = token_payload.get('token') or token_payload.get('access_token')
if not token:
    raise SystemExit('registry token response did not include token')

manifest = requests.get(
    uri,
    headers={
        'Accept': accept,
        'Authorization': f'Bearer {token}',
    },
    timeout=30,
)
manifest.raise_for_status()
digest = manifest.headers.get('docker-content-digest')
if not digest:
    raise SystemExit('registry manifest response did not include docker-content-digest')

print(digest)
'@

    $result = $pythonCommand | python - $ImageRepository $ImageTag 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw ($result.Trim())
    }

    $digest = $result.Trim()
    if (-not $digest) {
        throw "Docker registry helper returned an empty digest for $ImageRepository`:$ImageTag"
    }

    return $digest
}

$pull = $null
$inspectDigest = $null
$inspectUser = $null
$registryDigestError = $null
$repoDigest = ''
$configUser = ''

try {
    $registryDigest = Get-DockerRegistryManifestDigest -ImageRepository $Repository -ImageTag $Tag
    if ($registryDigest) {
        $repoDigest = '{0}@{1}' -f $Repository, $registryDigest
    }
}
catch {
    $registryDigestError = $_.Exception.Message
}

if (-not $RegistryOnly) {
    $pull = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('pull', $imageTag) -AllowFailure
    $inspectDigest = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('image', 'inspect', $imageTag, '--format', '{{index .RepoDigests 0}}') -AllowFailure
    $inspectUser = Invoke-AgentBridgeNativeCommand -FilePath $dockerCli -Arguments @('image', 'inspect', $imageTag, '--format', '{{.Config.User}}') -AllowFailure

    if (-not $repoDigest -and $inspectDigest.exit_code -eq 0) {
        $repoDigest = $inspectDigest.output.Trim()
    }
    if ($inspectUser.exit_code -eq 0) {
        $configUser = $inspectUser.output.Trim()
    }
}

$status = $ResolutionStatus
if (-not $status) {
    $status = 'pending_validation'
}

$notes = @()
if ($ResolutionNote) {
    $notes += $ResolutionNote
}
if ($registryDigestError) {
    $notes += $registryDigestError
}
if ($pull -and $pull.exit_code -ne 0) {
    $notes += "docker pull failed for $imageTag"
}
if ($inspectDigest -and $inspectDigest.exit_code -ne 0) {
    $notes += "image inspect for repo digest failed for $imageTag"
}
if ($inspectUser -and $inspectUser.exit_code -ne 0) {
    $notes += "image inspect for config user failed for $imageTag"
}
if (-not $repoDigest) {
    $notes += 'repo digest unresolved'
}
if (-not $configUser) {
    $notes += 'config user unresolved'
}

if (-not $repoDigest -or (-not $RegistryOnly -and -not $configUser)) {
    $status = 'blocked'
}
elseif ($repoDigest -and ($RegistryOnly -or $configUser)) {
    $status = 'resolved'
}

$payload = [ordered]@{
    source_release_tag = $SourceReleaseTag
    source_release_name = $SourceReleaseName
    repository = $Repository
    tag = $Tag
    repo_digest = $repoDigest
    config_user = $configUser
    resolution_status = $status
    resolution_notes = $notes
    pull_exit_code = if ($pull) { $pull.exit_code } else { $null }
    inspect_digest_exit_code = if ($inspectDigest) { $inspectDigest.exit_code } else { $null }
    inspect_user_exit_code = if ($inspectUser) { $inspectUser.exit_code } else { $null }
    registry_only = [bool]$RegistryOnly
    resolved_at = (Get-Date).ToUniversalTime().ToString('o')
}

$json = $payload | ConvertTo-Json -Depth 4
$json | Set-Content -NoNewline -Path $OutFile
$json
