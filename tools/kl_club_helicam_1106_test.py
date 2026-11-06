"""Off-game self-test of kl_club_helicam_1106 (fast: no game files, no 100 MB zips)."""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_club_helicam_1106 as H

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


fl, aim = H.wanted('A')
t('variant A sets f5/f6 only, aims at EscCameraLAST', fl[:4] == [None] * 4 and fl[4:] == [-900.0, 200.0] and aim == H.AIM_A)
fl, aim = H.wanted('B')
t('variant B is the stock F06 floats with a heli sibling', fl == [0.0, -270.0, -270.0, 80.0, 0.0, -170.0] and 'EscapeChopper' in aim)
fl, aim = H.wanted('A', f5=-800, f6=150, aim='ROOT\\x')
t('overrides apply', fl[4:] == [-800.0, 150.0] and aim == 'ROOT\\x')
fl, aim = H.wanted('F')
t('variant F = the stock LookFromPos floats, eye node CamPos01', fl == [0.0, 99999.0, 99999.0, 40.0, 0.0, 50.0] and aim.endswith('!CamPos01') and H.MODES['F'] == 'eFMM_LookFromPos')
vf = ['ECP_NotSet'] + fl + [0, 0, aim, 'eFMC_Unbreakable', 'eFMM_LookFromPos', 1]
t('done_state F true in LookFromPos, false in LookAtPos', H.done_state(vf, fl, aim, 'eFMM_LookFromPos') and not H.done_state(vf, fl, aim)
  and not H.done_state(vf[:11] + ['eFMM_LookAtPos', 1], fl, aim, 'eFMM_LookFromPos'))
fl, aim = H.wanted('D')
t('variant D = stock outside camera: LookFromPosFA, floats 0 -270 -270 80 0 0, aim the heli group, eye = the 2c eye',
  fl == [0.0, -270.0, -270.0, 80.0, 0.0, 0.0] and aim.endswith('EscapeChopper\\Escape_Chopper') and H.MODES['D'] == 'eFMM_LookFromPosFA'
  and H.EYES['D'] == (7093.0, 2181.0, 2727.0) and 'F' not in H.EYES)
vd = ['ECP_NotSet'] + fl + [0, 0, aim, 'eFMC_Unbreakable', 'eFMM_LookFromPosFA', 1]
t('done_state D true in LookFromPosFA, false in 2c LookFromPos', H.done_state(vd, fl, aim, 'eFMM_LookFromPosFA') and not H.done_state(vd[:11] + ['eFMM_LookFromPos', 1], fl, aim, 'eFMM_LookFromPosFA'))
t('done_state D false on an old floats set', not H.done_state(vd[:3] + [99999.0] + vd[4:], fl, aim, 'eFMM_LookFromPosFA'))
try:
    H.wanted('C'); t('unknown variant refused', False)
except ValueError:
    t('unknown variant refused', True)

fl, aim = H.wanted('A')
v = ['ECP_NotSet', 0.0, 99999.0, 99999.0, 40.0, -900.0, 200.0, 0, 0, aim, 'eFMC_Unbreakable', 'eFMM_LookAtPos', 1]
t('done_state true when mode, aim, f5/f6 and message-only match', H.done_state(v, fl, aim))
t('done_state false on the old mode', not H.done_state(v[:11] + ['eFMM_LookFromPos', 1], fl, aim))
t('done_state false when no longer message-only', not H.done_state(v[:12] + [0], fl, aim))
t('done_state false on a different f6', not H.done_state(v[:6] + [50.0] + v[7:], fl, aim))

with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, 'in'))
    open(os.path.join(d, 'in', 'F01_Main.zip'), 'wb').write(b'not the live zip')
    try:
        H.stage(os.path.join(d, 'out'), os.path.join(d, 'in'))
        t('stage refuses a zip with another md5', False)
    except ValueError as e:
        t('stage refuses a zip with another md5', 'refusing' in str(e) and not os.path.exists(os.path.join(d, 'out', 'F01_Main.zip')))
    st = os.path.join(d, 'st'); os.makedirs(st)
    H.write_install(st, {'F01_Main.zip': ('a' * 32, 'b' * 32), 'F01_Main.bots.base.md5': ('c' * 32, 'c' * 32)})
    src = open(os.path.join(st, 'install.py')).read()
    t('install.py has tag, pin, --undo, --skip-run-check', "'.before-helicam1106'" in src and "LIVE_ZIP_MD5 = '" + 'a' * 32 in src
      and '--undo' in src and '--skip-run-check' in src)
    r = subprocess.run([sys.executable, os.path.join(st, 'install.py'), '--dry', '--game', os.path.join(d, 'nogame')], capture_output=True, text=True)
    t('install.py --dry refuses a missing game folder', r.returncode == 1 and 'REFUSED' in r.stdout)
    H.write_install(st, {'F01_Main.zip': (H.LIVE_PINS['F01_Main.zip'], 'b' * 32)}, '.before-outcam2a1106')
    src = open(os.path.join(st, 'install.py')).read()
    t('install.py takes a custom tag and the live pin', "'.before-outcam2a1106'" in src and H.LIVE_PINS['F01_Main.zip'] in src
      and H.LIVE_PINS['F01_Main.zip'].startswith('e6d2f73e'))
t('wanted() message names A, B, D, F', 'A, B, D or F' in open(H.__file__, encoding='utf-8').read())
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
