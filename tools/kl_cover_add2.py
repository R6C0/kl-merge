#!/usr/bin/env python3
"""
TAKE THE DOUBTFUL EXTRA COVER BOXES OFF A MAP (cover2 'KL_CoverMore!' boxes, CoverBox?_KM_nn). 2026-10-24 17:20. OFFLINE.

    python kl_cover_add2.py plan   <live zip> <donor zip>                   which KM boxes would be switched off, and why
    python kl_cover_add2.py disable <live zip> <donor zip> <out folder>     the live zip with them switched off

WHY. Owner 16:50: 'sometimes going into cover it puts me inside the object and im stuck for the round'. cover2_1024
(kl_cover_add.py) laid up to 150 extra cover boxes per Dead Men map; two of its checks were not what they said:
  (1) 'not inside a NoCoverBox': rev2_1024 had already stripped the NoCoverBox controller of every box, and kl_cover_add.Lite
      finds a no-cover box by controller OR by a name holding 'nocoverbox' - after the strip only the name test is left, and
      the author's markers are named 'Respawn_HallWay_NoCover_07', 'NoCover_BugFix', 'Stairs_NoCover_01' ... (0 of 21 found on
      DM01, 0/31 DM11B, 5/40 DM03): the extra boxes were put INTO the very zones Dead Men itself forbade cover in;
  (2) kl_cover_add.sparse() fits a model to the object's rectangle within OVER (40) per axis, so the box can be SHORTER than
      the object: two of its four sides then lie inside the object, and the cover movement (four sides of the box, kl2
      0x603830) puts the player on a side that has no free floor.
This tool switches a KM box OFF when
  - a foot point of it (the 4 floor corners + middle, +50 up) is inside ANY box that carried NoCoverBox in the donor (the
    zip before rev_1024; its nodes are found in the live zip by path), or
  - kl_cover_vet finds a side ELEVATED (standing place on / in a solid) or DROP (over an edge) or 3 or more sides blocked.
OFF = the box's name has 'CoverBox' replaced by 'CvrOffBx' (same length, in place in the .buf: the .prp, .gms and every
other member stay byte for byte); the cover list (kl2 0x6d6a80) takes only names matching *coverbox*, so the box is no
cover any more and the model stays where it is (nothing in the level moves, no ids change). GUESS: 'ELEVATED/DROP/3 blocked'
use kl_cover_vet's STAND/BODY guesses; the NoCover-zone rule is evidence (author's marks), the vet rule is a ranking.
Proved on the result: the only member that differs is .buf; its length is unchanged; no other byte differs but the 8-letter
name stems of the boxes in the report; the cover boxes that are left all match the name test of the cover list.
"""
import json, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms, kl_graft
import kl_cover_add as A
import kl_cover_vet as V
import kl_cover_restore as R
import kl_fix_lean as FL

OLD, NEW = b'CoverBox', b'CvrOffBx'
BAD_SIDES = 3


def plan(lz, dz, log=print):
    A.use_slot(lz)
    L = A.Lite(lz)
    B, sc = L.B, L.B.sc
    don = R.donor_boxes(dz)
    cur = {sc.path[k]: k for k in range(1, len(sc.nodes))}
    zones = [cur[p] for p in don if p in cur]
    rep = V.vet(L, only=lambda n: '_KM_' in n)
    out = []
    for b in L.boxes:
        if '_KM_' not in b['name'] or b.get('cls', 'ZSTDOBJ') != 'ZSTDOBJ' or b.get('kind') is None or not b['bb']:
            continue
        k, bb = b['node'], b['bb']
        foot = [B.world(k, (x, bb[1] + 50.0, z)) for x in (bb[0], bb[3]) for z in (bb[2], bb[5])] \
            + [B.world(k, ((bb[0] + bb[3]) / 2, bb[1] + 50.0, (bb[2] + bb[5]) / 2))]
        why = None
        z = next((j for j in zones if any(B.in_box(j, q) for q in foot)), None)
        if z is not None:
            why = 'inside the former NoCoverBox %s' % sc.names[z]
        elif k in rep:
            st = rep[k]['sides']
            nb = sum(1 for v in st.values() if v == 'blocked')
            bad = [n for n, v in st.items() if v in ('elevated', 'drop')]
            if bad:
                why = 'side %s %s' % (bad[0], st[bad[0]])
            elif nb >= BAD_SIDES:
                why = '%d sides blocked' % nb
        if why:
            out.append((k, b['name'], why))
    n_km = sum(1 for b in L.boxes if '_KM_' in b['name'] and b.get('kind') is not None)
    log('%s: %d KM boxes, %d switched off (%d in a former NoCover zone)' % (
        os.path.basename(os.path.dirname(lz)), n_km, len(out), sum(1 for o in out if o[2].startswith('inside'))))
    return L, out


def disable(lz, dz, outdir, log=print):
    L, off = plan(lz, dz, log)
    if not off:
        raise ValueError('no box to switch off in %s' % lz)
    with zipfile.ZipFile(lz) as zf:
        prp = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
        stem = prp[:-4]
        raw = kl_gms.unpack(zf.read(stem + '.gms'))
        buf = bytearray(zf.read(stem + '.buf'))
        names = [None]
        offs = [None]
        for decl, tid, _prio in kl_gms.entities(raw):
            o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
            offs.append(o)
            names.append(buf[o:buf.index(b'\0', o)].decode('latin1'))
    if names != [None] + [L.B.sc.names[k] for k in range(1, len(L.B.sc.names))]:
        raise ValueError('the .gms names do not match the scene names')
    changed = []
    for k, nm, why in off:
        o = offs[k]
        s = bytes(buf[o:o + len(nm)])
        if s.decode('latin1') != nm or OLD not in s:
            raise ValueError('%s: name not where expected' % nm)
        i = o + s.index(OLD)
        buf[i:i + 8] = NEW
        changed.append(i)
    order, files, ext, sc, _l, _h = kl_graft.open_built(lz)
    old = files[ext['.buf']]
    if len(old) != len(buf):
        raise ValueError('length changed')
    files[ext['.buf']] = bytes(buf)
    os.makedirs(outdir, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(outdir, os.path.basename(lz)), [(n, files[n]) for n in order])
    diffs = [i for i in range(len(old)) if old[i] != buf[i]]
    allowed = {c + j for c in changed for j in range(8)}
    if any(i not in allowed for i in diffs):
        raise ValueError('more bytes differ than the name stems')
    with zipfile.ZipFile(lz) as a, zipfile.ZipFile(out) as b:
        ia, ib = a.infolist(), b.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        dm = [i.filename.rsplit('_Main', 1)[-1] for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if dm != ['.buf']:
        raise ValueError('more than the .buf differs: %s' % dm)
    # read back: the scene still loads, and the cover boxes that are left are all outside the report
    A.use_slot(out)
    L2 = A.Lite(out)
    left = [b['name'] for b in L2.boxes if b.get('kind') is not None and '_KM_' in b['name']]
    gone = {nm for _k, nm, _w in off}
    if any(nm in left for nm in gone):
        raise ValueError('a switched-off box still counts as cover')
    log('%s: %d KM boxes off, %d KM boxes left; only %s differs, %d bytes' % (os.path.basename(lz), len(off), len(left), dm, len(diffs)))
    with open(out + '.cover2b.json', 'w') as fh:
        json.dump({'live': lz, 'donor': dz, 'off': [{'node': k, 'name': nm, 'why': w} for k, nm, w in off], 'left': left}, fh, indent=1)
    return out


def main():
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == 'plan':
        L, off = plan(a[1], a[2])
        for k, nm, w in off:
            print('  OFF %s: %s' % (nm, w))
    elif len(a) == 4 and a[0] == 'disable':
        disable(a[1], a[2], a[3])
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
