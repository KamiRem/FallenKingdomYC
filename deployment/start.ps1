param([Parameter(Mandatory=$true)][int]$Port, [int]$Memory = 6)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    python maintenance/host_ops.py start --host 127.0.0.1 --port $Port --memory $Memory
    if ($LASTEXITCODE -ne 0) { throw 'Échec du serveur ; consulter les journaux.' }
} finally { Pop-Location }
