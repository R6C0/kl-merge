/*
 * klhud_tracker.c - the VEHICLE MARKER in the world (2026-10-14, the owner: 'those 3 states are so big far away, they need to only appear
 * visible when youre close and definitely smaller'). Part of KLHook, an add-on of klhud.c: included by klhook.c after klhud_escape.c.
 *
 * THE ELEMENT (kl2.exe build 0490, read statically): ZGameplayTrackerDisplay = [osd+0x10f8], vtable 0xbbe950, slot 2 Render
 * 0x8e2060 (thiscall, Render(ctx, cam), ret 8). Its Render walks FIVE tracked things, 0x110 bytes apart from +0x28: per entry
 *   +0x000 the tracked object (0 = the entry is skipped: `cmp dword [esi-0x10c], 0 / je` at 0x8e215e)
 *   +0x0f0 its distance in world units (x 0.01 = the '%.0f m' it prints, 0x8e2383)
 *   +0x10c its kind (1 / 2 / 5 / 6 / 7 = the vehicle's states: the coloured ball, the time, the bar)
 * Every size and offset it draws is multiplied by the float at 0xcee050 (1.0; the HUD's scale, read by the whole HUD).
 * WHAT THIS PART DOES (a private vtable copy of the element, slot 2 = kltrk_render, then the stock Render):
 *   - an entry farther than TrackerNear metres is hidden for the length of the call (its object pointer is 0 for the call and put
 *     back by compare-and-swap) - no ball, no time, no arrow at the screen's edge;
 *   - the scale float is TrackerScale for the length of the call (put back after; the render thread runs the HUD one element at a
 *     time, so no other element sees it).
 * Keys ([HUD], needs Enable=1): Tracker=1 (0 = stock)  TrackerNear=30 (m; 0 = no distance limit)  TrackerScale=0.6 (0.3 .. 1.0)
 */
#define KLHUD_TRACKER_C

#define KLTRK_VT        0x00bbe950u
#define KLTRK_RENDER    0x008e2060u
#define KLTRK_O_EL      0x10f8
#define KLTRK_SCALE     0x00cee050u
#define KLTRK_E0        0x28
#define KLTRK_ESTEP     0x110
#define KLTRK_N         5
#define KLTRK_E_DIST    0xf0
#define KLTRK_NSLOT     12

static struct { int on; float near_m, scale; } kltrk;
static struct { DWORD osd, elem; int told; } kltrk_r;
static int kltrk_code_bad, kltrk_scale_ok;
static DWORD kltrk_vt[KLTRK_NSLOT + 1];
static int kltrk_vt_ready;
static volatile LONG kltrk_n_call, kltrk_n_hid;

static char __fastcall kltrk_render(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el, saved[KLTRK_N], sc_old = 0, sc_new; int i, hid = 0, scaled = 0; char r; float f;
    (void)edx;
    InterlockedIncrement(&kltrk_n_call);
    memset(saved, 0, sizeof saved);
    if (kltrk.on && e == kltrk_r.elem) {
        if (kltrk.near_m > 0.0f) for (i = 0; i < KLTRK_N; i++) {
            DWORD base = e + KLTRK_E0 + KLTRK_ESTEP * i, obj = klh_rd32(base); float d = 0;
            if (!obj || !klh_rd(base + KLTRK_E_DIST, &d, 4) || !(d == d)) continue;
            if (d * 0.01f > kltrk.near_m &&
                InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)base, 0, (LONG)obj) == (LONG)obj) { saved[i] = obj; hid++; }
        }
        sc_old = klh_rd32((DWORD_PTR)KLH_VA(KLTRK_SCALE)); memcpy(&f, &sc_old, 4);
        if (kltrk_scale_ok && f > 0.5f && f < 2.0f && kltrk.scale < 0.999f) {
            f *= kltrk.scale; memcpy(&sc_new, &f, 4);
            scaled = InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)KLH_VA(KLTRK_SCALE), (LONG)sc_new, (LONG)sc_old) == (LONG)sc_old;
        }
        if (hid) InterlockedExchangeAdd(&kltrk_n_hid, hid);
    }
    r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLTRK_RENDER))(el, 0, ctx, cam);
    if (scaled) InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)KLH_VA(KLTRK_SCALE), (LONG)sc_old, (LONG)sc_new);
    for (i = 0; i < KLTRK_N; i++) if (saved[i])
        InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + KLTRK_E0 + KLTRK_ESTEP * i), (LONG)saved[i], 0);
    return r;
}

static int kltrk_wrap(DWORD osd)
{
    static const BYTE render_code[10] = { 0x6a, 0xff, 0x68, 0x89, 0x22, 0xad, 0x00, 0x64, 0xa1, 0x00 };     /* 0x8e2060 push -1; push 0xad2289; mov eax, fs:[0] */
    DWORD el, cur = 0, vt;
    if (!(el = klh_rd32(osd + KLTRK_O_EL)) || !klh_rd(el, &cur, 4)) return 0;
    if (!kltrk_vt_ready) {
        if (!klu_same_code(KLTRK_RENDER, render_code, sizeof render_code) || !klh_rd((DWORD_PTR)KLH_VA(KLTRK_VT - 4), kltrk_vt, sizeof kltrk_vt) || kltrk_vt[1 + 2] != KLTRK_RENDER) {
            klog("hud: tracker: the marker's Render is not the routine this build knows (0x8e2060; slot 2 = %08lx): the marker stays stock", kltrk_vt[1 + 2]);
            kltrk_code_bad = 1;
            return 0;
        }
        kltrk_vt[1 + 2] = (DWORD)(DWORD_PTR)kltrk_render;
        kltrk_vt_ready = 1;
        kltrk_scale_ok = klh_may_write((void *)(DWORD_PTR)KLH_VA(KLTRK_SCALE), 4, "the HUD scale float, for the marker's call only");     /* the guard's answer (hashed range / policy) */
        if (!kltrk_scale_ok) klog("hud: tracker: the HUD scale float 0xcee050 may not be written here: the marker keeps its size (the distance limit still works)");
    }
    vt = (DWORD)(DWORD_PTR)&kltrk_vt[1];
    if (cur == vt) { kltrk_r.elem = el; return 1; }
    if (cur != KLTRK_VT) { if (!kltrk_r.told++) klog("hud: tracker: the element at osd+0x10f8 = %08lx has vtable %08lx, not ZGameplayTrackerDisplay's: the marker stays stock", el, cur); return 0; }
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the vehicle marker's vtable (private copy, slot 2 wrapped)")) return 0;
    kltrk_r.elem = el;
    klog("hud: tracker: element %08lx (the vehicle marker) renders through the private vtable: hidden beyond %.0f m, drawn at %.0f %% size", el, kltrk.near_m, kltrk.scale * 100.0f);
    return 1;
}

static void kltrk_tick(int game_thread)
{
    static DWORD last, said; DWORD now = GetTickCount(), osd;
    if (!kltrk.on || !klu.on || !klh_exe_ok || !game_thread || kltrk_code_bad || now - last < 100) return;
    last = now;
    osd = klu_r.osd;
    if (!osd || !klu_r.made || klu_r.fault || klh_rd32(osd) != KLU_OSD_VT) { kltrk_r.osd = 0; kltrk_r.elem = 0; return; }
    if (osd != kltrk_r.osd) { kltrk_r.osd = osd; kltrk_r.elem = 0; }
    if (!kltrk_r.elem) kltrk_wrap(osd);
    if (klu.log >= 2 && now - said >= 10000) {
        said = now;
        klog("hud: tracker: %ld marker calls, %ld far entries hidden", (long)InterlockedExchange(&kltrk_n_call, 0), (long)InterlockedExchange(&kltrk_n_hid, 0));
    }
}

static void kltrk_init(void)
{
    if (!klu.on) return;
    kltrk.on = klu_inii("Tracker", 1, 0, 1);
    if (!kltrk.on) return;
    kltrk.near_m = klu_inif("TrackerNear", "30"); if (!(kltrk.near_m >= 0 && kltrk.near_m <= 1000)) kltrk.near_m = 30;
    kltrk.scale = klu_inif("TrackerScale", "0.6"); if (!(kltrk.scale >= 0.3f && kltrk.scale <= 1.0f)) kltrk.scale = 0.6f;
    klog("hud: tracker: on; the vehicle marker shows within %.0f m only, at %.0f %% of its size", kltrk.near_m, kltrk.scale * 100.0f);
}
