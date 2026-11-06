"""Off-game self-test of kl_club_rmi_1106 (candidate 2f): a synthetic 60-box .rmi in the stock frame, no game files."""
import os, struct, sys, tempfile, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_octree as O
import kl_club_rmi_1106 as R

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


ORIGIN, SCALE = (135184.5, 68404.640625, 23617.09375), 0.051582202315330505


def rec(c, h, room, tail=0):
    return O.Box(struct.pack('<I9f3f3f3fII I', 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, *c, *c, *h, room, 0, 0))


def make(box7=(R.OLD_CENTRE, R.OLD_HALF), room7=R.ROOF_SLOT):
    boxes = []
    for k in range(60):
        if k == 7:
            boxes.append(rec(box7[0], box7[1], room7))
        elif k == 59:
            boxes.append(rec((0.0, 68404.640625, 0.0), (175000.0, 78404.640625, 175000.0), 2))
        elif k == 2:                                        # Roof box that touches the enlarged one at x 9266
            boxes.append(rec((10086.3, 2035.2, 3233.2), (820.2, 575.2, 660.3), R.ROOF_SLOT))
        else:                                               # far-away filler rooms (street side), distinct slots
            boxes.append(rec((-30000.0 + 900.0 * (k % 20), 1500.0, -20000.0 - 900.0 * (k // 20)), (300.0, 500.0, 300.0), 100 + k))
    items = []
    for k, b in enumerate(boxes):
        c, h = struct.unpack_from('<3f', b.raw, 0x28), struct.unpack_from('<3f', b.raw, 0x40)
        items.append([k] + O.quantise_box(ORIGIN, SCALE, [c[a] - h[a] for a in range(3)], [c[a] + h[a] for a in range(3)]))
    tree = O.build_tree(items, ORIGIN, SCALE, True)
    return O.RoomIndex(tree, boxes, 0x58).pack()


old = make()
t('synthetic rmi round-trips', O.RoomIndex.parse(old).pack() == old)
new, info = R.edit(old)
t('edit changes only box 7 (59 records byte-identical) and reads back', not info['already'] and R.check_edit(old, new) == []
  and [k for k, (a, b) in enumerate(zip(O.RoomIndex.parse(old).boxes, O.RoomIndex.parse(new).boxes)) if a.raw != b.raw] == [7])
idx = O.RoomIndex.parse(new)
t('box 7 is x 6676..9266, y 1460..6600, z 2594..4426', struct.unpack_from('<3f', idx.boxes[7].raw, 0x28) == R.NEW_CENTRE and struct.unpack_from('<3f', idx.boxes[7].raw, 0x40) == R.NEW_HALF
  and [R.NEW_CENTRE[a] - R.NEW_HALF[a] for a in range(3)] == [6676.0, 1460.0, 2594.0] and [R.NEW_CENTRE[a] + R.NEW_HALF[a] for a in range(3)] == [9266.0, 6600.0, 4426.0])
t('route 2e points and the 2e eye resolve to Roof 7 + Backdrop 59', all(R.tree_at(idx, p) == [7, 59] for p in R.ROOF_POINTS))
import kl_club_outro_1106 as OU
t('every ROUTE_2E point and the pad are inside the new box', all(R.contains(idx.boxes[7].raw, p) for p in OU.ROUTE_2E) and R.contains(idx.boxes[7].raw, (7361.0, 2014.0, 3201.0)))
t('before the edit the climb points were Backdrop only', R.tree_at(O.RoomIndex.parse(old), (8268.0, 5005.0, 3207.0)) == [59])
t('edit is idempotent', R.edit(new) == (new, {'already': True}))
t('same size, same box count', len(new) == len(old) and len(idx.boxes) == 60)
for nm, data in (('another box 7 size', make(((7400.0, 2035.2, 3510.2), R.OLD_HALF))), ('box 7 in another room', make(room7=999))):
    try:
        R.edit(data); t('edit refuses ' + nm, False)
    except ValueError:
        t('edit refuses ' + nm, True)
# a tampered result is caught
bad = O.RoomIndex.parse(new)
struct.pack_into('<3f', bad.boxes[9].raw, 0x28, 1.0, 2.0, 3.0)
t('check_edit catches a second changed record', any('differ' in x for x in R.check_edit(old, bad.pack())))
bad = O.RoomIndex.parse(new)
struct.pack_into('<3f', bad.boxes[7].raw, 0x40, 1295.0, 2000.0, 916.0)
t('check_edit catches a wrong extent', R.check_edit(old, bad.pack()) != [])
oi = O.RoomIndex.parse(old)                                                    # a street box that sits inside the new volume
struct.pack_into('<3f', oi.boxes[11].raw, 0x28, 8000.0, 5000.0, 3500.0)
oi.tree.items[11] = [11] + O.quantise_box(ORIGIN, SCALE, (7700, 4700, 3200), (8300, 5300, 3800))
oi.tree = O.build_tree([list(i) for i in oi.tree.items], ORIGIN, SCALE, True)
try:
    R.edit(oi.pack()); t('edit refuses when another room overlaps the enlarged box', False)
except ValueError as e:
    t('edit refuses when another room overlaps the enlarged box', 'overlaps' in str(e))
# zip level: only the .rmi member changes
with tempfile.TemporaryDirectory() as d:
    src, dst = os.path.join(d, 'a.zip'), os.path.join(d, 'b.zip')
    with zipfile.ZipFile(src, 'w') as z:
        z.writestr('S/F01_Main.gms', b'gms'); z.writestr('S/F01_Main.rmi', old)
        z.writestr('S/F01_Main.rmc', make()); z.writestr('S/F01_Main.oct', b'x')
    mem = R.members(src)
    t('members() keeps archive order', [m[0] for m in mem] == ['S/F01_Main.gms', 'S/F01_Main.rmi', 'S/F01_Main.rmc', 'S/F01_Main.oct'])
    try:
        R.rmi_name(['a.rmi', 'b.rmi']); t('rmi_name refuses two .rmi', False)
    except ValueError:
        t('rmi_name refuses two .rmi', True)
    try:
        R.stage(os.path.join(d, 'o'), d, allow=['deadbeef'])
        t('stage refuses an unlisted md5', False)
    except (ValueError, OSError):
        t('stage refuses an unlisted md5', not os.path.exists(os.path.join(d, 'o', 'F01_Main.zip')))
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
