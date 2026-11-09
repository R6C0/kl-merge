#!/usr/bin/env python3
"""kl_campaign.py - run luvsic's Dead Men CAMPAIGN converter from kl-merge, without touching the game.

The converter is luvsic's (A Newer Perspective, third_party/anp/tools/port_level.py @32aa649, vendored; credit: in
contribution with luvsic). It turns a whole Dead Men story level into a Dog Days scene folder M01..M14 (campaign
chapters), the opposite direction of kl_graft.py (a Dead Men MAP under Dog Days' systems). Both coexist: this one only
ever writes NEW folders (M01, M02, ... M14, M07F), never an F0x/L0x slot.

  python tools/kl_campaign.py env                 print the environment the converter will run with
  python tools/kl_campaign.py setup               = his setup_workspace.py (about 2.5 min; reads both installs, writes only
                                                    <work>\\anp_work; the exact schemas come from `git show 8466319:..`)
  python tools/kl_campaign.py setup --schemas-only    just the schemas + run tree (seconds, no game needed)
  python tools/kl_campaign.py convert M01|all     = port_level.py per level, output <work>\\anp_out\\<ID>\\ (NOT the game)
  python tools/kl_campaign.py status              which ids are built / installed
  python tools/kl_campaign.py install M01|all     copy <anp_out>\\<ID>\\ into <DD>\\Scenes\\Locations\\<ID>\\ (additive)
  python tools/kl_campaign.py undo M01|all        remove exactly what install wrote (md5-checked)

Defaults (every one can be overridden from the environment or the options):
  ANP_WORK   = <kl_port_check.workdir()>\\anp_work          ANP_OUT = <workdir>\\anp_out
  ANP_DM_HUD=0, ANP_DM_FONTS=0   Dead Men's HUD art / typefaces are NOT converted (owner: not the whole UI thing)
  ANP_GRAFT_MENU=1, ANP_GRAFT_OSD=1  stay ON: they graft DOG DAYS' OWN menu / pause / OSD subtrees (needed for pause + HUD)
  ANP_SMB_FIX=0   tools/dd_enums_extra.json is not in luvsic's repo (see third_party/anp/README.md): the squad-modifier
                  enum supplement is off, patrol move sets then fall back to the field default (a small M02 detail)
  ANP_KLMERGE = this repo (schemas at commit 8466319, tools/kl_hvk.py ...)

The run tree: the vendored tools are copied to <anp_work>\\runtree (so union.pkl, __pycache__ and the schema pickles never
land in the repo) and a 15-line shim replaces dmhud.py (the one UI module prpconv imports even with the HUD off).

install is ADDITIVE and refuses: while kl2.exe runs, if the target folder exists and holds no KLCAMPAIGN_MANIFEST.json
(not ours), if a file of our earlier install was edited since, for an id outside the table, or into KL_PortBackup.
"""
import os, sys, json, hashlib, shutil, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
VENDOR = os.path.join(REPO, 'third_party', 'anp')
MANIFEST = 'KLCAMPAIGN_MANIFEST.json'
SCHEMA_COMMIT = '8466319'   # = third_party/anp/tools/anp_paths.py SCHEMA_COMMIT (checked by the self-test)
SCHEMA_FILES = (('re/schemas_dd.json', 'schemas_dd.json'), ('re/schemas_dm.json', 'schemas_dm.json'),
                ('tools/dd_enums.json', 'dd_enums.json'))

# id -> (Dead Men folder under Scenes\Locations, Dead Men file prefix). READ port_level.py:399-401 DM_SCENE_IDS (folder,
# id) + the files on disk (<folder>\<prefix>_Main.zip: M03_B -> M03B_Main.zip, prefix = folder without '_').
LEVELS = {
    'M01': ('M01_A', 'M01A'), 'M02': ('M02_A', 'M02A'), 'M03': ('M03_A', 'M03A'), 'M03B': ('M03_B', 'M03B'),
    'M05': ('M05_A', 'M05A'), 'M06': ('M06_A', 'M06A'), 'M07': ('M07_A', 'M07A'), 'M08': ('M08_A', 'M08A'),
    'M09': ('M09_A', 'M09A'), 'M09B': ('M09_B', 'M09B'), 'M11': ('M11_A', 'M11A'), 'M11B': ('M11_B', 'M11B'),
    'M12': ('M12_A', 'M12A'), 'M13': ('M13_A', 'M13A'), 'M13B': ('M13_B', 'M13B'), 'M14': ('M14_A', 'M14A'),
}
# special scene (port_level.py SPECIAL_SCENES): the funeral keeps Dead Men's path under Scenes\ (no Locations)
SPECIAL = {'M07F': dict(dm_folder='CutScenes\\M07', dm_name='M07_A_Funeral', rel='CutScenes/M07', stem='M07_A_Funeral')}
ALL_IDS = list(LEVELS) + list(SPECIAL)

# the modules the vendored converter imports that were left out on purpose (UI) -> shim
DMHUD_SHIM = '''"""kl-merge shim for luvsic's tools/dmhud.py (Dead Men HUD art conversion, left out: owner does not want his UI).
prpconv imports it only for xhair_props() (Dead Men's whole-crosshair art fields). None = "unknown shape, Dog Days
defaults kept" (prpconv.py handles that branch). HudPlan is never reached with ANP_DM_HUD=0."""
def xhair_props():
    return None
def HudPlan(*a, **k):
    raise SystemExit('dmhud.HudPlan: Dead Men HUD conversion is not part of kl-merge (run with ANP_DM_HUD=0)')
'''


# ------------------------------------------------------------------ paths and environment
def _port_check():
    sys.path.insert(0, HERE)
    try:
        import kl_port_check
        return kl_port_check
    except Exception:
        return None

def default_workdir():
    pc = _port_check()
    return pc.workdir() if pc else HERE

def find_game(which):
    """DD or DM folder: ANP_DD_GAME / ANP_DM_GAME, else kl_port_check's guesses; None when not found"""
    env = os.environ.get('ANP_DD_GAME' if which == 'dd' else 'ANP_DM_GAME')
    if env: return env
    pc = _port_check()
    if not pc: return None
    return pc.find(pc.DD_GUESSES, pc.DD_EXE) if which == 'dd' else pc.find(pc.DM_GUESSES, pc.DM_EXE)

def resolve(work=None, out=None, dd=None, dm=None):
    """the folders everything uses: {'work','out','dd','dm','wd'}"""
    wd = default_workdir()
    work = work or os.environ.get('ANP_WORK') or os.path.join(wd, 'anp_work')
    out = out or os.environ.get('ANP_OUT') or os.path.join(wd, 'anp_out')
    return dict(wd=wd, work=os.path.abspath(work), out=os.path.abspath(out),
                dd=dd or find_game('dd'), dm=dm or find_game('dm'))

def runtree(work): return os.path.join(work, 'runtree')

def converter_env(P, base=None):
    """the environment of every converter run. Anything already in `base` (default os.environ) wins, so the owner can
    still override; returns (env, notes) where notes[k] says where each ANP_* value came from."""
    env = dict(os.environ if base is None else base)
    notes = {}
    def dflt(k, v, why):
        if k in env and env[k] != '': notes[k] = 'environment'
        else: env[k] = v; notes[k] = why
    dflt('ANP_WORK', P['work'], 'kl-merge default (<workdir>\\anp_work)')
    dflt('ANP_OUT', P['out'], 'kl-merge default (<workdir>\\anp_out, never the game folder)')
    if P.get('dd'): dflt('ANP_DD_GAME', P['dd'], 'found (kl_port_check)')
    if P.get('dm'): dflt('ANP_DM_GAME', P['dm'], 'found (kl_port_check); read only')
    dflt('ANP_KLMERGE', REPO, 'this repo (schemas @%s, kl_hvk)' % SCHEMA_COMMIT)
    dflt('ANP_DM_HUD', '0', "Dead Men's HUD art off (UI left out)")
    dflt('ANP_DM_FONTS', '0', "Dead Men's typefaces off (UI left out)")
    dflt('ANP_GRAFT_MENU', '1', "ON: grafts Dog Days' OWN menu/pause subtrees")
    dflt('ANP_GRAFT_OSD', '1', "ON: grafts Dog Days' OWN HUD (OSD) subtrees")
    dflt('ANP_SMB_FIX', '0', 'off: tools/dd_enums_extra.json missing in luvsic repo')
    shim = os.path.join(runtree(P['work']), 'shim')
    env['PYTHONPATH'] = shim + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    return env, notes


# ------------------------------------------------------------------ run tree + schemas
def stage_runtree(work):
    """copy third_party/anp/{tools,fxc,scripts} to <work>/runtree and write the shim; never deletes union.pkl.
    Returns the number of files written."""
    rt = runtree(work); n = 0
    for sub in ('tools', 'fxc', 'scripts'):
        for root, dirs, files in os.walk(os.path.join(VENDOR, sub)):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                s = os.path.join(root, f)
                d = os.path.join(rt, os.path.relpath(s, VENDOR))
                if os.path.exists(d) and md5_file(d) == md5_file(s): continue
                os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copyfile(s, d); n += 1
    sd = os.path.join(rt, 'shim'); os.makedirs(sd, exist_ok=True)
    p = os.path.join(sd, 'dmhud.py')
    if not os.path.exists(p) or open(p, encoding='utf-8').read() != DMHUD_SHIM:
        open(p, 'w', encoding='utf-8', newline='\n').write(DMHUD_SHIM); n += 1
    return n

def git_exe():
    return shutil.which('git') or os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'Git', 'cmd', 'git.exe')

def install_schemas(work, repo=REPO):
    """git show 8466319:<file> from the kl-merge repo into <work>/ext/schemas (+ an EMPTY dd_enums_extra.json: the real one
    is not in luvsic's repo, see README). Returns [(name, bytes)]."""
    dst = os.path.join(work, 'ext', 'schemas'); os.makedirs(dst, exist_ok=True); done = []
    for src, name in SCHEMA_FILES:
        r = subprocess.run([git_exe(), '-C', repo, 'show', '%s:%s' % (SCHEMA_COMMIT, src)], capture_output=True)
        if r.returncode:
            raise SystemExit('git show %s:%s failed in %s: %s' % (SCHEMA_COMMIT, src, repo, r.stderr.decode(errors='replace')))
        open(os.path.join(dst, name), 'wb').write(r.stdout); done.append((name, len(r.stdout)))
    open(os.path.join(dst, 'dd_enums_extra.json'), 'w', encoding='utf-8').write('{"tables": {}}\n')
    done.append(('dd_enums_extra.json', 15))
    return done


# ------------------------------------------------------------------ md5 + install/undo
def md5_file(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def game_running(exe='kl2.exe'):
    """True while the game runs (Windows tasklist; elsewhere False). Zombie processes count: the owner checks by hand."""
    if os.name != 'nt': return False
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq %s' % exe, '/NH'], capture_output=True, text=True)
    return exe.lower() in r.stdout.lower()

def layout(level_id, out, dd):
    """(source folder, target folder, main zip name) of one id"""
    if level_id in SPECIAL:
        sp = SPECIAL[level_id]; rel = sp['rel'].split('/')
        return os.path.join(out, *rel), os.path.join(dd, 'Scenes', *rel), sp['stem'] + '.zip'
    if level_id in LEVELS:
        return os.path.join(out, level_id), os.path.join(dd, 'Scenes', 'Locations', level_id), level_id + '_Main.zip'
    raise SystemExit('unknown id %s (known: %s)' % (level_id, ' '.join(ALL_IDS)))

def _files(root):
    r = []
    for d, ds, fs in os.walk(root):
        for f in fs:
            r.append(os.path.relpath(os.path.join(d, f), root).replace('\\', '/'))
    return sorted(r)

def _guard_target(dst, dd):
    n = os.path.normcase(os.path.abspath(dst)).lower()      # .lower(): normcase folds case on Windows only; the refusal must hold on any host (cloud tests)
    if 'kl_portbackup' in n: raise SystemExit('refusing: %s is in KL_PortBackup' % dst)
    base = os.path.normcase(os.path.abspath(os.path.join(dd, 'Scenes'))).lower()
    if not n.startswith(base + os.sep): raise SystemExit('refusing: %s is not under %s' % (dst, base))

def install_level(level_id, out, dd, work, running=game_running, force=False, log=print):
    """Copy <out>/<ID>/ to <dd>/Scenes/Locations/<ID>/. Returns the manifest dict. Raises SystemExit on a refusal
    (nothing written then)."""
    src, dst, mainzip = layout(level_id, out, dd)
    _guard_target(dst, dd)
    if running(): raise SystemExit('refusing: kl2.exe is running (close it, also zombie processes in Task Manager)')
    if not os.path.isfile(os.path.join(src, mainzip)):
        raise SystemExit('%s not built: %s missing (python tools/kl_campaign.py convert %s)' % (level_id, os.path.join(src, mainzip), level_id))
    files = _files(src)
    if MANIFEST in files: raise SystemExit('refusing: the build folder %s contains %s' % (src, MANIFEST))
    old = None
    if os.path.isdir(dst):
        mp = os.path.join(dst, MANIFEST)
        if os.path.isfile(mp):
            old = json.load(open(mp, encoding='utf-8'))
            if old.get('tool') != 'kl_campaign': raise SystemExit('refusing: %s is not our manifest' % mp)
            bad = [f for f, h in old['files'].items() if os.path.isfile(os.path.join(dst, f)) and md5_file(os.path.join(dst, f)) != h]
            if bad and not force:
                raise SystemExit('refusing: %d file(s) of the earlier install changed since (e.g. %s); --force to overwrite' % (len(bad), bad[0]))
        elif os.listdir(dst):
            raise SystemExit('refusing: %s exists and is not ours (no %s). Stock or hand-made content stays untouched.' % (dst, MANIFEST))
    need = sum(os.path.getsize(os.path.join(src, f)) for f in files)
    probe = dst
    while not os.path.exists(probe): probe = os.path.dirname(probe)
    free = shutil.disk_usage(probe).free
    if free < need * 1.05 + (64 << 20):
        raise SystemExit('refusing: needs %d MB, %d MB free on the game drive' % (need >> 20, free >> 20))
    created = []
    p = dst
    while not os.path.exists(p): created.append(p); p = os.path.dirname(p)
    created.reverse()      # outermost first
    man = dict(tool='kl_campaign', id=level_id, source=os.path.abspath(src), target=os.path.abspath(dst),
               files={f: md5_file(os.path.join(src, f)) for f in files}, created_dirs=created if old is None else old.get('created_dirs', []))
    ul = os.path.join(work, 'anp_install'); os.makedirs(ul, exist_ok=True)
    ulp = os.path.join(ul, 'UNDO_%s.json' % level_id)
    json.dump(man, open(ulp, 'w', encoding='utf-8'), indent=1)       # written first: a half install can still be undone
    os.makedirs(dst, exist_ok=True)
    try:
        for f in files:
            d = os.path.join(dst, f); os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(os.path.join(src, f), d + '.klpart'); os.replace(d + '.klpart', d)
        if old:
            for f in old['files']:
                if f not in man['files'] and os.path.isfile(os.path.join(dst, f)): os.remove(os.path.join(dst, f))
        json.dump(man, open(os.path.join(dst, MANIFEST), 'w', encoding='utf-8'), indent=1)
    except BaseException:
        log('install failed: undoing %s' % level_id)
        undo_level(level_id, dd, work, running=lambda: False, log=log, manifest=man)
        raise
    log('installed %s: %d files, %d MB -> %s (undo list %s)' % (level_id, len(files), need >> 20, dst, ulp))
    return man

def undo_level(level_id, dd, work, running=game_running, log=print, manifest=None):
    """Delete exactly the files of the manifest whose md5 still matches; then the manifest and the dirs we made, if empty.
    Returns (removed, kept) lists."""
    sp = SPECIAL.get(level_id); rel = sp['rel'].split('/') if sp else ['Locations', level_id]
    if level_id not in ALL_IDS: raise SystemExit('unknown id %s' % level_id)
    dst = os.path.join(dd, 'Scenes', *rel)
    _guard_target(dst, dd)
    if running(): raise SystemExit('refusing: kl2.exe is running')
    mp = os.path.join(dst, MANIFEST)
    man = manifest
    if man is None:
        if os.path.isfile(mp): man = json.load(open(mp, encoding='utf-8'))
        else:
            ulp = os.path.join(work, 'anp_install', 'UNDO_%s.json' % level_id)
            if os.path.isfile(ulp): man = json.load(open(ulp, encoding='utf-8'))
    if man is None or man.get('tool') != 'kl_campaign':
        log('%s: nothing of ours to undo (no manifest)' % level_id); return [], []
    if os.path.normcase(os.path.abspath(man['target'])) != os.path.normcase(os.path.abspath(dst)):
        raise SystemExit('refusing: manifest target %s is not %s' % (man['target'], dst))
    removed, kept = [], []
    for f, h in man['files'].items():
        p = os.path.join(dst, f)
        if not os.path.isfile(p): continue
        if md5_file(p) == h: os.remove(p); removed.append(f)
        else: kept.append(f)
        if os.path.isfile(p + '.klpart'): os.remove(p + '.klpart')
    if kept:
        log('%s: %d file(s) changed since install were kept (e.g. %s); manifest kept' % (level_id, len(kept), kept[0]))
    else:
        if os.path.isfile(mp): os.remove(mp)
        # empty subdirs of the target, then the dirs this install created (innermost first)
        for d, ds, fs in sorted(os.walk(dst), key=lambda t: -len(t[0])):
            if not os.listdir(d): os.rmdir(d)
        for d in reversed(man.get('created_dirs', [])):
            if os.path.isdir(d) and not os.listdir(d): os.rmdir(d)
    log('%s: removed %d, kept %d' % (level_id, len(removed), len(kept)))
    return removed, kept

def is_installed(level_id, dd):
    sp = SPECIAL.get(level_id); rel = sp['rel'].split('/') if sp else ['Locations', level_id]
    return os.path.isfile(os.path.join(dd, 'Scenes', *rel, MANIFEST))


# ------------------------------------------------------------------ convert
def convert_args(level_id):
    if level_id in SPECIAL: return [level_id]
    folder, name = LEVELS[level_id]
    return [folder, name, level_id]

def workspace_ready(work):
    need = [os.path.join(work, 'dd_types.txt'), os.path.join(work, 'dd_db.pkl'), os.path.join(work, 'ext', 'schemas', 'schemas_dd.json'),
            os.path.join(runtree(work), 'fxc', 'union.pkl')]
    return [p for p in need if not os.path.exists(p)]

def run_convert(level_id, P, log=print):
    miss = workspace_ready(P['work'])
    if miss: raise SystemExit('workspace not set up (missing %s): run python tools/kl_campaign.py setup' % miss[0])
    if not P['dd'] or not P['dm']: raise SystemExit('both game folders are needed (set ANP_DD_GAME / ANP_DM_GAME or pass --dd/--dm)')
    if os.path.normcase(os.path.abspath(P['out'])).startswith(os.path.normcase(os.path.abspath(P['dd'])) + os.sep):
        raise SystemExit('refusing: ANP_OUT %s is inside the Dog Days folder; convert writes to the work folder, install copies' % P['out'])
    env, _ = converter_env(P)
    cmd = [sys.executable, '-u', os.path.join(runtree(P['work']), 'tools', 'port_level.py')] + convert_args(level_id)
    os.makedirs(os.path.join(P['work'], 'anp_logs'), exist_ok=True)
    lp = os.path.join(P['work'], 'anp_logs', 'convert_%s.log' % level_id)
    log('convert %s -> %s (log %s)' % (level_id, P['out'], lp))
    with open(lp, 'w', encoding='utf-8', errors='replace') as lf:
        r = subprocess.run(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT, cwd=runtree(P['work']))
    tail = open(lp, encoding='utf-8', errors='replace').read().strip().splitlines()[-3:]
    for t in tail: log('  ' + t)
    return r.returncode


# ------------------------------------------------------------------ CLI
def pick_ids(arg):
    if arg.lower() == 'all': return list(ALL_IDS)      # the 16 story levels + the M07 funeral cut scene
    ids = []
    for a in arg.replace(',', ' ').split():
        a = a.upper()
        if a not in ALL_IDS: raise SystemExit('unknown id %s (known: %s)' % (a, ' '.join(ALL_IDS)))
        ids.append(a)
    return ids

def cmd_status(P, log=print):
    rows = []
    for i in ALL_IDS:
        src, dst, mz = layout(i, P['out'], P['dd'] or '')
        z = os.path.join(src, mz)
        built = os.path.getsize(z) if os.path.isfile(z) else 0
        inst = bool(P['dd']) and is_installed(i, P['dd'])
        rows.append((i, built, inst)); log('%-5s built %-12s installed %s' % (i, ('%d MB' % (built >> 20)) if built else '-', 'yes' if inst else '-'))
    return rows

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--work'); ap.add_argument('--out'); ap.add_argument('--dd'); ap.add_argument('--dm')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('env'); sub.add_parser('status')
    s = sub.add_parser('setup'); s.add_argument('--schemas-only', action='store_true')
    for c in ('convert', 'install', 'undo'):
        x = sub.add_parser(c); x.add_argument('ids'); x.add_argument('--force', action='store_true') if c == 'install' else None
    a = ap.parse_args(argv)
    P = resolve(a.work, a.out, a.dd, a.dm)
    if a.cmd == 'env':
        env, notes = converter_env(P)
        for k in sorted(notes): print('%s=%s    [%s]' % (k, env[k], notes[k]))
        print('PYTHONPATH=%s    [shim for the left-out dmhud.py]' % env['PYTHONPATH'])
        print('run tree=%s (from %s)' % (runtree(P['work']), VENDOR))
        return 0
    if a.cmd == 'status':
        cmd_status(P); return 0
    if a.cmd == 'setup':
        n = stage_runtree(P['work']); print('run tree: %d file(s) written to %s' % (n, runtree(P['work'])))
        for name, sz in install_schemas(P['work']): print('schema %s %d bytes (kl-merge %s)' % (name, sz, SCHEMA_COMMIT))
        if a.schemas_only: return 0
        if not P['dd'] or not P['dm']: raise SystemExit('both game folders are needed (ANP_DD_GAME / ANP_DM_GAME or --dd/--dm)')
        env, _ = converter_env(P)
        # his setup_workspace with its two schema steps replaced by ours (they need a git checkout inside the work folder
        # and tools/dd_enums_extra.json); everything else (extracts, pickles, shader union) is his, unchanged
        code = ("import sys; sys.path.insert(0, %r); import setup_workspace as s; "
                "s.install_schemas = lambda w: None; s.install_enum_extra = lambda w: None; "
                "sys.argv = ['setup_workspace.py', '--dd', %r, '--dm', %r, '--work', %r]; s.main()"
                % (os.path.join(runtree(P['work']), 'tools'), P['dd'], P['dm'], P['work']))
        return subprocess.run([sys.executable, '-u', '-c', code], env=env, cwd=runtree(P['work'])).returncode
    ids = pick_ids(a.ids)
    if a.cmd == 'convert':
        stage_runtree(P['work']); rc = 0
        for i in ids: rc = run_convert(i, P) or rc
        return rc
    if not P['dd']: raise SystemExit('Dog Days folder not found: --dd or ANP_DD_GAME')
    if a.cmd == 'install':
        for i in ids: install_level(i, P['out'], P['dd'], P['work'], force=a.force)
        return 0
    if a.cmd == 'undo':
        for i in ids: undo_level(i, P['dd'], P['work'])
        return 0

if __name__ == '__main__':
    sys.exit(main())
