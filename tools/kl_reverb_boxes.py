#!/usr/bin/env python3
"""kl_reverb_boxes.py - the reverb-box table for klhook's [Echo] RoomBoxes (2026-11-08). OFFLINE: reads map zips, writes ONE text file to --out.

    python tools/kl_reverb_boxes.py --out C:/kl_build_1024/roomboxes_1108/KLReverbBoxes.ini            9 stock FA maps + every KLExpansion map
    python tools/kl_reverb_boxes.py --out t.ini --no-expansion                                         the 9 stock maps only
    python tools/kl_reverb_boxes.py --out t.ini --map f01\\f01_main=<zip> --map dm02=<zip> --no-stock --no-expansion

WHY. In Fragile Alliance every stock CCheckInside reverb box ends itself at load (re/reverb_path_1108.md), so the engine's reverb stack stays empty and
the sound system gets the I3DL2 default every frame. klhook ([Echo] RoomBoxes=1, klecho.c) tests the local hero against the boxes itself and calls the
engine's own AUD::Push / AUD::Remove. It needs, per map: where each box is, how it is turned, which roomeffect it selects and its priority.

SOURCE. Every Audio_ReverbActivater controller of the map zip (stock 'Audio!BOX!..' boxes AND the 'KL_Reverb!' boxes tools/kl_dm_reverb.py adds to Dead Men
maps) on a ZBoxPrimitive: field 0 = the SND offset of the roomeffect (valid only for that map's .SND), field 3 = the float priority. The box = the node's
own frame (kl_fa_bots.Built.fr: world = R * local + T) and its ZBoxPrimitive[0..2] half extents. The file stores the WORLD->LOCAL rotation Q = R^T, row
major, so klhook tests `local = Q * (p - centre)` without a matrix inverse.

FILE (klreverbbox_logic.h has the reader; one text file for all maps, written by the owner's install step, never by this tool into the game folder):
    [f01\\f01_main]            stock level: the scene key, lower case (klh_level_key); an expansion map: the lower-case folder name, e.g. [dm02]
    box cx cy cz hx hy hz q0 q1 q2 q3 q4 q5 q6 q7 q8 snd prio  ; <box name>
A map without any box has its section and no box line (it is KNOWN to have none; klhook then does nothing for it).

GUESSES (also marked where used):
  * the node origin is the box centre (the stock boxes are authored that way: spawns land inside the boxes named after their room, see spawn_report()).
  * a node frame has no scale (the tool warns when a column of R is not unit length; the table then holds the unit-length rotation of the normalised axes).
  * one ZBoxPrimitive may carry two Audio_ReverbActivater controllers (none seen): each becomes its own line.
"""
import argparse
import glob
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DD_DEFAULT = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
STOCK = ['F%02d' % i for i in range(1, 10)]


# ------------------------------------------------------------------ pure part (no game files; the self-test uses only this)
def fmt(x, nd=4):
    s = ('%.*f' % (nd, x)).rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


def box_line(b):
    """One 'box ...' line from a dict {name, c(3), h(3), q(9), snd, prio}."""
    nums = [fmt(v) for v in b['c']] + [fmt(v) for v in b['h']] + [fmt(v, 6) for v in b['q']] + [str(int(b['snd'])), fmt(b['prio'], 3)]
    return 'box ' + ' '.join(nums) + '  ; ' + re.sub(r'[\r\n]', ' ', b.get('name', ''))


def emit(sections, header=True):
    """{section key: [box dict]} -> text (sections in the given order if an OrderedDict / list of pairs, else sorted)."""
    items = list(sections.items()) if hasattr(sections, 'items') else list(sections)
    out = []
    if header:
        out += ['; KLReverbBoxes.ini - written by tools/kl_reverb_boxes.py; read by klhook ([Echo] RoomBoxes=1, klreverbbox_logic.h).',
                '; [map] = the stock scene key (f01\\f01_main) or the lower-case KLExpansion folder (dm02).',
                '; box cx cy cz hx hy hz q0..q8 snd prio  ; name      q = world->local rotation, row major; snd = SND offset of that map; prio: the highest wins', '']
    for key, boxes in items:
        out.append('[%s]' % key.lower())
        out += [box_line(b) for b in boxes]
        out.append('')
    return '\n'.join(out)


def parse(text):
    """Text -> {section key (lower): [box dict]} (the same reading klreverbbox_logic.h does; bad box lines raise ValueError)."""
    res, cur = {}, None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        name = ''
        if not line or line[0] in ';#':
            continue
        m = re.match(r'\[\s*([^\]]*?)\s*\]', line)
        if m:
            cur = m.group(1).lower()
            res.setdefault(cur, [])
            continue
        if cur is None or not re.match(r'box[ \t]', line):
            continue
        body, _s, name = line.partition(';')
        v = body.split()[1:]
        if len(v) != 17:
            raise ValueError('line %d: a box line has 17 numbers, this one has %d' % (n, len(v)))
        f = [float(x) for x in v]
        if min(f[3:6]) < 0 or f[15] < 0:
            raise ValueError('line %d: negative half extent or snd' % n)
        res[cur].append({'name': name.strip(), 'c': f[0:3], 'h': f[3:6], 'q': f[6:15], 'snd': int(f[15]), 'prio': f[16]})
    return res


def inside(b, p, margin=0.0):
    """Is world point p inside box b (dict as parse() gives)? margin > 0 widens, < 0 shrinks (at most to half), as klrb_inside."""
    d = [p[i] - b['c'][i] for i in range(3)]
    for i in range(3):
        l = sum(b['q'][3 * i + j] * d[j] for j in range(3))
        e = b['h'][i] + margin
        if margin < 0 and e < 0.5 * b['h'][i]:
            e = 0.5 * b['h'][i]
        if not (-e <= l <= e):
            return False
    return True


def q_from_frame(R):
    """World->local rotation Q = R^T from a node frame R (world = R * local + T, kl_fa_bots.Built.fr) -> (Q row-major 9 floats, worst axis-length error)."""
    Q = [R[j][i] for i in range(3) for j in range(3)]
    err = 0.0
    for j in range(3):                                     # column j of R = the local axis j in the world: unit length when there is no scale
        err = max(err, abs(math.sqrt(sum(R[i][j] ** 2 for i in range(3))) - 1.0))
    return Q, err


# ------------------------------------------------------------------ the map zips
def collect(zp, log=print):
    """[box dict] of every Audio_ReverbActivater box of a map zip (needs the game's zip; imports the build tools lazily)."""
    import kl_fa
    import kl_fa_bots as F
    B = F.Built(zp)
    sc = B.sc
    out = []
    for k, _i, v in kl_fa.controllers(sc, 'Audio_ReverbActivater'):
        if sc.cls(k) != 'ZBoxPrimitive':
            log('  skipped %s: an Audio_ReverbActivater on a %s, not a box' % (sc.names[k], sc.cls(k)))
            continue
        R, T = B.fr[B.ents[k - 1]]
        h = [abs(x) for x in B.box(k)]
        Q, err = q_from_frame(R)
        if err > 1e-3:
            log('  WARNING %s: node frame has scale (axis length off by %.4f); rotation stored as given' % (sc.names[k], err))
        out.append({'name': sc.names[k], 'c': [float(x) for x in T], 'h': [float(x) for x in h], 'q': [float(x) for x in Q],
                    'snd': int(v[0]), 'prio': float(v[3])})
    return out


def spawn_report(zp):
    """{box name: spawns inside} of a map: a check that centre + half extents + rotation describe real rooms (needs the game's zip)."""
    import kl_fa_bots as F
    B = F.Built(zp)
    boxes = collect(zp, log=lambda *_: None)
    cnt = {}
    for s in range(1, len(B.sc.names)):
        if B.sc.cls(s) == 'ZSpawnPoint':
            p = B.world(s, (0.0, 0.0, 0.0))
            for b in boxes:
                if inside(b, p):
                    cnt[b['name']] = cnt.get(b['name'], 0) + 1
    return cnt


def stock_maps(dd):
    return [('f%02d\\f%02d_main' % (i, i), os.path.join(dd, 'Scenes', 'Locations', 'F%02d' % i, 'F%02d_Main.zip' % i)) for i in range(1, 10)]


def expansion_maps(dd):
    """[(folder lower, zip)] of KLExpansion/Maps/<folder>/F??_Main.zip (the plain zip; the .bots.zip sibling is not a level of its own)."""
    out = []
    for d in sorted(glob.glob(os.path.join(dd, 'KLExpansion', 'Maps', '*'))):
        zs = sorted(z for z in glob.glob(os.path.join(d, 'F*_Main.zip')) if re.search(r'F\d\d_Main\.zip$', z, re.I))
        if len(zs) != 1:
            if zs:
                print('  %s: %d candidate zips, skipped (give it with --map)' % (os.path.basename(d), len(zs)))
            continue
        out.append((os.path.basename(d).lower(), zs[0]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', required=True, help='the table file to write (never the game folder from here; the install step copies it)')
    ap.add_argument('--dd', default=DD_DEFAULT, help='Dog Days folder (read only)')
    ap.add_argument('--no-stock', action='store_true')
    ap.add_argument('--no-expansion', action='store_true')
    ap.add_argument('--map', action='append', default=[], metavar='KEY=ZIP', help='one more section (KEY as the file wants it)')
    a = ap.parse_args(argv)
    maps = []
    if not a.no_stock:
        maps += stock_maps(a.dd)
    if not a.no_expansion:
        maps += expansion_maps(a.dd)
    for m in a.map:
        k, _s, z = m.partition('=')
        maps.append((k, z))
    sections, report = [], []
    for key, zp in maps:
        if not os.path.isfile(zp):
            print('%-14s MISSING %s' % (key, zp))
            continue
        boxes = collect(zp)
        sections.append((key, boxes))
        report.append((key, len(boxes), len({b['snd'] for b in boxes})))
        print('%-14s %2d boxes, %d distinct effects  (%s)' % (key, len(boxes), len({b['snd'] for b in boxes}), zp))
    text = emit(sections)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', newline='\n') as f:
        f.write(text)
    back = parse(text)
    if [k for k, _ in sections] != list(back) or any(len(back[k]) != len(b) for k, b in sections):
        sys.exit('round trip failed: the written file does not read back the same')
    print('wrote %s: %d maps, %d boxes' % (a.out, len(sections), sum(len(b) for _k, b in sections)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
