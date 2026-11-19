"""Disponibilité et comparabilité des attributs SFTP ; aucun réseau."""
import hashlib
import io
from pathlib import Path
import stat
import sys
import types
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sftp_attributes import capture,compare
import minestrator_cold_backup as backup

def attr(*,flags=15,uid=1001,gid=1002,size=3,mtime=1,mode=stat.S_IFREG|0o755):
    return types.SimpleNamespace(_flags=flags,st_size=size,st_mtime=mtime,st_mode=mode,st_uid=uid,st_gid=gid)
class Guard:
    def check(self):pass
class Handle(io.BytesIO):
    def __init__(self,attributes,data=b'abc'):super().__init__(data);self.attributes=attributes
    def stat(self):return self.attributes
class Client:
    def __init__(self,attributes=None):self.attributes=attributes or attr()
    def lstat(self,name):return self.attributes
    def open(self,name,mode):
        if mode!='rb':raise AssertionError('Remote write')
        return Handle(self.attributes)

class AttributeTests(unittest.TestCase):
    def test_listing_omits_owners(self):
        a=capture(attr(flags=13,uid=None,gid=None));b=capture(attr());r=compare(a,b)
        self.assertTrue(r['accepted']);self.assertTrue(r['criticalVerified']);self.assertFalse(r['fullyComparable'])
        self.assertEqual(r['optionalStatus']['uid'],'expected_absent_not_comparable')
    def test_two_missing_not_verified(self):
        a=capture(attr(flags=13,uid=None,gid=None));r=compare(a,a,same_source=True)
        self.assertEqual(r['optionalStatus']['uid'],'both_absent_not_verified');self.assertNotIn('uid',r['verifiedFields'])
    def test_zero_is_available_value(self):
        a=capture(attr(uid=0,gid=0,size=0,mtime=0));r=compare(a,a)
        self.assertTrue(r['fullyComparable']);self.assertEqual(r['optionalStatus']['uid'],'verified_equal')
    def test_missing_not_zero(self):
        a=capture(attr(flags=13,uid=None,gid=None));b=capture(attr(uid=0,gid=0));r=compare(a,b)
        self.assertEqual(r['optionalStatus']['uid'],'expected_absent_not_comparable')
    def test_critical_missing_even_on_both_sides_fails(self):
        for key in ('st_size','st_mtime','st_mode'):
            a=attr();setattr(a,key,None);r=compare(capture(a),capture(a));self.assertFalse(r['accepted'])
    def test_flags_override_placeholder(self):
        a=capture(attr(flags=13,uid=0,gid=0));self.assertFalse(a['attributes']['uid']['available']);self.assertFalse(a['attributes']['uid']['wireDeclared'])
    def test_critical_changes_rejected(self):
        for change in ({'size':4},{'mtime':2},{'mode':stat.S_IFREG|0o644},{'mode':stat.S_IFDIR|0o755}):
            with self.subTest(change=change):self.assertFalse(compare(capture(attr()),capture(attr(**change)))['accepted'])
    def test_owner_changes_when_known_rejected(self):
        self.assertFalse(compare(capture(attr()),capture(attr(uid=0)))['accepted'])
        self.assertFalse(compare(capture(attr()),capture(attr(gid=0)))['accepted'])
    def test_availability_loss_same_source_rejected(self):
        self.assertFalse(compare(capture(attr()),capture(attr(flags=13,uid=None,gid=None)),same_source=True)['accepted'])
    def test_cross_source_owner_absence_not_invented(self):
        r=compare(capture(attr()),capture(attr(flags=13,uid=None,gid=None)))
        self.assertTrue(r['accepted']);self.assertFalse(r['fullyComparable']);self.assertEqual(r['optionalStatus']['gid'],'observed_absent_not_comparable')
    def test_unavailable_type_bits_rejected(self):
        a=capture(attr(mode=0o755));self.assertFalse(a['attributes']['type']['available']);self.assertFalse(compare(a,a)['accepted'])
    def test_read_uses_lstat_anchor_and_traces(self):
        listing=backup.metadata(attr(flags=13,uid=None,gid=None));events=[];anchors={}
        digest=backup.read_remote(Client(),'dummy',listing,Guard(),evidence=events.append,anchors=anchors)
        self.assertEqual(digest,hashlib.sha256(b'abc').hexdigest());self.assertEqual(anchors['dummy']['uid'],1001)
        self.assertEqual(events[0]['stage'],'lstat_before_vs_listdir');self.assertFalse(events[0]['comparison']['fullyComparable'])
        self.assertTrue(events[1]['comparison']['fullyComparable'])
    def test_second_pass_owner_change_rejected(self):
        listing=backup.metadata(attr(flags=13,uid=None,gid=None));anchors={}
        backup.read_remote(Client(),'dummy',listing,Guard(),anchors=anchors)
        with self.assertRaises(backup.Unsafe) as ctx:backup.read_remote(Client(attr(uid=0)),'dummy',listing,Guard(),anchors=anchors)
        self.assertEqual(ctx.exception.details['stage'],'lstat_before_vs_first_pass')
    def test_mismatch_details_without_console_secret(self):
        events=[]
        with self.assertRaises(backup.Unsafe) as ctx:backup.assert_same(attr(mtime=2),backup.metadata(attr()),name='private-name',stage='lstat_after',evidence=events.append)
        self.assertEqual(str(ctx.exception),'ConcurrentFileChange');self.assertEqual(ctx.exception.details['path'],'private-name')
        self.assertEqual(events[-1]['comparison']['differences'],['mtime'])
    def test_content_change_same_metadata_rejected(self):
        with self.assertRaisesRegex(backup.Unsafe,'RemoteHashChanged'):backup.assert_hash_same(hashlib.sha256(b'abd').hexdigest(),hashlib.sha256(b'abc').hexdigest(),name='dummy',stage='second_pass')
    def test_snapshot_missing_owners_not_claimed_verified(self):
        a=backup.metadata(attr(flags=13,uid=None,gid=None));events=[]
        backup.assert_tree_same({'files':{'dummy':a},'directories':{}},{'files':{'dummy':a},'directories':{}},stage='tree',evidence=events.append)
        self.assertIn('uid',events[0]['comparison']['unverifiedFields'])
    def test_tree_change_rejected(self):
        with self.assertRaisesRegex(backup.Unsafe,'RemoteTreeChanged'):backup.assert_tree_same({'files':{},'directories':{}},{'files':{'dummy':backup.metadata(attr())},'directories':{}},stage='tree')
    def test_inconsistent_flat_metadata_rejected(self):
        a=backup.metadata(attr());a['size']=7
        with self.assertRaisesRegex(backup.Unsafe,'AttributeRecordInconsistent'):backup.assert_same(attr(),a)
