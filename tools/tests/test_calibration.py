import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from calibration import mugen, native
from calibration.extract import discover, extract
from calibration.pipeline import Transaction
from calibration.validate import Fighter, box_world, overlaps, contact, execute, command_matches, validate_tables


def controller(kind, fields):
    return {'type': kind, 'fields': [{'key': k, 'expression': v} for k, v in [('type', kind), *fields]]}


class Expressions(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(mugen.evaluate('floor((ifelse(var(6),9,7)-var(21))*fvar(7))',
                                        {'var(6)': 0, 'var(21)': 1, 'fvar(7)': .5}), 3)
        self.assertEqual(mugen.evaluate('-7 / 2'), -3)
        self.assertEqual(mugen.evaluate('-7 % 2'), -1)
        self.assertEqual(mugen.evaluate('7 / 2.0'), 3.5)
        self.assertEqual(mugen.evaluate('2 + 3*4'), 14)

    def test_no_invented_values(self):
        for expr in ('var(6)', 'floor(var(7)*10)', '6-ifelse(var(40),.5,0)',
                     'Helper(40000),var(0)', 'time = [0,4]', 'var(2) := 1',
                     '__import__("os")', '1/0', '2 ** 100000000', 'foo.bar'):
            with self.subTest(expr=expr), self.assertRaises(mugen.Unsupported): mugen.evaluate(expr)

    def test_comparisons(self):
        self.assertEqual(mugen.evaluate('time = 3 && !ctrl', {'time': 3, 'ctrl': 0}), 1)
        self.assertEqual(mugen.evaluate('time != 3 || ctrl', {'time': 3, 'ctrl': 0}), 0)
        self.assertEqual(mugen.evaluate('AnimElemTime(2) >= 0', {'animelemtime(2)': 0}), 1)

    def test_grouping(self):
        c = controller('null', [('triggerall', 'power >= 100'), ('trigger1', 'time = 2'),
                                ('trigger1', 'ctrl'), ('trigger2', 'time = 5')])
        self.assertFalse(mugen.triggers(c, {'power': 100, 'time': 2, 'ctrl': 0}))
        self.assertTrue(mugen.triggers(c, {'power': 100, 'time': 5, 'ctrl': 0}))
        self.assertFalse(mugen.triggers(c, {'power': 0, 'time': 5, 'ctrl': 1}))

    def test_commas(self):
        self.assertEqual(mugen.split_values('floor(ifelse(var(6),9,7)), 0'), ['floor(ifelse(var(6),9,7))', '0'])


class Parsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def file(self, name, text):
        p = self.root / name; p.write_text(text); return p

    def test_controller_enclosing_state_and_repeated_triggers(self):
        p = self.file('states.st7', '[Statedef 200]\nanim=200\n[State 999, copied label]\ntype=HitDef\n'
                      'trigger1=time=0\ntrigger1=ctrl\ndamage=5,0\n[Statedef 200]\nanim=201\n')
        s, dup, _, _ = mugen.states([p])
        self.assertEqual(s['200']['controllers'][0]['source']['line'], 3)
        self.assertEqual(len(s['200']['controllers'][0]['fields']), 4)
        self.assertEqual(dup[0]['state'], 200)

    def test_air_defaults_clear_and_hold(self):
        p = self.file('a.air', '[Begin Action 200]\nClsn2Default: 1\nClsn2[0]=-5,-10,5,0\n'
                      'Clsn1: 1\nClsn1[0]=5,-8,12,0\n0,0,0,0,3\n'
                      'Clsn2: 0\n0,1,0,0,0\nLoopStart\n0,2,0,0,-1,H\n')
        a = mugen.air(p)['200']; f = a['frames']
        self.assertEqual(f[0]['hitboxes'], [[5,-8,12,0]])
        self.assertEqual(f[1]['hurtboxes'], [])
        self.assertEqual(f[2]['hurtboxes'], [[-5,-10,5,0]])
        self.assertEqual(f[2]['hitboxes'], [])
        self.assertEqual(a['loopstart'], 2)
        self.assertIsNone(mugen.timeline(a)['duration'])
        self.assertIsNone(mugen.timeline(a)['startup'])

    def test_finite_air_duration_and_boxes(self):
        p = self.file('a.air', '[begin action 1]\n0,0,0,0,4\nclsn1:1\nclsn1[0]=0,0,3,3\n'
                      '0,1,0,0,2\n0,2,0,0,9\n')
        t = mugen.timeline(mugen.air(p)['1'])
        self.assertEqual(t['duration'], 15)
        self.assertEqual(t['box_windows'], [{'start':4, 'end':6, 'element':2}])

    def test_def_references_and_alias(self):
        self.file('C.sff', ''); self.file('C.air', '')
        self.file('Hero-KOF98.def', '[Info]\nname="Hero"\n[Files]\nsprite=c.sff\nanim=C.air\nst8=Other.st8\n')
        cfg = {'hero': {'sff': str(self.root / 'C.sff')}}
        d = discover(self.root, cfg)[0]
        self.assertEqual(d['native'], 'hero')
        self.assertTrue(d['files']['st8'].endswith('Other.st8'))

    def test_cache_invalidation(self):
        dpath = self.file('x.def', '[Info]\nname="X"\n[Files]\nanim=x.air\nst9=x.st9\n')
        self.file('x.air', '[Begin Action 1]\n0,0,0,0,2\n')
        st = self.file('x.st9', '[Statedef 1]\nanim=1\n')
        d = mugen.definition(dpath); d.update(native=None, id='x')
        a, hit = extract(d, self.root / 'cache'); self.assertFalse(hit)
        _, hit = extract(d, self.root / 'cache'); self.assertTrue(hit)
        st.write_text('[Statedef 2]\nanim=1\n')
        a, hit = extract(d, self.root / 'cache'); self.assertFalse(hit)
        self.assertIn('2', a['states'])

    def test_binary_indices(self):
        import struct
        data = bytearray(100)
        data[:12] = b'ElecbyteSpr\0'; data[15] = 2
        struct.pack_into('<II', data, 36, 64, 1)
        struct.pack_into('<hhHHhhH', data, 64, 200, 0, 32, 48, 16, 47, 0)
        p = self.root / 'x.sff'; p.write_bytes(data)
        row = mugen.binary_metadata(p, 'sprite')['entries'][0]
        self.assertEqual((row['width'], row['axis']), (32, [16,47]))
        data = bytearray(60); data[:12] = b'ElecbyteSnd\0'
        struct.pack_into('<II', data, 16, 1, 32)
        struct.pack_into('<IIII', data, 32, 0, 4, 3, 2)
        p = self.root / 'x.snd'; p.write_bytes(data)
        self.assertEqual(mugen.binary_metadata(p, 'sound')['entries'][0]['group'], 3)


class Simulation(unittest.TestCase):
    def test_fixed_point_distance_and_projectile_trajectory(self):
        p = Fighter(vx=384, vy=-512)
        for _ in range(4): p.advance(gravity=128)
        self.assertEqual((p.x, p.y, p.vy), (1536, -1280, 0))
        self.assertEqual(native.convert(-1.5, 'fixed', {'coord_scale': 1}), -384)

    def test_mirror_and_two_fighter_collision(self):
        a = box_world([5,-8,20,0], 50, 0, -1)
        self.assertEqual(a, [30,-8,45,0])
        self.assertTrue(overlaps(a, box_world([-5,-10,5,0], 40)))
        self.assertFalse(overlaps(a, box_world([-5,-10,5,0], 60)))
        self.assertEqual(box_world([-10,-20,10,0], scale=.85), [-8,-17,8,0])

    def test_damage_pushback_hitstun_and_guard(self):
        h = {'damage': 30, 'gdamage': 5, 'hittime': 12, 'gvx': 512, 'grvx': 256,
             'gvy': -128, 'p1pause': 3, 'p1gpause': 2, 'p2pause': 4}
        a, b = Fighter(facing=-1), Fighter()
        contact(a, b, h)
        self.assertEqual((b.hp,b.stun,b.vx,b.vy,a.pause), (170,12,-512,-128,3))
        b.hp = 3; contact(a,b,h,True)
        self.assertEqual((b.hp,b.stun,b.vx,b.vy,a.pause), (1,12,-256,0,2))
        before = b.x; b.advance(); self.assertEqual(b.x, before)

    def test_command_window_and_buffer(self):
        events = [(1,'D'), (3,'DF'), (5,'F+x')]
        self.assertTrue(command_matches(events, ['D','DF','F+x'], 5, 6, 2))
        self.assertFalse(command_matches(events, ['D','DF','F+x'], 3, 5))
        self.assertFalse(command_matches(events, ['D','DF','F+x'], 5, 7, 2))
        with self.assertRaises(mugen.Unsupported): command_matches(events, ['~30B','F+x'], 30, 5)

    def test_controller_chain_cancel_power_and_recovery(self):
        f = Fighter(power=1000, time=3)
        c = controller('changestate', [('triggerall','power >= 1000'), ('trigger1','movehit && command = "qcf_x"'), ('value','1000'), ('ctrl','0')])
        self.assertFalse(execute(c, f, {'movehit':0, 'command':'qcf_x'}))
        self.assertTrue(execute(c, f, {'movehit':1, 'command':'qcf_x'}))
        self.assertEqual((f.state, f.time), (1000,0))
        execute(controller('poweradd',[('trigger1','time=0'),('value','-1000')]), f)
        self.assertEqual(f.power,0)
        execute(controller('velset',[('trigger1','1'),('x','1.5'),('y','-2')]),f)
        self.assertEqual((f.vx,f.vy),(384,-512))
        execute(controller('varset',[('trigger1','1'),('var(1)','5')]),f)
        execute(controller('varadd',[('trigger1','1'),('var(1)','2')]),f)
        self.assertEqual(f.variables['var(1)'],7)
        execute(controller('ctrlset',[('trigger1','animtime=0'),('value','1')]),f, {'animtime':0})
        self.assertEqual(f.ctrl,1)
        with self.assertRaises(mugen.Unsupported): execute(controller('helper',[('trigger1','1')]),f)


class Safety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_transaction_rollback_preserves_prior_edits(self):
        p = self.root / 'user.txt'; p.write_text('already edited')
        tx = Transaction(self.root, self.root / 'journal')
        tx.add('user.txt', b'calibrated'); tx.add('new.txt', b'new')
        tx.prepare(); self.assertEqual(p.read_text(), 'already edited')
        self.assertTrue((tx.journal/'changes.patch').exists())
        tx.commit(); self.assertEqual(p.read_text(), 'calibrated')
        Transaction.rollback(self.root, tx.journal)
        self.assertEqual(p.read_text(), 'already edited')
        self.assertFalse((self.root/'new.txt').exists())

    def test_rollback_refuses_subsequent_changes(self):
        tx = Transaction(self.root, self.root/'journal'); tx.add('x', b'generated'); tx.commit()
        (self.root/'x').write_text('manual afterwards')
        with self.assertRaises(ValueError): Transaction.rollback(self.root, tx.journal)
        self.assertEqual((self.root/'x').read_text(), 'manual afterwards')

    def test_partial_commit_rollback_and_concurrency(self):
        tx = Transaction(self.root, self.root/'journal')
        (self.root/'a').write_text('before a'); (self.root/'b').write_text('before b')
        tx.add('a', b'after a'); tx.add('b', b'after b')
        (self.root/'b').write_text('concurrent')
        with self.assertRaises(ValueError): tx.commit()
        self.assertEqual((self.root/'a').read_text(), 'before a')
        self.assertEqual((self.root/'b').read_text(), 'concurrent')

    def test_idempotence(self):
        (self.root/'x').write_bytes(b'data')
        tx = Transaction(self.root, self.root/'journal'); tx.add('x', b'data')
        self.assertEqual(tx.entries, [])

    def test_stale_profile(self):
        p = self.root/'input.cns'; p.write_text('source')
        profile = {'schema':1, 'config_hash':native.config_hash({}), 'inputs':{'input.cns':mugen.sha(p)}, 'corrections':[]}
        d = self.root/native.PROFILE_DIR; d.mkdir(parents=True)
        (d/'kyo.json').write_text(json.dumps(profile))
        self.assertIsNotNone(native.read_profile(self.root, 'kyo', {}))
        p.write_text('changed')
        with self.assertRaises(ValueError): native.read_profile(self.root, 'kyo', {})

    def test_out_of_range_is_not_saturated(self):
        with self.assertRaises(mugen.Unsupported): native.convert(2.5, 'integer', {})
        self.assertEqual(native.convert(0, 'magnitude', {}), 0)

    def test_victim_pause_requires_custom_victim_state(self):
        self.assertFalse(native.runtime_supported('p2pause', {'p2state': 0xFF}))
        self.assertTrue(native.runtime_supported('p2pause', {'p2state': 12}))
        self.assertTrue(native.runtime_supported('avy', {'p2state': 0xFF}))

    def test_fall_calibration_applies_to_hitdef_flags(self):
        self.assertEqual(native.convert(1, 'integer', {}), 1)
        self.assertTrue(native.runtime_supported('fall', {}))
        cfg = {}
        profile = {
            'schema': 1,
            'config_hash': native.config_hash(cfg),
            'inputs': {},
            'corrections': [{'kind': 'combat', 'state': 1110, 'key': 'fall',
                             'before': 0, 'after': 1, 'confidence': 'ALTA'}],
        }
        path = self.root / native.PROFILE_DIR / 'kyo.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(profile))
        moves = {1110: {'fall': 0}}
        native.apply_profile(self.root, 'kyo', cfg, moves, {})
        self.assertEqual(moves[1110]['fall'], 1)


if __name__ == '__main__': unittest.main()
