#!/usr/bin/env python3
r"""kl_club_doors_1106.py - kick doors for Last Call (DM05A, slot F01), written 2026-11-06, REBASED the same day onto the LIVE DM05A zip.
OFFLINE only: nothing here is run in the game and nothing writes into the game folder (install.py does, run by the owner).

Owner 2026-11-05: "kickable doors toward the exit". The pass sits ON TOP of the live Last Call files:
  <DD>\KLExpansion\Maps\DM05A\F01_Main.zip  md5 e6d2f73e... = chain (life -> fight -> heli) + glass section + pd2guns + shop buttons + pics.
It is read by COPYING it into the stage folder (out\_in); any other md5 is refused (no --force). Steps:
  1. kl_interact_graft.build   4 virtual kick doors (the doorways have no door leaf left: the four animated doors are sunk by the club build)
  2. kl_bots_kick_1025.build   the heister bots get a KickDoorBehaviourRout step where a leg crosses a door (else they walk into a shut door)
  3. [BotGate] sibling (kl_botsonline eAllTypes) + bots.base.md5, rebuilt from the final plain zip
  4. KLJoin.ini / KLGuns.ini Entries= set to the new .prm chunk count (the graft appends .prm chunks), read from the live ini
  5. install.py (md5 pinned to the live files, refuses while kl2.exe runs, backups '.before-doors1106' next to the originals) with --undo / --dry
  6. `check`: the offline self-check live vs staged (see check()).

WHAT STAYS BYTE-IDENTICAL: every archive member except .prp .gms .buf .oct .rmi .rmc .prm .MAT .TEX .HVK .hrd. In particular the .sgd (the
HavokShatterGlassConnectivity section is keyed by REF label, not slot id, so renumbering slots cannot invalidate it) and the .LOC (cap 600,000 B).
The slot ids (.oct trees, .rmi, .rmc, list pool) are renumbered by the graft (kl_scene write) and then by the kick pass; `check` proves, by REF label,
that every live id maps to one staged id and nothing but the new entities was added to the trees.

THE DOORS (all on the walk from the loot room to the roof pad; measured on the chain zip's walk mesh, see re/club_fight_1105.md 2026-11-06;
the walk mesh is unchanged by glass/pd2guns/buttons/pics, they touch no geometry)
  B01  daughter-room door B  x 1500, opening z 3293..3433 (two nav wall points 140 cm apart), travel along x
  A02  daughter-room door A  x 2500, same opening z 3293..3433                                  (the 3 'Fight!Loot' guards stand between the two)
  F03  storage Firedoor_03   (-3190, 860, 2306), travel along z, in the 60 cm mesh strip that starts there
  F02  roof Firedoor_02      (-3790, 860, 3287), travel along z, in the 60 cm mesh strip
Orientation: kl_interact_graft.virtual_host(hinge, cx): cx = direction from the free end TO the hinge; the leaf lies along -cx from the hinge.
Width: one scale per map (median over hosts), so every door is 140 wide x 240 high (stock 120 x 220).

usage (from tools/):
  python kl_club_doors_1106.py stage [--out <dir>] [--live <DM05A dir>] [--no-bots]   build the stage (default C:\kl_build_1024\lcdoors_1106)
  python kl_club_doors_1106.py check [--out <dir>] [--live <DM05A dir>]               offline self-check of the stage against the live zip
"""
import collections, hashlib, json, math, os, re, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OUT = r'C:\kl_build_1024\lcdoors_1106'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
LIVE_PIN = 'e6d2f73ef0c51bfdbaec56c9534a4c9a'      # live plain zip (2026-11-06 10:19, bench lcglass1106)
TAG = '.before-doors1106'
WIDTH, HEIGHT = 140.0, 240.0
# name, hinge point (x, y, z), cx (from the free end to the hinge)
DOORS = (('B01', (1500.0, 360.0, 3433.0), (0.0, 0.0, 1.0)),
         ('A02', (2500.0, 360.0, 3433.0), (0.0, 0.0, 1.0)),
         ('F03', (-3120.0, 860.0, 2306.0), (1.0, 0.0, 0.0)),
         ('F02', (-3720.0, 860.0, 3287.0), (1.0, 0.0, 0.0)))
INI_FILES = ('KLJoin.ini', 'KLGuns.ini')
# members the doors pass may change (everything else must be byte-identical to the live zip)
CHANGED_OK = ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX', '.HVK', '.hrd')


def md5(p):
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
    """The ini text with its single Entries= line set to n -> (bytes, number of lines replaced)."""
    txt = open(path_in, 'rb').read().decode('latin-1')
    new, c = re.subn(r'(?m)^(Entries\s*=\s*)\d+', lambda m: m.group(1) + str(n), txt)
    return new.encode('latin-1'), c


def graft(src, dst, log):
    # spots=[]: DOORS ONLY. (ext=0 alone still picks one extinguisher spot, whose template no longer builds in this checkout; the owner asked for doors.)
    import kl_interact_graft as IG
    orig = IG.virtual_host
    IG.virtual_host = lambda hinge, cx, width=WIDTH, height=HEIGHT: orig(hinge, cx, width, height)
    try:
        return IG.build(src, dst, ext=0, spots=[], doors=[('at', h, cx) for _n, h, cx in DOORS], log=log)
    finally:
        IG.virtual_host = orig


INSTALL = r'''r"""Installs / undoes the Last Call KICK DOORS pass (2026-11-06) on top of the live DM05A files (zip e6d2f73e = chain + glass + pd2guns + buttons + pics).
  4 virtual kick doors + heister kick steps (tools/kl_club_doors_1106.py); .prm chunk count -> %(chunks)d, KLJoin.ini / KLGuns.ini Entries= follow.

  python install.py            install (originals -> <name>.before-doors1106 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also usable with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a scratch copy); --skip-run-check for those only
Every live md5 is pinned BEFORE anything is written (all or nothing: a failure part-way puts the originals back); nothing is written while kl2.exe runs.
Never touches KL_PortBackup or any other file."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM05A', '.before-doors1106'
LIVE_ZIP_MD5 = 'e6d2f73ef0c51bfdbaec56c9534a4c9a'      # the precheck: the live plain zip must still be exactly this
FILES = [   # name, live md5 before, staged md5 after
%(files)s]


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
            print('REFUSED: %%s is not there' %% live); return 1
        cur = md5(live)
        print('%%-26s live %%s' %% (n, cur))
        if n == 'F01_Main.zip' and not undo and cur != LIVE_ZIP_MD5:
            print('REFUSED: the live zip is %%s, not %%s: another pass changed it, re-stage the doors on the new live zip' %% (cur, LIVE_ZIP_MD5)); return 1
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %%s' %% bak); return 1
            if cur != new:
                print('REFUSED: %%s live md5 %%s is not the installed %%s' %% (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %%s is not md5 %%s' %% (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %%s live md5 %%s is not the pinned %%s (already installed, or another pass changed it: re-stage)' %% (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %%s missing or not md5 %%s' %% (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (1 << 30)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %%s %%s' %% ('restore' if undo else 'install', p[0]))
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
            print('%%s: %%s %%s' %% (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%%s); %%s' %% (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(st, files, nchunks):
    fl = ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w)
    txt = INSTALL % dict(files=fl, chunks=nchunks)
    compile(txt, 'install.py', 'exec')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(txt)
    open(os.path.join(st, 'INSTALL last call doors 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO last call doors 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')


def stage(out, live_dir=MAPDIR, bots=True, log=print):
    import kl_botsonline, kl_bots_kick_1025 as KK
    live_zip = os.path.join(live_dir, 'F01_Main.zip')
    if md5(live_zip) != LIVE_PIN:
        raise ValueError('%s md5 %s is not the live Last Call zip %s: refusing (re-pin after the new live pass is understood)' % (live_zip, md5(live_zip), LIVE_PIN))
    inp, work = os.path.join(out, '_in'), os.path.join(out, '_work')
    for d in (inp, work):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    src = os.path.join(inp, 'F01_Main.zip')
    shutil.copyfile(live_zip, src)                           # the live file is only ever READ, through this copy
    if md5(src) != LIVE_PIN:
        raise ValueError('the copy of the live zip changed while it was read (md5 %s): the game or another pass is writing it' % md5(src))
    g = os.path.join(work, 'grafted.zip')
    rep = {'live_zip_md5': LIVE_PIN, 'doors': [[n, list(h), list(c)] for n, h, c in DOORS]}
    rep['graft'] = graft(src, g, log)
    final = os.path.join(out, 'F01_Main.zip')
    if bots:
        rep['kick'] = KK.build(g, 'F01', final, log=log)
        if rep['kick'].get('md5_out') is None:               # nothing to kick: the grafted zip is the result
            shutil.copyfile(g, final)
    else:
        shutil.copyfile(g, final)
    rep['md5_plain'] = md5(final)
    rep['chunks'] = chunks(final)
    kl_botsonline.convert(final, os.path.join(out, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(rep['md5_plain'] + '\n')
    for n in INI_FILES:
        data, c = patch_entries(os.path.join(live_dir, n), rep['chunks'])
        if c != 1:
            raise ValueError('%s: %d Entries= lines' % (n, c))
        open(os.path.join(out, n), 'wb').write(data)
    files = {}
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5') + INI_FILES:
        files[n] = (md5(os.path.join(live_dir, n)), md5(os.path.join(out, n)))
    rep['files'] = files
    write_install(out, files, rep['chunks'])
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(inp, ignore_errors=True)                   # the scratch copy of the live zip (~115 MB)
    log('staged %s  plain md5 %s, chunks %d' % (out, rep['md5_plain'], rep['chunks']))
    return rep


# ------------------------------------------------------------------ the offline self-check
def check(out, live_dir=MAPDIR, log=print):
    """Diff the live zip against the staged one. Returns (faults list, facts dict). Reads the live zip through a scratch copy in out\\_chk."""
    import kl_fa_bots as KB, kl_octree as O, kl_prmgraph, kl_glass_conn as GC, kl_gms
    bad, facts = [], collections.OrderedDict()

    def fail(s):
        bad.append(s); log('FAIL ' + s)

    def ok(k, v):
        facts[k] = v; log('  ok  %s: %s' % (k, v))
    scratch = os.path.join(out, '_chk')
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    try:
        lz = os.path.join(scratch, 'live.zip')
        shutil.copyfile(os.path.join(live_dir, 'F01_Main.zip'), lz)
        sz = os.path.join(out, 'F01_Main.zip')
        if md5(lz) != LIVE_PIN:
            fail('live zip md5 %s is not the pin %s' % (md5(lz), LIVE_PIN))
        ok('live md5', md5(lz)); ok('staged md5', md5(sz))
        # 1. members
        zl, zs = zipfile.ZipFile(lz), zipfile.ZipFile(sz)
        if zl.namelist() != zs.namelist():
            fail('member list/order differs')
        diff = []
        for n in zl.namelist():
            same = zl.read(n) == zs.read(n)
            ext = n.rsplit('_Main', 1)[1] if '_Main' in n else n
            if not same:
                diff.append(ext)
                if ext not in CHANGED_OK:
                    fail('member %s changed but the doors pass must not touch it' % n)
        ok('members changed', ' '.join(sorted(diff)))
        sgd = [n for n in zl.namelist() if n.lower().endswith('.sgd')]
        loc = [n for n in zl.namelist() if n.lower().endswith('.loc')]
        for n in sgd + loc:
            if zl.read(n) != zs.read(n):
                fail('%s differs' % n)
        # 2. glass section
        gl, gs_ = GC.section_of(zl, sgd[0]), GC.section_of(zs, sgd[0])
        if not gl:
            fail('the LIVE zip has no HavokShatterGlassConnectivity section')
        elif gl != gs_:
            fail('glass section differs live vs staged')
        else:
            ok('glass section', '%d panes, %d records, identical (.sgd bytes identical)' % (len(gl), sum(len(r) for _, r in gl)))
        # 3. entities by REF
        L, S = KB.Built(lz, 'F01'), KB.Built(sz, 'F01')
        sref = {e.ref: e for e in S.ents}
        lref = {e.ref: e for e in L.ents}
        if len(lref) != len(L.ents) or len(sref) != len(S.ents):
            fail('duplicate REF labels')
        missing = [r for r in lref if r not in sref]
        if missing:
            fail('%d live entities missing in the stage by REF: %s' % (len(missing), missing[:5]))
        wrong = [r for r in lref if r in sref and (sref[r].name != lref[r].name or sref[r].tid != lref[r].tid)]
        if wrong:
            fail('%d entities changed name/class: %s' % (len(wrong), wrong[:5]))
        moved = [r for r in lref if r in sref and any(abs(L.fr[lref[r]][1][i] - S.fr[sref[r]][1][i]) > 1e-3 for i in range(3))]
        if moved:
            fail('%d entities moved: %s' % (len(moved), moved[:5]))
        new = [e for r, e in sref.items() if r not in lref]
        ok('entities', 'live %d, staged %d, all live present by REF with the same name/class/position; %d new' % (len(L.ents), len(S.ents), len(new)))
        # property tree: every live node path survives
        lp, sp = collections.Counter(L.sc.path[1:]), collections.Counter(S.sc.path[1:])
        lost = lp - sp
        if lost:
            fail('%d live .prp node paths lost, e.g. %s' % (sum(lost.values()), list(lost)[:3]))
        ok('.prp nodes', 'live %d, staged %d, none lost' % (len(L.sc.path) - 1, len(S.sc.path) - 1))
        # 4. slot ids
        sl0, sl1 = L.scene.slots(), S.scene.slots()
        ids = {sl0[e] + 2: sl1[sref[e.ref]] + 2 for e in L.ents if e.ref in sref}
        if len(set(ids.values())) != len(ids):
            fail('slot remap is not one-to-one')
        newids = {sl1[e] + 2 for e in new}
        lo, ls, lc = O.Oct.parse(L['.oct']), O.RoomIndex.parse(L['.rmi']), O.RoomIndex.parse(L['.rmc'])
        so, ss, sc_ = O.Oct.parse(S['.oct']), O.RoomIndex.parse(S['.rmi']), O.RoomIndex.parse(S['.rmc'])
        ids[1] = 1
        try:
            mo, ms, mc = O.remap_ids(lo, ids), O.remap_ids(ls, ids), O.remap_ids(lc, ids)
        except KeyError as e:
            fail('a live tree id has no staged slot: %s' % e)
            mo = ms = mc = None
        n_items = 0
        if mo is not None:
            if len(mo.rooms) != len(so.rooms):
                fail('room count %d -> %d' % (len(mo.rooms), len(so.rooms)))
            for ri, (ra, rb) in enumerate(zip(mo.rooms, so.rooms)):
                for ti, (ta, tb) in enumerate(zip(ra, rb)):
                    a_ = collections.Counter(it[0] for it in (ta.items if ta else ()))
                    b_ = collections.Counter(it[0] for it in (tb.items if tb else ()))
                    n_items += sum(a_.values())
                    if a_ - b_:
                        fail('room %d tree %d: %d live ids lost' % (ri, ti, sum((a_ - b_).values())))
                    extra = b_ - a_
                    if any(k not in newids for k in extra):
                        fail('room %d tree %d: ids added that are not new entities' % (ri, ti))
            for nm, a_, b_ in (('.rmi', ms, ss), ('.rmc', mc, sc_)):
                ka = collections.Counter((b.room, b.second) for b in a_.boxes)
                kb = collections.Counter((b.room, b.second) for b in b_.boxes)
                if ka - kb:
                    fail('%s: %d boxes lost/renumbered wrongly' % (nm, sum((ka - kb).values())))
                if any(k[0] not in newids and k[0] != 1 for k in (kb - ka)):
                    fail('%s: boxes added for a room that is not new' % nm)
            ok('slot ids', '%d live ids -> 1:1 remap by REF; %d tree items + .rmi/.rmc boxes all carried over; additions only new entities (%d new ids)' % (len(ids) - 1, n_items, len(newids)))
        fa = KB.room_sets_check(S.scene, so, ss, sc_)
        if fa:
            fail('room_sets_check on the stage: %s' % fa)
        else:
            ok('room_sets_check', 'staged trees/boxes name only entities of the right class')
        if S.scene.check():
            fail('kl_scene.check: %s' % S.scene.check()[:3])
        # 5. .prm chunks: every live chunk survives (root chunks may be re-pointed at a moved .oct record, +0x1c only)
        pl, ps = kl_prmgraph.read(L['.prm'], 'dd'), kl_prmgraph.read(S['.prm'], 'dd')
        repoint = lost_c = 0
        for i, c in enumerate(pl.chunks):
            d = ps.chunks[i] if i < len(ps.chunks) else None
            if d == c:
                continue
            if d is not None and len(c) == 64 and len(d) == 64 and c[:0x1c] == d[:0x1c] and c[0x20:] == d[0x20:]:
                repoint += 1
            else:
                lost_c += 1
        if lost_c:
            fail('%d live .prm chunks changed (not just a root re-point)' % lost_c)
        ok('.prm chunks', 'live %d, staged %d (+%d), %d root chunks re-pointed to moved .oct records, 0 other changes' % (len(pl.chunks), len(ps.chunks), len(ps.chunks) - len(pl.chunks), repoint))
        # 6. Entries= / ini / bots / md5 files
        for n in INI_FILES:
            m = re.search(rb'(?m)^Entries\s*=\s*(\d+)', open(os.path.join(out, n), 'rb').read())
            lm = re.search(rb'(?m)^Entries\s*=\s*(\d+)', open(os.path.join(live_dir, n), 'rb').read())
            if int(lm.group(1)) != len(pl.chunks):       # NOT a doors fault: the live inis are already stale (pics pass +72 chunks, 11-06); the stage fixes them
                facts['live ' + n + ' stale'] = 'Entries=%s vs live chunk count %d' % (lm.group(1).decode(), len(pl.chunks))
                log('  WARN live %s Entries=%s != live chunk count %d (pre-existing; the staged ini carries the true count)' % (n, lm.group(1).decode(), len(pl.chunks)))
            if int(m.group(1)) != len(ps.chunks):
                fail('%s Entries=%s != staged chunk count %d' % (n, m.group(1).decode(), len(ps.chunks)))
            a1 = open(os.path.join(live_dir, n), 'rb').read().decode('latin-1').splitlines()
            b1 = open(os.path.join(out, n), 'rb').read().decode('latin-1').splitlines()
            if len(a1) != len(b1) or sum(1 for x, y in zip(a1, b1) if x != y) != 1:
                fail('%s differs from the live ini in more than the Entries line' % n)
        ok('Entries=', 'KLJoin.ini and KLGuns.ini = %d = staged chunk count (live %d), only that line changed' % (len(ps.chunks), len(pl.chunks)))
        bz = os.path.join(out, 'F01_Main.bots.zip')
        zb = zipfile.ZipFile(bz)
        dd_ = [n for n in zs.namelist() if zs.read(n) != zb.read(n)]
        if zs.namelist() != zb.namelist() or [n.rsplit('_Main', 1)[1] for n in dd_] != ['.prp']:
            fail('bots zip differs from the plain zip in %s (want only .prp)' % dd_)
        if open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip() != md5(sz):
            fail('bots.base.md5 is not the md5 of the plain zip')
        ok('bots sibling', 'differs from the plain zip only in .prp; base.md5 = plain md5')
        # 7. doors
        doors = [n for n in S.sc.path[1:] if re.search(r'KL_Interact!1\\KL_Door_\d+$', n)]
        kicks = [n for n in S.sc.path[1:] if n.endswith('KickDoorBehaviour_PosInfo')]
        tail = lambda sc_, key: sum(1 for pth in sc_.path[1:] if key.lower() in pth.rsplit(chr(92), 1)[-1].lower())
        kr_l, kr_s = tail(L.sc, 'KickDoorBehaviourRout'), tail(S.sc, 'KickDoorBehaviourRout')
        pb_l, pb_s = tail(L.sc, 'PathBlocker'), tail(S.sc, 'PathBlocker')
        if len(doors) != len(DOORS):
            fail('%d KL_Door groups (want %d)' % (len(doors), len(DOORS)))
        if kr_s <= kr_l:
            fail('no kick steps added (%d -> %d)' % (kr_l, kr_s))
        ok('doors', '%d kick doors (%s); KickDoorBehaviourRout nodes live %d -> staged %d; PathBlocker nodes live %d -> staged %d' % (
            len(doors), ','.join(n for n, _h, _c in DOORS), kr_l, kr_s, pb_l, pb_s))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    log('SELFCHECK ' + ('PASS' if not bad else 'FAIL (%d)' % len(bad)))
    return bad, facts


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('stage', 'check'):
        print(__doc__)
        return 2
    if a[0] == 'stage':
        stage(opt('--out', OUT), opt('--live', MAPDIR), bots='--no-bots' not in a)
        return 0
    bad, _ = check(opt('--out', OUT), opt('--live', MAPDIR))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
