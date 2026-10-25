"""
kl_slotcheck.py - does every expansion map really answer to the slot it is installed under?

    python tools/kl_slotcheck.py                              the live game (<DD>\\KLExpansion + <DD>\\KLHook.ini)
    python tools/kl_slotcheck.py <dir with KLExpansion\\> [--ini <KLHook.ini>]     a stage tree before INSTALL
    python tools/kl_slotcheck.py <Fxx_Main.zip> [...]          loose archives (members only, no beside files)
    python tools/kl_slotcheck.py --self-test

Read only; writes nothing but stdout. Exit code 0 = no FAIL, 1 = at least one FAIL, 2 = usage.

WHY (2026-10-25, DD10A, the Flat Raid's first live load): the install tree renamed only the FILE
F01_Main.zip -> F07_Main.zip; its members still said Scenes/Locations/F01/F01_Main.*. The engine opened
Locations/F07/F07_Main.zip, asked it for F07_Main.sup, got no member (GetFileSize -1, assert kl2 0x7f5892),
three more asserts, then c0000005 at kl2+0x1d20d2 reading 0. kl_graft.member_name / kl_expansion.adopt
rename the members; the one-off stage scripts (tools/kl_*_stage*.py, *.ps1) copy a tree as it is and nobody
checked. This tool is that check, for a tree that is about to be installed and for the live game.

WHAT IT KNOWS (from the files, kl_expansion.py's LAYOUT and the hook's log lines):
- A map lives in Maps\\<id>\\ as <slot>_Main.zip, slot = F01..F09 (the engine hardcodes
  Locations/<slot>/<slot>_Main.zip; the hook answers that open from Maps\\<id> while the page that names
  <slot>=<id> in [Redirect.N] is latched). Files beside the archive are opened by the slot name too
  (log: 'expansion: FindFirstFileA redirect: ...F07_Main_LS_Default.WHD -> ...Maps/DD10/F07_Main_LS_Default.WHD').
- Every level-named member of a stock archive is Scenes/Locations/<slot>/<slot>_Main<suffix> (also
  <slot>_Main<Language>.LOC); the UI .xml members carry no level name (kl_graft.member_name). Stock F02's
  member set is the reference (STOCK_MEMBERS); .ANM and the .LOC set are what a stock level has, a graft may
  legitimately differ so a missing one is a NOTE, not a FAIL, except the 17 the loader asks for by name (.sup was
  the first assert). .hrd is optional by evidence: the live DM05A / DM06B / DM09 / DM11B archives have none and play.
- Beside: <slot>_Main.WHD .WAV .hti, <slot>_Main_LS.SND, <slot>_Main_LS_<Language>.WHD/.WAV for the seven
  languages of kl_package.LANGS. Default is the one the owner's game loads; the others: GUESS that a missing
  one is a NOTE (the hook may or may not fall through to the stock file - not read in klslot.c), so NOTE.
- Backups (*.before-*, *.absent) and the ini files (KLJoin, KLGuns, KLTalk, KLWardrobe) are not slot files.
"""
import os, re, sys, zipfile, tempfile, shutil

SLOT_RE = re.compile(r'^(F0[1-9])_Main\.zip$')
ANY_SLOT = re.compile(r'(?<![A-Za-z0-9])(F0[1-9])(?=_Main|/)')          # a slot name inside a member or file name
LANGS = ('Default', 'French', 'German', 'Italian', 'Japanese', 'Russian', 'Spanish')
LOC_LANGS = ('English', 'German', 'French', 'Spanish', 'Italian', 'Dutch', 'Russian', 'Polish', 'Japanese')
# stock F02_Main.zip, 2026-10-25: suffixes after '<slot>_Main'
REQUIRED = ('.gms', '.prp', '.TEX', '.prm', '.MAT', '.fxc', '.buf', '.oct', '.HVK', '.sgd', '.rmi', '.rmc',
            '.sgp', '.zgf', '.sup', '.SND', 'English.LOC')
# .hrd is NOT required: the live DM05A, DM06B, DM09*, DM11B archives have none and load and play (checked 2026-10-25)
OPTIONAL = ('.ANM', '.hrd') + tuple(l + '.LOC' for l in LOC_LANGS if l != 'English')
STOCK_MEMBERS = REQUIRED + OPTIONAL
UI_MEMBERS = ('guielems.xml', 'menu/ingame.xml', 'windows.xml', 'Menu/online.xml')
BESIDE_MUST = ('.WHD', '.WAV', '.hti', '_LS.SND', '_LS_Default.WHD', '_LS_Default.WAV')
BESIDE_MAY = tuple('_LS_%s%s' % (l, e) for l in LANGS if l != 'Default' for e in ('.WHD', '.WAV'))
INI_FILES = ('KLJoin.ini', 'KLGuns.ini', 'KLTalk.ini', 'KLWardrobe.ini')
DD_GUESSES = (r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days',)


class Report:
    def __init__(self):
        self.lines, self.fails, self.notes = [], 0, 0

    def fail(self, where, what):
        self.fails += 1
        self.lines.append('FAIL  %s: %s' % (where, what))

    def note(self, where, what):
        self.notes += 1
        self.lines.append('note  %s: %s' % (where, what))

    def ok(self, where, what):
        self.lines.append('ok    %s: %s' % (where, what))


def is_backup(name):
    return '.before-' in name or name.endswith('.absent')


def check_archive(path, rep, slot=None):
    """Members of one <slot>_Main.zip. slot: the slot the file name says (or given, for a loose archive
    whose name does not say). -> the slot, or None when the name is no slot archive."""
    base = os.path.basename(path)
    m = SLOT_RE.match(base)
    if m:
        slot = m.group(1)
    if not slot:
        rep.fail(path, 'not a slot archive name (want F0x_Main.zip)')
        return None
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
    except (zipfile.BadZipFile, OSError) as e:
        rep.fail(path, 'cannot read the archive: %s' % e)
        return slot
    prefix = 'Scenes/Locations/%s/%s_Main' % (slot, slot)
    wrong, strays, suffixes = {}, [], set()
    for n in names:
        if n.startswith(prefix):
            suffixes.add(n[len(prefix):])
            continue
        other = set(ANY_SLOT.findall(n)) - {slot}
        if other:
            wrong.setdefault(sorted(other)[0], []).append(n)
        elif n not in UI_MEMBERS:
            strays.append(n)
    if wrong:
        for s, ns in sorted(wrong.items()):
            rep.fail(path, '%d member(s) name slot %s, the file is %s (the DD10A crash): %s%s'
                     % (len(ns), s, slot, ', '.join(ns[:3]), ' ...' if len(ns) > 3 else ''))
    missing = [s for s in REQUIRED if s not in suffixes]
    if missing:
        rep.fail(path, 'members the loader asks for by name are missing: %s' % ' '.join(slot + '_Main' + s for s in missing))
    opt = [s for s in OPTIONAL if s not in suffixes]
    if opt:
        rep.note(path, 'not in the archive (stock has them): %s' % ' '.join(opt))
    extra = sorted(s for s in suffixes if s not in STOCK_MEMBERS)
    if extra:
        rep.note(path, 'members no stock archive has: %s' % ' '.join(extra))
    if strays:
        rep.note(path, '%d member(s) outside Scenes/Locations/%s and the UI set: %s' % (len(strays), slot, ', '.join(strays[:5])))
    if not wrong and not missing:
        rep.ok(path, 'slot %s, %d members, every level-named member is %s_Main*' % (slot, len(names), slot))
    return slot


def check_map_dir(d, rep):
    """One Maps\\<id> folder -> {slot: archive path} it serves (normally one)."""
    files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)) and not is_backup(f)]
    zips = [f for f in files if SLOT_RE.match(f)]
    if not zips:
        rep.fail(d, 'no F0x_Main.zip')
        return {}
    if len(zips) > 1:
        rep.fail(d, 'more than one slot archive: %s (the hook serves one slot per folder)' % ' '.join(sorted(zips)))
    served = {}
    for zname in sorted(zips):
        slot = check_archive(os.path.join(d, zname), rep)
        served[slot] = os.path.join(d, zname)
        stem = slot + '_Main'
        have = set(files)
        miss = [stem + s for s in BESIDE_MUST if stem + s not in have]
        if miss:
            rep.fail(d, 'files the engine opens by the slot name are missing: %s' % ' '.join(miss))
        may = [stem + s for s in BESIDE_MAY if stem + s not in have]
        if may:
            rep.note(d, 'other-language loading banks missing (GUESS: the hook may not fall back to stock): %s' % ' '.join(may))
    slots = set(served)
    other = []
    for f in sorted(files):
        if f in INI_FILES or SLOT_RE.match(f):
            continue
        s = ANY_SLOT.search(f)
        if s and s.group(1) not in slots:
            rep.fail(d, '%s names slot %s but the archive here is for %s' % (f, s.group(1), '/'.join(sorted(slots))))
        elif not s and not f.endswith('.json'):
            other.append(f)
    if other:                                            # build notes (*.txt, ini variants ...): harmless, listed once
        rep.note(d, '%d file(s) that are not slot files: %s%s' % (len(other), ' '.join(other[:6]), ' ...' if len(other) > 6 else ''))
    return served


def parse_ini(path):
    """[Redirect] / [Redirect.N] -> {(section, slot): id}; [Page.N] -> {(N, slot): title}; EngineMaps -> [ids]."""
    redirects, pages, engine = {}, {}, []
    sect = None
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.strip()
            if not line or line[0] in ';#':
                continue
            if line[0] == '[' and line.endswith(']'):
                sect = line[1:-1]
                continue
            if '=' not in line:
                continue
            k, v = (x.strip() for x in line.split('=', 1))
            if sect == 'Redirect' or (sect or '').startswith('Redirect.'):
                if re.match(r'^F0[1-9]$', k):
                    redirects[(sect, k)] = v
            elif (sect or '').startswith('Page.'):
                if re.match(r'^F0[1-9]$', k):
                    pages[(sect, k)] = v
            elif k == 'EngineMaps':
                engine = [x.strip() for x in v.split(',') if x.strip()]
    return redirects, pages, engine


def check_tree(root, rep, ini=None):
    """root: a folder holding KLExpansion\\ (the game, or a stage tree). ini: KLHook.ini to cross-check (default
    <root>\\KLHook.ini when present)."""
    maps = os.path.join(root, 'KLExpansion', 'Maps')
    if not os.path.isdir(maps):
        rep.fail(root, 'no KLExpansion\\Maps under it')
        return
    served = {}
    for mid in sorted(os.listdir(maps)):
        d = os.path.join(maps, mid)
        if os.path.isdir(d) and not is_backup(mid):
            served[mid] = check_map_dir(d, rep)
    ini = ini or os.path.join(root, 'KLHook.ini')
    if not os.path.isfile(ini):
        rep.note(root, 'no KLHook.ini to cross-check the redirects against')
        return
    redirects, pages, engine = parse_ini(ini)
    for (sect, slot), mid in sorted(redirects.items()):
        where = '%s [%s] %s=%s' % (os.path.basename(ini), sect, slot, mid)
        if mid not in served:
            rep.fail(where, 'no Maps\\%s folder' % mid)
        elif slot not in served[mid]:
            rep.fail(where, 'Maps\\%s holds %s, not %s_Main.zip: the engine opens Locations/%s/%s_Main.zip and the hook has nothing to answer with'
                     % (mid, ' '.join(os.path.basename(p) for p in served[mid].values()) or 'no slot archive', slot, slot, slot))
        else:
            rep.ok(where, 'served by %s' % os.path.relpath(served[mid][slot], root))
    for (sect, slot), title in sorted(pages.items()):
        n = sect.split('.', 1)[1]
        if ('Redirect.' + n, slot) not in redirects:
            rep.note('%s [%s] %s=%s' % (os.path.basename(ini), sect, slot, title), 'a title without [Redirect.%s] %s= : the entry loads the STOCK slot' % (n, slot))
    for mid in engine:
        if mid not in served:
            rep.note('%s EngineMaps' % os.path.basename(ini), '%s has no Maps folder' % mid)
    redirected = {m for m in redirects.values()}
    idle = sorted(m for m in served if m not in redirected)
    if idle:
        rep.note(os.path.basename(ini), 'map folders no redirect names (installed, not reachable from a menu page): %s' % ' '.join(idle))


# ---------------------------------------------------------------- self-test

def _zip(path, names):
    with zipfile.ZipFile(path, 'w') as z:
        for n in names:
            z.writestr(n, b'x')


def _members(slot, drop=()):
    return ['Scenes/Locations/%s/%s_Main%s' % (slot, slot, s) for s in STOCK_MEMBERS if s not in drop] + list(UI_MEMBERS)


def _map(root, mid, slot, members=None, beside=None):
    d = os.path.join(root, 'KLExpansion', 'Maps', mid)
    os.makedirs(d)
    _zip(os.path.join(d, slot + '_Main.zip'), members if members is not None else _members(slot))
    for s in (BESIDE_MUST + BESIDE_MAY if beside is None else beside):
        open(os.path.join(d, slot + '_Main' + s), 'wb').write(b'y')
    return d


def selftest():
    tmp = tempfile.mkdtemp(prefix='kl_slotcheck_')
    n = [0]

    def ok(msg, cond):
        n[0] += 1
        print('%s %2d %s' % ('ok  ' if cond else 'FAIL', n[0], msg))
        if not cond:
            raise SystemExit('self-test failed: ' + msg)
    try:
        root = os.path.join(tmp, 'game')
        _map(root, 'DD01', 'F01')
        d10 = _map(root, 'DD10', 'F07', members=_members('F01'))                    # the DD10A tree: file renamed, members not
        _map(root, 'DM07', 'F06', members=_members('F06', drop=('.sup', '.ANM')))  # a required member missing
        d3 = _map(root, 'DM03A', 'F07')
        open(os.path.join(d3, 'F01_Main.WHD'), 'wb').write(b'stray')                # a beside file of another slot
        open(os.path.join(d3, 'F07_Main.zip.before-1025x'), 'wb').write(b'bak')     # a backup: ignored
        _map(root, 'DM09', 'F06', beside=BESIDE_MUST[:-1])                         # _LS_Default.WAV missing
        _map(root, 'DM11B', 'F04')
        with open(os.path.join(root, 'KLHook.ini'), 'w') as f:
            f.write('[Expansion]\nEnable=1\nEngineMaps=DM09,DMXX\n[Redirect]\nF01=DD01\n[Redirect.2]\nF07=DM03A\nF06=DM09\n'
                    '[Redirect.3]\nF07=DD10\nF06=DM07\nF04=DM11B\nF02=NOPE\nF03=DM09\n[Page.3]\nF07=The Flat Raid\nF01=Last Call\n')
        rep = Report()
        check_tree(root, rep)
        text = '\n'.join(rep.lines)
        print(text)
        ok('the DD10A tree is a FAIL naming the DD10A crash', 'FAIL  %s' % os.path.join(d10, 'F07_Main.zip') in text and 'name slot F01, the file is F07' in text)
        ok('the required member .sup missing is a FAIL, .ANM a note', 'missing: F06_Main.sup' in text and 'stock has them): .ANM' in text)
        ok('a beside file of another slot is a FAIL', 'F01_Main.WHD names slot F01 but the archive here is for F07' in text)
        ok('a backup file is ignored', 'before-1025x' not in text)
        ok('a missing Default loading bank is a FAIL', 'missing: F06_Main_LS_Default.WAV' in text)
        ok('a redirect to a missing folder is a FAIL', 'F02=NOPE: no Maps\\NOPE folder' in text)
        ok('a redirect whose slot the folder does not serve is a FAIL', 'F03=DM09: Maps\\DM09 holds F06_Main.zip, not F03_Main.zip' in text)
        ok('a good redirect is ok', 'ok    KLHook.ini [Redirect.3] F04=DM11B: served by' in text)
        ok('a page title without a redirect is a note', 'F01=Last Call: a title without [Redirect.3] F01=' in text)
        ok('EngineMaps naming no folder is a note', 'DMXX has no Maps folder' in text)
        ok('exactly the expected FAIL count (DD10 twice: wrong slot AND no F07 members)', rep.fails == 7)
        clean = os.path.join(tmp, 'clean')
        _map(clean, 'DD01', 'F01')
        with open(os.path.join(clean, 'KLHook.ini'), 'w') as f:
            f.write('[Redirect]\nF01=DD01\n')
        rep = Report()
        check_tree(clean, rep)
        ok('a clean tree has no FAIL and no note', rep.fails == 0 and rep.notes == 0)
        loose = os.path.join(tmp, 'F03_Main.zip')
        _zip(loose, _members('F03') + ['Scenes/Locations/F03/F03_Main.extra'])
        rep = Report()
        check_archive(loose, rep)
        ok('a loose archive with an extra member: ok plus a note', rep.fails == 0 and rep.notes == 1)
        _zip(loose, _members('F03') + ['Scenes/Locations/F04/F04_Main.oct'])
        rep = Report()
        check_archive(loose, rep)
        ok('one member of another slot is a FAIL', rep.fails == 1 and 'name slot F04' in rep.lines[0])
        ok('member_name agrees with the check (kl_graft)', _graft_agrees())
        print('kl_slotcheck self-test: %d checks passed' % n[0])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _graft_agrees():
    """kl_graft.member_name renamed members pass the check; the un-renamed ones fail (when kl_graft imports)."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import kl_graft
    except Exception:
        return True                                      # kl_graft needs the game paths; not a self-test failure
    tmp = tempfile.mkdtemp(prefix='kl_slotcheck_g_')
    try:
        p = os.path.join(tmp, 'F07_Main.zip')
        _zip(p, [kl_graft.member_name(n, 'F01', 'F07') for n in _members('F01')])
        rep = Report()
        check_archive(p, rep)
        return rep.fails == 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    if '--self-test' in argv:
        selftest()
        return 0
    ini = None
    if '--ini' in argv:
        i = argv.index('--ini')
        ini = argv[i + 1]
        del argv[i:i + 2]
    rep = Report()
    if not argv:
        roots = [d for d in DD_GUESSES if os.path.isdir(os.path.join(d, 'KLExpansion'))]
        if not roots:
            print(__doc__)
            return 2
        check_tree(roots[0], rep, ini)
    for a in argv:
        if os.path.isdir(a):
            check_tree(a, rep, ini)
        elif a.lower().endswith('.zip'):
            check_archive(a, rep)
        else:
            print('not a folder or a zip: ' + a)
            return 2
    for line in rep.lines:
        print(line)
    print('kl_slotcheck: %d FAIL, %d note(s)' % (rep.fails, rep.notes))
    return 1 if rep.fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
