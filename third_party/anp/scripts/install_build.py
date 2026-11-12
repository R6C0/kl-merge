"""Install a converted build into Dog Days, with a backup and a rollback.

usage:
  install_build.py <out_dir> [levels...|all] [--dry] [--menu DIR] [--loader ASI] [--movie BIK]
                   [--wait-min N] [--allow-installed-funeral]
  install_build.py --rollback <backup_dir> [--dry]

<out_dir> is a build tree as port_level.py writes it with ANP_OUT=work\\<out> (a name alone is looked up under work\\):
  <out>\\<L>\\*            -> <DD>\\Scenes\\Locations\\<L>\\   (one folder per level; the nested <out>\\Scenes\\Locations\\<L>
                              layout is read too)
  <out>\\CutScenes\\M07\\*  -> <DD>\\Scenes\\CutScenes\\M07\\  (the funeral, port_level.py M07F) whenever M07 is installed
Levels are the 16 Dead Men ids (M01 .. M14) or 'all' (every one of them present in the build); 'M07F' alone installs
just the funeral. No level names means none (handy with --menu / --loader / --movie only).
Extras: --menu DIR (DIR\\ANP\\ANP_Patch01.zip + DIR\\ANP\\menu\\frontend.xml, or DIR = that ANP folder) -> <DD>\\ANP\\,
--loader ASI -> <DD>\\ANP_Loader.asi, --movie BIK -> <DD>\\Movies\\ANP\\M00_Intro.bik.

Rules enforced:
- refuses while kl2.exe runs (checked at start, after the lock and before every write);
- takes work\\GAME_LOCK with scripts\\kltest.py's protocol (waits while someone else's lock is younger than 15 min,
  --wait-min, default 30; a lock whose owner pid is still alive is never taken over, however old) and keeps it fresh;
- M07 whose zip (SceneChanger target in the .prp) or build log points at CutScenes/M07/M07_A_Funeral.zip is refused
  when the build has no complete CutScenes\\M07 (zip + .WHD + .WAV + Loader_Sequence.zip), unless
  --allow-installed-funeral and Dog Days already has a complete one;
- every folder/file it replaces is first moved to work\\backup\\install_<time>\\ (same relative path as in Dog Days) and
  checked by SHA-1 there; every copied file is checked by SHA-1 against the build; on any failure everything done so far
  is rolled back;
- prints the rollback command (install_build.py --rollback <backup dir>), which puts the backed-up folders/files back
  (what it removes from Dog Days goes to work\\backup\\rollback_<time>\\, not to the bin).
--dry writes nothing anywhere: it prints the plan, the SHA-1 comparison against what is installed, and the lock state.
Exit codes: 0 ok, 2 refused (game running / lock), 3 bad plan, 4 install failed and rolled back, 5 rollback problem."""
import ctypes, hashlib, json, os, re, shutil, subprocess, sys, time, zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'tools'))
import anp_paths

WORK = anp_paths.WORK
LOCK = os.path.join(WORK, 'GAME_LOCK')
DM_LEVELS = ['M01', 'M02', 'M03', 'M03B', 'M05', 'M06', 'M07', 'M08', 'M09', 'M09B', 'M11', 'M11B', 'M12', 'M13',
             'M13B', 'M14']
FUNERAL_DIR = 'CutScenes/M07'
FUNERAL_NEED = ['M07_A_Funeral.zip', 'M07_A_Funeral.WHD', 'M07_A_Funeral.WAV', 'Loader_Sequence.zip']
STALE_S = 15 * 60


def die(code, msg):
    print('REFUSED: ' + msg if code == 2 else 'ERROR: ' + msg, flush=True)
    sys.exit(code)


def kl2_running():
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True)
    return 'kl2.exe' in r.stdout.lower()


def pid_alive(pid):
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
    if not h: return False
    code = ctypes.c_ulong()
    ok = k32.GetExitCodeProcess(h, ctypes.byref(code)); k32.CloseHandle(h)
    return bool(ok) and code.value == 259               # STILL_ACTIVE


def sha1(p):
    h = hashlib.sha1()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()


def manifest(path):
    """{relative path: sha1} of a folder (recursive) or {'': sha1} of a file; {} when it does not exist"""
    if os.path.isfile(path): return {'': sha1(path)}
    m = {}
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                p = os.path.join(root, f)
                m[os.path.relpath(p, path).replace('\\', '/')] = sha1(p)
    return dict(sorted(m.items()))


def size_of(path):
    if os.path.isfile(path): return os.path.getsize(path)
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(path) for f in fs)


# ------------------------------------------------------------------------------------------------ GAME_LOCK
class Lock:
    """scripts\\kltest.py's protocol: write our owner text, re-read it 0.5 s later; wait while someone else's lock is
    younger than 15 min. Extra guard: never take over a lock whose 'pid=N' process is still alive."""
    def __init__(self, what):
        self.txt = 'install_build %s %s pid=%d' % (what, time.strftime('%Y-%m-%d %H:%M:%S'), os.getpid())
        self.have = False

    @staticmethod
    def state():
        try: return time.time() - os.path.getmtime(LOCK), open(LOCK).read().strip()
        except OSError: return None, ''

    @staticmethod
    def owner_alive(txt):
        m = re.search(r'pid=(\d+)', txt)
        return bool(m) and int(m.group(1)) != os.getpid() and pid_alive(int(m.group(1)))

    def take(self, wait_min):
        deadline = time.time() + wait_min * 60
        while True:
            age, txt = self.state()
            if age is None:
                try:
                    with open(LOCK, 'x') as f: f.write(self.txt)
                except FileExistsError:
                    continue
            elif txt != self.txt and age >= STALE_S and not self.owner_alive(txt):
                print('GAME_LOCK is stale (%.0f min, "%s"): taking it' % (age / 60, txt), flush=True)
                with open(LOCK, 'w') as f: f.write(self.txt)
            if age is None or txt == self.txt or (age >= STALE_S and not self.owner_alive(txt)):
                time.sleep(0.5)
                if self.state()[1] == self.txt: self.have = True; return True
            if time.time() > deadline: return False
            print('GAME_LOCK held: "%s" (%.0f s old) - waiting' % (txt, age or 0), flush=True); time.sleep(30)

    def touch(self):
        if self.have:
            try: os.utime(LOCK, None)
            except OSError: pass

    def release(self):
        try:
            if self.have and open(LOCK).read().strip() == self.txt: os.remove(LOCK)
        except OSError: pass
        self.have = False


def lock_report():
    age, txt = Lock.state()
    if age is None: return 'GAME_LOCK free'
    return 'GAME_LOCK held: "%s" (%.0f s old%s%s)' % (txt, age, ', stale' if age >= STALE_S else '',
                                                     ', owner pid alive' if Lock.owner_alive(txt) else '')


# ------------------------------------------------------------------------------------------------ plan
def resolve_out(arg):
    for p in (arg, os.path.join(WORK, arg)):
        if os.path.isdir(p): return os.path.abspath(p)
    die(3, 'build folder not found: %s' % arg)


def zip_targets_funeral(zpath):
    """True/False from the scene's .prp string table: the converted SceneChanger target is written in Dog Days form
    (forward slashes): 'CutScenes/M07/M07_A_Funeral.zip' or 'Locations/M08/M08_Main.zip'. The Dead Men entity keeps
    its backslash name 'CutScenes\\M07\\M07_A_Funeral.zip' in both cases, so slashes are NOT normalised here.
    None if it cannot be read or neither target is there."""
    try:
        with zipfile.ZipFile(zpath) as z:
            prps = [z.read(i).lower() for i in z.infolist() if i.filename.lower().endswith('.prp')]
    except (OSError, zipfile.BadZipFile):
        return None
    if any(b'\0cutscenes/m07/m07_a_funeral.zip\0' in d for d in prps): return True
    if any(b'\0locations/m08/m08_main.zip\0' in d for d in prps): return False
    return None


def log_targets_funeral(out, loc_root):
    """('<log>', True/False) from port_level's 'SceneChanger node ...: [..] -> [..]' line; (None, None) if no log"""
    for p in (os.path.join(out, '_logs', 'M07.log'), os.path.join(out, 'build_M07.log'), os.path.join(loc_root, '_logs', 'M07.log')):
        if os.path.isfile(p):
            raw = open(p, 'rb').read()          # PowerShell redirects write UTF-16 (BOM ff fe), py ones UTF-8
            text = raw.decode('utf-16', 'replace') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'replace')
            hits = [l.lstrip('﻿') for l in text.splitlines()]
            hits = [l for l in hits if l.startswith('SceneChanger node')]
            if hits:
                tgt = [l.split('->', 1)[1] for l in hits if '->' in l]
                return p, any('m07_a_funeral' in t.lower() for t in tgt)
    return None, None


def funeral_complete(d):
    return all(os.path.isfile(os.path.join(d, x)) for x in FUNERAL_NEED)


def build_plan(a, DD):
    out = resolve_out(a['out'])
    if os.path.abspath(out).lower().startswith(os.path.abspath(DD).lower()):
        die(3, 'the build folder is inside Dog Days: %s' % out)
    nested = os.path.join(out, 'Scenes', 'Locations')
    if os.path.isdir(nested):
        loc_root, cut_root = nested, os.path.join(out, 'Scenes', 'CutScenes')
    else:
        loc_root, cut_root = out, os.path.join(out, 'CutScenes')
    want = [x.upper() for x in a['levels']]
    if 'ALL' in want:
        want = [L for L in DM_LEVELS if os.path.isdir(os.path.join(loc_root, L))] + [x for x in want if x != 'ALL']
        if not want: die(3, 'no level folders in %s' % loc_root)
    levels, seen = [], set()
    for L in want:
        if L in seen: continue
        seen.add(L)
        if L != 'M07F' and L not in DM_LEVELS: die(3, '%s is not a Dead Men level id (%s, M07F)' % (L, ' '.join(DM_LEVELS)))
        levels.append(L)
    items, notes = [], []
    for L in levels:
        if L == 'M07F': continue
        src = os.path.join(loc_root, L)
        need = ['%s_Main.zip' % L, '%s_Main.WHD' % L, '%s_Main.WAV' % L, 'Loader_Sequence.zip']
        miss = [x for x in need if not os.path.isfile(os.path.join(src, x))]
        if miss: die(3, '%s: incomplete build in %s (missing %s)' % (L, src, ', '.join(miss)))
        items.append(dict(kind='dir', id=L, rel='Scenes/Locations/' + L, src=src))
    fun_src = os.path.join(cut_root, 'M07')
    if 'M07' in levels or 'M07F' in levels:
        have = os.path.isdir(fun_src)
        if have and not funeral_complete(fun_src):
            die(3, 'the build has an incomplete funeral in %s (needs %s)' % (fun_src, ', '.join(FUNERAL_NEED)))
        if 'M07' in levels:
            zt = zip_targets_funeral(os.path.join(loc_root, 'M07', 'M07_Main.zip'))
            lp, lt = log_targets_funeral(out, loc_root)
            notes.append('M07 SceneChanger -> funeral: zip %s, log %s' % (
                {True: 'yes', False: 'no (M08)', None: 'unreadable'}[zt],
                'n/a' if lp is None else ('%s (%s)' % ('yes' if lt else 'no (M08)', lp))))
            if zt is not None and lt is not None and zt != lt:
                notes.append('  note: zip and log disagree; the zip wins (the log may be from another build)')
            targets = zt if zt is not None else (lt if lt is not None else True)   # unknown = assume the funeral
            if targets and not have:
                dd_fun = os.path.join(DD, 'Scenes', *FUNERAL_DIR.split('/'))
                if a['allow_installed_funeral'] and funeral_complete(dd_fun):
                    notes.append('M07 points at the funeral; the build has none, Dog Days keeps its installed one '
                                 '(--allow-installed-funeral)')
                else:
                    die(3, 'M07 ends into CutScenes/M07/M07_A_Funeral.zip but the build has no %s (build it with '
                           'port_level.py M07F into the same ANP_OUT, or pass --allow-installed-funeral to keep the one '
                           'Dog Days has)' % fun_src)
        if have:
            items.append(dict(kind='dir', id='M07F', rel='Scenes/' + FUNERAL_DIR, src=fun_src))
        elif 'M07F' in levels:
            die(3, 'M07F asked for but the build has no %s' % fun_src)
    if a['menu']:
        m = os.path.abspath(a['menu'])
        base = m if os.path.isfile(os.path.join(m, 'ANP_Patch01.zip')) else os.path.join(m, 'ANP')
        for rel in ('ANP_Patch01.zip', 'menu/frontend.xml'):
            s = os.path.join(base, *rel.split('/'))
            if not os.path.isfile(s): die(3, '--menu: %s missing' % s)
            items.append(dict(kind='file', id='menu', rel='ANP/' + rel, src=s))
    if a['loader']:
        s = os.path.abspath(a['loader'])
        if not (os.path.isfile(s) and s.lower().endswith('.asi')): die(3, '--loader: not an .asi file: %s' % s)
        items.append(dict(kind='file', id='loader', rel='ANP_Loader.asi', src=s))
    if a['movie']:
        s = os.path.abspath(a['movie'])
        if not (os.path.isfile(s) and s.lower().endswith('.bik')): die(3, '--movie: not a .bik file: %s' % s)
        items.append(dict(kind='file', id='movie', rel='Movies/ANP/M00_Intro.bik', src=s))
    if not items: die(3, 'nothing to install')
    return out, items, notes


# ------------------------------------------------------------------------------------------------ moves
def dd_path(DD, rel): return os.path.join(DD, *rel.split('/'))


def move(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)


def copy_in(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src): shutil.copytree(src, dst, copy_function=shutil.copy2)
    else: shutil.copy2(src, dst)


def remove(p):
    if os.path.isdir(p): shutil.rmtree(p)
    elif os.path.exists(p): os.remove(p)


def save_state(bk, state):
    tmp = os.path.join(bk, 'install.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(state, f, indent=1)
    # a scanner/indexer can hold the fresh file for a moment (11 Oct: WinError 5 twice, a full rollback each time)
    for i in range(10):
        try:
            os.replace(tmp, os.path.join(bk, 'install.json')); return
        except PermissionError:
            if i == 9: raise
            time.sleep(0.5)


def undo(DD, bk, state, aside):
    """put back what install.json says was replaced; whatever is in Dog Days at those paths now goes to aside"""
    bad = 0
    for it in reversed(state['items']):
        if it.get('status') in (None, 'planned'): continue
        dst = dd_path(DD, it['rel']); saved = os.path.join(bk, *it['rel'].split('/'))
        if os.path.exists(dst):
            move(dst, os.path.join(aside, *it['rel'].split('/')))
        if it['existed']:
            if not os.path.exists(saved): print('  %s: backup copy missing (%s)' % (it['rel'], saved)); bad += 1; continue
            move(saved, dst)
            ok = manifest(dst) == it['before']
            print('  %s: restored, sha1 %s' % (it['rel'], 'OK' if ok else 'MISMATCH'), flush=True); bad += not ok
        else:
            print('  %s: was not there before, removed' % it['rel'], flush=True)
        for d in reversed(it.get('made_dirs', [])):
            try: os.rmdir(d)
            except OSError: pass
        it['status'] = 'rolled_back'
    state['rolled_back'] = time.strftime('%Y-%m-%d %H:%M:%S'); state['rollback_aside'] = aside
    save_state(bk, state)
    return bad


def missing_parents(p):
    out = []; d = os.path.dirname(p)
    while d and not os.path.isdir(d): out.append(d); d = os.path.dirname(d)
    return list(reversed(out))


def install(a, DD):
    out, items, notes = build_plan(a, DD)
    print('build : %s' % out)
    print('target: %s' % DD)
    for n in notes: print(n)
    running = kl2_running()
    print('kl2.exe running: %s' % ('YES - a real install refuses' if running else 'no'))
    print(lock_report())
    total = 0
    for it in items:
        it['want'] = manifest(it['src'])
        dst = dd_path(DD, it['rel'])
        it['existed'] = os.path.exists(dst)
        cur = manifest(dst) if it['existed'] else {}
        total += size_of(it['src'])
        if not it['existed']: how = 'new'
        elif cur == it['want']: how = 'identical to what is installed'
        else:
            ch = sum(1 for k in it['want'] if cur.get(k) != it['want'][k]); gone = sum(1 for k in cur if k not in it['want'])
            how = 'replaces installed (%d file(s) differ/new, %d installed file(s) not in the build)' % (ch, gone)
        it['dry_how'] = how
        print('  %-6s %-30s <- %s  [%d file(s), %.1f MB] %s' % (it['id'], it['rel'], os.path.relpath(it['src'], REPO),
                                                          len(it['want']), size_of(it['src']) / 1e6, how), flush=True)
    print('total %.1f MB, %d item(s)' % (total / 1e6, len(items)))
    if a['dry']:
        print('DRY RUN: nothing written (no backup, no lock, no copy)'); return 0
    if running: die(2, 'kl2.exe is running')
    lock = Lock(os.path.basename(out))
    if not lock.take(a['wait_min']): die(2, 'GAME_LOCK not free after %d min (%s)' % (a['wait_min'], lock_report()))
    bk = os.path.join(WORK, 'backup', 'install_' + time.strftime('%m%d_%H%M%S'))
    os.makedirs(bk)
    rb = '"%s" "%s" --rollback "%s"' % (sys.executable, os.path.abspath(__file__), bk)
    state = dict(created=time.strftime('%Y-%m-%d %H:%M:%S'), build=out, dd=DD, items=[
        dict(id=it['id'], kind=it['kind'], rel=it['rel'], src=it['src'], existed=it['existed'], status='planned',
             want=it['want']) for it in items])
    save_state(bk, state)
    print('backup: %s\nrollback: %s' % (bk, rb), flush=True)
    try:
        if kl2_running(): raise RuntimeError('kl2.exe started')
        # 1) back up every target that exists (moved, then checked by sha1 in its new place)
        for it in state['items']:
            dst = dd_path(DD, it['rel'])
            if not it['existed']: continue
            it['before'] = manifest(dst); save_state(bk, state)
            if kl2_running(): raise RuntimeError('kl2.exe started')
            saved = os.path.join(bk, *it['rel'].split('/'))
            move(dst, saved); it['status'] = 'backed_up'; save_state(bk, state)
            if manifest(saved) != it['before']: raise RuntimeError('%s: backup sha1 mismatch' % it['rel'])
            print('  backed up %s (%d file(s), sha1 OK)' % (it['rel'], len(it['before'])), flush=True)
            lock.touch()
        # 2) copy the build in, check every file by sha1
        for it in state['items']:
            if kl2_running(): raise RuntimeError('kl2.exe started')
            dst = dd_path(DD, it['rel'])
            it['made_dirs'] = missing_parents(dst); it['status'] = 'copying'; save_state(bk, state)
            copy_in(it['src'], dst)
            got = manifest(dst)
            if got != it['want']:
                bad = sorted(k for k in set(got) | set(it['want']) if got.get(k) != it['want'].get(k))
                raise RuntimeError('%s: sha1 mismatch after copy: %s' % (it['rel'], ', '.join(bad[:8])))
            it['status'] = 'installed'; save_state(bk, state)
            print('  installed %s (%d file(s), sha1 OK)' % (it['rel'], len(got)), flush=True)
            lock.touch()
    except Exception as e:
        print('FAILED: %s - rolling back' % e, flush=True)
        aside = os.path.join(WORK, 'backup', 'rollback_' + time.strftime('%m%d_%H%M%S'))
        bad = undo(DD, bk, state, aside)
        lock.release()
        print('rolled back%s; partial copies (if any) in %s' % ('' if not bad else ' WITH %d PROBLEM(S)' % bad, aside))
        return 4 if not bad else 5
    state['done'] = time.strftime('%Y-%m-%d %H:%M:%S'); save_state(bk, state)
    lock.release()
    print('done: %d item(s) installed and checked by sha1' % len(items))
    print('rollback: %s' % rb)
    return 0


def rollback(a, DD):
    bk = os.path.abspath(a['rollback'])
    p = os.path.join(bk, 'install.json')
    if not os.path.isfile(p): die(3, 'no install.json in %s' % bk)
    state = json.load(open(p, encoding='utf-8'))
    if state.get('rolled_back'): die(3, 'already rolled back on %s' % state['rolled_back'])
    if os.path.normcase(os.path.abspath(state['dd'])) != os.path.normcase(os.path.abspath(DD)):
        die(3, 'backup is for %s, not %s' % (state['dd'], DD))
    print('rollback of %s (build %s, %s)' % (bk, state['build'], state['created']))
    for it in reversed(state['items']):
        if it.get('status') in (None, 'planned'): continue
        print('  %-30s %s' % (it['rel'], 'restore the backed-up copy' if it['existed'] else 'remove (was not there before)'))
    print('kl2.exe running: %s' % ('YES' if kl2_running() else 'no')); print(lock_report())
    if a['dry']: print('DRY RUN: nothing written'); return 0
    if kl2_running(): die(2, 'kl2.exe is running')
    lock = Lock('rollback')
    if not lock.take(a['wait_min']): die(2, 'GAME_LOCK not free after %d min (%s)' % (a['wait_min'], lock_report()))
    try:
        if kl2_running(): die(2, 'kl2.exe is running')
        aside = os.path.join(WORK, 'backup', 'rollback_' + time.strftime('%m%d_%H%M%S'))
        bad = undo(DD, bk, state, aside)
    finally:
        lock.release()
    print('rollback %s; what was removed from Dog Days is in %s' % ('OK' if not bad else 'with %d PROBLEM(S)' % bad, aside))
    return 0 if not bad else 5


def parse(argv):
    a = dict(out=None, levels=[], dry=False, menu=None, loader=None, movie=None, wait_min=30, rollback=None,
             allow_installed_funeral=False)
    it = iter(argv)
    for x in it:
        if x == '--dry': a['dry'] = True
        elif x == '--allow-installed-funeral': a['allow_installed_funeral'] = True
        elif x in ('--menu', '--loader', '--movie', '--rollback', '--wait-min'):
            v = next(it, None)
            if v is None: die(3, '%s needs a value' % x)
            a[x[2:].replace('-', '_')] = int(v) if x == '--wait-min' else v
        elif x.startswith('--') or x in ('-h', '/?'): print(__doc__); sys.exit(0 if x in ('--help', '-h', '/?') else 3)
        elif a['out'] is None: a['out'] = x
        else: a['levels'].append(x)
    if not a['rollback'] and not a['out']: print(__doc__); sys.exit(3)
    return a


if __name__ == '__main__':
    args = parse(sys.argv[1:])
    DD = anp_paths.game_dir('ANP_DD_GAME', anp_paths.DD_FOLDER)
    sys.exit(rollback(args, DD) if args['rollback'] else install(args, DD))
