"""Lecture seule des palettes Anvil pour consigner les écarts déjà présents dans les monuments."""
import gzip
import io
import json
from pathlib import Path
import struct
import zlib
from server import ROOT, maintenance, server_dir, digest


from map_reader import nbt, normalized_state, Reader


def main():
    source=server_dir('map-v2');reader=Reader(source);differences=[]
    with maintenance(source):
        built=json.loads((source/'map-v2-construction.json').read_text(encoding='utf-8'))
        for monument in built['monuments']:
            plan=json.loads((ROOT/'maps/v2/structures'/f'{monument["id"]}.json').read_text(encoding='utf-8'))
            for dx,dy,dz,expected in plan['blocks']:
                x,y,z=monument['x']+dx,monument['y']+dy,monument['z']+dz
                actual=reader.block(x,y,z);expected=expected.split('[')[0]
                if actual!=expected:differences.append({'monument':monument['id'],'x':x,'y':y,'z':z,'plan':expected,'source':actual})
    directory=ROOT/'maps/v2-corrections';directory.mkdir(exist_ok=True)
    baseline=json.loads((ROOT/'.cache/v2-fixes-baseline.json').read_text(encoding='utf-8'))
    report={'source':'runtime/map-v2','sourceBackupSha256':baseline['sha256'],'differences':differences,
            'note':'Lecture seule du monde source après inspection utilisateur ; aucune réparation ni modification du monde.'}
    (directory/'preexisting-differences.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
