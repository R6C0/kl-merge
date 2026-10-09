#!/usr/bin/env python3
"""
Lighting of a grafted Dead Men map under Dog Days: what the level files hold, what differs from
every stock Dog Days level, and the normalisation the graft applies. Full account: re/lighting.md.

    python kl_light.py survey F09 M03_FA_A ...   every ZENVIRONMENT of a stock level: record, bits,
                                                 rooms, character link, and whether stock Dog Days
                                                 has that combination
    python kl_light.py catalogue                 recompute STOCK from the 21 stock Dog Days levels
    python kl_light.py test [maps]               the offline tests (see test()); 'problems: 0'

WHAT IS IN THE FILES (both games alike unless said; addresses kl2.exe / kaneandlynch.exe)
  light record   the .prm chunk a light entity names (.gms record +0x0c = ZGEOM[4]), lType 12:
                 +0x0c type (low word: 0 spot 64 B, 1 omni 48 B, 2 square spot 80 B, 3 ambient
                 environment, 4 directional environment; high word: flag bits), +0x10 colour
                 0x00RRGGBB, +0x14 intensity (float), +0x1c colour 2, +0x20 colour 3,
                 +0x24 byte 'directional' (1 in every type 4 record, 0 in every type 3 record:
                 763 of 763). Readers 0x8c9690 / 0x7bed90 take: not directional -> ambient =
                 colour * intensity; directional -> light = colour * intensity along the entity's
                 rotation, ambient = colour 3 * intensity.
  ZLIGHT         .prp fields: [0] bool -> object +0x10 bit 4, [1] reference list -> +0x14 (each
                 resolved object is handed to the light manager with the light, 0x46b7e0),
                 [2] reference list -> +0x1c (setter 0x638bb0 keeps only objects of one class).
                 In Dead Men [2] names the light's ZSHADOWMESHOBJ entities ('Light7_<lamp>_
                 <room>_Chunk0': 128-byte static-shadow meshes; M03_FA_A: 46 names, all of that
                 class, and 44 empty strings on the sun); 202 of 5,364 lights have it. In Dog
                 Days [2] is EMPTY ON ALL 18,944 LIGHTS (F07 and F09 have no 128-byte mesh
                 either). While the graft retyped ZSHADOWMESHOBJ to ZSTDOBJ every reference
                 named an object of the wrong class and the setter stored null for each (that is
                 the state the dark screenshots were taken in); since 2026-10-09 kl_gms keeps the
                 class, so the 46 real references resolve again - a list no stock Dog Days light
                 has, read by code that was not located.
  ZENVIRONMENT   [0..3] bools -> object +0x10 bits 0x1000, 0x4000, 0x8000, 0x2000 (same getters
                 in both exes), [4..7] colours -> +0x28..+0x34 (0 = take colour / colour 3 of the
                 record, 0x5683d0).
                 CHARACTER LINK, BY NAME (0x5683d0, Dead Men 0x4f7170, vtable slot 82 / 83): an
                 environment with neither bit 0x4000 nor 0x8000 looks among its siblings for
                 ZENVIRONMENTs named '*_env_character*' (matcher 0x8dfa90 uses _memicmp: case
                 does not matter) and stores one with bit 0x4000 at +0x20, one with bit 0x8000 at
                 +0x24. An environment that has either bit never searches.
  room pairs     .gms header +0x28 (kl_scene): one environment per room. 797 pairs.
  list pool      light <-> geometry lists (kl_scene); none belongs to an environment (0 of 763).
  baked light    Dead Men only: a 'lit' vertex stream (8 bytes per vertex: ff ff ff AA, then a
                 colour that is mostly 0) and a shared 16-byte record {number, colour}. A level
                 has as many distinct records as ZAMBIENTOCCLUSION objects (M02_FA_A 6 / 6,
                 M03_FA_A 6 / 6, M09_A 4 / 4, M09_B 5 / 5; M01_FA_A has neither), and each such
                 object lists rooms. ZAMBIENTOCCLUSION overrides nothing of ZLIST but its class
                 info (vtable slots 11-14, both exes): inert at run time, the build tool's "bake
                 these rooms" list. INFERENCE from that (the shader was not read): the stream is
                 baked AMBIENT OCCLUSION, a per-vertex factor that only ever darkens, so dropping
                 it (kl_prm) cannot be what makes a map dark. No Dog Days mesh has the stream
                 (0 of 94,851, kl_prm) and no Dog Days level a ZAMBIENTOCCLUSION (0 of 21);
                 a Dog Days descriptor has no field for it.
                 A second baked form was NOT examined: the 128-byte static-shadow meshes, some
                 named '<room>_Chunk0_Additive_Light_Tex0' (both exes hold the shader names
                 mapLightmap and v4LightMapColor). They come along as plain objects.

WHY THE GRAFTED BANK IS DARK - what is established and what is not
  Established: lights, room pairs and light lists of M03_FA_A all survive the graft (0 lists and
  0 pairs of M lost; 18 pairs, 10,566 list elements), and the light classes have the same
  fields in both games. What M03_FA_A has and M01_FA_A (which looks right) has not, outdoors:
    M01  rooms -> 'Environment#Character', type 3, bits 0x4000 + 0x8000, entity flags 0x80; the
         type 4 sun 'Environment#01' is paired with no room.
    M03  rooms -> 'Environment_env', TYPE 4, NO bit, ENTITY FLAGS 0x10080, 44 dangling ZLIGHT[2]
         entries, and by the name rule linked to 'Environment_env_character', a TYPE 3 light.
  No stock Dog Days level has either property of M03's:
    - a directional (type 4) environment linked to a non-directional (type 3) character light:
      0 of 260 linked environments (type 3 + 4: 247, 4 + 4: 11, 3 + 3: 2);
    - a paired type 4 environment with entity flag 0x10000 and bit 0x8000 clear: 0 of 44
      (the flag is on 9, all with bit 0x8000: F09's street suns; the other 35 have neither).
  NOT established (the renderer was not read, and nothing was run): which of the two makes the
  characters black and the map sunless. normalise() therefore removes both, and ZLIGHT[2], by
  turning each such environment into a combination stock Dog Days has.

WHAT normalise() DOES (each rule changes nothing in any of the 21 stock levels: test())
  R1  ZLIGHT[2] of every light of the map loses the references that name no ZSHADOWMESHOBJ
      (empty strings, retyped objects): they only make null entries. shadows='none' empties
      the list altogether (stock: always empty), 'keep' leaves it.
  R2  a paired type 4 environment without bit 0x4000 / 0x8000 but with entity flag 0x10000 gets
      ZENVIRONMENT[2] (bit 0x8000): the form of F09's street suns ('_Lights!Environment_Sun',
      bits 1011, flags 0x10080, 9 of them). With the bit it no longer searches for a character
      light, so its link goes too. ASSUMPTION: the flag means in Dog Days what it does on those
      suns; what bit 0x8000 does beyond the link rule is not known.
  R3  a paired type 4 environment WITHOUT that flag that would link to a type 3 character light:
      that light loses bits 0x4000 / 0x8000 (so it is no longer taken; stock has 7 unpaired
      plain type 3 environments). Characters are then lit by the room's own environment, as in
      F02 / F05 / F09.
  links='m01' instead of R2 / R3: the rooms of such an environment are paired with its character
      light, which is exactly M01_FA_A's outdoor layout (the one grafted map seen to look right):
      flat ambient, no sun. The fallback if the default still comes out dark.
  links='keep': R1 only.
NOT DONE: whether Dead Men's static shadow meshes (57 in M01, 97 in M03) draw correctly in Dog
Days, as ZSHADOWMESHOBJ or retyped, was not examined; the sun of M01 stays unpaired (as Dead Men has it).

CALL FOR kl_graft.build - after the 'Heroes!' block, before 'gms, buf = A.write()':
    import kl_light
    rep = kl_light.normalise(Jn, A, prm, nodes=set(mj.values()), log=log)
and in verify(), on the re-read files (sc = the kl_scene.Scene, prm = the .prm read there):
    bad += kl_light.check(Jn, sc, prm, nodes=set(mj.values()))
Jn = joined kl_prpjoin.Scene, A = joined kl_scene.Scene (entity k - 1 of A.entities() is node k),
prm = joined kl_prmgraph.Prm (only read). It edits Jn's tokens, entity flags and A.pairs.
"""
import collections, fnmatch, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prpjoin as J
from kl_prp import units

ENV_AMBIENT, ENV_SUN = 3, 4                # light record +0x0c, low word
CHARACTER = '*_env_character*'             # kl2 0xb87e14, matched without regard to case
CASTS = 0x10000                            # entity flag (.gms record +0x1c); see R2
B_CHAR, B_CHAR2 = 1, 2                     # ZENVIRONMENT[1] (bit 0x4000), ZENVIRONMENT[2] (bit 0x8000)
DD_LEVELS = ['F%02d' % i for i in range(1, 10)] + ['L%02d' % i for i in range(12)]

# Every combination the 21 stock Dog Days levels hold, with its count ('catalogue' prints this).
# main: ('main', type, entity flag 0x10000, paired with a room, type of the +0x20 character light
#        or 0, type of the +0x24 one or 0)
# char: ('char', type, bit 0x4000, bit 0x8000, entity flag 0x10000, paired with a room)
STOCK = {
    ('char', 3, 0, 1, False, True): 1,
    ('char', 3, 1, 0, False, False): 2,
    ('char', 3, 1, 0, False, True): 2,
    ('char', 3, 1, 1, False, False): 1,
    ('char', 3, 1, 1, False, True): 4,
    ('char', 4, 0, 1, True, True): 9,
    ('char', 4, 1, 0, False, False): 260,
    ('char', 4, 1, 0, False, True): 4,
    ('char', 4, 1, 0, True, False): 3,
    ('char', 4, 1, 1, False, False): 3,
    ('main', 3, False, False, 0, 0): 6,
    ('main', 3, False, False, 4, 0): 1,
    ('main', 3, False, True, 0, 0): 54,
    ('main', 3, False, True, 3, 0): 2,
    ('main', 3, False, True, 4, 0): 229,
    ('main', 3, False, True, 4, 4): 2,
    ('main', 3, True, False, 0, 0): 1,
    ('main', 3, True, True, 4, 0): 15,
    ('main', 4, False, True, 0, 0): 20,
    ('main', 4, False, True, 4, 0): 11,
}


def record(chunk):
    """A light record: dict(type, high, colour, intensity, colour2, colour3, directional)."""
    if chunk[:4] != b'\0\0\x0c\0' or len(chunk) < 48:
        raise ValueError('not a light record')
    t, col, inten, _w, c2, c3, d = struct.unpack_from('<IIfIIIB', chunk, 12)
    return dict(type=t & 0xffff, high=t >> 16, colour=col, intensity=inten, colour2=c2, colour3=c3, directional=bool(d))


def _is(sc, k, base):
    sch = J.schema(sc.game)
    return base in sch.bases(sc.cls(k) or '')


def _fields(sc, k):
    """{label: unit} of node k's own object."""
    return dict(zip(J.labels(sc.game, sc.cls(k)), units(sc.nodes[k]['props'][1:-1])))


def _edit(sc, k, changes):
    """Replace fields of node k: {label: unit tokens}."""
    obj = sc.nodes[k]['props']
    lab = J.labels(sc.game, sc.cls(k))
    us = [list(u) for u in units(obj[1:-1])]
    for name, unit in changes.items():
        us[lab.index(name)] = list(unit)
    sc.nodes[k]['props'] = [obj[0]] + [t for u in us for t in u] + [obj[-1]]


class Env:
    """One ZENVIRONMENT: node k, its entity, record and what the engine's rules make of it."""

    def __init__(self, sc, k, ent, prm):
        f = _fields(sc, k)
        self.k, self.ent, self.name, self.parent = k, ent, sc.names[k], sc.parent[k]
        self.bits = tuple(f['ZENVIRONMENT[%d]' % i][0][1][0] for i in range(4))
        self.refs2 = len(f['ZLIGHT[2]']) - 1
        self.rec = record(prm.chunks[ent.model]) if ent.model else None
        self.type = self.rec['type'] if self.rec else 0
        self.rooms, self.link, self.link2 = [], None, None      # filled by environments()

    char = property(lambda s: bool(s.bits[B_CHAR] or s.bits[B_CHAR2]))
    named = property(lambda s: fnmatch.fnmatchcase(s.name.lower(), CHARACTER))
    casts = property(lambda s: bool(s.ent.flags & CASTS))

    def key(self):
        if self.char:
            return ('char', self.type, self.bits[B_CHAR], self.bits[B_CHAR2], self.casts, bool(self.rooms))
        return ('main', self.type, self.casts, bool(self.rooms), self.link.type if self.link else 0,
                self.link2.type if self.link2 else 0)

    def __str__(self):
        r = self.rec or {}
        return '%-34s T%d %06x x %-4.2f c2 %06x c3 %06x bits %s flags %#x rooms %d%s%s%s' % (
            self.name[:34], self.type, r.get('colour', 0), r.get('intensity', 0), r.get('colour2', 0), r.get('colour3', 0),
            ''.join(map(str, self.bits)), self.ent.flags, len(self.rooms),
            ' ZLIGHT[2] %d' % self.refs2 if self.refs2 else '',
            ' -> +0x20 %s (T%d)' % (self.link.name, self.link.type) if self.link else '',
            ' -> +0x24 %s (T%d)' % (self.link2.name, self.link2.type) if self.link2 else '')


def environments(sc, scene, prm, nodes=None):
    """Every ZENVIRONMENT of a level (of `nodes` only, if given) with rooms and character links
    worked out as the engine does (kl2 0x5683d0: siblings named '*_env_character*', the last one
    with the bit wins). sc: kl_prpjoin.Scene, scene: kl_scene.Scene, prm: kl_prmgraph.Prm."""
    ents = list(scene.entities())
    if len(ents) != len(sc.nodes) - 1:
        raise ValueError('.prp and .gms disagree on the entities')
    out = [Env(sc, k, ents[k - 1], prm) for k in range(1, len(sc.nodes))
           if sc.cls(k) == 'ZENVIRONMENT' and (nodes is None or k in nodes)]
    by_ent = {e.ent: e for e in out}
    for room, env in scene.pairs:
        if env in by_ent:
            by_ent[env].rooms.append(room)
    sibs = collections.defaultdict(list)
    for e in out:
        sibs[e.parent].append(e)
    for e in out:
        if e.char:
            continue
        for c in sibs[e.parent]:
            if c is not e and c.named:
                if c.bits[B_CHAR]:
                    e.link = c
                if c.bits[B_CHAR2]:
                    e.link2 = c
    return out


def lights(sc, nodes=None):
    return [k for k in range(1, len(sc.nodes)) if (nodes is None or k in nodes) and _is(sc, k, 'ZLIGHT')]


def shadow_refs(sc, k):
    """ZLIGHT[2] of light k as (tokens that name a ZSHADOWMESHOBJ of the level, number of the
    others). The setter (kl2 0x638bb0) stores null for the others."""
    good, dead = [], 0
    for t in _fields(sc, k)['ZLIGHT[2]'][1:]:
        hit = sc.resolve(sc.p.key(t)) if t[0] == 0x0c else []
        if any(sc.cls(j) == 'ZSHADOWMESHOBJ' for j in hit):
            good.append(t)
        else:
            dead += 1
    return good, dead


def normalise(sc, scene, prm, nodes=None, links='stock', shadows='valid', log=print):
    """Bring the lights of a Dead Men map (nodes: its node numbers; None = the whole level) into
    forms stock Dog Days has: R1 - R3 of the module docstring. links: 'stock' (R2 + R3), 'm01'
    (rooms of a sun with a type 3 character light go to that light), 'keep' (R1 only).
    shadows: 'valid' (R1: ZLIGHT[2] keeps only references to a ZSHADOWMESHOBJ), 'none' (emptied,
    as every stock Dog Days light), 'keep'.
    Returns a report dict; 'unknown' lists what still fits no stock combination."""
    if links not in ('stock', 'm01', 'keep') or shadows not in ('valid', 'none', 'keep'):
        raise ValueError('links: stock, m01 or keep; shadows: valid, none or keep')
    rep = dict(lights=0, refs_cleared=0, refs_kept=0, lights_cleared=0, suns_flagged=[], unlinked=[], repaired=[], unknown=[])
    for k in lights(sc, nodes):
        rep['lights'] += 1
        good, dead = shadow_refs(sc, k)
        if shadows == 'none':
            good, dead = [], dead + len(good)
        if dead and shadows != 'keep':                  # R1
            _edit(sc, k, {'ZLIGHT[2]': [(0x04, struct.pack('<I', len(good)))] + good})
            rep['refs_cleared'] += dead; rep['lights_cleared'] += 1
        rep['refs_kept'] += len(good)
    yes, no = [(0x06, b'\x01')], [(0x06, b'\x00')]
    for e in environments(sc, scene, prm, nodes):
        if e.char or e.type != ENV_SUN or not e.rooms:
            continue
        odd_link = e.link is not None and e.link.type == ENV_AMBIENT
        if links == 'm01':
            if odd_link:
                # M01_FA_A's layout: the rooms take the character light, the sun is left alone
                scene.pairs[:] = [(r, e.link.ent if env is e.ent else env) for r, env in scene.pairs]
                rep['repaired'].append((e.name, e.link.name, len(e.rooms)))
        elif links == 'stock':
            if e.casts:                                 # R2
                _edit(sc, e.k, {'ZENVIRONMENT[2]': yes})
                rep['suns_flagged'].append(e.name)
            elif odd_link:                              # R3
                _edit(sc, e.link.k, {'ZENVIRONMENT[1]': no, 'ZENVIRONMENT[2]': no})
                rep['unlinked'].append((e.name, e.link.name))
    rep['unknown'] = [(e.name, e.key()) for e in environments(sc, scene, prm, nodes) if e.key() not in STOCK]
    log('  lights: %d of the map; ZLIGHT[2]: %d dead references removed on %d lights, %d kept; suns given bit 0x8000: %s; '
        'character lights unlinked: %s; rooms re-paired: %s; environments in no stock form: %s' % (
            rep['lights'], rep['refs_cleared'], rep['lights_cleared'], rep['refs_kept'], rep['suns_flagged'] or 'none',
            rep['unlinked'] or 'none', rep['repaired'] or 'none', rep['unknown'] or 'none'))
    return rep


def check(sc, scene, prm, nodes=None, strict=False):
    """Problems of a level's lights under the Dog Days rules this module knows: every light fits
    its class, names a light record of its kind and has no dead ZLIGHT[2] entry; every pair joins a room to
    an environment; no directional environment is linked to a non-directional character light,
    none has entity flag 0x10000 without bit 0x8000 while paired. strict: also every environment
    must be in a combination stock has (an unpaired sun, as M01_FA_A keeps, fails that)."""
    sch, bad = J.schema(sc.game), []
    ents = list(scene.entities())
    size = {'ZSPOTLIGHT': 64, 'ZSPOTLIGHTSQUARE': 80}
    for k in lights(sc, nodes):
        why = sch.misfit(sc.cls(k), sc.nodes[k]['props'])
        if why:
            bad.append('%s: %s' % (sc.path[k], why)); continue
        if shadow_refs(sc, k)[1]:
            bad.append('%s: ZLIGHT[2] holds %d references that name no ZSHADOWMESHOBJ' % (sc.path[k], shadow_refs(sc, k)[1]))
        e = ents[k - 1]
        try:
            r = record(prm.chunks[e.model])
        except (ValueError, IndexError):
            bad.append('%s: no light record at chunk %d' % (sc.path[k], e.model)); continue
        want = next((v for c, v in size.items() if c in sch.bases(sc.cls(k))), 48)
        if len(prm.chunks[e.model]) != want:
            bad.append('%s: light record of %d bytes, class wants %d' % (sc.path[k], len(prm.chunks[e.model]), want))
        if sc.cls(k) == 'ZENVIRONMENT' and (r['type'] not in (ENV_AMBIENT, ENV_SUN) or r['directional'] != (r['type'] == ENV_SUN)):
            bad.append('%s: environment record of type %d, directional %d' % (sc.path[k], r['type'], r['directional']))
    node = {e: k for k, e in enumerate(ents, 1)}
    for room, env in scene.pairs:
        if env not in node or sc.cls(node[env]) != 'ZENVIRONMENT':
            bad.append('room pair names something that is not an environment')
        elif nodes is not None and node[env] in nodes and room is not None and node[room] not in nodes:
            bad.append('room pair crosses the systems / map cut')
    for e in environments(sc, scene, prm, nodes):
        if not e.char and e.type == ENV_SUN and e.rooms:
            if e.link is not None and e.link.type == ENV_AMBIENT:
                bad.append('%s: directional environment linked to the ambient character light %s' % (sc.path[e.k], e.link.name))
            if e.casts:
                bad.append('%s: paired sun with entity flag 0x10000 but without bit 0x8000' % sc.path[e.k])
        if strict and e.key() not in STOCK:
            bad.append('%s: %r is in no stock Dog Days level' % (sc.path[e.k], e.key()))
    return bad


# ------------------------------------------------------------------ stock levels
def load(level, game=None):
    """(kl_prpjoin.Scene, kl_scene.Scene, kl_prmgraph.Prm) of a stock level of either game, as
    stored (a Dead Men level is NOT converted: its light fields are the same)."""
    import zipfile, kl_gms, kl_scene, kl_prmgraph as G
    game = game or ('dm' if level.startswith('M') else 'dd')
    sc = J.Scene.load(level, game)
    with zipfile.ZipFile(J.level_zip(level, game)) as z:
        f = {n.rsplit('_Main', 1)[1]: z.read(n) for n in z.namelist()
             if '_Main' in n and n.rsplit('_Main', 1)[1] in ('.gms', '.buf', '.prm')}
    return sc, kl_scene.Scene(kl_gms.unpack(f['.gms']), f['.buf']), G.read(f['.prm'], game)


def catalogue(levels=DD_LEVELS):
    out = collections.Counter()
    for lv in levels:
        out.update(e.key() for e in environments(*load(lv)))
    return dict(out)


def survey(level, log=print):
    sc, scene, prm = load(level)
    envs = environments(sc, scene, prm)
    n2 = sum(1 for k in lights(sc) if len(_fields(sc, k)['ZLIGHT[2]']) > 1)
    log('%s: %d lights, %d with ZLIGHT[2]; %d environments, %d room pairs' % (level, len(lights(sc)), n2, len(envs), len(scene.pairs)))
    for e in envs:
        log('  %s  %s' % (e, 'stock x%d' % STOCK[e.key()] if e.key() in STOCK else 'NOT IN STOCK %r' % (e.key(),)))
    return envs


def test(maps=('M01_FA_A', 'M03_FA_A'), log=print):
    """1. STOCK equals a fresh catalogue. 2. normalise() changes nothing in any stock Dog Days
    level and check() passes them all. 3. each Dead Men map (as the graft sees it:
    kl_graft.DeadMen) is normalised in both modes; the result fits the Dog Days schema, passes
    check(), survives a .gms / .buf / .prp write and re-read, and keeps every light, pair and
    record. Returns the number of problems."""
    import copy, kl_graft, kl_gms, kl_scene
    from kl_prp import Prp
    quiet = lambda *_a: None
    bad = 0
    fresh = catalogue()
    if fresh != STOCK:
        bad += 1; log('PROBLEM: STOCK is stale: run "kl_light.py catalogue"')
    for lv in DD_LEVELS:
        sc, scene, prm = load(lv)
        before, pairs = sc.p.serialize(), list(scene.pairs)
        flags = [e.flags for e in scene.entities()]
        rep = normalise(sc, scene, prm, log=quiet)
        same = sc.p.serialize() == before and scene.pairs == pairs and [e.flags for e in scene.entities()] == flags
        probs = check(sc, scene, prm, strict=True)
        bad += (not same) + len(probs)
        log('%s: %d lights, unchanged by normalise: %s, check problems: %d' % (lv, rep['lights'], same, len(probs)))
        for p in probs[:5]:
            log('  PROBLEM: ' + p)
    for name in maps:
        for mode in ('stock', 'm01'):
            lv = kl_graft.DeadMen(name, log=quiet)
            sc, scene, prm = lv.prp, lv.scene, kl_graft.G.read(lv['.prm'], 'dd')
            was = check(sc, scene, prm)
            n_l, n_p = len(lights(sc)), len(scene.pairs)
            rep = normalise(sc, scene, prm, links=mode, log=quiet)
            probs = check(sc, scene, prm)
            # write and read back
            data = sc.p.serialize()
            gms, buf = scene.write()
            sc2 = J.Scene(Prp(data), sc.names, sc.tids, 'dd', name)
            scene2 = kl_scene.Scene(kl_gms.unpack(kl_gms.pack(gms)), buf)
            probs += scene2.check()
            probs += check(sc2, scene2, prm)
            if len(lights(sc2)) != n_l or len(scene2.pairs) != n_p:
                probs.append('lights or pairs lost')
            if [str(e) for e in environments(sc2, scene2, prm)] != [str(e) for e in environments(sc, scene, prm)]:
                probs.append('environments differ after the re-read')
            bad += len(probs)
            log('%s, links=%s: check before %d, after %d; %s' % (name, mode, len(was), len(probs), {k: v for k, v in rep.items() if v}))
            for p in probs[:8]:
                log('  PROBLEM: ' + p)
            if mode == 'stock':
                for e in environments(sc2, scene2, prm):
                    log('    %s  %s' % (e, 'stock x%d' % STOCK[e.key()] if e.key() in STOCK else 'not in stock'))
    log('problems: %d' % bad)
    return bad


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'survey':
        for lv in a[1:]:
            survey(lv)
    elif a and a[0] == 'catalogue':
        for k, v in sorted(catalogue().items(), key=str):
            print('    %r: %d,' % (k, v))
    elif a and a[0] == 'test':
        sys.exit(1 if test(*([tuple(a[1:])] if a[1:] else [])) else 0)
    else:
        print(__doc__)
