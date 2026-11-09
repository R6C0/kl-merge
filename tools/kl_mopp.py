"""kl_mopp.py - read Havok 4.6 MOPP byte code (the .HVK section 2 of both games) as a tree, off-game (2026-11-09, scheduled check-in).

WHY: re/havok.md rested on an ASSUMPTION ("hkListShape child index as MOPP terminal; the code was not interpreted"), and
tools/kl_dm07plane_1109.py on a GUESS ("the list code only returns slot 256 / 248 for a query touching that slot's OLD volume").
Both are checked here: every path of a code is walked and, per terminal, the box of query positions that reaches it is kept.

OPCODES (hkMoppCommands.h of Havok 4.x; the public tables of niftools "Havok MOPP Data format" and PyNifly "MOPP Bytecode Format"
agree on the layout; the comparison rules below were FITTED to the real DM07 / DD10 files - see kl_mopp_test.py - not copied):
  00            RETURN (this path yields nothing)
  01-04 x y z   SCALE n: coordinates become (c - (x, y, z)) * 2^n (more precision for a small subtree); 169 of DM07's first 600 codes use it
  05 j / 06 jj / 07 jjj / 08 jjjj   JUMP forward by j, counted from the end of the instruction
  09 b / 0a bb  ADD b to the terminal base; 0b bbbb SET the base
  10-1c a b j   SPLIT on an axis (10 x, 11 y, 12 z, 13 y+z, 14 y-z, 15 x+z, 16 x-z, 17 x+y, 18 x-y, 19 x+y+z, 1a x+y-z, 1b x-y+z, 1c x-y-z):
                LEFT child = the next instruction when v <= a; RIGHT child at end + j when v >= b; both when a >= b (the children overlap)
  20-22 t j     SINGLE SPLIT x / y / z: v <= t left (next), v >= t right (end + j)
  23-25 a b jj jj   SPLIT with a 16-bit jump for each child (left at end + jj1, right at end + jj2)
  26-28 lo hi   CUT x / y / z: go on only when lo <= v <= hi, else RETURN
  29-2b lo(3) hi(3)   CUT with 24-bit bounds on the 24-bit coordinate of the ROOT frame (a SCALE above it changes nothing here)
  30-4f         TERMINAL base + (op - 0x30);  50 i / 51 ii / 52 iii / 53 iiii  TERMINAL base + i
COORDINATES: a query point p (Havok metres = cm / 100) gives c = (p - offset) * scale per axis, a 24-bit fixed-point number; v for a
plain axis is its high byte floor(c / 65536) (0..254); for a diagonal axis v = floor((sum of the signed high bytes + 256 per minus term)
/ number of terms) (fitted: 4260 of 4272 triangle centres reach their own terminal with it, 3029 of 6060 with the plain sum).
offset = the record's first three floats (= the shape's world box minimum - 0.01), scale = its fourth (= 254 * 65536 / (largest side
+ 0.02)); every multi-byte immediate is big-endian (the DD10 HERO plane's 24-bit x cut 0x00ba2e = 0.727 of 254 = exactly the 2 cm of
two 0.01 margins over a 6.99 m box; little-endian would be 1.28 m).
WHAT THIS GIVES: Code.terms[terminal] = the boxes (plain axes, in 8-bit units of the ROOT frame; SCALE frames are mapped back exactly)
of the paths that reach it; the diagonal constraints are kept (Box.diagonal) but NOT applied, so a box is never too small: a point
outside every box of a terminal is NEVER tested against that child / triangle by the game (a conservative reach). Code.query(p) walks
the code for one point with the exact rules (diagonals and SCALE included) and returns the terminals the game would test.
kl_mopp_test.py proves on the real files: every code walks with no unknown opcode and 100 % byte coverage; a placement's terminals
are exactly its triangles and each triangle's centre reaches its own terminal; a LIST code's terminals are child indices of its
510-block and each real child's world box lies inside its reach box - so "list terminal = child index" (re/havok.md) is PROVEN.
"""
import math
import struct

AXES = {0x10: 'x', 0x11: 'y', 0x12: 'z', 0x13: 'y+z', 0x14: 'y-z', 0x15: 'x+z', 0x16: 'x-z', 0x17: 'x+y', 0x18: 'x-y',
        0x19: 'x+y+z', 0x1a: 'x+y-z', 0x1b: 'x-y+z', 0x1c: 'x-y-z'}
SINGLE = {0x20: 'x', 0x21: 'y', 0x22: 'z'}
SPLIT16 = {0x23: 'x', 0x24: 'y', 0x25: 'z'}
CUT = {0x26: 'x', 0x27: 'y', 0x28: 'z'}
CUT24 = {0x29: 'x', 0x2a: 'y', 0x2b: 'z'}
JUMP = {0x05: 1, 0x06: 2, 0x07: 3, 0x08: 4}
REOFF = {0x09: 1, 0x0a: 2, 0x0b: 4}
TERMN = {0x50: 1, 0x51: 2, 0x52: 3, 0x53: 4}


class MoppError(ValueError):
    pass


def be(b):
    v = 0
    for x in b:
        v = (v << 8) | x
    return v


def axis_terms(axis):
    """'x-y+z' -> [(1, 0), (-1, 1), (1, 2)]"""
    out, sign = [], 1
    for ch in axis:
        if ch == '+': sign = 1
        elif ch == '-': sign = -1
        else: out.append((sign, 'xyz'.index(ch))); sign = 1
    return out


def diag_value(axis, c8):
    t = axis_terms(axis)
    return math.floor((sum(sg * c8[k] for sg, k in t) + 256 * sum(1 for sg, _ in t if sg < 0)) / float(len(t)))


class Frame:
    """The coordinate frame of a path: c_here = (c_root - o) * 2^s per axis (SCALE instructions compose). Bounds given in this frame
    are mapped back to the root frame, where all boxes live."""
    def __init__(self, o=(0.0, 0.0, 0.0), s=0):
        self.o, self.s = tuple(o), s

    def scaled(self, xyz, n):
        f = 1.0 / (1 << self.s)
        return Frame([self.o[k] + xyz[k] * f for k in range(3)], self.s + n)

    def root(self, k, v):
        return self.o[k] + v / float(1 << self.s)


class Box:
    """Half-open ranges per axis name in 8-bit units of the root frame (floats; 24-bit cuts give fractions). None = unbounded."""
    def __init__(self, d=None):
        self.d = dict(d or {})

    def cut(self, axis, lo=None, hi=None):
        b = Box(self.d)
        l, h = b.d.get(axis, (None, None))
        if lo is not None: l = lo if l is None else max(l, lo)
        if hi is not None: h = hi if h is None else min(h, hi)
        b.d[axis] = (l, h)
        return b

    def empty(self):
        """A path is dropped only when a plain axis range has lo > hi; lo == hi is kept: a zero-thickness plane (DM07 has 7 of them
        in block 0: x 1147..1147 ...) compiles to exactly that, and the game's byte compares do reach it."""
        return any(l is not None and h is not None and l > h for a, (l, h) in self.d.items() if len(a) == 1)

    def xyz(self, lo_default=0.0, hi_default=255.0):
        lo, hi = [], []
        for a in 'xyz':
            l, h = self.d.get(a, (None, None))
            lo.append(lo_default if l is None else l); hi.append(hi_default if h is None else h)
        return lo, hi

    def diagonal(self):
        return {a: r for a, r in self.d.items() if len(a) > 1}


class Code:
    """One MOPP record walked: terms = {terminal id: [Box, ...]} (one box per path that reaches it), covered = bytes visited."""
    def __init__(self, offset16, code):
        self.off = struct.unpack('<4f', offset16)
        self.code = bytes(code)
        self.terms = {}
        self.covered = bytearray(len(code))
        self.scaled = 0
        self.diag = 0
        self._walk(0, 0, Box(), Frame(), 0)

    def _mark(self, pc, n):
        if pc + n > len(self.code):
            raise MoppError('instruction at %#x runs past the code end (%d bytes)' % (pc, len(self.code)))
        for i in range(pc, pc + n):
            self.covered[i] = 1

    def _bound(self, fr, axis, v):
        """a bound in the path's frame -> root frame (plain axes exactly; a diagonal keeps its own value: not applied to boxes)"""
        return fr.root('xyz'.index(axis), v) if len(axis) == 1 else v

    def _walk(self, pc, base, box, fr, depth):
        c = self.code
        while True:
            if depth > 4096:
                raise MoppError('path deeper than 4096 at %#x' % pc)
            if pc >= len(c):
                raise MoppError('fell off the code end at %#x' % pc)
            op = c[pc]
            if op == 0x00:
                self._mark(pc, 1); return
            if 0x01 <= op <= 0x04:
                self._mark(pc, 4); self.scaled += 1; fr = fr.scaled(c[pc + 1:pc + 4], op); pc += 4; continue
            if op in JUMP:
                n = JUMP[op]; self._mark(pc, 1 + n); pc = pc + 1 + n + be(c[pc + 1:pc + 1 + n]); continue
            if op in REOFF:
                n = REOFF[op]; self._mark(pc, 1 + n); v = be(c[pc + 1:pc + 1 + n])
                base = v if op == 0x0b else base + v; pc += 1 + n; continue
            if op in AXES or op in SINGLE or op in SPLIT16:
                self._mark(pc, 4 if op in AXES else 3 if op in SINGLE else 7)
                if op in AXES: ax, a, b, jl, jr, ln = AXES[op], c[pc + 1], c[pc + 2], 0, c[pc + 3], 4
                elif op in SINGLE: ax, a, b, jl, jr, ln = SINGLE[op], c[pc + 1], c[pc + 1], 0, c[pc + 2], 3
                else: ax, a, b, jl, jr, ln = SPLIT16[op], c[pc + 1], c[pc + 2], be(c[pc + 3:pc + 5]), be(c[pc + 5:pc + 7]), 7
                if len(ax) > 1: self.diag += 1
                left, right = box.cut(ax, hi=self._bound(fr, ax, a + 1.0)), box.cut(ax, lo=self._bound(fr, ax, float(b)))
                if not left.empty(): self._walk(pc + ln + jl, base, left, fr, depth + 1)
                if right.empty(): return
                pc, box = pc + ln + jr, right; continue
            if op in CUT:
                self._mark(pc, 3); ax = CUT[op]
                box = box.cut(ax, lo=self._bound(fr, ax, float(c[pc + 1])), hi=self._bound(fr, ax, c[pc + 2] + 1.0))
                if box.empty(): return
                pc += 3; continue
            if op in CUT24:
                self._mark(pc, 7); ax = CUT24[op]
                box = box.cut(ax, lo=be(c[pc + 1:pc + 4]) / 65536.0, hi=(be(c[pc + 4:pc + 7]) + 1) / 65536.0)   # ROOT frame: a SCALE does not touch the 24-bit compare (fitted: DM07 block 0 child 108)
                if box.empty(): return
                pc += 7; continue
            if 0x30 <= op <= 0x4f:
                self._mark(pc, 1); self.terms.setdefault(base + op - 0x30, []).append(box); return
            if op in TERMN:
                n = TERMN[op]; self._mark(pc, 1 + n); self.terms.setdefault(base + be(c[pc + 1:pc + 1 + n]), []).append(box); return
            raise MoppError('unknown opcode %#04x at %#x' % (op, pc))

    def coverage(self):
        return sum(self.covered) / float(len(self.code) or 1)

    # ---- coordinates
    def to_scaled(self, p):
        """metres (Havok space) -> 8-bit units of the root frame (floats, 24-bit precision)"""
        return [(p[i] - self.off[i]) * self.off[3] / 65536.0 for i in range(3)]

    def to_world(self, c):
        return [self.off[i] + c[i] * 65536.0 / self.off[3] for i in range(3)]

    def reach(self, term):
        """(lo, hi) in metres: the union box of every path box of a terminal (plain axes). A point outside it never reaches the terminal."""
        bs = self.terms.get(term)
        if not bs:
            return None
        lo, hi = [1e30] * 3, [-1e30] * 3
        for b in bs:
            l, h = b.xyz()
            for i in range(3):
                lo[i], hi[i] = min(lo[i], l[i]), max(hi[i], h[i])
        return self.to_world(lo), self.to_world(hi)

    def query(self, p):
        """the terminals the game tests for the point p (metres): an exact walk with the fitted rules (SCALE and diagonals included)"""
        c = self.code; out = set(); root = self.to_scaled(p); stack = [(0, 0, list(root))]
        while stack:
            pc, base, cf = stack.pop()
            while True:
                op = c[pc]; c8 = [math.floor(v) for v in cf]
                if op == 0x00: break
                if 0x01 <= op <= 0x04:
                    cf = [(cf[k] - c[pc + 1 + k]) * (1 << op) for k in range(3)]; pc += 4; continue
                if op in JUMP:
                    n = JUMP[op]; pc = pc + 1 + n + be(c[pc + 1:pc + 1 + n]); continue
                if op in REOFF:
                    n = REOFF[op]; v = be(c[pc + 1:pc + 1 + n]); base = v if op == 0x0b else base + v; pc += 1 + n; continue
                if op in AXES or op in SINGLE or op in SPLIT16:
                    if op in AXES: ax, a, b, jl, jr, ln = AXES[op], c[pc + 1], c[pc + 2], 0, c[pc + 3], 4
                    elif op in SINGLE: ax, a, b, jl, jr, ln = SINGLE[op], c[pc + 1], c[pc + 1], 0, c[pc + 2], 3
                    else: ax, a, b, jl, jr, ln = SPLIT16[op], c[pc + 1], c[pc + 2], be(c[pc + 3:pc + 5]), be(c[pc + 5:pc + 7]), 7
                    v = c8['xyz'.index(ax)] if len(ax) == 1 else diag_value(ax, c8)
                    if v >= b: stack.append((pc + ln + jr, base, list(cf)))
                    if v <= a: pc += ln + jl; continue
                    break
                if op in CUT:
                    v = c8['xyz'.index(CUT[op])]
                    if c[pc + 1] <= v <= c[pc + 2]: pc += 3; continue
                    break
                if op in CUT24:
                    v = math.floor(root['xyz'.index(CUT24[op])] * 65536.0)          # the 24-bit cut reads the ROOT coordinate (see _walk)
                    if be(c[pc + 1:pc + 4]) <= v <= be(c[pc + 4:pc + 7]): pc += 7; continue
                    break
                if 0x30 <= op <= 0x4f: out.add(base + op - 0x30); break
                if op in TERMN:
                    n = TERMN[op]; out.add(base + be(c[pc + 1:pc + 1 + n])); break
                raise MoppError('unknown opcode %#04x at %#x' % (op, pc))
        return sorted(out)


def placement_box(inst, shape, pad=0.0):
    """world box (metres) of a placement from the shape's vertices (as kl_dm02fix_1108.mopp_offset reads it)"""
    f = struct.unpack_from('<12f', inst)
    p, R = f[:3], [f[3:6], f[6:9], f[9:12]]
    lo, hi = [1e30] * 3, [-1e30] * 3
    for j in range(len(shape.verts) // shape.vstride):
        v = struct.unpack_from('<3f', shape.verts, j * shape.vstride)
        for i in range(3):
            w = p[i] + sum(R[i][t] * v[t] for t in range(3))
            lo[i], hi[i] = min(lo[i], w - pad), max(hi[i], w + pad)
    return lo, hi


def triangle_boxes(inst, shape):
    """world box (metres) per triangle of a mesh placement, in index order (= the terminal numbers of its own code)"""
    f = struct.unpack_from('<12f', inst)
    p, R = f[:3], [f[3:6], f[6:9], f[9:12]]
    verts = [struct.unpack_from('<3f', shape.verts, j * shape.vstride) for j in range(len(shape.verts) // shape.vstride)]
    world = [[p[i] + sum(R[i][t] * v[t] for t in range(3)) for i in range(3)] for v in verts]
    idx = struct.unpack_from('<%dH' % (len(shape.idx) // 2), shape.idx)
    out = []
    for k in range(0, len(idx) - 2, 3):
        tri = [world[idx[k]], world[idx[k + 1]], world[idx[k + 2]]]
        out.append(([min(v[i] for v in tri) for i in range(3)], [max(v[i] for v in tri) for i in range(3)]))
    return out


def inside(inner, outer, slack=0.0):
    (il, ih), (ol, oh) = inner, outer
    return all(ol[i] - slack <= il[i] and ih[i] <= oh[i] + slack for i in range(3))


def statics(h):
    """[(shape index, placement index)] in static (file) order = the list children in order, 510 a block"""
    import kl_hvk
    return [(si, i) for si, s in enumerate(h.shapes) if s.type == kl_hvk.STATIC for i in range(len(s.inst))]


def list_reach(h, child):
    """(block, Code, reach box in metres or None) of static child number `child` (0-based, file order) in its 510-block list code"""
    import kl_hvk
    block, k = divmod(child, kl_hvk.CHUNK)
    code = Code(*h.lists[block])
    return block, code, code.reach(k)


def fmt_cm(lo, hi):
    return 'x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f' % (lo[0] * 100, hi[0] * 100, lo[1] * 100, hi[1] * 100, lo[2] * 100, hi[2] * 100)


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kl_hvk
    if len(sys.argv) < 2:
        print('usage: kl_mopp.py <file.HVK> [static child numbers...]   (walks every code; prints the reach box of the children)'); sys.exit(2)
    h = kl_hvk.Hvk(open(sys.argv[1], 'rb').read())
    st = statics(h)
    bad = sum(1 for si, i in st if Code(*h.shapes[si].mopp[i]).coverage() < 1.0)
    print('%s: %d static placements, %d list codes; placement codes with < 100%% coverage: %d' % (sys.argv[1], len(st), len(h.lists), bad))
    for b, (off, code) in enumerate(h.lists):
        c = Code(off, code)
        n = min(kl_hvk.CHUNK, len(st) - b * kl_hvk.CHUNK)
        print('  list %d: %d bytes, coverage %.3f, %d terminals, all in 0..%d: %s, diagonal splits %d, SCALE %d' % (
            b, len(code), c.coverage(), len(c.terms), n - 1, 'yes' if all(0 <= t < n for t in c.terms) else 'NO', c.diag, c.scaled))
    for a in sys.argv[2:]:
        child = int(a); si, i = st[child]
        block, code, r = list_reach(h, child)
        own = placement_box(h.shapes[si].inst[i], h.shapes[si])
        print('child %d (shape %d placement %d REF %d) block %d: %s | own box %s' % (
            child, si, i, kl_hvk.ref(h.shapes[si].inst[i]), block, 'reach ' + fmt_cm(*r) if r else 'NO list terminal (never tested)', fmt_cm(*own)))
