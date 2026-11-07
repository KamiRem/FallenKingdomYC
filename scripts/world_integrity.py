"""Compare une carte convertie à son archive, sans écrire dans les mondes.

Les octets Anvil peuvent changer (version NBT, éclairage, temps de sauvegarde).
On compare les blocs, biomes, block entities et inventaires pour chaque chunk modifié.
"""
from __future__ import annotations
import gzip
import hashlib
import json
from pathlib import Path
import zipfile
import zlib

from v2_reference import nbt, normalized_state


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      default=lambda b: {'bytes': b.hex()})


def states_equal(left, right, size=4096, minimum_bits=4, defaults=None):
    if left == right: return True
    if left is None or right is None: return False

    def values(states):
        palette = []
        for item in states['palette']:
            state = normalized_state(item)
            # 26.3 omet les propriétés par défaut. Les valeurs proviennent du registre
            # Bukkit réel de la version cible, jamais d'une supposition du lecteur.
            properties = dict((defaults or {}).get(state['Name'], {}))
            properties.update(state.get('Properties', {}))
            if properties: state['Properties'] = properties
            palette.append(canonical(state))
        if len(palette) == 1: return [palette[0]] * size
        bits = max(minimum_bits, (len(palette) - 1).bit_length())
        per_long = 64 // bits
        return [palette[((states['data'][i // per_long] & ((1 << 64) - 1))
                         >> ((i % per_long) * bits)) & ((1 << bits) - 1)] for i in range(size)]
    return values(left) == values(right)


def chunks(data: bytes):
    result = {}
    if len(data) < 8192: raise ValueError('Région Anvil tronquée.')
    for index in range(1024):
        offset = int.from_bytes(data[index * 4:index * 4 + 3], 'big')
        if not offset: continue
        at = offset * 4096
        length = int.from_bytes(data[at:at + 4], 'big')
        codec = data[at + 4]
        if codec & 128: raise ValueError('Chunk externe .mcc : contrôle dédié nécessaire.')
        result[index] = (codec, data[at + 5:at + 4 + length])
    return result


def decode(value):
    codec, data = value
    if codec == 1: data = gzip.decompress(data)
    elif codec == 2: data = zlib.decompress(data)
    elif codec != 3: raise ValueError('Compression Anvil inconnue.')
    return nbt(data)


def terrain_equal(left, right, defaults=None):
    left_sections = {s['Y']: s for s in left.get('sections', [])}
    right_sections = {s['Y']: s for s in right.get('sections', [])}
    if left_sections.keys() != right_sections.keys(): return False
    for y, section in left_sections.items():
        other = right_sections[y]
        if not states_equal(section.get('block_states'), other.get('block_states'), defaults=defaults): return False
        if not states_equal(section.get('biomes'), other.get('biomes'), 64, 1): return False
    # Les métadonnées des coffres, inventaires et PDC font partie du contrôle.
    def tiles(chunk):
        return sorted((canonical({k: v for k, v in entry.items() if k != 'keepPacked'})
                       for entry in chunk.get('block_entities', [])))
    return tiles(left) == tiles(right)


def entity_inventory(chunk):
    result = {}
    def walk(value, at=''):
        found = {}
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in {'items', 'inventory', 'handitems', 'armoritems', 'equipment', 'weapon', 'saddleitem'}:
                    found[at + '/' + key] = item
                else: found.update(walk(item, at + '/' + key))
        elif isinstance(value, list):
            for index, item in enumerate(value): found.update(walk(item, at + '/' + str(index)))
        return found
    for entity in chunk.get('Entities', []):
        identity = canonical(entity.get('UUID', entity.get('uuid')))
        result[identity] = {'id': entity.get('id'), 'inventories': walk(entity)}
    return result


def compare(root: Path, archive: Path, defaults=None):
    report = {'regionFilesByteIdentical': 0, 'regionFilesSemanticallyChecked': 0,
              'chunksByteIdentical': 0, 'chunksSemanticallyChecked': 0,
              'initialChunksMissing': 0, 'newChunks': 0, 'terrainAndContainerChanges': [],
              'entityInventoryChanges': [], 'worldMetadataFilesChanged': []}
    with zipfile.ZipFile(archive) as saved:
        manifest = json.loads(saved.read('BACKUP_MANIFEST.json'))['files']
        region_names = [n for n in manifest if n.startswith('world/') and n.endswith('.mca')]
        current = {p.relative_to(root).as_posix() for p in (root / 'world').rglob('*.mca')}
        if current != set(region_names):
            raise RuntimeError('Liste des fichiers de régions différente ; aucune génération attendue.')
        for name in region_names:
            path = root / name
            if hashlib.sha256(path.read_bytes()).hexdigest() == manifest[name]:
                report['regionFilesByteIdentical'] += 1
                continue
            old, new = chunks(saved.read(name)), chunks(path.read_bytes())
            report['regionFilesSemanticallyChecked'] += 1
            report['initialChunksMissing'] += len(old.keys() - new.keys())
            report['newChunks'] += len(new.keys() - old.keys())
            for index, before in old.items():
                if index not in new: continue
                if before == new[index]:
                    report['chunksByteIdentical'] += 1
                    continue
                left, right = decode(before), decode(new[index])
                report['chunksSemanticallyChecked'] += 1
                if '/region/' in name and not terrain_equal(left, right, defaults):
                    report['terrainAndContainerChanges'].append({'region': name, 'chunkIndex': index})
                if '/entities/' in name and entity_inventory(left) != entity_inventory(right):
                    report['entityInventoryChanges'].append({'region': name, 'chunkIndex': index})
        for name, expected in manifest.items():
            if name.startswith('world/') and not name.endswith('.mca'):
                path = root / name
                if not path.is_file(): raise RuntimeError('Fichier du monde manquant : ' + name)
                if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    report['worldMetadataFilesChanged'].append(name)
    report['passed'] = not any(report[k] for k in ('initialChunksMissing', 'newChunks',
                            'terrainAndContainerChanges', 'entityInventoryChanges'))
    return report
