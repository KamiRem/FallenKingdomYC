"""Recettes Paper sur copies jetables conservées, jamais sur le monde de référence."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import server

ROOT=server.ROOT
BASE=ROOT/'dist/fallenkingdom-preproduction-26.3.zip'
QA=ROOT/'.cache/vn'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['admin','core','gameplay','supplies','native','features','baseline','vnext'],required=True)
    parser.add_argument('--size',type=int,choices=range(1,5),default=2)
    parser.add_argument('--attempt',type=int,default=1)
    parser.add_argument('--port',type=int,default=25587)
    args=parser.parse_args()
    if not 1<=args.attempt<=100: raise ValueError('Tentative 1..100 requise.')
    assert server.digest(BASE)=='8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de'
    specs={
      'admin':('probe-admin','FKAdminRespawnProbe.jar',['-Dfk.adminprobe=true'],[[],['-Dfk.adminprobe.restart=true']],'ADMIN PROBE SUCCESS'),
      'core':('probe-admin-core','FKRuntimeProbe.jar',['-Dfkamis.probe=true'],[[],['-Dfkamis.probe.restore=true']],'PROBE SUCCESS'),
      'gameplay':('probe-v2-fixes-admin','FKGameplayProbe.jar',['-Dfk.gameplayprobe=true'],[[]],'GAMEPLAY PROBE SUCCESS'),
      'supplies':('map-v2-qa-admin','FKMapV2SupplyProbe.jar',['-Dfk.supplyprobe=true','-Dfk.supplyprobe.reportprefix=v2-fixes-supply'],[[],['-Dfk.supplyprobe.restart=true']],'SUPPLY PROBE SUCCESS'),
      'native':('probe-native-26-3-admin','FKMigrationNativeProbe.jar',['-Dfk.nativeprobe=true'],[[]],'NATIVE PROBE SUCCESS')}
    specs['vnext']=('probe-vnext','FKVNextProbe.jar',['-Dfk.vnext=true'],[[f'-Dfk.vnext.phase={n}'] for n in range(3)],'VNEXT PROBE SUCCESS')
    specs['baseline']=('probe-features-baseline','FKFeaturesProbe.jar',['-Dfk.featuresprobe=true','-Dfk.featuresprobe.baseline=true'],[[]],'FEATURES PROBE SUCCESS')
    specs['features']=('probe-features-'+str(args.size),'FKFeaturesProbe.jar',['-Dfk.featuresprobe=true','-Dfk.featuresprobe.size='+str(args.size)],[[f'-Dfk.featuresprobe.phase={n}'] for n in range(3)],'FEATURES PROBE SUCCESS')
    prefix,probe,flags,phases,success=specs[args.suite]
    root=QA/'runtime'/f'{prefix}-{args.attempt}'
    (QA/'tests/results').mkdir(parents=True,exist_ok=True)
    server.restore(root,BASE)
    binary=ROOT/'dist/admin-update/FKAmis-1.0.0.jar' if args.suite=='baseline' else server.PLUGIN
    shutil.copy2(binary,root/'plugins/FKAmis-1.0.0.jar')
    (root/'FKAmis.sha256').write_text(server.digest(binary)+'\n',encoding='ascii')
    props=root/'server.properties';props.write_text(re.sub(r'^max-players=.*$','max-players=10',props.read_text(encoding='utf-8'),flags=re.M),encoding='utf-8')
    if args.suite=='features':
        props.write_text(re.sub(r'^max-players=.*$','max-players=20',props.read_text(encoding='utf-8'),flags=re.M),encoding='utf-8')
        config=root/'plugins/FKAmis/config.yml'
        config.write_text(config.read_text(encoding='utf-8')+'\nplayers-per-team: '+str(args.size)+'\n',encoding='utf-8')
    config=root/'plugins/FKAmis/config.yml'
    if args.suite=='vnext':
        config.write_text(config.read_text(encoding='utf-8')+'\nplayers-per-team: 2\ncustom-vnext-note: conserver\n',encoding='utf-8')
        supply=root/'plugins/FKAmis/supplies.yml';supply.write_text(supply.read_text(encoding='utf-8')+'\ncustom-vnext-supply: conserver\n',encoding='utf-8')
        state=root/'plugins/FKAmis/state.yml';state.write_text(state.read_text(encoding='utf-8')+'\ncustom-vnext-state:\n  keep: 42\n',encoding='utf-8')
    else:config.write_text(config.read_text(encoding='utf-8')+'\nrespawn-protection-seconds: 0\n',encoding='utf-8')
    shutil.copy2(ROOT/'.cache'/probe,root/'plugins'/probe)
    (root/'plugins'/probe.removesuffix('.jar')).mkdir(exist_ok=True)
    dependency_source=ROOT/'runtime/preproduction-26-3'
    for folder in ('libraries','versions','cache'):
        if (dependency_source/folder).exists():shutil.copytree(dependency_source/folder,root/folder)
    report={'suite':args.suite,'attempt':args.attempt,'format':args.size if args.suite=='features' else 2,'authenticatedPlayers':0,'fkamisSha256':server.digest(binary),'checks':[]}
    for i,extra in enumerate(phases):
        with server.maintenance(root,check_worlds=False):
            server.validate(root)
            command=[str(server.java_path()),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8',*flags,*extra,
                     '-jar','paper.jar','--nogui','--host','127.0.0.1','--port',str(args.port)]
            process=subprocess.Popen(command,cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            try:log,_=process.communicate(timeout=300)
            except subprocess.TimeoutExpired:log,_=process.communicate(input='stop\n',timeout=120)
            (QA/f'tests/results/{args.suite}-{args.size}-{args.attempt}-{i}.log').write_text(log,encoding='utf-8')
            errors=[line for line in log.splitlines() if re.search(r'\b(ERROR|SEVERE)\b',line)]
            check={'phase':str(i),'assertions':log.count('PROBE PASS '),'passed':process.returncode==0 and success in log and not errors,
                   'errors':errors,'warnings':[line for line in log.splitlines() if re.search(r'\bWARN\b',line)]}
            report['checks'].append(check);report['passed']=all(c['passed'] for c in report['checks'])
            (ROOT/('tests/results/vnext-'+args.suite+('-'+str(args.size) if args.suite=='features' else '')+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            print(json.dumps(check,ensure_ascii=False),flush=True)
            if not check['passed']:raise RuntimeError('Recette échouée ; conserver les logs et la copie.')


if __name__=='__main__':main()
