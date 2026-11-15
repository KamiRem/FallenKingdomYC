# Stockage DPAPI local uniquement ; aucune commande réseau.
$ErrorActionPreference='Stop'
function Test-StoreConfig($Config) {
    try { return ($null -ne $Config -and [long]$Config.serverId -gt 0 -and $Config.sftpHost -match '^[a-zA-Z0-9.-]+$' -and [int]$Config.sftpPort -ge 1 -and [int]$Config.sftpPort -le 65535 -and $Config.sftpUser -match '^[a-zA-Z0-9_.-]+$') }
    catch { return $false }
}
function Assert-StorePath([string]$Path) {
    $current=[IO.Path]::GetFullPath($Path)
    while ($current) {
        $item=Get-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Lien ou jonction interdit dans le stockage.' }
        $current=[IO.Path]::GetDirectoryName($current)
    }
}
function Read-StoreConfig([string]$Directory) {
    try {
        $path=Join-Path $Directory 'connection.json'; Assert-StorePath $path
        $config=Get-Content -LiteralPath $path -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        if (Test-StoreConfig $config) { return $config }
    } catch { }
    return $null
}
function Get-MinestratorStoreState([string]$Directory) {
    Assert-StorePath $Directory
    $config=Read-StoreConfig $Directory
    $result=[ordered]@{connection='absente';apiKey='absente';sftpPassword='absent';complete=$false;remoteValidationPerformed=$false}
    if (Test-Path -LiteralPath (Join-Path $Directory 'connection.json')) { $result.connection=if ($config) {'valide'} else {'invalide'} }
    foreach ($entry in @(@('api-key.clixml','apiKey'),@('sftp.clixml','sftpPassword'))) {
        $path=Join-Path $Directory $entry[0]
        if (!(Test-Path -LiteralPath $path)) { continue }
        $result[$entry[1]]='illisible_ou_invalide'
        try {
            Assert-StorePath $path
            $value=Import-Clixml -LiteralPath $path -ErrorAction Stop
            if ($entry[1] -eq 'apiKey' -and $value -is [Security.SecureString] -and $value.Length -gt 0) { $result.apiKey='valide' }
            if ($entry[1] -eq 'sftpPassword' -and $value -is [pscredential] -and $value.Password.Length -gt 0) {
                $result.sftpPassword=if (!$config) {'dechiffrable_configuration_absente'} elseif ($value.UserName -ceq $config.sftpUser) {'valide'} else {'utilisateur_incompatible'}
            }
        } catch { }
        $value=$null
    }
    $result.complete=($result.connection -eq 'valide' -and $result.apiKey -eq 'valide' -and $result.sftpPassword -eq 'valide')
    [pscustomobject]$result
}
function Protect-StoreDirectory([string]$Directory) {
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $targets=@((Get-Item -LiteralPath $Directory)) + @(Get-ChildItem -LiteralPath $Directory -File -Force)
    foreach ($target in $targets) {
        Assert-StorePath $target.FullName
        $grant=if ($target.PSIsContainer) {"*$($sid.Value):(OI)(CI)F"} else {"*$($sid.Value):F"}
        & icacls.exe $target.FullName /inheritance:r /grant:r $grant | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Impossible de restreindre les ACL ; aucun secret écrit.' }
        $others=@((Get-Acl -LiteralPath $target.FullName).Access | ForEach-Object { $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value } | Where-Object { $_ -ne $sid.Value } | Sort-Object -Unique)
        foreach ($other in $others) {
            & icacls.exe $target.FullName /remove "*$other" | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Impossible de retirer une ACL tierce ; aucun secret écrit.' }
        }
        & icacls.exe $target.FullName /remove:d "*$($sid.Value)" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Impossible de vérifier les ACL ; aucun secret écrit.' }
    }
}
function Write-StoreFile([string]$Path,$Value,[bool]$Secret) {
    Assert-StorePath $Path
    $temporary=$Path+'.pending-'+[guid]::NewGuid().ToString('N')
    if ($Secret) {
        $Value | Export-Clixml -LiteralPath $temporary -ErrorAction Stop
        $check=Import-Clixml -LiteralPath $temporary -ErrorAction Stop
        if ($check -isnot [Security.SecureString] -and $check -isnot [pscredential]) { throw 'Échec de vérification du stockage chiffré.' }
        $check=$null
    } else { $Value | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8 }
    if (Test-Path -LiteralPath $Path) {
        [IO.File]::Replace($temporary,$Path,($Path+'.previous-'+[guid]::NewGuid().ToString('N')),$false)
    } else { [IO.File]::Move($temporary,$Path) }
    # Aucun nettoyage automatique : backups et éventuels pending restent privés.
}
function Initialize-MinestratorStore {
    param([string]$Directory,$Config,[switch]$StoreSftpPassword,
          [ValidateSet('Connection','ApiKey','SftpPassword')][string[]]$Replace=@())
    if ($env:OS -ne 'Windows_NT') { throw 'Stockage DPAPI réservé à Windows.' }
    if (!(Test-StoreConfig $Config)) { throw 'Paramètres locaux invalides ; aucun identifiant affiché.' }
    $Directory=[IO.Path]::GetFullPath($Directory); Assert-StorePath $Directory
    if (!(Test-Path -LiteralPath $Directory)) { [void][IO.Directory]::CreateDirectory($Directory) }
    if (!(Test-Path -LiteralPath $Directory -PathType Container)) { throw 'Le stockage doit être un dossier.' }
    Protect-StoreDirectory $Directory
    $lock=$null
    try {
        try { $lock=[IO.File]::Open((Join-Path $Directory '.configuration.lock'),'OpenOrCreate','ReadWrite','None') }
        catch { throw 'Configuration locale déjà en cours ; réessayer après sa fermeture.' }
        $state=Get-MinestratorStoreState $Directory
        $existing=Read-StoreConfig $Directory
        $connectionPath=Join-Path $Directory 'connection.json'
        $different=$false
        if ($existing) {
            foreach ($key in @('serverId','sftpHost','sftpPort','sftpUser','identityFile','knownHostsFile','remoteRoot')) {
                if ([string]$existing.$key -cne [string]$Config.$key) { $different=$true }
            }
        }
        if ((Test-Path -LiteralPath $connectionPath) -and (!$existing -or $different) -and 'Connection' -notin $Replace) {
            throw 'Configuration existante invalide ou différente. Utiliser -Replace Connection avec confirmation ; fichier conservé.'
        }
        foreach ($entry in @(@('apiKey','ApiKey','api-key.clixml'),@('sftpPassword','SftpPassword','sftp.clixml'))) {
            if ($entry[1] -eq 'SftpPassword' -and !$StoreSftpPassword -and 'SftpPassword' -notin $Replace) { continue }
            if ((Test-Path -LiteralPath (Join-Path $Directory $entry[2])) -and $state.($entry[0]) -notin @('valide','dechiffrable_configuration_absente') -and $entry[1] -notin $Replace) {
                throw 'Secret existant illisible ou incompatible : remplacement explicite requis ; fichier conservé.'
            }
        }
        if ($existing -and $existing.sftpUser -cne $Config.sftpUser -and (Test-Path -LiteralPath (Join-Path $Directory 'sftp.clixml')) -and 'SftpPassword' -notin $Replace) {
            throw 'Un changement de compte exige aussi -Replace SftpPassword ; aucun fichier remplacé.'
        }
        if ($state.sftpPassword -eq 'dechiffrable_configuration_absente' -and 'SftpPassword' -notin $Replace) {
            $stored=Import-Clixml -LiteralPath (Join-Path $Directory 'sftp.clixml')
            if ($stored.UserName -cne $Config.sftpUser) { throw 'Secret SFTP existant incompatible ; utiliser -Replace SftpPassword avec confirmation.' }
            $stored=$null
        }
        foreach ($part in $Replace) {
            if ((Read-Host "Remplacer volontairement $part ? Saisir REMPLACER pour confirmer") -cne 'REMPLACER') { throw 'Remplacement annulé ; fichiers de configuration conservés.' }
        }
        $api=$null;$password=$null
        if ($state.apiKey -ne 'valide' -or 'ApiKey' -in $Replace) {
            $api=Read-Host 'Clé API (saisie masquée, sans transcription)' -AsSecureString
            if ($api.Length -eq 0) { throw 'Secret vide refusé ; aucun fichier remplacé.' }
        }
        if (($StoreSftpPassword -and $state.sftpPassword -notin @('valide','dechiffrable_configuration_absente')) -or 'SftpPassword' -in $Replace) {
            $password=Read-Host 'Mot de passe SFTP (saisie masquée)' -AsSecureString
            if ($password.Length -eq 0) { throw 'Secret vide refusé ; aucun fichier remplacé.' }
        }
        if (!$existing -or 'Connection' -in $Replace) { Write-StoreFile $connectionPath $Config $false }
        if ($api) { Write-StoreFile (Join-Path $Directory 'api-key.clixml') $api $true }
        if ($password) { Write-StoreFile (Join-Path $Directory 'sftp.clixml') ([pscredential]::new($Config.sftpUser,$password)) $true }
        $api=$null;$password=$null
        Get-MinestratorStoreState $Directory
    } finally { if ($lock) { $lock.Dispose() } }
}
Export-ModuleMember -Function Get-MinestratorStoreState,Initialize-MinestratorStore
