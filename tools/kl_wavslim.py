#!/usr/bin/env python3
"""
Slim a built level's in-memory sound bank (<slot>_Main.WAV beside the archive): the clips that
nothing in the level can play become one shared block of silence.

    python kl_wavslim.py <build folder or _Main.zip> <out folder>     the pair rewritten there, the rest copied
    python kl_wavslim.py measure <build folder or _Main.zip> ...       what would go, nothing written
    python kl_wavslim.py test                                          stock levels: nothing may go

WHY. The game reads the whole .WAV into one block (kl2 0x51cf80; klmem.c: the fifth large block
of a level load, 25.9 MB on Retomoto against 14.7 on stock Subway). A grafted level keeps the
WHOLE bank of its systems level (kl_snd.merge appends to it), so the systems level's map sounds
stay: on Retomoto 14.9 of 27.8 MB are clips no object of the level names (wavreach census,
2026-10-11), 9.95 MB of them SFX/Environment (F07's sirens, traffic, machines).

WHAT IS REACHED. A clip is reached when a sound object of the .SND that some node's sound field
names (kl_snd.sound_fields over EVERY node, systems and map), or a .LOC leaf's sound id, leads to
its wave object (kl_str.closure: parameters, a set's / definition's members, a sequence's
targets). That is the merge's own rule for what a map needs (kl_snd.merge 'kids').

WHAT GOES. Only unreached clips under SFX/Environment and SFX/Ambiences (DROP), and not when a
sound that plays the clip is named audio:animation/... (KEEP_SOUND: an animation event may name
it by string - L03's chair quirk is such a one, unreached by any node). Evidence: in
stock F07 and F01 every clip of those folders is reached, while SFX/Impacts, Footsteps,
Characters, Weapons_KL2_Final, Animations and Animation/Resources have ~3 MB unreached in every
stock level: the engine names those by code or by the material matrix, not by a node, so they
stay. ASSUMPTION: a folder in which stock levels have no unreached clip is named by nodes only.

HOW. The .WHD keeps every record where it is (wave objects name records by offset, the .SND is
not touched): a dropped record's data offset / size / sample counts are rewritten to point at
one shared block of silence of its codec (IMA ADPCM: one zero block = predictor 0, step index 0,
all-zero nibbles = block-align bytes of silence; PCM: 0x400 zero bytes). A dropped sound, if
anything ever played it, plays a short silence. Kept clips are copied byte for byte, 16-aligned,
in their old order. Ogg records (format 0x1000) are never dropped (no silence written for them).

NOT LOADED LIVE as of 2026-10-11 02:50.
"""
import collections, os, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_whd as W

DROP = ('sfx/environment/', 'sfx/ambiences/')      # folders dropped when unreached (lower case, see WHAT GOES)
KEEP_SOUND = ('audio:animation/',)                  # sounds animation events may name by string (L03's chair quirk): kept
F = W.DD_F
IX = {k: i for i, k in enumerate(F)}
PCM, ADPCM, OGG = 1, 0x11, 0x1000
u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]


def open_level(zpath):
    """(kl_prpjoin.Scene of every node, .SND bytes, English .LOC bytes) of a built or stock archive."""
    import kl_gms, kl_rtp, kl_loc
    import kl_prpjoin as J
    from kl_prp import Prp
    with zipfile.ZipFile(zpath) as zf:
        prp = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
        p = Prp(zf.read(prp)); raw = kl_gms.unpack(zf.read(prp[:-4] + '.gms')); buf = zf.read(prp[:-4] + '.buf')
        snd = zf.read(prp[:-4] + '.SND'); loc = zf.read(kl_loc.members(zf)['English'])
    names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
    for decl, tid, _prio in kl_gms.entities(raw):
        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
        names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
    return J.Scene(p, names, tids, 'dd', os.path.basename(zpath)), snd, loc


def reached(sc, snd, loc):
    """.WHD offsets (as wave objects store them) of every clip the level can play: from the sound
    fields of ALL nodes and from every .LOC sound id. -> (set, Counter, {clip: [sound names]})"""
    import kl_snd, kl_str, kl_loc
    st = collections.Counter()
    ks = list(range(1, len(sc.nodes)))
    rs = kl_snd.roots(sc, ks)
    st['sound references on nodes'] = len(rs)
    for _p, k in kl_loc.leaves(kl_loc.parse(loc)):
        sid = kl_loc.fields(k)[2]
        if sid:
            rs.add(sid); st['.LOC sound ids'] += 1
    s = kl_snd.Snd('dd', snd).walk()
    objs = kl_str.closure(s, rs)
    st['.SND objects reached'] = len(objs)
    out = set(off for o, _i, off in s.waves() if o in objs)
    st['clips reached'] = len(out)
    waves = {o: off for o, _i, off in s.waves()}
    sounds = {}                                              # clip -> the names of the sounds that play it
    for o, t in s.kind.items():
        if t == 1 and u32(s.b, o + 0x14) in waves:
            sounds.setdefault(waves[u32(s.b, o + 0x14)], []).append(s.name(o).decode('latin1').replace('\\', '/').lower())
    return out, st, sounds


def plan(sc, snd, loc, whd, wav):
    """-> (recs {offset: fields}, names {name offset: bytes}, keep [offsets], drop [offsets], Counter)"""
    live, st, sounds = reached(sc, snd, loc)
    items, _T = W.parse('dd', whd)
    recs = {o - 4: list(v) for k, o, v in items if k == 'rec'}
    names = {o: b for k, o, b in items if k == 'name'}
    keep, drop = [], []
    for o, v in recs.items():
        if v[IX['fmt']] & W.STREAMED:
            continue
        if not (16 <= v[IX['off']] and v[IX['off']] + v[IX['size']] <= len(wav)):
            raise ValueError('record %#x: data outside the .WAV' % o)
        n = names.get(v[IX['name']], b'').decode('latin1').replace('\\', '/').lower()
        codec = v[IX['fmt']] & 0xffff
        if o not in live and n.startswith(DROP) and codec in (PCM, ADPCM) and not any(sn.startswith(KEEP_SOUND) for sn in sounds.get(o, ())):
            drop.append(o); st['dropped bytes'] += v[IX['size']]
        else:
            keep.append(o)
            st['kept, unreached' if o not in live else 'kept, reached'] += 1
    st['dropped clips'] = len(drop)
    return recs, names, keep, drop, st


def silence(v):
    """(bytes, pcm bytes, samples) of one block of silence in the record's codec."""
    codec, ch = v[IX['fmt']] & 0xffff, max(1, v[IX['ch']])
    if codec == ADPCM:
        block, spb = v[IX['block']] or 0x400, v[IX['spb']] or 0x7f9
        return bytes(block), spb * ch * 2, spb
    n = 0x400
    return bytes(n), n, n // (2 * ch)


def slim(sc, snd, loc, whd, wav, log=print):
    """-> (new .WHD, new .WAV, Counter). Every record keeps its offset in the .WHD."""
    recs, names, keep, drop, st = plan(sc, snd, loc, whd, wav)
    out = bytearray(wav[:16])
    blocks = {}                                              # codec/block -> offset of its silence
    whd = bytearray(whd)
    for o in sorted(keep, key=lambda o: recs[o][IX['off']]):
        v = recs[o]
        out += bytes(-len(out) % 16)
        new = len(out)
        out += wav[v[IX['off']]:v[IX['off']] + v[IX['size']]]
        v[IX['off']] = new
    for o in drop:
        v = recs[o]
        data, pcm, samples = silence(v)
        key = (v[IX['fmt']] & 0xffff, len(data))
        if key not in blocks:
            out += bytes(-len(out) % 16)
            blocks[key] = len(out); out += data
        v[IX['off']], v[IX['size']], v[IX['pcm']], v[IX['samples']] = blocks[key], len(data), pcm, samples
    for o, v in recs.items():
        if o in drop or o in keep:
            struct.pack_into('<17I', whd, o + 4, *v)
    out += bytes(-len(out) % 16)
    struct.pack_into('<4I', out, 0, 0, len(out), 3, 4)
    st['.WAV before'], st['.WAV after'] = len(wav), len(out)
    log('kl_wavslim: %d in-memory clips, %d reached; %d dropped (%.1f MB, %d silence block(s)); .WAV %.1f -> %.1f MB'
        % (len(keep) + len(drop), st['kept, reached'], len(drop), st['dropped bytes'] / 1e6, len(blocks), len(wav) / 1e6, len(out) / 1e6))
    return bytes(whd), bytes(out), st


def check(whd0, wav0, whd1, wav1):
    """Problems of a slimmed pair against its source: same records at the same offsets, kept
    clips byte-identical, dropped ones a silence block. -> [str]"""
    bad = []
    r0, r1 = W.records('dd', whd0), W.records('dd', whd1)
    if set(r0) != set(r1):
        return ['the records are not the same set']
    i0, _ = W.parse('dd', whd0); i1, _ = W.parse('dd', whd1)
    if [(k, o, v) for k, o, v in i0 if k == 'name'] != [(k, o, v) for k, o, v in i1 if k == 'name']:
        bad.append('the names changed')
    for o, a in r0.items():
        b = r1[o]
        if a['fmt'] & W.STREAMED:
            if a != b:
                bad.append('%#x: a streamed record changed' % o)
            continue
        same = {k: a[k] for k in F if k not in ('off', 'offhi', 'size', 'pcm', 'samples')}
        if same != {k: b[k] for k in same}:
            bad.append('%#x: fields other than the data ones changed' % o); continue
        if not (16 <= b['off'] and b['off'] + b['size'] <= len(wav1)):
            bad.append('%#x: data outside the new .WAV' % o); continue
        d1 = wav1[b['off']:b['off'] + b['size']]
        if (a['size'], a['pcm'], a['samples']) == (b['size'], b['pcm'], b['samples']):
            if d1 != wav0[a['off']:a['off'] + a['size']]:
                bad.append('%#x: kept clip differs' % o)
        elif any(d1):
            bad.append('%#x: dropped clip is not silence' % o)
    if u32(wav1, 4) != len(wav1) or u32(wav1, 0) != 0:
        bad.append('.WAV header')
    return bad


def run(src, dst, log=print):
    """A build folder (or its archive) -> folder dst with the slimmed .WHD / .WAV, everything else copied.
    -> (Counter, problems)"""
    zp = src if src.lower().endswith('.zip') else next(os.path.join(src, f) for f in sorted(os.listdir(src)) if f.lower().endswith('_main.zip'))
    base = zp[:-4]
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the output folder is the build\'s own')
    sc, snd, loc = open_level(zp)
    whd0, wav0 = open(base + '.WHD', 'rb').read(), open(base + '.WAV', 'rb').read()
    whd1, wav1, st = slim(sc, snd, loc, whd0, wav0, log)
    bad = check(whd0, wav0, whd1, wav1)
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(os.path.dirname(zp)):
        p = os.path.join(os.path.dirname(zp), f)
        if os.path.isfile(p):
            shutil.copyfile(p, os.path.join(dst, f))
    open(os.path.join(dst, os.path.basename(base) + '.WHD'), 'wb').write(whd1)
    open(os.path.join(dst, os.path.basename(base) + '.WAV'), 'wb').write(wav1)
    log('kl_wavslim: wrote %s (%s)' % (dst, 'check: 0 problems' if not bad else 'PROBLEMS: ' + '; '.join(bad[:5])))
    return st, bad


def measure(zp, log=print):
    base = zp[:-4]
    sc, snd, loc = open_level(zp)
    whd, wav = open(base + '.WHD', 'rb').read(), open(base + '.WAV', 'rb').read()
    recs, names, keep, drop, st = plan(sc, snd, loc, whd, wav)
    top = collections.Counter()
    for o in drop:
        n = names.get(recs[o][IX['name']], b'?').decode('latin1'); top['/'.join(n.split('/')[:3])] += recs[o][IX['size']]
    log('%s: .WAV %.1f MB, %d in-memory clips, %d reached, %d would go (%.1f MB): %s' % (
        os.path.basename(zp), len(wav) / 1e6, len(keep) + len(drop), st['kept, reached'], len(drop), st['dropped bytes'] / 1e6,
        ', '.join('%s %.2f' % (k, c / 1e6) for k, c in top.most_common(6)) or 'nothing'))
    return st


def selftest(log=print):
    """Stock Dog Days levels: the nine Fragile Alliance levels must lose nothing. Campaign levels
    may lose a few: 2026-10-11 L01 2, L04 2, L06 1, L07 2 clips (0.03-0.2 MB), all cutscene /
    scripted leftovers whose sound names kl2.exe does not hold (cans of l01_bigmarket_civil_life,
    horn_09a, moped_start_driveaway_02, kick_wall of 07_midship1_ambush): dead in stock too, as far
    as the files and the exe show. L03's chair quirk (sound audio:animation/...) is kept by KEEP_SOUND."""
    import kl_snd
    bad = 0
    for L in kl_snd.stock_levels('dd'):
        zp = kl_snd.level_zip(L, 'dd')
        if not os.path.isfile(zp[:-4] + '.WAV'):
            continue
        st = measure(zp, log)
        bad += L.startswith('F') and st['dropped clips'] != 0
    log('kl_wavslim test: %s' % ('PASS' if not bad else 'FAIL: %d Fragile Alliance level(s) would lose clips' % bad))
    return bad


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'test':
        sys.exit(selftest())
    if a and a[0] == 'measure':
        for p in a[1:]:
            zp = p if p.lower().endswith('.zip') else next(os.path.join(p, f) for f in sorted(os.listdir(p)) if f.lower().endswith('_main.zip'))
            measure(zp)
    elif len(a) == 2:
        _st, bad = run(a[0], a[1])
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)
