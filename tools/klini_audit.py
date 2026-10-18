#!/usr/bin/env python3
r"""klini_audit.py - does every per-map KL*.ini belong to the .prm beside it?

    python tools/klini_audit.py [MAPS_ROOT ...] [--map DM05A] [--quiet]

MAPS_ROOT defaults to <DD>\KLExpansion\Maps; also use C:\kl_build_1018\owner_1018\Maps.
Exit 0 = all OK, 1 = something STALE.

What the hook checks (klhook sources):
  KLGuns.ini  [Guns] Entries=  must equal the loaded .prm's chunk count (klgun.c klg_tick: klg_f.entries != count -> "was written
              for a .prm of N chunks" and nothing is written). A Version 2 file without Entries is refused too.
  KLJoin.ini  [FedBody] Entries=  the same (klfedkit.c klfk_level_ok), and Root < Entries.
  KLWardrobe.ini  no count is compared (klchar.c reads Root= per character); GUESS: a Root at or past the chunk count can only be a
              file from a larger build, so that is reported as STALE. A wardrobe file is not otherwise provable from the archive.
The chunk count is dword +4 of the archive's .prm (kl_map_guns.ini_entries reads it the same way).
Pure reader: writes nothing.
"""
import configparser, glob, os, re, struct, sys, zipfile

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'


def prm_count(folder):
    """-> (chunk count, archive name) of the folder's F0x_Main.zip, or (None, why)"""
    zs = sorted(glob.glob(os.path.join(folder, 'F??_Main.zip')))
    if not zs:
        return None, 'no F0x_Main.zip'
    with zipfile.ZipFile(zs[0]) as z:
        names = [n for n in z.namelist() if n.lower().endswith('.prm')]
        if not names:
            return None, os.path.basename(zs[0]) + ' has no .prm'
        with z.open(names[0]) as f:
            head = f.read(8)
    return struct.unpack_from('<I', head, 4)[0], os.path.basename(zs[0])


def read_ini(path):
    cp = configparser.RawConfigParser(strict=False)
    cp.optionxform = str
    txt = open(path, encoding='latin1').read()
    # the hook's GetPrivateProfile*: ';' lines are comments, duplicate keys keep the first
    cp.read_string(txt)
    return cp


def ini_get(cp, sec, key):
    if cp.has_section(sec) and cp.has_option(sec, key):
        return cp.get(sec, key).split(';')[0].strip()
    return None


def audit_map(folder):
    """-> list of (ini name, status 'OK'|'STALE'|'NOTE', want, have, text)"""
    out = []
    n, arch = prm_count(folder)
    for ini in ('KLGuns.ini', 'KLJoin.ini', 'KLWardrobe.ini'):
        p = os.path.join(folder, ini)
        if not os.path.isfile(p):
            continue
        if n is None:
            out.append((ini, 'STALE', None, None, arch)); continue
        cp = read_ini(p)
        if ini == 'KLGuns.ini':
            have = ini_get(cp, 'Guns', 'Entries')
            ver = ini_get(cp, 'Guns', 'Version')
            if have is None and ver == '2':
                out.append((ini, 'STALE', n, None, 'Version 2 without Entries= (refused)'))
            elif have is None:
                out.append((ini, 'NOTE', n, None, 'no Entries= (Version %s)' % ver))
            else:
                out.append((ini, 'OK' if have == str(n) else 'STALE', n, have, ''))
        elif ini == 'KLJoin.ini':
            if not cp.has_section('FedBody'):
                out.append((ini, 'NOTE', n, None, 'no [FedBody] section (nothing to check)')); continue
            have = ini_get(cp, 'FedBody', 'Entries')
            root = ini_get(cp, 'FedBody', 'Root')
            st = 'OK' if have == str(n) else 'STALE'
            txt = ''
            if st == 'OK' and root and root.isdigit() and int(root) >= n:
                st, txt = 'STALE', 'Root=%s is not below Entries' % root
            out.append((ini, st, n, have, txt))
        else:
            roots = [int(v) for s in cp.sections() if s.startswith('Character.')
                     for v in [ini_get(cp, s, 'Root')] if v and v.isdigit()]
            bad = [r for r in roots if r >= n]
            out.append((ini, 'STALE' if bad else 'OK', n, max(roots) if roots else None,
                        ('%d of %d Root(s) >= chunk count' % (len(bad), len(roots))) if bad else '%d Root(s), max below count' % len(roots)))
    return out


def audit_root(root, only=None, quiet=False):
    stale = 0
    rows = []
    for d in sorted(os.listdir(root)):
        folder = os.path.join(root, d)
        if not os.path.isdir(folder) or '.replaced' in d or (only and d.upper() != only.upper()):
            continue
        for ini, st, want, have, txt in audit_map(folder):
            rows.append((d, ini, st, want, have, txt))
    for d, ini, st, want, have, txt in rows:
        stale += st == 'STALE'
        if quiet and st == 'OK':
            continue
        print('%-7s %-15s %-5s want %-7s have %-7s %s' % (d, ini, st, want, have, txt))
    print('%s: %d ini(s), %d STALE' % (root, len(rows), stale))
    return stale


def main():
    a = sys.argv[1:]
    quiet = '--quiet' in a
    only = None
    if '--map' in a:
        i = a.index('--map'); only = a[i + 1]; del a[i:i + 2]
    a = [x for x in a if not x.startswith('--')]
    roots = a or [os.path.join(DD, 'KLExpansion', 'Maps')]
    return 1 if sum(audit_root(r, only, quiet) for r in roots) else 0


if __name__ == '__main__':
    sys.exit(main())
