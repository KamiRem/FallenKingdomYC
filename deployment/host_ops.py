"""Maintenance portable Python 3.11+, sans dépendance ni identifiants.

Copié dans maintenance/ du paquet. Exécuter depuis n'importe quel dossier.
Le panel doit être arrêté pour configure/backup/restore. Aucun lancement de partie.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

import serverlib as lib

ROOT = Path(__file__).resolve().parents[1]


def verify(root: Path):
    manifest = json.loads((root / 'DEPLOYMENT_MANIFEST.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        path = lib.confined(root / name, root)
        if not path.is_file() or lib.digest(path) != expected:
            raise RuntimeError(f'Fichier initial absent ou modifié : {name}')
    print(f"Manifeste initial : {len(manifest['files'])} empreintes vérifiées.")


def check(root: Path):
    lib.validate(root)
    props = lib.properties(root / 'server.properties')
    for key, value in {'enable-query': 'false', 'pvp': 'true', 'difficulty': 'normal'}.items():
        if props.get(key) != value:
            raise RuntimeError(f'Configuration inattendue : {key}')
    if props.get('rcon.password'):
        raise RuntimeError('Mot de passe RCON présent alors que RCON est désactivé.')
    expected = {'FallenKingdom-2.24.9.jar', 'FKAmis-1.0.0.jar'}
    if {p.name for p in (root / 'plugins').glob('*.jar')} != expected:
        raise RuntimeError('Exactement les deux plugins de production sont requis.')
    print('Authentification, whitelist et profil des deux plugins vérifiés.')


def configure(root: Path, port: int):
    if not 1024 <= port <= 65535:
        raise ValueError('Port attribué par le panel requis : 1024..65535.')
    with lib.maintenance(root):
        check(root)
        path = root / 'server.properties'
        text = path.read_text(encoding='utf-8')
        for key, value in {'server-ip': '', 'server-port': str(port)}.items():
            if not re.search(rf'^{key}=', text, re.M):
                raise RuntimeError(f'Propriété absente : {key}')
            text = re.sub(rf'^{key}=.*$', key + '=' + value, text, flags=re.M)
        path.write_text(text, encoding='utf-8')
    print('Copie configurée pour le port du panel. Le manifeste initial sera désormais différent.')


def backup(root: Path) -> Path:
    folder = root / '.fk-backups'
    if folder.is_symlink():
        raise RuntimeError('Dossier de sauvegarde symbolique interdit.')
    with lib.maintenance(root):
        check(root)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        target = folder / f'fk-{stamp}.zip'
        lib.create_archive(root, target, excluded_roots=(folder,root/'.fk-updates',root/'.fk-resets'))
    print(f'Sauvegarde à froid vérifiée : {target}')
    return target


def restore(archive: Path, destination: Path):
    archive = archive.resolve()
    sidecar = archive.with_suffix(archive.suffix + '.sha256')
    if not sidecar.is_file() or sidecar.read_text(encoding='ascii').split()[0] != lib.digest(archive):
        raise RuntimeError('Empreinte externe absente ou incorrecte.')
    destination = destination.resolve()
    if destination == ROOT or destination.is_relative_to(ROOT) or ROOT.is_relative_to(destination):
        raise RuntimeError('Restaurer dans un dossier séparé de cette installation.')
    lib.restore(destination, archive)
    print('Même version requise. Une archive de partie active peut reprendre active : isoler le réseau avant démarrage.')


def start(root: Path, memory: int, port: int, host: str):
    if not 2 <= memory <= 12 or not 1024 <= port <= 65535:
        raise ValueError('Mémoire 2..12 Go et port valide requis.')
    java = os.environ.get('JAVA_BIN', 'java')
    result = subprocess.run([java, '-version'], capture_output=True, text=True, check=True)
    if not re.search(r'version "25(?:[.\"]|$)', result.stderr + result.stdout):
        raise RuntimeError('Java 25 requis ; définir JAVA_BIN si nécessaire.')
    with lib.maintenance(root, check_worlds=False):
        check(root)
        # Ne pas bloquer session.lock : Java doit acquérir le verrou natif lui-même.
        process = subprocess.Popen([java, '-Xms1G', f'-Xmx{memory}G', '-jar', 'paper.jar',
                                    '--nogui', '--host', host, '--port', str(port)], cwd=root)
        try:
            code = process.wait()
        except KeyboardInterrupt:
            code = process.wait()
        if code:
            raise RuntimeError(f'Java terminé avec le code {code}. Contrôler les journaux.')
    backup(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify-baseline', 'check', 'configure', 'backup', 'restore', 'start','reset-logical','reset-cancel','seal-initial','restore-initial'])
    parser.add_argument('--port', type=int)
    parser.add_argument('--memory', type=int, default=6)
    parser.add_argument('--host', choices=['127.0.0.1', '0.0.0.0'], default='127.0.0.1')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--token')
    parser.add_argument('--approve-initial',action='store_true')
    parser.add_argument('--reference',type=Path,default=Path(__file__).with_name('new-match-reference.json'))
    args = parser.parse_args()
    if args.action == 'verify-baseline': verify(ROOT)
    elif args.action == 'check': check(ROOT)
    elif args.action == 'configure':
        if args.port is None: parser.error('--port attribué requis')
        configure(ROOT, args.port)
    elif args.action == 'backup': backup(ROOT)
    elif args.action == 'restore':
        if args.archive is None or args.destination is None:
            parser.error('--archive et --destination neuve requis')
        restore(args.archive, args.destination)
    elif args.action == 'start':
        if args.port is None: parser.error('--port requis')
        start(ROOT, args.memory, args.port, args.host)
    else:
        import new_match
        if args.action=='reset-cancel':result=new_match.cancel(ROOT)
        elif args.action=='seal-initial':
            if args.archive is None:parser.error('--archive hors instance requis')
            result=new_match.seal_baseline(ROOT,args.archive,args.reference,args.approve_initial)
        else:
            if not args.token:parser.error('--token issu de fka reset confirm requis')
            if args.action=='reset-logical':result=new_match.logical(ROOT,args.token)
            else:
                if args.archive is None or args.destination is None:parser.error('--archive et --destination neuve requis')
                result=new_match.restore_initial(ROOT,args.token,args.archive,args.destination,args.reference)
        print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
