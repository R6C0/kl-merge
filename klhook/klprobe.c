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
 *   GUESS (not proven): the controller list = [proxy+0x34], an array of [proxy+0x30] controller pointers; the target node = [e+4] with e =
 *   [[ctrl+0x24]+0x60] (the owner-slot path klpr_name uses), else [ctrl+4]; the position = kle_node (klescort.c: the node's own matrix chain,
 *   scene units - NOT x100); st21 is the byte the RE notes call the controller state (answers GetMatPosAnim in 1..5); raw = ctrl+0x20..0x3c dumped
 *   as is because NO frame / time offset is proven: whichever dword changes between samples is the clip clock. The proxy accept time is also
 *   handed to kljoin.c (klj_door_at, [Join] CarStallAfterDoorMs). With [Probe] DoorAll=0 only Elevator/Escape/VideoProxy/Exit/unreadable proxies count.
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

/* an accepted door proxy: stamp for kljoin.c and (DoorLeaves) start a 6 s sample series for this proxy (4 proxies at most; a re-accept restarts it) */
static void klpr_accepted(DWORD me)
{
    DWORD now = GetTickCount(); int k;
    klj_door_at = now ? now : 1;
    if (!klpr.leaves) return;
    for (k = 0; k < klpr.npr && klpr.pr[k].me != me; k++) ;
    if (k == klpr.npr) {                               /* a new proxy: reuse a finished slot first (rounds / levels re-create proxies at new addresses) */
        int f;
        for (f = 0; f < klpr.npr && klpr.pr[f].at && now - klpr.pr[f].at <= KLLEAF_SPAN_MS + KLLEAF_STEP_MS; f++) ;
        if (f < klpr.npr) k = f; else if (klpr.npr < 4) klpr.npr++; else return;
    }
    klpr.pr[k].at = 0;                                 /* klpr_tick may run on another thread: park the slot while it is rewritten */
    klpr.pr[k].me = me; klpr.pr[k].last = 0; klpr.pr[k].at = klj_door_at;
}

/* one controller of a proxy: one compact line (formats in the header comment) */
static void klpr_leaf_line(DWORD me, DWORD at, int n, int i, DWORD cnt, DWORD ctl)
{
    char b[64]; const char *nm; BYTE st = 0xff; DWORD raw[8], e, slot, node = 0; float pos[3]; int pv = 0, k;
    memset(raw, 0, sizeof raw);
    klh_rd(ctl + 0x21, &st, 1);
    klh_rd(ctl + 0x20, raw, sizeof raw);                                                  /* GUESS range, see the header */
    nm = klpr_name(ctl, b, sizeof b);
    if ((slot = klh_rd32(ctl + 0x24)) != 0 && (e = klh_rd32(slot + 0x60)) != 0) node = klh_rd32(e + 4);       /* GUESS: owner node */
    if (node) pv = kle_node(node, pos, 0);
    if (!pv && (node = klh_rd32(ctl + 4)) != 0) pv = kle_node(node, pos, 0);                                   /* GUESS: fallback */
    if (pv) klog("probe: leaf t=%lu n=%d prox=%08lx i=%d/%lu ctl=%08lx st21=%02x name=%s node=%08lx pos=(%.1f, %.1f, %.1f) raw=%08lx,%08lx,%08lx,%08lx,%08lx,%08lx,%08lx,%08lx",
                 (unsigned long)(GetTickCount() - at), n, (unsigned long)me, i, (unsigned long)cnt, (unsigned long)ctl, (unsigned)st, nm ? nm : "?", (unsigned long)node, pos[0], pos[1], pos[2],
                 (unsigned long)raw[0], (unsigned long)raw[1], (unsigned long)raw[2], (unsigned long)raw[3], (unsigned long)raw[4], (unsigned long)raw[5], (unsigned long)raw[6], (unsigned long)raw[7]);
    else klog("probe: leaf t=%lu n=%d prox=%08lx i=%d/%lu ctl=%08lx st21=%02x name=%s node=%08lx pos=? raw=%08lx,%08lx,%08lx,%08lx,%08lx,%08lx,%08lx,%08lx",
                 (unsigned long)(GetTickCount() - at), n, (unsigned long)me, i, (unsigned long)cnt, (unsigned long)ctl, (unsigned)st, nm ? nm : "?", (unsigned long)node,
                 (unsigned long)raw[0], (unsigned long)raw[1], (unsigned long)raw[2], (unsigned long)raw[3], (unsigned long)raw[4], (unsigned long)raw[5], (unsigned long)raw[6], (unsigned long)raw[7]);
    (void)k;
}

/* called every tick by klhook.c after klj_tick; reads only; costs one compare when no series runs */
static void klpr_tick(void)
{
    int k, i, n; DWORD now, cnt, list, ctl;
    if (!klpr.leaves || !klpr.npr) return;
    now = GetTickCount();
    for (k = 0; k < klpr.npr; k++) {
        if (!(n = klleaf_due(now, klpr.pr[k].at, klpr.pr[k].last))) continue;
        klpr.pr[k].last = n;
        if (klpr.nleaf > 1000) continue;                                                   /* log cap: about 40 series */
        klpr.nleaf++;
        cnt = klh_rd32(klpr.pr[k].me + 0x30); list = klh_rd32(klpr.pr[k].me + 0x34);
        if (cnt > 8) cnt = 8;                                                              /* LIFT9: 5 each */
        if (!list) { klog("probe: leaf t=%lu n=%d prox=%08lx list[+34]=0 count=%lu", (unsigned long)(now - klpr.pr[k].at), n, (unsigned long)klpr.pr[k].me, (unsigned long)cnt); continue; }
        for (i = 0; i < (int)cnt; i++) {
            ctl = klh_rd32(list + 4 * i);                                                  /* GUESS: array of controller pointers */
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
    klog("probe: DoorProxy on (%s), DoorLeaves %s", klpr.all ? "all names" : "names with Elevator/Escape/VideoProxy/Exit, or unreadable", klpr.leaves ? "on" : "off");
    klpr_wrap(KLPR_VT_PROXY, 14, KLPR_INIT_VA, (void *)klpr_init, (void **)&klpr.real_init, "ZMatPosAnimProxy init");
    klpr_wrap(KLPR_VT_PROXY, 26, KLPR_HAND_VA, (void *)klpr_hand, (void **)&klpr.real_hand, "ZMatPosAnimProxy handler");
    klpr_wrap(KLPR_VT_BOX, 34, KLPR_FIRE_VA, (void *)klpr_fire, (void **)&klpr.real_fire, "ZTriggerBox fire");
}
