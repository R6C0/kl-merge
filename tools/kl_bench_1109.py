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
HOOK = ('C:/kl_build_1024/merged_1108c/dll_test/dinput8.dll', '09a02a2cbcbeebb3eb3f01310c8b0cf8')   # TEST twin 09a02a2c of the live SHIP 246c643d
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
    s = ['tele %d %d %d' % (a[0], a[1] + 150, a[2]), 'wait 2500', 'pos %s-stand' % lbl, 'log BENCH1109 %s door %s: before' % (lbl, d['host']),
         'ents KL_Door 20', 'ents Door 200',
         'goto %d %d 70 6000' % (h[0], h[2]), 'pos %s-at-leaf' % lbl,
         'tap E 700', 'wait 600', 'tap E 700', 'wait 3500', 'log BENCH1109 %s door %s: kicked (E x2, GUESS key)' % (lbl, d['host']), 'pos %s-kicked' % lbl,
         'ents KL_Door 20', 'ents Door 200']
    if b:
        s += ['goto %d %d 70 9000' % (b[0], b[2]), 'pos %s-through' % lbl, 'log BENCH1109 %s door %s: through goto done' % (lbl, d['host'])]
    return s


# ------------------------------------------------------------------ item segments
def hasta_seg(who):
    s = ['wait 6000']
    for i in range(14):
        s += ['ents BarricadeB_ 8', 'ents OYCHECK 8', 'ents Roadblock_01 4', 'log BENCH1109 hasta sample %d' % i, 'wait 9000']
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


def dm07_seg(who):
    s = ['ents Chainlink_Fence 8', 'log BENCH1109 dm07 fence panels read']
    s += vans_seg(who, 0, 'dm07')
    if who == 'host':
        # players cannot walk out through the gap: stand east of the fence (x -3900, floor y GUESS 402 + 150), walk west through z 10400 toward x -6000
        s += ['tele -3900 552 10400', 'wait 2500', 'pos dm07-east-of-fence', 'goto -6000 10400 200 15000', 'pos dm07-after-walk', 'log BENCH1109 dm07 walk west done']
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


def gen(which='all'):
    for k in ORDER:
        if which not in ('all', k) and not (which == 'DOORS_1109' and k.startswith('DOORS_1109_')):
            continue
        B.gen(k)
        d = kd(k)
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
        base = '%s/KLHook_base.ini' % d
        if os.path.isfile(base):
            txt = open(base, encoding='latin-1').read()
            cb = (re.search(r'^ClientBuildMaps=([^\s;]*)', txt, re.M) or [0, ''])[1].split(',')
            need = K[k]['slot'] in ('F01', 'F03')          # only the DM01 / DM03 slots need the client build (memory: DM03 clients assert without it); the others load as they are
            v.ok(K[k]['slot'] in cb or not need, 'ClientBuildMaps=%s: %s %s' % (','.join(cb), K[k]['slot'], 'listed (needed for this slot)' if need else 'not needed for this slot (live setup, as the dm06b benches)'))
    print('RESULT: bench_1109 extras %s - %d FAIL (B.validate rc %d)' % ('OK' if not v.fail else 'FAILED', v.fail, rc))
    return 1 if (v.fail or rc) else 0


# ------------------------------------------------------------------ verify
ENT = re.compile(r"ents #\d+ slot \d+ obj \w+ name '([^']*)' .*?\(flags ([0-9a-fA-F]+)\) pos [^(]*\((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)")


def ents(lines, sub):
    """-> [(time, name, hidden, (x, y, z))] for every ents row whose name contains sub."""
    out = []
    for l in lines:
        m = ENT.search(l)
        if m and sub.lower() in m.group(1).lower():
            out.append((l[:12], m.group(1), bool(int(m.group(2), 16) & 0x400), tuple(float(m.group(i)) for i in (3, 4, 5))))
    return out


def secs_of(t):
    return int(t[0:2]) * 3600 + int(t[3:5]) * 60 + float(t[6:12])


def goto_lines(lines, x, z):
    return [l for l in lines if re.search(r'script \d+: goto \(%d, %d\) ' % (x, z), l)]


def verify(k, part='online'):
    rc = B.verify(k, 'online')
    L = B.logs('%s_online' % k)
    if 1 not in L:
        return 1
    a = L[1]
    res = []

    def chk(name, cond, detail='', warn=False):
        res.append(cond or warn)
        print('  %s %s %s' % ('PASS' if cond else ('WARN' if warn else 'FAIL'), name, detail))
    print('item checks %s (host log, %d lines)' % (k, len(a)))
    if k == 'HASTA1109':
        for pat in ('OYCHECK_BEFORE01', 'BarricadeB_01', 'Roadblock_01'):
            r = ents(a, pat)
            if r:
                chk('%s hidden by the beat' % pat, (not r[0][2]) and r[-1][2], 'first %s hidden=%s, last %s hidden=%s (%d samples)' % (r[0][0], r[0][2], r[-1][0], r[-1][2], len(r)), warn=not r[-1][2] and not r[0][2] and False)
            else:
                chk('%s sampled' % pat, False, 'no ents row (name not in the table?)', warn=True)
        for pat in ('Broken01', 'OYCHECK_AFTER01'):
            r = ents(a, pat)
            if r:
                chk('%s hidden at load, shown after the beat' % pat, r[0][2] and not r[-1][2], 'first hidden=%s, last hidden=%s (%d samples; 30 s backstop opens it)' % (r[0][2], r[-1][2], len(r)))
            else:
                chk('%s sampled' % pat, False, 'no ents row', warn=True)
        print('  info boom / camera shake / glare: not logged; LOOK at KLShot_inst1_*.jpg around the beat (timestamps of the hasta sample lines below)')
        for l in a:
            if 'BENCH1109 hasta sample' in l:
                print('       ', l[:12], l[13:90])
    if k in ('DM01B_1109', 'DM07_1109'):
        van = ents(a, 'V_Van')
        stl = [(l[:12], re.search(r'state (\d)', l)) for l in a if 'BENCH1109' in l and 'van at state' in l]
        chk('van entity sampled', bool(van), '%d rows' % len(van))
        s3 = next((l for l in a if 'BENCH1109' in l and 'van at state 3' in l), None)
        s7 = next((l for l in a if 'BENCH1109' in l and 'van at state 7' in l), None)
        chk('vehicle state 3 reached (van waits)', s3 is not None, s3[:12] if s3 else 'waitvan 3 timed out (the van never waited within 300 s)')
        chk('vehicle state 7 reached (van leaves)', s7 is not None, s7[:12] if s7 else 'waitvan 7 timed out')
        if van and s3 and s7:
            t3, t7 = secs_of(s3), secs_of(s7)
            at3 = [v for v in van if abs(secs_of(v[0]) - t3) < 4]
            late = [v for v in van if secs_of(v[0]) > t7 + 15]
            first = van[0][3]
            if k == 'DM01B_1109':
                stop = (4454, 31907)
                if at3:
                    chk('van waits near the stop (4454, 31907)', math.hypot(at3[0][3][0] - stop[0], at3[0][3][2] - stop[1]) < 2500 or math.hypot(at3[0][3][0] - stop[0], at3[1 if len(at3) > 1 else 0][3][2] - stop[1]) < 2500, 'at state 3: %s' % (at3[0][3],))
                chk('van starts west (x < stop - 3000) at the first sample', first[0] < stop[0] - 3000, 'first %s' % (first,), warn=True)
                if late and at3:
                    chk('van left EAST of the stop', late[-1][3][0] > at3[0][3][0] + 1000, 'stop x %.0f, last x %.0f' % (at3[0][3][0], late[-1][3][0]))
            else:
                if late and at3:
                    chk('van reversed out WEST (x decreasing after state 7)', late[-1][3][0] < at3[0][3][0] - 500, 'stop x %.0f, last x %.0f' % (at3[0][3][0], late[-1][3][0]))
            seq = [v for v in van if secs_of(v[0]) > t7]
            steps = [math.dist(x[3], y[3]) / max(0.1, secs_of(y[0]) - secs_of(x[0])) for x, y in zip(seq, seq[1:])]
            print('  info leave speeds (cm/s between samples, a pop would be one outlier): %s' % ' '.join('%.0f' % s for s in steps[:12]))
        print('  info no-pop: 3 s samples cannot show a one-frame jump; LOOK at the shots around state 7 and the arrival')
    if k == 'DM07_1109':
        fe = ents(a, 'Chainlink_Fence_4m')
        pan = [r for r in fe if r[1].endswith('4m_01') or r[1].endswith('4m_11')]
        chk('fence panels 4m_01 / 4m_11 hidden (gate)', bool(pan) and all(r[2] for r in pan), '%d rows: %s' % (len(pan), sorted({(r[1][-5:], r[2]) for r in pan})))
        g = goto_lines(a, -6000, 10400)
        tp = [l for l in a if 'tele' in l and ('REFUSED' in l or 'MISSED' in l or 'FAULTED' in l) and '-3900' in l]
        if g:
            blocked = any('NOT reached' in l for l in g)
            pos = [nums_ for nums_ in [B.nums(l) for l in a if 'pos dm07-after-walk' in l]]
            xs = pos[0][-4] if pos and len(pos[0]) >= 4 else None
            chk('player does NOT walk out through the gap', blocked and (xs is None or xs > -4700), 'goto: %s | after-walk pos line %s' % (g[0][g[0].find('goto'):][:110], 'x=%s' % xs), warn=bool(tp))
        else:
            chk('walk-out goto ran', False, 'no goto line%s' % (' (tele refused: %s)' % tp[0][:100] if tp else ''), warn=True)
    if k in ('DM03_1109', 'DM02_1109', 'DOORS_1109_DM01', 'DOORS_1109_DM03A'):
        dj = '%s/doors.json' % kd(k)
        dd = json.load(open(dj)) if os.path.isfile(dj) else []
        use = dd[:1] if k == 'DM03_1109' else dd
        for d in use:
            h = d['hinge']
            leaf = [r for r in ents(a, 'Door') if math.hypot(r[3][0] - h[0], r[3][2] - h[2]) < 150 and abs(r[3][1] - h[1]) < 200]
            chk('door %s leaf entity found near its hinge' % d['host'], bool(leaf), '%d rows (before + after); %s' % (len(leaf), ' | '.join('%s %s hidden=%s' % (r[0][:8], r[1][-18:], r[2]) for r in leaf[:4])), warn=True)
            b = d['back'] if d['front'] and d['back'] else None
            if b:
                g = goto_lines(a, b[0], b[2])
                chk('door %s: player walks through after the kick' % d['host'], bool(g) and 'NOT reached' not in g[-1] and ' reached ' in g[-1], g[-1][g[-1].find('goto'):][:120] if g else 'no goto line (tele refused?)',
                    warn=not g)
            else:
                print('  info door %s is one-sided on the mesh: no walk-through check, kick + shot only' % d['host'])
            tp = [l for l in a if 'tele' in l and ('REFUSED' in l or 'MISSED' in l or 'FAULTED' in l)]
            if tp:
                print('  info tele problem: %s' % tp[0][:160])
        print('  info kick sound / swing: not logged; LOOK at the shots and listen. Kick key E is a GUESS (boarding uses E)')
    if k == 'DM03_1109':
        for pat in ('ArrivingCops', 'Garage', 'Ramp', 'VehicleExit'):
            r = ents(a, pat)
            print('  info %-13s rows %d, names %s' % (pat, len(r), sorted({x[1][-26:] for x in r})[:6]))
        for pat in ('Cop', 'Police'):
            r = ents(a, pat)
            s1 = [x for x in r if secs_of(x[0]) - secs_of(r[0][0]) < 20]
            print('  info %-13s rows %d (first sample %d)' % (pat, len(r), len(s1)))
        cen = sorted({int(m.group(1)) for l in a for m in [re.search(r'botfill: round census: (\d+) ZFFActor', l)] if m})
        chk('census logged (44/29 expected after the cops pass; 33/27 before)', bool(cen), 'census lines %s' % (cen or 'none'), warn=True)
        print('  info police vs SWAT at the front / garage + ramp arrival: names above; LOOK at the shots')
    bad = res.count(False)
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
         'Before EACH: tasklist | findstr /i kl2.exe  must show nothing (a zombie with 0 threads is fine). Peers (f0 merged_1108f, fc shop, d0) bench too:',
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
