"""Correction locale du puits depuis l'archive approuvée ; aucun appel réseau."""
import argparse
import copy
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import zlib
import zipfile

import server
from anvil_patch import Tag, dump, load, patch_region, region_entries
from map_reader import Reader
from natural_caverns_rework import inventory, unpack, verify_region, write
from minestrator_cold_backup import protect_directory, now
from vanilla_underground import ArchiveReader, SOURCE
from terrain_reference import fingerprint, normalized, state, verify as verify_terrain
from v22_rebase_plan import simulate_transfer
from v22_cell_review import sha
from world_integrity import states_equal

PRIVATE = Path.home() / 'FKBackups'
AUDIT = PRIVATE / 'MS-V22-PREFLIGHT-20261123-01'
OLD = PRIVATE / 'V21-QUERY-20261120-01/preproduction-candidate'
FINAL = PRIVATE / 'V22-FINAL-20261123-02/candidate'
ARCHIVE = server.ROOT / 'dist/fallenkingdom-preproduction-26.3.zip'
load_json = lambda p: json.loads(p.read_text(encoding='utf-8'))


def full_text(value):
    props=value.get('Properties',{})
    return value['Name']+('['+','.join(k+'='+v for k,v in sorted(props.items()))+']' if props else '')


def packed_height(values,index):
    if len(values)!=37 or not 0<=index<256:raise ValueError('InvalidHeightmap')
    return (values[index//7]>>((index%7)*9))&511


def replace_height(values,index,value):
    packed_height(values,index)
    if not 0<=value<=384:raise ValueError('InvalidHeightValue')
    result=list(values);shift=(index%7)*9
    raw=(result[index//7]&((1<<64)-1))&~(511<<shift);raw|=value<<shift
    result[index//7]=raw if raw<(1<<63) else raw-(1<<64)
    return result


def restore_heightmaps(data,index,column,original_chunk):
    """Copier quatre valeurs d'une colonne historiquement identique, pas le chunk."""
    entries=region_entries(data);name,root=load(unpack(entries[index]))
    before=dump(name,root);maps=root.value['Heightmaps'].value;original=original_chunk['Heightmaps']
    if set(maps)!=set(original) or set(maps)!={'MOTION_BLOCKING','MOTION_BLOCKING_NO_LEAVES','WORLD_SURFACE','OCEAN_FLOOR'}:
        raise ValueError('UnknownHeightmapSchema')
    details=[]
    for key,tag in maps.items():
        if tag.kind!=12:raise ValueError('UnknownHeightmapType')
        wanted=packed_height(original[key],column);prior=list(tag.value)
        tag.value=replace_height(prior,column,wanted);tag.raw=None
        for i in range(256):
            if packed_height(tag.value,i)!=(wanted if i==column else packed_height(prior,i)):
                raise ValueError('OtherHeightmapColumnChanged')
        details.append({'kind':key,'oldEncodedHeight':packed_height(prior,column),'newEncodedHeight':wanted})
    modified=dump(name,root)
    _,a=load(before);_,b=load(modified)
    a.value.pop('Heightmaps');b.value.pop('Heightmaps')
    if dump(b'',a)!=dump(b'',b):raise ValueError('NonHeightmapNbtChanged')
    payload=zlib.compress(modified,6);record=(len(payload)+1).to_bytes(4,'big')+b'\x02'+payload
    out=bytearray(data);sectors=math.ceil(len(record)/4096);offset=len(out)//4096
    if sectors>255 or offset>=1<<24:raise ValueError('RegionOverflow')
    out[index*4:index*4+4]=offset.to_bytes(3,'big')+bytes([sectors])
    out.extend(record+b'\0'*(sectors*4096-len(record)));result=bytes(out)
    final=region_entries(result)
    if entries.keys()!=final.keys() or any(entries[i]!=final[i] for i in entries if i!=index) or data[4096:8192]!=result[4096:8192]:
        raise ValueError('OtherChunkOrTimestampChanged')
    return result,details


def sealed_inputs():
    receipt=load_json(server.ROOT/'tests/results/minestrator-v22-preflight-20261123.json')
    for name,h in receipt['privateEvidenceSha256'].items():
        if sha(AUDIT/name)!=h:raise ValueError('PreflightEvidenceChanged')
    plan=load_json(AUDIT/'transition-plan-private.json');payload=AUDIT/plan['payloadDirectory']
    files={payload/f['path']:f['newSha256'] for f in plan['files']}
    files[ARCHIVE]=SOURCE
    cells=PRIVATE/'MS-V22-CELL-REVIEW-20261123-02/cell-safety-review-private.json'
    files[cells]=load_json(server.ROOT/'tests/results/minestrator-v22-cell-review-20261123.json')['privateEvidenceSha256'][cells.name]
    restoration=PRIVATE/'V22-VANILLA-20261123-01/restoration-plan-private.json'
    files[restoration]=load_json(server.ROOT/'tests/results/vanilla-underground-20261123.json')['privateEvidenceSha256'][restoration.name]
    for name,h in load_json(AUDIT/'regions-private.json')['doubleReadHashes'].items():files[AUDIT/'region-readback'/name]=h
    for path,h in files.items():
        if sha(path)!=h:raise ValueError('SealedInputChanged')
    return files

def compare_target_chunks(original,fixed,positions,defaults):
    registry={name:normalized({'Name':name},defaults)['Properties'] for name in defaults}
    locations={tuple((p[0]//16,p[2]//16)) for p in positions};sections=0
    for cx,cz in locations:
        a={s['Y']:s for s in original.chunk(cx,cz).get('sections',[])}
        b={s['Y']:s for s in fixed.chunk(cx,cz).get('sections',[])}
        for sy in a.keys()|b.keys():
            left=a.get(sy,{}).get('block_states') or {'palette':['minecraft:air']}
            right=b.get(sy,{}).get('block_states') or {'palette':['minecraft:air']}
            if not states_equal(left,right,defaults=registry):raise ValueError('OtherTargetChunkTerrainDifference')
            sections+=1
    return {'chunksCompared':len(locations),'sectionsCompared':sections,'blockCellsCompared':sections*4096,'allTargetChunkBlockStatesMatchInitialArchive':True}


def prepare(work):
    work=work.resolve()
    if work==PRIVATE.resolve() or not work.is_relative_to(PRIVATE.resolve()) or work.exists():raise ValueError('NewPrivateDestinationRequired')
    inputs=sealed_inputs();plan=load_json(AUDIT/'transition-plan-private.json');prior=AUDIT/plan['payloadDirectory']
    review=load_json(PRIVATE/'MS-V22-CELL-REVIEW-20261123-02/cell-safety-review-private.json')
    original_ref=load_json(FINAL/'maintenance/new-match-reference-v2.2.json')
    defaults=load_json(prior/'maintenance/block-defaults-26.3.json')
    x,bottom,z=review['cells'][0]['bottomAir'];top=min(r['at'][1] for r in review['cells'][0]['rims'])
    positions=[(x,y,z) for y in range(bottom,top+1)]
    if len(positions)!=33:raise ValueError('UnexpectedShaftExtent')
    existing=load_json(PRIVATE/'V22-VANILLA-20261123-01/restoration-plan-private.json')
    targets={tuple(b['at']) for b in existing['blocks']};old_points={tuple(p) for p in original_ref['underground']['checkPoints']}
    if targets&set(positions) or sum(p not in old_points for p in positions)!=31:raise ValueError('UnexpectedTargetOverlap')
    current,old,r2=Reader(AUDIT/'region-readback'),Reader(OLD),Reader(prior)
    installed=load_json(PRIVATE/'MS-DEPLOY-V21-20261120-01/installed-manifest.json')
    region=f'world/dimensions/minecraft/overworld/region/r.{x//512}.{z//512}.mca'
    if sha(OLD/region)!=installed['files'][region]:raise ValueError('V21InstalledReferenceMismatch')
    cells=[];nearby=[];distances={}
    with zipfile.ZipFile(ARCHIVE) as archive:
        initial=ArchiveReader(archive)
        if fingerprint(initial,original_ref['underground']['checkPoints'],defaults)!=original_ref['underground']['blockStatesSha256']:
            raise ValueError('InitialReferenceMismatch')
        for at in positions:
            expected=normalized(state(initial,*at),defaults);v21=normalized(state(old,*at),defaults)
            if v21!=expected or normalized(state(current,*at),defaults)['Name']!='minecraft:air' or normalized(state(r2,*at),defaults)['Name']!='minecraft:air':
                raise ValueError('AmbiguousShaftCell')
            if expected['Name'] not in {'minecraft:stone','minecraft:diorite','minecraft:dirt','minecraft:grass_block'}:
                raise ValueError('UnapprovedReplacementMaterial')
            if any(tuple(t.get(k) for k in ('x','y','z'))==at for t in r2.chunk(x//16,z//16).get('block_entities',[])):
                raise ValueError('BlockEntityCollision')
            cells.append({'at':list(at),'before':full_text(normalized(state(r2,*at),defaults)),'after':full_text(expected),
                          'state':expected,'archiveState':expected,'installedV21State':v21,'insideHistoricalFootprint':at in old_points})
        # Environnement : états complets, ouvertures et distances conservés en privé.
        for yy in range(bottom-2,top+4):
            for dx in range(-2,3):
                for dz in range(-2,3):
                    at=(x+dx,yy,z+dz)
                    nearby.append({'at':list(at),'before':normalized(state(r2,*at),defaults),
                                   'initial':normalized(state(initial,*at),defaults)})
        protect_directory(work);payload=work/'payload';shutil.copytree(prior,payload)
        changes={}
        for c in cells:
            a,y,b=c['at'];changes.setdefault(y//16,{})[(y%16)*256+(b%16)*16+a%16]=c['after']
        index=x//16%32+z//16%32*32;raw=(prior/region).read_bytes();block_only,chunk_proof=patch_region(raw,{index:changes})
        proof=verify_region(raw,block_only,{index:changes})
        (payload/region).write_bytes(block_only);patched_reader=Reader(payload)
        # Une colonne identique à l'archive autorise la copie des seules hauteurs de cette colonne.
        for yy in range(-64,320):
            if normalized(state(patched_reader,x,yy,z),defaults)!=normalized(state(initial,x,yy,z),defaults):raise ValueError('FullColumnNotHistoricallyIdentical')
        final,heightmaps=restore_heightmaps(block_only,index,x%16+(z%16)*16,initial.chunk(x//16,z//16))
        (payload/region).write_bytes(final)
        fixed=Reader(payload)
        for n in nearby:
            actual=normalized(state(fixed,*n['at']),defaults)
            expected=normalized(state(initial,*n['at']),defaults) if tuple(n['at']) in positions else n['before']
            if actual!=expected:raise ValueError('UnexpectedNeighborhoodChange')
        for block in existing['blocks']:
            if full_text(normalized(state(fixed,*block['at']),defaults))!=full_text(normalized(state(initial,*block['at']),defaults)):
                raise ValueError('PreviousRestorationLost')
        complete_comparison=compare_target_chunks(initial,fixed,[b['at'] for b in existing['blocks']]+positions,defaults)
        if fingerprint(fixed,original_ref['underground']['checkPoints'],defaults)!=original_ref['underground']['blockStatesSha256']:
            raise ValueError('HistoricalFootprintNotFullyRestored')
        ref=copy.deepcopy(original_ref)
        ref['underground']['archiveRestorations']={'schema':1,'kind':'shaft-column-33','sourceArchiveSha256':SOURCE,
            'cells':[{'at':c['at'],'state':c['state']} for c in cells],
            'blockStatesSha256':fingerprint(initial,[c['at'] for c in cells],defaults)}
        ref['localProposal']={'revision':work.name,'status':'proposed_pending_human_inspection','preservedTerrainExceptions':0}
        for name in ('maintenance/new-match-reference.json','maintenance/new-match-reference-v2.2.json'):write(payload/name,ref)
        shutil.copy2(server.ROOT/'deployment/terrain_reference.py',payload/'maintenance/terrain_reference.py')
        meta=load_json(payload/'map-underground-restoration.json')
        for k in ('preservedCurrentTerrainEdits','approvalStatus','controlledCells'):meta.pop(k,None)
        meta.update({'localCorrectionRevision':work.name,'additionalArchiveRestorationsRequired':True,
            'additionalArchiveRestoredCells':33,'restoredBlockStates':22219,'totalArchiveRestoredCells':22252,
            'verifiedOriginalCells':37128,'uniqueControlledNaturalCells':37159,'preservedTerrainExceptions':0,'visualValidation':False})
        write(payload/'map-underground-restoration.json',meta)
        verification=verify_terrain(payload,ref,fixed)
        for base in original_ref['bases']:
            distances.setdefault('bases',[]).append({'team':base['team'],'center':base['center'],'spawn':base['spawn'],
                'horizontalDistanceToCenter':math.hypot(x-float(base['center']['X']),z-float(base['center']['Z'])),
                'horizontalDistanceToSpawn':math.hypot(x+.5-float(base['spawn']['x']),z+.5-float(base['spawn']['z']))})
        distances['monuments']=[{'id':m['id'],'horizontalDistance':math.hypot(x-m['x'],z-m['z'])} for m in original_ref['monuments']]
        distances['supplies']=[{'id':s['id'],'horizontalDistance':math.hypot(x-s['at'][0],z-s['at'][2])} for s in original_ref['supplies']]
        rim_checks=[]
        for dx,dz in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
            highest=next(yy for yy in range(319,-65,-1) if fixed.block(x+dx,yy,z+dz) not in {'minecraft:air','minecraft:cave_air','minecraft:void_air'})
            if highest!=top or any(fixed.block(x+dx,highest+n,z+dz)!='minecraft:air' for n in (1,2)):
                raise ValueError('UnexpectedSurfaceGeometry')
            rim_checks.append({'at':[x+dx,highest,z+dz],'state':full_text(normalized(state(fixed,x+dx,highest,z+dz),defaults))})
    manifest=load_json(payload/'DEPLOYMENT_MANIFEST.json')
    manifest.update({'integrationRevision':work.name,'preservedCurrentTerrainEditsRequireApproval':False,
        'archiveRestorationsRequired':True,'referenceStatus':'proposed_pending_human_inspection'})
    for name in manifest['files']:
        if (payload/name).is_file():manifest['files'][name]=sha(payload/name)
    write(payload/'DEPLOYMENT_MANIFEST.json',manifest)
    hashes=inventory(payload)
    if set(hashes)!={f['path'] for f in plan['files']} or len(manifest['files'])!=157:raise ValueError('TransitionScopeChanged')
    transition=copy.deepcopy(plan)
    transition.update({'payloadDirectory':'payload','referenceProposalRevision':work.name,'requiresExplicitReferenceApproval':True,
        'preservedCurrentTerrainEdits':[],'approvedInitialReferenceMatches':True,'readyForDeployment':False,
        'additionalArchiveRestoredCells':33,'uniqueControlledNaturalCells':37159,'visualInspectionPassed':False})
    for f in transition['files']:f['newSha256']=hashes[f['path']];f['bytes']=(payload/f['path']).stat().st_size
    space=transition['spacePlan'];space['stagingBytes']=sum(f['bytes'] for f in transition['files'])
    space['temporaryLargestFileBytes']=max(f['bytes'] for f in transition['files'])
    space['requiredAdditionalFreeBytes']=space['stagingBytes']+space['rollbackParallelReserveBytes']+space['temporaryLargestFileBytes']+space['marginBytes']
    transition['transferSimulation']=simulate_transfer(plan['sourcePreconditionSha256'],hashes,plan['quarantineActiveRecords'])
    transition['rollbackSimulation']=simulate_transfer(plan['sourcePreconditionSha256'],hashes,plan['quarantineActiveRecords'],fail_after=4,backup_verified=True)
    write(work/'transition-plan-private.json',transition)
    combined=copy.deepcopy(existing);combined['blocks']+=cells
    combined['checkPoints']=sorted({tuple(p) for p in combined['checkPoints']}|set(positions))
    combined['surfaceChecks']=rim_checks
    write(work/'restoration-plan-private.json',combined)
    report={'revision':work.name,'createdAtUtc':now(),'prepared':True,'remoteAccessPerformed':False,'deployed':False,
        'sourceObservationFinishedAtUtc':review['sourceObservationFinishedAtUtc'],
        'sourceArchiveSha256':SOURCE,'shaftCells':cells,'environment':nearby,'proximity':distances,
        'probableOrigin':'post_installation_change_consistent_with_recipe_unknown_actor',
        'installedV21RegionMatchesDeliveryEvidence':True,'originalShaftMaterials':dict(Counter(c['state']['Name'] for c in cells)),
        'blockVerification':proof,'heightmapCorrections':heightmaps,'fullColumnMatchesInitial':True,
        'fullTargetChunkComparison':complete_comparison,
        'previousRestorationsPreserved':22219,'naturalReferenceVerification':verification,
        'surfaceChecks':rim_checks,'currentEntityPositionsUnavailable':True,
        'humanInspectionPassed':False,'sourceInputsUnchanged':all(sha(p)==h for p,h in inputs.items()),
        'payloadChangedFromR2':sorted(n for n in hashes if hashes[n]!=sha(prior/n)),
        'payloadFiles':len(hashes),'manifestEntries':len(manifest['files'])}
    if not report['sourceInputsUnchanged']:raise ValueError('SourceChanged')
    write(work/'analysis-private.json',report)
    archive_path=work/'v22-shaft-transition-PROPOSED-private.zip'
    with zipfile.ZipFile(archive_path,'x',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for name in sorted(hashes):z.write(payload/name,name)
        z.writestr('UPDATE_MANIFEST.json',json.dumps({'revision':work.name,'files':hashes,'approved':False},indent=2))
    with zipfile.ZipFile(archive_path) as z:
        if z.testzip() or set(z.namelist())!=set(hashes)|{'UPDATE_MANIFEST.json'}:raise ValueError('ArchiveInvalid')
        for name,h in hashes.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=h:raise ValueError('ArchivePayloadMismatch')
    archive_path.with_suffix('.zip.sha256').write_text(sha(archive_path)+'\n',encoding='ascii')
    report['archive']={'file':archive_path.name,'sha256':sha(archive_path),'bytes':archive_path.stat().st_size}
    write(work/'analysis-private.json',report)
    return report


def rehearsal(work):
    """Répétition réelle sur les seuls octets courants disponibles, pas une sauvegarde."""
    plan=load_json(work/'transition-plan-private.json');source=work/'available-current-fixture'
    if source.exists():raise ValueError('RehearsalAlreadyExists')
    source.mkdir();unavailable=[]
    for name,h in plan['sourcePreconditionSha256'].items():
        found=next((p for p in (AUDIT/'readback'/name,AUDIT/'region-readback'/name,OLD/name) if p.is_file() and sha(p)==h),None)
        if found:
            target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(found,target)
        else:unavailable.append(name)
    before=inventory(source);payload=work/'payload'
    technical_before={p.relative_to(source).as_posix():sha(p) for p in source.rglob('session.lock') if p.is_file()}
    for f in plan['files']:
        if f['action']=='replace' and before.get(f['path'])!=f['oldSha256']:raise ValueError('RehearsalTargetUnavailable')
    if any(n not in before for n in plan['quarantineActiveRecords']):raise ValueError('RehearsalQuarantineUnavailable')
    quarantine=work/'rehearsal-quarantine';quarantine.mkdir();staging=work/'rehearsal-stage';shutil.copytree(payload,staging)
    payload_hashes={f['path']:f['newSha256'] for f in plan['files']}
    if inventory(staging)!=payload_hashes:raise ValueError('StagingCorrupt')
    with server.maintenance(source):
        for name in plan['quarantineActiveRecords']+sorted(inventory(staging),key=lambda n:(n=='DEPLOYMENT_MANIFEST.json',n)):
            target=source/name
            if target.exists():
                q=quarantine/name;q.parent.mkdir(parents=True,exist_ok=True);target.rename(q)
            staged=staging/name
            if staged.is_file():target.parent.mkdir(parents=True,exist_ok=True);staged.rename(target)
        after=inventory(source)
        protected={n:h for n,h in before.items() if n not in payload_hashes and n not in plan['quarantineActiveRecords']}
        if any(after.get(n)!=h for n,h in protected.items()):raise ValueError('RehearsalPreservedFileChanged')
        for f in plan['files']:
            if after[f['path']]!=f['newSha256']:raise ValueError('InstalledRehearsalHashWrong')
    # Conserver l'installation de test, reconstruire toute la fixture dans un dossier neuf.
    restored=work/'rehearsal-rollback-restored';restored.mkdir()
    for name,h in (before|technical_before).items():
        at=quarantine/name if (quarantine/name).is_file() else source/name
        target=restored/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(at,target)
        if sha(target)!=h:raise ValueError('PhysicalRollbackMismatch')
    if inventory(restored)!=before:raise ValueError('PhysicalRollbackTreeMismatch')
    all_restored={p.relative_to(restored).as_posix():sha(p) for p in restored.rglob('*') if p.is_file()}
    if all_restored!=before|technical_before:raise ValueError('PhysicalRollbackTechnicalLockMismatch')
    report={'passed':True,'realLocalFileOperations':True,'remoteOperations':False,
        'sourceAvailableFiles':len(before),'remoteSourceFiles':len(plan['sourcePreconditionSha256']),
        'unavailableCurrentFiles':unavailable,'fixtureIsNotCompleteCurrentInstance':True,
        'installedFiles':len(plan['files']),'quarantinedFiles':len(inventory(quarantine)),
        'preservedFiles':len(protected),'rollbackFilesVerified':len(before),
        'availableTechnicalLockFiles':len(technical_before),'sourceAvailableFilesIncludingTechnicalLocks':len(before)+len(technical_before),
        'allAvailableFilesRestoredIncludingLocks':len(all_restored),
        'fullCurrentBackupOrRestorePerformed':False,'installationAndQuarantinePreserved':True}
    write(work/'rehearsal-private.json',report);return report


def paper(work,attempt=1):
    if not 1<=attempt<=99:raise ValueError('InvalidPaperAttempt')
    area=work/('engine-validation' if attempt==1 else f'engine-validation-{attempt:02d}')
    if area.exists():raise ValueError('PaperValidationAlreadyExists')
    area.mkdir();candidate=area/'candidate';before=inventory(FINAL);shutil.copytree(FINAL,candidate)
    for name in inventory(work/'payload'):
        target=candidate/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(work/'payload'/name,target)
    # Cette fixture complète est issue de la livraison locale, pas de la partie courante.
    # Sceller un manifeste propre à cette fixture ; le manifeste de transfert reste intact.
    meta=load_json(candidate/'DEPLOYMENT_MANIFEST.json')
    for name in meta['files']:meta['files'][name]=sha(candidate/name)
    meta['localEngineFixtureOnly']=True;write(candidate/'DEPLOYMENT_MANIFEST.json',meta)
    shutil.copy2(work/'restoration-plan-private.json',area/'restoration-plan-private.json')
    for action in ('check','verify-baseline'):
        import subprocess
        result=subprocess.run([sys.executable,'-X','utf8','-B',str(candidate/'maintenance/host_ops.py'),action],capture_output=True,text=True,encoding='utf-8')
        (area/f'maintenance-{action}-private.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise ValueError('EngineFixtureMaintenanceFailed:'+action)
    code="import sys,json;from pathlib import Path;r=Path(sys.argv[1]);sys.path.insert(0,str(r/'maintenance'));import new_match;print(json.dumps(new_match.initial_checks(r,r/'maintenance/new-match-reference-v2.2.json')))"
    result=subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(candidate)],capture_output=True,text=True,encoding='utf-8')
    (area/'initial-checks-private.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise ValueError('EngineFixtureInitialChecksFailed')
    from vanilla_paper_probe import run
    result=run(area)
    result['engineFixtureDirectory']=area.name
    result['fixtureIsNotCurrentBackupRestore']=True;result['approvedCandidateUnchanged']=inventory(FINAL)==before
    if not result['approvedCandidateUnchanged'] or result.get('naturalBlocksChecked')!=22252 or result.get('surfaceChecksVerified')!=5:raise ValueError('PaperValidationIncomplete')
    write(work/'paper-validation-private.json',result);return result

def prepare_inspection(work):
    validated=load_json(work/'paper-validation-private.json')
    area=(work/validated['engineFixtureDirectory']).resolve()
    if not area.is_relative_to(work.resolve()):raise ValueError('UnsafeEngineFixture')
    source=area/'candidate';target=work/'inspection-candidate'
    if target.exists() or not validated['passed']:raise ValueError('InspectionDestinationOrValidationInvalid')
    before=inventory(source);shutil.copytree(source,target)
    if inventory(target)!=before:raise ValueError('InspectionCopyMismatch')
    if {p.name for p in (target/'plugins').glob('*.jar')}!={'FallenKingdom-2.24.9.jar','FKAmis-1.0.0.jar'}:raise ValueError('TestPluginInInspectionCopy')
    launcher="""# Serveur local d'inspection uniquement ; aucune commande MineStrator.
from pathlib import Path
import sys,socket,subprocess,os
sys.path.insert(0,REPO_SCRIPTS)
import server
root=Path(__file__).resolve().parent/'inspection-candidate'
server.validate(root)
with socket.socket() as tcp,socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:
    tcp.bind(('127.0.0.1',22880));udp.bind(('127.0.0.1',22880))
env=os.environ.copy()
for key in list(env):
    if any(s in key.upper() for s in ('MINESTRATOR','SFTP','PTERODACTYL')) or key in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS'):env.pop(key)
with server.maintenance(root,check_worlds=False):
    raise SystemExit(subprocess.call([str(server.java_path()),'-Xms1G','-Xmx4G','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','22880'],cwd=root,env=env))
""".replace('REPO_SCRIPTS',repr(str(server.ROOT/'scripts')))
    (work/'launch-inspection-local.py').write_text(launcher,encoding='utf-8')
    executable="'"+str(server.ROOT/'.tools/ms-audit/Scripts/python.exe').replace("'","''")+"'"
    ps="$ErrorActionPreference='Stop'\n& "+executable+" -X utf8 -B (Join-Path $PSScriptRoot 'launch-inspection-local.py')\nexit $LASTEXITCODE\n"
    (work/'start-inspection-local.ps1').write_text(ps,encoding='utf-8')
    review=load_json(work/'analysis-private.json');at=review['surfaceChecks'][0]['at'];x,y,z=at
    lines=['# Inspection humaine privée du puits restauré','',
        'Copie indépendante locale, jamais une restauration de la partie courante. Ne pas publier ces coordonnées.',
        'Le lanceur start-inspection-local.ps1 reste manuel. Accès client Java : 127.0.0.1:22880 uniquement.',
        'Whitelist et rôles existants inchangés : utiliser seulement un compte déjà vérifié et autorisé.',
        'Aucun fka start, reset, ajout de whitelist, commande de recette destructive ou commande distante.',
        'Dans la console locale : fka status ; fka config validate ; fka info teams.',
        'Téléporter le compte arbitre existant, après connexion autorisée :',
        f'minecraft:tp <arbitre_verifie_connecte> {x+.5} {y+1} {z+.5}',
        '', 'Contrôler visuellement le sol restauré, quatre approches, la base voisine et ses fondations,',
        'le spawn, l’absence de trou, de chute ou de passage artificiel ; inspecter les sous-sols en Spectator',
        'avec le compte arbitre, sans casser de blocs. Refaire les spawns et frontières des quatre équipes.',
        'Capturer des preuves privées avant/après ; noter heure, observé et décision. Ne pas déclarer la visite faite avant réalisation.',
        'Arrêt propre : stop dans cette console locale. Aucune sauvegarde automatique ou partie lancée.',
        '', '| Cellule | Coordonnées | État archivé complet |', '|---|---|---|']
    for i,c in enumerate(review['shaftCells'],1):lines.append(f"| {i} | {c['at']} | {c['after']} |")
    (work/'INSPECTION_CLIENT_PRIVATE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report={'prepared':True,'started':False,'filesVerified':len(before),'plugins':2,'testPluginPresent':False,'whitelistModified':False,'loopbackHost':'127.0.0.1','port':22880,'humanInspectionPerformed':False}
    write(work/'inspection-preparation-private.json',report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--phase',choices=('prepare','rehearsal','paper','inspection'),default='prepare');p.add_argument('--paper-attempt',type=int,default=1);a=p.parse_args()
    try:
        work=a.work.resolve()
        if work==PRIVATE.resolve() or not work.is_relative_to(PRIVATE.resolve()):raise ValueError('PrivateFolderRequired')
        result=paper(work,a.paper_attempt) if a.phase=='paper' else {'prepare':prepare,'rehearsal':rehearsal,'inspection':prepare_inspection}[a.phase](work)
        print(json.dumps({k:v for k,v in result.items() if k in ('prepared','passed','payloadFiles','manifestEntries','sourceInputsUnchanged','originalShaftMaterials','previousRestorationsPreserved','naturalReferenceVerification','payloadChangedFromR2','archive','sourceAvailableFiles','remoteSourceFiles','installedFiles','quarantinedFiles','preservedFiles','rollbackFilesVerified','naturalBlocksChecked','surfaceChecksVerified','territoriesAndSpawnsVerified','errors','warnings','candidateUnchanged','queryLoopback')},ensure_ascii=False))
    except Exception as error:
        print(json.dumps({'failed':True,'reason':type(error).__name__,'detail':str(error)},ensure_ascii=False));sys.exit(1)
