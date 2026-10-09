#!/usr/bin/env python3
"""
Where a level load spends its time, from kept logs, and what a built archive weighs. re/loading.md
has the findings these numbers led to.

    python kl_loadtime.py log <KLHook.log | kl_autotest output> [...]
                                    every scene load in the file: start, end, seconds per stage
                                    (when the hook's breadcrumbs were on), was the window in the
                                    foreground, which archive
    python kl_loadtime.py runs [folder]
                                    one line per kept run (default <work>/build/klhook/live) and
                                    the load time by foreground / background
    python kl_loadtime.py sheet <build folder | archive> [--top N]
                                    cost sheet of a built level: bytes per member, the textures by
                                    size, and the share that only the systems level's removed map
                                    still holds (kl_graft.dead_assets) = what '--load trim,slim' saves

WHAT THE LOG LINES MEAN (klhook/klauto.c writes them; the SHIP hook writes only the 'steam:' ones)
  LOAD start scene='..'              the scene loader was entered (Hooks=1)
  progress stage N a% -> b%          ZEngineDataBase slot 3 (kl2 0x53ac90): stage N at fraction a,
                                     b = the 'Buffering' number on screen. Stage bounds 0 .1 .15 .35
                                     .4 .5 .6 .7 .8 .9 1. Logged when the stage or the 5 % step changes.
  phase: ..                          entity loader 0x8ad7c0, scene block 0x862780, node properties
                                     0x46fe20, REF fix-up 0x6204b0, room fix-up, geom buffer pass,
                                     REF consumer, post-load init 0x5acc50
  geom init stage N begins           the staged init walks (N = 1, 2, 4, 5), each over every geom
  object init stage N begins, K objects
  LOAD end scene='..' T ms, K nodes  Hooks=1: the loader returned
  LOAD end ... pause of T ms         Hooks=0: seen at the first keyboard poll after it; T = how long
                                     the game did not poll the keyboard = the load, to about 0.1 s
  first keyboard poll (result R)     R = 00000000: the real device is acquired = the game window is
                                     in the FOREGROUND. 8007000c (DIERR_NOTACQUIRED) = it is not.
                                     This is the one line that predicts the load time (re/loading.md 1).
  steam: level archive X opened ...  CreateFile on a level archive: its size and whether it is stock
  kl2.exe+68e3cb                     Steam's probe, raised once before each scene load: a start mark
                                     when Hooks=0
STAGES. What stages 5 - 7 hold is known from the phase lines; stages 1 - 4 (10 % .. 50 %, the file
part) were not followed to the code that reports them and are printed by their numbers only.
"""
import collections, os, re, statistics, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STAGE = {0: 'before the scene', 1: 'stage 1 (10-15 %)', 2: 'stage 2 (15-35 %): level files', 3: 'stage 3 (35-40 %)',
         4: 'stage 4 (40-50 %)', 5: 'stage 5 (50-60 %): entities, then node properties', 6: 'stage 6 (60-70 %): REF fix-up',
         7: 'stage 7 (70-80 %): post-load init walks', 8: 'stage 8 (80-90 %): inside init stage 2', 9: 'stage 9 (90-100 %)'}
LINE = re.compile(r'^(?:\s*log \| )?(\d\d):(\d\d):(\d\d)\.(\d+) (.*)$')
FOCUS = {'00000000': 'foreground', '8007000c': 'background', '8007001e': 'background'}


class Load:
    """One scene load: scene, t0 / t1 (seconds of the day, None = not logged), how t0 was found,
    marks = [(t, text)] of the breadcrumbs inside, nodes, focus, archive = (bytes, 'STOCK' | 'NOT stock')."""

    def __init__(self, t0, how):
        self.scene, self.t0, self.t1, self.how, self.marks = '', t0, None, how, []
        self.nodes = self.focus = self.archive = self.pause = None
        self.soft = False                               # t1 is a later sign of life, not the loader's return
        self.opens = []

    seconds = property(lambda s: None if s.t1 is None or s.t0 is None else s.t1 - s.t0)

    def stages(self):
        """[(label, seconds)] between consecutive marks of one kind: progress stages, then phases."""
        out = []
        for kind in ('stage', 'phase'):
            ms = [(t, x) for t, k, x in self.marks if k == kind]
            for (t, x), (t2, _x) in zip(ms, ms[1:] + [(self.t1, None)]):
                if t2 is not None:
                    out.append((kind, x, t2 - t))
        return out


def parse(path):
    """-> (loads, info): every scene load of a KLHook.log or a kl_autotest output, in order.
    info: {'hooks': breadcrumbs seen, 'result': the RESULT line, 'focus': first keyboard poll state}."""
    loads, cur, info = [], None, {'hooks': False, 'result': '', 'focus': None, 'file': path}
    mark = None                                         # the last start mark that no load has taken
    sess, focus = 0, {}                                 # game process number -> window state at its first keyboard poll
    day = 0
    last = None
    for raw in open(path, errors='replace'):
        m = LINE.match(raw.rstrip('\r\n'))
        if not m:
            if raw.startswith('RESULT:'):
                info['result'] = raw.strip()
            continue
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + float('0.' + m.group(4))
        if last is not None and t + day < last - 3600:
            day += 86400                                # the run went past midnight
        t += day; last = t
        x = m.group(5)
        if x.startswith('==== KLHook loaded'):            # a new game process (a kept log can hold several)
            cur, mark = None, None
            sess += 1
        elif '68e3cb' in x and ('CRASH' in x or 'probe' in x):
            mark = (t, 'Steam probe')
        elif x.startswith("msg: 'StartGame'"):
            mark = (t, 'StartGame')
        elif x.startswith('LOAD start'):
            cur = Load(t, 'LOAD start'); loads.append(cur); info['hooks'] = True
            cur.sess = sess
            cur.scene = re.search(r"scene='([^']*)'", x).group(1)
            mark = None
        elif x.startswith('LOAD end'):
            scene = re.search(r"scene='([^']*)'", x).group(1)
            if cur is not None and cur.soft and cur.scene == scene:
                cur.soft, cur.how = False, cur.how.split(';')[0]       # the join module spoke first: same load
            elif cur is None or cur.t1 is not None:
                cur = Load(mark[0] if mark else None, mark[1] if mark else 'not logged'); loads.append(cur)
                cur.sess = sess
            cur.scene, cur.t1 = scene, t
            a = re.search(r'pause of (\d+) ms', x)
            b = re.search(r"' (\d+) ms, (\d+) nodes", x)
            if a:
                cur.pause = int(a.group(1)) / 1000
                if cur.t0 is None or (cur.pause and t - cur.t0 > cur.pause + 5):
                    cur.t0, cur.how = t - cur.pause, 'keyboard pause'     # the mark was an earlier scene's
            if b:
                cur.nodes = int(b.group(2))
            mark = None
        elif cur is not None and cur.t1 is None:
            a = re.match(r'progress stage (\d+) ', x)
            if a:
                s = int(a.group(1))
                if [v for _t, k, v in cur.marks if k == 'stage'][-1:] != [s]:
                    cur.marks.append((t, 'stage', s))
            elif x.startswith('phase: '):
                cur.marks.append((t, 'phase', x[7:]))
            elif x.startswith('geom init stage') or x.startswith('object init stage'):
                cur.marks.append((t, 'phase', x.split(',')[0].replace(' begins', '')))
        a = re.match(r"join: level '([^']*)': ", x)
        if a and mark and (cur is None or cur.t1 is not None):
            # the SHIP hook has no LOAD lines; its join module speaks on the first tick of a level that
            # has a KLJoin.ini: an end mark (later than the loader's return by the first frames)
            cur = Load(mark[0], mark[1] + '; end = first tick of the join module'); loads.append(cur)
            cur.scene, cur.t1, cur.soft, cur.sess, mark = a.group(1), t, True, sess, None
        a = re.search(r'level archive (\S+) opened .*?: (STOCK|NOT stock) \((\d+) bytes', x)
        if a:
            if mark is None and (cur is None or cur.t1 is not None):
                mark = (t, 'archive opened')
            info.setdefault('opens', []).append((t, a.group(1), int(a.group(3)), a.group(2)))
        a = re.search(r'first keyboard poll \(result ([0-9a-fA-F]{8})\)', x)
        if a and sess not in focus:
            focus[sess] = info['focus'] = FOCUS.get(a.group(1).lower(), 'result ' + a.group(1))
        if x.startswith('RESULT '):
            info['result'] = x
    for ld in loads:                                    # the archive of each load: the last one opened inside it
        slot = re.search(r'Locations[\\/](\w+)[\\/]', ld.scene)
        for t, name, size, stock in info.get('opens', ()):
            if slot and name.lower().startswith(slot.group(1).lower()) and (ld.t0 is None or t >= ld.t0 - 2) and (ld.t1 is None or t <= ld.t1):
                ld.archive = (size, stock); ld.opens.append(t)
        ld.focus = focus.get(ld.sess)
    return loads, info


def show_log(path, log=print):
    loads, info = parse(path)
    log('%s: %d scene load(s); window at the first keyboard poll: %s; breadcrumbs %s' % (
        path, len(loads), info['focus'] or 'not logged', 'on' if info['hooks'] else 'off'))
    for ld in loads:
        sec = ld.seconds
        log('  %s: %s%s%s%s' % (ld.scene, '%.1f s' % sec if sec is not None else 'end or start not logged',
                               ' (start = %s)' % ld.how, ', %d nodes' % ld.nodes if ld.nodes else '',
                               ', archive %.1f MB %s' % (ld.archive[0] / 1e6, ld.archive[1]) if ld.archive else ''))
        if ld.opens and ld.t0 is not None:
            log('      archive opened at +%s s' % ', +'.join('%.1f' % (t - ld.t0) for t in ld.opens))
        per = collections.OrderedDict()
        for kind, x, s in ld.stages():
            if kind == 'stage':
                per[x] = per.get(x, 0) + s
        for x, s in per.items():
            log('      %-52s %7.1f s' % (STAGE.get(x, 'stage %d' % x), s))
        for kind, x, s in ld.stages():
            if kind == 'phase' and s >= 0.05:
                log('        . %-50s %7.1f s' % (x[:50], s))
    if info['result']:
        log('  ' + info['result'][:160])
    return loads, info


def show_runs(folder=None, log=print):
    if folder is None:
        from kl_port_check import workdir
        folder = os.path.join(workdir(), 'build', 'klhook', 'live')
    rows = []
    for f in sorted((f for f in os.listdir(folder) if f.endswith('.log')), key=lambda f: os.path.getmtime(os.path.join(folder, f))):
        loads, info = parse(os.path.join(folder, f))
        seen = set()
        for ld in loads:
            if 'Locations' in ld.scene and ld.seconds is not None and (ld.scene, round(ld.seconds)) not in seen:
                seen.add((ld.scene, round(ld.seconds)))
                rows.append((f[:-4], ld))
    log('%-8s %-9s %-5s %-11s %8s %9s  %s' % ('run', 'end', 'level', 'window', 'load s', 'archive', 'start mark'))
    by, told = collections.defaultdict(list), set()
    for name, ld in rows:
        if (round(ld.t1 % 86400), ld.scene) in told:            # a log that was appended to holds the earlier runs again
            continue
        told.add((round(ld.t1 % 86400), ld.scene))
        h = int(ld.t1 % 86400)
        lvl = re.split(r'[\\/]', ld.scene)[-2]
        log('%-8s %02d:%02d:%02d  %-5s %-11s %8.1f %9s  %s' % (name, h // 3600, h // 60 % 60, h % 60, lvl, ld.focus or '?', ld.seconds,
                                                          '%.0f MB' % (ld.archive[0] / 1e6) if ld.archive else '-', ld.how))
        by[lvl, ld.focus or '?'].append(ld.seconds)
    for (lvl, k), v in sorted(by.items()):
        log('%-5s window %-11s %3d loads: median %.0f s, range %.0f .. %.0f s' % (lvl, k, len(v), statistics.median(v), min(v), max(v)))
    return rows


def sheet(path, top=15, log=print):
    """Cost sheet of a built level. -> dict of the numbers printed."""
    import kl_graft as K, kl_prmgraph as G, kl_texmat as T
    zp = path if path.lower().endswith('.zip') else next(os.path.join(path, f) for f in sorted(os.listdir(path)) if f.lower().endswith('_main.zip'))
    with zipfile.ZipFile(zp) as z:
        il = z.infolist()
    raw, packed = sum(i.file_size for i in il), sum(i.compress_size for i in il)
    log('%s: %.1f MB, %d members, %.1f MB unpacked' % (zp, os.path.getsize(zp) / 1e6, len(il), raw / 1e6))
    log('  %-34s %-8s %10s %10s %6s' % ('member', 'method', 'packed', 'unpacked', 'share'))
    for i in sorted(il, key=lambda i: -i.file_size)[:top]:
        log('  %-34s %-8s %10d %10d %5.1f%%' % (i.filename.rsplit('/', 1)[-1][:34], {0: 'stored', 8: 'deflate'}.get(i.compress_type, i.compress_type),
                                             i.compress_size, i.file_size, 100 * i.file_size / raw))
    stamps = {i.date_time for i in il}
    log('  time stamps: %s' % ('one for all members: %04d-%02d-%02d %02d:%02d:%02d' % next(iter(stamps)) if len(stamps) == 1 else '%d different' % len(stamps)))
    d = os.path.dirname(zp)
    beside = [(os.path.getsize(os.path.join(d, f)), f) for f in os.listdir(d) if os.path.join(d, f) != zp and '_Main' in f]
    log('  beside the archive: %d files, %.1f MB (largest: %s)' % (len(beside), sum(s for s, _f in beside) / 1e6,
                                                                 ', '.join('%s %.1f MB' % (f, s / 1e6) for s, f in sorted(beside, reverse=True)[:3])))
    order, files, ext, sc, live, hud = K.open_built(zp)
    prm, tex, mat = G.read(files[ext['.prm']], 'dd'), T.read_tex(files[ext['.TEX']]), T.read_mat(files[ext['.MAT']])
    dead = K.dead_assets(prm, mat, tex, live, hud)
    size = {i: len(x.entry) + sum(len(f) for f in x.faces or ()) for i, x in tex.tex.items()}
    dims = lambda x: struct.unpack_from('<HH', x.entry, 16)[::-1]
    log('  entities %d; .prm %d chunks (%d reached from the level, %d dead model roots); materials %d; textures %d of 4096 ids' % (
        len(sc.nodes) - 1, len(prm.chunks) - 1, len(dead['reached']), len(dead['roots']), len(mat.insts), len(tex.tex)))
    hist = collections.Counter()
    for i, x in tex.tex.items():
        w, h = dims(x)
        hist[max(w, h)] += size[i]
    log('  texture bytes by longer side: ' + ', '.join('%d px %.0f MB' % (k, v / 1e6) for k, v in sorted(hist.items(), reverse=True) if v >= 1e6))
    dt = set(dead['tex'])
    log('  largest textures (* = only the removed map of the systems level shows it):')
    for i in sorted(size, key=size.get, reverse=True)[:top]:
        w, h = dims(tex.tex[i])
        log('    %s %5d %4d x %-4d %6.1f MB  %s' % ('*' if i in dt else ' ', i, w, h, size[i] / 1e6, tex.tex[i].name[:70]))
    rep = {'zip': os.path.getsize(zp), 'unpacked': raw, 'packed': packed, 'entities': len(sc.nodes) - 1, 'textures': len(tex.tex),
           'tex bytes': len(files[ext['.TEX']]), 'dead textures': len(dt), 'dead tex bytes': sum(size[i] for i in dt),
           'shrinkable': sum(K.small_texture(tex.tex[i]) is not None for i in dt),
           'prm bytes': len(files[ext['.prm']]), 'dead prm chunks': len(dead['data']),
           'dead prm bytes': sum(len(prm.chunks[i]) for i in dead['data']), 'dead materials': len(dead['slots'])}
    log('  UNREFERENCED SHARE (dead = reached only from model roots that no entity or property names):')
    log('    .prm  %6.1f of %6.1f MB (%2.0f %%) vertex / index data in %d chunks          -> --load trim' % (
        rep['dead prm bytes'] / 1e6, rep['prm bytes'] / 1e6, 100 * rep['dead prm bytes'] / rep['prm bytes'], rep['dead prm chunks']))
    log('    .TEX  %6.1f of %6.1f MB (%2.0f %%) in %d of %d textures (%d can shrink)         -> --load slim' % (
        rep['dead tex bytes'] / 1e6, rep['tex bytes'] / 1e6, 100 * rep['dead tex bytes'] / rep['tex bytes'], len(dt), len(tex.tex), rep['shrinkable']))
    log('    .MAT  %d of %d material slots are used by dead meshes only (kept: the file is %.1f MB)' % (
        len(dead['slots']), len(mat.insts), len(files[ext['.MAT']]) / 1e6))
    return rep


if __name__ == '__main__':
    a = sys.argv[1:]
    top = 15
    if '--top' in a:
        i = a.index('--top'); top = int(a[i + 1]); del a[i:i + 2]
    if len(a) >= 2 and a[0] == 'log':
        for p in a[1:]:
            show_log(p)
    elif a and a[0] == 'runs':
        show_runs(*a[1:2])
    elif len(a) >= 2 and a[0] == 'sheet':
        sheet(a[1], top)
    else:
        print(__doc__)
