#!/usr/bin/env python3
"""
Every installed map's ini Entries= against its .prm chunk count. Read-only.

KLGuns.ini [Guns] Entries and KLJoin.ini [FedBody] Entries must equal the chunk count of the .prm in the map's installed
F0x_Main.zip; when they differ the hook ignores that file (klfedkit.c: Entries == [0xeac7a4]) and the gun looks / fed outfits
silently stay off. Any install that changes a map's .prm (vans, grenades, overhauls, guns) must regenerate both files after it.
Found 2026-10-25: DM02, DM03A, DM06, DM09, DM11B gun looks and DM01 fed outfits stale.

    python kl_entries_check.py [<KLExpansion\\Maps folder>]      exit 1 when any map is stale

Since 2026-10-25 tools/kl_slotcheck.py runs the same test (check_entries) on a STAGE tree before INSTALL, as a FAIL.
"""
import os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph

MAPS = r"C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps"


def check(maps):
    bad = 0
    for m in sorted(os.listdir(maps)):
        d = os.path.join(maps, m)
        zs = [f for f in os.listdir(d) if re.fullmatch(r'F\d\d_Main\.zip', f)] if os.path.isdir(d) else []
        if not zs:
            continue
        z = zipfile.ZipFile(os.path.join(d, zs[0]))
        prm = [n for n in z.namelist() if n.lower().endswith('.prm')]
        n = len(kl_prmgraph.read(z.read(prm[0])).chunks)
        out = []
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith('.ini'):
                continue
            sec = ''
            for line in open(os.path.join(d, f), encoding='latin-1'):
                s = line.strip()
                if s.startswith('['):
                    sec = s
                e = re.match(r'Entries\s*=\s*(\d+)', s)
                if e:
                    stale = int(e.group(1)) != n
                    bad += stale
                    out.append('%s%s=%s%s' % (f, sec, e.group(1), ' <-- STALE' if stale else ''))
        print('%-8s prm chunks %6d  %s' % (m, n, '; '.join(out) or '(no Entries)'))
    print('stale: %d' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if check(sys.argv[1] if len(sys.argv) > 1 else MAPS) else 0)
