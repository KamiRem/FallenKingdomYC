param([switch]$SkipTests, [switch]$Probe, [switch]$MapV2, [switch]$Corrections, [switch]$Migration, [switch]$Administration, [switch]$Features)
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
if ($Migration) {
    New-Item -ItemType Directory -Force .cache/migration-native/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/MigrationNativeProbe*.class .cache/migration-native/fr/fkamis/
    Copy-Item tests/migration-native-plugin.yml .cache/migration-native/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKMigrationNativeProbe.jar -C .cache/migration-native .
    if ($LASTEXITCODE -ne 0) { throw 'Création de la recette native de migration impossible.' }
}
if ($Administration) {
    New-Item -ItemType Directory -Force .cache/admin-respawn/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/AdminRespawnProbe*.class .cache/admin-respawn/fr/fkamis/
    Copy-Item tests/admin-respawn-plugin.yml .cache/admin-respawn/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKAdminRespawnProbe.jar -C .cache/admin-respawn .
    if ($LASTEXITCODE -ne 0) { throw 'Création de la recette administrateur impossible.' }
}
if ($MapV2) {
    New-Item -ItemType Directory -Force .cache/map-v2-builder/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/MapV2Builder*.class .cache/map-v2-builder/fr/fkamis/
    Copy-Item tests/map-v2-builder-plugin.yml .cache/map-v2-builder/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKMapV2Builder.jar -C .cache/map-v2-builder .
    if ($LASTEXITCODE -ne 0) { throw "Création de l'outil de chantier impossible." }
    New-Item -ItemType Directory -Force .cache/map-v2-supply-probe/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/MapV2SupplyProbe*.class .cache/map-v2-supply-probe/fr/fkamis/
    Copy-Item tests/map-v2-supply-plugin.yml .cache/map-v2-supply-probe/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKMapV2SupplyProbe.jar -C .cache/map-v2-supply-probe .
    if ($LASTEXITCODE -ne 0) { throw 'Création du plugin de recette impossible.' }
}
if ($Corrections) {
    New-Item -ItemType Directory -Force .cache/v2-corrections/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/MapV2Corrections*.class .cache/v2-corrections/fr/fkamis/
    Copy-Item tests/v2-corrections-plugin.yml .cache/v2-corrections/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKMapV2Corrections.jar -C .cache/v2-corrections .
    if ($LASTEXITCODE -ne 0) { throw 'Création du nettoyeur impossible.' }
    New-Item -ItemType Directory -Force .cache/gameplay-probe/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/GameplayProbe*.class .cache/gameplay-probe/fr/fkamis/
    Copy-Item tests/gameplay-probe-plugin.yml .cache/gameplay-probe/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKGameplayProbe.jar -C .cache/gameplay-probe .
    if ($LASTEXITCODE -ne 0) { throw 'Création de la recette gameplay impossible.' }
}
if ($Features) {
    New-Item -ItemType Directory -Force .cache/features-probe/fr/fkamis | Out-Null
    Copy-Item plugins-custom/fk-amis/target/test-classes/fr/fkamis/FeaturesProbe*.class .cache/features-probe/fr/fkamis/
    Copy-Item tests/features-plugin.yml .cache/features-probe/plugin.yml
    & "$($jdk.FullName)/bin/jar.exe" --create --file .cache/FKFeaturesProbe.jar -C .cache/features-probe .
    if ($LASTEXITCODE -ne 0) { throw 'Création de la recette des fonctionnalités impossible.' }
}
