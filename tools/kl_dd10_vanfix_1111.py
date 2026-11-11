#!/usr/bin/env python3
r"""kl_dd10_vanfix_1111.py - Flat Raid (DD10 = Dog Days L05 in slot F07): the escape van must never kill a heister at the street and never blow up from shooting/scripted hits.
Stage built from the LIVE files (2026-11-11, offline, stage only; nothing is installed, no game is launched).

OWNER (2026-11-11): "all u gotta know is the flat raid van spawns in and blows up its supposed to be a cutscene drive". First spawn died 3 of 3, ~18-25 s into the round,
KILLED BY <own name>, FA_DieFromSelf from 0x5008dc, x ~9100..9540 z ~936, van state 0 in the log all along, no hook van action (klescort/klbotfill write only upwards / only states 1..4).

WHAT IS MEASURED (live F07 e822d75d, node ids of THIS file; older tools are +17 lower):
 - the ONLY FA_DieFromSelf source in the map is V_Van_00\KillBox (node 21957): 'CheckInsideEnter', 'FA_DieFromSelf'. Its fields equal stock F07's (stock vans kill whoever they run over).
   Box half 90 x 100 x 56 (local), turned 90 deg about y, local centre (1.2, 92.5, 168.2) = the van's nose; it rides the van's key frames.
 - the van group (21803) is hidden from load; the approach box (node 22144, x 7500..9100, z 650..1550) shows it via ActivateGeom node 22000 on every heister enter edge.
   The death x (9060..9125 extrapolated from the log) is that box's EAST edge (x 9100); Crash_03 of the van is x 9170 -> 9499, z 1100 -> 980 (same patch, z ~936..980 borderline the KillBox z 940..1120).
 - damage reaches the van through RelayAnimatedVehicleHit on Body_Main (21943), Door_Hatchback (21960), Door_Right_Slide (21961) -> ZAnimatedVehicle 21982; the crash legs + Relay_VanExplotion
   (FX0900 gas explosion) are the van's destroyed path. The hook's shields cover vehicle states 1..4 only, never state 0 (= the state the shown, parked van is in), HealFloor only heals.
 - bench evidence: the 1st van was 3600/9600 AT the call (hit in state 0); a seat on the drive-in lane died to the nose KillBox.
WHAT IS GUESS: that the first-spawn death is the nose KillBox meeting the player when the approach box shows the van (the exact frame/pose at the show was NOT read: no log line has the van
 pose or a shown flag). Whatever pose the van is in, the stage removes both killers a van can be: the KillBox and the destroyed path.

PARTS (--parts, default killbox,nohit):
  killbox  node 21957: half 90/100/56 -> 1/1/1 cm and local y 92.5 -> -400 (4 m under the street). Nothing can be 'inside' it: the van no longer kills anybody it touches (the PathBlocker
           and the van's body collision still stand). GUESS: a box moved 4 m down inside its moving parent is still fine for the engine (bounds are BOUNDING_Static).
  nohit    the three RelayAnimatedVehicleHit controllers (Body_Main, Door_Hatchback, Door_Right_Slide) lose the controller (deleted, as kl_dm02shop_1110 deletes one): bullets / blasts relay no hit to the ZAnimatedVehicle, so its
           health never drops from the scene side, the controller never reaches its crash legs and Relay_VanExplotion never fires. GUESS: a damage-less van body is legal (the ZAnimatedVehicle has no controllers of its own). The hook's own [VanBlow] blow-up after the drive-out (empty van) is hook code and stays.
Kept: show-on-approach (22144 -> 22000), the call (otrExitLevel 22004), key frames, boarding, audio, cameras, loot, KLJoin.ini. Changes ONLY the .prp of the plain and the bots zip.

  python tools/kl_dd10_vanfix_1111.py stage [--parts killbox,nohit] [--in-dir <map dir>] [--out-root C:/kl_build_1024]
  python tools/kl_dd10_vanfix_1111.py check [--in-dir ...] [--out-root ...] [--no-undo]
Never installs anything. REFUSES unless the live files are the expected md5s and the nodes hold the pre-edit values.
Undo: UNDO.bat (python install.py --undo): every file back byte for byte."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, types, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DD10')
OUT_ROOT = 'C:/kl_build_1024'
MAP, SLOT = 'DD10', 'F07'
NAME, TAG = 'dd10vanfix_1111', '.before-dd10vanfix1111'
TEMPLATE = os.environ.get('KL_VANFIX_TEMPLATE', 'C:/kl_build_1024/dd10doorfix_1109/kit/install.py')
ZIP, BOTS, BASE = 'F07_Main.zip', 'F07_Main.bots.zip', 'F07_Main.bots.base.md5'
LIVE_MD5 = {ZIP: 'e822d75d689c8b8e18f8dd8ffdbc633a', BOTS: 'f16b4bc10930e743a3cc3a084025c50d', BASE: '0a1c00d04278f0ee0c38d14ff6e4e033'}
R = 'ROOT' + chr(92)
VAN = R + 'Animation/F07/F07_Escape_Vehicle_01.zip' + chr(92) + 'EscapeVehicle_Animation_F07' + chr(92)
KILLBOX = VAN + 'F07_Escape_Vehicle_01' + chr(92) + 'V_Van_00' + chr(92) + 'KillBox'
HITS = [VAN + 'F07_Escape_Vehicle_01' + chr(92) + 'V_Van_00' + chr(92) + x for x in ('Body' + chr(92) + 'Body_Main', 'Door_Hatchback', 'Door_Right_Slide')]
VAN_ENT = VAN + 'F07_EscapeVan_01'
KB_HALF_OLD, KB_POS_OLD = [89.81559753417969, 100.0, 55.97740173339844], [1.1981600522994995, 92.53379821777344, 168.18899536132812]
KB_HALF_NEW, KB_Y_NEW = [1.0, 1.0, 1.0], -400.0
PARTS_ALL = ('killbox', 'nohit')


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _mods():
    global kl_fa, F, A, J, SK
    import kl_fa, kl_fa_bots as F, kl_fa_author as A, kl_prpjoin as J, kl_skyline_1108 as SK


def kb_values(sc, k):
    lab = J.labels('dd', sc.cls(k))
    vv = kl_fa.node_values(sc, k)
    return [float(vv[lab.index('ZBoxPrimitive[%d]' % i)]) for i in range(3)], [float(x) for x in vv[lab.index('ZGEOM[2]')]]


def hit_target(sc, k):
    for kk, i, v in kl_fa.controllers(sc, 'RelayAnimatedVehicleHit'):
        if kk == k:
            return v[0]
    raise SystemExit('REFUSED: %s has no RelayAnimatedVehicleHit' % sc.path[k])


def edit_scene(B, parts=PARTS_ALL, log=print):
    sc = B.sc
    import kl_graft
    # pre-edit checks first (REFUSE unless this is the live state)
    kk = A.node_of(sc, KILLBOX)
    if 'killbox' in parts:
        if not [c for c in kl_fa.controllers(sc, 'KillBox') if c[0] == kk]:
            raise SystemExit('REFUSED: %s has no KillBox controller' % KILLBOX)
        half, pos = kb_values(sc, kk)
        if [round(x, 3) for x in half] != [round(x, 3) for x in KB_HALF_OLD] or [round(x, 3) for x in pos] != [round(x, 3) for x in KB_POS_OLD]:
            raise SystemExit('REFUSED: the nose KillBox is not the pre-edit one: half %r pos %r' % (half, pos))
    hk = [A.node_of(sc, n) for n in HITS]
    if 'nohit' in parts:
        for k in hk:
            if hit_target(sc, k) != VAN_ENT:
                raise SystemExit('REFUSED: %s RelayAnimatedVehicleHit does not target the van entity: %r' % (sc.path[k], hit_target(sc, k)))
    done = []
    if 'killbox' in parts:
        lab = J.labels('dd', sc.cls(kk))

        def fn(us):
            for i in range(3):
                A.setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), KB_HALF_NEW[i])
            A.setv(sc, us, lab.index('ZGEOM[2]'), [KB_POS_OLD[0], KB_Y_NEW, KB_POS_OLD[2]])
        kl_graft.edit(sc.nodes[kk], 'props', fn)
        log('  KillBox node %d: half %s -> %s, local y %.1f -> %.1f' % (kk, [round(x, 1) for x in KB_HALF_OLD], KB_HALF_NEW, KB_POS_OLD[1], KB_Y_NEW))
        done.append(kk)
    if 'nohit' in parts:
        for k in hk:
            del sc.nodes[k]['ctrls'][A.ctrl_of(sc, k, 'RelayAnimatedVehicleHit')]      # precedent: kl_dm02shop_1110 deletes a controller the same way
            log('  RelayAnimatedVehicleHit node %d: controller removed' % k)
            done.append(k)
    return done


def patch_zip(src, dst, parts=PARTS_ALL, log=print):
    B = F.Built(src)
    edit_scene(B, parts, log)
    new = dict(B.files)
    new[B.ext['.prp']] = B.sc.p.serialize()
    with zipfile.ZipFile(src) as z:
        order = [i.filename for i in z.infolist()]
    SK.write_zip(dst, [(n, new[n]) for n in order], SK.tex_level(src))


KNOWN_ARGS = """    known = ('--undo', '--dry', '--skip-run-check', '--game', '--root')
    vals = [a[i + 1] for i, x in enumerate(a) if x in ('--game', '--root') and i + 1 < len(a)]
    bad = [x for x in a if x not in known and x not in vals]
    if bad:
        print('REFUSED: unknown argument(s) %s' % bad)
        return 2
"""


def make_install(out, stage_md5, template_text=None):
    t = template_text if template_text is not None else open(TEMPLATE, encoding='utf-8').read()
    rows = ", ".join("('%s', '%s', '%s')" % (n, LIVE_MD5[n], stage_md5[n]) for n in (ZIP, BOTS, BASE))
    t, k = re.subn(r"^FILES = \[.*?\]\n", lambda m: "FILES = [" + rows + "]\n", t, flags=re.S | re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES line')
    t, k = re.subn(r"^MAP, TAG = '[A-Z0-9]+', '[^']+'", "MAP, TAG = '%s', '%s'" % (MAP, TAG), t, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no single MAP, TAG line')
    t, k = re.subn(r'^r?"""Installs / undoes[^\n]*\n', 'r"""Installs / undoes DD10 VAN FIX 1111 on the live DD10 files: the van nose KillBox is disarmed and its hit relays get no target (tools/kl_dd10_vanfix_1111.py).\n', t, count=1, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no docstring head')
    t, k = re.subn(r'^def main\(a\):\n', lambda m: m.group(0) + KNOWN_ARGS, t, count=1, flags=re.M)
    if k != 1:
        raise SystemExit('REFUSED: template has no main(a)')
    return t


README = """DD10 VAN FIX 1111 (Flat Raid, slot F07) - staged, NOT installed. (recommended on)
Tool: tools/kl_dd10_vanfix_1111.py (+ _test.py).   Parts built: %(parts)s
Live now (pinned): F07_Main.zip e822d75d, bots f16b4bc1, bots.base.md5 0a1c00d0 (KLJoin.ini NOT touched).
Staged:            F07_Main.zip %(zip)s, bots %(bots)s, bots.base.md5 %(base)s.

Owner 11-11: 'the flat raid van spawns in and blows up, its supposed to be a cutscene drive'; died on the first spawn 3 of 3 (FA_DieFromSelf, own name, x ~9100..9540 z ~936).
MEASURED: the only FA_DieFromSelf source in the map is the van's nose KillBox (node 21957); the damage path to the crash legs + gas explosion is RelayAnimatedVehicleHit (nodes 21943/21960/21961).
GUESS: the death is that KillBox meeting the player when the approach box (east edge x 9100) shows the van; not proven (no log carried the van pose).
What changes (.prp of the plain and the bots zip only): KillBox half 1 cm and 4 m under the street; the three RelayAnimatedVehicleHit controllers are deleted.
Unchanged: show on approach, the call (otrExitLevel), the key-framed drive-in / wait / drive-out, boarding, loot, KLJoin.ini. The hook's [VanBlow] blow-up of an EMPTY van after the drive-out stays.
Install: python install.py (game closed; backups *.before-dd10vanfix1111 next to the files).   Undo: UNDO.bat (python install.py --undo), byte exact.
Install order: pinned to the CURRENT live zip; if another DD10 kit goes in first, re-stage (the pins refuse otherwise).
Bench: first spawn (run west to x 8000), later spawn, round 2, call + board, shoot the parked van.
"""


def stage(in_dir, out_root, parts=PARTS_ALL, log=print):
    for n in (ZIP, BOTS, BASE):
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != LIVE_MD5[n]:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DD10 changed: re-stage)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', LIVE_MD5[n]))
    if open(os.path.join(in_dir, BASE)).read().strip() != fmd5(os.path.join(in_dir, ZIP)):
        raise SystemExit('REFUSED: the live bots.base.md5 is not the md5 of the live plain zip')
    out = os.path.join(out_root, NAME)
    os.makedirs(out, exist_ok=True)
    for old in (ZIP, BOTS, BASE):
        if os.path.exists(os.path.join(out, old)):
            os.remove(os.path.join(out, old))
    log('stage -> %s' % out)
    for n in (ZIP, BOTS):
        log(n)
        patch_zip(os.path.join(in_dir, n), os.path.join(out, n), parts, log)
    with open(os.path.join(out, BASE), 'w', newline='\n') as f:
        f.write(fmd5(os.path.join(out, ZIP)) + '\n')
    sm = {n: fmd5(os.path.join(out, n)) for n in (ZIP, BOTS, BASE)}
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(make_install(out, sm))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    open(os.path.join(out, 'README.txt'), 'w', newline='\n').write(README % dict(zip=sm[ZIP][:8], bots=sm[BOTS][:8], base=sm[BASE][:8], parts=','.join(parts)))
    json.dump(dict(md5=sm, live=LIVE_MD5, tag=TAG, parts=list(parts)), open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    for n in sorted(x for x in os.listdir(out) if os.path.isfile(os.path.join(out, x))):
        log('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return out


def check(in_dir, out_root, parts=PARTS_ALL, log=print, undo_rehearsal=True):
    out = os.path.join(out_root, NAME)
    bad = []

    def need(c, msg):
        log('  %s %s' % ('ok  ' if c else 'FAIL', msg))
        if not c:
            bad.append(msg)
    for n in (ZIP, BOTS):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
            changed = sorted(m.rsplit('_Main', 1)[1] for m in zb.namelist() if zb.read(m) != zs.read(m))
            need(changed == ['.prp'], '%s: only .prp differs (changed: %s)' % (n, changed))
            pa, pb = zb.read([m for m in zb.namelist() if m.endswith('.prp')][0]), zs.read([m for m in zs.namelist() if m.endswith('.prp')][0])
            need(len(pb) <= len(pa) and (len(pb) == len(pa)) == ('nohit' not in parts), '%s: .prp %d -> %d bytes (3 controllers deleted: shorter)' % (n, len(pa), len(pb)))
            diff = [i for i in range(min(len(pa), len(pb))) if pa[i] != pb[i]]
            need(len(diff) > 0, '%s: .prp %d bytes differ, span %s' % (n, len(diff), (diff[0], diff[-1]) if diff else None))
        Bb, Bs = F.Built(base), F.Built(stg)
        need(F.Prp(Bs['.prp']).serialize() == Bs['.prp'], '%s: .prp round trip' % n)
        kk = A.node_of(Bs.sc, KILLBOX)
        hk = [A.node_of(Bs.sc, x) for x in HITS]
        want = set()
        if 'killbox' in parts:
            h, pos = kb_values(Bs.sc, kk)
            need(h == KB_HALF_NEW and abs(pos[1] - KB_Y_NEW) < 1e-3 and abs(pos[0] - KB_POS_OLD[0]) < 1e-3, '%s: KillBox half %s local pos %s' % (n, h, [round(x, 2) for x in pos]))
            want.add(kk)
        if 'nohit' in parts:
            need(all(not [c for c in kl_fa.controllers(Bs.sc, 'RelayAnimatedVehicleHit') if c[0] == k] for k in hk) and len(kl_fa.controllers(Bs.sc, 'RelayAnimatedVehicleHit')) == len(kl_fa.controllers(Bb.sc, 'RelayAnimatedVehicleHit')) - 3, '%s: the 3 RelayAnimatedVehicleHit controllers are gone (others kept)' % n)
            want |= set(hk)
        diffn = [j for j in range(1, len(Bb.sc.nodes)) if Bb.sc.nodes[j]['props'] != Bs.sc.nodes[j]['props'] or len(Bb.sc.nodes[j]['ctrls']) != len(Bs.sc.nodes[j]['ctrls'])
                 or any(x != y for x, y in zip(Bb.sc.nodes[j]['ctrls'], Bs.sc.nodes[j]['ctrls']))]
        need(set(diffn) == want, '%s: exactly nodes %s differ (got %s)' % (n, sorted(want), diffn))
        need(len(Bb.sc.nodes) == len(Bs.sc.nodes), '%s: node count unchanged (slots stay)' % n)
        for nm in (R + 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn', R + 'Gameplay!EscapeSetup!otrExitLevel', R + 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT', VAN[:-1]):
            j = A.node_of(Bs.sc, nm)
            need(Bb.sc.nodes[j]['props'] == Bs.sc.nodes[j]['props'] and Bb.sc.nodes[j]['ctrls'] == Bs.sc.nodes[j]['ctrls'], '%s: %s untouched' % (n, nm.rsplit(chr(92), 1)[-1]))
        need(Bs.files[Bs.ext['.gms']] == Bb.files[Bb.ext['.gms']] if hasattr(Bs, 'files') else True, '%s: .gms byte-equal' % n)
    need(open(os.path.join(out, BASE)).read().strip() == fmd5(os.path.join(out, ZIP)), 'bots.base.md5 = md5 of the plain staged zip')
    with zipfile.ZipFile(os.path.join(in_dir, ZIP)) as a, zipfile.ZipFile(os.path.join(in_dir, BOTS)) as b, zipfile.ZipFile(os.path.join(out, ZIP)) as c, zipfile.ZipFile(os.path.join(out, BOTS)) as d:
        ld = [m for m in a.namelist() if a.read(m) != b.read(m)]
        sd = [m for m in c.namelist() if c.read(m) != d.read(m)]
        need(ld == sd, 'plain and bots zips differ only in %s (live %s)' % (sd, ld))
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in (ZIP, BOTS, BASE):
        need(("'%s', '%s', '%s')" % (n, LIVE_MD5[n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, LIVE_MD5[n][:8], fmd5(os.path.join(out, n))[:8]))
    if undo_rehearsal:
        sg = tempfile.mkdtemp(prefix='vanfixgame_', dir=out)
        try:
            d = os.path.join(sg, 'KLExpansion', 'Maps', MAP)
            os.makedirs(d)
            names = [x for x in os.listdir(in_dir) if x in LIVE_MD5 or x == 'KLJoin.ini']
            for n in names:
                shutil.copyfile(os.path.join(in_dir, n), os.path.join(d, n))
            before = {n: fmd5(os.path.join(d, n)) for n in names}
            run = lambda *a: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--game', sg, '--skip-run-check'] + list(a), capture_output=True, text=True)
            r = run('--dry')
            need(r.returncode == 0, 'install.py --dry rc %d' % r.returncode)
            r = run()
            need(r.returncode == 0 and all(fmd5(os.path.join(d, n)) == (fmd5(os.path.join(out, n)) if n in LIVE_MD5 else before[n]) for n in names) and all(os.path.isfile(os.path.join(d, n + TAG)) for n in LIVE_MD5), 'scratch install lands the staged md5s, backups *%s made, KLJoin.ini untouched' % TAG)
            r2 = run()
            need(r2.returncode != 0, 'a second install is refused')
            r = run('--undo')
            need(r.returncode == 0 and {n: fmd5(os.path.join(d, n)) for n in names} == before and not any(os.path.exists(os.path.join(d, n + TAG)) for n in LIVE_MD5), 'scratch undo restores every file byte for byte')
        finally:
            shutil.rmtree(sg, ignore_errors=True)
    log('CHECK %s (%d failures)' % ('PASS' if not bad else 'FAIL', len(bad)))
    return not bad


def report(in_dir, log=print):
    sc = F.Built(os.path.join(in_dir, ZIP)).sc
    kk = A.node_of(sc, KILLBOX)
    log('  KillBox node %d half/pos %s' % (kk, kb_values(sc, kk)))
    for n in HITS:
        log('  hit relay %s -> %s' % (n.rsplit(chr(92), 1)[-1], hit_target(sc, A.node_of(sc, n))[-30:]))


def main(a):
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('stage', 'check', 'report'):
        print(__doc__)
        return 2
    _mods()
    in_dir, out_root = opt('--in-dir', LIVE), opt('--out-root', OUT_ROOT)
    if a[0] == 'report':
        report(in_dir)
        return 0
    parts = tuple(opt('--parts', ','.join(PARTS_ALL)).split(','))
    if not set(parts) <= set(PARTS_ALL):
        print('REFUSED: unknown part in %s' % (parts,))
        return 2
    if a[0] == 'stage':
        stage(in_dir, out_root, parts)
    return 0 if check(in_dir, out_root, parts, undo_rehearsal='--no-undo' not in a) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
