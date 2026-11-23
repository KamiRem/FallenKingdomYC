"""Préparer les seules restaurations naturelles sur des régions relues, sans réseau."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from anvil_patch import parse_state,patch_region
from map_reader import Reader
from natural_caverns_rework import verify_region,inventory,write
import server
sys.path.insert(0,str(server.ROOT/'deployment'))
from terrain_reference import normalized,state


def canonical(text,defaults):
    name,props=parse_state(text)
    return normalized({'Name':name,'Properties':dict(props)},defaults)


def classify(reader,blocks,defaults):
    edits=[];already=[];conflicts=[]
    for block in blocks:
        at=block['at'];actual=normalized(state(reader,*at),defaults)
        if actual==canonical(block['after'],defaults):already.append(at)
        elif actual==canonical(block['before'],defaults):edits.append(block)
        else:conflicts.append({'at':at,'expectedOld':block['before'],'desiredNatural':block['after'],'actual':actual})
    return edits,already,conflicts


def simulate(work):
    work=work.resolve();parent=(Path.home()/'FKBackups').resolve()
    if work==parent or not work.is_relative_to(parent):raise RuntimeError('Dossier privé hors dépôt requis')
    audit=json.loads((work/'fingerprint-private.json').read_text(encoding='utf-8'));regions=json.loads((work/'regions-private.json').read_text(encoding='utf-8'))
    if not audit['passed'] or not regions['passed']:raise RuntimeError('Lectures complètes et régions stables requises')
    source=work/'region-readback';target=work/'simulated-region-payload'
    if target.exists():raise RuntimeError('Simulation existante conservée')
    delivery=Path.home()/'FKBackups/V22-FINAL-20261123-02';terrain_source=Path.home()/'FKBackups/V22-VANILLA-20261123-01'
    plan_path=terrain_source/'restoration-plan-private.json';proof=json.loads((server.ROOT/'tests/results/vanilla-underground-20261123.json').read_text(encoding='utf-8'))
    if server.digest(plan_path)!=proof['privateEvidenceSha256']['restoration-plan-private.json']:raise RuntimeError('Plan approuvé modifié')
    plan=json.loads(plan_path.read_text(encoding='utf-8'));defaults=json.loads((delivery/'candidate/maintenance/block-defaults-26.3.json').read_text(encoding='utf-8'))
    before=inventory(source)
    for name,h in before.items():
        if h!=audit['doubleReadHashes'][name] or h!=regions['doubleReadHashes'][name]:raise RuntimeError('Région différente des lectures distantes')
    edits,already,conflicts=classify(Reader(source),plan['blocks'],defaults)
    report={'simulationOnly':True,'remoteWritesPerformed':False,'currentCompleteBackupAvailable':False,'fullCurrentInstanceRestored':False,
            'plannedRestorations':len(plan['blocks']),'editsRequired':len(edits),'alreadyNatural':len(already),'conflicts':len(conflicts),'passed':False}
    if conflicts:
        write(work/'voxel-conflicts-private.json',conflicts);write(work/'rebase-simulation-private.json',report);return report
    target.mkdir();grouped={}
    for block in edits:
        x,y,z=block['at'];name=f'world/dimensions/minecraft/overworld/region/r.{x//512}.{z//512}.mca'
        grouped.setdefault(name,{}).setdefault(x//16%32+z//16%32*32,{}).setdefault(y//16,{})[(y%16)*256+(z%16)*16+x%16]=block['after']
    proofs=[]
    for name,changes in grouped.items():
        raw=(source/name).read_bytes();patched,chunks=patch_region(raw,changes);verification=verify_region(raw,patched,changes)
        destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(patched)
        proofs.append({'path':name,'oldSha256':before[name],'newSha256':server.digest(destination),'oldBytes':len(raw),'newBytes':len(patched),'chunks':chunks,**verification})
    if inventory(source)!=before:raise RuntimeError('Les lectures originales ont changé')
    report.update({'passed':True,'regions':proofs,'sourceReadbacksUnchanged':True,'inventoryAndNonLightingChunkMetadataPreserved':True})
    write(work/'rebase-simulation-private.json',report);return report


def simulate_transfer(before,payload,removed,*,fail_after=None,backup_verified=False,observed=None,staged=None):
    """Modèle de chemins/SHA, pas un client SFTP ni une restauration de fichiers."""
    original=dict(before);active=dict(before if observed is None else observed);staging=dict(payload if staged is None else staged);quarantine={}
    if active!=original:raise RuntimeError('Précondition source modifiée')
    if staging!=payload:raise RuntimeError('SHA de staging incorrect avant quarantaine')
    if set(removed)&set(payload):raise RuntimeError('Chemin à retirer encore ciblé')
    allowed_regions={f'world/dimensions/minecraft/overworld/region/r.{x}.{z}.mca' for x in (-1,0) for z in (-1,0)}
    if any((n.startswith('world/') and n not in allowed_regions) or n.startswith(('world_nether/','world_the_end/')) for n in payload):raise RuntimeError('Données protégées ciblées')
    if any(n.startswith(('world/','world_nether/','world_the_end/')) for n in removed):raise RuntimeError('Données protégées ciblées')
    for name in removed:
        if name not in active:raise RuntimeError('Source de quarantaine absente')
    count=0
    for name in list(removed)+sorted(payload,key=lambda n:(n=='DEPLOYMENT_MANIFEST.json',n)):
        if name in active:quarantine[name]=active.pop(name)
        if name in staging:active[name]=staging.pop(name);count+=1
        if fail_after is not None and count>=fail_after:
            if not backup_verified:raise RuntimeError('Rollback interdit sans sauvegarde courante vérifiée')
            failed=dict(active);active=dict(original)
            if active!=original:raise RuntimeError('Rollback incomplet')
            return {'passed':True,'failureInjected':True,'rollbackHashModelMatchesCurrentSource':True,'failedAttemptPreservedFiles':len(failed),'quarantinePreservedFiles':len(quarantine),'realRestorePerformed':False}
    protected={n:h for n,h in original.items() if n not in payload and n not in removed}
    if any(active.get(n)!=h for n,h in protected.items()):raise RuntimeError('Fichier conservé modifié')
    return {'passed':True,'failureInjected':False,'activeFilesAfter':len(active),'payloadFiles':len(payload),'quarantinedFiles':len(quarantine),'preservedFiles':len(protected),'stagingEmpty':not staging,'realTransferPerformed':False}


def propose_reference(original,reader,baseline_reader,defaults,planned_positions):
    """Proposition explicite ; ne corrige jamais un échec sur une cellule à restaurer."""
    from terrain_reference import fingerprint
    result=copy.deepcopy(original);differences=[]
    for at in original['underground']['checkPoints']:
        expected=normalized(state(baseline_reader,*at),defaults);actual=normalized(state(reader,*at),defaults)
        if actual!=expected:
            if tuple(at) in planned_positions:raise RuntimeError('Échec de restauration masqué par une référence interdite')
            differences.append({'at':at,'approvedInitial':expected,'preservedCurrent':actual})
    result['underground']['approvedInitialBlockStatesSha256']=original['underground']['blockStatesSha256']
    result['underground']['blockStatesSha256']=fingerprint(reader,original['underground']['checkPoints'],defaults)
    result['underground']['proposedPreservedCurrentEdits']=differences
    result['underground']['approvalStatus']='proposed_only_not_approved'
    return result,differences


def prepare_payload(work,propose_preserved_edits=False,payload_revision=1):
    work=work.resolve();parent=(Path.home()/'FKBackups').resolve()
    if work==parent or not work.is_relative_to(parent):raise RuntimeError('Dossier privé hors dépôt requis')
    load=lambda p:json.loads(p.read_text(encoding='utf-8'))
    audit=load(work/'fingerprint-private.json');simulation=load(work/'rebase-simulation-private.json')
    if not audit['passed'] or not simulation['passed']:raise RuntimeError('Audit et restauration de blocs validés requis')
    before=audit['doubleReadHashes'];attrs=load(work/'fingerprint-inventory-private.json')['files'];candidate=Path.home()/'FKBackups/V22-FINAL-20261123-02/candidate'
    approved=load(server.ROOT/'tests/results/v22-final-validation-20261123.json')
    expected=approved['delivery']['artifacts'][1]['sha256']
    if server.digest(candidate/'plugins/FKAmis-1.0.0.jar')!=expected:raise RuntimeError('JAR retenu modifié')
    if payload_revision not in range(1,100):raise RuntimeError('Révision de payload 1..99 requise')
    name='proposed-payload-preserve-current' if propose_preserved_edits else 'proposed-payload'
    payload=work/(name+(f'-r{payload_revision}' if payload_revision>1 else ''))
    if payload.exists():raise RuntimeError('Payload existant conservé')
    payload.mkdir();readback=work/'readback'
    def put(name,data):
        target=payload/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(data)
    def put_json(name,data):put(name,(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
    for name in ('plugins/FKAmis-1.0.0.jar','maintenance/new_match.py','maintenance/terrain_reference.py','maintenance/block-defaults-26.3.json','maintenance/new-match-reference-v2.2.json'):
        put(name,(candidate/name).read_bytes())
    put('maintenance/new-match-reference.json',(candidate/'maintenance/new-match-reference-v2.2.json').read_bytes())
    put('FKAmis.sha256',(expected+'\n').encode('ascii'))
    registry=load(readback/'RUNTIME_LOCK.json');registry['sha256']['plugins/FKAmis-1.0.0.jar']=expected;registry['fkamisUpdate']=load(candidate/'RUNTIME_LOCK.json')['fkamisUpdate'];put_json('RUNTIME_LOCK.json',registry)
    # Modifier les quatre seules clés de présentation ; préserver toutes les autres traductions.
    import re
    language=(readback/'plugins/FallenKingdom/locales/messages_fr.properties').read_bytes()
    for line in (server.ROOT/'configs/fallenkingdom/territory-notifications-fr.properties').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        key,value=line.split('=',1);language,count=re.subn(b'(?m)^'+re.escape(key.encode())+b'=[^\r\n]*',(key+'='+value).encode(),language)
        if count!=1:raise RuntimeError('Clé de traduction inconnue ou dupliquée')
    put('plugins/FallenKingdom/locales/messages_fr.properties',language)
    built=load(readback/'map-v2-construction.json');built['mapVersion']='2.2';built['mapVariant']='V2.2-vanilla-underground';put_json('map-v2-construction.json',built)
    restoration=load(candidate/'map-underground-restoration.json');restoration['integrationSource']='read_only_audit_before_fresh_backup';restoration['restoredBlockStates']=simulation['editsRequired'];put_json('map-underground-restoration.json',restoration)
    historic=sorted(n for n in before if n.startswith('map-v21-') and n.endswith('.json'))
    for name in historic:
        data=(candidate/'reference/history-v21'/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=before[name]:raise RuntimeError('Métadonnée historique locale différente du serveur')
        put('reference/history-v21/'+name,data)
    for region in simulation['regions']:
        name=region['path'];data=(work/'simulated-region-payload'/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=region['newSha256']:raise RuntimeError('Région simulée modifiée')
        put(name,data)
    # Contrôle de la référence naturelle complète dans ces quatre régions, sans présumer le reste du monde.
    from terrain_reference import fingerprint
    reference=load(payload/'maintenance/new-match-reference-v2.2.json');defaults=load(payload/'maintenance/block-defaults-26.3.json')
    matches_initial=fingerprint(Reader(payload),reference['underground']['checkPoints'],defaults)==reference['underground']['blockStatesSha256'];differences=[]
    if not matches_initial:
        if not propose_preserved_edits:raise RuntimeError('Terrain naturel différent de la référence sur les cellules contrôlées')
        plan=load(Path.home()/'FKBackups/V22-VANILLA-20261123-01/restoration-plan-private.json')
        reference,differences=propose_reference(reference,Reader(payload),Reader(candidate),defaults,{tuple(b['at']) for b in plan['blocks']})
        for name in ('maintenance/new-match-reference.json','maintenance/new-match-reference-v2.2.json'):
            (payload/name).write_text(json.dumps(reference,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        restoration['verifiedOriginalCells']=len(reference['underground']['checkPoints'])-len(differences)
        restoration['controlledCells']=len(reference['underground']['checkPoints']);restoration['preservedCurrentTerrainEdits']=len(differences);restoration['approvalStatus']='proposed_only_not_approved'
        (payload/'map-underground-restoration.json').write_text(json.dumps(restoration,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if fingerprint(Reader(payload),reference['underground']['checkPoints'],defaults)!=reference['underground']['blockStatesSha256']:raise RuntimeError('Proposition de référence incohérente')
    current_manifest=load(readback/'DEPLOYMENT_MANIFEST.json');manifest=copy.deepcopy(current_manifest)
    manifest['files']={n:before[n] for n in current_manifest['files'] if n not in historic}
    hashes=inventory(payload);manifest['files'].update(hashes);manifest['files']['spigot.yml']=before['spigot.yml']
    manifest['localMapVariant']='V2.2-vanilla-underground';manifest['integrationRevision']=work.name;manifest['sourceAuditManifestSha256']=server.digest(work/'fingerprint-private.json')
    manifest['preservedCurrentTerrainEditsRequireApproval']=bool(differences)
    put_json('DEPLOYMENT_MANIFEST.json',manifest);hashes=inventory(payload)
    result={'simulationOnly':True,'remoteWritesPerformed':False,'backupCreated':False,'currentColdBackupVerified':False,'fullCurrentInstanceRestored':False,'payloadFiles':len(hashes),'manifestEntries':len(manifest['files']),
            'sourceFiles':len(before),'sourceBytes':audit['activeBytes'],'quarantineActiveRecords':historic,'files':[],
            'preservedPolicyAndStateFiles':['plugins/FKAmis/state.yml','plugins/FKAmis/config.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','server.properties','whitelist.json','ops.json','spigot.yml'],
            'sourcePreconditionSha256':before,'naturalCellsVerified':len(reference['underground']['checkPoints']),
            'approvedInitialReferenceMatches':matches_initial,'preservedCurrentTerrainEdits':differences,'requiresExplicitReferenceApproval':bool(differences),'payloadDirectory':payload.name,'readyForDeployment':False}
    for name,h in sorted(hashes.items()):
        if name in before and before[name]==h:raise RuntimeError('Fichier inchangé inutilement transféré')
        mode_source=name if name in attrs else 'maintenance/new-match-reference.json' if name.startswith('maintenance/') else 'map-v2-construction.json'
        if name.startswith('reference/history-v21/'):mode_source=name.removeprefix('reference/history-v21/')
        result['files'].append({'path':name,'action':'replace' if name in before else 'create','oldSha256':before.get(name),'newSha256':h,'bytes':(payload/name).stat().st_size,'expectedMode':attrs[mode_source]['mode']})
    result['transferSimulation']=simulate_transfer(before,hashes,historic)
    result['rollbackSimulation']=simulate_transfer(before,hashes,historic,fail_after=4,backup_verified=True)
    largest=max(x['bytes'] for x in result['files']);total=sum(x['bytes'] for x in result['files'])
    technical=load(work/'regions-private.json').get('technicalNamespaceMetadata',[])
    technical_bytes=sum(op['bytes'] for ns in technical for op in ns['operations']);technical_files=sum(op['files'] for ns in technical for op in ns['operations'])
    complete_bytes=audit['activeBytes']+technical_bytes
    result['spacePlan']={'stagingBytes':total,'quarantineRenameAdditionalDataBytes':0,'rollbackParallelReserveBytes':complete_bytes,'completeInstanceBytesObservedByMetadata':complete_bytes,'completeInstanceFilesObservedByMetadata':len(before)+technical_files,'historicalQuarantineContentHashed':False,'temporaryLargestFileBytes':largest,'marginBytes':2*1024**3,'requiredAdditionalFreeBytes':total+complete_bytes+largest+2*1024**3,'remoteArchiveBytes':0}
    write(work/'transition-plan-private.json',result)
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--payload',action='store_true');p.add_argument('--propose-preserved-edits-reference',action='store_true');p.add_argument('--payload-revision',type=int,default=1);a=p.parse_args()
    result=prepare_payload(a.work,a.propose_preserved_edits_reference,a.payload_revision) if a.payload else simulate(a.work)
    print(json.dumps({k:v for k,v in result.items() if k in ('simulationOnly','remoteWritesPerformed','currentColdBackupVerified','plannedRestorations','editsRequired','alreadyNatural','conflicts','passed','payloadFiles','manifestEntries','sourceFiles','transferSimulation','rollbackSimulation','spacePlan')},ensure_ascii=False))
    if not result.get('passed',result.get('transferSimulation',{}).get('passed')):sys.exit(1)
