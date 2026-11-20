"""Complément ciblé en lecture seule : cinq petits fichiers, aucune relance ni audit complet."""
import sys
sys.dont_write_bytecode=True
import json
import re
import socket
from pathlib import Path
from minestrator_final_audit import BACKUP,EXPECTED_HOST,EXPECTED_SERVER,PIN,unprotect
from minestrator_cold_backup import Api,Guard,Unsafe,now,write,digest,protect_directory,protect_blob,read_remote,assert_hash_same,progress
from minestrator_sftp_inventory import pin_matches
import server
sys.modules['serverlib']=server
sys.path.insert(0,str(server.ROOT/'deployment'))
from new_match import section

TARGETS=('spigot.yml','config/paper-global.yml','server.properties','start.sh','start.ps1')

def describe(root):
    spigot=(root/'spigot.yml').read_text(encoding='utf-8-sig')
    paper=(root/'config/paper-global.yml').read_text(encoding='utf-8-sig')
    script=(root/'start.sh').read_text(encoding='utf-8-sig')
    return {'restartOnCrash':section(spigot,('settings','restart-on-crash')),
      'restartScript':section(spigot,('settings','restart-script')),'timeoutSeconds':section(spigot,('settings','timeout-time')),
      'paperWatchdogWarningDelayMs':section(paper,('watchdog','early-warning-delay')),
      'paperWatchdogWarningEveryMs':section(paper,('watchdog','early-warning-every')),
      'maxTickTimeMs':server.properties(root/'server.properties').get('max-tick-time'),
      'startShRequiresServerPort':'SERVER_PORT:?' in script,
      'startShInvokesHostOps':'maintenance/host_ops.py start' in script,
      'startShHasLoopKeyword':bool(re.search(r'(?m)^\s*(while|until|for)\b',script)),
      'scriptsExecuted':False}

def matching_host_keys(data,path=''):
    found=[]
    if not isinstance(data,dict):return found
    for key,value in data.items():
        if key in ('history','poweraction_message'):continue
        current=path+'/'+key
        if any(word in key.lower() for word in ('restart','crash','watchdog','daemon')):found.append(current)
        if isinstance(value,dict):found.extend(matching_host_keys(value,current))
    return found

def run(config):
    import paramiko
    if int(config['serverId'])!=EXPECTED_SERVER or config['host']!=EXPECTED_HOST or int(config['port'])!=2022 or config['fingerprint']!=PIN:raise Unsafe('IdentityMismatch')
    expected_manifest='b54da288c8ad983c6bc35172ed1e0a697812b210dd7afe38ffb7e060f9ff81a1'
    if digest(BACKUP/'manifest.json')!=expected_manifest:raise Unsafe('HistoricalManifestChanged')
    baseline=json.loads((BACKUP/'manifest.json').read_text(encoding='utf-8'))['files']
    for name in TARGETS:
        if digest(BACKUP/'restore'/name)!=baseline[name]['sha256']:raise Unsafe('HistoricalTargetChanged')
    out=Path(config['output']).resolve()
    if out.is_relative_to(server.ROOT) or out.is_relative_to(BACKUP):raise Unsafe('UnsafeOutput')
    protect_directory(out)
    report={'scope':'targeted_crash_restart_check','startedAtUtc':now(),'passed':False,'serverId':EXPECTED_SERVER,
      'fullAuditRepeated':False,'remoteWritesPerformed':False,'powerOrConsoleCommandSent':False,'scriptsExecuted':False,
      'hostingCrashRestartPolicyVerified':False,'exclusiveHostLock':False,'files':[]}
    api=Api(config.pop('apiKey'),config['serverId']);guard=Guard(api);transport=None
    try:
        data=api.get('');srv=data['server']
        if int(srv['id'])!=EXPECTED_SERVER or int(srv['port'])!=22880:raise Unsafe('ServerIdentityMismatch')
        info={k:data.get(k) for k in ('settings','ports','offer')}|{'resources':data.get('mybox',{}).get('resources'),'port':srv['port']}
        old=unprotect(BACKUP/'panel-settings.dpapi');settings=info.get('settings') or {};previous=old.get('settings') or {}
        changed=[key for key in settings.keys()|previous.keys() if settings.get(key)!=previous.get(key)]
        if changed or info.get('ports')!=old.get('ports'):raise Unsafe('PanelPreconditionChanged',details={'changedSettingKeys':changed,'portsChanged':info.get('ports')!=old.get('ports')})
        (out/'panel-current.dpapi').write_bytes(protect_blob(json.dumps(info).encode()))
        report.update({'panelSettingsUnchanged':True,'hostingRestartRelatedKeysExposed':matching_host_keys(data),
          'startupCommandHasLoopKeyword':bool(re.search(r'\b(while|until)\b',str(settings.get('startup','')))),
          'javaVersionId':settings.get('id_java_version'),'image':settings.get('image'),'startupFile':settings.get('startup_file')})
        guard.start();progress('targeted_identity_offline_confirmed',serverId=EXPECTED_SERVER)
        transport=paramiko.Transport(socket.create_connection((config['host'],int(config['port'])),timeout=15));guard.abort=transport.close;transport.start_client(timeout=20)
        if not pin_matches(transport.get_remote_server_key(),PIN):raise Unsafe('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise Unsafe('SftpAuthenticationFailed')
        anchors={n:baseline[n]['pathStatBaseline'] for n in TARGETS}
        with paramiko.SFTPClient.from_transport(transport) as client:
            client.get_channel().settimeout(15)
            for name in TARGETS:
                for index in range(2):
                    actual=read_remote(client,name,baseline[name],guard,anchors=anchors)
                    assert_hash_same(actual,baseline[name]['sha256'],name=name,stage='targeted_pass_'+str(index+1))
                report['files'].append({'path':name,'sha256':actual,'reads':2,'matchesBackup':True,'bytes':baseline[name]['size']})
            guard.poll();guard.check()
        report.update(describe(BACKUP/'restore'));report['passed']=True
    except Exception as error:
        report['failure']=str(error) if isinstance(error,Unsafe) else type(error).__name__
        if isinstance(error,Unsafe) and error.details:write(out/'divergence-private.json',error.details)
    finally:
        guard.close()
        if guard.failed.is_set():report['passed']=False;report['failure']=guard.reason
        if transport:transport.close()
        config.clear();report['apiObservations']=guard.samples;report['finishedAtUtc']=now()
        report['historicalTargetFilesUnchanged']=all(digest(BACKUP/'restore'/n)==baseline[n]['sha256'] for n in TARGETS)
        report['historicalManifestUnchanged']=digest(BACKUP/'manifest.json')==expected_manifest
        if not report['historicalTargetFilesUnchanged'] or not report['historicalManifestUnchanged']:report['passed']=False;report['failure']='HistoricalPreservationFailed'
        write(out/'report.json',report)
    progress('targeted_check_finished',passed=report['passed'],filesRead=len(report['files']),restartOnCrash=report.get('restartOnCrash'),failure=report.get('failure'))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    try:sys.exit(run(json.load(sys.stdin)))
    except Exception as error:progress('targeted_check_not_started',failure=str(error) if isinstance(error,Unsafe) else type(error).__name__);sys.exit(1)
