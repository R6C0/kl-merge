#!/usr/bin/env python3
r"""
The expansion as a thing somebody installs: every Dead Men map in a folder of its own beside the stock game, a menu page
for them, a manifest, and install / uninstall. Spec, layout, what is proven and the live checks: re/expansion.md.

    python kl_expansion.py build [--out <folder>] [--maps DM01,DM03] [-j 2] [--reuse] [--hook <dinput8.dll>]
                                 [--no-hook-build] [--no-stream] [--no-share] [--no-pictures] [--no-bones]
            builds <out>\KLExpansion (default <work>\build\expansion): each map through the graft with the options
            that ran live (MAPS), for the stock slot its menu entry loads; the menu overlay (klhook\mkoverlay.py);
            the merged stream file; manifest.json. Exit code 1 when a map has a problem that is not in its 'known'
            list, a Fragile Alliance finding CRASH / BROKEN, or the menu page fails a rule. --reuse keeps a map
            that is already built in <out>. Without --hook the SHIP hook is compiled from klhook\ (build.bat, into
            <out>\_stage\hook) when the tree has none or one made from other sources. Nothing outside <out> is
            written; the game is not started.
                                 [--ready <folder>] [--prebuilt DM09=<folder>[,DM03=<folder>]]
            --ready <folder>: the four Fragile Alliance maps are NOT built here but taken from the finished folders
            <folder>\M01 M02 M03 M06 of 'kl_maps.py ready' (re\maps.md 14: voices, lightened, wardrobe); --prebuilt: any
            map from a finished folder (the owner's Retomoto build). Such a folder holds an archive built for the F01
            test slot: adopt() writes it under the map's own slot name (member and file names only) and takes the
            hook's per-map files KLWardrobe.ini / KLJoin.ini along into Maps\<id>.
    python kl_expansion.py check [<tree>]                    every file of the tree against manifest.json (sha1)
    python kl_expansion.py menu [<tree>]                     the rules of re\menus.md on the tree's Overlay\Patch01.zip
    python kl_expansion.py share [<tree>]                    what the maps have in common with their systems level
                                                             and with each other (measured; nothing is changed)
    python kl_expansion.py pictures [<out>]                  Dead Men's own menu pictures of the five maps as Dog Days
                                                             level-picture tiles + a PNG each (<out>\pictures)
    python kl_expansion.py install [<tree>] [--game <Dog Days>] [--keep-slot] [--no-hook] [--no-stream] [--link]
                                   [--replace]
    python kl_expansion.py uninstall [--game <Dog Days>] [--restore-all]
    python kl_expansion.py status [--game <Dog Days>]        what is installed, and how the folder differs from stock
    python kl_expansion.py selftest [<scratch folder>]       install / uninstall against a made-up game folder

LAYOUT (what klhook\klslot.c reads; <DD> = the folder of kl2.exe)
    <DD>\dinput8.dll                     the hook (SHIP build of klhook\build.bat); the tree carries it as Hook\dinput8.dll
    <DD>\KLHook.ini                      gets the block of KLHook.expansion.ini between two marker lines
    <DD>\KLExpansion\manifest.json       ids, names, source levels, tool commit, sha1 of every file, sizes
    <DD>\KLExpansion\KLHook.expansion.ini
    <DD>\KLExpansion\Maps\<id>\          <slot>_Main.zip (members Scenes/Locations/<slot>/<slot>_Main.*), .WHD .WAV .hti,
                                         <slot>_Main_LS.SND, <slot>_Main_LS_<Language>.WHD / .WAV; Retomoto Tower also
                                         KLJoin.ini (klhook\kljoin.c: the jump box between its two parts); a map with
                                         the wardrobe also KLWardrobe.ini (klhook\klchar.c: its model numbers)
    <DD>\KLExpansion\Overlay\Patch01.zip the stock patch archive + the page 'Dead Men maps' in menu/frontend.xml
    <DD>\KLExpansion\Overlay\PC_Def.str  the merged stream file (Dog Days' + Dead Men's streamed clips)
    <DD>\KLExpansion\BuildInfo\<id>\     graft.txt, result.json, log.txt, preflight.json of the build
    <DD>\KLExpansion\_installed\         written by install: install.json and what it replaced (KLHook.ini, dinput8.dll)
  A map is built FOR A SLOT: the engine keeps loading 'Locations/<slot>/<slot>_Main' and the hook answers the opens
  from Maps\<id> while menu page 2 is chosen ([Redirect.2]). Entry k of a page loads slot F01 F02 F03 F04 F06 F07 F05
  F08 F09 [k] (kl2 0x746570); F05, F08 and F09 are the paid DLC slots and stay untouched, so a page has six free
  entries and the five maps take the first five (MAPS).

WHAT INSTALL DOES, IN ORDER (uninstall undoes each step; both refuse while a kl2.exe with a thread exists)
    1. the tree is checked against its manifest;
    2. a KLExpansion folder that is not an install of this tool is refused, or with --replace MOVED aside
       (KLExpansion.before-N) and moved back by uninstall;
    3. the tree is copied, every file read back (sha1); --link: byte-equal files of two maps become hard links;
    4. the hook: Hook\dinput8.dll replaces <DD>\dinput8.dll, the one that was there is kept in _installed (a locked
       file is renamed aside, debug\zombies.py); without one in the tree the game's own must be a klslot build with
       menu pages (looked up by its log texts);
    5. KLHook.ini: the sections [Expansion] [Redirect*] [Page*] [Slots] of the file are replaced by the tree's block
       between marker lines; every other section stays as it is; the file as it was is kept in _installed;
    6. the F01 test slot is put back to stock by COPY from KL_PortBackup (--keep-slot: not). KL_PortBackup is only
       ever read. PC_Def.str in the game folder is left alone (--restore-all on uninstall copies every file of
       KL_PortBackup back, PC_Def.str too).

RULES KEPT: nothing is written outside <out> by build and outside --game by install; KL_PortBackup is never written,
moved or removed; no stock file is deleted - a file that is replaced is first kept. Game data never goes into the repo.
ASSUMPTIONS are marked where they are made; what no live run has shown is listed in re/expansion.md section 6.
"""
import collections, ctypes, hashlib, json, os, re, shutil, struct, subprocess, sys, time, zipfile, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

ROOT = 'KLExpansion'
STATE = '_installed'
BACKUP = 'KL_PortBackup'
ORDER = [1, 2, 3, 4, 6, 7, 5, 8, 9]            # menu entry k -> slot number (kl2 0x746570; klhook\mkoverlay.py)
DLC = (5, 8, 9)                                # slots the game unlocks by ownership (re\fa_slots.md 1): never redirected here
PAGE = 2                                       # the stock page sets the option 'Dummy' to 1, ours to 2 (klslot.c)
PAGE_TITLE = 'Dead Men maps'
JOIN_NAME = '06_Exit'                          # Retomoto: the jump point the join box sends to (kl_fa_author: Specials!JumpPoints!06_Exit)
SYSTEMS = 'F07'                                # the only systems level a Dead Men map has run under (re\maps.md 3, 10)
SIDE = ('KLJoin.ini', 'KLWardrobe.ini')        # the hook's per-map files: read beside the archive that is opened (kljoin.c, klchar.c)
READY = {'DM01': 'M01', 'DM02': 'M02', 'DM03': 'M03', 'DM06': 'M06'}   # map id -> folder of 'kl_maps.py ready' (kl_maps.READY)
BEGIN, END = '; >>> KLExpansion (kl_expansion.py install) - do not edit between these lines', '; <<< KLExpansion'
OURS = re.compile(r'(?i)^(expansion|redirect(\.\d+)?|page\.\d+|slots)$')     # the ini sections that belong to klslot.c
# log texts only a klslot build with pages has. Since 0ad48d2 klslot.c reads the page off the window stack ('menu page %d
# latched'); the build before it logged 'menu page option' and lost the page at StartGame (re\hook_live.md): not accepted.
HOOK_MARKS = (b'expansion: enabled', b'Redirect.%d', b'menu page %d latched')
MENU_EXTRA = ('KLHeister', 'KLGuns')           # windows klhook\mkoverlay.py adds beside the map page (its HEISTER, GUNS_WINDOW)
# The maps. title: Dead Men's own name (its .LOC AllLevels/Menu/Online/Scenarios/Title00..03, re\maps.md 2; the tower
# is the campaign chapter M09A's name). slot: the stock slot the build is named for = the entry of the page.
# build: 'one' = kl_maps.one(S, M) with kl_graft's defaults, 'chain' = S + M[0], then that + M[1] with the authored
# layer (kl_fa_author, exactly its test()). known: verify() problems the build is accepted with (kl_fa_author.KNOWN).
# picture: the entity of DEAD MEN's frontend scene that holds the map's menu picture (pictures()).
# extra: files of the repo that go beside the archive under another name (read by the hook from the map's folder).
# live: what has run in the game - always as an F01-named build under F07 (kl_graft's run log); the slot names F02,
# F03, F04, F06 are new with this packaging and differ from those builds in member and file names only.
# OPTIONS: what kl_graft.build is given on top of its defaults; empty = the defaults, which are what the last live
# runs of the diner, the bank and the tower were built with (2026-10-09 12:43 - 14:20: BR1, M01R, S2, J1b - J3). The
# one option that is a choice is `bones` (kl_graft's skeleton renumbering, kl_chars): on by default there since
# 12:40; the first form of it failed its own check on four maps, the committed form (names without tracks are added
# to the .ANM bone table) passes on all five. 'build --no-bones' gives the builds of before (the ones M02r / M06r
# ran). `bones_live` below says per map whether a build WITH the step has run in the game.
# An option kl_graft.build does not have (an older tool) is left out.
OPTIONS = {}
MAPS = [
    dict(id='DM01', slot='F01', title='Hot Coffee', build='one', sources=['M01_FA_A'], known=(), picture='LevelPicture_FA01', bones_live=True,
         live='direct boot and a scripted walk clean (B-4, M01c, M01W); one Arcade round from the menu, in the round for 150 s, '
              'ended by the script (M01R, a build with the skeleton step); loot and escape not played'),
    dict(id='DM02', slot='F02', title='Late Night Opening', build='one', sources=['M02_FA_A'], known=(), picture='LevelPicture_FA02', bones_live=False,
         live='direct boots clean, one Arcade round to the score page and round 2 (M02c, M02r; builds WITHOUT the skeleton step); '
              'loot and escape not played'),
    dict(id='DM03', slot='F03', title='Withdrawal', build='one', sources=['M03_FA_A'], known=(), picture='LevelPicture_FA03', bones_live=True,
         live='Arcade rounds with loot, clock and score page (RN5 - RN14; BR1 and S1 with the skeleton step); a complete round with '
              'the escape only on the build without the map\'s guards (ESC3); loaded from Maps\\DM03 through the redirect (X2, X3)'),
    dict(id='DM06', slot='F04', title='A Walk in the Park', build='one', sources=['M06_FA_A'], known=(), picture='LevelPicture_FA06', bones_live=False,
         live='direct boot clean, one Arcade round to the score page and round 2 (M06a, M06r; builds WITHOUT the skeleton step); '
              'helicopters, loot and escape not played'),
    dict(id='DM09', slot='F06', title='Retomoto Tower', build='chain', sources=['M09_B', 'M09_A'], picture='LevelPicture_M09A', bones_live=True,
         join=True,                                 # Maps\DM09\KLJoin.ini, written by join_ini() from kl_fa_author's numbers
         known=('stream clips are not in the merged stream file', 'particle template names do not resolve'),
         live='loads, both parts walked, Arcade rounds start and reach the score page (RT2b - RT6); three lost rounds to the '
              'session end with every Steam write blocked (S2); the way from the tower to the lobby by the hook\'s jump box, '
              'on a direct boot and in an Arcade round (J1b, J2, J3; the builds without the map\'s guards); no round with loot and escape'),
]


# ------------------------------------------------------------------ small things
def sha1(path, limit=None):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        left = os.path.getsize(path) if limit is None else limit
        while left > 0:
            b = f.read(min(1 << 22, left))
            if not b:
                break
            h.update(b); left -= len(b)
    return h.hexdigest()


def files_under(folder):
    """Relative paths ('/' separators) of every file below a folder, sorted."""
    out = []
    for dp, _dn, fs in os.walk(folder):
        out += [os.path.relpath(os.path.join(dp, f), folder).replace('\\', '/') for f in fs]
    return sorted(out)


def copy_checked(src, dst, want=None):
    """Copy through a temporary name in the target folder, read the copy back, then put it in place. -> its sha1."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + '.kltmp'
    shutil.copyfile(src, tmp)
    got = sha1(tmp)
    if want and got != want:
        os.remove(tmp)
        raise SystemExit('copy of %s does not read back as written (sha1 %s, expected %s)' % (src, got, want))
    os.replace(tmp, dst)
    return got


def inside(path, folder):
    """True when path is the folder or lies in it (two drives have nothing in common)."""
    a, b = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(folder))
    return a == b or a.startswith(b.rstrip(os.sep + '/') + os.sep)


def default_out():
    from kl_port_check import workdir
    return os.path.join(workdir(), 'build', 'expansion')


def dog_days():
    from kl_port_check import find, DD_GUESSES, DD_EXE
    return find(DD_GUESSES, DD_EXE)


def stock_file(dd, rel):
    """A stock file of Dog Days: the copy in KL_PortBackup when the file was replaced (read only), else the game's."""
    b = os.path.join(dd, BACKUP, rel)
    return b if os.path.isfile(b) else os.path.join(dd, rel)


def tool_state():
    """Commit of the repo and what differs from it: a build is only as reproducible as the tools that made it."""
    def git(*a):
        try:
            return subprocess.run(('git', '-C', REPO) + a, capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception:
            return ''
    dirty = [l[3:] for l in git('status', '--porcelain').splitlines() if l[3:].startswith(('tools/', 'klhook/'))]
    return {'commit': git('rev-parse', 'HEAD') or None, 'branch': git('rev-parse', '--abbrev-ref', 'HEAD') or None,
            'changed_since_commit': {f: sha1(os.path.join(REPO, f)) for f in dirty if os.path.isfile(os.path.join(REPO, f))}}


def build_id(folder, slot):
    r"""One number for 'the same map build': the archive's members by name, CRC and size (not its bytes: the zip holds
    the time of the build) and the sha1 of every file beside it, named without the slot - so the same content built
    for another slot has the same id. For later online use every peer must show the same id (re\netcode.md 5: the
    game's own check knows nothing of our files). The .hti is left out (the exe never opens it)."""
    h = hashlib.sha1()
    with zipfile.ZipFile(os.path.join(folder, slot + '_Main.zip')) as z:
        for i in sorted(z.infolist(), key=lambda i: i.filename):
            h.update(('%s %08x %d\n' % (i.filename.replace('Locations/%s/%s_Main' % (slot, slot), '@'), i.CRC, i.file_size)).encode())
    for f in sorted(os.listdir(folder)):                # the files beside it, the hook's per-map files (KLJoin.ini) too
        if not f.lower().endswith(('.zip', '.hti')):
            h.update(('%s %s\n' % (f[len(slot):] if f.startswith(slot + '_Main') else f, sha1(os.path.join(folder, f)))).encode())
    return h.hexdigest()


def join_ini(log=print):
    r"""KLJoin.ini of Retomoto Tower (klhook\kljoin.c reads it beside the level archive): the jump box between the
    tower and the lobby. Written from kl_fa_author's numbers, which are the ones that ran (JOIN_BOX: runs RT4, J1b,
    J2; the box INSIDE the car that klhook\KLJoin.retomoto.ini named first is never reached - run J1), so the file
    cannot fall behind the level it belongs to. -> text."""
    import kl_fa_author as A
    (x0, x1), (y0, y1), (z0, z1) = A.JOIN_BOX
    L = ['; KLJoin.ini of Retomoto Tower: the way from the tower (M09_A) to the lobby (M09_B). Written by tools\\kl_expansion.py',
         '; from kl_fa_author.JOIN_BOX / JOIN_ENTRY / CAR_B (live: runs RT4, J1b, J2). Read by KLHook (kljoin.c) when the',
         '; archive beside it is opened; used only while that level runs and only when the jump list fits Name and Target.',
         '[Join]', 'Min=%g %g %g' % (x0, y0, z0), 'Max=%g %g %g' % (x1, y1, z1), 'Entry=%d' % A.JOIN_ENTRY, 'Name=' + JOIN_NAME,
         'Target=%g %g %g' % A.CAR_B, 'Tolerance=8']
    text = '\n'.join(L) + '\n'
    sample = os.path.join(REPO, 'klhook', 'KLJoin.retomoto.ini')
    if os.path.isfile(sample):
        keys = lambda t: sorted(l.strip() for l in t.splitlines() if '=' in l and not l.lstrip().startswith(';'))
        old = keys(open(sample).read())
        if old != keys(text):
            log('NOTE: klhook\\KLJoin.retomoto.ini does not hold kl_fa_author\'s box (it has %s); the tree gets kl_fa_author\'s' % (
                ', '.join(k for k in old if k not in keys(text))))
    return text


def hook_sources():
    r"""-> (sha1 over the sources of the SHIP hook, their names). klauto.c is the test rig and is not part of it."""
    d = os.path.join(REPO, 'klhook')
    names = sorted(f for f in os.listdir(d) if f.lower().endswith(('.c', '.h')) and f.lower() != 'klauto.c')
    h = hashlib.sha1()
    for f in names:
        h.update(('%s %s\n' % (f, sha1(os.path.join(d, f)))).encode())
    return h.hexdigest(), names


def hook_build(folder, log=print):
    r"""SHIP hook from the repo's sources by klhook\build.bat into `folder` (Visual Studio's x86 compiler).
    -> path of dinput8.dll, or None with the reason logged."""
    bat = os.path.join(REPO, 'klhook', 'build.bat')
    shutil.rmtree(folder, ignore_errors=True); os.makedirs(folder)
    try:
        r = subprocess.run(['cmd', '/c', bat, folder], capture_output=True, text=True, timeout=300)
    except Exception as x:
        log('hook: build.bat did not run: %s' % x)
        return None
    dll = os.path.join(folder, 'dinput8.dll')
    if r.returncode or not os.path.isfile(dll):
        log('hook: build.bat failed (exit %d): %s' % (r.returncode, (r.stdout + r.stderr).strip()[-400:]))
        return None
    return dll


# ------------------------------------------------------------------ build: one map (a process of its own)
def build_map(mid, stage):
    r"""Runs in a child process: the map `mid` into <stage> through kl_maps (which never writes kl_graft's own
    <work>\build\install). -> the folder that holds <slot>_Main.zip, result.json, log.txt, graft.txt."""
    import inspect
    import kl_maps as K, kl_graft
    m = next(m for m in MAPS if m['id'] == mid)
    known = inspect.signature(kl_graft.build).parameters
    opt = {k: v for k, v in OPTIONS.items() if k in known}
    if os.environ.get('KL_EXPANSION_NO_BONES') and 'bones' in known:
        opt['bones'] = False
    print('kl_expansion: options on top of kl_graft.build\'s defaults: %s' % opt)
    if m['build'] == 'one':
        r = K.one(stage, SYSTEMS, m['sources'][0], keep=True, slot=m['slot'], **opt)
        folder = os.path.join(stage, '%s+%s' % (SYSTEMS, m['sources'][0]))
    else:
        # kl_maps.chain / kl_fa_author.test with the slot's name on the second step (chain() itself has no slot
        # argument: its first step is the pseudo level R09, its second is always F01)
        m1, m2 = m['sources']
        mid_dir = os.path.join(stage, 'chain')
        r1 = K.one(mid_dir, SYSTEMS, m1, keep=True, campaign=True, slot='R09', author=True, **opt)
        if not r1['ok']:
            print('first step failed: %s' % r1.get('error'))
            return None
        K.PSEUDO['R09'] = os.path.join(mid_dir, '%s+%s' % (SYSTEMS, m1))
        tag = ' (R09 = %s+%s)' % (SYSTEMS, m1)
        r = K.one(stage, 'R09', m2, keep=True, campaign=True, heroes=False, slot=m['slot'], tag=tag, nav_base=K.nav_of('R09'), author=True, **opt)
        folder = os.path.join(stage, 'R09+%s%s' % (m2, tag))
        r['first'] = {k: r1.get(k) for k in ('problems', 'entities', 'textures', 'materials', 'sounds', 'waves', 'archive_mb', 'nav_bytes', 'fdx')}
        with open(os.path.join(folder, 'result.json'), 'w') as f:
            json.dump(r, f, indent=1)
        for f in os.listdir(K.PSEUDO['R09']):           # the first step's level is only the second step's input
            if f.startswith('R09_Main'):
                os.remove(os.path.join(K.PSEUDO['R09'], f))
    if not r.get('ok'):
        print('build failed: %s at %s' % (r.get('error'), r.get('where')))
        return None
    if m['build'] == 'one':                             # the offline checks of re\maps.md 9 on the kept build
        try:
            with open(os.path.join(folder, 'preflight.txt'), 'w') as fh:
                K.preflight(folder, m['slot'], log=lambda t: fh.write(str(t) + '\n'))
        except Exception as x:                          # preflight is a report; the verdict below does not lean on it
            print('preflight did not run: %s: %s' % (type(x).__name__, x))
    return folder


def adopt(m, src, d, info, log=print):
    r"""A FINISHED build folder as map m of the tree: `src` holds one <X>_Main.zip built for slot X (the F01 test slot
    for every kept build so far), the files beside it, the hook's per-map files (SIDE) and the build's notes. The
    archive is written again under the map's own slot name - member names and file names only, the members' bytes
    are not touched (kl_graft.member_name; packed as kl_graft.write_zip does, fixed time stamp) - into d =
    Maps\<id>, the SIDE files go with it, everything else (graft.txt, log.txt, result.json, audit.*, preflight.*,
    wardrobe.txt ...) into info = BuildInfo\<id>. `src` is only read. -> the slot the folder was built for.
    Why a rename is enough: nothing inside a level names its slot (kl_graft builds any slot from the same members;
    the engine asks for 'Locations/<slot>/<slot>_Main' and the hook answers from Maps\<id>). The model numbers in
    KLWardrobe.ini are .prm chunk indices and do not change."""
    import kl_graft
    zips = [f for f in sorted(os.listdir(src)) if f.lower().endswith('_main.zip')]
    if len(zips) != 1:
        raise SystemExit('%s: expected one *_Main.zip, found %s' % (src, zips))
    old, slot = zips[0][:-9], m['slot']
    for x in (d, info):
        shutil.rmtree(x, ignore_errors=True); os.makedirs(x)
    with zipfile.ZipFile(os.path.join(src, zips[0])) as z:
        members = [(kl_graft.member_name(n, old, slot), z.read(n)) for n in z.namelist()]
        crc = [(i.CRC, i.file_size) for i in z.infolist()]
    out = kl_graft.write_zip(os.path.join(d, slot + '_Main.zip'), members, kl_graft.load_options(''))
    with zipfile.ZipFile(out) as z:                     # read back: the same members in the same order
        if [(i.CRC, i.file_size) for i in z.infolist()] != crc or any(old + '_Main' in n for n in z.namelist() if old != slot):
            raise SystemExit('%s: the archive written for slot %s is not the folder\'s' % (m['id'], slot))
    for f in sorted(os.listdir(src)):
        p = os.path.join(src, f)
        if not os.path.isfile(p) or f == zips[0]:
            continue
        if f.startswith(old + '_Main'):
            copy_checked(p, os.path.join(d, slot + f[len(old):]))
        else:
            copy_checked(p, os.path.join(d if f in SIDE else info, f))
    if not os.path.isfile(os.path.join(info, 'result.json')):
        raise SystemExit('%s holds no result.json: not a kept build of kl_maps' % src)
    if not os.path.isfile(os.path.join(info, 'stdout.txt')) and os.path.isfile(os.path.join(info, 'log.txt')):
        shutil.copyfile(os.path.join(info, 'log.txt'), os.path.join(info, 'stdout.txt'))    # skeleton_step() reads it
    with open(os.path.join(info, 'adopted.json'), 'w') as f:
        json.dump({'from': os.path.abspath(src), 'built_for_slot': old, 'written_for_slot': slot,
                   'archive_sha1_of_the_folder': sha1(os.path.join(src, zips[0]))}, f, indent=1)
    log('%s: taken from %s (built for %s, written for %s; %s)' % (m['id'], src, old, slot, ', '.join(
        f for f in SIDE if os.path.isfile(os.path.join(d, f))) or 'no per-map hook file'))
    return old


def skeleton_step(m, info):
    """Whether this build has kl_graft's skeleton renumbering (read from the build's own log, not from an option:
    the line 'skeletons of <M>: n of n renumbered' is printed by the step), and whether such a build of this map
    has run in the game (MAPS)."""
    try:
        text = open(os.path.join(info, 'stdout.txt'), errors='replace').read()
    except OSError:
        text = ''
    done = re.findall(r'skeletons of (\S+): (\d+) of (\d+) renumbered', text)
    return {'in_this_build': bool(done), 'renumbered': {a: '%s of %s' % (b, c) for a, b, c in done},
            'ran_live_in_this_form': m['bones_live'] if done else True}


def verdict(m, res):
    """-> list of reasons the build of map m must not be shipped (empty = accepted)."""
    if not res.get('ok'):
        return ['build failed: %s' % res.get('error')]
    bad = ['problem: ' + p for p in res.get('problems', []) if not any(k in p for k in m['known'])]
    bad += ['Fragile Alliance check: ' + f for f in res.get('fa_findings', []) if f.startswith(('CRASH', 'BROKEN'))]
    return bad


def build(out=None, only=None, par=2, reuse=False, hook=None, stream=True, share_too=True, pictures_too=True, bones=True, hook_make=True, log=print,
          prebuilt=None):
    """prebuilt: {map id: finished build folder} - those maps are taken as they are (adopt()), not built."""
    out = os.path.abspath(out or default_out())
    prebuilt = dict(prebuilt or {})
    if bones:
        os.environ.pop('KL_EXPANSION_NO_BONES', None)
    else:
        os.environ['KL_EXPANSION_NO_BONES'] = '1'       # read by the child processes (build_map)
    tree, stage = os.path.join(out, ROOT), os.path.join(out, '_stage')
    dd = dog_days()
    if not dd:
        raise SystemExit('Dog Days not found (kl_port_check.DD_GUESSES)')
    if inside(out, dd):
        raise SystemExit('refusing to build inside the game folder: %s' % out)
    os.makedirs(tree, exist_ok=True); os.makedirs(stage, exist_ok=True)
    maps = [m for m in MAPS if not only or m['id'] in only]
    t0 = time.time()
    # ---- the maps, each in a process of its own, `par` at a time (a build takes 40 .. 90 s and about 3 GB of memory)
    todo, live, failed = [], [], []
    for m in maps:
        d = os.path.join(tree, 'Maps', m['id'])
        if m['id'] in prebuilt:
            adopt(m, prebuilt[m['id']], d, os.path.join(tree, 'BuildInfo', m['id']), log)
        elif reuse and os.path.isfile(os.path.join(d, m['slot'] + '_Main.zip')) and os.path.isfile(os.path.join(tree, 'BuildInfo', m['id'], 'result.json')):
            log('%s: kept (--reuse)' % m['id'])
        else:
            todo.append(m)
    while todo or live:
        while todo and len(live) < par:
            m = todo.pop(0)
            st = os.path.join(stage, m['id'])
            shutil.rmtree(st, ignore_errors=True); os.makedirs(st)
            f = open(os.path.join(stage, m['id'] + '.stdout.txt'), 'w')
            live.append((m, st, f, subprocess.Popen([sys.executable, os.path.abspath(__file__), '_map', m['id'], st], stdout=f, stderr=subprocess.STDOUT)))
            log('%s: building %s + %s for slot %s ...' % (m['id'], SYSTEMS, ' + '.join(m['sources']), m['slot']))
        time.sleep(2)
        for j in [j for j in live if j[3].poll() is not None]:
            live.remove(j); j[2].close()
            m, st = j[0], j[1]
            got = [l[8:].strip() for l in open(os.path.join(stage, m['id'] + '.stdout.txt'), errors='replace') if l.startswith('FOLDER: ')]
            if j[3].returncode or not got:
                failed.append(m['id']); log('%s: BUILD FAILED (exit %d), see %s' % (m['id'], j[3].returncode, os.path.join(stage, m['id'] + '.stdout.txt')))
                continue
            src, d, info = got[-1], os.path.join(tree, 'Maps', m['id']), os.path.join(tree, 'BuildInfo', m['id'])
            for x in (d, info):
                shutil.rmtree(x, ignore_errors=True); os.makedirs(x)
            for f in sorted(os.listdir(src)):
                os.replace(os.path.join(src, f), os.path.join(d if f.startswith(m['slot'] + '_Main') or f in SIDE else info, f))
            shutil.copyfile(os.path.join(stage, m['id'] + '.stdout.txt'), os.path.join(info, 'stdout.txt'))
            shutil.rmtree(st, ignore_errors=True)
            log('%s: built in %d s' % (m['id'], json.load(open(os.path.join(info, 'result.json'))).get('seconds', 0)))
    # ---- per map: verdict and the manifest entry
    entries, bad = [], {i: ['build failed'] for i in failed}
    for m in MAPS:
        d, info = os.path.join(tree, 'Maps', m['id']), os.path.join(tree, 'BuildInfo', m['id'])
        if not os.path.isfile(os.path.join(info, 'result.json')):
            continue
        res = json.load(open(os.path.join(info, 'result.json')))
        why = verdict(m, res)
        if m.get('join'):
            jp, keys = os.path.join(d, 'KLJoin.ini'), lambda t: sorted(l.strip() for l in t.splitlines() if '=' in l and not l.lstrip().startswith(';'))
            if m['id'] in prebuilt and os.path.isfile(jp):          # the file the folder was played with stays
                if keys(open(jp).read()) != keys(join_ini(lambda *_a: None)):
                    log('NOTE: %s: the folder\'s KLJoin.ini does not hold kl_fa_author\'s box as it is now; the folder\'s is kept' % m['id'])
            else:
                with open(jp, 'w', newline='\r\n') as f:
                    f.write(join_ini(log))
        if why:
            bad[m['id']] = why
        pre = os.path.join(info, 'preflight.json')
        pf = collections.Counter(x[0] for x in json.load(open(pre))['findings']) if os.path.isfile(pre) else None
        aud = json.load(open(os.path.join(info, 'audit.json'))) if os.path.isfile(os.path.join(info, 'audit.json')) else None
        if aud and aud.get('bad'):                      # kl_maps.audit: every checker on the finished folder
            why = why + ['audit: ' + x for x in aud['bad']]
            bad[m['id']] = why
        took = json.load(open(os.path.join(info, 'adopted.json'))) if os.path.isfile(os.path.join(info, 'adopted.json')) else None
        numbers = {k: res.get(k) for k in ('archive_mb', 'beside_mb', 'entities', 'rooms', 'textures', 'materials', 'prm_chunks', 'sounds', 'waves', 'nav_bytes')}
        # result.json is written by the graft; a finished folder was lightened and given the wardrobe after it (DM01: 336 MB
        # there, 197 MB in the tree). The sizes are read off the tree, the counts off the folder's audit where it has one.
        numbers['archive_mb'] = round(os.path.getsize(os.path.join(d, m['slot'] + '_Main.zip')) / 1e6, 1)
        numbers['beside_mb'] = round(sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)
                                         if f.startswith(m['slot'] + '_Main') and f != m['slot'] + '_Main.zip') / 1e6, 1)
        if aud:
            numbers.update({k: aud[k] for k in ('textures', 'materials', 'sounds', 'waves') if aud.get(k) is not None})
            if aud.get('prm_entries'):
                numbers['prm_chunks'] = aud['prm_entries'] - 1
        entries.append({
            'id': m['id'], 'name': m['title'], 'slot': m['slot'], 'menu_entry': ORDER.index(int(m['slot'][1:])), 'folder': 'Maps/' + m['id'],
            'scene': 'Locations/%s/%s_Main' % (m['slot'], m['slot']), 'systems_level': SYSTEMS, 'source_levels': m['sources'],
            'build': m['build'] + (' (kl_maps.one, kl_graft defaults)' if m['build'] == 'one' else ' (campaign pre-pass + kl_fa_author layer)'),
            'taken_from': took,                         # a finished folder (adopt()); None = built here by kl_graft's defaults
            'wardrobe': os.path.isfile(os.path.join(d, 'KLWardrobe.ini')),
            'audit': {k: aud.get(k) for k in ('prm_mb', 'prm_entries', 'tex_mb', 'people', 'weapons', 'fa', 'round', 'preflight')} if aud else None,
            'options': res.get('options', {}),
            'build_id': build_id(d, m['slot']), 'accepted': not why, 'not_accepted_because': why,
            'problems': res.get('problems', []), 'known_problems': list(m['known']), 'fa_check': res.get('fa', {}),
            'fa_findings': res.get('fa_findings', []), 'preflight': dict(pf) if pf else None, 'live': m['live'],
            'skeleton_step': skeleton_step(m, info),
            'extra_files': [f for f in SIDE if os.path.isfile(os.path.join(d, f))],
            'numbers': numbers,
            'bytes': sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))})
        log('%s %-20s slot %s: %s; %d problems (%d known), FA %s, %.0f MB' % (
            m['id'], m['title'], m['slot'], 'ACCEPTED' if not why else 'NOT ACCEPTED', len(res.get('problems', [])),
            len(res.get('problems', [])) - sum(w.startswith('problem') for w in why), res.get('fa', {}), entries[-1]['bytes'] / 1e6))
        for w in why:
            log('     ' + w[:200])
    # ---- the hook's ini block, the menu overlay, the stream file, the hook
    ini = os.path.join(tree, 'KLHook.expansion.ini')
    with open(ini, 'w', newline='\r\n') as f:
        f.write(ini_block(entries))
    stock_patch = stock_file(dd, 'Patch01.zip')
    r = subprocess.run([sys.executable, os.path.join(REPO, 'klhook', 'mkoverlay.py'), ini, stock_patch, tree], capture_output=True, text=True)
    log(r.stdout.rstrip() or r.stderr.rstrip())
    menu = {'ok': False, 'findings': ['mkoverlay.py failed: ' + (r.stderr or r.stdout).strip()[-300:]]} if r.returncode else menu_check(tree, stock_patch, entries, dd, log)
    menu['built_from'] = {'Patch01.zip': sha1(stock_patch)}
    merged = os.path.join(os.path.dirname(out), 'PC_Def.str') if os.path.isfile(os.path.join(os.path.dirname(out), 'PC_Def.str')) else None
    if merged is None:
        import kl_snd
        merged = kl_snd.stream_file('merged')
    stream_info = {'file': 'Overlay/PC_Def.str', 'sha1': None, 'bytes': os.path.getsize(merged) if os.path.isfile(merged) else None, 'in_tree': False}
    if os.path.isfile(merged):
        stream_info['sha1'] = sha1(merged)
        dst = os.path.join(tree, 'Overlay', 'PC_Def.str')
        if stream and not (os.path.isfile(dst) and os.path.getsize(dst) == stream_info['bytes'] and sha1(dst) == stream_info['sha1']):
            log('copying the merged stream file (%.2f GB) ...' % (stream_info['bytes'] / 1e9))
            copy_checked(merged, dst, stream_info['sha1'])
        if not stream and os.path.isfile(dst):
            os.remove(dst)
        stream_info['in_tree'] = os.path.isfile(dst)
    else:
        log('NOTE: no merged PC_Def.str in the work folder: the maps\' streamed clips (music) need one')
    hook_info = None
    hdst = os.path.join(tree, 'Hook', 'dinput8.dll')
    src_id, src_names = hook_sources()
    stamp = os.path.join(out, 'hook.json')              # which sources the DLL in the tree was compiled from (beside the tree)
    made = json.load(open(stamp)) if os.path.isfile(stamp) else {}
    if hook:
        made = {'sources': None, 'dll': sha1(hook), 'by': '--hook (sources not known)'}
    elif hook_make and not (os.path.isfile(hdst) and made.get('dll') == sha1(hdst) and made.get('sources') == src_id):
        hook = hook_build(os.path.join(stage, 'hook'), log)
        if hook:
            made = {'sources': src_id, 'dll': sha1(hook), 'by': 'klhook\\build.bat'}
            log('hook: SHIP build from klhook\\ (%d source files, %s...): %d bytes' % (len(src_names), src_id[:10], os.path.getsize(hook)))
    if hook:
        b = open(hook, 'rb').read()
        if not all(k in b for k in HOOK_MARKS):
            raise SystemExit('%s is not a klslot build with menu pages (texts %s not all found)' % (hook, HOOK_MARKS))
        copy_checked(hook, hdst)
        with open(stamp, 'w') as f:
            json.dump(made, f, indent=1)
    if os.path.isfile(hdst):
        b = open(hdst, 'rb').read()
        hook_info = {'file': 'Hook/dinput8.dll', 'sha1': hashlib.sha1(b).hexdigest(), 'bytes': len(b),
                     'test_build': b'waitwin' in b,     # a klauto script command: the TEST build must not be shipped
                     'steam_write_guard': b'SteamUserStats' in b,
                     'sources_sha1': src_id, 'source_files': src_names,
                     'built_from_these_sources': made.get('dll') == hashlib.sha1(b).hexdigest() and made.get('sources') == src_id}
        if not hook_info['built_from_these_sources']:
            log('NOTE: the hook in the tree was not compiled from the klhook\\ sources as they are now')
    # ---- pictures and the sharing measurement (reports beside the tree, not part of it)
    pics = pictures(out, log) if pictures_too else None
    if pics is None and os.path.isfile(os.path.join(out, 'pictures', 'pictures.json')):     # --no-pictures: what an earlier build made
        pics = json.load(open(os.path.join(out, 'pictures', 'pictures.json')))
    shared = share(tree, log) if share_too and entries else None
    if shared:
        with open(os.path.join(out, 'share.json'), 'w') as f:
            json.dump(shared, f, indent=1)
    # ---- manifest
    exe = os.path.join(dd, 'kl2.exe')
    man = {
        'format': 1, 'name': 'Kane & Lynch: Dead Men maps for Dog Days', 'built': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tools': tool_state(), 'root': ROOT, 'page': {'number': PAGE, 'title': PAGE_TITLE, 'option': 'Dummy'},
        'needs': {'kl2.exe': {'sha1': sha1(exe), 'bytes': os.path.getsize(exe)},
                  'systems_level': {SYSTEMS + '_Main.zip': sha1(stock_file(dd, os.path.join('Scenes', 'Locations', SYSTEMS, SYSTEMS + '_Main.zip')))},
                  'stream_file': stream_info, 'hook': hook_info or 'not in the tree: the game folder must hold a klslot build with menu pages'},
        'maps': entries, 'menu': menu, 'pictures': pics,
        'steam': ('the hook in the tree wraps SteamUserStats (klhook\\klsteam.c): uploads, stats and achievements of a redirected map are '
                  'failed. The LOCAL high-score list of the slot is still the stock map\'s (re/leaderboard.md 4.3).') if hook_info and hook_info['steam_write_guard'] else
                 ('NO STEAM GUARD in this hook: the engine files a redirected map under the stock map of its slot (leaderboard, stats, '
                  'achievements, local high scores - re/leaderboard.md 4). Never end an Arcade session on these maps: no Quit from the pause '
                  'menu, no third lost round; close the game instead.'),
        'files': {}, 'total_bytes': 0}
    for rel in files_under(tree):
        if rel == 'manifest.json' or rel.startswith(STATE + '/'):
            continue
        p = os.path.join(tree, rel)
        man['files'][rel] = {'sha1': sha1(p), 'bytes': os.path.getsize(p)}
    man['total_bytes'] = sum(v['bytes'] for v in man['files'].values())
    part = collections.Counter()
    for rel, v in man['files'].items():
        part['/'.join(rel.split('/')[:2]) if rel.startswith('Maps/') else rel.split('/')[0] if '/' in rel else '(root)'] += v['bytes']
    man['bytes_by_part'] = dict(part)
    with open(os.path.join(tree, 'manifest.json'), 'w') as f:
        json.dump(man, f, indent=1)
    log('\n%s: %d maps, %d files, %.2f GB (maps %.2f GB, overlay %.2f GB); built in %d s' % (
        tree, len(entries), len(man['files']), man['total_bytes'] / 1e9, sum(v for k, v in part.items() if k.startswith('Maps/')) / 1e9,
        part.get('Overlay', 0) / 1e9, time.time() - t0))
    ok = not bad and menu['ok'] and len(entries) == len(MAPS if not only else maps)
    log('RESULT: %s' % ('PASS' if ok else 'FAIL - ' + '; '.join(['%s: %s' % (k, v[0][:120]) for k, v in bad.items()] + menu['findings'][:3])))
    return 0 if ok else 1


def ini_block(entries):
    """The sections klslot.c and mkoverlay.py read. Only [Redirect.<PAGE>]: no rule for 'every page', so the stock
    page and a direct boot load the stock levels ([Expansion] Page=2 forces the page for a direct-boot test)."""
    L = ['[Expansion]', 'Enable=1', 'Root=' + ROOT, 'Overlay=1', 'Fallback=1', 'Log=1', '',
         '; menu page %d = the Arcade button "%s": <stock slot> = <folder under %s\\Maps>' % (PAGE, PAGE_TITLE, ROOT), '[Redirect.%d]' % PAGE]
    L += ['%s=%s' % (e['slot'], e['id']) for e in entries]
    L += ['', '[Page.%d]' % PAGE, 'Title=' + PAGE_TITLE] + ['%s=%s' % (e['slot'], e['name']) for e in entries]
    return '\n'.join(L) + '\n'


# ------------------------------------------------------------------ the menu page against re\menus.md
def frontend_names(dd):
    r"""Entity names of the frontend scene (a Graphic= value names one of them, re\menus.md 2.7)."""
    import kl_gms
    with zipfile.ZipFile(stock_file(dd, os.path.join('Scenes', 'kaneandlynch.zip'))) as z:
        raw, buf = kl_gms.unpack(z.read('Scenes/kaneandlynch.gms')), z.read('Scenes/kaneandlynch.buf')
        online = z.read('Menu/online.xml').decode('latin-1')
    names = set()
    for decl, _tid, _prio in kl_gms.entities(raw):
        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
        names.add(buf[o:buf.index(b'\0', o)].decode('latin1'))
    return names, online


def windows(xml):
    """{name: text of the <Window> element}; the file as a whole is not well-formed XML (stock: line 2661), a window is."""
    out = collections.OrderedDict()
    for m in re.finditer(r'<Window Name="([^"]+)"[^>]*>.*?</Window>', xml, re.S):
        out.setdefault(m.group(1), []).append(m.group(0))
    return out


def menu_check(tree, stock_patch, entries, dd, log=print):
    r"""The generated menu/frontend.xml against what re\menus.md establishes: nine entries per selector and per image
    list (4.3, 8.1), literal titles (2.6), graphics that exist in the frontend scene (2.7), the element table of 5096
    (2.5), unique window names, the stock map page byte for byte. -> {'ok', 'findings', numbers}."""
    import xml.etree.ElementTree as ET
    bad, note = [], []
    new = zipfile.ZipFile(os.path.join(tree, 'Overlay', 'Patch01.zip')); old = zipfile.ZipFile(stock_patch)
    if sorted(new.namelist()) != sorted(old.namelist()):
        bad.append('members differ from the stock patch archive: %s' % sorted(set(new.namelist()) ^ set(old.namelist())))
    for n in old.namelist():
        if n.lower() != 'menu/frontend.xml' and new.read(n) != old.read(n):
            bad.append('%s is not the stock member' % n)
    a, b = old.read('menu/frontend.xml').decode('latin-1'), new.read('menu/frontend.xml').decode('latin-1')
    wa, wb = windows(a), windows(b)
    name = 'HeistPlayMenu%d' % PAGE
    for k, v in wb.items():
        if len(v) > len(wa.get(k, [])) and len(v) > 1:  # stock itself holds three names twice (console alternatives)
            bad.append('window name %s is used %d times' % (k, len(v)))
    # mkoverlay.py also adds the Heister page and the Guns page unless the ini turns them off (its own check() covers
    # their rows); what this check is strict about is the MAP page and that nothing else is new
    extra = sorted((set(wb) - set(wa)) & set(MENU_EXTRA))
    if set(wb) - set(wa) - set(MENU_EXTRA) != {name}:
        bad.append('new windows %s, expected %s and at most %s' % (sorted(set(wb) - set(wa)), name, ', '.join(MENU_EXTRA)))
    if extra:
        note.append('windows beside the map page (klhook\\mkoverlay.py): ' + ', '.join(extra))
    changed = [k for k in wa if k in wb and wa[k] != wb[k]]
    if changed != ['HeistModeMenu']:
        bad.append('stock windows changed: %s (only HeistModeMenu may)' % changed)
    names, online = frontend_names(dd)
    want = {int(e['slot'][1:]): e for e in entries}
    if name in wb:
        try:
            w = ET.fromstring(wb[name][0])
        except ET.ParseError as x:
            w = None; bad.append('%s is not well-formed: %s' % (name, x))
        if w is not None:
            sel = [e for e in w.iter('GuiElement') if e.get('Type') == 'MercsLevelSelectorHeist']
            if len(sel) != 1 or sel[0].get('Option') != 'Heist_SelectedLevel':
                bad.append('%s: %d level selectors' % (name, len(sel)))
            else:
                texts = [t.get('Text') for t in sel[0].findall('Text')]
                if len(texts) != 9:
                    bad.append('%s: the selector has %d entries; nine is what the code is built for (re\\menus.md 4.3)' % (name, len(texts)))
                for k, t in enumerate(texts[:9]):
                    slot = ORDER[k]
                    exp = '%' + want[slot]['name'] if slot in want else '/Menu/Online/Scenarios/Title%02d' % slot
                    if t != exp:
                        bad.append('%s entry %d (slot F%02d): text %r, expected %r' % (name, k, slot, t, exp))
                    if slot in want and slot in DLC:
                        bad.append('%s: slot F%02d is a DLC slot and must keep its stock level' % (name, slot))
                    if slot in want and (not t[1:].isascii() or any(c in t for c in '&"<>') or len(t) > 48):
                        bad.append('%s entry %d: title %r breaks the literal-text rule' % (name, k, t))
                recv = (sel[0].get('ToggleReceivers') or '').split(',')
                togg = [e for e in w.iter('GuiElement') if e.get('Type') == 'ToggleImages' and e.get('Name') in recv]
                if len(togg) != 1 or len(togg[0].findall('Graphic')) != 9:
                    bad.append('%s: the picture toggler does not have nine pictures' % name)
                elif {g.get('Graphic') for g in togg[0].findall('Graphic')} - {e.get('Name') for e in w.iter('GuiElement')}:
                    bad.append('%s: the picture toggler names an element the page does not have' % name)
            if any(e.get('TagName') == 'HeistBriefing' for e in w.iter('GuiElement')):
                bad.append('%s still shows the stock map\'s briefing' % name)
            for e in w.iter('GuiElement'):
                g = e.get('Graphic')
                if g and e.get('Type') == 'Graphic' and g not in names:
                    bad.append('%s: Graphic="%s" is no entity of the frontend scene' % (name, g))
            used = collections.Counter(e.get('Name') for e in w.iter('GuiElement') if e.get('Name'))
            dup = [k for k, v in used.items() if v > 1]
            if dup:
                bad.append('%s: element names used twice: %s' % (name, dup))
            pics = {e.get('Name'): e.get('Graphic') for e in w.iter('GuiElement') if e.get('Type') == 'Graphic' and e.get('Template') == 'LevelPicture_T'}
            note.append('pictures of the page: ' + ', '.join('F%02d %s' % (s, pics.get('H%02d_LevelPicture' % s)) for s in ORDER if s in want))
    if 'HeistModeMenu' in wb:
        try:
            w = ET.fromstring(wb['HeistModeMenu'][0])
            btn = [e for e in w.iter('GuiElement') if e.get('Type') == 'OpenWindow' and (e.get('Window') or '').startswith('HeistPlayMenu')]
            vals = sorted((e.get('Window'), e.get('Option'), e.get('OptionValue')) for e in btn)
            if vals != [('HeistPlayMenu', 'Dummy', '1'), (name, 'Dummy', str(PAGE))]:
                bad.append('HeistModeMenu: map-page buttons %s' % vals)
            ours = [e.get('FocusGraphic') for e in btn if e.get('Window') == name]
            fg = [e.get('FocusGraphic') for e in w.iter('GuiElement') if e.get('FocusGraphic')]
            bars = [e.get('Name') for e in w.iter('GuiElement') if e.get('Template') == 'HM_FocusBar']
            if len(ours) != 1 or fg.count(ours[0]) != 1 or bars.count(ours[0]) != 1:
                bad.append('HeistModeMenu: the new button needs a focus bar of its own (%s)' % ours)
            ys = [e.get('Y') for e in w.iter('GuiElement') if e.get('Template') == 'HM_Button']
            if len(ours) == 1 and ys.count(next(e.get('Y') for e in btn if e.get('Window') == name)) != 1:
                bad.append('HeistModeMenu: the new button stands on another button')
            for e in w.iter('GuiElement'):
                if e.get('Template') == 'HM_FocusBar' and e.get('Graphic') not in names:
                    bad.append('HeistModeMenu: focus bar graphic %s is no entity of the frontend scene' % e.get('Graphic'))
        except ET.ParseError as x:
            bad.append('HeistModeMenu is not well-formed: %s' % x)
    # the element table: 5096 slots for every window, element, colour set and button graphic the manager creates
    # (kl2 0x7fad55; re\menus.md 2.5). What a tag costs is not established (templates, <Platform>), so the RAW tag
    # count is compared: the stock frontend already holds more tags than slots and runs, so only the growth counts.
    tags = lambda t: len(re.findall(r'<(?:Window|GuiElement|ColorSet|ButtonGraphic)\b', t))
    n0, n1, no = tags(a), tags(b), tags(online)
    n_extra = {k: sum(tags(t) for t in wb[k]) for k in extra}
    if n1 - n0 - sum(n_extra.values()) > 100:
        bad.append('the map page adds %d elements; more than 100 was never meant' % (n1 - n0 - sum(n_extra.values())))
    out = {'ok': not bad, 'findings': bad, 'notes': note, 'window': name, 'extra_windows': n_extra, 'elements_added': n1 - n0,
           'tags_stock_frontend': n0, 'tags_frontend': n1,
           'tags_online_xml': no, 'element_table': 5096, 'windows': len(wb), 'frontend_xml_sha1': hashlib.sha1(b.encode('latin-1')).hexdigest(),
           'entries': ['%s%s' % (want[s]['name'] if s in want else '(stock F%02d)' % s, ' [DLC slot]' if s in DLC else '') for s in ORDER]}
    log('menu page %s: %s; %d tags added to %d (frontend.xml) + %d (online.xml); table 5096, headroom not established' % (
        name, 'rules hold' if not bad else '%d FINDINGS' % len(bad), n1 - n0, n0, no))
    for x in bad:
        log('   MENU: ' + x)
    for x in note:
        log('   ' + x)
    return out


# ------------------------------------------------------------------ Dead Men's menu pictures as Dog Days tiles
def dxt1(data, w, h):
    """DXT1 -> rows of (r, g, b)."""
    px = [[(0, 0, 0)] * w for _ in range(h)]
    o = 0
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            c0, c1, bits = struct.unpack_from('<HHI', data, o); o += 8
            c = [((c >> 11) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31) for c in (c0, c1)]
            if c0 > c1:
                c += [tuple((2 * a + b) // 3 for a, b in zip(c[0], c[1])), tuple((a + 2 * b) // 3 for a, b in zip(c[0], c[1]))]
            else:
                c += [tuple((a + b) // 2 for a, b in zip(c[0], c[1])), (0, 0, 0)]
            for k in range(16):
                y, x = by + k // 4, bx + k % 4
                if y < h and x < w:
                    px[y][x] = c[(bits >> (2 * k)) & 3]
    return px


def dxt5(px, w, h):
    """rows of (r, g, b) -> DXT5 with full alpha. Per block the two colours are the ends of the brightness range
    (good enough for a menu picture; no dithering)."""
    out = bytearray()
    to565 = lambda c: ((c[0] * 31 + 127) // 255 << 11) | ((c[1] * 63 + 127) // 255 << 5) | ((c[2] * 31 + 127) // 255)
    un565 = lambda v: ((v >> 11) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31)
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            blk = [px[min(by + k // 4, h - 1)][min(bx + k % 4, w - 1)] for k in range(16)]
            lum = [2 * c[0] + 5 * c[1] + c[2] for c in blk]
            c0, c1 = to565(blk[lum.index(max(lum))]), to565(blk[lum.index(min(lum))])
            if c0 < c1:
                c0, c1 = c1, c0
            if c0 == c1:
                bits = 0
            else:
                a, b = un565(c0), un565(c1)
                pal = [a, b, tuple((2 * x + y) // 3 for x, y in zip(a, b)), tuple((x + 2 * y) // 3 for x, y in zip(a, b))]
                bits = 0
                for k, c in enumerate(blk):
                    d = [sum((p - q) ** 2 for p, q in zip(c, e)) for e in pal]
                    bits |= d.index(min(d)) << (2 * k)
            out += b'\xff\xff' + bytes(6) + struct.pack('<HHI', c0, c1, bits)
    return bytes(out)


def png(path, px):
    raw = b''.join(b'\0' + bytes(v for p in row for v in p) for row in px)
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', len(px[0]), len(px), 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def resize(px, w, h):
    """Bilinear to w x h."""
    sh, sw = len(px), len(px[0])
    out = []
    for y in range(h):
        fy = (y + 0.5) * sh / h - 0.5
        y0 = min(max(int(fy), 0), sh - 1); y1 = min(y0 + 1, sh - 1); ty = min(max(fy - y0, 0.0), 1.0)
        row = []
        for x in range(w):
            fx = (x + 0.5) * sw / w - 0.5
            x0 = min(max(int(fx), 0), sw - 1); x1 = min(x0 + 1, sw - 1); tx = min(max(fx - x0, 0.0), 1.0)
            a, b, c, d = px[y0][x0], px[y0][x1], px[y1][x0], px[y1][x1]
            row.append(tuple(int((a[i] * (1 - tx) + b[i] * tx) * (1 - ty) + (c[i] * (1 - tx) + d[i] * tx) * ty + 0.5) for i in range(3)))
        out.append(row)
    return out


PHOTO = (277, 169, 384, 236)            # x, y, width, height of the photograph on Dead Men's 891 x 530 sheet (photo())


def photo(px, aspect):
    """Dead Men's menu picture is a photograph on a black sheet with paint splashes; Dog Days' fills its whole
    rectangle. -> the photograph, cut to `aspect` (width / height) about its centre, and the box taken.
    PHOTO was measured on six pictures (FA01 FA02 FA03 FA06 M09A M09B): the rows in which more than 150 pixels are
    brighter than 12 are 168..405 in the four Fragile Alliance pictures (157..418 with the splashes of the M09 ones),
    the columns with more than 100 such pixels 273..662; a dark photograph (FA02) defeats a search per picture, so
    the box is fixed and a sheet of another size is refused."""
    if (len(px[0]), len(px)) != (891, 530):
        raise ValueError('the picture is %d x %d, not the 891 x 530 sheet PHOTO was measured on' % (len(px[0]), len(px)))
    x0, y0, w, h = PHOTO
    if w / h > aspect:
        cut = w - round(h * aspect); x0, w = x0 + cut // 2, w - cut
    else:
        cut = h - round(w / aspect); y0, h = y0 + cut // 2, h - cut
    return [row[x0:x0 + w] for row in px[y0:y0 + h]], (x0, y0, w, h)


def front_scene(game):
    """The frontend scene of a game: (kl_prpjoin.Scene, kl_prmgraph.Prm, kl_texmat.Tex)."""
    import kl_gms, kl_rtp, kl_texmat as T, kl_prmgraph as G, kl_prpjoin as J
    from kl_prp import Prp
    from kl_port_check import find, DM_GUESSES, DM_EXE
    if game == 'dm':
        path, stem = os.path.join(find(DM_GUESSES, DM_EXE), 'Scenes', 'KaneAndLynch.zip'), 'Scenes/KaneAndLynch'
    else:
        path, stem = stock_file(dog_days(), os.path.join('Scenes', 'kaneandlynch.zip')), 'Scenes/kaneandlynch'
    with zipfile.ZipFile(path) as z:
        prp, raw, buf = Prp(z.read(stem + '.prp')), kl_gms.unpack(z.read(stem + '.gms')), z.read(stem + '.buf')
        prm, tex = G.read(z.read(stem + '.prm'), game), T.read_tex(z.read(stem + '.TEX'))
    names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
    for decl, tid, _prio in kl_gms.entities(raw):
        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
        names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
    return J.Scene(prp, names, tids, game, 'frontend'), prm, tex


def winpic(sc, prm, tex, name):
    """A menu picture = ZWINGROUP <name> with a ZWINPIC child whose field ZWINPIC[2] is a 'winpic' chunk of the .prm:
    n tiles {centre x, centre -y, 0, 0, u, v, 0, width, height, -1}, then n sprite chunks (+4 = texture id).
    -> [(x0, y0, width, height, texture record)] of the picture's tiles, read from the files."""
    import kl_prpjoin as J
    k = next(k for k in range(1, len(sc.nodes)) if sc.names[k] == name and sc.cls(k) == 'ZWINGROUP')
    c = next(c for c in range(k, sc.end[k]) if sc.cls(c) == 'ZWINPIC')
    ch = next(struct.unpack('<I', u[0][1])[0] for _h, lab, u in J.fields(sc, c) if lab == 'ZWINPIC[2]')
    d = prm.chunks[ch]
    n = struct.unpack_from('<I', d, 0)[0]
    out = []
    for i in range(n):
        cx, cy, _a, _b, _u, _v, _c, w, h = struct.unpack_from('<9f', d, 4 + 40 * i)
        sp = struct.unpack_from('<I', d, 8 + 40 * n + 4 * i)[0]
        out.append((round(cx - w / 2), round(-cy - h / 2), round(w), round(h), tex.tex[prm.u32(sp, 4)].entry))
    return out


def pictures(out=None, log=print):
    r"""Dead Men ships a menu picture for each of its four Fragile Alliance maps and for both Retomoto chapters
    (frontend scene entities LevelPicture_FA01 / FA02 / FA03 / FA06 and LevelPicture_M09A / M09B: 891 x 530 pixels in
    nine DXT1 tiles: a photograph of about 400 x 250 on a black sheet). A Dog Days Arcade picture (LevelPicture_H01..
    H09) is 540 x 304 in six DXT5 tiles (512 + 28 wide, 256 + 32 + 16 high, in textures 512 / 32 wide), filled to the
    edge and opaque. The photograph is cut out, cut to that shape and scaled up (1.4 x, so it is softer). This writes, per map, <out>\pictures\<id>.png (to look at) and
    <id>.tiles (six texture records in Dog Days' .TEX record form, id 0, cut to the stock tiles' sizes and with the
    stock records' header fields) - what a ZWINPIC of the frontend scene needs. NOT DONE: the entity itself. A new
    LevelPicture_* needs a ZWINGROUP + ZWINPIC in Scenes\kaneandlynch.gms/.buf/.prp, a winpic and six sprite chunks in
    its .prm and six textures in its .TEX, delivered as Overlay\Scenes\kaneandlynch.zip - a graft on the frontend
    scene nobody has loaded yet. Until then the page shows the stock picture of each slot."""
    out = os.path.join(os.path.abspath(out or default_out()), 'pictures')
    os.makedirs(out, exist_ok=True)
    dm, dd = front_scene('dm'), front_scene('dd')
    ref = winpic(*dd, 'LevelPicture_H01')               # the layout and record headers every Arcade picture uses
    W, H = max(x + w for x, _y, w, _h, _e in ref), max(y + h for _x, y, _w, h, _e in ref)
    res = {'dog_days_picture': '%d x %d in %d tiles' % (W, H, len(ref)), 'maps': {}}
    for m in MAPS:
        tiles = winpic(*dm, m['picture'])
        sw, sh = max(x + w for x, _y, w, _h, _e in tiles), max(y + h for _x, y, _w, h, _e in tiles)
        px = [[(0, 0, 0)] * sw for _ in range(sh)]
        for x0, y0, w, h, e in tiles:
            size, f1, _f2, _id, th, tw, mips, _fl = struct.unpack_from('<I4s4sIHHII', e, 0)
            if f1 != b'1TXD':
                raise ValueError('%s: a tile is %r, not DXT1' % (m['picture'], f1))
            p = e.index(b'\0', 36) + 1
            n = struct.unpack_from('<I', e, p)[0]
            t = dxt1(e[p + 4:p + 4 + n], tw, th)
            for y in range(min(h, th)):
                px[y0 + y][x0:x0 + w] = t[y][:w]
        cut, box = photo(px, W / H)                         # the photograph alone, in the Arcade picture's shape
        small = resize(cut, W, H)
        png(os.path.join(out, m['id'] + '.png'), small)
        recs = []
        for x0, y0, w, h, e in ref:
            _size, f1, _f2, _id, th, tw, mips, _fl = struct.unpack_from('<I4s4sIHHII', e, 0)
            if f1 != b'5TXD' or mips != 1:
                raise ValueError('the stock Arcade picture is not single-mip DXT5 any more')
            t = [[small[min(y0 + y, H - 1)][min(x0 + x, W - 1)] for x in range(tw)] for y in range(th)]      # edge pixels repeated into the padding
            data = dxt5(t, tw, th)
            p = e.index(b'\0', 36) + 1
            body = bytearray(e[:p]) + struct.pack('<I', len(data)) + data
            struct.pack_into('<I', body, 0, len(body)); struct.pack_into('<I', body, 12, 0)
            if len(body) != len(e):
                raise ValueError('tile record size %d, stock %d' % (len(body), len(e)))
            recs.append(bytes(body))
        with open(os.path.join(out, m['id'] + '.tiles'), 'wb') as f:
            f.write(struct.pack('<I', len(recs)) + b''.join(struct.pack('<I', len(r)) + r for r in recs))
        res['maps'][m['id']] = {'from': 'Dead Men frontend scene, ' + m['picture'], 'source': '%d x %d, %d DXT1 tiles' % (sw, sh, len(tiles)), 'photograph': 'x %d y %d, %d x %d' % box,
                                'png': m['id'] + '.png', 'tiles': m['id'] + '.tiles', 'shown_in_menu': 'no: stock picture of slot %s (LevelPicture_H%s)' % (m['slot'], m['slot'][1:])}
        log('picture %s: %s %d x %d, photograph %d x %d at (%d, %d) -> %d x %d, %d DXT5 tiles' % (m['id'], m['picture'], sw, sh, box[2], box[3], box[0], box[1], W, H, len(recs)))
    with open(os.path.join(out, 'pictures.json'), 'w') as f:
        json.dump(res, f, indent=1)
    return res


# ------------------------------------------------------------------ what the maps share
def level_parts(zp):
    """What a level archive's two large members hold, by reference: vertex / index bytes of the .prm that no root of
    the level reaches (the systems level's own map models; kl_graft empties them only above PRM_LIMIT), and the
    textures no reached material, sprite, font or HUD picture names. The second is an UPPER bound of what is dead:
    some UI textures have no known referrer (kl_texmat) - share() measures the stock level the same way to say how
    many. -> numbers, and under '_tex' '_prm' '_named' the parsed files and the set of named texture ids."""
    import kl_fa, kl_gms, kl_scene, kl_prmgraph as G, kl_texmat as T, kl_prpjoin as J
    sc, _snd, _loc = kl_fa.load(zp)
    with zipfile.ZipFile(zp) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        prm, mat, tex = G.read(z.read(m['.prm']), 'dd'), T.read_mat(z.read(m['.MAT'])), T.read_tex(z.read(m['.TEX']))
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
    live = [(c, k) if k else c for _w, c, k in G.prp_roots(sc.p, sc.tids, J.schema('dd'), 'dd')] + [e.model for e in scene.entities() if e.model]
    kinds, args = G.walk(prm, live)
    dead = sum(len(prm.chunks[i]) for i, k in G.orphans(prm, kinds).items() if k in ('dead:vtx', 'dead:idx') and len(prm.chunks[i]) > 16)
    mats, texs = set(), set()
    for i, k in kinds.items():
        for off, typ, _t in G.fields(prm, i, k, args.get(i, 0)):
            if typ == 'm':
                mats.add(prm.u16(i, off))
            elif typ in 'tT':
                texs.add(prm.u32(i, off) % 4096)
    texs |= set(T.used_textures(mat, [x for x in mats if x in mat.insts]))
    for k in range(1, len(sc.nodes)):                   # the HUD's 200 pictures (.prp ZOnScreenDisplay2 field 7, kl_texmat)
        if sc.cls(k) == 'ZOnScreenDisplay2':
            for _h, lab, u in J.fields(sc, k):
                if lab == 'ZOnScreenDisplay2[7]':
                    texs |= {v for _op, pl in u for v in struct.unpack('<%dI' % (len(pl) // 4), pl[:len(pl) // 4 * 4]) if 128 <= v < 4096}
    grow = True
    while grow:                                         # animated textures name their frames
        more = {f for t in texs if t in tex.tex and tex.tex[t].frames for f in tex.tex[t].frames} - texs
        grow = bool(more); texs |= more
    return {'prm_bytes': sum(len(c) for c in prm.chunks if c), 'prm_dead_vertex_bytes': dead,
            'tex_bytes': sum(tex_size(x) for x in tex.tex.values()), 'tex_unnamed_bytes': sum(tex_size(x) for t, x in tex.tex.items() if t not in texs),
            'textures': len(tex.tex), 'textures_unnamed': sum(t not in texs for t in tex.tex), '_tex': tex, '_prm': prm, '_named': texs, '_live': live}


def tex_size(x):
    return len(x.entry) + sum(len(f) for f in x.faces or ())


def packed(parts):
    """Bytes these pieces take in the archive: deflate level 1, as kl_graft writes its members, each piece by itself
    (a texture or a chunk compressed alone comes out a little larger than inside its member: the window is 32 KB
    and a piece is seldom smaller, so the sum over a whole member is within a few percent of the member's packed
    size - share() prints both so the error can be read off)."""
    n = 0
    for b in parts:
        c = zlib.compressobj(1, zlib.DEFLATED, -15)
        n += len(c.compress(b)) + len(c.flush())
    return n


def tex_bytes(x):
    return [bytes(x.entry)] + [bytes(f) for f in x.faces or ()]


def share(tree, log=print):
    """MEASURES, changes nothing. Per map: how much of its .TEX and .prm is the systems level's own data (textures
    by content, .prm chunks by index and content - S is the base of both id spaces, kl_graft), how much of that no
    reference of the joined level reaches, which archive members are S's stock members byte for byte, and which
    files beside the archives are equal between maps. The stock systems level is measured the same way: what is
    'unnamed' there is the floor of the method, not dead data."""
    dd = dog_days()
    szip = stock_file(dd, os.path.join('Scenes', 'Locations', SYSTEMS, SYSTEMS + '_Main.zip'))
    with zipfile.ZipFile(szip) as z:
        base = {n.replace('Locations/%s/%s_Main' % (SYSTEMS, SYSTEMS), '@'): z.getinfo(n).CRC for n in z.namelist()}
    st = level_parts(szip)
    s_tex, s_prm, s_named = st.pop('_tex'), st.pop('_prm'), st.pop('_named'); st.pop('_live')
    skeys = {x.key() for x in s_tex.tex.values()} - {None}
    floor = {x.key() for t, x in s_tex.tex.items() if t not in s_named} - {None}     # unnamed in the stock level itself: NOT dead
    out = {'systems_level': SYSTEMS, 'systems_archive_bytes': os.path.getsize(szip), 'systems_level_parts': st, 'maps': {}, 'beside': {}}
    log('share: stock %s: archive %.0f MB; .TEX %.0f MB, of it %.0f MB (%d textures) named by nothing this method knows; .prm %.0f MB, %.1f MB unreached vertex data' % (
        SYSTEMS, os.path.getsize(szip) / 1e6, st['tex_bytes'] / 1e6, st['tex_unnamed_bytes'] / 1e6, st['textures_unnamed'], st['prm_bytes'] / 1e6, st['prm_dead_vertex_bytes'] / 1e6))
    by_hash = collections.defaultdict(list)
    for m in MAPS:
        d = os.path.join(tree, 'Maps', m['id'])
        zp = os.path.join(d, m['slot'] + '_Main.zip')
        if not os.path.isfile(zp):
            continue
        with zipfile.ZipFile(zp) as z:
            rows = {i.filename.replace('Locations/%s/%s_Main' % (m['slot'], m['slot']), '@'): {'bytes': i.file_size, 'packed': i.compress_size, 'crc': i.CRC} for i in z.infolist()}
        for k, r in rows.items():
            r['stock_member'] = base.get(k) == r.pop('crc')
        for f in sorted(os.listdir(d)):
            if not f.endswith('.zip'):
                by_hash[(f[len(m['slot']):], sha1(os.path.join(d, f)))].append((m['id'], os.path.getsize(os.path.join(d, f))))
        try:
            import kl_prmgraph as G
            r = level_parts(zp)
            tex, prm, named = r.pop('_tex'), r.pop('_prm'), r.pop('_named')
            mine = {t for t, x in tex.tex.items() if x.key() in skeys}
            r['tex_systems_bytes'] = sum(tex_size(tex.tex[t]) for t in mine)
            r['tex_systems_unnamed_bytes'] = sum(tex_size(tex.tex[t]) for t in mine if t not in named)
            r['tex_map_bytes'] = r['tex_bytes'] - r['tex_systems_bytes']
            n = len(s_prm.chunks)
            r['prm_systems_bytes'] = sum(len(c) for i, c in enumerate(prm.chunks[:n]) if c and c == s_prm.chunks[i])
            r['prm_systems_emptied_bytes'] = sum(len(s_prm.chunks[i]) - 16 for i, c in enumerate(prm.chunks[:n]) if c and c != s_prm.chunks[i] and c == bytes(16))
            r['prm_map_bytes'] = sum(len(c) for c in prm.chunks[n:] if c)
            # packed size goes with unpacked size per member (the archive is deflate level 1): an estimate
            ratio = lambda e: next(v['packed'] / max(v['bytes'], 1) for k, v in rows.items() if k.endswith('@' + e))
            r['could_go_packed_estimate'] = int((r['tex_systems_unnamed_bytes'] - st['tex_unnamed_bytes']) * ratio('.TEX') + r['prm_dead_vertex_bytes'] * ratio('.prm'))
            # the same MEASURED: every texture and every chunk deflated by itself at the archive's level (packed())
            pk = lambda ts: packed(b for t in ts for b in tex_bytes(tex.tex[t]))
            gone = {t for t in mine if t not in named and tex.tex[t].key() not in floor}
            kinds, _a = G.walk(prm, r.pop('_live'))
            deadc = [i for i, k in G.orphans(prm, kinds).items() if k in ('dead:vtx', 'dead:idx') and len(prm.chunks[i]) > 16]
            deads = set(deadc)
            r['packed'] = {
                'tex_member': next(v['packed'] for k, v in rows.items() if k.endswith('@.TEX')), 'tex_sum_of_pieces': pk(tex.tex),
                'tex_systems_dead': pk(gone), 'tex_systems_live': pk(mine - gone), 'tex_map': pk(set(tex.tex) - mine),
                'prm_member': next(v['packed'] for k, v in rows.items() if k.endswith('@.prm')), 'prm_sum_of_pieces': packed(c for c in prm.chunks if c),
                'prm_systems_dead': packed(prm.chunks[i] for i in deadc if i < n),
                'prm_systems_live': packed(c for i, c in enumerate(prm.chunks[:n]) if c and i not in deads),
                'prm_map': packed(c for c in prm.chunks[n:] if c),
                'other_members': sum(v['packed'] for k, v in rows.items() if not k.endswith(('@.TEX', '@.prm'))),
                'other_members_systems': sum(v['packed'] for k, v in rows.items() if k.endswith(('@.ANM', '@.fxc')))}
            q = r['packed']
            r['could_go_packed'] = q['tex_systems_dead'] + q['prm_systems_dead']
            r['systems_live_packed'] = q['tex_systems_live'] + q['prm_systems_live'] + q['other_members_systems']
        except Exception as x:                          # a report; a level the walk refuses is said so
            r = {'error': '%s: %s' % (type(x).__name__, x)}
        out['maps'][m['id']] = {'archive_bytes': os.path.getsize(zp), 'unpacked_bytes': sum(v['bytes'] for v in rows.values()),
                                'stock_members_packed': sum(v['packed'] for v in rows.values() if v['stock_member']), 'members': rows, 'parts': r}
        if 'error' in r:
            log('share %s: %s' % (m['id'], r['error']))
            continue
        q = r['packed']
        log('share %s packed (measured, piece by piece; members are %.0f + %.0f MB, the pieces sum to %.0f + %.0f): %s\'s dead map %.0f MB '
            '(.TEX %.0f, .prm %.0f), %s\'s live systems %.0f MB (.TEX %.0f, .prm %.0f, .ANM + .fxc %.0f), the Dead Men map %.0f MB (.TEX %.0f, .prm %.0f)' % (
                m['id'], q['tex_member'] / 1e6, q['prm_member'] / 1e6, q['tex_sum_of_pieces'] / 1e6, q['prm_sum_of_pieces'] / 1e6, SYSTEMS, r['could_go_packed'] / 1e6,
                q['tex_systems_dead'] / 1e6, q['prm_systems_dead'] / 1e6, SYSTEMS, r['systems_live_packed'] / 1e6, q['tex_systems_live'] / 1e6, q['prm_systems_live'] / 1e6,
                q['other_members_systems'] / 1e6, (q['tex_map'] + q['prm_map']) / 1e6, q['tex_map'] / 1e6, q['prm_map'] / 1e6))
        log('share %s: archive %.0f MB. .TEX %.0f MB = %s\'s %.0f (unnamed %.0f) + the map\'s %.0f; .prm %.0f MB = %s\'s %.0f (unreached vertex data %.0f, emptied %.0f) + the map\'s %.0f; '
            'about %.0f MB of the archive is %s\'s own map' % (
                m['id'], os.path.getsize(zp) / 1e6, r['tex_bytes'] / 1e6, SYSTEMS, r['tex_systems_bytes'] / 1e6, r['tex_systems_unnamed_bytes'] / 1e6, r['tex_map_bytes'] / 1e6,
                r['prm_bytes'] / 1e6, SYSTEMS, r['prm_systems_bytes'] / 1e6, r['prm_dead_vertex_bytes'] / 1e6, r['prm_systems_emptied_bytes'] / 1e6, r['prm_map_bytes'] / 1e6,
                r['could_go_packed_estimate'] / 1e6, SYSTEMS))
    dup = 0
    for (suffix, h), who in sorted(by_hash.items()):
        if len(who) > 1:
            out['beside'][suffix] = {'sha1': h, 'maps': [w[0] for w in who], 'bytes_each': who[0][1], 'saved_by_linking': who[0][1] * (len(who) - 1)}
            dup += who[0][1] * (len(who) - 1)
    out['beside_saved_by_linking'] = dup
    out['could_go_packed_estimate'] = sum(v['parts'].get('could_go_packed_estimate', 0) for v in out['maps'].values())
    out['could_go_packed'] = sum(v['parts'].get('could_go_packed', 0) for v in out['maps'].values())
    out['systems_live_packed'] = sum(v['parts'].get('systems_live_packed', 0) for v in out['maps'].values())
    log('share: MEASURED packed: %s\'s dead map %.0f MB over the maps; %s\'s live systems %.0f MB over the maps (one copy would do if a level could be read from two archives)' % (
        SYSTEMS, out['could_go_packed'] / 1e6, SYSTEMS, out['systems_live_packed'] / 1e6))
    log('share: files beside the archives equal in two or more maps: %d kinds, %.0f MB saved by hard links (install --link)' % (len(out['beside']), dup / 1e6))
    log('share: %s\'s own map in the five archives: about %.0f MB packed (an estimate; nothing was removed)' % (SYSTEMS, out['could_go_packed_estimate'] / 1e6))
    return out


# ------------------------------------------------------------------ check a tree
def check(tree, log=print, quiet=False):
    """Every file of the tree against manifest.json. -> the manifest; SystemExit when a file is missing or differs."""
    mp = os.path.join(tree, 'manifest.json')
    if not os.path.isfile(mp):
        raise SystemExit('%s holds no manifest.json: not an expansion tree' % tree)
    man = json.load(open(mp))
    bad = []
    for rel, v in man['files'].items():
        p = os.path.join(tree, rel)
        if not os.path.isfile(p):
            bad.append('missing: ' + rel)
        elif os.path.getsize(p) != v['bytes'] or sha1(p) != v['sha1']:
            bad.append('differs: ' + rel)
    extra = [r for r in files_under(tree) if r not in man['files'] and r != 'manifest.json' and not r.startswith(STATE + '/')]
    if not quiet:
        log('%s: %d files, %.2f GB, built %s, tools %s%s' % (tree, len(man['files']), man['total_bytes'] / 1e9, man['built'], (man['tools']['commit'] or '?')[:10],
                                                               ' + %d changed files' % len(man['tools']['changed_since_commit']) if man['tools']['changed_since_commit'] else ''))
        for e in man['maps']:
            log('  %s %-20s slot %s entry %d  %s  build id %s  %.0f MB' % (e['id'], e['name'], e['slot'], e['menu_entry'], 'accepted' if e['accepted'] else 'NOT ACCEPTED', e['build_id'][:12], e['bytes'] / 1e6))
        for r in extra:
            log('  not in the manifest: ' + r)
    if bad:
        raise SystemExit('the tree does not match its manifest:\n  ' + '\n  '.join(bad[:20]))
    return man


# ------------------------------------------------------------------ the game folder
def running(name='kl2.exe'):
    r"""[(pid, threads)] of every process of that name. An entry with 0 threads is not a running game: it is the
    snapshot Windows Error Reporting keeps of a crashed run (debug\zombies.py) - it cannot be ended and only locks
    dinput8.dll."""
    class PE(ctypes.Structure):
        _fields_ = [('dwSize', ctypes.c_ulong), ('cntUsage', ctypes.c_ulong), ('pid', ctypes.c_ulong), ('heap', ctypes.c_void_p), ('mod', ctypes.c_ulong),
                    ('threads', ctypes.c_ulong), ('ppid', ctypes.c_ulong), ('pri', ctypes.c_long), ('flags', ctypes.c_ulong), ('exe', ctypes.c_char * 260)]
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    k.Process32First.argtypes = k.Process32Next.argtypes = [ctypes.c_void_p, ctypes.POINTER(PE)]
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    snap = k.CreateToolhelp32Snapshot(2, 0)
    if not snap or snap == ctypes.c_void_p(-1).value:
        raise OSError('CreateToolhelp32Snapshot failed')
    e, out = PE(), []
    e.dwSize = ctypes.sizeof(PE)
    ok = k.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.exe.decode('mbcs', 'replace').lower() == name.lower():
            out.append((e.pid, e.threads))
        ok = k.Process32Next(snap, ctypes.byref(e))
    k.CloseHandle(snap)
    return out


def guard(game, log=print):
    """The folder is a Dog Days folder and no game is running. -> absolute path."""
    game = os.path.abspath(game or dog_days() or '')
    if not os.path.isfile(os.path.join(game, 'kl2.exe')):
        raise SystemExit('%s holds no kl2.exe: not a Dog Days folder' % game)
    procs = running()
    alive = [p for p in procs if p[1] > 0]
    if alive:
        raise SystemExit('kl2.exe is running (pid %s): close the game first. Nothing was changed.' % ', '.join(str(p[0]) for p in alive))
    if procs:
        log('note: %d kl2.exe entries without a thread (crash snapshots Windows keeps, debug\\zombies.py): not a running game' % len(procs))
    return game


def restore_stock(game, everything=False, log=print):
    """Stock files back BY COPY from KL_PortBackup, which is only read: the F01 test slot, or with everything=True
    every file the backup holds (PC_Def.str too). A file that already equals its backup is left alone. -> files copied."""
    broot = os.path.join(game, BACKUP)
    sub = broot if everything else os.path.join(broot, 'Scenes', 'Locations', 'F01')
    done = []
    if not os.path.isdir(sub):
        log('stock slot: %s has nothing for it - the slot was never replaced' % BACKUP)
        return done
    for rel in files_under(sub):
        rel = os.path.relpath(os.path.join(sub, rel), broot)
        src, dst = os.path.join(broot, rel), os.path.join(game, rel)
        if os.path.isfile(dst) and os.path.getsize(dst) == os.path.getsize(src) and sha1(dst) == sha1(src):
            continue
        copy_checked(src, dst, sha1(src))
        done.append(rel.replace('\\', '/'))
    log('stock files copied back from %s: %d%s' % (BACKUP, len(done), ' (%s)' % ', '.join(done[:4]) + (' ...' if len(done) > 4 else '') if done else ' (all were stock already)'))
    # A test build's per-map hook files must not stay beside the STOCK archive: klchar.c (klc_level_open) reads
    # KLWardrobe.ini beside ANY archive the game opens and would hand stock Subway the model numbers of the build that
    # was there (kljoin.c ignores its file beside a stock archive, verdict 1; it goes aside all the same). Renamed, not
    # deleted: the hook looks for the exact names. They are not in `done`: nothing of KL_PortBackup replaced them.
    slot = os.path.join(game, 'Scenes', 'Locations', 'F01')
    for f in SIDE:
        p, n = os.path.join(slot, f), 0
        if os.path.isfile(p):
            while os.path.exists('%s.of-test-build-%d' % (p, n)):
                n += 1
            os.rename(p, '%s.of-test-build-%d' % (p, n))
            log('test slot: %s of the build that was there is set aside as %s.of-test-build-%d (the archive beside it is stock now)' % (f, f, n))
    return done


def ini_sections(text):
    """[(section name or None, [lines])] of an ini text, in order; lines before the first header belong to None."""
    out = [(None, [])]
    for line in text.splitlines():
        m = re.match(r'\s*\[([^\]]+)\]', line)
        if m:
            out.append((m.group(1).strip(), [line]))
        else:
            out[-1][1].append(line)
    return out


def ini_without_ours(text):
    """The ini text without our marked block and without any section klslot.c reads (they would fight the block)."""
    text = re.sub(r'(?ms)^%s.*?^%s[^\n]*\n?' % (re.escape(BEGIN), re.escape(END)), '', text)
    keep = [l for name, lines in ini_sections(text) if not (name and OURS.match(name)) for l in lines]
    while keep and not keep[-1].strip():
        keep.pop()
    return '\n'.join(keep) + ('\n' if keep else '')


def ini_merge(text, block):
    rest = ini_without_ours(text)
    return rest + ('\n' if rest else '') + BEGIN + '\n' + block.rstrip('\n') + '\n' + END + '\n'


def put_dll(src, dst, log=print):
    """Copy the hook in. A dinput8.dll some crash snapshot still has mapped cannot be overwritten or deleted, but it
    can be renamed: it is moved aside as dinput8.dll.locked-N (delete those after a reboot)."""
    try:
        copy_checked(src, dst)
    except PermissionError:
        n = 0
        while os.path.exists('%s.locked-%d' % (dst, n)):
            n += 1
        os.rename(dst, '%s.locked-%d' % (dst, n))
        log('dinput8.dll is locked (a crash snapshot keeps it mapped): moved aside as %s' % os.path.basename('%s.locked-%d' % (dst, n)))
        copy_checked(src, dst)


def install(tree=None, game=None, keep_slot=False, use_hook=True, use_stream=True, link=False, replace=False, log=print):
    tree = os.path.abspath(tree or os.path.join(default_out(), ROOT))
    game = guard(game, log)
    if inside(tree, game):
        raise SystemExit('the tree to install lies inside the game folder')
    man = check(tree, log)
    refused = [e['id'] for e in man['maps'] if not e['accepted']]
    if refused:
        raise SystemExit('maps %s were not accepted by the build: not installed' % ', '.join(refused))
    dst, st = os.path.join(game, ROOT), os.path.join(game, ROOT, STATE)
    state = {'installed': time.strftime('%Y-%m-%d %H:%M:%S'), 'manifest_built': man['built'], 'files': [], 'aside': None, 'ini': None, 'dll': None, 'slot': [], 'linked': 0}
    old = json.load(open(os.path.join(st, 'install.json'))) if os.path.isfile(os.path.join(st, 'install.json')) else None
    if os.path.isdir(dst) and not old:
        if not replace:
            raise SystemExit('%s exists and is not an install of this tool (no %s\\install.json). --replace moves it aside as %s.before-N; nothing was changed.' % (dst, STATE, ROOT))
        n = 0
        while os.path.exists('%s.before-%d' % (dst, n)):
            n += 1
        os.rename(dst, '%s.before-%d' % (dst, n))
        state['aside'] = '%s.before-%d' % (ROOT, n)
        log('existing %s moved aside as %s (uninstall moves it back)' % (ROOT, state['aside']))
    if old:                                             # an update: what the earlier install put there and this tree lacks goes
        state.update({k: old.get(k) for k in ('aside', 'ini', 'dll')})
        for rel in old.get('files', []):
            if rel not in man['files'] and rel != 'manifest.json' and os.path.isfile(os.path.join(dst, rel)):
                os.remove(os.path.join(dst, rel))
    os.makedirs(st, exist_ok=True)
    # ---- the tree
    todo = [r for r in man['files'] if not r.startswith('Hook/') and (use_stream or r != 'Overlay/PC_Def.str')]
    seen = {}
    for rel in todo:
        v, p = man['files'][rel], os.path.join(dst, rel)
        twin = seen.get(v['sha1']) if link and rel.startswith('Maps/') and v['bytes'] > 65536 else None
        if twin:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if os.path.exists(p):
                os.remove(p)
            try:
                os.link(os.path.join(dst, twin), p); state['linked'] += 1
            except OSError:
                twin = None
        if not twin and not (os.path.isfile(p) and os.path.getsize(p) == v['bytes'] and sha1(p) == v['sha1']):
            copy_checked(os.path.join(tree, rel), p, v['sha1'])
        seen.setdefault(v['sha1'], rel)
        state['files'].append(rel)
    shutil.copyfile(os.path.join(tree, 'manifest.json'), os.path.join(dst, 'manifest.json'))
    state['files'].append('manifest.json')
    log('%d files in %s (%.2f GB%s)' % (len(todo), dst, sum(man['files'][r]['bytes'] for r in todo) / 1e9, ', %d as hard links' % state['linked'] if state['linked'] else ''))
    # ---- the hook
    dll, new = os.path.join(game, 'dinput8.dll'), os.path.join(tree, 'Hook', 'dinput8.dll')
    if use_hook and os.path.isfile(new):
        want = man['files']['Hook/dinput8.dll']['sha1']
        if not (os.path.isfile(dll) and sha1(dll) == want):
            if state['dll'] is None:
                state['dll'] = {'existed': os.path.isfile(dll), 'before': sha1(dll) if os.path.isfile(dll) else None, 'ours': want}
                if os.path.isfile(dll):
                    shutil.copyfile(dll, os.path.join(st, 'dinput8.dll.before'))
            state['dll']['ours'] = want
            put_dll(new, dll, log)
            log('hook installed (dinput8.dll %s); the one that was there is kept in %s\\%s' % (want[:10], ROOT, STATE) if state['dll']['existed'] else 'hook installed (dinput8.dll %s)' % want[:10])
    else:
        b = open(dll, 'rb').read() if os.path.isfile(dll) else b''
        if not all(k in b for k in HOOK_MARKS):
            log('WARNING: %s is %s. Without it the game is plain Dog Days and the folder %s does nothing.' % (
                dll, 'not a hook with the expansion\'s menu pages (klhook\\build.bat builds one)' if b else 'missing', ROOT))
    # ---- KLHook.ini
    ini = os.path.join(game, 'KLHook.ini')
    had = os.path.isfile(ini)
    text = open(ini, encoding='latin-1', newline='').read().replace('\r\n', '\n') if had else ''
    if state['ini'] is None:
        state['ini'] = {'existed': had, 'before': sha1(ini) if had else None}
        if had:
            shutil.copyfile(ini, os.path.join(st, 'KLHook.ini.before'))
    merged = ini_merge(text, open(os.path.join(tree, 'KLHook.expansion.ini'), encoding='latin-1', newline='').read().replace('\r\n', '\n'))
    with open(ini, 'w', encoding='latin-1', newline='\r\n') as f:
        f.write(merged)
    state['ini']['after'] = sha1(ini)
    gone = [n for n, _l in ini_sections(re.sub(r'(?ms)^%s.*?^%s[^\n]*\n?' % (re.escape(BEGIN), re.escape(END)), '', text)) if n and OURS.match(n)]
    log('KLHook.ini: the expansion\'s block %s%s' % ('added' if had else 'written (the file did not exist)',
                                                     '; its own sections %s were replaced (the file as it was: %s\\%s\\KLHook.ini.before)' % (gone, ROOT, STATE) if gone else ''))
    # ---- the test slot
    if not keep_slot:
        state['slot'] = restore_stock(game, False, log)
    with open(os.path.join(st, 'install.json'), 'w') as f:
        json.dump(state, f, indent=1)
    log('installed. In the game: Arcade Mode -> "%s". Remove with: python tools\\kl_expansion.py uninstall' % man['page']['title'])
    log('NOTE: ' + man['steam'])
    return state


def uninstall(game=None, everything=False, log=print):
    game = guard(game, log)
    dst = os.path.join(game, ROOT)
    st = os.path.join(dst, STATE)
    sp = os.path.join(st, 'install.json')
    if not os.path.isfile(sp):
        log('%s holds no install of this tool (no %s\\%s\\install.json): nothing removed' % (game, ROOT, STATE))
        restore_stock(game, everything, log)
        return None
    state = json.load(open(sp))
    # ---- KLHook.ini: back to the file it was when nobody touched it since, else only our block goes
    ini = os.path.join(game, 'KLHook.ini')
    if state.get('ini') and os.path.isfile(ini):
        before = os.path.join(st, 'KLHook.ini.before')
        if sha1(ini) == state['ini'].get('after'):
            if state['ini']['existed']:
                copy_checked(before, ini, state['ini']['before']); log('KLHook.ini: put back as it was before the install')
            else:
                os.remove(ini); log('KLHook.ini: removed (there was none before the install)')
        else:
            text = open(ini, encoding='latin-1', newline='').read().replace('\r\n', '\n')
            rest = re.sub(r'(?ms)^%s.*?^%s[^\n]*\n?' % (re.escape(BEGIN), re.escape(END)), '', text)
            if rest.strip() or state['ini']['existed']:
                with open(ini, 'w', encoding='latin-1', newline='\r\n') as f:
                    f.write(rest)
                log('KLHook.ini was edited after the install: only the expansion\'s block was taken out%s' % (
                    ' (the file from before the install: %s)' % os.path.join(game, 'KLHook.ini.before-expansion') if state['ini']['existed'] else ''))
                if state['ini']['existed']:
                    shutil.copyfile(before, os.path.join(game, 'KLHook.ini.before-expansion'))
            else:
                os.remove(ini); log('KLHook.ini: removed (nothing but the expansion\'s block was in it)')
    # ---- the hook
    dll = os.path.join(game, 'dinput8.dll')
    if state.get('dll'):
        d = state['dll']
        if os.path.isfile(dll) and sha1(dll) != d['ours']:
            log('dinput8.dll is not the one this install put there: left alone')
        elif d['existed']:
            put_dll(os.path.join(st, 'dinput8.dll.before'), dll, log); log('dinput8.dll: the one from before the install is back (%s)' % d['before'][:10])
        elif os.path.isfile(dll):
            try:
                os.remove(dll)
            except PermissionError:
                os.rename(dll, dll + '.locked-uninstalled')
                log('dinput8.dll is locked: renamed to dinput8.dll.locked-uninstalled (the game no longer loads it; delete it after a reboot)')
            else:
                log('dinput8.dll: removed (there was none before the install)')
    # ---- our files, then the folder if nothing else is in it
    for rel in state.get('files', []):
        p = os.path.join(dst, rel)
        if os.path.isfile(p):
            os.remove(p)
    shutil.rmtree(st)
    for dp, _dn, _fs in os.walk(dst, topdown=False):
        if not os.listdir(dp):
            os.rmdir(dp)
    if os.path.isdir(dst):
        left = files_under(dst)
        log('%s keeps %d files this tool did not put there (%s%s): folder left in place' % (dst, len(left), ', '.join(left[:3]), ' ...' if len(left) > 3 else ''))
    else:
        log('%s removed' % dst)
    if state.get('aside'):
        a = os.path.join(game, state['aside'])
        if os.path.isdir(a) and not os.path.exists(dst):
            os.rename(a, dst); log('%s moved back to %s' % (state['aside'], ROOT))
        elif os.path.isdir(a):
            log('%s stays beside %s (the folder could not be emptied)' % (state['aside'], ROOT))
    restore_stock(game, everything, log)
    log('uninstalled.')
    return state


def status(game=None, log=print):
    game = os.path.abspath(game or dog_days() or '')
    if not os.path.isfile(os.path.join(game, 'kl2.exe')):
        raise SystemExit('%s holds no kl2.exe' % game)
    procs = running()
    log('%s: kl2.exe %s' % (game, 'RUNNING' if any(t for _p, t in procs) else 'not running' + (' (%d thread-less entries)' % len(procs) if procs else '')))
    dst = os.path.join(game, ROOT)
    sp = os.path.join(dst, STATE, 'install.json')
    if os.path.isfile(sp):
        state, man = json.load(open(sp)), json.load(open(os.path.join(dst, 'manifest.json')))
        bad = [r for r in state['files'] if r != 'manifest.json' and (not os.path.isfile(os.path.join(dst, r)) or sha1(os.path.join(dst, r)) != man['files'][r]['sha1'])]
        log('expansion installed %s (built %s): %d files, %s' % (state['installed'], man['built'], len(state['files']), 'all as built' if not bad else '%d DIFFER or are missing: %s' % (len(bad), bad[:5])))
        for e in man['maps']:
            log('  %s %-20s Arcade page "%s" entry %d (slot %s), build id %s' % (e['id'], e['name'], man['page']['title'], e['menu_entry'], e['slot'], e['build_id'][:12]))
    elif os.path.isdir(dst):
        log('%s exists but is not an install of this tool: %s' % (ROOT, ', '.join(files_under(dst)[:6])))
    else:
        log('no %s folder' % ROOT)
    dll = os.path.join(game, 'dinput8.dll')
    b = open(dll, 'rb').read() if os.path.isfile(dll) else None
    log('dinput8.dll: %s' % ('none - plain Dog Days' if b is None else '%s, %s' % (hashlib.sha1(b).hexdigest()[:10], 'hook with expansion pages' if all(k in b for k in HOOK_MARKS) else 'NOT a hook with expansion pages')))
    ini = os.path.join(game, 'KLHook.ini')
    if os.path.isfile(ini):
        t = open(ini, encoding='latin-1').read()
        log('KLHook.ini: %s; sections %s' % ('has the expansion\'s block' if BEGIN in t else 'no block of the expansion', [n for n, _l in ini_sections(t) if n]))
    broot = os.path.join(game, BACKUP)
    diff = [r for r in (files_under(broot) if os.path.isdir(broot) else []) if not os.path.isfile(os.path.join(game, r)) or os.path.getsize(os.path.join(game, r)) != os.path.getsize(os.path.join(broot, r))
            or sha1(os.path.join(game, r)) != sha1(os.path.join(broot, r))]
    log('stock files replaced in the game folder (their originals are in %s): %s' % (BACKUP, diff or 'none'))


# ------------------------------------------------------------------ selftest on a made-up game folder
def selftest(scratch=None, log=print):
    """install / uninstall against a game folder made of dummy files. The real game folder is never named: every path
    lies under `scratch`, and running() is replaced for the 'game is running' case. -> number of failed checks."""
    import tempfile
    global running
    scratch = os.path.abspath(scratch or tempfile.mkdtemp(prefix='klexp_'))
    real = dog_days()
    if real and inside(scratch, real):
        raise SystemExit('selftest refuses a scratch folder inside the game folder')
    shutil.rmtree(scratch, ignore_errors=True)
    game, tree = os.path.join(scratch, 'game'), os.path.join(scratch, 'out', ROOT)
    fails = []

    def put(root, rel, data):
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data if isinstance(data, bytes) else data.encode())

    def snap(root, skip=()):
        return {r: sha1(os.path.join(root, r)) for r in files_under(root) if not r.startswith(skip)}

    def ok(what, cond):
        log('  %s  %s' % ('ok  ' if cond else 'FAIL', what))
        if not cond:
            fails.append(what)

    def refuses(fn, *a, **k):
        try:
            fn(*a, log=lambda *_a: None, **k)
        except SystemExit as x:
            return str(x)
        return None

    # the made-up game: a test build in the F01 slot, its stock files and a stock PC_Def.str in KL_PortBackup, an old
    # hook, an ini with sections of its own and stale expansion sections, a KLExpansion folder of earlier live tests
    put(game, 'kl2.exe', b'MZ made-up exe'); put(game, 'Patch01.zip', b'stock patch'); put(game, 'PC_Def.str', b'MERGED stream file')
    put(game, 'dinput8.dll', b'old hook without pages'); put(game, 'Scenes/Locations/F07/F07_Main.zip', b'stock F07')
    for f, stock in (('F01_Main.zip', b'STOCK F01 archive'), ('F01_Main.WAV', b'STOCK wav'), ('F01_Main_LS.SND', b'STOCK ls')):
        put(game, 'Scenes/Locations/F01/' + f, b'TEST BUILD ' + f.encode()); put(game, BACKUP + '/Scenes/Locations/F01/' + f, stock)
    put(game, 'Scenes/Locations/F01/Loader_Sequence.zip', b'stock loader (never replaced)')
    put(game, 'Scenes/Locations/F01/KLWardrobe.ini', b'[Wardrobe] of the test build'); put(game, 'Scenes/Locations/F01/KLJoin.ini', b'[Join] of the test build')
    put(game, 'Scenes/Locations/F01/F01_Main.WHD', b'stock whd, equal to its backup'); put(game, BACKUP + '/Scenes/Locations/F01/F01_Main.WHD', b'stock whd, equal to its backup')
    put(game, BACKUP + '/PC_Def.str', b'STOCK stream file')
    ini0 = '[KLHook]\r\nContinueAsserts=1\r\nMaxDumps=4\r\n[Expansion]\r\nEnable=1\r\nLog=2\r\n[Redirect]\r\nF01=DM03\r\n[Auto]\r\nEnable=0\r\n; a comment\r\n'
    put(game, 'KLHook.ini', ini0)
    put(game, ROOT + '/Maps/DM03/F01_Main.zip', b'bank build of an earlier live test')
    # the made-up tree: the layout and manifest of build(), dummy content; two maps share one _LS file
    entries = []
    for m in MAPS:
        d = 'Maps/%s/%s_Main' % (m['id'], m['slot'])
        put(tree, d + '.zip', b'archive of ' + m['id'].encode() * 9000); put(tree, d + '.WAV', b'wav of ' + m['id'].encode())
        put(tree, d + '_LS_Default.WAV', b'the same loading sound in every map' * 4000); put(tree, 'BuildInfo/%s/result.json' % m['id'], '{}')
        entries.append({'id': m['id'], 'name': m['title'], 'slot': m['slot'], 'menu_entry': ORDER.index(int(m['slot'][1:])), 'accepted': True, 'build_id': 'x' * 40, 'bytes': 1})
    put(tree, 'KLHook.expansion.ini', ini_block(entries).replace('\n', '\r\n'))
    put(tree, 'Overlay/Patch01.zip', b'patch with the page'); put(tree, 'Overlay/PC_Def.str', b'MERGED stream file')
    put(tree, 'Hook/dinput8.dll', b'new hook ' + b' '.join(HOOK_MARKS))
    man = {'format': 1, 'built': 'selftest', 'tools': {'commit': None, 'changed_since_commit': {}}, 'root': ROOT, 'page': {'number': PAGE, 'title': PAGE_TITLE},
           'maps': entries, 'steam': 'selftest', 'files': {r: {'sha1': sha1(os.path.join(tree, r)), 'bytes': os.path.getsize(os.path.join(tree, r))} for r in files_under(tree)}}
    man['total_bytes'] = sum(v['bytes'] for v in man['files'].values())
    put(tree, 'manifest.json', json.dumps(man))
    before, backup0 = snap(game), snap(os.path.join(game, BACKUP))
    quiet = lambda *_a: None

    log('1. refusals (nothing may change)')
    real_running = running
    running = lambda name='kl2.exe': [(4242, 17)]
    ok('install refuses while kl2.exe runs', 'is running' in (refuses(install, tree, game, replace=True) or ''))
    ok('uninstall refuses while kl2.exe runs', 'is running' in (refuses(uninstall, game) or ''))
    running = lambda name='kl2.exe': [(4242, 0)]        # a thread-less crash snapshot is not a running game
    ok('a KLExpansion folder of somebody else is refused without --replace', 'not an install of this tool' in (refuses(install, tree, game) or ''))
    ok('a folder without kl2.exe is refused', 'no kl2.exe' in (refuses(install, tree, os.path.join(scratch, 'out')) or ''))
    put(tree, 'Maps/DM02/F02_Main.WAV', b'tampered')
    ok('a tree that differs from its manifest is refused', 'does not match its manifest' in (refuses(install, tree, game, replace=True) or ''))
    put(tree, 'Maps/DM02/F02_Main.WAV', b'wav of DM02')
    ok('the game folder is byte for byte as before', snap(game) == before)

    log('2. install --replace --link (a thread-less kl2.exe entry exists)')
    state = install(tree, game, replace=True, link=True, log=quiet)
    dst = os.path.join(game, ROOT)
    ok('every file of the tree but Hook\\ is in KLExpansion and equal', all(sha1(os.path.join(dst, r)) == v['sha1'] for r, v in man['files'].items() if not r.startswith('Hook/')))
    ok('the earlier KLExpansion folder was moved aside whole', open(os.path.join(game, ROOT + '.before-0', 'Maps', 'DM03', 'F01_Main.zip'), 'rb').read() == b'bank build of an earlier live test')
    ok('equal files of two maps are hard links (%d)' % state['linked'], state['linked'] == len(MAPS) - 1 and os.stat(os.path.join(dst, 'Maps/DM01/F01_Main_LS_Default.WAV')).st_nlink == len(MAPS))
    ok('the hook is the tree\'s, the old one is kept', sha1(os.path.join(game, 'dinput8.dll')) == man['files']['Hook/dinput8.dll']['sha1'] and open(os.path.join(dst, STATE, 'dinput8.dll.before'), 'rb').read() == b'old hook without pages')
    t = open(os.path.join(game, 'KLHook.ini'), newline='').read()
    secs = [n for n, _l in ini_sections(t.replace('\r\n', '\n')) if n]
    ok('KLHook.ini keeps [KLHook] and [Auto], loses the stale [Redirect], gains the block: %s' % secs, secs == ['KLHook', 'Auto', 'Expansion', 'Redirect.2', 'Page.2'] and 'F01=DM03' not in t and '; a comment' in t and 'F06=DM09' in t and 'Log=2' not in t)
    ok('KLHook.ini has CRLF line ends only', '\n' not in t.replace('\r\n', ''))
    f01 = lambda f: open(os.path.join(game, 'Scenes/Locations/F01', f), 'rb').read()
    ok('the F01 slot is stock again, by copy', f01('F01_Main.zip') == b'STOCK F01 archive' and f01('F01_Main.WAV') == b'STOCK wav' and f01('Loader_Sequence.zip') == b'stock loader (never replaced)' and sorted(state['slot']) == ['Scenes/Locations/F01/F01_Main.WAV', 'Scenes/Locations/F01/F01_Main.zip', 'Scenes/Locations/F01/F01_Main_LS.SND'])
    ok('the test build\'s KLWardrobe.ini / KLJoin.ini no longer stand beside the stock archive, and are kept under another name',
       not any(os.path.exists(os.path.join(game, 'Scenes/Locations/F01', f)) for f in SIDE)
       and f01('KLWardrobe.ini.of-test-build-0') == b'[Wardrobe] of the test build' and f01('KLJoin.ini.of-test-build-0') == b'[Join] of the test build')
    ok('KL_PortBackup is untouched', snap(os.path.join(game, BACKUP)) == backup0)
    ok('PC_Def.str of the game folder is left alone', open(os.path.join(game, 'PC_Def.str'), 'rb').read() == b'MERGED stream file')
    ok('stock files outside the slot are untouched', all(snap(game)[r] == before[r] for r in ('kl2.exe', 'Patch01.zip', 'Scenes/Locations/F07/F07_Main.zip')))

    log('3. install again (an update: one map changed, one file gone from the tree)')
    put(tree, 'Maps/DM02/F02_Main.WAV', b'wav of DM02, second build'); os.remove(os.path.join(tree, 'BuildInfo/DM06/result.json'))
    man['files'] = {r: {'sha1': sha1(os.path.join(tree, r)), 'bytes': os.path.getsize(os.path.join(tree, r))} for r in files_under(tree) if r != 'manifest.json'}
    put(tree, 'manifest.json', json.dumps(man))
    state2 = install(tree, game, log=quiet)
    ok('the changed file is the new one, the dropped one is gone', open(os.path.join(dst, 'Maps/DM02/F02_Main.WAV'), 'rb').read() == b'wav of DM02, second build' and not os.path.exists(os.path.join(dst, 'BuildInfo/DM06/result.json')))
    ok('what the FIRST install replaced is still what uninstall will put back', state2['aside'] == ROOT + '.before-0' and state2['ini']['before'] == before['KLHook.ini'] and state2['dll']['before'] == before['dinput8.dll'])
    ok('KLHook.ini holds the block once', open(os.path.join(game, 'KLHook.ini')).read().count(BEGIN) == 1)

    log('4. uninstall')
    put(dst, 'KLHook_notes.txt', b'a file the player put there')
    uninstall(game, log=quiet)
    after = snap(game)
    ok('KLHook.ini is byte for byte the file from before', open(os.path.join(game, 'KLHook.ini'), 'rb').read() == ini0.encode())
    ok('dinput8.dll is the one from before', after['dinput8.dll'] == before['dinput8.dll'])
    ok('a file the player added keeps its folder; nothing of ours is left in it', files_under(dst) == ['KLHook_notes.txt'])
    os.remove(os.path.join(dst, 'KLHook_notes.txt')); os.rmdir(dst)
    ok('the folder moved aside is still there when ours could not be removed', os.path.isdir(os.path.join(game, ROOT + '.before-0')))
    os.rename(os.path.join(game, ROOT + '.before-0'), dst)
    diff = sorted(r for r in set(before) | set(snap(game)) if before.get(r) != snap(game).get(r))
    ok('the game folder differs from the start only by the F01 slot being stock and its two hook files set aside: %s' % diff,
       diff == sorted(['Scenes/Locations/F01/F01_Main.WAV', 'Scenes/Locations/F01/F01_Main.zip', 'Scenes/Locations/F01/F01_Main_LS.SND']
                      + ['Scenes/Locations/F01/' + f + x for f in SIDE for x in ('', '.of-test-build-0')]))
    ok('KL_PortBackup is untouched', snap(os.path.join(game, BACKUP)) == backup0)

    log('5. a clean game folder (no hook, no ini, no KLExpansion), the ini edited after the install, --restore-all')
    for f in ('dinput8.dll', 'KLHook.ini'):
        os.remove(os.path.join(game, f))
    shutil.rmtree(dst)
    clean = snap(game)
    install(tree, game, log=quiet)
    ok('ini written with nothing but the block', open(os.path.join(game, 'KLHook.ini')).read().startswith(BEGIN))
    with open(os.path.join(game, 'KLHook.ini'), 'a', newline='\r\n') as f:
        f.write('[KLHook]\nMaxDumps=9\n')
    uninstall(game, everything=True, log=quiet)
    ok('the player\'s later ini lines stay, the block is gone', open(os.path.join(game, 'KLHook.ini')).read().split() == ['[KLHook]', 'MaxDumps=9'])
    os.remove(os.path.join(game, 'KLHook.ini'))
    now = snap(game)
    ok('--restore-all: PC_Def.str is the stock one, by copy', open(os.path.join(game, 'PC_Def.str'), 'rb').read() == b'STOCK stream file' and snap(os.path.join(game, BACKUP)) == backup0)
    ok('otherwise the folder is the clean one: no hook, no KLExpansion', {r: h for r, h in now.items() if r != 'PC_Def.str'} == {r: h for r, h in clean.items() if r != 'PC_Def.str'})
    install(tree, game, log=quiet); uninstall(game, log=quiet)
    ok('install + uninstall on the clean folder leaves no trace', snap(game) == now)
    ok('uninstall with nothing installed changes nothing', uninstall(game, log=quiet) is None and snap(game) == now)

    running = real_running
    log('selftest in %s: %d checks failed' % (scratch, len(fails)))
    log('RESULT: %s' % ('PASS' if not fails else 'FAIL'))
    return len(fails)


def main():
    a = sys.argv[1:]
    sys.stdout.reconfigure(line_buffering=True)         # a build takes minutes: its lines must not wait in a pipe

    def opt(name, default=None):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]
            return v
        return default

    def flag(name):
        if name in a:
            a.remove(name)
            return True
        return False

    if len(a) == 3 and a[0] == '_map':
        folder = build_map(a[1], a[2])
        print('FOLDER: %s' % folder if folder else 'no build')
        sys.exit(0 if folder else 1)
    cmd = a.pop(0) if a else ''
    game, out, only, par, hook = opt('--game'), opt('--out'), opt('--maps'), int(opt('-j', 2)), opt('--hook')
    pre, ready_dir = {}, opt('--ready')
    if ready_dir:
        pre.update({i: os.path.join(ready_dir, t) for i, t in READY.items()})
    while '--prebuilt' in a:
        for w in opt('--prebuilt').split(','):
            i, _eq, folder = w.partition('=')
            pre[i] = folder
    f = {k: flag('--' + k) for k in ('reuse', 'no-stream', 'no-share', 'no-pictures', 'keep-slot', 'no-hook', 'link', 'replace', 'restore-all', 'bones', 'no-bones', 'no-hook-build')}
    if cmd == 'build':
        sys.exit(build(out, only.split(',') if only else None, par, f['reuse'], hook, not f['no-stream'], not f['no-share'], not f['no-pictures'], not f['no-bones'],
                       not f['no-hook-build'], prebuilt=pre))
    tree = os.path.join(default_out(), ROOT) if not a else a[0]
    if cmd == 'check':
        check(tree)
    elif cmd == 'menu':
        man, dd = check(tree, quiet=True), dog_days()
        sys.exit(0 if menu_check(tree, stock_file(dd, 'Patch01.zip'), man['maps'], dd)['ok'] else 1)
    elif cmd == 'share':
        r = share(tree)
        with open(os.path.join(os.path.dirname(os.path.abspath(tree)), 'share.json'), 'w') as f:
            json.dump(r, f, indent=1)
    elif cmd == 'pictures':
        pictures(a[0] if a else None)
    elif cmd == 'install':
        install(tree, game, f['keep-slot'], not f['no-hook'], not f['no-stream'], f['link'], f['replace'])
    elif cmd == 'uninstall':
        uninstall(game, f['restore-all'])
    elif cmd == 'status':
        status(game)
    elif cmd == 'selftest':
        sys.exit(1 if selftest(a[0] if a else None) else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
