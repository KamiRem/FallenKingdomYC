"""Démarrage fonctionnel d'une copie du rollback V2.1 restauré, sans partie lancée."""
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
    source=work/'rollback-control-v21';root=work/'rollback-boot-check'
    if root.exists():raise RuntimeError('Copie de test existante conservée')
    before=inventory(source)
    with server.maintenance(source):shutil.copytree(source,root,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    props=root/'server.properties';props.write_text(re.sub(r'(?m)^query.port=.*$','query.port=25632',props.read_text()),encoding='utf-8')
    spigot=root/'spigot.yml';spigot.write_text(re.sub(r'(?m)^(\s*restart-on-crash:) true$',r'\1 false',spigot.read_text()),encoding='utf-8')
    logpath=work/'rollback-boot-private.log';started=time.monotonic();ready=False
    with server.maintenance(root,check_worlds=False),logpath.open('w',encoding='utf-8') as log:
        p=subprocess.Popen([str(server.java_path()),'-Xms1G','-Xmx3G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25632'],cwd=root,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        while p.poll() is None:
            text=logpath.read_text(encoding='utf-8',errors='replace')
            if re.search(r'\b(ERROR|SEVERE)\b',text):p.communicate('stop\n',timeout=60);raise RuntimeError('Erreur de démarrage rollback')
            if 'Done (' in text and 'FKAmis prêt' in text:
                ready=True;p.stdin.write('fka status\nfka config validate\n');p.stdin.flush();time.sleep(1);p.communicate('stop\n',timeout=90);break
            if time.monotonic()-started>180:p.communicate('stop\n',timeout=60);raise RuntimeError('Démarrage rollback expiré')
            print(json.dumps({'stage':'rollback_functional_check','elapsedSeconds':round(time.monotonic()-started)}),flush=True);time.sleep(5)
    text=logpath.read_text(encoding='utf-8',errors='replace')
    if not ready or p.returncode or 'Jour 0' not in text or 'Configuration cohérente' not in text or re.search(r'\b(ERROR|SEVERE)\b',text):raise RuntimeError('Rollback fonctionnel non validé')
    result={'passed':True,'restoredFiles':len(before),'functionalBootPassed':True,'exitCode':p.returncode,'day':0,'gameStarted':False,
        'restorationControlUnchanged':inventory(source)==before,'errors':0,'warnings':len(re.findall(r'\bWARN\b',text)),
        'gamePort':25632,'queryLoopback':'Query running on 127.0.0.1:25632' in text,'authenticatedClients':0,'productionRollbackPerformed':False}
    if not result['restorationControlUnchanged'] or not result['queryLoopback']:raise RuntimeError('Isolation ou intégrité rollback non prouvée')
    write(work/'rollback-functional-result.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.work.resolve()),ensure_ascii=False))
