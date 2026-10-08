"""
MSVC RTTI and vtable index for a 32-bit Glacier exe (kl2.exe / kaneandlynch.exe).
Ported from HHCHunter/hbm-editor packages/formats/src/pe/msvcRtti.ts.
"""
import struct, re, pefile


class Image:
    def __init__(self, path):
        self.pe = pefile.PE(path, fast_load=True)
        self.d = open(path, 'rb').read()
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = {}
        for s in self.pe.sections:
            self.secs[s.Name.rstrip(b'\0').decode()] = (self.base + s.VirtualAddress,
                                                        max(s.Misc_VirtualSize, s.SizeOfRawData),
                                                        s.PointerToRawData, s.SizeOfRawData)

    def off(self, va):
        for a, vs, r, rs in self.secs.values():
            if a <= va < a + rs:
                return r + va - a
        return None

    def u32(self, va):
        o = self.off(va)
        return struct.unpack_from('<I', self.d, o)[0] if o is not None and o + 4 <= len(self.d) else None

    def u8(self, va):
        o = self.off(va)
        return self.d[o] if o is not None else None

    def bytes(self, va, n):
        o = self.off(va)
        return self.d[o:o + n] if o is not None else None

    def cstr(self, va, maxlen=200):
        o = self.off(va)
        if o is None:
            return None
        e = self.d.find(b'\0', o, o + maxlen)
        if e < 0:
            return None
        s = self.d[o:e]
        return s.decode('latin1') if all(32 <= c < 127 for c in s) else None

    def within(self, name, va):
        s = self.secs.get(name)
        return bool(s) and s[0] <= va < s[0] + s[1]


def demangle(m):
    r = re.match(r'^\.\?A[VU](.+)@@$', m)
    if not r or '?' in r.group(1):
        return None
    return '::'.join(reversed(r.group(1).split('@')))


def vtables(img):
    """-> (by_name, by_vtable, bases) using CompleteObjectLocators in .rdata."""
    a0, vs, r0, rs = img.secs['.rdata']
    rd = img.d[r0:r0 + rs]
    cands, votes = [], {}
    for i in range(0, len(rd) - 4, 4):
        loc = struct.unpack_from('<I', rd, i)[0]
        if not img.within('.rdata', loc):
            continue
        if img.u32(loc) != 0 or img.u32(loc + 4) != 0 or img.u32(loc + 8) != 0:
            continue
        td = img.u32(loc + 12)
        if td is None or not (img.within('.data', td) or img.within('.rdata', td)):
            continue
        nm = img.cstr(td + 8)
        name = demangle(nm) if nm else None
        tiv = img.u32(td)
        if not name or tiv is None:
            continue
        cands.append((a0 + i + 4, tiv, name, img.u32(loc + 16)))
        votes[tiv] = votes.get(tiv, 0) + 1
    ti = max(votes, key=votes.get)
    by_name, by_vt, bases = {}, {}, {}
    for vt, tiv, name, hier in cands:
        if tiv != ti or name in by_name:
            continue
        by_name[name] = vt; by_vt[vt] = name
        lst = []
        cnt = img.u32(hier + 8) if hier else None
        arr = img.u32(hier + 12) if hier else None
        if cnt is not None and arr is not None and cnt < 64:
            for k in range(cnt):
                bd = img.u32(arr + 4 * k)
                td = img.u32(bd) if bd else None
                nm = img.cstr(td + 8) if td else None
                dn = demangle(nm) if nm else None
                if dn:
                    lst.append(dn)
        bases[name] = lst or [name]
    return by_name, by_vt, bases


if __name__ == '__main__':
    import sys
    img = Image(sys.argv[1])
    bn, bv, bs = vtables(img)
    print(len(bn), 'classes')
    for n in sys.argv[2:]:
        print(n, hex(bn.get(n, 0)), bs.get(n))
