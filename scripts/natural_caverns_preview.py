"""Aperçus géométriques PNG des blocs réels ; éclairage illustratif, aucun client Minecraft."""
import argparse
import json
import math
from pathlib import Path
import struct
import zlib
from map_reader import Reader

COLORS={'stone':(111,111,108),'deepslate':(63,66,70),'tuff':(105,110,95),'andesite':(128,127,123),
    'water':(35,99,171),'glowstone':(224,191,119),'sea_lantern':(180,219,214),'calcite':(209,207,193),
    'amethyst_block':(125,93,165),'blackstone':(49,43,52),'polished_basalt':(76,75,78),'moss_block':(76,108,47),
    'rooted_dirt':(124,93,64),'dirt':(126,92,67),'red_terracotta':(154,70,54),'blue_terracotta':(77,62,104),'yellow_terracotta':(186,133,45),
    'coal_ore':(73,75,73),'iron_ore':(151,131,113),'copper_ore':(123,136,115),'redstone_ore':(147,84,81),'lapis_ore':(75,102,149),'gold_ore':(157,147,82),'diamond_ore':(80,165,163)}
def png(path,w,h,data):
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    rows=b''.join(b'\0'+data[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,6))+chunk(b'IEND',b''))

def render(root,cave,output,before=False,w=480,h=300):
    reader=Reader(root);team=cave['team'];mirror=-1 if team in ('Verte','Jaune') else 1
    source=json.loads((root/'map-v21-caverns.json').read_text())['caverns'];old=next(c for c in source if c['team']==team)
    cx,_,cz=old['center'];floor=old['floorY'];minx,maxx=cx-31,cx+31;miny,maxy=floor-23,floor+34;minz,maxz=cz-33,cz+32
    sx=maxx-minx+1;sy=maxy-miny+1;sz=maxz-minz+1
    grid=bytearray(sx*sy*sz);names=['air'];mapping={'air':0,'cave_air':0,'void_air':0}
    for y in range(miny,maxy+1):
        for z in range(minz,maxz+1):
            for x in range(minx,maxx+1):
                name=reader.block(x,y,z).removeprefix('minecraft:')
                if name=='glow_lichen':name='air'
                if name not in mapping:mapping[name]=len(names);names.append(name)
                grid[((y-miny)*sz+z-minz)*sx+x-minx]=mapping[name]
    colors=[COLORS.get(name,(101,102,98)) for name in names]
    water=mapping.get('water',-1);emissive={mapping.get('glowstone',-2),mapping.get('sea_lantern',-2)}
    def value(x,y,z):
        if minx<=x<=maxx and miny<=y<=maxy and minz<=z<=maxz:return grid[((y-miny)*sz+z-minz)*sx+x-minx]
        return -1
    camera=(cx+mirror*(7 if before else 11)+.5,floor+(3 if before else 8)+.5,cz+(7 if before else 12)+.5)
    if value(*map(math.floor,camera))!=0:raise RuntimeError('Caméra hors air : '+team)
    target=(cx-mirror*6,floor+2,cz-7);forward=[target[i]-camera[i] for i in range(3)]
    n=math.sqrt(sum(x*x for x in forward));forward=[x/n for x in forward]
    right=[-forward[2],0,forward[0]];n=math.hypot(right[0],right[2]);right=[x/n for x in right]
    up=[right[1]*forward[2]-right[2]*forward[1],right[2]*forward[0]-right[0]*forward[2],right[0]*forward[1]-right[1]*forward[0]]
    image=bytearray(w*h*3);scale=math.tan(math.radians(35));aspect=w/h
    for py in range(h):
        v=(1-2*(py+.5)/h)*scale
        for px in range(w):
            u=(2*(px+.5)/w-1)*aspect*scale
            d=[forward[i]+right[i]*u+up[i]*v for i in range(3)];length=math.sqrt(sum(x*x for x in d));d=[x/length for x in d]
            cell=list(map(math.floor,camera));step=[1 if a>0 else -1 for a in d];delta=[abs(1/a) if a else 1e30 for a in d]
            tmax=[((cell[i]+1-camera[i]) if step[i]>0 else (camera[i]-cell[i]))*delta[i] for i in range(3)]
            t=0;axis=1;tint=False;color=(16,20,24)
            for _ in range(180):
                material=value(*cell)
                if material==-1:break
                if material==water:tint=True
                elif material:
                    base=colors[material];x,y,z=cell
                    hit=[camera[i]+t*d[i] for i in range(3)]
                    a,b=(hit[0],hit[2]) if axis==1 else (hit[0],hit[1]) if axis==2 else (hit[2],hit[1])
                    tx,tz=math.floor(a*16),math.floor(b*16);noise=((tx*734287+tz*912271+y*6419+x*813+z*71)&255)/255
                    shade=(.78 if axis==1 else .63 if axis==0 else .52)*(.76+.34*noise)
                    shade*=.42+.58*math.exp(-t/52)
                    if material in emissive:shade=1
                    color=tuple(max(0,min(255,int(c*shade))) for c in base)
                    if tint:color=tuple(int(color[i]*.43+COLORS['water'][i]*.57) for i in range(3))
                    break
                axis=min(range(3),key=lambda i:tmax[i]);t=tmax[axis];tmax[axis]+=delta[axis];cell[axis]+=step[axis]
                if t>100:break
            i=(py*w+px)*3;image[i:i+3]=bytes(color)
    png(output,w,h,image)

def run(work,source):
    result=json.loads((work/'result-private.json').read_text());folder=work/'previews';folder.mkdir(exist_ok=False)
    images=[]
    for cave in result['caverns']:
        name=cave['team'].lower()+'.png';render(work/'candidate',cave,folder/name);images.append(name)
        print(json.dumps({'stage':'geometry_preview','team':cave['team']}),flush=True)
    render(source,result['caverns'][1],folder/'bleue-avant.png',before=True)
    html='<!doctype html><meta charset="utf-8"><title>Cavernes naturelles — aperçu local</title><style>body{background:#121519;color:#eee;font:17px system-ui;max-width:1100px;margin:30px auto}img{width:100%;image-rendering:pixelated;border-radius:8px}section{max-width:980px;margin:30px 0}p{line-height:1.6}</style><h1>'+result['variant']+'</h1><p>Aperçus calculés depuis les blocs réels de la copie locale. Éclairage et textures schématiques ; ce ne sont pas des captures Minecraft et ils ne valident pas la jouabilité.</p>'
    for team,name in zip(('Rouge','Bleue','Verte','Jaune','Bleue avant refonte'),images+['bleue-avant.png']):html+='<section><h2>'+team+'</h2><img src="'+name+'"></section>'
    (folder/'index.html').write_text(html,encoding='utf-8');return folder

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(run(a.work,a.source))
