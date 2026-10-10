"""
Payday 2 asset crates: `<PAYDAY 2>\\assets\\*.crate` (Steam build 25506656, read 2026-10-09; 98 files,
34.65 GB). Everything below was measured on all 98 files (re/pd2_crates.md has the numbers).

CRATE = header + entry table + (scripts/engine only) signature table + zero fill to 1,000,000 +
data blobs (+ signature blocks at the end of scripts.crate and engine.crate):
  0x00  'YAOI'  u32 version 1  u64 n
  0x10  n x 48 bytes: u64 ext idstring, u64 path idstring, u64 offset (from file start), u64 raw
        size, u64 stored size, u64 properties.  stored == 0: the blob is raw bytes of `raw` size;
        else a zlib stream (78 0d...) of `stored` bytes that inflates to `raw`.  raw == 0 entries
        (20,260, all cooked_physics) have offset 0: an empty file, nothing to read.
        The table is sorted by (ext, path). The blobs are NOT in table order: sorted by offset,
        every blob starts at align16(previous offset + previous stored-or-raw size), the first at
        1,000,000, the padding is zero, and the last blob ends at the file end (assets) or at the
        signature blocks (scripts, engine). Walking the TABLE order instead gives 5,286 "gaps":
        that is the whole explanation of the 5,286 deviations seen earlier.
        properties: 0 for 278,441 entries; a single bit for 237. The bit names a property of
        `crates.properties` (below): 14 language bits on strings/*.strings and fonts/*_mf.merged_font
        (the same (path, ext) appears once per installed language: 167 duplicate keys), d3d11 (bit 0)
        on the 7 core/shaders/*.shaders, dds (bit 18) on 55 and dds_hcm (bit 19) on 7 `.swatch`
        textures, model (bit 8) on one `.old` file. An entry with a bit is used only when that
        property is on (ASSUMPTION for the exact semantics; the language case is plain to see).
  after the table (scripts.crate, engine.crate): u64 0, u64 m, m x 40 bytes {ext, path, u64 0,
        u64 offset, u64 size = 512}: one RSA-4096 signature block (crate_public_key.pem in
        engine.crate is a 4096-bit RSA public key) per lua script (all 1,646) and for
        settings/game_config + core/settings/security_settings. Other crates: m = 0.
IDSTRING = Bob Jenkins lookup8 hash64 (level 0) of the lower-case path / extension bytes
  (hash64('lua') is the extension of every scripts.crate entry; the 186,212-line `hashlist` names
  278,490 of the 278,511 (path, ext) keys' paths; the hashlist also holds the extension and property
  words themselves, which is how 'continents', 'swatch', 'blacklist' ... were named).
crates.shipping_manifest: u32 2, u32 2, u32 0, "assets\\0159028\\0core\\03634\\0", u64 98, then per
  crate: name\\0, u64 k, k x {u64 ext, u64 path, u64 flag}; then 16 zero bytes, u64 21 and 21 x
  {u64 property idstring, u32 bit} (the properties table again, 12-byte records). It lists every
  (ext, path) once (278,605 records; the language duplicates are not repeated). flag = 1 on 105
  records: 94 of them are in no crate table (54 textures, 19 blacklists, 19 bnk, 1 movie, 1 of an
  unnamed extension: dangling references - ASSUMPTION), 11 are build products (7 shaders,
  banksinfo, pem, game_config, compile_meta). The 159028 / 3634 counts match no count of this
  file's records or paths (tried: records, distinct paths, core/ paths, per crate kind).
crates.properties: 'YURI', u64 21, 21 x {u64 idstring, u64 bit}: italian 0x200, x360 0x40,
  polish 0x8, french 0x800, ma 0x100000, turkish 0x20, korean 0x2, ps3 0x80, dds_hcm 0x80000,
  schinese 0x10, portuguese 0x1000, d3d11 0x1, russian 0x10000, finnish 0x2000, latam 0x20000,
  german 0x400, model 0x100, japanese 0x4, spanish 0x8000, dutch 0x4000, dds 0x40000.
  (16-byte records after a 12-byte head, not 20-byte ones.)
Crate families: assets_NN_S, init_NN_S, default_NN_0 (NN = 0..15, S = 0 big blobs / 1 small ones),
  movies_NN_0, engine, scripts. The shard NN is not path-hash mod 16 nor its top nibble (measured):
  the five files of one unit sit in five different crates. Only the (path, ext) key matters.
Lua: LuaJIT 2 bytecode ('\\x1bLJ\\x02'), not source (all 1,646; every blob of scripts.crate is
  zlib + one signature). .texture = DDS ('DDS ' + 124-byte header). .model = Diesel binary (first
  dword 0x44424f44; tools/pd2_model.py). .cooked_physics = PhysX cooked mesh ('NXS\\x01MESH' after
  a 8-byte head) but 20,260 of 23,446 are EMPTY entries (raw 0) - the four crew masks' among them.
  .unit / .object / .material_config are TEXT XML (0 binary of 22,431 material_configs, 1 of the
  first 3,000 objects); .sequence_manager and the world files are binary scriptdata (xml_text()).
  606 material_configs are TWO documents: `\\n<materials ...>...</materials>\\n ELSE {\\n<materials
  ...>...</materials>\\n}` (the crew masks: first branch render_template "solid_mask:MATS_3", second
  "solid_mask"). ASSUMPTION: a preprocessor keeps one branch by a build / platform flag; the IF line
  itself is not in the blob. text_documents() splits them; xml_text() returns the first.
Names: 278,508 of 278,511 keys have a hashlist path; the three unnamed are two .unit (196, 242
  bytes) and one 1.4 MB .texture. All 77 extension hashes are named. Mask folders: 70 folders
  with files directly under units/payday2/masks/ (+ shared_textures/patterns), 578 distinct
  `*/masks/<x>/` folder names over every DLC prefix, 804 distinct parent folders with '/masks/' in
  the path (so a count of 307 matches nothing measured here). msk_dallas_glow is
  units/pd2_dlc_cop/masks/msk_dallas_glow (not under units/payday2/).
Verified 2026-10-10 (`verify`): scripts.crate 1,646 entries all zlib, engine.crate 73, assets_00_1
  5,917 (853 empty); 0 size / inflate / layout / padding faults, 0.1 + 0.1 + 0.7 s.

Usage (from the repo root; outputs go to <KL_PortTools>\\pd2\\, never into the game folders):
  python tools/pd2_crate.py index                     rebuild pd2\\index.json + names.json
  python tools/pd2_crate.py find <substring>          paths containing it (ext, raw size, crate)
  python tools/pd2_crate.py extract <path> <ext> [<out file>] [--xml]    (--xml: text beside it)
  python tools/pd2_crate.py extract-prefix <path prefix> [<out dir>] [--xml]
  python tools/pd2_crate.py masks                     pd2\\masks_list.json: every '/masks/' folder
  python tools/pd2_crate.py verify <crate name>       inflate every blob, check sizes and padding
  python tools/pd2_crate.py stats                     per-extension table
  python tools/pd2_crate.py manifest                  what the manifest and properties files hold
  python tools/pd2_crate.py xml <file> [<out>]        Diesel binary XML -> text
"""
import json
import os
import re
import struct
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_port_check

ASSETS = r'C:\Steam\steamapps\common\PAYDAY 2\assets'
WORK = os.path.join(kl_port_check.workdir(), 'pd2')
DATA_START = 1000000

# Every extension found in the 98 crates (77), all resolved by name: the first group from the
# engine's known types, the second are words that stand in the hashlist as lines of their own.
EXTENSIONS = '''lua texture model unit object material_config cooked_physics animation stream movie
bnk font gui scene strings effect sequence_manager environment shaders render_template_database
physic_effect dialog dialog_index massunit world mission continent nav_data cover_data world_cameras
world_sounds world_setting prefhud achievment credits menu network_settings animation_def
animation_state_machine animation_states animation_subset post_processor decals
atom_batcher_settings merged_font package texture_channels scenes physics_settings bnkinfo
camera_shakes light_intensities cameras banksinfo tga
continents swatch blacklist bmfc timeline controller_settings action_message objective mop_data
hint neural_net comment diesel_layers game_config render_config compile_meta matchmaking_regions
security_settings pem mb old xbox_live
xml binary generic_xml custom_xml scriptdata'''.split()
PROPERTIES = '''italian x360 polish french ma turkish korean ps3 dds_hcm schinese portuguese d3d11
russian finnish latam german model japanese spanish dutch dds english'''.split()

M64 = (1 << 64) - 1


def _mix(a, b, c):
    a = (a - b - c) & M64; a ^= c >> 43
    b = (b - c - a) & M64; b ^= (a << 9) & M64
    c = (c - a - b) & M64; c ^= b >> 8
    a = (a - b - c) & M64; a ^= c >> 38
    b = (b - c - a) & M64; b ^= (a << 23) & M64
    c = (c - a - b) & M64; c ^= b >> 5
    a = (a - b - c) & M64; a ^= c >> 35
    b = (b - c - a) & M64; b ^= (a << 49) & M64
    c = (c - a - b) & M64; c ^= b >> 11
    a = (a - b - c) & M64; a ^= c >> 12
    b = (b - c - a) & M64; b ^= (a << 18) & M64
    c = (c - a - b) & M64; c ^= b >> 22
    return a, b, c


def hash64(k, level=0):
    """Bob Jenkins lookup8 hash64 of bytes (or a str, lower-cased): Diesel's idstring."""
    if isinstance(k, str):
        k = k.lower().encode('latin-1')
    a = b = level
    c = 0x9e3779b97f4a7c13
    p, n = 0, len(k)
    while n >= 24:
        a = (a + int.from_bytes(k[p:p + 8], 'little')) & M64
        b = (b + int.from_bytes(k[p + 8:p + 16], 'little')) & M64
        c = (c + int.from_bytes(k[p + 16:p + 24], 'little')) & M64
        a, b, c = _mix(a, b, c)
        p += 24
        n -= 24
    c = (c + len(k)) & M64
    t = k[p:p + n]
    if n > 16:
        c = (c + (int.from_bytes(t[16:], 'little') << 8)) & M64
    if n > 8:
        b = (b + int.from_bytes(t[8:16], 'little')) & M64
    a = (a + int.from_bytes(t[:8], 'little')) & M64
    a, b, c = _mix(a, b, c)
    return c


EXT_HASH = {hash64(w): w for w in EXTENSIONS}
PROP_HASH = {hash64(w): w for w in PROPERTIES}


class Entry:
    __slots__ = ('crate', 'ext', 'path', 'offset', 'raw', 'stored', 'props')

    def __init__(self, crate, ext, path, offset, raw, stored, props):
        self.crate, self.ext, self.path = crate, ext, path
        self.offset, self.raw, self.stored, self.props = offset, raw, stored, props

    def key(self):
        return (self.path, self.ext)


def crate_files(assets=ASSETS):
    return sorted(f for f in os.listdir(assets) if f.endswith('.crate'))


def read_table(path):
    """[(ext, path, offset, raw, stored, props)] and the signature table [(ext, path, 0, offset, size)]."""
    with open(path, 'rb') as f:
        head = f.read(16)
        magic, ver, n = struct.unpack('<4sIQ', head)
        if magic != b'YAOI' or ver != 1:
            raise ValueError('%s: not a crate (%r %d)' % (path, magic, ver))
        tab = f.read(48 * n + 16)
        ents = [struct.unpack_from('<6Q', tab, 48 * i) for i in range(n)]
        zero, m = struct.unpack_from('<QQ', tab, 48 * n)
        sigs = []
        if m:
            st = f.read(40 * m)
            sigs = [struct.unpack_from('<5Q', st, 40 * i) for i in range(m)]
    return ents, sigs


class Index:
    """All entries of all crates. by_key[(path hash, ext hash)] = [Entry, ...] (several only for
    the per-language duplicates; props == 0 first). Cached in <WORK>\\index.json, rebuilt when a
    crate's size or mtime changed; names from the hashlist cached in names.json."""

    def __init__(self, assets=ASSETS, work=WORK, force=False, quiet=False):
        self.assets, self.work = assets, work
        self.entries = []
        self.by_key = {}
        self.sigs = {}
        self._names = None
        self.load(force, quiet)

    # -- building --------------------------------------------------------------------------------
    def _stamp(self):
        return {f: [os.path.getsize(os.path.join(self.assets, f)),
                    int(os.path.getmtime(os.path.join(self.assets, f)))] for f in crate_files(self.assets)}

    def load(self, force=False, quiet=False):
        cache = os.path.join(self.work, 'index.json')
        stamp = self._stamp()
        if not force and os.path.isfile(cache):
            try:
                with open(cache) as f:
                    d = json.load(f)
                if d.get('crates') == stamp:
                    self._from_json(d)
                    return
            except (ValueError, KeyError):
                pass
        t0 = time.time()
        self.entries, self.by_key, self.sigs = [], {}, {}
        for name in stamp:
            ents, sigs = read_table(os.path.join(self.assets, name))
            for e, p, off, raw, stored, props in ents:
                self._add(Entry(name, e, p, off, raw, stored, props))
            if sigs:
                self.sigs[name] = sigs
        os.makedirs(self.work, exist_ok=True)
        with open(cache, 'w') as f:
            json.dump(self._to_json(stamp), f)
        if not quiet:
            print('indexed %d crates, %d entries in %.1f s -> %s' % (len(stamp), len(self.entries),
                                                                      time.time() - t0, cache))

    def _add(self, ent):
        self.entries.append(ent)
        lst = self.by_key.setdefault(ent.key(), [])
        if ent.props == 0:
            lst.insert(0, ent)
        else:
            lst.append(ent)

    def _to_json(self, stamp):
        ents = {}
        for (p, e), lst in self.by_key.items():
            ents['%016x.%016x' % (p, e)] = [[x.crate, x.offset, x.raw, x.stored, x.props] for x in lst]
        return {'crates': stamp, 'entries': ents,
                'signatures': {k: [list(s) for s in v] for k, v in self.sigs.items()}}

    def _from_json(self, d):
        self.entries, self.by_key = [], {}
        for key, lst in d['entries'].items():
            p, e = (int(x, 16) for x in key.split('.'))
            for crate, off, raw, stored, props in lst:
                self._add(Entry(crate, e, p, off, raw, stored, props))
        self.sigs = {k: [tuple(s) for s in v] for k, v in d.get('signatures', {}).items()}

    # -- names -----------------------------------------------------------------------------------
    @property
    def names(self):
        """{path idstring: path} from the hashlist (cached: hashing 186k lines takes 1.3 s)."""
        if self._names is None:
            cache = os.path.join(self.work, 'names.json')
            hl = os.path.join(self.assets, 'hashlist')
            st = [os.path.getsize(hl), int(os.path.getmtime(hl))]
            d = None
            if os.path.isfile(cache):
                try:
                    with open(cache) as f:
                        d = json.load(f)
                    if d.get('hashlist') != st:
                        d = None
                except ValueError:
                    d = None
            if d is None:
                names = {}
                with open(hl, 'rb') as f:
                    for line in f.read().split(b'\n'):
                        line = line.strip()
                        if line:
                            names['%016x' % hash64(line)] = line.decode('latin-1')
                d = {'hashlist': st, 'names': names}
                os.makedirs(self.work, exist_ok=True)
                with open(cache, 'w') as f:
                    json.dump(d, f)
            self._names = {int(k, 16): v for k, v in d['names'].items()}
        return self._names

    def path_name(self, h):
        return self.names.get(h) or '%016x' % h

    def ext_name(self, h):
        return EXT_HASH.get(h) or self.names.get(h) or '%016x' % h

    def name(self, ent):
        return self.path_name(ent.path) + '.' + self.ext_name(ent.ext)

    # -- lookups ---------------------------------------------------------------------------------
    def get(self, path, ext, props=0):
        """The Entry of path.ext (names or idstrings); props picks a language variant."""
        p = path if isinstance(path, int) else hash64(path)
        e = ext if isinstance(ext, int) else hash64(ext)
        lst = self.by_key.get((p, e))
        if not lst:
            raise KeyError('%s.%s is in no crate' % (path, ext))
        for x in lst:
            if x.props == props:
                return x
        return lst[0]

    def find(self, sub):
        """Entries whose named path contains sub (case-insensitive), sorted by name."""
        sub = sub.lower()
        hits = [x for x in self.entries if sub in self.path_name(x.path).lower()]
        hits.sort(key=lambda x: (self.path_name(x.path), self.ext_name(x.ext), x.props))
        return hits

    def prefix(self, pre):
        pre = pre.lower()
        hits = [x for x in self.entries if self.path_name(x.path).lower().startswith(pre)]
        hits.sort(key=lambda x: (self.path_name(x.path), self.ext_name(x.ext), x.props))
        return hits

    # -- data ------------------------------------------------------------------------------------
    def read(self, ent):
        """The entry's bytes (inflated)."""
        if ent.raw == 0:
            return b''
        with open(os.path.join(self.assets, ent.crate), 'rb') as f:
            f.seek(ent.offset)
            d = f.read(ent.stored or ent.raw)
        if ent.stored:
            d = zlib.decompress(d)
        if len(d) != ent.raw:
            raise ValueError('%s: %d bytes, table says %d' % (self.name(ent), len(d), ent.raw))
        return d

    def out_path(self, ent, root=None):
        root = root or os.path.join(self.work, 'extract')
        p = self.name(ent)
        if ent.props:
            p += '.' + (PROP_HASH_BY_BIT.get(ent.props) or '%x' % ent.props)
        return os.path.join(root, *p.split('/'))

    def extract(self, ent, out=None, root=None, xml=False):
        """Write the entry; xml=True also writes <out>.xml (and .else.xml for an ELSE pair) for
        the XML document extensions. Returns (out path, data)."""
        out = out or self.out_path(ent, root)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        d = self.read(ent)
        with open(out, 'wb') as f:
            f.write(d)
        if xml and d and self.ext_name(ent.ext) in XML_DOC_EXTS:
            write_xml(d, out)
        return out, d

    def masks(self):
        """{folder path: [{name, ext, raw, crate}]} for every folder whose path has '/masks/'."""
        out = {}
        for x in self.entries:
            n = self.path_name(x.path)
            if '/masks/' not in n:
                continue
            folder, base = n.rsplit('/', 1)
            out.setdefault(folder, []).append({'name': base, 'ext': self.ext_name(x.ext), 'raw': x.raw,
                                               'crate': x.crate})
        for v in out.values():
            v.sort(key=lambda r: (r['name'], r['ext']))
        return dict(sorted(out.items()))

    # -- checks ----------------------------------------------------------------------------------
    def verify(self, crate):
        """Inflate every blob of one crate and check: size == raw, blobs contiguous at 16-byte
        alignment with zero padding, the last one ending at the file end or the signature blocks.
        Returns a dict of counts."""
        name = crate if crate.endswith('.crate') else crate + '.crate'
        ents = sorted((x for x in self.entries if x.crate == name), key=lambda x: x.offset)
        path = os.path.join(self.assets, name)
        size = os.path.getsize(path)
        r = {'crate': name, 'entries': len(ents), 'empty': 0, 'compressed': 0, 'stored': 0,
             'bad_size': 0, 'bad_inflate': 0, 'bad_layout': 0, 'bad_padding': 0, 'bytes': 0}
        t0 = time.time()
        with open(path, 'rb') as f:
            pos = DATA_START
            for x in ents:
                if x.raw == 0:
                    r['empty'] += 1
                    if x.offset != 0:
                        r['bad_layout'] += 1
                    continue
                if x.offset != pos:
                    r['bad_layout'] += 1
                    pos = x.offset
                f.seek(x.offset)
                d = f.read(x.stored or x.raw)
                r['bytes'] += len(d)
                if x.stored:
                    r['compressed'] += 1
                    try:
                        d = zlib.decompress(d)
                    except zlib.error:
                        r['bad_inflate'] += 1
                        d = b''
                else:
                    r['stored'] += 1
                if len(d) != x.raw:
                    r['bad_size'] += 1
                end = x.offset + (x.stored or x.raw)
                pos = (end + 15) & ~15
                pad = min(pos, size) - end            # the last blob may end at the file end
                if pad > 0 and f.read(pad) != bytes(pad):
                    r['bad_padding'] += 1
            sig = self.sigs.get(name)
            tail_start = sig[0][3] if sig else size
            r['last_end'] = pos if ents and ents[-1].raw else DATA_START
            r['ends_at_tail'] = (r['last_end'] == tail_start) or (ents and ents[-1].offset + (ents[-1].stored or ents[-1].raw) == size)
            r['signatures'] = len(sig) if sig else 0
        r['seconds'] = round(time.time() - t0, 1)
        return r

    def stats(self):
        """[(ext name, entries, raw bytes, stored bytes, crate kinds)] sorted by entries."""
        acc = {}
        for x in self.entries:
            a = acc.setdefault(x.ext, [0, 0, 0, set()])
            a[0] += 1
            a[1] += x.raw
            a[2] += x.stored or x.raw
            a[3].add(x.crate.split('_')[0].replace('.crate', ''))
        rows = [(self.ext_name(e), n, raw, st, ','.join(sorted(k))) for e, (n, raw, st, k) in acc.items()]
        rows.sort(key=lambda r: -r[1])
        return rows


PROP_HASH_BY_BIT = {}


def properties(assets=ASSETS):
    """[(name, bit)] from crates.properties ('YURI', u64 n, n x {u64 idstring, u64 bit})."""
    with open(os.path.join(assets, 'crates.properties'), 'rb') as f:
        d = f.read()
    if d[:4] != b'YURI':
        raise ValueError('crates.properties: bad magic')
    n = struct.unpack_from('<Q', d, 4)[0]
    out = []
    for i in range(n):
        h, bit = struct.unpack_from('<QQ', d, 12 + 16 * i)
        out.append((PROP_HASH.get(h, '%016x' % h), bit))
    return out


def manifest(assets=ASSETS):
    """crates.shipping_manifest -> (head strings, {crate: [(ext, path, flag)]}, [(prop, bit)])."""
    with open(os.path.join(assets, 'crates.shipping_manifest'), 'rb') as f:
        d = f.read()
    a, b, c = struct.unpack_from('<III', d, 0)
    p = 12
    strs = []
    for _ in range(4):
        e = d.index(b'\0', p)
        strs.append(d[p:e].decode())
        p = e + 1
    ncr = struct.unpack_from('<Q', d, p)[0]
    p += 8
    crates = {}
    for _ in range(ncr):
        e = d.index(b'\0', p)
        name = d[p:e].decode()
        p = e + 1
        k = struct.unpack_from('<Q', d, p)[0]
        p += 8
        crates[name] = [struct.unpack_from('<QQQ', d, p + 24 * j) for j in range(k)]
        p += 24 * k
    p += 16
    n = struct.unpack_from('<Q', d, p)[0]
    p += 8
    props = []
    for i in range(n):
        h, bit = struct.unpack_from('<QI', d, p + 12 * i)
        props.append((PROP_HASH.get(h, '%016x' % h), bit))
    p += 12 * n
    if p != len(d):
        raise ValueError('manifest: %d bytes left' % (len(d) - p))
    return (a, b, c, strs), crates, props


try:
    PROP_HASH_BY_BIT = {bit: name for name, bit in properties()}
except (OSError, ValueError):
    PROP_HASH_BY_BIT = {}


# -- Diesel binary scriptdata ("binary XML") -------------------------------------------------------
# .unit / .object / .material_config in these crates are plain text XML. .sequence_manager (and
# .mission, .continent, .world, .environment, ...) are scriptdata: a Lua table tree serialized in
# the 64-bit layout (DieselEngineFormats calls it the "Raid" variant; measured here on the
# extracted files, see xml_text's self-check in re/pd2_crates.md):
#   0x00  6 sections x 32 bytes {u64 0, u64 count, u64 capacity, u64 offset}: float (4 bytes each),
#         string (16: u64 0, u64 offset of a NUL-terminated text), vector (12), quaternion (16),
#         idstring (8), table (40: u64 meta = string index or -1, u64 count, u64 capacity,
#         u64 items offset, u64 0)
#   0xc0  u64 0, u32 root item, u32 0 -> data starts at 0xd0
#   items are u32: type << 24 | index; type 0 nil, 1 false, 2 true, 3 number, 4 string,
#         5 vector, 6 quaternion, 7 idstring, 8 table; a table's items are {u32 key, u32 value}.
#   The file ends with 4 unreferenced bytes (ASSUMPTION: a checksum).
# custom_xml meaning: the table's meta is the node name; string keys with scalar values are
# attributes; children are the number-keyed entries (1, 2, 3 ...), each a table; a child also
# appears under its name as a string key when that name is unique - the same table, printed once.
SD_TYPES = ('nil', 'false', 'true', 'number', 'string', 'vector', 'quaternion', 'idstring', 'table')


class ScriptData:
    """Reader for the binary scriptdata above. .root is the root item; tables() gives the tree."""

    def __init__(self, d):
        self.d = d
        self.sec = [struct.unpack_from('<4Q', d, 32 * i) for i in range(6)]
        for i, s in enumerate(self.sec):
            if s[0] != 0 or s[1] != s[2]:
                raise ValueError('section %d header %r' % (i, s))
        self.root = struct.unpack_from('<I', d, 0xc8)[0]
        if struct.unpack_from('<Q', d, 0xc0)[0] != 0 or struct.unpack_from('<I', d, 0xcc)[0] != 0:
            raise ValueError('header tail %s' % d[0xc0:0xd0].hex())
        self.used = [set() for _ in range(6)]

    def count(self, sec):
        return self.sec[sec][1]

    def value(self, item):
        """Python value of one item: None/bool/float/str/tuple/('@ID', int)/('table', index)."""
        t, i = item >> 24, item & 0xffffff
        d = self.d
        if t == 0:
            return None
        if t == 1:
            return False
        if t == 2:
            return True
        if t in (3, 4, 5, 6, 7, 8):
            sec = {3: 0, 4: 1, 5: 2, 6: 3, 7: 4, 8: 5}[t]
            if i >= self.sec[sec][1]:
                raise ValueError('item %08x past section %d (%d)' % (item, sec, self.sec[sec][1]))
            self.used[sec].add(i)
            base = self.sec[sec][3]
            if t == 3:
                return struct.unpack_from('<f', d, base + 4 * i)[0]
            if t == 4:
                z, off = struct.unpack_from('<QQ', d, base + 16 * i)
                if z:
                    raise ValueError('string entry %d: first word %d' % (i, z))
                end = d.index(b'\0', off)
                return d[off:end].decode('utf-8', 'replace')
            if t == 5:
                return struct.unpack_from('<3f', d, base + 12 * i)
            if t == 6:
                return struct.unpack_from('<4f', d, base + 16 * i)
            if t == 7:
                return ('@ID', struct.unpack_from('<Q', d, base + 8 * i)[0])
            return ('table', i)
        raise ValueError('item %08x: unknown type' % item)

    def table(self, i):
        """(meta name or None, [(key, value)]) of table i."""
        base = self.sec[5][3]
        meta, n, cap, items, z = struct.unpack_from('<5Q', self.d, base + 40 * i)
        if z or n != cap:
            raise ValueError('table %d record %r' % (i, (meta, n, cap, items, z)))
        name = None
        if meta not in (M64, 0xffffffff):             # custom_xml files write -1 as u64, generic ones as u32
            if meta >= self.sec[1][1]:
                raise ValueError('table %d meta %d' % (i, meta))
            self.used[1].add(meta)
            z, off = struct.unpack_from('<QQ', self.d, self.sec[1][3] + 16 * meta)
            name = self.d[off:self.d.index(b'\0', off)].decode('utf-8', 'replace')
        pairs = []
        for k in range(n):
            key, val = struct.unpack_from('<II', self.d, items + 8 * k)
            pairs.append((self.value(key), self.value(val)))
        return name, pairs


def _sd_scalar(v):
    if v is None:
        return 'nil'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, float):
        return ('%d' % v) if v == int(v) and abs(v) < 1e15 else repr(v)
    if isinstance(v, str):
        return v
    if isinstance(v, tuple) and v and v[0] == '@ID':
        return '@ID%016x@' % v[1]
    return ' '.join(_sd_scalar(float(x)) for x in v)


def _xml_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


XML_DOC_EXTS = ('unit', 'object', 'material_config', 'sequence_manager')


def is_text_xml(data):
    return data.lstrip()[:1] == b'<'


def text_documents(data):
    """The XML documents of a text blob: one, or the two branches of the ` ELSE {` form."""
    t = data.decode('utf-8', 'replace')
    m = re.search(r'\n ELSE \{\n', t)
    if not m:
        return [t]
    a, b = t[:m.start() + 1], t[m.end():]
    if not b.rstrip().endswith('}'):
        raise ValueError('ELSE branch does not end with }')
    return [a, b.rstrip()[:-1]]


def xml_text(data, check=None):
    """Diesel document -> XML text. Text documents are returned decoded (the first branch of an
    ELSE pair; text_documents() gives both, and check gets 'branches' and the parse result of
    each); binary scriptdata is walked from the root table. check (a dict) receives the proof
    counters: tables printed vs the header count, strings referenced vs the string count, floats
    referenced vs the float count, open == close, trailing bytes."""
    if is_text_xml(data):
        docs = text_documents(data)
        if check is not None:
            import xml.dom.minidom
            res = []
            for t in docs:
                try:
                    xml.dom.minidom.parseString(t)
                    res.append('ok')
                except Exception as e:                      # noqa: BLE001 - the reason is the result
                    res.append(str(e))
            check.update({'text': True, 'branches': len(docs), 'well_formed': res})
        return docs[0]
    sd = ScriptData(data)
    if sd.root >> 24 != 8:
        raise ValueError('root item %08x is not a table' % sd.root)
    out = []
    printed = set()
    opened = closed = 0

    def node(ti, depth, default_name):
        nonlocal opened, closed
        printed.add(ti)
        name, pairs = sd.table(ti)
        name = name or default_name
        attrs, children = [], []
        for k, v in pairs:
            is_table = isinstance(v, tuple) and v and v[0] == 'table'
            if isinstance(k, float):
                if is_table:
                    children.append((k, v[1], None))
                else:
                    attrs.append(('_%s' % _sd_scalar(k), v))      # number key, scalar value (generic data)
            elif isinstance(k, str):
                if is_table:
                    children.append((None, v[1], k))                # named table: a child (custom_xml)
                else:
                    attrs.append((k, v))
            else:
                attrs.append((_sd_scalar(k), v))
        children.sort(key=lambda c: (c[0] is None, c[0] or 0))
        seen = set()
        kids = []
        for order, t, key in children:
            if t in seen:
                continue                       # the same child, reached by index and by name
            seen.add(t)
            kids.append((t, key))
        pad = '\t' * depth
        head = pad + '<' + _xml_escape(name) + ''.join(' %s="%s"' % (_xml_escape(k), _xml_escape(_sd_scalar(v))) for k, v in attrs)
        opened += 1
        if not kids:
            out.append(head + '/>')
            closed += 1
            return
        out.append(head + '>')
        for t, key in kids:
            node(t, depth + 1, key or 'table')
        out.append(pad + '</' + _xml_escape(name) + '>')
        closed += 1

    node(sd.root & 0xffffff, 0, 'root')
    if check is not None:
        last_end = 0xd0
        for i in range(sd.count(5)):
            meta, n, cap, items, z = struct.unpack_from('<5Q', data, sd.sec[5][3] + 40 * i)
            last_end = max(last_end, items + 8 * n, sd.sec[5][3] + 40 * (i + 1))
        for i in range(sd.count(1)):
            off = struct.unpack_from('<Q', data, sd.sec[1][3] + 16 * i + 8)[0]
            last_end = max(last_end, data.index(b'\0', off) + 1)
        check.update({'tables': sd.count(5), 'tables_printed': len(printed), 'strings': sd.count(1),
                      'strings_used': len(sd.used[1]), 'floats': sd.count(0), 'floats_used': len(sd.used[0]),
                      'vectors': sd.count(2), 'vectors_used': len(sd.used[2]), 'quats': sd.count(3),
                      'quats_used': len(sd.used[3]), 'idstrings': sd.count(4), 'idstrings_used': len(sd.used[4]),
                      'opened': opened, 'closed': closed, 'trailing': len(data) - last_end})
    return '\n'.join(out) + '\n'


def write_xml(data, out_base):
    """<out_base>.xml (+ .else.xml) from a document blob; returns the check dict (proof)."""
    chk = {}
    t = xml_text(data, chk)
    with open(out_base + '.xml', 'w', encoding='utf-8', newline='') as f:
        f.write(t)
    if chk.get('branches', 1) > 1:
        with open(out_base + '.else.xml', 'w', encoding='utf-8', newline='') as f:
            f.write(text_documents(data)[1])
    return chk


def xml_ok(chk):
    """True when a write_xml / xml_text proof holds: text branches parse, or binary counts match."""
    if chk.get('text'):
        return all(r == 'ok' for r in chk['well_formed'])
    return (chk['tables'] == chk['tables_printed'] and chk['opened'] == chk['closed']
            and chk['strings'] == chk['strings_used'] and chk['floats'] == chk['floats_used']
            and chk['trailing'] == 4)


# -- CLI -------------------------------------------------------------------------------------------
def _fmt_size(n):
    return '%d' % n


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    xml = '--xml' in args
    args = [a for a in args if a != '--xml']
    if cmd == 'index':
        Index(force=True)
        return 0
    ix = Index()
    if cmd == 'find':
        hits = ix.find(args[0])
        for x in hits:
            print('%-90s %-18s %10d  %s%s' % (ix.path_name(x.path), ix.ext_name(x.ext), x.raw, x.crate,
                                               (' [%s]' % PROP_HASH_BY_BIT.get(x.props, hex(x.props))) if x.props else ''))
        print('%d entries' % len(hits))
    elif cmd == 'extract':
        path, ext = args[0], args[1]
        out = args[2] if len(args) > 2 else None
        x = ix.get(path, ext)
        out, d = ix.extract(x, out, xml=xml)
        print('%s -> %s (%d bytes)' % (ix.name(x), out, len(d)))
    elif cmd == 'extract-prefix':
        pre = args[0]
        root = args[1] if len(args) > 1 else None
        hits = ix.prefix(pre)
        total = 0
        for x in hits:
            out, d = ix.extract(x, root=root, xml=xml)
            total += len(d)
            print('%s (%d)' % (out, len(d)))
        print('%d files, %d bytes' % (len(hits), total))
    elif cmd == 'masks':
        m = ix.masks()
        out = os.path.join(ix.work, 'masks_list.json')
        with open(out, 'w') as f:
            json.dump(m, f, indent=0)
        top = [k.split('/')[-1] for k in m if k.startswith('units/payday2/masks/') and k.count('/') == 3]
        print('%d folders with /masks/ in the path, %d directly under units/payday2/masks -> %s' % (len(m), len(top), out))
        print(' '.join(top))
    elif cmd == 'verify':
        for c in args:
            r = ix.verify(c)
            print(json.dumps(r))
    elif cmd == 'stats':
        print('%-28s %8s %14s %14s  %s' % ('extension', 'entries', 'raw bytes', 'stored bytes', 'crates'))
        for ext, n, raw, st, kinds in ix.stats():
            print('%-28s %8d %14d %14d  %s' % (ext, n, raw, st, kinds))
        print('%d entries, %d distinct (path, ext) keys, %d extensions' % (len(ix.entries), len(ix.by_key), len(ix.stats())))
    elif cmd == 'manifest':
        head, crates, props = manifest()
        print('head', head, 'crates', len(crates), 'records', sum(len(v) for v in crates.values()))
        print('properties (manifest tail):', props)
        print('properties (crates.properties):', properties())
        flagged = [(c, e, p) for c, v in crates.items() for e, p, fl in v if fl]
        print('flag == 1:', len(flagged))
        for c, e, p in flagged:
            present = (p, e) in ix.by_key
            print('  %-14s %-20s %s%s' % (c, ix.ext_name(e), ix.path_name(p), '' if present else '  (in no crate table)'))
    elif cmd == 'xml':
        with open(args[0], 'rb') as f:
            d = f.read()
        if len(args) > 1:
            chk = write_xml(d, args[1][:-4] if args[1].endswith('.xml') else args[1])
            print('ok' if xml_ok(chk) else 'MISMATCH', chk)
        else:
            print(xml_text(d))
    else:
        print('unknown command', cmd)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
