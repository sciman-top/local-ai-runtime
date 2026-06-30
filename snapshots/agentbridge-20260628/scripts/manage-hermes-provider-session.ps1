[CmdletBinding()]
param(
    [ValidateSet('load', 'switch', 'clear', 'status')]
    [string]$Action = 'status',
    [string]$Slot = 'primary',
    [string[]]$Slots,
    [string]$EnvFilePath,
    [string]$PrimaryBaseUrl,
    [string]$BackupBaseUrl,
    [string]$BaseUrl,
    [string]$ModelPrimary = 'gpt-5.4',
    [string]$ModelFallback = 'gpt-5.4',
    [Security.SecureString]$PrimaryKey,
    [Security.SecureString]$BackupKey,
    [hashtable]$KeyMap,
    [switch]$SkipBackupPrompt
)

$ErrorActionPreference = 'Stop'

$baseTrackedVariables = @(
    'HERMES_PROVIDER_API_KEY',
    'HERMES_PROVIDER_ACTIVE_SLOT',
    'HERMES_PROVIDER_BASE_URL',
    'HERMES_PROVIDER_SLOT_INDEX',
    'HERMES_MODEL_PRIMARY',
    'HERMES_MODEL_FALLBACK',
    'HERMES_INFERENCE_MODEL',
    'HERMES_INFERENCE_PROVIDER'
)

function Get-ProcessEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return [System.Environment]::GetEnvironmentVariable($Name, 'Process')
}

function Set-ProcessEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [AllowNull()]
        [string]$Value
    )

    [System.Environment]::SetEnvironmentVariable($Name, $Value, 'Process')
}

function Remove-ProcessEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    [System.Environment]::SetEnvironmentVariable($Name, $null, 'Process')
}

function Test-ProcessEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return -not [string]::IsNullOrWhiteSpace((Get-ProcessEnvValue -Name $Name))
}

function ConvertFrom-SecureStringToPlainText {
    param(
        [Parameter(Mandatory = $true)]
        [Security.SecureString]$SecureValue
    )

    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}

function ConvertTo-EnvSafeSlotName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $safe = $Name.Trim().ToUpperInvariant() -replace '[^A-Z0-9]+', '_'
    $safe = $safe.Trim('_')
    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw "Slot name is invalid: $Name"
    }

    return $safe
}

function ConvertFrom-EnvSafeSlotName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return $Name.Trim().ToLowerInvariant() -replace '_', '-'
}

function Get-SlotKeyEnvName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return 'HERMES_PROVIDER_API_KEY_{0}' -f (ConvertTo-EnvSafeSlotName -Name $Name)
}

function Get-SlotBaseUrlEnvName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return 'HERMES_PROVIDER_BASE_URL_{0}' -f (ConvertTo-EnvSafeSlotName -Name $Name)
}

function Get-TrackedVariables {
    $slotIndexRaw = Get-ProcessEnvValue -Name 'HERMES_PROVIDER_SLOT_INDEX'
    $tracked = [System.Collections.Generic.List[string]]::new()
    foreach ($item in $baseTrackedVariables) {
        $tracked.Add($item)
    }

    if (-not [string]::IsNullOrWhiteSpace($slotIndexRaw)) {
        $slotNames = @($slotIndexRaw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        foreach ($slotName in $slotNames) {
            $tracked.Add((Get-SlotKeyEnvName -Name $slotName))
            $tracked.Add((Get-SlotBaseUrlEnvName -Name $slotName))
        }
    }

    return @($tracked | Select-Object -Unique)
}

function Resolve-DotEnvPath {
    param(
        [AllowNull()]
        [string]$ExplicitPath
    )

    $candidates = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        $candidates.Add($ExplicitPath)
    }

    $cwdDotEnv = Join-Path (Get-Location) '.env'
    $candidates.Add($cwdDotEnv)

    $bridgeRoot = Split-Path -Parent $PSScriptRoot
    $bridgeDotEnv = Join-Path $bridgeRoot '.env'
    $candidates.Add($bridgeDotEnv)

    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }

        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

function ConvertFrom-DotEnvScalar {
    param(
        [AllowNull()]
        [string]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    $trimmed = $Value.Trim()
    if ($trimmed.Length -ge 2) {
        if (
            ($trimmed.StartsWith('"') -and $trimmed.EndsWith('"')) -or
            ($trimmed.StartsWith("'") -and $trimmed.EndsWith("'"))
        ) {
            $trimmed = $trimmed.Substring(1, $trimmed.Length - 2)
        }
    }

    return $trimmed
}

function Get-SlotDefinitionsFromDotEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $slotMap = @{}
    $pendingBareKeySlot = $null

    function ConvertFrom-LegacyIndexedSlotName {
        param(
            [Parameter(Mandatory = $true)]
            [string]$Prefix,
            [Parameter(Mandatory = $true)]
            [int]$Index
        )

        switch ($Index) {
            1 { return 'primary' }
            2 { return 'backup' }
            default {
                $normalizedPrefix = ($Prefix.ToLowerInvariant() -replace '[^a-z0-9]+', '-').Trim('-')
                if ([string]::IsNullOrWhiteSpace($normalizedPrefix)) {
                    $normalizedPrefix = 'slot'
                }

                return '{0}-{1}' -f $normalizedPrefix, $Index
            }
        }
    }

    function Ensure-SlotRecord {
        param(
            [Parameter(Mandatory = $true)]
            [string]$SlotName
        )

        $normalized = $SlotName.Trim()
        if ([string]::IsNullOrWhiteSpace($normalized)) {
            throw 'Slot name in .env cannot be blank.'
        }

        if (-not $slotMap.ContainsKey($normalized)) {
            $slotMap[$normalized] = [ordered]@{
                slot = $normalized
                base_url = $null
                plain_key = $null
                prompt = ("Enter {0} HERMES provider API key" -f $normalized)
            }
        }

        return $slotMap[$normalized]
    }

    $lines = Get-Content -LiteralPath $Path
    $declaredSlots = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#') -or $trimmed -notmatch '=') {
            continue
        }

        $parts = $trimmed -split '=', 2
        $name = $parts[0].Trim()
        if ($name -ne 'HERMES_SLOTS') {
            continue
        }

        $value = ConvertFrom-DotEnvScalar -Value $parts[1]
        foreach ($slotName in @([string]$value -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })) {
            $null = $declaredSlots.Add($slotName)
            Ensure-SlotRecord -SlotName $slotName | Out-Null
        }
    }

    function Test-SlotIsAllowed {
        param(
            [Parameter(Mandatory = $true)]
            [string]$SlotName
        )

        if ($declaredSlots.Count -eq 0) {
            return $true
        }

        return $declaredSlots.Contains($SlotName.Trim())
    }

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) {
            continue
        }

        if ($trimmed -notmatch '=') {
            if (-not [string]::IsNullOrWhiteSpace($pendingBareKeySlot)) {
                $record = Ensure-SlotRecord -SlotName $pendingBareKeySlot
                if ([string]::IsNullOrWhiteSpace([string]$record.plain_key)) {
                    $record.plain_key = ConvertFrom-DotEnvScalar -Value $trimmed
                }
            }

            $pendingBareKeySlot = $null
            continue
        }

        $parts = $trimmed -split '=', 2
        $name = $parts[0].Trim()
        if ([string]::IsNullOrWhiteSpace($name)) {
            $pendingBareKeySlot = $null
            continue
        }

        $value = ConvertFrom-DotEnvScalar -Value $parts[1]
        if ([string]::IsNullOrWhiteSpace($value)) {
            $pendingBareKeySlot = $null
            continue
        }

        if ($name -eq 'HERMES_SLOTS') {
            $pendingBareKeySlot = $null
            continue
        }

        $legacyIndexedMatch = [regex]::Match($name, '(?i)^(?<prefix>.+?)_(?<kind>base_url|url|api_key|key)_(?<index>\d+)$')
        if ($legacyIndexedMatch.Success -and $declaredSlots.Count -eq 0) {
            $slotName = ConvertFrom-LegacyIndexedSlotName `
                -Prefix ([string]$legacyIndexedMatch.Groups['prefix'].Value) `
                -Index ([int]$legacyIndexedMatch.Groups['index'].Value)
            $slotKind = [string]$legacyIndexedMatch.Groups['kind'].Value
            $record = Ensure-SlotRecord -SlotName $slotName

            if ($slotKind -in @('base_url', 'url')) {
                $record.base_url = $value
                $pendingBareKeySlot = $slotName
            }
            else {
                $record.plain_key = $value
                $pendingBareKeySlot = $null
            }

            continue
        }

        $baseUrlMatch = [regex]::Match($name, '^(?<slot>.+?)_(?<kind>base_url|url)$')
        if ($baseUrlMatch.Success) {
            $slotName = [string]$baseUrlMatch.Groups['slot'].Value
            if (-not (Test-SlotIsAllowed -SlotName $slotName)) {
                $pendingBareKeySlot = $null
                continue
            }
            (Ensure-SlotRecord -SlotName $slotName).base_url = $value
            $pendingBareKeySlot = $slotName
            continue
        }

        $keyMatch = [regex]::Match($name, '^(?<slot>.+?)_(?<kind>api_key|key)$')
        if ($keyMatch.Success) {
            $slotName = [string]$keyMatch.Groups['slot'].Value
            if (-not (Test-SlotIsAllowed -SlotName $slotName)) {
                $pendingBareKeySlot = $null
                continue
            }
            (Ensure-SlotRecord -SlotName $slotName).plain_key = $value
            $pendingBareKeySlot = $null
            continue
        }

        $plainSlotMatch = [regex]::Match($name, '^(?<slot>[A-Za-z0-9_-]+)$')
        if ($plainSlotMatch.Success) {
            $slotName = [string]$plainSlotMatch.Groups['slot'].Value
            $valueLooksLikeUrl = ($value -match '^https?://')
            if ($declaredSlots.Count -gt 0 -and -not (Test-SlotIsAllowed -SlotName $slotName)) {
                $pendingBareKeySlot = $null
                continue
            }
            if ($declaredSlots.Count -eq 0 -and -not $valueLooksLikeUrl) {
                $pendingBareKeySlot = $null
                continue
            }
            $record = Ensure-SlotRecord -SlotName $slotName
            if ($valueLooksLikeUrl) {
                $record.base_url = $value
                $pendingBareKeySlot = $slotName
            }
            else {
                $record.plain_key = $value
                $pendingBareKeySlot = $null
            }
            continue
        }

        $scopedBaseUrlMatch = [regex]::Match($name, '^HERMES_SLOT_(?<slot>[A-Z0-9_]+)_BASE_URL$')
        if ($scopedBaseUrlMatch.Success) {
            $slotName = ConvertFrom-EnvSafeSlotName -Name ([string]$scopedBaseUrlMatch.Groups['slot'].Value)
            if (-not (Test-SlotIsAllowed -SlotName $slotName)) {
                $pendingBareKeySlot = $null
                continue
            }
            (Ensure-SlotRecord -SlotName $slotName).base_url = $value
            $pendingBareKeySlot = $slotName
            continue
        }

        $scopedKeyMatch = [regex]::Match($name, '^HERMES_SLOT_(?<slot>[A-Z0-9_]+)_API_KEY$')
        if ($scopedKeyMatch.Success) {
            $slotName = ConvertFrom-EnvSafeSlotName -Name ([string]$scopedKeyMatch.Groups['slot'].Value)
            if (-not (Test-SlotIsAllowed -SlotName $slotName)) {
                $pendingBareKeySlot = $null
                continue
            }
            (Ensure-SlotRecord -SlotName $slotName).plain_key = $value
            $pendingBareKeySlot = $null
            continue
        }

        $pendingBareKeySlot = $null
    }

    return @(
        $slotMap.Values |
            ForEach-Object {
                [pscustomobject]@{
                    slot = [string]$_.slot
                    base_url = [string]$_.base_url
                    plain_key = [string]$_.plain_key
                    prompt = [string]$_.prompt
                }
            }
    )
}

function Merge-SlotDefinitions {
    param(
        [object[]]$PrimaryDefinitions,
        [object[]]$FallbackDefinitions
    )

    if (-not $PrimaryDefinitions -or $PrimaryDefinitions.Count -eq 0) {
        return @($FallbackDefinitions)
    }

    if (-not $FallbackDefinitions -or $FallbackDefinitions.Count -eq 0) {
        return @($PrimaryDefinitions)
    }

    $fallbackMap = @{}
    foreach ($item in $FallbackDefinitions) {
        $fallbackMap[[string]$item.slot] = $item
    }

    $merged = foreach ($item in $PrimaryDefinitions) {
        $slotName = [string]$item.slot
        $fallback = $fallbackMap[$slotName]

        [pscustomobject]@{
            slot = $slotName
            base_url = if (-not [string]::IsNullOrWhiteSpace([string]$item.base_url)) { [string]$item.base_url } elseif ($fallback) { [string]$fallback.base_url } else { $null }
            secure_key = if ($item.PSObject.Properties.Name -contains 'secure_key') { $item.secure_key } else { $null }
            plain_key = if ($item.PSObject.Properties.Name -contains 'plain_key' -and -not [string]::IsNullOrWhiteSpace([string]$item.plain_key)) { [string]$item.plain_key } elseif ($fallback) { [string]$fallback.plain_key } else { $null }
            prompt = if ($item.PSObject.Properties.Name -contains 'prompt') { [string]$item.prompt } else { ("Enter {0} HERMES provider API key" -f $slotName) }
        }
    }

    return @($merged)
}

function Get-LoadedSlotNames {
    $slotIndexRaw = Get-ProcessEnvValue -Name 'HERMES_PROVIDER_SLOT_INDEX'
    if ([string]::IsNullOrWhiteSpace($slotIndexRaw)) {
        return @()
    }

    return @($slotIndexRaw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Set-LoadedSlotNames {
    param(
        [string[]]$Names
    )

    $clean = @($Names | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
    if ($clean.Count -eq 0) {
        Remove-ProcessEnvValue -Name 'HERMES_PROVIDER_SLOT_INDEX'
        return
    }

    Set-ProcessEnvValue -Name 'HERMES_PROVIDER_SLOT_INDEX' -Value ($clean -join ',')
}

function Get-SessionStatus {
    $activeSlot = Get-ProcessEnvValue -Name 'HERMES_PROVIDER_ACTIVE_SLOT'
    $activeKeyLoaded = Test-ProcessEnvValue -Name 'HERMES_PROVIDER_API_KEY'
    $baseUrlLoaded = Test-ProcessEnvValue -Name 'HERMES_PROVIDER_BASE_URL'
    $loadedSlots = Get-LoadedSlotNames
    $slotStates = foreach ($slotName in $loadedSlots) {
        $keyName = Get-SlotKeyEnvName -Name $slotName
        $baseName = Get-SlotBaseUrlEnvName -Name $slotName
        [pscustomobject]@{
            slot = $slotName
            key_loaded = Test-ProcessEnvValue -Name $keyName
            base_url_loaded = Test-ProcessEnvValue -Name $baseName
            is_active = ($activeSlot -eq $slotName)
        }
    }

    [pscustomobject]@{
        action = $Action
        active_slot = if ([string]::IsNullOrWhiteSpace($activeSlot)) { 'unset' } else { $activeSlot }
        active_key_loaded = $activeKeyLoaded
        active_base_url_loaded = $baseUrlLoaded
        loaded_slots = $loadedSlots
        slot_states = $slotStates
        model_primary = if ([string]::IsNullOrWhiteSpace((Get-ProcessEnvValue -Name 'HERMES_MODEL_PRIMARY'))) { 'unset' } else { Get-ProcessEnvValue -Name 'HERMES_MODEL_PRIMARY' }
        model_fallback = if ([string]::IsNullOrWhiteSpace((Get-ProcessEnvValue -Name 'HERMES_MODEL_FALLBACK'))) { 'unset' } else { Get-ProcessEnvValue -Name 'HERMES_MODEL_FALLBACK' }
        inference_model = if ([string]::IsNullOrWhiteSpace((Get-ProcessEnvValue -Name 'HERMES_INFERENCE_MODEL'))) { 'unset' } else { Get-ProcessEnvValue -Name 'HERMES_INFERENCE_MODEL' }
        inference_provider = if ([string]::IsNullOrWhiteSpace((Get-ProcessEnvValue -Name 'HERMES_INFERENCE_PROVIDER'))) { 'unset' } else { Get-ProcessEnvValue -Name 'HERMES_INFERENCE_PROVIDER' }
        gate_ready = ($activeKeyLoaded -and $baseUrlLoaded)
    }
}

function Write-SessionStatus {
    Get-SessionStatus
}

function Set-ActiveSlot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RequestedSlot
    )

    $selectedKey = Get-ProcessEnvValue -Name (Get-SlotKeyEnvName -Name $RequestedSlot)
    $selectedBaseUrl = Get-ProcessEnvValue -Name (Get-SlotBaseUrlEnvName -Name $RequestedSlot)

    if ([string]::IsNullOrWhiteSpace($selectedKey)) {
        throw "No key is loaded for slot: $RequestedSlot"
    }

    if ([string]::IsNullOrWhiteSpace($selectedBaseUrl)) {
        throw "No base URL is loaded for slot: $RequestedSlot"
    }

    Set-ProcessEnvValue -Name 'HERMES_PROVIDER_API_KEY' -Value $selectedKey
    Set-ProcessEnvValue -Name 'HERMES_PROVIDER_BASE_URL' -Value $selectedBaseUrl
    Set-ProcessEnvValue -Name 'HERMES_PROVIDER_ACTIVE_SLOT' -Value $RequestedSlot
}

function Resolve-BaseUrlValue {
    param(
        [AllowNull()]
        [string]$ProvidedBaseUrl,
        [AllowNull()]
        [string]$CurrentBaseUrl,
        [Parameter(Mandatory = $true)]
        [string]$PromptLabel
    )

    foreach ($candidate in @($ProvidedBaseUrl, $CurrentBaseUrl)) {
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            return $candidate.Trim()
        }
    }

    $input = Read-Host $PromptLabel
    if ([string]::IsNullOrWhiteSpace($input)) {
        throw "$PromptLabel is required."
    }

    return $input.Trim()
}

function Read-RequiredSecureKey {
    param(
        [AllowNull()]
        [Security.SecureString]$ProvidedKey,
        [Parameter(Mandatory = $true)]
        [string]$PromptLabel
    )

    if ($ProvidedKey) {
        return $ProvidedKey
    }

    return Read-Host -AsSecureString $PromptLabel
}

function ConvertTo-SlotDefinition {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$InputSlots
    )

    $definitions = [System.Collections.Generic.List[object]]::new()
    foreach ($item in $InputSlots) {
        if ([string]::IsNullOrWhiteSpace($item)) {
            continue
        }

        $parts = $item.Split('=', 2)
        $slotName = $parts[0].Trim()
        if ([string]::IsNullOrWhiteSpace($slotName)) {
            throw "Slot definition must include a name: $item"
        }

        $slotBaseUrl = if ($parts.Count -gt 1) { $parts[1].Trim() } else { $null }
        $definitions.Add([pscustomobject]@{
                slot = $slotName
                base_url = if ([string]::IsNullOrWhiteSpace($slotBaseUrl)) { $null } else { $slotBaseUrl }
            })
    }

    return @($definitions)
}

function Get-CompatSlotDefinitions {
    $definitions = [System.Collections.Generic.List[object]]::new()

    $primaryUrl = $null
    foreach ($candidate in @($PrimaryBaseUrl, $BaseUrl)) {
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            $primaryUrl = $candidate.Trim()
            break
        }
    }
    if ($PrimaryKey -or $primaryUrl -or (Test-ProcessEnvValue -Name (Get-SlotKeyEnvName -Name 'primary'))) {
        $definitions.Add([pscustomobject]@{
                slot = 'primary'
                base_url = $primaryUrl
                secure_key = $PrimaryKey
                prompt = 'Enter primary HERMES provider API key'
            })
    }

    if (
        $BackupKey -or
        -not [string]::IsNullOrWhiteSpace($BackupBaseUrl) -or
        (Test-ProcessEnvValue -Name (Get-SlotKeyEnvName -Name 'backup'))
    ) {
        $definitions.Add([pscustomobject]@{
                slot = 'backup'
                base_url = if ([string]::IsNullOrWhiteSpace($BackupBaseUrl)) { $null } else { $BackupBaseUrl.Trim() }
                secure_key = $BackupKey
                prompt = 'Enter backup HERMES provider API key'
            })
    }

    return @($definitions)
}

function Get-LoadSlotDefinitions {
    $resolvedDotEnvPath = Resolve-DotEnvPath -ExplicitPath $EnvFilePath
    $dotEnvDefinitions = @()
    if ($resolvedDotEnvPath) {
        $dotEnvDefinitions = Get-SlotDefinitionsFromDotEnvFile -Path $resolvedDotEnvPath
    }

    if ($Slots -and $Slots.Count -gt 0) {
        $definitions = ConvertTo-SlotDefinition -InputSlots $Slots
        if ($KeyMap) {
            foreach ($definition in $definitions) {
                $slotName = [string]$definition.slot
                $definition | Add-Member -NotePropertyName secure_key -NotePropertyValue $KeyMap[$slotName] -Force
                $definition | Add-Member -NotePropertyName prompt -NotePropertyValue ("Enter {0} HERMES provider API key" -f $slotName) -Force
            }
        }
        else {
            foreach ($definition in $definitions) {
                $definition | Add-Member -NotePropertyName secure_key -NotePropertyValue $null -Force
                $definition | Add-Member -NotePropertyName prompt -NotePropertyValue ("Enter {0} HERMES provider API key" -f $definition.slot) -Force
            }
        }

        return Merge-SlotDefinitions -PrimaryDefinitions @($definitions) -FallbackDefinitions $dotEnvDefinitions
    }

    $compatDefinitions = @(Get-CompatSlotDefinitions)
    if ($compatDefinitions.Count -gt 0) {
        if ($compatDefinitions.Count -eq 1 -and $compatDefinitions[0].slot -eq 'primary' -and -not $BackupKey -and [string]::IsNullOrWhiteSpace($BackupBaseUrl) -and -not $SkipBackupPrompt) {
            $answer = Read-Host 'Load a backup HERMES provider API key into this session? [y/N]'
            if ($answer -match '^(?i)y(es)?$') {
                $compatDefinitions += [pscustomobject]@{
                    slot = 'backup'
                    base_url = $null
                    secure_key = $null
                    prompt = 'Enter backup HERMES provider API key'
                }
            }
        }
        return Merge-SlotDefinitions -PrimaryDefinitions @($compatDefinitions) -FallbackDefinitions $dotEnvDefinitions
    }

    if ($dotEnvDefinitions.Count -gt 0) {
        $defaultDefinitions = foreach ($definition in $dotEnvDefinitions) {
            [pscustomobject]@{
                slot = [string]$definition.slot
                base_url = [string]$definition.base_url
                secure_key = $null
                plain_key = [string]$definition.plain_key
                prompt = ("Enter {0} HERMES provider API key" -f [string]$definition.slot)
            }
        }
        return @($defaultDefinitions)
    }

    $firstBaseUrl = Resolve-BaseUrlValue `
        -ProvidedBaseUrl $null `
        -CurrentBaseUrl (Get-ProcessEnvValue -Name (Get-SlotBaseUrlEnvName -Name 'primary')) `
        -PromptLabel 'Enter primary HERMES provider base URL'

    $definitions = [System.Collections.Generic.List[object]]::new()
    $definitions.Add([pscustomobject]@{
            slot = 'primary'
            base_url = $firstBaseUrl
            secure_key = $null
            prompt = 'Enter primary HERMES provider API key'
        })

    while ($true) {
        $answer = Read-Host 'Add another HERMES provider slot to this session? [y/N]'
        if ($answer -notmatch '^(?i)y(es)?$') {
            break
        }

        $slotName = Read-Host 'Enter slot name'
        if ([string]::IsNullOrWhiteSpace($slotName)) {
            throw 'Slot name cannot be blank.'
        }

        $slotBaseUrl = Read-Host ("Enter {0} HERMES provider base URL" -f $slotName.Trim())
        if ([string]::IsNullOrWhiteSpace($slotBaseUrl)) {
            throw 'Slot base URL cannot be blank.'
        }

        $definitions.Add([pscustomobject]@{
                slot = $slotName.Trim()
                base_url = $slotBaseUrl.Trim()
                secure_key = $null
                prompt = ("Enter {0} HERMES provider API key" -f $slotName.Trim())
            })
    }

    return @($definitions)
}

function Set-LoadedSessionValues {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Definitions,
        [Parameter(Mandatory = $true)]
        [string]$ResolvedModelPrimary,
        [Parameter(Mandatory = $true)]
        [string]$ResolvedModelFallback,
        [Parameter(Mandatory = $true)]
        [string]$RequestedActiveSlot
    )

    $prepared = [System.Collections.Generic.List[object]]::new()
    try {
        foreach ($definition in $Definitions) {
            $slotName = [string]$definition.slot
            if ([string]::IsNullOrWhiteSpace($slotName)) {
                throw 'Slot name cannot be blank.'
            }

            $resolvedBaseUrl = Resolve-BaseUrlValue `
                -ProvidedBaseUrl ([string]$definition.base_url) `
                -CurrentBaseUrl (Get-ProcessEnvValue -Name (Get-SlotBaseUrlEnvName -Name $slotName)) `
                -PromptLabel ("Enter {0} HERMES provider base URL" -f $slotName)

            $plainKey = $null
            if (
                $definition.PSObject.Properties.Name -contains 'plain_key' -and
                -not [string]::IsNullOrWhiteSpace([string]$definition.plain_key)
            ) {
                $plainKey = [string]$definition.plain_key
            }
            else {
                $resolvedSecureKey = Read-RequiredSecureKey `
                    -ProvidedKey $definition.secure_key `
                    -PromptLabel ([string]$definition.prompt)

                $plainKey = ConvertFrom-SecureStringToPlainText -SecureValue $resolvedSecureKey
            }

            if ([string]::IsNullOrWhiteSpace($plainKey)) {
                throw "Slot key cannot be blank: $slotName"
            }

            $prepared.Add([pscustomobject]@{
                    slot = $slotName
                    base_url = $resolvedBaseUrl
                    plain_key = $plainKey
                })
        }

        foreach ($name in Get-TrackedVariables) {
            if ($name -notin $baseTrackedVariables) {
                Remove-ProcessEnvValue -Name $name
            }
        }

        foreach ($entry in $prepared) {
            Set-ProcessEnvValue -Name (Get-SlotKeyEnvName -Name $entry.slot) -Value $entry.plain_key
            Set-ProcessEnvValue -Name (Get-SlotBaseUrlEnvName -Name $entry.slot) -Value $entry.base_url
        }

        Set-LoadedSlotNames -Names @($prepared | ForEach-Object { $_.slot })
        Set-ProcessEnvValue -Name 'HERMES_MODEL_PRIMARY' -Value $ResolvedModelPrimary
        Set-ProcessEnvValue -Name 'HERMES_MODEL_FALLBACK' -Value $ResolvedModelFallback
        Set-ProcessEnvValue -Name 'HERMES_INFERENCE_MODEL' -Value $ResolvedModelPrimary
        Set-ProcessEnvValue -Name 'HERMES_INFERENCE_PROVIDER' -Value 'openai-api'
        Set-ActiveSlot -RequestedSlot $RequestedActiveSlot
    }
    finally {
        foreach ($entry in $prepared) {
            if ($entry.PSObject.Properties.Name -contains 'plain_key') {
                $entry.plain_key = $null
            }
        }
    }
}

switch ($Action) {
    'load' {
        $definitions = @(Get-LoadSlotDefinitions)
        if ($definitions.Count -eq 0) {
            throw 'No provider slot definitions were supplied for load.'
        }

        $requestedActiveSlot = if ([string]::IsNullOrWhiteSpace($Slot)) { [string]$definitions[0].slot } else { $Slot }
        if (@($definitions | ForEach-Object { [string]$_.slot }) -notcontains $requestedActiveSlot) {
            throw "Requested active slot is not part of this load set: $requestedActiveSlot"
        }

        Set-LoadedSessionValues `
            -Definitions $definitions `
            -ResolvedModelPrimary $ModelPrimary `
            -ResolvedModelFallback $ModelFallback `
            -RequestedActiveSlot $requestedActiveSlot

        Write-SessionStatus
    }
    'switch' {
        Set-ActiveSlot -RequestedSlot $Slot
        Write-SessionStatus
    }
    'clear' {
        foreach ($name in Get-TrackedVariables) {
            Remove-ProcessEnvValue -Name $name
        }

        Write-SessionStatus
    }
    'status' {
        Write-SessionStatus
    }
    default {
        throw "Unsupported action: $Action"
    }
}
