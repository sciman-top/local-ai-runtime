param(
    [string]$ReferencesRoot = 'D:\CODE\external\hermes-agent-references',
    [string[]]$RepoNames = @(
        'hermes-agent',
        'codex',
        'modelcontextprotocol',
        'servers'
    ),
    [string]$OutputDirectory = 'D:\CODE\local-ai-dev-orchestrator\references\updates',
    [switch]$FetchOnly,
    [switch]$SkipDirtyRepos
)

$ErrorActionPreference = 'Stop'

function Invoke-GitText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepositoryPath,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & git -C $RepositoryPath @Arguments 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        $rendered = $Arguments -join ' '
        throw "git -C `"$RepositoryPath`" $rendered failed with exit code $exitCode.`n$($output.TrimEnd())"
    }

    return $output.TrimEnd()
}

function Get-TrimmedErrorMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $normalized = ($Message -replace '\r\n', "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return 'unknown git error'
    }

    $lines = @($normalized -split "`n" | Where-Object { $_ -and $_.Trim() })
    if ($lines.Count -eq 0) {
        return 'unknown git error'
    }

    return $lines[-1].Trim()
}

function New-UtcTimestamp {
    (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
}

function Normalize-RepoNames {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Names
    )

    $normalized = [System.Collections.Generic.List[string]]::new()
    foreach ($name in $Names) {
        if ([string]::IsNullOrWhiteSpace($name)) {
            continue
        }

        foreach ($segment in ($name -split ',')) {
            $candidate = $segment.Trim()
            if ([string]::IsNullOrWhiteSpace($candidate)) {
                continue
            }

            if (-not $normalized.Contains($candidate)) {
                $normalized.Add($candidate)
            }
        }
    }

    return @($normalized)
}

if (-not (Test-Path -LiteralPath $ReferencesRoot)) {
    throw "References root not found: $ReferencesRoot"
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$RepoNames = Normalize-RepoNames -Names $RepoNames

$timestamp = New-UtcTimestamp
$reportPath = Join-Path $OutputDirectory ("reference-refresh-{0}.md" -f $timestamp)
$latestReportPath = Join-Path $OutputDirectory 'reference-refresh-latest.md'
$results = [System.Collections.Generic.List[object]]::new()
$defaultCoreRepos = @('hermes-agent', 'codex', 'modelcontextprotocol', 'servers')
$repoNamesLabel = if (@($RepoNames) -join ',' -eq ($defaultCoreRepos -join ',')) {
    'core-default'
} else {
    'custom'
}

foreach ($repoName in $RepoNames) {
    $repoPath = Join-Path $ReferencesRoot $repoName
    if (-not (Test-Path -LiteralPath $repoPath)) {
        $results.Add([pscustomobject]@{
                repo = $repoName
                path = $repoPath
                status = 'missing'
                branch = $null
                head_before = $null
                head_after = $null
                changed = $false
                ahead_behind = $null
                note = 'repository path not found'
                compare_log = @()
            })
        continue
    }

    $branch = Invoke-GitText -RepositoryPath $repoPath -Arguments @('branch', '--show-current')
    $headBefore = Invoke-GitText -RepositoryPath $repoPath -Arguments @('rev-parse', '--short=10', 'HEAD')
    $statusText = Invoke-GitText -RepositoryPath $repoPath -Arguments @('status', '--short')
    $isDirty = -not [string]::IsNullOrWhiteSpace($statusText)

    if ($isDirty -and $SkipDirtyRepos) {
        $results.Add([pscustomobject]@{
                repo = $repoName
                path = $repoPath
                status = 'skipped-dirty'
                branch = $branch
                head_before = $headBefore
                head_after = $headBefore
                changed = $false
                ahead_behind = $null
                note = 'dirty worktree; skipped by policy'
                compare_log = @()
            })
        continue
    }

    try {
        Invoke-GitText -RepositoryPath $repoPath -Arguments @('fetch', '--prune', 'origin') | Out-Null
    } catch {
        $results.Add([pscustomobject]@{
                repo = $repoName
                path = $repoPath
                status = 'fetch-failed'
                branch = $branch
                head_before = $headBefore
                head_after = $headBefore
                changed = $false
                ahead_behind = $null
                note = Get-TrimmedErrorMessage -Message $_.Exception.Message
                compare_log = @()
            })
        continue
    }

    $pullMode = if ($FetchOnly) { 'fetch-only' } else { 'pull' }
    $pullNote = 'remote refs fetched'
    if (-not $FetchOnly) {
        try {
            Invoke-GitText -RepositoryPath $repoPath -Arguments @('pull', '--ff-only', 'origin', $branch) | Out-Null
        } catch {
            $results.Add([pscustomobject]@{
                    repo = $repoName
                    path = $repoPath
                    status = 'pull-failed'
                    branch = $branch
                    head_before = $headBefore
                    head_after = $headBefore
                    changed = $false
                    ahead_behind = $null
                    note = Get-TrimmedErrorMessage -Message $_.Exception.Message
                    compare_log = @()
                })
            continue
        }
        $pullNote = 'pull --ff-only completed'
    }

    $headAfter = Invoke-GitText -RepositoryPath $repoPath -Arguments @('rev-parse', '--short=10', 'HEAD')
    $changed = ($headBefore -ne $headAfter)
    $aheadBehind = Invoke-GitText -RepositoryPath $repoPath -Arguments @('rev-list', '--left-right', '--count', ("{0}...origin/{1}" -f $branch, $branch))
    $compareLog = @()
    if ($changed) {
        $compareLogRaw = Invoke-GitText -RepositoryPath $repoPath -Arguments @('log', '--oneline', '--decorate', ("{0}..{1}" -f $headBefore, 'HEAD'))
        if (-not [string]::IsNullOrWhiteSpace($compareLogRaw)) {
            $compareLog = @($compareLogRaw -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
        }
    }

    $results.Add([pscustomobject]@{
            repo = $repoName
            path = $repoPath
            status = if ($changed) { 'updated' } else { $pullMode }
            branch = $branch
            head_before = $headBefore
            head_after = $headAfter
            changed = $changed
            ahead_behind = $aheadBehind
            note = $pullNote
            compare_log = $compareLog
        })
}

$lines = [System.Collections.Generic.List[string]]::new()
$modeLabel = if ($FetchOnly) { 'fetch-only' } else { 'pull --ff-only' }
$lines.Add('# 参考仓刷新摘要')
$lines.Add('')
$lines.Add(('生成时间（UTC）：`' + (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') + '`'))
$lines.Add(('模式：`' + $modeLabel + '`'))
$lines.Add(('根目录：`' + $ReferencesRoot + '`'))
$lines.Add(('集合：`' + $repoNamesLabel + '`'))
$lines.Add(('仓列表：`' + (($RepoNames -join ', ') -replace '\\', '/') + '`'))
$lines.Add('')

foreach ($result in $results) {
    $lines.Add(("## {0}" -f $result.repo))
    $lines.Add('')
    $lines.Add(('- 路径：`' + $result.path + '`'))
    if ($result.branch) {
        $lines.Add(('- 分支：`' + $result.branch + '`'))
    }
    $lines.Add(('- 状态：`' + $result.status + '`'))
    if ($result.head_before) {
        $lines.Add(('- 更新前：`' + $result.head_before + '`'))
    }
    if ($result.head_after) {
        $lines.Add(('- 更新后：`' + $result.head_after + '`'))
    }
    if ($result.ahead_behind) {
        $lines.Add(('- ahead/behind：`' + $result.ahead_behind + '`'))
    }
    $lines.Add(("- 说明：{0}" -f $result.note))
    if ($result.compare_log -and $result.compare_log.Count -gt 0) {
        $lines.Add('- 本次更新 commit：')
        foreach ($entry in $result.compare_log) {
            $lines.Add(('  - `' + $entry + '`'))
        }
    }
    $lines.Add('')
}

[System.IO.File]::WriteAllText(
    $reportPath,
    (($lines -join "`n") + "`n"),
    [System.Text.UTF8Encoding]::new($false)
)
[System.IO.File]::WriteAllText(
    $latestReportPath,
    (($lines -join "`n") + "`n"),
    [System.Text.UTF8Encoding]::new($false)
)

[pscustomobject]@{
    references_root = $ReferencesRoot
    output_path = $reportPath
    latest_output_path = $latestReportPath
    repo_set = $repoNamesLabel
    repo_names = $RepoNames
    fetch_only = [bool]$FetchOnly
    skip_dirty_repos = [bool]$SkipDirtyRepos
    results = $results
}
