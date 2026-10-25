/*
 * klnudge.c - experiment E1 of re\loading.md: is the slow load the game's own cursor nudge? Part of KLHook
 * (included by klhook.c, SHIP and TEST alike). One import slot; no code byte and no data of kl2.exe changes.
 * OFF unless KLHook.ini says [Load] NudgeMs=<n>. NOT RUN IN THE GAME YET (2026-10-09).
 *
 * THE GAME (re\loading.md 2, read in kl2.exe): the loader's progress callback, the scene loader, the staged
 * object init and the main loop all call 0x48a1e0 -> 0x82dfb0 -> 0x6f4220, once per load step and once per frame:
 *     h = top-level owner of GetForegroundWindow()
 *     if (h == the game's window) { GetCursorPos(&p); SetCursorPos(p.x, p.y); mouse_event(MOVE, 0, 0, 0, 0); }
 * and then pumps the window messages. GetForegroundWindow (import slot 0xb10594) has ONE reference in the exe,
 * 0x6f422b, so a wrapper on the slot is seen by this routine and nothing else. A load is about 60,000 - 75,000
 * such steps at 1.2 - 1.8 ms each; if the injected mouse event is what costs, most of a load is this.
 *
 * WHAT THE WRAPPER DOES: with NudgeMs = n > 0 it answers NULL (the game then skips the three cursor calls) except
 * once every n ms, when it passes the call on - so the idle-timer reset the nudge was written for still happens
 * about once a second, and SetThreadExecutionState in the same routine is untouched. With NudgeMs = 0 the slot
 * is not wrapped at all: the game as shipped.
 * With Count=1 (and NudgeMs=0) the slot IS wrapped but every call is passed on: the control run with the same
 * log lines.
 *
 * THE LOG (every 10 s while calls come, so a load shows as a burst):
 *     nudge: 10.0 s: 48213 calls (4821 /s), 10 passed on, game window in front at the last one: yes
 * calls /s IS the measurement: load steps per second, with and without the nudge.
 *
 * KLHook.ini
 *   [Load]
 *   NudgeMs=0     0 = off; 1000 = let one nudge a second through (max 86400000; over that = 0)
 *   Count=0       1 = wrap and count without changing anything (control run)
 *   CursorGuard=0 1 = wrap the game's ShowCursor import slot (kl2 0xb10654, read from the PE import table 2026-10-19) so a
 *                 call sequence cannot drive the cursor's display count very negative (below) and a slow sequence is logged
 *
 * CURSOR GUARD (2026-10-19, owner run 13:19:56: the game froze 6.5 s at kl2 0x41e980 = 'push 1; call [ShowCursor];
 * test eax,eax; jle 0x41e980': the game forces the cursor visible by calling ShowCursor(TRUE) until the count is positive,
 * and every call went through the Steam overlay's hook). The loop's length is -count + 1. What the wrapper does:
 *   - it keeps a shadow of the count from the values the real call returns (unknown until the first real call);
 *   - a ShowCursor(FALSE) while the shadow is already at or under KLN_CG_FLOOR (-2) is NOT passed on and answers the shadow:
 *     the count never goes under -2, so the show loop is 3 calls at most (GUESS: that no code of the game counts its own
 *     FALSE calls against its TRUE calls - the loop above suggests it does not rely on it, but nothing else was read);
 *   - ShowCursor(TRUE) is always passed on, as it is;
 *   - a run of ShowCursor(TRUE) calls that lasts over 1 s writes one line with the shadow count and the number of calls, and
 *     another when it ends. The log is the measurement: if the freeze comes back with the guard on, the count was not the cause.
 */
#ifndef KLNUDGE_C
#define KLNUDGE_C

static int kln_ms, kln_count;
static HWND (WINAPI *kln_real)(void);
static DWORD (WINAPI *kln_pid_of)(HWND, LPDWORD);      /* user32's GetWindowThreadProcessId, looked up at init: the hook does not link user32 */
static volatile LONG kln_calls, kln_passed;
static int kln_cg;                                    /* CursorGuard */
static int (WINAPI *kln_real_sc)(BOOL);
#define KLN_CG_FLOOR (-2)                             /* GUESS: the lowest display count the guard lets the game reach */

static HWND WINAPI kln_GetForegroundWindow(void)
{
    static DWORD last, mark; static LONG calls0, passed0; static int front = -1;
    DWORD now = GetTickCount(); HWND h = 0; LONG c = InterlockedIncrement(&kln_calls);
    if (kln_ms && !last) last = now;                  /* the first call is not passed on either: the timer starts here (E0d: the one
                                                         nudge a start passed on reset the solo bench's owner-idle check) */
    if (!kln_ms || now - last >= (DWORD)kln_ms) {
        DWORD pid = 0;
        last = now; h = kln_real(); InterlockedIncrement(&kln_passed);
        if (h && kln_pid_of) { kln_pid_of(h, &pid); front = pid == GetCurrentProcessId(); } else if (!h) front = 0;
    }
    if (!mark) { mark = now; calls0 = c - 1; passed0 = 0; }
    else if (now - mark >= 10000) {
        LONG p = kln_passed;
        klog("nudge: %.1f s: %ld calls (%ld /s), %ld passed on, game window in front at the last one: %s", (now - mark) / 1000.0, c - calls0,
             (long)((c - calls0) * 1000.0 / (now - mark)), p - passed0, front < 0 ? "not asked" : front ? "yes" : "no");
        mark = now; calls0 = c; passed0 = p;
    }
    return h;
}

static int WINAPI kln_ShowCursor(BOOL show)
{
    static int shadow, known, swallowed; static DWORD seq0, seqn; static int told;
    int r;
    if (!show && known && shadow <= KLN_CG_FLOOR) {
        /* k45: 1, 10, 100, 1000, then every 100000 (every 1000 wrote a line about every 5 s of play: the log grew by MBs a night) */
        ++swallowed;
        if (swallowed == 1 || swallowed == 10 || swallowed == 100 || swallowed == 1000 || swallowed % 100000 == 0) klog("cursor: ShowCursor(FALSE) not passed on while the count is %d (floor %d): %d swallowed so far", shadow, KLN_CG_FLOOR, swallowed);
        return shadow;
    }
    r = kln_real_sc(show); shadow = r; known = 1;
    if (show && r <= 0) {                             /* a run of 'show' calls that has not reached a visible cursor yet */
        DWORD now = GetTickCount();
        if (!seqn) { seq0 = now; told = 0; }
        seqn++;
        if (!told && now - seq0 > 1000) { told = 1; klog("cursor: ShowCursor(TRUE) run: %lu calls in %.1f s and the count is still %d (the game's show loop at 0x41e980; each call goes through the overlay)", seqn, (now - seq0) / 1000.0, r); }
    } else {
        if (seqn && told) klog("cursor: ShowCursor run over: %lu calls in %.1f s, count now %d", seqn, (GetTickCount() - seq0) / 1000.0, r);
        seqn = 0;
    }
    return r;
}

static void kln_init(void)
{
    kln_ms = (int)GetPrivateProfileIntA("Load", "NudgeMs", 0, klh_ini); if (kln_ms < 0 || kln_ms > 86400000) kln_ms = 0;   /* up to 24 h: the solo bench passes none on (kl_solo_test.py) */
    kln_count = GetPrivateProfileIntA("Load", "Count", 0, klh_ini);
    HMODULE u;
    kln_cg = GetPrivateProfileIntA("Load", "CursorGuard", 0, klh_ini) != 0;      /* opt-in: 0 = the slot is not touched */
    if (kln_cg) {
        if (klh_iat("USER32.dll", "ShowCursor", (void *)kln_ShowCursor, (void **)&kln_real_sc) && kln_real_sc) klog("cursor: ShowCursor wrapped (CursorGuard=1): the display count is kept at %d or above, slow runs of ShowCursor(TRUE) are logged", KLN_CG_FLOOR);
        else { kln_cg = 0; klog("cursor: ShowCursor NOT wrapped: nothing changes"); }
    }
    if (!kln_ms && !kln_count) return;                /* the game as shipped: the slot is not touched */
    if ((u = GetModuleHandleA("user32.dll")) != 0) kln_pid_of = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
    if (klh_iat("USER32.dll", "GetForegroundWindow", (void *)kln_GetForegroundWindow, (void **)&kln_real) && kln_real)
        klog("nudge: GetForegroundWindow wrapped: %s", kln_ms ? "the game's cursor nudge is let through once per NudgeMs only" : "counting only, every call passed on (control)");
    else { kln_ms = 0; klog("nudge: GetForegroundWindow NOT wrapped: nothing changes"); }
    if (kln_ms) klog("nudge: NudgeMs=%d", kln_ms);
}

#endif /* KLNUDGE_C */
