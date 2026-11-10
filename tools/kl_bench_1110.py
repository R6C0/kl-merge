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
    '6711bc5f5d9c6cbec06072f856ffe7f9': ('C:/kl_build_1024/merged_1110f/kit', 'ddf81d7f63a80169180dc307281eafb5'),  # 1110d + [Crash] ListUserGuard
}

K = {
    # STAGE KIT: back SWAT. 6 KL_Garage!Back + 5 KL_Ramp!Wave men re-formed to SWAT (EscSquad Reinforcement_01 template, AK74 / Type81),
    # + KL_BackSwat!Van: 4 SWAT around the van stop (3306, 2, 4), Defend, started by KL_BackSwat!Clock\Go. Census 44/29 -> 48/30. Front stays police.
    # The host goes to the van stop after the census samples (tele + shots) so the screenshots show the back; GUESS: (3306, 152, 4) is open floor.
    'DM03BS_1110': dict(map='DM03', slot='F03', live={'F03_Main.zip': '8e23cbd3', 'F03_Main.bots.zip': '2528e8f0', 'KLJoin.ini': '5c02ca99'}, shots='60-900:20',
                        stage='C:/kl_build_1024/dm03backswat_1110', tag='.before-dm03backswat1109',
                        files={'F03_Main.zip': 'a81ede87', 'F03_Main.bots.zip': 'e8c06e13', 'F03_Main.bots.base.md5': 'afc6ca40'}),
}
# VAULT kits (tools/kl_dm03vault_1110.py): live + files are filled from the final chain (back-SWAT a81ede87 -> d0 smartcops -> vault) by vault_pins()
# once the vault stage is re-staged on the live input; until then `gen` refuses them (no pins).
#   DM03VAULT_1110:  the host walks into KL_Vault!1\Arm -> 3 s Fuse -> Boom; doors sampled before/after, walk through the doorway, then
#                    sampled again past 240 s (the Backstop TriggerDelay2 cannot be cancelled: does it replay the opening and snap the leaves?)
#   DM03VAULTB_1110: nobody arms it; doors sampled at ~220 s and ~260 s from the round start: the Backstop alone opens them, quietly
VAULT_STAGE = 'C:/kl_build_1024/dm03vault_1110/stage_sc'  # on d0's smartcops DM03 (33361cd1), itself on back-SWAT a81ede87
for _k in ('DM03VAULT_1110', 'DM03VAULTB_1110'):
    K[_k] = dict(map='DM03', slot='F03', live={}, files={}, shots='60-900:20', stage=VAULT_STAGE, tag='.before-dm03vault1110')
ORDER = ['DM03BS_1110', 'DM03VAULT_1110', 'DM03VAULTB_1110']
VAN_STOP = (3306, 2, 4)
# from the vault stage's build report (GUESS-labelled there): Arm box centre (0, 340, -7006) half (150, 120, 150); doorway hinges x +-105 at z -6812;
# the moved piles at (0, 241, -6620), (120, 241, -6540), (200, 241, -6660)
VAULT_LOBBY = (0, 300, -7300)       # vestibule / lobby side, south of the Arm box (box z -7156..-6856); GUESS: open floor (lobby nav z -7500..-7000)
VAULT_ARM = (0, -6980)
VAULT_DOCK = (0, -6600)             # just past the doorway, dock side


def vault_pins():
    """Fill the two vault kits' live/files pins from the stage's install.py (its pinned input md5s -> output md5s) so `gen` and `run` check them.
    -> True when the stage exists and pins were read."""
    p = '%s/install.py' % VAULT_STAGE
    if not os.path.isfile(p):
        return False
    t = open(p, encoding='utf-8', errors='replace').read()
    # install.py: FILES = [('F03_Main.zip', '<input md5>', '<output md5>'), ...]
    pairs = re.findall(r"\('([\w.]+)',\s*'([0-9a-f]{32})',\s*'([0-9a-f]{32})'\)", t)
    if not pairs:
        return False
    for k in ('DM03VAULT_1110', 'DM03VAULTB_1110'):
        K[k]['live'] = {n: a[:8] for n, a, _ in pairs}
        K[k]['files'] = {n: b[:8] for n, _, b in pairs}
    return True


def vault_seg(who, arm):
    s = ['wait 3000', 'ents KL_Vault 10', 'ents KL_Door_4 10', 'ents KL_Door_5 10', 'log BENCH1110 vault t0']
    if who != 'host':
        for i in range(1, 9):
            s += ['wait 30000', 'ents KL_Vault 10', 'ents KL_Door_4 10', 'ents KL_Door_5 10', 'log BENCH1110 vault client sample %d' % i]
        return s
    s += ['waitstate 0x19 90000', 'tele %d %d %d' % VAULT_LOBBY, 'wait 2500', 'pos vault-lobby',
          'ents KL_Door_4 10', 'ents KL_Door_5 10', 'log BENCH1110 vault doors shut (before)']
    if arm:
        s += ['goto %d %d 40 6000' % VAULT_ARM, 'pos vault-arm', 'log BENCH1110 vault host in the Arm box',
              'wait 1500', 'ents KL_Vault 10', 'log BENCH1110 vault fuse running', 'wait 4000',
              'ents KL_Vault 10', 'ents KL_Door_4 10', 'ents KL_Door_5 10', 'log BENCH1110 vault after the blast',
              'goto %d %d 40 8000' % VAULT_DOCK, 'pos vault-dock', 'log BENCH1110 vault walked through the doorway',
              'goto %d %d 40 6000' % (VAULT_LOBBY[0], VAULT_LOBBY[2])]
        # the Backstop fires 240 s after the AIMonitor start: sample from ~200 s to ~290 s after this point (the arm happens well inside the first minute)
        s += ['wait 150000']
    else:
        s += ['wait 180000']
    for i in range(1, 10):
        s += ['ents KL_Vault 10', 'ents KL_Door_4 10', 'ents KL_Door_5 10', 'pos vault-late%d' % i, 'log BENCH1110 vault late sample %d' % i, 'wait 10000']
    s += ['goto %d %d 40 8000' % VAULT_DOCK, 'pos vault-dock-late', 'log BENCH1110 vault late walk through']
    return s


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
    if k == 'DM03BS_1110':
        p = '%s/doors.json' % M.kd(k)
        return back_seg(who, json.load(open(p)) if os.path.isfile(p) else [])
    return _segment(k, who)


def vault_checks(k, a):
    res, info = [], []

    def chk(name, cond, detail='', warn=False):
        res.append(('PASS' if cond else ('WARN' if warn else 'FAIL'), name, detail))
    chk('item segment ran on the host (level loaded ... segment done)', any('BENCH1109 %s host level loaded' % k in l for l in a)
        and any('BENCH1109 %s host segment done' % k in l for l in a), '%d host log lines' % len(a))
    g = M.by_entity(M.ents(a, 'KL_Vault'))
    chk('KL_Vault rows present (the vault stage is the one loaded)', len(g) >= 1, '%d entities, e.g. %s' % (len(g), sorted(x for _, x in g)[:5]))
    for d in ('KL_Door_4', 'KL_Door_5'):
        chk('%s rows present (vault leaf)' % d, len(M.by_entity(M.ents(a, d))) >= 1)
    lobby = [l for l in a if 'pos vault-lobby' in l]
    chk('host reached the lobby (tele)', bool(lobby), lobby[0][lobby[0].find('pos '):][:100] if lobby else 'no pos line', warn=True)
    if k == 'DM03VAULT_1110':
        arm = [l for l in a if 'pos vault-arm' in l]
        chk('host stood in the Arm box', bool(arm), arm[0][arm[0].find('pos '):][:100] if arm else 'no pos line', warn=True)
        dock = [l for l in a if 'pos vault-dock:' in l or 'pos vault-dock ' in l]
        # through = the body ended up dock side of the doorway (z > -6780) after the blast
        zs = [float(m.group(1)) for l in dock for m in [re.search(r'\(\s*-?[\d.]+,\s*-?[\d.]+,\s*(-?[\d.]+)\)', l)] if m]
        chk('walked through the doorway after the blast (z > -6780)', any(z > -6780 for z in zs), 'z %s' % zs, warn=True)
        info.append('blast: LOOK/listen at the shots right after "vault host in the Arm box" (+3 s): fire, shake, rocket sound 407600')
    late = [float(m.group(1)) for l in a if 'pos vault-dock-late' in l for m in [re.search(r'\(\s*-?[\d.]+,\s*-?[\d.]+,\s*(-?[\d.]+)\)', l)] if m]
    chk('late walk through the doorway (after the Backstop time) reached the dock side', any(z > -6780 for z in late), 'z %s' % late, warn=True)
    info.append('Backstop replay: compare the KL_Door_4/5 rows across "vault late sample 1..9" (a position or hidden-flag change after the blast = replay)')
    return res, info


def item_checks(k, a, dd=(), ctrl=None):
    if k in ('DM03VAULT_1110', 'DM03VAULTB_1110'):
        return vault_checks(k, a)
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
    rec = next((recorded(k) for k in K if recorded(k)), {})
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
