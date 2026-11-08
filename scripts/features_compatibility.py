"""Refus réels de capacité incompatible, sur copies privées ; state.yml doit rester identique."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import server

ROOT=server.ROOT


def run(attempt):
    source=ROOT/'.cache/gameplay-qa/runtime/probe-features-2-2'
    archive=ROOT/f'.cache/gameplay-qa/capacity-source-{attempt}.zip'
    with server.maintenance(source):server.create_archive(source,archive)
    results=[]
    for name,capacity,prestart,message in [
        ('started',3,False,'Partie déjà commencée'),('prestart',1,True,'inférieur à un effectif enregistré')]:
        # Chemin court : les bibliothèques Paper comprennent un nom Maven très long sous Windows.
        root=ROOT/'.cache'/f'cap-{attempt}-{name}'
        server.restore(root,archive)
        shutil.copy2(server.PLUGIN,root/'plugins/FKAmis-1.0.0.jar')
        (root/'FKAmis.sha256').write_text(server.digest(server.PLUGIN)+'\n',encoding='ascii')
        (root/'plugins/FKFeaturesProbe.jar').unlink(missing_ok=True)
        config=root/'plugins/FKAmis/config.yml';text=config.read_text(encoding='utf-8')
        config.write_text(re.sub(r'^players-per-team:.*$',f'players-per-team: {capacity}',text,flags=re.M),encoding='utf-8')
        state=root/'plugins/FKAmis/state.yml'
        if prestart:
            text=state.read_text(encoding='utf-8')
            text=re.sub(r'^day:.*$','day: 0',text,flags=re.M)
            text=re.sub(r'^started:.*$','started: false',text,flags=re.M)
            text=re.sub(r'^winner:.*$',"winner: ''",text,flags=re.M)
            text=re.sub(r'^eliminated:\n(?:-.*\n)*','eliminated: []\n',text,flags=re.M)
            state.write_text(text,encoding='utf-8')
        before=server.digest(state)
        with server.maintenance(root,check_worlds=False):
            server.validate(root)
            process=subprocess.Popen([str(server.java_path()),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8',
                '-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25592'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            try:log,_=process.communicate(timeout=180)
            except subprocess.TimeoutExpired:log,_=process.communicate(input='stop\n',timeout=120)
        (ROOT/f'.cache/gameplay-qa/tests/results/capacity-refusal-{name}.log').write_text(log,encoding='utf-8')
        ok=message in log and 'FKAmis prêt' not in log and before==server.digest(state)
        results.append({'case':name,'configuredCapacity':capacity,'expectedRefusal':message,'passed':ok,'stateByteIdentical':before==server.digest(state)})
        if not ok:raise RuntimeError('Refus de capacité non conforme : '+name)
    report={'passed':all(r['passed'] for r in results),'checks':results,'fkamisSha256':server.digest(server.PLUGIN),
        'authenticatedPlayers':0,'negativeTestsExpectedStartupRefusal':True}
    (ROOT/'tests/results/gameplay-update-capacity-refusals.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--attempt',type=int,default=1)
    args=parser.parse_args()
    if not 1<=args.attempt<=100:raise ValueError('Tentative 1..100 requise.')
    run(args.attempt)
