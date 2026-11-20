"""Validation d'une copie indépendante du rollback : aucun client API ou SFTP."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import socket
import subprocess
import threading
import time
import traceback
import argparse
import server
from minestrator_cold_backup import protect_directory

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def files(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def preservation(source):
    return {'archiveSha256':sha(source/'instance.zip'),'manifestSha256':sha(source/'manifest.json'),'files':files(source/'restore'),
      'directories':sorted(p.relative_to(source/'restore').as_posix() for p in (source/'restore').rglob('*') if p.is_dir()),
      'metadata':{p.relative_to(source/'restore').as_posix():[p.stat().st_size,p.stat().st_mtime_ns] for p in (source/'restore').rglob('*') if p.is_file()}}
def run_local(command,root,log):
    result=subprocess.run(command,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    log.write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Validation locale refusée : '+log.name)
    return result.stdout
def connections(pid):
    command=f"$ErrorActionPreference='Stop'; $t=@(Get-NetTCPConnection -OwningProcess {int(pid)} -ErrorAction SilentlyContinue | ForEach-Object {{ @{{localAddress=$_.LocalAddress;localPort=$_.LocalPort;remoteAddress=$_.RemoteAddress;remotePort=$_.RemotePort;state=$_.State.ToString()}} }}); $u=@(Get-NetUDPEndpoint -OwningProcess {int(pid)} -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort); @{{tcp=$t;udp=$u}} | ConvertTo-Json -Depth 4 -Compress"
    r=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,text=True,timeout=20)
    if r.returncode:raise RuntimeError('Inspection réseau locale impossible')
    return json.loads(r.stdout)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True,help='Nouveau dossier privé hors dépôt et hors sauvegarde')
    args=parser.parse_args()
    source=Path.home()/'FKBackups/MS-COLD-20261119-02';work=args.work.resolve();root=work/'preproduction'
    if work.is_relative_to(server.ROOT) or work.is_relative_to(source) or source.is_relative_to(work):raise RuntimeError('Destination de test hors dépôt et sauvegarde requise')
    if work.exists():raise RuntimeError('Destination de test existante, ne pas écraser.')
    evidence=json.loads((source/'report.json').read_text(encoding='utf-8'));manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    original=preservation(source)
    if original['archiveSha256']!=evidence['archiveSha256'] or original['manifestSha256']!=evidence['manifestSha256']:raise RuntimeError('Originaux modifiés')
    if original['files']!={n:a['sha256'] for n,a in manifest['files'].items()}:raise RuntimeError('Restauration originale modifiée')
    protect_directory(work);write(work/'original-preservation.json',original)
    report={'passed':False,'originalsUnchanged':False,'remoteConnectionsUsed':False,'remoteFilesModified':False,'deploymentAuthorized':False,'minecraftClientsAuthenticated':0,'processStarted':False}
    process=None
    try:
        shutil.copytree(source/'restore',root)
        if files(root)!=original['files']:raise RuntimeError('Copie indépendante différente')
        jar=root/'plugins/FKAmis-1.0.0.jar';actual=sha(jar)
        if actual!='46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442':raise RuntimeError('JAR VNext.1 inattendu')
        registry=json.loads((root/'RUNTIME_LOCK.json').read_text(encoding='utf-8-sig'))
        if registry['sha256']['plugins/FKAmis-1.0.0.jar']!=actual:raise RuntimeError('Registre incohérent')
        old_marker=(root/'FKAmis.sha256').read_text().strip();(root/'FKAmis.sha256').write_text(actual+'\n',encoding='ascii')
        before=files(root);changed=[n for n in before if before[n]!=original['files'][n]]
        if changed!=['FKAmis.sha256']:raise RuntimeError('Modification manuelle supplémentaire')
        report.update({'copyManifestFilesCompared':len(before),'manualChangesBeforeBoot':changed,'oldMarkerSha256':old_marker,'jarSha256':actual,'runtimeRegistryCoherent':True})
        print(json.dumps({'stage':'independent_copy_ready','files':len(before),'onlyManualChange':'FKAmis.sha256'}),flush=True)
        # Validateur courant externe : ne pas remplacer les outils ou données historiques.
        check_code="import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import server;sys.modules['serverlib']=server;sys.path.insert(0,sys.argv[2]);import host_ops;host_ops.check(Path(sys.argv[3]))"
        check_command=[sys.executable,'-B','-c',check_code,str(server.ROOT/'scripts'),str(server.ROOT/'deployment'),str(root)]
        if server.properties(root/'server.properties').get('max-players')!='10':raise RuntimeError('Capacité historique inattendue')
        run_local(check_command,root,work/'maintenance-before.log')
        report['maintenanceCheckBeforeBoot']=True
        report['externalMaintenanceValidatorSha256']=sha(server.ROOT/'scripts/server.py')
        report['historicalMaxPlayers']=10
        java=server.java_path();snake=server.ROOT/'.cache/m2/org/yaml/snakeyaml/2.2/snakeyaml-2.2.jar'
        version=subprocess.run([str(java),'-version'],capture_output=True,text=True,check=True)
        if not re.search(r'version "25[.\"]',version.stderr+version.stdout):raise RuntimeError('Java 25 requis')
        report['javaVersion']=(version.stderr+version.stdout).splitlines()[0]
        state_command=[str(java),'-cp',str(snake),str(server.ROOT/'scripts/RollbackStateCheck.java')]
        run_local([*state_command,str(root/'plugins/FKAmis/state.yml'),str(root/'plugins/FKAmis/state.yml')],root,work/'state-schema-before.log')
        report['historicalSchemaCompatible']=True
        # Seulement des copies privées des données de référence pour le contrôle après exécution.
        shutil.copy2(root/'plugins/FKAmis/state.yml',work/'state-before.yml')
        protected=[n for n in before if '/players/data/' in n or '/playerdata/' in n or n.startswith('plugins/FKAmis/history/') or n in ('plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml')]
        policies={n:json.loads((root/n).read_text(encoding='utf-8-sig')) for n in ('whitelist.json','ops.json','banned-players.json','banned-ips.json')}
        with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        report['localPort']=port
        config=server.properties(root/'server.properties')
        for key in ('enable-rcon','enable-query','management-server-enabled','enable-jmx-monitoring'):
            if config.get(key,'false')!='false':raise RuntimeError('Service annexe actif : '+key)
        logs=[];pending=queue.Queue()
        env=os.environ.copy()
        for key in list(env):
            if any(p in key.upper() for p in ('MINESTRATOR','SFTP','PTERODACTYL')) or key in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS'):env.pop(key)
        with server.maintenance(root,check_worlds=False):
            process=subprocess.Popen([str(java),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-jar','paper.jar','--nogui','--host','127.0.0.1','--port',str(port)],cwd=root,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1)
            report['processStarted']=True
            def read():
                for line in process.stdout:logs.append(line);pending.put(line)
            reader=threading.Thread(target=read,daemon=True);reader.start()
            def wait_for(marker,timeout=180):
                end=time.monotonic()+timeout
                while time.monotonic()<end:
                    if process.poll() is not None:raise RuntimeError('Paper arrêté avant validation')
                    try:line=pending.get(timeout=.5)
                    except queue.Empty:continue
                    if re.search(r'\b(ERROR|SEVERE)\b',line):raise RuntimeError('Erreur critique dans les logs locaux')
                    if marker in line:return
                raise RuntimeError('Délai de démarrage/commande dépassé')
            def command(value):process.stdin.write(value+'\n');process.stdin.flush()
            try:
                wait_for('Done (')
                if not any('FKAmis prêt' in x for x in logs):raise RuntimeError('FKAmis non activé')
                network=connections(process.pid);write(work/'network-private.json',network)
                listeners=[x for x in network['tcp'] if x['state']=='Listen']
                if not any(x['localAddress']=='127.0.0.1' and x['localPort']==port for x in listeners):raise RuntimeError('Socket de jeu local non confirmé')
                if any(x['localAddress'] not in ('127.0.0.1','::1') for x in listeners) or any(x['LocalAddress'] not in ('127.0.0.1','::1') for x in network['udp']):raise RuntimeError('Service exposé hors localhost')
                if any(x['remoteAddress']=='91.197.6.72' for x in network['tcp']):raise RuntimeError('Connexion vers le serveur MineStrator détectée')
                report['loopbackListenersVerified']=True;report['listeners']=listeners;report['udpEndpointsCount']=len(network['udp'])
                for cmd,marker in [('version','Paper version'),('plugins','FKAmis'),('fka status','Jour '),('fka config validate','Configuration cohérente'),('fka supply status',''),('fka admin list',''),('list','players online')]:
                    command(cmd)
                    if marker:wait_for(marker,30)
                if not any('There are 0 of a max of' in x for x in logs):raise RuntimeError('Absence de joueurs non confirmée')
                command('stop');process.wait(timeout=120);reader.join(timeout=5)
                if process.returncode:raise RuntimeError('Arrêt Paper en erreur')
            finally:
                if process.poll() is None:
                    command('stop')
                    try:process.wait(timeout=90)
                    except subprocess.TimeoutExpired:process.kill();process.wait();report['forcedLocalTermination']=True
                reader.join(timeout=5);(work/'paper-private.log').write_text(''.join(logs),encoding='utf-8')
        errors=[x for x in logs if re.search(r'\b(ERROR|SEVERE)\b',x)]
        if errors:raise RuntimeError('Logs critiques non vides')
        report['warningCount']=sum(bool(re.search(r'\bWARN\b',x)) for x in logs);report['errorCount']=len(errors)
        report['paperExitCode']=process.returncode
        for name in protected:
            if not (root/name).is_file() or sha(root/name)!=before[name]:raise RuntimeError('Donnée historique protégée modifiée')
        for name,value in policies.items():
            if json.loads((root/name).read_text(encoding='utf-8-sig'))!=value:raise RuntimeError('Politique d’accès modifiée')
        state_check=run_local([str(java),'-cp',str(snake),str(server.ROOT/'scripts/RollbackStateCheck.java'),str(work/'state-before.yml'),str(root/'plugins/FKAmis/state.yml')],root,work/'state-check-private.log')
        report.update(json.loads(state_check));report['protectedHistoricalFilesCompared']=len(protected)
        report['playerProfileFilesCompared']=sum('/players/data/' in n or '/playerdata/' in n for n in protected)
        report['accessPoliciesPreserved']=True
        run_local(check_command,root,work/'maintenance-after.log')
        report['maintenanceCheckAfterBoot']=True
        after=files(root);changes={'changed':[n for n in before if after.get(n)!=before[n]],'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys())}
        write(work/'runtime-diff-private.json',changes)
        report['runtimeChangesCounts']={k:len(v) for k,v in changes.items()}
        report['passed']=True
        print(json.dumps({'stage':'local_rollback_test_passed','port':port,'errorCount':0,'historicalStatePreserved':True}),flush=True)
    except Exception as error:
        report['failure']=str(error);(work/'failure-private.log').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        report['originalsUnchanged']=preservation(source)==original
        if not report['originalsUnchanged']:report['passed']=False;report['originalPreservationFailure']=True
        report['testDirectory']=str(root);write(work/'report.json',report)
    print(json.dumps({'passed':report['passed'],'originalsUnchanged':report['originalsUnchanged'],'processStarted':report['processStarted'],'failure':report.get('failure'),'reportDirectory':str(work)},ensure_ascii=True),flush=True)
    return 0 if report['passed'] else 1
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:print(json.dumps({'passed':False,'reason':type(error).__name__}));sys.exit(1)
