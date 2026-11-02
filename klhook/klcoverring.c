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
 * 4. CLIENTREWRITE (CR6, 2026-11-02): see kcr_rw_step. Client only, after ClientBuild, per prebuilt car on a state change. NOT RUN LIVE.
 * ini: [CoverRing] Enable=1 in the TEST build / 0 in SHIP (recommended on for test runs, off for players)
 *                  Callers=1 TEST / 0 SHIP (recommended on for test runs, off for players): only logs that the slot swaps are skipped (hashed vtables)
 *                  ClientBuild=0 by default (recommended on, host and every client together: CR3 11-01, CR5 + SN1 11-02 PASS)  ClientBuildMaps=F01,F03 (DM01 / DM03 slots)
 *                  ClientBuildHost=0 by default (recommended on, with ClientBuild): the HOST prebuilds at load too. CR1_DM01 showed the client never
 *                  runs the writer and the host runs it per car on ACTIVATION (order 871, 737+792, 906 = not table order), so client-only table order cannot match;
 *                  both seats in table order at load can, IF the host's later activation reuses rsv=1 indices (GUESS, see klcoverring_logic.h).
 * LINES (prefix 'coverring:'): on / callers / load / state / poll / car / scan / clientbuild.
 */
#ifndef KLCOVERRING_C
#define KLCOVERRING_C

#include <float.h>      /* _fpreset (review D4) */
#include "klcoverring_logic.h"

#define KCR_NCAR 64
static struct {
    int on, callers, bad, have, nenum;
    int rw, rw_bad, npre; DWORD rw_t;                                                         /* ClientRewrite (CR6) */
    int rs, rs_bad, rs_mis, rs_seq, rs_srcset; DWORD rs_t, rs_nrx, rs_nap, rs_toldrx, rs_nchg; unsigned long rs_src;   /* ClientRingSync (CR8, klcoverring_sync.c); rs_bad 1 = fault (run), 2 = mismatches (this load) */
    struct { DWORD car, script, s8c0, sa28, tries, last; } pre[KCR_NCAR];
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

static int kcr_cb_points(const char *who, unsigned long i, const DWORD *idx, DWORD n, DWORD pb, DWORD npts);

static void kcr_car_lines(DWORD now, DWORD pb, DWORD npts)
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
        if (n && d && npts) kcr_cb_points("poll", i, idx, n, pb, npts);      /* review D2: filled vs spare points of a built ring (host activation rebuilds included) */
    }
}

static void kcr_rearm(DWORD gd, DWORD st, DWORD now)
{
    memset(&kcr.c, 0, sizeof kcr.c);
    kcr.npre = 0; kcr.rw_t = 0; memset(&kcr.pre, 0, sizeof kcr.pre);
    kcr.rs_t = 0; kcr.rs_mis = 0; kcr.rs_nrx = 0; kcr.rs_nap = 0; kcr.rs_toldrx = 0; kcr.rs_nchg = 0; kcr.rs_srcset = 0; kcr.rs_src = 0;
    if (kcr.rs_bad == 2) kcr.rs_bad = 0;                                                     /* mismatches end with the load; a fault (1) stays off for the run */
    kcr.cb_done = 0; kcr.cb_last = -1; kcr.cb_cnt = 0xfffffffful; kcr.cb_cnt_at = now;
    kcr.have = 0; kcr.nenum = 0; kcr.ncars = 0; kcr.gd = gd; kcr.st = st; kcr.t_load = now; kcr.t_poll = 0; kcr.t_scan = 0; kcr.L = 0; kcr.cnt = 0; kcr.sig = 0;
    if (kcr.on) klog("coverring: load gd=%08lx state=%lx (poll every tick for %lu s, then every %lu s)", (unsigned long)gd, (unsigned long)st, KCR_FAST_MS / 1000, KCR_SLOW_MS / 1000);
}

/* ClientBuild (CR2): ONE call of the writer on the game thread. 0x81b6f0 (re/dm_car_cover_1101.md; dasm 2026-11-01): push ebp; mov ebp,esp; sub esp,0x1ac; push edi; mov edi,ecx ...
   pops edi/esi/ebx, mov esp,ebp; pop ebp; RET (plain ret, no stack argument), the only register input is ecx = the car SCRIPT. So a __fastcall (ecx, edx) pointer with a dummy
   edx matches it (the same way the hook calls other thiscall routines, klfreeclimb.c KLFC_CALL). It lies in a CEG-hashed range: it is CALLED, never patched. Returns 1 = ran, 0 = fault. */
static int kcr_cb_call(DWORD script)
{
    unsigned int cw = _control87(0, 0);
    __try {
        KLFC_CALL(void (__fastcall *)(DWORD, DWORD), 0x0081b6f0u)(script, 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        /* review D4: the writer runs x87 code (fld / fstp from 0x81b771); a fault mid-way can leave values on the FPU stack. _fpreset clears the stack but also resets
           the control word to the CRT default; the game thread (D3D9) may run another precision, so put the game's word back (review 11-02) */
        _fpreset();
        _control87(cw, _MCW_EM | _MCW_RC | _MCW_PC | _MCW_IC);
        return 0;
    }
    return 1;
}

/* review D2: after a call, read the flags [pt+0x68] and position (+0x28) of the car's indices from the points vector (begin pb, stride 0x7c, npts entries) and log them, so
   the bench can see filled (0x200) vs spare (0x400 only) points on both seats. Returns the number of usable points. */
static int kcr_cb_points(const char *who, unsigned long i, const DWORD *idx, DWORD n, DWORD pb, DWORD npts)
{
    char b[400]; int l = 0, good = 0; DWORD k;
    b[0] = 0;
    for (k = 0; k < n && k < 8; k++) {
        DWORD fl = 0; float p[3] = { 0, 0, 0 };
        if (idx[k] < npts && klh_rd(pb + idx[k] * 0x7c + 0x68, &fl, 4) && klh_rd(pb + idx[k] * 0x7c + 0x28, p, 12)) {
            good += kcr_pt_usable(fl);
            if (l < (int)sizeof b - 48) l += _snprintf(b + l, sizeof b - l - 1, " %lu:%03lx(%.0f,%.0f,%.0f)%s", (unsigned long)idx[k], (unsigned long)fl, p[0], p[1], p[2], kcr_pt_usable(fl) ? "" : "SPARE");
        } else if (l < (int)sizeof b - 24) l += _snprintf(b + l, sizeof b - l - 1, " %lu:UNREADABLE", (unsigned long)idx[k]);
    }
    b[sizeof b - 1] = 0;
    klog("coverring: %s car #%lu points usable %d/%lu:%s", who, i, good, (unsigned long)(n < 8 ? n : 8), b);
    return good;
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
    DWORD sm, role = 0, mode = 0, L, rb, rn, pb = 0, pe = 0, cnt = 0, i, npts, elig; int list_ok, why, map_ok = 0, ran = 0, ok_n = 0, usable = 0, checked = 0;
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
    npts = (pe >= pb && pe - pb < 0x4000000u) ? (pe - pb) / 0x7c : 0;
    for (i = 0, elig = 0; i < kcr.ncars; i++) {      /* review D3: count eligible cars first; refuse if their 8 indices each do not fit the points vector */
        DWORD s = klh_rd32(kcr.c[i].car + 0x968); int ok = kcvd_ptr_ok(s) && kcr_script_matches(kcr.c[i].car, klh_rd32(s + 0x40));
        if (kcr_cb_car_ok(ok, ok ? kcr_rd8(s + 0x1e8) : 1, ok ? kcr_rd8(s + 0x1e9) : 1)) elig++;
    }
    if (!kcr_cb_fits(cnt, elig, npts)) {
        klog("coverring: clientbuild REFUSED: capacity - count %lu + 8 x %lu eligible cars > points vector %lu (0x558350 has no bound check)", (unsigned long)cnt, (unsigned long)elig, (unsigned long)npts);
        return;
    }
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
        if (!kcr_cb_call(s)) {      /* review D4: say what is left half-done; the cars after this one stay unreserved, so this seat's later indices no longer match the other seat */
            kcr.cb_bad = 1;
            klog("coverring: clientbuild car #%lu '%s' script=%08lx: FAULT in 0x81b6f0 (FPU reset) - half state: count %lu -> %lu n[+1c4]=%lu rsv[+1e9]=%lu; %lu later car(s) NOT reserved, "
                 "indices DIVERGE from the other seat from here; ClientBuild off for the rest of the run", (unsigned long)i, nm, (unsigned long)s, (unsigned long)c0,
                 (unsigned long)klh_rd32(L + 0x68), (unsigned long)klh_rd32(s + 0x1c4), (unsigned long)kcr_rd8(s + 0x1e9), (unsigned long)(elig > (DWORD)ok_n ? elig - (DWORD)ok_n : 0));
            return;
        }
        ran++;
        if (kcr.npre < KCR_NCAR) {      /* CR6: remember the prebuilt car and its state as seen now; a later change is the GUESSed activation marker */
            kcr.pre[kcr.npre].car = car; kcr.pre[kcr.npre].script = s; kcr.pre[kcr.npre].s8c0 = klh_rd32(car + 0x8c0); kcr.pre[kcr.npre].sa28 = klh_rd32(car + 0xa28);
            kcr.pre[kcr.npre].tries = 0; kcr.pre[kcr.npre].last = 0; kcr.npre++;
        }
        c1 = klh_rd32(L + 0x68); n = klh_rd32(s + 0x1c4);
        memset(idx, 0xff, sizeof idx);
        for (k = 0; k < 8; k++) idx[k] = klh_rd32(s + 0x1c8 + k * 4);
        shown = kcr_idx_shown(n); ix[0] = 0;
        for (k = 0; k < shown && l < (int)sizeof ix - 12; k++) l += _snprintf(ix + l, sizeof ix - l - 1, "%s%ld", k ? "," : "", (long)idx[k]);
        ix[sizeof ix - 1] = 0;
        klog("coverring: clientbuild car #%lu slot %lu '%s' car=%08lx script=%08lx called 0x81b6f0: count %lu -> %lu (delta %ld) n[+1c4]=%lu done[+1e8]=%lu rsv[+1e9]=%lu idx[+1c8]=[%s]",
             (unsigned long)i, (unsigned long)kcr.c[i].slot, nm, (unsigned long)car, (unsigned long)s, (unsigned long)c0, (unsigned long)c1, (long)c1 - (long)c0, (unsigned long)n,
             (unsigned long)kcr_rd8(s + 0x1e8), (unsigned long)kcr_rd8(s + 0x1e9), ix);
        usable += kcr_cb_points("clientbuild", i, idx, n, pb, npts);
        checked += (int)(n < 8 ? n : 8);
    }
    klog("coverring: clientbuild END cars=%lu eligible=%d called=%d real-count %lu -> %lu usable points %d of %d", (unsigned long)kcr.ncars, ok_n, ran, (unsigned long)cnt,
         (unsigned long)klh_rd32(L + 0x68), usable, checked);
}

/* ClientRewrite (CR6): after ClientBuild, when a prebuilt car's state changes (GUESS: [car+0x8c0] / [car+0xa28] as the client sees them mark the activation that makes the HOST
   run 0x8d6210 -> 0x81b6f0), run the writer again on this seat. The writer returns at once when done[+1e8] != 0, and the host reaches it with done == 0 (CR1: done 1 -> 0 -> 1), so
   done is cleared here first (GUESS: the host's clearing site is not found). rsv[+1e9] == 1 makes it skip the 8 index reservations (dasm 0x81b709) and only rewrite the points'
   positions/flags (physics probe + 0x9015d0 per point). Checked after each call: count and the 8 indices must be unchanged, else the feature turns itself off. A fault restores done=1.
   The script is heap data (not hashed): a plain byte store inside kcr_tick's __try. */
static void kcr_rw_step(DWORD gd, DWORD st, DWORD now)
{
    DWORD sm, role = 0, mode = 0, L, rb, rn, pb = 0, pe = 0, npts, i;
    if (!kcr.rw || kcr.rw_bad || !kcr.cb_done || kcr.cb_bad || !kcr.npre) return;
    if (kcr.rw_t && now - kcr.rw_t < KCR_RW_SCAN_MS) return;
    kcr.rw_t = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !KLH_SM_VT_OK(klh_rd32(sm)) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4)) return;
    if (!kcr_rw_gate(1, kcr_cb_role_ok(role, mode, 0), 1, st)) return;       /* client only (host = 0 here on purpose) */
    if (!kcvd_read_list(gd, &L, &rb, &rn, &pb, &pe)) return;
    npts = (pe >= pb && pe - pb < 0x4000000u) ? (pe - pb) / 0x7c : 0;
    for (i = 0; i < (DWORD)kcr.npre; i++) {
        DWORD car = kcr.pre[i].car, s = kcr.pre[i].script, d, r, n, idx[8], idx2[8], k, c0, c1, spares = 0, since, v8c0, va28; int why, sc, same = 1, fault, oob = 0;
        if (!kcvd_ptr_ok(car) || !kcvd_ptr_ok(s) || klh_rd32(car + 0x968) != s || !kcr_script_matches(car, klh_rd32(s + 0x40))) continue;   /* car gone / script replaced: never touch it */
        d = kcr_rd8(s + 0x1e8); r = kcr_rd8(s + 0x1e9); n = klh_rd32(s + 0x1c4);
        v8c0 = klh_rd32(car + 0x8c0); va28 = klh_rd32(car + 0xa28);
        sc = v8c0 != kcr.pre[i].s8c0 || va28 != kcr.pre[i].sa28;
        for (k = 0; k < 8; k++) idx[k] = klh_rd32(s + 0x1c8 + k * 4);
        for (k = 0; k < n && k < 8; k++) {
            DWORD fl = 0;
            if (idx[k] >= npts) oob = 1;
            if (idx[k] >= npts || !klh_rd(pb + idx[k] * 0x7c + 0x68, &fl, 4) || !kcr_pt_usable(fl)) spares++;
        }
        if (oob) {                                  /* review 11-02: the writer would write pb + idx*0x7c past the list: never call it for this car */
            if (kcr.pre[i].tries < KCR_RW_MAXTRY) klog("coverring: rewrite car #%lu skipped: an index is past the list end (%lu points) - car left as built", (unsigned long)i, (unsigned long)npts);
            kcr.pre[i].tries = KCR_RW_MAXTRY;
            continue;
        }
        since = kcr.pre[i].tries ? now - kcr.pre[i].last : 0xfffffffful;
        why = kcr_rw_trigger(sc, spares, kcr.pre[i].tries, since);
        if (why == KCR_RW_NONE || !kcr_rw_pre_ok(d, r, n)) continue;
        kcr.pre[i].tries++; kcr.pre[i].last = now;
        klog("coverring: rewrite car #%lu trigger: [car+8c0] %08lx -> %08lx, [car+a28] %08lx -> %08lx, spares %lu", (unsigned long)i, (unsigned long)kcr.pre[i].s8c0,
             (unsigned long)v8c0, (unsigned long)kcr.pre[i].sa28, (unsigned long)va28, (unsigned long)spares);
        c0 = klh_rd32(L + 0x68);
        *(volatile BYTE *)(DWORD_PTR)(s + 0x1e8) = 0;
        fault = !kcr_cb_call(s);
        if (fault) { *(volatile BYTE *)(DWORD_PTR)(s + 0x1e8) = 1; kcr.rw_bad = 1; }
        c1 = klh_rd32(L + 0x68);
        for (k = 0; k < 8; k++) { idx2[k] = klh_rd32(s + 0x1c8 + k * 4); if (idx2[k] != idx[k]) same = 0; }
        kcr.pre[i].s8c0 = klh_rd32(car + 0x8c0); kcr.pre[i].sa28 = klh_rd32(car + 0xa28);
        klog("coverring: rewrite car #%lu script=%08lx %s try %lu: %s, spares before %lu, count %lu -> %lu, indices %s, done=%lu rsv=%lu",
             (unsigned long)i, (unsigned long)s, why == KCR_RW_STATE ? "state changed" : "spares remain", (unsigned long)kcr.pre[i].tries,
             fault ? "FAULT in 0x81b6f0 (FPU reset, done restored to 1)" : "called 0x81b6f0", (unsigned long)spares, (unsigned long)c0, (unsigned long)c1,
             same ? "unchanged" : "CHANGED", (unsigned long)kcr_rd8(s + 0x1e8), (unsigned long)kcr_rd8(s + 0x1e9));
        if (!fault) kcr_cb_points("rewrite", i, idx2, n, pb, npts);
        if (!fault && !kcr_rw_after_ok(c0, c1, same)) {
            kcr.rw_bad = 1;
            klog("coverring: rewrite WARN car #%lu: the writer reserved or moved indices (rsv semantics not as dasm'd) - ClientRewrite off for the rest of the run", (unsigned long)i);
        }
        if (kcr.rw_bad) return;
    }
}

static void kcr_tick(int game_thread)
{
    DWORD now, gd, st, L, rb, rn, pb, pe, cnt, sig, ran;
    if ((!kcr.on && !kcr.cb && !kcr.rw && !kcr.rs) || !game_thread || kcr.bad) return;
    now = GetTickCount();
    __try {
        if (!kcvd_state(&gd, &st)) return;
        if (gd != kcr.gd || (st == 0x16 && kcr.st != 0x16)) kcr_rearm(gd, st, now);
        if (st != kcr.st) {
            if (kcr.on) klog("coverring: state t+%lums %lx -> %lx", (unsigned long)(now - kcr.t_load), (unsigned long)kcr.st, (unsigned long)st);
            kcr.st = st;
        }
        if (kcr.cb) kcr_cb_step(gd, st, now);
        if (kcr.rw) kcr_rw_step(gd, st, now);
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
        kcr_car_lines(now, pb, (pe >= pb && pe - pb < 0x4000000u) ? (pe - pb) / 0x7c : 0);
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
    kcr.cb = GetPrivateProfileIntA("CoverRing", "ClientBuild", 0, klh_ini) != 0;      /* (recommended on, host and every client together; CR3/CR5/SN1 PASS) default 0 when the key is missing */
    GetPrivateProfileStringA("CoverRing", "ClientBuildMaps", "F01,F03", kcr.cb_maps, sizeof kcr.cb_maps, klh_ini);      /* slots (DM01 = F01, DM03 = F03) */
    kcr.cb_host = GetPrivateProfileIntA("CoverRing", "ClientBuildHost", 0, klh_ini) != 0;      /* (recommended on, with ClientBuild) the HOST prebuilds too */
    kcr.rw = GetPrivateProfileIntA("CoverRing", "ClientRewrite", 0, klh_ini) != 0;      /* (recommended off until benched) needs ClientBuild=1 */
    kcr.rs = GetPrivateProfileIntA("CoverRing", "ClientRingSync", 0, klh_ini) != 0;      /* (recommended off until benched) needs ClientBuild=1 on both seats; CR8 */
    kcr.cb_last = -1;
    if (kcr.rs) klog("coverring: ClientRingSync=1 (recommended off until benched): the HOST sends its cars' cover points (KLSYR, UDP 27415), an online CLIENT copies a point only where the host's is usable and its own is a spare; needs ClientBuild=1");
    if (kcr.rw) klog("coverring: ClientRewrite=1 (recommended off until benched): an online CLIENT re-runs 0x81b6f0 (done cleared first, rsv=1 keeps the indices) for a prebuilt car whose state changes; needs ClientBuild=1");
    if (kcr.cb) klog("coverring: ClientBuild=1 (recommended on, host and every client together; online CLIENT%s, once per load, slots '%s'): this seat calls the ring writer 0x81b6f0 for its cars at load, table order",
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
