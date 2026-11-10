#!/usr/bin/env python3
r"""
kl_menu_plates_1110.py - PLATE TEXT FIX for the live Dead Men menu look (track T9): the 'OnFocus' colour set back to ink.

THE BUG (11-10 ~02:55 shots, C:\kl_build_1024\menulook_1109\shots\{deadmen,stock}\lobby.png): text that sits ON a light plate is
black in stock and PALE in the Dead Men look = unreadable: the lobby column header ('NAME: / CRIMINAL LOYALTY: / CRIMINAL STYLE: /
CRIMINAL RANK:'), the selected lobby row ('LOCATION: ... HOT COFFEE'), the CLOSE SESSION / READY plates, the Heister page's
Character / Mask / Outfit values, the leaderboard column titles, the in-level 'Bonus' / 'Penalty' headings and the scoreboard columns.
CAUSE: tools/kl_menu_look_1109.py COLORSETS mapped the set 'OnFocus' BY NAME to chalk / ink / dim (the design's GUESS 'focus ink,
headings sit on bars', re/menu_look_1109.md 2.2). The stock set is ff000000 / ff000000 / ff888888 = ink on the plate ALWAYS: it is the
set a receiver switches to while it HAS focus (RecCSFocus="OnFocus" RecCSDefault="Default", re/menus.md 520 / 717) and the set of every
element that stands on a static plate (66 uses in frontend.xml, 7 in ingame.xml, 42 in online.xml; re/hud_menu.md 141 already said
'OnFocus = INK'). The table is fixed there (INK / INK / DIM); this kit repairs the files that were built BEFORE the fix.

WHAT IT DOES: for each live themed menu file it rewrites ONLY the three attribute values of every <ColorSet Name="OnFocus"> in the
menu XML members (menu/frontend.xml + menu/ingame.xml of a Patch01*.zip, Menu/online.xml of Scenes\kaneandlynch*.zip):
NormalColor -> ink 0c0c0d, FocusColor -> ink, DisableColor -> dim 8d8982, the alpha byte KEPT. Every other byte of every other member is
identical (proven member by member), the menu manager's table signature is equal (proven; refused otherwise), a set already ink is
reported and the file skipped (a stock black / grey value is the same role: 'already' too). Candidates (all under <DD>\KLExpansion\Overlay, never a stock file, never KL_PortBackup):
  Patch01_deadmen.zip, Patch01_rows12_deadmen.zip, Scenes\kaneandlynch_deadmen.zip     (the klslot.c [MenuLook] variant siblings: the live
                                                                                         install of 11-10 00:10, install.py --variant)
  Patch01.zip, Patch01_rows12.zip, Scenes\kaneandlynch.zip                               (only when the look was installed IN PLACE: a stock-
                                                                                         coloured OnFocus there is 'already ink' = untouched)
Only the files that are present AND pale are staged, so one `stage` is right whichever way the look went in.

  python tools\kl_menu_plates_1110.py stage [--overlay DIR] [--out DIR] [--accept-input]      -> <out>\<file>s + pins.json + install.py + bats
  python tools\kl_menu_plates_1110.py check <stage_dir> [--overlay DIR]                       re-proves every file against the live one
  python tools\kl_menu_plates_1110.py fix <src.zip> <dst.zip>                                 one file (tests, by hand)
  python tools\kl_menu_plates_1110.py show <file.zip> ...                                     read-only: the OnFocus values per member
Then (game closed): python C:\kl_build_1024\menuplates_1110\install.py --dry | (install) | --undo   (backups <name>.before-menuplates_1110
NEXT TO the live file, never overwritten; undo byte-exact only when the live file is exactly what install wrote; --game <copy> rehearsal).

Pins: the first `stage` on the PC records the live md5s in pins.json (--accept-input = you own the input); a later `stage` refuses when a
live file moved. install.py refuses when a live md5 is not its pin (another kit landed: re-stage).
GUESSES: none in the colour (stock role, read from the live stage report); the ELEMENT list above is from the themed stage1 XML
(66 / 7 / 42 uses), which page shows which of them is for the eye (bench ML1 shots: lobby, heister, leaderboard, round over).
Self-test: tools/kl_menu_plates_1110_test.py (synthetic archives; kl_tests.py --py). Real file: `fix` on a stage1 copy (device, 11-10).
"""
import hashlib, json, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hud_menu as HM

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OVERLAY = os.path.join(GAME, 'KLExpansion', 'Overlay')
OUT = r'C:\kl_build_1024\menuplates_1110'
TAG = '.before-menuplates_1110'
SET = 'OnFocus'
INK, DIM = HM.INK, HM.DIM                                 # (0c,0c,0d) / (8d,89,82): the kit's palette (kl_hud_menu.py)
WANT = (INK, INK, DIM)                                    # NormalColor, FocusColor, DisableColor; alpha kept
COLOR_ATTRS = HM.COLOR_ATTRS
# live name under Overlay -> the XML members that hold colour sets
CANDIDATES = (
    ('Patch01_deadmen.zip', (HM.FRONT, HM.INGAME)),
    ('Patch01_rows12_deadmen.zip', (HM.FRONT, HM.INGAME)),
    (os.path.join('Scenes', 'kaneandlynch_deadmen.zip'), (HM.ONLINE,)),
    ('Patch01.zip', (HM.FRONT, HM.INGAME)),
    ('Patch01_rows12.zip', (HM.FRONT, HM.INGAME)),
    (os.path.join('Scenes', 'kaneandlynch.zip'), (HM.ONLINE,)),
)


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def hexa(t):
    return '0x%02x%02x%02x%02x' % tuple(t)


def guard(path):
    """Refuse anything that is not under KLExpansion\\Overlay (stock files, KL_PortBackup): the overlay files are the mod's own copies."""
    low = os.path.normpath(path).lower().replace('/', os.sep)
    if 'kl_portbackup' in low:
        raise SystemExit('REFUSED: %s is under KL_PortBackup' % path)
    if (os.sep + 'klexpansion' + os.sep + 'overlay' + os.sep) not in low + os.sep:
        raise SystemExit('REFUSED: %s is not under KLExpansion\\Overlay (stock files are never written)' % path)


# ------------------------------------------------------------------ the XML edit
def fix_xml(xml):
    """-> (xml2, rows): every <ColorSet Name="OnFocus"> attribute decided. rows = [(occurrence, attr, old text, new text or '-', how)];
    how: 'ink' (changed), 'already' (was the wanted colour), 'malformed' (not 0xAARRGGBB: left alone), 'absent' (no such attribute)."""
    rows, occ = [], [0]

    def fn(t, text):
        if t.name != 'ColorSet' or dict(t.attrs).get('Name', '') != SET:
            return None
        occ[0] += 1
        attrs = dict(t.attrs)
        for an, rgb in zip(COLOR_ATTRS, WANT):
            old_txt = attrs.get(an)
            if old_txt is None:
                rows.append((occ[0], an, '(absent)', '-', 'absent')); continue
            old = HM._hex(old_txt)
            if old is None:
                rows.append((occ[0], an, old_txt, '-', 'malformed')); continue
            new = (old[0],) + tuple(rgb)
            role = HM._role(old)                              # stock black / grey are the SAME role as ink / dim: nothing to fix there
            if tuple(old) == new or (role and tuple(role[1:]) == tuple(rgb)):
                rows.append((occ[0], an, old_txt, '-', 'already')); continue
            text = HM.set_attr(text, an, hexa(new))
            rows.append((occ[0], an, old_txt, hexa(new), 'ink'))
        return text
    xml2, _n = HM.rewrite(xml, fn)
    return xml2, rows


def fix_zip(src, dst, members, log=print):
    """A copy of archive src at dst with the OnFocus set of each member fixed. -> {member: rows}. None (and no dst) when every set is
    already ink. Refuses when a member is missing, the table signature moves, or any other member would differ."""
    z = zipfile.ZipFile(src); new, report, changed = {}, {}, 0
    for member in members:
        i = HM._member(z, member)
        if i is None:
            raise ValueError('%s has no %s' % (src, member))
        xml = z.read(i).decode('latin-1')
        xml2, rows = fix_xml(xml)
        if not rows:
            raise ValueError('%s %s: no <ColorSet Name="%s"> at all (not a menu file?)' % (src, member, SET))
        if HM.signature(xml) != HM.signature(xml2):
            raise ValueError('%s %s: the table signature moved - refused' % (src, member))
        if len(HM.tags(xml)) != len(HM.tags(xml2)):
            raise ValueError('%s %s: tag count moved - refused' % (src, member))
        n_ink = sum(1 for r in rows if r[4] == 'ink')
        changed += n_ink
        report[member] = rows
        log('  %s %s: %s' % (os.path.basename(src), member, summary(rows)))
        if n_ink:
            new[i.filename.lower()] = xml2.encode('latin-1')
    if not changed:
        return None
    HM._rezip(src, dst, new)
    verify_pair(src, dst, members)
    return report


def summary(rows):
    c = {}
    for r in rows:
        c[r[4]] = c.get(r[4], 0) + 1
    return ', '.join('%d %s' % (v, k) for k, v in sorted(c.items()))


def verify_pair(src, dst, members):
    """src and dst: same member list, only `members` differ, and in those only the OnFocus values (fix_xml(src) == dst, signature equal)."""
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            raise ValueError('%s: member list differs from %s' % (dst, src))
        want = {m.lower() for m in members}
        for i in a.infolist():
            da, db = a.read(i), b.read(i.filename)
            if i.filename.lower() not in want:
                if da != db:
                    raise ValueError('%s: member %s differs (only the menu XML may)' % (dst, i.filename))
                continue
            xa, xb = da.decode('latin-1'), db.decode('latin-1')
            fixed, _rows = fix_xml(xa)
            if fixed != xb:
                raise ValueError('%s: %s is not the input with only the %s set fixed' % (dst, i.filename, SET))
            if HM.signature(xa) != HM.signature(xb):
                raise ValueError('%s: %s table signature differs from the input' % (dst, i.filename))


def members_for(path):
    """The XML members this kit touches in `path`: by the candidate name when it matches (a scene archive carries stock copies of
    frontend.xml / ingame.xml that Patch01.zip shadows: left alone), else every menu XML member present."""
    base = os.path.basename(path).lower()
    for n, members in CANDIDATES:
        if os.path.basename(n).lower() == base:
            return members
    with zipfile.ZipFile(path) as z:
        return tuple(m for m in (HM.FRONT, HM.INGAME, HM.ONLINE) if HM._member(z, m) is not None)


def show(path, members=None, log=print):
    """Read-only: the OnFocus values of each menu XML member. -> {member: [(occ, attr, value)]}"""
    out = {}
    with zipfile.ZipFile(path) as z:
        mem = members or members_for(path)
        for m in mem:
            i = HM._member(z, m)
            if i is None:
                continue
            _x, rows = fix_xml(z.read(i).decode('latin-1'))
            out[m] = [(r[0], r[1], r[2], r[4]) for r in rows]
            log('  %s %s: %s' % (os.path.basename(path), m, '; '.join('%s=%s (%s)' % (r[1], r[2], r[4]) for r in rows) or 'no OnFocus set'))
    return out


# ------------------------------------------------------------------ install template
INSTALL = r'''r"""Installs / undoes the MENU PLATE TEXT FIX @STAGE@ (tools/kl_menu_plates_1110.py) on the live Dead Men menu look files.

  python install.py            each live file -> <name>@TAG@ NEXT TO it (an existing backup is NEVER overwritten: refuses), then the fixed
                               copy in its place. Order as staged (Patch01* first: klslot.c 981 wants Overlay\Patch01.zip not newer than rows12;
                               the _deadmen siblings have no such rule).
  python install.py --undo     every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: every pin and what would happen (also with --undo)
  --game <dir>                 another Dog Days folder (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Every live md5 is pinned BEFORE anything is written (all or nothing); nothing is written while kl2.exe runs. Never touches a stock file
(<DD>\Patch01.zip, <DD>\Scenes\...) or KL_PortBackup: only KLExpansion\Overlay files, the mod's own copies."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '@TAG@'
FILES = @FILES@          # (relative name under KLExpansion\Overlay, live md5 pinned at stage time, md5 of the fixed copy)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    ov = os.path.join(game, 'KLExpansion', 'Overlay')
    if 'kl_portbackup' in ov.lower():
        print('REFUSED: KL_PortBackup'); return 1
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(ov, n), os.path.join(ov, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-36s live %s' % (n, cur))
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another kit landed: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) for p in plan) * 2 + (256 << 20)
        if shutil.disk_usage(ov).free < need:
            print('REFUSED: less than the files x2 + 256 MB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %s %s (backup %s)' % ('restore' if undo else 'install', p[1], p[2]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(stage_dir, files, game, log):
    src = (INSTALL.replace('@GAME@', game).replace('@TAG@', TAG).replace('@STAGE@', os.path.basename(stage_dir)).replace('@FILES@', repr(files)))
    open(os.path.join(stage_dir, 'install.py'), 'w', newline='\n').write(src)
    for nm, arg in (('INSTALL menu plates 1110.bat', ''), ('UNDO menu plates 1110.bat', ' --undo')):
        open(os.path.join(stage_dir, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    log('  install.py + bats written (%d files)' % len(files))


# ------------------------------------------------------------------ commands
def stage(overlay=OVERLAY, out=OUT, accept=False, game=GAME, log=print):
    """-> list of (name, live md5, staged md5) staged; [] when nothing is pale. Writes <out>\\<name>, pins.json, build_report.json, install.py."""
    present = [(n, mem) for n, mem in CANDIDATES if os.path.isfile(os.path.join(overlay, n))]
    if not present:
        raise SystemExit('no menu file under %s (Patch01*.zip / Scenes\\kaneandlynch*.zip): is the overlay there?' % overlay)
    pins_path = os.path.join(out, 'pins.json')
    pins = json.load(open(pins_path)) if os.path.isfile(pins_path) else None
    live = {}
    for n, _m in present:
        guard(os.path.join(overlay, n))
        live[n] = fmd5(os.path.join(overlay, n))
        log('  live %-36s %s' % (n, live[n]))
    if pins is not None and not accept:
        moved = [n for n in live if n in pins and pins[n] != live[n]]
        if moved:
            raise SystemExit('REFUSED: live file(s) moved since the pins: %s (re-run with --accept-input if you own that)' % moved)
    os.makedirs(out, exist_ok=True)
    files, report = [], {}
    for n, members in present:
        src, dst = os.path.join(overlay, n), os.path.join(out, n)
        if os.path.exists(dst):
            os.remove(dst)
        rep = fix_zip(src, dst, members, log)
        if rep is None:
            log('  %s: already ink - nothing to do' % n); continue
        files.append((n, live[n], fmd5(dst)))
        report[n] = {m: rows for m, rows in rep.items()}
        log('  staged %s -> %s (%s)' % (n, dst, files[-1][2]))
    json.dump(live, open(pins_path, 'w'), indent=1)
    json.dump({'overlay': overlay, 'set': SET, 'want': [hexa((0,) + tuple(c))[4:] for c in WANT], 'files': files, 'rows': report},
              open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    if not files:
        for stale in ('install.py', 'INSTALL menu plates 1110.bat', 'UNDO menu plates 1110.bat'):
            if os.path.exists(os.path.join(out, stale)):
                os.remove(os.path.join(out, stale))             # an older kit's installer must not outlive its files
        log('nothing staged: every %s set is ink already' % SET)
        return []
    write_install(out, files, game, log)
    log('staged %d file(s) in %s; next: python %s --dry' % (len(files), out, os.path.join(out, 'install.py')))
    return files


def check(stage_dir, overlay=OVERLAY, log=print):
    """Re-proves every staged file against the live one: pins, member equality outside the XML, OnFocus-only edit, signature. -> True."""
    rep = json.load(open(os.path.join(stage_dir, 'build_report.json')))
    pins = json.load(open(os.path.join(stage_dir, 'pins.json')))
    ok = True
    for n, old, new in rep['files']:
        src, dst = os.path.join(overlay, n), os.path.join(stage_dir, n)
        members = dict(CANDIDATES)[n]
        if not os.path.isfile(src):
            log('  %s: live file missing' % n); ok = False; continue
        cur = fmd5(src)
        if cur == new:
            log('  %s: live IS the staged file (installed) - skip' % n); continue
        if cur != old or pins.get(n) != old:
            log('  %s: live md5 %s is not the pinned %s' % (n, cur, old)); ok = False; continue
        if fmd5(dst) != new:
            log('  %s: staged md5 moved' % n); ok = False; continue
        try:
            verify_pair(src, dst, members)
        except ValueError as e:
            log('  %s: %s' % (n, e)); ok = False; continue
        vals = show(dst, members, log=lambda *_a: None)
        bad = [r for rows in vals.values() for r in rows if r[3] not in ('already', 'malformed', 'absent')]
        if bad:
            log('  %s: staged file still has a non-ink %s value: %s' % (n, SET, bad)); ok = False; continue
        log('  %s: PASS (only %s changed, signature equal, %d XML member(s))' % (n, SET, len(members)))
    log('check: %s' % ('PASS' if ok else 'FAIL'))
    return ok


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    cmd = a[0]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    if cmd == 'stage':
        files = stage(opt('--overlay', OVERLAY), opt('--out', OUT), '--accept-input' in a, opt('--game', GAME))
        return 0
    if cmd == 'check':
        return 0 if check(a[1], opt('--overlay', OVERLAY)) else 1
    if cmd == 'fix':
        src, dst = a[1], a[2]
        members = members_for(src)
        rep = fix_zip(src, dst, members)
        print('nothing to fix: already ink' if rep is None else 'wrote %s (%s)' % (dst, fmd5(dst)))
        return 0
    if cmd == 'show':
        for p in a[1:]:
            show(p)
        return 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
