#!/usr/bin/env python3
"""
Kane & Lynch .WHD (wave headers) + .WAV (in-memory wave data): parse, rebuild, convert a
Dead Men record to Dog Days' form. Spec with the evidence: re/audio.md section 3.

    python kl_whd.py test          every .WHD of both games: parse, rebuild, data inside the .WAV

.WHD   {u32 T, u32 size, 3, 4}, names and records, 16 zero bytes at T (_LS files: T = 0 and no
       terminator). A name starts 16-aligned; a record starts at 16n + 4 after 4 zero bytes.
       A wave object of the .SND names its record by the offset of those 4 zero bytes
       (record offset - 4).
.WAV   {0, size, 3, 4} + data; a record's data offset counts from the start of the file.

Record, dwords (Dead Men 0x38 bytes = 14, Dog Days 0x44 = 17):
   Dead Men   name fmt rate bits pcm size ch off        samples block spb lip x30 x34
   Dog Days   name fmt rate bits pcm size ch off offhi  samples block spb lip x34 x38 x3c x40
fmt: low word 1 = PCM, 0x11 = IMA ADPCM, 0x1000 = Ogg Vorbis; 0x00800000 = streamed (off is the
clip's offset in the stream file); 0x00400000 = in a language stream file, not PC_Def.str; top
byte 0x82 / 0x83 = first of 2 / 3 clips interleaved in one stream block, 0x01 / 0x02 = the
second / third.
NOT ESTABLISHED: 'lip' (0, 4, 0x100004 ...: called lip-sync word in the spec by its values only),
x30.. (cd fill or junk in most records), and the two dwords Dog Days added at the end (x3c, x40:
0 and 0x10 in 219,147 of 334,062 stream records).
"""
import collections, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_port_check import find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

NUL = bytes(1)
REC = {'dm': 0x38, 'dd': 0x44}
DM_F = 'name fmt rate bits pcm size ch off samples block spb lip x30 x34'.split()
DD_F = 'name fmt rate bits pcm size ch off offhi samples block spb lip x34 x38 x3c x40'.split()
FIELDS = {'dm': DM_F, 'dd': DD_F}
STREAMED, LANGFILE = 0x00800000, 0x00400000
u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]


def parse(game, b):
    """-> ([('name', offset, bytes) | ('rec', offset, tuple of dwords)] in file order, T).
    Every byte is a name, a record or zero: anything else raises."""
    T, size, v3, v4 = struct.unpack_from('<4I', b, 0)
    if size != len(b) or (v3, v4) != (3, 4):
        raise ValueError('not a .WHD')
    R, out, names, p = REC[game], [], {0}, 0x10
    end = T if T else len(b)
    while p < end:
        v = u32(b, p)
        if v in names and (v or len(names) == 1) and p + R <= end and 0 < (u32(b, p + 4) & 0xffff) <= 0x1000:
            out.append(('rec', p, struct.unpack_from('<%dI' % (R // 4), b, p))); p += R
        elif v == 0:
            p += 4
        elif p % 16 == 0 and 32 <= b[p] < 127:
            e = b.index(NUL, p)
            out.append(('name', p, b[p:e])); names.add(p)
            p = e + 1; p += -p % 4
        else:
            raise ValueError('%#x: neither a name nor a record (%08x)' % (p, v))
    return out, T


def records(game, b):
    """-> {offset a wave object uses (record offset - 4): dict of the record's fields}"""
    return {o - 4: dict(zip(FIELDS[game], v)) for k, o, v in parse(game, b)[0] if k == 'rec'}


def alias(rec):
    """Second / third clip of an interleaved stream block: follows its partner without re-aligning."""
    return (rec[1] >> 24) in (0x01, 0x02)


def build(game, items, T_zero=False, tail=16):
    """The layout the stock files have: a name padded to 16, a record after 4 zero bytes, 16 zero
    bytes at the end. Byte-identical for 183 of 184 Dog Days and 149 of 159 Dead Men files; the
    others pad entries with two or three names differently (rule not found)."""
    R, out, prev = REC[game], bytearray(16), None
    for i, (kind, _off, val) in enumerate(items):
        if kind == 'name':
            pair = prev == 'name' or (i + 1 < len(items) and items[i + 1][0] == 'name')   # two names, then their records
            out += bytes(-len(out) % 16)
            out += val + NUL + (NUL if pair else b'')
            out += bytes(-len(out) % 16)
        else:
            if not (prev == 'rec' and (val[1] >> 24) == 0x01):
                out += bytes(-len(out) % 16)
            out += bytes(4) + struct.pack('<%dI' % (R // 4), *val)
        prev = kind
    out += bytes(-len(out) % 16)
    T = 0 if T_zero else len(out)
    out += bytes(0 if T_zero else tail)
    struct.pack_into('<4I', out, 0, T, len(out), 3, 4)
    return bytes(out)


def to_dd(f, game):
    """Fields of a record of `game` in Dog Days' form (name and off are the caller's to set).
    ASSUMPTION: the two dwords Dog Days added get the most common stock values (0 and 0x10 for a
    streamed record, the cd fill for one in memory); 'offhi' is 0 in all 353,434 stock records."""
    if game == 'dd':
        return dict(f)
    g = {k: f[k] for k in DM_F[:12]}                     # name .. lip: the same fields, one dword further on
    g['offhi'], g['x34'], g['x38'] = 0, f['x30'], f['x34']   # the fill / junk after 'lip' moves along
    g['x3c'], g['x40'] = (0, 0x10) if f['fmt'] & STREAMED else (0xcdcdcd00, 0xcdcdcdcd)
    return g


class Writer:
    """A Dog Days .WHD / .WAV pair that grows: the base's bytes stay where they are (every wave
    object of the base bank names its record by offset), new names, records and data go behind."""

    def __init__(self, whd, wav):
        T = u32(whd, 0)
        if T == 0 or any(whd[T:]):
            raise ValueError('base .WHD has no terminator')
        self.whd, self.wav = bytearray(whd[:T]), bytearray(wav)
        self.added = 0

    def add(self, name, f, data=None):
        """name: bytes; f: Dog Days fields; data: the wave's bytes if it is held in memory.
        -> the offset a wave object stores."""
        f = dict(f)
        if data is not None:
            self.wav += bytes(-len(self.wav) % 16)
            off = len(self.wav)
            self.wav += data
            f['off'], f['offhi'] = off & 0xffffffff, off >> 32
        self.whd += bytes(-len(self.whd) % 16)
        f['name'] = len(self.whd)
        self.whd += name + NUL
        self.whd += bytes(-len(self.whd) % 16)
        at = len(self.whd)
        self.whd += bytes(4) + struct.pack('<17I', *(f[k] for k in DD_F)) + bytes(8)
        self.added += 1
        return at

    def finish(self):
        whd, wav = bytearray(self.whd), bytearray(self.wav)
        whd += bytes(-len(whd) % 16)
        T = len(whd)
        whd += bytes(16)
        struct.pack_into('<4I', whd, 0, T, len(whd), 3, 4)
        wav += bytes(-len(wav) % 16)
        struct.pack_into('<I', wav, 4, len(wav))
        return bytes(whd), bytes(wav)


def game_dir(game):
    return find(*((DM_GUESSES, DM_EXE) if game == 'dm' else (DD_GUESSES, DD_EXE)))


def files(game):
    """Every stock .WHD of a game: a file moved to KL_PortBackup wins over what stands in its
    place (that is our own build)."""
    base = game_dir(game)
    seen = set()
    for root in (os.path.join(base, 'KL_PortBackup', 'Scenes'), os.path.join(base, 'Scenes')):
        for d, _, fs in os.walk(root):
            for f in sorted(fs):
                rel = os.path.relpath(os.path.join(d, f), root)
                if f.upper().endswith('.WHD') and rel not in seen:
                    seen.add(rel)
                    yield os.path.join(d, f)


def selftest(log=print):
    """-> number of failures (a file that does not parse, or data outside the .WAV)"""
    fails = 0
    for g in ('dd', 'dm'):
        tot = collections.Counter()
        for p in files(g):
            b = open(p, 'rb').read()
            tot['files'] += 1
            try:
                items, T = parse(g, b)
            except ValueError as e:
                tot['parse failed'] += 1; fails += 1
                log('  %s %s: %s' % (g, p[-44:], e)); continue
            tot['rebuilt identical'] += build(g, items, T_zero=(T == 0)) == b
            wav = os.path.getsize(p[:-4] + '.WAV') if os.path.isfile(p[:-4] + '.WAV') else -1
            for kind, _off, v in items:
                tot[kind] += 1
                if kind == 'rec':
                    f = dict(zip(FIELDS[g], v))
                    if f['fmt'] & STREAMED:
                        tot['streamed'] += 1
                    else:
                        o = f['off'] | (f.get('offhi', 0) << 32)
                        tot['in memory'] += 1
                        tot['in memory, data inside the .WAV'] += 16 <= o and o + f['size'] <= wav
        fails += tot['in memory'] != tot['in memory, data inside the .WAV']
        log('%s .WHD: %s' % (g, dict(tot)))
    return fails


if __name__ == '__main__':
    if sys.argv[1:2] == ['test']:
        sys.exit(1 if selftest() else 0)
    print(__doc__)
