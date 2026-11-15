param([Parameter(Mandatory)][long]$ServerId,
      [Parameter(Mandatory)][string]$SftpHost,
      [Parameter(Mandatory)][ValidateRange(1,65535)][int]$SftpPort,
      [Parameter(Mandatory)][string]$SftpUser,
      [string]$IdentityFile='', [string]$KnownHostsFile='',
      [switch]$StoreSftpPassword,
      [ValidateSet('Connection','ApiKey','SftpPassword')][string[]]$Replace=@(),
      [string]$ConnectionDirectory=(Join-Path (Split-Path -Parent $PSScriptRoot) 'local/minestrator-secrets'))
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'minestrator_store.psm1') -Force
$configuration=[pscustomobject]@{serverId=$ServerId;sftpHost=$SftpHost;sftpPort=$SftpPort;sftpUser=$SftpUser;identityFile=$IdentityFile;knownHostsFile=$KnownHostsFile;remoteRoot='/'}
Initialize-MinestratorStore -Directory $ConnectionDirectory -Config $configuration -StoreSftpPassword:$StoreSftpPassword -Replace $Replace
