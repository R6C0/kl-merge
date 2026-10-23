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
 *        b. an FA lobby (game type 4) enters state 0xd (the 15 s start countdown; kllobby.c's reading), or
 *        c. the session reaches state 0x28 (SESSION END, klsteam.c's reading): the round is over.
 *      Only while another program is in front. Cheap: one foreground check per tick.
 *   2. BackgroundMs - while another program is in front, every game-thread tick sleeps this many ms (a frame
 *      cap in the background; 33 = ~30 fps). LOCAL sessions only (net role 0/1): in a hosted or joined game a
 *      slept frame would starve the peers, so there it does nothing.
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
 *     ticks, so the gap is measured between game_thread ticks only.
 *   - GUESS: state 0xd only occurs in the lobby countdown of game type 4 (kllobby.c: "in 0xd a 15 s countdown runs").
 *   - GUESS: a process-owned visible top-level window without an owner is the game window (EnumWindows below; the
 *     Steam overlay and the console window are owned or invisible). If none is found the flash is skipped and logged once.
 */
#ifndef KLQOL_C
#define KLQOL_C

static struct {
    int flash, gap_ms, bg_ms, rel_cur, log;
    int ok;                                           /* the user32 functions were found */
    DWORD last_tick;                                  /* the previous game-thread tick */
    DWORD state_prev;
    int was_front, told_nowin;
    HWND win;
    DWORD flashes, slept;
    BOOL  (WINAPI *p_enum)(WNDENUMPROC, LPARAM);
    DWORD (WINAPI *p_tid)(HWND, LPDWORD);
    BOOL  (WINAPI *p_vis)(HWND);
    HWND  (WINAPI *p_getwin)(HWND, UINT);
    HWND  (WINAPI *p_fg)(void);
    BOOL  (WINAPI *p_flash)(PFLASHWINFO);
    BOOL  (WINAPI *p_clip)(const RECT *);
} klq2;

static BOOL CALLBACK klq2_enum(HWND h, LPARAM lp)
{
    DWORD pid = 0; (void)lp;
    klq2.p_tid(h, &pid);
    if (pid != GetCurrentProcessId() || !klq2.p_vis(h) || klq2.p_getwin(h, 4 /* GW_OWNER */)) return TRUE;
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
    FLASHWINFO fi;
    if (!klq2.win) klq2.p_enum(klq2_enum, 0);
    if (!klq2.win) { if (!klq2.told_nowin++) klog("qol: no game window found - the taskbar flash is skipped"); return; }
    memset(&fi, 0, sizeof fi);
    fi.cbSize = sizeof fi; fi.hwnd = klq2.win;
    fi.dwFlags = 0x3 /* FLASHW_ALL */ | 0xC /* FLASHW_TIMERNOFG: until the window is in front */;
    fi.uCount = 8;
    if (!klq2.p_flash(&fi)) { klq2.win = 0; return; }       /* a stale handle: found again next time */
    klq2.flashes++;
    if (klq2.log) klog("qol: taskbar flash (%s), #%lu", why, klq2.flashes);
}

static void klq2_init(void)
{
    HMODULE u = GetModuleHandleA("user32.dll");
    klq2.flash = GetPrivateProfileIntA("QoL", "FlashOnReady", 0, klh_ini) != 0;
    klq2.gap_ms = GetPrivateProfileIntA("QoL", "LoadGapMs", 3000, klh_ini);
    if (klq2.gap_ms < 500 || klq2.gap_ms > 60000) klq2.gap_ms = 3000;
    klq2.bg_ms = GetPrivateProfileIntA("QoL", "BackgroundMs", 0, klh_ini);
    if (klq2.bg_ms < 0 || klq2.bg_ms > 200) klq2.bg_ms = 0;
    klq2.rel_cur = GetPrivateProfileIntA("QoL", "ReleaseCursor", 0, klh_ini) != 0;
    klq2.log = GetPrivateProfileIntA("QoL", "Log", 1, klh_ini) != 0;
    if (!klq2.flash && !klq2.bg_ms && !klq2.rel_cur) return;
    if (u) {
        klq2.p_enum = (BOOL (WINAPI *)(WNDENUMPROC, LPARAM))GetProcAddress(u, "EnumWindows");
        klq2.p_tid = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
        klq2.p_vis = (BOOL (WINAPI *)(HWND))GetProcAddress(u, "IsWindowVisible");
        klq2.p_getwin = (HWND (WINAPI *)(HWND, UINT))GetProcAddress(u, "GetWindow");
        klq2.p_fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
        klq2.p_flash = (BOOL (WINAPI *)(PFLASHWINFO))GetProcAddress(u, "FlashWindowEx");
        klq2.p_clip = (BOOL (WINAPI *)(const RECT *))GetProcAddress(u, "ClipCursor");
    }
    klq2.ok = klq2.p_enum && klq2.p_tid && klq2.p_vis && klq2.p_getwin && klq2.p_fg && klq2.p_flash && klq2.p_clip;
    if (!klq2.ok) { klog("qol: user32 functions not found - [QoL] does nothing"); return; }
    klog("qol: FlashOnReady=%d (LoadGapMs=%d) BackgroundMs=%d ReleaseCursor=%d", klq2.flash, klq2.gap_ms, klq2.bg_ms, klq2.rel_cur);
}

static void klq2_tick(int game_thread)
{
    DWORD now, role = 0, mode = 0, state = 0, sm; int front;
    if (!klq2.ok || !game_thread) return;
    now = GetTickCount();
    front = klq2_front();
    /* a. a level load ended: the main loop was silent, now it ticks again */
    if (klq2.last_tick && now - klq2.last_tick >= (DWORD)klq2.gap_ms) {
        if (klq2.log) klog("qol: main loop silent for %lu ms - a load ended (game in front: %s)", now - klq2.last_tick, front ? "yes" : "no");
        if (klq2.flash && !front) klq2_flash("level loaded");
    }
    klq2.last_tick = now;
    /* 3. the mouse clip is released once, on the way out of the foreground */
    if (klq2.rel_cur && klq2.was_front && !front) { klq2.p_clip(NULL); if (klq2.log) klog("qol: game left the foreground - mouse clip released"); }
    klq2.was_front = front;
    /* b. / c. session states (reads only; the same dwords kllobby.c reads) */
    sm = klh_exe_ok ? klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)) : 0;
    if (sm && klh_rd(sm + 0x54, &role, 4) && klh_rd(sm + 0x5c, &mode, 4) && klh_rd(sm + 0x70, &state, 4)) {
        if (state != klq2.state_prev) {
            if (klq2.flash && !front) {
                if (mode == 4 && state == 0xd) klq2_flash("lobby countdown");
                else if (state == 0x28) klq2_flash("session end");
            }
            klq2.state_prev = state;
        }
        /* 2. background frame cap, local sessions only (role 0 / 1; 2 = host, 3 = client: peers would starve) */
        if (klq2.bg_ms && !front && role < 2) {
            Sleep(klq2.bg_ms);
            if (!klq2.slept++ && klq2.log) klog("qol: game in the background - %d ms slept per tick (local session)", klq2.bg_ms);
        }
    }
}

#endif /* KLQOL_C */
