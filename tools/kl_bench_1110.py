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
}

K = {
    # STAGE KIT: back SWAT. 6 KL_Garage!Back + 5 KL_Ramp!Wave men re-formed to SWAT (EscSquad Reinforcement_01 template, AK74 / Type81),
    # + KL_BackSwat!Van: 4 SWAT around the van stop (3306, 2, 4), Defend, started by KL_BackSwat!Clock\Go. Census 44/29 -> 48/30. Front stays police.
    # The host goes to the van stop after the census samples (tele + shots) so the screenshots show the back; GUESS: (3306, 152, 4) is open floor.
    'DM03BS_1110': dict(map='DM03', slot='F03', live={'F03_Main.zip': '8e23cbd3', 'F03_Main.bots.zip': '2528e8f0', 'KLJoin.ini': '5c02ca99'}, shots='60-900:20',
                        stage='C:/kl_build_1024/dm03backswat_1110', tag='.before-dm03backswat1109',
                        files={'F03_Main.zip': 'a81ede87', 'F03_Main.bots.zip': 'e8c06e13', 'F03_Main.bots.base.md5': 'afc6ca40'}),
}
ORDER = ['DM03BS_1110']
VAN_STOP = (3306, 2, 4)


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
    if k == 'DM03BS_1110':
        p = '%s/doors.json' % M.kd(k)
        return back_seg(who, json.load(open(p)) if os.path.isfile(p) else [])
    return _segment(k, who)


def item_checks(k, a, dd=(), ctrl=None):
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
    _c['doors'] = ('DM03', 'F03', (176,))     # the live kick door the DM03_1109 segment kicks (dm03doorfix_1109 kept 176)
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
    sys.exit(M.main())
