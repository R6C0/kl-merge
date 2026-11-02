"""
klkeys_text_test.py - key text and key collision test (2026-11-01, task T1; no game files, no build; no crash involved).

The table of the mod's keys is klhook/klkeys.c (klkeys_def: old default, Map=1 default, Ctrl flag per feature). The MOD CONTROLS shop page and the
hint line print their key names from that table at run time, so the C side cannot disagree with itself. What CAN disagree is the TEXT around it:
KLHook.ini prose and its commented [Keys] lines, tools/kl_mod_options.py labels, re/keybinds_ui_1028.md, and the one literal fallback in
klshoppage.c. This test parses the C sources and checks:

  1. the table parses (17 rows, ids in order) and every fallback / doc line names the table's key:
       - klshoppage.c hireKey fallback == the HIRE row's default;
       - KLHook.ini ';PageKey=114' ([Hire]) == HIRE, '[Keys] PageKey=F2' == the PageKey row, every ';<Name>=<key>' line under [Keys] == that row's Map=1 key;
       - the kl_mod_options 'hirepage' / 'controlspage' labels name the key the table gives;
       - no text in klhook/*.c|h, KLHook.ini, kl_mod_options.py or re/keybinds_ui_1028.md says "F12" for a mod key (F12 may appear only beside "Steam" /
         "screenshot" / "was" - the history of the move to F3); no mod key defaults to F12 at all;
  2. collisions, per scenario (A: the code defaults = Map=0 and the features whose switch defaults to 1 in klkeys_on_ini; B: the recommended state =
     Map=1 [kl_mod_options 'keysmap' is recommended on] and the features whose rows are recommended on; C: Map=1 with EVERY feature on; D: Map=0 with every feature on, notes only):
       - two features on one key with the same Ctrl flag; a key on ReShade's F7 / F8 / F10 (the repo's ReShade.ini shortcuts), Steam's F12, or one of Dog Days'
         own binds (klkeys_stock in klkeys.c + the extra ones of re/keybinds_ui_1028.md section 2), unless the row is stockOk or Ctrl-gated.
       Known clashes are listed in KNOWN (they are the old Map=0 keys the file's own header describes); a clash that is NOT in KNOWN fails the test, and a
       KNOWN entry that no longer happens is only noted. Scenario B and C must have NO clash that is not Ctrl-gated except the ones in KNOWN_B.
     Nothing here changes a default key or a 'recommended' state.

    python tools/klkeys_text_test.py          -> RESULT: PASS / FAIL (exit 0 / 1)
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import kl_mod_options as M

FAILS = []
NOTES = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        FAILS.append(what)


def note(what):
    print('note ' + what)
    NOTES.append(what)


def rd(*p):
    with open(os.path.join(ROOT, *p), encoding='utf-8', errors='replace') as f:
        return f.read()


# ---- key names (mirrors klkeys_parse / klkeys_name in klkeys.c) ----
NAMES = {'backspace': 8, 'tab': 9, 'enter': 13, 'pause': 0x13, 'esc': 27, 'space': 32, 'pageup': 33, 'pagedown': 34, 'end': 35, 'home': 36,
         'left': 37, 'up': 38, 'right': 39, 'down': 40, 'printscreen': 44, 'insert': 45, 'delete': 46, 'capslock': 0x14, 'numlock': 0x90,
         'scrolllock': 0x91}


def parse_key(s):
    """'Ctrl+F3' / '114' / '0x76' / 'End' / 'J' -> (vk, ctl) or None"""
    s = s.split(';')[0].strip()
    ctl = 0
    if s.lower().startswith('ctrl+'):
        ctl, s = 1, s[5:]
    if not s or s.lower() == 'none':
        return (0, ctl)
    m = re.fullmatch(r'[Ff](\d{1,2})', s)
    if m and 1 <= int(m.group(1)) <= 24:
        return (int(m.group(1)) + 0x6f, ctl)
    m = re.fullmatch(r'[Nn]um(\d)', s)
    if m:
        return (0x60 + int(m.group(1)), ctl)
    if re.fullmatch(r'[A-Za-z]', s):
        return (ord(s.upper()), ctl)
    if s.lower() in NAMES:
        return (NAMES[s.lower()], ctl)
    try:
        v = int(s, 0)
        return (v, ctl) if 0 <= v <= 0xfe else None
    except ValueError:
        return None


def key_name(vk, ctl=0):
    pre = 'Ctrl+' if ctl else ''
    if vk <= 0:
        return 'none'
    if 0x70 <= vk <= 0x87:
        return '%sF%d' % (pre, vk - 0x6f)
    if 0x60 <= vk <= 0x69:
        return '%sNum%d' % (pre, vk - 0x60)
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5a:
        return pre + chr(vk)
    for n, v in NAMES.items():
        if v == vk:
            return pre + {'pageup': 'PageUp', 'pagedown': 'PageDown'}.get(n, n.capitalize())
    return '%skey %02X' % (pre, vk)


# ---- the table ----
ROW = re.compile(r'\{\s*"(\w+)",\s*"([^"]+)",\s*"(\w+)",\s*"(\w+)",\s*(0x[0-9a-fA-F]+),\s*(0x[0-9a-fA-F]+),\s*(\d),\s*(\d),\s*"([^"]*)"', re.M)


def load_table(src):
    i = src.index('klkeys_def[KK_N]')
    j = src.index('};', i)
    rows = []
    for m in ROW.finditer(src[i:j]):
        rows.append(dict(name=m.group(1), label=m.group(2), sec=m.group(3), key=m.group(4), old=int(m.group(5), 16), new=int(m.group(6), 16),
                         newctl=int(m.group(7)), stock_ok=int(m.group(8)), scope=m.group(9)))
    return rows


def load_enum(src):
    m = re.search(r'enum\s*\{(.*?)\};', src, re.S)
    ids = re.findall(r'\b(KK_\w+)\b(?:\s*=\s*\w+)?', m.group(1))
    return [x for x in ids if x not in ('KK_N', 'KK_ROWS')]


def load_on_terms(src):
    """klkeys_on_ini: KK id -> python expression over 'T(sec,key,default)' terms"""
    i = src.index('static int klkeys_on_ini')
    j = src.index('#undef KKE', i)
    out = {}
    for m in re.finditer(r'((?:case\s+KK_\w+:\s*)+)return\s+(.*?);', src[i:j], re.S):
        ids = re.findall(r'KK_\w+', m.group(1))
        expr = m.group(2)
        for k in ids:
            out[k] = expr
    return out


def eval_on(expr, term_val):
    e = re.sub(r'KKE\("(\w+)",\s*"(\w+)",\s*(\d+)\)', lambda m: '1' if term_val(m.group(1), m.group(2), int(m.group(3))) else '0', expr)
    e = e.replace('&&', ' and ').replace('||', ' or ')
    return bool(eval(e, {'__builtins__': {}}, {}))


# ---- reserved keys ----
RESHADE = {0x76: 'ReShade F7 (previous preset)', 0x77: 'ReShade F8 (next preset)', 0x79: 'ReShade F10 (Uplift switch)'}   # re/keybinds_ui_1028.md section 3
STEAM = {0x7b: "Steam's F12 (screenshot)"}
STOCK_EXTRA = {ord('E'): 'use / climb', ord('Y'): 'point of interest', ord('T'): 'teammate info', ord('P'): 'pillpopping (shop only)', ord('X'): 'pulse check',
               ord('B'): 'briefing', ord('O'): 'objective', 0x09: 'scoreboard', 0x20: 'jump / vault'}    # md section 2 (compiled GameplayInput string)

# Known clashes: (scenario, label, what). Scenario A = the code defaults (Map=0). These are the OLD keys that [Keys] Map=1 exists to move; the file header of
# klkeys.c and re/keybinds_ui_1028.md section 3 list them. NOT changed here (the peer c9 owns the ship decision).
KNOWN = {
    ('A', 'UNSTICK', 'ReShade F7 (previous preset)'),                  # Unstick is on by default and keeps F7 with Map=0
}


def scenarios(rows, ids, on_expr, recs):
    """-> {scenario: [(row, vk, ctl, enabled)]}"""
    def sw_default(sec, key, d):
        return d != 0
    def sw_rec(sec, key, d):
        r = recs.get((sec, key))
        return (r == 'on') if r is not None else d != 0
    out = {}
    for sc, mapv, tv in (('A', 0, sw_default), ('B', 1, sw_rec), ('C', 1, lambda s, k, d: True), ('D', 0, lambda s, k, d: True)):
        L = []
        for i, r in enumerate(rows):
            vk, ctl = (r['new'], r['newctl']) if mapv else (r['old'], 0)
            if ctl and r['name'] not in ('HostMap', 'HostAI', 'HostPool'):
                ctl = 0                                                  # klkeys_init: Ctrl is honoured by the three host keys only
            L.append((r, vk, ctl, eval_on(on_expr[ids[i]], tv)))
        out[sc] = L
    return out


def clashes(L, stock):
    found = set()
    for a in range(len(L)):
        r, vk, ctl, on = L[a]
        if not on or vk <= 0:
            continue
        for b in range(a + 1, len(L)):
            r2, vk2, ctl2, on2 = L[b]
            if on2 and vk2 == vk and ctl2 == ctl and not (r['stock_ok'] and r2['stock_ok']):
                found.add((r['label'] + '|' + r2['label'], key_name(vk, ctl)))
        if ctl or r['stock_ok']:
            continue
        for tbl in (RESHADE, STEAM, stock):
            if vk in tbl:
                found.add((r['label'], tbl[vk]))
    return found


def main():
    ks = rd('klhook', 'klkeys.c')
    rows = load_table(ks)
    ids = load_enum(ks)
    on_expr = load_on_terms(ks)
    check(len(rows) == 17, 'klkeys_def has 17 rows (16 page rows + the page-cycle key); parsed %d' % len(rows))
    check(len(ids) == len(rows), 'enum ids (%d) == rows (%d)' % (len(ids), len(rows)))
    check(all(i in on_expr for i in ids), 'klkeys_on_ini covers every id (missing: %s)' % [i for i in ids if i not in on_expr])
    by = {r['name']: r for r in rows}
    stock = dict(STOCK_EXTRA)
    for m in re.finditer(r"\{\s*'(\w)',\s*\"([^\"]+)\"\s*\}", ks):
        stock[ord(m.group(1))] = m.group(2)

    # ---- 1. text vs table ----
    hire = by['Hire']
    check(hire['old'] == 0x72 and hire['new'] == 0x72 and hire['newctl'] == 0, 'HIRE PAGE default is F3 (0x72) in both maps, no Ctrl (table: %s / %s)' % (key_name(hire['old']), key_name(hire['new'])))
    sp = rd('klhook', 'klshoppage.c')
    m = re.search(r'kspg\.hireKey\s*=\s*(0x[0-9a-fA-F]+);', sp)
    check(bool(m) and int(m.group(1), 16) == hire['old'], 'klshoppage.c hireKey fallback == table default (%s)' % (m.group(1) if m else 'not found'))
    check(by['PageKey']['old'] == 0x71, 'NEXT SHOP PAGE (cycle key) default is F2 (0x71)')
    check(not any(r['old'] == 0x7b or (r['new'] == 0x7b and not r['newctl']) for r in rows), 'no mod key defaults to F12 (Steam screenshot key) in either map')

    ini = rd('klhook', 'KLHook.ini')
    sec = None
    seen = {}
    for ln in ini.splitlines():
        s = re.match(r'\[(\w+)\]', ln)
        if s:
            sec = s.group(1)
            continue
        if sec == 'Hire':
            m = re.match(r';?\s*PageKey\s*=\s*([^;\s]+)', ln)
            if m and ln.startswith(';PageKey='):
                seen['hire_pagekey'] = parse_key(m.group(1))
        if sec == 'Keys':
            m = re.match(r'PageKey\s*=\s*([^;\s]+)', ln)
            if m:
                seen['keys_pagekey'] = parse_key(m.group(1))
            m = re.match(r';(\w+)\s*=\s*([^;\s]+)', ln)
            if m and m.group(1) in by:
                seen['k_' + m.group(1)] = parse_key(m.group(2))
    check(seen.get('hire_pagekey') == (hire['old'], 0), 'KLHook.ini [Hire] ;PageKey= doc line == F3 (%s)' % (seen.get('hire_pagekey'),))
    check(seen.get('keys_pagekey') == (by['PageKey']['old'], 0), 'KLHook.ini [Keys] PageKey= == F2 (%s)' % (seen.get('keys_pagekey'),))
    n_doc = 0
    for k, v in seen.items():
        if k.startswith('k_'):
            r = by[k[2:]]
            n_doc += 1
            check(v == (r['new'], r['newctl'] if r['name'] in ('HostMap', 'HostAI', 'HostPool') else 0), 'KLHook.ini [Keys] ;%s= doc line == the Map=1 key of the table (%s)' % (k[2:], key_name(r['new'], r['newctl'])))
    check(n_doc >= 12, 'at least 12 commented [Keys] override lines were found (%d)' % n_doc)

    # kl_mod_options labels
    feats = {f['id']: f for f in M.F}
    check('F3' in feats['hirepage']['label'], "kl_mod_options 'hirepage' label names F3: %s" % feats['hirepage']['label'][:70])
    check('(recommended on)' in feats['hirepage']['label'], "'hirepage' label says (recommended on) (LC2 + SN1 PASS, cleared for the next ship)")
    check('F2' in feats['controlspage']['label'] and feats['controlspage']['rec'] == 'on', "'controlspage' label names F2 and is recommended on (LC2 + SN1 PASS)")
    check('Ctrl+F3' in feats['keysmap']['label'], "'keysmap' label names Ctrl+F3 (the host map key of Map=1)")

    # F12 text sweep: a line with F12 must carry the Steam / screenshot / history context
    files = []
    for d in ('klhook',):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(('.c', '.h', '.ini')) and fn != 'klauto.c':              # klauto.c's DIK table lists every F-key
                files.append(os.path.join(d, fn))
    files += [os.path.join('tools', 'kl_mod_options.py'), os.path.join('re', 'keybinds_ui_1028.md')]
    bad = []
    for fp in files:
        for no, ln in enumerate(rd(*fp.split(os.sep)).splitlines(), 1):
            if re.search(r'\bF12\b', ln) and not re.search(r'Steam|screenshot|\bwas\b|\bWas\b|F1-F12|F1\.\.F12|history', ln):
                bad.append('%s:%d' % (fp, no))
    check(not bad, 'every "F12" in klhook/*, kl_mod_options.py and re/keybinds_ui_1028.md is the Steam / screenshot / was-F12 note (offenders: %s)' % bad[:6])
    hint = re.findall(r'"\s*\[%s\]\s*hire"', sp)
    check(bool(hint), "the in-game hire hint is built from the key name ('[%s] hire'), not a literal key")
    check(not re.search(r'"[^"\n]*\bF\d+\s+hire\b', sp + rd('klhook', 'klannounce.c')), 'no literal "F<n> hire" string in klshoppage.c / klannounce.c')

    # ---- 2. collisions ----
    recs = {}
    for f in M.F:
        k0 = f['keys'][0]
        recs[(k0[0], k0[1])] = f['rec']
    check(feats['keysmap']['rec'] == 'on', "scenario B premise: 'keysmap' is recommended on (the recommended state is Map=1)")
    sc = scenarios(rows, ids, on_expr, recs)
    for name in sorted(sc):
        L = sc[name]
        if name == 'D':        # Map=0 with every feature on: information only (the old keys; what Map=1 fixes)
            for c in sorted(clashes(L, stock)):
                note('Map=0, every feature on: %s clashes on %s (Map=1 moves it)' % c)
            continue
        en = [r['label'] for (r, vk, ctl, on) in L if on]
        print('     scenario %s: %d feature(s) on: %s' % (name, len(en), ', '.join(en)))
        found = clashes(L, stock)
        unknown = sorted(c for c in found if (name,) + c not in KNOWN)
        check(not unknown, 'scenario %s: no clash outside KNOWN (found: %s)' % (name, unknown))
        for c in sorted(found):
            if (name,) + c in KNOWN:
                note('known clash in scenario %s: %s on %s' % (name, c[0], c[1]))
    for k in sorted(KNOWN):
        if k[0] != 'A':
            check(False, 'KNOWN may only list scenario A (the old Map=0 keys): %s' % (k,))
    allA = {(r['label'], vk, ctl) for (r, vk, ctl, on) in sc['A'] if on}
    check(('UNSTICK', 0x76, 0) in allA, 'sanity: scenario A has Unstick on F7 (the default-enabled feature)')
    # the Map=1 map itself is clean for every feature at once (scenario C), Ctrl-gated host keys excepted by the flag compare
    cl_c = clashes(sc['C'], stock)
    check(not cl_c, 'Map=1 with every feature on: no feature/feature, ReShade, Steam or stock-bind clash (found: %s)' % sorted(cl_c))

    print()
    print('%d note(s) (known old-key clashes), %d FAIL' % (len(NOTES), len(FAILS)))
    print('RESULT: ' + ('FAIL' if FAILS else 'PASS'))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
