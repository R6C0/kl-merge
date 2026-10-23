/* klnetsmooth.c - [NetSmooth]: a receiver-side smoother for the DISPLAYED heading of REMOTE players (online FA, not ranked).
 * OFF unless [NetSmooth] Enable=1. Live 2026-10-20: chain, matrix form and write call proven offline (N1-N6); the online run is still untried. Research: re\netcode_smooth.md.
 *
 * WHY. A remote player's heading arrives as an unwrapped int16 (1024 per turn, klnet.c / re\netcode_receiver.md) and the
 * receiver uses it RAW: 0x600eb0 builds the body matrix from it and places the body with B->vtbl[0x8c](mat, pos). Whatever
 * the sender's heading did between two packets (a 100 ms update, a 2 s forced refresh, a late or doubled packet) the body
 * does in one frame: the "spinbot" look. This module lets the stock code run, then replaces only the displayed yaw of the
 * remote bodies with a rate-limited, critically damped version of it.
 *
 * HOW (no code byte of kl2.exe is touched; nothing hashed is written, klranges.h):
 *   - ZFFPlayer's vtable is 0xbb45f4. Slot 393 (the dword at 0xbb4c18) is 0x506350, the per-frame update that calls the
 *     replica receiver: [P+0x2720] & 2 -> 0x616050 (master), else 0x4a1890 -> 0x600eb0 (remote). READ in disassembly.
 *   - The 512 dwords of that vtable are copied into a private table (this file), slot 393 is pointed at kns_update, and
 *     the vtable POINTER (first dword) of each REMOTE ZFFPlayer on the heap is pointed at the copy. Players are listed
 *     from the game's own array [[0xdd265c] + 0x828 + 4*i], i < 28 (klcam.c / klauto.c). The local player is never
 *     swapped and kns_update also skips it. The stock vtable in .rdata stays as it is.
 *   - kns_update(P) calls the original slot-393 function, then, for a remote player (not local, flag 2 clear):
 *       B = [[[P'+4]+0x50]+0x60] with P' = [[P+0x274c]+0x540] (0x598460 does [[x+0x50]+0x60]); the body transform is the 0x30
 *       bytes AT THE ADDRESS HELD IN [B+4] (the code dereferences it; an unverified GUESS) (3x3 floats at +0, position at +0x24 - from 0x8c's callers, GUESS that it is row-major, Y up).
 *       If the matrix is a pure yaw (Y axis unmoved, the 2x2 block a rotation) the yaw is read, smoothed, and written back
 *       through the game's own B->vtbl[0x8c](mat, pos) (the call 0x600ff5 makes). A tilted or odd matrix is left alone.
 *   - The original pointer is put back when the key is off, the session is not an online unranked one, the object is gone or
 *     the level ends (the player array is empty), and the tick drops a swapped object that no longer shows our table.
 *
 * What it does NOT do (see the .md): hit tests (the server's own copy of the other player's heading, ZFFPlayer +0xc14 and
 * the weapon aim, are not changed: only the body matrix the renderer and animation read), positions, the AI actors
 * (0x569eb0 is reached from 0x82b7f0 whose vtable owner is not identified), the camera.
 *
 * CERTAIN (read in kl2.exe): slot 393 = 0x506350, its two branches, 0x598460, the 0x8c call shape, the player array.
 * GUESS: that bit 2 of [P+0x2720] means "owned here" (the branch name), that [R+0x540] is the player, that the matrix is
 *   row-major Y-up, that 0x8c's second argument is 3 floats, that the body matrix is rebuilt from the raw heading every
 *   frame (if not, the smoother just follows its own last value), that slot 0x8c is on the body object in vtable slot 35.
 *
 * KLHook.ini:
 *   [NetSmooth]
 *   Enable=0              1 = on (online FA / co-op, host or client, not ranked)
 *   MaxTurnDegPerSec=540  highest turn speed shown for a remote body
 *   SmoothMs=90           time constant of the damping (smaller = closer to raw)
 *   SnapUnits=300         a body that moved further than this in one frame (respawn, teleport) is not smoothed that frame
 *   Log=0                 1 = log swaps / restores and the first updates
 *   CamYaw=0              1 = also smooth the remote CAMERA yaw int16 [R+0xe0] (needs Enable=1; kns_camyaw, re\netsmooth_camyaw.md):
 *                         written after the stock update, the raw value put back before the next one. Online only, remote players only.
 *                         VISUAL ONLY, opt-in: code reading [R+0xe0] / [P+0xd74] between our write and the restore sees the smoothed value.
 *   CamSmoothMs=70        CamYaw time constant     MaxCamDegPerSec=720  CamYaw turn speed cap
 *   CamSnapDeg=150        a camera error above this (or [R+0x548]==0xff, dt > 0.25 s, a position jump) is followed at once
 *   Probe=0               READ-ONLY self-check, works offline (Arcade) and without Enable: every ProbeMs (1000) for up to
 *                         ProbeLines (400) lines, each player of the array: vtable, flags [+0x2720], the body chain above,
 *                         the 12 floats at the transform, the pure-yaw test and its yaw, and the position [P+0x460].
 *                         Turning the local player (scripted mouse) must turn that yaw if the chain and layout GUESSES hold.
 *                         N1/N2 2026-10-20: offline [P+0x274c] is 0 (online-only object), so the probe starts at P itself; from P the
 *                         chain holds (B vtable 0xb9c6cc, [B+4] = the transform, t follows the position, the yaw follows a flick).
 *   OfflineTest=0         TEST build only: 1 = the smoother runs offline too, on non-local players even with the master flag
 *                         (the Arcade AI heisters), to exercise the B->vtbl[0x8c] write without two PCs.
 *
 * Wiring (klhook.c, NEW lines only):
 *   #include "klnetsmooth.c"        below  #include "klinv.c"
 *   klnetsmooth_init();             below  klinv_init();
 *   klnetsmooth_tick(game_thread);  below  klinv_tick(game_thread);
 */
#ifndef KLNETSMOOTH_C
#define KLNETSMOOTH_C

#include <math.h>

#define KNS_PLAYER_VT   0x00bb45f4u
#define KNS_SLOT        393
#define KNS_NSLOT       512
#define KNS_NPL         28

static struct { int on, log; float maxdps, tau, snap; volatile LONG active; int told; int probe, probems, probemax, probed; DWORD probet; int offline;
               int cy; float cytau, cymaxu, cysnapu; } kns;      /* cy: [NetSmooth] CamYaw; cytau in s, cymaxu in units/s, cysnapu in units (1024 per turn) */
static DWORD kns_vtblk[KNS_NSLOT + 1];                /* [0] = the stock vt[-1] (MSVC RTTI locator), then the private vtable */
#define kns_vt (kns_vtblk + 1)
static DWORD kns_orig;                                /* the stock slot 393 function */
static DWORD kns_obj[KNS_NPL];                        /* objects given the private vtable */
static struct { int have; float yaw, vel, pos[3]; LARGE_INTEGER t;
               int cy_have, cy_pend, cy_out, cy_raw; DWORD cy_r, cy_log; float cy_s, cy_vel, cy_pos[3]; LARGE_INTEGER cy_t; LONG cy_nw, cy_nr; } kns_st[KNS_NPL];   /* cy_*: CamYaw state (kns_camyaw) */
static LONG kns_n_upd, kns_n_set, kns_n_skip, kns_n_rbok, kns_n_rbbad;
static LONG kns_n_cyw, kns_n_cyr, kns_n_cyseen, kns_n_cyask;      /* CamYaw: [R+0xe0] writes, raw puts back, movement saw our write n / asked m */

static void kns_cy_clear(int i) { kns_st[i].cy_have = 0; kns_st[i].cy_pend = 0; kns_st[i].cy_r = 0; }

static DWORD kns_ours(void) { return (DWORD)(DWORD_PTR)kns_vt; }

static int kns_local(DWORD *me)
{   /* the game's own local player: [gd + 0x828 + 4 * (char)[gd + 0x898]] */
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c)); BYTE sel = 0xff;
    *me = 0;
    if (!gd || !klh_rd(gd + 0x898, &sel, 1) || sel >= KNS_NPL) return 0;
    *me = klh_rd32(gd + 0x828 + 4 * sel);
    return 1;
}

static float kns_wrap(float a) { while (a > 3.14159265f) a -= 6.2831853f; while (a < -3.14159265f) a += 6.2831853f; return a; }

/* online the chain P -> R -> body is a GUESS (re\netcode_smooth.md): say once where it breaks, so a two-PC run tells either way */
static void kns_chain_fail(DWORD pl, const char *why)
{
    static int n;
    if (n < 3) { n++; klog("netsmooth: player %08lx: no body (%s) - not smoothed%s", pl, why, n == 3 ? " (not logged again)" : ""); }
}

/* the body of player P: B (the object whose vtable slot 0x8c places it) and its transform address, or 0 */
static int kns_body(DWORD pl, DWORD *B, DWORD *xf)
{
    DWORD r = klh_rd32(pl + 0x274c), p, e, b;
    if (!r && kns.offline) p = pl;                                /* OfflineTest: no replica offline (N1), start at P (N2: holds) */
    else if (!r || !(p = klh_rd32(r + 0x540))) { kns_chain_fail(pl, r ? "[R+0x540] = 0" : "no replica [P+0x274c]"); return 0; }
    if (!(e = klh_rd32(p + 4)) || !(e = klh_rd32(e + 0x50)) || !(b = klh_rd32(e + 0x60))) { kns_chain_fail(pl, "[[[p+4]+0x50]+0x60] = 0"); return 0; }
    if (!(*xf = klh_rd32(b + 4))) { kns_chain_fail(pl, "[B+4] = 0"); return 0; }
    *B = b; return 1;
}

static int kns_index(DWORD pl) { int i; for (i = 0; i < KNS_NPL; i++) if (kns_obj[i] == pl) return i; return -1; }

typedef void (__fastcall *kns_fn)(void *self, void *edx);
typedef void (__fastcall *kns_set_fn)(void *self, void *edx, float *mat, float *pos);

static void kns_smooth(DWORD pl)
{
    DWORD B, xf, me, vt; float m[12]; float c, s, yaw, d, dt = 0, step, w; int i, mir; LARGE_INTEGER now, fq;
    if (!kns_local(&me) || pl == me) return;                    /* never the local player */
    { BYTE fl = 0; if (!klh_rd(pl + 0x2720, &fl, 1) || ((fl & 2) && !kns.offline)) return; }   /* the master branch is not a remote (OfflineTest: AI heisters are) */
    if (!kns_body(pl, &B, &xf) || !klh_rd(xf, m, sizeof m)) return;
    for (i = 0; i < 12; i++) if (m[i] != m[i]) return;          /* NaN */
    /* a pure yaw about Y: row 1 / column 1 are the unit Y axis. LIVE N2 (2026-10-20, 3808 samples, offline): the body matrix is
       ALWAYS the mirrored form [c 0 s; 0 1 0; s 0 -c] (determinant -1), never the rotation [c 0 s; 0 1 0; -s 0 c] first assumed;
       both are accepted and the form is kept on write-back. */
    if (fabsf(m[4] - 1.0f) > 0.03f || fabsf(m[1]) > 0.03f || fabsf(m[3]) > 0.03f || fabsf(m[5]) > 0.03f || fabsf(m[7]) > 0.03f) { kns_n_skip++; return; }
    if (fabsf(m[8] + m[0]) <= 0.03f && fabsf(m[6] - m[2]) <= 0.03f) mir = 1;
    else if (fabsf(m[8] - m[0]) <= 0.03f && fabsf(m[6] + m[2]) <= 0.03f) mir = 0;
    else { kns_n_skip++; return; }
    i = kns_index(pl); if (i < 0) return;
    yaw = atan2f(m[2], m[0]);
    QueryPerformanceCounter(&now); QueryPerformanceFrequency(&fq);
    if (kns_st[i].have) {
        dt = (float)(now.QuadPart - kns_st[i].t.QuadPart) / (float)fq.QuadPart;
        if (dt > (kns.offline ? 1.0f : 0.25f) || dt < 0) kns_st[i].have = 0;   /* OfflineTest runs from the 250 ms tick */
        else {
            float dx = m[9] - kns_st[i].pos[0], dz = m[11] - kns_st[i].pos[2];
            if (dx * dx + dz * dz > kns.snap * kns.snap) kns_st[i].have = 0;      /* respawn / teleport */
        }
    }
    kns_st[i].t = now; memcpy(kns_st[i].pos, m + 9, 12);
    if (!kns_st[i].have) { kns_st[i].have = 1; kns_st[i].yaw = yaw; kns_st[i].vel = 0; return; }
    if (dt < 0.0005f) return;
    d = kns_wrap(yaw - kns_st[i].yaw);
    w = 2.0f / (kns.tau > 0.001f ? kns.tau : 0.001f);         /* critically damped spring: acc = w^2 d - 2 w v */
    kns_st[i].vel += (w * w * d - 2.0f * w * kns_st[i].vel) * dt;
    { float mx = klrigid_remote_cap(fabsf(d), kns.maxdps * 0.0174532925f);   /* klrigid.c: PD2 curve with [Rigid] Remote=1, else this flat cap */ if (kns_st[i].vel > mx) kns_st[i].vel = mx; if (kns_st[i].vel < -mx) kns_st[i].vel = -mx; }
    step = kns_st[i].vel * dt;
    if ((d > 0 && step > d) || (d < 0 && step < d)) { step = d; kns_st[i].vel = 0; }   /* no overshoot */
    kns_st[i].yaw = kns_wrap(kns_st[i].yaw + step);
    if (kns.offline) kns_st[i].yaw = kns_wrap(yaw + 0.17453293f);  /* OfflineTest (N5: at the 250 ms tick the spring is always caught up): write yaw +10 deg, read it back */
    if (fabsf(kns_wrap(kns_st[i].yaw - yaw)) < 0.0005f) return;                    /* already there: leave the game's matrix */
    c = cosf(kns_st[i].yaw); s = sinf(kns_st[i].yaw);
    m[0] = c; m[2] = s; m[6] = mir ? s : -s; m[8] = mir ? -c : c;
    vt = klh_rd32(B);
    { DWORD fn = vt ? klh_rd32(vt + 0x8c) : 0;
      if (!fn) return;
      __try { ((kns_set_fn)(DWORD_PTR)fn)((void *)(DWORD_PTR)B, 0, m, m + 9); kns_n_set++;
              if (kns.offline) {                                   /* OfflineTest: did the call place what was passed? */
                  float r[12]; DWORD xf2 = klh_rd32(B + 4);
                  if (xf2 && klh_rd(xf2, r, sizeof r) && fabsf(r[0] - m[0]) < 0.01f && fabsf(r[2] - m[2]) < 0.01f && fabsf(r[6] - m[6]) < 0.01f &&
                      fabsf(r[8] - m[8]) < 0.01f && fabsf(r[9] - m[9]) < 1.0f && fabsf(r[11] - m[11]) < 1.0f) kns_n_rbok++;
                  else { if (kns_n_rbbad++ < 5) klog("netsmooth: read-back differs: wrote %.2f %.2f %.2f %.2f t %.0f %.0f, read %.2f %.2f %.2f %.2f t %.0f %.0f",
                                                       m[0], m[2], m[6], m[8], m[9], m[11], r[0], r[2], r[6], r[8], r[9], r[11]); }
              } }
      __except (EXCEPTION_EXECUTE_HANDLER) { kns.on = 0; klog("netsmooth: fault in the body placement call: smoother off"); } }
}

/* CamYaw (re\netsmooth_camyaw.md): the remote camera yaw is the int16 [R+0xe0] (R = [P+0x274c], 1024 per turn); 0x5d31c0 turns it
   into the float [P+0x2808] = (short)[R+0xe0] / 162.97. We write a smoothed int16 there AFTER the stock update and put the raw
   one back BEFORE the next stock update, so 0x519e80 never extrapolates from our number. 0x5d31c0 is not in a vtable (SHIP refuses
   code patches), so [R+0xe0] is the only write target. GUESS: 0x5d31c0 runs after slot 393 in the frame (the "movement saw our
   write n / m" counter in the summary line tells; if it stays near 0 the smoothing does nothing visible). */
static float kns_wrapu(float a) { while (a > 512.0f) a -= 1024.0f; while (a < -512.0f) a += 1024.0f; return a; }

/* put the raw value back if our write is still there; pl = the ZFFPlayer. Safe to call with nothing outstanding. */
static void kns_cy_undo(DWORD pl, int i)
{
    SHORT cur = 0, raw;
    if (!kns_st[i].cy_pend) return;
    kns_st[i].cy_pend = 0;
    if (!kns_st[i].cy_r || klh_rd32(pl + 0x274c) != kns_st[i].cy_r) return;            /* the replica is gone or replaced */
    if (!klh_rd(kns_st[i].cy_r + 0xe0, &cur, 2) || cur != (SHORT)kns_st[i].cy_out) return;   /* the game wrote it since: nothing to give back */
    raw = (SHORT)kns_st[i].cy_raw;
    if (klh_data((void *)(DWORD_PTR)(kns_st[i].cy_r + 0xe0), &raw, 2, "remote camera yaw (raw put back)")) { kns_st[i].cy_nr++; kns_n_cyr++; }
}

static void kns_cy_pre(DWORD pl)
{   /* before the stock update: count whether the movement code saw our write, then give the raw value back */
    int i = kns_index(pl);
    if (i < 0 || !kns_st[i].cy_pend) return;
    { DWORD pp = kns_st[i].cy_r ? klh_rd32(kns_st[i].cy_r + 0x540) : 0; float f = 0;
      if (pp && klh_rd(pp + 0x2808, &f, 4)) { kns_n_cyask++; if (fabsf(f - (float)kns_st[i].cy_out / 162.97f) < 1e-3f) kns_n_cyseen++; } }
    kns_cy_undo(pl, i);
}

static void kns_cy_do(DWORD pl, int i)
{
    DWORD R = klh_rd32(pl + 0x274c); SHORT raw = 0; BYTE f548 = 0; float pos[3] = {0, 0, 0}, d, dt, w, step, off, o; int reset, out; LARGE_INTEGER now, fq;
    DWORD me;
    if (!kns_local(&me) || pl == me) return;                     /* never the local player */
    { BYTE fl = 0; if (!klh_rd(pl + 0x2720, &fl, 1) || (fl & 2)) return; }
    if (!R || klh_rd32(R + 0x540) != pl) return;                 /* offline Arcade has no R: nothing is written there */
    if (!klh_rd(R + 0xe0, &raw, 2)) return;
    klh_rd(R + 0x548, &f548, 1); klh_rd(pl + 0x460, pos, sizeof pos);
    QueryPerformanceCounter(&now); QueryPerformanceFrequency(&fq);
    dt = kns_st[i].cy_have ? (float)(now.QuadPart - kns_st[i].cy_t.QuadPart) / (float)fq.QuadPart : 0;
    reset = !kns_st[i].cy_have || dt > 0.25f || dt < 0 || f548 == 0xff || kns_st[i].cy_r != R;
    if (!reset) {
        float dx = pos[0] - kns_st[i].cy_pos[0], dz = pos[2] - kns_st[i].cy_pos[2];
        if (dx * dx + dz * dz > kns.snap * kns.snap) reset = 1;                                  /* respawn / teleport */
        else if (fabsf(kns_wrapu((float)raw - kns_st[i].cy_s)) > kns.cysnapu) reset = 1;         /* a real turn-around: follow at once */
    }
    memcpy(kns_st[i].cy_pos, pos, sizeof pos); kns_st[i].cy_r = R;
    if (reset) { kns_st[i].cy_have = 1; kns_st[i].cy_s = (float)raw; kns_st[i].cy_vel = 0; kns_st[i].cy_t = now; return; }
    if (dt >= 0.0005f) {                                         /* a second call within 0.5 ms only re-writes the state below */
        float s = kns_st[i].cy_s, h; int k, nsub = (int)(dt / 0.008f) + 1;
        kns_st[i].cy_t = now;
        w = 2.0f / (kns.cytau > 0.001f ? kns.cytau : 0.001f);   /* critically damped spring, as the body yaw above */
        h = dt / (float)nsub;                                   /* explicit Euler is stable only for 2*w*h < 2: sub-steps of at most 8 ms */
        for (k = 0; k < nsub; k++) {
            d = kns_wrapu((float)raw - s);
            kns_st[i].cy_vel += (w * w * d - 2.0f * w * kns_st[i].cy_vel) * h;
            if (kns_st[i].cy_vel > kns.cymaxu) kns_st[i].cy_vel = kns.cymaxu;
            if (kns_st[i].cy_vel < -kns.cymaxu) kns_st[i].cy_vel = -kns.cymaxu;
            step = kns_st[i].cy_vel * h;
            if ((d > 0 && step > d) || (d < 0 && step < d)) { step = d; kns_st[i].cy_vel = 0; }       /* no overshoot */
            s += step;
        }
        kns_st[i].cy_s = s;
    }
    off = kns_wrapu(kns_st[i].cy_s - (float)raw);
    kns_st[i].cy_s = (float)raw + off;                           /* stays on raw's int16 branch */
    o = (float)raw + floorf(off + 0.5f);
    out = (int)(SHORT)(int)o;                                    /* wrap, not clamp: raw is a free int16 and 65536 is a multiple of 1024 */
    if (kns.log && GetTickCount() - kns_st[i].cy_log >= 1000) {
        kns_st[i].cy_log = GetTickCount();
        klog("netsmooth camyaw: player %08lx raw %d out %d (smoothed %.1f) writes %ld restores %ld", pl, (int)raw, out, kns_st[i].cy_s, kns_st[i].cy_nw, kns_st[i].cy_nr);
    }
    if (out == (int)raw) return;                                 /* already there: leave the game's value */
    { SHORT v = (SHORT)out;
      if (klh_data((void *)(DWORD_PTR)(R + 0xe0), &v, 2, "remote camera yaw (smoothed)")) {
          kns_st[i].cy_pend = 1; kns_st[i].cy_out = out; kns_st[i].cy_raw = (int)raw; kns_st[i].cy_nw++; kns_n_cyw++;
      } }
}

static void kns_camyaw(DWORD pl)
{
    int i = kns_index(pl);
    if (i < 0) return;
    __try { kns_cy_do(pl, i); }
    __except (EXCEPTION_EXECUTE_HANDLER) { kns.cy = 0; klog("netsmooth: fault in the camera yaw step: CamYaw off"); }
}

static void __fastcall kns_update(void *self, void *edx)
{
    if (!IsBadReadPtr(self, 0x2750)) {                           /* give the raw camera yaw back first, whatever the keys say now */
        __try { kns_cy_pre((DWORD)(DWORD_PTR)self); } __except (EXCEPTION_EXECUTE_HANDLER) { kns.cy = 0; klog("netsmooth: fault in the camera yaw restore: CamYaw off"); }
    }
    ((kns_fn)(DWORD_PTR)kns_orig)(self, edx);                    /* the stock update first */
    kns_n_upd++;
    if (kns.on && kns.active && !IsBadReadPtr(self, 0x2750)) {
        kns_smooth((DWORD)(DWORD_PTR)self);
        if (kns.cy) kns_camyaw((DWORD)(DWORD_PTR)self);
    }
}

static void kns_restore_all(const char *why)
{
    int i, n = 0;
    for (i = 0; i < KNS_NPL; i++) {
        if (!kns_obj[i]) continue;
        kns_cy_undo(kns_obj[i], i);                              /* an outstanding camera yaw write goes back to raw first, whatever the vtable shows */
        if (klh_rd32(kns_obj[i]) == kns_ours()) {                /* freed memory showing our table is not expected */
            DWORD vt = (DWORD)(DWORD_PTR)KLH_VA(KNS_PLAYER_VT);
            if (klh_data((void *)(DWORD_PTR)kns_obj[i], &vt, 4, "ZFFPlayer vtable pointer (restore)")) n++;
        }
        kns_obj[i] = 0; kns_st[i].have = 0; kns_cy_clear(i);
    }
    if (n && kns.log) klog("netsmooth: %d player object(s) given back the stock vtable (%s)", n, why);
}

static int kns_gate(void)
{   /* same gate as klnetfix.c: online FA session, not ranked */
    DWORD sm, role = 0, mode = 0, state = 0, svc; BYTE ranked = 1; int act;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return 0;
    svc = klh_rd32(sm + 0x17c);
    /* 0xbd597c ZOnlineServiceSteam (online); 0xbd5ad4 ZOnlineServiceWintel, its subclass (RTTI; overrides slots 0, 40, 45 JoinSession,
       69-71, inherits CreateSession and the +0x36f / +0x370 layout). GUESS: Wintel = System Link - H2 (2026-10-23) ran a System Link
       round with the Steam-only gate and the smoother never switched on. */
    act = (role == 2 || role == 3) && mode == 4 && state >= 0x13 && state <= 0x1f && svc &&
          (klh_rd32(svc) == 0x00bd597c || klh_rd32(svc) == 0x00bd5ad4) && klh_rd(svc + 0x36f, &ranked, 1) && !ranked;
    if (act && role == 2) {
        BYTE props[0x20];
        if (!klh_rd(svc + 0x370, props, sizeof props) || ((props[8] >> 5) & 1)) act = 0;
    }
    if (!act && kns.log && (role == 2 || role == 3) && mode == 4 && state >= 0x13 && state <= 0x1f) {
        static DWORD told; DWORD vt = svc ? klh_rd32(svc) : 0;
        if (told != vt + 1) { told = vt + 1; klog("netsmooth: session refused: role %lu state 0x%lx service %08lx vtable %08lx ranked byte %u", role, state, svc, vt, ranked); }
    }
    return act;
}

/* [NetSmooth] Probe: reads only (klh_rd), never writes; offline-capable check of the body chain / matrix GUESSES */
static void kns_probe(void)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c)), me = 0, pl, r, p, e, b, xf; int i; float m[12], pos[3];
    if (!gd) return;
    kns_local(&me);
    for (i = 0; i < KNS_NPL && kns.probed < kns.probemax; i++) {
        BYTE fl = 0; int yawok;
        if (!(pl = klh_rd32(gd + 0x828 + 4 * i))) continue;
        klh_rd(pl + 0x2720, &fl, 1);
        r = klh_rd32(pl + 0x274c); p = r ? klh_rd32(r + 0x540) : 0;
        if (!r) p = pl;     /* offline (N1, 2026-10-20: [P+0x274c] is 0 for every player in Arcade): test the rest of the chain from P itself (GUESS [R+0x540] = P) */
        e = p ? klh_rd32(p + 4) : 0; e = e ? klh_rd32(e + 0x50) : 0;
        b = e ? klh_rd32(e + 0x60) : 0; xf = b ? klh_rd32(b + 4) : 0;
        memset(pos, 0, sizeof pos); klh_rd(pl + 0x460, pos, sizeof pos);
        if (!xf || !klh_rd(xf, m, sizeof m)) {
            klog("netsmooth probe: #%d %08lx%s vt %08lx fl %02x chain r %08lx p %08lx(=P? %d) b %08lx xf %08lx: no matrix; pos %.0f %.0f %.0f",
                 i, pl, pl == me ? " ME" : "", klh_rd32(pl), fl, r, p, p == pl, b, xf, pos[0], pos[1], pos[2]);
        } else {
            yawok = !(fabsf(m[4] - 1.0f) > 0.03f || fabsf(m[1]) > 0.03f || fabsf(m[3]) > 0.03f || fabsf(m[5]) > 0.03f || fabsf(m[7]) > 0.03f ||
                      fabsf(m[8] - m[0]) > 0.03f || fabsf(m[6] + m[2]) > 0.03f);
            klog("netsmooth probe: #%d %08lx%s fl %02x p=P %d b %08lx b.vt %08lx | %.2f %.2f %.2f / %.2f %.2f %.2f / %.2f %.2f %.2f | t %.0f %.0f %.0f | yaw %s %.1f | pos %.0f %.0f %.0f",
                 i, pl, pl == me ? " ME" : "", fl, p == pl, b, klh_rd32(b), m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11],
                 yawok ? "ok" : "NOT-pure", atan2f(m[2], m[0]) * 57.2957795f, pos[0], pos[1], pos[2]);
        }
        kns.probed++;
    }
    if (kns.probed >= kns.probemax) klog("netsmooth probe: %d lines written, probe done", kns.probed);
}

static void klnetsmooth_tick(int game_thread)
{
    static DWORD last; DWORD now = GetTickCount(), gd, me, pl; int act, i, n = 0;
    /* GAME THREAD ONLY (review 2026-10-19): the fallback ticker must not swap or restore vtable pointers while the game thread
       runs or frees player objects. The wrapper kns_update also runs on the game thread, so no lock is needed. */
    if (!game_thread || !klh_exe_ok || now - last < 250) return;
    last = now;
    if (kns.probe && kns.probed < kns.probemax && now - kns.probet >= (DWORD)kns.probems) { kns.probet = now; kns_probe(); }
    if (!kns.on) { if (kns.active) { kns.active = 0; kns_restore_all("smoother off"); } return; }   /* a fault switched it off */
    act = kns_gate();
#ifdef KLHOOK_TEST
    if (kns.offline && !act) { DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598)), role = 0; if (!sm || (klh_rd(sm + 0x54, &role, 4) && role != 2 && role != 3)) act = 1; }   /* OfflineTest: not in an online session */
#endif
    if (!act) { if (kns.active) { kns.active = 0; kns_restore_all("not an online unranked session"); } return; }
    gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c));
    if (!gd) { kns.active = 0; kns_restore_all("level end"); return; }
    if (!kns_orig) {
        DWORD vt = (DWORD)(DWORD_PTR)KLH_VA(KNS_PLAYER_VT);
        if (!klh_rd((DWORD_PTR)vt - 4, kns_vtblk, sizeof kns_vtblk) || kns_vt[KNS_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(0x506350)) {
            klog("netsmooth: ZFFPlayer slot %d is %08lx, not 0x506350: this build is not the one read - smoother off", KNS_SLOT, kns_vt[KNS_SLOT]);
            kns.on = 0; return;
        }
        kns_orig = kns_vt[KNS_SLOT]; kns_vt[KNS_SLOT] = (DWORD)(DWORD_PTR)kns_update;
    }
    if (!kns_local(&me) || !me) return;                          /* local player unknown: swap nothing (it must never be swapped) */
    for (i = 0; i < KNS_NPL; i++) {                              /* drop what is gone */
        if (kns_obj[i] && klh_rd32(kns_obj[i]) != kns_ours()) { kns_cy_undo(kns_obj[i], i); kns_obj[i] = 0; kns_st[i].have = 0; kns_cy_clear(i); }
    }
    for (i = 0; i < KNS_NPL; i++) {
        pl = klh_rd32(gd + 0x828 + 4 * i);
        if (!pl || pl == me || kns_index(pl) >= 0) continue;
        if (klh_rd32(pl) != (DWORD)(DWORD_PTR)KLH_VA(KNS_PLAYER_VT)) continue;
        { int k; for (k = 0; k < KNS_NPL && kns_obj[k]; k++) ;
          if (k == KNS_NPL) break;
          { DWORD vt = kns_ours();
            if (klh_data((void *)(DWORD_PTR)pl, &vt, 4, "ZFFPlayer vtable pointer (private copy)")) { kns_obj[k] = pl; n++; kns_st[k].have = 0; kns_cy_clear(k); } } }
    }
    kns.active = 1;
    if (kns.log && (n || !kns.told)) {
        BYTE fl = 0; int cnt = 0; for (i = 0; i < KNS_NPL; i++) if (kns_obj[i]) { cnt++; if (!kns.told) { klh_rd(kns_obj[i] + 0x2720, &fl, 1); klog("netsmooth: remote player %08lx flags[+0x2720]=%02x", kns_obj[i], fl); } }
        klog("netsmooth: %d remote player object(s) swapped (%d new); updates %ld, placed %ld, skipped (not a pure yaw) %ld", cnt, n, kns_n_upd, kns_n_set, kns_n_skip);
        kns.told = 1;
    }
#ifdef KLHOOK_TEST
    if (kns.offline) {                                            /* N4: offline nothing calls slot 393 (replica path); call the smoother from here */
        for (i = 0; i < KNS_NPL; i++) if (kns_obj[i] && klh_rd32(kns_obj[i]) == kns_ours()) kns_smooth(kns_obj[i]);
    }
#endif
    if (kns.log) {                                                /* a count line every 10 s while anything moves (N3: it was printed only on new swaps) */
        static DWORD tsum; static LONG lu = -1;
        if (now - tsum >= 10000 && kns_n_upd + kns_n_set + kns_n_skip != lu) {
            tsum = now; lu = kns_n_upd + kns_n_set + kns_n_skip;
            klog("netsmooth: updates %ld, placed %ld (read back ok %ld, differs %ld), skipped (not a pure yaw) %ld", kns_n_upd, kns_n_set, kns_n_rbok, kns_n_rbbad, kns_n_skip);
            if (kns.cy) klog("netsmooth camyaw: writes %ld, restores %ld, movement saw our write %ld / %ld", kns_n_cyw, kns_n_cyr, kns_n_cyseen, kns_n_cyask);
        }
    }
}

static void klnetsmooth_init(void)
{
    char b[32];
    kns.on = GetPrivateProfileIntA("NetSmooth", "Enable", 0, klh_ini) != 0;
    kns.log = GetPrivateProfileIntA("NetSmooth", "Log", 0, klh_ini) != 0;
    GetPrivateProfileStringA("NetSmooth", "MaxTurnDegPerSec", "540", b, sizeof b, klh_ini); kns.maxdps = (float)atof(b);
    GetPrivateProfileStringA("NetSmooth", "SmoothMs", "90", b, sizeof b, klh_ini); kns.tau = (float)atof(b) / 1000.0f;
    GetPrivateProfileStringA("NetSmooth", "SnapUnits", "300", b, sizeof b, klh_ini); kns.snap = (float)atof(b);
    if (kns.maxdps < 30.0f) kns.maxdps = 30.0f;
    kns.cy = kns.on && GetPrivateProfileIntA("NetSmooth", "CamYaw", 0, klh_ini) != 0;       /* opt-in, only with Enable=1 */
    GetPrivateProfileStringA("NetSmooth", "CamSmoothMs", "70", b, sizeof b, klh_ini); kns.cytau = (float)atof(b) / 1000.0f;
    GetPrivateProfileStringA("NetSmooth", "MaxCamDegPerSec", "720", b, sizeof b, klh_ini); kns.cymaxu = (float)atof(b);
    GetPrivateProfileStringA("NetSmooth", "CamSnapDeg", "150", b, sizeof b, klh_ini); kns.cysnapu = (float)atof(b);
    if (!(kns.cytau >= 0.0f && kns.cytau < 10.0f)) kns.cytau = 0.07f;     /* nan / inf / absurd in the ini */
    if (!(kns.cymaxu < 100000.0f)) kns.cymaxu = 720.0f;
    if (!(kns.cysnapu < 100000.0f)) kns.cysnapu = 150.0f;
    if (!(kns.cymaxu >= 30.0f)) kns.cymaxu = 30.0f;
    if (kns.cysnapu < 10.0f) kns.cysnapu = 10.0f;
    if (kns.cysnapu > 180.0f) kns.cysnapu = 180.0f;               /* above half a turn the shortest-path rule cannot tell */
    kns.cymaxu *= 1024.0f / 360.0f; kns.cysnapu *= 1024.0f / 360.0f;   /* degrees -> yaw units (1024 per turn) */
#ifdef KLHOOK_TEST
    kns.offline = GetPrivateProfileIntA("NetSmooth", "OfflineTest", 0, klh_ini) != 0;   /* TEST build only: smooth the Arcade AI heisters */
    if (kns.offline) klog("netsmooth: OfflineTest=1 (TEST build): the smoother also runs offline, on non-local players with the master flag (Arcade AI heisters)");
#endif
    kns.probe = GetPrivateProfileIntA("NetSmooth", "Probe", 0, klh_ini) != 0;
    kns.probems = GetPrivateProfileIntA("NetSmooth", "ProbeMs", 1000, klh_ini); if (kns.probems < 250) kns.probems = 250;
    kns.probemax = GetPrivateProfileIntA("NetSmooth", "ProbeLines", 400, klh_ini);
    if (kns.probe) klog("netsmooth: PROBE on (read-only): every %d ms, up to %d lines, the body chain / matrix of every player", kns.probems, kns.probemax);
    if (kns.cy)
        klog("netsmooth: CamYaw=1 (opt-in) CamSmoothMs=%.0f MaxCamDegPerSec=%.0f CamSnapDeg=%.0f: smoothed int16 [R+0xe0] of remote players, raw put back before each stock update; see re\\netsmooth_camyaw.md",
             kns.cytau * 1000.0f, kns.cymaxu * 360.0f / 1024.0f, kns.cysnapu * 360.0f / 1024.0f);
    if (kns.on)
        klog("netsmooth: on; MaxTurnDegPerSec=%.0f SmoothMs=%.0f SnapUnits=%.0f Log=%d; private ZFFPlayer vtable for REMOTE players only, online FA not ranked; EXPERIMENT (write path proven offline N6, online untested): see re\\netcode_smooth.md",
             kns.maxdps, kns.tau * 1000.0f, kns.snap, kns.log);
}

#endif /* KLNETSMOOTH_C */
