r"""kl_dm02combo_1110.py - DM02 (Late Night Opening, slot F02): ONE combined stage = shutter use-prompt + jeweller door/vault glass + shop dressing relist.
2026-11-10. OFFLINE: reads the live DM02 zips, writes a stage; nothing is installed, the game is not started.

OWNER (2026-11-10, playing): "fix the door already, I want the glass back, just make the AI heisters shoot it open" and "no prompt to open shutter, make it like a
shop, take assets from Dog Days, there are shops in it".  Chains the two earlier passes on the SAME live zip (43c088c2 / bots bb8f04cb):
  1. kl_dm02shop_1110.build        shutter 'Lift Door' use prompt back, CoopAirlock lists back, 90 s timer off            (.prp)
  2. kl_dm02doorglass_1110.build   Hertzer doors D1..D4 opened by relay, vault glass Whole04 x2 back + fallback timer       (.prp .gms .HVK)
  3. relist (this file)            the shop dress props go from the ROOT room tree into the shop's own room tree          (.oct only)

DOOR (decision): the grey leaf IN the Hertzer & Sons doorway is the kick-door leaf KL_Door_3 / KL_Door_4 (REF 34449 / 34472, model 0xe404 = plain F03 slab).
  doorglass_1110 swings it open on a timer, which leaves the slab standing open at the frame (still grey, still visible, and its body only leaves the doorway if
  the type-4 body follows the node: GUESS 4 there). This stage ALSO hides the leaf (flag 0x400, as D1/D2 already are): the doorway is empty whichever way the
  swing goes. The swing stays so the collision/path block still goes with the Pathblocker 'eUnblock'. Risk: if the swing does not move the body, an invisible
  blocker stays in the jewellers doorway (the bench shows it; UNDO / variant 'nodress' do not change that, --hide-doors "1,2" gives the old look).
  Rejected: cutting the door's collision from the .HVK: a type-4 (dynamic) body is not in the static list the doorglass pass proves; editing it is a new, unproven
  HVK write, the swing + hide is data the engine already runs for D1/D2.

GLASS: the glass breaks on its own as a FALLBACK after --glass-delay (default 60 s); the hook (klhook/klbotglass.c, separate agent) is meant to make bots shoot it first.

DRESS (what was found, MEASURED on the live zip): the five shops are the rooms Corridore_201a (shop 4), _201b (shop 1), _201c (shop 3), _201d (shop 2) and
  Corridore_101b (shop 5, floor 1), reached through the Atrium shutters (rmi boxes: x -7000..-2000 / 2000..6500, one small box per shop; the huge Backdrop box
  also covers them). Their stock content is 6 items each (floor, ceiling, walls). The KLDress* props (kl_dm02_coop_1026: rigid copies of DM02's own upstairs shop
  props) and the KLShop0N Montre_Desk props were listed in ROOT room tree 0 / 1 (room 0), NOT in the corridor room that holds the camera in the shop.
  Tree-0 rule: a room draws what its own trees list. This stage MOVES (an entity is in one tree only) those items to [shop room][same tree index]; ids are SLOT ids and do
  not change (no entity added/removed), the item box is the same world box re-quantised into the target tree (kl_octree.build_tree + join_trees, as kl_dm01b_undoor_1109).
  The room trees change size, so every .oct record moves: the .prm type-7 chunks (+0x1c = record offset) are repointed with kl_map_shift.repoint_prm (A1SHIFT2 crashed without it);
  check_passes A (oct-offsets) proves it.
  GUESS: the camera in a shop draws that room's trees (it draws the shop floor and walls that way); root-room items are not drawn from inside a corridor room.
  NOT done: grafting Dog Days' own F04 shop props (Shelf_A, Counter, Rack_*): that needs a model/material/texture graft (kl_prmgraph + kl_texmat) and is only worth it
  once the relist is benched (if the existing props show, more kits are cheap; if they do not, new props would not either).

usage (from tools/):
  python kl_dm02combo_1110.py stage [--out C:\kl_build_1024\dm02shop_1110\combined] [--live <Maps\DM02>] [--glass-delay 60] [--door-delay 1.5] [--hide-doors 1,2,3,4]
  python kl_dm02combo_1110.py check <zip> --base <F02_Main.zip of the door/glass output>        (relist check only)
"""
import collections, hashlib, json, os, shutil, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_gms, kl_octree as O
import kl_fa_bots as F
import kl_botsonline
import kl_dm02shop_1110 as PROMPT
import kl_dm02doorglass_1110 as DG

MAPDIR = DG.MAPDIR
OUT = r'C:\kl_build_1024\dm02shop_1110\combined'
TAG = '.before-dm02combo1110'
LIVE_PIN = '43c088c2d0ac4131a2f8d6a1667f965a'
LIVE_BOTS_PIN = 'bb8f04cb6b8460b5f34df021da629c9f'
LIVE_BASE_PIN = '43c088c2d0ac4131a2f8d6a1667f965a'
DEFAULT_GLASS_DELAY = 60.0
DEFAULT_DOOR_DELAY = 1.5
DEFAULT_HIDE = (1, 2, 3, 4)
VARIANTS = ('full', 'nodress')
DEFAULT_VARIANT = 'full'
# shop number (name KLDress<n>_ / KLShop0<n>_) -> room index in the .oct (MEASURED: item centres lie in exactly these corridor rmi boxes)
SHOP_ROOM = {1: 13, 2: 15, 3: 14, 4: 12, 5: 7}
SHOP_ROOM_NAME = {13: b'M02_FA_A_Ins_Corridore_201b', 15: b'M02_FA_A_Ins_Corridore_201d', 14: b'M02_FA_A_Ins_Corridore_201c', 12: b'M02_FA_A_Ins_Corridore_201a', 7: b'M02_FA_A_Ins_Corridore_101b'}
TREES = (0, 1)                                    # props (category 1) and lights (category 2); groups (tree 3) are not moved

GUESSES = [
    "the camera inside a shop draws only the trees of its own room (Corridore_20xx), so the dress props listed in the ROOT room never showed; listed in the shop room they draw",
    "a prop or light listed in a corridor room's tree is drawn / lights the same as the stock floor and wall objects of that room (the lights keep their list-pool links: only the room list moves)",
    "the item box re-quantised into the corridor tree's frame (origin / scale of that tree) stays inside the loose cell of its node (Tree.check() proves the rule offline, the engine walk is the stock one)",
    "a hidden (0x400) KL leaf in the Hertzer doorway that swings open leaves the doorway empty and free: if the type-4 body does not follow the swing, an invisible blocker stays",
    "all guesses of kl_dm02shop_1110 (PlayerAction prompt) and kl_dm02doorglass_1110 (relay shatters the glass, shatter drops its collision, MatPosAnimProxy accepts the delay forward) apply unchanged",
]


def md5(p):
    return DG.md5(p)


def _shop_of(name):
    n = name.decode('latin1')
    for pre in ('KLDress', 'KLShop0'):
        if n.startswith(pre) and n[len(pre)].isdigit():
            return int(n[len(pre)])
    return None


# ---------------------------------------------------------------- relist
def relist(src_zip, dst_zip, rep, log=print):
    """Move the shop dress items from the root room trees to the shop rooms. Only the .oct and the .prm (type-7 record offsets) change."""
    B = F.Built(src_zip, 'F02')
    A = B.scene
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(A, octx, rmi, rmc)
    slot = A.slots()
    byid = {s + 2: e for e, s in slot.items()}
    ents0, ro = kl_graft.rooms_of(A)
    if len(ro) != len(octx.rooms):
        raise ValueError('rooms_of %d vs .oct %d' % (len(ro), len(octx.rooms)))
    for ri, nm in SHOP_ROOM_NAME.items():
        if ro[ri] is None or ro[ri].name != nm:
            raise ValueError('room %d is %r, expected %r' % (ri, ro[ri] and ro[ri].name, nm))
    octn = O.Oct.parse(B['.oct'])
    moved = collections.OrderedDict()                 # (room, tree) -> [(id, lo, hi)]
    drop = collections.defaultdict(set)
    for ti in TREES:
        t = octx.rooms[0][ti]
        for it in t.items:
            e = byid[it[0]]
            shop = _shop_of(e.name)
            if shop is None:
                continue
            ri = SHOP_ROOM[shop]
            lo, hi = t.world(it[1:4]), t.world([v + 1 for v in it[4:7]])
            moved.setdefault((ri, ti), []).append((it[0], lo, hi))
            drop[ti].add(it[0])
    if not moved:
        raise ValueError('no KLDress / KLShop item in the root room trees (already relisted? wrong zip?)')
    for ti in TREES:
        if drop[ti]:
            ids = {it[0]: it[0] for it in octx.rooms[0][ti].items}
            octn.rooms[0][ti] = O.remap_tree(octx.rooms[0][ti], ids, drop[ti])
            octn.rooms[0][ti].check()
    made = collections.OrderedDict()
    for (ri, ti), items in sorted(moved.items()):
        t = octx.rooms[ri][ti]
        if t is None:                                 # an empty slot: take the frame of the room's tree 0
            base = octx.rooms[ri][0]
            if base is None:
                raise ValueError('room %d has no tree to take a frame from' % ri)
            new = O.build_tree(items, base.origin, base.scale)
        else:
            new = O.join_trees(t, O.build_tree(items, t.origin, t.scale))
        new.check()
        octn.rooms[ri][ti] = new
        made['%d/%d' % (ri, ti)] = len(items)
    post = F.room_sets_check(A, octn, rmi, rmc)
    if post != pre:
        raise ValueError('room set check changed: %s -> %s' % (pre, post))
    data = octn.pack()
    back = O.Oct.parse(data)
    if back.pack() != data:
        raise ValueError('.oct does not round-trip')
    files = dict(B.files)
    files[B.ext['.oct']] = data
    # every .oct record moves (the room trees changed size): the .prm type-7 chunks hold the record offsets (kl_map_shift.repoint_prm)
    import kl_map_shift as MS
    prm, nrep = MS.repoint_prm(B['.prm'], octx.record_refs(), back.record_refs())
    files[B.ext['.prm']] = prm
    rep_prm = nrep
    os.makedirs(os.path.dirname(dst_zip), exist_ok=True)
    kl_graft.write_zip(dst_zip, [(n, files[n]) for n in B.order])
    rep['relist'] = collections.OrderedDict(moved=sum(made.values()), per_room_tree=made, root_before=[len(octx.rooms[0][i].items) for i in TREES],
                                            root_after=[len(octn.rooms[0][i].items) for i in TREES], rooms_check=post or 'ok', prm_repointed=rep_prm)
    log('relist: %d items %s' % (sum(made.values()), dict(made)))


def check_relist(plain, base, log=print):
    """-> list of problems of the relisted zip against the zip it was made from."""
    bad = []
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(plain) as b:
        if a.namelist() != b.namelist():
            return ['member list changed']
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    if diff != ['F02_Main.oct', 'F02_Main.prm']:
        bad.append('members changed %s, wanted only the .oct and the .prm (record offsets)' % diff)
    A, N = F.Built(base, 'F02'), F.Built(plain, 'F02')
    sn = lambda B_: sorted((e.name, s_) for e, s_ in B_.scene.slots().items())
    if sn(A) != sn(N) or [e.name for e in A.ents] != [e.name for e in N.ents]:
        bad.append('slots / entities differ')
    oa, on = O.Oct.parse(A['.oct']), O.Oct.parse(N['.oct'])
    rk = lambda o_: [(r.vtable, r.pointer, r.tree.pack()) for r in o_.records]
    if rk(oa) != rk(on) or oa.tail != on.tail or list(oa.header) != list(on.header) or len(oa.rooms) != len(on.rooms):
        bad.append('.oct records / tail / header / room count changed')
    slot = N.scene.slots()
    byid = {s + 2: e for e, s in slot.items()}

    def boxes(octx):
        d = collections.defaultdict(list)
        for ri, room in enumerate(octx.rooms):
            for ti, t in enumerate(room):
                for it in (t.items if t else ()):
                    d[it[0]].append((ri, ti, tuple(round(v, 1) for v in t.world(it[1:4])), tuple(round(v, 1) for v in t.world([v + 1 for v in it[4:7]]))))
        return d
    da, dn = boxes(oa), boxes(on)
    moved = 0
    for i in set(da) | set(dn):
        if len(dn.get(i, ())) != len(da.get(i, ())) or len(dn.get(i, ())) > 1:
            bad.append('id %d listed %d -> %d times' % (i, len(da.get(i, ())), len(dn.get(i, ()))))
            continue
        if da[i] == dn[i]:
            continue
        a, n = da[i][0], dn[i][0]
        e = byid[i]
        shop = _shop_of(e.name)
        # same tree index, same world box (re-quantised: at most 1 quantum), root -> the shop's room
        if shop is None or a[0] != 0 or n[0] != SHOP_ROOM[shop] or a[1] != n[1]:
            bad.append('id %d (%s) moved %s -> %s' % (i, e.name, a[:2], n[:2]))
            continue
        q = [max(abs(x - y) for x, y in zip(a[2 + k], n[2 + k])) for k in (0, 1)]
        if max(q) > 3.0:
            bad.append('id %d box changed by %s cm' % (i, q))
        moved += 1
    # .prm: only the 4 bytes at +0x1c of the 64-byte type-7 chunks differ, and they now are exactly the new record offsets
    import kl_prmgraph as G
    pa, pn = G.read(A['.prm'], 'dd'), G.read(N['.prm'], 'dd')
    if len(pa.chunks) != len(pn.chunks):
        bad.append('.prm chunk count changed')
    else:
        want_refs = set(on.record_refs())
        for i, (ca, cn) in enumerate(zip(pa.chunks, pn.chunks)):
            if ca != cn:
                if not (len(ca) == 64 and ca[:4] == bytes((0, 1, 7, 0)) and ca[:0x1c] == cn[:0x1c] and ca[0x20:] == cn[0x20:]):
                    bad.append('.prm chunk %d changed outside the record offset' % i)
                elif int.from_bytes(cn[0x1c:0x20], 'little') not in want_refs:
                    bad.append('.prm chunk %d points at no new record' % i)
    left = [byid[it[0]].name for ti in TREES for it in on.rooms[0][ti].items if _shop_of(byid[it[0]].name) is not None]
    if left:
        bad.append('dress items still in the root room: %s' % left[:3])
    for room in on.rooms:
        for t in room:
            if t:
                t.check()
    if F.room_sets_check(N.scene, on, O.RoomIndex.parse(N['.rmi']), O.RoomIndex.parse(N['.rmc'])) != F.room_sets_check(A.scene, oa, O.RoomIndex.parse(A['.rmi']), O.RoomIndex.parse(A['.rmc'])):
        bad.append('room_sets_check differs')
    log('relist check: %d items moved, %d problems' % (moved, len(bad)))
    return bad


# ---------------------------------------------------------------- build / stage
def build_variant(live, outdir, variant, glass_delay, door_delay, hide, log=print):
    """prompt -> doorglass (-> relist). -> report. outdir gets F02_Main.zip / .bots.zip / .bots.base.md5."""
    if variant not in VARIANTS:
        raise ValueError('variant %s' % variant)
    work = tempfile.mkdtemp(prefix='dm02combo_', dir=os.path.dirname(outdir) if os.path.isdir(os.path.dirname(outdir)) else None)
    rep = collections.OrderedDict(variant=variant, live=live, live_md5=md5(live), glass_delay=glass_delay, door_delay=door_delay, hide_doors=list(hide))
    try:
        p1 = os.path.join(work, 'p1')
        rep['prompt'] = PROMPT.build(live, p1, log=log)
        bad = PROMPT.check(os.path.join(p1, 'F02_Main.zip'), live, log=log)
        if bad:
            raise ValueError('prompt check: %s' % bad)
        p1z = os.path.join(p1, 'F02_Main.zip')
        p2 = os.path.join(work, 'p2')
        rep['doorglass'] = DG.build(p1z, p2, 'shop', glass_delay, door_delay, DG.DEFAULT_OPEN, hide, log=log)
        p2z = os.path.join(p2, 'F02_Main.zip')
        bad = DG.check(p2z, p1z, 'shop', DG.DEFAULT_OPEN, hide, log=log)
        if bad:
            raise ValueError('doorglass check: %s' % bad)
        rep['doorglass']['check'] = 'ok'
        os.makedirs(outdir, exist_ok=True)
        final = os.path.join(outdir, 'F02_Main.zip')
        if variant == 'full':
            relist(p2z, final, rep, log=log)
            bad = check_relist(final, p2z, log=log)
            if bad:
                raise ValueError('relist check: %s' % bad)
            rep['relist']['check'] = 'ok'
        else:
            shutil.copyfile(p2z, final)
        kl_botsonline.convert(final, os.path.join(outdir, 'F02_Main.bots.zip'), 'eAllTypes', 'F02', log=lambda *a: None)
        with open(os.path.join(outdir, 'F02_Main.bots.base.md5'), 'w', newline='\n') as fh:
            fh.write(md5(final) + '\n')
        # whole-chain members against the LIVE zip
        with zipfile.ZipFile(live) as a, zipfile.ZipFile(final) as b:
            if a.namelist() != b.namelist():
                raise ValueError('member list changed against live')
            rep['members_changed'] = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
        want = {'F02_Main.prp', 'F02_Main.gms', 'F02_Main.HVK'} | ({'F02_Main.oct', 'F02_Main.prm'} if variant == 'full' else set())
        if set(rep['members_changed']) != want:
            raise ValueError('members changed against live %s, wanted %s' % (rep['members_changed'], sorted(want)))
        rep['out_md5'] = md5(final)
        rep['bots_md5'] = md5(os.path.join(outdir, 'F02_Main.bots.zip'))
        # the bots money census against the live zip
        mo = lambda z: [(o['node'], o['amount'], o['kind'], o['container']) for o in F.money_objects(F.Built(z, 'F02'))]
        rep['money_census_equal'] = mo(live) == mo(final)
        if not rep['money_census_equal']:
            raise ValueError('bots money census changed against live')
        return rep
    finally:
        shutil.rmtree(work, ignore_errors=True)


INSTALL_PY = r'''r"""Installs / undoes the DM02 COMBINED stage 1110 (shutter prompt + shop doors + vault glass + shop dressing relist).
  python install.py                       install the default variant (full) from the staged files (originals -> <name>.before-dm02combo1110; an existing backup is NEVER overwritten)
  python install.py --variant full|nodress   full = prompt + doors + glass + dress relist; nodress = without the .oct relist
  python install.py --undo                put the originals back byte for byte (only when each live file is exactly what an install wrote)
  python install.py --dry                 read-only: print every pin and what would happen (also with --undo)
  --game <dir>  other Dog Days folder (rehearsals); --skip-run-check for those only
Pins: live F02_Main.zip @LIVE@, bots @BOTS@, base @BASE@ (re-stage if another layer changed them).
Nothing is written while a kl2.exe with threads runs. Never touches KL_PortBackup or any other file. Undo this layer BEFORE any layer installed later on DM02."""
import hashlib, json, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '@TAG@'
NAMES = ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')
OLD = {'F02_Main.zip': '@LIVE@', 'F02_Main.bots.zip': '@BOTS@'}
OLD_BASE_TEXT = '@BASE@'
DEFAULT = '@DEFAULT@'
STAGED = @STAGED@      # variant -> {name: md5}
STATE = os.path.join(HERE, 'installed.json')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command', "(Get-Process kl2 -ErrorAction SilentlyContinue | ForEach-Object { $_.Threads.Count } | Measure-Object -Sum).Sum"],
                             capture_output=True, text=True).stdout.strip()
        return bool(out) and int(float(out)) > 0
    except (OSError, ValueError):
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    variant = a[a.index('--variant') + 1] if '--variant' in a else DEFAULT
    if variant not in STAGED:
        print('REFUSED: --variant takes %s' % ', '.join(sorted(STAGED))); return 1
    d = os.path.join(game, 'KLExpansion', 'Maps', 'DM02')
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    live = {n: os.path.join(d, n) for n in NAMES}
    bak = {n: live[n] + TAG for n in NAMES}
    for n in NAMES:
        if not os.path.isfile(live[n]):
            print('REFUSED: %s is not there' % live[n]); return 1
    if undo:
        if not os.path.isfile(STATE):
            print('REFUSED: no installed.json here (nothing was installed from this folder)'); return 1
        st = json.load(open(STATE))
        for n in NAMES:
            cur = md5(live[n])
            print('%-26s live %s' % (n, cur))
            if cur != st['new'][n]:
                print('REFUSED: %s live md5 %s is not the installed %s (another layer changed it: undo that one first)' % (n, cur, st['new'][n])); return 1
            if not os.path.isfile(bak[n]) or md5(bak[n]) != st['old'][n]:
                print('REFUSED: backup %s missing or not %s' % (bak[n], st['old'][n])); return 1
        if dry:
            print('would restore', ', '.join(NAMES)); return 0
        for n in NAMES:
            shutil.copyfile(bak[n], live[n] + '.tmp'); os.replace(live[n] + '.tmp', live[n]); os.remove(bak[n])
            print('%s: restored %s' % (n, md5(live[n])))
        os.remove(STATE)
        return 0
    cur = {n: md5(live[n]) for n in NAMES}
    for n in NAMES:
        print('%-26s live %s' % (n, cur[n]))
    if os.path.exists(STATE):
        print('REFUSED: installed.json exists: this folder was installed already (use --undo first)'); return 1
    if cur['F02_Main.zip'] != OLD['F02_Main.zip'] or cur['F02_Main.bots.zip'] != OLD['F02_Main.bots.zip'] or open(live['F02_Main.bots.base.md5']).read().strip() != OLD_BASE_TEXT:
        print('REFUSED: a live DM02 file is not the pinned one (%s / %s / base %s): another layer changed it: re-stage on the live files' % (
            OLD['F02_Main.zip'], OLD['F02_Main.bots.zip'], OLD_BASE_TEXT)); return 1
    for n in NAMES:
        if os.path.exists(bak[n]):
            print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak[n]); return 1
    src = os.path.join(HERE, 'variant_' + variant)
    new = {n: (md5(os.path.join(src, n)) if os.path.isfile(os.path.join(src, n)) else None) for n in NAMES}
    if None in new.values() or any(new[n] != STAGED[variant][n] for n in NAMES):
        print('REFUSED: staged files in %s are missing or not the md5 the stage recorded' % src); return 1
    if open(os.path.join(src, 'F02_Main.bots.base.md5')).read().strip() != new['F02_Main.zip']:
        print('REFUSED: base sidecar is not the md5 of the staged zip'); return 1
    need = sum(os.path.getsize(os.path.join(src, n)) + os.path.getsize(live[n]) for n in NAMES) + (1 << 30)
    if shutil.disk_usage(d).free < need:
        print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    if dry:
        print('would install variant', variant, 'from', src); return 0
    done = []
    try:
        for n in NAMES:
            shutil.copyfile(live[n], bak[n]); done.append(n)
            shutil.copyfile(os.path.join(src, n), live[n] + '.tmp'); os.replace(live[n] + '.tmp', live[n])
            print('%s: installed %s' % (n, md5(live[n])))
    except OSError as e:
        for n in reversed(done):
            shutil.copyfile(bak[n], live[n]); os.remove(bak[n])
        print('FAILED (%s); originals put back' % e); return 2
    json.dump({'variant': variant, 'old': {n: md5(bak[n]) for n in NAMES}, 'new': {n: md5(live[n]) for n in NAMES}}, open(STATE, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def make_install_py(staged):
    s = INSTALL_PY
    for k, v in (('@LIVE@', LIVE_PIN), ('@BOTS@', LIVE_BOTS_PIN), ('@BASE@', LIVE_BASE_PIN), ('@TAG@', TAG), ('@DEFAULT@', DEFAULT_VARIANT), ('@STAGED@', repr(staged))):
        s = s.replace(k, v)
    return s


README = r'''DM02 COMBINED 1110 (Late Night Opening, slot F02): shutter prompt + jeweller door + vault glass + shop dressing     built OFFLINE, NOT installed, NOT run in the game
==========================================================================================================================================================================
Owner: "fix the door already, I want the glass back, just make the AI heisters shoot it open" / "no prompt to open shutter, make it like a shop".
One stage = three passes chained on the live zip (pins below): kl_dm02shop_1110 (prompt) -> kl_dm02doorglass_1110 (door, glass) -> relist (dress), tool kl_dm02combo_1110.py.

 1. SHUTTER PROMPT  the 3 Atrium_201a shutters get the stock '{TapUse} Lift Door' use box back (KLCoopN!SoloLift) and the two-heister CoopAirlock lists; the 90 s timer is gone.
 2. DOOR            the grey leaf in the Hertzer & Sons doorway (KL_Door_3 / _4, REF 34449 / 34472) swings open %(ddelay)s s after the round start AND is hidden (flag 0x400): the
                    doorway is empty either way. KL_Door_1 / _2 (vault glass doorways) the same. (--hide-doors "1,2" would show the open slab again.)
 3. GLASS           the two vault glass doors (Whole04 REF 23182 / 24258) are back, draw and block, and break by themselves after %(gdelay)s s as the FALLBACK (stock shatter).
                    The hook klhook/klbotglass.c (other agent) is meant to make the bots shoot it open before that. Change: stage --glass-delay N.
 4. DRESS (variant full) the 86 KLDress* / KLShop props and lights (67 props, 19 lights) were listed in the ROOT room tree; the camera in a shop sits in the shop's own room
                    (Corridore_201a..d, 101b) and draws only that room's lists. They are MOVED into their shop room (same tree index). Only the .oct changes.
 Variants (install.py --variant): full (default) | nodress (1..3 only).

Install (game closed): INSTALL dm02 combined 1110.bat   or   python install.py [--variant nodress] [--dry] [--game <dir> --skip-run-check]
Undo: UNDO dm02 combined 1110.bat (byte exact). Backups <name>%(tag)s next to the live files. A second install is refused.
Pins: live F02_Main.zip %(live)s, bots %(bots)s, base %(base)s.
Staged: full zip %(fzip)s bots %(fbots)s | nodress zip %(nzip)s bots %(nbots)s

PROVEN OFFLINE (tools run the checks, kl_dm02combo_1110_test.py):
 - prompt check ok, doorglass check ok (all slots/entities equal, only .prp/.gms/.HVK change, glass statics = pre-fix records, order and list codes kept), relist check ok:
   only the .oct and .prm (type-7 record offsets repointed) change, slots/entities/records/tail/header equal, every moved id still listed once, same tree index, same world box (re-quantised), none left in the root,
   Tree.check() on every tree, room_sets_check equal, bots money census equal to live.
 - debug/check.py and check_passes.py: see the stage notes in build_report.json 'checks'.
 - The dress props have no collision (no HVK), so the relist cannot block the loot cases at x +/-2577; .HVK/.gms/.buf/.MAT/.TEX are identical to the door/glass output, the .prm differs only in the type-7 record offsets.

GUESSes (the bench decides):
%(guesses)s

BENCH PLAN (one bench at a time, TEST dll, owner not playing): 0. df; install.py --dry; install. 1. SOLO DM02, walk to the first shutter (x -1990, z ~1030): the prompt shows, press
use: it rises; inside: the dress (plaques, display table, lamps) is DRAWN (shots). 2. Jewellers front at the start: no grey leaf in the doorway, nothing blocks it. 3. vault glass: drawn and
blocking, breaks at %(gdelay)s s (or by bots with the hook on), walk through. 4. 2 seats. If the dress still does not draw: UNDO or install --variant nodress; the cause is then not the room list.
'''


def stage(live_dir, out, glass_delay=DEFAULT_GLASS_DELAY, door_delay=DEFAULT_DOOR_DELAY, hide=DEFAULT_HIDE, log=print):
    live = os.path.join(live_dir, 'F02_Main.zip')
    bots = os.path.join(live_dir, 'F02_Main.bots.zip')
    if md5(live) != LIVE_PIN or md5(bots) != LIVE_BOTS_PIN:
        raise SystemExit('live DM02 zip / bots zip are not the pinned %s / %s (another layer changed them: re-pin on the live md5s)' % (LIVE_PIN, LIVE_BOTS_PIN))
    if open(os.path.join(live_dir, 'F02_Main.bots.base.md5')).read().strip() != LIVE_BASE_PIN:
        raise SystemExit('live bots.base.md5 is not %s' % LIVE_BASE_PIN)
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        p = os.path.join(out, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    reps, staged = {}, {}
    for v in VARIANTS:
        d = os.path.join(out, 'variant_' + v)
        reps[v] = build_variant(live, d, v, glass_delay, door_delay, hide, log=log)
        staged[v] = {n: md5(os.path.join(d, n)) for n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')}
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(make_install_py(staged))
    for nm, arg in (('INSTALL dm02 combined 1110', ''), ('UNDO dm02 combined 1110', ' --undo')):
        with open(os.path.join(out, nm + '.bat'), 'w', newline='\r\n') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    with open(os.path.join(out, 'README.txt'), 'w', newline='\n') as fh:
        fh.write(README % dict(gdelay='%.0f' % glass_delay, ddelay='%.1f' % door_delay, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, tag=TAG,
                               fzip=staged['full']['F02_Main.zip'], fbots=staged['full']['F02_Main.bots.zip'],
                               nzip=staged['nodress']['F02_Main.zip'], nbots=staged['nodress']['F02_Main.bots.zip'],
                               guesses='\n'.join(' %d. GUESS: %s' % (i + 1, g) for i, g in enumerate(GUESSES))))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(dict(reports=reps, staged=staged), fh, indent=1, default=str)
    log(json.dumps(staged, indent=1))
    return reps, staged


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    if a and a[0] == 'stage':
        hide = tuple(int(x) for x in opt('--hide-doors', ','.join(map(str, DEFAULT_HIDE))).split(',') if x)
        stage(opt('--live', MAPDIR), opt('--out', OUT), float(opt('--glass-delay', DEFAULT_GLASS_DELAY)), float(opt('--door-delay', DEFAULT_DOOR_DELAY)), hide)
        return 0
    if len(a) >= 2 and a[0] == 'check' and '--base' in a:
        bad = check_relist(a[1], opt('--base', None))
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
