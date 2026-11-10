"""Pure-logic self-test of kl_smartcops_1110 (no game files, no zips)."""
import os, sys, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_smartcops_1110 as S

fails = []
def chk(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: fails.append(name)

mids = [(0, 0, 0), (300, 0, 0), (0, 500, 0), (900, 0, 0)]
chk('near_count height + radius', S.near_count((0, 0, 0), mids) == 2 and S.near_count((900, 0, 0), mids) == 1)
posts = [dict(pos=(0, 0, 0)), dict(pos=(5000, 0, 0))]
chk('weak_posts', [p['pos'] for p in S.weak_posts(posts, mids)] == [(0, 0, 0)[0:3]] or len(S.weak_posts(posts, mids)) == 1)
chk('weak_posts need=1', len(S.weak_posts(posts, mids, need=1)) == 1 and S.weak_posts(posts, mids, need=1)[0]['pos'] == (5000, 0, 0))
m = S.disc_mask([(0, 0, 0), (2000, 0, 0), (0, 900, 0)], [True, True, True], [(100, 0, 0)], 700)
chk('disc_mask', m == [True, False, False])
chk('disc_mask keeps ok=False', S.disc_mask([(0, 0, 0)], [False], [(0, 0, 0)]) == [False])
chk('assign_posts wraps', S.assign_posts(5, ['a', 'b']) == ['a', 'b', 'a', 'b', 'a'] and S.assign_posts(2, []) == [None, None])
chk('swap_entry', S.swap_entry(['X/A', 'x/a', 'B'], 'x/a', 'N') == (['N', 'N', 'B'], 2))
chk('parse_holder', S.parse_holder('ZBoxPrimitive + TriggerDelay2 (ZTriggerDelay2)', 'ZTriggerDelay2[4]') == ('TriggerDelay2', 4) and S.parse_holder('x', 'y') is None)
chk('budget', S.budget_ok(71, 32) and not S.budget_ok(99, 32, add_a=1) and not S.budget_ok(71, 55, add_s=1))
chk('ffcover / cap', S.ffcover_ok(1) and not S.ffcover_ok(2) and S.cap_ok(4500) and not S.cap_ok(4501))
try:
    S.parts_ok('cover,bogus'); chk('parts_ok rejects', False)
except SystemExit:
    chk('parts_ok rejects', S.parts_ok('cover,runcover') == ['cover', 'runcover'])
src = S.render_install([('a.zip', 'x' * 32, 'y' * 32)], r'C:\g', map_='DM01')
try:
    compile(src, 'install.py', 'exec'); chk('install renders and compiles', '@' not in src.replace('@echo', ''))
except SyntaxError as e:
    chk('install renders and compiles (%s)' % e, False)
print('RESULT: %s' % ('FAIL %s' % fails if fails else 'PASS'))
sys.exit(1 if fails else 0)
