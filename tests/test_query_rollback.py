"""Contrôles locaux des sockets et de la conservation d'inventaires."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from minestrator_rollback_local import verify_listeners
from rollback_integrity import inventory_records,compare

class RollbackGuards(unittest.TestCase):
    def network(self,address='127.0.0.1',udp='127.0.0.1',remote='0.0.0.0'):
        return {'tcp':[{'state':'Listen','localAddress':address,'localPort':22880,'remoteAddress':remote}], 'udp':[{'LocalAddress':udp,'LocalPort':22880}]}
    def test_tcp_and_query_loopback_are_accepted(self):
        self.assertEqual(1,len(verify_listeners(self.network())))
        self.assertEqual(1,len(verify_listeners(self.network(address='::1',udp='::ffff:127.0.0.1'))))
    def test_wildcard_tcp_or_udp_or_host_connection_is_rejected(self):
        for data in (self.network(address='0.0.0.0'),self.network(udp='0.0.0.0'),self.network(udp='::'),self.network(udp='::ffff:0.0.0.0'),self.network(udp='::ffff:91.197.6.72'),self.network(remote='91.197.6.72'),self.network(remote='::ffff:91.197.6.72')):
            with self.assertRaises(RuntimeError):verify_listeners(data)
    def test_inventory_comparison_ignores_runtime_counters_but_keeps_items(self):
        a={'InhabitedTime':1,'block_entities':[{'Items':[{'id':'minecraft:bread','count':7}]}]}
        b={'InhabitedTime':80,'block_entities':[{'Items':[{'count':7,'id':'minecraft:bread'}]}]}
        self.assertEqual(inventory_records(a),inventory_records(b))
        b['block_entities'][0]['Items'][0]['count']=6
        self.assertNotEqual(inventory_records(a),inventory_records(b))
    def test_unconsumed_loot_tables_and_multiplicity_are_protected(self):
        a={'block_entities':[{'LootTable':'minecraft:chests/dungeon','LootTableSeed':42}]}
        b={'block_entities':[{'LootTable':'minecraft:chests/dungeon','LootTableSeed':43}]}
        self.assertNotEqual(inventory_records(a),inventory_records(b))
        self.assertNotEqual(inventory_records([a,a]),inventory_records([a]))
    def test_chunk_removal_and_inventory_loss_are_critical(self):
        before={'regions':{'r':[1,2]},'inventoriesAndLoot':{'r:1':{'hash':1}}}
        self.assertTrue(compare(before,before)['inventoriesAndLootPreserved'])
        for after in ({**before,'regions':{'r':[1]}},{**before,'inventoriesAndLoot':{}}):
            with self.assertRaises(RuntimeError):compare(before,after)

if __name__=='__main__':unittest.main()
