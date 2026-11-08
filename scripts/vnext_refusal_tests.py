"""Refus Paper réels : extension future et demande destructive en attente, état intact."""
import json
from pathlib import Path
import re
import subprocess
import server

ROOT=server.ROOT;QA=ROOT/'.cache/vn'


def main():
    report={'passed':False,'authenticatedPlayers':0,'fkamisSha256':server.digest(server.PLUGIN),'checks':[]}
    for name,marker in [('future','Version VNext future ou invalide'),('reset-pending','Réinitialisation confirmée en attente')]:
        root=QA/'runtime'/('refusal-vnext-'+name);server.restore(root,QA/'vnext-initial-3.zip')
        with server.maintenance(root):
            state=root/'plugins/FKAmis/state.yml'
            if name=='future':state.write_text(state.read_text(encoding='utf-8').replace('  version: 1','  version: 2',1),encoding='utf-8')
            else:(root/'plugins/FKAmis/reset-request.json').write_text('{}\n',encoding='utf-8')
            before={p:server.digest(root/'plugins/FKAmis'/p) for p in ('state.yml','config.yml','admins.yml','supplies.yml')}
        with server.maintenance(root,check_worlds=False):
            process=subprocess.Popen([str(server.java_path()),'-Xms1G','-Xmx4G','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25598'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            try:log,_=process.communicate(timeout=180)
            except subprocess.TimeoutExpired:log,_=process.communicate(input='stop\n',timeout=120)
        (QA/f'tests/results/refusal-{name}.log').write_text(log,encoding='utf-8')
        with server.maintenance(root):unchanged=before=={p:server.digest(root/'plugins/FKAmis'/p) for p in before}
        passed=marker in log and 'FKAmis prêt' not in log and unchanged and process.returncode==0
        check={'case':name,'passed':passed,'stateAndPoliciesUnchanged':unchanged,'expectedStartupRefusal':marker,'expectedErrorsObserved':sum(bool(re.search(r'\b(ERROR|SEVERE)\b',line)) for line in log.splitlines())}
        report['checks'].append(check)
        if not passed:raise RuntimeError('Refus non démontré : '+name)
    report['passed']=True;(ROOT/'tests/results/vnext-refusals.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
