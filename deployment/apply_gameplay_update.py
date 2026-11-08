"""Mise à jour ciblée FKAmis, serveur arrêté, sans écrasement des données de partie."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import serverlib as lib

PACKAGE=Path(__file__).resolve().parent
ALLOWED={'plugins/FKAmis-1.0.0.jar','FKAmis.sha256','maintenance/serverlib.py','maintenance/host_ops.py'}


def config_defaults(text: str) -> str:
    """Ajoute seulement les défauts manquants, sans réécrire une configuration existante."""
    for key,value in {'players-per-team':'2','damage-debug':'false','disable-native-tips':'true'}.items():
        matches=re.findall(rf'^{re.escape(key)}\s*:\s*([^\n]*)$',text,re.M)
        if len(matches)>1:raise RuntimeError('Clé de configuration dupliquée : '+key)
        if matches:
            scalar=matches[0].split('#',1)[0].strip()
            if key=='players-per-team' and scalar not in ('1','2','3','4'):
                raise RuntimeError('players-per-team doit être un entier de 1 à 4 ; ne pas supprimer state.yml.')
        else:text=text.rstrip()+'\n'+key+': '+value+'\n'
    return text


def protected_files(root: Path):
    paths=list(lib.iter_files(root/'world'))
    for folder in ('plugins/FKAmis','plugins/FallenKingdom'):
        if (root/folder).exists():paths.extend(p for p in lib.iter_files(root/folder) if p.relative_to(root).as_posix()!='plugins/FKAmis/config.yml')
    for name in ('server.properties','whitelist.json','ops.json','banned-players.json','banned-ips.json'):
        if (root/name).exists():paths.append(root/name)
    return {p.relative_to(root).as_posix():lib.digest(p) for p in paths}


def apply(root: Path,package: Path=PACKAGE):
    root=root.resolve();package=package.resolve()
    if not (root/'world/level.dat').is_file() or not (root/'plugins/FKAmis/state.yml').is_file():
        raise RuntimeError('Instance existante avec monde et state.yml requise.')
    manifest=json.loads((package/'UPDATE_MANIFEST.json').read_text(encoding='utf-8'))
    if set(manifest['files'])!=ALLOWED:raise RuntimeError('Payload inattendu.')
    for name,expected in manifest['files'].items():
        source=lib.confined(package/'payload'/name,package/'payload')
        if not source.is_file() or lib.digest(source)!=expected:raise RuntimeError('Payload altéré : '+name)
    folder=root/'.fk-updates'
    if folder.is_symlink():raise RuntimeError('Dossier de sauvegarde symbolique interdit.')
    with lib.maintenance(root):
        lib.validate(root)
        if lib.digest(root/'paper.jar')!=manifest['paperSha256']:raise RuntimeError('Paper 26.3 build 244 requis.')
        current=lib.digest(root/'plugins/FKAmis-1.0.0.jar')
        if current not in [*manifest['previousPluginSha256s'],manifest['files']['plugins/FKAmis-1.0.0.jar']]:
            raise RuntimeError('Révision FKAmis inconnue : conserver les fichiers et vérifier la provenance.')
        config=root/'plugins/FKAmis/config.yml'
        updated=config_defaults(config.read_text(encoding='utf-8'))
        before=protected_files(root)
        backup=folder/('before-gameplay-update-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.zip')
        lib.create_archive(root,backup,excluded_roots=(folder,root/'.fk-backups'))
        for name in sorted(ALLOWED):
            target=lib.confined(root/name,root);target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_name(target.name+'.gameplay-update-new')
            if temporary.exists():raise RuntimeError('Temporaire préexistant à examiner : '+str(temporary))
            shutil.copy2(package/'payload'/name,temporary);temporary.replace(target)
        temporary=config.with_name('config.yml.gameplay-update-new')
        if temporary.exists():raise RuntimeError('Temporaire de configuration préexistant.')
        temporary.write_text(updated,encoding='utf-8');temporary.replace(config)
        lock=root/'RUNTIME_LOCK.json'
        if lock.exists():
            data=json.loads(lock.read_text(encoding='utf-8'));data.setdefault('sha256',{})['plugins/FKAmis-1.0.0.jar']=manifest['files']['plugins/FKAmis-1.0.0.jar']
            data['fkamisUpdate']='gameplay-eight-features'
            lock.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        if protected_files(root)!=before:raise RuntimeError('Données protégées différentes ; ne pas démarrer, restaurer le point complet.')
        lib.validate(root)
    result={'backup':str(backup),'backupSha256':lib.digest(backup),'protectedFiles':len(before),'worldStateRolesAndPropertiesUnchanged':True}
    print(json.dumps(result,ensure_ascii=False),flush=True)
    print('Mise à jour ciblée terminée, serveur laissé arrêté. Lire le guide avant le redémarrage.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--server',type=Path,required=True)
    apply(parser.parse_args().server)
