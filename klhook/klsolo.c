/*
 * klsolo.c - [Solo]: two kl2.exe on one PC, for testing the online code alone (2026-10-22, the owner: 'find a way to do
 * netsmooth online by yourself'). TEST builds only (included by klhook.c inside #ifdef KLHOOK_TEST). Plan and reasons:
 * re/netsmooth_solo.md. Off unless [Solo] Enable=1; then:
 *
 *   1. MUTEX. WinMain 0x47690b CreateMutexA("KANEANDLYNCH2MUTEX") through import slot 0xb10264 (outside every hashed range)
 *      and exits when it already exists (GetLastError 0xb7 at 0x476917). The import slot is wrapped: that one name gets
 *      "_<pid>" appended, so a second process makes its own. Every other name passes unchanged.
 *   2. WINDOWED. The game makes a fullscreen-exclusive Direct3D 9 device (ReShade.log: Windowed=FALSE) and has no windowed
 *      option (the registry key Graphics holds FullscreenID / DisplayWidth / WindowWidth; WindowWidth is read at 0x904953 and
 *      used nowhere else). Two exclusive devices cannot live side by side. Direct3DCreate9 is wrapped (in front of kltex.c's
 *      wrapper, which is installed first), then IDirect3D9::CreateDevice (slot 16) and the device's Reset (slot 16): the present
 *      parameters get Windowed=1, refresh 0, interval IMMEDIATE. The back buffer keeps the game's size (its render targets are
 *      made at that size); the window is then set to [Solo] X Y W H and Present scales the picture into it.
 *   3. FOCUS. The main loop 0x87a930 runs no frame while dword [sys+0xb10] (sys = [0xdd2640]) is 0 = window not active
 *      (written by the window procedure 0x714810 on WM_ACTIVATE / WM_SETFOCUS / WM_KILLFOCUS; re/freeze_1009.md 3.2). Only one
 *      of two windows can be in front, so every tick writes 1 there (heap data). The inactive branch still calls
 *      SteamAPI_RunCallbacks (0x48a1e0), so the tick runs and the next frame is a full one.
 *   4. ForceLan=1 (default 0): 0x5deb50 'is this a System Link game' ([mgr+0x58]==2 or MP_RankedGame==2; 23 callers, one of
 *      them the network start 0x7ee1cf that then skips the Steam transport) is made to answer 1: `mov eax,1 / ret` over its
 *      first 6 bytes (not hashed; the patch guard is asked anyway). For when the System Link menu route cannot be scripted.
 *      GUESS that the other 22 callers only pick the non-Steam path.
 *   Per-instance files: the env variable KLHOOK_DIR (klhook.c DllMain, TEST only) moves KLHook.ini / .log / .result / dumps.
 *
 * Keys ([Solo]): Enable=0  ForceLan=0  Windowed=1  X=0 Y=0 W=960 H=540  Focus=1
 */
#define KLSOLO_C

typedef HANDLE (WINAPI *klso_mutex_fn)(LPSECURITY_ATTRIBUTES, BOOL, LPCSTR);
typedef void *(WINAPI *klso_create9_fn)(UINT);
typedef HRESULT (WINAPI *klso_createdev_fn)(void *self, UINT adapter, DWORD type, HWND focus, DWORD flags, void *pp, void **dev);
typedef HRESULT (WINAPI *klso_reset_fn)(void *self, void *pp);

static int klso_on, klso_win = 1, klso_focus = 1, klso_x, klso_y, klso_w = 960, klso_h = 540;
static klso_mutex_fn     klso_real_mutex;
static klso_create9_fn   klso_real_create9;
static klso_createdev_fn klso_real_createdev;
static klso_reset_fn     klso_real_reset;
static HWND klso_hwnd;
static volatile LONG klso_focus_writes;

static HANDLE WINAPI klso_mutex(LPSECURITY_ATTRIBUTES sa, BOOL own, LPCSTR name)
{
    if (name && !strcmp(name, "KANEANDLYNCH2MUTEX")) {
        char n[64]; snprintf(n, sizeof n, "%s_%lu", name, (unsigned long)GetCurrentProcessId());
        klog("solo: single-instance mutex renamed to %s", n);
        return klso_real_mutex(sa, own, n);
    }
    return klso_real_mutex(sa, own, name);
}

/* D3DPRESENT_PARAMETERS (d3d9.h): +0x00 BackBufferWidth, +0x04 Height, +0x1c hDeviceWindow, +0x20 Windowed, +0x30 FullScreen_RefreshRateInHz,
   +0x34 PresentationInterval */
static void klso_pp(DWORD *pp, const char *what)
{
    if (!pp) return;
    klog("solo: %s: back buffer %lux%lu windowed %lu refresh %lu interval %08lx -> windowed, refresh 0, immediate", what,
         pp[0], pp[1], pp[8], pp[12], pp[13]);
    pp[8] = 1; pp[12] = 0; pp[13] = 0x80000000u;
}

static void klso_place(HWND w)
{
    typedef BOOL (WINAPI *swp_fn)(HWND, HWND, int, int, int, int, UINT);
    HMODULE u = GetModuleHandleA("user32.dll"); swp_fn swp = u ? (swp_fn)GetProcAddress(u, "SetWindowPos") : 0;   /* this DLL does not link user32 */
    if (!w) return;
    klso_hwnd = w;
    klog("solo: window %p placed at %d,%d %dx%d: %s", (void *)w, klso_x, klso_y, klso_w, klso_h,
         swp && swp(w, HWND_NOTOPMOST, klso_x, klso_y, klso_w, klso_h, SWP_NOACTIVATE | SWP_SHOWWINDOW) ? "ok" : "FAILED");
}

static HRESULT WINAPI klso_reset(void *self, void *pp)
{
    HRESULT r;
    klso_pp((DWORD *)pp, "Reset");
    r = klso_real_reset(self, pp);
    klog("solo: Reset -> %08lx", (unsigned long)r);
    if (r >= 0) klso_place(klso_hwnd);
    return r;
}

static void klso_wrap(void *obj, int slot, void *mine, void **real, const char *what)
{   /* as kltx_wrap_slot: the object's vtable lives in d3d9.dll / ReShade, not in kl2.exe */
    void **vt = obj ? *(void ***)obj : 0, *cur;
    if (!vt) return;
    cur = vt[slot];
    if (cur == mine) return;
    if (*real && *real != cur) { klog("solo: %s: a second class (%p, first %p) - left alone", what, cur, *real); return; }
    *real = cur;
    if (!klh_poke(&vt[slot], &cur, sizeof cur, &mine, sizeof mine, what)) { klog("solo: %s: vtable slot %d not changed", what, slot); *real = 0; return; }
    klog("solo: %s wrapped (vtable %p slot %d, was %p)", what, (void *)vt, slot, cur);
}

static HRESULT WINAPI klso_createdev(void *self, UINT adapter, DWORD type, HWND focus, DWORD flags, void *pp, void **dev)
{
    HRESULT r;
    klso_pp((DWORD *)pp, "CreateDevice");
    r = klso_real_createdev(self, adapter, type, focus, flags, pp, dev);
    klog("solo: CreateDevice -> %08lx", (unsigned long)r);
    if (r >= 0 && dev && *dev) {
        klso_wrap(*dev, 16, (void *)klso_reset, (void **)&klso_real_reset, "Reset");
        klso_place(pp && ((HWND *)pp)[7] ? ((HWND *)pp)[7] : focus);
    }
    return r;
}

static void *WINAPI klso_create9(UINT sdk)
{
    void *d3d = klso_real_create9(sdk);
    if (d3d) klso_wrap(d3d, 16, (void *)klso_createdev, (void **)&klso_real_createdev, "CreateDevice");
    return d3d;
}

static void klso_init(void)
{
    klso_on = GetPrivateProfileIntA("Solo", "Enable", 0, klh_ini);
    if (!klso_on) return;
    klso_win = GetPrivateProfileIntA("Solo", "Windowed", 1, klh_ini);
    klso_focus = GetPrivateProfileIntA("Solo", "Focus", 1, klh_ini);
    klso_x = GetPrivateProfileIntA("Solo", "X", 0, klh_ini); klso_y = GetPrivateProfileIntA("Solo", "Y", 0, klh_ini);
    klso_w = GetPrivateProfileIntA("Solo", "W", 960, klh_ini); klso_h = GetPrivateProfileIntA("Solo", "H", 540, klh_ini);
    klog("solo: on (pid %lu, files in %s): Windowed=%d Focus=%d window %d,%d %dx%d", (unsigned long)GetCurrentProcessId(), klh_out, klso_win, klso_focus, klso_x, klso_y, klso_w, klso_h);
    if (!klh_iat("KERNEL32.dll", "CreateMutexA", (void *)klso_mutex, (void **)&klso_real_mutex)) klog("solo: CreateMutexA import NOT wrapped - a second instance will exit");
    if (klso_win && !klh_iat("d3d9.dll", "Direct3DCreate9", (void *)klso_create9, (void **)&klso_real_create9)) klog("solo: Direct3DCreate9 import NOT wrapped - fullscreen");
    if (GetPrivateProfileIntA("Solo", "ForceLan", 0, klh_ini)) {
        static const BYTE expect[6] = { 0x83, 0x79, 0x58, 0x02, 0x74, 0x2a }, put[6] = { 0xb8, 0x01, 0x00, 0x00, 0x00, 0xc3 };   /* cmp [ecx+0x58],2 / je 0x5deb80 */
        klog("solo: ForceLan: 0x5deb50 -> return 1 %s", klh_poke(KLH_VA(0x5deb50), expect, 6, put, 6, "solo ForceLan") ? "patched" : "NOT patched (bytes differ or refused)");
    }
}

static void klso_tick(int game_thread)
{
    DWORD sys, v, one = 1;
    (void)game_thread;
    if (!klso_on || !klso_focus) return;
    if (!klh_rd(KL2_SYSIF, &sys, 4) || !sys || !klh_rd(sys + 0xb10, &v, 4) || v) return;
    if (klh_data((void *)(DWORD_PTR)(sys + 0xb10), &one, 4, "solo focus") && InterlockedIncrement(&klso_focus_writes) <= 3)
        klog("solo: window not active: [sys+0xb10] set to 1 so the main loop keeps running");
}
