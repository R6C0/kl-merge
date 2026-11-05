#!/usr/bin/env python3
"""
LAST CALL (DM05A) LIFE PASS, 2026-11-05 (OFFLINE; nothing is installed or started). Owner play feedback of 2026-11-05:
  1. "all the same guy, same voice lines": more women in suits, more different looks and voices (inside the memory budget).
  2. "just outside the club is a bit too quiet, get some car noises n stuff out there".
  3. "inside the club at the entrance you can hear the music slightly then it just goes dead silent in some parts of the club".

A separable POST-PASS on the finished map zip: it chains with tools/kl_club_fight_1105.py (the combat pass) in either order, because it
touches no entity, squad, route or nav data. Zip members it changes: .prp (always: looks, voices, emitters, music list), .gms (model id
of the actors that change model), .prm / .TEX / .MAT (the women's model + textures, kl_chars.put), .SND (the female voice sets); beside the
zip: F01_Main_LS.SND (the .SND's load-screen twin), F01_Main.bots.zip + .bots.base.md5 (the [BotGate] sibling, regenerated), KLJoin.ini and
KLGuns.ini (only their Entries= line, the new .prm chunk count). Unchanged on purpose: .fxc, .oct, .ANM, .WHD, .WAV, .buf, .sgd, ...

  python kl_club_life_1105.py stage [--src <folder>] [--out <dir>] [--wide] [--force]
        --src  folder with F01_Main.zip + the files beside it (default: the live map folder, READ ONLY; a copy is better)
        --out  default C:\\kl_build_1024\\lastcall_life_1105 ; writes <out>\\stage with the changed files, install.py (+ UNDO), build_report.json
        --wide two women looks (F08 1621 + 1680) instead of one (1621): +2.3 MB .TEX
  python kl_club_life_1105.py check <stage dir> <src folder>

WHAT IT DOES
  1. LOOKS. All 40 crowd civilians are Dog Days model 41803 variant 1 (one man) with the male voice pair. 30 % become a woman
     (Dog Days F08 'Civ_OfficeWorker_F_02', model 1621; --wide adds 1680) grafted with kl_chars.put from the stock F08 archive (a
     DDSource shim: kl_chars.Source reads Dead Men only); the other 70 % are spread over the 8 men looks the map's .prm already holds
     (41803 v1..v4 and 41556 v2,v3,v4,v6: different suits, headsets, hair, glasses). Nothing is added to the .prm for the men.
  2. VOICES. kl_snd.merge copies the two female civilian voice definitions of F08 (civilian_female, civilian_female_02: 2 defs + 8 sets,
     every wave is already in the live bank, so .WHD and .WAV do not change; +1776 bytes of .SND) and the women get slots
     (female, female_02, 0). Men keep their pair. Only two male and two female sets exist in Dog Days, so a third voice does not.
  3. STREET. 7 unreferenced duplicate roof ventilation emitters (RAM!Outside!Ventilation_Outside#01..#06, Ventilation_Air#03) become
     street traffic emitters just outside the entrance: car horns, truck/bus, idling car, moped horns, moped engine, tyre squeal, siren,
     all sets the live bank already holds. Gate: the Street_01 bed's own limiter lists (on = Streetbox, off = inside + rooftop boxes).
  4. MUSIC. Rooms with no music layer (CarShop_01a, Stairs_01a, Daughter_Room_01b) are added to the on-list of the muffled club layer
     (Club_01_Muffled_Music_01), so they hear the club muffled instead of nothing. Quieter in back rooms, never silent.
"""
import collections, hashlib, json, os, random, re, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_chars as C
import kl_prmgraph as G
import kl_texmat as T
import kl_prpjoin as J
import kl_octree as O
import kl_anm
import kl_gms
import kl_scene
import kl_snd as S
import kl_voice as V
import kl_fa
import kl_fa_author as AU
import kl_fa_bots as KB
import kl_club_lastcall3 as L3
import kl_club_lastcall5 as L5
import kl_botsonline

BS = chr(92)
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
OUT = r'C:\kl_build_1024\lastcall_life_1105'
CIVS_JSON = r'C:\kl_build_1024\club_1024d\DM05A\civs.json'
TAG = '.before-1105life'
SEED = 1105
WOMEN_SHARE = 0.30
F08 = 'F08'
WOMEN_MODELS = ['1621']                              # --wide adds '1680'
MEN_LOOKS = [('dd', 41803, 1, 0.125), ('dd', 41803, 2, 0.125), ('dd', 41803, 3, 0.125), ('dd', 41803, 4, 0.125),
             ('dd', 41556, 2, 0.125), ('dd', 41556, 3, 0.125), ('dd', 41556, 4, 0.125), ('dd', 41556, 6, 0.125)]
M_SND = 'Scenes/Locations/F01/F01_Main.SND'
FEMALE_DEFS = ('civilian_female#def', 'civilian_female_02#def')   # F08 bank names (suffix of the full name)
INI_FILES = ('KLJoin.ini', 'KLGuns.ini')

# STREET. emitter node (suffix of its path) -> (sound set name in the live bank, x, y, z). Positions are WORLD coordinates just outside the
# club entrance: Street_Amb_3D (the entrance's own street bed) sits at (50, 206, -2690) and the Streetbox gate spans z -6594..-2594.
# GUESS: BOX is 10000 x 1000 x 2000 as half or full extents around (1517,174,-4594); the positions stay in z -3000..-4300 so they are
# inside the box either way. GUESS: these sets (taken from F07's traffic) start themselves and loop at random intervals; if one is a
# one-shot it is audible once (a live test says).
STREET = collections.OrderedDict([
    ('RAM!Outside!Ventilation_Outside#01', ('car_horns#set', -600.0, 250.0, -3300.0)),
    ('RAM!Outside!Ventilation_Outside#02', ('truckbus#set', 1500.0, 250.0, -3600.0)),
    ('RAM!Outside!Ventilation_Outside#03', ('car_idle#set', 700.0, 250.0, -3000.0)),
    ('RAM!Outside!Ventilation_Outside#04', ('mopeds_horns#set', -1500.0, 250.0, -3800.0)),
    ('RAM!Outside!Ventilation_Outside#05', ('moped_driving#set', 300.0, 250.0, -3900.0)),
    ('RAM!Outside!Ventilation_Outside#06', ('squeals#set', 2300.0, 250.0, -3300.0)),
    ('RAM!Outside!Ventilation_Air#03', ('sirens_short/sirens_sort#set', 3200.0, 250.0, -4300.0)),
])
STREET_FADE = 3.0                                    # GUESS: list roles and the two fade floats of SoundLimiterFade, read off Street_01 / Street_Amb_3D
MUSIC_NODE = 'Music!Club_01_Muffled_Music_01'
MUSIC_ADD = ('M05_A_Inside_CarShop_01a', 'M05_A_Inside_Stairs_01a', 'M05_A_Inside_Daughter_Room_01b')

md5 = lambda b: hashlib.md5(b).hexdigest()


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


class DDSource(C.Source):
    """kl_chars.Source for a stock Dog Days level (kl_chars.Source itself reads Dead Men's)."""
    def __init__(self, level, log=print):
        import zipfile as zf
        with zf.ZipFile(J.level_zip(level, 'dd')) as z:
            m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
            rd = lambda e: z.read(m[e])
            self.level = level
            self.sc = J.Scene.load(level)
            self.prm = G.read(rd('.prm'), 'dd')
            self.tex = T.read_tex(rd('.TEX'))
            self.mat = T.read_mat(rd('.MAT'))
            self.oct = O.Oct.parse(rd('.oct'))
            self.rec = {v: k for k, v in enumerate(self.oct.record_refs())}
            self.anm = kl_anm.Anm(rd('.ANM'), 'dd').bones


def set_unit(sc, k, i, v, ctrl=None):
    """Field unit i of node k (or of its controller number `ctrl`) = v, in the token kind it already has."""
    kl_fa.edit(sc, k, ctrl, lambda us: AU.setv(sc, us, i, v))


def by_path(sc, suffix, cls=None):
    hit = [k for k in range(1, len(sc.nodes)) if sc.path[k].endswith(suffix) and (cls is None or sc.cls(k) == cls)]
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (suffix, len(hit)))
    return hit[0]


def limiter(sc, k):
    for i, (n, _b) in enumerate(sc.nodes[k]['ctrls']):
        if sc.p.key(n) == 'SoundLimiterFade':
            return i
    raise ValueError('%s has no SoundLimiterFade' % sc.path[k])


def read_set(folder):
    zp = os.path.join(folder, 'F01_Main.zip')
    with zipfile.ZipFile(zp) as z:
        snd = z.read(M_SND)
    rd = lambda n: open(os.path.join(folder, n), 'rb').read()
    return dict(zip=zp, snd=snd, whd=rd('F01_Main.WHD'), wav=rd('F01_Main.WAV'), ls=rd('F01_Main_LS.SND'))


# ------------------------------------------------------------------ build
def build(src, work, women, log=print, force=False):
    """src: folder with the map. work: an empty scratch folder. -> (report, files {name: bytes}) ; nothing is written outside `work`."""
    rep = collections.OrderedDict(src=src, src_zip_md5=fmd5(os.path.join(src, 'F01_Main.zip')))
    live = read_set(src)
    lv = C.Lv(src)
    sc0, _ = lv.scene()
    acts = L5.civ_actors(sc0)
    paths = sorted(sc0.path[k].replace('ROOT' + BS, '', 1) for k in acts)
    log('civilians: %d  looks now: %s' % (len(acts), dict(collections.Counter(C.person(sc0, k)[:2] for k in acts))))
    t0 = {e: len(lv[e]) for e in ('.prm', '.TEX', '.MAT', '.fxc', '.gms', '.prp')}
    # the plan: shuffled once, the first third women
    rng = random.Random(SEED)
    order = list(paths)
    rng.shuffle(order)
    nw = int(round(WOMEN_SHARE * len(order)))
    wpaths, mpaths = order[:nw], order[nw:]
    plan = L5.assign(mpaths, 0, SEED, MEN_LOOKS)
    # 1. women: Dog Days F08 office workers
    C._SOURCE[F08] = DDSource(F08)
    picks, chunk = [], (len(wpaths) + len(women) - 1) // len(women)
    for i, m in enumerate(women):
        ps = wpaths[i * chunk:(i + 1) * chunk]
        if ps:
            picks.append(C.Pick(ps, F08, m, {1: 1, 2: 1}))
    prep = C.put(lv, picks, log=lambda *a: None, union=False)
    if len(lv['.fxc']) != t0['.fxc']:
        raise ValueError('.fxc changed: the women need no new effect, expected it untouched')
    rep['put'] = dict(materials=prep.get('materials'), textures=prep.get('textures'))
    # 2. men's looks + the model record, then the women's voices
    sc, raw = lv.scene()
    raw = bytearray(raw)
    models = C.gms_models(raw)
    byp = {sc.path[k].replace('ROOT' + BS, '', 1): k for k in range(1, len(sc.nodes))}
    done = collections.Counter()
    for p, (_kind, m, v) in plan.items():
        k = byp[p]
        struct.pack_into('<I', raw, models[k - 1][0], m)
        L5.set_prop(sc, k, 'ZGEOM[4]', m)
        L5.set_prop(sc, k, 'ZLNKOBJ[0]', v)
        done[('man', m, v)] += 1
    wk = [byp[p] for p in wpaths]
    for k in wk:
        m, v, a = C.person(sc, k)
        done[('woman', m, v)] += 1
    rep['looks'] = {'%s %s v%s' % k: n for k, n in sorted(done.items())}
    log('looks: %s' % rep['looks'])
    # 3. the female voice sets from F08
    src8 = S.bank(F08, 'dd')
    roots = {o for o, t in src8.kind.items() if t == 5 and any(src8.name(o).endswith(n.encode()) for n in FEMALE_DEFS)}
    if len(roots) != 2:
        raise ValueError('F08: %d female civilian defs (want 2)' % len(roots))
    base = S.Snd('dd', live['snd'], live['ls']).walk()
    st = collections.Counter()
    snd, whd, wav, omap = S.merge(base, src8, live['whd'], live['wav'], S.read(S.beside(F08, '.WHD', 'dd')), S.read(S.beside(F08, '.WAV', 'dd')),
                                  roots, log=lambda *a: None, stats=st)
    if whd != live['whd'] or wav != live['wav']:
        raise ValueError('the merge changed .WHD/.WAV: expected a pure .SND addition (every wave is already in the live bank)')
    byname = {src8.name(o): omap[o] for o in roots}
    female = [omap[o] for o in sorted(roots, key=lambda o: src8.name(o)) ]       # civilian_female, civilian_female_02 (name order)
    log('female voice defs: %s  (.SND %d -> %d, merge %s)' % ([hex(x) for x in female], len(live['snd']), len(snd), dict(st)))
    for k in wk:
        V.set_voice(sc, k, [female[0], female[1], 0])
    ls = S.ls_bank(live['ls'], S.u32(snd, 0))
    rep['snd'] = dict(before=len(live['snd']), after=len(snd), female=[hex(x) for x in female], stats=dict(st))
    # 4. street emitters
    sref = by_path(sc, 'Street_Group!Street_01', 'ZSNDOBJ')
    lim = kl_fa.value(sc, units_of(sc, sref, limiter(sc, sref))[0]), kl_fa.value(sc, units_of(sc, sref, limiter(sc, sref))[1])
    on_list, off_list = lim
    names = {}
    for o, t in base.kind.items():
        if t == 2:
            names.setdefault(base.name(o).decode('latin1'), o)
    street, moved = [], {}
    for suf, (setname, x, y, z) in STREET.items():
        k = by_path(sc, suf, 'ZSNDOBJ')
        hit = [o for n, o in names.items() if n.endswith('/' + setname)]
        if len(hit) != 1:
            raise ValueError('%s: %d sets in the live bank' % (setname, len(hit)))
        if kl_fa.node_values(sc, k)[8:10][1] not in (0, 1):
            raise ValueError('%s: unexpected emitter flag' % suf)
        refs = [(r) for r in refs_to(sc, k)]
        if refs:
            raise ValueError('%s is referenced by %s: not an unreferenced duplicate' % (suf, refs[:3]))
        set_unit(sc, k, 8, hit[0])
        set_unit(sc, k, 2, [x, y, z])
        i = limiter(sc, k)
        kl_fa.edit(sc, k, i, lambda us: (us.__setitem__(0, kl_fa._refs(sc, on_list)), us.__setitem__(1, kl_fa._refs(sc, off_list)),
                                          AU.setv(sc, us, 2, STREET_FADE), AU.setv(sc, us, 3, STREET_FADE)))
        moved[k] = (x, y, z)
        street.append((suf, setname, hex(hit[0]), (x, y, z)))
    rep['street'] = street
    # 5. music on-list
    mk = by_path(sc, MUSIC_NODE, 'ZSNDOBJ')
    mi = limiter(sc, mk)
    now = kl_fa.value(sc, units_of(sc, mk, mi)[0])
    prefix = now[0].rsplit(BS, 1)[0]
    add = []
    for r in MUSIC_ADD:
        full = prefix + BS + r
        if r not in {sc.path[k].rsplit(BS, 1)[-1] for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZROOM'}:
            raise ValueError('no room %s' % r)
        if full not in now:
            add.append(full)
    kl_fa.edit(sc, mk, mi, lambda us: us.__setitem__(0, kl_fa._refs(sc, now + add)))
    rep['music_added'] = [a.rsplit(BS, 1)[-1] for a in add]
    # 6. serialize
    # the emitters' .gms records carry the position too (kept equal to the .prp's ZGEOM[2], as a build does; the exe reads the .prp's);
    # kl_scene round-trips the stock .gms/.buf byte for byte, so only these records change
    scn = kl_scene.Scene(bytes(raw), lv['.buf'])
    ents = list(scn.entities())
    for k, pos in moved.items():
        ents[k - 1].trans = struct.pack('<3f', *pos) + bytes(4)
    graw, lv['.buf'] = scn.write()
    lv['.gms'], lv['.prp'] = kl_gms.pack(graw), sc.p.serialize()
    lv['.SND'] = snd
    lv.beside['_LS.SND'] = os.path.join(work, 'F01_Main_LS.SND')
    os.makedirs(work, exist_ok=True)
    open(lv.beside['_LS.SND'], 'wb').write(ls)
    t1 = {e: len(lv[e]) for e in t0}
    nchunks = len(G.read(lv['.prm'], 'dd').chunks)
    rep['bytes'] = {e: [t0[e], t1[e], t1[e] - t0[e]] for e in t0}
    rep['bytes']['.SND'] = [len(live['snd']), len(snd), len(snd) - len(live['snd'])]
    rep['prm_chunks'] = [len(G.read(C.Lv(src)['.prm'], 'dd').chunks), nchunks]
    return rep, lv, ls, nchunks


def units_of(sc, k, i):
    from kl_prp import units
    return list(units(sc.nodes[k]['ctrls'][i][1][1:-1]))


def refs_to(sc, k):
    """[(node, where)] of every reference to node k's path in any property or controller field."""
    target = sc.path[k]
    out = []
    def walk(v, n, tag):
        if isinstance(v, str):
            if v.endswith(target):
                out.append((n, tag))
        elif isinstance(v, list):
            for x in v:
                walk(x, n, tag)
    from kl_prp import units
    for n in range(1, len(sc.nodes)):
        if n == k:
            continue
        try:
            for x in kl_fa.node_values(sc, n):
                walk(x, n, 'prop')
        except Exception:
            pass
        for nm, body in sc.nodes[n]['ctrls']:
            for u in units(body[1:-1]):
                walk(kl_fa.value(sc, u), n, sc.p.key(nm))
    return out


# ------------------------------------------------------------------ stage
INSTALL_PY = '''"""Installs / undoes the Last Call life pass (tools/kl_club_life_1105.py, 2026-11-05): more women and looks, female voices,
street traffic sounds, music in the quiet rooms. Each file it replaces moves to <name>%(tag)s first (never over an existing backup).
  python install.py           install       python install.py --undo    put every original back, byte for byte
  --game <dir>                a Dog Days folder other than the default (rehearsals)
Every live md5 is pinned before anything is written; nothing is written while kl2.exe runs."""
import hashlib, os, shutil, subprocess, sys

GAME = %(game)r
MAP, TAG = %(map)r, %(tag)r
FILES = %(files)r       # name -> [old md5 (None: file absent), new md5]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    a = sys.argv[1:]
    undo = '--undo' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    here = os.path.dirname(os.path.abspath(__file__))
    if '--skip-run-check' not in a and 'kl2.exe' in subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower():
        print('REFUSED: kl2.exe is running'); return 3
    live = lambda n: os.path.join(d, n)
    if undo:
        for n, (old, new) in FILES.items():
            if not os.path.isfile(live(n) + TAG):
                print('nothing to undo for %%s: no %%s' %% (n, n + TAG)); return 2
            if md5(live(n)) != new:
                print('REFUSED: %%s md5 %%s is not the installed %%s' %% (n, md5(live(n)), new)); return 2
            if md5(live(n) + TAG) != old:
                print('REFUSED: backup of %%s is not md5 %%s' %% (n, old)); return 2
        for n in FILES:
            os.replace(live(n) + TAG, live(n))
            print('restored', n)
        return 0
    for n, (old, new) in FILES.items():
        if not os.path.isfile(live(n)):
            print('REFUSED: %%s is not there' %% live(n)); return 2
        if md5(live(n)) == new and os.path.isfile(live(n) + TAG):
            print('already installed'); return 0
        if md5(live(n)) != old:
            print('REFUSED: %%s md5 %%s is not the pinned %%s (the map changed since this was staged)' %% (n, md5(live(n)), old)); return 2
        if os.path.exists(live(n) + TAG):
            print('REFUSED: %%s exists already' %% (live(n) + TAG)); return 2
        if md5(os.path.join(here, n)) != new:
            print('REFUSED: the staged %%s is not md5 %%s' %% (n, new)); return 2
    if shutil.disk_usage(d).free < sum(os.path.getsize(os.path.join(here, n)) for n in FILES) + (1 << 30):
        print('REFUSED: less than the files + 1 GB free on the game drive'); return 2
    done = []
    try:
        for n, (old, new) in FILES.items():
            os.replace(live(n), live(n) + TAG)
            done.append(n)
            shutil.copyfile(os.path.join(here, n), live(n))
            if md5(live(n)) != new:
                raise OSError('copy of %%s failed' %% n)
            print('installed', n)
    except OSError as e:
        for n in reversed(done):
            os.replace(live(n) + TAG, live(n))
        print('failed (%%s), originals put back' %% e); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
'''


def patch_entries(path_in, n):
    txt = open(path_in, 'rb').read().decode('latin-1')
    new, c = re.subn(r'(?m)^(Entries\s*=\s*)\d+', lambda m: m.group(1) + str(n), txt)
    return new.encode('latin-1'), c


def stage(src, out, wide=False, force=False, log=print):
    st = os.path.join(out, 'stage')
    work = os.path.join(out, '_work')
    for d in (st, work):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    rep, lv, ls, nchunks = build(src, work, WOMEN_MODELS + (['1680'] if wide else []), log, force)
    zp = lv.write(os.path.join(work, 'out'))
    shutil.copyfile(zp, os.path.join(st, 'F01_Main.zip'))
    shutil.copyfile(os.path.join(work, 'F01_Main_LS.SND'), os.path.join(st, 'F01_Main_LS.SND'))
    # [BotGate] sibling
    plain = os.path.join(st, 'F01_Main.zip')
    if os.path.isfile(os.path.join(src, 'F01_Main.bots.zip')):      # a map without the sibling (a bare combat-pass stage) gets none
        kl_botsonline.convert(plain, os.path.join(st, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
        open(os.path.join(st, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(fmd5(plain) + '\n')
    # the Entries= of the two hook files
    for n in INI_FILES:
        if os.path.isfile(os.path.join(src, n)):
            data, c = patch_entries(os.path.join(src, n), nchunks)
            if c != 1:
                raise ValueError('%s: %d Entries= lines' % (n, c))
            open(os.path.join(st, n), 'wb').write(data)
    files = collections.OrderedDict()
    for n in sorted(os.listdir(st)):
        old = os.path.join(src, n)
        if not os.path.isfile(old):
            raise ValueError('%s has no live original to back up' % n)
        o = fmd5(old)
        if o == fmd5(os.path.join(st, n)):                     # nothing changed (e.g. the ini already has the count): do not touch it
            os.remove(os.path.join(st, n))
            continue
        files[n] = [o, fmd5(os.path.join(st, n))]
    with open(os.path.join(st, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map='DM05A', tag=TAG, game=GAME, files=dict(files)))
    rep['files'] = files
    rep['members_changed'] = members_changed(os.path.join(src, 'F01_Main.zip'), plain)
    shutil.rmtree(work, ignore_errors=True)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    log('staged %s' % st)
    for n, (o, nw) in files.items():
        log('  %-28s %s -> %s' % (n, o[:8], nw[:8]))
    log('  members changed: %s' % ' '.join(rep['members_changed']))
    return rep


def members_changed(a, b):
    with zipfile.ZipFile(a) as za, zipfile.ZipFile(b) as zb:
        if za.namelist() != zb.namelist():
            raise ValueError('member list/order differs')
        return [n.rsplit('_Main', 1)[-1] for n in za.namelist() if za.read(n) != zb.read(n)]


# ------------------------------------------------------------------ check
def check(stg, src, log=print):
    bad = []
    zp = os.path.join(stg, 'F01_Main.zip')
    lv = C.Lv(stg)                                      # needs only the zip; the beside files are the staged ones
    sc, raw = lv.scene()
    acts = L5.civ_actors(sc)
    c = collections.Counter(C.person(sc, k)[:2] for k in acts)
    log('looks now: %s' % dict(c))
    if len(acts) != 40:
        bad.append('%d civilians (want 40)' % len(acts))
    if len(c) < 6:
        bad.append('only %d distinct looks' % len(c))
    women = [k for k in acts if C.person(sc, k)[0] not in (41803, 41556)]
    if not women:
        bad.append('no women')
    prm = G.read(lv['.prm'], 'dd')
    zg = J.labels('dd', 'ZFFActor').index('ZGEOM[4]')
    for k in acts:                                         # what kl_fa_civs.check asks of every actor: its model chunk is a live, walkable root
        m = kl_fa.value(sc, units_of_node(sc, k)[zg])
        if not G.walk(prm, [m]):
            bad.append('node %d: model %s is not a live root' % (k, m))
    labels = J.labels('dd', 'ZFFActor')
    snd = lv['.SND']
    bank = S.Snd('dd', snd, open(os.path.join(stg, 'F01_Main_LS.SND'), 'rb').read()).walk()
    voices = collections.Counter()
    for k in acts:
        us = units_of_node(sc, k)
        slots = tuple(kl_fa.value(sc, us[labels.index('ZLNKWHANDS[%d]' % i)]) for i in range(3))
        nm = tuple(bank.name(s).decode('latin1').rsplit('/', 1)[-1] if s else None for s in slots)
        voices[(C.person(sc, k)[0] not in (41803, 41556), nm)] += 1
        for s in slots:
            if s and bank.kind.get(s) != 5:
                bad.append('node %d voice slot %#x is not a def' % (k, s))
    log('voices: %s' % dict(voices))
    for (w, nm), n in voices.items():
        if w != any('female' in (x or '') for x in nm):
            bad.append('woman/voice mismatch %s %s' % (w, nm))
    # .SND against the live one: a pure addition
    live = read_set(src)
    problems, _n = S.verify(S.Snd('dd', live['snd'], live['ls']).walk(), snd, live['whd'], live['wav'], open(os.path.join(stg, 'F01_Main_LS.SND'), 'rb').read())
    bad += [p for p in problems if not p.startswith('stock bytes below')]
    # unchanged members
    chg = members_changed(os.path.join(src, 'F01_Main.zip'), zp)
    log('members changed: %s' % chg)
    for must in ('.fxc', '.ANM', '.buf', '.sgd'):
        if must in chg:
            bad.append('%s changed' % must)
    for n in os.listdir(stg):
        if n.endswith('.ini'):
            m = re.search(rb'(?m)^Entries\s*=\s*(\d+)', open(os.path.join(stg, n), 'rb').read())
            nch = len(G.read(lv['.prm'], 'dd').chunks)
            if not m or int(m.group(1)) != nch:
                bad.append('%s Entries %s != prm chunks %d' % (n, m and m.group(1), nch))
    # bots sibling
    if not os.path.isfile(os.path.join(stg, 'F01_Main.bots.zip')):
        return bad
    base = open(os.path.join(stg, 'F01_Main.bots.base.md5')).read().strip()
    if base != fmd5(zp):
        bad.append('bots.base.md5 is not the plain zip md5')
    if members_changed(zp, os.path.join(stg, 'F01_Main.bots.zip')) != ['.prp']:
        bad.append('bots.zip differs from the plain zip in more than the .prp')
    return bad


def units_of_node(sc, k):
    from kl_prp import units
    return list(units(sc.nodes[k]['props'][1:-1]))


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a and a[0] == 'stage':
        stage(opt('--src', LIVE), opt('--out', OUT), '--wide' in a, '--force' in a)
        return 0
    if a and a[0] == 'check' and len(a) == 3:
        bad = check(a[1], a[2])
        for b in bad:
            print('FAIL', b)
        print('RESULT: %s' % ('FAIL (%d)' % len(bad) if bad else 'PASS'))
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
