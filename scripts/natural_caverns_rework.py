"""Variante locale distincte, sans réseau : plan, patch borné, preuve et archives privées."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile
from datetime import datetime,timezone
import server
from anvil_patch import patch_region,region_entries,load,plain,indices,state_key,parse_state,dump,Tag
from natural_caverns_plan import make_plan,VARIANT
from minestrator_cold_backup import protect_directory

ROOT=Path(__file__).resolve().parents[1]
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def inventory(root):return {p.relative_to(root).as_posix():server.digest(p) for p in server.iter_files(root)}
def unpack(entry):
    import gzip,zlib
    codec,data=entry
    return zlib.decompress(data) if codec==2 else gzip.decompress(data) if codec==1 else data

def archive(root,path,names):
    manifest={name:server.digest(root/name) for name in sorted(names)}
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for name in manifest:z.write(root/name,name)
        z.writestr('VARIANT_FILE_MANIFEST.json',json.dumps({'schema':1,'variant':VARIANT,'files':manifest},indent=2))
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise RuntimeError('Archive CRC invalide')
        for name,h in manifest.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=h:raise RuntimeError('SHA archive invalide')
    return {'file':str(path),'bytes':path.stat().st_size,'sha256':server.digest(path),'files':len(manifest)}

def verify_region(before,after,edits):
    a,b=region_entries(before),region_entries(after)
    if a.keys()!=b.keys():raise RuntimeError('Chunks ajoutés ou supprimés')
    outside=0;cells=0
    for index,payload in a.items():
        if index not in edits:
            if payload!=b[index]:raise RuntimeError('Chunk non ciblé différent')
            outside+=1;continue
        name,x=load(unpack(payload));name2,y=load(unpack(b[index]))
        if name!=name2:raise RuntimeError('Nom NBT changé')
        def without_sections(t):return dump(b'',Tag(10,{k:v for k,v in t.value.items() if k not in ('sections','isLightOn','starlight.light_version')}))
        if without_sections(x)!=without_sections(y):raise RuntimeError('Métadonnées ou inventaires de chunk changés')
        sx={s.value['Y'].value:s for s in x.value['sections'].value[1]};sy={s.value['Y'].value:s for s in y.value['sections'].value[1]}
        if sx.keys()!=sy.keys():raise RuntimeError('Sections ajoutées ou supprimées')
        for height,left in sx.items():
            right=sy[height]
            ignore={'block_states','BlockLight','SkyLight','starlight.skylight_state','starlight.blocklight_state'}
            if dump(b'',Tag(10,{k:v for k,v in left.value.items() if k not in ignore}))!=dump(b'',Tag(10,{k:v for k,v in right.value.items() if k not in ignore})):raise RuntimeError('Biomes ou métadonnées de section changés')
            def block_values(section):
                states=section.value.get('block_states')
                if states is None:return [('minecraft:air',())]*4096
                palettes=[state_key(plain(v)) for v in states.value['palette'].value[1]]
                return [palettes[i] for i in indices(states.value)]
            expected=block_values(left);actual=block_values(right)
            for i,state in edits[index].get(height,{}).items():expected[i]=parse_state(state)
            if expected!=actual:raise RuntimeError('Bloc hors plan modifié ou sortie incorrecte')
            cells+=4096
    return {'untouchedChunkPayloadsIdentical':outside,'blockCellsCompared':cells,'targetedChunks':len(edits),'nonLightingMetadataIdentical':True}

def run(source,work):
    source=source.resolve();work=work.resolve()
    if work.exists() or work.is_relative_to(source) or source.is_relative_to(work) or work.is_relative_to(ROOT):raise RuntimeError('Sortie neuve privée hors dépôt et distincte de la source obligatoire')
    protect_directory(work);candidate=work/'candidate';baseline_restore=work/'rollback-control'
    from map_v21_tool import initial
    with server.maintenance(source):
        before=inventory(source);initial((source/'plugins/FKAmis/state.yml').read_text(encoding='utf-8'),before)
        approved=json.loads((ROOT/'tests/results/query-rollback-delivery.json').read_text())
        if before['DEPLOYMENT_MANIFEST.json']!=approved['deploymentManifestSha256']:raise RuntimeError('Source V2.1 approuvée différente')
        for name,h in json.loads((source/'DEPLOYMENT_MANIFEST.json').read_text())['files'].items():
            if before[name]!=h:raise RuntimeError('Source changée : '+name)
        write(work/'source-files-private.json',before)
        shutil.copytree(source,candidate,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
        if inventory(candidate)!=before:raise RuntimeError('Copie locale différente')
        baseline_archive=archive(source,work/'baseline-v21-world.zip',[n for n in before if n.startswith('world/')])
    with server.maintenance(candidate):
        plan=make_plan(candidate);write(work/'natural-caverns-plan-private.json',plan)
        grouped={}
        for block in plan['blocks']:
            x,y,z=block['at'];name=f'world/dimensions/minecraft/overworld/region/r.{x//512}.{z//512}.mca'
            grouped.setdefault(name,{}).setdefault((x//16)%32+((z//16)%32)*32,{}).setdefault(y//16,{})[(y%16)*256+(z%16)*16+x%16]=block['after']
        proofs=[]
        for name,changes in grouped.items():
            original=(source/name).read_bytes();result,chunks=patch_region(original,changes)
            proof=verify_region(original,result,changes)
            target=candidate/name;temporary=target.with_suffix('.natural-new')
            with temporary.open('xb') as f:f.write(result)
            temporary.replace(target)
            proofs.append({'path':name,'oldSha256':before[name],'newSha256':server.digest(target),'chunks':chunks,**proof})
            print(json.dumps({'stage':'region_verified','regions':len(proofs),'total':len(grouped)}),flush=True)
        # Les métadonnées de jeu restent intactes ; seules les références de caverne évoluent.
        from map_reader import Reader
        reader=Reader(candidate);refs=json.loads((candidate/'maintenance/new-match-reference-v2.1.json').read_text())
        original_refs=copy.deepcopy(refs)
        for cave in refs['caverns']:
            points=sorted({tuple(b['at']) for b in plan['blocks'] if b['team']==cave['team']}|{tuple(p) for p in cave['checkPoints']})
            cave['checkPoints']=[list(p) for p in points]
            observed=[[x,y,z,reader.block(x,y,z)] for x,y,z in points]
            cave['blockTypesSha256']=hashlib.sha256(json.dumps(observed,separators=(',',':')).encode()).hexdigest()
        for name in ('new-match-reference.json','new-match-reference-v2.1.json','new-match-reference-v2.1-natural.json'):write(candidate/'maintenance'/name,refs)
        meta={k:v for k,v in plan.items() if k!='blocks'};meta.update({'sourceDeploymentManifestSha256':before['DEPLOYMENT_MANIFEST.json'],'sourceRevision':'V21-QUERY-20261120-01','remoteAccessPerformed':False})
        write(candidate/'map-natural-caverns.json',meta)
        manifest=json.loads((candidate/'DEPLOYMENT_MANIFEST.json').read_text())
        for name in grouped:manifest['files'][name]=server.digest(candidate/name)
        for name in ('maintenance/new-match-reference.json','maintenance/new-match-reference-v2.1.json','maintenance/new-match-reference-v2.1-natural.json','map-natural-caverns.json'):manifest['files'][name]=server.digest(candidate/name)
        manifest['localMapVariant']=VARIANT;write(candidate/'DEPLOYMENT_MANIFEST.json',manifest)
        after=inventory(candidate)
        changed=sorted(n for n in before if before[n]!=after.get(n));added=sorted(after.keys()-before.keys());removed=sorted(before.keys()-after.keys())
        allowed=set(grouped)|{'maintenance/new-match-reference.json','maintenance/new-match-reference-v2.1.json','DEPLOYMENT_MANIFEST.json'}
        if set(changed)!=allowed or removed:raise RuntimeError('Fichiers hors périmètre modifiés')
        for key in refs.keys()-{'caverns'}:
            if refs[key]!=original_refs[key]:raise RuntimeError('Métadonnée de carte altérée')
        if inventory(source)!=before:raise RuntimeError('Source altérée')
        artifact_names=[n for n in after if n.startswith('world/')]+['map-natural-caverns.json','maintenance/new-match-reference-v2.1-natural.json']
        slug=VARIANT.lower().replace('v2.1','v21')
        world_archive=archive(candidate,work/(slug+'-world-private.zip'),artifact_names)
        patch_archive=archive(candidate,work/(slug+'-overlay-private.zip'),changed+added)
        # Restauration de contrôle locale du point de retour créé sous verrou.
        with zipfile.ZipFile(baseline_archive['file']) as z:
            names=json.loads(z.read('VARIANT_FILE_MANIFEST.json'))['files'];baseline_restore.mkdir()
            for name,h in names.items():
                p=baseline_restore/name;p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(z.read(name))
                if server.digest(p)!=h:raise RuntimeError('Rollback local différent')
        write(work/'variant-files-private.json',after)
        result={'variant':VARIANT,'passed':True,'work':str(work),'candidate':str(candidate),'sourceUnchanged':True,'remoteAccessPerformed':False,'deployed':False,
            'modifiedBlocks':len(plan['blocks']),'modifiedChunks':len(plan['chunks']),'regions':proofs,'changedFiles':changed,'addedFiles':added,'removedFiles':removed,
            'unchangedFiles':len(before)-len(changed),'caverns':plan['caverns'],'archives':[baseline_archive,world_archive,patch_archive],
            'rollbackControlFilesVerified':len(names),'worldMetadataByteIdentical':True,'entityAndPoiFilesByteIdentical':True,'monumentsAndSuppliesMetadataIdentical':True,
            'gameAndRuntimeFilesByteIdentical':True,'visualValidation':False,'sourceDeploymentManifestSha256':before['DEPLOYMENT_MANIFEST.json'],
            'newDeploymentManifestSha256':after['DEPLOYMENT_MANIFEST.json'],'createdAtUtc':datetime.now(timezone.utc).isoformat()}
        write(work/'result-private.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.source,a.output);print(json.dumps({k:v for k,v in r.items() if k not in ('regions','caverns')},ensure_ascii=False))
