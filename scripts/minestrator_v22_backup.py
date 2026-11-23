"""Sauvegarde actuelle V2.2 autorisée : API GET et SFTP rb exclusivement."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import shutil
import socket
import subprocess
import time
import zipfile
from minestrator_cold_backup import (Api,Guard,Unsafe,now,write,digest,protect_directory,protect_blob,
    snapshot,assert_tree_same,read_remote,assert_hash_same,archive_and_restore,structure_checks,progress)
from minestrator_v22_preflight import ReadOnlySftp
from minestrator_final_audit import EXPECTED_SERVER,EXPECTED_HOST,PIN
from minestrator_sftp_inventory import pin_matches
from anvil_patch import region_entries
from natural_caverns_rework import unpack
from map_reader import nbt
import server

OP='MS-COLD-V22-20261123-01'
PARENT=Path.home()/'FKBackups'
FRESH=PARENT/'MS-V22-PREFLIGHT-20261123-02'
PREVIOUS=PARENT/'MS-V22-PREFLIGHT-20261123-01'

def active_hashes(files):return {n:a for n,a in files.items() if n.split('/')[0] not in ('.fk-stage','.fk-quarantine')}

def preconditions():
    fresh=json.loads((FRESH/'fingerprint-private.json').read_text(encoding='utf-8'))
    old=json.loads((PREVIOUS/'fingerprint-private.json').read_text(encoding='utf-8'))
    if not fresh['passed'] or fresh['apiGameState']!='offline' or fresh['doubleReadHashes']!=old['doubleReadHashes']:
        raise Unsafe('FreshAuditDivergesOrIncomplete')
    return fresh

def deep_checks(restore,guard):
    counts={'allRegionFilesDecoded':0,'allRegionChunksDecoded':0,'allJarCrcChecked':0,'technicalRegionFilesDecoded':0}
    for path in restore.rglob('*'):
        if not path.is_file():continue
        guard.check()
        if path.suffix=='.mca':
            for value in region_entries(path.read_bytes()).values():nbt(unpack(value));counts['allRegionChunksDecoded']+=1
            counts['allRegionFilesDecoded']+=1
            if path.relative_to(restore).parts[0] in ('.fk-stage','.fk-quarantine'):counts['technicalRegionFilesDecoded']+=1
        elif path.suffix=='.jar':
            with zipfile.ZipFile(path) as z:
                if z.testzip():raise Unsafe('AnyJarCrcFailure')
            counts['allJarCrcChecked']+=1
    return counts

def run(config):
    import paramiko
    if int(config['serverId'])!=EXPECTED_SERVER or config['host']!=EXPECTED_HOST or int(config['port'])!=2022 or config['fingerprint']!=PIN:
        raise Unsafe('ConnectionIdentityMismatch')
    baseline=preconditions();root=PARENT/OP
    if root.exists():raise Unsafe('DestinationAlreadyExists')
    if any(p.is_symlink() or (p.exists() and p.is_junction()) for p in (root,*root.parents)):raise Unsafe('UnsafeLocalPath')
    protect_directory(root)
    report={'operation':OP,'status':'in_progress','startedAtUtc':now(),'remoteWritesPerformed':False,
        'sharedRemoteLock':False,'derogationExplicitlyAuthorized':True,'completelyGuaranteed':False,
        'ownerCurrentAvailableQuotaDeclarationGB':50,'schedulingAndHostingRestartNotIndependentlyExposed':True,
        'backupValidated':False,'functionalRestoreValidated':False}
    api=Api(config.pop('apiKey'),EXPECTED_SERVER);guard=Guard(api);transport=None
    trace=(root/'sftp-attributes-private.jsonl').open('x',encoding='utf-8')
    def evidence(value):trace.write(json.dumps(value,ensure_ascii=False)+'\n');trace.flush()
    try:
        data=api.get('');srv=data['server'];settings=data.get('settings') or {}
        if int(srv['id'])!=EXPECTED_SERVER or int(srv['port'])!=22880 or str(srv['ip']).split(':')[0]!='91.197.6.72':raise Unsafe('ServerIdentityMismatch')
        if settings.get('id_java_version')!=61 or '/java/25_perf:' not in settings.get('image','') or settings.get('startup_file')!='paper.jar':raise Unsafe('PanelVersionMismatch')
        info=api.info();(root/'panel-settings.dpapi').write_bytes(protect_blob(json.dumps(info).encode()))
        guard.start();progress('cold_backup_offline_confirmed',operation=OP)
        transport=paramiko.Transport(socket.create_connection((config['host'],2022),timeout=15));guard.abort=transport.close;transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),PIN):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        with paramiko.SFTPClient.from_transport(transport) as raw:
            raw.get_channel().settimeout(20);client=ReadOnlySftp(raw);initial=snapshot(client,guard)
            if set(active_hashes(initial['files']))!=set(baseline['doubleReadHashes']):raise Unsafe('ActiveTreeDivergedBeforeBackup')
            total=sum(a['size'] for a in initial['files'].values());write(root/'initial-inventory.json',initial)
            if shutil.disk_usage(root).free<total*6+2*1024**3:raise Unsafe('InsufficientLocalSpaceForCopies')
            progress('complete_inventory',files=len(initial['files']),directories=len(initial['directories']),bytes=total)
            copied=root/'download.partial';copied.mkdir()
            for name in initial['directories']:(copied/name).mkdir(parents=True,exist_ok=True)
            manifest=json.loads(json.dumps(initial));anchors={};last=time.monotonic()
            for index,(name,attrs) in enumerate(sorted(initial['files'].items()),1):
                dest=copied/name;dest.parent.mkdir(parents=True,exist_ok=True)
                h=read_remote(client,name,attrs,guard,dest,evidence=evidence,anchors=anchors)
                if name in baseline['doubleReadHashes']:assert_hash_same(h,baseline['doubleReadHashes'][name],name=name,stage='current_vs_fresh_audit',evidence=evidence)
                manifest['files'][name]['sha256']=h;manifest['files'][name]['pathStatBaseline']=anchors[name]
                if time.monotonic()-last>=10:progress('backup_copy',files=index,total=len(initial['files']));last=time.monotonic()
            assert_tree_same(snapshot(client,guard),initial,stage='after_complete_copy',evidence=evidence)
            for index,(name,attrs) in enumerate(sorted(initial['files'].items()),1):
                h=read_remote(client,name,attrs,guard,evidence=evidence,anchors=anchors)
                assert_hash_same(h,manifest['files'][name]['sha256'],name=name,stage='second_complete_remote_read',evidence=evidence)
                if time.monotonic()-last>=10:progress('backup_second_read',files=index,total=len(initial['files']));last=time.monotonic()
            assert_tree_same(snapshot(client,guard),initial,stage='after_second_complete_read',evidence=evidence)
            write(root/'manifest.json',manifest);progress('archive_restore_structure_checks')
            archive,restore=archive_and_restore(root,manifest,guard)
            expected={n:baseline['doubleReadHashes'][n] for n in ('paper.jar','server.jar','plugins/FallenKingdom-2.24.9.jar','plugins/FKAmis-1.0.0.jar')}
            checks=structure_checks(restore,guard,expected);checks.update(deep_checks(restore,guard))
            snake=server.ROOT/'.cache/m2/org/yaml/snakeyaml/2.2/snakeyaml-2.2.jar'
            result=subprocess.run([str(server.java_path()),'-cp',str(snake),str(server.ROOT/'scripts/BackupYamlCheck.java'),str(restore)],capture_output=True,text=True,encoding='utf-8',timeout=120)
            guard.check()
            if result.returncode:raise Unsafe('BackupYamlValidationFailed')
            checks.update(json.loads(result.stdout));checks['yamlCheckedBySafeParser']=True
            assert_tree_same(snapshot(client,guard),initial,stage='after_local_restore_checks',evidence=evidence)
            if api.info()!=info:raise Unsafe('PanelSettingsChanged')
            guard.poll();guard.close();guard.check()
        final=root/'instance.zip';archive.rename(final)
        for path in (final,root/'manifest.json'):path.with_suffix(path.suffix+'.sha256').write_text(digest(path)+'\n',encoding='ascii')
        report.update({'status':'binary_and_structural_verified_under_derogation','finishedAtUtc':now(),'backupValidated':True,
            'files':len(initial['files']),'directories':len(initial['directories']),'sourceBytes':total,
            'archiveSha256':digest(final),'manifestSha256':digest(root/'manifest.json'),'doubleRemoteReadVerified':True,
            'restoreAllFilesIdentical':True,'structuralChecks':checks,'linuxOwnershipRestoredOnWindows':False,
            'criticalAttributesVerified':True,'optionalAbsentValuesNotAssumedEqual':True,
            'apiSamples':len(guard.samples)})
        write(root/'report.json',report);progress('backup_binary_verified',files=report['files'],archiveSha256=report['archiveSha256'],manifestSha256=report['manifestSha256'])
        return 0
    except Exception as error:
        report.update({'status':'aborted','failure':guard.reason or (str(error) if isinstance(error,Unsafe) else type(error).__name__),'finishedAtUtc':now()})
        write(root/'report.json',report);progress('backup_aborted',reason=report['failure']);return 1
    finally:
        guard.close();write(root/'api-observations.json',guard.samples);trace.close()
        if transport:transport.close()
        api.token=None;config.clear()

if __name__=='__main__':
    try:sys.exit(run(json.load(sys.stdin)))
    except Exception as error:progress('backup_not_started',reason=str(error) if isinstance(error,Unsafe) else type(error).__name__);sys.exit(1)
