"""Sauvegarde dérogatoire ponctuelle, GET et SFTP en lecture uniquement."""
import sys
sys.dont_write_bytecode=True
import base64
import ctypes
from ctypes import wintypes
from datetime import datetime,timezone
import gzip
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import struct
import subprocess
import threading
import time
import urllib.request
import zipfile
import zlib
from minestrator_sftp_inventory import pin_matches
from map_reader import nbt
from sftp_attributes import capture,compare

logging.getLogger('paramiko').setLevel(logging.CRITICAL)
OPERATION='MS-COLD-20261119-02'
class Unsafe(RuntimeError):
    def __init__(self,reason,*,details=None):super().__init__(reason);self.details=details
def now():return datetime.now(timezone.utc).isoformat()
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def safe_name(name):
    if not name or name in ('.','..') or any(c in name for c in '/\\:<>"|?*') or any(ord(c)<32 for c in name) or name.endswith((' ','.')) or re.match(r'(?i)^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',name):raise Unsafe('UnsafeRemotePath')
    return name
def metadata(item):
    observed=capture(item)
    return {key:observed['attributes'][key]['value'] for key in ('size','mtime','mode','uid','gid')}|{'_sftp':observed}
def compare_observation(observed,expected,*,name=None,stage='unspecified',same_source=False,evidence=None):
    if '_sftp' not in expected or '_sftp' not in observed:raise Unsafe('AttributeBaselineUnavailable')
    for record in (expected,observed):
        for field in ('size','mtime','mode','uid','gid'):
            if record[field]!=record['_sftp']['attributes'][field]['value']:raise Unsafe('AttributeRecordInconsistent',details={'path':name,'stage':stage,'field':field})
    result=compare(expected['_sftp'],observed['_sftp'],same_source=same_source)
    detail={'atUtc':now(),'path':name,'stage':stage,'expected':expected['_sftp'],'observed':observed['_sftp'],'comparison':result}
    if evidence:evidence(detail)
    if not result['accepted']:
        reason='CriticalAttributeUnavailable' if result['missingCritical'] else 'AttributeAvailabilityLost' if result['availabilityLost'] else 'ConcurrentFileChange'
        raise Unsafe(reason,details=detail)
    return result
def assert_same(item,expected,**kwargs):return compare_observation(metadata(item),expected,**kwargs)
def assert_tree_same(observed,expected,*,stage,evidence=None):
    for group in ('files','directories'):
        if observed[group].keys()!=expected[group].keys():raise Unsafe('RemoteTreeChanged',details={'stage':stage,'group':group,'added':sorted(observed[group].keys()-expected[group].keys()),'removed':sorted(expected[group].keys()-observed[group].keys())})
        for name in expected[group]:compare_observation(observed[group][name],expected[group][name],name=name,stage=stage,same_source=True,evidence=evidence)
def assert_hash_same(actual,expected,*,name,stage,evidence=None):
    if actual!=expected:
        detail={'path':name,'stage':stage,'expectedSha256':expected,'observedSha256':actual}
        if evidence:evidence(detail)
        raise Unsafe('RemoteHashChanged',details=detail)
def snapshot(client,guard):
    files={};dirs={};seen=set();stack=['']
    while stack:
        folder=stack.pop();guard.check()
        for item in client.listdir_attr(folder or '.'):
            name=safe_name(item.filename);path=(folder+'/'+name).lstrip('/')
            attrs=metadata(item)
            if attrs['_sftp']['attributes']['type']['available'] and not(stat.S_ISDIR(item.st_mode) or stat.S_ISREG(item.st_mode)):raise Unsafe('LinkOrSpecialFile')
            compare_observation(attrs,attrs,name=path,stage='listdir_baseline')
            if path.casefold() in seen:raise Unsafe('WindowsPathCollision')
            seen.add(path.casefold())
            if len(seen)>100000:raise Unsafe('InventoryLimitExceeded')
            if stat.S_ISDIR(item.st_mode):dirs[path]=attrs;stack.append(path)
            elif stat.S_ISREG(item.st_mode):files[path]=attrs
            else:raise Unsafe('LinkOrSpecialFile')
    return {'files':files,'directories':dirs}
class Api:
    def __init__(self,token,server_id):self.token=token;self.server_id=int(server_id)
    def get(self,suffix):
        # Aucune redirection avec transmission possible de l'autorisation.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        request=urllib.request.Request('https://mine.sttr.io/server/'+str(self.server_id)+suffix,headers={'Authorization':'Bearer '+self.token},method='GET')
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=3) as response:
            data=json.load(response)['api']
        if data.get('code')!=200:raise Unsafe('ApiCodeNot200')
        return data['data']
    def info(self):
        data=self.get('')
        if int(data['server']['id'])!=self.server_id:raise Unsafe('ServerIdentityMismatch')
        return {k:data.get(k) for k in ('settings','ports','offer')} | {'resources':data.get('mybox',{}).get('resources'),'port':data['server']['port']}
    def offline(self):
        data=self.get('/live')
        if data.get('state')!='offline' or data.get('stats',{}).get('state')!='offline':raise Unsafe('ServerNotOffline')
        return {'atUtc':now(),'state':'offline','statsState':'offline'}
class Guard:
    def __init__(self,api,interval=5):
        self.api=api;self.interval=interval;self.samples=[];self.stop_event=threading.Event();self.failed=threading.Event();self.reason=None;self.abort=lambda:None;self.lock=threading.Lock();self.last=time.monotonic();self.thread=None
    def poll(self):
        with self.lock:
            try:self.samples.append(self.api.offline());self.last=time.monotonic()
            except Exception as error:
                self.reason=str(error) if isinstance(error,Unsafe) else 'ApiObservationFailed'
                self.failed.set();self.abort();raise Unsafe(self.reason) from None
    def start(self):
        self.poll()
        def watch():
            while not self.stop_event.wait(self.interval):
                try:self.poll()
                except Unsafe:return
        self.thread=threading.Thread(target=watch,daemon=True);self.thread.start()
    def check(self):
        if self.failed.is_set():raise Unsafe(self.reason)
        if time.monotonic()-self.last>self.interval+8:
            self.reason='ObservationGapExceeded';self.failed.set();self.abort();raise Unsafe(self.reason)
    def close(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=5)
def read_remote(client,name,expected,guard,destination=None,*,evidence=None,anchors=None):
    guard.check();anchor=metadata(client.lstat(name))
    compare_observation(anchor,expected,name=name,stage='lstat_before_vs_listdir',evidence=evidence)
    if anchors is not None:
        if name in anchors:compare_observation(anchor,anchors[name],name=name,stage='lstat_before_vs_first_pass',same_source=True,evidence=evidence)
        else:anchors[name]=anchor
    h=hashlib.sha256();count=0
    with client.open(name,'rb') as source:
        handle_anchor=metadata(source.stat())
        compare_observation(handle_anchor,anchor,name=name,stage='fstat_before_vs_lstat',evidence=evidence)
        if hasattr(source,'prefetch'):source.prefetch(expected['size'],max_concurrent_requests=8)
        target=destination.open('xb') if destination else None
        try:
            while True:
                guard.check();chunk=source.read(256*1024);guard.check()
                if not chunk:break
                count+=len(chunk)
                if count>expected['size']:raise Unsafe('ConcurrentFileChange',details={'path':name,'stage':'read_byte_count_exceeded','expectedSize':expected['size'],'observedSize':count})
                h.update(chunk)
                if target:target.write(chunk)
            after=metadata(source.stat())
            compare_observation(after,handle_anchor,name=name,stage='fstat_after_vs_fstat_before',same_source=True,evidence=evidence)
            compare_observation(after,anchor,name=name,stage='fstat_after_vs_lstat_before',evidence=evidence)
        finally:
            if target:target.close()
    assert_same(client.lstat(name),anchor,name=name,stage='lstat_after_vs_lstat_before',same_source=True,evidence=evidence)
    if count!=expected['size']:raise Unsafe('ConcurrentFileChange',details={'path':name,'stage':'read_byte_count','expectedSize':expected['size'],'observedSize':count})
    return h.hexdigest()
def progress(stage,**values):print(json.dumps({'stage':stage,**values}),flush=True)
def protect_directory(root):
    if root.exists():raise Unsafe('DestinationAlreadyExists')
    root.mkdir(parents=True)
    sid=subprocess.run(['powershell.exe','-NoProfile','-Command','[Security.Principal.WindowsIdentity]::GetCurrent().User.Value'],capture_output=True,text=True,check=True).stdout.strip()
    result=subprocess.run(['icacls.exe',str(root),'/inheritance:r','/grant:r','*'+sid+':(OI)(CI)F'],capture_output=True)
    if result.returncode:raise Unsafe('PrivateAclFailed')
def protect_blob(data):
    class Blob(ctypes.Structure):_fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_byte))]
    buffer=ctypes.create_string_buffer(data);original=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_byte)));encrypted=Blob()
    crypt=ctypes.WinDLL('Crypt32',use_last_error=True)
    crypt.CryptProtectData.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    if not crypt.CryptProtectData(ctypes.byref(original),'FK backup panel',None,None,None,1,ctypes.byref(encrypted)):raise Unsafe('PanelEncryptionFailed')
    try:return ctypes.string_at(encrypted.pbData,encrypted.cbData)
    finally:
        kernel=ctypes.WinDLL('Kernel32');kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree(ctypes.cast(encrypted.pbData,ctypes.c_void_p))
def archive_and_restore(root,manifest,guard):
    copied=root/'download.partial';archive=root/'instance.zip.partial'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for name,attrs in sorted(manifest['directories'].items()):
            guard.check();entry=zipfile.ZipInfo(name+'/');entry.external_attr=(stat.S_IFDIR|attrs['mode'])<<16;z.writestr(entry,b'')
        for name,attrs in sorted(manifest['files'].items()):
            guard.check();entry=zipfile.ZipInfo(name);entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=(stat.S_IFREG|attrs['mode'])<<16
            h=hashlib.sha256()
            with (copied/name).open('rb') as source,z.open(entry,'w',force_zip64=True) as target:
                while chunk:=source.read(1024*1024):guard.check();h.update(chunk);target.write(chunk)
            if h.hexdigest()!=attrs['sha256']:raise Unsafe('LocalCopyChanged')
    restore=root/'restore';restore.mkdir()
    with zipfile.ZipFile(archive) as z:
        expected=set(manifest['files'])|{n+'/' for n in manifest['directories']}
        if len(z.namelist())!=len(expected) or set(z.namelist())!=expected:raise Unsafe('ArchiveManifestMismatch')
        for name in manifest['directories']:(restore/name).mkdir(parents=True,exist_ok=True)
        for name,attrs in manifest['files'].items():
            guard.check();target=restore/name;target.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256()
            with z.open(name) as source,target.open('xb') as output:
                while chunk:=source.read(1024*1024):guard.check();h.update(chunk);output.write(chunk)
            if h.hexdigest()!=attrs['sha256'] or digest(target)!=attrs['sha256']:raise Unsafe('RestoreHashMismatch')
    actual={p.relative_to(restore).as_posix() for p in restore.rglob('*') if p.is_file()}
    actual_dirs={p.relative_to(restore).as_posix() for p in restore.rglob('*') if p.is_dir()}
    if actual!=set(manifest['files']) or actual_dirs!=set(manifest['directories']):raise Unsafe('RestoreTreeMismatch')
    return archive,restore
def structure_checks(restore,guard,expected_hashes):
    result={'regionFiles':0,'chunksDecoded':0,'nbtFiles':0,'playerProfiles':0,'jsonFiles':0,'jarFiles':0,'inventoryBearingRecords':0,'yamlCheckedBySafeParser':False,'paperStarted':False}
    def inventories(data):
        if isinstance(data,dict):
            for key,value in data.items():
                if key in ('Inventory','inventory','Items','items') and isinstance(value,list):result['inventoryBearingRecords']+=1
                inventories(value)
        elif isinstance(data,list):
            for value in data:inventories(value)
    for file in restore.rglob('*'):
        if not file.is_file():continue
        guard.check();name=file.relative_to(restore).as_posix()
        if name.startswith(('world/','world_nether/','world_the_end/')) and file.suffix=='.mca':
            data=file.read_bytes()
            if len(data)<8192 or len(data)%4096:raise Unsafe('InvalidRegionSize')
            occupied=set()
            for index in range(1024):
                offset=int.from_bytes(data[index*4:index*4+3],'big');sectors=data[index*4+3]
                if not offset:
                    if sectors:raise Unsafe('InvalidRegionHeader')
                    continue
                if offset<2 or not sectors or (offset+sectors)*4096>len(data):raise Unsafe('InvalidRegionBounds')
                if occupied.intersection(range(offset,offset+sectors)):raise Unsafe('OverlappingRegionChunks')
                occupied.update(range(offset,offset+sectors));at=offset*4096;length=int.from_bytes(data[at:at+4],'big');codec=data[at+4]
                if length<1 or length+4>sectors*4096 or codec&128:raise Unsafe('UnsupportedOrInvalidRegionChunk')
                chunk=data[at+5:at+4+length]
                if codec==1:chunk=gzip.decompress(chunk)
                elif codec==2:chunk=zlib.decompress(chunk)
                elif codec!=3:raise Unsafe('UnsupportedRegionCompression')
                inventories(nbt(chunk));result['chunksDecoded']+=1
            result['regionFiles']+=1
        elif name.startswith(('world/','world_nether/','world_the_end/')) and (name.endswith('.dat') or name.endswith('.dat_old')):
            data=file.read_bytes();data=gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data
            inventories(nbt(data));result['nbtFiles']+=1
            if '/players/data/' in name or '/playerdata/' in name:result['playerProfiles']+=1
        elif file.suffix=='.json':json.loads(file.read_text(encoding='utf-8-sig'));result['jsonFiles']+=1
        elif name=='paper.jar' or (name.startswith('plugins/') and name.count('/')==1 and name.endswith('.jar')):
            with zipfile.ZipFile(file) as z:
                if z.testzip() is not None:raise Unsafe('JarCrcFailure')
            result['jarFiles']+=1
    for name,expected in expected_hashes.items():
        if not (restore/name).is_file() or digest(restore/name)!=expected:raise Unsafe('InstalledArtifactMismatch')
    state=(restore/'plugins/FKAmis/state.yml').read_text(encoding='utf-8-sig')
    if not re.search(r'^schema: 1\s*$',state,re.M):raise Unsafe('UnsupportedGameStateSchema')
    for name in ('world/level.dat','plugins/FKAmis/config.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','server.properties','RUNTIME_LOCK.json'):
        if not (restore/name).is_file():raise Unsafe('CriticalFileMissing')
    lock=json.loads((restore/'RUNTIME_LOCK.json').read_text(encoding='utf-8-sig'))
    for name in ('paper.jar','plugins/FKAmis-1.0.0.jar','plugins/FallenKingdom-2.24.9.jar'):
        if lock.get('sha256',{}).get(name)!=digest(restore/name):raise Unsafe('RuntimeRegistryMismatch')
    return result
def run(config):
    import paramiko
    repository=Path(__file__).resolve().parents[1];root=Path(config['destination']).resolve()
    if config.get('operationId')!=OPERATION or root.name!=OPERATION:raise Unsafe('DerogationScopeMismatch')
    if root.is_relative_to(repository) or repository.is_relative_to(root):raise Unsafe('BackupInsideRepository')
    for parent in (root,*root.parents):
        if parent.is_symlink() or (parent.exists() and parent.is_junction()):raise Unsafe('UnsafeLocalPath')
    protect_directory(root)
    report={'operationId':OPERATION,'startedAtUtc':now(),'status':'in_progress','sharedRemoteLock':False,'derogationExplicitlyAuthorized':True,'schedulingDisabledVerified':False,'remoteWritesPerformed':False,'deploymentAuthorized':False,'completelyGuaranteed':False}
    api=Api(config.pop('apiKey'),config['serverId']);guard=Guard(api);transport=None
    trace=(root/'sftp-attributes.jsonl').open('x',encoding='utf-8')
    def evidence(data):trace.write(json.dumps(data,ensure_ascii=False)+'\n');trace.flush()
    try:
        info=api.info();(root/'panel-settings.dpapi').write_bytes(protect_blob(json.dumps(info,sort_keys=True).encode()))
        guard.start();progress('offline_confirmed',apiIntervalSeconds=5)
        transport=paramiko.Transport(socket.create_connection((config['host'],int(config['port'])),timeout=15));guard.abort=transport.close
        transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),config['fingerprint']):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        with paramiko.SFTPClient.from_transport(transport) as client:
            client.get_channel().settimeout(10)
            initial=snapshot(client,guard);total=sum(x['size'] for x in initial['files'].values())
            write(root/'initial-inventory.json',initial)
            write(root/'download-order.json',list(initial['files']))
            if shutil.disk_usage(root).free<total*3+128*1024**2:raise Unsafe('InsufficientLocalSpace')
            guard.poll();progress('inventory_ready',files=len(initial['files']),directories=len(initial['directories']),bytes=total)
            copy=root/'download.partial';copy.mkdir()
            for name in initial['directories']:(copy/name).mkdir(parents=True,exist_ok=True)
            manifest=json.loads(json.dumps(initial));done=0;last=time.monotonic();anchors={}
            for name,attrs in initial['files'].items():
                target=copy/name;target.parent.mkdir(parents=True,exist_ok=True)
                manifest['files'][name]['sha256']=read_remote(client,name,attrs,guard,target,evidence=evidence,anchors=anchors)
                manifest['files'][name]['pathStatBaseline']=anchors[name];done+=1
                if time.monotonic()-last>=10:progress('downloading',files=done,totalFiles=len(initial['files']));last=time.monotonic()
            assert_tree_same(snapshot(client,guard),initial,stage='tree_after_copy',evidence=evidence)
            progress('second_remote_read_started');done=0;last=time.monotonic()
            for name,attrs in initial['files'].items():
                actual_hash=read_remote(client,name,attrs,guard,evidence=evidence,anchors=anchors)
                assert_hash_same(actual_hash,manifest['files'][name]['sha256'],name=name,stage='second_remote_sha256',evidence=evidence)
                done+=1
                if time.monotonic()-last>=10:progress('remote_hashes',files=done,totalFiles=len(initial['files']));last=time.monotonic()
            assert_tree_same(snapshot(client,guard),initial,stage='tree_after_second_read',evidence=evidence)
            guard.poll();write(root/'manifest.json',manifest)
            progress('archive_and_restore_started');archive,restore=archive_and_restore(root,manifest,guard)
            checks=structure_checks(restore,guard,config['expectedHashes'])
            # Analyse YAML par SnakeYAML sûr, sans démarrage Minecraft ni exécution de tags objets.
            yaml=subprocess.run([config['java'],'-cp',config['snakeYamlJar'],str(repository/'scripts/BackupYamlCheck.java'),str(restore)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
            guard.check()
            if yaml.returncode:raise Unsafe('YamlStructureCheckFailed')
            checks.update(json.loads(yaml.stdout));checks['yamlCheckedBySafeParser']=True
            for name,anchor in anchors.items():
                guard.check();assert_same(client.lstat(name),anchor,name=name,stage='lstat_final',same_source=True,evidence=evidence)
            assert_tree_same(snapshot(client,guard),initial,stage='tree_final',evidence=evidence)
            if api.info()!=info:raise Unsafe('PanelSettingsChanged')
            guard.poll();guard.close();guard.check()
        final=root/'instance.zip';archive.replace(final);sha=digest(final)
        (root/'instance.zip.sha256').write_text(sha+'\n',encoding='ascii')
        (root/'manifest.json.sha256').write_text(digest(root/'manifest.json')+'\n',encoding='ascii')
        report.update({'status':'verified_under_derogation','finishedAtUtc':now(),'files':len(initial['files']),'directories':len(initial['directories']),'sourceBytes':total,'archiveSha256':sha,'manifestSha256':digest(root/'manifest.json'),'secondRemoteHashPass':True,'remoteMetadataCriticalFieldsVerified':True,'optionalListingAttributesNeverAssumedEqualWhenAbsent':True,'restoreAllFilesIdentical':True,'structuralChecks':checks,'apiSamples':len(guard.samples),'paperStarted':False,'linuxOwnershipRestoredOnWindows':False,'residualRisk':'Échantillonnage périodique et doubles lectures non atomiques ; écritures transitoires indétectables possibles.'})
        report['ownershipEvidence']={'filePathStatBaselinesKnown':sum(all(a['_sftp']['attributes'][f]['available'] for f in ('uid','gid')) for a in anchors.values()),'filePathStatBaselinesUnverified':sum(not all(a['_sftp']['attributes'][f]['available'] for f in ('uid','gid')) for a in anchors.values()),'directoryListingOwnershipUnverified':sum(not all(a['_sftp']['attributes'][f]['available'] for f in ('uid','gid')) for a in initial['directories'].values()),'absentValuesProveStability':False}
        write(root/'report.json',report);write(root/'api-observations.json',guard.samples)
        progress('completed',destination=str(root),files=report['files'],archiveSha256=sha,completelyGuaranteed=False)
        return 0
    except Exception as error:
        guard.close()
        report.update({'status':'aborted','finishedAtUtc':now(),'reason':guard.reason or (str(error) if isinstance(error,Unsafe) else type(error).__name__),'failureDetailsPrivate':getattr(error,'details',None),'backupValidated':False,'restoreValidated':False,'apiSamples':len(guard.samples)})
        write(root/'report.json',report);write(root/'api-observations.json',guard.samples)
        progress('aborted',reason=report['reason'],destination=str(root));return 1
    finally:
        trace.close()
        guard.close();config.clear();api.token=None
        if transport:transport.close()
if __name__=='__main__':
    try:sys.exit(run(json.load(sys.stdin)))
    except Exception as error:
        progress('not_started',reason=str(error) if isinstance(error,Unsafe) else type(error).__name__);sys.exit(1)
