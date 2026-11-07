"""Recettes techniques de Paper 26.3 dans le worktree de test uniquement.

Prérequis : copie migration-26-3 démarrée avec succès, JAR vérifié en cache,
trois plugins de recette compilés séparément. Aucun client authentifié.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

import server

ROOT = server.ROOT
WORKTREE = ROOT / '.cache/paper-26.3-worktree'


def run(retry_suite: str | None = None, worktree: Path = WORKTREE):
    worktree = server.confined(worktree, ROOT)
    package = json.loads((ROOT / 'tests/results/preproduction-package.json').read_text(encoding='utf-8'))
    baseline = ROOT / package['package']
    smoke = json.loads((worktree / 'tests/results/migration-smoke.json').read_text(encoding='utf-8'))
    if not smoke['passed']:
        raise RuntimeError('Le démarrage de migration doit réussir avant les fixtures.')
    report = {'atUtc': datetime.now(timezone.utc).isoformat(), 'branch': 'test/paper-26.3-preprod',
              'paper': '26.3-244', 'java': smoke['java'], 'smokePassed': True,
              'authenticatedPlayers': 0, 'simulatedPlayersInGameplayProbe': 8,
              'officialGameStarted': False, 'productionAdopted': False, 'checks': []}
    if retry_suite:
        previous = json.loads((ROOT / 'tests/results/paper-26.3-migration.json').read_text(encoding='utf-8'))
        report['checks'] = [c for c in previous['checks'] if c['suite'] != retry_suite]
        report['previousHarnessFailure'] = 'Supply probe expected.json parent folder absent; fixture preparation corrected, production JARs unchanged.'
    output = worktree / 'tests/results'
    suites = [
        ('core', 'probe-migration-core', 'FKRuntimeProbe.jar', ['-Dfkamis.probe=true'],
         [[], ['-Dfkamis.probe.restore=true']], 'PROBE SUCCESS'),
        ('gameplay', 'probe-v2-fixes-migration', 'FKGameplayProbe.jar', ['-Dfk.gameplayprobe=true'],
         [[]], 'GAMEPLAY PROBE SUCCESS'),
        ('supplies', 'map-v2-qa-migration', 'FKMapV2SupplyProbe.jar',
         ['-Dfk.supplyprobe=true', '-Dfk.supplyprobe.reportprefix=v2-fixes-supply'],
         [[], ['-Dfk.supplyprobe.restart=true']], 'SUPPLY PROBE SUCCESS')]
    for label, name, plugin, flags, phases, success in suites:
        if retry_suite and label != retry_suite: continue
        if retry_suite: name += '-retry'
        instance = worktree / 'runtime' / name
        server.restore(instance, baseline)  # Refuse toute fixture déjà existante.
        shutil.copy2(ROOT / '.cache/artifacts/paper-26.3-244.jar', instance / 'paper.jar')
        shutil.copy2(worktree / 'configs/artifacts.lock.json', instance / 'artifacts.lock.json')
        shutil.copy2(ROOT / '.cache' / plugin, instance / 'plugins' / plugin)
        (instance / 'plugins' / plugin.removesuffix('.jar')).mkdir(exist_ok=True)
        # Réutiliser uniquement les dépendances de la même version déjà téléchargées.
        for folder in ('libraries', 'versions', 'cache'):
            source = worktree / 'runtime/migration-26-3' / folder
            if source.exists(): shutil.copytree(source, instance / folder)
        for index, extra in enumerate(phases):
            with server.maintenance(instance, check_worlds=False):
                server.validate(instance)
                command = [str(server.java_path()), '-Xms1G', '-Xmx4G',
                           '-Dstdout.encoding=UTF-8', '-Dstderr.encoding=UTF-8', *flags, *extra,
                           '-jar', 'paper.jar', '--nogui', '--host', '127.0.0.1', '--port', '25582']
                # Ces probes s'arrêtent eux-mêmes. Conserver une console pour stop en cas d'échec.
                process = subprocess.Popen(command, cwd=instance, stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, encoding='utf-8', errors='replace')
                try:
                    log, _ = process.communicate(timeout=240)
                except subprocess.TimeoutExpired:
                    log, _ = process.communicate(input='stop\n', timeout=120)
                suffix = '-retry' if retry_suite else ''
                (output / f'migration-{label}{suffix}-{index}.log').write_text(log, encoding='utf-8')
                passed = success in log and 'PROBE FAILED' not in log and process.returncode == 0
                count = sum('PROBE PASS ' in line for line in log.splitlines())
                errors = [line for line in log.splitlines() if re.search(r'\b(ERROR|SEVERE)\b', line)]
                check = {'suite': label, 'phase': 'initial' if index == 0 else 'restart',
                         'passed': passed and not errors, 'assertions': count, 'errors': errors}
                report['checks'].append(check)
                print(json.dumps(check, ensure_ascii=False), flush=True)
                if not check['passed']:
                    report['passed'] = False
                    (ROOT / 'tests/results/paper-26.3-migration.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
                    raise RuntimeError('Échec de migration ; conserver copie et journal, ne pas adopter.')
    report['passed'] = all(c['passed'] for c in report['checks'])
    report['assertions'] = sum(c['assertions'] for c in report['checks'])
    report['realEightPlayerAcceptance'] = 'pending'
    report['declaredNativeCompatibility'] = 'FallenKingdom 2.24.9 declares 26.2; 26.3 not declared'
    for path in (ROOT / 'tests/results/paper-26.3-migration.json', output / 'migration-summary.json'):
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print('Migration technique terminée ; recette authentifiée et adoption humaine restent nécessaires.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retry-suite', choices=['core', 'gameplay', 'supplies'])
    parser.add_argument('--worktree', type=Path, default=WORKTREE)
    args = parser.parse_args()
    run(args.retry_suite, args.worktree)
