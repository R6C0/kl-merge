#!/usr/bin/env python3
"""kl_dm_reverb.py - room-adaptive reverb for a grafted Dead Men map (2026-11-08). OFFLINE: starts nothing, installs nothing.

    python tools/kl_dm_reverb.py plan  <F0x_Main.zip> [--src M02_FA_A]          what would be authored, nothing written
    python tools/kl_dm_reverb.py stage <F0x_Main.zip> <out folder> [--src M02_FA_A] [--bots <zip>] [--no-inside] [--no-outside]
                                       the zip (and the .bots.zip sibling with --bots) with a 'KL_Reverb!' group of Audio_ReverbActivater boxes
    python tools/kl_dm_reverb.py stage-map <Maps folder> <DMnn> <out folder>    the live plain zip + bots zip + base.md5 of one map, installer + pins.json
    python tools/kl_dm_reverb.py check <zip> [<base zip>]                       read a staged zip back: every box, every controller, nothing else changed

WHY. Dog Days' stock Fragile Alliance maps change the reverb with the room: a F0x_Audio group holds 'Audio!BOX!..' ZBoxPrimitives, each with a CheckInside
controller (the volume; subject = the local player) and an Audio_ReverbActivater controller (field 0 = the SND offset of a roomeffect object, fields 1/2 =
'CheckInsideEnter' / 'CheckInsideLeave', field 3 = a float 30..100). The player entering the box makes ZAudio_ReverbActivater (ClassInfo 0xd07164, vtable 0xbaa9fc)
set the one global OpenAL EFX reverb (ZSynthOpenAL::SetReverb 0x5fff30). A grafted Dead Men map has NO such box: the conversion drops Dead Men's own mechanism
(ZROOM field 13 = a roomeffect, EAX5) and the map plays dry. re/gun_echo_1107.md (option 2) and re/dm_reverb_1108.md say why this is the cheap, data-only fix.

WHAT IT DOES (data only; no .prm / .HVK / .SND / sound byte changes):
  1. rooms: every ZROOM of the map zip that has a Dead Men roomeffect (the source level's .SND, kl_snd.bank('M02_FA_A'); name rule: the roomeffect of room R is
     'audio:roomeffects/<src>/<group>/<R lower>#roomeffect', checked by plan()) and at least one .rmi box (flag 1 = an axis-aligned box: centre +0x28, half +0x40).
  2. DM EAX5 values -> one of the SEVEN Dog Days roomeffects the map's own .SND already holds (they are Dog Days' own, I3DL2 floats, SND offset = the ref).
     No new SND object is authored (that would grow the .SND, which every other tool treats as fixed): the nearest existing effect of the same kind (inside / outside) wins.
  3. one new top-level ZGROUP 'KL_Reverb!' (the build's own plain group form, as kl_fa_cover) with one ZBoxPrimitive per room box (size = the .rmi box, no model, flags of a
     stock Dog Days reverb box). Each carries CheckInside + Audio_ReverbActivater cloned from F01's 'Audio!BOX!010_Inside_DL10_Platform' with the fields set.
  4. the slot ids of .oct / .rmi / .rmc are renumbered (new entities move later slots; kl_fa_cover.apply's method), the group is listed in the root's group tree when
     the form group is. The four large blocks keep their size. Checked by reading everything back.

TOGGLE. "Every feature a toggle (recommended on/off)": this is level DATA, so the switch is INSTALL / UNDO of the staged pair (install.py / install.py --undo), and per
run --no-inside / --no-outside (an outside-only or inside-only set). A runtime [Reverb] key would need a klhook change; not made here (data only task).

RE-RUN ON THE LIVE ZIP. Peers rewrite map zips (pd2 rebase, DM05A music, glass ...). This tool reads whatever zip is given, so the stage is made from the zip that is live NOW:
`stage-map` pins the live md5s into pins.json and install.py refuses when a live file changed since; then run stage-map again. It refuses a zip that already has a
'KL_Reverb!' group (idempotent, never twice).

GUESSES (each also marked GUESS where used):
  * the reverb a box selects is the NEAREST existing Dog Days effect by a weighted distance (decay, decay HF ratio, room, reverb, reflections); not tuned by ear.
  * field 3 of Audio_ReverbActivater (stock 30..100, varies per effect) is copied from the stock F07 box that uses the same effect, else 60.0 (its meaning is not proven).
  * boxes that overlap fire in an unproven order at a simultaneous enter; stock maps overlap too.
  * no 'default outside' box covers the whole map (stock maps do): leaving every box keeps the last effect. The Dead Men outside is room Out_Parkinglot, which gets its boxes.
  * the new ZBoxPrimitive is in no room tree (stock Audio!BOX entities are not either: the audio group is listed in the root's group tree only).
"""
import collections
import hashlib
import json
import math
import os
import re
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F
import kl_fa_cover as C
import kl_cover_add as CA
import kl_fa
import kl_gms
import kl_octree as O
import kl_prpjoin as J
import kl_scene
import kl_snd
import kl_loot_1025 as LO

GROUP = 'KL_Reverb!'
TAG = '.before-1108dmreverb'
DONOR = ('F01', 'ROOT\\Locations/F01/F01_Audio.zip\\Audio!BOX!010_Inside_DL10_Platform')   # flags 0x200000, no model, CheckInside + Audio_ReverbActivater
WET_LEVEL = 'F07'            # the stock level whose boxes give field 3 per effect (its roomeffects are the ones the live Dead Men maps carry)
WET_DEFAULT = 60.0           # GUESS: median of the stock values (30..100)
SKIP_ROOMS = ('alwaysvisible', 'debugroom')
EFFECT_TABLE = 7             # kl_snd table of roomeffect objects


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ roomeffect values
def dm_params(b, o):
    """Dead Men roomeffect object (0x70 bytes) -> dict. Layout read from the 28 objects of M02_FA_A (every value in its EAX5 range, test checks):
    +0x18 environment, +0x1c size m, +0x20 diffusion 0..1, +0x24 room mB, +0x28 roomHF mB, +0x2c roomLF mB, +0x30 decay s, +0x34 decayHFratio, +0x38 decayLFratio,
    +0x3c reflections mB, +0x40 reflections delay s, +0x44 reverb mB, +0x48 reverb delay s. GUESS: the order of the last two pairs (EAX5 order without pans)."""
    i = lambda k: struct.unpack_from('<i', b, o + k)[0]
    f = lambda k: struct.unpack_from('<f', b, o + k)[0]
    return dict(env=i(0x18), size=f(0x1c), diffusion=f(0x20), room=i(0x24), roomHF=i(0x28), roomLF=i(0x2c), decay=f(0x30), decayHF=f(0x34),
                decayLF=f(0x38), refl=i(0x3c), reflDelay=f(0x40), reverb=i(0x44), reverbDelay=f(0x48))


def dd_params(b, o):
    """Dog Days roomeffect object (0x50 bytes): +0x1c diffusion %, +0x20 density %, +0x24 room mB, +0x28 roomHF mB, +0x2c decay s, +0x30 decayHFratio,
    +0x34 reflections mB, +0x38 reflections delay s, +0x3c reverb mB, +0x40 reverb delay s, +0x44 HF reference Hz (re/audio.md, I3DL2)."""
    f = lambda k: struct.unpack_from('<f', b, o + k)[0]
    return dict(diffusion=f(0x1c), density=f(0x20), room=f(0x24), roomHF=f(0x28), decay=f(0x2c), decayHF=f(0x30), refl=f(0x34), reflDelay=f(0x38),
                reverb=f(0x3c), reverbDelay=f(0x40), hfref=f(0x44))


def distance(dm, dd):
    """How far a Dog Days effect is from a Dead Men one. GUESS: weights chosen so that a doubling of the decay time (1.04) costs about as much as 3500 mB of level;
    nothing here was tuned by ear. Levels are the late field (room + reverb) and the early reflections."""
    d = 1.5 * abs(math.log(max(dm['decay'], 0.05) / max(dd['decay'], 0.05)))
    d += 1.0 * abs(dm['decayHF'] - dd['decayHF'])
    d += 0.3 * abs((dm['room'] + dm['reverb']) - (dd['room'] + dd['reverb'])) / 1000.0
    d += 0.2 * abs(dm['refl'] - dd['refl']) / 1000.0
    return d


def ideal_dd(dm):
    """What an authored Dog Days effect for this Dead Men room would hold (NOT written: the .SND stays as it is; kept in reverb.json for a later step that adds objects).
    GUESS: EAX5 diffusion 0..1 -> I3DL2 percent; density has no EAX5 twin -> 100 (GUESS); levels, times and ratios map one to one."""
    return dict(diffusion=round(dm['diffusion'] * 100.0, 1), density=100.0, room=dm['room'], roomHF=dm['roomHF'], decay=round(dm['decay'], 3), decayHF=round(dm['decayHF'], 3),
                refl=dm['refl'], reflDelay=round(dm['reflDelay'], 4), reverb=dm['reverb'], reverbDelay=round(dm['reverbDelay'], 4), hfref=5000.0)


def kind_of(name):
    """'inside' / 'outside' of a roomeffect (or room) name: stock names carry '/inside/' or '/outside/'; Dead Men rooms are M02_FA_A_Ins_* / _Out_*. None = unknown."""
    n = name.lower()
    if '/inside/' in n or '_ins_' in n:
        return 'inside'
    if '/outside/' in n or '_out_' in n:
        return 'outside'
    return None


def choose(dm, room_name, effects):
    """-> (effect, distance) from effects [{'off', 'name', 'p'}]: the nearest of the room's own kind (all when the kind or the kind's set is empty)."""
    k = kind_of(room_name)
    pool = [e for e in effects if kind_of(e['name']) == k] or list(effects)
    best = min(pool, key=lambda e: (distance(dm, e['p']), e['off']))
    return best, distance(dm, best['p'])


def zip_effects(zp):
    """The roomeffects of a map zip's own .SND -> [{'off', 'name', 'p'}] in table order (the SND offset is the ref a controller stores)."""
    with zipfile.ZipFile(zp) as z:
        n = next(m for m in z.namelist() if m.endswith('_Main.SND'))
        snd = kl_snd.Snd('dd', z.read(n)).walk()
    out = []
    for o in snd.tables.get(EFFECT_TABLE, []):
        nm = snd.name(o)
        nm = nm.decode('latin1') if isinstance(nm, bytes) else nm
        out.append({'off': o, 'name': nm, 'p': dd_params(snd.b, o)})
    return out


def dm_effects(src):
    """{room name lower: dm params} of the Dead Men source level's roomeffects ('...<room lower>#roomeffect')."""
    snd = kl_snd.bank(src)
    out = {}
    for o in snd.tables.get(EFFECT_TABLE, []):
        nm = snd.name(o)
        nm = nm.decode('latin1') if isinstance(nm, bytes) else nm
        out[nm.lower().rsplit('/', 1)[-1].split('#')[0]] = dm_params(snd.b, o)
    return out


_WET = {}


def wet_table():
    """{ref: float} from the stock boxes of WET_LEVEL (the most common float per ref). The refs of the live Dead Men maps are F07's SND offsets."""
    if not _WET:
        sc, _e = F.Maker.level(WET_LEVEL)
        cnt = collections.defaultdict(collections.Counter)
        for k, _i, v in kl_fa.controllers(sc, 'Audio_ReverbActivater'):
            cnt[v[0]][v[3]] += 1
        for ref, c in cnt.items():
            _WET[ref] = c.most_common(1)[0][0]
    return _WET


# ------------------------------------------------------------------ the plan
def source_level(B):
    """'M02_FA_A' from the audio group the graft kept ('ROOT\\Locations/M02_FA_A/M02FAA_Audio.zip')."""
    for p in B.sc.path:
        m = re.match(r'ROOT\\Locations/(M\d\d_FA_\w+)/', p)
        if m:
            return m.group(1)
    raise ValueError('no Dead Men source level named in the scene paths (pass --src)')


def room_boxes(B):
    """{room node k: [(centre, half)]} of the flag-1 .rmi boxes of every ZROOM node."""
    sc = B.sc
    rmi = O.RoomIndex.parse(B['.rmi'])
    by = {s + 2: e for e, s in B.scene.slots().items()}
    knode = {id(e): i + 1 for i, e in enumerate(B.ents)}
    out = collections.defaultdict(list)
    for bx in rmi.boxes:
        e = by.get(bx.room)
        if e is None:
            continue
        k = knode[id(e)]
        if sc.cls(k) != 'ZROOM':
            continue
        if struct.unpack_from('<I', bx.raw, 0)[0] != 1:
            continue                                     # GUESS: flag 1 = axis-aligned box (all 45 of DM02 are)
        c = struct.unpack_from('<3f', bx.raw, 0x28)
        h = struct.unpack_from('<3f', bx.raw, 0x40)
        out[k].append((c, h))
    return out


def plan(zp, src=None, opt=None, log=print):
    """-> (B, P). P = {'src', 'boxes': [{name, room, center, half, ref, ref_name, wet, dist}], 'skipped': [(room, why)], 'effects', 'options'}."""
    opt = dict({'inside': True, 'outside': True}, **(opt or {}))
    CA.use_slot(zp)
    B = F.Built(zp)
    sc = B.sc
    if any(sc.names[t] == GROUP for t in sc.tops()):
        raise ValueError('%s already has a %s group' % (zp, GROUP))
    src = src or source_level(B)
    eff = zip_effects(zp)
    if not eff:
        raise ValueError('the zip\'s .SND holds no roomeffect objects')
    dm = dm_effects(src)
    rb = room_boxes(B)
    wet = wet_table()
    rooms = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZROOM']
    boxes, skipped, n = [], [], 0
    order = sorted(rooms, key=lambda k: (kind_of(sc.names[k]) != 'outside', sc.names[k]))      # outside rooms first
    for k in order:
        nm = sc.names[k]
        kind = kind_of(nm)
        if nm.lower() in SKIP_ROOMS or any(s in nm.lower() for s in SKIP_ROOMS):
            skipped.append((nm, 'not a place (always visible / debug)')); continue
        if nm.lower() not in dm:
            skipped.append((nm, 'no Dead Men roomeffect named %s' % nm.lower())); continue
        if k not in rb:
            skipped.append((nm, 'no .rmi box')); continue
        if (kind == 'inside' and not opt['inside']) or (kind == 'outside' and not opt['outside']):
            skipped.append((nm, 'switched off (%s)' % kind)); continue
        e, dist = choose(dm[nm.lower()], nm, eff)
        for j, (c, h) in enumerate(rb[k]):
            if min(h) < 1.0:
                skipped.append((nm, 'box %d has no volume' % j)); continue
            n += 1
            boxes.append(collections.OrderedDict(
                name='Audio!BOX!KR%03d_%s' % (n, nm), room=nm, kind=kind, center=[float(x) for x in c], half=[float(x) for x in h], ref=e['off'],
                ideal=ideal_dd(dm[nm.lower()]), ref_name=e['name'].split('/')[-1].split('#')[0], wet=float(wet.get(e['off'], WET_DEFAULT)), dist=round(dist, 3)))
    P = collections.OrderedDict(src=src, boxes=boxes, skipped=skipped, effects=[(e['off'], e['name']) for e in eff], options=opt)
    use = collections.Counter(b['ref_name'] for b in boxes)
    log('%s: %d rooms, %d boxes planned for %d of the map\'s %d roomeffects (source %s); skipped %d: %s'
        % (zp, len({b['room'] for b in boxes}), len(boxes), len(use), len(eff), src, len(skipped), '; '.join('%s (%s)' % s for s in skipped)))
    for ref, c in use.most_common():
        log('  %3d boxes -> %s' % (c, ref))
    return B, P


# ------------------------------------------------------------------ writing
def apply(B, P, dst, log=print):
    """The plan's boxes written into a copy of the zip in folder dst (the zip's own file name) -> report dict. The method is kl_fa_cover.apply's, with the Audio boxes."""
    sc = B.sc
    if not P['boxes']:
        raise ValueError('no box to add')
    before = F.sizes(B.folder)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    prm = B['.prm']

    M = F.Maker()
    gk = C.group_form(B)
    grp = C._node(M, B, gk, GROUP)
    M.place(grp, (0.0, 0.0, 0.0))
    for b in P['boxes']:
        n = M.clone(DONOR[0], DONOR[1], b['name'])
        M.place(n, b['center'])
        M.set(n, None, {'ZBoxPrimitive[0]': b['half'][0], 'ZBoxPrimitive[1]': b['half'][1], 'ZBoxPrimitive[2]': b['half'][2]})
        M.set(n, 'CheckInside', {1: 'ROOT\\' + GROUP + '\\' + b['name']})
        M.set(n, 'Audio_ReverbActivater', {0: int(b['ref']), 3: float(b['wet'])})
        if n.model != 0 or n.links is not None or n.flags != 0x200000:
            raise ValueError('%s: not the form that was planned (flags %#x model %d)' % (b['name'], n.flags, n.model))
        grp.add(n)
    q, order = M.scene([grp])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'reverb')
    data = Jn.p.serialize()
    back = F.Prp(data)
    if back.serialize() != data or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, made = nxt, {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        made[id(n)] = e
        for k in n.kids:
            ent(k, e)
    ent(grp, None)
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
    moved = sum(1 for a, b in ids.items() if a != b)
    root3 = octn.rooms[0][3]
    listed = repointed = 0
    new_prm = None
    form_listed = root3 is not None and slot0[B.ents[gk - 1]] + 2 in {it[0] for it in octx.rooms[0][3].items}
    if form_listed:
        pts = [(b['center'][a] - b['half'][a], b['center'][a] + b['half'][a]) for b in P['boxes'] for a in range(3)]
        lo = tuple(min(p[0] for p in pts[a::3]) - 10.0 for a in range(3))
        hi = tuple(max(p[1] for p in pts[a::3]) + 10.0 for a in range(3))
        octn.rooms[0][3] = O.join_trees(root3, C._tree([(slot1[made[id(grp)]] + 2, lo, hi)]))
        octn.rooms[0][3].check()
        listed = 1
    if form_listed:
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            pm = bytearray(prm)
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

    repl = {B.ext['.prp']: data, B.ext['.gms']: kl_gms.pack(gms), B.ext['.buf']: buf,
            B.ext['.oct']: octn.pack(), B.ext['.rmi']: rmin.pack(), B.ext['.rmc']: rmcn.pack()}
    if new_prm is not None:
        repl[B.ext['.prm']] = new_prm
    repl = {n: v for n, v in repl.items() if v != B.files[n]}
    os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, os.path.basename(B.zp))
    LO.patch_zip(B.zp, out, repl)                       # every other member copied unchanged (bytes, compression, stamp, order)
    after = _sizes(out)
    if before != after:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    rep = collections.OrderedDict(
        source=B.zp, out=out, members_changed=sorted(e for e, n in B.ext.items() if n in repl), entities_before=len(B.ents), entities=len(ents),
        entities_added=len(order), group=GROUP, group_listed_in_root_tree_3=listed, ref_ids='%d..%d' % (ref0, nxt - 1), slot_ids_moved=moved,
        prm_model_roots_repointed=repointed, slot_id_faults_before=pre, slot_id_faults_after=post, big_before=before, big_after=after)
    log('written %s: %d entities added (1 ZGROUP, %d ZBoxPrimitive), REF ids %s; members changed: %s; %d slot ids renumbered; group listed in root tree 3: %s; '
        '%d model roots re-pointed' % (out, len(order), len(order) - 1, rep['ref_ids'], ' '.join(rep['members_changed']), moved, 'yes' if listed else 'no', repointed))
    return rep


def _sizes(zp):
    with zipfile.ZipFile(zp) as z:
        return collections.OrderedDict((e, next(i.file_size for i in z.infolist() if i.filename.endswith('_Main' + e))) for e in F.BIG)


# ------------------------------------------------------------------ read back
def check(zp, base=None, log=print):
    """Read a staged zip back -> [(status, text)]. Every added box: place, size, both controllers; the group; every old node unchanged; the slot ids; the big blocks."""
    out = []
    ok = lambda c, t: out.append(('PASS' if c else 'FAIL', t))
    CA.use_slot(zp)
    A = F.Built(zp)
    sc = A.sc
    tops = [t for t in sc.tops() if sc.names[t] == GROUP]
    ok(len(tops) == 1, 'one %s group' % GROUP)
    if len(tops) != 1:
        return out
    g = tops[0]
    kids = [k for k in range(1, len(sc.nodes)) if sc.parent[k] == g]
    ok(sc.cls(g) == 'ZGROUP' and len(kids) >= 1, 'the group is a ZGROUP with %d boxes' % len(kids))
    effects = {e['off']: e for e in zip_effects(zp)}
    seen = set()
    for k in kids:
        v = A.values(k)
        cv = {sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']}
        ci = {c: [x for kk, i, x in kl_fa.controllers(sc, c) if kk == k] for c in ('CheckInside', 'Audio_ReverbActivater')}
        e = A.ents[k - 1]
        good = (sc.cls(k) == 'ZBoxPrimitive' and e.flags == 0x200000 and e.model == 0 and cv == {'CheckInside', 'Audio_ReverbActivater'}
                and len(ci['CheckInside']) == 1 and len(ci['Audio_ReverbActivater']) == 1)
        if good:
            ch, au = ci['CheckInside'][0], ci['Audio_ReverbActivater'][0]
            good = (ch[0] == '' and ch[1] == sc.path[k] and ch[2:4] == ['CheckInsideEnter', 'CheckInsideLeave'] and ch[4:] == [1, 0, 1, 0, 0, 0, 0]
                    and au[0] in effects and au[1:3] == ['CheckInsideEnter', 'CheckInsideLeave'] and 30.0 <= au[3] <= 100.0
                    and all(v['ZBoxPrimitive[%d]' % a] >= 1.0 for a in range(3)) and sc.names[k] not in seen
                    and tuple(A.at(k)) == tuple(struct.unpack('<3f', e.trans[:12])) and list(v['ZGEOM[2]']) == list(A.at(k)))
            seen.add(sc.names[k])
        ok(good, '%s: CheckInside (own path) + Audio_ReverbActivater (an effect of the zip\'s .SND) + size + place' % sc.names[k])
    ok(not any(s == 'FAIL' for s, _t in out), 'all %d boxes read back' % len(kids))
    ok(len(A.ents) == len(sc.nodes) - 1, 'entities == nodes')
    octx, rmi, rmc = O.Oct.parse(A['.oct']), O.RoomIndex.parse(A['.rmi']), O.RoomIndex.parse(A['.rmc'])
    ok(F.room_sets_check(A.scene, octx, rmi, rmc) == [], 'room trees and room index agree with the scene (slot ids)')
    ok(octx.pack() == A['.oct'] and rmi.pack() == A['.rmi'] and rmc.pack() == A['.rmc'], '.oct / .rmi / .rmc re-pack byte for byte')
    if base:
        CA.use_slot(base)
        Bs = F.Built(base)
        n0 = len(Bs.sc.nodes)
        ok(len(sc.nodes) == n0 + 1 + len(kids), 'node count = base + group + boxes')
        fa, fb = J.fingerprints(sc), J.fingerprints(Bs.sc)
        # a subtree hash of an old node that is a top-level one stays equal; the root's changes by the new group, so compare the old tops one by one
        old_tops = [t for t in Bs.sc.tops()]
        new_tops = [t for t in sc.tops() if t != g]
        ok(len(old_tops) == len(new_tops) and all(fa[a] == fb[b] for a, b in zip(new_tops, old_tops)), 'every old top-level subtree identical (%d)' % len(old_tops))
        ok(_sizes(zp) == _sizes(base), 'the four large blocks keep their size')
        with zipfile.ZipFile(zp) as za, zipfile.ZipFile(base) as zb:
            na, nb = za.namelist(), zb.namelist()
            ok(na == nb, 'same members in the same order')
            diff = sorted(n.rsplit('_Main', 1)[-1] for n in nb if n in na and za.getinfo(n).CRC != zb.getinfo(n).CRC)
            ok(set(diff) <= {'.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm'}, 'members that differ: %s' % ' '.join(diff))
        # old entities: names, classes and .gms records unchanged apart from slot order
        ok([e.name for e in Bs.ents] == [e.name for e in A.ents[:len(Bs.ents)]], 'old entity names/order unchanged')
    for s, t in out:
        if s == 'FAIL':
            log('FAIL: ' + t)
    log('CHECK %s: %d PASS, %d FAIL' % (zp, sum(1 for s, _t in out if s == 'PASS'), sum(1 for s, _t in out if s == 'FAIL')))
    return out


# ------------------------------------------------------------------ staging + installer
INSTALL_PY = r'''"""Room reverb 1108 (kl_dm_reverb.py) for one Dead Men map: @FILES@. md5-pinned, all or nothing.
Live files must equal pins.json 'old' (else REFUSED, nothing touched: stage again with `python tools/kl_dm_reverb.py stage-map ...`).
Backups: each live file is renamed to <live>@TAG@ beside it (refused when one exists). Any failure rolls every rename back.
--undo needs live == pinned 'new' and the backup == pinned 'old', then puts the backups back (the staged files stay for a re-install).
usage: python install.py [--dry] [--undo] [--skip-run-check] [--game DIR]"""
import hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TAG = '@TAG@'
pins = json.load(open(os.path.join(HERE, 'pins.json')))
if '--game' in sys.argv:
    GAME = sys.argv[sys.argv.index('--game') + 1]
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', pins['map'])
undo, dry = '--undo' in sys.argv, '--dry' in sys.argv


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def die(m):
    sys.exit('REFUSED: ' + m)


if '--skip-run-check' not in sys.argv and sys.platform.startswith('win') and b'kl2.exe' in subprocess.run(['tasklist'], capture_output=True).stdout:
    die('kl2.exe is running')
files = pins['files']
live = {f: os.path.join(LIVE, f) for f in files}
bak = {f: live[f] + TAG for f in files}
new = {f: live[f] + '.new' for f in files}
for f in files:
    if not os.path.isfile(live[f]):
        die('%s is missing' % live[f])
if not undo:
    for f, p in files.items():
        if md5(live[f]) != p['old']:
            die('%s changed since it was staged (md5 %s, pinned %s): stage again' % (live[f], md5(live[f]), p['old']))
        if os.path.exists(bak[f]):
            die('%s exists: already installed (or a leftover)' % bak[f])
        st = os.path.join(HERE, f)
        if not os.path.isfile(st) or md5(st) != p['new']:
            die('staged %s missing or changed' % st)
    need = max(p['size'] for p in files.values()) + (256 << 20)
    free = shutil.disk_usage(LIVE).free
    if free < need + sum(p['size'] for p in files.values()):
        die('game drive needs %d MB, %d MB free' % ((need + sum(p['size'] for p in files.values())) >> 20, free >> 20))
    print('%s: %d files checked%s' % (pins['map'], len(files), ' (dry run, nothing written)' if dry else ''))
    if dry:
        sys.exit(0)
    done, copied = [], []
    try:
        for f in files:
            shutil.copyfile(os.path.join(HERE, f), new[f]); copied.append(f)
            if md5(new[f]) != files[f]['new']:
                raise RuntimeError('copy of %s differs' % f)
        for f in files:
            os.replace(live[f], bak[f]); done.append(f)
            os.replace(new[f], live[f])
    except BaseException as ex:
        for f in reversed(done):
            if os.path.exists(bak[f]):
                os.replace(bak[f], live[f])
        for f in copied:
            if os.path.exists(new[f]):
                os.remove(new[f])
        sys.exit('FAILED (%s): rolled back, live files as they were' % ex)
    bad = [f for f in files if md5(live[f]) != files[f]['new'] or md5(bak[f]) != files[f]['old']]
    if bad:
        sys.exit('VERIFY FAILED for %s: run --undo' % bad)
    print('INSTALLED %s: %s (backups *%s)' % (pins['map'], ' '.join(files), TAG))
else:
    for f, p in files.items():
        if not os.path.isfile(bak[f]) or md5(bak[f]) != p['old']:
            die('backup %s missing or not the pinned original' % bak[f])
        if md5(live[f]) != p['new']:
            die('%s is not the staged file any more (changed since): not touched' % live[f])
    if dry:
        print('%s: undo checked (dry run)' % pins['map']); sys.exit(0)
    for f in files:
        os.replace(bak[f], live[f])
    bad = [f for f in files if md5(live[f]) != files[f]['old']]
    if bad:
        sys.exit('UNDO VERIFY FAILED for %s' % bad)
    print('UNDONE %s: originals restored' % pins['map'])
'''


def stage(zp, dst, src=None, opt=None, bots=None, log=print):
    """Plain zip -> dst/<name>; bots sibling (same plan, must agree) -> dst/<bots name>. Returns (report, outs)."""
    B, P = plan(zp, src, opt, log)
    rep = apply(B, P, dst, log)
    res = check(rep['out'], zp, log)
    outs = {'plain': rep['out']}
    if bots:
        Bb, Pb = plan(bots, src, opt, log)
        if [(b['name'], b['center'], b['half'], b['ref']) for b in Pb['boxes']] != [(b['name'], b['center'], b['half'], b['ref']) for b in P['boxes']]:
            raise ValueError('the bots zip plans other boxes than the plain zip')
        repb = apply(Bb, Pb, dst, log)
        res += check(repb['out'], bots, log)
        outs['bots'] = repb['out']
    with open(os.path.join(dst, 'reverb.json'), 'w') as f:
        json.dump({'plan': P, 'report': rep, 'check': res}, f, indent=1, default=str)
    return rep, outs, res


def stage_map(maps, name, dst, src=None, opt=None, log=print):
    """The live map folder maps/name: plain zip + bots zip + bots.base.md5 -> dst with install.py and pins.json."""
    d = os.path.join(maps, name)
    zips = [f for f in os.listdir(d) if f.endswith('_Main.zip')]
    if len(zips) != 1:
        raise ValueError('%s: %d _Main.zip files' % (d, len(zips)))
    slot = zips[0][:-len('_Main.zip')]
    plain, botsz, base = (os.path.join(d, slot + s) for s in ('_Main.zip', '_Main.bots.zip', '_Main.bots.base.md5'))
    if os.path.isfile(base) and open(base).read().strip() != md5(plain):
        log('NOTE: %s names another plain zip than the live one (the bots sibling drifted before this run)' % base)
    os.makedirs(dst, exist_ok=True)
    rep, outs, res = stage(plain, dst, src, opt, botsz if os.path.isfile(botsz) else None, log)
    files = {}
    old_md5 = {plain: md5(plain), botsz: md5(botsz) if os.path.isfile(botsz) else None, base: md5(base) if os.path.isfile(base) else None}
    new_plain = md5(outs['plain'])
    files[slot + '_Main.zip'] = {'old': old_md5[plain], 'new': new_plain, 'size': os.path.getsize(outs['plain'])}
    if 'bots' in outs:
        files[slot + '_Main.bots.zip'] = {'old': old_md5[botsz], 'new': md5(outs['bots']), 'size': os.path.getsize(outs['bots'])}
        if old_md5[base]:
            bp = os.path.join(dst, slot + '_Main.bots.base.md5')
            with open(bp, 'w', newline='\n') as f:
                f.write(new_plain + '\n')                      # the md5 of the plain zip the sibling was made from (kl_bake_siblings)
            files[slot + '_Main.bots.base.md5'] = {'old': old_md5[base], 'new': md5(bp), 'size': os.path.getsize(bp)}
    with open(os.path.join(dst, 'pins.json'), 'w') as f:
        json.dump({'map': name, 'tag': TAG, 'files': files}, f, indent=1)
    with open(os.path.join(dst, 'install.py'), 'w') as f:
        f.write(INSTALL_PY.replace('@TAG@', TAG).replace('@FILES@', ', '.join(files)))
    log('pins: ' + json.dumps({k: (v['old'][:8], v['new'][:8]) for k, v in files.items()}))
    if any(s == 'FAIL' for s, _t in res):
        raise ValueError('check FAILED')
    return files


def main():
    a = sys.argv[1:]
    opt, src, bots = {}, None, None
    for flag, key in (('--no-inside', 'inside'), ('--no-outside', 'outside')):
        if flag in a:
            a.remove(flag); opt[key] = False
    for flag in ('--src', '--bots'):
        if flag in a:
            i = a.index(flag)
            if flag == '--src':
                src = a[i + 1]
            else:
                bots = a[i + 1]
            del a[i:i + 2]
    if len(a) == 2 and a[0] == 'plan':
        plan(a[1], src, opt)
    elif len(a) == 3 and a[0] == 'stage':
        _r, _o, res = stage(a[1], a[2], src, opt, bots)
        sys.exit(1 if any(s == 'FAIL' for s, _t in res) else 0)
    elif len(a) == 4 and a[0] == 'stage-map':
        stage_map(a[1], a[2], a[3], src, opt)
    elif len(a) in (2, 3) and a[0] == 'check':
        res = check(a[1], a[2] if len(a) == 3 else None)
        sys.exit(1 if any(s == 'FAIL' for s, _t in res) else 0)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
