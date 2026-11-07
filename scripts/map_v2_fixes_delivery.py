"""Contrôle à froid des sources préservées et de la livraison corrigée ; aucun monde remplacé."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
from server import ROOT, server_dir, maintenance, iter_files, digest, verify_archive, validate


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    results=ROOT/'tests/results'
    baseline=json.loads((ROOT/'.cache/v2-fixes-baseline.json').read_text(encoding='utf-8'))
    sources={}
    for name,expected in baseline['instances'].items():
        root=server_dir(name)
        with maintenance(root):actual={str(p.relative_to(root)):digest(p) for p in iter_files(root)}
        if actual!=expected:raise RuntimeError('Une source a changé : '+name)
        sources[name]={'unchanged':True,'comparedFiles':len(actual)}
    original_archive=ROOT/baseline['archive']
    if digest(original_archive)!=baseline['sha256']:raise RuntimeError('Archive source différente.')
    verify_archive(original_archive)
    root=server_dir('map-v2-fixes')
    with maintenance(root):
        validate(root)
        state=(root/'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
        for pattern in (r'^started: false$',r'^day: 0$',r'^  remaining: 1800$',r'^  event: 0$',r'^terrain-validated: \[\]$'):
            if not re.search(pattern,state,re.M):raise RuntimeError('État de livraison inattendu : '+pattern)
        if re.search(r'^(objectives|roster):',state,re.M):raise RuntimeError('Objectifs ou identités présents dans la candidate avant départ.')
        plugins=sorted(p.name for p in (root/'plugins').rglob('*.jar'))
        if any('Probe' in p or 'Builder' in p or 'Corrections' in p for p in plugins):raise RuntimeError('Outil temporaire présent dans la livraison.')
        jar=root/'plugins/FKAmis-1.0.0.jar'
        if digest(jar)!=digest(ROOT/'plugins-custom/fk-amis/target/fk-amis-1.0.0.jar'):raise RuntimeError('JAR livré différent du JAR compilé.')
        profile=ROOT/'configs/map-v2-fixes';profile.mkdir(exist_ok=True)
        shutil.copy2(root/'plugins/FKAmis/config.yml',profile/'fkamis.yml')
        shutil.copy2(root/'plugins/FKAmis/supplies.yml',profile/'supplies.yml')
    for name in ('v2-fixes-world.json','v2-fixes-gameplay.json','v2-fixes-cleanup-total.json','v2-fixes-supply-initial.json','v2-fixes-supply-restart.json','v2-fixes-supply-restoration.json'):
        if not (results/name).is_file():raise RuntimeError('Rapport requis absent : '+name)
    cleanup=json.loads((results/'v2-fixes-cleanup-total.json').read_text(encoding='utf-8'))
    gameplay=json.loads((results/'v2-fixes-gameplay.json').read_text(encoding='utf-8'))
    world=json.loads((results/'v2-fixes-world.json').read_text(encoding='utf-8'))
    archives=sorted((ROOT/'dist').glob('fallenkingdom-map-v2-fixes-*.zip'),key=lambda p:p.stat().st_mtime)
    if not archives:raise RuntimeError('Exporter la candidate corrigée avant le bilan final.')
    archive=archives[-1];manifest=verify_archive(archive)
    report={'checkedAtUtc':datetime.now(timezone.utc).isoformat(),'sources':sources,'initialV2Backup':baseline['archive'],
            'initialV2BackupSha256':baseline['sha256'],'candidate':'runtime/map-v2-fixes','jarSha256':digest(jar),
            'archive':str(archive.relative_to(ROOT)),'archiveSha256':digest(archive),'archiveBytes':archive.stat().st_size,
            'archiveFiles':len(manifest['files']),'cleanedNaturalBlocks':cleanup['totalRemoved'],
            'worldChecks':len(world['passed']),'gameplayChecks':len(gameplay['passed']),
            'authenticatedPlayers':gameplay['authenticatedPlayers'],'visualValidation':False,'officialGameStarted':False,'plugins':plugins}
    write(results/'v2-fixes-delivery.json',report)
    index=ROOT/'maps/manifest.json';data=json.loads(index.read_text(encoding='utf-8'))
    data.update({'candidate':'runtime/map-v2-fixes','previousCandidate':'runtime/map-v2','cleanupReport':'tests/results/v2-fixes-cleanup-total.json',
                 'worldChecks':'tests/results/v2-fixes-world.json','corrections':'docs/V2_CORRECTIONS.md','visualValidation':False})
    write(index,data)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
