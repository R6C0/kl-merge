"""kl_dm01_nogren_1111.py - TAKE THE THREE GRENADE PICKUPS OUT OF DM01 (Hot Coffee). Owner 2026-11-11: "the grenade pickups gone". STAGE ONLY.

    python kl_dm01_nogren_1111.py stage [--out C:\\kl_build_1024\\dm01nogren_1111] [--game <DD>] [--no-rehearse]

kl_grenade_1025 added Special!Pickups!Grenade_Frag_01..03 (ZFFItemWeapon, top-level entities) to the live DM01 zip and to its online bots variant.
METHOD (b): the three entities leave the map with the same machinery that took KL_CoverSix! out (kl_cover_strip_1026): .prp (kl_prpjoin.join skip),
.gms/.buf (kl_scene.remove, slot ids renumbered), .oct/.rmi/.rmc (kl_octree.remap_ids with the removed slot ids dropped), .prm model roots re-pointed
when .oct records move. Why not a field change (a): no pickup enabled/hidden field is proven from the exe schema or a stock map, and the engine
reading a half-disabled pickup is a guess; removal is the same shape the stock FA maps have (no pickup node at all). Why not relocation (c): needs a
provably unreachable spot, and the entity would still be in the lists. The Grenade_Fragmentation templates, the Ammo projectile patch (Rocket_Flare
chain) and every other entity stay as they are: the hook's [Grenade] paths keep working.
Proved on each result (stage verifies, the rehearsal repeats): .prp re-serialises, .prp and .gms list the same entities (live minus the 3), no
dangling reference added, room sets before == after (kl_fa_bots.room_sets_check), no 'Grenade_Frag_0' node left, every other node's class + path + values
unchanged, members other than the 6 (+ .prm when needed) byte for byte the live ones (same entry order, compression, stamps).
Kit: install.py pins the live md5s (F01_Main.zip, F01_Main.bots.zip, F01_Main.bots.base.md5 = the plain zip md5), backups <name>.before-dm01nogren_1111
(os.replace, never deleted), --undo byte exact, --dry, refuses while a real kl2.exe runs (zombies under 50 MB ignored).
"""
import hashlib, json, os, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = r'C:\kl_build_1024\dm01nogren_1111'
MAP, SLOT = 'DM01', 'F01'
FILES = ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')
PINS = {'F01_Main.zip': 'b3b5bee811beeabadc16550d7d9f4433', 'F01_Main.bots.zip': '8e1607074662c593c1a4c8a6b635752c'}
TAG = '.before-dm01nogren_1111'
PICK = 'Special!Pickups!Grenade_Frag_0'     # entity name prefix (kl_grenade_1025: ..._01.._03)
FREE_KEEP = 1 << 30


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def is_pickup(name):
    return name.startswith(PICK) and len(name) == len(PICK) + 1 and name[-1] in '123'


def strip(src, log=print):
    """-> (members {name: bytes} that change, report). Raises when the zip does not hold exactly the three pickups."""
    import kl_gms, kl_fa, kl_fa_bots as KB, kl_octree as O, kl_prpjoin as J
    from kl_prp import Prp
    B = KB.Built(src, SLOT)
    sc = B.sc
    tops = [t for t in sc.tops() if is_pickup(sc.names[t])]
    if len(tops) != 3 or any(sc.cls(t) != 'ZFFItemWeapon' or sc.end[t] != t + 1 for t in tops):
        raise ValueError('%s: expected 3 childless ZFFItemWeapon top-level pickups, found %s' % (src, [(sc.names[t], sc.cls(t)) for t in tops]))
    other = [sc.names[k] for k in range(1, len(sc.nodes)) if PICK in sc.names[k] and k not in tops]
    if other:
        raise ValueError('other nodes carry the pickup name: %s' % other[:5])
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the live .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the live .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the live .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    big0 = {e: len(B[e]) for e in KB.BIG}
    # ---- .prp
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'nogren', skip=set(tops))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    # ---- .gms / .buf
    slot0 = A.slots()
    gone_ents = set()
    for t in tops:
        gone_ents |= set(B.ents[t - 1].walk())
    if len(gone_ents) != len(tops):
        raise ValueError('the pickups own %d entities, expected %d' % (len(gone_ents), len(tops)))
    for t in tops:
        A.remove(B.ents[t - 1])
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    allents = list(A.entities())
    if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    gids = {slot0[e] + 2 for e in gone_ents}
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids, gids), O.remap_ids(rmi, ids, gids), O.remap_ids(rmc, ids, gids)
    left = sum(1 for room in octn.rooms for t in room if t is not None for it in t.items) - \
        sum(1 for room in octx.rooms for t in room if t is not None for it in t.items if it[0] not in gids)
    if left:
        raise ValueError('%d room-tree items still name a removed entity' % left)
    moved = sum(1 for a, b in ids.items() if a != b)
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
    if move:
        prm = bytearray(B['.prm'])
        tt, nn = struct.unpack_from('<II', prm, 0)
        old = set(octx.record_refs())
        for i in range(1, nn):
            off, size = struct.unpack_from('<II', prm, tt + 16 * i)
            if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', prm, off + 0x1c, move[v])
                    repointed += 1
                elif v and v not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
        new_prm = bytes(prm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('room sets after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    if big0 != {e: len(new[B.ext[e]]) for e in KB.BIG}:
        raise ValueError('a large block changed its size')
    repl = {n: new[n] for e, n in B.ext.items() if new[n] != B.files[n]}
    rep = {'entities_before': len(B.ents), 'entities': len(allents), 'removed': sorted(sc.names[t] for t in tops), 'removed_refs': sorted(e.ref for e in gone_ents),
           'slot_ids_moved': moved, 'oct_records_moved': len(move), 'prm_roots_repointed': repointed,
           'members_changed': sorted(e for e, n in B.ext.items() if n in repl)}
    log('  stripped %d pickups (%d -> %d entities), %d slot ids renumbered, %d .oct records moved, %d .prm roots re-pointed; members %s'
        % (len(tops), len(B.ents), len(allents), moved, len(move), repointed, rep['members_changed']))
    del B
    return repl, rep


def verify(old_zip, new_zip, repl, log=print):
    """Reload both zips: pickups gone, every other node identical (class, path, values), other members byte for byte."""
    import zipfile, kl_fa, kl_fa_bots as KB, kl_octree as O, kl_prpjoin as J
    Bo, Bn = KB.Built(old_zip, SLOT), KB.Built(new_zip, SLOT)
    so, sn = Bo.sc, Bn.sc
    data, bad, _p, _n = J.check(sn, log=lambda *_a: None)
    bad0 = J.check(so, log=lambda *_a: None)[1]
    assert data == Bn['.prp'] and len(bad) == len(bad0), 'new .prp does not re-serialise / misfits %d (live %d)' % (len(bad), len(bad0))
    assert not any(PICK in sn.names[k] for k in range(1, len(sn.nodes))), 'a Grenade_Frag_0 node is left'
    def gren(sc, k):
        v = kl_fa.node_values(sc, k)
        return sc.cls(k) == 'ZFFItemWeapon' and any(isinstance(x, str) and 'Grenade' in x for x in v)
    assert not any(gren(sn, k) for k in range(1, len(sn.nodes))), 'a grenade ZFFItemWeapon is left'
    assert sum(gren(so, k) for k in range(1, len(so.nodes))) == 3, 'the live map should hold exactly 3 grenade ZFFItemWeapon'
    keep = [k for k in range(1, len(so.nodes)) if not is_pickup(so.names[k])]
    assert len(keep) == len(sn.nodes) - 1, 'node count %d vs %d' % (len(keep), len(sn.nodes) - 1)
    for i, k in enumerate(keep, 1):
        assert (so.path[k], so.cls(k)) == (sn.path[i], sn.cls(i)), 'node %d differs: %s vs %s' % (i, so.path[k], sn.path[i])
        assert kl_fa.node_values(so, k) == kl_fa.node_values(sn, i), 'values of %s differ' % so.path[k]
    rs = KB.room_sets_check(Bn.scene, O.Oct.parse(Bn['.oct']), O.RoomIndex.parse(Bn['.rmi']), O.RoomIndex.parse(Bn['.rmc']))
    rs0 = KB.room_sets_check(Bo.scene, O.Oct.parse(Bo['.oct']), O.RoomIndex.parse(Bo['.rmi']), O.RoomIndex.parse(Bo['.rmc']))
    assert rs == rs0, 'room sets %s vs %s' % (rs, rs0)
    del Bo, Bn
    with zipfile.ZipFile(old_zip) as zo, zipfile.ZipFile(new_zip) as zn:
        io, inn = zo.infolist(), zn.infolist()
        assert [i.filename for i in io] == [i.filename for i in inn], 'member order differs'
        diff = [a.filename for a, b in zip(io, inn) if a.CRC != b.CRC or a.file_size != b.file_size]
        assert sorted(diff) == sorted(repl), 'members that differ %s != planned %s' % (sorted(diff), sorted(repl))
        assert zn.testzip() is None
    log('  verify ok: %d nodes kept unchanged, room sets %s, changed members %s' % (len(keep), rs or 'clean', [os.path.basename(x) for x in sorted(repl)]))


INSTALL = r'''"""Installs / undoes DM01 NO GRENADE PICKUPS 1111 on the live DM01 files: Special!Pickups!Grenade_Frag_01..03 leave the map (plain + online bots zip). Backups <name>.before-dm01nogren_1111 next to the file (moved with os.replace, never overwritten or deleted), --undo restores byte-exact, --dry, --root, --skip-run-check.

  python install.py            install
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game|--root <dir>          another Dog Days folder (rehearsals on a copy); --skip-run-check to ignore a running game (rehearsals only)
Every live md5 is pinned BEFORE anything is written (all or nothing); refuses while a real kl2.exe runs (zombies under 50 MB ignored). Never touches KL_PortBackup."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM01', '.before-dm01nogren_1111'
FILES = %(files)r


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def real_game():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    except OSError:
        return True
    for ln in out.splitlines():
        p = [x.strip('"') for x in ln.split('","')]
        if len(p) >= 5 and p[0].lower() == 'kl2.exe' and int(''.join(c for c in p[4] if c.isdigit()) or 0) > 50000:
            return True
    return False


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = next((a[a.index(f) + 1] for f in ('--game', '--root') if f in a), GAME)
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and real_game():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %%s is not there' %% live); return 1
        cur = md5(live)
        print('%%-26s live %%s' %% (n, cur))
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %%s' %% bak); return 1
            if cur != new:
                print('REFUSED: %%s live md5 %%s is not the installed %%s' %% (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %%s is not md5 %%s' %% (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %%s live md5 %%s is not the pinned %%s (already installed, or another pass changed it: re-stage on the live files)' %% (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %%s missing or not md5 %%s' %% (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) for p in plan) + (256 << 20)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the new files + 256 MB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %%s %%s' %% ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                os.replace(bak, live)                                 # the new file is replaced by the original (no delete)
            else:
                shutil.copyfile(src, live + '.tmp')
                os.replace(live, bak)                                 # the original is MOVED, never deleted
                done.append((live, bak))
                os.replace(live + '.tmp', live)
            print('%%s: %%s %%s' %% (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                if os.path.exists(bak):
                    os.replace(bak, live)
        print('FAILED (%%s); %%s' %% (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''

README = '''DM01 NO GRENADE PICKUPS 1111  (Hot Coffee)
==========================================
Why: the owner wants the three grenade pickups gone from Hot Coffee.

What it changes (DM01 only: F01_Main.zip, F01_Main.bots.zip, F01_Main.bots.base.md5):
  The three top-level pickups Special!Pickups!Grenade_Frag_01..03 (added by kl_grenade_1025, 3 m in front of START spawns 02/04/06) leave the map:
  nothing to see, nothing to pick up. Removed like the stock FA maps have no such node: .prp, .gms/.buf (slot ids renumbered), .oct/.rmi/.rmc
  (room sets checked before == after)%(prm)s. %(n0)d -> %(n)d entities; all other nodes are identical (class, path, values).
  NOT changed: the Weapon\\Grenade_Fragmentation templates, the projectile patch (Rocket_Flare chain), the hook's [Grenade] feature, every other zip member.

Install:  INSTALL.bat  (or: python install.py)     Undo: UNDO.bat  (or: python install.py --undo)     Check only: python install.py --dry
Close the game first (a zombie kl2.exe under 50 MB is ignored). Pinned live md5s: %(pins)s
If another DM01 step changed the files since, install.py REFUSES (re-stage: python tools/kl_dm01_nogren_1111.py stage).
Backups: <name>.before-dm01nogren_1111 next to each file (moved, never deleted). Undo is byte exact. Needs about 0.6 GB free on C: to install.

Result: %(res)s
GUESSES: none about the engine beyond what kl_cover_strip_1026 already relied on (removing top-level entities with the slot renumbering); NOT run in the game.
A hook that waits for a grenade pickup ("no grenade with ammo") will simply find none on DM01.
'''


def render_install(files):
    return INSTALL % dict(files=[tuple(f) for f in files])


def rehearsal(out, files, game, log):
    """install / 2nd install refused / --dry / undo byte exact on a COPY (never the game folder)."""
    scr = os.path.join(out, '_scratch')
    shutil.rmtree(scr, ignore_errors=True)
    d = os.path.join(scr, 'KLExpansion', 'Maps', MAP)
    os.makedirs(d)
    live = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    for n, _o, _w in files:
        shutil.copyfile(os.path.join(live, n), os.path.join(d, n))
    py = [sys.executable, os.path.join(out, 'install.py'), '--game', scr, '--skip-run-check']

    def run(*x):
        r = subprocess.run(py + list(x), capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    try:
        rc, t = run('--dry'); assert rc == 0, t
        rc, t = run(); assert rc == 0, t
        for n, o, w in files:
            assert fmd5(os.path.join(d, n)) == w and fmd5(os.path.join(d, n + TAG)) == o, n
        rc, t = run(); assert rc == 1 and 'REFUSED' in t, 'second install must be refused: %d %s' % (rc, t)
        rc, t = run('--undo', '--dry'); assert rc == 0, t
        rc, t = run('--undo'); assert rc == 0, t
        for n, o, w in files:
            assert fmd5(os.path.join(d, n)) == o and not os.path.exists(os.path.join(d, n + TAG)), 'undo not byte exact: ' + n
        rc, t = run('--undo'); assert rc == 1, 'undo with no backup must be refused'
        open(os.path.join(d, files[0][0]), 'ab').write(b'x')
        rc, t = run(); assert rc == 1 and 'pinned' in t, 'a changed live file must be refused'
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    log('rehearsal ok: install, 2nd install refused, --dry, undo byte exact, no-backup undo refused, changed live refused')


def stage(out=OUT, game=DD, rehearse=True, log=print):
    live_dir = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    live = {n: os.path.join(live_dir, n) for n in FILES}
    pins = {n: fmd5(p) for n, p in live.items() if n.endswith('.zip')}
    for n, h in PINS.items():
        if pins[n] != h:
            raise SystemExit('REFUSED: live %s is %s, not the pinned %s (another install came in: re-check)' % (n, pins[n], h))
    if open(live[FILES[2]]).read().strip() != pins[FILES[0]]:
        raise SystemExit('REFUSED: the live bots.base.md5 is not the live plain zip md5')
    pins[FILES[2]] = fmd5(live[FILES[2]])
    need = 3 * os.path.getsize(live[FILES[0]]) + os.path.getsize(live[FILES[1]]) + FREE_KEEP
    os.makedirs(out, exist_ok=True)
    if shutil.disk_usage(out).free < need:
        raise SystemExit('REFUSED: less than %d MB free on the stage drive' % (need >> 20))
    import kl_loot_1025 as LO
    reports = {}
    for n in FILES[:2]:
        log('== %s (%s)' % (n, pins[n]))
        src = os.path.join(out, '_src_' + SLOT + '_Main.zip')
        shutil.copyfile(live[n], src)       # Built wants the <slot>_Main name; the copy is deleted below
        try:
            repl, rep = strip(src, log)
            dst = os.path.join(out, n)
            LO.patch_zip(src, dst, repl)
            verify(src, dst, repl, log)
        finally:
            if os.path.exists(src):
                os.remove(src)
        reports[n] = rep
    base = fmd5(os.path.join(out, FILES[0]))
    open(os.path.join(out, FILES[2]), 'w', newline='\n').write(base + '\n')
    files = [(FILES[0], pins[FILES[0]], base), (FILES[1], pins[FILES[1]], fmd5(os.path.join(out, FILES[1]))),
             (FILES[2], pins[FILES[2]], fmd5(os.path.join(out, FILES[2])))]
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as f:
        f.write(render_install(files))
    for nm, arg in (('INSTALL.bat', ''), ('UNDO.bat', ' --undo')):
        with open(os.path.join(out, nm), 'w', newline='') as f:
            f.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    r0 = reports[FILES[0]]
    prm = ' and the .prm model roots re-pointed (%d)' % r0['prm_roots_repointed'] if r0['prm_roots_repointed'] else ''
    with open(os.path.join(out, 'README.txt'), 'w', newline='\n') as f:
        f.write(README % dict(prm=prm, n=r0['entities'], n0=r0['entities_before'], pins=', '.join('%s %s' % (n, h[:8]) for n, h in pins.items()),
                              res=', '.join('%s %s -> %s' % (n, o[:8], w[:8]) for n, o, w in files)))
    with open(os.path.join(out, 'build_report.json'), 'w') as f:
        json.dump(dict(pins=pins, files=files, reports=reports), f, indent=1)
    if rehearse:
        rehearsal(out, files, game, log)
    for n, o, w in files:
        log('%-26s %s -> %s' % (n, o, w))
    return files


def main(a):
    if not a or a[0] != 'stage':
        print(__doc__)
        return 2

    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    stage(opt('--out', OUT), opt('--game', DD), '--no-rehearse' not in a)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
