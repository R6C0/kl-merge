#!/usr/bin/env python3
"""
Map stage bench kits for the 11-10 release cut (d0), on the tools/kl_bench_1110.py setup (which pins the kl_bench_1109 harness to the live merged
SHIP and the live ini). Each kit is a STAGE kit: `run` installs the stage with its own install.py, benches 2 seats (round 1 -> shop -> round 2),
ALWAYS runs install.py --undo, then compares the map folder with the pre-run snapshot. Installing for real is a separate step after a PASS.

    LCDOORS_1110   DM05A (F01): luvsic's front-office sliding doors, timer variant (open 20 s after the round start), C:/kl_build_1024/lcdoors_1110
    DM02C_1110     DM02 (F02): door fix + vault glass back (60 s fallback) + shutter use prompt + shop dressing, C:/kl_build_1024/dm02shop_1110/combined (full)
    SMARTCOPS_DM01_1110 / SMARTCOPS_DM03_1110: KL_CoverSmart! boxes + RunToCover squads, C:/kl_build_1024/smartcops_1110/<map>
Segment + check drafts for DM02C / SMARTCOPS came from a workflow (11-10 ~03:20) and were checked against the harness by hand; positions are from the staged zips.

    python tools/kl_bench_1110m.py gen [kit|all]       (needs a SHIP dll live, not a bench's TEST)
    python tools/kl_bench_1110m.py validate [kit|all]
    python tools/kl_bench_1110m.py run <kit>           ONE bench (the game must be free)
    python tools/kl_bench_1110m.py verify <kit>
"""
import math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_bench_1110 as T

M, B = T.M, T.B

# the four sliding leaves (tools/kl_lc_doors_1110.py LEAVES; names from the staged zip): outer pair x 1500 (D04 / D05), inner pair x 2500 (D1 / D2)
LC_LEAVES = ('D04', 'D05', 'D1', 'D2')
LC_MID = (1900, 354, 3313)          # between the pairs: the LootArea spawn points (1900..2100, 354, 3300..3400) of the clearance report
LC_WEST = (1000, 3313)              # lobby side of the outer pair (trigger box x 900..2500)
LC_EAST = (3000, 3313)              # far side of the inner pair (GUESS: open floor; the clearance walk reached 26527 more cells with the doors open)

K = {
    'LCDOORS_1110': dict(map='DM05A', slot='F01', live={'F01_Main.zip': '0ff298a6', 'F01_Main.bots.zip': '72259e27', 'KLJoin.ini': '095e046f'},
                         shots='40-700:10', stage='C:/kl_build_1024/lcdoors_1110', tag='.before-lcdoors1110',
                         files={'variant_timer/F01_Main.zip': '791eb9c3', 'variant_timer/F01_Main.bots.zip': '912e08a5'}),
    'DM02C_1110': dict(map='DM02', slot='F02', live={'F02_Main.zip': '43c088c2', 'F02_Main.bots.zip': 'bb8f04cb', 'KLJoin.ini': '843b1c50'},
                       shots='60-420:5', stage='C:/kl_build_1024/dm02shop_1110/combined', tag='.before-dm02combo1110',
                       files={'variant_full/F02_Main.zip': '8baefac2', 'variant_full/F02_Main.bots.zip': '6293350c', 'variant_full/F02_Main.bots.base.md5': '791ffab0'}),
    'SMARTCOPS_DM01_1110': dict(map='DM01', slot='F01', live={'F01_Main.zip': '9ce9f34d', 'F01_Main.bots.zip': '975ad3c3', 'KLJoin.ini': '8201642d'},
                                shots='60-900:20', stage='C:/kl_build_1024/smartcops_1110/DM01', tag='.before-smartcops1110',
                                files={'F01_Main.zip': 'e091f0d8', 'F01_Main.bots.zip': '957f20aa', 'F01_Main.bots.base.md5': '6b7255e6'}),
    # DM03 pins = the stage on 8e23cbd3; re-pin after fc's back-SWAT (a81ede87) goes live and smartcops DM03 is re-staged on it
    'SMARTCOPS_DM03_1110': dict(map='DM03', slot='F03', live={'F03_Main.zip': '8e23cbd3', 'F03_Main.bots.zip': '2528e8f0', 'KLJoin.ini': '5c02ca99'},
                                shots='60-900:20', stage='C:/kl_build_1024/smartcops_1110/DM03', tag='.before-smartcops1110',
                                files={'F03_Main.zip': '8d9e3d16', 'F03_Main.bots.zip': 'd26bdc96', 'F03_Main.bots.base.md5': 'f5962b71'}),
}
ORDER = ['LCDOORS_1110', 'DM02C_1110', 'SMARTCOPS_DM01_1110', 'SMARTCOPS_DM03_1110']


def lc_ents():
    return ['ents DaughterRoomDoor 6'] + ['ents %s %d' % (n, 400 if len(n) == 2 else 20) for n in LC_LEAVES]


def lc_seg(who):
    s = ['wait 1000'] + lc_ents() + ['log BENCH1110 lcd t0 leaves']
    if who == 'host':
        # within the 20 s timer: from between the pairs try to walk out west (shut = NOT reached), then after the timer walk out both ways
        s += ['waitstate 0x19 90000', 'tele %d %d %d' % (LC_MID[0], LC_MID[1] + 60, LC_MID[2]), 'wait 1500', 'pos lcd-mid',
              'log BENCH1110 lcd shut try', 'goto %d %d 60 4000' % LC_WEST, 'pos lcd-shut', 'log BENCH1110 lcd shut try done'] + lc_ents() + [
              'wait 25000'] + lc_ents() + ['log BENCH1110 lcd after timer',
              'tele %d %d %d' % (LC_MID[0], LC_MID[1] + 60, LC_MID[2]), 'wait 1500', 'goto %d %d 80 8000' % LC_WEST, 'pos lcd-west', 'log BENCH1110 lcd west done',
              'tele %d %d %d' % (LC_MID[0], LC_MID[1] + 60, LC_MID[2]), 'wait 1500', 'goto %d %d 80 8000' % LC_EAST, 'pos lcd-east', 'log BENCH1110 lcd east done',
              'wait 60000'] + lc_ents() + ['log BENCH1110 lcd still open']
    else:
        s += ['wait 40000'] + lc_ents() + ['log BENCH1110 lcd join after timer']
    return s


def lc_checks(a, chk):
    info = []
    rows = {n: [r for r in M.ents(a, n) if r[1] == n and abs(r[3][0] - (1500 if n in ('D04', 'D05') else 2500)) < 600] for n in LC_LEAVES}
    for n, r in rows.items():
        chk('%s sampled near its doorway' % n, len(r) >= 2, '%d rows%s' % (len(r), (', first %s last %s' % (r[0][3], r[-1][3])) if r else ''))
        if r:
            chk('%s drawn (not hidden) at every sample' % n, not any(x[2] for x in r), 'hidden in %d of %d' % (sum(1 for x in r if x[2]), len(r)))
            mv = max(abs(r[-1][3][i] - r[0][3][i]) for i in (0, 2))
            chk('%s slid (moved >= 40 cm between the first and the last sample)' % n, mv >= 40, 'moved %.0f cm' % mv)
            chk('%s at floor height (y 300..450, not buried)' % n, all(300 <= x[3][1] <= 450 for x in r), 'y %s' % sorted({round(x[3][1]) for x in r}))
    shut = M.goto_lines(a, *LC_WEST)
    chk('walk west during the timer is blocked (doors shut)', bool(shut) and 'NOT reached' in shut[0], shut[0][13:150] if shut else 'no goto line', warn=True)
    chk('walk west after the timer reached (outer pair open)', len(shut) >= 2 and 'NOT reached' not in shut[1], shut[1][13:150] if len(shut) >= 2 else 'no 2nd goto line')
    east = M.goto_lines(a, *LC_EAST)
    chk('walk east after the timer reached (inner pair open)', bool(east) and 'NOT reached' not in east[0], east[0][13:150] if east else 'no goto line')
    info.append('LOOK at the shots near "lcd shut try" (doors drawn, closed) and "lcd after timer" (slid open); kick prompt must not show on them')
    return info


# ---- DM02 combined: facts taken from the stage (see the notes below the code) ------------------------------------------------------
DM02C_SH1 = dict(stand_from=(-1879, 1112), stand=(-1919, 1112), node=(-1990, 1032))   # KLCoop1!SoloLift box centre (-1919,624,1112); RollerShutterA_03 REF 24710
DM02C_SH2 = dict(stand_from=(1879, 1580), stand=(1919, 1580), node=(1990, 1660))      # KLCoop2!SoloLift (1919,624,1580); RollerShutterA_02 REF 24711
DM02C_DOORS = {   # doorway = (front stand, back stand) from the KickDoor_Arrow entities
    3: ((900, 2497), (1091, 2499)),     # jewellers, KL_Door_3\Door REF 34449, hinge (993,500,2560)
    4: ((1497, 1786), (1499, 1595)),    # jewellers, KL_Door_4\Door REF 34472, hinge (1560,500,1693)
    1: ((-902, 2499), (-1093, 2497)),   # vault glass doorway, KL_Door_1, hinge (-1000,500,2560)
    2: ((-1503, 1793), (-1501, 1602)),  # vault glass doorway, KL_Door_2, hinge (-1440,500,1700)
}
DM02C_GLASS = {23182: (-970, 524, 2566), 24258: (-1435, 519, 1670)}   # Whole04 REFs; both share the node name below
DM02C_GLASS_NAME = 'SI0401_M02_FA_Door_Shatter_Glass_01!Whole04'
DM02C_SHOPS = {   # n: (tele start x, z, goto x, z, expected KLDress<n>_ props, a prop to look at)
    1: (-2350, 1350, -2400, 1350, 10),    # Corridore_201b: watchtable (-2763,500,1350), plaques (-2600..-2900,650,1060/1640)
    2: (2350, 1300, 2400, 1300, 20),      # Corridore_201d: shelves (2771..2951,500,1078), desk (2951,499,1460)
    3: (2350, -2250, 2400, -2250, 18),    # Corridore_201c: shelves (2699..2879,500,-2087), sofa (2924,500,-2359)
    4: (-2350, -2400, -2400, -2400, 10),  # Corridore_201a: desk (-2951,499,-2347), plaques (-2600,650,-2637)
}


def dm02c_walk(lbl, front, back):
    """tele on the front stand (floor 500 + 60), settle, pos -a, walk to the back stand, pos -b."""
    return ['tele %d 560 %d' % front, 'wait 1500', 'goto %d %d 25 3000' % front, 'pos %s-a' % lbl,
            'goto %d %d 60 5000' % back, 'pos %s-b' % lbl, 'log BENCH1110 dm02c %s walked' % lbl]


def dm02c_shutter(tag, sh, key):
    """tele 40 cm behind the stand and goto it (the body then faces the shutter; 'face' cannot turn a standing player),
    peek the prompt codes (as kick_probe), log, press E, sample the shutter node every second."""
    s = ['tele %d 560 %d' % sh['stand_from'], 'wait 1500', 'goto %d %d 15 3000' % sh['stand'], 'wait 500', 'pos dm02c-%s-stand' % tag,
         'peek 0xdd265c+0x828+0xd00 dm02c-%s-prompt-best' % tag, 'peek 0xdd265c+0x828+0xcfc dm02c-%s-prompt-active' % tag,
         'ents RollerShutterA 12', 'log BENCH1110 dm02c %s tap' % tag, key]
    for i in range(7):
        s += ['wait 1000', 'ents RollerShutterA 12']
    return s + ['log BENCH1110 dm02c %s after' % tag]


def dm02c_seg(who):
    s = ['waitstate 0x19 90000', 'log BENCH1110 dm02c %s t0 round running' % who]
    if who != 'host':
        # join seat: sample the same entities every 15 s for ~170 s (client view of the shutter / glass / dress; not checked, read in the join log)
        s += ['ents RollerShutterA 12', 'ents KLCoop 60', 'ents Whole04 20', 'ents Remains04 20', 'ents KLDress 100']
        for i in range(11):
            s += ['wait 15000', 'ents RollerShutterA 12', 'ents Whole04 20', 'ents Remains04 20', 'log BENCH1110 dm02c join sample %d' % (i + 1)]
        return s
    # --- t0 census: stage entities present, glass intact, remains hidden; (2) door leaf by ents is best effort (cap 200 rows, leaf is named just 'Door')
    s += ['ents RollerShutterA 12', 'ents KLCoop 60', 'ents KLShop0 20', 'ents KLDress 100', 'ents Whole04 20', 'ents Remains04 20',
          'ents KL_Door_3 4', 'ents KL_Door_4 4', 'log BENCH1110 dm02c census t0']
    s += ['wait 2500', 'ents Door 200', 'log BENCH1110 dm02c door sample 2s']
    # (2) jewellers doors 3 and 4 (open + hidden by 1.5 s): walk THROUGH the doorway 4..8 s after the round starts; an invisible blocker would stop the goto
    s += ['wait 1000'] + dm02c_walk('dm02c-d3', *DM02C_DOORS[3]) + dm02c_walk('dm02c-d4', *DM02C_DOORS[4])
    # (3) glass BEFORE the break: Whole04 drawn + blocking at ~t0+15 s (the walk through door 1 / 2 must stop at the glass)
    s += ['ents Whole04 20', 'ents Remains04 20', 'log BENCH1110 dm02c g-pre sample']
    s += dm02c_walk('dm02c-g1pre', *DM02C_DOORS[1]) + dm02c_walk('dm02c-g2pre', *DM02C_DOORS[2])
    # (1) shutter prompt: shutter 1 = tap E 700, shutter 2 = hold E 1500 (separate shutters: a 2nd press may replay frames 0..82)
    s += dm02c_shutter('sh1', DM02C_SH1, 'tap E 700') + dm02c_shutter('sh2', DM02C_SH2, 'tap E 1500')
    # (4) shop dressing: one stand point per shop room, 11 s each so the shot loop (every 5 s) takes >= 2 pictures per shop
    for n, (tx, tz, gx, gz, _) in sorted(DM02C_SHOPS.items()):
        s += ['tele %d 560 %d' % (tx, tz), 'wait 1500', 'goto %d %d 40 3000' % (gx, gz), 'wait 500', 'pos dm02c-shop%d' % n,
              'ents KLDress%d_ 30' % n, 'log BENCH1110 dm02c shop%d look' % n, 'wait 8000']
    # (3) glass AFTER the 60 s fallback: well past t0+60 now (about t0+115 s). Sample first, then walk through.
    s += ['ents Whole04 20', 'ents Remains04 20', 'log BENCH1110 dm02c g-post sample']
    s += dm02c_walk('dm02c-g1post', *DM02C_DOORS[1]) + dm02c_walk('dm02c-g2post', *DM02C_DOORS[2])
    s += ['ents Whole04 20', 'ents Remains04 20', 'ents RollerShutterA 12', 'log BENCH1110 dm02c host done']
    return s


def dm02c_checks(a, chk):
    info = []
    T = lambda txt: next((M.secs_of(l[:12]) for l in a if 'BENCH1110 dm02c ' + txt in l), None)
    d2 = lambda p, q: math.hypot(p[0] - q[0], p[2 if len(p) > 2 else 1] - q[2 if len(q) > 2 else 1])
    near = lambda p, x, z, r: math.hypot(p[0] - x, p[2] - z) <= r

    chk('dm02c segment ran on the host (t0 ... host done)', T('host t0 round running') is not None and T('host done') is not None, '%d host log lines' % len(a))

    # --- walk-through verdicts -----------------------------------------------------------------------------------------
    def walk(lbl, front, back):
        pa, pb = M.pos_of(a, lbl + '-a'), M.pos_of(a, lbl + '-b')
        if pa is None or pb is None:
            return 'NOSAMPLE', 'no pos line for %s-a / %s-b' % (lbl, lbl)
        if math.hypot(pa[0] - front[0], pa[2] - front[1]) > 150:
            return 'VOID', 'tele/settle ended %.0f cm from the front stand %s (pos %s): no verdict' % (math.hypot(pa[0] - front[0], pa[2] - front[1]), front, pa)
        e = math.hypot(pb[0] - back[0], pb[2] - back[1])
        return ('THROUGH' if e <= 150 else 'BLOCKED'), 'start %s end %s, %.0f cm from the back stand %s' % (pa, pb, e, back)

    for n in (3, 4):
        v, note = walk('dm02c-d%d' % n, *DM02C_DOORS[n])
        t = T('dm02c-d%d walked' % n)
        chk('jewellers KL_Door_%d doorway walkable (door open/hidden, no blocker)' % n, v == 'THROUGH', '%s: %s' % (v, note), warn=v in ('VOID', 'NOSAMPLE'))
    # best-effort leaf read: ents 'Door' is cut at 200 rows and the leaf is named just 'Door' (kl_bench_1109 comment on kick_probe)
    leaf = [r for r in M.ents(a, 'Door') if r[1] == 'Door' and (near(r[3], 993, 2560, 40) or near(r[3], 1560, 1693, 40))]
    chk('door leaf rows for KL_Door_3/_4 visible to ents (best effort, cap 200)', bool(leaf),
        ('; '.join('%s hidden=%s pos=%s' % (r[0], r[2], tuple(round(x) for x in r[3])) for r in leaf[:4])) if leaf else 'not reached by ents (expected: 443 "door" nodes, leaf after the cap); the walk-through above is the evidence', warn=True)
    for n in (3, 4):
        g = [r for r in M.ents(a, 'KL_Door_%d' % n) if r[1] == 'KL_Door_%d' % n]
        chk('KL_Door_%d group present (stage map loaded)' % n, bool(g), '%d rows' % len(g))

    # --- glass ---------------------------------------------------------------------------------------------------------
    t_pre, t_post, t0 = T('g-pre sample'), T('g-post sample'), T('host t0 round running')
    chk('glass post-sample is >= 65 s after the round start (fallback timer 60 s)', t0 is not None and t_post is not None and t_post - t0 >= 65,
        'post at +%.0f s' % ((t_post - t0) if t0 is not None and t_post is not None else -1), warn=True)
    W = M.ents(a, 'Whole04')
    R = M.ents(a, 'Remains04')
    for ref, (gx, gy, gz) in sorted(DM02C_GLASS.items()):
        door = 1 if ref == 23182 else 2
        w = [r for r in W if near(r[3], gx, gz, 40)]
        rm = [r for r in R if near(r[3], gx, gz, 40)]
        pre = [r for r in w if t_pre is not None and M.secs_of(r[0]) <= t_pre + 1]
        post = [r for r in w if t_post is not None and M.secs_of(r[0]) >= t_post - 1]
        post_any = [r for r in W if t_post is not None and M.secs_of(r[0]) >= t_post - 1]
        rpre = [r for r in rm if t_pre is not None and M.secs_of(r[0]) <= t_pre + 1]
        rpost = [r for r in rm if t_post is not None and M.secs_of(r[0]) >= t_post - 1]
        chk('vault glass Whole04 REF %d at round start: present and drawn' % ref, bool(pre) and not pre[-1][2], 'rows %d, hidden=%s' % (len(pre), pre[-1][2] if pre else '-'))
        chk('Remains04 REF %d hidden at start' % ref, (not rpre) or rpre[-1][2], 'rows %d, hidden=%s' % (len(rpre), rpre[-1][2] if rpre else '-'), warn=True)
        v, note = walk('dm02c-g%dpre' % door, *DM02C_DOORS[door])
        chk('glass %d blocks before the break (walk stops)' % door, v == 'BLOCKED', '%s: %s' % (v, note), warn=True)   # WARN: the bot hook may have shot it already
        # what the stock shatter does to the entity is unknown: hidden flag on Whole04, or Remains04 unhidden, or the row gone. Any of the three = broken.
        gone = bool(post_any) and (not post or post[-1][2])
        remains_up = bool(rpost) and not rpost[-1][2]
        broke = gone or remains_up
        chk('glass %d broken after the fallback (Whole04 hidden/gone or Remains04 drawn)' % door, broke,
            'Whole04 post rows %d hidden=%s; Remains04 post rows %d hidden=%s; other Whole04 rows in the sample %d' % (
                len(post), post[-1][2] if post else '-', len(rpost), rpost[-1][2] if rpost else '-', len(post_any)), warn=True)
        v, note = walk('dm02c-g%dpost' % door, *DM02C_DOORS[door])
        chk('glass %d walk-through after the break' % door, v == 'THROUGH', '%s: %s' % (v, note), warn=(v in ('VOID', 'NOSAMPLE') or not broke))
    info.append('glass: what the stock shatter does to Whole04 is unknown to me; if both Whole04 and Remains04 keep their pre-state, LOOK at the g-post shots and the walk verdict')

    # --- shutter prompt + rise ---------------------------------------------------------------------------------------------
    def peek(label):
        for l in a:
            m = re.search(r'= ([0-9a-f]{8}) \(at [0-9a-f]+\)\s+%s\b' % re.escape(label), l)
            if m:
                return int(m.group(1), 16)
        return None
    for tag, sh, hard in (('sh1', DM02C_SH1, True), ('sh2', DM02C_SH2, False)):
        pb, pa_ = peek('dm02c-%s-prompt-best' % tag), peek('dm02c-%s-prompt-active' % tag)
        chk('%s: a use prompt is offered at the stand (prompt best/active nonzero)' % tag, bool(pb) or bool(pa_),
            'best %s active %s (0x12 = kick/use prompt; the Lift Door code is a GUESS)' % (pb if pb is None else hex(pb), pa_ if pa_ is None else hex(pa_)), warn=True)
        st = M.pos_of(a, 'dm02c-%s-stand' % tag)
        chk('%s: player stood at the SoloLift box' % tag, st is not None and math.hypot(st[0] - sh['stand'][0], st[2] - sh['stand'][1]) <= 120,
            'pos %s want %s' % (st, sh['stand']), warn=True)
        tt = T('%s tap' % tag)
        rows = [r for r in M.ents(a, 'RollerShutterA') if near(r[3], sh['node'][0], sh['node'][1], 25)]
        before = [r for r in rows if tt is not None and M.secs_of(r[0]) <= tt + 0.2]
        after = [r for r in rows if tt is not None and M.secs_of(r[0]) > tt + 0.2]
        if not before or not after:
            chk('%s: shutter leaf rises after E' % tag, False, 'rows before %d after %d (shutter node not read)' % (len(before), len(after)), warn=not hard)
            continue
        y0 = before[-1][3][1]
        ymax = max(r[3][1] for r in after)
        chk('%s: shutter leaf rises after E (node y +100 or more; keys rise 300)' % tag, ymax - y0 >= 100,
            'y %.0f -> max %.0f (+%.0f) over %d samples; series %s (ents pos = node transform following the keys is a GUESS)' % (
                y0, ymax, ymax - y0, len(after), ' '.join('%.0f' % r[3][1] for r in after)), warn=not hard)

    # --- shop dressing --------------------------------------------------------------------------------------------------
    for n, (tx, tz, gx, gz, want) in sorted(DM02C_SHOPS.items()):
        p = M.pos_of(a, 'dm02c-shop%d' % n)
        rows = [r for r in M.ents(a, 'KLDress%d_' % n) if M.secs_of(r[0]) >= (T('shop%d look' % n) or 0) - 3]
        slots = {r[4] for r in rows}
        chk('shop %d: player inside the shop room at the look point' % n, p is not None and math.hypot(p[0] - gx, p[2] - gz) <= 250, 'pos %s want (%d, %d)' % (p, gx, gz), warn=True)
        chk('shop %d: %d KLDress%d_ entities listed and not hidden' % (n, want, n), len(slots) >= want and all(not r[2] for r in rows),
            '%d slots, %d hidden' % (len(slots), sum(1 for r in rows if r[2])))
        tl = next((l[:12] for l in a if 'BENCH1110 dm02c shop%d look' % n in l), None)
        info.append('shop %d look logged at %s (shots every 5 s over the next ~10 s): LOOK for the plaques / tables / lamps drawn; the camera in the room is the GUESS' % (n, tl))
    info.append('shop 5 (Corridore_101b, floor 1) is not visited: KLDress5 has no props and KLShop05 sits at odd coordinates (desk (-2510,0,1352), cashdrawer (-1807,77,-3509)).')
    info.append('join seat: ents samples only; read the join log for the client view (shutter node, Whole04 / Remains04 state).')
    info.append('shots: dress and shutter images are the evidence the checks cannot give (relist = draw only); jeweller doorway look: the walk d3/d4 sits at +4..+14 s.')
    return info



# ---------------------------------------------------------------- data (from C:/kl_build_1024/smartcops_1110/<MAP>/build_report.json + cover_plan.json)
# members: (squad, entity name, planned post x, z)  <- build_report.json runcover.plain.squads[].infos
# cover:   plan boxes (name, origin x,z, stand x,z or None, stand y)  <- cover_plan.json (origin = box centre, stand = reachable floor point beside it)
SMART = {
    'DM01': dict(
        nbox=7,
        pats=['Wave_1_', 'Wave_2_', 'Wave_3_', 'M_Shop_', 'M_Floor_', 'M_Top_', 'FBI-Agents'],
        spots=[(4330, 62, 23347), (6815, 60, 22055)],       # KC_03 / KC_06 stand points + 60 cm (verified reachable floor)
        members=[
            ('Wave_1', 'Wave_1_05', 2890, 22450), ('Wave_1', 'Wave_1_06', 3070, 22210), ('Wave_1', 'Wave_1_07', 2650, 22150),
            ('Wave_1', 'Wave_1_08', 1810, 22570), ('Wave_1', 'Wave_1_09', 1810, 22930),
            ('Wave_2', 'Wave_2_01', 5770, 21430), ('Wave_2', 'Wave_2_02', 5350, 21550), ('Wave_2', 'Wave_2_03', 5050, 21550),
            ('Wave_2', 'Wave_2_04', 6310, 21190), ('Wave_2', 'Wave_2_05', 5350, 21250), ('Wave_2', 'Wave_2_06', 5950, 21250),
            ('Wave_2', 'Wave_2_07', 4810, 21430), ('Wave_2', 'Wave_2_08', 6610, 21190), ('Wave_2', 'Wave_2_09', 6910, 21190),
            ('Wave_3', 'Wave_3_01', 2530, 19510), ('Wave_3', 'Wave_3_02', 2350, 19930), ('Wave_3', 'Wave_3_03', 2410, 19210),
            ('Wave_3', 'Wave_3_04', 2830, 19570), ('Wave_3', 'Wave_3_05', 2170, 19690), ('Wave_3', 'Wave_3_06', 2170, 19090),
            ('Wave_3', 'Wave_3_07', 2950, 19330), ('Wave_3', 'Wave_3_08', 2950, 18790), ('Wave_3', 'Wave_3_09', 2110, 20050),
            ('Shop', 'M_Shop_01', 3130, 22750), ('Shop', 'M_Shop_02', 3130, 22390), ('Shop', 'M_Shop_03', 3490, 22570), ('Shop', 'M_Shop_04', 2830, 22150),
            ('Floor', 'M_Floor_01', 1770, 17530), ('Floor', 'M_Floor_02', 2730, 17570), ('Floor', 'M_Floor_03', 1650, 18050),
            ('Floor', 'M_Floor_04', 2290, 18170), ('Floor', 'M_Floor_05', 2930, 18810), ('Floor', 'M_Floor_06', 2930, 18450),
            ('Floor', 'M_Floor_07', 1650, 19050), ('Floor', 'M_Floor_08', 2330, 19210),
            ('Top', 'M_Top_01', 2931, 17159), ('Top', 'M_Top_02', 2910, 17080), ('Top', 'M_Top_03', 2919, 17004), ('Top', 'M_Top_04', 2851, 17159),
            # three squads whose single actor is called FBI-Agents_01 (matched by distance to the post)
            ('CheckFront', 'FBI-Agents_01', 6121, 23117), ('KitchenBoy', 'FBI-Agents_01', 6900, 23052), ('CornerShop', 'FBI-Agents_01', 3276, 22775),
        ],
        cover=[
            ('CoverBoxH_KC_01', 1015, 19615, 1050, 19775), ('CoverBoxH_KC_02', 1285, 19615, 1320, 19775), ('CoverBoxH_KC_03', 4357, 23204, 4330, 23347),
            ('CoverBoxH_KC_04', 7388, 23643, 7228, 23678), ('CoverBoxH_KC_05', 7388, 24073, 7228, 24108), ('CoverBoxH_KC_06', 6975, 22020, 6815, 22055),
            ('CoverBoxM_KC_01', 1724, 19493, None, None)]),
    'DM03': dict(
        nbox=12,
        pats=['M_Back_', 'M_Wave_'],
        spots=[(1575, 300, -6110), (-3231, 260, -1213)],     # KC_06 stand (garage, ~850 from the Back posts) / CoverBoxM_KC_01 stand (ramp)
        members=[
            ('Garage', 'M_Back_01', 480, -6640), ('Garage', 'M_Back_02', 480, -6400), ('Garage', 'M_Back_03', 480, -6160),
            ('Garage', 'M_Back_04', 660, -5980), ('Garage', 'M_Back_05', 720, -6340), ('Garage', 'M_Back_06', 900, -6640),
            ('Ramp', 'M_Wave_01', -3260, -2260), ('Ramp', 'M_Wave_02', -3200, -2140), ('Ramp', 'M_Wave_03', -3560, -2020),
            ('Ramp', 'M_Wave_04', -3200, -2020), ('Ramp', 'M_Wave_05', -3080, -2020)],
        cover=[
            ('CoverBoxH_KC_01', 1348, -6550, 1273, -6550), ('CoverBoxH_KC_02', 1290, -6855, 1240, -6955), ('CoverBoxH_KC_03', 1290, -7145, 1340, -7045),
            ('CoverBoxH_KC_04', -148, -6694, -73, -6694), ('CoverBoxM_KC_01', -3284, -1313, -3231, -1213), ('CoverBoxH_KC_05', -60, -7470, -25, -7315),
            ('CoverBoxH_KC_06', 1650, -6110, 1575, -6110), ('CoverBoxH_KC_07', -252, -6290, -327, -6290), ('CoverBoxM_KC_02', -3410, -2132, None, None),
            ('CoverBoxM_KC_03', -3437, -2397, None, None), ('CoverBoxH_KC_08', 1325, -6247, None, None), ('CoverBoxH_KC_09', -387, -6332, None, None)]),
}

NSAMP = 16          # host samples, ~10 s apart => ~165 s of script after the round starts


def smartcops_seg(who, mapname):
    D = SMART[mapname]
    ents = ['ents _KC_ 30'] + ['ents %s %d' % (p, 80 if p == 'FBI-Agents' else 40) for p in D['pats']]
    s = ['waitstate 0x19 120000', 'log BENCH1110 smartcops t0 round running (%s %s)' % (mapname, who)]
    if who == 'host':
        s += ents + ['log BENCH1110 smartcops sample 0']
        x, y, z = D['spots'][0]
        s += ['tele %d %d %d' % (x, y, z), 'wait 1500', 'pos smartcops-s0']
        for i in range(1, NSAMP):
            if i == 6:          # ~60 s: second quiet spot (trigger-box squads, other half of the map)
                x, y, z = D['spots'][1]
                s += ['tele %d %d %d' % (x, y, z), 'wait 1000', 'pos smartcops-s1']
            s += ['wait 9000'] + ents + ['log BENCH1110 smartcops sample %d' % i]
        s += ['pos smartcops-end', 'log BENCH1110 smartcops host done']
    else:   # join seat: boxes + squads every ~20 s, no moves
        for i in range(8):
            s += ['wait 19000'] + ents + ['log BENCH1110 smartcops jsample %d' % i]
        s += ['log BENCH1110 smartcops join done']
    return s


def smartcops_checks(a, chk, mapname):
    D = SMART[mapname]
    info = []
    d2 = lambda p, x, z: math.hypot(p[0] - x, p[2] - z)

    marks = [(i, M.secs_of(l[:12]), int(m.group(1))) for i, l in enumerate(a) for m in [re.search(r'BENCH1110 smartcops sample (\d+)', l)] if m]
    chk('smartcops segment ran on the host (t0 + >=12 samples + done)',
        any('BENCH1110 smartcops t0' in l for l in a) and len(marks) >= 12 and any('BENCH1110 smartcops host done' in l for l in a),
        '%d sample markers' % len(marks))
    if not marks:
        return info
    t0 = marks[0][1]

    def sample_of(i):               # rows are logged BEFORE their marker line
        for mi, t, n in marks:
            if mi > i:
                return n, t - t0
        return None, None

    # ---- boxes
    boxes = {(s, n): rs for (s, n), rs in M.by_entity(M.ents(a, '_KC_')).items() if re.match(r'CoverBox[HM]_KC_\d+$', n)}
    plan = {c[0]: c for c in D['cover']}
    ok = [n for (s, n), rs in boxes.items() if n in plan and d2(rs[-1][3], plan[n][1], plan[n][2]) <= 150]
    chk('KL_CoverSmart! boxes present at their planned spots (%d expected)' % D['nbox'], len(set(ok)) >= D['nbox'],
        '%d entities named CoverBox?_KC_nn, %d within 150 cm of the plan: %s' % (len(boxes), len(set(ok)), sorted(set(ok))[:4]))
    hid = [n for (s, n), rs in boxes.items() if rs[-1][2]]
    chk('boxes are hidden (flag 0x400)', len(hid) == len(boxes) and bool(boxes), '%d of %d hidden' % (len(hid), len(boxes)), warn=True)

    # ---- cover points (xz): box centre + its stand point
    cps = []
    for n, ox, oz, sx, sz in D['cover']:
        cps.append((ox, oz, n))
        if sx is not None:
            cps.append((sx, sz, n))

    def near_cover(p):
        b = min(cps, key=lambda c: d2(p, c[0], c[1]))
        return d2(p, b[0], b[1]), b[2]

    # ---- members: one track per entity, assigned to the planned member of that name whose post is nearest to its first position
    tracks = {}
    for pat in D['pats']:
        for (slot, name), rs in M.by_entity(M.ents(a, pat)).items():
            cand = [m for m in D['members'] if m[1] == name]
            rows = [(sample_of(r[5]), r[3]) for r in rs if not r[2]]        # skip hidden rows (unspawned)
            rows = [(sn[0], sn[1], p) for sn, p in rows if sn[0] is not None]
            if not cand or not rows:
                continue
            m = min(cand, key=lambda c: d2(rows[0][2], c[2], c[3]))
            if d2(rows[0][2], m[2], m[3]) > 400:        # some other actor with the same name (FBI-Agents_01 elsewhere)
                continue
            tracks[(slot, name)] = (m, rows)
    n_plan = len(D['members'])
    chk('planned squad members found visible in the ents rows (>= 60%%) (%d planned)' % n_plan, len(tracks) >= 0.6 * n_plan,
        '%d tracks' % len(tracks))

    sq = {}
    strict, loose, moved_early, moved_late, left = [], [], [], [], []
    for key, (m, rows) in tracks.items():
        sqd = sq.setdefault(m[0], dict(n=0, cov=0, mov=0))
        sqd['n'] += 1
        d0 = near_cover(rows[0][2])[0]
        hit = [(t, near_cover(p)[0]) for _, t, p in rows if near_cover(p)[0] <= 200]
        if hit:
            loose.append(key)
        if d0 > 250 and any(t <= 90 for t, _ in hit):
            strict.append((m[1], round(d0), round(min(d for _, d in hit))))
            sqd['cov'] += 1
        if max(d2(p, rows[0][2][0], rows[0][2][2]) for _, t, p in rows if t <= 90) >= 150:
            moved_early.append(key)
        ps = [(t, p) for _, t, p in rows]
        if any(t2 > 60 and d2(p2, p1[0], p1[2]) > 100 for (t1, p1), (t2, p2) in zip(ps, ps[1:])):
            moved_late.append(key)
            sqd['mov'] += 1
        # reached cover (<=200) at one sample and >300 cm from that spot at a later one
        for k, (t1, p1) in enumerate(ps):
            if near_cover(p1)[0] <= 200 and any(d2(p2, p1[0], p1[2]) > 300 for _, p2 in ps[k + 1:]):
                left.append(key)
                break
    chk('>= 1 squad member RAN to a cover point (started > 250 cm away, <= 200 cm of a box centre/stand within 90 s)', len(strict) >= 1,
        '%d members, e.g. %s (name, start dist, best dist)' % (len(strict), strict[:4]))
    chk('members were at a cover point at some sample at all (loose)', len(loose) >= 1, '%d members' % len(loose), warn=True)
    chk('members moved >= 150 cm from their first position within 90 s', len(moved_early) >= 1, '%d of %d tracks' % (len(moved_early), len(tracks)))
    chk('NOT frozen: >= 1 member still changes position (>100 cm between samples) after 60 s', len(moved_late) >= 1,
        '%d of %d tracks move after 60 s' % (len(moved_late), len(tracks)))
    chk('GUESS 1: members that reached cover later leave it (RunToCover hands over to Defend)', len(left) >= 1,
        '%d members left cover by > 300 cm' % len(left), warn=True)
    for k, v in sorted(sq.items()):
        info.append('squad %s: %d tracked, %d ran to cover, %d move after 60 s' % (k, v['n'], v['cov'], v['mov']))

    # ---- host stayed alive and got to its quiet spots
    for lbl, i in (('smartcops-s0', 0), ('smartcops-s1', 1)):
        p = M.pos_of(a, lbl)
        sp = D['spots'][i]
        chk('host pos %s near its tele spot (alive, not killed/respawned)' % lbl, p is not None and d2(p, sp[0], sp[2]) < 400,
            str(p), warn=True)
    info.append('LOOK at the shots: men crouching/standing behind the hidden boxes in the first minute, then walking back to the posts')
    return info


_segment, _item_checks = M.segment, M.item_checks


def segment(k, who):
    if k == 'LCDOORS_1110':
        return lc_seg(who)
    if k == 'DM02C_1110':
        return dm02c_seg(who)
    if k.startswith('SMARTCOPS_'):
        return smartcops_seg(who, K[k]['map'])
    return _segment(k, who)


def item_checks(k, a, dd=(), ctrl=None):
    if k not in K:
        return _item_checks(k, a, dd, ctrl)
    res, info = [], []

    def chk(name, cond, detail='', warn=False):
        res.append(('PASS' if cond else ('WARN' if warn else 'FAIL'), name, detail))
    chk('item segment ran on the host (level loaded ... segment done)', any('BENCH1109 %s host level loaded' % k in l for l in a)
        and any('BENCH1109 %s host segment done' % k in l for l in a), '%d host log lines' % len(a))
    if k == 'LCDOORS_1110':
        info += lc_checks(a, chk)
    elif k == 'DM02C_1110':
        info += dm02c_checks(a, chk)
    elif k.startswith('SMARTCOPS_'):
        info += smartcops_checks(a, chk, K[k]['map'])
    return res, info


for _k, _c in K.items():
    for _a, _b in dict(entry=0, hook=M.HOOK, solo_secs=600, parts=('online',), keepalive=1).items():
        _c.setdefault(_a, _b)
M.K.clear()
M.K.update(K)
M.ORDER[:] = ORDER
B.KITS.clear()
B.KITS.update(K)
M.segment, M.item_checks = segment, item_checks
T.K.clear()
T.K.update(K)
T.load_pins()

if __name__ == '__main__':
    sys.exit(M.main())
