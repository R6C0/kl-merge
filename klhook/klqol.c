/*
 * klqol.c - [QoL] small quality-of-life helpers for the PC player. Part of KLHook (included by klhook.c after
 * kllobby.c, SHIP and TEST alike). Win32 only: no byte of kl2.exe is written, no game routine is called; it reads
 * three session dwords that kllobby.c / klnet.c already read. Every key defaults to the game as it is.
 *
 * WHY (collected 2026-10-23 from re/open_work_log.md and the owner's play notes; the owner switches to the browser
 * or a second instance during the 60..120 s loads and the lobby countdown, and the game gives no sign when it is
 * ready; a window left in the background keeps rendering at full speed and holds the mouse clip):
 *   1. FlashOnReady - the game's taskbar button flashes (until the window is in front) when
 *        a. a level load ended (the main loop was silent for >= LoadGapMs, then ticks again), or
 *        b. an FA lobby (game type 4, role host/client) enters state 0xd (the 15 s start countdown; kllobby.c's reading), or
 *        c. the session reaches state 0x28 (SESSION END, klsteam.c's reading): the round is over.
 *      Only while another program is in front. Cheap: one foreground check per tick.
 *   2. BackgroundMs - while another program is in front, game-thread ticks sleep this many ms (a frame
 *      cap in the background; 33 = ~30 fps). LOCAL sessions only (net role 0/1, and not in or entering a type 4
 *      lobby): in a hosted or joined game a slept frame would starve the peers, so there it does nothing.
 *   3. ReleaseCursor - ClipCursor(NULL) once, when the game window loses the foreground (a window that clipped the
 *      mouse to itself and is then left with Alt+Tab or a second monitor click keeps the cursor caged otherwise).
 *
 * KLHook.ini
 *   [QoL]
 *   FlashOnReady=0   1 = the taskbar flashes on the three events above while the game is not in front
 *   LoadGapMs=3000   a main-loop silence this long (500..60000) counts as a finished load
 *   BackgroundMs=0   0 = off; 1..200 = ms slept per game tick while another program is in front (local sessions only)
 *   ReleaseCursor=0  1 = the mouse clip is released when the game loses the foreground
 *   Log=1            0 = no 'qol:' lines
 *
 * GUESSES (nothing here has run in the game):
 *   - GUESS: the main loop is silent for the whole of a level load (klhook.c's tick comment: "the main loop stands still");
 *     the load's own pump may call the tick from the loader's SteamAPI_RunCallbacks sites, which are not game_thread
 *     ticks, so the gap is measured between game_thread ticks only. A minimized/stalled window or a debugger pause also
 *     makes such a gap (only logged and flashed when FlashOnReady=1).
 *   - GUESS: state 0xd only occurs in the lobby countdown of game type 4 (kllobby.c: "in 0xd a 15 s countdown runs").
 *   - GUESS: ClipCursor(NULL) once on losing focus sticks (the game may re-clip every frame).
 *   - GUESS: a Sleep on the game thread is harmless for local sessions (see the gate in klq2_tick).
 *   - The game window is klh_uia_wnd (NoUIA's find) or the first visible window of the main-loop thread with a client area
 *     >= 640x400 (the same pick as klh_uia_pick), looked up again every 5 s and when FlashWindowEx fails. If none: skipped, logged once.
 */
#ifndef KLQOL_C
#define KLQOL_C

static DWORD klh_main_tid;                            /* defined in klhook.c (tentative here, as klslot.c does) */
static HWND klh_uia_wnd;                              /* likewise: the window NoUIA subclassed */

static struct {
    int flash, gap_ms, bg_ms, rel_cur, log;
    int ok;                                           /* the user32 functions were found */
    int resolved;                                     /* klq2_resolve ran (or nothing is asked for: it never will) */
    DWORD last_tick;                                  /* the previous game-thread tick */
    DWORD state_prev;
    DWORD win_at, sleep_at;                           /* when the window was last looked for / the last background sleep */
    int was_front, told_nowin;
    HWND win;
    DWORD flashes, slept;
    BOOL  (WINAPI *p_enum)(DWORD, WNDENUMPROC, LPARAM);
    BOOL  (WINAPI *p_rect)(HWND, LPRECT);
    DWORD (WINAPI *p_tid)(HWND, LPDWORD);
    BOOL  (WINAPI *p_vis)(HWND);
    HWND  (WINAPI *p_fg)(void);
    BOOL  (WINAPI *p_flash)(PFLASHWINFO);
    BOOL  (WINAPI *p_clip)(const RECT *);
} klq2;

static BOOL CALLBACK klq2_enum(HWND h, LPARAM lp)
{   /* the same pick as klhook.c's klh_uia_pick: visible, client area >= 640x400 */
    RECT r; (void)lp;
    if (!klq2.p_vis(h) || !klq2.p_rect(h, &r) || r.right - r.left < 640 || r.bottom - r.top < 400) return TRUE;
    klq2.win = h;
    return FALSE;
}

static int klq2_front(void)
{   /* 1 = a window of this process is in front (0 when nothing is: the desktop, another program) */
    DWORD pid = 0; HWND f = klq2.p_fg();
    if (!f) return 0;
    klq2.p_tid(f, &pid);
    return pid == GetCurrentProcessId();
}

static void klq2_flash(const char *why)
{
    FLASHWINFO fi; DWORD now = GetTickCount();
    /* the window the NoUIA subclass already found wins; otherwise the main-loop thread's own windows, looked up again every 5 s */
    if (klh_uia_wnd) klq2.win = klh_uia_wnd;
    else if (!klq2.win || now - klq2.win_at >= 5000) { klq2.win = 0; if (klh_main_tid) klq2.p_enum(klh_main_tid, klq2_enum, 0); klq2.win_at = now; }
    if (!klq2.win) { if (!klq2.told_nowin++) klog("qol: no game window found - the taskbar flash is skipped"); return; }
    memset(&fi, 0, sizeof fi);
    fi.cbSize = sizeof fi; fi.hwnd = klq2.win;
    fi.dwFlags = 0x3 /* FLASHW_ALL */ | 0xC /* FLASHW_TIMERNOFG: until the window is in front */;
    fi.uCount = 8;
    if (!klq2.p_flash(&fi)) { klq2.win = 0; return; }       /* a stale handle: found again next time */
    klq2.flashes++;
    if (klq2.log) klog("qol: taskbar flash (%s), #%lu", why, klq2.flashes);
}

static void klq2_resolve(void)
{   /* lazily, on the first game tick (not under DllMain's loader lock); LoadLibrary as a fallback if user32 is somehow not there */
    HMODULE u = GetModuleHandleA("user32.dll");
    if (!u) u = LoadLibraryA("user32.dll");
    klq2.resolved = 1;
    if (u) {
        klq2.p_enum = (BOOL (WINAPI *)(DWORD, WNDENUMPROC, LPARAM))GetProcAddress(u, "EnumThreadWindows");
        klq2.p_rect = (BOOL (WINAPI *)(HWND, LPRECT))GetProcAddress(u, "GetClientRect");
        klq2.p_tid = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
        klq2.p_vis = (BOOL (WINAPI *)(HWND))GetProcAddress(u, "IsWindowVisible");
        klq2.p_fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
        klq2.p_flash = (BOOL (WINAPI *)(PFLASHWINFO))GetProcAddress(u, "FlashWindowEx");
        klq2.p_clip = (BOOL (WINAPI *)(const RECT *))GetProcAddress(u, "ClipCursor");
    }
    klq2.ok = klq2.p_enum && klq2.p_rect && klq2.p_tid && klq2.p_vis && klq2.p_fg && klq2.p_flash && klq2.p_clip;
    if (!klq2.ok) { klog("qol: user32 functions not found - [QoL] does nothing"); return; }
    klog("qol: FlashOnReady=%d (LoadGapMs=%d) BackgroundMs=%d ReleaseCursor=%d", klq2.flash, klq2.gap_ms, klq2.bg_ms, klq2.rel_cur);
}

static void klq2_init(void)
{   /* ini only: runs from DllMain, so nothing is resolved here */
    klq2.flash = GetPrivateProfileIntA("QoL", "FlashOnReady", 0, klh_ini) != 0;
    klq2.gap_ms = GetPrivateProfileIntA("QoL", "LoadGapMs", 3000, klh_ini);
    if (klq2.gap_ms < 500 || klq2.gap_ms > 60000) klq2.gap_ms = 3000;
    klq2.bg_ms = GetPrivateProfileIntA("QoL", "BackgroundMs", 0, klh_ini);
    if (klq2.bg_ms < 0 || klq2.bg_ms > 200) klq2.bg_ms = 0;
    klq2.rel_cur = GetPrivateProfileIntA("QoL", "ReleaseCursor", 0, klh_ini) != 0;
    klq2.log = GetPrivateProfileIntA("QoL", "Log", 1, klh_ini) != 0;
    klq2.resolved = (!klq2.flash && !klq2.bg_ms && !klq2.rel_cur);     /* nothing asked for: never resolved, ok stays 0 */
}

static void klq2_tick(int game_thread)
{
    DWORD now, role = 0, mode = 0, state = 0, sm; int front;
    if (!game_thread) return;
    if (!klq2.resolved) klq2_resolve();
    if (!klq2.ok) return;
    now = GetTickCount();
    front = klq2_front();
    /* a. a level load ended: the main loop was silent, now it ticks again */
    if (klq2.last_tick && now - klq2.last_tick >= (DWORD)klq2.gap_ms && klq2.flash) {
        if (klq2.log) klog("qol: main loop silent for %lu ms - a load ended? (game in front: %s)", now - klq2.last_tick, front ? "yes" : "no");
        if (!front) klq2_flash("level loaded");
    }
    klq2.last_tick = now;
    /* 3. the mouse clip is released once, on the way out of the foreground */
    /* GUESS: one ClipCursor(NULL) sticks; if the game re-clips every frame the live test (step 3) shows the clip back at once */
    if (klq2.rel_cur && klq2.was_front && !front) { klq2.p_clip(NULL); if (klq2.log) klog("qol: game left the foreground - mouse clip released"); }
    klq2.was_front = front;
    /* b. / c. session states (reads only; the same dwords kllobby.c reads). The class is checked as kllobby.c does: fail closed. */
    sm = klh_exe_ok ? klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)) : 0;
    if (sm && KLH_SM_VT_OK(klh_rd32(sm)) /* ZSessionManagerMultiplayer */
        && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4)) {
        if (state != klq2.state_prev) {
            if (klq2.flash && !front) {
                /* GUESS: 0xd is the FA lobby countdown; role >= 2 (host/client) so a local game type 4 cannot flash */
                if (mode == 4 && state == 0xd && role >= 2) klq2_flash("lobby countdown");
                else if (state == 0x28) klq2_flash("session end");
            }
            klq2.state_prev = state;
        }
        /* 2. background frame cap, local sessions only (role 0 / 1; 2 = host, 3 = client: peers would starve).
           GUESS: a Sleep on the game thread also delays SteamAPI_RunCallbacks work. Role 0/1 is still reported while a local
           session turns into a lobby, so a type 4 session at state >= 0xd (in or entering a lobby) is excluded too, and sleeps
           are spaced >= 10 ms apart so the extra klh_tick(1) calls of the load pumps cannot stack them. */
        if (klq2.bg_ms && !front && role < 2 && !(mode == 4 && state >= 0xd) && now - klq2.sleep_at >= 10) {
            Sleep(klq2.bg_ms);
            klq2.sleep_at = GetTickCount();
            if (!klq2.slept++ && klq2.log) klog("qol: game in the background - %d ms slept per tick (local session)", klq2.bg_ms);
        }
    }
}

#endif /* KLQOL_C */
