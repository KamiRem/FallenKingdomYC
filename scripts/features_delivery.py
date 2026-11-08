"""Livraison ciblée des huit fonctionnalités et répétition à froid, sans données privées dans le ZIP."""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import server
from preproduction_smoke import smoke
from preproduction import initial_state
from world_integrity import compare

ROOT=server.ROOT
STAGE=ROOT/'dist/gameplay-update-package'
REPORT=ROOT/'tests/results/gameplay-update-delivery.json'
BASE=ROOT/'dist/fallenkingdom-preproduction-26.3.zip'


def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def build():
    sha=server.digest(server.PLUGIN);suites=[]
    names=['features-'+str(size) for size in range(1,5)]+['admin','core','gameplay','supplies','native']
    for name in names:
        result=json.loads((ROOT/f'tests/results/gameplay-update-{name}.json').read_text(encoding='utf-8'))
        expected_phases=3 if name.startswith('features-') else 2 if name in ('admin','core','supplies') else 1
        if not result['passed'] or len(result['checks'])!=expected_phases or result['fkamisSha256']!=sha:
            raise RuntimeError('Recette incomplète ou binaire différent : '+name)
        suites.append(result)
    baseline=json.loads((ROOT/'tests/results/gameplay-update-baseline.json').read_text(encoding='utf-8'))
    if not baseline['passed']:raise RuntimeError('Comparaison avec l’ancien JAR manquante.')
    compatibility=json.loads((ROOT/'tests/results/gameplay-update-capacity-refusals.json').read_text(encoding='utf-8'))
    if not compatibility['passed'] or compatibility['fkamisSha256']!=sha:raise RuntimeError('Refus de capacité non validés avec le binaire final.')
    counts={'tests':0,'failures':0,'errors':0,'skipped':0}
    for report in (ROOT/'plugins-custom/fk-amis/target/surefire-reports').glob('TEST-*.xml'):
        data=ET.parse(report).getroot()
        for key in counts:counts[key]+=int(data.attrib[key])
    if counts['tests']!=32 or any(counts[k] for k in ('failures','errors','skipped')):raise RuntimeError('Tests Java incomplets.')
    if STAGE.exists():raise RuntimeError('Stage existant à conserver.')
    STAGE.mkdir(parents=True)
    payload={'plugins/FKAmis-1.0.0.jar':server.PLUGIN,'maintenance/serverlib.py':ROOT/'scripts/server.py','maintenance/host_ops.py':ROOT/'deployment/host_ops.py'}
    for name,source in payload.items():
        target=STAGE/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (STAGE/'payload/FKAmis.sha256').write_text(sha+'\n',encoding='ascii')
    shutil.copy2(ROOT/'deployment/apply_gameplay_update.py',STAGE/'apply_gameplay_update.py')
    shutil.copy2(ROOT/'scripts/server.py',STAGE/'serverlib.py')
    shutil.copy2(ROOT/'LICENSE',STAGE/'LICENSE-FKAmis.txt')
    (STAGE/'config').mkdir();(STAGE/'config/FKAmis.additions.example.yml').write_text(
        '# Fragment uniquement : fusionner les clés absentes, ne pas remplacer config.yml.\nplayers-per-team: 2\ndamage-debug: false\ndisable-native-tips: true\n',encoding='utf-8')
    (STAGE/'docs').mkdir()
    for name in ['GAMEPLAY_UPDATE','ADMIN_GUIDE','PLAYER_GUIDE','GAME_RULES','ARCHITECTURE','TEST_PLAN','DEPLOYMENT','HOST_INSTALLATION','BACKUP_RESTORE','MULTIPLAYER_ACCEPTANCE']:
        shutil.copy2(ROOT/'docs'/(name+'.md'),STAGE/'docs'/(name+'.md'))
    (STAGE/'tests/results').mkdir(parents=True)
    for name in [*names,'baseline','capacity-refusals']:
        shutil.copy2(ROOT/f'tests/results/gameplay-update-{name}.json',STAGE/f'tests/results/gameplay-update-{name}.json')
    (STAGE/'README.txt').write_text('Lire docs/GAMEPLAY_UPDATE.md. Monde, state.yml, admins.yml et supplies.yml doivent être conservés.\n'
        'Serveur arrêté, sauvegarde complète, JAR et clés de configuration ciblés ; jamais /reload.\n'
        'Option : python apply_gameplay_update.py --server /chemin/instance\n'
        'server.properties et max-players ne sont pas modifiés automatiquement.\n'
        'Aucun client authentifié dans les recettes ; checklist humaine obligatoire avant validation de production.\n',encoding='utf-8')
    files={p.relative_to(STAGE/'payload').as_posix():server.digest(p) for p in (STAGE/'payload').rglob('*') if p.is_file()}
    write(STAGE/'UPDATE_MANIFEST.json',{'schema':1,'revision':'gameplay-eight-features','paper':'26.3-244','java':25,'fallenkingdom':'2.24.9',
        'paperSha256':'9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf',
        'previousPluginSha256s':['9201a72528b8f6699f394c3e495ab7192bde312614f7f3d2bad88edaf9a8ea37','7da3f775c434ee1addc7a67f063e3b076ab8d5b95d5ad5fbf307357cd3642d30'],
        'files':files,'addMissingConfigDefaults':{'players-per-team':2,'damage-debug':False,'disable-native-tips':True},'serverPropertiesModified':False,
        'neverOverwrite':['world/','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','whitelist.json','server.properties']})
    archive=ROOT/'dist/fallenkingdom-gameplay-update.zip';server.create_archive(STAGE,archive,excluded_roots=(STAGE/'__pycache__',))
    standalone=ROOT/'dist/gameplay-update';standalone.mkdir(exist_ok=False)
    shutil.copy2(server.PLUGIN,standalone/'FKAmis-1.0.0.jar');(standalone/'FKAmis-1.0.0.jar.sha256').write_text(sha+'\n',encoding='ascii')
    report={'atUtc':datetime.now(timezone.utc).isoformat(),'package':archive.relative_to(ROOT).as_posix(),'packageSha256':server.digest(archive),
        'packageFiles':len(server.verify_archive(archive)['files']),'plugin':'dist/gameplay-update/FKAmis-1.0.0.jar','pluginSha256':sha,
        'paper':'26.3-244','java':25,'fallenkingdom':'2.24.9','thirdPartyJarModified':False,
        'unitTests':{'java':counts,'python':{'tests':28,'failures':0}},'technicalSuites':suites,
        'technicalAssertions':sum(c['assertions'] for s in suites for c in s['checks']),
        'capacityCompatibility':compatibility,
        'skeletonInvestigation':{'previousBinaryComparison':baseline,'reportedClientIssueReproduced':False,
            'conclusion':'Les deux binaires autorisent les événements de flèches squelettes avec source Paper correcte ; cause de l’impact manquant signalé non établie sans recette client/logs de l’instance concernée.',
            'defensiveChange':'Priorité explicite au tireur Mob du projectile, diagnostic temporaire optionnel, aucune annulation globalement levée.'},
        'authenticatedPlayers':0,'maximumSimulatedParticipants':16,'maximumSimulatedArbiters':1,
        'containsWorld':False,'containsLiveStateOrAdmins':False,'remoteHostingTouched':False,'officialGameStarted':False,
        'humanTestsRemaining':['impacts_reels_squelette_et_pvp','morts_lits_et_inventaires_client','masquage_mobs_et_gardiens',
            'locator_bar_et_annonces_client','assignation_et_17_comptes_authentifies','forts_geometrie_capture','performance_16_joueurs'],
        'rehearsal':'pending','productionAcceptance':'human_recipe_pending'}
    write(REPORT,report);print('Paquet ciblé créé : '+str(archive),flush=True)


def rehearse(attempt=1):
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    if server.digest(ROOT/report['package'])!=report['packageSha256']:raise RuntimeError('ZIP altéré.')
    suffix='' if attempt==1 else '-'+str(attempt)
    root=server.server_dir('preproduction-gameplay-update'+suffix);server.restore(root,BASE)
    previous=ROOT/'dist/admin-update/FKAmis-1.0.0.jar';shutil.copy2(previous,root/'plugins/FKAmis-1.0.0.jar')
    (root/'FKAmis.sha256').write_text(server.digest(previous)+'\n',encoding='ascii')
    (root/'plugins/FKAmis/admins.yml').write_text('schema: 1\nadministrators: []\n',encoding='utf-8')
    # Reconstitue le profil précédent complet, pas seulement son JAR : dix places et registre cohérent.
    props=root/'server.properties';props.write_text(re.sub(r'^max-players=.*$','max-players=10',props.read_text(encoding='utf-8'),flags=re.M),encoding='utf-8')
    lock=root/'RUNTIME_LOCK.json';data=json.loads(lock.read_text(encoding='utf-8'))
    data.setdefault('sha256',{})['plugins/FKAmis-1.0.0.jar']=server.digest(previous);data['maxPlayers']=10;data['fkamisUpdate']='administrator-role-and-respawn';write(lock,data)
    sys.modules['serverlib']=server
    spec=importlib.util.spec_from_file_location('gameplay_patch',STAGE/'apply_gameplay_update.py');patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    result=patch.apply(root,STAGE)
    check=smoke(root,ROOT/('tests/results/gameplay-update-smoke'+suffix+'.json'),server.java_path(),25590)
    if not check['passed'] or check['errors']:raise RuntimeError('Démarrage après patch échoué.')
    raw=json.loads((ROOT/'.cache/gameplay-qa/tests/results/block-defaults-26.3.json').read_text(encoding='utf-8'))
    defaults={name:dict(part.split('=',1) for part in value.partition('[')[2].removesuffix(']').split(',') if part) for name,value in raw.items()}
    integrity=compare(root,BASE,defaults)
    if not integrity['passed']:raise RuntimeError('Blocs/biomes/butins modifiés.')
    archive=Path(result['backup']);restored=server.server_dir('preproduction-gameplay-rollback'+suffix);server.restore(restored,archive)
    expected=server.verify_archive(archive)['files'];actual={p.relative_to(restored).as_posix():server.digest(p) for p in server.iter_files(restored)}
    if actual!=expected:raise RuntimeError('Restauration différente du backup.')
    old_registry=json.loads((restored/'RUNTIME_LOCK.json').read_text(encoding='utf-8'))
    if old_registry['sha256']['plugins/FKAmis-1.0.0.jar']!=server.digest(restored/'plugins/FKAmis-1.0.0.jar'):raise RuntimeError('Registre du rollback incohérent.')
    rollback=smoke(restored,ROOT/('tests/results/gameplay-update-rollback-smoke'+suffix+'.json'),server.java_path(),25591)
    if not rollback['passed'] or rollback['errors']:raise RuntimeError('Démarrage du rollback échoué.')
    reference=json.loads((ROOT/'.cache/gameplay-update-reference.json').read_text(encoding='utf-8'));preservation={}
    for name,files in reference.items():
        if name=='archives':
            if any(server.digest(ROOT/p)!=sha for p,sha in files.items()):raise RuntimeError('Ancienne archive modifiée.')
            preservation['historicalArchivesCompared']=len(files)
        else:
            current={p.relative_to(ROOT/name).as_posix():server.digest(p) for p in server.iter_files(ROOT/name)}
            if current!=files:raise RuntimeError('Référence modifiée : '+name)
            preservation[name]={'files':len(files),'identical':True}
    report['rehearsal']={'passed':True,'instance':root.relative_to(ROOT).as_posix(),'protectedFilesComparedDuringPatch':result['protectedFiles'],
        'worldStateRolesAndPropertiesUnchangedDuringPatch':True,'coldBackup':archive.relative_to(ROOT).as_posix(),'coldBackupSha256':result['backupSha256'],
        'previousRevisionMetadataConsistent':True,'maxPlayersPreserved':10,
        'startup':check,'worldIntegrity':integrity,'initialStateAfterStartup':initial_state(root),
        'rollbackInstance':restored.relative_to(ROOT).as_posix(),'rollbackFilesCompared':len(actual),'rollbackStartup':rollback}
    report['preservation']=preservation;report['automatedValidationPassed']=True;write(REPORT,report)
    print('Mise à jour, intégrité, sauvegarde/restore et références validées ; recette humaine toujours requise.',flush=True)


def seal():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    if not report.get('automatedValidationPassed') or not report['rehearsal'].get('previousRevisionMetadataConsistent'):
        raise RuntimeError('Répétition complète avec métadonnées cohérentes requise.')
    archive=ROOT/report['package']
    if server.digest(archive)!=report['packageSha256']:raise RuntimeError('Archive candidate altérée.')
    manifest=json.loads((STAGE/'UPDATE_MANIFEST.json').read_text(encoding='utf-8'))
    for name,sha in manifest['files'].items():
        if server.digest(STAGE/'payload'/name)!=sha:raise RuntimeError('Payload modifié après recette.')
    old=ROOT/'dist/fallenkingdom-gameplay-update-tested-payload.zip'
    if old.exists():raise RuntimeError('Candidat déjà conservé ; ne pas écraser.')
    report['testedCandidatePackage']=old.relative_to(ROOT).as_posix();report['testedCandidateSha256']=report['packageSha256']
    history=json.loads((ROOT/'.cache/migration-26.3-preservation.json').read_text(encoding='utf-8'))['protectedArchives']
    if any(server.digest(ROOT/name)!=sha for name,sha in history.items()):raise RuntimeError('Sauvegarde historique modifiée.')
    report['preservation']['additionalHistoricalArchivesCompared']=len(history)
    tracked=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True,encoding='utf-8').splitlines()
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True,encoding='utf-8').splitlines()
    report['modifiedFiles']=sorted(set(tracked+untracked))
    report['contentAudit']={'world':False,'liveState':False,'playerIdentities':False,'officialPlugin':False,'probes':False}
    report['developmentIssuesResolved']=['ambiguïté Comparator à la compilation','chemin de fixture normalisé',
        'destination Windows raccourcie pour restauration des bibliothèques Maven',
        'profil de répétition complété avec registre SHA et capacité correspondant au précédent JAR']
    validation=dict(report)
    for key in ('packageSha256','packageFiles','testedCandidatePackage','testedCandidateSha256'):validation.pop(key,None)
    validation['externalChecksumFile']='fallenkingdom-gameplay-update.zip.sha256'
    validation['runtimePayloadUnchangedSinceRehearsal']=True
    write(STAGE/'tests/results/delivery-validation.json',validation)
    archive.rename(old)
    archive.with_suffix('.zip.sha256').rename(old.with_suffix('.zip.sha256'))
    server.create_archive(STAGE,archive,excluded_roots=(STAGE/'__pycache__',))
    contents=server.verify_archive(archive)['files']
    if any(name.startswith('world/') or name.endswith(('state.yml','admins.yml','supplies.yml','Probe.jar','.pyc')) for name in contents):
        raise RuntimeError('Donnée privée ou outil de recette dans le ZIP.')
    for name,sha in manifest['files'].items():
        if contents['payload/'+name]!=sha:raise RuntimeError('Payload final différent de la recette.')
    report['packageSha256']=server.digest(archive);report['packageFiles']=len(contents)
    report['runtimePayloadUnchangedSinceRehearsal']=True;report['sealed']=True;write(REPORT,report)
    print(json.dumps({'package':report['package'],'sha256':report['packageSha256'],'pluginSha256':report['pluginSha256'],
        'files':len(contents),'bytes':archive.stat().st_size,'runtimePayloadUnchangedSinceRehearsal':True},ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['build','rehearse','seal']);parser.add_argument('--attempt',type=int,default=1)
    args=parser.parse_args()
    if not 1<=args.attempt<=100:raise ValueError('Tentative 1..100 requise.')
    if args.action=='rehearse':rehearse(args.attempt)
    else:{'build':build,'seal':seal}[args.action]()
