#!/usr/bin/env python3
"""
The player's cover on a Dead Men map: what its NoCoverBox boxes forbid, and a step that takes them out.
Works on a FINISHED build folder (<slot>_Main.zip + the files beside it). Full account: re/lean_m02.md.

    python kl_fix_lean.py check <folder>                    read-only: the boxes, their footprint, the cover boxes
                                                            and the bots' places that lie in them
    python kl_fix_lean.py apply <folder> <out folder> [--keep <pattern>] ...
                                                            the build with the NoCoverBox controller taken off
                                                            every box (not those whose path matches a --keep
                                                            pattern, fnmatch, case-insensitive)
    python kl_fix_lean.py apply <folder> <out folder> --ctrl DistanceRumbleCam
                                                            the same step for another controller. DistanceRumbleCam
                                                            (owner, 2026-10-10, Hot Coffee: 'weird camera thing happens
                                                            where u can barely see anything for a few seconds after the
                                                            plane comes by'): M01's Planes!TrafficFlowController mixes
                                                            0.4 of the ZCAMERA 'AnimatedRumbleCamera' into the view
                                                            while the plane is within 1000..3300; that camera's motion
                                                            is a MatPosAnim clip of Dead Men's .ANM, which is not
                                                            carried. ASSUMPTION (not read in the exe, not tried): the
                                                            missing clip is what throws the view; without the
                                                            controller there is no plane rumble at all.

READ IN kl2.exe (static; nothing of it was tried in the game)
  - A cover is a ZSTDOBJ-family entity whose NAME matches *coverbox* (CFFCoverList slot 13, 0x6d6a80: it walks
    every entity of the scene, at most 5000); *coverboxcar*, *coverboxm*, *coverboxl* make a low cover,
    *coverboxh* a high one (0x603830), any other name matching *coverbox* is collected and then skipped. The
    Dead Men maps bring these boxes themselves (CoverBoxH_nn / CoverBoxM_nn, 104..260 a map).
  - ZNoCoverBox (vtable 0xbc60dc) slot 14, 0x723fb0, links every box into a list at gamedata + 0x8c0
    (gamedata = [0xdd265c]; 0x8d0ed0 sets the head, the box's +0x34 is 'next': no size limit).
  - ZFFPlayerMovementStandCover (vtable 0xbb5b6c) slot 14, 0x71f050, answers 0 at once when 0x6fa6a0 finds the
    player's place inside one of those boxes (the box's own point test, margin [0xb554fc] = -10: the box
    shrunk by 10). ASSUMPTION: slot 14 is 'may this movement run' - then inside a NoCoverBox the player cannot
    take cover at all, and so cannot lean out of one either.
  - No stock Dog Days level has a NoCoverBox (F01 F02 F03 F07 L03 looked at): Dog Days enters cover on a key
    (TapCover, C), Dead Men stuck the player to a wall by itself and needed boxes that say 'not here'.

WHY A STEP: Late Night Opening has 91 such boxes (footprints 645 m2: both escalators over all three floors,
the cafe, the start, the cash machines, benches, pillars, the jewel stores' fronts), the bank 40 (206 m2).
They are Dead Men's own data and the SAME in every build of the map, so they are NOT what changed between the
build the owner played in the morning and the one of the evening (re/lean_m02.md: nothing of the level that
the cover code reads changed). The step is for an A / B run: the map as Dog Days' own maps are, with no
no-cover box. PlayerCoverCollision boxes are not touched.

What apply changes: the .prp member only (one controller less on each box; no entity added, removed or moved,
no reference re-pointed - nothing names a controller by its index on these nodes). Proved on the result:
every other member equal by CRC, the files beside the archive copied, steps.json continued ('lean').
"""
import collections, fnmatch, json, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft
import kl_prpjoin as J

SLOT = 'F01'
CTRL = 'NoCoverBox'
MARGIN = -10.0                  # kl2 [0xb554fc], the margin 0x6fa6a0 hands to the box's point test
NEAR = 60.0                     # a cover box 'at' a no-cover box: its origin within this of the box (a man's reach)
COVER = ('coverboxh', 'coverboxm', 'coverboxl', 'coverboxcar')


def _archive(folder):
    if folder.lower().endswith('.zip'):
        return folder
    hit = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(hit) != 1:
        raise ValueError('%s: %d level archives' % (folder, len(hit)))
    return os.path.join(folder, hit[0])


def boxes(sc, ctrl=None):
    """-> [node index] of every node that carries the NoCoverBox controller."""
    return [k for k in range(1, len(sc.nodes)) if kl_fa.has(sc, k, ctrl or CTRL)]


def facts(folder, log=print):
    """Read-only report of a build's no-cover boxes. -> dict."""
    import kl_map_escape as E
    L = E.Level(folder)
    sc = L.sc
    bx = []
    for k in boxes(sc):
        v = L.values(k)
        size = [v[f] for f in sorted(v) if f.startswith('ZBoxPrimitive[')][:3]     # half sizes (ASSUMPTION: as the escalator
        R, T = L.frame(k)                                                          # boxes read, 0..1350 over three floors)
        bx.append((k, R, T, size))

    def inside(p, margin):
        out = []
        for k, R, T, s in bx:
            d = [p[i] - T[i] for i in range(3)]
            q = [sum(R[i][j] * d[i] for i in range(3)) for j in range(3)]
            if all(abs(q[i]) <= s[i] + margin for i in range(3)):
                out.append(k)
        return out

    cov = [k for k in range(1, len(sc.nodes)) if any(t in sc.names[k].lower() for t in COVER)]
    at = [k for k in cov if inside(L.place(k), NEAR)]
    rep = collections.OrderedDict(folder=folder, boxes=len(bx), footprint_m2=round(sum(4 * s[0] * s[2] for *_x, s in bx) / 1e4, 1),
                                  cover_boxes=len(cov), cover_boxes_at_a_no_cover_box=len(at))
    log('%s: %d NoCoverBox, footprints %.0f m2; %d cover boxes (CoverBoxH / M / L / Car), %d of them within %d of a no-cover box'
        % (folder, len(bx), rep['footprint_m2'], len(cov), len(at), NEAR))
    for k, _R, T, s in sorted(bx, key=lambda b: -b[3][0] * b[3][2])[:12]:
        log('  %-64s at (%6d %5d %6d) half (%4d %4d %4d)' % (sc.path[k][5:][-64:], T[0], T[1], T[2], s[0], s[1], s[2]))
    bj = os.path.join(os.path.dirname(L.zip), 'bots.json')
    if os.path.isfile(bj):
        n = tot = 0
        for st in json.load(open(bj)).get('plan', {}).get('stations') or []:
            for p in st.get('places') or []:
                if isinstance(p, (list, tuple)) and len(p) >= 3:
                    tot += 1; n += bool(inside(p[:3], MARGIN))
        rep['bot_places'], rep['bot_places_in_a_no_cover_box'] = tot, n
        log('  the AI heisters\' places (bots.json): %d of %d inside a no-cover box' % (n, tot))
    return rep


def apply(src, dst, keep=(), log=print, ctrl=CTRL):
    """The build of folder `src` written to folder `dst` with the NoCoverBox controller taken off its boxes. -> report."""
    zp = _archive(src)
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the out folder is the build itself')
    order, files, ext, sc, _live, _hud = kl_graft.open_built(zp)
    if sc.p.serialize() != files[ext['.prp']]:
        raise ValueError('the build\'s .prp does not re-serialise byte for byte: not changed')
    data0, bad0, _p, _n = J.check(sc, log=lambda *_a: None)
    keep = [p.lower() for p in keep]
    took, kept = [], []
    tag = 'lean' if ctrl == CTRL else ctrl.lower()
    for k in boxes(sc, ctrl):
        path = sc.path[k]
        if any(fnmatch.fnmatch(path.lower(), p) or fnmatch.fnmatch(sc.names[k].lower(), p) for p in keep):
            kept.append(path); continue
        n = sc.nodes[k]
        n['ctrls'] = [c for c in n['ctrls'] if sc.p.key(c[0]) != ctrl]
        took.append(path)
    if not took:
        raise ValueError('no %s to take off (%d kept)' % (ctrl, len(kept)))
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    if len(bad) > len(bad0):
        raise ValueError('%d objects do not fit their class after the change (%d before): %s' % (len(bad), len(bad0), bad[:3]))
    if boxes(sc, ctrl) and not kept:
        raise ValueError('a %s is left' % ctrl)
    # nothing names these controllers: a reference names a NODE, and the nodes stay
    files[ext['.prp']] = data
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp and not x.startswith(tag + '.'):
            shutil.copyfile(q, os.path.join(dst, x))
    with zipfile.ZipFile(zp) as a, zipfile.ZipFile(out) as b:
        ia, ib = a.infolist(), b.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        diff = [i.filename.rsplit('_Main', 1)[-1] for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if diff != ['.prp']:
        raise ValueError('more than the .prp member differs from the build: %s' % diff)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st[tag], st['final'] = diff, kl_maps.member_ids(dst, os.path.basename(zp)[:-len('_Main.zip')])
        st['same'] = [e for e in st.get('same', []) if e not in diff]
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    rep = collections.OrderedDict(source=zp, out=out, taken=len(took), kept=kept, members_changed=diff,
                                  prp_bytes=[len(data0), len(data)], boxes=took)
    with open(os.path.join(dst, tag + '.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    lines = ['kl_fix_lean: %s -> %s' % (zp, out),
             '  %s controller taken off %d objects, %d kept; only the .prp member differs (%d -> %d bytes)' % (ctrl, len(took), len(kept), len(data0), len(data))]
    lines += ['    ' + p[5:] for p in took]
    with open(os.path.join(dst, tag + '.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    for s in lines[:2]:
        log(s)
    return rep


def main():
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'check':
        facts(a[1])
    elif len(a) >= 3 and a[0] == 'apply':
        keep, rest, i, ctrl = [], a[3:], 0, CTRL
        while i < len(rest):
            if rest[i] == '--keep' and i + 1 < len(rest):
                keep.append(rest[i + 1]); i += 2
            elif rest[i] == '--ctrl' and i + 1 < len(rest):
                ctrl = rest[i + 1]; i += 2
            else:
                sys.exit('unknown option %s' % rest[i])
        apply(a[1], a[2], keep, ctrl=ctrl)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
