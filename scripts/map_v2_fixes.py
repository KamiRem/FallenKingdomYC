"""Nettoyage conservateur de la copie V2 ; ne reconstruit aucun terrain ni coffre."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import threading
from server import ROOT, backup, restore, maintenance, server_dir, digest, iter_files, java_path, validate


def prepare():
    source,target=server_dir('map-v2'),server_dir('map-v2-fixes')
    if target.exists(): raise RuntimeError('Copie déjà présente ; aucune donnée ne sera remplacée.')
    archive=backup(source)
    report={'archive':str(archive.relative_to(ROOT)), 'sha256':digest(archive),'instances':{}}
    for name in ('local','map-v2'):
        root=server_dir(name)
        with maintenance(root): report['instances'][name]={str(p.relative_to(root)):digest(p) for p in iter_files(root)}
    (ROOT/'.cache/v2-fixes-baseline.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    restore(target,archive)


def run():
    root=server_dir('map-v2-fixes')
    with maintenance(root):
        state=(root/'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
        if not re.search(r'^started: false$',state,re.M) or re.search(r'^objectives:',state,re.M):
            raise RuntimeError('Nettoyage interdit après départ ou présence d’objectifs.')
    backup(root)
    with maintenance(root,check_worlds=False):
        config=root/'plugins/FKAmis/config.yml'
        content=config.read_text(encoding='utf-8')
        match=re.search(r'^extra-banned: \[([^\n]*)\]$',content,re.M)
        if not match: raise RuntimeError('Liste extra-banned en ligne attendue ; conserver les restrictions existantes.')
        values=[s.strip().strip('"\'') for s in match[1].split(',') if s.strip()]
        values=list(dict.fromkeys(values+['ELYTRA','ENCHANTED_GOLDEN_APPLE']))
        content=content[:match.start()]+'extra-banned: '+json.dumps(values)+content[match.end():]
        config.write_text(content,encoding='utf-8')
        companion=ROOT/'plugins-custom/fk-amis/target/fk-amis-1.0.0.jar'
        shutil.copy2(companion,root/'plugins/FKAmis-1.0.0.jar')
        (root/'FKAmis.sha256').write_text(digest(companion)+'\n',encoding='ascii')
        shutil.copy2(ROOT/'.cache/FKMapV2Corrections.jar',root/'plugins/FKMapV2Corrections.jar')
        validate(root)
        command=[str(java_path()),'-Xms1G','-Xmx4G','-Dfk.corrections.authorized=true','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25579']
        process=subprocess.Popen(command,cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        lines=[]
        def read():
            for line in process.stdout:
                lines.append(line)
                if 'CORRECTIONS' in line: print(line.strip(),flush=True)
        reader=threading.Thread(target=read,daemon=True);reader.start()
        try: process.wait(timeout=1800)
        finally:
            if process.poll() is None:
                process.stdin.write('stop\n');process.stdin.flush();process.wait(timeout=120)
            reader.join(timeout=5)
        text=''.join(lines)
        (ROOT/'.cache/v2-fixes-cleanup.log').write_text(text,encoding='utf-8')
        if process.returncode or 'CORRECTIONS CLEAN SUCCESS' not in text or 'CORRECTIONS FAILED' in text:
            print(text[-14000:],flush=True);raise RuntimeError('Nettoyage échoué ; copie conservée pour examen.')
        destination=ROOT/'.cache'/('FKMapV2Corrections-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.jar')
        (root/'plugins/FKMapV2Corrections.jar').replace(destination)
    print('Copie nettoyée et serveur arrêté ; vérifier visuellement en jeu.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','clean']);args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:run()
