"""Lecture NBT/Anvil portable, strictement en lecture seule."""
import gzip
import io
import struct
import zlib

def nbt(data):
    stream=io.BytesIO(data)
    def number(fmt):
        size=struct.calcsize(fmt);value=stream.read(size)
        if len(value)!=size:raise ValueError('NBT tronqué.')
        return struct.unpack('>'+fmt,value)[0]
    def string():return stream.read(number('H')).decode('utf-8')
    def tag(kind):
        if kind in (1,2,3,4,5,6):return number({1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[kind])
        if kind==7:return stream.read(number('i'))
        if kind==8:return string()
        if kind==9:
            item,size=number('b'),number('i');return [tag(item) for _ in range(size)]
        if kind==10:
            result={}
            while (item:=number('b'))!=0:
                name=string();result[name]=tag(item)
            return result
        if kind in (11,12):return [number('i' if kind==11 else 'q') for _ in range(number('i'))]
        raise ValueError('Type NBT non reconnu : '+str(kind))
    kind=number('b');string();return tag(kind)


def normalized_state(value):
    """Palettes 26.2 (Name/Properties) et 26.3 (ID abrégé ou id/properties).

    Les listes NBT hétérogènes enveloppent leurs chaînes dans une clé vide.
    """
    if isinstance(value, str): return {'Name': value}
    if '' in value: return normalized_state(value[''])
    name = value.get('Name', value.get('id'))
    if not isinstance(name, str): raise ValueError('Entrée de palette inconnue.')
    result = {'Name': name}
    properties = value.get('Properties', value.get('properties', {}))
    if properties: result['Properties'] = properties
    return result


class Reader:
    def __init__(self,root):self.root=root;self.chunks={}
    def chunk(self,cx,cz):
        key=cx,cz
        if key in self.chunks:return self.chunks[key]
        path=self.root/'world/dimensions/minecraft/overworld/region'/f'r.{cx//32}.{cz//32}.mca'
        with path.open('rb') as stream:
            stream.seek(((cx%32)+(cz%32)*32)*4);offset=int.from_bytes(stream.read(3),'big');stream.read(1)
            if not offset:raise ValueError('Chunk source absent.')
            stream.seek(offset*4096);size=int.from_bytes(stream.read(4),'big');kind=stream.read(1)[0];data=stream.read(size-1)
        if kind==2:data=zlib.decompress(data)
        elif kind==1:data=gzip.decompress(data)
        elif kind!=3:raise ValueError('Compression de région non prise en charge : '+str(kind))
        result=nbt(data);self.chunks[key]=result;return result
    def block(self,x,y,z):
        chunk=self.chunk(x//16,z//16)
        section=next((s for s in chunk['sections'] if s['Y']==y//16),None)
        if not section or 'block_states' not in section:return 'minecraft:air'
        states=section['block_states'];palette=states['palette']
        if len(palette)==1:return normalized_state(palette[0])['Name']
        bits=max(4,(len(palette)-1).bit_length());per=64//bits;index=(y%16)*256+(z%16)*16+(x%16)
        value=((states['data'][index//per]&((1<<64)-1))>>((index%per)*bits))&((1<<bits)-1)
        return normalized_state(palette[value])['Name']
