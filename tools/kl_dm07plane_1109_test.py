"""Off-game self-test of tools/kl_dm07plane_1109.py: the HVK edit on SYNTHETIC HVKs of the real layout (a donor plane with the real DD10 numbers, a 12-placement map with
the two panel slots and a host-REF slot), the refusals, the free-space guard, the generated install.py, the zip repack; plus, read-only, the pinned live DM07 HVK + the
DD10 donor when both are on this machine (skips that part otherwise). Writes only into a temp dir. One RESULT: line."""
import os, struct, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hvk
import kl_dm07plane_1109 as T

# the real donor (DD10 ColiObj_HERO_Plane01, REF 31216): placement, vertices, indices, MOPP
D_INST = struct.pack('<12f', 80.17859649658203, 2.4724998474121094, 10.010499954223633, -4.3711398944878965e-08, 1.0, 0.0, -1.0, -4.3711398944878965e-08, 0.0, 0.0, 0.0, 1.0) + struct.pack('<II', 31216, 0)
D_VERTS = b''.join(struct.pack('<3f', x, -1.0807656281031086e-07, z) for x, z in ((-2.986953020095825, 3.4833624362945557), (-2.986953020095825, -3.4833624362945557), (2.986953020095825, 3.4833624362945557), (2.986953020095825, -3.4833624362945557)))
D_OFF = bytes.fromhex(T.PINS['donor_mopp_offset'])
D_CODE = bytes.fromhex(T.PINS['donor_mopp_code'])


def shape(verts, inst, sub, mopp, flags=0x66, nidx=(3, 1, 2, 2, 1, 0)):
    s = kl_hvk.Shape()
    s.type, s.flags, s.convex, s.vstride, s.istride = kl_hvk.STATIC, flags, 0, 12, 6
    s.verts, s.idx, s.inst, s.sub, s.mopp = verts, struct.pack('<%dH' % len(nidx), *nidx), list(inst), list(sub), list(mopp)
    return s


def hvk(shapes, box, lists, tail=bytes(32)):
    h = kl_hvk.Hvk.__new__(kl_hvk.Hvk)
    h.shapes, h.box, h.lists, h.tail = shapes, box, lists, tail
    return h.serialize()


def donor_raw():
    from kl_dm02fix_1108 import mopp_offset
    ds = kl_hvk.Hvk.__new__(kl_hvk.Hvk)
    s = shape(D_VERTS, [D_INST], [(0, 0x108, 2)], [(D_OFF, D_CODE)], flags=0x108)
    assert all(abs(a - b) < 1e-5 for a, b in zip(struct.unpack('<3f', mopp_offset(D_INST, s)), struct.unpack('<3f', D_OFF[:12]))), 'fixture: donor offset formula'
    filler = shape(D_VERTS, [D_INST[:0x30] + struct.pack('<II', 1, 0)], [(0, 0x72, 2)], [(D_OFF, D_CODE)])
    return hvk([filler, s], (-300, -300, -300, 300, 300, 300), [(D_OFF, D_CODE)])


def panel_inst(ref, x, z):
    return struct.pack('<12f', x, 4.71456, z, -1.0, 0.0, -1.5e-07, 0.0, 1.0, 0.0, 1.5e-07, 0.0, -1.0) + struct.pack('<II', ref, 0)


def box_verts():
    return b''.join(struct.pack('<3f', x, y, z) for x in (-0.02, 0.02) for y in (-3.3, 0.0) for z in (-2.0, 2.0))


def map_raw(pins, host_ref=None):
    from kl_dm02fix_1108 import mopp_offset
    shapes, k = [], 0
    for n in range(pins['static_n']):
        ref = {3: 21457, 7: 21449, 10: pins['host_ref']}.get(n, 5000 + n)
        z = {3: 101.93, 7: 105.955}.get(n, 20.0 + n)
        sub = [(0, 0x66, 12)] if n in (3, 7) else [(0, 0x108, 24)] if n == 10 else [(0, 0x72, 4)]
        s = shape(box_verts(), [panel_inst(ref, -45.99, z)], sub, [(b'\0' * 12 + b'\x01\x02\x03\x04', bytes([n + 1, 9, 9]))])
        s.mopp[0] = (mopp_offset(s.inst[0], s)[:12] + b'\x01\x02\x03\x04', s.mopp[0][1])
        shapes.append(s)
    return hvk(shapes, (-200, -50, -200, 200, 200, 200), [(struct.pack('<4f', -300, -30, -300, 0), b'\x09\x08')])


def refs_of(raw):
    h = kl_hvk.Hvk(raw)
    return [kl_hvk.ref(h.shapes[si].inst[i]) for si, i in T.statics(h)]


def refuses(fn, word):
    try:
        fn()
    except ValueError as e:
        assert word in str(e), (word, str(e))
        return
    raise SystemExit('FAIL: no refusal containing %r' % word)


def main():
    pins = dict(T.PINS, static_n=12)
    raw, dr = map_raw(pins), donor_raw()
    data, rep = T.plan(raw, dr, 0x108, pins)
    r0, r1 = refs_of(raw), refs_of(data)
    assert [n for n in range(12) if r0[n] != r1[n]] == [3, 7] and r1[3] == r1[7] == pins['host_ref'], 'replaced slots'
    assert [r['slot'] for r in rep] == [3, 7] and len(kl_hvk.Hvk(data).shapes) == 12 and kl_hvk.Hvk(data).static_count() == 12
    h = kl_hvk.Hvk(data)
    st = T.statics(h)
    for n, zc in ((3, 10200.0), (7, 10600.0)):
        s = h.shapes[st[n][0]]
        lo, hi = T.world_box(s.inst[0], s)
        assert abs(lo[0] + 4578) < 0.01 and abs(hi[0] + 4578) < 0.01, (lo, hi)
        assert abs(lo[1] - 381.3) < 0.1 and abs(hi[1] - 978.7) < 0.1 and abs((lo[2] + hi[2]) / 2 - zc) < 0.01 and abs(hi[2] - lo[2] - 696.7) < 0.1, (lo, hi)
        assert s.sub == [(0, 0x108, 2)] and s.mopp[0][1] == D_CODE and s.mopp[0][0][12:] == D_OFF[12:], 'donor sub / code / scale float kept'
        assert s.verts == D_VERTS and struct.unpack_from('<9f', s.inst[0], 12) == struct.unpack_from('<9f', D_INST, 12), 'donor shape + rotation kept'
    # the two planes meet in z (joint coverage 9851..10949 over the gap 9990..10800)
    b = [T.world_box(h.shapes[st[n][0]].inst[0], h.shapes[st[n][0]]) for n in (3, 7)]
    assert b[0][1][2] > b[1][0][2] and b[0][0][2] < 9990 and b[1][1][2] > 10800
    # the sub variant
    d72, _r = T.plan(raw, dr, 0x72, pins)
    h72 = kl_hvk.Hvk(d72)
    assert h72.shapes[st[3][0]].sub == [(0, 0x72, 2)] and h72.shapes[st[3][0]].flags == 0x72
    # deterministic
    assert T.plan(raw, dr, 0x108, pins)[0] == data
    # refusals
    refuses(lambda: T.plan(data, dr, 0x108, pins), 'already replaced')
    refuses(lambda: T.plan(raw, dr, 0x108, dict(pins, static_n=13)), 'static count')
    refuses(lambda: T.plan(raw, dr, 0x108, dict(pins, donor_mopp_code='00')), 'MOPP')
    refuses(lambda: T.plan(raw, dr, 0x108, dict(pins, host_ref=77)), 'host REF')
    refuses(lambda: T.plan(raw, dr, 0x108, dict(pins, panels=((21457, 10200.0), (21449, 11200.0)))), 'cover')
    refuses(lambda: T.plan(raw, dr, 0x108, dict(pins, gap=dict(pins['gap'], y=(100.0, 801.0)))), 'reach')
    refuses(lambda: T.plan(raw, raw, 0x108, pins), 'donor REF')
    refuses(lambda: T.plan(raw[:-16] + b'\1' * 16, dr, 0x108, pins), '')                                 # a damaged file never passes the round trip / parser silently
    # audit catches a stray change (a third record replaced)
    h3 = kl_hvk.Hvk(data)
    h3.shapes[0] = h3.shapes[st[3][0]]
    refuses(lambda: T.audit(raw, h3.serialize(), [3, 7], pins), 'differ')
    # the plane recipe leaves the list MOPP, header box and tail alone
    assert h.lists == kl_hvk.Hvk(raw).lists and h.box == kl_hvk.Hvk(raw).box
    # check(): stock zip -> False, plane zip -> True (synthetic zips)
    with tempfile.TemporaryDirectory() as td:
        for nm, body, want in (('stock.zip', raw, False), ('plane.zip', data, True)):
            zp = os.path.join(td, nm)
            with zipfile.ZipFile(zp, 'w') as z:
                z.writestr('X/F06_Main.HVK', body)
            assert T.check(zp, pins, out=lambda *_a: None) is want, 'check() on ' + nm
    # kit
    t = T.kit_text([('F06_Main.zip', 'a' * 32, 'b' * 32)])
    compile(t, 'install.py', 'exec')
    assert T.TAG in t and 'sink' not in t.lower() and '@' not in t.replace('@echo', ''), 'kit template'
    # free-space guard: refuses before anything is read or written
    with tempfile.TemporaryDirectory() as td:
        live = os.path.join(td, 'live')
        os.makedirs(live)
        for n in ('F06_Main.zip', 'F06_Main.bots.zip'):
            with open(os.path.join(live, n), 'wb') as f:
                f.write(b'x' * 4096)
        real = T.shutil.disk_usage
        try:
            T.shutil.disk_usage = lambda p: type('U', (), {'free': 1 << 20})()
            msg = T.need_free(os.path.join(td, 'not', 'yet'), live)
            assert msg and msg.startswith('REFUSED') and 'MB free' in msg, msg
            refuses(lambda: T.stage(os.path.join(td, 'out'), live), 'REFUSED')
            assert not os.path.exists(os.path.join(td, 'out')), 'stage created its output before the space check'
            T.shutil.disk_usage = lambda p: type('U', (), {'free': 1 << 30})()
            assert T.need_free(td, live) is None
        finally:
            T.shutil.disk_usage = real
        # zip repack keeps names, order, compression; only the HVK member changes
        src, dst = os.path.join(td, 'a.zip'), os.path.join(td, 'b.zip')
        with zipfile.ZipFile(src, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('X/F06_Main.prp', b'prp' * 100)
            z.writestr('X/F06_Main.HVK', raw)
            z.writestr('X/F06_Main.oct', b'oct')
        T.repack(src, dst, 'X/F06_Main.HVK', data)
        with zipfile.ZipFile(dst) as z:
            assert z.read('X/F06_Main.HVK') == data and z.namelist() == ['X/F06_Main.prp', 'X/F06_Main.HVK', 'X/F06_Main.oct']
            assert T.hvk_member(z) == 'X/F06_Main.HVK'
    # install / undo round trip of the generated kit on tiny synthetic files (scratch game folder, --skip-run-check: never touches a real game)
    import hashlib, subprocess
    md = lambda b: hashlib.md5(b).hexdigest()
    with tempfile.TemporaryDirectory() as td:
        stg, game = os.path.join(td, 'stage'), os.path.join(td, 'game')
        mp = os.path.join(game, 'KLExpansion', 'Maps', 'DM07')
        os.makedirs(stg)
        os.makedirs(mp)
        names = ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5')
        old = {n: b'old ' + n.encode() for n in names}
        new = {n: b'new ' + n.encode() for n in names}
        for n in names:
            open(os.path.join(mp, n), 'wb').write(old[n])
            open(os.path.join(stg, n), 'wb').write(new[n])
        T.write_kit(stg, [(n, md(old[n]), md(new[n])) for n in names], md(old['F06_Main.zip']))
        kit = lambda *a: subprocess.run([sys.executable, os.path.join(stg, 'install.py'), '--game', game, '--skip-run-check', '--min-free-mb', '1'] + list(a), capture_output=True, text=True)
        live = lambda n: open(os.path.join(mp, n), 'rb').read()
        r = kit()
        assert r.returncode == 0 and all(live(n) == new[n] for n in names), r.stdout + r.stderr
        assert all(open(os.path.join(mp, n + T.TAG), 'rb').read() == old[n] for n in names), 'backups'
        assert kit().returncode != 0 and all(live(n) == new[n] for n in names), '2nd install must refuse'
        r = kit('--undo')
        assert r.returncode == 0 and all(live(n) == old[n] for n in names), r.stdout + r.stderr
        assert not any(os.path.exists(os.path.join(mp, n + T.TAG)) for n in names), 'backups consumed by undo'
        assert kit('--undo').returncode != 0, 'undo twice must refuse'
        assert T.game_drive_note(stg, stg)[0] is False
    # live, read-only: the pinned DM07 HVK + the DD10 donor
    note = 'live skipped'
    zp = os.path.join(T.LIVE_DIR, 'F06_Main.zip')
    if os.path.isfile(zp) and os.path.isfile(T.DONOR_ZIP) and T.md5(zp) == T.LIVE_MD5['F06_Main.zip']:
        with zipfile.ZipFile(zp) as z:
            live_raw = z.read(T.hvk_member(z))
        d, rp = T.plan(live_raw, T.read_donor(T.DONOR_ZIP))
        assert sorted(r['slot'] for r in rp) == [248, 256]
        assert kl_hvk.Hvk(d).static_count() == 2777
        note = 'live DM07 slots 248/256 planned (HVK %d -> %d bytes)' % (len(live_raw), len(d))
    print('RESULT: OK kl_dm07plane_1109 (%s)' % note)
    return 0


if __name__ == '__main__':
    sys.exit(main())
