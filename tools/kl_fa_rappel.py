#!/usr/bin/env python3
"""
The ROPE DESCENT for Retomoto (owner 2026-10-11 23:15: "definitely rappel and climb"): research tool and the
level-data half. The account, every exe address, the three forms and the live checks: re/rappel.md.
OFFLINE: nothing here installs anything or starts a game.

    python kl_fa_rappel.py facts                 what Dead Men's rappel is made of in M09_A, which Dog Days levels have
                                                 rappel clips and in which sets, the numbers of the descent
    python kl_fa_rappel.py check <folder>        read-only: the rappel slots the build's .ANM sets have, their clips'
                                                 events and sound offsets; last line RESULT (kl_fa_rappel): ...
    python kl_fa_rappel.py joins                 the MEASURED answer to 'can the three drops be chained': end pose of one clip
                                                 against the start pose of the next (L07's own .ANM), heading drift, root travel
    python kl_fa_rappel.py plan <clip> X Y Z [yaw]  where a PosObject must stand so that clip lands the feet at (X, Y, Z)
    python kl_fa_rappel.py apply <folder> <out>  the build with Dog Days' OWN rappel clips (L07, 'Repelling_01..03' and
                                                 the two one-frame pose clips) added to the animation sets of the
                                                 people a Fragile Alliance level has; exit 1 on a FAIL

WHAT apply ADDS (an addition; nothing of the build is taken away or moved; only the .ANM member of the archive differs)
  Dog Days L07 ('Construction_Midship_Repelling', its enemies rappel a building side by MiniCutsceneRout + a clip
  from a PosObject) has five slots '/Level_Specific/L07/Situations/L07_Repelling_Enemies/Repelling_01 | _02 | _03 |
  _02_1F | _03_1F' in every one of its people sets, all five naming the SAME five clips (data, 7 sets of L07). No Fragile
  Alliance level has them. The three real clips are 105 + 90 + 82 frames at 25 a second and their root moves
  17.6 + 14.9 + 13.0 m along the clip's own y axis (net -1756 / -1487 / -1300 units).
  READ IN L07 (the MiniCutPosObject strings of its squads): the three are ALTERNATIVE drops, not stages - the places
  POS_Repelling_01 / _02 / _03 stand at world y 1756 / 1487 / 1300, i.e. exactly each clip's drop above the ground
  (y 0), identity rotation (so the clip's -y is world down: the clips fall straight down their PosObject).
  CHAINING THEM IS REFUTED (`joins`, measured from the keys, 2026-10-11): the end pose of one clip is 12.7 .. 40.9 degrees
  (mean over the shared bones; the pelvis 130 .. 179) away from the start pose of the next, so a chain snaps at every join,
  and Repelling_03 turns the root by 53 degrees on the way. The root drops add to 45.4 m, but the poses do not join. What
  the data supports is ONE clip a bot (or the human): Repelling_01 (17.6 m, 4.2 s, no heading drift, 1.6 m sideways) from
  a hang that is Repelling_03_1F (8.5 degrees from its first frame; the 02 / 03 `_1F` poses ARE their clips' frame 0, 0.0
  degrees). `plan` computes the PosObject place from the wanted landing. Retomoto's rope (44.7 m) is therefore NOT descended
  whole: the descent starts 17.6 m above the balcony row. The heading of L07's POS_Repelling_01 (turned 180 degrees from
  _02 / _03) is still not read: `plan` takes it as a parameter.
  Each clip is added to the build's sets of the same name (Kane, Lynch, Kane_NPC, Thug, Civilian from L07's set of
  that name; Lynch_NPC from L07's Lynch; Swat_02 from L07's Police). The clips carry Dog Days' own event data
  (none of them has an event) and the same bones as the base (proved). Clip record +0x2C is an offset into the
  level's own .SND (luvsic, re/luvsic_pass.md 1.2): it is set by NAME in the build's bank or cleared.

WHAT apply DOES NOT DO (and why) - re/rappel.md 5
  - It adds no MiniCutsceneRout / PosObject / rope model nodes: the engine is not told to play anything. Without
    them the clips are inert (nothing asks for the slots). The node pattern (L07 / L10 'MC_Repell') is listed in
    re/rappel.md 4; building it needs the descent's world orientation, which only a live play gives.
  - It does not carry Dead Men's own /Movement/Rappelling/* clips: Dog Days' player movement ZFFPlayerMovementRappel
    (kl2 vtable 0xbb5ebc, made at 0x51d2c6 as movement 16) looks the slots up at 0x77ac7a but nothing in the level
    format enters it; the free rappel of Dead Men is a hook job (re/rappel.md 3, form C).
"""
import collections, json, os, re, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_anm, kl_anmjoin

SOURCE = 'L07'                                  # the Dog Days level the clips are taken from
SLOT_RE = re.compile(r'/L07_Repelling_Enemies/')
# build set -> L07 set whose lists are copied (all L07 sets name the same clips; the name is for the audit trail)
SETS = collections.OrderedDict([('Kane', 'Kane'), ('Lynch', 'Lynch'), ('Kane_NPC', 'Kane_NPC'), ('Lynch_NPC', 'Lynch'),
                                ('Thug', 'Thug'), ('Civilian', 'Civilian'), ('Swat_02', 'Police')])
FPS = 25.0
# Dead Men: the rope's top (RappelBox) and the facing object, world places from re/retomoto.md line 155 and the
# M09_A scene (the RappelPoint group stands at the origin); today's start row of the balcony from the F01-slot build.
ROPE_TOP = (5999.0, 25483.0, -89.0)
FACING = (6049.0, 25650.0, -116.0)
BALCONY_Y = 21011.0                             # START points y; x 6000 / 6070, z -930 .. 770


# ------------------------------------------------------------------ helpers
def _archive(folder):
    if folder.lower().endswith('.zip'):
        return folder
    hit = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(hit) != 1:
        raise ValueError('%s: %d level archives' % (folder, len(hit)))
    return os.path.join(folder, hit[0])


def _members(zp):
    with zipfile.ZipFile(zp) as z:
        order = z.namelist()
        return order, {n: z.read(n) for n in order}


def _anm_snd(order):
    anm = [n for n in order if n.lower().endswith('.anm')]
    snd = [n for n in order if n.lower().endswith('.snd') and '_LS' not in n.upper()]
    if len(anm) != 1 or len(snd) != 1:
        raise ValueError('%d .ANM / %d .SND members' % (len(anm), len(snd)))
    return anm[0], snd[0]


def source_lists(src):
    """{L07 set: [(slot name, [(flags, clip)])]} of the five Repelling slots, slot order as the set's pool has it."""
    out = {}
    for c in src.cols:
        ls = [(src.slots[s], lst) for s, lst in sorted(c.lists().items(), key=lambda kv: c.table[kv[0]]) if SLOT_RE.search(src.slots[s])]
        if ls:
            out[c.short] = ls
    return out


def clip_numbers(a, i):
    r = a.clips[i]
    _h, frames, fps, ev = struct.unpack_from('<4h', r, 0)
    return frames, fps, ev, struct.unpack_from('<3f', r, 0x18), struct.unpack_from('<I', r, 8)[0], struct.unpack_from('<I', r, 0x2c)[0]


def descent_numbers(a, names):
    """frames / seconds / net root of the three drop clips -> dict."""
    tot_f, tot_u, rows = 0, 0.0, []
    for n in names:
        i = a.names.index(n)
        fr, fps, _ev, net, _fl, _s = clip_numbers(a, i)
        rows.append((n.split('#')[1], fr, fps, net))
        tot_f += fr
        tot_u += -net[1]
    return dict(clips=rows, frames=tot_f, seconds=tot_f / FPS, travel_units=tot_u)


# ------------------------------------------------------------------ joins / plan (offline, from the keys)
def _ang(q1, q2):
    import math
    d = abs(sum(a * b for a, b in zip(q1, q2)))
    return 2.0 * math.degrees(math.acos(min(1.0, d)))


def _yaw(q):
    import math
    x, y, z, w = q
    return math.degrees(math.atan2(2 * (w * y + x * z), 1 - 2 * (y * y + x * x)))


def clips_of(a):
    """{'Repelling_01': kl_animsheet.Clip, ...} for the five repelling clips of an Anm (the file spells the first one
    'Repilling_01'; the key is normalised)."""
    import kl_animsheet as S
    own = kl_anm.owners(a)
    out = {}
    for i, n in enumerate(a.names):
        t = n.split('#')[-1]
        if re.match(r'Rep[ie]lling_0[123](_1F)?$', t):
            out[t.replace('Repilling', 'Repelling')] = S.Clip(a, own, i)
    return out


def _pose_gap(c1, f1, c2, f2):
    rows = []
    for n in c1.tracks:
        if n in c2.tracks and n != 'GROUND':
            rows.append((_ang(c1.local(n, f1)[0], c2.local(n, f2)[0]), n))
    rows.sort(reverse=True)
    return sum(r[0] for r in rows) / len(rows), rows[:2]


def joins(a, log=print):
    """Measure whether Repelling_01 / 02 / 03 can follow one another. -> {(end clip, start clip): mean degrees}."""
    C = clips_of(a)
    big = ('Repelling_01', 'Repelling_02', 'Repelling_03')
    res = {}
    for x in big:
        for y in big:
            if x != y:
                m, top = _pose_gap(C[x], C[x].frames - 1, C[y], 0)
                res[(x, y)] = m
                log('  end of %s -> start of %s: mean %5.1f degrees over %d bones, worst %s' % (
                    x, y, m, len(C[x].tracks) - 1, ', '.join('%s %.0f' % (n, d) for d, n in top)))
    for x in big:
        g0, g1 = C[x].local('GROUND', 0), C[x].local('GROUND', C[x].frames - 1)
        log('  %s: root heading %.0f -> %.0f degrees, root travel (%.0f, %.0f, %.0f) units in %.1f s' % (
            x, _yaw(g0[0]), _yaw(g1[0]), g1[1][0] - g0[1][0], g1[1][1] - g0[1][1], g1[1][2] - g0[1][2], C[x].frames / FPS))
    for x in ('Repelling_02', 'Repelling_03'):
        log('  hang pose %s_1F against frame 0 of %s: %.1f degrees; against frame 0 of Repelling_01: %.1f degrees' % (
            x, x, _pose_gap(C[x + '_1F'], 1, C[x], 0)[0], _pose_gap(C[x + '_1F'], 1, C['Repelling_01'], 0)[0]))
    log('  CHAIN: best join %.1f, worst %.1f degrees mean: %s' % (min(res.values()), max(res.values()),
        'a snap at every join (a chain is NOT supported)' if min(res.values()) > 5.0 else 'joins'))
    return res


def plan(a, clip, target, yaw=0.0, log=print):
    """PosObject place for a clip that lands at `target`. Root travel net = GROUND place at the last frame minus the first
    (clip frame: x right, y up, z back). Turned by `yaw` degrees about y (ASSUMED convention: x' = x cos + z sin,
    z' = -x sin + z cos). L07 uses yaw 0 (identity) for 02 / 03."""
    import math
    c = clips_of(a)[clip]
    g0, g1 = c.local('GROUND', 0)[1], c.local('GROUND', c.frames - 1)[1]
    net = [g1[i] - g0[i] for i in range(3)]
    t = math.radians(yaw)
    rx = net[0] * math.cos(t) + net[2] * math.sin(t)
    rz = -net[0] * math.sin(t) + net[2] * math.cos(t)
    pos = (target[0] - rx, target[1] - net[1], target[2] - rz)
    log('  %s: %d frames = %.1f s, net root (%.0f, %.0f, %.0f) -> PosObject at (%.0f, %.0f, %.0f), yaw %g, heading at the end %.0f degrees' % (
        clip, c.frames, c.frames / FPS, net[0], net[1], net[2], pos[0], pos[1], pos[2], yaw, yaw + _yaw(c.local('GROUND', c.frames - 1)[0])))
    return pos


# ------------------------------------------------------------------ facts
def facts(log=print):
    import zipfile as zf, glob
    import kl_port_check as P
    dm_root, dd_root = P.find(P.DM_GUESSES, P.DM_EXE), P.find(P.DD_GUESSES, P.DD_EXE)
    log('Dead Men (kaneandlynch.exe): ZFFPlayerMovementRappel vtable 0x967144 (43 slots, ctor 0x606dd0 called at 0x5ef287), '
        'Locomotion::ZFFRappelling 0x9681d4 (NPC), ZRappellingBox 0x97bca4 (controller on a box), ZRappelCheckPoint 0x97dff4, ZRopeLnkObj 0x97a79c, ZAppendage 0x960144.')
    log('Dog Days (kl2.exe): the same five classes, vtables 0xbb5ebc / 0xb6c648 / 0xbc23bc / 0xbc3e14 / 0xbc14ec; the player movement is made as movement 16 '
        '(0x51d2c6 push 0x10, size 0x2020, ctor 0x7b5bc0). Stock Dog Days levels use ZRappellingBox 0 times and ZRopeLnkObj 0 times.')
    dm = kl_anm.Anm(kl_anmjoin.stock_anm('M09_A', 'dm'))
    slots = [s for s in dm.slots if 'Rappelling' in s]
    log('Dead Men .ANM: %d slots /Movement/Rappelling/* (%s) in 8 sets (PlayerCharacter Lynch_Coop Army Mercenary_04 Female Civilian Bouncer Thug), '
        '12 clips of 13..151 frames, flags 0xc0 / 0x40, clip record +0x2C non-zero in 4 of them.' % (len(slots), ', '.join(s.rsplit('/', 1)[1] for s in slots)))
    log('Dog Days .ANM: NO /Movement/Rappelling slot or clip in any of the 21 stock files.')
    rows = []
    for zp in sorted(glob.glob(os.path.join(dd_root, 'Scenes', 'Locations', '*', '*_Main.zip'))):
        bak = os.path.join(dd_root, 'KL_PortBackup', os.path.relpath(zp, dd_root))
        zp = bak if os.path.isfile(bak) else zp
        with zf.ZipFile(zp) as z:
            a = kl_anm.Anm(z.read(next(n for n in z.namelist() if n.lower().endswith('.anm'))), 'dd')
        sl = [i for i, s in enumerate(a.slots) if re.search('repel|rappel', s, re.I)]
        if sl:
            sets = [c.short for c in a.cols if any(s in c.lists() for s in sl)]
            rows.append((os.path.basename(os.path.dirname(zp)), len(sl), sets))
    for lv, n, sets in rows:
        log('  Dog Days %s: %d repelling slots in sets %s' % (lv, n, ', '.join(sets)))
    src = kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dd'), 'dd')
    srcl = source_lists(src)
    names = [src.names[lst[0][1]] for _s, lst in next(iter(srcl.values())) if lst[0][0] == 0]
    d = descent_numbers(src, names[:3])
    for n, fr, fps, net in d['clips']:
        log('    L07 clip %-16s %3d frames at %g/s, root net (%.0f, %.0f, %.0f)' % (n, fr, fps, net[0], net[1], net[2]))
    log('  the three drops end to end: %d frames = %.1f s, %.1f m of root travel (the ROOT adds up; the POSES do not join, below); Retomoto: rope top y %.0f, balcony row y %.0f = %.1f m' % (
        d['frames'], d['seconds'], d['travel_units'] / 100.0, ROPE_TOP[1], BALCONY_Y, (ROPE_TOP[1] - BALCONY_Y) / 100.0))
    joins(src)
    plan(src, 'Repelling_01', (6000.0, BALCONY_Y, 0.0))
    return rows


# ------------------------------------------------------------------ merge
def merge(raw, snd, log=print):
    """Dog Days .ANM `raw` + L07's five Repelling slots in the sets of SETS the file has. -> (bytes, report)."""
    base = kl_anm.Anm(raw)
    if base.game != 'dd':
        raise ValueError('the base is not a Dog Days .ANM')
    src = kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dd'), 'dd')
    srcl = source_lists(src)
    have = {c.short for c in base.cols}
    plan = collections.OrderedDict()
    for tgt, from_ in SETS.items():
        if tgt not in have:
            continue
        if from_ not in srcl:
            raise ValueError('L07 has no set %s' % from_)
        mine = [s for s in base.slots if SLOT_RE.search(s) and base.slots.index(s) in base.col(tgt).lists()]
        if mine:
            if len(mine) == len(srcl[from_]):
                continue
            raise ValueError('%s has %d of the %d repelling slots: not a file this step made' % (tgt, len(mine), len(srcl[from_])))
        plan[tgt] = from_
    rep = collections.OrderedDict(source=SOURCE, sets=dict(plan), bytes=[len(raw), len(raw)])
    if not plan:
        return raw, rep
    out = kl_anmjoin._Out(base)
    sc = kl_anmjoin._Source(out, src, False, 'L')
    a = out.a
    cols = {c.short: c for c in a.cols}
    taken = []
    for tgt, from_ in plan.items():
        got = kl_anmjoin._add_lists(out, cols[tgt], sc, srcl[from_])
        taken += [(tgt, from_, n) for n in got]
    first_new = len(base.clips)
    a.data = bytes(out.data)
    kl_anm.relist(a)
    snd_rep = dict(kl_anm.fix_clip_sounds(a, first_new, kl_anmjoin.stock_snd(SOURCE, 'dd'), snd))
    res = a.save()

    bad = []
    re_ = kl_anm.Anm(res, 'dd')
    if re_.save() != res:
        bad.append('the written file does not read back to the same bytes')
    bad += ['audit: ' + b for b in kl_anm.audit(re_)[:10]]
    n = len(base.clips)
    for what, x, y in (('clip records', re_.clips[:n], base.clips), ('clip names', re_.names[:n], base.names),
                       ('data', re_.data[:len(base.data)], base.data), ('bone names', re_.bones[:len(base.bones)], base.bones),
                       ('pose names', re_.poses[:len(base.poses)], base.poses), ('slot names', re_.slots[:len(base.slots)], base.slots),
                       ('manager dwords 9..12', re_.head[9:13], base.head[9:13])):
        if x != y:
            bad.append('the base changed: %s' % what)
    rc = {c.short: c for c in re_.cols}
    if [c.name for c in re_.cols] != [c.name for c in base.cols]:
        bad.append('the base changed: the sets or their order')
    for c in base.cols:
        mine, theirs = rc[c.short].lists(), c.lists()
        if any(mine.get(k) != v for k, v in theirs.items()):
            bad.append('the base changed: slot lists of %s' % c.short)
        extra = sorted(re_.slots[k] for k in mine if k not in theirs)
        want = sorted(s for s, _l in srcl[plan[c.short]]) if c.short in plan else []
        if extra != want:
            bad.append('%s gained %s, wanted %s' % (c.short, extra, want))
    own_r, own_s, cache = kl_anm.owners(re_), kl_anm.owners(src), {}
    for tgt, from_, slot in taken:
        theirs, mine = src.col(from_).lists()[src.slots.index(slot)], rc[tgt].lists()[re_.slots.index(slot)]
        want = [(f, kl_anmjoin.signature(src, i, own_s)) for f, i in theirs]
        got = [(f, kl_anmjoin.signature(re_, i, own_r, cache)) for f, i in mine]
        if got != want:
            bad.append('%s %s: not the clips of L07\'s %s' % (tgt, slot, from_))
    if len(re_.bones) != len(base.bones) or len(re_.poses) != len(base.poses):
        bad.append('bone / pose names were added: %s %s' % (re_.bones[len(base.bones):], re_.poses[len(base.poses):]))
    order = sorted(range(len(re_.slots)), key=lambda i: re_.slots[i].encode('latin1'))
    if [re_.slots[i] for i in order] != sorted(re_.slots, key=lambda s: s.encode('latin1')) or len(set(re_.slots)) != len(re_.slots):
        bad.append('the slot name index is not sorted / not unique')
    bad += ['sound: clip %d value %#x %s' % t for t in kl_anm.clip_snd_bad(re_, snd)]
    if bad:
        raise ValueError('the merged .ANM fails its proofs: ' + '; '.join(bad))
    st = out.st
    new = [re_.names[i] for i in range(n, len(re_.clips))]
    rep.update(bytes=[len(raw), len(res)], clips=[len(base.clips), len(re_.clips)], slot_names=[len(base.slots), len(re_.slots)],
               lists=len(taken), data_blocks_added=st['data blocks added'], data_bytes_added=st['data bytes added'],
               new_clips=new, strange_events=dict(out.strange), clip_sounds=snd_rep,
               descent=descent_numbers(re_, [x for x in new if x.split('#')[1] in ('Repilling_01', 'Repelling_02', 'Repelling_03')]))
    log('  .ANM %d -> %d bytes (+%d): %d clips added in %d data blocks, slot names %d -> %d, bones %d (+0), poses %d (+0); %d lists in %d sets (%s)' % (
        len(raw), len(res), len(res) - len(raw), len(re_.clips) - n, st['data blocks added'], len(base.slots), len(re_.slots),
        len(re_.bones), len(re_.poses), len(taken), len(plan), ', '.join(plan)))
    log('  clip sounds (+0x2C, by name in the build\'s bank): %s' % ', '.join('%s %d' % kv for kv in sorted(snd_rep.items())))
    log('  proofs: reads back to the same bytes; kl_anm.audit clean; the base is a prefix and no base list changed; %d added lists = L07\'s clips (name, events + '
        'data, bone names, flags); no bone or pose name added; every clip sound offset is 0 or a record start of the build\'s bank' % len(taken))
    return res, rep


# ------------------------------------------------------------------ check
def check(folder, log=print):
    out = []

    def say(s, t):
        out.append((s, t))
        log('  %-4s %s' % (s, t))
    zp = _archive(folder)
    order, files = _members(zp)
    an, sn = _anm_snd(order)
    a = kl_anm.Anm(files[an])
    snd = files[sn]
    say('NOTE', '%s: %d clips, %d slots, sets %s' % (os.path.basename(zp), len(a.clips), len(a.slots), ' '.join(c.short for c in a.cols[:8])))
    mine = [(i, s) for i, s in enumerate(a.slots) if SLOT_RE.search(s)]
    dmr = [s for s in a.slots if 'Rappelling' in s]
    say('FAIL' if dmr else 'PASS', 'Dead Men\'s /Movement/Rappelling slots in the file: %d (this step does not carry them)' % len(dmr))
    if not mine:
        say('NOTE', 'no L07 repelling slot yet: the build has no rappel clips')
    else:
        sets = [c.short for c in a.cols if any(k in c.lists() for k, _s in mine)]
        full = [c.short for c in a.cols if all(k in c.lists() for k, _s in mine)]
        say('PASS' if sets == full else 'FAIL', '%d repelling slots, in sets %s (%s)' % (len(mine), ', '.join(sets), 'all five each' if sets == full else 'NOT all five each'))
        own = kl_anm.owners(a)
        evs = []
        for c in a.cols:
            for k, _s in mine:
                for _f, i in c.lists().get(k, []):
                    blk, oev = own[struct.unpack_from('<i', a.clips[i], 0xc)[0]]
                    evs += [struct.unpack_from('<I', a.data, blk[0] + 8 * j)[0] for j in range(oev)]
        say('PASS' if not evs else 'FAIL', 'event ids in the repelling clips: %s' % (sorted(set(evs)) or 'none'))
        bad = kl_anm.clip_snd_bad(a, snd)
        say('PASS' if not bad else 'FAIL', 'clip sound offsets not a record start of the build\'s .SND: %d' % len(bad))
        names = sorted({a.names[i] for c in a.cols for k, _s in mine for _f, i in c.lists().get(k, [])})
        d = descent_numbers(a, [n for n in names if n.split('#')[1] in ('Repilling_01', 'Repelling_02', 'Repelling_03')])
        say('NOTE', 'the three drops end to end: %d frames = %.1f s, %.1f m of root travel (rope %.1f m) - the root only; the poses do not join: use ONE clip (kl_fa_rappel.py joins)' % (
            d['frames'], d['seconds'], d['travel_units'] / 100.0, (ROPE_TOP[1] - BALCONY_Y) / 100.0))
        j = joins(a, lambda _s: None)
        say('NOTE', 'chain of the added clips: best join %.1f, worst %.1f degrees mean (> 5 = a snap); same numbers as L07\'s own file' % (min(j.values()), max(j.values())))
    n_fail = sum(s == 'FAIL' for s, _t in out)
    log('RESULT (kl_fa_rappel): %s (%d FAIL)' % ('PASS' if not n_fail else 'FAIL', n_fail))
    return out


# ------------------------------------------------------------------ apply
def apply(src, dst, log=print):
    import kl_graft, kl_maps
    zp = _archive(src)
    dst = os.path.abspath(dst)
    if dst == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the out folder is the build itself')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: a build folder is never written into' % dst)
    lines = []

    def say(s=''):
        log(s)
        lines.append(s)
    say('kl_fa_rappel: %s -> %s' % (zp, dst))
    order, files = _members(zp)
    an, sn = _anm_snd(order)
    new, rep = merge(files[an], files[sn], say)
    if new == files[an]:
        raise ValueError('nothing to add: the sets have the repelling slots already')
    files[an] = new
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp and not x.startswith('rappel.'):
            shutil.copyfile(q, os.path.join(dst, x))
    with zipfile.ZipFile(zp) as za, zipfile.ZipFile(out) as zb:
        ia, ib = za.infolist(), zb.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        diff = [i.filename.rsplit('_Main', 1)[-1] for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if diff != ['.ANM']:
        raise ValueError('more than the .ANM member differs from the build: %s' % diff)
    slot = os.path.basename(zp)[:-len('_Main.zip')]
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        st = json.load(open(sj))
        st['rappel'], st['final'] = diff, kl_maps.member_ids(dst, slot)
        st['same'] = [e for e in st.get('same', []) if e not in diff]
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    say('  only the %s member differs from the build (%d members); %d files beside the archive copied' % (' / '.join(diff), len(order), len(os.listdir(dst)) - 1))
    for rj in ('dyn.json', 'fed.json'):                         # the .ANM is one of the four large blocks those steps recorded
        p = os.path.join(dst, rj)
        if os.path.isfile(p):
            d = json.load(open(p), object_pairs_hook=collections.OrderedDict)
            big = d.get('big_before')
            if isinstance(big, dict) and big.get('.ANM') == rep['bytes'][0]:
                d['big_before_rappel'] = collections.OrderedDict(big)
                big['.ANM'] = rep['bytes'][1]
                with open(p, 'w') as fh:
                    json.dump(d, fh, indent=1)
                say('  %s: its record of the large blocks continued (.ANM %d -> %d)' % (rj, rep['bytes'][0], rep['bytes'][1]))
    # KLTalk.ini (the approved countdown timing) must be untouched: byte-equal to the source build's
    for x in os.listdir(os.path.dirname(zp)):
        if x.lower() == 'kltalk.ini':
            if open(os.path.join(dst, x), 'rb').read() != open(os.path.join(os.path.dirname(zp), x), 'rb').read():
                raise ValueError('KLTalk.ini differs from the source build')
            say('  %s is byte-equal to the source build\'s' % x)
    report = collections.OrderedDict(source=zp, out=out, anm=rep, members_changed=diff)
    with open(os.path.join(dst, 'rappel.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    say('')
    res = check(dst, say)
    report['check'] = [list(r) for r in res]
    with open(os.path.join(dst, 'rappel.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(dst, 'rappel.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return report


def main():
    a = sys.argv[1:]
    if a == ['facts']:
        facts()
    elif a == ['joins']:
        joins(kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dd'), 'dd'))
    elif len(a) in (5, 6) and a[0] == 'plan':
        plan(kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dd'), 'dd'), a[1], tuple(float(x) for x in a[2:5]), float(a[5]) if len(a) == 6 else 0.0)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if any(s == 'FAIL' for s, _t in check(a[1])) else 0)
    elif len(a) == 3 and a[0] == 'apply':
        had = os.path.isdir(a[2]) and bool(os.listdir(a[2]))
        try:
            rep = apply(a[1], a[2])
        except (ValueError, KeyError) as e:
            left = not had and os.path.isdir(a[2]) and bool(os.listdir(a[2]))
            sys.exit('kl_fa_rappel: NOT applied: %s%s' % (e.args[0] if e.args else e, ' - %s HOLDS WHAT WAS WRITTEN BEFORE THAT: not a build, do not use it' % a[2] if left else ' - nothing was written'))
        sys.exit(1 if any(s == 'FAIL' for s, _t in rep['check']) else 0)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
