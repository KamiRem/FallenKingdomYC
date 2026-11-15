param([string]$ConnectionDirectory=(Join-Path (Split-Path -Parent $PSScriptRoot) 'local/minestrator-secrets'))
# Lecture locale exclusivement ; aucun identifiant, empreinte ou secret affiché.
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'minestrator_store.psm1') -Force
Get-MinestratorStoreState -Directory $ConnectionDirectory | ConvertTo-Json
