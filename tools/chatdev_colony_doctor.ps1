#requires -Version 5.1
param(
    [switch]$Json,
    [double]$Timeout = 2.0
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Doctor = Join-Path $ScriptDir "chatdev_colony_doctor.py"

$argsList = @($Doctor, "--timeout", ([string]$Timeout))
if ($Json) {
    $argsList += "--json"
}

python @argsList
