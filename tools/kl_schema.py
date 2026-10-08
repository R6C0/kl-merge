"""
Exact property schemas from a Glacier exe (kl2.exe / kaneandlynch.exe), via the engine's own
run-time property reflection (RTP). Ported from HHCHunter/hbm-editor (packages/formats/src/rtp).

A class deriving from RTP::cBase has GetProperties in its vtable: `mov eax, <ZPropertyInfo>; ret`.
ZPropertyInfo { +0 First cNode*, +4 Super ZPropertyInfo*, +8 Name }; cNode { +0 Next, +4 Name,
+8 Filter, +0xC handler } and handler slot 0 is the Load function, which identifies the type.
Level files load records whose Filter has bit 0. Base classes load first.

Controllers: a .data table of { name*, create* } pairs; the create function stamps the vtable
of the class it constructs, which names the class.
"""
import struct, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kl_rtti import Image, vtables

GETPROPS_SLOT = 11


class Schema:
    def __init__(self, exe):
        self.img = Image(exe)
        self.by_name, self.by_vt, self.bases = vtables(self.img)
        self._ctrl = None
        self._heads = None

    # -- property chains
    def head(self, cls):
        vt = self.by_name.get(cls)
        if vt is None:
            return None
        f = self.img.u32(vt + 4 * GETPROPS_SLOT)
        b = self.img.bytes(f, 6) if f else None
        if not b or b[0] != 0xb8 or b[5] != 0xc3:
            return None
        return struct.unpack_from('<I', b, 1)[0]

    def owners(self):
        if self._heads is None:
            self._heads = {}
            for cls, vt in self.by_name.items():
                if 'RTP::cBase' not in self.bases.get(cls, ()):
                    continue
                h = self.head(cls)
                if h is None:
                    continue
                cur = self._heads.get(h)
                if cur is None or len(self.bases[cur]) > len(self.bases[cls]):
                    self._heads[h] = cls
        return self._heads

    def chain(self, cls, level_only=True):
        """[(owner, [record...])] base first; record = dict(va, filter, load, enum)."""
        h = self.head(cls)
        if h is None:
            return None
        heads = []
        while h and h not in heads and len(heads) < 32:
            heads.append(h); h = self.img.u32(h + 4)
        img = self.img
        out = []
        for h in reversed(heads):
            recs, n, seen = [], img.u32(h), set()
            while n and n not in seen and len(recs) < 512:
                seen.add(n)
                filt, hnd = img.u32(n + 8), img.u32(n + 12)
                load = img.u32(hnd) if hnd else None
                if filt is None or load is None:
                    break
                if not level_only or filt & 1:
                    recs.append({'va': n, 'filter': filt, 'load': load, 'enum': self.enum_of(n, load)})
                n = img.u32(n)
            out.append((self.owners().get(h, '%#x' % h), recs))
        return out

    def fields(self, cls):
        c = self.chain(cls)
        return None if c is None else [r for _, recs in c for r in recs]

    # -- enums
    def enum_info(self, va):
        img = self.img
        name = img.cstr(img.u32(va + 4) or 0)
        size = img.u32(va + 8)
        if name is None or size is None or size > 8:
            return None
        opts, e, seen = [], img.u32(va), set()
        while e and e not in seen and len(opts) < 1024:
            seen.add(e)
            v, nm = img.u32(e + 4), img.cstr(img.u32(e + 8) or 0)
            if v is None or nm is None:
                break
            opts.append((nm, v)); e = img.u32(e)
        return {'name': name, 'size': size, 'options': list(reversed(opts))} if opts else None

    def enum_of(self, rec, load):
        # Enum records carry a ZEnumInfo* after the handler (member +0x14, accessor +0x20).
        for off in (0x14, 0x20):
            p = self.img.u32(rec + off)
            if p and (self.img.within('.data', p) or self.img.within('.rdata', p)):
                e = self.enum_info(p)
                if e:
                    return e
        return None

    # -- controllers
    def controllers(self):
        """scene controller name -> class name (via the create function's vtable stamp)."""
        if self._ctrl is not None:
            return self._ctrl
        img = self.img
        a0, vs, r0, rs = img.secs['.data']; dd = img.d[r0:r0 + rs]
        out = {}
        for i in range(0, len(dd) - 8, 4):
            s, f = struct.unpack_from('<II', dd, i)
            if not (img.within('.rdata', s) and img.within('.text', f)):
                continue
            nm = img.cstr(s, 64)
            if not nm or not nm[0].isalpha() or nm in out:
                continue
            cls = self.stamped_class(f)
            if cls:
                out[nm] = cls
        self._ctrl = out
        return out

    def stamped_class(self, fn, depth=0, found=None):
        found = set() if found is None else found
        img = self.img
        b = img.bytes(fn, 256)
        if not b:
            return None
        calls = 0
        j = 0
        while j + 6 <= len(b):
            if b[j] == 0xc7:
                for k in (j + 2, j + 3, j + 6):
                    if k + 4 <= len(b):
                        v = struct.unpack_from('<I', b, k)[0]
                        if v in self.by_vt:
                            found.add(self.by_vt[v])
            elif b[j] == 0xe8 and depth == 0 and calls < 6:
                calls += 1
                self.stamped_class(fn + j + 5 + struct.unpack_from('<i', b, j + 1)[0], 1, found)
            elif b[j] == 0xe9 and j == 0:
                return self.stamped_class(fn + 5 + struct.unpack_from('<i', b, 1)[0], depth, found)
            if b[j] == 0xcc and b[j + 1] == 0xcc:
                break
            j += 1
        if depth:
            return None
        if not found:
            return None
        return max(found, key=lambda c: len(self.bases.get(c, ())))


if __name__ == '__main__':
    s = Schema(sys.argv[1])
    for cls in sys.argv[2:]:
        c = s.controllers().get(cls, cls)
        print(cls, '->', c)
        for owner, recs in s.chain(c) or []:
            print('  ', owner, [(hex(r['load']), r['enum']['name'] if r['enum'] else '') for r in recs])
