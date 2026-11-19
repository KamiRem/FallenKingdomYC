param([Parameter(Mandatory)][ValidatePattern('^SHA256:[A-Za-z0-9+/]{43}$')][string]$HostFingerprint)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$store=Join-Path $root 'local/minestrator-secrets'
$config=Get-Content -LiteralPath (Join-Path $store 'connection.json') -Raw | ConvertFrom-Json
$credential=Import-Clixml -LiteralPath (Join-Path $store 'sftp.clixml')
$api=Import-Clixml -LiteralPath (Join-Path $store 'api-key.clixml')
if ($credential -isnot [pscredential] -or $credential.UserName -cne $config.sftpUser) { throw 'Credential local incompatible.' }
$operation='MS-COLD-20261119-01'
$clientDate=[TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow,[TimeZoneInfo]::FindSystemTimeZoneById('Romance Standard Time')).ToString('yyyy-MM-dd')
if ($clientDate -ne '2026-11-19') { throw 'Dérogation ponctuelle réservée au 19 novembre 2026 ; ne pas réutiliser automatiquement.' }
$destination=Join-Path ([Environment]::GetFolderPath('UserProfile')) "FKBackups/$operation"
$java=(Get-ChildItem -LiteralPath (Join-Path $root '.tools/jdk') -Directory | Select-Object -First 1).FullName+'/bin/java.exe'
$snake=Join-Path $root '.cache/m2/org/yaml/snakeyaml/2.2/snakeyaml-2.2.jar'
if (!(Test-Path -LiteralPath $java) -or !(Test-Path -LiteralPath $snake)) { throw 'Outils de vérification locaux absents.' }
$delivery=Get-Content -LiteralPath (Join-Path $root 'tests/results/vnext1-delivery.json') -Raw | ConvertFrom-Json
$ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($api)
$process=[Diagnostics.Process]::new()
try {
    $start=[Diagnostics.ProcessStartInfo]::new();$start.FileName=Join-Path $root '.tools/ms-audit/Scripts/python.exe'
    $start.ArgumentList.Add((Join-Path $PSScriptRoot 'minestrator_cold_backup.py'))
    $start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
    $process.StartInfo=$start
    $payload=@{operationId=$operation;destination=$destination;host=$config.sftpHost;port=$config.sftpPort;user=$credential.UserName;password=$credential.GetNetworkCredential().Password;apiKey=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr);serverId=$config.serverId;fingerprint=$HostFingerprint;java=$java;snakeYamlJar=$snake;expectedHashes=@{
      'paper.jar'=$delivery.runtime.paperSha256;'server.jar'=$delivery.runtime.paperSha256;'plugins/FallenKingdom-2.24.9.jar'=$delivery.runtime.fallenkingdomSha256;'plugins/FKAmis-1.0.0.jar'=$delivery.fkamisSha256}}
    [void]$process.Start();$process.StandardInput.WriteLine(($payload | ConvertTo-Json -Depth 5 -Compress));$process.StandardInput.Close();$payload.Clear()
    while ($null -ne ($line=$process.StandardOutput.ReadLine())) { Write-Output $line }
    $errors=$process.StandardError.ReadToEnd();$process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw 'Sauvegarde interrompue ou non validée. Consulter le rapport privé ; ne pas relancer automatiquement.' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr);$api=$null;$credential=$null;$payload=$null;$errors=$null;$process.Dispose()
}
