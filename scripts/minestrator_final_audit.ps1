param([Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $PSScriptRoot 'minestrator_store.psm1') -Force
$store=Join-Path $root 'local/minestrator-secrets'
if (!(Get-MinestratorStoreState $store).complete) { throw 'Configuration locale incomplète ; aucun accès réseau.' }
$config=Get-Content -LiteralPath (Join-Path $store 'connection.json') -Raw | ConvertFrom-Json
$credential=Import-Clixml -LiteralPath (Join-Path $store 'sftp.clixml')
$secure=Import-Clixml -LiteralPath (Join-Path $store 'api-key.clixml')
$ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$process=[Diagnostics.Process]::new()
try {
    $start=[Diagnostics.ProcessStartInfo]::new();$start.FileName=Join-Path $root '.tools/ms-audit/Scripts/python.exe'
    $start.ArgumentList.Add('-B');$start.ArgumentList.Add((Join-Path $PSScriptRoot 'minestrator_final_audit.py'))
    $start.UseShellExecute=$false;$start.CreateNoWindow=$true
    $start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    $process.StartInfo=$start
    $payload=@{serverId=$config.serverId;host=$config.sftpHost;port=$config.sftpPort;user=$credential.UserName;password=$credential.GetNetworkCredential().Password;apiKey=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr);fingerprint='SHA256:eXyAN0WEWh6kRFTNzHWollIGwpXMs9iRVm4mchwrlGI';output=$OutputDirectory}
    [void]$process.Start();$process.StandardInput.WriteLine(($payload|ConvertTo-Json -Compress));$process.StandardInput.Close();$payload.Clear()
    $stderrTask=$process.StandardError.ReadToEndAsync()
    while ($null -ne ($line=$process.StandardOutput.ReadLine())) { Write-Output $line }
    $process.WaitForExit();$errors=$stderrTask.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0) { throw 'Audit arrêté ou non terminé. Aucun transfert ni action de contrôle distante ; consulter le rapport privé.' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    $credential=$null;$secure=$null;$payload=$null;$errors=$null;$process.Dispose()
}
