#!/usr/bin/env python3
"""
pd2_guns_stage.py - stage pd2_guns_multi.SPECS (batch 1 + batch 2) as ONE installer (2026-11-06, offline; writes only the stage folder, never the game).

    python tools/pd2_guns_stage.py [--out <dir>] [--maps DM01,DM02] [--no-chain] [--no-doors] [--no-glass]   (default out <work>/build/pd2guns_1106)
    python tools/pd2_guns_stage.py --variant doors|chain|glass      rebuild only that DM05A variant into the existing stage (pins.json keeps the rest)

DM05A_doors = the same bake on the chain + kick doors stage (C:\\kl_build_1024\\lastcall_chain_doors_1106\\stage, zip 803a29c8). That stage ships its own
KLGuns.ini / KLJoin.ini (Entries 54378): they are the ini sources and the 'old' pins, stage_map rewrites 54378 to the new count, so NO follow-up step is needed.

Per map folder of the stage: the plate zip built by pd2_guns_multi.stage_map, the [BotGate] sibling (kl_botsonline.convert(zip, 'eAllTypes') as the
live ones), <slot>_Main.bots.base.md5 (md5 of the staged plain zip + LF, 33 bytes), DM11B's Int16Ok.txt (zip= / bots= sizes of the staged files),
KLGuns.ini / KLJoin.ini (Entries count). DM05A is built twice: on the live (stock) zip and on the Last Call chain stage (C:\\kl_build_1024\\
lastcall_chain_1105\\stage) -> folder DM05A_chain, pins.json 'variants'. pins.json pins the CURRENT live md5 of every file as 'old' (install.py
refuses a map that changed since); install.py / INSTALL.bat / UNDO.bat are the batch 1 ones (same backup tag .before-pd2guns, so the 1105 stage and
this one never both apply), shoppage/KLShopPage.ini comes from kl_pd2names.stage on the live Dog Days ini. fits.json is seeded from the 1105 stage
so batch 1 keeps its exact shifts.
"""
import hashlib, json, os, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pd2_guns_multi as M

CHAIN, DOORS, GLASS = M.CHAIN, M.DOORS, M.GLASS


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def finish(name, slot, d, log=print):
    """bots sibling + base.md5 (+ Int16Ok.txt) for the staged plain zip in d -> list of staged file names."""
    import kl_botsonline
    zp = os.path.join(d, slot + '_Main.zip')
    bp = os.path.join(d, slot + '_Main.bots.zip')
    kl_botsonline.convert(zp, bp, 'eAllTypes', slot, log=lambda *a: None)
    with open(os.path.join(d, slot + '_Main.bots.base.md5'), 'w', newline='') as f:
        f.write(md5(zp) + '\n')
    log('  %s: bots sibling %d bytes' % (name, os.path.getsize(bp)))


def int16(live, d, slot):
    """DM11B: the live Int16Ok.txt with zip= / bots= replaced by the staged sizes."""
    import re
    raw = open(os.path.join(live, 'Int16Ok.txt'), 'rb').read()
    sz = {b'zip': os.path.getsize(os.path.join(d, slot + '_Main.zip')), b'bots': os.path.getsize(os.path.join(d, slot + '_Main.bots.zip'))}
    out = []
    for ln in raw.split(b'\n'):
        m = re.match(rb'^(zip|bots)=(\d+)(\r?)$', ln)
        out.append((b'%s=%d%s' % (m.group(1), sz[m.group(1)], m.group(3))) if m else ln)
    open(os.path.join(d, 'Int16Ok.txt'), 'wb').write(b'\n'.join(out))


def pin_files(d, livedir, slot):
    """{file: {old, new, size}} for every staged file of d against the files in livedir (md5 of the live ones = 'old')."""
    pins = {}
    for f in sorted(os.listdir(d)):
        if f == 'report.json':
            continue
        lp = os.path.join(livedir, f)
        if not os.path.isfile(lp):
            raise ValueError('%s: no live %s to pin' % (d, f))
        pins[f] = dict(old=md5(lp), new=md5(os.path.join(d, f)), size=os.path.getsize(os.path.join(d, f)))
    return pins


def variant(out, vname, vstage, vnote, log=print):
    """DM05A baked on another Last Call stage (its F01_Main.zip, and its .ini files when it ships them; else the live ones) -> folder DM05A_<vname>.
    -> the pins.json variants entry. 'old' of every file = the stage's own file when it has one, else the live file (the stage does not change it).
    The stage's KLGuns.ini / KLJoin.ini already carry Entries= the stage's chunk count; stage_map rewrites exactly that number to the new count."""
    dname = 'DM05A_' + vname
    scratch = os.path.join(out, '_%ssrc' % vname)
    shutil.rmtree(scratch, ignore_errors=True); os.makedirs(scratch)
    live = os.path.join(M.MAPROOT, 'DM05A')
    shutil.copyfile(os.path.join(vstage, 'F01_Main.zip'), os.path.join(scratch, 'F01_Main.zip'))
    for src in (vstage, live):                    # the stage's inis win over the live ones
        for f in os.listdir(src):
            if f.lower().endswith('.ini') and not f.endswith('.before') and not os.path.isfile(os.path.join(scratch, f)):
                shutil.copyfile(os.path.join(src, f), os.path.join(scratch, f))
    rep = M.stage_map('DM05A', out, src=scratch, dirname=dname)
    d = os.path.join(out, dname)
    finish(dname, rep['slot'], d)
    shutil.rmtree(scratch, ignore_errors=True)
    fs = {}
    for f in sorted(os.listdir(d)):
        if f == 'report.json':
            continue
        src = os.path.join(vstage, f) if os.path.isfile(os.path.join(vstage, f)) else os.path.join(live, f)
        fs[f] = dict(old=md5(src), new=md5(os.path.join(d, f)), size=os.path.getsize(os.path.join(d, f)))
    return dict(dir=dname, note=vnote % fs['F01_Main.zip']['old'][:8], files=fs)


VARIANTS = [   # (name, stage dir, pins note); install order everywhere: the Last Call stage FIRST, then this installer
    ('chain', CHAIN, 'on top of the Last Call chain 1105 (zip %s): install the chain FIRST'),
    ('doors', DOORS, 'on top of the Last Call chain + doors 1106 (zip %s): install the doors stage FIRST (INSTEAD of the chain); undo this first'),
    ('glass', GLASS, 'on top of the Last Call chain + glass connectivity 1106 (zip %s): install the glass stage FIRST (INSTEAD of the chain); undo this first'),
]
# replaces the batch 1 installer's plain loop: on 11-06 a just-swapped map hit WinError 32 halfway (DM01, DM03) and was left half-installed
INSTALL_LOOP = '''def retry(fn, *a):
    """A just-read zip can stay locked a few seconds by another process (WinError 32 on 11-06, likely a scanner, GUESS): retry up to ~60 s."""
    import time
    for i in range(30):
        try:
            return fn(*a)
        except PermissionError:
            if i == 29:
                raise
            time.sleep(2)


def roll_back(done):
    """Put a map's already-swapped files back (reverse order) so a failed map is left exactly as before."""
    for live, tag in reversed(done):
        retry(os.remove, live); retry(os.rename, live + tag, live)
        print('  rolled back', os.path.basename(live))


failed = []
for mm in sorted({j[0] for j in todo}, key=[j[0] for j in todo].index):
    done = []
    try:
        for m, live, new, o, n, tag in [j for j in todo if j[0] == mm]:
            if undo:
                retry(os.remove, live); retry(os.rename, live + tag, live)
                print('restored', m, os.path.basename(live), _md5(live)[:8])
            else:
                retry(os.rename, live, live + tag)
                done.append((live, tag))
                shutil.copyfile(new, live)
                assert _md5(live) == n
                print('installed', m, os.path.basename(live), n[:8], '| backup', o[:8])
    except Exception as e:
        print('FAILED %s: %s' % (mm, e)); failed.append(mm)
        if not undo:
            roll_back(done)
if failed:
    sys.exit('failed (left as before): %s' % ' '.join(failed))
'''


def main(a):
    out = os.path.join(M.work(), 'build', 'pd2guns_1106')
    if '--out' in a:
        out = a[a.index('--out') + 1]
    if '--variant' in a:         # rebuild ONE variant (chain|doors) into an existing stage: pins.json keeps everything else
        vn = a[a.index('--variant') + 1]
        v = [x for x in VARIANTS if x[0] == vn][0]
        pp = os.path.join(out, 'pins.json')
        pins = json.load(open(pp))
        ent = variant(out, *v)
        pins['variants']['DM05A'] = [e for e in pins['variants'].get('DM05A', []) if e['dir'] != ent['dir']] + [ent]
        json.dump(pins, open(pp, 'w'), indent=1)
        print('variant %s staged in %s' % (vn, out))
        return
    maps = a[a.index('--maps') + 1].split(',') if '--maps' in a else list(M.MAPS)
    os.makedirs(out, exist_ok=True)
    need = (len(maps) + 1) * 450 << 20
    free = shutil.disk_usage(out).free
    if free < need + (2 << 30):
        sys.exit('disk: %d MB free, want %d MB' % (free >> 20, (need + (2 << 30)) >> 20))
    seed = os.path.join(M.work(), 'build', 'pd2guns_1105', 'fits.json')
    fp = os.path.join(out, 'fits.json')
    if not os.path.isfile(fp) and os.path.isfile(seed):
        shutil.copyfile(seed, fp)
    pins = dict(maps={}, variants={})
    t0 = time.time()
    for m in maps:
        rep = M.stage_map(m, out)
        d = os.path.join(out, m)
        finish(m, rep['slot'], d)
        live = os.path.join(M.MAPROOT, m)
        if os.path.isfile(os.path.join(live, 'Int16Ok.txt')):
            int16(live, d, rep['slot'])
        pins['maps'][m] = pin_files(d, live, rep['slot'])
        print('%s done (%.0f s)' % (m, time.time() - t0), flush=True)
    if 'DM05A' in maps:
        for vname, vstage, vnote in VARIANTS:
            if '--no-' + vname in a or not os.path.isdir(vstage):
                continue
            pins['variants'].setdefault('DM05A', []).append(variant(out, vname, vstage, vnote))
            print('DM05A_%s done (%.0f s)' % (vname, time.time() - t0), flush=True)
    # the shop page II names
    import kl_pd2names
    sd = os.path.join(out, 'shoppage')
    tmp = os.path.join(out, '_names')
    kl_pd2names.stage(tmp, kl_pd2names.live_ini())
    os.makedirs(sd, exist_ok=True)
    shutil.copyfile(os.path.join(tmp, 'KLShopPage.ini'), os.path.join(sd, 'KLShopPage.ini'))
    shutil.rmtree(tmp, ignore_errors=True)
    pins['shop'] = {'KLShopPage.ini': dict(old=md5(kl_pd2names.live_ini()), new=md5(os.path.join(sd, 'KLShopPage.ini')))}
    json.dump(pins, open(os.path.join(out, 'pins.json'), 'w'), indent=1)
    # installer = the batch 1 one
    old = os.path.join(M.work(), 'build', 'pd2guns_1105')
    s = open(os.path.join(old, 'install.py'), encoding='utf-8', newline='').read()
    s = s.replace('"""PD2 guns 1105 (items 35 SG 417, 38 G36, 41 RPK, 44 MK17 on shop page II)',
                  '"""PD2 guns 1106 (items 35 SG 417, 38 G36, 40 / 41 / 42 / 43 RPK, 44 MK17 on shop page II; batch 1 + batch 2 in one)', 1)
    loop = s.index('for m, live, new, o, n, tag in todo:')
    s = s[:loop] + INSTALL_LOOP.replace('\n', '\r\n' if '\r\n' in s else '\n')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='').write(s)
    for f in ('INSTALL.bat', 'UNDO.bat'):
        t = open(os.path.join(old, f), encoding='utf-8', newline='').read().replace('1105', '1106')
        open(os.path.join(out, f), 'w', encoding='utf-8', newline='').write(t)
    M.write_pics(out)
    print('staged in %s (%.0f s)' % (out, time.time() - t0))


if __name__ == '__main__':
    main(sys.argv[1:])
