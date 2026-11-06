"""Self-test of tools/kl_glass_conn.py (2026-11-06). Exit 0 only when every check passes.
Part 1 (always): the 0x4dfd60 / 0x4a45a0 port on synthetic pieces + the record codec.
Part 2 (only when Dead Men's M05A_Main.zip is on this machine): recompute the 10 shipped panes (691 records) byte for byte,
and build a section into a scratch copy and read it back."""
import os, sys, tempfile, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_glass_conn as G

DM = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\Scenes\Locations\M05_A\M05A_Main.zip'
bad = []


def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c:
        bad.append(m)


# --- synthetic pieces: 0 and 1 touch at 2.4 (< 2.5), 2 at exactly 2.5 from 1 (strict: not a neighbour), 3 far, 4 has NaN
P = [[(0, 0, 0)], [(2.4, 0, 0)], [(4.9, 0, 0)], [(100, 0, 0)], [(float('nan'),) * 3], [(0, 0, 2.4), (50, 50, 50)]]
nb = G.neighbours(P)
ok(nb[0] == [1, 5], 'piece 0 -> [1, 5]: %s' % nb[0])
ok(nb[1] == [0], 'piece 1 -> [0] (2.4 to 0, 2.5 to 2 is not below the threshold): %s' % nb[1])
ok(nb[2] == [] and nb[3] == [] and nb[4] == [], 'pieces 2, 3, 4 (far / NaN) have none')
ok(nb[5] == [0], 'piece 5 -> [0]: %s' % nb[5])
# cap 16 and ascending order
hub = [[(0, 0, 0)]] + [[(1, i * 0.01, 0)] for i in range(20)]
h = G.neighbours(hub)
ok(h[0] == list(range(1, 17)), 'hub keeps the first 16 neighbours ascending')
# codec
r = G.encode([3, 9, 12])
ok(len(r) == 40 and r[0] == 3 and r[1] == 7 and r[2:4] == b'\xcd\xcd' and r[4:8] == bytes(4) and r[14:] == b'\xff' * 26, 'record layout')
ok(G.decode(r) == (3, 7, [3, 9, 12]), 'decode(encode) round trip')
r = G.encode(list(range(16)))
ok(r[1] == 0xff and r[0] == 16 and G.decode(r)[2] == list(range(16)), 'mask stays 8 bit with 16 neighbours')
ok(G.encode([]) == bytes([0, 0, 0xcd, 0xcd]) + bytes(4) + b'\xff' * 32, 'empty record')

# --- shipped data
if os.path.isfile(DM):
    n, tot, eq, peq, bad_panes = G.compare(DM)
    ok(n == 10 and tot == 691 and eq == tot and peq == n, 'M05A shipped: %d panes, %d records, %d equal' % (n, tot, eq))
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 'o.zip')
        items = G.insert(DM, out, force=True)
        with zipfile.ZipFile(out) as zf:
            sc, prm, sgd = G.load(zf)
            have = G.section_of(zf, sgd)
        ok(have is not None and len(have) == len(items) == len(G.groups(sc)), 'built section covers every shard group (%d)' % len(items))
        ok(dict((a, b) for a, b in have) == dict((a, b) for a, b in items), 'section reads back as written')
else:
    print('skip M05A comparison: %s not on this machine' % DM)

print('%d check(s) failed' % len(bad) if bad else 'all passed')
sys.exit(1 if bad else 0)
