"""Paquet ciblé FKAmis et répétition locale de l'installation, sans monde dans le ZIP."""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import server
from preproduction_smoke import smoke
from preproduction import initial_state
from world_integrity import compare

ROOT=server.ROOT
STAGE=ROOT/'dist/admin-update-package'
REPORT=ROOT/'tests/results/admin-update-delivery.json'
BASE=ROOT/'dist/fallenkingdom-preproduction-26.3.zip'


def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def build():
    sha=server.digest(server.PLUGIN);suites=[]
    for name in ['admin','core','gameplay','supplies','native']:
        result=json.loads((ROOT/f'tests/results/admin-update-{name}.json').read_text(encoding='utf-8'))
        if not result['passed'] or result['fkamisSha256']!=sha:raise RuntimeError('Recette incomplète ou binaire différent : '+name)
        suites.append(result)
    if STAGE.exists():raise RuntimeError('Livraison déjà préparée, conserver sans écrasement.')
    STAGE.mkdir(parents=True)
    payload={
      'plugins/FKAmis-1.0.0.jar':server.PLUGIN,
      'maintenance/serverlib.py':ROOT/'scripts/server.py',
      'maintenance/host_ops.py':ROOT/'deployment/host_ops.py'}
    for name,source in payload.items():
        target=STAGE/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (STAGE/'payload/FKAmis.sha256').write_text(sha+'\n',encoding='ascii')
    shutil.copy2(ROOT/'deployment/apply_admin_update.py',STAGE/'apply_admin_update.py')
    shutil.copy2(ROOT/'scripts/server.py',STAGE/'serverlib.py')
    shutil.copy2(ROOT/'LICENSE',STAGE/'LICENSE-FKAmis.txt')
    (STAGE/'docs').mkdir()
    for name in ['ADMIN_UPDATE','ADMIN_GUIDE','PLAYER_GUIDE','GAME_RULES','ARCHITECTURE','TEST_PLAN','DEPLOYMENT','HOST_INSTALLATION']:
        shutil.copy2(ROOT/'docs'/(name+'.md'),STAGE/'docs'/(name+'.md'))
    (STAGE/'README.txt').write_text('Lire docs/ADMIN_UPDATE.md. Aucun monde, state.yml ni admins.yml à transférer.\n'
        'Serveur arrêté : sauvegarde complète puis JAR/configuration ciblés, sans /reload.\n'
        'Option Python : python apply_admin_update.py --server /chemin/instance\n',encoding='utf-8')
    files={p.relative_to(STAGE/'payload').as_posix():server.digest(p) for p in (STAGE/'payload').rglob('*') if p.is_file()}
    write(STAGE/'UPDATE_MANIFEST.json',{'schema':1,'paperSha256':'9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf',
        'previousPluginSha256s':['9201a72528b8f6699f394c3e495ab7192bde312614f7f3d2bad88edaf9a8ea37'],'files':files,
        'changes':{'max-players':'10','gamemode':'survival','force-gamemode':'false','disable-native-tips':True},
        'neverOverwrite':['world/','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml']})
    archive=ROOT/'dist/fallenkingdom-admin-update.zip';server.create_archive(STAGE,archive)
    standalone=ROOT/'dist/admin-update';standalone.mkdir(exist_ok=False)
    shutil.copy2(server.PLUGIN,standalone/'FKAmis-1.0.0.jar')
    (standalone/'FKAmis-1.0.0.jar.sha256').write_text(sha+'\n',encoding='ascii')
    write(REPORT,{'atUtc':datetime.now(timezone.utc).isoformat(),'package':archive.relative_to(ROOT).as_posix(),
        'packageSha256':server.digest(archive),'packageFiles':len(server.verify_archive(archive)['files']),
        'plugin':'dist/admin-update/FKAmis-1.0.0.jar','pluginSha256':sha,'paper':'26.3-244','java':25,
        'fallenkingdom':'2.24.9','thirdPartyJarModified':False,'unitTests':{'java':24,'python':24,'failures':0},
        'technicalSuites':suites,'technicalAssertions':sum(c['assertions'] for s in suites for c in s['checks']),
        'authenticatedPlayers':0,'simulatedPlayerActors':9,'containsWorld':False,'containsLiveStateOrAdmins':False,
        'humanTestsRemaining':['nine_authenticated_clients','real_respawn_and_bed','real_admin_permissions_and_flight',
                               'captured_player_reconnect','tips_absent_after_three_minutes','host_performance'],
        'rehearsal':'pending','remoteHostingTouched':False,'officialGameStarted':False})
    print('Paquet ciblé créé : '+str(archive),flush=True)


def rehearse():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    if server.digest(ROOT/report['package'])!=report['packageSha256']:raise RuntimeError('Archive de livraison altérée.')
    root=server.server_dir('preproduction-admin-update')
    server.restore(root,BASE)
    (root/'plugins/FKAmis/admins.yml').write_text('schema: 1\nadministrators: []\n',encoding='utf-8')
    sys.modules['serverlib']=server
    spec=importlib.util.spec_from_file_location('admin_patch',STAGE/'apply_admin_update.py');patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    result=patch.apply(root,STAGE)
    check=smoke(root,ROOT/'tests/results/admin-update-smoke.json',server.java_path(),25588)
    if not check['passed']:raise RuntimeError('Échec démarrage après mise à jour.')
    initial=initial_state(root)
    raw=json.loads((ROOT/'.cache/admin-qa/tests/results/block-defaults-26.3.json').read_text(encoding='utf-8'))
    defaults={name:dict(part.split('=',1) for part in value.partition('[')[2].removesuffix(']').split(',') if part) for name,value in raw.items()}
    integrity=compare(root,BASE,defaults)
    if not integrity['passed']:raise RuntimeError('Carte modifiée après mise à jour.')
    restored=server.server_dir('preproduction-admin-rollback')
    archive=Path(result['backup']);server.restore(restored,archive)
    manifest=server.verify_archive(archive)['files']
    actual={p.relative_to(restored).as_posix():server.digest(p) for p in server.iter_files(restored)}
    if manifest!=actual:raise RuntimeError('Retour arrière différent du point froid.')
    rollback_smoke=smoke(restored,ROOT/'tests/results/admin-update-rollback-smoke.json',server.java_path(),25589)
    if not rollback_smoke['passed']:raise RuntimeError('Échec de démarrage du retour arrière.')
    report['rehearsal']={'passed':True,'instance':root.relative_to(ROOT).as_posix(),
        'coldBackup':archive.relative_to(ROOT).as_posix(),'coldBackupSha256':result['backupSha256'],
        'protectedFilesComparedDuringPatch':result['protectedFiles'],'worldStateAndExistingAdminsUnchangedDuringPatch':True,
        'initialStateAfterStartup':initial,'worldIntegrity':integrity,'startup':check,
        'rollbackInstance':restored.relative_to(ROOT).as_posix(),'rollbackFilesCompared':len(actual),'rollbackStartup':rollback_smoke}
    report['passed']=True;write(REPORT,report)
    print('Installation ciblée et restauration complète validées sans modification des références.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['build','rehearse'])
    {'build':build,'rehearse':rehearse}[parser.parse_args().action]()
