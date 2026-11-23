"""Exécuteur V2.2 dédié : 17 cibles, activation journalisée et rollback complet."""
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
import urllib.request
from minestrator_cold_backup import Api,Guard,Unsafe,now,write,digest,metadata,snapshot,assert_tree_same,read_remote,assert_hash_same,compare_observation,safe_name,progress,protect_blob
from minestrator_final_audit import EXPECTED_HOST,EXPECTED_SERVER,PIN,unprotect
from minestrator_sftp_inventory import pin_matches
from minestrator_v22_preflight import ObservationGuard
from v22_current_local import BACKUP,WORK,files
from v22_current_prepare import check_backup,OP
from map_reader import Reader,nbt
from natural_caverns_rework import unpack
from anvil_patch import region_entries
import server
sys.modules['serverlib']=server
sys.path.insert(0,str(server.ROOT/'deployment'))
from new_match import section
from terrain_reference import verify as verify_terrain
from v22_shaft_restore import packed_height

STAGE='.fk-stage/'+OP
QUARANTINE='.fk-quarantine/'+OP
COMMANDS=('version','plugins','fka status','fka config validate','fka info teams','fka nether portal status','fka help','list','tps','mspt')
load=lambda p:json.loads(p.read_text(encoding='utf-8'))

class ExecutionApi(Api):
    def put(self,suffix,value):
        if not ((suffix=='/poweraction' and value in ({'poweraction':'start'},{'poweraction':'stop'})) or (suffix=='/command' and set(value)=={'command'} and value['command'] in COMMANDS)):
            raise Unsafe('ApiMutationForbidden')
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        request=urllib.request.Request('https://mine.sttr.io/server/'+str(self.server_id)+suffix,data=json.dumps(value).encode(),headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'},method='PUT')
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=20) as response:data=json.load(response)['api']
        if data.get('code')!=200:raise Unsafe('ApiMutationRejected')
        return data.get('data')

def local_gates():
    backup,manifest=check_backup();plan=load(WORK/'plan-private.json')
    if len(plan['files'])!=17 or plan['operation']!=OP or not load(WORK/'simulation-private.json')['passed'] or not load(WORK/'candidate-local/report.json')['passed']:
        raise Unsafe('LocalDeploymentValidationIncomplete')
    if digest(WORK/'simulation-private.json')!=plan['simulationReportSha256']:raise Unsafe('SimulationEvidenceChanged')
    for item in plan['files']:
        if digest(WORK/'payload'/item['path'])!=item['newSha256'] or digest(WORK/'candidate'/item['path'])!=item['newSha256']:raise Unsafe('LocalCandidateChanged')
    if plan['sourceFullHashes']!={n:a['sha256'] for n,a in manifest['files'].items()}:raise Unsafe('BackupPlanMismatch')
    return plan,manifest

def verify_panel(api):
    info=api.info()
    if info!=unprotect(BACKUP/'panel-settings.dpapi'):raise Unsafe('PanelSettingsChanged')
    return info

class Transaction:
    def __init__(self,client,guard,report):self.client=client;self.guard=guard;self.report=report
    def event(self,event,**values):
        with (WORK/'execution-journal-private.jsonl').open('a',encoding='utf-8') as out:out.write(json.dumps({'atUtc':now(),'event':event,**values},ensure_ascii=False)+'\n');out.flush()
        self.report['lastEvent']=event;write(WORK/'execution-report.json',self.report)
    def attr(self,path):
        try:return self.client.lstat(path)
        except FileNotFoundError:return None
    def absent(self,path):
        if self.attr(path) is not None:raise Unsafe('DestinationAlreadyExists',details={'path':path})
    def mkdirs(self,path,mode=0o755):
        if path in ('','.'):return
        if path.startswith('/') or any(p in ('','.','..') for p in PurePosixPath(path).parts):raise Unsafe('UnsafeRemotePath')
        current=''
        for part in PurePosixPath(path).parts:
            current=(current+'/'+part).lstrip('/');self.guard.check();item=self.attr(current)
            if item:
                if not stat.S_ISDIR(item.st_mode):raise Unsafe('RemoteParentNotDirectory')
            else:
                self.event('mkdir_intent',path=current);self.report['remoteWritesPerformed']=True;self.client.mkdir(current,mode);self.guard.check();self.event('mkdir_done',path=current)
    def hash(self,name):
        self.guard.check();return read_remote(self.client,name,metadata(self.client.lstat(name)),self.guard)
    def expect(self,name,h):assert_hash_same(self.hash(name),h,name=name,stage='v22_execution')
    def owner_mode(self,name,mode,uid,gid):
        item=self.client.lstat(name)
        if stat.S_IMODE(item.st_mode)!=stat.S_IMODE(mode):raise Unsafe('InstalledModeMismatch',details={'path':name})
        if item.st_uid is None or item.st_gid is None:raise Unsafe('InstalledOwnershipUnavailable')
        if (item.st_uid,item.st_gid)!=(uid,gid):raise Unsafe('InstalledOwnershipMismatch',details={'path':name})
    def upload(self,local,path,h,mode,uid,gid,mtime=None):
        self.guard.check();self.absent(path);self.mkdirs(str(PurePosixPath(path).parent),0o700 if path.startswith(('.fk-stage/','.fk-quarantine/')) else 0o755)
        if digest(local)!=h:raise Unsafe('LocalPayloadChanged')
        self.event('upload_intent',path=path,sha256=h);self.report['remoteWritesPerformed']=True
        with local.open('rb') as source,self.client.open(path,'wx') as out:
            while data:=source.read(256*1024):self.guard.check();out.write(data);self.guard.check()
            out.flush()
        self.client.chmod(path,stat.S_IMODE(mode))
        if mtime is not None:self.client.utime(path,(mtime,mtime))
        self.owner_mode(path,mode,uid,gid);self.expect(path,h);self.event('upload_verified',path=path,sha256=h)
    def move(self,source,target,h=None):
        self.guard.check();self.absent(target)
        if h:self.expect(source,h)
        self.mkdirs(str(PurePosixPath(target).parent),0o700 if target.startswith(('.fk-stage/','.fk-quarantine/')) else 0o755)
        self.event('rename_intent',source=source,target=target);self.report['remoteWritesPerformed']=True
        self.client.rename(source,target);self.guard.check();self.event('rename_done',source=source,target=target)
        if h:self.expect(target,h)

def verify_hashes(tx,expected,label,baseline=None):
    current=snapshot(tx.client,tx.guard)
    if set(current['files'])!=set(expected):raise Unsafe('RemoteFileSetDivergence',details={'stage':label,'added':sorted(current['files'].keys()-expected.keys()),'missing':sorted(expected.keys()-current['files'].keys())})
    if baseline:assert_tree_same(current,baseline,stage=label+'_metadata')
    anchors={n:a['pathStatBaseline'] for n,a in baseline['files'].items()} if baseline else None
    for i,(name,h) in enumerate(sorted(expected.items()),1):
        actual=read_remote(tx.client,name,current['files'][name],tx.guard,anchors=anchors);assert_hash_same(actual,h,name=name,stage=label)
        if i%25==0:progress(label,files=i,total=len(expected))
    assert_tree_same(snapshot(tx.client,tx.guard),current,stage=label+'_final')
    return current

def install(tx,plan,baseline):
    verify_hashes(tx,plan['sourceFullHashes'],'prewrite_all_source_hashes',baseline)
    tx.absent(STAGE);tx.absent(QUARANTINE)
    # Capturer les propriétaires de tous les répertoires originaux avant écriture.
    directories={}
    for name,attrs in baseline['directories'].items():
        tx.guard.check();item=tx.client.lstat(name)
        if item.st_uid is None or item.st_gid is None:raise Unsafe('DirectoryOwnershipUnavailable')
        directories[name]={'mode':stat.S_IMODE(item.st_mode),'uid':item.st_uid,'gid':item.st_gid}
    write(WORK/'original-directory-owners-private.json',directories)
    owners={(f['expectedUid'],f['expectedGid']) for f in plan['files']}
    if any((a['uid'],a['gid']) not in owners for a in directories.values()):raise Unsafe('DirectoryOwnershipNotRestorable')
    tx.mkdirs(STAGE,0o700);tx.mkdirs(QUARANTINE,0o700)
    for i,f in enumerate(plan['files'],1):
        tx.upload(WORK/'payload'/f['path'],STAGE+'/payload/'+f['path'],f['newSha256'],f['expectedMode'],f['expectedUid'],f['expectedGid'])
        tx.report['stagedFiles']=i;progress('v22_staging',files=i,total=17)
    for f in plan['files']:tx.expect(STAGE+'/payload/'+f['path'],f['newSha256'])
    # Les namespaces techniques créés sont exclus de cette seconde comparaison complète de l'état actif.
    for i,(name,h) in enumerate(sorted(plan['sourceFullHashes'].items()),1):
        compare_observation(metadata(tx.client.lstat(name)),baseline['files'][name]['pathStatBaseline'],name=name,stage='before_activation_original_metadata',same_source=True)
        tx.expect(name,h)
        if i%25==0:progress('before_activation_source_hashes',files=i,total=len(plan['sourceFullHashes']))
    expected_staged=set(plan['sourceFullHashes'])|{STAGE+'/payload/'+f['path'] for f in plan['files']}
    if set(snapshot(tx.client,tx.guard)['files'])!=expected_staged:raise Unsafe('FileSetChangedBeforeActivation')
    tx.guard.poll();tx.report['activationStarted']=True;tx.event('activation_boundary_before_first_active_rename')
    for name in plan['quarantineActiveRecords']:tx.move(name,QUARANTINE+'/files/'+name,plan['sourceFullHashes'][name])
    for f in sorted(plan['files'],key=lambda f:(f['path']=='DEPLOYMENT_MANIFEST.json',f['path'])):
        name=f['path']
        if f['action']=='replace':tx.move(name,QUARANTINE+'/files/'+name,f['oldSha256'])
        tx.move(STAGE+'/payload/'+name,name,f['newSha256'])
        tx.owner_mode(name,f['expectedMode'],f['expectedUid'],f['expectedGid'])
        tx.report['installedFiles']=tx.report.get('installedFiles',0)+1
    expected=dict(plan['candidateFullHashes'])
    for name in set(plan['sourceFullHashes'])&{f['path'] for f in plan['files']}|set(plan['quarantineActiveRecords']):expected[QUARANTINE+'/files/'+name]=plan['sourceFullHashes'][name]
    verify_hashes(tx,expected,'installed_and_preserved_all_hashes')
    changed={f['path'] for f in plan['files']}|set(plan['quarantineActiveRecords'])
    for name in plan['sourceFullHashes'].keys()-changed:
        compare_observation(metadata(tx.client.lstat(name)),baseline['files'][name]['pathStatBaseline'],name=name,stage='preserved_original_metadata_after_install',same_source=True)
    tx.report.update({'installationOfflineVerified':True,'installedFiles':17,'quarantinedFiles':13,'verifiedFullFilesAfterInstall':len(expected),'whitelistUnchanged':True,'restartOnCrash':False})
    tx.event('installed_offline_verified')

def read_bytes(client,name,limit=16*1024**2):
    item=client.lstat(name)
    if not stat.S_ISREG(item.st_mode) or item.st_size>limit:raise Unsafe('RuntimeReadLimit')
    with client.open(name,'rb') as source:data=source.read(limit+1)
    if len(data)>limit:raise Unsafe('RuntimeReadLimit')
    return data

class RemoteReader(Reader):
    def __init__(self,client,guard):self.client=client;self.guard=guard;self.chunks={}
    def chunk(self,cx,cz):
        self.guard.check()
        if (cx,cz) in self.chunks:return self.chunks[cx,cz]
        name=f'world/dimensions/minecraft/overworld/region/r.{cx//32}.{cz//32}.mca';a=self.client.lstat(name)
        with self.client.open(name,'rb') as stream:
            stream.seek((cx%32+cz%32*32)*4);head=stream.read(4);offset=int.from_bytes(head[:3],'big')
            if not offset:raise Unsafe('RuntimeChunkMissing')
            stream.seek(offset*4096);size=int.from_bytes(stream.read(4),'big');codec=stream.read(1)[0];data=stream.read(size-1)
        b=self.client.lstat(name)
        if (a.st_size,a.st_mtime)!=(b.st_size,b.st_mtime):raise Unsafe('RuntimeRegionChangedDuringRead')
        result=nbt(unpack((codec,data)));self.chunks[cx,cz]=result;return result

def query_udp():
    tag=b'V22F'
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.settimeout(5);sock.sendto(b'\xfe\xfd\x09'+tag,('91.197.6.72',22880));data,_=sock.recvfrom(65535)
        if data[:5]!=b'\x09'+tag:raise Unsafe('QueryChallengeInvalid')
        challenge=int(data[5:].rstrip(b'\0'));sock.sendto(b'\xfe\xfd\x00'+tag+struct.pack('>i',challenge)+b'\0'*4,('91.197.6.72',22880));data,_=sock.recvfrom(65535)
        if data[:5]!=b'\x00'+tag or b'maxplayers\x0020\x00' not in data:raise Unsafe('QueryCapacityInvalid')
    return {'udpQueryResponded':True,'capacity':20}

def varint(v):
    result=b'';v&=0xffffffff
    while True:
        b=v&127;v>>=7;result+=bytes([b|(128 if v else 0)])
        if not v:return result

def fresh_boot_section(text,previous_header):
    headers=[line for line in text.splitlines() if 'Running Java' in line]
    if not headers or headers[-1]==previous_header:return ''
    return text[text.rfind(headers[-1]):]

def tcp_status():
    def readint(s):
        value=0
        for i in range(5):
            b=s.recv(1)
            if not b:raise Unsafe('TcpStatusTruncated')
            value|=(b[0]&127)<<(7*i)
            if not b[0]&128:return value
        raise Unsafe('TcpVarintInvalid')
    def exact(s,n):
        result=b''
        while len(result)<n:
            data=s.recv(n-len(result))
            if not data:raise Unsafe('TcpStatusTruncated')
            result+=data
        return result
    with socket.create_connection(('91.197.6.72',22880),timeout=6) as sock:
        host=b'91.197.6.72';hello=b'\0'+varint(-1)+varint(len(host))+host+struct.pack('>H',22880)+b'\x01';sock.sendall(varint(len(hello))+hello+b'\x01\x00')
        length=readint(sock)
        if not 0<length<=1024**2 or readint(sock)!=0:raise Unsafe('TcpStatusInvalid')
        value=json.loads(exact(sock,readint(sock)))
    if value.get('players',{}).get('max')!=20 or '26.3' not in value.get('version',{}).get('name',''):raise Unsafe('TcpStatusVersionCapacityMismatch')
    return {'tcpStatusResponded':True,'version':value['version'],'capacity':20,'onlinePlayers':value['players']['online'],'realPlayerLoginPerformed':False}

def runtime_world(tx):
    ref=load(WORK/'candidate/maintenance/new-match-reference-v2.2.json');reader=RemoteReader(tx.client,tx.guard)
    local_reader=Reader(WORK/'candidate')
    text=read_bytes(tx.client,'plugins/FKAmis/state.yml').decode('utf-8-sig')
    if section(text,('day',))!='0' or section(text,('started',))!='false' or section(text,('roster',)) not in (None,'{}') or section(text,('objectives',)) not in (None,'{}'):raise Unsafe('GameNotInitialAfterStart')
    for base in ref['bases']:
        team=base['team']
        if section(text,('native','TeamManager',team,'Base','Radius'))!='40' or section(text,('native','TeamManager',team,'Members'))!='[]':raise Unsafe('RuntimeTerritoriesChanged')
        for k,v in base['center'].items():
            if section(text,('native','TeamManager',team,'Base','Center',k))!=str(v):raise Unsafe('RuntimeBaseCenterChanged')
        for k,v in base['spawn'].items():
            if abs(float(section(text,('spawns',team,k)))-float(v))>1e-6:raise Unsafe('RuntimeSpawnChanged')
        import math
        x,y,z=(math.floor(base['spawn'][k]) for k in ('x','y','z'))
        for dy in (-1,0,1):
            if reader.block(x,y+dy,z)!=local_reader.block(x,y+dy,z):raise Unsafe('RuntimeSpawnBlocksChanged')
    natural=verify_terrain(WORK/'candidate',ref,reader)
    shaft=ref['underground']['archiveRestorations']['cells'];x,_,z=shaft[0]['at'];column=x%16+z%16*16
    maps=reader.chunk(x//16,z//16)['Heightmaps'];local_maps=local_reader.chunk(x//16,z//16)['Heightmaps']
    for key in ('MOTION_BLOCKING','MOTION_BLOCKING_NO_LEAVES','WORLD_SURFACE','OCEAN_FLOOR'):
        if packed_height(maps[key],column)!=packed_height(local_maps[key],column):raise Unsafe('RuntimeShaftHeightmapChanged')
    for m in ref['monuments']:
        observed=[[dx,dy,dz,reader.block(m['x']+dx,m['y']+dy,m['z']+dz)] for dx,dy,dz in m['checkPoints']]
        if hashlib.sha256(json.dumps(observed,separators=(',',':')).encode()).hexdigest()!=m['blockTypesSha256']:raise Unsafe('RuntimeMonumentChanged')
        for loot in m['loot']:
            x,y,z=loot['at'];tile=next((t for t in reader.chunk(x//16,z//16).get('block_entities',[]) if (t.get('x'),t.get('y'),t.get('z'))==(x,y,z)),{})
            items=tile.get('Items',tile.get('items',[]));h=hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':'),default=lambda b:b.hex()).encode()).hexdigest()
            if h!=loot['inventorySha256']:raise Unsafe('RuntimeMonumentLootChanged')
    for s in ref['supplies']:
        if reader.block(*s['at'])!='minecraft:chest':raise Unsafe('RuntimeSupplyMissing')
    return {'day':0,'gameStarted':False,'territoriesVerified':4,'spawnsVerified':4,'monumentsVerified':7,'monumentLootChestsVerified':sum(len(m['loot']) for m in ref['monuments']),'supplySitesVerified':8,'shaftHeightmapFieldsVerified':4,'chunksRead':len(reader.chunks),'humanInspectionPerformed':False,**natural}

def startup(tx,api,plan):
    if not tx.report.get('installationOfflineVerified') or tx.report.get('startRequested'):raise Unsafe('SingleStartPreconditionFailed')
    for f in plan['files']:tx.expect(f['path'],f['newSha256'])
    for n in ('whitelist.json','ops.json','paper.jar','server.jar','plugins/FallenKingdom-2.24.9.jar','spigot.yml','server.properties'):tx.expect(n,plan['sourceFullHashes'][n])
    old_log=read_bytes(tx.client,'logs/latest.log').decode('utf-8',errors='replace')
    old_headers=[line for line in old_log.splitlines() if 'Running Java' in line];previous_header=old_headers[-1] if old_headers else ''
    tx.guard.poll();verify_panel(api);tx.guard.close();tx.report['startRequested']=True;tx.event('single_start_intent')
    api.put('/poweraction',{'poweraction':'start'});deadline=time.monotonic()+240;seen=False;samples=[];log=''
    while time.monotonic()<deadline:
        live=api.get('/live');state=live.get('state');samples.append({'atUtc':now(),'state':state,'statsState':(live.get('stats') or {}).get('state')})
        if state=='online':seen=True
        elif seen:raise Unsafe('UnexpectedStopAfterStart')
        log=re.sub(r'\x1b\[[0-9;]*m','',read_bytes(tx.client,'logs/latest.log').decode('utf-8',errors='replace'))
        (WORK/'startup-private.log').write_text(log,encoding='utf-8');write(WORK/'startup-api-private.json',samples)
        if re.search(r'\b(ERROR|SEVERE)\b',log):raise Unsafe('CriticalStartupLogError')
        fresh=fresh_boot_section(log,previous_header)
        if state=='online' and (live.get('stats') or {}).get('state')=='online' and 'Done (' in fresh and 'FKAmis prêt' in fresh:break
        time.sleep(3)
    else:raise Unsafe('StartupTimeout')
    online=ObservationGuard(api);online.initial='online';online.abort=lambda:tx.client.get_channel().close();tx.guard=online;online.start()
    for cmd in COMMANDS:tx.guard.check();api.put('/command',{'command':cmd});tx.event('readonly_command_sent',command=cmd);time.sleep(.5)
    time.sleep(2);log=re.sub(r'\x1b\[[0-9;]*m','',read_bytes(tx.client,'logs/latest.log').decode('utf-8',errors='replace'));(WORK/'startup-private.log').write_text(log,encoding='utf-8')
    if re.search(r'\b(ERROR|SEVERE)\b',log):raise Unsafe('CriticalRuntimeLogError')
    for marker in ('26.3-244','Configuration cohérente','Jour 0','Query running on','FKAmis prêt'):
        if marker not in log:raise Unsafe('StartupEvidenceMissing',details={'marker':marker})
    tx.report['world']=runtime_world(tx);tx.report['query']=query_udp();tx.report['tcp']=tcp_status()
    live=api.get('/live');(WORK/'live-after-start.dpapi').write_bytes(protect_blob(json.dumps(live).encode()))
    for n in ('whitelist.json','ops.json','paper.jar','plugins/FallenKingdom-2.24.9.jar','plugins/FKAmis-1.0.0.jar','FKAmis.sha256','RUNTIME_LOCK.json'):
        expected=next((f['newSha256'] for f in plan['files'] if f['path']==n),plan['sourceFullHashes'][n]);tx.expect(n,expected)
    props=server.properties(WORK/'candidate/server.properties')
    actual={}
    for line in read_bytes(tx.client,'server.properties').decode('utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):k,v=line.split('=',1);actual[k]=v
    if actual!=props:raise Unsafe('EffectivePropertiesChanged')
    if not re.search(r'(?m)^\s*restart-on-crash:\s*false\s*$',read_bytes(tx.client,'spigot.yml').decode('utf-8')):raise Unsafe('CrashRestartEnabled')
    tx.report.update({'startupPassed':True,'startupErrors':0,'startupWarnings':len(re.findall(r'\bWARN\b',log)),'state':'RUNNING_RECIPE_ONLY','restartOnCrash':False,'whitelistUnchanged':True,'officialGameStartSent':False,'visualClientInspectionPerformed':False})
    tx.event('v22_running_recipe_only')

def rollback(tx,api,plan,manifest):
    if not tx.report.get('activationStarted') or not tx.report.get('failure'):raise Unsafe('RollbackScopeNotSatisfied')
    tx.guard.close();state=api.get('/live').get('state')
    if state!='offline':tx.event('rollback_stop_intent');api.put('/poweraction',{'poweraction':'stop'})
    end=time.monotonic()+150
    while time.monotonic()<end:
        try:api.offline();break
        except Unsafe:time.sleep(3)
    else:raise Unsafe('RollbackOfflineNotConfirmed')
    tx.guard=Guard(api);tx.guard.abort=lambda:tx.client.get_channel().close();tx.guard.start();verify_panel(api);check_backup()
    historical={n:h for n,h in plan['sourceFullHashes'].items() if n.split('/')[0] in ('.fk-stage','.fk-quarantine')}
    for n,h in historical.items():tx.expect(n,h)
    restore_stage=STAGE+'/rollback-full';failed=QUARANTINE+'/failed-active';tx.absent(restore_stage);tx.absent(failed);tx.mkdirs(restore_stage,0o700)
    active={n:h for n,h in plan['sourceFullHashes'].items() if n not in historical}
    for i,(name,h) in enumerate(sorted(active.items()),1):
        a=manifest['files'][name];owner=a['pathStatBaseline'];tx.upload(BACKUP/'restore'/name,restore_stage+'/'+name,h,a['mode'],owner['uid'],owner['gid'],a['mtime'])
        if i%25==0:progress('rollback_staging',files=i,total=len(active))
    # Préserver toute la tentative active avant promotion cohérente du rollback.
    tx.mkdirs(failed,0o700)
    for item in tx.client.listdir_attr('.'):
        safe_name(item.filename)
        if item.filename in ('.fk-stage','.fk-quarantine'):continue
        if not (stat.S_ISDIR(item.st_mode) or stat.S_ISREG(item.st_mode)):raise Unsafe('UnsafeRollbackRoot')
        tx.move(item.filename,failed+'/'+item.filename)
    for item in tx.client.listdir_attr(restore_stage):safe_name(item.filename);tx.move(restore_stage+'/'+item.filename,item.filename)
    for name,attrs in manifest['directories'].items():
        if name.split('/')[0] in ('.fk-stage','.fk-quarantine'):continue
        tx.mkdirs(name,stat.S_IMODE(attrs['mode']));tx.client.chmod(name,stat.S_IMODE(attrs['mode']))
    for name,h in plan['sourceFullHashes'].items():tx.expect(name,h)
    tx.report.update({'rollbackCompleted':True,'rollbackFilesVerified':len(plan['sourceFullHashes']),'serverLeftOffline':True,'state':'ROLLED_BACK_OFFLINE'})
    tx.event('full_current_rollback_verified')

def postcheck(tx,plan):
    if not tx.report.get('startupPassed'):raise Unsafe('PostcheckRequiresSuccessfulStart')
    tree=snapshot(tx.client,tx.guard);write(WORK/'post-start-inventory-private.json',tree)
    checked=[];static_checked=0
    for item in plan['files']:
        if not item['path'].endswith('.mca'):tx.expect(item['path'],item['newSha256']);static_checked+=1
    for name,h in plan['sourceFullHashes'].items():
        if name.startswith('world/players/') or name in ('plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml'):
            tx.expect(name,h);checked.append(name)
        if name.startswith(('.fk-quarantine/','.fk-stage/')):
            compare_observation(metadata(tx.client.lstat(name)),load(BACKUP/'manifest.json')['files'][name]['pathStatBaseline'],name=name,stage='historical_post_start_metadata',same_source=True)
    old_count=sum(n.startswith('.fk-quarantine/MS-DEPLOY-V21-20261120-01/') for n in tree['files'])
    new_count=sum(n.startswith(QUARANTINE+'/files/') for n in tree['files'])
    stage_count=sum(n.startswith(STAGE+'/') for n in tree['files'])
    if (old_count,new_count,stage_count)!=(152,13,0):raise Unsafe('PostStartTechnicalNamespaceDivergence')
    config=read_bytes(tx.client,'plugins/FKAmis/config.yml').decode('utf-8-sig')
    if float(section(config,('players-per-team',)))!=4 or float(section(config,('capture-seconds',)))!=60 or float(section(config,('capture-radius',)))!=2.5:raise Unsafe('RuntimeGameplayConfigurationChanged')
    tx.report['postStartPreservation']={'staticTargetsShaVerified':static_checked,'playerFilesAndRoleSupplyFilesShaVerified':len(checked),'playerFilesShaVerified':sum(n.startswith('world/players/') for n in checked),
        'oldQuarantineFilesMetadataVerified':old_count,'newQuarantineFiles':new_count,'stagingFilesRemaining':stage_count,
        'runtimeTotalFiles':len(tree['files']),'runtimeActiveFiles':sum(n.split('/')[0] not in ('.fk-stage','.fk-quarantine') for n in tree['files']),
        'playersPerTeam':4,'captureSeconds':60,'captureRadius':2.5}
    tx.event('post_start_data_preservation_verified')

def run(config):
    import paramiko
    if int(config['serverId'])!=EXPECTED_SERVER or config['host']!=EXPECTED_HOST or int(config['port'])!=2022 or config['fingerprint']!=PIN:raise Unsafe('IdentityMismatch')
    phase=config['phase'];plan,manifest=local_gates();report_path=WORK/'execution-report.json'
    if phase=='install':
        if report_path.exists():raise Unsafe('ExecutionEvidenceAlreadyExists')
        report={'operation':OP,'state':'PREPARED','startedAtUtc':now(),'remoteWritesPerformed':False,'activationStarted':False,'startRequested':False,'ownerApproved':True}
    else:report=load(report_path)
    api=ExecutionApi(config.pop('apiKey'),EXPECTED_SERVER);guard=ObservationGuard(api) if phase=='postcheck' else Guard(api)
    if phase=='postcheck':guard.initial='online'
    transport=None;tx=None
    try:
        verify_panel(api)
        if phase!='rollback':guard.start()
        transport=paramiko.Transport(socket.create_connection((config['host'],2022),timeout=15));guard.abort=transport.close;transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),PIN):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        with paramiko.SFTPClient.from_transport(transport) as client:
            client.get_channel().settimeout(30);tx=Transaction(client,guard,report)
            if phase=='install':install(tx,plan,manifest)
            elif phase=='start':startup(tx,api,plan)
            elif phase=='rollback':rollback(tx,api,plan,manifest)
            elif phase=='postcheck':postcheck(tx,plan)
            else:raise Unsafe('UnknownPhase')
    except Exception as error:
        report['failure']=str(error) if isinstance(error,Unsafe) else type(error).__name__;report['failedPhase']=phase
        report['requiresRollback']=bool(report.get('activationStarted')) and not report.get('rollbackCompleted',False)
        if isinstance(error,Unsafe) and error.details:write(WORK/('failure-'+phase+'-private.json'),error.details)
        progress('v22_execution_interrupted',phase=phase,failure=report['failure'],activationStarted=report.get('activationStarted'),requiresRollback=report['requiresRollback'])
    finally:
        guard.close()
        if tx:
            tx.guard.close();write(WORK/('api-observations-'+phase+'-private.json'),{'offline':guard.samples,'runtimeOrRollback':tx.guard.samples if tx.guard is not guard else []})
            if tx.guard.failed.is_set():report['failure']=tx.guard.reason;report['requiresRollback']=bool(report.get('activationStarted'))
        if transport:transport.close()
        report['updatedAtUtc']=now();write(report_path,report);config.clear();api.token=None
    ok=report.get('rollbackCompleted') if phase=='rollback' else 'failure' not in report
    progress('v22_phase_finished',phase=phase,passed=bool(ok),state=report['state']);return 0 if ok else 1

if __name__=='__main__':
    try:sys.exit(run(json.load(sys.stdin)))
    except Exception as error:progress('v22_phase_not_started',failure=str(error) if isinstance(error,Unsafe) else type(error).__name__);sys.exit(1)
