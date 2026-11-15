# Tests Windows/DPAPI réels, exclusivement dans .cache ; aucun réseau.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'scripts/minestrator_store.psm1') -Force
$work=Join-Path $root ('.cache/ms-secrets-tests-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($work)
$config=[pscustomobject]@{serverId=42;sftpHost='example.invalid';sftpPort=2022;sftpUser='dummy-test-user';identityFile='';knownHostsFile='';remoteRoot='/'}
$global:secretTestAnswers=[Collections.Generic.Queue[object]]::new()
$global:secretTestPrompts=0
function global:Read-Host {
    param([string]$Prompt,[switch]$AsSecureString)
    $global:secretTestPrompts++
    if (!$global:secretTestAnswers.Count) { throw 'Saisie inattendue dans le test.' }
    $answer=$global:secretTestAnswers.Dequeue()
    if ($AsSecureString -and $answer -isnot [Security.SecureString]) { throw 'Saisie de secret non masquée.' }
    return $answer
}
function Answers([string[]]$Values) {
    foreach ($v in $Values) {
        if ($v -in @('REMPLACER','NON')) { $global:secretTestAnswers.Enqueue($v) }
        elseif ($v -eq '') { $global:secretTestAnswers.Enqueue([Security.SecureString]::new()) }
        else { $global:secretTestAnswers.Enqueue((ConvertTo-SecureString $v -AsPlainText -Force)) }
    }
}
$checks=[Collections.Generic.List[string]]::new()
function Check([bool]$Value,[string]$Name) { if (!$Value) { throw "Échec du test : $Name" }; $checks.Add($Name) }
function Hash($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function Init($dir,$replace=@()) { Initialize-MinestratorStore -Directory $dir -Config $config -StoreSftpPassword -Replace $replace }
try {
    $missing=Join-Path $work 'missing'
    $s=Get-MinestratorStoreState $missing
    Check (!$s.complete -and !(Test-Path $missing)) 'état absent sans création de dossier'
    $empty=Join-Path $work 'empty';[void][IO.Directory]::CreateDirectory($empty)
    Answers @('FAKE-API-ONE','FAKE-PASSWORD-ONE');$s=Init $empty
    Check $s.complete 'dossier préexistant vide complété avec DPAPI'
    $api=Join-Path $empty 'api-key.clixml';$password=Join-Path $empty 'sftp.clixml';$connection=Join-Path $empty 'connection.json'
    $before=@((Hash $api),(Hash $password),(Hash $connection));$prompts=$global:secretTestPrompts
    $s=Init $empty
    Check ($s.complete -and $prompts -eq $global:secretTestPrompts -and $before[0] -eq (Hash $api) -and $before[1] -eq (Hash $password) -and $before[2] -eq (Hash $connection)) 'réexécution valide sans saisie ni réécriture'
    $partial=Join-Path $work 'partial';[void][IO.Directory]::CreateDirectory($partial)
    Copy-Item -LiteralPath $api -Destination (Join-Path $partial 'api-key.clixml')
    Answers @('FAKE-PASSWORD-TWO');$s=Init $partial
    Check ($s.complete -and (Hash (Join-Path $partial 'api-key.clixml')) -eq $before[0]) 'reprise après interruption sans réécrire la clé existante'
    Answers @('NON');$refused=$false
    try { Init $empty @('ApiKey') | Out-Null } catch { $refused=$true }
    Check ($refused -and (Hash $api) -eq $before[0]) 'remplacement annulé sans modification du secret'
    Answers @('REMPLACER','FAKE-API-TWO');$s=Init $empty @('ApiKey')
    $backups=@(Get-ChildItem -LiteralPath $empty -Filter 'api-key.clixml.previous-*')
    Check ($s.complete -and $backups.Count -eq 1 -and (Hash $backups[0].FullName) -eq $before[0] -and (Hash $api) -ne $before[0]) 'rotation confirmée avec sauvegarde exacte du secret précédent'
    $decoded=Import-Clixml -LiteralPath $api
    Check ([pscredential]::new('dummy',$decoded).GetNetworkCredential().Password -ceq 'FAKE-API-TWO') 'nouvelle clé déchiffrable par DPAPI'
    $cipher=Get-Content -LiteralPath $api -Raw
    Check (!$cipher.Contains('FAKE-API-TWO')) 'secret absent du fichier en clair'
    $invalid=Join-Path $work 'invalid';[void][IO.Directory]::CreateDirectory($invalid)
    $bad=Join-Path $invalid 'api-key.clixml';'CLIXML factice invalide' | Set-Content -LiteralPath $bad
    $oldBad=Hash $bad;$refused=$false
    try { Init $invalid | Out-Null } catch { $refused=$true }
    Check ($refused -and (Hash $bad) -eq $oldBad) 'secret illisible conservé sans remplacement implicite'
    Answers @('REMPLACER','FAKE-API-THREE','FAKE-PASSWORD-THREE');$s=Init $invalid @('ApiKey')
    Check ($s.complete -and @(Get-ChildItem $invalid -Filter '*.previous-*').Count -eq 1) 'configuration invalide réparée uniquement après confirmation'
    $status=& (Join-Path $root 'scripts/minestrator_status.ps1') -ConnectionDirectory $empty
    Check (($status | ConvertFrom-Json).complete -and $status -notmatch 'FAKE-|dummy-test-user|example.invalid') 'commande état sans secret ni identifiant'
    $statusAlias=& (Join-Path $root 'scripts/minestrator_configure_local.ps1') -Status -ConnectionDirectory $empty
    Check (($statusAlias | ConvertFrom-Json).complete -and $statusAlias -notmatch 'FAKE-|dummy-test-user|example.invalid') 'alias état sans charger les paramètres réels'
    $oldPassword=Hash $password
    Answers @('REMPLACER','FAKE-PASSWORD-ROTATED');$s=Init $empty @('SftpPassword')
    $savedPassword=@(Get-ChildItem -LiteralPath $empty -Filter 'sftp.clixml.previous-*')
    $credential=Import-Clixml -LiteralPath $password
    Check ($s.complete -and $savedPassword.Count -eq 1 -and (Hash $savedPassword[0].FullName) -eq $oldPassword -and $credential.GetNetworkCredential().Password -ceq 'FAKE-PASSWORD-ROTATED') 'rotation du credential SFTP avec sauvegarde et DPAPI'
    $oldApi=Hash $api;Answers @('REMPLACER','');$refused=$false
    try { Init $empty @('ApiKey') | Out-Null } catch { $refused=$true }
    Check ($refused -and (Hash $api) -eq $oldApi) 'nouveau secret vide refusé sans perte de la version valide'
    $configDir=Join-Path $work 'config-change';[void][IO.Directory]::CreateDirectory($configDir)
    '{invalid json' | Set-Content (Join-Path $configDir 'connection.json');$old=Hash (Join-Path $configDir 'connection.json');$refused=$false
    try { Init $configDir | Out-Null } catch { $refused=$true }
    Check ($refused -and $old -eq (Hash (Join-Path $configDir 'connection.json'))) 'métadonnées invalides conservées sans remplacement explicite'
    Answers @('REMPLACER','FAKE-API-FOUR','FAKE-PASSWORD-FOUR');$s=Init $configDir @('Connection')
    Check ($s.complete -and @(Get-ChildItem $configDir -Filter 'connection.json.previous-*').Count -eq 1) 'métadonnées remplacées avec confirmation et copie précédente'
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $rules=@((Get-Acl -LiteralPath $empty).Access)+@((Get-Acl -LiteralPath $api).Access)
    Check (@($rules | Where-Object { $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -ne $sid -or $_.AccessControlType -ne 'Allow' }).Count -eq 0) 'ACL dossier et secret limitées au compte Windows courant'
    $lock=[IO.File]::Open((Join-Path $empty '.configuration.lock'),'Open','ReadWrite','None');$refused=$false
    try { Init $empty | Out-Null } catch { $refused=$true } finally { $lock.Dispose() }
    Check $refused 'écriture concurrente refusée'
    Check ($global:secretTestAnswers.Count -eq 0) 'toutes les saisies factices consommées'
    $report=@{passed=$true;checks=$checks;count=$checks.Count;networkCalls=0;actualCredentialsAccessed=$false;dpapiWindowsTested=$true}
    $report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $work 'result.json') -Encoding UTF8
    $report | ConvertTo-Json -Depth 4
} finally {
    Remove-Item Function:\Read-Host -ErrorAction SilentlyContinue
    Remove-Variable secretTestAnswers,secretTestPrompts -Scope Global -ErrorAction SilentlyContinue
}
