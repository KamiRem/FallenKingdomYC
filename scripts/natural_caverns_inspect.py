"""Préparer une copie de visite ; démarrage loopback uniquement sur --start explicite."""
import argparse
import json
from pathlib import Path
import re
import shutil
import server
from natural_caverns_rework import inventory,write

def prepare(work):
    work=work.resolve();candidate=work/'candidate';instance=work/'visual-inspection'
    if not candidate.is_dir():raise RuntimeError('Candidat local absent')
    if instance.exists():raise RuntimeError('Copie de visite existante : conservée sans écrasement')
    before=inventory(candidate)
    with server.maintenance(candidate):shutil.copytree(candidate,instance,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    if inventory(instance)!=before:raise RuntimeError('Copie de visite différente')
    spigot=instance/'spigot.yml';spigot.write_text(re.sub(r'(?m)^(\s*restart-on-crash:) true$',r'\1 false',spigot.read_text()),encoding='utf-8')
    write(instance/'.local-visual-inspection.json',{'localOnly':True,'gamePort':25625,'candidate':str(candidate),'sourceManifestSha256':before['DEPLOYMENT_MANIFEST.json']})
    visits=['VISITE LOCALE UNIQUEMENT — COMPTE DÉJÀ AUTORISÉ','Connexion Minecraft Java 26.3 : 127.0.0.1:25625',
        'Ne pas lancer la partie. Commandes ci-dessous dans la console locale uniquement.',
        'Remplacer <compte_autorise> par votre compte réel présent dans la whitelist, sans ajouter de compte.','']
    for cave in json.loads((candidate/'map-v21-caverns.json').read_text())['caverns']:
        x,y,z=cave['entrance'];visits.append(cave['team']+' — accès de surface : minecraft:tp <compte_autorise> '+f'{x+.5} {y} {z+.5}')
    (work/'VISITE_LOCALE_PRIVEE.txt').write_text('\n'.join(visits)+'\n',encoding='utf-8')
    if inventory(candidate)!=before:raise RuntimeError('Candidat modifié pendant préparation de visite')
    return instance

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--start',action='store_true');a=p.parse_args()
    instance=a.work.resolve()/'visual-inspection'
    if not a.start:print(prepare(a.work))
    else:
        marker=json.loads((instance/'.local-visual-inspection.json').read_text())
        if marker.get('localOnly') is not True or marker.get('gamePort')!=25625:raise RuntimeError('Copie de visite non reconnue')
        print('Visite locale 127.0.0.1:25625, whitelist inchangée. Saisir stop pour arrêter proprement. Aucune partie ne sera lancée par cet outil.',flush=True)
        server.start(instance,4,False,25625,False)
