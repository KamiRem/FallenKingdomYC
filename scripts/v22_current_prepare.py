"""Reconstruction et répétition complètes depuis la nouvelle sauvegarde vérifiée."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys
import zipfile
import server
from minestrator_cold_backup import write,digest
from v22_current_local import BACKUP,WORK,files
from v22_shaft_restore import restore_heightmaps,compare_target_chunks,full_text
from vanilla_underground import ArchiveReader,SOURCE
from map_reader import Reader
from terrain_reference import state,normalized,fingerprint,verify as verify_terrain
from anvil_patch import patch_region
from natural_caverns_rework import verify_region
from v22_rebase_plan import canonical,simulate_transfer

BASE=Path.home()/'FKBackups'
APPROVED=BASE/'V22-SHAFT-20261123-01'
OP='MS-DEPLOY-V22-20261123-01'
ATTACHMENT=Path.home()/'.codex/attachments/da51346e-e399-4e8a-9aea-ba1c50edd4a7/Texte collé.txt'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))

def check_backup():
    report=load(BACKUP/'report.json');manifest=load(BACKUP/'manifest.json')
    if not report['backupValidated'] or not report['functionalRestoreValidated']:raise RuntimeError('Sauvegarde fonctionnelle requise')
    if digest(BACKUP/'instance.zip')!=report['archiveSha256'] or digest(BACKUP/'manifest.json')!=report['manifestSha256']:raise RuntimeError('Archive ou manifeste altéré')
    if files(BACKUP/'restore')!={n:a['sha256'] for n,a in manifest['files'].items()}:raise RuntimeError('Restauration originale différente')
    return report,manifest

def build():
    report,manifest=check_backup();candidate=WORK/'candidate';payload=WORK/'payload'
    if candidate.exists() or payload.exists():raise RuntimeError('Candidat existant conservé')
    expected={n:a['sha256'] for n,a in manifest['files'].items()}
    prior=load(APPROVED/'transition-plan-private.json');approved_ref=load(APPROVED/'payload/maintenance/new-match-reference-v2.2.json')
    for item in prior['files']:
        if digest(APPROVED/'payload'/item['path'])!=item['newSha256']:raise RuntimeError('Proposition approuvée changée')
        if item['action']=='replace' and expected.get(item['path'])!=item['oldSha256']:raise RuntimeError('Cible actuelle différente du périmètre approuvé')
    shutil.copytree(BACKUP/'restore',candidate)
    if files(candidate)!=expected:raise RuntimeError('Copie actuelle incomplète')
    original_plan=load(BASE/'V22-VANILLA-20261123-01/restoration-plan-private.json')
    shaft=load(APPROVED/'analysis-private.json')['shaftCells']
    defaults=load(APPROVED/'payload/maintenance/block-defaults-26.3.json')
    current=Reader(candidate);grouped={}
    def group(at,text):
        x,y,z=at;region=f'world/dimensions/minecraft/overworld/region/r.{x//512}.{z//512}.mca'
        grouped.setdefault(region,{}).setdefault(x//16%32+z//16%32*32,{}).setdefault(y//16,{})[(y%16)*256+(z%16)*16+x%16]=text
    for block in original_plan['blocks']:
        if normalized(state(current,*block['at']),defaults)!=canonical(block['before'],defaults):raise RuntimeError('Conflit de restauration actuelle')
        group(block['at'],block['after'])
    proofs=[]
    for region,edits in grouped.items():
        raw=(candidate/region).read_bytes();patched,chunks=patch_region(raw,edits)
        proof=verify_region(raw,patched,edits);(candidate/region).write_bytes(patched);proofs.append({'path':region,**proof})
    # Appliquer séparément la correction approuvée pour reproduire exactement son édition NBT.
    x,bottom,z=shaft[0]['at'];region=f'world/dimensions/minecraft/overworld/region/r.{x//512}.{z//512}.mca';index=x//16%32+z//16%32*32
    fixed=Reader(candidate);edits={}
    for c in shaft:
        if normalized(state(fixed,*c['at']),defaults)['Name']!='minecraft:air':raise RuntimeError('Conflit au puits')
        a,y,b=c['at'];edits.setdefault(y//16,{})[(y%16)*256+(b%16)*16+a%16]=c['after']
    raw=(candidate/region).read_bytes();patched,chunks=patch_region(raw,{index:edits});verify_region(raw,patched,{index:edits});(candidate/region).write_bytes(patched)
    archive=server.ROOT/'dist/fallenkingdom-preproduction-26.3.zip'
    if digest(archive)!=SOURCE:raise RuntimeError('Source initiale changée')
    with zipfile.ZipFile(archive) as zz:
        initial=ArchiveReader(zz);fixed=Reader(candidate)
        for yy in range(-64,320):
            if normalized(state(fixed,x,yy,z),defaults)!=normalized(state(initial,x,yy,z),defaults):raise RuntimeError('Colonne différente avant correction heightmaps')
        patched,heightmaps=restore_heightmaps(patched,index,x%16+z%16*16,initial.chunk(x//16,z//16));(candidate/region).write_bytes(patched)
        geometry=compare_target_chunks(initial,Reader(candidate),[b['at'] for b in original_plan['blocks']]+[c['at'] for c in shaft],defaults)
    regions=set(grouped)
    for name in regions:
        approved=next(f['newSha256'] for f in prior['files'] if f['path']==name)
        if digest(candidate/name)!=approved:raise RuntimeError('Édition reconstruite différente du terrain approuvé')
    # Copier uniquement les autres cibles explicitement approuvées, depuis des octets contrôlés.
    for item in prior['files']:
        name=item['path']
        if name in regions:continue
        target=candidate/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(APPROVED/'payload'/name,target)
    approval={'operation':OP,'status':'owner_approved_human_inspection_waived','authorizationDocumentSha256':digest(ATTACHMENT),'humanInspectionPerformed':False}
    ref=copy.deepcopy(approved_ref);ref['localProposal']=approval
    for name in ('maintenance/new-match-reference.json','maintenance/new-match-reference-v2.2.json'):write(candidate/name,ref)
    meta=load(candidate/'map-underground-restoration.json');meta.update({'integrationSource':'verified_current_cold_backup','sourceBackupManifestSha256':report['manifestSha256'],'approval':approval});write(candidate/'map-underground-restoration.json',meta)
    history=WORK/'candidate-preserved-old-metadata';history.mkdir()
    for name in prior['quarantineActiveRecords']:(candidate/name).rename(history/name)
    owned=load(candidate/'DEPLOYMENT_MANIFEST.json')
    for name in owned['files']:owned['files'][name]=digest(candidate/name)
    owned.update({'integrationRevision':OP,'referenceStatus':approval['status'],'sourceBackupManifestSha256':report['manifestSha256'],'humanInspectionPerformed':False})
    write(candidate/'DEPLOYMENT_MANIFEST.json',owned)
    after=files(candidate);target_paths={f['path'] for f in prior['files']}
    changed={n for n in expected if n in after and expected[n]!=after[n]};added=set(after)-set(expected);removed=set(expected)-set(after)
    if changed|added!=target_paths or removed!=set(prior['quarantineActiveRecords']):raise RuntimeError('Périmètre substantiellement modifié')
    if len(target_paths)!=17 or len(owned['files'])!=157:raise RuntimeError('Périmètre 17/157 attendu')
    result=verify_terrain(candidate,ref,Reader(candidate))
    import subprocess
    for action in ('check','verify-baseline'):
        run=subprocess.run([sys.executable,'-X','utf8','-B',str(candidate/'maintenance/host_ops.py'),action],capture_output=True,text=True,encoding='utf-8')
        (WORK/f'candidate-{action}-private.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Validateur candidat refusé:'+action)
    code="import sys,json;from pathlib import Path;r=Path(sys.argv[1]);sys.path.insert(0,str(r/'maintenance'));import new_match;print(json.dumps(new_match.initial_checks(r,r/'maintenance/new-match-reference-v2.2.json')))"
    run=subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(candidate)],capture_output=True,text=True,encoding='utf-8');(WORK/'candidate-initial-checks-private.log').write_text(run.stdout+run.stderr,encoding='utf-8')
    if run.returncode:raise RuntimeError('Référence de partie initiale refusée')
    payload.mkdir();entries=[]
    anchor=manifest['files']['paper.jar']['pathStatBaseline']
    owners={(a['pathStatBaseline']['uid'],a['pathStatBaseline']['gid']) for a in manifest['files'].values()}
    if len(owners)!=1 or None in next(iter(owners)):raise RuntimeError('Propriétaires Linux non restaurables sans chown')
    for f in prior['files']:
        name=f['path'];p=payload/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(candidate/name,p)
        owner=manifest['files'].get(name,{}).get('pathStatBaseline',anchor)
        entries.append({**f,'newSha256':digest(p),'bytes':p.stat().st_size,'expectedUid':owner['uid'],'expectedGid':owner['gid']})
    plan={'operation':OP,'backupOperation':BACKUP.name,'backupArchiveSha256':report['archiveSha256'],'backupManifestSha256':report['manifestSha256'],
        'approval':approval,'files':entries,'quarantineActiveRecords':prior['quarantineActiveRecords'],
        'sourceFullHashes':expected,'sourceActiveHashes':{n:h for n,h in expected.items() if n.split('/')[0] not in ('.fk-stage','.fk-quarantine')},
        'candidateFullHashes':after,'candidateManifestSha256':digest(candidate/'DEPLOYMENT_MANIFEST.json'),'payloadFiles':17,'manifestEntries':157,
        'geometry':geometry,'terrainReference':result,'heightmapCorrections':heightmaps,'readyForInstall':False,
        'requiredAdditionalFreeBytes':sum(f['bytes'] for f in entries)+sum(a['size'] for a in manifest['files'].values())+max(f['bytes'] for f in entries)+2*1024**3}
    write(WORK/'plan-private.json',plan)
    update=WORK/'v22-final-current-transfer-private.zip'
    with zipfile.ZipFile(update,'x',zipfile.ZIP_DEFLATED,compresslevel=4) as zz:
        for f in entries:zz.write(payload/f['path'],f['path'])
        zz.writestr('UPDATE_MANIFEST.json',json.dumps({'files':{f['path']:f['newSha256'] for f in entries},'operation':OP},indent=2))
    with zipfile.ZipFile(update) as zz:
        if zz.testzip():raise RuntimeError('Archive finale CRC refusée')
        for f in entries:
            if hashlib.sha256(zz.read(f['path'])).hexdigest()!=f['newSha256']:raise RuntimeError('Archive finale SHA refusé')
    plan['transferArchiveSha256']=digest(update);write(WORK/'plan-private.json',plan)
    print(json.dumps({'candidatePrepared':True,'payloadFiles':17,'manifestEntries':157,'geometry':geometry,'transferArchiveSha256':plan['transferArchiveSha256']}));return plan

def simulate():
    check_backup();plan=load(WORK/'plan-private.json');root=WORK/'simulation';rollback=WORK/'simulation-restored'
    if root.exists() or rollback.exists():raise RuntimeError('Simulation existante conservée')
    shutil.copytree(BACKUP/'restore',root)
    before=files(root);payload={f['path']:f['newSha256'] for f in plan['files']}
    if before!=plan['sourceFullHashes']:raise RuntimeError('Simulation source incomplète')
    failures=[simulate_transfer(plan['sourceActiveHashes'],payload,plan['quarantineActiveRecords'],fail_after=i,backup_verified=True) for i in (0,1,4,8,16,17)]
    stage=root/'.fk-stage'/OP;quarantine=root/'.fk-quarantine'/OP/'files';stage.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(WORK/'payload',stage);quarantine.mkdir(parents=True)
    for name in plan['quarantineActiveRecords']+sorted(payload,key=lambda n:(n=='DEPLOYMENT_MANIFEST.json',n)):
        target=root/name
        if target.exists():q=quarantine/name;q.parent.mkdir(parents=True,exist_ok=True);target.rename(q)
        staged=stage/name
        if staged.is_file():target.parent.mkdir(parents=True,exist_ok=True);staged.rename(target)
    actual=files(root);expected=dict(plan['candidateFullHashes'])
    for name in set(payload)&before.keys()|set(plan['quarantineActiveRecords']):expected['.fk-quarantine/'+OP+'/files/'+name]=before[name]
    if actual!=expected:raise RuntimeError('Simulation installation complète différente')
    # Extraire à nouveau la sauvegarde complète, y compris historiques et session.lock.
    rollback.mkdir()
    with zipfile.ZipFile(BACKUP/'instance.zip') as zz:zz.extractall(rollback)
    if files(rollback)!=plan['sourceFullHashes']:raise RuntimeError('Simulation rollback complet différente')
    report={'passed':True,'completeSourceFiles':len(before),'completeInstalledFilesIncludingNewQuarantine':len(actual),
        'installedFiles':17,'quarantineFiles':13,'rollbackFilesVerified':len(files(rollback)),
        'failureInjectionCases':len(failures),'historicalQuarantinesPreserved':True,'realLocalFilesUsed':True,
        'linuxModesAndOwnersPlanned':True,'windowsPosixOwnershipApplied':False}
    write(WORK/'simulation-private.json',report);plan['simulationReportSha256']=digest(WORK/'simulation-private.json');write(WORK/'plan-private.json',plan)
    print(json.dumps(report));return report

if __name__=='__main__':
    try:
        result=simulate() if len(sys.argv)>1 and sys.argv[1]=='simulate' else build()
    except Exception as error:print(json.dumps({'passed':False,'failure':str(error)}));sys.exit(1)
