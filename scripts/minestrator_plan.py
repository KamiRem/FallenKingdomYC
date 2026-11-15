"""Plan local à partir de l'inventaire ; aucune opération distante."""
import sys
sys.dont_write_bytecode=True
import base64
import hashlib
import json
from pathlib import Path
import shutil
import server
from preproduction_smoke import smoke
sys.modules['serverlib']=server
sys.path.insert(0,str(server.ROOT/'deployment'))
from apply_vnext1_update import config_defaults
import new_match

def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    private=json.load(sys.stdin)
    contents={k:base64.b64decode(v) for k,v in private.items()}
    store=server.ROOT/'local/minestrator-secrets'
    inventories=[p for p in store.glob('remote-inventory-*.json') if 'files' in json.loads(p.read_text(encoding='utf-8'))]
    inventory=json.loads(max(inventories,key=lambda p:p.stat().st_mtime).read_text(encoding='utf-8'))
    assert inventory['authenticated'] and inventory['hostKeyVerified'] and inventory['complete']
    remote={f['path']:f for f in inventory['files']}
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,default=server.ROOT/'.cache/ms15p');args=parser.parse_args()
    work=args.work.resolve();server.confined(work,server.ROOT/'.cache')
    if work.exists():raise RuntimeError('Conserver le plan existant ; utiliser une nouvelle révision du dossier.')
    work.mkdir()
    source=server.ROOT/'.cache/mp15a/candidate-v21.zip'
    evidence=json.loads((server.ROOT/'.cache/mp15a/preparation.json').read_text(encoding='utf-8'))
    assert server.digest(source)==evidence['candidateArchiveSha256']
    root=work/'runtime/preproduction';server.restore(root,source)
    # Restreindre le candidat avant d'y écrire des politiques réelles, notamment server.properties.
    import subprocess
    sid=subprocess.run(['powershell.exe','-NoProfile','-Command','[Security.Principal.WindowsIdentity]::GetCurrent().User.Value'],capture_output=True,text=True,check=True).stdout.strip()
    restriction=subprocess.run(['icacls.exe',str(root),'/inheritance:r','/grant:r','*'+sid+':(OI)(CI)F'],capture_output=True)
    # Une erreur interdit de déchiffrer/écrire les politiques dans ce dossier.
    if restriction.returncode:raise RuntimeError('ACL du candidat non sécurisées.')
    with server.maintenance(root):
        for name in ('plugins/FKAmis/config.yml','plugins/FKAmis/admins.yml','server.properties','whitelist.json','ops.json'):
            data=contents[name]
            if name.endswith('config.yml'):data=config_defaults(data.decode('utf-8-sig')).encode('utf-8')
            (root/name).write_bytes(data)
        assert server.properties(root/'server.properties')['server-port']=='22880'
        assert server.properties(root/'server.properties')['level-name']=='world'
        assert server.properties(root/'server.properties')['allow-flight']=='true'
        checks=new_match.initial_checks(root,root/'maintenance/new-match-reference-v2.1.json')
        # La référence par défaut de cette NOUVELLE carte inclut aussi ses cavernes.
        shutil.copy2(root/'maintenance/new-match-reference-v2.1.json',root/'maintenance/new-match-reference.json')
    start=smoke(root,work/'startup-private.json',server.java_path(),25614)
    if not start['passed'] or start['errors']:raise RuntimeError('Démarrage du candidat préparé refusé.')
    with server.maintenance(root):
        (root/'server.properties').write_bytes(contents['server.properties'])
        checks=new_match.initial_checks(root,root/'maintenance/new-match-reference-v2.1.json')
    payload=work/'payload';payload.mkdir()
    exact=[]
    for path in server.iter_files(root):
        name=path.relative_to(root).as_posix()
        selected=name.startswith(('world/','world_nether/','world_the_end/','plugins/FKAmis/','plugins/FallenKingdom/','maintenance/')) or name in ('map-v2-construction.json','map-v21-caverns.json','RUNTIME_LOCK.json','FKAmis.sha256')
        if not selected:continue
        dest=payload/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        exact.append({'path':name,'newSha256':server.digest(path),'oldSha256':remote.get(name,{}).get('sha256'),'oldSize':remote.get(name,{}).get('size'),'existsRemotely':name in remote})
    # Les politiques copiées restent inchangées dans la racine distante et sont incluses dans les contrôles.
    retained={n:remote[n]['sha256'] for n in ['paper.jar','server.jar','plugins/FKAmis-1.0.0.jar','plugins/FallenKingdom-2.24.9.jar','server.properties','whitelist.json','ops.json']}
    baseline={e['path']:e['newSha256'] for e in exact};baseline.update(retained)
    manifest={'schema':1,'files':baseline,'requiresColdBackupAndExplicitApproval':True,'scope':'Nouvelle partie V2.1, sans fusion de progression'}
    write(payload/'DEPLOYMENT_MANIFEST.json',manifest)
    exact.append({'path':'DEPLOYMENT_MANIFEST.json','newSha256':server.digest(payload/'DEPLOYMENT_MANIFEST.json'),'existsRemotely':'DEPLOYMENT_MANIFEST.json' in remote})
    archiveRoots=['world','world_nether','world_the_end','plugins/FKAmis','plugins/FallenKingdom']
    oldScope=[f['path'] for f in inventory['files'] if any(f['path']==n or f['path'].startswith(n+'/') for n in archiveRoots)]
    plan={'schema':1,'executed':False,'remoteWritesPerformed':False,'candidate':str(root.relative_to(server.ROOT)),'files':exact,'retainUnchanged':retained,
      'quarantineBeforeTransferAfterVerifiedExternalBackup':archiveRoots+['BACKUP_MANIFEST.json'],
      'oldFilesInReplacedTrees':oldScope,'alsoPreserveUntouched':['.ai-backups','reference','libraries','cache','versions','config','bukkit.yml','spigot.yml','eula.txt','eula-acceptance.json','banned-players.json','banned-ips.json','usercache.json'],
      'initialChecks':checks,'localStartupPassed':True,'realWhitelistCount':len(json.loads(contents['whitelist.json'])),'realOpsCount':len(json.loads(contents['ops.json'])),
      'noPlayerDataImported':True,'noOldStateImported':True,'noOldSupplyProgressImported':True,
      'unverifiedItems':['Java effectif : serveur distant arrêté, identifiant panel 61 sans correspondance documentée','Espace disque nécessaire au backup et à la quarantaine','Désactivation/absence de redémarrage automatique avant sauvegarde','Inspection visuelle et approbation de la nouvelle référence'],
      'backupBeforeDeployment':'Téléchargement complet à froid + manifeste et SHA externes, relecture distante, restauration de contrôle ; snapshots existants insuffisants seuls.'}
    write(work/'transfer-plan-private.json',plan)
    safe={k:v for k,v in plan.items() if k not in ['files','oldFilesInReplacedTrees','retainUnchanged']}
    safe.update({'transferFiles':len(exact),'oldFilesInReplacedTreesCount':len(oldScope),'retainedCoreHashes':{n:h for n,h in retained.items() if n.endswith('.jar')},'privateManifest':str((work/'transfer-plan-private.json').relative_to(server.ROOT)),'productionReady':False})
    write(server.ROOT/'tests/results/minestrator-transfer-plan.json',safe)
    print(json.dumps({'planPrepared':True,'transferFiles':len(exact),'localStartupPassed':True,'checks':checks,'remoteWritesPerformed':False}))

if __name__=='__main__':main()
