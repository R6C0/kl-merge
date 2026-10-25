/*
 * klfps.c - [FrameLimit]: an RTSS-style frame limiter inside the hook (2026-10-24, the owner: 'also embed this to remove stutters ...
 * RTSS does the same while being free. These setup for RTSS is identical to this program: Frametime calculation point = frame
 * presentation; Enable framerate limiter = front edge sync; Enable passive waiting = false'). Part of KLHook (included by klhook.c,
 * SHIP and TEST alike). Timing only: no byte of kl2.exe is changed, no game data is written.
 *
 * WHICH API (PROVEN from the import table, not from a run of this file): kl2.exe imports d3d9.dll (Direct3DCreate9) and NOTHING of
 * d3d10 / d3d11 / dxgi. The launch option -dx10 is ignored by the build 0490 executable (re/dlss5_kl2.md 'WRONG ABOVE'), so the
 * game presents through IDirect3DDevice9::Present (vtable slot 17). The code of kl2.exe on disk is Steam-CEG encrypted (a scan of
 * .text for `call [reg+0x44]` finds nothing), so the call site is NOT patched and not even located: the device object's vtable
 * entry is wrapped instead, exactly as kltex.c wraps SetSamplerState.
 *
 * HOOK POINT: d3d9.dll!Direct3DCreate9 import slot of kl2.exe (kltx_init wraps it first, klso_init in TEST second, this file LAST,
 * so this wrapper is the outermost) -> the IDirect3D9 object's CreateDevice (slot 16) -> the DEVICE the game gets back, slot 17
 * Present. Because the vtable of the object the GAME holds is wrapped, this runs OUTSIDE everything else that may sit below it:
 * ReShade32.dll (a proxy device whose Present renders the effects, then calls the real one), gameoverlayrenderer.dll (Steam's
 * overlay detours the real d3d9 Present), the GITC Uplift add-on, DiscordHook. They all see the call after our wait. The wait
 * is therefore also before ReShade's effect pass (front edge, see below). Present is called by the game's render thread (the
 * crash notes put the render thread inside Present), so it is that thread that waits; the game thread is not stopped here, it
 * runs ahead until the engine's own hand-off events (DrawBegin / DrawEnd) make it wait for the render thread.
 * D3D9Ex / IDirect3DSwapChain9::Present and PresentEx are NOT wrapped (the exe imports no Direct3DCreate9Ex; the additional swap
 * chain route is GUESSED unused).
 *
 * THE ALGORITHM (RTSS semantics as the owner set them; sources: Guru3D forum, Unwinder quoted: 'front edge sync applies the
 * framerate limiter's delay immediately BEFORE the original Present call', RTSS hooks Present; PassiveWaitThreshold = how much of
 * the wait is a Sleep, the rest being the busy loop; there is no official document for the three options, this is the reading):
 *   - FRAMETIME CALCULATION POINT = PRESENTATION: the period is measured between two successive Present calls (the instant we hand
 *     the frame to the original Present), not from the frame's first draw call. So the wait absorbs whatever the frame needed.
 *   - FRONT EDGE SYNC (FrontEdge=1): the delay is placed right before the original Present: the frame is finished, held until its
 *     slot, then presented. The game thread meanwhile has already sampled input for the next frame only after this Present returns,
 *     so what is shown is the newest. Back edge (FrontEdge=0): the same deadline is waited out right AFTER Present returns, i.e.
 *     before the thread begins the next frame (older picture on screen, input sampled later). Offered as an option, not recommended.
 *   - PASSIVE WAITING = false (PassiveWait=0): the wait is a QueryPerformanceCounter busy loop with YieldProcessor, never Sleep. It
 *     burns one core while it waits (on the render thread, typically a few ms of every frame) and has no scheduler jitter.
 *     PassiveWait=1: Sleep(1) while more than 2.5 ms remain, then the busy loop (timeBeginPeriod(1) is asked for the process).
 *   - DEADLINE ACCUMULATOR: D = the time the next Present may happen. Wait until D; D += period (not D = now + period), so a late
 *     frame is paid back by a short one and the average is exact. When the frame arrived MORE than one period late (a hitch, a load,
 *     alt-tab) D is reset to now + period: no catch-up burst of presents. Period = freq / Fps in 64-bit ticks; the remainder is
 *     carried (Bresenham) so 144 Hz stays 144.000 and not 144.04.
 *
 * Fps: [FrameLimit] Fps=0 (default) = AUTO = the refresh rate of the device the game made (D3DPRESENT_PARAMETERS
 * FullScreen_RefreshRateInHz when fullscreen, else EnumDisplaySettings' current dmDisplayFrequency, else 60). Why the refresh rate:
 * the owner's runs are uncapped at 184 .. 250 fps (re/open_work_log.md 10-24), a rate no screen shows, and the stutter is the
 * frametime spread of such a free-running render thread; a cap at the refresh rate is the usual RTSS recommendation and keeps
 * every presented frame displayable. AUTO IS SKIPPED when the game's own vsync is on (PresentationInterval is not IMMEDIATE):
 * then Present already blocks for the vertical blank and a second limiter at the same rate would only beat against it. Timing and
 * the Log line still run. An explicit Fps=N applies in every case (so Fps=60 with the game's vsync off is a 60 cap).
 * The device is read at CreateDevice; a Reset to another refresh rate keeps the old target (GUESS: the game does not change it in a
 * level; the options menu does, and then a restart of the game is needed - the same as every other KLHook graphics key).
 *
 * THE GAME'S OWN CAP (item 3 of the task): kl2.exe has an option EnableVSync (re/menus.md 316: options 40 EnableVSync, 44 Refresh)
 * which becomes PresentationInterval; with it off the game is uncapped (measured 184 .. 250 fps) and has no frame limiter of its
 * own that was ever found. The main loop's Sleep(25) at 0x53c7f0 is the load-screen stream poll only. KLHook's other waits: [QoL]
 * BackgroundMs (sleeps on the GAME thread tick while the window is in the background, local sessions) and TEST-only [Solo] FpsCap
 * (game thread, SteamAPI_RunCallbacks). Those cannot fight this one in normal play ([Solo] is TEST and off; [QoL] only when
 * unfocused, and a limiter that finds the render thread late simply does not wait). This file NEVER touches the game's vsync.
 *
 * PRESETS (owner 2026-10-24 'have 4 different options: 240fps, 120fps, 60fps, 30fps'): auto takes the highest of 240 / 120 / 60 / 30
 * that is <= the refresh rate (klfps_preset); tools\kl_mod_options.py offers exactly those four. Fps=N by hand still takes any 10 .. 1000.
 * Keys ([FrameLimit]):  Enable=1 (recommended on; 0 = nothing is wrapped)   Fps=0 (0 = auto, see above; 10 .. 1000)
 *   SwapChain=1 (k36; 0 = leave IDirect3DSwapChain9::Present alone)   Reset=1 (k36; 0 = leave IDirect3DDevice9::Reset alone)
 *   Adaptive=0 (k30fps; 1 = pacing follows the machine's own frame time, see klfps_pace; experimental, not recommended)
 *   FrontEdge=1 (recommended on)   PassiveWait=0 (recommended off = busy loop)   Log=0 (1 = a line every 10 s: presents, fps,
 *   frametime avg / min / max, count over 33 ms, share of the frame spent waiting)
 * Read once at start. NOT RUN IN THE GAME: compiled and type-checked only.
 */
#ifndef KLFPS_C
#define KLFPS_C

typedef void *(WINAPI *klfps_create9_fn)(UINT);
typedef HRESULT (WINAPI *klfps_createdev_fn)(void *self, UINT adapter, DWORD type, HWND focus, DWORD flags, void *pp, void **dev);
typedef HRESULT (WINAPI *klfps_present_fn)(void *self, const RECT *src, const RECT *dst, HWND wnd, const void *dirty);

static klfps_create9_fn   klfps_real_create9;
static klfps_createdev_fn klfps_real_createdev;
static klfps_present_fn   klfps_real_present;
typedef HRESULT (WINAPI *klfps_present_sc_fn)(void *self, const RECT *src, const RECT *dst, HWND wnd, const void *dirty, DWORD flags);
static klfps_present_sc_fn klfps_real_present_sc;
static int klfps_seen;                          /* the first Present was logged */
static int  klfps_enable = 1, klfps_fps_ini, klfps_front = 1, klfps_passive, klfps_log;
static int  klfps_target;                       /* frames per second now enforced; 0 = timing only */
static int  klfps_auto_hz, klfps_vsync;         /* what the device said */
static LONGLONG klfps_freq, klfps_period, klfps_rem, klfps_acc, klfps_deadline;
static LONGLONG klfps_last_present, klfps_t0, klfps_sum, klfps_min, klfps_max, klfps_wait_sum;
static long klfps_n, klfps_over33;
/* k30fps (2026-10-24, owner: 'framerate doesnt feel exactly smooth'). The owner's game free-runs at 153 .. 251 fps with a 240 cap:
 * the cap only binds on the fast frames, so the SPREAD stays. ADAPTIVE PACING: pace = a running estimate of how long the game needs
 * per frame (rises fast, falls slowly); a frame is never presented earlier than pace after the previous one, so the screen sees an even
 * rhythm just below what the machine can do, instead of 150 / 250 / 160 / 240. SIMULATED RESULT (tools\sim_pace.py): frame spread -7 %, average -7 % fps - a small gain for a real cost, so it is OFF by default and NOT
 * recommended; the per-frame jitter of a free-running game cannot be pacing-corrected without queueing frames (latency). Kept as an experiment. GUESS:
 * the 0.05 / 0.01 gains and the 1.5x hitch clamp are chosen by an offline simulation (tools\sim_pace.py), not from a play test. */
static int  klfps_adaptive;                     /* [FrameLimit] Adaptive (code default 0 = off, not recommended, see above) */
#include <intrin.h>                               /* _ReturnAddress (k36 log of who calls the wrappers) */
static LONGLONG klfps_pace, klfps_ret, klfps_pace_sum;
static long klfps_pace_n, klfps_wd, klfps_resets;
typedef HRESULT (WINAPI *klfps_reset_fn)(void *self, void *pp);
static klfps_reset_fn klfps_real_reset;

/* owner 2026-10-24: four presets 240 / 120 / 60 / 30; auto = the highest one the screen shows (144 Hz -> 120, 75 Hz -> 60).
 * 1025: 2 Hz slack - Windows reports 59.94 Hz modes as 59 (K49I, monitor-off mode, got 30 fps) and 239.76 as 239 */
static int klfps_preset(int hz)
{
    static const int p[] = { 240, 120, 60, 30 };
    int i;
    for (i = 0; i < 3; i++) if (hz + 2 >= p[i]) return p[i];
    return 30;
}

static void klfps_set_target(void)
{
    int fps = klfps_fps_ini;
    if (!fps) fps = klfps_vsync ? 0 : klfps_preset(klfps_auto_hz);   /* auto: not on top of the game's own vsync */
    klfps_target = fps;
    if (fps > 0 && klfps_freq) { klfps_period = klfps_freq / fps; klfps_rem = klfps_freq % fps; }
    klfps_acc = 0; klfps_deadline = 0;
}

/* wait (busy, optional coarse sleep) until QPC >= until; returns the counter then. WATCHDOG: never longer than 200 ms in one call
 * (a corrupt deadline after a clock jump or a Reset must not freeze the render thread); counted in klfps_wd and logged. */
static LONGLONG klfps_spin(LONGLONG until)
{
    LARGE_INTEGER n; LONGLONG cap = 0;
    for (;;) {
        QueryPerformanceCounter(&n);
        if (n.QuadPart >= until) return n.QuadPart;
        if (!cap) cap = n.QuadPart + klfps_freq / 5;
        if (n.QuadPart >= cap) { klfps_wd++; klfps_deadline = 0; return n.QuadPart; }
        if (klfps_passive && (until - n.QuadPart) * 1000 > klfps_freq * 5 / 2) Sleep(1);
        else YieldProcessor();
    }
}

/* the deadline step for one frame: D += period with the remainder carried */
static LONGLONG klfps_step(void)
{
    LONGLONG p = klfps_period;
    klfps_acc += klfps_rem;
    if (klfps_acc >= klfps_target) { klfps_acc -= klfps_target; p++; }
    if (klfps_adaptive && klfps_pace > p) p = klfps_pace;          /* never faster than the machine's own rhythm */
    return p;
}

/* adaptive pacing: feed the time the game needed for the frame that is arriving (previous Present's return -> this Present's entry).
 * Rises with gain 0.05, falls with 0.01; one sample is clamped to 1.5x the current estimate (a 50 ms hitch must not set the rhythm);
 * the estimate lives between the cap's period and 1/30 s. Integer arithmetic only. */
static void klfps_pace_feed(LONGLONG work)
{
    LONGLONG lo = klfps_period, hi = klfps_freq / 30, ref = klfps_pace > lo ? klfps_pace : lo;
    if (work > ref * 3 / 2) work = ref * 3 / 2;
    if (!klfps_pace) klfps_pace = work > lo ? work : lo;
    else if (work > klfps_pace) klfps_pace += (work - klfps_pace) * 5 / 100;
    else klfps_pace -= (klfps_pace - work) * 1 / 100;
    if (klfps_pace < lo) klfps_pace = lo;
    if (klfps_pace > hi) klfps_pace = hi;
    klfps_pace_sum += klfps_pace; klfps_pace_n++;
}

/* hold until the slot; called before (front edge) or after (back edge) the original Present */
static void klfps_wait(void)
{
    LARGE_INTEGER n; LONGLONG t;
    if (klfps_target <= 0 || !klfps_freq) return;
    QueryPerformanceCounter(&n); t = n.QuadPart;
    if (!klfps_deadline) klfps_deadline = t;
    if (t < klfps_deadline) { LONGLONG w0 = t; t = klfps_spin(klfps_deadline); klfps_wait_sum += t - w0; }
    klfps_deadline += klfps_step();
    if (t > klfps_deadline) klfps_deadline = t + (klfps_adaptive && klfps_pace > klfps_period ? klfps_pace : klfps_period);     /* arrived more than one period after its slot (the new D is already past): resync, no burst */
}

static void klfps_stat(LONGLONG now)
{
    if (klfps_last_present) {
        LONGLONG dt = now - klfps_last_present;
        klfps_n++; klfps_sum += dt;
        if (!klfps_min || dt < klfps_min) klfps_min = dt;
        if (dt > klfps_max) klfps_max = dt;
        if (dt * 30 > klfps_freq) klfps_over33++;
    }
    klfps_last_present = now;
    if (!klfps_t0) klfps_t0 = now;
    if (klfps_log && now - klfps_t0 >= klfps_freq * 10 && klfps_n) {
        double secs = (double)(now - klfps_t0) / (double)klfps_freq, ms = 1000.0 / (double)klfps_freq;
        klog("fps: limiter: %ld presents in %.1f s = %.1f fps (target %d%s); frametime avg %.2f min %.2f max %.2f ms; %ld over 33 ms; waiting %.1f %% of the time; adaptive %s pace %.2f ms; watchdog %ld resets %ld",
             klfps_n, secs, klfps_n / secs, klfps_target, klfps_target ? "" : " = off, timing only",
             (double)klfps_sum * ms / klfps_n, (double)klfps_min * ms, (double)klfps_max * ms, klfps_over33,
             100.0 * (double)klfps_wait_sum / (double)(now - klfps_t0),
             klfps_adaptive ? "on" : "off", klfps_pace_n ? (double)klfps_pace_sum * ms / klfps_pace_n : 0.0, klfps_wd, klfps_resets);
        klfps_pace_sum = 0; klfps_pace_n = 0;
        klfps_t0 = now; klfps_n = 0; klfps_sum = klfps_min = klfps_max = 0; klfps_over33 = 0; klfps_wait_sum = 0;
    }
}

/* k36 (2026-10-24): k34 with [FrameLimit] Enable=1 died 60 ms after 'FIRST Present seen, via the swap chain route' with c00000fd (stack
 * overflow, twice, 17:32:50 and 17:33:17); the same build with Enable=0 ran. No dump was written, so the exact cycle is NOT proven
 * (no ReShade32 path was found that re-enters slot 3 or 17 by itself: ReShade's sc Present 507BCE00 and device Present 507A9A00 both
 * only call their _orig object). What is certain: the only difference was our patches on ReShade's shared class vtables (device
 * 509F9728 slots 16 / 17, swap chain 509F9D54 slot 3; ReShade's explicit swap chains share that vtable too), and the Steam overlay and
 * other layers also work on these objects. So the wrappers are now self-limiting:
 *   - a per-THREAD depth (TLS, not the old global flag): entering with depth >= 3 can only be a cycle (device -> swap chain is the one
 *     legitimate nesting, depth 2). That call is CUT: logged once with the caller's module, every slot we patched is put back to what it
 *     held, the limiter is dead for the run (klfps_dead) and the frame is dropped (S_OK) instead of recursing.
 *   - depth 0 times and waits; a nested call (depth 1, 2) or a dead limiter just forwards.
 *   - nothing is wrapped when the slot already holds one of OUR wrappers (a second device) ; a swap chain that shares the device's vtable is skipped.
 *   - [FrameLimit] SwapChain=0 skips the swap chain wrap, Reset=0 the Reset wrap; the first 3 calls of each route log depth and caller module. */
#define KLFPS_MAXDEPTH 3
static DWORD klfps_tls = TLS_OUT_OF_INDEXES;
static volatile LONG klfps_dead, klfps_cut_logged;
static int klfps_use_sc = 1, klfps_use_reset = 1;
static struct { void **slot; void *mine, *real; } klfps_wr[8];
static int klfps_nwr;
static HRESULT WINAPI klfps_reset(void *self, void *pp);
static HRESULT WINAPI klfps_createdev(void *self, UINT adapter, DWORD type, HWND focus, DWORD flags, void *pp, void **dev);

static const char *klfps_mod(const void *p, char *buf, size_t n)
{   /* "name.dll+0xoff" of the module holding p, for the log */
    HMODULE m = 0; char path[MAX_PATH], *b;
    buf[0] = 0;
    if (p && GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)p, &m) && m
        && GetModuleFileNameA(m, path, sizeof path)) {
        b = strrchr(path, '\\'); b = b ? b + 1 : path;
        _snprintf(buf, n, "%s+0x%x", b, (unsigned)((const char *)p - (const char *)m)); buf[n - 1] = 0;
    } else { _snprintf(buf, n, "%p", p); buf[n - 1] = 0; }
    return buf;
}

static void klfps_unwrap_all(void)
{
    int i;
    for (i = 0; i < klfps_nwr; i++) {
        void *cur = *klfps_wr[i].slot;
        if (cur == klfps_wr[i].mine) klh_poke(klfps_wr[i].slot, &cur, sizeof cur, &klfps_wr[i].real, sizeof cur, "frame limiter unwrap");
    }
}

static void klfps_cut(const char *route, void *ret)
{
    char m[MAX_PATH + 24];
    InterlockedExchange(&klfps_dead, 1);
    if (!InterlockedExchange(&klfps_cut_logged, 1)) {
        klog("fps: RECURSION CUT at the %s wrapper (depth >= %d on this thread, caller %s): every patched slot restored, the frame limiter is dead for this run",
             route, KLFPS_MAXDEPTH, klfps_mod(ret, m, sizeof m));
        klfps_unwrap_all();
    }
}

static int klfps_depth(void) { return klfps_tls == TLS_OUT_OF_INDEXES ? 0 : (int)(INT_PTR)TlsGetValue(klfps_tls); }
static void klfps_depth_set(int d) { if (klfps_tls != TLS_OUT_OF_INDEXES) TlsSetValue(klfps_tls, (LPVOID)(INT_PTR)d); }

static void klfps_first_calls(const char *route, int d, void *ret)
{
    static volatile LONG n[2]; char m[MAX_PATH + 24];
    LONG k = InterlockedIncrement(&n[route[0] == 'd' ? 0 : 1]);
    if (k <= 3) klog("fps: %s call %ld: depth %d, caller %s", route, (long)k, d, klfps_mod(ret, m, sizeof m));
}

/* the two halves of one Present, shared by the device route (slot 17) and the swap chain route (slot 3). Returns 1 = timed (the caller
 * runs klfps_post), 0 = forward only (nested, or dead), -1 = cut (call nothing, return S_OK). */
static int klfps_pre(const char *route, int d, void *ret)
{
    LARGE_INTEGER n;
    if (d >= KLFPS_MAXDEPTH) { klfps_cut(route, ret); return -1; }
    if (klfps_dead || d > 0) return 0;                        /* nested (device -> swap chain) or the limiter is dead: just forward */
    if (!klfps_seen) { klfps_seen = 1; klog("fps: FIRST Present seen, via the %s route", route); }
    QueryPerformanceCounter(&n);
    if (klfps_adaptive && klfps_target > 0 && klfps_ret) klfps_pace_feed(n.QuadPart - klfps_ret);
    if (klfps_front) klfps_wait();                            /* FRONT EDGE: the delay is the last thing before the original Present */
    QueryPerformanceCounter(&n);
    klfps_stat(n.QuadPart);                                   /* frametime at PRESENTATION */
    return 1;
}

/* GAME THREAD FALLBACK (2026-10-25, e8). FINDING: the RECURSION CUT above fires in EVERY session on the owner's PC (KLHook.log, 27 of
 * the live test logs): the Steam overlay's hook calls the swap chain slot 3 again from gameoverlayrenderer.dll+0x79ab4 (depth 0, 1, 2
 * in the same millisecond) - so since k36 the limiter was dead seconds after the first Present and the game ran at the bare 200 .. 470
 * fps. The cut stays (k34's stack overflow); once it has fired, the same deadline wait runs on the GAME thread instead, once a frame at
 * the main loop's second SteamAPI_RunCallbacks (return 0x87aa82, the one site [Solo] FpsCap uses): the render thread draws what the game
 * thread produced, so a paced game thread paces the presents (GUESS: the 1-frame queue between them adds no extra latency beyond one
 * frame; not measured). Sleep(1) with a 1 ms timer while more than 2.5 ms remain, so the main thread does not spin a whole core.
 * [FrameLimit] GameThread=1 (recommended on; 0 = a cut limiter stays dead, the k36 behaviour). Import slot (RunCallbacks) only: SHIP-safe. */
static int klfps_gt = 1;
static volatile LONG klfps_gt_on;
static void klfps_gtick(DWORD_PTR ra)
{
    LARGE_INTEGER n;
    if (!klfps_dead || !klfps_gt || klfps_target <= 0 || !klfps_freq) return;
    if (ra != (DWORD_PTR)KLH_VA(0x0087aa82u)) return;               /* once a frame: the main loop's second call only */
    if (!klfps_gt_on) {
        typedef DWORD (WINAPI *tbp_fn)(UINT); HMODULE m = LoadLibraryA("winmm.dll"); tbp_fn tbp = m ? (tbp_fn)GetProcAddress(m, "timeBeginPeriod") : 0;
        if (tbp && !klfps_passive) tbp(1);
        klfps_passive = 1; klfps_deadline = 0; klfps_t0 = 0; klfps_last_present = 0;
        InterlockedExchange(&klfps_gt_on, 1);
        klog("fps: game thread fallback ON: %d fps paced on the main loop (Present route cut; [FrameLimit] GameThread=0 turns this off)", klfps_target);
    }
    klfps_wait();
    QueryPerformanceCounter(&n);
    klfps_stat(n.QuadPart);                                         /* the Log=1 line now counts game frames */
}

static void klfps_post(void)
{
    LARGE_INTEGER n;
    if (!klfps_front) klfps_wait();                           /* back edge: the same wait after Present returned */
    QueryPerformanceCounter(&n); klfps_ret = n.QuadPart;
}

static HRESULT WINAPI klfps_present(void *self, const RECT *src, const RECT *dst, HWND wnd, const void *dirty)
{
    HRESULT r; void *ret = _ReturnAddress(); int d = klfps_depth(), t;
    klfps_first_calls("device (slot 17)", d, ret);
    t = klfps_pre("device (slot 17)", d, ret);
    if (t < 0) return 0;
    klfps_depth_set(d + 1);
    r = klfps_real_present(self, src, dst, wnd, dirty);
    klfps_depth_set(d);
    if (t) klfps_post();
    return r;
}

/* IDirect3DSwapChain9::Present (slot 3) has one more argument (dwFlags). 2026-10-24 FINDING: the k29d log of a whole 8 minute session
 * (15:59 .. 16:07) has the 'fps: on' and 'Present wrapped' lines but NOT ONE 'fps: limiter:' line (Log=1: every 10 s): the game never
 * went through the device vtable slot that klfps wrapped. k34's log: the first Present arrived by this swap chain route. */
static HRESULT WINAPI klfps_present_sc(void *self, const RECT *src, const RECT *dst, HWND wnd, const void *dirty, DWORD flags)
{
    HRESULT r; void *ret = _ReturnAddress(); int d = klfps_depth(), t;
    klfps_first_calls("swap chain (slot 3)", d, ret);
    t = klfps_pre("swap chain (slot 3)", d, ret);
    if (t < 0) return 0;
    klfps_depth_set(d + 1);
    r = klfps_real_present_sc(self, src, dst, wnd, dirty, flags);
    klfps_depth_set(d);
    if (t) klfps_post();
    return r;
}

static void klfps_wrap_slot(void *obj, int slot, void *mine, void **real, const char *what)
{
    void **vt = obj ? *(void ***)obj : 0, *cur; char m[MAX_PATH + 24];
    if (!vt) return;
    cur = vt[slot];
    if (cur == mine) return;                                         /* the same class twice: already wrapped */
    if (cur == (void *)klfps_present || cur == (void *)klfps_present_sc || cur == (void *)klfps_reset || cur == (void *)klfps_createdev) {
        klog("fps: %s: slot %d already holds another of our wrappers - left alone", what, slot); return;
    }
    if (*real && *real != cur) { klog("fps: %s: a second class (%p, first %p) - left alone", what, cur, *real); return; }
    if (klfps_nwr >= 8) return;
    *real = cur;
    if (!klh_poke(&vt[slot], &cur, sizeof cur, &mine, sizeof mine, what)) { klog("fps: %s: vtable slot %d not changed", what, slot); *real = 0; return; }
    klfps_wr[klfps_nwr].slot = &vt[slot]; klfps_wr[klfps_nwr].mine = mine; klfps_wr[klfps_nwr].real = cur; klfps_nwr++;
    klog("fps: %s wrapped (vtable %p slot %d, was %p = %s)", what, (void *)vt, slot, cur, klfps_mod(cur, m, sizeof m));
}

/* refresh rate + vsync from a D3DPRESENT_PARAMETERS (CreateDevice and Reset) and a new target */
static void klfps_read_pp(const void *pp)
{
    DWORD hz = 0, interval = 0; DEVMODEA dm; const DWORD *p = (const DWORD *)pp;
    if (p) { hz = p[0x30 / 4]; interval = p[0x34 / 4]; }      /* D3DPRESENT_PARAMETERS +0x30 FullScreen_RefreshRateInHz, +0x34 PresentationInterval (klsolo.c) */
    if (!hz || hz > 1000) {
        /* user32 is not on the build's link line: looked up (the game has it loaded) */
        typedef BOOL (WINAPI *eds_fn)(LPCSTR, DWORD, DEVMODEA *);
        HMODULE u = GetModuleHandleA("user32.dll"); eds_fn eds = u ? (eds_fn)GetProcAddress(u, "EnumDisplaySettingsA") : 0;
        memset(&dm, 0, sizeof dm); dm.dmSize = sizeof dm;
        hz = (eds && eds(0, ENUM_CURRENT_SETTINGS, &dm)) ? dm.dmDisplayFrequency : 0;
    }
    if (hz <= 1 || hz > 1000) hz = 60;                         /* 0 / 1 = 'hardware default' in DEVMODE */
    klfps_auto_hz = (int)hz;
    klfps_vsync = (interval != 0x80000000u);                   /* 0 DEFAULT = ONE, 1..4 = vblank multiples, 0x80000000 = IMMEDIATE */
    klfps_set_target();
    klfps_pace = 0; klfps_ret = 0; klfps_last_present = 0;
}

/* IDirect3DDevice9::Reset (slot 16): the options menu / alt-tab rebuilds the device, maybe at another refresh rate or vsync setting.
 * The target is re-read from the new parameters and the pacing restarts (the deadline would be stale). The real Reset runs first. */
static HRESULT WINAPI klfps_reset(void *self, void *pp)
{
    HRESULT r = klfps_real_reset(self, pp);
    klfps_resets++;
    if (r >= 0) { klfps_read_pp(pp); klog("fps: Reset ok: refresh %d Hz, game vsync %s, target %d fps", klfps_auto_hz, klfps_vsync ? "ON" : "off", klfps_target); }
    else { klfps_deadline = 0; klfps_pace = 0; klfps_ret = 0; }
    return r;
}

static HRESULT WINAPI klfps_createdev(void *self, UINT adapter, DWORD type, HWND focus, DWORD flags, void *pp, void **dev)
{
    HRESULT r = klfps_real_createdev(self, adapter, type, focus, flags, pp, dev);
    if (r >= 0 && dev && *dev) {
        klfps_read_pp(pp);
        if (klfps_use_reset) klfps_wrap_slot(*dev, 16, (void *)klfps_reset, (void **)&klfps_real_reset, "Reset");
        klfps_wrap_slot(*dev, 17, (void *)klfps_present, (void **)&klfps_real_present, "Present");
        {   /* the implicit swap chain: IDirect3DDevice9::GetSwapChain (slot 14), then its Release (slot 2) */
            typedef HRESULT (WINAPI *gsc_fn)(void *, UINT, void **); typedef ULONG (WINAPI *rel_fn)(void *);
            void **dvt = *(void ***)*dev, *sc = 0;
            HRESULT hr = ((gsc_fn)dvt[14])(*dev, 0, &sc);
            if (hr >= 0 && sc) {
                if (!klfps_use_sc) klog("fps: swap chain Present not wrapped ([FrameLimit] SwapChain=0)");
                else if (*(void ***)sc == dvt) klog("fps: swap chain %p shares the device's vtable %p - swap chain Present not wrapped", sc, (void *)dvt);
                else klfps_wrap_slot(sc, 3, (void *)klfps_present_sc, (void **)&klfps_real_present_sc, "SwapChain Present");
                ((rel_fn)(*(void ***)sc)[2])(sc);
            } else klog("fps: GetSwapChain(0) failed (%08lx): swap chain Present not wrapped", (unsigned long)hr);
        }
        klog("fps: device %p: refresh %d Hz, game vsync %s, target %d fps%s; %s edge, %s wait", *dev, klfps_auto_hz,
             klfps_vsync ? "ON" : "off", klfps_target, klfps_target ? "" : " (timing only: game vsync paces it, or set Fps=)",
             klfps_front ? "front" : "back", klfps_passive ? "passive+busy" : "busy");
    } else klog("fps: CreateDevice returned %08lx - Present not wrapped", (unsigned long)r);
    return r;
}

static void *WINAPI klfps_create9(UINT sdk)
{
    void *d3d = klfps_real_create9(sdk);
    if (d3d) klfps_wrap_slot(d3d, 16, (void *)klfps_createdev, (void **)&klfps_real_createdev, "CreateDevice");
    return d3d;
}

/* AFTER kltx_init and klso_init: this Direct3DCreate9 wrapper must be the outermost */
static void klfps_init(void)
{
    LARGE_INTEGER f;
    klfps_enable = GetPrivateProfileIntA("FrameLimit", "Enable", 1, klh_ini);
    if (!klfps_enable) { klog("fps: frame limiter off ([FrameLimit] Enable=0)"); return; }
    klfps_fps_ini = GetPrivateProfileIntA("FrameLimit", "Fps", 0, klh_ini);
    if (klfps_fps_ini < 0 || klfps_fps_ini > 1000) klfps_fps_ini = 0;
    else if (klfps_fps_ini > 0 && klfps_fps_ini < 10) klfps_fps_ini = 10;
    klfps_front   = GetPrivateProfileIntA("FrameLimit", "FrontEdge", 1, klh_ini) != 0;
    klfps_passive = GetPrivateProfileIntA("FrameLimit", "PassiveWait", 0, klh_ini) != 0;
    klfps_log     = GetPrivateProfileIntA("FrameLimit", "Log", 0, klh_ini) != 0;
    klfps_adaptive = GetPrivateProfileIntA("FrameLimit", "Adaptive", 0, klh_ini) != 0;
    klfps_use_sc    = GetPrivateProfileIntA("FrameLimit", "SwapChain", 1, klh_ini) != 0;   /* k36: 0 = do not wrap IDirect3DSwapChain9::Present */
    klfps_use_reset = GetPrivateProfileIntA("FrameLimit", "Reset", 1, klh_ini) != 0;       /* k36: 0 = do not wrap IDirect3DDevice9::Reset */
    klfps_gt        = GetPrivateProfileIntA("FrameLimit", "GameThread", 1, klh_ini) != 0;  /* 1025: pace on the game thread after a cut */
    klfps_tls = TlsAlloc();                                         /* per-thread nesting depth (k36 recursion guard); TLS_OUT_OF_INDEXES = depth always 0 */
    QueryPerformanceFrequency(&f); klfps_freq = f.QuadPart;
    if (klfps_passive) {                                            /* Sleep(1) is only useful with a 1 ms timer */
        typedef DWORD (WINAPI *tbp_fn)(UINT); HMODULE m = LoadLibraryA("winmm.dll"); tbp_fn tbp = m ? (tbp_fn)GetProcAddress(m, "timeBeginPeriod") : 0;
        if (tbp) tbp(1);
    }
    if (!klh_iat("d3d9.dll", "Direct3DCreate9", (void *)klfps_create9, (void **)&klfps_real_create9))
        klog("fps: d3d9.dll!Direct3DCreate9 import not wrapped - no frame limiter");
    else klog("fps: on (Fps=%d%s, FrontEdge=%d, PassiveWait=%d, Log=%d, Adaptive=%d); Direct3DCreate9 wrapped (was %p)", klfps_fps_ini, klfps_fps_ini ? "" : " = auto",
              klfps_front, klfps_passive, klfps_log, klfps_adaptive, (void *)klfps_real_create9);
}

#endif /* KLFPS_C */
