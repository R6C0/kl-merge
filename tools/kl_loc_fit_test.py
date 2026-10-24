#!/usr/bin/env python3
r"""kl_loc_fit_test.py - self-test of kl_loc_fit.fit() on SYNTHETIC .LOC trees (no game files; 2026-10-24, scheduled check-in).

    python tools/kl_loc_fit_test.py          -> 'RESULT: PASS (0 checks failed)' / exit 1

kl_loc_fit shrinks a level .LOC that grew past kl_loc.LOC_CAP (the Dead Men voice leaves in Russian / Japanese files) in six
steps and is installed on the big Dead Men maps; until now its only test was the real data. This builds a 'Russian' file
(long texts), its English twin and the stock Dog Days file of the slot with kl_loc's own writer, then lowers the cap step
by step and checks, for every output:
  - it parses, round-trips byte for byte and is within the cap;
  - EVERY stock key is still there, with its flags and its sound id (fit() must never drop or silence a stock leaf);
  - each step touches only what its docstring says: step 1 our texts, 2 stock SOUND texts, 3 stock UI texts (never before 2),
    4 blanks our texts but keeps the voice, 5 drops K_C1..K_C9 only while K stays, 6 drops our leaves and nothing stock;
  - a file within the cap or a stub comes back unchanged; an impossible cap raises ValueError;
  - the key-name heuristic (no stock file given) treats KLVoice/, KLTalk/ and _C<n> as ours and nothing else;
  - when nothing of ours fits, every our leaf goes, the emptied KLVoice/ and KLTalk/ tables are pruned and the output IS the
    stock file byte for byte (the drop estimates do not count table nodes; fit()'s second pass is the safety net for that -
    not provoked here: on these trees the first pass's estimate already lands under the cap).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_loc as L
import kl_loc_fit as F

FAILS = []


def check(ok, what):
    print('  %-5s %s' % ('ok' if ok else 'FAIL', what))
    if not ok:
        FAILS.append(what)


def T(name, kids):
    return L.Node(name, L.TABLE, kids)


def mk(long):
    """-> (tree, English tree, stock tree). long: this language's stock texts are longer than English (Russian / Japanese)"""
    def ru(t):
        return t + (b' \xd0\xb4\xd0\xbb\xd0\xb8\xd0\xbd\xd0\xbd\xd0\xb5\xd0\xb5' if long else b'')
    stock = lambda: [
        T(b'Menu', [L.leaf(b'Options', ru(b'Options'), 0), L.leaf(b'Quit', ru(b'Quit game'), 0), L.leaf(b'Empty', b'', 0)]),
        T(b'Multiplayer', [T(b'F01', [L.leaf(b'ExitLootArea_01_C%d' % i, ru(b'Get to the exit'), 0x1000 + i) for i in range(1, 10)]
                           + [L.leaf(b'Backstab_01', ru(b'Traitor!'), 0x2000)])]),
    ]
    en_stock = [
        T(b'Menu', [L.leaf(b'Options', b'Options', 0), L.leaf(b'Quit', b'Quit game', 0), L.leaf(b'Empty', b'', 0)]),
        T(b'Multiplayer', [T(b'F01', [L.leaf(b'ExitLootArea_01_C%d' % i, b'Get to the exit', 0x1000 + i) for i in range(1, 10)]
                           + [L.leaf(b'Backstab_01', b'Traitor!', 0x2000)])]),
    ]
    ours = lambda txt_long: [
        T(b'KLVoice', [T(b'Kane', [L.leaf(b'Backstab_%02d' % i, b'Dead Men line number %d, ' % i + txt_long, 0x3000 + i) for i in range(1, 7)]
                       + [L.leaf(b'TextOnly', b'a line with no sound ' + txt_long, 0)])]),
        T(b'KLTalk', [L.leaf(b'Lone', b'the only leaf of its table ' + txt_long, 0x4000)]),
    ]
    tree = stock() + ours(b'in a long translation' if long else b'in English')
    # our aliases K_C1..K_C9 of a key the stock file does not have, beside their base key (kl_loc.aliases' shape)
    f01 = tree[1].kids[0].kids
    L._insert(f01, L.leaf(b'FA_Drop_Cash', b'Drop the cash', 0x5000))
    for i in range(1, 10):
        L._insert(f01, L.leaf(b'FA_Drop_Cash_C%d' % i, b'Drop the cash', 0x5000))
    en = en_stock + ours(b'in English')
    f01 = en[1].kids[0].kids
    L._insert(f01, L.leaf(b'FA_Drop_Cash', b'Drop the cash', 0x5000))
    for i in range(1, 10):
        L._insert(f01, L.leaf(b'FA_Drop_Cash_C%d' % i, b'Drop the cash', 0x5000))
    return tree, en, stock()


def info(data):
    """-> {key: (flags, text, sid)}"""
    return {k: (n.flags, L.fields(n)[0], L.fields(n)[2]) for k, n in L.leaves(L.parse(data))}


def invariants(out, cap, stock_b, label):
    t = L.parse(out)
    check(t is not None and L.build(t) == out, '%s: output parses and round-trips' % label)
    check(len(out) <= cap, '%s: %d bytes <= cap %d' % (label, len(out), cap))
    s, o = info(stock_b), info(out)
    missing = [k for k in s if k not in o]
    check(not missing, '%s: every stock key kept (%s)' % (label, missing[:3] or 'all'))
    bad = [k for k in s if k in o and (o[k][0] != s[k][0] or o[k][2] != s[k][2])]
    check(not bad, '%s: stock flags and sound ids unchanged (%s)' % (label, bad[:3] or 'all'))
    return o


def run(tree, en, stock, cap, label, stock_given=True):
    data, en_b, st_b = L.build(tree), L.build(en), L.build(stock)
    rep = []
    out = F.fit(data, cap, en_b, st_b if stock_given else None, rep)
    print('  %s: %d -> %d (cap %d); %s' % (label, len(data), len(out), cap, ' | '.join(rep)))
    return data, out, rep, st_b


def main():
    tree, en, stock = mk(long=True)
    full = L.build(tree)
    before = info(full)
    print('synthetic: %d bytes, %d leaves (%d stock)' % (len(full), len(before), len(info(L.build(stock)))))

    # 0. within the cap / stub: unchanged
    check(F.fit(full, len(full), L.build(en), L.build(stock)) is full, 'a file within the cap comes back as the same object')
    check(F.fit(b'\x01x\x00\x08\0\0\0\0', 4) == b'\x01x\x00\x08\0\0\0\0', 'a stub (<= 9 bytes) is returned as it is')

    # 1. a few bytes over: only OUR texts go English
    our_gain = sum(len(before[k][1]) - len(info(L.build(en))[k][1]) for k in before if k.startswith('KLVoice/') or k.startswith('KLTalk/'))
    cap1 = len(full) - 1
    data, out, rep, st_b = run(tree, en, stock, cap1, 'step 1')
    o = invariants(out, cap1, st_b, 'step 1')
    check(rep and rep[0].startswith('1 our keys'), 'step 1: the report starts with step 1')
    check(all(o[k] == before[k] for k in before if not (k.startswith('KLVoice/') or k.startswith('KLTalk/'))),
          'step 1: no stock leaf changed')
    check(any(o[k][1] != before[k][1] for k in before if k.startswith('KLVoice/')), 'step 1: an our leaf took the English text')
    check(all(o[k][2] == before[k][2] for k in o if k in before), 'step 1: every kept leaf keeps its sound id')

    # 2. stock SOUND texts next; the UI strings (Menu/) stay long
    cap2 = len(full) - our_gain - 10
    data, out, rep, st_b = run(tree, en, stock, cap2, 'step 2')
    o = invariants(out, cap2, st_b, 'step 2')
    check(any(r.startswith('2 stock keys with a sound') for r in rep) and not any(r.startswith('3 ') for r in rep),
          'step 2: sound subtitles shortened, UI strings not yet')
    check(all(o[k][1] == before[k][1] for k in before if k.startswith('Menu/')), 'step 2: Menu/ texts untouched')
    changed = [k for k in before if k.startswith('Multiplayer/F01/ExitLootArea') and o[k][1] != before[k][1]]
    check(changed and all(o[k][1] == b'Get to the exit' for k in changed), 'step 2: a shortened subtitle is the English one')

    # 3. then the UI strings
    snd_gain = sum(len(before[k][1]) - len(info(L.build(en))[k][1]) for k in before if before[k][2] and k.startswith('Multiplayer/'))
    cap3 = len(full) - our_gain - snd_gain - 4
    data, out, rep, st_b = run(tree, en, stock, cap3, 'step 3')
    o = invariants(out, cap3, st_b, 'step 3')
    check(any(r.startswith('3 stock keys without a sound') for r in rep), 'step 3: UI strings shortened')
    check(o['Menu/Quit'][1] in (b'Quit game', before['Menu/Quit'][1]) and o['Menu/Empty'] == before['Menu/Empty'], 'step 3: English text taken, the empty one left')
    check(not any(r.startswith('4 ') for r in rep), 'step 3: nothing of ours blanked yet')

    # 4. blank our texts, voice kept
    en_full = info(L.build(en))
    ui_gain = sum(len(before[k][1]) - len(en_full[k][1]) for k in before if k.startswith('Menu/'))
    cap4 = len(full) - our_gain - snd_gain - ui_gain - 30
    data, out, rep, st_b = run(tree, en, stock, cap4, 'step 4')
    o = invariants(out, cap4, st_b, 'step 4')
    check(any(r.startswith('4 our keys: text blanked') for r in rep), 'step 4: our texts blanked')
    blanked = [k for k in o if k.startswith(('KLVoice/', 'KLTalk/')) and o[k][1] == b'']
    check(blanked and all(o[k][2] == before[k][2] and o[k][0] & L.SOUND for k in blanked), 'step 4: a blanked leaf keeps flags and sound id')
    check(o.get('KLVoice/Kane/TextOnly', (0, b'x', 0))[1] != b'', 'step 4: a text-only leaf of ours is not blanked (left for step 6)')
    check(not any(r.startswith('5 ') or r.startswith('6 ') for r in rep), 'step 4: no leaf dropped yet')

    # 5. aliases K_C1..K_C9 go, the base key stays
    ours_text = sum(len(before[k][1]) for k in before if before[k][2] and (k.startswith('KLVoice/') or k.startswith('KLTalk/')))
    cap5 = len(full) - our_gain - snd_gain - ui_gain - ours_text - 60
    data, out, rep, st_b = run(tree, en, stock, cap5, 'step 5')
    o = invariants(out, cap5, st_b, 'step 5')
    check(any(r.startswith('5 our alias duplicates') for r in rep), 'step 5: aliases dropped')
    gone = [i for i in range(1, 10) if 'Multiplayer/F01/FA_Drop_Cash_C%d' % i not in o]
    check(gone and 'Multiplayer/F01/FA_Drop_Cash' in o, 'step 5: %d alias(es) gone, the base key kept' % len(gone))
    check(all('Multiplayer/F01/ExitLootArea_01_C%d' % i in o for i in range(1, 10)), 'step 5: the STOCK _C<n> leaves are not aliases of ours')
    check(not any(r.startswith('6 ') for r in rep), 'step 5: no whole leaf of ours dropped yet')

    # 6. last resort: our leaves go, biggest first, stock stays whole
    st_only = len(L.build(stock))
    cap6 = st_only + 40
    data, out, rep, st_b = run(tree, en, stock, cap6, 'step 6')
    o = invariants(out, cap6, st_b, 'step 6')
    check(any(r.startswith('6 our leaves dropped') for r in rep), 'step 6: our leaves dropped')
    check('KLVoice/Kane/TextOnly' not in o, 'step 6: the biggest leaf of ours (the text-only one) went first')
    check(len([k for k in o if k in before and not k.startswith(('KLVoice/', 'KLTalk/')) and '_Drop_Cash' not in k]) == len(info(st_b)),
          'step 6: the stock leaf count is unchanged')
    check(rep[-1].startswith('result:'), 'the report ends with the result line')
    # 6b. room for nothing of ours: every our leaf goes, the emptied KLVoice/ and KLTalk/ tables are pruned, and the drop
    # estimates (which do not count the table nodes) are corrected by the second pass; what is left is the stock file itself
    # (on trees whose stock texts are already English-length, so the stock part cannot shrink and make room)
    tree2, en2, stock2 = mk(long=False)
    cap6b = len(L.build(stock2)) + 10
    data, out, rep, st_b = run(tree2, en2, stock2, cap6b, 'step 6b')
    o = invariants(out, cap6b, st_b, 'step 6b')
    check(not any(k.startswith(('KLVoice/', 'KLTalk/')) for k in o), 'step 6b: no leaf of ours left, the emptied tables pruned')
    check(out == st_b, 'step 6b: the output IS the stock file, byte for byte' if out == st_b
          else 'step 6b: output differs from the stock file by %d bytes' % (len(out) - len(st_b)))

    # 7. impossible: smaller than the stock file can get
    try:
        F.fit(full, st_only - 200, L.build(en), L.build(stock))
        check(False, 'impossible cap raises ValueError')
    except ValueError as e:
        check('cannot fit' in str(e), 'impossible cap raises ValueError (%s)' % str(e)[:40])

    # 8. ownership heuristic without a stock file (how kl_dmvoice calls fit): KLVoice/, KLTalk/ and an alias K_C<n> WITH its base
    # key K are ours; a stock per-character line K_C1..K_C9 (no base key) and every other key count as stock
    data, out, rep, st_b = run(tree, en, stock, cap6, 'heuristic', stock_given=False)
    o = invariants(out, cap6, st_b, 'heuristic')
    check(rep and rep[0].startswith('1 our keys: English text: 8 leaves'), 'heuristic: step 1 took the 8 KLVoice/KLTalk leaves, not the stock _C<n> ones')
    check(all(o['Multiplayer/F01/ExitLootArea_01_C%d' % i] == (before['Multiplayer/F01/ExitLootArea_01_C%d' % i][0], b'Get to the exit', 0x1000 + i)
              for i in range(1, 10)), 'heuristic: the stock _C<n> lines were only shortened to English (step 2), sound kept')
    keys = {'multiplayer/f01/fa_drop_cash', 'multiplayer/f01/fa_drop_cash_c1', 'multiplayer/f01/exitlootarea_01_c3', 'menu/quit'}
    check(F._is_ours('Multiplayer/F01/FA_Drop_Cash_C1', None, keys) and not F._is_ours('Multiplayer/F01/ExitLootArea_01_C3', None, keys)
          and not F._is_ours('Menu/Quit', None, keys) and not F._is_ours('Multiplayer/F01/FA_Drop_Cash', None, keys),
          'heuristic: K_C<n> is ours only beside its base key K; K itself and Menu/Quit are not')
    check(F._is_ours('Multiplayer/F01/ExitLootArea_01_C3', None), 'heuristic without the key set: the old, looser rule')
    check(F._is_ours('Menu/Quit', {'menu/options'}) and not F._is_ours('Menu/Options', {'menu/options'}), 'with a stock list: only a key the stock lacks is ours')
    # 8b. heuristic at the tightest cap on the same-length trees: every stock leaf survives; what the heuristic cannot see as ours
    # (the base key FA_Drop_Cash, a flag-0 key of ours) stays too, so the result is the stock file plus that one leaf
    exp = mk(long=False)[2]
    L._insert(exp[1].kids[0].kids, L.leaf(b'FA_Drop_Cash', b'Drop the cash', 0x5000))
    cap8 = len(L.build(exp)) + 4
    data, out, rep, st_b = run(tree2, en2, stock2, cap8, 'heuristic, tightest', stock_given=False)
    invariants(out, cap8, st_b, 'heuristic, tightest')
    check(out == L.build(exp), 'heuristic, tightest: output = the stock file + our one base key, byte for byte (no stock _C<n> leaf dropped)')

    # 9. a language that is NOT longer than English (Polish-like): steps 1-3 find nothing, step 4 starts at once
    full2 = L.build(tree2)
    data, out, rep, st_b = run(tree2, en2, stock2, len(full2) - 20, 'same-length language')
    invariants(out, len(full2) - 20, st_b, 'same-length language')
    check(rep and rep[0].startswith('4 '), 'same-length language: no text swap possible, blanking is the first step taken')

    # 10. compare(): the read-only check of a built file against its slot's stock file (what --verify runs on the installed zips)
    st_b = L.build(stock)
    c = F.compare(st_b, st_b)
    check(not c['stub'] and c['stock_sound'] == 10 and c['missing'] == c['blanked'] == c['sid_changed'] == c['flags_changed'] == c['swapped'] == 0
          and c['ours'] == 0, 'compare: the stock file against itself is clean (10 sound leaves)')
    data, out, rep, st_b = run(tree, en, stock, cap2, 'compare, step-2 output')
    c = F.compare(out, st_b)
    check(c['missing'] == c['blanked'] == c['sid_changed'] == c['flags_changed'] == 0 and c['swapped'] > 0 and c['ours'] > 0,
          'compare: a fit() output shows only English subtitles (swapped %d) and our leaves (%d), no fault' % (c['swapped'], c['ours']))
    bad = L.parse(st_b)
    f01 = bad[1].kids[0].kids
    for n in f01:
        if n.name == b'ExitLootArea_01_C2':
            n.raw = b'\0' + n.raw[n.raw.index(b'\0') + 1:]                  # the bug's step-4 damage: subtitle blanked, voice kept
        if n.name == b'ExitLootArea_01_C3':
            n.raw = n.raw[:-4] + struct.pack('<I', 0x9999)                 # another sound id
    f01[:] = [n for n in f01 if n.name != b'ExitLootArea_01_C4']            # a dropped stock sound leaf
    c = F.compare(L.build(bad), st_b)
    check(c['missing'] == 1 and c['missing_eg'] == ['Multiplayer/F01/ExitLootArea_01_C4'] and c['blanked'] == 1
          and c['blanked_eg'] == ['Multiplayer/F01/ExitLootArea_01_C2'] and c['sid_changed'] == 1
          and c['sid_changed_eg'] == ['Multiplayer/F01/ExitLootArea_01_C3'] and c['swapped'] == 0,
          'compare: a dropped, a blanked and a re-pointed stock sound leaf are each found and named')
    check(F.compare(b'\x01x\x00\x08\0\0\0\0', st_b)['stub'], 'compare: a stub is reported as such')

    print('RESULT: %s (%d checks failed)' % ('PASS' if not FAILS else 'FAIL', len(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
