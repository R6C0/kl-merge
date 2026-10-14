/*
 * kltex.c - [Graphics] Textures: sharper textures at a slant (2026-10-14, the owner: 'textures they need to be upscaled or look
 * better find something for that and make it an option to have on or off'). Part of KLHook (included by klhook.c).
 *
 * WHY NOT AN UPSCALED TEXTURE PACK: kl2.exe build 0490 is a 32-bit program and cannot be made large-address-aware (the engine
 * keeps a tag in the top bit of pointers); the level archives already fill most of its 2 GB (dgVoodoo ran it out of address space
 * at a level load). Textures at 2x are 4x the memory. What costs no memory is how the textures are SAMPLED: the game asks for
 * plain linear (trilinear) filtering, which smears every floor, road and wall seen at an angle. This part turns that into
 * anisotropic filtering (Level x, default 16) and, optionally, a mip bias (Sharpen: a small negative bias picks the sharper mip).
 *
 * HOW: kl2.exe's import slot d3d9.dll!Direct3DCreate9 is wrapped (after ReShade, when a look loads it, so the wrapper sits in
 * front of whatever ReShade put there). The first IDirect3D9 it returns gets its CreateDevice (vtable slot 16) wrapped; the
 * first device made through it gets its SetSamplerState (slot 69) wrapped. The wrapper, for samplers 0..15 only:
 *   MINFILTER LINEAR      -> ANISOTROPIC, and MAXANISOTROPY Level is set on that sampler too
 *   MAXANISOTROPY n       -> max(n, Level)
 *   MIPMAPLODBIAS (game)  -> the game's bias + Sharpen (only when Sharpen is not 0; the bias is a float in a DWORD)
 * POINT filtering (HUD pictures, shadow maps, look-up tables) is never touched; nor are the vertex samplers (D3DDMAPSAMPLER and
 * 257..260). ReShade's own passes draw through its device, not through the slot the game calls, so they keep their filters.
 * Read once at start: a change needs a restart. Off (Textures=0): nothing is wrapped at all.
 *
 * Keys ([Graphics]): Textures=1 (0 = off; 1 steps aside when Neural=1 loads the Uplift add-on: 106 fps with both against 174 with the add-on
 * alone, measured 2026-10-14; 2 = on even then)   TextureLevel=16 (2..16)   TextureSharpen=0 (mip bias added, -1.0 .. 0; e.g. -0.3)
 */
#define KLTEX_C

#define KLTX_SAMP_MAGFILTER     5
#define KLTX_SAMP_MINFILTER     6
#define KLTX_SAMP_MIPFILTER     7
#define KLTX_SAMP_MIPMAPLODBIAS 8
#define KLTX_SAMP_MAXANISO      10
#define KLTX_TEXF_LINEAR        2
#define KLTX_TEXF_ANISOTROPIC   3

typedef void *(WINAPI *kltx_create9_fn)(UINT);
typedef HRESULT (WINAPI *kltx_createdev_fn)(void *self, UINT adapter, DWORD type, HWND focus, DWORD flags, void *pp, void **dev);
typedef HRESULT (WINAPI *kltx_setss_fn)(void *self, DWORD sampler, DWORD type, DWORD value);

static kltx_create9_fn   kltx_real_create9;
static kltx_createdev_fn kltx_real_createdev;
static kltx_setss_fn     kltx_real_setss;
static DWORD kltx_level = 16;
static float kltx_bias;
static volatile LONG kltx_calls, kltx_changed;

static HRESULT WINAPI kltx_setss(void *self, DWORD s, DWORD type, DWORD value)
{
    if (InterlockedIncrement(&kltx_calls) == 200000)
        klog("graphics: textures: 200000 sampler calls so far, %ld linear -> anisotropic x%lu", (long)kltx_changed, kltx_level);
    if (s < 16) {
        if (type == KLTX_SAMP_MINFILTER && value == KLTX_TEXF_LINEAR) {
            HRESULT r = kltx_real_setss(self, s, KLTX_SAMP_MINFILTER, KLTX_TEXF_ANISOTROPIC);
            kltx_real_setss(self, s, KLTX_SAMP_MAXANISO, kltx_level);
            InterlockedIncrement(&kltx_changed);
            return r;
        }
        if (type == KLTX_SAMP_MAXANISO && value < kltx_level) value = kltx_level;
        else if (type == KLTX_SAMP_MIPMAPLODBIAS && kltx_bias != 0.0f) { float f; memcpy(&f, &value, 4); f += kltx_bias; memcpy(&value, &f, 4); }
    }
    return kltx_real_setss(self, s, type, value);
}

static void kltx_wrap_slot(void *obj, int slot, void *mine, void **real, const char *what)
{
    void **vt = obj ? *(void ***)obj : 0, *cur;
    if (!vt) return;
    cur = vt[slot];
    if (cur == mine) return;                                         /* the same class twice: already wrapped */
    if (*real && *real != cur) { klog("graphics: textures: %s: a second class (%p, first %p) - left alone", what, cur, *real); return; }
    *real = cur;
    if (!klh_poke(&vt[slot], &cur, sizeof cur, &mine, sizeof mine, what)) { klog("graphics: textures: %s: vtable slot %d not changed", what, slot); *real = 0; return; }
    klog("graphics: textures: %s wrapped (vtable %p slot %d, was %p)", what, (void *)vt, slot, cur);
}

static HRESULT WINAPI kltx_createdev(void *self, UINT adapter, DWORD type, HWND focus, DWORD flags, void *pp, void **dev)
{
    HRESULT r = kltx_real_createdev(self, adapter, type, focus, flags, pp, dev);
    if (r >= 0 && dev && *dev) {
        kltx_wrap_slot(*dev, 69, (void *)kltx_setss, (void **)&kltx_real_setss, "SetSamplerState");
        klog("graphics: textures: device %p made (anisotropic x%lu, mip bias %+.2f)", *dev, kltx_level, kltx_bias);
    } else klog("graphics: textures: CreateDevice returned %08lx - nothing wrapped", (unsigned long)r);
    return r;
}

static void *WINAPI kltx_create9(UINT sdk)
{
    void *d3d = kltx_real_create9(sdk);
    if (d3d) kltx_wrap_slot(d3d, 16, (void *)kltx_createdev, (void **)&kltx_real_createdev, "CreateDevice");
    return d3d;
}

static void kltx_init(void)
{
    char b[32]; int lv, tx;
    tx = GetPrivateProfileIntA("Graphics", "Textures", 1, klh_ini);
    if (!tx) { klog("graphics: textures: off (the game's own filtering)"); return; }
    if (tx == 1 && GetPrivateProfileIntA("Graphics", "Neural", 0, klh_ini) && GetPrivateProfileIntA("Graphics", "Look", 1, klh_ini) &&
        GetPrivateProfileIntA("Graphics", "ReShade", 1, klh_ini)) {
        /* measured 2026-10-14 (menu route, 486 s, Look=1): Neural=1 + Textures 106 fps, Neural=1 alone 174, Textures alone 188 - with the
           Uplift add-on loaded every sampler change the game makes costs far more, so Textures=1 steps aside for it; Textures=2 forces it */
        klog("graphics: textures: off because Neural=1 (with the Uplift add-on the anisotropic filter costs about 40 %% of the frame rate; Textures=2 forces it)");
        return;
    }
    lv = GetPrivateProfileIntA("Graphics", "TextureLevel", 16, klh_ini);
    kltx_level = (DWORD)(lv < 2 ? 2 : lv > 16 ? 16 : lv);
    GetPrivateProfileStringA("Graphics", "TextureSharpen", "0", b, sizeof b, klh_ini);
    kltx_bias = (float)atof(b);
    if (kltx_bias < -1.0f) kltx_bias = -1.0f;
    if (kltx_bias > 0.0f) kltx_bias = 0.0f;
    if (!klh_iat("d3d9.dll", "Direct3DCreate9", (void *)kltx_create9, (void **)&kltx_real_create9))
        klog("graphics: textures: d3d9.dll!Direct3DCreate9 import not wrapped - textures as the game has them");
    else klog("graphics: textures: on (anisotropic x%lu, mip bias %+.2f); Direct3DCreate9 wrapped (was %p)", kltx_level, kltx_bias, (void *)kltx_real_create9);
}

