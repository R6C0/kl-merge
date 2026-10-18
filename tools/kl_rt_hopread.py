"""kl_rt_hopread.py [KLHook.log] [--since HH:MM:SS] [--until HH:MM:SS] [--last N]

Read-only verdict on the Retomoto (DM09, slot F06) crew hop and join from the KLHook.log of a real round.
Nothing is written, installed or started; exit code 0. Default log: the Dog Days folder's KLHook.log.

What it reads (lines of klhop.c / klcrew_rt.c / kljoin.c / klfed*.c). Coordinates in them are (x, HEIGHT, z): the
tower floor is height 19600, the lobby car 560..570, so 'z about 190' in the notes is the THIRD number.
  hop: N hop(s) from ...\\DM09\\KLJoin.ini   starts a DM09 span; 'hop: hop H: From (..) radius R height Y' = the plan
                                             in force (so an old radius can be re-judged against the same sightings);
  hop: bot B is at From of hop H: node (..)  a bot seen standing in the place (the FIRST sighting per hop = ARRIVAL);
  hop: bot B (actor A) hop H: ... ordered to WALK / -> To.K  walk ordered / carried;
  hop: bot B (walk of hop H) at (..), D m from the walk's end   a STALL sample (on its walk, not arrived yet);
  '... GIVE UP - teleported'                 the walk's 40 s fallback;
  crewjoin: bot B at (..) -> place N / NOT moved: <why> / N moved / is the local FED's   the join's crew move;
  join: player 0 entered box ...;  fed: round N: ... / YOU ARE A FED ... at (..)   round split and the fed's place.
A span is cut into rounds at 'fed: round N:' lines. Per bot the outcome is
  HOP2/HOP1/HOP3  carried by that [CrewHop] by itself (HOP2 = the elevator floor);   GIVEUP  teleported by the walk fallback;
  JOIN   moved by the player's jump (crewjoin: ... -> place);   ENTRY  'NOT moved: it is at the entry already' (= a hop
  carried it before the jump);   NONE  no carry seen (died, not there yet, or the log ends).
Per bot it also prints the first sighting in hop 2's place: horizontal (x, z) distance from hop 2's From against the radius in
force and against 430 (the radius before 2026-10-15), its height difference against Height, and the walk re-orders."""
import re, sys, math, argparse

NUM = r'(-?\d+(?:\.\d+)?)'
V3 = r'\(' + NUM + r', ' + NUM + r', ' + NUM + r'\)'
T = re.compile(r'(\d\d):(\d\d):(\d\d\.\d+) (.*)')
R_PLAN = re.compile(r'hop: (\d+) hop\(s\) from (.*)DM09\\KLJoin\.ini')
R_HOP = re.compile(r'hop: hop (\d+): From ' + V3 + r' radius (\d+) height (\d+), wait ' + NUM + r' s')
R_WALKHOP = re.compile(r'hop: hop (\d+) is a WALK hop: a bot at From is ordered to walk to ' + V3 + r' .*?after (\d+) s')
R_SEEN = re.compile(r'hop: bot (\d+) is at From of hop (\d+): node ' + V3 + r', \+0x460 ' + V3 + r', heist stage (\d+); carried over in ' + NUM + r' s if it stays(.*)')
R_WALK = re.compile(r'hop: bot (\d+) \(actor \w+\) hop (\d+): at From for ' + NUM + r' s, node ' + V3 + r': ordered to WALK')
R_CARRY = re.compile(r'hop: bot (\d+) \(actor \w+\) hop (\d+): at From for ' + NUM + r' s, node ' + V3 + r' -> To\.(\d+) ' + V3)
R_AGAIN = re.compile(r'hop: bot (\d+) \(walk of hop (\d+)\) at ' + V3 + r', ' + NUM + r' m from the walk\'s end after ' + NUM + r' s')
R_GIVE = re.compile(r'hop: bot (\d+) walked ' + NUM + r' s towards .*GIVE UP - teleported from ' + V3 + r' to To\.(\d+)')
R_PLACE = re.compile(r'hop: bot (\d+) is at node ' + V3 + r', \+0x460 ' + V3 + r' 2 s after hop (\d+), heist stage (\d+)')
R_WALKEND = re.compile(r'hop: bot (\d+): its walk of hop (\d+) ends here \(' + NUM + r' s\)')
R_NOTCARRIED = re.compile(r'hop: bot (\d+) hop (\d+) NOT carried: (.*)')
R_CJ = re.compile(r'crewjoin: bot (\d+) \(actor \w+\) at ' + V3 + r' -> place (\d+)')
R_CJNO = re.compile(r'crewjoin: bot (\d+) \(actor \w+\) NOT moved: (.*)')
R_CJN = re.compile(r'crewjoin: (\d+) moved')
R_CJFED = re.compile(r'crewjoin: the jump to entry .* is the local FED\'s')
R_BOX = re.compile(r'join: player 0 entered box (\d+) at ' + V3)
R_BOXDEF = re.compile(r'join: box (\d+): ' + V3 + r' - ' + V3 + r' -> entry')
R_JAT = re.compile(r'join: player 0 is at ' + V3 + r' (\d+) ms after the request')
R_ROUND = re.compile(r'fed: round (\d+): .*?(\d+) AI \((\d+) in play\).*?round clock (\d+) s')
R_STAND = re.compile(r'fed: YOU STAND at ' + V3)
R_FED = re.compile(r'fed: YOU ARE A FED: .*? at ' + V3)
R_LEVEL = re.compile(r'steam: level archive (\S+) opened from (.*?): ')
TOWER_H = 10000.0                                   # height above this = the tower half, below = the street half
OLD_RADIUS = 430.0                                  # CrewHop.2 radius before 2026-10-15 (then raised to 700, a GUESS)


def secs(h, m, s): return int(h) * 3600 + int(m) * 60 + float(s)
def hms(t): return '%02d:%02d:%04.1f' % (t // 3600, (t % 3600) // 60, t % 60)
def fl(g): return tuple(float(x) for x in g)
def hd(a, b): return math.hypot(a[0] - b[0], a[2] - b[2])


class Bot:
    def __init__(s, n): s.n = n; s.first = {}; s.walk = {}; s.again = []; s.carry = None; s.outcome = 'NONE'; s.out_t = None; s.notes = []; s.landed = []; s.walked = []
class Round:
    def __init__(s, no, t0, ai, clock):
        s.no, s.t0, s.ai, s.clock = no, t0, ai, clock; s.bots = {}; s.join_t = None; s.join_at = None; s.join_after = None
        s.moved = None; s.fedat = []; s.fedstand = []; s.fedskip = 0; s.end = t0
    def bot(s, n): return s.bots.setdefault(n, Bot(n))
class Span:
    def __init__(s, t0, session): s.t0, s.session = t0, session; s.plan = {}; s.walkhop = {}; s.rounds = []; s.box = None; s.session_t = None


def parse(path, since, until):
    spans = []; sess = 0; cur = None; rnd = None; sess_t = {}; pend_box = None
    with open(path, 'r', encoding='latin-1', errors='replace') as fh:
        for ln in fh:
            if not ('hop' in ln or 'crewjoin' in ln or 'join:' in ln or 'fed:' in ln or '==== KLHook' in ln or 'steam: level archive' in ln):
                continue
            m = T.match(ln.rstrip('\r\n'))
            if not m: continue
            h, mi, s, r = m.groups(); t = secs(h, mi, s)
            if r.startswith('==== KLHook'):
                sess += 1; sess_t[sess] = t; cur = rnd = pend_box = None; continue
            if (since is not None and t < since) or (until is not None and t > until): continue
            if R_PLAN.match(r):
                cur = Span(t, sess); cur.box = pend_box; spans.append(cur); rnd = None; continue
            q = R_BOXDEF.match(r)
            if q: pend_box = (fl(q.groups()[1:4]), fl(q.groups()[4:7]))
            q = R_LEVEL.match(r)
            if q:
                if cur is not None and 'DM09' not in q.group(2): cur = rnd = None
                continue
            if cur is None: continue
            q = R_HOP.match(r)
            if q: cur.plan[int(q.group(1))] = dict(frm=fl(q.groups()[1:4]), radius=float(q.group(5)), height=float(q.group(6)), wait=float(q.group(7))); continue
            q = R_WALKHOP.match(r)
            if q: cur.walkhop[int(q.group(1))] = (fl(q.groups()[1:4]), int(q.group(5))); continue
            q = R_BOXDEF.match(r)
            if q: cur.box = (fl(q.groups()[1:4]), fl(q.groups()[4:7])); continue
            q = R_ROUND.match(r)
            if q:
                rnd = Round(int(q.group(1)), t, int(q.group(3)), int(q.group(4))); cur.rounds.append(rnd); continue
            if rnd is None:
                if r.startswith(('hop:', 'crewjoin:', 'join:')):
                    rnd = Round(0, t, -1, 0); cur.rounds.append(rnd)
                else: continue
            rnd.end = t
            q = R_SEEN.match(r)
            if q:
                b = rnd.bot(int(q.group(1))); hop = int(q.group(2))
                if hop not in b.first: b.first[hop] = dict(t=t, node=fl(q.groups()[2:5]), ft=fl(q.groups()[5:8]), stage=int(q.group(9)), dis=('they disagree' in q.group(11)))
                continue
            q = R_WALK.match(r)
            if q: rnd.bot(int(q.group(1))).walk.setdefault(int(q.group(2)), (t, fl(q.groups()[3:6]))); continue
            q = R_CARRY.match(r)
            if q:
                b = rnd.bot(int(q.group(1))); hop = int(q.group(2))
                if b.outcome == 'NONE':
                    b.outcome = 'HOP%d' % hop; b.out_t = t; b.carry = dict(hop=hop, at=fl(q.groups()[3:6]), to=int(q.group(7)), held=float(q.group(3)))
                continue
            q = R_AGAIN.match(r)
            if q: rnd.bot(int(q.group(1))).again.append((t, int(q.group(2)), fl(q.groups()[2:5]), float(q.group(6)), float(q.group(7)))); continue
            q = R_GIVE.match(r)
            if q:
                b = rnd.bot(int(q.group(1)))
                if b.outcome == 'NONE': b.outcome = 'GIVEUP'; b.out_t = t; b.carry = dict(at=fl(q.groups()[2:5]), to=int(q.group(6)))
                continue
            q = R_PLACE.match(r)
            if q: rnd.bot(int(q.group(1))).landed.append((t, int(q.group(8)), fl(q.groups()[1:4]), fl(q.groups()[4:7]), int(q.group(9)))); continue
            q = R_WALKEND.match(r)
            if q: rnd.bot(int(q.group(1))).walked.append((int(q.group(2)), float(q.group(3)))); continue
            q = R_NOTCARRIED.match(r)
            if q: rnd.bot(int(q.group(1))).notes.append((t, 'hop %s NOT carried: %s' % (q.group(2), q.group(3)[:80]))); continue
            if 'did NOT land' in r or 'NOT put back' in r:
                q = re.match(r'hop: bot (\d+) ', r)
                if q: rnd.bot(int(q.group(1))).notes.append((t, r[:150])); continue
            q = R_CJ.match(r)
            if q:
                b = rnd.bot(int(q.group(1)))
                if b.outcome == 'NONE': b.outcome = 'JOIN'; b.out_t = t; b.carry = dict(at=fl(q.groups()[1:4]), to=int(q.group(5)))
                continue
            q = R_CJNO.match(r)
            if q:
                b = rnd.bot(int(q.group(1)))
                if 'at the entry already' in q.group(2):
                    if b.outcome == 'NONE': b.outcome = 'ENTRY'; b.out_t = t
                else: b.notes.append((t, 'join NOT moved: ' + q.group(2)[:80]))
                continue
            q = R_CJN.match(r)
            if q: rnd.moved = int(q.group(1)); continue
            if R_CJFED.match(r): rnd.fedskip += 1; continue
            q = R_BOX.match(r)
            if q and rnd.join_t is None: rnd.join_t = t; rnd.join_at = fl(q.groups()[1:4]); continue
            q = R_JAT.match(r)
            if q and rnd.join_after is None: rnd.join_after = fl(q.groups()[0:3]); continue
            q = R_FED.match(r)
            if q: rnd.fedat.append((t, fl(q.groups()))); continue
            q = R_STAND.match(r)
            if q: rnd.fedstand.append((t, fl(q.groups()))); continue
    for sp in spans: sp.session_t = sess_t.get(sp.session)
    return spans


def inside(box, p): return all(box[0][i] <= p[i] <= box[1][i] for i in range(3))




def elevator_hop(sp):
    """The hop whose From is the elevator floor ([CrewHop.2]: (2560, 19600, 740)); older plans numbered the hops differently."""
    for h, p in sp.plan.items():
        if abs(p['frm'][0] - 2560) < 100 and abs(p['frm'][2] - 740) < 100 and p['frm'][1] > TOWER_H: return h
    return None


def report(spans):
    out = []; st = dict(first=[], land=[], walk=[], dis={}, dy3=[], rounds=[], giveups=0)
    for sp in spans:
        out.append('SPAN %s (session %d, KLHook loaded %s): %d hop(s) in the plan, %d round(s)' % (hms(sp.t0), sp.session, '?' if sp.session_t is None else hms(sp.session_t), len(sp.plan), len(sp.rounds)))
        for h in sorted(sp.plan):
            p = sp.plan[h]
            w = ('  WALK to (%.0f, %.0f, %.0f), give up %d s' % (sp.walkhop[h][0] + (sp.walkhop[h][1],))) if h in sp.walkhop else ''
            out.append('  plan hop %d: From (%.0f, %.0f, %.0f) radius %.0f height %.0f wait %.0f s%s' % (h, p['frm'][0], p['frm'][1], p['frm'][2], p['radius'], p['height'], p['wait'], w))
        eh = elevator_hop(sp)
        if sp.box: out.append('  join box: (%.0f, %.0f, %.0f) - (%.0f, %.0f, %.0f)' % (sp.box[0] + sp.box[1]))
        for rnd in sp.rounds:
            out.append('  ROUND %d from %s (%s AI in play, clock %d s), last line %s' % (rnd.no, hms(rnd.t0), '?' if rnd.ai < 0 else rnd.ai, rnd.clock, hms(rnd.end)))
            if rnd.join_t is not None:
                out.append('    join: box entered %.0f s into the round at (%.0f, %.0f, %.0f)%s; crewjoin moved %s; %s' % (
                    rnd.join_t - rnd.t0, rnd.join_at[0], rnd.join_at[1], rnd.join_at[2],
                    '' if rnd.join_after is None else ', 500 ms later at (%.0f, %.0f, %.0f)' % rnd.join_after,
                    '?' if rnd.moved is None else rnd.moved, ('FedSkip fired %d time(s)' % rnd.fedskip) if rnd.fedskip else 'no FedSkip line'))
            else:
                out.append('    join: the box was NOT entered in this round')
            for t, p in rnd.fedat:
                half = ''
                if rnd.join_t is not None: half = ' (%s the jump)' % ('before' if t < rnd.join_t else 'after')
                out.append('    fed: appeared %.0f s into the round at (%.0f, %.0f, %.0f) = %s half%s%s' % (t - rnd.t0, p[0], p[1], p[2],
                           'TOWER' if p[1] > TOWER_H else 'STREET', half, ' INSIDE the join box' if sp.box and inside(sp.box, p) else ''))
                st['rounds'].append((rnd, p))
            for t, p in rnd.fedstand:
                out.append('    fed: stood at (%.0f, %.0f, %.0f) 500 ms later%s%s' % (p[0], p[1], p[2], ' INSIDE the join box' if sp.box and inside(sp.box, p) else '',
                           (', %.2f s before the join fired' % (rnd.join_t - t)) if rnd.join_t is not None and 0 <= rnd.join_t - t < 5 else ''))
            if not rnd.bots: out.append('    no hop / join bot lines'); continue
            out.append('    bot  outcome      at(s)  hop1 seen  hop3 seen  elevator-hop first sighting: dist/radius/old430/dy (x, z)   walk s  re-orders (x, z, m left)   moved by join from')
            p2 = sp.plan.get(eh) if eh else None
            for n in sorted(rnd.bots):
                b = rnd.bots[n]
                def sn(h): return '%.0fs' % (b.first[h]['t'] - rnd.t0) if h in b.first else '-'
                s2 = '-'
                if eh in b.first and p2:
                    nd = b.first[eh]['node']; d = hd(nd, p2['frm']); dy = nd[1] - p2['frm'][1]
                    s2 = '%s %.0f/%.0f/%s/dy%+.0f (%.0f, %.0f)' % (sn(eh), d, p2['radius'], 'in' if d <= OLD_RADIUS else 'OUT', dy, nd[0], nd[2])
                    st['first'].append((rnd.no, n, d, dy, p2['radius'], p2['height']))
                for h, f1 in b.first.items():
                    if h != eh and sp.plan.get(h) and sp.walkhop.get(h):               # a walk hop other than the elevator: its height margin
                        st['dy3'].append((h, f1['node'][1] - sp.plan[h]['frm'][1], sp.plan[h]['height'], f1['dis']))
                        st['dis'].setdefault(h, [0, 0]); st['dis'][h][0] += 1; st['dis'][h][1] += 1 if f1['dis'] else 0
                ag = ' '.join('(%.0f,%.0f,%.0fm)' % (a[2][0], a[2][2], a[3]) for a in b.again[:4])
                if len(b.again) > 4: ag += ' +%d more' % (len(b.again) - 4)
                oc = b.outcome + ('>To.%d' % b.carry['to'] if b.carry and 'to' in b.carry else '')
                if b.outcome == 'GIVEUP': st['giveups'] += 1
                wk = ','.join('%.1f' % w for h, w in b.walked) or '-'
                for h, w in b.walked: st['walk'].append(w)
                mj = '(%.0f, %.0f) %.0f from the elevator' % (b.carry['at'][0], b.carry['at'][2], hd(b.carry['at'], (2560, 0, 740))) if b.outcome == 'JOIN' and b.carry else '-'
                out.append('    %-3d  %-12s %-6s %-10s %-10s %-56s %-7s %-26s %s' % (n, oc, '-' if b.out_t is None else '%.0f' % (b.out_t - rnd.t0), sn(1) if eh != 1 else '-', sn(3), s2, wk, ag or '-', mj))
                for t, y, nd, ft, stg in b.landed:
                    st['land'].append((nd[1], ft[1], stg))
                for t, x in b.notes[:3]: out.append('         note %s: %s' % (hms(t)[3:], x))
    return out, st


def verdict(spans, st):
    """Counted facts only; every threshold is named."""
    rounds = [r for sp in spans for r in sp.rounds if r.bots]
    cnt = {}
    for r in rounds:
        for b in r.bots.values(): cnt[b.outcome] = cnt.get(b.outcome, 0) + 1
    v = ['rounds with hop / join bot lines: %d; bot outcomes: %s' % (len(rounds), ', '.join('%s %d' % kv for kv in sorted(cnt.items())) or 'none')]
    d = st['first']
    if d:
        ds = sorted(x[2] for x in d); rad = sorted(set(x[4] for x in d)); hts = sorted(set(x[5] for x in d))
        v.append('elevator hop: first sighting of %d bot(s) at %.0f .. %.0f (x, z) from its From (median %.0f); radius in force %s; %d of %d are beyond the old 430; '
                 'the farthest has %.0f to spare; height difference %+.0f .. %+.0f against Height %s' % (
                     len(d), ds[0], ds[-1], ds[len(ds) // 2], '/'.join('%.0f' % x for x in rad), sum(1 for x in ds if x > OLD_RADIUS), len(ds),
                     min(x[4] for x in d) - ds[-1], min(x[3] for x in d), max(x[3] for x in d), '/'.join('%.0f' % x for x in hts)))
    if st['walk']:
        w = sorted(st['walk']); v.append('walk hops: %d walk(s) ended, %.1f .. %.1f s (median %.1f) of a 40 / 45 / 70 s budget; GIVE UP teleports: %d' % (len(w), w[0], w[-1], w[len(w) // 2], st['giveups']))
    if st['dy3']:
        v.append('walk hops other than the elevator: %d first sighting(s), height difference %+.0f .. %+.0f against Height %s; node and +0x460 disagree: %s' % (
            len(st['dy3']), min(x[1] for x in st['dy3']), max(x[1] for x in st['dy3']), '/'.join(sorted(set('%.0f' % x[2] for x in st['dy3']))),
            ', '.join('hop %d: %d of %d' % (h, c[1], c[0]) for h, c in sorted(st['dis'].items()))))
    if st['land']:
        s1 = [x for x in st['land'] if x[2] == 1]; s2 = [x for x in st['land'] if x[2] != 1]
        t = '2 s after a carry (%d bots): ' % len(st['land'])
        if s1: t += 'still at heist stage 1: %d bot(s), node height %.0f .. %.0f, +0x460 height %.0f .. %.0f (the places ask 570); ' % (len(s1), min(x[0] for x in s1), max(x[0] for x in s1), min(x[1] for x in s1), max(x[1] for x in s1))
        if s2: t += 'already at a later stage (walking down from the car): %d bot(s), node height %.0f .. %.0f' % (len(s2), min(x[0] for x in s2), max(x[0] for x in s2))
        nl = sum(1 for r in rounds for bb in r.bots.values() for _, x in bb.notes if 'NOT land' in x or 'NOT put back' in x)
        v.append(t + '; "did NOT land" / "NOT put back" lines: %d' % nl)
    fr = st['rounds']
    v.append('fed appearances: %d (%d in the tower half); FedSkip lines: %d' % (len(fr), sum(1 for r, p in fr if p[1] > TOWER_H), sum(r.fedskip for r in rounds)))
    return v


def main():
    ap = argparse.ArgumentParser(description='Read-only verdict on the Retomoto crew hop / join from a KLHook.log (see the module docstring).')
    ap.add_argument('log', nargs='?', default=r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLHook.log')
    ap.add_argument('--session', type=int, action='append', help='only this session (the Nth "==== KLHook loaded" of the file, 1-based); repeatable')
    ap.add_argument('--all', action='store_true', help='every DM09 span of the file (the default: the session that holds the last DM09 plan)')
    ap.add_argument('--since'); ap.add_argument('--until')
    a = ap.parse_args()
    def tt(x):
        if not x: return None
        p = x.split(':'); p += ['0'] * (3 - len(p)); return secs(*p)
    spans = parse(a.log, tt(a.since), tt(a.until))
    if a.session: spans = [sp for sp in spans if sp.session in a.session]
    elif not a.all and spans: spans = [sp for sp in spans if sp.session == spans[-1].session]
    if not spans: print('no DM09 hop plan in %s' % a.log); return 0
    out, st = report(spans)
    print('\n'.join(out)); print('\nVERDICT'); print('\n'.join('  ' + x for x in verdict(spans, st)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
