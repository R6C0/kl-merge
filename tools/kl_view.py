#!/usr/bin/env python3
"""
A look at skinned character models without the game: a small software renderer (pure Python, no modules to
install) that draws mesh objects of a .prm as TEXTURED triangles into a PNG.

    python kl_view.py wardrobe <build folder> <out.png>   the sixteen characters of a `kl_chars.py wardrobe` build:
                                                          face, a borrowed mask, the heaviest armour; front and
                                                          back, in a TEST POSE (head turned 40 degrees, arms
                                                          lowered 50) so that a wrong bone shows
    python kl_view.py heroes <level> <out.png>            the eight stock heisters of a Dog Days level, variants 1 / 2
    python kl_view.py masks <build folder> <out.png>      the eight masks, close, front and side (on J.C.'s body)
    python kl_view.py outfits <build folder> <out.png> [character 9..16 ...]
                                                          every Dead Men outfit: per character the four armour
                                                          levels, the two shirts and the three heads
    python kl_view.py look <build folder> <out.png> <character 1..16> <variant> [...]     any looks, front and back

Colour = the material's diffuse texture (.MAT stage mapDiffuse -> .TEX; DXT1 / DXT3 / DXT5, a small mip) at the
vertex's texture coordinate, lit flat. --plain: colour by material kind as before (mask red, bag green). The pose
is linear blend skinning from the file's own data: vertex +0 position, +12 three weights (the fourth is the rest),
+24 four palette bytes (3 * index into the object's bone runs), +36 two floats = texture coordinate, rest positions
from skeleton slot 2 - so a picture also proves the bone runs kl_chars rewrites when an object moves to another
skeleton. What it cannot show: what the game draws (no normal map, no specular, no alpha: hair cards and
glasses come out as solid sheets).
"""
import struct, zlib, math, sys, os, json


def png(path, w, h, rgb):
    raw = b''.join(b'\0' + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))
    def ch(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))

def mesh(p, o):
    """(positions [(x,y,z)], triangles [(a,b,c)]) of a mesh object."""
    d = p.u32(p.u32(o, 0x28), 0); nv = p.u32(d, 0); v = p.chunks[p.u32(d, 4)]
    stride = 52
    pos = [struct.unpack_from('<3f', v, stride * k) for k in range(nv)]
    ix = p.chunks[p.u32(d, 0x18)]; n = struct.unpack_from('<H', ix, 2)[0]
    ii = struct.unpack_from('<%dH' % n, ix, 4)
    return pos, [(ii[k], ii[k + 1], ii[k + 2]) for k in range(0, n - 2, 3)]


# ------------------------------------------------------------------ textures
def _565(c):
    return ((c >> 11) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31)

def decode(entry, want=128):
    """A texture record (kl_tex docstring) -> (w, h, bytearray rgb) of the first mip not wider than `want`,
    or None for a format this does not read. DXT1 (8-byte blocks), DXT3 / DXT5 (the colour block is the last 8
    of 16); alpha is ignored."""
    size, f1, _f2, _id, th, tw, mips, _fl = struct.unpack_from('<I4s4sIHHII', entry, 0)
    if f1 not in (b'1TXD', b'3TXD', b'5TXD'):
        return None
    q = entry.index(b'\0', 36) + 1
    for m in range(mips):
        n = struct.unpack_from('<I', entry, q)[0]
        w, h = max(tw >> m, 1), max(th >> m, 1)
        if w <= want or m == mips - 1:
            break
        q += 4 + n
    data = entry[q + 4:q + 4 + n]
    blk, off = (8, 0) if f1 == b'1TXD' else (16, 8)
    out = bytearray(3 * w * h); o = off
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            if o + 8 > len(data):
                break
            c0, c1, bits = struct.unpack_from('<HHI', data, o); o += blk
            a, b = _565(c0), _565(c1)
            if c0 > c1 or blk == 16:
                c = (a, b, tuple((2 * x + y) // 3 for x, y in zip(a, b)), tuple((x + 2 * y) // 3 for x, y in zip(a, b)))
            else:
                c = (a, b, tuple((x + y) // 2 for x, y in zip(a, b)), (0, 0, 0))
            for k in range(16):
                y, x = by + k // 4, bx + k % 4
                if y < h and x < w:
                    out[3 * (y * w + x):3 * (y * w + x) + 3] = bytes(c[(bits >> (2 * k)) & 3])
    return w, h, out


class Textures:
    """Diffuse texture of a material slot of one level, decoded once."""
    def __init__(self, mat, tex):
        self.mat, self.tex, self.cache = mat, tex, {}
    def of(self, slot):
        if slot not in self.cache:
            import kl_texmat as T
            t = None
            for name, v in T.texture_stages(self.mat.insts[slot]):
                if name == 'mapDiffuse' and v[-1] in self.tex.tex:
                    t = decode(self.tex.tex[v[-1]].entry)
            self.cache[slot] = t
        return self.cache[slot]


class View:
    def __init__(self, w, h, box, axis='front', bg=(40, 44, 52)):
        """box = (umin, umax, vmin, vmax) in model units; front: u = x, v = y, depth z; side: u = z, v = y, depth x"""
        self.w, self.h, self.box, self.axis = w, h, box, axis
        self.rgb = bytearray(bytes(bg) * (w * h)); self.z = [-1e30] * (w * h)
    def proj(self, q):
        x, y, z = q
        if self.axis == 'front': u, v, d = x, y, -z
        elif self.axis == 'back': u, v, d = -x, y, z
        elif self.axis == 'side': u, v, d = z, y, x
        else: u, v, d = -z, y, -x
        b = self.box
        return ((u - b[0]) / (b[1] - b[0]) * self.w, (b[3] - v) / (b[3] - b[2]) * self.h, d)
    def draw(self, pos, tris, col, uv=None, tex=None):
        """col: the colour without a texture. uv + tex (decode()): the texture's colour at each pixel."""
        P = [self.proj(q) for q in pos]
        w, h, zb, rgb = self.w, self.h, self.z, self.rgb
        if tex: tw, th, tp = tex
        for a, b, c in tris:
            (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = P[a], P[b], P[c]
            mnx, mxx = max(int(min(x0, x1, x2)), 0), min(int(max(x0, x1, x2)) + 1, w - 1)
            mny, mxy = max(int(min(y0, y1, y2)), 0), min(int(max(y0, y1, y2)) + 1, h - 1)
            if mnx > mxx or mny > mxy: continue
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-9: continue
            # flat shade from the model-space normal
            A, B, C = pos[a], pos[b], pos[c]
            ux, uy, uz = B[0] - A[0], B[1] - A[1], B[2] - A[2]; vx, vy, vz = C[0] - A[0], C[1] - A[1], C[2] - A[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
            # light: mostly along the view direction, a bit from above
            if self.axis == 'front': f = -nz
            elif self.axis == 'back': f = nz
            elif self.axis == 'side': f = nx
            else: f = -nx
            s = 0.35 + 0.55 * abs(f) / ln + 0.10 * (ny / ln)
            if tex:
                s *= 1.5                                    # the diffuse maps are dark
                (ua, va), (ub, vb), (uc, vc) = uv[a], uv[b], uv[c]
            else:
                cr, cg, cb = (max(0, min(255, int(k * s))) for k in col)
            for py in range(mny, mxy + 1):
                yy = py + 0.5
                for px in range(mnx, mxx + 1):
                    xx = px + 0.5
                    l0 = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / den
                    l1 = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / den
                    l2 = 1 - l0 - l1
                    if l0 < 0 or l1 < 0 or l2 < 0: continue
                    zz = l0 * z0 + l1 * z1 + l2 * z2
                    k = py * w + px
                    if zz > zb[k]:
                        if tex:
                            tu, tv = l0 * ua + l1 * ub + l2 * uc, l0 * va + l1 * vb + l2 * vc
                            t = 3 * (int((tv % 1.0) * th) % th * tw + int((tu % 1.0) * tw) % tw)
                            cr, cg, cb = min(255, int(tp[t] * s)), min(255, int(tp[t + 1] * s)), min(255, int(tp[t + 2] * s))
                        zb[k] = zz; rgb[3 * k] = cr; rgb[3 * k + 1] = cg; rgb[3 * k + 2] = cb

PALETTE = [(200, 170, 150), (120, 140, 200), (210, 90, 80), (110, 190, 120), (220, 200, 90), (170, 110, 200), (90, 200, 210), (230, 150, 70), (160, 160, 160), (240, 240, 240)]

def sheet(path, panels, w=220, h=300, cols=None):
    """panels: [(axis, box, [(pos, tris, col[, uv, tex])])] -> one PNG, panels side by side (rows of `cols`)."""
    cols = cols or len(panels); rows = (len(panels) + cols - 1) // cols
    W, H = w * cols, h * rows; out = bytearray(W * H * 3)
    for n, (axis, box, items) in enumerate(panels):
        v = View(w, h, box, axis)
        for it in items: v.draw(*it)
        ox, oy = (n % cols) * w, (n // cols) * h
        for y in range(h):
            out[((oy + y) * W + ox) * 3:((oy + y) * W + ox + w) * 3] = v.rgb[y * w * 3:(y + 1) * w * 3]
    png(path, W, H, out)


# ------------------------------------------------------------------ posed characters
def _rot(v, axis, deg, c):
    t = math.radians(deg); s, k = math.sin(t), math.cos(t)
    x, y, z = v[0] - c[0], v[1] - c[1], v[2] - c[2]
    if axis == 'y': x, z = k * x + s * z, -s * x + k * z
    elif axis == 'z': x, y = k * x - s * y, s * x + k * y
    else: y, z = k * y - s * z, s * y + k * z
    return (x + c[0], y + c[1], z + c[2])


def posed(p, mat, root, variant, turn, lod=1, textures=None):
    """[(positions, triangles, colour, uv, texture)] of one look. turn: {bone name: (axis, degrees)}, applied to
    the bone and everything below it, about the bone's rest position. textures: a Textures, or None for plain."""
    import kl_chars as C
    sk = C.skeleton(p, root); names = C.bone_names(p, sk); par = C.bone_parents(p, sk); rest = C._rest(p, sk)
    chain = []
    for b in range(len(names)):
        a, c = b, []
        while a >= 0:
            if names[a] in turn: c.append((turn[names[a]], rest[a][9:12]))
            a = par[a]
        chain.append(c)
    out = []
    for o in C.objects(p, root):
        ch = p.chunks[o]
        if ch[0x0f] != variant or ch[0x0e] != lod: continue
        nm = mat.insts[p.u16(o, 0x12)].name.split('/')[-1]
        if 'eye_Outer' in nm or 'Eyelash' in nm: continue      # alpha shells over the eyes: solid sheets here
        pal = C._palette(p, o)
        d = p.u32(p.u32(o, 0x28), 0); v = p.chunks[p.u32(d, 4)]
        pos, uv = [], []
        for k in range(p.u32(d, 0)):
            q = struct.unpack_from('<3f', v, 52 * k); w = list(struct.unpack_from('<3f', v, 52 * k + 12)); w.append(1 - sum(w))
            uv.append(struct.unpack_from('<2f', v, 52 * k + 36))
            acc = [0.0, 0.0, 0.0]
            for j in range(4):
                if w[j] > 1e-4:
                    r = q
                    for (axis, deg), cen in chain[pal[v[52 * k + 24 + j] // 3]]: r = _rot(r, axis, deg, cen)
                    acc = [acc[i] + w[j] * r[i] for i in range(3)]
            pos.append(tuple(acc))
        col = (230, 60, 60) if 'Mask' in nm else (90, 160, 90) if 'MoneyBag' in nm else (150, 150, 200) if 'Rank3' in nm else (200, 170, 150)
        out.append((pos, mesh(p, o)[1], col, uv, textures.of(p.u16(o, 0x12)) if textures else None))
    return out


POSE = {'HEAD': ('y', 40), 'RIGHT_UPPER_ARM': ('z', 50), 'LEFT_UPPER_ARM': ('z', -50)}
REST = {}
UPPER = (-60, 60, 90, 185)
HEADBOX = (-22, 22, 148, 186)
BODY = (-70, 70, 60, 190)

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kl_chars as C, kl_prmgraph as G, kl_texmat as T
    plain = '--plain' in sys.argv
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) >= 3 and a[0] in ('wardrobe', 'heroes', 'masks', 'outfits', 'look'):
        lv = C.Lv(a[1]); p = G.read(lv['.prm'], 'dd'); mat = T.read_mat(lv['.MAT'])
        tx = None if plain else Textures(mat, T.read_tex(lv['.TEX']))
        rep = json.load(open(os.path.join(a[1], 'chars.json'))) if a[0] != 'heroes' else None
        if a[0] == 'wardrobe':
            looks = []
            for i, c in enumerate(rep['characters']):
                looks += [(c['root'], C.variant_of(0, 0)), (c['root'], C.variant_of(0, 1 + (i + 3) % 8))]
                if c['outfits'] > 1: looks.append((c['root'], C.variant_of(3, -1)))
            panels = [(axis, UPPER, posed(p, mat, r, v, POSE, textures=tx)) for axis in ('front', 'back') for r, v in looks]
            sheet(a[2], panels, 150, 130, cols=len(looks) // 2 if len(looks) > 20 else len(looks))
            print('%s: %d looks, front and back' % (a[2], len(looks)))
        elif a[0] == 'heroes':
            sc, raw = lv.scene()
            looks = [(C.person(sc, C.find_node(sc, C.HERO % n))[0], v) for n in range(1, 9) for v in (1, 2)]
            panels = [(axis, UPPER, posed(p, mat, r, v, POSE, textures=tx)) for axis in ('front', 'back') for r, v in looks]
            sheet(a[2], panels, 150, 130, cols=len(looks))
            print('%s: %d looks, front and back' % (a[2], len(looks)))
        elif a[0] == 'masks':                            # row 1 front, row 2 from the side: mask 1..8
            r = rep['characters'][0]['root']
            panels = [(axis, HEADBOX if axis == 'front' else (-22, 22, 148, 186), posed(p, mat, r, C.variant_of(0, m), REST, textures=tx))
                      for axis in ('front', 'side') for m in range(1, 9)]
            sheet(a[2], panels, 220, 190, cols=8)
            print('%s: masks 1..8 (of %s), front and side' % (a[2], ', '.join(C.DD_NAMES)))
        elif a[0] == 'outfits':                          # per character one row: armour 0..3, shirt 1, heads 1 and 2; then the backs
            who = [int(x) for x in a[3:]] or [i + 1 for i, c in enumerate(rep['characters']) if c['outfits'] > 1]
            cols = [0, 1, 2, 3, 4, 7, 8, 16, 11, 19]
            panels = []
            for n in who:
                c = rep['characters'][n - 1]
                panels += [('front', BODY, posed(p, mat, c['root'], C.variant_of(o, 0), REST, textures=tx)) for o in cols]
            sheet(a[2], panels, 150, 140, cols=len(cols))
            print('%s: rows = %s; columns = outfits %s (%s)' % (a[2], ', '.join(rep['characters'][n - 1]['name'] for n in who), cols, ' | '.join(C.outfit_name(o) for o in cols)))
        else:
            c = rep['characters'][int(a[3]) - 1]
            vs = [int(x) for x in a[4:]]
            panels = [(axis, BODY, posed(p, mat, c['root'], v, POSE, textures=tx)) for axis in ('front', 'back') for v in vs]
            sheet(a[2], panels, 260, 240, cols=len(vs))
            print('%s: %s variants %s, front and back' % (a[2], c['name'], vs))
    else:
        print(__doc__); sys.exit(1)
