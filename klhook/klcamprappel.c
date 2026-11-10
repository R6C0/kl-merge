/*
 * klcamprappel.c - the Dead Men CAMPAIGN rappel (ZFFPlayerMovementRappel), ported from luvsic's a-newer-perspective
 * loader/rappel.inc @32aa649 (in contribution with luvsic). Part of KLHook (included by klhook.c AFTER klfreeclimb.c
 * and klrappel.c), ticked from klh_tick.
 *
 * WHAT IT DOES (READ rappel.inc 1-120, 393-515): on a campaign level (klcmp_level_active(): [Campaign] Enable=1 AND scene
 * m<NN>[ab]) the player's rappel movement (player +0xdf0 -> object of vt 0xbb5ebc) gets a COPY of its 43-slot vtable in
 * which TryActivate (slot 14), Activate (15) and Update (17) are wrapped by a fault guard. The stock rappel needs the
 * five clips /Movement/Rappelling/* in the level's .ANM (ids u16 at movement +0x1fe4..+0x1fec, 0xFFFF = missing); a stock
 * start with a NULL clip crashes at 0x5a503a. So a press is REFUSED (once-per-level log line) when a clip is missing.
 *
 * 1110: the LANDING CAMERA (land=, rappel.inc 69-73, 360-385) and CamFix=nocoll (rappel.inc 284-345) are ported, see below.
 * NOT PORTED (see the slice report): the loader's LIVE descent (ray-planned scripted slide), the camera diag,
 * the ANP_rappel_cmd.txt test command. Modes live / auto are accepted but behave like native (a log
 * line says so once). klrappel.c (the FA mini-cutscene) is untouched; this module idles whenever it owns the level
 * (klrp.on && klrp_lv.ok) so the two never both act.
 *
 * SHIP policy: the only writes are the vptr word of the heap movement object (klh_data); the vtable copy lives in this
 * DLL's .data. No code byte is touched. No exception handler is added (klfc_guard is a local __try).
 *
 * ini: [CampRappel] Cam=his|ours (default his in code, the fragment sets ours, recommended on; CamHandFrom=3, CamTailMs=1500), Land=off|turn|cam|turncam|auto (default off in code, the fragment sets auto, recommended on), CamFix=0|1 (recommended off).
 * [CampRappel] Mode=0 (0 off, 1 dry, 2 native, 3 live, 4 auto) - see ini_campaign_gameplayB.txt.
 */
#include "klcamprappel_logic.h"

#define KCAMR_MOV_VT   0x00bb5ebc          /* ZFFPlayerMovementRappel, 43 slots (READ rappel.inc RP_MOV_VT / RP_MOV_SLOTS) */
#define KCAMR_SLOTS    43
#define KCAMR_MOV_OFF  0xdf0               /* player -> movement object (READ rappel.inc RP_MOV_OFF) */
#define KCAMR_F_TRY    0x673a20
#define KCAMR_F_ACT    0x6db3b0
#define KCAMR_F_UPD    0x825290

static struct { int mode, log, land, camfix, cam, handfrom, tailms; } kcamr;
static int kcamr_land_dead;                /* a fault in the landing code: only the landing re-aim and CamFix idle */
static struct { int have, movid, st, active; } kcamr_ls;          /* previous sample for the landing edge */
static struct { BYTE *rec; BYTE v; } kcamr_cs[16]; static int kcamr_cn; static DWORD kcamr_cp;   /* CamFix: profile records whose collision flag we cleared */
static int kcamr_dead;                     /* a fault in a wrapped stock routine: the vtable goes back, the module idles */
static DWORD kcamr_vt[1 + KCAMR_SLOTS];      /* [0] = RTTI locator, [1..] = the slots; the object points at &kcamr_vt[1] */
static DWORD kcamr_lastP, kcamr_lastMov;
static DWORD kcamr_lastPress, kcamr_lastGate, kcamr_gate;
static int kcamr_lastGo, kcamr_told_refuse, kcamr_told_live, kcamr_buildok = -1;
static int kcamr_prev[3];                  /* dry-mode log of 0x1f64 / 0x1f6c / 0x1f6d */

typedef BYTE  (__fastcall *kcamr_try_t)(DWORD self, DWORD edx, void *a1, void *a2, void *a3);
typedef void  (__fastcall *kcamr_act_t)(DWORD self, DWORD edx);
typedef DWORD (__fastcall *kcamr_upd_t)(DWORD self, DWORD edx, void *a1, void *a2, void *a3, void *a4, void *a5);

static int kcamr_fa_owns(void) { return klrp.on && klrp_lv.ok; }     /* the FA mini-cutscene rappel has this level */

static void kcamr_disable(const char *where)
{
    DWORD stock = (DWORD)(DWORD_PTR)KLH_VA(KCAMR_MOV_VT);
    kcamr_dead = 1;
    if (kcamr_lastMov && klh_rd32(kcamr_lastMov) == (DWORD)(DWORD_PTR)&kcamr_vt[1]) klfc_put(kcamr_lastMov, &stock, 4, "camprappel vptr back (disable)");   /* the tick returns early when dead, so hand it back here */
    klog("camprappel: DISABLED for this session (fault in %s) - the stock vtable is handed back", where);
}

/* ---- the guarded stock calls */
struct kcamr_try_a { DWORD self; void *a1, *a2, *a3; int r; };
static int kcamr_try_body(void *p) { struct kcamr_try_a *t = (struct kcamr_try_a *)p; t->r = KLFC_CALL(kcamr_try_t, KCAMR_F_TRY)(t->self, 0, t->a1, t->a2, t->a3) & 0xff; return 0; }
struct kcamr_upd_a { DWORD self; void *a[5]; DWORD r; };
static int kcamr_upd_body(void *p) { struct kcamr_upd_a *u = (struct kcamr_upd_a *)p; u->r = KLFC_CALL(kcamr_upd_t, KCAMR_F_UPD)(u->self, 0, u->a[0], u->a[1], u->a[2], u->a[3], u->a[4]); return 0; }
static int kcamr_act_body(void *p) { KLFC_CALL(kcamr_act_t, KCAMR_F_ACT)((DWORD)(DWORD_PTR)p, 0); return 0; }

static int kcamr_clips(DWORD mov, unsigned short ids[5])
{   /* READ rappel.inc 402-408: u16 clip ids at movement +0x1fe4,+0x1fe6,+0x1fe8,+0x1fea,+0x1fec */
    int i;
    for (i = 0; i < 5; i++) { ids[i] = 0xFFFF; klh_rd(mov + 0x1fe4 + 2 * i, &ids[i], 2); }
    return kcamr_native_ok(ids);
}
/* READ rappel.inc 403-411 (rp_clips_body): every id must also resolve to a readable clip record through the player's
 * clip lookup 0x59d550(player, id) - an id != 0xFFFF alone does not prove the clip exists (a NULL clip = crash 0x5a503a).
 * The lookup draws one number of the game's anim RNG; called once per press only (the one-decision rule). */
struct kcamr_look_a { DWORD P; unsigned short *ids; int ok; };
static int kcamr_look_body(void *p)
{
    struct kcamr_look_a *a = (struct kcamr_look_a *)p; int i;
    a->ok = 1;
    for (i = 0; i < 5; i++) {
        DWORD clip = a->ids[i] == 0xFFFF ? 0 : KLFC_CALL(DWORD (__fastcall *)(DWORD, DWORD, DWORD), 0x59d550)(a->P, 0, (DWORD)a->ids[i]);
        if (!klfc_ok(clip, 0x68)) { a->ok = 0; return 0; }
    }
    return 0;
}
static int kcamr_clips_resolve(DWORD mov, unsigned short ids[5])
{
    struct kcamr_look_a a; DWORD P = klh_rd32(mov + 0x38);
    if (!kcamr_clips(mov, ids)) return 0;
    a.P = P; a.ids = ids; a.ok = 0;
    if (klfc_guard("camprappel clip lookup", kcamr_look_body, &a) < 0) { kcamr_disable("clip lookup"); return 0; }
    return a.ok;
}

static BYTE __fastcall kcamr_Try(DWORD self, DWORD edx, void *a1, void *a2, void *a3)
{
    struct kcamr_try_a t; BYTE act = 0, prompt = 0, started = 0; DWORD now;
    (void)edx;
    if (kcamr_dead) return KLFC_CALL(kcamr_try_t, KCAMR_F_TRY)(self, 0, a1, a2, a3);   /* off: exactly the stock call */
    klh_rd(self + 0x1f64, &act, 1); klh_rd(self + 0x1f6c, &prompt, 1); klh_rd(self + 0x1f6d, &started, 1);
    if (!act && !prompt && !started) { DWORD z = 0; klfc_put(self + 0x1f68, &z, 4, "camprappel point entry"); }   /* READ rappel.inc 441-444: keep the entry fresh */
    t.self = self; t.a1 = a1; t.a2 = a2; t.a3 = a3; t.r = 0;
    if (klfc_guard("camprappel TryActivate", kcamr_try_body, &t) < 0) { kcamr_disable("TryActivate"); return 0; }
    if (!t.r) return 0;
    klh_rd(self + 0x1f64, &act, 1);                                  /* READ rappel.inc 447: re-read after the stock call */
    if (act) return 1;                                              /* a native rappel already runs */
    now = GetTickCount();
    if (kcamr_lastPress && now - kcamr_lastPress < 1000 && !kcamr_lastGo) { kcamr_lastPress = now; return 0; }   /* one decision per press; only a REFUSAL is repeated silently (READ 448-451 !g_rpLastPressR) */
    kcamr_lastPress = now;
    {
        unsigned short ids[5]; int ok = kcamr_clips_resolve(self, ids), go = kcamr_decide(kcamr.mode, ok, 0);
        kcamr_lastGo = go;
        if (kcamr.mode == KCAMR_LIVE || kcamr.mode == KCAMR_AUTO) if (!kcamr_told_live++) klog("camprappel: Mode live/auto: the live descent is not ported - native only");
        if (kcamr.log) klog("camprappel: use pressed at a rappel point (mode %d, clips %d/5) -> %s", kcamr.mode, kcamr_clips_present(ids), go ? "native starts" : "REFUSED");
        if (!go && !ok && !kcamr_told_refuse++)
            klog("camprappel: REFUSED - this level's .ANM lacks the /Movement/Rappelling clips (ids %04x %04x %04x %04x %04x, or a clip does not resolve); the stock rappel would crash at 0x5a503a", ids[0], ids[1], ids[2], ids[3], ids[4]);
        return (BYTE)go;
    }
}

static void __fastcall kcamr_Act(DWORD self, DWORD edx)
{
    (void)edx;
    if (kcamr_dead) { KLFC_CALL(kcamr_act_t, KCAMR_F_ACT)(self, 0); return; }
    if (klfc_guard("camprappel Activate", kcamr_act_body, (void *)(DWORD_PTR)self) < 0) kcamr_disable("Activate");
}

static DWORD __fastcall kcamr_Upd(DWORD self, DWORD edx, void *a1, void *a2, void *a3, void *a4, void *a5)
{
    struct kcamr_upd_a u;
    (void)edx;
    if (kcamr_dead) return KLFC_CALL(kcamr_upd_t, KCAMR_F_UPD)(self, 0, a1, a2, a3, a4, a5);
    u.self = self; u.a[0] = a1; u.a[1] = a2; u.a[2] = a3; u.a[3] = a4; u.a[4] = a5; u.r = 0;
    if (klfc_guard("camprappel Update", kcamr_upd_body, &u) < 0) {
        /* the native no-op path (READ rappel.inc 483-488, 0x8259b7): out matrix = in matrix, out vector = in vector, second out vector = 0 */
        if (klfc_ok((DWORD)(DWORD_PTR)a1, 36) && klfc_ok((DWORD)(DWORD_PTR)a3, 36)) memcpy(a3, a1, 36);
        if (klfc_ok((DWORD)(DWORD_PTR)a2, 12) && klfc_ok((DWORD)(DWORD_PTR)a4, 12)) memcpy(a4, a2, 12);
        if (klfc_ok((DWORD)(DWORD_PTR)a5, 12)) memset(a5, 0, 12);
        kcamr_disable("Update");
        return (DWORD)(DWORD_PTR)a5;
    }
    return u.r;
}

static int kcamr_build_ok(void)
{   /* READ rappel.inc 153-168; GUESS: prologue bytes re-read through klh_rd (they equal luvsic's, measured on his build) */
    static const struct { DWORD a; BYTE b[6]; } t[] = {
        { 0x673a20, { 0x83, 0xec, 0x0c, 0x56, 0x8b, 0xf1 } }, { 0x6db3b0, { 0x83, 0xec, 0x6c, 0x53, 0x55, 0x56 } },
        { 0x825290, { 0x81, 0xec, 0xc0, 0x00, 0x00, 0x00 } },
    };
    int i; DWORD vt[18];
    for (i = 0; i < 3; i++) {
        BYTE b[6];
        if (!klh_rd((DWORD_PTR)KLH_VA(t[i].a), b, 6) || memcmp(b, t[i].b, 6)) { klog("camprappel: kl2 build mismatch at %08lx - module off", t[i].a); return 0; }
    }
    if (!klh_rd((DWORD_PTR)KLH_VA(KCAMR_MOV_VT), vt, sizeof vt) || vt[14] != (DWORD)(DWORD_PTR)KLH_VA(KCAMR_F_TRY) || vt[15] != (DWORD)(DWORD_PTR)KLH_VA(KCAMR_F_ACT) || vt[17] != (DWORD)(DWORD_PTR)KLH_VA(KCAMR_F_UPD)) {
        klog("camprappel: ZFFPlayerMovementRappel vtable differs - module off"); return 0;
    }
    return 1;
}

static void kcamr_vt_init(void)
{
    if (kcamr_vt[1]) return;
    kcamr_vt[0] = klh_rd32((DWORD_PTR)KLH_VA(KCAMR_MOV_VT) - 4);
    klh_rd((DWORD_PTR)KLH_VA(KCAMR_MOV_VT), &kcamr_vt[1], 4 * KCAMR_SLOTS);
    kcamr_vt[1 + 14] = (DWORD)(DWORD_PTR)kcamr_Try;
    kcamr_vt[1 + 15] = (DWORD)(DWORD_PTR)kcamr_Act;
    kcamr_vt[1 + 17] = (DWORD)(DWORD_PTR)kcamr_Upd;
}

static DWORD kcamr_mov(DWORD P)
{   /* the player's rappel movement object, 0 if it is not one (READ rappel.inc 179-184) */
    DWORD m = klh_rd32(P + KCAMR_MOV_OFF), vt;
    if (!klfc_ok(m, 0x2020)) return 0;
    vt = klh_rd32(m);
    return (vt == (DWORD)(DWORD_PTR)KLH_VA(KCAMR_MOV_VT) || vt == (DWORD)(DWORD_PTR)&kcamr_vt[1]) && klh_rd32(m + 0x38) == P ? m : 0;
}

static void kcamr_vt_apply(DWORD mov, int want)
{
    DWORD cur = klh_rd32(mov), stock = (DWORD)(DWORD_PTR)KLH_VA(KCAMR_MOV_VT), ours = (DWORD)(DWORD_PTR)&kcamr_vt[1];
    BYTE act = 0;
    klh_rd(mov + 0x1f64, &act, 1);
    if (want && cur == stock) {
        if (act) return;                                            /* never swap under a running native rappel */
        kcamr_vt_init(); klfc_put(mov, &ours, 4, "camprappel vptr");
        klog("camprappel: guards on the player's rappel movement %08lx (vtable copy %p)", mov, (void *)&kcamr_vt[1]);
    } else if (!want && cur == ours) {
        klfc_put(mov, &stock, 4, "camprappel vptr back");
        klog("camprappel: guards off");
    }
}


/* ---- landing camera (READ rappel.inc 273-282, 360-385). All engine calls inside klfc_guard; a fault only idles the landing code. */
struct kcamr_land_a { DWORD P; float M[9], f[3]; int ray_ok, ray_hit; };
static int kcamr_land_ray_body(void *p)
{   /* chest height (130 cm) 150 cm along his facing, mask 0x28 (hero-only walls block) */
    struct kcamr_land_a *a = (struct kcamr_land_a *)p; float o[3], seg[3], pt[3], y = kcamr_yaw(a->M) * 0.0174532925f; struct klfc_ray ray; int h;
    klfc_v3set(o, a->f[0], a->f[1] + 130.0f, a->f[2]); klfc_v3set(seg, (float)sin(y) * 150.0f, 0, (float)cos(y) * 150.0f);
    h = klfc_cast(o, seg, 0x28, &ray, pt);
    a->ray_ok = h >= 0; a->ray_hit = h;
    return 0;
}
struct kcamr_tele_a { DWORD P; float M[9], f[3]; int cam; };
static int kcamr_tele_body(void *p)
{   /* 0x82cc40(player, M, P, resetVel, force, 0): force=1 re-aims the camera behind the player (0x8de300(1)) */
    struct kcamr_tele_a *a = (struct kcamr_tele_a *)p;
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, const float *, const float *, int, int, int), KLFC_TELE)(a->P, 0, a->M, a->f, a->cam, a->cam, 0);
    return 0;
}
struct kcamr_pose_a { DWORD P; float M[9], f[3]; int ok; };
static int kcamr_pose_body(void *p) { struct kcamr_pose_a *a = (struct kcamr_pose_a *)p; a->ok = klfc_pose(a->P, a->M, a->f); return 0; }

static void kcamr_do_land(DWORD P)
{
    struct kcamr_pose_a pa; struct kcamr_land_a la; struct kcamr_tele_a ta; int fin, g; float yaw;
    memset(&pa, 0, sizeof pa); pa.P = P;
    if (klfc_guard("camprappel land pose", kcamr_pose_body, &pa) < 0 || !pa.ok) { if (kcamr.log) klog("camprappel: land: no player pose - skipped"); return; }
    yaw = kcamr_yaw(pa.M);
    if (yaw < 0) { if (kcamr.log) klog("camprappel: land: degenerate facing - skipped"); return; }
    memset(&la, 0, sizeof la); la.P = P; memcpy(la.M, pa.M, sizeof la.M); memcpy(la.f, pa.f, sizeof la.f);
    if (kcamr.land == KCAMR_L_AUTO && klfc_guard("camprappel land ray", kcamr_land_ray_body, &la) < 0) { kcamr_land_dead = 1; klog("camprappel: land DISABLED (fault in the wall ray)"); return; }
    fin = kcamr_land_resolve(kcamr.land, la.ray_ok, la.ray_hit);
    if (fin == KCAMR_L_OFF) return;
    memset(&ta, 0, sizeof ta); ta.P = P; ta.cam = kcamr_land_cam(fin);
    memcpy(ta.f, pa.f, sizeof ta.f); kcamr_yaw_matrix(kcamr_land_yaw(yaw, fin), ta.M);
    g = klfc_guard("camprappel land teleport", kcamr_tele_body, &ta);
    if (g < 0) { kcamr_land_dead = 1; klog("camprappel: land DISABLED (fault in the teleport)"); return; }
    if (kcamr.log) klog("camprappel: land=%d (ray ok %d hit %d) -> action %d: yaw %.1f -> %.1f, camera re-aim %d, feet (%.1f,%.1f,%.1f)", kcamr.land, la.ray_ok, la.ray_hit, fin, yaw, kcamr_land_yaw(yaw, fin), ta.cam, pa.f[0], pa.f[1], pa.f[2]);
}

static void kcamr_land_watch(DWORD P, DWORD mov)
{
    BYTE act = 0; int movid, st, landed;
    if (kcamr_land_dead || !kcamr.land) return;
    klh_rd(mov + 0x1f64, &act, 1);
    movid = klfc_movid(P);
    st = (act || movid == 0x10) ? (int)klh_rd32(P + 0x25c0) : -1;
    landed = kcamr_landed(kcamr_ls.have, kcamr_ls.movid, kcamr_ls.st, movid, act);
    kcamr_ls.have = 1; kcamr_ls.movid = movid; kcamr_ls.st = st; kcamr_ls.active = act;
    if (landed) kcamr_do_land(P);
}

/* ---- CamFix=nocoll (READ rappel.inc 284-345): clear the collision flag (+0x156) of every camera profile record that is active
 * during a rappel, so the camera is not pulled in under the facade girders; put it back when the rappel ends. Heap writes via klh_data. */
#define KCAMR_CAM_VT 0xbb76a4
static void kcamr_cam_restore(DWORD P)
{
    int i;
    for (i = 0; i < kcamr_cn; i++) if (P == kcamr_cp && klfc_ok((DWORD)(DWORD_PTR)kcamr_cs[i].rec, 0x198)) klfc_put((DWORD)(DWORD_PTR)kcamr_cs[i].rec + 0x156, &kcamr_cs[i].v, 1, "camprappel camfix restore");
    if (kcamr_cn && kcamr.log) klog("camprappel: camfix: %d profile collision flag(s) %s", kcamr_cn, P == kcamr_cp ? "restored" : "dropped (player changed)");
    kcamr_cn = 0; kcamr_cp = 0;
}
static void kcamr_cam_watch(DWORD P, DWORD mov)
{
    BYTE act = 0; int rap; DWORD cam, prof; BYTE fl = 0, z = 0; int k;
    if (!kcamr.camfix && !kcamr_cn) return;
    klh_rd(mov + 0x1f64, &act, 1);
    rap = act || klfc_movid(P) == 0x10;
    if (!rap || !kcamr.camfix) { if (kcamr_cn) kcamr_cam_restore(P); return; }
    cam = klh_rd32(P + 0xbd8);
    if (!klfc_ok(cam, 0xc00) || klh_rd32(cam) != KCAMR_CAM_VT) return;
    prof = klh_rd32(cam + 0xb2c);
    if (!klfc_ok(prof, 0x198)) return;
    klh_rd(prof + 0x156, &fl, 1);
    if (!fl) return;
    for (k = 0; k < kcamr_cn && (DWORD)(DWORD_PTR)kcamr_cs[k].rec != prof; k++) ;
    if (k == kcamr_cn && kcamr_cn < 16) { kcamr_cs[kcamr_cn].rec = (BYTE *)(DWORD_PTR)prof; kcamr_cs[kcamr_cn].v = fl; kcamr_cn++; kcamr_cp = P; }
    klfc_put(prof + 0x156, &z, 1, "camprappel camfix nocoll");
}


/* ---- Cam=ours (1110, owner: "the start animation is cool from his but when you are actually rappelling, looking left and right should be my version").
 * While the descent runs (sub-state >= HandFrom, until the landing + TailMs) the camera's box-profile pointer cam+0x7fc is cleared every frame, so the
 * stock free third-person follow camera (the one our klcam.c / klcamsmooth.c tune) takes over from the RappelCB_* fixed shots (see klcamprappel_logic.h).
 * One heap word, through klfc_put (klh_data refuses a non-writable page). Nothing is restored: a box that triggers later sets the pointer itself (0x700830).
 * GUESS: 0x7fc is the only switch (0x447240 / 0x78bbc0 READ); the volume list at gamedata+0x8e8 is not touched (a camera that still looks fixed is logged). */
#define KCAMR_CAM_BOX 0x7fc
static struct { int own, frames, clears, warned; DWORD last_own, cam_seen; DWORD ended; int had_end; } kcamr_co;
static void kcamr_cam_ours_watch(DWORD P, DWORD mov)
{
    BYTE act = 0; int rap, st = -1, ours, edge; DWORD cam, box, now = GetTickCount(); long since = -1;
    if (kcamr.cam != KCAMR_CAM_OURS && !kcamr_co.own) return;
    klh_rd(mov + 0x1f64, &act, 1);
    rap = act || klfc_movid(P) == 0x10;
    if (rap) st = (int)klh_rd32(P + 0x25c0);
    if (rap) { kcamr_co.had_end = 0; kcamr_co.last_own = 0; }
    else if (kcamr_co.own || kcamr_co.had_end) { if (!kcamr_co.had_end) { kcamr_co.had_end = 1; kcamr_co.ended = now; } since = (long)(now - kcamr_co.ended); }
    ours = kcamr_cam_ours_now(kcamr.cam, rap, st, kcamr.handfrom, since, kcamr.tailms);
    edge = kcamr_cam_edge(kcamr_co.own, ours);
    if (edge < 0) {
        if (kcamr.log) klog("camprappel: Cam=ours: camera handed back to the level (%d frame(s), box pointer cleared %d time(s), tail %d ms)", kcamr_co.frames, kcamr_co.clears, kcamr.tailms);
        memset(&kcamr_co, 0, sizeof kcamr_co); return;
    }
    if (!ours) return;
    cam = klh_rd32(P + 0xbd8);
    if (!klfc_ok(cam, 0xc00) || klh_rd32(cam) != KCAMR_CAM_VT) return;
    box = klh_rd32(cam + KCAMR_CAM_BOX);
    if (edge > 0) {
        DWORD cur = klh_rd32(cam + 0xb2c), efm = klfc_ok(box, 0x190) ? klh_rd32(box + 0x180) : 0;
        kcamr_co.own = 1; kcamr_co.frames = kcamr_co.clears = kcamr_co.warned = 0;
        if (kcamr.log) klog("camprappel: Cam=ours: TAKEN at rappel state %d (HandFrom %d): box profile %08lx (EFMMode %lu), current profile %08lx - the free follow camera takes over", st, kcamr.handfrom, box, efm, cur);
    }
    kcamr_co.frames++;
    if (kcamr_cam_must_clear(ours, box)) {
        DWORD z = 0;
        klfc_put(cam + KCAMR_CAM_BOX, &z, 4, "camprappel cam=ours box profile");
        if (!kcamr_co.clears++ && kcamr.log && edge <= 0) klog("camprappel: Cam=ours: a box set its profile again (%08lx) - cleared", box);
    }
    if (kcamr_co.frames == 90 && !kcamr_co.warned) {          /* 1.5 s at 60 fps: is the camera still on a fixed-shot profile? */
        DWORD cur = klh_rd32(cam + 0xb2c);
        if (klfc_ok(cur, 0x190) && (klh_rd32(cur + 0x180) == 1 || klh_rd32(cur + 0x180) == 3)) { kcamr_co.warned = 1; klog("camprappel: Cam=ours: the current profile %08lx still has EFMMode %lu after 90 frames (a camera volume, not a box pointer?) - GUESS: needs another switch", cur, klh_rd32(cur + 0x180)); }
    }
}

static int kcamr_tick_body(void *unused)
{
    DWORD gd, P, mov, now; signed char pi = -1; int want;
    (void)unused;
    now = GetTickCount();
    if (now - kcamr_lastGate > 1000 || !kcamr_lastGate) { kcamr_gate = klcmp_level_active() != 0; kcamr_lastGate = now ? now : 1; }
    want = kcamr.mode >= KCAMR_NATIVE && kcamr_gate && !kcamr_fa_owns();
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)))) return 0;
    if (!klh_rd(gd + 0x898, &pi, 1) || pi < 0 || pi > 7) return 0;
    if (!(P = klh_rd32(gd + 0x828 + 4 * pi)) || klh_pvt(P) != KLFC_PLAYER_VT || !klfc_ok(P, 0x2e00)) return 0;
    mov = kcamr_mov(P);
    if (!mov) {
        if (kcamr_gate && P != kcamr_lastP) { kcamr_lastP = P; klog("camprappel: no rappel movement at player+0x%x (vt check failed) - idle", KCAMR_MOV_OFF); }
        return 0;
    }
    if (P != kcamr_lastP || mov != kcamr_lastMov) {
        unsigned short ids[5];
        kcamr_lastP = P; kcamr_lastMov = mov; kcamr_told_refuse = 0; memset(kcamr_prev, 0, sizeof kcamr_prev);
        if (kcamr_gate && kcamr.mode) { kcamr_clips(mov, ids); klog("camprappel: level: native rappel clips %d/5 (ids %04x %04x %04x %04x %04x)", kcamr_clips_present(ids), ids[0], ids[1], ids[2], ids[3], ids[4]); }
    }
    kcamr_vt_apply(mov, want);
    if (kcamr_gate && !kcamr_fa_owns()) { kcamr_land_watch(P, mov); kcamr_cam_watch(P, mov); kcamr_cam_ours_watch(P, mov); }
    if (kcamr.mode == KCAMR_DRY && kcamr_gate) {
        BYTE a = 0, p = 0, s = 0; klh_rd(mov + 0x1f64, &a, 1); klh_rd(mov + 0x1f6c, &p, 1); klh_rd(mov + 0x1f6d, &s, 1);
        if (a != kcamr_prev[0] || p != kcamr_prev[1] || s != kcamr_prev[2]) {
            kcamr_prev[0] = a; kcamr_prev[1] = p; kcamr_prev[2] = s;
            klog("camprappel: dry: active %d prompt %d started %d (state %d)", a, p, s, (int)klh_rd32(P + 0x25c0));
        }
    }
    return 0;
}

static void kcamr_tick(int game_thread)
{
    if ((!kcamr.mode && !kcamr.land && !kcamr.camfix && !kcamr.cam) || kcamr_dead || !game_thread || !klh_exe_ok) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;        /* only the gameplay call (same filter as klfreeclimb.c) */
    if (kl_online()) return;                                          /* campaign levels are offline; never act in a session */
    if (kcamr_buildok < 0) kcamr_buildok = kcamr_build_ok();
    if (!kcamr_buildok) return;
    if (klfc_guard("camprappel tick", kcamr_tick_body, 0) < 0) kcamr_disable("tick");
}

static void kcamr_init(void)
{
    char s[32];
    memset(&kcamr, 0, sizeof kcamr);
    GetPrivateProfileStringA("CampRappel", "Mode", "0", s, sizeof s, klh_ini);
    kcamr.mode = kcamr_mode_parse(s);
    kcamr.log = (int)GetPrivateProfileIntA("CampRappel", "Log", 1, klh_ini);
    if (kcamr.mode) klog("camprappel: Mode=%s (%d) - acts only on a campaign level ([Campaign] Enable=1)", s, kcamr.mode);
    GetPrivateProfileStringA("CampRappel", "Land", "off", s, sizeof s, klh_ini);
    kcamr.land = kcamr_land_parse(s);
    kcamr.camfix = (int)GetPrivateProfileIntA("CampRappel", "CamFix", 0, klh_ini) != 0;
    GetPrivateProfileStringA("CampRappel", "Cam", "his", s, sizeof s, klh_ini);
    kcamr.cam = kcamr_cam_parse(s);
    kcamr.handfrom = kcamr_cam_handfrom((int)GetPrivateProfileIntA("CampRappel", "CamHandFrom", 3, klh_ini));
    kcamr.tailms = (int)GetPrivateProfileIntA("CampRappel", "CamTailMs", 1500, klh_ini);
    if (kcamr.tailms < 0) kcamr.tailms = 0;
    if (kcamr.tailms > 10000) kcamr.tailms = 10000;
    if (kcamr.cam) klog("camprappel: Cam=ours (HandFrom %d, TailMs %d) - acts only on a campaign level; GUESS (not run in kl2 yet)", kcamr.handfrom, kcamr.tailms);
    if (kcamr.land || kcamr.camfix) klog("camprappel: Land=%s (%d), CamFix=%d - acts only on a campaign level; GUESS (not run in kl2 yet)", s, kcamr.land, kcamr.camfix);
}
