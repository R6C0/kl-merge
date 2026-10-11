#!/usr/bin/env python3
"""
The stream file for THE VAULT (kl_fa_bank.py: Dead Men M03_A under F07): the stream file that is installed for the
owner + the sixteen clips the map's sound lacks in it (re/bank_campaign.md R1.2 and 'Music stage'). A DRIVER: the
writing is tools/kl_str.py's merge() - the same call tools/kl_fa_talk.py `stream` made for the talk clips - with
the installed file as the base and its .map.json as `prior`. Nothing here installs anything or starts the game.

    python kl_vault_str.py need                      the sixteen clips: Dead Men block, bytes, form (from M03_A's .WHD)
    python kl_vault_str.py build <base.str> <out.str>   out = base + those blocks (+ <out>.map.json extended, the
                                                     base's .bain.json carried), then `proof`; exit 1 on a problem
    python kl_vault_str.py proof <base.str> <out.str>   every old byte / clip / map entry is where it was (below)
    python kl_vault_str.py levels <out.str> [level ...]   kl_str.check_levels: the banks of the six Dead Men levels
                                                     the tab's maps are made from, merged against <out>'s map
    python kl_vault_str.py tab <base.str> <out.str> <folder with *_Main.WHD> ...
                                                     a BUILT map (a tab folder, read only): every streamed record
                                                     of its .WHD names a block of <out> that <base> has at the
                                                     same place with the same clips; KLTalk.ini's StreamBytes fits
    python kl_vault_str.py whd <out.str> <built folder> [--no-ai]   the bank of a build of The Vault: every streamed record
                                                     resolves into <out>; the sixteen clips have their record and
                                                     the index entry at that place is the clip (name of the block's
                                                     Dead Men source, rate, channels, codec, bytes)
    python kl_vault_str.py stamp <out.str> <built folder> ...   <folder>/stream.json: the file and the bytes of it the
                                                     build's streamed records need

WHAT 'EXTENSION' MEANS FOR THIS FORMAT (READ: kl_str.py's docstring; MEASURED by `proof`)
  An IOISNDSTREAM file is header (0x38) + data blocks from 0x100 + format table + name table + index, the index LAST
  and found through the header's offset. A level names a clip by the OFFSET of its block (its .WHD record), kl2.exe
  reads 0x38 header bytes and no table (kl_str: ASSUMPTION beyond 0x67e810). So a file cannot grow by plain
  appending: the new blocks take the place where the base's tables stood, and one fresh table + index for all clips
  follows them. `the first <base size> bytes are the base` therefore does NOT hold and is not claimed. What holds,
  and what proof() shows:
    1. bytes 0x38 .. the base's data end are the base's (one sha1 over 1.69 GB), the header differs only in the
       index offset and the clip count (0x18 .. 0x24);
    2. clip by clip: every index entry of the base stands in the new index with the same id, name, block offset,
       size, format bytes, lip word and layer;
    3. every entry of the base's .map.json is in the new one with the same new offset; the base's .bain.json is
       carried and each of its clips is found by name at its offset with the base's bytes;
    4. each appended block equals Dead Men's bytes and stands in the index as Dead Men has it;
    5. kl_str.Stream.account(): every byte of the file is claimed, no problem; the file is under 2 GB.

THE SIXTEEN (CLIPS; names as M03_A's .WHD has them. Dead Men's stream file also holds a second, shorter break-in set
'..._LOOP2.wav' (56 s, block 0x1e049d00) that the level does not name: the .WHD record's OFFSET decides, never a name)
  music      two interleaved PCM sets, each ONE block that must come whole: the break-in set (four stereo layers,
             32 kHz, 36.9 MB) and the way-out set (two stereo layers, 21.5 MB)
  ambience   one Vorbis clip (the vault, deeper)
  guards     nine single IMA ADPCM lines with a LIP block

GUESS / ASSUMED, each where the code makes it. NOTHING written by this file has run in the game.
"""
import collections, hashlib, json, os, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_str, kl_snd
import kl_whd as W

LEVEL = 'M03_A'
BS = chr(92)
LIMIT = 1 << 31                         # nothing past 2 GB was ever tried (the .WHD record has an 'offhi' dword; unused in stock)
MUSIC = ('Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav', 'Music/InHouse/M03A/BO_Sus_Layer2_Bass_LOOP.wav',
         'Music/InHouse/M03A/BO_Sus_Layer3_Intense_LOOP.wav', 'Music/InHouse/M03A/BO_Sus_Layer4_Basic_LOOP.wav',
         'Music/InHouse/M03A/M03_Bustout_ActionV34.wav', 'Music/InHouse/M03A/M03_Bustout_IntenseClimax_Loop.wav')       # = kl_fa_bank.MUSIC_CLIPS
AMBIENCE = ('SFX/Ambiences/M03_A/Inside/Ambience_Inside_Vault_Deeper.wav',)
GUARDS = tuple('Dialog/' + n + '.wav' for n in (
    'M02/Dialogue/Situation/M02_GuardsShout/M02_GuardsShout_020_Guard', 'M02/Dialogue/Situation/M02_GuardsShout/M02_GuardsShout_025_Guard',
    'M02/Dialogue/Situation/M02_GuardsShout/M02_GuardsShout_050_Guard', 'M02/Dialogue/Situation/M02_GuardsShout/M02_GuardsShout_060_Guard',
    'M03/Dialogue/M03a_OneLiners/M03_GuardAlarm/M03_GuardAlarm_010_Guard02', 'M03/Dialogue/M03a_OneLiners/M03_Spotted/M03_Spotted_040_Guard',
    'M03/Dialogue/Situation/M03_Enter/M03_Enter_011_Guard', 'M08/Dialogue/Situations/M08_Cantina/M08_Cantina_010_Guard01',
    'M08/Dialogue/Situations/M08_Cantina/M08_Cantina_030_Guard01'))
# MEASURED: exactly the names `kl_fa_bank.lost_clips` gives for <work>/build/c_bank/bank_vault_bare (the build
# against the installed file): of the 85 names its result.json lists these 16 have no record in the built .WHD
CLIPS = MUSIC + AMBIENCE + GUARDS


def norm(n):
    return n.replace(BS, '/').lower()


def source():
    """(M03_A's Dead Men .WHD bytes, its records, {lower-case name: [record offsets of the PC_Def.str ones]})."""
    whd = kl_snd.read(kl_snd.beside(LEVEL, '.WHD', 'dm'))
    recs, by = W.records('dm', whd), collections.defaultdict(list)
    for at, f in recs.items():
        if f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE:       # the language files' records are other recordings: not merged (kl_snd.merge)
            by[norm(kl_snd.cs(whd, f['name']).decode('latin1'))].append(at)
    return whd, recs, by


def need(names=CLIPS):
    """{Dead Men block offset in its PC_Def.str: sorted [.WHD record names]} of the clips, each interleaved group
    whole (kl_str.need()'s rule: a set is one block). ValueError when a name is not exactly one PC_Def.str record."""
    whd, recs, by = source()
    want = collections.defaultdict(set)
    for n in names:
        at = by.get(norm(n), [])
        if len(at) != 1:
            raise ValueError('kl_vault_str: %s has %d PC_Def.str records in %s.WHD, 1 expected' % (n, len(at), LEVEL))
        f = recs[at[0]]
        members = W.group_of('dm', recs, at[0]) if f['fmt'] >> 24 else [at[0]]
        if not members:
            raise ValueError('kl_vault_str: %s stands in a torn stream group' % n)
        if len({recs[m]['off'] for m in members}) != 1:
            raise ValueError('kl_vault_str: the group of %s is not one block' % n)
        for m in members:
            want[recs[m]['off']].add(kl_snd.cs(whd, recs[m]['name']).decode('latin1').replace(BS, '/'))
    extra = {n for v in want.values() for n in v} - set(names)
    if {norm(n) for n in extra}:
        raise ValueError('kl_vault_str: the groups bring clips that are not in CLIPS: %s' % sorted(extra))
    return {o: sorted(v) for o, v in want.items()}


def show_need(log=print):
    want = need()
    dm = kl_str.Stream(kl_str.paths()['dm'])
    total = 0
    for o in sorted(want):
        n = dm.copy_length(o)
        total += n
        log('  Dead Men %#11x  %9d bytes  %s%s' % (o, n, 'LIP + ' if dm.has_lip(o) else '', ' | '.join(
            '%s %d Hz %d ch %.1f s layer %d  %s' % (kl_str.CODEC.get(c.codec, c.codec), c.rate, c.channels, c.samples / max(1, c.rate), c.layer, c.name)
            for c in dm.blocks[o])))
        for n in want[o]:
            log('      .WHD name  %s' % n)
    log('%d blocks, %d .WHD names, %d bytes (%.2f MB)' % (len(want), sum(len(v) for v in want.values()), total, total / 2.0 ** 20))
    dm.close()
    return want


def _sha(f, a, b):
    h = hashlib.sha1()
    f.seek(a)
    left = b - a
    while left:
        chunk = f.read(min(left, 32 << 20))
        if not chunk:
            break
        h.update(chunk); left -= len(chunk)
    return h.hexdigest()


def proof(base_path, out_path, log=print):
    """The five statements of the docstring on a written file. -> [problems]"""
    P = kl_str.paths()
    b, m, dm = kl_str.Stream(base_path), kl_str.Stream(out_path), kl_str.Stream(P['dm'])
    bad = []
    prior = kl_str.load_map(base_path + '.map.json')
    full = kl_str.load_map(out_path + '.map.json')
    end = kl_str.data_end(b, dm, {at: o for o, (at, _n) in prior.items()})
    cut = b.table_start()
    log('base %s: %d bytes, %d clips in %d blocks; data ends at %d (%#x), its tables start at %d' % (base_path, b.size, len(b.clips), len(b.blocks), end, end, cut))
    log('new  %s: %d bytes (%.3f GB; +%d = %.2f MB), %d clips in %d blocks; %d bytes under 2 GB' % (
        out_path, m.size, m.size / 2.0 ** 30, m.size - b.size, (m.size - b.size) / 2.0 ** 20, len(m.clips), len(m.blocks), LIMIT - m.size))
    if m.size >= LIMIT:
        bad.append('the file has %d bytes: past 2 GB' % m.size)
    if end > cut:
        bad.append('the base\'s data end %#x lies behind the start of its tables %#x' % (end, cut))
    # 1. the bytes
    if m.build != b.build or m.head[:0x18] != b.head[:0x18] or m.head[0x24:] != b.head[0x24:]:
        bad.append('the header differs from the base beyond index offset and clip count')
    ha, hb = _sha(m.f, kl_str.HEAD, end), _sha(b.f, kl_str.HEAD, end)
    log('1. bytes 0x38 .. %#x (%d bytes): sha1 new %s, base %s: %s; header: build %x, differs from the base only in 0x18..0x24: %s' % (
        end, end - kl_str.HEAD, ha, hb, 'EQUAL' if ha == hb else 'DIFFERENT', m.build, m.head[:0x18] == b.head[:0x18] and m.head[0x24:] == b.head[0x24:]))
    if ha != hb:
        bad.append('bytes 0x38..%#x differ from the base' % end)
    whole = _sha(m.f, 0, b.size) == _sha(b.f, 0, b.size)
    log('   (the first %d bytes as a whole equal the base: %s - not claimed: the base\'s tables stood at %d .. %d, the new blocks start at %d)' % (
        b.size, whole, cut, b.size, min(at for o, (at, _n) in full.items() if o not in prior) if set(full) - set(prior) else 0))
    # 2. clip by clip
    new_by_id = {c.id: c for c in m.clips}
    moved = 0
    for c in b.clips:
        n = new_by_id.get(c.id)
        if n is None or (n.name, n.offset, n.size, n.fmt, n.lip, n.layer, n.key) != (c.name, c.offset, c.size, c.fmt, c.lip, c.layer, c.key):
            moved += 1
    log('2. clip by clip: %d of the base\'s %d index entries stand in the new index with the same id, name, block offset, size, format, lip word, layer' % (
        len(b.clips) - moved, len(b.clips)))
    if moved:
        bad.append('%d clips of the base moved or changed' % moved)
    # 3. the maps
    off_changed = [o for o, (at, _n) in prior.items() if o not in full or full[o][0] != at]
    len_changed = [o for o, (at, n) in prior.items() if o in full and full[o][1] != n]
    added = {o: v for o, v in full.items() if o not in prior}
    log('3. .map.json: %d entries, %d of the base\'s %d with the same new offset (%d with another byte count: kl_str.merge rewrites the count from the files), %d new' % (
        len(full), len(prior) - len(off_changed), len(prior), len(len_changed), len(added)))
    if off_changed:
        bad.append('%d entries of the base\'s map are gone or point elsewhere' % len(off_changed))
    bj, oj = base_path + '.bain.json', out_path + '.bain.json'
    if os.path.isfile(bj):
        if not os.path.isfile(oj) or open(bj, 'rb').read() != open(oj, 'rb').read():
            bad.append('the .bain.json was not carried unchanged')
        clips, ok = json.load(open(bj))['clips'], 0
        for name, (at, n) in clips.items():
            c = m.find(name)
            b.f.seek(at); m.f.seek(at)
            if c is None or (c.offset, c.size, c.codec, c.layer) != (at, n, kl_str.PCM, 0) or at >= end or b.f.read(n) != m.f.read(n):
                bad.append('Bain clip %s is not at %#x with the base\'s bytes' % (name, at))
            else:
                ok += 1
        log('   .bain.json carried byte for byte; %d of its %d clips found by name at their offset, PCM, with the base\'s bytes' % (ok, len(clips)))
    # 4. the appended blocks
    n_clip, first = 0, None
    for o, (at, n) in sorted(added.items(), key=lambda kv: kv[1][0]):
        first = at if first is None else first
        dm.f.seek(o); m.f.seek(at)
        same = dm.f.read(n) == m.f.read(n)
        got = {c.name: c for c in m.blocks.get(at, [])}
        okc = True
        for c in dm.blocks[o]:
            g = got.get(c.name)
            n_clip += 1
            okc &= g is not None and (g.size, g.fmt, g.lip, g.layer, g.key) == (c.size, c.fmt, c.lip, c.layer, c.key)
        if at < end or at % kl_str.ALIGN or not same or not okc or len(got) != len(dm.blocks[o]):
            bad.append('appended block %#x (Dead Men %#x): bytes equal %s, index as Dead Men %s' % (at, o, same, okc))
        log('   + %10d (%#x) <- Dead Men %#x, %8d bytes, bytes equal %s: %s' % (at, at, o, n, same, ' | '.join(
            '%s %d Hz %d ch layer %d %s' % (kl_str.CODEC.get(c.codec, c.codec), c.rate, c.channels, c.layer, c.name.rsplit('/', 1)[-1]) for c in m.blocks.get(at, []))))
    log('4. %d appended blocks (%d index entries) from %s on, each Dead Men\'s bytes with Dead Men\'s format, lip word and layer' % (len(added), n_clip, first))
    # 5. every byte
    by, acc = m.account()
    by0, acc0 = b.account()
    log('5. account: %s -> %d of %d bytes; problems %d (the base alone: %d)' % (dict(by), sum(by.values()), m.size, len(acc), len(acc0)))
    bad += ['account: ' + x for x in acc]
    for x in (b, m, dm):
        x.close()
    log('PROOF: %s' % ('PASS' if not bad else 'FAIL'))
    for x in bad:
        log('  PROBLEM ' + x)
    return bad


def build(base_path, out_path, log=print):
    """out = base + need()'s blocks by kl_str.merge (prior = the base's map), the .bain.json carried. -> [problems]"""
    P = kl_str.paths()
    out_abs = os.path.abspath(out_path).lower().replace(BS, '/')
    for banned in ('/kl_portbackup/', '/build/v_bain/over_talk/', '/build/w_tab'):
        if banned in out_abs:
            raise ValueError('kl_vault_str: %s is not a place this tool writes to' % out_path)
    if out_abs in (os.path.abspath(p).lower().replace(BS, '/') for p in (P['merged'], P['installed'], P['stock'], base_path)):
        raise ValueError('kl_vault_str: the output is one of the files that must stay')
    prior = kl_str.load_map(base_path + '.map.json')
    log('the clips:')
    want = show_need(log)
    have = sorted(o for o in want if o in prior)
    if have:
        log('  %d of the blocks are in the base already (not copied again)' % len(have))
    res = kl_str.merge(base_path, P['dm'], want, out_path, prior, log)
    if os.path.isfile(base_path + '.bain.json'):
        shutil.copyfile(base_path + '.bain.json', out_path + '.bain.json')
    log('  %d blocks added, %d index entries; %d names stand twice in the index (kl_str.merge: a Dead Men name that is a Dog Days name too)' % (
        res['blocks_added'], len(res['added']), res['names_twice']))
    return proof(base_path, out_path, log)


def _whd_of(folder):
    f = [x for x in sorted(os.listdir(folder)) if x.lower().endswith('_main.whd')]
    if len(f) != 1:
        raise ValueError('%s: %d *_Main.WHD' % (folder, len(f)))
    return open(os.path.join(folder, f[0]), 'rb').read()


def _streamed(whd):
    recs = W.records('dd', whd)
    return recs, [(at, f, f['off'] | f['offhi'] << 32) for at, f in sorted(recs.items()) if f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE]


def tab(base_path, out_path, folders, log=print):
    """Built maps against the new file: every streamed PC_Def.str record names a block the new file has, and the
    base has the same block with the same clips (so what the map plays is what it played). -> [problems]"""
    b, m = kl_str.Stream(base_path), kl_str.Stream(out_path)
    bad = []
    for folder in folders:
        whd = _whd_of(folder)
        _recs, st = _streamed(whd)
        miss = [o for _a, _f, o in st if o not in m.blocks]
        other = [o for _a, _f, o in st if o in m.blocks and (o not in b.blocks or [(c.name, c.size, c.fmt, c.layer) for c in b.blocks[o]]
                                                              != [(c.name, c.size, c.fmt, c.layer) for c in m.blocks[o]])]
        over = [o for _a, f, o in st if o in m.blocks and not f['fmt'] >> 24 and f['size'] > m.audio(o)]
        line = '%s: %d streamed PC_Def.str records on %d blocks: %d name no block of the new file, %d a block that is not the base\'s, %d larger than their block' % (
            folder, len(st), len({o for _a, _f, o in st}), len(miss), len(other), len(over))
        ini = os.path.join(folder, 'KLTalk.ini')
        if os.path.isfile(ini):
            sb = [int(l.split('=', 1)[1]) for l in open(ini, encoding='latin1').read().splitlines() if l.strip().lower().startswith('streambytes=')]
            names = [l.split('=', 1)[1].strip() for l in open(ini, encoding='latin1').read().splitlines() if l.strip().lower().startswith('map=')]
            line += '; KLTalk.ini %s StreamBytes %s <= %d: %s' % (names[:1], sb[:1], m.size, bool(sb) and sb[0] <= m.size)
            if not sb or sb[0] > m.size:
                bad.append('%s: KLTalk.ini\'s StreamBytes does not fit' % folder)
        log(line)
        if miss or other or over:
            bad.append('%s: %d / %d / %d stream records do not resolve as before' % (folder, len(miss), len(other), len(over)))
    b.close(); m.close()
    log('TAB: %s' % ('PASS' if not bad else 'FAIL'))
    return bad


def whd(out_path, folder, log=print, names=CLIPS):
    """The bank of a build of The Vault against the stream file: all streamed records resolve; each of the sixteen
    has ONE streamed record whose offset is a block of the file that holds Dead Men's bytes of that clip's block,
    and the index entry of that block and layer has the record's rate, channels and size. -> [problems]"""
    P = kl_str.paths()
    m, dm = kl_str.Stream(out_path), kl_str.Stream(P['dm'])
    full = kl_str.load_map(out_path + '.map.json')
    back = {at: o for o, (at, _n) in full.items()}
    want = need(names)
    block_of = {norm(n): o for o, v in want.items() for n in v}
    b = _whd_of(folder)
    recs, st = _streamed(b)
    bad = []
    miss = [o for _a, _f, o in st if o not in m.blocks]
    over = [o for _a, f, o in st if o in m.blocks and not f['fmt'] >> 24 and f['size'] > m.audio(o)]
    torn = W.torn_groups('dd', b)
    log('%s: %d records, %d streamed PC_Def.str ones on %d blocks: %d name no block of %s, %d larger than their block; torn groups %d' % (
        folder, len(recs), len(st), len({o for _a, _f, o in st}), len(miss), os.path.basename(out_path), len(over), len(torn)))
    if miss or over or torn:
        bad.append('%d records name no block, %d are larger than their block, %d torn groups' % (len(miss), len(over), len(torn)))
    by = collections.defaultdict(list)
    for at, f in recs.items():
        by[norm(kl_snd.cs(b, f['name']).decode('latin1'))].append((at, f))
    for n in names:
        got = by.get(norm(n), [])
        streamed = [(at, f) for at, f in got if f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE]
        if len(streamed) != 1:
            mem = [f for _a, f in got if not f['fmt'] & W.STREAMED]
            if len(mem) == 1 and not streamed:           # kl_snd.merge's `inmem`: a single ADPCM line moved into the level's .WAV
                log('  IN MEMORY  %-70s fmt %#x %d Hz %d ch %d bytes in the .WAV (not streamed: plays without the stream file)' % (
                    n.rsplit('/', 1)[-1], mem[0]['fmt'], mem[0]['rate'], mem[0]['ch'], mem[0]['size']))
                continue
            bad.append('%s: %d streamed records in the built .WHD, 1 expected' % (n, len(streamed)))
            log('  MISSING    %s (%d records of that name, %d streamed)' % (n, len(got), len(streamed)))
            continue
        at, f = streamed[0]
        o = f['off'] | f['offhi'] << 32
        src = back.get(o)
        layer = (f['fmt'] >> 24) & 0x7f if f['fmt'] >> 24 else 0
        layer = 1 if f['fmt'] >> 24 & 0x80 else (layer + 1 if f['fmt'] >> 24 else 0)   # group byte: 0x80 | n = the first, i = the (i+1)-th
        clip = next((c for c in m.blocks.get(o, []) if c.codec != kl_str.SET and c.layer == layer), None)
        ok = src == block_of[norm(n)] and clip is not None
        same = False
        if ok:
            k = full[src][1]
            dm.f.seek(src); m.f.seek(o)
            same = dm.f.read(k) == m.f.read(k)
            ok = same and (clip.rate, clip.channels) == (f['rate'], f['ch']) and (f['size'] == clip.size or f['fmt'] >> 24 == 0 and f['size'] <= m.audio(o))
        log('  %s  %-46s record %#x fmt %#010x -> %d (%#x) = Dead Men %s; index there: %s' % (
            'OK        ' if ok else 'WRONG     ', n.rsplit('/', 1)[-1], at, f['fmt'], o, o, '%#x' % src if src is not None else 'NO BLOCK OF THE MAP',
            '%s %d Hz %d ch %.1f s layer %d size %d (record: %d Hz %d ch size %d) %s, bytes = Dead Men\'s: %s' % (
                kl_str.CODEC.get(clip.codec, clip.codec), clip.rate, clip.channels, clip.samples / max(1, clip.rate), clip.layer, clip.size, f['rate'], f['ch'], f['size'],
                clip.name.rsplit('/', 1)[-1], same) if clip else 'no clip of layer %d' % layer))
        if not ok:
            bad.append('%s does not resolve to its clip' % n)
    m.close(); dm.close()
    log('WHD: %s' % ('PASS' if not bad else 'FAIL'))
    for x in bad:
        log('  PROBLEM ' + x)
    return bad


def stamp(out_path, folder, log=print):
    """Write <folder>/stream.json: which stream file the build needs. 'bytes_needed' = the end of the last block a
    streamed record of the built .WHD names: a PC_Def.str SHORTER than that (the pair installed before this one)
    has its tables or nothing where the record points - the map must not be loaded with it. KLTalk.ini's
    StreamBytes is the talk lines' need only (kl_fa_talk) and is smaller. -> the dict"""
    m = kl_str.Stream(out_path)
    _recs, st = _streamed(_whd_of(folder))
    ends = [o + m.length(o) for _a, _f, o in st if o in m.blocks]
    info = collections.OrderedDict(stream_file=out_path.replace(BS, '/'), stream_bytes=m.size, stream_sha1=_sha(m.f, 0, m.size),
                                   bytes_needed=max(ends), streamed_records=len(st), records_without_a_block=len(st) - len(ends),
                                   note='install this PC_Def.str (or a later extension of it) BEFORE the map: its music, vault ambience and nine guard '
                                        'lines lie behind the end of the data of the 1,694,610,488-byte file (re/bank_campaign.md, Music stage)')
    m.close()
    with open(os.path.join(folder, 'stream.json'), 'w') as f:
        json.dump(info, f, indent=1)
    log('%s/stream.json: needs %d bytes of %s (%d bytes, sha1 %s)' % (folder, info['bytes_needed'], os.path.basename(out_path), info['stream_bytes'], info['stream_sha1']))
    return info


def levels(out_path, names=None, log=print):
    bad = kl_str.check_levels(out_path, names or kl_str.LEVELS, log=log)
    log('LEVELS: %s' % ('PASS' if not bad else 'FAIL'))
    for x in bad:
        log('  ' + x)
    return bad


def main(a):
    cmd = a[0] if a else ''
    if cmd == 'need':
        show_need()
        return 0
    if cmd == 'build' and len(a) == 3:
        return 1 if build(a[1], a[2]) else 0
    if cmd == 'proof' and len(a) == 3:
        return 1 if proof(a[1], a[2]) else 0
    if cmd == 'stamp' and len(a) >= 3:
        for folder in a[2:]:
            stamp(a[1], folder)
        return 0
    if cmd == 'levels' and len(a) >= 2:
        return 1 if levels(a[1], a[2:]) else 0
    if cmd == 'tab' and len(a) >= 4:
        return 1 if tab(a[1], a[2], a[3:]) else 0
    if cmd == 'whd' and len(a) in (3, 4):
        # --no-ai: a build without enemies names no guard line (kl_fa_bank NO_AI): the music and the ambience only
        return 1 if whd(a[1], a[2], names=MUSIC + AMBIENCE if a[3:] == ['--no-ai'] else CLIPS) else 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
