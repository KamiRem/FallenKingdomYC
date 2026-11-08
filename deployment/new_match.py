"""Préparation et restauration de parties, uniquement à froid et avec confirmation explicite."""
from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import shutil
import time
import serverlib as lib
from map_reader import Reader

PAPER='9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf'
FK='9127a92a5ad621f74b29ab8e53b6785d4ee30dd15f720c82c64f2c6a5973ba3b'
TEAMS=('Rouge','Bleue','Verte','Jaune')
POLICY_FILES=('plugins/FKAmis/config.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml',
              'server.properties','whitelist.json','ops.json','banned-players.json','banned-ips.json')


def policies(root: Path):
    """Une restauration complète ne fusionne jamais des règles ou rôles de deux instants."""
    result={name:lib.digest(root/name) if (root/name).is_file() else None for name in POLICY_FILES}
    # Java réécrit la date en commentaire à chaque démarrage ; comparer toutes
    # les propriétés effectives, sans prendre ce commentaire pour un changement.
    if (root/'server.properties').is_file():result['server.properties']=hashlib.sha256(json.dumps(lib.properties(root/'server.properties'),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return result


def write(path: Path,text: str):
    temporary=path.with_name(path.name+'.new')
    with temporary.open('x',encoding='utf-8') as handle:
        handle.write(text);handle.flush()
        import os
        os.fsync(handle.fileno())
    temporary.replace(path)


def section(text: str,path: tuple[str,...]):
    """Lecture conservatrice des seules clés connues écrites par Bukkit, sans réécrire le YAML."""
    lines=text.splitlines();start=0;end=len(lines);indent=0;value=''
    for key in path:
        found=None
        for index in range(start,end):
            line=lines[index]
            match=re.fullmatch(' '*indent+re.escape(key)+r':(?:\s*(.*))?',line)
            if match:found=index;value=match.group(1) or '';break
        if found is None:return None
        start=found+1;end=next((i for i in range(start,end) if lines[i].strip() and len(lines[i])-len(lines[i].lstrip())<=indent),end)
        indent+=2
    return value.strip()


def check_versions(root: Path):
    lib.validate(root)
    if lib.digest(root/'paper.jar')!=PAPER or lib.digest(root/'plugins/FallenKingdom-2.24.9.jar')!=FK:raise RuntimeError('Paper 26.3-244 / FallenKingdom 2.24.9 requis, sans changement de version.')
    if {p.name for p in (root/'plugins').glob('*.jar')}!={'FallenKingdom-2.24.9.jar','FKAmis-1.0.0.jar'}:raise RuntimeError('Les deux plugins de production uniquement sont requis.')


def initial_checks(root: Path,reference: Path):
    check_versions(root);state=(root/'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
    if section(state,('schema',))!='1' or section(state,('vnext','version'))!='1':raise RuntimeError('État VNext initial requis ; versions futures refusées.')
    for path,value in [(('day',),'0'),(('started',),'false'),(('winner',),"''"),(('eliminated',),'[]')]:
        if section(state,path)!=value:raise RuntimeError('La partie n’est plus initiale : '+'.'.join(path))
    for key in ('roster','objectives'):
        if section(state,(key,)) not in (None,'{}'):raise RuntimeError('État initial sans joueurs attribués ni objectifs requis.')
    for team in TEAMS:
        if section(state,('native','TeamManager',team,'Members'))!='[]':raise RuntimeError('Affiliations natives non vides.')
    if (root/'plugins/FKAmis/reset-request.json').exists():raise RuntimeError('Une demande de reset est en attente.')
    data=json.loads(reference.read_text(encoding='utf-8'));built=json.loads((root/'map-v2-construction.json').read_text(encoding='utf-8'))
    if len(built['bases'])!=4 or len(built['monuments'])!=7 or len(built['supplies'])!=8:raise RuntimeError('Quatre bases, sept monuments, huit sites requis.')
    reader=Reader(root);blocks=0
    for monument in data['monuments']:
        actual=next((m for m in built['monuments'] if m['id']==monument['id']),None)
        if actual is None or any(actual[k]!=monument[k] for k in ('x','y','z')):raise RuntimeError('Monument déplacé : '+monument['id'])
        observed=[]
        for dx,dy,dz in monument['checkPoints']:
            observed.append([dx,dy,dz,reader.block(monument['x']+dx,monument['y']+dy,monument['z']+dz)]);blocks+=1
        if hashlib.sha256(json.dumps(observed,separators=(',',':')).encode()).hexdigest()!=monument['blockTypesSha256']:raise RuntimeError('Structure initiale différente : '+monument['id'])
        for loot in monument['loot']:
            x,y,z=loot['at'];tile=next((e for e in reader.chunk(x//16,z//16).get('block_entities',[]) if (e.get('x'),e.get('y'),e.get('z'))==(x,y,z)),{})
            items=tile.get('Items',tile.get('items',[]));actual_hash=hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':'),default=lambda value:value.hex()).encode()).hexdigest()
            if actual_hash!=loot['inventorySha256']:raise RuntimeError('Butin initial consommé ou modifié : '+monument['id'])
    for site in data['supplies']:
        if reader.block(*site['at'])!='minecraft:chest':raise RuntimeError('Support de ravitaillement absent.')
    for base in data['bases']:
        team=base['team']
        for key,expected in base['center'].items():
            if section(state,('native','TeamManager',team,'Base','Center',key))!=str(expected):raise RuntimeError('Territoire de référence différent : '+team)
        if section(state,('native','TeamManager',team,'Base','Radius'))!=str(base['radius']):raise RuntimeError('Rayon de territoire différent.')
        for key,expected in base['spawn'].items():
            actual=section(state,('spawns',team,key))
            if actual is None or abs(float(actual)-float(expected))>1e-6:raise RuntimeError('Spawn d’équipe différent : '+team)
    return {'bases':4,'monuments':7,'monumentBlocksChecked':blocks,'supplySites':8,'lootChestsVerified':sum(len(m['loot']) for m in data['monuments']),'day':0,'started':False}


def seal_baseline(root: Path,archive: Path,reference: Path,approve: bool):
    if not approve:raise RuntimeError('Approbation explicite --approve-initial requise après inspection de la copie initiale.')
    root=root.resolve();archive=archive.resolve()
    if archive.is_relative_to(root):raise RuntimeError('Conserver la référence scellée hors de l’instance à restaurer.')
    with lib.maintenance(root):
        checks=initial_checks(root,reference);lib.create_archive(root,archive,excluded_roots=tuple(root/name for name in ('.fk-backups','.fk-updates','.fk-resets')))
        approval={'schema':1,'sha256':lib.digest(archive),'pluginSha256':lib.digest(root/'plugins/FKAmis-1.0.0.jar'),'paperSha256':PAPER,'policies':policies(root),'checks':checks,'approvedInitial':True,'atUtc':datetime.now(timezone.utc).isoformat()}
        write(archive.with_suffix('.approved.json'),json.dumps(approval,indent=2,ensure_ascii=False)+'\n')
    return approval


def request(root: Path,token: str):
    path=root/'plugins/FKAmis/reset-request.json';data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema')!=1 or data.get('expiresAt',0)<int(time.time()*1000):raise RuntimeError('Demande absente, future ou expirée ; refaire la préparation.')
    if not hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(),data['tokenSha256']):raise RuntimeError('Jeton de confirmation incorrect.')
    if lib.digest(root/'plugins/FKAmis/state.yml')!=data['sourceStateSha256']:raise RuntimeError('Progression différente depuis la confirmation : aucune mutation.')
    if lib.digest(root/'paper.jar')!=data['paperSha256'] or lib.digest(root/'plugins/FKAmis-1.0.0.jar')!=data['pluginSha256']:raise RuntimeError('Binaires différents depuis la confirmation.')
    candidate=lib.confined(root/data['candidateFile'],root/'plugins/FKAmis')
    if candidate!=root/'plugins/FKAmis/reset-candidate.yml' or lib.digest(candidate)!=data['candidateSha256']:raise RuntimeError('Candidat de reset altéré ou inattendu.')
    return data,candidate


def cold_backup(root: Path):
    folder=root/'.fk-resets';folder.mkdir(exist_ok=True)
    if folder.is_symlink():raise RuntimeError('Dossier de reset symbolique interdit.')
    archive=folder/('before-reset-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.zip')
    lib.create_archive(root,archive,excluded_roots=tuple(root/name for name in ('.fk-backups','.fk-updates','.fk-resets')))
    return archive


def logical(root: Path,token: str):
    root=root.resolve()
    with lib.maintenance(root):
        check_versions(root);data,candidate=request(root,token);backup=cold_backup(root)
        protected={p.relative_to(root).as_posix():lib.digest(p) for p in lib.iter_files(root/'world')}
        target=root/'plugins/FKAmis/state.yml';temporary=target.with_name('state.yml.reset-new')
        with candidate.open('rb') as source,temporary.open('xb') as destination:
            shutil.copyfileobj(source,destination);destination.flush()
            import os
            os.fsync(destination.fileno())
        if lib.digest(temporary)!=data['candidateSha256']:raise RuntimeError('Candidat copié différent ; aucune application.')
        temporary.replace(target)
        if {p.relative_to(root).as_posix():lib.digest(p) for p in lib.iter_files(root/'world')}!=protected:raise RuntimeError('Monde modifié pendant le reset : conserver la sauvegarde complète.')
        receipt={'schema':1,'operation':'logical','backup':str(backup),'backupSha256':lib.digest(backup),'worldFilesUnchanged':len(protected),'previousMatchId':data['matchId'],'worldOrInventoriesRestored':False}
        finish(root,receipt)
    return receipt


def restore_initial(root: Path,token: str,archive: Path,destination: Path,reference: Path):
    root=root.resolve();archive=archive.resolve();destination=destination.resolve()
    if destination==root or destination.is_relative_to(root) or root.is_relative_to(destination):raise RuntimeError('Destination distincte, séparée et vide requise.')
    approval=json.loads(archive.with_suffix('.approved.json').read_text(encoding='utf-8'))
    if approval.get('schema')!=1 or not approval.get('approvedInitial') or approval['sha256']!=lib.digest(archive):raise RuntimeError('Archive initiale non approuvée ou altérée.')
    if archive.with_suffix('.zip.sha256').read_text(encoding='ascii').strip()!=approval['sha256']:raise RuntimeError('SHA-256 externe incohérent.')
    with lib.maintenance(root):
        check_versions(root);data,_=request(root,token)
        if approval['pluginSha256']!=data['pluginSha256'] or approval['paperSha256']!=PAPER:raise RuntimeError('La référence doit contenir la même révision VNext et Paper ; aucun ancien JAR réintroduit.')
        if approval.get('policies')!=policies(root):raise RuntimeError('Règles, rôles ou accès différents de la référence initiale : sceller une nouvelle copie initiale approuvée ; aucune fusion silencieuse.')
        backup=cold_backup(root);lib.restore(destination,archive)
        manifest=lib.verify_archive(archive)['files'];actual={p.relative_to(destination).as_posix():lib.digest(p) for p in lib.iter_files(destination)}
        if actual!=manifest:raise RuntimeError('Restauration différente de l’archive initiale.')
        with lib.maintenance(destination):
            if policies(destination)!=approval['policies']:raise RuntimeError('Règles restaurées différentes de l’approbation.')
            checks=initial_checks(destination,reference)
        receipt={'schema':1,'operation':'restore-approved-initial','backup':str(backup),'backupSha256':lib.digest(backup),'destination':str(destination),'restoredFiles':len(actual),'checks':checks,'oldInstanceAndHistoryPreserved':True}
        finish(root,receipt)
    return receipt


def finish(root: Path,receipt: dict):
    folder=root/'.fk-resets';write(folder/('receipt-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'),json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    for name in ('reset-request.json','reset-candidate.yml'):(root/'plugins/FKAmis'/name).unlink()


def cancel(root: Path):
    with lib.maintenance(root):
        for name in ('reset-request.json','reset-candidate.yml'):(root/'plugins/FKAmis'/name).unlink(missing_ok=True)
    return {'cancelled':True,'worldOrStateModified':False}
