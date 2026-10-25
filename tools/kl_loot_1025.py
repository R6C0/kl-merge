"""kl_loot_1025.py - loot placement fixes of the Dead Men maps (moves and value rebalance only). Written 2026-10-25, OFFLINE: nothing here is run in the game.

WHAT IT DOES (binding source: C:/kl_build_1024/owner1025/loot/critique.md; no new model root, no retype, .prm untouched)
  For one built map zip (a COPY of the live one, md5 pinned) it moves named loot nodes to new places and sets new amounts, and writes the zip again with
  ONLY the changed members replaced (.prp, .gms; .buf and .oct are written only when their bytes differ - they do not, see below).
    move(k, (x, y, z))  .prp ZGEOM[2] of the node + the .gms record's translation (kept equal, as kl_fa_loot.Edit.put / kl_fa_author.place do)
    amount(k, v)        OnlineMoneyCtrl field 1 (the amount) of the node
  Loot nodes are top-level nodes (parent 0): their ZGEOM values are world values. A node with children keeps them (they are local to it).

WHAT IS NOT TOUCHED
  .prm, .MAT, .TEX (so KLGuns / KLJoin Entries stay valid: the .prm member is byte-identical, asserted), .oct / .rmi / .rmc.
  GUESS (checked per node, not assumed): the .oct room trees hold an item (slot id + 2, a box) for an entity only when it is listed; the loot nodes of
  every map handled here are NOT listed in any room tree (checked: 0 items), so a moved loot node needs no octree edit. Should a node ever be listed, build()
  refuses (it does not guess a new box).

TOGGLE (owner's rule: every feature on/off). This is a map CONTENT change: its on/off switch is the install / undo pair. install.py puts the staged zip in
and moves the original aside as '<zip>.before-1025loot'; install.py --undo puts it back byte for byte. The live md5 is pinned before either step.

Usage (from tools/):
  python kl_loot_1025.py stage <root> [MAP ...] [--rehearse <scratch>]    <root>/<MAP>/in/<zip> (+ the ini files) -> <root>/<MAP>/stage/{zip, install.py, build_report.json}
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_octree as O
import kl_prpjoin as J

TAG = '.before-1025loot'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TOTAL = 4000000

# name -> slot, zip, live md5 (pinned in full), moves {node: (x, y, z)}, amounts {node: amount}
# (filled by the per-map section at the bottom of this file)
MAPS = collections.OrderedDict()


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def rmtree(p):
    def w(f, q, _e):
        os.chmod(q, 0o666)
        f(q)
    if os.path.isdir(p):
        shutil.rmtree(p, onexc=w)


def patch_zip(src, dst, repl):
    """src with the members in `repl` {name: bytes} replaced and every other member copied unchanged (bytes, compression, stamp, order)."""
    n = 0
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w', allowZip64=True) as zo:
        for info in zi.infolist():
            i2 = zipfile.ZipInfo(info.filename, info.date_time)
            i2.compress_type, i2.external_attr, i2.create_system = info.compress_type, info.external_attr, info.create_system
            i2.comment = info.comment
            if info.filename in repl:
                zo.writestr(i2, repl[info.filename], compress_type=info.compress_type)
                n += 1
            else:
                with zi.open(info) as fi, zo.open(i2, 'w', force_zip64=info.file_size > 0x7fffffff) as fo:
                    while True:
                        c = fi.read(1 << 20)
                        if not c:
                            break
                        fo.write(c)
    if n != len(repl):
        raise ValueError('%s: %d of %d members to replace were found' % (src, n, len(repl)))


def listed_in_oct(B, ks):
    """The nodes of ks that some .oct room tree lists (an item id = slot + 2) -> [node]."""
    slots = B.scene.slots()
    ids = {slots[B.ents[k - 1]] + 2: k for k in ks}
    oc = O.Oct.parse(B['.oct'])
    hit = set()
    for room in oc.rooms:
        for t in room:
            if t is not None:
                hit.update(ids[it[0]] for it in t.items if it[0] in ids)
    return sorted(hit)


def move(B, k, pos):
    """Node k to the world place pos: .prp ZGEOM[2] and the .gms record."""
    sc, e = B.sc, B.ents[k - 1]
    if sc.parent[k] != 0:
        raise ValueError('%s: not a top-level node, its ZGEOM is local' % sc.path[k])
    lab = J.labels('dd', sc.cls(k))
    i = lab.index('ZGEOM[2]')
    kl_graft.edit(sc.nodes[k], 'props', lambda us: AU.setv(sc, us, i, [float(x) for x in pos]))
    e.trans = struct.pack('<3f', *[float(x) for x in pos]) + e.trans[12:]


def amount(B, k, v):
    sc = B.sc
    i = AU.ctrl_of(sc, k, 'OnlineMoneyCtrl')
    kl_fa.edit(sc, k, i, lambda us: AU.setv(sc, us, 1, int(v)))


def zgeom(B, k):
    lab = J.labels('dd', B.sc.cls(k))
    return [round(v, 3) for v in kl_fa.node_values(B.sc, k)[lab.index('ZGEOM[2]')]]


def money(B):
    """{node: amount} of every loot object (NORMAL / CONTAINER) of the build, kl_fa_bots.money_objects."""
    return {o['node']: o['amount'] for o in KB.money_objects(B)}


def build(src, slot, dst, moves, amounts, log=print):
    """-> report dict. src is read only; dst is written."""
    B = KB.Built(src, slot)
    sc = B.sc
    before = money(B)
    pos0 = {k: zgeom(B, k) for k in moves}
    for k in list(moves) + list(amounts):
        if k not in before:
            raise ValueError('node %d is not a loot object of %s' % (k, src))
    stuck = listed_in_oct(B, moves)
    if stuck:
        raise ValueError('nodes %s are listed in an .oct room tree: moving them needs an octree edit (not done)' % stuck)
    for k, p in moves.items():
        move(B, k, p)
    for k, v in amounts.items():
        amount(B, k, v)
    prp = sc.p.serialize()
    gms, buf = B.scene.write()
    gms = kl_gms.pack(gms)
    new = {B.ext['.prp']: prp, B.ext['.gms']: gms, B.ext['.buf']: buf}
    repl = {n: b for n, b in new.items() if b != B.files[n]}
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    patch_zip(src, dst, repl)
    # read it back and verify: positions, amounts, total, every other member identical
    A = KB.Built(dst, slot)
    after = money(A)
    bad = []
    for k, p in moves.items():
        got = zgeom(A, k)
        if any(abs(a - b) > 0.01 for a, b in zip(got, p)):
            bad.append('node %d ZGEOM %s != %s' % (k, got, p))
        w = A.at(k)
        if any(abs(a - b) > 0.01 for a, b in zip(w, p)):
            bad.append('node %d .gms world %s != %s' % (k, [round(v, 2) for v in w], p))
    for k in before:
        want = amounts.get(k, before[k])
        if after.get(k) != want:
            bad.append('node %d amount %s != %s' % (k, after.get(k), want))
    if set(after) != set(before):
        bad.append('the set of loot objects changed')
    for n in A.files:
        if n not in repl and A.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    prm = B.ext['.prm']
    if A.files[prm] != B.files[prm]:
        bad.append('.prm changed')
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep = collections.OrderedDict(
        md5_in=md5(src), md5_out=md5(dst), members_changed=sorted(repl), total_before=sum(before.values()), total_after=sum(after.values()),
        objects=len(after),
        moved=[collections.OrderedDict(node=k, name=sc.names[k], old=pos0[k], new=[round(float(v), 3) for v in p]) for k, p in moves.items()],
        amounts=[collections.OrderedDict(node=k, name=sc.names[k], old=before[k], new=v) for k, v in amounts.items()],
        prm_identical=True, oct_listed=0)
    log('  members changed: %s; %d moved, %d amounts; total %d -> %d' % (' '.join(rep['members_changed']), len(moves), len(amounts), rep['total_before'], rep['total_after']))
    return rep


INSTALL_PY = '''"""Installs / undoes the staged %(map)s loot-placement zip (tools/kl_loot_1025.py, 2026-10-25). This pair IS the feature's on/off switch.
  python install.py           put %(zip)s in (the original moves to %(zip)s%(tag)s)
  python install.py --undo    put the original back, byte for byte
  --game <dir>                a Dog Days folder other than the default (rehearsals)
The live md5 is pinned before either step; nothing is written while kl2.exe runs."""
import hashlib, os, shutil, subprocess, sys

GAME = %(game)r
MAP, ZIP, TAG = %(map)r, %(zip)r, %(tag)r
OLD, NEW = %(old)r, %(new)r


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    a = sys.argv[1:]
    undo = '--undo' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    live = os.path.join(game, 'KLExpansion', 'Maps', MAP, ZIP)
    bak = live + TAG
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), ZIP)
    if '--skip-run-check' not in a and 'kl2.exe' in subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower():
        print('REFUSED: kl2.exe is running'); return 3
    if not os.path.isfile(live):
        print('REFUSED: %%s is not there' %% live); return 2
    cur = md5(live)
    if undo:
        if not os.path.isfile(bak):
            print('nothing to undo: no %%s' %% bak); return 0
        if cur != NEW:
            print('REFUSED: live md5 %%s is not the installed %%s' %% (cur, NEW)); return 2
        if md5(bak) != OLD:
            print('REFUSED: backup md5 %%s is not %%s' %% (md5(bak), OLD)); return 2
        os.replace(bak, live)
        print('undone: %%s md5 %%s' %% (live, md5(live))); return 0
    if cur == NEW and os.path.isfile(bak):
        print('already installed'); return 0
    if cur != OLD:
        print('REFUSED: live md5 %%s is not the pinned %%s (the map was changed since this was staged)' %% (cur, OLD)); return 2
    if os.path.exists(bak):
        print('REFUSED: %%s exists already' %% bak); return 2
    if md5(here) != NEW:
        print('REFUSED: the staged zip next to install.py is not md5 %%s' %% NEW); return 2
    os.replace(live, bak)
    shutil.copyfile(here, live)
    if md5(live) != NEW:
        os.replace(bak, live)
        print('copy failed, original put back'); return 2
    print('installed: %%s md5 %%s' %% (live, NEW)); return 0


if __name__ == '__main__':
    sys.exit(main())
'''


def rehearse(d, name, old_zip, new_md5, old_md5, scratch, log=print):
    """Install, undo (byte-identical), reinstall, again, undo, wrong live md5 refused - on a COPY tree under scratch, never the game folder."""
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game_' + name)
    slot, zn = MAPS[name]['slot'], MAPS[name]['zip']
    live = os.path.join(g, 'KLExpansion', 'Maps', name, zn)
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    rmtree(g)
    os.makedirs(os.path.dirname(live))
    shutil.copy2(old_zip, live)
    run = lambda *x: subprocess.run([sys.executable, os.path.join(d, 'install.py'), '--game', g, '--skip-run-check'] + list(x), capture_output=True, text=True).stdout
    t = run(); log('  ' + t.strip()); assert 'installed' in t and md5(live) == new_md5, t
    assert os.path.isfile(live + TAG) and md5(live + TAG) == old_md5
    t = run('--undo'); log('  ' + t.strip())
    assert md5(live) == old_md5 and not os.path.exists(live + TAG), 'undo not byte identical'
    assert open(live, 'rb').read() == open(old_zip, 'rb').read()
    t = run(); assert md5(live) == new_md5, t
    t = run(); assert 'already installed' in t, t
    t = run('--undo'); assert md5(live) == old_md5 and not os.path.exists(live + TAG)
    os.chmod(live, 0o666)
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = run(); log('  ' + t.strip()); assert 'REFUSED' in t and not os.path.exists(live + TAG), t
    rmtree(g)
    log('  rehearsal ok (install, undo byte-identical, reinstall, again = no-op, wrong live md5 refused)')


def stage(root, names=None, scratch=None, log=print):
    free = shutil.disk_usage(root).free
    if free < 3 << 30:
        raise SystemExit('only %d MB free under %s (need 3 GB)' % (free >> 20, root))
    for name in names or MAPS:
        m = MAPS[name]
        d = os.path.join(root, name)
        src = os.path.join(d, 'in', m['zip'])
        h = md5(src)
        if h != m['pin']:
            raise SystemExit('%s md5 %s is not the pinned %s' % (src, h, m['pin']))
        log('== %s (%s) ==' % (name, m['zip']))
        out = os.path.join(d, 'stage')
        rmtree(out)
        os.makedirs(out)
        rep = build(src, m['slot'], os.path.join(out, m['zip']), m['moves'], m['amounts'], log)
        with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
            fh.write(INSTALL_PY % dict(map=name, zip=m['zip'], tag=TAG, game=GAME, old=h, new=rep['md5_out']))
        with open(os.path.join(out, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        if scratch:
            rehearse(out, name, src, rep['md5_out'], h, scratch, log)
    return 0


# ------------------------------------------------------------------ the maps
# Per-map decisions live in loot_specs_1025.py (the numbers come from the Floors / nav surveys written up in each map's section there).
try:
    import kl_loot_specs_1025 as _S
    MAPS.update(_S.MAPS)
except ImportError:
    pass


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] != 'stage':
        print(__doc__)
        return 2
    return stage(a[1], [x for x in a[2:] if x in MAPS] or None, opt('--rehearse'))


if __name__ == '__main__':
    sys.exit(main())
