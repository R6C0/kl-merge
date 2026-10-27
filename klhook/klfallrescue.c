/*
 * klfallrescue.c - [FallRescue]: a player who leaves the level box (DM02 shop rear edge, the Retomoto ledge, a hole in a stock map) is put
 * back on the last place he stood still, BEFORE the game kills him. Included by klhook.c after klrappel.c (uses klfc_* of klfreeclimb.c,
 * klrp_r, klq_r, klog, klh_ini, klh_data). NOT RUN IN THE GAME (2026-10-26, written offline).
 *
 * THE FAULT (peer kl-merge-ce): ZFFPlayer vtable slot 415 = 0x87fb30 runs every tick. READ in kl2.exe 0490 (capstone, file):
 *   node  = [P+0x7d0]; p = [[[node+0x30]+0x18]+0x30] (three floats = the world matrix translation) times 100.0 (0x408060, constant
 *           0xb3dde8 = double 100.0)  ->  p100;   v = P+0x808 (three floats);   dt = [sys+0x50] (sys = [0xdd2640]);
 *   q     = p100 + v * dt (0x5f8fb0: out = base + vec * dt);
 *   box W = [[sys+0xac]+0x52cc]; 0x53f360 (thiscall on W, one stack arg = float *pt) is a pure compare: inside iff
 *           min <= pt <= max on every axis, max = W+0x166e0 (x), +0x166e4 (y), +0x166e8 (z), min = W+0x166ec (x), +0x166f0 (y), +0x166f4 (z)
 *           (the fcompp / test ah,0x41 / test ah,5 pairs at 0x53f366..0x53f3c5 decode to min <= pt and pt <= max);
 *   if p100 OR q is outside -> call at 0x87fe31 -> 0x8ce1e0 (sets [[0xdd265c]+0x4d1c]=1, MF_01 text, popup 0x8edc40 kind [P+0x91e]) = YouDied.
 * So the box is in x100 units of the matrix translation and the look-ahead adds v*dt UNSCALED to the x100 point (the game does just that).
 * y is the up axis (the box y pair is +0x166e4 / +0x166f0). The call site 0x87fe31 lies in the hashed range 0x87e000..0x880000
 * (klranges.h), so NO detour is made: the only answer is to move the player before the test fails.
 *
 * WHAT IT DOES (local human only; every peer moves his own player; the placement is the proven 0x82cc40 klunstick.c / klfreeclimb.c use):
 *   REMEMBER  every tick the player is alive, the round runs (session state [[0x168e598]+0x70] == 0x19), he is in plain locomotion or cover
 *             (movement id 2 / 3 / 8, no action running, no seat / carrier, no rappel / climb of ours), his p100 y has changed less than 5
 *             since the last tick for SafeMs, and p100 and p100 + v*dt*Look are inside the box (with the box read): lastSafe = his feet
 *             (klfc_pose P, the space 0x82cc40 takes) + his rotation + p100.
 *   TRIGGER   a) p100 or p100 + v*dt*Look (Look = 3 frames: the main-loop call may come after the game's own test of the same frame) is
 *                outside the box;  b) p100.y < lastSafe.p100.y - DropBelow  AND he is really falling (y speed over >= 100 ms below
 *                FallSpeed per second, so a lift or a ladder ride never counts).
 *   ACT       klfc_guard: leave-cover prep when in cover (as klunstick.c), then 0x82cc40(P, M, lastSafe + 10 up, resetVel 1, force 0, net 0),
 *             then the velocity floats [P+0x808] zeroed (a data write), 'fallrescue: N from .. to ..'.
 *   LIMITS    one rescue per 2 s; three in 30 s -> no more until the next level load (a new player object), logged.
 * GUESSES: the 5 / 100 ms / FallSpeed numbers; Look = 3; that a missing velocity or box read means 'inside'; that 0x82cc40 with force 0
 * accepts the target (the box check of lastSafe makes it a place the game's own test passes); that the main-loop call and the player
 * update interleave so that Look frames of look-ahead are enough (no live data). Not gated on offline: online each peer moves only his own.
 *
 * KLHook.ini
 *   [FallRescue]
 *   Enable=1      (recommended on) 0 = nothing
 *   DropBelow=1500 units of p100 below the last safe place that count as a fall (200 .. 100000)
 *   SafeMs=500    how long he must have stood still in y before a place is kept (100 .. 5000)
 *   FallSpeed=600 units / s of p100 y the fall must be faster than (50 .. 100000)
 *   Look=3        frames of v*dt look-ahead (1 .. 10)
 *   Dry=0         1 = log only
 *   Log=1
 *   Online=0      1 = also online (untested: the PlaceAt is local, sendNet 0)
 */
#ifndef KLFALLRESCUE_C
#define KLFALLRESCUE_C

#define KLFR_SM 0x0168e598u                   /* session manager: +0x70 state (0x19 = round running) */

static struct { int on, drop, safeMs, fall, look, dry, log, online, back; } klfr;
static struct { float p[3], p100[3], M[9]; int have; } klfr_safe;
/* peer DM02_fallR (05:34, LIVE PASS): the last still place was 7 units from the edge, so a player still holding a direction fell again at once.
   A ring of safe places, one every 250 ms; a rescue goes back to the newest that is at least BackMs old (x the rescue's number in a row), else the oldest. */
#define KLFR_RING 16
static struct { float p[3], p100[3], M[9]; DWORD t; } klfr_ring[KLFR_RING];
static int klfr_rn, klfr_rh;
static DWORD klfr_P, klfr_stillT, klfr_cool, klfr_ts[3], klfr_sampT;
static float klfr_lastY, klfr_sampY;
static float klfr_lastP[3];
static int klfr_falling, klfr_dryOut, klfr_n, klfr_ever, klfr_dead, klfr_stopped, klfr_lastT = -0x7fffffff, klfr_haveY;

static DWORD klfr_box(void)
{   /* W = [[sys+0xac]+0x52cc], or 0 */
    DWORD sys = klfc_sys(), db = sys ? klh_rd32(sys + 0xac) : 0;
    return db ? klh_rd32(db + 0x52cc) : 0;
}
static int klfr_in(DWORD W, const float *q)
{   /* the box test of 0x53f360 (min <= q <= max), done here by reads; unreadable box = inside */
    float mx[3], mn[3]; int i;
    if (!W || !klh_rd(W + 0x166e0, mx, 12) || !klh_rd(W + 0x166ec, mn, 12)) return 1;
    for (i = 0; i < 3; i++) if (!(q[i] >= mn[i]) || !(q[i] <= mx[i])) return 0;
    return 1;
}
static int klfr_p100(DWORD P, float *p)
{   /* 0x87fb30's own read of the place: world translation x 100 */
    DWORD a = klh_rd32(P + 0x7d0), b;
    a = a ? klh_rd32(a + 0x30) : 0; a = a ? klh_rd32(a + 0x18) : 0; b = a;
    if (!b || !klh_rd(b + 0x30, p, 12)) return 0;
    p[0] *= 100.0f; p[1] *= 100.0f; p[2] *= 100.0f;
    return p[0] == p[0] && p[1] == p[1] && p[2] == p[2];
}

static void klfr_reset(void)
{   /* a new level / round / life: nothing of the old place may be used */
    memset(&klfr_safe, 0, sizeof klfr_safe); klfr_rn = klfr_rh = 0; klfr_haveY = 0; klfr_n = 0; klfr_cool = 0; klfr_stopped = 0; klfr_dryOut = 0; klfr_falling = 0;
    memset(klfr_ts, 0, sizeof klfr_ts);
}

static int klfr_body(void *unused)
{
    DWORD gd, sys, sm, P, now, W, ho; signed char pi = -1; int T, id, out = 0, why = 0, k; BYTE b = 0;
    float p100[3], pf[3], M[9], v[3] = { 0, 0, 0 }, dt = 0, q[3], hv[2] = { -1, -1 };
    (void)unused;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(sys = klfc_sys())) return 0;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLFR_SM))) || klh_rd32(sm + 0x70) != 0x19) { klfr_P = 0; klfr_reset(); return 0; }   /* round not running (also frees the 'stop until next level' latch) */
    if (!klh_rd(gd + 0x898, &pi, 1) || pi < 0 || pi > 7) return 0;
    if (!(P = klh_rd32(gd + 0x828 + 4 * pi)) || klh_pvt(P) != KLFC_PLAYER_VT || !klfc_ok(P, 0x2e00)) return 0;
    T = (int)klh_rd32(sys + 0x48);
    if (T == klfr_lastT) { klfr_haveY = 0; return 0; }                  /* paused: still-time and fall speed restart on resume */
    klfr_lastT = T;
    if (P != klfr_P) { klfr_P = P; klfr_reset(); }                       /* a new player object */
    if (klfr_stopped) return 0;
    if (!klh_rd(P + 0x2720, &b, 1) || !(b & 2)) return 0;               /* not the local human */
    if ((ho = klh_rd32(P + 0xa48)) == 0 || !klh_rd(ho + 4, hv, 8) || !(hv[0] > 0.0f)) { klfr_reset(); return 0; }   /* dead / no health: forget the place (respawn = new life) */
    if (klh_rd32(P + 0xd50) || klh_rd32(P + 0xd44)) { klfr_haveY = 0; return 0; }   /* seat / carrier */
#ifdef KLRAPPEL_C
    if (klrp_r.player) { klfr_haveY = 0; return 0; }
#endif
    if (klq_r.player) { klfr_haveY = 0; return 0; }                     /* our climb / vault: a scripted move */
    if (!klfr_p100(P, p100)) return 0;
    now = GetTickCount();
    W = klfr_box();
    klh_rd(P + 0x808, v, 12); klh_rd(sys + 0x50, &dt, 4);
    if (!(dt > 0.0f) || dt > 1.0f) dt = 0.0f;
    if (!(v[0] == v[0] && v[1] == v[1] && v[2] == v[2])) v[0] = v[1] = v[2] = 0;
    {   /* the game rescales a copy of v when speed^2 > 250000 (double 0xb2f878); clamp conservatively to 500 so a knockback cannot fire early */
        float s2 = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
        if (s2 > 250000.0f) { float f = 500.0f / (float)sqrt(s2); v[0] *= f; v[1] *= f; v[2] *= f; }
    }
    for (k = 0; k < 3; k++) q[k] = p100[k] + v[k] * dt * (float)klfr.look;
    /* teleport / scripted move: a one-tick jump of more than 3000 p100 (30 m) is no fall (GUESS: 3000; a free fall at ~2000/s moves ~35 per 60 Hz tick) -> forget the place */
    if (klfr_haveY) {
        float dx = p100[0] - klfr_lastP[0], dy = p100[1] - klfr_lastP[1], dz = p100[2] - klfr_lastP[2];
        if (dx * dx + dy * dy + dz * dz > 3000.0f * 3000.0f) { memset(&klfr_safe, 0, sizeof klfr_safe); klfr_rn = klfr_rh = 0; klfr_haveY = 0; klfr_falling = 0; }
    }
    memcpy(klfr_lastP, p100, 12);
    /* y bookkeeping: still in y / fall speed over >= 100 ms */
    if (!klfr_haveY || fabs(p100[1] - klfr_lastY) >= 5.0f) klfr_stillT = now;
    klfr_lastY = p100[1];
    if (!klfr_haveY || now - klfr_sampT >= 100) {
        float fs = (klfr_haveY && now > klfr_sampT) ? (klfr_sampY - p100[1]) * 1000.0f / (float)(now - klfr_sampT) : 0.0f;   /* units / s downward */
        if (klfr_haveY && now - klfr_sampT >= 100) klfr_falling = fs > (float)klfr.fall;       /* reused as the 'falling' flag */
        klfr_sampT = now; klfr_sampY = p100[1];
        if (!klfr_haveY) klfr_falling = 0;
    }
    klfr_haveY = 1;
    id = klfc_movid(P);
    /* REMEMBER */
    if (klfr_in(W, p100) && klfr_in(W, q)) {
        if ((id == 2 || id == 3 || id == 8) && !klfc_cur_act(P) && now - klfr_stillT >= (DWORD)klfr.safeMs && klfc_pose(P, M, pf)) {
            memcpy(klfr_safe.p, pf, 12); memcpy(klfr_safe.p100, p100, 12); memcpy(klfr_safe.M, M, sizeof M); klfr_safe.have = 1;
            const float *nw = klfr_ring[(klfr_rh + KLFR_RING - 1) % KLFR_RING].p100;   /* standing on one spot keeps its first time (no ring of copies); GUESS: 250 ms / 25 p100 */
            if (!klfr_rn || (now - klfr_ring[(klfr_rh + KLFR_RING - 1) % KLFR_RING].t >= 250 && (nw[0] - p100[0]) * (nw[0] - p100[0]) + (nw[2] - p100[2]) * (nw[2] - p100[2]) + (nw[1] - p100[1]) * (nw[1] - p100[1]) > 25.0f * 25.0f)) {
                memcpy(klfr_ring[klfr_rh].p, pf, 12); memcpy(klfr_ring[klfr_rh].p100, p100, 12); memcpy(klfr_ring[klfr_rh].M, M, sizeof M); klfr_ring[klfr_rh].t = now;
                klfr_rh = (klfr_rh + 1) % KLFR_RING; if (klfr_rn < KLFR_RING) klfr_rn++;
            }
        }
    } else out = 1;
    /* TRIGGER (not while the game runs an action / cutscene: a scripted move must not be undone) */
    if (klfc_cur_act(P)) { klfr_falling = 0; return 0; }
    if (!out) klfr_dryOut = 0;
    if (klfr_safe.have && p100[1] < klfr_safe.p100[1] - (float)klfr.drop && klfr_falling) out = 2;
    if (!out || !klfr_safe.have) {
        if (out && !klfr_ever && klfr.log) { klfr_ever = 1; klog("fallrescue: the player is outside the level box at p100 (%.0f,%.0f,%.0f) but no safe place has been kept yet", p100[0], p100[1], p100[2]); }
        return 0;
    }
    if (now < klfr_cool) return 0;
    if (!klfr_in(W, klfr_safe.p100)) { memset(&klfr_safe, 0, sizeof klfr_safe); return 0; }   /* the kept place is outside THIS box (stale): drop it */
    why = out;
    /* LIMITS: 3 in 30 s (klfr_ts[n % 3] holds the rescue made 3 rescues ago) */
    if (klfr_n >= 3 && now - klfr_ts[klfr_n % 3] < 30000) {
        klfr_stopped = 1; klfr_cool = now + 2000;
        klog("fallrescue: 3 rescues in 30 s - NO MORE rescues until the next level load");
        return 0;
    }
    if (!klfc_pose(P, M, pf)) return 0;
    if (klfr.dry && klfr_dryOut) return 0;                              /* dry run: one line per excursion */
    {   /* step back along the ring: the newest place at least BackMs x (rescues in a row + 1) old that is inside this box, else the oldest inside */
        DWORD want = (DWORD)klfr.back * (DWORD)(klfr_n + 1); int j, pick = -1;
        for (j = 1; j <= klfr_rn; j++) {
            int r = (klfr_rh + KLFR_RING - j) % KLFR_RING;
            if (!klfr_in(W, klfr_ring[r].p100)) continue;
            pick = r;
            if (now - klfr_ring[r].t >= want) break;
        }
        if (pick >= 0) { memcpy(klfr_safe.p, klfr_ring[pick].p, 12); memcpy(klfr_safe.p100, klfr_ring[pick].p100, 12); memcpy(klfr_safe.M, klfr_ring[pick].M, sizeof klfr_safe.M); }
    }
    {
        float to[3];
        to[0] = klfr_safe.p[0]; to[1] = klfr_safe.p[1] + 10.0f; to[2] = klfr_safe.p[2];
        if (klfr.log) klog("fallrescue: %d from (%.0f,%.0f,%.0f) p100 (%.0f,%.0f,%.0f) [%s; box %s] to (%.0f,%.0f,%.0f) p100 (%.0f,%.0f,%.0f)%s", klfr_n + 1, pf[0], pf[1], pf[2], p100[0], p100[1], p100[2],
             why == 1 ? "left the level box" : "fell below the last safe place", W ? "read" : "unreadable", to[0], to[1], to[2],
             klfr_safe.p100[0], klfr_safe.p100[1], klfr_safe.p100[2], klfr.dry ? " - DRY RUN, nothing moved" : "");
        if (klfr.dry) { klfr_dryOut = 1; klfr_cool = now + 2000; return 0; }
        klfr_cool = now + 2000;
        if (id == 8 && klh_rd32(P + 0x2810)) KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_LEAVECOVER)(P, 0);
        KLFC_CALL(void (__fastcall *)(DWORD, DWORD, const float *, const float *, int, int, int), KLFC_TELE)(P, 0, klfr_safe.M, to, 1, 0, 0);
        { float z[3] = { 0, 0, 0 }; klh_data((void *)(DWORD_PTR)(P + 0x808), z, 12, "fallrescue velocity"); }
        klfr_ts[klfr_n % 3] = now; klfr_n++;
        klfr_stillT = now; klfr_haveY = 0;
    }
    return 0;
}

static void klfr_tick(int game_thread)
{
    if (!klfr.on || klfr_dead || !game_thread || !klh_exe_ok) return;
    if (kl_online() && !klfr.online) return;                            /* [Net] OnlineSafe: the PlaceAt is local (sendNet 0), peers would not see it; opt-in via Online=1 */
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;           /* the gameplay call of the main loop only */
    if (klfc_guard("fallrescue", klfr_body, 0) < 0) { klfr_dead = 1; klog("fallrescue: DISABLED for this session (fault) - restart the game before testing again"); }
}

static void klfr_init(void)
{
    memset(&klfr, 0, sizeof klfr);
    klfr.on = GetPrivateProfileIntA("FallRescue", "Enable", 1, klh_ini) != 0;
    if (!klfr.on) { klog("fallrescue: off"); return; }
    klfr.online = GetPrivateProfileIntA("FallRescue", "Online", 0, klh_ini) != 0;
    klfr.drop = (int)GetPrivateProfileIntA("FallRescue", "DropBelow", 1500, klh_ini); if (klfr.drop < 200) klfr.drop = 200; if (klfr.drop > 100000) klfr.drop = 100000;
    klfr.safeMs = (int)GetPrivateProfileIntA("FallRescue", "SafeMs", 500, klh_ini); if (klfr.safeMs < 100) klfr.safeMs = 100; if (klfr.safeMs > 5000) klfr.safeMs = 5000;
    klfr.fall = (int)GetPrivateProfileIntA("FallRescue", "FallSpeed", 600, klh_ini); if (klfr.fall < 50) klfr.fall = 50; if (klfr.fall > 100000) klfr.fall = 100000;
    klfr.look = (int)GetPrivateProfileIntA("FallRescue", "Look", 3, klh_ini); if (klfr.look < 1) klfr.look = 1; if (klfr.look > 10) klfr.look = 10;
    klfr.dry = GetPrivateProfileIntA("FallRescue", "Dry", 0, klh_ini) != 0;
    klfr.log = (int)GetPrivateProfileIntA("FallRescue", "Log", 1, klh_ini);
    klfr.back = (int)GetPrivateProfileIntA("FallRescue", "BackMs", 1500, klh_ini); if (klfr.back < 0) klfr.back = 0; if (klfr.back > 10000) klfr.back = 10000;   /* GUESS: 1.5 s (peer DM02_fallR) */
    klog("fallrescue: on (recommended on); DropBelow=%d SafeMs=%d FallSpeed=%d Look=%d BackMs=%d Dry=%d; a player who leaves the level box (or falls) is put back on a place he stood still about BackMs earlier, at most 3 times in 30 s", klfr.drop, klfr.safeMs, klfr.fall, klfr.look, klfr.back, klfr.dry);
}

#endif
