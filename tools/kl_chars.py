#!/usr/bin/env python3
"""
Dead Men character MODELS on Dog Days characters (stage 2 groundwork; nothing here is installed).

    python kl_chars.py survey [M01_FA_A ...]    every character model of the Dead Men maps (default: the four
                                                FA maps): users, bones, variants, LODs, materials, size
    python kl_chars.py bones                    proof of the skeleton <-> .ANM numbering on all 41 stock levels
    python kl_chars.py pose                     Dead Men heroes against Dog Days heroes: rest pose, proportions
    python kl_chars.py build civ|bot|heroes|all the three experiments of re/characters_graft.md, each a kept,
                                                checked build in <work>/build/chars/<name>
    python kl_chars.py put <base> <out folder> "<target path>=<map>:<source path>[:v,v]" ...
                                                the general form (base: stock level name or a build folder)
    python kl_chars.py check <folder>           re-read a build under every checker
    python kl_chars.py compact <folder> <out folder>
                                                the build with its .prm renumbered and the dead chunks dropped
                                                (compact_level; KLWardrobe.ini rewritten). NOT LOADED LIVE: it moves
                                                live chunks of the systems level - only when the count needs it
    python kl_chars.py invisible <folder | level> [--all] [--at x0,x1,z0,z1]
                                                every person of a built (or stock) level who would NOT BE
                                                DRAWN, and why (undrawn(); re/invisible.md): model, variant,
                                                detail levels, materials without a compiled shader, emptied
                                                mesh data, skeleton, room. --all: the table of everybody
    python kl_chars.py wardrobe <base> <out folder> [--level=M01_FA_A] [--slot=F01] [--armour=0,1,2,3] [--fix-bones] [--no-reuse]
                                                THE WARDROBE (re/wardrobe.md): the eight Dead Men heroes as extra
                                                models with all 24 Fragile Alliance looks, every body with every
                                                heister's mask as variants, and KLWardrobe.ini for klhook/klchar.c;
                                                <base> = a stock level or a FINISHED BUILD FOLDER (its side files -
                                                KLJoin.ini ... - go along); --armour=0,3 leaves two body meshes
                                                out (about 6.5 MB of .prm less); pictures: kl_view.py
    python kl_chars.py looks [M01_FA_A ...]     the 24 variants of each Dead Men hero, part by part, and whether
                                                the eight models are the same in every map
    install (a later LIVE agent, not this tool): python kl_graft.py install F01 --from <folder>

WHAT A BUILD CHANGES (put(); everything else of the base level is byte for byte the base's)
  .prm   the base's file + the model sub-graph of each chosen Dead Men character (kl_prmgraph.append of
         a converted extract): a NEW root per pick (its own object table), meshes, descriptors (48 bytes),
         vertex / index data, skeleton. Nothing of the base that is LIVE moves or changes.
         THE NUMBER OF CHUNKS IS LIMITED (73,728 table slots in kl2.exe, shared with run-time chunks;
         re/prm_limit.md - the full wardrobe on Retomoto had 80,628 and crashed 16 s into the load), so the
         new chunks are written INTO the indices of the base's dead chunks (what no .gms record, .prp field
         or wardrobe root reaches: in a grafted level S's removed map, 27,000 indices) and those that are
         not needed become 16-byte stubs: dead_indices(). --no-reuse: the old way, everything at the end.
  .MAT .TEX  the materials those objects name and their textures, renumbered (kl_texmat.merge_*); the
         .MAT use counts recomputed from the joined .prm; kl_light.fit_shaders on the NEW slots only.
  .fxc   the base's + <work>/build/shared/union.fxc when that exists (as kl_graft does for a Dead Men map).
  .oct   one record per new root (a copy of the source root's: a character's record is an EMPTY tree in
         both games - 0 items on every hero checked - but every root owns one, kl_octree).
  .gms   record +0x0c of each target entity = the new root.   .prp  ZGEOM[4] of the same node.
  .ANM   untouched, unless a bone name of a new skeleton is missing from its bone table (then appended).
  Not touched: the target's class, controllers, animation set, sound offsets, variant id, position.

THE SKELETON IS BAKED AGAINST THE LEVEL'S .ANM (found here, 2026-10-09; `python kl_chars.py bones`)
  skel chunk = 20 dwords (kl_prmgraph 'skel'). Per slot, n = bone count:
   [0]  n                                   [1]  64 B per bone: +0 vec3, +0x0c parent (int, -1 root),
                                                 +0x10 vec3, +0x1c name\\0 padded with 0xcd
   [2] [3] 48 B per bone: rest matrix (3x3 + position), global     [18] 48 B: its inverse
   [4]  36 B per bone (3x3; not decoded)    [6]  28 B per bone: quaternion + position (local rest)
   [5]  256 B: BONE ID -> bone index, 0xff = the model has no such bone; every bone has exactly one id.
        THIS is how game code finds a bone: ZLNKOBJ::GetBoneIndex(id) kl2 0x5575a0 (103 call sites; -1
        when the table says 0xff), through ZPrimControlWintel slot 48 (0x685bf0). No bone is looked up
        by NAME at run time. Two kinds of id:
        FIXED, the same in every level of both games: the bones named in the {id, name} table at kl2
          0xcd8850 (= property enum eBoneID): 1 GROUND, 2 PELVIS, 3 SPINE, 4 SPINE_1, 6 NECK, 7 HEAD,
          9..16 legs, 17..26 arms, hands and first finger, 31 / 32 'r / l hand attacher', 33 free_bone01
          (FREE_ATTACHER in Dead Men's exe: no Dead Men model has it), 34 'spine1 attacher', 35 'hip
          attacher', 36 'head attacher'. Every constant the code passes is one of these: 2 3 4 6 7 9 0xa
          0xc 0xd 0xe 0x10..0x14 0x16..0x19 0x1f 0x20 0x21 (kl2, 83 of the 103 sites; the rest pass a
          register). Every Dead Men person of the four FA maps has all of them but 0x21.
        PER LEVEL: every other bone (SPINE_2, neck1, the fa_*, xtra_*, finger, car and weapon bones) has
          a number that is consistent inside one level and differs between levels (5 is SPINE_2 in F01
          and M01_FA_A, 'body' - a car - in M02 / M03 / M06_FA_A). Who reads these was NOT found; a
          transplanted model is renumbered to the destination's ids all the same: reid().
   [8]  1024 B: ANIMATION BONE NUMBER -> bone index (0xff none; the last two bytes are 0)
   [9]  u16 per bone: bone index -> animation bone number
   [10] 1024 x u16: animation bone number -> 12 * bone index (0xffff none; the last two words are 0, so
        both tables really hold 1022 numbers)
        The animation bone number is the index of the bone's name in the bone-name table of THE LEVEL'S
        OWN .ANM (case-insensitive): 66,957 bones of 2,247 skeletons in the 41 stock levels, 0 exceptions,
        and [8] / [10] are exact inverses of [9]. The tables of all 41 files agree on the first 61 names
        only (PELVIS .. 'r hand attacher'; 61 is free_bone01 in Dog Days, FREE_ATTACHER in Dead Men);
        from 62 on every level has its own order (fa_jaw is 67 in F01, 72 in M01_FA_A, 80 in M03_FA_A).
        So a model moved to another level animates its body correctly and its face / muscle / finger
        helper bones WRONGLY unless [8] [9] [10] are rewritten against the destination's .ANM: rebind().
        kl_graft does not do this for the map's models (Dead Men agents, cars) - see re/characters_graft.md.
   [13] u8 per bone: parent index (0xff root)
   [19] u32 x (n - 1): 48 * parent of bone k + 1 (offset of the parent's matrix)
   [14]..[17] = eight u16: bone counts per level of detail: [0] and [7] = n, [1..5] = the leading bones
        kept at lower detail (36 / 34 in Dog Days people, 33 / 35 in Dead Men), [6] varies (kl2 0x4beab1
        takes the largest of those the mesh's LOD mask selects).
   [7] (IK chains), [11] (face: 220 44-byte records ...), [12]: not decoded, travel with the model.
  Mesh objects name bones as runs {12 * count, 12 * first bone} (+0x38 count, +0x3c chunk): bone indices
  of the model, so APPENDING a bone disturbs nothing.

free_bone01 (bone id 33): in every Dog Days person, in no Dead Men model. Read by exactly three places,
  all through GetBoneIndex(0x21): kl2 0x42f900 and 0x7db520 (both called from 0x4a1b40, an action of a
  player) and 0x5f2c66 (ZFFActionCheckPulse slot 2). With the bone missing GetBoneIndex returns -1, the
  matrix getter kl2 0x55c7b0 rejects the index (unsigned compare with the bone count) and returns false
  WITHOUT writing its outputs: no crash in the lookup, but the caller goes on with uninitialised vectors.
  Two repairs here:
   free='add'    a real bone appended at the END of the skeleton (parent GROUND as in Dog Days, rest
                 values copied from the Dog Days model the target had), bound to the destination's
                 animation bone 'free_bone01' so Dog Days' clips move it. ASSUMPTIONS: Dog Days keeps the
                 bone among the leading low-detail bones ([14..17] words 1..5), here it is past them, so
                 at lower detail it may not be updated; word 6 is raised only where it equalled n.
   free='alias'  nothing added: id 33 points at GROUND in table [5] (one byte). The three readers then
                 get the character's ground matrix: sane values, but whatever the animation does with
                 the free bone is lost. Animation is not affected ([8]..[10] are a different key).
   free='none'   left as Dead Men had it.

VARIANTS: a mesh object is drawn when its variant byte (+0x0f) equals the entity's variant (ZLNKOBJ[0];
  Dog Days sets 2 on a heister when masks are on, re/characters.md 6). put() gives the new root exactly
  the Dog Days variants the target can be asked for - 1, 2 and the target's own - each a chosen Dead Men
  variant (default: the same number if the model has it, else its first). Objects of other variants are
  left out; an object needed under two numbers is duplicated (64 bytes, the geometry is shared).
  Dead Men has NO masked look for Kane or Lynch: their 24 variants are 3 earpieces x 2 play-style kits x
  4 equipment levels, the face is in all of them (survey). Hero_03..08 are balaclava heads in every variant.
LODs: masks 0x01 / 0x02 / 0x7c in both games; nothing to convert.
NOT DONE: the money bag (Dog Days heroes carry a MoneyBag_01 mesh in both variants, weighted to spine and
  clavicle, and wear it from the start of a round: research/round_bank_hall_RN6_270s.png at $0; a Dead Men
  model has none, so a Dead Men heister has no bag on his back), voice sets, more than eight characters.
"""
import collections, os, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms, kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_prpjoin as J, kl_anm, kl_rtp
from kl_prp import Prp, units
from kl_port_check import find, workdir, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

FA_MAPS = ('M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A')
FREE_ID, FREE_NAME = 33, 'free_bone01'           # kl2 0xcd8850 row 33
ANM_SLOTS = 1024                                 # entries of skel [8] and [10]
PER_BONE = {1: 64, 2: 48, 3: 48, 18: 48, 4: 36, 6: 28}
PEOPLE = ('ZFFPlayer', 'ZFFActor')
# who the eight Dead Men Fragile Alliance heroes are. 01 / 02 by their head materials (Hero = Kane,
# Little = Lynch: the names the game's own files use); 03..08 have no head material of their own - a
# balaclava in every variant - and no name in the level: "the crew".
WHO = {'Hero_01': 'Kane', 'Hero_02': 'Lynch', 'Hero_03': 'crew, balaclava', 'Hero_04': 'crew, balaclava',
       'Hero_05': 'crew, balaclava', 'Hero_06': 'crew, balaclava', 'Hero_07': 'crew, balaclava',
       'Hero_08': 'crew, balaclava'}


def _pad(b, n=16):
    return bytes(b) + bytes(-len(b) % n)


def _put(c, off, fmt, *v):
    return c[:off] + struct.pack(fmt, *v) + c[off + struct.calcsize(fmt):]


# ------------------------------------------------------------------ skeleton
def skeleton(p, root):
    """Chunk index of a model root's skeleton, 0 if it has none (kl2 0x570b50)."""
    if p.u16(root, 2) != 7 or not p.chunks[root][0x0c] & 1:
        return 0
    prop = p.u32(root, 0x10)
    return p.u32(prop, 4) if prop else 0


def skeletons(p):
    """{skeleton chunk: [roots using it]} of a file, found by shape (as kl_texmat.material_refs finds roots)."""
    out, n = collections.OrderedDict(), len(p.chunks)
    for i in range(1, n):
        c = p.chunks[i]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and c[0x0c] & 1 and 0 < p.u32(i, 0x10) < n:
            prop = p.u32(i, 0x10)
            if len(p.chunks[prop]) == 16 and 0 < p.u32(prop, 4) < n and len(p.chunks[p.u32(prop, 4)]) == 80:
                out.setdefault(p.u32(prop, 4), []).append(i)
    return out


def bone_names(p, sk):
    n, d = p.u32(sk, 0), p.chunks[p.u32(sk, 4)]
    return [d[64 * b + 0x1c:64 * b + 64].split(b'\0')[0].decode('latin1') for b in range(n)]


def bone_parents(p, sk):
    n, d = p.u32(sk, 0), p.chunks[p.u32(sk, 4)]
    return [struct.unpack_from('<i', d, 64 * b + 0x0c)[0] for b in range(n)]


def anm_number(names):
    """{lower-case bone name: animation bone number} of an .ANM bone table; the exact spelling wins where a
    table holds a name twice in different case (none of the 41 stock tables does for a bone a model has)."""
    out = {}
    for i, s in enumerate(names):
        out.setdefault(s.lower(), i)
    return out


def bind_tables(names, number):
    """skel [8], [9], [10] for a model with these bone names. number: anm_number() of the level's table.
    Raises KeyError with the missing names."""
    lack = [s for s in names if s.lower() not in number]
    if lack:
        raise KeyError(lack)
    s9 = [number[s.lower()] for s in names]
    if max(s9) >= ANM_SLOTS - 2:
        raise ValueError('animation bone number %d does not fit the %d-entry tables' % (max(s9), ANM_SLOTS))
    s8, s10 = bytearray(b'\xff' * (ANM_SLOTS - 2) + b'\0\0'), [0xffff] * (ANM_SLOTS - 2) + [0, 0]
    for b, a in enumerate(s9):
        s8[a], s10[a] = b, 12 * b
    return bytes(s8), _pad(struct.pack('<%dH' % len(s9), *s9)), struct.pack('<%dH' % ANM_SLOTS, *s10)


def level_ids(p, sks=None):
    """{lower-case bone name: bone id} over the skeletons of a file (default: all). Raises when two
    skeletons disagree or a bone has no id or two (never in a stock level)."""
    ids, owner = {}, {}
    for sk in (skeletons(p) if sks is None else sks):
        names, t5 = bone_names(p, sk), p.chunks[p.u32(sk, 0x14)]
        seen = set()
        for i in range(256):
            if t5[i] != 0xff:
                s = names[t5[i]].lower()
                if i == FREE_ID and s != FREE_NAME:     # alias_free_bone(): a second id for an existing bone
                    continue
                if ids.setdefault(s, i) != i or owner.setdefault(i, s) != s or t5[i] in seen:
                    raise ValueError('skeleton %d: bone id %d (%s) disagrees with another skeleton of the level' % (sk, i, s))
                seen.add(t5[i])
        if len(seen) != len(names):
            raise ValueError('skeleton %d: %d bones without an id' % (sk, len(names) - len(seen)))
    return ids


def reid(p, sk, ids):
    """Table [5] of skeleton `sk` rewritten to the level numbering `ids` (level_ids() of the destination,
    extended here for names it does not know: the smallest unused id above 36). New chunk. Returns the
    number of bones whose id changed."""
    h = list(struct.unpack('<20I', p.chunks[sk]))
    names, old = bone_names(p, sk), p.chunks[h[5]]
    t5 = bytearray(b'\xff' * 256)
    for b, s in enumerate(names):
        if s.lower() not in ids:
            ids[s.lower()] = next(i for i in range(37, 255) if i not in set(ids.values()))
        t5[ids[s.lower()]] = b
    if bytes(t5) == old:
        return 0
    h[5] = _new(p, t5)
    p.chunks[sk] = struct.pack('<20I', *h)
    return sum(1 for i in range(256) if t5[i] != old[i] and t5[i] != 0xff)


def _new(p, data):
    return G.new_chunk(p, data)                       # a free index first (G.reuse), else one more at the end


def rebind(p, sk, number):
    """Rewrite skel [8] [9] [10] of skeleton chunk `sk` for the .ANM table `number` (anm_number()). The three
    tables become NEW chunks (a data chunk can serve two skeletons); the skeleton chunk is edited in place.
    Returns the number of bones whose animation number changed."""
    h = list(struct.unpack('<20I', p.chunks[sk]))
    names = bone_names(p, sk)
    s8, s9, s10 = bind_tables(names, number)
    old = struct.unpack_from('<%dH' % h[0], p.chunks[h[9]]) if h[9] else ()
    new = struct.unpack_from('<%dH' % h[0], s9)
    if (h[8] and p.chunks[h[8]] == s8) and (h[9] and p.chunks[h[9]] == s9) and (h[10] and p.chunks[h[10]] == s10):
        return 0
    h[8], h[9], h[10] = _new(p, s8), _new(p, s9), _new(p, s10)
    p.chunks[sk] = struct.pack('<20I', *h)
    return sum(1 for a, b in zip(old, new) if a != b) + abs(len(new) - len(old))


def free_bone(p, sk):
    """The model's free_bone01 as {slot: its bytes} (slots of PER_BONE), or None when it has none."""
    names = bone_names(p, sk)
    if FREE_NAME not in names:
        return None
    b, h = names.index(FREE_NAME), struct.unpack('<20I', p.chunks[sk])
    return {s: p.chunks[h[s]][z * b:z * b + z] for s, z in PER_BONE.items()}


def add_free_bone(p, sk, rest):
    """Append free_bone01 (parent GROUND) to skeleton `sk`. rest: free_bone() of a Dog Days model - the rest
    matrices are that model's (ASSUMPTION: good enough; a clip that moves the bone overrides them, and in
    Dog Days the values differ from model to model: 16 different sets on 102 people).
    Every per-bone slot gets a NEW chunk; [8]..[10] are left to rebind(). Returns the new bone's index."""
    h = list(struct.unpack('<20I', p.chunks[sk]))
    n, names = h[0], bone_names(p, sk)
    if FREE_NAME in names:
        return names.index(FREE_NAME)
    if names[0] != 'GROUND' or p.chunks[h[5]][FREE_ID] != 0xff or n >= 0xfe:
        raise ValueError('skeleton %d: not a person without a free bone' % sk)
    for s, z in PER_BONE.items():
        if len(p.chunks[h[s]]) != len(_pad(bytes(z * n))) or len(rest[s]) != z:
            raise ValueError('skeleton %d: slot %d is not %d bytes per bone' % (sk, s, z))
    if len(p.chunks[h[13]]) != len(_pad(bytes(n))) or len(p.chunks[h[19]]) != len(_pad(bytes(4 * (n - 1)))):
        raise ValueError('skeleton %d: parent tables have an unexpected size' % sk)
    name = FREE_NAME.encode() + b'\0'
    for s, z in PER_BONE.items():
        add = rest[s]
        if s == 1:                                      # definition: zero vectors, parent 0 (GROUND), the name
            add = bytes(12) + struct.pack('<i', 0) + bytes(12) + name + b'\xcd' * (36 - len(name))
        h[s] = _new(p, _pad(p.chunks[h[s]][:z * n] + add))
    h[13] = _new(p, _pad(p.chunks[h[13]][:n] + b'\0'))
    h[19] = _new(p, _pad(p.chunks[h[19]][:4 * (n - 1)] + struct.pack('<I', 0)))
    t5 = bytearray(p.chunks[h[5]]); t5[FREE_ID] = n
    h[5] = _new(p, t5)
    h[0] = n + 1
    c = struct.pack('<20I', *h)
    w = list(struct.unpack_from('<8H', c, 0x38))        # bone counts per level of detail
    if w[0] != n or w[7] != n:
        raise ValueError('skeleton %d: detail words %r do not start and end with the bone count' % (sk, w))
    w[0] = w[7] = n + 1
    if w[6] == n:                                       # ASSUMPTION: "all bones" where it said so before
        w[6] = n + 1
    p.chunks[sk] = _put(c, 0x38, '<8H', *w)
    return n


def alias_free_bone(p, sk, to='GROUND'):
    """Bone id 33 -> an existing bone in table [5] (new chunk). Returns False when the model has the bone."""
    h = list(struct.unpack('<20I', p.chunks[sk]))
    names = bone_names(p, sk)
    if p.chunks[h[5]][FREE_ID] != 0xff:
        return False
    t5 = bytearray(p.chunks[h[5]]); t5[FREE_ID] = names.index(to)
    h[5] = _new(p, t5)
    p.chunks[sk] = struct.pack('<20I', *h)
    return True


def check_bones(p, anm_names, roots=None):
    """Problems of the skeletons of `roots` (default: all of the file) against an .ANM bone table: every
    bone's name is in the table under its number, [8] and [10] invert [9], sizes fit, parents come first."""
    number, bad = anm_number(anm_names), []
    sks = skeletons(p) if roots is None else collections.OrderedDict((skeleton(p, r), [r]) for r in roots if skeleton(p, r))
    try:
        level_ids(p)                                    # always the whole file: ids are a level-wide numbering
    except ValueError as e:
        bad.append(str(e))
    for sk in sks:
        h = struct.unpack('<20I', p.chunks[sk]); n = h[0]
        names = bone_names(p, sk)
        if not (h[8] and h[9] and h[10]):
            bad.append('skeleton %d: no animation tables' % sk); continue
        try:
            want = bind_tables(names, number)
        except KeyError as e:
            bad.append('skeleton %d: bones %r are not in the .ANM bone table' % (sk, e.args[0][:4])); continue
        if (p.chunks[h[8]], p.chunks[h[9]], p.chunks[h[10]]) != want:
            s9 = struct.unpack_from('<%dH' % n, p.chunks[h[9]])
            w9 = struct.unpack_from('<%dH' % n, want[1])
            off = [names[b] for b in range(n) if s9[b] != w9[b]]
            bad.append('skeleton %d (%d bones): %d bones carry another level\'s animation number (%s ...)' % (
                sk, n, len(off), ', '.join(off[:3])) if off else 'skeleton %d: tables [8] / [10] do not invert [9]' % sk)
        par = p.chunks[h[13]]
        if any(par[b] >= b for b in range(1, n)) or par[0] != 0xff:
            bad.append('skeleton %d: a parent does not come before its child' % sk)
        if any(len(p.chunks[h[s]]) != len(_pad(bytes(z * n))) for s, z in PER_BONE.items()):
            bad.append('skeleton %d: a per-bone slot has the wrong size' % sk)
        t5 = p.chunks[h[5]]
        if any(t5[i] != 0xff and t5[i] >= n for i in range(256)):
            bad.append('skeleton %d: bone id table names a bone past the count' % sk)
    return bad


# ------------------------------------------------------------------ a level archive
class Lv:
    """A Dog Days level to edit. src: a stock level name ('F01': KL_PortBackup wins) or a folder holding
    <X>_Main.zip and the files beside it (a kept build). files / order as in the archive."""

    def __init__(self, src):
        if os.path.isdir(src):
            zips = [f for f in sorted(os.listdir(src)) if f.lower().endswith('_main.zip')]
            if len(zips) != 1:
                raise ValueError('%s: expected one *_Main.zip' % src)
            path, self.name = os.path.join(src, zips[0]), zips[0][:-9]
            self.beside = {f[len(self.name) + 5:]: os.path.join(src, f) for f in sorted(os.listdir(src))
                           if f.startswith(self.name + '_Main') and f != zips[0]}
            # what else lies beside the archive (KLJoin.ini, graft.txt ...): carried along by write()
            self.side = {f: os.path.join(src, f) for f in sorted(os.listdir(src))
                         if not f.startswith(self.name + '_Main') and os.path.isfile(os.path.join(src, f))}
        else:
            import kl_graft
            path, self.name = J.level_zip(src, 'dd'), src
            self.beside = kl_graft.beside_of(src)
            self.side = {}
        with zipfile.ZipFile(path) as z:
            self.order = z.namelist()
            self.files = {n: z.read(n) for n in self.order}
        self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}
        self.src = path

    def __getitem__(self, ext):
        return self.files[self.ext[ext]]

    def __setitem__(self, ext, data):
        self.files[self.ext[ext]] = data

    def scene(self):
        """kl_prpjoin.Scene of the current .gms / .prp / .buf, and the unpacked .gms."""
        raw = kl_gms.unpack(self['.gms'])
        names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
        buf = self['.buf']
        for decl, tid, _prio in kl_gms.entities(raw):
            o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
            names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
        return J.Scene(Prp(self['.prp']), names, tids, 'dd', self.name), raw

    def write(self, folder, slot='F01'):
        """<folder>/<slot>_Main.zip and the files beside it: what `kl_graft.py install <slot> --from <folder>`
        takes. The folder is emptied of an earlier build of that slot first."""
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):
            if f.startswith(slot + '_Main'):
                os.remove(os.path.join(folder, f))
        ren = lambda n: n.replace('Locations/%s/%s_Main' % (self.name, self.name), 'Locations/%s/%s_Main' % (slot, slot))
        path = os.path.join(folder, slot + '_Main.zip')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
            for n in self.order:
                z.writestr(ren(n), self.files[n])
        for suffix, v in self.beside.items():
            shutil.copyfile(v, os.path.join(folder, slot + '_Main' + suffix))
        for f, v in self.side.items():                  # KLJoin.ini and the like; a build's own notes are rewritten by the caller
            if os.path.abspath(v) != os.path.abspath(os.path.join(folder, f)):
                shutil.copyfile(v, os.path.join(folder, f))
        return path


def gms_models(raw):
    """[(offset of the record's +0x0c in the unpacked .gms, value)] in entity-table order."""
    t = struct.unpack_from('<I', raw, 0)[0]
    out = []
    for k in range(struct.unpack_from('<I', raw, t)[0]):
        rec = 4 * (struct.unpack_from('<I', raw, t + 4 + 8 * k)[0] & 0xffffff)
        out.append((rec + 0x0c, struct.unpack_from('<I', raw, rec + 0x0c)[0]))
    return out


def person(sc, k):
    """(model chunk, variant, animation set) of a ZFFPlayer / ZFFActor node, from its properties."""
    lab = J.labels(sc.game, sc.cls(k))
    us = units(sc.nodes[k]['props'][1:-1])
    val = lambda name: us[lab.index(name)][0]
    return (struct.unpack('<I', val('ZGEOM[4]')[1])[0], struct.unpack('<I', val('ZLNKOBJ[0]')[1])[0],
            sc.p.key(val('ZLNKOBJ[2]')).split('#')[-1])


def find_node(sc, path):
    """Node index of a scene path given without ROOT ('Heroes!Hero_02\\Ground'); exactly one must match."""
    hits = sc.resolve('ROOT\\' + path)
    if len(hits) != 1:
        raise ValueError('%s: %d nodes named %r' % (sc.label, len(hits), path))
    return hits[0]


# ------------------------------------------------------------------ the Dead Men side
_SOURCE = {}


class Source:
    """A Dead Men level's models in Dog Days form: .prm / .MAT / .TEX converted as kl_graft.DeadMen does
    (kl_prm, kl_mat with Dog Days surface numbers, kl_tex), its scene for looking a character up, its
    .oct and its .ANM bone table."""

    def __init__(self, level, log=print):
        import kl_dmassets as D, kl_prm, kl_mat, kl_tex
        src = D.dm_level(level, exts=('tex', 'prm', 'mat', 'gms', 'prp', 'buf', 'oct', 'anm'))
        self.level = level
        self.sc = J.Scene.load(level, 'dm')
        roots = D.prm_roots(src['gms'], src['prp'], 'dm')
        prm, rep = kl_prm.convert(src['prm'], roots)
        self.prm = G.read(prm, 'dd')
        self.tex = T.read_tex(kl_tex.convert(src['tex'])[0])
        self.mat = T.read_mat(kl_mat.convert_mat_full(src['mat'], prm=prm, surface='dd',
                                                     texture_ids=set(T.read_tex(src['tex']).tex))[0])
        self.oct = O.Oct.parse(src['oct'])
        self.rec = {v: k for k, v in enumerate(self.oct.record_refs())}
        self.anm = kl_anm.Anm(src['anm'], 'dm').bones
        log('%s converted: %d chunks, %d materials, %d textures' % (level, len(self.prm.chunks) - 1, len(self.mat.insts), len(self.tex.tex)))

    @classmethod
    def get(cls, level, log=print):
        if level not in _SOURCE:
            _SOURCE[level] = cls(level, log)
        return _SOURCE[level]

    def root(self, what):
        """Model root of a character: a chunk index, or a scene path without ROOT."""
        if isinstance(what, int) or what.isdigit():
            return int(what)
        return person(self.sc, find_node(self.sc, what))[0]


def objects(p, root):
    n = p.u32(root, 0x14)
    return list(struct.unpack_from('<%dI' % n, p.chunks[p.u32(root, 0x18)]))


def look(p, root, mat=None):
    """{variant: {lod mask: [(material name or slot, vertices)]}} of a model."""
    out = {}
    for o in objects(p, root):
        c = p.chunks[o]
        d = p.u32(p.u32(o, 0x28), 0)
        m = p.u16(o, 0x12)
        out.setdefault(c[0x0f], {}).setdefault(c[0x0e], []).append((mat.insts[m].name if mat else m, p.u32(d, 0)))
    return out


def with_variants(p, root, vmap):
    """A NEW root (copy of `root`, own object table) that has exactly the variants of vmap {variant of the
    result: variant of the source}. Object chunks are reused where the byte already fits, else copied with
    the new variant byte (the geometry below stays shared). Returns (new root, objects kept)."""
    have = {p.chunks[o][0x0f] for o in objects(p, root)}
    for d, s in vmap.items():
        if s not in have:
            raise ValueError('root %d has no variant %d (has %r)' % (root, s, sorted(have)))
    tab, used = [], set()
    for o in objects(p, root):
        c = p.chunks[o]
        if p.u16(o, 2) != 8 or len(c) != 64:
            raise ValueError('object %d of root %d is not a 64-byte mesh' % (o, root))
        for d in sorted(d for d, s in vmap.items() if s == c[0x0f]):
            if d == c[0x0f] and o not in used:
                used.add(o); tab.append(o)
            else:
                tab.append(_new(p, c[:0x0f] + bytes([d]) + c[0x10:]))
                p.refs[-1] = p.refs[o]
    if not tab:
        raise ValueError('root %d: no object left' % root)
    r = p.chunks[root]
    r = _put(r, 0x14, '<II', len(tab), _new(p, _pad(struct.pack('<%dI' % len(tab), *tab))))
    new = _new(p, r); p.refs[new] = 1
    return new, len(tab)


# ------------------------------------------------------------------ put
Pick = collections.namedtuple('Pick', 'targets level source variants donor', defaults=(None,))
Pick.__doc__ = """targets: scene paths (no ROOT) of the Dog Days people that take the model (they must
share one model today or the pick says which to take the free bone from: the first); level, source: the
Dead Men map and the character's scene path or root chunk; variants: {} or {Dog Days variant: Dead Men variant}.
A pick WITHOUT targets only adds the model to the level's .prm (nobody is given it: wardrobe()); donor is
then the Dog Days model root whose free bone it gets, and variants names every variant it keeps."""


def wardrobe_roots(src):
    """The model roots a build's KLWardrobe.ini lists (Root= of every [Character.n]): models NO entity
    names, so every walk for 'what is live' has to be told (G.level_roots extra; kl_graft lighten).
    src: an Lv, a build folder, or the ini's path. [] when there is no such file."""
    path = src.side.get('KLWardrobe.ini') if isinstance(src, Lv) else os.path.join(src, 'KLWardrobe.ini') if os.path.isdir(src) else src
    if not path or not os.path.isfile(path):
        return []
    return [int(l.split('=')[1]) for l in open(path) if l.startswith('Root=')]


def dead_indices(p, sc, raw, oct_s, extra=(), log=print):
    """G.reuse() on a level's .prm: the indices of every chunk the level's own files do not reach are
    handed to the chunks that come next. Live = G.level_roots (the .gms records, the .prp fields, the scene
    block) + `extra` (roots no entity names: an earlier wardrobe's, or this run's Dead Men heroes). Kept as
    they are although dead: the 64-byte meshes the .oct tail pairs name (kl_graft keeps S's removed map's
    collision records). -> (free indices, bytes saved by the stubs)."""
    live = G.level_roots(sc.p, sc.tids, raw, extra)
    n, saved = G.reuse(p, live, {c for _f, c in oct_s.tail})
    log('  .prm: %d of %d chunks are dead (no root of the level reaches them): their indices are free for the new chunks%s' % (
        n, len(p.chunks) - 1, '; stubs save %.1f MB' % (saved / 1e6) if saved else ''))
    return n, saved


def compact_level(lv, log=print):
    """THE LEVEL'S .prm RENUMBERED WITHOUT ITS DEAD CHUNKS (G.compact), every holder of a chunk index this
    project knows rewritten. lv: Lv, edited in place. -> report; rep['roots'] = {old wardrobe root: new}.
    NOT LOADED LIVE, and unlike put() / wardrobe() it MOVES S's live chunks (HUD, fonts, effects, heroes),
    which no build has done before (the graft appends M's chunks and never moves S's). Rewritten here:
      .gms record +0x0c; the .prp fields and scene-block entries of G.prp_roots; the .oct - only the records
      a live model root owns stay (kl_octree.select_records: record offsets change, so every live root's
      +0x1c is rewritten, as kl_graft does for S's records), their tail pairs renumbered; the caller rewrites
      KLWardrobe.ini / chars.json (compact command below).
    ASSUMPTION: nothing else holds a chunk index. G.PRP_FIELDS was found statistically (integer fields whose
    non-zero values are ALL chunks of one kind over the 41 stock levels): a field that holds an index only
    now and then, or one inside a raw blob (.buf, .sgd, .HVK, a KEYS track), would not be in it. Evidence
    for: those roots reach 99.991 % of Dog Days' chunks. Use it when the chunk count needs it, not before."""
    sc, raw = lv.scene()
    raw = bytearray(raw)
    p, oc = G.read(lv['.prm'], 'dd'), O.Oct.parse(lv['.oct'])
    wr = wardrobe_roots(lv)
    kinds, _args = G.walk(p, G.level_roots(sc.p, sc.tids, raw, wr))
    q, cmap = G.compact(p, G.level_roots(sc.p, sc.tids, raw, wr))
    rec = {v: k for k, v in enumerate(oc.record_refs())}
    owners = [i for i in sorted(kinds) if kinds[i] == 'root' and p.u32(i, 0x1c)]
    keep = sorted({rec[p.u32(i, 0x1c)] for i in owners})
    oc2, refs = O.select_records(oc, keep, cmap)        # KeyError = a live record's pair on a dead mesh: never seen
    for i in owners:
        q.chunks[cmap[i]] = _put(q.chunks[cmap[i]], 0x1c, '<I', refs[p.u32(i, 0x1c)])
    n_gms = 0
    for off, was in gms_models(raw):
        if was:
            struct.pack_into('<I', raw, off, cmap[was]); n_gms += 1
    n_prp = 0
    for where, c, _kind in G.prp_roots(sc.p, sc.tids, J.schema('dd'), 'dd'):
        new = struct.pack('<I', cmap[c])
        if where[0] == 'scene':
            s = sc.p.settings
            k = next(k for k, tok in enumerate(s) if tok[0] == 0x0c and sc.p.key(tok) == where[1])
            s[k + 4] = (s[k + 4][0], new)
        else:
            node, ctrl, k = where
            toks = sc.nodes[node]['props'] if ctrl is None else sc.nodes[node]['ctrls'][ctrl][1]
            us = [list(u) for u in units(toks[1:-1])]
            us[k][0] = (us[k][0][0], new)
            toks = [toks[0]] + [t for u in us for t in u] + [toks[-1]]
            if ctrl is None:
                sc.nodes[node]['props'] = toks
            else:
                sc.nodes[node]['ctrls'][ctrl] = (sc.nodes[node]['ctrls'][ctrl][0], toks)
        n_prp += 1
    prm_bytes = G.write(q)
    mat = T.read_mat(lv['.MAT'])
    mat.refs = T.material_refs(prm_bytes)
    rep = dict(entries=(len(p.chunks), len(q.chunks)), prm_bytes=(len(lv['.prm']), len(prm_bytes)), gms_fields=n_gms, prp_fields=n_prp,
               oct_records=(len(oc.records), len(oc2.records)), oct_pairs=(len(oc.tail), len(oc2.tail)), roots={r: cmap[r] for r in wr})
    lv['.prm'], lv['.MAT'], lv['.oct'] = prm_bytes, T.write_mat(mat), oc2.pack()
    lv['.gms'], lv['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    # proof: the rewritten files reach a graph of the same shape, chunk for chunk
    sc2, raw2 = lv.scene()
    k2 = G.walk(q, G.level_roots(sc2.p, sc2.tids, raw2, sorted(rep['roots'].values())))[0]
    if len(k2) != len(q.chunks) - 1 or {cmap[i]: k for i, k in kinds.items()} != k2:
        raise ValueError('compact: the renumbered level does not reach its own file as before')
    log('  compact: %d -> %d chunk-table entries, .prm %.1f -> %.1f MB; %d .gms and %d .prp references, %d of %d .oct records and %d of %d pairs kept' % (
        rep['entries'] + tuple(x / 1e6 for x in rep['prm_bytes']) + (n_gms, n_prp, len(oc2.records), len(oc.records), len(oc2.tail), len(oc.tail))))
    return rep


def put(base, picks, free='add', union=True, log=print, reuse=True):
    """base: Lv (edited in place). Returns a report dict; see the module docstring for what changes.
    reuse: the new chunks go INTO the indices of the base's dead chunks before the file grows
    (dead_indices(); re/prm_limit.md). False = everything at the end, as before 2026-10-09 21:30."""
    sc, raw = base.scene()
    raw = bytearray(raw)
    models = gms_models(raw)
    prm_s = G.read(base['.prm'], 'dd')
    anm = kl_anm.Anm(base['.ANM'], 'dd')
    oct_s = O.Oct.parse(base['.oct'])
    freed = dead_indices(prm_s, sc, raw, oct_s, wardrobe_roots(base), log) if reuse else (0, 0)
    tex, mat = T.read_tex(base['.TEX']), T.read_mat(base['.MAT'])
    n_mat, n_tex, n_chunks = len(mat.insts), len(tex.tex), len(prm_s.chunks) - 1
    rep = dict(picks=[], anm_added=[])
    ids = level_ids(prm_s)                              # the destination's bone ids, extended as models come
    by_level = collections.OrderedDict()
    for pk in picks:
        by_level.setdefault(pk.level, []).append(pk)
    new_slots = set()
    for level, pks in by_level.items():
        src = Source.get(level, log)
        # one extract for all picks of this map: what two characters share stays shared
        want = sorted({src.root(pk.source) for pk in pks})
        ex, cmap = G.extract(src.prm, want)
        work, todo = [], []
        for pk in pks:
            nodes = [find_node(sc, t) for t in pk.targets]
            for k in nodes:
                if sc.cls(k) not in PEOPLE:
                    raise ValueError('%s is a %s, not a character' % (sc.path[k], sc.cls(k)))
            ppl = [person(sc, k) for k in nodes]
            r0 = cmap[src.root(pk.source)]
            have = sorted({ex.chunks[o][0x0f] for o in objects(ex, r0)})
            vmap = {v: (v if v in have else have[0]) for v in {1, 2} | {v for _m, v, _s in ppl}} if nodes else {}
            vmap.update(pk.variants or {})
            root, nobj = with_variants(ex, r0, vmap)
            sk = skeleton(ex, root)
            if not sk:
                raise ValueError('%s %s: the model has no skeleton' % (level, pk.source))
            # the free bone, with the rest values of the Dog Days model the first target has today
            fb, free_here = None, free
            if FREE_NAME not in bone_names(ex, sk):
                droot = ppl[0][0] if ppl else pk.donor
                donor = free_bone(prm_s, skeleton(prm_s, droot)) if droot and skeleton(prm_s, droot) else None
                if free == 'add' and donor:
                    fb = 'added as bone %d' % add_free_bone(ex, sk, donor)
                elif free == 'add':                     # no Dog Days model to take the rest values from
                    free_here = 'alias'
            renamed = reid(ex, sk, ids)
            if fb is None and free_here == 'alias' and FREE_NAME not in bone_names(ex, sk):
                fb = 'bone id 33 -> GROUND' if alias_free_bone(ex, sk) else None
            # the id each bone carries itself (definition +0x3e) must lead back to it through table [5]:
            # a bullet mark looks the bone up that way (kl_impact; the builds made before needed its 'fix')
            import kl_impact
            kl_impact.sync_bone_ids(ex, [sk])
            # animation numbers of the destination; a name its table lacks is appended to the table
            number = anm_number(anm.bones)
            for s in bone_names(ex, sk):
                if s.lower() not in number:
                    anm.bones.append(s); rep['anm_added'].append(s)
                    number = anm_number(anm.bones)
            moved = rebind(ex, sk, number)
            # the source root's .oct record: an empty tree on every character seen; anything else is not handled
            ref = src.prm.u32(src.root(pk.source), 0x1c)
            rec = src.oct.records[src.rec[ref]] if ref else None
            if rec is not None and rec.tree.items:
                raise ValueError('%s %s: its .oct record lists %d triangle batches (not handled: the batches '
                                 'name mesh objects, which were renumbered)' % (level, pk.source, len(rec.tree.items)))
            work.append((pk, nodes, ppl, root, vmap, nobj, sk, fb, (moved, renamed), rec))
        roots = [w[3] for w in work]
        ex, cmap2 = G.extract(ex, roots)                # drops what the edits orphaned
        # materials and textures of what is left
        kinds, args = G.walk(ex, [cmap2[r] for r in roots])
        slots = {ex.u16(i, 0x12) for i, k in kinds.items() if k == 'mesh'}
        tex, tmap = T.merge_tex(tex, src.tex, set(T.used_textures(src.mat, slots)))
        before = set(mat.insts)
        mat, mmap = T.merge_mat(mat, src.mat, slots, tmap)
        new_slots |= set(mat.insts) - before
        # .oct records, then the model
        refs0 = oct_s.record_refs()
        recs = [w[9] for w in work]
        for w in work:
            if w[9] is not None:
                t = w[9].tree
                oct_s.records.append(O.Record(w[9].vtable, w[9].pointer, O.Tree(t.origin, t.scale, [list(n) for n in t.nodes], [], t.fill)))
        refs1 = oct_s.record_refs()
        if refs1[:len(refs0)] != refs0:
            raise ValueError('appending .oct records moved the base level\'s records')
        new_refs = iter(refs1[len(refs0):])
        for w in work:
            r = cmap2[w[3]]
            ex.chunks[r] = _put(ex.chunks[r], 0x1c, '<I', next(new_refs) if w[9] is not None else 0)
        prm_s, cmap3 = G.append(prm_s, ex, [cmap2[r] for r in roots], mmap, None, tmap)
        for pk, nodes, ppl, root, vmap, nobj, sk, fb, moved, rec in work:
            new = cmap3[cmap2[root]]
            for k, (old, var, aset) in zip(nodes, ppl):
                off, was = models[k - 1]
                if was != old:
                    raise ValueError('%s: .gms model %d, .prp model %d' % (sc.path[k], was, old))
                struct.pack_into('<I', raw, off, new)
                lab = J.labels('dd', sc.cls(k))
                node = sc.nodes[k]
                us = [list(u) for u in units(node['props'][1:-1])]
                us[lab.index('ZGEOM[4]')] = [(us[lab.index('ZGEOM[4]')][0][0], struct.pack('<I', new))]
                node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]
            nsk = skeleton(prm_s, new)
            rep['picks'].append(dict(targets=list(pk.targets), source='%s %s' % (level, pk.source), old_models=sorted({m for m, _v, _s in ppl}),
                                     new_model=new, bones=prm_s.u32(nsk, 0), objects=nobj, variants=dict(sorted(vmap.items())),
                                     target_variants=sorted({v for _m, v, _s in ppl}), sets=sorted({s for _m, _v, s in ppl}),
                                     free_bone=fb, renumbered_bones=moved[0], bone_ids_changed=moved[1]))
    prm_bytes = G.write(prm_s)
    mat.refs = T.material_refs(prm_bytes)
    fxc = base['.fxc']
    upath = os.path.join(workdir(), 'build', 'shared', 'union.fxc')
    if union and os.path.isfile(upath):
        fxc = T.merge_fxc(fxc, open(upath, 'rb').read())
    import kl_light
    fit = kl_light.fit_shaders(mat, fxc, slots=sorted(new_slots), log=log)
    rep.update(chunks=(n_chunks, len(prm_s.chunks) - 1), materials=(n_mat, len(mat.insts)), textures=(n_tex, len(tex.tex)),
               free_indices=(freed[0], len(prm_s.free)), stub_bytes_saved=freed[1],
               prm_bytes=(len(base['.prm']), len(prm_bytes)), new_material_slots=sorted(new_slots),
               shaders_fitted={mat.insts[s].name: v[1] for s, v in fit['fixed'].items()},
               shaders_missing=[v[0] for v in fit['unresolved'].values()])
    base['.prm'], base['.MAT'], base['.TEX'], base['.fxc'] = prm_bytes, T.write_mat(mat), T.write_tex(tex), fxc
    base['.oct'], base['.gms'], base['.prp'] = oct_s.pack(), kl_gms.pack(bytes(raw)), sc.p.serialize()
    if rep['anm_added']:
        base['.ANM'] = anm.save()
    return rep


# ------------------------------------------------------------------ the wardrobe
# Every heister body with every mask, as VARIANTS of one model per character (module docstring, WARDROBE).
MASKS = 8
V_FACE, V_OWN = 1, 2                             # the two variants stock Dog Days sets (masks off / on)
OUTFIT_STEP = 10                                 # variant = 10 * body + (1 face | 2 own mask | 2 + m mask m)
# EVERY LOOK A DEAD MEN FRAGILE ALLIANCE HERO HAS (measured on the four FA maps, whose eight hero models are the
# same objects in each: `python kl_chars.py looks`). A hero carries 24 variants,
#       Dead Men variant = 1 + armour + 4 * shirt + 8 * head
#   armour 0..3  the body mesh (Merc_Rank3_8): four meshes of growing vertex count. The game's own loading tip 13:
#                'The better weapon pack you buy, the better tactical armour you get'.
#   shirt  0..1  material playstyle_01a / playstyle_04 on the same mesh. Tip 4: 'Traitors spawn with a black shirt
#                in the next round'. (Hero_06 has no such part: his two shirts are one look.)
#   head   0..2  material multiplayer_headset01_Rank_01 / 02 / 03: on Kane and Lynch a 12-vertex earpiece, on the
#                six others THE BALACLAVA (the whole head). Tip 10: 'Balaclavas show who is leading: the darker
#                it is, the higher ...'.
# An OUTFIT of the wardrobe is one of them: outfit = Dead Men variant - 1 (0..23); body = outfit % 8 (armour and
# shirt), head = outfit // 8. A mask replaces the head, so the head choice only shows with the hero's own face:
#       face, head 0       variant = 10 * body + 1                       1, 11 .. 71
#       own mask / mask m  variant = 10 * body + 2 / + 2 + m             2..10, 12..20 .. 72..80
#       face, head 1 / 2   variant = HEAD_BASE + 8 * (head - 1) + body   81..96
# 96 variants, all below 128 (the variant is a byte in the mesh object; whether the engine reads it signed was
# not looked up, so the numbering stays where the sign cannot matter). KLWardrobe.ini Version 2; klchar.c holds
# the same formula.
DM_ARMOUR = ('Plain clothes', 'Light vest', 'Tactical vest', 'Heavy armour')     # names: by the look in kl_view (re/wardrobe.md)
DM_SHIRT = ('', 'black shirt')
DM_HEADS = ('', 'dark balaclava', 'black balaclava')
# THE SHIRT AND HEAD CHOICES ARE NOT IN DEAD MEN'S FILES AS PICTURES: playstyle_01a and playstyle_04 are the same
# material instance but for the name, and so are multiplayer_headset01_Rank_01 / 02 / 03 (02 / 03 differ from 01
# in the cull mode only) - same textures, same constants (compared node by node on M01_FA_A). Dead Men's code
# must colour them at run time by which material it is (the loading tips say what the player saw); Dog Days'
# exe has no such code, so all 24 variants would be drawn as 4. TINT makes the difference real the only way a
# level file can: the material gets a DARKENED COPY of its diffuse texture (one texture each, in the .TEX; the
# .prm does not grow). ASSUMPTION: the shades - Dead Men's own values are not in its level files.
TINT = (('playstyle_04', 0.16), ('multiplayer_headset02', 0.50), ('multiplayer_headset03', 0.22))
DM_BODIES = len(DM_ARMOUR) * len(DM_SHIRT)       # 8
DM_LOOKS = DM_BODIES * len(DM_HEADS)             # 24 = the Dead Men variants 1..24
HEAD_BASE = OUTFIT_STEP * DM_BODIES + 1          # 81
DM_HEAD = ('head', 'hair', 'eyelash', 'eye_', 'headset', 'glass')    # Dead Men materials a mask replaces
# The names of Dead Men's eight Fragile Alliance ranks, from its own .LOC (AllLevels/Menu/Online/Profile/
# FragileAllianceRank_01..08: 'Kane, no1 of The7', 'Lynch, Psycho7', 'Ashkanan, no2 of The7' ... 'Hutchison, no7
# of The7'). ASSUMPTION: rank n is the model Hero_0n - true for 01 and 02 by their head materials (Hero = Kane,
# Little = Lynch); nothing in the level files ties 03..08 to a name.
DM_NAMES = ('Kane', 'Lynch', 'Ashkanan', 'Meldal', 'Red', 'Parker', 'Standen', 'Hutchison')
DD_NAMES = ('J.C.', 'Tommy', 'Pierre', 'Liam', 'Jean', 'Elwood', 'Bud', 'Mitchel')    # .LOC FACharacters C1..C8
HERO = 'Heroes!Hero_%02d\\Ground'
MAX_REST = 0.3                                   # a bone of two skeletons is 'the same' when its rest matrices agree to this


def _darker(entry, k, ident):
    """A copy of a texture record (kl_tex docstring) with every colour multiplied by k and the id `ident`.
    DXT1 / DXT3 / DXT5 only: the two 565 end colours of each block are scaled; where that reverses their order
    (which selects the block's mode in DXT1) they are swapped and the indices with them. The name keeps its
    length (the last character becomes '~': nothing is known to look a texture up by name, but two records with
    one name need not exist either)."""
    size, f1 = struct.unpack_from('<I4s', entry, 0)
    if f1 not in (b'1TXD', b'3TXD', b'5TXD'):
        raise ValueError('texture %d is %r: only DXT1 / DXT3 / DXT5 can be darkened' % (struct.unpack_from('<I', entry, 12)[0], f1))
    mips = struct.unpack_from('<I', entry, 20)[0]
    e = bytearray(entry)
    struct.pack_into('<I', e, 12, ident)
    q = e.index(b'\0', 36)
    e[q - 1] = ord('~')
    q += 1
    step, off = (8, 0) if f1 == b'1TXD' else (16, 8)
    sc = lambda c: (int((c >> 11) * k + 0.5) << 11) | (int(((c >> 5) & 63) * k + 0.5) << 5) | int((c & 31) * k + 0.5)
    for _m in range(mips):
        n = struct.unpack_from('<I', e, q)[0]
        for o in range(q + 4 + off, q + 4 + n - 7, step):
            c0, c1, bits = struct.unpack_from('<HHI', e, o)
            d0, d1 = sc(c0), sc(c1)
            four = c0 > c1 or step == 16
            if four and d0 == d1 and step == 8:
                bits = 0                                 # one colour left: every pixel takes it (index 3 would turn transparent)
            elif (d0 > d1) != (c0 > c1) and d0 != d1:
                d0, d1 = d1, d0                          # order reversed: swap the ends, and 0 <-> 1 (2 <-> 3 in four-colour mode)
                bits = sum(((x ^ 1) if (four or x < 2) else x) << (2 * i) for i in range(16) for x in [(bits >> (2 * i)) & 3])
            struct.pack_into('<HHI', e, o, d0, d1, bits)
        q += 4 + n
    return bytes(e)


def tint(mat, tex, slots, log=print):
    """TINT on the material slots given: each named material gets a darkened copy of its diffuse texture under a
    new texture id. Returns {material name: (old texture, new texture, factor)}."""
    out = {}
    for s in sorted(slots):
        nm = mat.insts[s].name.split('/')[-1]
        k = dict(TINT).get(nm)
        if k is None:
            continue
        for path, node in T.walk(mat.insts[s].root):
            if node[0] == 'TEXT' and any(c[0] == 'NAME' and c[3].rstrip(b'\0') == b'mapDiffuse' for c in node[3]):
                txid = next(c for c in node[3] if c[0] == 'TXID')
                old = txid[3]
                if old not in tex.tex or tex.tex[old].frames is not None or tex.tex[old].faces:
                    raise ValueError('material %s: its diffuse texture %d is not a plain picture' % (nm, old))
                new = next(i for i in range(128, tex.slots) if i not in tex.tex)
                tex.tex[new] = T.Texture(_darker(tex.tex[old].entry, k, new), group=tex.tex[old].group)
                txid[3] = new
                out[nm] = (old, new, k)
    return out


def variant_of(outfit, mask):
    """outfit: 0..23 (0 on a Dog Days body); mask: 0 = the character's own face, 1..8 = that heister's mask,
    -1 = 'own' (the stock toggle's 2)."""
    body, head = outfit % DM_BODIES, outfit // DM_BODIES
    if mask == 0 and head:
        return HEAD_BASE + DM_BODIES * (head - 1) + body
    return OUTFIT_STEP * body + (V_FACE if mask == 0 else V_OWN if mask < 0 else V_OWN + mask)


def outfit_name(outfit):
    """The label of a Dead Men outfit (mkoverlay.py's Outfit row prints the same list)."""
    a, sh, hd = outfit % 4, outfit // 4 % 2, outfit // DM_BODIES
    return ', '.join(x for x in (DM_ARMOUR[a], DM_SHIRT[sh], DM_HEADS[hd]) if x)


def _palette(p, o):
    """Bone indices of a weighted mesh object in the order its vertices number them (the runs, expanded)."""
    nr, bc = p.u32(o, 0x38), p.chunks[p.u32(o, 0x3c)]
    if len(bc) not in (8 * nr, 8 * nr + 8) or p.chunks[o][0x0c] != 3 or len(p.chunks[o]) != 64:
        raise ValueError('object %d is not a weighted mesh with %d bone runs' % (o, nr))
    runs = struct.unpack_from('<%dI' % (2 * nr), bc)
    return [b for k in range(nr) for b in range(runs[2 * k + 1] // 12, (runs[2 * k + 1] + runs[2 * k]) // 12)]


def _runs(bones):
    """The runs chunk for a palette: {12 * count, 12 * first bone} per stretch of consecutive bones."""
    out = []
    for b in bones:
        if out and out[-1][1] + out[-1][0] == b:
            out[-1][0] += 1
        else:
            out.append([1, b])
    return len(out), _pad(b''.join(struct.pack('<II', 12 * n, 12 * b) for n, b in out))


def _rest(p, sk):
    h = struct.unpack('<20I', p.chunks[sk])
    return [struct.unpack_from('<12f', p.chunks[h[2]], 48 * b) for b in range(h[0])]


class _Fit:
    """Bones of skeleton `src` as bones of skeleton `dst` of the same file, by name. A bone `dst` lacks, or
    has somewhere else at rest (more than MAX_REST away: the face bones sit where each head has its mouth and
    brows, up to 3 units apart between two heisters; the body bones agree to 0.2), is its nearest ancestor that
    fits: the vertices then move rigidly with that bone - a borrowed mask follows the head but not the jaw."""

    def __init__(self, p, src, dst):
        sn, par = bone_names(p, src), bone_parents(p, src)
        dn = {s.lower(): i for i, s in enumerate(bone_names(p, dst))}
        self.same, self.names = src == dst, sn
        self.map, self.exact = [], []
        rs, rd = _rest(p, src), _rest(p, dst)
        far = lambda a: max(abs(x - y) for x, y in zip(rs[a], rd[dn[sn[a].lower()]]))
        for b in range(len(sn)):
            a = b
            while a >= 0 and (sn[a].lower() not in dn or (not self.same and far(a) > MAX_REST)):
                a = par[a]
            if a < 0:
                raise ValueError('skeleton %d: bone %s has no ancestor in skeleton %d' % (src, sn[b], dst))
            self.map.append(dn[sn[a].lower()]); self.exact.append(a == b)
        self.dpar = bone_parents(p, dst)
        self.low = min(struct.unpack_from('<8H', p.chunks[dst], 0x38)[1:6])     # bones kept at low detail
        self.rest = [max(abs(x - y) for x, y in zip(rs[b], rd[self.map[b]])) if self.exact[b] else 0.0 for b in range(len(sn))]


def _moved(p, o, fit, variant, note):
    """A copy of mesh object `o` (64 bytes; the geometry below it stays shared) with the variant byte given
    and, when it comes from another skeleton, its bone runs rewritten for the destination's bone order."""
    c = p.chunks[o]
    c = c[:0x0f] + bytes([variant]) + c[0x10:]
    if not fit.same:
        bones = _palette(p, o)
        new = [fit.map[b] for b in bones]
        if c[0x0e] & 0xfc:                            # drawn at low detail: only the leading bones are updated there
            for k, b in enumerate(new):
                while b >= fit.low:
                    b = fit.dpar[b]; note['low'] += 1
                new[k] = b
        note['inexact'] += sum(1 for b in bones if not fit.exact[b])
        for b in bones:
            if fit.rest[b] > note['rest']:
                note['rest'], note['worst'] = fit.rest[b], '%s of object %d' % (fit.names[b], o)
            note['by_bone'][fit.names[b]] = max(note['by_bone'].get(fit.names[b], 0.0), fit.rest[b])
        nr, chunk = _runs(new)
        cache = note.setdefault('runs', {})            # one chunk per distinct palette: a mask is copied 9 x 8 times a body
        if chunk not in cache:
            cache[chunk] = _new(p, chunk)
        c = _put(c, 0x38, '<II', nr, cache[chunk])
    i = _new(p, c); p.refs[i] = p.refs[o]
    return i


def _set_objects(p, root, objs):
    """Give a model root a new object table (the root chunk is rewritten in place)."""
    p.chunks[root] = _put(p.chunks[root], 0x14, '<II', len(objs), _new(p, _pad(struct.pack('<%dI' % len(objs), *objs))))


def wardrobe(base, level='M01_FA_A', free='add', log=print, armour=(0, 1, 2, 3), fix_bones=False, reuse=True):
    """base: Lv of a Dog Days level with the eight stock heisters (edited in place). Returns the report:
    report['characters'] = 16 dicts (name, root, slot, outfits), report['roots'] = the sixteen model roots.
    armour: the Dead Men armour levels whose body meshes join the file (each costs 2.9 - 4.9 MB of .prm over the
    eight heroes, `python kl_chars.py wardrobe` prints it). A level left out keeps its variant numbers and is drawn
    with the nearest lower level that is in, so every outfit the menu offers shows a body in every build.
    fix_bones: also repair the bone-id bytes of the BASE's own skeletons (kl_impact.sync_bone_ids on the whole
    file - what `kl_impact.py fix` does; a base grafted before 2026-10-09 18:00 needs it).
    reuse: the models and the 15,500 object copies take the indices of the base's dead chunks (put()); the
    file only grows when they run out. Lighten the base FIRST (kl_graft lighten): after this no dead root
    is left for trim / slim to find, and a later trim must be told the Dead Men roots (wardrobe_roots)."""
    armour = sorted(set(armour))
    if not armour or armour[0] != 0 or armour[-1] > 3:
        raise ValueError('armour levels: 0 (the suit) must be in, 3 is the highest')
    stand_in = lambda v: 1 + max(a for a in armour if a <= (v - 1) % 4) + 4 * ((v - 1) // 4)     # Dead Men variant drawn for variant v
    sc, raw = base.scene()
    old = [person(sc, find_node(sc, HERO % n))[0] for n in range(1, 9)]
    if len(set(old)) != 8:
        raise ValueError('%s: the eight heisters do not have eight models (%r) - already a wardrobe build?' % (base.name, old))
    # 1. the eight Dead Men heroes join the file with their own skeletons, as nobody's model yet
    size0 = len(base['.prm'])
    rep = put(base, [Pick((), level, HERO % n, {v: stand_in(v) for v in range(1, DM_LOOKS + 1)}, old[n - 1]) for n in range(1, 9)],
              free=free, log=log, reuse=reuse)
    size1 = len(base['.prm'])
    dm = [r['new_model'] for r in rep['picks']]
    sc, raw = base.scene(); raw = bytearray(raw)
    models = gms_models(raw)
    p, mat = G.read(base['.prm'], 'dd'), T.read_mat(base['.MAT'])
    tex = T.read_tex(base['.TEX'])
    tints = tint(mat, tex, rep['new_material_slots'], log)
    if len(tints) != len(TINT):
        raise ValueError('the shirt / balaclava materials were not all found (%r): are these Dead Men\'s FA heroes?' % sorted(tints))
    oct_s = O.Oct.parse(base['.oct'])
    if reuse:                                         # what put() left free (the Dead Men roots are nobody's model yet)
        dead_indices(p, sc, raw, oct_s, dm + wardrobe_roots(base), log=lambda *_a: None)
    mname = lambda o: mat.insts[p.u16(o, 0x12)].name.split('/')[-1].lower()
    # 2. the parts. Dog Days: variant 1 is the face look; variant 2 is mask + masked body (+ the bag)
    face, body, mask, bag = {}, {}, {}, {}
    for n in range(8):
        objs = objects(p, old[n])
        if {p.chunks[o][0x0f] for o in objs} != {V_FACE, V_OWN}:
            raise ValueError('heister %d: model %d has variants %r, not 1 and 2' % (n + 1, old[n], sorted({p.chunks[o][0x0f] for o in objs})))
        face[n] = [o for o in objs if p.chunks[o][0x0f] == V_FACE]
        two = [o for o in objs if p.chunks[o][0x0f] == V_OWN]
        mask[n] = [o for o in two if 'mask' in mname(o)]
        bag[n] = [o for o in two if 'moneybag' in mname(o)]
        body[n] = [o for o in two if o not in mask[n]]            # the bag stays with the body
        if {p.chunks[o][0x0e] for o in mask[n]} != {1, 2, 0x7c} or not bag[n]:
            raise ValueError('heister %d: mask or bag objects are not what this tool knows' % (n + 1))
    dbody, dhead = {}, {}
    part = lambda o: (p.chunks[o][0x0e], p.u16(o, 0x12), p.u32(o, 0x28))        # what an object draws: detail, material, geometry
    for n in range(8):
        for k in range(DM_LOOKS):
            objs = [o for o in objects(p, dm[n]) if p.chunks[o][0x0f] == k + 1]
            dhead[n, k] = [o for o in objs if any(s in mname(o) for s in DM_HEAD)]
            dbody[n, k] = [o for o in objs if o not in dhead[n, k]]
            if {p.chunks[o][0x0e] for o in dbody[n, k]} != {1, 2, 0x7c}:
                raise ValueError('Dead Men hero %d outfit %d: no body at every level of detail' % (n + 1, k))
            # the numbering this tool relies on: the body is the same whatever the head choice
            if sorted(map(part, dbody[n, k])) != sorted(map(part, dbody[n, k % DM_BODIES])):
                raise ValueError('Dead Men hero %d: the body of variant %d is not that of variant %d' % (n + 1, k + 1, k % DM_BODIES + 1))
    skel_dd, skel_dm = [skeleton(p, r) for r in old], [skeleton(p, r) for r in dm]
    # 3. the new models
    chars, note = [], dict(low=0, inexact=0, rest=0.0, worst='', by_bone={})
    refs0 = oct_s.record_refs(); rec_of = {v: k for k, v in enumerate(refs0)}
    new_dd = []
    for n in range(8):                                # Dog Days heister n: stock objects + every other mask
        same = _Fit(p, skel_dd[n], skel_dd[n])
        objs = list(objects(p, old[n]))
        for m in range(8):
            fit = _Fit(p, skel_dd[m], skel_dd[n])
            objs += [_moved(p, o, same, variant_of(0, m + 1), note) for o in body[n]]
            objs += [_moved(p, o, fit, variant_of(0, m + 1), note) for o in mask[m]]
        root = _new(p, p.chunks[old[n]]); p.refs[root] = 1
        _set_objects(p, root, objs)
        r = oct_s.records[rec_of[p.u32(old[n], 0x1c)]]
        if r.tree.items:
            raise ValueError('heister %d: its .oct record is not an empty tree' % (n + 1))
        oct_s.records.append(O.Record(r.vtable, r.pointer, O.Tree(r.tree.origin, r.tree.scale, [list(x) for x in r.tree.nodes], [], r.tree.fill)))
        new_dd.append(root)
        chars.append(dict(name=DD_NAMES[n], game='dd', slot=n, root=root, outfits=1, bodies=1, heads=1, objects=len(objs), bones=p.u32(skel_dd[n], 0)))
    refs1 = oct_s.record_refs()
    if refs1[:len(refs0)] != refs0:
        raise ValueError('appending .oct records moved the base level\'s records')
    for root, ref in zip(new_dd, refs1[len(refs0):]):
        p.chunks[root] = _put(p.chunks[root], 0x1c, '<I', ref)
    for n in range(8):                                # Dead Men hero n on its own skeleton: face, masks, the bag
        own = _Fit(p, skel_dm[n], skel_dm[n])
        fbag = _Fit(p, skel_dd[n], skel_dm[n])
        objs = []
        carry = [o for o in bag[n]]
        fits = {m: _Fit(p, skel_dd[m], skel_dm[n]) for m in range(8)}
        for k in range(DM_LOOKS):                     # own face: every armour, shirt and head
            objs += [_moved(p, o, own, variant_of(k, 0), note) for o in dbody[n, k] + dhead[n, k]]
            objs += [_moved(p, o, fbag, variant_of(k, 0), note) for o in carry]
        for k in range(DM_BODIES):                    # masked: every armour and shirt (the mask is the head)
            for m in [-1] + list(range(8)):           # 'own' (what the stock mask toggle asks for) = mask n
                v = variant_of(k, m + 1 if m >= 0 else -1)
                objs += [_moved(p, o, own, v, note) for o in dbody[n, k]]
                objs += [_moved(p, o, fits[n if m < 0 else m], v, note) for o in mask[n if m < 0 else m]]
                objs += [_moved(p, o, fbag, v, note) for o in carry]
        _set_objects(p, dm[n], objs)
        chars.append(dict(name=DM_NAMES[n], game='dm', slot=n, root=dm[n], outfits=DM_LOOKS, bodies=DM_BODIES, heads=len(DM_HEADS),
                          objects=len(objs), bones=p.u32(skel_dm[n], 0)))
    if note['rest'] > MAX_REST:
        raise ValueError('a moved object\'s bone rests %.2f units from where it did (limit %.1f): %s; per bone %r' % (
            note['rest'], MAX_REST, note['worst'], sorted(((round(v, 2), k) for k, v in note['by_bone'].items() if v > 0.3), reverse=True)))
    # 4. the heisters (and the bots that share their models) take the new Dog Days models
    moved = []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) in PEOPLE and person(sc, k)[0] in old:
            new = new_dd[old.index(person(sc, k)[0])]
            off, was = models[k - 1]
            struct.pack_into('<I', raw, off, new)
            lab = J.labels('dd', sc.cls(k)); node = sc.nodes[k]
            us = [list(u) for u in units(node['props'][1:-1])]
            us[lab.index('ZGEOM[4]')] = [(us[lab.index('ZGEOM[4]')][0][0], struct.pack('<I', new))]
            node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]
            moved.append((sc.path[k][5:], was, new))
    fixed = 0
    if fix_bones:
        import kl_impact
        fixed = kl_impact.sync_bone_ids(p)
    prm_bytes = G.write(p)
    mat.refs = T.material_refs(prm_bytes)
    base['.prm'], base['.MAT'], base['.oct'] = prm_bytes, T.write_mat(mat), oct_s.pack()
    base['.TEX'] = T.write_tex(tex)
    base['.gms'], base['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    rep.update(characters=chars, roots=[c['root'] for c in chars], stock_roots=old, retargeted=moved, level=level,
               bones_folded_for_low_detail=note['low'], bones_on_an_ancestor=note['inexact'], largest_rest_distance=round(note['rest'], 3),
               chunks=(rep['chunks'][0], len(p.chunks) - 1), prm_bytes=(rep['prm_bytes'][0], len(prm_bytes)),
               free_indices=(rep['free_indices'][0], len(p.free)),
               armour=armour, base_bone_ids_repaired=fixed, tints={k: list(v) for k, v in tints.items()}, textures=(rep['textures'][0], len(tex.tex)),
               cost=dict(dead_men_models=size1 - size0, looks=len(prm_bytes) - size1, total=len(prm_bytes) - size0,
                         objects=sum(c['objects'] for c in chars)))
    return rep


def wardrobe_ini(rep, path):
    """KLWardrobe.ini beside the level archive: what klhook\\klchar.c needs to dress the player on THIS build
    (the model roots are chunk numbers of this build's .prm)."""
    with open(path, 'w', newline='\r\n') as f:
        f.write('; written by tools/kl_chars.py wardrobe - belongs to the level archive beside it (klhook\\klchar.c)\n')
        f.write('; outfit = body + Bodies * head (a Dead Men body: body = armour 0..3 + 4 * shirt 0..1, head 0..2)\n')
        f.write('; variant of a look = %d * body + (1 own face | 2 own mask | 2 + m mask of heister m);\n' % OUTFIT_STEP)
        f.write(';                     own face with head 1.. = HeadBase + Bodies * (head - 1) + body\n')
        f.write('[Wardrobe]\nVersion=2\nCharacters=%d\nMasks=%d\nOutfitStep=%d\nHeadBase=%d\n' % (len(rep['characters']), MASKS, OUTFIT_STEP, HEAD_BASE))
        for i, c in enumerate(rep['characters'], 1):
            f.write('[Character.%d]\nName=%s\nRoot=%d\nSlot=%d\nOutfits=%d\nBodies=%d\nHeads=%d\nStock=%d\n' % (
                i, c['name'], c['root'], c['slot'], c['outfits'], c['bodies'], c['heads'], c['game'] == 'dd'))


def check_wardrobe(lv, rep):
    """What must hold for the sixteen models whatever the game does with them. -> problems."""
    bad = []
    p = G.read(lv['.prm'], 'dd')
    for c in rep['characters']:
        r, sk = c['root'], skeleton(p, c['root'])
        low, n = min(struct.unpack_from('<8H', p.chunks[sk], 0x38)[1:6]), p.u32(sk, 0)
        have = collections.defaultdict(set)
        for o in objects(p, r):
            ch = p.chunks[o]
            have[ch[0x0f]].add(ch[0x0e])
            try:
                bones = _palette(p, o)
            except ValueError as e:
                bad.append('%s: %s' % (c['name'], e)); continue
            if max(bones) >= n or (ch[0x0e] & 0xfc and max(bones) >= low):
                bad.append('%s: object %d (detail %02x) uses bone %d of %d (%d kept at low detail)' % (c['name'], o, ch[0x0e], max(bones), n, low))
            d = p.u32(p.u32(o, 0x28), 0); v = p.chunks[p.u32(d, 4)]
            top = max(v[52 * k + 24 + j] for k in range(p.u32(d, 0)) for j in range(4))
            if top // 3 >= len(bones):
                bad.append('%s: object %d: a vertex names palette entry %d of %d' % (c['name'], o, top // 3, len(bones)))
        want = {variant_of(k, 0) for k in range(c['outfits'])} | {variant_of(k, m) for k in range(c['bodies']) for m in range(-1, MASKS + 1)}
        if max(want) > 127:
            bad.append('%s: variant %d does not fit below 128' % (c['name'], max(want)))
        if set(have) != want:
            bad.append('%s: variants %r, expected %r' % (c['name'], sorted(have), sorted(want)))
        for v, lods in sorted(have.items()):
            if not {1, 2, 0x7c} <= lods:
                bad.append('%s: variant %d is not drawn at every level of detail (%r)' % (c['name'], v, sorted(lods)))
    if len(set(rep['roots'])) != len(rep['roots']):
        bad.append('two characters share a model root')
    return bad


# ------------------------------------------------------------------ checks
def check(lv, stock=None, roots=None, log=print, extra=()):
    """Re-read a level under every checker there is. stock: the Lv it was made from (then: everything of the
    stock level is still there, unchanged). roots: the new model roots (their skeletons must be bound to
    this level's .ANM; with None every skeleton of the file is tested, which a stock level passes).
    Returns the list of problems; logs counts."""
    import kl_dmassets as D, kl_prm, kl_mat, kl_tex, kl_light
    bad = []
    sc, raw = lv.scene()
    sch = J.schema('dd')
    # .gms <-> .prp
    models = gms_models(raw)
    people = 0
    for k in range(1, len(sc.nodes)):
        cls = sc.cls(k)
        why = sch.misfit(cls, sc.nodes[k]['props']) if cls else 'unregistered class'
        if why:
            bad.append('%s: %s' % (sc.path[k], why))
        if cls and 'ZGEOM[4]' in J.labels('dd', cls):
            v = struct.unpack('<I', units(sc.nodes[k]['props'][1:-1])[J.labels('dd', cls).index('ZGEOM[4]')][0][1])[0]
            if v != models[k - 1][1] and v and models[k - 1][1]:
                bad.append('%s: .prp model %d, .gms model %d' % (sc.path[k], v, models[k - 1][1]))
        people += cls in PEOPLE
    # .prm under Dog Days' rules, every root reachable
    proots = D.prm_roots(lv['.gms'], lv['.prp'], 'dd') + [r for r in extra]      # extra: models no entity names (wardrobe)
    try:
        counts = kl_prm.check(lv['.prm'], proots)
    except ValueError as e:
        bad.append('.prm: %s' % e); counts = {}
    p = G.read(lv['.prm'], 'dd')
    kinds, args = G.walk(p, proots)
    for r in proots:
        i = r if isinstance(r, int) else r[0]
        if i and i not in kinds:
            bad.append('.prm: root %d is not reachable' % i)
    # .MAT / .TEX
    mat, tex = T.read_mat(lv['.MAT']), T.read_tex(lv['.TEX'])
    try:
        kl_mat.check(lv['.MAT'])
    except ValueError as e:
        bad.append('.MAT: %s' % e)
    try:
        ntex = kl_tex.simulate_dd_loader(lv['.TEX'])
    except ValueError as e:
        bad.append('.TEX: %s' % e); ntex = None
    used = set()
    for i, k in kinds.items():
        for off, typ, _t in G.fields(p, i, k, args.get(i, 0)):
            if typ == 'm':
                used.add(p.u16(i, off))
                if p.u16(i, off) not in mat.insts:
                    bad.append('.prm: object %d names material slot %d, which the .MAT lacks' % (i, p.u16(i, off)))
            elif typ == 't' and p.u32(i, off) and p.u32(i, off) not in tex.tex:
                bad.append('.prm: sprite %d names texture %d' % (i, p.u32(i, off)))
    if mat.refs != T.material_refs(lv['.prm'], mat.ninst):
        bad.append('.MAT: use counts differ from the .prm')
    lack = T.used_textures(mat) - set(tex.tex)
    if lack:
        bad.append('.MAT: textures %r are not in the .TEX' % sorted(lack)[:5])
    miss = kl_light.missing_shaders(mat, lv['.fxc'], roots and sorted({p.u16(i, 0x12) for i, k in G.walk(p, roots)[0].items() if k == 'mesh'}))
    for s, l in sorted(miss.items())[:8]:
        bad.append('material %d (%s) asks for a shader the .fxc lacks: %s' % (s, mat.insts[s].name, l[0][:2]))
    # .oct: every model root names its own record
    oc = O.Oct.parse(lv['.oct'])
    if oc.pack() != lv['.oct']:
        bad.append('.oct does not re-pack to itself')
    refs = collections.Counter(p.u32(i, 0x1c) for i, k in kinds.items() if k == 'root' and p.u32(i, 0x1c))
    recs = set(oc.record_refs())
    if any(r not in recs for r in refs):
        bad.append('.prm: a model root names an .oct record that is not there')
    if any(c > 1 for c in refs.values()):
        bad.append('.prm: two model roots share one .oct record')
    # skeletons against the .ANM
    anm = kl_anm.Anm(lv['.ANM'], 'dd')
    bad += check_bones(p, anm.bones, roots)
    import kl_impact                                  # the two bone-id tables of every skeleton agree (bullet marks)
    bad += kl_impact.bone_faults(p)
    # variants: a person must have something to draw under its own variant, a heister also under 1 and 2
    lab = J.labels('dd', 'ZFFPlayer')
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) in PEOPLE:
            model, var, aset = person(sc, k)
            if not model:
                continue
            have = {p.chunks[o][0x0f] for o in objects(p, model)}
            need = {var} | ({1, 2} if sc.cls(k) == 'ZFFPlayer' and 'RANK_NONE' not in repr(sc.p.key(units(sc.nodes[k]['props'][1:-1])[lab.index('ZFFPlayer[2]')][0])) else set())
            if not need <= have:
                bad.append('%s: model %d has variants %r, needs %r' % (sc.path[k], model, sorted(have), sorted(need)))
            if 'anmcol:animationdatabase#' + aset not in {c.name for c in anm.cols}:
                bad.append('%s: animation set %s is not in the .ANM' % (sc.path[k], aset))
    # nothing of the stock level changed
    if stock is not None:
        p0 = G.read(stock['.prm'], 'dd')
        if p.chunks[1:len(p0.chunks)] != p0.chunks[1:]:
            bad.append('.prm: a chunk of the base level changed')
        m0, t0 = T.read_mat(stock['.MAT']), T.read_tex(stock['.TEX'])
        if any(s not in mat.insts or mat.insts[s].f[1:7] != m0.insts[s].f[1:7] or T._frozen(mat.insts[s].root) != T._frozen(m0.insts[s].root) for s in m0.insts):
            bad.append('.MAT: an instance of the base level changed')
        if any(i not in tex.tex or tex.tex[i].entry != t0.tex[i].entry for i in t0.tex):
            bad.append('.TEX: a texture of the base level changed')
        same = [e for e in stock.ext if e not in ('.prm', '.MAT', '.TEX', '.fxc', '.oct', '.gms', '.prp', '.ANM')]
        if any(lv[e] != stock[e] for e in same):
            bad.append('a member that should be untouched differs: %r' % [e for e in same if lv[e] != stock[e]][:5])
        o0 = O.Oct.parse(stock['.oct'])
        if oc.record_refs()[:len(o0.records)] != o0.record_refs() or lv['.oct'][:16] != stock['.oct'][:16]:
            bad.append('.oct: the base level\'s records moved')
    log('  check: %d nodes, %d people, .prm %d chunks %s, %d materials (%d used), %s textures, %d skeletons, .oct %d records: %s' % (
        len(sc.nodes), people, len(p.chunks) - 1, {k: counts.get(k) for k in ('root', 'mesh', 'desc', 'skel')}, len(mat.insts),
        len(used), ntex and ntex[0], len(skeletons(p)), len(oc.records), 'problems: %d' % len(bad)))
    for b in bad[:20]:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ who would not be drawn
# re/invisible.md. A person is one entity whose record names a model root; the engine draws the
# objects of that root whose variant byte (+0x0f) equals ZLNKOBJ[0] and whose detail mask (+0x0e)
# has the bit of the current detail level (01 near, 02 middle, 7c far on every human of both games;
# the dog 01 / 02 / fc). Each object is drawn with its material's passes; a pass whose effect
# permutation is not in the level's .fxc stays empty (kl2 0x50c2ff, re/lighting.md 1). So a person
# can be missing for five reasons a level's files show, and undrawn() tests each:
#   no model / the .gms and .prp disagree; no object of the asked variant; a detail level with no
#   object; objects on a material without its compiled shader; vertex or index data that is an
#   emptied stub (kl_graft's PRM_LIMIT trim) - plus a skeleton the level's .ANM does not fit.
DETAIL_BITS = 7                                  # detail levels 0..6: what the masks 01 + 02 + 7c of a person cover
HALF = 0.5                                       # UNDRAWN when at least this share of a level's vertices has no shader


def _files_scene(files):
    """(kl_prpjoin.Scene, unpacked .gms) of anything that answers ['.gms'] ['.buf'] ['.prp'] (an Lv, or the
    members kl_graft.verify() is given)."""
    raw = kl_gms.unpack(files['.gms'])
    names, tids, buf = ['ROOT'], [kl_rtp.ROOT_TYPE], files['.buf']
    for decl, tid, _prio in kl_gms.entities(raw):
        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
        names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
    return J.Scene(Prp(files['.prp']), names, tids, 'dd', 'level'), raw


def _levels(bits):
    """'0-1, 4' for a set of detail levels."""
    out, bits = [], sorted(bits)
    while bits:
        a = b = bits.pop(0)
        while bits and bits[0] == b + 1:
            b = bits.pop(0)
        out.append('%d' % a if a == b else '%d-%d' % (a, b))
    return ', '.join(out)


def people(files, rooms=True):
    """Every ZFFPlayer / ZFFActor of a level (files: an Lv or {'.gms': bytes ...}) -> [dict]:
    path, cls, model (.prp ZGEOM[4]), gms_model, variant, anim, pos (world), bones, chunks, variants
    {variant: [(detail mask, material slot, material name, vertices)]}, rooms ([names of the .rmi boxes the
    position is in]; None when rooms=False), faults [(severity, text)] with severity
      UNDRAWN  nothing (or less than half) of the body is drawn at some detail level, or at all
      PART     a smaller part is missing at some detail level (glasses, a visor)
      BONES    the skeleton does not fit the level's .ANM / its id tables disagree: drawn, but wrong or a crash
      NOTE     stands in no room box (3 of 43 actors of stock F07 do, and are drawn: not a fault by itself)"""
    import kl_light, kl_scene, kl_impact
    sc, raw = _files_scene(files)
    prm = G.read(files['.prm'], 'dd')
    mat = T.read_mat(files['.MAT'])
    miss = kl_light.missing_shaders(mat, files['.fxc'])
    gms = gms_models(raw)
    scene = kl_scene.Scene(raw, files['.buf'])
    ents = list(scene.entities())
    import kl_maps
    pos = kl_maps.world(scene)
    boxes = []
    if rooms:
        by_slot = {v + 2: e for e, v in scene.slots().items()}
        for b in O.RoomIndex.parse(files['.rmi']).boxes:
            boxes.append((struct.unpack_from('<I', b.raw, 0)[0], struct.unpack_from('<9f', b.raw, 4), struct.unpack_from('<3f', b.raw, 0x28),
                          struct.unpack_from('<3f', b.raw, 0x40), by_slot[b.room].name.decode('latin1') if b.room in by_slot else '?'))
    anm = kl_anm.Anm(files['.ANM'], 'dd').bones
    seen, out = {}, []
    for k in range(1, len(sc.nodes)):
        cls = sc.cls(k)
        if cls not in PEOPLE:
            continue
        model, variant, anim = person(sc, k)
        e = ents[k - 1]
        r = dict(path=sc.path[k], cls=cls, model=model, gms_model=gms[k - 1][1], variant=variant, anim=anim, pos=pos[e],
                 bones=0, chunks=0, variants={}, rooms=None, faults=[])
        out.append(r)
        f = r['faults']
        if rooms:
            r['rooms'] = []
            for aa, m, c, h, name in boxes:
                d = [pos[e][i] - c[i] for i in range(3)]
                if not aa:                               # ASSUMPTION: the matrix rows are the box's axes (40 of 43 stock F07 actors fall in a box this way)
                    d = [sum(m[3 * j + i] * d[i] for i in range(3)) for j in range(3)]
                if all(abs(d[i]) <= h[i] for i in range(3)):
                    r['rooms'].append(name)
            if boxes and not r['rooms']:
                f.append(('NOTE', 'stands in no room box of the .rmi'))
        if model != r['gms_model']:
            f.append(('UNDRAWN', '.prp names model %d, the .gms record %d' % (model, r['gms_model'])))
        if not (0 < model < len(prm.chunks)) or len(prm.chunks[model]) != 64 or prm.u16(model, 2) != 7:
            f.append(('UNDRAWN', 'no model: chunk %d is not a model root' % model)); continue
        if model not in seen:
            kinds = G.walk(prm, [model])[0]
            # kl_graft's trim leaves bytes(16); a real two-triangle index chunk is 16 bytes too, but never all zero
            empty = {i for i, kd in kinds.items() if kd in ('vtx', 'idx') and prm.chunks[i] == bytes(len(prm.chunks[i]))}
            look = {}
            for o in objects(prm, model):
                c = prm.chunks[o]
                d = prm.u32(prm.u32(o, 0x28), 0)
                dead = [prm.u32(d, off) for off in (4, 0x18) if prm.u32(d, off) in empty and prm.u32(d, 0)]
                look.setdefault(c[0x0f], []).append((c[0x0e], prm.u16(o, 0x12), prm.u32(d, 0), dead))
            sk = skeleton(prm, model)
            bf = (check_bones(prm, anm, [model]) + kl_impact.bone_faults(prm, [sk])) if sk else ['no skeleton']
            seen[model] = (len(kinds), look, prm.u32(sk, 0) if sk else 0, bf)
        r['chunks'], look, r['bones'], bf = seen[model]
        name = lambda m_: mat.insts[m_].name if m_ in mat.insts else 'material %d (not in the .MAT)' % m_
        r['variants'] = {v: [(mk, m_, name(m_), n) for mk, m_, n, _d in objs] for v, objs in look.items()}
        f += [('BONES', x) for x in bf]
        if variant not in look:
            f.append(('UNDRAWN', 'asks for variant %d; the model has %s' % (variant, sorted(look)))); continue
        objs = look[variant]
        gone = sum(1 for _mk, _m, _n, dead in objs if dead)
        if gone:
            f.append(('UNDRAWN', '%d of %d objects have emptied vertex / index data (chunks %s ...)' % (
                gone, len(objs), [c for _mk, _m, _n, dead in objs for c in dead][:4])))
        groups = collections.OrderedDict()
        for bit in range(DETAIL_BITS):
            here = [(m_, n) for mk, m_, n, _d in objs if mk >> bit & 1]
            lost = collections.Counter()
            for m_, n in here:
                if m_ in miss or m_ not in mat.insts:
                    lost[m_] += n
            groups.setdefault((sum(n for _m, n in here), tuple(sorted(lost.items()))), []).append(bit)
        for (total, lost), bits in groups.items():
            if not total:
                f.append(('UNDRAWN', 'detail level %s: no object' % _levels(bits)))
            elif lost:
                n = sum(v for _m, v in lost)
                f.append(('UNDRAWN' if n >= HALF * total else 'PART', 'detail level %s: %d of %d vertices on %s without a compiled shader (lacks %s)' % (
                    _levels(bits), n, total, ', '.join(name(m_) for m_, _v in lost),
                    ', '.join(sorted({x[0] for m_, _v in lost for x in miss.get(m_, ())})) or 'the material')))
    return out


def undrawn(files, notes=False):
    """The people of a level who would not be drawn as they should -> ['<SEVERITY> <path>: <reason>'];
    [] on every stock Dog Days level (`python kl_chars.py invisible F07`). files: an Lv, or the members
    kl_graft.verify() gets ({'.gms': ..., '.prp': ..., '.buf', '.prm', '.MAT', '.fxc', '.rmi', '.ANM'}).
    For kl_graft.verify:    bad += ['people: ' + x for x in kl_chars.undrawn(out)[:8]]"""
    return ['%s %s: %s' % (sev, r['path'], text) for r in people(files) for sev, text in r['faults'] if notes or sev != 'NOTE']


def invisible(src, everybody=False, box=None, log=print):
    """Print the people of a built or stock level and their faults; -> undrawn(). box: (x0, x1, z0, z1)
    to list only who stands there."""
    if src.lower().endswith('.zip'):
        src = os.path.dirname(os.path.abspath(src))
    rows = people(Lv(src))
    inside = lambda r: box is None or (box[0] <= r['pos'][0] <= box[1] and box[2] <= r['pos'][2] <= box[3])
    rows = [r for r in rows if inside(r)]
    count = collections.Counter()
    for r in rows:
        worst = next((sv for sv in ('UNDRAWN', 'BONES', 'PART') if any(f[0] == sv for f in r['faults'])), 'ok')
        count[worst] += 1
        if everybody or worst != 'ok':
            log('%-8s %s' % (worst, r['path'][5:]))
            log('         %s model %d (%d chunks, %d bones) variant %d set %s at (%d %d %d) rooms %s' % (
                r['cls'], r['model'], r['chunks'], r['bones'], r['variant'], r['anim'], r['pos'][0], r['pos'][1], r['pos'][2],
                ', '.join(r['rooms'] or ()) or '-'))
            if everybody and r['variant'] in r['variants']:
                by = collections.OrderedDict()
                for mk, _m, nm, n in sorted(r['variants'][r['variant']]):
                    by.setdefault(mk, []).append('%s %d' % (nm.split('/')[-1], n))
                log('         ' + '; '.join('mask %02x: %s' % (mk, ', '.join(v)) for mk, v in by.items()))
            for sv, text in r['faults']:
                log('         %s: %s' % (sv, text))
    log('%d people%s: %s' % (len(rows), '' if box is None else ' in x %d..%d z %d..%d' % tuple(box),
                             ', '.join('%d %s' % (count[k], k) for k in ('ok', 'UNDRAWN', 'PART', 'BONES') if count[k]) or 'none'))
    return ['%s %s: %s' % (sv, r['path'], text) for r in rows for sv, text in r['faults'] if sv != 'NOTE']


# ------------------------------------------------------------------ surveys
def survey(maps=FA_MAPS, log=print):
    """Every character model of the maps. Returns {map: [dict]}."""
    out = {}
    for lvn in maps:
        sc = J.Scene.load(lvn, 'dm')
        with zipfile.ZipFile(J.level_zip(lvn, 'dm')) as z:
            nm = {n.rsplit('.', 1)[-1].lower(): n for n in z.namelist() if '_main.' in n.lower()}
            p, mat = G.read(z.read(nm['prm']), 'dm'), T.read_mat(z.read(nm['mat']))
            tex = T.read_tex(z.read(nm['tex']))
        seen = collections.OrderedDict()
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) in PEOPLE:
                m, var, aset = person(sc, k)
                seen.setdefault(m, []).append((sc.path[k][5:], sc.cls(k), var, aset))
        rows = []
        log('===== %s: %d character models' % (lvn, len(seen)))
        for m, users in seen.items():
            sk = skeleton(p, m)
            lk = look(p, m, mat)
            cl = G.closure(p, [m])
            slots = {p.u16(o, 0x12) for o in objects(p, m)}
            names = bone_names(p, sk)
            who = next((WHO[u[0].split('!')[-1].split('\\')[0]] for u in users if u[0].split('!')[-1].split('\\')[0] in WHO), '')
            row = dict(root=m, users=len(users), first=users[0][0], classes=sorted({u[1] for u in users}), who=who,
                       user_variants=sorted({u[2] for u in users}), sets=sorted({u[3] for u in users}), bones=len(names),
                       free_bone=FREE_NAME in names, objects=len(objects(p, m)), variants=sorted(lk), lods=sorted({l for v in lk.values() for l in v}),
                       materials=sorted({mat.insts[s].name for s in slots}), textures=len(T.texture_closure(tex, T.used_textures(mat, slots))),
                       chunks=len(cl), bytes=sum(len(p.chunks[i]) for i in cl))
            rows.append(row)
            log('%6d %-52s x%d %-9s %s' % (m, users[0][0][:52], len(users), '/'.join(row['classes']), who))
            log('       %d bones, %d objects, variants %s (used: %s), LOD masks %s, %d materials, %d textures, %d chunks, %.2f MB, set %s' % (
                row['bones'], row['objects'], _span(row['variants']), row['user_variants'], ['%02x' % l for l in row['lods']], len(slots),
                row['textures'], row['chunks'], row['bytes'] / 1e6, '/'.join(row['sets'])))
            log('       ' + ', '.join(s.split('/')[-1] for s in row['materials']))
        out[lvn] = rows
    return out


def looks(maps=FA_MAPS, log=print):
    """The variants of the eight Dead Men heroes, part by part (nearest detail level), and a digest of each model
    per map: the same digest in every map = no per-map difference. Returns {map: [digest per hero]}."""
    import hashlib
    out = {}
    for lvn in maps:
        sc = J.Scene.load(lvn, 'dm')
        with zipfile.ZipFile(J.level_zip(lvn, 'dm')) as z:
            nm = {n.rsplit('.', 1)[-1].lower(): n for n in z.namelist() if '_main.' in n.lower()}
            p, mat = G.read(z.read(nm['prm']), 'dm'), T.read_mat(z.read(nm['mat']))
        out[lvn] = []
        for n in range(1, 9):
            root = person(sc, find_node(sc, HERO % n))[0]
            per, h = collections.OrderedDict(), hashlib.md5()
            for o in objects(p, root):
                c = p.chunks[o]
                d = p.u32(p.u32(o, 0x28), 0)
                h.update(bytes([c[0x0e], c[0x0f]]) + mat.insts[p.u16(o, 0x12)].name.encode() + struct.pack('<I', p.u32(d, 0)) + (p.chunks[p.u32(d, 4)] or b''))    # the vertex data
                if c[0x0e] == 1:
                    per.setdefault(c[0x0f], []).append((mat.insts[p.u16(o, 0x12)].name.split('/')[-1], p.u32(d, 4), p.u32(d, 0)))
            out[lvn].append(h.hexdigest()[:12])
            if lvn != maps[0]:
                continue
            parts = {}
            for v in sorted(per):
                for x in per[v]:
                    parts.setdefault(x, chr(ord('a') + len(parts)))
            log('Hero_%02d (%s), root %d of %s: parts at the nearest detail level' % (n, DM_NAMES[n - 1], root, lvn))
            for x, k in parts.items():
                log('    %s = %-30s %5d vertices' % (k, x[0], x[2]))
            for v in sorted(per):
                log('    variant %2d = outfit %2d (%-34s): %s' % (v, v - 1, outfit_name(v - 1), ' '.join(sorted(parts[x] for x in per[v]))))
    for lvn in maps:
        log('%s: model digests %s%s' % (lvn, ' '.join(out[lvn]), '' if out[lvn] == out[maps[0]] else '   <- DIFFERS from ' + maps[0]))
    return out


def _span(v):
    return '%d..%d' % (v[0], v[-1]) if len(v) > 2 and v == list(range(v[0], v[-1] + 1)) else ','.join(map(str, v))


def stock_levels():
    for game, base in (('dd', find(DD_GUESSES, DD_EXE)), ('dm', find(DM_GUESSES, DM_EXE))):
        for d in sorted(os.listdir(os.path.join(base, 'Scenes', 'Locations'))):
            try:
                yield game, d, J.level_zip(d, game)
            except FileNotFoundError:
                pass


def bones_proof(log=print):
    """The numbering claim of the docstring on every stock level of both games. Returns the problem count."""
    total, bad, tabs = collections.Counter(), 0, {}
    for game, name, path in stock_levels():
        with zipfile.ZipFile(path) as z:
            nm = {n.rsplit('.', 1)[-1].lower(): n for n in z.namelist() if '_main.' in n.lower()}
            if 'anm' not in nm:
                continue
            p, an = G.read(z.read(nm['prm']), game), kl_anm.Anm(z.read(nm['anm']), game).bones
        tabs[game, name] = [s.lower() for s in an]
        probs = check_bones(p, an)
        n = len(skeletons(p))
        total['levels'] += 1; total['skeletons'] += n
        total['bones'] += sum(p.u32(sk, 0) for sk in skeletons(p))
        bad += len(probs)
        log('%s %-9s %3d names in the .ANM, %3d skeletons: %s' % (game, name, len(an), n, probs[0] if probs else 'all bound to this table'))
    agree = next(n for n in range(400) if len({t[n] if n < len(t) else None for t in tabs.values()}) > 1)
    log('%(levels)d levels, %(skeletons)d skeletons, %(bones)d bones' % total + '; problems: %d; all tables agree on the first %d names' % (bad, agree))
    return bad


def pose(log=print, dd='F01', dm='M01_FA_A'):
    """Rest poses of the Dead Men heroes against the Dog Days heroes: bone lengths (local rest position,
    skel [6]) and global rest positions (skel [2]) of the bones both have, by name."""
    import math
    def load(level, game):
        sc = J.Scene.load(level, game)
        with zipfile.ZipFile(J.level_zip(level, game)) as z:
            nm = {n.rsplit('.', 1)[-1].lower(): n for n in z.namelist() if '_main.' in n.lower()}
            p = G.read(z.read(nm['prm']), game)
        out = collections.OrderedDict()
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == 'ZFFPlayer' and sc.path[k].startswith('ROOT\\Heroes!Hero_0'):
                sk = skeleton(p, person(sc, k)[0])
                h = struct.unpack('<20I', p.chunks[sk])
                names = bone_names(p, sk)
                out[sc.path[k].split('!')[1].split('\\')[0]] = {
                    s: (struct.unpack_from('<3f', p.chunks[h[6]], 28 * b + 16), struct.unpack_from('<3f', p.chunks[h[2]], 48 * b + 36),
                        struct.unpack_from('<4f', p.chunks[h[6]], 28 * b)) for b, s in enumerate(names)}
        return out
    a, b = load(dd, 'dd'), load(dm, 'dm')
    main = ('PELVIS', 'SPINE', 'SPINE_1', 'SPINE_2', 'NECK', 'HEAD', 'LEFT_CLAVICLE', 'LEFT_UPPER_ARM', 'LEFT_FOREARM', 'LEFT_HAND',
            'RIGHT_UPPER_ARM', 'RIGHT_FOREARM', 'RIGHT_HAND', 'LEFT_THIGH', 'LEFT_CALF', 'LEFT_FOOT', 'LEFT_TOE', 'RIGHT_THIGH', 'RIGHT_CALF', 'RIGHT_FOOT')
    ln = lambda v: math.sqrt(sum(x * x for x in v))
    log('bone length = |local rest position| (units as in the files; a Dog Days hero\'s HEAD is at height %.1f)' % a['Hero_01']['HEAD'][1][1])
    log('%-16s %s | %s' % ('', ' '.join('DD%s' % h[-2:] for h in a), ' '.join('DM%s' % h[-2:] for h in b)))
    for s in main:
        log('%-16s %s | %s' % (s, ' '.join('%4.1f' % ln(v[s][0]) for v in a.values()), ' '.join('%4.1f' % ln(v[s][0]) for v in b.values())))
    for s in ('HEAD', 'LEFT_HAND', 'RIGHT_HAND', 'PELVIS', 'r hand attacher', 'camera_bone'):
        if all(s in v for v in list(a.values()) + list(b.values())):
            log('%-16s global rest height: DD %s | DM %s' % (s, ' '.join('%5.1f' % v[s][1][1] for v in a.values()), ' '.join('%5.1f' % v[s][1][1] for v in b.values())))
    # spread inside Dog Days against the distance Dead Men -> nearest Dog Days hero, per bone
    worst_dd = max((max(ln(x[s][0]) for x in a.values()) - min(ln(x[s][0]) for x in a.values()), s) for s in main)
    out = []
    for hb, vb in b.items():
        d = max((min(abs(ln(vb[s][0]) - ln(va[s][0])) for va in a.values()), s) for s in main)
        lo = [s for s in main if ln(vb[s][0]) < min(ln(va[s][0]) for va in a.values()) - 0.5 or ln(vb[s][0]) > max(ln(va[s][0]) for va in a.values()) + 0.5]
        rot = max((min(1 - abs(sum(x * y for x, y in zip(vb[s][2], va[s][2]))) for va in a.values()), s) for s in main)
        out.append((hb, d, lo, rot))
        log('%s: largest bone-length distance to the nearest Dog Days hero %.2f (%s); bones outside the Dog Days range by > 0.5: %s; '
            'largest rest-rotation distance 1-|q.q| %.4f (%s)' % (hb, d[0], d[1], lo or 'none', rot[0], rot[1]))
    log('spread inside Dog Days\' own eight heroes: up to %.2f (%s)' % worst_dd)
    common = set.intersection(*[set(v) for v in list(a.values()) + list(b.values())])
    log('bones every one of the 16 heroes has: %d; Dog Days only: %s' % (len(common), sorted(set.intersection(*[set(v) for v in a.values()]) - set.union(*[set(v) for v in b.values()]))))
    return out


# ------------------------------------------------------------------ the experiments
CIVILIAN = 'Gameplay!CiviliansFront!Civ_Platform1_Runnning\\JPN_CIV_05\\Ground'
BUILDS = {
    # re/characters.md section 9: a Dead Men figure (the henchman: 95 bones, ONE variant) on one civilian
    'civ': [Pick((CIVILIAN,), 'M01_FA_A', 'Heroes!Henchmen_01\\Ground', {})],
    # one AI heister: Dead Men's Lynch on Hero_02 and on the bot that shares Hero_02's model
    'bot': [Pick(('Heroes!Hero_02\\Ground', 'Gameplay!merc_bot_squad!Squad#02\\Glazer_Bodyguard_02\\Ground'),
                 'M01_FA_A', 'Heroes!Hero_02\\Ground', {})],
    # all eight heroes and the seven bots that share their models
    'heroes': [Pick(('Heroes!Hero_01\\Ground',), 'M01_FA_A', 'Heroes!Hero_01\\Ground', {})] +
              [Pick(('Heroes!Hero_%02d\\Ground' % n, 'Gameplay!merc_bot_squad!Squad#%02d\\Glazer_Bodyguard_%02d\\Ground' % (n, n)),
                    'M01_FA_A', 'Heroes!Hero_%02d\\Ground' % n, {}) for n in range(2, 9)],
}


def build_dir(name, free='add'):
    return os.path.join(workdir(), 'build', 'chars', name + ('' if free == 'add' else '_' + free))


def build(name, base='F01', slot='F01', free='add', log=print):
    """One of BUILDS on a stock level: put, check against the stock level, write. Returns (folder, problems)."""
    lv, stock = Lv(base), Lv(base)
    rep = put(lv, BUILDS[name], free=free, log=log)
    for r in rep['picks']:
        log('  %s <- %s: model %s -> %d, %d bones, %d objects, variants %s, free bone: %s, %d bones renumbered for the .ANM, %d bone ids changed' % (
            ' + '.join(t.split('\\')[-2] for t in r['targets']), r['source'], r['old_models'], r['new_model'], r['bones'], r['objects'],
            r['variants'], r['free_bone'], r['renumbered_bones'], r['bone_ids_changed']))
    log('  .prm %d -> %d chunks, %.1f -> %.1f MB; materials %d -> %d; textures %d -> %d; shaders fitted %s, missing %s; .ANM bones added %s' % (
        rep['chunks'] + tuple(x / 1e6 for x in rep['prm_bytes']) + rep['materials'] + rep['textures'] +
        (rep['shaders_fitted'] or 'none', rep['shaders_missing'] or 'none', rep['anm_added'] or 'none')))
    bad = check(lv, stock, [r['new_model'] for r in rep['picks']], log)
    folder = build_dir(name, free)
    path = lv.write(folder, slot)
    import json
    with open(os.path.join(folder, 'chars.json'), 'w') as f:
        json.dump(dict(base=base, slot=slot, free=free, problems=bad, **rep), f, indent=1, default=str)
    log('built %s (%.0f MB), problems: %d' % (path, os.path.getsize(path) / 1e6, len(bad)))
    log('install (live agent): python tools/kl_graft.py install %s --from "%s"' % (slot, folder))
    return folder, bad


def parse_pick(s):
    target, _, rest = s.partition('=')
    parts = rest.split(':')
    v = [int(x) for x in parts[2].split(',')] if len(parts) > 2 else []
    return Pick(tuple(target.split('+')), parts[0], parts[1], dict(zip((1, 2), v)))


if __name__ == '__main__':
    a = sys.argv[1:]
    free = next((x.split('=')[1] for x in a if x.startswith('--free=')), 'add')
    a = [x for x in a if not x.startswith('--')]
    if a[:1] == ['survey']:
        survey(a[1:] or FA_MAPS)
    elif a[:1] == ['looks']:
        looks(a[1:] or FA_MAPS)
    elif a[:1] == ['bones']:
        sys.exit(1 if bones_proof() else 0)
    elif a[:1] == ['pose']:
        pose()
    elif a[:1] == ['build'] and len(a) > 1:
        n = 0
        for name in (BUILDS if a[1] == 'all' else a[1:]):
            print('=== build %s' % name)
            n += len(build(name, free=free)[1])
        sys.exit(1 if n else 0)
    elif a[:1] == ['put'] and len(a) > 3:
        lv, stock = Lv(a[1]), Lv(a[1])
        rep = put(lv, [parse_pick(s) for s in a[3:]], free=free, reuse='--no-reuse' not in sys.argv)
        bad = check(lv, stock, [r['new_model'] for r in rep['picks']])
        print('built', lv.write(a[2]), 'problems: %d' % len(bad))
        sys.exit(1 if bad else 0)
    elif a[:1] == ['wardrobe'] and len(a) > 2:
        level = next((x.split('=')[1] for x in sys.argv[1:] if x.startswith('--level=')), 'M01_FA_A')
        lv, stock = Lv(a[1]), Lv(a[1])
        slot = next((x.split('=')[1] for x in sys.argv[1:] if x.startswith('--slot=')), lv.name)
        arm = next((x.split('=')[1] for x in sys.argv[1:] if x.startswith('--armour=')), '0,1,2,3')
        import kl_impact
        # what the base has wrong before anything is added (an old graft's map skeletons): told apart from the new
        before = set(kl_impact.bone_faults(G.read(stock['.prm'], 'dd'))) | {'people: ' + x for x in undrawn(stock)}
        rep = wardrobe(lv, level, free=free, armour=[int(x) for x in arm.split(',')], fix_bones='--fix-bones' in sys.argv,
                       reuse='--no-reuse' not in sys.argv)
        for c in rep['characters']:
            print('  %-16s slot %d  model %5d  %3d bones  %4d objects  %2d outfit(s)' % (c['name'], c['slot'] + 1, c['root'], c['bones'], c['objects'], c['outfits']))
        print('  .prm %d -> %d chunks, %.1f -> %.1f MB; %d heisters / bots re-pointed; bones folded for low detail %d, on an ancestor %d, largest rest distance %.3f' % (
            rep['chunks'] + tuple(x / 1e6 for x in rep['prm_bytes']) + (len(rep['retargeted']), rep['bones_folded_for_low_detail'], rep['bones_on_an_ancestor'], rep['largest_rest_distance'])))
        print('  cost in the .prm: the eight Dead Men models (armour levels %s of 0..3; all %d looks numbered) %.2f MB, the mask / outfit variants of all sixteen %.2f MB (%d mesh objects)' % (
            rep['armour'], DM_LOOKS, rep['cost']['dead_men_models'] / 1e6, rep['cost']['looks'] / 1e6, rep['cost']['objects']))
        if rep['base_bone_ids_repaired']:
            print('  --fix-bones: %d bone-id bytes of the base\'s own skeletons repaired' % rep['base_bone_ids_repaired'])
        print('  chunk table: %d entries (%d of the base\'s %d dead indices taken, %d still free; limit %d of the game\'s %d: re/prm_limit.md)' % (
            rep['chunks'][1] + 1, rep['free_indices'][0] - rep['free_indices'][1], rep['free_indices'][0], rep['free_indices'][1],
            kl_impact.CHUNK_SAFE, kl_impact.CHUNK_TABLE))
        bad = check_wardrobe(lv, rep) + kl_impact.chunk_limit(lv['.prm'])
        for b in bad[:20]:
            print('  PROBLEM: ' + b)
        quiet = lambda *x: None
        rest = check(lv, None, rep['roots'], log=lambda t: print(t) if 'PROBLEM' not in t else None, extra=rep['roots'])
        rest += ['people: ' + x for x in undrawn(lv)]     # everybody an entity names (the heisters on their new roots too)
        old = [b for b in rest if b in before]
        new = [b for b in rest if b not in before]
        for b in new[:20]:
            print('  PROBLEM: ' + b)
        if old:
            print('  the BASE had %d of these faults before the wardrobe (not counted; --fix-bones repairs bone ids), e.g. %s' % (len(old), old[0][:150]))
        bad += new
        if os.path.isdir(a[1]) and os.path.abspath(a[1]) == os.path.abspath(a[2]):
            raise SystemExit('the out folder is the build folder: give another one (the build is not written over)')
        path = lv.write(a[2], slot)
        wardrobe_ini(rep, os.path.join(a[2], 'KLWardrobe.ini'))
        import json
        with open(os.path.join(a[2], 'chars.json'), 'w') as fh:
            json.dump(dict(base=a[1], slot=slot, free=free, problems=bad, base_problems=old, **rep), fh, indent=1, default=str)
        print('built %s (%.0f MB) + KLWardrobe.ini, problems: %d' % (path, os.path.getsize(path) / 1e6, len(bad)))
        sys.exit(1 if bad else 0)
    elif a[:1] == ['compact'] and len(a) > 2:
        import kl_impact, re
        lv = Lv(a[1])
        rep = compact_level(lv)
        bad = check(lv, None, None, extra=sorted(rep['roots'].values())) + ['people: ' + x for x in undrawn(lv)] + kl_impact.chunk_limit(lv['.prm'])
        path = lv.write(a[2], lv.name)
        ini = os.path.join(a[2], 'KLWardrobe.ini')
        if os.path.isfile(ini):                           # the roots klhook\klchar.c reads
            text = re.sub(r'(?m)^Root=(\d+)', lambda m: 'Root=%d' % rep['roots'][int(m.group(1))], open(ini, newline='').read())
            open(ini, 'w', newline='').write(text)
        for f in ('chars.json',):                         # notes of the build this was made from: its chunk numbers are the old ones
            if os.path.isfile(os.path.join(a[2], f)):
                os.remove(os.path.join(a[2], f))
        print('built %s, problems: %d (the base\'s own included)' % (path, len(bad)))
        sys.exit(1 if bad else 0)
    elif a[:1] == ['check'] and len(a) > 1:
        lv = Lv(a[1])
        sys.exit(1 if check(lv, extra=wardrobe_roots(lv)) else 0)
    elif a[:1] == ['invisible'] and len(a) > 1:
        at = next((sys.argv[i + 1] for i, x in enumerate(sys.argv) if x == '--at'), None)
        bad = invisible(a[1], '--all' in sys.argv, [float(v) for v in at.split(',')] if at else None)
        sys.exit(1 if bad else 0)
    else:
        print(__doc__); sys.exit(1)
