"""Archives privées, vérification du rollback local et visite séparée V2.2."""
import argparse
import json
from pathlib import Path
import re
import shutil
import server
from natural_caverns_rework import inventory,write

def inspection(work):
    candidate=work/'candidate';target=work/'visual-inspection'
    if target.exists():raise RuntimeError('Copie de visite existante conservée')
    before=inventory(candidate)
    with server.maintenance(candidate):shutil.copytree(candidate,target,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    if inventory(target)!=before:raise RuntimeError('Copie de visite non conforme')
    props=target/'server.properties';props.write_text(re.sub(r'(?m)^query.port=.*$','query.port=25631',props.read_text()),encoding='utf-8')
    write(target/'.local-vanilla-inspection.json',{'localOnly':True,'port':25631,'candidateManifestSha256':before['DEPLOYMENT_MANIFEST.json']})
    refs=json.loads((candidate/'maintenance/new-match-reference-v2.2.json').read_text())
    lines=['VISITE V2.2 LOCALE UNIQUEMENT : 127.0.0.1:25631','Utiliser votre compte réel déjà autorisé, ne pas modifier la whitelist.','Ne pas lancer de partie. Remplacer <compte_autorise> dans la console locale.','']
    for base in refs['bases']:
        s=base['spawn'];c=base['center'];x,z=int(c['X']),int(c['Z']);y=max(float(s['y'])+15,120)
        lines.extend([base['team'],f"Spawn : minecraft:tp <compte_autorise> {s['x']} {s['y']} {s['z']}",
            f"Arbitre Creative en vol, hors territoire : minecraft:tp <compte_autorise> {x+41} {y} {z}",
            f"Avancer normalement vers X={x+40} : une seule entrée colorée attendue.",
            'Pour examiner le sous-sol sans creuser : mode Spectator par console sur cette copie uniquement, puis rétablir Creative.',''])
    (work/'VISITE_V22_PRIVEE.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if inventory(candidate)!=before:raise RuntimeError('La visite a modifié le candidat')
    return target

def deliver(work):
    work=work.resolve();candidate=work/'candidate';before=inventory(candidate)
    expected=json.loads((work/'candidate-files-private.json').read_text())
    if before!=expected:raise RuntimeError('Candidat modifié hors préparation')
    for name in ('vanilla-paper-validation-result.json','territory-fixed-02-result.json','maintenance-validation-private.json','original-terrain-comparison-private.json'):
        data=json.loads((work/name).read_text())
        if name!='maintenance-validation-private.json' and not data.get('passed'):raise RuntimeError('Validation manquante')
    artifacts=[]
    with server.maintenance(candidate):
        world_names=[n for n in before if n.startswith('world/')]+['map-v2-construction.json','map-underground-restoration.json',
            'maintenance/new-match-reference.json','maintenance/new-match-reference-v2.2.json','maintenance/new_match.py','maintenance/terrain_reference.py','maintenance/block-defaults-26.3.json']
        plugin_names=['plugins/FKAmis-1.0.0.jar','FKAmis.sha256','RUNTIME_LOCK.json','plugins/FallenKingdom/locales/messages_fr.properties']
        for label,names in (('world',world_names),('fkamis-update',plugin_names)):
            stage=work/('payload-'+label)
            if stage.exists():raise RuntimeError('Payload existant, ne pas écraser')
            stage.mkdir()
            for name in names:
                target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(candidate/name,target)
            archive=work/('fallenkingdom-v22-'+label+'-private.zip')
            with server.maintenance(stage):server.create_archive(stage,archive)
            artifacts.append({'file':archive.name,'sha256':server.digest(archive),'bytes':archive.stat().st_size,'files':len(names)})
        complete=work/'fallenkingdom-v22-candidate-private.zip';server.create_archive(candidate,complete)
        artifacts.append({'file':complete.name,'sha256':server.digest(complete),'bytes':complete.stat().st_size,'files':len(before)})
    rollback=work/'rollback-control-v21';source_backup=work/'before-v22-local.zip';server.restore(rollback,source_backup)
    source=json.loads((work/'source-files-private.json').read_text())
    if inventory(rollback)!=source:raise RuntimeError('Restauration de contrôle V2.1 différente')
    artifacts.append({'file':source_backup.name,'sha256':server.digest(source_backup),'bytes':source_backup.stat().st_size,'files':len(source)})
    inspection(work)
    if inventory(candidate)!=before:raise RuntimeError('Le candidat a changé pendant la livraison')
    jars=work/'FKAmis-v22-notifications.jar';shutil.copy2(candidate/'plugins/FKAmis-1.0.0.jar',jars);jars.with_suffix('.jar.sha256').write_text(server.digest(jars)+'\n',encoding='ascii')
    artifacts.append({'file':jars.name,'sha256':server.digest(jars),'bytes':jars.stat().st_size,'files':1})
    summary={'variant':'V2.2-vanilla-underground','passed':True,'artifacts':artifacts,'rollbackFilesRestoredAndVerified':len(source),'candidateUnchanged':True,'inspectionPrepared':True,'inspectionStarted':False,'remoteAccessPerformed':False,'deployed':False}
    write(work/'delivery-private.json',summary)
    (work/'SHA256SUMS.txt').write_text('\n'.join(item['sha256']+'  '+item['file'] for item in artifacts)+'\n',encoding='ascii')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--start-inspection',action='store_true');a=p.parse_args();w=a.work.resolve()
    if a.start_inspection:
        target=w/'visual-inspection';marker=json.loads((target/'.local-vanilla-inspection.json').read_text())
        if marker.get('localOnly') is not True or marker.get('port')!=25631:raise RuntimeError('Copie locale non reconnue')
        print('Visite locale 127.0.0.1:25631 ; stop pour fermer proprement. Aucune partie ne sera lancée automatiquement.',flush=True)
        server.start(target,4,False,25631,False)
    else:print(json.dumps(deliver(w),ensure_ascii=False))
