#!/usr/bin/env python3
"""
Fit a level .LOC under the game's buffer cap (kl_loc.LOC_CAP = 612,634 for EVERY language, see kl_loc), losing as little
as possible and saying what was lost. Self-test on synthetic trees: `python tools/kl_loc_fit_test.py`.

    python kl_loc_fit.py --stage OUTDIR     scan <DD>\\KLExpansion\\Maps\\*\\*_Main.zip (read-only); for every zip with a .LOC
                                            member over the cap write OUTDIR\\<MapFolder>\\<zipname>: the same zip with ONLY
                                            those .LOC members replaced by fit() output, plus OUTDIR\\fit_report.txt
    python kl_loc_fit.py file.LOC [english.LOC] [stock.LOC]   fit one file, print the report (writes nothing)
    python kl_loc_fit.py --verify [DD]      read-only: every installed Russian / Japanese .LOC against the stock .LOC of its slot -
                                            missing / blanked / re-flagged stock sound leaves are FAULTs (verify(), compare())

Why files grow past the cap (found 2026-10-23): the KLVoice/ subtree (Dead Men voice leaves, ~93 KB, 1,850 leaves, text in
English in EVERY language file, added by kl_dmvoice) plus KLTalk/ and extra Multiplayer lines. Stock Dog Days Russian is
already 612,634 = the cap, Japanese 530,319, so any addition overflows those two. English (457,359 stock) has 155 KB room.

fit() priority (each step runs only while the file is still over the cap; inside a step the biggest saving goes first, so the
fewest leaves are touched). "Ours" = a key the stock Dog Days .LOC of the same slot does not have (stock= given), else a key
under KLVoice/ or KLTalk/, or an alias K_C1..K_C9 whose base key K is in the file (heuristic; a stock per-character line has
no base key and is NOT ours - kl_dmvoice runs fit() this way, without a stock file):
  1. ours, text longer than the English leaf's text -> take the English text (sound and ids kept).
  2. STOCK leaves WITH a sound (subtitles of a line the player hears anyway), text longer than English -> English text.
     Subtitles in English beat a crash; this is what saves Russian/Japanese, whose stock text is 20-40% longer than English.
  3. STOCK leaves without a sound (UI strings), same rule. After 2 because UI text is read, subtitles are heard.
  4. ours: blank the text (the voice stays, the subtitle goes).
  5. ours: drop alias duplicates K_C1..K_C9 whose base key K remains (a flag-1 field then falls silent for that heister).
  6. ours: drop whole leaves, biggest first (last resort).
Stock SOUND leaves are never dropped, and no stock leaf is ever removed; steps 2-3 only shorten text. If the cap still is not
met, fit() raises ValueError.
"""
import os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_loc as L

LOC_CAP = L.LOC_CAP
ALIAS = re.compile(rb'^(.*)_C[1-9]$', re.S)
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'


def _tails(k):
    """-> (text, bytes after the text's terminator) of a TEXT leaf, else None"""
    if not k.flags & L.TEXT:
        return None
    e = k.raw.index(b'\0')
    return k.raw[:e], k.raw[e + 1:]


def _walk(kids, path=()):
    """-> [(key, table list holding it, index-free Node)] for every leaf"""
    out = []
    for k in kids:
        p = path + (k.name.decode('latin1'),)
        if k.kids is not None:
            out += _walk(k.kids, p)
        else:
            out.append(('/'.join(p), kids, k))
    return out


def _is_ours(key, stock_keys, keys=None):
    """keys: lower-case set of every key in the file being fitted (the heuristic needs it, see below); None = the old, looser rule"""
    if stock_keys is not None:
        return key.lower() not in stock_keys
    low = key.lower()
    if low.startswith('klvoice/') or low.startswith('kltalk/'):
        return True
    m = re.match(r'^(.*)_c[1-9]$', low)
    # 2026-10-24 (kl_loc_fit_test): an alias K_C<n> of ours (kl_voice.loc_aliases) always stands beside its base key K, while a
    # STOCK per-character line ships as K_C1..K_C9 with no K (kl2 looks a key up either as K or as K_C<n>, never both). Without
    # this test every stock FA line of a Russian / Japanese file counted as ours and could lose its subtitle (step 4) or the
    # whole leaf (step 6) - kl_dmvoice calls fit() without a stock file, so it always ran on this heuristic.
    return m is not None and (keys is None or m.group(1) in keys)


def _prune(kids):
    """drop tables left empty"""
    for k in list(kids):
        if k.kids is not None:
            _prune(k.kids)
            if not k.kids:
                kids.remove(k)


def fit(data, cap=LOC_CAP, english=None, stock=None, report=None):
    """-> .LOC bytes <= cap (data itself if it already fits or is a stub). english: the same level's English .LOC bytes;
    stock: the stock Dog Days .LOC of the same slot and language (decides which keys are ours). report: a list that gets one
    line per step that changed something. Raises ValueError if no step list gets under the cap."""
    rep = report if report is not None else []
    if len(data) <= cap:
        return data
    tree = L.parse(data)
    if tree is None:
        return data
    en = {}
    if english is not None and L.parse(english) is not None:
        en = {k.lower(): n for k, n in L.leaves(L.parse(english))}
    stock_keys = None
    if stock is not None and L.parse(stock) is not None:
        stock_keys = {k.lower() for k, _n in L.leaves(L.parse(stock))}
    size = len(L.build(tree))
    start = size
    allkeys = {k.lower() for k, _n in L.leaves(tree)}         # for the ownership heuristic (the base key of an alias)

    def swap(sel, label):
        """text -> English text for the leaves sel(key, node) accepts, biggest saving first, until under the cap"""
        nonlocal size
        c = []
        for key, _tab, n in _walk(tree):
            if not sel(key, n) or key.lower() not in en:
                continue
            a, b = _tails(n), _tails(en[key.lower()])
            if a is None or b is None or len(b[0]) >= len(a[0]) or b[0].strip() == b'':
                continue
            c.append((len(a[0]) - len(b[0]), key, n, b[0], a[1]))
        c.sort(key=lambda x: -x[0])
        done = saved = 0
        for gain, key, n, txt, tail in c:
            if size <= cap:
                break
            n.raw = txt + b'\0' + tail
            size -= gain; done += 1; saved += gain
        if done:
            rep.append('%s: %d leaves, -%d bytes' % (label, done, saved))

    def ours(key, n):
        return _is_ours(key, stock_keys, allkeys)

    swap(ours, '1 our keys: English text')
    swap(lambda k, n: not ours(k, n) and bool(n.flags & L.SOUND), '2 stock keys with a sound: English subtitle')
    swap(lambda k, n: not ours(k, n) and not n.flags & L.SOUND, '3 stock keys without a sound: English text')
    # 4 blank our text (the leaf keeps its sound; a text-only leaf of ours is left for step 6)
    if size > cap:
        c = []
        for key, _tab, n in _walk(tree):
            t = _tails(n)
            if ours(key, n) and t is not None and t[0] and n.flags & L.SOUND:
                c.append((len(t[0]), n, t[1]))
        c.sort(key=lambda x: -x[0])
        done = saved = 0
        for gain, n, tail in c:
            if size <= cap:
                break
            n.raw = b'\0' + tail
            size -= gain; done += 1; saved += gain
        if done:
            rep.append('4 our keys: text blanked, voice kept: %d leaves, -%d bytes' % (done, saved))
    # 5 / 6 drops of our leaves
    def drop(cands, label):
        nonlocal size
        cands.sort(key=lambda x: -x[0])
        done = saved = 0
        for gain, tab, n in cands:
            if size <= cap:
                break
            tab.remove(n); size -= gain; done += 1; saved += gain
        if done:
            rep.append('%s: %d leaves, -%d bytes (estimate)' % (label, done, saved))
    if size > cap:
        c = []
        for key, tab, n in _walk(tree):
            m = ALIAS.match(n.name)
            if m and ours(key, n) and any(x.name.lower() == m.group(1).lower() for x in tab):
                c.append((len(n.name) + 2 + len(n.raw) + 4, tab, n))
        drop(c, '5 our alias duplicates K_C1..K_C9 dropped (base key kept)')
    if size > cap:
        c = [(len(n.name) + 2 + len(n.raw) + 4, tab, n) for key, tab, n in _walk(tree) if ours(key, n)]
        drop(c, '6 our leaves dropped (last resort)')
    _prune(tree)
    out = L.build(tree)
    if len(out) > cap:                       # drop estimates were a few bytes off (offset table, empty tables): pass again on the real size
        if len(out) >= len(data):
            raise ValueError('cannot fit: %d bytes after all steps, cap %d (start %d)' % (len(out), cap, start))
        return fit(out, cap, english, stock, rep)
    if L.build(L.parse(out)) != out:
        raise ValueError('fit() output does not round-trip')
    rep.append('result: %d -> %d bytes (cap %d)' % (len(data), len(out), cap))
    return out


def _loc_members(zf):
    return {n.rsplit('_Main', 1)[1][:-4]: n for n in zf.namelist() if n.upper().endswith('.LOC')}


def stage(outdir, dd=DD, log=print):
    maps = os.path.join(dd, 'KLExpansion', 'Maps')
    lines = []
    for folder in sorted(os.listdir(maps)):
        for zn in sorted(os.listdir(os.path.join(maps, folder))):
            if not zn.lower().endswith('_main.zip'):
                continue
            zp = os.path.join(maps, folder, zn)
            with zipfile.ZipFile(zp) as zin:
                mem = _loc_members(zin)
                over = {lg: n for lg, n in mem.items() if zin.getinfo(n).file_size > LOC_CAP}
                if not over:
                    lines.append('%s\\%s: all .LOC <= %d, not staged' % (folder, zn, LOC_CAP)); continue
                en = zin.read(mem['English']) if 'English' in mem else None
                stp = os.path.join(dd, 'Scenes', 'Locations', zn.split('_')[0], zn)
                stz = zipfile.ZipFile(stp) if os.path.isfile(stp) else None
                stm = _loc_members(stz) if stz else {}
                new, info = {}, {}
                for lg, n in over.items():
                    rep = []
                    old = zin.read(n)
                    stock = stz.read(stm[lg]) if lg in stm else None
                    new[n] = fit(old, LOC_CAP, en, stock, rep)
                    info[lg] = (len(old), len(new[n]), rep, stock is not None)
                od = os.path.join(outdir, folder)
                os.makedirs(od, exist_ok=True)
                with zipfile.ZipFile(os.path.join(od, zn), 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zo:
                    for zi in zin.infolist():
                        data = new.get(zi.filename)
                        if data is None:
                            data = zin.read(zi.filename)
                        ni = zipfile.ZipInfo(zi.filename, zi.date_time)
                        ni.compress_type, ni.external_attr, ni.create_system = zi.compress_type, zi.external_attr, zi.create_system
                        zo.writestr(ni, data)
                lines.append('%s\\%s: %d .LOC member(s) fitted (stock reference %s)' % (
                    folder, zn, len(over), 'yes' if stz else 'no, key-name heuristic'))
                for lg, (a, b, rep, hasstock) in info.items():
                    lines.append('    %-9s %d -> %d (-%d)%s' % (lg, a, b, a - b, '' if hasstock else '  [heuristic ownership]'))
                    lines += ['        ' + r for r in rep]
                if stz:
                    stz.close()
            log('%s done' % folder)
    with open(os.path.join(outdir, 'fit_report.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return lines


def compare(built, stock):
    """What a built .LOC did to the stock leaves of its slot -> dict (2026-10-24, scheduled check-in; the check that found the
    heuristic's damage in the installed DD01-DD09 Russian files):
      stock_sound   stock leaves with a sound           missing      of those, gone from the built file (fit() must never do this)
      sid_changed   kept, but another sound id          blanked      kept, had a text, now has none (step 4 on a stock key: the bug)
      flags_changed kept, other flags                   swapped      kept, non-empty text that differs from stock (step 2 / 3:
                                                                     English subtitle; by design)
      ours          leaves the stock file does not have   plus the first few keys of each fault list (*_eg).
    A grafted Dead Men map re-points EVERY stock sound id to the joined .SND (kl_snd), so for those zips sid_changed ==
    stock_sound is the graft, not a fault; 'missing' there can be the slot map's own campaign one-liners whose sound the joined
    .SND no longer holds (seen: 86 L04/Dialogue leaves on the F02 / F04 slots) - NOT verified to be by design, say so."""
    bt, st = L.parse(built), L.parse(stock)
    r = dict(stub=bt is None or st is None)
    if r['stub']:
        return r
    o = {k: n for k, n in L.leaves(bt)}
    s = {k: n for k, n in L.leaves(st)}
    r['stock_sound'] = sum(1 for n in s.values() if n.flags & L.SOUND)
    r['ours'] = sum(1 for k in o if k not in s)
    missing, sid, flg, blank, swap = [], [], [], [], []
    for k, n in s.items():
        if not n.flags & L.SOUND:
            continue
        m = o.get(k)
        if m is None:
            missing.append(k); continue
        if m.flags != n.flags:
            flg.append(k)
        a, b = L.fields(n), L.fields(m)
        if a[2] != b[2]:
            sid.append(k)
        if a[0] and not b[0]:
            blank.append(k)
        elif a[0] and b[0] and a[0] != b[0]:
            swap.append(k)
    for name, lst in (('missing', missing), ('sid_changed', sid), ('flags_changed', flg), ('blanked', blank), ('swapped', swap)):
        r[name] = len(lst); r[name + '_eg'] = lst[:4]
    return r


def verify(dd=DD, langs=('Russian', 'Japanese'), log=print):
    """Read-only scan of <dd>\\KLExpansion\\Maps\\*\\*_Main.zip: compare() every .LOC member of the given languages with the stock
    .LOC of its slot (<dd>\\Scenes\\Locations\\F0n\\F0n_Main.zip; the F01 test slot has no stock file in place and is skipped).
    -> [(map folder, zip name, language, compare() dict)]; one line per member is logged."""
    maps = os.path.join(dd, 'KLExpansion', 'Maps')
    out = []
    for folder in sorted(os.listdir(maps)):
        for zn in sorted(os.listdir(os.path.join(maps, folder))):
            if not zn.lower().endswith('_main.zip'):
                continue
            stp = os.path.join(dd, 'Scenes', 'Locations', zn.split('_')[0], zn)
            if not os.path.isfile(stp) or zn.split('_')[0].upper() == 'F01':
                log('%s\\%s: no stock %s in place, skipped' % (folder, zn, zn.split('_')[0])); continue
            with zipfile.ZipFile(os.path.join(maps, folder, zn)) as zb, zipfile.ZipFile(stp) as zs:
                bm, sm = _loc_members(zb), _loc_members(zs)
                for lg in langs:
                    if lg not in bm or lg not in sm:
                        continue
                    r = compare(zb.read(bm[lg]), zs.read(sm[lg]))
                    out.append((folder, zn, lg, r))
                    if r.get('stub'):
                        log('%s\\%s %s: stub' % (folder, zn, lg)); continue
                    faults = [k for k in ('missing', 'blanked', 'flags_changed') if r[k]]
                    log('%s\\%s %-9s stock sound leaves %d: missing %d, blanked %d, flags changed %d, sound id changed %d, English text %d, ours %d%s' % (
                        folder, zn, lg, r['stock_sound'], r['missing'], r['blanked'], r['flags_changed'], r['sid_changed'], r['swapped'], r['ours'],
                        ('  FAULT ' + ', '.join('%s %s' % (k, r[k + '_eg'][:2]) for k in faults)) if faults else ''))
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--stage'] and len(a) == 2:
        os.makedirs(a[1], exist_ok=True)
        print('\n'.join(stage(a[1])))
    elif a[:1] == ['--verify']:
        verify(*a[1:2])
    elif a and os.path.isfile(a[0]):
        rd = lambda i: open(a[i], 'rb').read() if len(a) > i else None
        rep = []
        out = fit(rd(0), LOC_CAP, rd(1), rd(2), rep)
        print('\n'.join(rep) or 'already within the cap')
    else:
        print(__doc__)
