#!/usr/bin/env python3
"""
pd2_gun.py - a Payday 2 rifle (wpn_npc_ak47, the AKM) on Dog Days' shop gun Rifle_Type81 (item 33, page II),
model, texture and shot sound. Data side only: it writes a staged F01 slot (zip + WHD + WAV), nothing is installed.
Plan: re/pd2_guns_page2_1025.md. Payday 2 data is read from <work>/pd2 and never leaves it.

    python tools/pd2_gun.py selftest            the stock Type 81 rigid parts rebuilt byte for byte (+ DXT5 -> DXT1, + the flat maps)
    python tools/pd2_gun.py build <outdir>      model + textures + sound -> <outdir>/F01_Main.zip, .WHD, .WAV, report.json
    python tools/pd2_gun.py model <outdir>      the model half only (F01_Main.zip, no sound change)

WHAT IS A RIGID GUN PART (read from the five Type 81 parts of the stock F01, 2026-10-25, selftest below)
  mesh object (64 bytes): +0x0c 2 (rigid), +0x0e lod mask, +0x0f variant, +0x12 material (u16), +0x28 subtab chunk,
                          +0x38 1, +0x3c bone number. subtab = [descriptor, 0, 0, 0]. descriptor = 12 dwords
                          [nv, vertex chunk, 0, 0, 0, dword5, index chunk, 0 x 5]; dword5 is 1541 / 130 / 58 / 40 / 98 on the
                          five parts (GUESS: a count the engine reads for something; the mask writer uses 0 and draws).
  vertex (40 bytes): +0 pos f32 x3, +12 normal B,G,R,0, +16 colour ff ff ff ff, +20 uv f32 x2, +28 tangent B,G,R,0,
                     +32 binormal B,G,R,0, +36 pad cd cd cd cd. The chunk is padded to 16 bytes.
  index chunk: u16 1, u16 n, n x u16, padded to 16.
"""
import json, math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G, kl_texmat as T
import kl_pd2mask as PM

TEMPLATE = 'Rifle_Type81'
PD2_DIR = 'units/payday2/weapons/wpn_npc_ak47'
PD2_MESH = 'g_body'                # 575 vertices, 396 triangles: receiver, barrel, stock, magazine in one mesh
STOCK_MAT_NAME = 'Weapons/W_Rifle_Type81_01'
NEW_MAT_NAME = 'Weapons/W_PD2_AKM_01'
TAG = '1025pd2gun'
# The PD2 -> Dog Days frame is the axis map (x, y, z)_dd = (y, z, -x)_pd2 (as for the masks, re/pd2_klside.md), THEN a turn of
# TURN_DEG about z, a SCALE and a SHIFT. Dog Days holds every gun 10 degrees nose-down in its own space (re/map_guns.md section 8:
# w_bone_frame rests turned 9.8 degrees, AK-74 DM -> DD = -10.00 degrees), so a model that is level in its own space points ~10
# degrees UP out of the hands and its fore-end floats 3 - 7 cm above the left hand (the owner's 'held weirdly when aiming in',
# 1025c: that build had no turn). 1025d: the turn is ESTABLISHED (-10); SCALE / SHIFT are FITTED with tools/pd2_gun_fit.py
# (python pd2_gun_fit.py) against the stock Type 81 surface (area-sampled triangles, not just vertices), cost = grip gap in
# kl_map_guns.GRIP_ZONE (both ways, worst 20 % left out) + the fore-end underside under the 'l hand attacher' (x 36..52, 2 cm
# bins) + 0.3 x the muzzle's distance from the stock's 71.43. Result: scale 1.0 (the PD2 AKM is 88 cm in real centimetres, the
# Type 81 95; the best fit lands on 1.0 - 1.02, 1.0 is kept = true size), shift (10.5, 2.0) -> grip gap 0.31 cm, fore-end
# underside within 0.13 cm of the Type 81's, muzzle 71.4 (stock 71.43), butt at -17.7 (the Type 81's stock reaches -24).
# The z shift 0.65 is the gun's axis: w_bone_frame z 0.65 and 'l hand attacher' z 0.64 (the old 1.9 was a bounds fit that the
# charging handle's z -3.9 pulled sideways). NOT seen in the hands yet (GUESS until the owner plays it).
TURN_DEG = -10.0
SCALE = 1.0
SHIFT = (10.5, 2.0, 0.65)


# ------------------------------------------------------------------ the 40-byte rigid vertex
def rigid_vertex(pos, nrm4, uv, tan4, bin4, colour=b'\xff\xff\xff\xff', pad=b'\xcd\xcd\xcd\xcd'):
    return struct.pack('<3f', *pos) + nrm4 + colour + struct.pack('<2f', *uv) + tan4 + bin4 + pad


def vertex_chunk(plate, flip=True):
    """40-byte rigid vertex stream of a Plate (tangent frame computed as the mask writer does)."""
    tris = [(a, c, b) for a, b, c in plate.tris] if flip else plate.tris
    tan, bin_ = PM.tangents(plate.pos, plate.uv, tris)
    out = b''.join(rigid_vertex(plate.pos[k], PM.pack_dir(plate.nrm[k]), plate.uv[k], PM.pack_dir(tan[k]), PM.pack_dir(bin_[k]))
                   for k in range(len(plate.pos)))
    return out + bytes(-len(out) % 16)


def rigid_object(template, lod, variant, material, sub):
    """64-byte rigid mesh object from a stock one (every other field is the template's: +0x14.. +0x1c draw mode, bone ...)."""
    c = bytearray(template)
    if len(c) != 64 or c[0x0c] != 2:
        raise ValueError('the template is not a rigid mesh object')
    c[0x0e], c[0x0f] = lod, variant
    struct.pack_into('<H', c, 0x12, material)
    struct.pack_into('<I', c, 0x28, sub)
    return bytes(c)


# ------------------------------------------------------------------ textures
def dxt5_to_dxt1(mips):
    """Drop the alpha half of every DXT5 block. A DXT5 colour half always decodes in 4-colour mode, a DXT1 block only
    when c0 > c1, so a block with c0 < c1 gets its end points swapped (indices 0<->1, 2<->3) and one with c0 == c1 all
    indices 0 (all four colours equal). Pixel-exact for the colour (selftest decodes both)."""
    swap = {0: 1, 1: 0, 2: 3, 3: 2}
    out = []
    for m in mips:
        o = bytearray()
        for q in range(0, len(m), 16):
            c0, c1, bits = struct.unpack_from('<HHI', m, q + 8)
            if c0 == c1:
                bits = 0
            elif c0 < c1:
                c0, c1 = c1, c0
                bits = sum(swap[(bits >> (2 * k)) & 3] << (2 * k) for k in range(16))
            o += struct.pack('<HHI', c0, c1, bits)
        out.append(bytes(o))
    return out


def _565(c):
    return ((c >> 11) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31)


def decode_colour(block, dxt5):
    """RGB x 16 of one block's colour half (DXT1 rules, or the always-4-colour DXT5 rule)."""
    c0, c1, bits = struct.unpack_from('<HHI', block, 8 if dxt5 else 0)
    a, b = _565(c0), _565(c1)
    if dxt5 or c0 > c1:
        pal = [a, b, tuple((2 * x + y) // 3 for x, y in zip(a, b)), tuple((x + 2 * y) // 3 for x, y in zip(a, b))]
    else:
        pal = [a, b, tuple((x + y) // 2 for x, y in zip(a, b)), (0, 0, 0)]
    return [pal[(bits >> (2 * k)) & 3] for k in range(16)]


def dds_bytes(fourcc, w, h, mips):
    """A minimal DDS file (what kl_pd2mask.dds_mips reads) from a mip chain."""
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000
    head = b'DDS ' + struct.pack('<7I', 124, flags, h, w, len(mips[0]), 0, len(mips)) + bytes(44)
    head += struct.pack('<II4s5I', 32, 4, fourcc, 0, 0, 0, 0, 0) + struct.pack('<5I', 0x401008, 0, 0, 0, 0)
    return head + b''.join(mips)


# A flat DXT5 normal-map block: copied from the stock Type 81 normal map (.TEX 998, selftest asserts it is there).
FLAT_NORMAL_BLOCK = bytes.fromhex('80800000000000' + '00' + 'c0070002ffffffff')
# A neutral grey DXT1 block (c0 = c1 = 0x4208 = rgb (8, 8, 8), every index 0): dull, no sparkle. GUESS: the stock spec maps are
# near-black too (3 mips of 4x4 in the stock Type 81's 999 are not read here).
GREY_BLOCK = struct.pack('<HHI', 0x4208, 0x4208, 0)


def flat_normal_dds():
    return dds_bytes(b'DXT5', 4, 4, [FLAT_NORMAL_BLOCK] * 3)


def grey_spec_dds():
    return dds_bytes(b'DXT1', 4, 4, [GREY_BLOCK] * 3)


def clone_material(mat, source_slot, name, diffuse, normal, specular):
    """A copy of the instance at `source_slot` (a 'Standard' material) with new .TEX ids. -> new slot."""
    src = mat.insts[source_slot]
    clone = T.Entry(src.cls, list(src.f), T._copy(src.root))
    for stage, node in T.texture_stages(clone):
        if stage == 'mapDiffuse':
            node[3] = diffuse
        elif stage == 'mapNormal':
            node[3] = normal
        elif stage in ('mapSpecularMask', 'mapReflectionMask'):
            node[3] = specular
    nm = next(n for n in clone.root[3] if n[0] == 'NAME')
    nm[3] = name.encode('latin1')
    slot = max(mat.insts) + 1
    if slot >= mat.ninst:
        raise ValueError('the .MAT has no free instance slot')
    mat.insts[slot] = clone
    return slot


# ------------------------------------------------------------------ the Payday 2 mesh
def pd2_dir():
    import kl_port_check
    return os.path.join(kl_port_check.workdir(), 'pd2', 'guns', 'src', PD2_DIR.replace('/', os.sep))


def pd2_plate(scale=SCALE, shift=SHIFT, deg=TURN_DEG):
    """The PD2 body mesh as a Plate in Dog Days model space + its DDS diffuse bytes. Axis map, then the turn about z (positions
    AND normals; the same matrix as kl_map_guns.house()), then scale and shift of the positions."""
    import pd2_model
    base = pd2_dir()
    model = pd2_model.Model(os.path.join(base, 'wpn_npc_ak47.model'))
    obj = next((o for o in model.mesh_objects() if o.name == PD2_MESH), None)
    if obj is None:
        raise ValueError('no mesh object %s (have %s)' % (PD2_MESH, [o.name for o in model.mesh_objects()]))
    m = model.world_mesh(obj)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    turn = lambda v: (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])
    kl = lambda v: tuple(a * scale + b for a, b in zip(turn((v[1], v[2], -v[0])), shift))
    pos = [kl(q) for q in m['pos']]
    nrm = [PM._norm(turn((n[1], n[2], -n[0]))) for n in m['nrm']]
    uv = [(u, 1.0 + v) for u, v in m['uv']]
    tris = [(a, c_, b) for a, b, c_ in (tuple(t) for t in m['tris'])]      # the frame is a reflection (det -1): reverse the sense
    plate = PM.Plate(pos, nrm, uv, tris, 'pd2_akm')
    return plate, open(os.path.join(base, 'ak_df.texture'), 'rb').read()


def split_magazine(plate):
    """Plate -> (body Plate, magazine Plate). The magazine is the connected piece of the mesh (vertices welded by position, so
    uv seams do not cut it) that holds the lowest vertex; whole triangles, so no stray ones. Each Plate keeps only its own
    vertices (indices remapped). Refuses a magazine that is not a small curved box below the receiver."""
    key, weld = {}, []
    for q in plate.pos:
        weld.append(key.setdefault(tuple(round(x, 3) for x in q), len(key)))
    par = list(range(len(key)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a, b, c in plate.tris:
        par[find(weld[a])] = find(weld[b]); par[find(weld[b])] = find(weld[c])
    low = min(range(len(plate.pos)), key=lambda i: plate.pos[i][1])
    root = find(weld[low])
    mag = [t for t in plate.tris if find(weld[t[0]]) == root]
    rest = [t for t in plate.tris if find(weld[t[0]]) != root]
    if not 10 <= len(mag) <= 80 or len(rest) < 100:
        raise ValueError('the lowest piece of the PD2 mesh has %d of %d triangles: not a magazine' % (len(mag), len(plate.tris)))

    def sub(tris, name):
        used = sorted({i for t in tris for i in t}); new = {o: n for n, o in enumerate(used)}
        return PM.Plate([plate.pos[i] for i in used], [plate.nrm[i] for i in used], [plate.uv[i] for i in used],
                        [tuple(new[i] for i in t) for t in tris], name)
    return sub(rest, 'pd2_akm_body'), sub(mag, 'pd2_akm_mag')


# ------------------------------------------------------------------ into the level
def build_model(lv, log=print, scale=SCALE, shift=SHIFT, deg=TURN_DEG, split=True):
    """lv (kl_chars.Lv of the F01 slot, edited in place): the Type 81's body part becomes the PD2 AK body on bone 1 and its
    magazine (split_magazine) a part of its own on bone 3 'w_bone_clip' (lod 15, a copy of the stock magazine part's object, so
    the reload animation takes it out of the gun), both on a new material with three new textures; the slide / sight parts are
    dropped (the bolt stays in the body: no part on bone 4); the stock box part, hidden, stays for the bounds. New model root, the
    template's Ground node(s) retargeted. split=False = the 1025c build (one part, the magazine baked in). -> report dict."""
    import kl_chars as C, kl_guns, kl_gms, kl_octree as O
    sc, raw = lv.scene(); raw = bytearray(raw)
    p, mat, tex = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT']), T.read_tex(lv['.TEX'])
    k = kl_guns.gun_node(sc, TEMPLATE)
    old, var, _aset = C.person(sc, k)
    objs = C.objects(p, old)
    nvs = {o: p.u32(p.u32(p.u32(o, 0x28), 0), 0) for o in objs}
    body = max(objs, key=lambda o: nvs[o])
    hidden = [o for o in objs if p.chunks[o][0x0e] == 16]      # the 52-vertex box part: lod mask 16, draw mode 0x80880, material _Basic/Colour_Black
    mags = [o for o in objs if p.u32(o, 0x3c) == 3 and p.chunks[o][0x0e] == 15]    # the stock magazine: bone 3 w_bone_clip, lod 15, 60 vertices
    if len(hidden) != 1 or p.u32(body, 0x3c) != 1 or p.chunks[body][0x0e] != 15 or var != 0 or len(mags) != 1 or mags[0] == body:
        raise ValueError('%s: unexpected parts (body %d bone %d, hidden %s, magazine %s, variant %d)' % (
            TEMPLATE, body, p.u32(body, 0x3c), hidden, mags, var))
    plate, df_dds = pd2_plate(scale, shift, deg)
    share = PM.outward_share(plate)
    if share < 0.95:
        raise ValueError('only %.1f %% of the PD2 triangles face outward' % (100 * share))
    whole = plate
    magp = None
    if split:
        plate, magp = split_magazine(whole)
    # textures: diffuse (alpha dropped), flat normal, neutral spec; the table-2 word of each is the stock Type 81 map's
    src_slot = p.u16(body, 0x12)
    stage = {s: n[3] for s, n in T.texture_stages(mat.insts[src_slot])}
    fourcc, w, h, mips = PM.dds_mips(df_dds)
    if fourcc == b'DXT5':
        mips, fourcc = dxt5_to_dxt1(mips), b'DXT1'
    df = PM.add_texture(tex, 'tex:Weapons/PD2_AKM#Diffuse_a', dds_bytes(fourcc, w, h, mips), group=tex.tex[stage['mapDiffuse']].group)
    nm = PM.add_texture(tex, 'tex:Weapons/PD2_AKM#Normal_a', flat_normal_dds(), normal_map=True, group=tex.tex[stage['mapNormal']].group)
    sp = PM.add_texture(tex, 'tex:Weapons/PD2_AKM#Specular_a', grey_spec_dds(), group=tex.tex[stage['mapSpecularMask']].group)
    slot = clone_material(mat, src_slot, NEW_MAT_NAME, df, nm, sp)
    # geometry: vertex / index / descriptor / subtab, then the object
    v = G.new_chunk(p, vertex_chunk(plate, flip=True))
    i = G.new_chunk(p, PM.index_chunk(plate.tris, flip=True))
    d = G.new_chunk(p, PM.descriptor(len(plate.pos), v, i, 0))        # dword5 = 0: GUESS (the stock parts carry 40..1541, meaning unread)
    sub = G.new_chunk(p, PM.subtab(d))
    new_body = G.new_chunk(p, rigid_object(p.chunks[body], 15, p.chunks[body][0x0f], slot, sub), p.refs[body])
    parts = [new_body]
    new_mag = None
    if magp is not None:
        mv = G.new_chunk(p, vertex_chunk(magp, flip=True))
        mi = G.new_chunk(p, PM.index_chunk(magp.tris, flip=True))
        md = G.new_chunk(p, PM.descriptor(len(magp.pos), mv, mi, 0))
        msub = G.new_chunk(p, PM.subtab(md))
        new_mag = G.new_chunk(p, rigid_object(p.chunks[mags[0]], 15, p.chunks[mags[0]][0x0f], slot, msub), p.refs[mags[0]])
        parts.append(new_mag)
    root = C._new(p, p.chunks[old]); p.refs[root] = 1
    C._set_objects(p, root, parts + [hidden[0]])
    PM.widen_root(p, root, whole.box())                      # the union of body and magazine
    # the .oct record of the root: a copy, as kl_guns.build does (its tree must be empty)
    oct_s = O.Oct.parse(lv['.oct'])
    refs0 = oct_s.record_refs(); rec_of = {x: n for n, x in enumerate(refs0)}
    ref = p.u32(old, 0x1c)
    if ref:
        r = oct_s.records[rec_of[ref]]
        if r.tree.items:
            raise ValueError('the .oct record of the Type 81 root is not an empty tree')
        oct_s.records.append(O.Record(r.vtable, r.pointer, O.Tree(r.tree.origin, r.tree.scale, [list(x) for x in r.tree.nodes], [], r.tree.fill)))
        refs1 = oct_s.record_refs()
        if refs1[:len(refs0)] != refs0:
            raise ValueError('appending an .oct record moved the base level records')
        p.chunks[root] = C._put(p.chunks[root], 0x1c, '<I', refs1[len(refs0)])
    models = C.gms_models(raw)
    users = [j for j in range(1, len(sc.nodes)) if models[j - 1][1] == old]
    for j in users:
        kl_guns._retarget(sc, raw, models, j, root)
    prm = G.write(p)
    mat.refs = T.material_refs(prm)
    lv['.prm'], lv['.MAT'], lv['.TEX'], lv['.oct'] = prm, T.write_mat(mat), T.write_tex(tex), oct_s.pack()
    lv['.gms'], lv['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    box = whole.box()
    rep = dict(template=TEMPLATE, stock_root=old, root=root, stock_parts=len(objs), kept_hidden_box=hidden[0], body_object=new_body,
               magazine_object=new_mag, stock_magazine_object=mags[0], vertices=len(whole.pos), triangles=len(whole.tris),
               body_vertices=len(plate.pos), body_triangles=len(plate.tris),
               magazine_vertices=len(magp.pos) if magp else 0, magazine_triangles=len(magp.tris) if magp else 0,
               outward_share=round(share, 4), material_slot=slot,
               textures=dict(diffuse=df, normal=nm, specular=sp), users=len(users), scale=scale, shift=list(shift), turn_deg=deg,
               box=[[round(x, 2) for x in box[0]], [round(x, 2) for x in box[1]]], prm_bytes=len(prm))
    if magp:
        mb = magp.box(); rep['magazine_box'] = [[round(x, 2) for x in mb[0]], [round(x, 2) for x in mb[1]]]
    log('  model: root %d -> %d, body %d verts / %d tris + magazine %d verts / %d tris (%.0f %% outward), material slot %d, textures %d/%d/%d, %d Ground node(s) retargeted' % (
        old, root, len(plate.pos), len(plate.tris), len(magp.pos) if magp else 0, len(magp.tris) if magp else 0, 100 * share, slot, df, nm, sp, len(users)))
    return rep


# ------------------------------------------------------------------ the HUD / shop picture
def silhouette_rgba(width_px=104, size=128, ss=4):
    """The AKM as a HUD silhouette: (size, size, 4) uint8, RGB 255 everywhere, alpha = the side view (axis map only, no turn: the
    pictures show a level gun), muzzle to the right, left-aligned at x 0, centred on row size/2. width_px 104 is the stock Type 81
    picture's 103 px (bbox x 0..102): GUESS that the two guns are drawn at the same cm per pixel (the AKM is about as long)."""
    import numpy as np
    from PIL import Image, ImageDraw
    plate, _df = pd2_plate(1.0, (0.0, 0.0, 0.0), 0.0)
    pos = np.array(plate.pos)
    x0, x1 = pos[:, 0].min(), pos[:, 0].max()
    s = width_px * ss / (x1 - x0)
    cy = (pos[:, 1].min() + pos[:, 1].max()) / 2
    im = Image.new('L', (size * ss, size * ss), 0); d = ImageDraw.Draw(im)
    px = lambda q: ((q[0] - x0) * s, size * ss / 2 - (q[1] - cy) * s)
    for a, b, c in plate.tris:
        d.polygon([px(pos[a]), px(pos[b]), px(pos[c])], fill=255)
    im = im.resize((size, size), Image.BOX)
    a = np.asarray(im, np.uint8)
    out = np.full((size, size, 4), 255, np.uint8); out[:, :, 3] = a
    return out


# ------------------------------------------------------------------ the shot sound
BANK = 'weapon_akm'
# Three of the ten mono 44.1 kHz clips of 0.31 - 0.39 s in weapon_akm.bnk (HIRC is not parsed, so WHICH clips are the plain shot
# cannot be read; chosen by shape, never heard - GUESS): 5554408, 9533249, 9912342 have the same envelope to within 2 % (RMS
# 0-25 ms 13.7-13.9 k, 25-100 ms 4.0 k, tail < 600 after 100 ms, peak at 6.5 / 8.8 / 9.3 ms), i.e. the three variations of ONE
# sound; the other seven fall in an 'A' family of 5 (these three + 210564 + 2888844) and a sharper 'B' family of 5 (peak 2-4 ms).
SHOT_IDS = (5554408, 9533249, 9912342)
# The Type 81 plays the AK-74's definition, shared with the AK-74 itself, and the AK-74 / AK47 / Zastava sound objects share ONE set
# of three wave objects, so replacing those clips would change all three guns. Instead: the Type 81 template is re-pointed at the
# AK47's definition (it keeps the dry fire, shell drop, pick-up and change sounds), the AK47's three shot sound objects get the wave
# objects of the Minimi helicopter gun (a campaign-only gun; 1.6 s records, used by nothing in a Fragile Alliance round), and the
# three helicopter records are overwritten with the PD2 clips. Side effect: Rifle_AK47 (item 31) plays the PD2 shot too.
GAIN_CAP_DB = 30.0
DONOR_DEF = 'rifle_ak47'
HELI_GUN = 'mg_minimi_spw_heli'
HELI_RECORDS = ['SFX/Weapons_KL2_Final/MG_MiniMi_SPW_Heli/MG_MiniMi_SPW_Heli_Shot_0%d.wav' % n for n in (1, 2, 3)]


def _lowpass(x, rate, fc):
    import numpy as np
    f = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1.0 / rate)
    f[fr > fc] = 0
    return np.fft.irfft(f, len(x))


def pd2_shots(log=print):
    """-> [(wem id, float mono at 32 kHz, seconds)] of SHOT_IDS read from the crates."""
    import numpy as np, pd2_audio
    import kl_gunsnd as K
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        streams = pd2_audio.bank(BANK)
    out = []
    for wid in SHOT_IDS:
        st = streams[wid]
        if st.channels != 1 or st.tag != 0x8311:
            raise ValueError('clip %d is not mono PTADPCM' % wid)
        x = np.array(st.decode()[0], dtype=np.float64) / 32768.0
        x = _lowpass(x, st.rate, 15500.0)                         # keep the 44.1 -> 32 kHz linear resample free of fold-over
        y = K.resample(x[:, None], st.rate, 32000)[:, 0]
        out.append((wid, y, len(y) / 32000.0))
    return out


def build_sound(lv, whd, wav, log=print):
    """-> (whd, wav, report). lv's .SND and .prp are edited in place. whd / wav: the F01 bank bytes."""
    import numpy as np, struct as st
    import kl_gunsnd as K, kl_gunsnd_match as M, kl_gunsnd_all as A, kl_snd as S, kl_map_guns as MG
    from kl_prp import units
    ref, how = A.ref_of(whd, wav)
    by = {w.name.lower(): w for w in K.waves(whd)}
    recs = [by[n.lower()] for n in HELI_RECORDS]
    repl, rows = {}, []
    # These clips are short (0.33 s) and fall away fast, so their first-250-ms RMS only reaches the reference with +33 dB (27 % of the
    # samples at the ceiling; the Desert Eagle reference has 7 %). The gain cap is raised from the bank tool's +18 dB to +30 dB: head
    # within 0.8 dB of the reference, 23 % of the samples clipped. A choice (GUESS, never heard): exact loudness costs more clipping.
    cap, M.MAXGAIN = M.MAXGAIN, GAIN_CAP_DB
    try:
        driven = [M.drive(y, ref) for _wid, y, _secs in pd2_shots(log)]
    finally:
        M.MAXGAIN = cap
    for w, (wid, _y, _secs), (z, gain, head) in zip(recs, [(i, None, None) for i in SHOT_IDS], driven):
        data, ns, pcmb = K.encode_for(w, z[:, None], 32000)
        repl[w.rec_off] = (data, ns, pcmb, ns / float(w.get('rate')))
        rows.append(dict(wem=wid, record=w.name, seconds=round(ns / float(w.get('rate')), 3), gain_db=round(float(gain), 2), head_db=round(float(head), 2), bytes=len(data)))
        log('  %-72s <- weapon_akm %d: %.3f s, gain %+.1f dB, head %.2f dBFS (reference %.2f, %s)' % (w.name[-72:], wid, ns / 32000.0, gain, head, ref, how))
    snd = lv['.SND']
    snd2, moved = K.repoint_snd(snd, DONOR_DEF, HELI_GUN)
    whd2, wav2, snd3 = K.rebuild(whd, wav, repl, snd2, log=lambda *_: None, keep_geometry=True)
    lv['.SND'] = snd3
    # the Type 81 template -> the AK47's definition
    sc, _raw = lv.scene()
    ss = S.Snd('dd', snd3)
    off = next(o for o, k in ss.kind.items() if k == 5 and ss.name(o).decode('latin1').endswith('/%s/%s#def' % (DONOR_DEF, DONOR_DEF)))
    kt = MG.template_node(sc, TEMPLATE)
    fld = MG.sound_field(); own = MG.sound_of(sc, kt, fld)
    node = sc.nodes[kt]
    us = [list(u) for u in units(node['props'][1:-1])]
    us[fld] = [(us[fld][0][0], st.pack('<I', off))]
    node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]
    lv['.prp'] = sc.p.serialize()
    log('  %s sound definition %s (%#x) -> %s (%#x); %d AK47 shot sound objects re-pointed at the %s wave objects' % (
        TEMPLATE, MG.sound_name(ss, own), own, DONOR_DEF, off, len(moved), HELI_GUN))
    return whd2, wav2, dict(clips=rows, reference_head_db=round(ref, 2), reference=how, definition_before=own, definition_after=off,
                            repointed=[(n, hex(a), hex(b)) for n, a, b in moved])


def build(outdir, with_sound=True, log=print):
    """The staged F01 slot: <outdir>/F01_Main.zip (+ .WHD / .WAV with sound) and report.json. Reads the LIVE slot's copy in
    <outdir>/../live (the caller copies it; this tool never touches the game folder)."""
    import kl_chars as C
    live = os.path.join(os.path.dirname(os.path.abspath(outdir)), 'live')
    lv = C.Lv(live)
    lv.beside, lv.side = {}, {}
    whd, wav = open(os.path.join(live, 'F01_Main.WHD'), 'rb').read(), open(os.path.join(live, 'F01_Main.WAV'), 'rb').read()
    rep = dict(model=build_model(lv, log))
    if with_sound:
        whd, wav, rep['sound'] = build_sound(lv, whd, wav, log)
    os.makedirs(outdir, exist_ok=True)
    lv.write(outdir, 'F01')
    if with_sound:
        open(os.path.join(outdir, 'F01_Main.WHD'), 'wb').write(whd)
        open(os.path.join(outdir, 'F01_Main.WAV'), 'wb').write(wav)
    import hashlib
    rep['md5'] = {f: hashlib.md5(open(os.path.join(outdir, f), 'rb').read()).hexdigest() for f in sorted(os.listdir(outdir)) if f.startswith('F01_Main')}
    json.dump(rep, open(os.path.join(outdir, 'report.json'), 'w'), indent=1, default=str)
    return rep


def verify(outdir, log=print):
    """Independent re-read of a staged slot against the live copy: which zip members / WHD records / WAV spans changed, the new
    root and parts parse, every vertex/index in range, the textures and the material resolve, the three records decode."""
    import zipfile, numpy as np
    import kl_chars as C, kl_guns, kl_gunsnd as K, kl_gunsnd_all as A, kl_gunsnd_match as M, kl_snd as S, kl_map_guns as MG
    live = os.path.join(os.path.dirname(os.path.abspath(outdir)), 'live')
    ok = True
    a, b = zipfile.ZipFile(os.path.join(live, 'F01_Main.zip')), zipfile.ZipFile(os.path.join(outdir, 'F01_Main.zip'))
    if a.namelist() != b.namelist():
        log('  member lists differ'); ok = False
    changed = sorted(n.rsplit('_Main', 1)[1] for n in a.namelist() if a.read(n) != b.read(n))
    log('  zip members changed: %s' % changed)
    ok &= set(changed) <= {'.prm', '.MAT', '.TEX', '.oct', '.gms', '.prp', '.SND'}
    lv = C.Lv(outdir)
    p, mat, tex = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT']), T.read_tex(lv['.TEX'])
    sc, raw = lv.scene()
    root = C.person(sc, kl_guns.gun_node(sc, TEMPLATE))[0]
    objs = C.objects(p, root)
    log('  Ground node of %s -> root %d with objects %s' % (TEMPLATE, root, objs))
    for o in objs:
        c = p.chunks[o]; d = p.u32(p.u32(o, 0x28), 0); nv = p.u32(d, 0)
        v = p.chunks[p.u32(d, 4)]; ix = p.chunks[p.u32(d, 0x18)]; n = struct.unpack_from('<H', ix, 2)[0]
        ii = struct.unpack_from('<%dH' % n, ix, 4)
        good = len(c) == 64 and c[0x0c] == 2 and len(v) == (nv * 40 + 15) // 16 * 16 and max(ii) < nv and n % 3 == 0 and p.u32(o, 0x3c) in (1, 3)
        m = mat.insts[p.u16(o, 0x12)]
        tx = {s: (n_[3], n_[3] in tex.tex) for s, n_ in T.texture_stages(m)}
        pts = [struct.unpack_from('<3f', v, 40 * k) for k in range(nv)]
        lo, hi = [min(q[k] for q in pts) for k in range(3)], [max(q[k] for q in pts) for k in range(3)]
        log('  object %d: %d verts, %d tris, bone %d, lod %d, material %d %s, box %s .. %s, textures %s -> %s' % (
            o, nv, n // 3, p.u32(o, 0x3c), c[0x0e], p.u16(o, 0x12), m.name, [round(x, 1) for x in lo], [round(x, 1) for x in hi],
            {k_: v_[0] for k_, v_ in tx.items()}, 'all present' if all(v_[1] or v_[0] in (0, 2147483648) for v_ in tx.values()) else 'MISSING'))
        ok &= good and all(v_[1] or v_[0] in (0, 2147483648) for v_ in tx.values())
    log('  material reference table matches the .prm: %s' % (mat.refs == T.material_refs(G.write(p))))
    # sound
    whd0, wav0 = open(os.path.join(live, 'F01_Main.WHD'), 'rb').read(), open(os.path.join(live, 'F01_Main.WAV'), 'rb').read()
    whd1, wav1 = open(os.path.join(outdir, 'F01_Main.WHD'), 'rb').read(), open(os.path.join(outdir, 'F01_Main.WAV'), 'rb').read()
    w0, w1 = {w.rec_off: w for w in K.waves(whd0)}, {w.rec_off: w for w in K.waves(whd1)}
    hl = {n.lower() for n in HELI_RECORDS}
    diff = [o for o in w0 if w0[o].name.lower() in hl]          # the three heli records (their WHD fields are kept since keep_geometry)
    log('  WHD records with changed fields: %s' % [w0[o].name.rsplit('/', 1)[-1] for o in w0 if w0[o].f != w1[o].f])
    ok &= all(w0[o].f == w1[o].f for o in w0)
    K.check_bank_preserved(whd0, wav0, whd1, wav1, changed=diff)
    log('  check_bank_preserved: every other record identical in fields and data')
    spans = [(w0[o].get('off'), w0[o].get('off') + w0[o].get('size')) for o in diff]      # the old span: a shorter clip is zero-padded to it
    outside = [i for i in range(0, len(wav0), 4096) if wav0[i:i + 4096] != wav1[i:i + 4096] and not any(s <= i + 4095 and i < e for s, e in spans)]
    log('  WAV: size %d -> %d, bytes differing outside the three record spans: %d blocks' % (len(wav0), len(wav1), len(outside)))
    ok &= len(diff) == 3 and not outside and len(wav0) == len(wav1) and len(whd0) == len(whd1)
    ref, how = A.ref_of(whd0, wav0)
    for o in diff:
        x = K.decode_wave(wav1, w1[o])[:, 0]
        pk = float(np.abs(x).max())
        log('    %s: %d samples (%.3f s), peak %.3f, head %.2f dBFS (reference %.2f), at the ceiling %.1f %%' % (
            w1[o].name.rsplit('/', 1)[-1], len(x), len(x) / 32000.0, pk, M.head_db(x), ref, 100.0 * float((np.abs(x) >= 0.98 * pk).mean())))
        ok &= len(x) == w1[o].get('samples') and 0.2 < float(np.count_nonzero(x)) / 32000.0 < 0.5
    snd = S.Snd('dd', lv['.SND'])
    sc2, _ = lv.scene()
    kt = MG.template_node(sc2, TEMPLATE)
    log('  %s plays %s; slots: %s' % (TEMPLATE, MG.sound_name(snd, MG.sound_of(sc2, kt)), [x.rsplit('/', 1)[-1] for x in MG.sound_slots(snd, MG.sound_of(sc2, kt)) if x]))
    # who else reaches the three records: their wave objects' sound objects
    so = K.snd_sounds(lv['.SND'])
    for o in diff:
        for wo, _s in K.snd_wave_objects(lv['.SND']).get(o, []):
            log('    record %s wave object %#x <- %s' % (w1[o].name.rsplit('/', 1)[-1], wo, so.get(wo)))
    log('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return ok


# ------------------------------------------------------------------ self test
def _stock_part(p, o):
    d = p.u32(p.u32(o, 0x28), 0); nv = p.u32(d, 0)
    return d, nv, bytes(p.chunks[p.u32(d, 4)]), bytes(p.chunks[p.u32(d, 0x18)])


def selftest(log=print):
    import kl_chars as C
    lv = C.Lv('F01')
    p, mat, tex = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT']), T.read_tex(lv['.TEX'])
    sc, _raw = lv.scene()
    import kl_guns
    root = C.person(sc, kl_guns.gun_node(sc, TEMPLATE))[0]
    ok = True
    tot = [0, 0]
    for o in C.objects(p, root):
        d, nv, v, ix = _stock_part(p, o)
        sub = p.u32(o, 0x28)
        # rebuild every piece from its parsed fields
        rv = b''.join(rigid_vertex(struct.unpack_from('<3f', v, 40 * k), v[40 * k + 12:40 * k + 16], struct.unpack_from('<2f', v, 40 * k + 20),
                                   v[40 * k + 28:40 * k + 32], v[40 * k + 32:40 * k + 36], v[40 * k + 16:40 * k + 20], v[40 * k + 36:40 * k + 40])
                      for k in range(nv))
        rv += bytes(-len(rv) % 16)
        n = struct.unpack_from('<H', ix, 2)[0]; ii = struct.unpack_from('<%dH' % n, ix, 4)
        tris = [(ii[k], ii[k + 1], ii[k + 2]) for k in range(0, n - 2, 3)]
        ri = PM.index_chunk(tris, flip=False)
        rd = PM.descriptor(nv, p.u32(d, 4), p.u32(d, 0x18), p.u32(d, 0x14))
        rs = PM.subtab(d)
        ro = rigid_object(p.chunks[o], p.chunks[o][0x0e], p.chunks[o][0x0f], p.u16(o, 0x12), sub)
        same = (rv == v, ri == ix, rd == bytes(p.chunks[d]), rs == bytes(p.chunks[sub]), ro == bytes(p.chunks[o]))
        # how well the COMPUTED tangent frame matches the stock bytes (the writer cannot reproduce the exporter's, so this is a measure)
        nrm = [PM.unpack_dir(v[40 * k + 12:40 * k + 16]) for k in range(nv)]
        pos = [struct.unpack_from('<3f', v, 40 * k) for k in range(nv)]
        uv = [struct.unpack_from('<2f', v, 40 * k + 20) for k in range(nv)]
        plate = PM.Plate(pos, nrm, uv, tris, 'stock')
        cv = vertex_chunk(plate, flip=False)
        ag = lambda off: sum(1 for k in range(nv) if PM._dot(PM.unpack_dir(cv[40 * k + off:40 * k + off + 4]), PM.unpack_dir(v[40 * k + off:40 * k + off + 4])) > 0.7)
        share = PM.outward_share(plate)
        log('  part %d (%4d verts, %4d tris, bone %d, lod %2d, mat %d): vertex/index/descriptor/subtab/object byte-identical %s;'
            ' computed tangent agrees on %d, binormal on %d; outward share of the FILE order %.2f' % (
                o, nv, len(tris), p.u32(o, 0x3c), p.chunks[o][0x0e], p.u16(o, 0x12), same, ag(28), ag(32), share))
        # the hidden box part (material 550) has no real uv layout: only its bytes are held to the test
        ok &= all(same)
        if p.u16(o, 0x12) != 550:
            tot[0] += nv; tot[1] += ag(28) + ag(32)
    log('  computed tangent + binormal agree with the stock bytes on %.1f %% of %d vertices (box part left out)' % (100.0 * tot[1] / (2 * tot[0]), tot[0]))
    ok &= tot[1] > 0.95 * 2 * tot[0]
    # the DXT5 -> DXT1 conversion decodes to the same pixels (on the real PD2 diffuse if it is there, else on random blocks)
    import random
    random.seed(5)
    blocks = [bytes(random.getrandbits(8) for _ in range(16)) for _ in range(500)]
    fixed = dxt5_to_dxt1([b''.join(blocks)])[0]
    same = all(decode_colour(b, True) == decode_colour(fixed[8 * i:8 * i + 8], False) for i, b in enumerate(blocks))
    log('  DXT5 -> DXT1 on 500 random blocks (colour half): %s' % ('identical pixels' if same else 'DIFFERENT'))
    ok &= same
    # the stock flat normal block is in the stock Type 81 normal map's smallest mip
    n = tex.tex[next(nn[3] for s, nn in T.texture_stages(mat.insts[p.u16(C.objects(p, root)[0], 0x12)]) if s == 'mapNormal')].entry
    log('  flat normal block %s the stock Type 81 normal map record' % ('is in' if FLAT_NORMAL_BLOCK in bytes(n) else 'is NOT in'))
    ok &= FLAT_NORMAL_BLOCK in bytes(n)
    f = PM.dds_mips(flat_normal_dds()); g = PM.dds_mips(grey_spec_dds())
    log('  flat normal DDS %s %dx%d x %d mips, grey spec DDS %s %dx%d x %d mips' % (f[0], f[1], f[2], len(f[3]), g[0], g[1], g[2], len(g[3])))
    log('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'selftest':
        sys.exit(0 if selftest() else 1)
    if a and a[0] == 'verify' and len(a) > 1:
        sys.exit(0 if verify(a[1]) else 1)
    if a and a[0] in ('build', 'model') and len(a) > 1:
        r = build(a[1], with_sound=a[0] == 'build')
        print(json.dumps(r['md5'], indent=1))
        sys.exit(0)
    print(__doc__)
