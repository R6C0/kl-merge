#!/usr/bin/env python3
r"""kl_doors_1108.py - OWN-LEAF KICK DOORS for DM01 (F01), DM03A (F07) and DM03 (F03), 2026-11-08. STAGE ONLY: reads the live zips (or the staged
dm03cops zips for DM03), writes C:\kl_build_1024\doors_1108\<MAP>, never installs.

Owner: "make more doors kickable even if u use the doors on the map already, stop reusing the same plain white door".
Until now every kick door was the white Dog Days leaf (kl_interact_graft cloned it and deleted the map's own leaf). Here the map's OWN leaf model is kept:
kl_interact_graft.build(own_leaf=True) makes the keyed DD leaf model-less and hangs the own leaf under it (re-pivoted by its transform, no vertex edit).
The leaf stands exactly where it stood (no snap), so bots meet the same closed door they meet today. Kick sound: the DD door nodes keep the SND references
the existing KL_Door groups already carry (default behaviour of the graft, unchanged); the audit (re/sfx_audit_1108.md) found kick_knee / door objects in every bank.
GUESS (nothing here is run in the game): (1) a model-less keyed ZSTDOBJ moves its kid with the keys and the Havok slab; (2) an unlisted group-0 child under
the pool-group-2 leaf is drawn; (3) the slab size (median host width x height over the map's hosts) fits each own leaf; (4) the DD kick sound plays with
the own leaf; (5) the own leaf's hinge end is the one nearest its origin (door_hosts' rule).

  python tools/kl_doors_1108.py stage [--maps DM01,DM03A,DM03] [--out <dir>] [--in-dir MAP=<dir>] [--no-own]
--no-own stages the same hosts with the white leaf (control). Per map: F0x_Main.zip, .bots.zip, .bots.base.md5, KLJoin.ini + KLGuns.ini (Entries= = new .prm
chunk count), install.py (+ INSTALL / UNDO bats), bench_cover_lines.txt, build_report.json.
DM03 sits ON TOP of the dm03cops_1108 stage (its zips are the input and their md5s the pins): INSTALL DM03 COPS FIRST, install.py refuses otherwise.
"""
import hashlib, json, math, os, re, shutil, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BS = chr(92)
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = r'C:\kl_build_1024\doors_1108'
TAG = '.before-doors_1108'
COPS = r'C:\kl_build_1024\dm03cops_1108'
# per map: slot, input dir, pinned md5 of (plain zip, bots zip, bots.base.md5 file), hosts (live .prp node numbers, picked by a 11-08 scan), top group, first door number
MAPS = {
    'DM01': dict(slot='F01', dir=os.path.join(GAME, 'KLExpansion', 'Maps', 'DM01'), top='KL_Interact!2', base=7,
                 pins=('9ce9f34d0294f0a6a3e76eea6ec92f46', '975ad3c3bc1e1ca83d68baf41e9f0d06', '5d48fb624ae6f916950b13f69a3b3966'),
                 hosts=[957, 2569]),
    'DM03A': dict(slot='F07', dir=os.path.join(GAME, 'KLExpansion', 'Maps', 'DM03A'), top='KL_Interact!2', base=5,
                  pins=('3371303dd338a837aaba2e33e00fe40b', '16ae8673f69e1b9092e89a9ab01f28d2', '24618ef2e64d68f2d6f36184b12e4382'),
                  hosts=[6516, 6770]),
    # DM03: input = the dm03cops stage (md5s of its F03_Main.zip / .bots.zip / .bots.base.md5), inis from the live DM03 folder
    'DM03': dict(slot='F03', dir=COPS, ini_dir=os.path.join(GAME, 'KLExpansion', 'Maps', 'DM03'), top='KL_Interact!1', base=0,
                 pins=('da7b36420dd353bdfb7741bd6cabf026', '0b90ab321c9b1d3504c9f9d0fe441719', 'fedcd656dcfe300e65e20da373f3a636'),
                 hosts=[176, 64, 546, 1076, 1255]),
}
INIS = ('KLJoin.ini', 'KLGuns.ini')
CHANGED_OK = ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX', '.HVK', '.hrd')


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def chunks(zp):
    import kl_prmgraph
    with zipfile.ZipFile(zp) as z:
        prm = [n for n in z.namelist() if n.lower().endswith('.prm')]
        return len(kl_prmgraph.read(z.read(prm[0])).chunks)


def patch_entries(path_in, n):
    txt = open(path_in, 'rb').read().decode('latin-1')
    new, c = re.subn(r'(?m)^(Entries\s*=\s*)\d+', lambda m: m.group(1) + str(n), txt)
    return new.encode('latin-1'), c


def safety(zp, hosts, log):
    """Offline checks on the INPUT zip's hosts: distance of each door hinge from the spawn points and the exit icon (a door is a solid slab: it must not
    stand on a spawn or the escape), and how many of its two sides lie on the main walk part (bots can only meet a door with both). The leaf stays where it
    stands today, so bot routes do not change. Returns [(k, spawn dist, exit dist, main-part sides)]."""
    import kl_fa_bots as F, kl_interact_graft as IG
    B = F.Built(zp)
    nav = F.Nav(B.scene.nav)
    main = IG.main_part(nav)
    allh = {h['k']: h for h in IG.door_hosts(B, nav)}
    pts = {'spawn': [], 'exit': []}
    for k, p in enumerate(B.sc.path):
        if not p or k == 0 or k > len(B.ents):
            continue
        last = p.rsplit(BS, 1)[-1].lower()
        pos = B.fr[B.ents[k - 1]][1]
        if last.endswith('mapiconexit'):
            pts['exit'].append(pos)
        elif 'spawn' in last or 'playerstart' in last:
            pts['spawn'].append(pos)
    out = []
    for k in hosts:
        if k not in allh:
            raise ValueError('%s: node %d is not a door host (door_hosts)' % (zp, k))
        h = allh[k]
        P = h['hinge']
        dm = lambda L: min([math.hypot(P[0] - q[0], P[2] - q[2]) for q in L] or [1e9])
        sides = sum(1 for x in IG.door_stand(nav, h) if x and x[1] == main)
        out.append((k, round(dm(pts['spawn'])), round(dm(pts['exit'])), sides))
        log('  host %d %s: spawn %.0f cm (of %d), exit %.0f cm, main-part sides %d' % (k, h['name'][-34:], dm(pts['spawn']), len(pts['spawn']), dm(pts['exit']), sides))
        if dm(pts['spawn']) < 150 or dm(pts['exit']) < 300:
            raise ValueError('door host %d stands on a spawn or the exit' % k)
    return out


def free_top(zp):
    """(first unused 'KL_Interact!N', number of KL_Door groups already in the zip) read off the .prp node paths."""
    import kl_fa_bots as F
    paths = [p for p in F.Built(zp).sc.path if p]
    tops = {p.split(BS)[1] for p in paths if p.startswith('ROOT' + BS + 'KL_Interact!')}
    doors = {BS.join(p.split(BS)[1:3]) for p in paths if p.startswith('ROOT' + BS + 'KL_Interact!') and p.split(BS)[2:3] and p.split(BS)[2].startswith('KL_Door_')}
    n = 1
    while 'KL_Interact!%d' % n in tops:
        n += 1
    return 'KL_Interact!%d' % n, len(doors)


def graft_one(src, dst, cfg, own, log):
    import kl_interact_graft as IG
    top, base = free_top(src)
    log('  top group %s, %d kick doors already in the zip (new ones numbered from %d)' % (top, base, base + 1))
    return IG.build(src, dst, ext=0, spots=[], doors=list(cfg['hosts']), log=log, top=top, door_base=base, own_leaf=own)


INSTALL = r'''"""Installs / undoes the OWN-LEAF KICK DOORS 1108 (tools/kl_doors_1108.py) on the live @MAP@ files@NEEDS@.

  python install.py            install (originals -> <name>.before-doors_1108 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 another Dog Days folder (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Every live md5 is pinned BEFORE anything is written (all or nothing); nothing is written while kl2.exe runs. Never touches KL_PortBackup."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = '@MAP@', '@TAG@'
FILES = @FILES@


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
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another pass changed it@HINT@: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (1 << 30)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + 1024 MB free on the game drive'); return 1
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
'''


def stage_map(name, out, in_dir=None, own=True, log=print):
    cfg = MAPS[name]
    slot = cfg['slot']
    src_dir = in_dir or cfg['dir']
    ini_dir = cfg.get('ini_dir', src_dir)
    zn, bn, mn = '%s_Main.zip' % slot, '%s_Main.bots.zip' % slot, '%s_Main.bots.base.md5' % slot
    for n, pin in zip((zn, bn, mn), cfg['pins']):
        got = fmd5(os.path.join(src_dir, n))
        if got != pin:
            raise ValueError('REFUSED: %s is %s, not the pinned %s%s' % (os.path.join(src_dir, n), got, pin, ' (stage dm03cops first)' if name == 'DM03' else ''))
    if open(os.path.join(src_dir, mn)).read().strip() != cfg['pins'][0]:
        raise ValueError('%s: bots.base.md5 is not the plain zip md5' % name)
    mo = os.path.join(out, name)
    os.makedirs(mo, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='doors_', dir=out)
    rep = {}
    try:
        log('== %s: safety' % name)
        rep['safety'] = safety(os.path.join(src_dir, zn), cfg['hosts'], log)
        res = {}
        for n in (zn, bn):
            log('== %s %s' % (name, n))
            dst = os.path.join(tmp, n)
            graft_one(os.path.join(src_dir, n), dst, cfg, own, log)
            res[n] = dst
            with zipfile.ZipFile(os.path.join(src_dir, n)) as a, zipfile.ZipFile(dst) as b:
                bad = [m for m in a.namelist() if m in b.namelist() and a.read(m) != b.read(m) and not m.endswith(CHANGED_OK)]
                if bad or a.namelist() != b.namelist():
                    raise ValueError('%s: members changed outside the allowed set: %s' % (n, bad))
        # the plain and the bots zip must differ only in the .prp, as before
        with zipfile.ZipFile(res[zn]) as a, zipfile.ZipFile(res[bn]) as b:
            diff = [m for m in a.namelist() if a.read(m) != b.read(m)]
            if any(not m.lower().endswith('.prp') for m in diff):
                raise ValueError('plain and bots zips differ outside the .prp: %s' % diff)
        plain = fmd5(res[zn])
        rep['chunks'] = chunks(res[zn])
        for n in (zn, bn):
            shutil.move(res[n], os.path.join(mo, n))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    open(os.path.join(mo, mn), 'w', newline='\n').write(plain + '\n')
    files = [(zn, cfg['pins'][0], plain), (bn, cfg['pins'][1], fmd5(os.path.join(mo, bn))), (mn, cfg['pins'][2], fmd5(os.path.join(mo, mn)))]
    for n in INIS:
        data, c = patch_entries(os.path.join(ini_dir, n), rep['chunks'])
        if c != 1:
            raise ValueError('%s: %d Entries= lines' % (n, c))
        open(os.path.join(mo, n), 'wb').write(data)
        files.append((n, fmd5(os.path.join(ini_dir, n)), fmd5(os.path.join(mo, n))))
    needs = " (needs dm03cops_1108 INSTALLED first: its zips are this pass's pinned base)" if name == 'DM03' else ''
    hint = '; install dm03cops_1108 first' if name == 'DM03' else ''
    src = INSTALL.replace('@MAP@', name).replace('@GAME@', GAME).replace('@TAG@', TAG).replace('@FILES@', repr(files)).replace('@NEEDS@', needs).replace('@HINT@', hint)
    open(os.path.join(mo, 'install.py'), 'w', newline='\n').write(src)
    for nm, arg in (('INSTALL %s doors 1108.bat' % name, ''), ('UNDO %s doors 1108.bat' % name, ' --undo')):
        open(os.path.join(mo, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    ini = os.path.join(GAME, 'KLHook.ini')
    cover = [ln.rstrip('\r\n') for ln in open(ini, encoding='latin1') if ln.split('=')[0].strip() in ('AssertSoft', 'ClientBuild', 'ClientBuildHost', 'ClientBuildMaps', 'ClientRewrite', 'ClientRingSync')]
    open(os.path.join(mo, 'bench_cover_lines.txt'), 'w').write('\n'.join(cover) + '\n')
    rep.update(files=files, own=own, hosts=cfg['hosts'], top=cfg['top'], door_base=cfg['base'])
    json.dump(rep, open(os.path.join(mo, 'build_report.json'), 'w'), indent=1, default=str)
    return files


def main(a):
    if not a or a[0] != 'stage':
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    maps = [m for m in opt('--maps', ','.join(MAPS)).split(',') if m]
    bad = [m for m in maps if m not in MAPS]
    if bad:
        raise SystemExit('unknown map %s (maps: %s)' % (bad, ','.join(MAPS)))
    ind = {}
    for i, x in enumerate(a):
        if x == '--in-dir':
            k, v = a[i + 1].split('=', 1)
            ind[k] = v
    for m in maps:
        for n, o, w in stage_map(m, opt('--out', OUT), ind.get(m), own='--no-own' not in a):
            print('%-6s %-26s %s -> %s' % (m, n, o, w))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
