"""Migration conservative des quatre carrés natifs, sans déplacer un objectif ou un spawn."""
import math
import re

TEAMS=('Rouge','Bleue','Verte','Jaune')


def locate(text,path):
    lines=text.splitlines(keepends=True);start=0;end=len(lines);indent=0;value=None;index=None
    for key in path:
        found=None
        for i in range(start,end):
            match=re.fullmatch(' '*indent+re.escape(key)+r':(?:\s*(.*))?\r?\n?',lines[i])
            if match:found=i;value=(match.group(1) or '').strip();break
        if found is None:return None,None
        index=found;start=found+1;end=next((i for i in range(start,end) if lines[i].strip() and len(lines[i])-len(lines[i].lstrip())<=indent),end);indent+=2
    return index,value


def get(text,*path):return locate(text,path)[1]
def number(text,*path):
    raw=get(text,*path)
    try:value=float(raw)
    except (TypeError,ValueError):raise RuntimeError('Coordonnée absente ou non numérique : '+'.'.join(path))
    if not math.isfinite(value):raise RuntimeError('Coordonnée non finie.')
    return value
def scalar(text,path,value):
    index,_=locate(text,path)
    if index is None:raise RuntimeError('Clé structurante absente : '+'.'.join(path))
    lines=text.splitlines(keepends=True);lines[index]='  '*(len(path)-1)+path[-1]+': '+str(value)+'\n';return ''.join(lines)


def plan(text,radius=40,capture_radius=2.5):
    if get(text,'schema')!='1' or get(text,'vnext','version') not in (None,'1','2'):raise RuntimeError('Schéma de progression incompatible.')
    if radius!=40:raise RuntimeError('Cette migration contrôlée accepte uniquement le rayon 40.')
    result=[];blocked=[]
    for team in TEAMS:
        path=('native','TeamManager',team,'Base');old=number(text,*path,'Radius')
        if old not in (80,40):raise RuntimeError('Rayon existant inattendu : '+team+' ; intervention humaine requise.')
        center={key:number(text,*path,'Center',key) for key in ('X','Y','Z')};world=get(text,*path,'Center','World')
        if world not in ('world',"'world'",'"world"'):raise RuntimeError('Centre de base hors Overworld attendu.')
        for label in ('spawns','objectives'):
            if get(text,label,team) is None:
                if label=='spawns':raise RuntimeError('Spawn absent : '+team)
                continue
            x=number(text,label,team,'x');z=number(text,label,team,'z');target_world=get(text,label,team,'world')
            margin=max(3,math.ceil(capture_radius)) if label=='objectives' else 0
            if target_world not in ('world',"'world'",'"world"') or abs(math.floor(x)-center['X'])+margin>radius or abs(math.floor(z)-center['Z'])+margin>radius:blocked.append({'team':team,'reason':label+' hors du nouveau périmètre, salle et position à vérifier humainement'})
        result.append({'team':team,'oldRadius':int(old),'newRadius':radius,'center':center,'minX':int(center['X'])-radius,'maxX':int(center['X'])+radius,'minZ':int(center['Z'])-radius,'maxZ':int(center['Z'])+radius,'verticalLimit':0,
            'geometricAreaBefore':(2*int(old))**2,'geometricAreaAfter':(2*radius)**2,'blockColumnsBefore':(2*int(old)+1)**2,'blockColumnsAfter':(2*radius+1)**2})
    for i,a in enumerate(result):
        for b in result[i+1:]:
            if a['minX']<=b['maxX'] and b['minX']<=a['maxX'] and a['minZ']<=b['maxZ'] and b['minZ']<=a['maxZ']:raise RuntimeError('Territoires en chevauchement.')
    return {'schema':1,'territories':result,'blocked':blocked,'passed':not blocked,'centralCoordinatesChanged':False,'squareBoundsInclusive':True}


def migrate(text,capture_radius=2.5):
    report=plan(text,capture_radius=capture_radius)
    if not report['passed']:raise RuntimeError('Réduction refusée : '+str(report['blocked']))
    for team in TEAMS:text=scalar(text,('native','TeamManager',team,'Base','Radius'),40)
    return text,report
