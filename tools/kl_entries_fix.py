#!/usr/bin/env python3
"""
Re-sync KLGuns.ini [Guns] Entries= and KLJoin.ini [FedBody] Entries= with the .prm chunk count of each installed map (2026-11-06).

Use it only after a bake that APPENDED chunks to the .prm (every old chunk index unchanged), so the ini's Root / chunk numbers stay
valid and only the Entries guard is stale. Found 2026-11-06: kl_shop_pics adds 72 chunks (a sprite + a picture chunk per card,
36 cards) on every map and did not touch the inis, so the hook refused every KLGuns.ini / KLJoin.ini (gun looks, fed bodies off).

    python kl_entries_fix.py --delta 72 [--skip DM05A ...] [--maps DD01 ...] [--go] [<KLExpansion\\Maps folder>]
    python kl_entries_fix.py --undo [--maps ...] [--go]

A file is changed only when its Entries equals (plain .prm chunks - delta) AND the bots zip's .prm has the same chunk count as the
plain one; anything else is reported and left alone. Dry by default. Backup tag .before-entries1106 (the undo puts it back only
when the live file is still exactly what this tool wrote).
"""
import os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph

MAPS = r"C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps"
TAG = '.before-entries1106'
FILES = (('KLGuns.ini', 'Guns'), ('KLJoin.ini', 'FedBody'))


def prm_chunks(zp):
    z = zipfile.ZipFile(zp)
    prm = [n for n in z.namelist() if n.lower().endswith('.prm')]
    return len(kl_prmgraph.read(z.read(prm[0])).chunks)


def section_entries(txt, sec):
    """-> (start, end, value) of the Entries= value inside [sec], or None"""
    m = re.search(r'(?im)^\[%s\][^\n]*\n' % re.escape(sec), txt)
    if not m:
        return None
    nxt = re.search(r'(?m)^\[', txt[m.end():])
    body_end = m.end() + (nxt.start() if nxt else len(txt) - m.end())
    e = re.search(r'(?im)^Entries\s*=\s*(\d+)', txt[m.end():body_end])
    if not e:
        return None
    return m.end() + e.start(1), m.end() + e.end(1), int(e.group(1))


def main(a):
    go, undo = '--go' in a, '--undo' in a
    opt = lambda k: a[a.index(k) + 1:] if k in a else []
    lst = lambda k: [x for x in opt(k)[:next((i for i, x in enumerate(opt(k)) if x.startswith('--')), len(opt(k)))]]
    delta = int(opt('--delta')[0]) if '--delta' in a else None
    skip, only = set(lst('--skip')), set(lst('--maps'))
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] not in ('--delta',)) and x not in skip | only]
    maps = pos[0] if pos else MAPS
    if not undo and delta is None:
        raise SystemExit('--delta N is required (the number of chunks the bake appended)')
    changed = refused = 0
    for m in sorted(os.listdir(maps)):
        d = os.path.join(maps, m)
        if not os.path.isdir(d) or m in skip or (only and m not in only):
            continue
        zs = [f for f in os.listdir(d) if re.fullmatch(r'F\d\d_Main\.zip', f)]
        if not zs:
            continue
        if undo:
            for f, _ in FILES:
                p = os.path.join(d, f)
                if os.path.exists(p + TAG):
                    print('%-6s %s: restore from %s%s' % (m, f, TAG, '' if go else ' (dry)'))
                    if go:
                        os.replace(p + TAG, p)
                    changed += 1
            continue
        n = prm_chunks(os.path.join(d, zs[0]))
        bots = os.path.join(d, zs[0][:-4] + '.bots.zip')
        nb = prm_chunks(bots) if os.path.exists(bots) else n
        for f, sec in FILES:
            p = os.path.join(d, f)
            if not os.path.exists(p):
                continue
            raw = open(p, 'rb').read()
            txt = raw.decode('latin-1')
            se = section_entries(txt, sec)
            if not se:
                continue
            s, e, v = se
            if v == n:
                print('%-6s %s [%s] Entries=%d ok' % (m, f, sec, v))
                continue
            if v != n - delta or nb != n:
                print('%-6s %s [%s] Entries=%d, prm %d, bots prm %d: NOT a +%d append, left alone' % (m, f, sec, v, n, nb, delta))
                refused += 1
                continue
            print('%-6s %s [%s] Entries %d -> %d%s' % (m, f, sec, v, n, '' if go else ' (dry)'))
            if go:
                if os.path.exists(p + TAG):
                    raise SystemExit('%s exists already: undo first' % (p + TAG))
                os.replace(p, p + TAG)
                with open(p, 'wb') as o:
                    o.write((txt[:s] + str(n) + txt[e:]).encode('latin-1'))
            changed += 1
    print('RESULT: %d file(s) %s, %d left alone%s' % (changed, 'restored' if undo else 'fixed', refused, '' if go else ' (dry run, nothing written)'))
    return 1 if refused else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
