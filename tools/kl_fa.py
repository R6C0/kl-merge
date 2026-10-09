#!/usr/bin/env python3
"""
The Fragile Alliance layer of a level: what a real round (started from the menu) will trip over,
and the repairs that need no new entity. Spec: re/fa_round.md (this tool's findings and the
route into a round) on top of re/fa_gamemode.md (what a round needs).

    python kl_fa.py check <archive | stock level>     findings, most severe first; exit 1 if any
                                                      CRASH or BROKEN one is left
    python kl_fa.py stock                             the same over the nine stock levels: the
                                                      control (no CRASH / BROKEN finding may show)
    python kl_fa.py repair <archive> <out.prp>        apply repair() to a built level's .prp
                                                      (a scratch copy: for looking, not for install)
    python kl_fa.py keep F07                          the host level's subtrees worth keeping
    python kl_fa.py defines <archive> <out.prp>       only define_master() (the execution crash) on a built level

A level is read from its archive (.prp + .gms + .buf, the English .LOC and the .SND if present),
so check() works on a finished build as well as on kl_graft's joined scene before it is written.

SEVERITY (the first two fail the check)
  CRASH    read in kl2.exe: the game hangs or faults when the round gets there
  BROKEN   the round cannot run its course (nothing to loot, nobody to call the van, no spawn);
           by the census of the nine stock levels unless an address is given
  DEGRADED something a Dog Days round has is missing; the round still plays
  NOTE     differs from every stock level, effect not established

FOR kl_graft (two calls, both on the joined scene `Jn` BEFORE Jn.p.serialize()):
    kept = kl_fa.host_keep(S.prp)                              # the host's position-free FA objects
    sel = kl_graft.Select(s_keep=kept)
    ...
    kl_fa.repair(Jn, kept, log)                                # after dm_rename / the second join
    for f in kl_fa.check(Jn, snd=..., loc=...): log(str(f))
repair() only edits values, appends controllers and shortens reference lists; it never removes a
controller, so the controller indices kl_graft keeps (kl_prmgraph.prp_roots) stay valid.
Every value a repair writes that is not read from a stock level is marked GUESS below.
"""
import collections, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms, kl_rtp, kl_loc
import kl_prpjoin as J
from kl_prp import Prp, units

CRASH, BROKEN, DEGRADED, NOTE = 0, 1, 2, 3
SEV = ('CRASH', 'BROKEN', 'DEGRADED', 'NOTE')
SETTINGS, MONITOR, EXIT = 'OnlineFragileAllianceSettings', 'OnlineEscVehicleMonitor', 'OnlineExitLevelTrigger'
VEHICLES = ('OnlineEscHavokCar', 'OnlineEscAnimatedVehicle')
SPEAKERS = ('ZSpeakerDriver', 'ZSpeakerTeamCriminals', 'ZSpeakerTeamPolice')
START, DEAD, TRAITOR = ('eSPAWN_TYPE_FRAGILE_ALLIANCE_START', 'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH',
                        'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR')
# settings fields (0-based, re/fa_gamemode.md section 7)
S_SOUNDS, S_MUSIC, S_LISTS, S_FLOATS = (3, 4, 5, 157, 158, 159), (157, 158), (331, 332), (324, 325, 326, 327, 328)
# position-free objects of a host level that a Dead Men map lacks (host_keep)
HOST_CTRL = ('FAMissionBriefingTrigger', 'AIMonitor', MONITOR)


class Finding(collections.namedtuple('Finding', 'sev code text fix')):
    def __str__(self):
        return '%-8s %-18s %s%s' % (SEV[self.sev], self.code, self.text, '   [repair: %s]' % self.fix if self.fix else '')


# ------------------------------------------------------------------ reading
def load(src):
    """-> (scene, .SND bytes or None, English .LOC bytes or None). src: an archive path, or the
    name of a stock level (the copy in KL_PortBackup wins, as everywhere)."""
    path = src if os.path.isfile(src) else J.level_zip(src)
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        prp = [n for n in names if n.lower().endswith('_main.prp')][0]
        p, raw, buf = Prp(zf.read(prp)), kl_gms.unpack(zf.read(prp[:-4] + '.gms')), zf.read(prp[:-4] + '.buf')
        snd = next((zf.read(n) for n in names if n.lower().endswith('_main.snd')), None)
        loc = next((zf.read(n) for n in names if n.lower().endswith('_mainenglish.loc')), None)
    ns, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
    for decl, tid, _prio in kl_gms.entities(raw):
        o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
        ns.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
    return J.Scene(p, ns, tids, 'dd', os.path.basename(path)), snd, loc


def value(sc, unit):
    """A field unit as a Python value: str (string / enum name), [str] (reference list), number,
    [numbers] (array), bytes (raw)."""
    unit, keys = list(unit), sc.p.keys
    op, pl = unit[0]
    if op in (0x0c, 0x0e):
        return keys[struct.unpack('<I', pl)[0]]
    if op == 0x04:
        if len(unit) > 1 and unit[1][0] == 0x0d:
            return unit[1][1][4:]
        return [keys[struct.unpack('<I', t[1])[0]] for t in unit[1:]]
    if op == 0x0a:
        return struct.unpack('<f', pl)[0]
    if op == 0x09:
        return struct.unpack('<I', pl)[0]
    if op == 0x08:
        return struct.unpack('<H', pl)[0]
    if op in (0x05, 0x06, 0x07):
        return pl[0]
    if op == 0x01:
        return [value(sc, [t]) for t in unit[1:-1]]
    return None


def controllers(sc, name):
    """[(node, index in the node's controller list, [field values])] of every controller `name`."""
    out = []
    for k in range(1, len(sc.nodes)):
        for i, (nm, body) in enumerate(sc.nodes[k]['ctrls']):
            if sc.p.key(nm) == name:
                out.append((k, i, [value(sc, u) for u in units(body[1:-1])]))
    return out


def has(sc, k, name):
    return any(sc.p.key(nm) == name for nm, _b in sc.nodes[k]['ctrls'])


def node_values(sc, k):
    return [value(sc, u) for u in units(sc.nodes[k]['props'][1:-1])]


def census(sc):
    ctrl, cls = collections.Counter(), collections.Counter()
    for k in range(1, len(sc.nodes)):
        cls[sc.cls(k)] += 1
        ctrl.update(sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls'])
    return ctrl, cls


def loc_keys(loc):
    """Lower-case keys of a .LOC ('a/b/c'), or None without one."""
    kids = kl_loc.parse(loc) if loc else None
    return None if kids is None else {k.lower() for k, _n in kl_loc.leaves(kids)}


def spoken(keys, s):
    """Dog Days looks a key up as K_C1..K_C9 and then K (kl2 0x6b879d, tools/kl_loc.py)."""
    s = s.lower()
    return s in keys or any('%s_c%d' % (s, i) in keys for i in range(1, 10))


# ------------------------------------------------------------------ writing
def _str(sc, s):
    return (0x0c, struct.pack('<I', sc.p.key_index(s)))


def _refs(sc, paths):
    return [(0x04, struct.pack('<I', len(paths)))] + [_str(sc, s) for s in paths]


def edit(sc, k, i, fn):
    """Run fn(list of field units) on controller i of node k (i None: the node itself)."""
    n = sc.nodes[k]
    obj = n['props'] if i is None else n['ctrls'][i][1]
    us = [list(u) for u in units(obj[1:-1])]
    fn(us)
    new = [obj[0]] + [t for u in us for t in u] + [obj[-1]]
    if i is None:
        n['props'] = new
    else:
        n['ctrls'][i] = (n['ctrls'][i][0], new)


def blank(sc, cls, floats=0.0):
    """Tokens of an object of class `cls` with every field empty: lists without entries, empty
    strings, zeros. Only for classes without enum or array fields (an enum needs a real name)."""
    out = [(0x02, b'')]
    for f in J.schema('dd').fields(cls):
        if f.kind == 'refs':
            out.append((0x04, bytes(4)))
        elif f.kind == 's':
            out.append(_str(sc, ''))
        elif f.kind == 'f':
            out.append((0x0a, struct.pack('<f', floats)))
        elif f.kind == 'b':
            out.append((0x06, b'\0'))
        elif f.kind == 'I':
            out.append((0x09, bytes(4)))
        else:
            raise ValueError('%s has a field of kind %s: no blank form' % (cls, f.kind))
    return out + [(0x7e, b'')]


# ------------------------------------------------------------------ the check
def check(sc, snd=None, loc=None, anm=None):
    """Findings about the Fragile Alliance layer of a Dog Days-form scene, most severe first.
    anm: the level's .ANM (bytes), for kl_arms' test of NPC weapons against the animation sets."""
    sch, out = J.schema('dd'), []
    add = lambda sev, code, text, fix=None: out.append(Finding(sev, code, text, fix))
    ctrl, cls = census(sc)
    res = lambda s: sc.resolve(s) if isinstance(s, str) and s else []

    # --- objects that do not fit Dog Days at all
    bad = J.misfits(sc)
    if bad:
        add(CRASH, 'layout', '%d objects do not fit their Dog Days class (the .prp reader asserts at kl2 0x64a856), first: %s %s: %s'
            % (len(bad), sc.path[bad[0][0]], bad[0][1], bad[0][2]))
    enum_bad = collections.Counter()
    for k in range(1, len(sc.nodes)):
        objs = [(sc.cls(k), sc.nodes[k]['props'])] + [(sch.controller(sc.p.key(nm), sc.cls(k)), b) for nm, b in sc.nodes[k]['ctrls']]
        for c, obj in objs:
            fs = sch.fields(c) if c else None
            for f, u in zip(fs or (), units(obj[1:-1])):
                if f.kind == 'e' and f.enum in sch.enums and u[0][0] == 0x0e:
                    v = sc.p.key(u[0])
                    if v not in [o[0] for o in sch.enums[f.enum]['options']]:
                        enum_bad[c, sch.enums[f.enum]['name'], v] += 1
    for (c, e, v), n in enum_bad.most_common():
        add(BROKEN, 'enum', '%d x %s holds %r, which %s does not have (stock levels: 0 such values; what the reader '
            'does with an unknown name is not established)' % (n, c, v, e))
    paths, _names = J.dangling(sc)
    if paths:
        top = collections.Counter(h.split(' (')[0] for _k, h, _f, _s in paths)
        add(DEGRADED, 'paths', '%d scene paths name no node (the link is dead): %s; first: %s -> %s'
            % (len(paths), ', '.join('%s %d' % x for x in top.most_common(5)), sc.path[paths[0][0]], paths[0][3]),
            'prune() for kept host objects')

    # --- settings (kl2 0x500990 / 0x728ba3: unchecked use of [0x168c630])
    st = controllers(sc, SETTINGS)
    if len(st) != 1:
        add(CRASH if not st else BROKEN, 'settings', '%d OnlineFragileAllianceSettings objects; without one [0x168c630] stays 0 and '
            'the death camera calls through it (0x500990, 0x728ba3); with two the later Init wins' % len(st))
    for k, _i, v in st:
        if sc.cls(k) != 'ZOnlineGameplaySettings':
            add(BROKEN, 'settings', 'the settings controller sits on a %s, stock: ZOnlineGameplaySettings' % sc.cls(k))
        if len(v) != 340:
            continue
        keys = loc_keys(loc)
        if keys is not None:
            miss = [(i, x) for i, x in enumerate(v[:339]) if isinstance(x, str) and x and not spoken(keys, x)]
            if len(miss) > 5:                           # the nine stock levels have 0..5 such strings
                add(DEGRADED, 'settings-text', '%d of %d settings strings are no key of the level\'s .LOC (stock: 0..5 of ~240; '
                    'such a line or HUD text stays silent / empty), e.g. field %d %r'
                    % (len(miss), sum(1 for x in v if isinstance(x, str) and x), miss[0][0], miss[0][1]))
        if snd is not None:
            far = [i for i in S_SOUNDS if v[i] >= len(snd)]
            if far:
                add(CRASH, 'settings-sound', 'settings sound fields %s point beyond the .SND (%d bytes)' % (far, len(snd)))
        if any(v[i] for i in S_LISTS):
            add(NOTE, 'settings-lists', 'settings fields 331 / 332 name %d objects (Dead Men: the escape vehicle\'s two routs); '
                'empty in all nine stock levels, whether Dog Days still uses them is not established' % sum(len(v[i]) for i in S_LISTS),
                'settings_lists()')
        if any(v[i] for i in S_MUSIC):
            add(NOTE, 'settings-music', 'settings fields 157 / 158 = %#x / %#x: Dead Men\'s level music and FA music; 157 is 0 in all nine '
                'stock levels but Init still forwards it (0x88edba -> 0x8ce720): listen for music in the round' % (v[157], v[158]))
    defines = collections.Counter(v[1] for _k, _i, v in controllers(sc, 'ZSetZDefine') if len(v) == 2)
    d = [0] * defines['IsMultiplayerLevel']
    if len(d) != 1:
        add(BROKEN if not d else NOTE, 'define', '%d ZSetZDefine \'IsMultiplayerLevel\' (stock: exactly 1; read at kl2 0x55d900, 0x602f90, 0x8859c0)' % len(d))
    for name, late, copies in define_order(sc):
        add(CRASH, 'define-order', 'ZSetZDefine %r: the last of its %d setters in scene order is the clone TEMPLATE %s, not one of its '
            '%d pooled copies (all 21 stock levels: a copy is last). The define then names an object whose clone master [+0x58] is '
            '0; for ExecutionBloodSpatter kl2 0x4098a1 calls through it when a human shield is executed (the owner\'s crash of '
            '2026-10-09 18:20, re/combat.md)' % (name, len(late) + len(copies), sc.path[late[-1][0]], len(copies)), 'define_master()')
    import kl_arms
    for sev, code, text in kl_arms.check(sc, anm):
        add(sev, code, text, 'kl_arms.arm()' if sev == BROKEN else None)

    # --- escape: exit trigger -> monitor -> vehicle
    ex, mon = controllers(sc, EXIT), controllers(sc, MONITOR)
    if not ex:
        add(BROKEN, 'exit-trigger', 'no OnlineExitLevelTrigger: nothing calls the escape vehicle (9 of 9 stock levels have one)')
    if ex and not mon:
        add(CRASH, 'monitor', 'an exit trigger but no OnlineEscVehicleMonitor: ZOnlineExitLevelTrigger slot 34 tail-calls 0x6276e0 '
            'with ecx = [0x168cc00] = 0, which reads [ecx+0x48] (0x6276fc) the moment the trigger picks a vehicle', 'monitor()')
    if len(mon) > 1:
        add(BROKEN, 'monitor', '%d OnlineEscVehicleMonitor: each Init deletes the one before (0x8d2b63)' % len(mon))
    for k, _i, v in ex:
        if len(v) != 6:
            continue
        picks = [x for x in v[2:6] if x]
        if not picks:
            add(CRASH, 'exit-trigger', '%s: fields 2..5 are all empty: the random pick at 0x6c3f90 never ends%s'
                % (sc.path[k], ' (the vehicle is in field 1, Dead Men\'s place)' if v[1] else ''), 'exit_trigger()' if v[1] else None)
        if v[0] and not v[1]:
            add(NOTE, 'exit-trigger', '%s: field 0 is set but field 1 names nothing' % sc.path[k])
        for x in picks + ([v[1]] if v[1] else []):
            hit = res(x)
            if not hit:
                add(CRASH if x in picks else BROKEN, 'exit-trigger', '%s names %r, which is no node' % (sc.path[k], x))
            elif not any(has(sc, hit[0], c) for c in VEHICLES):
                add(BROKEN, 'exit-trigger', '%s names %s, which has neither OnlineEscHavokCar nor OnlineEscAnimatedVehicle' % (sc.path[k], x))
    cars = controllers(sc, 'OnlineEscHavokCar')
    for k, _i, v in cars:
        for i, what in ((0, 'incoming rout'), (1, 'escaping rout'), (2, 'boarding trigger')):
            if v[i] and not res(v[i]):
                add(BROKEN, 'vehicle', '%s: field %d (%s) names no node: %s' % (sc.path[k], i, what, v[i]))
        body = collections.Counter(sc.cls(j) for j in range(k, sc.end[k]))
        if not (body['ZHavokCar'] or body['ZHeli']):
            add(BROKEN, 'vehicle', '%s: an OnlineEscHavokCar group without a ZHavokCar or ZHeli below it (classes: %s) - a retyped car '
                'cannot drive' % (sc.path[k], dict(body.most_common(4))))
        elif body['ZHavokCar']:
            add(DEGRADED, 'vehicle', '%s: the escape vehicle is a ZHavokCar driven along a spline (%d OnlineVehicleOnSpline in the level). '
                'Dog Days\' exe has the classes but none of its nine FA levels uses a ground car this way (vans are baked '
                'ZAnimatedVehicle, the rest helicopters): UNTESTED path, watch it arrive, take passengers and leave'
                % (sc.path[k], ctrl['OnlineVehicleOnSpline']))
    if ex and not cars and not ctrl['OnlineEscAnimatedVehicle']:
        add(BROKEN, 'vehicle', 'no OnlineEscHavokCar and no OnlineEscAnimatedVehicle in the level')
    for k, _i, v in controllers(sc, 'OnlineEscCamTrigger'):
        if len(v) == 2 and v[0] and not v[1] and res(v[0]) and has(sc, res(v[0])[0], 'CCameraBox'):
            add(DEGRADED, 'esc-camera', '%s: the camera is in field 0 (Dog Days: the vehicle), field 1 is empty' % sc.path[k], 'cam_trigger()')
        elif len(v) == 2 and v[1] and not res(v[1]):
            add(DEGRADED, 'esc-camera', '%s: field 1 names no node: %s' % (sc.path[k], v[1]))

    # --- spawn points and players
    types = collections.Counter(node_values(sc, k)[8] for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint')
    if types[START] < 8:
        add(BROKEN, 'spawn', '%d FRAGILE_ALLIANCE_START spawn points (stock: 8 in 9 of 9; a round has up to 8 criminals; what a '
            'missing point does is not established)' % types[START])
    if not types[DEAD]:
        add(BROKEN, 'spawn', 'no FRAGILE_ALLIANCE_AFTER_DEATH spawn point: a dead criminal has nowhere to return as police')
    if not types[TRAITOR]:
        add(DEGRADED, 'spawn', 'no FRAGILE_ALLIANCE_TRAITOR spawn point (stock: 4 or 6)')
    lack = [t for t in ('TEAM_MERC', 'TEAM_POLICE', 'UCC') if not any(t in x for x in types)]
    if lack:
        add(DEGRADED, 'spawn-modes', 'no spawn points of the Dog Days-only kinds %s: Cops & Robbers / Undercover Cop cannot place '
            'players (plain Fragile Alliance and Arcade use START / AFTER_DEATH / TRAITOR: ASSUMPTION from Dead Men having only those)'
            % ', '.join(lack))
    heroes = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFPlayer']
    if len(heroes) != 16:
        add(BROKEN, 'players', '%d ZFFPlayer entities (stock: 16 = Hero_01..08 and eight police; the server hands a dead criminal the '
            'first free type-3 player, 0x6ee860)' % len(heroes))

    # --- the round's own triggers, bounds, money
    kinds = collections.Counter(v[0] for _k, _i, v in controllers(sc, 'OnlineGamePlayTrigger') if v)
    for e in ('eOGPT_PLAYER_ENTERS_BANK', 'eOGPT_PLAYER_EXITS_BANK', 'eOGPT_PLAYER_BOARDS'):
        if not kinds[e]:
            add(BROKEN, 'gameplay-trigger', 'no OnlineGamePlayTrigger %s (stock: at least one of each in 9 of 9)' % e)
    if not ctrl['LevelBound']:
        add(DEGRADED, 'bounds', 'no LevelBound: players can leave the map')
    money = collections.Counter()
    for k, _i, v in controllers(sc, 'OnlineMoneyCtrl'):
        if len(v) == 12:
            money[v[2]] += 1
    if money and not any('DROP' in t for t in money):
        add(BROKEN, 'money', 'no OnlineMoneyCtrl of the DROP type: money a player drops has no object (stock: 100 or 108 + 25)')
    if not any(n for t, n in money.items() if 'DROP' not in t):
        add(BROKEN, 'money', 'no loot: every OnlineMoneyCtrl is a DROP stack (stock: 5..58 NORMAL or CONTAINER objects)')
    for k, _i, v in controllers(sc, 'OnlineMoneyContainer'):
        tgt = [j for s in v[0] for j in res(s)] if v and isinstance(v[0], list) else []
        if not any(has(sc, j, 'OnlineMoneyCtrl') for j in tgt):
            add(DEGRADED, 'money', '%s: the container\'s field 0 names no OnlineMoneyCtrl object' % sc.path[k]); break

    # --- what Dog Days levels have and a Dead Men map does not
    if not ctrl['AIMonitor']:
        add(DEGRADED, 'ai-monitor', 'no AIMonitor: nothing is started by the round-start event (0x8b5f60, event 2). The nine stock '
            'levels start the briefing, the loot marker, the bots and the opening from it; a Dead Men map starts its squads from '
            'trigger boxes instead (%d TriggerBox, %d OnlineTriggerBox here)' % (ctrl['TriggerBox'], ctrl['OnlineTriggerBox']),
            'host_keep() + prune()')
    elif ctrl['AIMonitor'] > 8:
        add(NOTE, 'ai-monitor', '%d AIMonitor: the table at 0x168a258 takes 8, the rest are ignored' % ctrl['AIMonitor'])
    if not ctrl['FAMissionBriefingTrigger']:
        add(DEGRADED, 'briefing', 'no FAMissionBriefingTrigger: the briefing lines of settings 17..21 are never asked for', 'host_keep()')
    gone = [c for c in SPEAKERS if not cls[c]]
    if gone:
        add(DEGRADED, 'speakers', 'no %s (one each in 9 of 9 stock levels; ASSUMPTION: the voices of the driver and of the team '
            'announcements; what a missing speaker does to a line was not read in code)' % ', '.join(gone), 'host_keep()')
    if ctrl['PointOfInterest'] < 2:
        add(DEGRADED, 'markers', '%d PointOfInterest (stock: 2, FA_LOOT and FA_ESCAPE): no loot / escape marker on the HUD. They are '
            'positional, so they have to be authored for the map' % ctrl['PointOfInterest'])
    cams = [x for x in defines if x.startswith('MercSpawn')]
    if not cams:
        add(NOTE, 'spawn-camera', 'no ZSetZDefine MercSpawnCam*: the spawn / respawn camera falls back to the player\'s own '
            '(0x6c24fb tests for null; the second reader 0x8dbc20 was not read)')
    if not ctrl['TriggerLootDepleted']:
        add(DEGRADED, 'bots', 'no bot squads (TriggerLootDepleted 0, stock 7): in Arcade the other criminals are AI; here the player '
            'is alone with the police')
    squads = controllers(sc, 'ZSquadScript')
    if squads:
        named = set()
        for _k, _h, _f, s, hit in J.references(sc):
            named.update(hit)
        idle = [k for k, _i, _v in squads if not any(j in named for j in range(k, sc.end[k]))]
        if idle:
            add(DEGRADED if len(idle) < len(squads) else BROKEN, 'squads', '%d of %d squads are named by no object (nothing can start '
                'them; stock: 0..2 per level), e.g. %s' % (len(idle), len(squads), sc.path[idle[0]]))
    else:
        add(BROKEN, 'squads', 'no ZSquadScript: no police')
    unknown = collections.Counter()
    for k in range(1, len(sc.nodes)):
        for nm, _b in sc.nodes[k]['ctrls']:
            n = sc.p.key(nm)
            if n not in sch.controllers and n not in sch.unregistered:
                unknown[n] += 1
    if unknown:
        add(NOTE, 'unregistered', 'controllers kl2.exe does not register (skipped cleanly at 0x4f9800): %s'
            % ', '.join('%s %d' % x for x in unknown.most_common()))
    if snd is not None:
        low = snd.lower()
        mute = []                                       # kl_graft.mute_speech's rule: the line is the first STRING token
        for k in range(1, len(sc.nodes)):
            for nm, body in sc.nodes[k]['ctrls']:
                line = next((sc.p.key(t) for t in body if t[0] == 0x0c), '')
                if sc.p.key(nm) == 'OnlineSpeakTrigger' and ('audio:dialog/%s#sound' % line.lower()).encode('latin1') not in low:
                    mute.append(sc.path[k])
        if mute:
            add(CRASH, 'speak-trigger', '%d OnlineSpeakTrigger name a line the .SND lacks: they delete themselves in Init (0x4eae60) '
                'and the first checkpoint calls into freed memory (kl_graft.mute_speech), e.g. %s' % (len(mute), mute[0]))
    wide = money_triggers(sc)
    if wide and any(sc.cls(k) == 'ZHavokCar' for k in range(1, len(sc.nodes))):
        add(CRASH, 'money-trigger', '%d money triggers (TriggerBox2 beside OnlineMoneyCtrl / OnlineMoneyContainer) fire for anything '
            'tracked, and the level has a ZHavokCar: a car within reach of loot is handed to ZGameRulesHeist slot 201 as an actor '
            '(kl2 0x6a8902, run ESC1), e.g. %s' % (len(wide), sc.path[wide[0][0]]), 'money_people')
    # a JumpPoint that gets a message: its handler (kl2 0x491e20) sets the request [0x156b35c], and
    # 0x8f3fa0 then also moves the player's CREW ([player + 0xcd0] -> +0xa4). ZFFPlayer slot 82
    # (0x89ca94) creates a crew only for player types 0 and 1 (the story's two); a Fragile Alliance
    # player has none: read of address 0xa4 at kl2 0x8f40c9 (run RT3, Retomoto's first join).
    # Stock: no object of any of the 21 levels names a JumpPoint.
    jumps = {k for k, _i, _v in controllers(sc, 'JumpPoint')}
    named = sorted({sc.path[k] for k, _h, _f, _s, hit in J.references(sc) if k >= 0 and jumps & set(hit)}) if jumps and ctrl[SETTINGS] else []
    if named:
        add(CRASH, 'jump-point', '%d objects send a message to a JumpPoint: the jump then walks the crew of a player that has none '
            '(kl2 0x8f40c9), e.g. %s' % (len(named), named[0]))
    return sorted(out, key=lambda f: f.sev)


# ------------------------------------------------------------------ repairs (values only, no new entity)
MONEY = ('OnlineMoneyCtrl', 'OnlineMoneyContainer')


def money_triggers(sc):
    """[(node, controller index)] of every TriggerBox2 on a node with a money controller whose
    field [3] is 0."""
    out = []
    for k in range(1, len(sc.nodes)):
        if any(has(sc, k, m) for m in MONEY):
            for i, (nm, body) in enumerate(sc.nodes[k]['ctrls']):
                if sc.p.key(nm) == 'TriggerBox2':
                    v = [value(sc, u) for u in units(body[1:-1])]
                    if len(v) == 7 and v[3] == 0:
                        out.append((k, i))
    return out


def money_people(sc, log=print):
    """TriggerBox2 field [3] = 1 on every money trigger: only people set it off.
    WHY (run ESC1, 2026-10-09: the first time Dead Men's escape van drove in Dog Days): the van
    stopped 40 units from a dropped wallet and the process faulted at kl2 0x6a8902. Read:
    ZTriggerBox2's update (slot 25, 0x626ec0) asks the entity tracker for everything within reach;
    when byte +0x44 is set (0x626fbd) it skips whatever is not of class [0x1548c7c] and not a
    player; otherwise the object is the activator of the message. ZOnlineMoneyCtrl slot 26
    (0x6cdb40) passes the activator to ZGameRulesHeist slot 201 (0x56f6e0), which takes anything
    that is not a player for an actor and reads [activator + 0x2940] (0x6a88fc): on a ZHavokCar
    (vtable 0xbcb00c, on the stack of the dump) that is not a pointer. No stock Fragile Alliance
    level has a ZHavokCar, so stock never gets there.
    Field [3] <-> byte +0x44 is an ASSUMPTION from one object in the dump (fields list, 1, 90.0,
    0, 0, message, 0 against bytes +0x3c: 00 01 00 00 / 90.0 / 00 00 / message / 0) and from stock:
    the pooled drop stacks (FASpecials!DropMoney!TeamModeDropMoney) store 1 there.
    -> the number of triggers changed."""
    hit = money_triggers(sc)
    for k, i in hit:
        def fn(us):
            us[3] = [(us[3][0][0], bytes([1]) + us[3][0][1][1:])]
        edit(sc, k, i, fn)
    if hit:
        log('  kl_fa: %d money triggers answer to people only now (TriggerBox2 field 3; a car as activator faults at kl2 0x6a8902)' % len(hit))
    return len(hit)

def define_order(sc):
    """[(define name, [(node, controller index)] of setters that come AFTER the last pooled copy, the copies)] for
    every ZSetZDefine name set both by nodes inside a 'CloneGroup_' subtree and by nodes outside of it.
    ZSetZDefine's Init (kl2 0x5c9b20, vtable 0xba8c3c slot 13) stores name -> this entity in the scene's define
    table ([[0xdd2640]+0xac]+0x116c, slot +0x54); the LAST Init wins (not read in the table's code: in the dump
    of the crash the define held the template, which is the last setter of that build and the first of every
    stock level). Order of Init = scene order is the ASSUMPTION behind 'last'."""
    sets = collections.OrderedDict()
    for k, i, v in controllers(sc, 'ZSetZDefine'):
        if len(v) == 2:
            sets.setdefault(v[1] or sc.names[k], []).append((k, i))
    out = []
    for name, l in sets.items():
        copies = [x for x in l if sc.names[sc.top[x[0]]].startswith('CloneGroup_')]
        late = [x for x in l if copies and x not in copies and x[0] > copies[-1][0]]
        if late:
            out.append((name, late, copies))
    return out


def define_master(sc, log=print):
    """A clone template that sets a define AFTER its pooled copies gets a define name of its own, so that the
    last setter of the real name is a copy again, as in every stock level.
    WHY (the owner's crash of 2026-10-09 18:20, kl2 0x4098a1, re/combat.md): the template of the blood spatter
    (ZAllocMany ...Effects/BulletImpacts.zip / Bullet / Blood_02) and each of its eight copies in
    CloneGroup_Effects/BulletImpacts.zip/Bullet/Blood_02 carry ZSetZDefine 'ExecutionBloodSpatter'. Stock: the
    systems subtree comes before the clone groups, a copy is last. A graft onto a Dead Men map takes the map's
    top-level order, where the clone groups come first: the template is last. ZFFActionShootHumanShield slot 11
    (0x4097c0, the execution shot) takes the define, reads its clone master at +0x58 - set on a COPY by the
    template's own slot 84 (0x48e1f3), 0 on the template - and calls through it.
    The new name '<name>_Template' is read by nothing (GUESS that one more name in the table is harmless: stock
    levels have 22..27 names). Only a string value changes. -> the number of controllers renamed."""
    n = 0
    for name, late, _copies in define_order(sc):
        for k, i in late:
            def fn(us, name=name):
                us[1] = [_str(sc, name + '_Template')]
            edit(sc, k, i, fn); n += 1
        log('  kl_fa: ZSetZDefine %r: %d clone template(s) set it after the pooled copies - renamed to %r, a copy is the last '
            'setter again (the human-shield execution crash at kl2 0x4098a1)' % (name, len(late), name + '_Template'))
    return n


def exit_trigger(sc, log=print):
    """Dead Men's vehicle (one string) belongs in Dog Days field 2, with field 0 false: fields
    2..5 are the random pick, field 1 is used once and only while field 0 is set (kl2 0x6c3f64)."""
    n = 0
    for k, i, v in controllers(sc, EXIT):
        if len(v) == 6 and v[1] and not any(v[2:6]):
            def fn(us):
                us[2], us[1], us[0] = us[1], [_str(sc, '')], [(0x06, b'\0')]
            edit(sc, k, i, fn); n += 1
    if n:
        log('  kl_fa: %d exit trigger(s): vehicle moved from field 1 to field 2' % n)
    return n


def cam_trigger(sc, log=print):
    """OnlineEscCamTrigger: the camera is Dog Days field 1; field 0 is the animated vehicle or ''."""
    n = 0
    for k, i, v in controllers(sc, 'OnlineEscCamTrigger'):
        hit = sc.resolve(v[0]) if len(v) == 2 and v[0] and not v[1] else []
        if hit and has(sc, hit[0], 'CCameraBox'):
            def fn(us):
                us[0], us[1] = [_str(sc, '')], us[0]
            edit(sc, k, i, fn); n += 1
    if n:
        log('  kl_fa: %d escape camera trigger(s): camera moved to field 1' % n)
    return n


def monitor(sc, log=print):
    """Give a level with an exit trigger and no OnlineEscVehicleMonitor one: a controller with nine
    empty lists and the four (-1.0, empty list) pairs every stock monitor has. With empty lists
    every case of 0x6276e0 leaves at its 'cmp [esi+0x48], 0 / je' test, so the object only has to
    exist. It is registered for ZGEOM (re/kl2.json), so any node can carry it.
    GUESS: the host node. Stock monitors sit on a ZBoxPrimitive of their own; this one goes on the
    first controller-less ZBoxPrimitive / ZGROUP / ZSTDOBJ of the exit trigger's top-level
    subtree, else on the trigger's own node. Consequences of the empty lists (stock: 3..9 targets):
    no 'last escape vehicle' message, no clean-up of boarding triggers when a vehicle is lost."""
    ex = controllers(sc, EXIT)
    if not ex or controllers(sc, MONITOR):
        return 0
    k0 = ex[0][0]
    t = sc.top[k0]
    host = next((k for k in range(t, sc.end[t]) if not sc.nodes[k]['ctrls'] and sc.cls(k) in ('ZBoxPrimitive', 'ZGROUP', 'ZSTDOBJ')), k0)
    sc.nodes[host]['ctrls'].append((_str(sc, MONITOR), blank(sc, 'ZOnlineEscVehicleMonitor', floats=-1.0)))
    log('  kl_fa: OnlineEscVehicleMonitor (empty) added to %s' % sc.path[host])
    return 1


def settings_lists(sc, log=print):
    """Empty settings fields 331 / 332 as in all nine stock levels. GUESS that this is better than
    Dead Men's two routs: Dog Days starts the vehicle through the exit trigger and the monitor;
    whether its settings Init still does anything with the lists was not read."""
    n = 0
    for k, i, v in controllers(sc, SETTINGS):
        if len(v) == 340 and any(v[j] for j in S_LISTS):
            def fn(us):
                for j in S_LISTS:
                    us[j] = [(0x04, bytes(4))]
            edit(sc, k, i, fn); n += 1
    if n:
        log('  kl_fa: settings fields 331 / 332 emptied')
    return n


def settings_from_host(sc, host, keep=S_SOUNDS + S_FLOATS, log=print):
    """Replace the level's settings values by those of a stock Dog Days level `host` (a scene),
    except the fields in `keep`, which stay the level's own. For a graft that should speak Dog
    Days' lines and show its HUD texts (re/fa_gamemode.md section 7: 'start from the host level's
    settings object'). The default keeps the six sound fields (offsets into THIS level's .SND, so
    they must never come from another level's file unless the bank is the host's own, unmoved)
    and the five per-level timers 324..328 (GUESS: which of Dead Men's four floats they are is
    not established, kl_convert's pairing stands). Not called by repair(): a choice for the lead."""
    src = controllers(host, SETTINGS)
    n = 0
    for k, i, v in controllers(sc, SETTINGS):
        if len(v) != 340 or len(src) != 1 or len(src[0][2]) != 340:
            continue
        theirs = units(host.nodes[src[0][0]]['ctrls'][src[0][1]][1][1:-1])
        def fn(us):
            for j, u in enumerate(theirs):
                if j not in keep:
                    us[j] = J._intern(list(u), host.p.keys, _Table(sc), None)
        edit(sc, k, i, fn); n += 1
    if n:
        log('  kl_fa: settings taken from %s, own fields kept: %s' % (host.label, sorted(keep)))
    return n


class _Table(dict):
    """kl_prpjoin._intern's (table, order) pair backed by a Prp that already has its keys."""
    def __init__(self, sc):
        super().__init__()
        self.sc = sc

    def __contains__(self, s):
        dict.__setitem__(self, s, self.sc.p.key_index(s))
        return True


def host_keep(S):
    """Top-level subtrees of a stock Dog Days level (scene S) that are FA plumbing without a place
    in the world, for kl_graft's Select(s_keep=...): the briefing trigger, the AIMonitor, the
    escape-vehicle monitor, the three speakers, and every single-node timer
    / relay the AIMonitor starts whose own targets are all kept. Everything else the kept objects
    name is gone with the host's map: prune() afterwards. Names, exact (no wildcards)."""
    side, tops = J.sides(S), {}
    for t in S.tops():
        if side[t] == 'map' and S.end[t] - t == 1:
            tops[S.path[t].lower()] = t
    keep = set()
    for t in tops.values():
        if S.cls(t) in SPEAKERS or any(S.p.key(nm) in HOST_CTRL for nm, _b in S.nodes[t]['ctrls']):
            keep.add(t)
    def targets(t):
        return [s for _h, _f, u in J.fields(S, t) for s in J.strings(S, u) if s[:5].upper() == 'ROOT\\']
    grew = True
    while grew:
        grew = False
        for t in [x for x in keep if has(S, x, 'AIMonitor')]:
            for s in targets(t):
                c = tops.get(s.lower())
                if c is not None and c not in keep and not S.nodes[c]['ctrls'] == [] and \
                        any(S.p.key(nm) in ('TriggerDelay', 'TriggerDelay2') for nm, _b in S.nodes[c]['ctrls']) and \
                        targets(c) and all(tops.get(x.lower()) in keep for x in targets(c)):
                    keep.add(c); grew = True
    return [S.names[t] for t in sorted(keep)]


def prune(sc, names, log=print):
    """In the top-level subtrees `names` (what host_keep kept): drop reference-list entries and
    blank strings that name no node - the host's map is gone, and a list entry without a target
    is at best a dead link. -> number of references removed."""
    want, n = {x.lower() for x in names}, 0
    for t in sc.tops():
        if sc.names[t].lower() not in want:
            continue
        for k in range(t, sc.end[t]):
            for i in [None] + list(range(len(sc.nodes[k]['ctrls']))):
                def fn(us):
                    nonlocal n
                    for j, u in enumerate(us):
                        if u[0][0] == 0x04 and len(u) > 1 and u[1][0] == 0x0c:
                            live = [x for x in u[1:] if sc.p.key(x)[:5].upper() != 'ROOT\\' or sc.resolve(sc.p.key(x))]
                            n += len(u) - 1 - len(live)
                            us[j] = [(0x04, struct.pack('<I', len(live)))] + live
                        elif u[0][0] == 0x0c and sc.p.key(u[0])[:5].upper() == 'ROOT\\' and not sc.resolve(sc.p.key(u[0])):
                            us[j] = [_str(sc, '')]; n += 1
                edit(sc, k, i, fn)
    if n:
        log('  kl_fa: %d references of kept host objects into the removed map cut' % n)
    return n


def boarding(sc, log=print):
    """A PlayerAction 'EnterVehicle' in the form of stock Dog Days' Fragile Alliance levels.
    WHY (run ESC2, 2026-10-09): Dead Men's van came, stood beside the player for its whole wait and
    left; E held inside its boarding box did nothing and no prompt showed. Dead Men's action
    converts to field [16] = 'eONLY_KANE' and bools [10..13] = 0, 0, 0, 0. No 'EnterVehicle' action
    of stock F01..F08 (31 of them) has eONLY_KANE: 24 have 'eBOTH_PLAYERS', 7 'eONLY_LYNCH', and
    all 31 have [12] = 1. GUESS that these two are what the boarding needs (the most common stock
    form: [12] = 1, [16] = 'eBOTH_PLAYERS'); what [12] means was not read. -> actions changed."""
    n = 0
    for k, i, v in controllers(sc, 'PlayerAction'):
        if len(v) == 21 and v[7] == 'EnterVehicle' and (v[16] == 'eONLY_KANE' or v[12] == 0):
            def fn(us):
                us[12] = [(us[12][0][0], bytes([1]) + us[12][0][1][1:])]
                us[16] = [(us[16][0][0], struct.pack('<I', sc.p.key_index('eBOTH_PLAYERS')))]
            edit(sc, k, i, fn)
            n += 1
    if n:
        log('  kl_fa: %d boarding actions (PlayerAction EnterVehicle) set to stock form: field 12 = 1, eBOTH_PLAYERS (GUESS)' % n)
    return n


def repair(sc, kept=(), log=print):
    """Everything above that is safe to do without asking: the exit trigger's field, the escape
    camera's field, a monitor if there is none, settings 331 / 332, and prune(kept).
    -> {repair: count}. Run check() afterwards: what is left needs authoring (re/fa_round.md)."""
    done = {'prune': prune(sc, kept, log) if kept else 0, 'exit_trigger': exit_trigger(sc, log), 'cam_trigger': cam_trigger(sc, log),
            'monitor': monitor(sc, log), 'settings_lists': settings_lists(sc, log),
            'boarding': boarding(sc, log), 'define_master': define_master(sc, log),
            'money_people': money_people(sc, log) if any(sc.cls(k) == 'ZHavokCar' for k in range(1, len(sc.nodes))) else 0}
    return {k: v for k, v in done.items() if v}


# ------------------------------------------------------------------ command line
def report(src, log=print):
    sc, snd, loc = load(src)
    import kl_arms
    fs = check(sc, snd, loc, kl_arms.read_anm(src))
    ctrl, _cls = census(sc)
    log('%s: %d nodes; %s' % (src, len(sc.nodes), ', '.join('%s %d' % (c, ctrl[c]) for c in
        (SETTINGS, EXIT, MONITOR, 'OnlineEscHavokCar', 'OnlineEscAnimatedVehicle', 'AIMonitor', 'OnlineMoneyCtrl', 'ZSquadScript'))))
    for f in fs:
        log('  ' + str(f))
    return fs


def main():
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'check':
        sys.exit(1 if any(f.sev <= BROKEN for f in report(a[1])) else 0)
    elif a == ['stock']:
        worst = 0
        for L in J.DD_FA:
            worst += sum(f.sev <= BROKEN for f in report(L))
        print('stock levels: %d CRASH / BROKEN findings (must be 0)' % worst)
        sys.exit(1 if worst else 0)
    elif len(a) == 3 and a[0] == 'repair':
        sc, snd, loc = load(a[1])
        print(repair(sc))
        data, bad, paths, _n = J.check(sc, log=lambda *_a: None)
        open(a[2], 'wb').write(data)
        print('written %s; objects that do not fit: %d; dead scene paths: %d' % (a[2], len(bad), len(paths)))
        for f in check(sc, snd, loc):
            print('  ' + str(f))
    elif len(a) == 3 and a[0] == 'defines':
        sc, snd, loc = load(a[1])
        n = define_master(sc)
        data, bad, _paths, _n = J.check(sc, log=lambda *_a: None)
        open(a[2], 'wb').write(data)
        print('written %s: %d define(s) renamed; objects that do not fit: %d; define-order faults left: %d' % (a[2], n, len(bad), len(define_order(sc))))
    elif len(a) == 2 and a[0] == 'keep':
        for n in host_keep(load(a[1])[0]):
            print(n)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
