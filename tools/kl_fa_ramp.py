"""kl_fa_ramp.py - the AI heisters' way UP a floor of a finished Fragile Alliance build (new, default off, nothing runs it).

Made for Last Call (DM05A, slot F01) after kl-merge-3f's live runs L2 / L2b (night 2026-10-18): the squads' steps
035_DefendBehaviour_out_lounge (floor y 460) -> 036_DefendBehaviour_out_third (floor y 860) never completed; bot record 1
stood on the y 460 floor. STATIC FINDINGS (build/club_civs4/DM05A, md5 6c092deb):
  * the navigation mesh DOES connect the floors: one ramp polygon (963) (-2589,860,-265) (-3789,460,-265) (-3789,460,-147)
    (-2589,860,-147), slope 0.33, and tools/kl_route.py walks it FREE. So "no connection" is not the cause.
  * but the places sit one above the other: Squad#02's 035 is at (-2245,460,40), its 036 at (-2275,860,-14), 60 apart in x/z
    and 400 up; the mesh way between them is 3670 long (4500 .. 5000 for the other squads), through a y 460 corridor
    (polygons 979 / 973 / 964 / 1012) that is only about 30 wide, with no step of the chain on the way. Whether the game's
    path search gives up on a goal stacked over the bot (it may test arrival or the polygon in x/z only) or on the 30-wide
    corridor is NOT known: both would leave the bot at y 460 beside a goal it is "near" - GUESS, the live run decides.
  * RestlessSnap refuses dy > 300 (klmove.c), so it cannot cover this.
WHAT THIS DOES (ini only, no .prp / .gms / .prm / .oct change, so the KLGuns / KLJoin Entries and every archive member stay):
a [CrewHop] section in the build's KLJoin.ini (klhop.c: an AI heister that has been at From for Wait seconds at heist stage
>= Stage is put on the next free To.n by the game's own actor teleport 0x62a900 and ordered to its place there). From =
the middle of the lower floor's step places, Radius covers them, Height keeps it to that floor; To = the upper floor's
step places themselves. klhop.c is built behind KLHook.ini [CrewHop] Enable=1 (off in the repo's KLHook.ini): kl-merge-3f
must switch it on for the live run. It is NEVER written unless this tool is called with --write.

  python tools/kl_fa_ramp.py find   <folder> <slot>                      list the lifts (a step place and the next one 300+ above it)
  python tools/kl_fa_ramp.py build  <folder> <slot> <dst> [--wait S] [--min-dy N] [--from-y LO HI]
                                  [--replace] [--hop-radius R]   (new; --replace rewrites a [CrewHop] the source already has)

Everything chosen here that the game has not shown is marked GUESS."""
import os, sys, math, shutil, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa_bots as F
import kl_fa_bots_dyn as D

MIN_DY = 300.0          # a step place and the next one at least this far UP (RestlessSnap refuses more than 300)
FROM_Y = (400.0, 520.0)  # GUESS: the y 460 floor of Last Call (the lifts of other floors are listed by `find`, not hopped)
WAIT = 25.0             # GUESS: s at From before the hop. A bot that walks to the ramp leaves a 1300 radius in about 4 s and a
                        # lounge hold is a few seconds, so 25 s only catches a bot that did not go
HEIGHT = 80.0           # above / below From (the floors are 400 apart)
RADIUS_PAD = 150.0
APART = 120.0           # klhop.c drops a landing place nearer than 100 to an earlier one
STAGE = 2


def lifts(B, min_dy=MIN_DY):
    """-> [dict]: per squad, the consecutive DefendBehaviourRout steps where the next place is min_dy or more above the
    last place of the step before it and the mesh way is longer than 3 times the x/z distance."""
    nav = F.Nav(B.scene.nav)
    out, seen = [], set()
    for sq, gg in D.graph(B).items():
        for sets in gg['sets']:
            for chain in sets:
                prev = None
                for it in chain:
                    if it['ctrl'] != 'DefendBehaviourRout':
                        continue
                    pl = [B.at(k) for k in it['places']]
                    if prev is not None:
                        a, b = prev, pl[0]
                        h = math.hypot(a[0] - b[0], a[2] - b[2])
                        if b[1] - a[1] >= min_dy:
                            pa, pb = nav.at(*a, dy=200), nav.at(*b, dy=200)
                            L = None
                            if pa and pb:
                                r = nav.path((a[0], pa[1], a[2], pa[0]), (b[0], pb[1], b[2], pb[0]))
                                L = r[1] if r else None
                            key = (sq, it['name'], tuple(round(v) for v in a), tuple(round(v) for v in b))
                            if key not in seen:
                                seen.add(key)
                                out.append(dict(squad=sq, step=it['name'], frm=tuple(a), to=tuple(b), dy=b[1] - a[1], h=h, path=L))
                    prev = pl[-1]
    return out


def plan(B, min_dy=MIN_DY, from_y=FROM_Y, wait=WAIT, log=print, radius=None):
    """-> [hop dicts] for kl_fa_bots.hop_text (one section: every lift that starts on the floor from_y)."""
    ls = [l for l in lifts(B, min_dy) if from_y[0] <= l['frm'][1] <= from_y[1] and (l['path'] is None or l['path'] > 3.0 * max(l['h'], 100.0))]
    if not ls:
        return []
    fr = [l['frm'] for l in ls]
    c = tuple(sum(p[i] for p in fr) / len(fr) for i in range(3))
    rad = max(math.hypot(p[0] - c[0], p[2] - c[2]) for p in fr) + RADIUS_PAD
    if radius is not None:                               # --hop-radius (new, default off): replaces the computed radius
        rad = float(radius)
    to = []
    for l in sorted(ls, key=lambda l: (l['squad'], l['to'])):
        t = l['to']
        if all(math.hypot(t[0] - o[0], t[2] - o[2]) >= APART for o in to) and len(to) < 8:
            to.append(t)
    nav = F.Nav(B.scene.nav)
    base = list(to)
    for o in base:                                       # more landing places on the same floor: klhop.c gives each bot its own (7 bots)
        for dx, dz in ((130, 0), (-130, 0), (0, 130), (0, -130), (130, 130), (-130, -130), (130, -130), (-130, 130), (260, 0), (-260, 0)):
            t = (o[0] + dx, o[1], o[2] + dz)
            hit = nav.at(*t, dy=15)
            t = (t[0], hit[1] if hit else t[1], t[2])
            if len(to) < 8 and hit and nav.clearance(*t) >= F.CLEAR / 2.0 + 20.0 and all(math.hypot(t[0] - q[0], t[2] - q[2]) >= APART for q in to):
                to.append(t)
    log('ramp: %d lift(s) from the floor y %d..%d; From (%d, %d, %d) radius %d height %g wait %g; %d landing place(s)'
        % (len(ls), from_y[0], from_y[1], *c, rad, HEIGHT, wait, len(to)))
    return [collections.OrderedDict([('from', [round(v, 1) for v in c]), ('radius', round(rad)), ('height', HEIGHT), ('wait', wait),
                                     ('stage', STAGE), ('player', 0), ('kind', 'lift'), ('to', [[round(v, 1) for v in t] for t in to])])]


def build(src, slot, dst, min_dy=MIN_DY, from_y=FROM_Y, wait=WAIT, log=print, radius=None, replace=False):
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError('the output folder is the build\'s own')
    B = F.Built(src, slot)
    hops = plan(B, min_dy, from_y, wait, log, radius)
    if not hops:
        raise ValueError('no lift from the floor y %s..%s: nothing to hop' % from_y)
    if F.hop_read(src) and not replace:   # --replace (new): hop_write swaps the old [CrewHop] sections for the new ones
        raise ValueError('%s already has [CrewHop] sections: not stacked' % os.path.join(src, F.HOP_FILE))
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p):
            shutil.copyfile(p, os.path.join(dst, f))
    F.hop_write(dst, hops, 'the y %d floor -> the y %d floor (kl_fa_ramp)' % (round(from_y[0] + 60), round(hops[0]['to'][0][1])), log)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_ramp: [CrewHop] in KLJoin.ini only (%d landing places, From %s radius %s wait %s); no archive member changed, from %s\n'
                % (len(hops[0]['to']), hops[0]['from'], hops[0]['radius'], hops[0]['wait'], src))
    return hops


def main():
    a = sys.argv[1:]
    opt = dict(min_dy=MIN_DY, from_y=FROM_Y, wait=WAIT)
    if '--replace' in a:
        a.remove('--replace'); opt['replace'] = True
    if '--hop-radius' in a:
        i = a.index('--hop-radius'); opt['radius'] = float(a[i + 1]); del a[i:i + 2]
    for flag, key in (('--wait', 'wait'), ('--min-dy', 'min_dy')):
        if flag in a:
            i = a.index(flag); opt[key] = float(a[i + 1]); del a[i:i + 2]
    if '--from-y' in a:
        i = a.index('--from-y'); opt['from_y'] = (float(a[i + 1]), float(a[i + 2])); del a[i:i + 3]
    if len(a) == 3 and a[0] == 'find':
        B = F.Built(a[1], a[2])
        for l in lifts(B, opt['min_dy']):
            print(l['squad'][-8:], l['step'], [round(v) for v in l['frm']], '->', [round(v) for v in l['to']], 'dy', round(l['dy']), 'h', round(l['h']),
                  'path', None if l['path'] is None else round(l['path']))
    elif len(a) == 4 and a[0] == 'build':
        build(a[1], a[2], a[3], **opt)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
