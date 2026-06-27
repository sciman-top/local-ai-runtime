param(
    [Parameter(Mandatory = $true)]
    [string]$TaskId,
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [ValidateSet('succeeded', 'partial', 'failed', 'blocked', 'needs_review')]
    [string]$Status = 'succeeded',
    [string]$Runner = 'codex',
    [string]$Runtime = 'codex',
    [string]$Model = 'gpt-5.5',
    [string]$Provider = 'third-party-openai-compatible',
    [string[]]$Summary = @('Offline file-bridge execution completed.'),
    [string[]]$Actions = @('Generated a result file from the approved task contract.'),
    [string[]]$Artifacts = @(),
    [string[]]$Failures = @(),
    [string]$NextAction = 'none',
    [bool]$MemoryCandidate = $true,
    [bool]$HumanReviewRequired = $false,
    [string[]]$Observations = @('This result was produced by the offline smoke flow.'),
    [datetime]$CreatedAt = (Get-Date),
    [datetime]$CompletedAt = (Get-Date)
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')

$resultPath = Join-Path $Root ("results\{0}.md" -f $TaskId)
$artifactList = @($Artifacts)
$artifactRecords = @($artifactList | ForEach-Object { Get-AgentBridgeArtifactRecord -Root $Root -ArtifactPath (Join-Path $Root $_) })
$artifactRelativePaths = @($artifactRecords | ForEach-Object { $_.relative_path })
$failureItems = @($Failures)

$frontMatter = @(
    '---'
    'task_id: {0}' -f $TaskId
    'created_at: {0}' -f (ConvertTo-UtcIsoString -Timestamp $CreatedAt)
    'completed_at: {0}' -f (ConvertTo-UtcIsoString -Timestamp $CompletedAt)
    'status: {0}' -f $Status
    'runner: {0}' -f $Runner
    'runtime: {0}' -f $Runtime
    'model: {0}' -f $Model
    'provider: {0}' -f $Provider
    'artifacts:'
)
$frontMatter += ConvertTo-YamlList -Items $artifactRelativePaths
$frontMatter += @(
    'failures:'
)
$frontMatter += if (@($failureItems).Count -gt 0) { ConvertTo-YamlList -Items $failureItems } else { @('  []') }
$frontMatter += @(
    'next_action: {0}' -f $NextAction
    'memory_candidate: {0}' -f ($(if ($MemoryCandidate) { 'true' } else { 'false' }))
    'human_review_required: {0}' -f ($(if ($HumanReviewRequired) { 'true' } else { 'false' }))
    '---'
)

$body = @(
    '# Summary'
    ''
)
$body += @($Summary | ForEach-Object { '- {0}' -f $_ })
$body += @(
    ''
    '# Actions'
    ''
)
$actionList = @($Actions)
$body += @(for ($i = 0; $i -lt @($actionList).Count; $i++) { '{0}. {1}' -f ($i + 1), $actionList[$i] })
$body += @(
    ''
    '# Artifacts'
    ''
)
$body += if (@($artifactRecords).Count -gt 0) {
    @($artifactRecords | ForEach-Object { '- {0}' -f $_.artifact_line })
}
else {
    @('- none | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
}
$body += @(
    ''
    '# Observations'
    ''
)
$body += @($Observations | ForEach-Object { '- {0}' -f $_ })

$content = ($frontMatter + '' + $body) -join "`n"
Write-AgentBridgeUtf8LfFile -Path $resultPath -Content $content

[pscustomobject]@{
    task_id = $TaskId
    result_path = $resultPath
    artifacts = $artifactRelativePaths
}
