#!/usr/bin/env python3
"""
Lighting of a grafted Dead Men map under Dog Days: what the level files hold, what differs from
every stock Dog Days level, and the normalisation the graft applies. Full account: re/lighting.md.

    python kl_light.py survey F09 M03_FA_A ...   every ZENVIRONMENT of a stock level: record, bits,
                                                 rooms, character link, and whether stock Dog Days
                                                 has that combination
    python kl_light.py catalogue                 recompute STOCK from the 21 stock Dog Days levels
    python kl_light.py test [maps]               the offline tests (see test()); 'problems: 0'
    python kl_light.py render-test [maps]        tests of the three steps below (test_render())
    python kl_light.py refit <build> <out>       a kept build with fit_shaders() run again on its .MAT
                                                 (scratch folders only; nothing is installed)

THREE MORE STEPS (2026-10-09, second pass; the renderer was read this time: compiled effects of
the .fxc, Dead Men's shipped .fx sources, kl2.exe). Each is optional and separate; the reasons are
in the comment above each function and in re/lighting.md, the calls for kl_graft at the end of
this text.
  fit_shaders       materials that ask for a shader permutation no cache entry has are NOT DRAWN
                    (kl2 0x8b8fd0 returns 0, 0x50c2ff skips the layer). The installed bank build
                    has 35 such materials on 920 objects (walls 'Stone_Pillar_06a_M03' x468, all
                    Dead Men cars). The cheapest feature switches are turned off until an entry fits.
                    Where no set of switches fits (the class has no permutation that plain: Dead
                    Men's far-detail police uniform 'Characters/_JPN/JPN_Police_LOD3' is SkinCloth
                    with neither bump nor specular, and Dog Days compiled Cloth / Skin only with
                    specular) the instance is rebuilt as a Standard/Standard material: plain_twin().
                    That one material made 13 policemen of the Retomoto street vanish beyond close
                    range (re/invisible.md). 'python kl_light.py refit <build> <out>' applies the
                    whole step to a build that exists (only the .MAT member changes).
  graft_postfilter  Dead Men grades each area through PostFilterBoxes (the bank: outside look-at,
                    outside dark, inside); the graft left them out because their sets index Dead
                    Men's palette. The palettes are one format: M's curves are appended to S's.
  bake_ao           Dead Men's baked lighting is an ambient-occlusion light map. No Dog Days shader
                    can read it; it is baked into the vertex colours instead (ASSUMPTIONS there).

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
  baked light    (first-pass notes; the shader source has since been read: see the comment above
                 bake_ao() - the stream is colour + light-map uv, the record a .TEX id + colour.)
                 Dead Men only: a 'lit' vertex stream (8 bytes per vertex: ff ff ff AA, then a
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

CALLS FOR THE THREE STEPS (kl_graft names; none is wired in yet)
  1 fit_shaders - in build(), just before "out = {'.gms': ...": the 'fxc = T.merge_fxc(...)' line
    has to stand above it, then
        kl_light.fit_shaders(mat, fxc, log=log)         # mat = the merged kl_texmat.Mat
    and in verify(), on the re-read members:
        bad += ['shaders: %s lacks %s' % (m.insts[s].name, l[0][0]) for s, l in kl_light.missing_shaders(m, fxc).items()]
    (a systems-only material that needs a switch turned ON stays unresolved and is reported;
    none is in the F07 + M03_FA_A build.)
  2 graft_postfilter - (a) take Dead Men's boxes: drop 'and not M.dm' from
        if 'PostFilterBoxes' in mblock and not M.dm:
    (b) after 'prm, cmap2 = G.append(...)' and before 'prm_bytes = G.write(prm)':
        blk = lambda lv, n: u32([t for t in dict(J.block(lv.prp))[n] if t[0] == 9][-1])
        kl_light.graft_postfilter(prm, blk(S, 'PostFilterPalettes'), prm_m.chunks[blk(M, 'PostFilterPalettes')],
                                  [cmap[i] for i, k in kinds.items() if k == 'pf'], log=log)
    It is right for a Dog Days M as well (today a Dog Days map's sets silently index S's palette).
  3 bake_ao - in DeadMen.__init__, around the kl_prm.convert line:
        dm_prm = self['.prm']
        self.files[self.ext['.prm']], rep = kl_prm.convert(dm_prm, roots)
        self.files[self.ext['.prm']], arep = kl_light.bake_ao(dm_prm, self['.prm'], roots, self['.TEX'], strength=0.5, log=log)
    BEFORE the .TEX is converted (it reads Dead Men's .TEX) and before kl_mat.convert_mat_full.
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


# ------------------------------------------------------------------ shader permutations
# A material draws through compiled effects only. kl2 0x50bac0 (class layer loader) asks 0x7113f0
# for the effect of each LAYE: defines = the mesh kind ('MESH_STANDARD' ...) + the upper-cased name
# of every BOOL of the instance that is true and not one of the six run-time switches at
# [0xcda50c] (EXCLUDED); effect file = LAYE PATH as it is when it holds '.fx', else PATH + '30.fx'.
# 0x8b8fd0 then walks the loaded cache (.fxc) and returns 0 when no entry has that file and those
# defines: nothing is compiled at run time (Dog Days ships no .fx source), and the layer loader
# skips the layer (0x50c2ff). A material none of whose layers resolves is not drawn at all.
# The model below reproduces every stock instance: 13,528 of 13,528 needed effects are in the
# level's own .fxc (test()).
EXCLUDED = ('STDCULLING', 'RIMLIGHTINGENABLED', 'ILLUMINATIONENABLED', 'SUBSURFACEENABLED', 'DIFFUSEISSPECULARMASK',
            'SPECMASKISREFLMASK')
MESH_KIND = {0: 'Standard', 1: 'Tweened', 2: 'Rigid', 3: 'Weighted'}       # .MAT entry +0x14 = SUBC STYP
# What switching a feature off costs the picture; fit_shaders() takes the cheapest set. GUESSES of
# mine, "least visible first"; anything not listed costs 3.
SWITCH_COST = {'PARALLAXENABLED': 1, 'BUMPDETAILENABLED': 1, 'USEDEFAULTREFLECTIONMAP': 1, 'ALPHAFADEENABLED': 2,
               'SCROLLENABLED': 2, 'REFRACTION2DENABLED': 3, 'REFLECTIONENABLED': 4, 'SPECULARENABLED': 5, 'BUMPENABLED': 6}


def _kid(node, tag):
    return next((c for c in node[3] if c[0] == tag), None)


def _bools(entry):
    """{upper-cased BOOL name: (node, true)} of a material instance. True = ENAB and VALU, as
    kl_mat.feature_flags reads it (VALU alone fits the stock files equally well)."""
    out = {}
    for n in _kid(entry.root, 'BIND')[3]:
        if n[0] == 'BOOL':
            e, v = _kid(n, 'ENAB'), _kid(n, 'VALU')
            out[_kid(n, 'NAME')[3].decode('latin1').upper()] = (n, bool(e and e[3] and v and v[3]))
    return out


def shader_needs(mat, entry, off=()):
    """The effects a material instance asks the cache for: {(effect file in lower case, mesh
    define, frozenset of the other defines)}. off: defines treated as switched off."""
    cls = mat.classes[entry.f[1]]
    kind = MESH_KIND.get(entry.f[5])
    if cls.cls == b'Sprites' or kind is None:           # sprites: one effect, no instance defines
        return set()
    bools = {k: v for k, (_n, v) in _bools(entry).items()}
    defs = {k for k, v in bools.items() if v and k not in EXCLUDED and k not in off}
    for n in _kid(entry.root, 'BIND')[3]:
        if n[0] == 'RSTA' and _kid(n, 'BENA') and _kid(n, 'BENA')[3]:
            defs.add('BLENDENABLED')
    out = set()
    for sub in cls.root[3]:
        if sub[0] != 'SUBC' or _kid(sub, 'STYP')[3].decode('latin1') != kind:
            continue
        cond = _kid(sub, 'VALI')
        if cond is not None and cond[1] == 3 and bool(bools.get(_kid(cond, 'BIND')[3].decode('latin1').upper())) != bool(_kid(cond, 'VALU')[3]):
            continue
        for lay in sub[3]:
            if lay[0] == 'LAYE':
                path = _kid(lay, 'PATH')[3].decode('latin1')
                out.add(((path if '.fx' in path else path + '30.fx').lower(), 'MESH_' + kind.upper(), frozenset(defs)))
    return out


def shader_cache(fxc):
    """{(effect file in lower case, mesh define, frozenset of the other defines)} of a .fxc."""
    import kl_mat, kl_texmat
    out = set()
    for head, _blob in kl_mat.read_fxc(fxc)[1]:
        d = [n for n, _v in kl_texmat.fxc_defines(head)]
        out.add((head[0x810:0x850].split(b'\0')[0].decode('latin1').lower(), d[0], frozenset(d[1:])))
    return out


def missing_shaders(mat, fxc, slots=None):
    """{instance slot: [needed effects the cache lacks]} (slots: which instances; default all).
    fxc: bytes of a .fxc, or the set shader_cache() made of one."""
    have = fxc if isinstance(fxc, (set, frozenset)) else shader_cache(fxc)
    out = {}
    for s in sorted(mat.insts if slots is None else slots):
        lack = sorted((x for x in shader_needs(mat, mat.insts[s]) if x not in have), key=str)
        if lack:
            out[s] = lack
    return out


ALWAYS_FX = {'sprite.fx'}      # in the cache of all 21 stock Dog Days levels although no material asks for it


def slim_cache(mat, fxc, log=print):
    """The cache `fxc` (bytes) without the entries nothing asks for -> (bytes, report).
    Kept, in their order: the first entry of every effect a material instance of `mat`
    (kl_texmat.Mat, as it is shipped: run fit_shaders first) asks for, and of ALWAYS_FX.
    Why this is what a level needs: measured 2026-10-10 on all 21 stock Dog Days levels, their
    1965 cache entries are exactly that - every entry is asked for by a material of its own level
    (shader_needs), except sprite.fx / SPRITES, which all 21 have; no level has a key twice.
    A grafted Dead Men map ships the systems level's cache + build/shared/union.fxc (every stock
    entry there is): Retomoto 242 entries, 16.9 MB, of which its materials ask for 129 effects =
    9.0 MB. The file is read whole into one heap block at load (klhook/klmem.c): 8 MB of address
    space. Where two entries have the same effect, file and defines the first stays - ASSUMPTION:
    the game's look-up (kl2 0x8b8fd0 walks the cache in order) takes the first too.
    NOT LOADED LIVE."""
    import kl_mat, kl_texmat
    ver, ent = kl_mat.read_fxc(fxc)
    need = set()
    for s in mat.insts:
        need |= set(shader_needs(mat, mat.insts[s]))
    out, seen, twice = [], set(), 0
    for head, blob in ent:
        d = [n for n, _v in kl_texmat.fxc_defines(head)]
        k = (head[0x810:0x850].split(b'\0')[0].decode('latin1').lower(), d[0], frozenset(d[1:]))
        if k in seen:
            twice += 1
        elif k in need or k[0] in ALWAYS_FX:
            seen.add(k); out.append((head, blob))
    new = kl_mat.write_fxc(out, ver)
    rep = {'entries before': len(ent), 'entries after': len(out), 'effects asked for': len(need), 'same effect twice': twice,
           'asked for but not in the cache': len(need - seen), 'bytes before': len(fxc), 'bytes after': len(new)}
    log('  shader cache: %d -> %d entries, %.2f -> %.2f MB (%d effects asked for by %d materials, %d of them in no entry; %d later copies of an effect dropped)' % (
        len(ent), len(out), len(fxc) / 1048576, len(new) / 1048576, len(need), len(mat.insts), rep['asked for but not in the cache'], twice))
    return new, rep


def fit_shaders(mat, fxc, slots=None, log=print):
    """Give every material instance (kl_texmat.Mat, edited in place) a shader permutation the
    cache `fxc` (bytes of the .fxc the level ships) holds: where an instance asks for an effect
    no entry has, the cheapest set of its feature switches (SWITCH_COST) is turned off (BOOL
    VALU = 0) so that every effect it then asks for exists; entry +0x08 follows (kl_mat rule).
    Nothing is ever switched on, blending is never touched. Stock Dog Days levels need nothing.
    An instance no set of switches helps is rebuilt as a Standard/Standard material (plain_twin()).
    Returns dict(fixed={slot: (name, [switches turned off])}, unresolved={slot: (name, lacking)},
    lost={switch: instances}, reclassed={slot: (name, class it had)})."""
    import itertools, kl_mat
    have = shader_cache(fxc)
    rep = dict(fixed={}, unresolved={}, lost=collections.Counter(), reclassed={})
    for s, lack in missing_shaders(mat, have, slots).items():
        e = mat.insts[s]
        on = sorted(k for k, (_n, v) in _bools(e).items() if v and k not in EXCLUDED)
        best = None
        for r in range(1, len(on) + 1):
            for off in itertools.combinations(on, r):
                if all(x in have for x in shader_needs(mat, e, off)):
                    cost = (sum(SWITCH_COST.get(k, 3) for k in off), r, off)
                    if best is None or cost < best:
                        best = cost
        if best is None:
            twin = plain_twin(mat, e, have)
            if twin is None:
                rep['unresolved'][s] = (e.name, lack); continue
            was = '%s/%s' % kl_mat.class_key(mat, e)
            mat.insts[s], off = twin
            for k in off:
                rep['lost'][k] += 1
            rep['fixed'][s] = (e.name, ['class %s -> %s/%s' % ((was,) + PLAIN)] + list(off))
            rep['reclassed'][s] = (e.name, was)
            continue
        nodes = _bools(e)
        for k in best[2]:
            _kid(nodes[k][0], 'VALU')[3] = 0
            rep['lost'][k] += 1
        e.f[2] = kl_mat.feature_flags(e)
        rep['fixed'][s] = (e.name, list(best[2]))
    log('  shaders: %d materials asked for an effect no cache entry has; switched off %s; unresolved: %s' % (
        len(rep['fixed']) + len(rep['unresolved']), dict(rep['lost']) or 'nothing',
        [v[0] for v in rep['unresolved'].values()] or 'none'))
    if rep['reclassed']:
        log('  shaders: rebuilt as %s/%s (no permutation of their own class is compiled): %s' % (
            PLAIN + (', '.join('%s (was %s)' % v for v in rep['reclassed'].values()),)))
    return rep


PLAIN = ('Standard', 'Standard')            # the class every mesh kind has compiled permutations of (kl_mat.FALLBACK)
# Classes whose instances plain_twin() may rebuild. SkinCloth only: a body in the plain shader still looks like
# a body. NOT Standard/Glow (Retomoto's 'Weapons/BombWindow_02', the lamps and beams of M02 / M06, re/maps.md 9):
# a glow drawn as a lit surface may look worse than a glow that is missing - add it here to try (GUESS either way).
TWIN_CLASSES = (('Standard', 'SkinCloth'),)


def plain_twin(mat, entry, have, ref=None):
    """A material instance that fit_shaders() cannot fit, rebuilt as an instance of Standard/Standard
    the way kl_mat.convert_mat_full builds one: the properties of that class in Dog Days' order, the
    instance's own node where it has a property of that name, Dog Days' most common node for one every
    stock instance has; its other properties (rim light, translucency, glow ...) are dropped. Texture,
    colour, blend state, render group, surface type and mesh kind stay. Then the cheapest switches
    go off, as in fit_shaders(). -> (kl_texmat.Entry, [switches turned off]) or None when the instance's
    class is not in TWIN_CLASSES, the level has no Standard/Standard class, the mesh kind never occurs
    with it, or nothing fits either.
    ASSUMPTION: a property two classes both name means the same in both (mapDiffuse, v4DiffuseColor,
    RenderState, BumpEnabled, SpecularEnabled ... do in every stock tree read), and a far-detail body
    drawn with the plain shader is close enough to the cloth one - it is what Dead Men's own
    'JPN_Swat_LOD3' and 'JPN_Police_female_LOD3' of the same level already are. NOT SEEN LIVE."""
    import itertools, kl_mat, kl_texmat as TM
    slot = next((s for s, c in sorted(mat.classes.items()) if kl_mat.class_key(mat, c) == PLAIN), None)
    if slot is None or entry.f[1] == slot or kl_mat.class_key(mat, entry) not in TWIN_CLASSES:
        return None
    ref = ref or kl_mat.dd_reference()
    if entry.f[5] not in ref.subtypes[PLAIN]:
        return None
    own = dict(kl_mat._keys(kl_mat._bind(entry)))
    bind = []
    for key in ref.order[PLAIN]:
        if key in own:
            bind.append(kl_mat._thaw(kl_mat._freeze(own[key])))
        elif key in ref.always[PLAIN]:
            n = kl_mat._thaw(ref.always[PLAIN][key])
            if n[0] == 'BOOL' and _kid(n, 'NAME')[3].lower().endswith(b'enabled') and _kid(n, 'VALU'):
                _kid(n, 'VALU')[3] = 0                  # nothing is switched ON: stock's most common BumpEnabled /
            bind.append(n)                              # SpecularEnabled are 1, and this material has no maps for them
    f = list(entry.f)
    f[1] = slot
    twin = TM.Entry(PLAIN[0].encode('latin1'), f, [entry.root[0], entry.root[1], 2, [
        kl_mat._thaw(kl_mat._freeze(_kid(entry.root, 'NAME'))), ['BIND', TM.LIST, len(bind), bind]]])
    on = sorted(k for k, (_n, v) in _bools(twin).items() if v and k not in EXCLUDED)
    best = None
    for r in range(0, len(on) + 1):
        for off in itertools.combinations(on, r):
            if all(x in have for x in shader_needs(mat, twin, off)):
                cost = (sum(SWITCH_COST.get(k, 3) for k in off), r, off)
                if best is None or cost < best:
                    best = cost
        if best is not None:
            break
    if best is None or not shader_needs(mat, twin, best[2]):
        return None
    nodes = _bools(twin)
    for k in best[2]:
        _kid(nodes[k][0], 'VALU')[3] = 0
    twin.f[2] = kl_mat.feature_flags(twin)
    return twin, list(best[2])


def refit(src, dst, log=print):
    """A built level (a folder with <slot>_Main.zip and the files beside it) written to folder `dst`
    with fit_shaders() run again on its .MAT against its own .fxc; no other member changes.
    -> (fit_shaders report, materials still without a compiled shader)."""
    import kl_chars, kl_mat, kl_texmat as TM
    lv = kl_chars.Lv(src)
    mat = TM.read_mat(lv['.MAT'])
    rep = fit_shaders(mat, lv['.fxc'], log=log)
    data = TM.write_mat(mat)
    kl_mat.check(data)                                  # still nothing a stock Dog Days .MAT could not hold
    if TM.read_mat(data).refs != TM.read_mat(lv['.MAT']).refs:
        raise ValueError('refit changed the material use counts')
    lv['.MAT'] = data
    path = lv.write(dst, lv.name)
    left = missing_shaders(TM.read_mat(data), lv['.fxc'])
    log('  refit: %s written (%.0f MB); %d materials fitted, %d still without a compiled shader' % (
        path, os.path.getsize(path) / 1e6, len(rep['fixed']), len(left)))
    return rep, left


# ------------------------------------------------------------------ post filter
# Scene property PostFilterPalettes names one .prm chunk: u16 offsets (count = first offset / 2,
# kl2 0x442779: movzx word [chunk] / shr 1), then the entries, each a run-length coded 256-byte
# curve (the engine decodes the 37 curves of the active set into 37 x 256 bytes at 0x1536278 and
# keeps one byte per entry in a 0x8000-byte table: no small limit on the count). Entries 0..26
# are byte-identical in all 41 stock levels of both games (0 = the zero curve, 1 = identity).
# A filter set ('pf', 176 bytes) = 25 floats, then 37 u16 at +0x64: palette entry numbers
# (0xffff = none; never >= the level's count: 558 sets of the 41 levels), then one 0.
# PostFilterBoxes names a chunk of 88-byte records, one per PostFilterBox controller, +0x30 = its set.
PF_SET, PF_INDEX, PF_COUNT, PF_NONE = 176, 0x64, 37, 0xffff


def palette_entries(chunk):
    """The curves of a PostFilterPalettes chunk (the last one keeps the chunk's zero padding)."""
    n = struct.unpack_from('<H', chunk, 0)[0] // 2
    offs = list(struct.unpack_from('<%dH' % n, chunk, 0)) + [len(chunk)]
    if not n or offs[0] != 2 * n or any(a >= b for a, b in zip(offs, offs[1:])):
        raise ValueError('not a post-filter palette')
    return [chunk[a:b] for a, b in zip(offs, offs[1:])]


def palette_pack(entries):
    out, o = [], 2 * len(entries)
    for e in entries:
        out.append(o); o += len(e)
    if o > 0xffff:
        raise ValueError('post-filter palette over 64 KB: offsets are 16 bit')
    b = struct.pack('<%dH' % len(entries), *out) + b''.join(entries)
    return b + bytes(-len(b) % 16)


def set_curves(chunk):
    """The 37 palette entry numbers of a 176-byte filter set (0xffff = none)."""
    if len(chunk) != PF_SET or struct.unpack_from('<H', chunk, PF_INDEX + 2 * PF_COUNT)[0]:
        raise ValueError('not a post-filter set')
    return struct.unpack_from('<%dH' % PF_COUNT, chunk, PF_INDEX)


def graft_postfilter(prm, pal_chunk, m_palette, m_sets, log=print):
    """Let M's post-filter sets work on the joined level's palette. prm: joined kl_prmgraph.Prm
    (edited in place); pal_chunk: index of the palette chunk the joined scene block names (S's);
    m_palette: bytes of M's palette chunk; m_sets: chunk indices, in prm, of M's 176-byte sets
    (those its PostFilterBoxes chunk and its map's post-filter events name). M's curves that
    S's palette lacks are appended, and the 37 entry numbers of each set are rewritten.
    Returns dict(entries (before, after), added, sets, renumbered)."""
    # Two entries are the same curve when they agree up to their trailing zeros: a curve ends
    # with 1 to 3 zero bytes (2,108 entries of the 41 levels) and a chunk's last entry has the
    # chunk's padding behind it, so its true length is not known. Entries are stored as found.
    key = lambda e: e.rstrip(b'\0')
    ents = palette_entries(prm.chunks[pal_chunk])
    have = {}
    for i, e in enumerate(ents):
        have.setdefault(key(e), i)
    n0, imap = len(ents), {}
    for i, e in enumerate(palette_entries(m_palette)):
        if key(e) not in have:
            have[key(e)] = len(ents)
            ents.append(e)
        imap[i] = have[key(e)]
    prm.chunks[pal_chunk] = palette_pack(ents)
    changed = 0
    for s in sorted(set(m_sets)):
        idx = set_curves(prm.chunks[s])
        if any(v != PF_NONE and v not in imap for v in idx):
            raise ValueError('post-filter set %d names a curve its palette does not have' % s)
        new = tuple(v if v == PF_NONE else imap[v] for v in idx)
        changed += new != idx
        c = prm.chunks[s]
        prm.chunks[s] = c[:PF_INDEX] + struct.pack('<%dH' % PF_COUNT, *new) + c[PF_INDEX + 2 * PF_COUNT:]
    rep = dict(entries=(n0, len(ents)), added=len(ents) - n0, sets=len(set(m_sets)), renumbered=changed)
    log('  post filter: palette %d -> %d curves, %d sets of the map, %d renumbered' % (n0, len(ents), rep['sets'], changed))
    return rep


# ------------------------------------------------------------------ baked ambient occlusion
# Dead Men's 'lit' data is an AMBIENT-OCCLUSION LIGHT MAP (shader source, shipped in every Dead
# Men archive: Shaders/PC/FX/Common.fx, StandardCommon.fx, Standard20/30.fx, Glow20.fx):
#   mesh descriptor [4] -> stream, 8 bytes per vertex: D3DCOLOR vLightMapVertexColor (COLOR6;
#                          rgb is ff ff ff in all 151,519 vertices of M03_FA_A, alpha 0..255) and
#                          2 x u16 vLightMapVertexCoords (TEXCOORD2)
#   mesh descriptor [5] -> record {u32 .TEX id of the light map (DXT1 atlas, 1024 x 1024 ...),
#                          colour 0x00RRGGBB = v4LightMapColor, 0, 0}
#   float3 AmbientOcclusion(uv, c) { return lerp(v4LightMapColor.rgb, c.rgb, tex2D(samplerLightmap, uv).g * c.a); }
#   and the pixel shader multiplies the diffuse texel (and the reflection) by it, MESH_STANDARD only.
# So it only darkens, and it darkens ambient and direct light alike.
# Dog Days: kl2.exe still declares COLOR6 / TEXCOORD2 in its static-mesh vertex declarations
# (0xb98568, 0xb985f8, 0xb98658, set up at 0x61ca80) and its effects still declare mapLightmap /
# v4LightMapColor, but NOT ONE of the 5,176 compiled shaders of the 242 distinct stock effects
# reads COLOR6, TEXCOORD2 or samplerLightmap, and effects cannot be compiled at run time. The
# data cannot be consumed as it is.
# Nearest equivalent, bake_ao(): the factor is evaluated per vertex and multiplied into the vertex
# colour (vertex +0x10, COLOR3). Dog Days multiplies that into dynamic light in the shader
# (Standard30 'Lighting': mul o0.xyz, lightcolour * diffusecolour, COLOR3) and, by the shader
# source's own input comment ('COLOR0: Light color * vertex color'), into the CPU-lit sun term.
# ASSUMPTIONS: (1) the CPU also multiplies the ambient term (COLOR2) by the vertex colour - not
# read; if it does not, the bake darkens lit surfaces only. (2) uv = u16 / 65536. (3) per vertex
# is enough: the light map's texel detail (soft contact shadows inside a triangle) is lost.
def dxt1_green(data, w, h):
    """Green channel (0..255, row major) of a DXT1 picture."""
    out, o = bytearray(w * h), 0
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            c0, c1, bits = struct.unpack_from('<HHI', data, o); o += 8
            g0, g1 = (c0 >> 5 & 63) * 255 // 63, (c1 >> 5 & 63) * 255 // 63
            pal = (g0, g1, (2 * g0 + g1) // 3, (g0 + 2 * g1) // 3) if c0 > c1 else (g0, g1, (g0 + g1) // 2, 0)
            for py in range(4):
                row = (by + py) * w + bx
                for px in range(4):
                    out[row + px] = pal[bits & 3]; bits >>= 2
    return out


def light_map(tex_entry):
    """(width, height, green channel) of a Dead Men .TEX record that is a DXT1 light map."""
    if tex_entry[4:8] != b'1TXD':
        raise ValueError('light map is not DXT1')
    h, w = struct.unpack_from('<HH', tex_entry, 16)
    o = tex_entry.index(b'\0', 36) + 1
    n = struct.unpack_from('<I', tex_entry, o)[0]
    if n != w * h // 2:
        raise ValueError('light map: first mip is %d bytes, %d x %d DXT1 needs %d' % (n, w, h, w * h // 2))
    return w, h, dxt1_green(tex_entry[o + 4:o + 4 + n], w, h)


def bake_ao(dm_prm, dd_prm, roots, dm_tex, strength=1.0, log=print):
    """Dead Men's ambient-occlusion light map baked into the vertex colours of the converted
    file. dm_prm: the level's .prm as Dead Men has it; dd_prm: what kl_prm.convert made of it
    (same chunk numbers); roots: as for kl_prm.convert; dm_tex: Dead Men's .TEX (bytes).
    strength 0..1 scales the darkening. A vertex chunk shared by descriptors with different
    streams (or with none) is cloned per stream and the descriptors are repointed. Returns
    (bytes, report: meshes, vertices, cloned chunks, added bytes, mean factor, maps)."""
    import kl_prmgraph as G, kl_texmat
    src, out = G.read(dm_prm, 'dm'), G.read(dd_prm, 'dd')
    if len(src.chunks) > len(out.chunks):
        raise ValueError('the converted .prm has fewer chunks than its source')
    kinds, _a = G.walk(src, roots)
    tex = kl_texmat.read_tex(dm_tex)
    maps, users, jobs = {}, collections.defaultdict(set), {}
    for i, k in kinds.items():
        if k != 'desc':
            continue
        nv, vtx, _n, _idx, lit, lit5 = struct.unpack_from('<6I', src.chunks[i], 0)
        if not vtx:
            continue
        users[vtx].add((lit, lit5) if lit else None)
        if lit:
            if len(src.chunks[vtx]) != (40 * nv + 15 & ~15) or len(src.chunks[lit]) < 8 * nv:
                raise ValueError('lit descriptor %d: not a 40-byte-vertex mesh with an 8-byte stream' % i)
            jobs.setdefault((vtx, lit, lit5), []).append((i, nv))
    rep = dict(meshes=0, vertices=0, cloned=0, added=0, mean=1.0, maps={})
    total = 0.0
    for (vtx, lit, lit5), descs in sorted(jobs.items()):
        tid, fade = struct.unpack_from('<II', src.chunks[lit5], 0)
        if tid not in maps:
            maps[tid] = light_map(tex.tex[tid].entry); rep['maps'][tid] = tex.tex[tid].name
        w, h, green = maps[tid]
        fb, fg, fr = fade & 255, fade >> 8 & 255, fade >> 16 & 255
        nv = max(n for _d, n in descs)
        v, s = bytearray(out.chunks[vtx]), src.chunks[lit]
        if bytes(v) != src.chunks[vtx]:
            raise ValueError('vertex chunk %d was changed by the conversion' % vtx)
        for j in range(nv):
            cb, cg, cr, ca, tu, tv = struct.unpack_from('<4B2H', s, 8 * j)
            t = green[min(tv * h >> 16, h - 1) * w + min(tu * w >> 16, w - 1)] * ca / 65025.0
            o = 40 * j + 16
            for c, (f, col) in enumerate(((fb, cb), (fg, cg), (fr, cr))):
                k = 1.0 - strength * (1.0 - (f + (col - f) * t) / 255.0)       # lerp(fade, colour, t), then strength
                v[o + c] = min(255, int(v[o + c] * k + 0.5))
                total += k
        rep['vertices'] += nv; rep['meshes'] += len(descs)
        if users[vtx] == {(lit, lit5)}:
            out.chunks[vtx] = bytes(v)                  # every user wants this very stream
        else:
            out.chunks.append(bytes(v)); out.refs.append(1)
            rep['cloned'] += 1; rep['added'] += len(v)
            for d, _n in descs:
                c = out.chunks[d]
                if len(c) != 48 or struct.unpack_from('<I', c, 4)[0] != vtx:
                    raise ValueError('descriptor %d of the converted file does not name vertex chunk %d' % (d, vtx))
                out.chunks[d] = c[:4] + struct.pack('<I', len(out.chunks) - 1) + c[8:]
    rep['mean'] = round(total / (3 * rep['vertices']), 4) if rep['vertices'] else 1.0
    log('  baked AO: %d meshes, %d vertices, mean factor %.3f, %d vertex chunks cloned (+%d bytes), light maps %s' % (
        rep['meshes'], rep['vertices'], rep['mean'], rep['cloned'], rep['added'], sorted(rep['maps'].values())))
    return G.write(out), rep


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


def _members(level, exts):
    import zipfile
    game = 'dm' if level.startswith('M') else 'dd'
    with zipfile.ZipFile(J.level_zip(level, game)) as z:
        return {n.rsplit('.', 1)[1].lower(): z.read(n) for n in z.namelist()
                if '_main.' in n.lower() and n.rsplit('.', 1)[1].lower() in exts}


def _postfilter(level):
    """(Prm, palette chunk index, [filter set chunk indices]) of a stock level of either game."""
    import kl_dmassets, kl_prmgraph as G
    game = 'dm' if level.startswith('M') else 'dd'
    f = _members(level, ('prm', 'gms', 'prp'))
    p = G.read(f['prm'], game)
    kinds, _a = G.walk(p, kl_dmassets.prm_roots(f['gms'], f['prp'], game))
    return p, next(i for i, k in kinds.items() if k == 'pfpal'), sorted(i for i, k in kinds.items() if k == 'pf')


def test_render(maps=('M01_FA_A', 'M03_FA_A'), systems='F07', log=print):
    """Offline tests of fit_shaders, graft_postfilter and bake_ao.
    1. Every stock Dog Days level: each effect its materials ask for is in its own .fxc, and
       fit_shaders changes nothing. 2. Every stock level of both games: the palette packs back
       byte for byte and no filter set names a curve past it. 3. Each Dead Men map, converted:
       fit_shaders against the cache the graft ships (systems' .fxc + build/shared/union.fxc)
       leaves only what it reports as unresolved and the .MAT still passes kl_mat.check; its filter sets grafted
       onto the systems level's palette see the curves they saw before, and so do the systems'
       own; bake_ao output passes kl_prm.check, moves nothing but vertex colours, never raises
       one, and leaves unlit meshes alone. Returns the number of problems."""
    import copy, kl_mat, kl_texmat as TM, kl_prm, kl_dmassets, kl_prmgraph as G, kl_port_check
    quiet = lambda *_a: None
    bad = 0
    need = 0
    for lv in DD_LEVELS:
        f = _members(lv, ('mat', 'fxc'))
        mat = TM.read_mat(f['mat'])
        need += sum(len(shader_needs(mat, e)) for e in mat.insts.values())
        lack = missing_shaders(mat, f['fxc'])
        rep = fit_shaders(mat, f['fxc'], log=quiet)
        same = TM.write_mat(mat) == f['mat']
        bad += len(lack) + (not same) + len(rep['fixed'])
        if lack or not same:
            log('PROBLEM: %s: %d instances lack an effect of the level\'s own cache; unchanged by fit_shaders: %s' % (lv, len(lack), same))
    log('stock Dog Days: %d effects asked for by the materials of %d levels, all in the level\'s own .fxc: %s' % (need, len(DD_LEVELS), not bad))
    dms = sorted(d for d in os.listdir(os.path.dirname(os.path.dirname(J.level_zip(maps[0], 'dm')))) if d.startswith('M') and '.' not in d)
    nset = npal = 0
    for lv in DD_LEVELS + dms:
        p, pal, sets = _postfilter(lv)
        ents = palette_entries(p.chunks[pal])
        npal += len(ents); nset += len(sets)
        if palette_pack(ents) != p.chunks[pal]:
            bad += 1; log('PROBLEM: %s: palette does not pack back' % lv)
        for s in sets:
            if any(v != PF_NONE and v >= len(ents) for v in set_curves(p.chunks[s])):
                bad += 1; log('PROBLEM: %s: set %d names a curve past the palette' % (lv, s))
    log('post filter: %d levels, %d curves, %d sets: palettes pack back and every set index is in range' % (len(DD_LEVELS) + len(dms), npal, nset))
    union = os.path.join(kl_port_check.workdir(), 'build', 'shared', 'union.fxc')
    cache = TM.merge_fxc(_members(systems, ('fxc',))['fxc'], open(union, 'rb').read())
    ps, pal_s, sets_s = _postfilter(systems)
    seen = lambda p, pal, sets: [[None if v == PF_NONE else palette_entries(p.chunks[pal])[v].rstrip(b'\0') for v in set_curves(p.chunks[s])] for s in sets]
    for name in maps:
        src = kl_dmassets.dm_level(name)
        roots = kl_dmassets.prm_roots(src['gms'], src['prp'], 'dm')
        conv, _r, _s = kl_dmassets.convert_level(name, src=src)
        probs = []
        # shaders
        mat = TM.read_mat(conv['MAT'])
        lack = missing_shaders(mat, cache)
        rep = fit_shaders(mat, cache, log=quiet)
        if set(missing_shaders(mat, cache)) != set(rep['unresolved']):
            probs.append('fit_shaders left materials without an effect that it did not report')
        try:
            kl_mat.check(TM.write_mat(mat))
        except ValueError as e:
            probs.append('fitted .MAT: %s' % e)
        log('%s: %d of %d materials lacked an effect (%d uses); switched off %s; unresolved (need a switch turned ON): %s' % (
            name, len(lack), len(mat.insts), sum(mat.refs[s] for s in lack), dict(rep['lost']),
            ['%s x%d' % (n, mat.refs[s]) for s, (n, _l) in rep['unresolved'].items()] or 'none'))
        # post filter: M's sets appended to the systems level's chunks, as the join does
        pm, pal_m, sets_m = _postfilter(name)
        j = G.Prm('dd', list(ps.chunks), list(ps.refs))
        new = []
        for s in sets_m:
            j.chunks.append(pm.chunks[s]); j.refs.append(1); new.append(len(j.chunks) - 1)
        prep = graft_postfilter(j, pal_s, pm.chunks[pal_m], new, log=quiet)
        if seen(j, pal_s, sets_s) != seen(ps, pal_s, sets_s) or seen(j, pal_s, new) != seen(pm, pal_m, sets_m):
            probs.append('a filter set sees other curves after the graft')
        G.read(G.write(j), 'dd')
        log('%s: post filter onto %s: %s' % (name, systems, prep))
        # baked AO
        out, arep = bake_ao(src['prm'], conv['prm'], roots, src['tex'], log=quiet)
        try:
            kl_prm.check(out, roots)
        except ValueError as e:
            probs.append('baked .prm: %s' % e)
        a, b, s0 = G.read(conv['prm'], 'dd'), G.read(out, 'dd'), G.read(src['prm'], 'dm')
        ka, _a = G.walk(a, roots)
        kb, _a = G.walk(b, roots)
        other = sum(1 for i in range(1, len(a.chunks)) if a.chunks[i] != b.chunks[i] and ka.get(i) not in ('vtx', 'desc'))
        moved = up = 0
        for i, k in kb.items():
            if k != 'desc' or i >= len(a.chunks):
                continue
            nv, vtx = struct.unpack_from('<II', b.chunks[i], 0)
            x, y = a.chunks[struct.unpack_from('<I', a.chunks[i], 4)[0]] if nv else b'', b.chunks[vtx] if nv else b''
            if i >= len(s0.chunks) or not struct.unpack_from('<I', s0.chunks[i], 16)[0]:     # unlit, or added by kl_prm
                moved += x != y
                continue
            for v in range(nv):
                q, r = x[40 * v:40 * v + 40], y[40 * v:40 * v + 40]
                moved += q[:16] != r[:16] or q[19:] != r[19:]
                up += any(r[16 + c] > q[16 + c] for c in range(3))
        if other or moved or up:
            probs.append('bake_ao: %d other chunks changed, %d vertices moved outside the colour or unlit meshes touched, %d colours raised' % (other, moved, up))
        zero, _z = bake_ao(src['prm'], conv['prm'], roots, src['tex'], strength=0.0, log=quiet)
        z = G.read(zero, 'dd')
        if any(z.chunks[struct.unpack_from('<I', z.chunks[i], 4)[0]] != a.chunks[struct.unpack_from('<I', a.chunks[i], 4)[0]]
               for i, k in ka.items() if k == 'desc' and struct.unpack_from('<I', a.chunks[i], 0)[0]):
            probs.append('bake_ao with strength 0 changes a vertex')
        log('%s: baked AO: %s' % (name, {k: v for k, v in arep.items() if k != 'maps'}))
        bad += len(probs)
        for p in probs:
            log('  PROBLEM: ' + p)
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
    elif a and a[0] == 'render-test':
        sys.exit(1 if test_render(*([tuple(a[1:])] if a[1:] else [])) else 0)
    elif len(a) == 3 and a[0] == 'refit':
        _rep, left = refit(a[1], a[2])
        sys.exit(1 if left else 0)
    else:
        print(__doc__)
