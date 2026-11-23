"""Charger le terrain restauré sur une seconde copie Paper, strictement loopback."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import server
from natural_caverns_rework import inventory,write

def run(work):
    candidate=work/'candidate';root=work/'vanilla-paper-validation';tools=work/'vanilla-probe-tools'
    if root.exists() or tools.exists():raise RuntimeError('Copie de validation existante, conserver les preuves')
    before=inventory(candidate)
    with server.maintenance(candidate):shutil.copytree(candidate,root,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    tools.mkdir();classes=tools/'classes';classes.mkdir();java=server.java_path()
    api=server.ROOT/'.cache/m2/io/papermc/paper/paper-api/26.3.build.244-stable/paper-api-26.3.build.244-stable.jar'
    cp=[api,*root.joinpath('libraries').rglob('*.jar'),*root.joinpath('plugins').glob('*.jar'),*server.ROOT.joinpath('.cache/m2/org/jetbrains/annotations').rglob('*.jar')]
    args=['--release','25','-encoding','UTF-8','-cp',';'.join(p.as_posix() for p in cp),'-d',classes.as_posix(),(server.ROOT/'tests/VanillaUndergroundProbe.java').as_posix()]
    argfile=tools/'javac.args';argfile.write_text('\n'.join('"'+s.replace('"','\\"')+'"' for s in args),encoding='utf-8')
    result=subprocess.run([str(java.with_name('javac.exe')),'@'+str(argfile)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (tools/'compilation-private.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Compilation de la sonde impossible')
    shutil.copy2(server.ROOT/'tests/vanilla-underground-probe-plugin.yml',classes/'plugin.yml');jar=tools/'FKVanillaUndergroundProbe.jar'
    subprocess.run([str(java.with_name('jar.exe')),'--create','--file',str(jar),'-C',str(classes),'.'],check=True,capture_output=True);shutil.copy2(jar,root/'plugins/FKVanillaUndergroundProbe.jar')
    props=root/'server.properties';props.write_text(re.sub(r'(?m)^query.port=.*$','query.port=25630',props.read_text()),encoding='utf-8')
    plan=work/'restoration-plan-private.json';logfile=work/'vanilla-paper-private.log'
    cmd=[str(java),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-Dfk.vanilla.probe=true','-Dfk.vanilla.plan='+str(plan),'-Dfk.vanilla.plan.sha256='+server.digest(plan),'-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25630']
    with server.maintenance(root,check_worlds=False),logfile.open('w',encoding='utf-8') as log:
        p=subprocess.Popen(cmd,cwd=root,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,creationflags=subprocess.CREATE_NO_WINDOW);start=time.monotonic()
        while p.poll() is None:
            if time.monotonic()-start>180:p.communicate('stop\n',timeout=60);raise RuntimeError('Validation Paper expirée')
            print(json.dumps({'stage':'vanilla_paper_validation','elapsedSeconds':round(time.monotonic()-start)}),flush=True);time.sleep(5)
    text=logfile.read_text(encoding='utf-8',errors='replace');errors=re.findall(r'\b(ERROR|SEVERE)\b',text)
    if p.returncode or errors or 'VANILLA UNDERGROUND PAPER SUCCESS' not in text:raise RuntimeError('Validation Paper interrompue ; journal conservé')
    result=json.loads((root/'vanilla-paper-result.json').read_text(encoding='utf-8'));result.update({'exitCode':p.returncode,'errors':len(errors),'warnings':len(re.findall(r'\bWARN\b',text)),'candidateUnchanged':inventory(candidate)==before,'queryLoopback':'Query running on 127.0.0.1:25630' in text})
    if not result['candidateUnchanged'] or not result['queryLoopback']:raise RuntimeError('Conservation ou isolation non vérifiée')
    write(work/'vanilla-paper-validation-result.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.work.resolve()),ensure_ascii=False))
