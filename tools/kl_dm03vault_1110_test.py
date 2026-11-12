"""Off-game self-test of kl_dm03vault_1110 (2026-11-10): the pure helpers on synthetic inputs, the install.py round trip in a scratch copy. No game files."""
import hashlib, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_dm03vault_1110 as V

fails = []
BS = chr(92)


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ValueError:
        return True
    return False


# ---- door scale
t('a 60 cm host gives sx 0.5', V.host_width_sx([60.0]) == 0.5)
t('a 120 cm host gives sx 1.0', V.host_width_sx([120.0]) == 1.0)
t('two hosts 105 / 105 give sx 0.875', V.host_width_sx([105.0, 105.0]) == 0.875)

# ---- door targets by path
top, nums = 'KL_Interact!2', [4, 5]
fr, pb, ac = V.door_target_paths(top, nums)
want_fr = [V.R + top + BS + 'KL_Door_%d' % n + BS + 'KickableDoor_Proxy_Variation01Front_A_01' for n in nums]
t('door-target paths: 2 front proxies, 2 pathblockers, 2 actions, the expected strings', fr == want_fr and len(pb) == 2 and len(ac) == 2 and pb[0].endswith('KL_Door_4' + BS + 'KickDoor_Pathblocker_01') and ac[1].endswith('KL_Door_5' + BS + 'KickDoor_Action_01'))
fl, bk = V.timer_lists(top, nums)
t('Fuse = Boom + 2 proxies + 2 pathblockers; Backstop = the same without the Boom', fl == [V.R + V.VAULT + BS + 'Boom'] + fr + pb and bk == fr + pb)


class FakeSc:
    def __init__(self, paths, dup=()):
        self.p = {}
        for i, p in enumerate(paths):
            self.p.setdefault(p, []).append(i + 1)
        for d in dup:
            self.p[d].append(900)

    def resolve(self, p):
        return list(self.p.get(p, []))


allp = fr + pb + ac
sc = FakeSc(allp)
got = V.door_targets(sc, top, nums)
t('door_targets resolves by path: exactly 2 + 2 + 2 entries, node numbers from the paths', [len(got[k]) for k in ('front', 'pb', 'action')] == [2, 2, 2] and got['front'] == [allp.index(p) + 1 for p in fr])
t('a missing path is refused', raises(V.door_targets, FakeSc(allp[:-1]), top, nums))
t('a path naming two nodes is refused', raises(V.door_targets, FakeSc(allp, dup=[fr[0]]), top, nums))

# ---- loot: 7,000,000 stays, moved piles are top-level nodes
old = {792: 700000, 793: 640000, 794: 710000, 795: 650000, 796: 1030000, 797: 520000, 798: 520000, 799: 420000}
t('the 8 piles of the map sum to 5,190,000 and the map to 7,000,000 with the rest', sum(old.values()) == 5190000 and 5190000 + 4 * 440000 + 50000 == 7000000)
rest = {k: v for k, v in old.items() if k not in (797, 798, 799)}
new = V.split_amounts(rest, sum(old.values()) - 3 * V.LOOT_EACH)
t('split_amounts: sums to the target, multiples of 10,000, order kept', sum(new.values()) == 2190000 and all(v % 10000 == 0 for v in new.values()) and sorted(new, key=new.get) == sorted(rest, key=rest.get))
t('loot after the move: 3 x 1,000,000 + the rest = the old piles total, so the map stays 7,000,000', sum(new.values()) + 3 * V.LOOT_EACH == sum(old.values()) and sum(new.values()) + 3 * V.LOOT_EACH + 4 * 440000 + 50000 == V.LOOT_TOTAL)
t('split_amounts refuses a target that is not a multiple of the step', raises(V.split_amounts, rest, 2190001))
t('split_amounts refuses an empty / zero input', raises(V.split_amounts, {}, 10000) and raises(V.split_amounts, {1: 0}, 10000))
# world -> local: the pile (top-level in its room group chain 682 > 22 > 21, identity rotation) and a nested one
chain = [(0.0, 0.0, 0.0), (0.014, 0.0, 0.006), (0.0, 0.0, 0.0)]
loc = V.world_to_local((0.0, 241.3, -6620.0), chain)
t('world_to_local: subtracts the whole chain of offsets', abs(loc[0] + 0.014) < 1e-9 and loc[1] == 241.3 and abs(loc[2] + 6620.006) < 1e-9)
t('world_to_local with a deeper chain subtracts every level', V.world_to_local((10.0, 0.0, 0.0), chain + [(3.0, 0.0, 0.0)])[0] == 10.0 - 0.014 - 3.0)
t('the three moved piles are three distinct world places, all in the dock room (z > -6760)', len(set(V.LOOT_MOVE)) == 3 and all(-6758 < p[2] < -6130 for p in V.LOOT_MOVE))
t('the dock filter drops cells behind the swung leaves (z < DOCK_MIN_Z)', V.dock_filter([(0, 240, -6700), (0, 240, -6620), (0, 240, -6659.9)]) == [(0, 240, -6620), (0, 240, -6659.9)])

# ---- input pins
a, b = 'a81ede87c6798642ebf8261499762fd0', 'e8c06e13d5bc2182fe005a1bf2bae741'
t('a known input pair is accepted', 'backswat' in V.check_input((a, b), False))
t('the live doorfix pair is accepted', 'doorfix' in V.check_input(('8e23cbd308d0a6bea1e2661a939c9881', '2528e8f08e0b1f96ca76d3aa9b3aac18'), False))
t('a wrong input md5 is refused', raises(V.check_input, ('0' * 32, b), False))
t('a wrong bots md5 is refused', raises(V.check_input, (a, '0' * 32), False))
t('--accept-input takes an unknown pair', 'UNKNOWN' in V.check_input(('0' * 32, '1' * 32), True))
t('--loot L2 is refused (not built)', raises(V.stage, loot='L2'))
t('defaults: out dir under dm03vault_1110, tag, in dir the backswat stage', 'dm03vault_1110' in V.OUT and V.TAG == '.before-dm03vault_1110' and V.IN_DIR.endswith('dm03backswat_1110'))
t('the Arm box is pinned one-shot (f10 = -1), not every-edge', V.ARM_REARM == 0xFFFFFFFF)
t('the vault nodes live under their own top group, not a KL_Interact', V.VAULT == 'KL_Vault!1')

# ---- install.py round trip in a scratch copy
tmp = tempfile.mkdtemp(prefix='vault_t_')
here, game = os.path.join(tmp, 'stage'), os.path.join(tmp, 'game')
d = os.path.join(game, 'KLExpansion', 'Maps', 'DM03')
os.makedirs(here)
os.makedirs(d)
m5 = lambda b: hashlib.md5(b).hexdigest()
names = ['F03_Main.zip', 'F03_Main.bots.zip', 'F03_Main.bots.base.md5', 'KLJoin.ini', 'KLGuns.ini']
olds = {n: ('old ' + n).encode() * 50 for n in names}
news = {n: ('new ' + n).encode() * 70 for n in names}
for n in names:
    open(os.path.join(d, n), 'wb').write(olds[n])
    open(os.path.join(here, n), 'wb').write(news[n])
files = [(n, m5(olds[n]), m5(news[n])) for n in names]
open(os.path.join(here, 'install.py'), 'w').write(V.make_install(files, V.TAG, game))


def run(*args):
    r = subprocess.run([sys.executable, os.path.join(here, 'install.py'), '--game', game, '--skip-run-check'] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


snap = lambda: {n: open(os.path.join(d, n), 'rb').read() for n in sorted(os.listdir(d))}
before = snap()
rc, out = run('--dry')
t('install --dry writes nothing', rc == 0 and snap() == before)
rc, out = run()
t('install: every file is the staged one, backups next to them', rc == 0 and all(open(os.path.join(d, n), 'rb').read() == news[n] for n in names) and all(open(os.path.join(d, n + V.TAG), 'rb').read() == olds[n] for n in names))
rc2, out2 = run()
t('a second install is refused and changes nothing', rc2 != 0 and 'REFUSED' in out2 and all(open(os.path.join(d, n), 'rb').read() == news[n] for n in names))
rc, out = run('--undo')
after = snap()
t('undo is byte-exact (no backups left, originals back)', rc == 0 and after == before)
rc, out = run('--undo')
t('a second undo is refused', rc != 0 and 'REFUSED' in out)
open(os.path.join(d, 'F03_Main.zip'), 'wb').write(b'someone else')
rc, out = run()
t('a live file that is not the pinned input is refused (all or nothing)', rc != 0 and open(os.path.join(d, 'KLJoin.ini'), 'rb').read() == olds['KLJoin.ini'])

t('imports without the game folder (module-level GAME is only a path)', os.path.basename(V.GAME) != '' and 'kl_dm03vault_1110' in sys.modules)

print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
