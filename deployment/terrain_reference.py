"""Référence V2.2 : vrais états de terrain, sans exiger de cavernes construites."""
import hashlib
import json
from map_reader import normalized_state

SOURCE='8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de'
def state(reader,x,y,z):
    chunk=reader.chunk(x//16,z//16);section=next((s for s in chunk.get('sections',[]) if s['Y']==y//16),None)
    if not section or 'block_states' not in section:return {'Name':'minecraft:air'}
    states=section['block_states'];palette=states['palette'];index=0
    if len(palette)>1:
        bits=max(4,(len(palette)-1).bit_length());per=64//bits;i=(y%16)*256+(z%16)*16+x%16
        index=((states['data'][i//per]&((1<<64)-1))>>((i%per)*bits))&((1<<bits)-1)
    return normalized_state(palette[index])

def normalized(value,defaults):
    name=value['Name'];base=defaults.get(name,name).partition('[')[2].removesuffix(']')
    props=dict(piece.split('=',1) for piece in base.split(',') if piece);props.update(value.get('Properties',{}))
    return {'Name':name,'Properties':props}

def fingerprint(reader,points,defaults):
    values=[[x,y,z,normalized(state(reader,x,y,z),defaults)] for x,y,z in points]
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def verify(root,data,reader):
    spec=data.get('underground') or {}
    if spec.get('mode')!='vanilla-restored' or spec.get('sourceArchiveSha256')!=SOURCE:raise RuntimeError('Référence du terrain naturel non approuvée')
    if data.get('caverns'):raise RuntimeError('La référence naturelle ne doit pas déclarer de cavernes artificielles')
    points=spec.get('checkPoints',[])
    if len(points)!=37128 or len({tuple(p) for p in points})!=len(points):raise RuntimeError('Empreinte de restauration naturelle incomplète')
    path=root/'maintenance/block-defaults-26.3.json'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=spec.get('blockDefaultsSha256'):raise RuntimeError('Registre des états Paper modifié')
    defaults=json.loads(path.read_text(encoding='utf-8'))
    if fingerprint(reader,points,defaults)!=spec.get('blockStatesSha256'):raise RuntimeError('Terrain naturel initial différent ou miné')
    return {'undergroundMode':'vanilla-restored','naturalTerrainBlocksChecked':len(points),'naturalSourceArchiveSha256':SOURCE}
