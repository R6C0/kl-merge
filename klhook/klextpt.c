/*
 * klextpt.c - the game thread's message pump must not run other programs' hook code (stutter fix, 2026-10-23). Part of KLHook.
 *
 * WHY: owner round 13:27 on DM01 (SHIP kit b): 14-15 frames over 33 ms per 10 s, longest 0.8 - 3.6 s, 'core: hitch' 150 - 600 ms every
 * 0.5 - 1 s. The hitch probe's main-thread samples, resolved against the PC's own DLLs (SysWOW64 exports):
 *     win32u+0x101c = NtUserPeekMessage, +0x107c = NtUserMessageCall, +0x11ec = NtUserCallNextHookEx,
 *     USER32+0x3c67a = PeekMessageW, +0x3c316 = CallNextHookEx, +0x209e5 = PeekMessageA, KL2+0x4d15a0 / KL2+0x7cbe1 = the main loop's pump
 *     (KL2+0x42dfeb = the pump's PeekMessageA return, KL2+0x13c806 = a Sleep(25) polling wait for a stream, KL2+0x1e8b20 = its caller),
 * i.e. 55 - 60 % of the samples inside a hook chain run by the pump, with gameoverlayrenderer.dll, ReShade32.dll and (13:28:02, and the
 * 2026-10-14 rounds) uiautomationcore.dll+0x655f0 on the stack. uiautomationcore is the accessibility client side that another program
 * (Grammarly.Desktop, TextInputHost, PhoneExperienceHost, copilot-runtime were running) puts into every process through a global hook /
 * in-context WinEvent hook: its code then runs in the game's own PeekMessage and calls out to its owner program synchronously.
 * The refusal of WM_GETOBJECT (klhook.c, noUIA) never fired (0 refused in every perf line), so it did not touch this path.
 * Autotest/bench rounds had no such stutter because no input reached them.  (GUESS where marked below; nothing here was run live.)
 *
 * WHAT: SetProcessMitigationPolicy(ProcessExtensionPointDisablePolicy = 6, DisableExtensionPoints): Windows stops loading legacy
 * extension points into this process: global SetWindowsHookEx DLLs, AppInit DLLs, Winsock LSPs, legacy IMEs. Hooks the game itself, ReShade
 * or the Steam overlay set inside this process are not extension points and keep working (GUESS: not seen live; the log line after the
 * call says whether Windows took it, and the 'inject:' lines below say which foreign DLLs still arrived).
 * Also a small watcher thread: every 2 s it looks at the module list and logs each DLL that is neither the game's, the hook's nor in
 * the Windows folders ('inject: <path>'), always uiautomationcore / msctf / Grammarly-like names, at most 60 lines - the evidence
 * for the next round.
 *
 * [KLHook] NoInject=1   (default 1; 0 = the game as before: foreign hook DLLs may be loaded into it)
 * [KLHook] InjectLog=1  (default 1; 0 = no watcher thread)
 * Windows 8 or later (the call is looked up in kernel32; absent = a log line and nothing else).
 */
static int klxp_noinject = 1;

typedef BOOL (WINAPI *klxp_spmp_fn)(int, PVOID, SIZE_T);
typedef BOOL (WINAPI *klxp_enum_fn)(HANDLE, HMODULE *, DWORD, LPDWORD);
typedef DWORD (WINAPI *klxp_name_fn)(HANDLE, HMODULE, LPSTR, DWORD);

static int klxp_foreign(const char *p, const char *gamedir)
{   /* a module worth a log line: not in the game folder (but the hook's own dir is the game folder) and not under Windows */
    char win[MAX_PATH]; UINT n = GetWindowsDirectoryA(win, sizeof win);
    if (n && n < sizeof win && _strnicmp(p, win, n) == 0) {
        if (strstr(p, "uiautomationcore") || strstr(p, "UIAutomationCore") || strstr(p, "msctf") || strstr(p, "MSCTF")) return 1;   /* system DLLs we do want to hear about */
        return 0;
    }
    if (gamedir && _strnicmp(p, gamedir, strlen(gamedir)) == 0) return 0;
    return 1;
}

static DWORD WINAPI klxp_watch(LPVOID unused)
{
    HMODULE k = GetModuleHandleA("kernel32.dll"), mods[1024]; klxp_enum_fn en; klxp_name_fn nm; int told = 0; HMODULE seen[1024]; int nseen = 0;
    char gamedir[MAX_PATH]; DWORD gl; (void)unused;
    en = (klxp_enum_fn)GetProcAddress(k, "K32EnumProcessModules"); nm = (klxp_name_fn)GetProcAddress(k, "K32GetModuleFileNameExA");
    if (!en || !nm) return 0;
    gl = GetModuleFileNameA(NULL, gamedir, sizeof gamedir);
    if (gl && gl < sizeof gamedir) { char *s = strrchr(gamedir, '\\'); if (s) *s = 0; } else gamedir[0] = 0;
    for (;;) {
        DWORD need = 0; Sleep(2000);
        if (!en(GetCurrentProcess(), mods, sizeof mods, &need)) continue;
        { DWORD cnt = need / sizeof(HMODULE), i, j; if (cnt > 1024) cnt = 1024;
          for (i = 0; i < cnt; i++) {
              char path[MAX_PATH];
              for (j = 0; j < (DWORD)nseen && seen[j] != mods[i]; j++);
              if (j < (DWORD)nseen) continue;
              if (nseen < 1024) seen[nseen++] = mods[i];
              if (!nm(GetCurrentProcess(), mods[i], path, sizeof path)) continue;
              if (told < 60 && klxp_foreign(path, gamedir[0] ? gamedir : 0)) { told++; klog("inject: module %s loaded at %p", path, (void *)mods[i]); }
          } }
    }
    return 0;
}

static void klxp_init(void)
{
    klxp_noinject = GetPrivateProfileIntA("KLHook", "NoInject", 1, klh_ini) != 0;
    if (klxp_noinject) {
        HMODULE k = GetModuleHandleA("kernel32.dll"); klxp_spmp_fn sp = k ? (klxp_spmp_fn)GetProcAddress(k, "SetProcessMitigationPolicy") : 0;
        if (!sp) klog("inject: SetProcessMitigationPolicy not found (before Windows 8): foreign hook DLLs may be loaded into the game as before");
        else {
            DWORD flags = 1;                                                    /* PROCESS_MITIGATION_EXTENSION_POINT_DISABLE_POLICY.DisableExtensionPoints */
            BOOL ok = sp(6 /* ProcessExtensionPointDisablePolicy */, &flags, sizeof flags);
            klog("inject: extension points %s (error %lu): global hook DLLs / AppInit / legacy IME no longer loaded into the game; [KLHook] NoInject=0 to undo",
                 ok ? "DISABLED" : "NOT disabled", ok ? 0UL : GetLastError());
        }
    } else klog("inject: NoInject=0: foreign hook DLLs may be loaded into the game");
    if (GetPrivateProfileIntA("KLHook", "InjectLog", 1, klh_ini) != 0) CloseHandle(CreateThread(0, 0, klxp_watch, 0, 0, 0));
}
