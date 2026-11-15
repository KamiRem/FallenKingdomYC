# Saisie locale seulement : aucun accès réseau et aucune modification distante.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$configuration=Get-Content -LiteralPath (Join-Path $root 'local/minestrator-connection.json') -Raw | ConvertFrom-Json
& (Join-Path $PSScriptRoot 'minestrator_secrets.ps1') -ServerId $configuration.serverId -SftpHost $configuration.sftpHost -SftpPort $configuration.sftpPort -SftpUser $configuration.sftpUser -StoreSftpPassword
