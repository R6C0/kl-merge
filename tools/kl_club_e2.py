#!/usr/bin/env python3
"""
Last Call (DM05A), audit 1018 items E1 (and the data side of E2). OFFLINE; reads a finished build folder, writes a new one.
Only the .prp member changes, and only behind a flag; WITHOUT a flag `build` writes a byte-identical copy (proved by `check`).

    python kl_club_e2.py build <folder> <out> [--run-to-escape] [--skip-gates walkway,floor2,third]
    python kl_club_e2.py check <folder> <out> [same flags]

--run-to-escape (E1): the four AfterLoot exit squads (030_FinancialAlleyExit_Left / _Right, ...ExitStreet_Left / _Right)
  each own a '40_RunToEscape' rout that NOTHING names (kl_fa_club.place_police note), so the police never get the push
  to run for the escape. Stock F07 pairs the squads: when one is wiped out, its field 8 (ZSquadScript, the list sent
  when the squad is wiped out - an ASSUMPTION shared with kl_fa_author.SQUAD_DEAD and kl_fa_street.FALL) names the
  partner's '40_RunToEscape'. Same pairing here (kl_fa_street.FALL lines 217-220). Field 8 is empty on all four now.
  GUESS: that the rout, once named, moves the partner squad to its 'at' place (kl_fa_club.place_police) and that this
  is the wanted push. NOT RUN IN THE GAME.
--skip-gates: kl_club_budget's data edit (guard list of the named gates emptied), see that file. Unproven loader case.
"""
import os, shutil, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_bots as F, kl_fa_author as A, kl_graft, kl_prp
import kl_club_budget as BU

BS = chr(92)
G3 = 'ROOT' + BS + 'Gameplay!030_AfterLoot!030_FinancialAlley'
PAIRS = [(G3 + 'Exit_Left', G3 + 'ExitStreet_Left'), (G3 + 'ExitStreet_Left', G3 + 'Exit_Left'),
         (G3 + 'Exit_Right', G3 + 'ExitStreet_Right'), (G3 + 'ExitStreet_Right', G3 + 'Exit_Right')]


def _edits(sc, run_to_escape, skip):
    """[(node, controller index, field, new list)] ; node paths are checked."""
    out = []
    if run_to_escape:
        for squad, partner in PAIRS:
            tgt = partner + BS + '40_RunToEscape'
            k = A.node_of(sc, squad)
            if len(sc.resolve(tgt)) != 1:
                raise ValueError('not in the level: %s / %s' % (squad, tgt))
            out.append((k, A.ctrl_of(sc, k, 'ZSquadScript'), A.SQUAD_DEAD, [tgt]))
    gn = BU.gate_nodes(sc)
    for g in skip:
        if g not in BU.GATES or not gn[g]:
            raise ValueError('gate %s unknown or absent' % g)
        for k in gn[g]:
            out.append((k, A.ctrl_of(sc, k, 'TriggerActorsDead'), BU.GUARD_LIST, []))
    return out


def build(src, dst, run_to_escape=False, skip=(), slot='F01', log=print):
    B = F.Built(src, slot)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s is there and not empty' % dst)
    ed = _edits(sc, run_to_escape, skip)
    for k, i, f, v in ed:
        kl_fa.edit(sc, k, i, lambda us, f=f, v=v: A.setv(sc, us, f, v))
    new = dict(B.files)
    if ed:
        prp = sc.p.serialize()
        back = kl_prp.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(sc.nodes):
            raise ValueError('the new .prp does not round-trip')
        new[B.ext['.prp']] = prp
    os.makedirs(dst, exist_ok=True)
    if ed:
        kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    else:
        shutil.copyfile(B.zp, os.path.join(dst, os.path.basename(B.zp)))
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'civs.')):
            shutil.copyfile(p, os.path.join(dst, f))
    if ed:
        sj = os.path.join(dst, 'steps.json')
        if os.path.isfile(sj):
            import kl_maps
            st = json.load(open(sj))
            st['e2'] = ['.prp']
            st['same'] = [e for e in st.get('same', []) if e != '.prp']
            st['final'] = kl_maps.member_ids(dst)
            with open(sj, 'w') as f:
                json.dump(st, f, indent=1)
        with open(os.path.join(dst, 'graft.txt'), 'a') as f:
            f.write('kl_club_e2: %d controller field(s) edited (run-to-escape=%s, skip-gates=%s); from %s\n'
                    % (len(ed), run_to_escape, ','.join(skip), B.folder))
    log('written %s: %d edit(s)' % (dst, len(ed)))
    return dst


def diff(src, dst, run_to_escape=False, skip=(), slot='F01'):
    a, b = F.Built(src, slot), F.Built(dst, slot)
    bad = []
    if a.order != b.order:
        bad.append('member order differs')
    for n in a.order:
        if a.files[n] != b.files.get(n) and not n.endswith('.prp'):
            bad.append('member %s differs' % n)
    if len(a.sc.nodes) != len(b.sc.nodes):
        return bad + ['node count differs']
    ok = {k: f for k, _i, f, _v in _edits(a.sc, run_to_escape, skip)}
    for k in range(len(a.sc.nodes)):
        if (a.sc.nodes[k]['props'], a.sc.nodes[k]['ctrls']) == (b.sc.nodes[k]['props'], b.sc.nodes[k]['ctrls']):
            continue
        if k not in ok:
            bad.append('node %d (%s) differs' % (k, a.sc.path[k])); continue
        va = [v for c in ('ZSquadScript', 'TriggerActorsDead') for kk, _i, v in kl_fa.controllers(a.sc, c) if kk == k]
        vb = [v for c in ('ZSquadScript', 'TriggerActorsDead') for kk, _i, v in kl_fa.controllers(b.sc, c) if kk == k]
        if len(va) != 1 or len(vb) != 1:
            bad.append('node %d: controller count' % k); continue
        d = [j for j in range(len(va[0])) if va[0][j] != vb[0][j]]
        if d != [ok[k]]:
            bad.append('node %d: fields %s changed, only %d allowed' % (k, d, ok[k]))
    if not (run_to_escape or skip) and a.files != b.files:
        bad.append('no flag, but the members differ')
    return bad


def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in ('build', 'check'):
        print(__doc__); return 2
    cmd = a.pop(0)
    rte = '--run-to-escape' in a
    if rte:
        a.remove('--run-to-escape')
    skip = []
    if '--skip-gates' in a:
        i = a.index('--skip-gates'); skip = [x for x in a[i + 1].split(',') if x]; del a[i:i + 2]
    if cmd == 'build':
        build(a[0], a[1], rte, skip)
    bad = diff(a[0], a[1], rte, skip)
    for x in bad:
        print('FAIL', x)
    print('check: %d FAIL' % len(bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
