/* kld3.c - [Memory] D3dCount: a TEST-only probe that counts the Direct3D 9 calls the game makes, per device vtable slot, so a live run
   can put the nvd3dum small-block pile (klarena.c's 'arena:' line) next to what the game asks of the driver (default 0).
   Plus [Memory] D3dFlushEvery=N (default 0): every N presents an EVENT query is issued and waited for (GPU idle) - does the pile go
   back to the driver then?

   Why (K49G..K49J, DM05A 2026-10-25): the pile grows only above ~60 fps, 40 blocks of ~2.8 KB per frame are taken and given back at
   any rate, ~0.43 x (fps - 60) more per frame stay until one mass free (a 130-190 ms hitch) at address-space exhaustion. Static
   reading of kl2.exe found no per-frame Create* call; the next suspect is plain call volume (a driver command queue). Nothing logged
   a draw / constant / state count so far.

   How: klfps.c's CreateDevice wrapper hands the device to kld3_device(). Every IDirect3DDevice9 vtable slot (119) except Reset (16) and
   Present (17), which klfps.c owns, gets a 16-byte thunk in a small executable page of ours: 'lock inc [count]; jmp [real]' - __stdcall
   needs no argument handling. Wrapped by hand besides (they also count): CreateTexture (23), CreateVertexBuffer (26), CreateIndexBuffer
   (27), DrawPrimitiveUP (83), DrawIndexedPrimitiveUP (84). The first buffer / texture each Create* returns shows the class vtable, whose
   Lock (VB, IB: slot 11) / LockRect (texture: slot 20) is wrapped once: DISCARD / NOOVERWRITE / other histogram and the bytes asked.
   Present (called from klfps.c's two Present wrappers) counts frames and runs the flush experiment, then the 10 s line is logged from
   klh_tick next to klarena_tick. Data in our own memory plus the device / buffer vtables (klh_poke); no game code bytes are written. */

#define KLD3_NSLOT 119
#define KLD3_FLUSH_MAXMS 50

static int kld3_on, kld3_flush_n;
static volatile LONG kld3_n[KLD3_NSLOT], kld3_snap[KLD3_NSLOT];
static void *kld3_real[KLD3_NSLOT];
static BYTE *kld3_page;
static void **kld3_vt_seen[4];                          /* the device vtables patched (a second CreateDevice on the same class is left alone) */
static volatile LONG kld3_frames, kld3_frames_snap;
static volatile LONG kld3_lk[3][4], kld3_lk_snap[3][4];  /* [VB, IB, texture][DISCARD, NOOVERWRITE, other, whole-buffer (size 0)] */
static volatile LONG64 kld3_lkbytes[3], kld3_lkbytes_snap[3], kld3_upbytes[2], kld3_upbytes_snap[2];
static void *kld3_lk_real[3]; static void **kld3_lk_vt[3]; static int kld3_lk_bad[3];
#define KLD3_RD64(p) InterlockedCompareExchange64((volatile LONG64 *)(p), 0, 0)   /* atomic 64-bit read on x86-32 (a plain read can tear) */
static volatile LONG kld3_fl_n, kld3_fl_to, kld3_fl_big, kld3_fl_told;   /* flush experiment: runs, timeouts, drops of >= 8 MB, lines told */
static volatile LONG64 kld3_fl_us, kld3_fl_maxus, kld3_fl_drop;          /* wait time sum / max in microseconds, in-use fall sum (bytes) */
static void *kld3_query; static LARGE_INTEGER kld3_qf; static int kld3_cqfail, kld3_qtold;
static volatile LONG kld3_win_t;
static LONG64 kld3_inuse0, kld3_nalloc0, kld3_nfree0;

static const char *const kld3_name[KLD3_NSLOT] = {
    "QueryInterface", "AddRef", "Release", "TestCooperativeLevel", "GetAvailableTextureMem", "EvictManagedResources", "GetDirect3D", "GetDeviceCaps",
    "GetDisplayMode", "GetCreationParameters", "SetCursorProperties", "SetCursorPosition", "ShowCursor", "CreateAdditionalSwapChain", "GetSwapChain",
    "GetNumberOfSwapChains", "Reset", "Present", "GetBackBuffer", "GetRasterStatus", "SetDialogBoxMode", "SetGammaRamp", "GetGammaRamp", "CreateTexture",
    "CreateVolumeTexture", "CreateCubeTexture", "CreateVertexBuffer", "CreateIndexBuffer", "CreateRenderTarget", "CreateDepthStencilSurface",
    "UpdateSurface", "UpdateTexture", "GetRenderTargetData", "GetFrontBufferData", "StretchRect", "ColorFill", "CreateOffscreenPlainSurface",
    "SetRenderTarget", "GetRenderTarget", "SetDepthStencilSurface", "GetDepthStencilSurface", "BeginScene", "EndScene", "Clear", "SetTransform",
    "GetTransform", "MultiplyTransform", "SetViewport", "GetViewport", "SetMaterial", "GetMaterial", "SetLight", "GetLight", "LightEnable",
    "GetLightEnable", "SetClipPlane", "GetClipPlane", "SetRenderState", "GetRenderState", "CreateStateBlock", "BeginStateBlock", "EndStateBlock",
    "SetClipStatus", "GetClipStatus", "GetTexture", "SetTexture", "GetTextureStageState", "SetTextureStageState", "GetSamplerState", "SetSamplerState",
    "ValidateDevice", "SetPaletteEntries", "GetPaletteEntries", "SetCurrentTexturePalette", "GetCurrentTexturePalette", "SetScissorRect",
    "GetScissorRect", "SetSoftwareVertexProcessing", "GetSoftwareVertexProcessing", "SetNPatchMode", "GetNPatchMode", "DrawPrimitive",
    "DrawIndexedPrimitive", "DrawPrimitiveUP", "DrawIndexedPrimitiveUP", "ProcessVertices", "CreateVertexDeclaration", "SetVertexDeclaration",
    "GetVertexDeclaration", "SetFVF", "GetFVF", "CreateVertexShader", "SetVertexShader", "GetVertexShader", "SetVertexShaderConstantF",
    "GetVertexShaderConstantF", "SetVertexShaderConstantI", "GetVertexShaderConstantI", "SetVertexShaderConstantB", "GetVertexShaderConstantB",
    "SetStreamSource", "GetStreamSource", "SetStreamSourceFreq", "GetStreamSourceFreq", "SetIndices", "GetIndices", "CreatePixelShader",
    "SetPixelShader", "GetPixelShader", "SetPixelShaderConstantF", "GetPixelShaderConstantF", "SetPixelShaderConstantI", "GetPixelShaderConstantI",
    "SetPixelShaderConstantB", "GetPixelShaderConstantB", "DrawRectPatch", "DrawTriPatch", "DeletePatch", "CreateQuery" };

static void kld3_lockcount(int kind, DWORD flags, DWORD size)
{   /* kind 0 VB, 1 IB, 2 texture */
    InterlockedIncrement(&kld3_lk[kind][flags & 0x2000 ? 0 : flags & 0x1000 ? 1 : 2]);
    if (!size) InterlockedIncrement(&kld3_lk[kind][3]); else InterlockedExchangeAdd64(&kld3_lkbytes[kind], size);
}

/* K50A (DM05A 120 fps): nvd3dum blocks taken per frame == VB DISCARD locks per frame (55/55, 71/71, 82/76) and a GPU flush every
 * frame (K50B) did not shrink the pile, so the ~2.8 KB blocks look like per-DISCARD rename records the driver keeps. WHO discards:
 * per 10 s window, the two return addresses above Lock (the game's wrapper and its caller) of every DISCARD VB lock, with the
 * buffer's size / usage / pool (IDirect3DVertexBuffer9::GetDesc, slot 13) and the number of distinct buffers discarded. */
#include <intrin.h>                                       /* _ReturnAddress */
typedef struct { void *ra[2]; LONG n; DWORD size, usage, pool; } kld3_dc_t;
static kld3_dc_t kld3_dc[128]; static LONG kld3_dc_lost;
static void *kld3_dbuf[2048]; static LONG kld3_dbuf_n;                  /* distinct buffers DISCARDed in the window (open addressing) */
static CRITICAL_SECTION kld3_dc_cs; static int kld3_dc_ok;
typedef HRESULT (WINAPI *kld3_vbdesc_fn)(void *, DWORD *);
static __declspec(noinline) void kld3_discard(void *self, void *ra)
{
    void *bt[2] = { 0 }, *st[8]; DWORD h, i, k, desc[6] = { 0 }; int fresh = 0, m;
    if (!kld3_dc_ok) return;
    bt[0] = ra;                                                      /* the game's Lock caller (_ReturnAddress in the wrapper) */
    m = RtlCaptureStackBackTrace(0, 8, st, 0);                       /* its caller: the entry after ra, if the walk found ra (our frames may lack EBP) */
    for (i = 0; (int)i + 1 < m; i++) if (st[i] == ra) { bt[1] = st[i + 1]; break; }
    EnterCriticalSection(&kld3_dc_cs);
    h = ((DWORD)(DWORD_PTR)self >> 4) * 2654435761u;
    for (i = 0; i < 2048; i++) { k = (h + i) & 2047; if (kld3_dbuf[k] == self) break; if (!kld3_dbuf[k]) { kld3_dbuf[k] = self; kld3_dbuf_n++; fresh = 1; break; } }
    h = ((DWORD)(DWORD_PTR)bt[0] ^ (DWORD)(DWORD_PTR)bt[1] * 31u) * 2654435761u;
    for (i = 0; i < 128; i++) {
        kld3_dc_t *e = &kld3_dc[(h + i) & 127];
        if (e->n && e->ra[0] == bt[0] && e->ra[1] == bt[1]) { e->n++; break; }
        if (!e->n) { e->ra[0] = bt[0]; e->ra[1] = bt[1]; e->n = 1; fresh = 1; break; }
    }
    if (i == 128) kld3_dc_lost++;
    LeaveCriticalSection(&kld3_dc_cs);
    if (fresh && i < 128 && ((void ***)self)[0][13]) {               /* a new buffer or caller: its desc (Format, Type, Usage, Pool, Size, FVF) */
        if (((kld3_vbdesc_fn)((void ***)self)[0][13])(self, desc) >= 0) {
            kld3_dc_t *e = &kld3_dc[(h + i) & 127]; e->size = desc[4]; e->usage = desc[2]; e->pool = desc[3];
        }
    }
}

typedef HRESULT (WINAPI *kld3_lock_fn)(void *, UINT, UINT, void **, DWORD);
typedef HRESULT (WINAPI *kld3_lockrect_fn)(void *, UINT, void *, const void *, DWORD);

/* [Memory] D3dRing=N (TEST, default 0 = off; N clamped 16..512). K50D (DM05A 120 fps): every VB DISCARD lock (55-65 per frame, one
 * driver block of ~2.8 KB each) comes from KL2+0x47bdbf in the game's lock wrapper 0x87bda0, on the 4 tiny quad buffers whose game
 * objects sit at the globals 0xf645c0 / c4 / c8 / cc (whole-buffer DISCARD from 0x45a084, 0x570380, 0x62ce10, 0x886c10, 0x900300;
 * 144 / 176 bytes, DYNAMIC|WRITEONLY, DEFAULT pool). The lever: each of those game objects gets N real buffers of the same desc
 * (slot 0 = the game's own); on a DISCARD lock the game object's +0x18 (its real VB, read fresh by Unlock and by the stream bind, e.g.
 * 0x5705d1) is moved to the next buffer, which is locked NOOVERWRITE instead - no driver rename, so no block. At ~15 locks per object
 * per frame N=128 is ~8 frames before a buffer is reused (more than the frames the driver queues).
 * References: we hold one on every ring buffer (the game's own included), the game holds its usual one on whichever +0x18 names
 * (moved with the swap: AddRef new, Release old). The game's lost-device path (0x84eb50 -> 0x456bf0, class 0xb99cbc slot 3) releases
 * +0x18; kld3_prereset (klfps.c's Reset wrapper, before the real Reset) drops our references, so no DEFAULT buffer outlives Reset.
 * A game object whose +0x18 is not its ring's current buffer (recreated) gets a fresh ring. Only buffers <= 1 KB with usage 0x208. */
#define KLD3_NOBJ 4
typedef HRESULT (WINAPI *kld3_cbuf_fn)(void *, UINT, DWORD, DWORD, DWORD, void **, void *);
static int kld3_ring_n;
static struct { void *obj; void **buf; int n, cur; } kld3_rg[KLD3_NOBJ];
static CRITICAL_SECTION kld3_rg_cs; static int kld3_rg_ok;
static volatile LONG kld3_rg_swaps, kld3_rg_made, kld3_rg_fail, kld3_rg_drops;
typedef ULONG (WINAPI *kld3_ref_fn)(void *);
#define KLD3_ADDREF(p) ((kld3_ref_fn)(*(void ***)(p))[1])(p)
#define KLD3_RELEASE(p) ((kld3_ref_fn)(*(void ***)(p))[2])(p)
static void kld3_rg_drop(int g)
{   /* our references on ring g (the game keeps its own on +0x18) */
    int i;
    if (kld3_rg[g].buf) { for (i = 0; i < kld3_ring_n; i++) if (kld3_rg[g].buf[i]) KLD3_RELEASE(kld3_rg[g].buf[i]); free(kld3_rg[g].buf); InterlockedIncrement(&kld3_rg_drops); }
    kld3_rg[g].buf = 0; kld3_rg[g].obj = 0; kld3_rg[g].n = 0; kld3_rg[g].cur = 0;
}
static void kld3_prereset(void)
{
    int g;
    if (!kld3_rg_ok) return;
    EnterCriticalSection(&kld3_rg_cs);
    for (g = 0; g < KLD3_NOBJ; g++) kld3_rg_drop(g);
    LeaveCriticalSection(&kld3_rg_cs);
    klog("d3count: ring: Reset - our buffer references dropped (rings rebuilt on the next DISCARD)");
}
/* the DISCARD lock of one of the 4 quad buffers: swap +0x18 to the next ring buffer and lock that NOOVERWRITE; 0 = not ours, lock as asked */
static int kld3_rg_lock(void *self, UINT off, UINT size, void **pp, DWORD flags, HRESULT *hr)
{
    typedef HRESULT (WINAPI *gdev_fn)(void *, void **);
    DWORD desc[6] = { 0 }; int g, nx; void *obj = 0, *nb, *dev = 0; void **slot;
    for (g = 0; g < KLD3_NOBJ; g++) {
        __try { obj = *(void **)(DWORD_PTR)(0xf645c0 + 4 * g); if (obj && *(void **)((BYTE *)obj + 0x18) == self) break; } __except (1) { obj = 0; }
    }
    if (g == KLD3_NOBJ) return 0;
    slot = (void **)((BYTE *)obj + 0x18);
    EnterCriticalSection(&kld3_rg_cs);
    if (kld3_rg[g].buf && (kld3_rg[g].obj != obj || kld3_rg[g].buf[kld3_rg[g].cur] != self)) kld3_rg_drop(g);   /* recreated */
    if (!kld3_rg[g].buf) {
        if (((kld3_vbdesc_fn)(*(void ***)self)[13])(self, desc) < 0 || desc[4] > 1024 || desc[2] != 0x208) { LeaveCriticalSection(&kld3_rg_cs); return 0; }
        kld3_rg[g].buf = (void **)calloc(kld3_ring_n, sizeof(void *));
        if (!kld3_rg[g].buf) { LeaveCriticalSection(&kld3_rg_cs); return 0; }
        kld3_rg[g].obj = obj; kld3_rg[g].buf[0] = self; KLD3_ADDREF(self); kld3_rg[g].cur = 0; kld3_rg[g].n = 1;
        klog("d3count: ring: game object %d (%p): buffer %p, %lu bytes, fvf %#lx - %d buffers", g, obj, self, (unsigned long)desc[4], (unsigned long)desc[5], kld3_ring_n);
    }
    nx = (kld3_rg[g].cur + 1) % kld3_ring_n;
    if (!kld3_rg[g].buf[nx]) {                                               /* made on first use, same desc, the device's real CreateVertexBuffer */
        if (!desc[4] && ((kld3_vbdesc_fn)(*(void ***)self)[13])(self, desc) < 0) { LeaveCriticalSection(&kld3_rg_cs); return 0; }
        nb = 0;
        if (((gdev_fn)(*(void ***)self)[3])(self, &dev) >= 0 && dev) {       /* IDirect3DResource9::GetDevice (AddRefs) */
            /* the buffer's own device and ITS vtable: with ReShade the game's device is ReShade's proxy (kld3_real[26] is ReShade's
               CreateVertexBuffer) but the buffers are plain d3d9 ones, whose GetDevice is the real device - K50F crashed in
               ReShade32+0x11ac5b calling the proxy's function with the real device */
            kld3_cbuf_fn cvb = (kld3_cbuf_fn)(*(void ***)dev)[26];
            if (cvb(dev, desc[4], desc[2], desc[5], desc[3], &nb, 0) < 0) nb = 0;
            KLD3_RELEASE(dev);
        }
        if (!nb) { InterlockedIncrement(&kld3_rg_fail); LeaveCriticalSection(&kld3_rg_cs); return 0; }   /* plain DISCARD this time */
        kld3_rg[g].buf[nx] = nb; kld3_rg[g].n++; InterlockedIncrement(&kld3_rg_made);
    }
    nb = kld3_rg[g].buf[nx];
    KLD3_ADDREF(nb); *slot = nb; KLD3_RELEASE(self);                         /* the game's reference moves with +0x18 */
    kld3_rg[g].cur = nx;
    LeaveCriticalSection(&kld3_rg_cs);
    InterlockedIncrement(&kld3_rg_swaps);
    *hr = ((kld3_lock_fn)kld3_lk_real[0])(nb, off, size, pp, (flags & ~0x2000) | 0x1000);
    return 1;
}

static HRESULT WINAPI kld3_w_lockvb(void *self, UINT off, UINT size, void **pp, DWORD flags)
{
    HRESULT hr;
    kld3_lockcount(0, flags, size);
    if (flags & 0x2000) {
        if (kld3_rg_ok && kld3_rg_lock(self, off, size, pp, flags, &hr)) return hr;
        kld3_discard(self, _ReturnAddress());
    }
    return ((kld3_lock_fn)kld3_lk_real[0])(self, off, size, pp, flags);
}
static HRESULT WINAPI kld3_w_lockib(void *self, UINT off, UINT size, void **pp, DWORD flags) { kld3_lockcount(1, flags, size); return ((kld3_lock_fn)kld3_lk_real[1])(self, off, size, pp, flags); }
static HRESULT WINAPI kld3_w_lockrect(void *self, UINT lvl, void *lr, const void *rc, DWORD flags) { kld3_lockcount(2, flags, 0); return ((kld3_lockrect_fn)kld3_lk_real[2])(self, lvl, lr, rc, flags); }

static void kld3_patch_lock(int kind, void *obj, int slot, void *mine)
{   /* the class vtable of the first buffer / texture Create* returns: its Lock / LockRect once */
    void **vt = obj ? *(void ***)obj : 0, *cur;
    if (!vt || kld3_lk_vt[kind] == vt || kld3_lk_bad[kind]) return;
    if (kld3_lk_vt[kind]) return;                        /* a second class (other pool / usage): its Lock must NOT go through the first class's saved pointer */
    cur = vt[slot];
    if (cur == mine) return;
    kld3_lk_real[kind] = cur; kld3_lk_vt[kind] = vt;
    if (!klh_poke(&vt[slot], &cur, sizeof cur, &mine, sizeof mine, "D3dCount Lock")) { kld3_lk_vt[kind] = 0; kld3_lk_bad[kind] = 1; klog("d3count: %s lock slot %d not changed", kind == 0 ? "VB" : kind == 1 ? "IB" : "texture", slot); return; }
    klog("d3count: %s %s wrapped (vtable %p slot %d, was %p)", kind == 0 ? "VB" : kind == 1 ? "IB" : "texture", kind == 2 ? "LockRect" : "Lock", (void *)vt, slot, cur);
}

typedef HRESULT (WINAPI *kld3_ctex_fn)(void *, UINT, UINT, UINT, DWORD, DWORD, DWORD, void **, void *);
typedef HRESULT (WINAPI *kld3_cib_fn)(void *, UINT, DWORD, DWORD, DWORD, void **, void *);
static HRESULT WINAPI kld3_w_ctex(void *self, UINT w, UINT h, UINT lv, DWORD us, DWORD fmt, DWORD pool, void **pp, void *sh)
{
    HRESULT r; InterlockedIncrement(&kld3_n[23]);
    r = ((kld3_ctex_fn)kld3_real[23])(self, w, h, lv, us, fmt, pool, pp, sh);
    if (r >= 0 && pp && *pp) kld3_patch_lock(2, *pp, 19, (void *)kld3_w_lockrect);
    return r;
}
static HRESULT WINAPI kld3_w_cvb(void *self, UINT len, DWORD us, DWORD fvf, DWORD pool, void **pp, void *sh)
{
    HRESULT r; InterlockedIncrement(&kld3_n[26]);
    r = ((kld3_cbuf_fn)kld3_real[26])(self, len, us, fvf, pool, pp, sh);
    if (r >= 0 && pp && *pp) kld3_patch_lock(0, *pp, 11, (void *)kld3_w_lockvb);
    return r;
}
static HRESULT WINAPI kld3_w_cib(void *self, UINT len, DWORD us, DWORD fmt, DWORD pool, void **pp, void *sh)
{
    HRESULT r; InterlockedIncrement(&kld3_n[27]);
    r = ((kld3_cib_fn)kld3_real[27])(self, len, us, fmt, pool, pp, sh);
    if (r >= 0 && pp && *pp) kld3_patch_lock(1, *pp, 11, (void *)kld3_w_lockib);
    return r;
}

typedef HRESULT (WINAPI *kld3_dpup_fn)(void *, DWORD, UINT, const void *, UINT);
typedef HRESULT (WINAPI *kld3_dipup_fn)(void *, DWORD, UINT, UINT, UINT, const void *, DWORD, const void *, UINT);
static HRESULT WINAPI kld3_w_dpup(void *self, DWORD type, UINT n, const void *p, UINT stride)
{
    static const BYTE add[7] = { 0, 0, 0, 1, 0, 2, 2 }, mul[7] = { 0, 1, 2, 1, 3, 1, 1 };   /* vertices = n * mul + add per D3DPRIMITIVETYPE 1..6 */
    InterlockedIncrement(&kld3_n[83]);
    if (type >= 1 && type <= 6) InterlockedExchangeAdd64(&kld3_upbytes[0], (LONG64)(n * mul[type] + add[type]) * stride);
    return ((kld3_dpup_fn)kld3_real[83])(self, type, n, p, stride);
}
static HRESULT WINAPI kld3_w_dipup(void *self, DWORD type, UINT minv, UINT nv, UINT n, const void *idx, DWORD fmt, const void *vtx, UINT stride)
{
    static const BYTE add[7] = { 0, 0, 0, 1, 0, 2, 2 }, mul[7] = { 0, 1, 2, 1, 3, 1, 1 };
    InterlockedIncrement(&kld3_n[84]);
    if (type >= 1 && type <= 6) InterlockedExchangeAdd64(&kld3_upbytes[1], (LONG64)nv * stride + (LONG64)(n * mul[type] + add[type]) * (fmt == 102 ? 4 : 2));
    return ((kld3_dipup_fn)kld3_real[84])(self, type, minv, nv, n, idx, fmt, vtx, stride);
}

static int kld3_ours(const void *p)
{
    if (kld3_page && (const BYTE *)p >= kld3_page && (const BYTE *)p < kld3_page + KLD3_NSLOT * 16) return 1;
    return p == (void *)kld3_w_ctex || p == (void *)kld3_w_cvb || p == (void *)kld3_w_cib || p == (void *)kld3_w_dpup || p == (void *)kld3_w_dipup;
}

/* klfps.c's CreateDevice wrapper: every slot but Reset / Present gets its counting thunk (once per vtable) */
static void kld3_device(void *dev)
{
    void **vt = dev ? *(void ***)dev : 0; int i, done = 0, k;
    if (!kld3_on || !vt) return;
    for (k = 0; k < 4 && kld3_vt_seen[k] && kld3_vt_seen[k] != vt; k++) ;
    if (k == 4 || kld3_vt_seen[k] == vt) { klog("d3count: device vtable %p already patched (or %d classes seen) - left alone", (void *)vt, k); return; }
    kld3_vt_seen[k] = vt;
    if (!kld3_page) kld3_page = (BYTE *)VirtualAlloc(0, KLD3_NSLOT * 16, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    if (!kld3_page) { klog("d3count: no executable page for the thunks: off"); kld3_on = 0; return; }
    for (i = 0; i < KLD3_NSLOT; i++) {
        void *cur = vt[i], *mine; BYTE *t = kld3_page + i * 16; volatile LONG *cnt = &kld3_n[i]; void **rp = &kld3_real[i];
        if (i == 16 || i == 17 || !cur || kld3_ours(cur)) continue;            /* Reset / Present: klfps.c's; or already ours */
        if (kld3_real[i] && kld3_real[i] != cur) { klog("d3count: slot %d (%s): a second class (%p, first %p) - left alone", i, kld3_name[i], cur, kld3_real[i]); continue; }
        kld3_real[i] = cur;
        t[0] = 0xF0; t[1] = 0xFF; t[2] = 0x05; memcpy(t + 3, &cnt, 4);       /* lock inc dword [cnt] */
        t[7] = 0xFF; t[8] = 0x25; memcpy(t + 9, &rp, 4);                     /* jmp dword [real] */
        mine = i == 23 ? (void *)kld3_w_ctex : i == 26 ? (void *)kld3_w_cvb : i == 27 ? (void *)kld3_w_cib : i == 83 ? (void *)kld3_w_dpup : i == 84 ? (void *)kld3_w_dipup : (void *)t;
        if (klh_poke(&vt[i], &cur, sizeof cur, &mine, sizeof mine, "D3dCount")) done++; else kld3_real[i] = 0;
    }
    FlushInstructionCache(GetCurrentProcess(), kld3_page, KLD3_NSLOT * 16);
    klog("d3count: device %p vtable %p: %d of %d slots counted (Reset / Present left to klfps.c)%s", dev, (void *)vt, done, KLD3_NSLOT - 2, kld3_flush_n ? "; flush experiment on" : "");
}

/* [Memory] D3dShotEvery=S (TEST, default 0 = off): every S seconds the back buffer (before Present: the finished frame, HUD
 * included) is saved as KLShot_<tag>_NN.jpg into [Memory] D3dShotDir (default: the game folder), at most 40 per run, with the
 * game's own d3dx9_42 D3DXSaveSurfaceToFileA. Why: a desktop grab of the full-screen game is black, and D3dRing needs a look
 * at the post-process passes (bloom / blur) it touches. */
static int kld3_shot_s, kld3_shot_n, kld3_shot_from; static DWORD kld3_shot_t0; static char kld3_shot_dir[MAX_PATH], kld3_shot_tag[64];
static void kld3_shot(void *dev)
{
    typedef HRESULT (WINAPI *gbb_fn)(void *, UINT, UINT, DWORD, void **);
    typedef HRESULT (WINAPI *save_fn)(const char *, DWORD, void *, const void *, const RECT *);
    static DWORD last; static save_fn save; static int told; char path[MAX_PATH + 96]; void *bb = 0; HRESULT hr;
    DWORD now = GetTickCount();
    if (kld3_shot_from && now - kld3_shot_t0 < (DWORD)kld3_shot_from * 1000) return;   /* D3dShotFrom: the 40 shots start that late */
    if (kld3_shot_n >= 40 || (last && now - last < (DWORD)kld3_shot_s * 1000)) return;
    if (!last) { last = now; return; }
    last = now;
    if (!save) { HMODULE m = GetModuleHandleA("d3dx9_42.dll"); save = m ? (save_fn)GetProcAddress(m, "D3DXSaveSurfaceToFileA") : 0; }
    if (!save) { if (!told++) klog("d3count: shot: d3dx9_42 D3DXSaveSurfaceToFileA not found - no shots"); kld3_shot_n = 40; return; }
    if (((gbb_fn)(*(void ***)dev)[18])(dev, 0, 0, 0, &bb) < 0 || !bb) { if (!told++) klog("d3count: shot: GetBackBuffer failed"); return; }
    _snprintf(path, sizeof path, "%s%sKLShot_%s_%02d.jpg", kld3_shot_dir, kld3_shot_dir[0] ? "\\" : "", kld3_shot_tag, kld3_shot_n);
    path[sizeof path - 1] = 0;
    hr = save(path, 1, bb, 0, 0);                                            /* D3DXIFF_JPG = 1 */
    ((ULONG (WINAPI *)(void *))(*(void ***)bb)[2])(bb);
    kld3_shot_n++;
    klog("d3count: shot %d: %s (%08lx)", kld3_shot_n, path, (unsigned long)hr);
}

/* klfps.c's Present wrappers (outermost call only): one frame; the optional flush experiment */
static void kld3_present(void *dev)
{
    typedef HRESULT (WINAPI *cq_fn)(void *, DWORD, void **); typedef HRESULT (WINAPI *iss_fn)(void *, DWORD); typedef HRESULT (WINAPI *gd_fn)(void *, void *, DWORD, DWORD);
    LONG f; void **qvt; LARGE_INTEGER a, b; LONG64 before, after, us; HRESULT hr; BOOL data = 0; int to = 0;
    if (!kld3_on) return;
    f = InterlockedIncrement(&kld3_frames);
    if (kld3_shot_s && dev) kld3_shot(dev);
    if (!kld3_flush_n || f % kld3_flush_n || !dev) return;
    /* a fresh query per flush, released at once: a default-pool query kept across Present would make a later Reset fail (D3DERR_INVALIDCALL),
       and a kept one dangles when the device is recreated */
    {
        void *q = 0; cq_fn cq = (cq_fn)(kld3_real[118] ? kld3_real[118] : (*(void ***)dev)[118]);
        if (!kld3_qf.QuadPart) QueryPerformanceFrequency(&kld3_qf);
        if (cq(dev, 8, &q) < 0 || !q) { if (++kld3_cqfail >= 5) { klog("d3count: flush: CreateQuery(EVENT) failed %d times - flush experiment off", kld3_cqfail); kld3_flush_n = 0; } return; }   /* D3DQUERYTYPE_EVENT = 8 */
        kld3_query = q;
        if (!kld3_qtold) { kld3_qtold = 1; klog("d3count: flush: EVENT query %p created (one per flush)", q); }
    }
    qvt = *(void ***)kld3_query;
    before = (LONG64)KLD3_RD64(&klar_inuse);
    QueryPerformanceCounter(&a);
    ((iss_fn)qvt[6])(kld3_query, 1);                                          /* Issue(D3DISSUE_END) */
    for (;;) {                                                                /* GetData(D3DGETDATA_FLUSH) until done, 50 ms at most */
        hr = ((gd_fn)qvt[7])(kld3_query, &data, sizeof data, 1);
        QueryPerformanceCounter(&b);
        if (hr != 1) break;                                                   /* S_OK = done, S_FALSE = not yet, negative = lost */
        if ((b.QuadPart - a.QuadPart) * 1000 > kld3_qf.QuadPart * KLD3_FLUSH_MAXMS) { to = 1; break; }
    }
    us = (b.QuadPart - a.QuadPart) * 1000000 / kld3_qf.QuadPart; after = (LONG64)KLD3_RD64(&klar_inuse);
    ((ULONG (WINAPI *)(void *))qvt[2])(kld3_query); kld3_query = 0;           /* Release */
    InterlockedIncrement(&kld3_fl_n); InterlockedExchangeAdd64(&kld3_fl_us, us); if (us > (LONG64)KLD3_RD64(&kld3_fl_maxus)) InterlockedExchange64(&kld3_fl_maxus, us);
    if (to) InterlockedIncrement(&kld3_fl_to);
    if (before > after) InterlockedExchangeAdd64(&kld3_fl_drop, before - after);
    if (before - after >= 8 * 1048576 && kld3_fl_told < 20) {
        InterlockedIncrement(&kld3_fl_told); InterlockedIncrement(&kld3_fl_big);
        klog("d3count: flush: frame %ld: arena in use %.1f -> %.1f MB across the flush (%.2f ms%s, GetData %08lx)", (long)f, before / 1048576.0, after / 1048576.0, us / 1000.0, to ? ", TIMEOUT" : "", (unsigned long)hr);
    }
}

static void kld3_tick(void)
{   /* every 10 s, next to klarena_tick */
    static DWORD last; LONG fr, d[KLD3_NSLOT]; int i, j, top[12], nt = 0; char line[1400]; size_t o = 0; double per;
    LONG64 in, na, nf, bytes[3], up[2]; LONG lk[3][4];
    if (!kld3_on || GetTickCount() - last < 10000) return;
    if (!last) { last = GetTickCount(); }                                    /* first call: start the window (the counters cover load as well) */
    last = GetTickCount();
    fr = kld3_frames - kld3_frames_snap; kld3_frames_snap = kld3_frames;
    for (i = 0; i < KLD3_NSLOT; i++) { LONG c = kld3_n[i]; d[i] = c - kld3_snap[i]; kld3_snap[i] = c; }
    for (i = 0; i < 3; i++) { for (j = 0; j < 4; j++) { LONG c = kld3_lk[i][j]; lk[i][j] = c - kld3_lk_snap[i][j]; kld3_lk_snap[i][j] = c; }
                              { LONG64 c = KLD3_RD64(&kld3_lkbytes[i]); bytes[i] = c - kld3_lkbytes_snap[i]; kld3_lkbytes_snap[i] = c; } }
    for (i = 0; i < 2; i++) { LONG64 c = KLD3_RD64(&kld3_upbytes[i]); up[i] = c - kld3_upbytes_snap[i]; kld3_upbytes_snap[i] = c; }
    per = fr > 0 ? 1.0 / fr : 0.0;
    for (i = 0; i < KLD3_NSLOT; i++) {                                       /* the 12 busiest slots by calls in the window (insertion into top[]) */
        if (d[i] <= 0) continue;
        for (j = nt; j > 0 && d[top[j - 1]] < d[i]; j--) if (j < 12) top[j] = top[j - 1];
        if (j < 12) { top[j] = i; if (nt < 12) nt++; }
    }
    o += sprintf(line + o, "d3count: %ld frames: per frame", (long)fr);
    for (i = 0; i < nt; i++) o += sprintf(line + o, " %s=%.2f", kld3_name[top[i]], d[top[i]] * per);
    klog("%s", line);
    klog("d3count: locks (calls: discard/nooverwrite/other, whole-buffer): VB %ld/%ld/%ld w%ld %.0f KB, IB %ld/%ld/%ld w%ld %.0f KB, tex %ld/%ld/%ld; per frame: VB %.2f IB %.2f tex %.2f; "
         "UP draws: DrawPrimitiveUP %.2f/frame %.1f KB/frame, DrawIndexedPrimitiveUP %.2f/frame %.1f KB/frame",
         (long)lk[0][0], (long)lk[0][1], (long)lk[0][2], (long)lk[0][3], bytes[0] / 1024.0, (long)lk[1][0], (long)lk[1][1], (long)lk[1][2], (long)lk[1][3], bytes[1] / 1024.0,
         (long)lk[2][0], (long)lk[2][1], (long)lk[2][2],
         (lk[0][0] + lk[0][1] + lk[0][2]) * per, (lk[1][0] + lk[1][1] + lk[1][2]) * per, (lk[2][0] + lk[2][1] + lk[2][2]) * per,
         d[83] * per, up[0] * per / 1024.0, d[84] * per, up[1] * per / 1024.0);
    in = klar_on ? (LONG64)KLD3_RD64(&klar_inuse) : 0; na = klar_on ? (LONG64)KLD3_RD64(&klar_nalloc) : 0; nf = klar_on ? (LONG64)KLD3_RD64(&klar_nfree) : 0;
    klog("d3count: window: %ld frames, arena in use %.1f MB (delta %+.1f MB over the window), blocks taken %+I64d (%.1f/frame), given back %+I64d (%.1f/frame)%s",
         (long)fr, in / 1048576.0, (in - kld3_inuse0) / 1048576.0, na - kld3_nalloc0, (na - kld3_nalloc0) * per, nf - kld3_nfree0, (nf - kld3_nfree0) * per, klar_on ? "" : " (DriverArena off: no arena numbers)");
    kld3_inuse0 = in; kld3_nalloc0 = na; kld3_nfree0 = nf;
    if (kld3_dc_ok) {                                                        /* who DISCARDs (kld3_discard): the 8 biggest callers, then a fresh window */
        kld3_dc_t c[128]; LONG nb, lost; int tp[8], ntp = 0; char m0[48], m1[48]; DWORD o0, o1;
        EnterCriticalSection(&kld3_dc_cs);
        memcpy(c, kld3_dc, sizeof c); memset(kld3_dc, 0, sizeof kld3_dc); nb = kld3_dbuf_n; kld3_dbuf_n = 0; memset(kld3_dbuf, 0, sizeof kld3_dbuf);
        lost = kld3_dc_lost; kld3_dc_lost = 0;
        LeaveCriticalSection(&kld3_dc_cs);
        for (i = 0; i < 128; i++) {
            if (!c[i].n) continue;
            for (j = ntp; j > 0 && c[tp[j - 1]].n < c[i].n; j--) if (j < 8) tp[j] = tp[j - 1];
            if (j < 8) { tp[j] = i; if (ntp < 8) ntp++; }
        }
        klog("d3count: VB DISCARD locks: %ld distinct buffer(s) in the window, %d caller pair(s) shown%s", (long)nb, ntp, lost ? " (some callers not tracked: table full)" : "");
        for (i = 0; i < ntp; i++) {
            klh_module((DWORD_PTR)c[tp[i]].ra[0], m0, sizeof m0, &o0); klh_module((DWORD_PTR)c[tp[i]].ra[1], m1, sizeof m1, &o1);
            klog("d3count:   %.2f/frame from %s+%x <- %s+%x; buffer %lu bytes, usage %#lx, pool %lu", c[tp[i]].n * per, m0, o0, m1, o1,
                 (unsigned long)c[tp[i]].size, (unsigned long)c[tp[i]].usage, (unsigned long)c[tp[i]].pool);
        }
    }
    if (kld3_rg_ok) klog("d3count: ring (D3dRing=%d): %ld DISCARD lock(s) turned into NOOVERWRITE on a fresh ring buffer so far, %ld buffer(s) made, %ld create failure(s), %ld ring drop(s)",
                         kld3_ring_n, (long)kld3_rg_swaps, (long)kld3_rg_made, (long)kld3_rg_fail, (long)kld3_rg_drops);
    if (kld3_flush_n) {
        LONG n = kld3_fl_n; klog("d3count: flush every %d: %ld flush(es) so far, avg wait %.2f ms, max %.2f ms, %ld timeout(s) (50 ms), arena in-use fall summed over all flushes %.1f MB, %ld flush(es) dropped >= 8 MB",
                                 kld3_flush_n, (long)n, n ? (LONG64)KLD3_RD64(&kld3_fl_us) / 1000.0 / n : 0.0, (LONG64)KLD3_RD64(&kld3_fl_maxus) / 1000.0, (long)kld3_fl_to, (LONG64)KLD3_RD64(&kld3_fl_drop) / 1048576.0, (long)kld3_fl_big);
    }
}

static void kld3_init(void)
{
    kld3_on = GetPrivateProfileIntA("Memory", "D3dCount", 0, klh_ini) != 0;
    kld3_flush_n = GetPrivateProfileIntA("Memory", "D3dFlushEvery", 0, klh_ini);
    if (kld3_flush_n < 0) kld3_flush_n = 0;
    kld3_shot_s = GetPrivateProfileIntA("Memory", "D3dShotEvery", 0, klh_ini);
    GetPrivateProfileStringA("Memory", "D3dShotDir", "", kld3_shot_dir, sizeof kld3_shot_dir, klh_ini);
    GetPrivateProfileStringA("Memory", "D3dShotTag", "run", kld3_shot_tag, sizeof kld3_shot_tag, klh_ini);
    kld3_shot_from = GetPrivateProfileIntA("Memory", "D3dShotFrom", 0, klh_ini);   /* seconds after the hook loads before the first shot (bench: a late round end within the 40-shot cap); 0 = at once */
    if (kld3_shot_from < 0) kld3_shot_from = 0;
    kld3_shot_t0 = GetTickCount();
    if (kld3_shot_s > 0) kld3_on = 1; else kld3_shot_s = 0;
    kld3_ring_n = GetPrivateProfileIntA("Memory", "D3dRing", 0, klh_ini);
    if (kld3_ring_n) { if (kld3_ring_n < 16) kld3_ring_n = 16; if (kld3_ring_n > 512) kld3_ring_n = 512; kld3_on = 1; InitializeCriticalSection(&kld3_rg_cs); kld3_rg_ok = 1;
                       klog("d3count: ring on (TEST): the 4 quad buffers (0xf645c0..cc) get %d buffers each, DISCARD -> NOOVERWRITE on the next one", kld3_ring_n); }
    if (kld3_flush_n) kld3_on = 1;                                           /* the experiment needs the frame count */
    if (kld3_on) { InitializeCriticalSection(&kld3_dc_cs); kld3_dc_ok = 1; }
    if (kld3_on) klog("d3count: on (TEST): device calls per vtable slot, lock flags, UP draw bytes, every 10 s%s", kld3_flush_n ? "; D3dFlushEvery set" : "");
    if (kld3_flush_n) klog("d3count: flush experiment: every %d present(s) an EVENT query is issued and waited for (50 ms cap)", kld3_flush_n);
}
