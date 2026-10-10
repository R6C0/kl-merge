#!/usr/bin/env python3
"""
One command for the three steps a FINISHED Dead Men map build gets after the owner's round on Late Night
Opening (2026-10-10: 'dead men guns dont show up in the late night, the late night van sometimes is a bit
weird? camera goes under the map when ur in it and then the ai a bit too easy ... do the same fixes for the
other maps'). Offline: nothing here installs anything, starts the game or writes into the Dog Days folder.
Spec, tables and the list for the owner: re/map_tune.md.

    python kl_map_tune.py build <finished build folder> <out folder> [options]
    python kl_map_tune.py all [<folder of builds> <out root>] [M01 M02 M03 M06] [options]
                                        default: <work>/build/z_maps -> <work>/build/t_maps
    python kl_map_tune.py check <tuned folder>      every checker again on a folder built here (exit 1 on a failure)
    python kl_map_tune.py table <out root>          the per-map tables from the folders' tune.json (markdown)
  options
    --no-guns --no-escape --no-ai     leave a step out
    --start=1 --set=1                 the looks baked by the gun step (kl_map_guns: the Guns page's two numbers)
    --no-strength --no-waves --no-chains --no-called --health=1.5     kl_map_ai's parts ('--no-called' is its
                                      '--no-escape': nothing is named when the escape vehicle is called)
    --keep                            keep the folders of the steps (<out root>/_work/<name>/1_guns ...)

THE STEPS AND THEIR ORDER (each is another agent's tool, called as a library; this file changes none of them)
  1 guns    tools/kl_map_guns.py build (re/map_guns.md)   ADDS: six Dead Men gun models into dead chunk indices of
            the .prm, 94 chunks at the end of its table, the guns' textures, material rows; rewrites .prm .TEX
            .MAT .gms .oct .prp through kl_chars.Lv and writes KLGuns.ini, which NAMES chunk indices of this .prm.
  2 escape  tools/kl_map_escape.py repair (re/map_escape.md)   VALUES: one enum per escape camera in the .prp.
  3 ai      tools/kl_map_ai.py apply (re/map_ai.md)   VALUES and reference lists of objects the .prp already has.
  Why this order:
  - the gun step is the only one that adds chunks and renumbers anything, and the only one that rewrites more
    than the .prp. Steps 2 and 3 each PROVE (CRC and size of every member) that they changed the .prp member and
    nothing else, so after them KLGuns.ini's chunk indices and KLWardrobe.ini's model numbers still name what
    they named. The other way round the gun step's kl_chars.Lv would re-write a .prp it did not read from a
    verified folder, and kl_map_guns refuses a folder that already has KLGuns.ini.
  - the ai step sets floors by the weapon template an actor carries (re/map_ai.md 10.5: 'run this AFTER a step
    that changes what actors carry'). The gun step keeps every template (a look is parts of the same model), so
    the floors come out the same either way (checked here: the ai totals of a tuned map are compared with the
    ai step run alone, when <work>/build/t_ai/<map> is there) - but after is the order its author asks for.
  - escape and ai do not touch the same objects (CCameraBox against soldiers, squads, timers, the two
    monitors); their order between themselves was NOT tried both ways. Escape goes first because it is the
    one with nothing assumed in it: if the ai step fails on a map, the map still has guns + camera.
  A step that raises, or reports a problem of its own, is LEFT OUT of that map: its folder is removed, the
  chain goes on from the folder before it, and tune.json / the RESULT line say so.

THE CHECKERS (run on the WRITTEN out folder, after the last step)
  kl_maps.preflight     again, because the gun step changed .gms / .prm (a CRASH finding fails)
  kl_maps.audit         kl_fa.check, boarding, kl_impact.check (bone ids, chunk limit, surface table),
                        kl_arms.check, kl_chars.undrawn, kl_chars.check with the wardrobe's roots,
                        kl_light.missing_shaders, kl_snd.verify, kl_voice.census, steps.json against the folder.
                        kl_impact and kl_chars are reported from the audit's own run (not run a second time).
  kl_map_guns.recheck   the game's walk takes exactly the shown group of each gun; KLGuns.ini names the roots
  kl_map_escape.check   no camera eye at the origin / under the map, no route point under the ground
  kl_map_ai             the .prp re-serialises byte for byte with 0 misfits; no list entry names nothing
  side files            KLWardrobe.ini byte for byte the source's; KLGuns.ini there exactly when the gun step
                        ran; every file beside the archive (.WAV .WHD .SND ...) the source's by sha1
  members               only the members the steps that ran may change differ from the source
  budget                .ANM, .fxc, the .WAV beside the archive unchanged; chunk table within kl_impact.CHUNK_SAFE
"""
import collections, hashlib, json, os, shutil, struct, sys, time, traceback, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SLOT = 'F01'
TAGS = ('M01', 'M02', 'M03', 'M06')
TITLES = {'M01': 'M01_FA_A diner (Sunny Hill Plaza), escape car', 'M02': 'M02_FA_A Late Night Opening, escape car',
          'M03': 'M03_FA_A the bank (Withdrawal), escape van', 'M06': 'M06_FA_A A Walk in the Park, helicopter'}
ORDER = ('guns', 'escape', 'ai')
# what a step may change in the archive (members by extension); anything else differing from the source fails
MAY = {'guns': {'.MAT', '.TEX', '.gms', '.oct', '.prm', '.prp'}, 'escape': {'.prp'}, 'ai': {'.prp'}}
BLOCKS = ('.prm', '.ANM', '.fxc', '.WAV')           # each read into one large memory block (the lead's budget)
NOTES = ('tune.json', 'tune.txt', 'audit.json', 'audit.txt')


def sizes(folder):
    """The four large members (+ .TEX, .prp and the chunk-table entries) of a build folder, without loading it."""
    out = collections.OrderedDict()
    with zipfile.ZipFile(os.path.join(folder, SLOT + '_Main.zip')) as z:
        by = {i.filename.rsplit('_Main', 1)[1]: i for i in z.infolist() if '_Main' in i.filename}
        for e in ('.prm', '.ANM', '.fxc'):
            out[e] = by[e].file_size
        wav = os.path.join(folder, SLOT + '_Main.WAV')
        out['.WAV'] = os.path.getsize(wav) if os.path.isfile(wav) else 0
        out['.TEX'], out['.prp'] = by['.TEX'].file_size, by['.prp'].file_size
        with z.open(by['.prm']) as f:
            out['entries'] = struct.unpack('<I', f.read(8)[4:])[0]      # the header's count, as kl_maps.audit reads it
    out['archive'] = os.path.getsize(os.path.join(folder, SLOT + '_Main.zip'))
    return out


def _sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def differ(a, b):
    """(members whose CRC or size differ between two build folders, True when names and order are equal)."""
    with zipfile.ZipFile(os.path.join(a, SLOT + '_Main.zip')) as za, zipfile.ZipFile(os.path.join(b, SLOT + '_Main.zip')) as zb:
        ia, ib = za.infolist(), zb.infolist()
        same = [i.filename for i in ia] == [i.filename for i in ib]
        mb = {i.filename: i for i in ib}
        d = sorted(i.filename.rsplit('_Main', 1)[1] for i in ia if i.filename not in mb or (i.CRC, i.file_size) != (mb[i.filename].CRC, mb[i.filename].file_size))
    return d, same


# ------------------------------------------------------------------ the three steps (wrappers; -> summary dict)
def step_guns(src, dst, o, log):
    import kl_map_guns as MG
    r = MG.build(src, dst, start=o['start'], sets=o['set'], audit=False, log=log)      # preflight / audit: once, at the end
    if r['bad']:
        raise ValueError('kl_map_guns reports %d problem(s): %s' % (len(r['bad']), '; '.join(r['bad'][:3])))
    return collections.OrderedDict(shows=r['shows'], carried_with_look=r['carried_with_look'], dead_indices=r['dead_indices'],
                                   growth=r['growth'], members=r['steps'], start=o['start'], set=o['set'])


def step_escape(src, dst, o, log):
    import kl_map_escape as ME
    r = ME.repair(src, dst, False, log)
    if r['after']['faults']:
        raise ValueError('kl_map_escape: %d fault(s) left: %s' % (len(r['after']['faults']), '; '.join(r['after']['faults'][:3])))
    return collections.OrderedDict(cameras=r['cameras_changed'], points_moved=len(r['points_moved']),
                                   faults=[len(r['before']['faults']), len(r['after']['faults'])], faults_before=r['before']['faults'],
                                   eyes=[[c['name'], c['eye'], c.get('over'), c.get('ground_name')] for c in r['after']['cameras']],
                                   members=r['members_changed'])


def step_ai(src, dst, o, log):
    import kl_map_ai as MA
    MA.HEALTH_SCALE = o['health']
    r = MA.apply(src, dst, o['parts'], False, log, False)
    A, B = MA.compare(src, dst, log)
    keep = ('soldiers', 'hit points (health added up)', 'health mean', 'accuracy mean (as used)', 'weapon classes', 'unleashed squads',
            'squads with a wiped-out list', 'named at the round start (AIMonitor 2)', 'named when the vehicle is called (monitor 4..7)', 'timers s')
    return collections.OrderedDict(parts=list(o['parts']), health_scale=o['health'],
                                   before={k: A['totals'][k] for k in keep}, after={k: B['totals'][k] for k in keep},
                                   lines={k: [x if isinstance(x, str) else '%s: %s' % (x[0], x[1]) for x in r.get(k, ())] for k in ('strength', 'cars', 'waves', 'chains', 'escape')},
                                   prp=list(r['prp bytes']))


STEPS = collections.OrderedDict([('guns', step_guns), ('escape', step_escape), ('ai', step_ai)])


# ------------------------------------------------------------------ the checkers
def checks(src, out, ran, log=print):
    """Every checker on the written folder `out` (made from `src` by the steps `ran`). -> OrderedDict name ->
    {'ok': bool, 'text': one line, ...}."""
    import kl_maps as M
    res = collections.OrderedDict()
    def put(name, ok, text, **more):
        res[name] = dict(ok=bool(ok), text=text, **more)
        log('  %-22s %-4s %s' % (name, 'ok' if ok else 'FAIL', text))
    def run(name, fn):
        try:
            fn()
        except Exception as x:                           # a checker that cannot run is a failed check, not a pass
            put(name, False, 'did not run: %s: %s' % (type(x).__name__, str(x)[:300]), trace=traceback.format_exc()[-1500:])

    def preflight():
        with open(os.path.join(out, 'preflight.txt'), 'w', encoding='utf-8') as fh:
            f = M.preflight(out, SLOT, log=lambda t: fh.write(str(t) + '\n'))
        c = collections.Counter(x[0] for x in f)
        put('kl_maps.preflight', not c['CRASH'], 'CRASH %d, RISK %d, NOTE %d' % (c['CRASH'], c['RISK'], c['NOTE']),
            crash=['%s %s' % (x[1], x[2]) for x in f if x[0] == 'CRASH'])
    run('kl_maps.preflight', preflight)

    def audit():
        a = M.audit(out, SLOT, log=lambda *_a: None)
        put('kl_maps.audit', not a['bad'], '%s (%d that must be 0, %d known and accepted), content id %s' % (
            'PASS' if not a['bad'] else 'FAIL', len(a['bad']), len(a['known']), a['content_id'][:10]),
            bad=a['bad'], known=a['known'], content_id=a['content_id'], prm_entries=a['prm_entries'])
        put('kl_impact.check', not a['impact'], 'problems: %d (inside the audit: bone ids, chunk limit, surface table)' % len(a['impact']), bad=a['impact'])
        cb = [x for x in a['chars_check'] if 'asks for a shader the .fxc lacks' not in x]
        put('kl_chars.check', not cb and not a['undrawn'], 'problems: %d, known (map materials without a compiled shader): %d; undrawn people %d of %d; wardrobe roots %d (inside the audit)' % (
            len(cb), len(a['chars_check']) - len(cb), len(a['undrawn']), a['people'], a['wardrobe_roots']), bad=cb + a['undrawn'])
        put('kl_fa / kl_arms', not [x for x in a['bad'] if x.startswith(('fa:', 'arms:', 'boarding:'))],
            'kl_fa.check %s; kl_arms.check %d finding(s); carried: %s' % (a['fa'] or 'nothing', len(a['arms']), ', '.join('%s %d' % kv for kv in a['weapons'].items())))
    run('kl_maps.audit', audit)

    def guns():
        import kl_map_guns as MG
        if 'guns' not in ran:
            return put('kl_map_guns.check', not os.path.isfile(os.path.join(out, 'KLGuns.ini')), 'step not run: no KLGuns.ini in the folder')
        lines = []
        bad = MG.recheck(out, log=lines.append)
        # who carries a gun with a look in the FINISHED folder (the ai step re-arms squads after the gun step)
        import kl_arms, kl_chars
        lv = kl_chars.Lv(out)
        look = {r['template'].lower(): r['shows'] for r in MG.weapons(lv)[0] if r.get('look_of') and r['shows'] != 'own model'}
        who = [[squad.split('!')[-1], w, look[w.lower()]] for _k, squad, w, _w2, _g1, _g2, _s in kl_arms.carriers(lv.scene()[0]) if w.lower() in look]
        put('kl_map_guns.check', not bad, (lines[0].split(': ', 1)[-1][:400] if lines else 'problems: %d' % len(bad)) + '; placed actors holding a look: %d' % len(who),
            bad=bad, carried_with_look=who)
    run('kl_map_guns.check', guns)

    def escape():
        import kl_map_escape as ME
        r = ME.check(ME.Level(out), log=lambda *_a: None)
        put('kl_map_escape.check', not r['faults'], '%d fault(s); %d vehicle(s), camera eyes: %s' % (len(r['faults']), len(r['vehicles']), '; '.join(
            '%s %s at (%d, %d, %d)%s' % (c['name'].split('!')[-1], c['mode'], *c['eye'], ' %.0f over the ground' % c['over'] if c.get('over') is not None else ' NO FLOOR under it')
            for c in r['cameras'])), bad=r['faults'])
    run('kl_map_escape.check', escape)

    def ai():
        import kl_map_ai as MA, kl_graft, kl_prpjoin as J
        order, files, ext, sc, _l, _h = kl_graft.open_built(os.path.join(out, SLOT + '_Main.zip'))
        data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
        dang = MA.faults(sc)
        t = MA.measure(out)['totals']
        text = '.prp re-serialises %s, %d misfit(s), %d list entries that name nothing; %d soldiers, %d hit points, accuracy as used %.1f' % (
            'byte for byte' if data == files[ext['.prp']] else 'DIFFERENTLY', len(bad), len(dang), t['soldiers'], t['hit points (health added up)'], t['accuracy mean (as used)'])
        ok = data == files[ext['.prp']] and not bad and not dang
        alone = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(src))), 't_ai', os.path.basename(os.path.normpath(src)))
        if 'ai' in ran and ran['ai'].get('parts') == ['strength', 'waves', 'chains', 'escape'] and ran['ai'].get('health_scale') == 1.0 \
                and os.path.isfile(os.path.join(alone, SLOT + '_Main.zip')):
            ta = MA.measure(alone)['totals']            # the ai step run alone on the same source, by its author
            eq = json.dumps(ta, default=str) == json.dumps(t, default=str)
            text += '; totals %s the ai step alone (%s)' % ('EQUAL to' if eq else 'DIFFER from', alone)
            ok = ok and eq
        put('kl_map_ai', ok, text, bad=[str(x) for x in bad[:5]] + dang[:5], totals=t)
    run('kl_map_ai', ai)

    def side():
        bad = []
        a, b = M.member_ids(src, SLOT)[1], M.member_ids(out, SLOT)[1]
        if a != b:
            bad.append('files beside the archive differ: %s' % sorted({x[0] for x in a} ^ {x[0] for x in b} | {x[0] for x, y in zip(a, b) if x != y}))
        w = [os.path.join(d, 'KLWardrobe.ini') for d in (src, out)]
        if os.path.isfile(w[0]) != os.path.isfile(w[1]) or (os.path.isfile(w[0]) and _sha1(w[0]) != _sha1(w[1])):
            bad.append('KLWardrobe.ini is not the source\'s')
        if os.path.isfile(os.path.join(out, 'KLGuns.ini')) != ('guns' in ran):
            bad.append('KLGuns.ini %s' % ('missing' if 'guns' in ran else 'there without the gun step'))
        have = [f for f in ('KLWardrobe.ini', 'KLGuns.ini', 'KLJoin.ini') if os.path.isfile(os.path.join(out, f))]
        put('side files', not bad, '; '.join(bad) or '%d files beside the archive equal by sha1; ini files: %s' % (len(b), ', '.join(have) or 'none'), bad=bad, ini=have)
    run('side files', side)

    def members():
        d, same = differ(src, out)
        may = set().union(*[MAY[s] for s in ran]) if ran else set()
        extra = [e for e in d if e not in may]
        put('members', same and not extra, 'differ from the source: %s%s%s' % (' '.join(d) or 'none', '' if same else '; NAMES OR ORDER DIFFER',
            '; NOT EXPECTED: ' + ' '.join(extra) if extra else ''), changed=d)
    run('members', members)

    def budget():
        import kl_impact
        a, b = sizes(src), sizes(out)
        moved = [e for e in ('.ANM', '.fxc', '.WAV') if a[e] != b[e]]
        ok = not moved and b['entries'] <= kl_impact.CHUNK_SAFE and (b['.prm'] == a['.prm'] or 'guns' in ran)
        put('budget', ok, '.prm %d -> %d (%+d), .ANM %d, .fxc %d, .WAV %d: %s; chunk table %d -> %d of %d' % (
            a['.prm'], b['.prm'], b['.prm'] - a['.prm'], b['.ANM'], b['.fxc'], b['.WAV'], 'unchanged' if not moved else 'CHANGED ' + ' '.join(moved),
            a['entries'], b['entries'], kl_impact.CHUNK_SAFE), before=a, after=b)
    run('budget', budget)
    return res


# ------------------------------------------------------------------ the command
def options(argv):
    o = {x for x in argv if x.startswith('--')}
    val = lambda k, d, t: next((t(x.split('=', 1)[1]) for x in o if x.startswith('--%s=' % k)), d)
    return dict(steps=[s for s in ORDER if '--no-' + s not in o], start=val('start', 1, int), set=val('set', 1, int), health=val('health', 1.0, float),
                parts=tuple(p for p, flag in (('strength', 'strength'), ('waves', 'waves'), ('chains', 'chains'), ('escape', 'called')) if '--no-' + flag not in o),
                keep='--keep' in o)


def build(src, out, o=None, log=print):
    """Finished build folder `src` (not changed) -> `out`: the steps in ORDER, each into its own folder under
    <out root>/_work/<name>/, the last good one moved to `out`; then checks(). -> report (also <out>/tune.json,
    the lines in <out>/tune.txt). report['ok'] = every step asked for ran and every checker passed."""
    o = o or options(())
    src, out = os.path.abspath(src), os.path.abspath(out)
    low = out.lower()
    if 'kl_portbackup' in low or 'dog days' in low or out == src:
        raise ValueError('kl_map_tune writes build folders only (never the game\'s, never the source build)')
    if not os.path.isfile(os.path.join(src, SLOT + '_Main.zip')):
        raise ValueError('%s: no %s_Main.zip' % (src, SLOT))
    name = os.path.basename(os.path.normpath(out))
    work = os.path.join(os.path.dirname(out), '_work', name)
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    lines, t0 = [], time.time()
    def say(s=''):
        lines.append(str(s)); log(s)
    rep = collections.OrderedDict(src=src, out=out, asked=list(o['steps']), order=list(ORDER), ran=collections.OrderedDict(),
                                  skipped=collections.OrderedDict(), sizes=collections.OrderedDict(source=sizes(src)))
    say('kl_map_tune: %s -> %s; steps: %s' % (src, out, ' -> '.join(o['steps']) or 'none'))
    cur = src
    for n, s in enumerate(o['steps'], 1):
        dst = os.path.join(work, '%d_%s' % (n, s))
        say('== step %d %s: %s -> %s' % (n, s, cur, dst))
        t = time.time()
        try:
            r = STEPS[s](cur, dst, o, say)
            d, same = differ(cur, dst)
            if not same or [e for e in d if e not in MAY[s]]:
                raise ValueError('the step changed members it should not: %s (names and order %s)' % (' '.join(d), 'equal' if same else 'DIFFER'))
            r['members_changed'], r['seconds'] = d, round(time.time() - t, 1)
            rep['ran'][s] = r
            rep['sizes'][s] = sizes(dst)
            cur = dst
            say('== step %d %s: done in %.0f s; members changed: %s' % (n, s, r['seconds'], ' '.join(d) or 'none'))
        except Exception as x:                           # the map is delivered WITHOUT this step rather than not at all
            rep['skipped'][s] = dict(error='%s: %s' % (type(x).__name__, x), trace=traceback.format_exc()[-3000:])
            shutil.rmtree(dst, ignore_errors=True)
            say('== step %d %s: FAILED and LEFT OUT (%s: %s); going on from %s' % (n, s, type(x).__name__, str(x)[:500], cur))
    shutil.rmtree(out, ignore_errors=True)
    if cur == src:
        shutil.copytree(src, out)
    else:
        os.replace(cur, out)
    for f in ('audit.json', 'audit.txt'):               # the source's: the audit below writes this folder's
        if os.path.isfile(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    rep['sizes']['out'] = sizes(out)
    say('== checkers on %s' % out)
    rep['checks'] = checks(src, out, rep['ran'], say)
    rep['failed'] = [k for k, v in rep['checks'].items() if not v['ok']]
    rep['ok'] = not rep['failed'] and not rep['skipped']
    rep['seconds'] = round(time.time() - t0, 1)
    rep['install'] = 'python debug\\slot.py put "%s" %s' % (out, SLOT)
    a, b = rep['sizes']['source'], rep['sizes']['out']
    say('sizes, bytes, source -> out: ' + ', '.join('%s %d -> %d' % (e, a[e], b[e]) for e in BLOCKS + ('.TEX', '.prp', 'entries', 'archive')))
    say('install (the lead; offline tool, not run here): %s' % rep['install'])
    say('RESULT %s: %s; steps run: %s%s; checkers failed: %s (%.0f s)' % (
        name, 'PASS' if rep['ok'] else ('DELIVERED WITHOUT ' + ', '.join(rep['skipped']) if not rep['failed'] else 'FAIL'), ' '.join(rep['ran']) or 'none',
        '; LEFT OUT: ' + ', '.join('%s (%s)' % (k, v['error'][:120]) for k, v in rep['skipped'].items()) if rep['skipped'] else '',
        ', '.join(rep['failed']) or 'none', rep['seconds']))
    with open(os.path.join(out, 'tune.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(out, 'tune.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    if not o['keep']:
        shutil.rmtree(work, ignore_errors=True)
        try:
            os.rmdir(os.path.dirname(work))
        except OSError:
            pass
    return rep


def recheck(folder, log=print):
    """Every checker again on a folder built here (tune.json says what it was made from). -> failed names."""
    rep = json.load(open(os.path.join(folder, 'tune.json')), object_pairs_hook=collections.OrderedDict)
    res = checks(rep['src'], os.path.abspath(folder), rep['ran'], log)
    bad = [k for k, v in res.items() if not v['ok']]
    log('RESULT %s: %s' % (os.path.basename(os.path.normpath(folder)), 'PASS' if not bad else 'FAIL: ' + ', '.join(bad)))
    return bad


def table(root, tags=None, log=print):
    """The per-map tables of re/map_tune.md, from <root>/<tag>/tune.json."""
    for tag in tags or [t for t in sorted(os.listdir(root)) if os.path.isfile(os.path.join(root, t, 'tune.json'))]:
        r = json.load(open(os.path.join(root, tag, 'tune.json')), object_pairs_hook=collections.OrderedDict)
        log('### %s - %s' % (tag, TITLES.get(tag, '')))
        log('')
        log('Steps run: %s. Left out: %s. Result: %s.' % (' -> '.join(r['ran']) or 'none', ', '.join('%s (%s)' % (k, v['error'][:200]) for k, v in r['skipped'].items()) or 'none',
                                                         'PASS' if r['ok'] else 'NOT PASS (%s)' % ', '.join(r['failed'] or r['skipped'])))
        log('')
        log('| step | members changed | what changed |')
        log('|---|---|---|')
        for s, v in r['ran'].items():
            if s == 'guns':
                who = collections.Counter('%s: %s shows the %s' % tuple(x) for x in r['checks'].get('kl_map_guns.check', {}).get('carried_with_look', ()))
                what = 'looks baked (start %d, set %d): %s; placed actors holding a look in the finished build: %s; dead chunk indices before / still free: %s' % (
                    v['start'], v['set'], ', '.join('%s = %s' % kv for kv in v['shows'].items()),
                    '; '.join('%s%s' % (k, ' x%d' % n if n > 1 else '') for k, n in who.items()) or 'none', ' / '.join(str(x) for x in v['dead_indices'] or ()))
            elif s == 'escape':
                what = '%d camera(s) `eFMM_LookFromPosFA` -> `eFMM_LookFromPos` (%s); route points moved: %d; faults %d -> %d' % (
                    len(v['cameras']), ', '.join(c.split('!')[-1] for c in v['cameras']), v['points_moved'], *v['faults'])
            else:
                a, b = v['before'], v['after']
                hp, acc = 'hit points (health added up)', 'accuracy mean (as used)'
                what = 'hit points %s -> %s (mean %s -> %s); accuracy as used %s -> %s; unleashed squads %s -> %s; squads with a wiped-out list %s -> %s; named at the round start %s -> %s; named when the vehicle is called %s -> %s; timers %s -> %s; weapon classes %s -> %s' % (
                    a[hp], b[hp], a['health mean'], b['health mean'], a[acc], b[acc], a['unleashed squads'], b['unleashed squads'],
                    a['squads with a wiped-out list'], b['squads with a wiped-out list'], a['named at the round start (AIMonitor 2)'], b['named at the round start (AIMonitor 2)'],
                    a['named when the vehicle is called (monitor 4..7)'], b['named when the vehicle is called (monitor 4..7)'], a['timers s'], b['timers s'],
                    ', '.join('%s %d' % kv for kv in a['weapon classes'].items()), ', '.join('%s %d' % kv for kv in b['weapon classes'].items()))
            log('| %s | %s | %s |' % (s, ' '.join(v['members_changed']), what))
        log('')
        log('| bytes | .prm | chunk-table entries | .ANM | .fxc | F01_Main.WAV | .TEX | .prp | archive |')
        log('|---|---:|---:|---:|---:|---:|---:|---:|---:|')
        for k, v in r['sizes'].items():
            log('| %s | %s |' % ({'source': 'before (z_maps)', 'out': '**after (t_maps)**'}.get(k, 'after ' + k),
                                 ' | '.join('{:,}'.format(v[e]) for e in ('.prm', 'entries', '.ANM', '.fxc', '.WAV', '.TEX', '.prp', 'archive'))))
        log('')
        log('| checker | | result |')
        log('|---|---|---|')
        for k, v in r['checks'].items():
            log('| %s | %s | %s |' % (k, 'ok' if v['ok'] else '**FAIL**', v['text'].replace('|', '/')))
        log('')
        log('Install: `%s`' % r['install'])
        log('')


def main():
    from kl_port_check import workdir
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    o = options(sys.argv[1:])
    if len(a) == 3 and a[0] == 'build':
        sys.exit(0 if build(a[1], a[2], o)['ok'] else 1)
    elif a[:1] == ['all']:
        rest = a[1:]
        if len(rest) >= 2 and os.path.isdir(rest[0]):
            src, dst, tags = rest[0], rest[1], rest[2:]
        else:
            src, dst, tags = os.path.join(workdir(), 'build', 'z_maps'), os.path.join(workdir(), 'build', 't_maps'), rest
        res = collections.OrderedDict()
        for tag in tags or TAGS:
            print('=' * 20 + ' ' + tag)
            try:
                res[tag] = build(os.path.join(src, tag), os.path.join(dst, tag), o)
            except Exception as x:
                res[tag] = dict(ok=False, error='%s: %s' % (type(x).__name__, x), ran={}, skipped={}, failed=['(the run)'])
                traceback.print_exc()
        print('=' * 20)
        for tag, r in res.items():
            print('%s: %s; steps run: %s; left out: %s; checkers failed: %s' % (
                tag, 'PASS' if r['ok'] else 'NOT PASS', ' '.join(r['ran']) or 'none', ' '.join(r['skipped']) or 'none', ', '.join(r['failed']) or 'none'))
        sys.exit(0 if all(r['ok'] for r in res.values()) else 1)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if recheck(a[1]) else 0)
    elif a[:1] == ['table'] and len(a) >= 2:
        table(a[1], a[2:] or None)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
