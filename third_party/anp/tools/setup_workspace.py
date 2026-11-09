"""Builds the converter's work folder from your own game installs (nothing here is shipped with the repo).

  python tools/setup_workspace.py --dd "C:/.../Kane & Lynch 2 - Dog Days" --dm "C:/.../Kane and Lynch Dead Men" --work work

Creates in the work folder:
  scn/dd/<scene>.{prp,gms,buf}    every stock Dog Days scene (statistics + graft donor L01_Main)
  scn/dm/<L>_Main.{prp,gms,buf}   Dead Men levels (analysis tools only)
  cache/L01_Main.TEX              graft donor textures
  dd_types.txt                    classes Dog Days scenes use (their class-stats tables, incl. dynamic pools)
  dd_db.pkl, dd_arrlen.pkl, dd_enums.pkl   Dog Days property statistics used by prpconv
  ../fxc/union.pkl                every shader permutation found in Dog Days scenes
  ext/schemas/*.json              kl-merge's exact class schemas, pinned (needs a git checkout of kl-merge in ext/kl-merge),
                                  plus ANP's dd_enums_extra.json (enum tables kl-merge's extractor misses; --enums-only
                                  installs just that one)
Then run tools/port_level.py (the games are found through Steam; ANP_WORK, ANP_DD_GAME, ANP_DM_GAME override).

The scene set and order reproduce the stats the tested builds used (verified 10 Oct 2026): every zip in
F01-F09 and L00-L11 except Loader_Sequence (so L00_Intro too) plus the front end Scenes/kaneandlynch.zip,
in name order. Order matters: ties in the statistics and the shader union keep the first scene's value."""
import os, sys, argparse, glob, pickle, subprocess, struct, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zipraw import read_zip, read_entry
from gms import load_gms

ENUM_EXTRA = 'dd_enums_extra.json'

def install_enum_extra(work):
    """copy ANP's own enum supplement (tools/dd_enums_extra.json: kl2.exe enum tables missing from kl-merge's pinned
    dd_enums.json, read by prpconv with ANP_SMB_FIX=1) next to the pinned files. The pinned files are not touched."""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), ENUM_EXTRA)
    dst = os.path.join(work, 'ext', 'schemas'); os.makedirs(dst, exist_ok=True)
    shutil.copyfile(src, os.path.join(dst, ENUM_EXTRA))
    print('schema', ENUM_EXTRA, os.path.getsize(src), 'bytes (ANP supplement)')

def install_schemas(work):
    """copy kl-merge's exact class schemas, at the pinned commit, from the checkout in <work>/ext/kl-merge to
    <work>/ext/schemas (git show, so JC's checkout is left as it is)"""
    import anp_paths
    install_enum_extra(work)
    km = os.path.join(work, 'ext', 'kl-merge'); dst = os.path.join(work, 'ext', 'schemas')
    git = shutil.which('git') or os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'Git', 'cmd', 'git.exe')
    if not os.path.isdir(os.path.join(km, '.git')) or not os.path.exists(git):
        print('WARNING: no git checkout of kl-merge in %s (or no git): exact schemas not installed; '
              'port_level.py will stop until they are (or run it with ANP_EXACT=0)' % km)
        return
    os.makedirs(dst, exist_ok=True)
    for src, name in anp_paths.SCHEMA_FILES:
        r = subprocess.run([git, '-C', km, 'show', '%s:%s' % (anp_paths.SCHEMA_COMMIT, src)], capture_output=True)
        if r.returncode: raise SystemExit('git show %s:%s failed: %s' % (anp_paths.SCHEMA_COMMIT, src, r.stderr.decode(errors='replace')))
        open(os.path.join(dst, name), 'wb').write(r.stdout)
        print('schema', name, len(r.stdout), 'bytes (kl-merge %s)' % anp_paths.SCHEMA_COMMIT)

def stock_dd_scenes(dd):
    """{scene name: zip} for every stock Dog Days scene; test clones (X07) and ported levels (M..) are not stock"""
    loc = os.path.join(dd, 'Scenes', 'Locations'); out = {}
    for d in os.listdir(loc):
        if d[:1] in 'FL' and len(d) == 3 and d[1:].isdigit():
            for z in glob.glob(os.path.join(loc, d, '*.zip')):
                if not os.path.basename(z).startswith('Loader_Sequence'): out[os.path.basename(z)[:-4]] = z
    out['kaneandlynch'] = os.path.join(dd, 'Scenes', 'kaneandlynch.zip')
    return out

def extract_scenes(scenes, out_dir):
    os.makedirs(out_dir, exist_ok=True); bases = []
    for name in sorted(scenes):
        for e in read_zip(scenes[name]):
            if os.path.basename(e.name) in (name + '.prp', name + '.gms', name + '.buf'):
                open(os.path.join(out_dir, os.path.basename(e.name)), 'wb').write(read_entry(e))
        b = os.path.join(out_dir, name)
        if os.path.exists(b + '.prp'): bases.append(b)
        print('extracted', name)
    return bases

def class_types(gms_path):
    """types in a scene's class-stats table (h4) and dynamic pools (h9): placed entities plus runtime-spawned classes"""
    g = load_gms(gms_path); h = struct.unpack_from('<20I', g); ts = set()
    if 0 < h[4] < len(g):
        ts.update(struct.unpack_from('<I', g, h[4] + 4 + i * 12)[0] for i in range(struct.unpack_from('<I', g, h[4])[0]))
    if 0 < h[9] <= len(g) - 4:
        n9 = struct.unpack_from('<I', g, h[9])[0]
        if h[9] + 4 + n9 * 8 <= len(g): ts.update(struct.unpack_from('<I', g, h[9] + 4 + i * 8)[0] for i in range(n9))
    return ts

def extract_levels(game, out_dir, pick):
    os.makedirs(out_dir, exist_ok=True); bases = []
    loc = os.path.join(game, 'Scenes', 'Locations')
    for d in sorted(os.listdir(loc)):
        if not pick(d): continue
        for z in glob.glob(os.path.join(loc, d, '*_Main.zip')):
            for e in read_zip(z):
                nm = os.path.basename(e.name)
                if nm.endswith(('_Main.prp', '_Main.gms', '_Main.buf')):
                    open(os.path.join(out_dir, nm), 'wb').write(read_entry(e))
            b = os.path.join(out_dir, os.path.basename(z)[:-4])
            if os.path.exists(b + '.prp'): bases.append(b)
            print('extracted', os.path.basename(z))
    return bases

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dd'); ap.add_argument('--dm')
    ap.add_argument('--enums-only', action='store_true', help='only install the ANP enum supplement (%s)' % ENUM_EXTRA)
    tools = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--work', default=os.path.join(tools, '..', 'work'))
    a = ap.parse_args()
    W = os.path.abspath(a.work); os.makedirs(W, exist_ok=True)
    if a.enums_only:
        install_enum_extra(W); return
    if not a.dd or not a.dm: ap.error('--dd and --dm are required (unless --enums-only)')
    install_schemas(W)
    scenes = stock_dd_scenes(a.dd)
    ddb = extract_scenes(scenes, os.path.join(W, 'scn', 'dd'))
    extract_levels(a.dm, os.path.join(W, 'scn', 'dm'), lambda d: d.startswith('M'))
    # graft donor textures
    os.makedirs(os.path.join(W, 'cache'), exist_ok=True)
    for e in read_zip(os.path.join(a.dd, 'Scenes', 'Locations', 'L01', 'L01_Main.zip')):
        if e.name.endswith('L01_Main.TEX'): open(os.path.join(W, 'cache', 'L01_Main.TEX'), 'wb').write(read_entry(e))
    # classes Dog Days uses. Not just placed entities: port_level keeps a Dead Men dynamic pool (h9) only when
    # its class is listed here (every Dead Men level has pools of 0x100489 and 0x10048b).
    from gms import GMS
    types = set()
    for b in ddb:
        G = GMS(b + '.gms', b + '.buf'); types.update(e['type'] for e in G.ents)
        types |= class_types(b + '.gms')
    open(os.path.join(W, 'dd_types.txt'), 'w', newline='\n').write('\n'.join('0x%x' % t for t in sorted(types)) + '\n')
    py = sys.executable
    subprocess.check_call([py, os.path.join(tools, 'build_dd_db.py'), os.path.join(W, 'dd_db.pkl')] + ddb)
    subprocess.check_call([py, os.path.join(tools, 'build_arrlen.py'), os.path.join(W, 'dd_arrlen.pkl')] + ddb)
    subprocess.check_call([py, os.path.join(tools, 'enumcheck.py'), 'build', os.path.join(W, 'dd_enums.pkl')] + ddb)
    # shader permutation union (first scene in name order wins)
    from fxclib import parse as fxparse
    union = {}
    for name in sorted(scenes):
        for e in read_zip(scenes[name]):
            if e.name.endswith('.fxc'):
                ver, recs = fxparse(read_entry(e))
                for r in recs: union.setdefault((r['kind'], r['name'], tuple(n for n, v in r['defs'])), r['raw'])
    fxd = os.path.join(tools, '..', 'fxc'); os.makedirs(fxd, exist_ok=True)
    pickle.dump(union, open(os.path.join(fxd, 'union.pkl'), 'wb'))
    print('work folder ready:', W, '| shader permutations:', len(union))

if __name__ == '__main__':
    main()
