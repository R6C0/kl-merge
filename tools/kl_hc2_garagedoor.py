"""kl_hc2_garagedoor.py - OPT-IN post-pass for Hot Coffee II (DM01B): the garage's roller door goes with the blast. Reads a BUILT F03_Main.zip,
writes a copy. Nothing imports it. Written 2026-10-24 (kl-merge-k29) after the owner: "on hot coffee ii the garage door doesnt blow up only the brick
wall does and the ai heisters just go through the wall / door whereas i cant".

FOUND (offline, DM01B F03_Main.zip of 2026-10-23, kl_map_escape.Level + kl_hvk):
  * The garage's east wall (x 120..200) has TWO openings on the way out: the brick wall at z 7200 (blown by the campaign's blast objects, kl_fa_v2_hotcoffee
    BLAST/GARAGE_BLAST) and the roller door 'M01A_Out_Junkyard_01a\\SI0102_M01_GarageDor_A_01' at z 4807..5593, y 0..339 (the doorway is a free frame in
    RepairWall_G_01: jambs and lintel only). The START rows (z 4150..4280) are 600 from the door and 3000 from the brick wall.
  * The door's collision is FIVE KEY-FRAMED shapes (HVK type 4, ZDynMeshShape, filter 0x172; REF 20364, 20366..20369 = Segment_01..05, x 167..172, z 4806..5593,
    y 0..337 stacked). The blast lists (GeomDeactivator_OnExplosion: 19 entries) hold only STATIC type 1 pieces (flags 0x72 / 0x172) and the brick wall;
    the door is in none of them, so it stays shut, visible and solid (nothing else references the group: its own RelayMessageList only).
  * The navigation mesh runs THROUGH the doorway: polygon 872 (x -397..90) -> 821 (x 90..199, z 4799..5599) -> 83 / 126 / 85 (x 199..907), all part 0, the same
    island as the brick wall's polygons (0, 3, 4, 5, 12, 11). So the bots' shortest way out of the garage is the door, not the hole the blast makes.
  * kl_walk2d on that zip (START (-400, 4200); blast pieces dropped): the person reaches the brick wall's far side (300, 7200) = True but the doorway's far side
    (300, 5200) = False; dropping ONLY the door group (7 refs) makes (300, 5200) True. So for the human the door is a solid plug the bots' path ignores.
    (WHY a bot passes a solid key-framed door is NOT established: GUESS that the character controller of an AI ignores the dynamic layer or that a bot that is
    inside the shape is pushed out; the owner saw it, nothing here reproduces it.)
WHAT IT CHANGES (both are in the output, each can be left out):
  1. the door group's full path is APPENDED to the DeactivateGeom list of 'Specials!GarageWallExplosion!GeomDeactivator_OnExplosion' (field 1) -> the door's
     mesh and bodies leave with the blast, exactly as the brick wall does -- and to the 'pre show' ActivateGeom list ('Gameplay!010_FirstFight!Shutters!
     GeomActivator_TearGas_RIGHT', field 1) so round 2 shows it again before its blast. Only the .prp differs (strings; no slot or REF number moves).
  2. (--no-sink leaves it out) the door's five key-framed shapes are sunk below the world in the .HVK as kl_fa_v2_hc_route2.COLL_ONLY does for the diner door
     (triangles copied and moved straight down; index lists keep their length; no MOPP for type 4). GUESS: DeactivateGeom removes a KEY-FRAMED body's
     collision (everything the blast list removes today is static); the sink makes the answer independent of that. Cost: before the blast the door is a ghost
     (looks shut, no collision); the blast comes 2 s into the round-start event, 8 s before GO, so nobody can reach it in that window. Round 2 shows the door
     (pre show) without collision until its blast again.
Usage (from tools/):  python kl_hc2_garagedoor.py <in F03_Main.zip> <out F03_Main.zip> [--no-sink] [--no-wire]
"""
import os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_hvk, kl_fa_author as A

DOOR_TAIL = 'M01A_Out_Junkyard_01a\\SI0102_M01_GarageDor_A_01'
OUT_NODE = 'Specials!GarageWallExplosion!GeomDeactivator_OnExplosion'       # DeactivateGeom, field 1 = the list the blast takes off
SHOW_NODE = 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_RIGHT'  # ActivateGeom, field 1 = the round-2 'pre show' list (kl_fa_v2_hotcoffee ROLE)
SEGMENTS = ('Segment_01', 'Segment_02', 'Segment_03', 'Segment_04', 'Segment_05')


def _door(sc):
    hit = [k for k in range(1, len(sc.names)) if sc.path[k] and sc.path[k].endswith('\\' + DOOR_TAIL)]
    if len(hit) != 1:
        raise ValueError('kl_hc2_garagedoor: %d nodes end in %s (this is not DM01B)' % (len(hit), DOOR_TAIL))
    return hit[0]


def wire(sc, log=print):
    """Append the door's path to the blast's DeactivateGeom list and the pre-show ActivateGeom list. -> number of lists changed."""
    door = sc.path[_door(sc)]
    n = 0
    for node, ctrl in ((OUT_NODE, 'DeactivateGeom'), (SHOW_NODE, 'ActivateGeom')):
        k = A.node_of(sc, node)
        i = A.ctrl_of(sc, k, ctrl)
        from kl_fa_bank import values
        lst = list(values(sc, k, ctrl)[1])
        if door in lst:
            log('  %s: door already listed' % node)
            continue
        kl_fa.edit(sc, k, i, lambda us: A.setv(sc, us, 1, lst + [door]))
        log('  %s %s: %d -> %d entries (+ the garage door)' % (node.split('!')[-1], ctrl, len(lst), len(lst) + 1))
        n += 1
    return n


def sink(zp, raw_hvk_name, log=print):
    """-> new .HVK bytes with the five door segments' triangles sunk (kl_fa_v2_hc_route2._sink)."""
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


def run(src, dst, do_wire=True, do_sink=True, log=print):
    sc, _, _ = kl_fa.load(src)
    zf = zipfile.ZipFile(src)
    names = zf.namelist()
    pn = [n for n in names if n.lower().endswith('_main.prp')][0]
    hn = [n for n in names if n.lower().endswith('_main.hvk')][0]
    new = {}
    if do_wire:
        if wire(sc, log):
            new[pn] = sc.p.serialize()
    if do_sink:
        new[hn], t = sink(src, hn, log)
        log('  door collision: %d triangles below the world' % t)
    if not new:
        log('kl_hc2_garagedoor: nothing to change')
        return {}
    members = [(n, new.get(n, zf.read(n))) for n in names]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    log('kl_hc2_garagedoor: wrote %s (changed: %s)' % (dst, ', '.join(sorted(new))))
    return new


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) != 2:
        print(__doc__)
        return 2
    run(a[0], a[1], '--no-wire' not in sys.argv, '--no-sink' not in sys.argv)
    return 0


if __name__ == '__main__':
    sys.exit(main())
