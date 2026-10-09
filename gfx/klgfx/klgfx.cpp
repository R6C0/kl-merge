/*
 * KLGfx - graphics proxy for Kane & Lynch 2: Dog Days (kl2.exe, 32-bit, Direct3D 9).
 *
 * Installed as d3d9.dll next to kl2.exe with KLGfx.ini. kl2.exe imports Direct3DCreate9 from d3d9.dll;
 * this DLL answers it and passes everything to Windows' own d3d9.dll. Nothing in kl2.exe is patched
 * (the Steam CEG integrity check hashes kl2.exe's code; see re/antitamper.md).
 *
 * KLGfx.ini [KLGfx] Mode=
 *   0  pass-through: Windows' d3d9 is used exactly as without this DLL (the default)
 *   1  wrap the device on native Direct3D 9: performance/memory lines, frame capture
 *   2  as 1, but the device runs on Direct3D 12 through Windows' D3D9On12 layer (a possible zero-copy route
 *      for the helper later, see gfx/README.md); mode 2 on its own only proves the game runs on it.
 *
 * [NR] Enable=1 (modes 1 and 2): each frame goes through klnr.exe, the 64-bit helper that runs OpenDLSS-NR's network
 * (gfx/klnr): GetRenderTargetData -> shared memory -> klnr.exe -> UpdateSurface, at Present for now. F9 switches
 * it on and off in game, F8 the split view. Without a model the frame only makes the round trip.
 *
 * Frame capture (modes 1 and 2): F10 in game, or CaptureAt=<seconds since the device was made,...>.
 * Writes <game>\KLGfx\frame_<n>\calls.txt (every render target switch, clear, copy, draw with its
 * shaders and states, shader constants with their names from the shaders' constant tables) and
 * rt_<seq>.png/.dds: each render target as it is left, plus the back buffer at Present.
 * gfx/tools/frame_report.py turns calls.txt into a pass list.
 *
 * Built by gfx/build_gfx.sh (MinGW) or gfx/build_gfx.bat (Visual Studio, x86).
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <initguid.h>   // defines the IIDs d3d9.h declares (this DLL must not link Windows' d3d9 import library)
#include <d3d9.h>
#include <stdio.h>
#include <ctype.h>
#include <stdint.h>
#include <string.h>
#include <string>
#include <vector>
#include <unordered_map>
#include "d3d9on12_decl.h"
#include "../klnr/klnr_client.h"

#define KLGFX_VERSION "0.2"

// ------------------------------------------------------------------------------------------ config
static char g_dir[MAX_PATH];
static int g_mode = 0;
static int g_stats_every = 10;
static std::vector<double> g_capture_at;
static int g_capture_key = VK_F10;
static int g_dump_targets = 1;
static int g_max_dumps = 80;
static int g_const_regs = 32;            // registers of a constant upload to print per call

static CRITICAL_SECTION g_cs;     // the log file
// The device is made with D3DCREATE_MULTITHREADED and the game uses it from more than one thread (it creates shaders
// and textures while another thread draws): everything this file keeps (the shader table, the capture) is under g_lock.
static CRITICAL_SECTION g_lock;
struct Locked {
    Locked() { EnterCriticalSection(&g_lock); }
    ~Locked() { LeaveCriticalSection(&g_lock); }
};

// [NR]: the neural rendering bridge
struct NrConfig {
    bool enable = false, split = false, test = false, temporal = true;
    int toggle_key = VK_F9, split_key = VK_F8;
    float intensity = 1.0f, local_tone = 1.0f, local_structure = 1.0f, skin_structure = -1.0f, paper_white = 1.0f,
          color_strength = 1.0f;
    int style = 0;
    KlnrClientConfig client;
};
static NrConfig g_nr;

static void klog(const char *fmt, ...)
{
    char path[MAX_PATH];
    snprintf(path, sizeof path, "%s\\KLGfx.log", g_dir);
    EnterCriticalSection(&g_cs);
    FILE *f = fopen(path, "a");
    if (f) {
        SYSTEMTIME t;
        GetLocalTime(&t);
        fprintf(f, "%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
        va_list a;
        va_start(a, fmt);
        vfprintf(f, fmt, a);
        va_end(a);
        fputc('\n', f);
        fclose(f);
    }
    LeaveCriticalSection(&g_cs);
}

static void read_ini()
{
    char ini[MAX_PATH], buf[512];
    snprintf(ini, sizeof ini, "%s\\KLGfx.ini", g_dir);
    g_mode = GetPrivateProfileIntA("KLGfx", "Mode", 0, ini);
    g_stats_every = GetPrivateProfileIntA("KLGfx", "StatsEvery", 10, ini);
    g_capture_key = GetPrivateProfileIntA("KLGfx", "CaptureKey", VK_F10, ini);
    g_dump_targets = GetPrivateProfileIntA("KLGfx", "CaptureDumpTargets", 1, ini);
    g_max_dumps = GetPrivateProfileIntA("KLGfx", "CaptureMaxDumps", 80, ini);
    g_const_regs = GetPrivateProfileIntA("KLGfx", "CaptureConstRegs", 32, ini);
    GetPrivateProfileStringA("KLGfx", "CaptureAt", "", buf, sizeof buf, ini);
    for (char *p = strtok(buf, ", "); p; p = strtok(NULL, ", "))
        g_capture_at.push_back(atof(p));

    auto f = [&](const char *key, float def) {
        char v[64], d[32];
        snprintf(d, sizeof d, "%g", def);
        GetPrivateProfileStringA("NR", key, d, v, sizeof v, ini);
        return (float)atof(v);
    };
    g_nr.enable = GetPrivateProfileIntA("NR", "Enable", 0, ini) != 0;
    g_nr.split = GetPrivateProfileIntA("NR", "Split", 0, ini) != 0;
    g_nr.test = GetPrivateProfileIntA("NR", "Test", 0, ini) != 0;
    g_nr.temporal = GetPrivateProfileIntA("NR", "Temporal", 1, ini) != 0;
    g_nr.toggle_key = GetPrivateProfileIntA("NR", "ToggleKey", VK_F9, ini);
    g_nr.split_key = GetPrivateProfileIntA("NR", "SplitKey", VK_F8, ini);
    g_nr.style = GetPrivateProfileIntA("NR", "Style", 0, ini);
    g_nr.intensity = f("Intensity", 1.0f);
    g_nr.local_tone = f("LocalTone", 1.0f);
    g_nr.local_structure = f("LocalStructure", 1.0f);
    g_nr.skin_structure = f("SkinStructure", -1.0f);
    g_nr.paper_white = f("PaperWhite", 1.0f);
    g_nr.color_strength = f("ColorStrength", 1.0f);
    g_nr.client.timeout_ms = GetPrivateProfileIntA("NR", "TimeoutMs", 100, ini);
    g_nr.client.max_misses = GetPrivateProfileIntA("NR", "MaxMisses", 30, ini);
    GetPrivateProfileStringA("NR", "Helper", "KLNR\\klnr.exe", buf, sizeof buf, ini);
    g_nr.client.helper = (buf[0] && buf[1] == ':') ? std::string(buf) : std::string(g_dir) + "\\" + buf;
    GetPrivateProfileStringA("NR", "Model", "", buf, sizeof buf, ini);
    g_nr.client.model = buf;
    if (g_nr.enable && g_mode <= 0)
        g_mode = 1;   // the bridge needs the wrapped device
}

// ------------------------------------------------------------------- Windows' own d3d9.dll exports
static HMODULE g_real;
typedef IDirect3D9 *(WINAPI *PFN_Create9)(UINT);
static PFN_Create9 p_Direct3DCreate9;

// Every other export is a jump stub, so arguments pass through untouched whatever their signature.
#define KLG_STUBS(X) X(Direct3DCreate9Ex) X(Direct3DCreate9On12) X(Direct3DCreate9On12Ex) \
    X(Direct3DShaderValidatorCreate9) X(D3DPERF_BeginEvent) X(D3DPERF_EndEvent) X(D3DPERF_GetStatus) \
    X(D3DPERF_QueryRepeatFrame) X(D3DPERF_SetMarker) X(D3DPERF_SetOptions) X(D3DPERF_SetRegion) \
    X(DebugSetLevel) X(DebugSetMute) X(Direct3D9EnableMaximizedWindowedModeShim) X(PSGPError) \
    X(PSGPSampleTexture)

extern "C" {
#define KLG_DECL(n) void *p_##n;
KLG_STUBS(KLG_DECL)
#undef KLG_DECL
void ensure_real();
}

static void *g_dummy_target;   // a missing export jumps here and returns 0 to the caller
static int __cdecl missing_export() { return 0; }

extern "C" void ensure_real()
{
    if (g_real)
        return;
    char p[MAX_PATH];
    GetSystemDirectoryA(p, MAX_PATH);   // a 32-bit process is redirected to SysWOW64
    strcat(p, "\\d3d9.dll");
    HMODULE m = LoadLibraryA(p);
    if (!m) {
        klog("cannot load %s (error %lu)", p, GetLastError());
        return;
    }
    p_Direct3DCreate9 = (PFN_Create9)GetProcAddress(m, "Direct3DCreate9");
    g_dummy_target = (void *)missing_export;
    std::string missing;
#define KLG_RESOLVE(n) p_##n = (void *)GetProcAddress(m, #n); if (!p_##n) { p_##n = g_dummy_target; missing += " " #n; }
    KLG_STUBS(KLG_RESOLVE)
#undef KLG_RESOLVE
    if (!missing.empty())
        klog("Windows' d3d9.dll lacks:%s (calls to those return 0)", missing.c_str());
    g_real = m;
}

#if defined(_MSC_VER)
#define KLG_STUB(n) extern "C" __declspec(naked) void stub_##n() { \
        __asm pushad __asm call ensure_real __asm popad __asm jmp dword ptr [p_##n] }
KLG_STUBS(KLG_STUB)
#else
#define KLG_STUB(n) __asm__(".globl _stub_" #n "\n_stub_" #n ":\n\tpushal\n\tcall _ensure_real\n\tpopal\n" \
                            "\tjmp *_p_" #n "\n");
KLG_STUBS(KLG_STUB)
#endif

// ------------------------------------------------------------------------------ small helpers
static const char *fmt_name(D3DFORMAT f)
{
    static char buf[8][16];
    static int k;
    switch ((DWORD)f) {
    case D3DFMT_UNKNOWN: return "UNKNOWN";
    case D3DFMT_A8R8G8B8: return "A8R8G8B8";
    case D3DFMT_X8R8G8B8: return "X8R8G8B8";
    case D3DFMT_R5G6B5: return "R5G6B5";
    case D3DFMT_A2R10G10B10: return "A2R10G10B10";
    case D3DFMT_A2B10G10R10: return "A2B10G10R10";
    case D3DFMT_A8B8G8R8: return "A8B8G8R8";
    case D3DFMT_A16B16G16R16: return "A16B16G16R16";
    case D3DFMT_A16B16G16R16F: return "A16B16G16R16F";
    case D3DFMT_A32B32G32R32F: return "A32B32G32R32F";
    case D3DFMT_R16F: return "R16F";
    case D3DFMT_G16R16F: return "G16R16F";
    case D3DFMT_R32F: return "R32F";
    case D3DFMT_G32R32F: return "G32R32F";
    case D3DFMT_G16R16: return "G16R16";
    case D3DFMT_A8: return "A8";
    case D3DFMT_L8: return "L8";
    case D3DFMT_A8L8: return "A8L8";
    case D3DFMT_L16: return "L16";
    case D3DFMT_D16: return "D16";
    case D3DFMT_D24S8: return "D24S8";
    case D3DFMT_D24X8: return "D24X8";
    case D3DFMT_D32: return "D32";
    case D3DFMT_D24FS8: return "D24FS8";
    case D3DFMT_D32F_LOCKABLE: return "D32F_LOCKABLE";
    }
    DWORD v = (DWORD)f;
    char *b = buf[k++ & 7];
    if (v > 0xffff && isprint(v & 0xff) && isprint((v >> 8) & 0xff))
        snprintf(b, 16, "'%c%c%c%c'", (char)(v & 0xff), (char)((v >> 8) & 0xff), (char)((v >> 16) & 0xff),
                 (char)(v >> 24));
    else
        snprintf(b, 16, "fmt%lu", v);
    return b;
}

static double now_s()
{
    static LARGE_INTEGER f;
    LARGE_INTEGER c;
    if (!f.QuadPart)
        QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    return (double)c.QuadPart / (double)f.QuadPart;
}

static uint32_t fnv1a(const void *p, size_t n)
{
    const uint8_t *b = (const uint8_t *)p;
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < n; i++)
        h = (h ^ b[i]) * 16777619u;
    return h;
}

// ------------------------------------------------------------------ shaders: hash + constant table
struct CtabConst {
    std::string name;
    int set;       // 0 bool, 1 int4, 2 float4, 3 sampler
    int index, count;
};
struct ShaderInfo {
    uint32_t hash = 0, id = 0, version = 0, dwords = 0;
    std::vector<CtabConst> consts;
};
static std::unordered_map<void *, ShaderInfo> g_shaders;   // real shader object -> info
static uint32_t g_next_shader_id = 1;

static ShaderInfo parse_shader(const DWORD *code)
{
    ShaderInfo s;
    if (!code)
        return s;
    s.version = code[0];
    size_t i = 1;
    for (; i < 1 << 20; i++) {
        DWORD t = code[i];
        if (t == 0x0000FFFF) { i++; break; }                    // end token
        if ((t & 0xFFFF) == 0xFFFE) {                            // comment block
            DWORD len = (t >> 16) & 0x7FFF;
            if (len >= 8 && code[i + 1] == 0x42415443) {         // 'CTAB'
                const uint8_t *base = (const uint8_t *)&code[i + 2];
                DWORD bytes = (len - 1) * 4;
                const DWORD *hdr = (const DWORD *)base;          // Size Creator Version Constants ConstantInfo
                DWORD n = hdr[3], off = hdr[4];
                for (DWORD c = 0; c < n && off + 20 * (c + 1) <= bytes; c++) {
                    const uint8_t *ci = base + off + 20 * c;
                    DWORD name_off = *(const DWORD *)ci;
                    CtabConst k;
                    k.set = *(const WORD *)(ci + 4);
                    k.index = *(const WORD *)(ci + 6);
                    k.count = *(const WORD *)(ci + 8);
                    if (name_off < bytes)
                        k.name.assign((const char *)base + name_off, strnlen((const char *)base + name_off, bytes - name_off));
                    s.consts.push_back(k);
                }
            }
            i += len;
            continue;
        }
    }
    s.dwords = (uint32_t)i;
    s.hash = fnv1a(code, i * 4);
    return s;
}

static std::string const_names(void *shader, UINT start, UINT count)
{
    Locked lock;
    std::string out;
    auto it = g_shaders.find(shader);
    if (it == g_shaders.end())
        return out;
    for (auto &c : it->second.consts) {
        if (c.set != 2)
            continue;
        if ((UINT)c.index < start + count && (UINT)(c.index + c.count) > start) {
            char b[160];
            snprintf(b, sizeof b, "%s%s@c%d+%d", out.empty() ? "" : " ", c.name.c_str(), c.index, c.count);
            out += b;
        }
    }
    return out;
}

// ------------------------------------------------------------------------- memory / perf lines
static void memory_line(char *out, size_t n)
{
    MEMORY_BASIC_INFORMATION mbi;
    size_t free_total = 0, free_max = 0;
    for (uint8_t *p = (uint8_t *)0x10000; (size_t)p < 0xFFFE0000u;) {
        if (!VirtualQuery(p, &mbi, sizeof mbi))
            break;
        if (mbi.State == MEM_FREE) {
            free_total += mbi.RegionSize;
            if (mbi.RegionSize > free_max)
                free_max = mbi.RegionSize;
        }
        uint8_t *next = (uint8_t *)mbi.BaseAddress + mbi.RegionSize;
        if (next <= p)
            break;
        p = next;
    }
    struct PMC {
        DWORD cb, PageFaultCount;
        SIZE_T Peak, Working, QPeakPaged, QPaged, QPeakNonPaged, QNonPaged, Pagefile, PeakPagefile, Private;
    } pmc = {};
    pmc.cb = sizeof pmc;
    typedef BOOL(WINAPI * GPMI)(HANDLE, void *, DWORD);
    static GPMI gpmi = (GPMI)GetProcAddress(GetModuleHandleA("kernel32.dll"), "K32GetProcessMemoryInfo");
    if (gpmi)
        gpmi(GetCurrentProcess(), &pmc, sizeof pmc);
    snprintf(out, n, "private %u MB, address space free %u MB (largest block %u MB)",
             (unsigned)(pmc.Private >> 20), (unsigned)(free_total >> 20), (unsigned)(free_max >> 20));
}

// ------------------------------------------------------------------------------- frame capture
typedef HRESULT(WINAPI *PFN_SaveSurface)(LPCSTR, DWORD, IDirect3DSurface9 *, const PALETTEENTRY *, const RECT *);

struct Capture {
    bool on = false;
    int frame = 0, seq = 0, dumps = 0;
    FILE *f = nullptr;
    char folder[MAX_PATH] = {};
    std::unordered_map<void *, int> ids;
    int next_id = 1;
    PFN_SaveSurface save = nullptr;
};
static Capture g_cap;
static int g_capture_count;

static void cap(const char *fmt, ...)
{
    if (!g_cap.on)
        return;
    Locked lock;
    if (!g_cap.on || !g_cap.f)
        return;
    fprintf(g_cap.f, "%d\t", g_cap.seq++);
    va_list a;
    va_start(a, fmt);
    vfprintf(g_cap.f, fmt, a);
    va_end(a);
    fputc('\n', g_cap.f);
}

static int surface_id(IDirect3DSurface9 *s);

static int texture_id(IDirect3DBaseTexture9 *t)
{
    if (!t)
        return 0;
    Locked lock;
    auto it = g_cap.ids.find(t);
    if (it != g_cap.ids.end())
        return it->second;
    int id = g_cap.next_id++;
    g_cap.ids[t] = id;
    D3DRESOURCETYPE ty = t->GetType();
    char d[160] = "?";
    if (ty == D3DRTYPE_TEXTURE) {
        D3DSURFACE_DESC sd;
        ((IDirect3DTexture9 *)t)->GetLevelDesc(0, &sd);
        snprintf(d, sizeof d, "tex %ux%u %s levels=%lu usage=%#lx pool=%d", sd.Width, sd.Height, fmt_name(sd.Format),
                 t->GetLevelCount(), sd.Usage, sd.Pool);
    } else if (ty == D3DRTYPE_CUBETEXTURE) {
        D3DSURFACE_DESC sd;
        ((IDirect3DCubeTexture9 *)t)->GetLevelDesc(0, &sd);
        snprintf(d, sizeof d, "cube %u %s levels=%lu usage=%#lx", sd.Width, fmt_name(sd.Format), t->GetLevelCount(), sd.Usage);
    } else if (ty == D3DRTYPE_VOLUMETEXTURE) {
        snprintf(d, sizeof d, "volume");
    }
    cap("R\t%d\t%s", id, d);
    return id;
}

static int surface_id(IDirect3DSurface9 *s)
{
    if (!s)
        return 0;
    Locked lock;
    auto it = g_cap.ids.find(s);
    if (it != g_cap.ids.end())
        return it->second;
    int id = g_cap.next_id++;
    g_cap.ids[s] = id;
    D3DSURFACE_DESC sd;
    s->GetDesc(&sd);
    IDirect3DTexture9 *tex = nullptr;
    int tid = 0;
    if (SUCCEEDED(s->GetContainer(IID_IDirect3DTexture9, (void **)&tex)) && tex) {
        tid = texture_id(tex);
        tex->Release();
    }
    cap("R\t%d\tsurf %ux%u %s usage=%#lx pool=%d msaa=%d%s%s", id, sd.Width, sd.Height, fmt_name(sd.Format), sd.Usage,
        sd.Pool, sd.MultiSampleType, tid ? " of tex " : "", tid ? std::to_string(tid).c_str() : "");
    return id;
}

static void dump_surface(IDirect3DSurface9 *s, const char *why)
{
    if (!g_cap.on || !g_dump_targets || !s || g_cap.dumps >= g_max_dumps)
        return;
    if (!g_cap.save) {
        HMODULE x = GetModuleHandleA("d3dx9_42.dll");
        if (!x)
            x = LoadLibraryA("d3dx9_42.dll");
        g_cap.save = x ? (PFN_SaveSurface)GetProcAddress(x, "D3DXSaveSurfaceToFileA") : nullptr;
        if (!g_cap.save)
            return;
    }
    D3DSURFACE_DESC sd;
    s->GetDesc(&sd);
    bool ldr = sd.Format == D3DFMT_A8R8G8B8 || sd.Format == D3DFMT_X8R8G8B8 || sd.Format == D3DFMT_A8B8G8R8 ||
               sd.Format == D3DFMT_R5G6B5;
    char path[MAX_PATH];
    snprintf(path, sizeof path, "%s\\rt_%05d_%d_%s.%s", g_cap.folder, g_cap.seq, surface_id(s), why, ldr ? "png" : "dds");
    HRESULT hr = g_cap.save(path, ldr ? 3 /*PNG*/ : 4 /*DDS*/, s, nullptr, nullptr);
    cap("DUMP\t%d\t%s\t%s", surface_id(s), SUCCEEDED(hr) ? "ok" : "failed", strrchr(path, '\\') + 1);
    g_cap.dumps++;
}

// ----------------------------------------------------------------------------------- the device
class KLDirect3D9;

class KLDevice9 : public IDirect3DDevice9 {
public:
    IDirect3DDevice9 *real;
    KLDirect3D9 *owner;
    D3DPRESENT_PARAMETERS pp;
    double t0, last_present = 0, stats_t0 = 0, ft_min = 1e9, ft_max = 0;
    unsigned frames = 0, stats_frames = 0;
    size_t next_capture = 0;
    bool key_down = false, want_capture = false;
    // state shadow (for draw lines and, later, for finding the DLSS insertion point)
    IDirect3DSurface9 *rt[4] = {};
    IDirect3DSurface9 *ds = nullptr;
    IDirect3DBaseTexture9 *tex[16] = {};
    void *vs = nullptr, *ps = nullptr;
    DWORD rs_zenable = 1, rs_zwrite = 1, rs_ablend = 0, rs_src = 2, rs_dst = 1, rs_cw = 15, rs_srgbw = 0;
    D3DVIEWPORT9 vp = {};
    unsigned draws_on_rt = 0;
    // neural rendering bridge (gfx/klnr)
    KlnrClient nr;
    bool nr_on = true, nr_tried = false, nr_said_off = false, nr_split = false, nr_reset_history = true;
    bool nr_direct_update = true, nr_toggle_down = false, nr_split_down = false;
    IDirect3DSurface9 *nr_sys = nullptr, *nr_gpu = nullptr;   // system-memory copy; video-memory fallback target
    UINT nr_w = 0, nr_h = 0;
    D3DFORMAT nr_fmt = D3DFMT_UNKNOWN;
    unsigned nr_frames = 0, nr_missed = 0;
    ULONG nr_refs = 0;               // the bridge's own surfaces (each holds a device reference)
    volatile LONG wrapper_refs = 1;  // references to this wrapper object (the game's and D3DX's)
    double nr_read_ms = 0, nr_wait_ms = 0, nr_write_ms = 0, nr_helper_ms = 0, nr_network_ms = 0;

    KLDevice9(IDirect3DDevice9 *r, KLDirect3D9 *o, const D3DPRESENT_PARAMETERS &p) : real(r), owner(o), pp(p)
    {
        t0 = stats_t0 = now_s();
        nr_split = g_nr.split;
        IDirect3DSurface9 *s = nullptr;
        if (SUCCEEDED(real->GetRenderTarget(0, &s)) && s) { rt[0] = s; s->Release(); }
        if (SUCCEEDED(real->GetDepthStencilSurface(&s)) && s) { ds = s; s->Release(); }
    }

#define KLG_WRAP_DEVICE
#include "d3d9_wrap.inl"
#undef KLG_WRAP_DEVICE

    // ---- IUnknown
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void **o) override
    {
        if (riid == IID_IUnknown || riid == IID_IDirect3DDevice9) {
            AddRef();
            *o = this;
            return S_OK;
        }
        return real->QueryInterface(riid, o);
    }
    // References are counted on the wrapper itself: when nobody holds it any more, the bridge's own surfaces go first
    // (each holds a device reference), then the game's last reference. The counts returned leave those surfaces out.
    ULONG STDMETHODCALLTYPE AddRef() override
    {
        InterlockedIncrement(&wrapper_refs);
        ULONG n = real->AddRef();
        return n > nr_refs ? n - nr_refs : n;
    }
    ULONG STDMETHODCALLTYPE Release() override
    {
        if (InterlockedDecrement(&wrapper_refs) == 0) {
            if (nr_gpu) nr_gpu->Release();
            if (nr_sys) nr_sys->Release();
            nr_sys = nr_gpu = nullptr;
            nr_refs = 0;
            nr.stop();
            ULONG n = real->Release();
            klog("device released after %u frames%s", frames, n ? " (resources of the game still hold it)" : "");
            delete this;
            return n;
        }
        ULONG n = real->Release();
        return n > nr_refs ? n - nr_refs : n;
    }
    void nr_release(IDirect3DSurface9 *&s)
    {
        if (s) {
            s->Release();
            s = nullptr;
            nr_refs--;
        }
    }

    HRESULT STDMETHODCALLTYPE GetDirect3D(IDirect3D9 **pp9) override;

    HRESULT STDMETHODCALLTYPE Reset(D3DPRESENT_PARAMETERS *p) override
    {
        nr_release(nr_gpu);   // D3DPOOL_DEFAULT: Reset fails while it exists (the system-memory copy may stay)
        nr_reset_history = true;
        HRESULT hr = real->Reset(p);
        klog("Reset %ux%u %s windowed=%d -> %#lx", p->BackBufferWidth, p->BackBufferHeight,
             fmt_name(p->BackBufferFormat), p->Windowed, hr);
        if (SUCCEEDED(hr)) {
            pp = *p;
            IDirect3DSurface9 *s = nullptr;
            memset(rt, 0, sizeof rt);
            if (SUCCEEDED(real->GetRenderTarget(0, &s)) && s) { rt[0] = s; s->Release(); }
            ds = nullptr;
            if (SUCCEEDED(real->GetDepthStencilSurface(&s)) && s) { ds = s; s->Release(); }
        }
        return hr;
    }

    // ---- frame boundary
    void begin_capture()
    {
        Locked lock;
        g_cap = Capture();
        g_cap.frame = ++g_capture_count;
        snprintf(g_cap.folder, MAX_PATH, "%s\\KLGfx", g_dir);
        CreateDirectoryA(g_cap.folder, nullptr);
        snprintf(g_cap.folder, MAX_PATH, "%s\\KLGfx\\frame_%d_%lu", g_dir, g_cap.frame, (unsigned long)GetTickCount());
        CreateDirectoryA(g_cap.folder, nullptr);
        char p[MAX_PATH];
        snprintf(p, sizeof p, "%s\\calls.txt", g_cap.folder);
        g_cap.f = fopen(p, "w");
        g_cap.on = g_cap.f != nullptr;
        cap("FRAME\t%u\t%.2f s after device creation\tbackbuffer %ux%u %s", frames, now_s() - t0,
            pp.BackBufferWidth, pp.BackBufferHeight, fmt_name(pp.BackBufferFormat));
        cap("STATE\trt0=%d\tds=%d", surface_id(rt[0]), surface_id(ds));
        klog("capture started: %s", g_cap.folder);
    }
    void end_capture()
    {
        Locked lock;
        IDirect3DSurface9 *bb = nullptr;
        if (SUCCEEDED(real->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &bb)) && bb) {
            dump_surface(bb, "present");
            bb->Release();
        }
        cap("END\t%d dumps", g_cap.dumps);
        fclose(g_cap.f);
        g_cap.f = nullptr;
        g_cap.on = false;
        klog("capture written (%d calls, %d images)", g_cap.seq, g_cap.dumps);
    }

    // ---- neural rendering bridge: the finished frame -> klnr.exe -> back, before it is shown
    bool key_edge(int key, bool &was_down)
    {
        bool down = key && (GetAsyncKeyState(key) & 0x8000) != 0;
        DWORD pid = 0;
        GetWindowThreadProcessId(GetForegroundWindow(), &pid);
        bool edge = down && !was_down && pid == GetCurrentProcessId();
        was_down = down;
        return edge;
    }
    void nr_off(const char *why)
    {
        if (!nr_said_off)
            klog("NR off for this session: %s", why);
        nr_said_off = true;
    }
    void nr_frame()
    {
        if (!g_nr.enable)
            return;
        if (key_edge(g_nr.toggle_key, nr_toggle_down)) {
            nr_on = !nr_on;
            nr_reset_history = true;
            klog("NR %s (key)", nr_on ? "on" : "off");
        }
        if (key_edge(g_nr.split_key, nr_split_down)) {
            nr_split = !nr_split;
            klog("NR split view %s (key)", nr_split ? "on" : "off");
        }
        if (!nr_on || nr_said_off)
            return;
        IDirect3DSurface9 *bb = nullptr;
        if (FAILED(real->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &bb)) || !bb)
            return;
        D3DSURFACE_DESC bd;
        bb->GetDesc(&bd);
        if (!nr_tried) {
            nr_tried = true;
            if (nr.start(g_nr.client, bd.Width, bd.Height))
                klog("NR: started %s (model '%s'), %ux%u", g_nr.client.helper.c_str(), g_nr.client.model.c_str(), bd.Width, bd.Height);
            else
                nr_off(nr.error().c_str());
        }
        if (!nr.ready()) {
            if (nr.given_up())
                nr_off(nr.error().c_str());
            bb->Release();
            return;
        }
        if (bd.Format != D3DFMT_A8R8G8B8 && bd.Format != D3DFMT_X8R8G8B8) {
            nr_off("the back buffer is not A8R8G8B8 / X8R8G8B8");
            bb->Release();
            return;
        }
        if (bd.MultiSampleType != D3DMULTISAMPLE_NONE) {
            nr_off("the back buffer is multisampled");
            bb->Release();
            return;
        }
        if (!nr_sys || nr_w != bd.Width || nr_h != bd.Height || nr_fmt != bd.Format) {
            nr_release(nr_sys);
            nr_release(nr_gpu);
            HRESULT hr = real->CreateOffscreenPlainSurface(bd.Width, bd.Height, bd.Format, D3DPOOL_SYSTEMMEM, &nr_sys, nullptr);
            if (SUCCEEDED(hr))
                nr_refs++;
            if (FAILED(hr)) {
                klog("NR: system-memory surface %ux%u failed (%#lx)", bd.Width, bd.Height, hr);
                nr_off("no system-memory surface");
                bb->Release();
                return;
            }
            nr_w = bd.Width;
            nr_h = bd.Height;
            nr_fmt = bd.Format;
            nr_reset_history = true;
        }
        double ta = now_s();
        HRESULT hr = real->GetRenderTargetData(bb, nr_sys);
        D3DLOCKED_RECT lr;
        uint8_t *buf = nullptr;
        if (SUCCEEDED(hr) && SUCCEEDED(nr_sys->LockRect(&lr, nullptr, D3DLOCK_READONLY))) {
            buf = nr.frame(nr_w, nr_h, (uint32_t)lr.Pitch);
            if (buf)
                memcpy(buf, lr.pBits, (size_t)lr.Pitch * nr_h);
            nr_sys->UnlockRect();
        } else if (FAILED(hr)) {
            klog("NR: GetRenderTargetData failed (%#lx)", hr);
            nr_off("cannot read the back buffer");
        }
        if (!buf) {
            bb->Release();
            return;
        }
        double tb = now_s();
        KlnrParams p;
        p.flags = KLNR_F_ENABLED | (g_nr.temporal ? KLNR_F_TEMPORAL : 0) | (nr_reset_history ? KLNR_F_RESET_HISTORY : 0) |
                  (nr_split ? KLNR_F_SPLIT : 0) | (g_nr.test ? KLNR_F_TEST : 0);
        p.intensity = g_nr.intensity;
        p.local_tone = g_nr.local_tone;
        p.local_structure = g_nr.local_structure;
        p.skin_structure = g_nr.skin_structure;
        p.paper_white = g_nr.paper_white;
        p.color_strength = g_nr.color_strength;
        p.style = g_nr.style;
        bool ok = nr.process(p);
        double tc = now_s();
        if (ok) {
            nr_reset_history = false;
            if (SUCCEEDED(nr_sys->LockRect(&lr, nullptr, 0))) {
                memcpy(lr.pBits, buf, (size_t)lr.Pitch * nr_h);
                nr_sys->UnlockRect();
            }
            if (nr_direct_update) {
                hr = real->UpdateSurface(nr_sys, nullptr, bb, nullptr);
                if (FAILED(hr)) {
                    klog("NR: UpdateSurface into the back buffer failed (%#lx): through a video-memory surface from now on", hr);
                    nr_direct_update = false;
                }
            }
            if (!nr_direct_update) {
                if (!nr_gpu && SUCCEEDED(real->CreateOffscreenPlainSurface(nr_w, nr_h, nr_fmt, D3DPOOL_DEFAULT, &nr_gpu, nullptr)))
                    nr_refs++;
                if (!nr_gpu || FAILED(real->UpdateSurface(nr_sys, nullptr, nr_gpu, nullptr)) ||
                    FAILED(real->StretchRect(nr_gpu, nullptr, bb, nullptr, D3DTEXF_NONE)))
                    nr_off("cannot write the result back");
            }
            nr_frames++;
            nr_helper_ms += nr.control()->ms_total;
            nr_network_ms += nr.control()->ms_network;
        } else {
            nr_missed++;
            if (nr.given_up())
                nr_off(nr.error().c_str());
        }
        double td = now_s();
        nr_read_ms += (tb - ta) * 1000;
        nr_wait_ms += (tc - tb) * 1000;
        nr_write_ms += (td - tc) * 1000;
        bb->Release();
    }

    HRESULT STDMETHODCALLTYPE Present(const RECT *a, const RECT *b, HWND w, const RGNDATA *d) override
    {
        nr_frame();
        if (g_cap.on) {
            cap("PRESENT");
            end_capture();
        }
        HRESULT hr = real->Present(a, b, w, d);
        double t = now_s();
        if (last_present > 0) {
            double ft = t - last_present;
            if (ft < ft_min) ft_min = ft;
            if (ft > ft_max) ft_max = ft;
        }
        last_present = t;
        frames++;
        stats_frames++;
        if (g_stats_every > 0 && t - stats_t0 >= g_stats_every) {
            char mem[160];
            memory_line(mem, sizeof mem);
            klog("frames %u: %.1f fps, frame time %.2f-%.2f ms; %s", frames, stats_frames / (t - stats_t0),
                 ft_min * 1000, ft_max * 1000, mem);
            if (nr_frames || nr_missed) {
                double n = nr_frames ? nr_frames : 1;
                klog("NR: %u frames through klnr, %u without a result; per frame: read %.2f ms, wait %.2f ms (klnr %.2f, "
                     "network %.2f), write %.2f ms", nr_frames, nr_missed, nr_read_ms / n, nr_wait_ms / n, nr_helper_ms / n,
                     nr_network_ms / n, nr_write_ms / n);
                nr_frames = nr_missed = 0;
                nr_read_ms = nr_wait_ms = nr_write_ms = nr_helper_ms = nr_network_ms = 0;
            }
            stats_t0 = t;
            stats_frames = 0;
            ft_min = 1e9;
            ft_max = 0;
        }
        // capture triggers: the key (only while the game has the focus) and the CaptureAt list
        bool down = (GetAsyncKeyState(g_capture_key) & 0x8000) != 0;
        DWORD pid = 0;
        GetWindowThreadProcessId(GetForegroundWindow(), &pid);
        if (down && !key_down && pid == GetCurrentProcessId())
            want_capture = true;
        key_down = down;
        if (next_capture < g_capture_at.size() && t - t0 >= g_capture_at[next_capture]) {
            next_capture++;
            want_capture = true;
        }
        if (want_capture) {
            want_capture = false;
            begin_capture();
        }
        return hr;
    }
    HRESULT STDMETHODCALLTYPE BeginScene() override { cap("BEGINSCENE"); return real->BeginScene(); }
    HRESULT STDMETHODCALLTYPE EndScene() override { cap("ENDSCENE"); return real->EndScene(); }

    // ---- targets and copies
    HRESULT STDMETHODCALLTYPE SetRenderTarget(DWORD i, IDirect3DSurface9 *s) override
    {
        if (g_cap.on) {
            if (i == 0 && rt[0] && rt[0] != s && draws_on_rt)
                dump_surface(rt[0], "left");
            cap("RT\t%lu\t%d", i, surface_id(s));
        }
        if (i == 0)
            draws_on_rt = 0;
        HRESULT hr = real->SetRenderTarget(i, s);
        if (SUCCEEDED(hr) && i < 4) {
            rt[i] = s;
            if (i == 0) {                     // D3D9 resets the viewport to the whole new target
                D3DSURFACE_DESC sd;
                if (s && SUCCEEDED(s->GetDesc(&sd))) {
                    vp.X = vp.Y = 0;
                    vp.Width = sd.Width;
                    vp.Height = sd.Height;
                    vp.MinZ = 0;
                    vp.MaxZ = 1;
                }
            }
        }
        return hr;
    }
    HRESULT STDMETHODCALLTYPE SetDepthStencilSurface(IDirect3DSurface9 *s) override
    {
        cap("DS\t%d", g_cap.on ? surface_id(s) : 0);
        ds = s;
        return real->SetDepthStencilSurface(s);
    }
    HRESULT STDMETHODCALLTYPE Clear(DWORD n, const D3DRECT *r, DWORD flags, D3DCOLOR c, float z, DWORD st) override
    {
        cap("CLEAR\tflags=%#lx\tcolor=%08lx\tz=%g\tstencil=%lu\trects=%lu\trt0=%d\tds=%d", flags, c, z, st, n,
            g_cap.on ? surface_id(rt[0]) : 0, g_cap.on ? surface_id(ds) : 0);
        return real->Clear(n, r, flags, c, z, st);
    }
    HRESULT STDMETHODCALLTYPE StretchRect(IDirect3DSurface9 *s, const RECT *sr, IDirect3DSurface9 *d,
                                          const RECT *dr, D3DTEXTUREFILTERTYPE f) override
    {
        if (g_cap.on)
            cap("STRETCH\t%d\t%d\tfilter=%d\tsrc=%s\tdst=%s", surface_id(s), surface_id(d), f,
                sr ? (std::to_string(sr->right - sr->left) + "x" + std::to_string(sr->bottom - sr->top)).c_str() : "all",
                dr ? (std::to_string(dr->right - dr->left) + "x" + std::to_string(dr->bottom - dr->top)).c_str() : "all");
        return real->StretchRect(s, sr, d, dr, f);
    }
    HRESULT STDMETHODCALLTYPE ColorFill(IDirect3DSurface9 *s, const RECT *r, D3DCOLOR c) override
    {
        cap("FILL\t%d\t%08lx", g_cap.on ? surface_id(s) : 0, c);
        return real->ColorFill(s, r, c);
    }
    HRESULT STDMETHODCALLTYPE UpdateSurface(IDirect3DSurface9 *s, const RECT *r, IDirect3DSurface9 *d, const POINT *p) override
    {
        if (g_cap.on) cap("UPDATESURF\t%d\t%d", surface_id(s), surface_id(d));
        return real->UpdateSurface(s, r, d, p);
    }
    HRESULT STDMETHODCALLTYPE UpdateTexture(IDirect3DBaseTexture9 *s, IDirect3DBaseTexture9 *d) override
    {
        if (g_cap.on) cap("UPDATETEX\t%d\t%d", texture_id(s), texture_id(d));
        return real->UpdateTexture(s, d);
    }
    HRESULT STDMETHODCALLTYPE GetRenderTargetData(IDirect3DSurface9 *s, IDirect3DSurface9 *d) override
    {
        if (g_cap.on) cap("READBACK\t%d\t%d", surface_id(s), surface_id(d));
        return real->GetRenderTargetData(s, d);
    }
    HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT9 *v) override
    {
        if (v) vp = *v;
        if (v) cap("VIEWPORT\t%lu,%lu %lux%lu z=%g..%g", v->X, v->Y, v->Width, v->Height, v->MinZ, v->MaxZ);
        return real->SetViewport(v);
    }

    // ---- states and resources
    HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE s, DWORD v) override
    {
        switch (s) {
        case D3DRS_ZENABLE: rs_zenable = v; break;
        case D3DRS_ZWRITEENABLE: rs_zwrite = v; break;
        case D3DRS_ALPHABLENDENABLE: rs_ablend = v; break;
        case D3DRS_SRCBLEND: rs_src = v; break;
        case D3DRS_DESTBLEND: rs_dst = v; break;
        case D3DRS_COLORWRITEENABLE: rs_cw = v; break;
        case D3DRS_SRGBWRITEENABLE: rs_srgbw = v; break;
        default: break;
        }
        return real->SetRenderState(s, v);
    }
    HRESULT STDMETHODCALLTYPE SetTexture(DWORD st, IDirect3DBaseTexture9 *t) override
    {
        if (st < 16)
            tex[st] = t;
        return real->SetTexture(st, t);
    }
    HRESULT STDMETHODCALLTYPE CreateTexture(UINT w, UINT h, UINT l, DWORD u, D3DFORMAT f, D3DPOOL p,
                                            IDirect3DTexture9 **t, HANDLE *sh) override
    {
        HRESULT hr = real->CreateTexture(w, h, l, u, f, p, t, sh);
        if (u & (D3DUSAGE_RENDERTARGET | D3DUSAGE_DEPTHSTENCIL))
            klog("CreateTexture %ux%u %s levels=%u usage=%#lx -> %#lx", w, h, fmt_name(f), l, u, hr);
        if (g_cap.on) cap("NEWTEX\t%ux%u\t%s\tusage=%#lx\tpool=%d", w, h, fmt_name(f), u, p);
        return hr;
    }
    HRESULT STDMETHODCALLTYPE CreateRenderTarget(UINT w, UINT h, D3DFORMAT f, D3DMULTISAMPLE_TYPE m, DWORD q, BOOL l,
                                                 IDirect3DSurface9 **s, HANDLE *sh) override
    {
        HRESULT hr = real->CreateRenderTarget(w, h, f, m, q, l, s, sh);
        klog("CreateRenderTarget %ux%u %s msaa=%d -> %#lx", w, h, fmt_name(f), m, hr);
        return hr;
    }
    HRESULT STDMETHODCALLTYPE CreateDepthStencilSurface(UINT w, UINT h, D3DFORMAT f, D3DMULTISAMPLE_TYPE m, DWORD q,
                                                        BOOL d, IDirect3DSurface9 **s, HANDLE *sh) override
    {
        HRESULT hr = real->CreateDepthStencilSurface(w, h, f, m, q, d, s, sh);
        klog("CreateDepthStencilSurface %ux%u %s msaa=%d -> %#lx", w, h, fmt_name(f), m, hr);
        return hr;
    }

    // ---- shaders and constants
    HRESULT STDMETHODCALLTYPE CreateVertexShader(const DWORD *code, IDirect3DVertexShader9 **s) override
    {
        HRESULT hr = real->CreateVertexShader(code, s);
        if (SUCCEEDED(hr) && s && *s) {
            ShaderInfo si = parse_shader(code);
            Locked lock;
            si.id = g_next_shader_id++;
            g_shaders[*s] = si;
        }
        return hr;
    }
    HRESULT STDMETHODCALLTYPE CreatePixelShader(const DWORD *code, IDirect3DPixelShader9 **s) override
    {
        HRESULT hr = real->CreatePixelShader(code, s);
        if (SUCCEEDED(hr) && s && *s) {
            ShaderInfo si = parse_shader(code);
            Locked lock;
            si.id = g_next_shader_id++;
            g_shaders[*s] = si;
        }
        return hr;
    }
    void describe_shader(void *s, const char *kind)
    {
        if (!g_cap.on || !s)
            return;
        Locked lock;
        if (!g_cap.on || g_cap.ids.count(s))
            return;
        g_cap.ids[s] = 0;
        auto it = g_shaders.find(s);
        if (it == g_shaders.end()) {
            cap("SHADER\t%s\t?", kind);
            return;
        }
        std::string names;
        for (auto &c : it->second.consts) {
            char b[160];
            snprintf(b, sizeof b, " %s:%c%d+%d", c.name.c_str(), "bifs"[c.set & 3], c.index, c.count);
            names += b;
        }
        cap("SHADER\t%s\t%u\thash=%08x\tver=%08lx\tdwords=%u\tconsts:%s", kind, it->second.id, it->second.hash,
            it->second.version, it->second.dwords, names.c_str());
    }
    static unsigned shader_id(void *s)
    {
        Locked lock;
        auto it = g_shaders.find(s);
        return it == g_shaders.end() ? 0 : it->second.id;
    }
    HRESULT STDMETHODCALLTYPE SetVertexShader(IDirect3DVertexShader9 *s) override
    {
        vs = s;
        describe_shader(s, "vs");
        return real->SetVertexShader(s);
    }
    HRESULT STDMETHODCALLTYPE SetPixelShader(IDirect3DPixelShader9 *s) override
    {
        ps = s;
        describe_shader(s, "ps");
        return real->SetPixelShader(s);
    }
    void log_consts(const char *kind, void *shader, UINT r, const float *d, UINT n)
    {
        if (!g_cap.on || !d)
            return;
        Locked lock;
        std::string v;
        UINT shown = n < (UINT)g_const_regs ? n : (UINT)g_const_regs;
        for (UINT i = 0; i < shown; i++) {
            char b[96];
            snprintf(b, sizeof b, "%s%.6g,%.6g,%.6g,%.6g", i ? " | " : "", d[4 * i], d[4 * i + 1], d[4 * i + 2], d[4 * i + 3]);
            v += b;
        }
        cap("%s\tc%u+%u\tshader=%u\t[%s]\t%s", kind, r, n, shader_id(shader), const_names(shader, r, n).c_str(), v.c_str());
    }
    HRESULT STDMETHODCALLTYPE SetVertexShaderConstantF(UINT r, const float *d, UINT n) override
    {
        log_consts("VSC", vs, r, d, n);
        return real->SetVertexShaderConstantF(r, d, n);
    }
    HRESULT STDMETHODCALLTYPE SetPixelShaderConstantF(UINT r, const float *d, UINT n) override
    {
        log_consts("PSC", ps, r, d, n);
        return real->SetPixelShaderConstantF(r, d, n);
    }

    // ---- draws
    void log_draw(const char *kind, D3DPRIMITIVETYPE t, UINT count)
    {
        draws_on_rt++;
        if (!g_cap.on)
            return;
        Locked lock;
        std::string texs;
        for (int s = 0; s < 16; s++)
            if (tex[s]) {
                char b[24];
                snprintf(b, sizeof b, "%s%d:%d", texs.empty() ? "" : ",", s, texture_id(tex[s]));
                texs += b;
            }
        cap("%s\tprim=%d\tcount=%u\trt=%d,%d,%d,%d\tds=%d\tvs=%u\tps=%u\tz=%lu/%lu\tblend=%lu:%lu/%lu\tcw=%#lx\tsrgbw=%lu"
            "\tvp=%lu,%lu,%lux%lu\ttex=%s",
            kind, t, count, surface_id(rt[0]), surface_id(rt[1]), surface_id(rt[2]), surface_id(rt[3]), surface_id(ds),
            shader_id(vs), shader_id(ps), rs_zenable, rs_zwrite, rs_ablend, rs_src, rs_dst, rs_cw, rs_srgbw, vp.X, vp.Y,
            vp.Width, vp.Height, texs.c_str());
    }
    HRESULT STDMETHODCALLTYPE DrawPrimitive(D3DPRIMITIVETYPE t, UINT sv, UINT n) override
    {
        log_draw("DRAW", t, n);
        return real->DrawPrimitive(t, sv, n);
    }
    HRESULT STDMETHODCALLTYPE DrawIndexedPrimitive(D3DPRIMITIVETYPE t, INT bv, UINT mi, UINT nv, UINT si, UINT n) override
    {
        log_draw("DRAWI", t, n);
        return real->DrawIndexedPrimitive(t, bv, mi, nv, si, n);
    }
    HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE t, UINT n, const void *d, UINT st) override
    {
        log_draw("DRAWUP", t, n);
        return real->DrawPrimitiveUP(t, n, d, st);
    }
    HRESULT STDMETHODCALLTYPE DrawIndexedPrimitiveUP(D3DPRIMITIVETYPE t, UINT mi, UINT nv, UINT n, const void *id,
                                                     D3DFORMAT f, const void *d, UINT st) override
    {
        log_draw("DRAWIUP", t, n);
        return real->DrawIndexedPrimitiveUP(t, mi, nv, n, id, f, d, st);
    }
};

// --------------------------------------------------------------------------------- IDirect3D9
class KLDirect3D9 : public IDirect3D9 {
public:
    IDirect3D9 *real;
    bool on12;
    KLDirect3D9(IDirect3D9 *r, bool o) : real(r), on12(o) {}

#define KLG_WRAP_D3D9
#include "d3d9_wrap.inl"
#undef KLG_WRAP_D3D9

    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void **o) override
    {
        if (riid == IID_IUnknown || riid == IID_IDirect3D9) {
            AddRef();
            *o = this;
            return S_OK;
        }
        return real->QueryInterface(riid, o);
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return real->AddRef(); }
    ULONG STDMETHODCALLTYPE Release() override
    {
        ULONG n = real->Release();
        if (n == 0)
            delete this;
        return n;
    }
    HRESULT STDMETHODCALLTYPE CreateDevice(UINT ad, D3DDEVTYPE ty, HWND w, DWORD fl, D3DPRESENT_PARAMETERS *p,
                                           IDirect3DDevice9 **out) override
    {
        D3DADAPTER_IDENTIFIER9 id = {};
        real->GetAdapterIdentifier(ad, 0, &id);
        klog("CreateDevice adapter %u '%s' driver %u.%u.%u.%u, flags %#lx, %ux%u %s windowed=%d msaa=%d swap=%d "
             "interval=%#x refresh=%u, depth %s auto=%d",
             ad, id.Description, HIWORD(id.DriverVersion.HighPart), LOWORD(id.DriverVersion.HighPart),
             HIWORD(id.DriverVersion.LowPart), LOWORD(id.DriverVersion.LowPart), fl, p->BackBufferWidth,
             p->BackBufferHeight, fmt_name(p->BackBufferFormat), p->Windowed, p->MultiSampleType, p->SwapEffect,
             p->PresentationInterval, p->FullScreen_RefreshRateInHz, fmt_name(p->AutoDepthStencilFormat),
             p->EnableAutoDepthStencil);
        IDirect3DDevice9 *dev = nullptr;
        HRESULT hr = real->CreateDevice(ad, ty, w, fl, p, &dev);
        klog("CreateDevice -> %#lx%s", hr, on12 ? " (on Direct3D 12)" : "");
        if (FAILED(hr) || !dev) {
            *out = dev;
            return hr;
        }
        if (on12) {
            KLG_IDirect3DDevice9On12 *d12 = nullptr;
            if (SUCCEEDED(dev->QueryInterface(KLG_IID_IDirect3DDevice9On12, (void **)&d12)) && d12) {
                klog("IDirect3DDevice9On12 available: Direct3D 12 resources can be shared with the DLSS helper");
                d12->Release();
            } else {
                klog("device does not expose IDirect3DDevice9On12");
            }
        }
        *out = new KLDevice9(dev, this, *p);
        return hr;
    }
};

HRESULT STDMETHODCALLTYPE KLDevice9::GetDirect3D(IDirect3D9 **pp9)
{
    if (!pp9)
        return D3DERR_INVALIDCALL;
    owner->AddRef();
    *pp9 = owner;
    return S_OK;
}

// ------------------------------------------------------------------------------ the entry point
extern "C" IDirect3D9 *WINAPI Direct3DCreate9(UINT sdk)
{
    ensure_real();
    if (!p_Direct3DCreate9)
        return nullptr;
    static bool said;
    if (!said) {
        said = true;
        klog("==== KLGfx %s, mode %d (0 pass-through, 1 wrap, 2 wrap on Direct3D 12)%s", KLGFX_VERSION, g_mode,
             g_nr.enable ? ", NR bridge on" : "");
    }
    if (g_mode <= 0)
        return p_Direct3DCreate9(sdk);
    IDirect3D9 *d = nullptr;
    bool on12 = false;
    if (g_mode >= 2) {
        PFN_KLG_Direct3DCreate9On12 f = (PFN_KLG_Direct3DCreate9On12)p_Direct3DCreate9On12;
        if (f && f != (void *)g_dummy_target) {
            KLG_D3D9ON12_ARGS args = {};
            args.Enable9On12 = TRUE;
            d = f(sdk, &args, 1);
            on12 = d != nullptr;
            klog("Direct3DCreate9On12 -> %p", (void *)d);
        } else {
            klog("this Windows' d3d9.dll has no Direct3DCreate9On12: using native Direct3D 9");
        }
    }
    if (!d)
        d = p_Direct3DCreate9(sdk);
    return d ? new KLDirect3D9(d, on12) : nullptr;
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(inst);
        InitializeCriticalSection(&g_cs);
        InitializeCriticalSection(&g_lock);
        GetModuleFileNameA(inst, g_dir, MAX_PATH);
        char *s = strrchr(g_dir, '\\');
        if (s)
            *s = 0;
        read_ini();
    }
    return TRUE;
}
