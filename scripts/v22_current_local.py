"""Validation fonctionnelle locale de copies complètes, sans accès MineStrator."""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import server
from minestrator_cold_backup import protect_directory,write,digest
from minestrator_rollback_local import files,connections,verify_listeners,is_loopback,query_local,run_local
from rollback_integrity import snapshot,compare

BASE=Path.home()/'FKBackups'
BACKUP=BASE/'MS-COLD-V22-20261123-01'
WORK=BASE/'MS-DEPLOY-V22-20261123-01'

def preservation(root):
    return {'files':files(root),'metadata':{p.relative_to(root).as_posix():[p.stat().st_size,p.stat().st_mtime_ns] for p in root.rglob('*') if p.is_file()}}

def validate(kind):
    if not WORK.exists():protect_directory(WORK)
    area=WORK/('rollback-local' if kind=='rollback' else 'candidate-local')
    if area.exists():raise RuntimeError('Validation locale existante conservée')
    source=BACKUP/'restore' if kind=='rollback' else WORK/'candidate'
    if kind=='rollback':
        info=json.loads((BACKUP/'report.json').read_text(encoding='utf-8'))
        manifest=json.loads((BACKUP/'manifest.json').read_text(encoding='utf-8'))
        if not info['backupValidated'] or digest(BACKUP/'instance.zip')!=info['archiveSha256'] or digest(BACKUP/'manifest.json')!=info['manifestSha256']:
            raise RuntimeError('Sauvegarde binaire non validée')
        if files(source)!={n:a['sha256'] for n,a in manifest['files'].items()}:raise RuntimeError('Restauration source différente')
    original=preservation(source);area.mkdir();root=area/'instance';shutil.copytree(source,root)
    if files(root)!=original['files']:raise RuntimeError('Copie de validation incomplète')
    before=files(root);report={'passed':False,'kind':kind,'sourceFiles':len(before),'remoteConnectionsUsed':False,'gameStarted':False,'authenticatedClients':0}
    code="import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import host_ops;host_ops.check(Path(sys.argv[2]),'v21-minestrator')"
    check=[sys.executable,'-X','utf8','-B','-c',code,str(root/'maintenance'),str(root)]
    process=None;logs=[];reader=None;watcher=None;network_stop=threading.Event();fault=[];samples=[]
    try:
        run_local(check,root,area/'maintenance-before.log');report['maintenanceBefore']=True
        java=server.java_path();snake=server.ROOT/'.cache/m2/org/yaml/snakeyaml/2.2/snakeyaml-2.2.jar'
        version=subprocess.run([str(java),'-version'],capture_output=True,text=True,check=True)
        if not re.search(r'version "25[.\"]',version.stderr+version.stdout):raise RuntimeError('Java 25 requis')
        report['javaVersion']=(version.stderr+version.stdout).splitlines()[0]
        shutil.copy2(root/'plugins/FKAmis/state.yml',area/'state-before.yml')
        world_before=snapshot(root);write(area/'world-before-private.json',world_before)
        import socket
        with socket.socket() as tcp,socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:tcp.bind(('127.0.0.1',22880));udp.bind(('127.0.0.1',22880))
        policies={n:(root/n).read_bytes() for n in ('whitelist.json','ops.json','banned-players.json','banned-ips.json')}
        protected=[n for n in before if n.startswith(('.fk-quarantine/','.fk-stage/','world/players/','plugins/FKAmis/history/')) or n in ('plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','paper.jar','plugins/FallenKingdom-2.24.9.jar','plugins/FKAmis-1.0.0.jar','FKAmis.sha256','RUNTIME_LOCK.json')]
        env=os.environ.copy()
        for key in list(env):
            if any(s in key.upper() for s in ('MINESTRATOR','SFTP','PTERODACTYL')) or key in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS'):env.pop(key)
        pending=queue.Queue()
        with server.maintenance(root,check_worlds=False):
            process=subprocess.Popen([str(java),'-Xms1G','-Xmx3G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','22880'],cwd=root,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW)
            report['processStarted']=True
            def read():
                for line in process.stdout:logs.append(line);pending.put(line)
            reader=threading.Thread(target=read,daemon=True);reader.start()
            def watch():
                while not network_stop.is_set() and process.poll() is None:
                    try:sample=connections(process.pid);verify_listeners(sample);samples.append(sample)
                    except Exception as error:
                        if process.poll() is None and not network_stop.is_set():fault.append(str(error))
                        return
                    network_stop.wait(2)
            watcher=threading.Thread(target=watch,daemon=True);watcher.start()
            def wait_for(marker,timeout=180):
                end=time.monotonic()+timeout
                while time.monotonic()<end:
                    if fault:raise RuntimeError(fault[0])
                    if process.poll() is not None:raise RuntimeError('Paper terminé avant validation')
                    try:line=pending.get(timeout=.5)
                    except queue.Empty:continue
                    if re.search(r'\b(ERROR|SEVERE)\b',line):raise RuntimeError('Erreur critique locale')
                    if marker in line:return
                raise RuntimeError('Validation locale expirée')
            def command(text):process.stdin.write(text+'\n');process.stdin.flush()
            wait_for('Done (');command('tick freeze')
            network=connections(process.pid);listeners=verify_listeners(network)
            if not any(is_loopback(x['localAddress']) and x['localPort']==22880 for x in listeners):raise RuntimeError('Écoute localhost non prouvée')
            report.update(query_local(22880,20));report['loopbackListenersVerified']=True
            for cmd,marker in [('version','Paper version'),('plugins','FKAmis'),('fka status','Jour 0'),('fka config validate','Configuration cohérente'),('fka info teams',''),('fka nether portal status','')]:
                command(cmd)
                if marker:wait_for(marker,30)
            command('stop');process.wait(timeout=120);reader.join(timeout=5)
            if process.returncode:raise RuntimeError('Arrêt local en erreur')
        if fault:raise RuntimeError(fault[0])
        text=''.join(logs)
        if re.search(r'\b(ERROR|SEVERE)\b',text):raise RuntimeError('Journal local critique')
        if 'FKAmis prêt' not in text or '26.3-244' not in text:raise RuntimeError('Preuve de plugins/versions absente')
        report.update(compare(world_before,snapshot(root)))
        for name in protected:
            if digest(root/name)!=before[name]:raise RuntimeError('Donnée protégée modifiée au boot')
        for name,data in policies.items():
            if (root/name).read_bytes()!=data:raise RuntimeError('Politique accès modifiée')
        state_check=run_local([str(java),'-cp',str(snake),str(server.ROOT/'scripts/RollbackStateCheck.java'),str(area/'state-before.yml'),str(root/'plugins/FKAmis/state.yml')],root,area/'state-comparison.log')
        report.update(json.loads(state_check));run_local(check,root,area/'maintenance-after.log')
        after=files(root);write(area/'runtime-differences-private.json',{'changed':[n for n in before if after.get(n)!=before[n]],'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys())})
        report.update({'passed':True,'maintenanceAfter':True,'paperExitCode':0,'errors':0,'warnings':len(re.findall(r'\bWARN\b',text)),
            'protectedFilesVerified':len(protected),'playerFilesVerified':sum(n.startswith('world/players/') for n in protected),
            'technicalFilesPreserved':sum(n.startswith(('.fk-quarantine/','.fk-stage/')) for n in protected)})
    except Exception as error:report['failure']=str(error)
    finally:
        if process and process.poll() is None:
            process.stdin.write('stop\n');process.stdin.flush()
            try:process.wait(timeout=120)
            except subprocess.TimeoutExpired:process.kill();process.wait();report['forcedTermination']=True
        network_stop.set()
        if watcher:watcher.join(timeout=25)
        if reader:reader.join(timeout=5)
        (area/'paper-private.log').write_text(''.join(logs),encoding='utf-8');write(area/'network-private.json',samples)
        report['sourceUnchanged']=preservation(source)==original
        if not report['sourceUnchanged']:report['passed']=False
        write(area/'report.json',report)
    if kind=='rollback' and report['passed']:
        info=json.loads((BACKUP/'report.json').read_text(encoding='utf-8'));info['functionalRestoreValidated']=True;info['functionalRestoreReportSha256']=digest(area/'report.json');write(BACKUP/'report.json',info)
    print(json.dumps(report,ensure_ascii=False));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('kind',choices=('rollback','candidate'));args=p.parse_args()
    try:r=validate(args.kind);sys.exit(0 if r['passed'] else 1)
    except Exception as error:print(json.dumps({'passed':False,'failure':type(error).__name__}));sys.exit(1)
