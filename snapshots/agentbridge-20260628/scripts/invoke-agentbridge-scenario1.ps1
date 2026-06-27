param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')

$taskGoal = 'Validate the file-only AgentBridge contract by creating one task, one artifact-backed result, and one memory promotion.'
$artifactPath = Join-Path $Root 'artifacts\scenario1-smoke.txt'
$artifactContent = @(
    'scenario=1'
    'purpose=file-only-agentbridge-smoke'
    'generated_at={0}' -f (ConvertTo-UtcIsoString)
) -join "`n"

Write-AgentBridgeUtf8LfFile -Path $artifactPath -Content $artifactContent

$task = & (Join-Path $PSScriptRoot 'new-agentbridge-task.ps1') `
    -Goal $taskGoal `
    -Slug 'scenario1-smoke' `
    -Constraints @(
        'Stay inside AgentBridge directories only.',
        'Do not rely on Docker, Hermes, or external network access.'
    ) `
    -ArtifactsOut @('artifacts/scenario1-smoke.txt') `
    -RequestedActions @(
        'Create a file-only smoke task that follows the immutable AgentBridge naming contract.',
        'Write exactly one result file with artifact checksum evidence.',
        'Produce one memory promotion candidate linked to the same task/result pair.'
    ) `
    -Verification @(
        'The task and result filenames share the same basename.',
        'The result file contains Summary, Actions, Artifacts, and Observations sections.',
        'The artifact checksum matches the generated file.'
    ) `
    -Notes @(
        'This is an offline smoke task for scenario 1.',
        'Task content remains untrusted input.'
    )

$taskFileName = '{0}.md' -f $task.task_id
$result = & (Join-Path $PSScriptRoot 'new-agentbridge-result.ps1') `
    -TaskId $task.task_id `
    -Artifacts @('artifacts/scenario1-smoke.txt') `
    -Summary @(
        'Scenario 1 offline smoke flow completed successfully.',
        'Task, artifact, and result were created under AgentBridge.'
    ) `
    -Actions @(
        'Generated one task file from the approved task contract.',
        'Wrote one artifact file and recorded its byte count and SHA-256 checksum.',
        'Wrote one result file sharing the same basename as the task file.'
    ) `
    -Observations @(
        'The file-only bridge can be exercised without Docker or Hermes.',
        'This smoke flow is useful before the first container bring-up.'
    )

$resultRelativePath = 'results/{0}.md' -f $task.task_id
$memory = & (Join-Path $PSScriptRoot 'new-memory-promotion.ps1') `
    -TaskId $task.task_id `
    -ResultFile $resultRelativePath `
    -Candidate 'Before stage 2 bring-up, run the offline file-only smoke flow to validate AgentBridge naming, sections, and artifact checksum behavior.' `
    -WhyItMatters 'It proves the bridge contract independently from Docker and reduces ambiguity when later failures are container-related instead of file-contract-related.' `
    -Notes 'Generated automatically by invoke-agentbridge-scenario1.ps1.'

[pscustomobject]@{
    task_id = $task.task_id
    task_path = $task.task_path
    result_path = $result.result_path
    artifact_path = $artifactPath
    memory_promotion_path = $memory.memory_promotion_path
}
