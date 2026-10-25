"""Dead Men names and pictures in the online lobby, 1025 (built by kl_lobbynames.py; this file lives in its output folder as install.py).
Puts <set>\\Overlay\\Scenes\\kaneandlynch.zip and <set>\\Overlay\\Patch01.zip over the LIVE overlay copies in <DD>\\KLExpansion\\Overlay.
Backups (renamed once, never overwritten): kaneandlynch.zip.before-1025lobbynames, Patch01.zip.before-1025lobbynames.
usage: python install.py --set 2|3|rand [--dry]     the set must match [Expansion] OnlineSet (2 -> set2, 3 -> set3, 9 -> rand)
       python install.py --undo                     back to the originals (what OnlineSet=0 wants)
Refuses while kl2.exe runs. Never touches KL_PortBackup. While a set is installed a Quick Match lobby shows the same names (static data)."""
import hashlib, json, os, shutil, subprocess, sys
D = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OV = os.path.join(D, 'KLExpansion', 'Overlay')
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '.before-1025lobbynames'
FILES = [os.path.join('Scenes', 'kaneandlynch.zip'), 'Patch01.zip']
a = sys.argv[1:]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


man = json.load(open(os.path.join(HERE, 'manifest.json')))
if '--dry' not in a and b'kl2.exe' in subprocess.run(['tasklist'], capture_output=True).stdout:
    sys.exit('kl2.exe is running: close the game first')
live = [os.path.join(OV, f) for f in FILES]
if '--undo' in a:
    for p in live:
        if os.path.exists(p + TAG):
            os.remove(p)
            os.rename(p + TAG, p)
            print('restored', p, md5(p))
    sys.exit()
if '--set' not in a:
    sys.exit(__doc__)
name = 'set' + a[a.index('--set') + 1] if a[a.index('--set') + 1] in ('2', '3') else a[a.index('--set') + 1]
if name not in man['sets']:
    sys.exit('unknown set ' + name)
want = man['sets'][name]
known = {man['base_scene'], man['base_patch']} | {v[k] for v in man['sets'].values() for k in ('scene', 'patch')}
for p in live:                                       # the live file is the original or one of OUR variants, nothing else
    assert md5(p) in known, 'live file changed since the build: ' + p
src = [os.path.join(HERE, name, 'Overlay', f) for f in FILES]
for p, h in zip(src, (want['scene'], want['patch'])):
    assert md5(p) == h, 'built file changed: ' + p
if '--dry' in a:
    print('dry: checks pass; would install', name, want['names'])
    sys.exit()
for p, s in zip(live, src):
    if not os.path.exists(p + TAG):
        os.rename(p, p + TAG)
    shutil.copyfile(s, p)
    print('installed', name, p, md5(p)[:8])
print('undo: python install.py --undo')
