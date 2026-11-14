"""Plans V2.1 déterministes : quatre cavernes, budget commun, accès et enveloppes bornés."""
import hashlib
import json
import math
from collections import Counter
from map_reader import Reader

TEAMS=('Rouge','Bleue','Verte','Jaune')
ORES={'coal_ore':24,'iron_ore':24,'copper_ore':16,'redstone_ore':12,'lapis_ore':6,'gold_ore':6,'diamond_ore':3}
THEMES={
 'Rouge':('volcanique_sans_lave','polished_basalt','blackstone','red_terracotta'),
 'Bleue':('cristaux','calcite','amethyst_block','blue_terracotta'),
 'Verte':('luxuriante','moss_block','rooted_dirt','azalea_leaves[persistent=true,distance=1,waterlogged=false]'),
 'Jaune':('mine_minerale','tuff','calcite','yellow_terracotta')}
NATURAL={'air','cave_air','void_air','stone','deepslate','tuff','dirt','grass_block','coarse_dirt','rooted_dirt','podzol',
 'gravel','sand','sandstone','clay','granite','andesite','diorite','calcite','smooth_basalt','water','lava','moss_block',
 'short_grass','tall_grass','fern','large_fern','snow','snow_block','dead_bush','seagrass','tall_seagrass','kelp','kelp_plant','glow_lichen','dripstone_block','pointed_dripstone',
 'copper_ore','iron_ore','gold_ore','coal_ore','redstone_ore','lapis_ore','diamond_ore','emerald_ore'}
NATURAL.update('deepslate_'+name for name in list(NATURAL) if name.endswith('_ore'))


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def surface(reader,x,z):
    cache=getattr(reader,'surfaces',None)
    if cache is None:cache={};reader.surfaces=cache
    if (x,z) in cache:return cache[x,z]
    for y in range(140,35,-1):
        material=reader.block(x,y,z).removeprefix('minecraft:')
        if material in {'grass_block','dirt','stone','sand','gravel','podzol','moss_block','coarse_dirt','rooted_dirt'}:cache[x,z]=y;return y
    raise RuntimeError('Sol naturel introuvable pour l’accès : '+str((x,z)))


def make_plan(root,metadata,reference):
    reader=Reader(root);changes={};metrics=[];collision=[];technical=[]
    for m in reference['monuments']:
        for dx,dy,dz in m['checkPoints']:technical.append((m['x']+dx,m['y']+dy,m['z']+dz))
    technical=set(technical)|{tuple(s['at']) for s in reference['supplies']}
    all_bases={b['team']:b for b in metadata['bases']}
    grounds={team:surface(reader,int(all_bases[team]['x']),int(all_bases[team]['z'])) for team in TEAMS}
    for team in TEAMS:
        base=all_bases[team];cx,cz=int(base['x']),int(base['z']);theme,wall,accent,color=THEMES[team]
        mirror=team in ('Verte','Jaune')
        def actual_x(x):return 2*cx-x if mirror else x
        floor=grounds[team]-42
        if floor<0:raise RuntimeError('Profondeur imprévue : refus plutôt qu’une caverne près du bedrock.')
        local={};access=set();floor_cells=[];walkable=set()
        def put(x,y,z,material,kind='chamber'):
            if abs(x-cx)>30 or abs(z-cz)>30:raise AssertionError('Volume hors du périmètre de sécurité.')
            local[x,y,z]=(material,kind)
        # Coque solide de deux blocs : les cavités et fluides voisins ne deviennent pas des passages.
        for dx in range(-16,17):
            for dz in range(-13,14):
                h=dx*dx/196+dz*dz/121
                if h>1.36:continue
                ceiling=floor+max(4,int(11*math.sqrt(max(0,1-min(h,1)))))
                for y in range(floor-2,ceiling+3):put(cx+dx,y,cz+dz,'stone')
                if h<=1:
                    for y in range(floor+1,ceiling+1):put(cx+dx,y,cz+dz,'air');walkable.add((cx+dx,y,cz+dz))
                    put(cx+dx,floor,cz+dz,wall if (dx*17+dz*31)%7==0 else 'stone')
                    if h<.82:floor_cells.append((cx+dx,floor,cz+dz))
                elif h<1.15:
                    for y in range(floor,ceiling+2):
                        if (dx*13+dz*11+y)%5==0:put(cx+dx,y,cz+dz,accent)
        entrance_x,entrance_z=cx+24,cz-28;entry_y=surface(reader,actual_x(entrance_x),entrance_z)+1;steps=entry_y-(floor+1)
        if not 30<=steps<=52:raise RuntimeError('Accès trop différent entre les royaumes : '+team)
        if -28+steps>27:raise RuntimeError('Escalier hors territoire réduit.')
        path=[(cx+24,entry_y-n,cz-28+n) for n in range(steps+1)]
        end_z=path[-1][2]
        path.extend((cx+x,floor+1,end_z) for x in range(23,7,-1))
        direction=-1 if end_z>cz+8 else 1
        path.extend((cx+8,floor+1,z) for z in range(end_z+direction,cz+8+direction,direction))
        for x,y,z in path:
            # Couloir 2×3 ; murs et plafond fermés, entrée seule ouverte en surface.
            for ax in range(x-2,x+2):
                for az in range(z-1,z+2):
                    for ay in range(y-2,y+5):
                        if ay<=surface_limit(root,reader,actual_x(ax),az,grounds[team]) and local.get((ax,ay,az),('',))[0]!='air':put(ax,ay,az,'stone','access')
        for i,(x,y,z) in enumerate(path):
            for ax in (x-1,x):
                put(ax,y-1,z,'stone_brick_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]' if i<steps else 'stone_bricks','access')
                for ay in range(y,y+3):put(ax,ay,z,'air','access');walkable.add((ax,ay,z))
                access.add((ax,y-1,z))
        # Lumière sans lave, magma, feu ni récompense renouvelable.
        for dx,dz in [(-8,-5),(8,-5),(-8,5),(8,5)]:
            put(cx+dx,floor,cz+dz,'sea_lantern');access.add((cx+dx,floor,cz+dz))
            put(cx+dx,floor+1,cz+dz,accent);put(cx+dx,floor+2,cz+dz,color)
            put(cx+dx,floor+3,cz+dz,'sea_lantern')
            walkable.discard((cx+dx,floor+1,cz+dz));walkable.discard((cx+dx,floor+2,cz+dz))
        candidates=sorted((p for p in floor_cells if p not in access and local.get(p,('',))[0] not in ('sea_lantern',accent,color)),key=lambda p:hashlib.sha256(str((p[0]-cx,p[2]-cz,2191)).encode()).digest())
        budget=[]
        for ore,count in ORES.items():budget.extend([ore]*count)
        if len(candidates)<len(budget):raise RuntimeError('Places de minerai insuffisantes.')
        for p,ore in zip(candidates,budget):local[p]=(ore,'resource')
        # Référence initiale : des animaux occupent les accès est de Verte et
        # Jaune. Le même plan est réfléchi, sans déplacer ces entités.
        if mirror:
            entrance_x=cx-24
            local={(2*cx-x,y,z):value for (x,y,z),value in local.items()}
        actual_resources=Counter()
        for (x,y,z),(material,kind) in sorted(local.items()):
            old=reader.block(x,y,z);name=old.removeprefix('minecraft:')
            if name not in NATURAL:collision.append({'team':team,'at':[x,y,z],'reason':'bloc hors palette naturelle','type':old})
            if (x,y,z) in technical or abs(x-cx)<=8 and abs(z-cz)<=8 and y>=grounds[team]-12:collision.append({'team':team,'at':[x,y,z],'reason':'volume technique ou fondation'})
            if (x,y,z) in changes:raise RuntimeError('Cavernes en intersection.')
            if material in ORES:actual_resources[material]+=1
            changes[x,y,z]={'at':[x,y,z],'before':old,'after':'minecraft:'+material,'team':team,'kind':kind}
        reachable=connected_floor(local,(cx,floor+1,cz))
        if len(reachable)<350:raise RuntimeError('Circulation de la caverne insuffisante : '+team)
        if (entrance_x,entry_y,entrance_z) not in reachable:raise RuntimeError('Entrée non reliée à la chambre : '+team)
        if any((x,y+1,z) not in reachable for (x,y,z),(material,kind) in local.items() if kind=='resource'):raise RuntimeError('Minerai inaccessible : '+team)
        metrics.append({'team':team,'theme':theme,'center':[cx,floor+1,cz],'entrance':[entrance_x,entry_y,entrance_z],
            'entryDistanceToBase':math.hypot(24,28),'entrances':1,'floorY':floor,'depthFromBase':grounds[team]-floor,
            'plannedAirBlocks':sum(m=='air' for m,k in local.values()),'reachableFloorCells':len(reachable),'stairs':steps,
            'resources':dict(actual_resources),'lavaBlocks':0,'fireBlocks':0,'minimumHorizontalTerritoryMargin':10,'modifiedBlocks':len(local),
            'visuallyInspected':False})
    # Les conteneurs et entités existants ne sont jamais déplacés pour forcer un plan.
    for (cx,cz),chunk in reader.chunks.items():
        for tile in chunk.get('block_entities',[]):
            at=(tile.get('x'),tile.get('y'),tile.get('z'))
            if at in changes:collision.append({'at':list(at),'reason':'block entity existante'})
    check_entity_collisions(root,changes,collision)
    blocks=[changes[key] for key in sorted(changes)];chunks=sorted({(x>>4,z>>4) for x,y,z in changes})
    return {'schema':1,'mapVersion':'2.1','referenceOnly':True,'radiusBefore':80,'radiusAfter':40,'blocks':blocks,'planSha256':digest(blocks),
        'chunks':[list(c) for c in chunks],'caverns':metrics,'collisions':collision,'passed':not collision,'visualValidation':False}


def surface_limit(root,reader,x,z,fallback):
    # Le plan ne ferme pas l'air du paysage au-dessus du relief.
    return max(fallback,surface(reader,x,z))


def connected_floor(local,start):
    def free(p):return local.get(p,('stone',''))[0]=='air'
    def supported(p):return free(p) and free((p[0],p[1]+1,p[2])) and local.get((p[0],p[1]-1,p[2]),('air',''))[0]!='air'
    seen=set();todo=[start]
    while todo:
        p=todo.pop()
        if p in seen or not supported(p):continue
        seen.add(p)
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
            for dy in (0,1,-1):
                nxt=(p[0]+dx,p[1]+dy,p[2]+dz)
                if nxt not in seen and supported(nxt):todo.append(nxt)
    return seen


def check_entity_collisions(root,changes,collision):
    import gzip,zlib
    from map_reader import nbt
    from pathlib import Path
    regions=root/'world/dimensions/minecraft/overworld/entities'
    chunk_positions={(x>>4,z>>4) for x,y,z in changes}
    for cx,cz in chunk_positions:
        path=regions/f'r.{cx//32}.{cz//32}.mca'
        if not path.exists():continue
        with path.open('rb') as f:
            f.seek(((cx%32)+(cz%32)*32)*4);offset=int.from_bytes(f.read(3),'big');f.read(1)
            if not offset:continue
            f.seek(offset*4096);size=int.from_bytes(f.read(4),'big');kind=f.read(1)[0];raw=f.read(size-1)
        data=nbt(zlib.decompress(raw) if kind==2 else gzip.decompress(raw) if kind==1 else raw)
        for entity in data.get('Entities',[]):
            pos=entity.get('Pos',entity.get('pos'))
            if pos:
                x,y,z=map(math.floor,pos)
                if any((x+dx,y+dy,z+dz) in changes for dx in (-1,0,1) for dy in (0,1,2) for dz in (-1,0,1)):collision.append({'at':[x,y,z],'reason':'entité existante dans le chantier','type':entity.get('id')})
