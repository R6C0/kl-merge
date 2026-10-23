"""
kl_hud_marks_test.py - the slot-number TEST BAKE (kl_hud.mark_slots / stamp_pixels, re/hud_killfeed_plan.md step 0) on a
SYNTHETIC Dog Days .TEX: no game files. Checks that every listed picture is stamped in its corner and nothing else in it
changes, that pictures outside the list (or outside `which`) and the record words are untouched, that DXT1 / DXT3 / DXT5 /
ABGR records all come out as ABGR of the same size under the same id, that the step is a byte-for-byte no-op when the
flag is off, and that the CLI refuses the flag without --test-bake or without TEST in the output name.

    python tools/kl_hud_marks_test.py          -> RESULT: PASS / FAIL
"""
import os, struct, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_hud as H
import kl_hud_marks as M
import kl_texmat as T

FAILS = []


def check(cond, what):
    if not cond:
        FAILS.append(what)
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))


def c565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def record(tid, fmt, w, h, rgb, alpha=255, name='tex:UserInterface/Synthetic#%d'):
    """a .TEX record in the shape kl_hud reads: 36 header bytes, name + NUL, u32 n, pixels; one mip, a flat colour"""
    c = c565(*rgb)
    if fmt == 'ABGR':
        px = bytes(rgb) + bytes((alpha,))
        data = px * (w * h)
    else:
        blocks = (w // 4) * (h // 4)
        colour = struct.pack('<HHI', c, c, 0)
        if fmt == 'DXT1':
            data = colour * blocks
        elif fmt == 'DXT3':
            data = (struct.pack('<Q', int('%x' % (alpha >> 4) * 16, 16)) + colour) * blocks
        else:                                               # DXT5: a0 = a1 = alpha, every index 0
            data = (bytes((alpha, alpha)) + bytes(6) + colour) * blocks
    nm = (name % tid).encode('latin1') + b'\0'
    body = struct.pack('<4s4sIHHIIfI', fmt.encode()[::-1], fmt.encode()[::-1], tid, h, w, 1, 0x10002, 1.0, 0) + nm + struct.pack('<I', len(data)) + data
    return struct.pack('<I', len(body) + 4) + body


def synthetic_tex():
    t = T.Tex('dd')
    t.tex[951] = T.Texture(record(951, 'DXT1', 64, 64, (96, 128, 160)))
    t.tex[952] = T.Texture(record(952, 'DXT5', 64, 64, (200, 40, 40), 160))
    t.tex[953] = T.Texture(record(953, 'DXT3', 128, 32, (40, 200, 40), 0xee))
    t.tex[954] = T.Texture(record(954, 'ABGR', 32, 32, (10, 10, 10), 255))
    t.tex[955] = T.Texture(record(955, 'DXT1', 256, 256, (128, 128, 128)))
    t.tex[960] = T.Texture(record(960, 'DXT5', 64, 64, (1, 2, 3), 77))       # in no slot
    return t


def pixels_of(entry):
    q = entry.index(b'\0', 36) + 1
    n = struct.unpack_from('<I', entry, q)[0]
    return entry[q + 4:q + 4 + n]


def main():
    print('kl_hud_marks_test: synthetic .TEX')
    slots = {0: 953, 2: 951, 52: 952, 53: 952, 178: 954, 181: 955}       # 952 sits in two slots, as 109 / 193 share a stock picture

    # 1. stamp_pixels: deterministic, corner only, digits present
    w, h = 64, 64
    base = bytearray(bytes((96, 128, 160, 255)) * (w * h))
    a = bytearray(base); bw, bh = H.stamp_pixels(a, w, h, [178])
    b = bytearray(base); H.stamp_pixels(b, w, h, [178])
    check(a == b, 'stamp is deterministic')
    check(bw <= w // 2 + 4 and bh <= h // 2, 'stamp stays in the corner (%dx%d of %dx%d)' % (bw, bh, w, h))
    outside = all(a[4 * (y * w + x):4 * (y * w + x) + 4] == base[:4] for y in range(h) for x in range(w) if x >= bw or y >= bh)
    check(outside, 'every pixel outside the box is unchanged')
    inside = [bytes(a[4 * (y * w + x):4 * (y * w + x) + 4]) for y in range(bh) for x in range(bw)]
    check(bytes(H.MARK_CHALK) + b'\xff' in inside and bytes(H.MARK_INK) + b'\xff' in inside and bytes(H.MARK_EDGE) + b'\xff' in inside,
          'the box has ink, chalk digits and a coral edge')
    one = bytearray(base); H.stamp_pixels(one, w, h, [5])
    two = bytearray(base); bw2, bh2 = H.stamp_pixels(two, w, h, [5, 199])
    check(one != two and bh2 > bh, 'a picture in two slots gets a second row')
    tiny = bytearray(bytes(4) * 32 * 32); bwt, bht = H.stamp_pixels(tiny, 32, 32, [193])
    check(bwt <= 32 and bht <= 32 and max(tiny) == 255, '32 x 32 icon: the stamp fits and is drawn')
    tall = bytearray(bytes(4) * 32 * 8); H.stamp_pixels(tall, 32, 8, [1, 2, 3])
    check(True, 'an over-tall stamp is clipped, no exception')

    # 2. mark_slots on the synthetic .TEX
    t = synthetic_tex()
    stock = {k: v.entry for k, v in t.tex.items()}
    log = []
    new = H.mark_slots(t, slots, None, log.append)
    check(set(new) == {951, 952, 953, 954, 955}, 'every listed id stamped once: %s' % sorted(new))
    check(960 not in new and t.tex[960].entry == stock[960], 'a texture in no slot is untouched')
    check(all(t.tex[k].entry == stock[k] for k in stock), 'mark_slots itself writes nothing into the Tex (the caller does)')
    for tid, (e, sl) in new.items():
        size, f1, f2, hid, th, tw, mips, fl, sc, x20 = struct.unpack_from('<I4s4sIHHIIfI', e, 0)
        _s, sf1, _sf2, _sid, sth, stw, _sm, sfl, ssc, sx20 = struct.unpack_from('<I4s4sIHHIIfI', stock[tid], 0)
        check(f1 == b'ABGR' and hid == tid and (tw, th) == (stw, sth) and mips == 1 and fl == sfl & ~0x100 and (sc, x20) == (ssc, sx20) and size == len(e),
              'id %d: ABGR record, same id / size / words (%s -> ABGR %dx%d)' % (tid, sf1[::-1].decode(), tw, th))
        check(e[36:e.index(b'\0', 36)] == stock[tid][36:stock[tid].index(b'\0', 36)], 'id %d: same name' % tid)
        sw, sh, spx = M.decode(stock[tid])
        px = pixels_of(e)
        check(len(px) == 4 * tw * th, 'id %d: one mip of pixels' % tid)
        ref = bytearray(spx); bw, bh = H.stamp_pixels(ref, sw, sh, sl)
        check(px == bytes(ref), 'id %d: pixels = the decoded stock picture with the stamp %s' % (tid, sl))
        untouched = all(px[4 * (y * tw + x):4 * (y * tw + x) + 4] == spx[4 * (y * tw + x):4 * (y * tw + x) + 4]
                        for y in range(th) for x in range(tw) if x >= bw or y >= bh)
        check(untouched, 'id %d: nothing outside the %dx%d box changed' % (tid, bw, bh))
    check(new[952][1] == [52, 53], 'id 952 carries both its slots: %s' % new[952][1])
    last = pixels_of(new[953][0])[4 * (31 * 128 + 127):4 * (31 * 128 + 127) + 4]
    check(new[953][1] == [0] and last[3] == 0xee and max(abs(a - b) for a, b in zip(last[:3], (40, 200, 40))) <= 2,
          'DXT3 (slot 0): the 4-bit alpha 0xee and the 565 colour decoded off the stamp (%s)' % list(last))

    # 3. `which` narrows the stamping
    t = synthetic_tex()
    new = H.mark_slots(t, slots, {52, 178}, lambda *_: None)
    check(set(new) == {952, 954} and new[952][1] == [52], 'which={52,178}: only 952 (slot 52 alone) and 954: %s' % {k: v[1] for k, v in new.items()})
    check(H.parse_slots('52,53,127-160,178') == {52, 53, 178} | set(range(127, 161)), 'parse_slots ranges')
    check(H.parse_slots('all') == set() and H.parse_slots('') == set(), 'parse_slots all / empty = every slot')
    try:
        H.parse_slots('200'); check(False, 'parse_slots refuses 200')
    except ValueError:
        check(True, 'parse_slots refuses 200')

    # 4. the step is a no-op when the flag is off (the plain bake is byte-identical), and refuses a non-TEST folder when on
    t = synthetic_tex()
    files = {'X_Main.TEX': T.write_tex(t)}
    before = dict(files)
    H.MARK_SLOTS = None
    r = H.apply_marks(files, {'.TEX': 'X_Main.TEX'}, '/nonexistent/out_plain', lambda *_: None)
    check(r == {} and files == before, 'MARK_SLOTS None: apply_marks changes nothing (byte-identical .TEX)')
    H.MARK_SLOTS = set()
    try:
        H.apply_marks(files, {'.TEX': 'X_Main.TEX'}, '/nonexistent/out_plain', lambda *_: None)
        check(False, 'MARK_SLOTS on: a folder without TEST is refused')
    except ValueError as ex:
        check('TEST' in str(ex) and files == before, 'MARK_SLOTS on: a folder without TEST is refused before anything is written')
    H.MARK_SLOTS = None

    # 5. the CLI guard: --mark-slots without --test-bake, or without TEST in the folder name, stops before any work
    def cli(args):
        try:
            H._test_bake_options(list(args), args[2]); return 'ran'
        except SystemExit as ex:
            return 'refused: %s' % ex
    check(cli(['all', 'in', 'out_TEST', '--mark-slots', '52,53']).startswith('refused'), 'CLI: --mark-slots alone is refused')
    check(cli(['all', 'in', 'out_TEST', '--test-bake']).startswith('refused'), 'CLI: --test-bake alone is refused')
    check(cli(['all', 'in', 'out_shipping', '--test-bake', '--mark-slots']).startswith('refused'), 'CLI: no TEST in the folder name is refused')
    H.MARK_SLOTS = None
    a = ['all', 'in', 'out_TEST', '--look', 'deadmen', '--test-bake', '--mark-slots', '52,53']
    check(cli(a) == 'ran' and H.MARK_SLOTS == {52, 53}, 'CLI: both flags + TEST folder: MARK_SLOTS = {52, 53}')
    a = ['all', 'in', 'K1_TEST', '--test-bake', '--mark-slots', '--look', 'deadmen']
    H.MARK_SLOTS = None
    b = list(a); H._test_bake_options(b, b[2])
    check(H.MARK_SLOTS == set() and b == ['all', 'in', 'K1_TEST', '--look', 'deadmen'], 'CLI: --mark-slots with no list = every slot, other options kept')
    H.MARK_SLOTS = None
    check(H.MARK_SLOTS is None, 'module default: MARK_SLOTS is None (a library caller such as kl_graft never stamps)')

    # 6. the whole step on the synthetic .TEX into a TEST folder: the written .TEX reads back with the stamps
    t = synthetic_tex()
    files = {'X_Main.TEX': T.write_tex(t)}
    H.MARK_SLOTS = set()
    out = os.path.join(tempfile.mkdtemp(), 'K1_TEST')
    try:
        H.hud_slots, saved = (lambda files_, ext_: dict(slots)), H.hud_slots
        try:
            r = H.apply_marks(files, {'.TEX': 'X_Main.TEX'}, out, lambda *_: None)
        finally:
            H.hud_slots = saved
        check(set(r) == {951, 952, 953, 954, 955}, 'apply_marks: five ids stamped')
        t2 = T.read_tex(files['X_Main.TEX'])
        check(all(struct.unpack_from('<4s', t2.tex[k].entry, 4)[0] == b'ABGR' for k in r) and t2.tex[960].entry == t.tex[960].entry,
              'written .TEX: stamped ids are ABGR, the unlisted one is byte-identical')
        note = open(os.path.join(out, 'TEST_BAKE_mark_slots.txt')).read()
        check('TEST BAKE' in note and ' 52  id  952' in note and '178  id  954' in note, 'TEST_BAKE_mark_slots.txt lists slot -> id -> name')
    finally:
        H.MARK_SLOTS = None

    print('RESULT: %s (%d checks failed)' % ('PASS' if not FAILS else 'FAIL', len(FAILS)))
    for f in FAILS:
        print('   ', f)
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
