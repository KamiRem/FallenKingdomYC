"""Recette des corrections sur Paper avec acteurs Player simulés, sans connexion client."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import threading
import re
from server import ROOT, server_dir, restore, maintenance, java_path, digest, validate


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--name',default='probe-v2-fixes');args=parser.parse_args()
    if not args.name.startswith('probe-v2-fixes'): raise ValueError('Nom de recette réservé.')
    root=server_dir(args.name)
    if root.exists(): raise RuntimeError('Recette conservée : choisir un nouveau nom sans écraser la précédente.')
    baseline=json.loads((ROOT/'.cache/v2-fixes-baseline.json').read_text(encoding='utf-8'))
    restore(root,ROOT/baseline['archive'])
    with maintenance(root,check_worlds=False):
        config=root/'plugins/FKAmis/config.yml'
        text=config.read_text(encoding='utf-8')
        if 'extra-banned: []' not in text: raise RuntimeError('Fixture historique attendue, conserver les restrictions existantes.')
        config.write_text(text.replace('extra-banned: []','extra-banned: [ELYTRA, ENCHANTED_GOLDEN_APPLE]'),encoding='utf-8')
        jar=ROOT/'plugins-custom/fk-amis/target/fk-amis-1.0.0.jar'
        shutil.copy2(jar,root/'plugins/FKAmis-1.0.0.jar');(root/'FKAmis.sha256').write_text(digest(jar)+'\n',encoding='ascii')
        shutil.copy2(ROOT/'.cache/FKGameplayProbe.jar',root/'plugins/FKGameplayProbe.jar')
        validate(root)
        command=[str(java_path()),'-Xms1G','-Xmx4G','-Dfk.gameplayprobe=true','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25580']
        process=subprocess.Popen(command,cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        lines=[]
        def read():
            for line in process.stdout:
                lines.append(line)
                if 'GAMEPLAY PROBE' in line: print(line.strip(),flush=True)
        reader=threading.Thread(target=read,daemon=True);reader.start()
        try:process.wait(timeout=300)
        finally:
            if process.poll() is None:process.stdin.write('stop\n');process.stdin.flush();process.wait(timeout=120)
            reader.join(timeout=5)
        text=''.join(lines);(ROOT/'.cache'/f'{args.name}.log').write_text(text,encoding='utf-8')
        if process.returncode or 'GAMEPLAY PROBE SUCCESS' not in text or 'GAMEPLAY PROBE FAILED' in text or re.search(r'\b(ERROR|SEVERE)\b',text):
            print('\n'.join(line for line in text.splitlines() if 'Exception' in line or 'AssertionError' in line or 'FAILED' in line)[:4000],flush=True)
            raise RuntimeError('Recette gameplay échouée, conserver la copie et son journal .cache.')
    print('Recette des événements API réussie ; essais avec vrais clients toujours distincts.')


if __name__=='__main__': main()
