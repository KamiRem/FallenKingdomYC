"""Recette des ravitaillements sur une copie isolée, puis après redémarrage."""
from pathlib import Path
import shutil
import subprocess
import argparse
import json
from server import ROOT, server_dir, backup, restore, maintenance, java_path, digest, validate, verify_archive


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',default='map-v2-qa')
    parser.add_argument('--source',choices=['map-v2','map-v2-fixes'],default='map-v2')
    args=parser.parse_args()
    if not args.name.startswith('map-v2-qa'): raise ValueError('Nom de recette réservé à map-v2-qa...')
    source = server_dir(args.source)
    prefix='v2-fixes-supply' if args.source=='map-v2-fixes' else 'map-v2-supply'
    root = server_dir(args.name)
    restored = server_dir(args.name + '-restored')
    if root.exists() or restored.exists():
        raise RuntimeError('Recette conservée : choisir un nouveau nom, sans écraser les résultats précédents.')
    restore(root, backup(source))
    with maintenance(root, check_worlds=False):
        companion = ROOT / "plugins-custom/fk-amis/target/fk-amis-1.0.0.jar"
        shutil.copy2(companion, root / "plugins/FKAmis-1.0.0.jar")
        (root / "FKAmis.sha256").write_text(digest(companion)+"\n", encoding="ascii")
        shutil.copy2(ROOT / ".cache/FKMapV2SupplyProbe.jar", root / "plugins/FKMapV2SupplyProbe.jar")
        validate(root)
        (root / "plugins/FKMapV2SupplyProbe").mkdir(exist_ok=True)
    for phase in ("initial", "restart"):
        with maintenance(root, check_worlds=False):
            command = [str(java_path()), "-Xms1G", "-Xmx4G", "-Dfk.supplyprobe=true",f"-Dfk.supplyprobe.reportprefix={prefix}"]
            if phase == "restart": command.append("-Dfk.supplyprobe.restart=true")
            command += ["-jar", "paper.jar", "--nogui", "--host", "127.0.0.1", "--port", "25578"]
            output = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
            text = output.stdout + output.stderr
            (ROOT / ".cache" / f"map-v2-supply-{phase}.log").write_text(text, encoding="utf-8")
            if output.returncode or "SUPPLY PROBE SUCCESS" not in text or "SUPPLY PROBE FAILED" in text:
                print(text[-18000:], flush=True)
                raise RuntimeError(f"Recette {phase} échouée")
            print(f"Recette {phase} réussie ; état et événements API vérifiés.", flush=True)
        if phase == 'initial':
            # Restauration complète de l'état contenant un lot récupéré et un actif.
            archive = backup(root)
            saved_hash = digest(root / 'plugins/FKAmis/state.yml')
            restore(restored, archive)
            if digest(restored / 'plugins/FKAmis/state.yml') != saved_hash:
                raise RuntimeError('État de ravitaillement différent après restauration.')
            report = {'source': str(root.relative_to(ROOT)), 'restored': str(restored.relative_to(ROOT)),
                      'archive': str(archive.relative_to(ROOT)), 'sha256': digest(archive),
                      'manifestFiles': len(verify_archive(archive)['files']), 'stateByteIdentical': True,
                      'note': 'La phase restart contrôle les lots actifs et récupérés dans cette copie restaurée.'}
            (ROOT / f'tests/results/{prefix}-restoration.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            root = restored


if __name__ == "__main__": main()
