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
 */
#ifndef KLCOVERDUMP_C
#define KLCOVERDUMP_C

#define KCVD_VT      0x00bbece4u
#define KCVD_SM      0x0168e598u
#define KCVD_DROPPED 0x0156b27cu
#define KCVD_CACHE   20000
#define KCVD_PER_TICK 100

static struct {
    int on, stage, armed;                              /* stage: 0 wait for a stable list, 1 records, 2 points, 3 near, 4 done */
    DWORD maxp, maxr, gd, st, L, rb, rn, pb, pe, npt, i, stab_at, t_dump, t_near, near_n;
    DWORD last_rb, last_rn, last_pb, last_pe, last_tick;
    int bad;
} kcvd;
static float kcvd_pos[KCVD_CACHE][3];

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

static void kcvd_rearm(DWORD gd, DWORD st)
{
    kcvd.stage = 0; kcvd.stab_at = 0; kcvd.gd = gd; kcvd.st = st; kcvd.last_rn = 0; kcvd.i = 0; kcvd.near_n = 0;
}

static void kcvd_tick(int game_thread)
{
    DWORD now, gd, st, L, rb, rn, pb, pe, n;
    if (!kcvd.on || !game_thread || kcvd.bad) return;
    now = GetTickCount();
    if (kcvd.last_tick && now - kcvd.last_tick < 50 && kcvd.stage != 1 && kcvd.stage != 2) return;       /* idle stages: 20 Hz at most */
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
            }
            return;
        }
        case 3:                                           /* 'near' every 5 s for 60 s */
            if (now - kcvd.t_near >= 5000) {
                kcvd.t_near = now; kcvd_near();
                if (++kcvd.near_n >= 12) kcvd.stage = 4;
            }
            return;
        default: return;
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
    kcvd.maxp = (DWORD)GetPrivateProfileIntA("CoverDump", "MaxPoints", 6000, klh_ini);
    kcvd.maxr = (DWORD)GetPrivateProfileIntA("CoverDump", "MaxRecords", 2000, klh_ini);
    if (kcvd.maxp > KCVD_CACHE) kcvd.maxp = KCVD_CACHE;
    if (kcvd.maxr > 100000u) kcvd.maxr = 100000u;
    if (kcvd.on) klog("coverdump: on (READ ONLY, recommended on for test runs, off for players): once per level load, records <= %lu, points <= %lu", (unsigned long)kcvd.maxr, (unsigned long)kcvd.maxp);
}

#endif
