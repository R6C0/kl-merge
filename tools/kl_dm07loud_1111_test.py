"""Self-test of tools/kl_dm07loud_1111.py: record selection, byte-range patch, and the generated install.py on a tiny fake game folder
(install, 2nd install refused, wrong pin refused, undo byte-exact). Prints 'PASS' / exits 1."""
import hashlib, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_dm07loud_1111 as T

bad = []


def check(c, m):
    if not c:
        bad.append(m)


recs = [{'n': 'SFX/Impacts/Shatter/Metal_Squeak/Metal_Squeak_002.wav', 'off': 8, 'size': 8, 'fmt': 0x11},
        {'n': 'SFX/Impacts/Shatter/Metal_Squeak/Metal_Squeak_003.wav', 'off': 24, 'size': 4, 'fmt': 0x11 | 0x00800000},     # streamed: skipped
        {'n': 'SFX/Impacts/Concrete_Break/Concrete_Burst_01.wav', 'off': 16, 'size': 8, 'fmt': 0x11},
        {'n': 'SFX/Weapons/Gun.wav', 'off': 0, 'size': 8, 'fmt': 1}]
check(T.select(recs, T.CREAK) == [(8, 8, recs[0]['n'])], 'creak selection')
check([r[0] for r in T.select(recs, T.IMPACTS)] == [8, 16], 'impacts selection')
live, src = bytes([1]) * 32, bytes([2]) * 32
p = T.patch(live, src, T.select(recs, T.CREAK))
check(p[8:16] == src[8:16] and p[:8] == live[:8] and p[16:] == live[16:], 'patch touches only the range')
try:
    T.patch(live, src[:31], []); check(False, 'size mismatch must raise')
except ValueError:
    pass
try:
    T.patch(live, src, [(30, 8, 'x')]); check(False, 'out-of-range must raise')
except ValueError:
    pass

with tempfile.TemporaryDirectory() as td:
    game = os.path.join(td, 'game'); d = os.path.join(game, T.MAPDIR); os.makedirs(d)
    kit = os.path.join(td, 'kit'); os.makedirs(kit)
    open(os.path.join(d, 'F06_Main.WAV'), 'wb').write(live)
    open(os.path.join(d, 'F06_Main.WHD'), 'wb').write(b'whd')
    sc, si = T.patch(live, src, T.select(recs, T.CREAK)), T.patch(live, src, T.select(recs, T.IMPACTS))
    m = lambda b: hashlib.md5(b).hexdigest()
    staged = {'creak': ('c.WAV', m(sc)), 'impacts': ('i.WAV', m(si))}
    open(os.path.join(kit, 'c.WAV'), 'wb').write(sc); open(os.path.join(kit, 'i.WAV'), 'wb').write(si)
    open(os.path.join(kit, 'install.py'), 'w').write(T.render_install(m(live), m(b'whd'), staged))

    def run(*a):
        r = subprocess.run([sys.executable, '-I', os.path.join(kit, 'install.py'), '--game', game, '--skip-run-check'] + list(a), capture_output=True, text=True)
        return r.returncode, r.stdout
    cur = lambda: open(os.path.join(d, 'F06_Main.WAV'), 'rb').read()
    rc, _ = run('--dry'); check(rc == 0 and cur() == live, 'dry writes nothing')
    rc, _ = run('--variant', 'nope'); check(rc == 1, 'unknown variant refused')
    rc, o = run('--variant', 'impacts'); check(rc == 0 and cur() == si and os.path.isfile(os.path.join(d, 'F06_Main.WAV.before-dm07loud_1111')), 'install ' + o)
    rc, _ = run('--variant', 'creak'); check(rc == 1 and cur() == si, '2nd install refused')
    rc, _ = run('--undo'); check(rc == 0 and cur() == live and not os.path.exists(os.path.join(d, 'F06_Main.WAV.before-dm07loud_1111')), 'undo byte-exact')
    rc, _ = run('--undo'); check(rc == 1, 'undo with nothing installed refused')
    open(os.path.join(d, 'F06_Main.WAV'), 'wb').write(b'x' * 32)
    rc, _ = run(); check(rc == 1 and cur() == b'x' * 32, 'changed live WAV refused')

print('FAIL: ' + '; '.join(bad) if bad else 'PASS')
sys.exit(1 if bad else 0)
