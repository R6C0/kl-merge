"""
.HVK physics file, same layout in Dead Men and Dog Days (re/havok.md; reader kl2 0x495070 /
0x593840 / 0x5dd590). Section 1: shape records, each with its placements (transform + REF id of
the entity) and sub-parts. Section 2: one MOPP code per static placement in file order, then
one per 510 static placements. Both games link Havok 4.6.1, so codes are interchangeable.
"""
import struct

CHUNK = 510          # children per static list shape (kl2 0x620760: cmp edx, 0x1fe)
STATIC, RIGID, VEHICLE, KEYFRAMED, WEAPON = 1, 2, 3, 4, 5


class Shape:
    """One shape record. inst = [0x38-byte placement: position x3, rotation 3x3, REF id, flag],
    sub = [(surface index, collision flags, primitive count)], mopp = one (offset, code) per
    placement of a STATIC shape, else []."""
    def clone(self, inst, mopp):
        s = Shape(); s.__dict__.update(self.__dict__); s.inst, s.mopp = list(inst), list(mopp)
        return s


class Hvk:
    def __init__(self, d):
        n, size = struct.unpack_from('<II', d, 0)
        self.box = struct.unpack_from('<6f', d, 8)
        self.shapes, p = [], 0x20
        for _ in range(n):
            s = Shape()
            s.type, ni, ns, s.flags, s.convex = struct.unpack_from('<5I', d, p); p += 20
            if s.convex:
                nv, s.vstride, npl = struct.unpack_from('<3I', d, p); p += 12
            else:
                nv, nidx, s.vstride, s.istride = struct.unpack_from('<4I', d, p); p += 16
            s.verts = d[p:p + (s.vstride >> 2) * nv * 4]; p += len(s.verts)
            if s.convex:
                s.planes = d[p:p + 16 * npl]; p += 16 * npl
            else:
                s.idx = d[p:p + 2 * nidx]; p += 2 * nidx
            s.inst = [d[p + 0x38 * i:p + 0x38 * i + 0x38] for i in range(ni)]; p += 0x38 * ni
            s.sub = [struct.unpack_from('<3I', d, p + 12 * i) for i in range(ns)]; p += 12 * ns
            s.mopp = []
            self.shapes.append(s)
        if p != size:
            raise ValueError('shape section ends at %#x, header says %#x' % (p, size))
        codes = []
        while p + 20 <= len(d) and d[p:p + 20] != bytes(20):
            k = struct.unpack_from('<I', d, p + 16)[0]
            codes.append((d[p:p + 16], d[p + 20:p + 20 + k]))
            p = (p + 20 + k + 15) & ~15
        self.tail = d[p:]
        static = [s for s in self.shapes if s.type == STATIC]
        n1 = sum(len(s.inst) for s in static)
        if len(codes) != n1 + -(-n1 // CHUNK):
            raise ValueError('%d MOPP codes for %d static placements' % (len(codes), n1))
        it = iter(codes)
        for s in static:
            s.mopp = [next(it) for _ in s.inst]
        self.lists = list(it)               # one per CHUNK static placements, in file order

    def serialize(self):
        out = bytearray(0x20)
        for s in self.shapes:
            out += struct.pack('<5I', s.type, len(s.inst), len(s.sub), s.flags, s.convex)
            nv = len(s.verts) // s.vstride
            if s.convex:
                out += struct.pack('<3I', nv, s.vstride, len(s.planes) // 16) + s.verts + s.planes
            else:
                out += struct.pack('<4I', nv, len(s.idx) // 2, s.vstride, s.istride) + s.verts + s.idx
            out += b''.join(s.inst)
            for x in s.sub:
                out += struct.pack('<3I', *x)
        struct.pack_into('<II6f', out, 0, len(self.shapes), len(out), *self.box)
        for off, code in [m for s in self.shapes for m in s.mopp] + self.lists:
            out += off + struct.pack('<I', len(code)) + code
            out += b'\xcd' * (-len(out) & 15)
        return bytes(out + self.tail)

    def static_count(self):
        return sum(len(s.inst) for s in self.shapes if s.type == STATIC)


def ref(inst):
    return struct.unpack_from('<I', inst, 0x30)[0]


def renumber(inst, refs):
    return inst[:0x30] + struct.pack('<I', refs[ref(inst)]) + inst[0x34:]


def remap(hvk, refs, filler=None):
    """Shapes of `hvk` with REF ids renumbered through `refs` (old -> new); a placement whose
    REF id is missing is dropped. With `filler` (a map: a (shape, placement, code) of a kept static
    placement) a dropped STATIC placement is replaced by it instead, because the list codes address
    static placements by position: the list code never returns the filler where it now lies."""
    out = []
    for s in hvk.shapes:
        keep = [k for k, i in enumerate(s.inst) if ref(i) in refs]
        if s.type != STATIC or filler is None:
            if keep:
                out.append(s.clone([renumber(s.inst[k], refs) for k in keep],
                                   [s.mopp[k] for k in keep] if s.mopp else []))
        elif len(keep) == len(s.inst):
            out.append(s.clone([renumber(i, refs) for i in s.inst], s.mopp))
        else:
            for k, i in enumerate(s.inst):          # one record per placement keeps the order
                if k in keep:
                    out.append(s.clone([renumber(i, refs)], [s.mopp[k]]))
                else:
                    out.append(filler[0].clone([filler[1]], [filler[2]]))
    return out


def first_static(shapes, refs=None):
    for s in shapes:
        if s.type == STATIC:
            for i, m in zip(s.inst, s.mopp):
                if refs is None or ref(i) in refs:
                    return s, (renumber(i, refs) if refs else i), m


def join(maps, systems, box=None):
    """maps: [(Hvk, refs)], systems: (Hvk, refs) or None; refs = {old REF id: new REF id} of the
    entities that survive. Every map keeps its static placements in file order and its own list
    codes; each part but the last is padded to a multiple of CHUNK static placements with copies of
    one of its own, which no list code refers to.
    The systems level's own systems never own static collision (re/havok.md), but a graft that
    keeps part of its MAP layer may (F07's escape vehicles: 2 static placements each). Then its
    whole static part is carried as one more part behind the maps: every static placement keeps
    its position (a dropped one is replaced by a copy of a kept one, as in remap) and its list
    codes are appended. ASSUMPTION as for two maps: a list code addresses the placements of its
    own 510 only, by position."""
    out = Hvk.__new__(Hvk); out.shapes, out.lists, out.tail = [], [], maps[0][0].tail
    parts = [(h, refs, first_static(h.shapes, refs)) for h, refs in maps]
    extra = []
    if systems:
        fill = first_static(systems[0].shapes, systems[1])
        if fill:
            parts.append((systems[0], systems[1], fill))
        else:
            extra = remap(*systems)                 # no filler: its static placements all go
    for n, (h, refs, fill) in enumerate(parts):
        out.shapes += remap(h, refs, fill)
        pad = -h.static_count() % CHUNK if n < len(parts) - 1 else 0
        if pad:
            out.shapes.append(fill[0].clone([fill[1]] * pad, [fill[2]] * pad))
        out.lists += h.lists
    out.shapes += extra
    lo = [min(h.box[k] for h, _ in maps) for k in range(3)]
    hi = [max(h.box[k] for h, _ in maps) for k in range(3, 6)]
    out.box = tuple(box or lo + hi)
    return out


def tops(names, decls):
    stack, out, pending = [], [], None
    for name, d in zip(names, decls):
        del stack[len(stack) - (d >> 25):]
        if pending is not None:
            stack.append(pending); pending = None
        out.append(stack[0] if stack else name)
        if d & 0x1000000:
            pending = name
    return out
