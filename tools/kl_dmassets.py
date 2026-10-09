#!/usr/bin/env python3
"""
Dead Men level assets -> Dog Days form, in one place, with the tests.

    python kl_dmassets.py                  test: the six maps below + every stock Dog Days level
    python kl_dmassets.py test M09_A ...   test only these maps
    python kl_dmassets.py convert [maps]   write <work>/build/FA/<map>/<base>_Main.TEX / .prm / .MAT
                                           and conversion.json (what was changed, dropped, guessed)
    add --dm-surface to keep Dead Men's surface type numbers in the .MAT (see below)

Each format has its own module with the facts and their sources:
  kl_tex.py   .TEX  container, cube maps, animated textures (kept); simulate_dd_loader
  kl_prm.py   .prm  mesh descriptors by graph walk, baked lighting, scatter, fonts, prop slot 2
  kl_mat.py   .MAT  Dog Days class trees, property lists, flags, surface type, render group
  kl_pf4.py   navigation mesh (a block of the .gms; kl_gms.convert converts it on the way)
ORDER MATTERS: the .MAT's use counts are derived from the CONVERTED .prm (scatter objects are
gone and their materials unused), so the .prm goes first. Texture ids, material slots and chunk
indices all stay as Dead Men had them: nothing that names them needs rewriting.

THE .MAT SURFACE NUMBERS: by default entry +0x18 is renumbered to Dog Days' surface table, which
is right for a graft onto a Dog Days level (it keeps that level's .buf tail). A whole-level
build that ships Dead Men's .buf (kl_package.build today) carries Dead Men's table and needs
--dm-surface / convert_level(..., surface=None).

The tests prove, for every map: the conversion runs; each output is read back under Dog Days'
rules by a checker that all 21 stock Dog Days files of that kind pass (so the rules are the
game's, not ours); nothing is lost that is not listed; and the three files still fit each other
(every root reachable, every material slot a model names exists, every texture a material,
sprite or glyph names exists, the .MAT use counts equal the .prm's).
"""
import json, os, struct, sys, time, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms, kl_mat, kl_pf4, kl_prm, kl_prmgraph as G, kl_tex, kl_texmat as TM
from kl_port_check import find, level_zips, workdir, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

MAPS = ('M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A', 'M09_A', 'M09_B')
_SCHEMA = {}


def members(path, exts):
    """{ext lower case: bytes} of a level archive's *_Main.<ext> members, and the base name."""
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            stem, _, ext = n.rpartition('.')
            if stem.lower().endswith('_main') and ext.lower() in exts:
                out[ext.lower()] = z.read(n)
                out['base'] = stem.rsplit('/', 1)[-1]
    return out


def dm_level(level, exts=('tex', 'prm', 'mat', 'gms', 'prp', 'buf'), dm=None):
    dm = dm or find(DM_GUESSES, DM_EXE)
    folder = os.path.join(dm, 'Scenes', 'Locations', level)
    zips = [f for f in sorted(os.listdir(folder)) if f.lower().endswith('_main.zip')]
    if len(zips) != 1:
        raise ValueError('%s: expected one *_Main.zip, found %r' % (level, zips))
    return members(os.path.join(folder, zips[0]), exts)


def prm_roots(gms, prp, game):
    """Everything that points into a level's .prm: chunk indices from the .gms (packed file) and
    (index, kind) pairs from the .prp fields kl_prmgraph knows."""
    import kl_rtp
    from kl_prp import Prp
    if game not in _SCHEMA:
        _SCHEMA[game] = kl_rtp.Schema.load(game)
    raw = kl_gms.unpack(gms)
    tids = [0x100021] + [e[1] for e in kl_gms.entities(raw)]
    return [c for c in G.gms_roots(raw)] + [(c, k) for _w, c, k in G.prp_roots(Prp(prp), tids, _SCHEMA[game], game)]


def nav_block(gms):
    raw = kl_gms.unpack(gms)
    nav = struct.unpack_from('<I', raw, 0x34)[0]
    return raw[nav + 4:nav + 4 + struct.unpack_from('<I', raw, nav)[0]] if nav else None


def convert_level(level, surface='dd', ref=None, src=None):
    """Convert one Dead Men map's assets. Returns ({'TEX': bytes, 'prm': bytes, 'MAT': bytes,
    'nav': bytes or None}, report, source members). The navigation mesh is returned for
    checking only: it lives in the .gms and kl_gms.convert writes it."""
    src = src or dm_level(level)
    roots = prm_roots(src['gms'], src['prp'], 'dm')
    tex, rtex = kl_tex.convert(src['tex'])
    prm, rprm = kl_prm.convert(src['prm'], roots)
    mat, rmat = kl_mat.convert_mat_full(src['mat'], ref, prm=prm, surface=surface,
                                        texture_ids=set(TM.read_tex(src['tex']).tex))
    rnav, nav = {}, None
    block = nav_block(src['gms'])
    if block is not None:
        nav = kl_pf4.convert(block, report=rnav)
    report = dict(level=level, base=src['base'], surface_numbers='Dog Days' if surface == 'dd' else 'Dead Men',
                  tex=rtex, prm=rprm, mat=rmat, nav=rnav)
    return {'TEX': tex, 'prm': prm, 'MAT': mat, 'nav': nav}, report, src


def _plain(x):
    """A report as JSON can hold it (tuple keys become 'a -> b' strings)."""
    if isinstance(x, dict):
        return {(' -> '.join(str(p) for p in k) if isinstance(k, tuple) else str(k)): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def write_level(level, surface='dd', ref=None, log=print):
    out, report, src = convert_level(level, surface, ref)
    problems = cross_check(out, src, report)
    if problems:
        raise ValueError('%s: %s' % (level, '; '.join(problems)))
    folder = os.path.join(workdir(), 'build', 'FA', level)
    os.makedirs(folder, exist_ok=True)
    for ext in ('TEX', 'prm', 'MAT'):
        with open(os.path.join(folder, '%s.%s' % (src['base'], ext)), 'wb') as f:
            f.write(out[ext])
    with open(os.path.join(folder, 'conversion.json'), 'w') as f:
        json.dump(_plain(report), f, indent=1, sort_keys=True)
    log('%s: wrote %s.TEX / .prm / .MAT and conversion.json to %s' % (level, src['base'], folder))
    return report


# ---------------------------------------------------------------- tests
def cross_check(out, src, report):
    """The converted files against each other and against the source. Returns problems."""
    bad = []
    roots = prm_roots(src['gms'], src['prp'], 'dm')
    # .TEX: the loader's walk, and every picture unchanged
    n, cubes, anims = kl_tex.simulate_dd_loader(out['TEX'])
    a, b = TM.read_tex(src['tex']), TM.read_tex(out['TEX'])
    same = lambda x, y: x[:12] == y[:12] and x[16:24] == y[16:24] and x[28:] == y[28:]
    if sorted(a.tex) != sorted(b.tex) or n != len(a.tex):
        bad.append('.TEX: texture ids changed')
    for i, x in a.tex.items():
        y = b.tex[i]
        if not same(x.entry, y.entry) or x.flags != y.flags:
            bad.append('.TEX: texture %d changed' % i)
        elif x.flags & kl_tex.CUBE:
            if len(y.faces) != 5 or not all(same(a.tex[j].entry, f) for j, f in zip(x.frames[1:], y.faces)):
                bad.append('.TEX: cube %d faces differ' % i)
        elif (x.frames is None) != (y.frames is None) or (x.frames is not None and tuple(x.frames) != tuple(y.frames)):
            bad.append('.TEX: frame list of %d differs' % i)
    if anims != sum(1 for x in a.tex.values() if x.flags & kl_tex.ANIMATED and not x.flags & kl_tex.CUBE and x.frames):
        bad.append('.TEX: animated textures lost')
    # .prm: Dog Days rules, every root still there, same kinds
    p0 = G.read(src['prm'], 'dm')
    before = G.walk(p0, roots)[0]
    kl_prm.check(out['prm'], roots, before)
    p1 = G.read(out['prm'], 'dd')
    kinds, args = G.walk(p1, roots)
    for r in roots:
        i = r if isinstance(r, int) else r[0]
        if i and i not in kinds:
            bad.append('.prm: root %d is not reachable' % i)
    lit = [i for i, k in before.items() if k == 'desc' and p0.u32(i, 0x10)]
    if report['prm']['lit'] < len(lit) or any(len(p1.chunks[i]) != 48 for i, k in before.items() if k == 'desc'):
        bad.append('.prm: a descriptor was not converted')
    # .prm -> .MAT and .TEX
    mat = TM.read_mat(out['MAT'])
    kl_mat.check(out['MAT'])
    for i, k in kinds.items():
        for off, typ, _t in G.fields(p1, i, k, args.get(i, 0)):
            if typ == 'm' and p1.u16(i, off) not in mat.insts:
                bad.append('.prm: object %d names material slot %d, which the .MAT lacks' % (i, p1.u16(i, off)))
            elif typ == 't' and p1.u32(i, off) and p1.u32(i, off) not in b.tex:
                bad.append('.prm: sprite %d names texture %d' % (i, p1.u32(i, off)))
            elif typ == 'T' and p1.u32(i, off) % G.SLOTS['dd'] not in b.tex:
                bad.append('.prm: font %d names texture %d' % (i, p1.u32(i, off)))
        if k == 'font':                             # glyph rectangle = size, in 1/512 of the page
            for q in range(p1.u32(i, 0x10)):
                ch, t, x0, y0, x1, y1, w, h = struct.unpack_from('<II6H', p1.chunks[i], 0x28 + 32 * q)
                th, tw = struct.unpack_from('<HH', b.tex[t % G.SLOTS['dd']].entry, 0x10)
                if (x1 - x0) * tw != w * 512 or (y1 - y0) * th != h * 512:
                    bad.append('.prm: font %d glyph %#x does not fit its page' % (i, ch)); break
    if mat.refs != TM.material_refs(out['prm'], mat.ninst):
        bad.append('.MAT: use counts differ from the .prm')
    if sorted(mat.insts) != sorted(TM.read_mat(src['mat']).insts):
        bad.append('.MAT: instance slots changed')
    missing = TM.used_textures(mat) - set(b.tex)
    if missing:
        bad.append('.MAT: textures %r are not in the .TEX' % sorted(missing)[:5])
    if report['mat']['misused']:
        bad.append('.MAT: scatter materials still in use: %r' % report['mat']['misused'])
    if out['nav'] is not None:
        kl_pf4.check(out['nav'], kl_pf4.DD_LINK_KINDS)
    return bad[:12]


def stock_check(log=print):
    """The checkers are Dog Days' rules only if every stock Dog Days file passes them."""
    dd = find(DD_GUESSES, DD_EXE)
    n = dict(tex=0, mat=0, prm=0, nav=0, levels=0)
    bad = 0
    ref = kl_mat.dd_reference(dd)
    for z in sorted(level_zips(dd)):
        if not z.endswith('_Main.zip') or os.sep + 'Locations' + os.sep not in z:
            continue
        m = members(z, ('tex', 'mat', 'prm', 'gms', 'prp'))
        n['levels'] += 1
        for what, fn in (('tex', lambda: kl_tex.simulate_dd_loader(m['tex'])),
                         ('mat', lambda: kl_mat.check(m['mat'], ref)),
                         ('prm', lambda: kl_prm.check(m['prm'], prm_roots(m['gms'], m['prp'], 'dd'))),
                         ('nav', lambda: kl_pf4.check(nav_block(m['gms'])))):
            try:
                fn(); n[what] += 1
            except ValueError as e:
                bad += 1; log('  STOCK FILE REJECTED: %s %s: %s' % (m.get('base'), what, e))
    log('stock Dog Days levels %d: .TEX accepted by simulate_dd_loader %d, .MAT by kl_mat.check %d, .prm by '
        'kl_prm.check %d, navigation mesh by kl_pf4.check %d' % (n['levels'], n['tex'], n['mat'], n['prm'], n['nav']))
    return bad


def test(maps=MAPS, log=print):
    bad = stock_check(log)
    ref = kl_mat.dd_reference()
    for level in maps:
        t = time.time()
        try:
            out, rep, src = convert_level(level, ref=ref)
            problems = cross_check(out, src, rep)
        except (ValueError, KeyError) as e:
            problems = ['conversion failed: %s' % e]
            log('%s: %s' % (level, problems[0])); bad += 1
            continue
        bad += len(problems)
        r = rep
        log('%s (%.0f s)' % (level, time.time() - t))
        log('  .TEX %(textures)d textures, %(cubes)d cube maps, %(animated)d animated (%(frames)d frames), '
            '%(dropped_lists)d unreachable lists dropped' % r['tex'])
        log('  .prm %(chunks)d chunks, %(descriptors)d descriptors of which %(lit)d lit (%(lit_meshes)d meshes '
            'unflagged), %(scatter)d scatter + %(water)d water objects emptied, %(fonts)d fonts (%(glyphs)d glyphs), '
            '%(prop2_roots)d reflection-plane roots, %(stripped)d chunks cut, %(added)d added, %(unknown)d unknown'
            % r['prm'] + ', %d scatter roots' % len(r['prm']['scatter_roots']))
        m = r['mat']
        log('  .MAT %d instances; classes without a Dog Days counterpart %s; bump bit set on %d; surface types '
            'renumbered %d by name + %d by guess; render groups changed %d, left %d, not seen in Dog Days %d; engine '
            'slots rewritten %d; properties added %d, dropped %d; use counts changed %d'
            % (m['instances'], ['/'.join(c) for c in m['no_counterpart']] or 'none', m['bump'],
               sum(m['surface'].values()), sum(m['surface_guess'].values()), sum(m['group'].values()),
               sum(m['group_unmapped'].values()), sum(m['group_not_in_dd'].values()),
               sum(m['engine_slots'].values()), sum(m['added'].values()), sum(m['dropped'].values()), m['refs_changed']))
        if out['nav'] is not None:
            log('  navigation mesh %s; links %d, kept %d, dropped by kind %s'
                % (kl_pf4.counts(out['nav'], True), r['nav']['links'], r['nav']['links_kept'], r['nav']['dropped'] or '{}'))
        for p in problems:
            log('  PROBLEM: ' + p)
    log('problems: %d' % bad)
    return bad


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    surface = None if '--dm-surface' in sys.argv else 'dd'
    if args and args[0] == 'convert':
        for lv in args[1:] or MAPS:
            write_level(lv, surface)
    elif not args or args[0] == 'test':
        sys.exit(1 if test(tuple(args[1:]) or MAPS) else 0)
    else:
        print(__doc__); sys.exit(1)
