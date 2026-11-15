"""Inventaire SFTP exclusivement en lecture ; secrets via stdin, clé hôte épinglée."""
import base64
import hashlib
import hmac
import io
import json
from pathlib import Path
import posixpath
import re
import socket
import stat
import sys
import zipfile
import logging
logging.getLogger('paramiko').setLevel(logging.CRITICAL)

def fingerprint(key):return 'SHA256:'+base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
def pin_matches(key,expected):
    if not re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}',expected):return False
    return hmac.compare_digest(fingerprint(key),expected)

def inventory(client):
    result={'files':[],'directories':[],'linksRefused':[],'pluginDescriptors':[],'complete':True}
    stack=['.'];count=0
    important={'server.properties','RUNTIME_LOCK.json','FKAmis.sha256','eula.txt','whitelist.json','ops.json','banned-players.json','banned-ips.json',
      'plugins/FKAmis/config.yml','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','map-v2-construction.json','map-v21-caverns.json'}
    while stack:
        folder=stack.pop()
        for item in client.listdir_attr(folder):
            name=item.filename
            if name in ('.','..') or '/' in name or '\\' in name:raise RuntimeError('UnsafeRemoteName')
            path=posixpath.join(folder,name).removeprefix('./');count+=1
            if count>50000:raise RuntimeError('InventoryLimitReached')
            if stat.S_ISLNK(item.st_mode):result['linksRefused'].append(path);result['complete']=False;continue
            if stat.S_ISDIR(item.st_mode):result['directories'].append(path);stack.append(path);continue
            if not stat.S_ISREG(item.st_mode):result['complete']=False;continue
            record={'path':path,'size':item.st_size,'mtime':item.st_mtime,'mode':stat.S_IMODE(item.st_mode)}
            jar=(path.endswith('.jar') and ('/' not in path or path.startswith('plugins/') and path.count('/')==1))
            if jar or path in important:
                if item.st_size>1024**3:raise RuntimeError('FileTooLarge')
                digest=hashlib.sha256();data=io.BytesIO() if jar and path.startswith('plugins/') and item.st_size<=64*1024**2 else None
                with client.open(path,'rb') as handle:
                    observed=handle.stat()
                    if observed.st_size!=item.st_size or observed.st_mtime!=item.st_mtime:raise RuntimeError('RemoteFileChanged')
                    total=0
                    while chunk:=handle.read(1024*1024):
                        total+=len(chunk)
                        if total>item.st_size:raise RuntimeError('RemoteFileChanged')
                        digest.update(chunk)
                        if data is not None:data.write(chunk)
                after=client.lstat(path)
                if total!=item.st_size or after.st_size!=item.st_size or after.st_mtime!=item.st_mtime:raise RuntimeError('RemoteFileChanged')
                record['sha256']=digest.hexdigest()
                if data is not None:
                    try:
                        with zipfile.ZipFile(data) as archive:
                            for descriptor in ('plugin.yml','paper-plugin.yml'):
                                if descriptor in archive.namelist():
                                    entry=archive.getinfo(descriptor)
                                    if entry.file_size>128*1024:raise RuntimeError('DescriptorTooLarge')
                                    text=archive.read(entry).decode('utf-8')
                                    values={}
                                    for key in ('name','version','main','api-version'):
                                        m=re.search(r'^'+key+r':\s*[\"\x27]?([^\r\n]+)',text,re.M)
                                        if m:values[key]=m.group(1).strip().strip('\"\x27')
                                    result['pluginDescriptors'].append({'path':path,**values})
                    except zipfile.BadZipFile:record['descriptorError']='invalidJar'
            result['files'].append(record)
    result['files'].sort(key=lambda x:x['path']);result['directories'].sort();return result

def main():
    import paramiko
    config=json.load(sys.stdin);out=Path(config['output'])
    if out.exists():raise RuntimeError('OutputExists')
    transport=None
    try:
        sock=socket.create_connection((config['host'],int(config['port'])),timeout=15)
        transport=paramiko.Transport(sock);transport.start_client(timeout=20)
        # Vérifier AVANT de transmettre le mot de passe.
        key=transport.get_remote_server_key()
        if not pin_matches(key,config['fingerprint']):raise RuntimeError('HostKeyMismatch')
        transport.auth_password(config['user'],config.pop('password'),fallback=False)
        if not transport.is_authenticated():raise RuntimeError('AuthenticationFailed')
        with paramiko.SFTPClient.from_transport(transport) as sftp:
            sftp.get_channel().settimeout(30)
            result=inventory(sftp)
            private={}
            for path in config.get('readFiles',[]):
                if path not in {'server.properties','RUNTIME_LOCK.json','plugins/FKAmis/config.yml','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','whitelist.json','ops.json','map-v2-construction.json','map-v21-caverns.json','logs/latest.log'}:raise RuntimeError('UnsafeRemoteName')
                try:attr=sftp.lstat(path)
                except FileNotFoundError:continue
                if not stat.S_ISREG(attr.st_mode) or attr.st_size>4*1024**2:raise RuntimeError('FileTooLarge')
                with sftp.open(path,'rb') as handle:data=handle.read(4*1024**2+1)
                after=sftp.lstat(path)
                if len(data)!=attr.st_size or after.st_size!=attr.st_size or after.st_mtime!=attr.st_mtime:raise RuntimeError('RemoteFileChanged')
                private[path]=base64.b64encode(data).decode()
        result.update({'authenticated':True,'hostKeyVerified':True,'hostKeyType':key.get_name(),'remoteWritesPerformed':False,'coldBackup':False})
        out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps({'authenticated':True,'hostKeyVerified':True,'complete':result['complete'],'files':len(result['files']),'directories':len(result['directories']),'remoteWritesPerformed':False,'privateContents':private}))
    finally:
        config.clear()
        if transport:transport.close()

if __name__=='__main__':
    try:main()
    except Exception as error:
        # Aucun traceback ou message libre pouvant contenir des paramètres privés.
        print(json.dumps({'passed':False,'failureType':type(error).__name__,'reason':str(error) if str(error) in {'HostKeyMismatch','OutputExists','RemoteFileChanged','InventoryLimitReached','UnsafeRemoteName','FileTooLarge','AuthenticationFailed'} else 'Détails masqués pour protéger les accès'}))
        sys.exit(1)
