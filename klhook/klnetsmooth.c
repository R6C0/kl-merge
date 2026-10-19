/* klnetsmooth.c - [NetSmooth]: a receiver-side smoother for the DISPLAYED heading of REMOTE players (online FA, not ranked).
 * OFF unless [NetSmooth] Enable=1. Written statically (nothing here has run in the game). Research: re\netcode_smooth.md.
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

static struct { int on, log; float maxdps, tau, snap; volatile LONG active; int told; } kns;
static DWORD kns_vt[KNS_NSLOT];                       /* the private vtable */
static DWORD kns_orig;                                /* the stock slot 393 function */
static DWORD kns_obj[KNS_NPL];                        /* objects given the private vtable */
static struct { int have; float yaw, vel, pos[3]; LARGE_INTEGER t; } kns_st[KNS_NPL];
static LONG kns_n_upd, kns_n_set, kns_n_skip;

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

/* the body of player P: B (the object whose vtable slot 0x8c places it) and its transform address, or 0 */
static int kns_body(DWORD pl, DWORD *B, DWORD *xf)
{
    DWORD r = klh_rd32(pl + 0x274c), p, e, b;
    if (!r || !(p = klh_rd32(r + 0x540)) || !(e = klh_rd32(p + 4)) || !(e = klh_rd32(e + 0x50)) || !(b = klh_rd32(e + 0x60))) return 0;
    if (!(*xf = klh_rd32(b + 4))) return 0;
    *B = b; return 1;
}

static int kns_index(DWORD pl) { int i; for (i = 0; i < KNS_NPL; i++) if (kns_obj[i] == pl) return i; return -1; }

typedef void (__fastcall *kns_fn)(void *self, void *edx);
typedef void (__fastcall *kns_set_fn)(void *self, void *edx, float *mat, float *pos);

static void kns_smooth(DWORD pl)
{
    DWORD B, xf, me, vt; float m[12]; float c, s, yaw, d, dt = 0, step, w; int i; LARGE_INTEGER now, fq;
    if (!kns_local(&me) || pl == me) return;                    /* never the local player */
    { BYTE fl = 0; if (!klh_rd(pl + 0x2720, &fl, 1) || (fl & 2)) return; }   /* the master branch is not a remote */
    if (!kns_body(pl, &B, &xf) || !klh_rd(xf, m, sizeof m)) return;
    for (i = 0; i < 12; i++) if (m[i] != m[i]) return;          /* NaN */
    /* a pure yaw about Y: row 1 / column 1 are the unit Y axis, the 2x2 block is a rotation */
    if (fabsf(m[4] - 1.0f) > 0.03f || fabsf(m[1]) > 0.03f || fabsf(m[3]) > 0.03f || fabsf(m[5]) > 0.03f || fabsf(m[7]) > 0.03f ||
        fabsf(m[8] - m[0]) > 0.03f || fabsf(m[6] + m[2]) > 0.03f) { kns_n_skip++; return; }
    i = kns_index(pl); if (i < 0) return;
    yaw = atan2f(m[2], m[0]);
    QueryPerformanceCounter(&now); QueryPerformanceFrequency(&fq);
    if (kns_st[i].have) {
        dt = (float)(now.QuadPart - kns_st[i].t.QuadPart) / (float)fq.QuadPart;
        if (dt > 0.25f || dt < 0) kns_st[i].have = 0;
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
    { float mx = kns.maxdps * 0.0174532925f; if (kns_st[i].vel > mx) kns_st[i].vel = mx; if (kns_st[i].vel < -mx) kns_st[i].vel = -mx; }
    step = kns_st[i].vel * dt;
    if ((d > 0 && step > d) || (d < 0 && step < d)) { step = d; kns_st[i].vel = 0; }   /* no overshoot */
    kns_st[i].yaw = kns_wrap(kns_st[i].yaw + step);
    if (fabsf(kns_wrap(kns_st[i].yaw - yaw)) < 0.0005f) return;                    /* already there: leave the game's matrix */
    c = cosf(kns_st[i].yaw); s = sinf(kns_st[i].yaw);
    m[0] = c; m[2] = s; m[6] = -s; m[8] = c;
    vt = klh_rd32(B);
    { DWORD fn = vt ? klh_rd32(vt + 0x8c) : 0;
      if (!fn) return;
      __try { ((kns_set_fn)(DWORD_PTR)fn)((void *)(DWORD_PTR)B, 0, m, m + 9); kns_n_set++; }
      __except (EXCEPTION_EXECUTE_HANDLER) { kns.on = 0; klog("netsmooth: fault in the body placement call: smoother off"); } }
}

static void __fastcall kns_update(void *self, void *edx)
{
    ((kns_fn)(DWORD_PTR)kns_orig)(self, edx);                    /* the stock update first */
    kns_n_upd++;
    if (kns.on && kns.active && !IsBadReadPtr(self, 0x2750)) kns_smooth((DWORD)(DWORD_PTR)self);
}

static void kns_restore_all(const char *why)
{
    int i, n = 0;
    for (i = 0; i < KNS_NPL; i++) {
        if (!kns_obj[i]) continue;
        if (klh_rd32(kns_obj[i]) == kns_ours()) {                /* freed memory showing our table is not expected */
            DWORD vt = (DWORD)(DWORD_PTR)KLH_VA(KNS_PLAYER_VT);
            if (klh_data((void *)(DWORD_PTR)kns_obj[i], &vt, 4, "ZFFPlayer vtable pointer (restore)")) n++;
        }
        kns_obj[i] = 0; kns_st[i].have = 0;
    }
    if (n && kns.log) klog("netsmooth: %d player object(s) given back the stock vtable (%s)", n, why);
}

static int kns_gate(void)
{   /* same gate as klnetfix.c: online FA session, not ranked */
    DWORD sm, role = 0, mode = 0, state = 0, svc; BYTE ranked = 1; int act;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return 0;
    svc = klh_rd32(sm + 0x17c);
    act = (role == 2 || role == 3) && mode == 4 && state >= 0x13 && state <= 0x1f && svc && klh_rd32(svc) == 0x00bd597c &&
          klh_rd(svc + 0x36f, &ranked, 1) && !ranked;
    if (act && role == 2) {
        BYTE props[0x20];
        if (!klh_rd(svc + 0x370, props, sizeof props) || ((props[8] >> 5) & 1)) act = 0;
    }
    return act;
}

static void klnetsmooth_tick(int game_thread)
{
    static DWORD last; DWORD now = GetTickCount(), gd, me, pl; int act, i, n = 0;
    /* GAME THREAD ONLY (review 2026-10-19): the fallback ticker must not swap or restore vtable pointers while the game thread
       runs or frees player objects. The wrapper kns_update also runs on the game thread, so no lock is needed. */
    if (!game_thread || !klh_exe_ok || now - last < 250) return;
    last = now;
    if (!kns.on) { if (kns.active) { kns.active = 0; kns_restore_all("smoother off"); } return; }   /* a fault switched it off */
    act = kns_gate();
    if (!act) { if (kns.active) { kns.active = 0; kns_restore_all("not an online unranked session"); } return; }
    gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c));
    if (!gd) { kns.active = 0; kns_restore_all("level end"); return; }
    if (!kns_orig) {
        DWORD vt = (DWORD)(DWORD_PTR)KLH_VA(KNS_PLAYER_VT);
        if (!klh_rd((DWORD_PTR)vt, kns_vt, sizeof kns_vt) || kns_vt[KNS_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(0x506350)) {
            klog("netsmooth: ZFFPlayer slot %d is %08lx, not 0x506350: this build is not the one read - smoother off", KNS_SLOT, kns_vt[KNS_SLOT]);
            kns.on = 0; return;
        }
        kns_orig = kns_vt[KNS_SLOT]; kns_vt[KNS_SLOT] = (DWORD)(DWORD_PTR)kns_update;
    }
    if (!kns_local(&me) || !me) return;                          /* local player unknown: swap nothing (it must never be swapped) */
    for (i = 0; i < KNS_NPL; i++) {                              /* drop what is gone */
        if (kns_obj[i] && klh_rd32(kns_obj[i]) != kns_ours()) { kns_obj[i] = 0; kns_st[i].have = 0; }
    }
    for (i = 0; i < KNS_NPL; i++) {
        pl = klh_rd32(gd + 0x828 + 4 * i);
        if (!pl || pl == me || kns_index(pl) >= 0) continue;
        if (klh_rd32(pl) != (DWORD)(DWORD_PTR)KLH_VA(KNS_PLAYER_VT)) continue;
        { int k; for (k = 0; k < KNS_NPL && kns_obj[k]; k++) ;
          if (k == KNS_NPL) break;
          { DWORD vt = kns_ours();
            if (klh_data((void *)(DWORD_PTR)pl, &vt, 4, "ZFFPlayer vtable pointer (private copy)")) { kns_obj[k] = pl; n++; kns_st[k].have = 0; } } }
    }
    kns.active = 1;
    if (kns.log && (n || !kns.told)) {
        BYTE fl = 0; int cnt = 0; for (i = 0; i < KNS_NPL; i++) if (kns_obj[i]) { cnt++; if (!kns.told) { klh_rd(kns_obj[i] + 0x2720, &fl, 1); klog("netsmooth: remote player %08lx flags[+0x2720]=%02x", kns_obj[i], fl); } }
        klog("netsmooth: %d remote player object(s) swapped (%d new); updates %ld, placed %ld, skipped (not a pure yaw) %ld", cnt, n, kns_n_upd, kns_n_set, kns_n_skip);
        kns.told = 1;
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
    if (kns.on)
        klog("netsmooth: on; MaxTurnDegPerSec=%.0f SmoothMs=%.0f SnapUnits=%.0f Log=%d; private ZFFPlayer vtable for REMOTE players only, online FA not ranked; EXPERIMENT (never run): see re\\netcode_smooth.md",
             kns.maxdps, kns.tau * 1000.0f, kns.snap, kns.log);
}

#endif /* KLNETSMOOTH_C */
