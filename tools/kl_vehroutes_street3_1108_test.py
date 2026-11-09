"""Off-game self-test of kl_vehroutes_street3_1108 (no game file): wider arcs, speed profiles inside the key budgets, template pins."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_vehroutes_street3_1108 as M

ok = True


def chk(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


A, D = M.arrival_path(), M.departure_path()
chk('arrival starts at the pocket heading north and meets the lane heading east', A.at(0)[0] == M.WAIT and abs(A.at(1)[1]) < 1 and abs(A.at(A.L - 1)[1] - 90) < 1)
chk('arrival ends on the stop', abs(A.at(A.L)[0][0] - M.STOP_X) < 1 and abs(A.at(A.L)[0][1] - M.LANE_Z) < 1)
chk('departure ends at the east pocket heading south', D.at(D.L)[0] == M.END and abs(abs(D.at(D.L - 1)[1]) - 180) < 1)
chk('both turns are at least 1200 wide (were 407 / 400)', M.R_ARR >= 1200 and M.R_DEP >= 1200)
chk('the departure turn stays east of the walkable street (x >= 10700) and inside the east pocket x <= 17600', D.at(0)[0][0] == M.STOP_X and M.END[0] - M.R_DEP > 10700 and M.END[0] <= 17600)
vc, da = M.solve_arrival(A, 155)
st = [da[i + 1] - da[i] for i in range(155)]
chk('arrival: 156 keys from 0 to the full length', len(da) == 156 and da[0] == 0 and da[-1] == A.L)
chk('arrival: no step over the stock cap, arc speed below the old 116', max(st) <= M.CAP + 1e-6 and vc < 100)
chk('arrival: distances never decrease', all(x >= -1e-9 for x in st))
chk('arrival: lateral acceleration under a third of the old one (old 116^2/407)', vc * vc / M.R_ARR < 116 * 116 / 407.0 / 3)
vd, pk, dd = M.solve_departure(D, 235)
sd = [dd[i + 1] - dd[i] for i in range(235)]
chk('departure: 236 keys, last on the end', len(dd) == 236 and dd[-1] == D.L and dd[0] == 0)
chk('departure: no step over the cap, arc slower than the peak, lateral under a tenth of the old', max(sd) <= M.CAP + 1e-6 and vd < pk and vd * vd / M.R_DEP < 116 * 116 / 400.0 / 10)
chk('departure: starts from nearly rest', sd[0] < 10)
try:
    M.solve_arrival(A, 20)
    chk('an impossible key budget is refused', False)
except ValueError:
    chk('an impossible key budget is refused', True)
# the kit template carries no hard-coded live pin of its own, and the pins are the street2 files
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kl_vehroutes_street2_install_tmpl.py'), encoding='utf-8').read()
chk('install template derives LIVE_ZIP_MD5 from FILES', 'LIVE_ZIP_MD5 = FILES[0][1]' in t and not re.search(r"LIVE_ZIP_MD5 = '[0-9a-f]{32}'", t))
chk('street3 pins are the street2 outputs (778b075c / dccc9250 / 6616525a)', [v[:8] for v in M.LIVE_MD5.values()] == ['778b075c', 'dccc9250', '6616525a'])
chk('street3 backup tag differs from street2', M.TAG != '.before-vehroutes1108street2')
sys.exit(0 if ok else 1)
