#!/usr/bin/env python3
"""
Cover on the installed Dead Men maps (owner 2026-10-24: 'withdrawal dont let you go into cover', 'majority of objects
you can press C').  OFFLINE: reads the installed zips, writes ONLY into a staging folder.

    python kl_cover_pass.py scan [MAP ...]            counts per installed map: NoCoverBox, cover boxes, cars
    python kl_cover_pass.py strip <zip> <out folder>  the zip with the NoCoverBox controller taken off every box
                                                      (only the .prp member differs; no sibling files are copied)

Cause read from the exe (re/lean_m02.md, kl_fix_lean.py docstring): ZFFPlayerMovementStandCover slot 14 (0x71f050) answers
0 when the player stands inside a NoCoverBox, so the C key does nothing there.  Stock Dog Days maps have none, Dead Men
maps carry 20..90.  ASSUMPTION (reading only, not proven live): slot 14 is 'may this movement run'.
"""
import os, sys, zipfile, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fix_lean as L
import kl_graft
import kl_prpjoin as J

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = os.path.join(DD, 'KLExpansion', 'Maps')


def zips(m):
    d = os.path.join(MAPS, m)
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith('_main.zip')]


def scan(maps, log=print):
    for m in maps or sorted(x for x in os.listdir(MAPS) if x.startswith('DM') or x == 'T01'):
        for zp in zips(m):
            try:
                order, files, ext, sc, _l, _h = kl_graft.open_built(zp)
                nb = len(L.boxes(sc))
                cov = [k for k in range(1, len(sc.nodes)) if any(t in sc.names[k].lower() for t in L.COVER)]
                cars = sum(1 for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZHavokCar')
                log('%-8s %s  NoCoverBox %3d  cover boxes %4d  ZHavokCar %3d' % (m, os.path.basename(zp), nb, len(cov), cars))
            except Exception as e:                                  # one bad map must not stop the scan
                log('%-8s %s  FAILED %s' % (m, os.path.basename(zp), e))


def strip(zp, outdir, log=print):
    """zp with NoCoverBox off every box -> outdir/<same name>; only the .prp member differs."""
    order, files, ext, sc, _l, _h = kl_graft.open_built(zp)
    if sc.p.serialize() != files[ext['.prp']]:
        raise ValueError('the .prp does not re-serialise byte for byte: not changed')
    data0, bad0, _p, _n = J.check(sc, log=lambda *_a: None)
    took = []
    for k in L.boxes(sc):
        n = sc.nodes[k]
        n['ctrls'] = [c for c in n['ctrls'] if sc.p.key(c[0]) != L.CTRL]
        took.append(sc.path[k])
    if not took:
        raise ValueError('no NoCoverBox in %s' % zp)
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    if len(bad) > len(bad0):
        raise ValueError('%d objects do not fit their class after the change (%d before)' % (len(bad), len(bad0)))
    if L.boxes(sc):
        raise ValueError('a NoCoverBox is left')
    files[ext['.prp']] = data
    os.makedirs(outdir, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(outdir, os.path.basename(zp)), [(n, files[n]) for n in order])
    with zipfile.ZipFile(zp) as a, zipfile.ZipFile(out) as b:
        ia, ib = a.infolist(), b.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        diff = [i.filename.rsplit('_Main', 1)[-1] for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if diff != ['.prp']:
        raise ValueError('more than the .prp differs: %s' % diff)
    log('%s: NoCoverBox off %d objects; only %s differs (%d -> %d bytes)' % (os.path.basename(zp), len(took), diff, len(data0), len(data)))
    with open(out + '.nocover.json', 'w') as fh:
        json.dump({'source': zp, 'taken': took}, fh, indent=1)
    return out


def main():
    a = sys.argv[1:]
    if a[:1] == ['scan']:
        scan(a[1:])
    elif len(a) == 3 and a[0] == 'strip':
        strip(a[1], a[2])
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
