"""Rebake ONLY the shop text (.LOC members) of an installed level archive (worker shop2, 2026-10-15).
usage: python3 shopbake.py <installed map folder> <out folder>
Reads <map>/<slot>_Main.zip + <map>/KLGuns.ini, runs kl_hud_shop.apply_level on the .LOC members only, and writes
<out>/<slot>_Main.zip: every other member's local header + compressed bytes are copied RAW (byte-identical), the
member order, names, dates, attributes and central-directory fields are the original's; only a changed .LOC member gets
new deflate data, CRC and sizes. Then verifies the output."""
import os, sys, struct, zlib, zipfile, shutil, hashlib
sys.path.insert(0, os.path.expanduser('~/w_shop2/tools'))
import kl_hud_shop

def main(mapdir, outdir):
    zp = next(os.path.join(mapdir, f) for f in sorted(os.listdir(mapdir)) if f.lower().endswith('_main.zip'))
    guns = os.path.join(mapdir, 'KLGuns.ini')
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, os.path.basename(zp))
    z = zipfile.ZipFile(zp)
    il = z.infolist()
    for i in il:
        assert i.flag_bits & ~0x800 == 0 and i.compress_type in (0, 8), (i.filename, i.flag_bits, i.compress_type)
    locs = {i.filename: z.read(i) for i in il if i.filename.lower().endswith('.loc')}
    files = dict(locs)
    counts = {}
    def log(s): print('  ' + s, flush=True)
    # per-member counts: apply_level changes files in place; count leaves with apply_loc on the same inputs
    looks = kl_hud_shop.read_looks(guns, log)
    changed = kl_hud_shop.apply_level(files, log, guns=guns)
    en = [m for m in locs if m.lower().endswith('english.loc')]
    for m in changed:
        _o, n = kl_hud_shop.apply_loc(locs[m], m == en[0], lambda s: None, m, looks)
        counts[m] = n
    if not changed:
        print('NOTHING CHANGED - no output written'); return 1
    # raw rewrite
    f = open(zp, 'rb')
    cd = []  # central dir entries (bytes)
    f.seek(z.start_dir); cdraw = f.read()
    # parse original central entries
    p = 0; cents = []
    for i in il:
        assert cdraw[p:p+4] == b'PK\x01\x02'
        nl, el, cl = struct.unpack('<HHH', cdraw[p+28:p+34])
        cents.append(bytearray(cdraw[p:p+46+nl+el+cl])); p += 46 + nl + el + cl
    eocd = cdraw[p:]
    assert eocd[:4] == b'PK\x05\x06', 'no plain EOCD (zip64?)'
    tmp = dst + '.part'
    o = open(tmp, 'wb')
    for idx, i in enumerate(il):
        f.seek(i.header_offset); lh = bytearray(f.read(30))
        assert lh[:4] == b'PK\x03\x04'
        nl, el = struct.unpack('<HH', lh[26:30])
        name_extra = f.read(nl + el)
        newoff = o.tell()
        if i.filename in changed:
            data = files[i.filename]
            c = zlib.compressobj(9, zlib.DEFLATED, -15); comp = c.compress(data) + c.flush()
            crc = zlib.crc32(data) & 0xffffffff
            struct.pack_into('<III', lh, 14, crc, len(comp), len(data))
            o.write(lh); o.write(name_extra); o.write(comp)
            struct.pack_into('<III', cents[idx], 16, crc, len(comp), len(data))
        else:
            o.write(lh); o.write(name_extra)
            left = i.compress_size
            while left:
                b = f.read(min(left, 8 << 20)); assert b; o.write(b); left -= len(b)
        struct.pack_into('<I', cents[idx], 42, newoff)
    cdoff = o.tell()
    for c in cents: o.write(c)
    cdsize = o.tell() - cdoff
    e = bytearray(eocd); struct.pack_into('<II', e, 12, cdsize, cdoff); o.write(e)
    o.close(); f.close()
    os.replace(tmp, dst)
    # verify
    a, b = zipfile.ZipFile(zp), zipfile.ZipFile(dst)
    ia, ib = a.infolist(), b.infolist()
    assert [x.filename for x in ia] == [x.filename for x in ib], 'member order/names differ'
    fa, fb = open(zp, 'rb'), open(dst, 'rb')
    def raw(fh, i):
        fh.seek(i.header_offset + 26); nl, el = struct.unpack('<HH', fh.read(4)); fh.seek(i.header_offset)
        return fh.read(30 + nl + el + i.compress_size)
    diff = []
    for x, y in zip(ia, ib):
        for fld in ('date_time', 'compress_type', 'external_attr', 'create_system', 'flag_bits', 'extra', 'comment'):
            assert getattr(x, fld) == getattr(y, fld), (x.filename, fld)
        if x.filename in changed:
            assert b.read(y.filename) == files[x.filename]      # CRC-checked read
            diff.append(x.filename)
        else:
            assert x.compress_size == y.compress_size and x.CRC == y.CRC and x.file_size == y.file_size
            ra, rb = raw(fa, x), raw(fb, y)
            assert ra == rb, 'raw entry differs: ' + x.filename
    bad = b.testzip()
    assert bad is None, 'testzip: ' + bad
    # second pass must change nothing
    again = {n: b.read(n) for n in changed}
    assert kl_hud_shop.apply_level(again, lambda s: None, guns=guns) == [], 'second pass not idempotent'
    sa, sb = os.path.getsize(zp), os.path.getsize(dst)
    h = hashlib.sha1(); fb.seek(0)
    for blk in iter(lambda: fb.read(8 << 20), b''): h.update(blk)
    print('OK %s -> %s  members=%d  changed .LOC=%d  size %d -> %d (%+d)  sha1=%s' % (zp, dst, len(ia), len(diff), sa, sb, sb - sa, h.hexdigest()))
    for m in changed: print('   %-50s %d leaves' % (m.rsplit('/', 1)[-1], counts[m]))
    print('   total leaves %d' % sum(counts.values()))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
