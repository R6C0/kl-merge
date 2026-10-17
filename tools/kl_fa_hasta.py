#!/usr/bin/env python3
"""
HASTA (Dead Men M11_B 'El Capitolio', chapter 11 alone) as a Fragile Alliance map under Dog Days F07.
Pattern: kl_fa_club.py / kl_fa_bank.py. OFFLINE: nothing here installs anything or starts the game.
Study: re/campaign_fa.md (Havana rows), re/campaign_v2_plan.md, handovers in re/hasta_fa.md.

    python kl_fa_hasta.py build-base [<out>] [--keep-all] [--from <stage>]
        STEP 1. The base the layer is authored on: F07 + M11_B --campaign (kl_maps.one), kl_graft lighten
        (--load trim,slim,fxc), kl_chars wardrobe, kl_chars compact, kl_impact. Order is the MEASURED one of
        re/campaign_fa_tooling.md 3.5 (wardrobe BEFORE compact). After each stage the chunk-table entries,
        the .prm size and the archive are measured and the previous stage's folder is wiped (only notes stay),
        so at most two archives lie on disk. Default <out> = <work>/build/hasta_1017. Result: <out>/base.json
        and <out>/final/ (the compacted base). --keep-all keeps every stage. --from light|ward|compact resumes.
    python kl_fa_hasta.py proof-pair [<out>]
        The compaction proof pair of re/campaign_fa.md (live proof I): fake-fix of x_chunks/retomoto_wardrobe
        and of x_chunks/retomoto_wardrobe_compact -> <out>/proof_pair/{uncompacted,compacted}. The stock
        x_chunks folders are only READ. Load these two in the F01 slot, one after the other (not run here).
    python kl_fa_hasta.py measure <folder>      chunk-table entries, .prm size and member sizes of a built folder
    python kl_fa_hasta.py read [<out>]
        STEP 2. Small READER for the design in re/hasta_fa.md: from the Dead Men M11_B archive (actors, props, switch
        collision) and the step 1 base <out>/final (road, van lane test) it writes <out>/design_read.json: the four
        geometry switches with their collision boxes, the loot props, the squads by group and side, the start floor and
        the van road trial (kl_map_escape.van_plan_points on the base, nothing built). Read-only; no game, no install.

Limits (kl_impact): chunk table 73,728 (CHUNK_TABLE), tools' line 69,632 (CHUNK_SAFE); .prm over 90 MB trips
the allocator at kl2 0x8e5bbd (re/campaign_v2_plan.md; the figure is the plan's, GUESS for the exact edge).
"""
import glob
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_port_check as P

WORK = P.workdir()
OUT = os.path.join(WORK, 'build', 'hasta_1017')
HOST, LEVEL = 'F07', 'M11_B'
PRM_LIMIT_MB = 90.0        # re/campaign_v2_plan.md: over this the allocator trips (0x8e5bbd)
CHUNK_SAFE = 69632         # kl_impact.CHUNK_SAFE
CHUNK_TABLE = 73728
MIN_FREE_GB = 4.0          # a stage is a 0.3 .. 0.5 GB archive; two at once plus sound files


def free_gb(path):
    os.makedirs(path, exist_ok=True)
    return shutil.disk_usage(path).free / 1e9


def measure(folder):
    """-> dict(archive, bytes, prm_mb, chunks, tex_mb, members) of the *_Main.zip in `folder`."""
    zs = glob.glob(os.path.join(folder, '*_Main.zip'))
    if not zs:
        return None
    z = zipfile.ZipFile(zs[0])
    by = {}
    prm = None
    for i in z.infolist():
        e = os.path.splitext(i.filename)[1].lower()
        by[e] = by.get(e, 0) + i.file_size
        if e == '.prm':
            prm = i
    chunks = None
    if prm is not None:
        chunks = struct.unpack_from('<I', z.read(prm)[:8], 4)[0]
    return dict(archive=os.path.basename(zs[0]), bytes=os.path.getsize(zs[0]),
                prm_mb=round(by.get('.prm', 0) / 1e6, 1), chunks=chunks,
                tex_mb=round(by.get('.tex', 0) / 1e6, 1),
                members={k: round(v / 1e6, 1) for k, v in sorted(by.items(), key=lambda kv: -kv[1])[:6]})


def wipe(folder):
    """delete the archive and the sound files beside it, keep the notes (as havana_ward.sh)."""
    for f in glob.glob(os.path.join(folder, '*')):
        if os.path.isfile(f) and not f.lower().endswith(('.json', '.txt', '.log', '.ini')):
            os.remove(f)


def run(name, args, logdir):
    t = time.time()
    log = os.path.join(logdir, name + '.log')
    with open(log, 'w') as fh:
        r = subprocess.run([sys.executable] + args, stdout=fh, stderr=subprocess.STDOUT, cwd=HERE)
    tail = open(log, errors='replace').read().strip().splitlines()[-3:]
    print('  %-8s exit %d  %.0f s  %s' % (name, r.returncode, time.time() - t, ' | '.join(x[:110] for x in tail[-1:])))
    return r.returncode


def build_base(out=OUT, keep_all=False, start='build'):
    out = os.path.abspath(out)
    logs = os.path.join(out, 'logs')
    os.makedirs(logs, exist_ok=True)
    if free_gb(out) < MIN_FREE_GB:
        raise SystemExit('only %.1f GB free under %s (need %.0f): free space first' % (free_gb(out), out, MIN_FREE_GB))
    d_build = os.path.join(out, '%s+%s campaign' % (HOST, LEVEL))
    d_light, d_ward, d_final = (os.path.join(out, n) for n in ('light', 'ward', 'final'))
    d_comp = d_final
    res = {}
    try:
        res = json.load(open(os.path.join(out, 'base.json')))
    except (OSError, ValueError):
        pass
    order = ['build', 'light', 'ward', 'compact']
    go = order.index(start if start in order else 'build')
    prev = None

    def stage(i, name, args, folder, drop_prev=None):
        if order.index(name) < go:
            return True
        if free_gb(out) < MIN_FREE_GB:
            print('STOP: %.1f GB free' % free_gb(out)); return False
        if os.path.isdir(folder) and name != 'build':
            shutil.rmtree(folder)
        rc = run(name, args, logs)
        m = measure(folder)
        res[name] = dict(exit=rc, **(m or {}))
        if m:
            print('           %d chunk-table entries, .prm %.1f MB, archive %.0f MB, members %s' % (
                m['chunks'] or -1, m['prm_mb'], m['bytes'] / 1e6, m['members']))
        json.dump(res, open(os.path.join(out, 'base.json'), 'w'), indent=1)
        if drop_prev and not keep_all and os.path.isdir(drop_prev):
            wipe(drop_prev)
        return m is not None and rc in (0, 1)       # 1 = a problem line (the chunk table before compaction is expected)

    tools = lambda n: os.path.join(HERE, n)
    print('hasta build-base -> %s (%.1f GB free)' % (out, free_gb(out)))
    ok = stage(0, 'build', [tools('kl_maps.py'), 'one', out, HOST, LEVEL, '--campaign', '--keep'], d_build)
    ok = ok and stage(1, 'light', [tools('kl_graft.py'), 'lighten', d_build, d_light, '--load', 'trim,slim,fxc'], d_light, d_build)
    ok = ok and stage(2, 'ward', [tools('kl_chars.py'), 'wardrobe', d_light, d_ward], d_ward, d_light)
    ok = ok and stage(3, 'compact', [tools('kl_chars.py'), 'compact', d_ward, d_comp], d_comp, d_ward)
    if not ok:
        print('stopped: see %s' % logs); return 1
    rc = run('impact', [tools('kl_impact.py'), d_comp], logs)
    res['impact_exit'] = rc
    fin = res['compact']
    res['verdict'] = dict(
        chunks_ok=bool(fin['chunks'] and fin['chunks'] <= CHUNK_SAFE),
        prm_ok=fin['prm_mb'] < PRM_LIMIT_MB, impact_problems_zero=(rc == 0),
        note='a compacted level has never been loaded in the game: run proof-pair first (re/hasta_fa.md)')
    json.dump(res, open(os.path.join(out, 'base.json'), 'w'), indent=1)
    print('RESULT:', json.dumps(res['verdict']))
    print('final base:', d_comp)
    return 0 if all(v for k, v in res['verdict'].items() if k != 'note') else 1


def proof_pair(out=OUT):
    xc = os.path.join(WORK, 'build', 'x_chunks')
    pairs = [('retomoto_wardrobe', 'uncompacted'), ('retomoto_wardrobe_compact', 'compacted')]
    base = os.path.join(os.path.abspath(out), 'proof_pair')
    rc = 0
    for src, dst in pairs:
        s, d = os.path.join(xc, src), os.path.join(base, dst)
        if not os.path.isdir(s):
            print('missing', s); return 2
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        rc |= subprocess.run([sys.executable, os.path.join(HERE, 'kl_fa_bots_dyn.py'), 'fake-fix', s, d], cwd=HERE).returncode
        m = measure(d)
        print(dst, m and (m['chunks'], m['bytes']))
    print('pair ready under', base, '- NOT loaded; load each in the F01 slot (retomoto_wardrobe vs _compact)')
    return rc


DM_ZIP = os.path.join(os.path.dirname(WORK), 'Scenes', 'Locations', 'M11_B', 'M11B_Main.zip')
SWITCHES = [      # (what, entity name in the campaign level, ancestor filter or None)
    ('loot wing door block', 'ColiObj_Obj_Roadblock_01', 'End_Corridor'),
    ('bunker wall', 'SI0100_M11_BarricadeB_01', None),
    ('bunker check block', 'M11B_OYCHECK_BEFORE01', None),
    ('Capitol corner (whole)', 'SO0201_M11_Corner_01', None),
    ('Capitol corner (broken, shown after)', 'SO0201_M11_CornerBroken_01', None),
    ('stair barricade', 'SO0201_M11_BarricadeXX_01', None)]
# the van road found by trial (measured on the step 1 base, GUESS where said in re/hasta_fa.md): in from the WEST end of
# the square's clean straight, out EAST to the shell craters; the wreck 'Vehicles!V_CUB_Chevy_B_Static_00#12' stands in the lane
VAN_TRY = dict(arrive=[(23400, 0, 21800), (24500, 0, 21800)], stop=(25600, 0, 21800), leave=[(29100, 0, 21800), (30600, 0, 21800)],
               wreck='Vehicles!V_CUB_Chevy_B_Static_00#12')


def _anc(sc, k):
    out = []
    while k > 0:
        out.append(sc.names[k]); k = sc.parent[k]
    return out


def read_design(out=OUT):
    import collections
    import kl_map_escape as E
    import kl_hvk
    res = collections.OrderedDict()
    L = E.Level(DM_ZIP)
    sc = L.sc
    G = E.Ground(L)
    ents = L.ents
    # 1. switches: the collision box of each (cm)
    sw = []
    for what, nm, anc in SWITCHES:
        for i, e in enumerate(ents):
            k = i + 1
            if e.name.decode('latin1') != nm or (anc and not any(anc in a for a in _anc(sc, k)[1:])):
                continue
            box = None
            for sh in L.hvk.shapes:
                vs = [struct.unpack_from('<3f', sh.verts, j * sh.vstride) for j in range(len(sh.verts) // sh.vstride)]
                for inst in sh.inst:
                    if kl_hvk.ref(inst) == e.ref:
                        w = G._world(inst, vs)
                        b = [(min(v[a] for v in w), max(v[a] for v in w)) for a in range(3)]
                        box = b if box is None else [(min(x[0], y[0]), max(x[1], y[1])) for x, y in zip(box, b)]
            sw.append(dict(what=what, name=nm, ref=e.ref, place=[round(v) for v in L.place(k)],
                           box_xyz=[[round(a), round(b)] for a, b in box] if box else None))
    res['switches'] = sw
    # 2. loot props
    cases, seen = [], set()
    for i, e in enumerate(ents):
        k = i + 1
        n = e.name.decode('latin1')
        if sc.cls(k) == 'ZGROUP' and 'Shop_Montre' in n and 'Shotactivate' in n.split('!')[-1]:
            p = tuple(round(v) for v in L.place(k))
            if p not in seen:
                seen.add(p); cases.append(dict(name=n.split('!')[0], place=list(p)))
        if sc.cls(k) == 'ZSTDOBJ' and n.endswith('!While_679') and 'Shop_Montre_A_0' in n:
            p = tuple(round(v) for v in L.place(k))
            if p not in seen:
                seen.add(p); cases.append(dict(name=n.split('!')[0], place=list(p)))
    res['display_cases'] = sorted(cases, key=lambda c: (c['place'][0], c['place'][2]))
    res['paintings_table'] = [dict(name=e.name.decode(), place=[round(v) for v in L.place(i + 1)]) for i, e in enumerate(ents)
                              if e.name.decode('latin1').startswith(('PC0200_CUB_Painting', 'PC0200_CUB_Table_A_01'))]
    # 3. actors by squad group
    g = collections.defaultdict(list)
    for i, e in enumerate(ents):
        k = i + 1
        if sc.cls(k) != 'ZFFActor':
            continue
        a = _anc(sc, k)
        key = [x for x in a if x[:1].isdigit() or '!' in x]
        g[(key[-1] if key else a[-1])].append(L.place(k))
    res['squads'] = [dict(group=k, n=len(v), x=[round(min(p[0] for p in v)), round(max(p[0] for p in v))],
                          z=[round(min(p[2] for p in v)), round(max(p[2] for p in v))], y=round(sum(p[1] for p in v) / len(v)))
                     for k, v in sorted(g.items())]
    # 4. start floor (base) and the van trial
    fin = os.path.join(out, 'final')
    if os.path.isfile(os.path.join(fin, 'F01_Main.zip')):
        F = E.Level(fin)
        FG = E.Ground(F)
        res['start_floor'] = [[x, z, [round(h[0]) for h in FG.hits(x, z) if h[1] > 0.7 and h[0] < 900][-1:]]
                              for x, z in ((33900, 29900), (33950, 30387), (34000, 30900))]
        fsc = F.sc
        top = next(i + 1 for i, e in enumerate(F.ents) if e.name.decode('latin1') == VAN_TRY['wreck'])
        clear = [F.ents[j - 1].ref for j in range(top, fsc.end[top])]
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            P = E.van_plan_points(fin, arrive=VAN_TRY['arrive'], stop=VAN_TRY['stop'], leave=VAN_TRY['leave'], heading=None,
                                  at='origin', clear=clear)
        res['van_trial'] = dict(points={k: VAN_TRY[k] for k in ('arrive', 'stop', 'leave')}, wreck_refs=clear, faults=P['faults'],
                                lin=P.get('lin'), lout=P.get('lout'), wait=P.get('wait'), stop=P.get('stop'), end=P.get('end'),
                                cam=P.get('cam'), notes=[n[:200] for n in P['notes']])
    path = os.path.join(out, 'design_read.json')
    json.dump(res, open(path, 'w'), indent=1)
    print('wrote', path, '| switches', len(sw), 'cases', len(cases), 'squads', len(res['squads']),
          '| van faults', len(res.get('van_trial', {}).get('faults', [])))
    return 0


def main():
    a = sys.argv[1:]
    opt = lambda k, dflt=None: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else dflt
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] not in ('--from',))]
    if pos[:1] == ['build-base']:
        sys.exit(build_base(pos[1] if len(pos) > 1 else OUT, '--keep-all' in a, opt('--from', 'build')))
    if pos[:1] == ['proof-pair']:
        sys.exit(proof_pair(pos[1] if len(pos) > 1 else OUT))
    if pos[:1] == ['read']:
        sys.exit(read_design(pos[1] if len(pos) > 1 else OUT))
    if pos[:1] == ['measure'] and len(pos) > 1:
        print(json.dumps(measure(pos[1]), indent=1)); return
    print(__doc__)


if __name__ == '__main__':
    main()
