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
    python kl_fa_rappel.py build <folder> <out> [--land X Y Z] [--delay S]   (2026-10-12) apply's clips PLUS the cut for the local human: a squad + a
                                                 one-act 'Lynch' MiniCutsceneRout + a PosObject 17.6 m over the landing + a TriggerDelay2 started by the
                                                 round-start event + a [Rappel] section in KLJoin.ini for klhook/klrappel.c; re/rappel.md 8
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
    if os.path.isfile(os.path.join(folder, 'KLJoin.ini')) and b'[Rappel]' in open(os.path.join(folder, 'KLJoin.ini'), 'rb').read():
        for x in check_cut(folder, log):
            out.append(x)
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


# ------------------------------------------------------------------ build: the cut (round two, 2026-10-12)
GROUP, SQUAD, ROUT, POS, TIMER = 'KL_Rappel!', 'Rappel_Squad', 'Rappel', 'PosObject_Rappel', 'Rappel_Timer'
CLIP = 'Repelling_01'
SLOT = '/Level_Specific/L07/Situations/L07_Repelling_Enemies/Repelling_01'
LAND = (6100.0, 21011.0, -100.0)        # the balcony row: floor y 21011 from x 5850 to 6150 (Ground.under, 2026-10-12), a gap between the spawn rows z -690 and 530
FACE = (-1.0, 0.0)                      # he faces the facade (-x); the START rows face -x as well
DELAY = 2.0                             # GUESS: seconds after the round-start event (the clip is 4.2 s; GO is 8.4 - 8.8 s after the event, the blast 16.5 s)
RT_TALK = 'rt_full6/retomoto_full/KLTalk.ini'
TIMER_DONOR = ('F07', 'ROOT\\Gameplay!merc_bot_squad!Timer_start_bots')
STEP = 4                                # profile sample step in frames (104 / 4 = 26 intervals -> 27 values)


def world_net(net, face):
    """The clip's root travel (clip frame: x right, y up, z BACK; he looks along local -z) in the world, for a body facing `face` (x, z).
    ASSUMPTION (sign conventions, re/rappel.md 8.3): local -z is `face`, local +x is its right-hand side:
    x' = x * fz - z * fx,  z' = x * fx - z * fz  (face (-1, 0): x' = z, z' = -x)."""
    fx, fz = face
    return (net[0] * fz - net[2] * fx, net[1], net[0] * fx - net[2] * fz)


def profile(a, clip=CLIP):
    """The clip's vertical root path as thousandths of the drop at every STEP-th frame -> (frames, net, [ints])."""
    c = clips_of(a)[clip]
    g = [c.local('GROUND', f)[1] for f in range(c.frames)]
    net = tuple(g[-1][i] - g[0][i] for i in range(3))
    if not (net[1] < -500.0):
        raise ValueError('%s: the root does not drop (%r)' % (clip, net))
    out = [int(round(1000.0 * (g[0][1] - g[min(f, c.frames - 1)][1]) / -net[1])) for f in range(0, c.frames - 1 + STEP, STEP)]
    out = [max(0, min(1000, v)) for v in out]
    out[0], out[-1] = 0, 1000
    for i in range(1, len(out)):
        out[i] = max(out[i], out[i - 1])
    return c.frames, net, out


def rappel_ini(frames, start, land, prof, slot=SLOT):
    return ('\n[Rappel]\n; written by tools\\kl_fa_rappel.py build for klhook\\klrappel.c ([Rappel] Enable=1 in KLHook.ini): the human\'s rope descent.\n'
            '; Start = the PosObject of the cut (the node is put there by the game), Land = the balcony row, Profile = the clip\'s vertical root path\n'
            '; in thousandths at every %d-th frame (the game does not apply the root motion of that cut: re\\rappel.md 8).\n'
            'Clip=%s\nFrames=%d\nStart=%.1f %.1f %.1f\nLand=%.1f %.1f %.1f\nProfile=%s\n') % (
        STEP, slot, frames, start[0], start[1], start[2], land[0], land[1], land[2], ' '.join(str(v) for v in prof))


def build(src, dst, land=LAND, face=FACE, delay=DELAY, log=print):
    """The build `src` written to the NEW folder `dst`: the L07 rappel clips in the .ANM (apply's merge), ONE cut for the local human
    (squad + MiniCutsceneRout with a 'Lynch' head and one act + a PosObject 17.6 m over `land`), a TriggerDelay2 `delay` seconds after the
    round-start event (AIMonitor list 2) that starts it, and a [Rappel] section in the KLJoin.ini for klhook\\klrappel.c."""
    import kl_fa_climb2 as C2
    import kl_fa, kl_gms
    import kl_prpjoin as J
    import kl_octree as O
    import kl_fa_bots as F
    import kl_fa_cover as CV
    import kl_graft, kl_maps
    B = F.Built(src)
    zp = B.zp
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the out folder is the build itself')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: a build folder is never written into' % dst)
    sc = B.sc
    if sc.resolve(F.R_ + GROUP):
        raise ValueError('the build already has %s' % GROUP)
    lines = []

    def say(s=''):
        log(s)
        lines.append(s)
    say('kl_fa_rappel build: %s -> %s' % (zp, dst))
    before = F.sizes(B.folder)
    # ---- the clips
    anm_name, snd_name = _anm_snd(B.order)
    new_anm, arep = merge(B.files[anm_name], B.files[snd_name], say)
    a_new = kl_anm.Anm(new_anm)
    frames, net, prof = profile(a_new)
    wnet = world_net(net, face)
    start = tuple(land[i] - wnet[i] for i in range(3))
    say('  %s: %d frames = %.1f s; root travel in the clip frame (%.0f, %.0f, %.0f) -> in the world for a body facing (%g, %g): (%.0f, %.0f, %.0f); '
        'PosObject (the start) at (%.0f, %.0f, %.0f), landing (%.0f, %.0f, %.0f); profile %d values' % (
            CLIP, frames, frames / FPS, net[0], net[1], net[2], face[0], face[1], wnet[0], wnet[1], wnet[2],
            start[0], start[1], start[2], land[0], land[1], land[2], len(prof)))
    # ---- the nodes
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    M = F.Maker()
    gk = CV.group_form(B)
    top = CV._node(M, B, gk, GROUP)
    M.place(top, (0.0, 0.0, 0.0))
    sq = top.add(M.clone(*C2.DONOR['squad'], name=SQUAD))
    M.place(sq, (0.0, 0.0, 0.0))
    ro = sq.add(M.clone(*C2.DONOR['rout'], name=ROUT))
    M.place(ro, (0.0, 0.0, 0.0))
    po = ro.add(M.clone(*C2.DONOR['pos'], name=POS))
    M.place(po, start, F.rot9(-face[0], -face[1]))              # he looks along face; rot9(n) holds look9(-n) (re/climb2.md): n is OUT of the wall
    tm = top.add(M.clone(*TIMER_DONOR, name=TIMER))
    M.place(tm, (0.0, 0.0, 0.0))
    M.set(ro, 'MiniCutsceneRout', {0: C2.script_for(SLOT, POS), 1: []})
    M.set(po, 'MiniCutPosObject', {0: ''})
    rout_path = F.R_ + GROUP + '\\' + SQUAD + '\\' + ROUT
    timer_path = F.R_ + GROUP + '\\' + TIMER
    M.set(tm, 'TriggerDelay2', {0: float(delay), 1: 0.0, 2: -1.0, 3: 0, 4: [rout_path]})
    for n in (sq, ro, po, tm):
        if n.links is not None or n.model:
            raise ValueError('%s: a donor with a list or a model' % n.name)
    q, order = M.scene([top])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'rappel')
    mon = Jn.resolve(F.R_ + 'Gameplay!AIMonitor')
    if len(mon) != 1:
        raise ValueError('%d Gameplay!AIMonitor nodes: nothing to start the cut from' % len(mon))
    mi = next(i for i, (nm, _b) in enumerate(Jn.nodes[mon[0]]['ctrls']) if Jn.p.key(nm) == 'AIMonitor')

    def fn(us):
        have = [Jn.p.key(t) for t in us[2][1:]]
        if timer_path.lower() not in [h.lower() for h in have]:
            us[2] = kl_fa._refs(Jn, have + [timer_path])
    kl_fa.edit(Jn, mon[0], mi, fn)
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, ents_made = nxt, {}
    nxt = C2._write_ent(A, top, None, nxt, ents_made)
    A.ref_slots = nxt
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for x, y in ids.items() if x != y)
    p = po.pos
    lo = tuple(p[i] - 10.0 for i in range(3))
    hi = tuple(p[i] + (10.0 if i != 1 else 190.0) for i in range(3))
    items = [(slot1[ents_made[id(sq)]] + 2, lo, hi), (slot1[ents_made[id(ro)]] + 2, lo, hi), (slot1[ents_made[id(top)]] + 2, lo, hi)]
    root3 = octn.rooms[0][3]
    listed = repointed = 0
    new_prm = None
    if root3 is not None:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
        octn.rooms[0][3].check()
        listed = len(items)
        move = {x: y for x, y in zip(octx.record_refs(), octn.record_refs()) if x != y}
        if move:
            pm = bytearray(B['.prm'])
            t, n = struct.unpack_from('<II', pm, 0)
            old = set(octx.record_refs())
            for i in range(1, n):
                o, size = struct.unpack_from('<II', pm, t + 16 * i)
                if size == 64 and pm[o:o + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', pm, o + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', pm, o + 0x1c, move[v]); repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            new_prm = bytes(pm)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[anm_name] = new_anm
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(nm, new[nm]) for nm in B.order])
    for x in os.listdir(B.folder):
        pth = os.path.join(B.folder, x)
        if os.path.isfile(pth) and pth != zp and not x.startswith(('audit.', 'rappel.')):
            shutil.copyfile(pth, os.path.join(dst, x))
    kj = os.path.join(dst, 'KLJoin.ini')
    if not os.path.isfile(kj):
        raise ValueError('the build has no KLJoin.ini to carry the [Rappel] section')
    txt = open(kj, 'rb').read().decode('latin1')
    if '[Rappel]' in txt:
        raise ValueError('KLJoin.ini has a [Rappel] section already')
    with open(kj, 'wb') as fh:
        fh.write((txt.rstrip('\r\n') + '\n' + rappel_ini(frames, start, land, prof)).encode('latin1'))
    after = F.sizes(dst)
    say('written %s: %d entities added (%s), REF ids %d..%d; members changed: %s; %d slot ids renumbered; %d groups listed in the root\'s group tree; %d model roots of the .prm re-pointed; AIMonitor list 2 + %s' % (
        out, len(order), ', '.join('%s %d' % kv for kv in collections.Counter(J.schema('dd').geoms.get(n.tid) for n in order).items()), ref0, nxt - 1,
        ' '.join(changed), moved, listed, repointed, TIMER))
    say('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    if before['.prm'] != after['.prm'] or before['.fxc'] != after['.fxc'] or before['.WAV'] != after['.WAV']:
        raise ValueError('a large block other than the .ANM changed its size: %s -> %s' % (dict(before), dict(after)))
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        st = json.load(open(sj))
        st['rappel'] = changed
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst, os.path.basename(zp)[:-len('_Main.zip')])
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    for rj in ('dyn.json', 'fed.json'):
        pth = os.path.join(dst, rj)
        if os.path.isfile(pth):
            d = json.load(open(pth), object_pairs_hook=collections.OrderedDict)
            big = d.get('big_before')
            if isinstance(big, dict) and big.get('.ANM') == arep['bytes'][0]:
                d['big_before_rappel'] = collections.OrderedDict(big)
                big['.ANM'] = arep['bytes'][1]
                with open(pth, 'w') as fh:
                    json.dump(d, fh, indent=1)
                say('  %s: its record of the large blocks continued (.ANM %d -> %d)' % (rj, arep['bytes'][0], arep['bytes'][1]))
    for x in os.listdir(B.folder):
        if x.lower() == 'kltalk.ini':
            if open(os.path.join(dst, x), 'rb').read() != open(os.path.join(B.folder, x), 'rb').read():
                raise ValueError('KLTalk.ini differs from the source build')
            say('  %s is byte-equal to the source build\'s' % x)
    report = collections.OrderedDict(source=B.folder, out=dst, land=list(land), face=list(face), delay=delay, start=list(start), net=list(net), world_net=list(wnet),
                                     frames=frames, profile=prof, anm=arep, members_changed=changed, entities_added=len(order), ref_ids='%d..%d' % (ref0, nxt - 1))
    say('')
    res = check(dst, say)
    report['check'] = [list(r) for r in res]
    with open(os.path.join(dst, 'rappel.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(dst, 'rappel.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return report


def check_cut(folder, log=print):
    """The cut of a `build`: the nodes, the timer, the PosObject, the KLJoin.ini section, the floor under the landing, the talk file."""
    import configparser
    import kl_fa
    import kl_fa_bots as F
    import kl_fa_climb2 as C2
    import kl_map_escape as E
    out = []

    def say(s, t):
        out.append((s, t))
        log('  %-4s %s' % (s, t))
    B = F.Built(folder)
    sc = B.sc
    rt = sc.resolve(F.R_ + GROUP + '\\' + SQUAD + '\\' + ROUT)
    po = sc.resolve(F.R_ + GROUP + '\\' + SQUAD + '\\' + ROUT + '\\' + POS)
    tm = sc.resolve(F.R_ + GROUP + '\\' + TIMER)
    if len(rt) != 1 or len(po) != 1 or len(tm) != 1:
        say('FAIL', 'the cut\'s nodes are missing (rout %d, pos %d, timer %d)' % (len(rt), len(po), len(tm)))
        return out
    rt, po, tm = rt[0], po[0], tm[0]
    ctl = {sc.p.key(nm): [kl_fa.value(sc, u) for u in kl_fa.units(body[1:-1])] for nm, body in sc.nodes[rt]['ctrls']}
    script = ctl['MiniCutsceneRout'][0]
    say('PASS' if script == C2.script_for(SLOT, POS) else 'FAIL', 'the rout\'s script is the one-act Lynch form of kl_fa_climb2.script_for: %s' % script[:150])
    rpath = F.R_ + GROUP + '\\' + SQUAD + '\\' + ROUT
    tv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if k == tm][0]
    say('PASS' if [str(x).lower() for x in tv[4]] == [rpath.lower()] else 'FAIL', 'the timer (%.1f s) names the rout: %r' % (tv[0], tv[4]))
    mon = [v for k, _i, v in kl_fa.controllers(sc, 'AIMonitor') if sc.names[k] == 'Gameplay!AIMonitor']
    named = bool(mon) and any(str(x).lower() == (F.R_ + GROUP + '\\' + TIMER).lower() for x in mon[0][2])
    say('PASS' if named else 'FAIL', 'Gameplay!AIMonitor list 2 (the round-start event) names the timer')
    start = B.at(po)
    cp = configparser.RawConfigParser(strict=False)
    cp.read_string(open(os.path.join(folder, 'KLJoin.ini'), 'rb').read().decode('latin1'))
    sec = dict(cp.items('Rappel')) if cp.has_section('Rappel') else {}
    if not sec:
        say('FAIL', 'KLJoin.ini has no [Rappel] section')
        return out
    st = [float(x) for x in sec['start'].split()]
    ld = [float(x) for x in sec['land'].split()]
    pr = [int(x) for x in sec['profile'].split()]
    say('PASS' if max(abs(st[i] - start[i]) for i in range(3)) < 0.05 else 'FAIL', 'the PosObject stands at the ini\'s Start: (%.1f, %.1f, %.1f) / (%.1f, %.1f, %.1f)' % (tuple(start) + tuple(st)))
    say('PASS' if pr[0] == 0 and pr[-1] == 1000 and all(b >= a for a, b in zip(pr, pr[1:])) and len(pr) == (int(sec['frames']) - 1 + STEP - 1) // STEP + 1 else 'FAIL',
        'Profile: %d values, 0 .. 1000, never back, one per %d frames of the %s-frame clip' % (len(pr), STEP, sec['frames']))
    an, _sn = _anm_snd(B.order)
    a = kl_anm.Anm(B.files[an])
    fr = clips_of(a)[CLIP].frames
    say('PASS' if fr == int(sec['frames']) else 'FAIL', 'the .ANM\'s %s has %d frames = Frames=%s' % (CLIP, fr, sec['frames']))
    drop = ld[1] - st[1]
    say('PASS' if abs(drop + 1756.0) < 1.0 else 'FAIL', 'Land is %.0f under Start (the clip\'s root drop is 1756)' % -drop)
    L = E.Level(B.zp)
    G = E.Ground(L)

    def floor_at(x):
        u = G.under(x, ld[1] + 5.0, ld[2])
        return u[0] if u else None
    f0 = floor_at(ld[0])
    say('PASS' if f0 is not None and abs(f0 - ld[1]) < 3.0 else 'FAIL', 'a floor under Land: %s (Land y %.0f)' % ('none' if f0 is None else '%.0f' % f0, ld[1]))
    out_ = [x for x in (20, 40, 60) if floor_at(ld[0] + x) is None or abs(floor_at(ld[0] + x) - ld[1]) > 3.0]
    say('PASS' if not out_ else 'NOTE', 'floor outside Land (20, 40, 60 units further out): %s' % ('all there' if not out_ else 'ends at %d units' % out_[0]))
    hit = [h for h in G.hits(st[0], st[2]) if st[1] - 1760.0 < h[0] < st[1] + 20.0]
    say('NOTE', 'floors or ceilings of the map on the descent\'s vertical line at the start (y %.0f .. %.0f): %s (collision is off during the cut; only the picture can say)' % (
        st[1] - 1760.0, st[1] + 20.0, ', '.join('%.0f' % h[0] for h in hit[:8]) or 'none'))
    ref = None
    here = os.path.abspath(folder)
    while True:
        c = os.path.join(here, 'build', RT_TALK.replace('/', os.sep))
        if os.path.isfile(c):
            ref = c
            break
        up = os.path.dirname(here)
        if up == here:
            break
        here = up
    mine = os.path.join(folder, 'KLTalk.ini')
    if ref and os.path.isfile(mine):
        say('PASS' if open(ref, 'rb').read() == open(mine, 'rb').read() else 'FAIL', 'KLTalk.ini byte-equal to rt_full6\'s (the approved countdown timing)')
    else:
        say('NOTE', 'KLTalk.ini not compared (no rt_full6 copy found above %s)' % folder)
    return out


def main():
    a = sys.argv[1:]
    if a == ['facts']:
        facts()
    elif a == ['joins']:
        joins(kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dd'), 'dd'))
    elif len(a) in (5, 6) and a[0] == 'plan':
        plan(kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dd'), 'dd'), a[1], tuple(float(x) for x in a[2:5]), float(a[5]) if len(a) == 6 else 0.0)
    elif len(a) >= 3 and a[0] == 'build':
        land, delay, i = LAND, DELAY, 3
        while i < len(a):
            if a[i] == '--land' and i + 3 < len(a):
                land = tuple(float(x) for x in a[i + 1:i + 4]); i += 4
            elif a[i] == '--delay' and i + 1 < len(a):
                delay = float(a[i + 1]); i += 2
            else:
                sys.exit(__doc__)
        had = os.path.isdir(a[2]) and bool(os.listdir(a[2]))
        try:
            rep = build(a[1], a[2], land=land, delay=delay)
        except (ValueError, KeyError) as e:
            left = not had and os.path.isdir(a[2]) and bool(os.listdir(a[2]))
            sys.exit('kl_fa_rappel: NOT built: %s%s' % (e.args[0] if e.args else e, ' - %s HOLDS WHAT WAS WRITTEN BEFORE THAT: not a build, do not use it' % a[2] if left else ' - nothing was written'))
        sys.exit(1 if any(s == 'FAIL' for s, _t in rep['check']) else 0)
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
