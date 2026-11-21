"""Sonde Paper locale sur une seconde copie, sans modification de l'artefact livré."""
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
    work=work.resolve();candidate=work/'candidate';copy=work/'paper-validation';tools=work/'probe-tools'
    if copy.exists() or tools.exists():raise RuntimeError('Copie de test existante : choisir une nouvelle tentative distincte')
    before=inventory(candidate);shutil.copytree(candidate,copy,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    tools.mkdir();classes=tools/'classes';classes.mkdir()
    java=server.java_path();javac=java.with_name('javac.exe');jar=java.with_name('jar.exe')
    api=server.ROOT/'.cache/m2/io/papermc/paper/paper-api/26.3.build.244-stable/paper-api-26.3.build.244-stable.jar'
    cp=';'.join(p.as_posix() for p in [api,*candidate.joinpath('libraries').rglob('*.jar')])
    args=['-encoding','UTF-8','--release','25','-cp',cp,'-d',classes.as_posix(),(server.ROOT/'tests/NaturalCavernsProbe.java').as_posix()]
    argfile=tools/'javac.args';argfile.write_text('\n'.join('"'+a.replace('"','\\"')+'"' for a in args),encoding='utf-8')
    result=subprocess.run([str(javac),'@'+str(argfile)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (tools/'compilation-private.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Compilation de la sonde échouée ; lire compilation-private.log')
    shutil.copy2(server.ROOT/'tests/natural-caverns-probe-plugin.yml',classes/'plugin.yml')
    target=tools/'FKNaturalCavernsProbe.jar';subprocess.run([str(jar),'--create','--file',str(target),'-C',str(classes),'.'],check=True,capture_output=True)
    shutil.copy2(target,copy/'plugins/FKNaturalCavernsProbe.jar')
    # Seule la copie éphémère reçoit ces réglages d'isolation.
    spigot=copy/'spigot.yml';spigot.write_text(re.sub(r'(?m)^(\s*restart-on-crash:) true$',r'\1 false',spigot.read_text()),encoding='utf-8')
    plan=work/'natural-caverns-plan-private.json';log=work/'paper-validation-private.log';started=time.monotonic()
    with server.maintenance(copy,check_worlds=False),log.open('w',encoding='utf-8') as output:
        command=[str(java),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-Dfk.natural.validation=true',
            '-Dfk.natural.plan='+str(plan),'-Dfk.natural.plan.sha256='+server.digest(plan),'-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25624']
        process=subprocess.Popen(command,cwd=copy,stdin=subprocess.PIPE,stdout=output,stderr=subprocess.STDOUT,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        while process.poll() is None:
            elapsed=time.monotonic()-started
            if elapsed>240:
                process.communicate('stop\n',timeout=60);raise RuntimeError('Sonde expirée ; copie conservée')
            print(json.dumps({'stage':'local_paper_validation','elapsedSeconds':round(elapsed)}),flush=True);time.sleep(10)
    text=log.read_text(encoding='utf-8',errors='replace');errors=[line for line in text.splitlines() if re.search(r'\b(ERROR|SEVERE)\b',line)]
    if process.returncode or errors or 'NATURAL CAVERNS PAPER VALIDATION SUCCESS' not in text:raise RuntimeError('Sonde Paper incomplète ; lire le journal privé')
    probe=json.loads((copy/'natural-caverns-paper-probe.json').read_text())
    probe.update({'exitCode':process.returncode,'errors':len(errors),'warnings':len(re.findall(r'\bWARN\b',text)),
        'artifactCandidateUnchanged':inventory(candidate)==before,'probeJarSha256':server.digest(target),
        'tcpBoundToLoopbackVerified':'127.0.0.1:25624' in text,'queryBoundToLoopbackVerified':'Query running on 127.0.0.1:22880' in text})
    if not all(probe[k] for k in ('artifactCandidateUnchanged','tcpBoundToLoopbackVerified','queryBoundToLoopbackVerified')):raise RuntimeError('Isolation ou conservation non validée')
    write(work/'paper-validation-result.json',probe);return probe

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.work),ensure_ascii=False))
