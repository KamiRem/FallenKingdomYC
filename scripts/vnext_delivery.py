"""Livraison VNext ciblée, répétition à froid et scellement après contrôle des preuves."""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import server
from preproduction_smoke import smoke
from world_integrity import compare

sys.dont_write_bytecode=True

ROOT=server.ROOT;QA=ROOT/'.cache/vn';STAGE=ROOT/'dist/vnext-update-package';REPORT=ROOT/'tests/results/vnext-delivery.json'
PREVIOUS='83e721d8ac12feefdb590976747f88d6825b3243976c7e9f10b1cc35fac5239d'


def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def files(root):return {p.relative_to(root).as_posix():server.digest(p) for p in server.iter_files(root)}


def prepare():
    if STAGE.exists():raise RuntimeError('Stage existant à conserver ; ne pas écraser une livraison en cours.')
    STAGE.mkdir(parents=True);sha=server.digest(server.PLUGIN)
    sources={'plugins/FKAmis-1.0.0.jar':server.PLUGIN,'maintenance/serverlib.py':ROOT/'scripts/server.py',
             'maintenance/host_ops.py':ROOT/'deployment/host_ops.py','maintenance/new_match.py':ROOT/'deployment/new_match.py',
             'maintenance/map_reader.py':ROOT/'scripts/map_reader.py','maintenance/new-match-reference.json':ROOT/'configs/vnext/new-match-reference.json'}
    for name,source in sources.items():
        target=STAGE/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (STAGE/'payload/FKAmis.sha256').write_text(sha+'\n',encoding='ascii')
    shutil.copy2(ROOT/'deployment/apply_vnext_update.py',STAGE/'apply_vnext_update.py');shutil.copy2(ROOT/'scripts/server.py',STAGE/'serverlib.py')
    shutil.copy2(ROOT/'LICENSE',STAGE/'LICENSE-FKAmis.txt')
    (STAGE/'config').mkdir();(STAGE/'config/FKAmis.additions.example.yml').write_text('# Fusionner seulement les clés absentes ; ne pas remplacer config.yml.\nrespawn-protection-seconds: 5\n',encoding='utf-8')
    (STAGE/'docs').mkdir()
    for name in ('FKAMIS_VNEXT','ADMIN_GUIDE','GAME_RULES','ARCHITECTURE','TEST_PLAN','DEPLOYMENT','BACKUP_RESTORE','HOST_INSTALLATION','MULTIPLAYER_ACCEPTANCE','PLAYER_GUIDE'):
        shutil.copy2(ROOT/'docs'/(name+'.md'),STAGE/'docs'/(name+'.md'))
    (STAGE/'README.txt').write_text('Lire docs/FKAMIS_VNEXT.md avant installation. Serveur arrêté, sauvegarde complète, aucun /reload.\n'
        'python apply_vnext_update.py --server /chemin/instance\n'
        'Conserver monde, state.yml, admins.yml, supplies.yml, port 22880, Paper 26.3-244 et Java 25.\n'
        'Révision précédente autorisée : '+PREVIOUS+'\n'
        'Rollback : restaurer la sauvegarde entière dans un dossier neuf. Recette humaine multijoueur requise.\n',encoding='utf-8')
    write(STAGE/'UPDATE_MANIFEST.json',{'schema':1,'revision':'fkamis-vnext','paper':'26.3-244','java':25,'fallenkingdom':'2.24.9',
        'paperSha256':'9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf',
        'previousPluginSha256s':[PREVIOUS],'files':files(STAGE/'payload'),'stateSchema':1,'vnextExtensionVersion':1,
        'addMissingConfigDefaults':{'players-per-team':2,'damage-debug':False,'disable-native-tips':True,'respawn-protection-seconds':5},
        'serverPropertiesModified':False,'neverOverwrite':['world/','world_nether/','world_the_end/','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','server.properties','whitelist.json']})
    server.create_archive(STAGE,QA/'vnext-tested-payload.zip')
    print('Candidat préparé ; payload figé, recette puis rapport nécessaires.',flush=True)


def rehearse(attempt,resume=False):
    sys.dont_write_bytecode=True;sys.modules['serverlib']=server
    spec=importlib.util.spec_from_file_location('vnext_patch',STAGE/'apply_vnext_update.py');patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    manifest=read(STAGE/'UPDATE_MANIFEST.json');sha=server.digest(server.PLUGIN)
    if manifest['files']['plugins/FKAmis-1.0.0.jar']!=sha:raise RuntimeError('Binaire changé après préparation.')
    reference=ROOT/'runtime/preproduction-gameplay-update-2';archive=QA/f'gameplay-reference-{attempt}.zip'
    root=QA/'runtime'/f'preproduction-vnext-update-{attempt}'
    with server.maintenance(reference):
        if server.digest(reference/'plugins/FKAmis-1.0.0.jar')!=PREVIOUS:raise RuntimeError('La référence gameplay doit correspondre à 83e721.')
        original=files(reference)
        if resume:
            expected=server.verify_archive(archive)['files']
            if any(original.get(name)!=value for name,value in expected.items()):raise RuntimeError('Référence différente de l’archive préparée.')
        else:server.create_archive(reference,archive,excluded_roots=tuple(reference/name for name in ('.fk-updates','.fk-backups','.fk-resets')))
        if files(reference)!=original:raise RuntimeError('Référence historique modifiée.')
    if resume:
        with server.maintenance(root):
            if server.digest(root/'plugins/FKAmis-1.0.0.jar')!=PREVIOUS:raise RuntimeError('Reprise réservée à une fixture préparée avant application.')
        preparation=read(ROOT/f'tests/results/vnext-fixture-preparation-{attempt}.json')
    else:
        server.restore(root,archive)
        preparation=smoke(root,ROOT/f'tests/results/vnext-fixture-preparation-{attempt}.json',server.java_path(),25589,
                          fixture_commands=('gamerule minecraft:random_tick_speed 0',))
    preparation_log=(ROOT/f'tests/results/vnext-fixture-preparation-{attempt}.log').read_text(encoding='utf-8')
    if not preparation['passed'] or 'now set to 0' not in preparation_log:raise RuntimeError('Contrôle des ticks aléatoires de fixture non appliqué.')
    # Injecter les sentinelles après le dernier démarrage de l'ancien JAR : cette
    # recette vérifie leur migration par VNext, pas le sérialiseur historique.
    with server.maintenance(root):
        for name,line in [('config.yml','\ncustom-vnext-migration: conserver\n'),('supplies.yml','\ncustom-vnext-migration: conserver\n'),('state.yml','\ncustom-vnext-migration:\n  keep: 42\n')]:
            path=root/'plugins/FKAmis'/name;text=path.read_text(encoding='utf-8')
            if 'custom-vnext-migration:' not in text:path.write_text(text+line,encoding='utf-8')
    result=patch.apply(root,STAGE)
    startup=smoke(root,ROOT/f'tests/results/vnext-update-smoke-{attempt}.json',server.java_path(),25589,settle_seconds=30)
    if not startup['passed'] or startup['errors']:raise RuntimeError('Démarrage après mise à jour échoué.')
    state=(root/'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
    if 'custom-vnext-migration:' not in state or '  keep: 42' not in state or 'vnext:' not in state:raise RuntimeError('Migration additive non conservatrice.')
    raw=read(ROOT/'.cache/gameplay-qa/tests/results/block-defaults-26.3.json')
    defaults={name:dict(part.split('=',1) for part in value.partition('[')[2].removesuffix(']').split(',') if part) for name,value in raw.items()}
    integrity=compare(root,Path(result['backup']),defaults)
    if not integrity['passed']:raise RuntimeError('Blocs, biomes ou inventaires de coffres modifiés.')
    backup=Path(result['backup']);rollback=QA/'runtime'/f'preproduction-vnext-rollback-{attempt}';server.restore(rollback,backup)
    actual=files(rollback);expected=server.verify_archive(backup)['files']
    if actual!=expected:raise RuntimeError('Retour arrière différent de la sauvegarde entière.')
    registry=read(rollback/'RUNTIME_LOCK.json')
    if registry['sha256']['plugins/FKAmis-1.0.0.jar']!=PREVIOUS:raise RuntimeError('Ancien registre incohérent.')
    rollback_startup=smoke(rollback,ROOT/f'tests/results/vnext-rollback-smoke-{attempt}.json',server.java_path(),25591)
    if not rollback_startup['passed'] or rollback_startup['errors']:raise RuntimeError('Démarrage du rollback échoué.')
    result.update({'passed':True,'fkamisSha256':sha,'instance':root.relative_to(ROOT).as_posix(),'referenceFilesUnchanged':len(original),
        'startup':startup,'worldIntegrity':integrity,'unknownStateFieldPreserved':True,'rollbackInstance':rollback.relative_to(ROOT).as_posix(),
        'fixtureRandomTickSpeed':0,'fixturePreparation':preparation,'productionRandomTickSpeedChangedByUpdater':False,
        'rollbackFilesCompared':len(actual),'rollbackStartup':rollback_startup,'rollbackPluginSha256':PREVIOUS,'serverPortChangedByUpdater':False})
    write(ROOT/'tests/results/vnext-update-rollback.json',result);print('Mise à jour, migration additive et rollback entier validés.',flush=True)


def inventory(attempt):
    source=QA/'runtime'/f'pve-fixed-{attempt}';destination=QA/'runtime'/f'pve-inventory-restored-{attempt}';archive=QA/f'pve-inventory-{attempt}.zip'
    if server.digest(source/'plugins/FKAmis-1.0.0.jar')!=server.digest(server.PLUGIN):raise RuntimeError('Corps physique issu d’un autre binaire.')
    import gzip
    from map_reader import nbt
    with server.maintenance(source):
        player_files=list((source/'world/players/data').glob('*.dat'))+list((source/'world/playerdata').glob('*.dat'))
        if not player_files:raise RuntimeError('Profil NMS sauvegardé absent.')
        observed=[]
        for path in player_files:
            data=nbt(gzip.decompress(path.read_bytes()));items=data.get('Inventory',data.get('inventory',[]))
            for item in items:
                if item.get('id')=='minecraft:bread' and item.get('count',item.get('Count'))==7:observed.append(path)
        if len(observed)!=1:raise RuntimeError('Sept pains du corps physique non retrouvés dans son profil.')
        server.create_archive(source,archive,excluded_roots=tuple(source/name for name in ('.fk-updates','.fk-backups','.fk-resets')))
        before={p.relative_to(source).as_posix():server.digest(p) for p in player_files}
    server.restore(destination,archive)
    if any(server.digest(destination/name)!=sha for name,sha in before.items()):raise RuntimeError('Inventaire différent après restauration entière.')
    result={'passed':True,'fkamisSha256':server.digest(server.PLUGIN),'authenticatedClients':0,'realNmsProfile':True,
        'inventoryItem':'minecraft:bread','inventoryCount':7,'profileFilesCompared':len(before),'backupSha256':server.digest(archive),'allRestoredFilesCompared':len(files(destination))}
    if files(destination)!=server.verify_archive(archive)['files']:raise RuntimeError('Restauration complète différente.')
    write(ROOT/'tests/results/vnext-inventory-restore.json',result);print('Profil et inventaire NMS conservés par restauration complète.',flush=True)


def preserve():
    result={};reference=read(ROOT/'.cache/gameplay-update-reference.json')
    for name,expected in reference.items():
        if name=='archives':
            for path,sha in expected.items():
                if server.digest(ROOT/path)!=sha:raise RuntimeError('Ancienne archive modifiée : '+path)
            result['historicalArchivesCompared']=len(expected)
        else:
            if files(ROOT/name)!=expected:raise RuntimeError('Référence historique modifiée : '+name)
            result[name]={'files':len(expected),'identical':True}
    extra=read(ROOT/'.cache/migration-26.3-preservation.json')['protectedArchives']
    for name,sha in extra.items():
        if server.digest(ROOT/name)!=sha:raise RuntimeError('Archive de migration modifiée : '+name)
    base=read(ROOT/'.cache/vnext-base.json')
    for name,sha in base['archives'].items():
        if server.digest(ROOT/name)!=sha:raise RuntimeError('Archive de base VNext modifiée : '+name)
    if server.digest(ROOT/'dist/gameplay-update/FKAmis-1.0.0.jar')!=PREVIOUS:raise RuntimeError('Ancien JAR gameplay modifié.')
    result['additionalHistoricalArchivesCompared']=len(extra);result['vnextBaseArchivesCompared']=len(base['archives']);return result


def reset_rollback():
    result=read(ROOT/'tests/results/vnext-reset-restore.json');backup=Path(result['logical']['backup'])
    root=QA/'runtime'/'preproduction-vnext-reset-rollback-3';server.restore(root,backup)
    expected=server.verify_archive(backup)['files'];before=files(root)
    if before!=expected:raise RuntimeError('Retour avant reset différent de la sauvegarde complète.')
    sys.modules['serverlib']=server
    spec=importlib.util.spec_from_file_location('reset_maintenance',STAGE/'payload/maintenance/new_match.py');maintenance=importlib.util.module_from_spec(spec);spec.loader.exec_module(maintenance)
    maintenance.cancel(root);after=files(root)
    remaining={name:sha for name,sha in before.items() if name not in ('plugins/FKAmis/reset-request.json','plugins/FKAmis/reset-candidate.yml')}
    if remaining!=after:raise RuntimeError('Annulation a modifié des données autres que la demande.')
    startup=smoke(root,ROOT/'tests/results/vnext-reset-rollback-smoke.json',server.java_path(),25597,expected_day=3)
    if not startup['passed'] or startup['errors']:raise RuntimeError('Retour à la partie avant reset non démarrable.')
    result['resetRollback']={'passed':True,'allRestoredFilesCompared':len(before),'onlyPendingRequestAndCandidateRemoved':True,'startup':startup}
    write(ROOT/'tests/results/vnext-reset-restore.json',result);print('Restauration du point avant reset et annulation de demande validées.',flush=True)


def seal():
    sha=server.digest(server.PLUGIN);manifest=read(STAGE/'UPDATE_MANIFEST.json')
    if manifest['files']!=files(STAGE/'payload'):raise RuntimeError('Payload différent de celui testé.')
    suites=[]
    for name in ['admin','core','gameplay','supplies','native','features-1','features-2','features-3','features-4','vnext']:
        result=read(ROOT/f'tests/results/vnext-{name}.json');phases=3 if name.startswith('features') or name=='vnext' else 2 if name in ('admin','core','supplies') else 1
        if not result.get('passed') or result.get('fkamisSha256')!=sha or len(result['checks'])!=phases:raise RuntimeError('Recette finale incomplète : '+name)
        suites.append(result)
    evidence={}
    for name in ('physics-fixed','reset-restore','inventory-restore','update-rollback','refusals'):
        result=read(ROOT/f'tests/results/vnext-{name}.json')
        if not result.get('passed') or result.get('fkamisSha256')!=sha:raise RuntimeError('Preuve finale manquante : '+name)
        evidence[name]=result
    baseline=read(ROOT/'tests/results/vnext-physics-baseline.json')
    if not baseline['passed'] or baseline['fkamisSha256']!=PREVIOUS:raise RuntimeError('Reproduction causale absente.')
    counts={'tests':0,'failures':0,'errors':0,'skipped':0}
    for path in (ROOT/'plugins-custom/fk-amis/target/surefire-reports').glob('TEST-*.xml'):
        data=ET.parse(path).getroot()
        for key in counts:counts[key]+=int(data.attrib[key])
    if counts['tests']!=46 or any(counts[k] for k in ('failures','errors','skipped')):raise RuntimeError('Tests Java incomplets.')
    unit=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,capture_output=True,text=True)
    (QA/'tests/results/python-final.log').write_text(unit.stdout+unit.stderr,encoding='utf-8')
    if unit.returncode:raise RuntimeError('Tests Python en échec.')
    import re
    python_tests=int(re.search(r'Ran (\d+) tests',unit.stderr).group(1))
    preservation=preserve();performance=read(QA/'tests/results/vnext-performance.json')
    performance['metricsIncludeStartupAndSynchronousFixtureWork']=True
    performance['idleMeasurement']='Voir updateAndRollback.startup : stabilisation séparée de trente secondes, zéro joueur authentifié.'
    report={'atUtc':datetime.now(timezone.utc).isoformat(),'branch':'feature/fkamis-vnext','baseCommit':'fb17bc0','previousPluginSha256':PREVIOUS,
        'package':'dist/fallenkingdom-vnext-update.zip','plugin':'dist/vnext/FKAmis-1.0.0.jar','pluginSha256':sha,
        'paper':'26.3-244','java':25,'fallenkingdom':'2.24.9','thirdPartyJarModified':False,'remoteHostingTouched':False,
        'unitTests':{'java':counts,'python':{'tests':python_tests,'failures':0}},'technicalSuites':suites,
        'technicalAssertions':sum(c['assertions'] for s in suites for c in s['checks'])+evidence['reset-restore']['logicalRestart']['assertions'],
        'skeletonDiagnosis':{'cause':'ItemBan réécrivait l’arc inchangé chaque seconde ; onEquipItem/reassessWeaponGoal réinitialisait le cycle IA avant le tir.',
            'correction':'Nettoyage sur clone, écriture seulement des cases et équipements modifiés, protections de dégâts conservées.','baseline':baseline,'fixed':evidence['physics-fixed']},
        'features':{'reset':'implemented_and_cold_rehearsed','captureUi':'implemented_technical_tests_human_ui_pending','placesAndRespawn':'implemented',
            'configuration':'implemented_atomic_journal','statistics':'implemented_uuid_versioned_history','information':'implemented_shared_state_no_secret_positions'},
        'resetAndRestore':evidence['reset-restore'],'inventoryRestoration':evidence['inventory-restore'],'updateAndRollback':evidence['update-rollback'],
        'startupRefusals':evidence['refusals'],
        'technicalPerformance':performance,'preservation':preservation,'authenticatedPlayers':0,'maximumSimulatedParticipants':16,
        'containsWorld':False,'containsLiveStateOrAdmins':False,'containsProbePlugins':False,'officialGameStarted':False,
        'migration':{'stateSchema':1,'extensionVersion':1,'additive':True,'unknownFieldsPreserved':True,'futureVersionRefused':True,'fullColdBackupRequired':True},
        'humanTestsRemaining':['connexions_authentifiees_4_a_16_et_arbitre','tirs_arc_client_et_sante_armures','bossbar_titres_sons_alertes_defenseurs',
            'respawn_lits_inventaires_reconnexion','inspection_visuelle_7_monuments_8_sites_et_salles','approbation_humaine_reference_initiale',
            'tps_mspt_ram_ping_charge_sur_hebergement'],'productionAcceptance':'human_recipe_pending','automatedValidationPassed':True,
        'documentation':'docs/FKAMIS_VNEXT.md','rollback':'Sauvegarde complète avant mise à jour, restauration entière dans une destination neuve, même Paper 26.3-244.'}
    report['commandsAdded']=['reset status|prepare|confirm <token>|cancel','config list|get|set|validate|defaults|diff','stats [match|player pseudo|team équipe|leaderboard]','info [teams|phases|supplies]']
    report['newConfigKey']={'respawn-protection-seconds':5};report['existingParametersReused']=True
    report['testedPayloadArchiveSha256']=server.digest(QA/'vnext-tested-payload.zip');report['runtimePayloadUnchangedSinceRehearsal']=True
    tracked=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines();new=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    report['modifiedFiles']=sorted(set(tracked+new+['tests/results/vnext-delivery.json']))
    (STAGE/'tests/results').mkdir(parents=True)
    for source in (ROOT/'tests/results').glob('vnext-*.json'):
        if source.name!='vnext-delivery.json':shutil.copy2(source,STAGE/'tests/results'/source.name)
    for target in (STAGE/'docs').glob('*.md'):shutil.copy2(ROOT/'docs'/target.name,target)
    if server.digest(STAGE/'apply_vnext_update.py')!=server.digest(ROOT/'deployment/apply_vnext_update.py'):raise RuntimeError('Script d’installation modifié après sa recette.')
    write(STAGE/'tests/results/delivery-validation.json',report)
    archive=ROOT/report['package'];server.create_archive(STAGE,archive,excluded_roots=(STAGE/'__pycache__',))
    contents=server.verify_archive(archive)['files']
    if any(name.startswith(('world/','world_nether/','world_the_end/')) or name.endswith(('state.yml','admins.yml','supplies.yml','Probe.jar','.pyc')) or '__pycache__' in name for name in contents):raise RuntimeError('Donnée privée ou plugin de recette dans le ZIP.')
    standalone=ROOT/'dist/vnext';standalone.mkdir(exist_ok=False);shutil.copy2(server.PLUGIN,standalone/'FKAmis-1.0.0.jar');(standalone/'FKAmis-1.0.0.jar.sha256').write_text(sha+'\n',encoding='ascii')
    report.update({'packageSha256':server.digest(archive),'packageFiles':len(contents),'packageBytes':archive.stat().st_size,'sealed':True})
    write(REPORT,report);print(json.dumps({key:report[key] for key in ('package','packageSha256','pluginSha256','technicalAssertions','packageFiles')},ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','rehearse','inventory','reset-rollback','seal'));parser.add_argument('--attempt',type=int,default=1);parser.add_argument('--resume-prepared',action='store_true');args=parser.parse_args()
    if args.action=='rehearse':rehearse(args.attempt,args.resume_prepared)
    elif args.action=='inventory':inventory(args.attempt)
    else:{'prepare':prepare,'seal':seal,'reset-rollback':reset_rollback}[args.action]()
