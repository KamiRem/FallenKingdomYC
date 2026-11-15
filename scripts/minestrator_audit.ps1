param([string]$ConnectionDirectory=(Join-Path (Split-Path -Parent $PSScriptRoot) 'local/minestrator-secrets'))
$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath (Join-Path $ConnectionDirectory 'connection.json') -Raw | ConvertFrom-Json
if ([long]$config.serverId -le 0) { throw 'ID serveur invalide.' }
$secure=Import-Clixml -LiteralPath (Join-Path $ConnectionDirectory 'api-key.clixml')
$ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$summary=[ordered]@{remoteWritesAllowed=$false;api=@();sftp='non testé';rawResponsesSaved=$false}
try {
    $token=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    # Liste fermée ; aucune commande console, création de snapshot ou alimentation.
    foreach ($suffix in @('', '/live', '/backups')) {
        try {
            $response=Invoke-RestMethod -Method Get -Uri "https://mine.sttr.io/server/$($config.serverId)$suffix" -Headers @{Authorization="Bearer $token"} -MaximumRedirection 0 -TimeoutSec 20
            $summary.api+=@{endpoint="/server/{id}$suffix";httpSuccess=$true;apiCode=$response.api.code}
            # Pas de dump : les réponses peuvent contenir des identifiants SFTP ou des liens signés.
        } catch {
            $status=$null
            if ($_.Exception.Response) { $status=[int]$_.Exception.Response.StatusCode }
            $summary.api+=@{endpoint="/server/{id}$suffix";httpSuccess=$false;httpStatus=$status}
        }
    }
    try {
        $profile=Invoke-RestMethod -Method Get -Uri 'https://mine.sttr.io/user' -Headers @{Authorization="Bearer $token"} -MaximumRedirection 0 -TimeoutSec 20
        $userId=[long]$profile.api.data.user.datas.id
        if ($userId -gt 0) {
            $snapshots=Invoke-RestMethod -Method Get -Uri "https://mine.sttr.io/user/$userId/snapshots" -Headers @{Authorization="Bearer $token"} -MaximumRedirection 0 -TimeoutSec 20
            $summary.api+=@{endpoint='/user/{id}/snapshots';httpSuccess=$true;apiCode=$snapshots.api.code}
        }
    } catch { $summary.api+=@{endpoint='/user/{id}/snapshots';httpSuccess=$false} }
} finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr);$token=$null;$secure=$null;$response=$null;$profile=$null;$snapshots=$null }
if ($config.identityFile -and $config.knownHostsFile) {
    if ($config.sftpHost -notmatch '^[a-zA-Z0-9.-]+$' -or $config.sftpUser -notmatch '^[a-zA-Z0-9_.-]+$' -or [int]$config.sftpPort -lt 1 -or [int]$config.sftpPort -gt 65535) { throw 'SFTP invalide.' }
    if (!(Test-Path -LiteralPath $config.identityFile) -or !(Test-Path -LiteralPath $config.knownHostsFile)) { throw 'Clé privée ou known_hosts absent.' }
    # Rejette toute nouvelle clé hôte. L'empreinte doit être validée hors bande dans le panel/support.
    $batch=Join-Path $ConnectionDirectory 'readonly.sftp'
    "pwd`nls -la`nbye" | Set-Content -LiteralPath $batch -Encoding ascii
    $sftpResult=& sftp.exe -F NUL -b $batch -P ([int]$config.sftpPort) -i $config.identityFile -o BatchMode=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$($config.knownHostsFile)" -o ConnectTimeout=15 "$($config.sftpUser)@$($config.sftpHost)" 2>&1
    $summary.sftp=if ($LASTEXITCODE -eq 0) {'connexion et liste racine réussies'} else {'échec : authentification, accès réseau ou clé hôte à vérifier localement'}
    $sftpResult=$null
} else { $summary.sftp='Clé SSH non configurée ; authentification par mot de passe à effectuer dans un client SFTP local sans journalisation.' }
$summary | ConvertTo-Json -Depth 5
