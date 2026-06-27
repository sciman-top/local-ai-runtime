Set-StrictMode -Version Latest

function Get-AgentBridgeRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptRoot
    )

    return (Split-Path -Parent $ScriptRoot)
}

function ConvertTo-AgentBridgeSlug {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $slug = $Text.ToLowerInvariant() -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    if (-not $slug) {
        return 'task'
    }

    return $slug
}

function New-AgentBridgeTaskId {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Slug,
        [datetime]$Timestamp = (Get-Date)
    )

    $safeSlug = ConvertTo-AgentBridgeSlug -Text $Slug
    return 'T-{0}-{1}' -f $Timestamp.ToString('yyyyMMdd-HHmmss'), $safeSlug
}

function ConvertTo-UtcIsoString {
    param(
        [datetime]$Timestamp = (Get-Date)
    )

    return $Timestamp.ToUniversalTime().ToString('o')
}

function Write-AgentBridgeUtf8LfFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $directory = Split-Path -Parent $Path
    if ($directory) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }

    $normalized = ($Content -replace "`r`n", "`n") -replace "`r", "`n"
    if (-not $normalized.EndsWith("`n")) {
        $normalized += "`n"
    }

    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $normalized, $encoding)
}

function ConvertTo-YamlQuotedScalar {
    param(
        [AllowNull()]
        [string]$Value
    )

    $escaped = ($Value ?? '') -replace '"', '\"'
    return '"' + $escaped + '"'
}

function ConvertTo-YamlList {
    param(
        [AllowEmptyCollection()]
        [string[]]$Items,
        [string]$Indent = '  '
    )

    if (-not $Items -or $Items.Count -eq 0) {
        return @("${Indent}- none")
    }

    return @($Items | ForEach-Object { '{0}- {1}' -f $Indent, $_ })
}

function Get-AgentBridgeRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return ([System.IO.Path]::GetRelativePath($Root, $Path)).Replace('\', '/')
}

function Get-AgentBridgeArtifactRecord {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [string]$ArtifactPath
    )

    if (-not (Test-Path $ArtifactPath)) {
        throw "Artifact path not found: $ArtifactPath"
    }

    $item = Get-Item -LiteralPath $ArtifactPath
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ArtifactPath).Hash.ToLowerInvariant()

    [pscustomobject]@{
        full_path = $item.FullName
        relative_path = Get-AgentBridgeRelativePath -Root $Root -Path $item.FullName
        bytes = [int64]$item.Length
        sha256 = $hash
        artifact_line = '{0} | {1} | {2}' -f (Get-AgentBridgeRelativePath -Root $Root -Path $item.FullName), [int64]$item.Length, $hash
    }
}

function Invoke-AgentBridgeNativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$AllowFailure
    )

    $output = & $FilePath @Arguments 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    $lines = @($output -split "`r?`n" | Where-Object { $_ -ne '' })

    if (-not $AllowFailure -and $exitCode -ne 0) {
        $renderedArgs = @($Arguments | ForEach-Object {
                if ($_ -match '\s') {
                    '"{0}"' -f $_
                }
                else {
                    $_
                }
            }) -join ' '
        $message = "External command failed with exit code {0}: {1} {2}" -f $exitCode, $FilePath, $renderedArgs
        if ($output.Trim()) {
            $message = "{0}`n{1}" -f $message, $output.TrimEnd()
        }

        throw $message
    }

    [pscustomobject]@{
        exit_code = $exitCode
        output = $output
        lines = $lines
    }
}
