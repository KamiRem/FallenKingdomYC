"""Préflight V2.2 : GET, READDIR/LSTAT/FSTAT/READ et statvfs exclusivement."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path
import socket
import stat
from minestrator_cold_backup import Api,Guard,Unsafe,now,write,digest,protect_directory,protect_blob,metadata,compare_observation,read_remote,safe_name,progress
from minestrator_final_audit import EXPECTED_SERVER,EXPECTED_HOST,PIN,disk_stats,unprotect
from minestrator_sftp_inventory import pin_matches
import server

TEXT_FILES=('server.properties','spigot.yml','config/paper-global.yml','RUNTIME_LOCK.json','DEPLOYMENT_MANIFEST.json','FKAmis.sha256',
    'plugins/FKAmis/config.yml','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml',
    'plugins/FallenKingdom/locales/messages_fr.properties','whitelist.json','ops.json','map-v2-construction.json','map-v21-plan.json','start.sh','start.ps1')

class ReadOnlySftp:
    def __init__(self,client):self.client=client
    def listdir_attr(self,path):return self.client.listdir_attr(path)
    def lstat(self,path):return self.client.lstat(path)
    def open(self,path,mode='rb'):
        if mode!='rb':raise Unsafe('RemoteWriteForbidden')
        return self.client.open(path,'rb')
    def get_channel(self):return self.client.get_channel()
    def _request(self,kind,*args):
        from paramiko.sftp import CMD_EXTENDED
        if kind!=CMD_EXTENDED or args!=('statvfs@openssh.com','.'):raise Unsafe('RemoteExtensionForbidden')
        return self.client._request(kind,*args)

class ObservationGuard(Guard):
    def __init__(self,api):super().__init__(api);self.initial=None
    def poll(self):
        import time
        with self.lock:
            try:
                data=self.api.get('/live');state=data.get('state');nested=data.get('stats',{}).get('state')
                if state not in ('online','offline') or nested!=state:raise Unsafe('UnstableServerState')
                if self.initial is None:self.initial=state
                if state!=self.initial:raise Unsafe('ServerStateChanged')
                self.samples.append({'atUtc':now(),'state':state,'statsState':nested});self.last=time.monotonic()
            except Exception as error:
                self.reason=str(error) if isinstance(error,Unsafe) else 'ApiObservationFailed';self.failed.set();self.abort();raise Unsafe(self.reason) from None

def active_snapshot(client,guard):
    found={};folders=[];technical=[];stack=[''];seen=set()
    while stack:
        guard.check();folder=stack.pop()
        for item in client.listdir_attr(folder or '.'):
            name=safe_name(item.filename);path=(folder+'/'+name).lstrip('/');attrs=metadata(item)
            compare_observation(attrs,attrs,name=path,stage='listdir_availability')
            if path.casefold() in seen:raise Unsafe('PathCollision')
            seen.add(path.casefold())
            if len(seen)>100000:raise Unsafe('InventoryLimitExceeded')
            if stat.S_ISDIR(item.st_mode):
                if not folder and name in ('.fk-stage','.fk-quarantine'):technical.append(path);continue
                folders.append(path);stack.append(path)
            elif stat.S_ISREG(item.st_mode):found[path]=attrs
            else:raise Unsafe('LinkOrSpecialFile')
    return {'files':found,'directories':folders,'technicalNamespacesNotTraversed':technical}

def checked_read(client,path,entry,guard,target=None,evidence=None):
    a=read_remote(client,path,entry,guard,evidence=evidence,destination=target)
    b=read_remote(client,path,entry,guard,evidence=evidence)
    if a!=b:raise Unsafe('ConcurrentContentChange',details={'path':path})
    return a

def technical_metadata(client,guard,namespaces):
    summaries=[]
    for namespace in namespaces:
        operations=[]
        for top in client.listdir_attr(namespace):
            safe_name(top.filename)
            if not stat.S_ISDIR(top.st_mode):raise Unsafe('UnsafeTechnicalNamespace')
            total=0;count=0;stack=[namespace+'/'+top.filename]
            while stack:
                guard.check();folder=stack.pop()
                for item in client.listdir_attr(folder):
                    safe_name(item.filename);path=folder+'/'+item.filename
                    if stat.S_ISDIR(item.st_mode):stack.append(path)
                    elif stat.S_ISREG(item.st_mode):count+=1;total+=item.st_size
                    else:raise Unsafe('LinkOrSpecialFile')
                    if count>100000:raise Unsafe('InventoryLimitExceeded')
            operations.append({'operation':top.filename,'files':count,'bytes':total,'directoryMtime':top.st_mtime})
        summaries.append({'namespace':namespace,'operations':operations,'contentsRead':False})
    return summaries

def hosting_fields(data,path=''):
    found=[]
    if not isinstance(data,dict):return found
    for key,value in data.items():
        if key in ('history','poweraction_message','websocket','sftp'):continue
        at=path+'/'+key
        if any(word in key.lower() for word in ('restart','crash','watchdog','schedule','planning','calendar','pending')):found.append(at)
        if isinstance(value,dict):found.extend(hosting_fields(value,at))
    return found

def run(config):
    import paramiko
    if int(config['serverId'])!=EXPECTED_SERVER or config['host']!=EXPECTED_HOST or int(config['port'])!=2022 or config['fingerprint']!=PIN:raise Unsafe('ConnectionIdentityMismatch')
    out=Path(config['output']).resolve();phase=config['phase'];parent=(Path.home()/'FKBackups').resolve()
    if out==parent or not out.is_relative_to(parent):raise Unsafe('UnsafeLocalDestination')
    if phase=='discover':protect_directory(out)
    elif not (out/'discover-private.json').is_file():raise Unsafe('DiscoveryRequired')
    elif not json.loads((out/'discover-private.json').read_text(encoding='utf-8')).get('passed'):raise Unsafe('SuccessfulDiscoveryRequired')
    if phase=='regions':
        prior=out/'fingerprint-private.json'
        if not prior.is_file() or not json.loads(prior.read_text(encoding='utf-8')).get('passed'):raise Unsafe('SuccessfulFingerprintRequired')
    target=out/(phase+'-private.json')
    if target.exists():raise Unsafe('EvidenceExists')
    report={'phase':phase,'startedAtUtc':now(),'passed':False,'serverId':EXPECTED_SERVER,'remoteWritesPerformed':False,'remotePowerOrConsoleCommands':False,'backupCreated':False}
    api=Api(config.pop('apiKey'),EXPECTED_SERVER);guard=ObservationGuard(api);transport=None
    trace=(out/(phase+'-attributes-private.jsonl')).open('x',encoding='utf-8')
    def evidence(value):trace.write(json.dumps(value,ensure_ascii=False)+'\n');trace.flush()
    try:
        data=api.get('');srv=data['server']
        if int(srv['id'])!=EXPECTED_SERVER or int(srv['port'])!=22880 or str(srv['ip']).split(':')[0]!='91.197.6.72':raise Unsafe('ServerIdentityMismatch')
        live=api.get('/live');(out/(phase+'-panel.dpapi')).write_bytes(protect_blob(json.dumps({'info':data,'live':live}).encode()))
        report['authenticatedIdentityVerified']=True;report['apiGameState']=live.get('state');report['apiGameVersion']=live.get('stats',{}).get('version')
        report['apiPlayers']={k:live.get('stats',{}).get('players',{}).get(k) for k in ('current','limit')}
        report['diskApi']=live.get('stats',{}).get('disk');report['hostingRestartSchedulingKeysExposed']=hosting_fields(data)
        settings=data.get('settings') or {};report['javaSettingId']=settings.get('id_java_version');report['javaImage']=settings.get('image');report['startupFile']=settings.get('startup_file')
        guard.start();progress('authenticated_readonly_identity',serverId=EXPECTED_SERVER,state=guard.initial)
        if phase!='discover' and guard.initial!='offline':raise Unsafe('ColdComparisonRequiresOffline')
        if phase=='checkpoint':
            guard.poll();report['passed']=True;progress('readonly_final_api_checkpoint',state=guard.initial);return 0
        transport=paramiko.Transport(socket.create_connection((config['host'],int(config['port'])),timeout=15));guard.abort=transport.close;transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),PIN):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        with paramiko.SFTPClient.from_transport(transport) as raw:
            raw.get_channel().settimeout(20);client=ReadOnlySftp(raw);tree=active_snapshot(client,guard)
            write(out/(phase+'-inventory-private.json'),tree);report['activeFiles']=len(tree['files']);report['activeBytes']=sum(a['size'] for a in tree['files'].values());report['technicalNamespacesNotTraversed']=tree['technicalNamespacesNotTraversed'];report['diskSftp']=disk_stats(client)
            if phase=='discover':
                readback=out/'readback';readback.mkdir();hashes={}
                names=list(TEXT_FILES)+['paper.jar','server.jar']+[n for n in tree['files'] if n.startswith('plugins/') and n.count('/')==1 and n.endswith('.jar')]
                if guard.initial=='offline':names.append('logs/latest.log')
                for name in names:
                    if name not in tree['files']:continue
                    if name in TEXT_FILES or name=='logs/latest.log':
                        if tree['files'][name]['size']>12*1024**2:raise Unsafe('AuditReadLimit')
                        local=readback/name;local.parent.mkdir(parents=True,exist_ok=True)
                    else:local=None
                    hashes[name]=checked_read(client,name,tree['files'][name],guard,local,evidence)
                report['doubleReadHashes']=hashes
            else:
                baseline=json.loads((out/'discover-inventory-private.json').read_text(encoding='utf-8'))
                if tree['files'].keys()!=baseline['files'].keys():raise Unsafe('TreeChangedSinceDiscovery')
                names=sorted(tree['files']) if phase=='fingerprint' else ['world/dimensions/minecraft/overworld/region/r.-1.-1.mca','world/dimensions/minecraft/overworld/region/r.-1.0.mca','world/dimensions/minecraft/overworld/region/r.0.-1.mca','world/dimensions/minecraft/overworld/region/r.0.0.mca']
                hashes={}
                for index,name in enumerate(names):
                    compare_observation(tree['files'][name],baseline['files'][name],name=name,stage='since_discovery',same_source=True,evidence=evidence)
                    local=None
                    if phase=='regions':local=out/'region-readback'/name;local.parent.mkdir(parents=True,exist_ok=True)
                    hashes[name]=checked_read(client,name,tree['files'][name],guard,local,evidence)
                    if index%25==0:progress('readonly_hash_progress',phase=phase,files=index+1,total=len(names))
                report['doubleReadHashes']=hashes
                after=active_snapshot(client,guard)
                if after['files'].keys()!=tree['files'].keys():raise Unsafe('ConcurrentTreeChange')
                for n,a in tree['files'].items():compare_observation(after['files'][n],a,name=n,stage='after_read',same_source=True,evidence=evidence)
                if phase=='regions':report['technicalNamespaceMetadata']=technical_metadata(client,guard,tree['technicalNamespacesNotTraversed'])
            guard.poll();report['passed']=True
    except Exception as error:
        report['failure']=str(error) if isinstance(error,Unsafe) else type(error).__name__
        if isinstance(error,Unsafe) and error.details:write(out/(phase+'-failure-details-private.json'),error.details)
    finally:
        guard.close()
        if guard.failed.is_set():report['passed']=False;report['failure']=guard.reason
        if transport:transport.close()
        config.clear();trace.close();report['apiObservations']=guard.samples;report['finishedAtUtc']=now();write(target,report)
    progress('readonly_audit_finished',phase=phase,passed=report['passed'],state=report.get('apiGameState'),activeFiles=report.get('activeFiles'),failure=report.get('failure'))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    try:sys.exit(run(json.load(sys.stdin)))
    except Exception as error:progress('readonly_audit_not_started',failure=str(error) if isinstance(error,Unsafe) else type(error).__name__);sys.exit(1)
