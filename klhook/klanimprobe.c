/*
 * klanimprobe.c - [AnimProbe] LOG-ONLY probe of the animation Play (0x4da1d0) around the local player's gait changes, 2026-10-24.
 * Part of KLHook (included by klhook.c right after klcamsmooth.c: uses klh_rd / klh_rd32 / klh_poke / klcam_player / klog / klh_ini).
 * NOTHING HERE HAS RUN IN THE GAME. It changes nothing: every call passes through to the game's own Play with the same arguments;
 * the only thing written is the 5-byte jump at the top of Play (and, while a line is being logged, the return address of that one
 * call, which points at our stub that logs and returns to the real caller).
 *
 * WHY (re/player_anim_blend.md, owner: "one second he's crouched, next frame he's just straight running"): BaseMove 0x7a43e0 commits
 * a gait after a 1-frame debounce and writes the new loop clip into [mover+0x58], but the visible pose comes from a Play through the
 * channel mixer, and the caller of that Play was not pinned statically. This logs, for the local player's objects only and only
 * within [AnimProbe] Ms around a gait/mode change: this, clip, flags (bit0 stops same-class channels = hard cut, bit1 = snap),
 * the clip record's +0x14 (blend time, /1024 per the doc), the return address (the CALLER), and the channel's +0x3c/+0x40 after return.
 *
 * PATCH SITE 0x4da1d0 (thiscall, args on the stack: clip, flags, startFrame, endFrame, speed). Prologue read from the exe FILE
 * (2026-10-24, kl2.exe build 0490): 83 ec 50 | 55 | 8b 6c 24 58 = sub esp,50h; push ebp; mov ebp,[esp+58h] - 8 bytes, whole
 * instructions, none position dependent, so they are re-executed in the stub and the jump goes back to 0x4da1d8. klh_poke compares
 * the live bytes with these eight and writes only if they match (otherwise: a log line, nothing patched, the game untouched).
 * POLICY: 0x4da1d0 is NOT inside a hashed range (klranges.h), so a TEST build with SessionSafe=1 may patch it; the SHIP build
 * refuses ("code or constants: a ship build writes import slots and data only") and this probe then logs that and does nothing.
 * Whether an unhashed .text byte survives a real session is only shown for five other detours (X3 runs): treat as NOT LIVE-TESTED.
 *
 * WHAT IS READ (all read-only through klh_rd, which cannot fault; every read is a GUESS where marked):
 *   player P = klcam_player(); the mover = [P+0x63c] (BaseMove is movement number 3 at [P+0x630+4*3], re/climb.md); the gait
 *   signature = ([mover+0x58] current loop clip, [mover+0x1e5c], [P+0x6b4] the current movement) - the two mover fields are the
 *   ones 0x5abbb0 writes at the commit (player_anim_blend.md). A change of the signature opens the window and dumps the last 16 Play
 *   calls of the player (ring, PRE data only: their post data is unknown).
 *   clip: GUESS that the first argument is a pointer to the clip record (climb.md: "clip event table = ...+[clip+0x10]", "[clip+6]
 *   entries"); a value below 0x10000 is shown as a plain id. Record +0x14 = blend time (player_anim_blend.md, GUESS for the width: shown
 *   as one dword and as the float it would be). The record's first bytes are dumped for the first calls (the name is not known).
 *   channel after return: GUESS that Play returns the channel index (0..15) in eax; if not, the channel whose +0 equals the clip is
 *   used (last match). Channel i is at [P+0x70]+0x1c+0x38*i (climb.md); +0x3c / +0x40 are read FROM THE CHANNEL START as the task asked
 *   (that is inside the next channel's block if the stride is 0x38 - the doc calls them "in the pool": GUESS, so the whole 0x38 channel
 *   is dumped for the first calls too).
 * The stub keeps a LIFO of 8 pending returns and drops an entry older than 5 s; only the game thread (the thread klh_tick runs on) is handled.
 *
 * KEYS ([AnimProbe]): Enable=0 (default OFF; diagnostic)  Ms=600 (window around a change, 100..5000)  MaxLines=400 (cap of all lines, 20..5000)
 * LOG LINES: "animprobe: ..." - CHANGE (the gait signature moved), RING (a call before the change), PLAY (a call in the window),
 *   RET (its channel after the return), WINDOW END (a count). The log says "NOT made"/"prologue differs" when the patch is not made.
 */
#define KLAP_SITE   0x004da1d0
#define KLAP_STOLEN 8
#define KLAP_RING   16
#define KLAP_PEND   8

typedef struct { DWORD t, thisp, clip, flags, caller, blend; } klap_e;
static struct {
    int on, installed, dead, window_open, havesig, lines, ncalls, nwin;
    DWORD ms, maxl, tid, until, t0;
    DWORD sig[3];
    klap_e ring[KLAP_RING]; int rn;
    klap_e pend[KLAP_PEND]; int np;
} klap;
static DWORD klap_back;                                   /* 0x4da1d8: where the stolen prologue returns to */

static void klap_say(const char *fmt, ...)
{
    char b[600]; va_list a;
    if ((DWORD)klap.lines >= klap.maxl) return;
    klap.lines++;
    va_start(a, fmt); _vsnprintf(b, sizeof b - 1, fmt, a); va_end(a); b[sizeof b - 1] = 0;
    klog("animprobe: %s", b);
    if ((DWORD)klap.lines == klap.maxl) klog("animprobe: line cap (MaxLines=%lu) reached - silent from here", (unsigned long)klap.maxl);
}

static float klap_f(DWORD v) { float f; memcpy(&f, &v, 4); return f; }

/* the record's blend dword (+0x14) of a clip argument, 0 if the argument is not a readable pointer (GUESS: a pointer to the record) */
static DWORD klap_blend(DWORD clip, int *ok)
{
    DWORD v = 0;
    *ok = clip >= 0x10000 && klh_rd(clip + 0x14, &v, 4);
    return *ok ? v : 0;
}

static void klap_head(DWORD clip)
{
    BYTE h[32]; char s[100]; int i;
    if (clip < 0x10000 || !klh_rd(clip, h, sizeof h)) return;
    for (i = 0; i < 32; i++) sprintf(s + i * 3, "%02x ", h[i]);
    klap_say("   clip record head: %s", s);
}

/* the gait signature; true when it differs from the last one seen (the first sight only records it) */
static int klap_watch(DWORD P, DWORD now)
{
    DWORD m = klh_rd32(P + 0x63c), s[3];
    s[0] = m ? klh_rd32(m + 0x58) : 0; s[1] = m ? klh_rd32(m + 0x1e5c) : 0; s[2] = klh_rd32(P + 0x6b4);
    if (!klap.havesig) { memcpy(klap.sig, s, sizeof s); klap.havesig = 1; return 0; }
    if (!memcmp(klap.sig, s, sizeof s)) return 0;
    klap_say("CHANGE mover=%08lx clip[+0x58] %08lx->%08lx  [+0x1e5c] %08lx->%08lx  movement[P+0x6b4] %08lx->%08lx  (window %lu ms)",
             (unsigned long)m, (unsigned long)klap.sig[0], (unsigned long)s[0], (unsigned long)klap.sig[1], (unsigned long)s[1],
             (unsigned long)klap.sig[2], (unsigned long)s[2], (unsigned long)klap.ms);
    memcpy(klap.sig, s, sizeof s);
    klap.until = now + klap.ms; klap.window_open = 1; klap.nwin++;
    return 1;
}

static void klap_ringdump(DWORD now)
{
    int i;
    for (i = 0; i < KLAP_RING; i++) {
        klap_e *e = &klap.ring[(klap.rn + i) % KLAP_RING];
        if (!e->t) continue;
        klap_say("RING -%lu ms: clip=%08lx flags=%08lx blend(rec+0x14)=%08lx caller=%08lx", (unsigned long)(now - e->t), (unsigned long)e->clip,
                 (unsigned long)e->flags, (unsigned long)e->blend, (unsigned long)e->caller);
    }
}

void klap_post_stub(void);

/* called by the stub on entry of Play: thisp = ecx, sp -> the return address slot, sp[1..5] = clip, flags, start, end, speed */
static void __cdecl klap_pre(DWORD thisp, DWORD *sp)
{
    __try {
        DWORD now, P, gd = 0, clip, flags, caller; int ok;
        if (!klap.on || klap.dead || GetCurrentThreadId() != klap.tid) return;
        if (!(P = klcam_player(&gd)) || thisp != P) return;
        now = GetTickCount(); clip = sp[1]; flags = sp[2]; caller = sp[0];
        klap.ncalls++;
        if (klap_watch(P, now)) klap_ringdump(now);
        { klap_e *e = &klap.ring[klap.rn]; klap.rn = (klap.rn + 1) % KLAP_RING;
          e->t = now ? now : 1; e->thisp = thisp; e->clip = clip; e->flags = flags; e->caller = caller; e->blend = klap_blend(clip, &ok); }
        if (klap.window_open && (int)(now - klap.until) > 0) {
            klap.window_open = 0; klap_say("WINDOW END (%d Play calls of the player seen in all)", klap.ncalls);
        }
        if (!klap.window_open || (DWORD)klap.lines >= klap.maxl) return;
        { DWORD blend = klap_blend(clip, &ok), m = klh_rd32(P + 0x63c);
          klap_say("PLAY this=%08lx clip=%08lx%s flags=%08lx (bit0 stop-same-class=%d, bit1 snap=%d) start=%ld end=%ld speed=%.3f blend(rec+0x14)=%s%08lx (as float %.4f) caller=%08lx mover[+0x58]=%08lx",
                 (unsigned long)thisp, (unsigned long)clip, clip < 0x10000 ? "(id?)" : "", (unsigned long)flags, (int)(flags & 1), (int)((flags >> 1) & 1),
                 (long)sp[3], (long)sp[4], klap_f(sp[5]), ok ? "" : "n/a ", (unsigned long)blend, klap_f(blend), (unsigned long)caller,
                 (unsigned long)(m ? klh_rd32(m + 0x58) : 0));
          if (klap.ncalls <= 40) klap_head(clip); }
        /* hook the return: remember it, point it at the post stub */
        if (klap.np && klap.pend[klap.np - 1].t && now - klap.pend[klap.np - 1].t > 5000) klap.np = 0;     /* stale entries from a return that never came */
        if (klap.np < KLAP_PEND) {
            klap_e *e = &klap.pend[klap.np++];
            e->t = now ? now : 1; e->thisp = thisp; e->clip = clip; e->flags = flags; e->caller = caller;
            sp[0] = (DWORD)(DWORD_PTR)klap_post_stub;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        klap.dead = 1;
    }
}

/* called by the post stub: ret = eax of Play, slot -> where the stub's `ret` will read the real return address from */
static void __cdecl klap_post(DWORD ret, DWORD *slot)
{
    DWORD back = 0;
    __try {
        klap_e e; DWORD P, gd = 0, pool, ch = 0, w[0x12]; int i, idx = -1; const char *by = "eax";
        memset(&e, 0, sizeof e);
        if (klap.np > 0) { e = klap.pend[--klap.np]; back = e.caller; }
        else { klap.dead = 1; klog("animprobe: post stub with an empty pending list - probe stops"); }
        if (back && (P = klcam_player(&gd)) && (pool = klh_rd32(P + 0x70))) {
            if (ret < 16) idx = (int)ret;
            else { by = "scan(clip)"; for (i = 0; i < 16; i++) if (klh_rd32(pool + 0x1c + 0x38 * i) == e.clip) idx = i; }
            if (idx >= 0) {
                ch = pool + 0x1c + 0x38 * idx;
                if (klh_rd(ch, w, sizeof w)) {
                    klap_say("RET  eax=%08lx channel=%d (by %s) at %08lx: +0=%08lx +4=%08lx flags[+0x14]=%08lx id[+0x18]=%08lx  +0x3c=%08lx (%.4f) +0x40=%08lx (%.4f)",
                             (unsigned long)ret, idx, by, (unsigned long)ch, (unsigned long)w[0], (unsigned long)w[1], (unsigned long)w[5], (unsigned long)w[6],
                             (unsigned long)w[0xf], klap_f(w[0xf]), (unsigned long)w[0x10], klap_f(w[0x10]));
                    if (klap.ncalls <= 40) {
                        char s[200]; int k; s[0] = 0;
                        for (k = 0; k < 14; k++) sprintf(s + strlen(s), "%08lx ", (unsigned long)w[k]);
                        klap_say("   channel dwords +0..+0x34: %s", s);
                    }
                }
            } else klap_say("RET  eax=%08lx: no channel found (eax not an index 0..15 and no channel holds clip %08lx)", (unsigned long)ret, (unsigned long)e.clip);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        klap.dead = 1;
    }
    *slot = back;       /* only klap_pre fills the pending list, always with a real return address, so back is never 0 here */
}

/* the stub at the top of Play (entered by the 5-byte jump): save, call klap_pre(ecx, &retaddr), restore, run the stolen prologue, go on */
static void __declspec(naked) klap_hook(void)
{
    __asm {
        pushfd
        pushad
        lea eax, [esp + 0x24]
        push eax
        push ecx
        call klap_pre
        add esp, 8
        popad
        popfd
        sub esp, 0x50
        push ebp
        mov ebp, dword ptr [esp + 0x58]
        jmp dword ptr [klap_back]
    }
}

/* Play returns here when klap_pre replaced the return address */
void __declspec(naked) klap_post_stub(void)
{
    __asm {
        push 0
        pushfd
        pushad
        lea ecx, [esp + 0x24]
        mov eax, dword ptr [esp + 0x1c]
        push ecx
        push eax
        call klap_post
        add esp, 8
        popad
        popfd
        ret
    }
}

static void klap_tick(int game_thread)
{
    DWORD P, gd = 0, now;
    if (!klap.on || !game_thread || klap.dead) return;
    klap.tid = GetCurrentThreadId();
    if (!klap.installed || !klx_on) return;
    if (!(P = klcam_player(&gd))) { klap.havesig = 0; return; }
    now = GetTickCount();
    if (klap_watch(P, now)) klap_ringdump(now);
    if (klap.window_open && (int)(now - klap.until) > 0) { klap.window_open = 0; klap_say("WINDOW END (%d Play calls of the player seen in all)", klap.ncalls); }
}

static void klap_init(void)
{
    BYTE site[KLAP_STOLEN], jmp[KLAP_STOLEN]; DWORD rel;
    static const BYTE expect[KLAP_STOLEN] = { 0x83, 0xec, 0x50, 0x55, 0x8b, 0x6c, 0x24, 0x58 };
    klap.on = GetPrivateProfileIntA("AnimProbe", "Enable", 0, klh_ini) != 0;
    klap.ms = (DWORD)GetPrivateProfileIntA("AnimProbe", "Ms", 600, klh_ini);
    if (klap.ms < 100) klap.ms = 100;
    if (klap.ms > 5000) klap.ms = 5000;
    klap.maxl = (DWORD)GetPrivateProfileIntA("AnimProbe", "MaxLines", 400, klh_ini);
    if (klap.maxl < 20) klap.maxl = 20;
    if (klap.maxl > 5000) klap.maxl = 5000;
    if (!klap.on) return;                                            /* off: nothing patched, no log line */
    if (!klh_rd((DWORD_PTR)KLH_VA(KLAP_SITE), site, KLAP_STOLEN)) { klog("animprobe: cannot read 0x4da1d0 - probe off"); klap.on = 0; return; }
    if (memcmp(site, expect, KLAP_STOLEN)) {
        klog("animprobe: prologue at 0x4da1d0 differs from build 0490 (%02x %02x %02x %02x %02x %02x %02x %02x) - NOT patched, probe off",
             site[0], site[1], site[2], site[3], site[4], site[5], site[6], site[7]);
        klap.on = 0; return;
    }
    klap_back = (DWORD)(DWORD_PTR)KLH_VA(KLAP_SITE + KLAP_STOLEN);
    rel = (DWORD)((BYTE *)klap_hook - (KLH_VA(KLAP_SITE) + 5));
    jmp[0] = 0xe9; memcpy(jmp + 1, &rel, 4); jmp[5] = jmp[6] = jmp[7] = 0x90;
    if (!klh_poke(KLH_VA(KLAP_SITE), expect, KLAP_STOLEN, jmp, KLAP_STOLEN, "animprobe: jump at the top of Play 0x4da1d0 (log only)")) {
        klog("animprobe: patch at 0x4da1d0 NOT made (refused by the patch guard - a SHIP build never patches code - or the bytes changed): probe off, game untouched");
        klap.on = 0; return;
    }
    klap.installed = 1;
    klog("animprobe: on (LOG ONLY): Play 0x4da1d0 detoured, passes through; window %lu ms around the local player's gait change, max %lu lines", (unsigned long)klap.ms, (unsigned long)klap.maxl);
}
