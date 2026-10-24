#!/usr/bin/env python3
"""
INTERACTIVITY CENSUS (2026-10-24, owner: "doors you can boot down, fire extinguishers, co-op shutters, more open shops,
scripted vehicles ... maps need to feel interactive and alive"). OFFLINE and READ-ONLY: starts nothing, installs nothing,
writes no zip. Plan and findings: re/interactivity.md.

    python kl_interact.py census                 the 9 stock FA maps (F01..F09): interactive templates, how many of each
    python kl_interact.py survey <zip> [...]     the same for finished Dead Men zips (default: every DM zip under KLExpansion\\Maps)
    python kl_interact.py wiring <level|zip> <name regex> [--limit N]   fields of the matching nodes (REF labels, refs, strings)
    python kl_interact.py gaps                   per DM map: which stock interactive classes it has NONE of (= graft needed)

The table is by NODE NAME (the Glacier entity path) because the stock templates carry their kind in the name
('KickDoor', 'Extinguisher', 'CoopAirlock', 'Shutter' ...) and by CONTROLLER (BarrelEffects, KickDoorBehaviourRout ...).
Nothing here is guessed: the rows are counted from the .prp token streams through kl_prpjoin.
"""
import collections, glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prpjoin as J

MAPS = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps'
STOCK = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09']

# controller classes that make a map "interactive" and what each is
CTRL = collections.OrderedDict([
    ('KickDoorBehaviourRout', 'AI kicks this door open (7 F01, 28 F03, 21 F06 in stock)'),
    ('KickDoorBehaviour_PosInfo', 'where the AI stands to kick'),
    ('BarrelEffects', 'explosive barrel / extinguisher / gas can: the blast, fire and smoke'),
    ('Throwable', 'a Havok can the player can pick up and throw'),
    ('HavokShatter', 'glass / board / crate that breaks (shot or blast)'),
    ('ShotActivate', 'a shot switches the targets on'),
    ('ActivateGeom', 'show a hidden mesh or switch on a body'),
    ('DeactivateGeom', 'hide a mesh / drop its collision'),
    ('PathBlocker', 'the AI route is shut until a message opens it'),
    ('Blocker', 'a movement blocker'),
    ('OnlineMoneyContainer', 'a loot CASE: closed until a message opens it'),
    ('OnlineMoneyCtrl', 'a loot stack (pick-up)'),
    ('RelayMessageList', 'a list of nodes sent one message (AITrigger Open, DoorOpened)'),
    ('MatPosAnimProxy', 'a key-framed door / shutter that another node plays'),
    ('MatPosAnim', 'a key-framed mesh (door leaf, shutter, lift)'),
    ('CoverStateChanger', 'cover on / off with the object (barricade, car)'),
    ('AIDWrapper', 'AI-path door wrapper'),
    ('KickDoor', 'the player kick door (ZKickDoorController, 11 fields)'),
    ('KickDoorMonitor', 'relay that tells the AI the door opened'),
    ('CoopAirlock', 'the co-op lift shutter (ZCOOPAirlockController, two boxes, both players)'),
    ('VehicleEffects', 'a car with blast effects'),
    ('OnlineEscHavokCar', 'the escape car'),
    ('HeliFlyBehaviourRout', 'a scripted helicopter'),
])
NAME_RE = re.compile(r'kickdoor|extingu|airlock|shutter|alarm|gascan|barrel|propane|rollerdoor|grate|lift', re.I)


def scene(x):
    if x.lower().endswith('.zip'):
        return J.Scene.from_zip(x, 'dm' if 'DM' in os.path.basename(os.path.dirname(x)) else 'dd')
    return J.Scene.load(x)


def count(sc):
    c, names = collections.Counter(), collections.Counter()
    for k in range(1, len(sc.nodes)):
        for nm, _b in sc.nodes[k]['ctrls']:
            c[sc.p.key(nm)] += 1
        m = NAME_RE.search(sc.names[k])
        if m:
            names[m.group(0).lower()] += 1
    return c, names


def table(rows):
    keys = list(CTRL)
    print('%-12s %7s ' % ('map', 'nodes') + ' '.join('%4s' % ('c%d' % i) for i in range(len(keys))))
    for lab, nn, c, _n in rows:
        print('%-12s %7d ' % (lab, nn) + ' '.join('%4d' % c.get(k, 0) for k in keys))
    print('columns:', ', '.join('c%d=%s' % (i, k) for i, k in enumerate(keys)))
    print('names (regex %s):' % NAME_RE.pattern)
    for lab, _nn, _c, n in rows:
        print('  %-12s %s' % (lab, dict(n)))


def dm_zips():
    return sorted(glob.glob(os.path.join(MAPS, 'DM*', 'F0*_Main.zip')))


def cmd_census(args):
    rows = []
    for L in STOCK:
        sc = scene(L)
        c, n = count(sc)
        rows.append((L, len(sc.nodes), c, n))
    table(rows)


def cmd_survey(args):
    zs = args or dm_zips()
    rows = []
    for z in zs:
        sc = scene(z)
        c, n = count(sc)
        rows.append((os.path.basename(os.path.dirname(z)), len(sc.nodes), c, n))
    table(rows)


def cmd_gaps(args):
    need = ['KickDoorBehaviourRout', 'BarrelEffects', 'Throwable', 'OnlineMoneyContainer', 'PathBlocker', 'HavokShatter']
    for z in dm_zips():
        sc = scene(z)
        c, _n = count(sc)
        print('%-10s none of: %s' % (os.path.basename(os.path.dirname(z)), ', '.join(k for k in need if not c.get(k)) or '-'))


def cmd_wiring(args):
    lim = 20
    if '--limit' in args:
        i = args.index('--limit')
        lim = int(args[i + 1])
        del args[i:i + 2]
    sc = scene(args[0])
    rx = re.compile(args[1], re.I)
    n = 0
    for k in range(1, len(sc.nodes)):
        if rx.search(sc.path[k]):
            n += 1
            if n > lim:
                continue
            print(k, sc.cls(k), sc.path[k][-110:], [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']])
            for h, lab, u in J.fields(sc, k):
                if not lab.startswith('?'):
                    print('     ', h, lab, J.strings(sc, u) or [(op, pl[:8].hex()) for op, pl in u][:5])
    print('matches', n)


def main():
    a = sys.argv[1:]
    cmds = {'census': cmd_census, 'survey': cmd_survey, 'gaps': cmd_gaps, 'wiring': cmd_wiring}
    if not a or a[0] not in cmds:
        print(__doc__)
        return 2
    cmds[a[0]](a[1:])
    return 0


if __name__ == '__main__':
    sys.exit(main())
