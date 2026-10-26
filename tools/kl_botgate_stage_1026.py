"""kl_botgate_stage_1026.py - stage the eAllTypes sibling zips for the hook's [BotGate] (2026-10-26).
OFFLINE: reads the LIVE zips, writes only under <root>/<MAP>/stage. Nothing is installed.

[BotGate] Enable=1 (klhook, f8cf4f2c4) swaps the archive a map open resolves to for '<name>.bots.zip' ONLY online and when the host's
[BotFill] OnlineHost=1; otherwise the plain zip (squad mask eHeistOnly) is used. NEVER put eAllTypes under the plain name.

  python kl_botgate_stage_1026.py stage <root> [MAP ...]   per expansion map: kl_botsonline.convert(plain zip) -> <root>/<MAP>/stage/<name>.bots.zip
                                                           + install.py (pins the plain zip md5; copies the sibling + <name>.bots.base.md5; --undo deletes both)
  python kl_botgate_stage_1026.py check [<Maps folder>]    OK / DRIFT per <name>.bots.zip (base md5 file vs the plain zip's md5 now); exit 1 on DRIFT
Every later install (cover/loot/arcade) changes the plain zip, so RE-STAGE + install after the last one.
"""
import glob, hashlib, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
MAPSDIR = GAME + '/KLExpansion/Maps'

INSTALL_PY = '''"""Installs / undoes the staged %(map)s bots sibling %(sib)s (tools/kl_botgate_stage_1026.py, 2026-10-26). This pair IS the feature's on/off switch.
  python install.py           copy %(sib)s + %(sib_md5)s next to %(zip)s (the plain zip is NOT touched)
  python install.py --undo    delete exactly those two files (only when their md5 is what this wrote)
  --game <dir>                a Dog Days folder other than the default (rehearsals)
The live plain md5 is pinned before the install; nothing is written while kl2.exe runs."""
import hashlib, os, shutil, subprocess, sys

GAME = %(game)r
MAP, ZIP, SIB, BASEF = %(map)r, %(zip)r, %(sib)r, %(sib_md5)r
BASE, NEW = %(base)r, %(new)r


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    a = sys.argv[1:]
    undo = '--undo' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    plain, sib, basef = os.path.join(d, ZIP), os.path.join(d, SIB), os.path.join(d, BASEF)
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), SIB)
    if '--skip-run-check' not in a and 'kl2.exe' in subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower():
        print('REFUSED: kl2.exe is running'); return 3
    if undo:
        for p, want in ((sib, NEW), (basef, None)):
            if os.path.isfile(p) and want and md5(p) != want:
                print('REFUSED: %%s md5 %%s is not the installed %%s' %% (p, md5(p), want)); return 2
        if os.path.isfile(basef) and open(basef).read().strip() != BASE:
            print('REFUSED: %%s does not hold %%s' %% (basef, BASE)); return 2
        n = 0
        for p in (sib, basef):
            if os.path.isfile(p):
                os.remove(p); n += 1
        print('undone: %%d file(s) removed' %% n); return 0
    if not os.path.isfile(plain):
        print('REFUSED: %%s is not there' %% plain); return 2
    cur = md5(plain)
    if cur != BASE:
        print('REFUSED: plain zip md5 %%s is not the pinned %%s (a later install changed it: re-stage)' %% (cur, BASE)); return 2
    if os.path.isfile(sib) and os.path.isfile(basef) and md5(sib) == NEW and open(basef).read().strip() == BASE:
        print('already installed'); return 0
    if os.path.exists(sib) or os.path.exists(basef):
        print('REFUSED: %%s or %%s exists already (other content)' %% (sib, basef)); return 2
    if md5(here) != NEW:
        print('REFUSED: the staged zip next to install.py is not md5 %%s' %% NEW); return 2
    if shutil.disk_usage(d).free < 2 * os.path.getsize(plain):
        print('REFUSED: less than 2x the zip size free on the game drive'); return 2
    try:
        shutil.copyfile(here, sib)
        if md5(sib) != NEW:
            raise OSError('md5 mismatch after copy')
        with open(basef, 'w', newline='\\n') as fh:
            fh.write(BASE + '\\n')
    except OSError as e:
        for p in (sib, basef):
            if os.path.isfile(p):
                os.remove(p)
        print('copy failed (%%s), partial files removed' %% e); return 2
    print('installed: %%s md5 %%s (base %%s)' %% (sib, NEW, BASE)); return 0


if __name__ == '__main__':
    sys.exit(main())
'''


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def plain_zips(d):
    """The plain *_Main.zip files of a map folder (never a .bots.zip)."""
    return sorted(f for f in os.listdir(d) if f.lower().endswith('_main.zip'))


def sibling_name(zn):
    return zn[:-4] + '.bots.zip'


def fnv(path):
    """The hook's botgate fingerprint (c9 fe0c72b71): FNV-1a 32 over the first 64 KB then the last 64 KB, one running hash.
    GUESS until compared with a live 'botgate: ... [size N fnv X]' line (the overlap rule for files under 128 KB is not known)."""
    n = os.path.getsize(path)
    with open(path, 'rb') as fh:
        a = fh.read(65536); fh.seek(max(0, n - 65536)); b = fh.read(65536)
    h = 0x811c9dc5
    for c in a + b:
        h = ((h ^ c) * 0x01000193) & 0xffffffff
    return 'size %d fnv %08x' % (n, h)


def drift(maps):
    """[(map, sibling, status, detail)] for every <name>.bots.zip under maps; status OK or DRIFT. Read-only."""
    res = []
    if not os.path.isdir(maps):
        return res
    for m in sorted(os.listdir(maps)):
        d = os.path.join(maps, m)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith('.bots.zip'):
                continue
            plain = os.path.join(d, f[:-len('.bots.zip')] + '.zip')
            bf = os.path.join(d, f[:-len('.zip')] + '.base.md5')
            if not os.path.isfile(plain):
                res.append((m, f, 'DRIFT', 'no plain zip %s' % os.path.basename(plain))); continue
            if not os.path.isfile(bf):
                res.append((m, f, 'DRIFT', 'no %s (sibling not installed by this tool)' % os.path.basename(bf))); continue
            base, now = open(bf).read().strip(), md5(plain)
            if base == now:
                res.append((m, f, 'OK', 'base md5 %s; sibling [%s], plain [%s]' % (now, fnv(os.path.join(d, f)), fnv(plain))))
            else:
                res.append((m, f, 'DRIFT', 'a later install changed the plain zip (base %s, now %s): rerun stage + install' % (base[:8], now[:8])))
    return res


def check(maps=MAPSDIR, log=print):
    bad = 0
    rs = drift(maps)
    for m, f, st, det in rs:
        log('%-8s %-22s %s  %s' % (m, f, st, det))
        bad += st == 'DRIFT'
    if not rs:
        log('no .bots.zip siblings installed')
    log('botgate drift: %d' % bad)
    return bad


def stage_map(root, name, log=print):
    import kl_botsonline
    d = os.path.join(MAPSDIR, name)
    zs = plain_zips(d) if os.path.isdir(d) else []
    if not zs:
        log('== %s: no *_Main.zip, skipped' % name); return None
    zn = zs[0]
    live = os.path.join(d, zn)
    sib = sibling_name(zn)
    out = os.path.join(root, name, 'stage')
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    base = md5(live)
    need = os.path.getsize(live) * 2
    free = shutil.disk_usage(root).free
    if free < need + (1 << 30):
        shutil.rmtree(out)
        log('== %s: SKIPPED, %d MB free under %s (need %d MB + 1 GB)' % (name, free >> 20, root, need >> 20)); return None
    dst = os.path.join(out, sib)
    log('== %s (%s) base md5 %s ==' % (name, zn, base))
    try:
        kl_botsonline.convert(live, dst, 'eAllTypes', os.path.basename(zn).split('_Main')[0], log)
    except Exception as e:
        shutil.rmtree(out)
        log('  SKIPPED: %s' % e); return {'map': name, 'skipped': str(e)}
    new = md5(dst)
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map=name, zip=zn, sib=sib, sib_md5=sib[:-4] + '.base.md5', game=GAME, base=base, new=new))
    rep = dict(map=name, zip=zn, sibling=sib, base_md5=base, sibling_md5=new, size=os.path.getsize(dst))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    log('  %s md5 %s (base %s)' % (sib, new, base))
    return rep


def main():
    a = sys.argv[1:]
    if a and a[0] == 'check':
        return 1 if check(a[1] if len(a) > 1 else MAPSDIR) else 0
    if len(a) < 2 or a[0] != 'stage':
        print(__doc__); return 2
    root = a[1]
    if os.path.normcase(os.path.abspath(root)).startswith(os.path.normcase(os.path.abspath(GAME))):
        print('REFUSED: stage root %s is inside the game folder' % root); return 2
    allm = sorted(m for m in os.listdir(MAPSDIR) if os.path.isdir(os.path.join(MAPSDIR, m)))
    unknown = [x for x in a[2:] if x not in allm]
    if unknown:
        print('REFUSED: unknown map(s) %s (have %s)' % (unknown, allm)); return 2
    os.makedirs(root, exist_ok=True)
    names = a[2:] or allm
    res = {n: stage_map(root, n) for n in names}
    with open(os.path.join(root, 'summary.json'), 'w') as fh:
        json.dump(res, fh, indent=1)
    skipped = [n for n, r in res.items() if not r or 'skipped' in r]
    print('staged %d, SKIPPED %d%s' % (len(res) - len(skipped), len(skipped), (': ' + ', '.join(skipped)) if skipped else ''))
    return 1 if skipped else 0


if __name__ == '__main__':
    sys.exit(main())
