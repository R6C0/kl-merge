/* ---- D3D9 back-buffer capture: hook Present (device + swap chain) via hot-patch ---- */
#include <d3d9.h>
typedef HRESULT (WINAPI *DevPresent_t)(IDirect3DDevice9*, const RECT*, const RECT*, HWND, const RGNDATA*);
typedef HRESULT (WINAPI *ScPresent_t)(IDirect3DSwapChain9*, const RECT*, const RECT*, HWND, const RGNDATA*, DWORD);
static DevPresent_t g_origDevPresent; static ScPresent_t g_origScPresent;
static volatile LONG g_shotReq, g_devPresents, g_scPresents;
static char g_shotName[64] = "ANP_shot.bmp";

static void d3d_capture(IDirect3DDevice9 *dev, IDirect3DSurface9 *bb) {
    IDirect3DSurface9 *rt = NULL, *sys = NULL, *src = bb; D3DSURFACE_DESC d; HRESULT hr;
    IDirect3DSurface9_GetDesc(bb, &d);
    if (d.MultiSampleType != D3DMULTISAMPLE_NONE) {
        hr = IDirect3DDevice9_CreateRenderTarget(dev, d.Width, d.Height, d.Format, D3DMULTISAMPLE_NONE, 0, FALSE, &rt, NULL);
        if (SUCCEEDED(hr) && SUCCEEDED(IDirect3DDevice9_StretchRect(dev, bb, NULL, rt, NULL, D3DTEXF_NONE))) src = rt;
    }
    hr = IDirect3DDevice9_CreateOffscreenPlainSurface(dev, d.Width, d.Height, d.Format, D3DPOOL_SYSTEMMEM, &sys, NULL);
    if (FAILED(hr)) { anp_log("d3dshot: CreateOffscreenPlainSurface %08lx", hr); goto out; }
    hr = IDirect3DDevice9_GetRenderTargetData(dev, src, sys);
    if (FAILED(hr)) { anp_log("d3dshot: GetRenderTargetData %08lx (fmt %d ms %d)", hr, d.Format, d.MultiSampleType); goto out; }
    D3DLOCKED_RECT lr;
    if (FAILED(IDirect3DSurface9_LockRect(sys, &lr, NULL, D3DLOCK_READONLY))) { anp_log("d3dshot: LockRect failed"); goto out; }
    if (d.Format == D3DFMT_X8R8G8B8 || d.Format == D3DFMT_A8R8G8B8) {
        int w = d.Width / 2, h = d.Height / 2, stride = (w * 3 + 3) & ~3;
        DWORD sz = stride * h; unsigned char *px = (unsigned char*)malloc(sz);
        if (px) {
            for (int y = 0; y < h; y++) {
                const unsigned char *s = (const unsigned char*)lr.pBits + (size_t)(2 * y) * lr.Pitch;
                unsigned char *o = px + (size_t)(h - 1 - y) * stride;
                for (int x = 0; x < w; x++) { o[3*x] = s[8*x]; o[3*x+1] = s[8*x+1]; o[3*x+2] = s[8*x+2]; }
            }
            char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\%s", g_dir, g_shotName);
            BITMAPINFOHEADER bi; memset(&bi, 0, sizeof bi);
            bi.biSize = sizeof bi; bi.biWidth = w; bi.biHeight = h; bi.biPlanes = 1; bi.biBitCount = 24;
            BITMAPFILEHEADER fh; memset(&fh, 0, sizeof fh);
            fh.bfType = 0x4d42; fh.bfOffBits = sizeof fh + sizeof bi; fh.bfSize = fh.bfOffBits + sz;
            FILE *f = fopen(fn, "wb");
            if (f) { fwrite(&fh, sizeof fh, 1, f); fwrite(&bi, sizeof bi, 1, f); fwrite(px, 1, sz, f); fclose(f); }
            free(px);
            anp_log("d3dshot: %ux%u fmt %d ms %d -> %s", d.Width, d.Height, d.Format, d.MultiSampleType, g_shotName);
        }
    } else anp_log("d3dshot: unsupported back buffer format %d", d.Format);
    IDirect3DSurface9_UnlockRect(sys);
out:
    if (sys) IDirect3DSurface9_Release(sys);
    if (rt) IDirect3DSurface9_Release(rt);
}
static HRESULT WINAPI hk_DevPresent(IDirect3DDevice9 *dev, const RECT *a, const RECT *b, HWND w, const RGNDATA *r) {
    InterlockedIncrement(&g_devPresents);
    if (g_shotReq && InterlockedExchange(&g_shotReq, 0)) {
        IDirect3DSurface9 *bb = NULL;
        if (SUCCEEDED(IDirect3DDevice9_GetBackBuffer(dev, 0, 0, D3DBACKBUFFER_TYPE_MONO, &bb))) { d3d_capture(dev, bb); IDirect3DSurface9_Release(bb); }
        else anp_log("d3dshot: GetBackBuffer failed");
    }
    return g_origDevPresent(dev, a, b, w, r);
}
static HRESULT WINAPI hk_ScPresent(IDirect3DSwapChain9 *sc, const RECT *a, const RECT *b, HWND w, const RGNDATA *r, DWORD fl) {
    InterlockedIncrement(&g_scPresents);
    if (g_shotReq && InterlockedExchange(&g_shotReq, 0)) {
        IDirect3DSurface9 *bb = NULL; IDirect3DDevice9 *dev = NULL;
        if (SUCCEEDED(IDirect3DSwapChain9_GetDevice(sc, &dev)) &&
            SUCCEEDED(IDirect3DSwapChain9_GetBackBuffer(sc, 0, D3DBACKBUFFER_TYPE_MONO, &bb))) { d3d_capture(dev, bb); }
        else anp_log("d3dshot: swapchain GetBackBuffer failed");
        if (bb) IDirect3DSurface9_Release(bb);
        if (dev) IDirect3DDevice9_Release(dev);
    }
    return g_origScPresent(sc, a, b, w, r, fl);
}
/* hot-patch: 5-byte jmp in the padding before fn, 2-byte short jmp over 'mov edi,edi'.
   If fn already starts with a jmp (another overlay's hook), retarget that jmp and chain to it. */
static int hook_fn(void *fn, void *hook, void **orig, const char *name) {
    unsigned char *p = (unsigned char*)fn; DWORD op;
    if (!readable(p - 5, 12)) { anp_log("hook %s: unreadable %p", name, p); return 0; }
    /* CEG: never hot-patch inside kl2.exe's image (hashed .text/.rdata); only d3d9 / overlay modules */
    if ((DWORD)p + 7 > 0x400000 && (DWORD)p - 5 < 0x1750000) { anp_log("hook %s: %p is inside kl2.exe, not patched (CEG)", name, p); return 0; }
    anp_log("hook %s at %p: %02x %02x %02x %02x %02x %02x | pre %02x %02x %02x %02x %02x", name, p,
            p[0], p[1], p[2], p[3], p[4], p[5], p[-5], p[-4], p[-3], p[-2], p[-1]);
    if (p[0] == 0x8B && p[1] == 0xFF) {
        for (int i = 1; i <= 5; i++) if (p[-i] != 0x90 && p[-i] != 0xCC) { anp_log("hook %s: no padding", name); return 0; }
        VirtualProtect(p - 5, 7, PAGE_EXECUTE_READWRITE, &op);
        p[-5] = 0xE9; *(DWORD*)(p - 4) = (DWORD)((unsigned char*)hook - p);
        *orig = p + 2;
        *(volatile WORD*)p = 0xF9EB;
        VirtualProtect(p - 5, 7, op, &op);
        FlushInstructionCache(GetCurrentProcess(), p - 5, 7);
        anp_log("hook %s: hot-patched", name); return 1;
    }
    if (p[0] == 0xE9) {
        unsigned char *tgt = p + 5 + *(LONG*)(p + 1);
        *orig = tgt;
        VirtualProtect(p, 5, PAGE_EXECUTE_READWRITE, &op);
        InterlockedExchange((LONG volatile*)(p + 1), (LONG)((unsigned char*)hook - (p + 5)));
        VirtualProtect(p, 5, op, &op);
        FlushInstructionCache(GetCurrentProcess(), p, 5);
        anp_log("hook %s: chained existing jmp -> %p", name, tgt); return 1;
    }
    anp_log("hook %s: unknown prologue, not hooked", name); return 0;
}
static void install_d3d_hooks(void) {
    char path[MAX_PATH]; GetSystemDirectoryA(path, sizeof path); strcat(path, "\\d3d9.dll");
    HMODULE m = LoadLibraryA(path);
    typedef IDirect3D9* (WINAPI *Create_t)(UINT);
    Create_t cr = m ? (Create_t)GetProcAddress(m, "Direct3DCreate9") : NULL;
    if (!cr) { anp_log("d3dhook: no Direct3DCreate9"); return; }
    IDirect3D9 *d3d = cr(D3D_SDK_VERSION);
    if (!d3d) { anp_log("d3dhook: Direct3DCreate9 failed"); return; }
    HWND hw = CreateWindowExA(0, "STATIC", "anp_d3d_probe", WS_POPUP, 0, 0, 8, 8, NULL, NULL, NULL, NULL);
    D3DPRESENT_PARAMETERS pp; memset(&pp, 0, sizeof pp);
    pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.BackBufferFormat = D3DFMT_UNKNOWN;
    pp.BackBufferWidth = 8; pp.BackBufferHeight = 8; pp.hDeviceWindow = hw;
    IDirect3DDevice9 *dev = NULL;
    HRESULT hr = IDirect3D9_CreateDevice(d3d, D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, hw,
                    D3DCREATE_SOFTWARE_VERTEXPROCESSING | D3DCREATE_MULTITHREADED, &pp, &dev);
    if (FAILED(hr)) { anp_log("d3dhook: dummy CreateDevice %08lx", hr); IDirect3D9_Release(d3d); DestroyWindow(hw); return; }
    void **vt = *(void***)dev;
    IDirect3DSwapChain9 *sc = NULL; void **svt = NULL;
    if (SUCCEEDED(IDirect3DDevice9_GetSwapChain(dev, 0, &sc))) svt = *(void***)sc;
    void *devPresent = vt[17], *scPresent = svt ? svt[3] : NULL;
    if (sc) IDirect3DSwapChain9_Release(sc);
    IDirect3DDevice9_Release(dev); IDirect3D9_Release(d3d); DestroyWindow(hw);
    hook_fn(devPresent, (void*)hk_DevPresent, (void**)&g_origDevPresent, "Device::Present");
    if (scPresent) hook_fn(scPresent, (void*)hk_ScPresent, (void**)&g_origScPresent, "SwapChain::Present");
}
