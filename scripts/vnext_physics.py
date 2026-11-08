"""Reproduction IA/projectile/santé sur copie Paper 26.3, aucune connexion authentifiée."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import server

ROOT=server.ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--attempt',type=int,required=True);parser.add_argument('--fixed',action='store_true')
    args=parser.parse_args();qa=ROOT/'.cache/vn';kind='fixed' if args.fixed else 'baseline';root=qa/'runtime'/f'pve-{kind}-{args.attempt}'
    base=ROOT/'dist/fallenkingdom-preproduction-26.3.zip'
    assert server.digest(base)=='8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de'
    server.restore(root,base)
    binary=server.PLUGIN if args.fixed else ROOT/'dist/gameplay-update/FKAmis-1.0.0.jar'
    if not args.fixed:assert server.digest(binary)=='83e721d8ac12feefdb590976747f88d6825b3243976c7e9f10b1cc35fac5239d'
    shutil.copy2(binary,root/'plugins/FKAmis-1.0.0.jar');(root/'FKAmis.sha256').write_text(server.digest(binary)+'\n')
    if args.fixed:
        config=root/'plugins/FKAmis/config.yml';config.write_text(re.sub(r'^damage-debug:.*$','damage-debug: true',config.read_text(encoding='utf-8'),flags=re.M)+'\ndamage-debug: true\n',encoding='utf-8')
    shutil.copy2(ROOT/'.cache/FKPvEPhysicsProbe.jar',root/'plugins/FKPvEPhysicsProbe.jar')
    for folder in ('libraries','versions','cache'):
        if (ROOT/'runtime/preproduction-26-3'/folder).exists():shutil.copytree(ROOT/'runtime/preproduction-26-3'/folder,root/folder)
    flags=['-Dfk.physics=true']+(['-Dfk.physics.fixed=true'] if args.fixed else [])
    with server.maintenance(root,check_worlds=False):
        server.validate(root)
        process=subprocess.Popen([str(server.java_path()),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8',*flags,
            '-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25593'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        try:log,_=process.communicate(timeout=600)
        except subprocess.TimeoutExpired:log,_=process.communicate(input='stop\n',timeout=120)
    out=qa/'tests/results';out.mkdir(parents=True,exist_ok=True);(out/f'physics-{kind}-{args.attempt}.log').write_text(log,encoding='utf-8')
    errors=[line for line in log.splitlines() if re.search(r'\b(ERROR|SEVERE)\b',line)]
    result={'passed':process.returncode==0 and 'PHYSICS PROBE SUCCESS' in log and not errors,'kind':kind,'attempt':args.attempt,
        'fkamisSha256':server.digest(binary),'authenticatedClients':0,'errors':errors,
        'cases':[json.loads(line.split('PHYSICS CASE ',1)[1]) for line in log.splitlines() if 'PHYSICS CASE ' in line]}
    (ROOT/f'tests/results/vnext-physics-{kind}.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if not result['passed']:raise RuntimeError('Recette physique incomplète : conserver les traces.')


if __name__=='__main__':main()
