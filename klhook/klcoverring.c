/*
 * klcoverring.c - [CoverRing] READ-ONLY, LOG-ONLY poll of the engine's real cover count and of the ZHavokCar scripts' ring state. 2026-11-01.
 * Included by klhook.c right after klcoverdump.c (uses klh_rd / klh_rd32 / klog / klh_ini / klh_avt / klh_is_hashed / KLE_ENTS / kle_node and
 * klcoverdump.c's kcvd_state / kcvd_read_list / kcvd_name / kcvd_ptr_ok). NOTHING HERE HAS RUN IN THE GAME. It patches no code, swaps no vtable
 * slot, sets no debug register and writes no memory: reads only (re/dm_car_cover_1101.md "Writer search" and "c9 addendum").
 *
 * WHY: the DM01 / DM03 online CLIENT asserts (0x6567e8 ...) come from cover indices the host replicated for points 347.. that the client's list does
 * not have. The writer of that ring is 0x81b6f0 (thiscall, ecx = the car SCRIPT, [script+0x40] = the ZHavokCar, car->script at [car+0x968]);
 * it bumps the REAL count [L+0x68] by 8 per car (0x558350) and records the indices at [script+0x1c8+n*4], count [script+0x1c4], done flag [script+0x1e8],
 * reserved flag [script+0x1e9]. The gate that keeps the client from running it (or lets the host run it for only some cars) is not found. This
 * probe gives the evidence by LOGGING on both seats: when [L+0x68] changes and what each car's script says at that moment.
 *   L = [[0xdd265c]+0x15a0] (klcoverdump.c's kcvd_read_list). Count = dword [L+0x68] (the real one; the points vector begin/end [L+0x44] / [L+0x48],
 *   stride 0x7c, is logged beside it). Cars: every entity-table object (klcensor.c walk) whose [obj+0x968] is a pointer to a script with
 *   [script+0x40] == obj (structural; the vtable is logged: ZHavokCar 0xbcb00c, ZOnlineEscHavokCar 0xbc94ac is a candidate subclass - GUESS).
 *   [car+0x8c0] (byte, the state setter 0x8d6210 clears it) and [car+0xa28] (state) are logged as dwords.
 *
 * 1. POLL: from each level load for 90 s at every game tick, then every 5 s, one 'coverring: poll' line per CHANGE of [L+0x68] (or of the car
 *    signature: a done / reserved flag flip), with the time since load and the session state. The first sample of a load always logs. At each
 *    logged sample every car gets a 'coverring: car' line. The entity table is rescanned for cars at the load, on a count change and every 5 s.
 *    Session-state changes are logged too ('coverring: state'). Budget: KCR_MAX_ENUM enumerations a load.
 * 2. CALLERS (Callers=1): NOT IMPLEMENTED ON PURPOSE. The vtables of the listed callers (ZHavokCarScript 0xbd1694, ZHavokCarIdleGoal 0xbd16dc,
 *    ZVehicleMove/Fire/FireOnRoad/SpecialMoveBehaviour 0xbcd740 0xbcd9c8 0xbcdaa0 0xbcdb78, ZAIInputRoadComponent 0xbcb9f8, ZVehicleExitBehaviour)
 *    lie in .rdata 0xb8b000-0xbeb000, which is CEG-hashed (klranges.h; re/antitamper.md: a changed vtable entry ends the process with 0x8000dead).
 *    So a slot swap is refused by policy; the key only logs, once, which slot addresses are hashed (klh_is_hashed, run time) and that the trampolines
 *    are skipped. Fallback = the poll above. (0x8d6210's other callers and 0x75eb80 / 0x5c2d50 are plain functions inside hashed .text.)
 *
 * 3. CLIENTBUILD (CR2, 2026-11-01, experimental): ONLY an online CLIENT (session role [sm+0x54]==3, game type 4), ONLY on slots in ClientBuildMaps, once per load, on the game
 *    thread: when the cover list exists, [L+0x68] has been unchanged for 1 s and cars were found, call the ring writer 0x81b6f0 (ecx = car script) for each car in ENTITY-TABLE
 *    order whose script has done==0 and rsv==0 (GUESS: this order equals the host's; every car and the indices are logged so the bench can compare). The writer is hashed
 *    code: CALLED, never patched; no debug register. A fault in it turns the feature off for the run. Lines: 'coverring: clientbuild ...'. Gate logic: klcoverring_logic.h.
 * ini: [CoverRing] Enable=1 in the TEST build / 0 in SHIP (recommended on for test runs, off for players)
 *                  Callers=1 TEST / 0 SHIP (recommended on for test runs, off for players): only logs that the slot swaps are skipped (hashed vtables)
 *                  ClientBuild=0 in TEST and SHIP (recommended off: experimental, enable only for the CR2 bench)  ClientBuildMaps=F01,F03 (DM01 / DM03 slots)
 *                  ClientBuildHost=0 in TEST and SHIP (recommended off: experimental, CR3 bench): the HOST prebuilds at load too. CR1_DM01 showed the client never
 *                  runs the writer and the host runs it per car on ACTIVATION (order 871, 737+792, 906 = not table order), so client-only table order cannot match;
 *                  both seats in table order at load can, IF the host's later activation reuses rsv=1 indices (GUESS, see klcoverring_logic.h).
 * LINES (prefix 'coverring:'): on / callers / load / state / poll / car / scan / clientbuild.
 */
#ifndef KLCOVERRING_C
#define KLCOVERRING_C

#include "klcoverring_logic.h"

#define KCR_NCAR 64
static struct {
    int on, callers, bad, have, nenum;
    int cb, cb_host, cb_done, cb_last, cb_bad; char cb_maps[64]; DWORD cb_cnt, cb_cnt_at;      /* ClientBuild (CR2) */
    DWORD gd, st, t_load, t_poll, t_scan, L, cnt, sig, ncars;
    struct { DWORD car, slot; } c[KCR_NCAR];
} kcr;

static BYTE kcr_rd8(DWORD p) { BYTE b = 0; klh_rd(p, &b, 1); return b; }

/* walk the entity table for ZHavokCar-shaped objects (klcensor.c walk) */
static void kcr_scan(void)
{
    DWORD p, tab, i, blk[64 * 32]; int n = 0;
    kcr.ncars = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x10000 && n < KCR_NCAR; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < KCR_NCAR; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], s;
            if (!kcvd_ptr_ok(o)) continue;
            s = klh_rd32(o + 0x968);
            if (!kcvd_ptr_ok(s) || !kcr_script_matches(o, klh_rd32(s + 0x40))) continue;
            kcr.c[n].car = o; kcr.c[n].slot = i + k; n++;
        }
    }
    kcr.ncars = (DWORD)n;
    kcr.t_scan = GetTickCount();
}

/* signature of the cars' ring state (also what the car lines print) */
static DWORD kcr_cars_sig(DWORD *ran)
{
    DWORD sig = 0, i; *ran = 0;
    for (i = 0; i < kcr.ncars; i++) {
        DWORD car = kcr.c[i].car, s = klh_rd32(car + 0x968), n = kcvd_ptr_ok(s) ? klh_rd32(s + 0x1c4) : 0, d = kcvd_ptr_ok(s) ? kcr_rd8(s + 0x1e8) : 0, r = kcvd_ptr_ok(s) ? kcr_rd8(s + 0x1e9) : 0;
        sig = kcr_sig_add(sig, car, s, n, d, r);
        if (d || r) (*ran)++;
    }
    return sig;
}

static void kcr_car_lines(DWORD now)
{
    DWORD i;
    for (i = 0; i < kcr.ncars; i++) {
        DWORD car = kcr.c[i].car, s = klh_rd32(car + 0x968), n = 0, d = 0, r = 0, idx[8], k, shown; char nm[80], ix[120]; int l = 0;
        memset(idx, 0xff, sizeof idx);
        if (kcvd_ptr_ok(s)) {
            n = klh_rd32(s + 0x1c4); d = kcr_rd8(s + 0x1e8); r = kcr_rd8(s + 0x1e9);
            for (k = 0; k < 8; k++) idx[k] = klh_rd32(s + 0x1c8 + k * 4);
        }
        shown = kcr_idx_shown(n);
        ix[0] = 0;
        for (k = 0; k < shown && l < (int)sizeof ix - 12; k++) l += _snprintf(ix + l, sizeof ix - l - 1, "%s%ld", k ? "," : "", (long)idx[k]);
        ix[sizeof ix - 1] = 0;
        kcvd_name(car, nm, sizeof nm);
        klog("coverring: car #%lu t+%lums slot %lu '%s' car=%08lx vt=%08lx script=%08lx n[+1c4]=%lu done[+1e8]=%lu rsv[+1e9]=%lu idx[+1c8]=[%s] car+8c0=%08lx car+a28=%08lx",
             (unsigned long)i, (unsigned long)(now - kcr.t_load), (unsigned long)kcr.c[i].slot, nm, (unsigned long)car, (unsigned long)klh_rd32(car),
             (unsigned long)s, (unsigned long)n, (unsigned long)d, (unsigned long)r, ix, (unsigned long)klh_rd32(car + 0x8c0), (unsigned long)klh_rd32(car + 0xa28));
    }
}

static void kcr_rearm(DWORD gd, DWORD st, DWORD now)
{
    memset(&kcr.c, 0, sizeof kcr.c);
    kcr.cb_done = 0; kcr.cb_last = -1; kcr.cb_cnt = 0xfffffffful; kcr.cb_cnt_at = now;
    kcr.have = 0; kcr.nenum = 0; kcr.ncars = 0; kcr.gd = gd; kcr.st = st; kcr.t_load = now; kcr.t_poll = 0; kcr.t_scan = 0; kcr.L = 0; kcr.cnt = 0; kcr.sig = 0;
    if (kcr.on) klog("coverring: load gd=%08lx state=%lx (poll every tick for %lu s, then every %lu s)", (unsigned long)gd, (unsigned long)st, KCR_FAST_MS / 1000, KCR_SLOW_MS / 1000);
}

/* ClientBuild (CR2): ONE call of the writer on the game thread. 0x81b6f0 (re/dm_car_cover_1101.md; dasm 2026-11-01): push ebp; mov ebp,esp; sub esp,0x1ac; push edi; mov edi,ecx ...
   pops edi/esi/ebx, mov esp,ebp; pop ebp; RET (plain ret, no stack argument), the only register input is ecx = the car SCRIPT. So a __fastcall (ecx, edx) pointer with a dummy
   edx matches it (the same way the hook calls other thiscall routines, klfreeclimb.c KLFC_CALL). It lies in a CEG-hashed range: it is CALLED, never patched. Returns 1 = ran, 0 = fault. */
static int kcr_cb_call(DWORD script)
{
    __try {
        KLFC_CALL(void (__fastcall *)(DWORD, DWORD), 0x0081b6f0u)(script, 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
    return 1;
}

static void kcr_cb_note(int why, DWORD now, DWORD st)
{
    static const char *nm[] = { "go", "off", "not a client", "already done for this load", "session state past in-play", "waiting for the cover list", "waiting for cars", "waiting for a stable count", "gave up (no list / no cars)" };
    if (why == kcr.cb_last) return;
    kcr.cb_last = why;
    if (why == KCR_CB_OFF || why == KCR_CB_NOT_CLIENT) return;       /* silent: every host / offline tick would say it */
    klog("coverring: clientbuild t+%lums state=%lx: %s", (unsigned long)(now - kcr.t_load), (unsigned long)st, nm[why]);
}

/* called every tick from kcr_tick (game thread, inside its __try). Does nothing unless ClientBuild=1, this is an online CLIENT and the slot is listed. */
static void kcr_cb_step(DWORD gd, DWORD st, DWORD now)
{
    DWORD sm, role = 0, mode = 0, L, rb, rn, pb, pe, cnt = 0, i; int list_ok, why, map_ok = 0, ran = 0, ok_n = 0;
    char scene[200], key[120];
    if (kcr.cb_bad || kcr.cb_done) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !KLH_SM_VT_OK(klh_rd32(sm)) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !kcr_cb_role_ok(role, mode, kcr.cb_host)) return;    /* host / offline: nothing, no log */
    key[0] = 0;
    if (klh_scene(scene, sizeof scene) && klh_level_key(scene, key, sizeof key)) map_ok = kcr_cb_map_listed(kcr.cb_maps, key);
    if (!map_ok) return;
    list_ok = kcvd_read_list(gd, &L, &rb, &rn, &pb, &pe) && kcr_count_sane(cnt = klh_rd32(L + 0x68)) && cnt > 0;
    if (list_ok && cnt != kcr.cb_cnt) { kcr.cb_cnt = cnt; kcr.cb_cnt_at = now; }
    if (list_ok && (!kcr.t_scan || now - kcr.t_scan >= 2000u)) kcr_scan();
    why = kcr_cb_gate(1, 1, map_ok, kcr.cb_done, st, list_ok, list_ok ? kcr.ncars : 0, (unsigned long)(now - kcr.t_load), (unsigned long)(now - kcr.cb_cnt_at));
    kcr_cb_note(why, now, st);
    if (why == KCR_CB_GAVE_UP || why == KCR_CB_STATE) { kcr.cb_done = 1; return; }
    if (why != KCR_CB_GO) return;
    {   /* review fix (c): the writer reserves 8 indices BEFORE its physics probe ([[0xdd2640]+0xac], 0x81b983..) and needs gamedata [0xdd265c] (0x713130): wait until both exist, else a fault would leave reserved-but-unfilled spares */
        DWORD w = klh_rd32((DWORD_PTR)KLH_VA(0x00dd2640));
        if (!klh_rd32((DWORD_PTR)KLH_VA(0x00dd265c)) || !w || !klh_rd32(w + 0xac)) { kcr_cb_note(KCR_CB_WAIT_LIST, now, st); return; }
    }
    kcr_scan();      /* fresh, in entity-table order */
    kcr.cb_done = 1;
    klog("coverring: clientbuild GO t+%lums slot '%s' state=%lx L=%08lx real-count[+68]=%lu cars=%lu (entity-table order; GUESS: equals the host's order - compare with the host's 'coverring: car #' lines)",
         (unsigned long)(now - kcr.t_load), key, (unsigned long)st, (unsigned long)L, (unsigned long)cnt, (unsigned long)kcr.ncars);
    for (i = 0; i < kcr.ncars; i++) {
        DWORD car = kcr.c[i].car, s = klh_rd32(car + 0x968), n = 0, d = 0, r = 0, c0, c1, idx[8], k, shown; char nm[80], ix[120]; int l = 0, scr_ok = kcvd_ptr_ok(s) && kcr_script_matches(car, klh_rd32(s + 0x40));
        kcvd_name(car, nm, sizeof nm);
        if (scr_ok) { d = kcr_rd8(s + 0x1e8); r = kcr_rd8(s + 0x1e9); }
        if (!kcr_cb_car_ok(scr_ok, d, r)) {
            klog("coverring: clientbuild car #%lu slot %lu '%s' car=%08lx script=%08lx %s done=%lu rsv=%lu - SKIPPED", (unsigned long)i, (unsigned long)kcr.c[i].slot, nm, (unsigned long)car,
                 (unsigned long)s, scr_ok ? "readable" : "UNREADABLE", (unsigned long)d, (unsigned long)r);
            continue;
        }
        ok_n++;
        c0 = klh_rd32(L + 0x68);
        if (!kcr_cb_call(s)) { kcr.cb_bad = 1; klog("coverring: clientbuild car #%lu '%s' script=%08lx: FAULT in 0x81b6f0 - ClientBuild off for the rest of the run", (unsigned long)i, nm, (unsigned long)s); return; }
        ran++;
        c1 = klh_rd32(L + 0x68); n = klh_rd32(s + 0x1c4);
        memset(idx, 0xff, sizeof idx);
        for (k = 0; k < 8; k++) idx[k] = klh_rd32(s + 0x1c8 + k * 4);
        shown = kcr_idx_shown(n); ix[0] = 0;
        for (k = 0; k < shown && l < (int)sizeof ix - 12; k++) l += _snprintf(ix + l, sizeof ix - l - 1, "%s%ld", k ? "," : "", (long)idx[k]);
        ix[sizeof ix - 1] = 0;
        klog("coverring: clientbuild car #%lu slot %lu '%s' car=%08lx script=%08lx called 0x81b6f0: count %lu -> %lu (delta %ld) n[+1c4]=%lu done[+1e8]=%lu rsv[+1e9]=%lu idx[+1c8]=[%s]",
             (unsigned long)i, (unsigned long)kcr.c[i].slot, nm, (unsigned long)car, (unsigned long)s, (unsigned long)c0, (unsigned long)c1, (long)c1 - (long)c0, (unsigned long)n,
             (unsigned long)kcr_rd8(s + 0x1e8), (unsigned long)kcr_rd8(s + 0x1e9), ix);
    }
    klog("coverring: clientbuild END cars=%lu eligible=%d called=%d real-count %lu -> %lu", (unsigned long)kcr.ncars, ok_n, ran, (unsigned long)cnt, (unsigned long)klh_rd32(L + 0x68));
}

static void kcr_tick(int game_thread)
{
    DWORD now, gd, st, L, rb, rn, pb, pe, cnt, sig, ran;
    if ((!kcr.on && !kcr.cb) || !game_thread || kcr.bad) return;
    now = GetTickCount();
    __try {
        if (!kcvd_state(&gd, &st)) return;
        if (gd != kcr.gd || (st == 0x16 && kcr.st != 0x16)) kcr_rearm(gd, st, now);
        if (st != kcr.st) {
            if (kcr.on) klog("coverring: state t+%lums %lx -> %lx", (unsigned long)(now - kcr.t_load), (unsigned long)kcr.st, (unsigned long)st);
            kcr.st = st;
        }
        if (kcr.cb) kcr_cb_step(gd, st, now);
        if (!kcr.on) { return; }
        if (!kcr_due((unsigned long)(now - kcr.t_load), kcr.t_poll ? (unsigned long)(now - kcr.t_poll) : 0xfffffffful)) return;
        kcr.t_poll = now;
        if (!kcvd_read_list(gd, &L, &rb, &rn, &pb, &pe)) return;               /* list not built yet: try again next tick */
        cnt = klh_rd32(L + 0x68);
        if (!kcr_count_sane(cnt)) return;
        if (!kcr.have || cnt != kcr.cnt || !kcr.t_scan || now - kcr.t_scan >= KCR_SLOW_MS) kcr_scan();
        sig = kcr_cars_sig(&ran);
        if (!kcr_changed(kcr.have, kcr.cnt, cnt, kcr.sig, sig)) return;
        if (kcr.nenum >= KCR_MAX_ENUM) { if (kcr.nenum == KCR_MAX_ENUM) { klog("coverring: poll budget (%d) used up for this load", KCR_MAX_ENUM); kcr.nenum++; } kcr.cnt = cnt; kcr.sig = sig; kcr.have = 1; return; }
        klog("coverring: poll t+%lums state=%lx L=%08lx real-count[+68]=%lu%s points(vec %lu) cars=%lu ring-ran=%lu (cars with done or reserved set)",
             (unsigned long)(now - kcr.t_load), (unsigned long)st, (unsigned long)L, (unsigned long)cnt,
             kcr.have ? (cnt != kcr.cnt ? " CHANGED" : " (cars changed)") : " (first sample of this load)",
             (unsigned long)((pe >= pb && pe - pb < 0x4000000u) ? (pe - pb) / 0x7c : 0), (unsigned long)kcr.ncars, (unsigned long)ran);
        if (kcr.have && cnt != kcr.cnt) klog("coverring: poll count %lu -> %lu (delta %ld)", (unsigned long)kcr.cnt, (unsigned long)cnt, (long)cnt - (long)kcr.cnt);
        kcr_car_lines(now);
        kcr.nenum++; kcr.L = L; kcr.cnt = cnt; kcr.sig = sig; kcr.have = 1;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        kcr.bad = 1;
        klog("coverring: exception in the poll - probe off");
    }
}

static void kcr_init(void)
{
#ifdef KLHOOK_TEST
    int def = 1;
#else
    int def = 0;
#endif
    memset(&kcr, 0, sizeof kcr);
    kcr.on = GetPrivateProfileIntA("CoverRing", "Enable", def, klh_ini) != 0;
    kcr.callers = GetPrivateProfileIntA("CoverRing", "Callers", def, klh_ini) != 0;
    kcr.cb = GetPrivateProfileIntA("CoverRing", "ClientBuild", 0, klh_ini) != 0;      /* (recommended off: experimental, enable only for the CR2 bench) default 0 in TEST and SHIP */
    GetPrivateProfileStringA("CoverRing", "ClientBuildMaps", "F01,F03", kcr.cb_maps, sizeof kcr.cb_maps, klh_ini);      /* slots (DM01 = F01, DM03 = F03) */
    kcr.cb_host = GetPrivateProfileIntA("CoverRing", "ClientBuildHost", 0, klh_ini) != 0;      /* (recommended off: experimental, CR3 bench) the HOST prebuilds too */
    kcr.cb_last = -1;
    if (kcr.cb) klog("coverring: ClientBuild=1 (experimental, recommended off; online CLIENT%s, once per load, slots '%s'): this seat calls the ring writer 0x81b6f0 for its cars at load, table order",
                     kcr.cb_host ? " and HOST (ClientBuildHost=1)" : " only", kcr.cb_maps);
    if (!kcr.on) return;
    klog("coverring: on (READ ONLY, LOG ONLY, recommended on for test runs, off for players): [L+0x68] poll + ZHavokCar script ring state, Callers=%d (recommended on for test runs, off for players)", kcr.callers);
    if (kcr.callers) {
        static const struct { const char *nm; DWORD va; } sl[] = {
            { "ZHavokCarScript slot 12 (stream reader 0x622470)", 0xbd1694u + 12 * 4 }, { "ZHavokCarIdleGoal slot 2 (0x564700)", 0xbd16dcu + 2 * 4 },
            { "ZVehicleMoveBehaviour slot 3 (0x7cb060)", 0xbcd740u + 3 * 4 }, { "ZVehicleFireBehaviour slot 3", 0xbcd9c8u + 3 * 4 },
            { "ZVehicleFireOnRoadBehaviour slot 3", 0xbcdaa0u + 3 * 4 }, { "ZVehicleSpecialMoveBehaviour slot 3", 0xbcdb78u + 3 * 4 },
            { "ZAIInputRoadComponent slot 13 (0x6df8c0)", 0xbcb9f8u + 13 * 4 },
        };
        int i;
        for (i = 0; i < (int)(sizeof sl / sizeof sl[0]); i++)
            klog("coverring: callers: %s entry %08lx %s - %s", sl[i].nm, (unsigned long)sl[i].va, klh_is_hashed(sl[i].va, 4) ? "inside a HASHED range" : "not hashed",
                 klh_is_hashed(sl[i].va, 4) ? "trampoline SKIPPED (vtable swap ends the process); poll only" : "trampoline NOT implemented (not needed: poll only)");
        klog("coverring: callers: ZVehicleExitBehaviour slot 2 (0x5c51b0): vtable address not resolved by the brief, SKIPPED");
    }
}

#endif
