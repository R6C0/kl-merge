/*
 * klfresh.c - [Memory] FreshRestart: when the game is idle at its menu and has loaded enough levels (or the address space is cut up), kl2.exe is
 * restarted cleanly, so a player never reaches the gray screen of a cut-up 2 GB address space. Part of KLHook (included by klhook.c after
 * klslot.c, SHIP and TEST alike). Writes no code byte; one data byte of the engine (the quit flag, as AutoExit does) and a process start.
 *
 * WHY (KLHook.log 2026-11-10 00:19 - 00:28, klmem.c): a process starts with 1931 MB free and a 512 MB largest piece; back at the menu after ONE
 * match the largest piece is 25 MB, and the third load (DM06B) ran at 1.4 fps for 40 s. LAA is off for good (re/high_half_1025.md), klmem's
 * reserve only moves the damage. A new process has the whole space again. This module makes that new process cost the player as little as
 * possible. Decision logic: klfresh_logic.h (klfresh_test.c).
 *
 * HOW (every step is data-only or an OS call; nothing of kl2.exe's code is touched)
 *  1. COUNT. Every tick the scene name (klh_scene) says frontend ('SCENES\KaneAndLynch.gms') or a level (...\Locations\...). Each entry into a
 *     level scene counts once (levels).
 *  2. GATE. The menu manager and its window stack are read like klslot.c does (reads only). Restart only when the TOP window is one of
 *     FreshWindows (default MainMenu, CampaignMenu, HeistModeMenu, HeistPlayMenu: not the shop, the hire page, a score page, the options),
 *     the stack has not changed for FreshStableMs, StartGame is not pending, no network session exists (kl_online), the process is at least
 *     FreshMinUpMs old, and the command line is not a scripted run (AutoExit / DefaultScene / DisableSplashScreens: such a restart would
 *     loop into the test level, or run without a profile).
 *  3. WHY (levels >= FreshLevels, default 2; or largest free piece < FreshMinPieceMB; or free total < FreshMinFreeMB, both default 0 = off
 *     except FreshMinFreeMB 200). Reasons are logged with the numbers.
 *  4. THE STEP. A small topmost window 'Refreshing memory...' (own thread, no focus) for FreshToastMs; then
 *       a. KLFresh.go is NOT written yet; env KLFRESH_PID=<our pid>, KLFRESH_N=<chain+1> are set and CreateProcess starts the SAME exe with the
 *          SAME command line and working directory (no handles inherited). The env is removed again.
 *       b. KLFresh.go (our pid) is written: the go-ahead.
 *       c. the engine's quit byte [[0xdd2640]+0x6d] = 1 (what AutoExit sets at 0x5c7203: the main loop ends, the game's own shutdown runs; the
 *          existing FastExit then ends the process). After 6 s WM_CLOSE to the top window, after 14 s TerminateProcess(self): the child never
 *          waits for ever.
 *  5. THE CHILD (klfh_boot, called first thing in DllMain, before any log line or Steam call). If KLFRESH_PID is in the environment the DLL
 *     waits (DllMain, no thread needed) until KLFresh.go names that pid AND the old process has ended; only then does the game start. If the
 *     old process ends without the go file (the player closed the game by hand in those seconds) the child ends itself at once: no game
 *     comes back that nobody asked for. If no go comes in 30 s the child ends itself too. The child then shows the toast
 *     'Dog Days restarted to free memory' for FreshToastMs (a thread, started after DllMain returns).
 *
 * STEAM. kl2.exe's WinMain calls SteamAPI_RestartAppIfNecessary(28000) (0x476781; exits if true), then SteamAPI_Init. There is no
 * steam_appid.txt in the game folder. A child created by a process that Steam launched inherits Steam's environment (SteamAppId, SteamGameId),
 * which is what RestartAppIfNecessary looks at, so it should return false and Init should connect to the running client. GUESS (not run: the
 * owner was playing). Fallback FreshVia=1: a hidden cmd.exe waits 5 s and starts steam://rungameid/28000 (Steam's own launch, its launch
 * options included, a normal Play); it needs Steam to have noticed the old process gone (GUESS on the 5 s). The launcher
 * (tools/launcher/KLMergeLauncher.ps1) starts the game the same way (steam://rungameid) and only WATCHES for kl2.exe: its game watch must
 * treat a kl2.exe that comes back within ~30 s as the same session (it hides on the first kl2.exe window and returns when the game ends);
 * today it would pop up between the two processes. Not edited here (another session's file).
 *
 * WHAT THE PLAYER SEES: after a match, back at the menu, ~5 s later the toast 'Refreshing memory...', the game window closes, Steam's launch
 * splash / logos play again, press start, the main menu. About the same as starting the game. NOT saved across: the menu page (the new
 * process opens on the main menu; the expansion's page latch kls_keep is per process). Nothing is skipped on purpose: -o DisableSplashScreens
 * would also skip ZPressStart, and then no profile is loaded (re/fa_round.md 5.1: money/rank read 0 and nothing is saved).
 *
 * KLHook.ini
 *   [Memory]
 *   FreshRestart=0       1 = on (recommended on). 0 = never restart by itself
 *   FreshLevels=2        restart at the menu once this many levels were loaded in this process (2 = before the 3rd; 1 = after every match; 0 = off)
 *   FreshMinPieceMB=0    or when the largest free piece is under this many MB at the menu (0 = off)
 *   FreshMinFreeMB=200   or when the free address space is under this many MB at the menu (0 = off)
 *   FreshStableMs=2500   the menu must look the same this long first
 *   FreshToastMs=2500    'Refreshing memory...' is shown this long before the restart (the child shows its note 4x this)
 *   FreshMinUpMs=60000   never in the first minute of a process
 *   FreshMax=8           at most this many restarts in a row (chain of children)
 *   FreshVia=0           0 = start the exe directly (inherits Steam's environment), 1 = ask Steam (steam://rungameid/28000) from a hidden cmd.exe
 *   FreshWindows=MainMenu,CampaignMenu,HeistModeMenu,HeistPlayMenu    top windows (name prefix) a restart may happen on
 *   FreshLog=1
 */
#ifndef KLFRESH_C
#define KLFRESH_C

#include "klfresh_logic.h"
#ifdef _MSC_VER
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdi32.lib")
#endif

static struct klfh_cfg klfh_c = { 0, 2, 0, 200, 2500, 60000, 8 };
static int klfh_toast_ms = 2500, klfh_via, klfh_log = 1, klfh_off;
static char klfh_win[256] = "MainMenu,CampaignMenu,HeistModeMenu,HeistPlayMenu";
static int klfh_chain, klfh_test, klfh_child_toast;
static char klfh_go[MAX_PATH];
static volatile LONG klfh_toast_stop; static char klfh_toast_text[96]; static DWORD klfh_toast_until;

/* ---------------------------------------------------------------- the note on screen (own thread, own window, never takes the focus) */

static LRESULT CALLBACK klfh_toast_proc(HWND h, UINT m, WPARAM w, LPARAM l)
{
    if (m == WM_PAINT) {
        PAINTSTRUCT ps; RECT r; HDC dc = BeginPaint(h, &ps); HFONT f, old; HBRUSH b = CreateSolidBrush(RGB(24, 24, 24));
        GetClientRect(h, &r); FillRect(dc, &r, b); DeleteObject(b);
        f = CreateFontA(-24, 0, 0, 0, FW_SEMIBOLD, 0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Segoe UI");
        old = (HFONT)SelectObject(dc, f); SetBkMode(dc, TRANSPARENT); SetTextColor(dc, RGB(240, 240, 240));
        DrawTextA(dc, klfh_toast_text, -1, &r, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
        SelectObject(dc, old); DeleteObject(f); EndPaint(h, &ps); return 0;
    }
    return DefWindowProcA(h, m, w, l);
}

static DWORD WINAPI klfh_toast_thread(LPVOID unused)
{
    WNDCLASSA wc; HWND h; MSG msg; int sw = GetSystemMetrics(SM_CXSCREEN), W = 520, H = 64; DWORD until;
    (void)unused;
    memset(&wc, 0, sizeof wc); wc.lpfnWndProc = klfh_toast_proc; wc.hInstance = GetModuleHandleA(0); wc.lpszClassName = "KLFreshToast"; wc.hCursor = LoadCursor(0, IDC_ARROW);
    RegisterClassA(&wc);
    h = CreateWindowExA(WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE, "KLFreshToast", "KLHook", WS_POPUP | WS_BORDER, (sw - W) / 2, 36, W, H, 0, 0, wc.hInstance, 0);
    if (!h) return 0;
    ShowWindow(h, SW_SHOWNOACTIVATE); UpdateWindow(h);
    until = klfh_toast_until;
    while (!klfh_toast_stop && (int)(GetTickCount() - until) < 0) {
        while (PeekMessageA(&msg, 0, 0, 0, PM_REMOVE)) { TranslateMessage(&msg); DispatchMessageA(&msg); }
        SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);     /* the game may have raised itself */
        Sleep(40);
    }
    DestroyWindow(h);
    return 0;
}

static void klfh_toast(const char *text, DWORD ms)
{   /* one note at a time; the previous one is told to stop first */
    HANDLE t;
    klfh_toast_stop = 1; Sleep(60);
    snprintf(klfh_toast_text, sizeof klfh_toast_text, "%s", text);
    klfh_toast_until = GetTickCount() + ms; klfh_toast_stop = 0;
    t = CreateThread(0, 0, klfh_toast_thread, 0, 0, 0);
    if (t) CloseHandle(t);
}

/* ---------------------------------------------------------------- the child: wait for the old process (called first in DllMain) */

static void klfh_boot(void)
{   /* nothing but kernel32 and the ini path; NO klog yet (the old process may still hold the log). Waits at most ~30 s. */
    char pid_s[24], n_s[16]; DWORD pid, t0, waited = 0; HANDLE proc; int go = 0, dead = 0, spins = 0;
    if (!GetEnvironmentVariableA("KLFRESH_PID", pid_s, sizeof pid_s)) return;
    n_s[0] = 0; GetEnvironmentVariableA("KLFRESH_N", n_s, sizeof n_s);
    SetEnvironmentVariableA("KLFRESH_PID", 0); SetEnvironmentVariableA("KLFRESH_N", 0);        /* grandchildren and later restarts start clean */
    pid = strtoul(pid_s, 0, 10); klfh_chain = atoi(n_s);
    snprintf(klfh_go, sizeof klfh_go, "%s\\KLFresh.go", klh_out);
    proc = pid ? OpenProcess(SYNCHRONIZE, FALSE, pid) : 0;
    t0 = GetTickCount();
    for (;;) {
        char buf[24] = ""; DWORD got = 0; HANDLE f;
        if (!go && (f = CreateFileA(klfh_go, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 0, OPEN_EXISTING, 0, 0)) != INVALID_HANDLE_VALUE) {
            ReadFile(f, buf, sizeof buf - 1, &got, 0); CloseHandle(f); buf[got] = 0;
            if ((DWORD)strtoul(buf, 0, 10) == pid) go = 1;
        }
        dead = !proc || WaitForSingleObject(proc, 0) == WAIT_OBJECT_0;
        if (go && dead) break;
        if (dead && !go) {                                           /* the old process ended without a go-ahead (the player closed the game by hand): nobody asked for this game */
            if (++spins > 6) TerminateProcess(GetCurrentProcess(), 0);   /* the file is read at the top of the loop: ~250 ms of grace for the disk */
            Sleep(40); continue;
        }
        waited = GetTickCount() - t0;
        if (waited > 30000) { TerminateProcess(GetCurrentProcess(), 0); }   /* the old game did not leave in 30 s: never run two */
        Sleep(40);
    }
    DeleteFileA(klfh_go);
    if (proc) CloseHandle(proc);
    klfh_child_toast = 1;
}

/* ---------------------------------------------------------------- the old process */

static int klfh_levels, klfh_kind_last = -1;
static DWORD klfh_t_start, klfh_menu_sig, klfh_menu_since, klfh_step_at, klfh_quit_at, klfh_last_check, klfh_walk_at;
static int klfh_state;                                              /* 0 idle, 1 toast shown (counting down), 2 quitting */
static unsigned klfh_largest = 0xffffffffu, klfh_free = 0xffffffffu;

static int klfh_top_allowed(const char *top)
{   /* the TOP window's name starts with one of the comma-separated FreshWindows */
    const char *p = klfh_win;
    while (*p) {
        const char *e = strchr(p, ','); size_t n = e ? (size_t)(e - p) : strlen(p);
        while (n && (*p == ' ')) { p++; n--; }
        if (n && !strncmp(top, p, n)) return 1;
        if (!e) break;
        p = e + 1;
    }
    return 0;
}

static int klfh_read_menu(char *top, int cap, DWORD *sig_out)
{   /* 1 = the menu manager has a window stack; top = the name of the topmost window; sig = a hash of the stack */
    DWORD gd, mgr, w, n, win[24], i, sig; char nm[64];
    top[0] = 0; *sig_out = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != KLS_MENUMGR_VT || !(w = klh_rd32(mgr + 4))) return 0;
    if (klh_rd32(w) != KLS_WSYS_VT) return 0;
    n = klh_rd32(w + 0x328);
    if (!n || n > 24 || !klh_rd(w + 0x330, win, 4 * n)) return 0;
    for (sig = n, i = 0; i < n; i++) sig = sig * 31 + win[i];
    kls_win_name(win[n - 1], nm, sizeof nm);                         /* the stack is stored bottom to top, as klslot.c reads it ('topmost' = last) */
    snprintf(top, cap, "%s", nm);
    *sig_out = sig;
    return 1;
}

static int klfh_launch(void)
{   /* starts the next process; 1 = started (the go file is NOT written yet) */
    char exe[MAX_PATH], cwd[MAX_PATH], cmd[4096], pid_s[24], n_s[16], *s; STARTUPINFOA si; PROCESS_INFORMATION pi;
    if (!GetModuleFileNameA(0, exe, sizeof exe)) return 0;
    snprintf(cwd, sizeof cwd, "%s", exe); s = strrchr(cwd, '\\'); if (s) *s = 0;
    memset(&si, 0, sizeof si); si.cb = sizeof si;
    if (klfh_via == 1) {
        snprintf(cmd, sizeof cmd, "cmd.exe /d /c \"ping -n 6 127.0.0.1 >nul & start \"\" steam://rungameid/28000\"");
        si.dwFlags = STARTF_USESHOWWINDOW; si.wShowWindow = SW_HIDE;
        if (!CreateProcessA(0, cmd, 0, 0, FALSE, CREATE_NO_WINDOW, 0, cwd, &si, &pi)) return 0;
        CloseHandle(pi.hThread); CloseHandle(pi.hProcess); return 1;
    }
    snprintf(cmd, sizeof cmd, "%s", GetCommandLineA());
    snprintf(pid_s, sizeof pid_s, "%lu", GetCurrentProcessId()); snprintf(n_s, sizeof n_s, "%d", klfh_chain + 1);
    SetEnvironmentVariableA("KLFRESH_PID", pid_s); SetEnvironmentVariableA("KLFRESH_N", n_s);
    {   BOOL ok = CreateProcessA(exe, cmd, 0, 0, FALSE, 0, 0, cwd, &si, &pi);
        SetEnvironmentVariableA("KLFRESH_PID", 0); SetEnvironmentVariableA("KLFRESH_N", 0);
        if (!ok) { klog("fresh: CreateProcess of %s failed (error %lu): no restart", exe, GetLastError()); return 0; }
    }
    klog("fresh: next process %lu started (chain %d), waiting for our go-ahead", pi.dwProcessId, klfh_chain + 1);
    CloseHandle(pi.hThread); CloseHandle(pi.hProcess);               /* no handle kept: a held handle is what makes a dead process a zombie */
    return 1;
}

static void klfh_write_go(void)
{
    HANDLE f; char b[24]; DWORD put; int n = snprintf(b, sizeof b, "%lu", GetCurrentProcessId());
    snprintf(klfh_go, sizeof klfh_go, "%s\\KLFresh.go", klh_out);
    f = CreateFileA(klfh_go, GENERIC_WRITE, FILE_SHARE_READ, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0);
    if (f != INVALID_HANDLE_VALUE) { WriteFile(f, b, (DWORD)n, &put, 0); FlushFileBuffers(f); CloseHandle(f); }
}

static void klfh_quit_byte(void)
{   /* [[0xdd2640]+0x6d] = 1: the byte AutoExit sets (0x5c7203); the main loop ends and the game shuts down by itself */
    DWORD sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)); BYTE one = 1, now = 0; SIZE_T put = 0;
    if (!sys) return;
    WriteProcessMemory(GetCurrentProcess(), (void *)(DWORD_PTR)(sys + 0x6d), &one, 1, &put);
    klh_rd(sys + 0x6d, &now, 1);
    klog("fresh: quit byte written (now %u, %lu byte(s) put)", now, (unsigned long)put);
}

static BOOL CALLBACK klfh_close_one(HWND h, LPARAM l)
{
    DWORD pid = 0; GetWindowThreadProcessId(h, &pid);
    if (pid == GetCurrentProcessId() && IsWindowVisible(h) && GetWindow(h, GW_OWNER) == 0) { char c[32]; GetClassNameA(h, c, sizeof c); if (strcmp(c, "KLFreshToast")) { PostMessageA(h, WM_CLOSE, 0, 0); (*(int *)l)++; } }
    return TRUE;
}

static void klfh_init(void)
{
    char cmd[2048], v[256];
    klfh_c.enable = GetPrivateProfileIntA("Memory", "FreshRestart", 0, klh_ini) != 0;
    klfh_log = GetPrivateProfileIntA("Memory", "FreshLog", 1, klh_ini);
    klfh_t_start = GetTickCount();
    if (klfh_child_toast) {                                          /* the child: a short note while the splash plays (the old process is gone) */
        klfh_toast_ms = (int)GetPrivateProfileIntA("Memory", "FreshToastMs", 2500, klh_ini);
        if (klfh_toast_ms > 0) klfh_toast("Dog Days restarted to free memory", (DWORD)klfh_toast_ms * 4);
    }
    if (!klfh_c.enable) return;
    klfh_c.every_levels = (int)GetPrivateProfileIntA("Memory", "FreshLevels", 2, klh_ini);
    klfh_c.min_piece_mb = (int)GetPrivateProfileIntA("Memory", "FreshMinPieceMB", 0, klh_ini);
    klfh_c.min_free_mb = (int)GetPrivateProfileIntA("Memory", "FreshMinFreeMB", 200, klh_ini);
    klfh_c.stable_ms = (unsigned)GetPrivateProfileIntA("Memory", "FreshStableMs", 2500, klh_ini);
    klfh_c.min_up_ms = (unsigned)GetPrivateProfileIntA("Memory", "FreshMinUpMs", 60000, klh_ini);
    klfh_c.max_chain = (int)GetPrivateProfileIntA("Memory", "FreshMax", 8, klh_ini);
    klfh_toast_ms = (int)GetPrivateProfileIntA("Memory", "FreshToastMs", 2500, klh_ini); if (klfh_toast_ms < 0) klfh_toast_ms = 0;
    klfh_via = (int)GetPrivateProfileIntA("Memory", "FreshVia", 0, klh_ini);
    GetPrivateProfileStringA("Memory", "FreshWindows", klfh_win, v, sizeof v, klh_ini); if (v[0]) snprintf(klfh_win, sizeof klfh_win, "%s", v);
    snprintf(cmd, sizeof cmd, "%s", GetCommandLineA());
    klfh_test = klfh_cmd_is_test(cmd) || GetPrivateProfileIntA("Auto", "Enable", 0, klh_ini) != 0;
    klog("fresh: FreshRestart on (levels %d, min piece %d MB, min free %d MB, stable %u ms, toast %d ms, via %s, chain %d)%s; windows %s",
         klfh_c.every_levels, klfh_c.min_piece_mb, klfh_c.min_free_mb, klfh_c.stable_ms, klfh_toast_ms, klfh_via ? "Steam" : "direct", klfh_chain,
         klfh_test ? " - a SCRIPTED run (AutoExit / DefaultScene / DisableSplashScreens / [Auto]): it will never restart" : "", klfh_win);
}

static void klfh_tick(int game_thread)
{
    DWORD now = GetTickCount(), sig; char scene[160], key[64], top[64]; int kind = -1, menu, pend = 0; BYTE pb = 0;
    struct klfh_in in; int why;
    if (!klfh_c.enable || klfh_off || !game_thread || !klh_exe_ok) return;
    if (klfh_state == 2) {                                           /* quitting: make sure it ends */
        if (now - klfh_quit_at > 14000) { klog("fresh: the game did not end in 14 s: TerminateProcess"); TerminateProcess(GetCurrentProcess(), 0); }
        else if (now - klfh_quit_at > 6000 && now - klfh_last_check > 1000) { int n = 0; klfh_last_check = now; EnumWindows(klfh_close_one, (LPARAM)&n); klog("fresh: no exit in 6 s: WM_CLOSE to %d window(s)", n); }
        return;
    }
    if (now - klfh_last_check < 250) return;
    klfh_last_check = now;
    if (klh_scene(scene, sizeof scene)) kind = klh_level_key(scene, key, sizeof key) ? 1 : (strstr(scene, "KaneAndLynch") || strstr(scene, "kaneandlynch") ? 0 : -1);
    if (klfh_count(&klfh_kind_last, kind, &klfh_levels) && klfh_log) klog("fresh: level load %d of this process (%s)", klfh_levels, scene);
    menu = kind == 0 && klfh_read_menu(top, sizeof top, &sig);
    if (menu) { if (sig != klfh_menu_sig) { klfh_menu_sig = sig; klfh_menu_since = now; } }
    else { klfh_menu_sig = 0; klfh_menu_since = now; top[0] = 0; }
    if (klh_rd((DWORD_PTR)KLH_VA(KLS_STARTPEND), &pb, 1)) pend = pb != 0;
    memset(&in, 0, sizeof in);
    in.test_run = klfh_test; in.online = kl_online(); in.at_menu = menu && klfh_top_allowed(top); in.start_pending = pend;
    in.menu_ms = now - klfh_menu_since; in.up_ms = now - klfh_t_start; in.levels = klfh_levels; in.chain = klfh_chain;
    in.largest_mb = klfh_largest; in.free_mb = klfh_free;
    if (klfh_state == 1) {                                           /* the note is up: still safe? then go */
        if (!klfh_gate(&klfh_c, &in)) { klfh_toast_stop = 1; klfh_state = 0; klog("fresh: restart cancelled (the player moved on: top '%s', pending %d)", top, pend); return; }
        if (now - klfh_step_at < (DWORD)klfh_toast_ms) return;
        if (!klfh_launch()) { klfh_off = 1; klfh_toast_stop = 1; return; }
        if (klfh_via == 0) klfh_write_go();
        klfh_quit_byte(); klfh_quit_at = now; klfh_state = 2;
        return;
    }
    if (klfh_needs_walk(&klfh_c, &in) && now - klfh_walk_at > 2000) {
        SIZE_T lg, tot; klfh_walk_at = now; klm_free_space(&lg, &tot); klfh_largest = (unsigned)(lg >> 20); klfh_free = (unsigned)(tot >> 20);
        in.largest_mb = klfh_largest; in.free_mb = klfh_free;
    }
    why = klfh_decide(&klfh_c, &in);
    if (why != KLFH_NO) {
        klog("fresh: restarting kl2.exe at the menu '%s': %s (level loads %d, largest free piece %u MB, free %u MB, up %lu s)", top, klfh_why(why), klfh_levels,
             klfh_largest, klfh_free, (unsigned long)(in.up_ms / 1000));
        klfh_toast("Refreshing memory...", (DWORD)klfh_toast_ms + 4000);
        klfh_step_at = now; klfh_state = 1;
    }
}

#endif /* KLFRESH_C */
