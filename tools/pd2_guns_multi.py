#!/usr/bin/env python3
"""
pd2_guns_multi.py - more Payday 2 guns on the duplicate variant items of shop page II (2026-11-05, offline, nothing installed).
Extends pd2_gun.py (the AKM on Rifle_Type81 / item 33) to other host templates of the KLExpansion Dead Men maps.

    python tools/pd2_guns_multi.py fit                 print the per-gun fit (no level written)
    python tools/pd2_guns_multi.py build DM02 [DM01 ...] [--out <dir>]    stage the maps (default out <work>/build/pd2guns_1105)
    python tools/pd2_guns_multi.py all                 every map in MAPS
    python tools/pd2_guns_multi.py verify <out>        re-read every staged map
    python tools/pd2_guns_multi.py pics                silhouettes -> <out>/pics/item_NN.png
    build / all / pics accept  --only KEY,KEY  (bake or draw just those SPECS keys; tools/pd2_guns_layer.py uses it for the 1106b layer)

WHAT IS DIFFERENT FROM pd2_gun.build_model
  * only the template's OWN Ground node is retargeted (kl_guns.gun_node: exactly one per template). The AKM code moved every
    node that used the old root, which is wrong on the shared roots (40-44 share root 2823, 45/46/48 the Minimi root);
  * the fit is made against the HOST's surface (its own muzzle, its own 'l hand attacher'), not the Type 81's;
  * the magazine is split off only when the host has a bone 3 'w_bone_clip' part to take the reload from; otherwise one part.
  * the host's other parts (slide / sight / bipod / LOD copies) are dropped, the hidden 'box' part (lod 16) stays.
GUESS (never seen in the hands): the pose of a rifle model held with a machine-gun hold (items 42, 43, 44), the muzzle weight of
the fit (MUZZLE_W), the sound (unchanged: the host's own).
"""
import hashlib, json, math, os, re, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G, kl_texmat as T, kl_pd2mask as PM
import pd2_gun as P

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPROOT = os.path.join(DD, 'KLExpansion', 'Maps')
CHAIN = r'C:\kl_build_1024\lastcall_chain_1105\stage'          # DM05A_chain is baked on this stage's zip
DOORS = r'C:\kl_build_1024\lastcall_chain_doors_1106\stage'    # DM05A_doors is baked on this stage's zip (+ its KLGuns/KLJoin)
GLASS = r'C:\kl_build_1024\lastcall_glass_1106\stage'          # DM05A_glass is baked on this stage's zip (chain + .sgd glass connectivity)
MAPS = ['DM01', 'DM01B', 'DM02', 'DM03', 'DM03A', 'DM05A', 'DM06', 'DM06B', 'DM07', 'DM09', 'DM11B']
TAG = '1105pd2guns'
MUZZLE_W = 0.15            # GUESS: weight of |PD2 muzzle x - host muzzle x| in the fit (the AKM fit used 0.3; the hands decide, not the muzzle)

M79_PARTS = [
    dict(model='wpn_third_gre_m79_barrel.model', meshes=['g_barrel'], tex='m79_third_barrel_df.texture', mat='barrel'),
    dict(model='wpn_third_gre_m79_barrelcatch.model', meshes=['g_barrelcatch'], tex='m79_third_barrelcatch_df.texture', mat='catch'),
    dict(model='wpn_third_gre_m79_sight_up.model', meshes=['g_sight'], tex='m79_third_sight_df.texture', mat='sight'),
    dict(model='wpn_third_gre_m79_stock.model', meshes=['g_stock'], tex='m79_third_stock_df.texture', mat='stock')]
# item -> (host template, PD2 unit dir under .../src/units, model/mesh/texture, short name for materials, shop name)
SPECS = [
    dict(item=35, template='Rifle_Type88_L09_NPC', unit='pd2_dlc_chico/weapons/wpn_npc_sg417', mesh='g_body', tex='wpn_npc_sg417_df.texture',
         key='SG417', name='PD2 SG 417', kind='marksman rifle'),
    dict(item=38, template='Rifle_Type95_L09_NPC', unit='payday2/weapons/wpn_npc_g36', mesh='g_body', tex='g36_df.texture',
         key='G36', name='PD2 G36', kind='assault rifle'),
    dict(item=41, template='MG_GP_Type88_L09_NPC', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK', name='PD2 RPK', kind='light machine gun'),
    dict(item=44, template='MG_GP_Type88_L10_Heli', unit='payday2/weapons/wpn_npc_scar_murkywater', mesh='g_body_lod0', tex='mk17_df.texture',
         key='MK17', name='PD2 MK17', kind='battle rifle'),
    # ---- batch 2 (2026-11-06): the same PD2 RPK on the other Type 88 MG items (same hold, same model root 2823 as item 41, so the fit is
    # near item 41's but fitted per item, see fits.json: shifts 40=(16.0,0.75) 41=42=(15.75,1.0) 43=(15.5,1.0); cost 1.2 - 1.3, muzzle 95.7 - 96.2 vs host 96.1). Own key per item = own texture / material, own Ground node retargeted.
    dict(item=40, template='MG_GP_Type88', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK40', name='PD2 RPK', kind='light machine gun'),
    dict(item=42, template='MG_GP_Type88_L09_Heli', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK42', name='PD2 RPK', kind='light machine gun'),
    dict(item=43, template='MG_GP_Type88_L09_Heli_Player', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK43', name='PD2 RPK', kind='light machine gun'),
    # ---- batch 3 (2026-11-06)
    dict(item=62, template='HG_M-77B_Human_Shield', unit='payday2/weapons/wpn_npc_c45', mesh='g_body', tex='pistol_df.texture',
         key='C45', name='PD2 Chimano 88', kind='pistol'),
    # ---- batch 4 (2026-11-06): both items <- PD2 HRL-7 body (wpn_third_rpg7_body.model g_body, 1304 tris, third_body_df). Hosts RPG_7V / RPG_7V_Hind each
    # have their OWN Ground node but share root 4959 (parts 7 / 7 / 248, no bone-3 clip), so body only: the rocket (g_rocket, own texture, 2nd material) is not
    # baked in (needs an atlas) and there is no clip part for the reload to take. fit DM02: cost 1.95 / 1.94, shift (7.0,-0.75) / (6.25,-0.5), muzzle 27.9 / 27.1 vs host 26.6, butt -67 vs -78.
    dict(item=50, template='RPG_7V', unit='pd2_dlc_overkill_pack/weapons/wpn_third_rpg7_pts', model='wpn_third_rpg7_body.model', mesh='g_body',
         tex='third_body_df.texture', key='HRL50', name='PD2 HRL-7', kind='rocket launcher'),
    dict(item=51, template='RPG_7V_Hind', unit='pd2_dlc_overkill_pack/weapons/wpn_third_rpg7_pts', model='wpn_third_rpg7_body.model', mesh='g_body',
         tex='third_body_df.texture', key='HRL51', name='PD2 HRL-7 HIND', kind='rocket launcher'),
    # ---- batch 5 (2026-11-06): item 49 <- PD2 R700 from the third-person parts unit wpn_fps_snp_r700_pts (the fps unit's model is a bare locator; wpn_fps_snp_r700_npc.unit
    # points at it). 6 materials: receiver (body_standard g_rec + g_release), bolt (g_bolt / g_handle / g_pin), long barrel (b_standard g_b), magazine (m_standard g_m,
    # the part flagged mag), standard stock (s_standard g_s), scope mount (o_rail g_rail). No scope exists in the unit; the suppressor, the b_short/b_medium barrels,
    # the military / tactical stocks and the fl_rail are not used. See pd2_parts_of.
    dict(item=49, template='Sn_Rem700', unit='pd2_dlc_atw/weapons/wpn_fps_snp_r700_pts', key='R700', name='PD2 R700', kind='sniper rifle', parts=[
        dict(model='wpn_third_snp_r700_body_standard.model', meshes=['g_rec', 'g_release'], tex='third_body_df.texture', mat='body'),
        dict(model='wpn_third_snp_r700_bolt_standard.model', meshes=['g_bolt', 'g_handle', 'g_pin'], tex='third_bolt_df.texture', mat='bolt'),
        dict(model='wpn_third_snp_r700_b_standard.model', meshes=['g_b'], tex='third_barrel_df.texture', mat='barrel'),
        dict(model='wpn_third_snp_r700_m_standard.model', meshes=['g_m'], tex='third_mag_df.texture', mat='mag', mag=True),
        dict(model='wpn_third_snp_r700_s_standard.model', meshes=['g_s'], tex='third_stock_standard_df.texture', mat='stock'),
        dict(model='wpn_third_snp_r700_o_rail.model', meshes=['g_rail'], tex='third_mount_df.texture', mat='mount')]),
    # ---- batch 6 (2026-11-06): items 52 / 53 / 54 <- PD2 GL40 (the M79, wpn_fps_gre_m79_pts third-person parts): barrel, barrelcatch, sight_up, long stock; barrel_short /
    # stock_short / grenade left out. Hosts Launcher_HK69A1_01 / ...TearGas / ...Flare share root 5001 (see build_level: detail-190 far copy, GUESS), each own Ground node.
    dict(item=52, template='Launcher_HK69A1_01', unit='pd2_dlc_gage_assault/weapons/wpn_fps_gre_m79_pts', key='GL40', name='PD2 GL40', kind='grenade launcher', parts=M79_PARTS),
    dict(item=53, template='Launcher_HK69A1_01TearGas', unit='pd2_dlc_gage_assault/weapons/wpn_fps_gre_m79_pts', key='GL40GAS', name='PD2 GL40 GAS', kind='grenade launcher', parts=M79_PARTS),
    dict(item=54, template='Launcher_HK69A1_01Flare', unit='pd2_dlc_gage_assault/weapons/wpn_fps_gre_m79_pts', key='GL40FLR', name='PD2 GL40 FLARE', kind='grenade launcher', parts=M79_PARTS),
    # ---- batch 7 (2026-11-06): items 45 / 46 / 47 / 48 (the four Minimi items, names KSP*) <- PD2 RPK (wpn_npc_rpk, 'g_body'), same gun as items 40 - 43. Hosts Mg_Minimi_SPW_L09_Heli_Player /
    # _L10_Heli / Mg_Minimi_SPW / Mg_Minimi_SPW_Heli: roots 2739 (45 / 46 / 48 share it) and 4626 (47), each template its OWN Ground node. Fit on DM02 (frozen in fits.json): see the
    # layer notes in re/pd2_guns.md. Earlier survey: the RPK is the PD2 LMG that fits the Minimi holds (cost 1.8 - 2.0, muzzle 82.7 - 83.2 vs host 80.4 - 81.9); the M249 does not (3.5+).
    dict(item=45, template='Mg_Minimi_SPW_L09_Heli_Player', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK45', name='PD2 RPK', kind='light machine gun'),
    dict(item=46, template='Mg_Minimi_SPW_L10_Heli', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK46', name='PD2 RPK', kind='light machine gun'),
    dict(item=47, template='Mg_Minimi_SPW', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK47', name='PD2 RPK', kind='light machine gun'),
    dict(item=48, template='Mg_Minimi_SPW_Heli', unit='pd2_dlc_mad/weapons/wpn_npc_rpk', mesh='g_body', tex='wpn_npc_rpk_df.texture',
         key='RPK48', name='PD2 RPK', kind='light machine gun'),
]
# Tried and dropped (fit on the MG hold leaves the stock 4 - 5 cm IN FRONT of the right hand): item 42 <- PD2 M4 (cost 3.30, butt +5.0),
# item 43 <- PD2 AKMSU (cost 3.99, butt +3.8). A short rifle model does not suit the long MG hold; a PD2 LMG (M249: 9 materials) would.
# Batch 2 survey (2026-11-06, fit_one on DM02 hosts, true size): PD2 M249 (the KSP) on the Type 88 hold cost 3.53 / 3.48 (muzzle 83 vs 96, butt -5.9,
# as bad as the dropped M4) and on the Minimi holds 3.77 / 3.46 (scaled x1.2 it reaches 1.95 - 2.39 but is then a 130 cm gun: rejected, and it needs
# a 9-material writer). So items 45 - 48 (Minimi holds, names KSP*) stay on their Dead Men model. PD2 RPK on the Minimi holds: cost 1.99 / 1.89,
# muzzle 83.2 / 82.7 (host 81.9 / 80.4) but there is no free RPK name left for them, so also not used.
# Batch 3 (2026-11-06, fit on DM02): item 62 <- PD2 C45 (Chimano 88) accepted: cost 1.17 (1.11 with another host sample), shift (10.0, 4.0), muzzle 28.2 vs
# host 25.6, butt 1.5 vs host 2.9, 148 tris, no magazine split. Item 63 <- PD2 Beretta 92 (Bernetti 9) dropped: cost 2.84 - 2.86, shift at the grid edge (-6),
# muzzle 31.9 vs 28.5, butt -11.5; the PD2 mesh is 43.5 cm long (-5.5 .. 37.9, a long barrel / suppressor) against the 25.9 cm host.


def work():
    import kl_port_check
    return kl_port_check.workdir()


def unit_dir(spec):
    return os.path.join(work(), 'pd2', 'guns', 'src', 'units', spec['unit'].replace('/', os.sep))


def _mesh_of(model, name, scale, shift, deg):
    """One named mesh object of a PD2 model in KL space: axis map, turn about z, scale, shift. -> (pos, nrm, uv, tris)."""
    import pd2_model
    obj = next((o for o in model.mesh_objects() if o.name == name), None)
    if obj is None:
        raise ValueError('no mesh object %s (have %s)' % (name, [o.name for o in model.mesh_objects()]))
    m = model.world_mesh(obj)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    turn = lambda v: (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])
    kl = lambda v: tuple(a * scale + b for a, b in zip(turn((v[1], v[2], -v[0])), shift))
    pos = [kl(q) for q in m['pos']]
    nrm = [PM._norm(turn((n[1], n[2], -n[0]))) for n in m['nrm']]
    uv = [(u, 1.0 + v) for u, v in m['uv']]
    tris = [(a, c_, b) for a, b, c_ in (tuple(t) for t in m['tris'])]
    return pos, nrm, uv, tris


def _merge(meshes, name):
    """Several (pos, nrm, uv, tris) -> one Plate (vertex lists appended, indices offset)."""
    pos, nrm, uv, tris = [], [], [], []
    for p_, n_, u_, t_ in meshes:
        o = len(pos)
        pos += p_; nrm += n_; uv += u_; tris += [(a + o, b + o, c + o) for a, b, c in t_]
    return PM.Plate(pos, nrm, uv, tris, name)


def pd2_plate_of(spec, scale=1.0, shift=(0.0, 0.0, 0.0), deg=P.TURN_DEG):
    """pd2_gun.pd2_plate for any wpn_npc_* unit: axis map, turn about z, scale, shift. -> (Plate, DDS diffuse bytes).
    A spec with 'parts' (batch 5, see pd2_parts_of) gives the WHOLE gun as one Plate (the fit, silhouettes, previews use it) and the first part's DDS."""
    import pd2_model
    if spec.get('parts'):
        groups = pd2_parts_of(spec, scale, shift, deg)
        return _merge([(g['plate'].pos, g['plate'].nrm, g['plate'].uv, g['plate'].tris) for g in groups], 'pd2_' + spec['key'].lower()), groups[0]['dds']
    base = unit_dir(spec)
    # batch 4: spec['model'] names the .model file when it is not <unit dir name>.model (wpn_third_rpg7_pts holds wpn_third_rpg7_body.model)
    model = pd2_model.Model(os.path.join(base, spec.get('model') or os.path.basename(base) + '.model'))
    pos, nrm, uv, tris = _mesh_of(model, spec['mesh'], scale, shift, deg)
    return PM.Plate(pos, nrm, uv, tris, 'pd2_' + spec['key'].lower()), open(os.path.join(base, spec['tex']), 'rb').read()


def pd2_parts_of(spec, scale=1.0, shift=(0.0, 0.0, 0.0), deg=P.TURN_DEG):
    """Batch 5: N parts, M materials. spec['parts'] = [dict(model=<.model file in the unit dir>, meshes=[mesh names], tex=<diffuse .texture>, mat=<short
    material name>, mag=True on the magazine part)]. Parts with the same 'mat' become ONE Plate (one object per material).
    -> [dict(mat, plate, dds, mag)] in first-use order. The parts of an assembled PD2 gun share one origin (the R700's receiver, barrel and stock
    ranges join without a transform), so no per-part offset is applied. GUESS: that holds for every part model of a *_pts unit."""
    import pd2_model
    base = unit_dir(spec)
    order, by = [], {}
    for pt in spec['parts']:
        model = pd2_model.Model(os.path.join(base, pt['model']))
        g = by.get(pt['mat'])
        if g is None:
            g = by[pt['mat']] = dict(mat=pt['mat'], meshes=[], tex=pt['tex'], mag=bool(pt.get('mag')))
            order.append(g)
        elif g['tex'] != pt['tex']:
            raise ValueError('%s: material %s has two diffuse textures' % (spec['key'], pt['mat']))
        for nm in pt['meshes']:
            g['meshes'].append(_mesh_of(model, nm, scale, shift, deg))
    return [dict(mat=g['mat'], plate=_merge(g['meshes'], 'pd2_%s_%s' % (spec['key'].lower(), g['mat'])), dds=open(os.path.join(base, g['tex']), 'rb').read(), mag=g['mag'])
            for g in order]


# ------------------------------------------------------------------ fit against the host
def _host(p, root, C, MG, V, rng, S):
    """(points of the host's holding surface, l hand attacher x, muzzle x). The magazine and the hidden box are left out."""
    import numpy as np
    sh = MG.shape(p, root)
    parts = [o for o in C.objects(p, root) if p.u32(o, 0x3c) in (1, 2, 4) and p.chunks[o][0x0e] != 16]
    pts = np.vstack([S(*V.part_mesh(p, o), rng) for o in parts])
    # GUESS (batch 3): a one-handed pistol has no 'l hand attacher'; its w_bone_frame x (12.8) stands in for the left-hand reference x
    lh = (sh['bones'].get('l hand attacher') or sh['bones']['w_bone_frame'])[9:12]
    return pts, lh[0], float(pts[:, 0].max())


def fit_one(spec, host, log=print):
    """Grid search of the shift (x, y) at scale 1.0. Cost as pd2_gun_fit: grip gap in GRIP_ZONE both ways (trimmed) + median
    difference of the lowest surface in 2 cm bins around the left hand + MUZZLE_W x muzzle distance. -> (shift, report)."""
    import numpy as np
    import pd2_gun_fit as F, kl_map_guns as MG
    pts, lhx, mux = host
    rng = np.random.default_rng(1)
    plate, _df = pd2_plate_of(spec)
    A1 = F.sample(plate.pos, plate.tris, rng, dens=0.5)
    if len(A1) > 6000:
        A1 = A1[rng.choice(len(A1), 6000, replace=False)]
    hp = pts if len(pts) <= 6000 else pts[rng.choice(len(pts), 6000, replace=False)]
    bins = np.arange(round(lhx) - 8, round(lhx) + 8, 2.0)
    under = lambda Pt: np.array([Pt[(Pt[:, 0] >= b) & (Pt[:, 0] < b + 2), 1].min() if ((Pt[:, 0] >= b) & (Pt[:, 0] < b + 2)).any() else np.nan for b in bins])
    hz, hu = hp[F._zone(hp, 2)], under(hp)

    def cost(tx, ty):
        A = A1 + np.array([tx, ty, 0.0])
        az = A[F._zone(A)]
        if len(az) < 10:
            return 1e9
        d = under(A) - hu
        d = d[~np.isnan(d)]
        if len(d) < 4:
            return 1e9
        return F._trim(F._nn(az, hz)) + F._trim(F._nn(hz, A[F._zone(A, 2)])) + float(np.median(np.abs(d))) + MUZZLE_W * abs(A[:, 0].max() - mux)
    best = min((cost(a, b), a, b) for a in np.arange(-5, 30, 1.0) for b in np.arange(-6, 10, 1.0))
    fine = min((cost(a, b), a, b) for a in np.arange(best[1] - 1, best[1] + 1.01, 0.25) for b in np.arange(best[2] - 1, best[2] + 1.01, 0.25))
    shift = (round(fine[1], 2), round(fine[2], 2), 0.65)
    A = A1 + np.array([shift[0], shift[1], 0.0])
    rep = dict(cost=round(float(fine[0]), 3), shift=list(shift), muzzle=round(float(A[:, 0].max()), 1), host_muzzle=round(mux, 1),
               butt=round(float(A[:, 0].min()), 1), l_hand_x=round(float(lhx), 1), pd2_box=[[round(float(x), 1) for x in A.min(0)], [round(float(x), 1) for x in A.max(0)]])
    log('  fit %-6s shift (%.2f, %.2f) cost %.2f muzzle %.1f (host %.1f) butt %.1f' % (spec['key'], shift[0], shift[1], fine[0], rep['muzzle'], mux, rep['butt']))
    return shift, rep


# ------------------------------------------------------------------ into the level
def build_level(lv, specs=SPECS, log=print, fits=None):
    """lv (kl_chars.Lv, edited in place): each spec's template gets a new model root (PD2 body, magazine when it can be split).
    -> {key: report}."""
    import numpy as np
    import kl_chars as C, kl_guns, kl_gms, kl_octree as O, kl_map_guns as MG, pd2_gun_preview as V, pd2_gun_fit as F
    sc, raw = lv.scene(); raw = bytearray(raw)
    p, mat, tex = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT']), T.read_tex(lv['.TEX'])
    oct_s = O.Oct.parse(lv['.oct'])
    reports = {}
    rng = np.random.default_rng(1)
    for spec in specs:
        k = kl_guns.gun_node(sc, spec['template'])
        old, var, _aset = C.person(sc, k)
        objs = C.objects(p, old)
        nvs = {o: p.u32(p.u32(p.u32(o, 0x28), 0), 0) for o in objs}
        hidden = [o for o in objs if p.chunks[o][0x0e] == 16]
        lowd, body_lod, mag_lod = [], 15, 15
        if not hidden:
            # GUESS (batch 3): a pistol root (HG_*) has no hidden 'box' part (detail 16): body / slide / magazine carry detail 7 and one
            # small type-1 object carries detail 24 (35 verts for Chimano's 596 = the low-detail copy). The new body takes 7|24 and
            # the stock low-detail copy is dropped, so the PD2 gun is drawn at every distance.
            lowd = [o for o in objs if p.u32(o, 0x3c) == 1 and p.chunks[o][0x0e] == 24]
            far = [o for o in objs if p.u32(o, 0x3c) == 1 and p.chunks[o][0x0e] == 248]
            if not lowd and len(far) == 1:
                # GUESS (batch 4): a rocket launcher root (RPG_7V / RPG_7V_Hind: 2 type-1 parts detail 7 + one detail 248) has no detail-16
                # box and no 24 copy; the detail-248 part (89 verts) is read as the far-LOD copy. The new body takes 7|248 (= 255) and the
                # stock far copy and the second near part (127 verts, the rocket or the sight?) are dropped; there is no bone-3 clip part.
                lowd = far
            if not lowd:
                far28 = [o for o in objs if p.u32(o, 0x3c) == 1 and p.chunks[o][0x0e] == 28]
                if len(far28) == 1:
                    # GUESS (batch 5): a sniper root (Sn_Rem700: type-1 detail 3 / 28 / 3 / 12 plus one type-4 detail 3 on bone w_bone_slide, no detail 16 / 24 / 248)
                    # is read as: 28 = far copy of the receiver+barrel+stock, the detail-3 type-1 part whose x extent matches it = the body, the other
                    # type-1 pair (detail 3 + its far copy 12, x 12.5 - 50) = the scope, kept as it is, the type-4 part = the bolt slide, dropped (the PD2 bolt is in the
                    # mesh). The new body takes 7|28 = 31 (every level), like the pistol.
                    lowd = far28
            if not lowd:
                far190 = [o for o in objs if p.u32(o, 0x3c) == 1 and p.chunks[o][0x0e] == 190]
                if len(far190) == 1:
                    # GUESS (batch 6): a grenade launcher root (Launcher_HK69A1_01 / ...TearGas / ...Flare, shared root: type-1 detail 1 body on the near
                    # side, type-3 detail 1 barrel on w_bone_pipe, type-1 detail 190 and type-2 detail 3 hammer; no detail 16 / 24 / 248 / 28) is read as:
                    # the detail-190 type-1 part = the far copy, the detail-1 type-1 part = the body. The new body objects take 1|190 = 191 (the whole
                    # M79 is in body objects, multi-part path); the host's type-3 barrel and type-2 hammer are dropped from the root (no clip to reload).
                    lowd = far190
            if not lowd:
                far62 = [o for o in objs if p.u32(o, 0x3c) == 1 and p.chunks[o][0x0e] == 62]
                if len(far62) == 2:
                    # GUESS (batch 7): a Minimi root (Mg_Minimi_SPW*: type-1 detail 1 body 2114 verts + type-1 detail 1 small part 34 verts (x 17 - 28, own material,
                    # a sight or the ammo box?) and their detail-62 copies 464 / 28 verts; no detail 16 / 24 / 248 / 28 / 190, no bone-3 clip) is read as: the larger
                    # detail-62 part = the far copy of the body, the larger detail-1 part = the body. The new body takes 62|7 = 63 (every distance); the small part
                    # and its far copy are dropped (the PD2 RPK carries its own bipod / sight in the mesh).
                    lowd = [max(far62, key=lambda o: nvs[o])]
            if len(lowd) != 1:
                raise ValueError('%s: unexpected parts %s' % (spec['template'], [(o, p.u32(o, 0x3c), p.chunks[o][0x0e]) for o in objs]))
            body_lod = mag_lod = (p.chunks[lowd[0]][0x0e] | (1 if p.chunks[lowd[0]][0x0e] == 190 else 7))   # 31 on a pistol, 255 on a launcher, 191 on the HK69 (GUESS)
        cands = [o for o in objs if p.u32(o, 0x3c) == 1 and p.chunks[o][0x0e] not in (16, 24, 248) and not (lowd and o == lowd[0] and p.chunks[o][0x0e] == 190)]
        if (len(hidden) != 1 and not lowd) or not cands or var != 0:
            raise ValueError('%s: unexpected parts %s' % (spec['template'], [(o, p.u32(o, 0x3c), p.chunks[o][0x0e]) for o in objs]))
        body = max(cands, key=lambda o: nvs[o])
        keep = []
        if not hidden and lowd and lowd[0] in cands and p.chunks[lowd[0]][0x0e] == 28:
            ext = lambda o: (lambda a: (a[:, 0].min(), a[:, 0].max()))(np.array(V.part_mesh(p, o)[0]))
            fe = ext(lowd[0])
            body = min((o for o in cands if p.chunks[o][0x0e] == 3), key=lambda o: sum(abs(x - y) for x, y in zip(ext(o), fe)))
            keep = [o for o in cands if o not in (body, lowd[0])]          # the scope pair (GUESS above)
        mags = [o for o in objs if p.u32(o, 0x3c) == 3 and p.chunks[o][0x0e] == (15 if hidden else 7)]
        cached = bool((fits or {}).get(spec['key']))
        shift, frep = (fits or {}).get(spec['key']) or fit_one(spec, _host(p, old, C, MG, V, rng, F.sample))
        plate, df_dds = pd2_plate_of(spec, 1.0, shift)
        share = PM.outward_share(plate)
        if share < 0.95:
            raise ValueError('%s: only %.1f %% of the PD2 triangles face outward' % (spec['key'], 100 * share))
        whole = plate
        src_slot = p.u16(body, 0x12)
        stage = {s: n[3] for s, n in T.texture_stages(mat.insts[src_slot])}
        grp = lambda st: tex.tex[stage[st]].group if st in stage and stage[st] in tex.tex else tex.tex[stage['mapDiffuse']].group
        if spec.get('parts'):
            # batch 5: N parts / M materials = one rigid object per material (each a copy of the host body object, its own material slot,
            # lod = body_lod); the part flagged mag takes the magazine object's place when the host has one (the reload hides it), else it is a
            # body part. Normal and specular maps are one flat pair shared by all the spec's materials.
            groups = pd2_parts_of(spec, 1.0, shift)
            key = spec['key']; magp = None; parts = []; slots = []; dfs = []
            fl_nm = fl_sp = None
            for g in groups:
                fourcc, w, h, mips = PM.dds_mips(g['dds'])
                if fourcc == b'DXT5':
                    mips, fourcc = P.dxt5_to_dxt1(mips), b'DXT1'
                nmk = '%s_%s' % (key, g['mat'])
                df = PM.add_texture(tex, 'tex:Weapons/PD2_%s#Diffuse_a' % nmk, P.dds_bytes(fourcc, w, h, mips), group=grp('mapDiffuse'))
                if fl_nm is None:
                    fl_nm = PM.add_texture(tex, 'tex:Weapons/PD2_%s#Normal_a' % key, P.flat_normal_dds(), normal_map=True, group=grp('mapNormal'))
                    fl_sp = PM.add_texture(tex, 'tex:Weapons/PD2_%s#Specular_a' % key, P.grey_spec_dds(), group=grp('mapSpecularMask'))
                gslot = P.clone_material(mat, src_slot, 'Weapons/W_PD2_%s_01' % nmk, df, fl_nm, fl_sp)
                gp = g['plate']
                v = G.new_chunk(p, P.vertex_chunk(gp, flip=True)); i = G.new_chunk(p, PM.index_chunk(gp.tris, flip=True))
                d = G.new_chunk(p, PM.descriptor(len(gp.pos), v, i, 0)); sub = G.new_chunk(p, PM.subtab(d))
                if g['mag'] and mags and magp is None:
                    magp = gp; tpl = mags[0]; lod_ = mag_lod
                else:
                    tpl = body; lod_ = body_lod
                parts.append(G.new_chunk(p, P.rigid_object(p.chunks[tpl], lod_, p.chunks[tpl][0x0f], gslot, sub), p.refs[tpl]))
                slots.append(gslot); dfs.append(df)
            df, nm, sp, slot = dfs, fl_nm, fl_sp, slots
            plate = whole
            new_body = parts[0]
        else:
            whole, magp = plate, None
            if mags:
                try:
                    plate, magp = P.split_magazine(whole)
                except ValueError as e:
                    log('  %s: no magazine split (%s)' % (spec['key'], e))
                    plate = whole
            fourcc, w, h, mips = PM.dds_mips(df_dds)
            if fourcc == b'DXT5':
                mips, fourcc = P.dxt5_to_dxt1(mips), b'DXT1'
            key = spec['key']
            df = PM.add_texture(tex, 'tex:Weapons/PD2_%s#Diffuse_a' % key, P.dds_bytes(fourcc, w, h, mips), group=grp('mapDiffuse'))
            nm = PM.add_texture(tex, 'tex:Weapons/PD2_%s#Normal_a' % key, P.flat_normal_dds(), normal_map=True, group=grp('mapNormal'))
            sp = PM.add_texture(tex, 'tex:Weapons/PD2_%s#Specular_a' % key, P.grey_spec_dds(), group=grp('mapSpecularMask'))
            slot = P.clone_material(mat, src_slot, 'Weapons/W_PD2_%s_01' % key, df, nm, sp)
            v = G.new_chunk(p, P.vertex_chunk(plate, flip=True)); i = G.new_chunk(p, PM.index_chunk(plate.tris, flip=True))
            d = G.new_chunk(p, PM.descriptor(len(plate.pos), v, i, 0)); sub = G.new_chunk(p, PM.subtab(d))
            new_body = G.new_chunk(p, P.rigid_object(p.chunks[body], body_lod, p.chunks[body][0x0f], slot, sub), p.refs[body])
            parts = [new_body]
            if magp is not None:
                mv = G.new_chunk(p, P.vertex_chunk(magp, flip=True)); mi = G.new_chunk(p, PM.index_chunk(magp.tris, flip=True))
                md = G.new_chunk(p, PM.descriptor(len(magp.pos), mv, mi, 0)); msub = G.new_chunk(p, PM.subtab(md))
                parts.append(G.new_chunk(p, P.rigid_object(p.chunks[mags[0]], mag_lod, p.chunks[mags[0]][0x0f], slot, msub), p.refs[mags[0]]))
        root = C._new(p, p.chunks[old]); p.refs[root] = 1
        C._set_objects(p, root, parts + keep + hidden)
        PM.widen_root(p, root, whole.box())
        ref = p.u32(old, 0x1c)
        if ref:
            refs0 = oct_s.record_refs(); rec_of = {x: n for n, x in enumerate(refs0)}
            r = oct_s.records[rec_of[ref]]
            if r.tree.items:
                raise ValueError('%s: the .oct record of the root is not an empty tree' % spec['template'])
            oct_s.records.append(O.Record(r.vtable, r.pointer, O.Tree(r.tree.origin, r.tree.scale, [list(x) for x in r.tree.nodes], [], r.tree.fill)))
            refs1 = oct_s.record_refs()
            if refs1[:len(refs0)] != refs0:
                raise ValueError('appending an .oct record moved the base level records')
            p.chunks[root] = C._put(p.chunks[root], 0x1c, '<I', refs1[len(refs0)])
        models = C.gms_models(raw)
        kl_guns._retarget(sc, raw, models, k, root)               # ONLY this template's Ground node (shared roots stay)
        box = whole.box()
        reports[key] = dict(item=spec['item'], template=spec['template'], stock_root=old, root=root, body_object=new_body, parts=len(parts),
                            body_vertices=len(plate.pos), body_triangles=len(plate.tris), magazine=bool(magp), outward_share=round(share, 4),
                            material_slot=slot, textures=[df, nm, sp], shift=list(shift), fit=None if cached else frep,
                            box=[[round(x, 2) for x in box[0]], [round(x, 2) for x in box[1]]])
        log('  item %d %s -> %s: root %d -> %d, %d verts / %d tris%s, material %s' % (
            spec['item'], spec['template'], key, old, root, len(plate.pos), len(plate.tris), ' + magazine' if magp else '', slot))
    prm = G.write(p)
    mat.refs = T.material_refs(prm)
    lv['.prm'], lv['.MAT'], lv['.TEX'], lv['.oct'] = prm, T.write_mat(mat), T.write_tex(tex), oct_s.pack()
    lv['.gms'], lv['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    return reports, len(G.read(prm, 'dd').chunks)


def stage_map(name, out, fits=None, log=print, src=None, dirname=None, only=None):
    """src: another folder to start from (default the live map folder), dirname: the staged folder name (default the map name),
    only: bake just these SPECS keys (a later layer on a live zip that already holds the earlier specs)."""
    import kl_chars as C
    fp = os.path.join(out, 'fits.json')
    if fits is None and os.path.isfile(fp):
        fits = {k: (tuple(v[0]), v[1]) for k, v in json.load(open(fp)).items()}
    src = src or os.path.join(MAPROOT, name)
    lv = C.Lv(src); lv.beside, lv.side = {}, {}
    slot = lv.name
    old_n = len(G.read(lv['.prm'], 'dd').chunks)
    t0 = time.time()
    reps, new_n = build_level(lv, specs=[s for s in SPECS if only is None or s['key'] in only], fits=fits, log=log)
    d = os.path.join(out, dirname or name)
    new_fits = {k: [g['shift'], g['fit']] for k, g in reps.items() if g['fit']}
    if new_fits:          # first map of a stage, or keys a fits.json made earlier does not hold yet (batch 2): the later maps reuse them
        os.makedirs(out, exist_ok=True)
        old = json.load(open(fp)) if os.path.isfile(fp) else {}
        old.update({k: v for k, v in new_fits.items() if k not in old})
        json.dump(old, open(fp, 'w'), indent=1)
    lv.write(d, slot)
    ini = {}
    for f in sorted(os.listdir(src)):
        if f.lower().endswith('.ini'):
            txt = open(os.path.join(src, f), encoding='latin-1', newline='').read()
            new, n = re.subn(r'(?m)^(Entries\s*=\s*)%d(\s*)$' % old_n, lambda m: m.group(1) + str(new_n) + m.group(2), txt)
            if n:
                open(os.path.join(d, f), 'w', encoding='latin-1', newline='').write(new)
                ini[f] = n
    zp = os.path.join(d, slot + '_Main.zip')
    rep = dict(map=name, slot=slot, chunks_before=old_n, chunks_after=new_n, ini_entries=ini, guns=reps,
               md5={os.path.basename(zp): hashlib.md5(open(zp, 'rb').read()).hexdigest(), **{f: hashlib.md5(open(os.path.join(d, f), 'rb').read()).hexdigest() for f in ini}},
               live_md5={f: hashlib.md5(open(os.path.join(src, f), 'rb').read()).hexdigest() for f in [slot + '_Main.zip'] + list(ini)},
               seconds=round(time.time() - t0, 1))
    json.dump(rep, open(os.path.join(d, 'report.json'), 'w'), indent=1)
    log('%s: %s chunks %d -> %d, ini %s, %.0f s' % (name, slot, old_n, new_n, ini, rep['seconds']))
    return rep


# ------------------------------------------------------------------ the HUD / shop pictures
def silhouette(spec, size=128, ss=4, px_per_cm=1.09):
    """The gun as a white HUD silhouette: (size, size, 4) uint8, RGB 255, alpha = side view (no turn), muzzle right, left aligned at
    x 0, vertically centred. 1.09 px/cm is the stock Type 81 picture's 103 px for its 95 cm (GUESS that all pictures share it)."""
    import numpy as np
    from PIL import Image, ImageDraw
    plate, _df = pd2_plate_of(spec, 1.0, (0.0, 0.0, 0.0), 0.0)
    pos = np.array(plate.pos)
    x0, x1 = pos[:, 0].min(), pos[:, 0].max()
    s = min(px_per_cm, (size - 2) / (x1 - x0)) * ss
    cy = (pos[:, 1].min() + pos[:, 1].max()) / 2
    im = Image.new('L', (size * ss, size * ss), 0); d = ImageDraw.Draw(im)
    px = lambda q: ((q[0] - x0) * s, size * ss / 2 - (q[1] - cy) * s)
    for a, b, c in plate.tris:
        d.polygon([px(pos[a]), px(pos[b]), px(pos[c])], fill=255)
    im = im.resize((size, size), Image.BOX)
    out = np.full((size, size, 4), 255, np.uint8); out[:, :, 3] = np.asarray(im, np.uint8)
    return out


def write_pics(out, log=print, only=None):
    from PIL import Image
    d = os.path.join(out, 'pics'); os.makedirs(d, exist_ok=True)
    for spec in SPECS:
        if only is not None and spec['key'] not in only:
            continue
        a = silhouette(spec)
        Image.fromarray(a, 'RGBA').save(os.path.join(d, 'item_%d.png' % spec['item']))
        ys, xs = (a[:, :, 3] > 0).nonzero()
        log('  item_%d.png %s: bbox x %d..%d y %d..%d' % (spec['item'], spec['key'], xs.min(), xs.max(), ys.min(), ys.max()))


# ------------------------------------------------------------------ previews
def previews(out, name, log=print):
    """<out>/png/<map>_<key>.png: side view, host model (blue), PD2 gun (yellow), magazine (magenta), grip zone, l hand attacher."""
    import kl_chars as C, kl_guns, kl_map_guns as MG, pd2_gun_preview as V
    rep = json.load(open(os.path.join(out, name, 'report.json')))
    lv0 = C.Lv(os.path.join(MAPROOT, name)); lv0.beside, lv0.side = {}, {}
    lv1 = C.Lv(os.path.join(out, name)); lv1.beside, lv1.side = {}, {}
    sc0, _ = lv0.scene(); p0 = G.read(lv0['.prm'], 'dd')
    sc1, _ = lv1.scene(); p1 = G.read(lv1['.prm'], 'dd')
    os.makedirs(os.path.join(out, 'png'), exist_ok=True)
    paths = []
    for key, g in rep['guns'].items():
        r0 = C.person(sc0, kl_guns.gun_node(sc0, g['template']))[0]; r1 = g['root']
        sh = MG.shape(p0, r0)
        host = [(*V.part_mesh(p0, o), (70, 150, 255), 36) for o in C.objects(p0, r0) if p0.chunks[o][0x0e] != 16]
        new = [(*V.part_mesh(p1, o), (255, 215, 60) if p1.u32(o, 0x3c) == 1 else (255, 60, 220), 70) for o in C.objects(p1, r1) if p1.chunks[o][0x0e] != 16]
        lh = sh['bones']['l hand attacher'][9:12]
        marks = [(lh[0], lh[1], 'l hand attacher', (255, 255, 255)), (0, 0, 'origin', (160, 160, 160))]
        box = (-40, 110, -26, 24)
        title = 'item %d %s on %s: blue = host %s, yellow = PD2 body, magenta = magazine; yellow frame = GRIP_ZONE' % (g['item'], key, name, g['template'])
        paths.append(V.side(host + new, box, os.path.join(out, 'png', '%s_%s.png' % (name, key)), scale=8.0, marks=marks, zone=MG.GRIP_ZONE, title=title))
        paths.append(V._top(host + new, (-40, 110, -14, 14), os.path.join(out, 'png', '%s_%s_top.png' % (name, key)), scale=8.0, title=key + ' from above'))
    for x in paths:
        log('  wrote ' + x)
    return paths


# ------------------------------------------------------------------ verify
def verify(out, log=print, live_root=None):
    import zipfile
    import kl_chars as C, kl_guns
    ok = True
    for name in sorted(os.listdir(out)):
        d = os.path.join(out, name)
        if not os.path.isfile(os.path.join(d, 'report.json')):
            continue
        rep = json.load(open(os.path.join(d, 'report.json')))
        live = os.path.join(live_root or MAPROOT, name)      # live_root: a layer baked on an earlier layer's stage (pd2_guns_layer)
        if name.endswith('_chain') and not os.path.isdir(live):      # variant on the Last Call chain stage (pd2_guns_stage.CHAIN)
            live = CHAIN
        elif name.endswith('_doors') and not os.path.isdir(live):    # variant on the Last Call chain + doors stage (pd2_guns_stage.DOORS)
            live = DOORS
        elif name.endswith('_glass') and not os.path.isdir(live):    # variant on the Last Call chain + glass connectivity stage (pd2_guns_stage.GLASS)
            live = GLASS
        zp = os.path.join(d, rep['slot'] + '_Main.zip')
        a, b = zipfile.ZipFile(os.path.join(live, rep['slot'] + '_Main.zip')), zipfile.ZipFile(zp)
        same_list = a.namelist() == b.namelist()
        changed = sorted(n.rsplit('_Main', 1)[-1] if '_Main' in n else n    # a changed non-_Main member (Menu/online.xml) fails the check below
                         for n in a.namelist() if a.read(n) != b.read(n))
        ok &= same_list and set(changed) <= {'.prm', '.MAT', '.TEX', '.oct', '.gms', '.prp'}
        lv = C.Lv(d); lv.beside, lv.side = {}, {}
        p, mat, tex = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT']), T.read_tex(lv['.TEX'])
        sc, _raw = lv.scene()
        lv0 = C.Lv(live); lv0.beside, lv0.side = {}, {}
        sc0, _r0 = lv0.scene()
        good = len(p.chunks) == rep['chunks_after']
        specs = {s['key']: s for s in SPECS}
        tpl_new = {}
        for key, g in rep['guns'].items():
            tpl_new[g['template']] = g['root']
            root = C.person(sc, kl_guns.gun_node(sc, g['template']))[0]
            good &= root == g['root']
            for o in C.objects(p, root):
                c = p.chunks[o]; dd = p.u32(p.u32(o, 0x28), 0); nv = p.u32(dd, 0)
                vch = p.chunks[p.u32(dd, 4)]; ix = p.chunks[p.u32(dd, 0x18)]; n = struct.unpack_from('<H', ix, 2)[0]
                ii = struct.unpack_from('<%dH' % n, ix, 4)
                good &= len(c) == 64 and c[0x0c] == 2 and len(vch) == (nv * 40 + 15) // 16 * 16 and max(ii) < nv and n % 3 == 0
                m = mat.insts[p.u16(o, 0x12)]
                good &= all(n_[3] in tex.tex or n_[3] in (0, 2147483648) for _s, n_ in T.texture_stages(m))
        # every OTHER template keeps the root it had
        import re as _re
        others = 0
        for k in range(1, len(sc.nodes)):
            pa = sc.path[k]
            if pa.endswith('\\Ground') and '\\Weapon\\' in pa:
                t = pa.split('\\')[-2]
                try:
                    r1 = C.person(sc, k)[0]; r0 = C.person(sc0, k)[0]
                except Exception:
                    continue
                if t in tpl_new:
                    good &= r1 == tpl_new[t]
                else:
                    good &= r1 == r0; others += 1
        good &= mat.refs == T.material_refs(G.write(p))
        log('%s: %s zip members changed %s; %d guns; %d other Ground nodes unchanged -> %s' % (name, rep['slot'], changed, len(rep['guns']), others, 'ok' if good else 'FAIL'))
        ok &= good
    log('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return ok


def main(a):
    out = os.path.join(work(), 'build', 'pd2guns_1105')
    if '--out' in a:
        out = a[a.index('--out') + 1]; del a[a.index('--out'):a.index('--out') + 2]
    only = None
    if '--only' in a:          # SPECS keys, e.g. --only C45,HRL50,HRL51 (build / all / pics)
        only = a[a.index('--only') + 1].split(','); del a[a.index('--only'):a.index('--only') + 2]
    if a[:1] == ['fit']:
        import numpy as np
        import kl_chars as C, kl_guns, kl_map_guns as MG, pd2_gun_preview as V, pd2_gun_fit as F
        lv = C.Lv(os.path.join(MAPROOT, 'DM02')); lv.beside, lv.side = {}, {}
        sc, _ = lv.scene(); p = G.read(lv['.prm'], 'dd'); rng = np.random.default_rng(1)
        for s in SPECS:
            root = C.person(sc, kl_guns.gun_node(sc, s['template']))[0]
            fit_one(s, _host(p, root, C, MG, V, rng, F.sample))
    elif a[:1] == ['build']:
        for m in a[1:]:
            stage_map(m, out, only=only)
    elif a[:1] == ['all']:
        for m in MAPS:
            stage_map(m, out, only=only)
    elif a[:1] == ['verify']:
        sys.exit(0 if verify(a[1] if len(a) > 1 else out) else 1)
    elif a[:1] == ['preview']:
        previews(out, a[1])
    elif a[:1] == ['pics']:
        write_pics(out, only=only)
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
