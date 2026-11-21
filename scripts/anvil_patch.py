"""Édition Anvil hors ligne : NBT typé et conservation des chunks non ciblés."""
from dataclasses import dataclass
import io
import math
import struct
import zlib
from map_reader import normalized_state

@dataclass
class Tag:
    kind:int
    value:object
    raw:bytes|None=None

def load(data):
    f=io.BytesIO(data)
    def take(n):
        if n<0 or n>128*1024**2:raise ValueError('Taille NBT invalide')
        b=f.read(n)
        if len(b)!=n:raise ValueError('NBT tronqué')
        return b
    def number(fmt):return struct.unpack('>'+fmt,take(struct.calcsize(fmt)))[0]
    def string():return take(number('H'))
    def node(k,depth=0):
        if depth>128:raise ValueError('NBT trop profond')
        start=f.tell()
        if k in (1,2,3,4,5,6):v=number({1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[k])
        elif k==7:v=take(number('i'))
        elif k==8:v=string()
        elif k==9:
            subtype=number('B');n=number('i')
            if n<0 or n>1000000 or (subtype==0 and n):raise ValueError('Liste NBT invalide')
            v=(subtype,[node(subtype,depth+1) for _ in range(n)])
        elif k==10:
            v={}
            while (sub:=number('B'))!=0:
                name=string().decode('utf-8',errors='surrogateescape')
                if name in v:raise ValueError('Clé NBT dupliquée')
                v[name]=node(sub,depth+1)
        elif k in (11,12):
            n=number('i')
            if n<0 or n>1000000:raise ValueError('Tableau NBT invalide')
            v=[number('i' if k==11 else 'q') for _ in range(n)]
        else:raise ValueError('Type NBT invalide')
        end=f.tell();raw=data[start:end] if k not in (9,10) else None
        return Tag(k,v,raw)
    kind=number('B');name=string();root=node(kind)
    if f.read(1):raise ValueError('Données après le NBT')
    return name,root

def dump(name,root):
    def string(b):return struct.pack('>H',len(b))+b
    def encode(t):
        if t.raw is not None:return t.raw
        k,v=t.kind,t.value
        if k in (1,2,3,4,5,6):return struct.pack('>'+{1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[k],v)
        if k==7:return struct.pack('>i',len(v))+v
        if k==8:return string(v)
        if k==9:return bytes([v[0]])+struct.pack('>i',len(v[1]))+b''.join(encode(x) for x in v[1])
        if k==10:return b''.join(bytes([x.kind])+string(n.encode('utf-8',errors='surrogateescape'))+encode(x) for n,x in v.items())+b'\0'
        if k in (11,12):return struct.pack('>i',len(v))+b''.join(struct.pack('>i' if k==11 else '>q',x) for x in v)
        raise ValueError('Type NBT invalide')
    return bytes([root.kind])+string(name)+encode(root)

def plain(t):
    if t.kind==8:return t.value.decode('utf-8',errors='surrogateescape')
    if t.kind==9:return [plain(x) for x in t.value[1]]
    if t.kind==10:return {k:plain(v) for k,v in t.value.items()}
    return t.value

def text(v):return Tag(8,v.encode())
def state_key(v):
    n=normalized_state(v)
    return n['Name'],tuple(sorted(n.get('Properties',{}).items()))
def state_tag(name,props):
    if not props:return Tag(10,{'':text(name)})
    return Tag(10,{'id':text(name),'properties':Tag(10,{k:text(v) for k,v in props})})
def parse_state(s):
    name,_,props=s.partition('[')
    return name,tuple(sorted(tuple(piece.split('=',1)) for piece in props.removesuffix(']').split(',') if piece))

def indices(blocks):
    palette=blocks['palette'].value[1]
    if not palette:raise ValueError('Palette vide')
    if len(palette)==1:return [0]*4096
    bits=max(4,(len(palette)-1).bit_length());per=64//bits;data=blocks['data'].value
    if len(data)!=math.ceil(4096/per):raise ValueError('Longueur de palette invalide')
    result=[((data[i//per]&((1<<64)-1))>>((i%per)*bits))&((1<<bits)-1) for i in range(4096)]
    if any(v>=len(palette) for v in result):raise ValueError('Index de palette invalide')
    return result

def edit_chunk(data,edits):
    name,root=load(data)
    if dump(name,root)!=data:raise ValueError('NBT non conservé par aller-retour')
    sections={s.value['Y'].value:s for s in root.value['sections'].value[1]}
    touched=[]
    for sy,changes in edits.items():
        if sy not in sections:raise ValueError('Section absente ; génération refusée')
        section=sections[sy].value;states=section.get('block_states')
        if states is None:states=Tag(10,{'palette':Tag(9,(8,[text('minecraft:air')]))});section['block_states']=states
        content=states.value;values=indices(content)
        keys=[state_key(plain(t)) for t in content['palette'].value[1]]
        # Format mixte 26.3 : chaînes enveloppées dans "", états avec id/properties.
        for cell,state in changes.items():
            key=parse_state(state)
            if key not in keys:keys.append(key)
            values[cell]=keys.index(key)
        content['palette']=Tag(9,(10,[state_tag(*key) for key in keys]))
        bits=max(4,(len(keys)-1).bit_length());per=64//bits;packed=[0]*math.ceil(4096/per)
        for i,value in enumerate(values):packed[i//per]|=value<<((i%per)*bits)
        content['data']=Tag(12,[v if v<(1<<63) else v-(1<<64) for v in packed])
        touched.append(sy)
    # L'éclairage précédent devient invalide ; Paper doit le recalculer.
    root.value['isLightOn']=Tag(1,0);root.value.pop('starlight.light_version',None)
    for section in sections.values():
        for key in ('BlockLight','SkyLight','starlight.skylight_state','starlight.blocklight_state'):section.value.pop(key,None)
    return dump(name,root),touched

def region_entries(data):
    if len(data)<8192 or len(data)%4096:raise ValueError('Région tronquée')
    used=set();out={}
    for i in range(1024):
        at=int.from_bytes(data[i*4:i*4+3],'big');sectors=data[i*4+3]
        if not at:
            if sectors:raise ValueError('Adresse Anvil invalide')
            continue
        if at<2 or not sectors or (at+sectors)*4096>len(data):raise ValueError('Secteurs Anvil invalides')
        if used.intersection(range(at,at+sectors)):raise ValueError('Secteurs partagés')
        used.update(range(at,at+sectors));start=at*4096;n=int.from_bytes(data[start:start+4],'big')
        if n<1 or n+4>sectors*4096:raise ValueError('Taille de chunk invalide')
        codec=data[start+4]
        if codec not in (1,2,3):raise ValueError('Chunk externe ou compression non prise en charge')
        out[i]=(codec,data[start+5:start+4+n])
    return out

def patch_region(data,edits):
    import gzip
    entries=region_entries(data);out=bytearray(data);proof=[]
    for index,changes in sorted(edits.items()):
        if index not in entries:raise ValueError('Chunk absent ; génération refusée')
        codec,compressed=entries[index]
        raw=zlib.decompress(compressed) if codec==2 else gzip.decompress(compressed) if codec==1 else compressed
        modified,sections=edit_chunk(raw,changes);payload=zlib.compress(modified,6)
        record=(len(payload)+1).to_bytes(4,'big')+b'\x02'+payload
        sectors=math.ceil(len(record)/4096);offset=len(out)//4096
        if sectors>255 or offset>=1<<24:raise ValueError('Chunk trop volumineux')
        out[index*4:index*4+4]=offset.to_bytes(3,'big')+bytes([sectors])
        out.extend(record+b'\0'*(sectors*4096-len(record)));proof.append({'index':index,'sections':sections})
    result=bytes(out);region_entries(result)
    # Le contenu et les horodatages de tous les chunks non ciblés sont intacts.
    result_entries=region_entries(result)
    if entries.keys()!=result_entries.keys():raise ValueError('Liste des chunks différente')
    if any(entries[i]!=result_entries[i] for i in entries.keys()-edits.keys()):raise ValueError('Chunk hors plan modifié')
    return result,proof
