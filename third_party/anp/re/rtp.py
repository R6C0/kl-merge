"""Property reflection (RTP) reader for Glacier 1 exes: class -> ordered property names/filters/loaders.
Own implementation; structure facts: GetProperties = vtable slot 11 (`mov eax, info; ret`),
ZPropertyInfo {+0 first node, +4 super info, +8 name}, node {+0 next, +4 name, +8 filter, +0xc handler}."""
import struct, re, sys, pefile
class Img:
    def __init__(s, path):
        s.pe = pefile.PE(path, fast_load=True); s.d = open(path, 'rb').read(); s.base = s.pe.OPTIONAL_HEADER.ImageBase
        s.secs = [(s.base + x.VirtualAddress, x.SizeOfRawData, x.PointerToRawData, x.Name.rstrip(b'\0').decode()) for x in s.pe.sections]
    def off(s, va):
        for a, n, r, _ in s.secs:
            if a <= va < a + n: return r + va - a
    def u32(s, va):
        o = s.off(va); return struct.unpack_from('<I', s.d, o)[0] if o is not None else None
    def cstr(s, va, m=128):
        o = s.off(va)
        if o is None: return None
        e = s.d.find(b'\0', o, o + m); return s.d[o:e].decode('latin1') if e > 0 else None
    def sec(s, name):
        for a, n, r, nm in s.secs:
            if nm == name: return a, n, r
def vtable_by_class(img):
    a, n, r = img.sec('.rdata'); out = {}
    rd = img.d[r:r + n]
    for i in range(0, n - 4, 4):
        col = struct.unpack_from('<I', rd, i)[0]
        if not (a <= col < a + n): continue
        if img.u32(col) != 0: continue
        td = img.u32(col + 12)
        if td is None: continue
        nm = img.cstr(td + 8)
        if not nm or not nm.startswith('.?AV'): continue
        if img.u32(col + 4) != 0: continue          # primary vtable only (offset 0)
        cls = nm[4:-2] if nm.endswith('@@') else nm
        out.setdefault(cls, a + i + 4)
    return out
def props(img, vt):
    f = img.u32(vt + 11 * 4); o = img.off(f) if f else None
    if o is None or img.d[o] != 0xb8 or img.d[o + 5] != 0xc3: return None
    info = struct.unpack_from('<I', img.d, o + 1)[0]
    levels = []; seen = set()
    while info and info not in seen and len(levels) < 32:
        seen.add(info)
        nm = img.cstr(img.u32(info + 8) or 0)
        recs = []; node = img.u32(info); k = 0
        while node and k < 400:
            recs.append(dict(name=img.cstr(img.u32(node + 4) or 0), filt=img.u32(node + 8), load=img.u32(img.u32(node + 12) or 0) if img.u32(node + 12) else None))
            node = img.u32(node); k += 1
        levels.append((nm, recs)); info = img.u32(info + 4)
    return list(reversed(levels))
if __name__ == '__main__':
    img = Img(sys.argv[1]); vts = vtable_by_class(img)
    for cls in sys.argv[2:]:
        vt = vts.get(cls); print('==', cls, hex(vt) if vt else None)
        if vt:
            for nm, recs in props(img, vt) or []:
                print('  ', nm, [(r['name'], hex(r['filt'] or 0)) for r in recs])
