"""V2.2 locale : retour exact aux blocs de l'archive approuvée, sans régénération."""
import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile
import server
from anvil_patch import patch_region
from natural_caverns_plan import text_state
from natural_caverns_rework import inventory,verify_region,write
from map_reader import Reader
from world_integrity import chunks,decode
from minestrator_cold_backup import protect_directory
sys.path.insert(0,str(server.ROOT/'deployment'))
from terrain_reference import SOURCE,fingerprint,normalized,state

VARIANT='V2.2-vanilla-underground'
class ArchiveReader(Reader):
    def __init__(self,archive):self.archive=archive;self.chunks={};self.regions={}
    def chunk(self,cx,cz):
        if (cx,cz) not in self.chunks:
            name=f'world/dimensions/minecraft/overworld/region/r.{cx//32}.{cz//32}.mca'
            if name not in self.regions:self.regions[name]=chunks(self.archive.read(name))
            self.chunks[cx,cz]=decode(self.regions[name][cx%32+cz%32*32])
        return self.chunks[cx,cz]

def plan(source,archive):
    old=json.loads((source/'map-v21-plan.json').read_text(encoding='utf-8'))
    if len(old['blocks'])!=37128 or {b['team'] for b in old['blocks']}!={'Rouge','Bleue','Verte','Jaune'}:raise RuntimeError('Plan historique incomplet')
    current=Reader(source);restoration=[];points=[];budgets={}
    with zipfile.ZipFile(archive) as z:
        initial=ArchiveReader(z)
        for block in old['blocks']:
            at=block['at'];target=text_state(initial,at);before=text_state(current,at)
            if target.partition('[')[0]!=block['before']:raise RuntimeError('Le plan historique ne correspond pas au terrain approuvé')
            points.append(at)
            if before!=target:restoration.append({'at':at,'before':before,'after':target,'team':block['team']})
            budgets.setdefault(block['team'],Counter())[target.partition('[')[0]]+=1
    if len({tuple(p) for p in points})!=len(points):raise RuntimeError('Cellules historiques dupliquées')
    return {'variant':VARIANT,'sourceArchiveSha256':SOURCE,'blocks':restoration,'checkPoints':sorted(points),'naturalBlockCountsByTeam':{k:dict(v) for k,v in budgets.items()},'historicalBeforeMismatches':0,'randomGenerationPerformed':False}

def refresh_manifest(candidate,original):
    data=copy.deepcopy(original)
    # Les anciens enregistrements de construction restent en historique, hors racine active.
    data['files']={name:server.digest(candidate/name) for name in original['files'] if (candidate/name).is_file()}
    for name in ('maintenance/new-match-reference-v2.2.json','maintenance/terrain_reference.py','maintenance/block-defaults-26.3.json','map-underground-restoration.json','spigot.yml'):
        data['files'][name]=server.digest(candidate/name)
    for path in (candidate/'reference/history-v21').glob('*'):
        data['files'][path.relative_to(candidate).as_posix()]=server.digest(path)
    data['localMapVariant']=VARIANT
    write(candidate/'DEPLOYMENT_MANIFEST.json',data)

def notification_language(candidate):
    overrides=server.ROOT/'configs/fallenkingdom/territory-notifications-fr.properties'
    path=candidate/'plugins/FallenKingdom/locales/messages_fr.properties';data=path.read_bytes()
    for line in overrides.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        key,value=line.split('=',1);pattern=b'(?m)^'+re.escape(key.encode())+b'=[^\r\n]*'
        data,count=re.subn(pattern,(key+'='+value).encode('utf-8'),data)
        if count!=1:raise RuntimeError('Clé de traduction absente ou dupliquée : '+key)
    path.write_bytes(data)

def reconcile_plugin(work,plugin):
    candidate=work/'candidate';expected=json.loads((work/'candidate-files-private.json').read_text())
    if inventory(candidate)!=expected:raise RuntimeError('Le candidat a changé hors préparation')
    source=json.loads((work/'source-files-private.json').read_text())
    original=json.loads((Path.home()/'FKBackups/V21-QUERY-20261120-01/preproduction-candidate/DEPLOYMENT_MANIFEST.json').read_text())
    with server.maintenance(candidate):
        shutil.copy2(plugin,candidate/'plugins/FKAmis-1.0.0.jar');h=server.digest(plugin)
        (candidate/'FKAmis.sha256').write_text(h+'\n',encoding='ascii')
        lock=json.loads((candidate/'RUNTIME_LOCK.json').read_text());lock['sha256']['plugins/FKAmis-1.0.0.jar']=h;write(candidate/'RUNTIME_LOCK.json',lock)
        notification_language(candidate)
        for name in ('new_match.py','terrain_reference.py'):shutil.copy2(server.ROOT/'deployment'/name,candidate/'maintenance'/name)
        refresh_manifest(candidate,original);after=inventory(candidate)
        report=json.loads((work/'prepared-private.json').read_text());report['fkamisSha256']=h
        report['changedFiles']=sorted(n for n in source.keys()&after.keys() if source[n]!=after[n]);report['addedFiles']=sorted(after.keys()-source.keys())
        report['translationOverridesApplied']=4
        write(work/'prepared-private.json',report);write(work/'candidate-files-private.json',after)
    return h

def verify_original_terrain(work,archive):
    from world_integrity import states_equal
    candidate=work/'candidate';report=json.loads((work/'prepared-private.json').read_text());reader=Reader(candidate)
    raw=json.loads((candidate/'maintenance/block-defaults-26.3.json').read_text())
    defaults={name:normalized({'Name':name},raw)['Properties'] for name in raw}
    checked=0;sections=0
    with zipfile.ZipFile(archive) as z:
        original=ArchiveReader(z)
        for region in report['regions']:
            rx,rz=map(int,Path(region['path']).stem.split('.')[1:])
            for chunk in region['chunks']:
                cx,cz=rx*32+chunk['index']%32,rz*32+chunk['index']//32
                a={s['Y']:s for s in original.chunk(cx,cz).get('sections',[])};b={s['Y']:s for s in reader.chunk(cx,cz).get('sections',[])}
                for y in a.keys()|b.keys():
                    left=a.get(y,{}).get('block_states') or {'palette':['minecraft:air']};right=b.get(y,{}).get('block_states') or {'palette':['minecraft:air']}
                    if not states_equal(left,right,defaults=defaults):raise RuntimeError('Terrain différent de l’archive approuvée dans un chunk restauré')
                    sections+=1
                checked+=1
    proof={'passed':True,'chunksComparedCompletelyToInitialTerrain':checked,'blockSectionsCompared':sections,'sourceArchiveSha256':SOURCE,'generationPerformed':False}
    write(work/'original-terrain-comparison-private.json',proof);return proof

def prepare(source,archive,output,plugin):
    source=source.resolve();archive=archive.resolve();output=output.resolve();plugin=plugin.resolve()
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output) or output.is_relative_to(server.ROOT):raise RuntimeError('Sortie privée neuve et distincte requise')
    if server.digest(archive)!=SOURCE:raise RuntimeError('Archive antérieure non approuvée')
    server.verify_archive(archive)
    protect_directory(output);candidate=output/'candidate'
    with server.maintenance(source):
        before=inventory(source)
        approved=json.loads((server.ROOT/'tests/results/query-rollback-delivery.json').read_text())
        if before['DEPLOYMENT_MANIFEST.json']!=approved['deploymentManifestSha256']:raise RuntimeError('Source V2.1 approuvée différente')
        for name,h in json.loads((source/'DEPLOYMENT_MANIFEST.json').read_text())['files'].items():
            if before[name]!=h:raise RuntimeError('Source V2.1 altérée')
        from map_v21_tool import initial
        initial((source/'plugins/FKAmis/state.yml').read_text(),before)
        server.create_archive(source,output/'before-v22-local.zip')
        write(output/'source-files-private.json',before)
        shutil.copytree(source,candidate,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
        if inventory(candidate)!=before:raise RuntimeError('Copie locale différente')
        restoration=plan(source,archive)
    with server.maintenance(candidate):
        write(output/'restoration-plan-private.json',restoration)
        grouped={}
        for block in restoration['blocks']:
            x,y,z=block['at'];name=f'world/dimensions/minecraft/overworld/region/r.{x//512}.{z//512}.mca'
            grouped.setdefault(name,{}).setdefault(x//16%32+z//16%32*32,{}).setdefault(y//16,{})[(y%16)*256+(z%16)*16+x%16]=block['after']
        proofs=[]
        for name,changes in grouped.items():
            raw=(source/name).read_bytes();patched,entries=patch_region(raw,changes)
            proof=verify_region(raw,patched,changes)
            target=candidate/name;temporary=target.with_suffix('.vanilla-new')
            with temporary.open('xb') as f:f.write(patched)
            temporary.replace(target)
            proofs.append({'path':name,'oldSha256':before[name],'newSha256':server.digest(target),'chunks':entries,**proof})
            print(json.dumps({'stage':'original_terrain_restored','regions':len(proofs),'total':len(grouped)}),flush=True)
        defaults_source=server.ROOT/'.cache/gameplay-qa/tests/results/block-defaults-26.3.json'
        defaults=json.loads(defaults_source.read_text())
        with zipfile.ZipFile(archive) as z:
            trusted=ArchiveReader(z);reader=Reader(candidate)
            target_hash=fingerprint(trusted,restoration['checkPoints'],defaults)
            if fingerprint(reader,restoration['checkPoints'],defaults)!=target_hash:raise RuntimeError('Restauration différente des blocs originaux')
        old_reference=json.loads((source/'maintenance/new-match-reference-v2.1.json').read_text())
        reference=copy.deepcopy(old_reference);reference['mapVersion']='2.2';reference['caverns']=[]
        reference['underground']={'mode':'vanilla-restored','sourceArchiveSha256':SOURCE,'checkPoints':restoration['checkPoints'],
            'blockStatesSha256':target_hash,'blockDefaultsSha256':server.digest(defaults_source)}
        for name in ('new-match-reference.json','new-match-reference-v2.2.json'):write(candidate/'maintenance'/name,reference)
        shutil.copy2(defaults_source,candidate/'maintenance/block-defaults-26.3.json')
        for name in ('new_match.py','terrain_reference.py'):shutil.copy2(server.ROOT/'deployment'/name,candidate/'maintenance'/name)
        historic=candidate/'reference/history-v21';historic.mkdir(parents=True)
        for path in candidate.glob('map-v21-*.json'):
            destination=historic/path.name
            if not destination.resolve().is_relative_to(candidate) or destination.exists():raise RuntimeError('Historique local hors périmètre')
            path.rename(destination)
        built=json.loads((candidate/'map-v2-construction.json').read_text());built['mapVersion']='2.2';built['mapVariant']=VARIANT
        write(candidate/'map-v2-construction.json',built)
        shutil.copy2(plugin,candidate/'plugins/FKAmis-1.0.0.jar');(candidate/'FKAmis.sha256').write_text(server.digest(plugin)+'\n',encoding='ascii')
        notification_language(candidate)
        lock=json.loads((candidate/'RUNTIME_LOCK.json').read_text());lock['sha256']['plugins/FKAmis-1.0.0.jar']=server.digest(plugin);lock['fkamisUpdate']='vnext.1-territory-notifications'
        write(candidate/'RUNTIME_LOCK.json',lock)
        patch=Path.home()/'FKBackups/MS-RESTART-CHECK-20261120-01/proposed-maintenance/spigot.yml'
        if server.digest(patch)!='63e939902bc52b0868598205130a94bb5e9f3733073008a05399fddfef687667':raise RuntimeError('Correctif Spigot approuvé différent')
        shutil.copy2(patch,candidate/'spigot.yml')
        meta={'variant':VARIANT,'undergroundMode':'vanilla-restored','sourceArchiveSha256':SOURCE,'restorationPlanSha256':server.digest(output/'restoration-plan-private.json'),
            'restoredBlockStates':len(restoration['blocks']),'verifiedOriginalCells':len(restoration['checkPoints']),'randomGenerationPerformed':False,'visualValidation':False}
        write(candidate/'map-underground-restoration.json',meta)
        original_manifest=json.loads((source/'DEPLOYMENT_MANIFEST.json').read_text());refresh_manifest(candidate,original_manifest)
        after=inventory(candidate)
        protected=('plugins/FKAmis/config.yml','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','server.properties','whitelist.json','ops.json')
        if any(before[n]!=after[n] for n in protected):raise RuntimeError('Données de jeu ou accès altérés')
        if inventory(source)!=before:raise RuntimeError('Référence source altérée')
        result={'variant':VARIANT,'prepared':True,'candidate':str(candidate),'sourceArchiveSha256':SOURCE,'fkamisSha256':server.digest(plugin),
            'restoredBlockStates':len(restoration['blocks']),'originalFootprintCellsVerified':len(restoration['checkPoints']),'regions':proofs,
            'modifiedChunks':sum(len(p['chunks']) for p in proofs),'sourceUnchanged':True,'protectedFilesUnchanged':list(protected),
            'changedFiles':sorted(n for n in before.keys()&after.keys() if before[n]!=after[n]),'addedFiles':sorted(after.keys()-before.keys()),
            'removedActivePaths':sorted(before.keys()-after.keys()),'historicalRecordsMovedNotDeleted':True,'remoteAccessPerformed':False,'deployed':False,'visualValidation':False}
        write(output/'prepared-private.json',result);write(output/'candidate-files-private.json',after)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--plugin',type=Path,default=server.PLUGIN);a=p.parse_args()
    print(json.dumps(prepare(a.source,a.archive,a.output,a.plugin),ensure_ascii=False))
