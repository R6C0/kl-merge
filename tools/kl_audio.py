#!/usr/bin/env python3
"""
Kane & Lynch sound-stream tool (PC_*.str, "IOISNDSTREAM" v9) - Dead Men and Dog Days.

    python kl_audio.py list    <file.str> [filter]
    python kl_audio.py extract <file.str> [filter] [outdir]

With no arguments it extracts every Fragile Alliance clip (voice lines, menu
lines, FA music) from Dead Men's PC_Def.str into ./audio/ as playable files:
  codec 2/26 -> 16-bit PCM .wav     codec 3 -> IMA ADPCM .wav     codec 4 -> .ogg
Each clip's lip-sync data (if any) is saved next to it as .lip.

Index record (72 bytes, 9 x u64):
  0 sample-ish id   1 data offset   2 audio size   3 format ptr   4 (fmt len | x<<32)
  5 name length     6 name ptr      7 flags        8 flags
Format: u32 codec, samples, channels, rate, bits (+ IMA: block align, samples/block)
Clips that start with 'LIP ' keep audio 0x1000 bytes further on.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DM_STR = [r"G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\PC_Def.str",
          os.path.join(os.path.dirname(HERE), 'PC_Def.str')]
FA_FILTER = ('Multiplayer/', 'Fragile_Alliance')
# Retomoto Tower (M09_A + M09_B as a Fragile Alliance map, re/retomoto.md 6, re/retomoto_fa.md 6): the
# level's music (7 clips, two layers each), its window explosion and bomb warm-up, A's ambience beds and
# the Japanese guard / police lines. None is matched by FA_FILTER, so the authored layer was silent.
# Prefixes are the clip names as kl_audio.py list prints them. Rebuild with 'python kl_audio.py merge'.
RETOMOTO_FILTER = ('Music/InHouse/Japan/M09_A/', 'LevelSetup/Level/M09_A/Music/', 'SFX/Explosions/Bomb/',
                   'SFX/Ambiences/M09_A/', 'SFX/Ambiences/M09_B/', 'LevelSetup/Level/M09_A/Cuts/',
                   'Dialog/AllLevels/Oneliners/Japanese/')
MERGE_FILTER = FA_FILTER + RETOMOTO_FILTER      # what merge() takes by default
LIP_BLOCK = 0x1000


class Clip:
    __slots__ = ('name', 'offset', 'size', 'codec', 'samples', 'channels', 'rate', 'bits',
                 'block', 'fmt', 'rec', 'lip')


class StreamFile:
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        h = self.f.read(0x40)
        if h[:12] != b'IOISNDSTREAM':
            raise ValueError('not an IOISNDSTREAM file')
        self.version = struct.unpack_from('<I', h, 12)[0]
        # Dead Men: u32 index offset @0x18, count @0x1c.  Dog Days: u64 @0x18, count @0x20.
        if struct.unpack_from('<I', h, 0x1c)[0] == 0:
            self.index, self.count, self.wide = struct.unpack_from('<Q', h, 0x18)[0], struct.unpack_from('<I', h, 0x20)[0], True
        else:
            self.index, self.count, self.wide = struct.unpack_from('<I', h, 0x18)[0], struct.unpack_from('<I', h, 0x1c)[0], False
        self.f.seek(self.index)
        raw = self.f.read(72 * self.count)
        self.clips = []
        for i in range(self.count):
            q = struct.unpack_from('<9Q', raw, 72 * i)
            c = Clip()
            c.rec = q
            c.offset, c.size = q[1], q[2]
            self.f.seek(q[6]); c.name = self.f.read(q[5]).split(b'\0')[0].decode('latin1')
            self.f.seek(q[3]); c.fmt = self.f.read(q[4] & 0xffffffff)
            c.codec, c.samples, c.channels, c.rate, c.bits = struct.unpack_from('<5I', c.fmt)
            c.block = struct.unpack_from('<I', c.fmt, 28)[0] if c.codec == 3 and len(c.fmt) >= 32 else 0
            self.f.seek(c.offset); c.lip = self.f.read(4) == b'LIP '
            self.clips.append(c)

    def read(self, c):
        """-> (audio bytes, lip bytes or None)"""
        self.f.seek(c.offset)
        if c.lip:
            head = self.f.read(LIP_BLOCK)
            L = struct.unpack_from('<I', head, 4)[0]
            lip = head[:8 + L]
        else:
            lip = None
        return self.f.read(c.size), lip


def wav_pcm(c, data):
    ch, rate = c.channels, c.rate
    hdr = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36 + len(data), b'WAVE', b'fmt ', 16, 1, ch, rate,
                      rate * ch * 2, ch * 2, 16, b'data', len(data))
    return hdr + data

def wav_ima(c, data):
    ch, rate, block = c.channels, c.rate, c.block or 1024
    spb = (block - 4 * ch) * 8 // (4 * ch) + 1
    fmt = struct.pack('<HHIIHHHH', 0x11, ch, rate, rate * block // spb, block, 4, 2, spb)
    fact = struct.pack('<4sII', b'fact', 4, c.samples)
    body = b'fmt ' + struct.pack('<I', len(fmt)) + fmt + fact + b'data' + struct.pack('<I', len(data)) + data
    return b'RIFF' + struct.pack('<I', 4 + len(body)) + b'WAVE' + body


# ---- IMA ADPCM decoder (used when converting clips for Dog Days)
_STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97,
         107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
         876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428,
         4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350,
         22385, 24623, 27086, 29794, 32767]
_IDX = [-1, -1, -1, -1, 2, 4, 6, 8]

def ima_to_pcm(c, data):
    """Mono IMA ADPCM (MS block layout) -> 16-bit PCM bytes."""
    import array
    block = c.block or 1024
    out = array.array('h')
    step_t, idx_t = _STEP, _IDX
    for b in range(0, len(data) - 3, block):
        blk = data[b:b + block]
        pred, idx = struct.unpack_from('<hB', blk, 0)
        idx = min(idx, 88)
        out.append(pred)
        for byte in blk[4:]:
            for nib in (byte & 15, byte >> 4):
                step = step_t[idx]
                diff = step >> 3
                if nib & 4: diff += step
                if nib & 2: diff += step >> 1
                if nib & 1: diff += step >> 2
                pred = pred - diff if nib & 8 else pred + diff
                pred = -32768 if pred < -32768 else 32767 if pred > 32767 else pred
                out.append(pred)
                idx += idx_t[nib & 7]
                idx = 0 if idx < 0 else 88 if idx > 88 else idx
    del out[c.samples:]
    if sys.byteorder != 'little':
        out.byteswap()
    return out.tobytes()


def export(sf, c, outdir):
    audio, lip = sf.read(c)
    base = os.path.join(outdir, *c.name.replace('\\', '/').split('/'))
    base = os.path.splitext(base)[0]
    os.makedirs(os.path.dirname(base), exist_ok=True)
    if c.codec == 4:
        path = base + '.ogg'; blob = audio
    elif c.codec == 3:
        path = base + '.wav'; blob = wav_ima(c, audio)
    elif c.codec == 2:
        path = base + '.wav'; blob = wav_pcm(c, audio)
    elif c.codec == 26:
        # alias entry: same audio as a codec-2 clip; 'samples' counts bytes at half rate
        class _C: pass
        a = _C(); a.channels, a.rate = c.channels, c.rate // 2
        path = base + '.wav'; blob = wav_pcm(a, audio[:c.samples])
    else:
        path = base + '.codec%d.bin' % c.codec; blob = audio
    open(path, 'wb').write(blob)
    if lip:
        open(base + '.lip', 'wb').write(lip)
    return path


def name_key(name):
    """Lookup key both games store per clip (index is sorted by it): h = h*5 + byte."""
    h = 0
    for b in name.encode('latin1'):
        h = (h * 5 + b) & 0xffffffff
    return h


def merge(dd_path, dm_path, out_path, want=lambda n: any(f in n for f in MERGE_FILTER), log=print):
    """Write a copy of Dog Days' stream file with Dead Men clips added.
    Dog Days' own clips and bytes are untouched; new clips, formats and names are appended
    and a new index (sorted by name key) is written at the end. Clips keep their original
    codec (Dead Men level sound banks refer to them by offset and format), so nothing is
    re-encoded. If out_path already holds a copy of the Dog Days file (e.g. made with a
    plain file copy) it is reused instead of copying 1.2 GB again.
    Also writes <out_path>.map.json: Dead Men offset -> [new offset, size]."""
    import json
    dd, dm = StreamFile(dd_path), StreamFile(dm_path)
    if not dd.wide:
        raise ValueError('first file must be the Dog Days stream file')
    have = {c.name.lower() for c in dd.clips}
    pick = [c for c in dm.clips if want(c.name) and c.name.lower() not in have]
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    if os.path.isfile(out_path) and os.path.getsize(out_path) >= dd.index:
        out = open(out_path, 'r+b')
        out.seek(0); same_head = out.read(0x40) == (dd.f.seek(0) or dd.f.read(0x40))
        out.seek(dd.index - 4096); dd.f.seek(dd.index - 4096)
        if not same_head and out.read(4096) != dd.f.read(4096):
            raise ValueError('existing output is not a copy of the Dog Days stream file')
        out.truncate(dd.index); out.seek(dd.index)
    else:
        out = open(out_path, 'w+b')
        dd.f.seek(0)
        remaining = dd.index
        while remaining:
            chunk = dd.f.read(min(remaining, 64 << 20)); out.write(chunk); remaining -= len(chunk)
    def align(n=0x100):
        out.write(b'\0' * ((-out.tell()) % n))
    placed = {}
    extent = {}                     # several clips can share one audio block: copy the largest
    for c in dm.clips:
        e = (LIP_BLOCK if c.lip else 0) + c.size
        if e > extent.get(c.offset, 0):
            extent[c.offset] = e
    recs = [c.rec for c in dd.clips]
    next_id = len(recs)
    for c in sorted(pick, key=lambda c: c.codec == 26):
        if c.offset not in placed:
            dm.f.seek(c.offset)
            raw = dm.f.read(extent[c.offset])
            align()
            placed[c.offset] = (out.tell(), c.size)
            out.write(raw)
        new_off = placed[c.offset][0]
        align(4); fmt_ptr = out.tell(); out.write(c.fmt)
        nb = c.name.encode('latin1') + b'\0'
        name_ptr = out.tell(); out.write(nb)
        q = list(c.rec)
        q[0] = next_id; next_id += 1
        q[1], q[3] = new_off, fmt_ptr
        q[4] = len(c.fmt) | (name_key(c.name) << 32)
        q[5], q[6] = len(nb), name_ptr
        recs.append(tuple(q))
    recs.sort(key=lambda q: q[4] >> 32)
    align(4)
    index = out.tell()
    for q in recs:
        out.write(struct.pack('<9Q', *q))
    out.truncate()
    out.seek(0x18); out.write(struct.pack('<QI', index, len(recs)))
    out.close()
    json.dump({str(k): v for k, v in placed.items()}, open(out_path + '.map.json', 'w'))
    log('added %d Dead Men clips (%d audio blocks) -> %s' % (len(pick), len(placed), out_path))
    return pick


def verify_merge(out_path, dd_path, dm_path, added):
    """Re-open the merged file and check every clip resolves and matches its source."""
    import bisect, hashlib
    m, dd, dm = StreamFile(out_path), StreamFile(dd_path), StreamFile(dm_path)
    keys = [c.rec[4] >> 32 for c in m.clips]
    assert keys == sorted(keys), 'index not sorted'
    by = {}
    for c in m.clips:
        by.setdefault(c.name, c)
    def find(name):
        k = name_key(name); i = bisect.bisect_left(keys, k)
        while i < len(keys) and keys[i] == k:
            if m.clips[i].name == name: return m.clips[i]
            i += 1
    bad = 0
    for c in dd.clips:
        n = find(c.name)
        if n is None or n.offset != c.offset or n.size != c.size: bad += 1
    for c in added:
        n = find(c.name)
        if n is None: bad += 1; continue
        if m.read(n)[0] != dm.read(c)[0]: bad += 1
    return len(m.clips), bad


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else 'extract'
    path = a[1] if len(a) > 1 else next((p for p in DM_STR if os.path.isfile(p)), None)
    if not path:
        path = input("Path to Dead Men's PC_Def.str: ").strip().strip('"')
    filt = a[2] if len(a) > 2 and cmd != 'merge' else None
    outdir = a[3] if len(a) > 3 else os.path.join(HERE, 'audio')
    sf = StreamFile(path)
    pick = [c for c in sf.clips if (filt in c.name if filt else any(f in c.name for f in FA_FILTER))]
    # one file per clip: skip codec-26 aliases that share audio with a codec-2 entry
    real = {c.offset for c in pick if c.codec != 26}
    pick = [c for c in pick if not (c.codec == 26 and c.offset in real)]
    if cmd == 'merge':
        # python kl_audio.py merge <DeadMen PC_Def.str> <DogDays PC_Def.str> <output PC_Def.str>
        # optional 5th arg: text file of extra clip names (one per line) to include
        dd_path, out_path = a[2], a[3]
        extra = set(open(a[4]).read().split('\n')) if len(a) > 4 else set()
        added = merge(dd_path, path, out_path,
                      want=lambda n: n in extra or any(f in n for f in MERGE_FILTER))
        total, bad = verify_merge(out_path, dd_path, path, added)
        print('verify: %d clips in merged file, %d problems' % (total, bad))
        return
    if cmd == 'list':
        for c in pick:
            print('%-6s %6.1fs %5dHz %dch %s' % ({2: 'pcm', 3: 'ima', 4: 'ogg', 26: 'pcm26'}.get(c.codec, c.codec),
                                                 c.samples / max(1, c.rate), c.rate, c.channels, c.name))
        print(len(pick), 'clips')
        return
    for k, c in enumerate(pick, 1):
        export(sf, c, outdir)
        print('\r  %d/%d' % (k, len(pick)), end='', flush=True)
    print('\nextracted %d clips -> %s' % (len(pick), outdir))


if __name__ == '__main__':
    main()
    if os.name == 'nt' and len(sys.argv) == 1:
        input('\nPress Enter to close...')
