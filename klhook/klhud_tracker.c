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
 * 2026-10-15 (owner: 'vehicle icons - make sure they don't overlap each other and make sure you can't see them if they're far
 * away'). Read again (objdump of 0x8e2060 and of the element's Tick, slot 5 = 0x691940): the five entries are EVERY in-world
 * marker this element draws - the stock Render has three drawing paths by the kind at +0x10c:
 *   kinds 1 2 5 6 7  = the ball (picture 161 row osd+0x78c) + the bar (182) + '%.0f m'          (0x8e2212..)
 *   kinds 8 9 10     = the escape vehicle: car 170 / chopper 171 (kind 8) on picture 164 + bar + 'm:ss' (0x8e2415..)
 *   kinds 3 4        = pictures 0xaa..0xac (162 row) + '%.0f m'                                  (0x8e2845..)
 * so the distance limit (object pointer 0 for the call) already covers all of them, whatever the kind; what the earlier part
 * did NOT do: (a) the band at the limit flickered as the distance crossed it; (b) markers on top of each other on the screen.
 * Entry fields used (Tick 0x691df8..0x691e18 writes them every frame, Render 0x8e2188..0x8e21f9 reads them):
 *   +0x0f0 distance (cm)   +0x0f4 the stock's MIN distance (kinds 1-7: hidden nearer)   +0x0f8 the stock's MAX (0 = none)
 *   +0x0fc / +0x100 the screen point x, y in -0.5 .. 0.5 (|x| or |y| >= 0.5 = off screen: the stock draws the edge arrow);
 *   the Render multiplies them by (-2 T+0, -2 T+4) = (1280 A, -720 B): virtual px = (640 + 1280 x, 360 - 720 y).
 * DE-CLUTTER (TrackerDeclutter=1): the on-screen entries the stock would draw are taken nearest first; one whose box overlaps a
 * box already kept is hidden for the call (the same compare-and-swap as the distance limit). WHY HIDE AND NOT PUSH APART: two
 * boxes that overlap point the same way, so the farther one adds nothing you can act on; a pushed stack would float off the
 * vehicle it names (the stack's point IS the vehicle's place) and could be pushed over other HUD parts; the three paths have
 * different stack heights (pictures 161 / 164 / 162 plus text) so a push needs their exact layout, the hide needs none; and the
 * same vehicle tracked by two entries (same place, same distance) is simply shown once. The box is TrackerSepW x TrackerSepH
 * virtual px x the HUD scale (48 x 56: the marker's icon + its text line; GUESS until seen live, the log line gives the points).
 * NO FADE: the colours the Render uses are rewritten by the Tick / the Render itself every frame (base+0x68 = [0xbbe490..4a0]
 * at 0x8e2543 / 0x8e2900, the bar corners base+0xdc..0xe8 in the Tick), so a fade would mean wrapping DrawChunk; not cheap. In its
 * place a hysteresis band: an entry hidden by distance shows again only TrackerBand metres inside the limit (no flicker).
 * Keys ([HUD], needs Enable=1): Tracker=1 (0 = stock)  TrackerNear=30 (m; 0 = no distance limit)  TrackerScale=1.0 (0.3 .. 1.0; OFF by default: live v60_TRK the scale float moved the marker's parts apart - a stray piece of its bar - rather than shrinking them; the ball is made smaller in its picture instead, tools/kl_hud_marks.py VEHICLE_DISC)
 *   TrackerBand=2 (m, 0 .. 20: hidden beyond TrackerNear, shown again within TrackerNear - TrackerBand)
 *   TrackerDeclutter=1 (0 = markers may overlap, stock)   TrackerSepW=48 TrackerSepH=56 (virtual px, 8 .. 400: two markers whose points are closer than this overlap)
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
#define KLTRK_E_MIN     0xf4
#define KLTRK_E_MAX     0xf8
#define KLTRK_E_X       0xfc
#define KLTRK_E_Y       0x100
#define KLTRK_E_KIND    0x10c

static struct { int on, declutter, escfar; float near_m, scale, band, sepw, seph; } kltrk;
static struct { DWORD osd, elem; int told; } kltrk_r;
static int kltrk_code_bad, kltrk_scale_ok;
static DWORD kltrk_vt[KLTRK_NSLOT + 1];
static int kltrk_vt_ready;
static volatile LONG kltrk_n_call, kltrk_n_hid, kltrk_n_lap, kltrk_n_max;
static DWORD kltrk_far[KLTRK_N];             /* render thread only: the object an entry had when the distance hid it (hysteresis) */
static char kltrk_seen[160];                 /* render thread: the last entry table, for the 10 s log line */

/* the stock Render's path for a kind: 1 = ball 161, 2 = vehicle 164, 3 = pictures 162; 0 = it draws nothing */
static int kltrk_path(DWORD kind)
{
    if (kind == 1 || kind == 2 || kind == 5 || kind == 6 || kind == 7) return 1;
    if (kind == 8 || kind == 9 || kind == 10) return 2;
    if (kind == 3 || kind == 4) return 3;
    return 0;
}

/* the box of a marker in virtual px (TrackerSepW x TrackerSepH at HUD scale 1). Not the picture's row: pictures 161..164 are
   256 x 64 sheets (re/hud_data.md), the drawn part is much smaller (the stock icon is about 26 px, re/hud_escape.md) */
static void kltrk_box(int path, float hud, float *w, float *h)
{
    (void)path;
    *w = kltrk.sepw * hud; *h = kltrk.seph * hud;
}

static char __fastcall kltrk_render(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el, saved[KLTRK_N], sc_old = 0, sc_new; int i, hid = 0, scaled = 0, nc = 0, lap = 0; char r; float f;
    struct kltrk_cand { int i, path, on; DWORD obj, kind; float d, px, py; } cand[KLTRK_N], tmpc;
    (void)edx;
    InterlockedIncrement(&kltrk_n_call);
    memset(saved, 0, sizeof saved);
    if (kltrk.on && e == kltrk_r.elem) {
        for (i = 0; i < KLTRK_N; i++) {
            DWORD base = e + KLTRK_E0 + KLTRK_ESTEP * i, obj = klh_rd32(base), kind = 0; float d = 0, mn = 0, mx = 0, x = 0, y = 0, lim;
            int path, on;
            if (!obj) { kltrk_far[i] = 0; continue; }
            if (!klh_rd(base + KLTRK_E_DIST, &d, 4) || !(d == d)) continue;
            kind = klh_rd32(base + KLTRK_E_KIND); path = kltrk_path(kind);
            klh_rd(base + KLTRK_E_MIN, &mn, 4); klh_rd(base + KLTRK_E_MAX, &mx, 4); klh_rd(base + KLTRK_E_X, &x, 4); klh_rd(base + KLTRK_E_Y, &y, 4);
            on = path && (x < 0.5f && x > -0.5f && y < 0.5f && y > -0.5f);
            if (path != 2 && path && !(mn <= d && (mx == 0.0f || mx >= d))) path = 0;                          /* the stock's own min / max gate (0x8e2188..0x8e21b4; not for 8 / 9 / 10) */
            lim = kltrk.near_m - (kltrk_far[i] == obj ? kltrk.band : 0.0f);                                      /* hysteresis: once hidden, back only inside the band */
            if (kltrk.near_m > 0.0f && d * 0.01f > lim && !(kltrk.escfar && path == 2)) {      /* TrackerEscapeFar: the escape vehicle (8 / 9 / 10) at any distance */
                if (InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)base, 0, (LONG)obj) == (LONG)obj) { saved[i] = obj; hid++; }
                kltrk_far[i] = obj;
                path = 0;
            } else kltrk_far[i] = 0;
            cand[nc].i = i; cand[nc].obj = obj; cand[nc].d = d; cand[nc].px = 640.0f + 1280.0f * x; cand[nc].py = 360.0f - 720.0f * y; cand[nc].path = path; cand[nc].on = on && path; cand[nc].kind = kind; nc++;
        }
        if (kltrk.declutter && nc > 1) {
            float hud = 1.0f; DWORD hb = klh_rd32((DWORD_PTR)KLH_VA(KLTRK_SCALE)); int j, k;
            memcpy(&hud, &hb, 4); if (!(hud > 0.1f && hud < 4.0f)) hud = 1.0f;
            for (j = 1; j < nc; j++) for (k = j; k > 0 && cand[k].d < cand[k - 1].d; k--) { tmpc = cand[k]; cand[k] = cand[k - 1]; cand[k - 1] = tmpc; }      /* nearest first; ties keep the entry order */
            for (j = 0; j < nc; j++) {
                float wj, hj, wk, hk;
                if (!cand[j].on) continue;
                kltrk_box(cand[j].path, hud, &wj, &hj);
                for (k = 0; k < j; k++) {
                    if (!cand[k].on) continue;
                    kltrk_box(cand[k].path, hud, &wk, &hk);
                    if (fabsf(cand[j].px - cand[k].px) < (wj + wk) * 0.5f && fabsf(cand[j].py - cand[k].py) < (hj + hk) * 0.5f) break;
                }
                if (k < j) {                                                                                     /* overlaps a nearer kept marker: hidden for this call */
                    DWORD base = e + KLTRK_E0 + KLTRK_ESTEP * cand[j].i;
                    cand[j].on = 0;
                    if (!saved[cand[j].i] && InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)base, 0, (LONG)cand[j].obj) == (LONG)cand[j].obj) { saved[cand[j].i] = cand[j].obj; lap++; }
                }
            }
            if (lap) InterlockedExchangeAdd(&kltrk_n_lap, lap);
        }
        if (nc > kltrk_n_max) InterlockedExchange(&kltrk_n_max, nc);
        if (nc) {   /* the table for the 10 s log line (render thread writes, the tick reads a copy; a torn line only) */
            char t[160]; int j, n = 0;
            for (j = 0; j < nc && n < (int)sizeof t - 40; j++)
                n += _snprintf(t + n, sizeof t - n, "%s#%d k%lu %.0fm (%.0f,%.0f)%s", j ? " " : "", cand[j].i, (unsigned long)cand[j].kind, cand[j].d * 0.01f, cand[j].px, cand[j].py,
                               saved[cand[j].i] ? (kltrk_far[cand[j].i] ? " far" : " lap") : cand[j].on ? " on" : " off");
            t[sizeof t - 1] = 0; memcpy(kltrk_seen, t, sizeof t);
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
    klog("hud: tracker: element %08lx (the vehicle marker) renders through the private vtable: hidden beyond %.0f m, overlaps %s, the scale float at %.0f %% for its call", el, kltrk.near_m, kltrk.declutter ? "nearest only" : "stock", kltrk.scale * 100.0f);
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
        klog("hud: tracker: %ld marker calls, %ld far entries hidden, %ld overlapping hidden, up to %ld entries; last: %s", (long)InterlockedExchange(&kltrk_n_call, 0),
             (long)InterlockedExchange(&kltrk_n_hid, 0), (long)InterlockedExchange(&kltrk_n_lap, 0), (long)InterlockedExchange(&kltrk_n_max, 0), kltrk_seen[0] ? kltrk_seen : "none");
        kltrk_seen[0] = 0;
    }
}

static void kltrk_init(void)
{
    if (!klu.on) return;
    kltrk.on = klu_inii("Tracker", 1, 0, 1);
    if (!kltrk.on) return;
    kltrk.near_m = klu_inif("TrackerNear", "30"); if (!(kltrk.near_m >= 0 && kltrk.near_m <= 1000)) kltrk.near_m = 30;
    kltrk.scale = klu_inif("TrackerScale", "1.0"); if (!(kltrk.scale >= 0.3f && kltrk.scale <= 1.0f)) kltrk.scale = 1.0f;
    kltrk.band = klu_inif("TrackerBand", "2"); if (!(kltrk.band >= 0 && kltrk.band <= 20)) kltrk.band = 2;
    if (kltrk.band > kltrk.near_m * 0.5f) kltrk.band = kltrk.near_m * 0.5f;
    kltrk.declutter = klu_inii("TrackerDeclutter", 1, 0, 1);
    kltrk.escfar = klu_inii("TrackerEscapeFar", 0, 0, 1);
    if (kltrk.escfar) klog("hud: tracker: TrackerEscapeFar=1: the escape vehicle marker (kinds 8 / 9 / 10) ignores the %.0f m limit", kltrk.near_m);
    kltrk.sepw = (float)klu_inii("TrackerSepW", 48, 8, 400); kltrk.seph = (float)klu_inii("TrackerSepH", 56, 8, 400);
    klog("hud: tracker: on; every in-world marker (ball / vehicle / pictures) shows within %.0f m only (back within %.0f m), at %.0f %% of its size; overlapping markers: %s (box %.0f x %.0f virtual px)",
         kltrk.near_m, kltrk.near_m - kltrk.band, kltrk.scale * 100.0f, kltrk.declutter ? "the nearest only" : "stock", kltrk.sepw, kltrk.seph);
}
