"""Déploiement autorisé V2.1 : phases journalisées, aucun effacement ni partie lancée."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import socket
import stat
import struct
import time
import traceback
import urllib.request
import zlib
import gzip
from minestrator_final_audit import BACKUP,CANDIDATE,EXPECTED_SERVER,EXPECTED_HOST,PIN,unprotect,local_checks
from minestrator_cold_backup import (Api,Guard,Unsafe,now,write,digest,protect_directory,snapshot,assert_tree_same,
    metadata,compare_observation,read_remote,assert_hash_same,progress,protect_blob)
from minestrator_sftp_inventory import pin_matches
from map_reader import Reader,nbt
import server
sys.modules['serverlib']=server
sys.path.insert(0,str(server.ROOT/'deployment'))
from new_match import section

OP='MS-DEPLOY-V21-20261120-01'
STAGE='.fk-stage/'+OP
QUARANTINE='.fk-quarantine/'+OP
PATCH=Path.home()/'FKBackups/MS-RESTART-CHECK-20261120-01/proposed-maintenance/spigot.yml'
PATCH_SHA='63e939902bc52b0868598205130a94bb5e9f3733073008a05399fddfef687667'
COMMANDS=('version','plugins','fka status','fka config validate','fka config list','fka info teams','fka nether portal status','list','tps','mspt')

class DeployApi(Api):
    def put(self,suffix,value):
        if not ((suffix=='/poweraction' and value in ({'poweraction':'start'},{'poweraction':'stop'})) or
                (suffix=='/command' and value.get('command') in COMMANDS)):
            raise Unsafe('ApiMutationNotAllowed')
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        body=json.dumps(value).encode()
        req=urllib.request.Request('https://mine.sttr.io/server/'+str(self.server_id)+suffix,data=body,
            headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'},method='PUT')
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=20) as response:data=json.load(response)['api']
        if data.get('code')!=200:raise Unsafe('ApiMutationRefused')
        return data.get('data')

class Transaction:
    def __init__(self,client,guard,work,report):self.client=client;self.guard=guard;self.work=work;self.report=report
    def event(self,action,**data):
        value={'atUtc':now(),'action':action,**data}
        with (self.work/'journal.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False)+'\n');stream.flush()
        self.report['lastEvent']=value;self.save()
    def save(self):write(self.work/'report.json',self.report)
    def state(self,value):self.report['state']=value;self.event('state',state=value);progress('deployment_state',state=value)
    def attr(self,path):
        try:return self.client.lstat(path)
        except FileNotFoundError:return None
    def absent(self,path):
        if self.attr(path) is not None:raise Unsafe('DestinationAlreadyExists',details={'path':path})
    def mkdirs(self,path,private=False):
        if path in ('','.'):return
        current=''
        for part in PurePosixPath(path).parts:
            if part in ('','..','.') or part.startswith('/'):raise Unsafe('UnsafeRemotePath')
            current=(current+'/'+part).lstrip('/');self.guard.check();item=self.attr(current)
            if item is not None:
                if not stat.S_ISDIR(item.st_mode):raise Unsafe('RemoteParentNotDirectory')
                continue
            self.event('mkdir_intent',path=current)
            self.report['remoteWritesPerformed']=True
            self.client.mkdir(current,0o700 if private else 0o755);self.guard.check()
            self.event('mkdir_done',path=current)
    def hash(self,path):
        item=self.client.lstat(path)
        if not stat.S_ISREG(item.st_mode):raise Unsafe('NotRegularFile',details={'path':path})
        return read_remote(self.client,path,metadata(item),self.guard)
    def expect_hash(self,path,expected):assert_hash_same(self.hash(path),expected,name=path,stage='deployment_verify')
    def upload(self,local,path,expected,mode=0o644,mtime=None):
        self.guard.check();self.absent(path);self.mkdirs(str(PurePosixPath(path).parent))
        if digest(local)!=expected:raise Unsafe('LocalPayloadChanged',details={'path':path})
        self.event('upload_intent',path=path,sha256=expected,bytes=local.stat().st_size)
        self.report['remoteWritesPerformed']=True
        h=hashlib.sha256();count=0
        # w+x : création exclusive, ne jamais tronquer un fichier existant.
        with local.open('rb') as source,self.client.open(path,'wx') as target:
            while data:=source.read(256*1024):
                self.guard.check();target.write(data);self.guard.check();h.update(data);count+=len(data)
            target.flush()
        if h.hexdigest()!=expected:raise Unsafe('LocalPayloadChangedDuringUpload')
        self.client.chmod(path,mode)
        if mtime is not None:self.client.utime(path,(mtime,mtime))
        if stat.S_IMODE(self.client.lstat(path).st_mode)!=mode:raise Unsafe('UploadedPermissionsMismatch')
        self.guard.check();self.expect_hash(path,expected)
        self.event('upload_verified',path=path,sha256=expected,bytes=count)
    def move(self,source,target,expected=None):
        self.guard.check();self.absent(target)
        item=self.client.lstat(source)
        if not (stat.S_ISREG(item.st_mode) or stat.S_ISDIR(item.st_mode)):raise Unsafe('UnsafeRenameSource')
        if expected is not None:self.expect_hash(source,expected)
        self.mkdirs(str(PurePosixPath(target).parent),private=target.startswith(QUARANTINE))
        self.event('rename_intent',source=source,target=target)
        self.report['remoteWritesPerformed']=True
        self.client.rename(source,target);self.guard.check()
        self.event('rename_done',source=source,target=target)
        if expected is not None:self.expect_hash(target,expected)

def verify_info(api):
    info=api.info();previous=unprotect(BACKUP/'panel-settings.dpapi')
    if info!=previous:raise Unsafe('PanelSettingsChanged')
    if int(info['port'])!=22880 or int((info.get('settings') or {})['id_java_version'])!=61:raise Unsafe('PanelVersionMismatch')
    return info

def preflight(tx,baseline,plan):
    observed=snapshot(tx.client,tx.guard)
    assert_tree_same(observed,baseline,stage='deployment_preflight_metadata')
    critical=set(plan['retainUnchanged'])|{'spigot.yml','server.properties','FKAmis.sha256','RUNTIME_LOCK.json',
      'plugins/FKAmis-1.0.0.jar','plugins/FKAmis/state.yml','plugins/FKAmis/config.yml','plugins/FKAmis/admins.yml',
      'plugins/FKAmis/supplies.yml','config/paper-global.yml','start.sh','start.ps1','DEPLOYMENT_MANIFEST.json'}
    for name in sorted(critical):
        actual=read_remote(tx.client,name,baseline['files'][name],tx.guard,
          anchors={name:baseline['files'][name]['pathStatBaseline']})
        assert_hash_same(actual,baseline['files'][name]['sha256'],name=name,stage='targeted_prewrite_hash')
    tx.report.update({'preflightSourceFilesMetadata':len(observed['files']),'preflightSourceDirectoriesMetadata':len(observed['directories']),
      'targetedPrewriteHashes':len(critical),'fullSourceContentAuditRepeated':False})
    tx.state('PREFLIGHT_OK')

def inspect_source_tree(tx,prefix,baseline):
    for group in ('directories','files'):
        for name,attrs in baseline[group].items():
            if name==prefix or name.startswith(prefix+'/'):
                tx.guard.check();anchor=attrs.get('pathStatBaseline',attrs)
                compare_observation(metadata(tx.client.lstat(name)),anchor,name=name,stage='before_quarantine_metadata')

def install(tx,baseline,plan,operation):
    preflight(tx,baseline,plan)
    tx.absent(STAGE);tx.absent(QUARANTINE)
    tx.mkdirs(STAGE,True);tx.mkdirs(QUARANTINE,True)
    tx.upload(PATCH,STAGE+'/maintenance/spigot.yml',PATCH_SHA,baseline['files']['spigot.yml']['mode'])
    tx.move('spigot.yml',QUARANTINE+'/files/spigot.yml',baseline['files']['spigot.yml']['sha256'])
    tx.move(STAGE+'/maintenance/spigot.yml','spigot.yml',PATCH_SHA)
    tx.report['spigotPatchApplied']=True;tx.state('RESTART_DISABLED')
    for i,entry in enumerate(plan['files'],1):
        name=entry['path'];mode=baseline['files'].get(name,{}).get('mode',0o644)
        tx.upload(CANDIDATE/'payload'/name,STAGE+'/payload/'+name,entry['newSha256'],mode)
        tx.report['stagedFiles']=i
        if i%15==0:progress('stage_progress',files=i,total=148)
    tx.state('STAGED')
    # Second contrôle de toutes les cibles avant de toucher aux anciens arbres.
    for entry in plan['files']:tx.expect_hash(STAGE+'/payload/'+entry['path'],entry['newSha256'])
    trees=[n for n in operation['quarantineWholeTrees'] if n in baseline['directories']]
    for tree in trees:
        inspect_source_tree(tx,tree,baseline);tx.move(tree,QUARANTINE+'/trees/'+tree)
        for name,attrs in baseline['files'].items():
            if name.startswith(tree+'/'):tx.expect_hash(QUARANTINE+'/trees/'+name,attrs['sha256'])
    for name in operation['quarantineIndividualFiles']:
        tx.move(name,QUARANTINE+'/files/'+name,baseline['files'][name]['sha256'])
    tx.report['quarantineSourceFiles']=len(operation['oldFilesInWholeTrees'])+len(operation['quarantineIndividualFiles'])+1
    tx.state('QUARANTINED')
    tx.guard.check();tx.report['activationStarted']=True;tx.state('ACTIVATING')
    active_trees=('world','plugins/FKAmis','plugins/FallenKingdom')
    for tree in active_trees:tx.move(STAGE+'/payload/'+tree,tree)
    # Les autres fichiers passent individuellement ; manifeste en dernier.
    entries=sorted(plan['files'],key=lambda f:(f['path']=='DEPLOYMENT_MANIFEST.json',f['path']))
    for entry in entries:
        name=entry['path']
        if any(name.startswith(tree+'/') for tree in active_trees):continue
        tx.move(STAGE+'/payload/'+name,name,entry['newSha256'])
    tx.state('ACTIVATED')
    permissions=[]
    for entry in plan['files']:
        name=entry['path'];tx.expect_hash(name,entry['newSha256']);attrs=metadata(tx.client.lstat(name))
        if attrs['mode']!=baseline['files'].get(name,{}).get('mode',0o644):raise Unsafe('InstalledPermissionsMismatch',details={'path':name})
        owner_anchor=baseline['files'].get(name,baseline['files']['paper.jar'])['pathStatBaseline']
        owner_verified=[]
        for field in ('uid','gid'):
            available=attrs['_sftp']['attributes'][field]['available'] and owner_anchor['_sftp']['attributes'][field]['available']
            if available:
                if attrs[field]!=owner_anchor[field]:raise Unsafe('InstalledOwnershipMismatch',details={'path':name,'field':field})
                owner_verified.append(field)
        permissions.append({'path':name,'mode':attrs['mode'],'ownershipFieldsVerified':owner_verified})
    write(tx.work/'installed-permissions-private.json',permissions)
    write(tx.work/'installed-manifest.json',{'operation':OP,'files':{entry['path']:entry['newSha256'] for entry in plan['files']},'spigot.yml':PATCH_SHA})
    for name,h in plan['retainUnchanged'].items():tx.expect_hash(name,h)
    tx.expect_hash('spigot.yml',PATCH_SHA)
    # Aucune ancienne donnée supplémentaire dans les trois arbres remplacés.
    for tree in active_trees:
        found=remote_files(tx.client,tree,tx.guard)
        expected={f['path'] for f in plan['files'] if f['path'].startswith(tree+'/')}
        if set(found)!=expected:raise Unsafe('UnexpectedActiveTreeFiles',details={'tree':tree})
    tx.report.update({'installedFiles':148,'installedSha256Verified':148,'retainedCoreVerified':5,'restartOnCrash':False,
      'whitelistUnchanged':True,'historicalDataMerged':False,'installationOfflineVerified':True,'installedFileModesVerified':148,
      'installedOwnershipVerifiedFiles':sum(len(p['ownershipFieldsVerified'])==2 for p in permissions)})
    tx.guard.poll();tx.guard.check()
    tx.state('INSTALLED_OFFLINE_VERIFIED')

def remote_files(client,root,guard,exclude_technical=False):
    found={};stack=[root]
    while stack:
        guard.check();folder=stack.pop()
        for item in client.listdir_attr(folder or '.'):
            if '/' in item.filename or '\\' in item.filename or item.filename in ('.','..'):raise Unsafe('UnsafeRemotePath')
            if not folder and exclude_technical and item.filename in ('.fk-stage','.fk-quarantine'):
                if not stat.S_ISDIR(item.st_mode):raise Unsafe('UnsafeTechnicalNamespace')
                continue
            name=(folder+'/'+item.filename).lstrip('/')
            if stat.S_ISDIR(item.st_mode):stack.append(name)
            elif stat.S_ISREG(item.st_mode):found[name]=metadata(item)
            else:raise Unsafe('UnexpectedFileType')
    return found

def read_bytes(client,path,limit=8*1024**2):
    attrs=client.lstat(path)
    if not stat.S_ISREG(attrs.st_mode) or attrs.st_size>limit:raise Unsafe('UnexpectedRuntimeFile')
    with client.open(path,'rb') as source:data=source.read(limit+1)
    if len(data)>limit:raise Unsafe('RuntimeReadLimit')
    return data

def clean_log(text):return re.sub(r'\x1b\[[0-9;]*m','',text)

class OnlineGuard(Guard):
    """Même surveillance et arrêt du transport, avec l'état online attendu après démarrage."""
    def poll(self):
        with self.lock:
            try:
                live=self.api.get('/live');state=live.get('state');stats=(live.get('stats') or {}).get('state')
                self.samples.append({'atUtc':now(),'state':state,'statsState':stats})
                if state!='online' or stats!='online':raise Unsafe('UnexpectedRuntimeState')
                self.last=time.monotonic()
            except Exception as error:
                self.reason=str(error) if isinstance(error,Unsafe) else 'ApiObservationFailed'
                self.failed.set();self.abort();raise Unsafe(self.reason) from None

class RemoteReader(Reader):
    def __init__(self,client,guard):self.client=client;self.guard=guard;self.chunks={}
    def chunk(self,cx,cz):
        self.guard.check()
        if (cx,cz) in self.chunks:return self.chunks[cx,cz]
        path=f'world/dimensions/minecraft/overworld/region/r.{cx//32}.{cz//32}.mca'
        a=self.client.lstat(path)
        with self.client.open(path,'rb') as f:
            f.seek(((cx%32)+(cz%32)*32)*4);header=f.read(4);offset=int.from_bytes(header[:3],'big')
            if not offset:raise Unsafe('ExpectedChunkMissing')
            f.seek(offset*4096);size=int.from_bytes(f.read(4),'big');codec=f.read(1)[0];data=f.read(size-1)
        b=self.client.lstat(path)
        if (a.st_size,a.st_mtime)!=(b.st_size,b.st_mtime):raise Unsafe('RuntimeRegionChangedDuringRead')
        if codec==2:data=zlib.decompress(data)
        elif codec==1:data=gzip.decompress(data)
        elif codec!=3:raise Unsafe('UnsupportedRuntimeRegion')
        result=nbt(data);self.chunks[cx,cz]=result;return result

def world_checks(client,guard):
    guard.check()
    state=read_bytes(client,'plugins/FKAmis/state.yml').decode('utf-8-sig')
    for keys,expected in [(('schema',),'1'),(('day',),'0'),(('started',),'false'),(('players-per-team',),'4')]:
        if section(state,keys)!=expected:raise Unsafe('UnexpectedGameState',details={'field':'.'.join(keys)})
    for key in ('roster','objectives'):
        if section(state,(key,)) not in (None,'{}'):raise Unsafe('UnexpectedInitialRosterOrObjectives')
    reference=json.loads((CANDIDATE/'preproduction-candidate/maintenance/new-match-reference-v2.1.json').read_text())
    reader=RemoteReader(client,guard);local_reader=Reader(CANDIDATE/'preproduction-candidate');spawns=0
    for base in reference['bases']:
        team=base['team']
        if section(state,('native','TeamManager',team,'Base','Radius'))!='40':raise Unsafe('TerritoryRadiusMismatch')
        if section(state,('native','TeamManager',team,'Members'))!='[]':raise Unsafe('UnexpectedNativeMembers')
        for key,value in base['spawn'].items():
            if abs(float(section(state,('spawns',team,key)))-float(value))>1e-6:raise Unsafe('SpawnMismatch')
        import math
        p=base['spawn'];x,y,z=(math.floor(p[k]) for k in ('x','y','z'))
        for dy in (-1,0,1):
            if reader.block(x,y+dy,z)!=local_reader.block(x,y+dy,z):raise Unsafe('SpawnBlocksMismatch')
        spawns+=1
    blocks=0
    for cave in reference['caverns']:
        observed=[[x,y,z,reader.block(x,y,z)] for x,y,z in cave['checkPoints']]
        actual=hashlib.sha256(json.dumps(observed,separators=(',',':')).encode()).hexdigest()
        if actual!=cave['blockTypesSha256']:raise Unsafe('CavernBlocksMismatch',details={'team':cave['team']})
        blocks+=len(observed)
    return {'day':0,'gameStarted':False,'officialParticipants':0,'territoryRadius':40,'territoriesVerified':4,'spawnsVerified':spawns,
      'cavernsVerified':4,'cavernReferenceBlocksVerified':blocks,'regionChunksRead':len(reader.chunks),'humanMapInspectionPerformed':False}

def query_remote():
    session=b'\x01\x02\x03\x04'
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.settimeout(4);sock.sendto(b'\xfe\xfd\x09'+session,('91.197.6.72',22880));data,_=sock.recvfrom(65535)
        if data[:5]!=b'\x09'+session:raise Unsafe('QueryChallengeInvalid')
        challenge=int(data[5:].rstrip(b'\0'));sock.sendto(b'\xfe\xfd\x00'+session+struct.pack('>i',challenge)+b'\0'*4,('91.197.6.72',22880));data,_=sock.recvfrom(65535)
        if data[:5]!=b'\x00'+session or b'maxplayers\x0020\x00' not in data:raise Unsafe('QueryCapacityMismatch')
    return {'udpQueryResponded':True,'queryCapacity':20}

def verify_preserved_metadata(tx,baseline,plan,operation):
    moved={name for name in baseline['files'] if any(name.startswith(tree+'/') for tree in operation['quarantineWholeTrees'])}
    moved.update(operation['quarantineIndividualFiles']);moved.add('spigot.yml')
    preserved=set(baseline['files'])-moved
    expected=preserved|{f['path'] for f in plan['files']}|{'spigot.yml'}
    active=remote_files(tx.client,'',tx.guard,exclude_technical=True)
    if set(active)!=expected:raise Unsafe('ActiveInstanceFileSetChanged',details={'added':sorted(set(active)-expected),'missing':sorted(expected-set(active))})
    for name in sorted(preserved):
        tx.guard.check()
        compare_observation(metadata(tx.client.lstat(name)),baseline['files'][name]['pathStatBaseline'],name=name,stage='preserved_before_start',same_source=True)
    tx.report.update({'untouchedFilesMetadataRecheckedBeforeStart':len(preserved),'activeFileCountBeforeStart':len(active)})
    tx.event('preserved_metadata_verified',files=len(preserved),activeFiles=len(active))

def startup(tx,api,plan,baseline,operation):
    if tx.report.get('state')!='INSTALLED_OFFLINE_VERIFIED' or tx.report.get('startRequested'):raise Unsafe('StartPreconditionFailed')
    verify_preserved_metadata(tx,baseline,plan,operation)
    for entry in plan['files']:tx.expect_hash(entry['path'],entry['newSha256'])
    for name in ('paper.jar','server.jar','plugins/FallenKingdom-2.24.9.jar','whitelist.json','ops.json'):tx.expect_hash(name,plan['retainUnchanged'][name])
    tx.expect_hash('spigot.yml',PATCH_SHA)
    tx.guard.poll();tx.guard.check();tx.guard.close()
    verify_info(api)
    tx.report['startRequested']=True;tx.report['startRequestedAtUtc']=now();tx.event('api_start_intent')
    api.put('/poweraction',{'poweraction':'start'});tx.event('api_start_sent')
    deadline=time.monotonic()+240;log='';samples=[];online_seen=False
    while time.monotonic()<deadline:
        live=api.get('/live');samples.append({'atUtc':now(),'state':live.get('state'),'statsState':(live.get('stats') or {}).get('state')})
        if live.get('state')=='online':online_seen=True
        elif online_seen:raise Unsafe('ServerStoppedAfterStart')
        try:log=clean_log(read_bytes(tx.client,'logs/latest.log').decode('utf-8',errors='replace'))
        except FileNotFoundError:log=''
        (tx.work/'startup-private.log').write_text(log,encoding='utf-8');write(tx.work/'runtime-api-observations.json',samples)
        if re.search(r'\b(ERROR|SEVERE)\b',log):raise Unsafe('CriticalStartupLogError')
        if online_seen and 'Done (' in log and 'FKAmis prêt' in log:break
        time.sleep(3)
    else:raise Unsafe('StartupTimeout')
    online_guard=OnlineGuard(api);online_guard.abort=lambda:tx.client.get_channel().close()
    tx.guard=online_guard;online_guard.start()
    for command in COMMANDS:
        tx.event('read_command_intent',command=command);api.put('/command',{'command':command});time.sleep(.5)
    time.sleep(2)
    log=clean_log(read_bytes(tx.client,'logs/latest.log').decode('utf-8',errors='replace'));(tx.work/'startup-private.log').write_text(log,encoding='utf-8')
    if re.search(r'\b(ERROR|SEVERE)\b',log):raise Unsafe('CriticalStartupLogError')
    for marker in ('26.3-244','FallenKingdom','FKAmis prêt','Configuration cohérente','Jour 0','Query running on'):
        if marker not in log:raise Unsafe('StartupEvidenceMissing',details={'marker':marker})
    tx.report.update({'startupPassed':True,'startupErrorCount':0,'startupWarningCount':len(re.findall(r'\bWARN\b',log)),
      'paperVersionVerified':'26.3-244','fallenKingdomVerified':'2.24.9','restrictedWhitelistRetained':True})
    tx.report.update(world_checks(tx.client,tx.guard))
    try:tx.report.update(query_remote())
    except (TimeoutError,OSError) as error:tx.report.update({'udpQueryResponded':False,'udpQueryReadLimitation':type(error).__name__})
    live=api.get('/live');(tx.work/'live-after-start.dpapi').write_bytes(protect_blob(json.dumps(live).encode()))
    game=api.get('/live/light');(tx.work/'live-light-after-start.dpapi').write_bytes(protect_blob(json.dumps(game).encode()))
    players=(game.get('players') or (live.get('stats') or {}).get('players') or {})
    tx.report.update({'mineBoardApiPlayerCapacity':players.get('limit'),'mineBoardApiPlayersOnline':players.get('current'),'mineBoardVisualInspectionPerformed':False})
    if not tx.report['udpQueryResponded'] and players.get('limit')!=20:raise Unsafe('QueryReadinessNotConfirmed')
    if live.get('state')!='online':raise Unsafe('ServerNotOnlineAfterChecks')
    # Les politiques conservées et Spigot restent impératifs après le démarrage.
    for name in ('whitelist.json','ops.json'):tx.expect_hash(name,plan['retainUnchanged'][name])
    tx.expect_hash('spigot.yml',PATCH_SHA)
    tx.state('RUNNING_RECIPE_ONLY')

def wait_offline(api,timeout=120):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        try:api.offline();time.sleep(2);api.offline();return
        except Unsafe:time.sleep(3)
    raise Unsafe('RollbackOfflineNotConfirmed')

def rollback(tx,api,baseline):
    if not tx.report.get('activationStarted'):raise Unsafe('RollbackNotAuthorizedBeforeActivation')
    if tx.report.get('rollbackCompleted'):raise Unsafe('RollbackAlreadyCompleted')
    if not tx.report.get('failure') or not tx.report.get('requiresRollback'):raise Unsafe('RollbackRequiresCriticalDeploymentFailure')
    tx.guard.close();live=api.get('/live')
    if live.get('state')!='offline':tx.event('rollback_stop_intent');api.put('/poweraction',{'poweraction':'stop'})
    wait_offline(api);verify_info(api)
    # Vérifier le point entier local avant toute restauration, jamais le modifier.
    delivery=json.loads((server.ROOT/'tests/results/query-rollback-delivery.json').read_text())
    if digest(BACKUP/'instance.zip')!=delivery['originalArchiveSha256']:raise Unsafe('RollbackArchiveChanged')
    for name,attrs in baseline['files'].items():
        if digest(BACKUP/'restore'/name)!=attrs['sha256']:raise Unsafe('RollbackSourceChanged')
    if 'failure' in tx.report:tx.report['originalDeploymentFailure']=tx.report.pop('failure')
    tx.report['requiresRollback']=False
    guard=Guard(api);guard.start();tx.guard=guard;guard.abort=lambda:tx.client.get_channel().close()
    failed=QUARANTINE+'/failed-instance';tx.absent(failed);tx.mkdirs(failed,True)
    for item in tx.client.listdir_attr('.'):
        name=item.filename
        if name in ('.fk-stage','.fk-quarantine'):continue
        if '/' in name or '\\' in name or name in ('.','..') or not (stat.S_ISDIR(item.st_mode) or stat.S_ISREG(item.st_mode)):raise Unsafe('UnsafeRollbackRoot')
        tx.move(name,failed+'/'+name)
    tx.state('ROLLBACK_EMPTY_APPLICATION')
    for name,attrs in sorted(baseline['directories'].items(),key=lambda x:x[0].count('/')):tx.mkdirs(name)
    old_jar=baseline['files']['plugins/FKAmis-1.0.0.jar']['sha256'];marker=tx.work/'rollback-FKAmis.sha256';marker.write_text(old_jar+'\n',encoding='ascii')
    expected={}
    for i,(name,attrs) in enumerate(sorted(baseline['files'].items()),1):
        source=PATCH if name=='spigot.yml' else marker if name=='FKAmis.sha256' else BACKUP/'restore'/name
        h=digest(source);tx.upload(source,name,h,attrs['mode'],attrs['mtime']);expected[name]=h
        if i%25==0:progress('rollback_progress',files=i,total=305)
    for name,h in expected.items():tx.expect_hash(name,h)
    for name,attrs in baseline['directories'].items():tx.client.chmod(name,attrs['mode'])
    tx.report.update({'rollbackCompleted':True,'rollbackFilesVerified':305,'rollbackExceptions':['spigot.yml restart-on-crash=false','FKAmis.sha256 réconcilié'],
      'rollbackServerLeftOffline':True,'restartOnCrash':False})
    tx.state('ROLLED_BACK_OFFLINE')

def main(config):
    import paramiko
    if int(config['serverId'])!=EXPECTED_SERVER or config['host']!=EXPECTED_HOST or int(config['port'])!=2022 or config['fingerprint']!=PIN:raise Unsafe('IdentityMismatch')
    phase=config['phase'];work=Path(config['output']).resolve()
    if work.name!=OP or work.is_relative_to(server.ROOT) or work.is_relative_to(BACKUP):raise Unsafe('OperationScopeMismatch')
    baseline=json.loads((BACKUP/'manifest.json').read_text(encoding='utf-8'))
    plan=json.loads((CANDIDATE/'transfer-plan-private.json').read_text(encoding='utf-8'))
    operation=json.loads((Path.home()/'FKBackups/MS-PREFLIGHT-20261120-01/operation-plan-private.json').read_text())
    if phase=='install':
        local_checks()
        if digest(PATCH)!=PATCH_SHA:raise Unsafe('ApprovedSpigotPatchChanged')
        protect_directory(work)
        report={'operation':OP,'state':'PREPARED','deploymentAuthorized':True,'residualRisksExplicitlyAccepted':True,'startedAtUtc':now(),
          'activationStarted':False,'stagedFiles':0,'remoteWritesPerformed':False,'officialGameStartCommandSent':False,'serverId':EXPECTED_SERVER}
        write(work/'authorization-scope.json',{'serverId':EXPECTED_SERVER,'candidate':str(CANDIDATE),'targetFiles':148,'spigotPatchApproved':True,
          'installAndRestrictedStartApproved':True,'fullRollbackAfterActivationApproved':True,'irreversibleDeleteApproved':False,'restartOnCrashReenableApproved':False})
    else:
        report=json.loads((work/'report.json').read_text(encoding='utf-8'))
        if report['operation']!=OP:raise Unsafe('OperationScopeMismatch')
    api=DeployApi(config.pop('apiKey'),config['serverId']);transport=None;guard=Guard(api)
    tx=None
    try:
        info=verify_info(api)
        if phase in ('install','start'):guard.start()
        transport=paramiko.Transport(socket.create_connection((config['host'],int(config['port'])),timeout=15));guard.abort=transport.close;transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),PIN):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        with paramiko.SFTPClient.from_transport(transport) as client:
            client.get_channel().settimeout(30);tx=Transaction(client,guard,work,report)
            if phase=='install':
                install(tx,baseline,plan,operation)
            elif phase=='start':startup(tx,api,plan,baseline,operation)
            elif phase=='rollback':rollback(tx,api,baseline)
            else:raise Unsafe('UnknownPhase')
    except Exception as error:
        report['failure']=str(error) if isinstance(error,Unsafe) else type(error).__name__
        report['failedPhase']=phase;report['requiresRollback']=bool(report.get('activationStarted')) and phase!='rollback'
        write(work/'failure-stack-private.json',[{'file':frame.filename,'line':frame.lineno,'function':frame.name} for frame in traceback.extract_tb(error.__traceback__)])
        if isinstance(error,Unsafe) and error.details:write(work/'failure-private.json',error.details)
        progress('deployment_stopped',phase=phase,failure=report['failure'],activationStarted=report.get('activationStarted'),requiresRollback=report['requiresRollback'])
    finally:
        if tx:tx.guard.close()
        guard.close()
        for monitor in (guard,tx.guard if tx else guard):
            if monitor.failed.is_set():
                report['failure']=monitor.reason;report['requiresRollback']=bool(report.get('activationStarted')) and not report.get('rollbackCompleted',False)
        if transport:transport.close()
        config.clear();report['lastUpdatedAtUtc']=now();report['apiObservationsForLastPhase']=guard.samples
        if tx and tx.guard is not guard:report['runtimeOrRollbackApiObservations']=tx.guard.samples
        write(work/('api-observations-'+phase+'.json'),{'offlineSamples':guard.samples,'runtimeOrRollbackSamples':tx.guard.samples if tx and tx.guard is not guard else []})
        report['originalArchiveSha256']=digest(BACKUP/'instance.zip');report['originalManifestSha256']=digest(BACKUP/'manifest.json')
        report['original305RestoredFilesUnchanged']={p.relative_to(BACKUP/'restore').as_posix():digest(p) for p in (BACKUP/'restore').rglob('*') if p.is_file()}=={n:a['sha256'] for n,a in baseline['files'].items()}
        if report['originalArchiveSha256']!='255fb82eeddb4b067313e8a6ce39ed012ada204f28d0a7bdb0b85ec2025663bf' or report['originalManifestSha256']!='b54da288c8ad983c6bc35172ed1e0a697812b210dd7afe38ffb7e060f9ff81a1' or not report['original305RestoredFilesUnchanged']:
            report['failure']='HistoricalPreservationFailed'
        write(work/'report.json',report)
    ok='failure' not in report
    progress('deployment_phase_finished',phase=phase,state=report['state'],passed=ok,work=str(work))
    return 0 if ok else 1

if __name__=='__main__':
    try:sys.exit(main(json.load(sys.stdin)))
    except Exception as error:progress('deployment_not_started',failure=str(error) if isinstance(error,Unsafe) else type(error).__name__);sys.exit(1)
