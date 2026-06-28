param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$issues = @()

$requirements = @(
    @{
        path = Join-Path $PSScriptRoot 'start-hermes.ps1'
        parameters = @('ReadOnlyRootfs', 'TmpfsMounts')
    },
    @{
        path = Join-Path $PSScriptRoot 'verify-hermes-boundary.ps1'
        parameters = @('ReadOnlyRootfs', 'TmpfsMounts')
    },
    @{
        path = Join-Path $PSScriptRoot 'invoke-hermes-bringup-once.ps1'
        parameters = @('ReadOnlyRootfs', 'TmpfsMounts')
    },
    @{
        path = Join-Path $PSScriptRoot 'invoke-phase0-readonly-probe.ps1'
        parameters = @('EnvFilePath')
    }
)

foreach ($requirement in $requirements) {
    $path = [string]$requirement.path
    if (-not (Test-Path -LiteralPath $path)) {
        $issues += "Missing required script: $path"
        continue
    }

    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count -gt 0) {
        $issues += "Failed to parse script: $path"
        continue
    }

    $parameterNames = @()
    if ($ast.ParamBlock) {
        $parameterNames = @($ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
    }

    foreach ($parameterName in @($requirement.parameters)) {
        if ([string]$parameterName -notin $parameterNames) {
            $issues += "Missing parameter '$parameterName' in $path"
        }
    }
}

[pscustomobject]@{
    root = $Root
    ok = ($issues.Count -eq 0)
    issues = $issues
}
