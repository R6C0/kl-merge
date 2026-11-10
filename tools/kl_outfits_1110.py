#!/usr/bin/env python3
"""kl_outfits_1110.py - campaign outfits for the Fragile Alliance wardrobe (owner 2026-11-10).

Adds NEW CHARACTERS (KLChar 17 ..) to a level that already has the 16-character wardrobe (tools/kl_chars.py wardrobe):
the Retomoto window-cleaner Kane / Lynch / mercs, the Vault-breaker, the Dead Men cast, other campaign Kane / Lynch
looks. Each is ONE Dead Men model put into the level's .prm (kl_chars.put, no entity names it - like the Dead Men
heroes) and dressed exactly like a Dog Days heister (Outfits=1 Bodies=1 Heads=1, re/wardrobe.md 3):
    variant 1            own face (the whole campaign model) + the money bag of the heister whose crew slot it takes
    variant 2            own mask = the stock mask of that heister (body without head + mask + bag)
    variant 2 + m        stock mask m (1..8): body without head + that heister's mask refitted by bone name + bag
    variant 2 + m (9-12) Payday 2 plates: the face look without face glasses + the plate objects of heister 1,
                         refitted by bone name (the same trick the stock masks use on another skeleton)
So klchar.c needs no new look logic: a character is a name, a root and a crew slot. Only its table size (KLC_NCHAR 16 -> 32,
[Wardrobe] CampaignOutfits) and the menu rows grow (klhook/klcampaign_outfits_logic.h, mkoverlay.py --outfits).

    python kl_outfits_1110.py list
    python kl_outfits_1110.py bake <in zip> <KLWardrobe.ini> <out zip> <out ini> [--count=N] [--only=KEY,KEY]
    python kl_outfits_1110.py stage <map folder> <out folder> [--count=N]   (plain zip + bots zip + ini)
    python kl_outfits_1110.py check <zip> <ini>

GUESS (never seen in the game): the look of every campaign model on a Dog Days animation set, the mask swap (DM_HEAD
materials are matched by name: a cap / helmet material would stay on a masked head), the bag position, variants other
than the first of a model with several (Vaultbreaker has 4, the bank Kane 3: only variant 1 is used).
"""
import collections, hashlib, json, os, re, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FIRST = 17                                       # KLChar of the first campaign outfit
MAX_NEW = 16                                     # klhook KLC_NCHAR 32 = 16 + 16
PRM_CAP = 94 * 1000 * 1000                       # re/wardrobe.md: the largest .prm that has loaded is 96.5 MB (a GUESS limit, not a proven one)
CHUNK_CAP = 69632                                # kl_impact.CHUNK_SAFE

# key, menu name, Dead Men level (survey name), model root in that level's .prm, crew slot it takes (0..7), group, why
SPECS = [
    ('wc_kane',   'Kane - window cleaner (Retomoto)',  'M09_A',   10159, 0, 'RETOMOTO', 'Retomoto Tower rappel, M09_A Hero_01_Suit (Hero_WindowCleaner_HEAD)'),
    ('wc_lynch',  'Lynch - window cleaner (Retomoto)', 'M09_A',   10366, 1, 'RETOMOTO', 'Retomoto Tower rappel, M09_A Lynch_COOP (Little_Windowcleaner_HEAD)'),
    ('vault',     'Vaultbreaker',                      'M03_A',   26824, 2, 'CAST',     'M03_A Vaultbreaker_Merc_01 (USA_Vaultbreaker_Head), variant 1 of 4'),
    ('shelly',    'Shelly - window cleaner',           'M09_A',   10480, 3, 'RETOMOTO', 'M09_A C_Merc_Shelly'),
    ('rific',     'Rific - window cleaner',            'M09_A',   10561, 4, 'RETOMOTO', 'M09_A C_Merc_Rific'),
    ('thapa',     'Thapa - window cleaner',            'M09_A',   10658, 5, 'RETOMOTO', 'M09_A C_Merc_Thapa'),
    ('carlos',    'Carlos',                            'M02_A',   12273, 6, 'CAST',     'M02_A Squad_The_7 Carlos'),
    ('lion',      'Lion (Elder Brother)',              'M02_A',   12360, 7, 'CAST',     'M02_A Squad_The_7 Elder_Brother'),
    ('flame',     'Flame (Little Brother)',            'M02_A',   12423, 0, 'CAST',     'M02_A Squad_The_7 Little_Brother'),
    ('mute',      'Mute (the Doctor)',                 'M02_A',   12548, 1, 'CAST',     'M02_A Squad_The_7 No4_Doctor_Mute'),
    ('fuentes',   'Fuentes',                           'M11_B',   28181, 2, 'CAST',     'M11_B Fuentes squad'),
    ('kane_bust', 'Kane - bust-out',                   'M01_A',   39409, 3, 'CAMPAIGN', 'M01_A Hero_01_Suit (bloody head), variant 1 of 3'),
    ('lynch_bust', 'Lynch - bust-out',                 'M01_A',   38622, 4, 'CAMPAIGN', 'M01_A Lynch_COOP'),
    ('kane_bank', 'Kane - bank',                       'M03_A',   26354, 5, 'CAMPAIGN', 'M03_A AI_Players Kane, variant 1 of 3 (1.8 MB)'),
    ('lynch_bank', 'Lynch - bank',                     'M03_A',   26649, 6, 'CAMPAIGN', 'M03_A AI_Players Lynch_COOP, variant 1 of 4 (1.7 MB)'),
    ('boss',      'Retomoto boss',                     'M06_FA_A', 848, 7, 'CAST',     'M06_FA_A JPN_Boss Retomoto'),
]
KEYS = [s[0] for s in SPECS]
STEP, MASKS, STOCK_MASKS = 14, 12, 8


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def lv_from_zip(path, ini):
    """kl_chars.Lv of ONE zip (not a folder): the live maps keep bots.zip and dozens of backups beside it."""
    import kl_chars as C
    lv = C.Lv.__new__(C.Lv)
    lv.name = os.path.basename(path)[:-len('_Main.zip')]
    lv.beside, lv.side = {}, {'KLWardrobe.ini': ini}
    with zipfile.ZipFile(path) as z:
        lv.order = z.namelist()
        lv.files = {n: z.read(n) for n in lv.order}
    lv.ext = {n.rsplit('_Main', 1)[1]: n for n in lv.order if '_Main' in n}
    lv.src = path
    return lv


def write_zip(lv, out):
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for n in lv.order:
            z.writestr(n, lv.files[n])


def read_ini(path):
    """-> (text, header dict, [character dict]) of a KLWardrobe.ini."""
    text = open(path, encoding='latin1').read()
    head, chars, cur = {}, [], None
    for ln in text.splitlines():
        m = re.match(r'\[(.+)\]', ln.strip())
        if m:
            cur = None
            if m.group(1).startswith('Character.'):
                cur = {}; chars.append(cur)
            continue
        if '=' in ln and not ln.startswith(';'):
            k, v = ln.split('=', 1)
            (cur if cur is not None else head)[k.strip()] = v.strip()
    return text, head, chars


class TooBig(Exception):
    def __init__(self, nbytes, nchunks, chunks0, bytes0, n):
        Exception.__init__(self, 'prm %d chunks %d' % (nbytes, nchunks))
        self.nbytes, self.nchunks, self.n = nbytes, nchunks, n
        self.per_bytes, self.per_chunks = (nbytes - bytes0) / max(n, 1), (nchunks - chunks0) / max(n, 1)


def bake_fit(src_zip, ini_in, out_zip, out_ini, specs=None, log=print):
    """bake() with as many of `specs` (priority order) as keep the .prm under PRM_CAP. -> report."""
    specs = list(specs or SPECS)
    n = len(specs)
    while n:
        try:
            r = bake(src_zip, ini_in, out_zip, out_ini, specs[:n], log)
            r['count'], r['wanted'] = n, len(specs)
            return r
        except TooBig as e:
            drop = max(int((e.nbytes - PRM_CAP) / e.per_bytes) + 1, int((e.nchunks - CHUNK_CAP) / e.per_chunks) + 1, 1)
            log('  .prm %.1f MB / %d chunks over the cap with %d models, retry with %d' % (e.nbytes / 1e6, e.nchunks, n, max(n - drop, 0)))
            n -= drop
    return dict(count=0, wanted=len(specs), new=[], out=None, note='no room: the .prm is already within %.1f MB of the cap' % (PRM_CAP / 1e6))


def stage_map(mapdir, out, count=None, log=print):
    r"""mapdir = <DD>\KLExpansion\Maps\<map>: writes the plain zip, the bots zip and the ini into `out`. -> report"""
    zp = next(f for f in os.listdir(mapdir) if f.endswith('_Main.zip'))
    bots = os.path.join(mapdir, zp.replace('.zip', '.bots.zip'))
    os.makedirs(out, exist_ok=True)
    o_zip, o_ini = os.path.join(out, zp), os.path.join(out, 'KLWardrobe.ini')
    r = bake_fit(os.path.join(mapdir, zp), os.path.join(mapdir, 'KLWardrobe.ini'), o_zip, o_ini, pick_specs(count), log)
    if not r.get('out'):
        return r
    # bots zip = its own members, with the ones the bake changed taken from the baked plain zip
    with zipfile.ZipFile(os.path.join(mapdir, zp)) as a, zipfile.ZipFile(o_zip) as n, zipfile.ZipFile(bots) as b:
        with zipfile.ZipFile(os.path.join(out, zp.replace('.zip', '.bots.zip')), 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as w:
            changed = []
            for name in b.namelist():
                data = b.read(name)
                if name in n.namelist() and name in a.namelist() and n.read(name) != a.read(name):
                    if a.read(name) != data:
                        raise ValueError('%s differs between the plain and bots zip and the bake changed it' % name)
                    data = n.read(name); changed.append(name)
                w.writestr(name, data)
    r['bots_changed'] = [c.rsplit('/', 1)[-1] for c in changed]
    return r


def pick_specs(count=None, only=None):
    sp = [s for s in SPECS if not only or s[0] in only]
    return sp[:count] if count else sp


def _mname(p, mat, o):
    return mat.insts[p.u16(o, 0x12)].name.split('/')[-1].lower()


def dress(p, mat, root, dd, slot, note):
    """Give the new model `root` the 14 looks (docstring). dd = [(heister root, skeleton)] of the 8 stock heisters in this
    level's wardrobe, in crew order. -> dict(objects, variants)."""
    import kl_chars as C
    skm = C.skeleton(p, root)
    note.setdefault('runs', {})
    own = C._Fit(p, skm, skm)
    objs = C.objects(p, root)
    have = {p.chunks[o][0x0f] for o in objs}
    if have != {1}:
        raise ValueError('root %d: expected only variant 1 after put (has %r)' % (root, sorted(have)))
    isd = lambda o: C.DM_HEAD and any(s in _mname(p, mat, o) for s in C.DM_HEAD)
    head = [o for o in objs if isd(o)]
    body = [o for o in objs if not isd(o)]
    if {p.chunks[o][0x0e] for o in body} != {1, 2, 0x7c}:
        raise ValueError('root %d: the body (everything but %s) has LOD masks %r, not 1 2 0x7c' % (
            root, '/'.join(sorted({_mname(p, mat, o) for o in head})), sorted({p.chunks[o][0x0e] for o in body})))
    # the stock heisters' parts: wardrobe roots hold variant 2 = mask + masked body + bag
    mask, bag = {}, {}
    for n, (r, sk) in enumerate(dd):
        v2 = [o for o in C.objects(p, r) if p.chunks[o][0x0f] == C.V_OWN]
        mask[n] = [o for o in v2 if 'mask' in _mname(p, mat, o)]
        bag[n] = [o for o in v2 if 'moneybag' in _mname(p, mat, o)]
        if {p.chunks[o][0x0e] for o in mask[n]} != {1, 2, 0x7c} or not bag[n]:
            raise ValueError('heister %d: mask / bag parts are not what this tool knows' % (n + 1))
    fits = {n: C._Fit(p, dd[n][1], skm) for n in range(8)}
    fit_bag = fits[slot]
    def with_v(parts, v, fit):
        return [C._moved(p, o, fit, v, note) for o in parts]
    out = list(objs) + with_v(bag[slot], 1, fit_bag)                      # variant 1: the model as put() left it + the bag
    for m in range(0, STOCK_MASKS + 1):
        v = C.V_OWN if m == 0 else 2 + m
        mm = slot if m == 0 else m - 1                                    # 'own mask' = the mask of the heister whose place it takes
        out += with_v(body, v, own) + with_v(mask[mm], v, fits[mm]) + with_v(bag[slot], v, fit_bag)
    C._set_objects(p, root, out)
    return dict(objects=len(out), head_parts=sorted({_mname(p, mat, o) for o in head}), body_parts=sorted({_mname(p, mat, o) for o in body}))


def add_plates_reuse(p, mat, tex, lv, chars, log, nplates=4):
    """kl_pd2mask.add_plates for the new characters only: the map already has the four plates' textures and materials
    (PD2_Mask_<name>), they are looked up by name instead of being added a second time. -> dict(tex_bytes=...)"""
    import kl_pd2mask as M, kl_texmat as T
    names = ['wolf', 'dallas', 'chains', 'hoxton'][:nplates]
    if not names:
        return dict(tex_bytes=T.write_tex(tex), plates=[])
    have = {e.name.split('/')[-1]: s for s, e in mat.insts.items() if e.name}
    queue = []
    for n in names:
        s = have.get('PD2_Mask_' + n.capitalize())
        if s is None:
            return dict(tex_bytes=T.write_tex(tex), skipped='no PD2 plate material for ' + n)
        st = dict(T.texture_stages(mat.insts[s]))
        queue += [st['mapDiffuse'][3], st['mapNormal'][3]]
        queue.append(s)
    specs = M.plate_specs(','.join(names), lv)
    q = iter(queue)
    o_tex, o_mat = M.add_texture, M.clone_material
    def tex_(*a, **k):
        return next(q)
    def mat_(*a, **k):
        return next(q)
    # add_plates asks per plate: diffuse texture, normal texture, material - the queue order above
    M.add_texture, M.clone_material = tex_, mat_
    try:
        rep = M.add_plates(p, mat, tex, chars, specs, log=log)
    finally:
        M.add_texture, M.clone_material = o_tex, o_mat
    return dict(tex_bytes=T.write_tex(tex), plates=rep)


def _skip_converted_levels():
    r"""luvsic's converted Locations\M* levels make kl_mat.dd_reference() fail ('two different trees'): not looked at."""
    import kl_port_check
    if getattr(kl_port_check.level_zips, '_kl1110', False):
        return
    orig = kl_port_check.level_zips
    def lz(*a, **k):
        r = orig(*a, **k)
        try:
            return [x for x in r if 'Locations\\M' not in str(x) and 'Locations/M' not in str(x)]
        except Exception:
            return r
    lz._kl1110 = True
    kl_port_check.level_zips = lz


def bake(src_zip, ini_in, out_zip, out_ini, specs=None, log=print):
    """-> report. src_zip must hold the 16-character wardrobe of ini_in (Characters=16, Masks=12)."""
    import kl_chars as C, kl_prmgraph as G, kl_texmat as T, kl_impact
    _skip_converted_levels()
    text, head, chars = read_ini(ini_in)
    if len(chars) != 16 or head.get('Characters') != '16':
        raise ValueError('%s: %s characters, a 16-character wardrobe is the base (already extended?)' % (ini_in, head.get('Characters')))
    nmask = int(head.get('Masks', 0))                 # 8 (stock masks only) .. 12 (+ plates); the look of body 0 is 1 / 2 / 2 + m whatever OutfitStep is
    if not STOCK_MASKS <= nmask <= MASKS or int(head.get('OutfitStep', 0)) < nmask + 2:
        raise ValueError('%s: Masks=%s OutfitStep=%s: not a wardrobe this tool knows' % (ini_in, head.get('Masks'), head.get('OutfitStep')))
    specs = specs or SPECS
    lv = lv_from_zip(src_zip, ini_in)
    keep = {e: lv[e] for e in ('.gms', '.prp')}      # nothing is retargeted: the scene stays byte for byte (the bots zip has its own .prp)
    prm0 = len(lv['.prm'])
    p0 = G.read(lv['.prm'], 'dd')
    n0 = len(p0.chunks) - 1
    donor = int(chars[0]['Root'])
    picks = []
    for s in specs:
        src = C.Source.get(s[2], lambda *a: None)
        have = sorted({src.prm.chunks[o][0x0f] for o in C.objects(src.prm, s[3])})
        # variant 0 draws at every variant, so a campaign model's objects are all variant 0; a model with several variants uses its first
        picks.append(C.Pick((), s[2], s[3], {1: have[0]}, donor))
    rep = C.put(lv, picks, free='add', log=log, reuse=False)
    p, mat = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT'])
    dd = [(int(c['Root']), C.skeleton(p, int(c['Root']))) for c in chars[:8]]
    if not all(c['Stock'] == '1' for c in chars[:8]):
        raise ValueError('characters 1..8 are not the Dog Days heisters')
    note = dict(low=0, inexact=0, rest=0.0, worst='', by_bone={})
    new = []
    for s, pk in zip(specs, rep['picks']):
        info = dress(p, mat, pk['new_model'], dd, s[4], note)
        new.append(dict(key=s[0], name=s[1], root=pk['new_model'], slot=s[4], bones=pk['bones'], **info))
    plates = add_plates_reuse(p, mat, T.read_tex(lv['.TEX']), lv, [dict(root=c['root'], bodies=1) for c in new], log, nmask - STOCK_MASKS)
    if note['rest'] > C.MAX_REST:
        raise ValueError('a moved object\'s bone rests %.2f units from where it did (limit %.1f): %s' % (note['rest'], C.MAX_REST, note['worst']))
    lv['.TEX'] = plates['tex_bytes']
    prm_bytes = G.write(p)
    mat.refs = T.material_refs(prm_bytes)
    lv['.prm'], lv['.MAT'] = prm_bytes, T.write_mat(mat)
    for e, b in keep.items():
        lv[e] = b
    if len(prm_bytes) > PRM_CAP or len(p.chunks) - 1 > CHUNK_CAP or kl_impact.chunk_limit(lv['.prm']):
        raise TooBig(len(prm_bytes), len(p.chunks) - 1, n0, prm0, len(specs))
    write_zip(lv, out_zip)
    # the ini: Characters= and the new sections; every other line of the old file stays as it is
    new_text = re.sub(r'^Characters=\d+', 'Characters=%d' % (16 + len(specs)), text, count=1, flags=re.M)
    if not new_text.endswith('\n'):
        new_text += '\r\n'
    new_text = new_text.replace('\r\n', '\n').replace('\n', '\r\n')
    add = ''.join('[Character.%d]\r\nName=%s\r\nRoot=%d\r\nSlot=%d\r\nOutfits=1\r\nBodies=1\r\nHeads=1\r\nStock=0\r\n' % (
        17 + i, c['name'], c['root'], c['slot']) for i, c in enumerate(new))
    with open(out_ini, 'w', newline='', encoding='latin1') as f:
        f.write(new_text + add)
    return dict(src=src_zip, out=out_zip, new=new, chunks=(n0, len(p.chunks) - 1), prm=(prm0, len(prm_bytes)),
                materials=rep['materials'], textures=rep['textures'], shaders_missing=rep['shaders_missing'],
                largest_rest=round(note['rest'], 3), inexact=note['inexact'])


def check(zip_path, ini_path, log=print):
    """Offline proof on a baked zip: every new character has all looks at three levels of detail, bones inside the skeleton,
    chunk table, kl_impact bone ids, .ANM binding of the new skeletons. -> list of problems."""
    import kl_chars as C, kl_prmgraph as G, kl_texmat as T, kl_impact
    _t, head, chars = read_ini(ini_path)
    lv = lv_from_zip(zip_path, ini_path)
    p, mat = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT'])
    bad = []
    new = chars[16:]
    nm = int(head.get('Masks', 12))
    for c in new:
        r = int(c['Root'])
        vs = collections.defaultdict(set)
        for o in C.objects(p, r):
            vs[p.chunks[o][0x0f]].add(p.chunks[o][0x0e])
        want = [1, 2] + [2 + m for m in range(1, nm + 1)]
        for v in want:
            if vs.get(v) != {1, 2, 0x7c}:
                bad.append('%s: variant %d has LOD masks %r' % (c['Name'], v, sorted(vs.get(v, ()))))
        extra = set(vs) - set(want)
        if extra:
            bad.append('%s: unexpected variants %r' % (c['Name'], sorted(extra)))
    roots = [int(c['Root']) for c in new]
    bad += ['impact: %s' % x for x in kl_impact.bone_faults(p)]
    limit = kl_impact.chunk_limit(lv['.prm'])
    if limit:
        bad.append(limit[0])
    bad += [x for x in C.check(lv, None, roots, lambda *a: None, extra=[int(c['Root']) for c in chars])
            if 'Sprites/Sprites has two different trees' not in x]       # also reported on the unmodified live zips
    log('%s: %d new characters, %d problems, .prm %.1f MB, %d chunks' % (os.path.basename(zip_path), len(new), len(bad), len(lv['.prm']) / 1e6, len(p.chunks) - 1))
    return bad


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = {x.split('=')[0]: x.split('=', 1)[1] for x in sys.argv[1:] if x.startswith('--') and '=' in x}
    if not a or a[0] == 'list':
        for i, s in enumerate(SPECS, FIRST):
            print('%2d %-11s %-38s %-8s root %-6d slot %d  %s' % (i, s[0], s[1], s[2], s[3], s[4], s[6]))
    elif a[0] == 'bake':
        sp = pick_specs(int(opt['--count']) if '--count' in opt else None, opt['--only'].split(',') if '--only' in opt else None)
        r = bake(a[1], a[2], a[3], a[4], sp)
        print(json.dumps(r, indent=1, default=str))
    elif a[0] == 'stage':
        r = stage_map(a[1], a[2], int(opt['--count']) if '--count' in opt else None)
        print(json.dumps(r, indent=1, default=str))
    elif a[0] == 'check':
        sys.exit(1 if check(a[1], a[2]) else 0)
    else:
        raise SystemExit(__doc__)
