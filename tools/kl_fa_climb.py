#!/usr/bin/env python3
"""
The wall CLIMB Dead Men had and Dog Days dropped: the LEVEL's half of giving it back. A step on a FINISHED build
folder (<slot>_Main.zip + the files beside it), in the style of kl_fix_lean.py. The account, every exe address, the
ranked plan and the live checks: re/climb.md. The other half is klhook/klclimb.c (not wired).
OFFLINE: nothing here installs anything or starts a game. NOTHING OF IT HAS RUN IN THE GAME.

    python kl_fa_climb.py rule                      Dead Men's table and edge rule as this file holds them
    python kl_fa_climb.py edges <folder>            the rule walked along the map's climb lines on the build's own
                                                    collision: which stretches pass, the [Climb] sections they give
    python kl_fa_climb.py check <folder>            read-only: the climb slots and clips of the build's .ANM set by
                                                    set, the [Climb] sections of its KLJoin.ini against the collision,
                                                    what stayed of the bots' way; last line RESULT (kl_fa_climb): ...
    python kl_fa_climb.py apply <folder> <out folder> [--players-only] [--no-edges]
                                                    the build with the two additions below; exit 1 on a FAIL

WHAT IS KNOWN (re/climb.md; read in the two exes and measured on the 41 stock files, nothing seen live)
  - Dead Men's player climbs by ZFFPlayerMovementClimb (kaneandlynch.exe vtable 0x966c44): no level data, rays find
    an edge 25 < h <= 220 over the feet; table (0x603340) Low <= 120 stand-off 81, Medium <= 170 / 47, High <= 220 /
    47; the clip's own root motion carries him, aligned so that the feet are at the foot of the face at clip event 5
    and at top level at event 6. Its NPCs climb on navigation links of kind 1 (ZFFSpecialLink@Locomotion).
  - kl2.exe has the NPC half still (mover 0x4a5160, the three slot names read at 0x579920) and no player half. No
    Dog Days .ANM has the slots '/Movement/Climb/Up/Low | Medium | High' or a clip for them.
  - The clips are the same format, move only bones every stock skeleton numbers alike (table entries 0..60), and
    can be put into a Dog Days file slot by slot with kl_anmjoin's own machinery (the code path of every graft).

WHAT apply ADDS - both are additions, nothing of the build is taken away or moved (the wall piece kl_escape sank
stays sunk: today's way through the wall and the AI heisters' drop link are untouched)
  1. .ANM: the three slot lists, with their clips, in the sets of the level's player bodies (from Dead Men's
     'PlayerCharacter') and, unless --players-only, in every NPC character set (from Dead Men's 'Police': the *_NPC
     clips). Nothing in the game asks for them by itself: the player's are for klclimb.c, the NPC ones for a later
     kind-1 link (and so that no NPC set ever meets such a link without a clip). Proved on the result: the file
     reads back to the same bytes, kl_anm.audit is clean, the base is a prefix (clips, names, data, bone / pose /
     slot tables, every slot list of every set), each added list plays its source's clips (compared by name, events
     + data, bone NAMES, condition flags), no bone or pose name was added; only the .ANM member of the archive
     differs.
  2. KLJoin.ini (the side file kljoin.c reads beside the archive; kl_fa_bots' [CrewHop] stays): [Climb] sections,
     one per stretch of an edge where Dead Men's own rule holds on the build's collision. The hook part reads them;
     without it (or with [Climb] Enable=0 in KLHook.ini) they do nothing.
         [Climb]                   ; [Climb.2] .. [Climb.8]
         A=-3450 403.5 -625        ; the two ends of the edge: the top of the obstacle, on the face that is climbed
         B=-1950 403.5 -625
         Normal=0 -1               ; x z, unit, level: out of that face, towards the side one stands on
         Floor=200                 ; the floor at its foot
         Depth=50                  ; how thick the obstacle is behind the edge
     The lines to walk are LINES below, per Dead Men map: a seed only - every number that is written is measured
     on the collision by the rule (edges prints the measurement).

GUESSES are marked where they are made (the margins and tolerances of the walk; the stretch itself is measured).
What the rule here does NOT model: the player's own state, the game's ray flags (every triangle of the map's
static and key-framed collision counts), cars. It is the offline stand-in for rays the hook does not cast.
"""
import collections, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_anm, kl_anmjoin

SIDE = 'KLJoin.ini'             # kljoin.c reads it beside the archive; klhop.c ([CrewHop]) and klclimb.c ([Climb]) share it
SOURCE = 'M03_FA_A'             # the Dead Men level whose .ANM the clips are taken from. All 20 Dead Men files hold the
                                # same 17 climb clips (frames, events, size, net root movement equal: re/climb.md B.4)
PLAYER_SOURCE, NPC_SOURCE = 'PlayerCharacter', 'Police'
FALL = '/Movement/Fall/Fall_1m'                 # an NPC character set = a set whose default clip for this slot is an *_NPC clip
# Dead Men's table, kaneandlynch.exe 0x603340: (slot name, greatest height over the feet, stand-off from the face).
# The stand-off is where the clip wants the feet when it starts (the code puts the player there at clip event 5).
CLASSES = [('/Movement/Climb/Up/Low', 120.0, 81.0), ('/Movement/Climb/Up/Medium', 170.0, 47.0), ('/Movement/Climb/Up/High', 220.0, 47.0)]
SLOTS = [c[0] for c in CLASSES]
H_MIN = 25.0                    # 0x93f720: a top not more than this over the feet is no climb
HEADROOM = 180.0                # a hit within this over the top refuses the climb
HD = 25.0                       # half the player's box depth ([player+0x5b0] * 0.5): the first probe is this far in front
PROBE_DOWN = 310.0              # the four probes start this far over the feet and go straight down
EV_FOOT, EV_TOP = 5, 6          # the clip events of the two alignments

# The lines to walk, per Dead Men map: 'sign' = scene paths that must all be in the build (which map it holds),
# then (name, (x, z) from, (x, z) to, (nx, nz) out of the face, floor seed).
# M03_FA_A: the yard's north wall, pieces SO0101_M03_Wall_Low_8m_02 and _01 (x -3500 .. -1900) from the yard side -
# the two pieces between the one kl_escape sank (x -1900 .. -1100) and the level's own 'not here', where the
# campaign's AI climbs (lanes x -3210 and x -2938, re/climb.md 2.2) and the dumpsters stand on the street side.
# Measured with the rule below (re/climb.md 4.2): 63 of 65 samples of this stretch pass; piece _03 (x -4300 ..
# -3500) fails it from x -3600 west (a hero-only collision object, ColiObj_OnlyHero_01, stands over the wall, then
# the wall SO0202_M03_Wall_ENTER_05_01); from the street side nothing passes (253.5 high). The seed is therefore
# what the rule itself allows; the GUESS left is only that 50 off both ends of a stretch is margin enough.
M03_OUT = 'Locations/M03_FA_A/M03FAA_Locations.zip\\Locations/M03_FA_A/M03FAA_LOC_Outside.zip\\M03_FAA_Outside_01A\\'
LINES = {
    'M03_FA_A': {'sign': [M03_OUT + 'SO0101_M03_Wall_Low_8m_02', M03_OUT + 'SO0101_M03_Wall_Low_8m_01'],
                 'lines': [('the yard\'s north wall, from the yard', (-3500.0, -625.0), (-1900.0, -625.0), (0.0, -1.0), 200.0)]},
}
STEP = 25.0                     # sampling along a line
REFS = (30.0, 47.0, 65.0)       # where the player's reference point is tried, from the face (the hook takes 15 .. 75)
MARGIN = 50.0                   # a passing stretch is shortened by this at both ends
MIN_RUN = 150.0                 # ... and kept when this much is left
BODY = (30.0, 170.0)            # something this far over the floor at the foot = no room to stand (as kl_escape.Walk's 55 .. 165)
MAX_SECTIONS = 8                # klclimb.c reads [Climb] .. [Climb.8]


def _archive(folder):
    if folder.lower().endswith('.zip'):
        return folder
    hit = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(hit) != 1:
        raise ValueError('%s: %d level archives' % (folder, len(hit)))
    return os.path.join(folder, hit[0])


def read_anm(zp):
    with zipfile.ZipFile(zp) as z:
        n = [m for m in z.namelist() if m.lower().endswith('.anm')]
        if len(n) != 1:
            raise ValueError('%s: %d .ANM members' % (zp, len(n)))
        return n[0], z.read(n[0])


# ------------------------------------------------------------------ the root track of a clip
def _bits(buf, at, n):
    return int.from_bytes(buf[at >> 3:(at >> 3) + 8], 'little') >> (at & 7) & ((1 << n) - 1)


def root_keys(a, i, own=None):
    """[(frame, (x, y, z))] = the position keys of clip i's ROOT track, or None when its first track is not the
    GROUND bone. y is up, forward is -z. Layout read in kaneandlynch.exe 0x5bfa60 / 0x5bdbd0 (re/climb.md B.4):
    clip data +0x24 = track 0 = {4 offsets, bone}; the root is bone 0x39 by NUMBER in both exes (kl2 0x5a5060);
    offsets [2] / [3] = an 'IdxT' key-frame table (the four letters, then a bit stream from bit 32: 2 bits, 4 bits
    = width W, 16 bits = count N, N frame numbers of W bits) and N raw float triples. Checked against the record:
    last key - first key equals the record's vector +0x18 on every climb clip (check() prints both)."""
    own = own or kl_anm.owners(a)
    blk, oev = own[struct.unpack_from('<i', a.clips[i], 0xc)[0]]
    o, d = blk[0] + 8 * oev, a.data
    _r0, _r1, p0, p1, bone = struct.unpack_from('<5i', d, o + 0x24)
    if bone != 0x39 or d[o + p0:o + p0 + 4] != b'IdxT':
        return None
    w, n = _bits(d, 8 * (o + p0) + 34, 4), _bits(d, 8 * (o + p0) + 38, 16)
    frames = [_bits(d, 8 * (o + p0) + 54 + w * k, w) for k in range(n)]
    return [(f, struct.unpack_from('<3f', d, o + p1 + 12 * k)) for k, f in enumerate(frames)]


def root_at(keys, f):
    """The root's place at frame f: linear between keys (the engine's 0x41f860)."""
    for (f0, p), (f1, q) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            t = (f - f0) / (f1 - f0) if f1 > f0 else 0.0
            return tuple(x + (y - x) * t for x, y in zip(p, q))
    return keys[-1][1] if f >= keys[-1][0] else keys[0][1]


def clip_facts(a, i, own=None):
    """What the hook and the reports need of a clip: frames, events {id: frame}, record flags and +0x28, the root's
    movement at the two events and at the end (relative to its first key), None when it has no root track."""
    r = a.clips[i]
    _h, frames, fps, ev = struct.unpack_from('<4h', r, 0)
    flags, off = struct.unpack_from('<Ii', r, 8)
    own = own or kl_anm.owners(a)
    blk, oev = own[off]
    events = {}
    for k in range(oev):
        e, f, _x = struct.unpack_from('<IHH', a.data, blk[0] + 8 * k)
        events.setdefault(e, f)
    keys = root_keys(a, i, own)
    out = {'clip': i, 'name': a.names[i], 'frames': frames, 'fps': fps, 'events': events, 'flags': flags,
           'class28': struct.unpack_from('<i', r, 0x28)[0], 'net': struct.unpack_from('<3f', r, 0x18), 'root': None}
    if keys:
        rel = lambda f: tuple(y - x for x, y in zip(keys[0][1], root_at(keys, f)))
        out['root'] = {'foot': rel(events[EV_FOOT]) if EV_FOOT in events else None, 'top': rel(events[EV_TOP]) if EV_TOP in events else None,
                       'end': rel(keys[-1][0])}
    return out


def clip_bones(a, i, own=None):
    """The bone table entries clip i's tracks move."""
    blk, oev = (own or kl_anm.owners(a))[struct.unpack_from('<i', a.clips[i], 0xc)[0]]
    return [struct.unpack_from('<i', a.data, p)[0] for p in kl_anm.tracks(a.data, blk[0], oev)[0]]


def after_top(facts):
    """(forward, up) the root still moves after the clip's event 6 (0, 0 without the event or the track)."""
    r = facts.get('root')
    if not r or not r['top']:
        return 0.0, 0.0
    return -(r['end'][2] - r['top'][2]), r['end'][1] - r['top'][1]


# ------------------------------------------------------------------ the .ANM
def sets_of(sc):
    """{animation set: Counter{class of the node that names it}} for the people of a built level (ZFFPlayer bodies
    and ZFFActor characters; a string 'anmcol:animationdatabase#X' in any of their fields or controllers)."""
    import kl_prpjoin as J
    who = collections.defaultdict(collections.Counter)
    for k in range(1, len(sc.nodes)):
        cls = sc.cls(k)
        if cls not in ('ZFFPlayer', 'ZFFActor'):
            continue
        for _holder, _lab, u in J.fields(sc, k):
            for s in J.strings(sc, u):
                if s.startswith(kl_anm.PREFIX) and s != kl_anm.PREFIX:
                    who[s.split('#', 1)[1]][cls] += 1
    return who


def npc_sets(a):
    """The NPC character sets of a file: those whose default clip for /Movement/Fall/Fall_1m is an *_NPC clip
    (the people who can walk a navigation link). Dog and the weapon / vehicle sets are not."""
    if FALL not in a.slots:
        return []
    f, out = a.slots.index(FALL), []
    for c in a.cols:
        lst = c.lists().get(f)
        if lst and a.names[lst[-1][1]].endswith('_NPC'):
            out.append(c.short)
    return out


def has_slots(a, short):
    """The climb slots a set has, as {slot name: [(flags, clip index)]}."""
    c = a.col(short)
    ls = c.lists()
    return {s: ls[a.slots.index(s)] for s in SLOTS if s in a.slots and a.slots.index(s) in ls}


def merge(raw, players, npcs, log=print):
    """A Dog Days .ANM + Dead Men's three climb slot lists in the sets `players` (from PLAYER_SOURCE) and `npcs`
    (from NPC_SOURCE). Sets that have all three already are left alone. -> (bytes, report). Raises on any failed
    proof. The machinery is kl_anmjoin's (_Out, _Source, _add_lists - the code of every graft's join; its names
    are private, used here as track F's trial used them: one public `add_slots` there would be the tidy form)."""
    base = kl_anm.Anm(raw)
    if base.game != 'dd':
        raise ValueError('the base is not a Dog Days .ANM')
    dm = kl_anm.convert(kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dm')))
    missing = [s for s in SLOTS if s not in dm.slots]
    if missing:
        raise ValueError('Dead Men\'s %s has no slot %s' % (SOURCE, missing))
    have = {c.short for c in base.cols}
    plan = collections.OrderedDict()
    for x, src in [(p, PLAYER_SOURCE) for p in players] + [(n, NPC_SOURCE) for n in npcs]:
        if x not in have:
            raise KeyError('the .ANM has no set %s' % x)
        got = has_slots(base, x)
        if len(got) == len(SLOTS):
            continue
        if got:
            raise ValueError('%s has %d of the %d climb slots: not a file this step made' % (x, len(got), len(SLOTS)))
        plan.setdefault(x, src)
    rep = collections.OrderedDict(source=SOURCE, sets=dict(plan), bytes=[len(raw), len(raw)])
    if not plan:
        return raw, rep
    out = kl_anmjoin._Out(base)
    src = kl_anmjoin._Source(out, dm, True, 'M')
    a = out.a
    cols = {c.short: c for c in a.cols}
    taken = []
    for x, sname in plan.items():
        got = kl_anmjoin._add_lists(out, cols[x], src, src.lists(dm.col(sname), set(SLOTS)))
        if sorted(got) != sorted(SLOTS):
            raise ValueError('%s: Dead Men\'s %s gave %s' % (x, sname, got))
        taken += [(x, n, sname) for n in got]
    a.data = bytes(out.data)
    kl_anm.relist(a)
    res = a.save()

    # ---- the proofs
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
        if extra != (sorted(SLOTS) if c.short in plan else []):
            bad.append('%s gained %s' % (c.short, extra))
    own_r, own_s, cache = kl_anm.owners(re_), kl_anm.owners(dm), {}
    for x, slot, sname in taken:
        want = [(f, kl_anmjoin.signature(dm, i, own_s)) for f, i in dm.col(sname).lists()[dm.slots.index(slot)]]
        got = [(f, kl_anmjoin.signature(re_, i, own_r, cache)) for f, i in rc[x].lists()[re_.slots.index(slot)]]
        if got != want:
            bad.append('%s %s: not the clips of Dead Men\'s %s' % (x, slot, sname))
    if len(re_.bones) != len(base.bones) or len(re_.poses) != len(base.poses):
        bad.append('bone / pose names were added: %s %s' % (re_.bones[len(base.bones):], re_.poses[len(base.poses):]))
    order = sorted(range(len(re_.slots)), key=lambda i: re_.slots[i].encode('latin1'))     # kl2 0x68a730 is a binary search
    if [re_.slots[i] for i in order] != sorted(re_.slots, key=lambda s: s.encode('latin1')) or len(set(re_.slots)) != len(re_.slots):
        bad.append('the slot name index is not sorted / not unique')
    if bad:
        raise ValueError('the merged .ANM fails its proofs: ' + '; '.join(bad))
    st = out.st
    rep.update(bytes=[len(raw), len(res)], clips=[len(base.clips), len(re_.clips)], slot_names=[len(base.slots), len(re_.slots)],
               bones=[len(base.bones), len(re_.bones)], poses=[len(base.poses), len(re_.poses)], lists=len(taken),
               data_blocks_added=st['data blocks added'], data_bytes_added=st['data bytes added'],
               new_clips=[re_.names[i] for i in range(n, len(re_.clips))], strange_events=dict(out.strange),
               slot_ids={s: re_.slots.index(s) for s in SLOTS})
    log('  .ANM %d -> %d bytes (+%d): %d clips added in %d data blocks, slot names %d -> %d, bones %d (+%d), poses %d (+%d); %d lists in %d sets' % (
        len(raw), len(res), len(res) - len(raw), len(re_.clips) - n, st['data blocks added'], len(base.slots), len(re_.slots),
        len(re_.bones), len(re_.bones) - len(base.bones), len(re_.poses), len(re_.poses) - len(base.poses), len(taken), len(plan)))
    log('  proofs: reads back to the same bytes; kl_anm.audit clean; the base is a prefix and no base list changed; %d added lists = their '
        'Dead Men source (name, events + data, bone names, flags); no bone or pose name added' % len(taken))
    return res, rep


# ------------------------------------------------------------------ Dead Men's rule on a build's collision
def rule(G, ref, feet, W):
    """Dead Men's test for a climb (kaneandlynch.exe 0x605b50, the local player's part; re/climb.md B.1) for a
    player whose reference point is at ref = (x, z) with his feet at height `feet`, looking along the level unit
    vector W = (x, z). G = kl_map_escape.Ground. -> {'ok': False, 'why': ...} or {'ok': True, 'h', 'top' (x, y, z),
    'face' (x, y, z: where the ray under the edge met the face), 'slot', 'stand', 'probe'}.
    What is NOT modelled: the player's own state (speed, the USE tap, the hand action), the ray flags 0x20 / 0x28
    (every triangle of the map's static and key-framed collision counts here), cars and the second refused class."""
    tops = []
    for i in range(4):
        d = HD + 15.0 * i
        x, z = ref[0] + W[0] * d, ref[1] + W[1] * d
        ys = [h[0] for h in G.hits(x, z) if feet + 0.5 < h[0] <= feet + PROBE_DOWN]      # a ray straight down: its first hit is the highest
        if ys:
            tops.append((d, (x, max(ys), z)))
    last, why = None, 'no top within %g in front' % (HD + 45.0)
    for d, (x, y, z) in tops:
        if last is not None and y < last:               # 'a top lower than the one tried before is skipped'
            continue
        last, h = y, y - feet
        a0 = (ref[0] - W[0] * 15.0, y + 15.0, ref[1] - W[1] * 15.0)
        if G.between(a0, (a0[0] + W[0] * (d + 30.0), a0[1], a0[2] + W[1] * (d + 30.0))):
            why = 'the way over the edge is not clear (15 over the top)'
            continue
        if any(y + 1.0 < hh[0] < y + 1.0 + HEADROOM for hh in G.hits(x, z)):
            return {'ok': False, 'why': 'less than %g headroom over the top' % HEADROOM}
        c0 = (ref[0] - W[0] * 10.0, y - 1.0, ref[1] - W[1] * 10.0)
        hit = G.between(c0, (c0[0] + W[0] * (d + 20.0), c0[1], c0[2] + W[1] * (d + 20.0)))
        if not hit:
            why = 'no face 1 under the edge'
            continue
        if h <= H_MIN:
            why = 'the top is %g over the feet: not over %g' % (h, H_MIN)
            continue
        cls = next((c for c in CLASSES if c[1] >= h), None)
        if cls is None:
            return {'ok': False, 'why': 'the top is %g over the feet: over %g' % (h, CLASSES[-1][1])}
        t = hit[0][0]
        return {'ok': True, 'h': h, 'top': (x, y, z), 'face': (c0[0] + W[0] * t, y, c0[2] + W[1] * t), 'slot': cls[0], 'stand': cls[2], 'probe': d}
    return {'ok': False, 'why': why}


def sample(L, G, e, n, floor_seed):
    """One point e = (x, z) of a face line with outward normal n: the rule from every REFS distance, the floor and
    the room at the foot, movable bodies, the obstacle's depth and what lies beyond. -> dict (ok / why / numbers)."""
    W = (-n[0], -n[1])
    got, floor = [], None
    for r in REFS:
        ref = (e[0] + n[0] * r, e[1] + n[1] * r)
        col = G.hits(ref[0], ref[1])
        fl = [h[0] for h in col if h[1] > 0.7 and abs(h[0] - floor_seed) <= 60.0]
        if not fl:
            return {'ok': False, 'why': 'no floor %g from the face' % r}
        f = max(fl)
        if any(f + BODY[0] < h[0] < f + BODY[1] for h in col):
            return {'ok': False, 'why': 'something stands %g from the face' % r}
        res = rule(G, ref, f, W)
        if not res['ok']:
            return {'ok': False, 'why': '%s (from %g)' % (res['why'], r)}
        floor = f if floor is None else floor
        if abs(f - floor) > 5.0:
            return {'ok': False, 'why': 'the floor at the foot is not level (%g, %g)' % (floor, f)}
        got.append(res)
    top, face = got[0]['top'][1], got[0]['face']
    if any(abs(g['top'][1] - top) > 2.0 or g['slot'] != got[0]['slot'] or math.hypot(g['face'][0] - face[0], g['face'][2] - face[2]) > 3.0 for g in got):
        return {'ok': False, 'why': 'the three stand-offs do not see the same edge'}
    for typ, ref_, lo, hi in G.boxes:                    # rigid props, vehicles, key-framed pieces: what may stand in the way
        x0, x1 = e[0] + n[0] * 90.0, e[0] - n[0] * 60.0
        z0, z1 = e[1] + n[1] * 90.0, e[1] - n[1] * 60.0
        if lo[0] <= max(x0, x1) + 30.0 and hi[0] >= min(x0, x1) - 30.0 and lo[2] <= max(z0, z1) + 30.0 and hi[2] >= min(z0, z1) - 30.0 \
                and lo[1] <= top + HEADROOM and hi[1] >= floor + 5.0:
            return {'ok': False, 'why': 'a movable body stands there: %s' % L.name(ref_)}
    on_top = lambda t: any(abs(h[0] - top) <= 2.0 and h[1] > 0.7 for h in G.hits(face[0] + W[0] * t, face[2] + W[1] * t))
    depth = 0.0
    for t in range(5, 405, 5):                           # the top surface behind the edge: every 5, then the last 5 by 0.5
        if not on_top(t):
            break
        depth = float(t)
    while depth < 400.0 and on_top(depth + 0.5):
        depth += 0.5
    bx, bz = face[0] + W[0] * (depth + 30.0), face[2] + W[1] * (depth + 30.0)
    below = [h[0] for h in G.hits(bx, bz) if h[1] > 0.7 and h[0] < top - 5.0]
    return {'ok': True, 'x': e[0], 'z': e[1], 'floor': floor, 'top': top, 'h': top - floor, 'slot': got[0]['slot'], 'stand': got[0]['stand'],
            'face': (face[0], face[2]), 'depth': depth, 'beyond': max(below) if below else None}


def find_level(sc):
    """The Dead Men map of LINES a built scene holds (None: none of them)."""
    for level, d in LINES.items():
        if all(len(sc.resolve('ROOT\\' + p)) == 1 for p in d['sign']):
            return level
    return None


def walk(L, G, level, log=print):
    """The rule along every line of LINES[level] -> [section dict] (at most MAX_SECTIONS), each a stretch where
    every sample passes with one class, one top, one floor."""
    out = []
    for name, a, b, n, seed in LINES[level]['lines']:
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
        rows = []
        for k in range(int(ln // STEP) + 1):
            e = (a[0] + u[0] * STEP * k, a[1] + u[1] * STEP * k)
            s = sample(L, G, e, n, seed)
            s['t'] = STEP * k
            s.setdefault('x', e[0]); s.setdefault('z', e[1])
            rows.append(s)
        runs, cur = [], []
        same = lambda p, q: p['slot'] == q['slot'] and abs(p['top'] - q['top']) <= 2.0 and abs(p['floor'] - q['floor']) <= 5.0 and \
            math.hypot(p['face'][0] - p['x'] - (q['face'][0] - q['x']), p['face'][1] - p['z'] - (q['face'][1] - q['z'])) <= 3.0
        for s in rows:
            if s['ok'] and (not cur or same(cur[-1], s)):
                cur.append(s)
            else:
                if cur:
                    runs.append(cur)
                cur = [s] if s['ok'] else []
        if cur:
            runs.append(cur)
        log('  line \'%s\': (%g, %g) -> (%g, %g), %d samples every %g, %d pass' % (name, a[0], a[1], b[0], b[1], len(rows), STEP, sum(s['ok'] for s in rows)))
        why = collections.OrderedDict()
        for s in rows:
            if not s['ok']:
                why.setdefault(s['why'], []).append(s['t'])
        for w, ts in why.items():
            log('    refused at %s: %s' % (', '.join('(%g, %g)' % (a[0] + u[0] * t, a[1] + u[1] * t) for t in ts[:6]) + (' ...' if len(ts) > 6 else ''), w))
        for r in runs:
            t0, t1 = r[0]['t'] + MARGIN, r[-1]['t'] - MARGIN
            if t1 - t0 < MIN_RUN:
                log('    a passing stretch of %g is too short to offer (least %g after %g off both ends)' % (r[-1]['t'] - r[0]['t'], MIN_RUN, MARGIN))
                continue
            off = (sum(s['face'][0] - s['x'] for s in r) / len(r), sum(s['face'][1] - s['z'] for s in r) / len(r))    # the measured face against the seed line
            top = sum(s['top'] for s in r) / len(r)
            sec = {'line': name, 'a': (a[0] + u[0] * t0 + off[0], top, a[1] + u[1] * t0 + off[1]),
                   'b': (a[0] + u[0] * t1 + off[0], top, a[1] + u[1] * t1 + off[1]), 'normal': n,
                   'floor': sum(s['floor'] for s in r) / len(r), 'depth': min(s['depth'] for s in r),
                   'slot': r[0]['slot'], 'stand': r[0]['stand'], 'h': top - sum(s['floor'] for s in r) / len(r),
                   'beyond': sorted({round(s['beyond']) if s['beyond'] is not None else None for s in r}, key=lambda v: (v is None, v))}
            out.append(sec)
    if len(out) > MAX_SECTIONS:
        log('  %d stretches, the hook reads %d: the longest are kept' % (len(out), MAX_SECTIONS))
        out = sorted(sorted(out, key=lambda s: -math.dist(s['a'], s['b']))[:MAX_SECTIONS], key=lambda s: (s['line'], s['a']))
    return out


# ------------------------------------------------------------------ the side file
def _g(v):
    return ' '.join('%g' % round(x, 1) for x in v)


def climb_text(secs, level=''):
    """The [Climb] sections of a level's KLJoin.ini as klhook\\klclimb.c reads them."""
    out = ['; [Climb]: written by tools\\kl_fa_climb.py%s. Read by KLHook (klclimb.c, NOT WIRED yet) from the KLJoin.ini beside the level' % (' for ' + level if level else ''),
           '; archive; acts only with [Climb] Enable=1 in KLHook.ini, in an Arcade round, on a level that is not stock. Each section is the top',
           '; edge of an obstacle where Dead Men\'s own climb rule holds on this build\'s collision (25 < top - floor <= 220, a face under the',
           '; edge, a clear way over it, 180 headroom): the local player who stands at its foot is carried up by Dead Men\'s climb clip. re\\climb.md']
    for i, s in enumerate(secs):
        out += ['[Climb%s]' % ('.%d' % (i + 1) if i else ''), 'A=' + _g(s['a']), 'B=' + _g(s['b']), 'Normal=%g %g' % tuple(s['normal']),
                'Floor=%g' % round(s['floor'], 1), 'Depth=%g' % round(s['depth'], 1)]
    return '\r\n'.join(out) + '\r\n'


def climb_strip(text):
    """An ini text without its [Climb...] sections and without climb_text's own comment lines."""
    out, skip = [], False
    marks = ('[Climb]: written by', 'archive; acts only with [Climb]', 'edge of an obstacle where Dead Men', 'edge, a clear way over it, 180 headroom')
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('['):
            skip = s.lower().startswith('[climb')
        if skip or (s.startswith(';') and any(m in s for m in marks)):
            continue
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return out


def climb_read(folder):
    """The [Climb], [Climb.2] .. sections of <folder>/KLJoin.ini as klclimb.c reads them -> [dict] ('bad' = why the
    hook would refuse it); [] without a file or a section."""
    p = os.path.join(folder, SIDE)
    if not os.path.isfile(p):
        return []
    sec, cur = collections.OrderedDict(), None
    for line in open(p, 'rb').read().decode('latin1').splitlines():
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            cur = sec.setdefault(s[1:-1].strip().lower(), collections.OrderedDict())
        elif cur is not None and '=' in s and not s.startswith(';'):
            k, v = s.split('=', 1)
            cur.setdefault(k.strip().lower(), v.strip())

    def nums(t, n):
        try:
            v = [float(x) for x in (t or '').replace(',', ' ').replace(';', ' ').replace('(', ' ').replace(')', ' ').split()[:n]]
            return v if len(v) == n else None
        except ValueError:
            return None
    out = []
    for i in range(MAX_SECTIONS):
        d = sec.get('climb' if i == 0 else 'climb.%d' % (i + 1))
        if d is None:
            continue
        s = {'section': 'Climb' if i == 0 else 'Climb.%d' % (i + 1), 'a': nums(d.get('a'), 3), 'b': nums(d.get('b'), 3),
             'normal': nums(d.get('normal'), 2), 'floor': nums(d.get('floor'), 1), 'depth': nums(d.get('depth', '50'), 1), 'bad': None}
        if not s['a'] or not s['b'] or not s['normal'] or not s['floor']:
            s['bad'] = 'A=, B= (three numbers each), Normal= (two) and Floor= are needed'
        else:
            s['floor'], s['depth'] = s['floor'][0], (s['depth'] or [50.0])[0]
            ln = math.hypot(*s['normal'])
            if abs(ln - 1.0) > 0.01:
                s['bad'] = 'Normal= is not a unit vector'
            elif abs(s['a'][1] - s['b'][1]) > 1.0:
                s['bad'] = 'A and B are not at one height'
            elif math.hypot(s['b'][0] - s['a'][0], s['b'][2] - s['a'][2]) < 60.0:
                s['bad'] = 'the edge is shorter than 60'
            else:
                u = ((s['b'][0] - s['a'][0]), (s['b'][2] - s['a'][2]))
                if abs(u[0] * s['normal'][0] + u[1] * s['normal'][1]) > 0.02 * math.hypot(*u):
                    s['bad'] = 'Normal= is not square to A - B'
                else:
                    h = s['a'][1] - s['floor']
                    cls = next((c for c in CLASSES if c[1] >= h), None)
                    if h <= H_MIN or cls is None:
                        s['bad'] = 'the top is %g over Floor=: outside %g .. %g' % (h, H_MIN, CLASSES[-1][1])
                    else:
                        s['h'], s['slot'], s['stand'] = h, cls[0], cls[2]
        out.append(s)
    return out


def climb_write(dst, secs, level='', log=print):
    """<dst>/KLJoin.ini gets the [Climb] sections (those a copied file had are replaced; everything else of the file
    stays, kl_fa_bots' [CrewHop] above all). -> the text written, or None when there is nothing to write."""
    p = os.path.join(dst, SIDE)
    old = climb_strip(open(p, 'rb').read().decode('latin1')) if os.path.isfile(p) else []
    if not secs:
        if os.path.isfile(p) and old:
            with open(p, 'wb') as f:
                f.write(('\r\n'.join(old) + '\r\n').encode('latin1'))
        return None
    text = ('\r\n'.join(old) + '\r\n\r\n' if old else '') + climb_text(secs, level)
    with open(p, 'wb') as f:
        f.write(text.encode('latin1'))
    log('  %s: %d [Climb] section(s) written (%s)' % (p, len(secs), 'beside the sections it had' if old else 'the file is new'))
    return text


# ------------------------------------------------------------------ check
def check(folder, log=print):
    """Read-only. -> [(severity, text)]; FAIL = the build must not be handed on as a climb build."""
    import kl_map_escape as E
    out = []

    def say(sev, text):
        out.append((sev, text))
        log('%-5s %s' % (sev, text))
    zp = _archive(folder)
    name, raw = read_anm(zp)
    a = kl_anm.Anm(raw)
    bad = kl_anm.audit(a)
    say('FAIL' if a.save() != raw or bad else 'PASS', '%s: %d bytes, %d clips, %d slot names, %d sets; round trip %s, kl_anm.audit %s' % (
        name, len(raw), len(a.clips), len(a.slots), len(a.cols), 'identical' if a.save() == raw else 'DIFFERS', 'clean' if not bad else bad[:3]))
    L = E.Level(zp)
    who = sets_of(L.sc)
    players = sorted(x for x, c in who.items() if c['ZFFPlayer'])
    actors = sorted(x for x, c in who.items() if c['ZFFActor'])
    log('      the level\'s people: ZFFPlayer bodies use %s; ZFFActor characters use %s' % (
        ', '.join('%s x%d' % (x, who[x]['ZFFPlayer']) for x in players) or 'no set', ', '.join('%s x%d' % (x, who[x]['ZFFActor']) for x in actors) or 'no set'))
    missing = [s for s in SLOTS if s not in a.slots]
    if missing:
        say('FAIL', 'the .ANM has no slot name %s: no climb clip can be asked for (run apply)' % ', '.join(missing))
    own = kl_anm.owners(a)
    facts = {}
    known = {c.short for c in a.cols}
    for x in players + [n for n in actors if n not in players]:
        if x not in known:
            say('FAIL', 'set %s is named by the level and is not in the .ANM' % x)
            continue
        got = has_slots(a, x) if not missing else {}
        is_player = x in players
        if len(got) != len(SLOTS):
            say('FAIL' if is_player else 'NOTE', 'set %s (%s) has %d of the %d climb slots%s' % (
                x, 'players' if is_player else 'NPC', len(got), len(SLOTS), '' if is_player else ': an NPC of it could play nothing at a kind-1 navigation link (there is none in a build of today)'))
            continue
        rows = []
        for s in SLOTS:
            for fl, ci in got[s]:
                f = facts.setdefault(ci, clip_facts(a, ci, own))
                why = []
                if not f['flags'] & 0x40:
                    why.append('record flag 0x40 (root motion) is not set: kl2 0x760120 would not find its channel, the alignment 0x80fdc0 would do nothing')
                if f['class28'] & 0x10:
                    why.append('record +0x28 has bit 0x10: not a full-body clip')
                if f['root'] is None:
                    why.append('its first track is not the GROUND bone: it carries nobody')
                elif max(abs(p - q) for p, q in zip(f['root']['end'], f['net'])) > 0.5:
                    why.append('root keys (%s) and record +0x18 (%s) disagree' % (_g(f['root']['end']), _g(f['net'])))
                if f['fps'] != 25:
                    why.append('%d frames a second, not 25' % f['fps'])
                for w in why:
                    say('FAIL', 'set %s %s: clip %s: %s' % (x, s, f['name'], w))
                if fl == 0:
                    rows.append((s, f))
        if is_player:
            for s, f in rows:
                fwd, up = after_top(f)
                cls = next(c for c in CLASSES if c[0] == s)
                ev = f['events']
                say('PASS' if EV_TOP in ev else 'NOTE', 'players\' set %s %-26s default %-22s %2d frames (%.2f s), events %s; root at event 6 (%s), end (%s): after event 6 %.1f forward, %.1f up = '
                    'he ends %.1f past the face, %.1f over the top%s' % (
                        x, s.rsplit('/', 1)[1], f['name'].split('#')[1], f['frames'], f['frames'] / 25.0,
                        ' '.join('%d@%d' % kv for kv in sorted(ev.items())) or 'none', _g(f['root']['top']) if f['root'] and f['root']['top'] else '-',
                        _g(f['root']['end']) if f['root'] else '-', fwd, up, fwd - cls[2], up, '' if EV_TOP in ev else ' - NO event 6: the hook aligns at the last frame'))
        else:
            say('PASS', 'NPC set %s has the three slots: default clips %s' % (x, ', '.join(f['name'].split('#')[1] for _s, f in rows)))
    if facts:
        # A clip names its bones by the number they have in THIS file's bone table (kl_anmjoin renumbers by name), and
        # every body of the build is bound to that table. So the question is only whether a climb clip moves a bone
        # that nothing else in the file moves (a name the join would have had to add: apply proves none was).
        mine = {b for ci in facts for b in clip_bones(a, ci, own)}
        climb = {i for i, n in enumerate(a.names) if 'Climb#' in n}
        others, seen = set(), set()
        for i in range(len(a.clips)):
            off = struct.unpack_from('<i', a.clips[i], 0xc)[0]
            if i in climb or off in seen:
                continue
            seen.add(off)
            others.update(clip_bones(a, i, own))
        alone = sorted(mine - others)
        say('PASS' if not alone else 'NOTE', 'the %d climb clips move %d bones, highest table entry %d (%s): %s' % (
            len(facts), len(mine), max(mine), a.bones[max(mine)],
            'every one is a bone other clips of this file move too - they are bound like every other clip, nothing to rebind' if not alone else
            'NO other clip of the file moves %s' % ', '.join('%d %s' % (b, a.bones[b]) for b in alone)))

    # the side file against the collision
    secs = climb_read(os.path.dirname(zp))
    level = find_level(L.sc)
    if not secs:
        say('NOTE', 'no [Climb] section in %s: klclimb.c has no place on this level%s' % (SIDE, '' if level else ' (and LINES has no line for the map this build holds)'))
    else:
        G = E.Ground(L)
        fmt = {c[0]: c for c in CLASSES}
        for s in secs:
            if s['bad']:
                say('FAIL', '[%s]: %s - the hook refuses the section' % (s['section'], s['bad']))
                continue
            ln = math.hypot(s['b'][0] - s['a'][0], s['b'][2] - s['a'][2])
            u = ((s['b'][0] - s['a'][0]) / ln, (s['b'][2] - s['a'][2]) / ln)
            n, fails, rows = tuple(s['normal']), collections.OrderedDict(), []
            for k in range(int(ln // STEP) + 1):
                e = (s['a'][0] + u[0] * STEP * k, s['a'][2] + u[1] * STEP * k)
                r = sample(L, G, e, n, s['floor'])
                if r['ok'] and (abs(r['top'] - s['a'][1]) > 2.0 or abs(r['floor'] - s['floor']) > 5.0 or r['slot'] != s['slot']):
                    r = {'ok': False, 'why': 'the collision has top %g, floor %g (%s); the section says %g, %g' % (r['top'], r['floor'], r['slot'].rsplit('/', 1)[1], s['a'][1], s['floor'])}
                if r['ok'] and math.hypot(r['face'][0] - e[0], r['face'][1] - e[1]) > 3.0:
                    r = {'ok': False, 'why': 'the face is %.1f from the line A - B' % math.hypot(r['face'][0] - e[0], r['face'][1] - e[1])}
                if r['ok']:
                    rows.append(r)
                else:
                    fails.setdefault(r['why'], []).append(e)
            for w, es in fails.items():
                say('FAIL', '[%s]: Dead Men\'s rule does not hold at %s: %s' % (s['section'], ', '.join('(%g, %g)' % e for e in es[:4]) + (' ...' if len(es) > 4 else ''), w))
            if not fails:
                f = next((facts[ci] for x in players for sl, lst in (has_slots(a, x).items() if not missing and x in known else []) if sl == s['slot'] for fl, ci in lst if fl == 0 and ci in facts), None)
                fwd, up = after_top(f) if f else (0.0, 0.0)
                over = fwd - s['stand']
                depth = min(r['depth'] for r in rows)
                beyond = sorted({round(r['beyond']) for r in rows if r['beyond'] is not None})
                say('PASS', '[%s]: (%s) - (%s), %d long, out of the face (%g, %g): Dead Men\'s rule holds at all %d samples; floor %g, top %g = %.1f over = %s, '
                    'stand-off %g; obstacle %g thick; %s; beyond it the floor is at %s' % (
                        s['section'], _g(s['a']), _g(s['b']), ln, n[0], n[1], len(rows), s['floor'], s['a'][1], s['h'], s['slot'].rsplit('/', 1)[1], fmt[s['slot']][2], depth,
                        ('the player ends %.1f past the face, %.1f over the top: ON the obstacle, %.1f short of its far edge' % (over, up, depth - over)) if f and over < depth else
                        ('the player ends %.1f past the face: beyond the obstacle, he drops' % over) if f else 'no player clip to say where he ends',
                        ' / '.join('%g (%g down)' % (b, s['a'][1] - b) for b in beyond) or 'not found'))
                if abs(s['depth'] - depth) > 5.0:
                    say('NOTE', '[%s]: Depth=%g, the collision says %g' % (s['section'], s['depth'], depth))

    # what must have stayed
    side = os.path.join(os.path.dirname(zp), SIDE)
    txt = open(side, 'rb').read().decode('latin1') if os.path.isfile(side) else ''
    low = [l.strip().lower() for l in txt.splitlines()]
    say('NOTE', '%s: %s' % (SIDE, ', '.join('%d [%s] section(s)' % (sum(l.startswith('[' + k) for l in low), t) for k, t in (('join', 'Join'), ('crewjoin', 'CrewJoin'), ('crewhop', 'CrewHop'), ('climb', 'Climb'))) if txt else 'none'))
    import kl_escape
    for lv, walls in kl_escape.OPEN.items():
        for path, dy in walls:
            k = L.sc.resolve('ROOT\\' + path)
            if len(k) == 1:
                y = L.place(k[0])[1]
                say('PASS' if abs(y - dy) < 1.0 else 'NOTE', '%s stands at y %g: %s' % (path.rsplit('\\', 1)[1], y, 'the piece kl_escape sank is still sunk - today\'s way through the wall is there'
                                                                                 if abs(y - dy) < 1.0 else 'NOT where kl_escape puts it (%g)' % dy))
    n_fail, n_note = sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out)
    log('RESULT (kl_fa_climb): %s (%d FAIL, %d NOTE)' % ('PASS' if not n_fail else 'FAIL', n_fail, n_note))
    return out


# ------------------------------------------------------------------ apply
def apply(src, dst, players_only=False, edges=True, log=print):
    """The build of folder `src` written to the NEW folder `dst` with the climb clips in its .ANM and the [Climb]
    sections in its KLJoin.ini. -> report dict. Raises before anything is written when a proof fails."""
    import kl_graft, kl_maps
    import kl_map_escape as E
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
    say('kl_fa_climb: %s -> %s' % (zp, dst))
    with zipfile.ZipFile(zp) as z:
        order = z.namelist()
        files = {n: z.read(n) for n in order}
    anm = [n for n in order if n.lower().endswith('.anm')]
    if len(anm) != 1:
        raise ValueError('%d .ANM members' % len(anm))
    L = E.Level(zp)
    who = sets_of(L.sc)
    base = kl_anm.Anm(files[anm[0]])
    players = sorted(x for x, c in who.items() if c['ZFFPlayer'])
    if not players:
        raise ValueError('no ZFFPlayer body of the level names an animation set')
    npcs = [] if players_only else [n for n in npc_sets(base) if n not in players]
    say('  players\' sets (ZFFPlayer bodies): %s <- Dead Men %s\'s %s; NPC sets: %s <- %s' % (
        ', '.join(players), SOURCE, PLAYER_SOURCE, ', '.join(npcs) or 'none (--players-only)', NPC_SOURCE))
    new, rep = merge(files[anm[0]], players, npcs, say)
    secs, level = [], find_level(L.sc)
    if edges and level:
        say('  the map is %s: Dead Men\'s rule along its climb lines, on the build\'s collision' % level)
        secs = walk(L, E.Ground(L), level, say)
        for s in secs:
            say('    section: (%s) - (%s), floor %g, top %.1f over = %s, obstacle %g thick, beyond it the floor at %s' % (
                _g(s['a']), _g(s['b']), s['floor'], s['h'], s['slot'].rsplit('/', 1)[1], s['depth'], ' / '.join(str(b) for b in s['beyond'])))
        if not secs:
            say('  NO stretch of a line passes: no [Climb] section is written')
    elif edges:
        say('  LINES has no line for the map this build holds: no [Climb] section is written (the clips are added all the same)')
    changed = new != files[anm[0]]
    if not changed and not secs:
        raise ValueError('nothing to add: the sets have the slots and no section would be written')
    files[anm[0]] = new
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp and not x.startswith('climb.'):
            shutil.copyfile(q, os.path.join(dst, x))
    with zipfile.ZipFile(zp) as za, zipfile.ZipFile(out) as zb:
        ia, ib = za.infolist(), zb.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        diff = [i.filename.rsplit('_Main', 1)[-1] for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if diff != (['.ANM'] if changed else []):
        raise ValueError('more than the .ANM member differs from the build: %s' % diff)
    before = open(os.path.join(dst, SIDE), 'rb').read().decode('latin1') if os.path.isfile(os.path.join(dst, SIDE)) else ''
    climb_write(dst, secs, level or '', say)
    after = open(os.path.join(dst, SIDE), 'rb').read().decode('latin1') if os.path.isfile(os.path.join(dst, SIDE)) else ''
    if climb_strip(after) != climb_strip(before):
        raise ValueError('%s lost something it had' % SIDE)
    slot = os.path.basename(zp)[:-len('_Main.zip')]
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        st = json.load(open(sj))
        st['climb'], st['final'] = diff, kl_maps.member_ids(dst, slot)
        st['same'] = [e for e in st.get('same', []) if e not in diff]
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    say('  only the %s member differs from the build (%d members); %d files beside the archive copied; steps.json continued (\'climb\')' % (
        ' / '.join(diff) or 'no', len(order), len(os.listdir(dst)) - 1))
    # kl_fa_bots_dyn.check (and kl_fa_fed's) FAIL a build whose four large blocks are not the ones their step
    # recorded ('big_before' of dyn.json / fed.json): the .ANM is one of the four and this step grows it on purpose.
    # The record in the COPIED report is continued, the numbers it had are kept beside it - said here and in climb.txt.
    if changed:
        for rj in ('dyn.json', 'fed.json'):
            p = os.path.join(dst, rj)
            if not os.path.isfile(p):
                continue
            d = json.load(open(p), object_pairs_hook=collections.OrderedDict)
            big = d.get('big_before')
            if isinstance(big, dict) and big.get('.ANM') == rep['bytes'][0]:
                d['big_before_climb'] = collections.OrderedDict(big)
                big['.ANM'] = rep['bytes'][1]
                d['climb_note'] = 'kl_fa_climb.py grew the .ANM %d -> %d (Dead Men\'s climb clips); big_before was continued, the numbers before are big_before_climb' % tuple(rep['bytes'])
                with open(p, 'w') as fh:
                    json.dump(d, fh, indent=1)
                say('  %s: its record of the large blocks continued (.ANM %d -> %d; the numbers before kept as big_before_climb) - without that '
                    'the check of the step that wrote it calls this step\'s own change a fault' % (rj, rep['bytes'][0], rep['bytes'][1]))
    report = collections.OrderedDict(source=zp, out=out, level=level, anm=rep, members_changed=diff,
                                     sections=[dict(s, a=list(s['a']), b=list(s['b']), normal=list(s['normal'])) for s in secs])
    with open(os.path.join(dst, 'climb.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    say('')
    res = check(dst, say)
    report['check'] = [list(r) for r in res]
    with open(os.path.join(dst, 'climb.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(dst, 'climb.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return report


def show_rule(log=print):
    log('Dead Men\'s climb (kaneandlynch.exe ZFFPlayerMovementClimb, vtable 0x966c44; table 0x603340, test 0x605b50):')
    for s, h, d in CLASSES:
        log('  %-28s top up to %3g over the feet, clip starts %2g from the face' % (s, h, d))
    log('  a top must be more than %g over the feet; found by four rays straight down from %g over the feet, %s in front of the reference point;' % (
        H_MIN, PROBE_DOWN, ' / '.join('%g' % (HD + 15 * i) for i in range(4))))
    log('  the way 15 over the top must be clear, %g over the top must be free, a face must lie 1 under the edge. No level data is asked for.' % HEADROOM)
    log('  the clip is aligned so that the feet are at the foot of the face at clip event %d and at top level at event %d; then its own root motion goes on.' % (EV_FOOT, EV_TOP))
    log('this file walks the rule along LINES (%s) from %s units off the face, every %g; a stretch is offered when %g is left after %g off both ends.' % (
        ', '.join(LINES), ' / '.join('%g' % r for r in REFS), STEP, MIN_RUN, MARGIN))


def main():
    a = sys.argv[1:]
    if a == ['rule']:
        show_rule()
    elif len(a) == 2 and a[0] == 'edges':
        import kl_map_escape as E
        L = E.Level(_archive(a[1]))
        level = find_level(L.sc)
        if not level:
            sys.exit('LINES has no line for the map this build holds')
        print('%s holds %s' % (a[1], level))
        secs = walk(L, E.Ground(L), level)
        print(climb_text(secs, level) if secs else 'no stretch passes')
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if any(s == 'FAIL' for s, _t in check(a[1])) else 0)
    elif len(a) >= 3 and a[0] == 'apply':
        opt = set(a[3:])
        if opt - {'--players-only', '--no-edges'}:
            sys.exit('unknown option %s' % sorted(opt - {'--players-only', '--no-edges'}))
        rep = apply(a[1], a[2], players_only='--players-only' in opt, edges='--no-edges' not in opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in rep['check']) else 0)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
