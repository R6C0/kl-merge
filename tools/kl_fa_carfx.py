#!/usr/bin/env python3
"""
The black box around a burning car (owner, 2026-10-11, playing Withdrawal: 'fix that black box on these cars
that are blown up'). A step on a FINISHED build folder: it reads, and `apply` writes a NEW folder.

    python kl_fa_carfx.py check [--cars] <build folder> [<build folder> ...]
                                                                        the table (--cars: every vehicle on a line
                                                                        of its own); exit 1 if a box would be drawn
    python kl_fa_carfx.py apply <build folder> <new folder>             the build with the box switched off
    python kl_fa_carfx.py apply --alpha-only <build folder> <new folder>   the same, the mesh's shape kept (alpha 0
                                                                        only): if a blast misbehaves with the fix
    python kl_fa_carfx.py apply --smoke-clear <build folder> <new folder>  TEST ONLY, NOT A FIX: the mesh kept and the
                                                                        fires' dark smoke made invisible - the
                                                                        twin for the live look (re/carfx.md 5)
    python kl_fa_carfx.py material <build folder>                       the material, node by node, and its shaders

READ THIS FIRST (after the review, re/carfx_review.md): THAT THE DARK BLOCK OF THE OWNER'S PICTURES IS THIS MESH IS A
GUESS, AND NOT THE BEST-FITTING ONE. The pictures are darker than the mesh's alpha allows (over 97 % at the top of
the frame against 0.75 at most, and 0 at the mesh's top), dark where the mesh is clear, and the car inside the box
is not darkened. The other candidate is the fires' own near-black smoke (templates Smoke_CarFire_01a / 02a /
02: colour key (26, 24, 22), texture FX_Par_Smoke_Dark_05), which this fix does NOT touch: `check` lists it, and
`apply --smoke-clear` makes the twin build that tells the two apart in the game. Everything below that says what
the mesh LOOKS like in Dog Days ('dark', 'black', 'a pane') is that guess; what the files hold is fact.

WHAT THE BOX IS (re/carfx.md; files of the five maps of the owner's tab, both games' stock levels, Dead Men's
shader source and the compiled shader of the level's own .fxc; NOTHING OF THIS WAS SEEN IN THE GAME)
  Dead Men's car fire - `CarFire_USA_Sedan_01_Cheap.zip\\Car_Fire_USA_Sedan_01_Cheap\\Group_CarFire_ALL`, which a
  vehicle's VehicleEffects controller names and starts when it blows up (Retomoto also `SWAT_Explosion_AM.zip` /
  `Bus_Explosion_AM.zip\\Explosion_and_Fire_01`) - holds, beside its emitters, ONE MESH: `HeatShimmer` (ZSTDOBJ).
  It is an open box round the vehicle: 3.3 m wide at the top, 6.3 m long, 3.7 m high for a car (bounds -164 0 -305
  .. 162 367 320; 3.4 x 6.9 x 8.2 m for the SWAT truck, 3.4 x 6.9 x 11.9 m for a bus), 28 vertices, vertex alpha 0
  at the bottom and top ring and 0.75 at the ring half way up. Material `Effects/Heat_Shimmer_01`, Standard/Glass:
      Dead Men   blend TRANS_ON_OPAQUE, render group 0x31, Refraction2D + Bump + Scroll + AlphaFade
                 (gm_vAlphaFadeDistScaleOffset 0 -0.002 1 2.167: by Common.fx CalculateAlphaFade, whole up to
                 5.8 m from the eye, gone at 10.8 m), diffuse texture grey with alpha 0 everywhere, no mask texture
      the build  the same, render group 0x41, and Scroll and AlphaFade OFF: kl_mat drops gm_vAlphaFade* (Dog
                 Days' Glass class never has them) and kl_light.fit_shaders then switches the two BOOLs off,
                 because no glass.fx entry of the cache has them.
  The shader is the same in both games (Dead Men's Glass.fx AmbientHQ_PS20 as source; Dog Days' glass.fx entry
  MESH_STANDARD + BLENDENABLED + BUMPENABLED + REFRACTION2DENABLED + STDSAMPLERSTATE, disassembled from the .fxc):
      refr   = tex(samplerRefraction2D, screen uv - normal.xy * gm_vRefraction2DScale)   (the copy of the frame)
      colour = lerp(refr * gm_vRefraction2DColor * tex(samplerRefraction2DMask, uv),
                    2 * light * tex(samplerDiffuse).rgb, tex(samplerDiffuse).a)          = the first: alpha is 0
      alpha  = the vertex's alpha (* CalculateAlphaFade in Dead Men)                     = up to 0.75
  So in Dead Men the box shows the frame behind it again, wobbling: nothing to see but the wobble. GUESS: in Dog
  Days the same arithmetic comes out dark (`refr * mask` black or near it), at up to 75 % in a band at roof
  height that fades to nothing at 3.7 m, and, without the fade, at any distance. No picture shows that band.
  Dog Days draws its own Glass materials (50 instances in the 21 stock levels, all with Refraction2D) in five
  forms only - STOCK_GLASS below - and 'TRANS_ON_OPAQUE in group 0x41' is none of them (for the class Glass:
  the same blend and group is Dog Days' commonest decal form, 1045 Standard/Standard instances); and no stock Dog Days
  level has a heat-shimmer mesh on a fire at all (its one 'Heat_Shimmer' material, L11's jet exhaust, is a
  Standard/Standard reflection with Dog Days' own SmoothSmear, not a refraction).
  NOT ESTABLISHED: whether it is dark at all, and if so which factor is black in Dog Days - the frame copy, not yet made when the 'on opaque' groups
  are drawn (stock refracts in groups 0, 0x46, 0x69, 0x6c, 0x6f only), or the mask stage without a texture (33
  stock materials have none either, but every stock material whose diffuse alpha is under 0.35 has one, bar
  F06's river). Neither can be tried offline, and neither would give the fade back: no glass.fx entry has
  ALPHAFADEENABLED, so a 'right' material could at best be a wobbling pane round every burning car at any distance.

THE FIX: the mesh is switched OFF - every vertex of it moved to its local origin (28 points in one place: no
triangle has an area, so no technique of the effect draws a pixel, the refraction mask included) and every vertex
alpha set to 0. Only the vertex chunk changes (1120 bytes, same size): the .prm keeps its size, its chunk count
and every index; the entity, its model root, the material and the textures stay as they are.
LOST: the heat shimmer over a burning car - which Dog Days has on none of its own fires. Flames, smoke, sparks,
the blast and the light are emitters and a light: untouched.
The rule `check` uses does not need the Dead Men files: a material instance of class Standard/Glass whose
(blend on, blend mode, render group) is not one of STOCK_GLASS is 'a glass form no stock level draws', and every
mesh of the level that uses it must be off. Every other emitter of the level is looked at too (template found by
name, sprite chunk, texture in the .TEX): particles are sprites and have no material, so they cannot have this fault.

THE CAUSE IN THE CONVERTER, for whoever holds those files (NOT changed here): kl_mat.convert_mat_full keeps a Dead
Men Standard/Glass instance in a (blend mode, render group) form Dog Days never draws that class in
(TRANS_ON_OPAQUE, 0x31 -> 0x41 by RENDER_GROUP), and kl_light.fit_shaders() then switches its ALPHAFADEENABLED off
as a 'cost 2' feature - on a refraction that fade is all that hides the surface. Such an instance should take
its mesh out of the model (or the converter should say so and stop), not be drawn.
"""
import collections, json, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G
import kl_texmat as T
import kl_prpjoin as J
import kl_fa

BS = chr(92)
GLASS = ('Standard', 'Glass')
# (blend enabled, blend mode, render group) of every Standard/Glass instance of the 21 stock Dog Days levels,
# with the number of instances (counted 2026-10-11; all 50 have Refraction2DEnabled).
STOCK_GLASS = {(0, None, 0x00): 5, (1, 'TRANS', 0x6c): 42, (1, 'TRANS', 0x46): 1, (1, 'ADD', 0x6f): 1,
               (1, 'ADD_BEFORE_TRANS', 0x69): 1}
VERTEX = 40          # static mesh vertex: +0 position (3 floats), +16 colour B G R A (the shader's COLOR3)
ALPHA_AT = 19
NAME = 'carfx'


# ------------------------------------------------------------------ reading
def _archive(folder):
    z = [f for f in sorted(os.listdir(folder)) if f.lower().endswith('_main.zip')]
    if len(z) != 1:
        raise ValueError('%s: expected one *_Main.zip' % folder)
    return os.path.join(folder, z[0])


class Build:
    def __init__(self, folder):
        import kl_gms, kl_rtp
        from kl_prp import Prp
        self.folder, self.zip = folder, _archive(folder)
        with zipfile.ZipFile(self.zip) as z:
            self.order = z.namelist()
            self.files = {n: z.read(n) for n in self.order}
        self.ext = {n.rsplit('_Main', 1)[1]: n for n in self.order if '_Main' in n}
        self.raw = kl_gms.unpack(self['.gms'])
        names, tids, buf = ['ROOT'], [kl_rtp.ROOT_TYPE], self['.buf']
        for decl, tid, _prio in kl_gms.entities(self.raw):
            o = struct.unpack_from('<I', self.raw, 4 * (decl & 0xffffff))[0]
            names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
        self.sc = J.Scene(Prp(self['.prp']), names, tids, 'dd', os.path.basename(self.zip))
        self.prm = G.read(self['.prm'], 'dd')
        self.mat = T.read_mat(self['.MAT'])
        self.tex = T.read_tex(self['.TEX'])

    def __getitem__(self, ext):
        return self.files[self.ext[ext]]

    def wardrobe_roots(self):
        p = os.path.join(self.folder, 'KLWardrobe.ini')
        if not os.path.isfile(p):
            return []
        with open(p) as fh:
            return [int(l.split('=')[1]) for l in fh if l.startswith('Root=')]


def _kid(node, tag):
    return next((c for c in node[3] if c[0] == tag), None)


def glass_form(mat, e):
    """(blend enabled, blend mode or None, render group) of a material instance."""
    rs = next((n for n in _kid(e.root, 'BIND')[3] if n[0] == 'RSTA'), None)
    bena = _kid(rs, 'BENA')[3] if rs and _kid(rs, 'BENA') else 0
    bmod = _kid(rs, 'BMOD')[3].decode('latin1') if rs and bena and _kid(rs, 'BMOD') else None
    return (1 if bena else 0, bmod, e.f[3])


def bools(e):
    out = {}
    for n in _kid(e.root, 'BIND')[3]:
        if n[0] == 'BOOL':
            en, v = _kid(n, 'ENAB'), _kid(n, 'VALU')
            out[_kid(n, 'NAME')[3].decode('latin1')] = bool(en and en[3] and v and v[3])
    return out


def bad_materials(mat):
    """{slot: (blend, mode, group)} of the Standard/Glass instances in a form no stock Dog Days level has."""
    import kl_mat
    out = {}
    for s, e in sorted(mat.insts.items()):
        if kl_mat.class_key(mat, e) == GLASS:
            f = glass_form(mat, e)
            if f not in STOCK_GLASS:
                out[s] = f
    return out


def texture_alpha(entry):
    """Mean alpha (0..255) of the first mip of a DXT3 / DXT5 texture record, None for another format."""
    _size, f1, _f2, _id, th, tw, _mips, _fl = struct.unpack_from('<I4s4sIHHII', entry, 0)
    if f1 not in (b'3TXD', b'5TXD'):
        return None
    q = entry.index(b'\0', 36) + 1
    n = struct.unpack_from('<I', entry, q)[0]
    data, total, count = entry[q + 4:q + 4 + n], 0, 0
    for b in range(((tw + 3) // 4) * ((th + 3) // 4)):
        blk = data[16 * b:16 * b + 8]
        if len(blk) < 8:
            break
        if f1 == b'3TXD':
            v = [(blk[k // 2] >> (4 * (k % 2)) & 15) * 17 for k in range(16)]
        else:
            a0, a1, bits = blk[0], blk[1], int.from_bytes(blk[2:8], 'little')
            pal = [a0, a1] + ([((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)] if a0 > a1 else
                              [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255])
            v = [pal[(bits >> (3 * k)) & 7] for k in range(16)]
        total += sum(v); count += 16
    return total / count if count else None


def vertices(prm, mesh):
    """-> (vertex chunk index, vertex count) of a mesh object; raises when it is not a 40-byte-vertex mesh."""
    sub = prm.u32(mesh, 0x28)
    if not sub or not prm.u32(sub, 0) or (len(prm.chunks[sub]) >= 8 and prm.u32(sub, 4)):
        raise ValueError('mesh %d: not exactly one descriptor' % mesh)
    d = prm.u32(sub, 0)
    nv, vtx = prm.u32(d, 0), prm.u32(d, 4)
    if len(prm.chunks[d]) != 48 or len(prm.chunks[vtx]) != (VERTEX * nv + 15 & ~15):
        raise ValueError('mesh %d: descriptor %d is not a Dog Days mesh of %d-byte vertices' % (mesh, d, VERTEX))
    return vtx, nv


def mesh_state(prm, mesh):
    """dict(vtx, nv, size=(x, y, z extent), lo, hi, alpha=(min, max), off=bool) of a mesh object."""
    vtx, nv = vertices(prm, mesh)
    v = prm.chunks[vtx]
    pos = [struct.unpack_from('<3f', v, VERTEX * j) for j in range(nv)]
    al = [v[VERTEX * j + ALPHA_AT] for j in range(nv)]
    lo = tuple(min(p[c] for p in pos) for c in range(3)); hi = tuple(max(p[c] for p in pos) for c in range(3))
    size = tuple(hi[c] - lo[c] for c in range(3))
    # off = nothing of it can be seen through the material's alpha; flat = it has no area either (the default fix)
    return dict(vtx=vtx, nv=nv, size=size, lo=lo, hi=hi, alpha=(min(al), max(al)), off=max(al) == 0, flat=max(size) == 0.0)


def _texture_of(B, chunk):
    """Texture id of a sprite chunk, or None."""
    prm = B.prm
    if not 0 < chunk < len(prm.chunks) or prm.u16(chunk, 2) != 2:
        return None
    return prm.u32(chunk, 4) % G.SLOTS['dd']


def fire_smoke(B, sc, groups):
    """The smoke of the fires the vehicles name: [dict(template, emitters, copies, same, colour, texture, name,
    alpha, shared)] for every template with 'smoke' in its name that an emitter inside one of `groups` names.
    copies / same: how many templates of that name the level holds and whether they are all alike (the emitter
    names its template by NAME: with unlike copies which one the game takes was not read)."""
    li = J.labels('dd', 'ZParticleEmitter').index('ZParticleEmitter[34]')
    tlab = J.labels('dd', 'ZParticleTemplate')
    tg, tc = tlab.index('ZGEOM[4]'), tlab.index('ZParticleTemplate[29]')
    named = collections.Counter()
    for g in sorted(groups):
        for k in range(g, sc.end[g]):
            if sc.cls(k) == 'ZParticleEmitter':
                n = kl_fa.node_values(sc, k)[li]
                if isinstance(n, str) and 'smoke' in n.lower():
                    named[n.lower()] += 1
    tpl, by_tex = collections.defaultdict(list), collections.defaultdict(set)
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZParticleTemplate':
            v = kl_fa.node_values(sc, k)
            tpl[sc.names[k].lower()].append((sc.names[k], v))
            by_tex[_texture_of(B, v[tg])].add(sc.names[k].lower())
    out = []
    for n, count in sorted(named.items()):
        cs = tpl.get(n, [])
        if not cs:
            continue
        name, v = cs[0]
        tex = _texture_of(B, v[tg])
        t = B.tex.tex.get(tex)
        ramp = v[tc] if isinstance(v[tc], list) else []
        keys = [ramp[i:i + 4] for i in range(0, len(ramp) - 3, 4)]
        dark = min(keys, key=lambda c: sum(c[:3])) if keys else None
        out.append(dict(template=name, emitters=count, copies=len(cs), same=all(c[1] == v for c in cs),
                        colour=[round(x) for x in dark] if dark else None, keys=len(keys), alpha_key=round(max(c[3] for c in keys)) if keys else None,
                        texture=tex, name=t.name.split('/')[-1] if t else None,
                        alpha=None if t is None else texture_alpha(t.entry), shared=sorted(by_tex[tex] - set(named))))
    return out


def survey(B):
    """Everything check() and apply() need: the bad materials, the meshes that use them, the entities that hold
    those meshes, the cars, and the emitters' cross-check."""
    sc, prm, mat = B.sc, B.prm, B.mat
    bad = bad_materials(mat)
    roots = G.level_roots(sc.p, sc.tids, B.raw, B.wardrobe_roots())
    kinds, _args = G.walk(prm, roots)
    meshes = {i: prm.u16(i, 0x12) for i, k in kinds.items() if k == 'mesh' and prm.u16(i, 0x12) in bad}
    # who uses a vertex chunk: {vtx: set(mesh)}
    users = collections.defaultdict(set)
    for i, k in kinds.items():
        if k == 'mesh':
            sub = prm.u32(i, 0x28)
            if sub:
                d = prm.u32(sub, 0)
                if d:
                    users[prm.u32(d, 4)].add(i)
    root_of = collections.defaultdict(list)                 # model root -> its bad meshes
    for i, k in kinds.items():
        if k == 'root':
            t, n = prm.u32(i, 0x18), prm.u32(i, 0x14)
            for j in range(n):
                m = prm.u32(t, 4 * j)
                if m in meshes:
                    root_of[i].append(m)
    gms = G.gms_roots(B.raw)
    ents = []
    for k in range(1, len(sc.nodes)):
        r = gms[k - 1]
        if r in root_of:
            v = kl_fa.node_values(sc, k)
            ents.append(dict(node=k, path=sc.path[k], cls=sc.cls(k), hidden=v[3], root=r, meshes=root_of[r]))
    # the cars: every node with a VehicleEffects controller, the groups it names, and whether one holds the mesh
    holder = {e['node'] for e in ents}
    cars, fire_groups = [], set()
    for k, _i, vals in kl_fa.controllers(sc, 'VehicleEffects'):
        named, box = [], []
        for s in vals:
            if isinstance(s, str) and s[:5].upper() == 'ROOT' + BS:
                for g in sc.resolve(s):
                    short = sc.names[g]
                    fire_groups.add(g)
                    named.append(short)
                    if any(g <= h < sc.end[g] for h in holder):
                        box.append(short)
        drive = [sc.cls(c) for c in range(k + 1, sc.end[k]) if sc.parent[c] == k and sc.cls(c) in ('ZHavokCar',)]
        cars.append(dict(node=k, path=sc.path[k], pos=[round(x) for x in kl_fa.node_values(sc, k)[2]],
                         drive=drive[0] if drive else 'no ZHavokCar', blowup=next((s for s in vals if isinstance(s, str) and 'blowup' in s.lower()), ''),
                         groups=sorted(set(named)), box=sorted(set(box))))
    # the emitters: template by name -> sprite chunk -> texture
    lab = J.labels('dd', 'ZParticleEmitter')
    i34 = lab.index('ZParticleEmitter[34]')
    tl = J.labels('dd', 'ZParticleTemplate').index('ZGEOM[4]')
    tpl = {}
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZParticleTemplate':
            tpl.setdefault(sc.names[k].lower(), k)
    em = dict(emitters=0, no_template=collections.Counter(), no_sprite=collections.Counter(), no_texture=collections.Counter())
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZParticleEmitter':
            continue
        em['emitters'] += 1
        name = kl_fa.node_values(sc, k)[i34]
        t = tpl.get(name.lower()) if isinstance(name, str) else None
        if t is None:
            em['no_template'][name] += 1
            continue
        ch = kl_fa.node_values(sc, t)[tl]
        if not 0 < ch < len(prm.chunks) or prm.u16(ch, 2) != 2:
            em['no_sprite'][name] += 1
        elif prm.u32(ch, 4) % G.SLOTS['dd'] not in B.tex.tex:
            em['no_texture'][name] += 1
    return dict(bad=bad, meshes=meshes, users=users, ents=ents, cars=cars, emitters=em, kinds=kinds,
                smoke=fire_smoke(B, sc, fire_groups))


def material_lines(B, slot):
    """The material instance in words: name, form, switches on, texture stages with the diffuse alpha."""
    e = B.mat.insts[slot]
    on = sorted(k for k, v in bools(e).items() if v)
    st = []
    for name, n in T.texture_stages(e):
        v = n[3]
        if v and not v & T.ENGINE_SLOT and v in B.tex.tex:
            x = B.tex.tex[v]
            a = texture_alpha(x.entry)
            st.append('%s = %d %s %s%s' % (name, v, x.name.split('/')[-1], x.entry[4:8][::-1].decode('latin1'),
                                           '' if a is None else ' (mean alpha %.0f of 255)' % a))
        else:
            st.append('%s = %s' % (name, 'no texture' if not v else hex(v)))
    f = glass_form(B.mat, e)
    return ['material %d %s: Standard/Glass, blend %s, render group 0x%x - stock Dog Days has this class only as %s' % (
                slot, e.name, f[1] or 'off', f[2], ', '.join('%s in 0x%x (%d)' % (m or 'opaque', g, n) for (_b, m, g), n in STOCK_GLASS.items())),
            '    switches on: %s' % ', '.join(on),
            '    stages: %s' % '; '.join(st)]


# ------------------------------------------------------------------ check
def check(folder, log=print, B=None, cars=False):
    """-> (faults [text], facts dict). A fault = a mesh that would be drawn with a glass form no stock level has."""
    B = B or Build(folder)
    S = survey(B)
    faults, facts = [], collections.OrderedDict(build=B.zip)
    log('kl_fa_carfx check: %s' % B.zip)
    if not S['bad']:
        log('  no Standard/Glass material in a form stock Dog Days does not have')
    for slot in S['bad']:
        for l in material_lines(B, slot):
            log('  ' + l)
    states = {}
    for m in sorted(S['meshes']):
        try:
            states[m] = mesh_state(B.prm, m)
        except ValueError as x:
            states[m] = None
            faults.append('mesh %d uses material %d and cannot be read: %s' % (m, S['meshes'][m], x))
    log('  meshes with it: %d; entities that hold one: %d' % (len(S['meshes']), len(S['ents'])))
    rows = []
    groups = collections.OrderedDict()
    for e in S['ents']:
        par = e['path'].split(BS)
        key = (BS.join(par[-3:-1]) if len(par) > 3 else par[0], e['path'].split(BS)[-1], tuple(e['meshes']))
        groups.setdefault(key, []).append(e)
    for (where, name, ms), es in groups.items():
        for m in ms:
            st = states.get(m)
            if st is None:
                continue
            word = ('off (no area, alpha 0)' if st['off'] and st['flat'] else
                    'off by alpha 0 only (the shape of %.1f x %.1f x %.1f m is kept: the --alpha-only variant)' % tuple(x / 100 for x in st['size'])
                    if st['off'] else 'DRAWN: a box of %.1f x %.1f x %.1f m, vertex alpha up to %.2f' % (
                        st['size'][0] / 100, st['size'][1] / 100, st['size'][2] / 100, st['alpha'][1] / 255))
            log('    %-11s x%-2d in %s (mesh %d, %d vertices, hidden %s): %s' % (name, len(es), where[-78:], m, st['nv'], es[0]['hidden'], word))
            rows.append(dict(name=name, where=where, copies=len(es), mesh=m, off=st['off'], flat=st['flat'], size=[round(x, 1) for x in st['size']],
                             alpha=list(st['alpha']), nodes=[e['node'] for e in es]))
            if not st['off']:
                faults.append('%s in %s (%d entities, mesh %d) is drawn with material %d %s: a box of %.1f x %.1f x %.1f m in a glass form no stock level draws' % (
                    name, where, len(es), m, S['meshes'][m], B.mat.insts[S['meshes'][m]].name, st['size'][0] / 100, st['size'][1] / 100, st['size'][2] / 100))
    held = {m for e in S['ents'] for m in e['meshes']}
    for m in sorted(set(S['meshes']) - held):
        st = states.get(m)
        if st and not st['off']:
            faults.append('mesh %d (material %d) is in a model no entity names by its root and is not off' % (m, S['meshes'][m]))
    log('  vehicles with a VehicleEffects controller: %d' % len(S['cars']))
    drawn = any(not r['off'] for r in rows)
    kinds = collections.OrderedDict()
    for c in S['cars']:
        fire = [g for g in c['groups'] if 'fire' in g.lower()]
        word = (('THE BOX (%s)' % ', '.join(c['box'])) if c['box'] and drawn else
                ('its fire holds the mesh: off' if c['box'] else 'no such mesh in what it names'))
        c['verdict'] = word
        if cars:
            log('    %-62s at (%d, %d, %d) %s %s: fire %s -> %s' % (
                c['path'][5:][-62:], *c['pos'], c['drive'], c['blowup'] or '-', ', '.join(fire) or 'none', word))
        kinds.setdefault((c['drive'], c['blowup'] or '-', ', '.join(fire) or 'none', word), []).append(c['path'].split(BS)[-1])
    if not cars:
        for (drive, blow, fire, word), names in kinds.items():
            log('    x%-3d %s, %s, fire %s -> %s   [%s%s]' % (len(names), drive, blow, fire, word, ', '.join(names[:3]),
                                                           ', ...' if len(names) > 3 else ''))
    em = S['emitters']
    log('  emitters: %d; template not in the level: %d (%s); template without a sprite chunk: %d; sprite texture not in the .TEX: %d'
        % (em['emitters'], sum(em['no_template'].values()), ', '.join('%s x%d' % kv for kv in em['no_template'].most_common(4)) or '-',
           sum(em['no_sprite'].values()), sum(em['no_texture'].values())))
    if em['no_sprite'] or em['no_texture']:
        faults.append('emitters whose template has no sprite or whose sprite has no texture: %s' % dict(em['no_sprite'] + em['no_texture']))
    # NOT a fault, a fact for whoever looks at the game: the fires' own smoke, which this tool's fix leaves alone
    # and which can be the dark block of the owner's pictures as well as the mesh (re/carfx.md 2).
    if S['smoke']:
        log('  smoke of the fires the vehicles name (NOT changed by the fix; a dark column over a burning car may be this):')
    for s in S['smoke']:
        log('    %-22s x%-2d emitters; darkest colour key %s, highest alpha key %s of 255 (%s keys); texture %s %s mean alpha %s%s%s' % (
            s['template'], s['emitters'], tuple(s['colour'][:3]) if s['colour'] else '-', s['alpha_key'], s['keys'], s['texture'], s['name'],
            '-' if s['alpha'] is None else '%.0f' % s['alpha'],
            '' if s['copies'] == 1 else '; %d templates of this name, %s' % (s['copies'], 'alike' if s['same'] else 'UNLIKE (which one the game takes: not read)'),
            '' if not s['shared'] else '; texture shared with %d other template(s)' % len(s['shared'])))
    facts.update(smoke=S['smoke'])
    facts.update(materials={str(s): [B.mat.insts[s].name] + list(f) for s, f in S['bad'].items()}, rows=rows,
                 cars=S['cars'], emitters=dict(emitters=em['emitters'], no_template=dict(em['no_template']),
                                               no_sprite=dict(em['no_sprite']), no_texture=dict(em['no_texture'])))
    for f in faults:
        log('  FAIL ' + f)
    log('  RESULT %s: %d fault(s); %d place(s) hold such a mesh, %d off; %d of %d vehicles name a fire that holds one' % (
        'FAIL' if faults else 'PASS', len(faults), len(rows), sum(r['off'] for r in rows), sum(1 for c in S['cars'] if c['box']), len(S['cars'])))
    return faults, facts


# ------------------------------------------------------------------ apply
def clear_smoke(B, S, log=print):
    """TEST ONLY (`apply --smoke-clear`): the alpha of the sprite textures only the fires' smoke templates use is
    set to 0 in every mip, in place - that smoke is then not drawn. -> (new .TEX bytes, [(texture id, name,
    templates)]). A texture another template uses too is left alone and said."""
    data, done = bytearray(B['.TEX']), []
    by_tex = collections.defaultdict(list)
    for s in S['smoke']:
        by_tex[s['texture']].append(s)
    for tex, ss in sorted(by_tex.items(), key=lambda kv: str(kv[0])):
        names = [s['template'] for s in ss]
        t = B.tex.tex.get(tex)
        if t is None or ss[0]['shared']:
            log('  smoke texture %s (%s) is left alone: %s' % (tex, ', '.join(names), 'not in the .TEX' if t is None else
                'also the sprite of %s' % ', '.join(ss[0]['shared'][:4])))
            continue
        e = t.entry
        _size, f1, _f2, _id, _th, _tw, mips, _fl = struct.unpack_from('<I4s4sIHHII', e, 0)
        at = bytes(data).find(e)
        if f1 not in (b'3TXD', b'5TXD') or at < 0 or bytes(data).find(e, at + 1) >= 0:
            raise ValueError('texture %s: not one DXT3 / DXT5 record in the .TEX' % tex)
        q = e.index(b'\0', 36) + 1
        for _m in range(mips):
            n = struct.unpack_from('<I', e, q)[0]
            for b in range(n // 16):
                data[at + q + 4 + 16 * b:at + q + 4 + 16 * b + 8] = bytes(8)     # alpha (DXT3: 4 bits a texel; DXT5: two ends + indices) = 0
            q += 4 + n
        if q != len(e):
            raise ValueError('texture %s: its mips do not fill the record (%d of %d bytes)' % (tex, q, len(e)))
        done.append((tex, t.name, names))
        log('  smoke texture %d %s (sprite of %s only): alpha 0 in its %d mips' % (tex, t.name, ', '.join(names), mips))
    return bytes(data), done


def switch_off(B, S, log=print, keep_shape=False):
    """Every mesh of a bad material: all vertices to the local origin (not with keep_shape), vertex alpha 0.
    -> [(mesh, vtx, nv)]."""
    prm, done, seen = B.prm, [], set()
    for m in sorted(S['meshes']):
        vtx, nv = vertices(prm, m)
        other = S['users'][vtx] - set(S['meshes'])
        if other:
            raise ValueError('vertex chunk %d of mesh %d is also used by meshes %s that keep their material' % (vtx, m, sorted(other)[:4]))
        if vtx in seen:
            continue
        seen.add(vtx)
        v = bytearray(prm.chunks[vtx])
        for j in range(nv):
            if not keep_shape:
                struct.pack_into('<3f', v, VERTEX * j, 0.0, 0.0, 0.0)
            v[VERTEX * j + ALPHA_AT] = 0
        if bytes(v) != prm.chunks[vtx]:
            prm.chunks[vtx] = bytes(v)
            done.append((m, vtx, nv))
            log('  mesh %d: its %d vertices (chunk %d, %d bytes) %s, alpha 0' % (
                m, nv, vtx, len(v), 'keep their places' if keep_shape else 'moved to one point'))
    return done


def apply(src, dst, log=print, mode='off'):
    """The build of folder `src` written to the NEW folder `dst`. -> report. mode:
      'off'    the heat-shimmer meshes off (no area, alpha 0): THE FIX
      'alpha'  the same with the vertices left in place (alpha 0 only): to tell the two changes apart if a blast
               misbehaves with 'off'
      'smoke'  TEST ONLY, not a fix: the meshes LEFT AS THEY ARE and the fires' dark smoke made invisible
               (clear_smoke) - the twin of 'off' for the live look that says which of the two the dark block is
    Raises before anything is written when there is nothing to do or a proof fails."""
    import kl_graft
    if mode not in ('off', 'alpha', 'smoke'):
        raise ValueError(mode)
    member = '.TEX' if mode == 'smoke' else '.prm'
    zp = _archive(src)
    dst = os.path.abspath(dst)
    if dst == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the out folder is the build itself')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: a build folder is never written into' % dst)
    lines = []

    def say(s=''):
        log(s)
        lines.append(s)
    say('kl_fa_carfx apply (%s): %s -> %s' % ({'off': 'the fix', 'alpha': 'alpha only', 'smoke': 'TEST ONLY: smoke cleared, mesh kept'}[mode], zp, dst))
    B = Build(src)
    before, facts0 = check(src, say, B)
    if not before:
        raise ValueError('nothing to switch off: check finds no fault in %s' % src)
    S = survey(B)
    old = list(B.prm.chunks)
    files, textures = dict(B.files), []
    if mode == 'smoke':
        data, textures = clear_smoke(B, S, say)
        done, changed = [], []
        if not textures or len(data) != len(B['.TEX']):
            raise ValueError('no smoke texture of the fires could be cleared')
    else:
        done = switch_off(B, S, say, keep_shape=mode == 'alpha')
        if not done:
            raise ValueError('check names a fault that switching the meshes off does not touch: %s' % before[:2])
        data = G.write(B.prm)
        if len(data) != len(B['.prm']):
            raise ValueError('the .prm changed its size')
        changed = [i for i in range(1, len(old)) if old[i] != B.prm.chunks[i]]
        if sorted(changed) != sorted(v for _m, v, _n in done):
            raise ValueError('chunks other than the vertex chunks changed: %s' % changed[:8])
    files[B.ext[member]] = data
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in B.order])
    skip = (NAME + '.json', NAME + '.txt')
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp and x not in skip:
            shutil.copyfile(q, os.path.join(dst, x))
    with zipfile.ZipFile(zp) as za, zipfile.ZipFile(out) as zb:
        ia, ib = za.infolist(), zb.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        diff = [i.filename.rsplit('_Main', 1)[-1] for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
        grown = [i.filename for i, j in zip(ia, ib) if j.file_size > i.file_size]
    if diff != [member] or grown:
        raise ValueError('not exactly the %s differs from the build (%s), or a member grew (%s)' % (member, diff, grown))
    slot = os.path.basename(zp)[:-len('_Main.zip')]
    sj = os.path.join(dst, 'steps.json')
    step = NAME if mode == 'off' else NAME + '_' + mode
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st[step], st['final'] = diff, kl_maps.member_ids(dst, slot)
        st['same'] = [e for e in st.get('same', []) if e not in diff]
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    say('  only the %s member differs from the build (%d members, %d bytes each side%s); %d files beside the '
        'archive copied%s' % (member, len(B.order), len(data), '' if mode == 'smoke' else ', %d of its %d chunks: %s' % (len(changed), len(old) - 1, changed),
                              len(os.listdir(dst)) - 1, '; steps.json continued (\'%s\')' % step if os.path.isfile(sj) else ''))
    say('')
    after, facts = check(dst, say)
    if mode == 'smoke':
        if len(after) != len(before):
            raise ValueError('the smoke test build must keep the mesh as it was: %d fault(s) before, %d after' % (len(before), len(after)))
        if any(s['alpha'] for s in facts['smoke'] if s['texture'] in {t for t, _n, _l in textures}):
            raise ValueError('a cleared smoke texture still has alpha')
        say('  TEST BUILD, NOT A FIX: check still FAILs on purpose (the mesh is kept); the smoke of %s is not drawn' % ', '.join(
            n for _t, _n, l in textures for n in l))
    elif after:
        raise ValueError('the written build still fails: %s' % after[:2])
    report = collections.OrderedDict(source=zp, out=out, mode=mode, members_changed=diff, chunks_changed=changed,
                                     textures_cleared=[dict(texture=t, name=n, templates=l) for t, n, l in textures],
                                     meshes=[dict(mesh=m, vertex_chunk=v, vertices=n) for m, v, n in done],
                                     faults_before=before, check=facts)
    with open(os.path.join(dst, NAME + '.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(dst, NAME + '.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return report


# ------------------------------------------------------------------ the material, node by node
def material(folder, log=print):
    import kl_light as L
    B = Build(folder)
    bad = bad_materials(B.mat)
    have = L.shader_cache(B['.fxc'])
    for slot in bad:
        e = B.mat.insts[slot]
        for l in material_lines(B, slot):
            log(l)
        for path, n in T.walk(e.root):
            if n[1] == T.LIST and n[0] in ('TEXT', 'BOOL', 'COLO', 'FLTV', 'RSTA', 'SCRL'):
                d = []
                for ch in n[3]:
                    v = ch[3]
                    if isinstance(v, bytes) and ch[1] != T.STRING:
                        v = [round(f, 3) for f in struct.unpack('<%df' % (len(v) // 4), v)]
                    elif ch[1] == T.FLOAT and isinstance(v, int):
                        v = round(struct.unpack('<f', struct.pack('<I', v))[0], 3)
                    elif isinstance(v, bytes):
                        v = v.decode('latin1')
                    d.append('%s=%s' % (ch[0], v))
                log('    %s %s' % (n[0], ' '.join(d)))
        for need in sorted(L.shader_needs(B.mat, e), key=str):
            log('    asks for %s %s %s: %s' % (need[0], need[1], sorted(need[2]), 'in the cache' if need in have else 'NOT in the cache'))
    if not bad:
        log('no Standard/Glass material in a form stock Dog Days does not have')


def main():
    a = sys.argv[1:]
    cars = '--cars' in a
    mode = 'alpha' if '--alpha-only' in a else 'smoke' if '--smoke-clear' in a else 'off'
    a = [x for x in a if x not in ('--cars', '--alpha-only', '--smoke-clear')]
    if len(a) >= 2 and a[0] == 'check':
        n = 0
        for f in a[1:]:
            faults, _facts = check(f, cars=cars)
            n += len(faults)
        sys.exit(1 if n else 0)
    elif len(a) == 3 and a[0] == 'apply':
        apply(a[1], a[2], mode=mode)
    elif len(a) == 2 and a[0] == 'material':
        material(a[1])
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
