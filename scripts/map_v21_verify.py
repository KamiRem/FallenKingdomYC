"""Comparaison complète des blocs hors chantier et des inventaires/entités d'une sortie V2.1."""
import hashlib
import json
from pathlib import Path
import zipfile
import copy
from world_integrity import chunks,decode,canonical,entity_inventory,states_equal
from map_reader import normalized_state,Reader
from cavern_plan import connected_floor
import server


def state_value(value,defaults):
    value=normalized_state(value);props=dict(defaults.get(value['Name'],{}));props.update(value.get('Properties',{}))
    return canonical({'Name':value['Name'],'Properties':props} if props else {'Name':value['Name']})


def expanded(states,defaults):
    if not states:return [state_value('minecraft:air',defaults)]*4096
    palette=[state_value(value,defaults) for value in states['palette']]
    if len(palette)==1:return palette*4096
    bits=max(4,(len(palette)-1).bit_length());per=64//bits
    return [palette[((states['data'][i//per]&((1<<64)-1))>>((i%per)*bits))&((1<<bits)-1)] for i in range(4096)]


def after_state(text,defaults):
    name,_,properties=text.partition('[');value={'Name':name}
    if properties:value['Properties']=dict(piece.split('=',1) for piece in properties.removesuffix(']').split(','))
    return state_value(value,defaults)


def verify(root,backup,defaults_path,plan=None):
    root=root.resolve();plan=plan if plan is not None else json.loads((root/'map-v21-plan.json').read_text(encoding='utf-8'));raw=json.loads(defaults_path.read_text(encoding='utf-8'))
    defaults={name:dict(piece.split('=',1) for piece in value.partition('[')[2].removesuffix(']').split(',') if piece) for name,value in raw.items()}
    modifications={};actual_changed=set();errors=[];checked=0;identical=0;entities=0;inventory_chunks=0;runtime_fields=[]
    for b in plan['blocks']:
        x,y,z=b['at'];modifications.setdefault((x>>4,z>>4),{}).setdefault(y>>4,{})[(y&15)*256+(z&15)*16+(x&15)]=after_state(b['after'],defaults)
    with server.maintenance(root),zipfile.ZipFile(backup) as source:
        manifest=json.loads(source.read('BACKUP_MANIFEST.json'))['files'];names=[name for name in manifest if name.startswith('world/') and name.endswith('.mca')]
        if set(names)!={p.relative_to(root).as_posix() for p in (root/'world').rglob('*.mca')}:raise RuntimeError('Régions ajoutées ou retirées.')
        for name in names:
            path=root/name
            if server.digest(path)==manifest[name]:identical+=1;continue
            before,after=chunks(source.read(name)),chunks(path.read_bytes())
            if before.keys()!=after.keys():raise RuntimeError('Chunks ajoutés ou supprimés : '+name)
            region_x,region_z=map(int,path.stem.split('.')[1:])
            for index,value in before.items():
                if value==after[index]:continue
                a,b=decode(value),decode(after[index]);cx=region_x*32+index%32;cz=region_z*32+index//32
                if '/region/' in name:
                    checked+=1;old_sections={s['Y']:s for s in a.get('sections',[])};new_sections={s['Y']:s for s in b.get('sections',[])}
                    if old_sections.keys()!=new_sections.keys():raise RuntimeError('Sections de terrain différentes.')
                    for y,section in old_sections.items():
                        expected=expanded(section.get('block_states'),defaults);observed=expanded(new_sections[y].get('block_states'),defaults)
                        for cell,state in modifications.get((cx,cz),{}).get(y,{}).items():expected[cell]=state
                        if expected!=observed:errors.append({'chunk':[cx,cz],'section':y,'reason':'bloc hors plan ou état de sortie différent','cells':sum(x!=y for x,y in zip(expected,observed))})
                        if not states_equal(section.get('biomes'),new_sections[y].get('biomes'),64,1):errors.append({'chunk':[cx,cz],'reason':'biomes différents'})
                    def tiles(chunk):
                        result=[]
                        for raw_tile in chunk.get('block_entities',[]):
                            tile=copy.deepcopy(raw_tile);tile.pop('keepPacked',None)
                            if tile.get('id') in ('minecraft:furnace','minecraft:blast_furnace','minecraft:smoker') and tile.get('speed_multiplier')==1:tile.pop('speed_multiplier')
                            if tile.get('id')=='minecraft:vault' and 'server_data' in tile:tile['server_data'].pop('state_updating_resumes_at',None)
                            result.append(canonical(tile))
                        return sorted(result)
                    old_tiles={(t.get('x'),t.get('y'),t.get('z')):t for t in a.get('block_entities',[])}
                    for tile in b.get('block_entities',[]):
                        at=(tile.get('x'),tile.get('y'),tile.get('z'));old=old_tiles.get(at,{})
                        if old!=tile and tiles({'block_entities':[old]})==tiles({'block_entities':[tile]}):runtime_fields.append({'at':list(at),'type':tile.get('id'),'normalizedFields':['keepPacked','default furnace speed_multiplier=1','vault server_data.state_updating_resumes_at']})
                    if tiles(a)!=tiles(b):errors.append({'chunk':[cx,cz],'reason':'conteneurs ou block entities différents'})
                    if (cx,cz) in modifications:actual_changed.add((cx,cz))
                elif '/entities/' in name:
                    inventory_chunks+=1
                    if entity_inventory(a)!=entity_inventory(b):errors.append({'chunk':[cx,cz],'reason':'UUID ou inventaires entités différents'})
                    def positions(chunk):return {canonical(e.get('UUID',e.get('uuid'))):e.get('Pos',e.get('pos')) for e in chunk.get('Entities',[])}
                    if positions(a)!=positions(b):errors.append({'chunk':[cx,cz],'reason':'positions entités différentes'})
                    entities+=len(positions(a))
        reader=Reader(root);routes=[]
        for cave in plan['caverns']:
            local={tuple(b['at']):(reader.block(*b['at']).removeprefix('minecraft:'),b['kind']) for b in plan['blocks'] if b['team']==cave['team']}
            reachable=connected_floor(local,tuple(cave['center']));valid=tuple(cave['entrance']) in reachable
            if not valid:errors.append({'team':cave['team'],'reason':'accès non relié dans les chunks enregistrés'})
            routes.append({'team':cave['team'],'entranceConnected':valid,'actualReachableFloorCells':len(reachable)})
    result={'passed':not errors,'sourceBackupSha256':server.digest(backup),'regionFilesByteIdentical':identical,'terrainChunksSemanticallyChecked':checked,
        'constructionChunks':len(actual_changed),'plannedChunks':len(plan['chunks']),'entityChunksCompared':inventory_chunks,'entitiesInChangedChunksCompared':entities,'errors':errors,'routes':routes,
        'runtimeBlockEntityFieldsNormalized':runtime_fields,
        'blockEntitiesAndInventoriesUnchanged':not any('inventair' in e['reason'] or 'conteneur' in e['reason'] for e in errors),'visualInspection':False}
    return result
