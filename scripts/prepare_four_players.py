"""Préparer un candidat V2.1 privé, sans réseau MineStrator et sans écraser de sortie."""
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import sys
sys.dont_write_bytecode=True
import server
from minestrator_cold_backup import protect_directory
from preproduction_smoke import smoke
from map_reader import Reader
sys.modules['serverlib']=server
sys.path.insert(0,str(server.ROOT/'deployment'))
import host_ops
import new_match

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def files(root):return {p.relative_to(root).as_posix():server.digest(p) for p in server.iter_files(root)}
def setting(path,key,value,separator):
    text=path.read_text(encoding='utf-8-sig');pattern=r'^'+re.escape(key)+re.escape(separator)+r'.*$'
    line=key+separator+value
    text=re.sub(pattern,lambda m:line,text,flags=re.M) if re.search(pattern,text,re.M) else text.rstrip()+'\n'+line+'\n'
    path.write_text(text,encoding='utf-8')

def prepare(work,rollback_report=None):
    rollback_validated=False;rollback_hash=None
    if rollback_report is not None:
        proof=json.loads(rollback_report.read_text(encoding='utf-8'))
        if not all(proof.get(k) is True for k in ('passed','originalsUnchanged','processStarted','historicalStatePreserved','queryRespondedLocally','maintenanceCheckAfterBoot')) or proof.get('paperExitCode')!=0 or proof.get('profile')!='historical-rollback':raise RuntimeError('Preuve de rollback fonctionnel insuffisante')
        rollback_validated=True;rollback_hash=server.digest(rollback_report)
    work=work.resolve();backup=Path.home()/'FKBackups/MS-COLD-20261119-02'
    if work.is_relative_to(server.ROOT) or work.is_relative_to(backup) or backup.is_relative_to(work):raise RuntimeError('Destination privée neuve hors dépôt et sauvegarde requise')
    source=server.ROOT/'.cache/ms15q/runtime/preproduction'
    previous=server.ROOT/'.cache/ms15q/payload/DEPLOYMENT_MANIFEST.json'
    oldmanifest=json.loads(previous.read_text(encoding='utf-8'))
    missing_alias=False
    for name,expected in oldmanifest['files'].items():
        path=source/name
        if name=='server.jar' and not path.exists():
            # Alias Paper conservé sur l'hôte, absent du candidat de construction.
            path=backup/'restore/server.jar';missing_alias=True
            if server.digest(path)!=server.digest(source/'paper.jar'):raise RuntimeError('Alias Paper historique différent')
        if server.digest(path)!=expected:raise RuntimeError('Candidat précédent différent du manifeste : '+name)
    original_world={n:h for n,h in files(source).items() if n.startswith(('world/','world_nether/','world_the_end/'))}
    source_before=files(source)
    protect_directory(work);root=work/'preproduction-candidate';shutil.copytree(source,root)
    if missing_alias:shutil.copy2(backup/'restore/server.jar',root/'server.jar')
    with server.maintenance(root):
        shutil.copy2(server.PLUGIN,root/'plugins/FKAmis-1.0.0.jar');jar=server.digest(server.PLUGIN)
        (root/'FKAmis.sha256').write_text(jar+'\n',encoding='ascii')
        registry=json.loads((root/'RUNTIME_LOCK.json').read_text(encoding='utf-8-sig'));registry['sha256']['plugins/FKAmis-1.0.0.jar']=jar;registry['fkamisUpdate']='VNext.1 / quatre membres, 2026-11-20';write(root/'RUNTIME_LOCK.json',registry)
        setting(root/'plugins/FKAmis/config.yml','players-per-team','4',': ')
        setting(root/'plugins/FKAmis/state.yml','players-per-team','4',': ')
        setting(root/'server.properties','max-players','20','=')
        # Profil MineStrator explicite : conserver Query pour la liste des joueurs MineBoard.
        setting(root/'server.properties','enable-query','true','=')
        setting(root/'server.properties','query.port','22880','=')
        shutil.copy2(server.ROOT/'scripts/server.py',root/'maintenance/serverlib.py')
        shutil.copy2(server.ROOT/'deployment/host_ops.py',root/'maintenance/host_ops.py')
        host_ops.check(root,'v21-minestrator')
        checks=new_match.initial_checks(root,root/'maintenance/new-match-reference-v2.1.json')
        if {n:server.digest(root/n) for n in original_world}!=original_world:raise RuntimeError('Modification de carte interdite')
        if any('/playerdata/' in n or '/players/data/' in n for n in original_world):raise RuntimeError('Profils de joueur inattendus')
        oldprops=server.properties(source/'server.properties');props=server.properties(root/'server.properties')
        changes={k:{'before':oldprops.get(k),'after':props.get(k)} for k in oldprops.keys()|props.keys() if oldprops.get(k)!=props.get(k)}
        if set(changes)-{'max-players','enable-query','query.port'}:raise RuntimeError('Autre paramètre hébergeur modifié')
        if props['server-port']!='22880' or props['online-mode']!='true' or props['white-list']!='true' or props['enforce-whitelist']!='true':raise RuntimeError('Profil MineStrator ou whitelist invalide')
        # Quatre positions distinctes autour du spawn, critère conservateur air + sol plein connu.
        reader=Reader(root);reference=json.loads((root/'maintenance/new-match-reference-v2.1.json').read_text(encoding='utf-8'))
        spawn_audit=[];solid={'minecraft:grass_block','minecraft:dirt','minecraft:stone','minecraft:andesite','minecraft:granite','minecraft:diorite','minecraft:coarse_dirt','minecraft:rooted_dirt','minecraft:podzol','minecraft:moss_block','minecraft:gravel','minecraft:sand','minecraft:deepslate'}
        air={'minecraft:air','minecraft:cave_air','minecraft:void_air','minecraft:short_grass','minecraft:fern'}
        for base in reference['bases']:
            at=base['spawn'];x,y,z=math.floor(at['x']),math.floor(at['y']),math.floor(at['z']);positions=[]
            for dx in range(-2,3):
                for dz in range(-2,3):
                    if reader.block(x+dx,y-1,z+dz) in solid and reader.block(x+dx,y,z+dz) in air and reader.block(x+dx,y+1,z+dz) in air:positions.append([x+dx,y,z+dz])
            spawn_audit.append({'team':base['team'],'safeAdjacentCellsConservative':len(positions),'atLeastFourCells':len(positions)>=4,'radius':base['radius'],'territoryColumns':81*81})
        write(work/'spawn-audit.json',spawn_audit)
    # Le candidat préparé ne démarre jamais : démarrer exclusivement une seconde copie jetable.
    probe=work/'preproduction-smoke';shutil.copytree(root,probe)
    startup=smoke(probe,work/'startup-private.json',server.java_path(),25638,settle_seconds=10,expected_query_capacity=20)
    if not startup['passed'] or startup['errors']:raise RuntimeError('Démarrage de recette du candidat refusé')
    backupmanifest=json.loads((backup/'manifest.json').read_text(encoding='utf-8'))['files']
    oldplan=json.loads((server.ROOT/'.cache/ms15q/transfer-plan-private.json').read_text(encoding='utf-8'))
    names={f['path'] for f in oldplan['files']};names.discard('DEPLOYMENT_MANIFEST.json');names.update(('plugins/FKAmis-1.0.0.jar','server.properties'))
    payload=work/'payload';payload.mkdir()
    for name in sorted(names):
        target=payload/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
    retained={n:h for n,h in oldplan['retainUnchanged'].items() if n not in names}
    for n,h in retained.items():
        if server.digest(root/n)!=h:raise RuntimeError('Fichier retenu modifié : '+n)
    deploy={'schema':1,'revision':'V2.1-quatre-membres-query-20261120','validationProfile':'v21-minestrator','enableQuery':True,'queryPort':22880,'files':{**files(payload),**retained},'maxPlayers':20,'playersPerTeam':4,'maxParticipants':16,'arbiterExcluded':True,'requiresColdBackupAndExplicitApproval':True,'scope':'Nouvelle partie, aucun état historique importé'}
    write(payload/'DEPLOYMENT_MANIFEST.json',deploy)
    write(root/'DEPLOYMENT_MANIFEST.json',deploy)
    host_ops.verify(root)
    host_ops.check(root,host_ops.selected_profile(root))
    plan={'schema':1,'executed':False,'remoteWritesPerformed':False,'deploymentAuthorized':False,'sourceBackup':'MS-COLD-20261119-02','supersedesTransferCount':146,'files':[{'path':n,'newSha256':h,'oldSha256':backupmanifest.get(n,{}).get('sha256')} for n,h in sorted(files(payload).items())],'retainUnchanged':retained,'propertyChanges':changes,'rollbackFunctionalValidated':False,'requiresFreshRemoteReadOnlyPreflightBeforeApproval':True}
    scope=['world','world_nether','world_the_end','plugins/FKAmis','plugins/FallenKingdom']
    plan.update({'sourcePreconditionSha256':{n:a['sha256'] for n,a in backupmanifest.items()},
      'quarantineBeforeTransferAfterVerifiedExternalBackup':scope+['BACKUP_MANIFEST.json'],
      'oldFilesInReplacedTrees':[n for n in backupmanifest if any(n==prefix or n.startswith(prefix+'/') for prefix in scope)],
      'alsoPreserveUntouched':oldplan['alsoPreserveUntouched'],'neverMergeOldProgressOrInventories':True,
      'rollback':'Restauration complète du point -02 dans une destination vide ; marqueur et Query à traiter séparément, sans réécrire la sauvegarde.'})
    write(work/'transfer-plan-private.json',plan)
    if files(source)!=source_before:raise RuntimeError('Candidat précédent modifié')
    if {n:server.digest(root/n) for n in original_world}!=original_world:raise RuntimeError('Carte source modifiée')
    with server.maintenance(root):server.create_archive(payload,work/'v21-fourplayers-transfer-private.zip')
    # JAR indépendant public au dépôt de travail (ignoré Git), aucune donnée privée.
    delivery=server.ROOT/'dist/fourplayers-20261120';delivery.mkdir(exist_ok=True)
    artifact=delivery/'FKAmis-1.0.0.jar'
    if artifact.exists():
        if server.digest(artifact)!=jar:raise RuntimeError('Ancien artefact différent, ne pas écraser')
    else:
        shutil.copy2(server.PLUGIN,artifact);(delivery/'FKAmis-1.0.0.jar.sha256').write_text(jar+'\n',encoding='ascii')
    safe={'preparedLocally':True,'deploymentAuthorized':False,'remoteWritesPerformed':False,'remoteConnectionsUsed':False,'newMaxPlayers':20,'historicalMaxPlayers':10,'playersPerTeamMaximum':4,'maxParticipants':16,'fkamisSha256':jar,'sourceManifestVerified':len(oldmanifest['files']),'worldFilesUnchanged':len(original_world),'previousCandidateUnchanged':True,'initialChecks':checks,'spawnAudit':spawn_audit,'localStartupPassed':True,'authenticatedPlayers':0,'privateWork':str(work),'privateArchiveSha256':server.digest(work/'v21-fourplayers-transfer-private.zip'),'transferFiles':len(plan['files']),'supersedes146FilePlan':True,'propertyChanges':changes,'policyFilesPreserved':all(server.digest(root/n)==server.digest(source/n) for n in ('whitelist.json','ops.json','banned-players.json','banned-ips.json','plugins/FKAmis/admins.yml')),'whitelistExtended':False,'humanInspectionPerformed':False,'hostingCapacityAtSeventeenConcurrentUsersMeasured':False,'rollbackFunctionalValidated':False,'readyForRemoteDeployment':False}
    archive_manifest=server.verify_archive(work/'v21-fourplayers-transfer-private.zip')['files']
    if archive_manifest!=files(payload):raise RuntimeError('Archive de transfert différente du payload')
    safe.update({'whitelistEntries':len(json.loads((root/'whitelist.json').read_text(encoding='utf-8-sig'))),
      'transferPlanSha256':server.digest(work/'transfer-plan-private.json'),
      'deploymentManifestSha256':server.digest(payload/'DEPLOYMENT_MANIFEST.json'),
      'all148PayloadAndArchiveHashesVerified':len(archive_manifest)==148,'fullSourcePreconditionFiles':len(backupmanifest)})
    safe.update({'queryEnabled':True,'queryPort':22880,'validationProfile':'v21-minestrator','tcpAndUdpLoopbackVerified':startup['tcpAndUdpLoopbackVerified'],'queryRespondedLocally':startup['queryRespondedLocally']})
    safe.update({'rollbackFunctionalValidated':rollback_validated,'rollbackReportSha256':rollback_hash})
    plan.update({'rollbackFunctionalValidated':rollback_validated,'rollbackReportSha256':rollback_hash,
      'rollback':'Restaurer le point -02 entier dans une destination vide ; réconcilier le seul marqueur FKAmis.sha256 et utiliser les outils externes avec le profil historical-rollback. Garder dix places et Query actif.'})
    write(work/'transfer-plan-private.json',plan);safe['transferPlanSha256']=server.digest(work/'transfer-plan-private.json')
    write(work/'preparation.json',safe);write(server.ROOT/'tests/results/query-v21-candidate.json',safe)
    print(json.dumps({'preparedLocally':True,'transferFiles':safe['transferFiles'],'worldFilesUnchanged':len(original_world),'startupPassed':True,'spawnAudit':spawn_audit}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--rollback-report',type=Path);args=parser.parse_args();prepare(args.work,args.rollback_report)
