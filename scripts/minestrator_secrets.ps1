param([Parameter(Mandatory)][long]$ServerId,
      [Parameter(Mandatory)][string]$SftpHost,
      [Parameter(Mandatory)][ValidateRange(1,65535)][int]$SftpPort,
      [Parameter(Mandatory)][string]$SftpUser,
      [string]$IdentityFile='', [string]$KnownHostsFile='',
      [switch]$StoreSftpPassword)
$ErrorActionPreference='Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Stockage DPAPI réservé à Windows.' }
if ($ServerId -le 0 -or $SftpHost -notmatch '^[a-zA-Z0-9.-]+$' -or $SftpUser -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Paramètres de connexion invalides.' }
$secretFolder=Join-Path (Split-Path -Parent $PSScriptRoot) 'local/minestrator-secrets'
if (Test-Path -LiteralPath $secretFolder) { throw 'Dossier existant : ne pas écraser les accès.' }
New-Item -ItemType Directory -Path $secretFolder | Out-Null
$accountSid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
& icacls.exe $secretFolder /inheritance:r /grant:r "$($accountSid):(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Impossible de restreindre les ACL ; aucun secret enregistré.' }
# Read-Host ne place pas la clé dans la ligne de commande ou un fichier en clair.
$apiSecret=Read-Host 'Clé API MineStrator (saisie masquée, ne pas utiliser de transcription)' -AsSecureString
$apiSecret | Export-Clixml -LiteralPath (Join-Path $secretFolder 'api-key.clixml')
if ($StoreSftpPassword) {
    $sftpSecret=Read-Host 'Mot de passe SFTP (saisie masquée)' -AsSecureString
    [pscredential]::new($SftpUser,$sftpSecret) | Export-Clixml -LiteralPath (Join-Path $secretFolder 'sftp.clixml')
    $sftpSecret=$null
}
@{serverId=$ServerId;sftpHost=$SftpHost;sftpPort=$SftpPort;sftpUser=$SftpUser;identityFile=$IdentityFile;knownHostsFile=$KnownHostsFile;remoteRoot='/'} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $secretFolder 'connection.json') -Encoding UTF8
Write-Host 'Clé chiffrée avec DPAPI pour cet utilisateur Windows ; dossier ignoré par Git.'
