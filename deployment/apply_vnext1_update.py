"""Mise à jour ciblée VNext.1, sur une instance existante arrêtée, sauvegarde complète préalable."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import shutil
import serverlib as lib
import territory_migration as territories

PACKAGE=Path(__file__).resolve().parent
PREVIOUS='fd12c43c0f33fa84f4721d49de2c248c7cd1609f0c502403dc8155975ecc0cee'
PAPER='9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf'
FK='9127a92a5ad621f74b29ab8e53b6785d4ee30dd15f720c82c64f2c6a5973ba3b'
ALLOWED={'plugins/FKAmis-1.0.0.jar','FKAmis.sha256','maintenance/serverlib.py','maintenance/host_ops.py',
         'maintenance/new_match.py','maintenance/map_reader.py','maintenance/new-match-reference.json','maintenance/territory_migration.py'}


def config_defaults(text: str):
    for key,value in {'players-per-team':'2','damage-debug':'false','disable-native-tips':'true','respawn-protection-seconds':'5'}.items():
        matches=re.findall(rf'^{re.escape(key)}\s*:\s*([^\n]*)$',text,re.M)
        if len(matches)>1:raise RuntimeError('Clé de configuration dupliquée : '+key)
        if matches:
            scalar=matches[0].split('#',1)[0].strip()
            if key=='players-per-team' and scalar not in ('1','2','3','4'):raise RuntimeError('Capacité existante invalide ; conserver state.yml.')
            if key=='respawn-protection-seconds' and (not scalar.isdigit() or not 0<=int(scalar)<=30):raise RuntimeError('Protection de respawn invalide : entier 0..30.')
        else:text=text.rstrip()+'\n'+key+': '+value+'\n'
    return text


def protected_files(root: Path):
    paths=list(lib.iter_files(root/'world'))
    for folder in ('world_nether','world_the_end','plugins/FKAmis','plugins/FallenKingdom'):
        if (root/folder).exists():paths.extend(p for p in lib.iter_files(root/folder) if p.relative_to(root).as_posix() not in ('plugins/FKAmis/config.yml','plugins/FKAmis/state.yml'))
    for name in ('whitelist.json','ops.json','banned-players.json','banned-ips.json'):
        if (root/name).exists():paths.append(root/name)
    return {p.relative_to(root).as_posix():lib.digest(p) for p in paths}


def atomic(path: Path,data: bytes):
    temporary=path.with_name(path.name+'.vnext-new');path.parent.mkdir(parents=True,exist_ok=True)
    with temporary.open('xb') as handle:
        handle.write(data);handle.flush()
        import os
        os.fsync(handle.fileno())
    temporary.replace(path)


def apply(root: Path,package: Path=PACKAGE):
    root=root.resolve();package=package.resolve()
    manifest=json.loads((package/'UPDATE_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('schema')!=1 or set(manifest['files'])!=ALLOWED:raise RuntimeError('Payload VNext inattendu.')
    if manifest.get('previousPluginSha256s')!=[PREVIOUS] or manifest.get('paperSha256')!=PAPER:raise RuntimeError('Versions de départ inattendues.')
    for name,expected in manifest['files'].items():
        path=lib.confined(package/'payload'/name,package/'payload')
        if not path.is_file() or lib.digest(path)!=expected:raise RuntimeError('Payload altéré : '+name)
    if not (root/'world/level.dat').is_file() or not (root/'plugins/FKAmis/state.yml').is_file():raise RuntimeError('Instance existante et état de partie requis.')
    folder=root/'.fk-updates'
    if folder.is_symlink():raise RuntimeError('Dossier de sauvegarde symbolique interdit.')
    with lib.maintenance(root):
        lib.validate(root)
        if lib.digest(root/'paper.jar')!=PAPER or lib.digest(root/'plugins/FallenKingdom-2.24.9.jar')!=FK:raise RuntimeError('Paper 26.3-244 et FallenKingdom 2.24.9 intacts requis.')
        if {p.name for p in (root/'plugins').glob('*.jar')}!={'FallenKingdom-2.24.9.jar','FKAmis-1.0.0.jar'}:raise RuntimeError('Deux plugins de production uniquement requis.')
        if lib.digest(root/'plugins/FKAmis-1.0.0.jar') not in (PREVIOUS,manifest['files']['plugins/FKAmis-1.0.0.jar']):raise RuntimeError('Révision FKAmis de départ inconnue ; appliquer d’abord la livraison VNext fd12c43c.')
        for name in ('reset-request.json','settings-transaction.json'):
            if (root/'plugins/FKAmis'/name).exists():raise RuntimeError('Opération en attente à résoudre avant mise à jour : '+name)
        if not (root/'map-v2-construction.json').is_file():raise RuntimeError('Métadonnées de la carte approuvée absentes.')
        state=(root/'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
        if not re.search(r'^schema: 1\s*$',state,re.M):raise RuntimeError('Schéma de state.yml incompatible.')
        if territories.get(state,'vnext','version') not in ('1','2'):raise RuntimeError('Extension VNext future ou invalide : aucune migration.')
        config=root/'plugins/FKAmis/config.yml';updated=config_defaults(config.read_text(encoding='utf-8'))
        capture_radius=float(territories.get(updated,'capture-radius') or '2.5')
        migrated,territory_report=territories.migrate(state,capture_radius=capture_radius)
        metadata_path=root/'map-v2-construction.json';metadata=json.loads(metadata_path.read_text(encoding='utf-8'))
        for base in metadata['bases']:base['radius']=40
        metadata['territoryRevision']='VNext.1'
        properties=root/'server.properties';original_properties=properties.read_text(encoding='utf-8')
        property_count=len(re.findall(r'^allow-flight=.*$',original_properties,re.M))
        if property_count>1:raise RuntimeError('allow-flight dupliqué : intervention humaine requise.')
        changed_properties=re.sub(r'^allow-flight=.*$','allow-flight=true',original_properties,flags=re.M) if property_count else original_properties.rstrip()+'\nallow-flight=true\n'
        registry=json.loads((root/'RUNTIME_LOCK.json').read_text(encoding='utf-8'))
        if registry.get('sha256',{}).get('plugins/FKAmis-1.0.0.jar')!=lib.digest(root/'plugins/FKAmis-1.0.0.jar'):raise RuntimeError('Registre FKAmis incohérent avec le JAR ; résoudre avant migration.')
        before=protected_files(root)
        backup=folder/('before-vnext1-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.zip')
        lib.create_archive(root,backup,excluded_roots=tuple(root/name for name in ('.fk-updates','.fk-backups','.fk-resets')))
        for name in sorted(ALLOWED):atomic(lib.confined(root/name,root),(package/'payload'/name).read_bytes())
        atomic(config,updated.encode('utf-8'))
        atomic(root/'plugins/FKAmis/state.yml',migrated.encode('utf-8'))
        atomic(metadata_path,(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
        atomic(properties,changed_properties.encode('utf-8'))
        lock=root/'RUNTIME_LOCK.json';data=registry
        data.setdefault('sha256',{})['plugins/FKAmis-1.0.0.jar']=manifest['files']['plugins/FKAmis-1.0.0.jar'];data['fkamisUpdate']='vnext.1'
        atomic(lock,(json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
        if protected_files(root)!=before:raise RuntimeError('Données protégées différentes ; ne pas démarrer, restaurer la sauvegarde complète.')
        lib.validate(root)
    result={'backup':str(backup),'backupSha256':lib.digest(backup),'protectedFiles':len(before),'worldInventoriesRolesAndHistoryUnchanged':True,'territories':territory_report,'onlyChangedServerProperty':'allow-flight=true','noCavernGeneration':True,'serverLeftStopped':True}
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--server',type=Path,required=True)
    apply(parser.parse_args().server)
