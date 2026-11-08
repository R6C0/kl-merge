"""kl_hasta_blast_1108.py - OPT-IN post-pass for Hasta (DM11B, slot F04): a real blast where the loot-wing barricade goes.
Reads a BUILT F04_Main.zip (the kl_hasta_vault_1108 output), writes a copy. Rerunnable (same bytes on its own output). Nothing imports it.
Written 2026-11-08 after the owner: "the loot room u can go in but the explosion doesnt open it up its weird".

THE GAP (PROVEN offline): at the beat (TriggerCounter 2 dead squads, or the 30 s backstop -> the two campaign timers) the barricade is swapped
(DeactivateGeom Roadblock_01 / BarricadeB_01 / OYCHECK_BEFORE01, ActivateGeom of the remains, 18 dust emitters) but nothing explodes: the campaign's BoomBoxDust
is an Explode with an EMPTY effect name and was dropped. No sound, no shake, no fireball.

WHAT THIS ADDS (no new entity, nothing renumbered: .oct / .rmi / .rmc and every slot id are untouched)
  ONE spare box is re-used: F07's 'Gameplay!010_FirstFight!Shutters!TimerShuttersClose', the corner blast's 'second' role (an Explode that SECOND = 0 leaves OFF: nothing
  names it). It is the rocket's own pair of controllers cloned token for token (what kl_fa_hasta_blast.dress does for the corner boxes):
    Explode      both radii 1 cm, tinnitus 0, fuse 0, particle group = the systems' FX_Grenade_RPG_01 cluster (fireball, smoke, sparks, debris, flash light),
                 sound = the rocket's explosion sound, message 'AITrigger'
    ShakeCamera  strength 3.0 (stock F01's scExplosion), message 'AITrigger', not at start, reach 8000 (distance-weighted: the nearer the player the harder)
  placed on the barricade (WORLD 26409, 920, 14031 = the Broken01 node's place 38697, 800, 30415 in the map frame + the Locations group's (-12288, 0, -16384), 1.2 m up), identity matrix, .prp ZGEOM[1]/[2] and the .gms record both.
  HOOK: the box is appended to the event list of the campaign's Timer_SandbagsDeactive (the 1 s timer that swaps the wall), which sends 'AITrigger' like it does to
  the geom switches. No new trigger, no new chain: the beat that opens the wing is the beat that blows it. Same instant as the swap, so boom + shake + wreck together.
  PURELY COSMETIC: radii 1 cm (nobody stands within 1 cm of the box centre inside a wall), tinnitus 0, same harmless settings as the corner boxes (re/retomoto_blast.md).
  No DocuCamControl (it jolts every local player's camera whatever the distance; the beat can be 40 m away): ShakeCamera is distance-weighted.

GUESSES (no live run): that Explode / ShakeCamera answer a 'AITrigger' sent straight by a TriggerDelay (stock F01 does it for DocuCamControl; the corner blast goes
through an AIDWrapper 'Activate' instead); that a controller-only box moved without an .oct / .rmi edit still updates (the corner boxes are moved the same way);
that the fireball (grenade FX) reads well in a hall. --message Activate leaves the box on the stock 'Activate' (then it needs a wrapper: NOT wired by this tool).
--no-blast: writes the input back unchanged (a rebuild without the blast).
KIT: python kl_hasta_blast_1108.py --kit <base dir (the hastavault stage)> <out dir>   writes both zips, base md5, KLGuns.ini, install.py / UNDO.bat (backups
*.before-hastablast1108).
Usage (from tools/):  python kl_hasta_blast_1108.py <in F04_Main.zip> <out F04_Main.zip> [--no-blast] [--force]
                      python kl_hasta_blast_1108.py --check <F04_Main.zip>
"""
import hashlib, math, os, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_scene, kl_gms, kl_prpjoin as J, kl_fa_author as A, kl_fa_blast as B, kl_fa_hasta_layer as H, kl_fa_hasta_blast as HB

# the hastavault stage's output: plain zip bf774c69, bots zip 530c7e7d (the two inputs); the outputs of this pass are added below once built
KNOWN_INPUT_MD5 = {'bf774c69890baa15cb43c8d84d6619dc', '530c7e7d98a713030845d13df0a2c56e'}
KNOWN_OUTPUT_MD5 = {'d98d60f7ec6bb3305596e04643b53090', '5968f07dcedf7476206f55860e865b63'}
R = 'ROOT\\'
BOX = HB.SH + 'TimerShuttersClose'               # the corner blast's 'second' box (Explode only, named by nothing)
TIMER = H.SAND_TIMER                             # the 1 s campaign timer that swaps the wall
WALL_LEAF = 'SI0100_M11_BarricadeB_Broken01'     # the wall's place is read from this node, in WORLD terms (the M11B_Locations group sits at (-12288, 0, -16384))
UP_Y = 120.0                                     # 1.2 m above the floor. GUESS
MSG = 'AITrigger'                                # what a TriggerDelay sends (B.TRIGGER)
STRENGTH = 3.0                                   # stock F01 scExplosion (B.SHAKE)
MAP_SHIFT = (-12288.0, 0.0, -16384.0)            # M11B_Locations group offset (MEASURED, read back by world_place); HB._starts() is in the map's own frame


def world_place(sc, k):
    """World position of node k: its own ZGEOM[2] plus every ancestor's; refuses a turned ancestor."""
    tot, c = [0.0, 0.0, 0.0], k
    while c > 0:
        lab = J.labels('dd', sc.cls(c))
        v = kl_fa.node_values(sc, c)
        if c != k and max(abs(a - b) for a, b in zip(v[lab.index('ZGEOM[1]')], B.UP)) > 1e-4:
            raise ValueError('%s: an ancestor is turned' % sc.names[c])
        tot = [a + float(b) for a, b in zip(tot, v[lab.index('ZGEOM[2]')])]
        c = sc.parent[c]
    return tuple(tot)


def target(sc):
    ks = [k for k in range(1, len(sc.names)) if sc.names[k] == WALL_LEAF]
    if len(ks) != 1:
        raise ValueError('expected one %s, found %d' % (WALL_LEAF, len(ks)))
    w = world_place(sc, ks[0])
    return (w[0], w[1] + UP_Y, w[2])


def spawns():
    return [tuple(a + b for a, b in zip(p, MAP_SHIFT)) for p in HB._starts()]


def md5(b):
    return hashlib.md5(b).hexdigest()


def _timer_ctrl(sc, k):
    return A.ctrl_of(sc, k, 'TriggerDelay')


def dress(sc, k, message=MSG, log=print):
    """Box k: exactly Explode + ShakeCamera, built again from the rocket's tokens (idempotent)."""
    rk = A.node_of(sc, B.ROCKET)
    pat = {n: sc.nodes[rk]['ctrls'][A.ctrl_of(sc, rk, n)] for n in ('Explode', 'ShakeCamera')}
    sound = B.values(sc, rk, 'Explode')[B.E_SOUND]
    fire = B.clusters(sc)['fire']
    sc.nodes[k]['ctrls'] = [(pat['Explode'][0], list(pat['Explode'][1])), (pat['ShakeCamera'][0], list(pat['ShakeCamera'][1]))]
    def ex(us):
        A.setv(sc, us, B.E_REACH, 1.0)
        A.setv(sc, us, B.E_INNER, 1.0)
        A.setv(sc, us, B.E_TINNITUS, 0.0)
        A.setv(sc, us, B.E_MESSAGE, message)
        A.setv(sc, us, B.E_PARTICLES, fire)
        A.setv(sc, us, B.E_FUSE, 0.0)
        A.setv(sc, us, B.E_SOUND_FUSE, 0)
        A.setv(sc, us, B.E_SOUND, sound)
    kl_fa.edit(sc, k, 0, ex)
    def sh(us):
        A.setv(sc, us, B.S_STRENGTH, STRENGTH)
        A.setv(sc, us, B.S_MESSAGE, message)
        A.setv(sc, us, B.S_AT_START, 0)
        A.setv(sc, us, B.S_RADIUS, B.SHAKE[1])
    kl_fa.edit(sc, k, 1, sh)
    log('  box %s: Explode (fire cluster + rocket sound %d, radii 1, tinnitus 0) + ShakeCamera %.1f / %.0f, message %s' % (sc.names[k], sound, STRENGTH, B.SHAKE[1], message))
    return sound


def move(sc, scene, k, pos, log=print):
    """.prp ZGEOM[1] (identity) / [2] and the .gms record, as kl_fa_blast.place does."""
    lab = J.labels('dd', sc.cls(k))
    old = tuple(kl_fa.node_values(sc, k)[lab.index('ZGEOM[2]')])
    def fn(us):
        A.setv(sc, us, lab.index('ZGEOM[1]'), list(B.UP))
        A.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in pos])
    kl_fa.edit(sc, k, None, fn)
    e = list(scene.entities())[k - 1]
    e.rot = struct.pack('<9f', *B.UP) + bytes(12)
    e.trans = struct.pack('<3f', *pos) + bytes(4)
    log('  box moved (%d %d %d) -> (%d %d %d)' % (*old, *pos))


def hook(sc, log=print):
    """Append the box to the campaign timer's event list (once)."""
    kt = A.node_of(sc, TIMER)
    cur = list(B.values(sc, kt, 'TriggerDelay')[4])
    me = R + BOX
    if me.lower() in [c.lower() for c in cur]:
        return False
    kl_fa.edit(sc, kt, _timer_ctrl(sc, kt), lambda us: A.setv(sc, us, 4, cur + [me]))
    log('  %s event list: +%s' % (TIMER.split('!')[-1], BOX.split('!')[-1]))
    return True


def apply(sc, scene, message=MSG, log=print):
    k = A.node_of(sc, BOX)
    if sc.parent[k] != 0 or sc.end[k] - k != 1 or sc.cls(k) != 'ZBoxPrimitive':
        raise ValueError('%s is not a single top-level ZBoxPrimitive' % BOX)
    others = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) not in ('Explode', 'ShakeCamera')]
    if others:
        raise ValueError('%s holds %s: not the spare box this pass expects' % (BOX, [sc.p.key(c[0]) for c in others]))
    # nothing else may name the box (but the timer, after this)
    me = (R + BOX).lower()
    for j in range(1, len(sc.nodes)):
        if j == A.node_of(sc, TIMER):
            continue
        for _h, _f, u in J.fields(sc, j):
            if any(s.lower() == me for s in J.strings(sc, u)):
                raise ValueError('%s is named by %s: not free' % (BOX, sc.path[j][-70:]))
    dress(sc, k, message, log)
    move(sc, scene, k, target(sc), log)
    hook(sc, log)
    return k


def run(src, dst, force=False, blast=True, message=MSG, log=print):
    raw = open(src, 'rb').read()
    if md5(raw) not in KNOWN_INPUT_MD5 | KNOWN_OUTPUT_MD5 and not force:
        raise ValueError('kl_hasta_blast_1108: %s md5 %s is not a known Hasta input (use --force)' % (src, md5(raw)))
    if not blast:
        shutil.copyfile(src, dst)
        log('kl_hasta_blast_1108: --no-blast: %s copied unchanged, md5 %s' % (dst, md5(raw)))
        return dst
    sc, _, _ = kl_fa.load(src)
    zf = zipfile.ZipFile(src)
    names = zf.namelist()
    pn = [n for n in names if n.lower().endswith('_main.prp')][0]
    gn, bn = pn[:-4] + '.gms', pn[:-4] + '.buf'
    scene = kl_scene.read(zf)
    apply(sc, scene, message, log)
    g, b = scene.write()
    new = {pn: sc.p.serialize(), gn: kl_gms.pack(g)}
    if b != zf.read(bn):
        new[bn] = b
    members = [(n, new[n] if n in new else zf.read(n)) for n in names]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    log('kl_hasta_blast_1108: wrote %s md5 %s' % (dst, md5(open(dst, 'rb').read())))
    return dst


def check(path, log=print):
    """-> [faults] for a built F04_Main.zip carrying the blast."""
    sc, snd, _ = kl_fa.load(path)
    bad = []
    k = A.node_of(sc, BOX)
    cs = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
    if cs != ['Explode', 'ShakeCamera']:
        return ['box holds %s' % cs]
    v, s = B.values(sc, k, 'Explode'), B.values(sc, k, 'ShakeCamera')
    rk = A.node_of(sc, B.ROCKET)
    rsound = B.values(sc, rk, 'Explode')[B.E_SOUND]
    if v[B.E_REACH] > 1.0 or v[B.E_INNER] > 1.0 or v[B.E_TINNITUS] > 0:
        bad.append('not harmless: %s' % v)
    if v[B.E_MESSAGE] != s[B.S_MESSAGE]:
        bad.append('Explode message %r != ShakeCamera message %r' % (v[B.E_MESSAGE], s[B.S_MESSAGE]))
    if v[B.E_SOUND] != rsound or not (snd is not None and 0 < rsound < len(snd)):
        bad.append('sound %d is not the rocket\'s %d or outside the .SND' % (v[B.E_SOUND], rsound))
    if v[B.E_PARTICLES] != B.clusters(sc)['fire']:
        bad.append('particle group %s' % v[B.E_PARTICLES])
    if s[B.S_AT_START]:
        bad.append('shake at start')
    pos = tuple(kl_fa.node_values(sc, k)[J.labels('dd', sc.cls(k)).index('ZGEOM[2]')])
    if math.dist(pos, target(sc)) > 1.0:
        bad.append('box at %s, planned %s' % (pos, target(sc)))
    sc2 = kl_scene.read(zipfile.ZipFile(path))
    gp = struct.unpack_from('<3f', list(sc2.entities())[k - 1].trans, 0)
    if math.dist(gp, pos) > 0.5:
        bad.append('.gms place %s differs from the .prp place %s' % (gp, pos))
    kt = A.node_of(sc, TIMER)
    tl = [c.lower() for c in B.values(sc, kt, 'TriggerDelay')[4]]
    if (R + BOX).lower() not in tl:
        bad.append('the timer does not name the box: %s' % tl)
    # the campaign's own chain must be intact
    for n in H.SHOW_NODES[:2] + (H.OPENER, H.COUNTER):
        if not sc.resolve(R + n):
            bad.append('missing %s' % n)
    if len(B.values(sc, kt, 'TriggerDelay')[4]) != 4:
        bad.append('timer list size %d (3 campaign + the box)' % len(B.values(sc, kt, 'TriggerDelay')[4]))
    far = [math.dist(target(sc), p) for p in spawns()]
    log('  shake factor %.2f - %.2f at the START rows %d - %d cm away (Subway %.2f)' % (
        B.shake_at(max(far), s[B.S_STRENGTH], s[B.S_RADIUS]), B.shake_at(min(far), s[B.S_STRENGTH], s[B.S_RADIUS]), min(far), max(far), B.SUBWAY_SHAKE))
    log('  timeline: beat -> TriggerDelay %.1f s -> %s: Explode fuse %.1f + shake, sound %d' % (B.values(sc, kt, 'TriggerDelay')[0], BOX.split('!')[-1], v[B.E_FUSE], v[B.E_SOUND]))
    return bad


def kit(base, out, log=print):
    import re
    NL, CR = chr(10), chr(13)
    os.makedirs(out, exist_ok=True)
    for n in ('F04_Main.zip', 'F04_Main.bots.zip'):
        run(os.path.join(base, n), os.path.join(out, n), False, True, MSG, log)
    open(os.path.join(out, 'F04_Main.bots.base.md5'), 'w').write(md5(open(os.path.join(out, 'F04_Main.zip'), 'rb').read()) + NL)
    shutil.copy2(os.path.join(base, 'KLGuns.ini'), os.path.join(out, 'KLGuns.ini'))
    files = [(n, md5(open(os.path.join(base, n), 'rb').read()), md5(open(os.path.join(out, n), 'rb').read()))
             for n in ('F04_Main.zip', 'F04_Main.bots.zip', 'F04_Main.bots.base.md5', 'KLGuns.ini')]
    t = open(os.path.join(base, 'install.py'), encoding='utf-8').read()
    rows = NL.join('    (%r, %r, %r),' % f for f in files)
    t = re.sub(r'FILES = \[.*?' + NL + r'\]' + NL, lambda m: 'FILES = [   # name, md5 before (the hastavault_1108 output), md5 after' + NL + rows + NL + ']' + NL, t, flags=re.S)
    t = t.replace('.before-hastavault1108', '.before-hastablast1108').replace('HASTAVAULT1108 (tools/kl_hasta_vault_1108.py)', 'HASTABLAST1108 (tools/kl_hasta_blast_1108.py)')
    t = t.replace('the hastalook_1108 output', 'the hastavault_1108 output')
    t = re.sub(r"LIVE_ZIP_MD5 = '[0-9a-f]+'", "LIVE_ZIP_MD5 = '%s'" % files[0][1], t)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=NL).write(t)
    open(os.path.join(out, 'UNDO.bat'), 'w', newline=CR + NL).write('@echo off' + CR + NL + 'python "%~dp0install.py" --undo %*' + CR + NL + 'pause' + CR + NL)
    for f in files:
        log('  %-24s %s -> %s' % f)


def main():
    argv = sys.argv[1:]
    a = [x for x in argv if not x.startswith('--')]
    if '--check' in argv and len(a) == 1:
        bad = check(a[0])
        for b in bad:
            print('  FAIL: ' + b)
        print('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
        return 1 if bad else 0
    if '--kit' in argv and len(a) == 2:
        kit(a[0], a[1])
        return 0
    if len(a) != 2:
        print(__doc__)
        return 2
    msg = argv[argv.index('--message') + 1] if '--message' in argv else MSG
    if '--message' in argv:
        a = [x for x in a if x != msg]
    run(a[0], a[1], '--force' in argv, '--no-blast' not in argv, msg)
    return 0


if __name__ == '__main__':
    sys.exit(main())
