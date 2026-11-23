"""Comparer le JAR historique et le correctif sur deux instances locales distinctes."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import server
from natural_caverns_rework import inventory,write

def run(work,source,baseline,attempt):
    work=work.resolve();source=source.resolve();mode='baseline' if baseline else 'fixed'
    root=work/('territory-'+mode+'-'+attempt);tools=work/('territory-tools-'+mode+'-'+attempt)
    if root.exists() or tools.exists():raise RuntimeError('Tentative existante, ne pas écraser les preuves')
    before=inventory(source)
    with server.maintenance(source):shutil.copytree(source,root,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    tools.mkdir();classes=tools/'classes';classes.mkdir()
    api=server.ROOT/'.cache/m2/io/papermc/paper/paper-api/26.3.build.244-stable/paper-api-26.3.build.244-stable.jar'
    dependencies=[api,*root.joinpath('libraries').rglob('*.jar'),*root.joinpath('plugins').glob('*.jar'),*server.ROOT.joinpath('.cache/m2/org/jetbrains/annotations').rglob('*.jar')]
    args=['-encoding','UTF-8','--release','25','-cp',';'.join(p.as_posix() for p in dependencies),'-d',classes.as_posix(),
        (server.ROOT/'plugins-custom/fk-amis/src/test/java/fr/fkamis/SyntheticPlayer.java').as_posix(),
        (server.ROOT/'plugins-custom/fk-amis/src/test/java/fr/fkamis/TerritoryProbe.java').as_posix()]
    argfile=tools/'javac.args';argfile.write_text('\n'.join('"'+arg.replace('"','\\"')+'"' for arg in args),encoding='utf-8')
    java=server.java_path();compilation=subprocess.run([str(java.with_name('javac.exe')),'@'+str(argfile)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (tools/'compilation-private.log').write_text(compilation.stdout+compilation.stderr,encoding='utf-8')
    if compilation.returncode:raise RuntimeError('Compilation sonde échouée, lire son journal privé')
    shutil.copy2(server.ROOT/'tests/territory-probe-plugin.yml',classes/'plugin.yml');jar=tools/'FKTerritoryProbe.jar'
    subprocess.run([str(java.with_name('jar.exe')),'--create','--file',str(jar),'-C',str(classes),'.'],check=True,capture_output=True)
    shutil.copy2(jar,root/'plugins/FKTerritoryProbe.jar')
    spigot=root/'spigot.yml';spigot.write_text(re.sub(r'(?m)^(\s*restart-on-crash:) true$',r'\1 false',spigot.read_text()),encoding='utf-8')
    logfile=work/('territory-'+mode+'-'+attempt+'-private.log');port=25628 if baseline else 25629
    props=root/'server.properties';props.write_text(re.sub(r'(?m)^query.port=.*$','query.port='+str(port),props.read_text()),encoding='utf-8')
    command=[str(java),'-Xms1G','-Xmx3G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-Dfk.territory.probe=true','-Dfk.territory.baseline='+str(baseline).lower(),'-jar','paper.jar','--nogui','--host','127.0.0.1','--port',str(port)]
    with server.maintenance(root,check_worlds=False),logfile.open('w',encoding='utf-8') as log:
        process=subprocess.Popen(command,cwd=root,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,creationflags=subprocess.CREATE_NO_WINDOW);start=time.monotonic()
        while process.poll() is None:
            if time.monotonic()-start>180:process.communicate('stop\n',timeout=60);raise RuntimeError('Sonde expirée')
            print(json.dumps({'stage':'territory_probe','mode':mode,'elapsedSeconds':round(time.monotonic()-start)}),flush=True);time.sleep(5)
    log=logfile.read_text(encoding='utf-8',errors='replace')
    errors=re.findall(r'\b(ERROR|SEVERE)\b',log)
    if process.returncode or errors or 'TERRITORY PROBE SUCCESS' not in log:raise RuntimeError('Sonde interrompue, consulter le journal privé')
    result=json.loads((root/'territory-probe-result.json').read_text(encoding='utf-8'));result.update({'exitCode':process.returncode,'errors':len(errors),'warnings':len(re.findall(r'\bWARN\b',log)),
        'sourceUnchanged':inventory(source)==before,'gamePort':port,'queryLoopback':('Query running on 127.0.0.1:'+str(port)) in log})
    if not result['sourceUnchanged'] or not result['queryLoopback']:raise RuntimeError('Conservation ou isolation non validée')
    write(work/('territory-'+mode+'-'+attempt+'-result.json'),result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--baseline',action='store_true');p.add_argument('--attempt',default='01');a=p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.attempt):raise RuntimeError('Identifiant de tentative invalide')
    print(json.dumps(run(a.work,a.source,a.baseline,a.attempt),ensure_ascii=False))
