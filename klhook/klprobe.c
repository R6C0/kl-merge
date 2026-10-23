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
 * KEYS ([Probe]): DoorProxy=0  DoorAll=0
 */
#define KLPR_VT_PROXY  0x00bc36bc
#define KLPR_VT_BOX    0x00bc232c
#define KLPR_INIT_VA   0x004093c0
#define KLPR_HAND_VA   0x007ed520
#define KLPR_FIRE_VA   0x0045f5d0

typedef DWORD (__fastcall *klpr_0_fn)(void *self, void *edx);
typedef DWORD (__fastcall *klpr_2_fn)(void *self, void *edx, DWORD a1, DWORD a2);

static struct { int on, all; volatile LONG ni, nh, nb; klpr_0_fn real_init, real_fire; klpr_2_fn real_hand; } klpr;

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
    if (!klh_exe_ok) { klog("probe: DoorProxy: not the known kl2.exe - off"); klpr.on = 0; return; }
    klog("probe: DoorProxy on (%s)", klpr.all ? "all names" : "names with Elevator/Escape/VideoProxy/Exit, or unreadable");
    klpr_wrap(KLPR_VT_PROXY, 14, KLPR_INIT_VA, (void *)klpr_init, (void **)&klpr.real_init, "ZMatPosAnimProxy init");
    klpr_wrap(KLPR_VT_PROXY, 26, KLPR_HAND_VA, (void *)klpr_hand, (void **)&klpr.real_hand, "ZMatPosAnimProxy handler");
    klpr_wrap(KLPR_VT_BOX, 34, KLPR_FIRE_VA, (void *)klpr_fire, (void **)&klpr.real_fire, "ZTriggerBox fire");
}
