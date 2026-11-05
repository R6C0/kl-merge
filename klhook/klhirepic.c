/* DEAD ROUTE (2026-11-05): Present is never wrapped on the owner's PC (with [FrameLimit] Enable=0 nothing is wrapped; with Enable=1 the Steam overlay forces
   "RECURSION CUT" about 1 s after start, which unwraps Present), so this overlay can never draw there. The replacement is [Hire] BakedPics / [ShopPage] OwnPics
   (klpicown_logic.h, tools/kl_shop_pics.py): the game's own menu renderer draws baked picture entities. Kept (default off, tests green) until BakedPics has passed live. */
/*
 * klhirepic.c - [Hire] PagePics: the black and white heister card drawn over the big picture box of the HIRE A HEISTER page (2026-11-05; owner: 'please get
 * the correct black and white icon for everyone'). Part of KLHook (included by klhook.c right AFTER klmappool_ov.c, whose D3D9 helpers it reuses). NOT run live.
 * READ-ONLY towards the game: no .text / .rdata patch, no data write. It reads kspg.* (klshoppage.c) and the shop's shown row, and draws with the game's own
 * IDirect3DDevice9 from klfps.c's Present wrapper, the way klmappool_ov.c does (same setup: one state block captured and applied, render target put back,
 * XYZRHW quad, __try guard that disables the overlay for the session).
 *
 * WHY AN OVERLAY: the stock big picture shows one of the 36 shared gun tiles (page II only re-points among them; adding a new entity to the menu scene is
 * unproven), so a heister's own picture cannot be put into the game's picture. The hire page already hides the stock picture for rows without stars
 * (klshoppage.c gfx hook), so the card is drawn where it was.
 *
 * GATE (game thread, klhp_snap from klshoppage_tick's caller, every 50 ms): kspg.hire && !kspg.ctl && kspg.hact && KSPG_MODE == 2 (khp_want), the row
 * = KSPG_SHOWN_ROW -> KLChar 1..16 (khp_char_of_row, the same table as kspg_h_ch). Nothing is drawn outside the hire page; host and client both draw (local).
 * IMAGES: <PagePicsDir>\char_NN.kmi (KMI1, tools/kl_portraits.py gray), 445 x 210 normally, any size up to 512 x 512 is stretched into the box.
 * A missing / bad file draws nothing (logged once per heister). Position / scale: khp_box (klhirepic.h), GUESS at 16:9 and larger, measured at 4:3.
 *
 * [Hire] PagePics=0 (recommended off until tested live) / PagePicsDir= (empty = <game folder>\KLPortraits) / PagePicsLog=1.
 */
#ifndef KLHIREPIC_C
#define KLHIREPIC_C

#include "klhirepic.h"

static struct {
    int on, log, dead, drawn; char dir[MAX_PATH];
    volatile int ch; volatile DWORD at;
    void *texdev;
    struct { void *tex; int w, h, tried; } t[17];
} khp;

/* game thread: publish which heister the page shows (0 = none) */
static void khp_snap(int game_thread)
{
    static DWORD last; DWORD now = GetTickCount(); int ch = 0;
    if (!khp.on || khp.dead || !game_thread || !klh_exe_ok) return;
    if (now - last < 50) return;
    last = now;
    if (kspg.hire)
        ch = khp_want(kspg.hire, kspg.ctl, kspg.hact, klh_rd32((DWORD_PTR)KLH_VA(KSPG_MODE)), (int)klh_rd32((DWORD_PTR)KLH_VA(KSPG_SHOWN_ROW)));
    khp.ch = ch; khp.at = now ? now : 1;
}

static void khp_forget(void) { memset(khp.t, 0, sizeof khp.t); }

/* the card of one heister; 0 = none. Looked for once per device. */
static int khp_tex(void *dev, int ch, void **tex, int *w, int *h)
{
    if (!khp.t[ch].tried) {
        char f[16], p[MAX_PATH + 32]; DWORD sz = 0; BYTE *b; unsigned iw = 0, ih = 0;
        khp.t[ch].tried = 1;
        khp_file(ch, f, sizeof f); snprintf(p, sizeof p, "%s\\%s", khp.dir, f);
        b = kmpo_readfile(p, &sz);
        if (b && khp_kmi_ok(b, sz, &iw, &ih)) {
            void *t = kmpo_mktex(dev, (int)iw, (int)ih, (const DWORD *)(b + 12));
            if (t) { khp.t[ch].tex = t; khp.t[ch].w = (int)iw; khp.t[ch].h = (int)ih; }
        }
        if (b) HeapFree(GetProcessHeap(), 0, b);
        if (khp.log) klog("hirepic: heister %d: %s %s", ch, p, khp.t[ch].tex ? "loaded" : "NOT usable (missing or not a KMI1 up to 512 x 512): nothing drawn");
    }
    *tex = khp.t[ch].tex; *w = khp.t[ch].w; *h = khp.t[ch].h; return *tex != 0;
}

static void khp_draw(void *dev, int ch)
{
    void *sb = 0, *rt = 0, *bb = 0, *tex = 0; DWORD desc[8] = { 0 }; float W = 0, H = 0; HRESULT hr; struct { DWORD x, y, w, h; float n, f; } vp; int iw = 0, ih = 0;
    if (((kmpo_pu)KMPO_VT(dev, 3))(dev) != 0) return;                                                         /* TestCooperativeLevel: not lost */
    if (dev != khp.texdev) { khp_forget(); khp.texdev = dev; }
    if (!khp_tex(dev, ch, &tex, &iw, &ih)) return;
    hr = ((kmpo_pdp)KMPO_VT(dev, 59))(dev, 1 /* D3DSBT_ALL */, &sb);
    if (hr < 0 || !sb) return;
    ((kmpo_pdp)KMPO_VT(dev, 38))(dev, 0, &rt);
    if (((kmpo_pbb)KMPO_VT(dev, 18))(dev, 0, 0, 0, &bb) >= 0 && bb) {
        ((kmpo_pp)KMPO_VT(bb, 12))(bb, desc);
        W = (float)desc[6]; H = (float)desc[7];
        if (rt) ((kmpo_pdp)KMPO_VT(dev, 37))(dev, 0, bb);
    }
    if (W >= 320 && H >= 240 && W <= 8192 && H <= 8192 && ((kmpo_pu)KMPO_VT(dev, 41))(dev) >= 0) {           /* BeginScene (fails while the game's scene is open: nothing is drawn) */
        float x, y, w, h;
        vp.x = 0; vp.y = 0; vp.w = desc[6]; vp.h = desc[7]; vp.n = 0.0f; vp.f = 1.0f;
        ((kmpo_pp)KMPO_VT(dev, 47))(dev, &vp);
        ((kmpo_pp)KMPO_VT(dev, 92))(dev, 0);
        ((kmpo_pp)KMPO_VT(dev, 107))(dev, 0);
        ((kmpo_pd)KMPO_VT(dev, 89))(dev, 0x144);                                           /* SetFVF(XYZRHW | DIFFUSE | TEX1) */
        kmpo_rs(dev, 7, 0); kmpo_rs(dev, 14, 0); kmpo_rs(dev, 15, 0);
        kmpo_rs(dev, 19, 5); kmpo_rs(dev, 20, 6); kmpo_rs(dev, 27, 1);
        kmpo_rs(dev, 22, 1); kmpo_rs(dev, 28, 0); kmpo_rs(dev, 52, 0);
        kmpo_rs(dev, 137, 0); kmpo_rs(dev, 168, 15); kmpo_rs(dev, 174, 0);
        kmpo_rs(dev, 194, 0); kmpo_rs(dev, 8, 3);
        kmpo_tss(dev, 0, 1, 4); kmpo_tss(dev, 0, 2, 2); kmpo_tss(dev, 0, 3, 0);
        kmpo_tss(dev, 0, 4, 4); kmpo_tss(dev, 0, 5, 2); kmpo_tss(dev, 0, 6, 0);
        kmpo_tss(dev, 1, 1, 1);
        kmpo_ss(dev, 0, 5, 2); kmpo_ss(dev, 0, 6, 2); kmpo_ss(dev, 0, 7, 0);
        kmpo_ss(dev, 0, 1, 3); kmpo_ss(dev, 0, 2, 3);
        khp_box(W, H, &x, &y, &w, &h);
        kmpo_quad(dev, tex, x, y, w, h, 0xffffffffu);
        if (!khp.drawn++ && khp.log) klog("hirepic: FIRST draw: heister %d, image %dx%d into %.0f,%.0f %.0fx%.0f on a %dx%d screen", ch, iw, ih, x, y, w, h, (int)W, (int)H);
        ((kmpo_pu)KMPO_VT(dev, 42))(dev);                                                                      /* EndScene */
    }
    if (rt) ((kmpo_pdp)KMPO_VT(dev, 37))(dev, 0, rt);
    ((kmpo_pu)KMPO_VT(sb, 5))(sb);                                                                            /* IDirect3DStateBlock9::Apply */
    kmpo_rel(sb); kmpo_rel(rt); kmpo_rel(bb);
}

/* from klfps.c's Present wrappers (depth 0, before the real Present), render thread */
static void klhp_present(void *dev)
{
    int ch;
    if (!khp.on || khp.dead || !dev) return;
    ch = khp.ch;
    if (ch < 1 || ch > 16 || !khp_fresh(GetTickCount(), khp.at, 400)) return;      /* no tick for 0.4 s (page closed, session over): hidden */
    __try { khp_draw(dev, ch); }
    __except (EXCEPTION_EXECUTE_HANDLER) { khp.dead = 1; klog("hirepic: DISABLED: exception in the D3D9 draw (%08lx)", (unsigned long)GetExceptionCode()); }
}

static void khp_init(void)
{
    khp.on = GetPrivateProfileIntA("Hire", "PagePics", 0, klh_ini) != 0;
    if (!khp.on) return;
    khp.log = GetPrivateProfileIntA("Hire", "PagePicsLog", 1, klh_ini) != 0;
    GetPrivateProfileStringA("Hire", "PagePicsDir", "", khp.dir, sizeof khp.dir, klh_ini);
    if (!khp.dir[0]) snprintf(khp.dir, sizeof khp.dir, "%s\\KLPortraits", dir);
    { size_t n = strlen(khp.dir); while (n && (khp.dir[n - 1] == '\\' || khp.dir[n - 1] == '/')) khp.dir[--n] = 0; }
    klog("hirepic: PagePics ON (NOT run live): dir '%s'; needs [FrameLimit] Enable=1 (the Present wrapper) and the hire page", khp.dir);
}

#endif
