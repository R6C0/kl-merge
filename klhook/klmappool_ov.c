/*
 * klmappool_ov.c - [MapPool] Overlay: the LIVE map pool drawn over the online lobby (2026-10-27, mappool_ov_1027; owner: 'random maps with the icons
 * showing what maps in the pool e.g. full dead men, full dog days, mix'). Part of KLHook (included by klhook.c right AFTER klmappool.c). SHIP and TEST.
 * NOT run live. READ-ONLY towards the game: no .text / .rdata patch, no vtable write of its own. It reads kmp.* (klmappool.c), the session state, and
 * draws with the game's own IDirect3DDevice9 from klfps.c's Present wrapper (a wrapper that already exists; klfps.c only gained 3 lines: the device
 * pointer and a call, see below).
 *
 * WHAT IT SHOWS (a panel, lobby / map-select screen only): the pool label (FULL DEAD MEN / FULL DOG DAYS / MIX), 'played/total' on the right, and
 *   a grid of small thumbnails of EVERY map in the pool in the order the pool will be played (the seeded permutation, klmappool.c): the NEXT map
 *   has a gold frame and a NEXT badge, maps already played in this cycle are dimmed, the rest are normal. When every map is played the cycle is spent:
 *   nothing is dimmed (the next load starts a new order). Host and client alike: kmp.pool / kmp.seed are the host's on a client (klhostopt.c).
 *
 * WHY NOT THE HUD PATH: klhud*.c draws through the HUD clock element's pictures (klu_pic) which only exist from session state 0x19 on and can only show
 *   the game's own sprite handles; the lobby is a menu scene. The shop page II (klshoppage.c) swaps the game's own picture rows (data writes), which
 *   cannot show a list of N foreign thumbnails. So this draws with plain Direct3D 9 at the end of the frame (the way an overlay such as RTSS does).
 *
 * HOW (all D3D9 vtable indices are the public d3d9.h order, not read from the exe):
 *   - klfps.c's Present wrappers (device slot 17 and swap chain slot 3, depth 0 only, i.e. not the Steam overlay's nested call) call klmpo_present(dev)
 *     right before the real Present. Needs [FrameLimit] Enable=1 (default), whose CreateDevice wrapper hands the device over (klmpo_dev).
 *   - DRAW: ONE state block (CreateStateBlock D3DSBT_ALL) is captured every frame the overlay is up and applied after, the render target is saved and
 *     put back; the quads are screen-space (FVF XYZRHW|DIFFUSE|TEX1, DrawPrimitiveUP, fixed function: vertex/pixel shader NULL). Textures are D3DPOOL_MANAGED
 *     (survive Reset; a new device drops them). The whole draw is inside __try: an exception disables the overlay for the session (logged).
 *   - GATE + DATA: kmpo_snap() runs on the GAME thread from klho_tick (klhostopt.c, host and client), at most every 100 ms: it reads the session
 *     state (sm = [0x168e598], +0x70) and, when it is in [MapPool] OverlayStates (bit mask, default 0x2000 = state 0xd, the lobby, GUESS: 0xd is the
 *     screen the host's Apply step and klhostopt.c's 'lobby' notion use; the log prints every state change while a pool is on, so the right bit can be set
 *     in the ini without a rebuild), copies kmp's permutation + used marks into a double buffer the render thread reads.
 *   - IMAGES: <OverlayDir>\<map>.kmi, written by tools/kl_mappool.py (build or 'thumbs') into <work>\build\mappool_1027\overlay: 'KMI1', u32 w, u32 h,
 *     w*h*4 bytes B,G,R,A, at most 512 x 512. A missing / bad file = a dark card with the map's name (text only); names are drawn with GDI into a
 *     texture (gdi32 looked up at run time: not on the link line).
 *
 * GUESSES (not verified in the game): the lobby is session state 0xd; the lobby's draw order leaves the frame in a state where BeginScene works and the
 *   render target is the back buffer at Present (if BeginScene fails nothing is drawn, the state is restored anyway); panel position (default 2 % / 74 %)
 *   does not cover something important on the lobby screen; the game's device is a plain D3D9 device (no D3D9Ex), so MANAGED textures are legal.
 *
 * [MapPool] Overlay=0 (recommended off until benched; needs Enable=1 and a pool) / OverlayDir= (folder of the .kmi files; empty = text-only names)
 *   / OverlayX=2 / OverlayY=74 (panel top-left, percent of the screen) / OverlayScale=100 (percent) / OverlayCols=8 / OverlayStates=0x2000 / OverlayNames=1.
 */
#ifndef KLMAPPOOL_OV_C
#define KLMAPPOOL_OV_C

#include "klmappool_ov.h"

#define KMPO_NTH (KMP_MAX + 8)
#define KMPO_NTXT 64
#define KMPO_PAD 8.0f
#define KMPO_HEAD 28.0f
#define KMPO_TW 72.0f
#define KMPO_TH 40.0f
#define KMPO_NAMEH 14.0f
#define KMPO_GAP 6.0f

struct kmpo_snap { DWORD at; int valid, pool, n, next, played, state; int st[KMP_MAX]; char name[KMP_MAX][48]; };

static struct {
    int on, log, x, y, scale, cols, names, dead; unsigned mask; char dir[MAX_PATH];
    struct kmpo_snap s[2]; volatile int cur; DWORD snapAt; int lastState, nstate, drawn, shownLogged;
    void *texdev, *white;
    struct { char name[48]; void *tex; int w, h, tried; } th[KMPO_NTH]; int nth;
    struct { char key[80]; void *tex; int w, h; } tx[KMPO_NTXT]; int ntx;
    HMODULE gdi; int gdiTried;
} kmpo;

/* ------------------------------------------------------------------ game thread: the snapshot */
static void kmpo_publish(struct kmpo_snap *s) { kmpo.cur = (int)(s - kmpo.s); }

static void kmpo_snap(int game_thread)
{
    DWORD now = GetTickCount(), sm, state = 0xffff; struct kmpo_snap *s; int i;
    if (!kmpo.on || kmpo.dead || !game_thread || !klh_exe_ok) return;
    if (now - kmpo.snapAt < 100) return;
    kmpo.snapAt = now;
    s = &kmpo.s[1 - kmpo.cur];
    s->valid = 0; s->at = now;
    if (!kmp.on || kmp.pool < 1 || kmp.pool > 3 || !kmp.seed) { kmpo_publish(s); return; }
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION));
    if (!sm || !klh_rd(sm + 0x70, &state, 4)) state = 0xffff;
    if ((int)state != kmpo.lastState) {
        kmpo.lastState = (int)state;
        if (kmpo.log && kmpo.nstate++ < 40) klog("mappool: overlay: session state %lu (%s; shown states mask %08x)", (unsigned long)state, kmpo_state_shown(kmpo.mask, state) ? "SHOWN" : "hidden", kmpo.mask);
    }
    if (!kmpo_state_shown(kmpo.mask, state)) { kmpo_publish(s); return; }
    kmp_ready();                                       /* the same call the load path and the host tick make, on this (game) thread */
    s->pool = kmp.pool; s->state = (int)state;
    s->n = kmp.norder < KMP_MAX ? kmp.norder : KMP_MAX;
    s->next = kmpo_states(kmp.order, kmp.used, s->n, s->st);
    s->played = kmpo_played(s->st, s->n);
    for (i = 0; i < s->n; i++) { strncpy(s->name[i], kmp.name[kmp.order[i]], 47); s->name[i][47] = 0; }
    s->valid = s->n > 0;
    kmpo_publish(s);
}

/* ------------------------------------------------------------------ render thread: Direct3D 9 by vtable */
#define KMPO_VT(o, i) ((*(void ***)(o))[i])
typedef HRESULT (__stdcall *kmpo_pu)(void *);
typedef HRESULT (__stdcall *kmpo_pp)(void *, void *);
typedef HRESULT (__stdcall *kmpo_pd)(void *, DWORD);
typedef HRESULT (__stdcall *kmpo_pdd)(void *, DWORD, DWORD);
typedef HRESULT (__stdcall *kmpo_pdp)(void *, DWORD, void *);
typedef HRESULT (__stdcall *kmpo_pddd)(void *, DWORD, DWORD, DWORD);
typedef HRESULT (__stdcall *kmpo_pdpp)(void *, DWORD, void *, const void *, DWORD);
typedef HRESULT (__stdcall *kmpo_pmk)(void *, UINT, UINT, UINT, DWORD, DWORD, DWORD, void **, void *);
typedef HRESULT (__stdcall *kmpo_pbb)(void *, UINT, UINT, DWORD, void **);
typedef HRESULT (__stdcall *kmpo_pdraw)(void *, DWORD, UINT, const void *, UINT);
typedef ULONG (__stdcall *kmpo_prel)(void *);

struct kmpo_v { float x, y, z, rhw; DWORD c; float u, v; };

static void kmpo_rel(void *o) { if (o) ((kmpo_prel)KMPO_VT(o, 2))(o); }
static void kmpo_rs(void *d, DWORD st, DWORD v) { ((kmpo_pdd)KMPO_VT(d, 57))(d, st, v); }
static void kmpo_tss(void *d, DWORD stage, DWORD t, DWORD v) { ((kmpo_pddd)KMPO_VT(d, 67))(d, stage, t, v); }
static void kmpo_ss(void *d, DWORD s, DWORD t, DWORD v) { ((kmpo_pddd)KMPO_VT(d, 69))(d, s, t, v); }

static void *kmpo_mktex(void *dev, int w, int h, const DWORD *px)
{   /* A8R8G8B8 (21), MANAGED (1), one level */
    void *tex = 0; struct { int pitch; void *bits; } lr; int y;
    if (w < 1 || h < 1 || w > 512 || h > 512) return 0;
    if (((kmpo_pmk)KMPO_VT(dev, 23))(dev, (UINT)w, (UINT)h, 1, 0, 21, 1, &tex, 0) < 0 || !tex) return 0;
    memset(&lr, 0, sizeof lr);
    if (((kmpo_pdpp)KMPO_VT(tex, 19))(tex, 0, &lr, 0, 0) < 0 || !lr.bits) { kmpo_rel(tex); return 0; }       /* IDirect3DTexture9::LockRect(level, &LOCKED_RECT, NULL, 0) */
    for (y = 0; y < h; y++) memcpy((BYTE *)lr.bits + (size_t)y * (size_t)lr.pitch, px + (size_t)y * (size_t)w, (size_t)w * 4);
    ((kmpo_pd)KMPO_VT(tex, 20))(tex, 0);                                                                  /* UnlockRect(level) */
    return tex;
}

static void kmpo_forget(void)
{   /* a new device: the old textures belong to it; forget them (the old device may be gone, so no Release) */
    memset(kmpo.th, 0, sizeof kmpo.th); kmpo.nth = 0; memset(kmpo.tx, 0, sizeof kmpo.tx); kmpo.ntx = 0; kmpo.white = 0;
}

static BYTE *kmpo_readfile(const char *path, DWORD *size)
{
    HANDLE h = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, 0, 0); DWORD n, got = 0; BYTE *b;
    if (h == INVALID_HANDLE_VALUE) return 0;
    n = GetFileSize(h, 0);
    if (n < 12 || n > 512u * 512u * 4u + 12u || !(b = (BYTE *)HeapAlloc(GetProcessHeap(), 0, n))) { CloseHandle(h); return 0; }
    if (!ReadFile(h, b, n, &got, 0) || got != n) { HeapFree(GetProcessHeap(), 0, b); CloseHandle(h); return 0; }
    CloseHandle(h); *size = n; return b;
}

/* the thumbnail of a pool entry; 0 = none (text only). Looked for once. */
static int kmpo_thumb(void *dev, const char *name, void **tex, int *w, int *h)
{
    int i;
    for (i = 0; i < kmpo.nth; i++) if (!strcmp(kmpo.th[i].name, name)) { *tex = kmpo.th[i].tex; *w = kmpo.th[i].w; *h = kmpo.th[i].h; return *tex != 0; }
    if (kmpo.nth >= KMPO_NTH) return 0;
    i = kmpo.nth++; strncpy(kmpo.th[i].name, name, 47); kmpo.th[i].tried = 1;
    if (kmpo.dir[0]) {
        char f[64], p[MAX_PATH + 64]; DWORD sz = 0; BYTE *b;
        kmpo_file(name, f, sizeof f); snprintf(p, sizeof p, "%s\\%s", kmpo.dir, f);
        b = kmpo_readfile(p, &sz);
        if (b) {
            DWORD iw = *(DWORD *)(b + 4), ih = *(DWORD *)(b + 8);
            if (!memcmp(b, "KMI1", 4) && iw >= 1 && ih >= 1 && iw <= 512 && ih <= 512 && sz == 12 + iw * ih * 4) {
                void *t = kmpo_mktex(dev, (int)iw, (int)ih, (const DWORD *)(b + 12));
                if (t) { kmpo.th[i].tex = t; kmpo.th[i].w = (int)iw; kmpo.th[i].h = (int)ih; }
            }
            HeapFree(GetProcessHeap(), 0, b);
        }
        if (kmpo.log && !kmpo.th[i].tex) klog("mappool: overlay: no usable thumbnail %s: text only for %s", p, name);
    }
    *tex = kmpo.th[i].tex; *w = kmpo.th[i].w; *h = kmpo.th[i].h; return *tex != 0;
}

/* ---- text: GDI into a memory bitmap, then a white texture whose alpha is the glyph coverage ---- */
static HDC (WINAPI *g_cdc)(HDC); static HFONT (WINAPI *g_font)(int, int, int, int, int, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, LPCSTR);
static HGDIOBJ (WINAPI *g_sel)(HDC, HGDIOBJ); static BOOL (WINAPI *g_ext)(HDC, LPCSTR, int, LPSIZE);
static HBITMAP (WINAPI *g_dib)(HDC, const BITMAPINFO *, UINT, VOID **, HANDLE, DWORD); static int (WINAPI *g_bk)(HDC, int);
static COLORREF (WINAPI *g_col)(HDC, COLORREF); static BOOL (WINAPI *g_out)(HDC, int, int, LPCSTR, int);
static BOOL (WINAPI *g_del)(HGDIOBJ); static BOOL (WINAPI *g_flush)(void); static BOOL (WINAPI *g_ddc)(HDC);

static int kmpo_gdi(void)
{
    if (!kmpo.gdiTried) {
        kmpo.gdiTried = 1; kmpo.gdi = LoadLibraryA("gdi32.dll");
        if (kmpo.gdi) {
            g_cdc = (HDC (WINAPI *)(HDC))GetProcAddress(kmpo.gdi, "CreateCompatibleDC");
            g_font = (HFONT (WINAPI *)(int, int, int, int, int, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, LPCSTR))GetProcAddress(kmpo.gdi, "CreateFontA");
            g_sel = (HGDIOBJ (WINAPI *)(HDC, HGDIOBJ))GetProcAddress(kmpo.gdi, "SelectObject");
            g_ext = (BOOL (WINAPI *)(HDC, LPCSTR, int, LPSIZE))GetProcAddress(kmpo.gdi, "GetTextExtentPoint32A");
            g_dib = (HBITMAP (WINAPI *)(HDC, const BITMAPINFO *, UINT, VOID **, HANDLE, DWORD))GetProcAddress(kmpo.gdi, "CreateDIBSection");
            g_bk = (int (WINAPI *)(HDC, int))GetProcAddress(kmpo.gdi, "SetBkMode");
            g_col = (COLORREF (WINAPI *)(HDC, COLORREF))GetProcAddress(kmpo.gdi, "SetTextColor");
            g_out = (BOOL (WINAPI *)(HDC, int, int, LPCSTR, int))GetProcAddress(kmpo.gdi, "TextOutA");
            g_del = (BOOL (WINAPI *)(HGDIOBJ))GetProcAddress(kmpo.gdi, "DeleteObject");
            g_ddc = (BOOL (WINAPI *)(HDC))GetProcAddress(kmpo.gdi, "DeleteDC");
            g_flush = (BOOL (WINAPI *)(void))GetProcAddress(kmpo.gdi, "GdiFlush");
        }
    }
    return g_cdc && g_font && g_sel && g_ext && g_dib && g_bk && g_col && g_out && g_del && g_ddc;
}

static void *kmpo_text(void *dev, const char *s, int px, int *w, int *h)
{   /* -> a texture of the string at px pixels high, size in *w *h (native pixels); 0 = no GDI / failed */
    char key[80]; int i, len = (int)strlen(s), tw, th, x; HDC dc; HFONT f, of; SIZE sz; BITMAPINFO bi; void *bits = 0; HBITMAP bm, ob; void *tex = 0; DWORD *out;
    snprintf(key, sizeof key, "%d|%s", px, s);
    for (i = 0; i < kmpo.ntx; i++) if (!strcmp(kmpo.tx[i].key, key)) { *w = kmpo.tx[i].w; *h = kmpo.tx[i].h; return kmpo.tx[i].tex; }
    if (kmpo.ntx >= KMPO_NTXT) {      /* full (changing strings): drop the lot, they are rebuilt on demand */
        for (i = 0; i < kmpo.ntx; i++) kmpo_rel(kmpo.tx[i].tex);
        memset(kmpo.tx, 0, sizeof kmpo.tx); kmpo.ntx = 0;
    }
    i = kmpo.ntx++; strncpy(kmpo.tx[i].key, key, 79); *w = *h = 0;
    if (!len || !kmpo_gdi() || !(dc = g_cdc(0))) return 0;
    f = g_font(-px, 0, 0, 0, 700, 0, 0, 0, 1 /* DEFAULT_CHARSET */, 0, 0, 4 /* ANTIALIASED_QUALITY: grey, not ClearType */, 0, "Arial");
    of = f ? (HFONT)g_sel(dc, f) : 0; memset(&sz, 0, sizeof sz);
    if (!g_ext(dc, s, len, &sz) || sz.cx < 1 || sz.cy < 1) goto done;
    tw = sz.cx + 4; th = sz.cy + 2;
    if (tw > 512 || th > 128) goto done;
    memset(&bi, 0, sizeof bi); bi.bmiHeader.biSize = sizeof bi.bmiHeader; bi.bmiHeader.biWidth = tw; bi.bmiHeader.biHeight = -th; bi.bmiHeader.biPlanes = 1; bi.bmiHeader.biBitCount = 32;
    bm = g_dib(dc, &bi, 0, &bits, 0, 0);
    if (!bm || !bits) { if (bm) g_del(bm); goto done; }
    ob = (HBITMAP)g_sel(dc, bm);
    memset(bits, 0, (size_t)tw * (size_t)th * 4);
    g_bk(dc, 1 /* TRANSPARENT */); g_col(dc, 0xffffff); g_out(dc, 2, 1, s, len);
    if (g_flush) g_flush();
    out = (DWORD *)HeapAlloc(GetProcessHeap(), 0, (size_t)tw * (size_t)th * 4);
    if (out) {
        for (x = 0; x < tw * th; x++) { DWORD a = ((DWORD *)bits)[x] & 0xff; out[x] = (a << 24) | 0x00ffffffu; }
        tex = kmpo_mktex(dev, tw, th, out); HeapFree(GetProcessHeap(), 0, out);
    }
    g_sel(dc, ob); g_del(bm);
    if (tex) { kmpo.tx[i].tex = tex; kmpo.tx[i].w = tw; kmpo.tx[i].h = th; *w = tw; *h = th; }
done:
    if (of) g_sel(dc, of);
    if (f) g_del(f);
    g_ddc(dc);
    return tex;
}

/* one textured quad in screen pixels; tex NULL = the white texture (a flat colour) */
static void kmpo_quad(void *dev, void *tex, float x, float y, float w, float h, DWORD c)
{
    struct kmpo_v v[4]; int i;
    static const float uu[4] = { 0, 1, 0, 1 }, vv[4] = { 0, 0, 1, 1 };
    for (i = 0; i < 4; i++) { v[i].x = x + (i & 1 ? w : 0) - 0.5f; v[i].y = y + (i & 2 ? h : 0) - 0.5f; v[i].z = 0; v[i].rhw = 1; v[i].c = c; v[i].u = uu[i]; v[i].v = vv[i]; }
    ((kmpo_pdp)KMPO_VT(dev, 65))(dev, 0, tex ? tex : kmpo.white);                                          /* SetTexture(0, tex) */
    ((kmpo_pdraw)KMPO_VT(dev, 83))(dev, 5 /* D3DPT_TRIANGLESTRIP */, 2, v, sizeof v[0]);                  /* DrawPrimitiveUP */
}

static void kmpo_label_text(void *dev, float x, float y, const char *s, int px, DWORD c, float *wout)
{
    int w, h; void *t = kmpo_text(dev, s, px, &w, &h);
    if (wout) *wout = t ? (float)w : 0;
    if (t) kmpo_quad(dev, t, x, y, (float)w, (float)h, c);
}

static void kmpo_scene(void *dev, const struct kmpo_snap *s, float sw, float sh)
{
    float sc = sh / 720.0f * (float)kmpo.scale / 100.0f, lw = 0, pw2 = 0, gw, panw, panh, ox, oy, thw, thh;
    int cols = kmpo_cols(s->n, kmpo.cols), rows = kmpo_rows(s->n, cols), i, tpx = (int)(18.0f * sc + 0.5f), npx = (int)(11.0f * sc + 0.5f);
    char prog[48]; DWORD lc = s->pool == 1 ? 0xffe05040u : s->pool == 2 ? 0xff4a98e8u : 0xffe8c848u;
    if (tpx < 8) tpx = 8;
    if (npx < 7) npx = 7;
    snprintf(prog, sizeof prog, "%d / %d PLAYED", s->played, s->n);
    { int w, h; void *t = kmpo_text(dev, kmpo_label(s->pool), tpx, &w, &h); lw = t ? (float)w : 0; t = kmpo_text(dev, prog, npx + 1, &w, &h); pw2 = t ? (float)w : 0; }
    gw = ((float)cols * KMPO_TW + (float)(cols - 1) * KMPO_GAP) * sc;
    panw = gw + 2 * KMPO_PAD * sc;
    if (lw + pw2 + 3 * KMPO_PAD * sc > panw) panw = lw + pw2 + 3 * KMPO_PAD * sc;
    panh = (KMPO_PAD + KMPO_HEAD + (float)rows * (KMPO_TH + KMPO_NAMEH + KMPO_GAP) - KMPO_GAP + KMPO_PAD) * sc;
    kmpo_place((int)sw, (int)sh, panw, panh, kmpo.x, kmpo.y, &ox, &oy);
    kmpo_quad(dev, 0, ox, oy, panw, panh, 0xc0101014u);                                                       /* backing */
    kmpo_quad(dev, 0, ox, oy, panw, 3.0f * sc, lc);                                                           /* pool colour bar */
    kmpo_label_text(dev, ox + KMPO_PAD * sc, oy + (KMPO_PAD - 1) * sc, kmpo_label(s->pool), tpx, 0xffffffffu, 0);
    kmpo_label_text(dev, ox + panw - KMPO_PAD * sc - pw2, oy + (KMPO_PAD + 5) * sc, prog, npx + 1, 0xffc0c0c0u, 0);
    thw = KMPO_TW * sc; thh = KMPO_TH * sc;
    for (i = 0; i < s->n; i++) {
        float cx, cy, x, y; void *tex = 0; int w = 0, h = 0, st = s->st[i], have; DWORD tint = kmpo_tint(st), tc;
        kmpo_cell(i, cols, KMPO_TW * sc, (KMPO_TH + KMPO_NAMEH) * sc, KMPO_GAP * sc, &cx, &cy);
        x = ox + KMPO_PAD * sc + cx; y = oy + (KMPO_PAD + KMPO_HEAD) * sc + cy;
        have = kmpo_thumb(dev, s->name[i], &tex, &w, &h);
        if (st == KMPO_NEXT) kmpo_quad(dev, 0, x - 2 * sc, y - 2 * sc, thw + 4 * sc, thh + 4 * sc, 0xffffc832u);       /* gold frame */
        if (have) kmpo_quad(dev, tex, x, y, thw, thh, tint);
        else { kmpo_quad(dev, 0, x, y, thw, thh, st == KMPO_PLAYED ? 0x80303038u : 0xff2c2c36u); }
        tc = st == KMPO_PLAYED ? 0x80909090u : st == KMPO_NEXT ? 0xffffe070u : 0xffd0d0d0u;
        {
            const char *nm = s->name[i]; int tw, th; void *t;
            if (!strncmp(nm, "stock ", 6)) nm += 6;
            t = kmpo_text(dev, nm, npx, &tw, &th);
            if (t) {
                if (!have) kmpo_quad(dev, t, x + (thw - (float)tw) * 0.5f, y + (thh - (float)th) * 0.5f, (float)tw, (float)th, tc);    /* text-only card: the name inside */
                if (kmpo.names) kmpo_quad(dev, t, x + (thw - (float)tw) * 0.5f, y + thh + 1.0f * sc, (float)tw, (float)th, tc);
            }
        }
        if (st == KMPO_NEXT) {
            int bw, bh; void *t = kmpo_text(dev, "NEXT", npx, &bw, &bh);
            if (t) { kmpo_quad(dev, 0, x, y, (float)bw + 4, (float)bh, 0xe0c89000u); kmpo_quad(dev, t, x + 2, y, (float)bw, (float)bh, 0xff101010u); }
        }
    }
}

static void kmpo_draw(void *dev, const struct kmpo_snap *s)
{
    void *sb = 0, *rt = 0, *bb = 0; DWORD desc[8] = { 0 }; float W = 0, H = 0; HRESULT hr; struct { DWORD x, y, w, h; float n, f; } vp;
    if (((kmpo_pu)KMPO_VT(dev, 3))(dev) != 0) return;                                                         /* TestCooperativeLevel: not lost */
    if (dev != kmpo.texdev) { kmpo_forget(); kmpo.texdev = dev; }
    hr = ((kmpo_pdp)KMPO_VT(dev, 59))(dev, 1 /* D3DSBT_ALL */, &sb);                                          /* CreateStateBlock captures the state as it is now */
    if (hr < 0 || !sb) return;
    ((kmpo_pdp)KMPO_VT(dev, 38))(dev, 0, &rt);                                                                /* GetRenderTarget(0, &rt) */
    if (((kmpo_pbb)KMPO_VT(dev, 18))(dev, 0, 0, 0, &bb) >= 0 && bb) {                                         /* GetBackBuffer(0, 0, MONO, &bb) */
        ((kmpo_pp)KMPO_VT(bb, 12))(bb, desc);                                                                  /* IDirect3DSurface9::GetDesc: Width = dword 6, Height = dword 7 */
        W = (float)desc[6]; H = (float)desc[7];
        if (rt) ((kmpo_pdp)KMPO_VT(dev, 37))(dev, 0, bb);                                                     /* SetRenderTarget(0, bb): only when the old target can be put back */
    }
    if (W >= 320 && H >= 240 && W <= 8192 && H <= 8192 && ((kmpo_pu)KMPO_VT(dev, 41))(dev) >= 0) {           /* BeginScene (fails while the game's scene is open: nothing is drawn) */
        vp.x = 0; vp.y = 0; vp.w = desc[6]; vp.h = desc[7]; vp.n = 0.0f; vp.f = 1.0f;
        ((kmpo_pp)KMPO_VT(dev, 47))(dev, &vp);                                                                 /* SetViewport */
        ((kmpo_pp)KMPO_VT(dev, 92))(dev, 0);                                                                  /* SetVertexShader(NULL) */
        ((kmpo_pp)KMPO_VT(dev, 107))(dev, 0);                                                                 /* SetPixelShader(NULL) */
        ((kmpo_pd)KMPO_VT(dev, 89))(dev, 0x144);                                           /* SetFVF(XYZRHW | DIFFUSE | TEX1) */
        kmpo_rs(dev, 7, 0);   /* ZENABLE */      kmpo_rs(dev, 14, 0);  /* ZWRITEENABLE */    kmpo_rs(dev, 15, 0);  /* ALPHATESTENABLE */
        kmpo_rs(dev, 19, 5);  /* SRCBLEND SRCALPHA */   kmpo_rs(dev, 20, 6);  /* DESTBLEND INVSRCALPHA */   kmpo_rs(dev, 27, 1);  /* ALPHABLENDENABLE */
        kmpo_rs(dev, 22, 1);  /* CULLMODE NONE */   kmpo_rs(dev, 28, 0);  /* FOGENABLE */   kmpo_rs(dev, 52, 0);  /* STENCILENABLE */
        kmpo_rs(dev, 137, 0); /* LIGHTING */     kmpo_rs(dev, 168, 15); /* COLORWRITEENABLE */   kmpo_rs(dev, 174, 0); /* SCISSORTESTENABLE */
        kmpo_rs(dev, 194, 0); /* SRGBWRITEENABLE */   kmpo_rs(dev, 8, 3); /* FILLMODE SOLID */
        kmpo_tss(dev, 0, 1, 4); kmpo_tss(dev, 0, 2, 2); kmpo_tss(dev, 0, 3, 0);                                 /* stage 0 colour: MODULATE(TEXTURE, DIFFUSE) */
        kmpo_tss(dev, 0, 4, 4); kmpo_tss(dev, 0, 5, 2); kmpo_tss(dev, 0, 6, 0);                                 /* alpha: the same */
        kmpo_tss(dev, 1, 1, 1);                                                                                 /* stage 1 off */
        kmpo_ss(dev, 0, 5, 2); kmpo_ss(dev, 0, 6, 2); kmpo_ss(dev, 0, 7, 0);                                    /* MAG / MIN linear, MIP none */
        kmpo_ss(dev, 0, 1, 3); kmpo_ss(dev, 0, 2, 3);                                                           /* ADDRESSU / V clamp */
        if (!kmpo.white) { DWORD one[4] = { 0xffffffffu, 0xffffffffu, 0xffffffffu, 0xffffffffu }; kmpo.white = kmpo_mktex(dev, 2, 2, one); }
        if (kmpo.white) {
            kmpo_scene(dev, s, W, H);
            if (!kmpo.drawn++ && kmpo.log) klog("mappool: overlay: FIRST draw: pool %d (%s), %d maps (%d played), state %d, screen %dx%d, dir '%s'", s->pool, kmpo_label(s->pool), s->n, s->played, s->state, (int)W, (int)H, kmpo.dir);
        }
        ((kmpo_pu)KMPO_VT(dev, 42))(dev);                                                                      /* EndScene */
    }
    if (rt) ((kmpo_pdp)KMPO_VT(dev, 37))(dev, 0, rt);                                                         /* SetRenderTarget back */
    ((kmpo_pu)KMPO_VT(sb, 5))(sb);                                                                            /* IDirect3DStateBlock9::Apply */
    kmpo_rel(sb); kmpo_rel(rt); kmpo_rel(bb);
}

/* from klfps.c's Present wrappers (depth 0, before the real Present), render thread */
static void klmpo_present(void *dev)
{
    struct kmpo_snap c;
    if (!kmpo.on || kmpo.dead || !dev) return;
    if (!kmpo.s[kmpo.cur].valid || GetTickCount() - kmpo.s[kmpo.cur].at > 1500) return;      /* no tick for 1.5 s (session over): stale, hidden */
    c = kmpo.s[kmpo.cur];
    __try { kmpo_draw(dev, &c); }
    __except (EXCEPTION_EXECUTE_HANDLER) { kmpo.dead = 1; klog("mappool: overlay DISABLED: exception in the D3D9 draw (%08lx)", (unsigned long)GetExceptionCode()); }
}

static void kmpo_init(void)
{
    char b[24];
    kmpo.on = GetPrivateProfileIntA("MapPool", "Overlay", 0, klh_ini) != 0;
    if (!kmpo.on) return;
    kmpo.log = GetPrivateProfileIntA("MapPool", "Log", 1, klh_ini) != 0;
    GetPrivateProfileStringA("MapPool", "OverlayDir", "", kmpo.dir, sizeof kmpo.dir, klh_ini);
    { size_t n = strlen(kmpo.dir); while (n && (kmpo.dir[n - 1] == '\\' || kmpo.dir[n - 1] == '/')) kmpo.dir[--n] = 0; }
    kmpo.x = GetPrivateProfileIntA("MapPool", "OverlayX", 2, klh_ini);         if (kmpo.x < 0 || kmpo.x > 95) kmpo.x = 2;
    kmpo.y = GetPrivateProfileIntA("MapPool", "OverlayY", 74, klh_ini);        if (kmpo.y < 0 || kmpo.y > 95) kmpo.y = 74;
    kmpo.scale = GetPrivateProfileIntA("MapPool", "OverlayScale", 100, klh_ini); if (kmpo.scale < 50 || kmpo.scale > 300) kmpo.scale = 100;
    kmpo.cols = GetPrivateProfileIntA("MapPool", "OverlayCols", 8, klh_ini);   if (kmpo.cols < 1 || kmpo.cols > 16) kmpo.cols = 8;
    kmpo.names = GetPrivateProfileIntA("MapPool", "OverlayNames", 1, klh_ini) != 0;
    GetPrivateProfileStringA("MapPool", "OverlayStates", "0x2000", b, sizeof b, klh_ini);
    kmpo.mask = (unsigned)strtoul(b, 0, 0); if (!kmpo.mask) kmpo.mask = 0x2000u;
    kmpo.lastState = -2;
    klog("mappool: overlay ON (NOT run live): dir '%s' at %d%%/%d%% scale %d%% cols %d states mask %08x; needs [FrameLimit] Enable=1 (the Present wrapper) and a pool", kmpo.dir, kmpo.x, kmpo.y, kmpo.scale, kmpo.cols, kmpo.mask);
}

#endif
