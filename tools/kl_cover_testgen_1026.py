"""kl_cover_testgen_1026.py - generate a live cover test ini (COVER16_<MAP>.ini; COVER14 had no NO_DAMAGE, COVER15 one attempt) for one expansion map (2026-10-26). OFFLINE: reads files, writes one ini.

Usage:  python tools/kl_cover_testgen_1026.py <MAP> [--n 8] [--out C:/kl_build_1024/live_1026] [--plans C:/kl_build_1024/cover_fix_1026d]
        python tools/kl_cover_testgen_1026.py all          (every map that has a staged plan)

Per map the ini is COVER13.ini's header ([KLHook] .. [CoverDump] .. [Auto], everything before [Script]) plus a [Script] made of
  1. the map-selection part COPIED from <out>/<MAP>.ini (the smoke ini: menu taps, 'sel HeistLevel_Px 0xceceec <i>', 'expect', and its
     'msg HeistLevel_Px StartGame' line). Page 2 maps (DM01 DM02 DM03 DM03A DM06 DM09) wait for HeistPlayMenu2, page 3 maps (DM05A DM06B
     DM07 DM11B DD10 DM01B) for HeistPlayMenu3; the number of DOWN taps differs by page. Nothing is hard-coded here, the part of the smoke
     script up to its 'expect' line is taken verbatim. A map without a smoke ini, or whose script has no sel/expect/msg StartGame line, is refused.
  2. load + 23 s, the COVER LIST peeks, idle 15 s (as COVER13).
  3. up to N blocks (tags k1..kN) in COVER13's per-box pattern: tele to stand (y = ground + 5), wait 1500, pos, face the face point, wait 700,
     peek movement id, tap C 400, wait 2000, log CHECK, peek, pos, tap C 400, wait 1500.
  4. 'log COVER16_<MAP> DONE' and 'pass 1000'.
Tiles come from <plans>/<MAP>/stage/cover_plan.json (list of dicts: name, kind, mid, ext = [along-face, depth], face_normal [x,z],
stand [x, ground, z], ground). Face point = stand - 50 * face_normal (the face centre; the stand point is 50 OUT of the face along the normal;
COVER13's lines agree: k46 stand z -2685, normal -1, face z -2635).
Choice (deterministic): one thin/short tile (smallest ext[0], only if < LONG) seeds the set, then farthest-point sampling by mid (x,z) over the
long pool (kind high, ext[0] >= LONG; relaxed to kind high, then to all, when the pool is smaller than N). Without a thin tile the seed is the
tile nearest the centroid. Ties break on name.
Verdict: cover14_verdict.py <KLHook.log> [MAP] (in the same folder as the inis).
"""
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = 'C:/kl_build_1024/live_1026'
PLANS = 'C:/kl_build_1024/cover_fix_1026d'
MAPS = ['DM01B', 'DM06', 'DM06B', 'DM07', 'DM09', 'DM11B', 'DD10', 'DM03A', 'DM01', 'DM02', 'DM03']
LONG = 100.0
GROUND_BAND = 800.0    # max |ground - median ground| of a chosen tile
LEAD_WAIT = 23000       # after 'waitload', as COVER13
IDLE_MS = 15000
BLOCK_MS = 2 * (4000 + 700 + 400 + 2000 + 400 + 3000)     # the waits of one block, two attempts (the taps/peeks/face add a little)
TAG = 'COVER16'         # COVER16 = two attempts per block, longer settles (see block()); COVER15 = COVER14 + no_damage_to_you(): in COVER14 police downed the test player on DM01B/DM06/DM06B and a down blocks cover
# [Balance] keys set in the test ini: police / point-blank / crew damage to the local player 0; Ramp=0 or CopToYou would be raised to stock
NO_DAMAGE = [('Ramp', '0'), ('CopToYou', '0.0'), ('PointBlankToYou', '0.0'), ('CrewToYou', '0.0')]


def read_lines(p):
    return open(p, encoding='utf-8', errors='replace').read().replace('\r\n', '\n').split('\n')


def split_ini(lines):
    """-> (header lines before '[Script]', script lines as a list of text after the '<n>=' key)"""
    i = lines.index('[Script]')
    body = []
    for l in lines[i + 1:]:
        m = re.match(r'^(\d+)=(.*)$', l)
        if m:
            body.append((int(m.group(1)), m.group(2)))
    return lines[:i], body


def selection_part(smoke_path):
    """The smoke ini's script up to and including its 'expect' line, plus its 'msg HeistLevel_Px StartGame' line. Verifies the structure."""
    if not os.path.isfile(smoke_path):
        raise SystemExit('no smoke ini %s: map selection unknown' % smoke_path)
    _, body = split_ini(read_lines(smoke_path))
    cmds = [t for _, t in body]
    ie = next((i for i, t in enumerate(cmds) if t.startswith('expect ')), None)
    if ie is None or not any(t.startswith('sel HeistLevel_') for t in cmds[:ie]):
        raise SystemExit('%s: no sel/expect pair, selection differs from COVER13 structure' % smoke_path)
    msg = next((t for t in cmds[ie:] if re.match(r'msg HeistLevel_P\d StartGame', t)), None)
    if msg is None:
        raise SystemExit('%s: no msg HeistLevel_Px StartGame after expect' % smoke_path)
    return cmds[:ie + 1], msg


def no_damage_to_you(hdr):
    """Set NO_DAMAGE inside the header's [Balance] section (replacing the keys it already has, adding the rest after its first line)."""
    i = hdr.index('[Balance]')
    j = next((k for k in range(i + 1, len(hdr)) if hdr[k].startswith('[')), len(hdr))
    keys = dict(NO_DAMAGE)
    sec = [l for l in hdr[i + 1:j] if l.split('=', 1)[0] not in keys]
    return hdr[:i + 1] + ['%s=%s' % kv for kv in NO_DAMAGE] + sec + hdr[j:]


def d2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def choose(tiles, n):
    """Deterministic spread choice, see the module docstring. -> list of tiles (thin one first when present)."""
    # Reviewed 2026-10-26: drop tiles whose ground is far from the map's median ground (plans hold -980 / 21000 grounds; a tele to ground+5
    # there can drop the player into the void and kill every later block). Only when enough tiles remain.
    gs = sorted(t['ground'] for t in tiles)
    med = gs[len(gs) // 2]
    near = [t for t in tiles if abs(t['ground'] - med) <= GROUND_BAND]
    if len(near) >= n:
        tiles = near
    tiles = sorted(tiles, key=lambda t: t['name'] or '')
    xz = lambda t: (t['mid'][0], t['mid'][2])
    thin = [t for t in tiles if t['ext'][0] < LONG]
    thin = min(thin, key=lambda t: (t['ext'][0], t['name'] or '')) if thin else None
    pool = [t for t in tiles if t['kind'] == 'high' and t['ext'][0] >= LONG]
    if len(pool) < n:
        pool = [t for t in tiles if t['kind'] == 'high' and t is not thin] or tiles
    if len(pool) < n:
        pool = [t for t in tiles if t is not thin]
    pool = [t for t in pool if t is not thin]
    chosen = []
    if thin:
        chosen.append(thin)
    elif pool:
        cx = sum(xz(t)[0] for t in tiles) / len(tiles); cz = sum(xz(t)[1] for t in tiles) / len(tiles)
        s = min(pool, key=lambda t: (d2(xz(t), (cx, cz)), t['name'] or ''))
        chosen.append(s); pool.remove(s)
    while pool and len(chosen) < n:
        best = max(pool, key=lambda t: (min(d2(xz(t), xz(c)) for c in chosen), -ord((t['name'] or ' ')[-1])))
        chosen.append(best); pool.remove(best)
    return chosen


def block(tag, t):
    """COVER16 (2026-10-26 triage of the COVER14/15 NOs, workflow w5j0dddil): no box fault found; the NOs were carry-over from the block
    before (the second C leaves cover ~0.8 s late and the next tele lands in that state) and taps ~2 s after the tele when no face steering ran.
    So: wait 4000 after each tele, wait 3000 after the exit C, and a second attempt (b) with a fresh tele and the face aimed 30 degrees off
    the face centre (bearing errors of 19-180 degrees all gave cover). Verdict: COVER if either attempt's after-C peek reads 8."""
    sx, g, sz = t['stand']; nx, nz = t['face_normal']
    fx, fz = sx - 50 * nx, sz - 50 * nz
    c, sn = math.cos(math.radians(30)), math.sin(math.radians(30))
    ox, oz = sx - 50 * (nx * c - nz * sn), sz - 50 * (nx * sn + nz * c)      # face point rotated 30 degrees about the stand
    r = lambda v: int(round(v))
    out = ['log === %s: %s %s ext %.0fx%.0f y %.1f stand (%.1f,%.1f) face (%.1f,%.1f) ===' % (tag, t['name'], t['kind'], t['ext'][0], t['ext'][1], g, sx, sz, fx, fz)]
    for att, (px, pz) in (('1', (fx, fz)), ('b', (ox, oz))):
        out += [
            'tele %d %d %d' % (r(sx), r(g + 5), r(sz)),
            'wait 4000',
            'pos %s%s-at-stand' % (tag, att),
            'face %d %d 6 4000' % (r(px), r(pz)),
            'wait 700',
            'peek 0xdd265c+828+6b4+44 %s-%s-before-C-movement-id(secondary)' % (tag, att),
            'tap C 400',
            'wait 2000',
            'log %s CHECK %s' % (tag, att),
            'peek 0xdd265c+828+6b4+44 %s-%s-after-C-movement-id(secondary)' % (tag, att),
            'pos %s%s-after-C' % (tag, att),
            'tap C 400',
            'wait 3000',
        ]
    return out


def build(map_id, n=8, out=OUT, plans=PLANS):
    plan = os.path.join(plans, map_id, 'stage', 'cover_plan.json')
    tiles = json.load(open(plan))
    sel, msg = selection_part(os.path.join(out, map_id + '.ini'))
    ch = choose(tiles, n)
    hdr, _ = split_ini(read_lines(os.path.join(out, 'COVER13.ini')))
    hdr = no_damage_to_you(hdr)
    hdr[0] = ('; ' + TAG + ' %s (2026-10-26): generated by tools/kl_cover_testgen_1026.py from COVER13.ini (header) and %s.ini (map selection). %d K6 tiles '
              'of %d staged, spread over the map (first = thin/short if any). Same op sequence as COVER13: tele to a stand point 50 outside the face, face it, C, C. '
              'Police / crew damage to you 0 ([Balance] %s). Verdict = cover14_verdict.py.' % (map_id, map_id, len(ch), len(tiles), ' '.join('%s=%s' % kv for kv in NO_DAMAGE)))
    s = list(sel)
    s += ['log ' + TAG + '_%s: %s - [CoverDump] run: %d blocks k1..k%d: %s' % (map_id, map_id, len(ch), len(ch), ' '.join('k%d=%s' % (i + 1, t['name']) for i, t in enumerate(ch))),
          msg, 'waitload 300000', 'log level loaded: %s' % map_id, 'wait %d' % LEAD_WAIT,
          'peek 0x168e598+0x70 session-state-must-be-0x19',
          'peek 0xdd265c+898 gamedata-selected-player-byte-must-be-00-in-low-byte',
          'pos spawn',
          'log === COVER LIST (engine: L=[gd+0x15a0]; records [L+0x74] stride 0xa8; point vector [L+0x44]..[L+0x48] stride 0x7c; dropped-points counter 0x156b27c) ===',
          'peek 0xdd265c+15a0+74 coverlist-record-count',
          'peek 0xdd265c+15a0+44 coverlist-point-vec-begin',
          'peek 0xdd265c+15a0+48 coverlist-point-vec-end',
          'peek 0x156b27c coverlist-dropped-points-global']
    if ch:
        s.append('ents %s 3' % ch[0]['name'])
    s += ['log === ' + TAG + ': idle %d s at the spawn (coverdump dumps after the list is stable 2 s) ===' % (IDLE_MS // 1000), 'wait %d' % IDLE_MS, 'pos idle-end']
    for i, t in enumerate(ch):
        s += block('k%d' % (i + 1), t)
    s += ['log ' + TAG + '_%s DONE' % map_id, 'pass 1000']
    total = LEAD_WAIT + IDLE_MS + BLOCK_MS * len(ch)
    assert total < 400000, 'run too long: %d ms after load' % total
    text = '\n'.join(hdr) + '\n[Script]\n' + '\n'.join('%d=%s' % (i + 1, t) for i, t in enumerate(s)) + '\n'
    p = os.path.join(out, TAG + '_%s.ini' % map_id)
    open(p, 'w', encoding='ascii', errors='replace', newline='\n').write(text)
    return p, ch, total


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 2
    n, out, plans, maps = 8, OUT, PLANS, []
    i = 0
    while i < len(argv):
        if argv[i] == '--n': n = int(argv[i + 1]); i += 2
        elif argv[i] == '--out': out = argv[i + 1]; i += 2
        elif argv[i] == '--plans': plans = argv[i + 1]; i += 2
        else: maps.append(argv[i]); i += 1
    if maps == ['all']:
        maps = MAPS
    for m in maps:
        p, ch, total = build(m, n, out, plans)
        print('%s -> %s (%d blocks, ~%d s after load)' % (m, p, len(ch), total // 1000))
        for k, t in enumerate(ch):
            print('   k%d %s %s ext %s stand %s' % (k + 1, t['name'], t['kind'], t['ext'], t['stand']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
