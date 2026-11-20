"""Audit final : GET API, READDIR/LSTAT/FSTAT/READ et statvfs uniquement ; aucun transfert."""
import sys
sys.dont_write_bytecode=True
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import socket
import time
from minestrator_cold_backup import (Api,Guard,Unsafe,now,write,digest,protect_directory,protect_blob,
    snapshot,assert_tree_same,read_remote,assert_hash_same,progress)
from minestrator_sftp_inventory import pin_matches
import server

REPOSITORY=Path(__file__).resolve().parents[1]
EXPECTED_COMMIT='93fd580'
EXPECTED_SERVER=513365
EXPECTED_HOST='8007.mystrator.com'
PIN='SHA256:eXyAN0WEWh6kRFTNzHWollIGwpXMs9iRVm4mchwrlGI'
BACKUP=Path.home()/'FKBackups/MS-COLD-20261119-02'
CANDIDATE=Path.home()/'FKBackups/V21-QUERY-20261120-01'

def unprotect(path):
    class Blob(ctypes.Structure):_fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_byte))]
    data=path.read_bytes();buffer=ctypes.create_string_buffer(data)
    src=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_byte)));out=Blob()
    crypt=ctypes.WinDLL('Crypt32',use_last_error=True)
    if not crypt.CryptUnprotectData(ctypes.byref(src),None,None,None,None,0,ctypes.byref(out)):raise Unsafe('BaselinePanelDecryptionFailed')
    try:return json.loads(ctypes.string_at(out.pbData,out.cbData))
    finally:
        kernel=ctypes.WinDLL('Kernel32');kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree(ctypes.cast(out.pbData,ctypes.c_void_p))

def local_checks():
    import subprocess
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPOSITORY,capture_output=True,text=True,check=True).stdout.strip()
    commit=subprocess.run(['git','rev-parse',EXPECTED_COMMIT],cwd=REPOSITORY,capture_output=True,text=True,check=True).stdout.strip()
    ancestry=subprocess.run(['git','merge-base','--is-ancestor',commit,head],cwd=REPOSITORY,capture_output=True)
    if ancestry.returncode:raise Unsafe('UnexpectedRepositoryCommit')
    delivery=json.loads((REPOSITORY/'tests/results/query-rollback-delivery.json').read_text(encoding='utf-8'))
    for name,expected in delivery['toolSha256'].items():
        if digest(REPOSITORY/name)!=expected:raise Unsafe('ApprovedMaintenanceToolChanged',details={'path':name})
    unchanged=subprocess.run(['git','diff','--quiet',commit,'--','scripts/minestrator_cold_backup.py','scripts/sftp_attributes.py','scripts/minestrator_sftp_inventory.py','tests/results/query-rollback-delivery.json','configs/artifacts.lock.json'],cwd=REPOSITORY,capture_output=True)
    if unchanged.returncode:raise Unsafe('ApprovedSftpControlsChanged')
    if digest(BACKUP/'instance.zip')!=delivery['originalArchiveSha256'] or digest(BACKUP/'manifest.json')!=delivery['originalManifestSha256']:raise Unsafe('HistoricalBackupChanged')
    baseline=json.loads((BACKUP/'manifest.json').read_text(encoding='utf-8'))
    actual={p.relative_to(BACKUP/'restore').as_posix():digest(p) for p in (BACKUP/'restore').rglob('*') if p.is_file()}
    if actual!={n:a['sha256'] for n,a in baseline['files'].items()}:raise Unsafe('HistoricalRestorationChanged')
    if digest(CANDIDATE/'payload/DEPLOYMENT_MANIFEST.json')!=delivery['deploymentManifestSha256'] or digest(CANDIDATE/'transfer-plan-private.json')!=delivery['transferPlanSha256']:raise Unsafe('CandidateManifestChanged')
    plan=json.loads((CANDIDATE/'transfer-plan-private.json').read_text(encoding='utf-8'))
    manifest=json.loads((CANDIDATE/'payload/DEPLOYMENT_MANIFEST.json').read_text(encoding='utf-8'))
    if len(plan['files'])!=148 or plan['sourcePreconditionSha256']!={n:a['sha256'] for n,a in baseline['files'].items()}:raise Unsafe('TransferPlanBaselineMismatch')
    payload={p.relative_to(CANDIDATE/'payload').as_posix():digest(p) for p in (CANDIDATE/'payload').rglob('*') if p.is_file()}
    if payload!={f['path']:f['newSha256'] for f in plan['files']}:raise Unsafe('PayloadChanged')
    for name,h in manifest['files'].items():
        if digest(CANDIDATE/'preproduction-candidate'/name)!=h:raise Unsafe('CandidateChanged',details={'path':name})
    archive=CANDIDATE/'v21-fourplayers-transfer-private.zip'
    if digest(archive)!=delivery['privateTransferArchiveSha256'] or server.verify_archive(archive)['files']!=payload:raise Unsafe('TransferArchiveChanged')
    total=sum(a['size'] for a in baseline['files'].values())
    payload_bytes=sum((CANDIDATE/'payload'/n).stat().st_size for n in payload)
    largest=max((CANDIDATE/'payload'/n).stat().st_size for n in payload)
    margin=2*1024**3
    space={'historicalInstanceBytes':total,'payloadBytes':payload_bytes,'largestTransferFileBytes':largest,
      'externalBackupZipBytes':(BACKUP/'instance.zip').stat().st_size,'transferZipBytes':archive.stat().st_size,
      'quarantineRenameAdditionalDataBytes':0,'rollbackStagingReserveBytes':total,'operationalMarginBytes':margin,
      'requiredAdditionalFreeBytes':payload_bytes+total+largest+margin,
      'assumptions':['Fichiers SFTP dans staging neuf puis renommage sur le même filesystem','Quarantaine par renommage, sans duplication des anciens arbres','Réserve pour une restauration complète en parallèle et un fichier temporaire supplémentaire','Aucune extraction ZIP distante ; marge de 2 Gio proposée pour croissance et écritures de démarrage']}
    return baseline,plan,{'baseCommit':commit,'auditedRepositoryHead':head,'sourceFiles':len(baseline['files']),'payloadFiles':148,'completeManifestFiles':len(manifest['files']),
      'originalsUnchanged':True,'candidateAndArchiveVerified':True,'deploymentManifestSha256':delivery['deploymentManifestSha256'],
      'sourceArchiveSha256':delivery['originalArchiveSha256'],'sourceManifestSha256':delivery['originalManifestSha256'],
      'transferPlanSha256':delivery['transferPlanSha256'],'spacePlan':space}

def audit_hashes(client,baseline,guard,evidence,report):
    current=snapshot(client,guard)
    assert_tree_same(current,baseline,stage='remote_vs_backup_before_read',evidence=evidence)
    report['treeAndMetadataMatchBackup']=True
    anchors={n:a['pathStatBaseline'] for n,a in baseline['files'].items() if a.get('pathStatBaseline')}
    report['filesHashedPerPass']=[0,0]
    for index in range(2):
        for name,attrs in sorted(baseline['files'].items()):
            h=read_remote(client,name,current['files'][name],guard,evidence=evidence,anchors=anchors)
            assert_hash_same(h,attrs['sha256'],name=name,stage='content_vs_backup_pass_'+str(index+1),evidence=evidence)
            report['filesHashedPerPass'][index]+=1
            if report['filesHashedPerPass'][index]%25==0:progress('hash_progress',passNumber=index+1,files=report['filesHashedPerPass'][index],total=len(baseline['files']))
        observed=snapshot(client,guard)
        assert_tree_same(observed,current,stage='tree_after_pass_'+str(index+1),evidence=evidence)
        assert_tree_same(observed,baseline,stage='backup_after_pass_'+str(index+1),evidence=evidence)
    report['allSourceHashesMatchBackupTwice']=True

def disk_stats(client):
    # Extension OpenSSH en lecture seule. Aucun exec SSH ni commande système.
    try:
        from paramiko.sftp import CMD_EXTENDED,CMD_EXTENDED_REPLY
        kind,msg=client._request(CMD_EXTENDED,'statvfs@openssh.com','.')
        if kind!=CMD_EXTENDED_REPLY:return {'available':False,'reason':'UnexpectedReply'}
        keys=('bsize','frsize','blocks','bfree','bavail','files','ffree','favail','fsid','flag','namemax')
        data={k:msg.get_int64() for k in keys}
        if data['frsize']<=0:return {'available':False,'reason':'InvalidFragmentSize'}
        return {'available':True,'filesystemFreeToUserBytes':data['bavail']*data['frsize'],'filesystemCapacityBytes':data['blocks']*data['frsize'],'provesHostingQuota':False}
    except (OSError,EOFError):return {'available':False,'reason':'SftpStatvfsUnavailable'}

def run(config):
    import paramiko
    if int(config['serverId'])!=EXPECTED_SERVER or config['host']!=EXPECTED_HOST or int(config['port'])!=2022 or config['fingerprint']!=PIN:raise Unsafe('ConnectionIdentityMismatch')
    baseline,plan,local=local_checks()
    out=Path(config['output']).resolve()
    if out.is_relative_to(REPOSITORY) or out.is_relative_to(BACKUP) or out.is_relative_to(CANDIDATE):raise Unsafe('UnsafeAuditDestination')
    protect_directory(out)
    report={'operation':out.name,'startedAtUtc':now(),'status':'in_progress','remoteWritesPerformed':False,
      'remotePowerOrConsoleCommands':False,'remoteDeploymentPerformed':False,'local':local,'remoteAuditCompleted':False,'readyForDeployment':False}
    api=Api(config.pop('apiKey'),config['serverId']);guard=Guard(api);transport=None
    trace=(out/'attributes-private.jsonl').open('x',encoding='utf-8')
    def evidence(value):trace.write(json.dumps(value,ensure_ascii=False)+'\n');trace.flush()
    try:
        data=api.get('');srv=data['server']
        if int(srv['id'])!=EXPECTED_SERVER or int(srv['port'])!=22880:raise Unsafe('ServerIdentityMismatch')
        if srv.get('ip') is not None and str(srv['ip']).split(':')[0]!='91.197.6.72':raise Unsafe('ServerAddressMismatch')
        report['authenticatedIdentity']={'serverId':EXPECTED_SERVER,'port':22880,'matched':True}
        info={k:data.get(k) for k in ('settings','ports','offer')}|{'resources':data.get('mybox',{}).get('resources'),'port':srv['port']}
        (out/'panel-current.dpapi').write_bytes(protect_blob(json.dumps(info,sort_keys=True).encode()))
        old=unprotect(BACKUP/'panel-settings.dpapi')
        settings=info.get('settings') or {};oldsettings=old.get('settings') or {}
        report['panel']={'settingsKeys':sorted(settings),'changedSettingKeys':[k for k in settings.keys()|oldsettings.keys() if settings.get(k)!=oldsettings.get(k)],
          'javaVersionId':settings.get('id_java_version'),'image':settings.get('image'),'javaMemory':settings.get('java_memory'),'startupFile':settings.get('startup_file'),
          'startupCommandSameAsBackup':settings.get('startup')==oldsettings.get('startup'),'portsSameAsBackup':info.get('ports')==old.get('ports')}
        if report['panel']['changedSettingKeys'] or not report['panel']['portsSameAsBackup']:
            raise Unsafe('RemotePanelSettingsChanged',details={'changedSettingKeys':report['panel']['changedSettingKeys'],'portsSameAsBackup':report['panel']['portsSameAsBackup']})
        # Aucun dump des messages, commandes, identifiants SFTP ou historiques.
        live=api.get('/live');(out/'live-current.dpapi').write_bytes(protect_blob(json.dumps(live).encode()))
        report['diskApi']={k:(live.get('stats') or {}).get('disk',{}).get(k) for k in ('current','limit','percent')}
        report['diskApi']['unitsIndependentlyVerified']=False
        report['scheduling']={'publicApiExposesVerifiedTaskList':False,'disabledVerified':False,'exclusiveHostLockAvailable':False,
          'possibleSettingKeys':[k for k in settings if any(word in k.lower() for word in ('schedul','cron','restart','auto'))],
          'notificationMessagesAreNotRestartDisableProof':True}
        guard.start();progress('identity_and_offline_confirmed',serverId=EXPECTED_SERVER)
        transport=paramiko.Transport(socket.create_connection((config['host'],int(config['port'])),timeout=15));guard.abort=transport.close
        transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),PIN):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        report.update({'sftpAuthenticated':True,'hostKeyVerified':True})
        with paramiko.SFTPClient.from_transport(transport) as client:
            client.get_channel().settimeout(20)
            report['diskSftp']=disk_stats(client)
            audit_hashes(client,baseline,guard,evidence,report)
            guard.poll();guard.check()
        report['remoteAuditCompleted']=True;report['status']='read_only_audit_completed'
    except Exception as error:
        report['status']='stopped';report['failure']=str(error) if isinstance(error,Unsafe) else type(error).__name__
        if isinstance(error,Unsafe) and error.details:write(out/'divergence-private.json',error.details);report['divergence']=error.details
    finally:
        guard.close()
        if guard.failed.is_set():report.update({'status':'stopped','failure':guard.reason,'remoteAuditCompleted':False})
        if transport:transport.close()
        trace.close();config.clear()
        report['apiObservations']=guard.samples;report['finishedAtUtc']=now()
        report['originalArchiveAndManifestUnchanged']=digest(BACKUP/'instance.zip')==local['sourceArchiveSha256'] and digest(BACKUP/'manifest.json')==local['sourceManifestSha256']
        report['original305RestoredFilesUnchanged']={p.relative_to(BACKUP/'restore').as_posix():digest(p) for p in (BACKUP/'restore').rglob('*') if p.is_file()}=={n:a['sha256'] for n,a in baseline['files'].items()}
        if not report['originalArchiveAndManifestUnchanged'] or not report['original305RestoredFilesUnchanged']:
            report.update({'status':'stopped','failure':'HistoricalPreservationFailed','remoteAuditCompleted':False})
        write(out/'report-private.json',report)
    progress('audit_finished',status=report['status'],failure=report.get('failure'),hashesPerPass=report.get('filesHashedPerPass'),privateDirectory=str(out))
    return 0 if report['remoteAuditCompleted'] else 1

if __name__=='__main__':
    try:sys.exit(run(json.load(sys.stdin)))
    except Exception as error:progress('audit_not_started',failure=str(error) if isinstance(error,Unsafe) else type(error).__name__);sys.exit(1)
