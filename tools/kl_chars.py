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
    install (a later LIVE agent, not this tool): python kl_graft.py install F01 --from <folder>

WHAT A BUILD CHANGES (put(); everything else of the base level is byte for byte the base's)
  .prm   the base's file + the model sub-graph of each chosen Dead Men character (kl_prmgraph.append of
         a converted extract): a NEW root per pick (its own object table), meshes, descriptors (48 bytes),
         vertex / index data, skeleton. Nothing of the base moves.
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
    p.chunks.append(bytes(data)); p.refs.append(1)
    return len(p.chunks) - 1


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
        else:
            import kl_graft
            path, self.name = J.level_zip(src, 'dd'), src
            self.beside = kl_graft.beside_of(src)
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
Pick = collections.namedtuple('Pick', 'targets level source variants')
Pick.__doc__ = """targets: scene paths (no ROOT) of the Dog Days people that take the model (they must
share one model today or the pick says which to take the free bone from: the first); level, source: the
Dead Men map and the character's scene path or root chunk; variants: {} or {Dog Days variant: Dead Men variant}."""


def put(base, picks, free='add', union=True, log=print):
    """base: Lv (edited in place). Returns a report dict; see the module docstring for what changes."""
    sc, raw = base.scene()
    raw = bytearray(raw)
    models = gms_models(raw)
    prm_s = G.read(base['.prm'], 'dd')
    anm = kl_anm.Anm(base['.ANM'], 'dd')
    oct_s = O.Oct.parse(base['.oct'])
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
            vmap = {v: (v if v in have else have[0]) for v in {1, 2} | {v for _m, v, _s in ppl}}
            vmap.update(pk.variants or {})
            root, nobj = with_variants(ex, r0, vmap)
            sk = skeleton(ex, root)
            if not sk:
                raise ValueError('%s %s: the model has no skeleton' % (level, pk.source))
            # the free bone, with the rest values of the Dog Days model the first target has today
            fb, free_here = None, free
            if FREE_NAME not in bone_names(ex, sk):
                donor = free_bone(prm_s, skeleton(prm_s, ppl[0][0])) if skeleton(prm_s, ppl[0][0]) else None
                if free == 'add' and donor:
                    fb = 'added as bone %d' % add_free_bone(ex, sk, donor)
                elif free == 'add':                     # no Dog Days model to take the rest values from
                    free_here = 'alias'
            renamed = reid(ex, sk, ids)
            if fb is None and free_here == 'alias' and FREE_NAME not in bone_names(ex, sk):
                fb = 'bone id 33 -> GROUND' if alias_free_bone(ex, sk) else None
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
        first = len(prm_s.chunks)
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
               prm_bytes=(len(base['.prm']), len(prm_bytes)), new_material_slots=sorted(new_slots),
               shaders_fitted={mat.insts[s].name: v[1] for s, v in fit['fixed'].items()},
               shaders_missing=[v[0] for v in fit['unresolved'].values()])
    base['.prm'], base['.MAT'], base['.TEX'], base['.fxc'] = prm_bytes, T.write_mat(mat), T.write_tex(tex), fxc
    base['.oct'], base['.gms'], base['.prp'] = oct_s.pack(), kl_gms.pack(bytes(raw)), sc.p.serialize()
    if rep['anm_added']:
        base['.ANM'] = anm.save()
    return rep


# ------------------------------------------------------------------ checks
def check(lv, stock=None, roots=None, log=print):
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
    proots = D.prm_roots(lv['.gms'], lv['.prp'], 'dd')
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
        rep = put(lv, [parse_pick(s) for s in a[3:]], free=free)
        bad = check(lv, stock, [r['new_model'] for r in rep['picks']])
        print('built', lv.write(a[2]), 'problems: %d' % len(bad))
        sys.exit(1 if bad else 0)
    elif a[:1] == ['check'] and len(a) > 1:
        sys.exit(1 if check(Lv(a[1])) else 0)
    else:
        print(__doc__); sys.exit(1)
