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


def add_fed(text, src_text):
    if re.search(r'(?m)^On=FedKill\s*$', text):
        return text, 0
    blocks = fed_pools(src_text)
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
    ap.add_argument('--owner', required=True); ap.add_argument('--map', required=True); ap.add_argument('--staged', required=True)
    ap.add_argument('--md5'); ap.add_argument('--tag', default='swap'); ap.add_argument('--game', default=DD)
    ap.add_argument('--gunpics', choices=['check', 'apply', 'off'], default='apply')
    ap.add_argument('--talk-fed-from'); ap.add_argument('--delete-old', action='store_true'); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    mid, owner, staged = a.map, a.owner, a.staged
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
        print('gunpics: %d picture(s) would change -> %s' % (ch, 'already applied' if ch == 0 else 'MISSING'))
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
    for n in names:
        shutil.copyfile(final_zip if n == zname else os.path.join(staged, n), os.path.join(build, n))
    if talk_src:
        t = open(os.path.join(staged, talk_src), 'rb').read().decode('latin1')
        if a.talk_fed_from:
            t, k = add_fed(t, open(a.talk_fed_from, 'rb').read().decode('latin1'))
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
