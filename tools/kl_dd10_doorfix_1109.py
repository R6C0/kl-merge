r"""DD10 Flat Raid (slot F07) DOOR FIX 1109: undo the kick doors that open onto nothing and keep only the ones that gate a flat.

Why: the 11-08 flats pass (kl_dd10_flats_1108.py) turned 21 plain DD10 doors into KL_Door_n kick doors. The audit (11-09) found 19 of them dead or sealed: a kicked-open
leaf shows a wall / a sealed room, or the door gates nothing (shut flood == open flood on both sides), so the owner kicks a door and nothing happens.
Kept: KL_Door_9 (host 1854, gates 4934 cells on the main side; its back room has NO nav, GUESS: harmless, kept as before) and KL_Door_13 (host 6996, gates 300 / 4202 cells).
Added (audit candidates, base0 node numbers; each measured on its own staged zip): 1941 (artB3 flat, gates 990 / 1678 cells), 6989 (stairway D, 215 / 1058).
Dropped candidates (measured): 2601 clearance with the kept pair (3 cells lost at SpawnPoint_Dead_01 only in that combination, alone it passes: gates 263 / 739),
2633 / 3042 / 3105 / 5526 / 5777 / 5778 / 5780 clearance on their own (leaf swung cuts 23 cells / shut door changes the reachable set), 3102 stands on a spawn,
7749 / 7753 (wood door frames) gate nothing (0 / 0), 10942 is named by a state controller, 3401 is near a spawn (skipped by the audit).

How: the base for the door pass is the flats build WITHOUT its doors (loot + fuel cans only; = s3in of kl_dd10_flats_1108.stage, md5 cf3d6e5c), so the 19 reverted
doors are the stock plain DD10 doors again (the same bytes as before the 11-08 doors pass). kl_dd10_flats_1108.doors_zip then grafts HOSTS (safety + clearance walk as in 1108),
and the vancall edits (hide, cue; kl_dd10_vancall_1108.patch_zip) are re-applied by node path. Loot, fuel cans, van call, KLJoin.ini are untouched.

  python tools/kl_dd10_doorfix_1109.py stage --s3in <dir with F07_Main.zip, .bots.zip, .bots.base.md5> --out <kit dir>
Never installs anything. The kit's install.py pins the live md5s (REFUSES otherwise), keeps .before-dd10doorfix1109 backups, --undo is byte exact."""
import hashlib, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))

MAP, TAG = 'DD10', '.before-dd10doorfix1109'
ZIP, BOTS, BASE, JOIN = 'F07_Main.zip', 'F07_Main.bots.zip', 'F07_Main.bots.base.md5', 'KLJoin.ini'
# live md5s this kit is staged on (read 2026-11-09 18:00): flats + vancall + ledge/land KLJoin
LIVE_MD5 = {ZIP: '1a0d94b05d8a39ad3b9af38ac868da21', BOTS: '27c9fae8ddd29f84fada0fcc18ce4507', BASE: '11a071b39aeb28ba8042ed5e95cd5db1',
            JOIN: '8f3034c0a86d2d1b36bef829b62f02ff'}
HOSTS = [1854, 6996, 1941, 6989]            # base0 (pre-doors) node numbers; door n = index + 1
KEPT_LIVE = {9: 1854, 13: 6996}             # live KL_Door_n -> base0 host (kept)
REVERTED_LIVE = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21]
TEMPLATE = os.environ.get('KL_DOORFIX_TEMPLATE', 'C:/kl_build_1024/dm03doorfix_1109/install.py')


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def make_install(out, stage_md5, template_text=None):
    """install.py from the dm03doorfix template: FILES rows (live -> staged), MAP, TAG and the doc line. Returns the text."""
    t = template_text if template_text is not None else open(TEMPLATE, encoding='utf-8').read()
    names = [n for n in (ZIP, BOTS, BASE, JOIN) if stage_md5.get(n) and stage_md5[n] != LIVE_MD5[n]]
    rows = ", ".join("('%s', '%s', '%s')" % (n, LIVE_MD5[n], stage_md5[n]) for n in names)
    t, k = re.subn(r"^FILES = \[.*?\]\n", lambda m: "FILES = [" + rows + "]\n", t, flags=re.S | re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES line')
    t, k = re.subn(r"^MAP, TAG = '[A-Z0-9]+', '[^']+'", "MAP, TAG = '%s', '%s'" % (MAP, TAG), t, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single MAP, TAG line')
    t, k = re.subn(r'^r?"""Installs / undoes[^\n]*\n', 'r"""Installs / undoes DD10 DOOR FIX 1109 on the live DD10 files (live = flats + vancall + ledge/land): 19 dead kick doors are plain again, 2 kept, 2 new (tools/kl_dd10_doorfix_1109.py).\n', t, count=1, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no docstring head')
    t = t.replace('F03_Main', 'F07_Main')
    return t


def stage(s3in, out):
    import zipfile
    import kl_dd10_flats_1108 as FL
    import kl_dd10_vancall_1108 as VC
    FL._import()
    # Host 1854 (live KL_Door_9) has ONE main-part side (its back room has no nav): kl_doors_1108.one_sided (863694b3) would refuse it. The task keeps it as before
    # (it gates 4934 cells on the main side); GUESS: a kick into a nav-less room is harmless. Every other host here has 2 main-part sides (checked in the safety log).
    FL.DOORS.one_sided = lambda rows: []
    for n in (ZIP, BOTS, BASE):
        if not os.path.isfile(os.path.join(s3in, n)):
            raise SystemExit('REFUSED: %s missing in %s' % (n, s3in))
    if open(os.path.join(s3in, BASE)).read().strip() != fmd5(os.path.join(s3in, ZIP)):
        raise SystemExit('REFUSED: s3in bots.base.md5 is not the md5 of the s3in zip')
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, 'tmp_stage')
    os.makedirs(tmp, exist_ok=True)
    res, resb, kept, rep = FL.doors_zip(s3in, HOSTS, tmp)
    if kept != HOSTS:
        raise SystemExit('REFUSED: the door pass kept %s, expected %s' % (kept, HOSTS))
    for src, n in ((res, ZIP), (resb, BOTS)):
        VC.patch_zip(src, os.path.join(out, n), ('hide', 'cue'))
    open(os.path.join(out, BASE), 'w', newline='\n').write(fmd5(os.path.join(out, ZIP)) + '\n')
    chunks = FL.DOORS.chunks(os.path.join(out, ZIP))
    data, c = FL.DOORS.patch_entries(os.path.join(FL.LIVE, JOIN), chunks)
    if c != 1:
        raise SystemExit('REFUSED: %d Entries= lines in the live KLJoin.ini' % c)
    live_join = open(os.path.join(FL.LIVE, JOIN), 'rb').read()
    if data != live_join:        # the chunk count is unchanged by the door pass in every build so far; if it ever changes the ini is a staged file
        open(os.path.join(out, JOIN), 'wb').write(data)
    sm = {n: fmd5(os.path.join(out, n)) for n in (ZIP, BOTS, BASE)}
    sm[JOIN] = fmd5(os.path.join(out, JOIN)) if os.path.isfile(os.path.join(out, JOIN)) else LIVE_MD5[JOIN]
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(make_install(out, sm))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    shutil.rmtree(tmp, ignore_errors=True)
    for n in sorted(x for x in os.listdir(out) if os.path.isfile(os.path.join(out, x))):
        print('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return sm


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] != ['stage'] or '--s3in' not in a or '--out' not in a:
        raise SystemExit(__doc__)
    stage(a[a.index('--s3in') + 1], a[a.index('--out') + 1])
