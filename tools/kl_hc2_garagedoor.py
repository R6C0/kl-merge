"""kl_hc2_garagedoor.py - OPT-IN post-pass for Hot Coffee II (DM01B): the garage's door goes with the blast. Reads a BUILT F03_Main.zip,
writes a copy. Nothing imports it. Written 2026-10-24 (kl-merge-k29); REWORKED 2026-10-24 (hc2hasta_1024b) after the owner: "you opened the wrong garage".

WHICH DOOR (the k29 version got this wrong)
  * k29 opened 'M01A_Out_Junkyard_01a\\SI0102_M01_GarageDor_A_01', a roller door on the garage's EAST wall (x ~170, z 4807..5593) made of five key-framed
    shapes. The owner meant the GARAGE DOOR the heisters start next to, on the WEST side: the Havok shatter door 'M01A_Ins_Garage_101a\\
    SI0120_M01_GarageDorHavok_A_01' = '!While_01' (the intact door, node at x -1970, z 6200) + '!Shards' (60 STATIC type-1 pieces 'Hinges_FRAG_nn' /
    'Segment_FRAG_nn', x -1975..-1927, z 5836..6564) + the two frame/guard pieces 'M01A_Out_Garage_01a\\SI0102_M01_GarageDor_A_STATIC_HEADS_01' (z 4200) and
    '_HEADS_02' (z 6200). All of them are plain STATIC pieces (HVK type 1), which is what DeactivateGeom removes (the 19 entries of the blast list today).
  * Evidence (offline, kl_walk2d on the live DM01B zip, box -4000,1000,3000,8000, START (-400,4200)): the person does NOT reach (-2400,6200), (-2400,4200)
    or (-2200,5200) (west of the door); with the Havok door group and the two HEADS pieces dropped ALL THREE are reached (5687 -> 9989 cells, x down to -3980).
    The bots' navmesh runs through that door (so the AI heisters walk out while the human is stopped), exactly the owner's description of the other garage.
WHAT IT CHANGES (--door west is the default; east/both exist for the record)
  1. wire: the west door's leaf paths (While_01, 60 Shards children, HEADS_01, HEADS_02 = 63) are APPENDED to the DeactivateGeom list of
     'Specials!GarageWallExplosion!GeomDeactivator_OnExplosion' (field 1) and to the round-2 'pre show' ActivateGeom list ('Gameplay!010_FirstFight!
     Shutters!GeomActivator_TearGas_RIGHT', field 1). Leaf paths, because every entry of those lists today is a leaf (the group path k29 used for the east
     door is not shown to work). Only the .prp differs; no slot or REF number moves.
  2. unwire east: the east GarageDor_A_01 group path k29 added is REMOVED from both lists (it was never the door the owner meant).
  3. --restore-hvk <zip>: the east door's five key-framed shapes were sunk below the world by k29 (to make a DeactivateGeom of a key-framed body
     unnecessary); this puts the ORIGINAL .HVK back from <zip> (a backup from before k29, e.g. F03_Main.zip.before-1024cover) after checking that sinking
     that file's east segments reproduces the live .HVK byte for byte. The east door is solid again (its brick-wall neighbour still blows).
GUESS: DeactivateGeom of the leaf pieces leaves no visible stump (the 60 pieces are the door itself, 'FRAG' = fragments of the Havok door); the player-side
collision answer is the kl_walk2d check above, not a live run.
Usage (from tools/):  python kl_hc2_garagedoor.py <in F03_Main.zip> <out F03_Main.zip> [--door west|east|both] [--restore-hvk <zip>] [--sink] [--no-wire]
  (--sink = the old k29 east sinking; off by default now)
"""
import os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_hvk, kl_fa_author as A

DOOR_TAIL = 'M01A_Out_Junkyard_01a\\SI0102_M01_GarageDor_A_01'              # the EAST roller door (k29's wrong choice)
WEST_HAVOK = 'M01A_Ins_Garage_101a\\SI0120_M01_GarageDorHavok_A_01!'          # + 'While_01' / 'Shards' (+ '\\<child>')
WEST_HEADS = ('M01A_Out_Garage_01a\\SI0102_M01_GarageDor_A_STATIC_HEADS_01', 'M01A_Out_Garage_01a\\SI0102_M01_GarageDor_A_STATIC_HEADS_02')
OUT_NODE = 'Specials!GarageWallExplosion!GeomDeactivator_OnExplosion'       # DeactivateGeom, field 1 = the list the blast takes off
SHOW_NODE = 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_RIGHT'  # ActivateGeom, field 1 = the round-2 'pre show' list (kl_fa_v2_hotcoffee ROLE)
SEGMENTS = ('Segment_01', 'Segment_02', 'Segment_03', 'Segment_04', 'Segment_05')


def _door(sc):
    hit = [k for k in range(1, len(sc.names)) if sc.path[k] and sc.path[k].endswith('\\' + DOOR_TAIL)]
    if len(hit) != 1:
        raise ValueError('kl_hc2_garagedoor: %d nodes end in %s (this is not DM01B)' % (len(hit), DOOR_TAIL))
    return hit[0]


def west_paths(sc):
    """-> the 63 full paths of the west Havok door (While_01, every child of !Shards, the two HEADS pieces), in node order."""
    out = []
    shards = None
    for k in range(1, len(sc.names)):
        p = sc.path[k]
        if not p:
            continue
        if p.endswith('\\' + WEST_HAVOK + 'While_01'):
            out.append(p)
        elif p.endswith('\\' + WEST_HAVOK + 'Shards'):
            shards = p
    if len(out) != 1 or shards is None:
        raise ValueError('kl_hc2_garagedoor: west Havok door not found (%d While_01, shards %s); this is not DM01B' % (len(out), shards))
    kids = [sc.path[k] for k in range(1, len(sc.names)) if sc.path[k] and sc.path[k].startswith(shards + '\\')
            and sc.path[k].count('\\') == shards.count('\\') + 1]
    if len(kids) != 60:
        raise ValueError('kl_hc2_garagedoor: !Shards has %d direct children, expected 60' % len(kids))
    out += kids
    for tail in WEST_HEADS:
        hit = [sc.path[k] for k in range(1, len(sc.names)) if sc.path[k] and sc.path[k].endswith('\\' + tail)]
        if len(hit) != 1:
            raise ValueError('kl_hc2_garagedoor: %d nodes end in %s' % (len(hit), tail))
        out += hit
    return out


def wire(sc, door='west', log=print):
    """Edit the blast's DeactivateGeom list and the pre-show ActivateGeom list. -> number of lists changed."""
    from kl_fa_bank import values
    add = []
    drop = set()
    if door in ('west', 'both'):
        add += west_paths(sc)
    if door in ('east', 'both'):
        add.append(sc.path[_door(sc)])
    else:
        drop.add(sc.path[_door(sc)])                      # take k29's east entry out again
    n = 0
    for node, ctrl in ((OUT_NODE, 'DeactivateGeom'), (SHOW_NODE, 'ActivateGeom')):
        k = A.node_of(sc, node)
        i = A.ctrl_of(sc, k, ctrl)
        lst = list(values(sc, k, ctrl)[1])
        new = [x for x in lst if x not in drop] + [x for x in add if x not in lst]
        if new == lst:
            log('  %s %s: unchanged (%d entries)' % (node.split('!')[-1], ctrl, len(lst)))
            continue
        kl_fa.edit(sc, k, i, lambda us, new=new: A.setv(sc, us, 1, new))
        log('  %s %s: %d -> %d entries (+%d, -%d)' % (node.split('!')[-1], ctrl, len(lst), len(new),
                                                   len([x for x in add if x not in lst]), len([x for x in lst if x in drop])))
        n += 1
    return n


def sink(zp, raw_hvk_name, log=print):
    """-> (new .HVK bytes with the five EAST door segments' triangles sunk (kl_fa_v2_hc_route2._sink), triangles moved). The k29 behaviour."""
    import kl_map_escape as ESC, kl_fa_v2_hc_route2 as R2
    L = ESC.Level(zp)
    with zipfile.ZipFile(zp) as z:
        raw = z.read(raw_hvk_name)
    if L.hvk.serialize() != raw:
        raise ValueError('kl_hc2_garagedoor: the .HVK does not round-trip; nothing written')
    total = 0
    for seg in SEGMENTS:
        hit = [k for k in range(1, len(L.sc.names)) if L.sc.path[k] and L.sc.path[k].endswith('\\' + DOOR_TAIL + '\\' + seg)]
        if len(hit) != 1:
            raise ValueError('kl_hc2_garagedoor: %s: %d nodes' % (seg, len(hit)))
        ref = L.ents[hit[0] - 1].ref
        shapes = [s for s in L.hvk.shapes if any(kl_hvk.ref(i) == ref for i in s.inst)]
        if len(shapes) != 1 or len(shapes[0].inst) != 1 or shapes[0].type != 4:
            raise ValueError('kl_hc2_garagedoor: %s (REF %d) is not one key-framed shape with one placement' % (seg, ref))
        c = R2._sink(L.hvk, ref, None, None)
        if not c:
            raise ValueError('kl_hc2_garagedoor: %s: no triangles moved' % seg)
        log('  sunk %s (REF %d): %d triangles' % (seg, ref, c))
        total += c
    return L.hvk.serialize(), total


def restore_hvk(live_raw, orig_zip, hvk_name, log=print):
    """-> the original .HVK bytes of orig_zip, after proving that sink(orig) == live_raw (the live file differs from the original ONLY by k29's sink)."""
    sunk, _t = sink(orig_zip, hvk_name, lambda *a: None)
    if sunk != live_raw:
        raise ValueError('kl_hc2_garagedoor: sinking %s does not reproduce the live .HVK (it holds other changes); nothing restored' % orig_zip)
    with zipfile.ZipFile(orig_zip) as z:
        raw = z.read(hvk_name)
    log('  .HVK: original east door collision restored (%d bytes; sink(original) == live, verified)' % len(raw))
    return raw


def run(src, dst, door='west', do_wire=True, do_sink=False, orig=None, log=print):
    sc, _, _ = kl_fa.load(src)
    zf = zipfile.ZipFile(src)
    names = zf.namelist()
    pn = [n for n in names if n.lower().endswith('_main.prp')][0]
    hn = [n for n in names if n.lower().endswith('_main.hvk')][0]
    new = {}
    if do_wire:
        if wire(sc, door, log):
            new[pn] = sc.p.serialize()
    if do_sink:
        new[hn], t = sink(src, hn, log)
        log('  door collision: %d triangles below the world' % t)
    elif orig:
        new[hn] = restore_hvk(zf.read(hn), orig, hn, log)
    if not new:
        log('kl_hc2_garagedoor: nothing to change')
        return {}
    members = [(n, new.get(n, zf.read(n))) for n in names]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    log('kl_hc2_garagedoor: wrote %s (changed: %s)' % (dst, ', '.join(sorted(new))))
    return new


def main():
    argv = sys.argv[1:]
    opt = {}
    a = []
    i = 0
    while i < len(argv):
        x = argv[i]
        if x in ('--door', '--restore-hvk'):
            opt[x] = argv[i + 1]
            i += 2
        elif x.startswith('--'):
            opt[x] = True
            i += 1
        else:
            a.append(x)
            i += 1
    if len(a) != 2:
        print(__doc__)
        return 2
    door = opt.get('--door', 'west')
    if door not in ('west', 'east', 'both'):
        print('--door west|east|both')
        return 2
    run(a[0], a[1], door, '--no-wire' not in opt, '--sink' in opt, opt.get('--restore-hvk'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
