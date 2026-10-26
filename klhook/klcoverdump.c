/*
 * klcoverdump.c - [CoverDump] READ-ONLY dump of the engine's cover list (CFFCoverList) to KLHook.log, once per level load. 2026-10-26.
 * Included by klhook.c right after klmfprobe.c (uses klh_rd / klh_rd32 / klh_rdstr / klog / klh_ini / klcam_player / kle_node). NOTHING HERE
 * HAS RUN IN THE GAME. It patches no code and writes no memory; it is ticked from the same game-thread entry as klcensus.c (kcvd_tick(game_thread)).
 *
 * WHY: which of our KL_CoverSix coverbox entities (and which stock ones) end up as cover POINTS in the list the player's cover test reads
 * (CFFCoverList is built ONCE at the load, 0x6d6a80 -> 0x603830, from the coverbox-named ZSTDOBJ boxes). tools/kl_coverdump_parse.py
 * compares the dumped points with the boxes of a map zip.
 *
 * LAYOUT (from the COVER8 script and the task; every offset below except the list's vtable is a GUESS until the first dump is read):
 *   L = [[0xdd265c]+0x15a0]  CFFCoverList, vtable 0xbbece4 (verified at run time and logged; a mismatch is logged and the dump goes on,
 *                            and if [gd+0x15a0] itself carries the vtable the list is taken as embedded: L = gd+0x15a0)
 *   records: base [L+0x70], count [L+0x74], stride 0xa8        points: vector begin [L+0x44], end [L+0x48], stride 0x7c, float3 at +0x28
 *   (+0x34 float3 = normal / direction GUESS)                  dropped-points counter dword at 0x156b27c
 *   record -> entity map at [L+0x98]: GUESS, only its raw dwords are logged (header at L+0x80..0xb0 and 24 dwords behind [L+0x98]).
 * WHEN: once per level load (key = the game-data pointer; also re-armed when the session state [[0x168e598]+0x70] goes back to 0x16), when
 * the session state is 0x19 (in play) and the record count is nonzero and the count / begin / end are unchanged over ~2 s of ticks.
 * HOW MUCH: lines are queued by the dump state machine, 100 lines a tick (klog is one WriteFile a line), at most MaxRecords record lines and
 * MaxPoints point lines. Point positions are cached (up to KCVD_CACHE) for the 'near' lines: every 5 s for 60 s after the dump, the 3 points
 * nearest the local player (3D distance).
 * LINES (prefix 'coverdump:'): begin / list / dropped / map / rec / pt / end / near. The parser reads from the last 'coverdump: begin'.
 * ini: [CoverDump] Enable=1 in the TEST build / 0 in SHIP (recommended on for test runs, off for players)  MaxPoints=6000  MaxRecords=2000
 *       FullRecords=1 (TEST) / 0 (SHIP) (recommended on for test runs, off for players): stage 5, 'full' lines (below)
 *       Finder=1 (TEST) / 0 (SHIP) (recommended on for test runs, off for players): read-only emulation of the finder 0x797480, 'finder' lines
 *       FinderMax=400 (cap of finder lines per load)
 *
 * 2026-10-26 (workflow w4zrc2bfc follow-up, why do our K6 boxes give no cover): FullRecords + Finder.
 * FINDER FACTS (disassembly of 0x797480, thiscall ecx=L, ret 0x14, args pos*, out*, max 0x40, radius float [0xb243f4]=400): NOT detoured, it lies in the
 * hashed range 0x791000..0x798000 (klranges.h). Instead this file re-does its read-only part from the same data:
 *   cell key = 0x6db910(pos) (pure, stdcall 1 arg, pos* x at +0 and z at +8): ((floor(x*0.01+0.5)+1024)&0xfff)<<12 | ((floor(z*0.01+0.5)+1024)&0xfff)
 *   n = 2*ceil(radius*0.01) (8), start = key - (n/2)*0x1001; cells start + i + j*0x1000 for i,j in 0..n-1
 *   table at L+0x78: buckets begin [L+0x7c] end [L+0x80] (pointers to nodes), size [L+0x88]; bucket = ((key>>12)+(key&0xfff)) % nbuckets;
 *   node {+0 next, +4 key, +8 head of a list}; list element {+0 record index, +4 next}; record = [L+0x70] + index*0xa8
 *   kept if |pos.y - (rec[+0x60] - rec[+0x54])| < 50.0 (the double at 0xb71b60)  (GUESS what +0x54 / +0x60 mean; the arithmetic is read from the code)
 *   second source: vector [L+0x8c]..[L+0x90] of record pointers, taken when byte [rec+0xa6] != 0 (plane test 0x548af0/0x639bd0 NOT emulated)
 * GUESS: the position the real caller 0x849700 passes is the player's scene node place (kle_node(P+4)); the emulation says what the finder WOULD return there.
 * LINES: 'full rec' (header with cached place, hash cell count and first/last cell of that record, +0x54 / +0x60), 'full dw' (the 0xa8 bytes as 3 lines of 14 dwords),
 *   'full side' (each non-null side pointer at record +0x90..+0x9c, dwords +0..+0x40), 'full hash' / 'full dyn' (table summary), 'finder' (summary + peeks of the
 *   player's [+0x2d60] [+0x2d64] [+0x2d74] [+0x2954] [+0xb50] [+0xb54] and movement id [[P+0x6b4]+0x44]) and 'finder rec' (nearest records within 400 on the XZ plane:
 *   in the scanned cells yes/no, y test pass/fail), logged on a change or every 5 s while a record is within 400.
 */
#ifndef KLCOVERDUMP_C
#define KLCOVERDUMP_C

#define KCVD_VT      0x00bbece4u
#define KCVD_SM      0x0168e598u
#define KCVD_DROPPED 0x0156b27cu
#define KCVD_CACHE   20000
#define KCVD_PER_TICK 100
#define KCVD_RMAX    4096                              /* records with cached name / place / hash stats */
#define KCVD_FULL_TICK 12                              /* records per tick in the full stage */

static struct {
    int on, full, finder, stage, armed;                              /* stage: 0 wait for a stable list, 1 records, 2 points, 3 near, 4 done (finder goes on), 5 full records */
    DWORD maxp, maxr, gd, st, L, rb, rn, pb, pe, npt, i, stab_at, t_dump, t_near, near_n;
    DWORD last_rb, last_rn, last_pb, last_pe, last_tick;
    DWORD fmax, flines, t_find, t_flog, f_sig;
    int bad;
} kcvd;
static float kcvd_pos[KCVD_CACHE][3];
static float kcvd_rpos[KCVD_RMAX][3];                  /* record place via its entity's scene node */
static BYTE kcvd_rok[KCVD_RMAX];
static char kcvd_rname[KCVD_RMAX][48];
static DWORD kcvd_rcell[KCVD_RMAX], kcvd_rk0[KCVD_RMAX], kcvd_rk1[KCVD_RMAX];   /* hash cells that list the record; first / last key seen */
static DWORD kcvd_hnodes, kcvd_hrefs, kcvd_hnb;

static int kcvd_ptr_ok(DWORD v) { return v >= 0x10000u && v < 0x7ff00000u; }

/* entity name via [[ptr+4]+0x6c] like klmfprobe.c; 0 = does not look like an entity */
static int kcvd_name(DWORD ptr, char *nm, int cap)
{
    DWORD node, s; int n, i;
    nm[0] = 0;
    if (!kcvd_ptr_ok(ptr) || !(node = klh_rd32(ptr + 4)) || !kcvd_ptr_ok(node) || !(s = klh_rd32(node + 0x6c)) || !kcvd_ptr_ok(s)) return 0;
    n = klh_rdstr(s, nm, cap);
    if (n < 3) { nm[0] = 0; return 0; }
    for (i = 0; i < n; i++) if ((BYTE)nm[i] < 0x20 || (BYTE)nm[i] > 0x7e) { nm[0] = 0; return 0; }
    return n;
}

static int kcvd_state(DWORD *gd, DWORD *st)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(KCVD_SM));
    *gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA));
    *st = sm ? klh_rd32(sm + 0x70) : 0;
    return *gd != 0;
}

/* the list pointer and its fields; 0 = not readable. Sets kcvd.L / rb / rn / pb / pe */
static int kcvd_read_list(DWORD gd, DWORD *L, DWORD *rb, DWORD *rn, DWORD *pb, DWORD *pe)
{
    DWORD l = klh_rd32(gd + 0x15a0), vt = (DWORD)(DWORD_PTR)KLH_VA(KCVD_VT);
    if (!kcvd_ptr_ok(l)) return 0;
    if (klh_rd32(l) != vt && klh_rd32(gd + 0x15a0) == vt) l = gd + 0x15a0;     /* embedded instead of a pointer (GUESS, only if the vtable shows it) */
    *L = l; *rb = klh_rd32(l + 0x70); *rn = klh_rd32(l + 0x74); *pb = klh_rd32(l + 0x44); *pe = klh_rd32(l + 0x48);
    return 1;
}

static void kcvd_hexdw(char *out, int cap, const DWORD *d, int n)
{
    int i, k = 0;
    out[0] = 0;
    for (i = 0; i < n && k < cap - 10; i++) k += _snprintf(out + k, cap - k - 1, "%s%08lx", i ? " " : "", (unsigned long)d[i]);
    out[cap - 1] = 0;
}

static void kcvd_begin(void)
{
    char h[400]; DWORD dw[12], i, vt = klh_rd32(kcvd.L), mp = klh_rd32(kcvd.L + 0x98);
    klog("coverdump: begin gd=%08lx state=%lx L=%08lx vtable=%08lx expected=%08lx %s", (unsigned long)kcvd.gd, (unsigned long)kcvd.st, (unsigned long)kcvd.L,
         (unsigned long)vt, (unsigned long)(DWORD_PTR)KLH_VA(KCVD_VT), vt == (DWORD)(DWORD_PTR)KLH_VA(KCVD_VT) ? "VTABLE OK" : "VTABLE MISMATCH (offsets are guesses!)");
    klog("coverdump: list records base=%08lx count=%lu stride=0xa8 | points begin=%08lx end=%08lx stride=0x7c count=%lu%s | MaxRecords=%lu MaxPoints=%lu",
         (unsigned long)kcvd.rb, (unsigned long)kcvd.rn, (unsigned long)kcvd.pb, (unsigned long)kcvd.pe, (unsigned long)kcvd.npt,
         (kcvd.pe - kcvd.pb) % 0x7c ? " (NOT a multiple of 0x7c!)" : "", (unsigned long)kcvd.maxr, (unsigned long)kcvd.maxp);
    klog("coverdump: dropped counter [0x156b27c]=%lu", (unsigned long)klh_rd32((DWORD_PTR)KLH_VA(KCVD_DROPPED)));
    memset(dw, 0, sizeof dw);
    for (i = 0; i < 12; i++) dw[i] = klh_rd32(kcvd.L + 0x70 + i * 4);
    kcvd_hexdw(h, sizeof h, dw, 12);
    klog("coverdump: list dwords +0x70..+0x9c: %s", h);
    memset(dw, 0, sizeof dw);
    for (i = 0; i < 12; i++) dw[i] = klh_rd32(kcvd.L + 0xa0 + i * 4);
    kcvd_hexdw(h, sizeof h, dw, 12);
    klog("coverdump: list dwords +0xa0..+0xcc: %s", h);
    if (kcvd_ptr_ok(mp)) {                                    /* GUESS: [L+0x98] = record -> entity map */
        DWORD m[24];
        memset(m, 0, sizeof m);
        for (i = 0; i < 24; i++) m[i] = klh_rd32(mp + i * 4);
        kcvd_hexdw(h, sizeof h, m, 12);
        klog("coverdump: map [L+0x98]=%08lx raw dwords 0..11: %s", (unsigned long)mp, h);
        kcvd_hexdw(h, sizeof h, m + 12, 12);
        klog("coverdump: map [L+0x98]=%08lx raw dwords 12..23: %s", (unsigned long)mp, h);
    } else
        klog("coverdump: map [L+0x98]=%08lx is not a pointer", (unsigned long)mp);
}

static void kcvd_rec_line(DWORD i)
{
    DWORD d[0xa8 / 4], k; char hx[400], ents[600], nm[80]; int en = 0, got;
    memset(d, 0, sizeof d);
    got = klh_rd(kcvd.rb + i * 0xa8, d, 0xa8);
    ents[0] = 0;
    if (got) for (k = 0; k < 0xa8 / 4; k++) {
        if (kcvd_name(d[k], nm, sizeof nm) && en < 6) {
            int l = (int)strlen(ents);
            _snprintf(ents + l, sizeof ents - l - 1, " ent@+0x%lx=%08lx'%s'", (unsigned long)(k * 4), (unsigned long)d[k], nm); ents[sizeof ents - 1] = 0;
            en++;
        }
    }
    if (got && i < KCVD_RMAX) {                           /* GUESS: dword +0 of the record = the coverbox entity (scene node at entity+4) */
        DWORD node = kcvd_ptr_ok(d[0]) ? klh_rd32(d[0] + 4) : 0; float q[3] = { 0, 0, 0 };
        kcvd_rok[i] = (BYTE)(kcvd_ptr_ok(node) && kle_node(node, q, 0));
        memcpy(kcvd_rpos[i], q, sizeof q);
        kcvd_name(d[0], kcvd_rname[i], sizeof kcvd_rname[i]);
    }
    kcvd_hexdw(hx, sizeof hx, d, 12);
    klog("coverdump: rec %lu%s %s |%s", (unsigned long)i, got ? "" : " UNREADABLE", hx, en ? ents : " no entity pointer found");
}

static void kcvd_pt_line(DWORD i)
{
    DWORD d[0x7c / 4]; float p[3], n[3]; char hx[300]; int got;
    memset(d, 0, sizeof d);
    got = klh_rd(kcvd.pb + i * 0x7c, d, 0x7c);
    memcpy(p, &d[0x28 / 4], 12); memcpy(n, &d[0x34 / 4], 12);
    if (i < KCVD_CACHE) { kcvd_pos[i][0] = p[0]; kcvd_pos[i][1] = p[1]; kcvd_pos[i][2] = p[2]; }
    if (i < kcvd.maxp) {
        kcvd_hexdw(hx, sizeof hx, d, 10);
        klog("coverdump: pt %lu%s pos %.1f %.1f %.1f | +34 %.3f %.3f %.3f | %s", (unsigned long)i, got ? "" : " UNREADABLE", p[0], p[1], p[2], n[0], n[1], n[2], hx);
    }
}

/* the 3 cached points nearest the local player */
static void kcvd_near(void)
{
    DWORD P, gd = 0, node, i, lim = kcvd.npt < KCVD_CACHE ? kcvd.npt : KCVD_CACHE; float me[3] = { 0, 0, 0 }; int k, j;
    DWORD bi[3] = { 0xffffffffu, 0xffffffffu, 0xffffffffu }; float bd[3] = { 1e30f, 1e30f, 1e30f };
    if (!(P = klcam_player(&gd)) || !(node = klh_rd32(P + 4)) || !kle_node(node, me, 0)) { klog("coverdump: near - no local player place"); return; }
    for (i = 0; i < lim; i++) {
        float dx = kcvd_pos[i][0] - me[0], dy = kcvd_pos[i][1] - me[1], dz = kcvd_pos[i][2] - me[2], d = dx * dx + dy * dy + dz * dz;
        for (k = 0; k < 3; k++) if (d < bd[k]) {
            for (j = 2; j > k; j--) { bd[j] = bd[j - 1]; bi[j] = bi[j - 1]; }
            bd[k] = d; bi[k] = i; break;
        }
    }
    klog("coverdump: near t+%lus me (%.1f %.1f %.1f) of %lu points: #%lu d=%.1f (%.1f %.1f %.1f) | #%lu d=%.1f | #%lu d=%.1f",
         (unsigned long)((GetTickCount() - kcvd.t_dump) / 1000), me[0], me[1], me[2], (unsigned long)lim,
         (unsigned long)bi[0], bi[0] == 0xffffffffu ? -1.0 : sqrt((double)bd[0]), bi[0] == 0xffffffffu ? 0.f : kcvd_pos[bi[0]][0],
         bi[0] == 0xffffffffu ? 0.f : kcvd_pos[bi[0]][1], bi[0] == 0xffffffffu ? 0.f : kcvd_pos[bi[0]][2],
         (unsigned long)bi[1], bi[1] == 0xffffffffu ? -1.0 : sqrt((double)bd[1]), (unsigned long)bi[2], bi[2] == 0xffffffffu ? -1.0 : sqrt((double)bd[2]));
}

/* ---- 2026-10-26: FullRecords / Finder (read-only) ---------------------------------------------------------------------------------------------------- */

/* the engine's own cell key function 0x6db910 (pure, stdcall, one argument: float[3] with x at +0 and z at +8) */
static DWORD kcvd_cellkey(const float *p)
{
    typedef DWORD (__stdcall *key_fn)(const float *);
    return ((key_fn)(DWORD_PTR)KLH_VA(0x006db910u))(p);
}
/* my re-computation of the same (float stores like the code); only used to cross-check the engine's answer */
static DWORD kcvd_mykey(const float *p)
{
    float a = (float)((double)p[0] * 0.009999999776482582), b = (float)((double)p[2] * 0.009999999776482582);
    int ia, ib;
    a = (float)((double)a + 0.5); b = (float)((double)b + 0.5);
    a = (float)(floor((double)a) + 1024.0); b = (float)(floor((double)b) + 1024.0);
    ia = (int)a; ib = (int)b;
    return ((DWORD)(ia & 0xfff) << 12) | (DWORD)(ib & 0xfff);
}

/* the record indices listed in one hash cell; returns 1 if the cell exists (count in *n, at most cap indices stored) */
static int kcvd_cell(DWORD L, DWORD key, DWORD *out, int cap, int *n)
{
    DWORD b0 = klh_rd32(L + 0x7c), b1 = klh_rd32(L + 0x80), nb, node, head; int steps = 0, k;
    *n = 0;
    if (!kcvd_ptr_ok(b0) || b1 < b0) return 0;
    nb = (b1 - b0) / 4;
    if (!nb || nb > 0x1000000u) return 0;
    node = klh_rd32(b0 + 4 * (((key >> 12) + (key & 0xfff)) % nb));
    while (node && steps++ < 4096) {
        if (klh_rd32(node + 4) == key) {
            head = klh_rd32(node + 8);
            for (k = 0; head && k < 4096; k++, head = klh_rd32(head + 4)) { if (*n < cap) out[*n] = klh_rd32(head); (*n)++; }
            return 1;
        }
        node = klh_rd32(node);
    }
    return 0;
}

/* the whole table: how many cells list each record (kcvd_rcell) and the first / last key; totals in kcvd_hnodes / kcvd_hrefs */
static void kcvd_census(DWORD L)
{
    DWORD b0 = klh_rd32(L + 0x7c), b1 = klh_rd32(L + 0x80), nb, b, node, head, key, idx; int steps, k;
    memset(kcvd_rcell, 0, sizeof kcvd_rcell); memset(kcvd_rk0, 0xff, sizeof kcvd_rk0); memset(kcvd_rk1, 0xff, sizeof kcvd_rk1);
    kcvd_hnodes = kcvd_hrefs = kcvd_hnb = 0;
    if (!kcvd_ptr_ok(b0) || b1 < b0) return;
    nb = (b1 - b0) / 4; kcvd_hnb = nb;
    if (!nb || nb > 0x1000000u) return;
    for (b = 0; b < nb; b++) {
        node = klh_rd32(b0 + 4 * b);
        for (steps = 0; node && steps < 4096; steps++, node = klh_rd32(node)) {
            key = klh_rd32(node + 4);
            if ((((key >> 12) + (key & 0xfff)) % nb) != b) break;            /* not a chain of this bucket: stop */
            kcvd_hnodes++;
            head = klh_rd32(node + 8);
            for (k = 0; head && k < 4096; k++, head = klh_rd32(head + 4)) {
                idx = klh_rd32(head); kcvd_hrefs++;
                if (idx < KCVD_RMAX) { if (kcvd_rk0[idx] == 0xffffffffu) kcvd_rk0[idx] = key; kcvd_rk1[idx] = key; kcvd_rcell[idx]++; }
            }
        }
    }
}

static void kcvd_keyxz(DWORD key, int *x, int *z)           /* cell centre in world units */
{
    *x = ((int)((key >> 12) & 0xfff) - 1024) * 100; *z = ((int)(key & 0xfff) - 1024) * 100;
}

/* FullRecords: header once, then one record at a time */
static void kcvd_full_begin(void)
{
    DWORD L = kcvd.L, d0 = klh_rd32(L + 0x8c), d1 = klh_rd32(L + 0x90), i, nd = (d1 >= d0 && d1 - d0 < 0x100000u) ? (d1 - d0) / 4 : 0;
    char h[500]; int k = 0;
    klog("coverdump: full hash L+0x78: buckets begin=%08lx end=%08lx (%lu) size [L+0x88]=%lu | walked: %lu cells, %lu record references | records %lu",
         (unsigned long)klh_rd32(L + 0x7c), (unsigned long)klh_rd32(L + 0x80), (unsigned long)kcvd_hnb, (unsigned long)klh_rd32(L + 0x88),
         (unsigned long)kcvd_hnodes, (unsigned long)kcvd_hrefs, (unsigned long)kcvd.rn);
    h[0] = 0;
    for (i = 0; i < nd && i < 40; i++) {
        DWORD r = klh_rd32(d0 + 4 * i); BYTE a6 = 0; klh_rd(r + 0xa6, &a6, 1);
        k += _snprintf(h + k, sizeof h - k - 1, " [%lu]=%08lx idx %lu a6=%u", (unsigned long)i, (unsigned long)r, (unsigned long)klh_rd32(r + 0xa0), a6);
        if (k > (int)sizeof h - 60) break;
    }
    klog("coverdump: full dyn vector [L+0x8c]=%08lx..%08lx count %lu:%s", (unsigned long)d0, (unsigned long)d1, (unsigned long)nd, nd ? h : " (empty)");
}

static void kcvd_full_rec(DWORD i)
{
    DWORD d[0xa8 / 4], k, s; char hx[300]; float p[3], f54, f60; int x0 = 0, z0 = 0, x1 = 0, z1 = 0, j;
    memset(d, 0, sizeof d);
    if (!klh_rd(kcvd.rb + i * 0xa8, d, 0xa8)) { klog("coverdump: full rec %lu UNREADABLE", (unsigned long)i); return; }
    if (i < KCVD_RMAX) { kcvd_keyxz(kcvd_rk0[i], &x0, &z0); kcvd_keyxz(kcvd_rk1[i], &x1, &z1); memcpy(p, kcvd_rpos[i], 12); } else memset(p, 0, 12);
    memcpy(&f54, &d[0x54 / 4], 4); memcpy(&f60, &d[0x60 / 4], 4);
    klog("coverdump: full rec %lu rb=%08lx ent=%08lx '%s' place %s(%.1f %.1f %.1f) cells=%lu first %s(%d,%d) last (%d,%d) | f54=%.3f f60=%.3f diff=%.3f own-idx[+a0]=%lu a6=%u",
         (unsigned long)i, (unsigned long)(kcvd.rb + i * 0xa8), (unsigned long)d[0], i < KCVD_RMAX ? kcvd_rname[i] : "", i < KCVD_RMAX && kcvd_rok[i] ? "" : "NOPLACE ",
         p[0], p[1], p[2], (unsigned long)(i < KCVD_RMAX ? kcvd_rcell[i] : 0), i < KCVD_RMAX && kcvd_rk0[i] == 0xffffffffu ? "NONE " : "", x0, z0, x1, z1,
         f54, f60, f60 - f54, (unsigned long)d[0xa0 / 4], (unsigned)((d[0xa4 / 4] >> 16) & 0xff));
    for (j = 0; j < 3; j++) {
        kcvd_hexdw(hx, sizeof hx, d + j * 14, 14);
        klog("coverdump: full dw %lu +%02x: %s", (unsigned long)i, j * 14 * 4, hx);
    }
    for (k = 0; k < 4; k++) {                             /* GUESS (task): side pointers at +0x90..+0x9c */
        DWORD sp = d[0x90 / 4 + k], sd[17]; float nx, ny, nz;
        if (!sp) continue;
        memset(sd, 0, sizeof sd);
        for (s = 0; s < 17; s++) sd[s] = klh_rd32(sp + s * 4);
        memcpy(&nx, &sd[3], 4); memcpy(&ny, &sd[4], 4); memcpy(&nz, &sd[5], 4);
        kcvd_hexdw(hx, sizeof hx, sd, 17);
        klog("coverdump: full side %lu s%lu %08lx +0..+40: %s | rec@+8=%08lx nrm(+0xc) %.3f %.3f %.3f flags24/28/3c=%08lx/%08lx/%08lx",
             (unsigned long)i, (unsigned long)k, (unsigned long)sp, hx, (unsigned long)sd[2], nx, ny, nz, (unsigned long)sd[9], (unsigned long)sd[10], (unsigned long)sd[15]);
    }
}

/* Finder: what 0x797480 would return for the local player's place (read-only emulation) */
static void kcvd_finder_tick(DWORD now)
{
    DWORD P, gd = 0, node, L = kcvd.L, key, mk, start, cellrecs[256], fall[512], fpass[128], sig = 0, i, mover, mv, pk[6], rv;
    float me[3] = { 0, 0, 0 }, radius, t, last = -1.f; int n, nin = 0, nall = 0, npass = 0, c, j, a, b, cells = 0, present = 0, cnt;
    if (!kcvd.finder || now - kcvd.t_find < 1000) return;
    kcvd.t_find = now;
    if (kcvd.flines >= kcvd.fmax) return;
    if (!(P = klcam_player(&gd)) || !(node = klh_rd32(P + 4)) || !kle_node(node, me, 0)) return;
    for (i = 0; i < kcvd.rn && i < KCVD_RMAX; i++) {     /* any record within 400 on the XZ plane? */
        float dx, dz;
        if (!kcvd_rok[i]) continue;
        dx = kcvd_rpos[i][0] - me[0]; dz = kcvd_rpos[i][2] - me[2];
        if (dx * dx + dz * dz <= 400.f * 400.f) nin++;
    }
    if (!nin) return;
    rv = klh_rd32((DWORD_PTR)KLH_VA(0x00b243f4u)); memcpy(&radius, &rv, 4);
    if (!(radius > 1.f && radius < 5000.f)) radius = 400.f;
    t = (float)((double)radius * 0.009999999776482582);
    n = (int)(2.0 * ceil((double)t));
    if (n < 2 || n > 40) n = 8;
    key = kcvd_cellkey(me); mk = kcvd_mykey(me);
    start = key - (DWORD)(n / 2) * 0x1001u;
    for (a = 0; a < n; a++) for (b = 0; b < n; b++) {
        int cn = 0; DWORD ck = start + (DWORD)a + (DWORD)b * 0x1000u; cells++;
        if (!kcvd_cell(L, ck, cellrecs, 256, &cn)) continue;
        present++;
        for (c = 0; c < cn && c < 256; c++) {
            int dup = 0;
            for (j = 0; j < nall; j++) if (fall[j] == cellrecs[c]) { dup = 1; break; }
            if (!dup && nall < 512) fall[nall++] = cellrecs[c];
        }
    }
    for (j = 0; j < nall; j++) {                          /* the y test of the code */
        DWORD r = kcvd.rb + fall[j] * 0xa8; float y60 = 0, y54 = 0, dy;
        if (fall[j] >= kcvd.rn) continue;
        klh_rd(r + 0x60, &y60, 4); klh_rd(r + 0x54, &y54, 4);
        dy = me[1] - (y60 - y54);
        if (fabs((double)dy) < 50.0 && npass < 128) fpass[npass++] = fall[j];
    }
    mover = klh_rd32(P + 0x6b4); mv = mover ? klh_rd32(mover + 0x44) : 0xffffffffu;
    pk[0] = klh_rd32(P + 0x2d60); pk[1] = klh_rd32(P + 0x2d64); pk[2] = klh_rd32(P + 0x2d74); pk[3] = klh_rd32(P + 0x2954); pk[4] = klh_rd32(P + 0xb50); pk[5] = klh_rd32(P + 0xb54);
    for (j = 0; j < npass; j++) sig = sig * 31u + fpass[j] + 1u;
    for (j = 0; j < 6; j++) sig = sig * 131u + pk[j];
    sig = sig * 131u + mv;
    if (sig == kcvd.f_sig && kcvd.t_flog && now - kcvd.t_flog < 5000) return;
    kcvd.f_sig = sig; kcvd.t_flog = now; kcvd.flines++;
    klog("coverdump: finder t+%lus me (%.1f %.1f %.1f) key=%08lx%s cells %d (present %d) start %08lx n=%d radius %.0f | hash records %d, y-pass %d (as 0x797480 would return), %d records within 400 XZ | "
         "peek [P+2d60]=%08lx [P+2d64]=%08lx [P+2d74]=%08lx [P+2954]=%08lx [P+b50]=%08lx [P+b54]=%08lx mover=%08lx move-id=%lu",
         (unsigned long)((now - kcvd.t_dump) / 1000), me[0], me[1], me[2], (unsigned long)key, key == mk ? "" : " KEYMISMATCH(mine differs!)", cells, present, (unsigned long)start, n, radius,
         nall, npass, nin, (unsigned long)pk[0], (unsigned long)pk[1], (unsigned long)pk[2], (unsigned long)pk[3], (unsigned long)pk[4], (unsigned long)pk[5], (unsigned long)mover, (unsigned long)mv);
    for (cnt = 0; cnt < 10; cnt++) {                      /* up to 10 nearest records within 400 (XZ): in a scanned cell? y test? */
        int best = -1; float bd = 1e30f;
        for (i = 0; i < kcvd.rn && i < KCVD_RMAX; i++) {
            float dx, dz, dd;
            if (!kcvd_rok[i]) continue;
            dx = kcvd_rpos[i][0] - me[0]; dz = kcvd_rpos[i][2] - me[2]; dd = dx * dx + dz * dz;
            if (dd > 400.f * 400.f || dd <= last || dd >= bd) continue;
            bd = dd; best = (int)i;
        }
        if (best < 0) break;
        last = bd;
        {
            DWORD r = kcvd.rb + (DWORD)best * 0xa8; float y60 = 0, y54 = 0, dy; int inh = 0, inp = 0;
            klh_rd(r + 0x60, &y60, 4); klh_rd(r + 0x54, &y54, 4); dy = me[1] - (y60 - y54);
            for (j = 0; j < nall; j++) if (fall[j] == (DWORD)best) inh = 1;
            for (j = 0; j < npass; j++) if (fpass[j] == (DWORD)best) inp = 1;
            klog("coverdump: finder rec %d '%s' place (%.1f %.1f %.1f) dXZ=%.1f | in scanned cells=%s y-test(|%.1f-(%.1f-%.1f)|=%.1f <50)=%s | hash cells listing it=%lu sides %08lx %08lx %08lx %08lx",
                 best, kcvd_rname[best], kcvd_rpos[best][0], kcvd_rpos[best][1], kcvd_rpos[best][2], sqrt((double)bd), inh ? "YES" : "NO", me[1], y60, y54, fabs((double)dy),
                 inp ? "PASS" : (inh ? "FAIL" : "-"), (unsigned long)kcvd_rcell[best], (unsigned long)klh_rd32(r + 0x90), (unsigned long)klh_rd32(r + 0x94),
                 (unsigned long)klh_rd32(r + 0x98), (unsigned long)klh_rd32(r + 0x9c));
        }
    }
}

static void kcvd_rearm(DWORD gd, DWORD st)
{
    memset(kcvd_rok, 0, sizeof kcvd_rok); memset(kcvd_rname, 0, sizeof kcvd_rname); memset(kcvd_rcell, 0, sizeof kcvd_rcell);
    kcvd.flines = 0; kcvd.f_sig = 0; kcvd.t_flog = 0; kcvd.t_find = 0;
    kcvd.stage = 0; kcvd.stab_at = 0; kcvd.gd = gd; kcvd.st = st; kcvd.last_rn = 0; kcvd.i = 0; kcvd.near_n = 0;
}

static void kcvd_tick(int game_thread)
{
    DWORD now, gd, st, L, rb, rn, pb, pe, n;
    if (!kcvd.on || !game_thread || kcvd.bad) return;
    now = GetTickCount();
    if (kcvd.last_tick && now - kcvd.last_tick < 50 && kcvd.stage != 1 && kcvd.stage != 2 && kcvd.stage != 5) return;       /* idle stages: 20 Hz at most */
    kcvd.last_tick = now;
    __try {
        if (!kcvd_state(&gd, &st)) return;
        if (gd != kcvd.gd || (st == 0x16 && kcvd.st != 0x16)) kcvd_rearm(gd, st);      /* a new level load */
        kcvd.st = st;
        switch (kcvd.stage) {
        case 0:
            if (st != 0x19 || !kcvd_read_list(gd, &L, &rb, &rn, &pb, &pe) || !rn || rn > 100000u || !rb) { kcvd.stab_at = 0; return; }
            if (!kcvd.stab_at || rn != kcvd.last_rn || rb != kcvd.last_rb || pb != kcvd.last_pb || pe != kcvd.last_pe) {
                kcvd.stab_at = now; kcvd.last_rn = rn; kcvd.last_rb = rb; kcvd.last_pb = pb; kcvd.last_pe = pe; return;
            }
            if (now - kcvd.stab_at < 2000) return;
            kcvd.L = L; kcvd.rb = rb; kcvd.rn = rn; kcvd.pb = pb; kcvd.pe = pe;
            kcvd.npt = (pe >= pb && pe - pb < 0x4000000u) ? (pe - pb) / 0x7c : 0;
            kcvd.t_dump = now;
            kcvd_begin();
            kcvd.i = 0; kcvd.stage = 1;
            return;
        case 1:                                           /* records */
            for (n = 0; n < KCVD_PER_TICK && kcvd.i < kcvd.rn && kcvd.i < kcvd.maxr; n++, kcvd.i++) kcvd_rec_line(kcvd.i);
            if (kcvd.i >= kcvd.rn || kcvd.i >= kcvd.maxr) { kcvd.i = 0; kcvd.stage = 2; }
            return;
        case 2: {                                         /* points (all read so the cache is whole; lines only below MaxPoints) */
            DWORD lim = kcvd.npt < KCVD_CACHE ? kcvd.npt : KCVD_CACHE;
            for (n = 0; n < KCVD_PER_TICK && kcvd.i < lim; n++, kcvd.i++) kcvd_pt_line(kcvd.i);
            if (kcvd.i >= lim) {
                klog("coverdump: end records=%lu (lines %lu) points=%lu (lines %lu, cached %lu) dropped=%lu", (unsigned long)kcvd.rn,
                     (unsigned long)(kcvd.rn < kcvd.maxr ? kcvd.rn : kcvd.maxr), (unsigned long)kcvd.npt, (unsigned long)(kcvd.npt < kcvd.maxp ? kcvd.npt : kcvd.maxp),
                     (unsigned long)lim, (unsigned long)klh_rd32((DWORD_PTR)KLH_VA(KCVD_DROPPED)));
                kcvd.t_near = now; kcvd.near_n = 0; kcvd.stage = 3;
                if (kcvd.full || kcvd.finder) kcvd_census(kcvd.L);
                if (kcvd.full) { kcvd_full_begin(); kcvd.i = 0; kcvd.stage = 5; }
            }
            return;
        }
        case 5:                                           /* FullRecords: records, their hash cells, sides */
            for (n = 0; n < KCVD_FULL_TICK && kcvd.i < kcvd.rn && kcvd.i < kcvd.maxr; n++, kcvd.i++) kcvd_full_rec(kcvd.i);
            if (kcvd.i >= kcvd.rn || kcvd.i >= kcvd.maxr) { klog("coverdump: full end %lu records", (unsigned long)kcvd.i); kcvd.t_near = now; kcvd.near_n = 0; kcvd.stage = 3; }
            return;
        case 3:                                           /* 'near' every 5 s for 60 s */
            kcvd_finder_tick(now);
            if (now - kcvd.t_near >= 5000) {
                kcvd.t_near = now; kcvd_near();
                if (++kcvd.near_n >= 12) kcvd.stage = 4;
            }
            return;
        default: kcvd_finder_tick(now); return;           /* stage 4: done, the finder probe goes on */
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        kcvd.bad = 1;
        klog("coverdump: exception in the dump - probe off");
    }
}

static void kcvd_init(void)
{
#ifdef KLHOOK_TEST
    int def = 1;
#else
    int def = 0;
#endif
    memset(&kcvd, 0, sizeof kcvd);
    kcvd.on = GetPrivateProfileIntA("CoverDump", "Enable", def, klh_ini) != 0;
    kcvd.full = GetPrivateProfileIntA("CoverDump", "FullRecords", def, klh_ini) != 0;
    kcvd.finder = GetPrivateProfileIntA("CoverDump", "Finder", def, klh_ini) != 0;
    kcvd.fmax = (DWORD)GetPrivateProfileIntA("CoverDump", "FinderMax", 400, klh_ini);
    kcvd.maxp = (DWORD)GetPrivateProfileIntA("CoverDump", "MaxPoints", 6000, klh_ini);
    kcvd.maxr = (DWORD)GetPrivateProfileIntA("CoverDump", "MaxRecords", 2000, klh_ini);
    if (kcvd.maxp > KCVD_CACHE) kcvd.maxp = KCVD_CACHE;
    if (kcvd.maxr > 100000u) kcvd.maxr = 100000u;
    if (kcvd.on) klog("coverdump: on (READ ONLY, recommended on for test runs, off for players): once per level load, records <= %lu, points <= %lu, FullRecords=%d Finder=%d (both recommended on for test runs, off for players) FinderMax=%lu",
                                    (unsigned long)kcvd.maxr, (unsigned long)kcvd.maxp, kcvd.full, kcvd.finder, (unsigned long)kcvd.fmax);
}

#endif
