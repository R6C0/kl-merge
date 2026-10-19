"""kl_hc2_attic.py - OPT-IN post-pass for 'Hot Coffee II' (DM01B, slot F03): the warehouse attic as part of the round, and the diner's
front door kicked in. Reads a BUILT F03_Main.zip, writes a copy. Does nothing unless run; no builder imports it. 2026-10-19.
Plan and facts: re/hotcoffee2_attic_door.md. NOTHING OF IT HAS RUN IN THE GAME (labels: MEASURED = on the real file, READ = from
code/data, GUESS = not shown).

With NO feature flag the output has the same member contents as the input (byte for byte; only the zip container is rewritten).

  --loot-attic      MoneyStack_093/094/095 (floor, z20150) move up into the attic room at y860 (2800/2900/3000, 860, 16950): 3 attic / 3 floor
                    (MEASURED: the stair chain START -> stairs -> those spots has no closure, kl_route doors). The floor loot area
                    (EnterLootArea / POI box at (3100,60,20250)) stays where it is: bots get their heist stage by entering it (READ, kl_fa_bots).
  --bot-stops       the 'to_loot_b' stop (the 'to_loot' stop stays on the floor: it gives the bot its stage) of squads #02 #04 #06 #08 move into the attic (a bot walks the nav stairs; the mesh's
                    stair polygons 716/731 join the floor through gap 2 MEASURED). Bots do not vault; they only take mesh edges (READ).
                    GUESS: that the five-nearest loot window (800 / 400) then picks the attic stacks for them.
  --attic-squad     the two policemen of 04_Squad_03_IntoWarehouse (C_Policeman_01/_02) and its 010_DefendInside stops move into the attic
                    (no entity is added, so the slot order stays). GUESS on how they behave there.
  --door            the diner front (PC0901_M01_Dor_Diner_Anim_01, a shootable glass door: ShotActivate Whole -> Shattered) is kicked in when
                    an FA merc enters a door box: the spare unreferenced TriggerBox TB_OB_120 (MEASURED: nothing names it) is moved to
                    (6100,100,22900) half (300,200,250), just before the door on the route (door z23088; the old speak box at z23950..24550
                    fired AFTER the crew was through: review MEASURED). It sends 'AITrigger' (READ) to the door group, Dor_attach, Dor_Win_Whole;
                    the door group's own empty RelayMessageList becomes 'AITrigger' -> 'Activate' on Dor_Win_Shattered, Dor_Win_Remains and the
                    5 glass emitters (what the stock shot activates). GUESS: that the box (a child of a squad group) ticks, that
                    eTGS_AllInside fires for one merc, what the leaves' animations look like, that Whole stays visible beside Shattered
                    (no Deactivate is sent), whether the door's HVK (y -452..-200) stops anyone. No sound / shake.
  --door-fx         with --door: Whole is forced off (Dor_attach relays 'ForceTriggerShotActivate' to it), two spare glass-sound ZSNDOBJ move to the
                    door and join Whole's on-list (offsets FX_SOUNDS), a ShakeCamera (FX_SHAKE) joins the door group. See run().
  --drop-gap2       VARIANT: removes the office->warehouse nav bridge (gap 2) with the exact inverse of kl_nav_bridge (MEASURED: removing and
                    re-adding it gives the live block byte for byte). Then the attic part is cut from the warehouse floor and bots cannot
                    use it as a way down: writes a [CrewHop] block (KLJoin.ini, see --ini) that must carry them. UNPROVEN; the crew
                    bots' routes all cross gap 2, so this is NOT recommended without the hop being shown to work.
  --ini FILE        with --drop-gap2: where to write the CrewHop section (default: next to the output as KLJoin_attic_hop.ini).
Usage (from tools/):  python kl_hc2_attic.py <in F03_Main.zip> <out F03_Main.zip> [flags] [--check]
"""
import os, sys, struct, zipfile, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_pf4, kl_map_ai as MA
import kl_fa_bots as F
import kl_prpjoin as J
import kl_fa_author as A
from kl_prp import units

BS = chr(92)
LOOT_UP = {'MoneyStack_093': (2800, 860, 16950), 'MoneyStack_094': (2900, 860, 16950), 'MoneyStack_095': (3000, 860, 16950)}
BOT_UP = {  # squad -> the to_loot_b stop's attic point (x, 860, z), on the attic mesh. The squad's first stop 'to_loot' STAYS on the floor: it is the
    # place inside the ENTERS_BANK box that gives the bot heist stage 1 (kl_fa_bots check FAILs 'no route place inside an ENTERS_BANK
    # trigger' when both moved: MEASURED 2026-10-19). (2700,860,16750) is NOT on a walkable polygon (MEASURED); these four are.
    '02': (2800, 860, 17000), '04': (3000, 860, 17000), '06': (2600, 860, 17000), '08': (2500, 860, 17100)}
ATTIC_SQUAD = '04_Squad_03_IntoWarehouse'
ATTIC_POLICE = {'C_Policeman_02': (2850, 860, 17500), 'C_Policeman_01': (2850, 860, 17900)}
ATTIC_STOPS = ((2850, 860, 17450), (2850, 860, 17800), (2900, 860, 17700))      # the 010_DefendInside Pos nodes (the group has 2; the 3rd is unused). (2700,860,17800) was OFF the mesh (MEASURED by review, nav.at dy=120 None): all three are on polygon 987/777
SPEAK_BOX = 'Specials!LevelSpeak!TriggerBox'
SPEAK_LIST = 17
DOOR = 'PC0901_M01_Dor_Diner_Anim_01'
FX_SOUNDS = (2365088, 440992)   # glass_break_medium_01#set (the stock windows' Window_Shatter, MEASURED) ; glass_shatter_big#set (in the DD-systems bank: playable is a GUESS)
FX_SHAKE = (0.8, 3000.0)        # strength, radius: GUESS (the rocket 0.5 / 4000, Subway 3.0 / 8000)
HOP = ('[CrewHop.6]\n; attic -> warehouse floor, ONLY with --drop-gap2 (UNPROVEN vertically). Bots only; no NoHuman: a human can use the stairs\n'
       'From=2800 860 18400\nRadius=250\nHeight=150\nWait=2\nStage=1\nWalkTo=1\nAgain=0\nTo.1=2800 0 19900\nTo.2=2900 0 19900\nTo.3=3000 0 19900\n'
       'To.4=3100 0 19900\nTo.5=3200 0 19900\nTo.6=3300 0 19900\n')


def remove_last(block, k):
    """Inverse of kl_nav_bridge.add_bridges for the LAST k bridges (MEASURED round trip, 2026-10-19)."""
    n, A = kl_pf4.split(block, True)
    A = [list(a) for a in A]
    polys = [list(struct.unpack('<BBHIIIIIII', r)) for r in A[3]]
    areas = [list(struct.unpack('<12I', r[:48])) for r in A[4]]
    boxes = [r[48:] for r in A[4]]
    edges = [list(struct.unpack('<iII', r)) for r in A[9]]
    nb = len(polys) - k
    newp = set(range(nb, len(polys)))
    # areas/polys belong to the tail
    na = len(areas) - k
    for i in range(na, len(areas)):
        assert areas[i][7] in newp and areas[i][2] == 1
    # old edges pointing at the new polys
    touched = collections.Counter()
    for pi in range(nb):
        p = polys[pi]
        for e in range(p[0]):
            ed = edges[p[5] + e]
            if ed[0] <= -2 and (-2 - ed[0]) in newp:
                ed[0] = -1
                touched[p[4]] += 1
    verts = list(A[6])
    for ai in sorted(touched, reverse=True):
        for _ in range(touched[ai]):
            pos = areas[ai][6] + areas[ai][1] - 1
            v = struct.unpack('<5f', verts[pos]); assert v[3] == 0 and v[4] == 0
            del verts[pos]
            for e in edges:
                if e[1] > pos: e[1] -= 1
            for q in areas[ai + 1:]: q[6] -= 1
            areas[ai][1] -= 1
    # truncate the tails
    t0s = areas[na][9]; t1s = areas[na][10]; t2s = areas[na][11]
    nv = areas[na][6]; ne = polys[nb][5]
    A[0] = A[0][:t0s]; A[1] = A[1][:t1s]; A[2] = A[2][:t2s]
    A[3] = [struct.pack('<BBHIIIIIII', *p) for p in polys[:nb]]
    A[4] = [struct.pack('<12I', *a) + b for a, b in zip(areas[:na], boxes[:na])]
    A[6] = verts[:nv]
    A[9] = [struct.pack('<iII', *e) for e in edges[:ne]]
    return kl_pf4.join(A)


def _find(B, suffix):
    hit = [k for k in range(1, len(B.sc.names)) if B.sc.path[k].endswith(suffix)]
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (suffix, len(hit)))
    return hit[0]


def move(B, k, pos, log=print):
    """Put node k at the WORLD point pos: .prp ZGEOM[2] and the .gms record (as kl_fa_author.place); a child gets the point in its
    parent's frame (assumes the node's own rotation is irrelevant to its position, READ)."""
    sc, e = B.sc, B.ents[k - 1]
    w = B.at(k)
    par = sc.parent[k]
    world = tuple(pos)
    if par:   # a child of a group placed elsewhere: its own values are LOCAL to the parent (READ kl_fa_bots frames); pos is world
        pos = tuple(round(x, 3) for x in B.local(par, pos))
    lab = J.labels('dd', sc.cls(k))
    kl_graft.edit(sc.nodes[k], 'props', lambda us: A.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos]))
    e.trans = struct.pack('<3f', *pos) + e.trans[12:]
    log('  moved %s: %s -> world %s (requested; B.at caches frames)' % (sc.path[k][-60:], [round(x) for x in w], [round(x, 1) for x in world]))


def run(src, dst, loot=False, stops=False, squad=False, door=False, gap2=False, ini=None, log=print, door_fx=False):
    B = F.Built(src, 'F03')
    sc = B.sc
    touched = set()
    if loot:
        for n, p in LOOT_UP.items():
            move(B, _find(B, 'DropMoney!' + n), p, log)
        touched |= {'.prp', '.gms', '.buf'}
    if stops:
        for q, b in BOT_UP.items():
            move(B, _find(B, 'merc_bot_squad!Squad#' + q + BS + '014_DefendBehaviour_to_loot_b' + BS + 'Pos#01'), b, log)
        touched |= {'.prp', '.gms', '.buf'}
    if squad:
        for n, p in ATTIC_POLICE.items():
            move(B, _find(B, ATTIC_SQUAD + BS + n), p, log)
        top = _find(B, ATTIC_SQUAD + BS + '010_DefendInside')
        pts = [j for j in range(top + 1, sc.end[top]) if sc.cls(j) != 'ZGROUP' and not sc.nodes[j]['ctrls']]
        for j, p in zip(pts, ATTIC_STOPS):
            move(B, j, p, log)
        touched |= {'.prp', '.gms', '.buf'}
    if door:
        dk = _find(B, DOOR)
        shat = _find(B, DOOR + BS + 'Dor_Diner_Anim_Geom_01' + BS + 'Dor_Win_Shattered')
        sh_ci = [i for i, (nm, _b) in enumerate(sc.nodes[shat]['ctrls']) if sc.p.key(nm) == 'ShotActivate'][0]
        # the glass / debris the stock SHOT turns on (ShotActivate list 3 of the shattered pane: remains + 5 emitters)
        deb = list(kl_fa.value(sc, [list(u) for u in units(sc.nodes[shat]['ctrls'][sh_ci][1][1:-1])][3]))
        pane = [p for p in (sc.path[shat], sc.path[_find(B, DOOR + BS + 'Dor_Diner_Anim_Geom_01' + BS + 'Dor_Win_Remains')])]
        turn_on = pane + [p for p in deb if p not in pane]
        # (1) the door group's own empty RelayMessageList becomes {'AITrigger' -> 'Activate', shattered pane + remains + emitters, 0.0}:
        #     what the shot does (activate list), as a relay because a TriggerBox only sends 'AITrigger' (READ re/club_campaign.md 1634).
        ri = [i for i, (nm, _b) in enumerate(sc.nodes[dk]['ctrls']) if sc.p.key(nm) == 'RelayMessageList'][0]
        def relay(f):
            MA.setv(sc, f, 0, 'AITrigger'); MA.setv(sc, f, 1, 'Activate'); MA.setv(sc, f, 2, turn_on)
        kl_fa.edit(sc, dk, ri, relay)
        # (2) a spare, unreferenced TriggerBox (TB_OB_120, KANEONLY, empty list, child of squad 04_Squad_01_IntoWarehouseFRONT: nothing
        #     in the .prp names it, MEASURED) becomes the door box: x 5800..6400, z 22650..23150 (the route passes the door at
        #     z 23055..23187, MEASURED), FA mercs. It sends 'AITrigger' to the door group (-> the relay) and the two visible leaves.
        bx = _find(B, '04_Squad_01_IntoWarehouseFRONT' + BS + 'TB_OB_120')
        move(B, bx, (6100.0, 100.0, 22900.0), log)
        lab = J.labels('dd', sc.cls(bx))
        kl_graft.edit(sc.nodes[bx], 'props', lambda us: [A.setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), float(v)) for i, v in enumerate((300, 200, 250))])
        e = B.ents[bx - 1]
        bci = [i for i, (nm, _b) in enumerate(sc.nodes[bx]['ctrls']) if sc.p.key(nm) == 'TriggerBox'][0]
        tl = [sc.path[dk]] + [sc.path[_find(B, DOOR + BS + 'Dor_Diner_Anim_Geom_01' + BS + n)] for n in ('Dor_attach', 'Dor_Win_Whole')]
        def box(f):
            MA.setv(sc, f, 14, 'ECPS_FA_MERCONLY'); MA.setv(sc, f, SPEAK_LIST, tl)
        kl_fa.edit(sc, bx, bci, box)
        if door_fx:
            # --door-fx: (a) hide Whole by the stock path: Dor_attach (the box already messages it) gets a RelayMessageList 'AITrigger' ->
            # 'ForceTriggerShotActivate' on Whole (the forced swap = on-list shown, off-list hidden; READ kl2 0x47f2f4, proven live on Retomoto's
            # window). Not on the group itself (its RelayMessageList already sends 'Activate'; two of one class on a node never occur, MEASURED).
            # (b) two unreferenced ZSNDOBJ (GlassA_Diner_01/02!Glass_Break_Sound, MEASURED) move to the door and join Whole's on-list, as stock windows
            # carry theirs. (c) a ShakeCamera cloned from the rocket's joins the door group, message 'AITrigger'.
            ga = DOOR + BS + 'Dor_Diner_Anim_Geom_01' + BS
            wh, at_ = _find(B, ga + 'Dor_Win_Whole'), _find(B, ga + 'Dor_attach')
            ri2 = [i for i, (nm, _b) in enumerate(sc.nodes[dk]['ctrls']) if sc.p.key(nm) == 'RelayMessageList'][0]
            nm0, body0 = sc.nodes[dk]['ctrls'][ri2]
            sc.nodes[at_]['ctrls'].append((nm0, list(body0)))
            def rel2(f):
                MA.setv(sc, f, 0, 'AITrigger'); MA.setv(sc, f, 1, 'ForceTriggerShotActivate'); MA.setv(sc, f, 2, [sc.path[wh]])
            kl_fa.edit(sc, at_, len(sc.nodes[at_]['ctrls']) - 1, rel2)
            # the box list is NOT trimmed: Whole keeps the box's 'AITrigger' (its MatPosAnim listens to it, MEASURED)
            snds = []
            for n, off in (('GlassA_Diner_01', FX_SOUNDS[0]), ('GlassA_Diner_02', FX_SOUNDS[1])):
                sk = _find(B, n + '!Glass_Break_Sound')
                if any(sc.path[sk] in str(v) for _k, _i, v in kl_fa.controllers(sc, 'ShotActivate')):
                    raise SystemExit('sound node %s is referenced' % sc.path[sk])
                move(B, sk, (6160.0, 100.0, 23090.0), log)
                sl = J.labels('dd', sc.cls(sk))
                kl_graft.edit(sc.nodes[sk], 'props', lambda us, off=off: A.setv(sc, us, sl.index('ZSNDOBJ[0]'), off))
                snds.append(sc.path[sk])
            wi = [i for i, (nm, _b) in enumerate(sc.nodes[wh]['ctrls']) if sc.p.key(nm) == 'ShotActivate'][0]
            def addon(f):
                MA.setv(sc, f, 3, list(kl_fa.value(sc, f[3])) + snds)
            kl_fa.edit(sc, wh, wi, addon)
            rk = _find(B, 'Projectile' + BS + 'Projectiles_01' + BS + 'Rocket_RPG7')
            pat = sc.nodes[rk]['ctrls'][A.ctrl_of(sc, rk, 'ShakeCamera')]
            sc.nodes[dk]['ctrls'].append((pat[0], list(pat[1])))
            def shk(f):
                MA.setv(sc, f, 0, FX_SHAKE[0]); MA.setv(sc, f, 1, 'AITrigger'); MA.setv(sc, f, 2, 0); MA.setv(sc, f, 3, FX_SHAKE[1])
            kl_fa.edit(sc, dk, len(sc.nodes[dk]['ctrls']) - 1, shk)
            log('  door-fx: Whole forced off via Dor_attach, sounds %s on the on-list of Whole, shake %s' % (FX_SOUNDS, FX_SHAKE))
        log('  door: box %s -> (6100,100,22900) half (300,200,250), targets %s; door relay -> %d nodes' % (sc.path[bx][-20:], [t.split(BS)[-1] for t in tl], len(turn_on)))
        touched |= {'.prp', '.gms', '.buf'}
    if gap2:
        B.scene.nav = remove_last(B.scene.nav, 2)
        touched |= {'.gms', '.buf'}
        open(ini or os.path.join(os.path.dirname(dst), 'KLJoin_attic_hop.ini'), 'w').write(HOP)
        log('  gap 2 removed; CrewHop section written (UNPROVEN)')
    files = dict(B.files)
    if '.prp' in touched:
        files[B.ext['.prp']] = sc.p.serialize()
    if touched & {'.gms', '.buf'}:
        import kl_gms
        gms, buf = B.scene.write()
        files[B.ext['.gms']], files[B.ext['.buf']] = kl_gms.pack(gms), buf
    kl_graft.write_zip(dst, [(n, files[n]) for n in B.order], kl_graft.load_options('level=9'))
    log('kl_hc2_attic: wrote %s (changed: %s)' % (dst, sorted(touched) or 'nothing'))
    return touched


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    ini = a[a.index('--ini') + 1] if '--ini' in a else None
    if '--door-fx' in a and '--door' not in a:
        print('--door-fx requires --door')
        return 2
    run(a[0], a[1], '--loot-attic' in a, '--bot-stops' in a, '--attic-squad' in a, '--door' in a, '--drop-gap2' in a, ini, door_fx='--door-fx' in a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
