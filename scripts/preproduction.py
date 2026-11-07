"""Sceller une copie initiale privée sans modifier runtime/map-v2-fixes.

Utilise une sauvegarde intégrale existante et le relevé privé de ses empreintes.
Refuse toute destination existante, tout état déjà joué et tout butin manquant.
"""
from __future__ import annotations

from collections import Counter
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import zipfile

import server
from v2_reference import Reader

ROOT = server.ROOT


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def snapshot(root: Path):
    return {str(p.relative_to(root)): server.digest(p) for p in server.iter_files(root)}


def initial_state(root: Path):
    state = (root / 'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
    for pattern in (r'^day: 0$', r'^started: false$', r"^winner: ''$", r'^eliminated: \[\]$',
                    r'^validated: \[\]$', r'^terrain-validated: \[\]$',
                    r'^  remaining: 1800$', r'^  event: 0$', r'^  history: \[\]$'):
        if not re.search(pattern, state, re.M):
            raise RuntimeError(f'La référence n’est plus initiale : {pattern}')
    if re.search(r'(?im)^.*[a-f0-9]{8}-[a-f0-9-]{27,}', state) or 'objectives:' in state or 'roster:' in state:
        raise RuntimeError('Objectifs, comptes ou roster présents : audit manuel nécessaire.')
    supply = (root / 'plugins/FKAmis/supplies.yml').read_text(encoding='utf-8')
    if not re.search(r'^test-mode: false$', supply, re.M):
        raise RuntimeError('Mode de test des ravitaillements actif.')
    built = json.loads((root / 'map-v2-construction.json').read_text(encoding='utf-8'))
    if len(built['supplies']) != 8 or len(built['bases']) != 4 or len(built['monuments']) != 7:
        raise RuntimeError('Nombre de sites, bases ou monuments inattendu.')
    reader = Reader(root)
    locations = supply.split('locations:\n', 1)[-1]
    sites = re.findall(r'^  (supply-\d+):\n    world: (\w+)\n    x: (-?\d+)\n    y: (-?\d+)\n    z: (-?\d+)', locations, re.M)
    actual_sites = {name: (world, int(x), int(y), int(z)) for name, world, x, y, z in sites}
    expected_sites = {s['id']: ('world', s['x'], s['y'], s['z']) for s in built['supplies']}
    if actual_sites != expected_sites:
        raise RuntimeError('Coordonnées des huit ravitaillements différentes du plan.')
    for _, x, y, z in actual_sites.values():
        if reader.block(x, y, z) != 'minecraft:chest':
            raise RuntimeError('Un coffre de ravitaillement manque dans le monde.')
    chest_count = 0
    for monument in built['monuments']:
        plan = json.loads((ROOT / 'maps/v2/structures' / (monument['id'] + '.json')).read_text(encoding='utf-8'))
        for loot in plan['loot']:
            x, y, z = (monument[k] + loot[k] for k in ('x', 'y', 'z'))
            tile = next((e for e in reader.chunk(x // 16, z // 16).get('block_entities', [])
                         if (e.get('x'), e.get('y'), e.get('z')) == (x, y, z)), {})
            actual = Counter()
            for item in tile.get('Items', tile.get('items', [])):
                actual[item['id']] += item.get('count', item.get('Count', 0))
            expected = Counter()
            for item in loot['items']:
                expected['minecraft:' + item['material'].lower()] += item['amount']
            if actual != expected:
                raise RuntimeError(f'Butin initial différent : {monument["id"]}')
            chest_count += 1
    return {'day': 0, 'started': False, 'roster': 0, 'objectives': 0,
            'bases': 4, 'monuments': 7, 'lootChestsVerified': chest_count,
            'supplySites': 8, 'supplyRemainingSeconds': 1800, 'supplyEvent': 0}


def excluded(name: str) -> str | None:
    parts = Path(name).parts
    if parts[0] in {'libraries', 'versions', 'cache', 'logs', 'crash-reports', '.paper'}:
        return 'caches_logs_histories'
    if parts[0] in {'ops.json', 'whitelist.json', 'usercache.json', 'banned-players.json', 'banned-ips.json'}:
        return 'access_and_account_lists'
    if parts[0] == 'world' and len(parts) > 1 and parts[1] in {'players', 'playerdata', 'stats', 'advancements'}:
        return 'visitor_profiles'
    if parts[0] == 'plugins' and len(parts) > 1 and parts[1] in {'.paper-remapped', 'spark', 'bStats'}:
        return 'plugin_caches_telemetry'
    return None


def prepare(name: str = 'preproduction'):
    reference = json.loads((ROOT / '.cache/preproduction-reference.json').read_text(encoding='utf-8-sig'))
    source = ROOT / reference['source']
    archive = ROOT / reference['archive']
    if server.digest(archive) != reference['sha256']:
        raise RuntimeError('Sauvegarde intégrale différente du relevé.')
    server.verify_archive(archive)
    stage = server.server_dir(name + '-baseline')
    instance = server.server_dir(name)
    if stage.exists() or instance.exists():
        raise RuntimeError('Destinations existantes : choisir de nouveaux noms, ne rien écraser.')
    counts = Counter()
    with server.maintenance(source):
        if snapshot(source) != reference['files']:
            raise RuntimeError('Référence modifiée depuis la sauvegarde.')
        server.validate(source)
        initial = initial_state(source)
        stage.mkdir(parents=True)
        # Lecture de l’archive vérifiée : la source reste strictement en lecture seule.
        with zipfile.ZipFile(archive) as saved:
            for name in saved.namelist():
                if name == 'BACKUP_MANIFEST.json': continue
                reason = excluded(name)
                if reason:
                    counts[reason] += 1
                    continue
                target = server.confined(stage / name, stage)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(saved.read(name))
        # L’autorité règles/équipes est conservée ; seul le cache des visiteurs est retiré.
        native = stage / 'plugins/FallenKingdom/save.yml'
        text = native.read_text(encoding='utf-8')
        text, changes = re.subn(r'^PlayerManager:\n.*?(?=^[^ \n]|\Z)',
                                'PlayerManager:\n  Players: {}\n', text, flags=re.M | re.S)
        if changes != 1:
            raise RuntimeError('Format du cache natif inattendu.')
        native.write_text(text, encoding='utf-8')
        for name in ('ops.json', 'whitelist.json', 'banned-players.json', 'banned-ips.json'):
            (stage / name).write_text('[]\n', encoding='utf-8')
        # Pas de secret même si une configuration future ajoute un mot de passe désactivé.
        properties = stage / 'server.properties'
        props = properties.read_text(encoding='utf-8')
        props = re.sub(r'^rcon.password=.*$', 'rcon.password=', props, flags=re.M)
        properties.write_text(props, encoding='utf-8')
        maintenance = stage / 'maintenance'
        maintenance.mkdir()
        shutil.copy2(ROOT / 'scripts/server.py', maintenance / 'serverlib.py')
        shutil.copy2(ROOT / 'deployment/host_ops.py', maintenance / 'host_ops.py')
        for name in ('start.sh', 'start.ps1'):
            shutil.copy2(ROOT / 'deployment' / name, stage / name)
        # Les plans sont des références de butin ; aucun plugin de construction n'est livré.
        shutil.copytree(ROOT / 'maps/v2/structures', stage / 'reference/structures')
        for document in ('HOST_INSTALLATION', 'BACKUP_RESTORE', 'OFFICIAL_LAUNCH', 'MULTIPLAYER_ACCEPTANCE', 'PRODUCTION_CHECKLIST', 'HOSTING_COMPARISON', 'PREPRODUCTION_AUDIT'):
            shutil.copy2(ROOT / 'docs' / (document + '.md'), stage / (document + '.md'))
        shutil.copy2(ROOT / 'deployment/acceptance-metrics.example.csv', stage / 'acceptance-metrics.example.csv')
        (stage / 'NOTICE.md').write_text(
            'Paquet privé FallenKingdomYC. FallenKingdom officiel de syldium 2.24.9, JAR intact, '
            'CC BY-NC-ND 4.0 : https://github.com/syldium/FallenKingdom\n'
            'FKAmis et structures indépendants : licence MIT du projet.\n'
            'EULA copiée après acceptation explicite du propriétaire pour les tests locaux. '
            'Vérifier personnellement les conditions avant hébergement.\n'
            'Whitelist et opérateurs vides. Aucun compte, secret SFTP ou jeton de panel.\n', encoding='utf-8')
        shutil.copy2(ROOT / 'LICENSE', stage / 'LICENSE-FKAmis.txt')
        jars = {str(p.relative_to(stage)).replace('\\', '/'): server.digest(p)
                for p in (stage / 'paper.jar', *(stage / 'plugins').glob('*.jar'))}
        write_json(stage / 'RUNTIME_LOCK.json', {'javaMajor': 25, 'paper': '26.2-135',
                   'fallenkingdom': '2.24.9', 'fkamis': '1.0.0', 'sha256': jars})
        initial_state(stage)
        server.validate(stage)
        world_paths = [p for p in server.iter_files(stage / 'world')]
        if not all(server.digest(p) == server.digest(source / p.relative_to(stage)) for p in world_paths):
            raise RuntimeError('Un fichier du monde a changé pendant la préparation.')
        files = {p.relative_to(stage).as_posix(): server.digest(p) for p in server.iter_files(stage)}
        write_json(stage / 'DEPLOYMENT_MANIFEST.json', {'schema': 1, 'files': files,
                   'initialState': initial, 'visualValidation': reference['visualValidation']})
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        package = ROOT / 'dist' / f'fallenkingdom-preproduction-26.2-{stamp}.zip'
        server.create_archive(stage, package)
        if snapshot(source) != reference['files']:
            raise RuntimeError('La référence a changé.')
    server.restore(instance, package)
    if snapshot(stage) != snapshot(instance):
        raise RuntimeError('Restauration différente du paquet scellé.')
    report = {'atUtc': datetime.now(timezone.utc).isoformat(),
              'source': reference['source'], 'sourceUnchanged': True,
              'sourceFilesVerified': len(reference['files']),
              'fullBackup': reference['archive'].replace('\\', '/'),
              'fullBackupSha256': reference['sha256'], 'package': package.relative_to(ROOT).as_posix(),
              'packageSha256': server.digest(package), 'packageFiles': len(files) + 1,
              'worldFilesUnchanged': len(world_paths), 'restoredInstance': instance.relative_to(ROOT).as_posix(),
              'restoredByteIdentical': True, 'excludedFileCounts': dict(counts),
              'nativeVisitorCacheCleared': True, 'initialState': initial, 'runtime': jars,
              'visualValidation': reference['visualValidation'], 'authenticatedPlayerTest': 'pending',
              'officialGameStarted': False, 'hostingOrdered': False}
    write_json(ROOT / 'tests/results/preproduction-package.json', report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='preproduction')
    prepare(parser.parse_args().name)
