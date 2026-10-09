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
 *   NudgeMs=0     0 = off; 1000 = let one nudge a second through
 *   Count=0       1 = wrap and count without changing anything (control run)
 */
#ifndef KLNUDGE_C
#define KLNUDGE_C

static int kln_ms, kln_count;
static HWND (WINAPI *kln_real)(void);
static DWORD (WINAPI *kln_pid_of)(HWND, LPDWORD);      /* user32's GetWindowThreadProcessId, looked up at init: the hook does not link user32 */
static volatile LONG kln_calls, kln_passed;

static HWND WINAPI kln_GetForegroundWindow(void)
{
    static DWORD last, mark; static LONG calls0, passed0; static int front = -1;
    DWORD now = GetTickCount(); HWND h = 0; LONG c = InterlockedIncrement(&kln_calls);
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

static void kln_init(void)
{
    kln_ms = (int)GetPrivateProfileIntA("Load", "NudgeMs", 0, klh_ini); if (kln_ms < 0 || kln_ms > 60000) kln_ms = 0;
    kln_count = GetPrivateProfileIntA("Load", "Count", 0, klh_ini);
    HMODULE u;
    if (!kln_ms && !kln_count) return;                /* the game as shipped: the slot is not touched */
    if ((u = GetModuleHandleA("user32.dll")) != 0) kln_pid_of = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
    if (klh_iat("USER32.dll", "GetForegroundWindow", (void *)kln_GetForegroundWindow, (void **)&kln_real) && kln_real)
        klog("nudge: GetForegroundWindow wrapped: %s", kln_ms ? "the game's cursor nudge is let through once per NudgeMs only" : "counting only, every call passed on (control)");
    else { kln_ms = 0; klog("nudge: GetForegroundWindow NOT wrapped: nothing changes"); }
    if (kln_ms) klog("nudge: NudgeMs=%d", kln_ms);
}

#endif /* KLNUDGE_C */
