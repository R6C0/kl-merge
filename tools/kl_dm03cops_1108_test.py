"""Off-game self-test of kl_dm03cops_1108's backswat part (2026-11-09): the pure planning / validation functions on synthetic inputs. No game files.
Also pins what keeps the 1108 stage byte-identical: DEFAULT_PARTS leaves backswat out, backswat runs alone, its own clock / out dir / tag."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_dm03cops_1108 as D

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ValueError:
        return True
    return False


# ---- parts
t('backswat is a part but not a default part', 'backswat' in D.PARTS and 'backswat' not in D.DEFAULT_PARTS and D.DEFAULT_PARTS == D.PARTS[:5])
t('default parts validate', D.validate_parts(D.DEFAULT_PARTS) == [])
t('backswat alone validates', D.validate_parts(('backswat',)) == [])
t('backswat with another part is refused', any('alone' in p for p in D.validate_parts(('garage', 'backswat'))))
t('unknown part is refused', any('unknown' in p for p in D.validate_parts(('garage', 'swatx'))))
t('no parts is refused', D.validate_parts(()) != [])
t('own clock / squad / out / tag names', D.BS_CLOCK != D.CLOCK and D.BS_VAN not in (D.GARAGE, D.RAMP) and D.OUT_BS != D.OUT and D.TAG_BS != D.TAG)
t('BS_INPUTS pins the cops output and the doors output', len(D.BS_INPUTS) == 2 and all(len(a) == 32 and len(b) == 32 for a, b in D.BS_INPUTS))

# ---- SWAT template choice (candidates = (k, path, model, anm) in node order)
BS = chr(92)
cands = [
    (7036, 'AI_Enemies!ParkingLotSWAT_01' + BS + 'cop_#01' + BS + 'Ground', 59361, 'Characters#Police'),       # the lot men: police after frontcops
    (6953, 'AI_Enemies!ArrivingCops_Squad_02' + BS + 'Reinforcement_03' + BS + 'Ground', 59361, 'Characters#Police'),
    (6801, 'AI_Enemies!ArrivingCops_Squad_01' + BS + 'Reinforcement_01' + BS + 'Ground', 59891, 'Characters#Swat'),
    (6803, 'AI_Enemies!ArrivingCops_Squad_01' + BS + 'Reinforcement_02' + BS + 'Ground', 59891, 'Characters#Swat'),
    (7113, 'AI_Enemies!LoadingDock' + BS + 'Guard' + BS + 'Ground', 60016, 'Characters#Guard'),
    (6700, 'AI_Enemies!EscSquad' + BS + 'Esc_01' + BS + 'Ground', 59891, 'Characters#Swat'),
    (6710, 'AI_Enemies!EscSquadX' + BS + 'Esc_01' + BS + 'Ground', 59891, 'Characters#Swat'),                      # a name that only STARTS like a template squad
]
got = D.pick_templates(cands)
t('templates: the 59891 men under the template squads, node order', [c[0] for c in got] == [6801, 6803, 6700])
t('a squad whose name only starts like a template squad is not one', 6710 not in [c[0] for c in got])
t('a police-set man of the right model is refused as template', not D.fits_template((1, 'AI_Enemies!EscSquad' + BS + 'x', 59891, 'Characters#Police')))
t('no template -> ValueError', raises(D.pick_templates, cands[:2]))
t('SWAT dict: model 59891 from police 59361, fields 4/10/20', D.SWAT['model'] == 59891 and D.SWAT['from_model'] == 59361 and tuple(D.SWAT['fields']) == (4, 10, 20))

# ---- weapons
t('weapon_cycle round robin, duplicates removed', D.weapon_cycle(['a', 'b', 'a'], 5) == ['a', 'b', 'a', 'b', 'a'])
t('weapon_cycle refuses an empty pool', raises(D.weapon_cycle, [], 3))

# ---- budget
t('budget: cops output 44 / 29 + 4 men + 1 squad fits 99 / 55', D.budget_ok(44, 29, 4, 1))
t('budget: 96 actors + 4 does not', not D.budget_ok(96, 29, 4, 1))
t('budget: 55 squads + 1 does not', not D.budget_ok(44, 55, 4, 1))


# ---- van cells on a fake mesh: a 40 cm grid floor x -1000..3000, z -1000..1000 at y 133 (part 0), walls at z = +-1000
class FakeNav:
    def __init__(self, bad=()):
        self.bad = set(bad)

    def around(self, p, radius, part, step=40.0, dy=80.0):
        out, k = [], int(radius // step)
        for ix in range(-k, k + 1):
            for iz in range(-k, k + 1):
                x, z = p[0] + ix * step, p[2] + iz * step
                if math.hypot(ix, iz) * step > radius or not (-1000 <= x <= 3000 and -1000 <= z <= 1000) or (round(x), round(z)) in self.bad:
                    continue
                out.append((x, 133.0, z, 0))
        return out

    def clearance(self, x, y, z, limit=400.0):
        return min(limit, 1000.0 - abs(z))

    def spots(self, cands, n, sep, ref=None, clear=60.0):
        out = []
        for c in sorted(cands, key=lambda c: math.dist(c[:3], ref[:3])):
            if len(out) >= n:
                break
            if self.clearance(c[0], c[1], c[2]) >= clear and all(math.hypot(c[0] - o[0], c[2] - o[2]) >= sep for o in out):
                out.append(c)
        return out


nav = FakeNav()
anchor = (1000.0, 133.0, 0.0)
lane = [[(-1000.0, 133.0, 0.0), (3000.0, 133.0, 0.0)]]          # the van drives along z = 0 through the anchor
cells = D.plan_van_cells(nav, anchor, 0, D.VAN_SWAT, lane)
t('van cells: exactly n', len(cells) == D.VAN_SWAT['n'])
t('van cells: all at least keep_off from the anchor and within radius', all(D.VAN_SWAT['keep_off'] <= math.hypot(c[0] - anchor[0], c[2] - anchor[2]) <= D.VAN_SWAT['radius'] for c in cells))
t('van cells: all lane_clear off the lane (|z| >= 250)', all(abs(c[2]) >= D.VAN_SWAT['lane_clear'] for c in cells))
t('van cells: sep kept', all(math.hypot(a[0] - b[0], a[2] - b[2]) >= D.VAN_SWAT['sep'] for i, a in enumerate(cells) for b in cells[i + 1:]))
t('van cells: on the floor height', all(c[1] == 133.0 for c in cells))
box = lambda p: abs(p[0] - 1000.0) <= 400 and abs(p[2]) <= 400           # an escape box round the anchor
cells2 = D.plan_van_cells(nav, anchor, 0, D.VAN_SWAT, lane, in_escape=box)
t('van cells: none inside the escape box', all(not box(c) for c in cells2))
t('van cells: an anchor off the floor -> ValueError', raises(D.plan_van_cells, nav, (9000.0, 133.0, 0.0), 0, D.VAN_SWAT, lane))
tight = dict(D.VAN_SWAT, radius=600.0, keep_off=550.0, sep=2000.0)
t('van cells: too few spots -> ValueError (never a short squad)', raises(D.plan_van_cells, nav, anchor, 0, tight, lane))
t('VAN_SWAT anchor is a van_drives key', D.VAN_SWAT['anchor'] in ('stop', 'wait', 'end', 'board'))

print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
