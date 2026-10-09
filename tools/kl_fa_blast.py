#!/usr/bin/env python3
"""
Retomoto Tower: the window blast made 'volatile, like the Subway one' (owner, 2026-10-09 18:40:
'it does the explosion but not smoke or anything or camera shake'). Offline; nothing here installs
anything or starts the game. Spec, evidence, the side-by-side table: re/retomoto_blast.md.
The sequence (arm at 9 s, blast 4 s later) and the street layer are not touched: this file hangs
its objects on the blast timer kl_fa_author already has, and edits nothing of that file.

    python kl_fa_blast.py test <out> [--keep] [--no-ai] [options]
                                     build F07 + M09_B + M09_A with kl_fa_author's layer,
                                     kl_fa_street's and this one into <out> (a scratch folder),
                                     verify, kl_fa.check, read the blast back from the archive:
                                     objects, every template / sprite / texture / sound they name,
                                     the opening's timeline. Exit 1 on an unknown problem.
                                     --blast X        strength knob: 1.0 default, 0.5 mild, 1.5 heavy
                                     --blast-second S a second, smaller pop S seconds after the blast
                                                      (default: none - Subway has none; 0.5 from --blast 1.5)
                                     --blast-no-fire  dust clusters instead of the two fireballs
                                     --blast-quiet    the added clusters carry no sound of their own
                                     --blast-daze     OPTION (GUESS, see DAZE): the bomb keeps its reach, damage 0
                                     --blast-bomb-native  TEST: the bomb itself spawns a Dog Days cluster instead of
                                                      Dead Men's glass burst (does the hidden bomb spawn anything?)
                                     --blast-real     kl_fa_author's: the bomb keeps its two radii (it can kill)
                                     --loot-bags      the loot as before kl_fa_loot: money bags, the old places.
                                                      Without it the written level is dressed (kl_fa_loot.finish
                                                      through kl_fa_author.FINISH; its options --case dm|dd|bag,
                                                      --case-scale X, --statue suit|bag, --room-reach R go through)
    python kl_fa_blast.py report <archive>   the same read-back of a built level
    python kl_fa_blast.py subway             how stock F01 (Subway) opens: every object of its breach
    python kl_fa_blast.py selftest           the three controllers this file writes, token for token
                                             against stock objects (no build; 20 s)

WHAT WAS MISSING (re/retomoto_blast.md 2; kl2.exe read with debug/dasm.py)
  Shake. Nothing in the level shakes a camera. Dog Days has two ways: the controller ShakeCamera
  (ZShakeCamera: on its message it sends 'msgShakeCamera' {strength, own position, radius} to the
  local players' cameras, kl2 0x6124e0 -> 0x5de4b0 -> 0x756c20) and DocuCamControl (ZDocuCamControl:
  on its message every local player's hand-held camera plays a profile, kl2 0x718a80; Subway's
  breach uses profile 'OnExplosion'). Explode (CExplode) has NO shake of its own: its 18 fields are
  two radii, tinnitus radius, fuse, particle group, two sounds and flags (kl2 0x60b230); the rockets
  carry a ShakeCamera NEXT TO their Explode, on the same message. The campaign shook the camera
  from a cutscene ('Characters!Hero!CameraControl\\Cam_Explosion', a MiniCutsceneRout with a
  camera profile 'effect Shake'): gone with the campaign. Host F07 has no DocuCamControl and no
  ShakeCamera outside the two rocket templates.
  Smoke. The bomb's particle group is Dead Men's 'Particles_M09_BigWindow': glass, frame bits, a
  flash, one 0.7 s smoke puff and three dust emitters - a glass burst, complete in the archive
  (12 templates, 3 sprites). Subway's cloud is three loose emitters with two templates of F01's
  own map (BlowOut_01 / _02): neither the templates nor any loose emitter exists in host F07's
  systems. What every Dog Days level does have are the systems' explosion clusters (ZAllocMany
  under ...\\Effects/BulletImpacts.zip), spawned by an Explode's field 8 - the rocket's fireball,
  smoke, sparks, debris and flash light.

WHAT THIS ADDS (no new entity; six spare F07 helper boxes re-placed, their controller replaced)
  role      at (x y z)            controller(s)                                           cluster
  fan       5850 21150 -100       its own AIDWrapper: 'Activate' to the boxes below that  -
                                  the knobs switch on; + DocuCamControl 'AITrigger'
                                  'OnExplosion' (stock F01's DocuCam_Explotion, the same)
  cloud     5650 21000  150       Explode, harmless                                       FX_Grenade_RPG_01 + rocket sound
  spray     5800 21150 -100       Explode, harmless, local +Y turned outward;             Rocket_Default_01
                                  + ShakeCamera 3.0 x BLAST, 'Activate', 0, 8000
                                  (stock F01's scExplosion: 3.0, 'Activate', 1, 8000)
  glass s   5850 21300 -330       Explode, harmless, outward                              Glass_Exit_01
  glass n   5850 21300  130       Explode, harmless, outward                              Glass_Exit_01
  second    5400 21000 -100       Explode, harmless, fuse SECOND (off by default)         Rocket_Default_01 + rocket sound
  and the campaign's own InvisiBomb (5685 20997 -394, the one that kills the guard at the glass)
  gets the fireball cluster as its particle group (it had none).
  The route is stock's, link for link: kl_fa_author's blast timer (TriggerDelay2) names the fan,
  an AIDWrapper sends 'Activate', an Explode / ShakeCamera on one box takes it - F01's
  tdExplosion -> ... -> awSoundAndSmokeEFX 'Activate', and the rocket's Explode + ShakeCamera on
  one node and one message. Explode and ShakeCamera are cloned token for token from stock F07's
  Rocket_RPG7. The added Explodes have both radii 1 (kl_fa_author's own way of making the bomb
  harmless) and tinnitus radius 0: pictures and sound, whatever --blast-real says about the bomb.

FOR kl_fa_author (the exact lines; until they are in, hook() patches the same three places from
outside for the length of a process, after kl_fa_street's hook or before it, and 'test' does that):
    KEEP = (...) + kl_fa_blast.KEEP                               # kl_fa_author.KEEP
    kl_fa_blast.prepare_host(S, log)                              # last line of prepare_host(S, log)
    kl_fa_blast.wire(sc, log)                                     # last line of wire(sc, log)
Both functions are idempotent; wire() may be called again with other knobs on the same scene
(tested, re/retomoto_blast.md 5).

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence,
not proven. Each is marked where it stands; re/retomoto_blast.md 6 lists them.
"""
import collections, math, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps
import kl_prpjoin as J
import kl_fa_author as au
from kl_prp import units

R = 'ROOT\\'

# ------------------------------------------------------------------ knobs
BLAST = 1.0                             # GUESS, the one strength knob: 0.5 mild, 1.0 default, 1.5 heavy (see active())
SHAKE = (3.0, 8000.0)                   # stock F01 Gameplay!Blowout!scExplosion: ShakeCamera 3.0, 'Activate', 1, 8000.0.
                                        # Field 0 scales the amplitude, field 3 is the reach (kl2 0x756c20: no shake at or
                                        # beyond it, 1/10 at it); a shake lasts 0.3 + 0.5 s whatever the values (0x704e60)
SECOND = None                           # seconds from the blast to a second, smaller pop; None = by BLAST (0.5 from 1.5 on,
                                        # GUESS), 0 = never. Stock Subway has no second pop: all of its breach is one moment
FIRE = True                             # the cloud clusters are the rocket's fireball (GUESS that a breaching charge may
                                        # burn: Subway's cloud is grey dust). False: the systems' concrete dust instead
SOUND = True                            # the cloud clusters play the rocket's explosion sound (GUESS; Subway: four sound
                                        # objects at once). The bomb's own two sounds are not touched either way
DAZE = False                            # OPTION, GUESS, default off: BombWindow03 gets its reach back (600 / 400) and field
                                        # 4 = 0. CExplode gives every local player a 5 s effect of strength 1 - (d / field 0)^2
                                        # (kl2 0x60b540..0x60b637 -> 0x590170; what draws it, 0x82c210, was not read), which
                                        # is 0 with reach 1 and 0 at the START points with 600 (they are 616+ away).
                                        # ASSUMPTION that field 4 is the damage (3000 on the bomb, 700 on the campaign's
                                        # 'kill the player' bomb, 200 on a rocket): if it is not, the heisters die at 13 s
BOMB_GROUP = None                       # TEST, default off: a CLUSTER name ('spray') = BombWindow03 names that Dog Days cluster
                                        # instead of the campaign's 'Particles_M09_BigWindow'. One variable for a live run: the
                                        # owner saw nothing of that group, whose dust would hang for 30 s - if the bomb shows a
                                        # Dog Days cluster, the fault is in the converted group, if not, in the bomb (it is a
                                        # hidden entity with a fuse; nothing else in the level is)

# ------------------------------------------------------------------ the window (M09_A; kl_fa_author's measurements)
GLASS_X = 5850.0                        # the glass; the bay that blows is z -550..350, the floor inside y 20993
BAY = (-550.0, 350.0)
UP = [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0]      # ZGEOM[1] of every stock helper box: the identity
# local +Y -> world +x (out of the room, towards the balcony), +Z stays, +X -> world -y. Every emitter of
# the systems' clusters shoots along its local +Y (ZParticleEmitter[21] = (0, n, 0) on all 30 read).
# ASSUMPTION on the layout [third, second, first column]: kl_fa_author.rot9's, seen live for turns about Y only
OUT = [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0]

# stock F07's rocket: its Explode and ShakeCamera are the token patterns everything here is cloned from
ROCKET = R + 'AllLevels/mainsceneincludes_multiplayer.zip\\AllLevels/equipment.zip\\Projectile\\Projectiles_01\\Rocket_RPG7'
# the systems' clusters, below the folder the rocket's own particle group is in (...\Effects/BulletImpacts.zip).
# name -> (path below it, copies in its clone group = how many can play at once, what it shows)
CLUSTER = collections.OrderedDict([
    ('fire', ('Grenade\\FX_Grenade_RPG_01', 3, 'fireball 45, smoke 25 (4 s), sparks 100, debris 75 + 75, blast flash, a light that fades in 3 s')),
    ('spray', ('Rocket\\Rocket_Default_01', 4, 'debris 400, sparks 500, fire, a light; a half sphere round local +Y')),
    ('glass', ('Bullet\\Glass_Exit_01', 30, 'glass debris 25 + 25 + 30, glass dust and smoke; a narrow jet along local +Y (small: a bullet\'s exit)')),
    ('dust', ('Bullet\\Concrete_02', 15, 'concrete smoke, debris, pebbles, a puff that stays 6 s (small: a bullet\'s impact)')),
])
# role -> (spare F07 helper box, world position, ZGEOM[1], cluster or None, why there). Every position is a GUESS
# from the window's measured frame; the six boxes are single top-level ZBoxPrimitive nodes of F07's shutter
# script at (10000 0 10000), named by nothing that stays (the script's first timer, the only one F07's AIMonitor
# names, is not among them and is not kept)
SH = 'Gameplay!010_FirstFight!Shutters!'
PLAN = collections.OrderedDict([
    ('fan', (SH + 'Activator_Shutter_LEFT', (GLASS_X, 21150.0, -100.0), UP, None, 'anywhere: it only passes the message on (and jolts the hand-held camera)')),
    ('cloud', (SH + 'Activator_Shutters_RIGHT', (5650.0, 21000.0, 150.0), UP, 'fire', '2 m inside on the floor, north half of the bay (the InvisiBomb is the south half)')),
    ('spray', (SH + 'Activator_Shutter_Close_LEFT', (5800.0, 21150.0, -100.0), OUT, 'spray', 'half a metre inside the glass, middle of the bay, blowing out over the balcony; the shake\'s centre')),
    ('glass s', (SH + 'Activator_Shutter_Close_RIGHT', (GLASS_X, 21300.0, -330.0), OUT, 'glass', 'in the glass, head height, south half')),
    ('glass n', (SH + 'TimerShuttersOpenDif', (GLASS_X, 21300.0, 130.0), OUT, 'glass', 'in the glass, head height, north half')),
    ('second', (SH + 'TimerShuttersClose', (5400.0, 21000.0, -100.0), UP, 'spray', '4.5 m inside on the floor: the pop comes from the room')),
])
SHAKER = 'spray'                        # the box that also carries the ShakeCamera (always on)
SOUNDED = ('cloud', 'second')           # roles whose Explode keeps the rocket's explosion sound (SOUND)
KEEP = tuple(v[0] for v in PLAN.values())
INVISIBOMB = 'WindowBlowup!InvisiBomb'  # campaign, kept by kl_fa_author; fired at the blast through its own wrapper
BOMB = 'WindowBlowup!BombWindow03'
BOMB_REACH, BOMB_F4 = (600.0, 400.0), 3000.0     # the campaign's own values (stock M09_A: 600, 400, 2000, 3000, ...)
BOMB_OWN = R + 'Effects/AllocMany/M09/AllocMany_BigWindow_M09.zip\\Particles_M09_BigWindow'    # ... and its own particle group
# CExplode's fields as kl2 0x60b230 / 0x8fb660 use them (object offsets +0x34.. in declaration order)
E_REACH, E_INNER, E_TINNITUS, E_F4, E_MESSAGE, E_PARTICLES, E_FUSE, E_SOUND_FUSE, E_SOUND = 0, 1, 3, 4, 7, 8, 9, 11, 12
S_STRENGTH, S_MESSAGE, S_AT_START, S_RADIUS = 0, 1, 2, 3
TRIGGER = 'AITrigger'                   # what a TriggerDelay2 sends to its list: the message stock's DocuCamControl, ActivateGeom
                                        # and AIDWrapper wait for (ASSUMPTION by their stored field; kl_fa_author's layer rests on it)
MESSAGE = 'Activate'                    # what the fan sends on: the message of F01's scExplosion and of the campaign's two bombs.
                                        # NOT 'AITrigger' on an Explode: its handler (kl2 0x5589d0) has a second, built-in message
                                        # whose argument it takes for the attacker; which name that is was not found


def second():
    return (0.5 if BLAST >= 1.5 else 0.0) if SECOND is None else SECOND


def active():
    """The boxes the fan names, by the knobs. GUESS, all of it: mild = no second fireball."""
    return [r for r in PLAN if r != 'fan' and not (r == 'cloud' and BLAST < 0.75) and not (r == 'second' and second() <= 0)]


def shake_at(d, strength, radius):
    """Amplitude factor kl2 0x756c20 hands the camera for a 'msgShakeCamera' from d away, as read:
    nothing at or beyond the radius; x = max(d, 500) / 500; factor = strength * x ^ -(ln 10 / ln(radius / 500))
    (so 1 x strength within 5 m, a tenth of it at the radius). The game multiplies by 25 and starts
    the shake d / 7500 + 0.05 s later."""
    if radius < 1.2e-4:
        radius = 4000.0
    if d >= radius:
        return 0.0
    if radius <= 500.0:                                 # the game divides by ln(radius / 500) here; no stock object is that small
        return strength
    return strength * (max(d, 500.0) / 500.0) ** -(math.log(10.0) / math.log(radius / 500.0))


# ------------------------------------------------------------------ small tools
def values(sc, k, name):
    return [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][au.ctrl_of(sc, k, name)][1][1:-1])]


def has(sc, k, name):
    return any(sc.p.key(nm) == name for nm, _b in sc.nodes[k]['ctrls'])


def clusters(sc):
    """{name: scene path} of the systems' clusters, found beside the rocket's own particle group."""
    rk = au.node_of(sc, ROCKET)
    own = values(sc, rk, 'Explode')[E_PARTICLES]
    base = own.rsplit('\\', 2)[0]
    if not own.lower().endswith(CLUSTER['fire'][0].lower()):
        raise ValueError('Rocket_RPG7 names %s, not the cluster this file was written for' % own)
    out = {}
    for name, (sub, _n, _what) in CLUSTER.items():
        hit = sc.resolve(base + '\\' + sub)
        if len(hit) != 1 or sc.cls(hit[0]) != 'ZAllocMany':
            raise ValueError('%s: %d nodes at %s' % (sc.label, len(hit), base + '\\' + sub))
        out[name] = sc.path[hit[0]]
    return out


def place(S, k, pos, m9):
    """kl_fa_author.place with a whole ZGEOM[1] (that one makes turns about Y): .prp and .gms record."""
    sc = S.prp
    lab, e = J.labels('dd', sc.cls(k)), S.ents[k - 1]
    def fn(us):
        au.setv(sc, us, lab.index('ZGEOM[1]'), list(m9))
        au.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
    kl_graft.edit(sc.nodes[k], 'props', fn)
    e.rot = struct.pack('<9f', *m9) + bytes(12)
    e.trans = struct.pack('<3f', *pos) + bytes(4)


def docucam(sc, message, event):
    """A DocuCamControl as stock stores it: { string, enum } (stock F01: 'AITrigger', 'OnExplosion')."""
    return (kl_fa._str(sc, 'DocuCamControl'), [(0x02, b''), kl_fa._str(sc, message), (0x0e, struct.pack('<I', sc.p.key_index(event))), (0x7e, b'')])


def dress(sc):
    """Give the six boxes their controllers and values (by the knobs). Each box ends with exactly
    the controllers of its role; Explode and ShakeCamera are built again from the rocket's tokens
    on every call, the fan keeps the AIDWrapper it has in stock."""
    rk = au.node_of(sc, ROCKET)
    pat = {n: sc.nodes[rk]['ctrls'][au.ctrl_of(sc, rk, n)] for n in ('Explode', 'ShakeCamera')}
    sound = values(sc, rk, 'Explode')[E_SOUND]
    paths = clusters(sc)
    done = {r: au.node_of(sc, v[0]) for r, v in PLAN.items() if sc.resolve(R + v[0])}
    for role, k in done.items():
        cluster = PLAN[role][3]
        if role == 'fan':
            wrap = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) == 'AIDWrapper']
            if len(wrap) != 1:
                raise ValueError('%s: %d AIDWrapper' % (PLAN[role][0], len(wrap)))
            sc.nodes[k]['ctrls'] = [wrap[0], docucam(sc, TRIGGER, 'OnExplosion')]
            def fn(us):
                au.setv(sc, us, 0, [R + PLAN[r][0] for r in active() if r in done])
                au.setv(sc, us, 1, MESSAGE)
                au.setv(sc, us, 2, 0)                   # as the campaign's two wrappers and all 10 of stock F07
            kl_fa.edit(sc, k, 0, fn)
            continue
        cl = cluster if FIRE or cluster != 'fire' else 'dust'
        sc.nodes[k]['ctrls'] = [(pat['Explode'][0], list(pat['Explode'][1]))]
        def fn(us, role=role, cl=cl):
            au.setv(sc, us, E_REACH, 1.0)               # as kl_fa_author makes the bomb harmless (the rocket: 500 / 150)
            au.setv(sc, us, E_INNER, 1.0)
            au.setv(sc, us, E_TINNITUS, 0.0)            # no ear ring from a picture (the rocket: 1000; the bomb keeps its 2000)
            au.setv(sc, us, E_MESSAGE, MESSAGE)
            au.setv(sc, us, E_PARTICLES, paths[cl])
            au.setv(sc, us, E_FUSE, float(second()) if role == 'second' else 0.0)
            au.setv(sc, us, E_SOUND_FUSE, 0)
            au.setv(sc, us, E_SOUND, sound if SOUND and role in SOUNDED else 0)
        kl_fa.edit(sc, k, 0, fn)
        if role == SHAKER:                              # the rocket's idiom: Explode and ShakeCamera on one node, one message
            sc.nodes[k]['ctrls'].append((pat['ShakeCamera'][0], list(pat['ShakeCamera'][1])))
            def fn(us):
                au.setv(sc, us, S_STRENGTH, SHAKE[0] * BLAST)
                au.setv(sc, us, S_MESSAGE, MESSAGE)
                au.setv(sc, us, S_AT_START, 0)          # Subway's has 1: it also shakes when the object starts (kl2 0x48ed30)
                au.setv(sc, us, S_RADIUS, SHAKE[1])
            kl_fa.edit(sc, k, 1, fn)
    return done


def scrub(sc, paths, but=()):
    """Take `paths` out of every reference list and string of the scene, except in the nodes `but`.
    -> [(node, how many)]. A box that became an Explode must not be named by anything of its old job."""
    low, out = {p.lower() for p in paths}, []
    for k in range(1, len(sc.nodes)):
        if k in but:
            continue
        n = sc.nodes[k]
        for i, obj in [(None, n['props'])] + [(i, c[1]) for i, c in enumerate(n['ctrls'])]:
            if not any(op in (0x0c, 0x0f) for op, _pl in obj):
                continue
            us = [list(u) for u in units(obj[1:-1])]
            hits = [j for j, u in enumerate(us) if any(s.lower() in low for s in J.strings(sc, u))]
            if not hits:
                continue
            def fn(us, hits=hits):
                for j in hits:
                    if us[j][0][0] == 0x04:
                        us[j] = kl_fa._refs(sc, [s for s in J.strings(sc, us[j]) if s.lower() not in low])
                    else:
                        us[j] = [kl_fa._str(sc, '')]
            kl_fa.edit(sc, k, i, fn)
            out.append((k, len(hits)))
    return out


# ------------------------------------------------------------------ 1. the host level, before the graft
def prepare_host(S, log=print):
    """Re-place six spare helper boxes of F07 at the window and make them the blast's fan, shake
    and particle spawners. S: kl_graft.Level('F07') AFTER kl_fa_author.prepare_host(S)."""
    sc = S.prp
    if getattr(S, 'blast', None):                       # hook() and the native lines together: once
        return S.blast
    taken = set(au.ROLE.values()) | set(au.PLACE) | set(au.PARKED)
    try:
        import kl_fa_street
        taken |= set(kl_fa_street.KEEP) | {kl_fa_street.DOG_BOX}
    except ImportError:
        pass
    clash = sorted(set(KEEP) & taken)
    if clash:
        raise ValueError('another layer uses boxes this one needs: %s' % clash)
    for role, (name, pos, m9, _cl, _why) in PLAN.items():
        k = au.node_of(sc, name)
        if sc.parent[k] != 0 or sc.end[k] - k != 1 or sc.cls(k) != 'ZBoxPrimitive':
            raise ValueError('%s is not a single top-level ZBoxPrimitive' % name)
        place(S, k, pos, m9)
    done = dress(sc)
    gone = scrub(sc, [R + n for n in KEEP], but={done['fan']})
    S.blast = {'boxes': done, 'scrubbed': gone}
    log('  kl_fa_blast: %d boxes at the window (%s); %d references to their old job removed (%s)' % (
        len(done), ', '.join(done), sum(n for _k, n in gone), ', '.join(sorted({sc.names[sc.top[k]].split('!')[-1] for k, _n in gone})) or '-'))
    return S.blast


# ------------------------------------------------------------------ 2. the joined scene
def wire(sc, log=print):
    """After kl_fa_author.wire(sc): the blast timer also names the fan, the boxes get the knobs'
    values, the InvisiBomb gets a particle group. Idempotent, with any knobs."""
    node = lambda n: au.node_of(sc, n)
    done = dress(sc)
    if 'fan' not in done:
        log('  kl_fa_blast: NOT IN THE LEVEL: %s - nothing wired' % PLAN['fan'][0])
        return {'boxes': done, 'on': [], 'bombs': []}
    fan = R + PLAN['fan'][0]
    t = node(au.ROLE['blast timer'])
    cur = values(sc, t, 'TriggerDelay2')[4]
    if fan.lower() not in [p.lower() for p in cur]:
        kl_fa.edit(sc, t, au.ctrl_of(sc, t, 'TriggerDelay2'), lambda us: au.setv(sc, us, 4, cur + [fan]))
    stray = scrub(sc, [R + n for n in KEEP], but={t, done['fan']})
    if stray:
        log('  kl_fa_blast: %d references to the boxes from elsewhere removed: %s' % (sum(n for _k, n in stray), [sc.path[k] for k, _n in stray][:4]))
    now = [p.lower() for p in values(sc, t, 'TriggerDelay2')[4]]
    if now.count(fan.lower()) != 1 or any((R + PLAN[r][0]).lower() in now for r in PLAN if r != 'fan'):
        raise ValueError('the blast timer must name the fan once and no other box: %s' % now)
    paths = clusters(sc)
    bombs = []
    if sc.resolve(R + INVISIBOMB):
        b = node(INVISIBOMB)
        v = values(sc, b, 'Explode')
        want = paths['fire' if FIRE else 'dust']
        if len(v) != 18 or not (v[E_PARTICLES] == '' or v[E_PARTICLES].lower() in {p.lower() for p in paths.values()}):
            raise ValueError('InvisiBomb: not the Explode this file was written for: %s' % v)
        kl_fa.edit(sc, b, au.ctrl_of(sc, b, 'Explode'), lambda us: au.setv(sc, us, E_PARTICLES, want))
        bombs.append('InvisiBomb -> %s' % want.split('\\')[-1])
    else:
        log('  kl_fa_blast: NOT IN THE LEVEL: %s' % INVISIBOMB)
    if sc.resolve(R + BOMB):
        b = node(BOMB)
        v = values(sc, b, 'Explode')
        group = paths[BOMB_GROUP] if BOMB_GROUP else BOMB_OWN
        if v[E_PARTICLES].lower() != group.lower() and len(sc.resolve(group)) == 1:
            kl_fa.edit(sc, b, au.ctrl_of(sc, b, 'Explode'), lambda us: au.setv(sc, us, E_PARTICLES, sc.path[sc.resolve(group)[0]]))
        if BOMB_GROUP:
            bombs.append('TEST: BombWindow03 -> %s' % group.split('\\')[-1])
        if DAZE:
            def fn(us):
                au.setv(sc, us, E_REACH, BOMB_REACH[0])
                au.setv(sc, us, E_INNER, BOMB_REACH[1])
                au.setv(sc, us, E_F4, 0.0)              # ASSUMPTION: the damage
            kl_fa.edit(sc, b, au.ctrl_of(sc, b, 'Explode'), fn)
            bombs.append('OPTION daze: BombWindow03 reach %g / %g, field 4 = 0' % BOMB_REACH)
        elif v[E_F4] == 0.0:                            # the option was on in an earlier call on this scene: as kl_fa_author leaves it
            def fn(us):
                au.setv(sc, us, E_REACH, 1.0 if au.BLAST_HARMLESS else BOMB_REACH[0])
                au.setv(sc, us, E_INNER, 1.0 if au.BLAST_HARMLESS else BOMB_REACH[1])
                au.setv(sc, us, E_F4, BOMB_F4)
            kl_fa.edit(sc, b, au.ctrl_of(sc, b, 'Explode'), fn)
    far = [math.dist(PLAN[SHAKER][1], p) for p in au.START]
    on = [r for r in active() if r in done]
    log('  kl_fa_blast: blast %.2f: blast timer -> fan -> %d boxes (%s); shake %.2f / %.0f (factor %.2f - %.2f at the START points, '
        'Subway %.2f at its own); second pop %s; %s' % (
            BLAST, len(on), ', '.join(on), SHAKE[0] * BLAST, SHAKE[1],
            shake_at(max(far), SHAKE[0] * BLAST, SHAKE[1]), shake_at(min(far), SHAKE[0] * BLAST, SHAKE[1]), SUBWAY_SHAKE,
            '%.1f s later' % second() if second() > 0 else 'none', '; '.join(bombs) or 'no bomb edited'))
    return {'boxes': done, 'on': on, 'bombs': bombs}


# Subway's shake where its players stand: scExplosion (151 -2556 16286), START points (7..751 -1714 13336..13701)
SUBWAY_SHAKE = shake_at(math.dist((151.0, -2556.0, 16286.0), (379.0, -1714.0, 13518.0)), 3.0, 8000.0)


def hook():
    """Put this layer into kl_fa_author from outside (the three lines of the docstring), once."""
    if getattr(au, '_blast', False):
        return
    au._blast = True
    au.KEEP = tuple(au.KEEP) + tuple(k for k in KEEP if k not in au.KEEP)
    prep, wir = au.prepare_host, au.wire
    def prepare2(S, log=print):
        r = prep(S, log)
        prepare_host(S, log)
        return r
    def wire2(sc, log=print):
        r = wir(sc, log)
        wire(sc, log)
        return r
    au.prepare_host, au.wire = prepare2, wire2


# ------------------------------------------------------------------ reading a built level back
def members(archive):
    import kl_prmgraph as G, kl_texmat as T
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        get = lambda end: zf.read(next(n for n in names if n.lower().endswith(end)))
        return G.read(get('_main.prm'), 'dd'), T.read_tex(get('_main.tex'))


def cluster_parts(sc, path, prm, tex):
    """What a particle group needs to draw, followed into the archive: -> (lines, faults).
    group -> its clone group -> emitters -> template (by name) -> sprite chunk -> texture."""
    import kl_prmgraph as G
    lines, bad = [], []
    hit = sc.resolve(path)
    if len(hit) != 1 or sc.cls(hit[0]) != 'ZAllocMany':
        return lines, ['%s: %d nodes' % (path, len(hit))]
    a = hit[0]
    v = kl_fa.node_values(sc, a)
    group = [g for g in sc.resolve(v[-1]) if sc.parent[g] == 0] if isinstance(v[-1], str) else []
    copies = sum(1 for g in group for c in range(g + 1, sc.end[g]) if sc.parent[c] == g and sc.cls(c) == 'ZAllocMany')
    if not copies:
        bad.append('%s: no clone group %s' % (sc.names[a], v[-1]))
    lines.append('%s: ZAllocMany, %d copies in its clone group (the template says %s)' % (sc.path[a].split('.zip\\')[-1], copies, v[-4]))
    tpl = collections.defaultdict(list)
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZParticleTemplate':
            tpl[sc.names[k].lower()].append(k)
    lab, tl = J.labels('dd', 'ZParticleEmitter'), J.labels('dd', 'ZParticleTemplate')
    for c in range(a + 1, sc.end[a]):
        if sc.cls(c) != 'ZParticleEmitter':
            lines.append('    %-30s %s%s' % (sc.names[c], sc.cls(c), ' + ' + ', '.join(sc.p.key(nm) for nm, _b in sc.nodes[c]['ctrls']) if sc.nodes[c]['ctrls'] else ''))
            continue
        d = dict(zip(lab, kl_fa.node_values(sc, c)))
        name = d['ZParticleEmitter[34]']
        if name.lower() not in tpl:
            bad.append('%s: emitter %s names template %s, which the level lacks' % (sc.names[a], sc.names[c], name))
            continue
        t = dict(zip(tl, kl_fa.node_values(sc, tpl[name.lower()][0])))
        chunk = t['ZGEOM[4]']
        what = 'chunk %d' % chunk
        if not 0 < chunk < len(prm.chunks) or prm.u16(chunk, 2) != 2:
            bad.append('%s: template %s: chunk %d is not a sprite' % (sc.names[a], name, chunk))
        else:
            tid = prm.u32(chunk, 4) % G.SLOTS['dd']
            if tid not in tex.tex:
                bad.append('%s: template %s: texture %d is not in the .TEX' % (sc.names[a], name, tid))
            else:
                what = 'sprite %d -> texture %d %s' % (chunk, tid, tex.tex[tid].name)
        lines.append('    %-30s x%-4d -> template %-34s life %-5.4g size %-5.4g -> %s' % (
            sc.names[c], d['ZParticleEmitter[1]'], name, t['ZParticleTemplate[2]'], t['ZParticleTemplate[4]'], what))
    return lines, bad


def report(archive, log=print):
    """Read the blast back from a built level: objects, what they name, the timeline. -> faults."""
    sc, snd, _loc = kl_fa.load(archive)
    prm, tex = members(archive)
    bad = []
    node = lambda n: au.node_of(sc, n)
    pos = lambda k: tuple(kl_fa.node_values(sc, k)[2])
    log('\nThe window blast in %s' % archive)
    # the chain: monitor -> arm timer -> bomb; -> blast timer -> the rest
    arm, blast = values(sc, node(au.ROLE['arm timer']), 'TriggerDelay2'), values(sc, node(au.ROLE['blast timer']), 'TriggerDelay2')
    mon = next(v for k, _i, v in kl_fa.controllers(sc, 'AIMonitor') if k == node(au.ROLE['monitor']))[2]
    for n in ('arm timer', 'blast timer'):
        if R + au.ROLE[n] not in mon:
            bad.append('the AIMonitor does not name the %s' % n)
    bomb = values(sc, node(BOMB), 'Explode') if sc.resolve(R + BOMB) else None
    t0 = blast[0]
    if bomb and abs(arm[0] + bomb[E_FUSE] - t0) > 1e-3:
        bad.append('the bomb goes off at %.1f s, the blast timer fires at %.1f s' % (arm[0] + bomb[E_FUSE], t0))
    mine = {(R + v[0]).lower(): r for r, v in PLAN.items()}
    fan = node(PLAN['fan'][0]) if sc.resolve(R + PLAN['fan'][0]) else None
    named = set()
    if fan is None:
        bad.append('the fan %s is not in the level' % PLAN['fan'][0])
    else:
        cs = [sc.p.key(nm) for nm, _b in sc.nodes[fan]['ctrls']]
        if cs != ['AIDWrapper', 'DocuCamControl']:
            bad.append('the fan holds %s' % cs)
        else:
            w, d = values(sc, fan, 'AIDWrapper'), values(sc, fan, 'DocuCamControl')
            named = {p.lower() for p in w[0]}
            if w[1] != MESSAGE or w[2] or d != [TRIGGER, 'OnExplosion']:
                bad.append('fan values: %s %s' % (w, d))
            if [p.lower() for p in blast[4]].count(R.lower() + PLAN['fan'][0].lower()) != 1:
                bad.append('the blast timer does not name the fan exactly once')
            for p in w[0]:
                if p.lower() not in mine or mine[p.lower()] == 'fan':
                    bad.append('the fan names %s' % p)
    # who else names the boxes: nobody may
    for k in range(1, len(sc.nodes)):
        for _h, _f, u in J.fields(sc, k):
            for s in J.strings(sc, u):
                if s.lower() in mine and not (k == fan and mine[s.lower()] != 'fan') and not (k == node(au.ROLE['blast timer']) and mine[s.lower()] == 'fan'):
                    bad.append('%s names the box of role %s' % (sc.path[k], mine[s.lower()]))
    rk = node(ROCKET)
    rsound = values(sc, rk, 'Explode')[E_SOUND]
    rows, groups, sounds = [], collections.OrderedDict(), collections.OrderedDict()
    if fan is not None and not bad:
        rows.append((t0, 'fan', True, pos(fan), 'AIDWrapper \'%s\' -> %s; DocuCamControl \'%s\': every local player\'s hand-held camera plays its OnExplosion profile' % (
            MESSAGE, ', '.join(mine[p.lower()] for p in values(sc, fan, 'AIDWrapper')[0]), d[1])))
    for role, (name, _p, _m, _cl, _why) in PLAN.items():
        if role == 'fan':
            continue
        if not sc.resolve(R + name):
            bad.append('role %s: %s is not in the level' % (role, name)); continue
        k = node(name)
        on = (R + name).lower() in named
        cs = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
        if cs != ['Explode'] + ['ShakeCamera'] * (role == SHAKER):
            bad.append('%s box holds %s' % (role, cs)); continue
        v = values(sc, k, 'Explode')
        if v[E_MESSAGE] != MESSAGE or v[E_REACH] > 1.0 or v[E_INNER] > 1.0 or v[E_TINNITUS] > 0:
            bad.append('%s box is not harmless / not on the fan\'s message: %s' % (role, v))
        if v[E_SOUND] not in (0, rsound):
            bad.append('%s box: sound %d is not the rocket\'s (%d)' % (role, v[E_SOUND], rsound))
        if on:
            groups.setdefault(v[E_PARTICLES], []).append(role)
            if v[E_SOUND]:
                sounds.setdefault(v[E_SOUND], []).append(role)
        rows.append((t0 + v[E_FUSE], role, on, pos(k), 'Explode reach %g / %g, fuse %g -> %s%s' % (
            v[E_REACH], v[E_INNER], v[E_FUSE], v[E_PARTICLES].split('\\')[-1], ', the rocket\'s sound' if v[E_SOUND] else '')))
        if role == SHAKER:
            s_ = values(sc, k, 'ShakeCamera')
            if s_[S_MESSAGE] != MESSAGE or s_[S_AT_START]:
                bad.append('shake values: %s' % s_)
            if not on:
                bad.append('the fan does not name the box with the ShakeCamera')
            far = [math.dist(pos(k), p) for p in au.START]
            rows.append((t0, 'shake', on, pos(k), 'ShakeCamera strength %.2f reach %.0f: factor %.2f - %.2f at the START points %.0f - %.0f away (Subway: %.2f at %.0f); lasts 0.8 s' % (
                s_[S_STRENGTH], s_[S_RADIUS], shake_at(max(far), s_[S_STRENGTH], s_[S_RADIUS]), shake_at(min(far), s_[S_STRENGTH], s_[S_RADIUS]), min(far), max(far),
                SUBWAY_SHAKE, math.dist((151.0, -2556.0, 16286.0), (379.0, -1714.0, 13518.0)))))
    if sc.resolve(R + INVISIBOMB):
        k = node(INVISIBOMB)
        v = values(sc, k, 'Explode')
        if v[E_PARTICLES]:
            groups.setdefault(v[E_PARTICLES], []).append('InvisiBomb')
        rows.append((t0, 'InvisiBomb', any(R + 'WindowBlowup!Activator_KillGuyNearWindow' == p for p in blast[4]), pos(k),
                     'campaign Explode reach %g / %g (it kills the guard at the glass) -> %s' % (v[E_REACH], v[E_INNER], v[E_PARTICLES].split('\\')[-1] or 'NO particle group')))
    if bomb:
        groups.setdefault(bomb[E_PARTICLES], []).append('BombWindow03')
        k = node(BOMB)
        rows.append((arm[0] + bomb[E_FUSE], 'bomb', R + au.ROLE['bomb'] in arm[4], pos(k), 'campaign Explode reach %g / %g, tinnitus within %g, fuse %g, hidden %d -> %s; sounds %d (warm-up) + %d' % (
            bomb[E_REACH], bomb[E_INNER], bomb[E_TINNITUS], bomb[E_FUSE], kl_fa.node_values(sc, k)[3], bomb[E_PARTICLES].split('\\')[-1], bomb[E_SOUND_FUSE], bomb[E_SOUND])))
        for o in (bomb[E_SOUND_FUSE], bomb[E_SOUND]):
            sounds.setdefault(o, []).append('BombWindow03')
    # use of each cluster against its pool
    for path, who in groups.items():
        lines, b = cluster_parts(sc, path, prm, tex)
        bad += b
        short = path.split('.zip\\')[-1]
        pool = next((n for _nm, (sub, n, _w) in CLUSTER.items() if path.lower().endswith(sub.lower())), None)
        if pool is not None and len(who) > pool:
            bad.append('%s is asked for %d times at once, its clone group has %d' % (short, len(who), pool))
        log('\n  particle group of %s:' % ', '.join(who))
        for l in lines:
            log('    ' + l)
    log('\n  sounds (offsets into the level\'s .SND, %d bytes):' % (len(snd) if snd else 0))
    for o, who in sounds.items():
        ok = snd is not None and 0 < o < len(snd)
        if not ok:
            bad.append('sound %d of %s is outside the .SND' % (o, who))
        name = ''
        try:
            import kl_snd
            name = kl_snd.Snd('dd', snd).name(o).decode('latin1')
        except Exception:
            pass
        log('    %8d %-40s %s%s' % (o, name, ', '.join(who), '' if o != rsound else '  (= Rocket_RPG7\'s own)'))
    log('\n  the opening, seconds from the round-start event (the countdown\'s first second):')
    log('    %5.1f  %-11s the heisters stand on the balcony; briefing voice at 0.5' % (0.0, ''))
    log('    %5.1f  %-11s GO' % (8.0, ''))
    log('    %5.1f  %-11s the bomb gets \'Activate\': its warm-up sound' % (arm[0], 'arm timer'))
    order = ['bomb', 'InvisiBomb', 'fan', 'shake'] + list(PLAN)
    for t, role, on, p, what in sorted(rows, key=lambda r: (r[0], order.index(r[1]))):
        log('    %5.1f  %-11s %s(%d %d %d) %s' % (t, role, '' if on else 'OFF (nothing names it) ', *p, what))
    rest = [p for p in blast[4] if p.lower() not in mine]
    log('    %5.1f  %-11s and, as before: %s' % (t0, 'blast timer', ', '.join(p.split('\\')[-1].split('!')[-1] for p in rest[:9]) + (' + %d squad routs' % (len(rest) - 9) if len(rest) > 9 else '')))
    if sc.resolve(R + 'WindowBlowup!Timer'):
        log('    %5s  %-11s a pillar comes down %d s after the first heister walks in (campaign, kept)' % ('', '', values(sc, node('WindowBlowup!Timer'), 'TriggerDelay')[0]))
    return bad


# ------------------------------------------------------------------ Subway
def subway(log=print):
    """Stock F01's opening breach, object by object (re/retomoto_blast.md 1)."""
    sc = J.Scene.load('F01')
    pos = lambda k: tuple(round(x) for x in kl_fa.node_values(sc, k)[2])
    wpos = lambda k: tuple(round(sum(kl_fa.node_values(sc, j)[2][i] for j in chain(k))) for i in range(3))
    def chain(k):
        while k > 0:
            yield k
            k = sc.parent[k]
    log('Stock F01 (Subway): Gameplay!Blowout! and what it names')
    for t in sc.tops():
        n = sc.names[t]
        if n == 'Gameplay!AIMonitor' or n.startswith('Gameplay!Blowout!'):
            for nm, body in sc.nodes[t]['ctrls']:
                v = [kl_fa.value(sc, u) for u in units(body[1:-1])]
                short = [[s.split('\\')[-1] for s in x] if isinstance(x, list) and x and isinstance(x[0], str) else x for x in v]
                log('  %-46s at %-22s %-16s %s' % (n.split('!')[-1], pos(t), sc.p.key(nm), str(short)[:400]))
    lab, tl = J.labels('dd', 'ZParticleEmitter'), J.labels('dd', 'ZParticleTemplate')
    tpl = {sc.names[k]: k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZParticleTemplate'}
    log('emitters (world positions = parent group + own; identity rotations):')
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZParticleEmitter' and sc.names[k].startswith('BlowOut_Emitter'):
            d = dict(zip(lab, kl_fa.node_values(sc, k)))
            t = dict(zip(tl, kl_fa.node_values(sc, tpl[d['ZParticleEmitter[34]']])))
            log('  %-26s at %-20s box %s, every %.4g s for %.3g s, speed %s cone %.3g -> template %s (life %.3g s, size %.4g; in %s)' % (
                sc.names[k], wpos(k), d['ZParticleEmitter[0]'], d['ZParticleEmitter[3]'], d['ZParticleEmitter[4]'], d['ZParticleEmitter[21]'], d['ZParticleEmitter[6]'],
                d['ZParticleEmitter[34]'], t['ZParticleTemplate[2]'], t['ZParticleTemplate[4]'], sc.path[sc.parent[tpl[d['ZParticleEmitter[34]']]]].split('\\', 1)[1]))
    for k in range(1, len(sc.nodes)):
        if 'Wall_Explosion_Sound' in sc.names[k] or sc.names[k] in ('Flash_FX', 'BombFlash'):
            log('  %-34s %-12s at %-22s hidden %d  %s' % (sc.names[k], sc.cls(k), wpos(k), kl_fa.node_values(sc, k)[3], ', '.join(sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls'])))
    start = [pos(t) for t in sc.tops() if sc.cls(t) == 'ZSpawnPoint' and kl_fa.node_values(sc, t)[8] == 'eSPAWN_TYPE_FRAGILE_ALLIANCE_START']
    log('START points: %s' % start)
    f7 = J.Scene.load('F07')
    have = {f7.names[k] for k in range(1, len(f7.nodes)) if f7.cls(k) == 'ZParticleTemplate'}
    log('in host F07: BlowOut_01 %s, BlowOut_02 %s; DocuCamControl %d, ShakeCamera %d (both on rocket templates); loose emitters outside its map, vans and systems: %d' % (
        'BlowOut_01' in have, 'BlowOut_02' in have, len(kl_fa.controllers(f7, 'DocuCamControl')), len(kl_fa.controllers(f7, 'ShakeCamera')),
        sum(1 for k in range(1, len(f7.nodes)) if f7.cls(k) == 'ZParticleEmitter' and J.family(f7.names[f7.top[k]]) not in
            ('Locations/*', 'Animation/*', 'CloneGroup_Effects', 'AllLevels/mainsceneincludes_multiplayer.zip'))))
    return 0


def selftest(log=print):
    """The controllers this file writes against stock ones, as token text (kl_prpjoin.text):
    a ShakeCamera set to Subway's values = stock F01's scExplosion; the DocuCamControl = stock F01's
    DocuCam_Explotion; a spawner's Explode fits CExplode and differs from the rocket's in the eight
    fields dress() sets. And dress() twice = dress() once."""
    f1, f7 = J.Scene.load('F01'), J.Scene.load('F07')
    bad = []
    k = au.node_of(f1, 'Gameplay!Blowout!DocuCam_Explotion')
    if J.text(f1, [docucam(f1, 'AITrigger', 'OnExplosion')[0]] + docucam(f1, 'AITrigger', 'OnExplosion')[1]) != J.text(f1, [f1.nodes[k]['ctrls'][0][0]] + f1.nodes[k]['ctrls'][0][1]):
        bad.append('DocuCamControl tokens differ from stock F01 DocuCam_Explotion')
    global BLAST, SHAKE
    keep = BLAST, SHAKE
    BLAST, SHAKE = 1.0, (3.0, 8000.0)
    try:
        dress(f7)
        a = [J.text(f7, [c[0]] + c[1]) for v in PLAN.values() for c in f7.nodes[au.node_of(f7, v[0])]['ctrls']]
        dress(f7)
        if a != [J.text(f7, [c[0]] + c[1]) for v in PLAN.values() for c in f7.nodes[au.node_of(f7, v[0])]['ctrls']]:
            bad.append('dress() is not idempotent')
    finally:
        BLAST, SHAKE = keep
    sk = au.node_of(f7, PLAN[SHAKER][0])
    sx = au.node_of(f1, 'Gameplay!Blowout!scExplosion')
    mine, stock = values(f7, sk, 'ShakeCamera'), values(f1, sx, 'ShakeCamera')
    if [mine[0], mine[1], mine[3]] != [stock[0], stock[1], stock[3]] or [op for op, _p in f7.nodes[sk]['ctrls'][1][1]] != [op for op, _p in f1.nodes[sx]['ctrls'][0][1]]:
        bad.append('ShakeCamera %s is not stock scExplosion %s' % (mine, stock))
    fk = au.node_of(f7, PLAN['fan'][0])
    if J.text(f7, [f7.nodes[fk]['ctrls'][1][0]] + f7.nodes[fk]['ctrls'][1][1]) != J.text(f1, [f1.nodes[k]['ctrls'][0][0]] + f1.nodes[k]['ctrls'][0][1]):
        bad.append('the fan\'s DocuCamControl is not stock F01 DocuCam_Explotion')
    rv = values(f7, au.node_of(f7, ROCKET), 'Explode')
    sch = J.schema('dd')
    for role, (name, *_x) in PLAN.items():
        k = au.node_of(f7, name)
        for nm, body in f7.nodes[k]['ctrls']:
            why = sch.misfit(sch.controller(f7.p.key(nm), f7.cls(k)), body)
            if why:
                bad.append('%s: %s does not fit its class: %s' % (role, f7.p.key(nm), why))
        if role != 'fan':
            v = values(f7, k, 'Explode')
            diff = [i for i in range(18) if v[i] != rv[i]]
            if not set(diff) <= {E_REACH, E_INNER, E_TINNITUS, E_MESSAGE, E_PARTICLES, E_FUSE, E_SOUND_FUSE, E_SOUND}:
                bad.append('%s: Explode differs from the rocket in fields %s' % (role, diff))
            log('  %-8s Explode %s' % (role, [x.split('\\')[-1] if isinstance(x, str) else x for x in v]))
    log('  %-8s ShakeCamera %s (stock F01 scExplosion: %s)' % (SHAKER, mine, stock))
    log('  %-8s AIDWrapper %s, DocuCamControl %s' % ('fan', [[x.split('!')[-1] for x in y] if isinstance(y, list) else y for y in values(f7, fk, 'AIDWrapper')], values(f7, fk, 'DocuCamControl')))
    log('  rocket   Explode %s' % [x.split('\\')[-1] if isinstance(x, str) else x for x in rv])
    for b in bad:
        log('FAULT ' + b)
    log('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    return 1 if bad else 0


def test(out, keep=False, log=print):
    import kl_fa_street as st
    work = os.path.normcase(os.path.abspath(kl_graft.out_dir('F01')))
    dd = os.path.normcase(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(J.level_zip('F02')))))))
    o = os.path.normcase(os.path.abspath(out))
    if o.startswith(dd) or o.startswith(work):
        log('refused: %s is the game\'s folder or the work folder\'s install' % out)
        return 1
    st.hook()
    hook()
    r = kl_maps.chain(out, au.HOST, au.PART_B, au.PART_A, campaign=True, heroes=False, keep=True, author=True)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    folder = os.path.join(out, 'R09+%s%s' % (au.PART_A, r['tag']))
    archive = os.path.join(folder, kl_maps.SLOT + '_Main.zip')
    late = [p for fn in au.FINISH for p in fn(folder, log)]         # kl_fa_loot: the loot's props, on the written level
    bad = report(archive, log) + ['kl_fa_loot: ' + p for p in late]
    street = st.report(archive, lambda *_a: None)       # the street layer must read back as without this file
    known = au.KNOWN + (('no ZSquadScript: no police',) if au.NO_AI and not st.POLICE else ())
    mine = [p for p in r['problems'] if not any(k in p for k in known)]
    fa = [f for f in r['fa_findings'] if f.startswith(('CRASH', 'BROKEN')) and not any(k in f for k in known)]
    log('\nkl_graft.verify: %d problems, %d of them not known' % (len(r['problems']), len(mine)))
    for p in r['problems']:
        log('  %s %s' % ('known ' if p not in mine else 'OPEN  ', p[:230]))
    log('kl_fa.check: %s' % r['fa'])
    for f in r['fa_findings']:
        log('  ' + f[:230])
    log('kl_fa_street.report: %d faults' % len(street))
    for b in street:
        log('  FAULT ' + b[:300])
    log('kl_fa_blast: %d faults' % len(bad))
    for b in bad:
        log('  FAULT ' + b[:300])
    log('level: %d entities, %d rooms, %.0f MB; kept in %s' % (r['entities'], r['rooms'], r['archive_mb'], folder if keep else '(removed)'))
    if not keep:
        for d in (folder, os.path.join(out, 'chain', '%s+%s' % (au.HOST, au.PART_B))):
            for f in os.listdir(d):
                if '_Main' in f:
                    os.remove(os.path.join(d, f))
    ok = not mine and not fa and not bad and not street
    log('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


def main():
    global BLAST, SECOND, FIRE, SOUND, DAZE, BOMB_GROUP
    a = sys.argv[1:]
    def opt(name):
        if name in a:
            i = a.index(name)
            v = float(a[i + 1])
            del a[i:i + 2]
            return v
    b, s = opt('--blast'), opt('--blast-second')
    BLAST = BLAST if b is None else b
    SECOND = SECOND if s is None else s
    FIRE = '--blast-no-fire' not in a
    SOUND = '--blast-quiet' not in a
    DAZE = '--blast-daze' in a
    BOMB_GROUP = 'spray' if '--blast-bomb-native' in a else None
    au.BLAST_HARMLESS = '--blast-real' not in a
    au.NO_AI = '--no-ai' in a
    if '--loot-bags' not in a and a[:1] == ['test']:    # the loot's props and places (re/retomoto_loot.md)
        import kl_fa_loot
        a = kl_fa_loot.options(a)
        kl_fa_loot.hook()
    a = [x for x in a if not x.startswith('--') or x == '--keep']
    if len(a) >= 2 and a[0] == 'test':
        sys.exit(test(a[1], '--keep' in a))
    elif len(a) == 2 and a[0] == 'report':
        bad = report(a[1])
        for x in bad:
            print('FAULT ' + x)
        sys.exit(1 if bad else 0)
    elif a == ['subway']:
        sys.exit(subway())
    elif a == ['selftest']:
        sys.exit(selftest())
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_blast                  # one module: kl_fa_author is imported once, hook() patches that one
    kl_fa_blast.main()
