param([switch]$Status,
      [ValidateSet('Connection','ApiKey','SftpPassword')][string[]]$Replace=@(),
      [string]$ConnectionDirectory=(Join-Path (Split-Path -Parent $PSScriptRoot) 'local/minestrator-secrets'))
# Saisie locale seulement : aucun accès réseau et aucune modification distante.
$ErrorActionPreference='Stop'
if ($Status) {
    & (Join-Path $PSScriptRoot 'minestrator_status.ps1') -ConnectionDirectory $ConnectionDirectory
    return
}
$root=Split-Path -Parent $PSScriptRoot
$configuration=Get-Content -LiteralPath (Join-Path $root 'local/minestrator-connection.json') -Raw | ConvertFrom-Json
& (Join-Path $PSScriptRoot 'minestrator_secrets.ps1') -ServerId $configuration.serverId -SftpHost $configuration.sftpHost -SftpPort $configuration.sftpPort -SftpUser $configuration.sftpUser -StoreSftpPassword -Replace $Replace -ConnectionDirectory $ConnectionDirectory
