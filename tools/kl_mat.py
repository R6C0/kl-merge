"""
Materials (.MAT) and compiled shader caches (.fxc) for Dead Men -> Dog Days.

.MAT (both games): header [classes table][entries table][0][end]; tables of u32 offsets
to records [type str, ..., props ptr, count]; properties are 16-byte records
[tag (reversed fourcc), value/ptr, count, type 0 float/1 string/2 int/3 list].
Strings are referenced by absolute file offset, so renaming = append the new string and
repoint every reference to the old one.

.fxc (Dog Days only): [u32 100][u32 count][u32 bytes after header][u32 16] then entries:
0x850-byte header (material class, permutation key, blob size, ..., blob offset at +0x80c,
source shader name at +0x810) followed by a compiled D3D9 effect (fx_2_0) blob.
"""
import hashlib, re, struct

# Dead Men shaders / material classes Dog Days doesn't have -> closest Dog Days one
REMAP = {
    'ScatterNew': 'ScatterManual', 'ScatterNew.fx': 'ScatterManual.fx',
    'GlassSurface': 'Glass', 'GlassSurface.fx': 'Glass.fx',
    'Mirror': 'Glass', 'Mirror.fx': 'Glass.fx',
}


def convert_mat(data, remap=REMAP):
    d = bytearray(data)
    changes = 0
    added = {}
    for old, new in remap.items():
        pat = re.compile(re.escape(b'\0' + old.encode() + b'\0'), re.I)
        for m in pat.finditer(bytes(data)):
            pos = m.start() + 1
            ref = struct.pack('<I', pos)
            hits = [k for k in range(0, len(data) - 3, 4) if data[k:k + 4] == ref]
            if not hits:
                continue
            if new not in added:
                added[new] = len(d)
                d += new.encode() + b'\0'
                d += b'\0' * ((-len(d)) % 4)
            for k in hits:
                struct.pack_into('<I', d, k, added[new]); changes += 1
    return bytes(d), changes


# ---------------------------------------------------------------- fxc
FXC_HDR = 0x850
FX_MAGIC = b'\x01\x09\xff\xfe'


def read_fxc(data):
    ver, count, size, hdr = struct.unpack_from('<4I', data, 0)
    o, out = 16, []
    for _ in range(count):
        bs = struct.unpack_from('<I', data, o + 8)[0]
        head = data[o:o + FXC_HDR]
        blob = data[o + FXC_HDR:o + FXC_HDR + bs]
        if blob[:4] != FX_MAGIC:
            raise ValueError('fxc entry without effect blob at %#x' % o)
        out.append((head, blob))
        o += FXC_HDR + bs
    if o != len(data):
        raise ValueError('fxc size mismatch')
    return ver, out


def entry_key(head, blob):
    h = bytearray(head)
    h[0x80c:0x810] = b'\0\0\0\0'                 # absolute offset differs per file
    return hashlib.md5(bytes(h) + blob).hexdigest()


def write_fxc(entries, ver=100):
    out = bytearray(struct.pack('<4I', ver, len(entries), 0, 16))
    for head, blob in entries:
        h = bytearray(head)
        struct.pack_into('<I', h, 0x80c, len(out) + FXC_HDR)
        out += h + blob
    struct.pack_into('<I', out, 8, len(out) - 16)
    return bytes(out)


def entry_info(head):
    kind, key, bs = struct.unpack_from('<3I', head, 0)
    cls = head[12:12 + 64].split(b'\0')[0].decode('latin1')
    shader = head[0x810:0x850].split(b'\0')[0].decode('latin1')
    return cls, key, shader


# ---------------------------------------------------------------- property record repack
# Dead Men property record: tag u32, value/ptr u32, count u32, type u32   (16 bytes)
# Dog Days property record: tag u32, value/ptr u32, count u16, type u16   (12 bytes)
# The trees are otherwise identical, so each array is rewritten in place (12n <= 16n);
# strings, float arrays and every pointer keep their offsets.

def _tables(d):
    o1, o2, _z, _o3 = struct.unpack_from('<4I', d, 0)
    roots = []
    for off in (o1, o2):
        i = 1
        while True:
            h = struct.unpack_from('<I', d, off + 4 * i)[0]
            if h == 0:
                break
            roots.append(struct.unpack_from('<I', d, h + 28)[0])     # root property (count 1)
            i += 1
    return roots


def repack_props(data):
    d = bytearray(data)
    arrays = {}
    stack = [(r, 1) for r in _tables(data)]
    while stack:
        pos, n = stack.pop()
        if pos in arrays:
            continue
        recs = [struct.unpack_from('<4I', data, pos + 16 * k) for k in range(n)]
        arrays[pos] = recs
        for tag, val, cnt, typ in recs:
            if typ > 3 or cnt > 0xffff:
                raise ValueError('unexpected material property at %#x' % pos)
            if typ == 3:
                stack.append((val, cnt))
    for pos, recs in arrays.items():
        out = b''.join(struct.pack('<IIHH', t, v, c, ty) for t, v, c, ty in recs)
        d[pos:pos + 16 * len(recs)] = out + b'\0' * (4 * len(recs))
    return bytes(d), len(arrays)


def read_tree(d, wide):
    """Parse every class/entry into nested tuples (tag, type, value) for comparisons."""
    size = 16 if wide else 12
    def props(pos, n):
        out = []
        for k in range(n):
            p = pos + size * k
            tag = d[p:p + 4]
            if wide:
                val, cnt, typ = struct.unpack_from('<3I', d, p + 4)
            else:
                val, cnt, typ = struct.unpack_from('<IHH', d, p + 4)
            if typ == 3:
                v = props(val, cnt)
            elif typ == 1:
                v = d[val:d.index(b'\0', val)]
            elif typ == 0 and cnt > 1:
                v = d[val:val + 4 * cnt]
            else:
                v = val
            out.append((tag, typ, v))
        return tuple(out)
    return [props(r, 1) for r in _tables(d)]


def convert_mat_full(data, remap=REMAP):
    renamed, changes = convert_mat(data, remap)        # string repoints (on Dead Men layout)
    packed, narrays = repack_props(renamed)
    if read_tree(packed, False) != read_tree(renamed, True):
        raise ValueError('material repack changed the tree')
    return packed, changes, narrays
