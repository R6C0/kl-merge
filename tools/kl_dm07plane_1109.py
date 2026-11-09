"""kl_dm07plane_1109.py - DM07 van gate, recipe C "PLANE": the two hidden gate panels' collision slots become two copies of Dog Days' hero-only collision plane (HVK only).

Background: tools/kl_vehroutes_dm07_1108.py opens the escape-van gate by HIDING (gms flag 0x400) the chain-link panels SO0301_USA_Chainlink_Fence_4m_11 (node 1425,
REF 21449, HVK static slot 248, x -4611..-4547, z 10395..10795) and _4m_01 (node 1433, REF 21457, slot 256, z 9993..10393), both y 471..801. PROVEN live (2026-11-09):
0x400 removes PLAYER collision too, so players walk out west into the van pocket; the mud there is y 388..460 (an 11-83 cm geometric hole under the panels as well).
The panels must STAY hidden (the van drives through them visually). Recipe C puts a wall back that has no look at all:
  * donor = DD10's (stock F07) ColiObj_HERO_Plane01: node 11171, REF 31216, entity flags 0x308, HVK shape 1060, type 1 static, 4 vertices / 2 triangles,
    sub (0, 0x108, 2), local plane y = 0, x +-298.7, z +-348.3 (597 x 697 cm), MOPP offset 5256a0428d4206bf648cd0402c6b114a, code 2800ff27...6c013031;
    its own rotation (rows (0,1,0) (-1,0,0) (0,0,1)) already stands the plane in an x = const plane: world y <- -local x (597 tall), world z <- local z (697 wide).
  * TWO copies, at x -4578, y centre 680 (reaches 381..979: from under the mud to above the panels), z centres 10200 (replaces the 4m_01 slot) and 10600 (the 4m_11 slot):
    jointly z 9851..10949 over the gap 9990..10800. Each copy = donor shape + donor MOPP code with the 16-byte offset recomputed for its place
    (the same formula as kl_dm02fix_1108.part_coop_hvk, reproduced on the donor first).

WHY REPLACE THE TWO SLOTS, NOT APPEND (decided from the code): the Havok world builds one list shape per 510 static placements, and the list MOPP code addresses its
children BY POSITION and only returns a child for the child's OLD volume (re/havok.md "Section 2" rules 4 and 5; kl_hvk.remap / kl_hvk_donor). An appended placement
sits in list block 5 (257 of 510 used, so it would be child 257), whose list code never returns it: it would be silently inert. A placement moved elsewhere in
the file is found only where the list code of its slot looks. The panels' own slots (block 0, children 248 and 256, one shape record each, 1 placement each) are looked at
exactly over the gap (their volumes x -4611..-4547, z 9993..10795, y 471..801), so the planes go INTO those slots: static count 2777, static order, shape count, every list
code, header box and tail are unchanged (audit() asserts it). GUESS: a walker whose capsule overlaps y 471..801 finds the child (the list code), and the plane's own MOPP
then tests the whole 380..980 triangle pair, so the mud hole below 471 is closed for anyone who is in the gap at all (standing on the mud, feet at 460, the head is over 471).
EFFECTIVE COVERAGE (not the planes' size): the list code only returns slot 256 / 248 for a query touching that slot's OLD volume - x -4611..-4547, y 471..801,
z 9993..10393 / 10395..10795 - so what blocks is the plane INSIDE those volumes. The planes' overhang (z 9852..9993, 10795..10948, y 381..471, y 801..979) is reached only
through a query that also touches the old volume; the gap ends z 9990..9993 and 10795..10800 lean on the neighbouring real fence panels. The bench must walk
the gap at z 9995 / 10394 / 10790 and get the capsule BELOW y 471 (crawl / jump / mud edge) to prove the mud hole closed: plan() proves geometry, not list-code reach.

REF (the research answer to "fresh REFs with real .gms entities?"): NOT needed here, so no entity is added (an added entity renumbers every SLOT id in .oct / .rmi / .rmc and
the .prp / .gms / .buf, as kl_fa_cover.apply does; that is a 170 MB re-write and the largest risk of the pass). The planes take the REF of an existing, never-hidden collision
entity of DM07: ColiObj_LevelBound_01 (node 1296, REF 21320, flags 0x308, scene dump 2026-11-09), whose static placement is in this same HVK with sub (0, 0x108, 24)
- so a 0x308 entity with 0x108 sub-parts is the shipped DM07 pattern (9 such shapes already). Stock files already place ONE REF many times (DM07: REF 20269 x 1760, REF 20094 x 344;
re/havok.md "The same REF id is used twice 21 / 126 times"), so this is not a new shape of data (but those repeated REFs are generic props, not a 0x308 entity: if the engine keeps a REF -> body map, bodies sharing
REF 21320 may be ignored or overwrite each other; the bench decides, a fresh-entity route is the fallback). GUESS: the entity link of a static placement is by REF only (it carries the
0x400 hide, nothing else is read from it for a type 1 shape), the handle table needs the REF to exist (it does: 21320 < ref_slots 25458), and nothing hides/moves LevelBound_01.
The hidden panels' REFs 21449 / 21457 then have NO static placement: an entity without collision, as most are.

SUB VARIANT: the sub-part collision word is (surface 0, flags, 2 primitives); re/bank_campaign.md:625-629 reads the flags BY NAME ONLY as 0x20 every character, 0x8 heroes only,
0x40 camera, 0x10 sight, 0x2 shots, plain world 0x72. "0x108 = hero-only" is a GUESS. Default --sub 0x108 (the donor as it is); --sub 0x72 gives the planes plain-world flags
(blocks every character and shots; also blocks cops / AI that route through the gate if they are not in a kill state - bench both). For a non-donor value the shape record's own
flags word (the donor has 264 = 0x108 there too) is set to the same number - GUESS: it mirrors the sub flags.

What changes per zip (the .HVK member of BOTH zips, the same new bytes in both: their HVKs are byte-equal, asserted; every other member byte-identical, order kept):
  slot 248 and 256: the whole shape record (verts, indices, 1 placement, sub-part) and their 2 MOPP (offset + code). F06_Main.bots.base.md5 = md5 of the new plain zip.

    python tools/kl_dm07plane_1109.py --dry [--live DIR] [--sub 0x108|0x72] [--donor ZIP]      read-only: pins, plan, coverage, the sizes it would write; writes nothing
    python tools/kl_dm07plane_1109.py stage --out DIR [--live DIR] [--sub 0x72] [--min-free-mb N]   stage the 2 zips + md5 + hard-link install kit (refuses early when DIR's drive is short)
    python tools/kl_dm07plane_1109.py check <zip>                                              both slots of a zip: REF, sub, world box, coverage
    python tools/kl_dm07plane_1109_test.py                                                     off-game self-test (synthetic inputs; the live HVK is read when it is the pinned one)
"""
import os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm07sink_1109 as S

DD = S.DD
LIVE_DIR = S.LIVE_DIR
DONOR_ZIP = DD + r'\KLExpansion\Maps\DD10\F07_Main.zip'
SLOT = S.SLOT
LIVE_MD5 = S.LIVE_MD5
TAG = '.before-dm07plane1109'
md5 = S.md5
hvk_member = S.hvk_member

# the pins; the self-test passes a synthetic set of the same shape
PINS = dict(
    static_n=2777,
    donor_ref=31216,                                 # DD10 ColiObj_HERO_Plane01
    donor_mopp_offset='5256a0428d4206bf648cd0402c6b114a',
    donor_mopp_code='2800ff2700da2900000000ba2e13806c013031',
    host_ref=21320,                                  # DM07 ColiObj_LevelBound_01 (flags 0x308, never hidden); the REF both planes carry
    panels=((21457, 10200.0), (21449, 10600.0)),     # (REF of the hidden panel = whose slot is replaced, z centre of its plane in cm): 4m_01 z 9993..10393, 4m_11 z 10395..10795
    gap=dict(x=(-4611.0, -4547.0), y=(388.0, 801.0), z=(9990.0, 10800.0)),   # what the planes must jointly cover (mud bottom .. panel top)
)
PLANE_X = -4578.0       # cm, world: inside the fence line (panel x -4611..-4547)
PLANE_Y = 680.0         # cm, centre: the donor is 597 tall -> 381.3..978.7
SUB_DEFAULT = 0x108
PANEL_SUB = (0, 0x66, 12)


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def statics(h):
    """[(shape index, placement index)] in static order"""
    import kl_hvk
    return [(si, i) for si, s in enumerate(h.shapes) if s.type == kl_hvk.STATIC for i in range(len(s.inst))]


def world_box(inst, shape):
    """world bounding box in cm of a placement (pos * 100 + R * v), from the shape's vertices"""
    f = struct.unpack_from('<12f', inst)
    p, R = f[:3], [f[3:6], f[6:9], f[9:12]]
    lo, hi = [1e30] * 3, [-1e30] * 3
    for j in range(len(shape.verts) // shape.vstride):
        v = struct.unpack_from('<3f', shape.verts, j * shape.vstride)
        for i in range(3):
            w = (p[i] + sum(R[i][t] * v[t] for t in range(3))) * 100.0
            lo[i], hi[i] = min(lo[i], w), max(hi[i], w)
    return lo, hi


def find_donor(dh, pins=PINS):
    """The donor shape (a Shape of the donor HVK): REF placed once, alone in its record, 4 vertices / 2 triangles, the pinned MOPP; offset formula reproduced."""
    import kl_hvk
    from kl_dm02fix_1108 import mopp_offset
    hit = [(si, i) for si, i in statics(dh) if kl_hvk.ref(dh.shapes[si].inst[i]) == pins['donor_ref']]
    if len(hit) != 1:
        raise ValueError('donor REF %d placed %d times (want 1)' % (pins['donor_ref'], len(hit)))
    ds = dh.shapes[hit[0][0]]
    if len(ds.inst) != 1 or ds.convex or len(ds.verts) // ds.vstride != 4 or len(ds.idx) // 2 != 6 or len(ds.sub) != 1 or ds.sub[0][2] != 2:
        raise ValueError('donor is not the single 4-vertex / 2-triangle plane')
    off, code = ds.mopp[0]
    if off.hex() != pins['donor_mopp_offset'] or code.hex() != pins['donor_mopp_code']:
        raise ValueError('donor MOPP is not the pinned one (offset %s, code %s)' % (off.hex(), code.hex()[:40]))
    o1, o2 = struct.unpack('<3f', mopp_offset(ds.inst[0], ds)), struct.unpack('<3f', off[:12])
    if any(abs(a - b) > 1e-5 for a, b in zip(o1, o2)):
        raise ValueError('mopp offset formula does not reproduce the donor offset %s vs %s' % (o1, o2))
    f = struct.unpack_from('<12f', ds.inst[0])
    # the donor's rotation must stand the plane in an x = const plane with the long side along z (GUESS-free: measured from its own box)
    lo, hi = world_box(ds.inst[0], ds)
    if hi[0] - lo[0] > 0.01 or not 595 < hi[1] - lo[1] < 600 or not 695 < hi[2] - lo[2] < 700:
        raise ValueError('donor world box is not 0 x 597 x 697: %s %s' % (lo, hi))
    return ds


def plan(raw, donor_raw, sub=SUB_DEFAULT, pins=PINS):
    """-> (new HVK bytes, report). Asserts: both byte-exact round trips; the two panel slots are single-placement records of one list block; the host REF is placed
    with collision in this HVK; the planes jointly cover the gap; audit() of the result against the original."""
    import kl_hvk
    from kl_dm02fix_1108 import mopp_offset
    h, dh = kl_hvk.Hvk(raw), kl_hvk.Hvk(donor_raw)
    if h.serialize() != raw:
        raise ValueError('the DM07 HVK does not round-trip byte-exact (stop: nothing was written)')
    if dh.serialize() != donor_raw:
        raise ValueError('the donor HVK does not round-trip byte-exact')
    if h.static_count() != pins['static_n']:
        raise ValueError('static count %d, want %d' % (h.static_count(), pins['static_n']))
    ds = find_donor(dh, pins)
    st = statics(h)
    refs = [kl_hvk.ref(h.shapes[si].inst[i]) for si, i in st]
    if pins['host_ref'] not in refs:
        raise ValueError('host REF %d has no static placement in this HVK (is the pinned file the live DM07?)' % pins['host_ref'])
    slots = []
    for ref, zc in pins['panels']:
        if refs.count(ref) != 1:
            raise ValueError('panel REF %d is placed %d times (already replaced by another pass?)' % (ref, refs.count(ref)))
        n = refs.index(ref)
        si, i = st[n]
        s = h.shapes[si]
        if len(s.inst) != 1 or s.type != kl_hvk.STATIC or s.sub != [PANEL_SUB]:
            raise ValueError('panel REF %d (static slot %d): not a single-placement record with sub %s (has %d placements, sub %s)' % (ref, n, PANEL_SUB, len(s.inst), s.sub))
        slots.append((n, si, ref, zc))
    if len({n // kl_hvk.CHUNK for n, *_ in slots}) != 1:
        raise ValueError('the two panel slots are in different list blocks')
    block = slots[0][0] // kl_hvk.CHUNK
    d0 = struct.unpack_from('<12f', ds.inst[0])
    rep, cover = [], []
    for n, si, ref, zc in slots:
        old = h.shapes[si]
        olo, ohi = world_box(old.inst[0], old)
        # placement: the donor's own rotation; the donor's vertex box is centred on its local origin (asserted below), so position = the wanted centre
        pos = [PLANE_X * 0.01, PLANE_Y * 0.01, zc * 0.01]
        inst = struct.pack('<12f', *pos, *d0[3:12]) + struct.pack('<II', pins['host_ref'], struct.unpack_from('<I', ds.inst[0], 0x34)[0])
        noff = mopp_offset(inst, ds)
        sh = ds.clone([inst], [(noff + ds.mopp[0][0][12:], ds.mopp[0][1])])
        if sub != ds.sub[0][1]:
            sh.sub = [(ds.sub[0][0], sub, ds.sub[0][2])]
            sh.flags = sub                                  # GUESS: the record's flags word mirrors the sub flags (the donor has 264 = 0x108 in both)
        lo, hi = world_box(inst, sh)
        cover.append((lo, hi))
        h.shapes[si] = sh
        rep.append(dict(slot=n, ref_old=ref, ref_new=pins['host_ref'], old_box=(olo, ohi), box=(lo, hi), sub=sh.sub[0], mopp_off=struct.unpack('<3f', noff)))
    g = pins['gap']
    cover.sort(key=lambda b: b[0][2])
    if not all(c[0][0] <= g['x'][1] and c[1][0] >= g['x'][0] for c in cover):
        raise ValueError('a plane is not in the fence line in x: %s' % cover)
    if min(c[0][1] for c in cover) > g['y'][0] or max(c[1][1] for c in cover) < g['y'][1]:
        raise ValueError('the planes do not reach y %s: %s' % (g['y'], cover))
    if cover[0][0][2] > g['z'][0] or cover[-1][1][2] < g['z'][1] or cover[0][1][2] < cover[1][0][2]:
        raise ValueError('the planes do not jointly cover z %s: %s' % (g['z'], cover))
    # the list block's MOPP offset (block bb min - 0.01) must not lie above the new plane's low corner, and the header box must hold them
    lo_y = min(c[0][1] for c in cover) * 0.01
    list_y = struct.unpack_from('<f', h.lists[block][0], 4)[0]
    if lo_y < list_y:
        raise ValueError('list block %d MOPP offset y %.3f m is above the new plane bottom %.3f m' % (block, list_y, lo_y))
    bx = h.box
    for c in cover:
        if any(c[0][a] * 0.01 < bx[a] or c[1][a] * 0.01 > bx[3 + a] for a in range(3)):
            raise ValueError('a plane leaves the HVK header box %s' % (bx,))
    data = h.serialize()
    audit(raw, data, [n for n, *_ in slots], pins)
    return data, rep


def audit(raw, data, slots, pins=PINS):
    """Nothing but the shape records of the two slots differs: static count, shape count, static order (but for those 2 REFs), lists, box, tail, every other
    shape field and placement/MOPP identical; the two new records are exactly one placement with the host REF."""
    import kl_hvk
    a, b = kl_hvk.Hvk(raw), kl_hvk.Hvk(data)
    if kl_hvk.Hvk(data).serialize() != data:
        raise ValueError('result does not round-trip')
    if a.static_count() != b.static_count() or a.box != b.box or a.tail != b.tail or a.lists != b.lists or len(a.shapes) != len(b.shapes):
        raise ValueError('static count / box / tail / list MOPPs / shape count changed')
    sa, sb = statics(a), statics(b)
    if sa != sb:
        raise ValueError('static order (record, placement) changed')
    ra = [kl_hvk.ref(a.shapes[si].inst[i]) for si, i in sa]
    rb = [kl_hvk.ref(b.shapes[si].inst[i]) for si, i in sb]
    diff = [n for n in range(len(ra)) if ra[n] != rb[n]]
    if diff != sorted(slots):
        raise ValueError('REF order differs at %s, want %s' % (diff, sorted(slots)))
    if any(rb[n] != pins['host_ref'] for n in slots):
        raise ValueError('a plane does not carry the host REF')
    nrec = 0
    for x, y in zip(a.shapes, b.shapes):
        if vars(x) != vars(y):
            nrec += 1
    if nrec != len(slots):
        raise ValueError('%d shape records differ, want %d' % (nrec, len(slots)))
    return nrec


def repack(src, dst, name, new_raw):
    return S.repack(src, dst, name, new_raw=new_raw)


def need_bytes(live_dir):
    """what a stage writes: both zips (full copies) + 8 MB of slack"""
    return sum(os.path.getsize(os.path.join(live_dir, n)) for n in ('F06_Main.zip', 'F06_Main.bots.zip')) + (8 << 20)


def need_free(out, live_dir, min_free_mb=64):
    """refuse early, before anything is read or written; -> None or the refusal text"""
    probe = probe_dir(out)
    free = shutil.disk_usage(probe or '.').free
    need = need_bytes(live_dir) + (min_free_mb << 20)
    if free < need:
        return 'REFUSED: %s has %d MB free, a stage needs %d MB (2 zips + %d MB slack); stage on another drive with --out' % (probe, free >> 20, need >> 20, min_free_mb + 8)
    return None


def probe_dir(p):
    """ the nearest existing directory at or above p """
    while p and not os.path.exists(p):
        nxt = os.path.dirname(p)
        if nxt == p:
            break
        p = nxt
    return p or '.'


def game_drive_note(out, live_dir):
    """ -> (cross_drive, text). install.py hard-links only when the stage sits on the game folder's volume; from another drive (D:) it COPIES the new zips into the game
    folder (about the zips' size free on the game drive; install.py's own guard asks for staged + live sizes + its --min-free-mb, default 1024). """
    live_dir = probe_dir(live_dir)
    cross = os.stat(probe_dir(out)).st_dev != os.stat(live_dir).st_dev
    if not cross:
        return False, 'stage on the game drive: install hard-links, needs no extra game-drive space'
    zips = need_bytes(live_dir) - (8 << 20)
    free = shutil.disk_usage(live_dir).free
    return True, ('stage on ANOTHER drive than the game: install COPIES the zips, so the game drive needs about %d MB free (it has %d MB; install.py itself asks for %d MB + '
                  '--min-free-mb, pass --min-free-mb 300 to it)' % (zips >> 20, free >> 20, 2 * zips >> 20))


def pins_ok(live_dir):
    for n, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (n, h))


def read_hvks(live_dir):
    raws = {}
    for n in ('F06_Main.zip', 'F06_Main.bots.zip'):
        with zipfile.ZipFile(os.path.join(live_dir, n)) as z:
            raws[n] = z.read(hvk_member(z))
    return raws


def read_donor(donor_zip):
    with zipfile.ZipFile(donor_zip) as z:
        return z.read(hvk_member(z))


def describe(rep, log):
    for r in rep:
        (olo, ohi), (lo, hi) = r['old_box'], r['box']
        log('    slot %d (REF %d -> %d): old box x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f cm; plane x %.0f y %.0f..%.0f z %.0f..%.0f; sub %s; mopp offset %s'
            % (r['slot'], r['ref_old'], r['ref_new'], olo[0], ohi[0], olo[1], ohi[1], olo[2], ohi[2], lo[0], lo[1], hi[1], lo[2], hi[2], r['sub'], tuple(round(v, 4) for v in r['mopp_off'])))


def dry(live_dir=LIVE_DIR, donor_zip=DONOR_ZIP, sub=SUB_DEFAULT, log=print):
    """read-only: pins, the plan on the live HVK(s), the sizes a stage would write"""
    pins_ok(live_dir)
    raws, dr = read_hvks(live_dir), read_donor(donor_zip)
    equal = raws['F06_Main.zip'] == raws['F06_Main.bots.zip']
    log('  pinned live md5s ok; plain and bots HVK equal: %s (%d bytes)' % (equal, len(raws['F06_Main.zip'])))
    for n in (('F06_Main.zip',) if equal else raws):
        data, rep = plan(raws[n], dr, sub)
        log('  %s: sub 0x%x, HVK %d -> %d bytes, 2 shape records replaced, static count %d unchanged' % (n, sub, len(raws[n]), len(data), PINS['static_n']))
        describe(rep, log)
    log('  a stage would write: %d MB (2 zips) + kit on the --out drive' % (need_bytes(live_dir) >> 20))
    log('  game drive has %d MB free; --out on the game drive: install hard-links (0 MB); --out elsewhere: install copies, ~%d MB free needed on the game drive'
        % (shutil.disk_usage(probe_dir(live_dir)).free >> 20, (need_bytes(live_dir) >> 20) - 8))
    return 0


def stage(out, live_dir=LIVE_DIR, donor_zip=DONOR_ZIP, sub=SUB_DEFAULT, min_free_mb=64, log=print):
    msg = need_free(out, live_dir, min_free_mb)
    if msg:
        raise ValueError(msg)
    pins_ok(live_dir)
    cross, note = game_drive_note(out, live_dir)
    log('  ' + ('WARNING: ' if cross else '') + note)
    os.makedirs(out, exist_ok=True)
    raws, dr = read_hvks(live_dir), read_donor(donor_zip)
    equal = raws['F06_Main.zip'] == raws['F06_Main.bots.zip']
    log('  plain and bots HVK equal: %s' % equal)
    news, plain_new = {}, None
    for n in ('F06_Main.zip', 'F06_Main.bots.zip'):
        news[n] = next(iter(news.values())) if equal and news else plan(raws[n], dr, sub)
        new, rep = news[n]
        src, dst = os.path.join(live_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(src) as z:
            name = hvk_member(z)
        repack(src, dst, name, new)
        with zipfile.ZipFile(dst) as a:
            if a.read(name) != new:
                raise ValueError('re-read HVK differs from the intended bytes')
        log('  %s: 2 planes in slots %s; every other member byte-identical' % (n, [r['slot'] for r in rep]))
        describe(rep, log)
        if n == 'F06_Main.zip':
            plain_new = md5(dst)
    with open(os.path.join(out, 'F06_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(plain_new + '\n')
    files = []
    for n in ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5'):
        files.append((n, LIVE_MD5[n], md5(os.path.join(out, n))))
        log('  %-24s %s -> %s' % files[-1])
    write_kit(out, files)
    return files


def kit_text(files, live_zip_md5=None):
    t = S.INSTALL_TEMPLATE.replace('.before-dm07sink1109', TAG).replace('DM07 SINK 1109 (tools/kl_dm07sink_1109.py)', 'DM07 PLANE 1109 (tools/kl_dm07plane_1109.py)')
    t = t.replace('Static fence-line slabs sunk to the mud (collision only).', 'Gate panel slots now hold two hero-only collision planes (HVK only).')
    t = t.replace('@LIVEZIP@', repr(live_zip_md5 or LIVE_MD5['F06_Main.zip'])).replace('@FILES@', '\n'.join('    (%r, %r, %r),' % f for f in files))
    assert 'sink' not in t.lower(), 'template still mentions sink'
    return t


def write_kit(out, files, live_zip_md5=None):
    nl, cr = chr(10), chr(13)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(kit_text(files, live_zip_md5))
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM07 plane 1109.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


def is_plane(s):
    """ a single-placement 4-vertex record with 2 sub primitives whose world box is flat in x (a donor copy), not the 24-primitive LevelBound box """
    if len(s.inst) != 1 or len(s.verts) // s.vstride != 4 or len(s.sub) != 1 or s.sub[0][2] != 2:
        return False
    lo, hi = world_box(s.inst[0], s)
    return hi[0] - lo[0] < 0.01


def check(zp, pins=PINS, out=print):
    """Both panel slots of a zip: REF, sub, world box. -> True when both hold a plane of the host REF."""
    import kl_hvk
    with zipfile.ZipFile(zp) as z:
        raw = z.read(hvk_member(z))
    h = kl_hvk.Hvk(raw)
    if h.serialize() != raw:
        raise ValueError('HVK does not round-trip byte-exact')
    st = statics(h)
    ok = h.static_count() == pins['static_n']
    out('static count %d (want %d)' % (h.static_count(), pins['static_n']))
    slots = []
    for n, (si, i) in enumerate(st):
        s = h.shapes[si]
        r = kl_hvk.ref(s.inst[i])
        if r in [p[0] for p in pins['panels']]:
            slots.append((n, 'STOCK PANEL', r, s))
    if not slots:
        slots = [(n, 'PLANE', pins['host_ref'], h.shapes[st[n][0]]) for n in range(len(st)) if kl_hvk.ref(h.shapes[st[n][0]].inst[st[n][1]]) == pins['host_ref'] and is_plane(h.shapes[st[n][0]])]
    for n, what, r, s in slots:
        lo, hi = world_box(s.inst[0], s)
        out('%s slot %d REF %d sub %s: x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f cm' % (what, n, r, s.sub[0], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    ok = ok and len(slots) == 2 and all(w == 'PLANE' for _n, w, _r, _s in slots)
    out('RESULT: %s' % ('both gate slots hold a hero-plane copy' if ok else 'NOT the plane zip (stock zip or other)'))
    return ok


def main(a):
    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a else default
    sub = int(opt('--sub', hex(SUB_DEFAULT)), 0)
    if sub not in (0x108, 0x72):
        raise SystemExit('--sub is 0x108 (the donor) or 0x72')
    live, donor = opt('--live', LIVE_DIR), opt('--donor', DONOR_ZIP)
    if '--dry' in a:
        return dry(live, donor, sub)
    if a[:1] == ['stage']:
        if not opt('--out'):
            raise SystemExit('stage needs --out <dir>')
        try:
            stage(opt('--out'), live, donor, sub, int(opt('--min-free-mb', 64)))
        except ValueError as e:
            if str(e).startswith('REFUSED'):
                print(e); return 1
            raise
        return 0
    if a[:1] == ['check'] and len(a) == 2:
        return 0 if check(a[1]) else 1
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
