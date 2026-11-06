"""Off-game self-test of kl_lastcall_chain_1106 (fast: tiny fake files, no game folder, no 100 MB zips)."""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_lastcall_chain_1106 as C
import kl_club_doors_1106 as D
import kl_club_outro_1106 as O
import kl_club_helicam_1106 as H

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


def put(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)


def run(st, *args):
    r = subprocess.run([sys.executable, os.path.join(st, 'install.py'), '--skip-run-check', '--min-free-mb', '0'] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout


# cam sets
t('cam none = no helicam', C.cam_params('none') is None)
t('cam 2a = f5 700, f6 -500, heli ShatterGeom', C.cam_params('2a') == ('A', 700.0, -500.0, H.AIM_B) and 'ShatterGeom' in H.AIM_B)
t('cam 2b = f5 -450, f6 100, EscCameraLAST', C.cam_params('2b') == ('A', -450.0, 100.0, H.AIM_A))
t('cam 2c = fixed eye CamPos01 (variant F) + the outro climb route', C.cam_params('2c') == ('F', None, None, H.AIM_F) and H.AIM_F.endswith('!CamPos01')
  and len(O.ROUTE_2C) == 5)
t('2c outro stage name differs from the plain outro stage', C.out_name('outro', '2c', 'a' * 32, C.MAPDIR) != C.out_name('outro', '2a', 'a' * 32, C.MAPDIR))
t('2c chain name', C.out_name('chain', '2c', 'a' * 32, C.MAPDIR).startswith('lcchain_2c_live_aaaaaaaa'))
t('cam 2d = variant D (LookFromPosFA, heli group) + the 2c climb route', C.cam_params('2d') == ('D', None, None, H.AIM_D) and '2d' in C.ROUTE_CAMS and '2c' in C.ROUTE_CAMS)
t('2d outro/chain names', C.out_name('outro', '2d', 'a' * 32, C.MAPDIR) == 'lcoutro2d_live_aaaaaaaa' and C.out_name('chain', '2d', 'a' * 32, C.MAPDIR).startswith('lcchain_2d_live_'))
t('2a/2b/2c unchanged', C.cam_params('2c') == ('F', None, None, H.AIM_F) and C.cam_params('2a')[0] == 'A' and '2a' not in C.ROUTE_CAMS)
try:
    C.cam_params('3'); t('unknown cam refused', False)
except ValueError:
    t('unknown cam refused', True)

# the allow= hooks of the pass tools
h = 'ab' * 16
t('doors allowed(): pin and allow prefixes only', D.allowed(D.LIVE_PIN) and D.allowed(h, [h]) and D.allowed(h, [h[:8]]) and not D.allowed(h) and not D.allowed(h, [h[:6]]) and not D.allowed(h, ['']))
for mod, nm, fn in ((O, 'outro', lambda d, o, a: O.stage(o, d, allow=a)), (H, 'helicam', lambda d, o, a: H.stage(o, d, allow=a))):
    with tempfile.TemporaryDirectory() as d:
        put(os.path.join(d, 'in', 'F01_Main.zip'), b'not a zip')
        import hashlib
        hh = hashlib.md5(b'not a zip').hexdigest()
        try:
            fn(os.path.join(d, 'in'), os.path.join(d, 'out'), [])
            t('%s refuses an unknown md5 without allow' % nm, False)
        except ValueError as e:
            t('%s refuses an unknown md5 without allow' % nm, 'refusing' in str(e))
        try:
            fn(os.path.join(d, 'in'), os.path.join(d, 'out'), [hh])
            t('%s allow= lets the md5 through' % nm, False)
        except Exception as e:                     # passes the md5 gate, then fails on the fake zip: that is the point
            t('%s allow= lets the md5 through' % nm, 'refusing' not in str(e))

# a pass that cannot find its edit REFUSES with its name, and leaves no output
with tempfile.TemporaryDirectory() as d:
    ind = os.path.join(d, 'in')
    for n in C.FILES5:
        put(os.path.join(ind, n), b'fake ' + n.encode())
    live = C.read_live(ind)
    t('read_live reads 5 md5s', list(live) == list(C.FILES5) and all(len(v) == 32 for v in live.values()))
    os.remove(os.path.join(ind, 'KLGuns.ini'))
    try:
        C.read_live(ind); t('read_live refuses a missing file', False)
    except C.Refused:
        t('read_live refuses a missing file', True)
    put(os.path.join(ind, 'KLGuns.ini'), b'fake KLGuns.ini')
    for p in C.PASSES:
        out = os.path.join(d, 'out_' + p)
        try:
            C.stage_single(p, ind, out, cam='2a', log=lambda *a: None)
            t('single %s refuses a fake zip' % p, False)
        except C.Refused as e:
            t('single %s refuses a fake zip, names the pass, leaves nothing' % p, ('pass ' + p) in str(e) and not os.path.exists(out))
    out = os.path.join(d, 'chain')
    try:
        C.stage_chain(ind, out, cam='2a', log=lambda *a: None)
        t('chain refuses a fake zip', False)
    except C.Refused as e:
        t('chain refuses a fake zip and leaves nothing', 'pass doors' in str(e) and not os.path.exists(out))
    try:
        C.stage_single('doors', ind, os.path.join(C.GAME, 'x'), log=lambda *a: None)
        t('a stage inside the game folder is refused', False)
    except C.Refused:
        t('a stage inside the game folder is refused', True)
    # names
    t('out names carry the first 8 of the zip md5', C.out_name('doors', '2a', 'e6d2f73e' + '0' * 24, C.MAPDIR) == 'lcdoors_live_e6d2f73e'
      and C.out_name('helicam', '2b', 'e6d2f73e' + '0' * 24, C.MAPDIR) == 'lcoutcam2b_live_e6d2f73e'
      and C.out_name('chain', 'none', 'e6d2f73e' + '0' * 24, C.MAPDIR) == 'lcchain_nocam_live_e6d2f73e')

import kl_club_doors_1106 as _D
t('chain out name carries the doors subset only when given', C.out_name('chain', '2a', 'e6d2f73e' + '0' * 24, C.MAPDIR, _D.select('B01,A02')) == 'lcchain_2a_dB01-A02_live_e6d2f73e'
  and C.out_name('chain', '2a', 'e6d2f73e' + '0' * 24, C.MAPDIR) == 'lcchain_2a_live_e6d2f73e')
try:
    C.stage_chain(doors='X9', root=os.path.join(tempfile.gettempdir(), 'klchain_nowhere'), log=lambda *a: None)
    t('chain refuses an unknown door name', False)
except C.Refused as e:
    t('chain refuses an unknown door name', '--doors' in str(e))
try:
    C.stage_chain(doors='B01', only=['outro'], root=os.path.join(tempfile.gettempdir(), 'klchain_nowhere'), log=lambda *a: None)
    t('chain refuses --doors without the doors pass', False)
except C.Refused as e:
    t('chain refuses --doors without the doors pass', 'doors pass' in str(e))

# the generated installer: pins, install, undo, all-or-nothing, never overwrites a backup
with tempfile.TemporaryDirectory() as d:
    st, game = os.path.join(d, 'st'), os.path.join(d, 'game')
    md = os.path.join(game, 'KLExpansion', 'Maps', 'DM05A')
    old = {n: b'old ' + n.encode() for n in C.FILES5}
    new = dict(old)
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5', 'KLJoin.ini'):      # KLGuns.ini stays unchanged
        new[n] = b'NEW ' + n.encode()
    import hashlib
    m = lambda b: hashlib.md5(b).hexdigest()
    for n in C.FILES5:
        put(os.path.join(md, n), old[n])
        put(os.path.join(st, n), new[n])
    files = {n: (m(old[n]), m(new[n])) for n in C.FILES5}
    C.write_install(st, files, ['doors', 'outro'])
    src = open(os.path.join(st, 'install.py')).read()
    t('install.py: tag, zip pin, ini pin, --undo, --skip-run-check', "'.before-chain1106'" in src and "LIVE_ZIP_MD5 = '" + files['F01_Main.zip'][0] in src
      and files['KLJoin.ini'][0] in src and files['KLGuns.ini'][0] not in src and '--undo' in src and '--skip-run-check' in src)
    C.write_install(st, files, ['doors', 'outro', 'cam2d'], '.before-chain2d1106')
    src2 = open(os.path.join(st, 'install.py')).read()
    t('install.py takes a custom backup tag (2d)', "MAP, TAG = 'DM05A', '.before-chain2d1106'" in src2 and 'cam2d' in src2 and '.before-chain1106' not in src2.split('FILES = [')[0].split('MAP, TAG')[1])
    C.write_install(st, files, ['doors', 'outro'])
    rc, out = run(st, '--game', os.path.join(d, 'nogame'), '--dry')
    t('install.py refuses a missing game folder', rc == 1 and 'REFUSED' in out)
    rc, out = run(st, '--game', game, '--dry')
    t('install.py --dry says would install, writes nothing', rc == 0 and out.count('would install') == 4 and not any(f.endswith('.before-chain1106') for f in os.listdir(md)))
    # all or nothing: one ini changed since staging
    put(os.path.join(md, 'KLJoin.ini'), b'someone edited this')
    rc, out = run(st, '--game', game)
    t('a changed pin refuses everything', rc == 1 and 'REFUSED' in out and open(os.path.join(md, 'F01_Main.zip'), 'rb').read() == old['F01_Main.zip']
      and not any(f.endswith('.before-chain1106') for f in os.listdir(md)))
    put(os.path.join(md, 'KLJoin.ini'), old['KLJoin.ini'])
    # an existing backup is never overwritten
    put(os.path.join(md, 'KLJoin.ini.before-chain1106'), b'mine')
    rc, out = run(st, '--game', game)
    t('an existing backup refuses, is not overwritten', rc == 1 and open(os.path.join(md, 'KLJoin.ini.before-chain1106'), 'rb').read() == b'mine'
      and open(os.path.join(md, 'F01_Main.zip'), 'rb').read() == old['F01_Main.zip'])
    os.remove(os.path.join(md, 'KLJoin.ini.before-chain1106'))
    rc, out = run(st, '--game', game)
    t('install writes the 4 changed files, backs up the originals', rc == 0 and all(open(os.path.join(md, n), 'rb').read() == new[n] for n in C.FILES5)
      and all(open(os.path.join(md, n + '.before-chain1106'), 'rb').read() == old[n] for n in C.FILES5 if n != 'KLGuns.ini')
      and not os.path.exists(os.path.join(md, 'KLGuns.ini.before-chain1106')))
    rc, out = run(st, '--game', game)
    t('a second install refuses (already installed)', rc == 1)
    put(os.path.join(md, 'KLJoin.ini'), b'edited after install')
    rc, out = run(st, '--game', game, '--undo')
    t('undo refuses when a file is not what the install wrote', rc == 1 and open(os.path.join(md, 'F01_Main.zip'), 'rb').read() == new['F01_Main.zip'])
    put(os.path.join(md, 'KLJoin.ini'), new['KLJoin.ini'])
    rc, out = run(st, '--game', game, '--undo')
    t('undo restores every original byte for byte and removes the backups', rc == 0 and all(open(os.path.join(md, n), 'rb').read() == old[n] for n in C.FILES5)
      and not any(f.endswith('.before-chain1106') for f in os.listdir(md)))
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
