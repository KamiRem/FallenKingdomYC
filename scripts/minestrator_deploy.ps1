param([Parameter(Mandatory)][ValidateSet('install','start','rollback')][string]$Phase)
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
    $start.ArgumentList.Add('-B');$start.ArgumentList.Add((Join-Path $PSScriptRoot 'minestrator_deploy.py'))
    $start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    $process.StartInfo=$start
    $payload=@{serverId=$config.serverId;host=$config.sftpHost;port=$config.sftpPort;user=$credential.UserName;password=$credential.GetNetworkCredential().Password;apiKey=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr);fingerprint='SHA256:eXyAN0WEWh6kRFTNzHWollIGwpXMs9iRVm4mchwrlGI';output=(Join-Path ([Environment]::GetFolderPath('UserProfile')) 'FKBackups/MS-DEPLOY-V21-20261120-01');phase=$Phase}
    [void]$process.Start();$process.StandardInput.WriteLine(($payload|ConvertTo-Json -Compress));$process.StandardInput.Close();$payload.Clear()
    $stderrTask=$process.StandardError.ReadToEndAsync()
    while ($null -ne ($line=$process.StandardOutput.ReadLine())) { Write-Output $line }
    $process.WaitForExit();$errors=$stderrTask.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0) { throw 'Phase interrompue. Consulter le journal privé avant toute reprise ; ne pas relancer aveuglément.' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr);$credential=$null;$secure=$null;$payload=$null;$errors=$null;$process.Dispose()
}
