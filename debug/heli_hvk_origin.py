"""heli_hvk_origin.py <heli build folder> <out folder>   Variant of a Last Call heli build whose chopper vehicle placement (.HVK, shape type 3) stays at the
ORIGIN with the identity frame, as in stock M06_FA_A / F03 / F06 (what `python tools/kl_fa_club.py test <out> --exit heli-roof --hvk-origin` leaves
heli_hvk to do on a fresh build). It copies EVERY file of the folder and rewrites only the placement bytes of the one type-3 placement inside
F01_Main.zip's .HVK (same size; every other member is copied unchanged, decompressed and recompressed). Proof printed: the placement found must equal
heli_hvk's forward motion of (origin, identity), so the inverse is exact. Read only on the source; nothing installed."""
import os, shutil, struct, sys, zipfile, hashlib, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import kl_hvk

HVK = 'Scenes/Locations/F01/F01_Main.HVK'
IDENT = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def main(src, out):
    if os.path.exists(out):
        sys.exit('refusing to write into an existing %s' % out)
    os.makedirs(out)
    for f in os.listdir(src):
        if f != 'F01_Main.zip':
            shutil.copy2(os.path.join(src, f), os.path.join(out, f))
    zin = zipfile.ZipFile(os.path.join(src, 'F01_Main.zip'))
    h = kl_hvk.Hvk(zin.read(HVK))
    hits = [(s, j) for s in h.shapes if s.type == kl_hvk.VEHICLE for j in range(len(s.inst))]
    if len(hits) != 1:
        sys.exit('expected exactly one vehicle placement, found %d' % len(hits))
    s, j = hits[0]
    inst = s.inst[j]
    p, m = struct.unpack_from('<3f', inst, 0), struct.unpack_from('<9f', inst, 12)
    # the forward motion of (origin, identity) is  p' = heli_to(origin) (cm -> m),  m' = R: R must be a yaw about y and p' must be heli_to's image
    c, sn = m[0], -m[2]          # heli_hvk: R = ((c,0,-s),(0,1,0),(s,0,c)) times the identity
    ok = abs(m[4] - 1) < 1e-5 and abs(c * c + sn * sn - 1) < 1e-5 and abs(m[8] - c) < 1e-5 and abs(m[6] - sn) < 1e-5
    print('moved placement: REF %d pos %s rot yaw %.2f deg; pure yaw about y: %s' % (kl_hvk.ref(inst), tuple(round(x, 3) for x in p), math.degrees(math.atan2(sn, c)), ok))
    if not ok:
        sys.exit('the placement is not a pure yaw about y: not the heli_hvk motion of the identity')
    # the landing point (-1535, 368, -6276) and pad (-2900, 859, 3900) cm of the build: p' = pad + (-land) turned, y + 859 - 0
    land, pad = (-1535.0, 368.0, -6276.0), (-2900.0, 859.0, 3900.0)
    x, z = -land[0], -land[2]
    fwd = ((pad[0] + x * c - z * sn) / 100, 8.59, (pad[2] + x * sn + z * c) / 100)
    print('forward image of the origin with this yaw: %s (max error %.4f m)' % (tuple(round(v, 3) for v in fwd), max(abs(fwd[i] - p[i]) for i in range(3))))
    if max(abs(fwd[i] - p[i]) for i in range(3)) > 0.05:
        sys.exit('the placement is not the image of the origin: refusing')
    s.inst[j] = struct.pack('<3f9f', 0.0, 0.0, 0.0, *IDENT) + inst[48:]
    data = h.serialize()
    old = zin.read(HVK)
    assert len(data) == len(old)
    diff = [i for i in range(len(old)) if old[i] != data[i]]
    print('HVK bytes changed: %d (all inside the one 0x38 placement: %s)' % (len(diff), max(diff) - min(diff) < 0x30))
    with zipfile.ZipFile(os.path.join(out, 'F01_Main.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zo:
        for i in zin.infolist():
            zi = zipfile.ZipInfo(i.filename, i.date_time)
            zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, i.external_attr
            zo.writestr(zi, data if i.filename == HVK else zin.read(i.filename))
    b = open(os.path.join(out, 'F01_Main.zip'), 'rb').read()
    print('F01_Main.zip md5 %s sha1 %s' % (hashlib.md5(b).hexdigest(), hashlib.sha1(b).hexdigest()))


if __name__ == '__main__':
    main(*sys.argv[1:3])
