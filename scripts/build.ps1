param([switch]$SkipTests, [switch]$Probe)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$jdk = Get-ChildItem .tools/jdk -Directory | Select-Object -First 1
$maven = Get-ChildItem .tools/maven -Directory | Select-Object -First 1
if (!$jdk -or !$maven) { throw 'Exécuter scripts/bootstrap.ps1 au préalable.' }
$env:JAVA_HOME = $jdk.FullName
$env:PATH = "$($jdk.FullName)\bin;$env:PATH"
$arguments = @('-B', '--no-transfer-progress', "-Dmaven.repo.local=$repo/.cache/m2", '-f', 'plugins-custom/fk-amis/pom.xml', 'verify')
if ($SkipTests) { $arguments += '-DskipTests' }
& "$($maven.FullName)/bin/mvn.cmd" @arguments
if ($LASTEXITCODE -ne 0) { throw 'La compilation ou les tests ont échoué.' }
if ($Probe) {
    New-Item -ItemType Directory -Force .cache/probe/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/RuntimeProbe*.class .cache/probe/fr/fkamis/
    Copy-Item tests/probe-plugin.yml .cache/probe/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKRuntimeProbe.jar -C .cache/probe .
    if ($LASTEXITCODE -ne 0) { throw 'Création du JAR de recette impossible.' }
}
