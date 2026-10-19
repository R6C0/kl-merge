/* klrigid.c - [Rigid]: a heavier, more rigid TURN for the local player (mouse input side) and the shaping functions a
 * remote-player smoother can call. OFF unless [Rigid] Enable=1. Part of KLHook (SHIP and TEST alike). Design and numbers:
 * re\rigid_feel.md. NOTHING HERE HAS RUN IN THE GAME (compile-checked only; the curve maths ran in an off-game harness).
 *
 * WHAT IT IS (labels: CERTAIN = read in a file / the exe, GUESS = inference)
 *   1. LOCAL INPUT (the lever re\kl2_rotation.md section 5A found). The game reads its mouse once a frame through
 *      IDirectInputDevice8::GetDeviceState (ZMouseWintel update 0x650840, 0x14-byte DIMOUSESTATE2: lX +0, lY +4) - CERTAIN
 *      (klauto.c). The camera IS the aim ray, so what turns the camera turns the aim. This module changes only the
 *      relative counts lX / lY of that one call, per frame, and CONSERVES them: counts that exceed the turn-rate budget wait in
 *      a backlog (capped) and are paid out over the next frames. Nothing is lost except what overflows the backlog, so
 *      a 180 degree flick takes longer instead of being cut; a slow aim correction is untouched.
 *        out_yaw = min( pending * (1 - exp(-dt / SmoothMs)) , cap(pending) * dt )
 *        cap(e)  = YawMinDps + (YawMaxDps - YawMinDps) * sqrt(min(e / CurveFullDeg, 1))   (e = the pending turn in degrees)
 *      The curve is Payday 2's husk look limiter (re\pd2_netfeel.md 2: lerp(40,360,sqrt(err/90))), used here on the
 *      pending turn: small corrections run slowly (and cost almost no time), big ones at the top rate. Counts are turned
 *      into degrees with DegPerCount (the test rig measured 0.17 at the owner's sensitivity: GUESS that it still holds, it
 *      only scales the caps, never the amount turned).
 *      Aiming: while the camera's aim byte is set the filter is bypassed (AimExempt=1; the pending backlog is paid out at
 *      once). The byte is [cam+0x640], cam = [P+0xbd8] - klcam.c calls it "the aiming case, ASSUMPTION": Log=1 prints
 *      its changes so it can be checked; a wrong byte only moves the exemption, never breaks input.
 *      Pass-through (and the backlog is cleared) when there is no local player, the pause / cut flag [gd+0x4cd8] is set
 *      (klcam.c: ASSUMPTION), a frame gap over 250 ms, or the key is off. So menus (the mouse also moves the cursor there)
 *      are left alone as far as those two tests can see. Gamepad input (gc0 in the binding text) is NOT touched.
 *   2. HOW IT HOOKS (no code byte, no .rdata, nothing hashed: re\antitamper.md, klranges.h). The hook is a vtable-POINTER
 *      swap on two HEAP objects of dinput8: the IDirectInput8 object (slot 3 CreateDevice) and then the MOUSE device it
 *      returns (slot 9 GetDeviceState); each gets a private copy of its vtable. It works on top of klauto.c's proxy objects too
 *      (the proxy's vtable pointer is swapped the same way; its functions are called through the copy). klrigid_di8(o) is
 *      called from DirectInput8Create after the real call (and after kla_di8 in a TEST build). The keyboard is never swapped.
 *      Put back: klrigid_tick() writes the stock vtable pointer back into every object that still shows our copy when the
 *      module switches itself off (a fault in the filter, or Enable cleared); the device normally lives until exit.
 *   3. REMOTE SHAPING (klrigid_remote_cap / klrigid_follow). klnetsmooth.c (receiver-side, remote ZFFPlayer) already does: a
 *      flat MaxTurnDegPerSec cap, a critically damped spring (SmoothMs) and a position snap. It does NOT do: an
 *      ERROR-DEPENDENT cap (PD2's curve), or a body-follows-look deadband (turn-in-place threshold). Those two are provided
 *      here as PURE functions with no game access, so the owner of klnetsmooth.c can call them (re\rigid_feel.md 4 has the exact
 *      two-line change). Nothing in this file touches a remote player by itself.
 *
 * KLHook.ini
 *   [Rigid]
 *   Enable=0            1 = on (offline and online: it changes only what THIS machine's mouse sends to ITS camera)
 *   YawMaxDps=300       top turn speed of the mouse yaw, degrees/s; 0 = no cap
 *   YawMinDps=60        speed allowed for a tiny pending turn (PD2: 40); with CurveFullDeg=0 the cap is flat YawMaxDps
 *   CurveFullDeg=90     pending turn at which the cap reaches YawMaxDps; 0 = flat cap
 *   YawSmoothMs=40      low-pass time constant of the yaw (0 = none)
 *   PitchMaxDps=0       same for pitch (lY); 0 = none (default: aim height stays direct)
 *   PitchSmoothMs=0
 *   YawMul=1.0 PitchMul=1.0   plain sensitivity factors (applied first)
 *   BacklogSec=0.30     most pending turn kept, in seconds at the top rate (older counts are dropped)
 *   DegPerCount=0.17    degrees of turn per mouse count (only for the caps)
 *   AimExempt=1         bypass while aiming ([cam+0x640], ASSUMPTION)
 *   AimByte=0x640       offset of that byte in the camera
 *   Log=0               1 = a line when the filter engages, on aim changes, and a 10 s summary
 *   Remote=0            1 = klrigid_remote_cap() answers PD2's curve instead of the caller's flat cap (works without Enable=1)
 *   RemoteMaxDps=300  RemoteMinDps=40  RemoteFullDeg=90
 *   RemoteTurnInPlace=0 1 = klrigid_follow() holds the body until the look is TurnStartDeg away (EXPERIMENT, see the .md)
 *   TurnStartDeg=65  TurnStopDeg=6  TwistMaxDeg=70  LegDps=120
 *
 * Wiring (klhook.c, NEW lines only):
 *   #include "klrigid.c"            above  #include "klnetsmooth.c"   (anywhere after klcam.c; before klnetsmooth.c if it calls the helpers)
 *   klrigid_init();                 below  klnetsmooth_init();
 *   klrigid_tick(game_thread);      below  klnetsmooth_tick(game_thread);
 *   in DirectInput8Create, after the real call (after kla_di8):   if (SUCCEEDED(hr)) klrigid_di8(o);
 */
#ifndef KLRIGID_C
#define KLRIGID_C

#include <math.h>

#define KRG_PLAYER_VT 0x00bb45f4u
#define KRG_NPL       28
#define KRG_NDEV      4
#define KRG_DEVSLOTS  32
#define KRG_DISLOTS   11

struct krg_axis { float maxdps, mindps, full, tau, mul; };
static struct {
    int on, log, aimex, rem, remturn; DWORD aimoff;
    struct krg_axis yaw, pit;
    float backlog, dpc, full;
    float remmax, remmin, remfull, tstart, tstop, twist, leg;
} krg;

static struct { float pend, frac; } krg_ax[2];
static LARGE_INTEGER krg_t; static int krg_have, krg_aim_prev = -1;
static LONG krg_n_frames, krg_n_active, krg_n_bypass, krg_n_aim, krg_n_clamped; static DWORD krg_sum_t;

typedef HRESULT (WINAPI *krg_create_fn)(void *self, const GUID *g, void **out, void *outer);
typedef HRESULT (WINAPI *krg_state_fn)(void *self, DWORD cb, BYTE *data);

static struct { DWORD obj, orig_vt, orig_fn; DWORD vt[KRG_DISLOTS]; } krg_di[KRG_NDEV];
static struct { DWORD obj, orig_vt, orig_fn; DWORD vt[KRG_DEVSLOTS]; } krg_dev[KRG_NDEV];

/* ---------------------------------------------------------------- the maths (no game access) */

static float krg_clampf(float v, float lo, float hi) { return v < lo ? lo : v > hi ? hi : v; }

/* PD2's husk look limiter: speed allowed for an error of err_deg, degrees per second */
static float krg_curve_dps(float err_deg, float lo, float hi, float full)
{
    float rel;
    if (full <= 0.0f || hi <= lo) return hi;
    rel = sqrtf(krg_clampf(fabsf(err_deg) / full, 0.0f, 1.0f));
    return lo + (hi - lo) * rel;
}

/* one axis: counts in (relative, signed), whole counts out. *pend = backlog in counts, *frac = rounding remainder. */
static int krg_step(const struct krg_axis *a, float *pend, float *frac, int in, float dt)
{
    float p = *pend + (float)in * a->mul, out = p, tot, whole;
    if (a->maxdps > 0.0f || a->tau > 0.0f) {
        if (a->tau > 0.0f) out = p * (1.0f - expf(-dt / a->tau));
        if (a->maxdps > 0.0f) {
            float rate = krg_curve_dps(fabsf(p) * krg.dpc, a->mindps, a->maxdps, krg.full);   /* deg/s for this pending turn */
            float cap = rate / krg.dpc * dt;                                                   /* counts allowed this frame */
            if (out > cap) out = cap; else if (out < -cap) out = -cap;
        }
        p -= out;
        if (a->maxdps > 0.0f) {                                                                /* drop what no one will wait for */
            float lim = a->maxdps / krg.dpc * krg.backlog;
            if (p > lim) { p = lim; krg_n_clamped++; } else if (p < -lim) { p = -lim; krg_n_clamped++; }
        }
        if (fabsf(p) < 0.01f) p = 0.0f;
    } else p = 0.0f;
    *pend = p;
    tot = out + *frac; whole = (float)(int)tot; *frac = tot - whole;
    return (int)whole;
}

/* ---------------------------------------------------------------- game side (reads only) */

static DWORD krg_player(DWORD *camout)
{   /* the local ZFFPlayer P = [gd + 0x828 + 4 * byte [gd + 0x898]] (klcam.c) -> 0 when none, or when the pause / cut flag is set */
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(0x00dd265cu)), pl; BYTE idx = 0xff;
    if (!gd || !klh_rd(gd + 0x898, &idx, 1) || idx >= KRG_NPL) return 0;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_rd32(pl) != (DWORD)(DWORD_PTR)KLH_VA(KRG_PLAYER_VT)) return 0;
    if (klh_rd32(gd + 0x4cd8) & 0xff) return 0;                  /* the pause / cut flag (ASSUMPTION, as klcam.c) */
    *camout = klh_rd32(pl + 0xbd8);
    return pl;
}

static void krg_reset(void) { krg_ax[0].pend = krg_ax[0].frac = krg_ax[1].pend = krg_ax[1].frac = 0.0f; krg_have = 0; }

/* the filter on one DIMOUSESTATE2 (cb >= 8 bytes: lX lY) */
static void krg_filter(LONG *xy)
{
    LARGE_INTEGER now, fq; float dt; DWORD cam = 0, pl; int aim = 0;
    QueryPerformanceCounter(&now); QueryPerformanceFrequency(&fq);
    krg_n_frames++;
    if (krg_have) {
        dt = (float)(now.QuadPart - krg_t.QuadPart) / (float)fq.QuadPart;
        if (dt > 0.25f || dt < 0.0f) { krg_reset(); dt = 0.0f; }
    } else dt = 0.0f;
    krg_t = now;
    if (!(pl = krg_player(&cam))) { krg_reset(); krg_n_bypass++; return; }           /* menu / no round: hands off */
    if (cam && krg.aimex) { BYTE b = 0; if (klh_rd(cam + krg.aimoff, &b, 1)) aim = b != 0; }
    if (krg.log && aim != krg_aim_prev) { klog("rigid: aim byte [cam+0x%lx] = %d (filter %s)", krg.aimoff, aim, aim ? "bypassed" : "active"); krg_aim_prev = aim; }
    if (!krg_have || dt < 0.0005f) { krg_have = 1; return; }                          /* first frame of a stretch / a double call: pass the counts untouched */
    if (aim) {                                                                       /* pay the backlog out at once, then plain counts */
        int i; for (i = 0; i < 2; i++) { xy[i] += (LONG)krg_ax[i].pend; krg_ax[i].pend = 0.0f; }
        krg_n_aim++; return;
    }
    krg_n_active++;
    xy[0] = krg_step(&krg.yaw, &krg_ax[0].pend, &krg_ax[0].frac, xy[0], dt);
    xy[1] = krg_step(&krg.pit, &krg_ax[1].pend, &krg_ax[1].frac, xy[1], dt);
}

/* ---------------------------------------------------------------- the DirectInput hook (heap vtable pointers) */

static int krg_ptr_set(DWORD obj, DWORD val, const char *what)
{   /* the first dword of a dinput8 / proxy heap object is its vtable pointer */
    return klh_data((void *)(DWORD_PTR)obj, &val, 4, what);
}

/* A slot is LIVE only while its object still shows our private vtable. A freed object whose heap address was reused (the game may
   recreate its mouse device) leaves a stale entry; without this test a new device at the same address would count as "already
   wrapped" and stay unfiltered, and stale entries would fill the table. */
static int krg_dev_live(int i) { return krg_dev[i].obj && klh_rd32(krg_dev[i].obj) == (DWORD)(DWORD_PTR)krg_dev[i].vt; }
static int krg_di_live(int i) { return krg_di[i].obj && klh_rd32(krg_di[i].obj) == (DWORD)(DWORD_PTR)krg_di[i].vt; }
static int krg_dev_index(void *self) { int i; for (i = 0; i < KRG_NDEV; i++) if (krg_dev[i].obj == (DWORD)(DWORD_PTR)self) return i; return -1; }
static int krg_di_index(void *self) { int i; for (i = 0; i < KRG_NDEV; i++) if (krg_di[i].obj == (DWORD)(DWORD_PTR)self) return i; return -1; }
static int krg_dev_free(void) { int i; for (i = 0; i < KRG_NDEV; i++) if (!krg_dev[i].obj || !krg_dev_live(i)) return i; return -1; }
static int krg_di_free(void) { int i; for (i = 0; i < KRG_NDEV; i++) if (!krg_di[i].obj || !krg_di_live(i)) return i; return -1; }

static HRESULT WINAPI krg_getstate(void *self, DWORD cb, BYTE *data)
{
    int i = krg_dev_index(self); HRESULT hr;
    if (i < 0) {   /* only registered devices carry our table; if it ever happens, pass through via the stock slot (an object's own orig_vt) */
        DWORD ovt = 0; int k; for (k = 0; k < KRG_NDEV; k++) if (krg_dev[k].orig_fn && klh_rd32((DWORD_PTR)self) == (DWORD)(DWORD_PTR)krg_dev[k].vt) { ovt = krg_dev[k].orig_fn; break; }
        return ovt ? ((krg_state_fn)(DWORD_PTR)ovt)(self, cb, data) : E_FAIL;
    }
    hr = ((krg_state_fn)(DWORD_PTR)krg_dev[i].orig_fn)(self, cb, data);
    if (SUCCEEDED(hr) && krg.on && data && cb >= 8 && !IsBadWritePtr(data, 8)) {
        __try { krg_filter((LONG *)data); }
        __except (EXCEPTION_EXECUTE_HANDLER) { krg.on = 0; krg_reset(); klog("rigid: fault in the mouse filter: input filter off"); }
    }
    return hr;
}

static const GUID krg_sysmouse = { 0x6f1d2b60, 0xd5a0, 0x11cf, { 0xbf, 0xc7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00 } };

static void krg_wrap_device(void *dev)
{
    DWORD obj = (DWORD)(DWORD_PTR)dev, vt; int i;
    if (!dev) return;
    if ((i = krg_dev_index(dev)) >= 0 && krg_dev_live(i)) return;             /* already ours */
    if ((i = krg_dev_index(dev)) < 0 && (i = krg_dev_free()) < 0) return;      /* (a stale entry for this address is simply reused) */
    krg_dev[i].obj = 0;
    vt = klh_rd32(obj);
    if (!vt || !klh_rd(vt, krg_dev[i].vt, sizeof krg_dev[i].vt)) return;
    krg_dev[i].orig_vt = vt; krg_dev[i].orig_fn = krg_dev[i].vt[9];
    if (!krg_dev[i].orig_fn) return;
    krg_dev[i].vt[9] = (DWORD)(DWORD_PTR)krg_getstate;
    krg_dev[i].obj = obj;                                                        /* registered BEFORE the pointer swap: another thread may call at once */
    if (krg_ptr_set(obj, (DWORD)(DWORD_PTR)krg_dev[i].vt, "mouse device vtable pointer (private copy)"))
        klog("rigid: mouse device %08lx: GetDeviceState wrapped (stock slot 9 = %08lx)", obj, krg_dev[i].orig_fn);
    else krg_dev[i].obj = 0;
}

static HRESULT WINAPI krg_create(void *self, const GUID *g, void **out, void *outer)
{
    int i = krg_di_index(self); HRESULT hr;
    if (i < 0) return E_FAIL;
    hr = ((krg_create_fn)(DWORD_PTR)krg_di[i].orig_fn)(self, g, out, outer);
    if (SUCCEEDED(hr) && krg.on && out && *out && !outer && g && !memcmp(g, &krg_sysmouse, sizeof krg_sysmouse)) krg_wrap_device(*out);
    return hr;
}

/* DirectInput8Create hook point: o = the IDirectInput8 the game gets (or klauto.c's proxy of it) */
static void klrigid_di8(void **o)
{
    DWORD obj, vt; int i;
    if (!krg.on || !o || !*o) return;
    obj = (DWORD)(DWORD_PTR)*o;
    if ((i = krg_di_index(*o)) >= 0 && krg_di_live(i)) return;
    if (i < 0 && (i = krg_di_free()) < 0) return;
    krg_di[i].obj = 0;
    vt = klh_rd32(obj);
    if (!vt || !klh_rd(vt, krg_di[i].vt, sizeof krg_di[i].vt)) return;
    krg_di[i].orig_vt = vt; krg_di[i].orig_fn = krg_di[i].vt[3];
    if (!krg_di[i].orig_fn) return;
    krg_di[i].vt[3] = (DWORD)(DWORD_PTR)krg_create;
    krg_di[i].obj = obj;
    if (krg_ptr_set(obj, (DWORD)(DWORD_PTR)krg_di[i].vt, "IDirectInput8 vtable pointer (private copy)"))
        klog("rigid: IDirectInput8 %08lx: CreateDevice wrapped (the mouse device only is wrapped further)", obj);
    else krg_di[i].obj = 0;
}

/* ---------------------------------------------------------------- remote shaping (pure; called by klnetsmooth.c if wired) */

/* The highest turn speed (rad/s) to show for a remote body whose displayed heading is err_rad away from the received one.
   Remote=0: returns the caller's own flat cap unchanged. */
static float klrigid_remote_cap(float err_rad, float fallback_rad_s)
{
    if (!krg.rem) return fallback_rad_s;
    return krg_curve_dps(fabsf(err_rad) * 57.2957795f, krg.remmin, krg.remmax, krg.remfull) * 0.0174532925f;
}

/* PD2 husk legs (re/pd2_netfeel.md 3): the body (legs) holds still while the look is within TurnStartDeg of it, then turns toward
   the look at LegDps until the gap is under TurnStopDeg; the gap never exceeds TwistMaxDeg. *turning is the caller's state.
   RemoteTurnInPlace=0: returns the look unchanged (the body IS the look). All angles radians, shortest arc. */
static float krg_wrap(float a) { while (a > 3.14159265f) a -= 6.2831853f; while (a < -3.14159265f) a += 6.2831853f; return a; }
static float klrigid_follow(float body, int *turning, float look, float dt)
{
    float gap, ag, step, tmax;
    if (!krg.remturn) return look;
    gap = krg_wrap(look - body); ag = fabsf(gap);
    if (!*turning && ag > krg.tstart * 0.0174532925f) *turning = 1;
    if (*turning && ag < krg.tstop * 0.0174532925f) *turning = 0;
    if (*turning) { step = krg.leg * 0.0174532925f * dt; if (step > ag) step = ag; body = krg_wrap(body + (gap > 0 ? step : -step)); }
    tmax = krg.twist * 0.0174532925f; gap = krg_wrap(look - body);
    if (gap > tmax) body = krg_wrap(look - tmax); else if (gap < -tmax) body = krg_wrap(look + tmax);
    return body;
}

/* ---------------------------------------------------------------- put-back, tick, init */

static void krg_restore_all(const char *why)
{
    int i, n = 0;
    for (i = 0; i < KRG_NDEV; i++) {
        /* the entry is kept unless the stock pointer went back (or the object no longer shows our copy: freed / re-pointed), so a
           call that still reaches our private table can always find its stock function (a lost entry would make it fail). */
        if (krg_dev[i].obj) {
            if (!krg_dev_live(i)) krg_dev[i].obj = 0;
            else if (krg_ptr_set(krg_dev[i].obj, krg_dev[i].orig_vt, "mouse device vtable pointer (restore)")) { n++; krg_dev[i].obj = 0; }
        }
        if (krg_di[i].obj) {
            if (!krg_di_live(i)) krg_di[i].obj = 0;
            else if (krg_ptr_set(krg_di[i].obj, krg_di[i].orig_vt, "IDirectInput8 vtable pointer (restore)")) { n++; krg_di[i].obj = 0; }
        }
    }
    if (n) klog("rigid: %d DirectInput object(s) given back their stock vtable (%s)", n, why);
}

static void klrigid_tick(int game_thread)
{
    static DWORD last; static int was_on; DWORD now = GetTickCount();
    if (!game_thread || now - last < 1000) return;
    last = now;
    if (krg.on) was_on = 1;
    else if (was_on) { was_on = 0; krg_restore_all("filter off"); return; }
    if (!krg.on || !krg.log) return;
    if (!krg_sum_t) krg_sum_t = now;
    if (now - krg_sum_t >= 10000) {
        krg_sum_t = now;
        klog("rigid: 10 s: frames %ld active %ld aim-bypass %ld menu/none-bypass %ld backlog-clamped %ld | pending yaw %.1f pitch %.1f counts",
             krg_n_frames, krg_n_active, krg_n_aim, krg_n_bypass, krg_n_clamped, krg_ax[0].pend, krg_ax[1].pend);
        krg_n_frames = krg_n_active = krg_n_aim = krg_n_bypass = krg_n_clamped = 0;
    }
}

static float krg_f(const char *key, const char *def, float lo, float hi)
{
    char b[32]; float v;
    GetPrivateProfileStringA("Rigid", key, def, b, sizeof b, klh_ini); v = (float)atof(b);
    if (!(v >= lo && v <= hi)) { klog("rigid: [Rigid] %s=%s outside %.2f .. %.2f: default %s used", key, b, lo, hi, def); v = (float)atof(def); }
    return v;
}

static void klrigid_init(void)
{
    char b[32];
    /* the remote shaping keys stand on their own (3f, 2026-10-20): Remote=1 must not need the local mouse filter (Enable) */
    krg.rem = GetPrivateProfileIntA("Rigid", "Remote", 0, klh_ini) != 0;
    krg.remmax = krg_f("RemoteMaxDps", "300", 30, 3600); krg.remmin = krg_f("RemoteMinDps", "40", 1, 3600); krg.remfull = krg_f("RemoteFullDeg", "90", 0, 720);
    krg.remturn = GetPrivateProfileIntA("Rigid", "RemoteTurnInPlace", 0, klh_ini) != 0;
    krg.tstart = krg_f("TurnStartDeg", "65", 10, 170); krg.tstop = krg_f("TurnStopDeg", "6", 1, 60);
    krg.twist = krg_f("TwistMaxDeg", "70", 20, 170); krg.leg = krg_f("LegDps", "120", 20, 1000);
    if ((krg.rem || krg.remturn) && !GetPrivateProfileIntA("Rigid", "Enable", 0, klh_ini))
        klog("rigid: remote shaping only (mouse filter off): Remote=%d %.0f..%.0f deg/s full at %.0f deg, turn-in-place %d; used by [NetSmooth]", krg.rem, krg.remmin, krg.remmax, krg.remfull, krg.remturn);
    krg.on = GetPrivateProfileIntA("Rigid", "Enable", 0, klh_ini) != 0;
    if (!krg.on) return;
    krg.log = GetPrivateProfileIntA("Rigid", "Log", 0, klh_ini) != 0;
    krg.aimex = GetPrivateProfileIntA("Rigid", "AimExempt", 1, klh_ini) != 0;
    GetPrivateProfileStringA("Rigid", "AimByte", "0x640", b, sizeof b, klh_ini); krg.aimoff = strtoul(b, 0, 16); if (krg.aimoff > 0x2000) krg.aimoff = 0x640;
    krg.yaw.maxdps = krg_f("YawMaxDps", "300", 0, 3600);   krg.yaw.mindps = krg_f("YawMinDps", "60", 1, 3600);
    krg.yaw.tau = krg_f("YawSmoothMs", "40", 0, 1000) / 1000.0f;   krg.yaw.mul = krg_f("YawMul", "1.0", 0.05f, 5);
    krg.pit.maxdps = krg_f("PitchMaxDps", "0", 0, 3600);   krg.pit.mindps = krg.yaw.mindps < krg.pit.maxdps ? krg.yaw.mindps : krg.pit.maxdps;
    krg.pit.tau = krg_f("PitchSmoothMs", "0", 0, 1000) / 1000.0f;  krg.pit.mul = krg_f("PitchMul", "1.0", 0.05f, 5);
    krg.full = krg_f("CurveFullDeg", "90", 0, 720);
    krg.backlog = krg_f("BacklogSec", "0.30", 0.05f, 3);
    krg.dpc = krg_f("DegPerCount", "0.17", 0.005f, 5);
    klog("rigid: on; yaw max %.0f deg/s (min %.0f, full at %.0f deg, smooth %.0f ms, mul %.2f), pitch max %.0f (smooth %.0f ms, mul %.2f), backlog %.2f s, %.3f deg/count, aim exempt %d byte +0x%lx, remote %d turn-in-place %d, Log=%d; mouse yaw/pitch counts only, EXPERIMENT (never run): re/rigid_feel.md",
         krg.yaw.maxdps, krg.yaw.mindps, krg.full, krg.yaw.tau * 1000.0f, krg.yaw.mul, krg.pit.maxdps, krg.pit.tau * 1000.0f, krg.pit.mul, krg.backlog, krg.dpc, krg.aimex, krg.aimoff, krg.rem, krg.remturn, krg.log);
}

#endif /* KLRIGID_C */

