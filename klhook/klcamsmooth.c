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
 * WIRING (klhook.c): #include "klcamsmooth.c" after klcam.c; klcamsmooth_tick(game_thread); after klcam_tick; klcamsmooth_init();
 * after klcam_init(). ini: [CamSmooth] Enable=1 PivotMs=60 BlendMs=250 AimOutMs=320 AimInMs=90 DtFix=1 Log=0 Dry=0 JumpCm=12 JumpFov=0.05 StanceMs=280 StanceCm=6
 */
#ifndef KLCAMSMOOTH_C
#define KLCAMSMOOTH_C

#define KCS_RCB_RA 0x0087aa82u
#define KCS_EYEFN  0x007c9030u

static struct {
    int enable, pivotms, blendms, aimoutms, aiminms, dtfix, log, dry, stancems;
    float jumpcm, jumpfov, stancecm;
    /* stance stage (StanceMs): last stage, works on the displayed eye relative to the FEET so running never lags */
    float qprev[3], qpv[3]; int qprev_ok;            /* raw pivot offset from the feet, last frame, and its smooth velocity */
    float S[3], Sv[3]; int sact;                      /* open stance takeover: S = shown eye - input eye (feet-relative), decays critically damped */
    float Orel[3], Ov[3], Iprev[3], Iv[3]; int orel_ok; /* last shown eye rel feet and its velocity; last input eye rel feet and its pre-step velocity */
    long nstance; float maxstep_s;
    /* per camera */
    DWORD cam; int have;                  /* have = previous frame state valid */
    long lastframe;
    double dtavg;
    float h_orig[6]; int h_ok[6], h_told;
    float R[3], Rv[3];                    /* raw pose (h, y, fov) and its velocity */
    float D[3], Dv[3];                    /* displayed pose and velocity */
    float e[3], ev[3], w[3]; int act;     /* open takeover: e = D - R, decay rate per channel (1/s) */
    float qs[3], qv[3]; int qhave;        /* pivot offset follower */
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
    kcs.have = 0; kcs.act = 0; kcs.qhave = 0; kcs.eprev_ok = 0; kcs.qprev_ok = 0; kcs.sact = 0; kcs.orel_ok = 0;
    memset(kcs.S, 0, sizeof kcs.S); memset(kcs.Sv, 0, sizeof kcs.Sv); memset(kcs.Iv, 0, sizeof kcs.Iv); memset(kcs.Ov, 0, sizeof kcs.Ov); memset(kcs.qpv, 0, sizeof kcs.qpv);
    memset(kcs.e, 0, sizeof kcs.e); memset(kcs.ev, 0, sizeof kcs.ev); memset(kcs.Dv, 0, sizeof kcs.Dv); memset(kcs.Rv, 0, sizeof kcs.Rv);
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
    DWORD gd, P, cam, sys; float rawdt = 0, dt, E[3], Pv[3], feet[3], o[3], fov = 0, R[3], hv, q[3], Pv2[3], E2[3], f2; long frame; int i, trig = 0;
    DWORD nd;
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

    /* ---- pose takeover */
    if (kcs.have) {
        float pr[3], res[3], inv = 1.0f / dt;
        for (i = 0; i < 3; i++) { pr[i] = kcs.R[i] + kcs.Rv[i] * dt; res[i] = R[i] - pr[i]; }
        if (fabs(res[0]) > kcs.jumpcm || fabs(res[1]) > kcs.jumpcm || fabs(res[2]) > kcs.jumpfov) {
            float T; const char *why;
            if (res[2] > 0.02f) { T = (float)kcs.aimoutms; why = "out"; }
            else if (res[2] < -0.02f) { T = (float)kcs.aiminms; why = "in"; }
            else { T = (float)kcs.blendms; why = "mode"; }
            if (T >= 20.0f) {
                float Dp[3];
                for (i = 0; i < 3; i++) {
                    Dp[i] = kcs.D[i] + kcs.Dv[i] * dt;                    /* where the displayed pose would be by itself */
                    kcs.e[i] = Dp[i] - R[i]; kcs.ev[i] = kcs.Dv[i] - kcs.Rv[i];
                    kcs.w[i] = 6.0f / (T * 0.001f);
                }
                if (fabs(kcs.e[0]) > 400 || fabs(kcs.e[1]) > 400) memset(kcs.e, 0, sizeof kcs.e);
                if (fabs(kcs.e[2]) > 1.5f) kcs.e[2] = 0;
                kcs.act = 1; trig = 1; kcs.ntrig++;
                kcs.logleft = T * 0.001 + 1.0; kcs.loglines = 0; kcs.maxdisp = kcs.maxraw = kcs.maxfdisp = kcs.maxfraw = 0;
                strncpy(kcs.why, why, sizeof kcs.why - 1);
                if (kcs.log) klog("camsm: TRIGGER %s: raw jump h %.1f y %.1f fov %.3f (predicted from last frame), takeover e h %.1f y %.1f fov %.3f over %.0f ms | f %ld dt %.4f", why, res[0], res[1], res[2], kcs.e[0], kcs.e[1], kcs.e[2], T, frame, rawdt);
            }
        }
        (void)inv;
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
        if (kcs.have) for (i = 0; i < 3; i++) { kcs.Dv[i] = (Dn[i] - kcs.D[i]) / dt; kcs.Rv[i] = (R[i] - kcs.R[i]) / dt; }
        memcpy(kcs.D, Dn, 12); memcpy(kcs.R, R, 12);
        kcs.have = 1;
    }

    /* ---- stance pop detector (runs on the RAW pivot offset q from the feet, before the follower; mouse yaw / pitch never moves q) */
    {
        int pop = 0;
        if (kcs.stancems >= 20 && kcs.qprev_ok) {
            float qp[3], r = 0;
            for (i = 0; i < 3; i++) { qp[i] = kcs.qprev[i] + kcs.qpv[i] * dt; r += (q[i] - qp[i]) * (q[i] - qp[i]); }
            r = (float)sqrt(r);
            if (r > kcs.stancecm) pop = 1;
            if (pop && kcs.log) klog("camsm: STANCE pop: pivot offset from the feet stepped %.1f cm (limit %.1f) in one frame: q %.1f %.1f %.1f <- %.1f %.1f %.1f | f %ld dt %.4f", r, kcs.stancecm, q[0], q[1], q[2], kcs.qprev[0], kcs.qprev[1], kcs.qprev[2], frame, rawdt);
        }
        if (pop) {
            memcpy(kcs.qs, q, 12); memset(kcs.qv, 0, 12); kcs.qhave = 1;      /* the stance stage eases it, not the 60 ms follower */
            memset(kcs.qpv, 0, sizeof kcs.qpv);
        } else if (kcs.qprev_ok) for (i = 0; i < 3; i++) kcs.qpv[i] += ((q[i] - kcs.qprev[i]) / dt - kcs.qpv[i]) * 0.5f;
        memcpy(kcs.qprev, q, 12); kcs.qprev_ok = 1;
        kcs.sact = kcs.sact | (pop << 1);                                     /* bit 1 = start a takeover below */
    }

    /* ---- pivot offset follower (animation bob / snaps of the pivot's offset from the feet) */
    if (kcs.pivotms > 0) {
        float w = 6.0f / ((float)kcs.pivotms * 0.001f), x[3];
        if (!kcs.qhave || kcs_len(q, 3) - kcs_len(kcs.qs, 3) > 200.0f) { memcpy(kcs.qs, q, 12); memset(kcs.qv, 0, 12); kcs.qhave = 1; }
        for (i = 0; i < 3; i++) { x[i] = kcs.qs[i] - q[i]; kcs_cd(&x[i], &kcs.qv[i], w, dt); kcs.qs[i] = q[i] + x[i]; }
        for (i = 0; i < 3; i++) Pv2[i] = feet[i] + kcs.qs[i];
    } else memcpy(Pv2, Pv, 12);

    /* ---- the displayed eye and FOV */
    E2[0] = Pv2[0] + o[0] / hv * kcs.D[0]; E2[1] = Pv2[1] + kcs.D[1]; E2[2] = Pv2[2] + o[2] / hv * kcs.D[0];
    f2 = kcs.D[2];

    /* ---- stance stage: LAST stage, on whatever eye (E2) the stages above leave, relative to the feet. A stance pop of the pivot
       moves the eye with it (same frame), so the pose detector above sees no jump (eye over pivot unchanged) and only the 60 ms
       follower softened it. Here the velocity-continuous critically damped takeover (StanceMs) eases it, as the pose takeover does. */
    if (kcs.stancems >= 20) {
        float I[3], Ip[3], Oc[3];
        for (i = 0; i < 3; i++) I[i] = E2[i] - feet[i];
        if (kcs.sact & 2) {
            kcs.sact &= 1;
            if (kcs.orel_ok) {
                for (i = 0; i < 3; i++) {
                    Ip[i] = kcs.Orel[i] + kcs.Ov[i] * dt;                    /* where the shown eye would be by itself */
                    kcs.S[i] = Ip[i] - I[i]; kcs.Sv[i] = kcs.Ov[i] - kcs.Iv[i];
                }
                if (kcs_len(kcs.S, 3) > 150.0f) { memset(kcs.S, 0, sizeof kcs.S); memset(kcs.Sv, 0, sizeof kcs.Sv); }
                else { kcs.sact = 1; kcs.nstance++; if (kcs.log) klog("camsm: STANCE takeover: shown-vs-input step %.1f %.1f %.1f cm eased over %d ms", kcs.S[0], kcs.S[1], kcs.S[2], kcs.stancems); }
            }
            memset(kcs.Iv, 0, sizeof kcs.Iv);
        } else if (kcs.orel_ok) for (i = 0; i < 3; i++) kcs.Iv[i] += ((I[i] - kcs.Iprev[i]) / dt - kcs.Iv[i]) * 0.5f;
        if (kcs.sact & 1) {
            float w = 6.0f / ((float)kcs.stancems * 0.001f);
            for (i = 0; i < 3; i++) kcs_cd(&kcs.S[i], &kcs.Sv[i], w, dt);
            if (kcs_len(kcs.S, 3) < 0.05f && kcs_len(kcs.Sv, 3) < 1.0f) { memset(kcs.S, 0, sizeof kcs.S); memset(kcs.Sv, 0, sizeof kcs.Sv); kcs.sact = 0; }
        }
        for (i = 0; i < 3; i++) Oc[i] = I[i] + ((kcs.sact & 1) ? kcs.S[i] : 0.0f);
        if (kcs.orel_ok) for (i = 0; i < 3; i++) kcs.Ov[i] = (Oc[i] - kcs.Orel[i]) / dt;
        memcpy(kcs.Orel, Oc, 12); memcpy(kcs.Iprev, I, 12); kcs.orel_ok = 1;
        for (i = 0; i < 3; i++) E2[i] = feet[i] + Oc[i];
    }
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
    if (kcs.enable) klog("camsm: on: PivotMs %d BlendMs %d AimOutMs %d AimInMs %d DtFix %d JumpCm %.0f JumpFov %.3f StanceMs %d StanceCm %.1f Log %d%s", kcs.pivotms, kcs.blendms, kcs.aimoutms, kcs.aiminms, kcs.dtfix, kcs.jumpcm, kcs.jumpfov, kcs.stancems, kcs.stancecm, kcs.log, kcs.dry ? " DRY" : "");
}

#endif
