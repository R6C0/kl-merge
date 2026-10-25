"""kl_dm_overhaul_1025.py - the DM02 mall overhaul recipe applied to the other Dead Men maps (owner ask 2026-10-25; plan: re/dm_overhaul_1025.md).

    python tools/kl_dm_overhaul_1025.py list
    python tools/kl_dm_overhaul_1025.py build  <MAP> <live zip> <out zip>
    python tools/kl_dm_overhaul_1025.py stage  <MAP> <live zip> <stage folder> [--rehearse <scratch>]

Chain (all of it is reused from the mall tool, kl_dm02_mall_1025): kick doors + wall extinguishers (kl_interact_graft, new top KL_Interact!2) ->
fuel cans (kl_dm01b_gas_1025, new top KL_Gas!2) -> police cars + SWAT cells along a plan polyline (kl_dm02_mall_1025.cars(plan=)) -> sound references
re-pointed by name for the nodes this build added.  Every new node sits in a NEW top group; nothing existing is deleted, the AIMonitor start list
gets one entry (the cars' Backstop timer).  The stage is pinned on the md5 of the live zip it was built from.
Installer: md5-chained INSTALL / UNDO .bat + .ps1 (the gas installer text, retagged), -Rehearsal -Game and -DryRun, backup tag .before-1025overhaul.
Never installs, never launches the game; reads the live zip only.
"""
import collections, hashlib, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_interact_graft as IG
import kl_dm01b_gas_1025 as GS
import kl_dm02_mall_1025 as MALL

TAG = '.before-1025overhaul'                # default; a map's SPECS entry may carry its own 'tag' (DM03A: .before-1025overhaul2)
BS = chr(92)
IG_TOP, GS_TOP = 'KL_Interact!2', 'KL_Gas!2'

# DM06 car lanes (x, z, y): every 125 cm on the collision terrain, ground y smoothed 1-2-1 (verifier scan 2026-10-25, car column free of collision, step <= 16 per 125)
LANES06 = {'A': [(3125.0, -8000.0, 143.0), (3000.0, -8000.0, 159.0), (2875.0, -8000.0, 172.0), (2750.0, -8000.0, 178.0), (2625.0, -8000.0, 180.0), (2500.0, -8000.0, 181.0), (2375.0, -8000.0, 180.0), (2250.0, -8000.0, 180.0), (2125.0, -8000.0, 180.0), (2000.0, -8000.0, 180.0), (1875.0, -8000.0, 179.0), (1750.0, -8000.0, 179.0), (1625.0, -8000.0, 179.0), (1500.0, -8000.0, 180.0), (1375.0, -8000.0, 180.0), (1250.0, -8000.0, 180.0), (1125.0, -8000.0, 179.0), (1000.0, -8000.0, 179.0), (875.0, -8000.0, 179.0)], 'B': [(-2875.0, -7875.0, 180.0), (-2750.0, -7875.0, 186.0), (-2625.0, -7875.0, 191.0), (-2500.0, -7875.0, 192.0), (-2375.0, -7875.0, 190.0), (-2250.0, -7875.0, 186.0), (-2125.0, -7875.0, 182.0), (-2000.0, -7875.0, 183.0), (-1875.0, -7875.0, 182.0), (-1750.0, -7875.0, 173.0), (-1625.0, -7875.0, 166.0)], 'C': [(-2375.0, -1125.0, 167.0), (-2250.0, -1250.0, 165.0), (-2125.0, -1375.0, 165.0), (-2000.0, -1500.0, 169.0), (-1875.0, -1625.0, 174.0), (-1750.0, -1750.0, 172.0), (-1625.0, -1875.0, 166.0), (-1500.0, -2000.0, 159.0)]}

# Per map.  doors: kl_interact_graft door specs (int = a leaf node of the build; every one measured with nav on BOTH sides of the leaf, main part).
# ext: spots_near targets (x, z, floor y) for wall extinguishers (snapped to the nearest wall edge).  fuel: anchors (x, z, floor y).
SPECS = {
    'DM01B': dict(
        slot='F03', file='F03_Main.zip', title='Hot Coffee II',
        # doors: leaf nodes 7209 (south office, hinge 2217,62,16512), 7165 (1640,462,17290), 7268 (1915,862,17205).
        # Skipped on purpose: 7210 (named by the garage tear-gas lists), 1373/7208/8274/8279/8280/8831/8840 have no nav on one side (a dead door); 8276/8277/8278 stand beside doors that already exist.
        doors=[7209, 7165, 7268],
        ext=[(2600.0, 16700.0, 60.0), (2800.0, 17100.0, 60.0), (1500.0, 19800.0, 60.0)],
        fuel=[(2500.0, 18600.0, 60.0), (2300.0, 15900.0, 60.0)],
        # cars: a three-car convoy on the street band z 8900 (nav clearance >= 150 from x -7000 to 1500, measured), coming from the west.
        # GUESS: the start points beyond x -7000 are checked by cars() (every 6th key must be on the main part with clearance 100).
        cars=dict(
            paths={12579: [(-6600.0, 8900.0), (1500.0, 8900.0)], 12754: [(-7100.0, 8900.0), (1000.0, 8900.0)], 12929: [(-7600.0, 8900.0), (500.0, 8900.0)]},
            cells={1: [(2000.0, 0.0, 8900.0), (2400.0, 0.0, 8900.0)], 2: [(-150.0, 0.0, 8900.0), (-600.0, 0.0, 8900.0)], 3: [(-1000.0, 0.0, 8900.0), (2800.0, 0.0, 8900.0)]},
            wave3='AI_Players!Enemies!03_Garage!03_Squad_02_OnStreet_Wave_03',   # DM01B has no OldWaves!Wave_3: its own street wave (3 police actors) is the clone template
            backstop=25.0,            # GUESS as the mall: ~25 s after the round start
            anm_col='Army',           # the police actors of the map hold the 'Army' collection token (the prp lists no Mercenary_04)
            caps=(99, 64)),           # GUESS: DM01B is already at 58 squads (past the engine-proven 55); only 3 more, actors 91 + 6 = 97 <= 99
    ),
    'DM03A': dict(
        slot='F07', file='F07_Main.zip', title='The vault', tag='.before-1025overhaul2',
        # NO new kick doors: door_hosts finds 18 leaves, 16 of them on nav part 1 (the upper-floor island, no spawn on it = dead door) and the 2 on the
        # main part (6516 at -828,-6259 / 6770 at -701,-5426) stand beside the 5 doors KL_Interact!1 already holds (151..218 cm: the other leaf of the same double door).
        doors=[],
        # ext: three wall spots on the main part (spot_near snapped, measured 2026-10-25): west lobby (-1036, 240, -4710), start side (-236, 200, -3387), far south (329, 240, -7859).
        ext=[(-1000.0, -4300.0, 200.0), (-500.0, -3500.0, 200.0), (0.0, -8000.0, 240.0)],
        # fuel: anchors snapped to open floor by snap() (measured: -350,-7010 and -960,-4900; GUESS that these are good fights spots); the 3 stock cans of KL_Gas!1 stand at (301,-5420) (800,-5390) (700,-5090).
        fuel=[(-350.0, -6950.0, 240.0), (-1000.0, -4900.0, 240.0)],
        # NO cars / SWAT: census 106 actors / 54 squads already past the proven 99 / 55 (re/dm_overhaul_1025.md 1.2), a police car's cell costs actors.
        cars=None,
    ),
    # ---- DM06 A Walk in the Park (F04 slot), 2026-10-25.  The park is open ground: no roads, and kl_interact_graft.door_hosts finds 0 leaves -> no kick doors.
    # Cars drive on the open grass fields the walk mesh shows (GUESS: the ground is drivable; the cars are animated bodies, no real driving).  The SWAT are
    # the map's own JPN_DrugSquad actors (DM06 has no police: the FA 'police' are the drug gangs; anmcol Mercenary_04, read from ZLNKOBJ[2] 2026-10-25).
    # The floor here is ~220..290, not 0: the car lanes carry y (plan 'y', kl_dm02_mall_1025._lane_y).  Measured with C:/kl_build_1024/overhaul_1025a/lanes06.py.
    'DM06': dict(
        slot='F04', file='F04_Main.zip', title='A Walk in the Park', tag='.before-1025overhaul2',
        # 2026-10-25 independent check (collision .HVK via kl_route) refuted the first build's guesses: the walk mesh floats 20..60 above the collision terrain, the first
        # extinguisher spots (nav wall edges) were open air or bushes/trees, and the south-field lanes at constant y crossed a 150 cm hill.  So here: ext = explicit spots (x, FLOOR y, z, 0, zdir)
        # found on real wall collision (pavilion, tea house, scaffold: SO0100 refs, a wall >= 160 cm long 20..40 cm from the spot, free floor before it); fuel cans stand on the collision floor
        # (fuel_ground); the car lanes carry the terrain height per point and were scanned for collision in the car column.  The park has no roads and no door leaves -> no kick doors.
        doors=[],
        ext_spots=[(880.0, 625.0, 2152.0, 0.0, (1.0, 0.0)), (880.0, 625.0, 2552.0, 0.0, (1.0, 0.0)), (-2500.0, 175.0, -1880.0, 0.0, (1.0, 0.0)),
                   (-2260.0, 173.0, -2080.0, 0.0, (0.0, 1.0)), (1040.0, 166.0, 3720.0, 0.0, (1.0, 0.0)), (1160.0, 181.0, 3440.0, 0.0, (0.0, 1.0))],
        ext=[],
        fuel=[(750.0, -8750.0, 220.0), (-1000.0, -4500.0, 220.0), (2500.0, -3500.0, 220.0)], fuel_ground=True,
        # cars: two on the south field, east and west of the escape point (-1040,-6721), and one mid-route; lanes follow the collision terrain (path points (x, z, y)).
        cars=dict(
            nav_dy=125.0,
            paths={12579: LANES06['A'], 12754: LANES06['B'], 12929: LANES06['C']},
            cells={1: [(1125.0, 236.0, -8375.0), (750.0, 225.0, -8500.0)], 2: [(-1875.0, 220.0, -8250.0), (-1875.0, 220.0, -7500.0)],
                   3: [(-1750.0, 220.0, -2375.0), (-1000.0, 220.0, -2000.0)]},
            wave3='AI_Enemies!JPN_DrugSquad_Island_01',   # 2 Mercenary_04 actors in 2 groups + a ZSquadScript: the clone template (GUESS: the map's own drug-gang squad can be the SWAT)
            backstop=60.0,            # GUESS: the crew needs ~60 s from the bridge end to the south; the lanes take ~10 s
            anm_col='Mercenary_04',
            caps=(99, 64)),           # census 21 / 18 + 6 / 3 = 27 / 21, far below the proven 99 / 55
    ),
    # ---- DM11B Hasta la Vista (F04 slot), 2026-10-25.  Plaza (nav y ~20, collision floor 0) x 21200..32000, z 21600..30000; Capitol hall + loot wing (y 800) x 33000..43500, z 28000..33000.
    # Escape pad (27500, 0, 22800), police spawn (27500, 200, 22800), stair foot (26667, 20, 27758).  No kick doors: door_hosts finds 0 leaves (survey 2026-10-25).
    # Everything below was checked against the COLLISION (kl_route grid), not only the walk mesh (DM06 lesson): extinguishers where a wall >= 160 cm wide stands 30..60 cm behind the spot at
    # 70/120/170 cm height and the body column in front is free; car lanes where a 3 m disc around every 100 cm point is free of solid 25..210 above a flat floor 0 (scan 2026-10-25).
    'DM11B': dict(
        slot='F04', file='F04_Main.zip', title='Hasta la Vista', tag='.before-1025overhaul3',
        doors=[],
        ext_spots=[(26201.0, 20.0, 27298.0, 0.0, (1.0, 0.0)), (27601.0, 20.0, 27298.0, 0.0, (1.0, 0.0)), (20980.0, 22.0, 27934.0, 0.0, (-1.0, 0.0)),
                   (34824.0, 813.0, 29764.0, 0.0, (0.0, -1.0)), (33184.0, 800.0, 28150.0, 0.0, (0.0, -1.0))],
        ext=[],
        fuel=[(25000.0, 26000.0, 20.0), (23500.0, 25400.0, 20.0), (30000.0, 27500.0, 20.0), (36500.0, 30500.0, 800.0)], fuel_ground=True,
        # cars: A and B drive east along the south road of the plaza (z 21800 / 22400), C comes down the west edge (x 21600); stops stay >= 1100 from the pad (27500, 22800).
        # GUESS: the cars are animated bodies (no real driving); the SWAT are the map's own police actors (wave3 clone of its Plaza_Wave template, see below).
        cars=dict(
            paths={12579: [(22000.0, 21800.0), (25000.0, 21800.0)], 12754: [(24000.0, 22400.0), (26000.0, 22400.0)], 12929: [(21600.0, 28800.0), (21600.0, 25000.0)]},
            cells={1: [(24600.0, 0.0, 22300.0), (24000.0, 0.0, 22200.0)], 2: [(26800.0, 0.0, 23400.0), (27200.0, 0.0, 22000.0)], 3: [(22100.0, 0.0, 26200.0), (22100.0, 0.0, 24600.0)]},
            wave3='Gameplay!030_AfterLoot!030_FinancialAlleyExit_Left',   # the map's own 3-man Police_SWAT squad (ARRIVE_XZ of the FA layer): the clone template
            backstop=40.0,            # GUESS: the crew needs ~30 s from the stair to the plaza; the cars arrive on the timer
            anm_col='Army',           # GUESS: same collection token as DM01B's police actors; build fails loudly if the .ANM lacks it
            caps=(99, 55)),           # census 43 / 24 + 6 / 3, far below the proven 99 / 55
    ),
    # ---- DM09 Retomoto Tower (F06 slot), 2026-10-25.  Live pin cf6b62ee (vans pass).  Tower office floors (y 19400..21050) are their own nav part (33), the street/lobby the main part (0).
    # No kick doors: door_hosts finds 0 leaves on this map.  NO police cars / SWAT: census is 99 actors / 56 squads, already at/over the proven 99 / 55, and cars() adds 6 / 3 (refused by its own budget check).
    # ext_spots (x, FLOOR y, z, wall length, zdir): picked 2026-10-25 by tools-free scan (s4.py in C:/kl_build_1024/overhaul_1025c/scratch): nav wall edge >= 150 long, collision floor within -110..+30 of the mesh,
    # solid wall at 70..170 above the floor within 20..60 cm along zdir at 2-3 of 3 sample points, free body column; the most fights (Pos# nodes) within 900 cm.  Two on the street, four on the office floors.
    'DM09': dict(
        slot='F06', file='F06_Main.zip', title='Retomoto Tower', tag='.before-1025overhaul3',
        doors=[],
        ext_spots=[(4847.0, 160.0, -6967.0, 209.0, (1.0, 0.0)), (2079.0, 20.0, -4740.0, 407.0, (-0.99997, -0.0079)),
                   (2385.0, 21000.0, -100.0, 979.0, (1.0, 0.0)), (5184.0, 20993.0, -759.0, 244.0, (1.0, 0.0)),
                   (-1678.0, 19600.0, -446.0, 205.0, (0.0638, 0.9980)), (-160.0, 21000.0, -1450.0, 171.0, (0.3641, -0.9314))],
        ext=[],
        # fuel: street cans on the collision floor (fuel_ground).  GUESS: anchors near the street fights (4300,-6300) and the lobby side; snap() moves them onto the mesh.
        fuel=[(4300.0, -6300.0, 160.0), (-1000.0, 9500.0, 0.0)], fuel_ground=True,
        cars=None,
    ),
}


def tag_of(mapname):
    return SPECS[mapname].get('tag', TAG)


def md5(b):
    return hashlib.md5(b).hexdigest()


def _ground_fuel(orig, log):
    """Wrap kl_dm01b_gas_1025.fuel_spots: the walk mesh floats above the collision terrain on open ground (DM06: 20..60 cm), so each can's floor y is the collision floor
    nearest below the mesh height (kl_route grid, floors within 110 under .. 30 over the mesh), else the mesh height stays."""
    def fn(B, nav):
        import kl_route as RT
        g = RT.load(B.zp).grid('all')
        out = []
        for (x, y, z) in orig(B, nav):
            fl = [q for q, _r in g.floors(int(x // RT.CELL), int(z // RT.CELL)) if y - 110.0 <= q <= y + 30.0]
            out.append((x, float(fl[-1]) if fl else y, z))
            log('  fuel can floor: mesh %d -> collision %s at (%d, %d)' % (y, fl[-1] if fl else 'none', x, z))
        return out
    return fn


def build(mapname, src, dst, log=print, keep=None):
    sp = SPECS[mapname]
    pin = md5(open(src, 'rb').read())
    work = keep or tempfile.mkdtemp(prefix='ovh_%s_' % mapname)
    os.makedirs(work, exist_ok=True)
    rep = collections.OrderedDict(map=mapname, pin=pin)
    try:
        s1, s2, s3 = [os.path.join(work, 's%d.zip' % i) for i in (1, 2, 3)]
        IG.TOP, IG.TOP_PATH = IG_TOP, 'ROOT' + BS + IG_TOP
        log('step 1: doors + extinguishers (kl_interact_graft.build, top %s)' % IG_TOP)
        IG.build(src, s1, ext=len(sp.get('ext_spots') or sp['ext']), doors=sp['doors'], ext_doors=0, spots=sp.get('ext_spots'), spots_near=sp['ext'], pin=pin, log=log, ext_lift=MALL.EXT_LIFT)
        m1 = md5(open(s1, 'rb').read())
        log('step 2: fuel cans (kl_dm01b_gas_1025.build, top %s)' % GS_TOP)
        GS.TOP = GS_TOP
        GS.FUEL_ANCHORS, GS.EXT_WALL = sp['fuel'], []
        GS.ext_spots_wall = lambda B, nav: []
        if sp.get('fuel_ground'):
            GS.fuel_spots = _ground_fuel(GS.fuel_spots, log)
        GS.build(s1, s2, pin=m1, log=log)
        last = s2
        if sp.get('cars'):
            log('step 3: police cars + SWAT along the plan')
            rep['cars'] = MALL.cars(s2, s3, log=log, plan=sp['cars'])
            last = s3
        log('step 4: sound references by name (only the nodes this build added)')
        mine = lambda p: (BS + IG_TOP + BS) in p or (BS + GS_TOP + BS) in p or (BS + 'KL_Cars!') in p
        rep['sound'] = MALL.resound(last, dst, log=log, scope=mine, cars_donor=bool(sp.get('cars')))
        rep['md5'] = md5(open(dst, 'rb').read())
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)
    return rep


# ------------------------------------------------------------------ installer
def ps_text(mapname):
    sp = SPECS[mapname]
    s = GS.PS1
    s = s.replace('gas.json', 'overhaul.json').replace('.before-1025dm01bgas', tag_of(mapname)).replace('gas.ps1', 'overhaul.ps1')
    s = s.replace(GS.MAP, mapname).replace(GS.FILE, sp['file'])      # the gas installer's text names DM01B / F03_Main.zip in its comments (and in its paths: the manifest holds them)
    # header fix 2026-10-25: the gas installer text names DM01B / F03 in its WHAT lines; name this map and its slot file instead
    s = s.replace('Maps' + BS + 'DM01B' + BS + 'F03_Main.zip', 'Maps' + BS + mapname + BS + sp['file']).replace('F03_Main.zip.before', sp['file'] + '.before')
    first = s.index('\n')
    return ('# overhaul.ps1 - %s (%s), 2026-10-25 (tools/kl_dm_overhaul_1025.py): %s extinguishers, fuel cans%s.\n'
            '#   Chained on the live zip named in overhaul.json "old"; the install refuses any other md5, refuses while kl2.exe runs.\n') % (
        mapname, sp['title'], 'kick doors,' if sp['doors'] else '', ', police cars + SWAT' if sp.get('cars') else '') + s[first + 1:]


BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0overhaul.ps1" {arg}\r\npause\r\n'


def run_ps(d, game, undo=False, dry=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'overhaul.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    if dry:
        a.append('-DryRun')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(mapname, src, out, scratch=None, log=print):
    sp = SPECS[mapname]
    old = md5(open(src, 'rb').read())
    os.makedirs(out, exist_ok=True)
    z = os.path.join(out, sp['file'])
    rep = build(mapname, src, z, log=log)
    new = md5(open(z, 'rb').read())
    man = dict(m=mapname, f=sp['file'], old=old, new=new, tag=tag_of(mapname), chain='live %s zip %s' % (mapname, old[:8]))
    with open(os.path.join(out, 'overhaul.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'overhaul.ps1'), 'w', newline='\r\n') as fh:
        fh.write(ps_text(mapname))
    for nm, arg in (('INSTALL %s overhaul.bat' % mapname, ''), ('UNDO %s overhaul.bat' % mapname, '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    log('staged %s: %s -> %s' % (out, old, new))
    if scratch:
        rehearse(mapname, src, out, man, scratch, log)
    return man


def rehearse(mapname, src, d, man, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game_' + mapname)
    live = os.path.join(g, 'KLExpansion', 'Maps', mapname, SPECS[mapname]['file'])
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(src, live)
    t = run_ps(d, g, dry=True); log(t.strip()); assert 'would install' in t and md5(open(live, 'rb').read()) == man['old'], t
    t = run_ps(d, g); log(t.strip()); assert 'installed' in t and md5(open(live, 'rb').read()) == man['new'], t
    assert md5(open(live + tag_of(mapname), 'rb').read()) == man['old']
    assert 'already installed' in run_ps(d, g)
    t = run_ps(d, g, undo=True); log(t.strip())
    assert md5(open(live, 'rb').read()) == man['old'] and not os.path.exists(live + tag_of(mapname)), 'undo not byte identical'
    assert 'already undone' in run_ps(d, g, undo=True)
    run_ps(d, g); assert md5(open(live, 'rb').read()) == man['new']
    run_ps(d, g, undo=True); assert md5(open(live, 'rb').read()) == man['old'] and not os.path.exists(live + tag_of(mapname))
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = run_ps(d, g); log(t.strip()); assert 'SKIP, live md5' in t and not os.path.exists(live + tag_of(mapname)), t
    shutil.rmtree(g, ignore_errors=True)
    log('rehearsal ok (dry run, install, idempotent, undo byte-identical, undo twice, reinstall, wrong md5 refused)')


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] == 'list':
        print(__doc__)
        print('maps:', ', '.join(SPECS))
        return 0
    if a[0] == 'build':
        print(json.dumps(build(a[1], a[2], a[3]), indent=1, default=str))
        return 0
    if a[0] == 'stage':
        stage(a[1], a[2], a[3], opt('--rehearse'))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
