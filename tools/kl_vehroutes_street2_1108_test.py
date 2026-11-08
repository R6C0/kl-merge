"""Off-game self-test of kl_vehroutes_street2_1108 (hand-made fixtures, no game file): bridge corners, convexity, pin refusal."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_vehroutes_street2_1108 as T

ok = True


def chk(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


class FakeNav:
    def __init__(self):
        self.pv, self.en = {}, {}
        for (p, e, a, b) in (T.ALLEY, T.STREET, T.NORTH):
            vs = [(a[0], 0.0, a[1]), (b[0], 0.0, b[1])] * 2
            vs = [None] * 8
            vs[e] = (a[0], 0.0, a[1])
            vs[e + 1] = (b[0], 0.0, b[1])
            self.pv[p] = vs[:e + 2]
            self.en[p] = {e: -1}


nav = FakeNav()
br = T.nav_bridges(nav)
chk('three bridge areas', len(br) == 3)
chk('first bridge corner 0 is the alley edge end', br[0]['corners'][0][0] == 4660.0 and br[0]['corners'][1][0] == 2238.0)
chk('throat is at z 31400 and x 3500..4100', br[0]['corners'][2][2] == 31400.0 and br[0]['corners'][3][0] == 4100.0)
chk('bridges 0 and 1 are convex', all(T.convex([(c[0], c[2]) for c in b['corners']]) for b in br[:2]))
chk('north bridge reaches z 32480', br[2]['corners'][2][2] == 32480.0)
chk('convex rejects a bow tie', not T.convex([(0, 0), (1, 1), (1, 0), (0, 1)]))
bad = FakeNav()
bad.pv[T.ALLEY[0]][T.ALLEY[1]] = (0.0, 0.0, 0.0)
try:
    T.nav_bridges(bad)
    chk('a moved pinned edge is refused', False)
except ValueError:
    chk('a moved pinned edge is refused', True)
sys.exit(0 if ok else 1)
