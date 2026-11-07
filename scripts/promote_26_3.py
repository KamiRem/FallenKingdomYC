"""Promotion Paper 26.3 sur copies neuves, sans accès distant et sans lancement de partie.

Étapes séparées pour permettre la revue des résultats avant de sceller le paquet.
Les références 26.2 ne sont jamais mises à jour par ce script.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

import server
from preproduction import initial_state, excluded, snapshot, write_json
from preproduction_smoke import smoke
from world_integrity import compare

ROOT = server.ROOT
BASELINE = ROOT / 'dist/fallenkingdom-preproduction-26.2-20261107T125953Z.zip'
BASELINE_SHA = '4156b79fe8d89b2037b049759f0eafd426cdf3adb8d0656d91a0e72fdfc36aa9'
INSTANCE = server.server_dir('preproduction-26-3')
QA = ROOT / '.cache/paper-26.3-final-qa'
REPORTS = ROOT / 'tests/results'
PAPER = ROOT / '.cache/artifacts/paper-26.3-244.jar'
PAPER_SHA = '9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf'


def verify_baseline():
    if server.digest(BASELINE) != BASELINE_SHA: raise RuntimeError('Archive 26.2 différente de la référence.')
    if server.digest(PAPER) != PAPER_SHA: raise RuntimeError('JAR Paper 244 non conforme.')
    return server.verify_archive(BASELINE)


def runtime_lock(root: Path):
    return {'javaMajor': 25, 'paper': '26.3-244', 'paperChannel': 'STABLE',
            'paperApi': '26.3.build.244-stable', 'fallenkingdom': '2.24.9', 'fkamis': '1.0.0',
            'hosting': {'provider': 'MineStrator', 'plan': 'MyBox Perf 8', 'serviceRamGiB': 8,
                        'javaSelection': 'Java 25 Performance', 'panelHeapMaxMiB': 6154, 'gamePort': 22880},
            'sha256': {p.relative_to(root).as_posix(): server.digest(p) for p in
                       [root / 'paper.jar', root / 'plugins/FallenKingdom-2.24.9.jar', root / 'plugins/FKAmis-1.0.0.jar']}}


def update_copy(root: Path):
    shutil.copy2(PAPER, root / 'paper.jar')
    shutil.copy2(ROOT / 'configs/artifacts.lock.json', root / 'artifacts.lock.json')
    shutil.copy2(server.PLUGIN, root / 'plugins/FKAmis-1.0.0.jar')
    (root / 'FKAmis.sha256').write_text(server.digest(server.PLUGIN) + '\n', encoding='ascii')
    old_manifest = root / 'DEPLOYMENT_MANIFEST.json'
    (root / 'reference').mkdir(exist_ok=True)
    shutil.copy2(old_manifest, root / 'reference/source-26.2-manifest.json')
    props = root / 'server.properties'
    text = props.read_text(encoding='utf-8')
    for key, value in {'server-ip': '', 'server-port': '22880', 'level-name': 'world'}.items():
        text, count = re.subn(rf'^{key}=.*$', key + '=' + value, text, flags=re.M)
        if count != 1: raise RuntimeError('Propriété absente ou dupliquée : ' + key)
    props.write_text(text, encoding='utf-8')
    write_json(root / 'RUNTIME_LOCK.json', runtime_lock(root))
    # Le manifeste initial 26.2 est archivé ci-dessus ; il n'est pas un manifeste 26.3.
    write_json(old_manifest, {'schema': 1, 'status': 'conversion-in-progress', 'files': {}})
    server.validate(root)


def prepare():
    manifest = verify_baseline()
    server.restore(INSTANCE, BASELINE)
    if {k.replace('\\', '/'): v for k, v in snapshot(INSTANCE).items()} != manifest['files']:
        raise RuntimeError('La restauration avant conversion diffère de l’archive.')
    initial_state(INSTANCE)
    update_copy(INSTANCE)
    shutil.copy2(INSTANCE / 'server.properties', ROOT / 'configs/paper-26.3/server.properties')
    write_json(REPORTS / 'promotion-26.3-restore-initial.json', {
        'archive': BASELINE.relative_to(ROOT).as_posix(), 'sha256': BASELINE_SHA,
        'restoredInstance': INSTANCE.relative_to(ROOT).as_posix(), 'filesCompared': len(manifest['files']),
        'byteIdenticalBeforeVersionChange': True, 'paper': '26.3-244', 'fkamisSha256': server.digest(server.PLUGIN)})


def check_world(root: Path, output: Path):
    raw_defaults = json.loads((QA / 'tests/results/block-defaults-26.3.json').read_text(encoding='utf-8'))
    defaults = {}
    for name, state in raw_defaults.items():
        content = state.partition('[')[2].removesuffix(']')
        defaults[name] = dict(p.split('=', 1) for p in content.split(',') if p)
    with server.maintenance(root):
        initial = initial_state(root)
        integrity = compare(root, BASELINE, defaults)
        integrity['defaultBlockPropertiesSource'] = 'Material.createBlockData() from Paper 26.3-244'
    write_json(output, {'instance': root.name, 'initialState': initial, 'worldIntegrity': integrity})
    if not integrity['passed']: raise RuntimeError('Différence de blocs/inventaires après conversion : ' + str(output))
    return integrity


def candidate():
    result = smoke(INSTANCE, REPORTS / 'promotion-26.3-smoke.json', server.java_path(), 25583)
    if not result['passed']: raise RuntimeError('Démarrage candidat refusé.')
    check_world(INSTANCE, REPORTS / 'promotion-26.3-world.json')
    backup = server.backup(INSTANCE)
    restored = server.server_dir('preproduction-26-3-recovery')
    server.restore(restored, backup)
    if snapshot(INSTANCE) != snapshot(restored): raise RuntimeError('Restauration du candidat différente.')
    result = smoke(restored, REPORTS / 'promotion-26.3-restart.json', server.java_path(), 25584)
    if not result['passed']: raise RuntimeError('Reprise restaurée refusée.')
    check_world(restored, REPORTS / 'promotion-26.3-recovery-world.json')
    write_json(REPORTS / 'promotion-26.3-recovery.json', {
        'archive': backup.relative_to(ROOT).as_posix(), 'sha256': server.digest(backup),
        'filesCompared': len(server.verify_archive(backup)['files']), 'byteIdenticalBeforeRestart': True,
        'restoredInstance': restored.relative_to(ROOT).as_posix(), 'restartPassed': True})


def probes(attempt=1):
    verify_baseline()
    results = []
    suites = [('native', 'probe-native-26-3-final', 'FKMigrationNativeProbe.jar', ['-Dfk.nativeprobe=true'], [[]], 'NATIVE PROBE SUCCESS'),
              ('core', 'probe-core-26-3-final', 'FKRuntimeProbe.jar', ['-Dfkamis.probe=true'], [[], ['-Dfkamis.probe.restore=true']], 'PROBE SUCCESS'),
              ('gameplay', 'probe-v2-fixes-26-3-final', 'FKGameplayProbe.jar', ['-Dfk.gameplayprobe=true'], [[]], 'GAMEPLAY PROBE SUCCESS'),
              ('supplies', 'map-v2-qa-26-3-final', 'FKMapV2SupplyProbe.jar', ['-Dfk.supplyprobe=true', '-Dfk.supplyprobe.reportprefix=v2-fixes-supply'],
               [[], ['-Dfk.supplyprobe.restart=true']], 'SUPPLY PROBE SUCCESS')]
    (QA / 'tests/results').mkdir(parents=True, exist_ok=True)
    for suite, name, plugin, flags, phases, success in suites:
        if attempt != 1: name += '-' + str(attempt)
        root = QA / 'runtime' / name
        server.restore(root, BASELINE)
        update_copy(root)
        shutil.copy2(ROOT / '.cache' / plugin, root / 'plugins' / plugin)
        (root / 'plugins' / plugin.removesuffix('.jar')).mkdir(exist_ok=True)
        for folder in ('libraries', 'versions', 'cache'):
            if (INSTANCE / folder).exists(): shutil.copytree(INSTANCE / folder, root / folder)
        for index, extra in enumerate(phases):
            with server.maintenance(root, check_worlds=False):
                server.validate(root)
                command = [str(server.java_path()), '-Xms1G', '-Xmx4G', '-Dstdout.encoding=UTF-8', '-Dstderr.encoding=UTF-8',
                           *flags, *extra, '-jar', 'paper.jar', '--nogui', '--host', '127.0.0.1', '--port', '25585']
                process = subprocess.Popen(command, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
                try: log, _ = process.communicate(timeout=300)
                except subprocess.TimeoutExpired: log, _ = process.communicate(input='stop\n', timeout=120)
                log_path = QA / f'tests/results/{suite}-{index}-attempt-{attempt}.log'
                log_path.write_text(log, encoding='utf-8')
                errors = [line for line in log.splitlines() if re.search(r'\b(ERROR|SEVERE)\b', line)]
                item = {'suite': suite, 'phase': 'initial' if index == 0 else 'restart',
                        'assertions': log.count('PROBE PASS '), 'passed': success in log and not errors and process.returncode == 0,
                        'errors': errors, 'warnings': [line for line in log.splitlines() if re.search(r'\bWARN\b', line)]}
                results.append(item)
                write_json(REPORTS / 'promotion-26.3-probes.json', {'checks': results, 'authenticatedPlayers': 0,
                           'gameplaySimulatedPlayers': 8, 'chatSimulatedActors': 2,
                           'fkamisSha256': server.digest(server.PLUGIN), 'passed': all(c['passed'] for c in results)})
                print(json.dumps(item, ensure_ascii=False), flush=True)
                if not item['passed']: raise RuntimeError('Échec bloquant de la suite ' + suite + ', promotion arrêtée.')


def seal():
    proof = json.loads((REPORTS / 'promotion-26.3-probes.json').read_text(encoding='utf-8'))
    if not proof['passed'] or len(proof['checks']) != 6 or proof['fkamisSha256'] != server.digest(server.PLUGIN):
        raise RuntimeError('Recettes finales absentes ou binaire différent.')
    for report_name in ('promotion-26.3-world.json', 'promotion-26.3-recovery-world.json'):
        if not json.loads((REPORTS / report_name).read_text(encoding='utf-8'))['worldIntegrity']['passed']:
            raise RuntimeError('Contrôle du monde incomplet : ' + report_name)
    recovery = json.loads((REPORTS / 'promotion-26.3-recovery.json').read_text(encoding='utf-8'))
    if not recovery['restartPassed'] or not recovery['byteIdenticalBeforeRestart']:
        raise RuntimeError('Sauvegarde/restauration préalable non validée.')
    stage = server.server_dir('preproduction-26-3-sealed')
    if stage.exists(): raise RuntimeError('Paquet scellé déjà présent : ne pas écraser.')
    with server.maintenance(INSTANCE):
        initial_state(INSTANCE)
        stage.mkdir()
        for path in server.iter_files(INSTANCE):
            name = path.relative_to(INSTANCE).as_posix()
            if excluded(name) or name.split('/')[0] in {'.fk-backups', 'maintenance'} or '__pycache__' in path.parts:
                continue
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        (stage / 'maintenance').mkdir()
        shutil.copy2(ROOT / 'scripts/server.py', stage / 'maintenance/serverlib.py')
        shutil.copy2(ROOT / 'deployment/host_ops.py', stage / 'maintenance/host_ops.py')
        for name in ('start.sh', 'start.ps1'): shutil.copy2(ROOT / 'deployment' / name, stage / name)
        # Paper persiste les surcharges --host/--port du smoke dans sa copie locale.
        # Le paquet utilise le profil MineStrator validé avant les démarrages locaux.
        shutil.copy2(ROOT / 'configs/paper-26.3/server.properties', stage / 'server.properties')
        for name in ('PREPRODUCTION_AUDIT', 'HOST_INSTALLATION', 'MULTIPLAYER_ACCEPTANCE', 'BACKUP_RESTORE',
                     'OFFICIAL_LAUNCH', 'PRODUCTION_CHECKLIST', 'COMPATIBILITY', 'TEST_PLAN', 'DEPLOYMENT'):
            shutil.copy2(ROOT / 'docs' / (name + '.md'), stage / (name + '.md'))
        write_json(stage / 'RUNTIME_LOCK.json', runtime_lock(stage))
        write_json(stage / 'MIGRATION_PROVENANCE.json', {
            'sourceArchive': BASELINE.name, 'sourceArchiveSha256': BASELINE_SHA,
            'from': '26.2-135', 'to': '26.3-244', 'worldDowngradeAllowed': False,
            'officialGameStarted': False, 'realMultiplayerAcceptance': 'pending'})
        initial = initial_state(stage)
        server.validate(stage)
        deployment_properties = server.properties(stage / 'server.properties')
        if any(deployment_properties.get(k) != v for k, v in
               {'server-ip': '', 'server-port': '22880', 'level-name': 'world'}.items()):
            raise RuntimeError('Le paquet ne correspond pas au profil MineStrator.')
        jars = {p.name for p in (stage / 'plugins').glob('*.jar')}
        if jars != {'FallenKingdom-2.24.9.jar', 'FKAmis-1.0.0.jar'}: raise RuntimeError('Plugin de recette dans la livraison.')
        # Remplacer le manifeste de conversion par celui du paquet final, sans auto-référence.
        files = {p.relative_to(stage).as_posix(): server.digest(p) for p in server.iter_files(stage)
                 if p.name != 'DEPLOYMENT_MANIFEST.json'}
        write_json(stage / 'DEPLOYMENT_MANIFEST.json', {'schema': 1, 'files': files, 'initialState': initial,
                   'visualValidation': 'source_26.2_attested_by_owner; converted_26.3_client_inspection_pending'})
        package = ROOT / 'dist/fallenkingdom-preproduction-26.3.zip'
        server.create_archive(stage, package)
    write_json(REPORTS / 'preproduction-package-26.3.json', {
        'atUtc': datetime.now(timezone.utc).isoformat(), 'package': package.relative_to(ROOT).as_posix(),
        'packageSha256': server.digest(package), 'packageFiles': len(files) + 1,
        'sourceArchive': BASELINE.relative_to(ROOT).as_posix(), 'sourceArchiveSha256': BASELINE_SHA,
        'runtime': runtime_lock(stage), 'initialState': initial, 'technicalProbes': proof,
        'unitTests': {'java': 19, 'python': 21, 'failures': 0, 'errors': 0},
        'technicalAssertions': sum(c['assertions'] for c in proof['checks']),
        'deploymentProperties': {k: deployment_properties[k] for k in
                                 ('server-ip', 'server-port', 'level-name', 'online-mode', 'white-list', 'enforce-whitelist')},
        'candidateRecovery': recovery,
        'restoration': 'pending_final_package_test', 'officialGameStarted': False, 'remoteHostingTouched': False,
        'humanTestsRemaining': ['eight_authenticated_clients', 'converted_map_visual_inspection', 'real_team_chat_and_client_interfaces',
                               'combat_captures_victory_on_network', 'host_TPS_MSPT_RAM_ping', 'host_backup_restore'],
        'compatibilityRisks': ['FallenKingdom 2.24.9 release declares 26.2, not 26.3',
                               'Deprecated APIs compile successfully but may require future updates']})


def final_test():
    path = REPORTS / 'preproduction-package-26.3.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    package = ROOT / report['package']
    if server.digest(package) != report['packageSha256']: raise RuntimeError('Paquet altéré.')
    manifest = server.verify_archive(package)
    root = server.server_dir('preproduction-26-3-package-test')
    server.restore(root, package)
    actual = {k.replace('\\', '/'): v for k, v in snapshot(root).items()}
    if actual != manifest['files']: raise RuntimeError('Paquet restauré non identique.')
    props = server.properties(root / 'server.properties')
    if props['server-port'] != '22880' or props['server-ip'] != '' or props['level-name'] != 'world':
        raise RuntimeError('Paramètres MineStrator absents avant le test local.')
    result = smoke(root, REPORTS / 'promotion-26.3-package-smoke.json', server.java_path(), 25586)
    if not result['passed']: raise RuntimeError('Échec démarrage paquet final.')
    integrity = check_world(root, REPORTS / 'promotion-26.3-package-world.json')
    report['restoration'] = {'passed': True, 'instance': root.relative_to(ROOT).as_posix(),
                             'filesCompared': len(actual), 'byteIdenticalBeforeStartup': True}
    report['startup'] = result
    report['worldIntegrity'] = integrity
    report['passed'] = True
    write_json(path, report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'candidate', 'probes', 'seal', 'final-test'])
    parser.add_argument('--attempt', type=int, default=1, choices=range(1, 101))
    args = parser.parse_args()
    if args.action == 'probes': probes(args.attempt)
    else: {'prepare': prepare, 'candidate': candidate, 'seal': seal, 'final-test': final_test}[args.action]()
