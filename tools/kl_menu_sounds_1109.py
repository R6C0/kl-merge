#!/usr/bin/env python3
r"""
kl_menu_sounds_1109.py - Dead Men's front-end clicks in Dog Days' menu (T9 stage 4a, re/menu_look_1109.md 3 + "Stage 4 tool").

Dog Days plays its menu clicks (navigate up / down, confirm, back, error ...) from in-memory `SFX/OSD/*.wav` records of the
GLOBAL bank pair <DD>\Scenes\kaneandlynch.WHD + .WAV, chosen by CODE (re/menu_look_1109.md 3.1; the OSS_DD09_ECHO_S2 dump named
`SFX/OSD/Up_Down.wav` = record 0x64f4: IMA ADPCM 0x11, 32000 Hz, mono, 3 blocks of 0x400, re/gun_echo_1107.md 8). This tool makes a
THEMED COPY of that pair, `kaneandlynch_deadmen.WHD` + `.WAV`, in which ONLY the mapped OSD records' sample data is replaced by a
Dead Men clip decoded, resampled and re-encoded to each record's own format. Every name, every record offset and every other
record stays byte for byte (the .SND inside Scenes\kaneandlynch.zip points at the records by offset and is never touched); the
tool REFUSES when the untouched part does not rebuild byte-identical. The stock pair is never written.

    python tools\kl_menu_sounds_1109.py probe --dd <DD> [--dm <DM>] [--out <dir>] [--max-ms 3000] [--no-levels]
        lists every SFX/OSD/* record of the Dog Days global pair (name, codec, rate, channels, samples, ms, offsets) and every
        short UI-looking clip Dead Men has: in-memory records of every .WHD under <DM>\Scenes (the front-end bank(s) at the top,
        the level banks unless --no-levels) and the clips of <DM>\PC_Def.str. Writes probe.json, probe.txt and a TEMPLATE
        mapping.json (GUESS pairs by name similarity, '_candidates' per record; edit it, null = leave the record stock).
        Says which Dead Men files it could open. Read-only. THIS IS WHAT THE LOCAL SESSION RUNS FIRST.
    python tools\kl_menu_sounds_1109.py stage --dd <DD> --dm <DM> --map <mapping.json> [--out <dir>] [--accept-input]
                                              [--keep-length] [--linear] [--rail] [--level peak|none] [--previews]
        mapping = {"SFX/OSD/<record>.wav": "<Dead Men clip name>" | {"clip": ..., "gain_db": 0.0, "level": "peak"|"none"} | null}.
        Writes <out>\kaneandlynch_deadmen.WHD + .WAV, build_report.json, pins.json (--accept-input on the first run on a PC:
        md5s of the stock pair as read; later runs refuse when the stock pair differs), install.py + INSTALL / UNDO .bat,
        previews\<record>_{stock,deadmen}.wav (16-bit PCM, for the owner's ear) with --previews.
    python tools\kl_menu_sounds_1109.py check <stage dir> --dd <DD>
        re-runs every proof of the stage against the live stock pair (pins, md5s of the staged files, record table, data spans).

LENGTH RULE (default: --keep-length off = "grow"): the .WHD stores per-record sizes the engine TRUSTS: voice init 0x4465f0 reads
the record's rate (+0xc), size-as-PCM (+0x14) and channels (+0x1c) from the record (re/gun_echo_1107.md 8) and the buffer lock
caller takes the record's pcm as the buffer size (re/bank_merge_audit_1025.md); kl_gunsnd.rebuild rewrote pcm / size / samples
/ off of gun records in 42 live level banks (gunraw / gunpunch) and of the F01 PD2 heli records. So the default writes the WHOLE
Dead Men clip: a clip that fits its record's old data span is written there (rest zeroed), a longer one is APPENDED to the .WAV
(16-aligned) and the record's `off` moved; pcm / size / samples follow the new data. install.py (variant) puts the pair BESIDE
the stock one, where the klslot.c [MenuLook] DeadMen=1 step (klmenulook_logic.h, in the tree since 11-09, not run live) opens it. --keep-length instead trims (5 ms fade) or
pads the clip to the record's old sample count so the .WHD stays BYTE-IDENTICAL and only the old data spans change
(kl_gunsnd.rebuild keep_geometry) - the mode for a first bench if the grown bank misbehaves. GUESS: the .SND wave objects'
f32 seconds (+0x18) stay stock in both modes (as in the 42 live gun banks); what the engine does with them is not established.

RESAMPLE / ENCODE: Dead Men clip -> float frames -> channel fit (stereo -> mono = mean, mono -> stereo = copy) -> windowed-sinc
resample to the record's rate (Kaiser beta 8, 16 zero crossings; GUESS: the writer's parameters, no reference; --linear = the
np.interp of kl_gunsnd.resample instead) -> level (default --level peak: scaled so the clip's peak equals the STOCK record's
decoded peak, GUESS so the menu does not get louder / quieter; --level none keeps the Dead Men level; gain_db on top) -> 16-bit
-> the record's codec: IMA ADPCM through kl_gunsnd.ima_encode (block / spb of the record; --rail = its rail-aware quantiser) or
16-bit PCM. A record of another codec (Vorbis 0x1000) or a streamed one is refused.

PROOFS (stage refuses on any; check re-runs them): .WHD same length, same T, same item list (kinds, offsets, name bytes), every
non-mapped record's 17 dwords identical, a mapped record differs only in pcm / size / samples / off / offhi (nothing with
--keep-length); .WAV header {0, size, 3, 4}, every non-mapped in-memory record's data span identical at its old offset, every
byte of the old .WAV outside the mapped records' old spans identical, mapped data inside the file, 16-aligned, size a multiple
of the block, pcm == 2 * samples * channels, every IMA block head valid (step index <= 88, reserved 0), no span overlap;
kl_gunsnd.check_bank_preserved agrees. Record fields are READ through kl_whd (DD_F); nothing is hardcoded by offset.

WHAT IS GUESSED (each marked GUESS in the code / report): which DD OSD record is which click (the template pairs are name
similarity only - the owner / local session decides with the probe table and the previews); that the global pair is what plays
in a level too (re/menu_look_1109.md 3.1); the sinc parameters; the peak match; the .SND seconds; that Dead Men's front-end bank
is <DM>\Scenes\KaneAndLynch.WHD (the probe opens every .WHD under <DM>\Scenes, so a wrong guess costs nothing).
Never: writes the stock pair, a level pair or KL_PortBackup; commits game files (the stage folder is outside the repo).
"""
import argparse, collections, datetime, difflib, glob, hashlib, json, math, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_whd as W                               # .WHD parse / fields (DD_F, DM_F), both games
import kl_gunsnd as G                            # IMA codec (ima_decode / ima_encode rail-aware), rebuild, check_bank_preserved
import kl_launcher_music as L                    # Dead Men stream index + PCM / IMA / Vorbis decode chain (kl_oggdec / ffmpeg / kl_pyvorbis)

try:
    import numpy as np
except ImportError:                              # the probe runs without numpy; stage / check need it (kl_gunsnd does too)
    np = None

STAGE = 'menusounds_1109'
TAG = '.before-' + STAGE
VARIANT = '_deadmen'
OUT_DEFAULT = r'C:\kl_build_1024\menusounds_1109'
STOCK_STEM = 'kaneandlynch'                      # <DD>\Scenes\kaneandlynch.WHD / .WAV (case of the live file kept)
DM_STEM_GUESS = 'kaneandlynch'                   # GUESS: Dead Men's front-end pair has the same stem (Scenes\KaneAndLynch.zip is its menu scene)
OSD_PREFIX = 'sfx/osd/'
PCM, ADPCM, VORBIS = 1, 0x11, 0x1000
CODEC_NAME = {PCM: 'pcm16', ADPCM: 'ima', VORBIS: 'vorbis'}
MAX_MS_DEFAULT = 3000
FADE_MS = 5.0                                    # --keep-length: fade at a cut
# the UI-looking names of Dead Men (lower-case substrings): the probe lists a short clip when one matches
UI_WORDS = ('userinterface', '/ui/', 'menu', 'click', 'confirm', 'back', 'cancel', 'select', 'error', 'osd', 'button', 'cursor',
            'navigate', 'scroll', 'accept', 'deny', 'slider', 'frontend', 'hud', 'tick', 'beep', 'invalid', 'locked', 'focus')
# GUESS pairs by name: a Dog Days record stem token -> words a Dead Men clip name may carry for the same click
SYN = {
    'up_down': ('navigate', 'scroll', 'move', 'cursor', 'up', 'down', 'updown', 'hover', 'focus', 'tick', 'browse', 'switch', 'change'),
    'up': ('up', 'navigate', 'scroll', 'cursor', 'move'),
    'down': ('down', 'navigate', 'scroll', 'cursor', 'move'),
    'menu': ('menu', 'open', 'enter', 'confirm', 'accept', 'ok', 'click', 'press', 'start', 'select'),
    'confirm': ('confirm', 'accept', 'ok', 'enter', 'select', 'click', 'yes', 'start', 'press'),
    'accept': ('confirm', 'accept', 'ok', 'enter', 'select', 'click', 'yes'),
    'select': ('select', 'confirm', 'accept', 'click', 'enter', 'ok'),
    'back': ('back', 'cancel', 'exit', 'close', 'return', 'escape', 'no', 'abort'),
    'cancel': ('cancel', 'back', 'exit', 'close', 'abort', 'no'),
    'error': ('error', 'deny', 'denied', 'invalid', 'locked', 'wrong', 'fail', 'buzz', 'nope', 'negative', 'refuse'),
    'slider': ('slider', 'slide', 'adjust', 'scroll', 'tick'),
    'popup': ('popup', 'open', 'window', 'appear', 'show'),
    'close': ('close', 'back', 'exit', 'cancel'),
}

u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]


class Refused(Exception):
    """A proof failed or an input is not what the tool needs: nothing is written."""


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def md5b(b):
    return hashlib.md5(b).hexdigest()


def read(p):
    with open(p, 'rb') as f:
        return f.read()


# ------------------------------------------------------------------ banks (both games, through kl_whd)
class Rec(object):
    """One .WHD record. rec_off = offset of the record's first dword (what kl_gunsnd.rebuild keys on); whd_ref = rec_off - 4 =
    what a .SND wave object stores (re/audio.md 2.3). f = the fields by kl_whd's names (DD_F / DM_F)."""
    __slots__ = ('game', 'name', 'rec_off', 'f', 'index')

    def __init__(self, game, name, rec_off, f, index):
        self.game, self.name, self.rec_off, self.f, self.index = game, name, rec_off, f, index

    @property
    def whd_ref(self):
        return self.rec_off - 4

    @property
    def codec(self):
        return self.f['fmt'] & 0xffff

    @property
    def streamed(self):
        return bool(self.f['fmt'] & W.STREAMED)

    @property
    def langfile(self):
        return bool(self.f['fmt'] & W.LANGFILE)

    @property
    def data_off(self):
        return self.f['off'] | (self.f.get('offhi', 0) << 32)

    def frames(self):
        """Sample frames: pcm bytes / (2 * channels) - codec independent (pcm = the decoded 16-bit size in both games)."""
        ch = max(1, self.f['ch'])
        return self.f['pcm'] // (2 * ch)

    def ms(self):
        return 1000.0 * self.frames() / self.f['rate'] if self.f['rate'] else 0.0

    def info(self):
        return collections.OrderedDict([
            ('name', self.name), ('rec_off', '%#x' % self.rec_off), ('whd_ref', '%#x' % self.whd_ref),
            ('codec', CODEC_NAME.get(self.codec, '%#x' % self.codec)), ('fmt', '%#x' % self.f['fmt']),
            ('rate', self.f['rate']), ('ch', self.f['ch']), ('bits', self.f['bits']), ('samples', self.f['samples']),
            ('frames', self.frames()), ('ms', round(self.ms(), 1)), ('pcm', self.f['pcm']), ('size', self.f['size']),
            ('data_off', '%#x' % self.data_off), ('block', self.f['block']), ('spb', self.f['spb']),
            ('streamed', self.streamed), ('langfile', self.langfile)])


class Bank(object):
    """A .WHD (+ its .WAV beside it when in-memory data is wanted) of either game, parsed with kl_whd."""

    def __init__(self, game, whd_path, wav_path=None, load_wav=True):
        self.game, self.whd_path = game, whd_path
        self.wav_path = wav_path if wav_path else os.path.splitext(whd_path)[0] + '.WAV'
        if not os.path.isfile(self.wav_path):                     # the live file may spell it .wav
            alt = os.path.splitext(whd_path)[0] + '.wav'
            self.wav_path = alt if os.path.isfile(alt) else self.wav_path
        self.whd = read(whd_path)
        self._wav = None
        self.load_wav = load_wav
        self.items, self.T = W.parse(game, self.whd)
        names = {o: v.decode('latin1') for k, o, v in self.items if k == 'name'}
        self.records = []
        for k, o, v in self.items:
            if k == 'rec':
                f = dict(zip(W.FIELDS[game], v))
                self.records.append(Rec(game, names.get(f['name'], '?'), o, f, len(self.records)))
        self.by_name = {}
        for r in self.records:
            self.by_name.setdefault(r.name.lower().replace('\\', '/'), r)

    @property
    def wav(self):
        """The .WAV bytes, read on first use (the probe never needs the level banks' 20 MB each)."""
        if self._wav is None and self.load_wav and os.path.isfile(self.wav_path):
            self._wav = read(self.wav_path)
        return self._wav

    def find(self, name):
        n = name.lower().replace('\\', '/')
        r = self.by_name.get(n) or self.by_name.get(n + '.wav') or (self.by_name.get(n[:-4]) if n.endswith('.wav') else None)
        if r:
            return r
        hits = [x for k, x in self.by_name.items() if k.endswith('/' + n) or k.endswith('/' + n + '.wav')]
        return hits[0] if len(hits) == 1 else None

    def data(self, r):
        if r.streamed:
            raise Refused('%s is a streamed record (no data in the .WAV)' % r.name)
        if self.wav is None:
            raise Refused('%s: no .WAV beside %s' % (r.name, self.whd_path))
        o, n = r.data_off, r.f['size']
        if not (16 <= o and o + n <= len(self.wav)):
            raise Refused('%s: data %#x+%#x outside the .WAV (%d bytes)' % (r.name, o, n, len(self.wav)))
        return self.wav[o:o + n]


def decode_record(bank, r):
    """In-memory record -> (int16 numpy [frames, ch], rate). PCM 16, IMA ADPCM (kl_gunsnd.ima_decode), Vorbis (kl_launcher_music chain)."""
    data = bank.data(r)
    ch = max(1, r.f['ch'])
    if r.codec == ADPCM:
        block, spb = r.f['block'] or 0x400, r.f['spb'] or ((r.f['block'] or 0x400) - 4 * ch) * 2 // ch + 1
        frames = r.f['samples'] or r.frames()                   # IMA: samples = frames in both games (pcm == 2 * samples, mono)
        return G.ima_decode(data, ch, block, spb, frames), r.f['rate']
    if r.codec == PCM:
        if r.f['bits'] != 16:
            raise Refused('%s: PCM with %d bits (only 16 is decoded)' % (r.name, r.f['bits']))
        a = np.frombuffer(data[:len(data) - len(data) % (2 * ch)], '<i2').reshape(-1, ch)
        return a, r.f['rate']
    if r.codec == VORBIS:
        class _C(object):
            pass
        c = _C(); c.name, c.rate = r.name, r.f['rate']
        try:
            s, vch, vrate = L.decode_vorbis(c, data, L.MAX_SECONDS)
        except L.NoClip as e:
            raise Refused(str(e))
        a = np.frombuffer(s.tobytes(), '<i2' if sys.byteorder == 'little' else '>i2').astype(np.int16).reshape(-1, vch)
        return a, vrate
    raise Refused('%s: codec %#x not decoded' % (r.name, r.codec))


# ------------------------------------------------------------------ Dead Men sources
def dm_whd_paths(dm, levels=True):
    """Every .WHD under <DM>\\Scenes: the top level first (the front-end pair, GUESS KaneAndLynch.WHD), then Locations\\*\\ (level
    banks, their _LS files skipped) when levels. A file moved to KL_PortBackup wins over what stands in its place (kl_whd.files)."""
    out, seen = [], set()
    for root in (os.path.join(dm, 'KL_PortBackup', 'Scenes'), os.path.join(dm, 'Scenes')):
        pats = [os.path.join(root, '*')] + ([os.path.join(root, 'Locations', '*', '*')] if levels else [])
        for pat in pats:
            for p in sorted(glob.glob(pat)):
                if p.upper().endswith('.WHD') and '_LS' not in os.path.basename(p).upper():
                    rel = os.path.relpath(p, root).lower()
                    if rel not in seen:
                        seen.add(rel); out.append(p)
    return out


class DMSources(object):
    """What the Dead Men side can open: banks (.WHD + .WAV, through kl_whd / Bank) and the stream file (kl_launcher_music.Stream).
    opened / failed: what the probe reports."""

    def __init__(self, dm, levels=True, log=print, lazy=True, load_wav=True):
        self.dm, self.log, self.load_wav = dm, log, load_wav
        self.paths = dm_whd_paths(dm, levels)
        self.banks = {}
        self.opened, self.failed = [], []
        self.stream = None
        sp = os.path.join(dm, L.STREAM_NAME)
        if os.path.isfile(sp):
            try:
                self.stream = L.Stream(sp); self.opened.append('%s (%d clips, build %x)' % (sp, self.stream.count, self.stream.build))
            except Exception as e:
                self.failed.append('%s: %s' % (sp, e))
        else:
            self.failed.append('%s: not there' % sp)
        if not lazy:
            for p in self.paths:
                self.bank(p)

    def bank(self, p):
        if p not in self.banks:
            try:
                b = Bank('dm', p, load_wav=self.load_wav)
                self.banks[p] = b
                self.opened.append('%s (%d records, %s)' % (p, len(b.records), '.WAV %d bytes' % os.path.getsize(b.wav_path)
                                                              if os.path.isfile(b.wav_path) else 'NO .WAV'))
            except Exception as e:
                self.banks[p] = None
                self.failed.append('%s: %s' % (p, e))
        return self.banks[p]

    def find(self, name):
        """-> ('bank', Bank, Rec) | ('stream', Stream, Clip) | None; banks in path order (front-end first), then the stream."""
        for p in self.paths:
            b = self.bank(p)
            if b:
                r = b.find(name)
                if r and not r.streamed:
                    return ('bank', b, r)
        for p in self.paths:                                      # a streamed .WHD record: resolve by its clip offset
            b = self.banks.get(p)
            if b:
                r = b.find(name)
                if r and r.streamed and self.stream and not r.langfile:
                    hits = self.stream.blocks.get(r.data_off)
                    if hits:
                        return ('stream', self.stream, [c for c in hits if c.codec != L.SET][0])
        if self.stream:
            c = self.stream.find(name)
            if c:
                return ('stream', self.stream, c)
        return None

    def decode(self, hit):
        """-> (int16 numpy [frames, ch], rate, description)"""
        kind, src, obj = hit
        if kind == 'bank':
            a, rate = decode_record(src, obj)
            return a, rate, 'bank %s record %#x %s' % (os.path.basename(src.whd_path), obj.rec_off, CODEC_NAME.get(obj.codec, '%#x' % obj.codec))
        try:
            s, ch, rate = L.decode(src, obj, L.MAX_SECONDS)
        except L.NoClip as e:
            raise Refused(str(e))
        a = np.frombuffer(s.tobytes(), '<i2' if sys.byteorder == 'little' else '>i2').astype(np.int16).reshape(-1, ch)
        return a, rate, 'stream %s clip @%#x %s' % (os.path.basename(src.path), obj.offset, L.CODEC.get(obj.codec, obj.codec))


def ui_like(name):
    n = name.lower().replace('\\', '/')
    return any(w in n for w in UI_WORDS)


# ------------------------------------------------------------------ Dog Days stock pair
def dd_pair(dd):
    """-> (whd path, wav path) of the LIVE <DD>\\Scenes\\kaneandlynch pair (the case the folder spells). Warns through the return
    when a KL_PortBackup copy exists (then the live one is somebody's build: the .SND it matches is the live kaneandlynch.zip's)."""
    scenes = os.path.join(dd, 'Scenes')
    whd = wav = None
    for p in glob.glob(os.path.join(scenes, '*')):
        b = os.path.basename(p).lower()
        if b == STOCK_STEM + '.whd':
            whd = p
        elif b == STOCK_STEM + '.wav':
            wav = p
    if not whd or not wav:
        raise Refused('no %s.WHD / .WAV pair under %s' % (STOCK_STEM, scenes))
    return whd, wav


def variant_names(whd, wav):
    s1, e1 = os.path.splitext(os.path.basename(whd))
    s2, e2 = os.path.splitext(os.path.basename(wav))
    return s1 + VARIANT + e1, s2 + VARIANT + e2


def osd_records(bank):
    return [r for r in bank.records if r.name.lower().replace('\\', '/').startswith(OSD_PREFIX)]


# ------------------------------------------------------------------ resample / fit / encode
def kaiser(r, beta):
    """Kaiser window at normalised positions r (|r| <= 1 inside, 0 outside)."""
    inside = np.abs(r) <= 1.0
    w = np.zeros_like(r)
    w[inside] = np.i0(beta * np.sqrt(1.0 - r[inside] ** 2)) / np.i0(beta)
    return w


def resample_sinc(x, src, dst, half=16, beta=8.0, chunk=4096):
    """float [frames, ch] at src Hz -> [frames', ch] at dst Hz by a windowed-sinc filter evaluated per output sample
    (= a polyphase FIR with as many phases as output samples). Cutoff = half the lower rate (anti-alias when going down).
    GUESS: 16 zero crossings and Kaiser beta 8 (about -80 dB stop band) are the writer's choice; no reference measurement."""
    if src == dst or len(x) == 0:
        return x
    ratio = float(dst) / float(src)
    n_out = int(round(len(x) * ratio))
    fc = 0.5 * min(1.0, ratio)                         # cycles per input sample
    H = int(math.ceil(half / min(1.0, ratio)))
    offs = np.arange(-H, H + 1)
    xp = np.pad(x, ((H + 1, H + 1), (0, 0)))
    out = np.zeros((n_out, x.shape[1]))
    for s in range(0, n_out, chunk):
        t = np.arange(s, min(n_out, s + chunk)) / ratio
        k0 = np.floor(t).astype(np.int64)
        idx = k0[:, None] + offs[None, :]
        d = t[:, None] - idx
        w = 2.0 * fc * np.sinc(2.0 * fc * d) * kaiser(d / (H + 1.0), beta)
        w /= w.sum(1, keepdims=True)
        out[s:s + len(t)] = np.einsum('nk,nkc->nc', w, xp[idx + H + 1])
    return out


def to_channels(x, ch):
    if x.shape[1] == ch:
        return x
    mono = x.mean(1, keepdims=True)                    # stereo -> mono: mean; mono -> n: copies
    return np.repeat(mono, ch, 1)


def fade_edges(x, rate, ms=FADE_MS, head=False, tail=True):
    n = min(len(x) // 2, max(1, int(rate * ms / 1000.0)))
    if n and tail:
        x[-n:] *= np.linspace(1.0, 0.0, n)[:, None]
    if n and head:
        x[:n] *= np.linspace(0.0, 1.0, n)[:, None]
    return x


def swappable(r):
    """Raises Refused unless record r can take new data here: in memory, 16-bit PCM or IMA ADPCM."""
    if r.streamed:
        raise Refused('%s is a streamed record: not swappable here' % r.name)
    if r.codec not in (PCM, ADPCM) or (r.codec == PCM and r.f['bits'] != 16):
        raise Refused('%s: codec %#x bits %d cannot be encoded (only 16-bit PCM and IMA ADPCM)' % (r.name, r.codec, r.f['bits']))


def fit_clip(a, rate, r, stock_peak=None, keep_length=False, linear=False, level='peak', gain_db=0.0, rail=False):
    """Dead Men clip (int16 [frames, ch] at rate) -> (data bytes, samples field, pcm field, seconds, notes) in record r's format.
    level 'peak': scale so the peak equals stock_peak (the record's own decoded peak; GUESS). gain_db on top. 16-bit clip at the end."""
    notes = []
    swappable(r)
    x = a.astype(np.float64) / 32768.0
    ch = max(1, r.f['ch'])
    if x.shape[1] != ch:
        notes.append('channels %d -> %d (%s)' % (x.shape[1], ch, 'mean' if x.shape[1] > ch else 'copied'))
        x = to_channels(x, ch)
    if rate != r.f['rate']:
        x = G.resample(x, rate, r.f['rate']) if linear else resample_sinc(x, rate, r.f['rate'])
        notes.append('resampled %d -> %d Hz (%s)' % (rate, r.f['rate'], 'linear np.interp' if linear else 'windowed sinc'))
    if keep_length:
        want = r.frames()
        if len(x) > want:
            x = fade_edges(x[:want].copy(), r.f['rate']); notes.append('trimmed to the record\'s %d frames (%.0f ms, %.0f ms fade)' % (want, 1000.0 * want / r.f['rate'], FADE_MS))
        elif len(x) < want:
            x = np.concatenate([x, np.zeros((want - len(x), ch))]); notes.append('padded with silence to %d frames' % want)
    peak = float(np.abs(x).max()) if len(x) else 0.0
    g = 1.0
    if level == 'peak' and stock_peak and peak > 0:
        g = (stock_peak / 32768.0) / peak
        notes.append('level: peak %.3f -> stock peak %.3f (x%.3f, GUESS)' % (peak, stock_peak / 32768.0, g))
    if gain_db:
        g *= 10.0 ** (gain_db / 20.0); notes.append('gain %+.1f dB' % gain_db)
    x = x * g
    if np.abs(x).max() > 1.0:
        notes.append('clipped at 0 dBFS (%.2f)' % np.abs(x).max())
    pcm16 = G.to_i16(np.clip(x, -1.0, 1.0))
    seconds = len(pcm16) / float(r.f['rate'])
    if r.codec == ADPCM:
        block = r.f['block'] or 0x400
        data, spb = G.ima_encode(pcm16, block, rail)
        if r.f['spb'] and spb != r.f['spb']:
            raise Refused('%s: samples per block %d (block %#x, %d ch) != the record\'s %d' % (r.name, spb, block, ch, r.f['spb']))
        return data, len(pcm16), len(pcm16) * ch * 2, seconds, notes
    return pcm16.astype('<i2').tobytes(), len(pcm16) * ch, len(pcm16) * ch * 2, seconds, notes   # PCM: samples x channels (whdconv)


def ima_blocks_ok(data, block, ch):
    """Every block head of an IMA span: step index <= 88, reserved byte 0 (the 14,588 stock blocks' rule, bank_merge_audit_1025)."""
    for bo in range(0, len(data), block):
        for c in range(ch):
            if data[bo + 4 * c + 2] > 88 or data[bo + 4 * c + 3] != 0:
                return False
    return True


# ------------------------------------------------------------------ build + proofs
def build_pair(whd0, wav0, repl, keep_length, log=print):
    """repl: {rec_off: (data, samples, pcm, seconds)} -> (whd1, wav1) through kl_gunsnd.rebuild (keep_geometry = keep_length)."""
    try:
        whd1, wav1, _ = G.rebuild(whd0, wav0, repl, None, log=log, keep_geometry=keep_length)
    except AssertionError as e:
        raise Refused('kl_gunsnd.rebuild / check_bank_preserved: %s' % e)
    return whd1, wav1


def proofs(whd0, wav0, whd1, wav1, mapped, keep_length):
    """-> (problems [], counts {}) of the themed pair against the stock one. mapped = {rec_off} of the swapped records."""
    bad, n = [], collections.OrderedDict()
    mapped = set(mapped)
    try:
        i0, T0 = W.parse('dd', whd0); i1, T1 = W.parse('dd', whd1)
    except ValueError as e:
        return ['.WHD does not parse: %s' % e], n
    n['whd bytes'] = len(whd1); n['records'] = sum(1 for k, _, _ in i1 if k == 'rec'); n['mapped'] = len(mapped)
    if len(whd1) != len(whd0):
        bad.append('.WHD length %d != stock %d' % (len(whd1), len(whd0)))
    if T1 != T0:
        bad.append('.WHD terminator %#x != stock %#x' % (T1, T0))
    if struct.unpack_from('<4I', whd1, 0) != (T0, len(whd1), 3, 4):
        bad.append('.WHD header is not {T, size, 3, 4}')
    if keep_length and whd1 != whd0:
        bad.append('--keep-length: .WHD is not byte-identical')
    if len(i0) != len(i1):
        bad.append('.WHD item count %d != stock %d' % (len(i1), len(i0)))
    free = {'pcm', 'size', 'samples', 'off', 'offhi'}
    recs0, recs1 = {}, {}
    for (k0, o0, v0), (k1, o1, v1) in zip(i0, i1):
        if (k0, o0) != (k1, o1):
            bad.append('.WHD item at %#x: %s != stock %s at %#x' % (o1, k1, k0, o0)); break
        if k0 == 'name':
            if v0 != v1:
                bad.append('name at %#x changed' % o0)
            continue
        f0, f1 = dict(zip(W.DD_F, v0)), dict(zip(W.DD_F, v1))
        recs0[o0], recs1[o0] = f0, f1
        diff = [k for k in W.DD_F if f0[k] != f1[k]]
        if o0 in mapped:
            if set(diff) - free:
                bad.append('mapped record %#x changed %s (only %s may)' % (o0, diff, sorted(free)))
        elif diff:
            bad.append('record %#x (not mapped) changed %s' % (o0, diff))
    for o in mapped:
        if o not in recs0:
            bad.append('mapped offset %#x is no record' % o)
    # .WAV
    if wav1[:4] != wav0[:4] or wav1[8:16] != wav0[8:16] or u32(wav1, 4) != len(wav1):
        bad.append('.WAV header is not {0, size, 3, 4} with size = length')
    if len(wav1) < len(wav0):
        bad.append('.WAV shrank')
    n['wav bytes'] = len(wav1); n['wav grew by'] = len(wav1) - len(wav0)
    spans1 = []
    old_spans_mapped = []
    for o, f0 in recs0.items():
        f1 = recs1[o]
        if f0['fmt'] & W.STREAMED or not f0['size']:
            continue
        a0, s0 = f0['off'] | (f0['offhi'] << 32), f0['size']
        a1, s1 = f1['off'] | (f1['offhi'] << 32), f1['size']
        if o in mapped:
            old_spans_mapped.append((a0, a0 + s0))
            ch = max(1, f1['ch'])
            if not (16 <= a1 and a1 + s1 <= len(wav1)):
                bad.append('mapped %#x: data %#x+%#x outside the .WAV' % (o, a1, s1))
                continue
            if a1 % 16:
                bad.append('mapped %#x: data offset %#x not 16-aligned' % (o, a1))
            if f1['pcm'] != 2 * f1['samples'] * (ch if (f1['fmt'] & 0xffff) == ADPCM else 1):
                bad.append('mapped %#x: pcm %d != 2 * samples %d%s' % (o, f1['pcm'], f1['samples'], ' * ch' if (f1['fmt'] & 0xffff) == ADPCM else ''))
            if (f1['fmt'] & 0xffff) == ADPCM:
                blk = f1['block'] or 0x400
                if s1 % blk:
                    bad.append('mapped %#x: size %#x not a multiple of the block %#x' % (o, s1, blk))
                elif not ima_blocks_ok(wav1[a1:a1 + s1], blk, ch):
                    bad.append('mapped %#x: an IMA block head is invalid' % o)
            spans1.append((a1, a1 + s1, o))
        else:
            if not (16 <= a0 and a0 + s0 <= len(wav1)) or wav1[a0:a0 + s0] != wav0[a0:a0 + s0]:
                bad.append('record %#x (not mapped): data span %#x+%#x differs' % (o, a0, s0))
            spans1.append((a0, a0 + s0, o))
    # every byte of the old file outside the mapped records' OLD spans must be the stock byte
    if np is not None and len(wav1) >= len(wav0):
        A = np.frombuffer(wav0, np.uint8); B = np.frombuffer(wav1[:len(wav0)], np.uint8)
        ok = np.ones(len(wav0), bool)
        ok[4:8] = False                                             # the size field
        for a, e in old_spans_mapped:
            ok[a:e] = False
        n['bytes changed outside the mapped spans'] = int(np.count_nonzero((A != B) & ok))
        if n['bytes changed outside the mapped spans']:
            bad.append('%d .WAV bytes changed outside the mapped records\' spans' % n['bytes changed outside the mapped spans'])
    # no mapped span overlaps another record's span (stock banks share two spans among themselves: only MAPPED overlaps count)
    spans1.sort()
    for (a, e, o), (a2, e2, o2) in zip(spans1, spans1[1:]):
        if a2 < e and (o in mapped or o2 in mapped):
            bad.append('span of %#x overlaps %#x' % (o2, o))
    try:
        n['check_bank_preserved records'] = G.check_bank_preserved(whd0, wav0, whd1, wav1, changed=mapped)
    except AssertionError as e:
        bad.append('kl_gunsnd.check_bank_preserved: %s' % e)
    return bad, n


# ------------------------------------------------------------------ mapping template
def tokens(name):
    stem = os.path.splitext(name.replace('\\', '/').rsplit('/', 1)[-1])[0].lower()
    return [t for t in re.split(r'[^a-z0-9]+', stem) if t], stem


def guess_pairs(dd_names, dm_names, top=4):
    """-> {dd name: [(dm name, score)]} by stem similarity + the SYN table (GUESS pairs, for the template only).
    Score = difflib ratio of the stems, +0.4 a Dog Days token in the Dead Men stem, +0.5 a synonym there, +0.3 when the LAST Dead Men
    token (the specific one: Menu_Back -> back) is a token / synonym, -0.3 when a Dead Men token belongs to ANOTHER Dog Days record's
    family (Menu_Back is not the 'menu' click when a 'back' record exists), +0.2 for a UI folder name."""
    dm_names = list(collections.OrderedDict((n, 1) for n in dm_names))          # unique, order kept
    fam = {}
    for d in dd_names:
        dt, _ = tokens(d)
        syn = set(dt)
        for t in dt:
            syn.update(SYN.get(t, ()))
        syn.update(SYN.get('_'.join(dt), ()))
        fam[d] = syn
    out = {}
    for d in dd_names:
        dt, ds = tokens(d)
        syn = fam[d]
        others = set()
        for o in dd_names:
            if o != d:
                others |= fam[o]
        others -= syn
        scored = []
        for m in dm_names:
            mt, ms = tokens(m)
            s = difflib.SequenceMatcher(None, ds, ms).ratio()
            if any(t in mt for t in dt):
                s += 0.4
            if any(t in syn for t in mt):
                s += 0.5
            if mt and mt[-1] in syn:
                s += 0.3
            if any(t in others for t in mt):
                s -= 0.3
            if 'userinterface' in m.lower() or '/ui/' in m.lower() or 'menu' in m.lower():
                s += 0.2
            scored.append((m, round(s, 3)))
        scored.sort(key=lambda x: -x[1])
        out[d] = scored[:top]
    return out


def template_mapping(dd_names, dm_names):
    cand = guess_pairs(dd_names, dm_names)
    m = collections.OrderedDict()
    m['_note'] = ('TEMPLATE written by kl_menu_sounds_1109.py probe: every pair is a GUESS by name similarity. Edit: value = a Dead Men clip '
                  'name from probe.txt (or {"clip": name, "gain_db": 0.0, "level": "peak"|"none"}), null = leave the record stock. '
                  'Keys starting with _ are ignored by stage.')
    for d in dd_names:
        c = cand[d]
        m[d] = c[0][0] if c and c[0][1] >= 0.5 else None
    m['_candidates'] = {d: cand[d] for d in dd_names}
    return m


def parse_mapping(mapping):
    """mapping.json content -> [(dd name, dm name, gain_db, level or None)] of the pairs that are set."""
    out = []
    for k, v in mapping.items():
        if k.startswith('_') or v is None:
            continue
        if isinstance(v, str):
            out.append((k, v, 0.0, None))
        elif isinstance(v, dict) and v.get('clip'):
            out.append((k, v['clip'], float(v.get('gain_db', 0.0)), v.get('level')))
        else:
            raise Refused('mapping %r: value must be a clip name, {"clip": ...} or null' % k)
    return out


# ------------------------------------------------------------------ pins + install template
def check_pins(found, out_dir, accept, log=print):
    pins_path = os.path.join(out_dir, 'pins.json')
    if accept:
        os.makedirs(out_dir, exist_ok=True)
        json.dump(found, open(pins_path, 'w'), indent=1)
        log('  pins.json written (%d inputs accepted)' % len(found))
        return found
    if not os.path.isfile(pins_path):
        raise Refused('no %s yet: the first stage on this PC needs --accept-input (it records the stock pair\'s md5s as the pins)' % pins_path)
    pins = json.load(open(pins_path))
    for k, v in found.items():
        if pins.get(k) != v:
            raise Refused('%s is md5 %s, pinned %s (the stock pair changed: re-stage with --accept-input)' % (k, v, pins.get(k)))
    return pins


INSTALL = r'''r"""Installs / undoes the DEAD MEN MENU SOUNDS stage @STAGE@ (tools/kl_menu_sounds_1109.py): the themed copy of Dog Days'
global sound bank pair. The STOCK pair <DD>\Scenes\kaneandlynch.WHD / .WAV is NEVER written (asserted on every path).

  python install.py              variant: copy kaneandlynch_deadmen.WHD + .WAV BESIDE the stock pair (<DD>\Scenes\). Played by the
                                 klslot.c [MenuLook] DeadMen=1 step (klmenulook_logic.h: the open of Scenes\kaneandlynch.WHD / .WAV takes
                                 the _deadmen sibling when it exists; a DLL with that step, in the tree since 11-09). NOTE: when an
                                 OVERLAY copy KLExpansion\Overlay\Scenes\kaneandlynch.WHD exists, the step looks for the sibling THERE
                                 (klslot.c 596): then install with --overlay-variant.
  python install.py --overlay-variant  the siblings beside the overlay copy (KLExpansion\Overlay\Scenes\kaneandlynch_deadmen.*)
  python install.py --overlay    copy them as <DD>\KLExpansion\Overlay\Scenes\kaneandlynch.WHD + .WAV (the STOCK names, in the mod's
                                 overlay folder): audible today with [Expansion] Overlay=1 (klslot.c overlay rule), no toggle.
  python install.py --undo       remove what this wrote (md5-checked, only the files it wrote); --overlay --undo for the overlay copies
  python install.py --dry        read-only: pins and what would happen
  --game <dir>                   another Dog Days folder (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
Refuses unless the live stock pair's md5s are the pins (the copy was derived from exactly that pair; its record offsets must match
the .SND inside Scenes\kaneandlynch.zip), unless the staged files are the md5s build_report.json names, while kl2.exe runs, and
when a target exists already (never overwritten). All or nothing."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = @STOCK@            # [(live stock file name under Scenes, pinned md5)]
STAGED = @STAGED@          # [(staged file name, md5, stock file name it stands for)]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry, overlay, ov_var = '--undo' in a, '--dry' in a, '--overlay' in a, '--overlay-variant' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    scenes = os.path.join(game, 'Scenes')
    stock_paths = {os.path.normcase(os.path.join(scenes, n)) for n, _ in STOCK}
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    for n, pin in STOCK:
        p = os.path.join(scenes, n)
        if not os.path.isfile(p):
            print('REFUSED: stock %s is not there' % p); return 1
        cur = md5(p)
        print('%-24s live %s' % (n, cur))
        if cur != pin:
            print('REFUSED: %s md5 is not the pinned %s (the stock pair changed: re-stage with --accept-input)' % (n, pin)); return 1
    plan = []
    for name, m, stock_name in STAGED:
        src = os.path.join(HERE, name)
        if overlay:
            dst = os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', stock_name)
        elif ov_var:
            dst = os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', name)
            if not undo and not os.path.isfile(os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', stock_name)):
                print('REFUSED: no overlay copy %s: the hook would never look for a sibling there (use the plain variant install)'
                      % os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', stock_name)); return 1
        else:
            dst = os.path.join(scenes, name)
        if os.path.normcase(dst) in stock_paths:
            print('REFUSED: target %s is the stock file (never written)' % dst); return 1
        if undo:
            if not os.path.isfile(dst):
                print('REFUSED: %s is not there' % dst); return 1
            if md5(dst) != m:
                print('REFUSED: %s is not the staged md5 %s (not this stage\'s file: left alone)' % (dst, m)); return 1
        else:
            if not os.path.isfile(src) or md5(src) != m:
                print('REFUSED: staged %s missing or not md5 %s' % (src, m)); return 1
            if os.path.exists(dst):
                print('REFUSED: %s exists already (never overwritten; --undo removes this stage\'s own copy)' % dst); return 1
        plan.append((src, dst))
    if not undo:
        need = sum(os.path.getsize(s) for s, _ in plan) + (64 << 20)
        if shutil.disk_usage(game).free < need:
            print('REFUSED: less than the files + 64 MB free on the game drive'); return 1
    if dry:
        for src, dst in plan:
            print('would %s %s' % ('remove' if undo else 'write', dst))
        if overlay and not undo:
            print('note: the overlay copy plays only with [Expansion] Overlay=1 in KLHook.ini')
        return 0
    done = []
    try:
        for src, dst in plan:
            if undo:
                os.remove(dst); print('removed %s' % dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst + '.tmp'); os.replace(dst + '.tmp', dst); done.append(dst)
                print('written %s %s' % (dst, md5(dst)))
    except OSError as e:
        for d in reversed(done):
            try:
                os.remove(d)
            except OSError:
                pass
        print('FAILED (%s); %s' % (e, 'nothing left behind' if not undo else 'rerun --undo')); return 2
    if overlay and not undo:
        print('note: the overlay copy plays only with [Expansion] Overlay=1 in KLHook.ini; the variant form needs the [MenuLook] step')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(stage_dir, game, stock, staged, log=print):
    src = (INSTALL.replace('@GAME@', game).replace('@STAGE@', os.path.basename(stage_dir))
           .replace('@STOCK@', repr(stock)).replace('@STAGED@', repr(staged)))
    open(os.path.join(stage_dir, 'install.py'), 'w', newline='\n').write(src)
    for nm, arg in (('INSTALL menu sounds 1109 (variant).bat', ''), ('INSTALL menu sounds 1109 (overlay).bat', ' --overlay'),
                    ('UNDO menu sounds 1109 (variant).bat', ' --undo'), ('UNDO menu sounds 1109 (overlay).bat', ' --overlay --undo')):
        open(os.path.join(stage_dir, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    log('  install.py + 4 bats written')


def write_wav16(path, a, rate):
    """int16 numpy [frames, ch] -> RIFF/WAVE (previews)."""
    ch = a.shape[1]; d = a.astype('<i2').tobytes()
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(d)) + b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 1, ch, rate, rate * ch * 2, ch * 2, 16))
        f.write(b'data' + struct.pack('<I', len(d)) + d)


# ------------------------------------------------------------------ commands
def probe(dd, dm=None, out_dir=OUT_DEFAULT, max_ms=MAX_MS_DEFAULT, levels=True, log=print):
    rep = collections.OrderedDict([('tool', 'kl_menu_sounds_1109.py probe'), ('when', datetime.datetime.now().isoformat(timespec='seconds')),
                                   ('dd', dd), ('dm', dm)])
    whd, wav = dd_pair(dd)
    bank = Bank('dd', whd, wav)
    rep['dd_pair'] = collections.OrderedDict([('whd', whd), ('whd_md5', md5b(bank.whd)), ('whd_bytes', len(bank.whd)), ('wav', bank.wav_path),
                                              ('wav_md5', md5b(bank.wav) if bank.wav else None), ('wav_bytes', len(bank.wav) if bank.wav else None),
                                              ('records', len(bank.records)), ('T', '%#x' % bank.T)])
    bak = os.path.join(dd, 'KL_PortBackup', 'Scenes', os.path.basename(whd))
    rep['dd_backup_exists'] = os.path.isfile(bak)
    osd = osd_records(bank)
    rep['dd_osd'] = [r.info() for r in osd]
    lines = ['Dog Days global pair %s (%d records, T %#x)%s' % (whd, len(bank.records), bank.T,
                                                               '  WARNING: a KL_PortBackup copy exists, the live one is a build' if rep['dd_backup_exists'] else ''),
             '  SFX/OSD/* records: %d' % len(osd),
             '  %-44s %-6s %6s %2s %7s %7s %8s %8s %10s' % ('name', 'codec', 'rate', 'ch', 'frames', 'ms', 'rec_off', 'size', 'data_off')]
    for r in osd:
        lines.append('  %-44s %-6s %6d %2d %7d %7.1f %8x %8x %10x%s' % (r.name[-44:], CODEC_NAME.get(r.codec, '%#x' % r.codec), r.f['rate'], r.f['ch'],
                                                                     r.frames(), r.ms(), r.rec_off, r.f['size'], r.data_off, ' STREAMED' if r.streamed else ''))
    dm_clips = []
    if dm:
        src = DMSources(dm, levels=levels, log=log, lazy=False, load_wav=False)
        seen = {}
        for p in src.paths:
            b = src.banks.get(p)
            if not b:
                continue
            for r in b.records:
                if not ui_like(r.name):
                    continue
                key = (r.name.lower(), r.f['size'], r.f['rate'])
                if key in seen:
                    seen[key]['also_in'].append(os.path.basename(p)); continue
                d = r.info(); d['source'] = 'bank ' + os.path.relpath(p, dm); d['also_in'] = []
                d['short'] = r.ms() < max_ms
                seen[key] = d
                dm_clips.append(d)
        if src.stream:
            for c in src.stream.clips:
                if c.codec == L.SET or not ui_like(c.name):
                    continue
                ms = 1000.0 * c.seconds()
                dm_clips.append(collections.OrderedDict([('name', c.name), ('codec', L.CODEC.get(c.codec, '%#x' % c.codec)), ('rate', c.rate),
                                                         ('ch', c.channels), ('bits', c.bits), ('ms', round(ms, 1)), ('size', c.size),
                                                         ('data_off', '%#x' % c.offset), ('layer', c.layer), ('source', 'stream PC_Def.str'),
                                                         ('short', ms < max_ms), ('also_in', [])]))
        rep['dm_opened'] = src.opened; rep['dm_failed'] = src.failed
        rep['dm_not_opened'] = ['level archives (.zip: hold the .SND, not .WHD/.WAV; kl_snd reads those for the graft, not needed here)',
                                'language stream files PC_<lang>.str (UI clicks are not localized; a LANGFILE record is skipped)']
        lines += ['', 'Dead Men: opened %d, failed %d' % (len(src.opened), len(src.failed))] + ['  ' + x for x in src.opened] + ['  FAILED ' + x for x in src.failed]
        short = [d for d in dm_clips if d['short']]
        lines += ['', '  UI-looking clips (%d, %d under %d ms; a name with %s):' % (len(dm_clips), len(short), max_ms, ', '.join(UI_WORDS[:8]) + ' ...'),
                  '  %-56s %-6s %6s %2s %7s %-28s %s' % ('name', 'codec', 'rate', 'ch', 'ms', 'source', 'also in')]
        for d in sorted(dm_clips, key=lambda d: (not d['short'], d['name'].lower())):
            lines.append('  %-56s %-6s %6d %2d %7.1f %-28s %s%s' % (d['name'][-56:], d['codec'], d['rate'], d['ch'], d['ms'], d['source'][-28:],
                                                                 ','.join(sorted(set(d['also_in'])))[:40], '' if d['short'] else '  LONG'))
        rep['dm_clips'] = dm_clips
        mapping = template_mapping([r.name for r in osd], [d['name'] for d in short])
    else:
        mapping = template_mapping([r.name for r in osd], [])
        lines += ['', 'no --dm: Dead Men side not probed; mapping.json template has null pairs']
    os.makedirs(out_dir, exist_ok=True)
    json.dump(rep, open(os.path.join(out_dir, 'probe.json'), 'w'), indent=1)
    open(os.path.join(out_dir, 'probe.txt'), 'w').write('\n'.join(lines) + '\n')
    mp = os.path.join(out_dir, 'mapping.json')
    if os.path.isfile(mp):
        mp = os.path.join(out_dir, 'mapping.template.json')
        lines.append('mapping.json exists: template written as mapping.template.json')
    json.dump(mapping, open(mp, 'w'), indent=1)
    for ln in lines:
        log(ln)
    log('wrote %s, probe.txt, %s' % (os.path.join(out_dir, 'probe.json'), os.path.basename(mp)))
    return rep, mapping


def stage(dd, dm, mapping, out_dir=OUT_DEFAULT, accept=False, keep_length=False, linear=False, rail=False, level='peak',
          previews=False, levels=True, log=print, game_for_install=None):
    """-> build report dict. Raises Refused (nothing written then, except pins.json with --accept-input)."""
    if np is None:
        raise Refused('numpy is needed for stage (kl_gunsnd uses it)')
    whd_p, wav_p = dd_pair(dd)
    bank = Bank('dd', whd_p, wav_p)
    if bank.wav is None:
        raise Refused('no .WAV beside %s' % whd_p)
    found = collections.OrderedDict([(os.path.basename(whd_p), md5b(bank.whd)), (os.path.basename(wav_p), md5b(bank.wav))])
    log('stock pair %s (%d records) md5 %s / %s' % (whd_p, len(bank.records), found[os.path.basename(whd_p)][:8], found[os.path.basename(wav_p)][:8]))
    check_pins(found, out_dir, accept, log)
    pairs = parse_mapping(mapping)
    if not pairs:
        raise Refused('the mapping has no pair set (every value null?)')
    src = DMSources(dm, levels=levels, log=log)
    repl, rows, skipped = {}, [], []
    for dd_name, dm_name, gain_db, lv in pairs:
        r = bank.find(dd_name)
        if r is None:
            raise Refused('mapping: %s is no record of %s' % (dd_name, whd_p))
        if r.rec_off in repl:
            raise Refused('mapping: %s named twice' % r.name)
        hit = src.find(dm_name)
        if hit is None:
            raise Refused('mapping: Dead Men clip %r not found in %d banks or the stream (opened: %d, failed: %d)' % (dm_name, len(src.paths), len(src.opened), len(src.failed)))
        a, rate, desc = src.decode(hit)
        if len(a) == 0:
            raise Refused('%s decodes to nothing' % dm_name)
        swappable(r)
        stock, _ = decode_record(bank, r)
        stock_peak = int(np.abs(stock.astype(np.int32)).max()) if len(stock) else 0
        data, samples, pcm, seconds, notes = fit_clip(a, rate, r, stock_peak, keep_length, linear, lv or level, gain_db, rail)
        repl[r.rec_off] = (data, samples, pcm, seconds)
        row = collections.OrderedDict([('dd', r.name), ('rec_off', '%#x' % r.rec_off), ('whd_ref', '%#x' % r.whd_ref), ('dd_codec', CODEC_NAME.get(r.codec)),
                                       ('dd_rate', r.f['rate']), ('dd_ch', r.f['ch']), ('stock_ms', round(r.ms(), 1)), ('stock_size', r.f['size']),
                                       ('dm', dm_name), ('dm_source', desc), ('dm_rate', rate), ('dm_ch', int(a.shape[1])), ('dm_ms', round(1000.0 * len(a) / rate, 1)),
                                       ('new_ms', round(1000.0 * seconds, 1)), ('new_size', len(data)), ('new_samples', samples), ('gain_db', gain_db),
                                       ('level', lv or level), ('notes', notes)])
        rows.append(row)
        log('  %-40s <- %-50s %6.0f ms -> %6.0f ms %s' % (r.name[-40:], dm_name[-50:], r.ms(), 1000.0 * seconds, '; '.join(notes)))
    log('rebuilding (%s):' % ('keep length, .WHD byte-identical' if keep_length else 'grow: in place when it fits, else appended'))
    whd1, wav1 = build_pair(bank.whd, bank.wav, repl, keep_length, log)
    recs1 = {o: dict(zip(W.DD_F, v)) for k, o, v in W.parse('dd', whd1)[0] if k == 'rec'}
    by_off = {r.rec_off: r for r in bank.records}
    for row in rows:
        o = int(row['rec_off'], 16); f1 = recs1[o]
        row['how'] = 'in place' if f1['off'] == by_off[o].f['off'] else 'appended at %#x' % f1['off']
        row['new_fields'] = {k: f1[k] for k in ('pcm', 'size', 'samples', 'off')}
    bad, counts = proofs(bank.whd, bank.wav, whd1, wav1, set(repl), keep_length)
    for b in bad:
        log('  PROOF FAILED: ' + b)
    if bad:
        raise Refused('%d proof(s) failed: nothing written' % len(bad))
    os.makedirs(out_dir, exist_ok=True)
    v_whd, v_wav = variant_names(whd_p, wav_p)
    open(os.path.join(out_dir, v_whd), 'wb').write(whd1)
    open(os.path.join(out_dir, v_wav), 'wb').write(wav1)
    staged = [(v_whd, md5b(whd1), os.path.basename(whd_p)), (v_wav, md5b(wav1), os.path.basename(wav_p))]
    stock = [(os.path.basename(whd_p), found[os.path.basename(whd_p)]), (os.path.basename(wav_p), found[os.path.basename(wav_p)])]
    rep = collections.OrderedDict([
        ('tool', 'kl_menu_sounds_1109.py stage'), ('when', datetime.datetime.now().isoformat(timespec='seconds')), ('dd', dd), ('dm', dm),
        ('stock', stock), ('staged', staged), ('mode', collections.OrderedDict([('keep_length', keep_length), ('resample', 'linear' if linear else 'sinc'),
                                                                                ('rail', rail), ('level', level)])),
        ('mapped_rec_offs', ['%#x' % o for o in sorted(repl)]), ('pairs', rows), ('skipped', skipped), ('proof_counts', counts), ('proofs', 'PASS'),
        ('dm_opened', src.opened), ('dm_failed', src.failed),
        ('GUESS', ['which record is which click (name pairs)', 'the global pair also plays in a level', 'sinc parameters', 'peak match',
                   '.SND wave seconds stay stock'])])
    json.dump(rep, open(os.path.join(out_dir, 'build_report.json'), 'w'), indent=1)
    write_install(out_dir, game_for_install or dd, stock, staged, log)
    if previews:
        pd = os.path.join(out_dir, 'previews'); os.makedirs(pd, exist_ok=True)
        b1 = Bank('dd', os.path.join(out_dir, v_whd), os.path.join(out_dir, v_wav))
        for row in rows:
            r0 = bank.find(row['dd']); r1 = b1.find(row['dd'])
            nm = re.sub(r'[^A-Za-z0-9_]+', '_', os.path.splitext(r0.name.rsplit('/', 1)[-1])[0])
            a0, rt0 = decode_record(bank, r0); a1, rt1 = decode_record(b1, r1)
            write_wav16(os.path.join(pd, nm + '_stock.wav'), a0, rt0); write_wav16(os.path.join(pd, nm + '_deadmen.wav'), a1, rt1)
        log('  previews: %d pairs in %s' % (len(rows), pd))
    log('STAGED %s + %s in %s (%d records swapped, .WAV %+d bytes); proofs PASS; NOT installed' % (v_whd, v_wav, out_dir, len(repl), len(wav1) - len(bank.wav)))
    return rep


def check(stage_dir, dd, log=print):
    """-> problems [] (empty = PASS)."""
    bad = []
    rp = os.path.join(stage_dir, 'build_report.json')
    if not os.path.isfile(rp):
        return ['no build_report.json in %s' % stage_dir]
    rep = json.load(open(rp))
    pins = json.load(open(os.path.join(stage_dir, 'pins.json'))) if os.path.isfile(os.path.join(stage_dir, 'pins.json')) else {}
    if not pins:
        bad.append('no pins.json')
    whd_p, wav_p = dd_pair(dd)
    bank = Bank('dd', whd_p, wav_p)
    live = {os.path.basename(whd_p): md5b(bank.whd), os.path.basename(wav_p): md5b(bank.wav)}
    for n, m in rep['stock']:
        if live.get(n) != m:
            bad.append('live stock %s md5 %s != the stage\'s %s' % (n, live.get(n), m))
        if pins and pins.get(n) != m:
            bad.append('pins.json %s != build_report stock md5' % n)
    staged = {}
    for n, m, stock_name in rep['staged']:
        p = os.path.join(stage_dir, n)
        if not os.path.isfile(p):
            bad.append('staged %s missing' % n); continue
        if fmd5(p) != m:
            bad.append('staged %s md5 != build_report' % n)
        staged[os.path.splitext(n)[1].lower()] = p
    if '.whd' in staged and '.wav' in staged and not bad:
        whd1, wav1 = read(staged['.whd']), read(staged['.wav'])
        mapped = {int(x, 16) for x in rep['mapped_rec_offs']}
        pb, counts = proofs(bank.whd, bank.wav, whd1, wav1, mapped, rep['mode']['keep_length'])
        bad += pb
        for k, v in counts.items():
            log('  %s: %s' % (k, v))
        for row in rep['pairs']:
            r = bank.find(row['dd'])
            if r is None or r.rec_off not in mapped:
                bad.append('pair %s: record not in the live pair / not mapped' % row['dd'])
    for b in bad:
        log('  FAIL ' + b)
    log('check %s: %s' % (stage_dir, 'PASS' if not bad else '%d problem(s)' % len(bad)))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    p = sub.add_parser('probe'); p.add_argument('--dd', required=True); p.add_argument('--dm'); p.add_argument('--out', default=OUT_DEFAULT)
    p.add_argument('--max-ms', type=float, default=MAX_MS_DEFAULT); p.add_argument('--no-levels', action='store_true')
    s = sub.add_parser('stage'); s.add_argument('--dd', required=True); s.add_argument('--dm', required=True); s.add_argument('--map')
    s.add_argument('--out', default=OUT_DEFAULT); s.add_argument('--accept-input', action='store_true'); s.add_argument('--keep-length', action='store_true')
    s.add_argument('--linear', action='store_true'); s.add_argument('--rail', action='store_true'); s.add_argument('--level', choices=('peak', 'none'), default='peak')
    s.add_argument('--previews', action='store_true'); s.add_argument('--no-levels', action='store_true')
    c = sub.add_parser('check'); c.add_argument('stage_dir'); c.add_argument('--dd', required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'probe':
            probe(a.dd, a.dm, a.out, a.max_ms, not a.no_levels)
            return 0
        if a.cmd == 'stage':
            mp = a.map or os.path.join(a.out, 'mapping.json')
            if not os.path.isfile(mp):
                raise Refused('no mapping file %s (run probe first, then edit mapping.json)' % mp)
            stage(a.dd, a.dm, json.load(open(mp)), a.out, a.accept_input, a.keep_length, a.linear, a.rail, a.level, a.previews, not a.no_levels)
            return 0
        if a.cmd == 'check':
            return 1 if check(a.stage_dir, a.dd) else 0
    except Refused as e:
        print('REFUSED: %s' % e)
        return 1
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
