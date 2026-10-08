"""
32-bit Windows executable read by virtual address: sections, C strings, the export table and
the Visual C++ run-time type information (RTTI) that both Kane & Lynch executables keep.

After HHCHunter's hbm-editor (packages/formats/src/pe/PeImage.ts and msvcRtti.ts), which reads
Hitman: Blood Money's executable the same way.

RTTI: the dword just before a vtable points at a CompleteObjectLocator
  +0x00 signature (0)   +0x04 offset of this vtable in the object   +0x08 constructor displacement
  +0x0C TypeDescriptor*  +0x10 ClassHierarchyDescriptor*
A TypeDescriptor is { type_info vftable, spare, ".?AV<name>@@" }. A ClassHierarchyDescriptor has
the base count at +0x08 and at +0x0C an array of BaseClassDescriptor*, each starting with a
TypeDescriptor*, the class itself first. The complete-object ("primary") vtable of a class is the
one whose locator has offset 0 and displacement 0.
"""
import array, collections, re, struct

Rtti = collections.namedtuple('Rtti', 'by_name by_vtable bases')


class Exe:
    def __init__(self, path):
        self.path = path
        self.d = d = open(path, 'rb').read()
        if d[:2] != b'MZ':
            raise ValueError('not a Windows executable: ' + path)
        pe = struct.unpack_from('<I', d, 0x3c)[0]
        if d[pe:pe + 4] != b'PE\0\0' or struct.unpack_from('<H', d, pe + 24)[0] != 0x10b:
            raise ValueError('not a 32-bit Windows executable: ' + path)
        self.timestamp = struct.unpack_from('<I', d, pe + 8)[0]
        nsec = struct.unpack_from('<H', d, pe + 6)[0]
        optsz = struct.unpack_from('<H', d, pe + 20)[0]
        self._opt = pe + 24
        self.base = struct.unpack_from('<I', d, self._opt + 28)[0]
        self.sections = {}                       # name -> (va, virtual size, file offset, file size)
        self._map = []
        for i in range(nsec):
            o = self._opt + optsz + 40 * i
            name = d[o:o + 8].rstrip(b'\0').decode('latin1')
            vsz, rva, rsz, rptr = struct.unpack_from('<IIII', d, o + 8)
            self.sections[name] = (self.base + rva, vsz, rptr, rsz)
            self._map.append((self.base + rva, max(vsz, rsz), rptr, rsz))

    def off(self, va):
        """File offset of a virtual address, or None where no file bytes back it (.bss)."""
        for lo, span, rptr, rsz in self._map:
            into = va - lo
            if 0 <= into < span:
                return rptr + into if into < rsz else None
        return None

    def u32(self, va):
        o = self.off(va)
        return None if o is None or o + 4 > len(self.d) else struct.unpack_from('<I', self.d, o)[0]

    def read(self, va, n):
        o = self.off(va)
        return None if o is None else self.d[o:o + n]

    def cstr(self, va, maxlen=256):
        """Printable NUL-terminated string at va, or None."""
        o = self.off(va) if va else None
        if o is None:
            return None
        e = self.d.find(b'\0', o, o + maxlen + 1)
        if e <= o:
            return None
        s = self.d[o:e]
        return s.decode('latin1') if all(32 <= c < 127 for c in s) else None

    def va_of(self, file_offset):
        for lo, _span, rptr, rsz in self._map:
            if rptr <= file_offset < rptr + rsz:
                return lo + file_offset - rptr
        return None

    def code(self):
        """(.text bytes, virtual address of its first byte)."""
        va, vsz, rptr, rsz = self.sections['.text']
        return self.d[rptr:rptr + min(vsz, rsz)], va

    def exports(self):
        """Exported name -> virtual address."""
        rva = struct.unpack_from('<I', self.d, self._opt + 96)[0]
        e = self.off(self.base + rva) if rva else None
        if e is None:
            return {}
        nnames, afun, anam, aord = struct.unpack_from('<IIII', self.d, e + 24)
        fo, no, oo = (self.off(self.base + a) for a in (afun, anam, aord))
        out = {}
        for i in range(nnames):
            name = self.cstr(self.base + struct.unpack_from('<I', self.d, no + 4 * i)[0], 512)
            ordinal = struct.unpack_from('<H', self.d, oo + 2 * i)[0]
            out[name] = self.base + struct.unpack_from('<I', self.d, fo + 4 * ordinal)[0]
        return out

    def rtti(self):
        """Primary vtables of every polymorphic class, with each class's base list."""
        rlo, rvsz, rptr, rrsz = self.sections['.rdata']
        rhi = rlo + min(rvsz, rrsz)
        dlo, dvsz, _p, drsz = self.sections['.data']
        dhi = dlo + max(dvsz, drsz)
        words = array.array('I')
        words.frombytes(self.d[rptr:rptr + ((rhi - rlo) & ~3)])
        u32 = self.u32

        def type_name(descriptor):
            return demangle(self.cstr(descriptor + 8)) if descriptor else None

        cands, votes = [], collections.Counter()
        for i, loc in enumerate(words):
            if not rlo <= loc < rhi - 20:
                continue
            k = (loc - rlo) >> 2
            if (loc - rlo) & 3 or words[k] or words[k + 1] or words[k + 2]:
                continue
            descriptor = words[k + 3]
            if not (dlo <= descriptor < dhi or rlo <= descriptor < rhi):
                continue
            name, vft = type_name(descriptor), u32(descriptor)
            if name and vft is not None:
                cands.append((rlo + 4 * i + 4, vft, name, words[k + 4]))
                votes[vft] += 1
        by_name, by_vtable, bases = {}, {}, {}
        if not votes:
            return Rtti(by_name, by_vtable, bases)
        # every TypeDescriptor shares type_info's vftable: the commonest value filters stray matches
        type_info = votes.most_common(1)[0][0]
        for vtable, vft, name, hierarchy in cands:
            if vft != type_info or name in by_name:
                continue
            by_name[name] = vtable
            by_vtable[vtable] = name
            chain = []
            count, arr = u32(hierarchy + 8), u32(hierarchy + 12)
            if count is not None and arr is not None and count < 64:
                for j in range(count):
                    base = u32(arr + 4 * j)
                    base_name = type_name(u32(base)) if base else None
                    if base_name:
                        chain.append(base_name)
            bases[name] = chain or [name]
        return Rtti(by_name, by_vtable, bases)


def demangle(mangled):
    """'.?AVcNode@RTP@@' -> 'RTP::cNode'; None for templates and anything unexpected."""
    m = re.match(r'^\.\?A[VU](.+)@@$', mangled or '')
    if not m or '?' in m.group(1):
        return None
    return '::'.join(reversed(m.group(1).split('@')))
