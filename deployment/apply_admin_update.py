"""Mise à jour ciblée, Python 3.11+, serveur arrêté, sans écrire le monde ni state.yml.

Ce script est livré à côté de serverlib.py et UPDATE_MANIFEST.json.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

import serverlib as lib

PACKAGE = Path(__file__).resolve().parent
ALLOWED = {'plugins/FKAmis-1.0.0.jar', 'FKAmis.sha256', 'maintenance/serverlib.py', 'maintenance/host_ops.py'}


def patch_keys(text: str, updates: dict[str, str], separator='=') -> str:
    for key, value in updates.items():
        pattern=rf'^{re.escape(key)}\s*{re.escape(separator)}.*$'
        if len(re.findall(pattern,text,re.M))>1: raise RuntimeError('Clé dupliquée : '+key)
        replacement=key+separator+(' ' if separator==':' else '')+value
        if re.search(pattern,text,re.M):text=re.sub(pattern,lambda _:replacement,text,flags=re.M)
        else:text=text.rstrip()+'\n'+replacement+'\n'
    return text


def protected_files(root: Path):
    paths=list(lib.iter_files(root/'world'))
    paths.append(root/'plugins/FKAmis/state.yml')
    if (root/'plugins/FKAmis/admins.yml').exists():paths.append(root/'plugins/FKAmis/admins.yml')
    return {p.relative_to(root).as_posix():lib.digest(p) for p in paths}


def apply(root: Path, package: Path = PACKAGE):
    root=root.resolve();package=package.resolve()
    if not (root/'world/level.dat').is_file() or not (root/'plugins/FKAmis/state.yml').is_file():
        raise RuntimeError('Instance existante avec monde et state.yml requise ; aucune installation automatique.')
    manifest=json.loads((package/'UPDATE_MANIFEST.json').read_text(encoding='utf-8'))
    if set(manifest['files'])!=ALLOWED:raise RuntimeError('Contenu de mise à jour inattendu.')
    for name,expected in manifest['files'].items():
        path=lib.confined(package/'payload'/name,package/'payload')
        if not path.is_file() or lib.digest(path)!=expected:raise RuntimeError('Payload altéré : '+name)
    folder=root/'.fk-updates'
    if folder.is_symlink():raise RuntimeError('Dossier de sauvegarde symbolique interdit.')
    with lib.maintenance(root):
        lib.validate(root)
        if lib.digest(root/'paper.jar')!=manifest['paperSha256']:
            raise RuntimeError('Paper 26.3 build 244 officiel requis.')
        current=lib.digest(root/'plugins/FKAmis-1.0.0.jar')
        if current not in [*manifest['previousPluginSha256s'],manifest['files']['plugins/FKAmis-1.0.0.jar']]:
            raise RuntimeError('Révision FKAmis non reconnue ; conserver les fichiers et vérifier la provenance.')
        before=protected_files(root)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup=folder/('before-admin-update-'+stamp+'.zip')
        lib.create_archive(root,backup,excluded_roots=(folder,root/'.fk-backups'))
        print('Sauvegarde complète à froid vérifiée : '+str(backup),flush=True)
        for name in sorted(ALLOWED):
            target=lib.confined(root/name,root);target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_name(target.name+'.admin-update-new')
            if temporary.exists():raise RuntimeError('Fichier temporaire préexistant : conserver et examiner '+str(temporary))
            shutil.copy2(package/'payload'/name,temporary);temporary.replace(target)
        props=root/'server.properties'
        props.write_text(patch_keys(props.read_text(encoding='utf-8'),{
            'max-players':'10','gamemode':'survival','force-gamemode':'false'}),encoding='utf-8')
        config=root/'plugins/FKAmis/config.yml'
        config.write_text(patch_keys(config.read_text(encoding='utf-8'),{'disable-native-tips':'true'},':'),encoding='utf-8')
        lock=root/'RUNTIME_LOCK.json'
        if lock.exists():
            data=json.loads(lock.read_text(encoding='utf-8'));data.setdefault('sha256',{})['plugins/FKAmis-1.0.0.jar']=manifest['files']['plugins/FKAmis-1.0.0.jar']
            data['maxPlayers']=10;data['fkamisUpdate']='administrator-role-and-respawn'
            lock.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        if protected_files(root)!=before:raise RuntimeError('Les données protégées ont changé : ne pas démarrer, utiliser la sauvegarde complète.')
        lib.validate(root)
        result={'backup':str(backup),'backupSha256':lib.digest(backup),'protectedFiles':len(before),
                'worldStateAndExistingAdminsUnchanged':True,'pluginSha256':manifest['files']['plugins/FKAmis-1.0.0.jar']}
    print('Mise à jour locale terminée ; monde, state.yml et rôles existants conservés. Redémarrage humain requis.')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server',type=Path,required=True)
    args=parser.parse_args();apply(args.server)


if __name__=='__main__':main()
