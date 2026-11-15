"""Préparation locale uniquement ; aucun client distant ni action d'alimentation."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import zipfile
import server
from map_v21_tool import build,SOURCE
from preproduction_smoke import smoke

def write(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def files(root):return {p.relative_to(root).as_posix():server.digest(p) for p in server.iter_files(root)}
def prepare(work):
    work=work.resolve()
    if work.exists():raise RuntimeError('Destination existante : conserver cet essai et choisir un autre dossier.')
    server.confined(work,server.ROOT/'.cache');work.mkdir(parents=True)
    delivery=json.loads((server.ROOT/'tests/results/vnext1-delivery.json').read_text(encoding='utf-8'))
    for name,sha in delivery['artifacts'].items():
        if server.digest(server.ROOT/name)!=sha:raise RuntimeError('Livrable différent : '+name)
    source=server.ROOT/'dist/fallenkingdom-preproduction-26.3.zip'
    if server.digest(source)!=SOURCE:raise RuntimeError('Référence source différente.')
    # L'artefact autonome est extrait avec vérification du manifeste de sauvegarde.
    tool=work/'construction-tool';server.restore(tool,server.ROOT/'dist/fallenkingdom-map-v2.1-build.zip')
    candidate=work/'runtime/map-v21-candidate'
    # Le constructeur et les fichiers utilisés sont ceux de l'artefact validé.
    result=build(source,SOURCE,candidate,True,True,tool/'plugins/FKAmis-1.0.0.jar',tool/'tools/FKMapV21Builder.jar',
                 tool/'configs/vnext/new-match-reference.json',tool/'configs/block-defaults-26.3.json',server.java_path(),server.ROOT/'runtime/preproduction-26-3')
    # Simulation nouvelle partie : ancienne fixture conservée entière, jamais fusionnée.
    previous=json.loads((server.ROOT/'tests/results/vnext1-update-rollback.json').read_text(encoding='utf-8'))
    old=work/'runtime/preproduction-simulation-old';server.restore(old,Path(previous['update']['backup']))
    cold=work/'simulation-old-full.zip'
    with server.maintenance(old):server.create_archive(old,cold)
    new_archive=work/'candidate-v21.zip'
    with server.maintenance(candidate):
        state=(candidate/'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
        from map_v21_tool import initial
        initial(state,files(candidate))
        if {p.name for p in (candidate/'plugins').glob('*.jar')}!={'FKAmis-1.0.0.jar','FallenKingdom-2.24.9.jar'}:raise RuntimeError('Plugins inattendus.')
        server.create_archive(candidate,new_archive)
    new=work/'runtime/preproduction-simulation-new';server.restore(new,new_archive)
    expected=server.verify_archive(new_archive)['files'];assert files(new)==expected
    before=files(old);after=files(new)
    diff={'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys()),'changed':sorted(n for n in before.keys()&after.keys() if before[n]!=after[n])}
    write(work/'transfer-diff-private.json',diff)
    declared=(new/'server.properties').read_bytes()
    boot=smoke(new,work/'simulation-startup.json',server.java_path(),25611)
    if not boot['passed'] or boot['errors']:raise RuntimeError('Échec du démarrage simulé.')
    with server.maintenance(new):(new/'server.properties').write_bytes(declared)
    rollback=work/'runtime/preproduction-simulation-rollback';server.restore(rollback,cold)
    assert files(rollback)==server.verify_archive(cold)['files']
    # L'ancienne fixture contient une partie terminée jour 3, avec historique.
    restored=smoke(rollback,work/'simulation-rollback-startup.json',server.java_path(),25612,expected_day=3)
    assert restored['passed'] and not restored['errors']
    report={'schema':1,'localPreparationPassed':True,'phaseEAuthorized':False,'remoteModified':False,
      'authenticatedRemoteAuditCompleted':False,'remoteBackupCreated':False,'remoteBackupReason':'Accès non configurés ; arrêt interdit avant autorisation E.',
      'referenceSha256':SOURCE,'artifactsVerified':delivery['artifacts'],'candidate':str(candidate.relative_to(server.ROOT)),
      'candidateArchiveSha256':server.digest(new_archive),'mapBuild':result,'simulation':{'passed':True,'usesSyntheticHistoricalFixture':True,'usesActualRemoteData':False,
      'newInstanceManifestFilesCompared':len(expected),'diffCounts':{k:len(v) for k,v in diff.items()},'privateDiff':str((work/'transfer-diff-private.json').relative_to(server.ROOT)),
      'oldBackupSha256':server.digest(cold),'rollbackFullManifestCompared':True,'newStartupPassed':True,'rollbackStartupPassed':True,'inventoriesAndStateMerged':False},
      'blockingBeforeRemotePlanApproval':['ID serveur et paramètres SFTP réels','Authentification API et SFTP, clé hôte vérifiée','Audit versions/fichiers/config/politiques/sauvegardes distantes','Inspection visuelle V2.1 et approbation de référence','Sauvegarde distante cohérente après arrêt explicitement autorisé','Diff réel à recalculer à partir du point arrêté'],
      'humanInspectionPerformed':False,'productionReady':False}
    write(work/'preparation.json',report)
    print(json.dumps({'localPreparationPassed':True,'report':str(work/'preparation.json'),'diffCounts':report['simulation']['diffCounts'],'remoteModified':False}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);prepare(p.parse_args().work)
