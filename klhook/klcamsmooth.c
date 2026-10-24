/*
 * klcamsmooth.c - [CamSmooth]: the third-person camera during animations and aim transitions. NOTHING HERE HAS RUN IN THE GAME.
 * Owner 2026-10-24: "the actual camera just feels janky with animations, it needs to feel more smoothened out", and
 * "coming out of aiming ... it comes back naturally, no snapping of the camera at all". He plays uncapped at 150 .. 240 fps
 * with uneven frame times (KLHook.log: dt 0.0049 / 0.0059 / 0.0146 / 0.0225 in consecutive logged frames).
 * Part of KLHook: included by klhook.c AFTER klcam.c (uses klcam_player, klcam_v3, klcam_nodepos, klcam_eye_body / struct klcam_eye,
 * klcam_chasers, klfc_guard, klfc_f). Runs on the game thread at the same site as klcam_tick (return address 0x87aa82, after the
 * camera tick, before the render: ASSUMPTION, the same one klcam's Recover makes).
 *
 * WHAT IS WRONG (evidence in the owner's KLHook.log, read-only)
 *  1. The six camera chasers (cam+0x658, 0x68c, 0x6c0, 0x6f4, 0x728, 0x75c) integrate in substeps of h = [chaser+0x30] and run
 *     trunc(dt / h) substeps clamped to 1..10 (READ 0x5a3150, re\camera.md). The log line "UnstickFilter: substep h of the 6 chasers
 *     reads 0.0150" shows h = 0.015 in his build (the design notes assumed 0.005). With h = 0.015 every frame shorter than 30 ms runs
 *     exactly ONE substep = a fixed 15 ms of camera time whatever the frame lasted: at 200 fps the camera runs 3x too fast, and with
 *     dt jumping 5 / 6 / 15 / 22 ms (his log) the camera's advance per frame does not follow the frame time, so its motion judders;
 *     frames of 30 ms and up jump to 2 substeps (a step in speed). The log shows it: eye step per 50 ms is smooth but the per-frame
 *     speed (vE) reads 46 .. 254 cm/s on the same smooth glide. DtFix sets h to the smoothed frame time each frame, so one substep
 *     = one frame of real time (dt-correct, alpha = 1 - (1-a)^(dt / h) for the chaser's own per-step constant).
 *     GUESS: that one substep advances the chaser by h seconds and that the chaser's coefficients do not cache h (the same GUESS klcam's
 *     UnstickFilter makes). Untested: this changes how fast the camera follows at his frame rates (3x slower at 200 fps than now).
 *  2. The pivot (cam+0x398) sits on an animated point (feet + 145 cm standing); crouch, cover, vault and hit animations move it in
 *     steps. PivotMs low-passes ONLY the pivot's offset from the feet (q = pivot - feet), so running does not lag (feet are physics, not
 *     filtered) and the mouse orbit (eye - pivot) is untouched.
 *  3. Aim in / aim out (and cover / shoulder mode switches) change the eye's distance + height from the pivot and the FOV in one frame
 *     or in the game's coarse steps. Jump detector: the new pose (horizontal distance h, height y of eye over pivot, FOV) is compared
 *     with the prediction from last frame + its velocity; a residual above JumpCm / JumpFov starts a TAKEOVER: the displayed pose D
 *     = raw R + e where e = (last displayed pose + displayed velocity * dt) - R, with the velocity continuity e' = dD - dR, then e decays
 *     as an exact critically damped spring (no start or stop jerk) over AimOutMs (FOV getting wider / eye farther = aim out),
 *     AimInMs (narrower = aim in, short) or BlendMs (other mode switches). The mouse is never filtered: the yaw direction of the eye
 *     around the pivot is taken from the raw eye every frame, only h, y and the FOV carry the decaying difference.
 *     NOT SMOOTHED (limit of the method, GUESS that it matters): a sideways shoulder shift is a yaw change of the raw eye and passes
 *     as it is, because it cannot be told from mouse yaw without the camera's orientation (not found).
 *
 * HOW IT WRITES: the eye through the engine's node setter 0x7c9030 (thiscall(cam, float[3]), as klcam's Recover: prologue
 * 51 8B 54 24 08 checked; the node position must equal cam+0x508 to 0.5 cm before each use, three strikes switch the feature off);
 * the FOV with klh_data at node+0x70 ([[cam+0x24]+0x70], where klcam reads it: GUESS that this is the value the render uses and that
 * the engine recomputes it each tick instead of integrating our write back); the chaser h with klh_data (heap).
 * Dry=1: everything is computed and logged, nothing is written (the eye, the FOV, the h).
 *
 * LOG (Log=1, lines "camsm:"): trigger lines with the jump and the time constant; during an aim / mode takeover (and 1 s after) one
 * line per frame: dt, raw eye step, DISPLAYED eye step (cm), raw and displayed FOV step, the open e; a summary when it ends with the
 * largest displayed step against the raw jump (the proof there was no snap: displayed step stays near the raw glide).
 *
 * STANCE (added 2026-10-24, owner: "one second he's crouched, next frame he's straight running, no anim, no camera smoothing").
 *  What the stages above MISSED: (a) the pose detector looks at the eye over the pivot (h, y). On a stance change the eye moves WITH the
 *  pivot in the same frame (owner log: pivot offset from the feet 160 -> 145 / 130 / 110 cm, eye height follows 1:1, steps of 15 .. 55 cm
 *  between 20 Hz log lines), so the eye-over-pivot residual stays ~0 and nothing triggers. (b) PivotMs=60 only low-passes the pivot: a
 *  critically damped 60 ms settle moves 15 .. 55 cm in about 12 frames at 200 fps, peak speed ~ 0.37 * w * step = 550 .. 2000 cm/s;
 *  it still reads as a snap. Fix: StanceMs, a last stage. A pivot-offset step above StanceCm in one frame (mouse never moves it) snaps
 *  the pivot follower to the new pivot and opens a velocity-continuous critically damped takeover on the shown eye relative to the
 *  FEET (so running does not lag), decaying over StanceMs. STANCE FLAG not found: the pivot-height step is the detector (GUESS).
 *  Limit: the takeover offset is a world translation, so a mouse turn during its 280 ms is not filtered but is added to a decaying offset.
 *  ini: StanceMs=280 (0 = off), StanceCm=6. Offline check: tools/sim_camsmooth.py.
 *
 * K37 FIXES (owner log 2026-10-24 19:2x - 19:3x, hook k36, the smoother itself caused jumps; tools/sim_camsmooth.py replays them):
 *  a) STANCE measured the pivot offset from the feet as a WORLD vector; the ~30 cm horizontal part rotates with the player, so a fast turn read
 *     as a 43 / 86 / 100 / 133 cm 'pop' and the takeover dragged the camera. Now (horizontal length, height): a turn changes neither. The
 *     pivot follower works in the same coordinates (direction from the raw pivot each frame, so a turn is never lagged).
 *  b) Rv (raw pose velocity) absorbed the jump itself on the trigger frame (70 cm / 10 ms = -7000 cm/s), so a second trigger 4 ms later seeded
 *     ev = +7000 and the offset GREW 70 -> 163 cm (raw 1.13 cm -> shown 60.86 cm). Rv is now frozen on a jump frame, and an initial
 *     velocity that would grow the offset is zeroed (pose and stance takeovers).
 *  c) The takeover was seeded with the displayed eye height OVER THE PIVOT, so a pivot step with the eye staying moved the shown eye with
 *     the pivot (raw 0.72 -> shown 12.24 cm). It is now seeded from the last shown eye in the WORLD (pre-stance, so no stacking with the
 *     stance offset), expressed over the new followed pivot.
 *  d) Hard limit kcs_clamp: the shown eye never moves more than (raw eye step + max(0.8 cm, 300 cm/s * dt)) per frame, whatever else is wrong.
 *
 * K39 (2026-10-25, owner: "if u crouch then crouch again it cancels the animation ... the camera doesnt keep its consistentness"; k37 log 19:52:59;
 *  tools/sim_camsmooth.py section 3 replays it). NOT RUN IN THE GAME.
 *  a) stance detector is ramp-aware: the pop residual is the SMALLER of (old 0.5-smoothed velocity prediction, 3-frame trend prediction), so a smooth
 *     357 -> 161 cm descent is no pop.
 *  b) outlier guard: a residual above 25 cm is HELD for up to 2 frames (the followed pivot offset stays at the pre-jump trend, the eye does not
 *     follow the jump); if the raw offset comes back it was a one-frame read outlier and is ignored ("OUTLIER ignored"), else it is confirmed as a pop.
 *  c) stance takeover MERGES: an open takeover keeps its velocity and just absorbs the new step (no re-seed from zero, no stacking).
 *  d) pose TRIGGER within 100 ms of the last one merges into the open e (e -= residual), ev kept.
 *  e) while kcs_stancefix_busy (klstancefix.c mirrors a re-toggled crouch clip) the stance limit is doubled and StanceMs x1.5.
 *  f) CLAMP logs "CLAMP hid X cm" when it hides more than 15 cm, so masking is visible.
 *  klstancefix.c is included from here (no change to klhook.c needed); its tick runs first thing in klcamsmooth_tick, its init in klcamsmooth_init.
 *
 * WIRING (klhook.c): #include "klcamsmooth.c" after klcam.c; klcamsmooth_tick(game_thread); after klcam_tick; klcamsmooth_init();
 * after klcam_init(). ini: [CamSmooth] Enable=1 PivotMs=60 BlendMs=250 AimOutMs=320 AimInMs=90 DtFix=1 Log=0 Dry=0 JumpCm=12 JumpFov=0.05 StanceMs=280 StanceCm=6
 */
#ifndef KLCAMSMOOTH_C
#define KLCAMSMOOTH_C

#define KCS_RCB_RA 0x0087aa82u
#define KCS_EYEFN  0x007c9030u

static int kcs_stancefix_busy;                       /* set by klstancefix.c while it mirrors a re-toggled crouch / stand clip */
static void klstancefix_tick(int game_thread);
static void klstancefix_init(void);

static struct {
    int enable, pivotms, blendms, aimoutms, aiminms, dtfix, log, dry, stancems;
    float jumpcm, jumpfov, stancecm;
    /* stance stage (StanceMs): last stage, works on the displayed eye relative to the FEET so running never lags */
    float qhprev, qyprev, qhpv, qypv; int qprev_ok;  /* raw pivot offset from the feet in PLAYER-INDEPENDENT coordinates (horizontal length qh, height qy: a turn rotates the horizontal offset but changes neither), last frame, and smooth velocity */
    float S[3], Sv[3]; int sact;                      /* open stance takeover: S = shown eye - input eye (feet-relative), decays critically damped */
    float Orel[3], Ov[3], Iprev[3], Iv[3]; int orel_ok, iprev_ok; /* last shown eye rel feet and its velocity; last input eye rel feet and its pre-step velocity */
    long nstance; float maxstep_s;
    /* k39: 3-frame trend history of the raw pivot offset, outlier hold, time base */
    float hqh[3], hqy[3], hdt[3]; int nhist; float lvh, lvy;   /* lv = velocity of the last accepted step (also a pop frame): a ramp that began with a pop continues as a ramp */
    int pend, pend_n; float pend_dt; double tnow, trigt; long noutlier, nmerge;
    /* per camera */
    DWORD cam; int have;                  /* have = previous frame state valid */
    long lastframe;
    double dtavg;
    float h_orig[6]; int h_ok[6], h_told;
    float R[3], Rv[3];                    /* raw pose (h, y, fov) and its velocity */
    float D[3], Dv[3];                    /* displayed pose and velocity */
    float e[3], ev[3], w[3]; int act;     /* open takeover: e = D - R, decay rate per channel (1/s) */
    float qhs, qys, qhv, qyv, qdir[2]; int qhave; /* pivot offset follower in (qh, qy); the direction of the horizontal offset is taken from the raw pivot each frame */
    long nclamp; int clampgate;
    float Eprev[3], Edisp[3], fovraw, fovdisp; int eprev_ok;
    int rc_checked, rc_on, strikes, fault;
    /* log */
    double logleft; int loglines; float maxdisp, maxraw, maxfdisp, maxfraw; long ntrig;
    char why[24];
} kcs;

static float kcs_ini_f(const char *key, float def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("CamSmooth", key, "", t, sizeof t, klh_ini);
    if (!t[0]) return def;
    v = (float)atof(t);
    if (!klcam_fin(v) || v < lo || v > hi) { klog("camsm: [CamSmooth] %s=%s out of range %.2f .. %.2f, %.2f used", key, t, lo, hi, def); return def; }
    return v;
}
static float kcs_len(const float *a, int n) { float s = 0; int i; for (i = 0; i < n; i++) s += a[i] * a[i]; return (float)sqrt(s); }

/* exact step of x'' = -2w x' - w^2 x (critically damped, x -> 0), position x and velocity v, over dt */
static void kcs_cd(float *x, float *v, float w, float dt)
{
    float a = *v + w * *x, ex = (float)exp(-w * dt);
    float nx = (*x + a * dt) * ex, nv = (*v - a * w * dt) * ex;
    *x = nx; *v = nv;
}

static void kcs_reset(void)
{
    kcs.have = 0; kcs.act = 0; kcs.qhave = 0; kcs.eprev_ok = 0; kcs.qprev_ok = 0; kcs.sact = 0; kcs.orel_ok = 0; kcs.iprev_ok = 0; kcs.qhv = kcs.qyv = 0; kcs.qhpv = kcs.qypv = 0;
    memset(kcs.S, 0, sizeof kcs.S); memset(kcs.Sv, 0, sizeof kcs.Sv); memset(kcs.Iv, 0, sizeof kcs.Iv); memset(kcs.Ov, 0, sizeof kcs.Ov);
    memset(kcs.e, 0, sizeof kcs.e); memset(kcs.ev, 0, sizeof kcs.ev); memset(kcs.Dv, 0, sizeof kcs.Dv); memset(kcs.Rv, 0, sizeof kcs.Rv);
    kcs.nhist = 0; kcs.pend = 0; kcs.pend_n = 0; kcs.pend_dt = 0; kcs.trigt = -10.0;
}

/* HARD LIMIT: the shown eye may move at most (raw eye step + a small easing budget) per frame. Whatever the takeovers compute (seeded
   wrongly, stacked, in the wrong frame), the displayed step can no longer exceed the raw step by more than the budget (owner log: raw 1.13 cm
   -> shown 60.86 cm; raw 0.7 -> shown 12.2). Budget = max(0.8 cm, 300 cm/s * dt). When it binds the shown eye trails the raw one and
   catches up at the budget rate. A raw step that is itself huge (cut / respawn) is allowed through: the takeover seeded in the world eases it. */
static void kcs_clamp(float *E2, const float *E, float dt)
{
    float st[3], sraw, lim, sl, bud = 300.0f * dt; int i;
    if (!kcs.eprev_ok) return;
    if (bud < 0.8f) bud = 0.8f;
    for (i = 0; i < 3; i++) st[i] = E2[i] - kcs.Edisp[i];
    sl = kcs_len(st, 3);
    sraw = klcam_dist(E, kcs.Eprev);
    lim = sraw + bud;
    if (sl > lim && sl > 1e-4f) {
        float k = lim / sl;
        for (i = 0; i < 3; i++) E2[i] = kcs.Edisp[i] + st[i] * k;
        kcs.nclamp++;
        if (kcs.log && kcs.nclamp < 200) klog("camsm: CLAMP: shown step %.2f cm > raw %.2f + budget, limited to %.2f cm", sl, sraw, lim);
        if (kcs.log && sl - lim > 15.0f) klog("camsm: CLAMP hid %.1f cm (shown step %.1f, raw %.1f): something upstream still steps the eye", sl - lim, sl, sraw);
    }
}

/* DtFix: h of the six chasers = the smoothed frame time, so one substep is one frame (see the header, point 1) */
static void kcs_dtfix(DWORD cam, double dtavg)
{
    int i; float hv = (float)dtavg;
    if (!kcs.dtfix) return;
    if (hv < 0.002f) hv = 0.002f; if (hv > 0.02f) hv = 0.02f;
    if (kc.h_boost) return;                                    /* klcam's low-fps raise owns h for now */
    for (i = 0; i < 6; i++) {
        DWORD at = cam + klcam_chasers[i] + 0x30; float cur = klfc_f(at);
        if (!kcs.h_told) { kcs.h_orig[i] = cur; kcs.h_ok[i] = klcam_fin(cur) && cur >= 0.0015f && cur <= 0.03f; }
        if (!kcs.h_ok[i]) continue;
        if (!klcam_fin(cur) || cur < 0.0015f || cur > 0.03f) continue;     /* not the substep any more: leave it alone */
        if (!kcs.dry && (cur > hv * 1.08f || cur < hv * 0.92f)) klh_data((void *)(DWORD_PTR)at, &hv, 4, "camera chaser substep (DtFix)");
    }
    if (!kcs.h_told) {
        kcs.h_told = 1;
        klog("camsm: DtFix: chaser substep h stock %.4f %.4f %.4f %.4f %.4f %.4f -> %.4f (frame time avg)%s", kcs.h_orig[0], kcs.h_orig[1], kcs.h_orig[2], kcs.h_orig[3], kcs.h_orig[4], kcs.h_orig[5], hv, kcs.dry ? " DRY" : "");
    }
}

static void klcamsmooth_tick(int game_thread)
{
    DWORD gd, P, cam, sys; float rawdt = 0, dt, E[3], Pv[3], feet[3], o[3], fov = 0, R[3], hv, q[3], Pv2[3], E2[3], f2, qh, qy; long frame; int i, trig = 0, jumped = 0;
    DWORD nd;
    klstancefix_tick(game_thread);                                  /* k39: mirrors a re-toggled crouch clip first (own ini switch, independent of CamSmooth) */
    if (!kcs.enable || !klh_exe_ok || !game_thread) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KCS_RCB_RA)) return;
    if (!(P = klcam_player(&gd))) { kcs_reset(); kcs.cam = 0; return; }
    if (!(cam = klh_rd32(P + 0xbd8)) || klh_rd32(klh_rd32(cam) - 4) != KLCAM_COL) { kcs_reset(); kcs.cam = 0; return; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)))) return;
    klh_rd(sys + 0x50, &rawdt, 4); frame = (long)klh_rd32(sys + 0x48);
    if (frame == kcs.lastframe) return;
    kcs.lastframe = frame;
    if (!klcam_fin(rawdt) || rawdt <= 0) return;
    dt = rawdt > 0.1f ? 0.1f : rawdt;
    kcs.tnow += dt;
    kcs.dtavg += ((rawdt > 0.05f ? 0.05f : rawdt) - kcs.dtavg) * 0.05;
    if (cam != kcs.cam) { kcs.cam = cam; kcs.h_told = 0; kcs.strikes = 0; kcs_reset(); kcs.dtavg = rawdt < 0.05f ? rawdt : 0.016; klog("camsm: camera %08lx (PivotMs %d BlendMs %d AimOutMs %d AimInMs %d DtFix %d%s)", (unsigned long)cam, kcs.pivotms, kcs.blendms, kcs.aimoutms, kcs.aiminms, kcs.dtfix, kcs.dry ? " DRY" : ""); }
    kcs_dtfix(cam, kcs.dtavg);
    if (rawdt >= 0.05f) { kcs_reset(); return; }                    /* a hitch / pause: no filtering across it */
    if (klh_rd32(gd + 0x4cd8)) { kcs_reset(); return; }             /* ASSUMPTION (klcam.c): the pause / cut flag */
    if (!klcam_v3(cam + 0x508, E) || !klcam_v3(cam + 0x398, Pv) || !klcam_v3(P + 0x460, feet)) { kcs_reset(); return; }
    nd = klh_rd32(cam + 0x24); if (nd) klh_rd(nd + 0x70, &fov, 4);
    if (!nd || !klcam_fin(fov) || fov <= 0.05f || fov > 3.0f) { kcs_reset(); return; }
    for (i = 0; i < 3; i++) { o[i] = E[i] - Pv[i]; q[i] = Pv[i] - feet[i]; }
    hv = (float)sqrt(o[0] * o[0] + o[2] * o[2]);
    if (hv < 5.0f || kcs_len(q, 3) > 400.0f) { kcs_reset(); return; }          /* straight above / below, or the pivot is not near the feet */
    R[0] = hv; R[1] = o[1]; R[2] = fov;
    qh = (float)sqrt(q[0] * q[0] + q[2] * q[2]); qy = q[1];

    /* ---- stance pop detector, FIRST (the pose takeover below needs the followed pivot Pv2).
       Measured in (qh, qy) = horizontal LENGTH and height of the pivot offset from the feet, NOT as a world vector: the ~30 cm horizontal
       offset (shoulder / aim offset) ROTATES with the player, so a fast turn changed the world vector by up to 43 cm in one frame and read
       as a stance pop (owner log 19:23:10 'q -21.2 141.1 1.9 <- -1.8 141.1 -19.9'). A turn changes neither qh nor qy. */
    {
        int pop = 0, held = 0; float qlim = kcs.stancecm * (kcs_stancefix_busy ? 2.0f : 1.0f);
        float qh_raw = qh;                                                    /* the horizontal direction below comes from the RAW offset */
        if (kcs.stancems >= 20 && kcs.qprev_ok) {
            /* k39: the residual is the SMALLER of two predictions from the past (a ramp is no pop): (1) last value + smoothed velocity, (2) last value +
               the average velocity of the last 3 accepted frames. adt = time since the last accepted frame (a held outlier frame does not advance it). */
            float adt = dt + kcs.pend_dt, ph, py, dh, dy, r, r2;
            dh = qh - (kcs.qhprev + kcs.qhpv * adt); dy = qy - (kcs.qyprev + kcs.qypv * adt); r = (float)sqrt(dh * dh + dy * dy);
            ph = kcs.qhprev; py = kcs.qyprev;
            if (kcs.nhist >= 3 && kcs.hdt[1] + kcs.hdt[2] > 1e-4f) {
                float tt = kcs.hdt[1] + kcs.hdt[2], vh = (kcs.hqh[2] - kcs.hqh[0]) / tt, vy = (kcs.hqy[2] - kcs.hqy[0]) / tt;
                ph = kcs.hqh[2] + vh * adt; py = kcs.hqy[2] + vy * adt;
                dh = qh - ph; dy = qy - py; r2 = (float)sqrt(dh * dh + dy * dy);
                if (r2 < r) r = r2;
            }
            {   /* third explanation: the last accepted step simply goes on (the 2nd frame of a ramp that began with a pop) */
                float r3h = qh - (kcs.qhprev + kcs.lvh * adt), r3y = qy - (kcs.qyprev + kcs.lvy * adt), r3 = (float)sqrt(r3h * r3h + r3y * r3y);
                if (r3 < r) r = r3;
            }
            if (kcs.pend) {
                if (r <= qlim * 1.5f) {                                       /* back on the trend: it was one bad read, not a stance change */
                    kcs.pend = 0; kcs.pend_dt = 0; kcs.noutlier++;
                    if (kcs.log) klog("camsm: OUTLIER ignored: pivot offset (length %.1f height %.1f) was off the trend by a one-frame excursion, now back (%.1f cm) | f %ld", qh, qy, r, frame);
                } else if (++kcs.pend_n >= 2) {
                    pop = 1; kcs.pend = 0; kcs.pend_dt = 0;
                    if (kcs.log) klog("camsm: STANCE pop (confirmed after %d held frames): pivot offset (length %.1f height %.1f) off the trend by %.1f cm | f %ld", kcs.pend_n, qh, qy, r, frame);
                } else held = 1;
            } else if (r > qlim) {
                if (r > 25.0f) {
                    kcs.pend = 1; kcs.pend_n = 0; held = 1;
                    if (kcs.log) klog("camsm: STANCE candidate %.1f cm (limit %.1f): pivot offset (length %.1f height %.1f), held up to 2 frames | f %ld dt %.4f", r, qlim, qh, qy, frame, rawdt);
                } else {
                    pop = 1;
                    if (kcs.log) klog("camsm: STANCE pop: pivot offset (length %.1f height %.1f) stepped %.1f cm (limit %.1f) in one frame, was (%.1f %.1f) | f %ld dt %.4f", qh, qy, r, qlim, kcs.qhprev, kcs.qyprev, frame, rawdt);
                }
            }
            if (held) { kcs.pend_dt += dt; qh = ph; qy = py; }                /* follower and eye keep the pre-jump trend while it is judged */
        }
        if (held) { /* nothing accepted: history, velocity and prev stay as they were */ }
        else {
            if (pop) {
                kcs.qhs = qh; kcs.qys = qy; kcs.qhv = kcs.qyv = 0; kcs.qhave = 1;     /* the stance stage eases it, not the 60 ms follower */
                kcs.qhpv = kcs.qypv = 0; kcs.nhist = 0;
            } else if (kcs.qprev_ok) { kcs.qhpv += ((qh - kcs.qhprev) / dt - kcs.qhpv) * 0.5f; kcs.qypv += ((qy - kcs.qyprev) / dt - kcs.qypv) * 0.5f; }
            if (kcs.qprev_ok) { kcs.lvh = (qh - kcs.qhprev) / dt; kcs.lvy = (qy - kcs.qyprev) / dt; } else kcs.lvh = kcs.lvy = 0.0f;
            kcs.qhprev = qh; kcs.qyprev = qy; kcs.qprev_ok = 1;
            if (kcs.nhist >= 3) { kcs.hqh[0] = kcs.hqh[1]; kcs.hqy[0] = kcs.hqy[1]; kcs.hdt[0] = kcs.hdt[1]; kcs.hqh[1] = kcs.hqh[2]; kcs.hqy[1] = kcs.hqy[2]; kcs.hdt[1] = kcs.hdt[2]; kcs.nhist = 2; }
            kcs.hqh[kcs.nhist] = qh; kcs.hqy[kcs.nhist] = qy; kcs.hdt[kcs.nhist] = dt; kcs.nhist++;
        }
        if (qh_raw > 0.5f) { kcs.qdir[0] = q[0] / qh_raw; kcs.qdir[1] = q[2] / qh_raw; }
        kcs.sact = kcs.sact | (pop << 1);                                     /* bit 1 = start a takeover below */
    }

    /* ---- pivot offset follower (animation bob / snaps), also in (qh, qy): the direction of the horizontal offset comes from the raw pivot
       every frame, so a turn is never lagged (the old world-vector follower lagged a rotating 30 cm offset by up to ~40 cm). */
    if (kcs.pivotms > 0) {
        float w = 6.0f / ((float)kcs.pivotms * 0.001f), xh, xy;
        if (!kcs.qhave || fabs(qh - kcs.qhs) > 200.0f || fabs(qy - kcs.qys) > 200.0f) { kcs.qhs = qh; kcs.qys = qy; kcs.qhv = kcs.qyv = 0; kcs.qhave = 1; }
        xh = kcs.qhs - qh; xy = kcs.qys - qy;
        kcs_cd(&xh, &kcs.qhv, w, dt); kcs_cd(&xy, &kcs.qyv, w, dt);
        kcs.qhs = qh + xh; kcs.qys = qy + xy;
        Pv2[0] = feet[0] + kcs.qdir[0] * kcs.qhs; Pv2[1] = feet[1] + kcs.qys; Pv2[2] = feet[2] + kcs.qdir[1] * kcs.qhs;
    } else memcpy(Pv2, Pv, 12);

    /* ---- pose takeover */
    if (kcs.have) {
        float pr[3], res[3];
        for (i = 0; i < 3; i++) { pr[i] = kcs.R[i] + kcs.Rv[i] * dt; res[i] = R[i] - pr[i]; }
        if (fabs(res[0]) > kcs.jumpcm || fabs(res[1]) > kcs.jumpcm || fabs(res[2]) > kcs.jumpfov) {
            float T; const char *why;
            jumped = 1;                                                       /* the raw velocity must not absorb this jump (see Rv below) */
            if (res[2] > 0.02f) { T = (float)kcs.aimoutms; why = "out"; }
            else if (res[2] < -0.02f) { T = (float)kcs.aiminms; why = "in"; }
            else { T = (float)kcs.blendms; why = "mode"; }
            if (T >= 20.0f) {
                float Dp[3]; int merge = kcs.act && kcs.tnow - kcs.trigt < 0.1;
                if (merge) {
                    /* k39: a second jump within 100 ms (owner log 19:52:59: TRIGGER, and 5 ms later another on top) is ADDED to the open offset: the shown
                       pose stays continuous (e -= residual), the velocity ev is kept, no fresh seed from the displayed eye, so takeovers never stack. */
                    for (i = 0; i < 3; i++) Dp[i] = R[i] + kcs.e[i] - res[i];
                    kcs.nmerge++;
                } else if (kcs.iprev_ok) {
                    /* CONTINUITY IN THE WORLD: the displayed (pre-stance) eye of last frame carried on by its velocity, expressed over the NEW followed
                       pivot. Seeding from the old displayed (h, y) alone moved the eye with the pivot: owner log 19:22:44 'raw jump y 12.3' was the
                       pivot stepping with the eye staying (raw eye step 0.7 cm), and the takeover then shifted the shown eye 12.2 cm in one frame. */
                    float Ep[3], rx, rz;
                    for (i = 0; i < 3; i++) Ep[i] = feet[i] + kcs.Iprev[i] + kcs.Iv[i] * dt;
                    rx = Ep[0] - Pv2[0]; rz = Ep[2] - Pv2[2];
                    Dp[0] = (float)sqrt(rx * rx + rz * rz); Dp[1] = Ep[1] - Pv2[1]; Dp[2] = kcs.D[2] + kcs.Dv[2] * dt;
                } else for (i = 0; i < 3; i++) Dp[i] = kcs.D[i] + kcs.Dv[i] * dt;
                for (i = 0; i < 3; i++) {
                    kcs.e[i] = Dp[i] - R[i];
                    if (!merge) kcs.ev[i] = kcs.Dv[i] - kcs.Rv[i];             /* Rv is the glide BEFORE the jump (not updated on a jump frame); a merge keeps the open ev */
                    if (kcs.ev[i] * kcs.e[i] > 0.0f) kcs.ev[i] = 0.0f;         /* never an initial velocity that grows the offset (a critically damped spring would overshoot to e + ev/w) */
                    kcs.w[i] = 6.0f / (T * 0.001f);
                }
                if (fabs(kcs.e[0]) > 400 || fabs(kcs.e[1]) > 400) { memset(kcs.e, 0, sizeof kcs.e); memset(kcs.ev, 0, sizeof kcs.ev); }
                if (fabs(kcs.e[2]) > 1.5f) { kcs.e[2] = 0; kcs.ev[2] = 0; }
                kcs.act = 1; trig = 1; kcs.ntrig++; kcs.trigt = kcs.tnow;
                if (merge && kcs.log) klog("camsm: TRIGGER merged into the open takeover (second jump within 100 ms)");
                kcs.logleft = T * 0.001 + 1.0; kcs.loglines = 0; kcs.maxdisp = kcs.maxraw = kcs.maxfdisp = kcs.maxfraw = 0;
                strncpy(kcs.why, why, sizeof kcs.why - 1);
                if (kcs.log) klog("camsm: TRIGGER %s: raw jump h %.1f y %.1f fov %.3f (predicted from last frame), takeover e h %.1f y %.1f fov %.3f over %.0f ms | f %ld dt %.4f", why, res[0], res[1], res[2], kcs.e[0], kcs.e[1], kcs.e[2], T, frame, rawdt);
            }
        }
    }
    if (kcs.act && !trig) {
        for (i = 0; i < 3; i++) kcs_cd(&kcs.e[i], &kcs.ev[i], kcs.w[i], dt);
        if (fabs(kcs.e[0]) < 0.05f && fabs(kcs.e[1]) < 0.05f && fabs(kcs.e[2]) < 0.0003f && fabs(kcs.ev[0]) < 1.0f && fabs(kcs.ev[1]) < 1.0f && fabs(kcs.ev[2]) < 0.005f) {
            memset(kcs.e, 0, sizeof kcs.e); memset(kcs.ev, 0, sizeof kcs.ev); kcs.act = 0;
        }
    }
    {
        float Dn[3];
        for (i = 0; i < 3; i++) Dn[i] = R[i] + (kcs.act ? kcs.e[i] : 0.0f);
        if (kcs.have) for (i = 0; i < 3; i++) {
            kcs.Dv[i] = (Dn[i] - kcs.D[i]) / dt;
            if (!jumped) kcs.Rv[i] = (R[i] - kcs.R[i]) / dt;                  /* on a jump frame Rv stays the pre-jump glide: (R - R_old)/dt there is the jump / dt (-7000 cm/s for a 70 cm step in 10 ms), which seeded the NEXT takeover with ev = +7000 and made the offset grow 70 -> 163 cm (owner log 19:31:21) */
        }
        memcpy(kcs.D, Dn, 12); memcpy(kcs.R, R, 12);
        kcs.have = 1;
    }

    /* ---- the displayed eye and FOV */
    E2[0] = Pv2[0] + o[0] / hv * kcs.D[0]; E2[1] = Pv2[1] + kcs.D[1]; E2[2] = Pv2[2] + o[2] / hv * kcs.D[0];
    f2 = kcs.D[2];
    {   /* eye before the stance stage, relative to the feet: carried on by Iv it is the continuity seed of the next pose takeover (no stacking with the stance offset S) */
        float I0[3];
        for (i = 0; i < 3; i++) I0[i] = E2[i] - feet[i];
        if (kcs.iprev_ok && !(kcs.sact & 2)) for (i = 0; i < 3; i++) kcs.Iv[i] = (I0[i] - kcs.Iprev[i]) / dt;   /* unsmoothed one-frame estimate; kept across a stance-pop frame */
        memcpy(kcs.Iprev, I0, 12); kcs.iprev_ok = 1;
    }

    /* ---- stance stage: LAST stage, on whatever eye (E2) the stages above leave, relative to the feet. A stance pop of the pivot
       moves the eye with it (same frame), so the pose detector above sees no jump (eye over pivot unchanged) and only the 60 ms
       follower softened it. Here the velocity-continuous critically damped takeover (StanceMs) eases it, as the pose takeover does. */
    if (kcs.stancems >= 20) {
        float I[3], Ip[3], Oc[3];
        for (i = 0; i < 3; i++) I[i] = E2[i] - feet[i];
        if (kcs.sact & 2) {
            kcs.sact &= 1;
            if (kcs.orel_ok) {
                int merge = kcs.sact & 1;                                    /* k39: a takeover is open: ADD the new step, keep its velocity (no re-seed, no stacking) */
                for (i = 0; i < 3; i++) {
                    Ip[i] = kcs.Orel[i] + kcs.Ov[i] * dt;                    /* where the shown eye would be by itself */
                    kcs.S[i] = Ip[i] - I[i];
                    if (!merge) { kcs.Sv[i] = kcs.Ov[i] - kcs.Iv[i]; if (kcs.Sv[i] * kcs.S[i] > 0.0f) kcs.Sv[i] = 0.0f; }   /* no initial velocity that grows the offset */
                }
                if (merge) kcs.nmerge++;
                if (kcs_len(kcs.S, 3) > 150.0f) { memset(kcs.S, 0, sizeof kcs.S); memset(kcs.Sv, 0, sizeof kcs.Sv); }
                else { kcs.sact = 1; kcs.nstance++; if (kcs.log) klog("camsm: STANCE takeover: shown-vs-input step %.1f %.1f %.1f cm eased over %d ms", kcs.S[0], kcs.S[1], kcs.S[2], kcs.stancems); }
            }
        }
        if (kcs.sact & 1) {
            float w = 6.0f / ((float)kcs.stancems * (kcs_stancefix_busy ? 1.5f : 1.0f) * 0.001f);   /* k39: longer while a mirrored crouch clip runs */
            for (i = 0; i < 3; i++) kcs_cd(&kcs.S[i], &kcs.Sv[i], w, dt);
            if (kcs_len(kcs.S, 3) < 0.05f && kcs_len(kcs.Sv, 3) < 1.0f) { memset(kcs.S, 0, sizeof kcs.S); memset(kcs.Sv, 0, sizeof kcs.Sv); kcs.sact = 0; }
        }
        for (i = 0; i < 3; i++) Oc[i] = I[i] + ((kcs.sact & 1) ? kcs.S[i] : 0.0f);
        for (i = 0; i < 3; i++) E2[i] = feet[i] + Oc[i];
        kcs_clamp(E2, E, dt);                                                 /* hard per-frame limit against the raw step */
        for (i = 0; i < 3; i++) Oc[i] = E2[i] - feet[i];
        if (kcs.orel_ok) for (i = 0; i < 3; i++) kcs.Ov[i] = (Oc[i] - kcs.Orel[i]) / dt;
        memcpy(kcs.Orel, Oc, 12); kcs.orel_ok = 1;
    } else kcs_clamp(E2, E, dt);
    {
        float d_raw = kcs.eprev_ok ? klcam_dist(E, kcs.Eprev) : 0, d_disp = kcs.eprev_ok ? klcam_dist(E2, kcs.Edisp) : 0;
        float fr = kcs.eprev_ok ? (float)fabs(fov - kcs.fovraw) : 0, fd = kcs.eprev_ok ? (float)fabs(f2 - kcs.fovdisp) : 0;
        if (kcs.logleft > 0) {
            if (d_disp > kcs.maxdisp) kcs.maxdisp = d_disp; if (d_raw > kcs.maxraw) kcs.maxraw = d_raw;
            if (fd > kcs.maxfdisp) kcs.maxfdisp = fd; if (fr > kcs.maxfraw) kcs.maxfraw = fr;
            if (kcs.log && kcs.loglines < 400) {
                kcs.loglines++;
                klog("camsm: %s f %ld dt %.4f | eye step raw %.2f disp %.2f cm | fov step raw %.4f disp %.4f (fov %.3f -> %.3f) | e h %.1f y %.1f fov %.3f | pivot shift %.1f", kcs.why, frame, rawdt, d_raw, d_disp, fr, fd, fov, f2, kcs.act ? kcs.e[0] : 0, kcs.act ? kcs.e[1] : 0, kcs.act ? kcs.e[2] : 0, klcam_dist(Pv, Pv2));
            }
            kcs.logleft -= dt;
            if (kcs.logleft <= 0 && kcs.log) klog("camsm: %s takeover ended: largest eye step shown %.2f cm (raw %.2f), largest FOV step shown %.4f (raw %.4f), %d frame lines", kcs.why, kcs.maxdisp, kcs.maxraw, kcs.maxfdisp, kcs.maxfraw, kcs.loglines);
        }
        memcpy(kcs.Eprev, E, 12); kcs.fovraw = fov; kcs.eprev_ok = 1;
    }
    if (kcs.dry) { memcpy(kcs.Edisp, E2, 12); kcs.fovdisp = f2; return; }
    if (kcs.fault >= 3) { memcpy(kcs.Edisp, E, 12); kcs.fovdisp = fov; return; }
    if (klcam_dist(E, E2) > 0.05f && kcs.rc_on != 2) {
        if (!kcs.rc_checked) {
            BYTE pro[5]; static const BYTE want[5] = { 0x51, 0x8B, 0x54, 0x24, 0x08 };
            kcs.rc_checked = 1;
            if (klh_rd((DWORD_PTR)KLH_VA(KCS_EYEFN), pro, 5) && !memcmp(pro, want, 5)) kcs.rc_on = 1;
            else { kcs.rc_on = 2; klog("camsm: eye writes REFUSED: the first bytes of 0x7c9030 are not the ones read (another build)"); }
        }
        if (kcs.rc_on == 1) {
            float chk[3] = { 0, 0, 0 }; struct klcam_eye a;
            if (!klcam_nodepos(cam, chk) || klcam_dist(chk, E) > 0.5f) {
                if (++kcs.strikes >= 3) { kcs.rc_on = 2; klog("camsm: eye writes OFF: the node %.1f %.1f %.1f is not the eye %.1f %.1f %.1f (3 strikes)", chk[0], chk[1], chk[2], E[0], E[1], E[2]); }
            } else {
                a.cam = cam; memcpy(a.p, E2, 12);
                if (klfc_guard("camsmooth eye", klcam_eye_body, &a) < 0) { kcs.fault++; klog("camsm: guarded fault in the eye setter (%d/3)", kcs.fault); }
                else { kcs.fault = 0; memcpy(kcs.Edisp, E2, 12); }
            }
        }
    } else memcpy(kcs.Edisp, E, 12);
    if (kcs.rc_on != 1) memcpy(kcs.Edisp, E, 12);
    if (fabs(f2 - fov) > 1e-5f) { klh_data((void *)(DWORD_PTR)(nd + 0x70), &f2, 4, "camera FOV (CamSmooth)"); kcs.fovdisp = f2; } else kcs.fovdisp = fov;
}

static void klcamsmooth_init(void)
{
    memset(&kcs, 0, sizeof kcs);
    kcs.enable = GetPrivateProfileIntA("CamSmooth", "Enable", 1, klh_ini) != 0;
    kcs.log = GetPrivateProfileIntA("CamSmooth", "Log", 0, klh_ini) != 0;
    kcs.dry = GetPrivateProfileIntA("CamSmooth", "Dry", 0, klh_ini) != 0;
    kcs.dtfix = GetPrivateProfileIntA("CamSmooth", "DtFix", 1, klh_ini) != 0;
    kcs.pivotms = (int)kcs_ini_f("PivotMs", 60.0f, 0.0f, 400.0f);
    kcs.blendms = (int)kcs_ini_f("BlendMs", 250.0f, 0.0f, 1500.0f);
    kcs.aimoutms = (int)kcs_ini_f("AimOutMs", 320.0f, 0.0f, 1500.0f);
    kcs.aiminms = (int)kcs_ini_f("AimInMs", 90.0f, 0.0f, 1500.0f);
    kcs.jumpcm = kcs_ini_f("JumpCm", 12.0f, 2.0f, 200.0f);
    kcs.jumpfov = kcs_ini_f("JumpFov", 0.05f, 0.005f, 1.0f);
    kcs.stancems = (int)kcs_ini_f("StanceMs", 280.0f, 0.0f, 1500.0f);
    kcs.stancecm = kcs_ini_f("StanceCm", 6.0f, 1.0f, 100.0f);   /* GUESS: crouch/stand pivot pops are 15 .. 55 cm (owner log), bob is < 1 cm per frame */
    kcs.dtavg = 0.016;
    kcs.trigt = -10.0;
    klstancefix_init();
    if (kcs.enable) klog("camsm: on: PivotMs %d BlendMs %d AimOutMs %d AimInMs %d DtFix %d JumpCm %.0f JumpFov %.3f StanceMs %d StanceCm %.1f Log %d%s", kcs.pivotms, kcs.blendms, kcs.aimoutms, kcs.aiminms, kcs.dtfix, kcs.jumpcm, kcs.jumpfov, kcs.stancems, kcs.stancecm, kcs.log, kcs.dry ? " DRY" : "");
}

#include "klstancefix.c"                                   /* k39: [StanceFix]; its tick/init are called from the functions above */

#endif
