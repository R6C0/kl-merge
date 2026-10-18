"""Night 1018 balance pass for the old Dead Men FA maps (DM03 / DM06), .prp ONLY, on a copy of a finished folder.

  python tools/kl_fa_bots_balance.py SRC_FOLDER DST_FOLDER --slot=F04 [--acc-cap=75] [--squads=05,08 --target=30000]

Both parts are OFF unless asked for, so a run with neither flag writes a folder whose archive is byte-identical to
SRC's (proved by the member CRC compare at the end).

--acc-cap=N   (E5) every cop (ZSoldier that is not an Ally / eDog) whose accuracy AS USED is above N gets
              accuracy N: skill -> eCustom with the old preset's numbers kept, ACC = N / factor (No_Mercenary x1.1,
              kl_map_ai.ACC_FACTOR). Aim, health and everything else stay. N = 75 is the owner-feedback figure
              ('about 75 instead of about 100'); the exact value is a GUESS.
--squads=05,08 --target=T   (E7) bot squads Squad#NN: the RandomTrigger forks named '*_way' (a way between two
              places) are thinned one at a time: the branch whose removal (weight -> 0, the stock form of a
              disabled branch, see kl_fa_bots.fork_branches) shortens the squad's longest branch set most is
              switched off, as long as the squad is above T and >= 2 branches with a weight and a target are
              left (check() FAILs otherwise). T = 30000 follows the other squads (22-28K); a GUESS.
Needs: nothing but the folder; check() is run per trial (~15 s each)."""
import os, shutil, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa, kl_map_ai as A, kl_prpjoin as J, kl_graft
import kl_fa_bots as F


def cap_accuracy(sc, cap, log=print):
    """Accuracy as used above `cap` -> cap, on every cop. -> [(path, old, new)]."""
    rep = []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor':
            continue
        hit = [(i, v) for i, n, v in A.ctrls(sc, k) if n == 'ZSoldier']
        if not hit:
            continue
        i, v = hit[0]
        if len(v) != 23:
            raise ValueError('%s: ZSoldier is not in the Dog Days layout' % sc.path[k])
        if kl_fa.node_values(sc, k)[J.labels('dd', 'ZFFActor').index('ZFFActor[0]')] == 'Ally' or v[A.STYLE] == 'eDog':
            continue
        fac = A.ACC_FACTOR if v[A.MERC] == 'No_Mercenary' else 1.0
        e = A.effective(v)[A.ACC]
        if e <= cap + 0.01:
            continue
        new = {}
        if v[A.SKILL] != 'eCustom':
            new[A.SKILL] = 'eCustom'
            for fi, x in zip(A.PRESET_FIELDS, A.PRESET[v[A.SKILL]]):
                new[fi] = float(x)
        new[A.ACC] = round(cap / fac, 1)
        new = {fi: x for fi, x in new.items() if x != v[fi]}
        kl_fa.edit(sc, k, i, lambda us, new=new: [A.setv(sc, us, fi, x) for fi, x in new.items()])
        after = A.effective([new.get(fi, x) for fi, x in enumerate(v)])[A.ACC]
        rep.append((sc.path[k], round(e, 1), round(after, 1)))
    log('  accuracy cap %g: %d cops lowered' % (cap, len(rep)))
    return rep


def forks(sc, squad):
    """[(node, [weights 1..4], [target present x4])] of the '*_way' RandomTriggers of Squad#<squad>."""
    out = []
    tag = '!Squad#%s' % squad
    for k, _i, v in kl_fa.controllers(sc, 'RandomTrigger'):
        if tag + chr(92) in sc.path[k] and sc.names[k].endswith('_way'):
            out.append((k, list(v[1:5]), [bool(l) for l in v[5:9]]))
    return out


def set_weight(sc, k, idx, w):
    i, _n, _v = A.ctrl(sc, k, 'RandomTrigger')
    def fn(us):
        op = us[1 + idx][0][0]
        if op == 0x08:                                  # a weight is a 2-byte short (kl_prp.FIXED)
            us[1 + idx] = [(op, struct.pack('<h', int(w)))]
        else:
            A.setv(sc, us, 1 + idx, w)
    kl_fa.edit(sc, k, i, fn)


def write_folder(src, dst, files_over, small_only=False):
    """dst = src with archive members replaced from files_over {name: bytes}. small_only: only the archive + ini files."""
    zp = A.archive_of(src)
    order, files, ext, sc, _l, _h = kl_graft.open_built(zp)
    files.update(files_over)
    os.makedirs(dst, exist_ok=True)
    kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp:
            d = os.path.join(dst, x)
            if small_only and os.path.getsize(q) > (1 << 20):
                try:
                    os.link(q, d)                       # a trial only reads sizes of the big files
                    continue
                except OSError:
                    pass
            shutil.copyfile(q, d)
    return ext


def lengths(folder, slot, squads):
    out, facts = F.check(folder, slot=slot, log=lambda *_a: None)
    fails = [l for l in out if str(l).startswith('FAIL')] if isinstance(out, list) else []
    res = {}
    for sq in squads:
        key = 'Gameplay!merc_bot_squad!Squad#%s' % sq
        res[sq] = [round(b['path_length']) for b in facts['route_branches'][key]]
    return res, facts, out


def balance(src, dst, slot, squads, target, tmp, log=print):
    zp = A.archive_of(src)
    order, files, ext, sc, _l, _h = kl_graft.open_built(zp)
    base, _f, _o = lengths(src, slot, squads)
    log('  start: ' + ', '.join('#%s max %d (%s)' % (s, max(v), v) for s, v in base.items()))
    done = []
    for sq in squads:
        cur = max(base[sq])
        for k, w, has in forks(sc, sq):
            if cur <= target:
                break
            live = [j for j in range(4) if w[j] and has[j]]
            if len(live) <= 2:
                continue
            best = None
            for j in live:
                set_weight(sc, k, j, 0)
                data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
                if bad:
                    raise ValueError(bad[:3])
                t = os.path.join(tmp, 'trial')
                write_folder(src, t, {ext['.prp']: data}, small_only=True)
                r, _f, _o = lengths(t, slot, [sq])
                m = max(r[sq])
                log('    #%s %s: branch %d off -> max %d' % (sq, sc.names[k], j, m))
                set_weight(sc, k, j, w[j])
                if m < cur and (best is None or m < best[0]):
                    best = (m, j)
                shutil.rmtree(t, ignore_errors=True)
            if best:
                set_weight(sc, k, best[1], 0)
                done.append((sc.path[k], best[1], w[best[1]], cur, best[0]))
                log('  #%s %s: branch %d weight %d -> 0 (max %d -> %d)' % (sq, sc.names[k], best[1], w[best[1]], cur, best[0]))
                cur = best[0]
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    return sc, data, done


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    o = dict(x[2:].split('=', 1) if '=' in x else (x[2:], '1') for x in sys.argv[1:] if x.startswith('--'))
    src, dst = a
    slot = o['slot']
    zp = A.archive_of(src)
    order, files, ext, sc, _l, _h = kl_graft.open_built(zp)
    data0, bad0, _p, _n = J.check(sc, log=lambda *_a: None)
    if data0 != files[ext['.prp']] or bad0:
        raise ValueError('the .prp does not re-serialise byte for byte')
    log = print
    if 'squads' in o:
        sc, data, done = balance(src, dst + '_tmp', slot, o['squads'].split(','), float(o.get('target', 30000)), os.path.dirname(os.path.abspath(dst)))
        shutil.rmtree(dst + '_tmp', ignore_errors=True)
    else:
        data = data0
    if 'acc-cap' in o:
        cap_accuracy(sc, float(o['acc-cap']))
        data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
        if bad:
            raise ValueError(bad[:3])
    if A.faults(sc):
        raise ValueError(A.faults(sc)[:8])
    write_folder(src, dst, {ext['.prp']: data})
    # member compare
    za, zb = zipfile.ZipFile(zp), zipfile.ZipFile(os.path.join(dst, os.path.basename(zp)))
    ca = {i.filename: i.CRC for i in za.infolist()}
    cb = {i.filename: i.CRC for i in zb.infolist()}
    print('members differing:', [n for n in ca if ca[n] != cb.get(n)], 'only in one:', set(ca) ^ set(cb))


if __name__ == '__main__':
    main()
