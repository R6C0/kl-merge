"""kl_rt_joinini.py SRC_DM09_FOLDER OUT_FOLDER [--margins] [--set SECTION.KEY=VALUE ...] [--dry]

Opt-in post-pass on a built Retomoto (DM09) folder: copies every file of SRC to OUT and rewrites ONLY
KLJoin.ini values that the caller asks for. With no flag the output is byte-identical to the source
(proved by md5 in the run's summary). Nothing in the Dog Days folder is touched; nothing is installed.

Why (re/retomoto_fa.md 13.1): the crew hop / join margins read from the owner's real rounds were thin:
  [CrewHop.2] Radius 700: the 11 first sightings lie 653..697 from From (3 to spare for one bot in eleven);
  [CrewHop.3] Height 150: sightings sit at dy +130..+146 (4 to spare), the +0x460 place disagrees (dy +217..225).
--margins applies exactly those two GUESSes:  CrewHop.2.Radius 700 -> 800,  CrewHop.3.Height 150 -> 250.
--set edits any other single key (the section header must be exact, e.g. CrewHop.2; the key must exist ONCE
in that section, else the tool stops - it never adds a key).

GUESS (not tested in the game): 800 catches a bot earlier on its way in (it is carried the moment it stands
Wait=1 s inside the circle), so bots may be carried from a little further away; whether walls lie within 800
of the lift lobby is unchecked. 250 only widens the height window of hop 3; hop 3 already worked on the node
alone. Revert = use the source folder.

--rescue-wedge APPENDS one section [CrewHop.6] (the only mode that adds anything; refused if the section exists):
a rescue for the boardroom-corridor wedge at (797, 21000, 639), where bots stood motionless 277..287 s (KLHook.log
sessions 89/1 and 65/2; 18/1 and 37/1 at the same spot) and no hop covers them. It carries a bot standing there for
100 s to the street landing places. ALL VALUES ARE GUESSES (Radius 250, Height 200, Wait 100: longer than the longest
lingering seen outside the wedge, about 85 s, shorter than the wedges seen, 277 s and up).

--giveup N (2026-10-18, L79 finding, re/retomoto_fa.md s14): sets GiveUp (seconds) of the two WALK hops, [CrewHop] (40) and
[CrewHop.3] (45), to N. In L79 five hop-3 walks hit 45 s while fedkit-hunted kept re-ordering the bots (see below); a longer budget
only helps if the walk is still progressing. GUESS: 80. The real fix is [Bots] WalkExclusive=1 in KLHook.ini (hook side, not here).

--leaderless-hop N (2026-10-18, re/retomoto_leaderless.md): APPENDS [CrewHop.6], a tower-wide catch-all that carries a bot to the
street places once after it has stayed N s in the tower. Not tied to the human becoming a fed. Refused with --rescue-wedge or
if [CrewHop.6] exists. GUESS values; N 10..600.

--leaderless-player (2026-10-19, re/retomoto_hop6_ini.md; needs --leaderless-hop): writes [CrewHop.6] with Player=1 instead of Player=0.
klhop.c then lets the hop fire only after a LIVING criminal human has stood nearer To.1 than From (sticky). A living human in the
tower never does, so the crew is not carried away from them. NOTE (from the code, not a guess): a fed or dead human never does either
(kle_human is type 2 only), so with this flag the hop never fires for a fed crew. It is the living-human half only.

--leaderless-nohuman (2026-10-19, re/retomoto_hop6_living.md s6; needs --leaderless-hop; needs a klhop.c WITH the NoHuman gate):
writes NoHuman=1 after Player= in [CrewHop.6]. The hop then idles (its timers stay 0) while a LIVING human exists and counts Wait
from the moment they are dead or a fed. REFUSED together with --leaderless-player: Player=1 never passes for a fed, so the hop would
not fire for a fed crew and the gate would be pointless. An OLD hook ignores the unknown key (GetPrivateProfileInt) = the plain hop.

Exit code 0 = written and verified (only the named lines differ), 1 = refused."""
import sys, os, re, shutil, hashlib, argparse

RESCUE = ["; --rescue-wedge (kl_rt_joinini.py): boardroom-corridor wedge, bots stood 277..287 s (log sessions 89/1, 65/2).",
          "; GUESS: Radius / Height / Wait are not tested in the game.",
          "[CrewHop.6]", "From=797 21000 639", "Radius=250", "Height=200", "Wait=100", "Stage=0", "Player=0", "Again=0",
          "Places=7", "To.1=6272 570 -5200", "To.2=5872 570 -5585", "To.3=5708 570 -5705", "To.4=5828 570 -6309",
          "To.5=5708 570 -7245", "To.6=5872 570 -7025", "To.7=5952 570 -7770"]
MARGINS = ['CrewHop.2.Radius=800', 'CrewHop.3.Height=250']


def leaderless_lines(n, player=0, nohuman=0):
    """--leaderless-hop N (re/retomoto_leaderless.md): a catch-all hop for the whole tower. A bot that has stayed N s inside it
    (the timer is per bot and restarts when it leaves the circle) is carried to the street places once. It is NOT tied to the
    human becoming a fed (a hop cannot see that; that needs hook code, see the doc). ALL VALUES ARE GUESSES."""
    return ["; --leaderless-hop %d (kl_rt_joinini.py): any bot that stays in the tower %d s is carried to the street (once)." % (n, n),
            "; GUESS: From / Radius / Height cover the tower floors (heights 18500..21500, 6000 around x=2000 z=-500); N is not tested.",
            "[CrewHop.6]", "From=2000 20000 -500", "Radius=6000", "Height=1500", "Wait=%d" % n, "Stage=0", "Player=%d" % player] + (["NoHuman=1"] if nohuman else []) + ["Again=0",
            "Places=7", "To.1=6272 570 -5200", "To.2=5872 570 -5585", "To.3=5708 570 -5705", "To.4=5828 570 -6309",
            "To.5=5708 570 -7245", "To.6=5872 570 -7025", "To.7=5952 570 -7770"]


# kl_fa_author.JOIN_BOX_CAR = ((2802, 3142), (19560, 19860), (789, 1029)): the inside of the tower's escape car (x, y up, z)
CAR_MIN, CAR_MAX = '2802 19560 789', '3142 19860 1029'


def add_ride(data, delay, car, fallback):
    """--delay S (2026-10-23, klhook/kljoin.c 'the ride'): INSERTS keys into the [Join] section (right after its last key line):
    Delay=S, and with --car CarMin / CarMax (+ CarWait=6, CarFallback=0 with --no-car-fallback). Refused if [Join] already has any of
    them. Returns (new bytes, [inserted lines as text]). An old hook ignores the unknown keys (GetPrivateProfileInt) = the instant jump."""
    nl = b'\r\n' if b'\r\n' in data else b'\n'
    lines = data.split(b'\n')
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == b'[Join]':
            start = i
            break
    if start is None:
        raise SystemExit('refused: no [Join] section')
    end = start + 1
    last = start
    while end < len(lines) and not lines[end].strip().startswith(b'['):
        s = lines[end].strip()
        if s and not s.startswith(b';'):
            last = end
            if re.match(rb'(Delay|Slack|CarMin|CarMax|CarWait|CarFallback)\s*=', s, re.I):
                raise SystemExit('refused: [Join] already has a ride key: ' + s.decode('latin1'))
        end += 1
    add = ['; 2026-10-23 THE RIDE (kl_rt_joinini.py --delay; klhook/kljoin.c): the jump comes %g s after the feet enter the box, if the player is' % delay,
           '; then alive and still near it%s. An older hook ignores these keys (= the instant jump).' % (' (the jump waits for the car box CarMin/CarMax = kl_fa_author.JOIN_BOX_CAR, 6 s at most%s)' % ('' if fallback else ', no fallback') if car else ''),
           'Delay=%g' % delay]
    if car:
        add += ['CarMin=' + CAR_MIN, 'CarMax=' + CAR_MAX, 'CarWait=6']
        if not fallback:
            add.append('CarFallback=0')
    cr = b'\r' if lines[last].endswith(b'\r') else b''
    lines[last + 1:last + 1] = [x.encode() + cr for x in add]
    return b'\n'.join(lines), add


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def edit(data, sets):
    """data: bytes of KLJoin.ini. sets: list of (section, key, value). Returns (new bytes, [(section,key,old,new)])."""
    lines = data.split(b'\n')          # keeps any \r at the end of a line
    done = []
    for sec, key, val in sets:
        cur = None
        hits = []
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s.startswith(b'[') and s.endswith(b']'):
                cur = s[1:-1].decode('latin1')
            elif cur == sec and not s.startswith(b';'):
                m = re.match(rb'^(\s*)' + re.escape(key.encode()) + rb'(\s*=\s*)([^\r]*?)(\s*)$', ln.rstrip(b'\r'))
                if m:
                    hits.append((i, m))
        if len(hits) != 1:
            raise SystemExit('refused: [%s] %s found %d times (need exactly 1)' % (sec, key, len(hits)))
        i, m = hits[0]
        cr = b'\r' if lines[i].endswith(b'\r') else b''
        old = m.group(3).decode('latin1')
        lines[i] = m.group(1) + key.encode() + m.group(2) + val.encode() + m.group(4) + cr
        done.append((sec, key, old, val))
    return b'\n'.join(lines), done


def parse_set(s):
    if '=' not in s or '.' not in s.split('=')[0]:
        raise SystemExit('refused: --set wants SECTION.KEY=VALUE, got ' + s)
    lhs, val = s.split('=', 1)
    sec, key = lhs.rsplit('.', 1)
    return sec, key, val


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--margins', action='store_true')
    ap.add_argument('--set', action='append', default=[])
    ap.add_argument('--rescue-wedge', action='store_true')
    ap.add_argument('--giveup', type=int, metavar='SECONDS', default=None)
    ap.add_argument('--leaderless-hop', type=int, metavar='SECONDS', default=None)
    ap.add_argument('--leaderless-player', action='store_true')
    ap.add_argument('--leaderless-nohuman', action='store_true')
    ap.add_argument('--delay', type=float, metavar='SECONDS', default=None)
    ap.add_argument('--car', action='store_true')
    ap.add_argument('--no-car-fallback', action='store_true')
    ap.add_argument('--ini-only', action='store_true')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args(argv)
    if a.delay is not None and not 0 < a.delay <= 30:
        raise SystemExit('refused: --delay must be 0..30 seconds (kljoin.c ignores a Delay outside 0..30)')
    if (a.car or a.no_car_fallback) and a.delay is None:
        raise SystemExit('refused: --car / --no-car-fallback need --delay S')
    if a.no_car_fallback and not a.car:
        raise SystemExit('refused: --no-car-fallback needs --car')
    if a.leaderless_hop is not None:
        if not 10 <= a.leaderless_hop <= 600:
            raise SystemExit('refused: --leaderless-hop must be 10..600 (klhop.c clamps Wait to 1..600)')
        if a.rescue_wedge:
            raise SystemExit('refused: --leaderless-hop and --rescue-wedge both add [CrewHop.6]')
    if a.leaderless_player and a.leaderless_hop is None:
        raise SystemExit('refused: --leaderless-player needs --leaderless-hop N')
    if a.leaderless_nohuman and a.leaderless_hop is None:
        raise SystemExit('refused: --leaderless-nohuman needs --leaderless-hop N')
    if a.leaderless_nohuman and a.leaderless_player:
        raise SystemExit('refused: --leaderless-nohuman and --leaderless-player cancel out (Player=1 never passes for a fed)')
    gu = []
    if a.giveup is not None:
        if not 5 <= a.giveup <= 600:
            raise SystemExit('refused: --giveup must be 5..600 (klhop.c clamps GiveUp to that)')
        gu = ['CrewHop.GiveUp=%d' % a.giveup, 'CrewHop.3.GiveUp=%d' % a.giveup]
    sets = [parse_set(s) for s in (MARGINS if a.margins else []) + gu + a.set]
    ini = os.path.join(a.src, 'KLJoin.ini')
    if not os.path.isfile(ini):
        raise SystemExit('refused: no KLJoin.ini in ' + a.src)
    src_abs, out_abs = os.path.abspath(a.src), os.path.abspath(a.out)
    if src_abs == out_abs:
        raise SystemExit('refused: OUT must differ from SRC')
    if 'KL_PortBackup' in out_abs or 'steamapps' in out_abs.lower():
        raise SystemExit('refused: OUT must not be a game folder')
    data = open(ini, 'rb').read()
    new, done = edit(data, sets)
    pre_delay = new
    ins = []
    if a.delay is not None:
        new, ins = add_ride(new, a.delay, a.car, not a.no_car_fallback)
        for x in ins:
            print('KLJoin.ini [Join] added: ' + x)
    base = new
    if a.rescue_wedge:
        if re.search(rb'^\s*\[CrewHop\.6\]', data, re.M):
            raise SystemExit('refused: [CrewHop.6] already exists')
        nl = b'\r\n' if b'\r\n' in data else b'\n'
        add = nl.join(x.encode() for x in RESCUE) + nl
        new = new + (b'' if new.endswith(b'\n') else nl) + nl + add
    if a.leaderless_hop is not None:
        if re.search(rb'^\s*\[CrewHop\.6\]', data, re.M):
            raise SystemExit('refused: [CrewHop.6] already exists')
        nl = b'\r\n' if b'\r\n' in data else b'\n'
        add = nl.join(x.encode() for x in leaderless_lines(a.leaderless_hop, 1 if a.leaderless_player else 0, 1 if a.leaderless_nohuman else 0)) + nl
        new = new + (b'' if new.endswith(b'\n') else nl) + nl + add
        print('appended [CrewHop.6] catch-all, Wait=%d, Player=%d%s' % (a.leaderless_hop, 1 if a.leaderless_player else 0, ', NoHuman=1' if a.leaderless_nohuman else ''))
    for d in done:
        print('KLJoin.ini [%s] %s: %s -> %s' % d)
    if a.dry:
        print('dry run: nothing written')
        return 0
    os.makedirs(a.out, exist_ok=True)
    for n in sorted(os.listdir(a.src)):
        p = os.path.join(a.src, n)
        if not os.path.isfile(p):
            continue
        q = os.path.join(a.out, n)
        if a.ini_only and n != 'KLJoin.ini':
            continue          # --ini-only: just the file (the map zip is not copied: it is large and unchanged)
        if n == 'KLJoin.ini':
            open(q, 'wb').write(new)
        else:
            shutil.copy2(p, q)
    diff = []
    for n in sorted(os.listdir(a.src)):
        p = os.path.join(a.src, n)
        if a.ini_only and n != 'KLJoin.ini':
            continue
        if os.path.isfile(p) and md5(p) != md5(os.path.join(a.out, n)):
            diff.append(n)
    if diff != (['KLJoin.ini'] if new != data else []):
        raise SystemExit('refused: unexpected differing members %s' % diff)
    # only the named lines differ
    if not (new.startswith(base) or ins):
        raise SystemExit('refused: appended text changed existing bytes')
    if ins:       # the added ride keys: removing exactly those lines must give back the file as it was before them
        if base.replace(b'\r\n', b'\n').split(b'\n') == pre_delay.replace(b'\r\n', b'\n').split(b'\n'):
            raise SystemExit('refused: --delay added nothing')
        lines_b = base.split(b'\n')
        keep = [l for l in lines_b if l.rstrip(b'\r').decode('latin1') not in ins]
        if b'\n'.join(keep) != pre_delay:
            raise SystemExit('refused: --delay changed more than its own lines')
        base = pre_delay
    a_l, b_l = data.split(b'\n'), base.split(b'\n')
    nd = sum(1 for x, y in zip(a_l, b_l) if x != y)
    if len(a_l) != len(b_l) or nd != len(done):
        raise SystemExit('refused: %d lines differ, expected %d' % (nd, len(done)))
    print('differs from source: %s; lines changed: %d' % (diff or 'nothing (byte-identical)', nd))
    for n in sorted(os.listdir(a.out)):
        print('%s %s' % (md5(os.path.join(a.out, n)), n))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
