param([ValidateSet('discover','fingerprint','regions','checkpoint')][string]$Phase='discover',[string]$Operation='MS-V22-PREFLIGHT-20261123-01')
$ErrorActionPreference='Stop'
if ($Operation -notmatch '^MS-V22-PREFLIGHT-[0-9]{8}-[0-9]{2}$') { throw "Identifiant d'audit invalide." }
$root=Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $PSScriptRoot 'minestrator_store.psm1') -Force
$store=Join-Path $root 'local/minestrator-secrets'
if (!(Get-MinestratorStoreState $store).complete) { throw 'Accès locaux incomplets.' }
$config=Get-Content -LiteralPath (Join-Path $store 'connection.json') -Raw | ConvertFrom-Json
$credential=Import-Clixml -LiteralPath (Join-Path $store 'sftp.clixml')
$secure=Import-Clixml -LiteralPath (Join-Path $store 'api-key.clixml')
$ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$process=[Diagnostics.Process]::new()
try {
    $start=[Diagnostics.ProcessStartInfo]::new();$start.FileName=Join-Path $root '.tools/ms-audit/Scripts/python.exe'
    foreach ($arg in @('-X','utf8','-B',(Join-Path $PSScriptRoot 'minestrator_v22_preflight.py'))) { $start.ArgumentList.Add($arg) }
    $start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    $process.StartInfo=$start
    $payload=@{serverId=$config.serverId;host=$config.sftpHost;port=$config.sftpPort;user=$credential.UserName;password=$credential.GetNetworkCredential().Password;apiKey=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr);fingerprint='SHA256:eXyAN0WEWh6kRFTNzHWollIGwpXMs9iRVm4mchwrlGI';output=(Join-Path ([Environment]::GetFolderPath('UserProfile')) "FKBackups/$Operation");phase=$Phase}
    [void]$process.Start();$process.StandardInput.WriteLine(($payload|ConvertTo-Json -Compress));$process.StandardInput.Close();$payload.Clear()
    $stderr=$process.StandardError.ReadToEndAsync()
    while ($null -ne ($line=$process.StandardOutput.ReadLine())) { Write-Output $line }
    $process.WaitForExit();$discarded=$stderr.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0) { throw 'Audit interrompu ; consulter le rapport privé, sans relance automatique ni modification distante.' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr);$credential=$null;$secure=$null;$payload=$null;$discarded=$null;$process.Dispose()
}
