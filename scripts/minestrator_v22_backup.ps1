$ErrorActionPreference='Stop'
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
    foreach ($arg in @('-X','utf8','-B',(Join-Path $PSScriptRoot 'minestrator_v22_backup.py'))) { $start.ArgumentList.Add($arg) }
    $start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    $process.StartInfo=$start
    $payload=@{serverId=$config.serverId;host=$config.sftpHost;port=$config.sftpPort;user=$credential.UserName;password=$credential.GetNetworkCredential().Password;apiKey=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr);fingerprint='SHA256:eXyAN0WEWh6kRFTNzHWollIGwpXMs9iRVm4mchwrlGI'}
    [void]$process.Start();$process.StandardInput.WriteLine(($payload|ConvertTo-Json -Compress));$process.StandardInput.Close();$payload.Clear()
    $stderr=$process.StandardError.ReadToEndAsync()
    while ($null -ne ($line=$process.StandardOutput.ReadLine())) { Write-Output $line }
    $process.WaitForExit();$discarded=$stderr.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0) { throw 'Sauvegarde interrompue ; aucune relance automatique. Consulter le rapport privé.' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr);$credential=$null;$secure=$null;$payload=$null;$discarded=$null;$process.Dispose()
}
