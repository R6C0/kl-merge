/*
 * klfreeclimb.c - DEAD MEN'S FREE CLIMB for the local player: hold W (forward), tap E at a ledge 25 .. 220 high and he
 * pulls himself up with Dead Men's own /Movement/Climb/Up/<class> clip. No level data: any collision with flag 0x20 is
 * climbable, as in Dead Men. Part of KLHook (included by klhook.c, SHIP and TEST alike), ticked from klh_tick on the
 * main loop's gameplay call of SteamAPI_RunCallbacks.
 *
 * CREDIT: luvsic's "A Newer Perspective" loader, loader/climb.inc (third_party/anp/loader/climb.inc and
 * build/claude_stage/x/luvsic_f38/climb.inc, 747 lines, the same file), and his CLAUDE.md 'Climbing' / 'CEG-clean
 * loader'. The method, every address below and the probe are his; this file is a port of it into KLHook's style
 * (MSVC, klh_* reads and writes, our tick instead of a second SteamAPI hook, SEH instead of his VEH + asm guard).
 * HIS EVIDENCE: live in his loader 11 Oct 08:47 and 08:50 on Dead Men's M01 ported to Dog Days, unattended, five of
 * five spots (van rear -> roof High 200, van roof -> shelter Medium 140, Crate_C Low 97, Crate_A Medium 128, crate
 * stack High 177), each ending 2 .. 4 cm from the computed end place, no snap, camera following, control back.
 * OF THIS PORT NOTHING HAS RUN IN THE GAME.
 *
 * WHAT HE DOES (and this file does the same)
 *  - Dead Men's ZFFPlayerMovementClimb test (kaneandlynch.exe 0x605b50) re-done on Dog Days' world: four rays straight
 *    down from feet + 310 at 25 / 40 / 55 / 70 in front (mask 0x20, layer 11) through ZCollisionWintel's raycast
 *    (kl2 0x7daa80, [0x138c868], Havok path only: [0xcd9c60] == 1); for each candidate top (non-decreasing): a clear
 *    way at h + 15 (mask 0x28: hero-only walls block), 180 head room, a wall face at h - 1. A rigid body or an actor
 *    under a ray calls it off. Class by h over his feet: 25 < h <= 120 Low (stand 81 back from the face; Sprint_Low
 *    when sprinting), <= 170 Medium (47), <= 220 High (47).
 *  - The end place: the clip's own root motion (0x5a5030 on the GROUND bone) from event 5 to the last frame, turned
 *    into the world by his rotation (0x857110's rows), added to the start S and lifted by h; then pushed so it lies at
 *    least MinIn past the face when the ground there is the same top and the way is clear (his 'minin').
 *  - The move: a REAL ZFFActionVaultOver (kind 0x2B, made by the player's own factory vt +0x384) whose vptr is pointed
 *    at a COPY of its vtable (0xbb5188, 12 slots) that lives in this DLL, with slot 2 Start, 4 Update, 5 End and 10
 *    AnimEnd replaced by the functions below; started through the player's dispatcher (vt +0x370). Start: leave cover
 *    0x5fcb80 (as the stock start does), the collision off (vt +0x560; the stock End 0x82f780 switches it back on
 *    through vt +0x564), Play (vt +0x204), ONE AlignTo (vt +0x208) to the end place over the whole clip, the camera
 *    0x798d00. Update: the stock vault update 0x5b1e40 (camera follow), ends at the clip's end, a lost channel or a
 *    time-out. AnimEnd: only OUR channel ends it (the vault's own slot 10 says yes to ANY channel - re\climb.md 1.3).
 *    End: the stock End (proxy, collision, stance, teleport to +0x38 / +0x68) and, after a completed clip more than
 *    25 from the end place, one unforced teleport there (0x82cc40, a4 = 0: a forced one would arm the 0.8 s cooldown).
 *  - Why a vault and not a mini animation (our klclimb.c): the vault never subscribes its channel to clip events and
 *    answers slot 11 with `mov al, 1`, so Dead Men's event 5 cannot reach ZFFActionGeneric's case 5 - the crash at
 *    kl2+0x7e400 that klclimb.c met (re\climb_crash.md). Our builds' players' clips carry that event as 105: both ids
 *    are looked up here (5 first).
 *
 * CEG (his 'CEG-clean loader', and klhook.c's patch guard): NO code byte and no vtable of kl2.exe is changed. The
 * vtable copy is this DLL's own data; what is written into the game is data only, through klh_data: the action's
 * vptr and fields (the action pool lives in kl2's .data, 0x15151c0, which is not hashed), [player+0x2d60] = 0 in the
 * start as the stock start does.
 *
 * THE FAULT GUARD. Every call of a game routine runs inside klfc_guard (MSVC __try / __except): a fault on the way is
 * logged ('fclimb: FAULT ...', and klhook.c's VEH has already written its CRASH line and a dump - that is evidence, not
 * a crash), the routine's frames are unwound, the FPU is re-initialised with the control word it had, and the climb is
 * DISABLED for the rest of the session (a climb that was running is aborted under a second guard). His guard did the
 * same with a VEH and an asm landing pad (MinGW has no __try).
 *
 * WHERE IT RUNS: klh_tick (klhook.c) on the game's thread, only when the SteamAPI_RunCallbacks call came from the main
 * loop's GAMEPLAY site (return address 0x87aa82, his filter; klhook.c keeps it in klh_rcb_ra), once a frame; nothing
 * while the game clock [[0xdd2640]+0x48] stands (a pause). The press is Dead Men's: E seen on frame N (armed), the
 * probe on frame N + 1 with W (or the forward axis [player+0xb94] > 0.5) held. When Dog Days itself has a use for E
 * (a stock vault is offered: [player+0x2d60] bit 0x10; an action or a use action runs) the press is left to it.
 *
 * ANY LEVEL, BUT THE CLIPS: the move asks for no level data and is not gated to Arcade or to a non-stock level (it
 * is a player move, not a balance change). It plays ONLY where the level's .ANM has the slot names
 * '/Movement/Climb/Up/Low|Medium|High|Sprint_Low': NONE of the 21 stock Dog Days .ANM files has them (re\climb.md
 * 2.3), so on a stock level the press logs 'clip ... missing in this level's .ANM' and nothing moves. Levels built
 * with Dead Men's animations merged (luvsic's ports, our kl_fa_climb / tab builds that carry the climb slots) climb.
 * ONLINE: the action is local; whether the other machines of a network round see the climb, a slide or a pop was not
 * read (the stock vault start 0x619790 is what the network receiver 0x60c610 replays; this file does not call it).
 *
 * KLHook.ini
 *   [Climb]
 *   Enable=0      1 = on (OFF when the key is absent). With it on, klclimb.c's [EdgeClimb] stays off.
 *   Dry=0         1 = probe and log every press, start nothing (his 'dry')
 *   Log=1         0 = only the start-up line and faults; 1 = press / RESULT / START / END lines; 2 = also every ray
 *   Key=0x45      the virtual key of the press (E); W / forward must be held as well
 *   NeedBlock=0   1 = also ask Dead Men's 'blocked' (moving >= 300 and the proxy at < 75 % of it)
 *   MinIn=30      the end place lies at least this far past the face where that is safe (0 = Dead Men exact, 0 .. 100)
 *   Camera=1      the vault camera's settings (0x798d00: 67, 40, 0.5) during the climb
 *   Snap=1        after a completed clip more than 25 from the end place, one unforced teleport there
 *   Early=0       1 = probe on the frame of the press itself (rope, 2026-10-16). Dead Men probes one frame LATER; in the live logs
 *                 (owner's Retomoto rounds 10-15) the presses at walls ended 'press ignored (action running)' on that next frame:
 *                 Dog Days had started an action of its own for the same key (the line now names its class). Early=1 starts the
 *                 climb before Dog Days can, and only when a ledge with a clip is found; otherwise the press stays Dog Days'.
 *
 * LEVEL CHECK (rope): once per player object the tick logs whether the level's .ANM has the climb slots ('fclimb: level: ...');
 * the KL Merge maps get them from tools\kl_fa_climb.py apply (build\rope\<map>, with Dead Men's hand-on-wall / footstep foley
 * in clip record +0x2C, carried into the level's bank by build\rope's rope_snd.py).
 */
#ifndef KLFREECLIMB_C
#define KLFREECLIMB_C

#include <math.h>

#define KLFC_PLAYER_VT   0x00bb45f4u          /* ZFFPlayer */
#define KLFC_VAULT_VT    0x00bb5188u          /* ZFFActionVaultOver (12 slots; [vt - 4] = its RTTI locator) */
#define KLFC_RIGID_VT    0x00bb09f4u          /* ZHavokRigidBody */
#define KLFC_COLLW_VT    0x00b9a1d4u          /* ZCollisionWintel */
#define KLFC_COLLW       0x0138c868u          /* -> the collision world */
#define KLFC_HAVOK       0x00cd9c60u          /* 1 = the Havok path of 0x5022b0 (else the legacy one) */
#define KLFC_RCB_RA      0x0087aa82u          /* the return address of the gameplay call of SteamAPI_RunCallbacks */
#define KLFC_RAY         0x007daa80u          /* ZCollisionWintel vt +0x2c: (cw; res, 0, o, seg, 0, mask, 1, 0, layer) -> al */
#define KLFC_POSE        0x00857110u          /* (node; M[9], P[3]): rows +Z (the back), up, +X; P = the feet */
#define KLFC_EVENT       0x004a75d0u          /* __stdcall (clip, id, int *) -> the frame of that event, -1 = none */
#define KLFC_ROOT        0x005a5030u          /* (clip; anmdb, float frame, q[4], p[3], mirror): the GROUND bone at a frame */
#define KLFC_CAM_GET     0x008fde70u          /* (player) -> his camera */
#define KLFC_CAM_SET     0x00798d00u          /* (camera; float, float, float): the vault's camera settings */
#define KLFC_TELE        0x0082cc40u          /* (player; M, P, resetVel, force, 0) */
#define KLFC_LEAVECOVER  0x005fcb80u          /* (player): the stock vault start's first call; derefs [player+0x2810] */
#define KLFC_V_UPDATE    0x005b1e40u          /* ZFFActionVaultOver's own update (camera follow) -> al */
#define KLFC_V_END       0x0082f780u          /* ZFFActionVaultOver's own End: proxy, vt +0x564, stance, teleport to +0x38 / +0x68 */
#define KLFC_EVTAB       0x01546f6cu          /* the animation manager; [+0x10] = the clips' event block (0x4a75d0 reads it) */
#define KLFC_CLIPVAR     0x0059d550u          /* (player; u16 slot) -> clip record (draws one number of the game's generator) */
#define KLFC_SYNC        0x004af5b0u          /* (player): the proxy is put at the node */

static struct { int on, dry, log, key, needblock, minin, cam, snap, early; } klfc;
static DWORD klfc_lvlP;                       /* the player object whose level was checked for the climb slots */
static struct {                               /* the climb that runs (act != 0) */
    int active, startT, did560, reached, e5, e6, frames, animEndLogs;
    DWORD act, P, clip, anim, anim0; int animId; float from, to, h;
    float S[3], Final[3], M[9], gv[3], push[3];
    const char *endReason;
} klfc_c;
struct klfc_probe {
    float M[9], Pf[3], F[3], B[3], Wp[3], Wn[3], S[3], Final[3], gv[3], g0[3], ge5[3], ge6[3], gend[3], push[3];
    float h; int cls, frames, e5, e6; DWORD clip; int id; const char *clipName, *why;
};
#pragma pack(push, 1)
struct klfc_ray { float frac, hit[3]; DWORD node; float v0[3], v1[3], v2[3]; BYTE pad[0x100]; };
#pragma pack(pop)
static const struct { const char *name; float max, off; } klfc_cls[3] = { { "Low", 120, 81 }, { "Medium", 170, 47 }, { "High", 220, 47 } };   /* kaneandlynch 0x603340 */
static DWORD klfc_vt[13];                     /* [0] = the RTTI locator, [1 .. 12] = the vtable copy the action's vptr points at */
static BYTE klfc_edge[0x80];                  /* a dummy cover edge for act+0x7c (nothing reads it: re\climb.md 1) */
static int klfc_dead, klfc_lastT = -0x7fffffff, klfc_prevE, klfc_armed;
static DWORD klfc_lastPress;
static SHORT (WINAPI *klfc_key)(int);
static HWND (WINAPI *klfc_fg)(void);
static DWORD (WINAPI *klfc_wtp)(HWND, LPDWORD);
#ifdef KLHOOK_TEST
/* TEST build only: klauto.c's scripted keys reach the game through DirectInput, which GetAsyncKeyState never sees (and an
   unattended run's window need not be in front), so a script's 'tap E' / 'down W' could not start a climb. The press,
   W and LSHIFT also count when klauto holds them (its kla_held[] by DIK code; klhud.c's klu_tab_held reads Tab the same
   way). klfc_dik = the DIK code of [Climb] Key (user32 MapVirtualKeyA, VK -> scan code; E = 0x12). SHIP: unchanged. */
static int kla_key_held(int dik);
static int klfc_dik = 0x12;
#define KLFC_SCRIPTED(dik) kla_key_held(dik)
#else
#define KLFC_SCRIPTED(dik) 0
#endif

/* ---------------------------------------------------------------- the fault guard */

static int klfc_filter(EXCEPTION_POINTERS *ep, const char *what)
{
    DWORD code = ep->ExceptionRecord->ExceptionCode; CONTEXT *c = ep->ContextRecord;
    switch (code) {
    case EXCEPTION_ACCESS_VIOLATION: case EXCEPTION_ILLEGAL_INSTRUCTION: case EXCEPTION_PRIV_INSTRUCTION:
    case EXCEPTION_INT_DIVIDE_BY_ZERO: case EXCEPTION_INT_OVERFLOW: case EXCEPTION_FLT_DENORMAL_OPERAND:
    case EXCEPTION_FLT_DIVIDE_BY_ZERO: case EXCEPTION_FLT_INEXACT_RESULT: case EXCEPTION_FLT_INVALID_OPERATION:
    case EXCEPTION_FLT_OVERFLOW: case EXCEPTION_FLT_STACK_CHECK: case EXCEPTION_FLT_UNDERFLOW: case EXCEPTION_BREAKPOINT: break;
    default: return EXCEPTION_CONTINUE_SEARCH;                       /* C++ exceptions of the game and the like: its own business */
    }
    if (klh_exe_ok && c->Eip == (DWORD)(DWORD_PTR)KLH_VA(KL2_PROBE)) return EXCEPTION_CONTINUE_SEARCH;     /* Steam's probe: its own handler */
    klog("fclimb: FAULT %08lx at %08lx (address %08lx) in %s; eax=%08lx ebx=%08lx ecx=%08lx edx=%08lx esi=%08lx edi=%08lx esp=%08lx",
         code, c->Eip, ep->ExceptionRecord->NumberParameters > 1 ? (DWORD)ep->ExceptionRecord->ExceptionInformation[1] : 0,
         what, c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Esp);
    return EXCEPTION_EXECUTE_HANDLER;
}
/* fn(arg), or -1 after a fault (logged, unwound, FPU re-initialised with the control word it had) */
static int klfc_guard(const char *what, int (*fn)(void *), void *arg)
{
    int r; WORD cw = 0;
    __asm fnstcw cw
    __try { r = fn(arg); }
    __except (klfc_filter(GetExceptionInformation(), what)) {
        __asm fninit
        __asm fldcw cw
        r = -1;
    }
    return r;
}
static void klfc_disable(const char *where)
{
    klfc_dead = 1;
    klog("fclimb: DISABLED for this session (fault in %s) - restart the game before testing again", where);
}

/* ---------------------------------------------------------------- reads and small helpers */

#define KLFC_CALL(type, va) ((type)(DWORD_PTR)KLH_VA(va))      /* a routine of kl2.exe by its address */
#define KLFC_PTR(type, p) ((type)(DWORD_PTR)(p))              /* a routine by a pointer read from a vtable */
static DWORD klfc_vf(DWORD obj, DWORD off) { DWORD vt = klh_rd32(obj); return vt ? klh_rd32(vt + off) : 0; }
static int klfc_ok(DWORD p, DWORD n) { BYTE b; return p && klh_rd(p, &b, 1) && klh_rd(p + n - 1, &b, 1); }
static float klfc_f(DWORD p) { float f = 0; klh_rd(p, &f, 4); return f; }
static void klfc_v3set(float *d, float x, float y, float z) { d[0] = x; d[1] = y; d[2] = z; }
static void klfc_v3madd(float *d, const float *a, const float *b, float s) { d[0] = a[0] + b[0] * s; d[1] = a[1] + b[1] * s; d[2] = a[2] + b[2] * s; }
static float klfc_v3dist(const float *a, const float *b) { float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2]; return (float)sqrt(x * x + y * y + z * z); }
static DWORD klfc_sys(void) { return klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)); }
static int klfc_T(void) { DWORD s = klfc_sys(); return s ? (int)klh_rd32(s + 0x48) : 0; }
static int klfc_movid(DWORD P) { DWORD mov = klh_rd32(P + 0x6b4); return mov ? (int)klh_rd32(mov + 0x44) : -1; }
static DWORD klfc_cur_act(DWORD P) { DWORD d = klh_rd32(P + 0x19c); return d ? klh_rd32(d + 4) : 1; }   /* 1 = unreadable */
static void klfc_put(DWORD at, const void *v, int n, const char *what) { if (!klh_data((void *)(DWORD_PTR)at, v, n, what)) klog("fclimb: write of %d byte(s) at %08lx (%s) REFUSED", n, at, what); }
static const char *klfc_rtti(DWORD obj, char *out, int cap)
{   /* the class name of a game object from its RTTI (vtable[-1] -> locator +0xc -> type descriptor +8), '-' if none */
    DWORD vt = obj ? klh_rd32(obj) : 0, col = vt ? klh_rd32(vt - 4) : 0, td = col ? klh_rd32(col + 0xc) : 0;
    if (!td || !klh_rdstr(td + 8, out, cap)) strcpy(out, "-");
    return out;
}
/* engine calls - only ever made inside klfc_guard */
static int klfc_pose(DWORD P, float *M, float *Pf)
{
    DWORD node = klh_rd32(P + 4);
    if (!klfc_ok(node, 0x80)) return 0;
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, float *, float *), KLFC_POSE)(node, 0, M, Pf);
    return 1;
}
static float klfc_anim_cur(void)
{   /* the frame our channel is at, -1 when the channel was taken by another clip / lost */
    if (!klfc_c.anim || klh_rd32(klfc_c.anim) != klfc_c.anim0) return -1.0f;
    return klfc_f(klfc_c.anim + 4);
}

/* ---------------------------------------------------------------- the raycast (his cl_ray) */

static int klfc_cast(const float o[3], const float seg[3], unsigned mask, struct klfc_ray *r, float pt[3])
{   /* -> 1 hit, 0 none, -1 the world cannot be asked */
    DWORD sys = klfc_sys(), db, ph, cw; int havok = 0, hit;
    if (!sys || !(db = klh_rd32(sys + 0xac)) || !(ph = klh_rd32(db + 0x52cc)) || !klh_rd32(ph + 0x14dc)) return -1;
    if (!(cw = klh_rd32((DWORD_PTR)KLH_VA(KLFC_COLLW))) || klh_rd32(cw) != KLFC_COLLW_VT) return -1;
    if (!klh_rd((DWORD_PTR)KLH_VA(KLFC_HAVOK), &havok, 4) || havok != 1) return -1;
    memset(r, 0, sizeof *r); r->frac = 1.0f;
    hit = KLFC_CALL(BYTE (__fastcall *)(DWORD, DWORD, void *, DWORD, const float *, const float *, DWORD, DWORD, DWORD, DWORD, DWORD), KLFC_RAY)
          (cw, 0, r, 0, o, seg, 0, mask, 1, 0, 11) & 1;
    if (r->frac >= 0.0f && r->frac <= 1.0f) klfc_v3madd(pt, o, seg, r->frac);
    else memcpy(pt, r->hit, 12);
    return hit;
}
static const char *klfc_hit_bad(const struct klfc_ray *r, DWORD *obj)
{   /* a rigid body or an actor under a ray calls the climb off (Dead Men's rule) */
    char nm[96];
    *obj = r->node ? klh_rd32(r->node + 0x60) : 0;
    if ((*obj && klh_rd32(*obj) == KLFC_RIGID_VT) || (r->node && klh_rd32(r->node) == KLFC_RIGID_VT)) return "rigid";
    klfc_rtti(*obj, nm, sizeof nm);
    if (strstr(nm, "Actor") || strstr(nm, "Player")) return "actor";
    return 0;
}

/* ---------------------------------------------------------------- the probe: Dead Men's 0x605b50 on Dog Days' world */

static int klfc_probe(DWORD P, struct klfc_probe *r)
{   /* 1 = a ledge (r->cls, S, h, Wp), 0 = none, -1 = called off (r->why) */
    const float rr = 25.0f;
    struct { float h, hit[3]; int i; } cand[4]; int n = 0, i, k, c, hit; float L, cur = 0, pt[3], o[3], seg[3]; struct klfc_ray ray; DWORD obj; const char *bad; char nm[96];
    memset(r, 0, sizeof *r); r->cls = -1; r->why = "no candidate";
    if (!klfc_pose(P, r->M, r->Pf)) { r->why = "no node"; return 0; }
    L = (float)sqrt(r->M[0] * r->M[0] + r->M[2] * r->M[2]);
    if (L < 1e-3f) { r->why = "bad facing"; return 0; }
    klfc_v3set(r->F, -r->M[0] / L, 0, -r->M[2] / L);                  /* world forward = -row 0 (Dead Men's D = +row 0) */
    klfc_v3set(r->B, -r->F[0], 0, -r->F[2]);
    for (i = 0; i < 4; i++) {
        klfc_v3set(o, r->Pf[0] + r->F[0] * (rr + 15 * i), r->Pf[1] + 310, r->Pf[2] + r->F[2] * (rr + 15 * i));
        klfc_v3set(seg, 0, -310, 0);
        hit = klfc_cast(o, seg, 0x20, &ray, pt);
        if (hit < 0) { r->why = "raycast unavailable"; return 0; }
        obj = 0; bad = hit ? klfc_hit_bad(&ray, &obj) : 0;
        if (klfc.log >= 2)
            klog("fclimb: ray down%d o=(%.1f,%.1f,%.1f) hit=%d h=%.1f frac=%.3f obj=%s(%08lx)", i, o[0], o[1], o[2], hit, hit ? pt[1] - r->Pf[1] : 0.0f, ray.frac,
                 hit ? klfc_rtti(obj, nm, sizeof nm) : "-", obj);
        if (!hit) continue;
        if (bad) { r->why = bad; return -1; }
        cand[n].h = pt[1] - r->Pf[1]; memcpy(cand[n].hit, pt, 12); cand[n].i = i; n++;
    }
    for (k = 0; k < n; k++) {
        float h; int c1, c2, c3;
        if (cand[k].h < cur) continue;                              /* non-decreasing */
        h = cur = cand[k].h; i = cand[k].i;
        /* clearance at h + 15 from 15 behind (hero-only walls block: mask 0x28) */
        klfc_v3set(o, r->Pf[0] + r->B[0] * 15, r->Pf[1] + h + 15, r->Pf[2] + r->B[2] * 15);
        klfc_v3set(seg, r->F[0] * (rr + 15 * (i + 2)), 0, r->F[2] * (rr + 15 * (i + 2)));
        if ((c1 = klfc_cast(o, seg, 0x28, &ray, pt)) < 0) { r->why = "raycast unavailable"; return 0; }
        if (c1) { if (klfc.log >= 2) klog("fclimb: cand %d h=%.1f: the way over the top is blocked at (%.1f,%.1f,%.1f)", k, h, pt[0], pt[1], pt[2]); continue; }
        /* head room: 180 straight up from the ledge point */
        klfc_v3set(o, cand[k].hit[0], cand[k].hit[1] + 1, cand[k].hit[2]); klfc_v3set(seg, 0, 180, 0);
        if ((c2 = klfc_cast(o, seg, 0x20, &ray, pt)) < 0) { r->why = "raycast unavailable"; return 0; }
        if (c2) { r->h = h; r->why = "headroom"; return -1; }
        /* the wall face at h - 1 */
        klfc_v3set(o, r->Pf[0] + r->B[0] * 10, r->Pf[1] + h - 1, r->Pf[2] + r->B[2] * 10);
        klfc_v3set(seg, r->F[0] * (rr + 15 * i + 20), 0, r->F[2] * (rr + 15 * i + 20));
        if ((c3 = klfc_cast(o, seg, 0x20, &ray, pt)) < 0) { r->why = "raycast unavailable"; return 0; }
        if (!c3) { if (klfc.log >= 2) klog("fclimb: cand %d h=%.1f: no wall face", k, h); continue; }
        memcpy(r->Wp, pt, 12);
        {   float a[3], b[3], nx, ny, nz, nl;
            klfc_v3set(a, ray.v2[0] - ray.v0[0], ray.v2[1] - ray.v0[1], ray.v2[2] - ray.v0[2]);
            klfc_v3set(b, ray.v1[0] - ray.v0[0], ray.v1[1] - ray.v0[1], ray.v1[2] - ray.v0[2]);
            nx = a[1] * b[2] - a[2] * b[1]; ny = a[2] * b[0] - a[0] * b[2]; nz = a[0] * b[1] - a[1] * b[0];
            nl = (float)sqrt(nx * nx + ny * ny + nz * nz); if (nl > 1e-6f) klfc_v3set(r->Wn, nx / nl, ny / nl, nz / nl); }
        if (klfc.log >= 2) klog("fclimb: cand %d h=%.1f: wall at (%.1f,%.1f,%.1f) n=(%.2f,%.2f,%.2f)", k, h, r->Wp[0], r->Wp[1], r->Wp[2], r->Wn[0], r->Wn[1], r->Wn[2]);
        if (h <= 25) continue;
        r->h = h;
        for (c = 0; c < 3; c++) if (h <= klfc_cls[c].max) { r->cls = c; break; }
        if (r->cls < 0) { r->why = "too high"; return -1; }
        klfc_v3set(r->S, r->Wp[0] + r->B[0] * klfc_cls[r->cls].off, r->Pf[1], r->Wp[2] + r->B[2] * klfc_cls[r->cls].off);
        r->why = "OK";
        return 1;
    }
    return 0;
}

/* ---------------------------------------------------------------- the clip and the end place */

static void klfc_root(DWORD clip, DWORD db, float f, int mirror, float p[3])
{
    float q[4] = { 0, 0, 0, 1 };
    p[0] = p[1] = p[2] = 0;
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, DWORD, float, float *, float *, int), KLFC_ROOT)(clip, 0, db, f, q, p, mirror);
}
/* Final = S + horizontal(world(root(last) - root(e5))) + (0, h, 0) */
static int klfc_final(struct klfc_probe *r, int mirror)
{
    DWORD sys = klfc_sys(), w = sys ? klh_rd32(sys + 0xac) : 0, db = w ? klh_rd32(w + 0x14) : 0;
    int last = r->frames > 0 ? r->frames - 1 : 0, e5 = r->e5 >= 0 ? r->e5 : 0, e6 = r->e6 >= 0 ? r->e6 : last;
    float v[3], rise, wx, wz; const float *M = r->M;
    if (!db) return 0;
    klfc_root(r->clip, db, 0, mirror, r->g0);
    klfc_root(r->clip, db, (float)e5, mirror, r->ge5);
    klfc_root(r->clip, db, (float)e6, mirror, r->ge6);
    klfc_root(r->clip, db, (float)last, mirror, r->gend);
    klfc_v3set(v, r->gend[0] - r->ge5[0], r->gend[1] - r->ge5[1], r->gend[2] - r->ge5[2]);
    rise = r->gend[1] - r->g0[1];
    if (fabs(rise) > 0.01f && fabs(rise) < 5.0f) {                  /* a root in metres? Dead Men's data is cm */
        klog("fclimb: root rise %.3f looks like metres -> x100", rise);
        v[0] *= 100; v[1] *= 100; v[2] *= 100;
    }
    wx = v[0] * M[6] + v[1] * M[3] + v[2] * M[0];                   /* local -> world (0x6be1c0): x*row2 + y*row1 + z*row0 */
    wz = v[0] * M[8] + v[1] * M[5] + v[2] * M[2];
    klfc_v3set(r->gv, wx, v[1], wz);
    klfc_v3set(r->Final, r->S[0] + wx, r->S[1] + r->h, r->S[2] + wz);
    return 1;
}
static int klfc_event(DWORD clip, int id) { return KLFC_CALL(int (__stdcall *)(DWORD, int, int *), KLFC_EVENT)(clip, id, 0); }
static int klfc_clip(DWORD P, struct klfc_probe *r, int sprint)
{
    static const char *nm[3] = { "/Movement/Climb/Up/Low", "/Movement/Climb/Up/Medium", "/Movement/Climb/Up/High" };
    int id; DWORD clip, eb;
    r->clipName = (r->cls == 0 && sprint) ? "/Movement/Climb/Up/Sprint_Low" : nm[r->cls];
    id = klq_slot(P, r->clipName);                                  /* klclimb.c: the game's own slot search (0x68a730), by reads */
    if (id < 0 && r->cls == 0 && sprint) { r->clipName = nm[0]; id = klq_slot(P, r->clipName); }
    r->id = id;
    if (id < 0) { klog("fclimb: clip '%s' missing in this level's .ANM (no stock Dog Days level has the climb clips) - nothing started", r->clipName); return 0; }
    clip = KLFC_CALL(DWORD (__fastcall *)(DWORD, DWORD, DWORD), KLFC_CLIPVAR)(P, 0, (DWORD)id);
    if (!klfc_ok(clip, 0x68)) { klog("fclimb: clip '%s' id %d -> no variant (%08lx)", r->clipName, id, clip); return 0; }
    r->clip = clip;
    r->frames = (int)(klh_rd32(clip + 2) & 0xffff);
    eb = klh_rd32((DWORD_PTR)KLH_VA(KLFC_EVTAB));
    if (!eb || !klh_rd32(eb + 0x10)) { klog("fclimb: the clips' event table is missing"); return 0; }
    r->e5 = klfc_event(clip, 5);
    if (r->e5 < 0) r->e5 = klfc_event(clip, (int)KLQ_EV_FOOT);     /* our builds' players' clips carry Dead Men's 5 as 105 (klclimb.c section 0) */
    r->e6 = klfc_event(clip, 6);
    if (r->e5 < 0 || r->e6 < 0) klog("fclimb: clip events missing (e5=%d e6=%d): using 0 / the last frame", r->e5, r->e6);
    return klfc_final(r, 0);
}
/* Dead Men's clips end only ~10 (Low) / ~15 (Medium) past the face: push Final to MinIn past it, only when the ground
   there is the same top (+-10), the way is clear at knee and chest height and there are 180 of head room. */
static void klfc_min_in(struct klfc_probe *r)
{
    float past, add, C[3], o[3], seg[3], pt[3]; struct klfc_ray ray; const char *why = 0; int g, k;
    klfc_v3set(r->push, 0, 0, 0);
    if (klfc.minin <= 0) return;
    past = (r->Final[0] - r->Wp[0]) * r->F[0] + (r->Final[2] - r->Wp[2]) * r->F[2];
    if (past >= (float)klfc.minin) return;
    add = (float)klfc.minin - past;
    klfc_v3set(C, r->Final[0] + r->F[0] * add, r->Final[1], r->Final[2] + r->F[2] * add);
    klfc_v3set(o, C[0], C[1] + 60, C[2]); klfc_v3set(seg, 0, -120, 0);
    g = klfc_cast(o, seg, 0x20, &ray, pt);
    if (g != 1 || fabs(pt[1] - r->Final[1]) > 10.0f) why = "no ledge top there";
    for (k = 0; !why && k < 2; k++) {
        klfc_v3set(o, r->Final[0], r->Final[1] + (k ? 120 : 40), r->Final[2]); klfc_v3set(seg, r->F[0] * add, 0, r->F[2] * add);
        if (klfc_cast(o, seg, 0x28, &ray, pt) != 0) why = k ? "blocked at chest" : "blocked at knee";
    }
    if (!why) { klfc_v3set(o, C[0], C[1] + 1, C[2]); klfc_v3set(seg, 0, 180, 0); if (klfc_cast(o, seg, 0x20, &ray, pt) != 0) why = "head room"; }
    if (why) { if (klfc.log) klog("fclimb: MinIn: end place kept %.1f past the face (%s)", past, why); return; }
    klfc_v3set(r->push, r->F[0] * add, 0, r->F[2] * add);
    r->Final[0] = C[0]; r->Final[2] = C[2];
    if (klfc.log) klog("fclimb: MinIn: end place pushed %.1f (%.1f -> %d past the face)", add, past, klfc.minin);
}

/* ---------------------------------------------------------------- the action's slots (the engine calls them, main thread) */

static int klfc_start_body(void *arg)
{
    DWORD self = (DWORD)(DWORD_PTR)arg, pl = klh_rd32(self + 8), anim, zero = 0; int mirror, ok; float cur;
    if (!klfc_c.active || klfc_c.act != self || pl != klfc_c.P) { klog("fclimb: START on an unknown record"); return 0; }
    if (klh_rd32(pl + 0x2810)) KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_LEAVECOVER)(pl, 0);       /* stock prep */
    klfc_put(pl + 0x2d60, &zero, 4, "fclimb vault offer");
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD), klfc_vf(pl, 0x560))(pl, 0); klfc_c.did560 = 1;    /* the collision off; End's vt +0x564 undoes it */
    anim = KLFC_PTR(DWORD (__fastcall *)(DWORD, DWORD, DWORD, int), klfc_vf(pl, 0x204))(pl, 0, klfc_c.clip, 1);
    if (!klfc_ok(anim, 0x20)) { klog("fclimb: START Play failed (%08lx)", anim); klfc_c.endReason = "playanim"; return 0; }
    klfc_put(self + 0xc, &anim, 4, "fclimb action channel");
    klfc_c.anim = anim; klfc_c.anim0 = klh_rd32(anim); klfc_c.animId = (int)klh_rd32(anim + 0x18);
    mirror = (klh_rd32(anim + 0x14) >> 8) & 1;
    cur = klfc_f(anim + 4); klfc_c.from = klfc_f(anim + 8); klfc_c.to = klfc_f(anim + 0xc);
    if (mirror) {                                                   /* the end place again with the mirrored root (keeping the MinIn push) */
        struct klfc_probe r;
        memset(&r, 0, sizeof r);
        memcpy(r.M, klfc_c.M, sizeof r.M); memcpy(r.S, klfc_c.S, 12); r.h = klfc_c.h;
        r.clip = klfc_c.clip; r.frames = klfc_c.frames; r.e5 = klfc_c.e5; r.e6 = klfc_c.e6;
        if (klfc_final(&r, 1)) { klfc_v3madd(klfc_c.Final, r.Final, klfc_c.push, 1.0f); memcpy(klfc_c.gv, r.gv, 12); }
    }
    ok = KLFC_PTR(BYTE (__fastcall *)(DWORD, DWORD, const float *, const float *, float), klfc_vf(pl, 0x208))
         (pl, 0, klfc_c.M, klfc_c.Final, klfc_c.to - klfc_c.from - 1.0f) & 0xff;
    if (!ok) { klog("fclimb: START AlignTo failed (no root channel?)"); klfc_c.endReason = "warp"; return 0; }
    if (klfc.cam) {
        DWORD cam = KLFC_CALL(DWORD (__fastcall *)(DWORD, DWORD), KLFC_CAM_GET)(pl, 0);
        if (klfc_ok(cam, 0xca0)) KLFC_CALL(void (__fastcall *)(DWORD, DWORD, float, float, float), KLFC_CAM_SET)(cam, 0, 67.0f, 40.0f, 0.5f);
    }
    if (klfc.log)
        klog("fclimb: START act=%08lx anim=%08lx id=%d mirror=%d cur=%.1f from=%.1f to=%.1f e5=%d e6=%d Final=(%.1f,%.1f,%.1f)",
             self, anim, klfc_c.animId, mirror, cur, klfc_c.from, klfc_c.to, klfc_c.e5, klfc_c.e6, klfc_c.Final[0], klfc_c.Final[1], klfc_c.Final[2]);
    return 1;
}
static BYTE __fastcall klfc_v_start(DWORD self, DWORD edx)
{
    int r; (void)edx;
    r = klfc_guard("Start", klfc_start_body, (void *)(DWORD_PTR)self);
    if (r < 0) { klfc_disable("Start"); klfc_c.endReason = "fault"; return 0; }
    return (BYTE)(r == 1);
}

static int klfc_update_body(void *arg)
{
    DWORD self = (DWORD)(DWORD_PTR)arg; int r, T; float cur;
    r = KLFC_CALL(BYTE (__fastcall *)(DWORD, DWORD), KLFC_V_UPDATE)(self, 0) & 0xff;        /* stock: camera follow */
    if (!klfc_c.active || klfc_c.act != self) return r;
    cur = klfc_anim_cur();
    if (cur >= (float)klfc_c.e5 && !klfc_c.reached) { klfc_c.reached = 1; klfc_put(self + 0x68, klfc_c.Final, 12, "fclimb end place"); }
    T = klfc_T();
    if (cur < 0) { klfc_c.endReason = "channel lost"; return 0; }
    if (T - klfc_c.startT > klfc_c.frames * 1024 / 25 + 1024) { klfc_c.endReason = "timeout"; return 0; }
    if (cur >= klfc_c.to - 0.5f) { klfc_c.endReason = "clip end"; return 0; }
    return r;
}
static BYTE __fastcall klfc_v_update(DWORD self, DWORD edx)
{
    int r; (void)edx;
    r = klfc_guard("Update", klfc_update_body, (void *)(DWORD_PTR)self);
    if (r < 0) { klfc_disable("Update"); klfc_c.endReason = "fault"; return 0; }
    return (BYTE)(r != 0);
}

struct klfc_ae { DWORD self; int id; };
static int klfc_animend_body(void *arg)
{
    struct klfc_ae *a = (struct klfc_ae *)arg;
    if (!klfc_c.active || klfc_c.act != a->self) return 1;
    if (klfc_anim_cur() >= 0 && a->id == klfc_c.animId) { klfc_c.endReason = "animend"; return 1; }
    if (klfc_c.animEndLogs++ < 5 && klfc.log) klog("fclimb: another channel ended (id %d, ours %d) - ignored", a->id, klfc_c.animId);
    return 0;
}
static BYTE __fastcall klfc_v_animend(DWORD self, DWORD edx, int id)
{   /* thiscall (self; id), ret 4: as __fastcall the id is the one stack argument and the callee pops it */
    struct klfc_ae a; int r; (void)edx;
    a.self = self; a.id = id;
    r = klfc_guard("AnimEnd", klfc_animend_body, &a);
    if (r < 0) { klfc_disable("AnimEnd"); klfc_c.endReason = "fault"; return 1; }
    return (BYTE)(r != 0);
}

static int klfc_end_body(void *arg)
{
    DWORD self = (DWORD)(DWORD_PTR)arg, pl = klh_rd32(self + 8); int mine = klfc_c.active && klfc_c.act == self, reached, completed, snapped = 0;
    float cur = mine ? klfc_anim_cur() : -1.0f, M[9], f[3] = { 0, 0, 0 }, dist = -1;
    reached = mine && (klfc_c.reached || (cur >= 0 && cur >= (float)klfc_c.e5));
    if (!reached && klfc_pose(pl, M, f)) {                          /* the stock End teleports to +0x38 / +0x68: make that where he is */
        klfc_put(self + 0x38, M, sizeof M, "fclimb end rotation"); klfc_put(self + 0x68, f, 12, "fclimb end place");
    }
    if (!mine || klfc_c.did560) KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_V_END)(self, 0);   /* undoes vt +0x560, stance, teleport */
    else KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_SYNC)(pl, 0);
    /* the safety snap only when OUR clip completed; engine aborts (death, another action) arrive with no endReason */
    completed = klfc_c.endReason && (!strcmp(klfc_c.endReason, "animend") || !strcmp(klfc_c.endReason, "clip end"));
    if (mine && reached && klfc_pose(pl, M, f)) {
        dist = klfc_v3dist(f, klfc_c.Final);
        if (klfc.snap && completed && dist > 25.0f) {
            KLFC_CALL(void (__fastcall *)(DWORD, DWORD, const float *, const float *, int, int, int), KLFC_TELE)(pl, 0, klfc_c.M, klfc_c.Final, 0, 0, 0);
            snapped = 1;
        }
    }
    if (klfc.log)
        klog("fclimb: END reason=%s cur=%.1f reached=%d feet=(%.1f,%.1f,%.1f) Final=(%.1f,%.1f,%.1f) dist=%.1f snapped=%d%s",
             klfc_c.endReason ? klfc_c.endReason : "engine", cur, reached, f[0], f[1], f[2], klfc_c.Final[0], klfc_c.Final[1], klfc_c.Final[2],
             dist, snapped, mine ? "" : " (unknown record)");
    if (mine) memset(&klfc_c, 0, sizeof klfc_c);
    return 0;
}
static void __fastcall klfc_v_end(DWORD self, DWORD edx)
{
    (void)edx;
    if (klfc_guard("End", klfc_end_body, (void *)(DWORD_PTR)self) < 0) { klfc_disable("End"); memset(&klfc_c, 0, sizeof klfc_c); }
}

/* ---------------------------------------------------------------- starting a climb (from the tick, inside the guard) */

static void klfc_go(DWORD P, const struct klfc_probe *r, int T)
{
    DWORD act, vt, zero = 0, ptr; BYTE z2[2] = { 0, 0 };
    if (!klfc_vt[1]) {
        int i;
        klfc_vt[0] = klh_rd32((DWORD_PTR)KLH_VA(KLFC_VAULT_VT - 4));
        for (i = 0; i < 12; i++) klfc_vt[1 + i] = klh_rd32((DWORD_PTR)KLH_VA(KLFC_VAULT_VT + 4 * i));
        klfc_vt[1 + 2] = (DWORD)(DWORD_PTR)klfc_v_start;
        klfc_vt[1 + 4] = (DWORD)(DWORD_PTR)klfc_v_update;
        klfc_vt[1 + 5] = (DWORD)(DWORD_PTR)klfc_v_end;
        klfc_vt[1 + 10] = (DWORD)(DWORD_PTR)klfc_v_animend;
    }
    act = KLFC_PTR(DWORD (__fastcall *)(DWORD, DWORD, int), klfc_vf(P, 0x384))(P, 0, 0x2B);
    if (!klfc_ok(act, 0x80)) { klog("fclimb: CreateAction(0x2B) failed (%08lx)", act); return; }
    if (klh_rd32(act) != KLFC_VAULT_VT || klh_rd32(act + 8) != P) {
        klog("fclimb: CreateAction(0x2B) gave an unexpected object %08lx vt=%08lx owner=%08lx - not used", act, klh_rd32(act), klh_rd32(act + 8));
        return;
    }
    vt = (DWORD)(DWORD_PTR)&klfc_vt[1];
    if (!klh_data((void *)(DWORD_PTR)act, &vt, 4, "fclimb vptr")) { klog("fclimb: the action's vptr could not be written (%08lx) - not started", act); return; }
    klfc_put(act + 0x14, r->M, 36, "fclimb act"); klfc_put(act + 0x5c, r->Pf, 12, "fclimb act");
    klfc_put(act + 0x38, r->M, 36, "fclimb act"); klfc_put(act + 0x68, r->Pf, 12, "fclimb act");      /* where he is, until event 5 */
    klfc_put(act + 0x10, &r->clip, 4, "fclimb act"); klfc_put(act + 0xc, &zero, 4, "fclimb act");
    klfc_put(act + 0x74, z2, 2, "fclimb act"); klfc_put(act + 0x78, &zero, 4, "fclimb act");
    ptr = (DWORD)(DWORD_PTR)klfc_edge; klfc_put(act + 0x7c, &ptr, 4, "fclimb act");
    memset(&klfc_c, 0, sizeof klfc_c);
    klfc_c.active = 1; klfc_c.act = act; klfc_c.P = P; klfc_c.clip = r->clip; klfc_c.e5 = r->e5 >= 0 ? r->e5 : 0;
    klfc_c.e6 = r->e6 >= 0 ? r->e6 : (r->frames > 0 ? r->frames - 1 : 0); klfc_c.frames = r->frames; klfc_c.h = r->h; klfc_c.startT = T;
    memcpy(klfc_c.S, r->S, 12); memcpy(klfc_c.Final, r->Final, 12); memcpy(klfc_c.M, r->M, 36); memcpy(klfc_c.gv, r->gv, 12); memcpy(klfc_c.push, r->push, 12);
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD), klfc_vf(P, 0x374))(P, 0);                   /* Abort: a no-op when idle (0x869e10 int3s if an action is current) */
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD, DWORD), klfc_vf(P, 0x370))(P, 0, act);       /* StartAction: klfc_v_start runs in here */
    if (klfc_cur_act(P) != act) {
        klog("fclimb: start failed (%s) - the action finished at once", klfc_c.endReason ? klfc_c.endReason : "?");
        if (klfc_c.act == act) memset(&klfc_c, 0, sizeof klfc_c);
    }
}

/* ---------------------------------------------------------------- the tick */

static char klfc_actname[96];
static const char *klfc_precond(DWORD P, int T)
{   /* Dead Men's 'may he climb now', as luvsic reads it on Dog Days' player; 0 = yes */
    DWORD sys, db, ph, cw, fl = 0; BYTE b = 0; int id, havok = 0;
    if (klfc_dead) return "disabled after fault";
    if (klfc_c.active) return "climbing";
    if (klh_rd32(P + 0x6b0) != P + 0xdb0) return "movement table (MiniScene?)";
    id = klfc_movid(P);
    if (id != 2 && id != 3) { _snprintf(klfc_actname, sizeof klfc_actname - 1, "movement %d", id); return "movement not Stand/BaseMove"; }
    if (klfc_cur_act(P)) { klfc_rtti(klfc_cur_act(P), klfc_actname, sizeof klfc_actname); return "action running"; }                   /* the dispatcher's current action (his vt +0x388) */
    if (T - (int)klh_rd32(P + 0x2c48) < 512) return "< 0.5 s since the last action";
    if (klh_rd(P + 0xd29, &b, 1) && b) return "use action running";
    if (klh_rd(P + 0xed0, &fl, 4) && (fl & 0x80)) return "input blocked";
    if (klh_rd32(P + 0xd50) || klh_rd32(P + 0xd44)) return "seat/carrier";
    if (!klh_rd(P + 0x2720, &b, 1) || !(b & 2)) return "not local human";
    if (klh_rd32(P + 0x2d60) & 0x10) return "stock vault available";
    if (!klh_rd32(P + 0x2810)) return "P+0x2810 null";
    if (!(cw = klh_rd32((DWORD_PTR)KLH_VA(KLFC_COLLW))) || klh_rd32(cw) != KLFC_COLLW_VT) return "no collision world";
    sys = klfc_sys(); db = sys ? klh_rd32(sys + 0xac) : 0; ph = db ? klh_rd32(db + 0x52cc) : 0;
    if (!ph || !klh_rd32(ph + 0x14dc) || !klh_rd((DWORD_PTR)KLH_VA(KLFC_HAVOK), &havok, 4) || havok != 1) return "no Havok world";
    return 0;
}
static int klfc_tick_body(void *unused)
{
    DWORD gd, sys, P, now, pid = 0; signed char pi = -1; int T, E, Wk, sprint, edge, fg, blocked, res, clipOk; HWND fw;
    float V[3] = { 0, 0, 0 }, S = 0, vxz, fwd = 0; BYTE spr = 0; const char *why; struct klfc_probe r;
    (void)unused;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(sys = klfc_sys())) return 0;
    if (!klh_rd(gd + 0x898, &pi, 1) || pi < 0 || pi > 7) return 0;
    if (!(P = klh_rd32(gd + 0x828 + 4 * pi)) || klh_rd32(P) != KLFC_PLAYER_VT || !klfc_ok(P, 0x2e00)) return 0;
    T = (int)klh_rd32(sys + 0x48);
    if (T == klfc_lastT) return 0;                                  /* paused */
    klfc_lastT = T;
    if (P != klfc_lvlP) {
        int lo = klq_slot(P, "/Movement/Climb/Up/Low"), me = klq_slot(P, "/Movement/Climb/Up/Medium"), hi = klq_slot(P, "/Movement/Climb/Up/High");
        klfc_lvlP = P;
        if (lo >= 0 && me >= 0 && hi >= 0) klog("fclimb: level: the climb clips are here (slots Low %d Medium %d High %d): hold W and press the key at a ledge 25 .. 220 high", lo, me, hi);
        else klog("fclimb: level: NO climb clips in this level's .ANM (Low %d Medium %d High %d): presses here do nothing - install the build\\rope map", lo, me, hi);
    }
    if (klfc_c.active) {
        if (klfc_c.P != P || klfc_cur_act(P) != klfc_c.act) { klog("fclimb: record dropped (the action is gone)"); memset(&klfc_c, 0, sizeof klfc_c); }
        return 0;
    }
    fw = klfc_fg ? klfc_fg() : 0;
    if (fw && klfc_wtp) klfc_wtp(fw, &pid);
    fg = fw && pid == GetCurrentProcessId();
    E = (fg && (klfc_key(klfc.key) & 0x8000)) || KLFC_SCRIPTED(klfc_dik);
    klh_rd(P + 0xb94, &fwd, 4);
    Wk = (fg && (klfc_key('W') & 0x8000)) || fwd > 0.5f || KLFC_SCRIPTED(0x11);
    klh_rd(P + 0x850, &spr, 1);
    sprint = spr || (fg && (klfc_key(VK_LSHIFT) & 0x8000)) || KLFC_SCRIPTED(0x2a);
    klh_rd(P + 0x5ec, V, 12); klh_rd(P + 0x5f8, &S, 4);
    vxz = (float)sqrt(V[0] * V[0] + V[2] * V[2]);
    blocked = vxz >= 300.0f && S < 0.75f * vxz;
    edge = E && !klfc_prevE; klfc_prevE = E;
    now = GetTickCount();
    if (klfc_armed) {                                               /* Dead Men: the use seen on call N, the probe on call N + 1 */
        klfc_armed = 0;
        why = klfc_precond(P, T);
        if (!why && !Wk) why = "W not held";
        if (!why && klfc.needblock && !blocked) why = "not blocked";
        if (why) { int nm = !strcmp(why, "action running") || !strcmp(why, "movement not Stand/BaseMove"); if (klfc.log) klog("fclimb: press ignored (%s%s%s)", why, nm ? ": " : "", nm ? klfc_actname : ""); return 0; }
        res = klfc_probe(P, &r);
        if (res <= 0) { if (klfc.log) klog("fclimb: RESULT %s%s h=%.1f at (%.1f,%.1f,%.1f)", res < 0 ? "called off: " : "none: ", r.why, r.h, r.Pf[0], r.Pf[1], r.Pf[2]); return 0; }
        clipOk = klfc_clip(P, &r, sprint);
        if (clipOk) klfc_min_in(&r);
        if (klfc.log)
            klog("fclimb: RESULT OK class=%s h=%.1f feet=(%.1f,%.1f,%.1f) S=(%.1f,%.1f,%.1f) Final=(%.1f,%.1f,%.1f) clip='%s' id=%d frames=%d e5=%d e6=%d sprint=%d%s",
                 klfc_cls[r.cls].name, r.h, r.Pf[0], r.Pf[1], r.Pf[2], r.S[0], r.S[1], r.S[2], r.Final[0], r.Final[1], r.Final[2],
                 r.clipName ? r.clipName : "-", r.id, r.frames, r.e5, r.e6, sprint, !clipOk ? " - NO CLIP, nothing started" : klfc.dry ? " - DRY: nothing started" : "");
        if (clipOk && !klfc.dry) klfc_go(P, &r, T);
        return 0;
    }
    if (edge) {
        if (now - klfc_lastPress < 300) return 0;
        klfc_lastPress = now;
        why = klfc_precond(P, T);
        if (why) {
            if (klfc.log && (strcmp(why, "stock vault available") && strcmp(why, "action running") && strcmp(why, "use action running"))) klog("fclimb: press ignored (%s)", why);
            else if (klfc.log >= 2) klog("fclimb: press left to Dog Days (%s%s%s)", why, strcmp(why, "action running") ? "" : ": ", strcmp(why, "action running") ? "" : klfc_actname);
            return 0;
        }
        if (klfc.early && Wk) {                                     /* Early=1: the probe now, before Dog Days acts on the same key */
            res = klfc_probe(P, &r);
            if (res > 0 && klfc_clip(P, &r, sprint)) {
                klfc_min_in(&r);
                if (klfc.log)
                    klog("fclimb: RESULT OK (early) class=%s h=%.1f feet=(%.1f,%.1f,%.1f) Final=(%.1f,%.1f,%.1f) clip='%s' id=%d frames=%d%s",
                         klfc_cls[r.cls].name, r.h, r.Pf[0], r.Pf[1], r.Pf[2], r.Final[0], r.Final[1], r.Final[2], r.clipName ? r.clipName : "-", r.id, r.frames,
                         klfc.dry ? " - DRY: nothing started" : "");
                if (!klfc.dry) klfc_go(P, &r, T);
                return 0;
            }
            if (klfc.log) klog("fclimb: RESULT (early) %s%s h=%.1f at (%.1f,%.1f,%.1f) - the press is left to Dog Days", res < 0 ? "called off: " : res ? "no clip" : "none: ", res ? (res < 0 ? r.why : "") : r.why, r.h, r.Pf[0], r.Pf[1], r.Pf[2]);
            return 0;
        }
        klfc_armed = 1;
    }
    return 0;
}
static int klfc_cleanup_body(void *unused)
{   /* after a fault of the tick: abort our action (its End, ours, gives the collision back) */
    DWORD P = klfc_c.P; (void)unused;
    if (P && klh_rd32(P) == KLFC_PLAYER_VT && klfc_cur_act(P) == klfc_c.act) {
        KLFC_PTR(void (__fastcall *)(DWORD, DWORD), klfc_vf(P, 0x374))(P, 0);
        klog("fclimb: cleanup: action aborted");
    }
    memset(&klfc_c, 0, sizeof klfc_c);
    return 0;
}

static void klfc_tick(int game_thread)
{
    if (!klfc.on || klfc_dead || !game_thread || !klh_exe_ok) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;        /* only the gameplay call of the main loop (his filter) */
    if (!klfc_c.active && kl_online()) {                              /* [Net] OnlineSafe: this part has no mode test of its own; it moves a body peers see only as position updates. GUESS: a climb already running is let finish */
        static int toldnet;
        if (!toldnet++) klog("fclimb: a network session: no climb starts ([Net] OnlineSafe=1)");
        return;
    }
    if (klfc_guard("tick", klfc_tick_body, 0) < 0) {
        klfc_disable("tick");
        if (klfc_c.active && klfc_c.P && klfc_guard("cleanup", klfc_cleanup_body, 0) < 0) memset(&klfc_c, 0, sizeof klfc_c);
    }
}

static void klfc_init(void)
{
    HMODULE u;
    memset(&klfc, 0, sizeof klfc); memset(&klfc_c, 0, sizeof klfc_c);
    klfc.on = GetPrivateProfileIntA("Climb", "Enable", 0, klh_ini) != 0;
    if (!klfc.on) return;
    klfc.dry = GetPrivateProfileIntA("Climb", "Dry", 0, klh_ini) != 0;
    klfc.log = (int)GetPrivateProfileIntA("Climb", "Log", 1, klh_ini);
    klfc.key = (int)GetPrivateProfileIntA("Climb", "Key", 0x45, klh_ini) & 0xff;
    if (!klfc.key) klfc.key = 0x45;
    klfc.needblock = GetPrivateProfileIntA("Climb", "NeedBlock", 0, klh_ini) != 0;
    klfc.minin = (int)GetPrivateProfileIntA("Climb", "MinIn", 30, klh_ini); if (klfc.minin < 0) klfc.minin = 0; if (klfc.minin > 100) klfc.minin = 100;
    klfc.cam = GetPrivateProfileIntA("Climb", "Camera", 1, klh_ini) != 0;
    klfc.snap = GetPrivateProfileIntA("Climb", "Snap", 1, klh_ini) != 0;
    klfc.early = GetPrivateProfileIntA("Climb", "Early", 0, klh_ini) != 0;
    klfc_lvlP = 0;
    u = GetModuleHandleA("user32.dll");                             /* the hook does not link user32 (klnudge.c) */
    if (!u) u = LoadLibraryA("user32.dll");
    if (u) {
        klfc_key = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState");
        klfc_fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
        klfc_wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
    }
#ifdef KLHOOK_TEST
    if (u) {
        UINT (WINAPI *mvk)(UINT, UINT) = (UINT (WINAPI *)(UINT, UINT))GetProcAddress(u, "MapVirtualKeyA");
        UINT sc = mvk ? mvk((UINT)klfc.key, 0) : 0;                 /* MAPVK_VK_TO_VSC */
        if (sc > 0 && sc < 0x80) klfc_dik = (int)sc;
        klog("fclimb: TEST build: klauto's scripted keys count too (press DIK 0x%02x, W 0x11, LSHIFT 0x2a; no foreground needed for them)", klfc_dik);
    }
#endif
    if (!klfc_key || !klfc_fg || !klfc_wtp) { klfc.on = 0; klog("fclimb: user32's GetAsyncKeyState / GetForegroundWindow / GetWindowThreadProcessId not found: OFF"); return; }
    klog("fclimb: on; Dry=%d Log=%d Key=0x%02x NeedBlock=%d MinIn=%d Camera=%d Snap=%d Early=%d; Dead Men's free climb (luvsic's ANP climb.inc): hold W and press the key at a ledge 25 .. 220 high; "
         "plays only where the level's .ANM has /Movement/Climb/Up/* (no stock Dog Days level has them)%s",
         klfc.dry, klfc.log, klfc.key, klfc.needblock, klfc.minin, klfc.cam, klfc.snap, klfc.early, klfc.dry ? " - DRY RUN: probes and logs, starts nothing" : "");
}

#endif /* KLFREECLIMB_C */
