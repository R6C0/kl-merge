"""Flat Raid (DD10) ledge, 2026-11-08 (owner: "fix the ledge bit on flat raid, so you can either get a secret way back to the van or something
with more loot there").  Writes the stage C:\\kl_build_1024\\flatledge_1108 : the live DD10 KLJoin.ini + two [Join] boxes, install.py, UNDO.bat.
No zip change, no dll change (klhook/kljoin.c already has Enable / Delay / Slack / FedRide).  Reads the game folder, never writes it.

WHAT THE LEDGE IS (nav mesh of the live F07_Main.zip, kl_route.Mesh; coordinates x, y up, z)
  The campaign's window ledge: a strip x 6435 .. 6805, y 1187 .. 1300, z 2485 .. 4388 (nav part 6, 12), OUTSIDE the tower's wall (mesh of the
  FA map starts x 6842), 12 m over the street.  The campaign reaches it from the flat's window by two drop links:
    (6835, 1600, 3100) -> (6743, 1441, 3100) -> (6593, 1200, 3101)       (sill -> balcony -> ledge)
  Nothing in the FA layer lets a player do that (the window is blocked, REF 21530 / 27838 walk-proof), so the ledge "leads nowhere".  Its north
  end (6446..6583, 1190, 2485) is 14 m from the van's lane (z 1100) and 18 m from the boarding place 06_Exit (8300, 0, 1100).
  The ledge's south end (z > 4037) lies in the map's Warn slab and z > 4284 in its Bound slab (kl_l05_layer.BOUND_GROUPS): the danger zone.

DESIGN (a) = two KLJoin rides, both off for the police and for bots (they are not local players / FedRide=0), each its own toggle:
  [Join.2]  window sill -> ledge     entry Jump05 (6489, 1200, 3123) = the campaign's own jump point on the ledge (MEASURED: on mesh poly 196)
  [Join.3]  ledge north end -> street entry 06_Exit (8300, 0, 1100) = the boarding place (the van's stop)
  Risk / reward: the heister who goes out of the window walks the 1.4 m strip 7 m north (z 3123 -> 2600, ~5 s) in view of the street, then rides to the
  van's stop.  It skips the whole ground floor and the plaza, so it is only worth it while the van is already there.  It does not skip the loot
  rules: the escape is still the van's own (the box moves a player, it never escapes him), carried loot goes with him.
  (b) more loot on the ledge: NOT done - it needs a zip change on the file d0's van-shield work also stages, and DD10 already holds the 4M..8M
  total (8 stacks x 500k = 4M); the ride is a pure KLJoin.ini change that cannot collide.
GUESS: the sill box (the window plane is near x 6840, the mesh edge is x 6835), the ride delays, and whether a landing on 06_Exit is clear of the van.

  python kl_flatledge_1108.py            write the stage (reads the live files)
  python kl_flatledge_1108.py --check    only verify the pieces (selftest, used by kl_tests)
"""
import hashlib, os, sys

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE_JOIN = os.path.join(DD, 'KLExpansion', 'Maps', 'DD10', 'KLJoin.ini')
LIVE_MD5 = '847639de9065b7e145f40439cc9bcf23'
STAGE = r'C:\kl_build_1024\flatledge_1108'
TAG = '.before-flatledge1108'

BLOCK = '''
; ---- flatledge_1108 (tools\\kl_flatledge_1108.py): the campaign's window ledge as a secret way to the van. (recommended on); Enable=0 in a box = off.
; Both boxes are for heisters only (FedRide=0: the police never ride them); the AI crew does not use them (not local players).
; [Join.2] the window sill of the 2nd-floor flat (the campaign drop link starts at 6835, 1600, 3100) -> the ledge jump point Jump05 (6489, 1200, 3123,
; measured on the nav mesh). GUESS: the box (x 6790..6900 = 50 inside the mesh edge, z 3040..3160, y 1560..1700) and Delay 1.5.
[Join.2]
Enable=1
Min=6790 1560 3040
Max=6900 1700 3160
Name=Jump05
Target=6489 1200 3123
Tolerance=8
Delay=1.5
Slack=120
FedRide=0
; [Join.3] the ledge's north end (nav poly 197: x 6446..6583, y 1190, z 2485..2720) -> the boarding place 06_Exit (8300, 0, 1100, the van's stop).
; GUESS: Delay 3 (a short ride) and that a landing on 06_Exit is clear of the van.
[Join.3]
Enable=1
Min=6430 1100 2470
Max=6600 1320 2640
Name=06_Exit
Target=8300 0 1100
Tolerance=8
Delay=3
Slack=150
FedRide=0
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def new_ini(old):
    nl = b'\r\n' if b'\r\n' in old else b'\n'
    if b'flatledge_1108' in old:
        raise SystemExit('the live KLJoin.ini already has the flatledge boxes')
    return old.rstrip(b'\r\n') + nl + BLOCK.replace('\n', nl.decode()).encode('ascii')


INSTALL = r'''"""flatledge 1108 stage: DD10 KLJoin.ini + 2 boxes (window sill -> ledge, ledge -> van stop). python install.py | --undo | --dry [--root <DD>]
Refuses unless the live KLJoin.ini is %(old)s. Backup KLJoin.ini%(tag)s; undo only when live == the kit's file."""
import hashlib, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OLD, NEW, TAG = '%(old)s', '%(new)s', '%(tag)s'
def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()
a = sys.argv[1:]
dd = a[a.index('--root') + 1] if '--root' in a else r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
f = os.path.join(dd, 'KLExpansion', 'Maps', 'DD10', 'KLJoin.ini')
kit = os.path.join(HERE, 'KLJoin.ini')
if '--skip-run-check' not in a and b'kl2.exe' in subprocess.run(['tasklist'], capture_output=True).stdout:
    sys.exit('kl2.exe is running: close the game first')
dry = '--dry' in a
if '--undo' in a:
    if not os.path.isfile(f + TAG): sys.exit('no backup: nothing to undo')
    if md5(f) != NEW or md5(f + TAG) != OLD: sys.exit('refused: live file or backup is not the pinned one')
    print('restore', f)
    if not dry:
        shutil.copyfile(f + TAG, f); os.remove(f + TAG)
    sys.exit(0)
if md5(kit) != NEW: sys.exit('kit KLJoin.ini damaged')
if md5(f) != OLD: sys.exit('refused: live KLJoin.ini is %%s, expected %%s' %% (md5(f), OLD))
if os.path.exists(f + TAG): sys.exit('backup exists: already installed')
print('install', f)
if not dry:
    shutil.copyfile(f, f + TAG); shutil.copyfile(kit, f)
    assert md5(f) == NEW
'''


def stage():
    old = open(LIVE_JOIN, 'rb').read()
    if md5(old) != LIVE_MD5:
        raise SystemExit('live DD10 KLJoin.ini changed (%s): re-check before staging' % md5(old))
    new = new_ini(old)
    os.makedirs(STAGE, exist_ok=True)
    open(os.path.join(STAGE, 'KLJoin.ini'), 'wb').write(new)
    open(os.path.join(STAGE, 'install.py'), 'w').write(INSTALL % dict(old=LIVE_MD5, new=md5(new), tag=TAG))
    open(os.path.join(STAGE, 'UNDO.bat'), 'w').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')
    open(os.path.join(STAGE, 'INSTALL.bat'), 'w').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    print('staged', STAGE, 'KLJoin.ini', md5(new))


def selftest():
    base = b'[FedBody]\r\nEntries=1\r\n'
    n = new_ini(base)
    assert n.startswith(base.rstrip()) and n.count(b'\r\n[Join') == 2 and b'\n' not in n.replace(b'\r\n', b'')
    try:
        new_ini(n)
        raise AssertionError
    except SystemExit:
        pass
    for k in (b'Min=', b'Max=', b'Name=', b'FedRide=0'):
        assert n.count(bytes([13, 10]) + k) == 2
    print('kl_flatledge_1108 selftest ok')


if __name__ == '__main__':
    selftest()
    if '--check' not in sys.argv:
        stage()
