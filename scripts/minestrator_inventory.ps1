param([Parameter(Mandatory)][ValidatePattern('^SHA256:[A-Za-z0-9+/]{43}$')][string]$HostFingerprint,[switch]$ReadConfiguration)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$directory=Join-Path $root 'local/minestrator-secrets'
$config=Get-Content -LiteralPath (Join-Path $directory 'connection.json') -Raw | ConvertFrom-Json
$credential=Import-Clixml -LiteralPath (Join-Path $directory 'sftp.clixml')
if ($credential -isnot [pscredential] -or $credential.UserName -cne $config.sftpUser) { throw 'Credential SFTP incompatible.' }
$python=Join-Path $root '.tools/ms-audit/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Client isolé ms-audit absent : installer les dépendances verrouillées.' }
$output=Join-Path $directory ('remote-inventory-'+[guid]::NewGuid().ToString('N')+'.json')
$start=[Diagnostics.ProcessStartInfo]::new()
$start.FileName=$python
$start.ArgumentList.Add((Join-Path $PSScriptRoot 'minestrator_sftp_inventory.py'))
$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
$process=[Diagnostics.Process]::new();$process.StartInfo=$start
try {
    [void]$process.Start()
    $payload=@{host=$config.sftpHost;port=$config.sftpPort;user=$credential.UserName;password=$credential.GetNetworkCredential().Password;fingerprint=$HostFingerprint;output=$output}
    if ($ReadConfiguration) { $payload.readFiles=@('server.properties','RUNTIME_LOCK.json','plugins/FKAmis/config.yml','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','whitelist.json','ops.json','map-v2-construction.json','map-v21-caverns.json','logs/latest.log') }
    $process.StandardInput.WriteLine(($payload | ConvertTo-Json -Compress));$process.StandardInput.Close();$payload.Clear()
    $result=$process.StandardOutput.ReadToEnd();$errors=$process.StandardError.ReadToEnd();$process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw 'Inventaire SFTP refusé ou incomplet ; aucun fichier distant modifié.' }
    $parsed=$result | ConvertFrom-Json
    if ($ReadConfiguration) {
        ($parsed.privateContents | ConvertTo-Json -Depth 5 -Compress | ConvertTo-SecureString -AsPlainText -Force) | Export-Clixml -LiteralPath ([IO.Path]::ChangeExtension($output,'contents.clixml'))
    }
    $parsed.PSObject.Properties.Remove('privateContents');$result=$null
    $parsed | ConvertTo-Json
    Write-Output 'Inventaire détaillé conservé uniquement dans le stockage local privé.'
} finally { $credential=$null;$errors=$null;$process.Dispose() }
