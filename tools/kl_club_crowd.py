"""kl_club_crowd.py - fill Last Call (DM05A) with a crowd of cheap civilians (owner 2026-10-24: "still empty, needs to be full to the brim").

WHY THE CLUB LOOKED EMPTY: the installed DM05A has ten civilians (Civ_FA_000..009, one model 54304) in a map of 67 actors
(guards, bots, you); a civilian stands still until a player walks into her tbCivRunToGate box (half extents = alert,
1200 by default) and then runs, so in a big club ten of them are a handful. This tool adds more of the SAME proven form
(kl_fa_civs.add: stock F07's civilian clone, 8 entities, 1 actor, 1 squad each, the live model of the build) and places
them with kl_fa_civs.plan_places on the build's navigation mesh: the ground floor (y about 40) and the upper floor
(y about 460) of the play part, away from walls, from every actor, from each other, from the LevelBound kill boxes, and
clear of every START spawn. The run box is SMALL (alert 450): the crowd stands, it does not stampede the moment you arrive.

BUDGET (GUESS, said plainly): the live DM05A has 67 actors / 39 squads. Each civilian adds 1 actor and 1 squad, so
the default 40 more give 107 actors / 79 squads. The largest build proven live is 99 actors / 55 squads (kl_fa_civs.CAP_*),
stock Last Call (L07) has 148 actors / 90 squads and the tool's own envelope is 147 / 500 (re/civilians.md), so this is
over the proven point and under the stock one: a RISK, not a fact. --count lowers it; the install bat leaves the previous zip
as .before-1024club.

  python tools/kl_club_crowd.py build <live DM05A folder> <out folder> [--count 40] [--upper 12] [--alert 450] [--seed 7]
  python tools/kl_club_crowd.py check <out folder>

Nothing is written into the game: <out folder> gets the finished zip and every non-backup file of the source.
"""
import hashlib
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa_bots as F
import kl_fa_civs as C

SLOT = 'F01'
CENTRE = (500.0, 40.0, 2800.0)      # GUESS: the middle of the club's ground floor on the nav mesh (read off plan_places probes, 2026-10-24)
RADIUS = 2400.0
GROUND_SEP, UPPER_SEP = 100.0, 100.0
BOUNDS = 150.0
START_CLEAR = 150.0


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def trimmed_copy(src, dst):
    """Copy the live folder without its .before-* backups and tool by-products (add() copies every file of its source)."""
    os.makedirs(dst)
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p) and '.before-' not in f and not f.startswith(('audit.', 'civs.')) and not f.endswith(('.bak', '.old')):
            shutil.copyfile(p, os.path.join(dst, f))


def plan(B, count, upper, alert, seed):
    area = C.play_area(B, F.Nav(B.scene.nav), C.PLAY_BAND)
    ground = dict(part=area['part'], centre=CENTRE, y0=40.0, band=70.0)
    out = C.plan_places(B, count - upper, centre=CENTRE, radius=RADIUS, seed=seed, sep=GROUND_SEP, flee=2, play=ground, bounds=BOUNDS,
                        start_clear=START_CLEAR, alert=alert)
    if upper > 0:
        up = dict(part=area['part'], centre=(0.0, 460.0, 900.0), y0=460.0, band=70.0)
        try:
            more = C.plan_places(B, upper * 2, centre=up['centre'], radius=1800.0, seed=seed + 1, sep=UPPER_SEP, flee=2, play=up,
                                 bounds=BOUNDS, start_clear=START_CLEAR, alert=alert)
        except ValueError as e:
            print('NOTE: no upper floor group (%s)' % e)
            more = []
        for c in more:                                     # plan_places knows only the actors already in the build: keep the groups apart too
            if len(out) >= count:
                break
            if all(math.hypot(c['pos'][0] - o['pos'][0], c['pos'][2] - o['pos'][2]) >= UPPER_SEP for o in out):
                out.append(c)
    return out, ground


def build(src, dst, count, upper, alert, seed):
    live = os.path.join(src, 'F01_Main.zip')
    tmp = dst.rstrip('\\/') + '_src'
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    trimmed_copy(src, tmp)
    try:
        B = F.Built(tmp, SLOT)
        c0 = C.census(B)
        civs, play = plan(B, count, upper, alert, seed)
        print('census before: %d actors, %d squads, %d civilians; %d of %d places found' % (c0['actors'], c0['squads'], c0['civilians'], len(civs), count))
        if not civs:
            raise SystemExit('no places')
        play = dict(part=play['part'], centre=list(CENTRE), radius=RADIUS, band=70.0, y0=40.0, source='kl_club_crowd')
        rep = C.add(tmp, dst, civs, SLOT, 'auto', alert, True, play=None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    with open(os.path.join(dst, 'BUILT_ON.txt'), 'w') as f:
        f.write('built on %s md5 %s\n%d civilians added (actors %d -> %d, squads %d -> %d)\n' % (
            live, md5(live), len(civs), c0['actors'], c0['actors'] + len(civs), c0['squads'], c0['squads'] + len(civs)))
    fails, _ = C.check(dst, SLOT, play=False)
    c1 = C.census(F.Built(dst, SLOT))
    print('census after: %d actors, %d squads, %d civilians' % (c1['actors'], c1['squads'], c1['civilians']))
    return 1 if fails else 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a.pop(0)

    def opt(flag, conv, default):
        if flag in a:
            i = a.index(flag)
            v = conv(a[i + 1])
            del a[i:i + 2]
            return v
        return default
    if cmd == 'check':
        fails, _ = C.check(a[0], SLOT)
        return 1 if fails else 0
    if cmd == 'build':
        count, upper = opt('--count', int, 40), opt('--upper', int, 12)
        alert, seed = opt('--alert', float, 450.0), opt('--seed', int, 7)
        return build(a[0], a[1], count, upper, alert, seed)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
