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

def verify_archive_restorations(spec,reader,defaults,original_points):
    """Contrôle supplémentaire strict ; l'emprise historique reste obligatoire."""
    if not isinstance(spec,dict) or spec.get('schema')!=1 or spec.get('kind')!='shaft-column-33' or spec.get('sourceArchiveSha256')!=SOURCE:
        raise RuntimeError('Restauration complémentaire : source ou schéma non approuvé')
    cells=spec.get('cells',[])
    if not isinstance(cells,list) or len(cells)!=33:raise RuntimeError('Restauration complémentaire : 33 cellules requises')
    points=[]
    for cell in cells:
        if not isinstance(cell,dict) or set(cell)!={'at','state'}:raise RuntimeError('Cellule complémentaire invalide')
        at=cell['at'];value=cell['state']
        if not isinstance(at,list) or len(at)!=3 or any(type(v) is not int for v in at) or not -64<=at[1]<320:
            raise RuntimeError('Coordonnée complémentaire invalide')
        if not isinstance(value,dict) or not isinstance(value.get('Name'),str) or value!=normalized(value,defaults):
            raise RuntimeError('État complémentaire incomplet ou invalide')
        points.append(at)
    if len({tuple(p) for p in points})!=33 or len({(p[0],p[2]) for p in points})!=1 or sorted(p[1] for p in points)!=list(range(min(p[1] for p in points),max(p[1] for p in points)+1)):
        raise RuntimeError('Colonne complémentaire dupliquée ou discontinue')
    old={tuple(p) for p in original_points}
    if sum(tuple(p) not in old for p in points)!=31:raise RuntimeError('Emprise complémentaire différente : 31 nouvelles cellules requises')
    expected=hashlib.sha256(json.dumps([[*c['at'],c['state']] for c in cells],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if expected!=spec.get('blockStatesSha256') or fingerprint(reader,points,defaults)!=expected:
        raise RuntimeError('Restauration complémentaire différente du terrain archivé')
    return {'additionalArchiveRestorationsChecked':33,'uniqueNaturalTerrainBlocksChecked':len(old|{tuple(p) for p in points}),'preservedTerrainExceptions':0}

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
    extra={}
    meta=root/'map-underground-restoration.json'
    required=meta.is_file() and json.loads(meta.read_text(encoding='utf-8')).get('additionalArchiveRestorationsRequired') is True
    if required and 'archiveRestorations' not in spec:raise RuntimeError('Contrôle complémentaire obligatoire absent')
    if 'archiveRestorations' in spec:extra=verify_archive_restorations(spec['archiveRestorations'],reader,defaults,points)
    return {'undergroundMode':'vanilla-restored','naturalTerrainBlocksChecked':len(points),'naturalSourceArchiveSha256':SOURCE,**extra}
