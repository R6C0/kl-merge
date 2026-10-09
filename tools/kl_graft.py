#!/usr/bin/env python3
"""
Graft: the game systems of one Dog Days level (S) and the map of another level (M) as one level
archive in a slot. Milestone A = two stock Dog Days levels (no Dead Men data): proves the join.

    python kl_graft.py plain F02 [F01]         stock F02 under the slot's names (the baseline)
    python kl_graft.py build F07 F09 [F01]     systems of F07 + map of F09 -> the slot's archive,
                                               verified; exit code 1 if a check fails
    python kl_graft.py build F07 M01_FA_A      the same with a Dead Men map (converted on the fly)
                       ... --geometry          experiment: only M's geometry, S's game-mode layer
                       ... --m-add / --m-drop / --s-keep / --s-drop A,B   bisect by top-level
                                               subtree name or family (class Select)
    python kl_graft.py install [F01]           put the last build into Dog Days (each stock file
                                               is MOVED to KL_PortBackup once, never overwritten)
    python kl_graft.py pairs                   which S / M pairs need the least guessing

Outputs: <work folder>/build/install/Scenes/Locations/<slot>/ (kl_port_check.workdir()).

WHO OWNS WHAT (S = systems level, M = map level; top-level subtrees by kl_prpjoin.sides)
  S is the BASE of every file with an id space, so nothing of S is renumbered: its REF ids, .prm
  chunk indices, texture ids, material slots, .buf head offsets and .SND offsets stay as they are.
  M's map subtrees are appended and everything of M is renumbered:
  .gms/.buf  kl_scene: S's map subtrees removed, M's grafted (new REF ids), M's .buf head appended
             at a constant shift. Top-level order = kl_prpjoin.graft_picks. Room pairs and
             light<->geometry lists between two grafted subtrees are restored from M (graft() only
             keeps those inside one subtree). Navigation mesh: M's (built before any entity loads,
             names none). Dynamic list: per class the larger of the two counts, heap budget: the
             sum (both ASSUMPTIONS; neither is decoded). Surface table: S's (its REFs are all
             systems effects). FDX bone-dynamics block: M's, model indices renumbered
             (kl_members.fdx_join) - it belongs to the hanging lamps of the map.
  .prp       kl_prpjoin.join, then on every node that came from M:
             chunk indices (kl_prmgraph.prp_roots: ZGEOM[4], ZWINPIC[2] ...) through the .prm map;
             ZROOM[9] / ZROOM[10] (gate array, neighbour lists) + shift when the room has any;
             ZParticleEmitter[10] / [11] + shift (ASSUMPTION that they are .buf offsets: all 56
             non-zero values of F01..F09 lie in the head, the rest are 0 or -1);
             sound references (type handlers 70 and 46 = offsets into the level's .SND, re/audio.md)
             set to 0, because the bank is S's: THE MAP IS SILENT until the banks are merged.
             Heroes! are S's (systems) but take rotation / position from M's group of that name.
             Scene block: camera far plane, fog, background, SSAO from M; PostFilterBoxes from M
             (world-space boxes) or none; PostFilterPalettes stays S's, so M's post-filter sets
             index S's palette - harmless only when the two blobs are equal (python kl_graft.py pairs).
  KEYS       FOUND HERE (2026-10-09): the .buf head is addressed from the .gms too. An entity's
             raw data block of 64 bytes with 'KEYS' at +0x10 holds six .buf offsets at +0x28..+0x3c
             (key-frame tracks). With the ZROOM arrays and the emitter fields they cover the head
             of F01, F02, F04, F05 without a gap larger than one track. Grafted entities get them
             + shift. The 11 fields kl_prpjoin lists as "probably .buf offsets" are .SND offsets
             (handler 70 / 46) and are NOT shifted.
  .prm       S's file whole + the closure of M's roots (kl_prmgraph.append). S's dead map models
             stay in (bloat, no risk); only +0x1c of S's roots moves with the .oct.
  .TEX .MAT  kl_texmat merges, M's ids renumbered; MAT ref table recomputed from the joined .prm.
  .fxc       union.
  .oct       five-tree sets in room_order of the JOINED scene; root set = S's + M's with the
             entities that left removed; slot ids of both sides renumbered (old and new slots
             from the scenes before and after); S's records all kept, M's records of the kept
             models appended.
  .rmi .rmc  M's boxes renumbered (+ S's, if a systems room has one).
  .HVK       M's file is the base (static collision and MOPP order untouched), M's systems
             shapes dropped, S's systems shapes added, REF ids renumbered (kl_hvk.join).
  .sgd       both sides' shatter / explodable octrees with REFs renumbered (kl_members.sgd_join).
  .sgp       sound portals of M's rooms + S's systems rooms (kl_members.Sgp.join).
  .hrd       M's if all its rigid bodies come along (kl_members.hrd_join), else none.
  .ANM       ONE file: the level whose file has every animation set the joined .prp names; M's
             when both do (it also holds the map's own clips: escape vehicles, doors). Not joined.
  .SND .LOC .WHD .WAV, the .xml members, .sup .zgf: S's. The .SND is the weapons', voices' and
             HUD's bank and the .LOC keys index it. Map sounds need the bank merge of re/audio.md.
  .hti       S's; kl2.exe holds no ".hti" string, so nothing reads it.
NOT JOINED YET: sounds of the map (zeroed), animations (one side's file), light<->geometry lists
between systems and map (dropped by remove/graft), S's unused map models/textures (kept).

CHOICE OF S AND M FOR MILESTONE A: S = F07, M = F09 (python kl_graft.py pairs). S must be one of
F04..F09 (their systems hold the particle templates: no dangling path, kl_prpjoin). Of those
pairs only F07 + F09 has all three: equal PostFilterPalettes blobs, every animation set of M's
map in S's .ANM (and the reverse), and neither level has an FDX block or PostFilterBoxes.
(F04 + F02, the first idea: palettes differ, F04's .ANM lacks 'Police', F04 has an FDX block.)

LIVE RUNS 2026-10-09 (python kl_autotest.py <wait>; the default wait of 200 s is too short: a
healthy level needs 205 s or more to its AutoExit and is then reported as 'hung')
  1 stock F02 as F01 (plain), wait 200   RESULT: hung - still running after 200 s
  2 the same, wait 420                   RESULT: clean exit after 207 s. On screen: Buffering 52 %
                                         at 70 s, 99 % at 115 s, black from 160 s. = the baseline
  3 F07 systems + F09 map, first build   RESULT: clean exit after 205 s. At 100 s the player
                                         stands in F09's map with HUD and weapon (screenshot
                                         <work>/research/graft_A_F07sys_F09map_100s.png), black
                                         at 150 s like the baseline. MILESTONE A.
  4 F07 systems + M01_FA_A map (B1)      RESULT: crash kl2.exe+0x18a7fc after 39 s. All 14,993
                                         nodes had loaded. ZHavokCarScript (slot 2) walks the wheel
                                         list of a ZHavokCar that kl_gms.RETYPE made a ZSTDOBJ.
                                         Fix: DeadMen drops controllers owned by the class a
                                         retyped node no longer is (5 HavokCarScriptRout, 1
                                         InventoryBinding).
  5 the same, rebuilt (B2), twice        RESULT: crash outside kl2.exe after 80 s, both times.
                                         Still on the loading screen (Buffering 99 % at 70 s).
                                         eip = 0x1ad7945c = the object ZFFGameData keeps at
                                         +0x48ac (gamedata + 0x3e3c, all zero), reached from the
                                         update 0x4bca90 at 0x4bccd5 -> thunk 0x8af460 -> resolver
                                         0x45d600 -> jmp eax. Slot 10 (0x705200) arms that pointer
                                         when a scene other than KaneAndLynch / AttractMode starts.
                                         CAUSE NOT ESTABLISHED: the same call passes in runs 2, 3.
                                         Next: tell the map from Dead Men's game-mode layer
                                         (--geometry; kl_hvk.join first has to accept static
                                         collision from S's layer: F07's escape vehicles have it).
  6 F07 + F09 rebuilt with the final tool RESULT: hung - still running after 331 s, nothing logged
  7 the same installed build, wait 400   RESULT: clean exit after 324 s (black screen at 100 s).
                                         AutoExit counts engine ticks, not seconds: the same
                                         level left after 205 s and after 324 s. Run 6 was most
                                         likely the slow clock again (not proven). USE A WAIT OF
                                         420 s OR MORE.
LIVE RUNS 2026-10-09, second set (python kl_autotest.py --shots ... ; F07 systems + M01_FA_A map)
  B-1 rebuilt with the current converters RESULT: crash outside kl2.exe after 87 s: the same jump
      (kl_mat now gets the converted .prm)   into ZFFGameData+0x3e3c as run 5.
  B-2 the same build, tables watched      RESULT: crash outside kl2.exe after 61 s. A read-only
      from outside (ReadProcessMemory)       watch of the save-state tables 0xe0de38 / 0xe09e38
                                             (re/crash_gamedata.md) showed 9 of 1228 entries turn
                                             from ZOnlineSpeakTrigger (vtable 0xbc98fc) into
                                             ZSerializable and then freed memory within a second.
                                             Cause: mute_speech(). Fix: those controllers go.
  B-3 without the 9 speech triggers       RESULT: crash kl2.exe+0x41e714 after 92 s. The level
                                             started (checkpoint taken at 88 s). A ZMatPosAnim
                                             read a bit-packed key index far outside the .buf:
                                             the KEYS chunk of M01's AnimatedRumbleCamera sits at
                                             +0xaa0 of a 2804-byte raw block and its six offsets
                                             were not shifted. Fix: keys_tracks().
  B-4 with every KEYS chunk shifted       RESULT: clean exit after 219 s. At 130 s the player
                                             runs along the street of Dead Men's M01 (Sunny Hill
                                             Plaza), textured, lit, with Dog Days' HUD and pistol,
                                             Dead Men's agents and cars in the car park
                                             (<work>/research/graft_B_F07sys_M01map_130s.png).
                                             Black at 100 s and 160 s, as the baseline is at times.
                                             MILESTONE B. This build is what the F01 slot holds.
BISECT (not needed in the end, but it works): build ... --geometry [--m-add A,B] [--m-drop ..]
  [--s-keep ..] [--s-drop ..], see Select. '--geometry --s-drop *' = M's geometry and no game-mode
  layer at all verifies with 0 problems; plain '--geometry' leaves S's game-mode layer with scene
  paths into S's map that is gone (verify reports them).
"""
import collections, os, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_package, kl_gms, kl_scene, kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_members as MB, kl_hvk, kl_anm
import kl_prpjoin as J
from kl_prp import Prp, units
from kl_port_check import find, workdir, DD_GUESSES, DD_EXE

BESIDE = ('.WHD', '.WAV', '.hti')      # files next to the archive that belong to its members
SOUND_TYPES = {70: '0x5f7640', 46: '0x6c4230'}   # re/kl2.json type handler index -> its load function
KEYS = 0x4b455953                      # 'SYEK': a key-frame track chunk in a raw data block (keys_tracks)
TAKE = ('CameraFar', 'CameraFogBegin', 'CameraFogFull', 'CameraFogMin', 'CameraBackgroundColor',
        'SSAO_Blur', 'SSAO_Strength')  # scene properties that describe the map
LANGS = kl_package.LANGS


# ------------------------------------------------------------------ files in and out
def out_dir(slot):
    d = os.path.join(workdir(), 'build', 'install', 'Scenes', 'Locations', slot)
    os.makedirs(d, exist_ok=True)
    return d


def stock_beside(level, ext):
    """Stock <level>_Main<ext> next to the archive; a file moved to KL_PortBackup wins."""
    dd = find(DD_GUESSES, DD_EXE)
    for root in (os.path.join(dd, kl_package.BACKUP), dd):
        p = os.path.join(root, 'Scenes', 'Locations', level, level + '_Main' + ext)
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(level + '_Main' + ext)


def member_name(name, level, slot):
    """Archive member of `level` under the slot's name (the UI .xml members have no level name)."""
    return name.replace('Locations/%s/%s_Main' % (level, level), 'Locations/%s/%s_Main' % (slot, slot))


def write_level(slot, members, beside, log=print):
    """members: [(member name, bytes)] in archive order; beside: {extension: source path}."""
    d = out_dir(slot)
    path = os.path.join(d, slot + '_Main.zip')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for name, data in members:
            z.writestr(name, data)
    for ext in BESIDE:
        shutil.copyfile(beside[ext], os.path.join(d, slot + '_Main' + ext))
    log('built %s, %.0f MB, %d members' % (path, os.path.getsize(path) / 1e6, len(members)))
    return path


def plain(level, slot='F01', log=print):
    """Stock `level` with nothing changed but the member names: what a healthy level looks like
    through the unattended launcher, and the proof that renaming alone is harmless. No member
    of F02 or F04 holds its own file name (searched 2026-10-09)."""
    with zipfile.ZipFile(J.level_zip(level)) as z:
        members = [(member_name(n, level, slot), z.read(n)) for n in z.namelist()]
    return write_level(slot, members, {e: stock_beside(level, e) for e in BESIDE}, log)


def install(slot='F01', log=print):
    """Copy the built archive and the files beside it into Dog Days' slot. Each stock file is
    moved to KL_PortBackup the first time (kl_package._backup_then_copy), never overwritten."""
    dd, d = find(DD_GUESSES, DD_EXE), out_dir(slot)
    for f in [slot + '_Main.zip'] + [slot + '_Main' + e for e in BESIDE]:
        kl_package._backup_then_copy(dd, os.path.join('Scenes', 'Locations', slot, f), os.path.join(d, f))


class Level:
    """One stock Dog Days level: its members, property tree (kl_prpjoin.Scene) and scene
    (kl_scene.Scene). ents[k - 1] is the entity of .prp node k."""

    def __init__(self, name):
        self.name = name
        with zipfile.ZipFile(J.level_zip(name)) as z:
            self.order = z.namelist()
            self.files = {n: z.read(n) for n in self.order}
        self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}   # '.gms', 'English.LOC'
        self.prp = J.Scene.load(name)
        self.scene = kl_scene.Scene(kl_gms.unpack(self[".gms"]), self['.buf'])
        self.ents = list(self.scene.entities())
        if [e.name.decode('latin1') for e in self.ents] != self.prp.names[1:]:
            raise ValueError('%s: .gms and .prp disagree on the entities' % name)
        self.slot0 = self.scene.slots()                 # before any edit
        self.side = J.sides(self.prp)
        self.dm = False

    def __getitem__(self, ext):
        return self.files[self.ext[ext]]


class DeadMen(Level):
    """A Dead Men level presented in Dog Days form, with the converters as they are today:
    .prp kl_convert (schema-driven; pairings marked 'assumed' there), classes kl_gms.RETYPE,
    navigation mesh kl_pf4, gates 0x38 -> 0x74 (kl_rooms.dd_gate) appended to the .buf head,
    .prm / .TEX / .MAT kl_prm / kl_tex / kl_mat. Chunk indices, REF ids, slot ids, .buf offsets
    and texture / material ids are still Dead Men's own: build() renumbers them like any M.
    NOT converted (copied, ASSUMPTION that Dog Days reads them alike): entity flags and raw data
    blocks (KEYS, light curves), .HVK surface indices, .sgd octrees, .sgp, .hrd, FDX block.
    Dead Men's 'CoverList' (a top-level list with FFCoverList) is counted as map: Dog Days keeps
    its own under Specials!CoverPoints!, which leaves with S's map."""

    def __init__(self, name, log=print):
        import kl_convert as K, kl_pf4, kl_rooms, kl_prm, kl_mat, kl_tex
        self.name, self.dm = name, True
        with zipfile.ZipFile(J.level_zip(name, 'dm')) as z:
            self.order = z.namelist()
            self.files = {n: z.read(n) for n in self.order}
        self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}
        src = J.Scene.load(name, 'dm')
        self.side = J.sides(src)
        for k in range(1, len(src.nodes)):
            if src.names[src.top[k]] == 'CoverList':
                self.side[k] = 'map'
        raw = kl_gms.unpack(self['.gms'])
        conv = K.converter(find(DD_GUESSES, DD_EXE), workdir())
        data, st = K.convert_level(self['.prp'], conv, src.tids)
        tids = [src.tids[0]] + [K.RETYPE.get(t, t) for t in src.tids[1:]]
        self.prp = J.Scene(Prp(data), src.names, tids, 'dd', name)
        # A controller written for the class a node WAS: HavokCarScriptRout on a ZHavokCar that
        # kl_gms.RETYPE made a ZSTDOBJ walks the car's wheel list at object +0x96c, far behind a
        # ZSTDOBJ (crash kl2 0x58a7fc right after the load, run B1). Such controllers go.
        sch, cut = J.schema('dd'), collections.Counter()
        for k in range(1, len(tids)):
            if tids[k] != src.tids[k]:
                node, chain = self.prp.nodes[k], sch.bases(sch.geoms[src.tids[k]]) if src.tids[k] in sch.geoms else None
                keep = []
                for nm, body in node['ctrls']:
                    owners = [e[0] for e in sch.controllers.get(self.prp.p.key(nm), [])]
                    if chain and owners and not set(owners) & set(sch.bases(self.prp.cls(k))) and set(owners) & set(chain):
                        cut[self.prp.p.key(nm)] += 1
                    else:
                        keep.append((nm, body))
                node['ctrls'] = keep
        if cut:
            log('%s: controllers of retyped nodes removed: %s' % (name, dict(cut)))
        sc = kl_scene.Scene(raw, self['.buf'])
        self.slot0 = sc.slots()
        for e in sc.entities():
            e.tid = K.RETYPE.get(e.tid, e.tid)
        if sc.slots() != self.slot0:
            raise ValueError('a retype in kl_gms.RETYPE moves entities to another pool: slot ids would be stale')
        sc.game = 'dd'
        if sc.nav is not None:
            sc.nav = kl_pf4.convert(sc.nav)
        self.scene, self.ents = sc, list(sc.entities())
        ngates = 0
        for k, node in enumerate(self.prp.nodes):       # gate arrays in Dog Days' record size
            lab = labels(self.prp.cls(k))
            if 'ZROOM[9]' not in lab:
                continue
            def fn(us):
                nonlocal ngates
                n, off = u32(us[lab.index('ZROOM[0]')][0]), u32(us[lab.index('ZROOM[9]')][0])
                us[lab.index('ZROOM[2]')] = [(0x09, bytes(4))]      # as kl_rooms.convert_gates (ASSUMPTION there)
                if n:
                    if off + 0x38 * n > len(sc.head):
                        raise ValueError('room gates lie outside the .buf head')
                    sc.head += bytes(-len(sc.head) % 16)
                    us[lab.index('ZROOM[9]')] = [(0x09, struct.pack('<I', len(sc.head)))]
                    sc.head += b''.join(kl_rooms.dd_gate(sc.head[off + 0x38 * i:off + 0x38 * i + 0x38]) for i in range(n))
                    ngates += n
            edit(node, 'props', fn)
        roots = [c for c in G.gms_roots(raw) if c] + [(c, k) if k else c for _w, c, k in G.prp_roots(src.p, src.tids, J.schema('dm'), 'dm')]
        self.files[self.ext['.prm']], rep = kl_prm.convert(self['.prm'], roots)
        # as kl_dmassets.convert_level: the .MAT's use counts and surface numbers follow the
        # CONVERTED .prm and Dog Days' surface table (the graft keeps S's .buf tail)
        tex_ids = set(T.read_tex(self['.TEX']).tex)
        self.files[self.ext['.TEX']] = kl_tex.convert(self['.TEX'])[0]
        self.files[self.ext['.MAT']] = kl_mat.convert_mat_full(self['.MAT'], prm=self['.prm'], surface='dd',
                                                               texture_ids=tex_ids)[0]
        log('%s converted: %s; %d gates; .prm %s' % (name, dict(st), ngates, {k: v for k, v in rep.items() if v and not isinstance(v, list)}))


GEOMETRY = ('Locations/*', 'CloneGroup_Locations')      # + anything with 'Backdrop' in its name


def geometry(name):
    return J.family(name) in GEOMETRY or 'backdrop' in name.lower()


class Select:
    """Which top-level MAP subtrees go into the graft (systems subtrees are always S's).
    Default: all of M's, none of S's. geometry: of M only the geometry, and S keeps its own
    game-mode layer (FASpecials!, Gameplay!, Specials!, Animation/...), which then stands in M's
    geometry at S's coordinates. The four pattern lists then adjust that, one bisect step per
    command; a pattern is matched (fnmatch, case-insensitive) against the subtree's name and its
    kl_prpjoin.family ('Settings!', 'Locations/*', 'CloneGroup_Effects' ...):
      m_add   M's subtrees taken although geometry-only would leave them out
      m_drop  M's subtrees left out
      s_keep  S's map subtrees kept
      s_drop  S's map subtrees left out although geometry-only would keep them"""

    def __init__(self, geometry=False, m_add=(), m_drop=(), s_keep=(), s_drop=()):
        self.geometry, self.m_add, self.m_drop, self.s_keep, self.s_drop = geometry, m_add, m_drop, s_keep, s_drop

    @staticmethod
    def match(name, pats):
        import fnmatch
        return any(fnmatch.fnmatch(x.lower(), p.lower()) for p in pats for x in (name, J.family(name)))

    def m(self, name):
        return (not self.geometry or geometry(name) or self.match(name, self.m_add)) and not self.match(name, self.m_drop)

    def s(self, name):
        return ((self.geometry and not geometry(name)) or self.match(name, self.s_keep)) and not self.match(name, self.s_drop)

    def __str__(self):
        return ' '.join(['--geometry'] * self.geometry + ['--%s %s' % (k.replace('_', '-'), ','.join(v)) for k, v in
                        (('m_add', self.m_add), ('m_drop', self.m_drop), ('s_keep', self.s_keep), ('s_drop', self.s_drop)) if v]) or 'whole map'


def picks_of(S, M, sel=None):
    """kl_prpjoin.graft_picks with each level's own sides: M's top-level order, its map subtrees
    kept, each systems subtree replaced by S's of the same name; S's other systems subtrees go in
    before the closing systems objects. A MAP subtree of M with the name of a systems subtree of
    S also gives way to S's (Dead Men M01 keeps bullet-impact effects, and so their clone groups,
    inside the map: two top-level subtrees of one name would make every path to them ambiguous;
    no pair of Dog Days levels has such a name). -> (picks, names of M left out).
    sel (Select) narrows M's map subtrees and keeps map subtrees of S: the bisect of a crash."""
    sel = sel or Select()
    def owner(lv, t):
        """The name the selection goes by: a clone group follows the subtree of its template
        (M01's Locations hold ZAllocMany templates whose groups are CloneGroup_Effects/...)."""
        if lv not in tpl:
            tpl[lv] = J.templates(lv.prp)
        return lv.prp.names[lv.prp.top[tpl[lv][t]]] if t in tpl[lv] else lv.prp.names[t]
    tpl = {}
    mine = {}
    for t in S.prp.tops():
        if S.side[t] == 'systems':
            mine.setdefault(S.prp.names[t], []).append(t)
    out, dropped = [], []
    for t in M.prp.tops():
        if mine.get(M.prp.names[t]):
            out.append((S.prp, mine[M.prp.names[t]].pop(0)))
            if M.side[t] == 'map':
                dropped.append(M.prp.names[t])
        elif M.side[t] == 'map' and sel.m(owner(M, t)):
            out.append((M.prp, t))
        else:
            dropped.append(M.prp.names[t])
    taken = {M.prp.names[t] for sc, t in out if sc is M.prp}
    out += [(S.prp, t) for t in S.prp.tops() if S.side[t] == 'map' and sel.s(owner(S, t)) and S.prp.names[t] not in taken]
    rest = sorted(t for ts in mine.values() for t in ts)
    at = next((i for i, (sc, t) in enumerate(out) if sc is S.prp and S.prp.names[t] in ('TrackLinkObjects', 'ZParticleController')), len(out))
    return out[:at] + [(S.prp, t) for t in rest] + out[at:], dropped


# ------------------------------------------------------------------ small helpers
def u32(tok):
    return struct.unpack('<I', tok[1])[0]


def labels(cls):
    return J.labels('dd', cls)


def objects(sc, k):
    """(class, object holder, key) of node k and of its controllers the game registers; the
    object's tokens are holder[key]."""
    n, cls = sc.nodes[k], sc.cls(k)
    out = [(cls, n, 'props')]
    for i, (nm, _body) in enumerate(n['ctrls']):
        impl = J.schema('dd').controller(sc.p.key(nm), cls)
        if impl:
            out.append((impl, n['ctrls'], i))
    return out


def get_obj(holder, key):
    return holder[key] if key == 'props' else holder[key][1]


def set_obj(holder, key, toks):
    if key == 'props':
        holder[key] = toks
    else:
        holder[key] = (holder[key][0], toks)


def edit(holder, key, fn):
    """Run fn(list of field units) on an object and store the result."""
    obj = get_obj(holder, key)
    us = [list(u) for u in units(obj[1:-1])]
    fn(us)
    set_obj(holder, key, [obj[0]] + [t for u in us for t in u] + [obj[-1]])


def is_room(tid):
    sch = J.schema('dd')
    return 'ZROOM' in sch.bases(sch.geoms.get(tid, ''))


def rooms_of(scene):
    """(entities, room_order as entities with None for the root) of a kl_scene.Scene."""
    ents = list(scene.entities())
    idx = {e: i for i, e in enumerate(ents)}
    order = O.room_order([idx[e.parent] if e.parent else -1 for e in ents], [is_room(e.tid) for e in ents])
    return ents, [None if i < 0 else ents[i] for i in order]


def keys_tracks(raw):
    """[(position in the raw data block, the six .buf offsets)] of every KEYS chunk in it.
    A chunk is 'SYEK', its size 0x30, key count, 0, count - 1, 1 and six .buf offsets at +0x18
    (reader kl2 0x422c50: [chunk + 0x18 + 0x10 .. 0x24] + .buf base). Mostly it is the whole of a
    64-byte block (chunk at +0x10), but a camera or a light with several animated parameters
    carries it at the end of a longer block: M01's AnimatedRumbleCamera (2804 bytes, chunk at
    +0xaa0), stock F01's too, lights in L02 / L04 / L05. Missing those left the track offsets
    unshifted: crash kl2 0x81e714 (bit-packed key index read far outside the .buf)."""
    out = []
    if raw is not None:
        for p in range(0, len(raw) - 0x2c, 4):
            if struct.unpack_from('<II', raw, p) == (KEYS, 0x30):
                out.append((p + 0x18, struct.unpack_from('<6I', raw, p + 0x18)))
    return out


def mute_speech(sc, ctrl, snd):
    """True for an OnlineSpeakTrigger controller whose line the level's .SND does not hold.
    ZOnlineSpeakTrigger's init (kl2 0x4eae60, vtable 0xbc98fc slot 13) looks its line up by name
    (0x828fa0; the bank lists it as 'audio:dialog/<name, lower case>#sound') and, when that
    fails, deletes itself through slot 30 - but it has already been entered in the save-state
    table at 0xe09e38, which has no 'unregister'. The level-start checkpoint (0x65a4d0) then
    calls slot 21 of the freed object: nine such triggers of M01_FA_A (AI_Enemies!, Civilians!)
    were the jump into ZFFGameData+0x3e3c at Buffering 99 % (seen live 2026-10-09: the nine
    table entries go ZOnlineSpeakTrigger -> ZSerializable -> freed within a second).
    The line is the object's first string (F06's only stock trigger: Multiplayer/F06/
    Chopper_response_R, and its bank has audio:dialog/multiplayer/f06/chopper_response_r#sound)."""
    nm, body = ctrl
    if sc.p.key(nm) != 'OnlineSpeakTrigger':
        return False
    line = next((sc.p.key(t) for t in body if t[0] == 0x0c), '')
    return ('audio:dialog/%s#sound' % line.lower()).encode('latin1') not in snd.lower()


def dm_rename(Jn, S, log=print):
    """{string: string} for a Dead Men map under Dog Days systems: scene paths into Dead Men's
    systems subtree get Dog Days' top-level name; a weapon template Dog Days does not have is
    replaced by one of S's whose name starts alike (ASSUMPTION: a guess by family, any weapon is
    safer than a path that names nothing); animation sets the .ANM lacks take the stand-ins of
    kl_package.ANIM_SETS (guesses, see there)."""
    old, new = 'ROOT\\AllLevels/mainsceneincludes.zip', 'ROOT\\AllLevels/mainsceneincludes_multiplayer.zip'
    weapons = [S.prp.path[k] for k in range(1, len(S.prp.nodes))
               if S.prp.path[k].lower().startswith((new + '\\AllLevels/equipment.zip\\Weapon\\').lower())
               and S.prp.path[k].count('\\') == 4]
    have = {c.name for c in kl_anm.Anm(S['.ANM'], 'dd').cols}
    out, guessed = {}, {}
    for s in Jn.p.keys:
        if s.lower().startswith(old.lower() + '\\'):
            t = new + s[len(old):]
            if not S.prp.resolve(t) and '\\Weapon\\' in t and weapons:
                fam = t.rsplit('\\', 1)[1].split('_')[0].lower()
                t = guessed[s.rsplit('\\', 1)[1]] = next((w for w in weapons if w.rsplit('\\', 1)[1].lower().startswith(fam)), weapons[0])
            out[s] = t
        elif s.startswith(kl_anm.PREFIX) and s not in have:
            t = kl_anm.PREFIX + (kl_package.ANIM_SETS.get(s[len(kl_anm.PREFIX):]) or '')
            if t in have:
                out[s] = t
    log('  Dead Men paths re-pointed: %d; weapons replaced: %s' % (len(out), {k: v.rsplit('\\', 1)[1] for k, v in guessed.items()}))
    return out


# ------------------------------------------------------------------ the graft
def build(s_name, m_name, slot='F01', log=print, sel=None):
    """Systems of S + map of M -> (path of the archive, problems found by verify())."""
    sch = J.schema('dd')
    for t, load in SOUND_TYPES.items():
        if sch.types[t]['load'] != load:
            raise ValueError('re/kl2.json was rebuilt: type handler %d is no longer the sound reference' % t)
    S, M = Level(s_name), (DeadMen(m_name, log) if m_name.startswith('M') else Level(m_name))
    notes = []
    note = lambda s: (notes.append(s), log('  note: ' + s))

    # ---- which subtrees
    sel = sel or Select()
    picks, dropped = picks_of(S, M, sel)
    s_tops = {t for sc, t in picks if sc is S.prp}
    m_tops = [t for sc, t in picks if sc is M.prp]
    m_nodes = {k for t in m_tops for k in range(t, M.prp.end[t])}
    log('%s systems (%d subtrees, %d nodes) + %s map (%d subtrees, %d nodes); left out of %s: %s' % (
        s_name, len(s_tops), sum(S.prp.end[t] - t for t in s_tops), m_name, len(m_tops), len(m_nodes), m_name,
        collections.Counter(J.family(n) for n in dropped).most_common()))

    # ---- .gms / .buf: remove S's map, graft M's map
    A, B = S.scene, M.scene
    lost = collections.Counter()
    for t in S.prp.tops():
        if t not in s_tops:
            r = A.remove(S.ents[t - 1])
            lost['S links'] += r['links']; lost['S pairs'] += r['pairs']
    s_kept = set(A.entities())
    copy, refs_m, shift = {}, {}, None
    for t in m_tops:
        r = A.graft(B, M.ents[t - 1], head=True)
        refs_m.update(r['refs']); shift = r['buf']
        copy.update(zip(M.ents[t - 1].walk(), r['top'].walk()))
    top_ent = {(id(S.prp), t): S.ents[t - 1] for t in s_tops}
    top_ent.update({(id(M.prp), t): copy[M.ents[t - 1]] for t in m_tops})
    A.roots = [top_ent[id(sc), t] for sc, t in picks]
    # lists and pairs between two grafted subtrees (graft() keeps only those inside one)
    for e, c in copy.items():
        if e.links is not None:
            c.links = [(copy[t] if t is not None else None, b) for t, b in e.links if t is None or t in copy]
            lost['M links'] += len(e.links) - len(c.links)
    have = set(A.pairs)
    for a, b in B.pairs:
        if (a is None or a in copy) and b in copy:
            p = (copy.get(a), copy[b])
            if p not in have:
                A.pairs.append(p); have.add(p)
        else:
            lost['M pairs'] += 1
    log('  lists / pairs that crossed the cut and are gone: %s' % dict(lost))
    # KEYS tracks of grafted entities live in M's head, now at + shift
    nkeys = 0
    for e, c in copy.items():
        r = e.raw
        for p, ko in keys_tracks(e.raw):
            if any(not 16 <= v < len(B.head) for v in ko):
                raise ValueError('%r: KEYS offset outside the .buf head' % e)
            r = r[:p] + struct.pack('<6I', *(v + shift for v in ko)) + r[p + 24:]
            nkeys += 1
        if r is not e.raw:
            c.raw = r
    A.nav = B.nav
    A.budget += B.budget                                # ASSUMPTION, see kl_scene
    if A.dyn is not None and B.dyn is not None:
        if [c for c, _n in A.dyn] != [c for c, _n in B.dyn]:
            note('dynamic lists name different classes; kept %s\'s' % s_name)
        else:
            A.dyn = [(c, max(n, m)) for (c, n), (_c, m) in zip(A.dyn, B.dyn)]   # ASSUMPTION
    slot1 = A.slots()
    final = list(A.entities())

    # ---- .prp join
    base_settings = S.prp.p.settings
    mblock, sblock = dict(J.block(M.prp)), dict(J.block(S.prp))
    take = {n: M.prp for n in TAKE if n in mblock}
    if 'PostFilterBoxes' in mblock and not M.dm:        # Dead Men's sets index Dead Men's palette: left out
        take['PostFilterBoxes'] = M.prp
    elif 'PostFilterBoxes' in sblock:                   # S's boxes lie in S's world: none
        ent = [(n, t) for n, t in J.block(S.prp) if n != 'PostFilterBoxes']
        S.prp.p.settings = [(0x04, struct.pack('<I', len(ent)))] + [x for _n, t in ent for x in t]
    try:
        label = '%s systems + %s map' % (s_name, m_name)
        Jn = J.join(S.prp, picks, label, take=take)
        if M.dm:
            rename = dm_rename(Jn, S, log)
            Jn = J.join(S.prp, picks, label, rename=lambda s: rename.get(s, s), take=take)
    finally:
        S.prp.p.settings = base_settings
    if Jn.names[1:] != [e.name.decode('latin1') for e in final]:
        raise ValueError('joined .prp and joined .gms list different entities')
    at = {(id(sc), k): j for j, (sc, k) in enumerate(Jn.origin)}      # source node -> joined node
    mj = {k: at[id(M.prp), k] for k in m_nodes}

    # ---- roots of M in its .prm
    prm_s, prm_m = G.read(S['.prm'], 'dd'), G.read(M['.prm'], 'dd')
    proots = [r for r in G.prp_roots(M.prp.p, M.prp.tids, sch, 'dd')
              if (r[0][0] == 'scene' and r[0][1] in take) or (r[0][0] != 'scene' and r[0][0] in m_nodes)]
    roots = [(c, k) if k else c for _w, c, k in proots] + [e.model for e in copy if e.model]
    kinds, _args = G.walk(prm_m, roots)
    order = sorted(kinds)
    cmap = {old: len(prm_s.chunks) + k for k, old in enumerate(order)}   # what append() will hand out
    # materials and textures M's kept chunks name
    slots = {prm_m.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    tex_s, tex_m, mat_s, mat_m = T.read_tex(S['.TEX']), T.read_tex(M['.TEX']), T.read_mat(S['.MAT']), T.read_mat(M['.MAT'])
    want = set(T.used_textures(mat_m, slots))
    for i, k in kinds.items():
        for off, typ, _k in G.fields(prm_m, i, k, _args.get(i, 0)):
            if typ in 'tT' and prm_m.u32(i, off):
                want.add(prm_m.u32(i, off) % G.SLOTS['dd'])
    tex, tmap = T.merge_tex(tex_s, tex_m, want)
    mat, mmap = T.merge_mat(mat_s, mat_m, slots, tmap)
    log('  .prm: %d of %d chunks of %s appended to %d; materials %d -> %d slots (+%d), textures %d -> %d ids (+%d)' % (
        len(order), len(prm_m.chunks) - 1, m_name, len(prm_s.chunks) - 1, len(mat_s.insts), len(mat.insts),
        len(mat.insts) - len(mat_s.insts), len(tex_s.tex), len(tex.tex), len(tex.tex) - len(tex_s.tex)))

    # ---- .oct / .rmi / .rmc: slot ids of both sides, then the sets in the joined room order
    oct_s, oct_m = O.Oct.parse(S['.oct']), O.Oct.parse(M['.oct'])
    ids_s = {S.slot0[e] + 2: slot1[e] + 2 for e in s_kept}
    drop_s = {S.slot0[e] + 2 for e in S.ents if e not in s_kept}
    ids_m = {M.slot0[e] + 2: slot1[c] + 2 for e, c in copy.items()}
    drop_m = {M.slot0[e] + 2 for e in M.ents if e not in copy}
    ids_s[1] = ids_m[1] = 1                             # the scene root
    sets = {}
    for lv, octx, ids, drop, to in ((S, oct_s, ids_s, drop_s, lambda e: e), (M, oct_m, ids_m, drop_m, copy.get)):
        ro = O.room_order([lv.prp.parent[k] - 1 for k in range(1, len(lv.prp.nodes))],
                          [is_room(t) for t in lv.prp.tids[1:]])
        if len(ro) != len(octx.rooms):
            raise ValueError('%s: %d rooms, %d tree sets in the .oct' % (lv.name, len(ro), len(octx.rooms)))
        new = O.remap_ids(octx, ids, drop)
        for i, five in zip(ro, new.rooms):
            e = None if i < 0 else to(lv.ents[i])
            if i < 0:
                sets.setdefault(None, []).append(five)
            elif e is not None and e in slot1:
                sets[e] = five
    _ents, ro = rooms_of(A)
    rooms = [O.join_room_trees(*sets[None]) if e is None else sets[e] for e in ro]
    rec_m = {v: n for n, v in enumerate(oct_m.record_refs())}
    keep_m = sorted({rec_m[prm_m.u32(i, 0x1c)] for i, k in kinds.items() if k == 'root' and prm_m.u32(i, 0x1c)})
    base = O.Oct(oct_s.header, rooms, oct_s.records, oct_s.tail)
    octj, _same, refs_b = O.append_records(base, oct_m, cmap, keep_m)
    refs_a = dict(zip(oct_s.record_refs(), octj.record_refs()))        # S's records moved with the room trees
    unref = lambda v: (v & ~1) - 4
    prm, cmap2 = G.append(prm_s, prm_m, roots, mmap, {unref(a): unref(b) for a, b in refs_b.items()}, tmap)
    if cmap2 != cmap:
        raise ValueError('kl_prmgraph.append numbers chunks differently than assumed here')
    moved = 0
    for i in range(1, len(prm_s.chunks)):               # S's model roots: (.oct record offset + 4) | 1 at +0x1c
        c = prm.chunks[i]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0] in refs_a:
            v = refs_a[struct.unpack_from('<I', c, 0x1c)[0]]
            prm.chunks[i] = c[:0x1c] + struct.pack('<I', v) + c[0x20:]
            moved += 1
    if moved != len(oct_s.records):
        raise ValueError('%d of %s\'s %d .oct records are named by a model root' % (moved, s_name, len(oct_s.records)))
    prm_bytes = G.write(prm)
    mat.refs = T.material_refs(prm_bytes)
    index = {}
    for ext in ('.rmi', '.rmc'):
        a = O.remap_ids(O.RoomIndex.parse(S[ext]), ids_s, drop_s)
        b = O.remap_ids(O.RoomIndex.parse(M[ext]), ids_m, drop_m)
        b = O.RoomIndex(b.tree, [x.sized(O.BOX['dd']) for x in b.boxes], O.BOX['dd'])
        index[ext] = (O.join_index(a, b) if a.boxes and b.boxes else b if b.boxes else a).pack()
        log('  %s: %d boxes of %s + %d of %s' % (ext, len(a.boxes), s_name, len(b.boxes), m_name))
    log('  .oct: %d room sets, %d + %d records' % (len(rooms), len(oct_s.records), len(keep_m)))

    # ---- entity models, then the properties of M's nodes
    for e, c in copy.items():
        if e.model:
            c.model = cmap[e.model]
    for (node, ctrl, f), chunk, _kind in proots:
        if node == 'scene':
            s = Jn.p.settings
            k = next(i for i, t in enumerate(s) if t[0] == 0x0c and Jn.p.key(t) == ctrl)
            if u32(s[k + 4]) != chunk:
                raise ValueError('scene property %s is not where prp_roots found it' % ctrl)
            s[k + 4] = (s[k + 4][0], struct.pack('<I', cmap[chunk]))
            continue
        n = Jn.nodes[mj[node]]
        def fn(us, f=f, chunk=chunk):
            if u32(us[f][0]) != chunk:
                raise ValueError('chunk field moved')
            us[f][0] = (us[f][0][0], struct.pack('<I', cmap[chunk]))
        edit(n, 'props', fn) if ctrl is None else edit(n['ctrls'], ctrl, fn)
    count = collections.Counter()
    room_cells = set()
    for k in sorted(m_nodes):
        for cls, holder, key in objects(Jn, mj[k]):
            fs, lab = sch.fields(cls), labels(cls)
            hot = [i for i, f in enumerate(fs) if f.type in SOUND_TYPES and f.kind == 'I']
            pos = {l: i for i, l in enumerate(lab) if l in ('ZROOM[0]', 'ZROOM[1]', 'ZROOM[9]', 'ZROOM[10]',
                                                           'ZParticleEmitter[10]', 'ZParticleEmitter[11]')}
            if not hot and not pos:
                continue
            def fn(us):
                for i in hot:
                    if u32(us[i][0]):
                        us[i][0] = (us[i][0][0], bytes(4)); count['sound references set to 0'] += 1
                if 'ZROOM[9]' in pos:
                    ng, nl = u32(us[pos['ZROOM[0]']][0]), us[pos['ZROOM[1]']][0][1][0]
                    g, l = u32(us[pos['ZROOM[9]']][0]), u32(us[pos['ZROOM[10]']][0])
                    if ng:
                        us[pos['ZROOM[9]']][0] = (us[pos['ZROOM[9]']][0][0], struct.pack('<I', g + shift))
                    if nl:
                        us[pos['ZROOM[10]']][0] = (us[pos['ZROOM[10]']][0][0], struct.pack('<I', l + shift))
                    if ng or nl:
                        room_cells.update(kl_scene.room_refs(A.head, 'dd', g + shift, ng, l + shift, nl))
                        count['rooms with gates or lists'] += 1
                for l in ('ZParticleEmitter[10]', 'ZParticleEmitter[11]'):
                    if l in pos and u32(us[pos[l]][0]) not in (0, 0xffffffff):
                        v = u32(us[pos[l]][0])
                        if not 16 <= v < len(B.head) and not M.dm:
                            raise ValueError('emitter offset %#x outside the .buf head' % v)
                        if not 16 <= v < len(B.head):   # a converted field that is not an offset: none
                            v = 0xffffffff - shift; count['emitter fields cleared'] += 1
                        us[pos[l]][0] = (us[pos[l]][0][0], struct.pack('<I', v + shift)); count['emitter offsets'] += 1
            edit(holder, key, fn)
    # REF ids in M's gates and neighbour lists; an id no entity has (stock has them) goes to a free one
    A.head = kl_scene.remap_refs(A.head, sorted(room_cells), refs_m, missing=A.ref_slots)
    log('  M nodes: %s; %d KEYS blocks moved by %#x; %d REF cells in gates / lists' % (dict(count), nkeys, shift, len(room_cells)))

    # Heroes!: S's nodes at M's places
    placed = 0
    m_top = {M.prp.names[t]: t for t in M.prp.tops()}
    for t in s_tops:
        name = S.prp.names[t]
        if name.startswith('Heroes!') and name in m_top:
            src = units(M.prp.nodes[m_top[name]]['props'][1:-1])
            lab = labels(S.prp.cls(t))
            if lab != labels(M.prp.cls(m_top[name])):
                continue
            def fn(us):
                for l in ('ZGEOM[1]', 'ZGEOM[2]'):
                    us[lab.index(l)] = list(src[lab.index(l)])
            edit(Jn.nodes[at[id(S.prp), t]], 'props', fn)
            S.ents[t - 1].rot, S.ents[t - 1].trans = M.ents[m_top[name] - 1].rot, M.ents[m_top[name] - 1].trans
            placed += 1
    log('  Heroes! groups placed where %s has them: %d' % (m_name, placed))

    # ---- speech triggers without their line (after every edit that goes by controller index)
    cut = collections.Counter()
    for k in range(1, len(Jn.nodes)):
        keep = [c for c in Jn.nodes[k]['ctrls'] if not mute_speech(Jn, c, S['.SND'])]
        cut['M' if Jn.origin[k][0] is M.prp else 'S'] += len(Jn.nodes[k]['ctrls']) - len(keep)
        Jn.nodes[k]['ctrls'] = keep
    if sum(cut.values()):
        note('OnlineSpeakTrigger controllers removed, their line is not in the .SND of %s: %s' % (s_name, dict(cut)))

    # ---- FDX (bone dynamics of the map's hanging objects)
    A.fdx = None
    if B.fdx is not None:
        block = MB.fdx_join([(M['.buf'], B.fdx, cmap)])
        if block:
            A.head += bytes(-len(A.head) % 16)
            A.fdx = len(A.head)
            A.head += block + bytes(-len(block) % 16)
    # surface table: S's; every REF must still be there
    table = MB.SurfaceTable(A.tail)
    gone = table.refs() - {e.ref for e in final}
    if gone:
        note('surface table: %d effects were in %s\'s map and are cleared' % (len(gone), s_name))
        table.remap({e.ref: e.ref for e in final}, missing=MB.NONE)
        A.tail = table.serialize()
    gms, buf = A.write()

    # ---- the members no id space module covers
    refs_s = {e.ref: e.ref for e in s_kept}
    hvk = kl_hvk.join([(kl_hvk.Hvk(M['.HVK']), refs_m)], (kl_hvk.Hvk(S['.HVK']), refs_s)).serialize()
    sgd = MB.sgd_join([(M['.sgd'], refs_m), (S['.sgd'], refs_s)])
    s_names = {S.prp.names[t] for t in s_tops}
    m_names = {M.prp.names[t] for t in m_tops}
    room_paths = [Jn.path[k][5:] for k in range(1, len(Jn.nodes)) if is_room(Jn.tids[k])]
    sgp = MB.Sgp.join([(MB.Sgp(M['.sgp']), lambda p: p.split('\\')[0] in m_names),
                       (MB.Sgp(S['.sgp']), lambda p: p.split('\\')[0] in s_names)], room_paths).serialize()
    body = [k for k, v in sch.geoms.items() if v == 'ZHavokRigidBody']
    nb = lambda ents: sum(e.tid in body for e in ents)
    hrd = MB.hrd_join([(M['.hrd'] if '.hrd' in M.ext else None, nb(M.ents), nb(copy)),
                       (S['.hrd'] if '.hrd' in S.ext else None, nb(S.ents), nb(s_kept))])
    if hrd is None:
        note('.hrd left out: the rigid bodies do not all come from one level')
    # animations: one file that has every set the joined .prp names
    used = {s for s in Jn.p.keys if s.startswith(kl_anm.PREFIX)}
    anm = None
    for lv in ((S,) if M.dm else (M, S)):                # Dead Men's .ANM has another clip header
        have = {c.name for c in kl_anm.Anm(lv['.ANM'], 'dd').cols}
        if anm is None and used <= have:
            anm = lv
        log('  .ANM of %s lacks %s' % (lv.name, sorted(x[len(kl_anm.PREFIX):] for x in used - have) or 'nothing the level names'))
    if anm is None:
        anm = S
        note('no single .ANM has every animation set; %s\'s is used' % s_name)

    union = os.path.join(workdir(), 'build', 'shared', 'union.fxc')    # Dead Men has no cache of its own
    fxc = T.merge_fxc(S['.fxc'], M['.fxc'] if '.fxc' in M.ext else open(union, 'rb').read())
    out = {'.gms': kl_gms.pack(gms), '.buf': buf, '.prp': Jn.p.serialize(), '.prm': prm_bytes,
           '.TEX': T.write_tex(tex), '.MAT': T.write_mat(mat), '.fxc': fxc,
           '.oct': octj.pack(), '.rmi': index['.rmi'], '.rmc': index['.rmc'], '.HVK': hvk, '.sgd': sgd,
           '.sgp': sgp, '.hrd': hrd, '.ANM': anm['.ANM']}
    members = []
    for n in S.order:                                   # S's archive order; everything else is S's
        ext = n.rsplit('_Main', 1)[1] if '_Main' in n else None
        data = out.get(ext, S.files[n]) if ext else S.files[n]
        if data is not None:
            members.append((member_name(n, s_name, slot), data))
    problems = verify(dict(out, snd=S['.SND']), Jn, S, M, copy, s_kept, mj, shift, log)
    for p in problems:
        log('  PROBLEM: ' + p)
    log('verify: problems: %d' % len(problems))
    path = write_level(slot, members, {e: stock_beside(s_name, e) for e in BESIDE}, log)
    with open(os.path.join(out_dir(slot), 'graft.txt'), 'w') as f:
        f.write('%s systems + %s map (%s)\nproblems: %d\n%s\n' % (s_name, m_name, sel, len(problems), '\n'.join(problems + notes)))
    return path, problems


# ------------------------------------------------------------------ verification
def verify(out, Jn, S, M, copy, s_kept, mj, shift, log=print):
    """Re-read every written member with its module and follow every cross-reference this file
    knows. Returns the problems ([] = install)."""
    sch, bad = J.schema('dd'), []
    # .gms / .buf
    sc = kl_scene.Scene(kl_gms.unpack(out['.gms']), out['.buf'])
    bad += sc.check()
    g2, b2 = sc.write()
    if kl_gms.pack(g2) != out['.gms'] or b2 != out['.buf']:
        bad.append('.gms / .buf do not round-trip')
    ents = list(sc.entities())
    slot = sc.slots()
    by_slot = {v + 2: e for e, v in slot.items()}
    by_ref = {e.ref: e for e in ents}
    head = len(sc.head)
    # .prp
    data, misfits, paths, names = J.check(Jn, log=lambda *_a: None)
    if data != out['.prp']:
        bad.append('.prp changed after it was written')
    bad += ['%s: %s: %s' % (Jn.path[k], what, why) for k, what, why in misfits[:10]]
    bad += ['scene path does not resolve: %s %s -> %s' % (h, f, s) for _k, h, f, s in paths[:10]]
    # stock Dog Days levels carry 0..18 emitter names without a template (kl_prpjoin); Dead Men's
    # Impacts_Default_Smoke has no Dog Days template
    base_names = max(len(J.dangling(M.prp)[1]), 18)
    twice = [n for n, c in collections.Counter(Jn.names[k] for k in Jn.tops()).items() if c > 1]
    if twice:
        bad.append('%d top-level names are used twice, e.g. %s' % (len(twice), twice[0]))
    if len(names) > base_names:
        bad.append('%d particle template names do not resolve (stock %s: %d)' % (len(names), M.name, base_names))
    p = Prp(out['.prp'])
    nodes = p.nodes()
    if len(nodes) != len(ents) + 1 or Jn.names[1:] != [e.name.decode('latin1') for e in ents] or Jn.tids[1:] != [e.tid for e in ents]:
        bad.append('.prp nodes and .gms entities differ')
    items = collections.Counter()
    for k in range(len(Jn.nodes)):
        for nm, obj in Jn.nodes[k]['ctrls']:
            if Jn.p.key(nm) == 'InventoryBinding':
                item = [Jn.p.key(t) for t in obj if t[0] == 0x0e][0]
                items[item] += item != 'eFF2ItemNoItem'
    bad += ['item %s is bound %d times' % (k, v) for k, v in items.items() if v > 1]
    mute = sum(mute_speech(Jn, c, out['snd']) for k in range(len(Jn.nodes)) for c in Jn.nodes[k]['ctrls'])
    if mute:
        bad.append('%d OnlineSpeakTrigger name a line the .SND lacks (they delete themselves; crash at the first checkpoint)' % mute)
    # .prm, with the roots of the joined level
    prm = G.read(out['.prm'], 'dd')
    if G.write(prm) != out['.prm']:
        bad.append('.prm does not round-trip')
    proots = G.prp_roots(p, Jn.tids, sch, 'dd')
    geom = {w[0]: c for w, c, k in proots if w[0] != 'scene' and w[1] is None and k is None}
    wrong = sum(1 for k, e in enumerate(ents, 1) if e.model != geom.get(k, 0))
    if wrong:
        bad.append('%d entities: .gms model differs from ZGEOM[4]' % wrong)
    try:
        kinds, args = G.walk(prm, [(c, k) if k else c for _w, c, k in proots] + [e.model for e in ents if e.model])
    except ValueError as x:
        kinds, args = {}, {}
        bad.append('.prm: %s' % x)
    tex, mat = T.read_tex(out['.TEX']), T.read_mat(out['.MAT'])
    if T.write_tex(tex) != out['.TEX'] or T.write_mat(mat) != out['.MAT']:
        bad.append('.TEX / .MAT do not round-trip')
    octj = O.Oct.parse(out['.oct'])
    if octj.pack() != out['.oct']:
        bad.append('.oct does not round-trip')
    recs, seen = set(octj.record_refs()), collections.Counter()
    miss = collections.Counter()
    for i, k in kinds.items():
        for off, typ, _k in G.fields(prm, i, k, args.get(i, 0)):
            if typ == 'm' and prm.u16(i, off) not in mat.insts:
                miss['material'] += 1
            elif typ in 'tT' and prm.u32(i, off) and prm.u32(i, off) % G.SLOTS['dd'] not in tex.tex:
                miss['texture'] += 1
            elif typ == 'o':
                seen[prm.u32(i, off)] += 1
                miss['.oct record'] += prm.u32(i, off) not in recs
    bad += ['.prm names %d missing %ss' % (v, k) for k, v in miss.items() if v]
    if any(v > 1 for v in seen.values()):
        bad.append('.oct record named by two live model roots')
    if mat.refs != T.material_refs(out['.prm']):
        bad.append('.MAT ref table is not the .prm\'s')
    lost = T.used_textures(mat) - set(tex.tex)
    if lost:
        bad.append('%d material textures are not in the .TEX' % len(lost))
    if any(not (0 < c < len(prm.chunks) and len(prm.chunks[c]) == 64 and prm.u16(c, 2) == 8) for _f, c in octj.tail):
        bad.append('.oct tail names a chunk that is not a 64-byte mesh')
    # room trees: order, and every id an entity of the right kind under that room
    _e, ro = rooms_of(sc)
    if len(ro) != len(octj.rooms):
        bad.append('.oct has %d tree sets, the scene %d rooms' % (len(octj.rooms), len(ro)))
    def room_above(e):
        e = e.parent
        while e is not None and not is_room(e.tid):
            e = e.parent
        return e
    wrong = collections.Counter()
    for owner, five in zip(ro, octj.rooms):
        for ti, t in enumerate(five):
            for it in (t.items if t else ()):
                e = by_slot.get(it[0])
                if e is None:
                    wrong['no entity'] += 1
                elif room_above(e) is not owner:
                    wrong['other room'] += 1
                elif (ti == 4) != is_room(e.tid) or (ti < 4 and kl_gms.category(e.tid) != {0: 1, 1: 2, 2: 3, 3: 0}[ti]):
                    wrong['wrong tree'] += 1
            if t:
                try:
                    t.check()
                except Exception as x:
                    wrong['tree: %s' % x] += 1
    bad += ['.oct room trees: %d items: %s' % (v, k) for k, v in wrong.items()]
    for ext in ('.rmi', '.rmc'):
        ri = O.RoomIndex.parse(out[ext])
        if ri.pack() != out[ext]:
            bad.append(ext + ' does not round-trip')
        for b in ri.boxes:
            if b.room not in by_slot or not is_room(by_slot[b.room].tid):
                bad.append('%s: box names slot id %d, not a room' % (ext, b.room))
            if b.second and b.second not in by_slot:
                bad.append('%s: second id %d is no entity' % (ext, b.second))
    # .buf offsets: rooms (with their REFs), emitters, KEYS
    cells = 0
    for k in range(len(Jn.nodes)):
        cls = Jn.cls(k)
        lab = labels(cls)
        if 'ZROOM[9]' in lab:
            us = units(Jn.nodes[k]['props'][1:-1])
            ng, nl = u32(us[lab.index('ZROOM[0]')][0]), us[lab.index('ZROOM[1]')][0][1][0]
            g, l = u32(us[lab.index('ZROOM[9]')][0]), u32(us[lab.index('ZROOM[10]')][0])
            if (ng and not 16 <= g <= head - 0x74 * ng) or (nl and not 16 <= l < head):
                bad.append('%s: gates / lists outside the .buf head' % Jn.path[k]); continue
            for o in kl_scene.room_refs(out['.buf'], 'dd', g, ng, l, nl):
                v = struct.unpack_from('<I', out['.buf'], o)[0]
                cells += 1
                if (o - g) % 0x74 == 0x30 and g <= o < g + 0x74 * ng and (v not in by_ref or not is_room(by_ref[v].tid)):
                    bad.append('%s: gate leads to REF %d, not a room' % (Jn.path[k], v))
        for l in ('ZParticleEmitter[10]', 'ZParticleEmitter[11]'):
            if l in lab:
                v = u32(units(Jn.nodes[k]['props'][1:-1])[lab.index(l)][0])
                if v not in (0, 0xffffffff) and not 16 <= v < head:
                    bad.append('%s: %s outside the .buf head' % (Jn.path[k], l))
    for e in ents:
        if any(not 16 <= v < head for _p, ko in keys_tracks(e.raw) for v in ko):
            bad.append('%r: KEYS offset outside the .buf head' % e)
    # grafted KEYS tracks and room data still read the bytes M had
    mh = len(M.scene.head)
    if shift is not None and out['.buf'][shift:shift + 16] != M['.buf'][:16]:
        bad.append('M\'s .buf head is not at the shift')
    # other members
    h = kl_hvk.Hvk(out['.HVK'])
    if h.serialize() != out['.HVK']:
        bad.append('.HVK does not round-trip')
    stray = sum(1 for s in h.shapes for i in s.inst if kl_hvk.ref(i) not in by_ref)
    if stray:
        bad.append('.HVK: %d placements name no entity' % stray)
    for name, payload in MB.sgd_read(out['.sgd']):
        if name in ('HavokShatterOctree', 'ExplodableOctree'):
            stray = sum(1 for leaf in MB.Octree(payload).leaves if leaf[0] not in by_ref)
            if stray:
                bad.append('.sgd %s: %d leaves name no entity' % (name, stray))
    g = MB.Sgp(out['.sgp'])
    if g.serialize() != out['.sgp']:
        bad.append('.sgp does not round-trip')
    want = sorted(Jn.path[k][5:] for k in range(1, len(Jn.nodes)) if is_room(Jn.tids[k]))
    if sorted(r[0] for r in g.rooms) != want:
        bad.append('.sgp rooms are not the level\'s rooms')
    table = MB.SurfaceTable(sc.tail)
    if table.refs() - set(by_ref):
        bad.append('surface table names %d entities that are gone' % len(table.refs() - set(by_ref)))
    if sc.fdx is not None:
        for r in MB.fdx_read(out['.buf'], sc.fdx)[1]:
            if kinds.get(r['model']) != 'root':
                bad.append('FDX record names chunk %d, not a model' % r['model'])
    # sound references: S's stay inside S's bank, M's are 0
    size = len(out['snd'])
    left = 0
    for k in range(1, len(Jn.nodes)):
        from_m = Jn.origin[k][0] is M.prp
        for cls, holder, key in objects(Jn, k):
            fs = sch.fields(cls)
            for f, u in zip(fs, units(get_obj(holder, key)[1:-1])):
                if f.type in SOUND_TYPES and f.kind == 'I' and u32(u[0]):
                    left += from_m
                    if u32(u[0]) >= size:
                        bad.append('%s: sound reference beyond the .SND' % Jn.path[k])
    if left:
        bad.append('%d sound references of the map still point into another bank' % left)
    a = kl_anm.Anm(out['.ANM'], 'dd')
    lack = {s for s in p.keys if s.startswith(kl_anm.PREFIX)} - {c.name for c in a.cols}
    if lack:
        bad.append('animation sets the .ANM lacks: %s' % sorted(lack))
    log('  verified: %d entities, %d nodes, %d reachable chunks, %d room sets, %d gate / list REF cells, %d textures, %d materials' % (
        len(ents), len(nodes), len(kinds), len(octj.rooms), cells, len(tex.tex), len(mat.insts)))
    return bad


def pairs(log=print):
    """For every S in F04..F09 (systems without dangling paths, kl_prpjoin) and every M: are the
    post-filter palettes equal, and which animation sets of M's map does S's .ANM lack."""
    pal, cols, used = {}, {}, {}
    for L in J.DD_FA:
        lv = Level(L)
        blk = dict(J.block(lv.prp))
        prm = G.read(lv['.prm'], 'dd')
        pal[L] = prm.chunks[[u32(t) for t in blk['PostFilterPalettes'] if t[0] == 9][-1]]
        cols[L] = {c.name for c in kl_anm.Anm(lv['.ANM'], 'dd').cols}
        side = J.sides(lv.prp)
        used[L] = {lv.prp.p.keys[u32(t)] for k in range(1, len(lv.prp.nodes)) if side[k] == 'map'
                   for toks in [lv.prp.nodes[k]['props']] + [b for _n, b in lv.prp.nodes[k]['ctrls']]
                   for t in toks if t[0] == 0x0c and lv.prp.p.keys[u32(t)].startswith(kl_anm.PREFIX)}
        log('%s: FDX %s, PostFilterBoxes %s' % (L, lv.scene.fdx is not None, 'PostFilterBoxes' in blk))
    for s in J.DD_FA[3:]:
        for m in J.DD_FA:
            if s != m:
                log('S %s M %s: palettes %s; map animation sets S lacks: %s' % (
                    s, m, 'equal' if pal[s] == pal[m] else 'DIFFER', sorted(x[len(kl_anm.PREFIX):] for x in used[m] - cols[s])))


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'plain':
        plain(a[1], *a[2:3])
    elif len(a) >= 3 and a[0] == 'build':
        opt = {}
        for o in ('--m-add', '--m-drop', '--s-keep', '--s-drop'):
            while o in a:
                i = a.index(o)
                opt.setdefault(o[2:].replace('-', '_'), []).extend(a[i + 1].split(','))
                del a[i:i + 2]
        g = '--geometry' in a
        a = [x for x in a if x != '--geometry']
        sys.exit(1 if build(a[1], a[2], *a[3:4], sel=Select(g, **opt))[1] else 0)
    elif a and a[0] == 'install':
        install(*a[1:2])
    elif a and a[0] == 'pairs':
        pairs()
    else:
        print(__doc__)
