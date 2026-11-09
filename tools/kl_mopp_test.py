"""kl_mopp_test.py - off-game checks of kl_mopp.py (2026-11-09). Run: python kl_mopp_test.py
Synthetic part always: hand-built codes for every opcode class, the pinned DD10 HERO plane code of kl_dm07plane_1109.
Real-file part when it finds .HVK files: $KL_MOPP_HVK (a folder of *.HVK) or the live DM07 / DD10 zips under <DD>\\KLExpansion\\Maps:
every code 100 %% byte coverage, list terminals = the real children of each 510-block (the fillers are never returned), every real
child's world box inside its reach box, >= 99.5 %% of triangle centres reach their own terminal with Code.query."""
import glob
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_hvk                          # noqa: E402
import kl_mopp as M                    # noqa: E402

fails = 0


def check(ok, what):
    global fails
    print(('  ok   ' if ok else '  FAIL ') + what)
    if not ok:
        fails += 1


def off16(x, y, z, scale):
    return struct.pack('<4f', x, y, z, scale)


# ---------------- synthetic: one code per opcode class; offset 0, scale 65536 -> 1 metre = 1 unit, 254 m box
OFF = off16(0.0, 0.0, 0.0, 65536.0)

# SPLIT x: a=10 (left v <= 10), b=12 (right v >= 12), right child 1 byte further: left TERM 0, right TERM 1
c = M.Code(OFF, bytes([0x10, 10, 12, 1, 0x30, 0x31]))
check(sorted(c.terms) == [0, 1] and c.coverage() == 1.0, 'SPLIT: two terminals, every byte walked')
check(c.query([5, 0, 0]) == [0] and c.query([20, 0, 0]) == [1] and c.query([11, 0, 0]) == [], 'SPLIT: v <= a left, v >= b right, the gap between reaches nothing')
check(c.query([10.9, 0, 0]) == [0] and c.query([12.0, 0, 0]) == [1], 'SPLIT: the byte compare is floor(v)')
lo, hi = c.reach(0); check(hi[0] == 11.0 and lo[0] == 0.0, 'SPLIT: reach of the left child ends at a + 1 (exclusive): %s' % hi[0])
lo, hi = c.reach(1); check(lo[0] == 12.0, 'SPLIT: reach of the right child starts at b')
# overlapping children (a >= b): a point in the overlap reaches both
c = M.Code(OFF, bytes([0x11, 20, 15, 1, 0x30, 0x31]))
check(c.query([0, 17, 0]) == [0, 1] and c.query([0, 10, 0]) == [0] and c.query([0, 30, 0]) == [1], 'SPLIT y with overlapping children: both in the overlap')
# SINGLE SPLIT z, t = 100
c = M.Code(OFF, bytes([0x22, 100, 1, 0x30, 0x31]))
check(c.query([0, 0, 99]) == [0] and c.query([0, 0, 100]) == [0, 1] and c.query([0, 0, 101]) == [1], 'SINGLE SPLIT: v <= t left, v >= t right (v == t both)')
# SPLIT16 x: left at end + 2 (skips a 2-byte TERM8), right at end + 0
c = M.Code(OFF, bytes([0x23, 50, 60, 0, 2, 0, 0, 0x50, 7, 0x50, 9]))
check(c.query([40, 0, 0]) == [9] and c.query([70, 0, 0]) == [7] and c.coverage() == 1.0, 'SPLIT16: 16-bit jumps for both children, TERM8 ids')
# CUT y 10..20 then TERM 3; outside = nothing
c = M.Code(OFF, bytes([0x27, 10, 20, 0x33]))
check(c.query([0, 10, 0]) == [3] and c.query([0, 20.99, 0]) == [3] and c.query([0, 21, 0]) == [] and c.query([0, 9.99, 0]) == [], 'CUT: lo <= floor(v) <= hi')
lo, hi = c.reach(3); check(lo[1] == 10.0 and hi[1] == 21.0, 'CUT: reach y 10..21 (hi + 1 exclusive)')
# CUT24 x: 1.5 .. 2.5 units in 24-bit = 98304 .. 163840
c = M.Code(OFF, bytes([0x29, 0x01, 0x80, 0x00, 0x02, 0x80, 0x00, 0x30]))
check(c.query([1.5, 0, 0]) == [0] and c.query([2.5, 0, 0]) == [0] and c.query([1.49, 0, 0]) == [] and c.query([2.51, 0, 0]) == [], 'CUT24: big-endian 24-bit bounds, inclusive')
# JUMP8 over a dead TERM, then TERM 2
c = M.Code(OFF, bytes([0x05, 1, 0x31, 0x32]))
check(c.query([0, 0, 0]) == [2] and c.coverage() == 0.75, 'JUMP8 skips one byte (the dead TERM 1 stays unwalked = 75 %% coverage)')
# base: ADD 100, ADD16 0x0102, SET32 7 then TERM4_1
c = M.Code(OFF, bytes([0x09, 100, 0x31]))
check(c.query([0, 0, 0]) == [101], 'ADD8 base')
c = M.Code(OFF, bytes([0x0a, 0x01, 0x02, 0x31]))
check(c.query([0, 0, 0]) == [0x0102 + 1], 'ADD16 base is big-endian')
c = M.Code(OFF, bytes([0x09, 5, 0x0b, 0, 0, 0, 7, 0x31]))
check(c.query([0, 0, 0]) == [8], 'SET32 base replaces the base')
c = M.Code(OFF, bytes([0x52, 0x01, 0x00, 0x00]))
check(c.query([0, 0, 0]) == [65536], 'TERM24 id big-endian')
# SCALE2 (100, 0, 0): x' = (x - 100) * 4; then SPLIT x a=7 b=8 -> left x < 102 (x' <= 7 -> x' < 8 -> x < 102), right x >= 102
c = M.Code(OFF, bytes([0x02, 100, 0, 0, 0x10, 7, 8, 1, 0x30, 0x31]))
check(c.query([101.9, 0, 0]) == [0] and c.query([102.0, 0, 0]) == [1] and c.query([101.99, 0, 0]) == [0], 'SCALE: 8-bit compares in the scaled frame')
lo, hi = c.reach(0); check(abs(hi[0] - 102.0) < 1e-9, 'SCALE: the reach box is mapped back to the root frame (left ends at 102): %s' % hi[0])
lo, hi = c.reach(1); check(abs(lo[0] - 102.0) < 1e-9, 'SCALE: right starts at 102 in the root frame')
# SCALE then CUT24: the 24-bit cut reads the ROOT coordinate (x 101.5 .. 102.5 -> 0x658000 .. 0x668000)
c = M.Code(OFF, bytes([0x02, 100, 0, 0, 0x29, 0x65, 0x80, 0x00, 0x66, 0x80, 0x00, 0x30]))
check(c.query([102, 0, 0]) == [0] and c.query([101.4, 0, 0]) == [] and c.query([102.6, 0, 0]) == [], 'SCALE then CUT24: the cut is in the root frame')
lo, hi = c.reach(0); check(abs(lo[0] - 101.5) < 1e-9 and abs(hi[0] - (102.5 + 1 / 65536.0)) < 1e-9, 'SCALE then CUT24: reach in root units')
# diagonal: SPLIT y+z a=100 b=101: v = floor((y8 + z8) / 2)
c = M.Code(OFF, bytes([0x13, 100, 101, 1, 0x30, 0x31]))
check(c.query([0, 100, 100]) == [0] and c.query([0, 101, 101]) == [1] and c.query([0, 100, 102]) == [1], 'diagonal y+z = floor((y + z) / 2)')
# diagonal with a minus term: x-y = floor((x - y + 256) / 2)
c = M.Code(OFF, bytes([0x18, 128, 129, 1, 0x30, 0x31]))
check(c.query([10, 10, 0]) == [0] and c.query([12, 10, 0]) == [1] and c.query([10, 12, 0]) == [0], 'diagonal x-y = floor((x - y + 256) / 2): equal -> 128 (left)')
lo, hi = c.reach(0); check(lo == [0.0, 0.0, 0.0] and hi[0] == 255.0, 'diagonal constraints do not narrow the reach box (conservative)')
check(bool(c.terms[0][0].diagonal()), 'diagonal constraints are kept on the box')
# unknown opcode
try:
    M.Code(OFF, bytes([0x0e, 0x30])); check(False, 'unknown opcode must raise')
except M.MoppError:
    check(True, 'unknown opcode raises MoppError')
try:
    M.Code(OFF, bytes([0x10, 1, 2])); check(False, 'a truncated instruction must raise')
except M.MoppError:
    check(True, 'truncated instruction raises MoppError')

# the pinned DD10 HERO plane code (kl_dm07plane_1109.PINS): offset (80.17, -0.52, 6.52, 2382539), 597 x 697 cm plane at x = const
donor = M.Code(bytes.fromhex('5256a0428d4206bf648cd0402c6b114a'), bytes.fromhex('2800ff2700da2900000000ba2e13806c013031'))
check(sorted(donor.terms) == [0, 1] and donor.coverage() == 1.0, 'HERO plane code: two triangles, fully walked')
lo, hi = donor.reach(0)
check(abs((hi[0] - lo[0]) * 100 - 2.0) < 0.05, 'HERO plane: the 24-bit x cut is 2.0 cm wide (two 0.01 margins) = big-endian proven: %.3f cm' % ((hi[0] - lo[0]) * 100))
check(abs(lo[0] - 80.1686) < 1e-3, 'HERO plane: x reach starts at the offset (world box min - 0.01)')
check(abs(hi[1] - lo[1] - 6.02) < 0.1 and abs(hi[2] - lo[2] - 7.04) < 0.1, 'HERO plane: y 6.02 m (0xda + 1 units of 2.75 cm), z 7.04 m (the whole 0..0xff box): %.2f %.2f' % (hi[1] - lo[1], hi[2] - lo[2]))
mid = [lo[0] + 0.01, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2]
check(donor.query(mid) in ([0, 1], [0], [1]), 'HERO plane: a point on the plane reaches a triangle: %s' % donor.query(mid))
check(donor.query([lo[0] + 0.05, mid[1], mid[2]]) == [], 'HERO plane: 5 cm off the plane reaches nothing')


# ---------------- real files
def hvk_files():
    d = os.environ.get('KL_MOPP_HVK')
    if d and os.path.isdir(d):
        return [(os.path.basename(p), open(p, 'rb').read()) for p in sorted(glob.glob(os.path.join(d, '*.HVK')) + glob.glob(os.path.join(d, '*.hvk')))]
    out = []
    base = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps'
    for m, slot in (('DM07', 'F06'), ('DD10', 'F07')):
        zp = os.path.join(base, m, slot + '_Main.zip')
        if os.path.isfile(zp):
            with zipfile.ZipFile(zp) as z:
                n = next(x for x in z.namelist() if x.lower().endswith('_main.hvk'))
                out.append((m + '/' + os.path.basename(n), z.read(n)))
    return out


for name, data in hvk_files():
    h = kl_hvk.Hvk(data)
    st = M.statics(h)
    print('-- %s: %d static placements, %d list codes' % (name, len(st), len(h.lists)))
    # placement codes
    # a FILLER is one placement repeated many times (kl_hvk.remap: the slot of a dropped static keeps the count; the list code still
    # returns it, its own code then rejects every query away from its real place): DM07 has REF 20269 x 1760, the systems blocks are all filler
    from collections import Counter
    cnt = Counter(h.shapes[si].inst[i] for si, i in st)
    filler = {k for k, (si, i) in enumerate(st) if cnt[h.shapes[si].inst[i]] >= 20}
    print('   filler placements: %d of %d' % (len(filler), len(st)))
    cov_bad = 0; centre_n = centre_ok = 0; terms_bad = 0
    for si, i in st:
        s = h.shapes[si]
        c = M.Code(*s.mopp[i])
        if c.coverage() < 1.0: cov_bad += 1
        if s.convex: continue
        tris = M.triangle_boxes(s.inst[i], s)
        # the compiler drops degenerate triangles: terminals are a subset of 0..n-1, most of them present
        if not (all(0 <= t < len(tris) for t in c.terms) and (len(s.sub) > 1 or len(c.terms) >= 0.25 * len(tris))): terms_bad += 1   # degenerate triangles are dropped by the compiler: DM07 two-sub-part shapes keep 16 of 24, DD10 shape 851 12 of 44
        for t, (lo, hi) in enumerate(tris[:12]):
            centre_n += 1
            centre_ok += t in c.query([(lo[k] + hi[k]) / 2 for k in range(3)])
    check(cov_bad == 0, '%s: every placement code walks to 100 %% byte coverage (%d short)' % (name, cov_bad))
    check(terms_bad == 0, '%s: a mesh placement\'s terminals are triangle numbers 0..n-1, a quarter or more present (%d differ)' % (name, terms_bad))
    check(centre_ok >= 0.995 * centre_n, '%s: triangle centres reach their own terminal: %d of %d' % (name, centre_ok, centre_n))
    # list codes
    for b, (off, code) in enumerate(h.lists):
        c = M.Code(off, code)
        n = min(kl_hvk.CHUNK, len(st) - b * kl_hvk.CHUNK)
        real = sorted(c.terms)
        check(c.coverage() == 1.0, '%s list %d: 100 %% coverage' % (name, b))
        check(all(0 <= t < n for t in real), '%s list %d: every terminal is a child index of the block (%d terminals, %d children)' % (name, b, len(real), n))
        # the terminals are the leading children; what follows them is filler (copies of one placement that no terminal returns)
        check(real == list(range(len(real))), '%s list %d: terminals are children 0..%d (the rest of the block = filler)' % (name, b, len(real) - 1))
        if real and real[-1] + 1 < n:
            si, i = st[b * kl_hvk.CHUNK + real[-1] + 1]
            fill_ref = kl_hvk.ref(h.shapes[si].inst[i])
            same = all(kl_hvk.ref(h.shapes[st[k][0]].inst[st[k][1]]) == fill_ref for k in range(b * kl_hvk.CHUNK + real[-1] + 1, b * kl_hvk.CHUNK + n))
            check(same, '%s list %d: the %d unreturned children all carry one REF (%d) = the filler' % (name, b, n - len(real), fill_ref))
        bad_in = 0; checked = 0
        for t in real:
            if b * kl_hvk.CHUNK + t in filler: continue
            checked += 1
            si, i = st[b * kl_hvk.CHUNK + t]
            own = M.placement_box(h.shapes[si].inst[i], h.shapes[si])
            r = c.reach(t)
            slack = 65536.0 / c.off[3] * 1.0        # one 8-bit unit of this list's box in metres
            if not M.inside(own, r, slack): bad_in += 1
        check(bad_in == 0, '%s list %d: every returned non-filler child\'s world box lies inside its reach box (+- 1 unit) (%d of %d outside)' % (name, b, bad_in, checked))
    if name.startswith('DM07'):
        for child, want_z in ((248, (10384, 10843)), (256, (9989, 10395))):
            _, c, (lo, hi) = M.list_reach(h, child)
            check(abs(lo[1] * 100 - 464) <= 2 and abs(hi[1] * 100 - 817) <= 2 and abs(lo[2] * 100 - want_z[0]) <= 2 and abs(hi[2] * 100 - want_z[1]) <= 2,
                  'DM07 panel slot %d reach = y 464..817, z %d..%d (the plane tool\'s effective window): %s' % (child, want_z[0], want_z[1], M.fmt_cm(lo, hi)))

print('kl_mopp_test: %d FAIL' % fails)
sys.exit(1 if fails else 0)
