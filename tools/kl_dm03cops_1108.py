#!/usr/bin/env python3
r"""kl_dm03cops_1108.py - DM03 (Withdrawal, F03 slot) cops pass, 2026-11-08. STAGE ONLY: reads the live DM03 zips, writes C:\kl_build_1024\dm03cops_1108, never installs.

Owner (11-08): "some cops in withdrawal DM03 stay in the cars", "more cops at the back in the garage", "the ramp outside that goes to where the cops wait outside
the garage: make them come through there, more chaos", "no swat cops at the front of the store, just the normal cops".

Five switchable parts (--parts carexit,garage,ramp,frontcops,allpolice; default all):
  carexit    the 4 VehicleExitBehaviourRout controllers kl_convert dropped (kl_rtp has no kind for field 2) put back from M03_FA_A (kl_map_ai.cars restore=True).
             PROVEN cause: live DM03 has the 4 VehicleExitBehaviour nodes (EscSquad, ArrivingCops_Squad_01 / _02, ParkingLotSWAT_01) WITHOUT their controller, so nothing takes
             a seated cop out of his car. GUESS: that DD's ZVehicleExitBehaviourRout then runs (no stock level stores it; DM01 carries it live since 10-25, no load crash).
  garage     KL_Garage!Back: 6 normal police pre-placed (ZSquadScript f3 = 1) on nav cells at the back of the garage, Defend-only (they stay and shoot what comes).
  ramp       KL_Ramp!Wave: 5 normal police pre-placed on the outside ramp, Defend there; KL_Ramp!Clock\Go2 (RAMP_DELAY s after the round start) starts a Hunt rout whose SearchBox
             sits in the garage: they come down the ramp and through the garage. GUESS: the ramp is the Dead Men 'Ramp_01' at (-3500, 200, -2235) beside the SWAT lot (the walk from
             the lot cells to the garage dock is a mesh path of 7.9 m x 10, measured); GUESS: a Hunt rout started while a Defend rout runs replaces it.
  frontcops  the 3 ParkingLotSWAT_01 men and the 2 ArrivingCops_Squad_02 men (front street) get the normal police form: ZFFActor model 59361 (entity + field 4), anmcol #Police,
             weapon SMG_Type79 / Shotgun_Hawk_Bullpup, ZSoldier controller of the BankMain police (eGuard, 125 hp). GUESS: the Police animation set works for the squads' rout
             animations (BankMain police use it with Defend / Hunt, so likely). ArrivingCops_Squad_01 and EscSquad (arrive off-mesh, from the back) are NOT touched.
  allpolice  the remaining Army-form (model 59891) men of KL_Cover!Squad_01..03 (6 cops, z -7300..-9990 = the garage / back area) get the same police form as frontcops, so the
             garage is not a mix of Army and police. EscSquad and ArrivingCops_Squad_01 stay Army (they arrive off-mesh from the back with their own rout animations; their model
             swap is NOT proven safe). Weapons: cop_#01 SMG_Type79, cop_#02 Shotgun_Hawk_Bullpup. Same GUESS as frontcops (Police animation set works for these squads' routs).
One new squad = 1 squad script; budget measured by census (live 33 actors / 27 squads, engine-proven cap 99 / 55).

  python tools/kl_dm03cops_1108.py stage [--parts a,b] [--in-dir <DM03 dir>] [--out <dir>]
Refuses unless the live plain zip is LIVE_ZIP_MD5 and the bots zip LIVE_BOTS_MD5. BOTH zips are changed; F03_Main.bots.base.md5 = md5 of the staged plain zip.
"""
import collections, hashlib, json, math, os, shutil, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_octree as O
import kl_old_waves as KOW
import kl_prpjoin as J
import kl_dm02_assault_1025 as AS
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM03')
OUT = r'C:\kl_build_1024\dm03cops_1108'
TAG = '.before-dm03cops_1108'
LIVE_ZIP_MD5 = '802fd1f7c644f6baa2be43b63f7e7270'
LIVE_BOTS_MD5 = '19adc63d632c27c83197223887c1ff69'
FILES = ('F03_Main.zip', 'F03_Main.bots.zip', 'F03_Main.bots.base.md5')
PARTS = ('carexit', 'garage', 'ramp', 'frontcops', 'allpolice')
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55
LEVEL = 'M03_FA_A'
CLOCK, GARAGE, RAMP = 'KL_Squads!Clock', 'KL_Garage!Back', 'KL_Ramp!Wave'
GO_DELAY, RAMP_DELAY = 0.1, 45.0                 # GUESS: 45 s after the round start the ramp wave comes down (the crew is in the bank by then)
# nav cells (measured 2026-11-08 on the live zip's walk mesh: home part, clearance >= 70, spaced >= 220 / 120 cm; re-verified at build time)
GARAGE_CELLS = [(480, 240, -6640), (480, 240, -6400), (480, 224, -6160), (660, 206, -5980), (720, 232, -6340), (900, 240, -6640)]
RAMP_CELLS = [(-3260, 220, -2260), (-3200, 220, -2140), (-3560, 220, -2020), (-3200, 220, -2020), (-3080, 220, -2020)]
DOCK_BOX = ((0.0, 200.0, -5600.0), (500.0, 200.0, 700.0))     # the Hunt SearchBox: centre, size (the loading dock / garage floor)
POLICE_MEN = (7120, 7122, 6808, 7029)            # live node ids of the BankMain police actors (SMG_Type79, M9, SigSauer226, SMG_Type79): the clone templates
POLICE_TMPL = 7029                               # ZFFActor + ZSoldier values copied onto the SWAT men (SMG_Type79)
FRONT_MEN = {7036: 'SMG', 7038: 'SMG', 7045: 'SHOTGUN', 6953: 'SMG', 6955: 'SHOTGUN'}      # lot SWAT x3, ArrivingCops_Squad_02 x2
SHOTGUN_TMPL = 7113                              # LoadingDock guard (model 60016): only its weapon path is used
FACE = (0.0, 1.0)
md5 = lambda b: hashlib.md5(b).hexdigest()


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def one(sc, name):
    hit = sc.resolve(R + name)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (name, len(hit)))
    return hit[0]


# ---------------------------------------------------------------- part carexit (prp only)
def _check_inproc(path):
    """Run in a FRESH process only (python kl_dm03cops_1108.py _check <zip>): kl_map_ai.cars(restore=True) registers the exit-rout field kinds in this process, after which
    J.check reports none of them. Prints one JSON line: round trip, misfits (path, text), unresolved path count."""
    _o, f, e, sc2, _l, _h = kl_graft.open_built(path)
    d2, bad, p, _ = J.check(sc2, log=lambda *_a: None)
    print(json.dumps(dict(rt=d2 == f[e['.prp']], bad=[(sc2.path[b[0]], str(b[2])) for b in bad], unres=len(p))))


def check_zip(path, allowed, n_unres0, log, what, exact=False):
    """J.check the written zip in a fresh process: every misfit must be a 'ZVehicleExitBehaviourRout field 2 expected None' on one of the `allowed` restored exit routs
    (exact: all of them must be reported), no new unresolved path. Deletes `path` and raises otherwise. kl_rtp has no kind for field 2, so the restored routs show as
    misfits exactly as on live DM01 (by design); measured: 0 right after carexit's own serialise, 4 once the zip is re-read."""
    import subprocess
    r = subprocess.run([sys.executable, os.path.abspath(__file__), '_check', path], capture_output=True, text=True)
    if r.returncode:
        os.remove(path); raise ValueError('%s: misfit check process failed: %s' % (what, r.stderr[-300:]))
    j = json.loads(r.stdout.strip().splitlines()[-1])
    got = {p for p, t in j['bad'] if 'ZVehicleExitBehaviourRout' in t and 'expected None' in t}
    other = [(p, t[:80]) for p, t in j['bad'] if p not in allowed or 'ZVehicleExitBehaviourRout' not in t or 'expected None' not in t]
    if not j['rt'] or other or j['unres'] > n_unres0 or (exact and got != allowed):
        os.remove(path)
        raise ValueError('%s: misfit guard: unexpected misfits %s, unresolved %d (before %d), reported exit routs %d of %d allowed, round trip %s'
                         % (what, other[:5], j['unres'], n_unres0, len(got), len(allowed), j['rt']))
    log('  %s: J.check %d misfits = %d allowed restored VehicleExitBehaviour routs (field 2 expected None), 0 other, %d unresolved paths' % (what, len(j['bad']), len(got), j['unres']))
    return len(j['bad'])


def carexit(src, dst, log):
    import kl_map_ai as MA
    order, files, ext, sc, _l, _h = kl_graft.open_built(src)
    d0, bad0, p0, _ = J.check(sc, log=lambda *_a: None)      # BEFORE kl_map_ai touches the schema (see _check_inproc)
    if d0 != files[ext['.prp']]:
        raise ValueError('the .prp does not re-serialise byte for byte')
    lost = MA.lost_exits(sc, LEVEL)
    if not lost:
        shutil.copyfile(src, dst); return {'restored': []}
    if bad0 or p0:
        raise ValueError('live scene already has %d misfits / %d unresolved paths' % (len(bad0), len(p0)))
    MA.cars(sc, LEVEL, restore=True, log=lambda *_a: None)
    if MA.faults(sc) or MA.lost_exits(sc, LEVEL):
        raise ValueError('carexit: reference lists at fault or exit routs still missing')
    d = sc.p.serialize()
    new = dict(files)
    new[ext['.prp']] = d
    kl_graft.write_zip(dst, [(n, new[n]) for n in order])
    # Misfit guard (check_zip, fresh process): allowed = only the restored routs; any other misfit or unresolved path raises.
    check_zip(dst, {sc.path[x[0]] for x in lost}, 0, log, 'carexit')
    log('  carexit: %d exit routs restored (%s), .prp %d -> %d bytes' % (len(lost), ', '.join(sc.names[x[0]] for x in lost), len(files[ext['.prp']]), len(d)))
    return {'restored': [sc.path[x[0]] for x in lost], 'prp_bytes': [len(files[ext['.prp']]), len(d)]}


# ---------------------------------------------------------------- part frontcops (in place: props + ZSoldier + entity model)
def front_edit(B, log, men=None, label='frontcops'):
    sc = B.sc
    tp = kl_fa.node_values(sc, POLICE_TMPL)
    zs_t = [(nm, body) for nm, body in sc.nodes[POLICE_TMPL]['ctrls'] if sc.p.key(nm) == 'ZSoldier']
    if len(zs_t) != 1 or tp[4] != 59361 or not tp[10].endswith('#Police'):
        raise ValueError('police template %d is not a model 59361 / #Police actor' % POLICE_TMPL)
    shot = kl_fa.node_values(sc, SHOTGUN_TMPL)[20]
    if not shot.endswith('Shotgun_Hawk_Bullpup'):
        raise ValueError('shotgun template: %s' % shot)
    model = tp[4]
    done = []
    for k, w in (FRONT_MEN if men is None else men).items():
        if sc.cls(k) != 'ZFFActor' or kl_fa.node_values(sc, k)[4] != 59891:
            raise ValueError('node %d is not an Army ZFFActor (model 59891)' % k)
        us0 = [list(u) for u in kl_fa.units(sc.nodes[k]['props'][1:-1])]
        ut = [list(u) for u in kl_fa.units(sc.nodes[POLICE_TMPL]['props'][1:-1])]
        for f in (4, 10, 20):
            us0[f] = [(t[0], t[1]) for t in ut[f]]
        if w == 'SHOTGUN':
            us0[20] = [kl_fa._str(sc, shot)]
        obj = sc.nodes[k]['props']
        sc.nodes[k]['props'] = [obj[0]] + [t for u in us0 for t in u] + [obj[-1]]
        for i, (nm, body) in enumerate(sc.nodes[k]['ctrls']):
            if sc.p.key(nm) == 'ZSoldier':
                sc.nodes[k]['ctrls'][i] = (nm, list(zs_t[0][1]))
        B.ents[k - 1].model = model
        done.append(sc.path[k][len(R):])
    log('  %s: %d men -> police form (model %d, #Police, eGuard 125 hp)' % (label, len(done), model))
    return done


# ---------------------------------------------------------------- parts garage / ramp (new squads)
def make_nodes(B, parts):
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    sqtop = one(sc, 'AI_Enemies!BankMainSquad_02')
    dform = node(R + KB.SQUAD + 'Squad#02' + BS + '010_DefendBehaviour_way_a')
    pform = dform + 1
    hform = node(R + 'AI_Enemies!ArrivingCops_Squad_02' + BS + 'HuntBehaviour')
    bform = node(R + 'AI_Enemies!ArrivingCops_Squad_02' + BS + 'HuntBehaviour' + BS + 'SearchBox')
    if sc.names[pform] != 'Pos#01' or sc.parent[pform] != dform:
        raise ValueError('defend form: node %d is not the Pos#01 of %d' % (pform, dform))
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), CLOCK)          # a group (dm01squads does the same)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    tops, starts = [clock], []

    def squad(name, cells, men, hunt_box=None):
        top = FED.clone_built(M, B, sqtop, name)
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        M.set(top, 'ZSquadScript', {3: 1, **{j: [] for j in range(4, 19)}})
        me = R + name
        d = top.add(FED.clone_built(M, B, dform, '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, cell in enumerate(cells):
            pp = d.add(FED.clone_built(M, B, pform, 'Pos#%02d' % (j + 1)))
            M.place(pp, cell)
            refs.append(me + BS + '10_Defend' + BS + 'Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        short = name.split('!')[-1]
        for j, (cell, a) in enumerate(zip(cells, men)):
            gr = top.add(FED.clone_built(M, B, sc.parent[a], 'M_%s_%02d' % (short, j + 1)))
            M.place(gr, cell, KB.rot9(*FACE))
            gr.add(FED.clone_built(M, B, a))
        out = [me + BS + '10_Defend']
        if hunt_box:
            h = top.add(FED.clone_built(M, B, hform, 'HuntBehaviour'))
            M.place(h, (0.0, 0.0, 0.0))
            box = h.add(FED.clone_built(M, B, bform, 'SearchBox'))
            M.place(box, hunt_box[0])
            M.set(box, None, {'ZBoxPrimitive[%d]' % a: float(hunt_box[1][a]) for a in range(3)})
            M.set(h, 'HuntBehaviourRout', {0: me + BS + 'HuntBehaviour' + BS + 'SearchBox', 1: 1, 2: [], 3: 1, 4: 0})
            out.append(me + BS + 'HuntBehaviour')
        tops.append(top)
        return out

    go_paths = []
    n_men = 0
    if 'garage' in parts:
        go_paths += squad(GARAGE, [tuple(map(float, c)) for c in GARAGE_CELLS], [POLICE_MEN[j % len(POLICE_MEN)] for j in range(len(GARAGE_CELLS))])[:1]
        n_men += len(GARAGE_CELLS)
    go2 = None
    if 'ramp' in parts:
        o = squad(RAMP, [tuple(map(float, c)) for c in RAMP_CELLS], [POLICE_MEN[(j + 1) % len(POLICE_MEN)] for j in range(len(RAMP_CELLS))], DOCK_BOX)
        go_paths.append(o[0]); go2 = o[1]
        n_men += len(RAMP_CELLS)
    go = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), 'Go'))
    M.place(go, (0.0, 0.0, 0.0))
    M.set(go, 'TriggerDelay2', {0: float(GO_DELAY), 4: go_paths})
    gos = [R + CLOCK + BS + 'Go']
    if go2:
        g2 = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), 'Go2'))
        M.place(g2, (0.0, 0.0, 0.0))
        M.set(g2, 'TriggerDelay2', {0: float(RAMP_DELAY), 4: [go2]})
        gos.append(R + CLOCK + BS + 'Go2')
    return M, tops, gos, n_men


def rebuild(src, dst, parts, log):
    """frontcops + garage / ramp: one pass over a zip (kl_dm01squads_1025.squads pattern, nothing removed)."""
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + CLOCK):
        raise ValueError('%s already holds %s' % (src, CLOCK))
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    a0, s0 = AS.census(sc)
    nav = KB.Nav(A.nav, links=True)
    home = KB.stations(B, nav)['home']
    rep = collections.OrderedDict(census_before=[a0, s0])
    squads = [p for p in ('garage', 'ramp') if p in parts]
    for nm, cells in (('garage', GARAGE_CELLS), ('ramp', RAMP_CELLS), ('ramp', [DOCK_BOX[0]])):
        if nm not in parts:
            continue
        for c in cells:
            a = nav.at(c[0], c[1], c[2], dy=80.0)
            if a is None or nav.part[a[0]] != home or (nm != 'ramp' or c in RAMP_CELLS) and nav.clearance(c[0], c[1], c[2], limit=200.0) < 60.0:
                raise ValueError('%s cell %s is not a home-part nav cell with clearance' % (nm, (c,)))
    if 'ramp' in parts:
        ra, rb = RAMP_CELLS[0], DOCK_BOX[0]
        r = nav.path(tuple(map(float, ra)) + (nav.at(ra[0], ra[1], ra[2], dy=80.0)[0],), tuple(map(float, rb)) + (nav.at(rb[0], rb[1], rb[2], dy=80.0)[0],))
        if r is None:
            raise ValueError('no mesh walk from the ramp to the garage dock')
        rep['ramp_walk_cm'] = round(r[1])
    if 'frontcops' in parts:
        rep['frontcops'] = front_edit(B, log)
    if 'allpolice' in parts:
        men = {}
        for k in range(1, len(sc.nodes)):
            pa = sc.path[k]
            if sc.cls(k) == 'ZFFActor' and pa.startswith(R + 'KL_Cover!Squad_') and kl_fa.node_values(sc, k)[4] == 59891 and k not in FRONT_MEN:
                z = struct.unpack('<4f', B.ents[k - 1].parent.trans)[2]      # the cop_# group's world position: x, y(up), z, w (the Ground actor itself sits at 0)
                if not -10000.0 <= z <= -7290.0:        # the garage / back band; a cop outside it stays Army
                    continue
                men[k] = 'SHOTGUN' if pa.split(BS)[-2].endswith('#02') else 'SMG'
        if len(men) != 6:
            raise ValueError('allpolice: expected the 6 KL_Cover cops, found %d' % len(men))
        rep['allpolice'] = front_edit(B, log, men, 'allpolice')
    tops, n_men, gos = [], 0, []
    if squads:
        M, tops, gos, n_men = make_nodes(B, parts)
        if a0 + n_men > ENGINE_ACTORS or s0 + len(squads) > ENGINE_SQUADS:
            raise ValueError('budget: %d / %d' % (a0 + n_men, s0 + len(squads) + 1))
        q, order = M.scene(tops)
        picks = [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()]
    else:
        order = []
        picks = [(sc, t) for t in sc.tops()]
    Jn = J.join(sc, picks, 'dm03cops')
    if gos:
        km = Jn.resolve(KOW.MONITOR)[0]
        ci = AU.ctrl_of(Jn, km, 'AIMonitor')
        have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
        kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + gos))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if fa != a0 + n_men or fs != s0 + len(squads) or fa > ENGINE_ACTORS or fs > ENGINE_SQUADS:
        raise ValueError('census %d / %d -> %d / %d' % (a0, s0, fa, fs))
    rep['census_after'] = [fa, fs]
    log('  census %d / %d -> %d / %d (cap %d / %d)' % (a0, s0, fa, fs, ENGINE_ACTORS, ENGINE_SQUADS))
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    if not tops:
        gms, buf = A.write()
        new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
    else:
        slot0 = A.slots()
        nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
        made = {}

        def ent(n, parent):
            nonlocal nxt
            e = kl_scene.Entity()
            e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
            e.rot, e.trans, e.raw, e.aux, e.links, e.lkey = n.rot, n.trans, None, n.aux, n.links, 0
            e.ref = nxt
            nxt += 1
            e.parent = parent
            e.kids = []
            (parent.kids if parent else A.roots).append(e)
            made[id(n)] = e
            for c in n.kids:
                ent(c, e)
        for t in tops:
            ent(t, None)
        A.ref_slots = max(A.ref_slots, nxt)
        faults = A.check()
        if faults:
            raise ValueError('kl_scene.check: %s' % faults[:3])
        allents = list(A.entities())
        if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
            raise ValueError('the new .gms and .prp disagree on the entities')
        gms, buf = A.write()
        slot1 = A.slots()
        ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
        ids[1] = 1
        octn, rmin, rmcn = O.remap_ids(octx, ids, set()), O.remap_ids(rmi, ids, set()), O.remap_ids(rmc, ids, set())
        items = []
        for t in tops:
            pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)] + [p.pos for k in t.kids for p in k.kids if p.pos and p.pos != (0.0, 0.0, 0.0)]
            lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
            hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
            items.append((slot1[made[id(t)]] + 2, lo, hi))
        r3 = octn.rooms[0][3]
        if r3 is None:
            raise ValueError('the root has no tree 3')
        octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
        octn.rooms[0][3].check()
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        repointed = 0
        if move:
            prm = bytearray(B['.prm'])
            tt, nn = struct.unpack_from('<II', prm, 0)
            for i in range(1, nn):
                off, size = struct.unpack_from('<II', prm, tt + 16 * i)
                if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', prm, off + 0x1c, move[v]); repointed += 1
            new[B.ext['.prm']] = bytes(prm)
        post = KB.room_sets_check(A, octn, rmin, rmcn)
        if post != pre:
            raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
        new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
        new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
        rep.update(entities_added=len(order), slot_ids_moved=sum(1 for a, b in ids.items() if a != b), prm_roots_repointed=repointed, go=gos)
    work = tempfile.mkdtemp(prefix='dm03cops_')
    try:
        zp = kl_graft.write_zip(os.path.join(work, 'F03_Main.zip'), [(n, new[n]) for n in B.order])
        import kl_fa_bank
        rep['sealed'] = kl_fa_bank.seal(work, log=lambda *_: None)
        probs = kl_fa_bank.reverify(work, log=lambda *_: None)
        if probs:
            log('  reverify notes: %s' % probs[:5])
        rep['reverify'] = probs[:5]
        shutil.copyfile(zp, dst)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rep['members_changed'] = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    log('  written %s: members changed: %s' % (dst, ' '.join(rep['members_changed'])))
    return rep


def apply(src, dst, parts, log=print):
    rep = {}
    cur = src
    tmp = tempfile.mkdtemp(prefix='dm03c1_')
    try:
        if 'carexit' in parts:
            mid = os.path.join(tmp, os.path.basename(dst))
            rep['carexit'] = carexit(cur, mid, log)
            cur = mid
        if any(p in parts for p in ('garage', 'ramp', 'frontcops', 'allpolice')):
            rep['rebuild'] = rebuild(cur, dst, parts, log)
        else:
            shutil.copyfile(cur, dst)
        if 'carexit' in parts:
            # the final file: exactly the 4 restored routs are reported once a rebuild pass re-joined the scene (measured), none otherwise
            rep['final_check'] = check_zip(dst, set(rep['carexit']['restored']), 0, log, 'final', exact=any(p in parts for p in ('garage', 'ramp', 'frontcops', 'allpolice')))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rep


INSTALL = r'''"""Installs / undoes the DM03 COPS PASS 1108 (tools/kl_dm03cops_1108.py) on the live DM03 files (parts: @PARTS@).

  python install.py            install (originals -> <name>.before-dm03cops_1108 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Every live md5 is pinned BEFORE anything is written (all or nothing); nothing is written while kl2.exe runs. Never touches KL_PortBackup."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM03', '@TAG@'
FILES = @FILES@


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-26s live %s' % (n, cur))
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another pass changed it: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (1 << 30)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + 1024 MB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %s %s' % ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def stage(parts, in_dir=MAPDIR, out=OUT, log=print):
    zp, bp = os.path.join(in_dir, FILES[0]), os.path.join(in_dir, FILES[1])
    live = {n: fmd5(os.path.join(in_dir, n)) for n in FILES[:2]}
    if live[FILES[0]] != LIVE_ZIP_MD5:
        raise ValueError('REFUSED: the live DM03 plain zip is %s, not the pinned %s' % (live[FILES[0]], LIVE_ZIP_MD5))
    if live[FILES[1]] != LIVE_BOTS_MD5:
        raise ValueError('REFUSED: the live DM03 bots zip is %s, not the pinned %s' % (live[FILES[1]], LIVE_BOTS_MD5))
    work = os.path.join(out, 'work')
    keep = os.path.isdir(work)
    tmp = tempfile.mkdtemp(prefix='dm03out_')
    reps = {}
    try:
        for name, src in ((FILES[0], zp), (FILES[1], bp)):
            log('== %s' % name)
            reps[name] = apply(src, os.path.join(tmp, name), parts, log)
        plain = fmd5(os.path.join(tmp, FILES[0]))
        os.makedirs(out, exist_ok=True)
        for n in os.listdir(out):
            if n != 'work':
                p = os.path.join(out, n)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        for name in FILES[:2]:
            shutil.copyfile(os.path.join(tmp, name), os.path.join(out, name))
        open(os.path.join(out, FILES[2]), 'w', newline='\n').write(plain + '\n')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    old_base = open(os.path.join(in_dir, FILES[2])).read().strip()
    files = [(FILES[0], live[FILES[0]], fmd5(os.path.join(out, FILES[0]))), (FILES[1], live[FILES[1]], fmd5(os.path.join(out, FILES[1]))),
             (FILES[2], fmd5(os.path.join(in_dir, FILES[2])), fmd5(os.path.join(out, FILES[2])))]
    if old_base != live[FILES[0]]:
        raise ValueError('live bots.base.md5 (%s) is not the live plain zip md5' % old_base)
    src = INSTALL.replace('@PARTS@', ','.join(parts)).replace('@GAME@', GAME).replace('@TAG@', TAG).replace('@FILES@', repr(files))
    open(os.path.join(out, 'install.py'), 'w', newline='\n').write(src)
    for nm, arg in (('INSTALL DM03 cops 1108.bat', ''), ('UNDO DM03 cops 1108.bat', ' --undo')):
        open(os.path.join(out, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    ini = os.path.join(GAME, 'KLHook.ini')
    cover = [ln.rstrip('\r\n') for ln in open(ini, encoding='latin1') if ln.split('=')[0].strip() in ('AssertSoft', 'ClientBuild', 'ClientBuildHost', 'ClientBuildMaps', 'ClientRewrite', 'ClientRingSync')]
    open(os.path.join(out, 'bench_cover_lines.txt'), 'w').write('\n'.join(cover) + '\n')
    json.dump(dict(parts=parts, files=files, reports=reps, cover_lines=cover), open(os.path.join(out, 'build_report.json'), 'w'), indent=1, default=str)
    return files


def main(a):
    if a and a[0] == '_check':
        _check_inproc(a[1]); return 0
    if not a or a[0] != 'stage':
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    parts = tuple(p for p in opt('--parts', ','.join(PARTS)).split(',') if p)
    bad = [p for p in parts if p not in PARTS]
    if bad:
        raise SystemExit('unknown part %s (parts: %s)' % (bad, ','.join(PARTS)))
    for n, o, w in stage(parts, opt('--in-dir', MAPDIR), opt('--out', OUT)):
        print('%-26s %s -> %s' % (n, o, w))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
