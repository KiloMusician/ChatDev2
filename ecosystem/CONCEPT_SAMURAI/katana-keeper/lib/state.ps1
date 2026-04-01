# lib/state.ps1
# State file I/O: current.json, rollback.json, ringbuffer.json.
# Depends on: config.ps1 (Read-JsonFile, Write-JsonFile, Get-ObjectValue)

function Get-CurrentModeName {
    $state = Read-JsonFile -Path $script:CurrentStatePath -Default ([pscustomobject]@{ mode = "idle" })
    return (Get-ObjectValue -Object $state -Name "mode" -Default "idle")
}

function Save-CurrentState {
    param([Parameter(Mandatory = $true)]$State)
    Write-JsonFile -Path $script:CurrentStatePath -Object $State
}

function Save-RollbackState {
    param([Parameter(Mandatory = $true)]$Rollback)
    Write-JsonFile -Path $script:RollbackPath -Object $Rollback
}

function Add-RingBufferSample {
    param(
        [Parameter(Mandatory = $true)]$Sample,
        [Parameter(Mandatory = $true)]$Settings
    )
    $watch      = Get-ObjectValue -Object $Settings -Name "watch" -Default ([pscustomobject]@{})
    $maxSamples = [int](Get-ObjectValue -Object $watch -Name "ringBufferSamples" -Default 180)
    $existing   = @(Read-JsonFile -Path $script:RingBufferPath -Default @())
    $items      = @($existing) + @($Sample)
    if ($items.Count -gt $maxSamples) {
        $items = $items[($items.Count - $maxSamples)..($items.Count - 1)]
    }
    Write-JsonFile -Path $script:RingBufferPath -Object $items
}
