#!/usr/bin/env python3
"""
Kane & Lynch: Dead Men -> Dog Days port checker
================================================

Reads both games' level archives (read-only, nothing is modified) and reports,
for every Dead Men level, what would break if it were loaded in Dog Days:

  * entity classes used by the level (from the .gms scene file) and whether
    Dog Days still has each class, plus its in-memory size in both games
  * controllers attached to entities (from the .prp property file) and whether
    their saved field layout matches what Dog Days levels use
  * whether the level's entities use the Dead Men base-class layout
    (Dog Days added one bool field to every entity, so all DM levels need it)

Only needs Python 3.8+ (no extra packages). Run:

    python kl_port_check.py                    (auto-finds both games)
    python kl_port_check.py "<Dead Men folder>" "<Dog Days folder>"

Output goes to a "report" folder next to this script:
    report.html, levels.csv, entity_classes.csv, controllers.csv
"""
import collections, csv, html, json, os, re, struct, sys, time, zipfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
DM_GUESSES = [os.path.dirname(HERE),
              r"G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men",
              r"C:\Program Files (x86)\Steam\steamapps\common\Kane and Lynch Dead Men",
              r"C:\Steam\steamapps\common\Kane and Lynch Dead Men"]
DD_GUESSES = [r"C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days",
              r"G:\SteamLibrary\steamapps\common\Kane & Lynch 2 - Dog Days",
              r"C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"]
DM_EXE, DD_EXE = "kaneandlynch.exe", "kl2.exe"


# ---------------------------------------------------------------- executables
def pe_va2off(d):
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    base = struct.unpack_from('<I', d, pe + 24 + 28)[0]
    secs = []
    for i in range(nsec):
        o = pe + 24 + optsz + 40 * i
        vsz, va, rsz, rptr = struct.unpack_from('<IIII', d, o + 8)
        secs.append((va, max(vsz, rsz), rptr))
    def va2off(v):
        rva = v - base
        for va, sz, rp in secs:
            if va <= rva < va + sz:
                return rp + rva - va
        return None
    return va2off

# push 0; push SIZE; push 0; push NAME; lea ecx,[esp+x]; call init; lea eax,[esp]; push eax; push TYPEID; mov ecx,REGISTRY
CLASS_REG = re.compile(rb'\x6a\x00(?:\x6a(.)|\x68(....))\x6a\x00\x68(....)\x8d\x4c\x24.\xe8....'
                       rb'\x8d\x04\x24\x50\x68(....)\xb9', re.S)

def exe_classes(path):
    d = open(path, 'rb').read()
    va2off = pe_va2off(d)
    out = {}
    for m in CLASS_REG.finditer(d):
        size = m.group(1)[0] if m.group(1) else struct.unpack('<I', m.group(2))[0]
        o = va2off(struct.unpack('<I', m.group(3))[0])
        if o is None:
            continue
        e = d.find(b'\0', o, o + 100)
        name = d[o:e]
        if e > o and all(32 < c < 127 for c in name):
            out[struct.unpack('<I', m.group(4))[0]] = (name.decode(), size)
    return out, d


# ---------------------------------------------------------------- .prp (IOPacked v0.1)
FIXED = {0x01: 4, 0x04: 4, 0x05: 1, 0x06: 1, 0x07: 1, 0x08: 2, 0x09: 4, 0x0a: 4,
         0x0b: 8, 0x0c: 4, 0x0e: 4}
LETTER = {0x04: 'i', 0x05: 'c', 0x06: 'b', 0x07: 'B', 0x08: 'h', 0x09: 'I', 0x0a: 'f',
          0x0b: 'd', 0x0c: 's', 0x0e: 'e', 0x0d: 'r', 0x0f: 'k'}

def prp_tokens(d):
    if not d.startswith(b'IOPacked v0.1'):
        raise ValueError('not an IOPacked v0.1 file')
    _flags, _z, _n, off = struct.unpack_from('<IIII', d, 15)
    keys = [k.decode('latin1') for k in d[0x1f:off + 0x1f].split(b'\0')]
    pos, end = off + 0x1f + 4, len(d)
    toks = []
    ap = toks.append
    while pos < end:
        op = d[pos]; p = pos + 1
        if op in FIXED:
            n = FIXED[op]; pos = p + n
            if op in (0x0c, 0x0e) or op in (0x01, 0x04):
                ap((op, struct.unpack_from('<I', d, p)[0]))
            else:
                ap((op, None))
        elif op == 0x0d:
            pos = p + 4 + struct.unpack_from('<I', d, p)[0]; ap((op, None))
        elif op == 0x0f:
            pos = p + 4 + 4 * struct.unpack_from('<I', d, p)[0]; ap((op, None))
        elif op in (0x02, 0x7c, 0x7e):
            pos = p; ap((op, None))
        elif op == 0x7f:
            break
        else:
            raise ValueError('unknown opcode %#x at %#x' % (op, pos))
    return toks, keys

def obj_sig(toks, i):
    """toks[i] is the first token inside '{'. Returns (normalised signature, index after '}')."""
    out = []
    while True:
        op, v = toks[i]
        if op == 0x7e:
            return ''.join(out), i + 1
        if op == 0x02:
            s, i = obj_sig(toks, i + 1); out.append('{' + s + '}'); continue
        if op == 0x01:                       # array: keep element type, drop length
            j, depth = i + 1, 1
            first = ''
            while depth:
                o2 = toks[j][0]
                if o2 == 0x01: depth += 1
                elif o2 == 0x7c: depth -= 1
                elif not first and depth == 1: first = '{' if o2 == 0x02 else LETTER.get(o2, '?')
                j += 1
            out.append('[' + first + '*]'); i = j; continue
        out.append(LETTER.get(op, '?')); i += 1

def parse_prp(d):
    toks, keys = prp_tokens(d)
    i = 0
    while toks[i][0] != 0x02:
        i += 1
    nodes, ctrls = [], []
    stack = [1]
    while stack:
        if stack[-1] == 0:
            stack.pop(); continue
        stack[-1] -= 1
        assert toks[i][0] == 0x02, 'tree desync'
        sig, i = obj_sig(toks, i + 1)
        op, nc = toks[i]; i += 1
        for _ in range(nc):
            _, k = toks[i]; name = keys[k]
            csig, i = obj_sig(toks, i + 2)
            ctrls.append((name, csig))
        op, nch = toks[i]; i += 1
        nodes.append(sig)
        stack.append(nch)
    return nodes, ctrls

DM_BASE = re.compile(r'^e\[f\*\]\[f\*\]bI(?!b)')     # Dead Men ZGEOM base
DD_BASE = re.compile(r'^e\[f\*\]\[f\*\]bIb')         # Dog Days: extra bool after the int


# ---------------------------------------------------------------- .gms
def gms_types(b):
    raw = zlib.decompressobj(-15).decompress(b[9:])
    h = struct.unpack_from('<16I', raw, 0)
    types = collections.Counter()
    o = h[4]; n = struct.unpack_from('<I', raw, o)[0]
    for k in range(n):
        tid, cnt, _ = struct.unpack_from('<III', raw, o + 4 + 12 * k); types[tid] += cnt
    return types


# ---------------------------------------------------------------- level scanning
def level_zips(game):
    root = os.path.join(game, 'Scenes')
    for dp, _dn, fn in os.walk(root):
        for f in sorted(fn):
            if f.lower().endswith('.zip'):
                z = os.path.join(dp, f)
                bak = os.path.join(game, 'KL_PortBackup', os.path.relpath(z, game))
                yield bak if os.path.isfile(bak) else z    # never learn from our own installs

def read_level(path):
    with zipfile.ZipFile(path) as z:
        prp = [n for n in z.namelist() if n.lower().endswith('.prp')]
        gms = [n for n in z.namelist() if n.lower().endswith('.gms')]
        if not prp:
            return None
        nodes, ctrls = parse_prp(z.read(prp[0]))
        types = gms_types(z.read(gms[0])) if gms else collections.Counter()
    return nodes, ctrls, types

def short(path, game):
    return os.path.relpath(path, os.path.join(game, 'Scenes')).replace('\\', '/')


def find(guesses, exe):
    for g in guesses:
        if g and os.path.isfile(os.path.join(g, exe)):
            return g
    return None

def workdir():
    """Where converted levels and build files live: the KL_PortTools folder inside Dead Men when
    it exists (it holds the converted textures, models and merged audio), else next to the scripts."""
    dm = find(DM_GUESSES, DM_EXE)
    w = os.path.join(dm, 'KL_PortTools') if dm else None
    return w if w and os.path.isdir(w) else HERE

def main():
    a = sys.argv[1:]
    dm = a[0] if len(a) > 0 else find(DM_GUESSES, DM_EXE)
    dd = a[1] if len(a) > 1 else find(DD_GUESSES, DD_EXE)
    while not dm or not os.path.isfile(os.path.join(dm, DM_EXE)):
        dm = input('Path to Kane & Lynch: Dead Men folder: ').strip().strip('"')
    while not dd or not os.path.isfile(os.path.join(dd, DD_EXE)):
        dd = input('Path to Kane & Lynch 2: Dog Days folder: ').strip().strip('"')
    print('Dead Men :', dm); print('Dog Days :', dd)
    t0 = time.time()

    dm_cls, dm_bin = exe_classes(os.path.join(dm, DM_EXE))
    dd_cls, dd_bin = exe_classes(os.path.join(dd, DD_EXE))
    print('classes registered: Dead Men %d, Dog Days %d' % (len(dm_cls), len(dd_cls)))

    # Dog Days reference: every controller layout used by any DD level
    dd_ctrl = collections.defaultdict(collections.Counter)
    dd_zips = list(level_zips(dd))
    for n, p in enumerate(dd_zips, 1):
        print('\r  reading Dog Days levels %d/%d' % (n, len(dd_zips)), end='', flush=True)
        try:
            r = read_level(p)
        except Exception as e:
            print('\n  ! skipped', short(p, dd), e); continue
        if r:
            for name, sig in r[1]:
                dd_ctrl[name][sig] += 1
    print()

    def in_exe(blob, name):
        return (b'\0' + name.encode() + b'\0') in blob

    levels, cls_rows, ctrl_rows = [], [], []
    dm_zips = list(level_zips(dm))
    for n, p in enumerate(dm_zips, 1):
        print('\r  checking Dead Men levels %d/%d' % (n, len(dm_zips)), end='', flush=True)
        try:
            r = read_level(p)
        except Exception as e:
            print('\n  ! skipped', short(p, dm), e); continue
        if not r:
            continue
        nodes, ctrls, types = r
        lv = short(p, dm)
        dm_base = sum(1 for s in nodes if DM_BASE.match(s))
        missing_cls = changed_cls = 0
        for tid, cnt in sorted(types.items(), key=lambda x: -x[1]):
            name, dsz = dm_cls.get(tid, ('?%#x' % tid, None))
            ddc = dd_cls.get(tid)
            if ddc is None:
                status = 'MISSING in Dog Days'; missing_cls += 1
            elif ddc[1] != dsz:
                status = 'size changed'; changed_cls += 1
            else:
                status = 'same size'
            cls_rows.append([lv, name, '%#x' % tid, cnt, dsz, ddc[1] if ddc else '', status])
        cc = collections.defaultdict(collections.Counter)
        for name, sig in ctrls:
            cc[name][sig] += 1
        bad_ctrl = 0
        for name, sigs in sorted(cc.items(), key=lambda x: -sum(x[1].values())):
            total = sum(sigs.values())
            ref = dd_ctrl.get(name)
            if ref:
                unmatched = sum(c for s, c in sigs.items() if s not in ref)
                status = 'same layout' if not unmatched else 'layout changed (%d/%d)' % (unmatched, total)
            elif in_exe(dd_bin, name):
                status = 'in Dog Days exe, unused by its levels'; unmatched = 0
            elif in_exe(dm_bin, name):
                status = 'MISSING in Dog Days'; unmatched = total
            else:
                status = 'not seen in Dog Days'; unmatched = total
            if unmatched:
                bad_ctrl += 1
            ctrl_rows.append([lv, name, total, status,
                              sigs.most_common(1)[0][0][:120],
                              (ref.most_common(1)[0][0][:120] if ref else '')])
        levels.append(dict(level=lv, entities=len(nodes), controllers=len(ctrls),
                           dm_base=dm_base, classes=len(types), missing_classes=missing_cls,
                           changed_classes=changed_cls, ctrl_types=len(cc), bad_ctrl_types=bad_ctrl))
    print()

    out = os.path.join(HERE, 'report'); os.makedirs(out, exist_ok=True)
    def wcsv(fn, head, rows):
        with open(os.path.join(out, fn), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(head); w.writerows(rows)
    wcsv('levels.csv', list(levels[0].keys()) if levels else [], [list(l.values()) for l in levels])
    wcsv('entity_classes.csv', ['level', 'class', 'type_id', 'count', 'dm_size', 'dd_size', 'status'], cls_rows)
    wcsv('controllers.csv', ['level', 'controller', 'count', 'status', 'dm_layout', 'dd_layout'], ctrl_rows)
    write_html(out, dm, dd, dm_cls, dd_cls, levels, cls_rows, ctrl_rows)
    print('done in %.0fs -> %s' % (time.time() - t0, os.path.join(out, 'report.html')))


def write_html(out, dm, dd, dm_cls, dd_cls, levels, cls_rows, ctrl_rows):
    e = html.escape
    # aggregate across all levels
    agg_cls = {}
    for lv, name, tid, cnt, dsz, ddsz, st in cls_rows:
        a = agg_cls.setdefault(name, [tid, 0, set(), dsz, ddsz, st]); a[1] += cnt; a[2].add(lv)
    agg_ctrl = {}
    for lv, name, cnt, st, dml, ddl in ctrl_rows:
        a = agg_ctrl.setdefault(name, [0, set(), set(), dml, ddl]); a[0] += cnt; a[1].add(lv); a[2].add(st)
    def badge(st):
        k = 'bad' if 'MISSING' in st or 'not seen' in st else 'warn' if 'changed' in st else 'ok'
        return '<span class="b %s">%s</span>' % (k, e(st))
    rows_l = ''.join('<tr><td>%s</td><td>%d</td><td>%d</td><td>%d%%</td><td>%d</td><td>%d</td><td>%d</td></tr>' % (
        e(l['level']), l['entities'], l['controllers'],
        round(100 * l['dm_base'] / max(1, l['entities'])), l['missing_classes'], l['changed_classes'],
        l['bad_ctrl_types']) for l in levels)
    rows_c = ''.join('<tr><td>%s</td><td><code>%s</code></td><td>%d</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        e(n), a[0], a[1], len(a[2]), a[3], a[4], badge(a[5]))
        for n, a in sorted(agg_cls.items(), key=lambda x: ('MISSING' not in x[1][5], -x[1][1])))
    def worst(sts):
        for k in ('MISSING', 'not seen', 'changed'):
            for s in sts:
                if k in s: return s
        return sorted(sts)[0]
    rows_k = ''.join('<tr><td>%s</td><td>%d</td><td>%d</td><td>%s</td><td><code>%s</code></td><td><code>%s</code></td></tr>' % (
        e(n), a[0], len(a[1]), badge(worst(a[2])), e(a[3][:60]), e(a[4][:60]))
        for n, a in sorted(agg_ctrl.items(), key=lambda x: (('MISSING' not in worst(x[1][2]) and 'not seen' not in worst(x[1][2]), 'changed' not in worst(x[1][2])), -x[1][0])))
    tot_e = sum(l['entities'] for l in levels); tot_b = sum(l['dm_base'] for l in levels)
    miss_c = sorted(n for n, a in agg_cls.items() if 'MISSING' in a[5])
    miss_k = sorted(n for n, a in agg_ctrl.items() if any('MISSING' in s or 'not seen' in s for s in a[2]))
    chg_k = sorted(n for n, a in agg_ctrl.items() if any('changed' in s for s in a[2]) and n not in miss_k)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>K&amp;L Port Check</title><style>
:root{{--bg:#fafaf8;--fg:#1d1d1b;--mut:#6b6b66;--line:#e2e1dc;--ok:#2f7d4f;--warn:#a86b00;--bad:#b3261e;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--fg:#ecebe6;--mut:#9a9993;--line:#2c2b29;--ok:#6cc58f;--warn:#e0a23a;--bad:#ef6b62;--card:#1c1c1a}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,sans-serif;margin:0;padding:24px 16px}}
main{{max-width:1100px;margin:auto}} h1{{font-size:24px;margin:0 0 4px}} h2{{font-size:18px;margin:32px 0 8px}}
.m{{color:var(--mut)}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}} .card b{{font-size:22px;display:block}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}
th{{position:sticky;top:0;background:var(--card)}} code{{font-size:12px}}
.b{{padding:1px 8px;border-radius:99px;font-size:12px;border:1px solid currentColor}} .ok{{color:var(--ok)}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}}
</style></head><body><main>
<h1>Dead Men &rarr; Dog Days port check</h1>
<p class="m">Read-only scan. Dead Men: {e(dm)}<br>Dog Days: {e(dd)}</p>
<div class="cards">
<div class="card"><b>{len(levels)}</b>Dead Men level archives</div>
<div class="card"><b>{tot_e:,}</b>entities ({round(100*tot_b/max(1,tot_e))}% need the base-layout fix)</div>
<div class="card"><b class="bad">{len(miss_c)}</b>entity classes missing in Dog Days</div>
<div class="card"><b class="bad">{len(miss_k)}</b>controllers Dog Days doesn't know</div>
<div class="card"><b class="warn">{len(chg_k)}</b>controllers with a changed layout</div>
</div>
<h2>What this means</h2>
<p><b>Base layout:</b> every Dog Days entity has one extra bool after the first int of the shared base class (always 0 in Dog Days levels). Dead Men levels don't have it, so each entity must be rewritten with it inserted, otherwise Dog Days reads every entity one field off and the level fails to load.</p>
<p><b>Missing entity classes:</b> {e(', '.join(miss_c)) or 'none'}.</p>
<p><b>Unknown controllers</b> (must be stripped or rebuilt): {e(', '.join(miss_k)) or 'none'}.</p>
<p><b>Changed controllers</b> (need a field-by-field converter): {e(', '.join(chg_k)) or 'none'}.</p>
<h2>Levels</h2><div class="wrap"><table><tr><th>Archive</th><th>Entities</th><th>Controllers</th><th>DM base layout</th><th>Missing classes</th><th>Resized classes</th><th>Problem controller types</th></tr>{rows_l}</table></div>
<h2>Entity classes (all levels)</h2><p class="m">"size changed" = the C++ object is a different size in Dog Days, a strong hint its saved properties changed too.</p>
<div class="wrap"><table><tr><th>Class</th><th>Type ID</th><th>Instances</th><th>Levels</th><th>DM size</th><th>DD size</th><th>Status</th></tr>{rows_c}</table></div>
<h2>Controllers (all levels)</h2><p class="m">Layout letters: e enum, s string, b bool, I int, f float, [x*] array, {{…}} sub-object.</p>
<div class="wrap"><table><tr><th>Controller</th><th>Uses</th><th>Levels</th><th>Status</th><th>Dead Men layout</th><th>Dog Days layout</th></tr>{rows_k}</table></div>
</main></body></html>"""
    open(os.path.join(out, 'report.html'), 'w', encoding='utf-8').write(doc)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    if os.name == 'nt' and not sys.argv[1:]:
        input('\nPress Enter to close...')
