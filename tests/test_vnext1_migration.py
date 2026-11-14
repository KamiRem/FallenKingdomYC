import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'deployment'));sys.path.insert(0,str(ROOT/'scripts'))
import territory_migration as migration
from map_v21_tool import initial


def state():
    text='schema: 1\nstarted: false\nday: 0\nunknown: conserver\nnative:\n  TeamManager:\n'
    for team,x,z in [('Rouge',-240,-240),('Bleue',200,-200),('Verte',-200,240),('Jaune',280,200)]:
        text+=f'    {team}:\n      Base:\n        Radius: 80\n        Center:\n          World: world\n          X: {x}\n          Y: 70\n          Z: {z}\n'
    text+='spawns:\n'
    for team,x,z in [('Rouge',-240,-240),('Bleue',200,-200),('Verte',-200,240),('Jaune',280,200)]:text+=f'  {team}:\n    world: world\n    x: {x+.5}\n    y: 70\n    z: {z+.5}\n'
    return text


class VNext1MigrationTests(unittest.TestCase):
    def test_radius_half_is_quarter_geometric_area_and_centers_do_not_move(self):
        original=state();changed,report=migration.migrate(original)
        self.assertTrue(report['passed']);self.assertIn('unknown: conserver',changed)
        for item in report['territories']:
            self.assertEqual(6400,item['geometricAreaAfter']);self.assertEqual(25600,item['geometricAreaBefore']);self.assertEqual(6561,item['blockColumnsAfter'])
            for key in ('X','Y','Z'):self.assertEqual(migration.get(original,'native','TeamManager',item['team'],'Base','Center',key),migration.get(changed,'native','TeamManager',item['team'],'Base','Center',key))
    def test_objective_outside_new_bounds_is_refused_without_a_relocation(self):
        original=state()+'objectives:\n  Rouge:\n    world: world\n    x: -165\n    y: 72\n    z: -240\n'
        self.assertFalse(migration.plan(original)['passed'])
        with self.assertRaises(RuntimeError):migration.migrate(original)
    def test_objective_at_edge_requires_room_margin(self):
        original=state()+'objectives:\n  Rouge:\n    world: world\n    x: -202\n    y: 72\n    z: -240\n'
        self.assertFalse(migration.plan(original)['passed'])
    def test_idempotence_and_future_schema_refusal(self):
        changed,_=migration.migrate(state());self.assertEqual(changed,migration.migrate(changed)[0])
        with self.assertRaises(RuntimeError):migration.migrate(state().replace('schema: 1','schema: 2'))
    def test_played_archive_and_existing_profiles_never_become_cavern_inputs(self):
        initial(state(),[])
        for text,names in [(state().replace('started: false','started: true'),[]),(state()+"roster:\n  ancien: valeur\n",[]),(state(),['world/players/data/player.dat'])]:
            with self.assertRaises(RuntimeError):initial(text,names)


if __name__=='__main__':unittest.main()
