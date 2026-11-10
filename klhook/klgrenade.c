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
 *
 * [Grenade] Release=1 (2026-11-09, NEW, default 0 "(recommended off)"): luvsic's DIRECT RELEASE, ported from his a-newer-perspective
 *   loader/grenade.inc @32aa649 (gr_try, gr_probe_body, gr_throw_body, gr_ammo_body; in contribution with luvsic). It does not play the dead
 *   0x40 / 0x800 button bits. On the G press it calls, in order, under klfc_guard (this DLL's existing fault guard, no second handler):
 *     0x477650 (item, &rel[3])   SetReleasePos          READ grenade.inc GR_F_SETREL
 *     item vt+0x2cc = 0x536dc0 (item, &v[3])             SetThrowVelocity
 *     0x659be0 (item)            TryFire -> vt+0x340 = 0x4cb7a0 (the shot) -> projectile pool 0x696f50
 *   then consumes one grenade (vt+0x300 / vt+0x308) and raises PlayerMonitor event 30 (0x589600, cdecl) as he does. The velocity is his
 *   NPC formula (klgrenade_logic.h). A shot counts only when item+0x138 moved AND the release point (item+0x140) was consumed AND the pool
 *   cursor moved; otherwise nothing is consumed.
 *   WHERE: offline only. Arcade rounds through klinv_player() (any map where you hold a kind-0 item) plus the campaign levels when
 *   [Campaign] Enable=1 (klcmp_level_active, local player slot). NOT gated to the campaign.
 *   ONLINE: whether Dog Days replicates a fired projectile to peers is a GUESS and was NOT tested, so the mode stays off online.
 *   NOT BENCHED: the chain ran in luvsic's Dead Men loader, never in this DLL.
 *   KEYS: Release=0  ReleaseRange=2000  ReleaseSpeed=1000  ReleaseVMax=1500  ReleaseUp=150  ReleaseFwd=70  ReleaseCoolMs=1000
 *         ReleaseConsume=1  ReleaseRefill=1  ReleaseEvent=30 (0 = none). Release wins over Throw when both are 1.
 */
#ifndef KLGRENADE_C
#define KLGRENADE_C

#include "klgrenade_logic.h"
#include "klgrenadefx_logic.h"

#define KLGR_WEAPON_VT 0x00bc042cu               /* ZFFItemWeapon (READ grenade.inc GR_WEAPON_VT) */
#define KLGR_AMMOT_VT  0x00bbfbfcu               /* ZFFItemTemplateAmmo */
#define KLGR_SETREL    0x00477650u               /* SetReleasePos(item, float[3]) */
#define KLGR_TRYFIRE   0x00659be0u
#define KLGR_SETVEL    0x00536dc0u               /* what item vt+0x2cc holds */
#define KLGR_SHOT      0x004cb7a0u               /* what item vt+0x340 holds */
#define KLGR_PMRAISE   0x00589600u               /* cdecl(P, event) */
#define KLGR_HOBJ      0x008ccde0u               /* cdecl(handle) -> object */

#define KLGR_O_BTN   0xb90                   /* replicated button state; bit 0x40 = grenade (READ 0x4aa410) */
#define KLGR_O_ACT   0x818                   /* action word; bit 0x800 = grenade (READ 0x5447f9) */

static struct {
    int on, probe, thr, key, actbit, logn, spawn;
    DWORD hold_ms, press_at, last_sample, watch_until, last_btn, last_act, after_at, after_p;
    DWORD sp_at, sp_p, sp_obj; int sp_n;
    int samples, was, fgwarned, presses, nonade, ticks0x40, actwarned, holding, faults;
    int rel, relConsume, relRefill, relEvent, relN, relHeads, relDead; DWORD relCoolMs, relLast, fxDue, fxP; struct klgr_cfg rc;
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

/* ---- [Grenade] Release: luvsic's direct release (see the header) ---- */
static int klgr_rel_heads(void)               /* once: code heads and vtable slots this mode calls through (MEASURED in kl2.exe 2026-11-09) */
{
    static const BYTE setrel[5] = { 0x51, 0x8b, 0x44, 0x24, 0x08 }, tryf[7] = { 0x83, 0xec, 0x0c, 0x53, 0x56, 0x8b, 0xf1 },
                      pm[5] = { 0x55, 0x8b, 0x6c, 0x24, 0x0c }, hobj[6] = { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d },
                      shot[6] = { 0x81, 0xec, 0xa0, 0x01, 0x00, 0x00 }, pool[6] = { 0x8b, 0x81, 0xb0, 0x00, 0x00, 0x00 };   /* READ grenade.inc:154-155 (0x4cb7a0, 0x696f50) */
    if (klgr.relHeads) return klgr.relHeads > 0;
    klgr.relHeads = -1;
    if (!klb_same_code(KLGR_SETREL, setrel, 5) || !klb_same_code(KLGR_SETVEL, setrel, 5) || !klb_same_code(KLGR_TRYFIRE, tryf, 7)
        || !klb_same_code(KLGR_PMRAISE, pm, 5) || !klb_same_code(KLGR_HOBJ, hobj, 6) || !klb_same_code(KLGR_SHOT, shot, 6) || !klb_same_code(0x00696f50u, pool, 6)) { klog("grenade release: a routine head is not the one this build knows: OFF"); return 0; }
    if (klh_rd32((DWORD_PTR)KLH_VA(KLGR_WEAPON_VT + 0x2cc)) != KLGR_SETVEL || klh_rd32((DWORD_PTR)KLH_VA(KLGR_WEAPON_VT + 0x340)) != KLGR_SHOT
        || klh_rd32((DWORD_PTR)KLH_VA(KLGR_WEAPON_VT + 0x300)) != 0x006f4f30u || klh_rd32((DWORD_PTR)KLH_VA(KLGR_WEAPON_VT + 0x308)) != 0x008be2c0u
        || klh_rd32((DWORD_PTR)KLH_VA(KLGR_AMMOT_VT + 0x2bc)) != 0x00696f50u) {   /* READ grenade.inc:159-161 (clip / reserve setters, the pool pick) */ klog("grenade release: weapon vtable slots +0x2cc / +0x340 / +0x300 / +0x308 / ammo +0x2bc are not the known routines: OFF"); return 0; }
    klgr.relHeads = 1; return 1;
}
/* the player for the release: the Arcade player (klinv_player), else on a campaign level the selected local slot. Never online. */
static DWORD klgr_rel_player(void)
{
    DWORD p = klinv_player(), gd; BYTE sel = 0xff;
    if (p) return p;
    if (kl_online() || !klcmp_level_active()) return 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3 || !(p = klh_rd32(gd + 0x828 + 4 * sel)) || klh_pvt(p) != KLINV_PLAYER_VT) return 0;
    return p;
}
static DWORD klgr_hobj(DWORD h) { return h ? ((DWORD (__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLGR_HOBJ))(h) : 0; }

struct klgr_rl {
    DWORD P, it, ammoT, proj; const char *why;
    float rel[3], v[3], rel1[3];
    int shots0, shots1, pCnt, pIdx, pNext, pValid, pellets, idx1;
};
/* what the shot needs to launch (reads and handle lookups only): READ grenade.inc gr_probe_body */
static int klgr_rl_probe(void *arg)
{
    struct klgr_rl *a = (struct klgr_rl *)arg; DWORD ownerObj, ammoT, h[256], wt, k; int i;
    a->why = 0; a->ammoT = a->proj = 0; a->pCnt = a->pValid = a->pellets = 0; a->pIdx = a->pNext = -1;
    a->shots0 = (int)klh_rd32(a->it + 0x138);
    ownerObj = klgr_hobj(klh_rd32(a->it + 0x5c));
    if (ownerObj != a->P) { a->why = ownerObj ? "the item's owner (item+0x5c) is not the player" : "the item has no owner (item+0x5c)"; return 0; }
    ammoT = klgr_hobj(klh_rd32(a->it + 0xd4));
    if (!klfc_ok(ammoT, 0xc0) || klh_rd32(ammoT) != KLGR_AMMOT_VT) { a->why = "no ZFFItemTemplateAmmo at item+0xd4"; return 0; }
    a->ammoT = ammoT; a->pellets = (int)klh_rd32(ammoT + 0x80);
    a->pCnt = (int)klh_rd32(ammoT + 0xac); a->pIdx = (int)klh_rd32(ammoT + 0xb0); k = klh_rd32(ammoT + 0xa8);
    if (!k || a->pCnt <= 0 || a->pCnt > 256 || a->pIdx < 0 || a->pIdx >= a->pCnt || !klh_rd(k, h, 4 * a->pCnt)) { a->why = "no projectile pool (ammo template +0xa8 / +0xac / +0xb0)"; return 0; }
    for (i = 0; i < a->pCnt; i++) {
        int j = (a->pIdx + i) % a->pCnt; DWORD o = klgr_hobj(h[j]);
        if (o) { a->pValid++; if (a->pNext < 0) { a->pNext = j; a->proj = o; } }
    }
    if (!a->pValid) { a->why = "the projectile pool is empty (no clone of the projectile template)"; return 0; }
    if (a->pellets < 1) { a->why = "the ammo template launches 0 projectiles (+0x80)"; return 0; }
    wt = klh_rd32(a->it + 0xc4);   /* READ grenade.inc:370 and gr_tmpl:268: item+0xc4 is the weapon template POINTER (not a handle; passing it to 0x8ccde0 was a bug) */
    if (!klfc_ok(wt, 0x1b0) || (klh_rd32(wt + 0xac) != 11 && klh_rd32(wt + 0xac) != 12)) { a->why = "the item's template is not a grenade weapon type (template +0xac is not 11 / 12)"; return 0; }   /* READ gr_is_grenade */
    if (!klh_rd32(wt + 0x1a4)) { a->why = "the weapon template's launch box (+0x1a4) is null: the shot would skip the launch"; return 0; }
    return 1;
}
/* THE RELEASE: SetReleasePos, SetThrowVelocity, TryFire (the shot 0x4cb7a0 runs inside TryFire) */
static int klgr_rl_throw(void *arg)
{
    struct klgr_rl *a = (struct klgr_rl *)arg;
    ((void (__fastcall *)(DWORD, DWORD, float *))(DWORD_PTR)KLH_VA(KLGR_SETREL))(a->it, 0, a->rel);
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD, float *), klfc_vf(a->it, 0x2cc))(a->it, 0, a->v);
    ((void (__fastcall *)(DWORD, DWORD))(DWORD_PTR)KLH_VA(KLGR_TRYFIRE))(a->it, 0);
    a->shots1 = (int)klh_rd32(a->it + 0x138); a->idx1 = (int)klh_rd32(a->ammoT + 0xb0);
    klh_rd(a->it + 0x140, a->rel1, 12);
    return 1;
}
struct klgr_am { DWORD P, it; int clip, res, setClip, setRes, ev; };
static int klgr_rl_ammo(void *arg)           /* READ grenade.inc gr_ammo_body: setters vt+0x300 (clip) / vt+0x308 (reserve), then the PlayerMonitor raise */
{
    struct klgr_am *m = (struct klgr_am *)arg;
    if (m->setClip) KLFC_PTR(void (__fastcall *)(DWORD, DWORD, int), klfc_vf(m->it, 0x300))(m->it, 0, m->clip);
    if (m->setRes) KLFC_PTR(void (__fastcall *)(DWORD, DWORD, int), klfc_vf(m->it, 0x308))(m->it, 0, m->res);
    if (m->ev > 0) ((void (__cdecl *)(DWORD, int))(DWORD_PTR)KLH_VA(KLGR_PMRAISE))(m->P, m->ev);
    return 1;
}
/* the first kind-0 inventory item with ammo. GUESS: binding kind 0 = Grenade (klinv.c's reading, as Throw uses it); luvsic picks by
   eFF2ItemType (0x539e30) with SpecialEquipment as the second choice: not ported. */
static DWORD klgr_rel_pick(DWORD P, int *clip, int *res)
{
    DWORD inv, arr, cnt, i, obj, bind, item, kind;
    if (!klinv_inv(P, &inv, &arr, &cnt)) return 0;
    for (i = 0; i < cnt; i++) {
        if (!klinv_entry(arr, i, &obj, &bind, &item, &kind) || !obj || kind != 0 || klh_rd32(obj) != KLGR_WEAPON_VT) continue;
        { DWORD t = klh_rd32(obj + 0xc4), w = klfc_ok(t, 0xb0) ? klh_rd32(t + 0xac) : 0; if (w != 11 && w != 12) continue; }   /* READ gr_is_grenade: template +0xac 11 / 12 */
        *clip = klgr_unxor(klh_rd32(obj + 0xdc)); *res = klgr_unxor(klh_rd32(obj + 0xe0));
        if (*clip + (*res > 0 ? *res : 0) > 0) return obj;
    }
    return 0;
}
static DWORD klgx_press(DWORD P, DWORD now);             /* klgrenadefx.c (included after kladren.c): PinSound / ThrowAnim */
static void klgx_launched(void);
static int klgx_own_act(DWORD act);
static void klgx_poll(void);
static void klgx_init(void);
/* fromGo=0: the G press; fromGo=1: the release that klgx_press delayed. Returns 0 only for "not now, try again" (a delayed release outside the gameplay call). */
static int klgr_release(DWORD P, DWORD now, int fromGo)
{
    struct klgr_rl a; struct klgr_plan pl; struct klgr_am m; float feet[3], aim[3], rz[3]; int clip = 0, res = 0, ran, relUsed, launched, nc, nr, empty;
    if (klgr.relDead) return 1;
    if (!fromGo && klgr.fxDue) return 1;                                    /* a release is pending: this press is the same throw */
    if (!klgr_cool_over(klgr.relLast, now, klgr.relCoolMs)) return 1;
    if (!klgr_rel_heads()) { klgr.relDead = 1; return 1; }
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) { if (fromGo) return 0; if (klgr.relN++ < 5) klog("grenade release: not the main loop's gameplay call: skipped"); return 1; }
    if (klh_rd32(P + 0x6b0) != P + 0xdb0 || klh_rd32(P + 0xd50) || klh_rd32(P + 0xd44) || klfc_movid(P) == 0x10) { if (klgr.relN++ < 5) klog("grenade release: movement table (MiniScene) / seat or carrier / rappel: skipped (READ grenade.inc gr_precond)"); return 1; }
    { BYTE lh = 0; if (!klh_rd(P + 0x2720, &lh, 1) || !(lh & 2)) { if (klgr.relN++ < 5) klog("grenade release: not the local human player: skipped"); return 1; } }
    { DWORD act = klfc_cur_act(P); if (act != 0 && !(fromGo && klgx_own_act(act))) { if (klgr.relN++ < 5) klog("grenade release: an action is running (or unreadable): skipped"); return 1; } }
    memset(&a, 0, sizeof a); a.P = P;
    if (!(a.it = klgr_rel_pick(P, &clip, &res))) { if (klgr.relN++ < 5) klog("grenade release: G pressed but no grenade with ammo in the inventory: nothing called"); return 1; }
    if (!fromGo) { DWORD due = klgx_press(P, now); if (due) { klgr.fxDue = due; klgr.fxP = P; return 1; } }      /* pin sound / throw clip first, the release follows ThrowDelayMs later */
    if (!klh_rd(P + 0x460, feet, 12) || !klh_rd(P + 0x27b0, aim, 12) || !klgr_plan_throw(feet, aim, &klgr.rc, &pl)) { if (klgr.relN++ < 5) klog("grenade release: no usable feet / aim point: refused"); return 1; }
    memcpy(a.rel, pl.rel, 12); memcpy(a.v, pl.v, 12);
    if (klfc_guard("grenade release probe", klgr_rl_probe, &a) < 0) { klgr.relDead = 1; klog("grenade release: DISABLED (fault in the probe)"); return 1; }
    klog("grenade release: item %08lx clip %d res %d rel=(%.1f,%.1f,%.1f) dist=%.0f t=%.2fs v=(%.1f,%.1f,%.1f)%s%s", a.it, clip, res,
         pl.rel[0], pl.rel[1], pl.rel[2], (double)pl.dist, (double)pl.t, pl.v[0], pl.v[1], pl.v[2], a.why ? " REFUSED: " : "", a.why ? a.why : "");
    if (a.why) return 1;
    klgr.relLast = now ? now : 1;
    if (a.pNext != a.pIdx) { DWORD c = (DWORD)a.pNext; klfc_put(a.ammoT + 0xb0, &c, 4, "grenade release: pool cursor"); klog("grenade release: pool entry %d empty: cursor moved to %d", a.pIdx, a.pNext); }
    if (klfc_guard("grenade release", klgr_rl_throw, &a) < 0) { klgr.relDead = 1; klog("grenade release: DISABLED (fault in the throw; restart the game)"); return 1; }
    memset(rz, 0, sizeof rz);
    ran = a.shots1 != a.shots0; relUsed = !memcmp(a.rel1, rz, 12);                  /* the shot zeroes the release point once it used it (READ 0x4cb95a) */
    launched = klgr_launched(a.shots0, a.shots1, relUsed, a.pNext, a.idx1, a.pCnt);
    klog("grenade release: shot %s (item+0x138 %d -> %d), release point %s, pool cursor %d -> %d: %s", ran ? "RAN" : "did NOT run", a.shots0, a.shots1,
         relUsed ? "used" : "NOT used", a.pNext, a.idx1, launched ? "LAUNCHED" : "no launch, no ammo used");
    if (!launched) return 1;
    klgr.presses++;
    klgx_launched();
    memset(&m, 0, sizeof m); m.P = P; m.it = a.it; m.ev = klgr.relEvent;
    if (klgr.relConsume) {
        empty = klgr_consume(clip, res, klgr.relRefill, &nc, &nr);
        m.clip = nc; m.res = nr; m.setClip = nc != clip; m.setRes = nr != (res > 0 ? res : 0);
        klog("grenade release: ammo clip %d -> %d, reserve %d -> %d%s", clip, nc, res, nr, empty ? " (empty; the item stays in the inventory)" : "");
    }
    if (klfc_guard("grenade release ammo", klgr_rl_ammo, &m) < 0) { klgr.relDead = 1; klog("grenade release: DISABLED (fault in the ammo / event step)"); return 1; }
    return 1;
}

static void klgrenade_tick(int game_thread)
{
    DWORD now, p, pid = 0; int down, edge;
    if (!klgr.on || !klh_exe_ok || !game_thread) return;
    now = GetTickCount();
    klgx_poll();
    if (klgr.fxDue && klgx_is_due(now, klgr.fxDue)) {                       /* the delayed release (klgrenadefx.c) */
        DWORD fp = klgr_rel_player();
        if (!fp || fp != klgr.fxP) klgr.fxDue = 0;
        else if (klgr_release(fp, now, 1) || klgx_expired(now, klgr.fxDue, 1500)) klgr.fxDue = 0;
    }
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
    if (!(p = klgr.rel ? klgr_rel_player() : klinv_player())) { klgr.was = down; klgr.holding = 0; return; }   /* a held key never re-edges after a player gap */
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
    if (klgr.rel) { if (edge) klgr_release(p, now, 0); klgr.was = down; return; }     /* [Grenade] Release: the direct release, no button bits */
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
    klgr.rel = GetPrivateProfileIntA("Grenade", "Release", 0, klh_ini) != 0;
    if (!klgr.probe && !klgr.thr && !klgr.spawn && !klgr.rel) return;
    v = klkeys_vk(KK_GREN); klgr.key = v < 1 || v > 0xfe ? 0x47 : v;
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
    if (klgr.rel) {
        klgr.rc.range = (float)GetPrivateProfileIntA("Grenade", "ReleaseRange", 2000, klh_ini); klgr.rc.speed = (float)GetPrivateProfileIntA("Grenade", "ReleaseSpeed", 1000, klh_ini);
        klgr.rc.vmax = (float)GetPrivateProfileIntA("Grenade", "ReleaseVMax", 1500, klh_ini); klgr.rc.up = (float)GetPrivateProfileIntA("Grenade", "ReleaseUp", 150, klh_ini);
        klgr.rc.fwd = (float)GetPrivateProfileIntA("Grenade", "ReleaseFwd", 70, klh_ini); klgr_cfg_clamp(&klgr.rc);
        v = (int)GetPrivateProfileIntA("Grenade", "ReleaseCoolMs", 1000, klh_ini); klgr.relCoolMs = v < 0 ? 0 : v > 60000 ? 60000 : v;
        klgr.relConsume = GetPrivateProfileIntA("Grenade", "ReleaseConsume", 1, klh_ini) != 0; klgr.relRefill = GetPrivateProfileIntA("Grenade", "ReleaseRefill", 1, klh_ini) != 0;
        v = (int)GetPrivateProfileIntA("Grenade", "ReleaseEvent", 30, klh_ini); klgr.relEvent = v < 0 ? 0 : v > 120 ? 120 : v;
        klog("grenade release: ON (luvsic's direct release, NOT benched; offline only, online replication is a GUESS and untested): Key=0x%02x range %.0f speed %.0f vmax %.0f up %.0f fwd %.0f cool %lu ms consume %d event %d",
             klgr.key, (double)klgr.rc.range, (double)klgr.rc.speed, (double)klgr.rc.vmax, (double)klgr.rc.up, (double)klgr.rc.fwd, klgr.relCoolMs, klgr.relConsume, klgr.relEvent);
    }
    klgr.on = 1;
    if (klgr.rel) klgx_init();
    if (klgr.rel) {}
    else if (klgr.thr)
        klog("grenade throw: on; Key=0x%02x HoldMs=%lu ActBit=%d Log=%d; offline Arcade, local player, only with a grenade in the inventory. re\\grenades_1025.md step 1",
             klgr.key, klgr.hold_ms, klgr.actbit, klgr.logn);
    else klog("grenade probe: on (log only, no writes); Key=0x%02x; offline Arcade, local player. re\\grenades_1025.md step 0", klgr.key);
    if (klgr.spawn) klog("grenade spawn: on (Spawn=%d, TEST build): G press logs the clip lookup%s", klgr.spawn, klgr.spawn >= 2 ? " and starts a ZFFActionThrow with that clip in [P+a1c]" : "");
    if (klgr.probe >= 2) klog("grenade probe2: on (also the throw-action fields on press / release; reads only)");
}

#endif /* KLGRENADE_C */
