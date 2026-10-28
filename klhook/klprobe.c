/*
 * klprobe.c - TEST-ONLY probe of the escape-lift door chain ([Probe] DoorProxy, default 0). Part of KLHook, included by
 * klhook.c inside #ifdef KLHOOK_TEST after klsolo.c (uses klog, klh_rd, klh_rd32, klh_poke, klh_ini, klh_exe_ok, KLH_VA).
 *
 * Question (Retomoto FA map, escape-lift doors never open): does TriggerBox_OpenExitElevator fire, does the
 * ZMatPosAnimProxy get controllers (count > 0 at [this+0x30]), does its message handler run?
 *
 * Three vtable-slot wrappers (a vtable entry is DATA, no code is touched; the entries lie inside a hashed range, so the
 * guard klh_may_write allows the write only under policy 'direct', i.e. [KLHook] SessionSafe=0, a direct-boot test run):
 *   ZMatPosAnimProxy vtable 0xbc36bc slot 14 = 0x4093c0  init      thiscall, 0 stack args (every ret is plain `ret`)
 *   ZMatPosAnimProxy vtable 0xbc36bc slot 26 = 0x7ed520  handler   thiscall, 2 stack args (`ret 8`; arg1 low word = message id
 *                                                                  compared with word [this+0x268] and word [0x1689640] 'Activate')
 *   ZTriggerBox      vtable 0xbc232c slot 34 = 0x45f5d0  fire      thiscall, 0 stack args (first ret at 0x45f683 is plain `ret`)
 * Subclasses of ZTriggerBox with a vtable of their own are not covered (only the class whose vtable is 0xbc232c).
 * Each wrapper is __fastcall(self, edx, stack args...): the same register/stack layout as thiscall, callee pops the same bytes.
 *
 * Probe=0 (default): klpr_init reads the key once and RETURNS: no patch, no write, no log line; the wrappers are never reached.
 * Probe=1: lines 'probe:' in KLHook.log. Names are GUESSES read safely (klh_rd, never faults): [[this+4]+0x6c] (a geom's entity name,
 *   klauto.c) and the same through the owner slot [this+0x24] -> [slot+0x60] -> [obj+4] -> +0x6c. '?' = not readable.
 *   Only lines whose name is unreadable or contains Elevator / Escape / VideoProxy / Exit are written, unless [Probe] DoorAll=1.
 *   Caps: init 200, handler 400, box 400 lines in all.
 * LEAF PROBE ([Probe] DoorLeaves=1, needs DoorProxy=1; recommended off, TEST diagnostics): after each ACCEPTED proxy handler call (count > 0 and
 *   message = own id or Activate) klpr_tick() (called by klhook.c right after klj_tick, any tick thread, reads only) logs for 6 s every 250 ms
 *   (klleaf_logic.h) one line per collected controller:
 *     probe: leaf t=<ms since accept> n=<sample> prox=<proxy> i=<index>/<count> ctl=<ctrl> st21=<byte [ctrl+0x21]> name=<ctrl name or ?> node=<node or 0>
 *            pos=(x, y, z)|pos=? raw=<8 dwords ctrl+0x20..0x3c, hex>
 *   READ (kl2.exe 0x7ed520, see klpr_leaf_line): the controller list is INLINE at proxy+0x34, [proxy+0x30] ZMatPosAnim pointers (the old line read [proxy+0x34] as a pointer to the list = WRONG); the lines below that still say GUESS are superseded by klpr_leaf_line's comment. the target node = [e+4] with e =
 *   [[ctrl+0x24]+0x60] (the owner-slot path klpr_name uses), else [ctrl+4]; the position = kle_node (klescort.c: the node's own matrix chain,
 *   scene units - NOT x100); st21 is the byte the RE notes call the controller state (answers GetMatPosAnim in 1..5); raw = ctrl+0x20..0x3c dumped
 *   as is because NO frame / time offset is proven: whichever dword changes between samples is the clip clock. The proxy accept time is also
 *   handed to kljoin.c (klj_door_at, [Join] CarStallAfterDoorMs). With [Probe] DoorAll=0 only Elevator/Escape/VideoProxy/Exit/unreadable proxies count.
 * [Join] DoorCloseMs=0 (klpr_dc_*): closes the lift doors again, see the block above klpr_dc_note.
 * KEYS ([Probe]): DoorProxy=0  DoorAll=0  DoorLeaves=0
 */
#include "klleaf_logic.h"
#define KLPR_VT_PROXY  0x00bc36bc
#define KLPR_VT_BOX    0x00bc232c
#define KLPR_INIT_VA   0x004093c0
#define KLPR_HAND_VA   0x007ed520
#define KLPR_FIRE_VA   0x0045f5d0

typedef DWORD (__fastcall *klpr_0_fn)(void *self, void *edx);
typedef DWORD (__fastcall *klpr_2_fn)(void *self, void *edx, DWORD a1, DWORD a2);

static struct { int on, all, leaves, nleaf; struct { DWORD me, at; int last; } pr[4]; int npr; volatile LONG ni, nh, nb; klpr_0_fn real_init, real_fire; klpr_2_fn real_hand; } klpr;

/* a printable C string at p (0 = unreadable) into out */
static const char *klpr_str(DWORD p, char *out, int cap)
{
    int i;
    if (p < 0x10000 || !klh_rd(p, out, 1)) return 0;
    for (i = 0; i < cap - 1; i++) {
        if (!klh_rd(p + i, out + i, 1)) return 0;
        if (!out[i]) return i ? out : 0;
        if ((BYTE)out[i] < 0x20 || (BYTE)out[i] > 0x7e) return 0;
    }
    out[cap - 1] = 0;
    return out;
}

/* entity name guess for an object: [[obj+4]+0x6c], else via its owner slot [obj+0x24] */
static const char *klpr_name(DWORD obj, char *out, int cap)
{
    DWORD n, slot, o2;
    if (!obj) return 0;
    if ((n = klh_rd32(obj + 4)) && klpr_str(klh_rd32(n + 0x6c), out, cap)) return out;
    if ((slot = klh_rd32(obj + 0x24)) && (o2 = klh_rd32(slot + 0x60)) && (n = klh_rd32(o2 + 4)) && klpr_str(klh_rd32(n + 0x6c), out, cap)) return out;
    return 0;
}

static int klpr_interesting(const char *nm)
{
    if (klpr.all || !nm) return 1;
    return strstr(nm, "Elevator") || strstr(nm, "Escape") || strstr(nm, "VideoProxy") || strstr(nm, "Exit");
}

static DWORD __fastcall klpr_init(void *self, void *edx)
{
    DWORD me = (DWORD)(DWORD_PTR)self, r = klpr.real_init(self, edx);
    char b[96]; const char *nm = klpr_name(me, b, sizeof b);
    if (klpr_interesting(nm) && InterlockedIncrement(&klpr.ni) <= 200)
        klog("probe: proxy.init this=%08lx name=%s count[+30]=%lu list[+34]=%08lx ctl244=%08lx ret=%lu", (unsigned long)me, nm ? nm : "?",
             (unsigned long)klh_rd32(me + 0x30), (unsigned long)klh_rd32(me + 0x34), (unsigned long)klh_rd32(me + 0x244), (unsigned long)r);
    return r;
}

/* ---- [Join] DoorCloseMs (2026-10-28, TEST build only, default 0 = off, recommended off until benched) ----
   Basis: re/retomoto_lift_doors.md section 5 B, "cheaper variant". The door clip is 160 frames (open 0..75, close ~80..160); the proxy only ever plays 0..75.
   DoorCloseMs ms after an accepted lift-door proxy (vtable 0xbc36bc) opened, each of its leaves (vtable 0xba8f3c, array INLINE at proxy+0x34, count [proxy+0x30]) gets
   [leaf+0xd0]=75 (first) and [leaf+0xd4]=160 (last) - the leaf tick copies them into the play head via 0x78f190 / 0x505550 (READ, doc section 1) - and then
   0x59dce0(leaf) restarts the clock and sets [leaf+0x99]=1. 0x59dce0 calling convention READ from kl2.exe: thiscall, ecx=leaf, no stack args, plain `ret`
   (one path ends `jmp [vtable+0x64]` of the leaf: its argument count is GUESS = none, the game's own handler 0x7ed520 reaches it the same way).
   Seamless at the pose (frame 75 = held pose) is GUESS per the doc. Runs in klpr_tick = klh_tick = the game thread (same thread as klj_tick). Never closes while a LOCAL
   player's feet are within the car box (+KLPR_DC_PAD units, GUESS) or a ride is in progress: postponed, re-checked every tick. Needs [Probe] DoorProxy=1 (that is how a
   TEST build sees the proxy); the SHIP build never sees one, so the key does nothing there. Key read from [Join] (fallback [KLHook]). */
#define KLPR_VT_LEAF   0x00ba8f3c
#define KLPR_CLOSE_FN  0x0059dce0
#define KLPR_DC_PAD    60.0f
static struct { DWORD me, at; int done; } klpr_dc[4]; static int klpr_dc_ms;

static void klpr_leaf_start(DWORD me, DWORD at);

static void klpr_dc_note(DWORD me)
{
    int k, f = -1;
    if (klpr_dc_ms <= 0) return;
    for (k = 0; k < 4; k++) { if (klpr_dc[k].me == me) { f = k; break; } if (f < 0 && (!klpr_dc[k].me || klpr_dc[k].done)) f = k; }
    if (f < 0) return;
    klpr_dc[f].me = me; klpr_dc[f].at = klj_door_at; klpr_dc[f].done = 0;
}

/* a local player (or a ride in progress) is at a lift car: do not shut the doors */
static int klpr_dc_busy(void)
{
    DWORD gd, pl; BYTE sel[2]; int i, b; float feet[3];
    if (klj_ride.on) return 1;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, sel, 2)) return 1;
    for (i = 0; i < 2; i++) {
        if (sel[i] == 0xff || sel[i] >= 28 || !(pl = klh_rd32(gd + 0x828 + 4 * sel[i])) || !klj_feet(pl, feet)) continue;
        for (b = 0; b < KLJ_NBOX; b++) if (klj_box[b].on && klj_box[b].has_car && klj_in_box(feet, klj_box[b].clo, klj_box[b].chi, KLPR_DC_PAD)) return 1;
    }
    return 0;
}

static void klpr_dc_tick(void)
{
    int k, i, n = 0; DWORD now, cnt, ctl, first = 75, last = 160;
    if (klpr_dc_ms <= 0 || !klh_exe_ok) return;
    now = GetTickCount();
    for (k = 0; k < 4; k++) {
        if (!klpr_dc[k].me || klpr_dc[k].done || now - klpr_dc[k].at < (DWORD)klpr_dc_ms) continue;
        if (now - klpr_dc[k].at > (DWORD)klpr_dc_ms + 120000) { klpr_dc[k].done = 1; continue; }          /* stale (level left): give up, touch nothing */
        if (klh_rd32(klpr_dc[k].me) != (DWORD)(DWORD_PTR)KLH_VA(KLPR_VT_PROXY)) { klpr_dc[k].done = 1; continue; }
        cnt = klh_rd32(klpr_dc[k].me + 0x30);
        if (cnt < 1 || cnt > 8) { klpr_dc[k].done = 1; continue; }
        if (klpr_dc_busy()) continue;                                                                      /* postponed, asked again next tick */
        n = 0;                                                                                             /* per proxy (A1LIFT6 logged "10 of 5") */
        for (i = 0; i < (int)cnt; i++) {
            ctl = klh_rd32(klpr_dc[k].me + 0x34 + 4 * i);
            if (ctl < 0x10000 || klh_rd32(ctl) != (DWORD)(DWORD_PTR)KLH_VA(KLPR_VT_LEAF)) continue;
            if (!klh_data((void *)(DWORD_PTR)(ctl + 0xd0), &first, 4, "doorclose first") || !klh_data((void *)(DWORD_PTR)(ctl + 0xd4), &last, 4, "doorclose last")) continue;
            ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLPR_CLOSE_FN))((void *)(DWORD_PTR)ctl, 0);
            n++;
        }
        klpr_dc[k].done = 1;
        klog("doorclose: proxy %08lx: %d of %lu leaf(s) set to frames 75..160 and restarted %lu ms after the doors opened (DoorCloseMs=%d)", (unsigned long)klpr_dc[k].me, n, (unsigned long)cnt, (unsigned long)(now - klpr_dc[k].at), klpr_dc_ms);
        klpr_leaf_start(klpr_dc[k].me, now);                                                               /* DoorLeaves: sample the closing too */
    }
}

/* an accepted door proxy: stamp for kljoin.c and (DoorLeaves) start a 6 s sample series for this proxy (4 proxies at most; a re-accept restarts it) */
static void klpr_accepted(DWORD me)
{
    DWORD now = GetTickCount();
    klj_door_at = now ? now : 1;
    klpr_dc_note(me);
    klpr_leaf_start(me, klj_door_at);
}

/* DoorLeaves: (re)start a 6 s sample series for this proxy from 'at' (the open accept, or a DoorCloseMs close) */
static void klpr_leaf_start(DWORD me, DWORD at)
{
    DWORD now = GetTickCount(); int k;
    if (!klpr.leaves) return;
    for (k = 0; k < klpr.npr && klpr.pr[k].me != me; k++) ;
    if (k == klpr.npr) {                               /* a new proxy: reuse a finished slot first (rounds / levels re-create proxies at new addresses) */
        int f;
        for (f = 0; f < klpr.npr && klpr.pr[f].at && now - klpr.pr[f].at <= KLLEAF_SPAN_MS + KLLEAF_STEP_MS; f++) ;
        if (f < klpr.npr) k = f; else if (klpr.npr < 4) klpr.npr++; else return;
    }
    klpr.pr[k].at = 0;                                 /* klpr_tick may run on another thread: park the slot while it is rewritten */
    klpr.pr[k].me = me; klpr.pr[k].last = 0; klpr.pr[k].at = at ? at : 1;
}

/* one controller of a proxy: one compact line (formats in the header comment).
   LAYOUT (READ from kl2.exe 2026-10-28, "ZMatPosAnim" vtable 0xba8f3c, size 0xe0): handler 0x7ed520 loops edi over the INLINE array
   [proxy+0x34+4*i], i < [proxy+0x30], writes first/last ints to [ctl+0xd0]/[ctl+0xd4] (and into the clip state via 0x78f190/0x505550),
   then 0x59dce0(ctl): [ctl+0x99]=1, [ctl+0x34]=game ms [[0xdd2640]+0x48] (clip start). Clip state at ctl+0x34 (evaluator 0x422c50, caller 0x7b9590
   from vtable slot 25 0x51a120): +0 start ms, +4 rate, +8 flag, +0xc keys, +0x10 first, +0x14 last (floats), +0x18 = current frame
   (cached; 0x51a120 reads it at ctl+0x4c). Moved geom = [ctl+0x24] (0x7b9633 calls its vtable+0x8c); node = [geom+4] (GUESS: same node kle_node
   walks for actors; 0x7b9670 reads [[geom+4]+0x30..0x38] as a second position triple). */
static void klpr_leaf_line(DWORD me, DWORD at, int n, int i, DWORD cnt, DWORD ctl)
{
    char b[64]; const char *nm; BYTE act = 0xff; DWORD vt, geom, node = 0, gt, fi = 0, la = 0; float pos[3], fr = 0, rate = 0, f0 = 0, f1 = 0; DWORD st = 0; int pv = 0;
    vt = klh_rd32(ctl);
    klh_rd(ctl + 0x99, &act, 1);
    klh_rd(ctl + 0x34, &st, 4); klh_rd(ctl + 0x38, &rate, 4); klh_rd(ctl + 0x44, &f0, 4); klh_rd(ctl + 0x48, &f1, 4); klh_rd(ctl + 0x4c, &fr, 4);
    klh_rd(ctl + 0xd0, &fi, 4); klh_rd(ctl + 0xd4, &la, 4);
    gt = klh_rd32(klh_rd32((DWORD_PTR)KLH_VA(0x00dd2640)) + 0x48);                       /* game ms, the clock the clip start is taken from */
    geom = klh_rd32(ctl + 0x24);
    nm = klpr_name(geom, b, sizeof b);
    if (geom && (node = klh_rd32(geom + 4)) != 0) pv = kle_node(node, pos, 0);
    klog("probe: leaf t=%lu n=%d prox=%08lx i=%d/%lu ctl=%08lx vt=%08lx%s act99=%u frame4c=%.2f start=%lu gms=%lu age=%ld rate=%g clip=%g..%g ints=%ld..%ld geom=%08lx name=%s node=%08lx %s",
         (unsigned long)(GetTickCount() - at), n, (unsigned long)me, i, (unsigned long)cnt, (unsigned long)ctl, (unsigned long)vt, vt == (DWORD)KLH_VA(0x00ba8f3c) ? "(ZMatPosAnim)" : "(NOT ZMatPosAnim)",
         (unsigned)act, fr, (unsigned long)st, (unsigned long)gt, (long)(gt - st), rate, f0, f1, (long)fi, (long)la, (unsigned long)geom, nm ? nm : "?", (unsigned long)node, "pos:");
    if (pv) klog("probe: leaf   pos=(%.1f, %.1f, %.1f)", pos[0], pos[1], pos[2]); else klog("probe: leaf   pos=?");
}

/* called every tick by klhook.c after klj_tick; reads only; costs one compare when no series runs */
static void klpr_tick(void)
{
    int k, i, n; DWORD now, cnt, list, ctl;
    klpr_dc_tick();                                    /* [Join] DoorCloseMs: idle (one compare) when 0 */
    if (!klpr.leaves || !klpr.npr) return;
    now = GetTickCount();
    for (k = 0; k < klpr.npr; k++) {
        if (!(n = klleaf_due(now, klpr.pr[k].at, klpr.pr[k].last))) continue;
        klpr.pr[k].last = n;
        if (klpr.nleaf > 1000) continue;                                                   /* log cap: about 40 series */
        klpr.nleaf++;
        cnt = klh_rd32(klpr.pr[k].me + 0x30); list = klpr.pr[k].me + 0x34;                 /* READ 0x7ed5d2: the array is INLINE at proxy+0x34 */
        if (cnt > 8) cnt = 8;                                                              /* LIFT9: 5 each */
        for (i = 0; i < (int)cnt; i++) {
            ctl = klh_rd32(list + 4 * i);
            if (ctl < 0x10000) { klog("probe: leaf t=%lu n=%d prox=%08lx i=%d/%lu ctl=%08lx unreadable", (unsigned long)(now - klpr.pr[k].at), n, (unsigned long)klpr.pr[k].me, i, (unsigned long)cnt, (unsigned long)ctl); continue; }
            klpr_leaf_line(klpr.pr[k].me, klpr.pr[k].at, n, i, cnt, ctl);
        }
    }
}

static DWORD __fastcall klpr_hand(void *self, void *edx, DWORD a1, DWORD a2)
{
    DWORD me = (DWORD)(DWORD_PTR)self, cnt = klh_rd32(me + 0x30), r;
    WORD own = 0, act = 0; char b[96]; const char *nm = klpr_name(me, b, sizeof b);
    int log = klpr_interesting(nm);
    klh_rd(me + 0x268, &own, 2); klh_rd((DWORD_PTR)KLH_VA(0x01689640), &act, 2);
    if (log && InterlockedIncrement(&klpr.nh) <= 400)
        klog("probe: proxy.handler ENTER this=%08lx name=%s count[+30]=%lu msg=%04x a2=%08lx own[+268]=%04x activate=%04x -> %s", (unsigned long)me,
             nm ? nm : "?", (unsigned long)cnt, (unsigned)(a1 & 0xffff), (unsigned long)a2, (unsigned)own, (unsigned)act,
             !cnt ? "RETURNS (count 0)" : (WORD)a1 == own ? "accepted (own id)" : (WORD)a1 == act ? "accepted (Activate)" : "ignored (id differs)");
    r = klpr.real_hand(self, edx, a1, a2);
    if (log && cnt && ((WORD)a1 == own || (WORD)a1 == act)) klpr_accepted(me);
    if (log && klpr.nh <= 400) klog("probe: proxy.handler LEAVE this=%08lx ret=%lu count[+30]=%lu", (unsigned long)me, (unsigned long)r, (unsigned long)klh_rd32(me + 0x30));
    return r;
}

static DWORD __fastcall klpr_fire(void *self, void *edx)
{
    DWORD me = (DWORD)(DWORD_PTR)self;
    char b[96]; const char *nm = klpr_name(me, b, sizeof b);
    if (klpr_interesting(nm) && InterlockedIncrement(&klpr.nb) <= 400)
        klog("probe: box.fire this=%08lx name=%s list[+38]=%08lx", (unsigned long)me, nm ? nm : "?", (unsigned long)klh_rd32(me + 0x38));
    return klpr.real_fire(self, edx);
}

static int klpr_wrap(DWORD vt, int slot, DWORD expect, void *mine, void **real, const char *what)
{
    DWORD *e = (DWORD *)KLH_VA(vt + 4 * slot), cur = e ? *e : 0, m = (DWORD)(DWORD_PTR)mine;
    if (cur != expect) { klog("probe: %s: vtable %08lx slot %d holds %08lx, expected %08lx - not wrapped", what, (unsigned long)vt, slot, (unsigned long)cur, (unsigned long)expect); return 0; }
    *real = (void *)(DWORD_PTR)KLH_VA(expect);
    if (!klh_poke(e, &cur, 4, &m, 4, what)) { klog("probe: %s: vtable entry not changed (refused? needs [KLHook] SessionSafe=0)", what); *real = 0; return 0; }
    klog("probe: %s wrapped (vtable %08lx slot %d, was %08lx)", what, (unsigned long)vt, slot, (unsigned long)cur);
    return 1;
}

static void klpr_init_all(void)
{
    klpr.on = GetPrivateProfileIntA("Probe", "DoorProxy", 0, klh_ini) != 0;
    if (!klpr.on) return;                              /* Probe off: nothing below runs, nothing is written */
    klpr.all = GetPrivateProfileIntA("Probe", "DoorAll", 0, klh_ini) != 0;
    klpr.leaves = GetPrivateProfileIntA("Probe", "DoorLeaves", 0, klh_ini) != 0;       /* TEST diagnostics: position / state samples of the proxy's controllers */
    if (!klh_exe_ok) { klog("probe: DoorProxy: not the known kl2.exe - off"); klpr.on = 0; return; }
    klpr_dc_ms = GetPrivateProfileIntA("Join", "DoorCloseMs", GetPrivateProfileIntA("KLHook", "DoorCloseMs", 0, klh_ini), klh_ini);
    if (klpr_dc_ms < 0 || klpr_dc_ms > 120000) klpr_dc_ms = 0;
    klog("doorclose: [KLHook] DoorCloseMs=%d (%s)", klpr_dc_ms, klpr_dc_ms ? "doors are closed again that many ms after they opened, never while a player is at the car" : "off");
    klog("probe: DoorProxy on (%s), DoorLeaves %s", klpr.all ? "all names" : "names with Elevator/Escape/VideoProxy/Exit, or unreadable", klpr.leaves ? "on" : "off");
    klpr_wrap(KLPR_VT_PROXY, 14, KLPR_INIT_VA, (void *)klpr_init, (void **)&klpr.real_init, "ZMatPosAnimProxy init");
    klpr_wrap(KLPR_VT_PROXY, 26, KLPR_HAND_VA, (void *)klpr_hand, (void **)&klpr.real_hand, "ZMatPosAnimProxy handler");
    klpr_wrap(KLPR_VT_BOX, 34, KLPR_FIRE_VA, (void *)klpr_fire, (void **)&klpr.real_fire, "ZTriggerBox fire");
}
