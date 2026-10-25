/* klquad.c - [Memory] QuadRing=N: the game's 4 tiny screen-quad vertex buffers get a ring of N buffers each, so the graphics
   driver stops keeping one small block per DISCARD lock (default 0 = off; KLHook.ini ships 128, "(recommended on)").

   Why (K50A-I, DM05A 2026-10-25): Last Call died in round 1 with the 32-bit address space full. nvd3dum.dll takes one ~2.8 KB
   process-heap block per vertex-buffer DISCARD lock and gives them back late; at 120 fps the game makes 55-65 DISCARD locks a
   frame, all from KL2+0x47bdbf in the lock wrapper 0x87bda0, all on the 4 quad buffers whose game objects sit at the globals
   0xf645c0 / c4 / c8 / cc (post-process passes of the render interpreter 0x7c1c30: bloom, blur, grade, full-screen quads; 112 /
   144 / 176 bytes, D3DUSAGE_DYNAMIC|WRITEONLY, DEFAULT pool). Free address space fell 1696 -> 18 MB in 70 s and textures broke
   (K50H). With the ring (TEST kld3.c D3dRing=128, K50F2 / K50G / K50I): 119 fps, free space flat at ~520-560 MB, 0 heap
   refusals, the picture the same as a fresh baseline (K50I vs K50H shots at the same round time).

   How: each game object keeps N real buffers of the same desc (slot 0 = its own). On a DISCARD lock of the buffer a game object's
   +0x18 names, +0x18 is moved to the next ring buffer (the game reads +0x18 fresh in Unlock 0x5a06a0 and in the stream bind
   0x6661f0) and that buffer is locked NOOVERWRITE instead: no rename, no driver block. At ~15 locks per object a frame, N=128 is
   ~8 frames before a buffer comes round again, more than the driver queues. The game's reference moves with +0x18 (AddRef new,
   Release old); we hold one on every ring buffer. Before every IDirect3DDevice9::Reset (klfps.c's wrapper) our references are
   dropped, so no DEFAULT buffer outlives it; the rings are rebuilt on the next DISCARD. Without klfps.c's Reset wrapper
   ([FrameLimit] Enable=0 or Reset=0) the ring stays off. A game object whose +0x18 is not its ring's current buffer (recreated
   by the lost-device path 0x84eb50 -> class 0xb99cbc slots 3 / 4) gets a fresh ring. Only buffers <= 1 KB with usage 0x208.

   Patch: one vtable slot, IDirect3DVertexBuffer9::Lock (11) of the class of the buffer at [0xf645c0]+0x18, written once from the
   tick when that buffer first exists (data, like klfps.c's device slots; no code bytes - SHIP rule). New buffers are made with the
   buffer's OWN device (GetDevice): with ReShade the game's device is a proxy, the buffers are plain d3d9 ones (K50F crashed in
   ReShade32 when the proxy's CreateVertexBuffer got the real device). Works on every map (the 4 objects are the exe's own). */

#ifndef KLQUAD_C
#define KLQUAD_C

#define KLQR_NOBJ 4
#define KLQR_OBJS 0xf645c0                  /* kl2.exe: 4 game objects of the quad buffers; the D3D buffer at +0x18 */
typedef HRESULT (WINAPI *klqr_lock_fn)(void *, UINT, UINT, void **, DWORD);
typedef HRESULT (WINAPI *klqr_desc_fn)(void *, DWORD *);                     /* IDirect3DVertexBuffer9::GetDesc (13): fmt, type, usage, pool, size, fvf */
typedef HRESULT (WINAPI *klqr_cvb_fn)(void *, UINT, DWORD, DWORD, DWORD, void **, void *);
typedef ULONG (WINAPI *klqr_ref_fn)(void *);
#define KLQR_ADDREF(p) ((klqr_ref_fn)(*(void ***)(p))[1])(p)
#define KLQR_RELEASE(p) ((klqr_ref_fn)(*(void ***)(p))[2])(p)

static int klqr_n, klqr_on, klqr_resetok, klqr_done;
static void **klqr_vt; static klqr_lock_fn klqr_real;
static struct { void *obj; void **buf; int cur; } klqr_rg[KLQR_NOBJ];
static CRITICAL_SECTION klqr_cs;
static volatile LONG klqr_swaps, klqr_made, klqr_fail, klqr_drops, klqr_resets;

static void klqr_drop(int g)
{   /* our references on ring g (the game keeps its own on +0x18) */
    int i;
    if (klqr_rg[g].buf) { for (i = 0; i < klqr_n; i++) if (klqr_rg[g].buf[i]) KLQR_RELEASE(klqr_rg[g].buf[i]); free(klqr_rg[g].buf); InterlockedIncrement(&klqr_drops); }
    klqr_rg[g].buf = 0; klqr_rg[g].obj = 0; klqr_rg[g].cur = 0;
}

/* klfps.c's Reset wrapper, before the real Reset */
static void klquad_prereset(void)
{
    int g;
    if (!klqr_on) return;
    EnterCriticalSection(&klqr_cs);
    for (g = 0; g < KLQR_NOBJ; g++) klqr_drop(g);
    LeaveCriticalSection(&klqr_cs);
    InterlockedIncrement(&klqr_resets);
}

/* the DISCARD lock of one of the 4 quad buffers: swap +0x18 to the next ring buffer and lock that NOOVERWRITE; 0 = not ours */
static int klqr_lock(void *self, UINT off, UINT size, void **pp, DWORD flags, HRESULT *hr)
{
    typedef HRESULT (WINAPI *gdev_fn)(void *, void **);
    DWORD desc[6] = { 0 }; int g, nx; void *obj = 0, *nb, *dev = 0; void **slot;
    for (g = 0; g < KLQR_NOBJ; g++) {
        __try { obj = *(void **)(DWORD_PTR)(KLQR_OBJS + 4 * g); if (obj && *(void **)((BYTE *)obj + 0x18) == self) break; } __except (1) { obj = 0; }
    }
    if (g == KLQR_NOBJ) return 0;
    slot = (void **)((BYTE *)obj + 0x18);
    EnterCriticalSection(&klqr_cs);
    if (klqr_rg[g].buf && (klqr_rg[g].obj != obj || klqr_rg[g].buf[klqr_rg[g].cur] != self)) klqr_drop(g);   /* recreated */
    if (!klqr_rg[g].buf) {
        if (((klqr_desc_fn)(*(void ***)self)[13])(self, desc) < 0 || desc[4] > 1024 || desc[2] != 0x208) { LeaveCriticalSection(&klqr_cs); return 0; }
        klqr_rg[g].buf = (void **)calloc(klqr_n, sizeof(void *));
        if (!klqr_rg[g].buf) { LeaveCriticalSection(&klqr_cs); return 0; }
        klqr_rg[g].obj = obj; klqr_rg[g].buf[0] = self; KLQR_ADDREF(self); klqr_rg[g].cur = 0;
    }
    nx = (klqr_rg[g].cur + 1) % klqr_n;
    if (!klqr_rg[g].buf[nx]) {                                                /* made on first use, same desc, the buffer's own device */
        if (!desc[4] && ((klqr_desc_fn)(*(void ***)self)[13])(self, desc) < 0) { LeaveCriticalSection(&klqr_cs); return 0; }
        nb = 0;
        if (((gdev_fn)(*(void ***)self)[3])(self, &dev) >= 0 && dev) {      /* IDirect3DResource9::GetDevice (AddRefs) */
            if (((klqr_cvb_fn)(*(void ***)dev)[26])(dev, desc[4], desc[2], desc[5], desc[3], &nb, 0) < 0) nb = 0;
            KLQR_RELEASE(dev);
        }
        if (!nb) { InterlockedIncrement(&klqr_fail); LeaveCriticalSection(&klqr_cs); return 0; }   /* plain DISCARD this time */
        klqr_rg[g].buf[nx] = nb; InterlockedIncrement(&klqr_made);
    }
    nb = klqr_rg[g].buf[nx];
    KLQR_ADDREF(nb); *slot = nb; KLQR_RELEASE(self);                           /* the game's reference moves with +0x18 */
    klqr_rg[g].cur = nx;
    LeaveCriticalSection(&klqr_cs);
    InterlockedIncrement(&klqr_swaps);
    *hr = klqr_real(nb, off, size, pp, (flags & ~0x2000) | 0x1000);           /* D3DLOCK_DISCARD -> D3DLOCK_NOOVERWRITE */
    return 1;
}

static HRESULT WINAPI klqr_w_lock(void *self, UINT off, UINT size, void **pp, DWORD flags)
{
    HRESULT hr;
    if ((flags & 0x2000) && klqr_on && klqr_lock(self, off, size, pp, flags, &hr)) return hr;
    return klqr_real(self, off, size, pp, flags);
}

/* klfps.c's CreateDevice wrapper, after its own slots: the ring needs klfps.c's Reset wrapper to drop its buffers */
static void klquad_device(void *dev, void *reset_wrapper)
{
    if (!klqr_n) return;
    klqr_resetok = dev && (*(void ***)dev)[16] == reset_wrapper;
    if (!klqr_resetok) klog("quad: ring OFF: IDirect3DDevice9::Reset is not wrapped ([FrameLimit] Reset=0 or the wrap was refused)");
}

/* the tick: wrap Lock once, when the first quad buffer exists; every 60 s a line */
static void klquad_tick(void)
{
    static DWORD last;
    DWORD now;
    if (!klqr_n) return;
    if (!klqr_done && klqr_resetok) {
        void *obj = 0, *vb = 0, **vt = 0, *cur, *mine = (void *)klqr_w_lock; char m[MAX_PATH] = "?"; HMODULE h = 0;
        __try { obj = *(void **)(DWORD_PTR)KLQR_OBJS; vb = obj ? *(void **)((BYTE *)obj + 0x18) : 0; vt = vb ? *(void ***)vb : 0; } __except (1) { vt = 0; }
        if (vt) {
            klqr_done = 1;
            cur = vt[11];
            if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)cur, &h)) GetModuleFileNameA(h, m, sizeof m);
            if (cur == mine) return;
            klqr_real = (klqr_lock_fn)cur; klqr_vt = vt;
            if (!klh_poke(&vt[11], &cur, sizeof cur, &mine, sizeof mine, "QuadRing Lock")) { klog("quad: VB Lock slot not changed - ring off"); klqr_real = 0; return; }
            klqr_on = 1;
            klog("quad: ring of %d on: IDirect3DVertexBuffer9::Lock wrapped (vtable %p slot 11, was %p = %s)", klqr_n, (void *)vt, cur, m);
        }
    }
    now = GetTickCount();
    if (klqr_on && now - last >= 60000) {
        last = now;
        klog("quad: %ld DISCARD lock(s) made NOOVERWRITE, %ld buffer(s) made, %ld create failure(s), %ld ring drop(s), %ld Reset(s)",
             klqr_swaps, klqr_made, klqr_fail, klqr_drops, klqr_resets);
    }
}

static void klquad_init(void)
{
    klqr_n = GetPrivateProfileIntA("Memory", "QuadRing", 0, klh_ini);
    if (klqr_n <= 0) { klqr_n = 0; klog("quad: off ([Memory] QuadRing=0)"); return; }
    if (klqr_n < 16) klqr_n = 16; else if (klqr_n > 512) klqr_n = 512;
#ifdef KLHOOK_TEST
    if (GetPrivateProfileIntA("Memory", "D3dRing", 0, klh_ini) > 0) { klqr_n = 0; klog("quad: off: the TEST ring kld3.c D3dRing is on"); return; }
#endif
    InitializeCriticalSection(&klqr_cs);
    klog("quad: QuadRing=%d: the 4 screen-quad vertex buffers get a ring each (wrapped once the first exists)", klqr_n);
}

#endif /* KLQUAD_C */
