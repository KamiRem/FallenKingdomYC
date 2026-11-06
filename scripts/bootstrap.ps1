param()
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$headers = @{ 'User-Agent' = 'FallenKingdomYC/1.0 (private Minecraft project)' }
New-Item -ItemType Directory -Force .tools, .cache | Out-Null
$lock = Get-Content -Raw configs/artifacts.lock.json | ConvertFrom-Json
foreach ($artifact in $lock.artifacts) {
    $destination = Join-Path $repo $artifact.path
    New-Item -ItemType Directory -Force (Split-Path -Parent $destination) | Out-Null
    if (!(Test-Path -LiteralPath $destination)) {
        $temporary = "$destination.part"
        Invoke-WebRequest -Headers $headers -Uri $artifact.url -OutFile $temporary
        if ((Get-FileHash -LiteralPath $temporary -Algorithm $artifact.algorithm).Hash.ToLowerInvariant() -ne $artifact.hash) {
            throw "Empreinte incorrecte : $($artifact.name). Fichier non installé."
        }
        Move-Item -LiteralPath $temporary -Destination $destination
    }
    if ((Get-FileHash -LiteralPath $destination -Algorithm $artifact.algorithm).Hash.ToLowerInvariant() -ne $artifact.hash) {
        throw "Archive modifiée : $($artifact.name)."
    }
    if ($artifact.name -eq 'temurin' -and !(Test-Path .tools/jdk)) {
        Expand-Archive -LiteralPath $destination -DestinationPath .tools/jdk
    }
    if ($artifact.name -eq 'maven' -and !(Test-Path .tools/maven)) {
        Expand-Archive -LiteralPath $destination -DestinationPath .tools/maven
    }
}
Write-Host 'Archives vérifiées. Java et Maven portables disponibles dans .tools ; EULA inchangée.'
