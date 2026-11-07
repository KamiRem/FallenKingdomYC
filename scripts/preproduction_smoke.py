"""Démarrage technique local d'une COPIE, sans fka start ni joueur simulé.

Conserve la source et le ZIP scellé ; le démarrage modifie uniquement la copie.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import queue
import re
import subprocess
import threading
import time

import server


def smoke(root: Path, report_path: Path, java: Path, port: int):
    root = root.resolve()
    if root == server.server_dir('map-v2-fixes') or not root.name.startswith(('preproduction', 'migration-')):
        raise RuntimeError('Essai réservé à une copie de préproduction/migration.')
    report = {'atUtc': datetime.now(timezone.utc).isoformat(), 'instance': root.name,
              'authenticatedPlayers': 0, 'simulatedPlayers': 0, 'officialGameStarted': False,
              'commands': [], 'passed': False}
    lines = queue.Queue()
    full_log = []
    report_path.parent.mkdir(parents=True, exist_ok=True)
    java_version = subprocess.run([str(java), '-version'], capture_output=True, text=True, check=True)
    report['java'] = (java_version.stderr + java_version.stdout).splitlines()[0]
    with server.maintenance(root, check_worlds=False):
        server.validate(root)
        process = subprocess.Popen([str(java), '-Xms1G', '-Xmx4G', '-Dstdout.encoding=UTF-8', '-Dstderr.encoding=UTF-8', '-jar', 'paper.jar', '--nogui',
                                    '--host', '127.0.0.1', '--port', str(port)], cwd=root,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace', bufsize=1)

        def read():
            for line in process.stdout:
                full_log.append(line)
                lines.put(line)
        thread = threading.Thread(target=read, daemon=True)
        thread.start()

        def wait(marker, timeout=240):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try: line = lines.get(timeout=.5)
                except queue.Empty:
                    if process.poll() is not None: raise RuntimeError('Paper arrêté avant ' + marker)
                    continue
                if marker in line:
                    return
            raise RuntimeError('Délai dépassé : ' + marker)

        def command(value):
            report['commands'].append(value)
            process.stdin.write(value + '\n')
            process.stdin.flush()

        try:
            wait('Done (')
            if not any('FKAmis pr' in line for line in full_log):
                raise RuntimeError('FKAmis non activé ; migration non compatible.')
            command('version'); command('plugins')
            command('fka status'); wait('Jour 0')
            command('fka supply status')
            command('tps'); command('mspt')
            # Une barrière console laisse traiter les commandes de mesure précédentes.
            command('list'); wait('players online')
            try:
                with server.maintenance(root):
                    raise AssertionError('Verrou concurrent non appliqué')
            except RuntimeError:
                report['runningBackupRefused'] = True
            command('stop')
            code = process.wait(timeout=120)
            thread.join(timeout=5)
            report['exitCode'] = code
            if code:
                raise RuntimeError(f'Code Java {code}')
            server.check_logs(root)
            report['passed'] = True
        except Exception as exc:
            report['failure'] = str(exc)
        finally:
            if process.poll() is None:
                command('stop')
                process.wait(timeout=120)
            thread.join(timeout=5)
            log = ''.join(full_log)
            report_path.with_suffix('.log').write_text(log, encoding='utf-8')
            report['warnings'] = [line.strip() for line in full_log if re.search(r'\bWARN\b', line)]
            report['errors'] = [line.strip() for line in full_log if re.search(r'\b(ERROR|SEVERE)\b', line)]
            report['idleMetricsOnly'] = [line.strip() for line in full_log if
                                        any(marker in line for marker in ('TPS from', 'Server tick times', 'avg/min/max', '◴'))]
            state = (root / 'plugins/FKAmis/state.yml').read_text(encoding='utf-8')
            report['stillDayZero'] = bool(re.search(r'^day: 0$', state, re.M))
            report['notStarted'] = bool(re.search(r'^started: false$', state, re.M))
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('warnings', 'idleMetricsOnly')}, indent=2, ensure_ascii=False), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=server.server_dir('preproduction'))
    parser.add_argument('--report', type=Path, default=server.ROOT / 'tests/results/preproduction-smoke.json')
    parser.add_argument('--port', type=int, default=25580)
    parser.add_argument('--java', type=Path)
    args = parser.parse_args()
    result = smoke(args.root, args.report, args.java or server.java_path(), args.port)
    if not result['passed']: raise SystemExit(1)


if __name__ == '__main__': main()
