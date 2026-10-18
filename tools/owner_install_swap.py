#!/usr/bin/env python3
r"""owner_install_swap.py - replace ONE map's folder in an owner install directory (e.g. C:\kl_build_1018\owner_1018) with a staged folder.

    python tools/owner_install_swap.py --owner C:\kl_build_1018\owner_1018 --map DM03A --staged <folder holding F07_Main.zip ...>
           [--md5 <expected md5 of the staged *_Main.zip>] [--tag 1018b] [--gunpics check|apply|off]
           [--talk-fed-from <ini with the FedRespawn/FedKill pools>] [--delete-old] [--dry-run]

WHAT IT DOES (reads <DD> only; writes only inside --owner)
  1. Picks the files the map needs from the staged folder: F0x_Main.zip/.WAV/.WHD/.hti, F0x_Main_LS.SND, F0x_Main_LS_<lang>.WAV/.WHD,
     and KLGuns.ini / KLJoin.ini / KLWardrobe.ini / KLTalk.ini when present.
     KLTalk: if the install's hook (manifest hook.src) knows the new words (contains 'FedKill') and the staged folder has
     KLTalk.newhook.ini, THAT file is installed as KLTalk.ini; otherwise the staged KLTalk.ini. (owner_1018 ships the new hook, so
     newhook wins; the manifest marks KLTalk.ini needs_hook so install_owner_1018.ps1 leaves it out if the hook is not installed.)
     --talk-fed-from INI appends the FedRespawn / FedKill pools of INI (e.g. owner_1018\Maps\DM03A\KLTalk.ini) when the chosen
     KLTalk.ini has none, and fixes Pools=N. Those pools only name stock Dog Days sound keys, so they are map independent.
  2. Checks the zip: --md5 (if given), debug/check_passes.py (0 FAIL required; the run must say '0 failed check(s)'), and the gun
     pictures: kl_gunpics apply into a temp file must change 0 pictures. --gunpics apply (default) puts the result in place when it
     does not (and re-checks); check only reports; off skips.
  3. Moves the old Maps\<map> to Maps\<map>.replaced-<tag> (kept: outside the manifest, so the installer never looks at it; it costs disk
     space - --delete-old removes it instead). Writes the new Maps\<map>\ and Maps\<map>.json.
  4. Rewrites that map's entries in Install.manifest.json in place (same position): size, md5, sha1, needs_hook, and 'before' =
     the md5 now in <DD>\KLExpansion\Maps\<map>\<file> (or 'absent') + the old manifest's before list and old md5 for that file
     (so a machine in the previous owner_1018 state still passes the installer's before-md5 guard). The old manifest is saved as
     Install.manifest.json.bak-<tag>. Files the old entry had that the new folder lacks simply drop out.
  5. KL*.ini Entries (klini_audit.py): the hook ignores KLGuns.ini [Guns] Entries= / KLJoin.ini [FedBody] Entries= that differ from the
     loaded .prm's chunk count (dword +4 of the .prm), so every swap now rewrites a stale Entries to the staged zip's count (only when
     the old folder's .prm shows the chunk indices unchanged: same size for every old index, i.e. chunks were only appended; else it
     refuses) and fails on a KLWardrobe.ini Root at or past the count. A step that appends chunks AFTER the guns build (the fed body)
     used to leave KLGuns.ini one build behind; this cannot recur silently.
  --fix-ini repairs ONLY the KL*.ini of --map in place (no --staged; the zip is not touched): rewrites Entries, refreshes the
     manifest entries (size/md5/sha1, before = md5 in <DD> + old before list + old md5), saves Install.manifest.json.bak-<tag>.
Nothing is installed in the game folder; run install_owner_1018.ps1 -DryRun afterwards.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
KEEP = re.compile(r'^F\d\d_Main(\.zip|\.WAV|\.WHD|\.hti|_LS\.SND|_LS_\w+\.(WAV|WHD))$|^(KLGuns|KLJoin|KLWardrobe)\.ini$', re.I)


def hashes(p):
    a, b = hashlib.md5(), hashlib.sha1()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(8 << 20), b''):
            a.update(c); b.update(c)
    return a.hexdigest(), b.hexdigest()


def run(args):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=REPO)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def fed_pools(text):
    """-> list of (name-less) pool blocks of text whose On= is FedRespawn / FedKill"""
    parts = re.split(r'(?m)^(?=\[Pool\.\d+\])', text)
    return [p for p in parts[1:] if re.search(r'(?m)^On=Fed(Respawn|Kill)\s*$', p)]


def loc_missing(zpath, keys):
    """-> keys found in NONE of the zip's English .LOC (a pool naming them is a failed lookup at run time)"""
    import zipfile
    with zipfile.ZipFile(zpath) as z:
        locs = [n for n in z.namelist() if re.search(r'Main_?English\.LOC$', n, re.I)]
        data = z.read(locs[0]) if locs else b''
    return [k for k in keys if k.encode('latin1') not in data]


# ---------------------------------------------------------------- KL*.ini Entries (see klini_audit.py)
GUNPICS_NOISE = 2   # see the gunpics step in main()
INI_ENTRIES = {'KLGuns.ini': 'Guns', 'KLJoin.ini': 'FedBody'}


def prm_chunks(zpath, table=False):
    """-> chunk count (dword +4 of the archive's .prm); table=True -> (count, [size of every chunk]) (table = count x [ofs,size,ref,0] at the file's end)"""
    import struct, zipfile
    with zipfile.ZipFile(zpath) as z:
        nm = [n for n in z.namelist() if n.lower().endswith('.prm')]
        if not nm:
            raise SystemExit('FAIL: %s has no .prm' % zpath)
        if not table:
            with z.open(nm[0]) as f:
                return struct.unpack_from('<I', f.read(8), 4)[0]
        d = z.read(nm[0])
    to, n = struct.unpack_from('<2I', d)
    return n, [struct.unpack_from('<I', d, to + 16 * i + 4)[0] for i in range(n)]


def append_only(old_zip, new_zip):
    """True when every chunk index of the old .prm has the same size in the new one and the new one has at least as many
    (GUESS: same size = same chunk; a changed byte inside, e.g. a remapped texture id, keeps the index)."""
    n0, s0 = prm_chunks(old_zip, True)
    n1, s1 = prm_chunks(new_zip, True)
    return n1 >= n0 and s1[:n0] == s0


def section_span(text, sec):
    m = re.search(r'(?mi)^\[%s\][^\n]*\n' % re.escape(sec), text)
    if not m:
        return None
    e = re.search(r'(?m)^\[', text[m.end():])
    return m.end(), m.end() + e.start() if e else len(text)


def fix_entries(name, text, count, old_zip=None, new_zip=None, allow=False):
    """-> (new text, note). KLGuns.ini [Guns] / KLJoin.ini [FedBody] Entries= -> count. Refuses (SystemExit) when Entries was for a
    different chunk table and the old archive does not show the indices unchanged, unless allow. KLWardrobe.ini: only checks Root < count."""
    if name == 'KLWardrobe.ini':
        roots = [int(x) for x in re.findall(r'(?m)^Root=(\d+)', text)]
        bad = [r for r in roots if r >= count]
        if bad:
            raise SystemExit('FAIL: KLWardrobe.ini has %d Root(s) >= the .prm chunk count %d (%s)' % (len(bad), count, bad[:5]))
        return text, 'wardrobe Roots below %d' % count
    sec = INI_ENTRIES.get(name)
    if not sec:
        return text, ''
    span = section_span(text, sec)
    if not span:
        return text, 'no [%s] section' % sec
    body = text[span[0]:span[1]]
    m = re.search(r'(?m)^Entries=(\d+)', body)
    have = int(m.group(1)) if m else None
    if have == count:
        return text, 'Entries=%d OK' % count
    if have is not None and not allow:
        if not (old_zip and os.path.isfile(old_zip) and append_only(old_zip, new_zip)):
            raise SystemExit('FAIL: %s [%s] Entries=%d but the .prm has %d chunks, and the chunk indices are not shown to be unchanged '
                             '(no old archive, or a size differs): build the file again with its tool (kl_map_guns / kl_fa_fedbody apply)' % (name, sec, have, count))
    if m:
        body = body[:m.start()] + 'Entries=%d' % count + body[m.end():]
    else:
        nl = '\r\n' if '\r\n' in text else '\n'
        body = body.rstrip('\r\n') + nl + 'Entries=%d' % count + nl
    return text[:span[0]] + body + text[span[1]:], 'Entries %s -> %d' % (have, count)


def fix_ini_in_place(owner, mid, game, tag):
    maps = os.path.join(owner, 'Maps'); folder = os.path.join(maps, mid)
    mf = os.path.join(owner, 'Install.manifest.json'); man = json.load(open(mf))
    zs = [n for n in os.listdir(folder) if re.match(r'^F\d\d_Main\.zip$', n, re.I)]
    if len(zs) != 1:
        raise SystemExit('need one *_Main.zip in ' + folder)
    zp = os.path.join(folder, zs[0]); count = prm_chunks(zp)
    old_zip = None
    for d in sorted((d for d in os.listdir(maps) if d.startswith(mid + '.replaced-')), key=lambda d: os.path.getmtime(os.path.join(maps, d)), reverse=True):
        c = os.path.join(maps, d, zs[0])
        if os.path.isfile(c):
            old_zip = c; break
    changed = []
    for n in ('KLGuns.ini', 'KLJoin.ini', 'KLWardrobe.ini'):
        p = os.path.join(folder, n)
        if not os.path.isfile(p):
            continue
        t = open(p, 'rb').read().decode('latin1')
        t2, note = fix_entries(n, t, count, old_zip, zp)
        print('%s %-15s %s' % (mid, n, note))
        if t2 != t:
            open(p, 'wb').write(t2.encode('latin1')); changed.append(n)
    if not changed:
        print('nothing to fix'); return
    old = {f['name']: f for f in man['files'] if f['map'] == mid}
    for n in changed:
        md5, sha1 = hashes(os.path.join(folder, n))
        e = old[n]
        inst = os.path.join(game, 'KLExpansion', 'Maps', mid, n)
        before = set(e['before']); before.add(e['md5'])
        before.add(hashes(inst)[0] if os.path.isfile(inst) else 'absent')
        e.update(size=os.path.getsize(os.path.join(folder, n)), md5=md5, sha1=sha1, before=sorted(before))
    shutil.copyfile(mf, mf + '.bak-' + tag)
    json.dump(man, open(mf + '.new', 'w'), indent=1); os.replace(mf + '.new', mf)
    print('fixed %s; manifest updated (backup %s)' % (', '.join(changed), mf + '.bak-' + tag))


def add_fed(text, src_text, zpath=None):
    if re.search(r'(?m)^On=FedKill\s*$', text):
        return text, 0
    blocks = fed_pools(src_text)
    if zpath:
        # The Fed pools name stock Dog Days keys, but a converted map's own .LOC has them only if its builder added them
        # (DM03A's does; the v2final DM01B / DM06B do not): never ship a pool whose keys the level cannot resolve.
        blocks = [b for b in blocks if not loc_missing(zpath, re.findall(r'(?m)^Key\.\d+=(.*?)\r?$', b))]
        if not blocks:
            print("KLTalk: Fed pools NOT appended - their keys are missing from this zip's .LOC")
            return text, 0
    if not blocks:
        raise SystemExit('--talk-fed-from has no FedRespawn/FedKill pools')
    nl = '\r\n' if '\r\n' in text else '\n'
    n = int(re.search(r'(?m)^Pools=(\d+)', text).group(1))
    if not text.endswith('\n'):
        text += nl
    for b in blocks:
        n += 1
        b = re.sub(r'^\[Pool\.\d+\]', '[Pool.%d]' % n, b.replace('\r\n', '\n').replace('\n', nl))
        text += b if b.endswith(nl) else b + nl
    text = re.sub(r'(?m)^Pools=\d+', 'Pools=%d' % n, text, count=1)
    return text, len(blocks)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--owner', required=True); ap.add_argument('--map', required=True); ap.add_argument('--staged'); ap.add_argument('--fix-ini', action='store_true')
    ap.add_argument('--md5'); ap.add_argument('--tag', default='swap'); ap.add_argument('--game', default=DD)
    ap.add_argument('--gunpics', choices=['check', 'apply', 'off'], default='apply')
    ap.add_argument('--talk-fed-from'); ap.add_argument('--delete-old', action='store_true'); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    mid, owner, staged = a.map, a.owner, a.staged
    if a.fix_ini:
        fix_ini_in_place(owner, mid, a.game, a.tag); return
    if not staged:
        raise SystemExit('--staged is required (or --fix-ini)')
    if os.path.normcase(os.path.abspath(owner)).startswith(os.path.normcase(os.path.abspath(a.game))):
        raise SystemExit('--owner must not be inside the game folder')
    maps = os.path.join(owner, 'Maps')
    mf = os.path.join(owner, 'Install.manifest.json')
    man = json.load(open(mf))
    old_dir = os.path.join(maps, mid)
    if not os.path.isdir(staged):
        raise SystemExit('no staged folder ' + staged)
    names = sorted(n for n in os.listdir(staged) if KEEP.match(n))
    zips = [n for n in names if n.lower().endswith('_main.zip')]
    if len(zips) != 1:
        raise SystemExit('need exactly one *_Main.zip in %s, found %s' % (staged, zips))
    zname = zips[0]
    new_hook = False
    hp = os.path.join(owner, man['hook']['src'])
    if os.path.isfile(hp):
        new_hook = b'FedKill' in open(hp, 'rb').read()
    talk_src = None
    for cand in (['KLTalk.newhook.ini', 'KLTalk.ini'] if new_hook else ['KLTalk.ini']):
        if os.path.isfile(os.path.join(staged, cand)):
            talk_src = cand; break
    print('map %s zip %s hook-new=%s KLTalk from %s' % (mid, zname, new_hook, talk_src))
    # ---- zip checks
    zpath = os.path.join(staged, zname)
    zmd5 = hashes(zpath)[0]
    if a.md5 and zmd5 != a.md5.lower():
        raise SystemExit('FAIL: staged zip md5 %s != expected %s' % (zmd5, a.md5))
    final_zip, steps, tmpd = zpath, [], tempfile.mkdtemp(prefix='ois_')
    if a.gunpics != 'off':
        out = os.path.join(tmpd, zname)
        rc, txt = run([os.path.join('tools', 'kl_gunpics.py'), 'apply', zpath, out])
        last = txt.strip().splitlines()[-1] if txt.strip() else ''
        m = re.search(r"'changed': (\d+)", last)
        if rc or not m:
            raise SystemExit('FAIL: kl_gunpics rc=%d: %s' % (rc, last))
        ch = int(m.group(1))
        steps.append(dict(step='gunpics', changed_before=ch, last=last[:200]))
        # kl_gunpics apply is not idempotent: on a zip it already ran on, the lossy re-encode still changes 1..2 pictures.
        # Applying again then double-encodes them (owner_1018 DM03A/DM05A got that way), so <= GUNPICS_NOISE counts as applied.
        # GUESS: a zip that never had gunpics changes more than 2.
        if ch <= GUNPICS_NOISE:
            print('gunpics: %d picture(s) would change -> already applied (re-encode noise, left alone)' % ch)
            ch = 0
        else:
            print('gunpics: %d picture(s) would change -> MISSING' % ch)
        if ch and a.gunpics == 'apply':
            final_zip = out
            print('gunpics applied; zip is now', hashes(out)[0])
        elif ch:
            raise SystemExit('FAIL: gun pictures missing (use --gunpics apply)')
    rc, txt = run([os.path.join('debug', 'check_passes.py'), final_zip])
    fails = txt.count('FAIL ')
    ok = rc == 0 and '0 failed check(s)' in txt
    steps.append(dict(step='check_passes', rc=rc, fails=fails, tail=txt.strip().splitlines()[-1] if txt.strip() else ''))
    if not ok:
        print(txt[-2000:])
        raise SystemExit('FAIL: check_passes')
    print('check_passes: 0 FAIL')
    # ---- assemble new folder (in tmp first, then swap)
    build = os.path.join(tmpd, 'new')
    os.makedirs(build)
    files = {}
    old_zip = os.path.join(old_dir, zname)
    for n in names:
        shutil.copyfile(final_zip if n == zname else os.path.join(staged, n), os.path.join(build, n))
    count = prm_chunks(final_zip)
    for n in ('KLGuns.ini', 'KLJoin.ini', 'KLWardrobe.ini'):
        bp = os.path.join(build, n)
        if os.path.isfile(bp):
            t = open(bp, 'rb').read().decode('latin1')
            t2, note = fix_entries(n, t, count, old_zip, final_zip)
            print('%s: %s' % (n, note))
            if t2 != t:
                open(bp, 'wb').write(t2.encode('latin1'))
    if talk_src:
        t = open(os.path.join(staged, talk_src), 'rb').read().decode('latin1')
        if a.talk_fed_from:
            t, k = add_fed(t, open(a.talk_fed_from, 'rb').read().decode('latin1'), final_zip)
            print('KLTalk: appended %d Fed pool(s)' % k)
        open(os.path.join(build, 'KLTalk.ini'), 'wb').write(t.encode('latin1'))
    for n in sorted(os.listdir(build)):
        files[n] = hashes(os.path.join(build, n))
    old = {f['name']: f for f in man['files'] if f['map'] == mid}
    entries = []
    for n in sorted(files, key=lambda s: s.lower()):
        md5, sha1 = files[n]
        inst = os.path.join(a.game, 'KLExpansion', 'Maps', mid, n)
        cur = hashes(inst)[0] if os.path.isfile(inst) else 'absent'
        before = {cur}
        if n in old:
            before.update(old[n]['before']); before.add(old[n]['md5'])
        if n == 'KLTalk.ini':
            before.add('absent')
        entries.append(dict(map=mid, name=n, src=n, size=os.path.getsize(os.path.join(build, n)), md5=md5, sha1=sha1,
                            before=sorted(before), needs_hook=(n == 'KLTalk.ini')))
        print('  %-28s %s now %s' % (n, md5[:8], cur[:8]))
    if a.dry_run:
        print('DRY RUN: nothing written in', owner); shutil.rmtree(tmpd, True); return
    # ---- swap folder
    if os.path.isdir(old_dir):
        keep = os.path.join(maps, '%s.replaced-%s' % (mid, a.tag))
        if os.path.exists(keep):
            raise SystemExit('exists: ' + keep)
        if a.delete_old:
            shutil.rmtree(old_dir)
        else:
            os.rename(old_dir, keep); print('old folder kept as', keep, '(outside the manifest)')
    shutil.move(build, old_dir)
    # ---- manifest in place
    shutil.copyfile(mf, mf + '.bak-' + a.tag)
    pos = next((i for i, f in enumerate(man['files']) if f['map'] == mid), len(man['files']))
    rest = [f for f in man['files'] if f['map'] != mid]
    pos = min(pos, len(rest))
    man['files'] = rest[:pos] + entries + rest[pos:]
    tmpm = mf + '.new'
    json.dump(man, open(tmpm, 'w'), indent=1)
    os.replace(tmpm, mf)
    rep = dict(map=mid, steps=steps, base='swap:' + a.tag, staged=staged, files={n: files[n][0] for n in files})
    json.dump(rep, open(os.path.join(maps, mid + '.json'), 'w'), indent=1)
    shutil.rmtree(tmpd, True)
    print('manifest updated: %d entries for %s; backup %s' % (len(entries), mid, mf + '.bak-' + a.tag))


if __name__ == '__main__':
    main()
