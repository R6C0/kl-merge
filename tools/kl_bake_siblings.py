"""kl_bake_siblings.py - one map = up to four files that must change together (shared by kl_shop_buttons.py and kl_shop_pics.py, 2026-11-05).

A KLExpansion map folder holds, next to <slot>_Main.zip:
  <slot>_Main.bots.zip        the [BotGate] sibling the hook loads ONLINE when the gate is on (klhook/klslot.c ~421): the same level with eAllTypes squads
  <slot>_Main.bots.base.md5   md5 of the plain zip the sibling was made from (tools/kl_botgate_stage_1026.py check flags DRIFT when it no longer matches)
  Int16Ok.txt                 (DM11B only) 'zip=<bytes>' / 'bots=<bytes>' pins (klslot.c kls_i16_marked): a size change makes online refuse the map
A bake that only rewrote the plain zip would leave online players without the change and the md5 / sizes stale. This module bakes ALL of them as one
transaction per map, each file backed up with the caller's tag ('.before-shopbuttons' / '.before-shoppics'), and undoes them together.
Stock Scenes/Locations/Fxx folders have no bots sibling (checked 2026-11-05): only the plain zip is touched there.

  install_map(zip path, tag, bake_fn)   bake_fn(src, dst) -> True when it wrote dst, False when src is already baked, raises when it cannot
  undo_map(zip path, tag)               moves every <file><tag> back (the live, baked file is dropped)
Rules: the md5 file is rewritten only when it matched the OLD plain zip (a sibling that had drifted before stays flagged, with a WARNING); an Int16Ok
size line is rewritten only when it matched the OLD file (a marker that was already void stays void). Any failure restores every file of the map.
"""
import hashlib, os, re, shutil

RBK = '.rbk'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def paths(zp):
    """the four live paths of a map (they need not exist): plain, bots, md5, i16"""
    base = zp[:-len('.zip')]
    return {'plain': zp, 'bots': base + '.bots.zip', 'md5': base + '.bots.base.md5', 'i16': os.path.join(os.path.dirname(zp), 'Int16Ok.txt')}


def _fix_i16(raw, old_plain, new_plain, old_bots, new_bots, log):
    """Int16Ok.txt bytes -> bytes. zip= / bots= lines take the new size when they matched the old one."""
    out = []
    for ln in raw.split(b'\n'):
        m = re.match(rb'^(zip|bots)=(\d+)(\s*)$', ln.rstrip(b'\r'))
        if m:
            key, want = m.group(1).decode(), int(m.group(2))
            old, new = (old_plain, new_plain) if key == 'zip' else (old_bots, new_bots)
            if old is None:
                pass                                                 # no such file: the line proves nothing, leave it
            elif want == old:
                if new != old:
                    ln = (b'%s=%d' % (m.group(1), new)) + (b'\r' if ln.endswith(b'\r') else b'')
            else:
                log('  WARNING: Int16Ok.txt %s=%d did not match the zip (%d) before the bake: left as it was (marker already void)' % (key, want, old))
        out.append(ln)
    return b'\n'.join(out)


def install_map(zp, tag, bake_fn, log=print):
    """-> 'installed' or 'noop'. All-or-nothing for the files of this map."""
    P = paths(zp)
    live = {k: p for k, p in P.items() if os.path.isfile(p)}
    tmps = {}
    need = sum(os.path.getsize(p) for k, p in live.items() if k in ('plain', 'bots')) + (64 << 20)      # the baked temps, worst case
    if shutil.disk_usage(os.path.dirname(zp)).free < need:
        raise OSError('less than %d MB free next to %s' % (need >> 20, zp))
    committed = []                                                   # (live, restore-from) in commit order, for the rollback
    try:
        for k in ('plain', 'bots'):
            if k not in live:
                continue
            t = live[k] + '.new' + tag
            if os.path.exists(t):
                os.remove(t)
            if bake_fn(live[k], t):
                tmps[k] = t
            elif os.path.exists(t):
                os.remove(t)
        if not tmps:
            return 'noop'
        old_p, old_b = os.path.getsize(live['plain']), (os.path.getsize(live['bots']) if 'bots' in live else None)
        new_p = os.path.getsize(tmps['plain']) if 'plain' in tmps else old_p
        new_b = (os.path.getsize(tmps['bots']) if 'bots' in tmps else old_b)
        if 'md5' in live and 'plain' in tmps:
            cur = open(live['md5']).read().strip()
            was, now = md5(live['plain']), md5(tmps['plain'])
            if cur == was:
                t = live['md5'] + '.new' + tag
                with open(t, 'w', newline='\n') as f:
                    f.write(now + '\n')
                tmps['md5'] = t
            else:
                log('  WARNING: %s held %s, not the plain zip md5 %s: it had drifted before this bake, left as it was' % (os.path.basename(live['md5']), cur[:8], was[:8]))
        if 'i16' in live and (new_p != old_p or new_b != old_b):
            raw = open(live['i16'], 'rb').read()
            fixed = _fix_i16(raw, old_p, new_p, old_b, new_b, log)
            if fixed != raw:
                t = live['i16'] + '.new' + tag
                open(t, 'wb').write(fixed)
                tmps['i16'] = t
        for k in ('bots', 'plain', 'md5', 'i16'):
            if k not in tmps:
                continue
            lp, bak = live[k], live[k] + tag
            if not os.path.exists(bak):
                os.replace(lp, bak); old = bak                       # the first bake MOVES the original to the tag (never overwritten later)
            else:
                os.replace(lp, lp + RBK); old = lp + RBK             # an earlier bake left the original: only a rollback copy
            committed.append((lp, old))
            os.replace(tmps[k], lp)
            log('  %-5s %s' % (k, os.path.basename(lp)))
        for lp, old in committed:
            if old.endswith(RBK) and os.path.exists(old):
                os.remove(old)
        return 'installed'
    except BaseException:
        for lp, old in reversed(committed):                          # restore every file of the map
            if os.path.exists(old):
                os.replace(old, lp)
        raise
    finally:
        for t in tmps.values():
            if os.path.exists(t):
                os.remove(t)


def undo_map(zp, tag, log=print):
    """-> number of files restored. Transactional: a failure puts the baked files back."""
    P = paths(zp)
    todo = [(k, P[k]) for k in ('bots', 'plain', 'md5', 'i16') if os.path.exists(P[k] + tag)]
    done = []
    try:
        for k, lp in todo:
            had = os.path.exists(lp)
            if had:
                os.replace(lp, lp + RBK)
            done.append((lp, had))
            os.replace(lp + tag, lp)
            log('  %-5s restored %s' % (k, os.path.basename(lp)))
        for lp, had in done:
            if had and os.path.exists(lp + RBK):
                os.remove(lp + RBK)
        return len(done)
    except BaseException:
        for lp, had in reversed(done):
            if os.path.exists(lp):
                os.replace(lp, lp + tag)
            if had and os.path.exists(lp + RBK):
                os.replace(lp + RBK, lp)
        raise
