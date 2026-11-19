param([Parameter(Mandatory)][ValidatePattern('^SHA256:[A-Za-z0-9+/]{43}$')][string]$HostFingerprint)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot;$store=Join-Path $root 'local/minestrator-secrets'
$config=Get-Content -LiteralPath (Join-Path $store 'connection.json') -Raw | ConvertFrom-Json
$credential=Import-Clixml -LiteralPath (Join-Path $store 'sftp.clixml')
$api=Import-Clixml -LiteralPath (Join-Path $store 'api-key.clixml')
if ($credential.UserName -cne $config.sftpUser) { throw 'Credential local incompatible.' }
$ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($api)
$start=[Diagnostics.ProcessStartInfo]::new();$start.FileName=Join-Path $root '.tools/ms-audit/Scripts/python.exe'
$start.ArgumentList.Add((Join-Path $PSScriptRoot 'minestrator_sftp_diagnostic.py'))
$start.UseShellExecute=$false;$start.CreateNoWindow=$true;$start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
$process=[Diagnostics.Process]::new();$process.StartInfo=$start
try {
    $payload=@{host=$config.sftpHost;port=$config.sftpPort;user=$credential.UserName;password=$credential.GetNetworkCredential().Password;serverId=$config.serverId;apiKey=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr);fingerprint=$HostFingerprint;output=(Join-Path $store ('sftp-diagnostic-'+[guid]::NewGuid().ToString('N')+'.json'))}
    [void]$process.Start();$process.StandardInput.WriteLine(($payload | ConvertTo-Json -Compress));$process.StandardInput.Close();$payload.Clear()
    $result=$process.StandardOutput.ReadToEnd();$errors=$process.StandardError.ReadToEnd();$process.WaitForExit()
    Write-Output $result
    if ($process.ExitCode -ne 0) { throw 'Diagnostic ciblé interrompu ; aucune sauvegarde lancée.' }
} finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr);$api=$null;$credential=$null;$payload=$null;$errors=$null;$process.Dispose() }
