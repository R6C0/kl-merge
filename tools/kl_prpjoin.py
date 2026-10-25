#!/usr/bin/env python3
"""
The property side of a graft: one .prp from the ROOT of one level and chosen top-level subtrees
of several levels, and the check of what such a cut severs.

    python kl_prpjoin.py graft F04 F02 [out.prp]    systems of F04 + map of F02, checked
    python kl_prpjoin.py check F01                  a stock level through the same checks

Everything below was measured on the stock files (Dog Days F01..F09, F01 from KL_PortBackup; Dead
Men M01/M02/M03/M06_FA_A) on 2026-10-09 unless marked ASSUMPTION / not established.

File facts
- Keys are stored in order of first use in the token stream, each once, all used; the header key
  count is one LESS than the number of keys (103 of 103 stock .prp; each has exactly one empty
  key). join() of a level with all its own subtrees is byte-identical to the stock file: 17 of
  17 (the 13 above, L01, L10, M09_A, M09_B).
- Names and classes are not in the .prp: node k is .gms entity k-1, its name is at .buf offset
  [record +0]. Scene paths ('ROOT\\a\\b') resolve case-insensitively by walking those names:
  every ROOT\\ string of the 13 levels resolves in its own level.
- ZGEOM[4] (every node) equals the node's .gms record +0x0c, the model's chunk index in the .prm:
  all 157,897 + 60,937 entities of the 13 levels. Renumbering models must rewrite both.
- Scene property block: 34 or 33 named entries in Dog Days (PostFilterBoxes absent in F03, F06..F09),
  32 in Dead Men. Per level: CameraFar, CameraFogBegin/Full/Min, CameraBackgroundColor, SSAO_Blur,
  SSAO_Strength, PostFilterPalettes, PostFilterBoxes (the last two are ids, Boxes = Palettes + 1;
  of what, not established). MainCamera / DefaultPostFilterCamera(2) name cameras under
  mainsceneincludes_multiplayer.zip (Player0 or Player1; empty in some levels); the rest is equal.
- ROOT: no controllers, no references, identical properties in all 9 Dog Days levels. Dead Men's
  ROOT has one field less (ZGEOM) and in M02 names 'ROOT\\Environment#01' (ZROOM[11]). Take ROOT
  from the Dog Days systems level.

Systems or map (same scene path + class in every level = level-independent)
- Dog Days systems: AllLevels/mainsceneincludes_multiplayer.zip (3417 nodes F01..F03, 4016
  F04..F09; all 3417 paths in all 9, 1893 nodes byte-equal), the 115 CloneGroup_Effects groups
  whose template is inside it (5087 nodes, all in all 9, 3941 byte-equal), TrackLinkObjects,
  ZParticleController, AllLevels/OnlineWeaponPacks.zip (F09 only). No other family has a single
  path common to all levels: Locations/*, Animation/*, Gameplay!, FASpecials!, Specials!,
  AI_Players!, Escape!, SpawnPoint!, Scripting!, PointOfIntrest!, Settings!, levelbounds!,
  jump_point*, *Backdrop*, Effects/Helicopter_Damage_01.zip, CloneGroup_Locations/ROOT are map.
- Heroes!: Hero_01..08 exist in all 9 (16 of 32 nodes), the police/henchmen names vary. The group
  differs per level only in rotation and position (ZGEOM[1], ZGEOM[2]), the ZFFPlayer below only
  in ids. Classed systems here; a graft must still give them the map's positions.
- A clone group 'CloneGroup_<x>' holds the copies of the ZAllocMany whose path ends in <x>, so
  it belongs to the side of that template: 9 CloneGroup_Effects groups of F02/F03/F06/F08 are map
  (template under Effects/Helicopter_Damage_01.zip).
- What differs inside systems subtrees between levels is ids into that level's other files, not
  content: ZGEOM[4] (.prm chunk); multiples of 16 below the .buf size, so .buf offsets
  (ASSUMPTION): ZItemTemplate[4], ZItemTemplateWeapon[0], ZLNKOBJ[1], ZLNKWHANDS[5],
  ZParticleEmitter[10], ZGetAudioDefinition[0], CExplode[12], ZProjectileBase[0],
  ZHavokProjectileBallistic[2], ZDocuCamProfile[6], ZROOM[9]; other ids, kind not established:
  ZWINPIC[2], ZTTFONT[0], ZPostFilterSetEvent[4], ZPostFilterEvent[0], ZOnScreenDisplay2[7]
  (200 ints), ZBulletMarks[6], ZBloodSplatters[3], ZBloodStains[3]. The systems subtrees are
  therefore only valid together with their own level's .buf / .prm numbering. Map classes will
  hold more such fields; they were not searched.
- Effects/ParticleTemplates.zip (599 nodes, same paths in all 9) is inside the MAP in F01..F03
  (Locations/Fxx/..LOC_Inside or _Outside.zip) and inside mainsceneincludes_multiplayer.zip in
  F04..F09: that is the whole 3417 / 4016 difference. USE F04..F09 AS SYSTEMS DONOR.
- Dead Men systems: gamemenu.zip, AllLevels/mainsceneincludes.zip (915 / 2492 / 1344 / 1344
  nodes), AllLevels/OnlineWeaponPacks.zip, CoverList, TrackLinkObjects, ZParticleController,
  Heroes!, and the clone groups with a template in those. In M01 Effects/BulletImpacts.zip and
  Bullet_Holes_01.zip sit in the map (67 CloneGroup_Effects groups are map there).

References across the cut (all 9 Dog Days levels)
- systems -> map by path: none in F04..F09. In F01..F03 44 per level, all ZFFItemTemplateAmmo
  ZItemTemplateAmmo[10] -> cartridge ZParticleTemplate in the map's ParticleTemplates.zip.
- systems -> map by name: ZParticleEmitter[34] names a ZParticleTemplate by bare name; 3374
  emitters of F01..F03's systems find theirs only in the map (2997 inside systems in F04..F09).
- map -> systems by path: ZFFActor[1] (an actor's weapon -> ..\\AllLevels/equipment.zip\\Weapon\\x),
  28..51 per level; ZHeliWeapon[3], 0..2. By name: ZParticleEmitter[34], 353..2223 map emitters
  in F04..F09 (none in F01..F03, where the templates are map).
- scene property block -> systems: the 2..4 camera paths.
- Nothing in systems names a spawn point, camera, escape vehicle, loot object, room or sound
  object of the map, by path or by name. How the game rules find them is not established
  (ASSUMPTION: by class when the objects register).
- Stock levels already carry 0..18 emitter names without a template (Bullet_Impact_Debris_Default).

Dead Men maps: what points into the Dead Men systems that a graft drops
- ZParticleEmitter[32] -> ZParticleTemplate by name: 2673 / 3351 / 3370 / 2601 uses, 188 names;
  187 exist as ZParticleTemplate in Dog Days F04's systems, missing: Impacts_Default_Smoke (11).
- ZFFActor[1] -> weapon template path, 13 / 12 / 15 / 14: Smg_FN_P90_01 19, HG_HK_USP_01 17,
  Rifle_M4A1_01 13, Smg_MP5-A3_01 3, Rifle_SG552_01 1 have no Dog Days node at that path;
  Shotgun_Remington_870 1 has. M06 only: ZItem[0] -> RPG_7V 3 (exists), Mg_Minimi_SPW_01 1 (not);
  ZHeliWeapon[3] -> Mg_Minimi_SPW_01_Heli 1 (not); ZHavokShatter[1] / [3] -> ..\\Effects/
  BulletImpacts.zip\\Bullet\\Wood_02 20 / Wood_01 24 (both exist at the same path below
  mainsceneincludes_multiplayer.zip). Every such path needs its first component renamed.

Validation: systems of S + map of M for all 72 pairs of Dog Days FA levels parse back, round-trip
and have 0 misfits (Schema.misfit on every node and controller). S = F04..F09: 0 unresolved
paths with any M. S = F01..F03: the 44 cartridge paths, plus 3745..5610 template names when M is
F04..F09. F01 + F02 with those 44 paths re-pointed (join(rename=...)): 0 unresolved.
"""
import collections, glob, hashlib, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_prp import Prp, units
import kl_gms, kl_rtp
from kl_port_check import find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

DD_FA = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09']
DM_FA = ['M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A']
KEYED = (0x0c, 0x0e)             # tokens whose payload is one key index; 0x0f holds a list of them
_schemas = {}


def schema(game):
    if game not in _schemas:
        _schemas[game] = kl_rtp.Schema.load(game)
    return _schemas[game]


def level_zip(level, game=None):
    """Stock archive of a level ('F02', 'M01_FA_A'). A stock file moved to KL_PortBackup wins over
    what stands in its place (that is our own build). Dead Men names the archive without '_'."""
    game = game or ('dm' if level.startswith('M') else 'dd')
    base = find(*((DM_GUESSES, DM_EXE) if game == 'dm' else (DD_GUESSES, DD_EXE)))
    for root in (os.path.join(base, 'KL_PortBackup'), base):
        hit = glob.glob(os.path.join(root, 'Scenes', 'Locations', level, '*_Main.zip'))
        if hit:
            return hit[0]
    raise FileNotFoundError(level)


class Scene:
    """A property tree with the name and class of every node (the .prp holds neither).
    nodes[k] is .prp node k (0 = ROOT); parent[k], top[k] (its top-level ancestor, 0 for ROOT)."""

    def __init__(self, prp, names, tids, game, label=''):
        self.p, self.names, self.tids, self.game, self.label = prp, names, tids, game, label
        self.nodes, self.parent, self.top, self.path = [], [], [], []
        st = [(prp.root, -1)]
        while st:
            n, par = st.pop()
            k = len(self.nodes)
            self.nodes.append(n); self.parent.append(par)
            self.top.append(0 if par < 0 else k if par == 0 else self.top[par])
            self.path.append(names[k] if par < 0 else self.path[par] + '\\' + names[k])
            st.extend((c, k) for c in reversed(n['children']))
        if not len(self.nodes) == len(names) == len(tids):
            raise ValueError('%s: %d nodes, %d names, %d classes' % (label, len(self.nodes), len(names), len(tids)))
        self.index = collections.defaultdict(list)          # lower-case scene path -> node indices
        for k, pa in enumerate(self.path):
            self.index[pa.lower()].append(k)
        self.end = [0] * len(self.nodes)                    # subtree of k = nodes k .. end[k]-1
        for k in range(len(self.nodes) - 1, -1, -1):
            self.end[k] = max(self.end[k], k + 1)
            if self.parent[k] >= 0:
                self.end[self.parent[k]] = max(self.end[self.parent[k]], self.end[k])

    @classmethod
    def load(cls, level, game=None):
        game = game or ('dm' if level.startswith('M') else 'dd')
        return cls.from_zip(level_zip(level, game), game, level)

    @classmethod
    def from_zip(cls, path, game='dd', label=None):
        """The Scene of any level archive (a stock one or one of our builds)."""
        with zipfile.ZipFile(path) as zf:
            prp = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
            p = Prp(zf.read(prp))
            raw = kl_gms.unpack(zf.read(prp[:-4] + '.gms'))
            buf = zf.read(prp[:-4] + '.buf')
        names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
        for decl, tid, _prio in kl_gms.entities(raw):
            o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
            names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
        return cls(p, names, tids, game, label or path)

    def cls(self, k):
        return schema(self.game).geoms.get(self.tids[k])

    def tops(self):
        return [k for k in range(1, len(self.nodes)) if self.parent[k] == 0]

    def resolve(self, s):
        """Node indices a scene path names ('ROOT\\a\\b', case-insensitive), [] if none."""
        return self.index.get(s.lower(), [])


# ---------------------------------------------------------------- join

def _intern(tokens, keys, table, order, rename=None):
    out = []
    for op, pl in tokens:
        if op in KEYED or op == 0x0f:
            idx = struct.unpack_from('<%dI' % (len(pl) // 4), pl)
            new = []
            for i in (idx if op in KEYED else idx[1:]):
                s = keys[i]
                if rename and op != 0x0e:
                    s = rename(s)
                if s not in table:
                    table[s] = len(order); order.append(s)
                new.append(table[s])
            pl = struct.pack('<%dI' % len(idx), *(new if op in KEYED else (idx[0],) + tuple(new)))
        out.append((op, pl))
    return out


def join(base, picks, label='join', rename=None, take=None, skip=(), adopt=None):
    """One Scene from `base`'s header, scene property block and ROOT node, and the top-level
    subtrees `picks` = [(scene, top-level node index), ...] in that order under it. Every key is
    re-interned into one table in order of first use (the order the games' own files have), the
    key count and blob size follow, and the object count is recounted by Prp.serialize.
    `rename` (string -> string) is applied to every string and key-list entry (not to enum
    names) while interning: the way to re-point scene paths that cross the cut.
    `take` = {entry name: scene} replaces (or adds) entries of the scene property block by
    another level's, e.g. the map's fog and far plane.
    `skip` = node indices of `base` (with their subtrees) left out of the copy (kl_interact_graft: a static door leaf that a kick door replaces).
    `adopt` = {top-level node index of `base`: [(scene, top-level node index), ..]}: subtrees of other scenes added as the LAST children of that
    picked top (kl_bots_kick_1025: a kick step under a squad top, which stays the same node so every reference to it keeps working).
    Returns the Scene; scene.origin[k] = (source scene, source node index) of node k - the order
    the joined .gms must list its entities in."""
    table, order = {}, []
    new = Prp.__new__(Prp)
    new.head, new.flags, new.zero = base.p.head, base.p.flags, base.p.zero
    entries = [(name, toks, base) for name, toks in block(base)]
    for name, sc in (take or {}).items():
        theirs = [(n, toks, sc) for n, toks in block(sc) if n == name]
        if not theirs:
            raise ValueError('%s has no scene property %s' % (sc.label, name))
        at = [i for i, e in enumerate(entries) if e[0] == name]
        entries[at[0] if at else len(entries):at[0] + 1 if at else len(entries)] = theirs
    new.settings = [(0x04, struct.pack('<I', len(entries)))]
    for _name, toks, sc in entries:
        new.settings += _intern(toks, sc.p.keys, table, order, rename)
    names, tids, origin = ['ROOT'], [base.tids[0]], [(base, 0)]

    def copy(sc, k):
        n, keys = sc.nodes[k], sc.p.keys
        props = _intern(n['props'], keys, table, order, rename)
        ctrls = [(_intern([nm], keys, table, order)[0], _intern(body, keys, table, order, rename)) for nm, body in n['ctrls']]
        return {'props': props, 'ctrls': ctrls, 'children': []}

    new.root = copy(base, 0)
    for sc, t in picks:
        if sc.parent[t] != 0:
            raise ValueError('%s node %d (%s) is not a top-level subtree' % (sc.label, t, sc.names[t]))
        made, dead = {}, set()
        for k in range(t, sc.end[t]):                     # preorder: a parent comes before its children
            if sc is base and (k in skip or sc.parent[k] in dead):
                dead.add(k)
                continue
            made[k] = copy(sc, k)
            (new.root if k == t else made[sc.parent[k]])['children'].append(made[k])
            names.append(sc.names[k]); tids.append(sc.tids[k]); origin.append((sc, k))
        for sc2, t2 in ((adopt or {}).get(t, ()) if sc is base else ()):
            if sc2.parent[t2] != 0:
                raise ValueError('%s node %d (%s) is not a top-level subtree' % (sc2.label, t2, sc2.names[t2]))
            made2 = {}
            for k in range(t2, sc2.end[t2]):
                made2[k] = copy(sc2, k)
                (made[t] if k == t2 else made2[sc2.parent[k]])['children'].append(made2[k])
                names.append(sc2.names[k]); tids.append(sc2.tids[k]); origin.append((sc2, k))
    new.tail = [(0x7f, b'')]
    if '' not in table:
        raise ValueError('no empty key: the header count of such a file is not established')
    new.keys, new.nkeys = order, len(order) - 1           # the header counts one less than there are
    new.keyblob = b''.join(s.encode('latin1') + b'\0' for s in order)
    out = Scene(new, names, tids, base.game, label)
    out.origin = origin
    return out


# ---------------------------------------------------------------- survey

def text(sc, tokens):
    """Tokens as bytes with every key index replaced by its string: comparable between files."""
    out, keys = [], sc.p.keys
    for op, pl in tokens:
        if op in KEYED:
            pl = keys[struct.unpack('<I', pl)[0]].encode('latin1') + b'\0'
        elif op == 0x0f:
            pl = b''.join(keys[i].encode('latin1') + b'\0' for i in struct.unpack_from('<%dI' % (len(pl) // 4 - 1), pl, 4))
        out.append(bytes([op]) + pl)
    return b''.join(out)


def fingerprints(sc):
    """Per node, a hash of its whole subtree: names, classes, properties, controllers."""
    fp = [None] * len(sc.nodes)
    kids = collections.defaultdict(list)
    for k in range(len(sc.nodes) - 1, -1, -1):
        n = sc.nodes[k]
        h = hashlib.md5(('%s\0%x\0' % (sc.names[k], sc.tids[k])).encode('latin1'))
        h.update(text(sc, n['props']))
        for nm, body in n['ctrls']:
            h.update(text(sc, [nm] + body))
        for c in reversed(kids.pop(k, [])):
            h.update(fp[c])
        fp[k] = h.digest()
        kids[sc.parent[k]].append(k)
    return fp


_labels = {}

def labels(game, cls):
    """'Owner[i]' for each level-file field of a class: the class level declaring it (schema
    owner) and the field's index among that level's stored fields."""
    if (game, cls) not in _labels:
        out, seen = [], collections.Counter()
        for f in schema(game).fields(cls) or []:
            out.append('%s[%d]' % (f.owner, seen[f.owner])); seen[f.owner] += 1
        _labels[game, cls] = out
    return _labels[game, cls]


def fields(sc, k):
    """Every stored field of node k and of its controllers: (holder, field label, unit tokens).
    holder is the node's class, or 'Class + controller Name (implementing class)'."""
    cls, n, sch = sc.cls(k), sc.nodes[k], schema(sc.game)
    objs = [(cls, cls, n['props'])]
    for nm, body in n['ctrls']:
        name = sc.p.key(nm)
        impl = sch.controller(name, cls)
        objs.append(('%s + %s (%s)' % (cls, name, impl or 'unregistered'), impl, body))
    for holder, c, obj in objs:
        lab = labels(sc.game, c) if c else []
        for i, u in enumerate(units(obj[1:-1])):
            yield holder, lab[i] if i < len(lab) else '?[%d]' % i, u


def strings(sc, unit):
    """The strings a field holds (0x0c tokens and 0x0f lists; enum names are not references)."""
    out, keys = [], sc.p.keys
    for op, pl in unit:
        if op == 0x0c:
            out.append(keys[struct.unpack('<I', pl)[0]])
        elif op == 0x0f:
            out += [keys[i] for i in struct.unpack_from('<%dI' % (len(pl) // 4 - 1), pl, 4)]
    return out


# Top-level subtrees that are game systems (see the module docstring for the measurements).
SYSTEMS = {'dd': ('AllLevels/mainsceneincludes_multiplayer.zip', 'AllLevels/OnlineWeaponPacks.zip',
                  'TrackLinkObjects', 'ZParticleController'),
           'dm': ('AllLevels/mainsceneincludes.zip', 'AllLevels/OnlineWeaponPacks.zip', 'gamemenu.zip',
                  'TrackLinkObjects', 'ZParticleController', 'CoverList')}


def family(name):
    """Group of a top-level name: 'Gameplay!', 'Locations/*', 'CloneGroup_Effects', the name itself."""
    if name.startswith('CloneGroup_'):
        return name.split('/')[0].split('.zip')[0]
    if '!' in name:
        return name.split('!')[0] + '!'
    a = name.split('/')
    if len(a) > 1 and len(a[1]) >= 3 and a[1][0] in 'FLM' and a[1][1:3].isdigit():
        return a[0] + '/*'
    return name


def templates(sc):
    """{clone-group top: its template node}. 'CloneGroup_<x>' holds the run-time copies of the
    ZAllocMany whose scene path, written with '/', ends in <x> ('ROOT/' dropped)."""
    want = {}
    for t in sc.tops():
        if sc.names[t].startswith('CloneGroup_'):
            x = sc.names[t][11:].lower()
            want.setdefault(x[5:] if x.startswith('root/') else x, []).append(t)
    out = {}
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZAllocMany':
            parts = sc.path[k].lower().replace('\\', '/').split('/')
            for i in range(1, len(parts)):
                for t in want.get('/'.join(parts[i:]), ()):
                    out.setdefault(t, k)
    return out


def tpl_key(path):
    # '!' and '/' both separate path parts: a template is named 'Effects!010_X!Artillery!Group', its clone group 'CloneGroup_ROOT/Effects/010_X/Artillery/Group'
    return path.lower().replace('\\', '/').replace('!', '/')


def orphan_clone_groups(sc, dropped=()):
    """Top-level 'CloneGroup_*' nodes holding ZAllocMany copies for which the scene has no template: a ZAllocMany outside every clone group (and
    outside the node indices `dropped`, which will not exist) whose path, '!' read as '/', ends in the group's path. templates() only reads '/'.
    A copy without its template keeps ZAllocMany +0x58 = 0 and the first ZParticleEmitter crashes at kl2 0x4c63f2. -> [top node indices]"""
    tops = [t for t in sc.tops() if sc.names[t].startswith('CloneGroup_')]
    inside = set(dropped)
    for t in tops:
        inside.update(range(t, sc.end[t]))
    have = [tpl_key(sc.path[k]) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZAllocMany' and k not in inside]
    out = []
    for t in tops:
        if not any(sc.cls(k) == 'ZAllocMany' for k in range(t, sc.end[t])):
            continue
        x = sc.names[t][11:].lower()
        x = x[5:] if x.startswith('root/') else x
        if not any(h == x or h.endswith('/' + x) for h in have):
            out.append(t)
    return out


def sides(sc):
    """'systems' or 'map' for every node (ROOT: 'root'), decided by its top-level subtree: the
    names in SYSTEMS and Heroes!* are systems; a clone group goes where its template is (map if
    it has none); everything else is map."""
    tpl, top = templates(sc), {}
    for t in sc.tops():
        if not sc.names[t].startswith('CloneGroup_'):
            top[t] = 'systems' if sc.names[t] in SYSTEMS[sc.game] or sc.names[t].startswith('Heroes!') else 'map'
    for t in sc.tops():
        if t not in top:
            top[t] = top[sc.top[tpl[t]]] if t in tpl else 'map'
    return ['root'] + [top[sc.top[k]] for k in range(1, len(sc.nodes))]


def references(sc):
    """Every string of every field (and of the scene property block, holder node -1) that names
    a node by scene path: (holder node, holder, field, string, [target nodes])."""
    s = sc.p.settings
    for i, (op, pl) in enumerate(s):
        if op == 0x0c and sc.resolve(sc.p.key((op, pl))) and i and s[i - 1][0] == 0x09:
            yield -1, 'scene property block', sc.p.key(s[i - 2]) if s[i - 2][0] == 0x0c else '?', sc.p.key((op, pl)), sc.resolve(sc.p.key((op, pl)))
    for k in range(len(sc.nodes)):
        for holder, field, unit in fields(sc, k):
            for st in strings(sc, unit):
                hit = sc.index.get(st.lower()) if st[:4].upper() == 'ROOT' else None
                if hit or st[:5].upper() == 'ROOT\\':
                    yield k, holder, field, st, hit or []


# Fields that name a node by its bare name (no path). Found by matching every non-path string
# against the node names of the 9 + 4 Fragile Alliance levels: this is the only field whose
# namesakes sit on the other side of the cut. How the engine looks the name up is not established.
NAME_FIELDS = {'dd': {('ZParticleEmitter', 'ZParticleEmitter[34]'): 'ZParticleTemplate'},
               'dm': {('ZParticleEmitter', 'ZParticleEmitter[32]'): 'ZParticleTemplate'}}


def dangling(sc):
    """What no longer resolves: ([(node, holder, field, path)], [(node, holder, field, name)]) -
    scene paths without a node, and NAME_FIELDS names without a node of the expected class."""
    paths = [(k, h, f, s) for k, h, f, s, hit in references(sc) if not hit]
    have = collections.defaultdict(set)
    for k in range(1, len(sc.nodes)):
        have[sc.cls(k)].add(sc.names[k].lower())
    names = []
    for k in range(1, len(sc.nodes)):
        if any(c == sc.cls(k) for c, _f in NAME_FIELDS[sc.game]):
            for holder, field, unit in fields(sc, k):
                want = NAME_FIELDS[sc.game].get((holder, field))
                names += [(k, holder, field, s) for s in strings(sc, unit) if want and s and s.lower() not in have[want]]
    return paths, names


def misfits(sc):
    """Every node and controller that does not fit its class (Schema.misfit): [(node, what, why)]."""
    sch, out = schema(sc.game), []
    for k, n in enumerate(sc.nodes):
        cls = sc.cls(k)
        why = sch.misfit(cls, n['props']) if cls else 'unregistered type %#x' % sc.tids[k]
        if why:
            out.append((k, cls, why))
        for nm, body in n['ctrls']:
            impl = sch.controller(sc.p.key(nm), cls)
            why = sch.misfit(impl, body) if impl else None
            if why:
                out.append((k, 'controller %s (%s)' % (sc.p.key(nm), impl), why))
    return out


def block(sc):
    """The scene property block before ROOT: [(name, tokens of the whole entry)], in file order.
    An entry is 0c name, 09 type, then a string (types 16, 12) or 09 count + array (types 2, 3)."""
    s = sc.p.settings
    out, i = [], 1
    for _ in range(struct.unpack('<I', s[0][1])[0]):
        j = i + 3
        if s[i + 2][0] == 0x09 and s[i + 3][0] == 0x01:
            while s[j][0] != 0x7c:
                j += 1
            j += 1
        out.append((sc.p.key(s[i]), s[i:j])); i = j
    if i != len(s):
        raise ValueError('scene property block: %d tokens left over' % (len(s) - i))
    return out


def graft_picks(S, M):
    """The picks of a graft: M's top-level order, its map subtrees kept and each systems subtree
    replaced by S's of the same name; S's remaining systems subtrees go in before the first of
    the closing systems objects. Also returns what was left out: (picks, dropped names of M)."""
    ss, sm = sides(S), sides(M)
    mine = {}
    for t in S.tops():
        if ss[t] == 'systems':
            mine.setdefault(S.names[t], []).append(t)
    picks, dropped = [], []
    for t in M.tops():
        if sm[t] == 'map':
            picks.append((M, t))
        elif mine.get(M.names[t]):
            picks.append((S, mine[M.names[t]].pop(0)))
        else:
            dropped.append(M.names[t])
    rest = sorted(t for ts in mine.values() for t in ts)
    at = next((i for i, (sc, t) in enumerate(picks) if sc is S and S.names[t] in ('TrackLinkObjects', 'ZParticleController')), len(picks))
    return picks[:at] + [(S, t) for t in rest] + picks[at:], dropped


def check(sc, log=print):
    """Serialize, parse back, fit every object to its class, resolve every reference."""
    data = sc.p.serialize()
    back = Prp(data)
    if back.serialize() != data or len(back.nodes()) != len(sc.nodes) or back.keys != sc.p.keys:
        raise ValueError('joined file does not round-trip')
    used = set()
    for op, pl in back.tokens:
        if op in KEYED:
            used.add(struct.unpack('<I', pl)[0])
        elif op == 0x0f:
            used.update(struct.unpack_from('<%dI' % (len(pl) // 4 - 1), pl, 4))
    bad, (paths, names) = misfits(sc), dangling(sc)
    log('%s: %d nodes, %d keys (%d unused, %d duplicate), %d objects, %d bytes; parses back and round-trips'
        % (sc.label, len(sc.nodes), len(back.keys), len(back.keys) - len(used), len(back.keys) - len(set(back.keys)), back.count, len(data)))
    log('  objects that do not fit their class: %d' % len(bad))
    for k, what, why in bad[:20]:
        log('    %s: %s: %s' % (sc.path[k], what, why))
    for title, rows in (('scene paths', paths), ('bare names', names)):
        log('  %s that do not resolve: %d (%d distinct)' % (title, len(rows), len(set(r[3] for r in rows))))
        for (h, f, s), c in collections.Counter((h, f, s) for _k, h, f, s in rows).most_common(60):
            log('    %4d  %s %s -> %s' % (c, h, f, s))
    return data, bad, paths, names


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'graft':
        S, M = Scene.load(a[1]), Scene.load(a[2])
        picks, dropped = graft_picks(S, M)
        j = join(S, picks, '%s systems + %s map' % (a[1], a[2]))
        fam = collections.Counter()
        for k in j.tops():
            fam[(j.origin[k][0].label, family(j.names[k]))] += j.end[k] - k
        for (src, f), n in sorted(fam.items()):
            print('  from %-9s %-48s %6d nodes' % (src, f, n))
        print('  left out of %s: %s' % (a[2], collections.Counter(family(n) for n in dropped).most_common()))
        twice = [n for n, c in collections.Counter(j.names[k] for k in j.tops()).items() if c > 1]
        print('  top-level names used twice: %d %s' % (len(twice), twice[:8]))
        data = check(j)[0]
        if len(a) > 3:
            with open(a[3], 'wb') as f:
                f.write(data)
            print('  ->', a[3])
    elif len(a) == 2 and a[0] == 'check':
        s = Scene.load(a[1])
        check(join(s, [(s, t) for t in s.tops()], a[1] + ' (identity join)'))
    else:
        print('usage: kl_prpjoin.py graft <systems level> <map level> [out.prp]\n       kl_prpjoin.py check <level>')


if __name__ == '__main__':
    main()
