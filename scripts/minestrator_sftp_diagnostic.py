"""Diagnostic borné de trois petits fichiers, aucune sauvegarde ni écriture SFTP."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
import socket
import stat
from pathlib import Path
from minestrator_cold_backup import Api,Guard,assert_same,metadata,Unsafe,now,safe_name
from minestrator_sftp_inventory import pin_matches
from sftp_attributes import capture

# Reproduction figée du comparateur du 19 novembre, indépendante du correctif.
def legacy_metadata(item):return {'size':item.st_size,'mtime':item.st_mtime,'mode':stat.S_IMODE(item.st_mode),'uid':getattr(item,'st_uid',None),'gid':getattr(item,'st_gid',None)}
def legacy_assert(item,expected):
    if not stat.S_ISREG(item.st_mode) or legacy_metadata(item)!=expected:raise Unsafe('ConcurrentFileChange')

def run(config):
    import paramiko
    api=Api(config.pop('apiKey'),config['serverId']);guard=Guard(api);transport=None
    result={'startedAtUtc':now(),'scope':'root-list-and-three-small-files','backupPerformed':False,'remoteWritesPerformed':False,'files':[]}
    output=Path(config['output'])
    if output.exists():raise Unsafe('OutputExists')
    try:
        api.info();guard.start()
        transport=paramiko.Transport(socket.create_connection((config['host'],int(config['port'])),timeout=15));guard.abort=transport.close;transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),config['fingerprint']):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        with paramiko.SFTPClient.from_transport(transport) as client:
            client.get_channel().settimeout(10)
            listing=client.listdir_attr('.')
            first=next(x for x in listing if stat.S_ISREG(x.st_mode))
            result['currentFirstFileInOriginalTraversal']=first.filename
            for name in dict.fromkeys([first.filename,'FKAmis.sha256','server.properties']):
                safe_name(name);guard.check();item=next(x for x in listing if x.filename==name)
                entry={'path':name,'listdir':capture(item),'rounds':[]}
                for index in range(2):
                    path_stat=client.lstat(name)
                    round={'lstatBefore':capture(path_stat),'legacyResults':{},'correctedResults':{},'contentRead':False}
                    for stage,value in [('lstat_before',path_stat)]:
                        try:legacy_assert(value,legacy_metadata(item));round['legacyResults'][stage]='pass'
                        except Unsafe as error:round['legacyResults'][stage]=str(error)
                        round['correctedResults'][stage]=assert_same(value,metadata(item),name=name,stage=stage)
                    with client.open(name,'rb') as handle:
                        before=handle.stat();round['fstatBefore']=capture(before)
                        try:legacy_assert(before,legacy_metadata(item));round['legacyResults']['fstat_before']='pass'
                        except Unsafe as error:round['legacyResults']['fstat_before']=str(error)
                        round['correctedResults']['fstat_before']=assert_same(before,metadata(path_stat),name=name,stage='fstat_before')
                        if item.st_size is not None and 0<=item.st_size<=16384:
                            data=handle.read(16385)
                            if len(data)!=item.st_size:raise Unsafe('DiagnosticContentSizeChanged')
                            round['sha256']=hashlib.sha256(data).hexdigest();round['contentRead']=True
                        end_stat=handle.stat();round['fstatAfter']=capture(end_stat)
                        round['correctedResults']['fstat_after']=assert_same(end_stat,metadata(before),name=name,stage='fstat_after',same_source=True)
                    end_path=client.lstat(name);round['lstatAfter']=capture(end_path)
                    round['correctedResults']['lstat_after']=assert_same(end_path,metadata(path_stat),name=name,stage='lstat_after',same_source=True)
                    entry['rounds'].append(round)
                if all(r['contentRead'] for r in entry['rounds']):
                    if entry['rounds'][0]['sha256']!=entry['rounds'][1]['sha256']:raise Unsafe('DiagnosticContentChanged')
                    entry['contentVerification']='two_reads_equal'
                else:entry['contentVerification']='not_verified_size_limit'
                result['files'].append(entry)
            guard.poll();guard.close();guard.check()
        result.update({'finishedAtUtc':now(),'passed':True,'apiObservations':guard.samples,'authenticated':True,'hostKeyVerified':True})
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        # Valeurs et chemins restent dans le rapport privé.
        print(json.dumps({'passed':True,'filesExamined':len(result['files']),'oldFailureStages':[stage for e in result['files'] for r in e['rounds'] for stage,status in r['legacyResults'].items() if status!='pass'],'correctedComparisonsAccepted':all(c['accepted'] for e in result['files'] for r in e['rounds'] for c in r['correctedResults'].values()),'backupPerformed':False,'remoteWritesPerformed':False}))
    finally:
        guard.close();config.clear();api.token=None
        if transport:transport.close()
if __name__=='__main__':
    try:run(json.load(sys.stdin))
    except Exception as error:
        print(json.dumps({'passed':False,'reason':str(error) if isinstance(error,Unsafe) else type(error).__name__}));sys.exit(1)
