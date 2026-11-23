"""Livraison locale corrigée et restauration fonctionnelle d'une partie simulée terminée."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import server
from natural_caverns_rework import inventory,write
from rollback_integrity import snapshot,compare
from v22_final_campaign import prepare,run_phase

SUITES=['final','four','features-1','features-2','features-3','features-4','next1','supplies','statistics','physics']


def deliver(work,source):
    expected=prepare(work,source);h=server.digest(server.PLUGIN)
    for name in SUITES:
        result=json.loads((work/f'{name}-result.json').read_text(encoding='utf-8'))
        if not result['passed'] or not result['sourceUnchanged'] or result['fkamisSha256']!=h:raise RuntimeError('Campagne incomplète ou JAR différent : '+name)
    candidate=work/'candidate'
    if candidate.exists():raise RuntimeError('Candidat existant conservé')
    with server.maintenance(source):shutil.copytree(source,candidate,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    if inventory(candidate)!=expected:raise RuntimeError('Copie initiale différente')
    with server.maintenance(candidate):
        shutil.copy2(server.PLUGIN,candidate/'plugins/FKAmis-1.0.0.jar');(candidate/'FKAmis.sha256').write_text(h+'\n',encoding='ascii')
        registry=candidate/'RUNTIME_LOCK.json';data=json.loads(registry.read_text(encoding='utf-8'));data['sha256']['plugins/FKAmis-1.0.0.jar']=h;write(registry,data)
        manifest=candidate/'DEPLOYMENT_MANIFEST.json';data=json.loads(manifest.read_text(encoding='utf-8'))
        for name in data['files']:data['files'][name]=server.digest(candidate/name)
        data['localValidationRevision']=work.name;write(manifest,data)
        after=inventory(candidate)
        changed=sorted(n for n in expected if expected[n]!=after[n])
        allowed=['DEPLOYMENT_MANIFEST.json','FKAmis.sha256','RUNTIME_LOCK.json','plugins/FKAmis-1.0.0.jar']
        if changed!=allowed or set(after)!=set(expected):raise RuntimeError('Différence de livraison inattendue')
        if any(after[n]!=expected[n] for n in expected if n.startswith('world/')):raise RuntimeError('Terrain modifié par la finalisation')
        write(work/'candidate-files-private.json',after)
        for action in ('check','verify-baseline'):
            result=subprocess.run([sys.executable,'-X','utf8','-B',str(candidate/'maintenance/host_ops.py'),action],capture_output=True,text=True,encoding='utf-8',errors='strict')
            (work/f'maintenance-{action}-private.log').write_text(result.stdout+result.stderr,encoding='utf-8')
            if result.returncode:raise RuntimeError('Maintenance refusée : '+action)
        sys.path.insert(0,str(candidate/'maintenance'))
        import new_match
        checks=new_match.initial_checks(candidate,candidate/'maintenance/new-match-reference-v2.2.json')
        write(work/'maintenance-validation-private.json',checks)
        archive=work/'fallenkingdom-v22-final-candidate-private.zip';server.create_archive(candidate,archive)
    artifacts=[{'file':archive.name,'sha256':server.digest(archive),'files':len(after),'bytes':archive.stat().st_size}]
    jar=work/'FKAmis-v22-final.jar';shutil.copy2(server.PLUGIN,jar);jar.with_suffix('.jar.sha256').write_text(h+'\n',encoding='ascii')
    artifacts.append({'file':jar.name,'sha256':h,'files':1,'bytes':jar.stat().st_size})
    if inventory(candidate)!=after or inventory(source)!=expected:raise RuntimeError('Source ou candidat modifié pendant la livraison')
    result={'passed':True,'revision':work.name,'artifacts':artifacts,'changedCandidateFiles':changed,'candidateManagedFiles':len(after),'manifestEntries':len(data['files']),
            'worldFilesIdenticalToDed565d':sum(n.startswith('world/') for n in after),'originalCandidateUnchanged':True,'maintenanceChecks':checks,'remoteAccessPerformed':False,'deployed':False}
    write(work/'delivery-private.json',result);(work/'SHA256SUMS.txt').write_text('\n'.join(a['sha256']+'  '+a['file'] for a in artifacts)+'\n',encoding='ascii')
    return result


def restore_finished(work):
    work=work.resolve();private_parent=(Path.home()/'FKBackups').resolve()
    if work==private_parent or not work.is_relative_to(private_parent):raise RuntimeError('Restauration réservée au dossier privé hors dépôt')
    source=work/'runtime/probe-features-4-01'
    result=json.loads((work/'features-4-result.json').read_text(encoding='utf-8'))
    if not result['passed']:raise RuntimeError('Partie à seize non validée')
    archive=work/'finished-simulated-match-private.zip';restored=work/'finished-match-restored';boot=work/'finished-match-boot'
    if archive.exists() or restored.exists() or boot.exists():raise RuntimeError('Archives et restaurations existantes conservées')
    with server.maintenance(source):
        before=inventory(source);original_snapshot=snapshot(source);server.create_archive(source,archive)
    server.restore(restored,archive)
    if inventory(restored)!=before:raise RuntimeError('Restauration binaire différente')
    with server.maintenance(restored):shutil.copytree(restored,boot,ignore=shutil.ignore_patterns('.control.lock','session.lock'))
    staging=work/'restore-probe-classes';staging.mkdir();folder=staging/'fr/fkamis';folder.mkdir(parents=True)
    for pattern in ('CampaignRestoreProbe*.class','SyntheticPlayer*.class'):
        files=list((server.ROOT/'plugins-custom/fk-amis/target/test-classes/fr/fkamis').glob(pattern))
        if not files:raise RuntimeError('Sonde de restauration non compilée')
        for path in files:shutil.copy2(path,folder/path.name)
    shutil.copy2(server.ROOT/'tests/campaign-restore-plugin.yml',staging/'plugin.yml')
    excluded=boot/'fixture-plugins';excluded.mkdir()
    for path in (boot/'plugins').glob('*Probe.jar'):path.rename(excluded/path.name)
    subprocess.run([str(server.java_path().with_name('jar.exe')),'--create','--file',str(boot/'plugins/FKCampaignRestoreProbe.jar'),'-C',str(staging),'.'],check=True,capture_output=True)
    props=boot/'server.properties';props.write_text(re.sub(r'(?m)^query.port=.*$','query.port=25641',props.read_text(encoding='utf-8')),encoding='utf-8')
    histories=list((boot/'plugins/FKAmis/history').glob('*/result.json'))
    if len(histories)!=1:raise RuntimeError('Historique final unique attendu')
    stats_hash=hashlib.sha256(histories[0].read_bytes().removesuffix(b'\n')).hexdigest()
    phase=run_phase(work,boot,'finished-match-restore',0,['-Dfk.campaign.restore=true','-Dfk.campaign.statistics.sha256='+stats_hash],'CAMPAIGN RESTORE SUCCESS',240,25641)
    proof=json.loads((boot/'campaign-restore-result.json').read_text(encoding='utf-8'))
    preservation=compare(original_snapshot,snapshot(boot))
    if inventory(restored)!=before or inventory(source)!=before:raise RuntimeError('Restauration de contrôle ou source modifiée')
    result={'passed':True,'archive':archive.name,'sha256':server.digest(archive),'filesRestoredAndVerified':len(before),'functionalBoot':phase,'restoredGame':proof,'preservation':preservation,'restoreControlUnchanged':True,'sourceUnchanged':True,'historicalBackupUsed':False,'authenticatedClients':0}
    write(work/'finished-match-restore-result.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path);p.add_argument('--restore-finished',action='store_true');a=p.parse_args()
    if a.restore_finished:result=restore_finished(a.work.resolve())
    elif a.source:result=deliver(a.work.resolve(),a.source.resolve())
    else:p.error('--source requis pour la livraison')
    print(json.dumps(result,ensure_ascii=False))
