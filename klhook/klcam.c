/*
 * klcam.c - the camera rework ([Camera] in KLHook.ini): faster, steadier follow, the shoulder key in cover and in cover
 * aim, softer cover-aim blends, and a measurement log. Design: re\camera.md. NOTHING HERE HAS RUN IN THE GAME.
 * The owner, 2026-10-17: "the camera glitches and stays stuck and takes forever to follow your character; change shoulder
 * in cover and when you aim in cover; more smooth, like a cinematic experience".
 * Part of KLHook (included by klhook.c after klshoulder.c, SHIP and TEST alike; uses klshoulder.c's klo_input and
 * klfreeclimb.c's klfc_guard / KLFC_CALL / klfc_f).
 * ROUND 2 (2026-10-17, static research, re\camera.md "Round 2: implementation"): LeanFollow, three more stuck remedies, the cinematic
 * knobs that have a DATA route (FlipTime, FovStep, ShakeScale) and the extended measurement log. NOTHING OF IT HAS RUN EITHER.
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
 *               LeanFollow (round 2, below) makes the body follow.
 *               The stock handler applies the side with 0 seconds (0x640176 fldz): the camera's own sweep (0x9088c0) is the
 *               only smoothing. ASSUMPTION that the cover state re-seats harmlessly on the changed bit (re\camera.md 4.1).
 *  F2b LeanFollow (round 2; default 1, offline only, local player only) The body leans by the COVER side bit [P+0x438] bit 10, not by
 *               the camera bit [P+0x818] bit 10 (READ 0x544780: 0x438 bit 10 is copied every frame from [P+0xb90] & 0x20). After a successful swap the
 *               cover state SC = [P+0xdd0] is checked ([SC] == vtable 0xbb5b6c, [SC+0x44] == 8, [SC+0x100] == P, [P+0x6b4] == SC, [P+0xb64] == 0,
 *               and with LeanGate the clearance bit of [P+0x2d6c] for the new side, bit 4 left / bit 8 right: that mapping is an ASSUMPTION), and bit
 *               0x20 of [P+0xb90] is set (left) / cleared (right). The game's own decider 0x89fd90 then sees SC+0x105 differ and re-seats the state
 *               (action 1 / 2 of StandCover slot 14, 0x71f050). The write is re-asserted for 0.6 s; when SC+0x105 does not follow, [P+0xb90] is put
 *               back and the camera-only swap stays (round 1); two such failures switch LeanFollow off. [P+0xb90] is replicated state: this is
 *               why it is offline only. No code is called or patched. ASSUMPTION: polarity (bit set = left = bit 10 of [P+0x818] set).
 *  F3a CineAim  The cover-aim profile +3 (0x154ace8): timings 0.1 / 0.5 / 0.2 -> 0.25 / 0.5 / 0.35, FOV [+0x15c] 0.698 -> 0.80
 *               (the FOV is at +0x15c with the flag byte +0x150; 0x5ea72f copies it to cam+0x550: READ; re\camera.md said
 *               +0x550, which is the camera's field). Refused when the values differ.
 *  F3b FlipTime (round 2) The shoulder sweep 0x9088c0 reads its duration from the floats 0xceb5e0 (0.2, normal) and 0xceb5e4 (0.1, byte
 *               [cam+0x640] set: the aiming case, ASSUMPTION) directly (READ 0x9088dd / 0x9088e5; step = dt / t at 0x9089ab). They are in
 *               .data (0xcd7000..), NOT .rdata. FlipTime=<s> writes e0 = FlipTime and e4 = 0.5 x FlipTime (capped at the stock 0.1). 0 = off.
 *               Checked against the stock values first. CORRECTION (review, READ 0x9088f9..0x90892c): 0xceb5e8 (0.8) REPLACES the time when the owner's
 *               movement id ([vt+0x5d8]) is 8 (cover) AND 0x88c5e0 is true AND 0x492ff0 is false, i.e. SC+0xf8 (cover substate) in {14, 15, 30, 31}
 *               (tables READ at 0x88c604/0x88c60c and 0x493014/0x49301c). In those substates the flip still takes 0.8 s whatever FlipTime says. It is left
 *               unchanged by default (what those substates are is UNKNOWN: GUESS a larger swing); FlipTimeSpecial=<s> (default 0 = unchanged) writes it.
 *               The SIDEBLEND log line shows the achieved time: 0.8 there means this case.
 *  F3c ShakeScale (round 2) The hand-held shaker S = [P+0x2c8c] (heap, no vptr; created at 0x692e30..0x692e8f) has a table of 41 float
 *               multipliers at S+0x34 (read by 0x510500). All of them are multiplied by ShakeScale (ShakeKeep lists indices left unscaled:
 *               the state -> name order is NOT known, so explosion / hit states are scaled too: GUESS (that the table at 0x510500 is the one that also drives
 *               the explosion states of the shaker is NOT verified); the table is logged once to pick indices).
 *  F3d FovStep (round 2) The channel at cam+0x790 (0x806d40) divides by its step interval T = [cam+0x7a4] (stock 1/30, set from the
 *               .rdata float 0xb3c404 at 0x6470c1). FovStep = factor on T (1.0 = stock, default 1.8: GUESS); T is a per-camera heap float.
 *               GUESS (not verified): that this channel is the FOV one; nothing here shows what it smooths. The Log's FOV lines tell.
 *  NOT DONE: look smoothing and pitch limits (the rig behind 0x653e00 / 0x7d72c0 was not traced: no data route known), the base-offset
 *               constants .data 0xceb590.. (roles only inferred: not written), F1d the smoothing reset (code).
 *  F1d Unstick, round 2 (each behind Unstick, offline only, each with its own camev line):
 *       R1 UnstickFilter (default 1) the chaser filters (cam+0x658 / 0x68c / 0x6c0 / 0x6f4 / 0x728 / 0x75c, substep h at +0x30, stock 0.005 =
 *          .rdata 0xb23bcc) run trunc(dt / h) substeps clamped to 1..10 (READ 0x5a3150), so at most 0.05 s of camera time passes per frame:
 *          below 20 fps the camera crawls. While the smoothed frame time stays above 0.05 s, h is raised to dtavg / 8 (0.0075 .. 0.02) and
 *          put back below 0.04 s. GUESS: the filter's coefficients (0x51b430) do not cache h; a chaser whose h does not read 0.005 is left alone.
 *       R2 UnstickGate (default 0 = log only) a freeze episode that lasts 1 s with a gate value abnormal ([cam+0x30] == 0 or [cam+0xc54] != 0):
 *          with UnstickGate=1 the BYTE [cam+0x30] = 1 and, when the dword [cam+0xc54] <= 0, [cam+0xc54] = 4 are written (READ 0x65016e / 0x650178: the
          tick returns early on byte == 0 or counter <= 0 (jle); 0 would freeze it).
 *       R3 UnstickTarget (default 0 = log only) [cam+0x540] (the owner player; READ 0x9088ce) no longer equals P for 0.5 s: with
 *          UnstickTarget=1 it is rewritten to P.
 *       R4/R5 (the +0x124 rest value, the filter taus) are NOT written: their rest value / writer is unknown.
 *  F4  Log      "cam:" lines at LogHz, "camev:" at every change, a 10 s summary. Read only. Round 2 adds (re\camera.md R2.3): raw dt, HITCH / GAP / SKIP
 *               events, a per-field freeze watch with STUCK2 / LAG2 episodes and a camdump, the live chase constants, BLEND / FOV / EYE /
 *               SIDEBLEND settle events, key edges (GetAsyncKeyState; X RMB LMB C LSHIFT, F9 = MARK) with the stock gate verdict, COVER enter /
 *               leave with +1 s / +3 s snapshots and SWAP+0.5 s. tools\kl_camlog.py summarises them.
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
    int leangate, ufilter, ugate, utarget, logkeys;
    float blendscale, recoverspeed, fliptime, fliptimespecial, shakescale, fovstep;
    BYTE shakekeep[41];
};
struct klcam_rest { DWORD at; float orig; };
/* the extended log's state (round 2) */
struct klcam_pend { double left; char tag[16]; };
struct klcam_xs {
    int have0; LARGE_INTEGER t0, qprev; double T;
    int skip; double skip_s; DWORD skip_a, skip_b;
    BYTE prev[8][12]; double same[8]; int prev_ok;
    double still_s, lag_s, lag_base; int ep, lagep; double ep_s, lag_ep_s; float ep_eye0[3];
    DWORD snap_prof; BYTE snap_cs, snap_blk, snap_side; float snap_blend; long snap_tick, snap_b84; int snap_keys;
    int dump_n; double dump_win;
    int keys, mark_n; BYTE cs_prev; int cs_init;
    struct klcam_pend pend[6];
    float b_prev; int blend_on; double blend_s; DWORD blend_prof;
    float fov_prev, fov_from; int fov_move, fov_calm; double fov_s; char fov_why[16];
    float sb_prev, sb_from, sb_x0; int sb_move, sb_calm; double sb_s; BYTE sb_s0;
    double eye_wait; int eye_wait_on;
    int n_ep, n_lag, n_big, n_swap, n_swapfail; double max_blend, max_fov, max_sb, lag_tot;
    double low_s;
    char why[64];
};

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
    /* round 2 */
    DWORD sc; int ln_pend, ln_fail, ln_off, ln_told; double ln_t; DWORD ln_b90o; int ln_tgt;
    double dtavg; int h_ok[6], h_checked, h_boost, h_refused, h_probes; DWORD h_cam, h_retry; float h_orig[6];
    double ug_s, tg_s; int ug_ep, tg_ep;
    int fl_state; float fl_orig[3]; int fl_told;                  /* 0 not read, 1 on, 2 refused */
    DWORD fv_cam; float fv_orig; int fv_state;
    DWORD sh_obj; float sh_orig[41]; int sh_state, sh_told;
    DWORD cine_check;
    struct klcam_xs x;
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

/* the cover movement state of P, or 0 (round 2). READ by klfreeclimb.c's klfc_movid (mover = [P+0x6b4], id = [mover+0x44]) and the research:
   cached pointer [P+0xdd0], vtable 0xbb5b6c, id 8, back pointer [SC+0x100] == P; active only while [P+0x6b4] == SC */
static DWORD klcam_sc(DWORD P)
{
    DWORD sc = klh_rd32(P + 0xdd0);
    if (!sc || klh_rd32(sc) != (DWORD)(DWORD_PTR)KLH_VA(0x00bb5b6cu) || klh_rd32(sc + 0x44) != 8 || klh_rd32(sc + 0x100) != P || klh_rd32(P + 0x6b4) != sc) return 0;
    return sc;
}

/* keys (read-only; the game reads DirectInput, so this changes nothing). user32 is looked up, not linked (kladren.c does the same) */
static SHORT (WINAPI *klcam_aks)(int);
static HWND (WINAPI *klcam_fgw)(void);
static DWORD (WINAPI *klcam_wtp)(HWND, LPDWORD);
static int klcam_key(int vk)
{
    static int tried; DWORD pid = 0; HWND fg;
    if (!tried) {
        HMODULE u = GetModuleHandleA("user32.dll"); tried = 1;
        if (u) { klcam_fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); klcam_wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); klcam_aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); }
        if (!klcam_fgw || !klcam_wtp || !klcam_aks) klog("cam: user32's key functions not found: the KEY / MARK lines are off");
    }
    if (!klcam_fgw || !klcam_wtp || !klcam_aks || !(fg = klcam_fgw())) return 0;
    klcam_wtp(fg, &pid);
    return pid == GetCurrentProcessId() && (klcam_aks(vk) & 0x8000) != 0;
}

/* raw dwords of a game structure, 16 per line (read only) */
static void klcam_dump(const char *tag, DWORD base, DWORD from, DWORD to)
{
    DWORD o;
    for (o = from; o < to; o += 64) {
        char b[16 * 9 + 1]; int i, n = 0;
        for (i = 0; i < 16 && o + 4 * i < to; i++) { DWORD w; if (!klh_rd(base + o + 4 * i, &w, 4)) w = 0xdeadbeefu; n += snprintf(b + n, sizeof b - n, "%08lx ", w); }
        klog("camdump: %s+0x%lx: %s", tag, o, b);
    }
}
/* at most 3 dumps a minute */
static int klcam_dump_ok(double T)
{
    if (T - kc.x.dump_win >= 60.0) { kc.x.dump_win = T; kc.x.dump_n = 0; }
    return kc.x.dump_n++ < 3;
}
static void klcam_dumps(DWORD P, DWORD cam)
{
    klcam_dump("cam", cam, 0x120, 0x160); klcam_dump("cam", cam, 0x390, 0x3d0); klcam_dump("cam", cam, 0x500, 0x540);
    klcam_dump("cam", cam, 0x590, 0x5b0); klcam_dump("cam", cam, 0xb20, 0xb60); klcam_dump("cam", cam, 0xc50, 0xcb0);
    klcam_dump("P", P, 0x810, 0x820); klcam_dump("P", P, 0x2940, 0x2980); klcam_dump("P", P, 0xb80, 0xb90);
}

/* a snapshot line due in <secs> of frame time (SWAP+0.5s, COVER+1.0s, COVER+3.0s) */
static void klcam_pend_add(double secs, const char *tag)
{
    int i;
    if (!kc.c.log) return;
    for (i = 0; i < 6; i++) if (kc.x.pend[i].left <= 0) { kc.x.pend[i].left = secs; snprintf(kc.x.pend[i].tag, sizeof kc.x.pend[i].tag, "%s", tag); return; }
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

/* ---------------------------------------------------------------- F2b: LeanFollow (round 2) */

/* ASSUMPTIONS here (not verified): the clearance bits of [P+0x2d6c] (bit 4 = left, bit 8 = right), the polarity (b90 bit 0x20 set = left), and that
   [P+0xccc] (read at 0x5ed5c0 among others) / [P+0x29a4] need no mirror: they are only logged.
   after a successful swap: tell the cover state which side the shoulder is on, through the game's own source [P+0xb90] bit 0x20 (see the header) */
static void klcam_lean_start(DWORD P, DWORD bit)
{
    DWORD sc, clr, b90, nb, need, old;
    /* offline only: [P+0xb90] is replicated button state (review: ShoulderCoverOnline=1 lets klcam_cover run in a network session) */
    if (!kc.c.leanfollow || kc.ln_off || kl_online()) return;
    if (!(sc = klcam_sc(P))) { klog("camev: LEAN skipped: no valid cover state object at [P+0xdd0] (camera-only swap)"); return; }
    if (klh_rd32(P + 0xb64) != 0) { klog("camev: LEAN skipped: [P+0xb64] = %08lx, not 0 (camera-only swap)", klh_rd32(P + 0xb64)); return; }
    clr = klh_rd32(P + 0x2d6c); need = bit ? 4u : 8u;                 /* ASSUMPTION: bit 4 = left, bit 8 = right clearance */
    if (kc.c.leangate && !(clr & need)) { klog("camev: LEAN skipped: clearance [P+0x2d6c] = %08lx has no bit %lu for the %s side (camera-only swap)", clr, need, bit ? "left" : "right"); return; }
    b90 = klh_rd32(P + 0xb90); nb = bit ? (b90 | 0x20u) : (b90 & ~0x20u);
    /* polarity check (review): the write is only meaningful if the polarity ASSUMPTION (bit 0x20 of [P+0xb90] set = left = bit 10 of [P+0x818] set)
       holds in the live state BEFORE the swap: the old side (the opposite of the new bit) must equal both b90 bit 0x20 and SC+0x105. Otherwise a
       mismatch would flip the lean to the WRONG side: skip (camera-only swap). */
    old = bit ? 0u : 1u;
    {
        BYTE s105b = 0xff; klh_rd(sc + 0x105, &s105b, 1);
        if (((b90 >> 5) & 1u) != old || (DWORD)s105b != old) {
            klog("camev: LEAN skipped: polarity check failed: old side %lu, b90 bit5 %lu, SC+0x105 %u, b90 %08lx (camera-only swap)", old, (b90 >> 5) & 1u, (unsigned)s105b, b90);
            return;
        }
    }
    kc.sc = sc; kc.ln_b90o = b90; kc.ln_tgt = (int)bit; kc.ln_t = 0;
    if (nb != b90 && !klh_data((void *)(DWORD_PTR)(P + 0xb90), &nb, 4, "cover lean side source (bit 0x20 of [P+0xb90])")) { klog("camev: LEAN write refused"); return; }
    kc.ln_pend = 1;
    klog("camev: LEAN start: [P+0xb90] %08lx -> %08lx (want %s), SC %08lx st104 %u st105 %u st10c %lu, clearance %08lx | [P+0xccc] %08lx [P+0x29a4] %02x (read, not written: whether they mirror the lean is UNKNOWN)",
         b90, nb, bit ? "left" : "right", sc, (unsigned)(klh_rd32(sc + 0x104) & 0xff), (unsigned)(klh_rd32(sc + 0x105) & 0xff), klh_rd32(sc + 0x10c), clr, klh_rd32(P + 0xccc), (unsigned)(klh_rd32(P + 0x29a4) & 0xff));
}
/* put bit 0x20 of [P+0xb90] back to what it was before LEAN start (review). NOT done after a successful LEAN: there the new bit matches the re-seated
   state, and putting the old one back would make the decider (0x89fd90) re-seat the state to the OLD side again. P is checked to still be a ZFFPlayer. */
static void klcam_lean_putback(DWORD P)
{
    DWORD b90, nb;
    if (!P || klh_rd32(P) != KLCAM_PL_VT) return;
    b90 = klh_rd32(P + 0xb90); nb = (b90 & ~0x20u) | (kc.ln_b90o & 0x20u);
    if (nb != b90) klh_data((void *)(DWORD_PTR)(P + 0xb90), &nb, 4, "cover lean side source put back");
}
static void klcam_lean_tick(DWORD P, float dt)
{
    DWORD sc; BYTE s105 = 0, s104 = 0;
    if (!kc.ln_pend) return;
    if (kl_online()) { klcam_lean_putback(P); kc.ln_pend = 0; return; }
    sc = klcam_sc(P);
    if (!sc || sc != kc.sc) { klcam_lean_putback(P); kc.ln_pend = 0; klog("camev: LEAN ends: the cover state is gone before it followed (left cover?)"); return; }
    klh_rd(sc + 0x105, &s105, 1); klh_rd(sc + 0x104, &s104, 1);
    kc.ln_t += dt;
    if ((int)s105 == kc.ln_tgt) {
        kc.ln_pend = 0; kc.ln_fail = 0;
        klog("camev: LEAN ok after %.2f s: st105 %u st104 %u st10c %lu b90 %08lx", kc.ln_t, (unsigned)s105, (unsigned)s104, klh_rd32(sc + 0x10c), klh_rd32(P + 0xb90));
        return;
    }
    if (kc.ln_t < 0.6) {                                              /* re-assert while something may overwrite the source */
        DWORD b90 = klh_rd32(P + 0xb90), nb = kc.ln_tgt ? (b90 | 0x20u) : (b90 & ~0x20u);
        if (nb != b90) klh_data((void *)(DWORD_PTR)(P + 0xb90), &nb, 4, "cover lean side source re-asserted");
        return;
    }
    kc.ln_pend = 0;
    klcam_lean_putback(P);                                             /* a failed experiment leaves nothing behind */
    if (++kc.ln_fail >= 2) { kc.ln_off = 1; klog("camev: LEAN FAILED twice (st105 %u, wanted %d, st104 %u): LeanFollow off for this run (camera-only swap)", (unsigned)s105, kc.ln_tgt, (unsigned)s104); }
    else klog("camev: LEAN did not follow in 0.6 s (st105 %u, wanted %d, st104 %u): [P+0xb90] put back", (unsigned)s105, kc.ln_tgt, (unsigned)s104);
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
            kc.x.n_swap++; klcam_lean_start(P, bit1);
            klcam_pend_add(0.5, "SWAP+0.5s");
            klog("camev: shoulder swapped in cover: side bit %lu -> %lu (side byte %u), want %lu -> %lu, coverside %u, b84 %ld -> %ld, cam blend %.2f, cam profile %08lx. "
                 "ASSUMPTION: the cover state's own exit (0x71f3df forces the side from state+0x104) may override b84 - read the 'coverside 1->0' camev line that follows",
                 bit0, bit1, (unsigned)(klh_rd32(P + 0x280c) & 0xff), w0, w1, (unsigned)cs, (long)b84, (long)klh_rd32(P + 0xb84), klfc_f(cam + 0xb9c), klh_rd32(cam + 0xb2c));
        } else { kc.x.n_swapfail++; klog("camev: shoulder key in cover: the side bit did not change (%lu; key no longer down, or another gate); want %lu -> %lu", bit0, w0, w1); }
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

/* ---------------------------------------------------------------- F1d (round 2): the further stuck remedies */

static const DWORD klcam_chasers[6] = { 0x658, 0x68c, 0x6c0, 0x6f4, 0x728, 0x75c };

/* R1: the six chaser filters run trunc(dt / h) substeps of h (stock 0.005, [f+0x30]) clamped to 1..10 (READ 0x5a3150 via 0x4a0570): at most
   0.05 s of camera time per frame. While the smoothed frame time stays above 0.05 s (below 20 fps, or for a few frames after a hitch) h is
   raised to dtavg / 8 so 8 substeps cover the frame; below 0.04 s it is put back. GUESS: the coefficients (0x51b430) are not cached from h. */
/* put the substeps back (also when the player is down: the boost must not outlive the situation that asked for it) */
static void klcam_filter_off(DWORD cam)
{
    int i;
    if (!kc.h_boost || cam != kc.h_cam) return;
    for (i = 0; i < 6; i++) {
        float cur;
        if (!kc.h_ok[i]) continue;
        cur = klfc_f(cam + klcam_chasers[i] + 0x30);
        if (!klcam_near(cur, kc.h_orig[i], 1e-7f)) klh_data((void *)(DWORD_PTR)(cam + klcam_chasers[i] + 0x30), &kc.h_orig[i], 4, "camera chaser filter substep put back");
    }
    kc.h_boost = 0;
    if (kc.c.log) klog("camev: FILTER substep put back (player not alive)");
}
static void klcam_filter(DWORD cam, float rawdt)
{
    int i, want, nok = 0; float hv, cur; double a = kc.dtavg; DWORD gt = GetTickCount();
    if (!kc.c.unstick || !kc.c.ufilter || kl_online()) return;
    /* a refusal is per camera and not permanent (review): the probe may have read a camera still under construction. The same camera is probed
       again every 3 s (at most 5 times, the log line only the first 2 times); a different camera is probed at once. */
    if (kc.h_refused) {
        if (cam == kc.h_cam && (gt - kc.h_retry < 3000 || kc.h_probes >= 5)) return;
        kc.h_refused = 0;
    }
    if (cam != kc.h_cam || !kc.h_checked) {
        char b[160]; int n = 0;
        if (cam != kc.h_cam) kc.h_probes = 0;
        kc.h_cam = cam; kc.h_boost = 0; kc.h_checked = 1; kc.h_probes++;
        for (i = 0; i < 6; i++) {
            float h = klfc_f(cam + klcam_chasers[i] + 0x30);
            kc.h_ok[i] = klcam_fin(h) && h >= 0.003f && h <= 0.0075f;      /* stock 0.005: anything else is not the filter I read */
            kc.h_orig[i] = h; nok += kc.h_ok[i];
            n += snprintf(b + n, sizeof b - n, " %.4f", h);
        }
        if (kc.h_probes <= 2 || nok) klog("cam: UnstickFilter: substep h of the 6 chasers (cam+0x658 .. 0x75c, +0x30) reads%s; %d usable%s", b, nok, nok ? "" : " - feature off for now (probed again in 3 s)");
        if (!nok) { kc.h_refused = 1; kc.h_retry = gt; kc.h_checked = 0; return; }
    }
    want = kc.h_boost ? a > 0.04 : a > 0.05;
    hv = (float)(a / 8.0); if (hv < 0.0075f) hv = 0.0075f; if (hv > 0.02f) hv = 0.02f;
    /* never above the real frame time (review): the count is trunc(dt / h) clamped to 1..10, so on a frame faster than the average an h above dt
       would still run one full substep and advance the filter by more than the frame lasted. The floor 0.002 keeps h sane. */
    if (rawdt > 0 && hv > rawdt) hv = rawdt < 0.002f ? 0.002f : rawdt;
    for (i = 0; i < 6; i++) {
        if (!kc.h_ok[i]) continue;
        cur = klfc_f(cam + klcam_chasers[i] + 0x30);
        if (want) { if (!klcam_near(cur, hv, 1e-6f)) klh_data((void *)(DWORD_PTR)(cam + klcam_chasers[i] + 0x30), &hv, 4, "camera chaser filter substep (low frame rate)"); }
        else if (kc.h_boost && !klcam_near(cur, kc.h_orig[i], 1e-7f)) klh_data((void *)(DWORD_PTR)(cam + klcam_chasers[i] + 0x30), &kc.h_orig[i], 4, "camera chaser filter substep put back");
    }
    if (want != kc.h_boost) {
        kc.h_boost = want;
        if (kc.c.log) klog("camev: FILTER substep %s: frame time avg %.4f s, h %.4f (stock %.4f)", want ? "raised" : "put back", a, want ? hv : kc.h_orig[0], kc.h_orig[0]);
    }
}

/* R2 (log; writes only with UnstickGate=1) and R3 (log; writes only with UnstickTarget=1). frozen = a freeze episode is open (STUCK2) */
static void klcam_gates(DWORD P, DWORD cam, float dt, int frozen)
{
    DWORD c54 = klh_rd32(cam + 0xc54), own = klh_rd32(cam + 0x540); BYTE g30b = 1; DWORD g30;
    if (!kc.c.unstick) return;
    klh_rd(cam + 0x30, &g30b, 1); g30 = g30b;                  /* a BYTE: the tick gate tests "cmp byte ptr [esi+0x30], 0" (READ 0x65016e) */
    if (frozen) kc.ug_s += dt; else { kc.ug_s = 0; kc.ug_ep = 0; }
    if (kc.ug_s > 1.0 && !kc.ug_ep) {
        DWORD sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)), db = sys ? klh_rd32(sys + 0xac) : 0; BYTE sysb = 0xff;
        if (db) klh_rd(db + 0xbc, &sysb, 1);
        kc.ug_ep = 1;
        klog("camev: GATE frozen for %.1f s: [cam+0x30] %08lx [cam+0xc54] %08lx [cam+0x504] %08lx [cam+0x540] %08lx (P %08lx) sysb %02x%s",
             kc.ug_s, g30, c54, klh_rd32(cam + 0x504), own, P, (unsigned)sysb, (g30b == 0 || (int)c54 <= 0) ? " ABNORMAL" : "");
        /* READ 0x65016e..0x65017f: the camera tick returns early (0x650389) when byte [cam+0x30] == 0 OR dword [cam+0xc54] <= 0 (jle). 0x6501a8 counts the
           counter down while the system byte is set; 0x6500d9 sets it to 4. So the remedy is byte 1 and counter 4 (round 1's ladder step 1), never 0. */
        if ((g30b == 0 || (int)c54 <= 0) && kc.c.ugate && !kl_online()) {
            BYTE one = 1; DWORD four = 4;
            if (g30b == 0) klh_data((void *)(DWORD_PTR)(cam + 0x30), &one, 1, "camera tick gate byte [cam+0x30]");
            if ((int)c54 <= 0) klh_data((void *)(DWORD_PTR)(cam + 0xc54), &four, 4, "camera tick counter [cam+0xc54]");
            klog("camev: GATE remedy written:%s%s", g30b == 0 ? " byte [cam+0x30] = 1" : "", (int)c54 <= 0 ? " [cam+0xc54] = 4" : "");
        }
    }
    if (own != P) kc.tg_s += dt; else { kc.tg_s = 0; kc.tg_ep = 0; }
    if (kc.tg_s > 0.5 && !kc.tg_ep) {
        kc.tg_ep = 1;
        klog("camev: TARGET [cam+0x540] = %08lx is not the local player %08lx for %.1f s%s", own, P, kc.tg_s, kc.c.utarget && !kl_online() ? " - rewritten" : " (log only)");
        if (kc.c.utarget && !kl_online()) klh_data((void *)(DWORD_PTR)(cam + 0x540), &P, 4, "camera owner pointer");
    }
}

/* ---------------------------------------------------------------- F3b / F3c / F3d (round 2): the cinematic knobs with a data route */

static void klcam_cine(DWORD P, DWORD cam)
{
    int i;
    if (!kc.c.cine) return;
    /* FlipTime: 0xceb5e0 / e4 are .data floats read directly by 0x9088c0 (READ) */
    if (kc.c.fliptime > 0 && kc.fl_state != 2) {
        DWORD a = (DWORD)(DWORD_PTR)KLH_VA(0xceb5e0u); float c[3], w0 = kc.c.fliptime, w1 = kc.c.fliptime * 0.5f, w2 = kc.c.fliptimespecial;
        if (w1 > 0.1f) w1 = 0.1f;                                 /* review: the aim flip is never slower than stock (0.1 s) */
        for (i = 0; i < 3; i++) c[i] = klfc_f(a + 4 * i);
        if (!kc.fl_state) {
            if (klcam_near(c[0], 0.2f, 1e-4f) && klcam_near(c[1], 0.1f, 1e-4f) && klcam_near(c[2], 0.8f, 1e-4f)) {
                for (i = 0; i < 3; i++) kc.fl_orig[i] = c[i];
                kc.fl_state = 1; klog("cam: FlipTime on: 0xceb5e0 %.2f -> %.3f, 0xceb5e4 %.2f -> %.3f (0xceb5e8 %.2f %s)", c[0], w0, c[1], w1, c[2], w2 > 0 ? "FlipTimeSpecial" : "left: cover substates 14/15/30/31 still flip in 0.8 s");
            } else {
                kc.fl_state = 2; klog("cam: FlipTime REFUSED: 0xceb5e0 / e4 / e8 read %.4f / %.4f / %.4f, not 0.2 / 0.1 / 0.8 (another build, or already changed)", c[0], c[1], c[2]);
            }
        }
        if (kc.fl_state == 1) {
            if (!klcam_near(c[0], w0, 1e-5f) && klcam_near(c[0], kc.fl_orig[0], 1e-5f)) klcam_putf(a, kc.fl_orig[0], w0, "shoulder flip time (normal)");
            if (!klcam_near(c[1], w1, 1e-5f) && klcam_near(c[1], kc.fl_orig[1], 1e-5f)) klcam_putf(a + 4, kc.fl_orig[1], w1, "shoulder flip time (aim)");
            if (w2 > 0 && !klcam_near(c[2], w2, 1e-5f) && klcam_near(c[2], kc.fl_orig[2], 1e-5f)) klcam_putf(a + 8, kc.fl_orig[2], w2, "shoulder flip time (cover substates)");
        }
    }
    /* FovStep: the per-camera step interval of the FOV channel (cam+0x7a4, stock 1/30) */
    if (kc.c.fovstep != 1.0f) {
        if (cam != kc.fv_cam) {
            float t = klfc_f(cam + 0x7a4), al = klfc_f(cam + 0x7a8);
            kc.fv_cam = cam;
            if (klcam_near(t, 1.0f / 30.0f, 2e-4f)) { kc.fv_orig = t; kc.fv_state = 1; klog("cam: FovStep on: cam+0x7a4 %.4f x %.2f = %.4f (alpha cam+0x7a8 %.3f)", t, kc.c.fovstep, t * kc.c.fovstep, al); }
            else { kc.fv_state = 2; klog("cam: FovStep REFUSED for this camera: cam+0x7a4 reads %.5f, not 1/30 (alpha %.3f)", t, al); }
        }
        if (kc.fv_state == 1) {
            float cur = klfc_f(cam + 0x7a4), w = kc.fv_orig * kc.c.fovstep;
            if (!klcam_near(cur, w, 1e-6f) && klcam_near(cur, kc.fv_orig, 1e-6f)) klh_data((void *)(DWORD_PTR)(cam + 0x7a4), &w, 4, "camera FOV channel step interval");
        }
    }
    /* ShakeScale: the 41 multipliers at S+0x34 of the shaker S = [P+0x2c8c]. Applied only after two reads 0.5 s apart agree (constants, not live values) */
    if (kc.c.shakescale != 1.0f && kc.sh_state != 2) {
        DWORD S = klh_rd32(P + 0x2c8c); float cur[41]; int bad = 0;
        if (!S || !klh_rd(S + 0x34, cur, sizeof cur)) { kc.sh_obj = 0; kc.sh_state = 0; return; }
        for (i = 0; i < 41; i++) if (!klcam_fin(cur[i]) || cur[i] < 0 || cur[i] > 10.0f) bad = 1;
        if (S != kc.sh_obj) {
            kc.sh_obj = S; kc.sh_state = bad ? 2 : 0;
            for (i = 0; i < 41; i++) kc.sh_orig[i] = cur[i];
            if (bad) { klog("cam: ShakeScale REFUSED: the table at S+0x34 (S %08lx) is not 41 floats in 0..10", S); return; }
            { char b[41 * 7 + 4]; int n = 0; for (i = 0; i < 41; i++) n += snprintf(b + n, sizeof b - n, "%.2f ", cur[i]); klog("cam: shaker %08lx table S+0x34: %s", S, b); }
            return;
        }
        if (bad) { kc.sh_state = 2; klog("cam: ShakeScale off: the table became invalid"); return; }
        if (kc.sh_state == 0) {
            for (i = 0; i < 41; i++) if (!klcam_near(cur[i], kc.sh_orig[i], 1e-6f)) bad = 1;
            if (bad) { kc.sh_state = 2; klog("cam: ShakeScale REFUSED: the table changes by itself (live values, not constants)"); return; }
            kc.sh_state = 1; klog("cam: ShakeScale on: x%.2f on the 41 entries (GUESS: explosions / hits are scaled too unless ShakeKeep lists them)", kc.c.shakescale);
        }
        for (i = 0; i < 41; i++) {
            float w = kc.c.shakekeep[i] ? kc.sh_orig[i] : kc.sh_orig[i] * kc.c.shakescale;
            if (!klcam_near(cur[i], w, 1e-6f) && klcam_near(cur[i], kc.sh_orig[i], 1e-6f)) klh_data((void *)(DWORD_PTR)(S + 0x34 + 4 * i), &w, 4, "shaker multiplier");
        }
    }
}

/* ---------------------------------------------------------------- F4 (round 2): the extended log. Reads only. */

struct klcam_fr {
    DWORD gd, P, cam, sys; float dt, rawdt, E[3], feet[3], Pv[3], b0[3], node[3], cd, blend, sideb, fov;
    BYTE blocked, side; signed char cs; int stuck; long frame; LARGE_INTEGER now; int mv;
};

static const char *klcam_pname(DWORD p)
{   /* re\firstperson_camera.md: the profile pointers by role */
    static const struct { DWORD a; const char *n; } t[] = { { 0x154ace8u, "cover-aim" }, { 0x154a9b8u, "aim" }, { 0x154b9a8u, "FA-aim" }, { 0x154b810u, "FA-default" }, { 0x154ab50u, "cover-low" } };
    int i;
    for (i = 0; i < 5; i++) if (p == (DWORD)(DWORD_PTR)KLH_VA(t[i].a)) return t[i].n;
    return "?";
}
static const char *const klcam_skipn[] = { "-", "NOPLAYER", "NOCAM", "NOSYS", "GATE4CD8", "READFAIL", "ZERODT" };
/* every silent return of the tick says so on change (wall seconds, because the frame clock may be what is missing) */
static void klcam_skip(int code, DWORD a, DWORD b)
{
    struct klcam_xs *x = &kc.x;
    if (!kc.c.log || code == x->skip) return;
    if (x->skip) klog("camev: SKIP %s ends after %.2f s | T %.2f", klcam_skipn[x->skip], x->T - x->skip_s, x->T);
    x->skip = code; x->skip_s = x->T;
    if (code) klog("camev: SKIP %s begins | T %.2f a %08lx b %08lx", klcam_skipn[code], x->T, a, b);
}

/* the state words every key / cover / mark line carries; with the cover state object the lean fields too */
static int klcam_state(char *b, int cap, const struct klcam_fr *f)
{
    DWORD sc = klcam_sc(f->P); int n;
    n = snprintf(b, cap, "cs %d side %u bit818 %lu want %ld b84 %ld camside %u mv %d prof %08lx(%s) fov %.3f blend %.2f sideb %.2f",
                 (int)f->cs, (unsigned)f->side, (unsigned long)(klh_rd32(f->P + 0x818) >> 10 & 1), (long)klh_rd32(f->P + 0x29a0), (long)klh_rd32(f->P + 0xb84),
                 (unsigned)(klh_rd32(f->cam + 0xb40) & 0xff), f->mv, klh_rd32(f->cam + 0xb2c), klcam_pname(klh_rd32(f->cam + 0xb2c)), f->fov, f->blend, f->sideb);
    if (sc && n < cap) n += snprintf(b + n, cap - n, " st104 %d st105 %d st10c %lu c2d6c %08lx b90 %08lx", (int)(signed char)(klh_rd32(sc + 0x104) & 0xff), (int)(signed char)(klh_rd32(sc + 0x105) & 0xff),
                                     klh_rd32(sc + 0x10c), klh_rd32(f->P + 0x2d6c), klh_rd32(f->P + 0xb90));
    return n;
}

/* the module's own verdict for a press of the shoulder key, from the same predicates klcam_cover tests */
static void klcam_verdict(char *b, int cap, DWORD H, BYTE cs)
{
    BYTE kind = 0, fired = 0; float tmr = 0; const char *r = 0;
    if (H) { klh_rd(H + 0x34, &kind, 1); klh_rd(H + 0x3c, &fired, 1); klh_rd(H + 0x38, &tmr, 4); }
    if (!kc.c.shouldercover) r = "ShoulderCover=0";
    else if (!kc.c.scoronline && kl_online()) r = "online";
    else if (!kc.sc_on) r = "gate bytes not as read";
    else if (kc.sc_fault >= 3) r = "disabled after faults";
    else if (!H) r = "no input record";
    else if (cs == 0) r = "not in cover (the stock handler acts)";
    else if (kind != 2) r = "record kind != 2";
    else if (kc.sc_cool > 0) r = "cooldown";
    else if (kc.cs_s <= 0.15) r = "cover entered < 0.15 s ago";
    else if (kc.sc_wait) r = "hold-off";
    snprintf(b, cap, "module=%s%s%s%s | kind %u fired %u timer %.3f cs_s %.2f", r ? "skipped(" : "would_fire", r ? r : "", r ? ")" : "", "", (unsigned)kind, (unsigned)fired, tmr, kc.cs_s);
}

/* C: the per-field freeze watch, STUCK2 / LAG2 episodes. Runs whenever Log or Unstick is on; prints only with Log. Returns 1 while a freeze episode is open. */
static int klcam_watch(const struct klcam_fr *f)
{
    struct klcam_xs *x = &kc.x;
    static const char *const nm[8] = { "P", "PIV", "B0", "EYE", "NODE", "BLEND", "TICK", "FOV" };
    static const int len[8] = { 12, 12, 12, 12, 12, 4, 4, 4 };
    BYTE cur[8][12]; DWORD tick = klh_rd32(f->cam + 0xc54); int i, active; float vPiv = 0, d; char fz[80]; int n = 0;
    memset(cur, 0, sizeof cur);
    memcpy(cur[0], f->feet, 12); memcpy(cur[1], f->Pv, 12); memcpy(cur[2], f->b0, 12); memcpy(cur[3], f->E, 12); memcpy(cur[4], f->node, 12);
    memcpy(cur[5], &f->blend, 4); memcpy(cur[6], &tick, 4); memcpy(cur[7], &f->fov, 4);
    if (x->prev_ok) {
        for (i = 0; i < 8; i++) if (!memcmp(cur[i], x->prev[i], len[i])) x->same[i] += f->dt; else x->same[i] = 0;
        vPiv = klcam_dist(f->Pv, (const float *)x->prev[1]) / f->dt;
    }
    memcpy(x->prev, cur, sizeof cur); x->prev_ok = 1;
    for (i = 0; i < 5; i++) if (x->same[i] >= 0.25) n += snprintf(fz + n, sizeof fz - n, "%s%s", n ? "," : "", nm[i]);
    if (!n) strcpy(fz, "-");
    active = kc.pv && (kc.vP > 50.0f || vPiv > 100.0f);
    d = kc.pv ? klcam_dist(f->E, x->ep_eye0) : 0;
    if (!x->ep) {
        if (kc.pv && active && f->rawdt < 0.1f && d < 0.5f) x->still_s += f->dt; else { x->still_s = 0; memcpy(x->ep_eye0, f->E, 12); }
        if (x->still_s >= 0.25) {
            x->ep = 1; x->ep_s = x->still_s; x->n_ep++;
            x->snap_prof = klh_rd32(f->cam + 0xb2c); x->snap_cs = (BYTE)f->cs; x->snap_blk = f->blocked; x->snap_side = f->side; x->snap_blend = f->blend; x->snap_tick = (long)tick;
            x->snap_b84 = (long)klh_rd32(f->P + 0xb84); x->snap_keys = x->keys;
            if (kc.c.log) {
                WORD a54 = 0; BYTE kind = 0; char st[300];
                klh_rd(f->P + 0xa54, &a54, 2); klh_rd(f->P + 0x2720, &kind, 1); klcam_state(st, sizeof st, f);
                klog("camev: STUCK2 begins frozen=%s | f %ld T %.2f rdt %.4f | P %.1f %.1f %.1f piv %.1f %.1f %.1f eye %.1f %.1f %.1f node %.1f %.1f %.1f | vP %.0f vPiv %.0f | mv %d kind %02x a54 %04x d50 %lx d44 %lx | blk %u cd %.1f | tick %ld(same %.2f) blend %.2f(same %.2f) fov same %.2f flag4cd8 %lu | %s",
                     fz, f->frame, x->T, f->rawdt, f->feet[0], f->feet[1], f->feet[2], f->Pv[0], f->Pv[1], f->Pv[2], f->E[0], f->E[1], f->E[2], f->node[0], f->node[1], f->node[2], kc.vP, vPiv, f->mv, (unsigned)kind, (unsigned)a54,
                     klh_rd32(f->P + 0xd50), klh_rd32(f->P + 0xd44), (unsigned)f->blocked, f->cd, (long)tick, x->same[6], f->blend, x->same[5], x->same[7], (unsigned long)(klh_rd32(f->gd + 0x4cd8) & 0xff), st);
                if (klcam_dump_ok(x->T)) klcam_dumps(f->P, f->cam);
            }
        }
    } else {
        x->ep_s += f->dt;
        if (d > 2.0f) {
            x->ep = 0; x->still_s = 0; memcpy(x->ep_eye0, f->E, 12);
            if (kc.c.log) {
                char df[160]; int k = 0; DWORD prof = klh_rd32(f->cam + 0xb2c);
                if (prof != x->snap_prof) k += snprintf(df + k, sizeof df - k, " prof %08lx->%08lx", x->snap_prof, prof);
                if ((BYTE)f->cs != x->snap_cs) k += snprintf(df + k, sizeof df - k, " cs %d->%d", (int)(signed char)x->snap_cs, (int)f->cs);
                if (f->blocked != x->snap_blk) k += snprintf(df + k, sizeof df - k, " blk %u->%u", (unsigned)x->snap_blk, (unsigned)f->blocked);
                if (f->side != x->snap_side) k += snprintf(df + k, sizeof df - k, " side %u->%u", (unsigned)x->snap_side, (unsigned)f->side);
                if (!klcam_near(f->blend, x->snap_blend, 0.001f)) k += snprintf(df + k, sizeof df - k, " blend %.2f->%.2f", x->snap_blend, f->blend);
                if ((long)tick != x->snap_tick) k += snprintf(df + k, sizeof df - k, " tick %ld->%ld", x->snap_tick, (long)tick);
                if (x->keys != x->snap_keys) k += snprintf(df + k, sizeof df - k, " keys %02x->%02x", x->snap_keys, x->keys);
                if (!k) strcpy(df, " (nothing watched changed)");
                klog("camev: STUCK2 ends after %.2f s frozen=%s | f %ld T %.2f | changed:%s", x->ep_s, fz, f->frame, x->T, df);
            }
        }
    }
    /* LAG2: the eye falls far behind the pivot compared with its own recent distance (distance only; the facing field is not known) */
    if (kc.pv && kc.vE > 5.0f && vPiv > 100.0f) {
        float dd = klcam_dist(f->E, f->Pv);
        if (x->lag_base <= 0) x->lag_base = dd;
        if (dd > x->lag_base + 150.0f) x->lag_s += f->dt; else { if (x->lagep && dd < x->lag_base + 75.0f) { x->lagep = 0; x->lag_tot += x->lag_ep_s; if (kc.c.log) klog("camev: LAG2 ends after %.2f s | dist %.1f base %.1f", x->lag_ep_s, dd, x->lag_base); } x->lag_s = 0; }
        if (x->lagep) x->lag_ep_s += f->dt;
        if (!x->lagep && x->lag_s > 0.5) { x->lagep = 1; x->lag_ep_s = x->lag_s; x->n_lag++; if (kc.c.log) klog("camev: LAG2 begins | f %ld T %.2f dist %.1f base %.1f vE %.0f vPiv %.0f", f->frame, x->T, dd, x->lag_base, kc.vE, vPiv); }
        if (!x->lagep) x->lag_base += (dd - x->lag_base) * (f->dt / 5.0f > 1 ? 1 : f->dt / 5.0f);
    }
    return x->ep;
}

static void klcam_log2(const struct klcam_fr *f, const char *stuck_s)
{
    struct klcam_xs *x = &kc.x;
    static const struct { int vk; const char *n; char c; } K[6] = { { 0x58, "X", 'X' }, { 0x02, "RMB", 'R' }, { 0x01, "LMB", 'L' }, { 0x43, "C", 'C' }, { 0xA0, "LSHIFT", 'S' }, { 0x78, "F9", '9' } };
    char st[360]; int i; long pflag = 0;
    (void)stuck_s; (void)pflag;
    /* F: key edges */
    if (kc.c.logkeys) {
        for (i = 0; i < 6; i++) {
            int dn = klcam_key(K[i].vk), was = (x->keys >> i) & 1;
            if (dn == was) continue;
            x->keys ^= 1 << i;
            klcam_state(st, sizeof st, f);
            if (i == 5) {
                if (dn) {
                    x->mark_n++;
                    klog("camev: MARK %d | f %ld T %.2f | %s", x->mark_n, f->frame, x->T, st);
                    if (klcam_dump_ok(x->T)) klcam_dumps(f->P, f->cam);
                }
                continue;
            }
            klog("camev: KEY %s %s | f %ld T %.2f | %s", K[i].n, dn ? "down" : "up", f->frame, x->T, st);
            if (i == 0 && dn) {
                DWORD H = klo_input(f->gd, f->P), g209 = klh_rd32((DWORD_PTR)KLH_VA(0x168d7c0u)); char vd[160]; WORD a54 = 0;
                klh_rd(f->P + 0xa54, &a54, 2); klcam_verdict(vd, sizeof vd, H, (BYTE)f->cs);
                klog("camev: KEY X gates: cfg209 %u k2720&2 %u d50 %lx a54 %04x ed0b7 %lu H330 %lx cs %d | %s", (unsigned)(g209 ? klh_rd32(g209 + 0x209) & 0xff : 0xff), (unsigned)(klh_rd32(f->P + 0x2720) & 2),
                     klh_rd32(f->P + 0xd50), (unsigned)a54, (unsigned long)(klh_rd32(f->P + 0xed0) >> 7 & 1), H ? klh_rd32(H + 0x330) : 0, (int)f->cs, vd);
            }
            if (i == 1) { strncpy(x->fov_why, dn ? "RMB down" : "RMB up", sizeof x->fov_why - 1); x->fov_s = x->T; x->fov_move = 0; }
        }
    }
    /* G: cover enter / leave, due snapshots */
    if (!x->cs_init) { x->cs_init = 1; x->cs_prev = (BYTE)f->cs; }
    if (((x->cs_prev != 0) != (f->cs != 0))) {
        klcam_state(st, sizeof st, f);
        klog("camev: COVER %s | f %ld T %.2f | %s", f->cs ? "enter" : "leave", f->frame, x->T, st);
        if (!f->cs) { klcam_pend_add(1.0, "COVER+1.0s"); klcam_pend_add(3.0, "COVER+3.0s"); }
    }
    x->cs_prev = (BYTE)f->cs;
    for (i = 0; i < 6; i++) {
        if (x->pend[i].left <= 0) continue;
        x->pend[i].left -= f->dt;
        if (x->pend[i].left <= 0) { x->pend[i].left = 0; klcam_state(st, sizeof st, f); klog("camev: %s | f %ld T %.2f x-off %.1f | %s", x->pend[i].tag, f->frame, x->T, klfc_f(f->cam + 0x530), st); }
    }
    /* E: achieved timings */
    {
        DWORD profp = klh_rd32(f->cam + 0xb2c); float t[3];
        t[0] = klfc_f(profp + 0x170); t[1] = klfc_f(profp + 0x174); t[2] = klfc_f(profp + 0x178);
        if (f->blend > 0.0001f) {
            if (!x->blend_on || profp != x->blend_prof) {
                if (x->blend_on) klog("camev: BLEND restarted by a new profile after %.2f s", x->blend_s);
                x->blend_on = 1; x->blend_s = 0; x->blend_prof = profp;
                klog("camev: BLEND start prof %08lx(%s) t %.2f/%.2f/%.2f timer %.2f | f %ld T %.2f", profp, klcam_pname(profp), t[0], t[1], t[2], f->blend, f->frame, x->T);
                strncpy(x->fov_why, "profile", sizeof x->fov_why - 1); x->fov_s = x->T; x->fov_move = 0;
            }
            x->blend_s += f->dt;
        } else if (x->blend_on) {
            x->blend_on = 0; if (x->blend_s > x->max_blend) x->max_blend = x->blend_s;
            klog("camev: BLEND end after %.2f s (prof %08lx(%s)) | f %ld T %.2f", x->blend_s, x->blend_prof, klcam_pname(x->blend_prof), f->frame, x->T);
        }
        {   /* FOV */
            float dl = f->fov - x->fov_prev; if (dl < 0) dl = -dl;
            if (!klcam_fin(f->fov) || f->fov == 0) { x->fov_prev = f->fov; }
            else {
                if (!x->fov_move) {
                    if (x->fov_prev != 0 && dl > 0.0005f) { x->fov_move = 1; x->fov_from = x->fov_prev; x->fov_calm = 0; if (x->T - x->fov_s > 3.0 || !x->fov_why[0]) { x->fov_s = x->T; strcpy(x->fov_why, "move"); } }
                } else {
                    if (dl < 0.0002f) x->fov_calm++; else x->fov_calm = 0;
                    if (x->fov_calm >= 5) {
                        double el = x->T - x->fov_s; x->fov_move = 0; if (el > x->max_fov) x->max_fov = el;
                        klog("camev: FOV %.3f -> %.3f settled after %.2f s since %s%s | f %ld T %.2f", x->fov_from, f->fov, el, x->fov_why, f->cs && (x->keys & 2) ? " (coveraim)" : "", f->frame, x->T);
                        x->fov_why[0] = 0;
                    }
                }
                x->fov_prev = f->fov;
            }
        }
        {   /* SIDEBLEND [cam+0xb9c], walked by 0x9088c0: the achieved flip time (stock 0.2 s, .data 0xceb5e0) */
            float dl = f->sideb - x->sb_prev; if (dl < 0) dl = -dl;
            if (!x->sb_move) {
                if (dl > 0.001f) { x->sb_move = 1; x->sb_from = x->sb_prev; x->sb_calm = 0; x->sb_s = x->T; x->sb_s0 = f->side; x->sb_x0 = klfc_f(f->cam + 0x530); }
            } else {
                if (dl < 0.0005f) x->sb_calm++; else x->sb_calm = 0;
                if (x->sb_calm >= 3) {
                    double el = x->T - x->sb_s; x->sb_move = 0; if (el > x->max_sb) x->max_sb = el;
                    klog("camev: SIDEBLEND %.2f -> %.2f in %.2f s (side %u -> %u, x-off %.1f -> %.1f) | f %ld T %.2f", x->sb_from, f->sideb, el, (unsigned)x->sb_s0, (unsigned)f->side, x->sb_x0, klfc_f(f->cam + 0x530), f->frame, x->T);
                }
            }
            x->sb_prev = f->sideb;
        }
        {   /* EYE settle after the player stops */
            if (kc.vP < 5.0f) { if (!x->eye_wait_on && kc.pv && x->low_s <= 0) { x->eye_wait_on = 1; x->eye_wait = x->T; } if (x->eye_wait_on && kc.vE < 5.0f) { klog("camev: EYE settled after %.2f s | f %ld T %.2f", x->T - x->eye_wait, f->frame, x->T); x->eye_wait_on = 0; x->low_s = 1; } }
            else { x->eye_wait_on = 0; x->low_s = 0; }
        }
    }
}

/* ---------------------------------------------------------------- the tick */

static void klcam_lost(void)
{
    DWORD pl_old = kc.pl;
    if (kc.have) klog("cam: no local player / camera any more");
    kc.have = 0; kc.pv = 0; kc.stuckS = 0; kc.step = 0; kc.blockS = 0; kc.rc_win = 0; kc.rc_d = 0; kc.fired0 = 0; kc.cs_s = 0; kc.pl = kc.cam = 0;
    if (kc.ln_pend) klcam_lean_putback(pl_old);
    kc.ln_pend = 0; kc.ug_s = 0; kc.tg_s = 0; kc.ug_ep = kc.tg_ep = 0;
    /* the camera object is gone: forget everything keyed to it (a stale boost / a stale refusal / a stale FOV or shaker state must not carry over) */
    kc.h_cam = 0; kc.h_boost = 0; kc.h_refused = 0; kc.h_probes = 0; kc.fv_cam = 0; kc.fv_state = 0; kc.fl_told = 0; kc.sh_obj = 0; kc.sh_state = 0;
    kc.x.prev_ok = 0; kc.x.ep = 0; kc.x.still_s = 0; kc.x.lag_base = 0; kc.x.lagep = 0; kc.x.lag_s = 0; kc.x.blend_on = 0; kc.x.fov_move = 0; kc.x.sb_move = 0; kc.x.eye_wait_on = 0;
}

static void klcam_tick(int game_thread)
{
    DWORD gd, P, cam, sys; LARGE_INTEGER now; float dt = 0, rawdt = 0, E[3], feet[3], Pv[3], Pv2[3], node[3], cd = 0, blend = 0, sideb = 0, fov = 0; BYTE blocked = 0, side = 0, cs = 0;
    long frame; int stuck = 0, frozen = 0, alive = 0; DWORD gnow, rb; struct klcam_fr f; struct klcam_xs *x = &kc.x;
    if (!kc.c.enable || !klh_exe_ok || !game_thread) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLCAM_RCB_RA)) return;
    QueryPerformanceCounter(&now);
    if (!x->have0) { x->have0 = 1; x->t0 = now; x->qprev = now; }
    x->T = (double)(now.QuadPart - x->t0.QuadPart) / (double)kc.qf.QuadPart;
    if (kc.c.log) {   /* A: a wall-clock gap between two entries means frames without the 0x87aa82 call, or a stall */
        double gap = (double)(now.QuadPart - x->qprev.QuadPart) / (double)kc.qf.QuadPart;
        if (gap > 0.25) klog("camev: GAP wall %.3f s since the last tick | T %.2f", gap, x->T);
    }
    x->qprev = now;
    if (!(P = klcam_player(&gd))) { klcam_skip(1, klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), 0); klcam_lost(); return; }
    if (!(cam = klh_rd32(P + 0xbd8)) || klh_rd32(klh_rd32(cam) - 4) != KLCAM_COL) { klcam_skip(2, cam, cam ? klh_rd32(klh_rd32(cam) - 4) : 0); klcam_lost(); return; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)))) { klcam_skip(3, 0, 0); return; }
    klh_rd(sys + 0x50, &rawdt, 4); frame = (long)klh_rd32(sys + 0x48);
    if (frame == kc.lastframe) return;                             /* once a frame */
    if (!klcam_fin(rawdt) || rawdt <= 0) { memcpy(&rb, &rawdt, 4); klcam_skip(6, rb, 0); return; }   /* a failed / zero dt read: skip the frame (no 0.001 s clamp: it made vE / vP huge) */
    if (P != kc.pl || cam != kc.cam) {                             /* a new level / respawn: the old objects are gone */
        DWORD oldpl = kc.pl;
        kc.pl = P; kc.cam = cam; kc.pv = 0; kc.stuckS = 0; kc.step = 0; kc.blockS = 0; kc.rc_win = 0; kc.rc_d = 0; kc.fired0 = 0; kc.cs_s = 0; kc.sc_cool = 0;
        if (kc.ln_pend) klcam_lean_putback(oldpl);
        kc.ln_pend = 0; x->prev_ok = 0; x->ep = 0; x->still_s = 0; x->lag_base = 0; x->lagep = 0; x->blend_on = 0; x->fov_move = 0; x->sb_move = 0;
        if (!kc.have) klog("cam: local player %08lx camera %08lx", P, cam);
        kc.have = 1;
    }
    kc.lastframe = frame;
    dt = rawdt;
    if (rawdt > 0.1f) {
        x->n_big++;
        if (kc.c.log) klog("camev: HITCH rdt %.3f s | f %ld T %.2f", rawdt, frame, x->T);
        dt = 0.1f;
    }
    kc.dtavg += ((rawdt > 0.3f ? 0.3f : rawdt) - kc.dtavg) * 0.1;
    gnow = GetTickCount();
    if (gnow - kc.prof_check >= 2000) { kc.prof_check = gnow; klcam_profiles(); }
    if (klh_rd32(gd + 0x4cd8) & 0xff) {                                              /* the pause / cut flag (ASSUMPTION): hands off */
        kc.gate_s += dt; kc.pv = 0; kc.stuckS = 0;
        klcam_skip(4, klh_rd32(gd + 0x4cd8), 0);
        if (kc.c.log && (long)kc.gate_s != (long)(kc.gate_s - dt)) {
            float ge[3] = { 0, 0, 0 }; klcam_v3(cam + 0x508, ge);
            klog("cam: gated f %ld T %.2f flag4cd8 %lu eye %.1f %.1f %.1f tick %ld", frame, x->T, (unsigned long)(klh_rd32(gd + 0x4cd8) & 0xff), ge[0], ge[1], ge[2], (long)klh_rd32(cam + 0xc54));
        }
        if (kc.gate_s > 5.0 && !kc.gate_told) { kc.gate_told = 1; klog("cam: the pause / cut flag [gd+0x4cd8] has stood nonzero for 5 s in a round: the watchdog, ShoulderCover and Recover are idle (ASSUMPTION about this flag; check in a normal round)"); }
        return;
    }
    kc.gate_s = 0;
    {
        int bad = 0;
        if (!klcam_v3(cam + 0x508, E)) bad |= 1;
        if (!klcam_v3(P + 0x460, feet)) bad |= 2;
        if (!klcam_v3(cam + 0x398, Pv)) bad |= 4;
        if (bad) { klcam_skip(5, (DWORD)bad, 0); kc.pv = 0; return; }
    }
    klcam_skip(0, 0, 0);
    klh_rd(cam + 0x394, &blocked, 1); klh_rd(cam + 0x124, &cd, 4); if (!klcam_fin(cd)) cd = 0;
    if (!klcam_v3(cam + 0xb0, Pv2)) Pv2[0] = Pv2[1] = Pv2[2] = 0;
    kc.vE = kc.pv ? klcam_dist(E, kc.peye) / dt : 0; kc.vP = kc.pv ? klcam_dist(feet, kc.pfeet) / dt : 0;
    if (kc.pv && klcam_dist(feet, kc.pfeet) > 300.0f) { kc.pv = 0; kc.vE = kc.vP = 0; kc.rc_win = 0; kc.stuckS = 0; }      /* a teleport / respawn */
    /* the player's state: down bits (klshoulder.c: word [P+0xa54] & 0x102) */
    {
        WORD a54 = 0; int loco; BYTE kind = 0, cov = 0; int mv;
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
        if (!alive) klcam_filter_off(cam);
        if (alive) {
            klcam_filter(cam, rawdt);
            if (gnow - kc.cine_check >= 500) { kc.cine_check = gnow; klcam_cine(P, cam); }
            klcam_lean_tick(P, dt);
            if (loco) klcam_unstick(P, cam, dt, stuck, blocked, cd);
            klcam_cover(gd, P, cam, dt);
            klcam_recover(P, cam, dt, E, Pv, feet, blocked, cd);
        }
    }
    /* ---- F4: the measurement */
    klh_rd(cam + 0xb9c, &sideb, 4); klh_rd(cam + 0x5a0, &blend, 4); klh_rd(P + 0x280c, &side, 1); klh_rd(P + 0x2954, &cs, 1);
    if (!klcam_nodepos(cam, node)) node[0] = node[1] = node[2] = 0;
    { DWORD nd = klh_rd32(cam + 0x24); if (nd) klh_rd(nd + 0x70, &fov, 4); }
    memset(&f, 0, sizeof f);
    f.gd = gd; f.P = P; f.cam = cam; f.sys = sys; f.dt = dt; f.rawdt = rawdt; memcpy(f.E, E, 12); memcpy(f.feet, feet, 12); memcpy(f.Pv, Pv, 12); memcpy(f.b0, Pv2, 12); memcpy(f.node, node, 12);
    f.cd = cd; f.blend = blend; f.sideb = sideb; f.fov = fov; f.blocked = blocked; f.side = side; f.cs = (signed char)cs; f.stuck = stuck; f.frame = frame; f.now = now; f.mv = klfc_movid(P);
    if (kc.c.log || kc.c.unstick) frozen = klcam_watch(&f);
    if (alive) klcam_gates(P, cam, dt, frozen);
    if (kc.c.log) klcam_log2(&f, "");
    {
        DWORD profp = klh_rd32(cam + 0xb2c); long want = (long)klh_rd32(P + 0x29a0); int blk = blocked != 0;
        int ev = 0; char why[220]; int n = 0; why[0] = 0;
        if (kc.c.log && kc.ev_profp != profp) { n += snprintf(why + n, sizeof why - n, " profile %08lx(%s)->%08lx(%s)", kc.ev_profp, klcam_pname(kc.ev_profp), profp, klcam_pname(profp)); ev = 1; }
        if (kc.c.log && kc.ev_side != (long)side) { n += snprintf(why + n, sizeof why - n, " side %ld->%u", kc.ev_side, (unsigned)side); ev = 1; }
        if (kc.c.log && kc.ev_cs != (long)(signed char)cs) { n += snprintf(why + n, sizeof why - n, " coverside %ld->%d", kc.ev_cs, (int)(signed char)cs); ev = 1; }
        if (kc.c.log && kc.ev_stuck != stuck) { n += snprintf(why + n, sizeof why - n, " %s", stuck ? "STUCK begins" : "stuck ends"); ev = 1; }
        if (kc.c.log && kc.ev_blk != blk) { n += snprintf(why + n, sizeof why - n, " blocked %d->%d", kc.ev_blk, blk); ev = 1; }
        if (ev) klog("camev:%s | f %ld T %.2f dt %.4f x-off %.1f sideblend %.2f want %ld bit818 %lu b84 %ld eye %.1f %.1f %.1f", why, frame, x->T, dt, klfc_f(cam + 0x530), sideb, want,
                     (unsigned long)(klh_rd32(P + 0x818) >> 10 & 1), (long)klh_rd32(P + 0xb84), E[0], E[1], E[2]);
        kc.ev_profp = profp; kc.ev_side = side; kc.ev_cs = (long)(signed char)cs; kc.ev_stuck = stuck; kc.ev_blk = blk;
        if (kc.c.log) {
            int idle = kc.vP < 1.0f && kc.vE < 1.0f && blend <= 0.0001f && !x->keys && !x->ep && !x->blend_on;
            LONGLONG period = idle ? kc.qf.QuadPart / 2 : kc.qf.QuadPart / kc.c.loghz;
            kc.sum_t += dt; if (dt > 0.033f) kc.sum_hitch++;
            if (stuck) kc.sum_stuck += dt;
            { double dd = klcam_hdist(E, feet); if (dd > kc.sum_maxd) kc.sum_maxd = dd; }
            if (blocked && cd > 0 && cd < kc.rc_cd - 3.0f) kc.sum_pull++;
            if (kc.vE > 5.0f && kc.pv) { float tau = klcam_dist(E, Pv) / kc.vE; kc.sum_taus += tau; kc.sum_taun++; if (tau > kc.sum_taumax) kc.sum_taumax = tau; }
            kc.sum_n++;
            if (!kc.qlast.QuadPart || now.QuadPart - kc.qlast.QuadPart >= period) {
                DWORD profp2 = profp; float t[3]; BYTE sysb = 0; DWORD db = klh_rd32(sys + 0xac); char ex[480], ks[7]; int en, i; DWORD sc = klcam_sc(P);
                t[0] = klfc_f(profp2 + 0x170); t[1] = klfc_f(profp2 + 0x174); t[2] = klfc_f(profp2 + 0x178);
                if (db) klh_rd(db + 0xbc, &sysb, 1);
                for (i = 0; i < 6; i++) ks[i] = (x->keys >> i & 1) ? "XRLCS9"[i] : '.';
                ks[6] = 0;
                en = snprintf(ex, sizeof ex, " | T %.2f rdt %.4f mv %d bit818 %lu camside %u keys %s | t560 %.3f t564 %.3f f568 %08lx k590 %.3f k594 %.3f slow %.3f",
                              x->T, rawdt, f.mv, (unsigned long)(klh_rd32(P + 0x818) >> 10 & 1), (unsigned)(klh_rd32(cam + 0xb40) & 0xff), ks,
                              klfc_f(cam + 0x560), klfc_f(cam + 0x564), klh_rd32(cam + 0x568), klfc_f(cam + 0x590), klfc_f(cam + 0x594), klfc_f(cam + 0xca0));
                if (sc) en += snprintf(ex + en, sizeof ex - en, " st104 %d st105 %d st10c %lu c2d6c %08lx b90 %08lx", (int)(signed char)(klh_rd32(sc + 0x104) & 0xff), (int)(signed char)(klh_rd32(sc + 0x105) & 0xff), klh_rd32(sc + 0x10c), klh_rd32(P + 0x2d6c), klh_rd32(P + 0xb90));
                if (cs && (x->keys & 2)) strncat(ex, " coveraim", sizeof ex - strlen(ex) - 1);
                klog("cam: f %ld dt %.4f%s | P %.1f %.1f %.1f vP %.0f | eye %.1f %.1f %.1f vE %.0f node %.1f %.1f %.1f | piv398 %.1f %.1f %.1f dPiv %.1f | b0 %.1f %.1f %.1f | hdist %.1f 3d %.1f | blk %u en7eb %u cd %.1f | blend %.2f sideblend %.2f side %u want %ld cs %d 818b10 %lu b84 %ld | prof %08lx t %.2f/%.2f/%.2f fov %.3f | tick %ld sysb %u flag4cd8 %lu%s%s",
                     frame, dt, dt > 0.033f ? " HITCH" : "", feet[0], feet[1], feet[2], kc.vP, E[0], E[1], E[2], kc.vE, node[0], node[1], node[2], Pv[0], Pv[1], Pv[2], klcam_dist(E, Pv),
                     Pv2[0], Pv2[1], Pv2[2], klcam_hdist(E, feet), klcam_dist(E, feet), (unsigned)blocked, (unsigned)klh_rd32(cam + 0x7eb) & 0xff, cd, blend, sideb, (unsigned)side, want, (int)(signed char)cs,
                     (unsigned long)(klh_rd32(P + 0x818) >> 10 & 1), (long)klh_rd32(P + 0xb84), profp, t[0], t[1], t[2], fov, (long)klh_rd32(cam + 0xc54), (unsigned)sysb,
                     (unsigned long)(klh_rd32(gd + 0x4cd8) & 0xff), stuck ? " STUCK" : "", ex);
                kc.qlast = now;
            }
            if (kc.sum_t >= 10.0) {
                klog("cam: 10 s: frames %ld, hitch frames %ld, stuck %.1f s, max hdist %.1f, pull-in frames %ld, tau mean %.3f max %.3f s (%ld samples), STUCK2 episodes %d (total), LAG2 %d (%.1f s), frames with rdt > 0.1 s %d, swaps %d ok / %d no change, max BLEND %.2f s FOV %.2f s SIDEBLEND %.2f s",
                     kc.sum_n, kc.sum_hitch, kc.sum_stuck, kc.sum_maxd, kc.sum_pull, kc.sum_taun ? kc.sum_taus / kc.sum_taun : -1.0, kc.sum_taumax, kc.sum_taun,
                     x->n_ep, x->n_lag, x->lag_tot, x->n_big, x->n_swap, x->n_swapfail, x->max_blend, x->max_fov, x->max_sb);
                kc.sum_t = kc.sum_stuck = kc.sum_maxd = 0; kc.sum_hitch = kc.sum_pull = kc.sum_n = kc.sum_taun = 0; kc.sum_taumax = 0; kc.sum_taus = 0;
            }
        }
    }
    memcpy(kc.peye, E, 12); memcpy(kc.pfeet, feet, 12); kc.pv = 1; kc.pdt = dt;
    if (!kc.rc_d) { kc.rc_d = klcam_dist(E, Pv); kc.rc_cd = cd; }
}

static void klcam_init(void)
{
    struct klcam_cfg *c = &kc.c;
    memset(&kc, 0, sizeof kc);
    QueryPerformanceFrequency(&kc.qf);
    kc.dtavg = 0.016;
    c->enable = klcam_ini_i("Enable", 1) != 0;
    if (!c->enable) return;
    c->log = klcam_ini_i("Log", 0) != 0;
    c->logkeys = klcam_ini_i("LogKeys", 1) != 0;
    c->loghz = klcam_ini_i("LogHz", 20); if (c->loghz < 1) c->loghz = 1; if (c->loghz > 120) c->loghz = 120;
    c->blend = klcam_ini_i("Blend", 1) != 0;
    c->blendscale = klcam_ini_f("BlendScale", 0.4f, 0.1f, 1.0f);
    c->unstick = klcam_ini_i("Unstick", 1) != 0;
    c->ufilter = klcam_ini_i("UnstickFilter", 1) != 0;
    c->ugate = klcam_ini_i("UnstickGate", 0) != 0;
    c->utarget = klcam_ini_i("UnstickTarget", 0) != 0;
    c->recover = klcam_ini_i("Recover", 0) != 0;
    c->recoverspeed = klcam_ini_f("RecoverSpeed", 350.0f, 50.0f, 5000.0f);
    c->shouldercover = klcam_ini_i("ShoulderCover", 1) != 0;
    c->scoronline = klcam_ini_i("ShoulderCoverOnline", 0) != 0;
    c->leanfollow = klcam_ini_i("LeanFollow", 1) != 0;
    c->leangate = klcam_ini_i("LeanGate", 1) != 0;
    c->cine = klcam_ini_i("Cine", 1) != 0;
    c->cineaim = c->cine && klcam_ini_i("CineAim", 1) != 0;
    c->fliptime = klcam_ini_f("FlipTime", 0.35f, 0.0f, 2.0f);
    c->fliptimespecial = klcam_ini_f("FlipTimeSpecial", 0.0f, 0.0f, 2.0f);
    c->shakescale = klcam_ini_f("ShakeScale", 0.8f, 0.0f, 2.0f);
    c->fovstep = klcam_ini_f("FovStep", 1.8f, 0.5f, 6.0f);
    {   /* ShakeKeep=3,7,12: shaker table entries left at their own value */
        char t[160], *p; int v;
        GetPrivateProfileStringA("Camera", "ShakeKeep", "", t, sizeof t, klh_ini);
        for (p = t; *p; ) { while (*p == ' ' || *p == ',') p++; if (!*p) break; v = atoi(p); if (v >= 0 && v < 41) c->shakekeep[v] = 1; while (*p && *p != ',') p++; }
    }
    klog("cam: on: Blend %d (x%.2f) Unstick %d (filter %d gate %d target %d) Recover %d (%.0f cm/s) ShoulderCover %d LeanFollow %d (gate %d) Cine %d CineAim %d FlipTime %.2f (special %.2f) ShakeScale %.2f FovStep x%.2f Log %d (%d Hz, keys %d). "
         "No data route (no effect): look smoothing, pitch limits",
         c->blend, c->blendscale, c->unstick, c->ufilter, c->ugate, c->utarget, c->recover, c->recoverspeed, c->shouldercover, c->leanfollow, c->leangate, c->cine, c->cineaim, c->fliptime, c->fliptimespecial, c->shakescale, c->fovstep,
         c->log, c->loghz, c->logkeys);
}

#endif /* KLCAM_C */
