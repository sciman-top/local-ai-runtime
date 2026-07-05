param(
    [switch]$DisableAutoCommit,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-GateRecord {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Gate,
        [Parameter(Mandatory = $true)]
        [string]$Status,
        [string]$Command = '',
        [string]$Reason = '',
        [string]$AlternativeVerification = '',
        [string]$EvidenceLink = '',
        [string]$ExpiresAt = '',
        [string[]]$KeyOutput = @()
    )

    [pscustomobject]@{
        gate = $Gate
        status = $Status
        command = $Command
        reason = $Reason
        alternative_verification = $AlternativeVerification
        evidence_link = $EvidenceLink
        expires_at = $ExpiresAt
        key_output = $KeyOutput
    }
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    $output = & $Action 2>&1 | ForEach-Object { $_.ToString() }
    $exitCode = $LASTEXITCODE
    return [pscustomobject]@{
        command = $Command
        exit_code = $exitCode
        output = @($output)
    }
}

function Assert-PythonScriptsParse {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $pythonFiles = Get-ChildItem -Path (Join-Path $RepoRoot 'scripts') -Filter *.py -Recurse | Select-Object -ExpandProperty FullName
    if ($pythonFiles.Count -gt 0) {
        & python -m py_compile @pythonFiles
        if ($LASTEXITCODE -ne 0) {
            throw 'python -m py_compile failed'
        }
    }
}

function Assert-PowerShellScriptsParse {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $parseErrors = New-Object System.Collections.Generic.List[string]
    $psFiles = Get-ChildItem -Path (Join-Path $RepoRoot 'scripts') -Filter *.ps1 -Recurse | Select-Object -ExpandProperty FullName
    foreach ($file in $psFiles) {
        $tokens = $null
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($file, [ref]$tokens, [ref]$errors)
        if ($errors) {
            foreach ($error in $errors) {
                $parseErrors.Add(("{0}: {1}" -f $file, $error.Message))
            }
        }
    }

    if ($parseErrors.Count -gt 0) {
        throw ($parseErrors -join [Environment]::NewLine)
    }
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$records = New-Object System.Collections.Generic.List[object]
$failures = New-Object System.Collections.Generic.List[string]

$records.Add((New-GateRecord -Gate 'build' -Status 'gate_na' -Reason 'repo-owned build gate is not defined yet for the generic orchestrator mainline' -AlternativeVerification 'uv run --project .\runtime\host-orchestrator python -m pytest' -EvidenceLink 'docs/plans/orchestrator-implementation-plan.md' -ExpiresAt 'when a repo-owned build gate is introduced'))

$testResult = Invoke-CheckedCommand -Command 'uv run --project .\runtime\host-orchestrator python -m pytest' -Action {
    uv run --project .\runtime\host-orchestrator python -m pytest
}
if ($testResult.exit_code -ne 0) {
    $records.Add((New-GateRecord -Gate 'test' -Status 'fail' -Command $testResult.command -KeyOutput $testResult.output))
    $failures.Add('test')
} else {
    $records.Add((New-GateRecord -Gate 'test' -Status 'pass' -Command $testResult.command -KeyOutput $testResult.output))
}

$contractResult = Invoke-CheckedCommand -Command 'python .\scripts\verify-planning-status.py' -Action {
    python .\scripts\verify-planning-status.py
}
if ($contractResult.exit_code -ne 0) {
    $records.Add((New-GateRecord -Gate 'contract/invariant' -Status 'fail' -Command $contractResult.command -KeyOutput $contractResult.output))
    $failures.Add('contract/invariant')
} else {
    $records.Add((New-GateRecord -Gate 'contract/invariant' -Status 'pass' -Command $contractResult.command -KeyOutput $contractResult.output))
}

$records.Add((New-GateRecord -Gate 'hotspot' -Status 'gate_na' -Reason 'repo-owned hotspot gate is not defined yet for the generic orchestrator mainline' -AlternativeVerification 'repo-side proof is currently limited to verifier + pytest + diff hygiene' -EvidenceLink 'docs/roadmap/orchestrator-roadmap.md' -ExpiresAt 'when a repo-owned hotspot gate is introduced'))

$docsResult = Invoke-CheckedCommand -Command 'python .\scripts\verify-planning-status.py' -Action {
    python .\scripts\verify-planning-status.py
}
if ($docsResult.exit_code -ne 0) {
    $records.Add((New-GateRecord -Gate 'Docs' -Status 'fail' -Command $docsResult.command -KeyOutput $docsResult.output))
    $failures.Add('Docs')
} else {
    $records.Add((New-GateRecord -Gate 'Docs' -Status 'pass' -Command $docsResult.command -KeyOutput $docsResult.output))
}

$scriptsResult = Invoke-CheckedCommand -Command 'python -m py_compile scripts/*.py && parse scripts/*.ps1' -Action {
    Assert-PythonScriptsParse -RepoRoot $repoRoot
    Assert-PowerShellScriptsParse -RepoRoot $repoRoot
    Write-Output 'Python and PowerShell script parsing passed.'
}
if ($scriptsResult.exit_code -ne 0) {
    $records.Add((New-GateRecord -Gate 'Scripts' -Status 'fail' -Command $scriptsResult.command -KeyOutput $scriptsResult.output))
    $failures.Add('Scripts')
} else {
    $records.Add((New-GateRecord -Gate 'Scripts' -Status 'pass' -Command $scriptsResult.command -KeyOutput $scriptsResult.output))
}

$diffResult = Invoke-CheckedCommand -Command 'git diff --check' -Action {
    git diff --check
}
if ($diffResult.exit_code -ne 0) {
    $records.Add((New-GateRecord -Gate 'git diff --check' -Status 'fail' -Command $diffResult.command -KeyOutput $diffResult.output))
    $failures.Add('git diff --check')
} else {
    $records.Add((New-GateRecord -Gate 'git diff --check' -Status 'pass' -Command $diffResult.command -KeyOutput $diffResult.output))
}

if ($Json.IsPresent) {
    $payload = [ordered]@{
        exit_code = if ($failures.Count -gt 0) { 1 } else { 0 }
        summary = [ordered]@{
            entrypoint = 'scripts/governance/preflight.ps1'
            disable_auto_commit = [bool]$DisableAutoCommit
            gates = $records
        }
    }
    Write-Output ($payload | ConvertTo-Json -Depth 8)
}
else {
    Write-Output 'Governance preflight summary:'
    foreach ($record in $records) {
        Write-Output ("- [{0}] {1}" -f $record.status, $record.gate)
        if ($record.command) {
            Write-Output ("  command: {0}" -f $record.command)
        }
        if ($record.reason) {
            Write-Output ("  reason: {0}" -f $record.reason)
        }
        foreach ($line in $record.key_output) {
            Write-Output ("  {0}" -f $line)
        }
    }
}

if ($failures.Count -gt 0) {
    throw ("Governance preflight failed: {0}" -f ($failures -join ', '))
}

exit 0
