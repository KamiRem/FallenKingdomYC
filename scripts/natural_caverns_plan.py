"""Quatre cavernes organiques locales : volumes bornés, budgets et accès conservés."""
from collections import Counter,deque
import hashlib
import json
import math
from cavern_plan import ORES,TEAMS,NATURAL,check_entity_collisions,surface
from map_reader import Reader
from world_integrity import chunks,decode

VARIANT='V2.1-natural-caverns-r2'
AIR={'minecraft:air','minecraft:cave_air','minecraft:void_air'}
def stable(n,x,y,z):return int.from_bytes(hashlib.sha256(f'{n}:{x}:{y}:{z}'.encode()).digest()[:4],'big')

def room_shape(seed):
    phase=seed*.811
    cells=set()
    for x in range(-24,25):
        for z in range(-21,22):
            xx=x-1.8*math.sin(z*.19+phase);zz=z-.8*math.cos(x*.22-phase)
            angle=math.atan2(zz/17.8,xx/21.2)
            limit=1+.07*math.sin(3*angle+phase)+.04*math.sin(5*angle-phase)
            if (xx/21.2)**2+(zz/17.8)**2<limit**2:cells.add((x,z))
    return cells

def distance_from_edge(cells):
    distance={p:0 for p in cells if any((p[0]+dx,p[1]+dz) not in cells for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)))}
    queue=deque(distance)
    while queue:
        x,z=queue.popleft()
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
            q=x+dx,z+dz
            if q in cells and q not in distance:distance[q]=distance[x,z]+1;queue.append(q)
    return distance

def text_state(reader,p):
    from map_reader import normalized_state
    x,y,z=p;chunk=reader.chunk(x//16,z//16)
    section=next(s for s in chunk['sections'] if s['Y']==y//16);states=section.get('block_states')
    if not states:return 'minecraft:air'
    palette=states['palette'];index=0
    if len(palette)>1:
        bits=max(4,(len(palette)-1).bit_length());per=64//bits;i=(y%16)*256+(z%16)*16+x%16
        index=((states['data'][i//per]&((1<<64)-1))>>((i%per)*bits))&((1<<bits)-1)
    state=normalized_state(palette[index]);props=state.get('Properties',{})
    return state['Name']+('['+','.join(k+'='+v for k,v in sorted(props.items()))+']' if props else '')

def walkable(local):
    free=lambda s:s.partition('[')[0] in AIR|{'minecraft:glow_lichen'}
    solid=lambda p:local.get(p,'minecraft:stone').partition('[')[0] not in AIR|{'minecraft:water','minecraft:glow_lichen'}
    return {p for p,s in local.items() if free(s) and free(local.get((p[0],p[1]+1,p[2]),'minecraft:stone')) and solid((p[0],p[1]-1,p[2]))}

def reachable(cells,start):
    seen=set();todo=[start]
    while todo:
        p=todo.pop()
        if p in seen or p not in cells:continue
        seen.add(p)
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
            for dy in (-1,0,1):
                q=p[0]+dx,p[1]+dy,p[2]+dz
                # Saut d'une marche : espace au-dessus du marcheur avant montée.
                if q in cells and q not in seen:todo.append(q)
    return seen

def make_plan(root):
    reader=Reader(root)
    original=json.loads((root/'map-v21-plan.json').read_text())
    reference=json.loads((root/'maintenance/new-match-reference-v2.1.json').read_text())
    old_metrics=json.loads((root/'map-v21-caverns.json').read_text())['caverns']
    bases={b['team']:b for b in reference['bases']};all_edits={};metrics=[];collision=[];technical=set()
    for m in reference['monuments']:
        technical.update((m['x']+x,m['y']+y,m['z']+z) for x,y,z in m['checkPoints'])
    technical.update(tuple(s['at']) for s in reference['supplies'])
    entity_positions=[]
    for path in (root/'world/dimensions/minecraft/overworld/entities').glob('*.mca'):
        for payload in chunks(path.read_bytes()).values():
            for entity in decode(payload).get('Entities',[]):
                pos=entity.get('Pos',entity.get('pos'))
                if pos:entity_positions.append(tuple(map(math.floor,pos)))
    for seed,team in enumerate(TEAMS,1):
        old=next(c for c in old_metrics if c['team']==team);cx,_,cz=old['center'];f=old['floorY'];ground=f+42
        mirror=-1 if team in ('Verte','Jaune') else 1
        local={};kinds={};old_blocks=[b for b in original['blocks'] if b['team']==team]
        preserved_access={tuple(b['at']):text_state(reader,tuple(b['at'])) for b in old_blocks if b['kind']=='access' and (b['after'].endswith(':air') or 'stone_brick' in b['after'])}
        def put(p,s,kind='rock'):
            if s=='waterfall':s='minecraft:water[level=8]'
            elif not s.startswith('minecraft:'):s='minecraft:'+s
            local[p]=s;kinds[p]=kind
        def at(x,y,z):return cx+mirror*x,y,cz+z
        def rock(x,y,z):
            band=math.sin(y*.31+1.4*math.sin(x*.13+seed)+1.1*math.cos(z*.17-seed))+.38*math.sin(x*.37+z*.21+y*.19)
            return 'deepslate' if y<f-8 and band<-.7 else 'tuff' if band>1.03 else 'andesite' if band<-.95 else 'stone'
        cells=room_shape(seed);distance=distance_from_edge(cells)
        nearby_entities=[(x-cx,y,z-cz) for x,y,z in entity_positions if abs(x-cx)<=30 and abs(z-cz)<=30 and f-22<=y<=f+34]
        # Le sol est un relief continu à marches d'un bloc, avec vallée profonde.
        floor={p:min(f,f-min(15,d)+round(.9*math.sin(p[0]*.39+p[1]*.21+seed)+.5*math.cos(p[0]*.2-p[1]*.41))) for p,d in distance.items()}
        protected_floors=[(mirror*(x-cx),y,z-cz) for (x,y,z),s in preserved_access.items() if 'stone_brick' in s and (mirror*(x-cx),z-cz) in cells]
        for (x,z) in cells:
            if protected_floors:floor[x,z]=max(floor[x,z],max(y-abs(x-ax)-abs(z-az) for ax,y,az in protected_floors))
        ceiling={}
        for x,z in cells:
            radial=(x/23)**2+(z/20)**2
            ceiling[x,z]=f+max(9,int(24-9*radial+2.2*math.sin(x*.23+seed)+1.5*math.cos(z*.31-seed)))
            # Toujours au moins 15 blocs de terrain conservés sous la base.
            ceiling[x,z]=min(ceiling[x,z],ground-17,surface(reader,cx+mirror*x,cz+z)-12)
            for ex,ey,ez in nearby_entities:
                d=max(abs(mirror*x-ex),abs(z-ez))
                if ey>floor[x,z]+7:ceiling[x,z]=min(ceiling[x,z],ey-7+max(0,d-3)*3)
                elif ey<floor[x,z]:floor[x,z]=max(floor[x,z],ey+6-max(0,d-3)*3)
            ceiling[x,z]=max(ceiling[x,z],floor[x,z]+4)
        expanded=set(cells)
        for x,z in cells:
            for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                for n in (1,2,3):expanded.add((x+dx*n,z+dz*n))
        for x,z in expanded:
            nearest=(x,z) if (x,z) in cells else min(cells,key=lambda p:abs(p[0]-x)+abs(p[1]-z))
            top=min(ceiling[nearest]+3,surface(reader,cx+mirror*x,cz+z)-9);bottom=floor[nearest]-3
            for y in range(bottom,top+1):put(at(x,y,z),rock(x,y,z))
        # L'ancien décor est retiré, sans retirer les escaliers d'accès.
        for b in old_blocks:
            p=tuple(b['at'])
            if b['kind']!='access':put(p,rock(mirror*(p[0]-cx),p[1],p[2]-cz))
        for x,z in cells:
            angle=math.atan2(z,x)
            for y in range(floor[x,z]+1,ceiling[x,z]+1):
                inset=max(0,round(1.1+1.1*math.sin((y-f)*.25+angle*2+seed)+.6*math.cos((y-f)*.43+angle*3)))
                if distance[x,z]>=inset:put(at(x,y,z),'cave_air','room')
        # Pont rocheux asymétrique, avec des rebords visibles, sans minerais bonus.
        bridge=[]
        for x in range(-19,20):
            z=-3+round(2.6*math.sin(x*.12+seed*.4));y=f-3+round(1.3*math.sin(x*.13))
            if (x,z) not in cells:continue
            width=3+int(math.sin(x*.3+seed)>0.65)
            thickness=2+int(4*(abs(x)/19)**2)
            for dz in range(-1,width-1):
                p=at(x,y,z+dz)
                for below in range(thickness):put(at(x,y-below,z+dz),rock(x,y-below,z+dz),'bridge')
                for dy in (1,2,3):put(at(x,y+dy,z+dz),'cave_air','bridge')
                bridge.append(p)
            for dz in (-2,width-1):
                for dy in range(1+int(stable(seed,x//2,0,dz)%5==0)):put(at(x,y+dy,z+dz),rock(x,y+dy,z+dz),'bridge_edge')
        for p,s in list(local.items()):
            if s not in AIR or kinds[p] not in ('room','bridge'):continue
            for dx,dy,dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                for n in (1,2):
                    q=p[0]+dx*n,p[1]+dy*n,p[2]+dz*n
                    if q not in local:put(q,rock(mirror*(q[0]-cx),q[1],q[2]-cz),'seal')
        # Une seule cascade par équipe, bassin peu profond bordé de roche.
        wx,wz=-12,6;bottom=floor.get((wx,wz),f-5);top=min(ceiling.get((wx,wz),f+15)-2,f+16)
        for dx in range(-2,3):
            for dz in range(-2,3):
                for dy in (-2,-1):put(at(wx+dx,bottom+dy,wz+dz),'stone','basin')
                put(at(wx+dx,bottom,wz+dz),'stone' if max(abs(dx),abs(dz))==2 else 'minecraft:water[level=0]','basin')
        for y in range(bottom+1,top+1):
            for dx,dz in ((-1,0),(0,-1),(0,1)):
                put(at(wx+dx,y,wz+dz),rock(wx+dx,y,wz+dz),'water_backwall')
            put(at(wx,y,wz),'waterfall','waterfall')
        put(at(wx,top,wz),'minecraft:water[level=0]','waterfall')
        # Rétablissement exact des marches et du passage 2×3 existants.
        for p,s in preserved_access.items():put(p,s,'preserved_access')
        protected_entity_cells=set()
        for ex,ey,ez in nearby_entities:
            for dx in range(-2,3):
                for dz in range(-2,3):
                    for dy in range(-1,4):
                        p=cx+ex+dx,ey+dy,cz+ez+dz
                        if p in local:put(p,text_state(reader,p),'preserved_entity');protected_entity_cells.add(p)
        # Même dotation lumineuse pour chaque équipe, sans piliers décoratifs.
        lights=[]
        light_places=[]
        for x,z in cells:
            for dy in (2,4,7):
                p=at(x,floor[x,z]+dy,z)
                if p in preserved_access or p in protected_entity_cells or local.get(p) not in AIR:continue
                for dx,dz,face in ((1,0,'east'),(-1,0,'west'),(0,1,'south'),(0,-1,'north')):
                    neighbor=p[0]+dx,p[1],p[2]+dz
                    if kinds.get(neighbor) in ('rock','seal'):
                        light_places.append((p,face));break
        for p,face in sorted(light_places,key=lambda item:stable(seed,*item[0]))[:24]:put(p,'glow_lichen['+face+'=true]','light');lights.append(p)
        if len(lights)!=24:raise RuntimeError('Dotation lumineuse incomplète')
        start=tuple(old['entrance']);walking=walkable(local);reach=reachable(walking,start)
        if start not in reach:raise RuntimeError('Accès de surface non raccordé : '+team)
        # Minerais disposés dans le sol accessible, tous à la même dotation.
        candidates=[p for p,s in local.items() if kinds[p]=='rock' and (p[0],p[1]+1,p[2]) in reach and p not in preserved_access and p not in protected_entity_cells]
        candidates.sort(key=lambda p:stable(seed,*p))
        budget=[ore for ore,n in ORES.items() for _ in range(n)]
        if len(candidates)<len(budget):raise RuntimeError('Sol accessible insuffisant pour minerais : '+team)
        for p,ore in zip(candidates,budget):put(p,ore,'resource')
        # Contrôle des enveloppes, structures, fluides et inventaires avant édition.
        modifications=[]
        for p,s in sorted(local.items()):
            x,y,z=p
            if abs(x-cx)>30 or abs(z-cz)>30:raise RuntimeError('Enveloppe hors marge de territoire')
            if p in technical or abs(x-cx)<=8 and abs(z-cz)<=8 and y>=ground-12:raise RuntimeError('Collision technique')
            before=text_state(reader,p)
            if before==s:continue
            if y>=surface(reader,x,z)-8:raise RuntimeError('Modification trop proche du paysage de surface')
            old_name=before.partition('[')[0].removeprefix('minecraft:')
            if old_name not in NATURAL|{'infested_stone','infested_deepslate','polished_basalt','blackstone','red_terracotta','amethyst_block','blue_terracotta','yellow_terracotta','sea_lantern','azalea_leaves','stone_bricks','stone_brick_stairs'}:collision.append({'team':team,'at':list(p),'type':old_name,'reason':'matériau source non reconnu'})
            if p in all_edits:raise RuntimeError('Chantiers superposés')
            edit={'at':list(p),'before':before,'after':s,'team':team,'kind':kinds[p]};all_edits[p]=edit;modifications.append(edit)
        actual_resources=Counter(s.partition('[')[0].removeprefix('minecraft:') for s in local.values() if s.partition('[')[0].removeprefix('minecraft:') in ORES)
        if actual_resources!=Counter(ORES):raise RuntimeError('Budget de minerais différent')
        if any((p[0],p[1]+1,p[2]) not in reach for p,s in local.items() if kinds[p]=='resource'):raise RuntimeError('Minerai inaccessible')
        # Toute cavité ajoutée est entourée de la coque pleine, sauf l'accès conservé.
        leaks=[]
        for p,s in local.items():
            if kinds[p]!='room' or s not in AIR:continue
            for dx,dy,dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                q=p[0]+dx,p[1]+dy,p[2]+dz
                if q not in local:leaks.append(list(q))
        if leaks:raise RuntimeError('Coque de caverne ouverte')
        metrics.append({'team':team,'sourceEntrance':list(start),'entrancePreserved':all(text_state(reader,p)==local[p] for p in preserved_access),
            'sourcePlannedAirBlocks':old['plannedAirBlocks'],'airBlocks':sum(s in AIR for s in local.values()),'reachableFloorCells':len(reach),
            'reachableLowestY':min(p[1] for p in reach),'maxInteriorHeight':max(ceiling[p]-floor[p] for p in cells),'resources':dict(actual_resources),
            'waterfalls':1,'lavaBlocks':0,'bridgeBlocks':len(bridge),'lightInclusions':len(lights),'modifiedBlocks':len(modifications),
            'bridgeStandingCellsReachable':sum((x,y+1,z) in reach for x,y,z in bridge),
            'existingEntitiesAvoided':len(nearby_entities),'entityNeighborhoodCellsPreserved':len(protected_entity_cells),
            'bbox':[[min(p[i] for p in local) for i in range(3)],[max(p[i] for p in local) for i in range(3)]],
            'minimumTerritoryMargin':40-max(max(abs(x-cx),abs(z-cz)) for x,y,z in local),'visuallyInspected':False})
    for chunk in reader.chunks.values():
        for tile in chunk.get('block_entities',[]):
            if (tile.get('x'),tile.get('y'),tile.get('z')) in all_edits:collision.append({'reason':'block entity dans le chantier'})
    check_entity_collisions(root,all_edits,collision)
    if collision:raise RuntimeError('Collisions détectées : '+json.dumps(collision[:3]))
    return {'schema':1,'variant':VARIANT,'scope':'four_caverns_user_clarification','blocks':[all_edits[p] for p in sorted(all_edits)],'caverns':metrics,
        'chunks':[list(p) for p in sorted({(x//16,z//16) for x,y,z in all_edits})],'collisions':collision,'passed':True,'visualValidation':False}
