"""ANP movies: Dead Men's intro (Movies\\M00_Intro*.bik) as one Dog Days style multi-language Bink file.

    py -I tools\\anp_movie.py [--out work\\out_movies\\Movies\\ANP\\M00_Intro.bik] [--check-only]

Reads the player's own Dead Men Movies folder (read only) and writes only --out. Install = copy the file to
<DD>\\Movies\\ANP\\M00_Intro.bik (the menu plays it as Movie00="Movies/ANP/M00_Intro").

Why a rebuild and not a plain copy:
  * kl2 plays movies with binkw32 1.6a (the same version Dead Men ships) and both games' files are 'BIKi',
    1280x720, 48 kHz stereo Bink audio, so the DM file plays as is.
  * But kl2 opens every movie with BINKSNDTRACK (BinkOpen(path, 0x4000) at 0x4df095) after
    BinkSetSoundTrack(1, &id), id = [0xdda79c] (language: 0 English, 1 German, 2 French, 3 Spanish, 4 Italian,
    6 Russian, 7 Polish, 8 Japanese; forced to 0 when [0xddb955] is set). DD's own movies carry 7 tracks with ids
    0,2,4,1,3,6,8. Each DM file has one track, id 0, so in any non-English Dog Days a plain copy plays silent.
  * So: English video + one audio track per DD id, each from DM's file for that language (DM has English, French,
    German, Italian, Spanish; Russian/Japanese get the English audio). Bink audio packets are self-contained (each
    starts with its decoded byte count) and per-track streams are independent, so packet i of language X goes into
    frame i of the output. Costs ~1.2 MB per extra track.

Bink 1 layout used (as read by binkw32 / ffmpeg's bink demuxer):
  0x00 'BIKi', 0x04 file size - 8, 0x08 frames, 0x0c largest frame packet, 0x10 frames, 0x14 w, 0x18 h,
  0x1c fps num, 0x20 fps den, 0x24 video flags, 0x28 n audio tracks, then n x u32 max decoded audio size,
  n x (u16 rate, u16 flags), n x u32 track id, then frames+1 x u32 frame offsets (bit 0 = keyframe; the last one
  = file size). Frame packet = per track (u32 size, data), then video.
"""
import argparse, hashlib, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anp_paths

DD_TRACKS = [0, 2, 4, 1, 3, 6, 8]                        # order and ids exactly as in DD's own movies
LANG_OF_ID = {0: 'English', 1: 'German', 2: 'French', 3: 'Spanish', 4: 'Italian', 6: 'Russian', 7: 'Polish', 8: 'Japanese'}
DM_FILE = {'English': 'M00_Intro.bik', 'German': 'M00_Intro_German.bik', 'French': 'M00_Intro_French.bik',
           'Spanish': 'M00_Intro_Spanish.bik', 'Italian': 'M00_Intro_Italian.bik'}


class Bink:
    def __init__(self, path):
        self.path = path
        d = self.d = open(path, 'rb').read()
        if len(d) < 0x2c or d[:3] != b'BIK':
            raise SystemExit('%s: not a Bink 1 file' % path)
        (self.sig, size, self.frames, self.largest, frames2, self.w, self.h, self.fpsn, self.fpsd, self.vflags,
         self.ntr) = struct.unpack_from('<4s10I', d, 0)
        if size + 8 != len(d) or frames2 != self.frames or not 0 < self.ntr <= 16:
            raise SystemExit('%s: unexpected header (size %d/%d, frames %d/%d, tracks %d)'
                             % (path, size + 8, len(d), self.frames, frames2, self.ntr))
        n = self.ntr; o = 0x2c
        self.maxdec = list(struct.unpack_from('<%dI' % n, d, o)); o += 4 * n
        self.afmt = [struct.unpack_from('<HH', d, o + 4 * i) for i in range(n)]; o += 4 * n
        self.ids = list(struct.unpack_from('<%dI' % n, d, o)); o += 4 * n
        self.idx = struct.unpack_from('<%dI' % (self.frames + 1), d, o)
        self.hdr_end = o + 4 * (self.frames + 1)
        if (self.idx[0] & ~1) != self.hdr_end or (self.idx[-1] & ~1) != len(d):
            raise SystemExit('%s: frame table does not span the file' % path)
        sizes = [(self.idx[i + 1] & ~1) - (self.idx[i] & ~1) for i in range(self.frames)]
        if max(sizes) != self.largest:
            raise SystemExit('%s: largest-frame field %d != %d' % (path, self.largest, max(sizes)))

    def packet(self, i):
        """(keyframe, [audio packet per track], video bytes)"""
        a, b = self.idx[i] & ~1, self.idx[i + 1] & ~1
        p = a; au = []
        for t in range(self.ntr):
            n = struct.unpack_from('<I', self.d, p)[0]
            if p + 4 + n > b:
                raise SystemExit('%s: frame %d audio overruns the packet' % (self.path, i))
            au.append(self.d[p + 4:p + 4 + n]); p += 4 + n
        return self.idx[i] & 1, au, self.d[p:b]

    def describe(self):
        return '%s %s %dx%d %d frames %.2f fps, tracks %s ids %s, %d bytes' % (
            os.path.basename(self.path), self.sig.decode(), self.w, self.h, self.frames, self.fpsn / self.fpsd,
            ['%d Hz %04x' % f for f in self.afmt], self.ids, len(self.d))


def build(dm_movies, out, check_only=False):
    src = {}
    for lang, fn in DM_FILE.items():
        p = os.path.join(dm_movies, fn)
        if os.path.isfile(p):
            src[lang] = Bink(p)
            print('  ' + src[lang].describe())
        else:
            print('  %s: missing (%s falls back to English audio)' % (fn, lang))
    if 'English' not in src:
        raise SystemExit('Dead Men intro not found: %s' % os.path.join(dm_movies, DM_FILE['English']))
    base = src['English']
    for lang, b in src.items():
        if b.ntr != 1 or (b.w, b.h) != (base.w, base.h) or b.afmt != base.afmt:
            raise SystemExit('%s: unexpected format (want 1 track, %dx%d, %s)' % (b.path, base.w, base.h, base.afmt))
        if b.sig != base.sig:
            raise SystemExit('%s: Bink revision %s != %s' % (b.path, b.sig, base.sig))
    tracks = []                                           # (dd id, source Bink)
    for tid in DD_TRACKS:
        lang = LANG_OF_ID[tid]
        tracks.append((tid, src.get(lang, base)))
    n = len(tracks); F = base.frames
    for tid, b in tracks:
        if b.frames != F:
            tail = [len(b.packet(i)[1][0]) for i in range(F, b.frames)]
            print('  note: %s has %d frames (English %d); its last %d audio packets (%d bytes) are dropped'
                  % (os.path.basename(b.path), b.frames, F, b.frames - F, sum(tail)))
    if check_only:
        return None
    # header
    hdr = bytearray(struct.pack('<4s10I', base.sig, 0, F, 0, F, base.w, base.h, base.fpsn, base.fpsd, base.vflags, n))
    hdr += struct.pack('<%dI' % n, *[b.maxdec[0] for _, b in tracks])
    hdr += b''.join(struct.pack('<HH', *b.afmt[0]) for _, b in tracks)
    hdr += struct.pack('<%dI' % n, *[tid for tid, _ in tracks])
    table_at = len(hdr); hdr += b'\0' * 4 * (F + 1)
    body = []; offs = []; pos = len(hdr); largest = 0
    for i in range(F):
        key, _, video = base.packet(i)
        parts = []
        for tid, b in tracks:
            a = b.packet(i)[1][0] if i < b.frames else b''
            parts.append(struct.pack('<I', len(a)) + a)
        pk = b''.join(parts) + video
        offs.append(pos | key); pos += len(pk); largest = max(largest, len(pk)); body.append(pk)
    offs.append(pos)
    struct.pack_into('<%dI' % (F + 1), hdr, table_at, *offs)
    struct.pack_into('<I', hdr, 4, pos - 8)
    struct.pack_into('<I', hdr, 0xc, largest)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = out + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(hdr)
        for pk in body: f.write(pk)
    # verify: re-parse, video identical to the English file, every track's audio stream identical to its source
    o = Bink(tmp)
    assert o.frames == F and o.ids == [t for t, _ in tracks] and o.sig == base.sig
    hv = hashlib.sha1(); hb = hashlib.sha1(); ha = [hashlib.sha1() for _ in tracks]; hs = [hashlib.sha1() for _ in tracks]
    for i in range(F):
        k, au, v = o.packet(i); k0, _, v0 = base.packet(i)
        assert k == k0
        hv.update(v); hb.update(v0)
        for t, (tid, b) in enumerate(tracks):
            ha[t].update(au[t])
            if i < b.frames: hs[t].update(b.packet(i)[1][0])
    assert hv.digest() == hb.digest(), 'video differs'
    assert all(x.digest() == y.digest() for x, y in zip(ha, hs)), 'audio differs'
    os.replace(tmp, out)
    print('  wrote %s: %s' % (out, o.describe().split(' ', 1)[1]))
    print('  track sources: %s' % ', '.join('%d=%s' % (tid, os.path.basename(b.path)) for tid, b in tracks))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dm', help='Dead Men folder (default: found by anp_paths / ANP_DM_GAME)')
    ap.add_argument('--out', default=os.path.join(anp_paths.WORK, 'out_movies', 'Movies', 'ANP', 'M00_Intro.bik'))
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--install', action='store_true',
                    help='write straight to <DD>\\Movies\\ANP\\M00_Intro.bik (game closed); the menu (anp_menu.py --intro '
                         'auto) then turns the intro on')
    a = ap.parse_args()
    dm = a.dm or anp_paths.game_dir('ANP_DM_GAME', anp_paths.DM_FOLDER)
    dd_movies = None
    try:
        dd_movies = os.path.join(anp_paths.game_dir('ANP_DD_GAME', anp_paths.DD_FOLDER), 'Movies')
    except SystemExit:
        pass
    if a.install:
        if not dd_movies: raise SystemExit('--install: Dog Days folder not found (set ANP_DD_GAME)')
        a.out = os.path.join(dd_movies, 'ANP', 'M00_Intro.bik')
    if dd_movies and os.path.abspath(a.out).lower().startswith(os.path.abspath(dd_movies).lower()) and anp_paths.game_running():
        raise SystemExit('kl2.exe is running: Bink keeps movie files open; close the game first')
    if os.path.abspath(a.out).lower().startswith(os.path.abspath(dm).lower()):
        raise SystemExit('refusing to write into the Dead Men folder')
    print('Dead Men movies: %s' % os.path.join(dm, 'Movies'))
    build(os.path.join(dm, 'Movies'), a.out, a.check_only)


if __name__ == '__main__':
    main()
