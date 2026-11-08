"""Recette à froid : reset logique, référence initiale de fixture et restauration complète isolée."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import re
import server
from preproduction_smoke import smoke

ROOT=server.ROOT
sys.modules['serverlib']=server
spec=importlib.util.spec_from_file_location('new_match',ROOT/'deployment/new_match.py')
reset=importlib.util.module_from_spec(spec);spec.loader.exec_module(reset)


def files(root):return {p.relative_to(root).as_posix():server.digest(p) for p in server.iter_files(root)}
def remove_probe(root):
    with server.maintenance(root):(root/'plugins/FKVNextProbe.jar').unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-attempt',type=int,required=True);parser.add_argument('--attempt',type=int,required=True);parser.add_argument('--resume-full',action='store_true');args=parser.parse_args()
    qa=ROOT/'.cache/vn';root=qa/'runtime'/f'probe-vnext-{args.source_attempt}';reference=ROOT/'configs/vnext/new-match-reference.json'
    report={'authenticatedPlayers':0,'fkamisSha256':server.digest(server.PLUGIN),'passed':False}
    pending=qa/f'tests/results/reset-pending-{args.attempt}.json'
    if args.resume_full:
        report=json.loads(pending.read_text(encoding='utf-8'))
        if report['fkamisSha256']!=server.digest(server.PLUGIN):raise RuntimeError('Binaire changé : refaire la recette.')
        full(root,qa,reference,args,report);return
    remove_probe(root)
    before=files(root);token=(root/'plugins/FKVNextProbe/reset-token.txt').read_text()
    logical=reset.logical(root,token);after=files(root)
    protected=[name for name in before if name.startswith(('world/','world_nether/','world_the_end/','plugins/FKAmis/history/')) or name in reset.POLICY_FILES]
    if any(before[name]!=after.get(name) for name in protected):raise RuntimeError('Monde, inventaires, historique ou règles modifiés par reset logique.')
    report['logical']={**logical,'protectedFilesCompared':len(protected)}
    # Réinstalle uniquement le probe de recette dans sa copie privée.
    with server.maintenance(root):shutil.copy2(ROOT/'.cache/FKVNextProbe.jar',root/'plugins/FKVNextProbe.jar')
    with server.maintenance(root,check_worlds=False):
        process=subprocess.Popen([str(server.java_path()),'-Xms1G','-Xmx4G','-Dfk.vnext=true','-Dfk.vnext.phase=3','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25596'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        try:log,_=process.communicate(timeout=300)
        except subprocess.TimeoutExpired:log,_=process.communicate(input='stop\n',timeout=120)
    (qa/f'tests/results/vnext-reset-{args.attempt}.log').write_text(log,encoding='utf-8')
    errors=[line for line in log.splitlines() if re.search(r'\b(ERROR|SEVERE)\b',line)]
    if process.returncode or 'VNEXT PROBE SUCCESS' not in log or errors:raise RuntimeError('Redémarrage après reset échoué : '+str(errors))
    report['logicalRestart']={'passed':True,'assertions':log.count('PROBE PASS '),'errors':errors}
    remove_probe(root)
    pending.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    full(root,qa,reference,args,report)


def full(root,qa,reference,args,report):
    # Référence initiale construite exclusivement depuis l'archive initiale : aucun
    # bloc, joueur ou inventaire de la partie technique n'y est transféré.
    baseline=qa/'runtime'/f'preproduction-vnext-initial-{args.attempt}'
    server.restore(baseline,ROOT/'dist/fallenkingdom-preproduction-26.3.zip')
    with server.maintenance(baseline):
        shutil.copy2(server.PLUGIN,baseline/'plugins/FKAmis-1.0.0.jar');(baseline/'FKAmis.sha256').write_text(server.digest(server.PLUGIN)+'\n')
        for name in reset.POLICY_FILES:
            if (root/name).is_file():shutil.copy2(root/name,baseline/name)
        lock=baseline/'RUNTIME_LOCK.json';data=json.loads(lock.read_text());data['sha256']['plugins/FKAmis-1.0.0.jar']=server.digest(server.PLUGIN);lock.write_text(json.dumps(data,indent=2)+'\n')
        for folder in ('libraries','versions','cache'):
            if (ROOT/'runtime/preproduction-26-3'/folder).exists():shutil.copytree(ROOT/'runtime/preproduction-26-3'/folder,baseline/folder)
    check=smoke(baseline,ROOT/f'tests/results/vnext-initial-smoke-{args.attempt}.json',server.java_path(),25594)
    if not check['passed'] or check['errors']:raise RuntimeError('Copie initiale VNext non saine.')
    # L'option --port du démarrage technique est enregistrée par Paper. Remettre
    # ici les propriétés déclarées de la fixture avant de sceller sa référence.
    with server.maintenance(baseline):shutil.copy2(root/'server.properties',baseline/'server.properties')
    archive=qa/f'vnext-initial-{args.attempt}.zip'
    approval=reset.seal_baseline(baseline,archive,reference,True) # approbation de fixture automatisée, aucune approbation production.
    report['baseline']={**approval,'testFixtureOnly':True,'visuallyInspected':False}
    token=(root/'plugins/FKVNextProbe/reset-token.txt').read_text()
    # Vérifie le refus de mélange de rôles, puis rétablit exactement la fixture.
    admins=root/'plugins/FKAmis/admins.yml';original=admins.read_bytes()
    with server.maintenance(root):admins.write_bytes(original+b'\n# politique differente\n')
    try:
        try:reset.restore_initial(root,token,archive,qa/'runtime'/f'refused-policy-{args.attempt}',reference)
        except RuntimeError as e:
            if 'Règles, rôles' not in str(e):raise
            report['differentPoliciesRefused']=True
        else:raise AssertionError('Une politique différente doit être refusée.')
    finally:
        with server.maintenance(root):admins.write_bytes(original)
    destination=qa/'runtime'/f'preproduction-vnext-restored-{args.attempt}'
    report['fullRestore']=reset.restore_initial(root,token,archive,destination,reference)
    report['fullRestoreStartup']=smoke(destination,ROOT/f'tests/results/vnext-restored-smoke-{args.attempt}.json',server.java_path(),25595)
    if not report['fullRestoreStartup']['passed'] or report['fullRestoreStartup']['errors']:raise RuntimeError('Démarrage initial restauré échoué.')
    report['passed']=True
    (ROOT/'tests/results/vnext-reset-restore.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('fullRestoreStartup',)},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
