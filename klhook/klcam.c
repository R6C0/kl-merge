/*
 * klcam.c - the camera rework ([Camera] in KLHook.ini): faster, steadier follow, the shoulder key in cover and in cover
 * aim, softer cover-aim blends, and a measurement log. Design: re\camera.md. NOTHING HERE HAS RUN IN THE GAME.
 * The owner, 2026-10-17: "the camera glitches and stays stuck and takes forever to follow your character; change shoulder
 * in cover and when you aim in cover; more smooth, like a cinematic experience".
 * Part of KLHook (included by klhook.c after klshoulder.c, SHIP and TEST alike; uses klshoulder.c's klo_input and
 * klfreeclimb.c's klfc_guard / KLFC_CALL / klfc_f).
 *
 * WHAT MAY BE WRITTEN (SHIP rule: IAT, .data / .bss, heap only): every write goes through klh_data, which refuses a page
 * that is not writable data. No code byte of kl2.exe is patched, nothing in .rdata. Calls into the game (inside
 * klfc_guard, a fault is caught, logged and unwound): 0x640080 (the shoulder key handler) and 0x7c9030 (the camera's eye
 * setter). Three guarded faults in a row switch the feature that faulted OFF. The profile floats are .data and stay changed until the game
 * is restarted (there is no put-back call). ONLINE ([Net] OnlineSafe, kl_online()): ShoulderCover and the Unstick writes stay out of network
 * sessions (Unstick only logs what it would do); the profile floats (client data), Recover's eye and the Log are not gated.
 *
 * WHERE IT RUNS: game thread only, once a frame, at the gameplay call of SteamAPI_RunCallbacks (return address 0x87aa82,
 * klh_rcb_ra; the same site klfreeclimb.c uses; ASSUMPTION: the camera tick, event 0x10 -> 0x650070, has run before it
 * in the same frame). The 100 ms fallback thread does nothing here.
 * The local player P = [[0xdd265c] + 0x828 + 4 * byte [[0xdd265c]+0x898]], a ZFFPlayer (vtable 0xbb45f4); its camera
 * cam = [P+0xbd8], a ZFFCamera1 (vtable 0xbb76a4; checked by its locator [[cam]-4] == 0xc8e50c, READ). dt = float
 * [[0xdd2640]+0x50], frame = int [[0xdd2640]+0x48]. A failed read, no player, a paused / cut frame ([[0xdd265c]+0x4cd8],
 * ASSUMPTION: the global pause / cut flag the camera tick tests at 0x6500e3): nothing is done and the filter state is cleared.
 *
 * THE FEATURES (each has its own ini switch)
 *  F1a Blend    The 25 camera profile structs (0..24 of the 27 that exist) (0x154a820 + i * 0x198, selected by 0x778f50, applied by 0x5ea690) hold three blend
 *               times at +0x170 / +0x174 / +0x178 (copied to cam+0x560 / +0x564 / the timer +0x5a0; READ 0x5ea6b8..0x5ea99f).
 *               The chasers settle in about 0.7 x the time (a = 8 d / T^2, 0x51b430), so the stock FA profile's 3.0 s is about 2 s:
 *               "takes forever to follow". Every time above 0.2 s is multiplied by BlendScale; none goes below min(orig, 0.2) (the
 *               design said 0.05; the fast profiles 0.1 .. 0.4 are left near stock so the aim stays calm: GUESS). Checked first: the
 *               default profile (+10) must read 0.2 / 3.0 / 2.0 and the low cover (+2) 0.4 / 3.0 / 0.8 (READ in the live dump), else
 *               refused. The structs are .data (zero in the file, filled at start: READ), so the values are re-checked every 2 s
 *               and re-written if they were put back to the original. Skipped: +3 (F3a), +16 and +18 (special timers, 0x5ea6b1 ..
 *               0x5ea709 treat 0x154c1a0 / 0x154c4d0 / 0x154cff8 by address). The pair of profiles +10 / +2 is waited for while either reads
 *               all zero (retried every 2 s, refused after 150 tries). Blend semantic (READ 0x5eac54..0x5eac8b): +0x178 is both the duration of a
 *               transition and the constant used during it; 0x48ec00 uses cam+0x560/0x564 only when cam+0x568 bit 0x10 is set; a profile is applied only
 *               when the profile POINTER changes (0x5ea6a1), so rewriting a profile mid-flight does not take effect until the next pointer change.
 *  F1b Unstick  Detector (plain locomotion only: local human [P+0x2720]&2, no cover [P+0x2954], movement id 2/3, no seat/carrier [P+0xd50]/[P+0xd44],
 *               no free climb): player alive, speed > 200 cm/s, the eye (cam+0x508) slower than 20 cm/s, for 1.0 s with normal frames (dt < 0.1).
 *               Then, one step per 0.5 s while it lasts: (1) latch byte [cam+0x394] == 1 with a constant pull-in distance [cam+0x124] -> 0,
 *               (2) blend timer [cam+0x5a0] -> 0 when it reads > 0.05 (selects the fast +0x170 constant at 0x5eac54; cam+0xca0 is NOT written: it is a
 *               decaying slow-down, 0x48ec78..0x48ecbb), (3) the stale side: byte [cam+0xb40] != [P+0x280c] -> copy, (4) give up for 5 s.
 *               Which is the real cause is UNKNOWN (ASSUMPTION); the log's STUCK mark and the step lines tell. Offline only (online: logged).
 *  F1c Recover  (default OFF until a Log=1 run shows the latch and the node behave) A pulled-in eye (0x897d60 sets cam+0x124, 0x56e4c0 puts the eye there) snaps back out in one frame. After a
 *               pull-in the eye may move OUTWARD along the pivot -> eye line at most RecoverSpeed cm/s; inward is untouched. Applied
 *               with the engine's own setter 0x7c9030(cam, &pos) (thiscall, one argument, callee pops it: READ; first bytes
 *               51 8B 54 24 08 are checked). Refuses itself unless the node position [[[cam+0x24]+4]+0x24] equals the eye to 0.5 cm
 *               before the first use and again after each call. The pivot is cam+0x398 as re\camera.md says (the code at
 *               0x56e524 starts the pull-in from cam+0xb0: both are logged; the filter is skipped when 0x398 is not within
 *               400 cm of the player, GUESS). ASSUMPTION that the render follows the call in the same frame.
 *  F2  ShoulderCover  The key handler 0x640080 (called from 0x8464f9 for the three records H+0x10 / +0x20 / +0x30; SwitchCameraSide
 *               is H+0x30, kind [H+0x34] == 2, timer [H+0x38], fired byte [H+0x3c]) refuses at 0x64011d / 0x640124 while byte
 *               [P+0x2954] (the cover / aim-point side, nonzero in cover and in cover aim) is nonzero. There is NO vtable slot for
 *               the handler (no dword 0x640080 in kl2.exe), so re\camera.md 4.2's vtable wrap is impossible. Instead, on the
 *               frame the handler refused (fired 0 -> 1 while [P+0x2954] != 0): [P+0x2954] is set to 0, fired to 0, the ORIGINAL
 *               handler is called once (it checks the key itself, 0x5f4310, and every other gate), then [P+0x2954] is put back.
 *               The two gate instructions are compared with their bytes first (80 B8 54 29 00 00 00 / 0F 85 E7 00 00 00): a
 *               different build refuses the feature. After the toggle [P+0xb84] is set to (want == 0 ? +1 : -1) like 0x513dcb ..
 *               0x513de9 so leaving the cover does not snap back (written only when it holds -1 or +1; success = the side-in-use bit 10 of [P+0x818] changed, NOT [P+0x29a0], which the handler resyncs first: 0x640142..0x64016d; b84 = -1 left / +1 right from the post-call bit). LeanFollow: not
 *               available (no route to the cover state object was found): logged once if asked for.
 *               The stock handler applies the side with 0 seconds (0x640176 fldz): the camera's own sweep (0x9088c0) is the
 *               only smoothing. ASSUMPTION that the cover state re-seats harmlessly on the changed bit (re\camera.md 4.1).
 *  F3a CineAim  The cover-aim profile +3 (0x154ace8): timings 0.1 / 0.5 / 0.2 -> 0.25 / 0.5 / 0.35, FOV [+0x15c] 0.698 -> 0.80
 *               (the FOV is at +0x15c with the flag byte +0x150; 0x5ea72f copies it to cam+0x550: READ; re\camera.md said
 *               +0x550, which is the camera's field). Refused when the values differ.
 *  NOT DONE (needs code or an unread route): F3b the flip duration (floats 0xceb5e0.. are .rdata), F3c the shake scale (no route to
 *               the shaker object; ctor 0x641410 not followed), F3d the FOV step (0xb24824 is .rdata), F1d the smoothing reset.
 *               FlipTime / ShakeScale / FovStep are read and logged but have no effect.
 *  F4  Log      "cam:" lines at LogHz, "camev:" at every change, a 10 s summary. Read only.
 *
 * WIRING (klhook.c; nothing else of the hook changes)
 *   #include "klcam.c"           after  #include "klshoulder.c"
 *   klcam_tick(game_thread);      in klh_tick, after  klo_tick(game_thread);
 *   klcam_init();                 in the init list, after  klo_init();
 * KLHook.ini: [Camera], see the commented block there.
 */
#ifndef KLCAM_C
#define KLCAM_C

#define KLCAM_PL_VT     ((DWORD)(DWORD_PTR)KLH_VA(0x00bb45f4u))   /* ZFFPlayer */
#define KLCAM_COL       ((DWORD)(DWORD_PTR)KLH_VA(0x00c8e50cu))   /* the RTTI locator of ZFFCamera1 (vtable 0xbb76a4) */
#define KLCAM_PROF      ((DWORD)(DWORD_PTR)KLH_VA(0x0154a820u))   /* profile structs of 0x198 bytes (27 exist, READ in KLHook_1/2.dmp) */
#define KLCAM_NPROF     25                        /* 0..24 scaled; 25 (0x154cff8) is a special-cased address (0x5ea6b1..), 26 reads 0.5/0.5/0.5, 27 is zero: not touched */
#define KLCAM_RCB_RA    0x0087aa82u
#define KLCAM_NPL       28                        /* the player array [gd+0x828 + 4 * i] holds 28 entries (klfed.c / klfedkit.c: sel < 28) */
#define KLCAM_KEYFN     0x00640080u               /* the shoulder key handler, thiscall(H, record) ret 4 */
#define KLCAM_EYEFN     0x007c9030u               /* the camera's eye setter, thiscall(cam, float[3]) ret 4 */
#define KLCAM_NREST     80
#define KLCAM_PROF_TRIES 150                      /* 2 s apart: 5 minutes of a zero table before Blend refuses itself */

struct klcam_cfg {
    int enable, log, loghz, blend, unstick, recover, shouldercover, scoronline, leanfollow, cine, cineaim;
    float blendscale, recoverspeed, fliptime, shakescale, fovstep;
};
struct klcam_rest { DWORD at; float orig; };

static struct {
    struct klcam_cfg c;
    LARGE_INTEGER qf, qlast;
    /* identity */
    DWORD pl, cam; int have; long lastframe;
    /* profiles */
    int prof_tries, prof_ok, prof_refused, prof_told, aim_ok, aim_refused; DWORD prof_check; float orig[KLCAM_NPROF][3], aim_orig[3], aim_fov_orig;
    struct klcam_rest rest[KLCAM_NREST]; int nrest;
    /* per-frame state */
    float peye[3], pfeet[3], pdt; int pv, gate_told; float vE, vP; double gate_s;
    double stuckS, stepS, quietS, blockS; int step; float lastcd; long pulls;
    /* F1c */
    int rc_on, rc_checked, rc_fault, rc_strikes; float rc_d; double rc_win; float rc_cd;
    /* F2 */
    int sc_on, sc_checked, sc_fault, sc_wait, sc_online_told; BYTE fired0, cs0; double cs_s, sc_cool, sc_waits; int sc_lean_told;
    /* events */
    long ev_side, ev_prof, ev_cs; int ev_stuck, ev_blk; DWORD ev_profp;
    /* summary */
    double sum_t, sum_stuck, sum_maxd; long sum_hitch, sum_pull, sum_n; float sum_taumax; double sum_taus; long sum_taun;
} kc;

/* ---------------------------------------------------------------- helpers */

static int klcam_fin(float f) { return f == f && f > -1e9f && f < 1e9f; }
static int klcam_v3(DWORD p, float *v) { if (!klh_rd(p, v, 12)) return 0; return klcam_fin(v[0]) && klcam_fin(v[1]) && klcam_fin(v[2]); }
static float klcam_dist(const float *a, const float *b) { float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2]; return (float)sqrt(x * x + y * y + z * z); }
static float klcam_hdist(const float *a, const float *b) { float x = a[0] - b[0], z = a[2] - b[2]; return (float)sqrt(x * x + z * z); }   /* y is up */
static int klcam_near(float a, float b, float e) { return a - b < e && b - a < e; }
static float klcam_ini_f(const char *key, float def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("Camera", key, "", t, sizeof t, klh_ini);
    if (!t[0]) return def;
    v = (float)atof(t);
    if (!klcam_fin(v) || v < lo || v > hi) { klog("cam: [Camera] %s=%s is out of range %.2f .. %.2f, %.2f used", key, t, lo, hi, def); return def; }
    return v;
}
static int klcam_ini_i(const char *key, int def) { return (int)GetPrivateProfileIntA("Camera", key, def, klh_ini); }

/* a profile write that remembers the float it replaced. Profiles are .data and are put back only by restarting the game */
static int klcam_putf(DWORD at, float orig, float v, const char *what)
{
    int i;
    if (!klh_data((void *)(DWORD_PTR)at, &v, 4, what)) return 0;
    for (i = 0; i < kc.nrest; i++) if (kc.rest[i].at == at) return 1;
    if (kc.nrest < KLCAM_NREST) { kc.rest[kc.nrest].at = at; kc.rest[kc.nrest].orig = orig; kc.nrest++; }
    return 1;
}
static DWORD klcam_player(DWORD *gdout)
{
    DWORD gd, pl; BYTE idx = 0xff;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || idx >= KLCAM_NPL) return 0;   /* 0xff / a negative signed char = none */
    if (!(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_rd32(pl) != KLCAM_PL_VT) return 0;
    *gdout = gd;
    return pl;
}

/* ---------------------------------------------------------------- F1a / F3a: the profile structs */

static void klcam_prof_scale(int i, float *orig, float *out)
{
    int k;
    for (k = 0; k < 3; k++) {
        float o = orig[k], floor_ = o < 0.2f ? o : 0.2f, n = o * kc.c.blendscale;
        out[k] = n < floor_ ? floor_ : n;
        if (o <= 0.2f) out[k] = o;                               /* the fast ones stay as they are */
    }
    (void)i;
}
static int klcam_prof_skip(int i) { return i == 3 || i == 16 || i == 18; }

static void klcam_profiles(void)
{
    int i, k, nre = 0; float v[3], want[3], f; DWORD a;
    if (!kc.c.blend && !kc.c.cineaim) return;
    if (!kc.prof_ok && !kc.prof_refused && kc.c.blend) {
        /* verify the build / the table before the first write */
        float p10[3], p2[3]; int ok = 1;
        for (k = 0; k < 3; k++) { p10[k] = klfc_f(KLCAM_PROF + 10 * 0x198 + 0x170 + 4 * k); p2[k] = klfc_f(KLCAM_PROF + 2 * 0x198 + 0x170 + 4 * k); }
        /* the table is filled at start: an all-zero +10 OR +2 means "not yet", retried every 2 s (at most KLCAM_PROF_TRIES times, then refused) */
        if ((p10[0] == 0 && p10[1] == 0 && p10[2] == 0) || (p2[0] == 0 && p2[1] == 0 && p2[2] == 0)) {
            if (!kc.prof_told) { kc.prof_told = 1; klog("cam: profile table not filled yet, waiting"); }
            if (++kc.prof_tries > KLCAM_PROF_TRIES) { kc.prof_refused = 1; klog("cam: Blend REFUSED: the profile table stayed zero for %d checks (+10 %.2f/%.2f/%.2f, +2 %.2f/%.2f/%.2f)", KLCAM_PROF_TRIES, p10[0], p10[1], p10[2], p2[0], p2[1], p2[2]); }
            return;
        }
        ok = klcam_near(p10[0], 0.2f, 1e-4f) && klcam_near(p10[1], 3.0f, 1e-4f) && klcam_near(p10[2], 2.0f, 1e-4f) &&
             klcam_near(p2[0], 0.4f, 1e-4f) && klcam_near(p2[1], 3.0f, 1e-4f) && klcam_near(p2[2], 0.8f, 1e-4f);
        if (!ok) {
            kc.prof_refused = 1;
            klog("cam: Blend REFUSED: profile +10 reads %.4f / %.4f / %.4f and +2 reads %.4f / %.4f / %.4f, not 0.2 / 3 / 2 and 0.4 / 3 / 0.8 (another build, or the table is already changed)",
                 p10[0], p10[1], p10[2], p2[0], p2[1], p2[2]);
        } else {
            for (i = 0; i < KLCAM_NPROF; i++) for (k = 0; k < 3; k++) kc.orig[i][k] = klfc_f(KLCAM_PROF + i * 0x198 + 0x170 + 4 * k);
            kc.prof_ok = 1;
            klog("cam: Blend on: the %d profiles' times are read, BlendScale %.2f", KLCAM_NPROF, kc.c.blendscale);
        }
    }
    if (kc.prof_ok && kc.c.blend) {
        for (i = 0; i < KLCAM_NPROF; i++) {
            if (klcam_prof_skip(i)) continue;
            klcam_prof_scale(i, kc.orig[i], want);
            for (k = 0; k < 3; k++) {
                a = KLCAM_PROF + i * 0x198 + 0x170 + 4 * k; f = klfc_f(a);
                if (!klcam_fin(kc.orig[i][k]) || kc.orig[i][k] <= 0 || kc.orig[i][k] > 20) continue;         /* not a time: leave it */
                if (klcam_near(f, want[k], 1e-5f)) continue;
                if (klcam_near(f, kc.orig[i][k], 1e-5f)) { if (klcam_putf(a, kc.orig[i][k], want[k], "camera profile blend time")) nre++; }
                /* else somebody else changed it: left alone */
            }
        }
        (void)v;
    }
    if (kc.c.cineaim && !kc.aim_refused) {
        DWORD b = KLCAM_PROF + 3 * 0x198; float t[3], fov = klfc_f(b + 0x15c); BYTE has = 0; static const float nt[3] = { 0.25f, 0.5f, 0.35f };
        for (k = 0; k < 3; k++) t[k] = klfc_f(b + 0x170 + 4 * k);
        klh_rd(b + 0x150, &has, 1);
        if (!kc.aim_ok) {
            if (t[0] == 0 && t[1] == 0 && t[2] == 0) return;
            if (klcam_near(t[0], 0.1f, 1e-4f) && klcam_near(t[1], 0.5f, 1e-4f) && klcam_near(t[2], 0.2f, 1e-4f) && klcam_near(fov, 0.698f, 0.005f) && has) {
                for (k = 0; k < 3; k++) kc.aim_orig[k] = t[k];
                kc.aim_fov_orig = fov; kc.aim_ok = 1;
                klog("cam: CineAim on: cover-aim profile +3 (0x154ace8) times 0.1/0.5/0.2 -> 0.25/0.5/0.35, FOV 0.698 -> 0.80");
            } else {
                kc.aim_refused = 1;
                klog("cam: CineAim REFUSED: profile +3 reads %.4f / %.4f / %.4f, FOV(+0x15c) %.4f, flag %u (expected 0.1 / 0.5 / 0.2, 0.698, nonzero)", t[0], t[1], t[2], fov, (unsigned)has);
            }
        }
        if (kc.aim_ok) {
            for (k = 0; k < 3; k++) {
                if (klcam_near(t[k], nt[k], 1e-5f)) continue;
                if (klcam_near(t[k], kc.aim_orig[k], 1e-5f) && klcam_putf(b + 0x170 + 4 * k, kc.aim_orig[k], nt[k], "cover-aim profile blend time")) nre++;
            }
            if (!klcam_near(fov, 0.80f, 1e-5f) && klcam_near(fov, kc.aim_fov_orig, 1e-5f) && klcam_putf(b + 0x15c, kc.aim_fov_orig, 0.80f, "cover-aim profile FOV")) nre++;
        }
    }
    if (nre) klog("cam: %d profile float(s) written", nre);
}

/* ---------------------------------------------------------------- F2: the shoulder key in cover */

struct klcam_key { DWORD H, P; };
static int klcam_key_body(void *arg)
{
    struct klcam_key *k = (struct klcam_key *)arg;
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, DWORD), KLCAM_KEYFN)(k->H, 0, k->H + 0x30);
    return 0;
}

static void klcam_cover(DWORD gd, DWORD P, DWORD cam, float dt)
{
    DWORD H; BYTE cs = 0, fired = 0, fired1 = 0, kind = 0, z = 0; DWORD bit0, bit1, b84, w0, w1; struct klcam_key a; BYTE gate1[7], gate2[6]; float tmr = 0;
    static const BYTE g1[7] = { 0x80, 0xB8, 0x54, 0x29, 0x00, 0x00, 0x00 }, g2[6] = { 0x0F, 0x85, 0xE7, 0x00, 0x00, 0x00 };
    int r;
    if (!kc.c.shouldercover || kc.sc_fault >= 3) return;
    /* [Net] OnlineSafe: the swap writes [P+0xb84] / the shoulder bit and runs the game's handler; the cover side is replicated (0x4520d0,
       re\camera.md 4.4): offline only, unless [Camera] ShoulderCoverOnline=1 (a test switch) */
    if (!kc.c.scoronline && kl_online()) {
        if (!kc.sc_online_told) { kc.sc_online_told = 1; klog("cam: ShoulderCover stays off in a network session ([Net] OnlineSafe; [Camera] ShoulderCoverOnline=1 lifts it for a test)"); }
        kc.fired0 = 0; return;
    }
    if (!kc.sc_checked) {
        kc.sc_checked = 1;
        if (klh_rd((DWORD_PTR)KLH_VA(0x64011d), gate1, 7) && klh_rd((DWORD_PTR)KLH_VA(0x640124), gate2, 6) && !memcmp(gate1, g1, 7) && !memcmp(gate2, g2, 6)) {
            kc.sc_on = 1;
            klog("cam: ShoulderCover on: the key handler's cover gate (0x64011d / 0x640124) is as read; the key is run once more with the gate lifted when it was refused in cover");
        } else klog("cam: ShoulderCover REFUSED: the gate bytes at 0x64011d / 0x640124 are not the ones read (another build)");
        if (kc.c.leanfollow) klog("cam: LeanFollow is not available (no route to the cover state object); the body stays on its side");
    }
    if (!kc.sc_on) return;
    klh_rd(P + 0x2954, &cs, 1);
    if (cs != 0) kc.cs_s += dt; else kc.cs_s = 0;
    kc.sc_cool -= dt;
    if (!(H = klo_input(gd, P))) { kc.fired0 = 0; kc.cs0 = cs; return; }
    klh_rd(H + 0x3c, &fired, 1); klh_rd(H + 0x34, &kind, 1); klh_rd(H + 0x38, &tmr, 4);
    /* hold-off: after a toggle the next one needs the record's timer back at its idle value (0.08) - fail open after 2 s so a different timer meaning cannot kill the feature */
    if (kc.sc_wait) {
        kc.sc_waits += dt;
        if (klcam_fin(tmr) && tmr >= 0.07f) kc.sc_wait = 0;
        else if (kc.sc_waits > 2.0) { kc.sc_wait = 0; klog("cam: ShoulderCover hold-off released after 2 s (record timer reads %.3f, not back at 0.08)", tmr); }
    }
    if (cs != 0 && fired && !kc.fired0 && kind == 2 && kc.sc_cool <= 0 && kc.cs_s > 0.15 && !kc.sc_wait) {
        bit0 = klh_rd32(P + 0x818) >> 10 & 1; w0 = klh_rd32(P + 0x29a0);
        a.H = H; a.P = P;
        klh_data((void *)(DWORD_PTR)(P + 0x2954), &z, 1, "player cover side byte lifted for one call of the key handler");
        klh_data((void *)(DWORD_PTR)(H + 0x3c), &z, 1, "key record fired byte cleared");
        r = klfc_guard("cover key", klcam_key_body, &a);
        klh_data((void *)(DWORD_PTR)(P + 0x2954), &cs, 1, "player cover side byte put back");
        if (r < 0) { kc.sc_fault++; if (kc.sc_fault >= 3) klog("cam: feature ShoulderCover disabled after fault"); kc.fired0 = fired; return; }
        kc.sc_fault = 0;
        /* success = the SIDE IN USE (bit 10 of [P+0x818]) changed. [P+0x29a0] is not a valid test: the handler first resyncs it to the live bit
           (0x640142..0x64016d), so a stale value would look like "no toggle" (review finding) */
        bit1 = klh_rd32(P + 0x818) >> 10 & 1; w1 = klh_rd32(P + 0x29a0); b84 = klh_rd32(P + 0xb84);
        kc.sc_cool = 0.25; kc.sc_wait = 1; kc.sc_waits = 0;
        if (bit1 != bit0) {
            /* leaving the cover restores the side from [P+0xb84] (0x5ea972..0x5ea984): -1 left, +1 right (0x513dcb..0x513de9) */
            if (b84 == 1 || b84 == 0xffffffffu) {
                DWORD nb = bit1 ? 0xffffffffu : 1;
                klh_data((void *)(DWORD_PTR)(P + 0xb84), &nb, 4, "cover return side kept in step with the new shoulder");
            }
            klog("camev: shoulder swapped in cover: side bit %lu -> %lu (side byte %u), want %lu -> %lu, coverside %u, b84 %ld -> %ld, cam blend %.2f, cam profile %08lx. "
                 "ASSUMPTION: the cover state's own exit (0x71f3df forces the side from state+0x104) may override b84 - read the 'coverside 1->0' camev line that follows",
                 bit0, bit1, (unsigned)(klh_rd32(P + 0x280c) & 0xff), w0, w1, (unsigned)cs, (long)b84, (long)klh_rd32(P + 0xb84), klfc_f(cam + 0xb9c), klh_rd32(cam + 0xb2c));
        } else klog("camev: shoulder key in cover: the side bit did not change (%lu; key no longer down, or another gate); want %lu -> %lu", bit0, w0, w1);
        klh_rd(H + 0x3c, &fired1, 1); kc.fired0 = fired1;           /* what the record holds NOW (the handler sets it to 1 again: 0x6400e1) */
        kc.cs0 = cs;
        return;
    }
    kc.fired0 = fired; kc.cs0 = cs;
}

/* ---------------------------------------------------------------- F1c: the pull-in recovery */

struct klcam_eye { DWORD cam; float p[3]; };
static int klcam_eye_body(void *arg)
{
    struct klcam_eye *e = (struct klcam_eye *)arg;
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, float *), KLCAM_EYEFN)(e->cam, 0, e->p);
    return 0;
}
static int klcam_nodepos(DWORD cam, float *out)
{
    DWORD node = klh_rd32(cam + 0x24), geom = node ? klh_rd32(node + 4) : 0;
    return geom && klcam_v3(geom + 0x24, out);
}

static void klcam_recover(DWORD P, DWORD cam, float dt, const float *E, const float *Pv, const float *feet, BYTE blocked, float cd)
{
    float d, u[3], m[3], ml, cosang, lim, pos[3]; int i;
    if (!kc.c.recover || kc.rc_fault >= 3) return;
    d = klcam_dist(E, Pv);
    if (!kc.rc_checked) {
        BYTE pro[5]; static const BYTE want[5] = { 0x51, 0x8B, 0x54, 0x24, 0x08 };
        kc.rc_checked = 1;
        if (klh_rd((DWORD_PTR)KLH_VA(KLCAM_EYEFN), pro, 5) && !memcmp(pro, want, 5)) kc.rc_on = 1;
        else klog("cam: Recover REFUSED: the first bytes of 0x7c9030 are not the ones read (another build)");
    }
    if (!kc.rc_on) return;
    /* a pull-in window: opens when the pull-in distance or the eye distance dropped WHILE the latch is set (0x89851c sets it on a hit, 0x898384
       clears it on every call), stays 0.8 s. The apply condition does NOT need the latch: on the snap-out frame it is already 0 (0x56e511 skips
       0x56e4c0), which is exactly the frame this filter exists for. */
    if (blocked && kc.pv && (cd < kc.rc_cd - 3.0f || d < kc.rc_d - 10.0f)) { kc.rc_win = 0.8; kc.pulls++; }
    else if (kc.rc_win > 0) kc.rc_win -= dt;
    lim = kc.rc_d + kc.c.recoverspeed * dt;
    if (kc.pv && kc.rc_win > 0 && dt > 0.0005f && dt < 0.1f && d > lim && d - kc.rc_d < 300.0f &&
        klcam_dist(feet, kc.pfeet) < 300.0f && klcam_dist(Pv, feet) < 400.0f && d > 1.0f) {
        for (i = 0; i < 3; i++) { u[i] = (E[i] - Pv[i]) / d; m[i] = E[i] - kc.peye[i]; }
        ml = (float)sqrt(m[0] * m[0] + m[1] * m[1] + m[2] * m[2]);
        cosang = ml > 1e-3f ? (m[0] * u[0] + m[1] * u[1] + m[2] * u[2]) / ml : 0;
        if (cosang > 0.866f) {          /* mostly outward along the line: 30 degrees */
            struct klcam_eye a; float chk[3] = { 0, 0, 0 };
            for (i = 0; i < 3; i++) a.p[i] = Pv[i] + u[i] * lim;
            a.cam = cam; memcpy(pos, a.p, 12);
            if (!klcam_nodepos(cam, chk) || klcam_dist(chk, E) > 0.5f) {
                if (++kc.rc_strikes >= 3) kc.rc_on = 0;
                klog("cam: Recover self-test strike %d/3: the node position %.1f %.1f %.1f is not the eye %.1f %.1f %.1f%s", kc.rc_strikes, chk[0], chk[1], chk[2], E[0], E[1], E[2], kc.rc_on ? "" : " - feature off");
                kc.rc_win = 0; kc.rc_d = d; kc.rc_cd = cd;
                return;
            }
            if (klfc_guard("eye", klcam_eye_body, &a) < 0) { kc.rc_fault++; if (kc.rc_fault >= 3) klog("cam: feature Recover disabled after fault"); return; }
            kc.rc_fault = 0;
            if (!klcam_nodepos(cam, chk) || klcam_dist(chk, pos) > 0.5f) {
                if (++kc.rc_strikes >= 3) kc.rc_on = 0;
                klog("cam: Recover strike %d/3: after 0x7c9030 the node is at %.1f %.1f %.1f, not at %.1f %.1f %.1f%s", kc.rc_strikes, chk[0], chk[1], chk[2], pos[0], pos[1], pos[2], kc.rc_on ? "" : " - feature off");
                kc.rc_win = 0;
                return;
            }
            kc.rc_d = lim; memcpy(kc.peye, pos, 12);
            return;
        }
    }
    kc.rc_d = d; kc.rc_cd = cd;
}

/* ---------------------------------------------------------------- F1b: the watchdog */

static void klcam_unstick(DWORD P, DWORD cam, float dt, int stuck, BYTE blocked, float cd)
{
    BYTE side = 0, camside = 0; float z = 0, tmr = 0; BYTE zb = 0; int on = !kl_online();
    if (kc.quietS > 0) { kc.quietS -= dt; return; }
    if (blocked == 1 && klcam_near(cd, kc.lastcd, 0.01f)) kc.blockS += dt; else kc.blockS = 0;
    kc.lastcd = cd;
    if (!stuck) { kc.step = 0; kc.stepS = 0; return; }
    if (!kc.c.unstick) return;
    kc.stepS += dt;
    if (kc.stepS < 0.5 && kc.step) return;
    kc.stepS = 0;
    /* Three steps (the old step 1, "tick counter -> 4", is gone: 0x6500d9 already sets the tick to 4 when the system byte is 0). In a network
       session ([Net] OnlineSafe) nothing is written, the steps are only logged. */
    switch (++kc.step) {
    case 1:
        if (blocked == 1 && kc.blockS > 0.5) {
            if (on) klh_data((void *)(DWORD_PTR)(cam + 0x394), &zb, 1, "camera pull-in latch");
            klog("cam: unstick 1: pull-in latch %s (it stood 1 for %.1f s at distance %.1f)", on ? "cleared" : "would be cleared (online: log only)", kc.blockS, cd);
        } else klog("cam: unstick 1: skipped (latch %u for %.1f s)", (unsigned)blocked, kc.blockS);
        break;
    case 2:
        /* only the blend timer: 0 selects the fast +0x170 constant at 0x5eac54. cam+0xca0 is a decaying SLOW-DOWN (0x48ec78..0x48ecbb, constants = max(target, ca0)): left alone */
        klh_rd(cam + 0x5a0, &tmr, 4);
        if (klcam_fin(tmr) && tmr > 0.05f) {
            if (on) klh_data((void *)(DWORD_PTR)(cam + 0x5a0), &z, 4, "camera blend timer");
            klog("cam: unstick 2: blend timer %.2f -> 0%s", tmr, on ? "" : " (online: log only)");
        } else klog("cam: unstick 2: skipped (no blend pending: timer %.2f)", tmr);
        break;
    case 3:
        klh_rd(P + 0x280c, &side, 1); klh_rd(cam + 0xb40, &camside, 1);
        if (side <= 1 && camside != side) {
            if (on) klh_data((void *)(DWORD_PTR)(cam + 0xb40), &side, 1, "camera side copy");
            klog("cam: unstick 3: camera side %u -> %u%s", (unsigned)camside, (unsigned)side, on ? "" : " (online: log only)");
        } else klog("cam: unstick 3: skipped (sides %u / %u)", (unsigned)side, (unsigned)camside);
        break;
    default:
        klog("cam: stuck unrecovered (3 steps tried); quiet for 5 s"); kc.quietS = 5.0; kc.step = 0;
        break;
    }
}

/* ---------------------------------------------------------------- the tick */

static void klcam_lost(void)
{
    if (kc.have) klog("cam: no local player / camera any more");
    kc.have = 0; kc.pv = 0; kc.stuckS = 0; kc.step = 0; kc.blockS = 0; kc.rc_win = 0; kc.rc_d = 0; kc.fired0 = 0; kc.cs_s = 0; kc.pl = kc.cam = 0;
}

static void klcam_tick(int game_thread)
{
    DWORD gd, P, cam, sys; LARGE_INTEGER now; float dt = 0, E[3], feet[3], Pv[3], Pv2[3], node[3], cd = 0, blend = 0, sideb = 0, fov = 0; BYTE blocked = 0, side = 0, cs = 0;
    long frame; int stuck; DWORD gnow;
    if (!kc.c.enable || !klh_exe_ok || !game_thread) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLCAM_RCB_RA)) return;
    if (!(P = klcam_player(&gd))) { klcam_lost(); return; }
    if (!(cam = klh_rd32(P + 0xbd8)) || klh_rd32(klh_rd32(cam) - 4) != KLCAM_COL) { klcam_lost(); return; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)))) return;
    klh_rd(sys + 0x50, &dt, 4); frame = (long)klh_rd32(sys + 0x48);
    if (frame == kc.lastframe) return;                             /* once a frame */
    if (!klcam_fin(dt) || dt <= 0) return;                         /* a failed / zero dt read: skip the frame (no 0.001 s clamp: it made vE / vP huge) */
    if (P != kc.pl || cam != kc.cam) {                             /* a new level / respawn: the old objects are gone */
        kc.pl = P; kc.cam = cam; kc.pv = 0; kc.stuckS = 0; kc.step = 0; kc.blockS = 0; kc.rc_win = 0; kc.rc_d = 0; kc.fired0 = 0; kc.cs_s = 0; kc.sc_cool = 0;
        if (!kc.have) klog("cam: local player %08lx camera %08lx", P, cam);
        kc.have = 1;
    }
    kc.lastframe = frame;
    if (dt > 0.1f) dt = 0.1f;
    QueryPerformanceCounter(&now);
    gnow = GetTickCount();
    if (gnow - kc.prof_check >= 2000) { kc.prof_check = gnow; klcam_profiles(); }
    if (klh_rd32(gd + 0x4cd8) & 0xff) {                                              /* the pause / cut flag (ASSUMPTION): hands off */
        kc.gate_s += dt; kc.pv = 0; kc.stuckS = 0;
        if (kc.gate_s > 5.0 && !kc.gate_told) { kc.gate_told = 1; klog("cam: the pause / cut flag [gd+0x4cd8] has stood nonzero for 5 s in a round: the watchdog, ShoulderCover and Recover are idle (ASSUMPTION about this flag; check in a normal round)"); }
        return;
    }
    kc.gate_s = 0;
    if (!klcam_v3(cam + 0x508, E) || !klcam_v3(P + 0x460, feet) || !klcam_v3(cam + 0x398, Pv)) { kc.pv = 0; return; }
    klh_rd(cam + 0x394, &blocked, 1); klh_rd(cam + 0x124, &cd, 4); if (!klcam_fin(cd)) cd = 0;
    klcam_v3(cam + 0xb0, Pv2);
    kc.vE = kc.pv ? klcam_dist(E, kc.peye) / dt : 0; kc.vP = kc.pv ? klcam_dist(feet, kc.pfeet) / dt : 0;
    if (kc.pv && klcam_dist(feet, kc.pfeet) > 300.0f) { kc.pv = 0; kc.vE = kc.vP = 0; kc.rc_win = 0; kc.stuckS = 0; }      /* a teleport / respawn */
    /* the player's state: down bits (klshoulder.c: word [P+0xa54] & 0x102) */
    {
        WORD a54 = 0; int alive, loco; BYTE kind = 0, cov = 0; int mv;
        klh_rd(P + 0xa54, &a54, 2); alive = !(a54 & 0x102);
        /* the watchdog only judges plain locomotion of the local human: not a seat / carrier / heli ride ([P+0xd50], [P+0xd44]), not cover, not a free
           climb (klfc_c.active), and only movement ids 2 / 3 (Stand / BaseMove: klfreeclimb.c klfc_precond). Rappel and downed states are not
           read here (klrappel.c / kldown.c are included later): ASSUMPTION that their movement ids are not 2 / 3. A scripted camera is NOT excluded
           by the locator test (that is the player's own camera): only by the [gd+0x4cd8] gate above (ASSUMPTION). */
        klh_rd(P + 0x2720, &kind, 1); klh_rd(P + 0x2954, &cov, 1); mv = klfc_movid(P);
        loco = (kind & 2) && !cov && (mv == 2 || mv == 3) && !klh_rd32(P + 0xd50) && !klh_rd32(P + 0xd44) && !klfc_c.active;
        stuck = 0;
        if (alive && loco && dt < 0.1f && kc.pv && kc.vP > 200.0f && kc.vE < 20.0f) kc.stuckS += dt; else kc.stuckS = 0;
        stuck = kc.stuckS > 1.0;
        if (alive) {
            if (loco) klcam_unstick(P, cam, dt, stuck, blocked, cd);
            klcam_cover(gd, P, cam, dt);
            klcam_recover(P, cam, dt, E, Pv, feet, blocked, cd);
        }
    }
    /* ---- F4: the measurement */
    klh_rd(cam + 0xb9c, &sideb, 4); klh_rd(cam + 0x5a0, &blend, 4); klh_rd(P + 0x280c, &side, 1); klh_rd(P + 0x2954, &cs, 1);
    if (!klcam_nodepos(cam, node)) node[0] = node[1] = node[2] = 0;
    { DWORD nd = klh_rd32(cam + 0x24); if (nd) klh_rd(nd + 0x70, &fov, 4); }
    {
        DWORD profp = klh_rd32(cam + 0xb2c); long want = (long)klh_rd32(P + 0x29a0); int blk = blocked != 0;
        int ev = 0; char why[160]; int n = 0; why[0] = 0;
        if (kc.c.log && kc.ev_profp != profp) { n += snprintf(why + n, sizeof why - n, " profile %08lx->%08lx", kc.ev_profp, profp); ev = 1; }
        if (kc.c.log && kc.ev_side != (long)side) { n += snprintf(why + n, sizeof why - n, " side %ld->%u", kc.ev_side, (unsigned)side); ev = 1; }
        if (kc.c.log && kc.ev_cs != (long)cs) { n += snprintf(why + n, sizeof why - n, " coverside %ld->%u", kc.ev_cs, (unsigned)cs); ev = 1; }
        if (kc.c.log && kc.ev_stuck != stuck) { n += snprintf(why + n, sizeof why - n, " %s", stuck ? "STUCK begins" : "stuck ends"); ev = 1; }
        if (kc.c.log && kc.ev_blk != blk) { n += snprintf(why + n, sizeof why - n, " blocked %d->%d", kc.ev_blk, blk); ev = 1; }
        if (ev) klog("camev:%s | f %ld dt %.4f x-off %.1f sideblend %.2f want %ld eye %.1f %.1f %.1f", why, frame, dt, klfc_f(cam + 0x530), sideb, want, E[0], E[1], E[2]);
        kc.ev_profp = profp; kc.ev_side = side; kc.ev_cs = cs; kc.ev_stuck = stuck; kc.ev_blk = blk;
        if (kc.c.log) {
            LONGLONG period = kc.qf.QuadPart / kc.c.loghz;
            kc.sum_t += dt; if (dt > 0.033f) kc.sum_hitch++;
            if (stuck) kc.sum_stuck += dt;
            { double dd = klcam_hdist(E, feet); if (dd > kc.sum_maxd) kc.sum_maxd = dd; }
            if (blocked && cd > 0 && cd < kc.rc_cd - 3.0f) kc.sum_pull++;
            if (kc.vE > 5.0f && kc.pv) { float tau = klcam_dist(E, Pv) / kc.vE; kc.sum_taus += tau; kc.sum_taun++; if (tau > kc.sum_taumax) kc.sum_taumax = tau; }
            kc.sum_n++;
            if (!kc.qlast.QuadPart || now.QuadPart - kc.qlast.QuadPart >= period) {
                DWORD profp2 = profp; float t[3]; BYTE sysb = 0; DWORD db = klh_rd32(sys + 0xac);
                t[0] = klfc_f(profp2 + 0x170); t[1] = klfc_f(profp2 + 0x174); t[2] = klfc_f(profp2 + 0x178);
                if (db) klh_rd(db + 0xbc, &sysb, 1);
                klog("cam: f %ld dt %.4f%s | P %.1f %.1f %.1f vP %.0f | eye %.1f %.1f %.1f vE %.0f node %.1f %.1f %.1f | piv398 %.1f %.1f %.1f dPiv %.1f | b0 %.1f %.1f %.1f | hdist %.1f 3d %.1f | blk %u en7eb %u cd %.1f | blend %.2f sideblend %.2f side %u want %ld cs %u 818b10 %lu b84 %ld | prof %08lx t %.2f/%.2f/%.2f fov %.3f | tick %ld sysb %u flag4cd8 %lu%s",
                     frame, dt, dt > 0.033f ? " HITCH" : "", feet[0], feet[1], feet[2], kc.vP, E[0], E[1], E[2], kc.vE, node[0], node[1], node[2], Pv[0], Pv[1], Pv[2], klcam_dist(E, Pv),
                     Pv2[0], Pv2[1], Pv2[2], klcam_hdist(E, feet), klcam_dist(E, feet), (unsigned)blocked, (unsigned)klh_rd32(cam + 0x7eb) & 0xff, cd, blend, sideb, (unsigned)side, want, (unsigned)cs,
                     (unsigned long)(klh_rd32(P + 0x818) >> 10 & 1), (long)klh_rd32(P + 0xb84), profp, t[0], t[1], t[2], fov, (long)klh_rd32(cam + 0xc54), (unsigned)sysb,
                     (unsigned long)(klh_rd32(gd + 0x4cd8) & 0xff), stuck ? " STUCK" : "");
                kc.qlast = now;
            }
            if (kc.sum_t >= 10.0) {
                klog("cam: 10 s: frames %ld, hitch frames %ld, stuck %.1f s, max hdist %.1f, pull-in frames %ld, tau mean %.3f max %.3f s (%ld samples), cover swaps seen in log above",
                     kc.sum_n, kc.sum_hitch, kc.sum_stuck, kc.sum_maxd, kc.sum_pull, kc.sum_taun ? kc.sum_taus / kc.sum_taun : -1.0, kc.sum_taumax, kc.sum_taun);
                kc.sum_t = kc.sum_stuck = kc.sum_maxd = 0; kc.sum_hitch = kc.sum_pull = kc.sum_n = kc.sum_taun = 0; kc.sum_taumax = 0; kc.sum_taus = 0;
            }
        }
    }
    memcpy(kc.peye, E, 12); memcpy(kc.pfeet, feet, 12); kc.pv = 1; kc.pdt = dt;
    if (!kc.rc_d) { kc.rc_d = klcam_dist(E, Pv); kc.rc_cd = cd; }
    (void)Pv2;
}

static void klcam_init(void)
{
    struct klcam_cfg *c = &kc.c;
    memset(&kc, 0, sizeof kc);
    QueryPerformanceFrequency(&kc.qf);
    c->enable = klcam_ini_i("Enable", 1) != 0;
    if (!c->enable) return;
    c->log = klcam_ini_i("Log", 0) != 0;
    c->loghz = klcam_ini_i("LogHz", 20); if (c->loghz < 1) c->loghz = 1; if (c->loghz > 120) c->loghz = 120;
    c->blend = klcam_ini_i("Blend", 1) != 0;
    c->blendscale = klcam_ini_f("BlendScale", 0.4f, 0.1f, 1.0f);
    c->unstick = klcam_ini_i("Unstick", 1) != 0;
    c->recover = klcam_ini_i("Recover", 0) != 0;
    c->recoverspeed = klcam_ini_f("RecoverSpeed", 350.0f, 50.0f, 5000.0f);
    c->shouldercover = klcam_ini_i("ShoulderCover", 1) != 0;
    c->scoronline = klcam_ini_i("ShoulderCoverOnline", 0) != 0;
    c->leanfollow = klcam_ini_i("LeanFollow", 0) != 0;
    c->cine = klcam_ini_i("Cine", 1) != 0;
    c->cineaim = c->cine && klcam_ini_i("CineAim", 1) != 0;
    c->fliptime = klcam_ini_f("FlipTime", 0.35f, 0.0f, 5.0f);
    c->shakescale = klcam_ini_f("ShakeScale", 0.8f, 0.0f, 2.0f);
    c->fovstep = klcam_ini_f("FovStep", 0.20f, 0.01f, 1.0f);
    klog("cam: on: Blend %d (x%.2f) Unstick %d Recover %d (%.0f cm/s) ShoulderCover %d CineAim %d Log %d (%d Hz); FlipTime / ShakeScale / FovStep have no effect in this build",
         c->blend, c->blendscale, c->unstick, c->recover, c->recoverspeed, c->shouldercover, c->cineaim, c->log, c->loghz);
}

#endif /* KLCAM_C */
