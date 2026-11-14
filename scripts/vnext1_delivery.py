"""Livraison VNext.1 : recettes à froid isolées, conservation et artefacts séparés."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
import server
from preproduction_smoke import smoke
from map_v21_verify import verify
from map_reader import nbt

ROOT=server.ROOT;QA=ROOT/'.cache/vn1';STAGE=ROOT/'dist/vnext1-update-package'
sys.path.insert(0,str(ROOT/'deployment'));sys.modules['serverlib']=server
import new_match as reset
import territory_migration as territories
import apply_vnext1_update as patch
PREVIOUS=patch.PREVIOUS
DEFAULTS=ROOT/'.cache/gameplay-qa/tests/results/block-defaults-26.3.json'
REFERENCE=ROOT/'configs/vnext1/new-match-reference.json'

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def files(root):return {p.relative_to(root).as_posix():server.digest(p) for p in server.iter_files(root)}
def result(name,data):write(ROOT/'tests/results'/('vnext1-'+name+'.json'),data)
def startup(root,name,day=0,settle=0,commands=()):
    data=smoke(root,ROOT/'tests/results'/('vnext1-'+name+'.json'),server.java_path(),25608,settle_seconds=settle,expected_day=day,fixture_commands=commands)
    if not data['passed'] or data['errors']:raise RuntimeError('Démarrage échoué : '+name)
    return data
def registry(root,sha):
    shutil.copy2(server.PLUGIN,root/'plugins/FKAmis-1.0.0.jar');(root/'FKAmis.sha256').write_text(sha+'\n',encoding='ascii')
    lock=read(root/'RUNTIME_LOCK.json');lock['sha256']['plugins/FKAmis-1.0.0.jar']=sha;write(root/'RUNTIME_LOCK.json',lock)
def dependencies(root):
    for folder in ('libraries','versions','cache'):
        if not (root/folder).exists() and (ROOT/'runtime/preproduction-26-3'/folder).exists():shutil.copytree(ROOT/'runtime/preproduction-26-3'/folder,root/folder)
def prepare():
    if STAGE.exists():raise RuntimeError('Candidat existant, ne pas écraser.')
    STAGE.mkdir(parents=True);sha=server.digest(server.PLUGIN)
    sources={'plugins/FKAmis-1.0.0.jar':server.PLUGIN,'maintenance/serverlib.py':ROOT/'scripts/server.py',
      'maintenance/host_ops.py':ROOT/'deployment/host_ops.py','maintenance/new_match.py':ROOT/'deployment/new_match.py',
      'maintenance/map_reader.py':ROOT/'scripts/map_reader.py','maintenance/new-match-reference.json':REFERENCE,
      'maintenance/territory_migration.py':ROOT/'deployment/territory_migration.py'}
    for name,source in sources.items():
        target=STAGE/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (STAGE/'payload/FKAmis.sha256').write_text(sha+'\n',encoding='ascii')
    for source,name in [('deployment/apply_vnext1_update.py','apply_vnext1_update.py'),('scripts/server.py','serverlib.py'),('deployment/territory_migration.py','territory_migration.py'),('LICENSE','LICENSE-FKAmis.txt')]:shutil.copy2(ROOT/source,STAGE/name)
    write(STAGE/'UPDATE_MANIFEST.json',{'schema':1,'revision':'fkamis-vnext.1','paper':'26.3-244','java':25,'fallenkingdom':'2.24.9',
      'paperSha256':patch.PAPER,'previousPluginSha256s':[PREVIOUS],'files':files(STAGE/'payload'),'stateSchema':1,'vnextExtensionVersion':2,
      'territoryRadius':40,'onlyServerPropertyChanged':'allow-flight=true','cavernGeneration':False,
      'preserved':['worlds','player profiles','UUIDs','admins','objectives','statistics','history','supplies','host port and memory']})
    print('Candidat VNext.1 préparé : '+sha,flush=True)

def migration():
    source=Path(read(ROOT/'tests/results/vnext-reset-restore.json')['logical']['backup']);root=QA/'runtime/preproduction-vnext1-update-3'
    server.restore(root,source);reset.cancel(root)
    with server.maintenance(root):
        for probe in (root/'plugins').glob('*Probe.jar'):probe.unlink()
        assert server.digest(root/'plugins/FKAmis-1.0.0.jar')==PREVIOUS
        lock=read(root/'RUNTIME_LOCK.json');lock['sha256']['plugins/FKAmis-1.0.0.jar']=PREVIOUS;write(root/'RUNTIME_LOCK.json',lock)
    preparation=startup(root,'migration-before',3,commands=('gamerule minecraft:random_tick_speed 0',))
    with server.maintenance(root):
        for name,sentinel in [('config.yml','\ncustom-vnext1: conserver\n'),('supplies.yml','\ncustom-vnext1: conserver\n'),('state.yml','\ncustom-vnext1:\n  keep: 42\n')]:
            path=root/'plugins/FKAmis'/name;path.write_text(path.read_text(encoding='utf-8')+sentinel,encoding='utf-8')
        before_props=server.properties(root/'server.properties')
    # Refus d'un objectif hors territoire avant toute sauvegarde/écriture.
    state=root/'plugins/FKAmis/state.yml';original=state.read_bytes();text=original.decode('utf-8')
    start=text.index('\nobjectives:');end=text.find('\nspawns:',start)
    objective=text[start:end if end!=-1 else len(text)]
    match=re.search(r'^    x: ([-\d.]+)',objective,re.M)
    if not match:raise RuntimeError('Fixture sans objectif pour la garde de migration.')
    at=start+match.start(1);bad=text[:at]+str(float(match.group(1))+1000)+text[start+match.end(1):]
    with server.maintenance(root):state.write_text(bad,encoding='utf-8')
    before=files(root)
    try:patch.apply(root,STAGE)
    except RuntimeError as e:
        if 'hors du nouveau' not in str(e).lower():raise
    else:raise AssertionError('Objectif hors 40 accepté')
    assert before==files(root),'Écriture lors du refus'
    with server.maintenance(root):state.write_bytes(original)
    update=patch.apply(root,STAGE);backup=Path(update['backup'])
    assert server.properties(root/'server.properties')=={**before_props,'allow-flight':'true'}
    after=startup(root,'migration-after',3,settle=30)
    content=state.read_text(encoding='utf-8');assert 'custom-vnext1:' in content and '  keep: 42' in content
    assert territories.get(content,'vnext','version')=='2'
    integrity=verify(root,backup,DEFAULTS,{'blocks':[],'chunks':[],'caverns':[]});assert integrity['passed'],integrity['errors']
    rollback=QA/'runtime/preproduction-vnext1-rollback-3';server.restore(rollback,backup)
    restored=files(rollback);assert restored==server.verify_archive(backup)['files']
    assert read(rollback/'RUNTIME_LOCK.json')['sha256']['plugins/FKAmis-1.0.0.jar']==PREVIOUS
    old=startup(rollback,'rollback-startup',3)
    result('update-rollback',{'passed':True,'fkamisSha256':server.digest(server.PLUGIN),'sourcePluginSha256':PREVIOUS,'sourceBackupSha256':server.digest(source),
      'update':update,'preparation':preparation,'startup':after,'worldIntegrity':integrity,'unknownStateFieldPreserved':True,'outOfBoundsObjectiveRefusedWithoutWrites':True,
      'onlyAllowFlightPropertyChanged':True,'beforeMigrationFixtureRegistryReconciled':True,'rollbackEntireManifestCompared':len(restored),'rollbackStartup':old,'authenticatedPlayers':0})

def inventory():
    archive=ROOT/'.cache/vn/pve-inventory-6.zip';root=QA/'runtime/preproduction-vnext1-inventory-1';server.restore(root,archive)
    with server.maintenance(root):
        for probe in (root/'plugins').glob('*Probe.jar'):probe.unlink()
        assert server.digest(root/'plugins/FKAmis-1.0.0.jar')==PREVIOUS
        lock=read(root/'RUNTIME_LOCK.json');lock['sha256']['plugins/FKAmis-1.0.0.jar']=PREVIOUS;write(root/'RUNTIME_LOCK.json',lock)
        profiles={p.relative_to(root).as_posix():server.digest(p) for p in root.rglob('*.dat') if '/players/data/' in p.as_posix() or '/playerdata/' in p.as_posix()}
        breads=0
        for name in profiles:
            d=nbt(gzip.decompress((root/name).read_bytes()))
            breads+=sum(item.get('id')=='minecraft:bread' and item.get('count',item.get('Count'))==7 for item in d.get('Inventory',d.get('inventory',[])))
        assert breads==1 and profiles
    update=patch.apply(root,STAGE);assert all(server.digest(root/name)==sha for name,sha in profiles.items())
    dest=QA/'runtime/preproduction-vnext1-inventory-rollback-1';server.restore(dest,Path(update['backup']));restored=files(dest)
    assert restored==server.verify_archive(Path(update['backup']))['files']
    result('inventory-restore',{'passed':True,'fkamisSha256':server.digest(server.PLUGIN),'authenticatedClients':0,'realNmsProfile':True,'inventoryItem':'minecraft:bread','inventoryCount':7,
      'profileFilesCompared':len(profiles),'beforeMigrationFixtureRegistryReconciled':True,'allRestoredFilesCompared':len(restored),'update':update})

def map_restore():
    root=QA/'runtime/map-v21-built-3';ref=root/'maintenance/new-match-reference-v2.1.json';archive=QA/'map-v21-initial-1.zip'
    approval=reset.seal_baseline(root,archive,ref,True)
    dest=QA/'runtime/preproduction-map-v21-restored-1';server.restore(dest,archive)
    restored=files(dest);assert restored==server.verify_archive(archive)['files']
    boot=startup(dest,'map-restored-startup')
    with server.maintenance(dest):checks=reset.initial_checks(dest,dest/'maintenance/new-match-reference-v2.1.json')
    oldarchive=ROOT/'.cache/vn/vnext-initial-3.zip';old=QA/'runtime/preproduction-map-v2-rollback-1';server.restore(old,oldarchive)
    oldfiles=files(old);assert oldfiles==server.verify_archive(oldarchive)['files']
    assert server.digest(old/'plugins/FKAmis-1.0.0.jar')==PREVIOUS
    oldboot=startup(old,'map-v2-rollback-startup')
    result('map-restore',{'passed':True,'fkamisSha256':server.digest(server.PLUGIN),'testFixtureApprovalOnly':True,'visualInspection':False,
      'sealedReferenceSha256':approval['sha256'],'allRestoredFilesCompared':len(restored),'initialChecksAfterStartup':checks,'startup':boot,
      'vnextV2ReferenceSha256':server.digest(oldarchive),'vnextV2EntireManifestCompared':len(oldfiles),'vnextV2RollbackStartup':oldboot})

def probe_phase(root,phase):
    with server.maintenance(root):shutil.copy2(ROOT/'.cache/FKVNextProbe.jar',root/'plugins/FKVNextProbe.jar')
    with server.maintenance(root,check_worlds=False):
        process=subprocess.Popen([str(server.java_path()),'-Xms1G','-Xmx4G','-Dfk.vnext=true','-Dfk.vnext1=true','-Dfk.vnext.phase='+str(phase),'-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25607'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        try:log,_=process.communicate(timeout=240)
        except subprocess.TimeoutExpired:log,_=process.communicate(input='stop\n',timeout=120)
    (QA/('reset-phase-'+str(phase)+'.log')).write_text(log,encoding='utf-8')
    errors=[line for line in log.splitlines() if re.search(r'\b(ERROR|SEVERE)\b',line)]
    assert process.returncode==0 and 'VNEXT PROBE SUCCESS' in log and not errors,errors
    with server.maintenance(root):(root/'plugins/FKVNextProbe.jar').unlink()
    return {'passed':True,'assertions':log.count('PROBE PASS '),'errors':errors}

def resets():
    root=QA/'runtime/probe-vnext-reset-2';baseline=QA/'runtime/preproduction-vnext1-initial-2';archive=QA/'vnext1-initial-2.zip'
    receipts=[read(p) for p in (QA/'runtime/probe-vnext-1/.fk-resets').glob('receipt-*.json')]
    source=next(r['backup'] for r in receipts if r['operation']=='logical')
    server.restore(root,Path(source))
    server.restore(baseline,ROOT/'dist/fallenkingdom-preproduction-26.3.zip')
    with server.maintenance(baseline):
        registry(baseline,server.digest(server.PLUGIN));dependencies(baseline)
        state=baseline/'plugins/FKAmis/state.yml';text,_=territories.migrate(state.read_text(encoding='utf-8'));state.write_text(text,encoding='utf-8')
        metadata=read(baseline/'map-v2-construction.json')
        for b in metadata['bases']:b['radius']=40
        write(baseline/'map-v2-construction.json',metadata)
        for name in reset.POLICY_FILES:
            if (root/name).is_file():shutil.copy2(root/name,baseline/name)
    startup(baseline,'initial-smoke')
    with server.maintenance(baseline):
        text=(root/'server.properties').read_text(encoding='utf-8');text=re.sub(r'^server-port=.*$','server-port=25607',text,flags=re.M)
        (baseline/'server.properties').write_text(text,encoding='utf-8')
    approval=reset.seal_baseline(baseline,archive,REFERENCE,True)
    reset.cancel(root);phase2=probe_phase(root,2)
    before=files(root);token=(root/'plugins/FKVNextProbe/reset-token.txt').read_text();logical=reset.logical(root,token);after=files(root)
    protected=[n for n in before if n.startswith(('world/','world_nether/','world_the_end/','plugins/FKAmis/history/')) or n in reset.POLICY_FILES]
    assert all(before[n]==after.get(n) for n in protected)
    phase3=probe_phase(root,3)
    token=(root/'plugins/FKVNextProbe/reset-token.txt').read_text();admins=root/'plugins/FKAmis/admins.yml';original=admins.read_bytes()
    with server.maintenance(root):admins.write_bytes(original+b'\n# autre politique\n')
    try:
        try:reset.restore_initial(root,token,archive,QA/'runtime/refused-vnext1-policy',REFERENCE)
        except RuntimeError as e:assert 'Règles, rôles' in str(e)
        else:raise AssertionError('Politique différente acceptée')
    finally:
        with server.maintenance(root):admins.write_bytes(original)
    dest=QA/'runtime/preproduction-vnext1-reset-restored-2';full=reset.restore_initial(root,token,archive,dest,REFERENCE);boot=startup(dest,'reset-restored-startup')
    rollback=QA/'runtime/preproduction-vnext1-reset-rollback-2';server.restore(rollback,Path(logical['backup']));restored=files(rollback)
    assert restored==server.verify_archive(Path(logical['backup']))['files'];reset.cancel(rollback)
    assert files(rollback)=={n:s for n,s in restored.items() if n not in ('plugins/FKAmis/reset-request.json','plugins/FKAmis/reset-candidate.yml')}
    old=startup(rollback,'reset-rollback-startup',3)
    result('reset-restore',{'passed':True,'fkamisSha256':server.digest(server.PLUGIN),'authenticatedPlayers':0,'logical':logical,'protectedFilesCompared':len(protected),
      'beforeResetRestart':phase2,'logicalRestart':phase3,'baseline':approval,'testFixtureApprovalOnly':True,'visuallyInspected':False,
      'differentPoliciesRefused':True,'fullRestore':full,'fullRestoreStartup':boot,'resetRollbackEntireManifestCompared':len(restored),'resetRollbackStartup':old})

def refusals():
    checks=[]
    for name,marker in [('future','Version VNext future ou invalide'),('reset-pending','Réinitialisation confirmée en attente')]:
        root=QA/'runtime'/('refusal-vnext1-'+name+'-3');server.restore(root,QA/'vnext1-initial-2.zip')
        with server.maintenance(root):
            state=root/'plugins/FKAmis/state.yml'
            if name=='future':state.write_text(state.read_text(encoding='utf-8').replace('  version: 2','  version: 3',1),encoding='utf-8')
            else:(root/'plugins/FKAmis/reset-request.json').write_text('{}\n',encoding='utf-8')
            before={n:server.digest(root/'plugins/FKAmis'/n) for n in ('state.yml','config.yml','admins.yml','supplies.yml')}
        with server.maintenance(root,check_worlds=False):
            p=subprocess.Popen([str(server.java_path()),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25606'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            try:log,_=p.communicate(timeout=180)
            except subprocess.TimeoutExpired:log,_=p.communicate(input='stop\n',timeout=120)
        (QA/('refusal-'+name+'.log')).write_text(log,encoding='utf-8')
        unchanged=before=={n:server.digest(root/'plugins/FKAmis'/n) for n in before}
        diagnostic={'markerFound':marker in log,'notEnabled':'FKAmis prêt' not in log,'unchanged':unchanged,'exitCode':p.returncode}
        print(json.dumps(diagnostic),flush=True)
        assert marker in log and 'FKAmis prêt' not in log and unchanged and p.returncode==0,diagnostic
        checks.append({'case':name,'passed':True,'stateAndPoliciesUnchanged':unchanged,'expectedStartupRefusal':marker,'expectedErrorsObserved':sum(bool(re.search(r'\b(ERROR|SEVERE)\b',l)) for l in log.splitlines()),'officialPluginShutdownZipClosedObserved':'zip file closed' in log})
    result('refusals',{'passed':True,'fkamisSha256':server.digest(server.PLUGIN),'checks':checks,'authenticatedPlayers':0})

def package_map():
    stage=ROOT/'dist/map-v2.1-build-package'
    if stage.exists():raise RuntimeError('Artefact carte existant, conserver la livraison.')
    stage.mkdir(parents=True)
    names=['scripts/'+n+'.py' for n in ('server','map_reader','cavern_plan','map_v21_tool','map_v21_verify','world_integrity','v2_reference')]
    names+=['deployment/territory_migration.py','deployment/new_match.py','deployment/host_ops.py','configs/vnext/new-match-reference.json','docs/FKAMIS_VNEXT_1.md','LICENSE','configs/artifacts.lock.json']
    for name in names:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    for name,source in [('tools/FKMapV21Builder.jar',ROOT/'.cache/FKMapV21Builder.jar'),('plugins/FKAmis-1.0.0.jar',server.PLUGIN),('configs/block-defaults-26.3.json',DEFAULTS)]:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (stage/'README.txt').write_text('CONSTRUCTION DISTINCTE SUR REFERENCE INITIALE UNIQUEMENT\n'
      'Python 3.11+, Java 25, EULA acceptée personnellement, archive initiale privée Paper 26.3-244 nécessaire.\n'
      'Depuis le dossier extrait, aperçu (aucune modification de blocs) :\n'
      'python scripts/map_v21_tool.py --input /chemin/reference-initiale.zip --sha256 '+__import__('map_v21_tool').SOURCE+' --output /chemin/map-v21-apercu --initial-reference --reference configs/vnext/new-match-reference.json\n'
      'Construction : choisir une AUTRE sortie vide map-v21-*, reprendre cette commande et ajouter :\n'
      '--apply --plugin plugins/FKAmis-1.0.0.jar --builder tools/FKMapV21Builder.jar --defaults configs/block-defaults-26.3.json --java /chemin/java --dependencies /chemin/copie-paper-arretee\n'
      'Ne jamais désigner la partie jouée. La référence officielle source SHA8120 est reconnue ; toute autre référence exige un sidecar .approved.json scellé.\n'
      'Le serveur outil écoute localhost:25604, construit à partir des chunks existants, retire son JAR de maintenance et contrôle tous les blocs hors plan/inventaires/entités.\n'
      'Lire map-v21-preview.json, map-v21-build-report.json et le fichier *-result.json à côté de la sortie.\n'
      'Sauvegarde complète avant construction dans .map-v21-backups, hors sortie. Tous les fichiers restent privés.\n'
      'Inspecter les quatre cavernes et spawns en jeu, puis utiliser maintenance/new-match-reference-v2.1.json pour le scellement de cette nouvelle référence.\n'
      'La production n’embarque que FKAmis et FallenKingdom officiel. Ne pas transférer FKMapV21Builder.jar sur le serveur de jeu.\n',encoding='utf-8')
    write(stage/'BUILD_MANIFEST.json',{'schema':1,'mapVersion':'2.1','sourceReferenceSha256':__import__('map_v21_tool').SOURCE,
      'fkamisSha256':server.digest(server.PLUGIN),'files':files(stage),'containsWorldOrPlayerData':False,'requiresHumanInspection':True})
    print('Outil carte autonome préparé.',flush=True)

def seal():
    sha=server.digest(server.PLUGIN);manifest=read(STAGE/'UPDATE_MANIFEST.json')
    assert manifest['files']==files(STAGE/'payload') and manifest['files']['plugins/FKAmis-1.0.0.jar']==sha
    evidence={}
    names=['admin','core','gameplay','supplies','native','vnext','features-1','features-2','features-3','features-4','next1','physics-fixed','update-rollback','inventory-restore','reset-restore','map-v21','map-restore','refusals','map-tool-portable']
    for name in names:
        path=ROOT/'tests/results'/('vnext1-'+name+'.json');d=read(path);assert d['passed'],name
        if 'fkamisSha256' in d:assert d['fkamisSha256']==sha,name
        evidence[name]={'path':path.relative_to(ROOT).as_posix(),'sha256':server.digest(path),'passed':True}
    native={name:read(QA/'tests/results'/('vnext1-probe'+suffix+'.json')) for name,suffix in [('firstStartup',''),('restart','-restart')]}
    result('native-features',{'passed':True,'fkamisSha256':sha,'authenticatedClients':0,**native})
    performance=read(QA/'tests/results/vnext1-performance.json');idle=read(ROOT/'tests/results/vnext1-migration-after.json')
    result('performance',{'passed':True,'fkamisSha256':sha,'microbench':performance,'idleAfter30Seconds':{k:idle.get(k) for k in ('idleMetricsOnly','idleHeapInfo','idleSettleSeconds')},
      'cavernConstruction':{k:read(QA/'runtime/map-v21-built-3/map-v21-build-report.json')[k] for k in ('constructionMillis','plannedBlocks','changedBlocks','chunks')},
      'authenticatedClients':0,'scope':'Coûts locaux seulement. TPS de sonde influencés par démarrage et constructions synchrones ; charge réseau/MineStrator à mesurer.'})
    import vnext_delivery
    preservation=vnext_delivery.preserve();base=read(QA/'base.json')
    for name,expected in base['archives'].items():assert server.digest(ROOT/name)==expected,name
    for name,expected in base['source'].items():
        if name.startswith('tests/results/') or name=='configs/artifacts.lock.json':assert server.digest(ROOT/name)==expected,name
    preservation['vnext1BaseArchivesCompared']=len(base['archives']);preservation['historicalReportsUnchanged']=True
    tests=[]
    for path in (ROOT/'plugins-custom/fk-amis/target/surefire-reports').glob('TEST-*.xml'):
        xml=ET.parse(path).getroot();tests.append({k:int(xml.get(k,0)) for k in ('tests','failures','errors','skipped')})
    java={k:sum(t[k] for t in tests) for k in ('tests','failures','errors','skipped')};assert java['tests']==51 and not java['failures'] and not java['errors']
    python_log=(QA/'python-final.log').read_text(encoding='utf-8',errors='replace');assert 'Ran 43 tests' in python_log and '\nOK' in python_log
    docs=['FKAMIS_VNEXT_1','FKAMIS_VNEXT','ADMIN_GUIDE','GAME_RULES','ARCHITECTURE','TEST_PLAN','DEPLOYMENT','BACKUP_RESTORE','HOST_INSTALLATION','MULTIPLAYER_ACCEPTANCE','PLAYER_GUIDE']
    (STAGE/'docs').mkdir(exist_ok=True)
    for name in docs:shutil.copy2(ROOT/'docs'/(name+'.md'),STAGE/'docs'/(name+'.md'))
    (STAGE/'README.txt').write_text('FKAmis VNext.1 : lire docs/FKAMIS_VNEXT_1.md avant toute opération.\n'
      'Fermer accès, pause, save, stop, attendre Java, sauvegarder toute l’instance à froid.\n'
      'Vérifier le SHA-256 externe, extraire hors instance puis :\npython apply_vnext1_update.py --server /chemin/instance\n'
      'Départ VNext fd12c43c, Paper 26.3-244, Java25, FK2.24.9 intacts. Aucun monde ni état remplacé.\n'
      'Rayons 80→40 sous contrôle des objectifs ; allow-flight=true uniquement. Port22880 et paramètres panel conservés.\n'
      'Aucune caverne sur partie jouée : artefact de carte séparé, référence initiale obligatoire.\n'
      'Rollback : restaurer la sauvegarde COMPLÈTE dans un dossier neuf, jamais l’ancien JAR seul.\n'
      'Tests locaux techniques réussis ; recette humaine et inspection en jeu encore requises. Aucun accès à MineStrator.\n',encoding='utf-8')
    for path in (STAGE,ROOT/'dist/map-v2.1-build-package'):
        assert not any(p.name=='__pycache__' or p.suffix=='.pyc' for p in path.rglob('*'))
    jar=ROOT/'dist/vnext1/FKAmis-1.0.0.jar';jar.parent.mkdir(parents=True,exist_ok=True)
    if jar.exists():raise RuntimeError('JAR de livraison existant')
    shutil.copy2(server.PLUGIN,jar);jar.with_suffix('.jar.sha256').write_text(sha+'\n',encoding='ascii')
    report={'schema':1,'revision':'FKAmis VNext.1 / carte V2.1','passed':True,'branch':'feature/fkamis-vnext-1-map-v2-1','baseCommit':'c631fad','fkamisSha256':sha,
      'runtime':{'paper':'26.3-244','paperSha256':patch.PAPER,'fallenkingdom':'2.24.9','fallenkingdomSha256':patch.FK,'java':25,'hostGamePortPreserved':22880},
      'javaUnitTests':java,'pythonUnitTests':43,'evidence':evidence,'preservation':preservation,'authenticatedClients':0,'mineStratorAccessed':False,
      'locator':{'nativeEnabled':False,'fallback':'ActionBar propre spawn et /fka base','apiAudit':'API locale build244 : portées/styles d’entité, aucune API publique de point fixe filtré par destinataire trouvée','outgoingTextAndPrivacyAttributesVerified':True,'clientRenderingVerified':False},
      'caverns':{'built':4,'input':'référence initiale uniquement','blocksPlanned':37128,'chunks':47,'newChunksGenerated':False,'inventoriesAndEntitiesPreserved':True,'humanInspection':False,'mineralBudgetPerCavern':91,'depthRelativeToBase':42},
      'territories':{'teams':4,'radiusBefore':80,'radiusAfter':40,'centersSpawnsFlagsUnchanged':True,'shape':'carré inclusif, toute hauteur','geometricAreaRatio':0.25,'columnsBefore':25921,'columnsAfter':6561,'incompatibleObjectivesRefusedBeforeWrites':True},
      'portals':{'registeredEndpointsInNativeProbe':2,'bidirectionalTravelAndNetherReconnectVerified':True,'onlyOfficialPairAllowed':True,'vanillaFireAndFireChargeDenied':True,'dispenserDeniedBeforeIgnition':True,'lavaIgniteEventDenied':True,'physicalRandomLavaCycleVerified':False,'productionEndpointsRequireAdminRegistration':True},
      'features':['menu spectateur privé et destinations sûres','aucune pause automatique au départ, seuil roster et grâce conservés','allow-flight serveur sans vol Survival','pause XYZ/gravité/vélocité/montures/projectiles/téléportations/spectateurs'],
      'migration':'apply_vnext1_update.py : sauvegarde complète, migration conservatrice, aucun creusement','rollback':'restauration intégrale VNext/V2 dans une destination neuve, manifeste comparé et démarrage prouvé',
      'humanChecksRemaining':['rendu ActionBar/confidentialité avec clients Java26.3','inspection quatre cavernes et salles dans rayon40','menu/caméra spectateur sous latence','pause sous nage/vol/reconnexion et ping réel','allumage lave réel, routage portails en situation de jeu','combat/déconnexion/capture avec 1 à 4 membres par royaume','TPS/MSPT/RAM/ping sur MineStrator avec clients authentifiés'],
      'commands':['/fka base','/fka spectate [pseudo]','/fka nether portal register overworld|nether','/fka nether portal activate','/fka nether portal deactivate','/fka nether portal status'],
      'guide':'docs/FKAMIS_VNEXT_1.md','testFixtureApprovalsAreNotProductionApprovals':True}
    # Les preuves précèdent le scellement ; les empreintes des ZIP ne peuvent pas
    # être intégrées à leur propre contenu.
    write(STAGE/'TEST_REPORT.json',report)
    artifacts={}
    for name,source in [('fallenkingdom-vnext1-update.zip',STAGE),('fallenkingdom-map-v2.1-build.zip',ROOT/'dist/map-v2.1-build-package')]:
        target=ROOT/'dist'/name;server.create_archive(source,target);artifacts[target.relative_to(ROOT).as_posix()]=server.digest(target)
    artifacts[jar.relative_to(ROOT).as_posix()]=sha;report['artifacts']=artifacts
    report['modifiedTrackedOrNewFiles']=subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    result('delivery',report);print(json.dumps({'passed':True,'artifacts':artifacts},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','migration','inventory','map-restore','reset','refusals','package-map','seal']);args=parser.parse_args()
    {'prepare':prepare,'migration':migration,'inventory':inventory,'map-restore':map_restore,'reset':resets,'refusals':refusals,'package-map':package_map,'seal':seal}[args.action]()
