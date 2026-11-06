param(
    [Parameter(Mandatory, Position=0)][string]$Action,
    [string]$Name = 'local',
    [switch]$Accept,
    [int]$Memory = 4,
    [int]$Port = 25565,
    [switch]$Public,
    [string]$Source
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$arguments = @("$PSScriptRoot/server.py", $Action, '--name', $Name, '--memory', $Memory, '--port', $Port)
if ($Accept) { $arguments += '--accept' }
if ($Public) { $arguments += '--public' }
if ($Source) { $arguments += @('--source', $Source) }
python @arguments
if ($LASTEXITCODE -ne 0) { throw "Opération $Action interrompue." }
