r"""Installs / undoes the DM01B VAN ON THE MAIN STREET + OPEN PLANTER + NAV BRIDGE 1108 (tools/kl_vehroutes_street2_1108.py; replaces tools/kl_vehroutes_street_1108.py and tools/kl_vehroutes_1108.py: install ONE) on the live DM01B files, which were read at stage time:
every pin below is the md5 of a live file as it was then.

  python install.py            install (originals -> <name>.before-vehroutes1108street2 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
  --min-free-mb N              free space wanted on the game drive besides the files (default 300: the files themselves are counted on top)
Every live md5 is pinned BEFORE anything is written (all or nothing: a failure part-way puts the originals back); nothing is written while kl2.exe runs.
Never touches KL_PortBackup or any other file."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM01B', '.before-vehroutes1108street2'
LIVE_ZIP_MD5 = '74d3723323dc1aa03d3166b522ae5448'
FILES = [   # name, live md5 before, staged md5 after
    ('F03_Main.zip', '74d3723323dc1aa03d3166b522ae5448', '1d68eadef23caf9fecbbfeadab68c7f3'),
    ('F03_Main.bots.zip', '73583df1aa6b251d3c4aca7d86cebaa6', 'd84ed4104336f8e587cc9ada2b3f2087'),
    ('F03_Main.bots.base.md5', 'c3535e34052721460900c50dae9e0811', 'fcac2fd26f699838929441ade96c4219'),
]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    min_free = (int(a[a.index('--min-free-mb') + 1]) if '--min-free-mb' in a else 300) << 20
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-26s live %s' % (n, cur))
        if n == 'F03_Main.zip' and not undo and cur != LIVE_ZIP_MD5:
            print('REFUSED: the live zip is %s, not %s: another pass changed it, re-stage the chain on the new live files' % (cur, LIVE_ZIP_MD5)); return 1
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another pass changed it: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[1]) for p in plan) + max(os.path.getsize(p[3]) for p in plan) + min_free
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + %d MB free on the game drive' % (min_free >> 20)); return 1
    if dry:
        for p in plan:
            print('would %s %s' % ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
