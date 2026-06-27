param(
    [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$DestinationRoot = 'C:\Users\sciman\Documents\AgentBridge',
    [switch]$PruneExtraneous
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $SourceRoot)) {
    throw "Source root not found: $SourceRoot"
}

$requiredChildren = @(
    'compose.hermes.yml',
    'Dockerfile.hermes-nonroot',
    'README.md',
    'docs',
    'scripts',
    'tasks',
    'results',
    'skills-drafts',
    'memory-promotions',
    'artifacts',
    'logs'
)

$missing = @($requiredChildren | Where-Object { -not (Test-Path (Join-Path $SourceRoot $_)) })
if ($missing.Count -gt 0) {
    throw "Source root is missing required AgentBridge entries: $($missing -join ', ')"
}

if (-not (Test-Path $DestinationRoot)) {
    throw "Destination root not found: $DestinationRoot"
}

$sourceEntries = Get-ChildItem -LiteralPath $SourceRoot -Force
foreach ($entry in $sourceEntries) {
    Copy-Item -LiteralPath $entry.FullName -Destination $DestinationRoot -Recurse -Force
}

$prunedFiles = 0
$prunedDirectories = 0

if ($PruneExtraneous) {
    $sourceFiles = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    Get-ChildItem -LiteralPath $SourceRoot -Recurse -Force -File | ForEach-Object {
        $null = $sourceFiles.Add([System.IO.Path]::GetRelativePath($SourceRoot, $_.FullName))
    }

    Get-ChildItem -LiteralPath $DestinationRoot -Recurse -Force -File |
        ForEach-Object {
            $relative = [System.IO.Path]::GetRelativePath($DestinationRoot, $_.FullName)
            if (-not $sourceFiles.Contains($relative)) {
                Remove-Item -LiteralPath $_.FullName -Force
                $prunedFiles++
            }
        }

    $sourceDirectories = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    Get-ChildItem -LiteralPath $SourceRoot -Recurse -Force -Directory | ForEach-Object {
        $null = $sourceDirectories.Add([System.IO.Path]::GetRelativePath($SourceRoot, $_.FullName))
    }

    Get-ChildItem -LiteralPath $DestinationRoot -Recurse -Force -Directory |
        Sort-Object { $_.FullName.Length } -Descending |
        ForEach-Object {
            $relative = [System.IO.Path]::GetRelativePath($DestinationRoot, $_.FullName)
            if (-not $sourceDirectories.Contains($relative)) {
                $hasChildren = @(Get-ChildItem -LiteralPath $_.FullName -Force).Count -gt 0
                if (-not $hasChildren) {
                    Remove-Item -LiteralPath $_.FullName -Force
                    $prunedDirectories++
                }
            }
        }
}

[pscustomobject]@{
    source_root = $SourceRoot
    destination_root = $DestinationRoot
    pruned_extraneous = [bool]$PruneExtraneous
    pruned_file_count = $prunedFiles
    pruned_directory_count = $prunedDirectories
    synced_at = (Get-Date).ToUniversalTime().ToString('o')
}
