"""Lecture seule des régions, inventaires et butins pour la recette de rollback."""
from collections import Counter
import gzip
import hashlib
from pathlib import Path
from world_integrity import chunks, decode, canonical
from map_reader import nbt

def inventory_records(value):
    """Empreintes des inventaires non vides et tables non consommées."""
    found=Counter()
    def walk(data):
        if isinstance(data,dict):
            for key,item in data.items():
                if key.lower() in {'inventory','items','handitems','armoritems','equipment','saddleitem','loottable','loot_table','loottableseed','loot_table_seed'} and item:
                    found[hashlib.sha256(canonical({key:item}).encode()).hexdigest()]+=1
                else:walk(item)
        elif isinstance(data,list):
            for item in data:walk(item)
    walk(value)
    return dict(sorted(found.items()))

def snapshot(root: Path):
    regions={};records={};nbt_count=0
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        name=path.relative_to(root).as_posix()
        if not name.startswith(('world/','world_nether/','world_the_end/')):continue
        if path.suffix=='.mca':
            entries=chunks(path.read_bytes());regions[name]=sorted(entries)
            for index,value in entries.items():
                data=inventory_records(decode(value))
                if data:records[name+':'+str(index)]=data
        elif path.suffix=='.dat' or name.endswith('.dat_old'):
            data=path.read_bytes();data=gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data
            data=inventory_records(nbt(data));nbt_count+=1
            if data:records[name]=data
    return {'regions':regions,'inventoriesAndLoot':records,'nbtFilesDecoded':nbt_count}

def compare(before,after):
    if before['regions']!=after['regions']:raise RuntimeError('Régions ou chunks ajoutés/supprimés pendant le rollback')
    if before['inventoriesAndLoot']!=after['inventoriesAndLoot']:raise RuntimeError('Inventaires ou tables de butin différents après démarrage')
    return {'worldRegionFilesCompared':len(before['regions']),'worldChunksCompared':sum(len(v) for v in before['regions'].values()),'inventoryAndLootLocationsCompared':len(before['inventoriesAndLoot']),'inventoriesAndLootPreserved':True,'noRegionOrChunkRemovedOrAdded':True}
