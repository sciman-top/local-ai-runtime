param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AgentBridge.Common.ps1')

function Test-LfOnly {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    for ($i = 1; $i -lt $bytes.Length; $i++) {
        if ($bytes[$i - 1] -eq 13 -and $bytes[$i] -eq 10) {
            return $false
        }
    }

    return $true
}

function Get-FrontMatter {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $content = Get-Content -Raw -Path $Path
    $match = [regex]::Match($content, '(?s)^---\n(.*?)\n---\n')
    if (-not $match.Success) {
        throw "Missing YAML front matter: $Path"
    }

    $result = [ordered]@{}
    $currentKey = $null
    foreach ($line in ($match.Groups[1].Value -split "`n")) {
        $trimmed = $line.TrimEnd()
        if (-not $trimmed) {
            continue
        }

        if ($trimmed -match '^(?<key>[A-Za-z0-9_]+):\s*(?<value>.*)$') {
            $currentKey = $Matches.key
            $value = $Matches.value.Trim()
            if ($value -eq '') {
                $result[$currentKey] = @()
            }
            else {
                $result[$currentKey] = $value
            }
            continue
        }

        if ($trimmed -match '^\s*-\s*(?<item>.+)$' -and $currentKey) {
            if ($result[$currentKey] -isnot [System.Collections.IList]) {
                $result[$currentKey] = @()
            }
            $result[$currentKey] += $Matches.item.Trim()
        }
    }

    return $result
}

function Test-RequiredKeys {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$FrontMatter,
        [Parameter(Mandatory = $true)]
        [string[]]$RequiredKeys
    )

    $missing = @($RequiredKeys | Where-Object { -not $FrontMatter.Contains($_) })
    return $missing
}

function Test-ContainsHeadings {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string[]]$Headings
    )

    $content = Get-Content -Raw -Path $Path
    $missing = @()
    foreach ($heading in $Headings) {
        if ($content -notmatch "(?m)^#\s+$([regex]::Escape($heading))\s*$") {
            $missing += $heading
        }
    }
    return $missing
}

function Test-ArtifactLines {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $content = Get-Content -Raw -Path $Path
    return @([regex]::Matches($content, '(?m)^-\s+(?<path>[^\r\n|]+?)\s+\|\s+(?<bytes>\d+)\s+\|\s+(?<sha>[0-9a-f]{64})\s*$'))
}

function Test-MemoryPromotionLinkage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    $content = Get-Content -Raw -Path $Path
    $issues = @()

    $taskMatch = [regex]::Match($content, '(?m)^- Task ids:\s*(?<task>.+?)\s*$')
    $resultMatch = [regex]::Match($content, '(?m)^- Result files:\s*(?<result>.+?)\s*$')

    if (-not $taskMatch.Success) {
        $issues += "Memory promotion missing Task ids line: $Path"
    }

    if (-not $resultMatch.Success) {
        $issues += "Memory promotion missing Result files line: $Path"
    }

    if ($taskMatch.Success) {
        $taskId = $taskMatch.Groups['task'].Value.Trim()
        $taskPath = Join-Path $Root ("tasks\{0}.md" -f $taskId)
        if (-not (Test-Path $taskPath)) {
            $issues += "Memory promotion references missing task: $taskId"
        }
    }

    if ($resultMatch.Success) {
        $resultRelativePath = $resultMatch.Groups['result'].Value.Trim()
        $resultPath = Join-Path $Root $resultRelativePath
        if (-not (Test-Path $resultPath)) {
            $issues += "Memory promotion references missing result: $resultRelativePath"
        }
    }

    return @($issues)
}

$requiredTaskKeys = @(
    'id',
    'created_at',
    'requested_by',
    'source_runtime',
    'source_model',
    'source_provider',
    'goal',
    'constraints',
    'runner',
    'requires_gui',
    'approval_level',
    'artifacts_out'
)

$requiredResultKeys = @(
    'task_id',
    'created_at',
    'completed_at',
    'status',
    'runner',
    'runtime',
    'model',
    'provider',
    'artifacts',
    'failures',
    'next_action',
    'memory_candidate',
    'human_review_required'
)

$approvalLevels = @('safe', 'review', 'manual_only')
$resultStatuses = @('succeeded', 'partial', 'failed', 'blocked', 'needs_review')
$requiredResultHeadings = @('Summary', 'Actions', 'Artifacts', 'Observations')

$contractFiles = @(
    Join-Path $Root 'tasks\_TEMPLATE.md'
    Join-Path $Root 'results\_TEMPLATE.md'
)

$taskDirectory = Join-Path $Root 'tasks'
$resultDirectory = Join-Path $Root 'results'
$memoryDirectory = Join-Path $Root 'memory-promotions'

$issues = @()

foreach ($path in $contractFiles) {
    if (-not (Test-Path $path)) {
        $issues += "Missing contract file: $path"
        continue
    }

    if (-not (Test-LfOnly -Path $path)) {
        $issues += "CRLF detected: $path"
    }
}

$taskMatter = if (Test-Path $contractFiles[0]) { Get-FrontMatter -Path $contractFiles[0] } else { @{} }
$resultMatter = if (Test-Path $contractFiles[1]) { Get-FrontMatter -Path $contractFiles[1] } else { @{} }

$missingTaskKeys = @(Test-RequiredKeys -FrontMatter $taskMatter -RequiredKeys $requiredTaskKeys)
$missingResultKeys = @(Test-RequiredKeys -FrontMatter $resultMatter -RequiredKeys $requiredResultKeys)

if (@($missingTaskKeys).Count -gt 0) {
    $issues += "tasks/_TEMPLATE.md missing keys: $($missingTaskKeys -join ', ')"
}

if (@($missingResultKeys).Count -gt 0) {
    $issues += "results/_TEMPLATE.md missing keys: $($missingResultKeys -join ', ')"
}

if ($taskMatter.Contains('approval_level') -and $approvalLevels -notcontains [string]$taskMatter['approval_level']) {
    $issues += "tasks/_TEMPLATE.md uses unsupported approval_level: $($taskMatter['approval_level'])"
}

if ($resultMatter.Contains('status') -and $resultStatuses -notcontains [string]$resultMatter['status']) {
    $issues += "results/_TEMPLATE.md uses unsupported status: $($resultMatter['status'])"
}

$missingHeadings = if (Test-Path $contractFiles[1]) {
    Test-ContainsHeadings -Path $contractFiles[1] -Headings $requiredResultHeadings
}
else {
    @()
}

if (@($missingHeadings).Count -gt 0) {
    $issues += "results/_TEMPLATE.md missing headings: $($missingHeadings -join ', ')"
}

$resultContent = if (Test-Path $contractFiles[1]) { Get-Content -Raw -Path $contractFiles[1] } else { '' }
if ($resultContent -notmatch '(?m)^-\s+.+\s+\|\s+\d+\s+\|\s+[0-9a-f]{64}\s*$') {
    $issues += 'results/_TEMPLATE.md is missing the required artifact checksum line shape.'
}

$taskFiles = @(
    Get-ChildItem -LiteralPath $taskDirectory -Filter 'T-*.md' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne '_TEMPLATE.md' }
)
$resultFiles = @(
    Get-ChildItem -LiteralPath $resultDirectory -Filter 'T-*.md' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne '_TEMPLATE.md' }
)

$resultLookup = @{}
foreach ($resultFile in $resultFiles) {
    $resultLookup[$resultFile.BaseName] = $resultFile.FullName
}

$taskLookup = @{}
foreach ($taskFile in $taskFiles) {
    $taskLookup[$taskFile.BaseName] = $taskFile.FullName
}

foreach ($taskFile in $taskFiles) {
    if (-not (Test-LfOnly -Path $taskFile.FullName)) {
        $issues += "CRLF detected: $($taskFile.FullName)"
    }

    $taskFrontMatter = Get-FrontMatter -Path $taskFile.FullName
    $missingKeys = @(Test-RequiredKeys -FrontMatter $taskFrontMatter -RequiredKeys $requiredTaskKeys)
    if (@($missingKeys).Count -gt 0) {
        $issues += "$($taskFile.Name) missing keys: $($missingKeys -join ', ')"
    }

    if (-not $resultLookup.ContainsKey($taskFile.BaseName)) {
        $issues += "Missing matching result file for task: $($taskFile.Name)"
        continue
    }

    $resultFilePath = $resultLookup[$taskFile.BaseName]
    if (-not (Test-LfOnly -Path $resultFilePath)) {
        $issues += "CRLF detected: $resultFilePath"
    }

    $resultFrontMatter = Get-FrontMatter -Path $resultFilePath
    $missingResult = @(Test-RequiredKeys -FrontMatter $resultFrontMatter -RequiredKeys $requiredResultKeys)
    if (@($missingResult).Count -gt 0) {
        $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) missing keys: $($missingResult -join ', ')"
    }

    if ([string]$resultFrontMatter['task_id'] -ne $taskFile.BaseName) {
        $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) task_id does not match task basename."
    }

    $status = [string]$resultFrontMatter['status']
    $nextAction = [string]$resultFrontMatter['next_action']
    if ($status -in @('failed', 'blocked', 'needs_review')) {
        if ($nextAction -ne 'none' -and $nextAction -notmatch 'manual' -and $nextAction -notmatch 'human') {
            $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) uses status '$status' but next_action does not reflect manual stop."
        }
    }

    if ($status -eq 'needs_review' -and [string]$resultFrontMatter['human_review_required'] -ne 'true') {
        $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) uses needs_review but human_review_required is not true."
    }

    $missingRuntimeHeadings = Test-ContainsHeadings -Path $resultFilePath -Headings $requiredResultHeadings
    if (@($missingRuntimeHeadings).Count -gt 0) {
        $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) missing headings: $($missingRuntimeHeadings -join ', ')"
    }

    $artifactLines = Test-ArtifactLines -Path $resultFilePath
    foreach ($match in $artifactLines) {
        $relativeArtifactPath = $match.Groups['path'].Value.Trim()
        if ($relativeArtifactPath -eq 'none') {
            continue
        }

        $artifactPath = Join-Path $Root $relativeArtifactPath
        if (-not (Test-Path $artifactPath)) {
            $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) references missing artifact: $relativeArtifactPath"
            continue
        }

        $artifactInfo = Get-AgentBridgeArtifactRecord -Root $Root -ArtifactPath $artifactPath
        if ([string]$artifactInfo.bytes -ne $match.Groups['bytes'].Value) {
            $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) artifact byte count mismatch for $relativeArtifactPath"
        }

        if ($artifactInfo.sha256 -ne $match.Groups['sha'].Value) {
            $issues += "$([System.IO.Path]::GetFileName($resultFilePath)) artifact sha256 mismatch for $relativeArtifactPath"
        }
    }
}

foreach ($resultFile in $resultFiles) {
    if (-not $taskLookup.ContainsKey($resultFile.BaseName)) {
        $issues += "Orphan result file without matching task: $($resultFile.Name)"
    }
}

$memoryFiles = @(
    Get-ChildItem -LiteralPath $memoryDirectory -Filter '*.md' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne '_TEMPLATE.md' }
)

foreach ($memoryFile in $memoryFiles) {
    if (-not (Test-LfOnly -Path $memoryFile.FullName)) {
        $issues += "CRLF detected: $($memoryFile.FullName)"
    }

    $memoryIssues = @(Test-MemoryPromotionLinkage -Path $memoryFile.FullName -Root $Root)
    if ($memoryIssues.Count -gt 0) {
        $issues += $memoryIssues
    }
}

[pscustomobject]@{
    root = $Root
    ok = ($issues.Count -eq 0)
    issues = $issues
}
