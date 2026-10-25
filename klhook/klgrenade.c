/*
 * klgrenade.c - DEAD MEN GRENADES. re\grenades_1025.md section 5 is the plan.
 *   STEP 0 ([Grenade] Probe=1): a LOG-ONLY probe.  STEP 1 ([Grenade] Throw=1): the G key throws a grenade you carry.
 *
 * THE CHAIN (READ, re\grenades.md 7 and 13): HoldGrenade -> setter 0x4aa410 -> bit 0x40 of [player+0xb90] -> 0x544780 copies
 * that bit every frame into bit 0x800 of the action word [player+0x818] (0x5447f9 / 0x544805) -> ZFFActionThrow (action 0x11)
 * -> the projectile of the item's Ammo. kl2.exe's 0x4aa410 can only CLEAR bit 0x40 (READ), so the key is dead in Dog Days.
 *
 * STEP 0 does nothing but reads. On a key press (and every 200 ms while it is held, at most 10 samples, then once on
 * release) it logs [P+0xb90], [P+0x818], [P+0x924] (selected item id) and every inventory entry ([P+0xcec]: +8 array of
 * 16-byte entries, +0xc count; entry +0 key, +8 object, +0xc binding; binding +4 item id (GUESS, see klinv.c), +8 kind
 * 0 grenade, 1 two-handed, 2 one-handed, 3 special). For 3 s after a press it also logs any change of bit 0x40 / 0x800.
 *
 * STEP 1 plays the dead button: while G is held (game window in front) AND the inventory has a kind-0 entry with an
 * object, it ORs bit 0x40 into [P+0xb90] every game tick, as a real HoldGrenade press would, for at most HoldMs (a stuck
 * key cannot keep it on). Release = no more writes; the game's own 0x4aa410 clears the bit again. Data writes only
 * (klh_data on the heap player object), no code patch, so it is SHIP-safe.
 *   GUESS 1: that our tick runs between the input's clear and 0x544780's copy often enough; if 3 ticks pass with 0x40 set
 *     and 0x800 still clear, ActBit=1 (default) also ORs 0x800 into [P+0x818] while held (logged once per press).
 *   GUESS 2: that ZFFActionThrow takes the item, spends it and spawns the Ammo's projectile itself; this file does NOT
 *     count grenades down. The log shows the inventory 1.5 s after each release, so a first run tells whether it did.
 *   GUESS 3: hold-to-aim / release-to-throw as in Dead Men; a short tap may be too short for the action to start.
 * With no kind-0 entry (every stock FA map, or before a pickup) nothing is written: one log line per press, at most 5.
 * Local player, offline Arcade only (klinv_player: not online, a round of the Heist rules, a ZFFPlayer).
 *
 * WIRING: klhook.c  #include "klgrenade.c" below #include "klinv.c"; klgrenade_tick(game_thread) below klinv_tick;
 *   klgrenade_init() below klinv_init().
 * STEP 1b ([Grenade] Probe=2, log only, any build): see klgr_deep. VERIFIED 10-25 (wvnb1pun0): nothing in kl2.exe reads bit 0x800
 *   of [P+0x818] (Dead Men's reader 0x5f4c10 was dropped), so step 1 sets a dead bit; 0x898a50 / 0x432440 are ZFFActor methods
 *   and must never be called on the player. Probe=2 decides whether the player's own Create(0x11)+Start can work.
 * KEYS: [Grenade] Probe=0 (1 = log only, 2 = also the throw-action fields; recommended off)  Throw=0 (1 = the G key throws; off until the owner's first run)
 *   Key=0x47 (VK 'G'; polled, not consumed)  HoldMs=3000 (100 .. 10000)  ActBit=1 (0 = never touch [P+0x818])  Log=8 (presses logged in full)
 */
#ifndef KLGRENADE_C
#define KLGRENADE_C

#define KLGR_O_BTN   0xb90                   /* replicated button state; bit 0x40 = grenade (READ 0x4aa410) */
#define KLGR_O_ACT   0x818                   /* action word; bit 0x800 = grenade (READ 0x5447f9) */

static struct {
    int on, probe, thr, key, actbit, logn, spawn;
    DWORD hold_ms, press_at, last_sample, watch_until, last_btn, last_act, after_at, after_p;
    DWORD sp_at, sp_p, sp_obj; int sp_n;
    int samples, was, fgwarned, presses, nonade, ticks0x40, actwarned, holding, faults;
} klgr;

static void klgr_deep(DWORD p);

static void klgr_dump(DWORD p, const char *why)
{
    DWORD btn = 0, act = 0, sel = 0, inv, arr, cnt, i, obj, bind, item, kind;
    klh_rd(p + KLGR_O_BTN, &btn, 4); klh_rd(p + KLGR_O_ACT, &act, 4); klh_rd(p + KLINV_O_SEL, &sel, 4);
    klog("grenade %s (%s): player %08lx b90=%08lx (0x40 %s) 818=%08lx (0x800 %s) selected item %lu", klgr.thr ? "throw" : "probe",
         why, p, btn, btn & 0x40 ? "SET" : "clear", act, act & 0x800 ? "SET" : "clear", sel);
    klgr.last_btn = btn; klgr.last_act = act;
    if (!klinv_inv(p, &inv, &arr, &cnt)) { klog("grenade: inventory not readable"); return; }
    for (i = 0; i < cnt; i++)
        if (klinv_entry(arr, i, &obj, &bind, &item, &kind))
            klog("grenade:   entry %lu key %lu object %08lx binding %08lx item %lu kind %lu%s", i, klh_rd32(arr + 16 * i), obj, bind, item, kind,
                 kind == 0 ? " (GRENADE)" : kind == 3 ? " (special)" : "");
    if (klgr.probe >= 2 && strcmp(why, "held")) klgr_deep(p);                /* step 1b: press, release, 1.5 s after (not the 200 ms samples) */
}

/* STEP 1b ([Grenade] Probe=2): the fields a player ZFFActionThrow (action 0x11) would be built from. Reads only, no vt call.
 * READ: ZFFPlayer CreateAction (vt 0xbb45f4 +0x384 = 0x839740) case 0x11 at 0x839807 builds ctor 0x6757b0 (vt 0xbb4d24) with
 *   (0x11, P, [P+0xa1c], 0x59d550(this=P, word [P+0x239c])); its tick 0x65ce70 reads word [[action+0xc]+2], so [P+0xa1c] must
 *   point at a descriptor. A float or 0 there = the action is dead Dead Men code and Create+Start would crash.
 *   0x59d550 picks a random entry for that word (0xFFFF = none; it also reads [P+0x84]).
 *   vt+0x388 = 0x76ea90 calls vt+4 of [[P+0x19c]+4]; vt+0x4c8 = 0x6a85a0 / vt+0x4cc = 0x763480 call vt+8 of the subobjects at
 *   P+0x310 / P+0x388 (0x898a50's hand-object pair; which hand is which is a GUESS), so those are logged as raw pointers.
 * The 0x2c-stride structs around 0xa1c (0x9c4 .. 0xa74) are logged whole; [P+0x239c..] (0x84*4+2 bytes of words) only where not 0xFFFF. */
static void klgr_deep(DWORD p)
{
    DWORD vt = 0, v[6] = {0}, a1c = 0, d[11], k, n = 0, o19c = 0, o19c4 = 0, h[4] = {0};
    WORD tab[0x109], w2 = 0; float f; char line[240]; int len, i;
    klh_rd(p, &vt, 4);
    if (vt) { klh_rd(vt + 0x370, &v[0], 4); klh_rd(vt + 0x384, &v[1], 4); klh_rd(vt + 0x388, &v[2], 4); klh_rd(vt + 0x4c8, &v[3], 4); klh_rd(vt + 0x4cc, &v[4], 4); }
    klog("grenade probe2: player vt %08lx (ZFFPlayer = 00bb45f4) +370 %08lx (00542c00) +384 %08lx (00839740) +388 %08lx (0076ea90) +4c8 %08lx (006a85a0) +4cc %08lx (00763480)",
         vt, v[0], v[1], v[2], v[3], v[4]);
    klh_rd(p + 0xa1c, &a1c, 4); memcpy(&f, &a1c, 4);
    if (a1c > 0x10000 && klh_rd(a1c, d, 8) && klh_rd(a1c + 2, &w2, 2))
        klog("grenade probe2: [P+a1c] %08lx (as float %g): readable, +0 %08lx +4 %08lx, word +2 = %d (the tick's frame count)", a1c, f, d[0], d[1], (int)(short)w2);
    else klog("grenade probe2: [P+a1c] %08lx (as float %g): NOT a readable pointer -> action 0x11 has no descriptor (dead)", a1c, f);
    for (k = 0; k < 5; k++) {
        DWORD o = 0x9c4 + k * 0x2c;
        if (!klh_rd(p + o, d, sizeof d)) { klog("grenade probe2: struct +%03lx unreadable", o); continue; }
        klog("grenade probe2: struct +%03lx: %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx", o,
             d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8], d[9], d[10]);
    }
    klh_rd(p + 0x84, &v[5], 4);
    if (!klh_rd(p + 0x239c, tab, sizeof tab)) klog("grenade probe2: [P+239c] table unreadable");
    else {
        len = _snprintf(line, sizeof line - 1, "grenade probe2: [P+84] %08lx; [P+239c] word0 %04x (the throw's index); not-FFFF:", v[5], tab[0]);
        for (i = 0; i < 0x109; i++) {
            if (tab[i] == 0xffff) continue;
            if (++n <= 24 && len > 0 && len < (int)sizeof line - 16) len += _snprintf(line + len, sizeof line - 1 - len, " %d=%04x", i, tab[i]);
        }
        line[sizeof line - 1] = 0;
        klog("%s%s (%lu in all)", line, n > 24 ? " ..." : "", n);
    }
    klh_rd(p + 0x19c, &o19c, 4); if (o19c > 0x10000) klh_rd(o19c + 4, &o19c4, 4);
    klh_rd(p + 0x310, &h[0], 4); klh_rd(p + 0x314, &h[1], 4); klh_rd(p + 0x388, &h[2], 4); klh_rd(p + 0x38c, &h[3], 4);
    klog("grenade probe2: [P+19c] %08lx -> +4 %08lx (vt+388's object); P+310: %08lx %08lx; P+388: %08lx %08lx (hand subobjects: vtable, first field)",
         o19c, o19c4, h[0], h[1], h[2], h[3]);
}

/* the first kind-0 entry with an object -> its index, or -1 */
static int klgr_find(DWORD p)
{
    DWORD inv, arr, cnt, i, obj, bind, item, kind;
    if (!klinv_inv(p, &inv, &arr, &cnt)) return -1;
    for (i = 0; i < cnt; i++)
        if (klinv_entry(arr, i, &obj, &bind, &item, &kind) && obj && bind > 0x10000 && kind == 0) return (int)i;
    return -1;
}

/* step 1, one game tick with the key down: set the grenade bit (and the action bit, see GUESS 1) */
static void klgr_hold(DWORD p, DWORD now, int edge)
{
    DWORD btn = 0, act = 0, v; int full = klgr.presses <= klgr.logn;
    if (edge) {
        klgr.holding = 0; klgr.ticks0x40 = 0; klgr.actwarned = 0;
        if (klgr_find(p) < 0) {
            if (++klgr.nonade <= 5) klog("grenade throw: G pressed but you carry no grenade (no inventory kind-0 entry): nothing written");
            return;
        }
        klgr.holding = 1; klgr.presses++; full = klgr.presses <= klgr.logn;
        if (full) klgr_dump(p, "press");
    }
    if (!klgr.holding) return;
    if (now - klgr.press_at > klgr.hold_ms) {
        if (klgr.holding == 1 && full) klog("grenade throw: held %lu ms: stopped writing (HoldMs)", klgr.hold_ms);
        klgr.holding = 2; return;
    }
    if (klgr.holding != 1) return;
    if (!klh_rd(p + KLGR_O_BTN, &btn, 4) || !klh_rd(p + KLGR_O_ACT, &act, 4)) return;
    if (act & 0x800) klgr.ticks0x40 = 0;                                     /* the game's copy works: no fallback */
    if (btn & 0x40) {                                                       /* still set from the last tick: has the copy run? */
        if (!(act & 0x800) && ++klgr.ticks0x40 >= 3 && klgr.actbit) {        /* 3 CONSECUTIVE ticks (reset below and above) */
            if (!klgr.actwarned++ && full) klog("grenade throw: 0x40 set for 3 ticks but 0x800 of 818 clear: ORing 0x800 into 818 too (ActBit=1, GUESS 1)");
            v = act | 0x800; klh_data((void *)(DWORD_PTR)(p + KLGR_O_ACT), &v, 4, "grenade action bit");
        }
    } else {
        klgr.ticks0x40 = 0;
        v = btn | 0x40;
        if (!klh_data((void *)(DWORD_PTR)(p + KLGR_O_BTN), &v, 4, "grenade button bit") && ++klgr.faults <= 3) klog("grenade throw: write to b90 refused");
    }
}

/* SPAWN PROTOTYPE ([Grenade] Spawn, TEST build only, default 0). re\grenade_spawn_plan.md steps 2a / 2b.
 * READ 2026-10-25: CreateAction case 0x11 (0x839807) calls ctor 0x6757b0 with (0x11, P, [P+0xa1c], clip), so action+0xc = [P+0xa1c],
 *   action+0x10 = the clip 0x59d550(P, word [P+0x239c]) gives. The tick 0x65ce70 reads word [[action+0xc]+2] (frame count) at 0x65cea5 AND
 *   at 0x65cf79 plays [action+0xc] as a clip (P vt+0x210), at 0x65cfc3 reads [[action+0x10]+2]: BOTH are clip records of the kind 0x59d550
 *   returns (the same kind kladren.c / klclimb.c use), not a separate descriptor. [P+0xa1c] is dead in Dog Days (never written), so the
 *   guess is that any valid clip there lets the tick run.  GUESS: the same clip for both fields (the first-phase clip is unknown).
 * Spawn=1: on G press (game window in front, a kind-0 inventory entry) log the clip 0x59d550 gives for the throw index, its first 16 bytes,
 *   and the item's +0xc8..0xd0 floats. Reads plus the game's own clip lookup (it draws one number from the game's generator). No action.
 * Spawn=2: also write that clip into [P+0xa1c] (data write), Abort (vt+0x374), CreateAction(0x11) (vt+0x384), StartAction (vt+0x370), inside
 *   klfc_guard, restore [P+0xa1c]=old, then log the player's action and the item's +0xc8..0xd0 floats at once, +0.5 s and +1.5 s.
 *   Fires only when the player has NO action (klfc_cur_act == 0) and at most once per 3 s. A velocity appearing in the item = the release worked. */
#ifdef KLHOOK_TEST
#define KLGR_CLIP 0x0059d550u
static void klgr_itemvel(DWORD obj, const char *when)
{
    float f[3] = {0, 0, 0};
    if (obj && klfc_ok(obj, 0xe0) && klh_rd(obj + 0xc8, f, 12)) klog("grenade spawn: item %08lx vel(+c8..d0) %g %g %g (%s)", obj, f[0], f[1], f[2], when);
    else klog("grenade spawn: item %08lx unreadable (%s)", obj, when);
}
struct klgr_sp { DWORD P, obj, clip, old; int ok; };
static int klgr_sp_body(void *arg)
{
    struct klgr_sp *g = (struct klgr_sp *)arg; DWORD P = g->P, act, zero = 0, cur;
    cur = klfc_cur_act(P);
    if (cur != 0) { klog("grenade spawn: player has an action (%08lx): not starting", cur); return 0; }
    g->old = klh_rd32(P + 0xa1c);
    klfc_put(P + 0xa1c, &g->clip, 4, "grenade spawn: [P+a1c]");
    act = KLFC_PTR(DWORD (__fastcall *)(DWORD, DWORD, int), klfc_vf(P, 0x384))(P, 0, 0x11);
    if (!klfc_ok(act, 0x28) || klh_rd32(act) != 0x00bb4d24u || klh_rd32(act + 8) != P) { klog("grenade spawn: CreateAction(0x11) gave %08lx (not a ZFFActionThrow)", act); klfc_put(P + 0xa1c, &g->old, 4, "grenade spawn: restore"); return 0; }
    klog("grenade spawn: action %08lx made: +c %08lx +10 %08lx; starting", act, klh_rd32(act + 0xc), klh_rd32(act + 0x10));
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD), klfc_vf(P, 0x374))(P, 0);
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD, DWORD), klfc_vf(P, 0x370))(P, 0, act);
    klfc_put(P + 0xa1c, &g->old, 4, "grenade spawn: restore");
    (void)zero;
    klog("grenade spawn: started; player action now %08lx (ours %08lx)", klfc_cur_act(P), act);
    g->ok = 1; return 1;
}
static void klgr_spawn(DWORD P)
{
    struct klgr_sp g; DWORD word = 0, rec[4] = {0, 0, 0, 0}; int idx = klgr_find(P); WORD w2 = 0; DWORD inv, arr, cnt, obj = 0, bind, item, kind; DWORD now = GetTickCount();
    if (now - klgr.sp_at < 3000 && klgr.sp_at) return;
    klgr.sp_at = now;
    if (idx < 0) { if (klgr.sp_n++ < 3) klog("grenade spawn: no grenade in the inventory"); return; }
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) { klog("grenade spawn: not the main loop's gameplay call: skipped"); return; }
    memset(&g, 0, sizeof g); g.P = P;
    if (klinv_inv(P, &inv, &arr, &cnt) && klinv_entry(arr, (DWORD)idx, &obj, &bind, &item, &kind)) {}
    klh_rd(P + 0x239c, &word, 2); word &= 0xffff;
    __try { g.clip = ((DWORD (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLGR_CLIP))((void *)(DWORD_PTR)P, 0, word); }
    __except (EXCEPTION_EXECUTE_HANDLER) { klog("grenade spawn: fault in 0x59d550"); klgr.spawn = 0; return; }
    if (g.clip > 0x10000 && klfc_ok(g.clip, 0x10)) { klh_rd(g.clip, rec, 16); klh_rd(g.clip + 2, &w2, 2); }
    klog("grenade spawn: step 2a: index %lu -> clip %08lx (frames word +2 = %d) bytes %08lx %08lx %08lx %08lx; inventory entry %d item obj %08lx",
         word, g.clip, (int)(short)w2, rec[0], rec[1], rec[2], rec[3], idx, obj);
    klgr.sp_obj = obj; klgr.sp_p = P;
    klgr_itemvel(obj, "before");
    if (klgr.spawn >= 2) {
        if (!klfc_ok(g.clip, 0x68)) { klog("grenade spawn: step 2b skipped: no usable clip (index %lu)", word); return; }
        if (!klfc_guard("grenade spawn", klgr_sp_body, &g)) klog("grenade spawn: step 2b faulted or refused (a1c restored)");
        klgr_itemvel(obj, "at once");
        klgr.sp_at = now; klgr.after_at = 0; klgr.sp_n = 0;
    }
}
#endif

static void klgrenade_tick(int game_thread)
{
    DWORD now, p, pid = 0; int down, edge;
    if (!klgr.on || !klh_exe_ok || !game_thread) return;
    now = GetTickCount();
    down = (klinv_key(klgr.key) & 0x8000) != 0;
    if (klgr.after_at && (int)(now - klgr.after_at) >= 0) {                 /* 1.5 s after a logged release: what is left */
        klgr.after_at = 0;
        if ((p = klinv_player()) && p == klgr.after_p) __try { klgr_dump(p, "1.5 s after release"); } __except (EXCEPTION_EXECUTE_HANDLER) {}
    }
#ifdef KLHOOK_TEST
    if (klgr.spawn >= 2 && klgr.sp_obj && klgr.sp_p) {                      /* +0.5 s / +1.5 s after a started throw: did the item get a velocity? */
        static DWORD t0; static int stage;
        if (klgr.sp_at != t0) { t0 = klgr.sp_at; stage = 0; }
        if (stage < 2 && now - t0 >= (stage ? 1500u : 500u)) { stage++; __try { klgr_itemvel(klgr.sp_obj, stage == 1 ? "+0.5 s" : "+1.5 s"); } __except (EXCEPTION_EXECUTE_HANDLER) {} }
    }
#endif
    if (!down && !klgr.was && !(klgr.watch_until && (int)(klgr.watch_until - now) > 0)) return;   /* idle: no player reads */
    if (!(p = klinv_player())) { klgr.was = down; klgr.holding = 0; return; }   /* a held key never re-edges after a player gap */
    if (klgr.watch_until && (int)(klgr.watch_until - now) > 0 && (klgr.probe || klgr.presses <= klgr.logn)) {   /* bit changes after a press */
        DWORD btn = 0, act = 0;
        if (klh_rd(p + KLGR_O_BTN, &btn, 4) && klh_rd(p + KLGR_O_ACT, &act, 4)) {   /* a failed read is skipped, not logged as a change */
            if ((btn ^ klgr.last_btn) & 0x40) klog("grenade: b90 bit 0x40 now %s (+%lu ms)", btn & 0x40 ? "SET" : "clear", now - klgr.press_at);
            if ((act ^ klgr.last_act) & 0x800) klog("grenade: 818 bit 0x800 now %s (+%lu ms)", act & 0x800 ? "SET" : "clear", now - klgr.press_at);
            klgr.last_btn = btn; klgr.last_act = act;
        }
    }
    if (down) {
        klinv_wtp(klinv_fg(), &pid);
        if (pid != GetCurrentProcessId()) {                                 /* was = down: focus coming back with G held is no press */
            if (!klgr.fgwarned++) klog("grenade: key seen but the game window is not in front: ignored");
            klgr.holding = 0; klgr.was = down; return;
        }
    }
    edge = down && !klgr.was;
#ifdef KLHOOK_TEST
    if (edge && klgr.spawn) __try { klgr_spawn(p); } __except (EXCEPTION_EXECUTE_HANDLER) { klog("grenade spawn: fault: spawn off"); klgr.spawn = 0; }
#endif
    __try {
        if (edge) { klgr.press_at = klgr.last_sample = now; klgr.samples = 0; if (klgr.probe && !klgr.thr) klgr.watch_until = now + 3000; }
        if (klgr.thr) {
            if (down) klgr_hold(p, now, edge);
            if (edge && klgr.holding == 1 && klgr.presses <= klgr.logn) klgr.watch_until = now + 3000;   /* change lines only for logged throws */
            else if (!down && klgr.was && klgr.holding) {                   /* the release only: while held this ran on tick 2 and ended the hold */
                if (klgr.presses <= klgr.logn) { klgr_dump(p, "release"); klgr.after_at = now + 1500; klgr.after_p = p; }
                klgr.holding = 0;
            }
        } else {
            if (edge) klgr_dump(p, "press");
            else if (down && now - klgr.last_sample >= 200 && klgr.samples < 10) { klgr.last_sample = now; klgr.samples++; klgr_dump(p, "held"); }
            else if (!down && klgr.was) klgr_dump(p, "release");
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { klog("grenade: fault while reading the player: grenades off"); klgr.on = 0; }
    klgr.was = down;
}

static void klgrenade_init(void)
{
    int v;
    v = (int)GetPrivateProfileIntA("Grenade", "Probe", 0, klh_ini); klgr.probe = v < 0 ? 0 : v > 2 ? 2 : v;
    klgr.thr = GetPrivateProfileIntA("Grenade", "Throw", 0, klh_ini) != 0;
#ifdef KLHOOK_TEST
    v = (int)GetPrivateProfileIntA("Grenade", "Spawn", 0, klh_ini); klgr.spawn = v < 0 ? 0 : v > 2 ? 2 : v;
#endif
    if (!klgr.probe && !klgr.thr && !klgr.spawn) return;
    v = (int)GetPrivateProfileIntA("Grenade", "Key", 0x47, klh_ini); klgr.key = v < 1 || v > 0xfe ? 0x47 : v;
    v = (int)GetPrivateProfileIntA("Grenade", "HoldMs", 3000, klh_ini); klgr.hold_ms = v < 100 ? 100 : v > 10000 ? 10000 : v;
    klgr.actbit = GetPrivateProfileIntA("Grenade", "ActBit", 1, klh_ini) != 0;
    v = (int)GetPrivateProfileIntA("Grenade", "Log", 8, klh_ini); klgr.logn = v < 0 ? 0 : v > 100 ? 100 : v;
    if (!klinv_key) {                                                        /* klinv_init fills these only when [Inv] is on */
        HMODULE u = GetModuleHandleA("user32.dll"); if (!u) u = LoadLibraryA("user32.dll");
        if (u) {
            klinv_key = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState");
            klinv_fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
            klinv_wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
        }
    }
    if (!klinv_key || !klinv_fg || !klinv_wtp) { klog("grenade: user32 functions not found: OFF"); return; }
    klgr.on = 1;
    if (klgr.thr)
        klog("grenade throw: on; Key=0x%02x HoldMs=%lu ActBit=%d Log=%d; offline Arcade, local player, only with a grenade in the inventory. re\\grenades_1025.md step 1",
             klgr.key, klgr.hold_ms, klgr.actbit, klgr.logn);
    else klog("grenade probe: on (log only, no writes); Key=0x%02x; offline Arcade, local player. re\\grenades_1025.md step 0", klgr.key);
    if (klgr.spawn) klog("grenade spawn: on (Spawn=%d, TEST build): G press logs the clip lookup%s", klgr.spawn, klgr.spawn >= 2 ? " and starts a ZFFActionThrow with that clip in [P+a1c]" : "");
    if (klgr.probe >= 2) klog("grenade probe2: on (also the throw-action fields on press / release; reads only)");
}

#endif /* KLGRENADE_C */
