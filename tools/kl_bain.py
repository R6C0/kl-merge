#!/usr/bin/env python3
"""
Bain (Payday 2's voice in the crew's ear) as the announcer of a finished Fragile Alliance build.
Spec, the line tables with both texts and the live checks: re/bain.md.

    python kl_bain.py lines [<build dir>]        the mapping: field, Dog Days key + text, Bain label + text
    python kl_bain.py find <text>                Bain's subtitled lines that hold the text (label, s, text)
    python kl_bain.py wav <label> <out.wav>      decode one line to listen to it (plain PCM WAVE)
    python kl_bain.py events                     Bain's lines WITHOUT a label, found through the sound banks
    python kl_bain.py build [<src dir> [<dst dir>]] [--set driver,brief] [--stream <base PC_Def.str>]
                            [--radio 0]          (--radio 1, the default: each line between Bain's two radio clicks)
                                                 <dst dir> = the build with Bain; <dst dir>/../PC_Def.str
                                                 = the stream file it needs. Nothing is installed.
    python kl_bain.py check <dst dir> [<PC_Def.str>]   the checks of build(), again
    Defaults: src <work>/build/rt_ai3/retomoto_ai3, dst <work>/build/v_bain/retomoto_bain, the base
    stream file <work>/build/PC_Def.str (= the one installed for the owner, 1,684,486,009 bytes).

WHAT IT DOES (every step measured offline on 2026-10-10; NOTHING of it has run in the game)
  Payday 2 side. A voice stream of Payday 2 (a Wwise .wem under soundbanks/streamed/<bank>/<id>) carries
  its subtitle keys as RIFF cue labels: `cue ` = u32 n + n x {u32 id, u32 position, 'data', 3 x u32},
  `LIST` 'adtl' = `labl` {u32 cue id, text}. The label IS the key of strings/subtitles.strings
  (hash64 of the label): 19,004 labels on 18,608 of the 74,437 streams, 8,841 of Bain's (`pln_*`, 4
  `ban_*`), 8,710 with an English text. All of Bain's labelled streams are PTADPCM (tag 0x8311), which
  pd2_audio decodes (8,512 mono 32 kHz, 200 stereo 32 kHz, 129 at 44.1 kHz); all the ones chosen here
  are mono 32,000 Hz - the rate and layout of Dog Days'
  own dialogue, so nothing is resampled. Bain's GENERIC lines (gamedata/dialogs/planner_generic,
  narrator: 'Van's here!', 'One minute.', 'The police are here!') carry no label; they are found
  through the sound bank instead (pd2_events: soundbanks/regular_vox.bnk, HIRC event -> play action
  -> sequence container -> sounds -> stream ids). An event with ONE line stream is exact (its text is
  subtitle <event>_01); with several, WHICH stream speaks which text is an ASSUMPTION (the playlist
  order is the subtitle number in 74 % of the labelled events only), so TABLE takes single ones.
  RADIO. Bain's events are a sequence of three sounds: regular_vox/111416 (0.154 s, his radio
  opening), the line, regular_vox/229541 (0.116 s, closing) - counts: `kl_bain.py events`.
  --radio 1 (default) writes each clip that way, as Payday 2 plays it.
  Kane & Lynch side, on a COPY of the build:
  1. each chosen line is decoded, turned down to the loudness of the line it replaces (GAIN) and
     appended to the stream file as a single 16-bit PCM clip (stream_add): the base file's bytes up
     to its tables keep their place, so every level built against the base stays valid. PCM because
     that is what can be written here and what the stream player is known to take: Dog Days' own
     file has 42 PCM clips (re/audio.md 3), the Retomoto theme (a PCM set) was heard by the owner.
  2. one sound + one wave per clip are appended to the level's .SND (bank_add: the sound is a copy
     of the sound of the line it replaces - same mixer group, same parameters - with a new name and
     wave; the wave is the one-record streamed form kl_snd.merge writes for Dead Men's single PCM
     lines), one record per clip to the .WHD. NOTHING goes into the .WAV: the clips are streamed.
  3. the .LOC leaves of the announcer's keys get Bain's text and the new sound (repoint): a plain
     key K its one leaf, a per-character key its K_C1 .. K_C9 leaves, all nine with the one clip
     (kl2 0x6b8710 looks up exactly those, re/bots_voice.md 1.1). The settings, the .prp and every
     other member are not touched; the stock sounds stay in the bank, unused by these leaves.
  'Behind an option' = this tool is the option: the source build is not changed, a build without
  Bain is the source build. --set picks the groups of TABLE.

ASSUMPTIONS (each marked where the code makes it)
  - the line choice (TABLE), by the texts only: nobody has listened to either side;
  - GAIN: a Bain clip is scaled so its RMS is that of the Dog Days line it replaces (measured through
    ffmpeg when it is installed, else TARGET_RMS), never up;
  - a single streamed PCM mono clip without a LIP block plays as a dialogue line (the 8 records of
    that shape in the Retomoto builds are Dead Men's Japanese police lines; nobody has reported
    hearing exactly those);
  - the sound / wave pools take 26 more of each (Retomoto: 4,993 / 4,842; the most that ran live is
    4,967 / 4,816, re/bots_voice.md 9);
  - the other eight languages' .LOC get Bain's English text (there is no other recording).
Payday 2's files are the owner's own on the owner's machine: the decoded clips exist only inside
the stream file and <work>, never in the repository.
"""
import collections, json, os, re, shutil, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd, kl_loc, kl_whd as W, kl_str, kl_fa, kl_voice
from kl_snd import u32, u16, cs
from kl_port_check import workdir

NUL = bytes(1)
SRC = os.path.join('build', 'rt_ai3', 'retomoto_ai3')
DST = os.path.join('build', 'v_bain', 'retomoto_bain')
SND_NAME = 'audio:dialog/kl_merge/bain/%s#sound'
WAV_NAME = 'Dialog/kl_merge/Bain/%s.wav'
RATE = 32000                                # every clip of TABLE; another rate is refused (nothing resamples)
TARGET_RMS = 4000                           # ASSUMPTION: used when ffmpeg cannot measure the replaced line
#                                             (three stock lines measured 2,466 / 4,348 / 5,335 of 32,767)
GAIN_MIN = 0.2
# Bain's radio: the first and the last sound of a pln_* / ban_* event's sequence container
# (MEASURED by pd2_events, counts printed by `events`; both mono 32 kHz PTADPCM)
RADIO = ('soundbanks/streamed/regular_vox/111416', 'soundbanks/streamed/regular_vox/229541')
# (group, settings field, Bain label) - ASSUMPTION throughout: chosen by meaning from the two
# subtitle texts (re/bain.md 3 has both texts per row and the events nothing fits).
# 'driver' = the lines the escape driver speaks (plain keys, speaker -4): the one voice of a round
#            that is not a heister's. Bain takes all of them but 'bribe accepted'.
# 'brief'  = lines a HEISTER speaks over the radio in stock that are a planner's by content:
#            briefing, reminders, loot, the end. With them the crew no longer says these itself.
TABLE = (
    ('driver', 87, 'pln_esc_fixed_van'),            # Calm down, I'm on my way          <- A van is coming in to get you out!
    ('driver', 88, 'pln_gen_bfr_05_01'),            # I'm almost there                  <- I'm sending the loot van.   (generic, by the bank)
    ('driver', 89, 'pln_fost_en_03_03'),            # I'll be there soon                <- You got enough. I'll get our man on the way.
    ('driver', 108, 'pln_esc_arrival_van'),         # Get in now!                       <- Alright the van is there. Move!
    ('driver', 109, 'pln_cr2_90_02'),               # Hurry up! Hurry up!               <- Van's ready and waiting, gang. Move it!
    ('driver', 112, 'pln_branchbank_stage1_30_any_01'),  # ... this is your last chance <- Getting pretty unpleasant out there. You guys sure you wanna stick around?
    ('driver', 113, 'pln_ko1_17_02'),               # ... or I'll leave you behind      <- Make sure you're with the driver when he bails ...
    ('driver', 114, 'pln_ko1_17_01'),               # You got 2 seconds!                <- The driver's gonna bail! Make sure you're with him.
    ('driver', 161, 'pln_esc_01_to_departure_van'),  # one minute left                  <- The van leaves in one minute. Wrap it up!
    ('driver', 162, 'pln_esc_02_to_departure'),     # 2 more minutes                    <- ... leaving in two minutes, with or without you.
    ('driver', 163, 'pln_esc_03_to_departure'),     # Only 3 minutes left               <- ... The escape vehicle is leaving in three minutes.
    ('driver', 173, 'pln_pt2_17_03'),               # Hold on - wait for the others!    <- Hold it, hold it - wait til everyone's in the car.
    ('driver', 185, 'pln_fj1_06_01'),               # Fuck! I'm leaving!                <- The van had to leave. He'll be back soon at another location.
    ('driver', 186, 'pln_fj1_06_02'),               # Too slow! Find another ride!      <- The van had to leave. He'll be back, keep your eyes out ...
    ('driver', 187, 'pln_fj1_06_01'),               # I'm getting out now!              <- (as 185)
    ('driver', 188, 'pln_dah_109_08'),              # (inside) I'm leaving!             <- Job is over guys. Time to go.
    ('driver', 189, 'pln_dah_55_01'),               # (inside) Too slow! ...            <- OK, that's it. Time to go.
    ('driver', 190, 'pln_chw_14_02'),               # (inside) I'm getting out now!     <- Time to go! Come on!
    ('brief', 17, 'pln_flt_07_03'),                 # first briefing                    <- It's time. Put on the masks and let's do this.
    ('brief', 18, 'pln_fwb_26_01'),                 # briefing                          <- Come on, crew. Get in there, grab that loot.
    ('brief', 19, 'pln_fost_brf_04_02'),            # briefing                          <- OK let's do this one.
    ('brief', 20, 'pln_framing_stage2_13_any_03'),  # briefing                          <- Get the money and clear out ASAP!
    ('brief', 127, 'pln_ed3_13_01'),                # Alright! Grab the cash.           <- Come on, guys - time to grab the cash.
    ('brief', 130, 'pln_dah_53_01'),                # We got it! Let's keep moving!     <- Great, that's everything, now get out of there!
    ('brief', 136, 'pln_fwb_54_01'),                # Just get the money.               <- Come on, we're almost done. Get the money!
    ('brief', 137, 'pln_ch1_24_02'),                # Be quick, this is gonna turn nasty <- Cops are on the way. Time is important, so hustle!
    ('brief', 169, 'pln_at1_end_02_02'),            # everybody escaped                 <- Well done gentlemen! Some hard-earned cash!
)
GROUPS = ('driver', 'brief')


# ------------------------------------------------------------------ Payday 2: labelled streams
def pd2_index(force=False, log=print):
    """-> {'streams': {crate path: [tag, channels, rate, data bytes, [labels in cue order]]},
    'labels': {label: [crate paths]}} of every stream with cue labels. Cached in
    <work>/pd2/audio/labels.json (20 s to build: the first 1,024 bytes of all 74,437 streams are read)."""
    import pd2_crate
    cache = os.path.join(pd2_crate.WORK, 'audio', 'labels.json')
    ix = pd2_crate.Index(quiet=True)
    stamp = len(ix.entries)
    if not force and os.path.isfile(cache):
        with open(cache) as f:
            d = json.load(f)
        if d.get('entries') == stamp:
            return d
    files, streams = {}, {}
    ents = sorted((e for e in ix.entries if ix.ext_name(e.ext) == 'stream' and not e.stored), key=lambda e: (e.crate, e.offset))
    for e in ents:
        f = files.get(e.crate) or files.setdefault(e.crate, open(os.path.join(ix.assets, e.crate), 'rb'))
        f.seek(e.offset)
        r = riff_labels(f.read(min(e.raw, 1024)))
        if r and r[4]:
            streams[ix.path_name(e.path)] = list(r)
    for f in files.values():
        f.close()
    labels = collections.defaultdict(list)
    for p, v in sorted(streams.items()):
        for l in v[4]:
            labels[l].append(p)
    d = dict(entries=stamp, streams=streams, labels=labels)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, 'w') as f:
        json.dump(d, f)
    log('  kl_bain: %d of %d streams carry %d subtitle labels -> %s' % (len(streams), len(ents), len(labels), cache))
    return d


def pd2_events(force=False, log=print):
    """Bain's sound events through the Wwise banks -> {'events': {event without play_: [bank, [stream
    ids of the LINES in playlist order]]}, 'radio': n, 'radio_ordered': n}. Cached in
    <work>/pd2/audio/bain_events.json (all 496 .bnk are read once).
    Bank layout, MEASURED on BKHD version 145 (495 banks; core.bnk is version 44 and skipped):
    HIRC = u32 n + n x {u8 type, u32 size, u32 id, body}. Event (4): u8 n + n x u32 action. Action
    (3): u16 type (0x0403 = play), u32 target. Sound (2): u32 plugin, u8 stream type, u32 SOURCE id
    (= the name of soundbanks/streamed/<bank>/<id>), u32 size, u8, 5 bytes, u32 bus, u32 parent.
    Random / sequence container (5): 5 bytes, u32 bus, u32 parent ... and at its end u16 n + n x
    {u32 child, u32 weight} = the playlist. Event ids = FNV-1 of the lower-case name
    (pd2_audio._fnv32); the names come from gamedata/dialogs/*.dialog. The two RADIO streams are
    taken out of the line list."""
    import pd2_crate, pd2_audio
    cache = os.path.join(pd2_crate.WORK, 'audio', 'bain_events.json')
    ix = pd2_crate.Index(quiet=True)
    stamp = len(ix.entries)
    if not force and os.path.isfile(cache):
        with open(cache) as f:
            d = json.load(f)
        if d.get('entries') == stamp:
            return d
    want = {}
    for e in ix.entries:
        if ix.ext_name(e.ext) == 'dialog':
            for m in re.findall(rb'[Pp]lay_((?:pln|ban)_[A-Za-z0-9_]+)', ix.read(e)):
                want[pd2_audio._fnv32('play_' + m.decode().lower())] = m.decode().lower()
    radio = tuple(int(p.rsplit('/', 1)[1]) for p in RADIO)
    events, n_radio, n_ordered = {}, 0, 0
    for e in ix.entries:
        if ix.ext_name(e.ext) != 'bnk':
            continue
        d, o, hirc, ver = ix.read(e), 0, None, None
        while o + 8 <= len(d):
            cid, sz = d[o:o + 4], u32(d, o + 4)
            if cid == b'BKHD':
                ver = u32(d, o + 8)
            elif cid == b'HIRC':
                hirc = o + 8
            o += 8 + sz
        if hirc is None or ver != 145:
            continue
        objs, q = {}, hirc + 4
        for _i in range(u32(d, hirc)):
            objs[u32(d, q + 5)] = (d[q], d[q + 9:q + 5 + u32(d, q + 1)])
            q += 5 + u32(d, q + 1)
        kids = collections.defaultdict(list)
        for oid, (t, b) in objs.items():
            if t == 2 and len(b) >= 27:
                kids[u32(b, 23)].append(oid)
            elif t in (5, 6, 7) and len(b) >= 13:
                kids[u32(b, 9)].append(oid)

        def sounds(oid, depth=0):
            t, b = objs[oid]
            if t == 2:
                return [u32(b, 5)]
            order = kids.get(oid, [])
            n = len(order)
            if t == 5 and n and len(b) >= 8 * n + 2 and u16(b, len(b) - 8 * n - 2) == n:
                pl = [u32(b, len(b) - 8 * n + 8 * i) for i in range(n)]
                if set(pl) == set(order):
                    order = pl
            return [x for k in order for x in sounds(k, depth + 1)] if depth < 8 else []
        bank = ix.path_name(e.path)
        for oid, (t, b) in objs.items():
            if t != 4 or oid not in want or not b:
                continue
            src = []
            for i in range(b[0]):
                a = objs.get(u32(b, 1 + 4 * i)) if 5 + 4 * i <= len(b) else None
                if a and a[0] == 3 and len(a[1]) >= 6 and u16(a[1], 0) == 0x0403 and u32(a[1], 2) in objs:
                    src += sounds(u32(a[1], 2))
            if not src:
                continue
            if radio[0] in src and radio[1] in src:
                n_radio += 1
                n_ordered += src[0] == radio[0] and src[-1] == radio[1]
            events.setdefault(want[oid], [bank, [x for x in src if x not in radio]])
    d = dict(entries=stamp, names=len(want), events=events, radio=n_radio, radio_ordered=n_ordered)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, 'w') as f:
        json.dump(d, f)
    log('  kl_bain: %d of Bain\'s %d dialogue events found in the banks; %d hold both radio clicks, %d as first and last sound -> %s' % (
        len(events), len(want), n_radio, n_ordered, cache))
    return d


def event_line(label):
    """A line WITHOUT a label, named '<event>_<nn>' like its subtitle: the nn-th line stream of the
    event's playlist. exact = the event has one line stream; else ASSUMPTION (playlist order = the
    subtitle number: true for 3,702 of 4,980 labelled events with two or more lines, 74 %).
    -> (crate path, exact) or None."""
    import pd2_crate
    m = re.match(r'(.+)_(\d\d)$', label.lower())
    ev = pd2_events()['events'].get(m.group(1)) if m else None
    if not ev or not 1 <= int(m.group(2)) <= len(ev[1]):
        return None
    path = 'soundbanks/streamed/%s/%d' % (ev[0].rsplit('/', 1)[1], ev[1][int(m.group(2)) - 1])
    return (path, len(ev[1]) == 1) if pd2_crate.Index(quiet=True).get(path, 'stream') else None


def riff_labels(h):
    """(tag, channels, rate, data bytes, [labels in cue order]) from the head of a .wem, None if it is
    no RIFF WAVE. The chunks stand before `data` (fmt, hash, cue, LIST, junk: re/pd2_audio.md)."""
    if h[:4] != b'RIFF' or h[8:12] != b'WAVE':
        return None
    o, fmt, pos, lab, size = 12, None, {}, [], 0
    while o + 8 <= len(h):
        cid, sz = h[o:o + 4], u32(h, o + 4)
        body = h[o + 8:o + 8 + sz]
        if cid == b'fmt ':
            fmt = struct.unpack_from('<HHI', body)
        elif cid == b'cue ':
            for i in range(u32(body, 0)):
                if 4 + 24 * i + 8 <= len(body):
                    pos[u32(body, 4 + 24 * i)] = u32(body, 8 + 24 * i)
        elif cid == b'LIST':
            p = 4
            while p + 12 <= len(body):
                c2, s2 = body[p:p + 4], u32(body, p + 4)
                if c2 == b'labl':
                    lab.append((u32(body, p + 8), body[p + 12:p + 8 + s2].split(NUL)[0].decode('latin-1')))
                p += 8 + s2 + (s2 & 1)
        elif cid == b'data':
            size = sz
            break
        o += 8 + sz + (sz & 1)
    if fmt is None:
        return None
    return fmt[0], fmt[1], fmt[2], size, [l for _i, l in sorted(lab, key=lambda x: (pos.get(x[0], 0), x[0]))]


_SUBS = None
def subtitle(label):
    """English subtitle of a label, '' when strings/subtitles.strings has none."""
    global _SUBS
    import pd2_crate, pd2_audio
    if _SUBS is None:
        ix = pd2_crate.Index(quiet=True)
        d = ix.read(ix.get('strings/subtitles', 'strings', 0))
        _SUBS = (d, pd2_audio._strings_table(d))
    d, tab = _SUBS
    o = tab.get(pd2_crate.hash64(label.lower()))
    return d[o:d.index(NUL, o)].decode('utf-8', 'replace').strip() if o else ''


def bain_line(label, idx=None):
    """-> dict(label, path, text, rate, channels, seconds) of the stream that carries `label`: the
    first by path when several do. text = the subtitles of ALL the stream's labels in cue order (a
    stream with two cues is two subtitle lines spoken in one clip)."""
    idx = idx or pd2_index()
    paths, exact = idx['labels'].get(label), True
    if paths:
        tag, ch, rate, size, labs = idx['streams'][paths[0]]
    else:                                               # no label: through the bank (a generic line)
        import pd2_crate
        ev = event_line(label)
        if not ev:
            raise KeyError('no Payday 2 stream carries the label %s, and no event of the banks has that line' % label)
        ix = pd2_crate.Index(quiet=True)
        e = ix.get(ev[0], 'stream')
        with open(os.path.join(ix.assets, e.crate), 'rb') as f:
            f.seek(e.offset)
            tag, ch, rate, size, _l = riff_labels(f.read(min(e.raw, 1024)))
        paths, labs, exact = [ev[0]], [label], ev[1]
    if tag != 0x8311:
        raise ValueError('%s: tag %#x is not PTADPCM (pd2_audio decodes nothing else of the voice streams)' % (label, tag))
    labs = list(dict.fromkeys(labs))                    # one label on two cues (pln_ko1_17_01): one line
    return dict(label=label, path=paths[0], text=' '.join(t for t in (subtitle(l) for l in labs) if t), rate=rate, channels=ch,
                seconds=size // (36 * ch) * 64 / rate, streams=len(paths), exact=exact)


def decode(line):
    """The line's samples: list of int16, mono (a stereo stream is refused: none is in TABLE)."""
    import pd2_crate, pd2_audio
    ix = pd2_crate.Index(quiet=True)
    st = pd2_audio.Stream(ix.read(ix.get(line['path'], 'stream')), line['label'])
    if st.channels != 1 or st.rate != RATE:
        raise ValueError('%s: %d channels at %d Hz; only mono %d Hz clips are taken (nothing here resamples)' % (
            line['label'], st.channels, st.rate, RATE))
    return st.decode()[0]


_RADIO = None
def radio_clicks():
    """(opening, closing): the samples of Bain's two radio clicks."""
    global _RADIO
    if _RADIO is None:
        _RADIO = tuple(decode(dict(path=p, label=p.rsplit('/', 1)[1])) for p in RADIO)
    return _RADIO


def rms(s):
    return (sum(x * x for x in s) / len(s)) ** 0.5 if s else 0.0


def scaled(s, target, radio=False):
    """ASSUMPTION (GAIN): the clip scaled so that its RMS is `target`, never louder than it is and
    never below GAIN_MIN of itself. radio: between the two radio clicks, which get the line's gain
    (ASSUMPTION: Payday 2 plays the three sounds of the sequence at one volume; the container's
    volume fields were not read). -> (bytes of 16-bit PCM, gain)"""
    r = rms(s)
    g = max(GAIN_MIN, min(1.0, target / r)) if r else 1.0
    if radio:
        a, z = radio_clicks()
        s = list(a) + list(s) + list(z)
    return struct.pack('<%dh' % len(s), *(max(-32768, min(32767, int(round(x * g)))) for x in s)), g


def vorbis_rms(str_file, off, size):
    """RMS of a stock Vorbis clip of the stream file (an Ogg stream from `off`), through ffmpeg.
    None when ffmpeg is not there or does not take it."""
    try:
        str_file.seek(off)
        d = str_file.read(size)
        if d[:4] != b'OggS':
            return None
        r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'ogg', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', 'pipe:1'],
                           input=d, capture_output=True, timeout=60)
        n = len(r.stdout) // 2
        return rms(struct.unpack('<%dh' % n, r.stdout[:2 * n])) if n else None
    except (OSError, subprocess.SubprocessError):
        return None


# ------------------------------------------------------------------ the stream file
def stream_add(base_path, out_path, clips, log=print):
    """out_path = base_path + clips ([(name, bytes of 16-bit PCM, rate, channels)]), each a block of
    its own without a LIP block, codec 2. The base's bytes below its tables keep their place (no
    clip of the base moves); one fresh format table, name table and sorted index follow the new
    blocks, as kl_str.merge writes them. A clip the base already holds under the same name with
    the same bytes is not added again. -> {name: (offset, bytes)}. Also copies the base's
    .map.json (the Dead Men offsets it lists are unchanged) and writes <out>.bain.json."""
    base = kl_str.Stream(base_path)
    if base.game != 'dd':
        raise ValueError('stream_add: the base must be a Dog Days stream file')
    if os.path.abspath(out_path).lower() == os.path.abspath(base_path).lower():
        raise ValueError('stream_add: the output may not be the base')
    cut = base.table_start()
    last = max(base.blocks)
    if cut % kl_str.ALIGN or cut <= last or cut < last + base.audio(last):
        raise ValueError('stream_add: the base\'s tables do not start behind its last block on a multiple of 0x100')
    placed, new = {}, []
    for name, pcm, rate, ch in clips:
        c = base.find(name)
        if c is not None:
            base.f.seek(c.offset)
            if c.codec != kl_str.PCM or c.size != len(pcm) or base.f.read(c.size) != pcm:
                raise ValueError('stream_add: the base holds another clip named %s' % name)
            placed[name] = (c.offset, c.size)
        else:
            new.append((name, pcm, rate, ch))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    all_clips = sorted(base.clips, key=lambda c: c.id)
    with open(out_path, 'wb') as out:
        base.f.seek(0)
        left = cut
        while left:
            chunk = base.f.read(min(left, 32 << 20))
            out.write(chunk); left -= len(chunk)
        for name, pcm, rate, ch in new:
            out.write(bytes(-out.tell() % kl_str.ALIGN))
            c = kl_str.Clip()
            c.id, c.offset, c.size, c.name, c.key, c.lip, c.layer = len(all_clips), out.tell(), len(pcm), name, kl_str.name_key(name), 0, 0
            c.codec, c.samples, c.channels, c.rate, c.bits = kl_str.PCM, len(pcm) // (2 * ch), ch, rate, 16
            # a PCM format entry: codec, samples, channels, rate, bits, 8 bytes the build tool left
            # uninitialised (zero here), frame bytes
            c.fmt = struct.pack('<5I', c.codec, c.samples, ch, rate, 16) + bytes(8) + struct.pack('<I', 2 * ch)
            c.fmt_at = c.name_at = 0
            out.write(pcm)
            all_clips.append(c); placed[name] = (c.offset, c.size)
        out.write(bytes(-out.tell() % kl_str.ALIGN))
        for c in all_clips:
            c.fmt_at = out.tell(); out.write(c.fmt)
        for c in all_clips:
            c.name_at = out.tell(); out.write(c.name.encode('latin1') + NUL)
        index = out.tell()
        for c in sorted(all_clips, key=lambda c: (c.key, c.id)):
            out.write(c.record())
        size = out.tell()
        out.seek(0)
        h = bytearray(base.head)
        struct.pack_into('<QI', h, 0x18, index, len(all_clips))
        out.write(h)
    if os.path.isfile(base_path + '.map.json'):
        shutil.copyfile(base_path + '.map.json', out_path + '.map.json')
    with open(out_path + '.bain.json', 'w') as f:
        json.dump(dict(base=base_path, base_size=base.size, base_tables=cut, clips={n: list(v) for n, v in sorted(placed.items())}), f, indent=1)
    log('  kl_bain: %s = %s + %d clips (%d were there), %d bytes behind %#x; %d -> %d bytes (+%.2f MB), %d clips' % (
        out_path, os.path.basename(base_path), len(new), len(clips) - len(new), sum(len(c[1]) for c in new), cut,
        base.size, size, (size - base.size) / 2 ** 20, len(all_clips)))
    base.close()
    return placed


def stream_verify(out_path, base_path, clips, log=print):
    """Re-read stream_add's file: every byte accounted for (kl_str.Stream.account), the base's
    bytes below its tables identical, every base clip in the index as it was, every new clip
    there with its bytes. -> [problems]"""
    import hashlib
    m, base = kl_str.Stream(out_path), kl_str.Stream(base_path)
    by, bad = m.account()
    cut = base.table_start()
    if m.build != base.build or m.head[:0x18] != base.head[:0x18] or m.head[0x24:] != base.head[0x24:]:
        bad.append('header differs from the base beyond index offset and count')
    ha, hb = hashlib.sha1(), hashlib.sha1()
    for f, h in ((m.f, ha), (base.f, hb)):
        f.seek(0x38); left = cut - 0x38
        while left:
            chunk = f.read(min(left, 32 << 20)); h.update(chunk); left -= len(chunk)
    if ha.digest() != hb.digest():
        bad.append('bytes 0x38..%#x differ from the base' % cut)
    moved = 0
    for c in base.clips:
        if not any((n.offset, n.size, n.fmt, n.lip, n.layer, n.id) == (c.offset, c.size, c.fmt, c.lip, c.layer, c.id) for n in m.blocks.get(c.offset, ())
                   if n.name == c.name):
            moved += 1
    if moved:
        bad.append('%d clips of the base moved or changed' % moved)
    for name, pcm, rate, ch in clips:
        c = m.find(name)
        if c is None or (c.codec, c.channels, c.rate, c.bits, c.size, c.samples) != (kl_str.PCM, ch, rate, 16, len(pcm), len(pcm) // (2 * ch)):
            bad.append('clip %s is not in the index as written' % name); continue
        m.f.seek(c.offset)
        if m.f.read(c.size) != pcm or m.has_lip(c.offset):
            bad.append('clip %s: other bytes at %#x' % (name, c.offset))
    log('  kl_bain: verify %s: %s; %d base clips, %d Bain clips; %d problems' % (os.path.basename(out_path), dict(by), len(base.clips), len(clips), len(bad)))
    m.close(); base.close()
    return bad


class kl_str_open:
    """`with` around kl_str.Stream (it has close() only)."""

    def __init__(self, path):
        self.m = kl_str.Stream(path)

    def __enter__(self):
        return self.m

    def __exit__(self, *_a):
        self.m.close()


# ------------------------------------------------------------------ the level's bank
def bank_add(S, items):
    """Append one sound + one wave per item to the walked Dog Days bank S.
    items: [(label, template sound offset, .WHD offset of the clip's record, seconds)].
    The sound = the template's 0x34 bytes (cone, flags, the SAME parameter list: the form
    kl_snd.merge gives its silent sound) with its own name and wave; the wave = one streamed
    record: {4, cd fill, file name*, u16 1 + cd fill, 0, .WHD offset, f32 seconds, 0} - what
    kl_snd.merge writes for a Dead Men single PCM stream line (8 in the Retomoto builds).
    Every byte below the first type table keeps its place; type tables and parameter tables (one
    entry per use) and the trailer are written anew, as kl_snd.merge step 4.
    -> (new .SND, {label: sound offset})"""
    bad = S.clean()
    if bad:
        raise ValueError('bank: ' + '; '.join(bad))
    b = S.b
    out, made, newtab, newpar = bytearray(b[:S.cut]), {}, collections.defaultdict(list), collections.defaultdict(list)
    def put(data):
        out.extend(bytes(-len(out) % 16)); at = len(out); out.extend(data)
        return at
    for label, tmpl, whd_at, secs in items:
        if S.kind.get(tmpl) != 1:
            raise ValueError('bank_add: %#x is no sound of the bank' % tmpl)
        name = put((SND_NAME % label.lower()).encode('latin1') + NUL)
        fname = put((WAV_NAME % label).encode('latin1') + NUL)
        wave = put(struct.pack('<I', 4) + b'\xcd' * 4 + struct.pack('<I', fname) + b'\x01\0\xcd\xcd' + bytes(4) +
                   struct.pack('<If', whd_at, secs) + bytes(4))
        body = bytearray(b[tmpl:tmpl + 0x34])
        struct.pack_into('<I', body, 8, name)
        struct.pack_into('<I', body, 0x14, wave)
        made[label] = put(bytes(body))
        newtab[1].append(made[label]); newtab[4].append(wave)
        if u32(b, tmpl + 0x10):
            for q in struct.unpack_from('<%dI' % u16(b, tmpl + 0xc), b, u32(b, tmpl + 0x10)):
                newpar[u32(b, q)].append(q)
    counts, tabs = list(S.counts), list(S.tabs)
    for t in range(kl_snd.NTYPES):
        add = newtab.get(t + 1, [])
        if S.counts[t] or add:
            out.extend(bytes(-len(out) % 16)); tabs[t] = len(out); counts[t] = S.counts[t] + len(add)
            out.extend(b[S.tabs[t]:S.tabs[t] + 4 * S.counts[t]] + struct.pack('<%dI' % len(add), *add))
    pairs = []
    for k in range(S.nparam):
        n, p = struct.unpack_from('<2I', b, S.P + 8 * k)
        add = newpar.get(k + 1, [])
        if n or add:
            out.extend(bytes(-len(out) % 16)); pairs += [n + len(add), len(out)]
            out.extend(b[p:p + 4 * n] + struct.pack('<%dI' % len(add), *add))
        else:
            pairs += [0, 0]
    out.extend(bytes(-len(out) % 16))
    T, tr = len(out), bytearray(b[S.T:])
    struct.pack_into('<%dI' % kl_snd.NTYPES, tr, S.H - S.T + 16, *counts)
    struct.pack_into('<%dI' % kl_snd.NTYPES, tr, S.H - S.T + 16 + 4 * kl_snd.NTYPES, *tabs)
    struct.pack_into('<%dI' % len(pairs), tr, S.P - S.T, *pairs)
    out.extend(tr); struct.pack_into('<2I', out, 0, T, len(out))
    return bytes(out), made


def whd_record(size, rate, ch, off):
    """Dog Days .WHD fields of a single streamed PCM clip at `off` of PC_Def.str: the shape of the
    Dead Men single PCM stream records the Retomoto builds carry (fmt 0x00800001, 16 bits, block
    = frame bytes, 'samples per block' and the two junk dwords = fill, then 0 and 0x10), without
    the lip-sync word: the clip has no LIP block."""
    return dict(name=0, fmt=W.STREAMED | 1, rate=rate, bits=16, pcm=size, size=size, ch=ch, off=off & 0xffffffff, offhi=off >> 32,
                samples=size // (2 * ch), block=2 * ch, spb=0xcdcdcdcd, lip=0, x34=0xcdcdcdcd, x38=0xcdcdcdcd, x3c=0, x40=0x10)


# ------------------------------------------------------------------ the .LOC
def find_leaf(kids, key):
    """The leaf node of key 'A/B/C' (case-blind, as the keys are compared everywhere here), or None."""
    tab = kids
    part = key.strip('/').lower().split('/')
    for i, p in enumerate(part):
        k = next((k for k in tab if k.name.lower() == p.encode('latin1')), None)
        if k is None or (k.kids is None) != (i == len(part) - 1):
            return None
        tab = k.kids
    return k


def repoint(loc, edits):
    """A .LOC with the leaves of `edits` ({key: (text bytes, sound id)}) rewritten in Dog Days'
    leaf form (text, the id, the id). A key the file lacks is left out. -> (bytes, leaves changed)"""
    t = kl_loc.parse(loc)
    if t is None:
        return loc, 0                                   # the Dutch stub
    n = 0
    for key, (text, sid) in edits.items():
        k = find_leaf(t, key)
        if k is not None:
            new = kl_loc.leaf(k.name, text, sid)
            k.flags, k.raw = new.flags, new.raw
            n += 1
    return kl_loc.build(t), n


# ------------------------------------------------------------------ the build
def plan(src_zip, groups=GROUPS, idx=None):
    """What a build gets: [dict(group, field, flag, key, leaves=[.LOC keys to re-point], template =
    sound of the first of them, old = its English text, bain = bain_line())], and [notes] for the
    rows that are left out (an empty field, a key without a leaf or sound)."""
    sc, S, recs, leaves = kl_voice.load(src_zip)
    with zipfile.ZipFile(src_zip) as zf:
        eng = next(n for n in zf.namelist() if n.lower().endswith('_mainenglish.loc'))
        text = {p.lower(): (kl_loc.fields(k)[0] or b'').decode('latin1') for p, k in kl_loc.leaves(kl_loc.parse(zf.read(eng)))}
    st = kl_voice.settings(sc)
    if len(st) != 1:
        raise ValueError('%s: %d Fragile Alliance settings objects' % (src_zip, len(st)))
    v, flags = st[0][2], kl_voice.line_fields()
    idx = idx or pd2_index()
    rows, notes, used = [], [], collections.defaultdict(list)
    for f, (flag, _prio) in flags.items():
        if v[f]:
            used[v[f].strip('/').lower()].append(f)
    for group, f, label in TABLE:
        if group not in groups:
            continue
        key = (v[f] or '').strip('/')
        if not key:
            notes.append('field %d is empty in this build: %s not placed' % (f, label)); continue
        flag = flags[f][0]
        names = ['%s_c%d' % (key.lower(), i) for i in range(1, kl_voice.VARIANTS + 1)] if flag else [key.lower()]
        names = [n for n in names if leaves.get(n) and S.kind.get(leaves[n]) == 1]
        if not names:
            notes.append('field %d %s: no leaf with a sound: %s not placed' % (f, key, label)); continue
        rows.append(dict(group=group, field=f, flag=flag, key=key, leaves=names, template=leaves[names[0]], old=text.get(names[0], ''),
                         bain=bain_line(label, idx), shared=[x for x in used[key.lower()] if x != f]))
    chosen = {r['field'] for r in rows}
    for r in rows:
        other = [x for x in r['shared'] if x not in chosen]
        if other:
            notes.append('field %d %s: the key is also in field(s) %s, which get Bain\'s line with it' % (r['field'], r['key'], other))
    return rows, notes, (sc, S, recs, leaves)


def budget(folder):
    """The four blocks a level reads in one piece: {'.prm' ...: bytes}."""
    z = next(os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('_main.zip'))
    out = {}
    with zipfile.ZipFile(z) as zf:
        for i in zf.infolist():
            e = os.path.splitext(i.filename)[1].lower()
            if e in ('.prm', '.anm', '.fxc'):
                out[e] = out.get(e, 0) + i.file_size
    out['.wav'] = os.path.getsize(z[:-4] + '.WAV')
    return out


def build(src=None, dst=None, groups=GROUPS, stream_base=None, log=print, radio=True):
    """dst = a copy of the finished build src with Bain on the announcer's lines; <dst>/../PC_Def.str
    = the stream file it needs (stream_base + the clips). -> dict(problems=[...], ...). Writes
    <dst>/bain.json (the mapping with both texts) and bain.txt (the log)."""
    w = workdir()
    src, dst = src or os.path.join(w, SRC), dst or os.path.join(w, DST)
    stream_base = stream_base or kl_snd.stream_file('merged')
    if os.path.abspath(dst).lower().startswith(os.path.abspath(kl_snd.game_dir('dd')).lower()):
        raise ValueError('kl_bain writes build folders only, never the game\'s')
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    zname = next(f for f in os.listdir(src) if f.lower().endswith('_main.zip'))
    src_zip, stem = os.path.join(src, zname), zname[:-4]
    rows, notes, (_sc, S, recs, _leaves) = plan(src_zip, groups)
    say('kl_bain: %s -> %s; groups %s; radio clicks %s; %d lines, %d distinct Bain clips' % (
        src, dst, ','.join(groups), 'on' if radio else 'off', len(rows), len({r['bain']['label'] for r in rows})))
    for n in notes:
        say('  NOTE %s' % n)
    # 1. the clips, each at the loudness of the first line it replaces
    clips, gain = {}, {}
    with open(stream_base, 'rb') as sf:
        for r in rows:
            lab = r['bain']['label']
            if lab in clips:
                continue
            wv = u32(S.b, r['template'] + 0x14)
            f = recs.get(u32(S.b, wv + 0x14)) if wv and wv < S.T else None
            ref = None
            if f and f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE and f['fmt'] & 0xffff == 0x1000 and not f['fmt'] >> 24:
                ref = vorbis_rms(sf, f['off'] | (f['offhi'] << 32), f['size'])
            s = decode(r['bain'])
            pcm, g = scaled(s, ref or TARGET_RMS, radio)
            clips[lab] = pcm
            gain[lab] = dict(rms=round(rms(s)), target=round(ref or TARGET_RMS), measured=ref is not None, gain=round(g, 3))
    order = sorted(clips)
    str_out = os.path.join(os.path.dirname(os.path.abspath(dst)), 'PC_Def.str')
    str_clips = [(WAV_NAME % l, clips[l], RATE, 1) for l in order]
    problems = None
    if os.path.isfile(str_out):                         # a file of an earlier run that holds exactly these clips is kept
        try:
            problems = stream_verify(str_out, stream_base, str_clips, lambda *_a: None)
        except (ValueError, OSError, struct.error):
            problems = ['unreadable']
    if problems == []:
        with kl_str_open(str_out) as m:
            placed = {n: (m.find(n).offset, m.find(n).size) for n, _p, _r, _c in str_clips}
        say('  kl_bain: %s holds the %d clips already (verified against the base): kept' % (str_out, len(str_clips)))
    else:
        placed = stream_add(stream_base, str_out, str_clips, say)
    problems = ['stream file: ' + x for x in stream_verify(str_out, stream_base, str_clips, say)]
    # 2. the bank
    whd0, wav0 = kl_snd.read(os.path.join(src, stem + '.WHD')), kl_snd.read(os.path.join(src, stem + '.WAV'))
    writer = W.Writer(whd0, wav0)
    tmpl = {}
    for r in rows:
        tmpl.setdefault(r['bain']['label'], r['template'])
    items = []
    for l in order:
        off, size = placed[WAV_NAME % l]
        items.append((l, tmpl[l], writer.add((WAV_NAME % l).encode('latin1'), whd_record(size, RATE, 1, off)), size / 2 / RATE))
    whd, wav = writer.finish()
    ls_path = os.path.join(src, stem + '_LS.SND')
    ls0 = kl_snd.read(ls_path) if os.path.isfile(ls_path) else b''
    base = kl_snd.Snd('dd', S.b, ls0).walk()             # with the loading-sound bank: its strings live in this image
    snd, made = bank_add(base, items)
    ls = kl_snd.ls_bank(ls0, u32(snd, 0))
    bad, n = kl_snd.verify(base, snd, whd, wav, ls)
    problems += ['bank: ' + x for x in bad]
    if wav != wav0:
        problems.append('.WAV changed (%d -> %d bytes): no clip of this tool is held in memory' % (len(wav0), len(wav)))
    # 3. the .LOC leaves
    edits = {}
    for r in rows:
        for name in r['leaves']:
            edits[name] = (r['bain']['text'].encode('latin1', 'replace'), made[r['bain']['label']])
    os.makedirs(dst, exist_ok=True)
    changed, locn = [], collections.Counter()
    with zipfile.ZipFile(src_zip) as zi, zipfile.ZipFile(os.path.join(dst, zname), 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zo:
        for info in zi.infolist():
            data = zi.read(info.filename)
            low = info.filename.lower()
            if low.endswith('_main.snd'):
                data = snd; changed.append(info.filename)
            elif low.endswith('.loc'):
                new, k = repoint(data, edits)
                locn[k] += 1
                if new != data:
                    data = new; changed.append(info.filename)
            ni = zipfile.ZipInfo(info.filename, info.date_time)
            ni.external_attr = info.external_attr
            zo.writestr(ni, data, info.compress_type, 1)
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p) and f != zname and f not in ('bain.json', 'bain.txt'):
            shutil.copyfile(p, os.path.join(dst, f))
    for suffix, data in (('.WHD', whd), ('.WAV', wav)) + ((('_LS.SND', ls),) if ls else ()):
        with open(os.path.join(dst, stem + suffix), 'wb') as f:
            f.write(data)
    say('  bank: sounds %d -> %d, waves %d -> %d, .SND %d -> %d bytes, .WHD %d -> %d (%d records added), .WAV %d -> %d' % (
        S.counts[0], n['table: sound'], S.counts[3], n['table: wave'], len(S.b), len(snd), len(whd0), len(whd), writer.added, len(wav0), len(wav)))
    say('  .LOC: %d leaves to re-point; files by leaves changed: %s; members rewritten: %d (%s)' % (
        len(edits), dict(locn), len(changed), ', '.join(os.path.splitext(c)[1] for c in changed)))
    problems += check(dst, str_out, say, rows=rows)
    b0, b1 = budget(src), budget(dst)
    say('  budget (bytes, before -> after): ' + ', '.join('%s %d -> %d' % (k, b0[k], b1[k]) for k in ('.prm', '.anm', '.fxc', '.wav')))
    for r in rows:
        g = gain[r['bain']['label']]
        say('  %-6s %3d %-52s %-30s x%.2f%s%s | %s  <-  %s' % (r['group'], r['field'], r['key'].replace('Multiplayer/', ''), r['bain']['label'],
                                                          g['gain'], '' if g['measured'] else '*', '' if r['bain']['exact'] else ' ~', r['old'], r['bain']['text']))
    say('kl_bain: %d problems' % len(problems))
    for x in problems:
        say('  PROBLEM %s' % x)
    res = dict(src=src, dst=dst, stream=str_out, stream_base=stream_base, groups=list(groups), radio=radio, problems=problems, notes=notes,
               budget=dict(before=b0, after=b1), gain=gain,
               lines=[dict(group=r['group'], field=r['field'], flag=r['flag'], key=r['key'], leaves=r['leaves'], dog_days=r['old'],
                           bain=r['bain']['label'], text=r['bain']['text'], exact=r['bain']['exact'], seconds=round(r['bain']['seconds'], 2), stream=r['bain']['path'],
                           clip=WAV_NAME % r['bain']['label'], offset=placed[WAV_NAME % r['bain']['label']][0]) for r in rows])
    with open(os.path.join(dst, 'bain.json'), 'w') as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(dst, 'bain.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return res


def check(dst, str_path=None, log=print, rows=None):
    """The checks on a build with Bain: the bank walks clean, every wave hits a .WHD record, every
    streamed PC_Def.str record of the .WHD is a block of str_path with the bank's build id, every
    Bain record names a PCM clip of exactly its size / rate / channels, every Bain sound is named by
    a .LOC leaf in all eight real languages, kl_voice.heisters reports no CRASH and no SILENT the
    build did not have, kl_fa.check has no new finding (rows: the plan, when build() calls).
    -> [problems]"""
    zname = next(f for f in os.listdir(dst) if f.lower().endswith('_main.zip'))
    z, stem = os.path.join(dst, zname), zname[:-4]
    str_path = str_path or os.path.join(os.path.dirname(os.path.abspath(dst)), 'PC_Def.str')
    bad = []
    with zipfile.ZipFile(z) as zf:
        if zf.testzip():
            bad.append('archive: a member fails its CRC')
        snd = next(zf.read(n) for n in zf.namelist() if n.lower().endswith('_main.snd'))
        locs = {n: zf.read(n) for n in zf.namelist() if n.lower().endswith('.loc')}
    whd, wav = kl_snd.read(os.path.join(dst, stem + '.WHD')), kl_snd.read(os.path.join(dst, stem + '.WAV'))
    ls = kl_snd.read(os.path.join(dst, stem + '_LS.SND')) if os.path.isfile(os.path.join(dst, stem + '_LS.SND')) else b''
    S = kl_snd.Snd('dd', snd, ls).walk()
    bad += ['bank: ' + x for x in S.clean()]
    if ls and u32(ls, 0) != S.T:
        bad.append('_LS.SND does not name the bank\'s trailer')
    recs = W.records('dd', whd)
    m = kl_str.Stream(str_path)
    if m.build != S.build:
        bad.append('stream file build id %x, the bank\'s %x' % (m.build, S.build))
    miss = sum(1 for f in recs.values() if f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE and (f['off'] | (f['offhi'] << 32)) not in m.blocks)
    if miss:
        bad.append('%d streamed records of the .WHD are no block of %s' % (miss, str_path))
    mine = {o: cs(S.b, u32(S.b, o + 8)) for o in S.tables[1] if o < S.T and cs(S.b, u32(S.b, o + 8)).startswith(SND_NAME.split('%')[0].encode())}
    for o, name in mine.items():
        wv = u32(S.b, o + 0x14)
        f = recs.get(u32(S.b, wv + 0x14)) if S.kind.get(wv) == 4 else None
        c = m.find(cs(S.b, u32(S.b, wv + 8)).decode('latin1')) if f else None
        if c is None or (c.offset, c.size, c.rate, c.channels, c.codec, c.layer) != (f['off'] | (f['offhi'] << 32), f['size'], f['rate'], f['ch'], kl_str.PCM, 0) \
                or f['fmt'] != W.STREAMED | 1 or f['bits'] != 16 or f['samples'] * 2 * f['ch'] != f['size'] or f['lip']:
            bad.append('%s: its record is not the PCM clip of that name in the stream file' % name.decode('latin1'))
        elif abs(struct.unpack_from('<f', S.b, wv + 0x18)[0] - c.samples / c.rate) > 1e-3:
            bad.append('%s: the wave\'s length is not the clip\'s' % name.decode('latin1'))
    named = collections.Counter()
    for n, d in locs.items():
        t = kl_loc.parse(d)
        if t is None:
            continue
        ids = collections.Counter(kl_loc.fields(k)[2] for _p, k in kl_loc.leaves(t))
        named[sum(1 for o in mine if ids[o])] += 1
        if kl_loc.build(t) != d:
            bad.append('%s does not rebuild to itself' % n)
    if set(named) != {len(mine)}:
        bad.append('Bain sounds named by a leaf, per .LOC file: %s (there are %d)' % (dict(named), len(mine)))
    h = kl_voice.heisters(z, None, None)
    sev = collections.Counter(s for s, _t in h['findings'])
    if sev['CRASH']:
        bad.append('kl_voice.heisters: %d CRASH findings' % sev['CRASH'])
    silent = [t for s, t in h['findings'] if s == 'SILENT' and 'OnlineSpeakPlayer' not in t]
    if silent:
        bad.append('kl_voice.heisters: SILENT %s' % '; '.join(silent))
    if rows is not None:
        want = {r['bain']['label'].lower() for r in rows}
        got = {n.decode('latin1').split('/')[-1].split('#')[0] for n in mine.values()}
        if want != got:
            bad.append('Bain sounds in the bank %d, planned %d' % (len(got), len(want)))
    log('  check %s: %d Bain sounds, each named by a leaf in %s .LOC files; %d streamed records, %d not in %s; heisters: plain %s, '
        'per-character pairs %s, findings %s; %d problems' % (
            dst, len(mine), dict(named), sum(1 for f in recs.values() if f['fmt'] & W.STREAMED), miss, os.path.basename(str_path),
            h['plain keys (flag 0) by clip'], h['  key x heister pairs by clip'], dict(sev) or 'none', len(bad)))
    m.close()
    return bad


def fa_findings(folder):
    """kl_fa.check's findings of a build as strings (compared before / after by main)."""
    z = next(os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('_main.zip'))
    return sorted(str(f) for f in kl_fa.report(z, log=lambda *_a: None))


# ------------------------------------------------------------------ command line
def main(a):
    w = workdir()
    opt = {a[i]: a[i + 1] for i in range(len(a) - 1) if a[i].startswith('--')}
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or not a[i - 1].startswith('--'))]
    if not pos:
        print(__doc__); return 0
    cmd, pos = pos[0], pos[1:]
    if cmd == 'lines':
        rows, notes, _x = plan(os.path.join(pos[0] if pos else os.path.join(w, SRC), 'F01_Main.zip'))
        for r in rows:
            b = r['bain']
            print('%-6s %3d %s %-48s | %s\n%14s %-46s | %s  (%.1f s, %s)' % (r['group'], r['field'], 'C' if r['flag'] else ' ', r['key'], r['old'],
                                                                       '', b['label'], b['text'], b['seconds'], b['path']))
        for n in notes:
            print('NOTE', n)
        return 0
    if cmd == 'find':
        idx = pd2_index()
        t = ' '.join(pos).lower()
        for l in sorted(idx['labels']):
            if l.startswith(('pln_', 'ban_')):
                s = subtitle(l)
                if t in s.lower():
                    v = idx['streams'][idx['labels'][l][0]]
                    print('%-40s %5d Hz %d ch %5.1f s | %s' % (l, v[2], v[1], v[3] // (36 * v[1]) * 64 / v[2], s))
        for ev, (bank, ids) in sorted(pd2_events()['events'].items()):     # lines without a label: by the bank
            for i in range(len(ids)):
                l = '%s_%02d' % (ev, i + 1)
                s = subtitle(l)
                if l not in idx['labels'] and s and t in s.lower():
                    print('%-40s %s (%s, %d line streams) | %s' % (l, 'bank, exact' if len(ids) == 1 else 'bank, WHICH stream is assumed', bank.rsplit('/', 1)[1], len(ids), s))
        return 0
    if cmd == 'events':
        import pd2_crate
        d, idx = pd2_events('--force' in a), pd2_index()
        ix = pd2_crate.Index(quiet=True)
        tags = collections.Counter()
        for ev, (bank, ids) in sorted(d['events'].items()):
            p = ['soundbanks/streamed/%s/%d' % (bank.rsplit('/', 1)[1], x) for x in ids]
            if any(q in idx['streams'] for q in p):
                tags['events with labelled streams'] += 1; continue
            kind = collections.Counter()
            for q in p:
                e = ix.get(q, 'stream')
                if e:
                    with open(os.path.join(ix.assets, e.crate), 'rb') as f:
                        f.seek(e.offset)
                        r = riff_labels(f.read(min(e.raw, 1024)))
                    kind['%#x %d ch %d Hz' % r[:3]] += 1
                else:
                    kind['no stream'] += 1
            ok = set(kind) == {'0x8311 1 ch 32000 Hz'}
            tags['unlabelled events, ' + ('PTADPCM mono 32 kHz (usable)' if ok else 'other formats or no stream (not decoded here)')] += 1
            if ok:
                texts = [subtitle('%s_%02d' % (ev, i + 1)) for i in range(len(ids))]
                print('%-26s %2d %s | %s' % (ev, len(ids), 'exact  ' if len(ids) == 1 else 'assumed', ' / '.join(x for x in texts if x)[:150]))
        print('%d events of Bain (of %d names in the dialogue lists) in the banks; both radio clicks in %d, as first and last sound in %d' % (
            len(d['events']), d['names'], d['radio'], d['radio_ordered']))
        for k, v in sorted(tags.items()):
            print('  %5d %s' % (v, k))
        return 0
    if cmd == 'wav':
        import pd2_audio
        line = bain_line(pos[0])
        s = decode(line)
        if opt.get('--radio', '1') != '0':
            s = list(radio_clicks()[0]) + list(s) + list(radio_clicks()[1])
        pd2_audio.write_wav(pos[1], [s], RATE)
        print('%s: %.1f s, "%s" -> %s' % (line['label'], line['seconds'], line['text'], pos[1]))
        return 0
    if cmd == 'build':
        src, dst = (pos + [None, None])[:2]
        groups = tuple(opt.get('--set', ','.join(GROUPS)).split(','))
        if set(groups) - set(GROUPS):
            raise ValueError('--set: groups are %s' % ', '.join(GROUPS))
        res = build(src, dst, groups, opt.get('--stream'), radio=opt.get('--radio', '1') != '0')
        a0, a1 = fa_findings(res['src']), fa_findings(res['dst'])
        print('kl_fa.check: %d findings before, %d after, %s' % (len(a0), len(a1), 'the same' if a0 == a1 else 'DIFFERENT'))
        return 1 if res['problems'] or a0 != a1 else 0
    if cmd == 'check':
        bad = check(pos[0], pos[1] if len(pos) > 1 else None)
        for x in bad:
            print('PROBLEM', x)
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
