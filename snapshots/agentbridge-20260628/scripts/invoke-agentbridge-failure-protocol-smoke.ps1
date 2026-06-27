param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')

$scenarios = @(
    @{
        Slug = 'failure-protocol-failed'
        Status = 'failed'
        NextAction = 'manual triage required'
        HumanReviewRequired = $false
        Summary = @('The task failed and must not auto-retry.')
        Observations = @('Failure protocol smoke for failed status.')
    }
    @{
        Slug = 'failure-protocol-blocked'
        Status = 'blocked'
        NextAction = 'manual unblock required'
        HumanReviewRequired = $false
        Summary = @('The task is blocked on a missing prerequisite and must stop.')
        Observations = @('Failure protocol smoke for blocked status.')
    }
    @{
        Slug = 'failure-protocol-needs-review'
        Status = 'needs_review'
        NextAction = 'manual review required'
        HumanReviewRequired = $true
        Summary = @('The task produced output but must not auto-continue before review.')
        Observations = @('Failure protocol smoke for needs_review status.')
    }
)

$outputs = @()

foreach ($scenario in $scenarios) {
    $task = & (Join-Path $PSScriptRoot 'new-agentbridge-task.ps1') `
        -Goal ("Validate fail-closed handling for status '{0}'." -f $scenario.Status) `
        -Slug $scenario.Slug `
        -Constraints @(
            'This is a file-only failure-protocol smoke task.',
            'No automatic retry or in-place rewrite is allowed.'
        ) `
        -ApprovalLevel 'review' `
        -ArtifactsOut @() `
        -RequestedActions @(
            "Create a result file with status '$($scenario.Status)'.",
            'Make next_action explicitly manual so downstream automation cannot continue silently.'
        ) `
        -Verification @(
            "Result status is '$($scenario.Status)'.",
            'next_action clearly indicates manual handling.',
            'No artifact is required for this failure-protocol smoke.'
        ) `
        -Notes @(
            'This task exists only to validate fail-closed contract behavior.',
            'Task content remains untrusted input.'
        )

    $result = & (Join-Path $PSScriptRoot 'new-agentbridge-result.ps1') `
        -TaskId $task.task_id `
        -Status $scenario.Status `
        -Failures @("Simulated $($scenario.Status) condition for fail-closed verification.") `
        -NextAction $scenario.NextAction `
        -MemoryCandidate $false `
        -HumanReviewRequired $scenario.HumanReviewRequired `
        -Summary $scenario.Summary `
        -Actions @(
            "Generated a result file for status '$($scenario.Status)'.",
            'Verified the task remains one-to-one with a single result file.',
            'Left the next action in manual state to prevent automatic continuation.'
        ) `
        -Observations $scenario.Observations

    $outputs += [pscustomobject]@{
        status = $scenario.Status
        task_id = $task.task_id
        task_path = $task.task_path
        result_path = $result.result_path
    }
}

$outputs
