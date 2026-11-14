"""Construction V2.1 sur une référence initiale scellée, toujours dans une sortie distincte."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
import server
from cavern_plan import make_plan,digest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'deployment'))
import territory_migration as territories
SOURCE='8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de'


def initial(text,names):
    if territories.get(text,'schema')!='1' or territories.get(text,'started')!='false' or territories.get(text,'day')!='0':raise RuntimeError('Une référence initiale jour zéro est obligatoire.')
    for key in ('roster','objectives'):
        if territories.get(text,key) not in (None,'{}'):raise RuntimeError('Affiliations ou objectifs présents : génération destructive refusée.')
    if any(name.endswith('.dat') and ('/players/data/' in name or '/playerdata/' in name) for name in names):raise RuntimeError('Profils joueurs présents : ne pas utiliser une sauvegarde jouée.')


def write(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def build(source,expected,output,apply,initial_reference,plugin,builder,reference,defaults,java,dependencies=None):
    source=source.resolve();output=output.resolve()
    if not initial_reference:raise RuntimeError('Déclarer explicitement --initial-reference ; jamais la sauvegarde de la partie réelle.')
    if server.digest(source)!=expected:raise RuntimeError('Archive différente de son SHA-256 de confiance.')
    if expected!=SOURCE:
        approval=source.with_suffix('.approved.json')
        approval_data=json.loads(approval.read_text()) if approval.is_file() else {}
        if approval_data.get('schema')!=1 or approval_data.get('sha256')!=expected or not approval_data.get('approvedInitial'):raise RuntimeError('Référence inconnue : approbation initiale scellée requise.')
    if source.is_relative_to(output):raise RuntimeError('Archive source distincte de la sortie requise.')
    server.verify_archive(source)
    with zipfile.ZipFile(source) as z:initial(z.read('plugins/FKAmis/state.yml').decode('utf-8'),z.namelist())
    server.restore(output,source)
    with server.maintenance(output):
        metadata=json.loads((output/'map-v2-construction.json').read_text(encoding='utf-8'))
        if (output/'map-v21-caverns.json').exists():raise RuntimeError('Cette référence a déjà des cavernes ; aucune régénération automatique.')
        state=(output/'plugins/FKAmis/state.yml').read_text(encoding='utf-8');territory=territories.plan(state)
        if not territory['passed']:raise RuntimeError('Territoires incompatibles.')
        plan=make_plan(output,metadata,json.loads(reference.read_text(encoding='utf-8')))
        summary={k:v for k,v in plan.items() if k!='blocks'};summary.update({'inputSha256':expected,'output':str(output),'dryRun':not apply})
        write(output/'map-v21-preview.json',summary)
        if not plan['passed']:raise RuntimeError('Collision détectée ; copie conservée, aucun bloc modifié. Lire map-v21-preview.json.')
        write(output/'map-v21-plan.json',plan)
        if not apply:return summary
        backup=output.parent/'.map-v21-backups'/(output.name+'-before.zip');server.create_archive(output,backup)
        old_config=(output/'plugins/FKAmis/config.yml').read_bytes();old_admins=(output/'plugins/FKAmis/admins.yml').read_bytes() if (output/'plugins/FKAmis/admins.yml').exists() else None;old_supplies=(output/'plugins/FKAmis/supplies.yml').read_bytes()
        new_state,_=territories.migrate(state);(output/'plugins/FKAmis/state.yml').write_text(new_state,encoding='utf-8')
        for b in metadata['bases']:b['radius']=40
        metadata['territoryRevision']='VNext.1';write(output/'map-v2-construction.json',metadata)
        shutil.copy2(plugin,output/'plugins/FKAmis-1.0.0.jar');(output/'FKAmis.sha256').write_text(server.digest(plugin)+'\n',encoding='ascii')
        lock=output/'RUNTIME_LOCK.json';registry=json.loads(lock.read_text(encoding='utf-8'));registry.setdefault('sha256',{})['plugins/FKAmis-1.0.0.jar']=server.digest(plugin);registry['fkamisUpdate']='vnext.1';write(lock,registry)
        props=output/'server.properties';text=props.read_text(encoding='utf-8');count=len(re.findall(r'^allow-flight=.*$',text,re.M))
        if count>1:raise RuntimeError('allow-flight dupliqué dans la référence initiale.')
        declared_properties=re.sub(r'^allow-flight=.*$','allow-flight=true',text,flags=re.M) if count else text.rstrip()+'\nallow-flight=true\n'
        props.write_text(declared_properties,encoding='utf-8')
        shutil.copy2(builder,output/'plugins/FKMapV21Builder.jar')
        if dependencies:
            for name in ('libraries','versions','cache'):
                if (dependencies/name).exists() and not (output/name).exists():shutil.copytree(dependencies/name,output/name)
    with server.maintenance(output,check_worlds=False):
        server.validate(output)
        process=subprocess.Popen([str(java),'-Xms1G','-Xmx4G','-Dfk.mapv21=true','-Dstdout.encoding=UTF-8','-Dstderr.encoding=UTF-8','-jar','paper.jar','--nogui','--host','127.0.0.1','--port','25604'],cwd=output,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        try:log,_=process.communicate(timeout=360)
        except subprocess.TimeoutExpired:log,_=process.communicate(input='stop\n',timeout=120)
    (output.parent/(output.name+'-construction.log')).write_text(log,encoding='utf-8')
    errors=[line for line in log.splitlines() if re.search(r'\b(ERROR|SEVERE)\b',line)]
    if process.returncode or 'MAP V21 BUILD SUCCESS' not in log or errors:raise RuntimeError('Construction incomplète ; copie et sauvegarde conservées : '+str(errors[:2]))
    with server.maintenance(output):
        (output/'plugins/FKMapV21Builder.jar').unlink()
        # Paper enregistre les options --host/--port du serveur de construction.
        # La sortie reprend les paramètres déclarés de sa référence, sauf allow-flight.
        (output/'server.properties').write_text(declared_properties,encoding='utf-8')
        if (output/'plugins/FKAmis/config.yml').read_bytes()!=old_config or (output/'plugins/FKAmis/supplies.yml').read_bytes()!=old_supplies or old_admins is not None and (output/'plugins/FKAmis/admins.yml').read_bytes()!=old_admins:raise RuntimeError('Configuration, rôles ou ravitaillement différents.')
        metadata=json.loads((output/'map-v2-construction.json').read_text(encoding='utf-8'));metadata['mapVersion']='2.1';write(output/'map-v2-construction.json',metadata)
        cave_reference=json.loads(reference.read_text(encoding='utf-8'))
        for b in cave_reference['bases']:b['radius']=40
        cave_reference['mapVersion']='2.1';cave_reference['caverns']=[]
        for team in territories.TEAMS:
            entries=[b for b in plan['blocks'] if b['team']==team]
            actual=[[b['at'][0],b['at'][1],b['at'][2],b['after'].partition('[')[0]] for b in entries]
            cave_reference['caverns'].append({'team':team,'checkPoints':[b['at'] for b in entries],'blockTypesSha256':hashlib.sha256(json.dumps(actual,separators=(',',':')).encode()).hexdigest()})
        write(output/'map-v21-caverns.json',{**summary,'built':True,'visuallyInspected':False,'backupSha256':server.digest(backup)})
        (output/'maintenance').mkdir(exist_ok=True);write(output/'maintenance/new-match-reference-v2.1.json',cave_reference)
        source_root=Path(__file__).resolve().parents[1]
        for name,relative in {'serverlib.py':'scripts/server.py','map_reader.py':'scripts/map_reader.py','new_match.py':'deployment/new_match.py','host_ops.py':'deployment/host_ops.py','territory_migration.py':'deployment/territory_migration.py'}.items():
            shutil.copy2(source_root/relative,output/'maintenance'/name)
        # Les fichiers de travail de construction restent dans la copie de recette,
        # jamais dans une archive de mise à jour de partie jouée.
    from map_v21_verify import verify
    integrity=verify(output,backup,defaults,plan)
    if not integrity['passed']:raise RuntimeError('Intégrité hors chantier non conservée ; ne pas utiliser cette sortie. Lire les erreurs : '+str(integrity['errors'][:3]))
    result={**summary,'passed':True,'dryRun':False,'build':json.loads((output/'map-v21-build-report.json').read_text()),'integrity':integrity,'backup':str(backup),'backupSha256':server.digest(backup),'fkamisSha256':server.digest(plugin),'visualInspection':False}
    write(output.parent/(output.name+'-result.json'),result);return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');parser.add_argument('--initial-reference',action='store_true')
    parser.add_argument('--plugin',type=Path,default=server.PLUGIN);parser.add_argument('--builder',type=Path,default=server.ROOT/'.cache/FKMapV21Builder.jar');parser.add_argument('--reference',type=Path,default=server.ROOT/'configs/vnext/new-match-reference.json');parser.add_argument('--defaults',type=Path,default=server.ROOT/'.cache/gameplay-qa/tests/results/block-defaults-26.3.json');parser.add_argument('--java',type=Path);parser.add_argument('--dependencies',type=Path)
    args=parser.parse_args();result=build(args.input,args.sha256,args.output,args.apply,args.initial_reference,args.plugin,args.builder,args.reference,args.defaults,args.java or server.java_path(),args.dependencies)
    print(json.dumps({k:v for k,v in result.items() if k not in ('chunks','build')},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
