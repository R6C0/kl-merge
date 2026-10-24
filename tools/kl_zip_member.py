#!/usr/bin/env python3
"""
Replace ONE member of a zip, every other member byte-for-byte the same (decompressed), same order, same compression.
Self-contained (standard library only): the installer of a build that touches one member (kl_club_music.py) ships it.

    python kl_zip_member.py replace <in.zip> <member> <new file> <out.zip>
    python kl_zip_member.py md5 <zip> <member>        md5 of one member (decompressed)
    python kl_zip_member.py same <a.zip> <b.zip> <member to ignore>   exit 0 if all other members are identical
"""
import hashlib, sys, zipfile


def replace(src, member, new, dst):
    data = open(new, 'rb').read()
    n = 0
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w', allowZip64=True) as zo:
        for info in zi.infolist():
            i2 = zipfile.ZipInfo(info.filename, info.date_time)
            i2.compress_type, i2.external_attr, i2.create_system = info.compress_type, info.external_attr, info.create_system
            i2.comment, i2.extra = info.comment, b''
            if info.filename == member:
                zo.writestr(i2, data, compress_type=info.compress_type); n += 1
            else:
                with zi.open(info) as fi, zo.open(i2, 'w', force_zip64=info.file_size > 0x7fffffff) as fo:
                    while True:
                        c = fi.read(1 << 20)
                        if not c:
                            break
                        fo.write(c)
    if n != 1:
        raise SystemExit('%s: member %r found %d times' % (src, member, n))


def md5(path, member):
    with zipfile.ZipFile(path) as z:
        return hashlib.md5(z.read(member)).hexdigest()


def same(a, b, ignore):
    with zipfile.ZipFile(a) as za, zipfile.ZipFile(b) as zb:
        na, nb = [i.filename for i in za.infolist()], [i.filename for i in zb.infolist()]
        if na != nb:
            print('member lists differ'); return False
        bad = 0
        for n in na:
            if n == ignore:
                continue
            ia, ib = za.getinfo(n), zb.getinfo(n)
            if (ia.CRC, ia.file_size, ia.compress_type) != (ib.CRC, ib.file_size, ib.compress_type):
                print('differs:', n); bad += 1
        return not bad


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['replace'] and len(a) == 5:
        replace(a[1], a[2], a[3], a[4])
    elif a[:1] == ['md5'] and len(a) == 3:
        print(md5(a[1], a[2]))
    elif a[:1] == ['same'] and len(a) == 4:
        sys.exit(0 if same(a[1], a[2], a[3]) else 1)
    else:
        print(__doc__)
