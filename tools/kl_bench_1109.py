#!/usr/bin/env python3
"""
Bench kits for the maps INSTALLED on 2026-11-08/09 (nothing is staged: every kit runs on the live map folder as it is and pins its md5s).
Built on tools/kl_bench_1106.py (imported; its KITS table is replaced in this process only). 2 seats, Q32 online pair, round 1 -> shop -> round 2.
A per-kit item segment is spliced into BOTH seats' scripts right after the first `waitload`; only the host seat moves (tele / goto / tap E).

    python tools/kl_bench_1109.py gen [kit|all]       write C:/kl_build_1024/bench_1109/<kit> (no game contact; reads the live zips and the
                                                      *.before-doors_1108 backups read-only to find the door stand points)
    python tools/kl_bench_1109.py validate [kit|all]  DRY RUN: pins, TEST dll, script ops, door/stand data. Never launches the game.
    python tools/kl_bench_1109.py run <kit>           ONE bench (needs the game free: no other kl2.exe). Nothing is installed; the map folder
                                                      md5s are compared before/after.
    python tools/kl_bench_1109.py verify <kit>        re-read the logs of the last run (no game contact)
    python tools/kl_bench_1109.py order               (re)write C:/kl_build_1024/bench_1109/RUN_ORDER.txt

Kits: HASTA1109 (DM11B) DM03_1109 DM02_1109 DM01B_1109 DM07_1109 DOORS_1109_DM01 DOORS_1109_DM03A (DOORS_1109 = the last two).
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
# live = f0's merged_1108g: SHIP d1145cbe (built from b5465f50), its TEST twin (build_auto.bat, klauto) 95de3af2; KLHook.ini f7f11dcc is still the one
# merged_1108f wrote (1108g is dll only), so the base ini fallback stays on INI_KIT's install.py + backup.
# The live dinput8.dll can be a peer's TEST dll swapped in by a bench, so the kit takes the twin from the merged kit folder, never from the live file.
MERGED = 'C:/kl_build_1024/merged_1108g'
INI_KIT = 'C:/kl_build_1024/merged_1108f'
SHIP_MD5 = 'd1145cbef96b405f4bbba13e7c555ed4'
TEST_MD5 = '95de3af20ff3fab80526460de5c37bee'
INI_MD5 = 'f7f11dccac532b7ffcb283526eb3ca73'
HOOK = (MERGED + '/dll_test/dinput8.dll', TEST_MD5)
INI_KEYS = (('ShopPage', 'TidyPage2'), ('Hire', 'TidyPage'))      # fc's keys merged_1108f writes (=1)
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
    'DOORS_1109_DM01': dict(map='DM01', slot='F01', live={'F01_Main.zip': '444a3ed6', 'F01_Main.bots.zip': 'f3ed6155', 'KLJoin.ini': 'db4516c6'}, shots='60-700:20',
                            doors=('DM01', 'F01', (957, 2569))),
    'DOORS_1109_DM03A': dict(map='DM03A', slot='F07', live={'F07_Main.zip': 'aa79d66d', 'F07_Main.bots.zip': 'd1a8dd0c', 'KLJoin.ini': '958c24b6'}, shots='60-700:20',
                             doors=('DM03A', 'F07', (6516,))),
}
ORDER = ['HASTA1109', 'DM03_1109', 'DM02_1109', 'DM01B_1109', 'DM07_1109', 'DOORS_1109_DM01', 'DOORS_1109_DM03A']
for _k, _c in K.items():
    _c.update(entry=0, stage=None, tag=None, hook=HOOK, solo_secs=600, parts=('online',))
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
            out.append(dict(host=int(mm.group(1)), name=p.split(BS, 1)[1][:34], hinge=[round(v) for v in P], front=a, back=b))
    return out


def door_seg(d, lbl):
    """Walk to the leaf from the mesh side, kick (2 taps of E, GUESS key), look at the leaf before/after, walk through when both sides are on the mesh."""
    h = d['hinge']
    a = d['front'] or d['back']
    b = d['back'] if d['front'] and d['back'] else None
    # aim at the doorway's middle (half way between the two stand points), not the hinge: DM03_1109 run 1 walked at the hinge edge
    # 60 cm off-centre, stuck on the jamb with a 104 deg bearing error and pressed E at the wall. One-sided doors keep the hinge.
    c = ((a[0] + b[0]) / 2.0, (a[2] + b[2]) / 2.0) if b else (h[0], h[2])
    s = ['tele %d %d %d' % (a[0], a[1] + 150, a[2]), 'wait 2500', 'pos %s-stand' % lbl, 'log BENCH1109 %s door %s: before' % (lbl, d['host']),
         'ents KL_Door 20', 'ents Door 200',
         'face %d %d' % c, 'goto %d %d 70 6000' % c, 'face %d %d' % c, 'pos %s-at-leaf' % lbl,
         'tap E 700', 'wait 600', 'tap E 700', 'wait 3500', 'log BENCH1109 %s door %s: kicked (E x2, GUESS key)' % (lbl, d['host']), 'pos %s-kicked' % lbl,
         'ents KL_Door 20', 'ents Door 200']
    if b:
        s += ['goto %d %d 70 9000' % (b[0], b[2]), 'pos %s-through' % lbl, 'log BENCH1109 %s door %s: through goto done' % (lbl, d['host'])]
    return s


# ------------------------------------------------------------------ item segments
def hasta_seg(who):
    s = ['wait 6000']
    for i in range(14):
        s += ['ents BarricadeB_ 8', 'ents OYCHECK 8', 'ents Roadblock_01 4', 'ents Broken01 4', 'log BENCH1109 hasta sample %d' % i, 'wait 9000']
    s += ['pos hasta-end']
    return s


def vans_seg(who, lead, lbl):
    """Samples of the van entity every ~5 s from the load, state 3 (waiting), 7 (leaving), then every 3 s while it leaves."""
    s = []
    for i in range(6):
        s += ['ents V_Van 3', 'wait 5000']
    s += ['log BENCH1109 %s waiting for vehicle state 3' % lbl, 'waitvan 3 300000', 'ents V_Van 3', 'log BENCH1109 %s van at state 3' % lbl, 'wait 10000', 'ents V_Van 3',
          'waitvan 7 150000', 'log BENCH1109 %s van at state 7 (leaving)' % lbl]
    for i in range(10):
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
    s = ['ents Chainlink_Fence 8', 'log BENCH1109 dm07 fence panels read']
    s += vans_seg(who, 0, 'dm07')
    if who == 'host':
        # players cannot walk out through the gap: stand east of the fence (floor from the mesh + 150), walk west through z 10400 toward x -6000.
        # CONTROL: from the same start, the same length through open mesh must be reached, else a blocked goto proves nothing (kit file dm07.json).
        p = '%s/dm07.json' % kd('DM07_1109')
        c = json.load(open(p)) if os.path.isfile(p) else dict(start=[-3900, 552, 10400], control=None)
        s += ['tele %d %d %d' % tuple(c['start']), 'wait 2500', 'pos dm07-east-of-fence', 'goto -6000 10400 200 15000', 'pos dm07-after-walk', 'log BENCH1109 dm07 walk west done']
        if c.get('control'):
            s += ['tele %d %d %d' % tuple(c['start']), 'wait 2500', 'goto %d %d 200 15000' % tuple(c['control']), 'pos dm07-after-control', 'log BENCH1109 dm07 control walk done']
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
            kv = [(a, b) for a, b in kv if a not in ('CmdAdd', 'MaxRunMs')] + [('CmdAdd', '-o DisableSplashScreens -o AutoExit=%d' % total), ('MaxRunMs', str((total - 10) * 1000))]
        t.append('[%s]' % name)
        t += ['%s=%s' % kv_ for kv_ in kv]
    t += probes(k) + ['[Script]'] + B.renumber(scr)
    return '\n'.join(t) + '\n'


def md5_of(b):
    import hashlib
    return hashlib.md5(b).hexdigest()


def base_ini():
    """-> (bytes, source). The live KLHook.ini when it is f0's merged_1108f one (f7f11dcc, read only); else (a bench is running and has swapped its own ini in)
    the ini merged_1108f's install.py would write: its .before-merged1108f backup + the two Tidy keys, accepted only when that md5 is f7f11dcc."""
    live = open('%s/KLHook.ini' % DD, 'rb').read()
    if md5_of(live) == INI_MD5:
        return live, 'live KLHook.ini'
    import importlib.util
    sp = importlib.util.spec_from_file_location('merged1108f_install', INI_KIT + '/install.py')
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    bak = '%s/KLHook.ini.before-merged1108f' % DD
    out = m.set_keys(open(bak, 'rb').read().decode('latin1'), m.KEYS).encode('latin1')
    if md5_of(out) != INI_MD5:
        raise SystemExit('gen: live KLHook.ini is %s (not %s) and %s + merged_1108f keys gives %s: no base ini, stop' % (md5_of(live)[:8], INI_MD5[:8], bak, md5_of(out)[:8]))
    return out, 'merged_1108f install.py set_keys on KLHook.ini.before-merged1108f (live differed: %s)' % md5_of(live)[:8]


def stamp(k):
    """Pin the kit to MERGED (merged_1108g): the TEST twin dll from its folder and the base ini; record both (and the SHIP they twin) in kit.json."""
    import shutil
    d = kd(k)
    src = MERGED + '/dll_test/dinput8.dll'
    if md5_of(open(src, 'rb').read()) != TEST_MD5:
        raise SystemExit('gen: %s is not the TEST twin %s' % (src, TEST_MD5[:8]))
    shutil.copy2(src, '%s/hook_test/dinput8.dll' % d)
    ini, how = base_ini()
    open('%s/KLHook_base.ini' % d, 'wb').write(ini)
    B.write('%s/kit.json' % d, json.dumps(dict(ship=SHIP_MD5, test=TEST_MD5, ini=md5_of(ini), ini_source=how, merged=MERGED, built_from='b5465f50'), indent=1))


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
            if who == 'host' and (K[k].get('doors') or K[k].get('doors2')):
                dj = '%s/doors.json' % d
                dd = json.load(open(dj)) if os.path.isfile(dj) else []
                v.ok(bool(dd), 'doors.json: %d doors, stand points %s' % (len(dd), [bool(x['front'] or x['back']) for x in dd]))
                v.ok(any('tele' in l for l in scr) and any(l.startswith('goto') for l in scr), 'host script teleports to the stand and walks to the leaf')
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
            v.ok(md5_of(raw) == INI_MD5 and rec.get('ini') == INI_MD5, 'base ini md5 %s = recorded %s = merged_1108f live ini %s (%s)' % (md5_of(raw)[:8], str(rec.get('ini'))[:8], INI_MD5[:8], rec.get('ini_source', '?')))
            sec, got = None, set()
            for l in raw.decode('latin1').splitlines():
                m_ = re.match(r'\s*\[([^\]]+)\]', l)
                if m_:
                    sec = m_.group(1).lower()
                elif sec and re.match(r'\s*(\w+)\s*=\s*1\b', l) and (sec, re.match(r'\s*(\w+)', l).group(1).lower()) in {(s_.lower(), k_.lower()) for s_, k_ in INI_KEYS}:
                    got.add((sec, re.match(r'\s*(\w+)', l).group(1).lower()))
            v.ok(len(got) == len(INI_KEYS), 'base ini carries fc TidyPage2=1 under [ShopPage] and TidyPage=1 under [Hire] (%d of %d)' % (len(got), len(INI_KEYS)))
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


def door_lbl(k, i):
    return 'dm03door' if k == 'DM03_1109' else 'dm02door%d' % (i + 1) if k == 'DM02_1109' else 'door%d' % (i + 1)


STOP_DM01B = (4454, 31907)


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
    if k in ('DM01B_1109', 'DM07_1109'):
        van = ents(a, 'V_Van')
        s3 = next((l for l in a if 'BENCH1109' in l and 'van at state 3' in l), None)
        s7 = next((l for l in a if 'BENCH1109' in l and 'van at state 7' in l), None)
        chk('van entity sampled', bool(van), '%d rows' % len(van))
        chk('vehicle state 3 reached (van waits)', s3 is not None, s3[:12] if s3 else 'waitvan 3 timed out (the van never waited within 300 s)')
        chk('vehicle state 7 reached (van leaves)', s7 is not None, s7[:12] if s7 else 'waitvan 7 timed out')
        t3 = secs_of(s3) if s3 else None
        t7 = secs_of(s7) if s7 else None
        at3 = sorted((v for v in van if t3 is not None and abs(secs_of(v[0]) - t3) < 4), key=lambda v: abs(secs_of(v[0]) - t3)) if van else []
        late = [v for v in van if t7 is not None and secs_of(v[0]) > t7 + 15]
        chk('van sampled at state 3 (within 4 s)', bool(at3), '%d rows' % len(at3))
        chk('van sampled 15+ s after state 7', bool(late), '%d rows' % len(late))
        if k == 'DM01B_1109':
            stop = STOP_DM01B
            n = at3[0] if at3 else None                                       # the sample nearest the state-3 line: x and z of the SAME row
            chk('van waits near the stop (4454, 31907)', n is not None and math.hypot(n[3][0] - stop[0], n[3][2] - stop[1]) < 2500,
                'at state 3: %s' % (str(n[3]) if n else 'no sample'))
            chk('van starts west (x < stop - 3000) at the first sample', bool(van) and van[0][3][0] < stop[0] - 3000, 'first %s' % (str(van[0][3]) if van else 'no sample'))
            chk('van left EAST of the stop', bool(late and at3) and late[-1][3][0] > at3[0][3][0] + 1000,
                'stop x %s, last x %s' % ('%.0f' % at3[0][3][0] if at3 else '-', '%.0f' % late[-1][3][0] if late else '-'))
        else:
            chk('van reversed out WEST (x decreasing after state 7)', bool(late and at3) and late[-1][3][0] < at3[0][3][0] - 500,
                'stop x %s, last x %s' % ('%.0f' % at3[0][3][0] if at3 else '-', '%.0f' % late[-1][3][0] if late else '-'))
        if s7:
            seq = [v for v in van if secs_of(v[0]) > t7]
            steps = [math.dist(x[3], y[3]) / max(0.1, secs_of(y[0]) - secs_of(x[0])) for x, y in zip(seq, seq[1:])]
            info.append('leave speeds (cm/s between samples, a pop would be one outlier): %s' % ' '.join('%.0f' % s for s in steps[:12]))
        info.append('no-pop: 3 s samples cannot show a one-frame jump; LOOK at the shots around state 7 and the arrival')
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
    if k in ('DM03_1109', 'DM02_1109', 'DOORS_1109_DM01', 'DOORS_1109_DM03A'):
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
    same = B.snap(md) == before
    print('map folder unchanged: %s' % same)
    print('RESULT: %s run done, %s' % (k, 'ALL PASS' if not (rc or not same) else 'see FAIL lines'))
    return 1 if (rc or not same) else 0


def order():
    t = ['bench_1109 RUN ORDER (written by tools/kl_bench_1109.py order). ONE bench at a time; each needs the game free.',
         'Before EACH: tasklist | findstr /i kl2.exe  must show nothing (a zombie with 0 threads is fine). Peers (f0 merged_1108g, fc shop, d0) bench too:',
         'wait for their "done, game free". Nothing is installed by any of these; every kit pins the live md5s and compares the map folder after.',
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
