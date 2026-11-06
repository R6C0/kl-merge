#!/usr/bin/env python3
"""
pd2_guns_stage.py - stage pd2_guns_multi.SPECS (batch 1 + batch 2) as ONE installer (2026-11-06, offline; writes only the stage folder, never the game).

    python tools/pd2_guns_stage.py [--out <dir>] [--maps DM01,DM02] [--no-chain]   (default out <work>/build/pd2guns_1106)

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

CHAIN = r'C:\kl_build_1024\lastcall_chain_1105\stage'


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


def main(a):
    out = os.path.join(M.work(), 'build', 'pd2guns_1106')
    if '--out' in a:
        out = a[a.index('--out') + 1]
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
    if 'DM05A' in maps and '--no-chain' not in a and os.path.isdir(CHAIN):
        scratch = os.path.join(out, '_chainsrc')
        shutil.rmtree(scratch, ignore_errors=True); os.makedirs(scratch)
        live = os.path.join(M.MAPROOT, 'DM05A')
        shutil.copyfile(os.path.join(CHAIN, 'F01_Main.zip'), os.path.join(scratch, 'F01_Main.zip'))
        for f in os.listdir(live):
            if f.lower().endswith('.ini') and not f.endswith('.before'):
                shutil.copyfile(os.path.join(live, f), os.path.join(scratch, f))
        rep = M.stage_map('DM05A', out, src=scratch, dirname='DM05A_chain')
        d = os.path.join(out, 'DM05A_chain')
        finish('DM05A_chain', rep['slot'], d)
        shutil.rmtree(scratch, ignore_errors=True)
        # 'old' of the chain variant: the chain stage's own files (zip, bots, base.md5) and the live ini (the chain does not change them)
        fs = {}
        for f in sorted(os.listdir(d)):
            if f == 'report.json':
                continue
            src = os.path.join(CHAIN, f) if os.path.isfile(os.path.join(CHAIN, f)) else os.path.join(live, f)
            fs[f] = dict(old=md5(src), new=md5(os.path.join(d, f)), size=os.path.getsize(os.path.join(d, f)))
        pins['variants']['DM05A'] = [dict(dir='DM05A_chain', note='on top of the Last Call chain 1105 (zip %s): install the chain FIRST' % fs['F01_Main.zip']['old'][:8], files=fs)]
        print('DM05A_chain done (%.0f s)' % (time.time() - t0), flush=True)
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
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='').write(s)
    for f in ('INSTALL.bat', 'UNDO.bat'):
        t = open(os.path.join(old, f), encoding='utf-8', newline='').read().replace('1105', '1106')
        open(os.path.join(out, f), 'w', encoding='utf-8', newline='').write(t)
    M.write_pics(out)
    print('staged in %s (%.0f s)' % (out, time.time() - t0))


if __name__ == '__main__':
    main(sys.argv[1:])
