#!/usr/bin/env python3
"""
Bench kits for the maps INSTALLED on 2026-11-08/09. Every kit pins its md5s and runs on the live map folder as it is, EXCEPT the stage kits
(K entry with stage= and tag=, today DM07UNHIDE_1109): `run` installs the stage with its own install.py (originals -> *<tag>, never overwritten),
benches, and ALWAYS runs install.py --undo in a finally block, then compares every map-folder md5 with the pre-run snapshot.
Built on tools/kl_bench_1106.py (imported; its KITS table is replaced in this process only). 2 seats, Q32 online pair, round 1 -> shop -> round 2.
A per-kit item segment is spliced into BOTH seats' scripts right after the first `waitload`; only the host seat moves (tele / goto / tap E).

    python tools/kl_bench_1109.py gen [kit|all]       write C:/kl_build_1024/bench_1109/<kit> (no game contact; reads the live zips and the
                                                      *.before-doors_1108 backups read-only to find the door stand points)
    python tools/kl_bench_1109.py validate [kit|all]  DRY RUN: pins, TEST dll, script ops, door/stand data. Never launches the game.
    python tools/kl_bench_1109.py run <kit>           ONE bench (needs the game free: no other kl2.exe). Nothing is installed; the map folder
                                                      md5s are compared before/after.
    python tools/kl_bench_1109.py verify <kit>        re-read the logs of the last run (no game contact)
    python tools/kl_bench_1109.py order               (re)write C:/kl_build_1024/bench_1109/RUN_ORDER.txt

Kits: HASTA1109 (DM11B) DM03_1109 DM02_1109 DM01B_1109 DM07_1109 DM07GATE_1109 DM07UNHIDE_1109 (stage kit) DM07SINK_1109 (stage kit) DM07CURTAIN_1109 (stage kit, KeepAlive off) DM07PLANE_1109 + DM07PLANE72_1109 (stage kits, HERO-plane gate) DD10GATE_1109 (live DD10 gate leak) DOORS_1109_DM01 DOORS_1109_DM03A (DOORS_1109 = the last two).
What the log CAN decide: faults/dumps, round 2 reached, 0x25 dwell, botgate, entity hidden flags and positions (`ents`), vehicle state
(`waitvan`), goto reached / NOT reached. What it CANNOT: boom, camera shake, glare, kick sound, pop (a 1-frame jump), cover pillars: those
need the screenshots (ReShade bridge D3dShotPost, KLShot_inst1_NN.jpg in the run folder) and an ear/eye.
GUESSES are marked GUESS: the kick key (E, as for boarding), the tele floor height (stand y + 150), the shot windows.
"""
import json, math, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_bench_1106 as B

KIT = 'C:/kl_build_1024/bench_1109'
DD = B.DD
MAPS = DD + '/KLExpansion/Maps'
# live = merged_1108h (81 installs it after DM02_1109): SHIP 52b37716 (built from 8c4292b9), its TEST twin (build_auto.bat, klauto) fceb3c6d;
# KLHook.ini 4a740f92 = merged_1108f's f7f11dcc + [VanBlow] ShieldCalled=1 + HealFloor=95 (checked: 1108h set_keys on f7f11dcc gives 4a740f92).
# The live dinput8.dll can be a peer's TEST dll swapped in by a bench, so the kit takes the twin from the merged kit folder, never from the live file.
MERGED = 'C:/kl_build_1024/merged_1108h'
INI_KIT = MERGED
INI_TAG = 'merged1108h'
BUILT_FROM = '8c4292b9'
SHIP_MD5 = '52b3771659650f89c22249b775777da9'
TEST_MD5 = 'fceb3c6df5208b46e98f97d9f663d308'
INI_MD5 = '4a740f9232e157b04b15ec6b4718302f'
HOOK = (MERGED + '/dll_test/dinput8.dll', TEST_MD5)
INI_KEYS = (('ShopPage', 'TidyPage2', '1'), ('Hire', 'TidyPage', '1'),      # fc's keys merged_1108f wrote
            ('VanBlow', 'ShieldCalled', '1'), ('VanBlow', 'HealFloor', '95'))  # d0's keys merged_1108h writes
BS = chr(92)

# kit -> map, slot, live pins (md5 prefixes of the files the bench must find), shot windows (seconds since the launch, 'a-b:step', comma list)
K = {
    'HASTA1109': dict(map='DM11B', slot='F04', live={'F04_Main.zip': 'd98d60f7', 'F04_Main.bots.zip': '5968f07d', 'KLJoin.ini': '187fd94f'}, shots='60-700:12'),
    'DM03_1109': dict(map='DM03', slot='F03', live={'F03_Main.zip': 'c586d445', 'F03_Main.bots.zip': '143f95f8', 'KLJoin.ini': '5c02ca99'}, shots='60-900:25',
                      doors=('DM03', 'F03', (176,))),
    'DM02_1109': dict(map='DM02', slot='F02', live={'F02_Main.zip': 'bd119e9c', 'F02_Main.bots.zip': 'a5068fa0', 'KLJoin.ini': '843b1c50'}, shots='60-900:25',
                      doors2=(1, 2)),
    'DM01B_1109': dict(map='DM01B', slot='F03', live={'F03_Main.zip': '778b075c', 'F03_Main.bots.zip': 'dccc9250', 'KLJoin.ini': 'f28992a5'}, shots='60-900:15'),
    'DM07_1109': dict(map='DM07', slot='F06', live={'F06_Main.zip': 'f35e4133', 'F06_Main.bots.zip': '1f514d51', 'KLJoin.ini': '73e113d9'}, shots='60-900:15'),
    # the gate leak alone (no van): crossings through two VISIBLE panels (controls) and the hidden 4m_01, sampled at the fence line x -4560..-4600
    'DM07GATE_1109': dict(map='DM07', slot='F06', live={'F06_Main.zip': 'f35e4133', 'F06_Main.bots.zip': '1f514d51', 'KLJoin.ini': '73e113d9'}, shots='60-500:10'),
    # TOGGLE TEST (stage kit): the live DM07 with fence panel 4m_01 UN-hidden (tools/kl_dm07unhide_1109.py: gms flags 0x205e6 -> 0x201e6 in the plain AND the bots
    # zip, the online bench plays the bots zip). Same walk as DM07GATE_1109 but only H (4m_01) and the A control (4m_02), no south walk. `live` = the pins before the install.
    'DM07UNHIDE_1109': dict(map='DM07', slot='F06', live={'F06_Main.zip': 'f35e4133', 'F06_Main.bots.zip': '1f514d51', 'KLJoin.ini': '73e113d9'}, shots='60-500:10',
                            stage='C:/kl_build_1024/dm07unhide_1109', tag='.before-dm07unhide1109',
                            files={'F06_Main.zip': '92ad73451bd70151116d7367f1e7645c', 'F06_Main.bots.zip': '58203a1c52e8d2c788be4d51a932e561',
                                   'F06_Main.bots.base.md5': 'd1b973d815af69622dc5cbd37a213de2'}),
    # FIX TEST (stage kit): the 13 fence-line slabs sunk to the mud (tools/kl_dm07sink_1109.py: .HVK placement y 4.715 -> 3.85, collision bottom 471.5 -> 385
    # over mud 388..460; the 11-09 unhide run crossed at z ~10420 = under 4m_11, gap 72 cm). Four crossings that must all read BLOCKED (4m_01 z 10334, 4m_11 z 10420
    # and 10700, 4m_10 z 10850, where sinking 4m_01 + 4m_11 alone moved the crossing in the walk model), then the van round (arrive, wait, reverse out). install.py hard-links (C: 271 MB free on 11-09)
    'DM07SINK_1109': dict(map='DM07', slot='F06', live={'F06_Main.zip': 'f35e4133', 'F06_Main.bots.zip': '1f514d51', 'KLJoin.ini': '73e113d9'}, shots='60-900:15',
                          stage='C:/kl_build_1024/dm07sink_1109', tag='.before-dm07sink1109',
                          files={'F06_Main.zip': 'a98e1f7562f031c7c4d590106c07212e', 'F06_Main.bots.zip': '0a80cfef9ab72d0c4aeae39d152ec811',
                                 'F06_Main.bots.base.md5': '0ee0ef216ecb3a16628ad291c7caa3b7'}),
    # FIX TEST (stage kit): a KillBox "curtain" box (cm) x -4720..-4560, y 300..1100, z 9990..10800 just west of the gate (tools/kl_dm07curtain_1109.py, the DM11B
    # donor_kill recipe: an inert *NoCover* box + the stock KillBox controller). Walks: controls first (z 9800 = visible 4m_02, z 10850 = 4m_10: BLOCKED), then four
    # through the gate (z 10334, 10420, 10600, 10700): each must end KILLED (dead inside the curtain) or BLOCKED east of x -4565; alive west of -4700 = THROUGH = FAIL.
    # Then the van round: the van must still reach state 7 (GUESS: a KillBox ignores a vehicle; if it kills the driver the van never leaves = FAIL).
    # keepalive=0: KeepAlive refills the local player's health every poll while health > 0 (klauto.c kla_keep_alive); a KillBox that kills through damage (not by
    # setting health to 0 in one step) could be undone by it, so this kit runs without it (police kills before the fence then read DIED-EAST = WARN, rerun).
    'DM07CURTAIN_1109': dict(map='DM07', slot='F06', live={'F06_Main.zip': 'f35e4133', 'F06_Main.bots.zip': '1f514d51', 'KLJoin.ini': '73e113d9'}, shots='60-900:15',
                             stage='C:/kl_build_1024/dm07curtain_1109', tag='.before-dm07curtain1109',
                             files={'F06_Main.zip': '2529fb77e18a62e101a6bc544956b8e9', 'F06_Main.bots.zip': 'da69d8b3ad2ff9abf1b9925e9fdecbd6',
                                    'F06_Main.bots.base.md5': '8ee12031c0e0da6af2a94304892b8b6e'},
                             keepalive=0),
    # FIX TEST (stage kit): the two hidden gate panels' HVK slots 248/256 replaced by two clones of DD10's collision-only ColiObj_HERO_Plane01 at x -4578
    # (tools/kl_dm07plane_1109.py; DM07PLANE_1109 = --sub 0x108 hero-only flags, DM07PLANE72_1109 = --sub 0x72 plain world flags, separate stage dirs, same tag). The panels
    # stay hidden (the van drives through them). Order: the van round FIRST (it must still reverse out through the gap, state 7), then the walks: controls (plA = visible 4m_02
    # BLOCKED, plF = free path east, must PASS), 10 gate crossings z 9995..10850 that must read BLOCKED (z 10850 = visible 4m_10, so it is a control too), two crouched ones (GUESS: LCONTROL toggles the stance).
    # `files` md5s are '' until the stage exists (existence only is checked; fill in the 8-char prefixes from the `stage` output). KeepAlive stays on (nothing here kills).
    'DM07PLANE_1109': dict(map='DM07', slot='F06', live={'F06_Main.zip': 'f35e4133', 'F06_Main.bots.zip': '1f514d51', 'KLJoin.ini': '73e113d9'}, shots='60-900:15',
                           stage='C:/kl_build_1024/dm07plane_1109', tag='.before-dm07plane1109',
                           files={'F06_Main.zip': '', 'F06_Main.bots.zip': '', 'F06_Main.bots.base.md5': ''}),
    'DM07PLANE72_1109': dict(map='DM07', slot='F06', live={'F06_Main.zip': 'f35e4133', 'F06_Main.bots.zip': '1f514d51', 'KLJoin.ini': '73e113d9'}, shots='60-900:15',
                             stage='C:/kl_build_1024/dm07plane72_1109', tag='.before-dm07plane1109',
                             files={'F06_Main.zip': '', 'F06_Main.bots.zip': '', 'F06_Main.bots.base.md5': ''}),
    # LEAK TEST on the LIVE DD10 (nothing installed): BigFence_A_02 (REF 31255, x 7999..8014, z 845..1145) is hidden by kl_dd10_vanlane_1108.py with the same
    # 0x400 flag that the DM07 benches proved loses player collision; the collision-only ColiObj_HERO_Plane01 (x 8017, z 652..1349) should still block (GUESS).
    # The van is called first (the tele lands in otrExitLevel) and parks at x 8640 east of the gate, then three walks west through the pillar gap (z 848..1142).
    'DD10GATE_1109': dict(map='DD10', slot='F07', entry=5, live={'F07_Main.zip': '1a0d94b0', 'F07_Main.bots.zip': '27c9fae8', 'KLJoin.ini': 'ebdf1472'},
                          shots='60-400:10'),
    'DOORS_1109_DM01': dict(map='DM01', slot='F01', live={'F01_Main.zip': '444a3ed6', 'F01_Main.bots.zip': 'f3ed6155', 'KLJoin.ini': 'db4516c6'}, shots='60-700:20',
                            doors=('DM01', 'F01', (957, 2569))),
    # door 2569 first: runs 2 and 3 lost door 2 to a police kill ~19 s into the round (05:53:28, 06:22:36), always after door 1
    'DOORS_1109_DM01R': dict(map='DM01', slot='F01', live={'F01_Main.zip': '444a3ed6', 'F01_Main.bots.zip': 'f3ed6155', 'KLJoin.ini': 'db4516c6'}, shots='60-700:20',
                             doors=('DM01', 'F01', (2569, 957))),
    'DOORS_1109_DM03A': dict(map='DM03A', slot='F07', live={'F07_Main.zip': 'aa79d66d', 'F07_Main.bots.zip': 'd1a8dd0c', 'KLJoin.ini': '958c24b6'}, shots='60-700:20',
                             doors=('DM03A', 'F07', (6516,))),
}
ORDER = ['HASTA1109', 'DM03_1109', 'DM02_1109', 'DM01B_1109', 'DM07_1109', 'DM07GATE_1109', 'DM07UNHIDE_1109', 'DM07SINK_1109', 'DM07CURTAIN_1109', 'DM07PLANE_1109', 'DM07PLANE72_1109', 'DD10GATE_1109', 'DOORS_1109_DM01', 'DOORS_1109_DM01R', 'DOORS_1109_DM03A']
for _k, _c in K.items():
    for _a, _b in dict(entry=0, stage=None, tag=None, hook=HOOK, solo_secs=600, parts=('online',), keepalive=1).items():
        _c.setdefault(_a, _b)
    if _k not in B.KITS:
        pass
B.KITS.clear()
B.KITS.update(K)
B.KIT = KIT


def kd(k):
    return '%s/%s' % (KIT, k)


# ------------------------------------------------------------------ door data (read-only on the game folder)
def door_data(k):
    """Kick-door stand points. doors=(map, slot, hosts): the INPUT zip (*.before-doors_1108 backup, where the hosts are still static
    leaves) gives hinge + stand points through kl_interact_graft.door_stand. doors2=(1, 2): DM02's glass kick doors in the live zip
    (KL_Interact!N\\KL_Door_n\\Door leaf), the through line is the leaf's thickness axis (the two of +-x/+-z whose point 130 out is on the walk mesh)."""
    import kl_fa_bots as F, kl_interact_graft as IG
    c = K[k]
    out = []
    if 'doors' in c:
        m, slot, hosts = c['doors']
        B_ = F.Built('%s/%s/%s_Main.zip.before-doors_1108' % (MAPS, m, slot))
        nav = F.Nav(B_.scene.nav)
        allh = {h['k']: h for h in IG.door_hosts(B_, nav)}
        for hk in hosts:
            h = allh[hk]
            cx, cy, cz = h['R']
            P = h['hinge']
            st = []
            for l in (IG.ARROW_FRONT, IG.ARROW_BACK):
                x, z = P[0] + cx[0] * l[0] + cz[0] * l[2], P[2] + cx[2] * l[0] + cz[2] * l[2]
                a = nav.at(x, P[1], z, dy=120.0)
                st.append([round(x), round(P[1]), round(z)] if a is not None else None)
            out.append(dict(host=hk, name=h['name'][-34:], hinge=[round(v) for v in P], front=st[0], back=st[1]))
    if 'doors2' in c:
        B_ = F.Built('%s/%s/%s_Main.zip' % (MAPS, c['map'], c['slot']))
        nav = F.Nav(B_.scene.nav)
        for k_, p in enumerate(B_.sc.path):
            if not p or not p.endswith(BS + 'Door'):
                continue
            mm = re.search(r'KL_Door_(\d+)' + re.escape(BS) + 'Door$', p)
            if not mm or int(mm.group(1)) not in c['doors2']:
                continue
            R, P = B_.fr[B_.ents[k_ - 1]]
            cx, cy, cz = R
            cand = []
            for v in (cx, [-a for a in cx], cz, [-a for a in cz]):
                x, z = P[0] + 130 * v[0], P[2] + 130 * v[2]
                cand.append([round(x), round(P[1]), round(z)] if nav.at(x, P[1], z, dy=150.0) is not None else None)
            pair = [(cand[0], cand[1]), (cand[2], cand[3])]
            a, b = next(((x, y) for x, y in pair if x and y), (None, None))
            # snap onto the group's own KickDoor_ArrowBack/Front entities (the doorway middle): door 1's leaf hangs from the hinge at its END
            # (leaf z 2440..2560, hinge z 2560), so +-130 from the hinge sat on the jamb edge at z 2560, outside the kick box (z ~2419..2583
            # GUESS orientation) at x -830/-800 and the prompt never showed (DM02_1109 runs b + c). Arrows: (-902, 2499) / (-1093, 2497).
            grp = p[:-len('Door')]
            arr = [[round(v) for v in B_.fr[B_.ents[j - 1]][1]] for j, q in enumerate(B_.sc.path)
                   if q and q.startswith(grp) and re.search(r'KickDoor_Arrow(Back|Front)_\d+$', q)]
            if a and b and len(arr) == 2:
                d2 = lambda u, w: (u[0] - w[0]) ** 2 + (u[2] - w[2]) ** 2
                a, b = (arr[0], arr[1]) if d2(a, arr[0]) + d2(b, arr[1]) <= d2(a, arr[1]) + d2(b, arr[0]) else (arr[1], arr[0])
            out.append(dict(host=int(mm.group(1)), name=p.split(BS, 1)[1][:34], hinge=[round(v) for v in P], front=a, back=b))
    return out


def kick_probe(lbl, when, n=10):
    """Read-only peeks of the human kick registry (static RE 0x55e600/0x46b330, workflow wywe974am): count at [[0xdd265c]+0xaa4],
    pointers from +0xaa8; per controller +0x58 character gate (-1 = never), +0x5c state (1 = kickable, 3 = kicked), +0x34, +0x60/+0x64 box nodes.
    A grafted door missing from the registry (count 0) can never offer the kick prompt."""
    # player slot 0 = [gd+0x828]: +0xd00 best prompt, +0xcfc active prompt; 0x12 = the kick/use prompt is offered (no key needed to show it)
    s = ['peek 0xdd265c+0xaa4 %s-%s-kickreg-count' % (lbl, when),
         'peek 0xdd265c+0x828+0xd00 %s-%s-prompt-best' % (lbl, when),
         'peek 0xdd265c+0x828+0xcfc %s-%s-prompt-active' % (lbl, when)]
    for i in range(n):
        o = 0xaa8 + 4 * i
        # the pointer itself = the controller object, the same 'obj' 'ents KickDoor_Action' prints: ties a registry slot to a door.
        # DOORS_1109_DM01 run 1: 9 registered (all gate 2 state 1); only slots 0..3 were read, so the kicked door's slot was unseen.
        s += ['peek 0xdd265c+0x%x %s-%s-ctrl%d-ptr' % (o, lbl, when, i)]
        # ptr + state only: gate/p34/box fields read 2/1/set on all 9 in runs 1 + 2, and 6 lines a slot crowd the 640-line script (klauto kla_cmd[640])
        s += ['peek 0xdd265c+0x%x+0x5c %s-%s-ctrl%d-state' % (o, lbl, when, i)]
    return s


# no leaf-rotation peeks: DOORS_1109_DM01 run 3 read the guessed slots 16724..6 / 16746..8 as identity before AND after (that run also missed the
# kick), and the runtime slot order is not the gms order (KL_Door_9 = slot 16704 at runtime, gms index 16726), so the leaf slot is unknown;
# 'ents' (substring only, at most 200 rows shown) cannot reach a node named just 'Door' (351 matches, cut at slot 16375). The kick result is the
# registry controller's state (1 -> 3), read before and after each attempt.


def door_seg(d, lbl):
    """Kick from the stand point (inside the kick box) facing the doorway (2 taps of E), look at the leaf before/after, walk through when both sides are on the mesh."""
    h = d['hinge']
    a = d['front'] or d['back']
    b = d['back'] if d['front'] and d['back'] else None
    # aim at the doorway's middle (half way between the two stand points), not the hinge: DM03_1109 run 1 walked at the hinge edge
    # 60 cm off-centre, stuck on the jamb with a 104 deg bearing error and pressed E at the wall. One-sided doors keep the hinge.
    c = ((a[0] + b[0]) / 2.0, (a[2] + b[2]) / 2.0) if b else (h[0], h[2])
    # at the leaf, face the far stand point (the walk direction), not c: DM02_1109 faced c from 77 cm and 60 cm sideways (bearing error 74, 4 s timeout)
    f = (b[0], b[2]) if b else (h[0], h[2])
    # waitstate 0x19 first: DM02_1109's first tele came 5 s after 'level loaded', before the round ran (session state not 0x19), and was refused
    # tele 60 cm over the stand, not 150: DOORS_1109_DM01R door 957 landed 1.5 m up on shop furniture at (1969, 156, 22127) out of the kick box
    # (prompt 0 all through), where run 3 from the same point slid to the floor at (2045, 8, 21973) and had the prompt
    # tele 70 cm BEHIND the stand (away from c) and walk onto it: 'face' cannot turn a standing player, a goto does, so the body arrives facing c.
    # DOORS_1109_DM01R door 957 stood at bearing error 121 the whole time with prompt 6 (never 0x12) and E did nothing; door 2569 at -59 kicked on
    # the 2nd pair. GUESS: the back-off point is open floor (not checked on the mesh; the stand points are)
    # 40 cm, not 70, then a short step PAST the stand toward c: DM02_1109 door 1 never left its 70 cm back-off point (-800, 2560) (bearing error 173,
    # prompt 6): GUESS the back-off sat against a wall. The 2nd goto (20 cm toward c, 15 cm tolerance) turns the body toward c even if the 1st one stalled.
    v = (a[0] - c[0], a[2] - c[1])
    n = max(1.0, (v[0] ** 2 + v[1] ** 2) ** 0.5)
    k = 40.0 / n
    p = (a[0] - v[0] * 20.0 / n, a[2] - v[1] * 20.0 / n)
    s = ['waitstate 0x19 90000', 'tele %d %d %d' % (a[0] + v[0] * k, a[1] + 60, a[2] + v[1] * k), 'wait 2500', 'goto %d %d 25 5000' % (a[0], a[2]),
         'goto %d %d 15 3000' % p, 'wait 500',
         'pos %s-stand' % lbl, 'log BENCH1109 %s door %s: before' % (lbl, d['host']),
         'ents KL_Door 20', 'ents KickDoor_Action 20'] + kick_probe(lbl, 'stand') + [
         # kick from the stand, no walk first: DOORS_1109_DM01 run 1 door 2 had the kick prompt (0x12) at the stand and lost it (0) after the goto to
         # the hinge (out of the box), so E did nothing; door 1 kept 0x12 at the leaf and E snapped the player 55 cm / 60 deg (kick animation, GUESS).
         'face %d %d' % c, 'wait 700', 'pos %s-at-leaf' % lbl] + kick_probe(lbl, 'atleaf') + [
         'tap E 700', 'wait 600', 'tap E 700', 'wait 3500', 'log BENCH1109 %s door %s: kicked (E x2)' % (lbl, d['host']), 'pos %s-kicked' % lbl,
         'ents KL_Door 20'] + kick_probe(lbl, 'kicked') + [
         # second attempt: run 3's door 1 kept the prompt (active 0x12, best 6) after a face that timed out (bearing error 123) and E did not kick;
         # face again and press twice more (a kicked door ignores it: its controller stays 3)
         # DM01R: door 2569 kicked only on this second pair (prompt 0x12 at the first pair too), so press four times here. 'face' cannot turn a
         # standing player (the heading read is the body's; DM01R kept 129 / 86 through every 4 s face), so it stays a no-harm try
         'face %d %d' % c, 'wait 1000', 'tap E 400', 'wait 900', 'tap E 400', 'wait 900', 'tap E 400', 'wait 900', 'tap E 400', 'wait 3000',
         'log BENCH1109 %s door %s: kicked again (E x4)' % (lbl, d['host']), 'pos %s-kicked2' % lbl] + kick_probe(lbl, 'kicked2')
    if b:
        s += ['goto %d %d 70 6000' % c, 'face %d %d' % f, 'goto %d %d 70 9000' % (b[0], b[2]), 'pos %s-through' % lbl, 'log BENCH1109 %s door %s: through goto done' % (lbl, d['host'])]
    return s


# ------------------------------------------------------------------ item segments
def hasta_seg(who):
    s = ['wait 6000']
    for i in range(14):
        s += ['ents BarricadeB_ 8', 'ents OYCHECK 8', 'ents Roadblock_01 4', 'ents Broken01 4', 'log BENCH1109 hasta sample %d' % i, 'wait 9000']
    s += ['pos hasta-end']
    return s


def vans_seg(who, lead, lbl):
    """Samples of the van entity every ~5 s from the load, at state 3 (waiting), every 1 s from state 5 (drives out), then after state 7.
    DM01B_1109 run 1: state 3 -> 5 after 8 s, the van drove east (x 4436 -> 5729 in 1 s), and at state 7 (8 s later) it sat back at its start
    pocket (-8000, 30500) for the rest of the run: the drive-out ends at 7 and the vehicle is reset (GUESS: stock, the pocket is unseen).
    Samples after 7 alone can't show the drive, so the drive is sampled in state 5."""
    s = []
    for i in range(6):
        s += ['ents V_Van 3', 'wait 5000']
    s += ['log BENCH1109 %s waiting for vehicle state 3' % lbl, 'waitvan 3 300000', 'ents V_Van 3', 'log BENCH1109 %s van at state 3' % lbl,
          'waitvan 5 150000', 'log BENCH1109 %s van at state 5 (drives out)' % lbl]
    for i in range(14):
        s += ['ents V_Van 3', 'wait 1000']
    s += ['waitvan 7 150000', 'log BENCH1109 %s van at state 7 (leaving)' % lbl]
    for i in range(6):
        s += ['ents V_Van 3', 'wait 3000']
    s += ['log BENCH1109 %s van leave samples done' % lbl]
    return s


def dm07_control():
    """Control for the walk-out test, from the live DM07 walk mesh (read-only): the same tele start (-3900, 10400; floor from the mesh, GUESS 402 when
    the mesh has nothing there) and a goto of the SAME length (2100) through open mesh, every 60 units of the line on the mesh, away from the -x gap.
    -> dict(start=[x, y, z], blocked=[-6000, 10400], control=[x, z], length) or None."""
    import kl_fa_bots as F
    nav = F.Nav(F.Built('%s/DM07/F06_Main.zip' % MAPS).scene.nav)
    sx, sz, L = -3900.0, 10400.0, 2100.0
    a = nav.at(sx, 402.0, sz, dy=300.0)
    if a is None:
        return None
    y0 = a[1]
    best = None
    for deg in range(0, 360, 15):
        dx, dz = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        if dx < -0.2:                                    # not toward the gap / the blocked line
            continue
        ok, y = True, y0
        for i in range(1, int(L // 60) + 1):
            h = nav.at(sx + dx * 60 * i, y, sz + dz * 60 * i, dy=60.0)
            if h is None or nav.clearance(sx + dx * 60 * i, h[1], sz + dz * 60 * i, 60.0) < 25.0:
                ok = False; break
            y = h[1]
        if ok:
            best = (deg, round(sx + dx * L), round(sz + dz * L)); break
    if best is None:
        return None
    return dict(start=[round(sx), round(y0 + 150), round(sz)], blocked=[-6000, 10400], control=[best[1], best[2]], length=L, deg=best[0])


def dm07_seg(who):
    # the two gate panels by name: DM07_1109 run 1 'ents Chainlink_Fence 8' listed 8 other fence pieces (EntranceSide_1m_*, Small_4m_1*) first
    s = ['ents Chainlink_Fence_4m_01 4', 'ents Chainlink_Fence_4m_11 4', 'log BENCH1109 dm07 fence panels read']
    # the walk BEFORE the van: run 1 walked after state 7 (round over, outro) and the player never moved (both gotos stuck at the tele point)
    if who == 'host':
        s += ['waitstate 0x19 90000']
        # players cannot walk out through the gap: stand east of the fence (floor from the mesh + 150), walk west through z 10400 toward x -6000.
        # CONTROL: from the same start, the same length through open mesh must be reached, else a blocked goto proves nothing (kit file dm07.json).
        p = '%s/dm07.json' % kd('DM07_1109')
        c = json.load(open(p)) if os.path.isfile(p) else dict(start=[-3900, 552, 10400], control=None)
        s += ['tele %d %d %d' % tuple(c['start']), 'wait 2500', 'pos dm07-east-of-fence', 'goto -6000 10400 200 15000', 'pos dm07-after-walk', 'log BENCH1109 dm07 walk west done']
        if c.get('control'):
            s += ['tele %d %d %d' % tuple(c['start']), 'wait 2500', 'goto %d %d 200 15000' % tuple(c['control']), 'pos dm07-after-control', 'log BENCH1109 dm07 control walk done']
    s += vans_seg(who, 0, 'dm07')
    return s


# DM07GATE_1109 crossings: (label, tele start = floor + 150, goto z). From the static read of live f35e4133 (HVK): fence line x about -4560..-4600,
# fence bottom y 471.5 over floor 393..413. A = 4m_02 (visible, 29 cm gap), B = 4m_03 (visible), H = 4m_01 (hidden, 58..79 cm gap; DM07_1109 run 2
# walked through here). 4m_09 / 4m_10 skipped (Pillar_F_07, ConcetePipe_19 nearby). Floors are GUESSes from the static read (tele snaps to ground).
# Order H first: DM07GATE_1109 run 1 (A, B, H) lost B and H to a police kill 18 s into the round (06:03:06, A stopped at x -4549 alive just before);
# DM07_1109 run 2 walked H first at round start and lived. The south walk goes LAST: in run 2 it ended at y 2 (-6897, 6593), the player died 4 s later
# (06:13:10) and A and B ran on the corpse.
GATE_WALKS = (('gateH', (-4000, 550, 10334)), ('gateA', (-4000, 562, 9793)), ('gateB', (-4000, 560, 9393)))
GATE_WALKS_UNHIDE = GATE_WALKS[:2]              # DM07UNHIDE_1109: H (4m_01, un-hidden there) first, then the A control (4m_02, visible)
GATE_WALKS_SINK = (('sink01', (-4000, 550, 10334)), ('sink11a', (-4000, 550, 10420)), ('sink11b', (-4000, 550, 10700)), ('sink10', (-4000, 550, 10850)))
GATE_XS = (-4400, -4520, -4620, -4750, -5000)   # goto steps: one pos per step, so the crossing is read without a mid-goto sample
# DM07CURTAIN_1109: (label, tele start, expect). Controls first (they do not die, and show the method discriminates), then the four gate crossings.
# 4m_01 z 9993..10393 (10334, 10420 = under 4m_11), 4m_11 z 10395..10795 (10600, 10700); z 9800 = visible 4m_02; z 10850 = 4m_10 (visible, past the curtain box z 10800).
CURTAIN_WALKS = (('curA', (-4000, 550, 9800), 'BLOCKED'), ('curB', (-4000, 550, 10850), 'BLOCKED'),
                 ('cur01', (-4000, 550, 10334), 'KILL'), ('cur11a', (-4000, 550, 10420), 'KILL'), ('cur11b', (-4000, 550, 10600), 'KILL'), ('cur11c', (-4000, 550, 10700), 'KILL'))
CURTAIN_X = -4560           # east edge of the curtain box: a corpse west of it died inside the box; a body blocked at the fence stands at -4549 / -4503 or east
CURTAIN_BOX_W = -4720       # west edge of the curtain box
CURTAIN_THROUGH = -4700     # alive west of this = through the gate
CURTAIN_MOVED = 300         # a walk counts only when the player moved this far in total from the settle point, else VOID
CURTAIN_RESPAWN_MS = 8000   # after a kill walk: wait (GUESS: a dead heister is back as police within that; else the next walks read DEAD-BEFORE = WARN)

# DM07PLANE_1109 / DM07PLANE72_1109: (label, tele start, kind). kind CTRL = visible fence panel, must read BLOCKED (the method discriminates); FREE = open ground east of the
# tele, must PASS (the player can move at all); GATE = a crossing of the hidden gate (panels z 9993..10393 / 10395..10795; z 10850 = visible 4m_10 past the gap) that must read
# BLOCKED; CROUCH = a gate crossing with the stance toggled low. Crouch is GUESS work: klauto has no crouch op, only key down/up/tap; LCONTROL is the assumed toggle key and
# the log (pos = actor origin) cannot show the stance, so the shots decide whether he really crouched. Coverage BELOW y 471 (the mud hole) is only reached by a capsule
# that overlaps the panels' old volume (kl_dm07plane_1109 docstring): any walker on the mud (feet 388..460) does, so every GATE walk tests it; the crouch walk is the
# lowest capsule this bench can make.
PLANE_WALKS = (('plA', (-4000, 550, 9800), 'CTRL'), ('plF', (-4000, 550, 10334), 'FREE'),
               ('pl9995', (-4000, 550, 9995), 'GATE'), ('pl10100', (-4000, 550, 10100), 'GATE'), ('pl10200', (-4000, 550, 10200), 'GATE'),
               ('pl10334', (-4000, 550, 10334), 'GATE'), ('pl10394', (-4000, 550, 10394), 'GATE'), ('pl10420', (-4000, 550, 10420), 'GATE'),
               ('pl10600', (-4000, 550, 10600), 'GATE'), ('pl10700', (-4000, 550, 10700), 'GATE'), ('pl10790', (-4000, 550, 10790), 'GATE'),
               ('pl10850', (-4000, 550, 10850), 'GATE'), ('plC10394', (-4000, 550, 10394), 'CROUCH'), ('plC10790', (-4000, 550, 10790), 'CROUCH'))
PLANE_FREE_XS = (-3800, -3600, -3400, -3200, -3000)    # the free walk goes EAST, away from the fence, along the same z
PLANE_FREE_MOVED = 700      # the free walk must cover this much from the settle point, else VOID (stuck start)
PLANE_THROUGH = -4600       # alive west of this = through the plane (x -4578; a blocked capsule stands east of ~ -4545: visible 4m_02 blocked at -4549 in the 11-09 runs)
PLANE_MIN_VALID = 7         # of the 12 gate + crouch crossings at least this many must read BLOCKED (the rest VOID / DIED = WARN)
PLANE_KITS = ('DM07PLANE_1109', 'DM07PLANE72_1109')
PLANE_VOID = ('VOID', 'DIED', 'DEAD-BEFORE')

# DD10GATE_1109: (label, tele start). Starts 135 cm east of the fence, south of the parked van's line (the van stops at z 1030, half width 110).
DD10_GATE_WALKS = (('dg900', (8150, 60, 900)), ('dg1000', (8150, 60, 1000)), ('dg1100', (8150, 60, 1100)))
DD10_GATE_XS = (8050, 7950, 7850, 7700, 7500)
DD10_THROUGH = 7960         # alive west of this = through the gate (fence x 7999..8014, plane x 8017; a blocked capsule stands ~40 cm east of it)
DD10_CTRL_MOVED = 150       # the control (goto east from the same tele) must move this far, else the start was stuck and the walk proves nothing


def dd10gate_seg(who):
    s = ['ents BigFence 4', 'ents Plane01 4', 'log BENCH1109 dd10 gate panels read']
    if who != 'host':
        return s + ['wait 60000']
    # call the van first (a heister in otrExitLevel with $0 calls it, dd10call1109) and let it park, so its drive-in cannot run over a walk
    s += ['waitstate 0x19 90000', 'tele 8300 50 800', 'wait 1000', 'waitvan 3 60000', 'ents V_Van 3', 'log BENCH1109 dd10gate van parked']
    for lbl, st in DD10_GATE_WALKS:
        s += ['tele %d %d %d' % st, 'wait 2000', 'pos %s-t' % lbl]
        for i, x in enumerate(DD10_GATE_XS):
            s += ['goto %d %d 60 %d' % (x, st[2], 3000 if i < len(DD10_GATE_XS) - 1 else 5000), 'pos %s-%d' % (lbl, i + 1)]
        s += ['tele %d %d %d' % st, 'wait 1500', 'pos %s-ct' % lbl, 'goto %d %d 40 3000' % (st[0] + 250, st[2]), 'pos %s-c' % lbl, 'log BENCH1109 dd10gate %s done' % lbl]
    return s


def dd10gate_walk(a, lbl, deaths):
    """-> (verdict, note): NOSAMPLE | DIED (a kind-3 row in the walk: no verdict) | THROUGH (alive west of DD10_THROUGH) | VOID (the control goto east from the same
    tele moved < DD10_CTRL_MOVED: stuck start) | BLOCKED."""
    names = ['t'] + [str(i) for i in range(1, len(DD10_GATE_XS) + 1)] + ['ct', 'c']
    ps = [pos_of(a, '%s-%s' % (lbl, n)) for n in names]
    miss = [n for n, p in zip(names, ps) if p is None]
    if miss:
        return 'NOSAMPLE', 'no pos line for %s' % ', '.join('%s-%s' % (lbl, n) for n in miss)
    t0 = next((secs_of(l) for l in a if 'pos %s-t:' % lbl in l), None)
    t1 = next((secs_of(l) for l in a if 'pos %s-c:' % lbl in l), None)
    walk, ct, c = ps[:-2], ps[-2], ps[-1]
    minx = min(p[0] for p in walk)
    path = ' '.join('(%d,%d,%d)' % p for p in walk)
    if t0 is not None and t1 is not None and [l for l in deaths if t0 < secs_of(l) <= t1 + 2]:
        return 'DIED', 'death row inside the walk; min x %d; %s' % (minx, path)
    if minx < DD10_THROUGH:
        return 'THROUGH', 'ALIVE at x %d (< %d): the hidden gate lets players out; %s' % (minx, DD10_THROUGH, path)
    cm = math.hypot(c[0] - ct[0], c[2] - ct[2])
    if cm < DD10_CTRL_MOVED:
        return 'VOID', 'control goto east moved only %.0f cm (< %d): stuck start; %s' % (cm, DD10_CTRL_MOVED, path)
    return 'BLOCKED', 'min x %d, control moved %.0f; %s' % (minx, cm, path)


def gate_seg(who, walks=None, south=True):
    # 4m_11 by its full name: run 1's 'ents Chainlink_Fence_4m_1 6' showed 6 of 8 (_19.._12) and missed it
    s = ['ents Chainlink_Fence_4m_0 12', 'ents Chainlink_Fence_4m_11 2', 'log BENCH1109 gate fence panels read']
    if who != 'host':
        return s + ['wait 60000']
    # right after the round starts: DM07_1109 run 2's control walk ran late and a cop downed the player at (-2905, 10432)
    s += ['waitstate 0x19 90000']
    for lbl, st in (walks or GATE_WALKS):
        s += ['tele %d %d %d' % st, 'wait 2000', 'face -5000 %d' % st[2], 'pos %s-0' % lbl]
        for i, x in enumerate(GATE_XS):
            s += ['goto %d %d 60 %d' % (x, st[2], 3000 if i < len(GATE_XS) - 1 else 5000), 'pos %s-%d' % (lbl, i + 1)]
        s += ['log BENCH1109 gate %s done' % lbl]
    if not south:
        return s
    # from the pocket (H gets through): does its south slope lead off the map? (static read: mud floor x -11000..-4600, outside every LevelBound)
    s += ['tele -4944 450 10333', 'wait 2000', 'goto -6900 8100 100 9000', 'pos gateS-1', 'goto -6900 6500 100 9000', 'pos gateS-2', 'log BENCH1109 gate south done']
    return s


def plane_seg(who):
    """DM07PLANE*_1109 crossings, the curtain_seg pattern (tele, wait, pos -t, short settle goto east, pos -s, then the goto steps with a pos each); the FREE walk steps
    east, a CROUCH walk taps LCONTROL after the tele (GUESS: toggle) and again at the end. Labels: <lbl>-t, <lbl>-s, <lbl>-1..5."""
    s = ['ents Chainlink_Fence_4m_0 12', 'ents Chainlink_Fence_4m_11 2', 'log BENCH1109 plane fence panels read']
    if who != 'host':
        return s + ['wait 60000']
    s += ['waitstate 0x19 90000']
    for lbl, st, kind in PLANE_WALKS:
        s += ['tele %d %d %d' % st, 'wait 2000', 'pos %s-t' % lbl]
        if kind == 'CROUCH':
            s += ['tap LCONTROL', 'wait 800']
        s += ['goto %d %d 60 2500' % (st[0] + 150, st[2]), 'pos %s-s' % lbl, 'face %d %d' % ((-3000 if kind == 'FREE' else -5000), st[2])]
        xs = PLANE_FREE_XS if kind == 'FREE' else GATE_XS
        for i, x in enumerate(xs):
            s += ['goto %d %d 60 %d' % (x, st[2], 3000 if i < len(xs) - 1 else 5000), 'pos %s-%d' % (lbl, i + 1)]
        if kind == 'CROUCH':
            s += ['tap LCONTROL', 'wait 800']
        s += ['log BENCH1109 plane %s done' % lbl]
    return s


def curtain_seg(who):
    """DM07CURTAIN_1109 crossings. Fixes the control bugs of GATE/UNHIDE (their walks never moved: a tele start landed stuck, z-10334 walks began at
    (-4009, 403, 10236), ~100 cm off the tele): tele, wait, then a short SETTLE goto 150 cm east (open ground) and a pos read before the walk; the verdict
    only counts a walk that moved >= CURTAIN_MOVED cm in total from the settle point. Labels: <lbl>-t tele, <lbl>-s settled, <lbl>-1..5 the goto steps."""
    s = ['ents Chainlink_Fence_4m_0 12', 'ents Chainlink_Fence_4m_11 2', 'ents NoCover 10', 'log BENCH1109 curtain fence panels read']
    if who != 'host':
        return s + ['wait 60000']
    s += ['waitstate 0x19 90000']
    for lbl, st, exp in CURTAIN_WALKS:
        s += ['tele %d %d %d' % st, 'wait 2000', 'pos %s-t' % lbl, 'goto %d %d 60 2500' % (st[0] + 150, st[2]), 'pos %s-s' % lbl, 'face -5000 %d' % st[2]]
        for i, x in enumerate(GATE_XS):
            s += ['goto %d %d 60 %d' % (x, st[2], 3000 if i < len(GATE_XS) - 1 else 5000), 'pos %s-%d' % (lbl, i + 1)]
        s += ['log BENCH1109 curtain %s done' % lbl]
        if exp == 'KILL':
            s += ['wait %d' % CURTAIN_RESPAWN_MS]
    return s


def dm03_seg(who, doors):
    s = ['wait 4000', 'ents VehicleExit 12', 'ents ArrivingCops 40', 'ents Garage 30', 'ents Ramp 30', 'log BENCH1109 dm03 t0 census']
    for i in range(1, 6):
        s += ['wait 15000', 'ents ArrivingCops 40', 'ents Cop 60', 'ents Police 60', 'log BENCH1109 dm03 sample %d' % i]
    if who == 'host' and doors:
        s += door_seg(doors[0], 'dm03door')
    return s


def doors_seg(who, doors, lbl):
    s = ['wait 5000']
    if who == 'host':
        for i, d in enumerate(doors):
            s += door_seg(d, '%s%d' % (lbl, i + 1)) + ['wait 2000']
    else:
        s += ['ents KL_Door 20', 'wait 60000', 'ents KL_Door 20']
    return s


def segment(k, who):
    doors = []
    p = '%s/doors.json' % kd(k)
    if os.path.isfile(p):
        doors = json.load(open(p))
    if k == 'HASTA1109':
        return hasta_seg(who)
    if k == 'DM03_1109':
        return dm03_seg(who, doors)
    if k == 'DM02_1109':
        return doors_seg(who, doors, 'dm02door')
    if k == 'DM01B_1109':
        return vans_seg(who, 0, 'dm01b')
    if k == 'DM07_1109':
        return dm07_seg(who)
    if k == 'DM07GATE_1109':
        return gate_seg(who)
    if k == 'DM07UNHIDE_1109':
        return gate_seg(who, GATE_WALKS_UNHIDE, south=False)
    if k == 'DM07SINK_1109':
        return gate_seg(who, GATE_WALKS_SINK, south=False) + vans_seg(who, 0, 'dm07')
    if k == 'DD10GATE_1109':
        return dd10gate_seg(who)
    if k == 'DM07CURTAIN_1109':
        # van first: the walks + respawn waits take ~150 s and DM07_1109 saw state 3 at ~90 s; waitvan matches 3/4 only, so a van already at 5/7
        # after the walks would time out (300 s + 150 s). The walks then run in round 2 (curtain_seg starts with waitstate 0x19).
        return vans_seg(who, 0, 'dm07') + ['wait 15000'] + curtain_seg(who)
    if k in PLANE_KITS:
        # van first (as the curtain kit): the 14 walks take ~5 min and the van is called early in round 1; the walks then run in round 2
        return vans_seg(who, 0, 'dm07') + ['wait 15000'] + plane_seg(who)
    return doors_seg(who, doors, 'door')


# ------------------------------------------------------------------ generation
def probes(k):
    return ['[Memory]', 'Log=1', 'D3dShotPost=1', '[ReShade]', 'Bridge=1']


B.probes = probes


def pair(k, who):
    q = '%s/Q32_%s_%s.ini' % (B.Q32, K[k]['map'], who)
    secs, scr = B.read_secs(q), B.script_of(q)
    i = next(j for j, l in enumerate(scr) if l.startswith('waitload')) + 1
    seg = ['log BENCH1109 %s %s level loaded' % (k, who)] + segment(k, who) + ['log BENCH1109 %s %s segment done' % (k, who)]
    scr = scr[:i] + seg + scr[i:]
    t = ['; bench_1109 %s %s: Q32 pair (round 1 -> shop -> round 2) + item segment after waitload + shot probes' % (k, who)]
    total = 1950
    for name, kv in secs:
        if name == 'Script':
            continue
        if name == 'Auto':
            # KeepAlive=1 (klauto.c kla_keep_alive, TEST rig only): refills the local player's health every poll. Police killed the host ~19 s
            # into the round on DOORS_1109_DM01 runs 2/3, DM07GATE runs 1/2 and DM07UNHIDE (control A), voiding the verdicts; both seats
            # K[k]['keepalive'] = 0 (DM07CURTAIN_1109 only): written as KeepAlive=0 so a KillBox death cannot be refilled
            kv = [(a, b) for a, b in kv if a not in ('CmdAdd', 'MaxRunMs', 'KeepAlive')] + [('CmdAdd', '-o DisableSplashScreens -o AutoExit=%d' % total), ('MaxRunMs', str((total - 10) * 1000)),
                                                                                           ('KeepAlive', '1' if K[k]['keepalive'] else '0')]
        t.append('[%s]' % name)
        t += ['%s=%s' % kv_ for kv_ in kv]
    t += probes(k) + ['[Script]'] + B.renumber(scr)
    return '\n'.join(t) + '\n'


def md5_of(b):
    import hashlib
    return hashlib.md5(b).hexdigest()


def base_ini():
    """-> (bytes, source). The live KLHook.ini when it is the INI_KIT one (INI_MD5, read only); else (a bench is running and has swapped its own ini in)
    the ini INI_KIT's install.py would write: its .before-<INI_TAG> backup + its KEYS, accepted only when that md5 is INI_MD5."""
    live = open('%s/KLHook.ini' % DD, 'rb').read()
    if md5_of(live) == INI_MD5:
        return live, 'live KLHook.ini'
    import importlib.util
    sp = importlib.util.spec_from_file_location(INI_TAG + '_install', INI_KIT + '/install.py')
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    bak = '%s/KLHook.ini.before-%s' % (DD, INI_TAG)
    out = m.set_keys(open(bak, 'rb').read().decode('latin1'), m.KEYS).encode('latin1')
    if md5_of(out) != INI_MD5:
        raise SystemExit('gen: live KLHook.ini is %s (not %s) and %s + %s keys gives %s: no base ini, stop' % (md5_of(live)[:8], INI_MD5[:8], bak, INI_TAG, md5_of(out)[:8]))
    return out, '%s install.py set_keys on KLHook.ini.before-%s (live differed: %s)' % (INI_TAG, INI_TAG, md5_of(live)[:8])


def stamp(k):
    """Pin the kit to MERGED: the TEST twin dll from its folder and the base ini; record both (and the SHIP they twin) in kit.json."""
    import shutil
    d = kd(k)
    src = MERGED + '/dll_test/dinput8.dll'
    if md5_of(open(src, 'rb').read()) != TEST_MD5:
        raise SystemExit('gen: %s is not the TEST twin %s' % (src, TEST_MD5[:8]))
    shutil.copy2(src, '%s/hook_test/dinput8.dll' % d)
    ini, how = base_ini()
    open('%s/KLHook_base.ini' % d, 'wb').write(ini)
    B.write('%s/kit.json' % d, json.dumps(dict(ship=SHIP_MD5, test=TEST_MD5, ini=md5_of(ini), ini_source=how, merged=MERGED, built_from=BUILT_FROM), indent=1))


def gen(which='all'):
    for k in ORDER:
        if which not in ('all', k) and not (which == 'DOORS_1109' and k.startswith('DOORS_1109_')):
            continue
        B.gen(k)
        stamp(k)
        d = kd(k)
        if k == 'DM07_1109':
            c = dm07_control()
            B.write('%s/dm07.json' % d, json.dumps(c or dict(start=[-3900, 552, 10400], control=None), indent=1))
            print('  DM07 walk control: %s' % (c or 'NONE FOUND (validate will FAIL)'))
        if 'doors' in K[k] or 'doors2' in K[k]:
            dd = door_data(k)
            B.write('%s/doors.json' % d, json.dumps(dd, indent=1))
            for x in dd:
                print('  %s door %s %s hinge %s front %s back %s' % (k, x['host'], x['name'], x['hinge'], x['front'], x['back']))
        B.write('%s/online_host.ini' % d, pair(k, 'host'))
        B.write('%s/online_join.ini' % d, pair(k, 'join'))
    print('gen: kits under', KIT)


# ------------------------------------------------------------------ validate
def validate(which):
    names = [k for k in ORDER if which in ('all', k) or (which == 'DOORS_1109' and k.startswith('DOORS_1109_'))]
    if not names:
        print('unknown kit', which); return 2
    rc = B.validate(which) if which in K else B.validate('all') if which == 'all' else 0
    if which == 'DOORS_1109':
        rc = max(B.validate(n) for n in names)
    v = B.V()
    for k in names:
        print('[%s] bench_1109 extras' % k)
        d = kd(k)
        for who in ('host', 'join'):
            p = '%s/online_%s.ini' % (d, who)
            if not os.path.isfile(p):
                v.ok(False, '%s missing (run gen)' % p); continue
            scr = B.script_of(p)
            v.ok(any(l.startswith('log BENCH1109') for l in scr), '%s carries the BENCH1109 item segment (%d script lines)' % (who, len(scr)))
            iw = next((j for j, l in enumerate(scr) if l.startswith('waitload')), -1)
            v.ok(iw >= 0 and scr[iw + 1].startswith('log BENCH1109'), '%s: segment sits right after waitload' % who)
            v.ok(any('Bridge=1' in x for x in open(p, encoding='latin-1').read().splitlines()), '%s: ReShade bridge + D3dShotPost probes' % who)
            ka = [x.strip() for x in open(p, encoding='latin-1').read().splitlines() if x.strip().lower().startswith('keepalive=')]
            v.ok(ka == ['KeepAlive=%d' % K[k]['keepalive']], '%s: [Auto] %s (K keepalive=%d%s)' % (who, ka, K[k]['keepalive'], ': OFF for this kit, a KillBox death must not be refilled' if not K[k]['keepalive'] else ''))
            if who == 'host' and (K[k].get('doors') or K[k].get('doors2')):
                dj = '%s/doors.json' % d
                dd = json.load(open(dj)) if os.path.isfile(dj) else []
                v.ok(bool(dd), 'doors.json: %d doors, stand points %s' % (len(dd), [bool(x['front'] or x['back']) for x in dd]))
                # one-sided doors kick from the stand and no longer walk (DOORS_1109_DM01 run 1: the walk to the hinge left the kick box)
                v.ok(any('tele' in l for l in scr) and any(l.startswith('tap E') for l in scr), 'host script teleports to the stand and kicks there (tap E)')
        kj = '%s/kit.json' % d
        rec = json.load(open(kj)) if os.path.isfile(kj) else {}
        v.ok(bool(rec), 'kit.json (the SHIP / TEST twin / ini this kit was built against)')
        dll = '%s/hook_test/dinput8.dll' % d
        dm = md5_of(open(dll, 'rb').read()) if os.path.isfile(dll) else '-'
        v.ok(rec.get('test') == TEST_MD5 and rec.get('ship') == SHIP_MD5 and dm == TEST_MD5,
             'kit dll %s = recorded TEST twin %s of SHIP %s (module pins %s / %s)' % (dm[:8], str(rec.get('test'))[:8], str(rec.get('ship'))[:8], TEST_MD5[:8], SHIP_MD5[:8]))
        pj = MERGED + '/pins.json'
        pins = json.load(open(pj)) if os.path.isfile(pj) else {}
        news = {x.get('new') for n_, x in pins.items() if n_.lower().endswith('dinput8.dll')}
        v.ok(SHIP_MD5 in news, "the merged kit's own pins.json installs SHIP %s (the SHIP this kit twins)" % SHIP_MD5[:8])
        tw = MERGED + '/dll_test/dinput8.dll'
        v.ok(os.path.isfile(tw) and md5_of(open(tw, 'rb').read()) == TEST_MD5, 'merged kit dll_test twin %s is still %s' % (md5_of(open(tw, 'rb').read())[:8] if os.path.isfile(tw) else '-', TEST_MD5[:8]))
        ld = '%s/dinput8.dll' % DD
        lm = md5_of(open(ld, 'rb').read()) if os.path.isfile(ld) else '-'
        if lm in (SHIP_MD5, TEST_MD5):
            v.ok(True, 'live dinput8.dll %s is the merged kit SHIP or twin (%s)' % (lm[:8], 'SHIP' if lm == SHIP_MD5 else "the TEST twin: a bench has swapped it in"))
        else:
            swapped = os.path.isfile(ld) and b"klauto's scripted keys" in open(ld, 'rb').read()
            v.ok(False, 'live dinput8.dll %s is neither SHIP %s nor the twin %s: %s' % (lm[:8], SHIP_MD5[:8], TEST_MD5[:8],
                 "it carries klauto (a peer's TEST dll swapped in by a bench): cannot say which SHIP is live, re-run validate when the game is free" if swapped else 'a newer SHIP is live, this kit is STALE: gen it again from that kit\'s TEST twin'),
                 warn=swapped)
        bi = '%s/KLHook_base.ini' % d
        if os.path.isfile(bi):
            raw = open(bi, 'rb').read()
            v.ok(md5_of(raw) == INI_MD5 and rec.get('ini') == INI_MD5, 'base ini md5 %s = recorded %s = merged kit live ini %s (%s)' % (md5_of(raw)[:8], str(rec.get('ini'))[:8], INI_MD5[:8], rec.get('ini_source', '?')))
            sec, got = None, set()
            for l in raw.decode('latin1').splitlines():
                m_ = re.match(r'\s*\[([^\]]+)\]', l)
                if m_:
                    sec = m_.group(1).lower()
                elif sec:
                    kv = re.match(r'\s*(\w+)\s*=\s*(\w+)', l)
                    if kv and (sec, kv.group(1).lower(), kv.group(2)) in {(s_.lower(), k_.lower(), v_) for s_, k_, v_ in INI_KEYS}:
                        got.add((sec, kv.group(1).lower()))
            v.ok(len(got) == len(INI_KEYS), 'base ini carries %s (%d of %d)' % (', '.join('[%s] %s=%s' % x for x in INI_KEYS), len(got), len(INI_KEYS)))
        if k == 'DM07_1109':
            cj = '%s/dm07.json' % d
            cc = json.load(open(cj)) if os.path.isfile(cj) else {}
            v.ok(bool(cc.get('control')), 'dm07.json: walk control (same start, length %s) %s' % (cc.get('length', '?'), cc.get('control')))
            v.ok(any('goto %d %d' % tuple(cc['control']) in l for l in (B.script_of('%s/online_host.ini' % d))) if cc.get('control') else False, 'host script runs the control goto')
        base = '%s/KLHook_base.ini' % d
        if os.path.isfile(base):
            txt = open(base, encoding='latin-1').read()
            cb = (re.search(r'^ClientBuildMaps=([^\s;]*)', txt, re.M) or [0, ''])[1].split(',')
            need = K[k]['slot'] in ('F01', 'F03')          # only the DM01 / DM03 slots need the client build (memory: DM03 clients assert without it); the others load as they are
            v.ok(K[k]['slot'] in cb or not need, 'ClientBuildMaps=%s: %s %s' % (','.join(cb), K[k]['slot'], 'listed (needed for this slot)' if need else 'not needed for this slot (live setup, as the dm06b benches)'))
    print('RESULT: bench_1109 extras %s - %d FAIL (B.validate rc %d)' % ('OK' if not v.fail else 'FAILED', v.fail, rc))
    return 1 if (v.fail or rc) else 0


# ------------------------------------------------------------------ verify
# slot, name, flags, position of one `ents` row (klauto.c: "script N: ents #i slot S obj O name 'NAME' class C ... (flags F) pos (x, y, z)")
ENT = re.compile(r"ents #\d+ slot (\d+) obj \w+ name '([^']*)' .*?\(flags ([0-9a-fA-F]+)\) pos [^(]*\((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)")
# "pos <label>: me #N (x, y, z) heading H" (klauto.c kla_log_pos): the label and the coordinates by NAME
POSL = re.compile(r"\bpos (\S+): me #\d+ \((-?\d+), (-?\d+), (-?\d+)\) heading")


def ents(lines, sub):
    """-> [(time, name, hidden, (x, y, z), slot, line index)] for every ents row whose name contains sub."""
    out = []
    for i, l in enumerate(lines):
        m = ENT.search(l)
        if m and sub.lower() in m.group(2).lower():
            out.append((l[:12], m.group(2), bool(int(m.group(3), 16) & 0x400), tuple(float(m.group(j)) for j in (4, 5, 6)), int(m.group(1)), i))
    return out


HASTA_VAULT = (26200.0, 14000.0)                  # x, z of the DM11B loot wing wall (HASTA1109 log: barricade 26409/14031, roadblock 26560/13426)


def by_entity(rows):
    """rows -> {(slot, full name): [rows in log order]}: one entry per entity, never per name fragment."""
    g = {}
    for r in rows:
        g.setdefault((r[4], r[1]), []).append(r)
    return g


def secs_of(t):
    return int(t[0:2]) * 3600 + int(t[3:5]) * 60 + float(t[6:12])


def goto_lines(lines, x, z):
    return [l for l in lines if re.search(r'script \d+: goto \(%d, %d\) ' % (x, z), l)]


def reached(g):
    """The last goto line of g says 'reached' (and not 'NOT reached')."""
    return bool(g) and ' reached ' in g[-1] and 'NOT reached' not in g[-1]


def pos_of(lines, label):
    """(x, y, z) of the LAST `pos <label>:` line, or None."""
    r = [tuple(int(m.group(j)) for j in (2, 3, 4)) for m in (POSL.search(l) for l in lines) if m and m.group(1) == label]
    return r[-1] if r else None


def kick_states(a, lbl, when):
    """{controller slot: state} from the kick_probe lines '<lbl>-<when>-ctrlN-state' (raw hex)."""
    out = {}
    for l in a:
        m = re.search(r'= ([0-9a-f]{8}) \(at [0-9a-f]+\)\s+%s-%s-ctrl(\d+)-state' % (re.escape(lbl), re.escape(when)), l)
        if m:
            out[int(m.group(2))] = int(m.group(1), 16)
    return out


def door_lbl(k, i):
    return 'dm03door' if k == 'DM03_1109' else 'dm02door%d' % (i + 1) if k == 'DM02_1109' else 'door%d' % (i + 1)


STOP_DM01B = (4454, 31907)
# x, z of each staged route's unseen START / END pocket (re/vehicle_routes_1108.md: DM01B waits (-8000, 30500), ends (17400, 30400), seen by 0
# viewers at both; DM07 waits and ends in the floorless mud pocket (-9300, 10400)). A jump from the END pocket to the START pocket is the
# vehicle's reset at the drive-out end (DM01B_1109 run 2: 17365, 31663 -> -8000, 30500 a second before state 7), not a pop on screen.
# DM07: the reset goes to the van NODE's own place (-6000, 397, 10400; hidden there at load), not to the staged key-0 pocket -9300
# (DM07_1109 run 1: reversed 700 -> -5384 in 8 s, then sat at -6000 from 1 s later to the end). GUESS: DM01B's node sits in its start pocket.
POCKETS = {'DM01B_1109': ((-8000, 30500), (17400, 30400)), 'DM07_1109': ((-6000, 10400), (-9300, 10400))}


CURTAIN_VOID = ('VOID', 'DIED-EAST', 'DEAD-BEFORE')       # no verdict: WARN, rerun


def curtain_walk(a, lbl, deaths, lives):
    """One DM07CURTAIN_1109 crossing from the host log -> (verdict, note). Samples <lbl>-t (tele), -s (settled), -1..-5 (goto steps).
    NOSAMPLE (a pos line missing) | DEAD-BEFORE (dead at the tele, no kind-1 row since) | VOID (moved < CURTAIN_MOVED cm in total from the settle point: stuck / frozen,
    the GATE/UNHIDE walks never moved that way) | THROUGH (alive, x < CURTAIN_THROUGH) | INSIDE (alive, CURTAIN_THROUGH <= x < CURTAIN_X: in the box, not killed)
    | KILLED (a kind-3 row inside the walk and a sample west of CURTAIN_X: died in the curtain box; GUESS: FA_DieFromSelf logs kind 3 like FA_DieFromPolice)
    | DIED-EAST (a kind-3 row but never west of CURTAIN_X: police or other, no verdict) | BLOCKED (alive, never west of CURTAIN_X)."""
    names = ['t', 's'] + [str(i) for i in range(1, len(GATE_XS) + 1)]
    ps = [pos_of(a, '%s-%s' % (lbl, n)) for n in names]
    miss = [n for n, p in zip(names, ps) if p is None]
    if miss:
        return 'NOSAMPLE', 'no pos line for %s' % ', '.join('%s-%s' % (lbl, n) for n in miss)
    walk = ps[1:]
    moved = sum(math.hypot(p[0] - q[0], p[2] - q[2]) for p, q in zip(walk, walk[1:]))
    t0 = next((secs_of(l) for l in a if 'pos %s-t:' % lbl in l), None)
    t1 = next((secs_of(l) for l in a if 'pos %s-%d:' % (lbl, len(GATE_XS)) in l), None)
    if t0 is None or t1 is None:
        return 'NOSAMPLE', 'no timestamps for %s' % lbl
    # a death before the tele with no kind-1 row since: the player is a corpse (or not yet back) for the whole walk
    before = [secs_of(l) for l in deaths if secs_of(l) <= t0]
    if before and not any(before[-1] < secs_of(v) <= t0 for v in lives):
        return 'DEAD-BEFORE', 'dead at %.1f s before the tele, no respawn row since' % (t0 - before[-1])
    died = [l[:12] for l in deaths if t0 < secs_of(l) <= t1 + 2]
    minx = min(p[0] for p in walk)
    path = ' '.join('(%d,%d,%d)' % p for p in ps)
    if died:
        if minx < CURTAIN_BOX_W:
            return 'THROUGH', 'death row at %s but a sample at x %d is WEST of the box (%d): passed the curtain first; %s' % (died[0], minx, CURTAIN_BOX_W, path)
        if minx < CURTAIN_X:
            return 'KILLED', 'death row at %s, west of x %d (min x %d); moved %.0f; %s' % (died[0], CURTAIN_X, minx, moved, path)
        return 'DIED-EAST', 'death row at %s, never west of x %d (min x %d): not the curtain; %s' % (died[0], CURTAIN_X, minx, path)
    if minx < CURTAIN_THROUGH:
        return 'THROUGH', 'ALIVE at x %d (< %d); moved %.0f; %s' % (minx, CURTAIN_THROUGH, moved, path)
    if moved < CURTAIN_MOVED:
        return 'VOID', 'moved only %.0f cm from the settle point (< %d): stuck, no verdict; %s' % (moved, CURTAIN_MOVED, path)
    if minx < CURTAIN_X:
        return 'INSIDE', 'ALIVE at x %d inside the curtain box (%d..%d): the KillBox did not kill; moved %.0f; %s' % (minx, CURTAIN_THROUGH, CURTAIN_X, moved, path)
    return 'BLOCKED', 'end x %d, min x %d, moved %.0f; %s' % (walk[-1][0], minx, moved, path)


def plane_walk(a, lbl, kind, deaths, lives):
    """One DM07PLANE*_1109 crossing from the host log -> (verdict, note). Samples <lbl>-t (tele), -s (settled), -1..-5 (goto steps).
    NOSAMPLE | DEAD-BEFORE (corpse at the tele) | DIED (a kind-3 row in the walk, never west of PLANE_THROUGH) | KILLED (a kind-3 row and a sample west of PLANE_THROUGH:
    passed the plane first, then died) | FREE walks: PASSED (moved >= PLANE_FREE_MOVED) / VOID | other walks: THROUGH (alive west of PLANE_THROUGH) | VOID (moved <
    CURTAIN_MOVED from the settle point) | BLOCKED (alive, stayed east of PLANE_THROUGH after a real walk)."""
    names = ['t', 's'] + [str(i) for i in range(1, 6)]
    ps = [pos_of(a, '%s-%s' % (lbl, n)) for n in names]
    miss = [n for n, p in zip(names, ps) if p is None]
    if miss:
        return 'NOSAMPLE', 'no pos line for %s' % ', '.join('%s-%s' % (lbl, n) for n in miss)
    walk = ps[1:]
    moved = sum(math.hypot(p[0] - q[0], p[2] - q[2]) for p, q in zip(walk, walk[1:]))
    t0 = next((secs_of(l) for l in a if 'pos %s-t:' % lbl in l), None)
    t1 = next((secs_of(l) for l in a if 'pos %s-5:' % lbl in l), None)
    if t0 is None or t1 is None:
        return 'NOSAMPLE', 'no timestamps for %s' % lbl
    before = [secs_of(l) for l in deaths if secs_of(l) <= t0]
    if before and not any(before[-1] < secs_of(v) <= t0 for v in lives):
        return 'DEAD-BEFORE', 'dead at %.1f s before the tele, no respawn row since' % (t0 - before[-1])
    died = [l[:12] for l in deaths if t0 < secs_of(l) <= t1 + 2]
    minx = min(p[0] for p in walk)
    path = ' '.join('(%d,%d,%d)' % p for p in ps)
    if died:
        if kind != 'FREE' and minx < PLANE_THROUGH:
            return 'KILLED', 'death row at %s but a sample at x %d is WEST of the plane (%d): passed it first; %s' % (died[0], minx, PLANE_THROUGH, path)
        return 'DIED', 'death row at %s (min x %d): police or other, no verdict; %s' % (died[0], minx, path)
    if kind == 'FREE':
        if moved >= PLANE_FREE_MOVED:
            return 'PASSED', 'moved %.0f cm east, end x %d; %s' % (moved, walk[-1][0], path)
        return 'VOID', 'moved only %.0f cm (< %d): stuck start, the free path proves nothing; %s' % (moved, PLANE_FREE_MOVED, path)
    if minx < PLANE_THROUGH:
        return 'THROUGH', 'ALIVE at x %d (< %d); moved %.0f; %s' % (minx, PLANE_THROUGH, moved, path)
    if moved < CURTAIN_MOVED:
        return 'VOID', 'moved only %.0f cm from the settle point (< %d): stuck, no verdict; %s' % (moved, CURTAIN_MOVED, path)
    return 'BLOCKED', 'end x %d, min x %d, moved %.0f; %s' % (walk[-1][0], minx, moved, path)


def item_checks(k, a, dd=(), ctrl=None):
    """The map-specific checks over the host log `a` (list of lines). -> (checks, infos); a check is (status, name, detail), status PASS / FAIL / WARN.
    No vacuous PASS: an empty log, a missing sample or a missing row is a FAIL for every kit (tools/kl_bench_1109_test.py runs this on synthetic logs).
    dd = doors.json rows, ctrl = dm07.json."""
    res, info = [], []

    def chk(name, cond, detail='', warn=False):
        res.append(('PASS' if cond else ('WARN' if warn else 'FAIL'), name, detail))
    chk('item segment ran on the host (level loaded ... segment done)', any('BENCH1109 %s host level loaded' % k in l for l in a) and any('BENCH1109 %s host segment done' % k in l for l in a),
        '%d host log lines' % len(a))
    if k == 'HASTA1109':
        for pat, before in (('OYCHECK_BEFORE01', True), ('BarricadeB_01', True), ('Roadblock_01', True), ('Broken01', False), ('OYCHECK_AFTER01', False)):
            # only the vault's own pieces: the map has a second ColiObj_Obj_Roadblock_01 at (13721, 4735) that the beat never touches
            g = by_entity([r for r in ents(a, pat) if abs(r[3][0] - HASTA_VAULT[0]) < 3000 and abs(r[3][2] - HASTA_VAULT[1]) < 3000])
            bad = []
            for (slot, name), r in sorted(g.items()):
                first, last = r[0][2], r[-1][2]
                if len(r) < 2 or not ((not first and last) if before else (first and not last)):
                    bad.append('%s (%d rows, first hidden=%s, last hidden=%s)' % (name, len(r), first, last))
            chk('%s: every entity %s' % (pat, 'visible at load, hidden by the beat' if before else 'hidden at load, shown after the beat (30 s backstop opens it)'),
                bool(g) and not bad, '%d entities%s' % (len(g), ('; WRONG: ' + ' | '.join(bad)) if bad else ('' if g else ' (no ents row: not sampled)')))
        info.append('boom / camera shake / glare: not logged; LOOK at KLShot_inst1_*.jpg around the beat (timestamps of the hasta sample lines)')
        info += [l[:12] + ' ' + l[13:90] for l in a if 'BENCH1109 hasta sample' in l]
    if k in ('DM01B_1109', 'DM07_1109', 'DM07SINK_1109', 'DM07CURTAIN_1109') + PLANE_KITS:
        # the van body only: DM01B_1109 run 1 matched 'V_Van_Reflection' (a ZGROUP parked at y -60000) first and judged its position
        van = [r for r in ents(a, 'V_Van') if 'reflection' not in r[1].lower() and r[3][1] > -50000]
        s3 = next((l for l in a if 'BENCH1109' in l and 'van at state 3' in l), None)
        s5 = next((l for l in a if 'BENCH1109' in l and 'van at state 5' in l), None)
        s7 = next((l for l in a if 'BENCH1109' in l and 'van at state 7' in l), None)
        chk('van entity sampled', bool(van), '%d rows' % len(van))
        chk('vehicle state 3 reached (van waits)', s3 is not None, s3[:12] if s3 else 'waitvan 3 timed out (the van never waited within 300 s)')
        chk('vehicle state 7 reached (van leaves)', s7 is not None, s7[:12] if s7 else 'waitvan 7 timed out')
        t3 = secs_of(s3) if s3 else None
        t7 = secs_of(s7) if s7 else None
        at3 = sorted((v for v in van if t3 is not None and abs(secs_of(v[0]) - t3) < 4), key=lambda v: abs(secs_of(v[0]) - t3)) if van else []
        t5 = secs_of(s5) if s5 else None
        chk('vehicle state 5 reached (van drives out)', s5 is not None, s5[:12] if s5 else 'waitvan 5 timed out')
        # the drive: samples from state 5 up to state 7 (after 7 the vehicle is reset to its start pocket)
        late = [v for v in van if t5 is not None and secs_of(v[0]) >= t5 and (t7 is None or secs_of(v[0]) <= t7)]
        chk('van sampled at state 3 (within 4 s)', bool(at3), '%d rows' % len(at3))
        chk('van sampled while it drives out (state 5 .. 7, >= 3 rows)', len(late) >= 3, '%d rows' % len(late))
        if k == 'DM01B_1109':
            stop = STOP_DM01B
            n = at3[0] if at3 else None                                       # the sample nearest the state-3 line: x and z of the SAME row
            chk('van waits near the stop (4454, 31907)', n is not None and math.hypot(n[3][0] - stop[0], n[3][2] - stop[1]) < 2500,
                'at state 3: %s' % (str(n[3]) if n else 'no sample'))
            chk('van starts west (x < stop - 3000) at the first sample', bool(van) and van[0][3][0] < stop[0] - 3000, 'first %s' % (str(van[0][3]) if van else 'no sample'))
            chk('van drives EAST of the stop (state 5 .. 7)', bool(late and at3) and max(v[3][0] for v in late) > at3[0][3][0] + 3000,
                'stop x %s, farthest x %s' % ('%.0f' % at3[0][3][0] if at3 else '-', '%.0f' % max(v[3][0] for v in late) if late else '-'))
        else:
            chk('van reverses out WEST (state 5 .. 7)', bool(late and at3) and min(v[3][0] for v in late) < at3[0][3][0] - 500,
                'stop x %s, farthest x %s' % ('%.0f' % at3[0][3][0] if at3 else '-', '%.0f' % min(v[3][0] for v in late) if late else '-'))
        if s7:
            after = [v for v in van if secs_of(v[0]) > t7]
            if after:
                info.append('after state 7 the van is at %s (a reset to its start pocket is the drive-out end, GUESS stock)' % str(after[-1][3]))
        if s5:
            seq = late
            steps = [math.dist(x[3], y[3]) / max(0.1, secs_of(y[0]) - secs_of(x[0])) for x, y in zip(seq, seq[1:])]
            info.append('leave speeds (cm/s between samples, a pop would be one outlier): %s' % ' '.join('%.0f' % s for s in steps[:12]))
        if s3:
            # a jump > 5000 cm between samples <= 6 s apart from state 3 on: DM01B_1109 run 1 drove east to x 5729, then at state 7 sat at the
            # start pocket (-8000, 30500) for the rest of the run (13700 cm in 6.5 s, no drive)
            seq = [v for v in van if secs_of(v[0]) >= t3 - 4 and (t7 is None or secs_of(v[0]) <= t7)]
            st, en = POCKETS['DM07_1109' if k in ('DM07SINK_1109', 'DM07CURTAIN_1109') + PLANE_KITS else k]
            jumps = [(x, y) for x, y in zip(seq, seq[1:]) if secs_of(y[0]) - secs_of(x[0]) <= 6.5 and math.dist(x[3], y[3]) > 5000]
            reset = [(x, y) for x, y in jumps if math.hypot(x[3][0] - en[0], x[3][2] - en[1]) < 2500 and math.hypot(y[3][0] - st[0], y[3][2] - st[1]) < 1000]
            for x, y in reset:
                info.append('reset at the unseen END pocket %s -> START pocket %s at %s (the drive-out end, not a pop)' % (tuple(round(c) for c in x[3]), tuple(round(c) for c in y[3]), y[0]))
            pops = ['%s %s -> %s' % (y[0], tuple(round(c) for c in x[3]), tuple(round(c) for c in y[3])) for x, y in jumps if (x, y) not in reset]
            chk('van never jumps (> 50 m between samples <= 6.5 s apart) from state 3 to 7, except the END -> START pocket reset', not pops, '; '.join(pops[:3]) or '%d samples' % len(seq))
        info.append('no-pop: 1 s samples cannot show a one-frame jump; LOOK at the shots around state 5 and the arrival')
    if k == 'DM07_1109':
        pan = [r for r in ents(a, 'Chainlink_Fence_4m') if r[1].endswith('4m_01') or r[1].endswith('4m_11')]
        names = {r[1][-5:] for r in pan}
        chk('fence panels 4m_01 AND 4m_11 hidden (gate)', names >= {'4m_01', '4m_11'} and all(r[2] for r in pan), '%d rows: %s' % (len(pan), sorted({(r[1][-5:], r[2]) for r in pan})))
        c = ctrl or {}
        cg = goto_lines(a, *c['control']) if c.get('control') else []
        chk('control walk (same start, same length %s through open mesh) is reached' % c.get('length', '?'), reached(cg),
            (cg[-1][cg[-1].find('goto'):][:110] if cg else 'no control goto line (dm07.json has no control, or the walk never ran)'))
        g = goto_lines(a, -6000, 10400)
        tp = [l for l in a if 'tele' in l and ('REFUSED' in l or 'MISSED' in l or 'FAULTED' in l) and '-3900' in l]
        xp = pos_of(a, 'dm07-after-walk')
        xs = xp[0] if xp else None
        chk('walk-out goto ran', bool(g), g[0][g[0].find('goto'):][:110] if g else 'no goto line%s' % (' (tele refused: %s)' % tp[0][:100] if tp else ''))
        chk('player does NOT walk out through the gap (blocked, control walks)', bool(g) and 'NOT reached' in g[0] and xs is not None and xs > -4700 and reached(cg),
            'goto: %s | pos dm07-after-walk x=%s | control reached=%s' % (g[0][g[0].find('goto'):][:90] if g else 'none', xs, reached(cg)))
    if k == 'DM07CURTAIN_1109':
        s7c = next((l for l in a if 'BENCH1109' in l and 'van at state 7' in l), None)
        chk('van reaches state 7 (leaves): the curtain did not kill the driver (GUESS: a KillBox ignores a vehicle)', s7c is not None,
            s7c[:12] if s7c else 'waitvan 7 timed out: if the walks above read KILLED, suspect the driver died in the curtain box')
        deaths = [l for l in a if 'skulls state: row 0' in l and 'kind 3' in l]
        lives = [l for l in a if 'skulls state: row 0' in l and 'kind 1' in l]
        verdict = {}
        for lbl, st, exp in CURTAIN_WALKS:
            v, note = curtain_walk(a, lbl, deaths, lives)
            verdict[lbl] = v
            info.append('%s (z %d, expect %s): %s - %s' % (lbl, st[2], exp, v, note))
            if v == 'NOSAMPLE':
                chk('%s: crossing sampled (tele, settle, %d steps)' % (lbl, len(GATE_XS)), False, note)
            elif exp == 'BLOCKED':
                chk('%s: control reads BLOCKED (the method discriminates)' % lbl, v == 'BLOCKED', '%s - %s' % (v, note), warn=v in CURTAIN_VOID)
            else:
                chk('%s: the gate crossing ends KILLED or BLOCKED, never alive west of x %d' % (lbl, CURTAIN_THROUGH), v in ('KILLED', 'BLOCKED'), '%s - %s' % (v, note), warn=v in CURTAIN_VOID)
        kw = [l_ for l_, _, e_ in CURTAIN_WALKS if e_ == 'KILL']
        good = [l_ for l_ in kw if verdict.get(l_) in ('KILLED', 'BLOCKED')]
        chk('at least 2 of the %d gate crossings gave a valid verdict (not VOID)' % len(kw), len(good) >= 2, ', '.join('%s %s' % (l_, verdict.get(l_, '?')) for l_ in kw))
        info.append('curtain verdict: %s. KILLED = the KillBox kills a player in the gate; BLOCKED = something else stopped him (the curtain is then unproven); THROUGH / INSIDE = open'
                    % ', '.join('%s %s' % (l_, verdict.get(l_, '?')) for l_, _, _ in CURTAIN_WALKS))
        info.append('KeepAlive is OFF for this kit (K keepalive=0): a police kill east of the fence reads DIED-EAST (WARN, rerun)')
    if k in PLANE_KITS:
        s7p = next((l for l in a if 'BENCH1109' in l and 'van at state 7' in l), None)
        chk('van reaches state 7 (leaves): the planes did not block the reverse-out through the gap (GUESS: a hero-only plane ignores a vehicle)', s7p is not None,
            s7p[:12] if s7p else 'waitvan 7 timed out: suspect the planes block the van (try the other sub variant)')
        pan = [r for r in ents(a, 'Chainlink_Fence_4m') if r[1].endswith('4m_01') or r[1].endswith('4m_11')]
        chk('fence panels 4m_01 AND 4m_11 still hidden (the van drives through them)', {r[1][-5:] for r in pan} >= {'4m_01', '4m_11'} and all(r[2] for r in pan), '%d rows' % len(pan))
        deaths = [l for l in a if 'skulls state: row 0' in l and 'kind 3' in l]
        lives = [l for l in a if 'skulls state: row 0' in l and 'kind 1' in l]
        verdict = {}
        for lbl, st, kind in PLANE_WALKS:
            v, note = plane_walk(a, lbl, kind, deaths, lives)
            verdict[lbl] = v
            info.append('%s (z %d, %s): %s - %s' % (lbl, st[2], kind, v, note))
            if v == 'NOSAMPLE':
                chk('%s: crossing sampled (tele, settle, 5 steps)' % lbl, False, note)
            elif kind == 'CTRL':
                chk('%s: control (visible fence) reads BLOCKED (the method discriminates)' % lbl, v == 'BLOCKED', '%s - %s' % (v, note), warn=v in PLANE_VOID)
            elif kind == 'FREE':
                chk('%s: the free path east PASSES (the player can move)' % lbl, v == 'PASSED', '%s - %s' % (v, note), warn=v in PLANE_VOID)
            else:
                chk('%s: the gate plane stops the %s (never alive west of x %d)' % (lbl, 'crouched player' if kind == 'CROUCH' else 'player', PLANE_THROUGH), v == 'BLOCKED', '%s - %s' % (v, note), warn=v in PLANE_VOID)
        gw = [l_ for l_, _, kd_ in PLANE_WALKS if kd_ in ('GATE', 'CROUCH')]
        chk('at least %d of the %d gate crossings gave a BLOCKED verdict (not VOID / DIED)' % (PLANE_MIN_VALID, len(gw)), sum(1 for l_ in gw if verdict.get(l_) == 'BLOCKED') >= PLANE_MIN_VALID,
            ', '.join('%s %s' % (l_, verdict.get(l_, '?')) for l_ in gw))
        info.append('plane verdict: %s. BLOCKED = the planes hold at that z; THROUGH / KILLED = open there (list-code reach: only the old panel volumes z 9993..10393 / 10395..10795 are looked at); '
                    'VOID / DIED = no verdict, rerun' % ', '.join('%s %s' % (l_, verdict.get(l_, '?')) for l_, _, _ in PLANE_WALKS))
        info.append('crouch (plC*): stance NOT logged (pos = actor origin), key LCONTROL is a GUESS: LOOK at the shots; coverage below y 471 is by the list-code rule above, not provable here')
        info.append('variant: %s (sub flags %s)' % (k, '0x72 plain world' if k == 'DM07PLANE72_1109' else '0x108 donor hero-only, GUESS blocks players'))
    if k == 'DD10GATE_1109':
        pk = next((l for l in a if 'BENCH1109 dd10gate van parked' in l), None)
        info.append('van before the walks: %s' % (pk[:12] if pk else 'no parked line'))
        deaths = [l for l in a if 'skulls state: row 0' in l and 'kind 3' in l]
        vs = {}
        for lbl, st in DD10_GATE_WALKS:
            v, note = dd10gate_walk(a, lbl, deaths)
            vs[lbl] = v
            info.append('%s (z %d): %s - %s' % (lbl, st[2], v, note))
            if v == 'NOSAMPLE':
                chk('%s: walk sampled' % lbl, False, note)
            else:
                chk('%s: the hidden DD10 gate stops the player (never alive west of x %d)' % (lbl, DD10_THROUGH), v == 'BLOCKED', '%s - %s' % (v, note), warn=v in ('VOID', 'DIED'))
        chk('at least 2 of the %d gate walks gave a verdict' % len(DD10_GATE_WALKS), sum(1 for v in vs.values() if v in ('BLOCKED', 'THROUGH')) >= 2,
            ', '.join('%s %s' % kv for kv in vs.items()))
    if k in ('DM07GATE_1109', 'DM07UNHIDE_1109', 'DM07SINK_1109'):
        unhide = k in ('DM07UNHIDE_1109', 'DM07SINK_1109')      # no south walk, own verdict line
        sink = k == 'DM07SINK_1109'
        walks = GATE_WALKS_SINK if sink else GATE_WALKS_UNHIDE if unhide else GATE_WALKS
        pan = [r for r in ents(a, 'Chainlink_Fence_4m') if r[1].endswith('4m_01') or r[1].endswith('4m_11')]
        if sink:
            pass                                                 # panels keep the live flags (4m_01 + 4m_11 hidden): only the .HVK changed
        elif unhide:
            p1, p11 = [r for r in pan if r[1].endswith('4m_01')], [r for r in pan if r[1].endswith('4m_11')]
            chk('fence panel 4m_01 reads VISIBLE (un-hidden by the stage) and 4m_11 still hidden', bool(p1) and bool(p11) and not any(r[2] for r in p1) and all(r[2] for r in p11),
                '4m_01 %d rows hidden=%s, 4m_11 %d rows hidden=%s' % (len(p1), sorted({r[2] for r in p1}), len(p11), sorted({r[2] for r in p11})))
        else:
            chk('fence panels 4m_01 AND 4m_11 read hidden (the live gate)', {r[1][-5:] for r in pan} >= {'4m_01', '4m_11'} and all(r[2] for r in pan), '%d rows' % len(pan))
        verdict = {}
        # the host's own seat: 'hud: ONLINE skulls state: row 0 ... kind 3 deaths N' (kind 3 = just died, run 1 at 06:03:06 with FA_DieFromPolice)
        deaths = [l for l in a if 'skulls state: row 0' in l and 'kind 3' in l]
        # kind 1 on row 0 = alive again (run 2: died 06:13:10, back at 06:16:41 = next round)
        lives = [l for l in a if 'skulls state: row 0' in l and 'kind 1' in l]
        for lbl, st in walks:
            ps = [pos_of(a, '%s-%d' % (lbl, i)) for i in range(len(GATE_XS) + 1)]
            got = [p for p in ps if p]
            chk('%s: crossing sampled (start + %d steps)' % (lbl, len(GATE_XS)), len(got) == len(ps) and abs(got[0][0] - st[0]) < 300,
                ' '.join('(%d,%d,%d)' % tuple(round(c) for c in p) if p else '-' for p in ps))
            if got:
                end = got[-1]
                verdict[lbl] = 'THROUGH' if end[0] < -4700 else 'BLOCKED' if end[0] > -4700 and abs(end[2] - st[2]) < 400 else 'OFF-LINE'
                # a host death inside the crossing voids a BLOCKED (DM07GATE_1109 run 1: police kill at 06:03:06, then B and H never left the tele point)
                t0 = next((secs_of(l) for l in a if 'pos %s-0:' % lbl in l), None)
                t1 = next((secs_of(l) for l in a if 'pos %s-%d:' % (lbl, len(GATE_XS)) in l), None)
                # dead at the crossing = a death before its end with no kind-1 row in between (run 2: the death 2 s before gateA-0 was missed by a t0-1 window)
                dead = [l[:12] for l in deaths if t0 is not None and t1 is not None and secs_of(l) <= t1
                        and not any(secs_of(l) < secs_of(v) <= t0 for v in lives)]
                if dead and verdict[lbl] != 'THROUGH':
                    verdict[lbl] = 'DEAD'
                    info.append('%s: the host died at %s, before or inside the crossing: no verdict' % (lbl, dead[-1]))
                elif verdict[lbl] == 'BLOCKED' and max(abs(p[0] - got[0][0]) for p in got) < 30:
                    # a real block walks up to the panel (run 1: A to x -4549); never leaving the tele point = frozen, not the fence
                    verdict[lbl] = 'FROZEN'
                    info.append('%s: never left x %d: frozen, not blocked' % (lbl, got[0][0]))
                low = min((p[1] for p in got if -4700 < p[0] < -4450), default=None)
                info.append('%s: %s, end x %d (z %d), lowest y near the fence line %s' % (lbl, verdict[lbl], end[0], end[2], low))
        if sink:
            info.append('sink verdict: %s. All BLOCKED (walked up to the slab, not frozen) = the pocket is sealed at the measured leak; any THROUGH = still open there'
                        % ', '.join('%s %s' % (l_, verdict.get(l_, '?')) for l_, _ in walks))
            for l_, _ in walks:
                chk('%s: the sunk fence blocks the crossing' % l_, verdict.get(l_) in ('BLOCKED', 'DEAD', 'FROZEN'), verdict.get(l_, 'no samples'))
        elif unhide:
            info.append('unhide verdict: H (4m_01 UN-hidden) %s, A (visible 4m_02) %s. H BLOCKED = the hide flag removes player collision at runtime (the static reading was '
                        'wrong; un-hide or re-route fixes it); H THROUGH = the gap under the panel is the leak (needs a blocker). A must read BLOCKED for either to count '
                        '(A THROUGH = this crossing method does not discriminate); DEAD / FROZEN = no verdict, rerun'
                        % (verdict.get('gateH', '?'), verdict.get('gateA', '?')))
            chk('control A (visible 4m_02) reads BLOCKED (else the crossing does not discriminate)', verdict.get('gateA') == 'BLOCKED', 'A %s, H %s' % (verdict.get('gateA', '?'), verdict.get('gateH', '?')), warn=True)
        else:
            info.append('gate verdict: A (visible 4m_02) %s, B (visible 4m_03) %s, H (hidden 4m_01) %s. A/B BLOCKED + H THROUGH = the hidden panels pass players '
                        '(un-hide fixes it, or the gap); all THROUGH = the fence never blocks players (filter or gap): re-route the van or add a blocker'
                        % (verdict.get('gateA', '?'), verdict.get('gateB', '?'), verdict.get('gateH', '?')))
        chk('no crossing voided by a host death or a freeze', not [v for v in verdict.values() if v in ('DEAD', 'FROZEN')], ', '.join('%s %s' % kv for kv in sorted(verdict.items())), warn=True)
        for n in (() if unhide else ('gateS-1', 'gateS-2')):
            p = pos_of(a, n)
            info.append('%s (pocket south slope): %s' % (n, p and tuple(round(c) for c in p)))
    if k in ('DM03_1109', 'DM02_1109') or k.startswith('DOORS_1109'):
        use = list(dd)[:1] if k == 'DM03_1109' else list(dd)
        chk('doors.json lists the kit doors', bool(use), '%d doors' % len(use))
        tp = [l for l in a if 'tele' in l and ('REFUSED' in l or 'MISSED' in l or 'FAULTED' in l)]
        for i, d in enumerate(use):
            h = d['hinge']
            lbl = door_lbl(k, i)
            kick = next((j for j, l in enumerate(a) if 'BENCH1109 %s door %s: kicked' % (lbl, d['host']) in l), None)
            leaf = [r for r in ents(a, 'Door') if math.hypot(r[3][0] - h[0], r[3][2] - h[2]) < 150 and abs(r[3][1] - h[1]) < 200]
            bef = [r for r in leaf if kick is not None and r[5] < kick]
            aft = [r for r in leaf if kick is not None and r[5] > kick]
            chk('door %s: kick happened (log line)' % d['host'], kick is not None, 'no "%s door %s: kicked" line' % (lbl, d['host']) if kick is None else 'line %d' % kick)
            # the engine's answer: a registry controller kickable (1) at the stand and kicked (3) after an attempt (run 2: slot 7 went 1 -> 3 for door 957)
            st = {w: kick_states(a, lbl, w) for w in ('stand', 'kicked', 'kicked2')}
            went = sorted(i_ for i_, v in st['stand'].items() if v == 1 and 3 in (st['kicked'].get(i_), st['kicked2'].get(i_)))
            # a host death between the stand probe and the last attempt's probe voids the verdict (runs 2/3 lost door 2 to police that way)
            pl = [l[:12] for l in a if re.search(r'  %s-(stand|kicked2)-ctrl\d+-state' % re.escape(lbl), l)]
            dead = [l[:12] for l in a if pl and 'skulls state: row 0' in l and 'kind 3' in l and pl[0] <= l[:12] <= pl[-1]]
            chk('door %s: a kick controller went 1 -> 3 (kicked in the engine)' % d['host'], bool(went),
                'ctrl %s (%s)' % (went, 'first try' if any(st['kicked'].get(i_) == 3 for i_ in went) else 'second try') if went else
                'states stand %s / kicked %s / kicked2 %s%s' % (st['stand'], st['kicked'], st['kicked2'], '; the host died at %s before it: no verdict' % dead[-1] if dead else ''),
                warn=bool(dead))
            chk('door %s: leaf entity sampled near its hinge before AND after the kick' % d['host'], bool(bef) and bool(aft), '%d rows before, %d after' % (len(bef), len(aft)))

            def sig(rows):
                return {(r[1], r[2], tuple(round(v) for v in r[3])) for r in rows}
            changed = bool(bef and aft) and sig(bef) != sig(aft)
            chk('door %s: leaf state changed by the kick (position or hidden flag)' % d['host'], changed,
                ' | '.join('%s %s hidden=%s' % (r[0][:8], r[1][-18:], r[2]) for r in (bef[:2] + aft[:2])) or 'no leaf rows',
                warn=(k != 'DM03_1109'))                    # DM03 host 176 must move (owner's rule); the others: the leaf origin may stay on the hinge while it swings (not logged)
            b = d['back'] if d['front'] and d['back'] else None
            if b:
                g = goto_lines(a, b[0], b[2])
                chk('door %s: player walks through after the kick' % d['host'], reached(g), g[-1][g[-1].find('goto'):][:120] if g else 'no goto line (tele refused?)')
            else:
                info.append('door %s is one-sided on the mesh: no walk-through check, kick + shot only' % d['host'])
        if tp:
            info.append('tele problem: %s' % tp[0][:160])
        info.append('kick sound / swing: not logged; LOOK at the shots and listen. Kick key E is a GUESS (boarding uses E)')
    if k == 'DM03_1109':
        cars = ('car', 'van', 'truck', 'heli')
        mv = []
        for pat in ('ArrivingCops', 'VehicleExit'):
            for (slot, name), r in by_entity(ents(a, pat)).items():
                if any(c in name.lower().replace('vehicleexit', '') for c in cars):
                    continue
                if len(r) >= 2 and max(math.dist(r[0][3], x[3]) for x in r[1:]) >= 300:
                    mv.append('%s moved %.0f' % (name[-30:], max(math.dist(r[0][3], x[3]) for x in r[1:])))
        # WARN only: 'ents' lists named scene nodes, and the ArrivingCops / VehicleExit rows are squad groups and trigger boxes that never move; the cop
        # actors are not listed and their guns read (0,0,0). Proving 'out of the car' needs a hook-side enemy actor position dump (not in the TEST dll).
        chk('a VehicleExit / ArrivingCops (non-car) entity left its first position (>= 300; GUESS: leaving the car moves it)', bool(mv),
            '; '.join(mv[:3]) or 'none moved (or no rows): groups/triggers only, cop actors not listed', warn=True)
        hits = sum(int(m.group(1)) for l in a for m in [re.search(r'cop->bot factor 5 s: (\d+) cop hits on bots', l)] if m)
        chk('cops engage (cop hits on the Ally bots logged)', hits > 0, '%d cop hits on bots in all' % hits)
        pol = by_entity(ents(a, 'Police'))
        chk('police rows present', bool(pol), '%d police entities, e.g. %s' % (len(pol), sorted(n for _, n in pol)[:3]))
        for pat in ('ArrivingCops', 'Garage', 'Ramp', 'VehicleExit'):
            r = ents(a, pat)
            info.append('%-13s rows %d, names %s' % (pat, len(r), sorted({x[1][-26:] for x in r})[:6]))
        cen = sorted({int(m.group(1)) for l in a for m in [re.search(r'botfill: round census: (\d+) ZFFActor', l)] if m})
        chk('census logged (44/29 expected after the cops pass; 33/27 before)', bool(cen), 'census lines %s' % (cen or 'none'), warn=True)
        info.append('police vs SWAT at the front / garage + ramp arrival: names above; LOOK at the shots')
    return res, info


def verify(k, part='online'):
    rc = B.verify(k, 'online')
    L = B.logs('%s_online' % k)
    if 1 not in L:
        return 1
    a = L[1]

    def rd(n):
        p = '%s/%s' % (kd(k), n)
        return json.load(open(p)) if os.path.isfile(p) else None
    res, info = item_checks(k, a, rd('doors.json') or [], rd('dm07.json'))
    print('item checks %s (host log, %d lines)' % (k, len(a)))
    for st, name, det in res:
        print('  %s %s %s' % (st, name, det))
    for i in info:
        print('  info', i)
    bad = sum(1 for r in res if r[0] == 'FAIL')
    print('RESULT: %s items %s (%d checks, %d FAIL)' % (k, 'PASS' if not bad else 'FAIL', len(res), bad))
    return 1 if (bad or rc) else 0


def run(k):
    if validate(k):
        print('RESULT: not started - validate failed'); return 1
    z = B.kl2_procs()
    if any(kb >= 1024 for _, kb in z):
        print('RESULT: not started - a live kl2.exe is running: %s' % z); return 1
    c, d = K[k], kd(k)
    md = B.mapdir(k)
    before = B.snap(md)
    tag = '%s_online' % k
    import shutil
    # stage kit (K entry with stage=): install.py before, --undo in the finally below (as kl_bench_1106.run); a zombie kl2.exe (working set < 1 MB, z non-empty
    # here) gets --skip-run-check when that install.py knows the flag
    inst = [sys.executable, '%s/install.py' % c['stage']] if c.get('stage') else None
    if inst and z and '--skip-run-check' in open('%s/install.py' % c['stage'], encoding='utf-8', errors='replace').read():
        print('  ignoring zombie kl2.exe (working set < 1 MB): %s' % z, flush=True)
        inst.append('--skip-run-check')
    if inst:
        print('INSTALLING the stage into the LIVE game folder (undone at the end): %s' % md, flush=True)
        if B.sh(inst):
            print('RESULT: not started - install.py refused (nothing changed)'); return 1
    rc = 1
    try:
        for i in (1, 2):
            os.makedirs('%s/%s/inst%d' % (B.SOLO, tag, i), exist_ok=True)
            shutil.copy2('%s/KLShopPage.ini' % d, '%s/%s/inst%d/KLShopPage.ini' % (B.SOLO, tag, i))
        cmd = [sys.executable, 'tools/kl_solo_test.py', '--hook', '%s/hook_test' % d, '--tag', tag, '--base', '%s/KLHook_base.ini' % d, '--owner-away',
               '--n', '2', '--secs', '1900', '--gap', '45', '--relaunch', '2', '--ini1', '%s/online_host.ini' % d, '--ini2', '%s/online_join.ini' % d,
               '--shots', c['shots'], '--d3shots']
        with open('%s/online_run.txt' % d, 'w') as out:
            print('  run %s (log %s/online_run.txt)' % (tag, d), flush=True)
            rcb = subprocess.run(cmd, cwd=B.ROOT, stdout=out, stderr=subprocess.STDOUT).returncode
        print('  bench exit %d' % rcb, flush=True)
        rc = verify(k)
    finally:
        r = 0
        if inst:
            print('UNDOING the stage (install.py --undo)', flush=True)
            r = B.sh(inst + ['--undo'])
    after = B.snap(md)
    same = {n: m for n, m in after.items() if not (c.get('tag') and n.endswith(c['tag']))} == before
    if inst and (r or not same):
        print('UNDO FAILED - run by hand: python "%s/install.py" --undo ; then compare with the md5s above' % c['stage'])
    print('map folder unchanged: %s' % same)
    print('RESULT: %s run done, %s' % (k, 'ALL PASS' if not (rc or not same) else 'see FAIL lines'))
    return 1 if (rc or not same) else 0


def order():
    t = ['bench_1109 RUN ORDER (written by tools/kl_bench_1109.py order). ONE bench at a time; each needs the game free.',
         'Before EACH: tasklist | findstr /i kl2.exe  must show nothing (a zombie with 0 threads is fine). Peers (f0/81 merged kits, fc shop, d0) bench too:',
         'wait for their "done, game free". Nothing is installed by any of these except the stage kit; every kit pins the live md5s and compares the map folder after.',
         'Stage kit DM07UNHIDE_1109: its run INSTALLS C:/kl_build_1024/dm07unhide_1109 into the live DM07 folder (install.py) and undoes it in a finally block.',
         'Pre-flight for all (read only, no game launch):   cd C:\\kl-merge\\kl-merge ; python tools/kl_bench_1109.py validate all',
         'Disk: each run writes a few hundred MB of shots/logs under the solo work folder; keep C: above 2 GB free.',
         '']
    for i, k in enumerate(ORDER, 1):
        t.append('%d. python tools/kl_bench_1109.py run %s        # %s, slot %s%s' % (i, k, K[k]['map'], K[k]['slot'], ' (FIRST)' if i == 1 else ''))
        t.append('   re-read only:   python tools/kl_bench_1109.py verify %s' % k)
    t += ['', 'Each prints "RESULT: <kit> run done, ALL PASS" or "see FAIL lines"; the run folder is %s/<kit>_online (inst1 = host, inst2 = join; KLHook.log, KLShot_inst1_NN.jpg).' % B.SOLO]
    B.write('%s/RUN_ORDER.txt' % KIT, '\n'.join(t) + '\n')
    print('wrote %s/RUN_ORDER.txt' % KIT)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 2
    cmd, arg = a[0], (a[1] if len(a) > 1 else 'all')
    if cmd == 'gen':
        gen(arg); order(); return 0
    if cmd == 'validate':
        return validate(arg)
    if cmd == 'order':
        order(); return 0
    if cmd == 'run' and arg in K:
        return run(arg)
    if cmd == 'verify' and arg in K:
        return verify(arg)
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
