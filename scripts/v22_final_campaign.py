"""Campagne Paper exclusivement locale sur copies privées V2.2, sans accès distant."""
import argparse
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
import server
from natural_caverns_rework import inventory,write
from minestrator_cold_backup import protect_directory


def spec(suite):
    if suite.startswith('features-'):
        size=int(suite.removeprefix('features-'))
        if size not in range(1,5):raise ValueError('Effectif 1..4 uniquement')
        return f'probe-features-{size}','FKFeaturesProbe.jar',['-Dfk.featuresprobe=true',f'-Dfk.featuresprobe.size={size}'],[[f'-Dfk.featuresprobe.phase={n}'] for n in range(3)],'FEATURES PROBE SUCCESS',400
    return {
        'four':('probe-fourplayers','FKFourPlayersProbe.jar',['-Dfk.fourplayers=true'],[[]],'FOUR PLAYERS PROBE SUCCESS',240),
        'next1':('probe-vnext1','FKVNext1Probe.jar',['-Dfk.vnext1=true'],[[],['-Dfk.vnext1.restart=true']],'VNEXT1 PROBE SUCCESS',300),
        'supplies':('map-v2-qa-v22','FKMapV2SupplyProbe.jar',['-Dfk.supplyprobe=true','-Dfk.supplyprobe.reportprefix=v2-fixes-supply'],[[],['-Dfk.supplyprobe.restart=true']],'SUPPLY PROBE SUCCESS',240),
        'physics':('pve-v22','FKPvEPhysicsProbe.jar',['-Dfk.physics=true','-Dfk.physics.fixed=true'],[[]],'PHYSICS PROBE SUCCESS',600),
        'final':('probe-final-v22','FKFinalValidationProbe.jar',['-Dfk.finalprobe=true'],[[],['-Dfk.finalprobe.restart=true']],'FINAL PROBE SUCCESS',240),
        'statistics':('probe-vnext-v22','FKVNextProbe.jar',['-Dfk.vnext=true'],[[f'-Dfk.vnext.phase={n}'] for n in range(3)],'VNEXT PROBE SUCCESS',300),
    }[suite]


def prepare(work,source):
    work=work.resolve();source=source.resolve();parent=(Path.home()/'FKBackups').resolve()
    if not work.is_relative_to(parent) or work==parent or work.is_relative_to(source) or source.is_relative_to(work):raise RuntimeError('Dossier neuf hors dépôt et distinct de la source requis')
    if not source.is_dir() or not (source/'maintenance/new-match-reference-v2.2.json').is_file():raise RuntimeError('Source V2.2 obligatoire')
    expected=json.loads((source.parent/'candidate-files-private.json').read_text(encoding='utf-8'))
    with server.maintenance(source):
        if inventory(source)!=expected:raise RuntimeError('Source V2.2 modifiée : arrêt')
        if not work.exists():
            protect_directory(work);write(work/'source-files-private.json',expected)
        if json.loads((work/'source-files-private.json').read_text(encoding='utf-8'))!=expected:raise RuntimeError('Campagne liée à une autre source')
    (work/'runtime').mkdir(exist_ok=True);(work/'tests/results').mkdir(parents=True,exist_ok=True)
    return expected


def pack_final():
    target=server.ROOT/'.cache/v22-final-probe'
    target.mkdir(exist_ok=True);folder=target/'fr/fkamis';folder.mkdir(parents=True,exist_ok=True)
    for pattern in ('FinalValidationProbe*.class','SyntheticPlayer*.class'):
        files=list((server.ROOT/'plugins-custom/fk-amis/target/test-classes/fr/fkamis').glob(pattern))
        if not files:raise RuntimeError('Compiler les tests Java avant la sonde finale')
        for path in files:shutil.copy2(path,folder/path.name)
    shutil.copy2(server.ROOT/'tests/final-validation-plugin.yml',target/'plugin.yml')
    subprocess.run([str(server.java_path().with_name('jar.exe')),'--create','--file',str(server.ROOT/'.cache/FKFinalValidationProbe.jar'),'-C',str(target),'.'],check=True,capture_output=True)


def run_phase(work,root,suite,phase,flags,success,timeout,port):
    # Réserver un port de test libre ; Query est isolé en UDP et le jeu en TCP.
    for kind in (socket.SOCK_STREAM,socket.SOCK_DGRAM):
        with socket.socket(socket.AF_INET,kind) as sock:sock.bind(('127.0.0.1',port))
    logpath=work/f'{root.name}-phase-{phase}-private.log'
    command=[str(server.java_path()),'-Xms1G','-Xmx3G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8',*flags,'-jar','paper.jar','--nogui','--host','127.0.0.1','--port',str(port)]
    start=time.monotonic();timed_out=False
    with server.maintenance(root,check_worlds=False),logpath.open('x',encoding='utf-8') as log:
        server.validate(root)
        p=subprocess.Popen(command,cwd=root,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            while p.poll() is None:
                if time.monotonic()-start>timeout:
                    timed_out=True;p.communicate('stop\n',timeout=120);break
                print(json.dumps({'suite':suite,'phase':phase,'elapsedSeconds':round(time.monotonic()-start)}),flush=True);time.sleep(5)
        finally:
            if p.poll() is None:
                try:p.communicate('stop\n',timeout=120)
                except subprocess.TimeoutExpired:p.kill();p.wait();timed_out=True
            p.stdin.close()
    text=logpath.read_text(encoding='utf-8',errors='strict');errors=re.findall(r'^.*\b(?:ERROR|SEVERE)\b.*$',text,re.M);warnings=re.findall(r'^.*\bWARN\b.*$',text,re.M)
    result={'suite':suite,'phase':phase,'passed':p.returncode==0 and not timed_out and not errors and success in text,
            'assertions':len(re.findall(r'PROBE PASS ',text)),'exitCode':p.returncode,'timeout':timed_out,'errors':errors,'warnings':warnings,
            'queryLoopback':f'Query running on 127.0.0.1:{port}' in text,'authenticatedClients':0,'elapsedSeconds':round(time.monotonic()-start),'logSha256':server.digest(logpath)}
    result['passed']=result['passed'] and result['queryLoopback']
    write(work/f'{root.name}-phase-{phase}-result.json',result)
    if not result['passed']:raise RuntimeError('Échec critique, journal privé conservé : '+str(logpath))
    return result


def run(work,source,suite,attempt,port):
    expected=prepare(work,source);prefix,jar,flags,phases,success,timeout=spec(suite)
    root=work/'runtime'/f'{prefix}-{attempt}'
    if root.exists():raise RuntimeError('Copie existante conservée ; nouvel identifiant requis')
    with server.maintenance(source):shutil.copytree(source,root,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    if inventory(root)!=expected:raise RuntimeError('Copie non conforme à la source')
    if suite=='final':pack_final()
    shutil.copy2(server.ROOT/'.cache'/jar,root/'plugins'/jar)
    shutil.copy2(server.PLUGIN,root/'plugins/FKAmis-1.0.0.jar');h=server.digest(server.PLUGIN)
    (root/'FKAmis.sha256').write_text(h+'\n',encoding='ascii')
    lock=root/'RUNTIME_LOCK.json';data=json.loads(lock.read_text(encoding='utf-8'));data['sha256']['plugins/FKAmis-1.0.0.jar']=h;write(lock,data)
    (root/'plugins'/jar.removesuffix('.jar')).mkdir(exist_ok=True)
    props=root/'server.properties';props.write_text(re.sub(r'(?m)^query.port=.*$','query.port='+str(port),props.read_text(encoding='utf-8')),encoding='utf-8')
    # Les anciennes sondes d'événements attendent une grâce nulle ; les tests nouveaux utilisent les 5 s réelles.
    if suite.startswith('features-') or suite=='physics':
        config=root/'plugins/FKAmis/config.yml';config.write_text(re.sub(r'(?m)^respawn-protection-seconds:.*$','respawn-protection-seconds: 0',config.read_text(encoding='utf-8')),encoding='utf-8')
    if suite=='statistics':
        for name,note in [('config.yml','\ncustom-vnext-note: conserver\n'),('supplies.yml','\ncustom-vnext-supply: conserver\n'),('state.yml','\ncustom-vnext-state:\n  keep: 42\n')]:
            path=root/'plugins/FKAmis'/name;path.write_text(path.read_text(encoding='utf-8')+note,encoding='utf-8')
    results=[]
    for phase,extra in enumerate(phases):results.append(run_phase(work,root,suite,phase,flags+extra,success,timeout,port))
    unchanged=inventory(source)==expected
    result={'suite':suite,'passed':all(r['passed'] for r in results) and unchanged,'sourceUnchanged':unchanged,'fkamisSha256':h,'phases':results,'clientRenderingVerified':False,'remoteAccessPerformed':False}
    write(work/f'{suite}-result.json',result)
    if not unchanged:raise RuntimeError('Source modifiée pendant la campagne')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--suite',choices=['features-1','features-2','features-3','features-4','four','next1','supplies','physics','final','statistics'],required=True);p.add_argument('--attempt',default='01');p.add_argument('--port',type=int,default=25640);a=p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.attempt) or not 1024<=a.port<=65535:raise ValueError('Identifiant ou port invalide')
    print(json.dumps(run(a.work.resolve(),a.source.resolve(),a.suite,a.attempt,a.port),ensure_ascii=False))
