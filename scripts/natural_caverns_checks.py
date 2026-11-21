"""Contrôles complémentaires en lecture seule : confinement et maintenance initiale."""
from collections import deque
import argparse
import json
from pathlib import Path
import sys
import server
from map_reader import Reader
from natural_caverns_rework import write,inventory

PASSABLE={'minecraft:air','minecraft:cave_air','minecraft:void_air','minecraft:water','minecraft:glow_lichen'}
def containment(reader,start,bounds,entrance,limit=180000):
    low,high=bounds;ex,ey,ez=entrance;seen=set();queue=deque([tuple(start)]);gates=set();cache={}
    while queue:
        p=queue.popleft()
        if p in seen:continue
        x,y,z=p
        if abs(x-ex)<=7 and abs(z-ez)<=7 and y>=ey-6:gates.add(p);continue
        if not all(low[i]<=p[i]<=high[i] for i in range(3)):raise RuntimeError('Ouverture souterraine hors enveloppe')
        if p not in cache:cache[p]=reader.block(*p)
        if cache[p] not in PASSABLE:continue
        seen.add(p)
        if len(seen)>limit:raise RuntimeError('Volume de confinement dépassé')
        for dx,dy,dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            q=x+dx,y+dy,z+dz
            if q not in cache:cache[q]=reader.block(*q)
            if cache[q] in PASSABLE and q not in seen:queue.append(q)
    if not gates:raise RuntimeError('Accès de surface absent du volume connecté')
    return {'connectedPassableCells':len(seen),'entranceGateCells':len(gates),'undergroundContained':True}

def run(work):
    candidate=work/'candidate';result=json.loads((work/'result-private.json').read_text());source_metrics=json.loads((candidate/'map-v21-caverns.json').read_text())['caverns']
    before=inventory(candidate);checks=[]
    with server.maintenance(candidate):
        reader=Reader(candidate)
        for cave in result['caverns']:
            old=next(c for c in source_metrics if c['team']==cave['team'])
            proof=containment(reader,old['center'],cave['bbox'],cave['sourceEntrance'])
            checks.append({'team':cave['team'],**proof})
        sys.modules['serverlib']=server;sys.path.insert(0,str(server.ROOT/'deployment'))
        import host_ops,new_match
        host_ops.check(candidate,'v21-minestrator');host_ops.verify(candidate)
        initial=new_match.initial_checks(candidate,candidate/'maintenance/new-match-reference-v2.1-natural.json')
    if inventory(candidate)!=before:raise RuntimeError('Les contrôles ont changé le candidat')
    output={'passed':True,'containment':checks,'hostProfile':'v21-minestrator','deploymentManifestVerified':True,'initialReferenceChecks':initial,'candidateUnchanged':True,'remoteAccessPerformed':False}
    write(work/'additional-checks-private.json',output)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.work),ensure_ascii=False))
