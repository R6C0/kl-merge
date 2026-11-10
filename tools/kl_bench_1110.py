#!/usr/bin/env python3
"""
Bench kits for the 11-10 stages, on the tools/kl_bench_1109.py harness (imported; its K / ORDER / KIT / merged-kit pins are replaced in this process only).
Today: DM03BS_1110 = stage kit C:/kl_build_1024/dm03backswat_1110 (tools/kl_dm03cops_1108.py --parts backswat on the live dm03doorfix_1109 map):
`run` installs the stage with its own install.py (originals -> *.before-dm03backswat1109), benches 2 seats (round 1 -> shop -> round 2), and ALWAYS
runs install.py --undo, then compares every map-folder md5 with the pre-run snapshot.

    python tools/kl_bench_1110.py gen [kit|all]       write C:/kl_build_1024/bench_1110/<kit> (no game contact; needs a SHIP dll live, not a bench's TEST)
    python tools/kl_bench_1110.py validate [kit|all]  DRY RUN, never launches the game
    python tools/kl_bench_1110.py run <kit>           ONE bench (the game must be free)
    python tools/kl_bench_1110.py verify <kit>        re-read the last run's logs

The merged kit (SHIP + its TEST twin) is the one whose SHIP is live at `gen` time (MERGED_KITS); kit.json records it and later
validate / verify / run use that record. The base ini = the live KLHook.ini at `gen` time (the 11-10 chain has more layers than one merged kit:
driverarena, menupick, campaign), so `gen` refuses while a bench's TEST dll is live.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_bench_1109 as M

B = M.B
KIT = 'C:/kl_build_1024/bench_1110'
# SHIP md5 -> (merged kit folder with dll_ship / dll_test / pins.json, TEST twin md5)
MERGED_KITS = {
    '6e3ca2add3c138b962815fe103a31e63': ('C:/kl_build_1024/merged_1110c/kit', 'fdaeaf10dad4775f218478a22478824e'),
    '38104558ca96a9a2a4cbec8b967b486a': ('C:/kl_build_1024/merged_1110d/kit', 'f4c8c3fdf1a8a0accc565d28b7dd3f02'),
    # 1110d + [Crash] ListUserGuard; TEST twin rebuilt from the listguard worktree + klauto [Auto] KeepAliveHp (was ddf81d7f, merged_1110f/kit)
    '6711bc5f5d9c6cbec06072f856ffe7f9': ('C:/kl_build_1024/merged_1110f_kahp/kit', '03840ed00268983d16d4233546807408'),
}

K = {
    # STAGE KIT: back SWAT. 6 KL_Garage!Back + 5 KL_Ramp!Wave men re-formed to SWAT (EscSquad Reinforcement_01 template, AK74 / Type81),
    # + KL_BackSwat!Van: 4 SWAT around the van stop (3306, 2, 4), Defend, started by KL_BackSwat!Clock\Go. Census 44/29 -> 48/30. Front stays police.
    # The host goes to the van stop after the census samples (tele + shots) so the screenshots show the back; GUESS: (3306, 152, 4) is open floor.
    'DM03BS_1110': dict(map='DM03', slot='F03', live={'F03_Main.zip': '8e23cbd3', 'F03_Main.bots.zip': '2528e8f0', 'KLJoin.ini': '5c02ca99'}, shots='60-900:20',
                        stage='C:/kl_build_1024/dm03backswat_1110', tag='.before-dm03backswat_1109',
                        files={'F03_Main.zip': 'a81ede87', 'F03_Main.bots.zip': 'e8c06e13', 'F03_Main.bots.base.md5': 'afc6ca40'}),
}
# VAULT kits (tools/kl_dm03vault_1110.py): live + files are filled from the final chain (back-SWAT a81ede87 -> d0 smartcops -> vault) by vault_pins()
# once the vault stage is re-staged on the live input; until then `gen` refuses them (no pins).
#   DM03VAULT_1110:  the host walks into KL_Vault!1\Arm -> 3 s Fuse -> Boom; doors sampled before/after, walk through the doorway, then
#                    sampled again past 240 s (the Backstop TriggerDelay2 cannot be cancelled: does it replay the opening and snap the leaves?)
#   DM03VAULTB_1110: nobody arms it; doors sampled at ~220 s and ~260 s from the round start: the Backstop alone opens them, quietly
VAULT_STAGE = 'C:/kl_build_1024/dm03vault_1110/stage_sc'  # on d0's smartcops DM03 (33361cd1), itself on back-SWAT a81ede87
for _k in ('DM03VAULT_1110', 'DM03VAULTB_1110'):
    K[_k] = dict(map='DM03', slot='F03', live={}, files={}, shots='60-900:20', stage=VAULT_STAGE, tag='.before-dm03vault_1110')  # = the stage install.py TAG
# DM03VAULTK_1110 (DIAGNOSTIC, never installed for play): stage_diag = the same vault built with --keep-kick (KickDoor controller + kick sound kept).
# Bench 11-10 DM03VAULTB_1110: the shut leaves did not stop a dock -> lobby walk. Three control lanes split the suspects: blocked at x -50/+50 but
# not at 0 = the seam between the two slabs; blocked everywhere here but not on stage_sc = the stripped controller; open everywhere = neither
VAULT_DIAG_STAGE = 'C:/kl_build_1024/dm03vault_1110/stage_diag'
K['DM03VAULTK_1110'] = dict(map='DM03', slot='F03', live={}, files={}, shots='60-300:20', stage=VAULT_DIAG_STAGE, tag='.before-dm03vault_1110')
VAULT_LANES = (-50, 0, 50)
ORDER = ['DM03BS_1110', 'DM03VAULT_1110', 'DM03VAULTB_1110', 'DM03VAULTK_1110']
VAN_STOP = (3306, 2, 4)
# from the vault stage's build report (GUESS-labelled there): Arm box centre (0, 340, -7006) half (150, 120, 150); doorway hinges x +-105 at z -6812;
# the moved piles at (0, 241, -6620), (120, 241, -6540), (200, 241, -6660)
VAULT_LOBBY = (0, 248, -7300)       # floor + 8 (d0, LCDOORS 11-10: a +60 tele and a tele right after GO preceded a frozen walker); lobby side, south of the Arm box (box z -7156..-6856); checked on stage_sc nav: lobby, Arm, dock all over floor y 240, one part (122 cells within 3 m)
VAULT_ARM = (0, -6980)
VAULT_DOCK = (0, -6600)             # just past the doorway, dock side
VAULT_WARM = (150, -7300)           # warm-up walk, 1.5 m east of the lobby tele (same floor part)
DOCK_Z = -6780                      # dock side of the doorway (hinges at z -6812)
# closed-door control (run 1 11-10: the proxies/pathblockers never change in ents, so a walk-through alone cannot tell "opened" from "never blocked"):
# from the dock side walk to just past the hinge plane, 10 cm radius so it stops short of the Arm box (z edge -6856) and never arms the fuse
VAULT_SHUT = (0, -6845)
HINGE_Z = -6812
# ents matches the node's OWN name (klauto.c kla_ents): the KL_Door_N group nodes never move; the blast / Backstop act on their children
# (kl_dm03vault_1110 DOOR_CHILD_FRONT / DOOR_CHILD_PB). Every DM03 kick door has children of these names, so rows are kept by position
VAULT_KIDS = ('KickableDoor_Proxy_Variation01Front', 'KickDoor_Pathblocker')
VAULT_DOORWAY = (-400, 400, -7100, -6500)   # x0, x1, z0, z1 around the doorway


def vault_pins():
    """Fill the two vault kits' live/files pins from the stage's install.py (its pinned input md5s -> output md5s) so `gen` and `run` check them.
    -> True when the stage exists and pins were read."""
    got = False
    for k in ('DM03VAULT_1110', 'DM03VAULTB_1110', 'DM03VAULTK_1110'):
        p = '%s/install.py' % K[k]['stage']
        if not os.path.isfile(p):
            continue
        t = open(p, encoding='utf-8', errors='replace').read()
        # install.py: FILES = [('F03_Main.zip', '<input md5>', '<output md5>'), ...]
        pairs = re.findall(r"\('([\w.]+)',\s*'([0-9a-f]{32})',\s*'([0-9a-f]{32})'\)", t)
        if pairs:
            K[k]['live'] = {n: a[:8] for n, a, _ in pairs}
            K[k]['files'] = {n: b[:8] for n, _, b in pairs}
            got = True
    return got


def vault_doors(tag):
    return ['ents KL_Vault 10', 'ents KL_Door_4 10', 'ents KL_Door_5 10'] + ['ents %s 40' % c for c in VAULT_KIDS] + ['log BENCH1110 vault %s' % tag]


def vault_seg(who, arm):
    s = ['wait 3000'] + vault_doors('t0')
    if who != 'host':
        for i in range(1, 9):
            s += ['wait 30000'] + vault_doors('client sample %d' % i)
        return s
    # 15 s after GO before the first tele, then a warm-up walk: a frozen local player shows as 'not simulated', not as a door FAIL
    s += ['waitstate 0x19 90000', 'wait 15000', 'tele %d %d %d' % (VAULT_DOCK[0], VAULT_LOBBY[1], VAULT_DOCK[1]), 'wait 2500', 'pos vault-shut0',
          'goto %d %d 10 5000' % VAULT_SHUT, 'pos vault-shut', 'log BENCH1110 vault closed-door control']
    s += ['tele %d %d %d' % VAULT_LOBBY, 'wait 2500', 'pos vault-lobby',
          'goto %d %d 40 6000' % VAULT_WARM, 'pos vault-warm', 'log BENCH1110 vault warm-up walk'] + vault_doors('before')
    if arm:
        s += ['goto %d %d 40 6000' % VAULT_ARM, 'pos vault-arm', 'log BENCH1110 vault host in the Arm box',
              'wait 1500', 'ents KL_Vault 10', 'log BENCH1110 vault fuse running', 'wait 4000'] + vault_doors('after')
        s += ['goto %d %d 40 8000' % VAULT_DOCK, 'pos vault-dock', 'log BENCH1110 vault walked through the doorway',
              'goto %d %d 40 6000' % (VAULT_LOBBY[0], VAULT_LOBBY[2])]
        # the Backstop fires 240 s after the AIMonitor start; ~45 s of the above + 175 s -> samples ~220..300 s after GO (0x19)
        s += ['wait 175000']
    else:
        s += ['wait 170000']   # ~25 s + 170 s -> samples ~195..275 s after GO: straddle 240 s
    for i in range(1, 10):
        s += vault_doors('late sample %d' % i)[:-1] + ['pos vault-late%d' % i, 'log BENCH1110 vault late sample %d' % i, 'wait 10000']
    s += ['goto %d %d 40 8000' % VAULT_DOCK, 'pos vault-dock-late', 'log BENCH1110 vault late walk through']
    return s


def lanes_seg(who):
    """DM03VAULTK_1110: the closed-door control walk in three lanes, nothing armed (the Backstop is 240 s away)."""
    s = ['wait 3000'] + vault_doors('t0')
    if who != 'host':
        return s + ['wait 60000'] + vault_doors('client sample')
    s += ['waitstate 0x19 90000', 'wait 15000', 'tele %d %d %d' % (VAULT_WARM[0], VAULT_LOBBY[1], VAULT_DOCK[1]), 'wait 2500', 'pos vault-lobby',
          'goto %d %d 40 6000' % (VAULT_WARM[0] - 150, VAULT_DOCK[1]), 'pos vault-warm', 'log BENCH1110 vault warm-up walk (dock side)']
    for x in VAULT_LANES:
        s += ['tele %d %d %d' % (x, VAULT_LOBBY[1], VAULT_DOCK[1]), 'wait 2500', 'pos vault-lane%d-0' % x,
              'goto %d %d 10 5000' % (x, VAULT_SHUT[1]), 'pos vault-lane%d' % x, 'log BENCH1110 vault control lane x %d' % x]
    return s + vault_doors('after lanes')


def md5_file(p):
    return M.md5_of(open(p, 'rb').read()) if os.path.isfile(p) else '-'


def pin(ship):
    """Point the harness at the merged kit whose SHIP is `ship`."""
    d, test = MERGED_KITS[ship]
    M.MERGED = M.INI_KIT = d
    M.SHIP_MD5, M.TEST_MD5 = ship, test
    M.HOOK = (d + '/dll_test/dinput8.dll', test)
    for c in K.values():
        c['hook'] = M.HOOK


def recorded(k):
    p = '%s/%s/kit.json' % (KIT, k)
    return json.load(open(p)) if os.path.isfile(p) else {}


def base_ini():
    live_dll = md5_file('%s/dinput8.dll' % M.DD)
    if live_dll not in MERGED_KITS:
        raise SystemExit('gen: live dinput8.dll %s is not a known SHIP (%s): a bench is running or a newer SHIP is live; add it to MERGED_KITS / gen when free'
                         % (live_dll[:8], ', '.join(s[:8] for s in MERGED_KITS)))
    live = open('%s/KLHook.ini' % M.DD, 'rb').read()
    M.INI_MD5 = M.md5_of(live)
    return live, 'live KLHook.ini under SHIP %s' % live_dll[:8]


def back_seg(who, doors):
    s = ['wait 3000', 'ents KL_BackSwat 30', 'ents M_Back 30', 'ents M_Wave 30', 'log BENCH1109 dm03bs t0 back census'] + M.dm03_seg(who, doors)
    for i in range(1, 4):
        s += ['wait 10000', 'ents KL_BackSwat 30', 'ents M_Back 30', 'ents M_Wave 30', 'log BENCH1109 dm03bs back sample %d' % i]
    if who == 'host':
        s += ['waitstate 0x19 90000', 'tele %d %d %d' % (VAN_STOP[0], VAN_STOP[1] + 150, VAN_STOP[2]), 'wait 3000', 'pos dm03bs-van',
              'log BENCH1109 dm03bs host at the van stop', 'wait 20000', 'pos dm03bs-van2', 'ents KL_BackSwat 30', 'log BENCH1109 dm03bs van look done']
    return s


_segment, _item_checks = M.segment, M.item_checks


def segment(k, who):
    if k in ('DM03VAULT_1110', 'DM03VAULTB_1110'):
        return vault_seg(who, k == 'DM03VAULT_1110')
    if k == 'DM03VAULTK_1110':
        return lanes_seg(who)
    if k == 'DM03BS_1110':
        p = '%s/doors.json' % M.kd(k)
        return back_seg(who, json.load(open(p)) if os.path.isfile(p) else [])
    return _segment(k, who)


def vault_kid_states(a):
    """{(slot, name): [(log index, hidden, (x, y, z))]} for the vault doorway's door children (the leaf proxies + pathblockers)."""
    x0, x1, z0, z1 = VAULT_DOORWAY
    g = {}
    for c in VAULT_KIDS:
        for r in M.ents(a, c):
            if x0 <= r[3][0] <= x1 and z0 <= r[3][2] <= z1:
                g.setdefault((r[4], r[1]), []).append((r[5], r[2], r[3]))
    return g


def vault_changed(rows, i0, i1):
    """Did any row with log index in [i0, i1) differ (hidden bit, or > 5 cm) from the last row before i0?"""
    pre = [r for r in rows if r[0] < i0]
    if not pre:
        return False
    h, p = pre[-1][1], pre[-1][2]
    return any(r[1] != h or max(abs(u - v) for u, v in zip(r[2], p)) > 5 for r in rows if i0 <= r[0] < i1)


def vault_checks(k, a):
    res, info = [], []
    arm = k == 'DM03VAULT_1110'

    def chk(name, cond, detail='', warn=False):
        res.append(('PASS' if cond else ('WARN' if warn else 'FAIL'), name, detail))

    def at(label):
        return next((i for i, l in enumerate(a) if 'BENCH1110 vault %s' % label in l), None)

    def states(ch):
        return ', '.join('%s#%d %s' % (n, s, 'changed' if v else 'same') for (s, n), v in sorted(ch.items())) or 'no rows'
    chk('item segment ran on the host (level loaded ... segment done)', any('BENCH1109 %s host level loaded' % k in l for l in a)
        and any('BENCH1109 %s host segment done' % k in l for l in a), '%d host log lines' % len(a))
    g = M.by_entity(M.ents(a, 'KL_Vault'))
    chk('KL_Vault rows present (the vault stage is the one loaded)', len(g) >= 1, '%d entities, e.g. %s' % (len(g), sorted(x for _, x in g)[:5]))
    for d in ('KL_Door_4', 'KL_Door_5'):
        chk('%s rows present (vault door group)' % d, len(M.by_entity(M.ents(a, d))) >= 1)
    kids = vault_kid_states(a)
    chk('vault doorway children sampled (2 leaf proxies + 2 pathblockers in the doorway box)', len(kids) >= 4,
        '%d: %s' % (len(kids), sorted('%s#%d' % (n, s) for s, n in kids)))
    lb, wm = M.pos_of(a, 'vault-lobby'), M.pos_of(a, 'vault-warm')
    chk('local player simulated: the warm-up walk moved the host >= 50 cm (else the bench is INVALID, not a door result)',
        bool(lb and wm) and abs(wm[0] - lb[0]) + abs(wm[2] - lb[2]) >= 50, 'lobby %s -> warm %s' % (lb, wm))
    chk('host reached the lobby (tele to %s)' % (VAULT_LOBBY,), bool(lb) and abs(lb[0] - VAULT_LOBBY[0]) <= 300 and abs(lb[2] - VAULT_LOBBY[2]) <= 300, 'pos %s' % (lb,))
    s0, sh = M.pos_of(a, 'vault-shut0'), M.pos_of(a, 'vault-shut')
    chk('control: tele to the dock side landed (z > %d)' % DOCK_Z, bool(s0) and s0[2] > DOCK_Z, 'pos %s' % (s0,))
    # without this a walk-through after the blast proves nothing: doors that never block would pass it too
    chk('control: the CLOSED doors stopped a dock -> lobby walk before the blast (host stayed z >= %d)' % HINGE_Z,
        bool(s0 and sh) and s0[2] > DOCK_Z and sh[2] >= HINGE_Z, 'dock %s -> after the walk %s' % (s0, sh))
    i_before, i_after = at('before'), at('after')
    if arm:
        p = M.pos_of(a, 'vault-arm')
        chk('host stood in the Arm box (|x| <= 150, z -7156..-6856)', bool(p) and abs(p[0]) <= 150 and -7156 <= p[2] <= -6856, 'pos %s' % (p,))
        ok = i_before is not None and i_after is not None
        ch = {e: vault_changed(r, i_before + 1, i_after + 1) for e, r in kids.items()} if ok else {}
        # GUESS: the MatPosAnimProxy swing moves the proxy node and/or the pathblocker gets hidden; if neither shows, the shots + the walk decide
        chk('a vault door child changed between "before" and "after" (the blast opened the doors)', any(ch.values()), states(ch), warn=True)
        d = M.pos_of(a, 'vault-dock')
        chk('walked through the doorway after the blast (z > %d)' % DOCK_Z, bool(d) and d[2] > DOCK_Z, 'pos %s' % (d,))
        rp = {e: vault_changed(r, i_after + 1, len(a)) for e, r in kids.items()} if i_after is not None else {}
        chk('no door child changed again after the blast (no Backstop replay)', not any(rp.values()), states(rp), warn=True)
        info.append('blast: LOOK/listen at the shots right after "vault host in the Arm box" (+3 s): fire, shake, rocket sound 407600')
    elif i_before is not None:
        ch = {e: vault_changed(r, i_before + 1, len(a)) for e, r in kids.items()}
        chk('a vault door child changed during the late samples (the Backstop opened the doors)', any(ch.values()), states(ch), warn=True)
    # same rule as kl_bench_1110m (d0, LCDOORS/DM02C 11-10): police can down the host despite KeepAlive=1; every walk after a death is void
    i0 = next((i for i, l in enumerate(a) if 'BENCH1109 %s host level loaded' % k in l), 0)
    i1 = next((i for i, l in enumerate(a) if 'BENCH1109 %s host segment done' % k in l), len(a))
    died = [l for l in a[i0:i1] if 'FA_DieFrom' in l or re.search(r'skulls state: row 0 .* deaths [1-9]', l)]
    chk('host stayed alive through the segment (else later walks are void)', not died,
        ('died %s: %s' % (died[0][:12], died[0][13:120])) if died else 'no FA_DieFrom / skulls death on row 0')
    late = M.pos_of(a, 'vault-dock-late')
    chk('late walk through the doorway (after the Backstop time) reached the dock side (z > %d)' % DOCK_Z, bool(late) and late[2] > DOCK_Z, 'pos %s' % (late,))
    return res, info


def lanes_checks(k, a):
    res, info = [], []

    def chk(name, cond, detail='', warn=False):
        res.append(('PASS' if cond else ('WARN' if warn else 'FAIL'), name, detail))
    chk('item segment ran on the host (level loaded ... segment done)', any('BENCH1109 %s host level loaded' % k in l for l in a)
        and any('BENCH1109 %s host segment done' % k in l for l in a), '%d host log lines' % len(a))
    chk('KL_Vault rows present (the diag stage is the one loaded)', len(M.by_entity(M.ents(a, 'KL_Vault'))) >= 1)
    lb, wm = M.pos_of(a, 'vault-lobby'), M.pos_of(a, 'vault-warm')
    chk('local player simulated: the warm-up walk moved the host >= 50 cm (else the bench is INVALID)',
        bool(lb and wm) and abs(wm[0] - lb[0]) + abs(wm[2] - lb[2]) >= 50, '%s -> %s' % (lb, wm))
    blocked = []
    for x in VAULT_LANES:
        p0, p1 = M.pos_of(a, 'vault-lane%d-0' % x), M.pos_of(a, 'vault-lane%d' % x)
        chk('lane x %d: tele landed on the dock side (z > %d)' % (x, DOCK_Z), bool(p0) and p0[2] > DOCK_Z, 'pos %s' % (p0,))
        b = bool(p0 and p1) and p0[2] > DOCK_Z and p1[2] >= HINGE_Z
        blocked.append(b)
        # a lane result, not a pass/fail: WARN marks "walked through"
        chk('lane x %d: the shut doors stopped the walk (stayed z >= %d)' % (x, HINGE_Z), b, '%s -> %s' % (p0, p1), warn=True)
    v = dict(zip(VAULT_LANES, blocked))
    verdict = ('all lanes blocked: the controller (stripped on stage_sc) is what holds the shut slab' if all(blocked) else
               'only the seam lane x 0 walked through: the slabs leave a gap at x 0' if not v[0] and v[-50] and v[50] else
               'no lane blocked: neither the controller nor the seam; the slab body itself does not stop the capsule' if not any(blocked) else
               'mixed: %s' % v)
    info.append('VERDICT: ' + verdict)
    return res, info


def item_checks(k, a, dd=(), ctrl=None):
    if k in ('DM03VAULT_1110', 'DM03VAULTB_1110'):
        return vault_checks(k, a)
    if k == 'DM03VAULTK_1110':
        return lanes_checks(k, a)
    if k != 'DM03BS_1110':
        return _item_checks(k, a, dd, ctrl)
    res, info = _item_checks('DM03_1109', a, dd, ctrl)
    # the DM03_1109 'segment ran' row looks for its own kit name: replace it with this kit's
    res = [r for r in res if not r[1].startswith('item segment ran')]

    def chk(name, cond, detail='', warn=False):
        res.append(('PASS' if cond else ('WARN' if warn else 'FAIL'), name, detail))
    chk('item segment ran on the host (level loaded ... segment done)', any('BENCH1109 %s host level loaded' % k in l for l in a)
        and any('BENCH1109 %s host segment done' % k in l for l in a), '%d host log lines' % len(a))
    for pat, n in (('KL_BackSwat', 1), ('M_Back', 6), ('M_Wave', 5)):
        g = M.by_entity(M.ents(a, pat))
        chk('%s rows present (the stage is the one loaded)' % pat, len(g) >= 1, '%d entities (%d men authored), e.g. %s' % (len(g), n, sorted(x for _, x in g)[:3]))
    cen = sorted({int(m.group(1)) for l in a for m in [re.search(r'botfill: round census: (\d+) ZFFActor', l)] if m})
    chk('census 48 logged (backswat stage; 44 = the live map without it)', 48 in cen, 'census lines %s' % (cen or 'none'), warn=True)
    van = [l for l in a if 'pos dm03bs-van' in l]
    chk('host reached the van stop (tele)', bool(van), van[0][van[0].find('pos '):][:100] if van else 'no pos line (tele refused?)', warn=True)
    info.append('SWAT look (black SWAT bodies, rifles) at the garage, ramp and van stop vs police at the front: LOOK at the shots after "dm03bs host at the van stop"')
    return res, info


def stamp(k):
    rec = recorded(k)
    live_dll = md5_file('%s/dinput8.dll' % M.DD)
    pin(live_dll if live_dll in MERGED_KITS else rec.get('ship', next(iter(MERGED_KITS))))
    _stamp(k)


def load_pins():
    # the kit named on the command line first: another kit's older kit.json (e.g. DM03BS under 1110d) would pin the wrong SHIP
    named = [a for a in sys.argv[1:] if a in K]
    rec = next((recorded(k) for k in named + list(K) if recorded(k)), {})
    if rec.get('ship') in MERGED_KITS:
        pin(rec['ship'])
        M.INI_MD5 = rec.get('ini', M.INI_MD5)
    else:
        live_dll = md5_file('%s/dinput8.dll' % M.DD)
        pin(live_dll if live_dll in MERGED_KITS else next(iter(MERGED_KITS)))


_stamp = M.stamp
for _k, _c in K.items():
    for _a, _b in dict(entry=0, stage=None, tag=None, hook=M.HOOK, solo_secs=600, parts=('online',), keepalive=1).items():
        _c.setdefault(_a, _b)
    if _k == 'DM03BS_1110':
        _c['doors'] = ('DM03', 'F03', (176,))  # the live kick door the DM03_1109 segment kicks (dm03doorfix_1109 kept 176)
M.K.clear()
M.K.update(K)
M.ORDER[:] = ORDER
M.KIT = B.KIT = KIT
B.KITS.clear()
B.KITS.update(K)
M.segment, M.item_checks, M.stamp, M.base_ini = segment, item_checks, stamp, base_ini
load_pins()


def order():
    M.order()


if __name__ == '__main__':
    vault_pins()
    sys.exit(M.main())
