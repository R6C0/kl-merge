/*
 * klroundkeep.c - [Lobby] KeepRound: an online Fragile Alliance round must not be cut short just because the human crew is small
 * (a lone host with AI heisters). Plus [Lobby] ExtraSeats (TEST only): seats for players 9..12. Part of KLHook (included by klhook.c after
 * klbotfill.c, SHIP and TEST alike); the SHIP part is a VTABLE route (a private copy of the rules object's vtable, the pattern of kllobby.c / kllobbyopt.c).
 * 2026-10-25, built, NOT run live.
 *
 * WHAT THE EXE SHOWS (kl2.exe 0490, read statically 2026-10-25; CERTAIN unless marked; re\round_end_online.md has the whole reading):
 *   The Sv rules' per-frame tick (slot 211 chain -> 0x80ad60, the function whose tail also raises the session END request that kllobby.c Solo=1 drops)
 *   holds TWO early cuts of the round clock for game type != 2 (not Cops & Robbers). Records = [rules+8] (0x74 bytes each, [rules+0x14] of them,
 *   free flags [rules+0xc]); a record exists only for a HUMAN connection, an AI heister has none:
 *   (A) 0x80b1c0..0x80b208: if slot 168 (0x641750 = number of records whose slot-114 status (0x625be0) has neither bit 0x10 nor 0x40 = heisters
 *       "still in play") is < 2 and [sm+0xb8] > 1 (always), then if [rules+0x4c] (time left) is above 70.0 (0xb20cbc), CUT: slot 42 (0x4c3c10) with 70.0.
 *       -> ONE human heister (a lone host, AI filling the rest) always had the round cut to 70 s at its first frame. That is the 70.00 left
 *          at the start of every live round and the 83 s round (70 s + the 13 s end sequence). Not the lobby time, not the number of humans connected.
 *   (B) 0x80b18c..0x80b1be: if [rules+0x200] (END timer) > 11.0 and 0x86f520 is true (state 0x19 and EVERY in-use record of type 0 has status bit 4
 *       set, or has its player's police byte [p+0x2723] / [p+0x2729] set; also true when no record is in use) then slot 193 (0x8a6140, sets
 *       [rules+0x200] while state 0x19) with 10.0: the "all heisters down/out" end, 10 s later the round is over. AI heisters are not records,
 *       so the round ends as soon as the last HUMAN is down or out, however many AI heisters still stand.
 *   The returns of these two calls are the only places this module acts: 0x80b208 (slot 42) and 0x80b1c0 (slot 193). Every other caller is passed through.
 * WHAT IT DOES ([Lobby] KeepRound, default 0 "(recommended on) for a solo host with AI heisters"):
 *   The Sv rules object (vtable 0xbd2eb4) gets a PRIVATE vtable copy whose slots 42 and 193 are ours (one heap pointer write, SHIP-safe). The wrapper
 *   returns without calling the stock function when the caller is one of the two return addresses above and the toggle says so:
 *     KeepRound=1: only while at most one human is connected (kllb_connected) or [Bots] OnlineFill planned AI heisters (klbf_fill > 0)
 *     KeepRound=2: always (bench / owner decides; a round with two idle humans)
 *   The round then ends by its clock (the lobby heist time + 10 s), by the escape, or when the stock end tests of the other kind fire.
 *   klbot.c / klnet.c accept the private vtable (KLH_RULES_SV_OK).
 * AI AS CREW (what is and is not done here):
 *   done: the round no longer ends because the AI heisters are not "crew" (the cuts above). NOT done (needs code, TEST-only at best): a record per AI
 *   heister in [rules+8] (so slot 168 / 0x86f520 / the HUD crew list / the scoreboard count them), see re\round_end_online.md for the design and why not.
 * TEST (KLHOOK_TEST): every cut call (slot 42 / 193, any caller) is logged with the caller, the argument, the clock and a dump of the records
 *   ('roundkeep-test:' lines: type, status, the player's flags, slot 168, 0x86f520), and the same dump at the session state 0x1f (round over): it names
 *   WHICH test fired. The dump also names every record's seat type.
 * [Lobby] ExtraSeats=1 (TEST only, default 0, GUESS): the level has 8 type-2 (heister) and 8 type-3 (police) ZFFPlayer seats, 0x54cab0 gives a joiner the
 *   first free seat whose [player+0x273c] equals the wanted type and returns -1 for a 9th heister. With a target [sm+0xb9] above 8 (kllobbyopt.c PlayersMax),
 *   `target - 8` free type-3 seats (from the END of the table) get their type byte set to 2, so the extra players start as heisters on the police seats.
 *   GUESS: their spawn place is the seat entity's own (not FA_START); the cops then have fewer seats for the dead heisters.
 *
 * KLHook.ini
 *   [Lobby]
 *   KeepRound=0     0 = stock. 1 = no early cut while at most one human is connected or AI heisters are planned (recommended on for a solo host). 2 = never cut.
 *   ExtraSeats=0    TEST build only: seats for players 9..12 (see above).
 */
#ifndef KLROUNDKEEP_C
#define KLROUNDKEEP_C

#define KLRK_SLOTS 260
static int klrk_keep, klrk_seats;
static DWORD klrk_vt[1 + KLRK_SLOTS];                          /* [0] = RTTI locator, [1..] = slots of 0xbd2eb4 */
static void (__fastcall *klrk_real42)(void *, void *, float);
static void (__fastcall *klrk_real193)(void *, void *, float);
static LONG klrk_n, klrk_dropped;

static void klrk_init(void)
{
    klrk_keep = GetPrivateProfileIntA("Lobby", "KeepRound", 0, klh_ini);
    if (klrk_keep < 0 || klrk_keep > 2) klrk_keep = 0;
#ifdef KLHOOK_TEST
    klrk_seats = GetPrivateProfileIntA("Lobby", "ExtraSeats", 0, klh_ini) != 0;
#endif
    if (klrk_keep) klog("roundkeep: KeepRound=%d - the online rules' early round cuts (fewer than 2 heisters in play -> 70 s; all humans out -> 10 s) are skipped %s", klrk_keep,
                        klrk_keep == 2 ? "always" : "while at most one human is connected or AI heisters are planned");
    if (klrk_seats) klog("roundkeep: ExtraSeats=1 (TEST, GUESS): type-3 seats are turned into heister seats for a target above 8");
}

/* is the cut to be skipped now */
static int klrk_active(DWORD sm, const char **why)
{
    int h;
    if (!klrk_keep) return 0;
    if (klrk_keep == 2) { *why = "KeepRound=2"; return 1; }
    h = sm ? kllb_connected(sm) : 99;
    if (h <= 1) { *why = "at most one human connected"; return 1; }
    if (klbf_on && klbf_fill > 0) { *why = "AI heisters planned (OnlineFill)"; return 1; }
    return 0;
}

#ifdef KLHOOK_TEST
static DWORD klrk_rules(void)
{
    DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(0x168e9e4)), r = gs ? klh_rd32(gs + 0x54) : 0;
    return (r && KLH_RULES_SV_OK(klh_rd32(r))) ? r : 0;
}
/* the end conditions of both cuts, read the way the exe reads them */
static void klrk_dump(const char *what)
{
    DWORD r = klrk_rules(), sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)), vt, arr, fr, i, n = 0; int inplay = -1, allout = -1;
    if (!r) return;
    vt = klh_rd32(r); arr = klh_rd32(r + 8); fr = klh_rd32(r + 0xc);
    klh_rd(r + 0x14, &n, 4);
    if (n > 16) n = 16;
    if (vt) inplay = (BYTE)((kllo_f0)(DWORD_PTR)klh_rd32(vt + 0x2a0))((void *)(DWORD_PTR)r, 0);
    allout = (BYTE)((kllo_f0)KLH_VA(0x86f520))((void *)(DWORD_PTR)r, 0);
    klog("roundkeep-test: %s: rules %08lx left[+4c]=%.1f played[+50]=%.1f end[+200]=%.1f phase[+1dc]=%u b204=%u | in-play(slot168)=%d allOut(0x86f520)=%d | humans connected=%d botfill=%d/%d | %lu records",
         what, (unsigned long)r, kllo_rf(r + 0x4c), kllo_rf(r + 0x50), kllo_rf(r + 0x200), (unsigned)(BYTE)klh_rd32(r + 0x1dc), (unsigned)(BYTE)klh_rd32(r + 0x204), inplay, allout,
         sm ? kllb_connected(sm) : -1, klbf_on, klbf_fill, (unsigned long)n);
    for (i = 0; i < n && arr; i++) {
        DWORD rec = arr + i * 0x74, cl, pl, st = 0; BYTE used = 0, ty = 0, pol = 0, f29 = 0, sty = 0;
        klh_rd(fr + i, &used, 1); klh_rd(rec + 0xc, &ty, 1);
        if (used) { klog("roundkeep-test:   record %lu: free", (unsigned long)i); continue; }
        if (vt) st = ((DWORD (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)klh_rd32(vt + 0x1c8))((void *)(DWORD_PTR)r, 0, i);
        cl = klh_rd32(rec); pl = cl ? klh_rd32(cl + 0x378) : 0;
        if (pl) { klh_rd(pl + 0x2723, &pol, 1); klh_rd(pl + 0x2729, &f29, 1); klh_rd(pl + 0x273c, &sty, 1); }
        klog("roundkeep-test:   record %lu: type=%u status=%08lx (bit4 %d, bit10 %d, bit40 %d) player=%08lx police[2723]=%u [2729]=%u seat type[273c]=%u",
             (unsigned long)i, ty, (unsigned long)st, (st & 4) != 0, (st & 0x10) != 0, (st & 0x40) != 0, (unsigned long)pl, pol, f29, sty);
    }
}
#else
static void klrk_dump(const char *what) { (void)what; }
#endif

static void __fastcall klrk_w42(void *self, void *edx, float a)
{
    void *ra = _ReturnAddress(); const char *why = ""; int site = ra == (void *)KLH_VA(0x80b208), drop;
    drop = site && klrk_active(klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)), &why);
#ifdef KLHOOK_TEST
    if (InterlockedIncrement(&klrk_n) <= 80) {
        char t[64]; snprintf(t, sizeof t, "CUT slot42(%.1f) from %p%s%s", a, ra, site ? " = the 'fewer than 2 heisters in play' cut (A)" : "", drop ? ", DROPPED" : "");
        klrk_dump(t);
    }
#endif
    if (drop) { if (InterlockedIncrement(&klrk_dropped) <= 20) klog("roundkeep: cut (A) 'fewer than 2 heisters in play -> %.1f s' skipped: %s", a, why); return; }
    klrk_real42(self, edx, a);
}

static void __fastcall klrk_w193(void *self, void *edx, float a)
{
    void *ra = _ReturnAddress(); const char *why = ""; int site = ra == (void *)KLH_VA(0x80b1c0), drop;
    drop = site && klrk_active(klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)), &why);
#ifdef KLHOOK_TEST
    if (InterlockedIncrement(&klrk_n) <= 80) {
        char t[72]; snprintf(t, sizeof t, "END TIMER slot193(%.1f) from %p%s%s", a, ra, site ? " = the 'all heisters out' cut (B)" : "", drop ? ", DROPPED" : "");
        klrk_dump(t);
    }
#endif
    if (drop) { if (InterlockedIncrement(&klrk_dropped) <= 20) klog("roundkeep: cut (B) 'all human heisters out -> end timer %.1f s' skipped: %s", a, why); return; }
    klrk_real193(self, edx, a);
}

#ifdef KLHOOK_TEST
/* ExtraSeats: the seat table of the session (0x6161c0(sm) -> {entries 12 bytes: +4 ZFFPlayer*, +9 used; +4 free flags; +0xc count}) */
static void klrk_extra_seats(DWORD sm)
{
    static DWORD lastT, lastn; static DWORD last; DWORD now = GetTickCount(), T, ent, fl, cnt, i, need, n2 = 0, conv = 0; int target, stt;
    if (!klrk_seats || now - last < 500) return;
    last = now;
    if (klh_rd32(sm + 0x54) != 2 || klh_rd32(sm + 0x5c) != 4) return;                      /* host, Fragile Alliance */
    stt = (int)klh_rd32(sm + 0x70);
    if (stt < 0xd || stt >= 0x19) return;
    target = (signed char)((kllo_f0)KLH_VA(0x54d140))((void *)(DWORD_PTR)sm, 0);          /* [sm+0xb9], the lobby's player count */
    if (target <= 8 || target > 12) return;
    T = ((kllo_f0)KLH_VA(0x6161c0))((void *)(DWORD_PTR)sm, 0);
    if (!T) return;
    ent = klh_rd32(T); fl = klh_rd32(T + 4); cnt = klh_rd32(T + 0xc);
    if (!ent || !fl || cnt == 0 || cnt > 32) return;
    for (i = 0; i < cnt; i++) {
        BYTE f = 0, ty = 0; DWORD pl;
        klh_rd(fl + i, &f, 1);
        if (f) continue;
        pl = klh_rd32(ent + i * 12 + 4);
        if (pl < 0x10000 || !klh_rd(pl + 0x273c, &ty, 1)) continue;
        if (ty == 2) n2++;
    }
    if (n2 >= (DWORD)target) return;
    need = (DWORD)target - n2;
    for (i = cnt; i-- > 0 && conv < need; ) {
        BYTE f = 0, ty = 0, used = 0, two = 2; DWORD pl;
        klh_rd(fl + i, &f, 1);
        if (f) continue;
        klh_rd(ent + i * 12 + 9, &used, 1);
        pl = klh_rd32(ent + i * 12 + 4);
        if (used || pl < 0x10000 || !klh_rd(pl + 0x273c, &ty, 1) || ty != 3) continue;
        if (klh_data((void *)(DWORD_PTR)(pl + 0x273c), &two, 1, "extra seats: police seat -> heister seat")) conv++;
    }
    if (conv && (T != lastT || conv != lastn)) { klog("roundkeep-test: ExtraSeats: target %d, %lu heister seats found, %lu police seats turned into heister seats (table %08lx, %lu entries)", target, (unsigned long)n2, (unsigned long)conv, (unsigned long)T, (unsigned long)cnt); lastT = T; lastn = conv; }
}
#endif

/* called from kllo_tick (every game-thread tick): wrap the Sv rules object once per level */
static void klrk_tick(void)
{
    static DWORD last; DWORD now = GetTickCount(), gs, r, vt, nv, sm;
#ifndef KLHOOK_TEST
    if (!klrk_keep) return;
#endif
    if (!klh_exe_ok || now - last < 200) return;
    last = now;
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION));
#ifdef KLHOOK_TEST
    if (sm && (klh_rd32(sm) == 0xbd1ebc || KLH_SM_VT_OK(klh_rd32(sm)))) {
        static int ls = -1; int stt = (int)klh_rd32(sm + 0x70);
        if (stt != ls) { if (stt == 0x1f) klrk_dump("session state 0x1f (round over)"); ls = stt; }
        klrk_extra_seats(sm);
    }
#endif
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(0x168e9e4))) || !(r = klh_rd32(gs + 0x54))) return;
    vt = klh_rd32(r);
    nv = (DWORD)(DWORD_PTR)&klrk_vt[1];
    if (vt == nv || vt != 0xbd2eb4) return;
    if (!klrk_vt[0]) {
        if (!klh_rd((DWORD_PTR)KLH_VA(0xbd2eb4 - 4), klrk_vt, sizeof klrk_vt)) return;
        if (klrk_vt[1 + 42] != (DWORD)(DWORD_PTR)KLH_VA(0x4c3c10) || klrk_vt[1 + 193] != (DWORD)(DWORD_PTR)KLH_VA(0x8a6140)) {
            klog("roundkeep: Sv rules slot 42 = %08lx, slot 193 = %08lx, not the known 0x4c3c10 / 0x8a6140: left alone", (unsigned long)klrk_vt[1 + 42], (unsigned long)klrk_vt[1 + 193]);
            klrk_vt[0] = 0; klrk_keep = 0; return;
        }
        klrk_real42 = (void (__fastcall *)(void *, void *, float))(DWORD_PTR)klrk_vt[1 + 42];
        klrk_real193 = (void (__fastcall *)(void *, void *, float))(DWORD_PTR)klrk_vt[1 + 193];
        klrk_vt[1 + 42] = (DWORD)(DWORD_PTR)klrk_w42;
        klrk_vt[1 + 193] = (DWORD)(DWORD_PTR)klrk_w193;
    }
    klh_rules_vt2 = nv;
    if (klh_data((void *)(DWORD_PTR)r, &nv, 4, "round keep: Sv rules vtable (private copy, slots 42 / 193)"))
        klog("roundkeep: Sv rules %08lx wrapped (slots 42 and 193), KeepRound=%d", (unsigned long)r, klrk_keep);
    else klh_rules_vt2 = 0;
}

#endif
