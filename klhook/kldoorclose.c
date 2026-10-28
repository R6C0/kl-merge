/*
 * kldoorclose.c - [KLHook] DoorCloseMs: the Retomoto lift doors shut again (SHIP and TEST alike). Part of KLHook, included by klhook.c AFTER
 * kljoin.c and klescort.c (uses klog, klh_rd, klh_rd32, klh_data, klh_rdstr, klh_ini, klh_exe_ok, KLH_VA, KLE_ENTS, kle_node, klj_box, klj_feet,
 * klj_in_box, klj_ride, klj_door_at, KLJ_NBOX).
 *
 * Why: the escape lift's door clip is 160 frames (open 0..75, close ~80..160) but the ZMatPosAnimProxy only ever plays 0..75, so once open
 * the doors stay open (re/retomoto_lift_doors.md). DoorCloseMs ms after a lift-door proxy opened, each of its leaves gets the closing half:
 *   [leaf+0xd0]=75, [leaf+0xd4]=160 (ints the leaf tick copies into the play head) AND the clip-state floats [leaf+0x44]=75.0f, [leaf+0x48]=160.0f
 *   (A1LIFT6b: the ints alone replayed the opening), then 0x59dce0(leaf) (thiscall, no args, restarts the clock). Proven live in the TEST build
 *   (A1LIFT6c PASS, 0 faults: both lifts slide shut in 3.5 s).
 *
 * HOW THE OPEN IS SEEN (the TEST build's probe wrapped vtable 0xbc36bc slots; a vtable entry lies in the hashed range and a SHIP build refuses
 * every such write, and every .text patch). Here NOTHING is written to the exe's image: the proxy objects are found by READING (entity table
 * walk [[[KLE_ENTS]+0xc]+0xc], 0x80-byte slots, object at +0x60, as klsync.c; if the walk finds none, a rate-limited scan of the private
 * read-write memory for the proxy vtable, as klbotfill.c's ramp probe) and each tick their first leaf is POLLED:
 *   the handler 0x7ed520 (READ) writes [leaf+0xd0]=[proxy+0x23c], [leaf+0xd4]=[proxy+0x240], [leaf+0x99]=1 and the start ms [leaf+0x34] =
 *   game ms [[0xdd2640]+0x48]. So "leaf start changed, leaf plays, ints = the proxy's own first/last (last nonzero)" is an OPEN; the tick of
 *   the open is now - (game ms - start), exact even when found late. Our own close writes 75/160 and never matches. The only writes are
 *   heap data (the leaf's ints and floats) and one thiscall into 0x59dce0, on the game thread only; no code, vtable or import is touched.
 * GUESS: the proxies are in the entity table (klbotfill's DD02r note says a ZTriggerBox walk found none; hence the memory-scan fallback).
 *
 * SAFETY: only while a [Join] box with a car box (CarMin/CarMax) is active on this scene (a lift map); only proxies whose entity name contains
 *   Elevator / Escape / VideoProxy / Exit, or is unreadable (as the probe); 1..8 leaves, each with vtable 0xba8f3c; never while a LOCAL player's feet
 *   are within the car box (+KLDC_PAD units, GUESS) or a lift ride runs (postponed, re-asked every tick); a close more than 2 min overdue is
 *   given up. One 'doorclose:' line per close. Key: [KLHook] DoorCloseMs (default 0 = off, NOT in [Join]: kljoin reads that section as a lift box).
 *   Also stamps klj_door_at (CarStallAfterDoorMs) when it sees an open, only while DoorCloseMs > 0.
 */
#include "kldoorclose_logic.h"
#define KLDC_VT_PROXY  0x00bc36bc
#define KLDC_VT_LEAF   0x00ba8f3c
#define KLDC_CLOSE_FN  0x0059dce0
#define KLDC_GAMECLK   0x00dd2640
#define KLDC_PAD       60.0f
#define KLDC_FIND_MS   3000
#define KLDC_SCAN_MS   15000

static struct kldc_p kldc_t[KLDC_N];
static int kldc_ms, kldc_nscan, kldc_remote;     /* kldc_remote: [KLHook] DoorCloseRemote (default 0) */ static DWORD kldc_find_at, kldc_scan_at;
#ifdef KLHOOK_TEST
static void klpr_leaf_start(DWORD me, DWORD at);       /* klprobe.c (DoorLeaves): sample the closing too */
#endif

static int kldc_name_ok(DWORD obj)
{
    char b[96]; DWORD n = klh_rd32(obj + 4);
    if (n && klh_rdstr(klh_rd32(n + 0x6c), b, sizeof b)) return strstr(b, "Elevator") || strstr(b, "Escape") || strstr(b, "VideoProxy") || strstr(b, "Exit");
    /* unreadable name: allowed only if the proxy has the lift door's own frames (first 0, last 75; GUESS from the Retomoto data), so a generic
       anim proxy is never closed with the lift's 75..160 */
    return klh_rd32(obj + 0x23c) == 0 && klh_rd32(obj + 0x240) == 75;
}

/* a proxy that looks sane: vtable, 1..8 leaves, leaf 0 a ZMatPosAnim */
static int kldc_sane(DWORD me)
{
    DWORD cnt, l0;
    if (klh_rd32(me) != (DWORD)(DWORD_PTR)KLH_VA(KLDC_VT_PROXY)) return 0;
    cnt = klh_rd32(me + 0x30);
    if (cnt < 1 || cnt > 8) return 0;
    l0 = klh_rd32(me + 0x34);
    return l0 > 0x10000 && klh_rd32(l0) == (DWORD)(DWORD_PTR)KLH_VA(KLDC_VT_LEAF);
}

static void kldc_add(DWORD me)
{
    int f = kldc_slot_free(kldc_t, KLDC_N, me); DWORD l0;
    if (f < 0 || kldc_t[f].me == me || !kldc_sane(me) || !kldc_name_ok(me)) return;
    l0 = klh_rd32(me + 0x34);
    /* baseline the leaf's current start: a door that never opened must not look like an open because its init state already matches */
    kldc_t[f].me = me; kldc_t[f].at = 0; kldc_t[f].seen = klh_rd32(l0 + 0x34); kldc_t[f].done = 1;       /* followed; nothing to close until an open is seen */
    klog("doorclose: following lift-door proxy %08lx (%lu leaf(s))", (unsigned long)me, (unsigned long)klh_rd32(me + 0x30));
}

/* entity table walk (read only); -> proxies seen */
static int kldc_walk(void)
{
    DWORD p, tab, i, blk[64 * 32]; int n = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return 0;
    for (i = 0; i < 0x10000; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4];
            if (o < 0x10000 || klh_rd32(o) != (DWORD)(DWORD_PTR)KLH_VA(KLDC_VT_PROXY)) continue;
            n++; kldc_add(o);
        }
    }
    return n;
}

/* fallback: the private read-write memory, like klbotfill.c's ramp probe (0.2 - 1 s: at most 3 scans in 2 min, only on a lift map) */
static int kldc_scan(void)
{
    static BYTE buf[0x10000]; MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; int n = 0;
    while ((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            SIZE_T o, j;
            for (o = 0; o < mbi.RegionSize; o += sizeof buf) {
                SIZE_T m = mbi.RegionSize - o < sizeof buf ? mbi.RegionSize - o : sizeof buf;
                if (!klh_rd((DWORD_PTR)mbi.BaseAddress + o, buf, m)) continue;
                for (j = 0; j + 4 <= m; j += 4)
                    if (*(DWORD *)(buf + j) == (DWORD)(DWORD_PTR)KLH_VA(KLDC_VT_PROXY)) { n++; kldc_add((DWORD)((DWORD_PTR)mbi.BaseAddress + o + j)); }
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    return n;
}

/* a local player (or a ride in progress) is at a lift car: do not shut the doors */
static int kldc_busy(void)
{
    DWORD gd, pl; BYTE sel[2]; int i, b; float feet[3];
    if (klj_ride.on) return 1;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, sel, 2)) return 1;
    for (i = 0; i < 2; i++) {
        if (sel[i] == 0xff || sel[i] >= 28 || !(pl = klh_rd32(gd + 0x828 + 4 * sel[i])) || !klj_feet(pl, feet)) continue;
        for (b = 0; b < KLJ_NBOX; b++) if (klj_box[b].on && klj_box[b].has_car && klj_in_box(feet, klj_box[b].clo, klj_box[b].chi, KLDC_PAD)) return 1;
    }
    /* [KLHook] DoorCloseRemote=1, network session only: any other player of the session's hero table (remote human, AI heister) whose feet are at a
       car holds the doors too, so the host does not shut them on a joiner who is still riding. The table (klco_table, 0x74ee24) is the one the online
       escort and get-up code read live (BP2: 8 humans); [gd+0x828] is the LOCAL slot list only (every reader indexes it by +0x898; research 10-29).
       Entries this machine is master of (klco_is_master) are skipped: they are the local players already checked above. Game thread only (kldc_tick). */
    if (kldc_remote_slot(0, -1, -1, kl_online(), kldc_remote)) {
        DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598)), ents = 0, P; int n = 0; static int toldTbl, toldNone;
        if (!sm || !klco_table(sm, &ents, &n)) { if (!toldNone++) klog("doorclose: DoorCloseRemote: the session player table is not readable yet (said once)"); return 0; }
        if (!toldTbl++) klog("doorclose: DoorCloseRemote: the session player table holds %d player(s)", n);
        for (i = 0; i < n && i < 16; i++) {
            if (!(P = klco_ent(ents, n, i)) || klco_is_master(P) || !klj_feet(P, feet)) continue;
            for (b = 0; b < KLJ_NBOX; b++) if (klj_box[b].on && klj_box[b].has_car && klj_in_box(feet, klj_box[b].clo, klj_box[b].chi, KLDC_PAD)) {
                static int told; if (!told++) klog("doorclose: table player %d (not ours) is at car %d: doors held", i, b + 1);
                return 1;
            }
        }
    }
    return 0;
}

static int kldc_lift_map(void)
{
    int b;
    for (b = 0; b < KLJ_NBOX; b++) if (klj_box[b].on && klj_box[b].wasactive && klj_box[b].has_car) return 1;
    return 0;
}

/* an open seen from outside (the TEST probe's handler wrapper): follow it from now. Idempotent with the poll. */
static void kldc_note(DWORD me)
{
    int f; DWORD l0;
    if (kldc_ms <= 0 || !kldc_sane(me)) return;
    f = kldc_slot(kldc_t, KLDC_N, me);
    if (f < 0) return;
    l0 = klh_rd32(me + 0x34);
    kldc_t[f].me = me; kldc_t[f].at = GetTickCount() ? GetTickCount() : 1; kldc_t[f].seen = klh_rd32(l0 + 0x34); kldc_t[f].done = 0;
}

static void kldc_close(int k, DWORD now)
{
    int i, n = 0; DWORD cnt, ctl, first = 75, last = 160; float f_first = 75.0f, f_last = 160.0f;
    cnt = klh_rd32(kldc_t[k].me + 0x30);
    for (i = 0; i < (int)cnt; i++) {
        ctl = klh_rd32(kldc_t[k].me + 0x34 + 4 * i);
        if (ctl < 0x10000 || klh_rd32(ctl) != (DWORD)(DWORD_PTR)KLH_VA(KLDC_VT_LEAF)) continue;
        if (!klh_data((void *)(DWORD_PTR)(ctl + 0xd0), &first, 4, "doorclose first") || !klh_data((void *)(DWORD_PTR)(ctl + 0xd4), &last, 4, "doorclose last")) continue;
        /* A1LIFT6b: the ints alone are not enough - the clip state floats (ctl+0x44 first, +0x48 last, READ) stayed 0..75 and the restart replayed
           the OPENING. The handler copies the ints there via 0x78f190 / 0x505550 before 0x59dce0; we write the floats ourselves. */
        if (!klh_data((void *)(DWORD_PTR)(ctl + 0x44), &f_first, 4, "doorclose clip first") || !klh_data((void *)(DWORD_PTR)(ctl + 0x48), &f_last, 4, "doorclose clip last")) continue;
        ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLDC_CLOSE_FN))((void *)(DWORD_PTR)ctl, 0);
        n++;
    }
    kldc_t[k].done = 1;
    kldc_t[k].seen = klh_rd32(klh_rd32(kldc_t[k].me + 0x34) + 0x34);                   /* our restart is not an open */
    klog("doorclose: proxy %08lx: %d of %lu leaf(s) set to frames 75..160 and restarted %lu ms after the doors opened (DoorCloseMs=%d)", (unsigned long)kldc_t[k].me, n,
         (unsigned long)cnt, (unsigned long)(now - kldc_t[k].at), kldc_ms);
#ifdef KLHOOK_TEST
    klpr_leaf_start(kldc_t[k].me, now);
#endif
}

/* every tick (klhook.c, right after klj_tick). Idle (one compare) when DoorCloseMs = 0. Detection runs on either tick thread; the close only on the game's. */
static void kldc_tick(int game_thread)
{
    int k; DWORD now;
    if (kldc_ms <= 0 || !klh_exe_ok) return;
    if (!kldc_lift_map()) {                                    /* not a lift map (or level left): forget proxies and the scan budget */
        memset(kldc_t, 0, sizeof kldc_t); kldc_nscan = 0; kldc_find_at = 0; kldc_scan_at = 0;
        return;
    }
    now = GetTickCount();
    if (now - kldc_find_at >= KLDC_FIND_MS) {                  /* look for proxies (also re-found after a level load) */
        int found, any = 0;
        kldc_find_at = now;
        found = kldc_walk();
        for (k = 0; k < KLDC_N; k++) if (kldc_t[k].me && kldc_sane(kldc_t[k].me)) any = 1;
        if (!found && !any) {
            /* at most 3 scans per lift-map visit (no refilling window): the proxies may simply not be where we look */
            if (kldc_nscan < 3 && now - kldc_scan_at >= KLDC_SCAN_MS) {
                kldc_scan_at = now; kldc_nscan++;
                { int sn = kldc_scan(); klog("doorclose: the entity walk found no door proxy: memory scan %d of 3 found %d", kldc_nscan, sn); }
            }
        }
    }
    for (k = 0; k < KLDC_N; k++) {
        DWORD me = kldc_t[k].me, l0, st, gms, i0 = 0, i1 = 0, p0 = 0, p1 = 0; BYTE act = 0; int step;
        if (!me) continue;
        if (!kldc_sane(me)) { kldc_t[k].me = 0; continue; }     /* gone (level left) */
        l0 = klh_rd32(me + 0x34);
        st = klh_rd32(l0 + 0x34);
        klh_rd(l0 + 0x99, &act, 1); klh_rd(l0 + 0xd0, &i0, 4); klh_rd(l0 + 0xd4, &i1, 4); klh_rd(me + 0x23c, &p0, 4); klh_rd(me + 0x240, &p1, 4);
        if (kldc_is_open(kldc_t[k].seen, st, act, i0, i1, p0, p1)) {
            gms = klh_rd32(klh_rd32((DWORD_PTR)KLH_VA(KLDC_GAMECLK)) + 0x48);
            if (!gms || gms < st) klog("doorclose: game clock %lu unusable against leaf start %lu: open taken as now", (unsigned long)gms, (unsigned long)st);
            kldc_t[k].at = kldc_open_at(now, gms, st); kldc_t[k].seen = st; kldc_t[k].done = 0;
            klj_door_at = kldc_t[k].at;
            klog("doorclose: proxy %08lx opened %lu ms ago (leaf start %lu, game ms %lu): close due in %d ms", (unsigned long)me, (unsigned long)(now - kldc_t[k].at), (unsigned long)st, (unsigned long)gms, kldc_ms);
        } else if (st != kldc_t[k].seen && !kldc_t[k].at) kldc_t[k].seen = st;          /* baseline of a proxy that has not opened */
        if (kldc_t[k].done) continue;
        step = kldc_step(now, kldc_t[k].at, kldc_ms, 0);
        if (step == 0) continue;
        if (step == 1 || step == 3) step = kldc_step(now, kldc_t[k].at, kldc_ms, (!game_thread || kldc_busy()) ? 1 : 0);
        if (step == 2) { kldc_t[k].done = 1; continue; }        /* stale: give up, touch nothing */
        if (step == 1) kldc_close(k, now);                      /* step 3 = postponed, asked again next tick */
    }
}

static void kldc_init(void)
{
    kldc_ms = GetPrivateProfileIntA("KLHook", "DoorCloseMs", 0, klh_ini);
    if (kldc_ms < 0 || kldc_ms > 120000) kldc_ms = 0;
    kldc_remote = GetPrivateProfileIntA("KLHook", "DoorCloseRemote", 0, klh_ini) != 0;
    klog("doorclose: [KLHook] DoorCloseRemote=%d (online: other actors at the car hold the doors)", kldc_remote);
    klog("doorclose: [KLHook] DoorCloseMs=%d (%s)", kldc_ms, kldc_ms ? "doors are closed again that many ms after they opened, never while a player is at the car" : "off");
}
