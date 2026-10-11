/* ==================== Dead Men climb in Dog Days (W + E into a ledge) ====================
   Included by anp_loader.c (after the helpers it uses: anp_log, readable, rtti_name, hook_iat, g_dir).
   Dead Men's ZFFPlayerMovementClimb (kaneandlynch.exe 0x605b50) rebuilt as a free player move:
   - frame hook: kl2's IAT slot for steam_api!SteamAPI_RunCallbacks (no kl2 byte changed, CEG-safe);
     only the gameplay-frame call site (return address 0x87aa82) runs the climb tick.
   - probe: DM's ledge rays through DD's ZCollisionWintel raycast (0x7daa80), DM order and outcomes.
   - live: a real ZFFActionVaultOver (type 0x2B) with its vptr pointed at a loader-owned copy of the vtable
     (slots 2 Start, 4 Update, 5 End, 10 AnimEnd replaced), playing /Movement/Climb/Up/<class>.
   Config: <DD>\ANP_climb.txt, first token off | dry | live (absent = dry), then key=value options:
     warp=end|dm  vehicle=action|snap  needblock=0|1  fwd=1|-1  cam=0|1  snap=0|1  trace=0|1
     (trace=1 also logs 'climb: pos: x y z yaw' once a second, in any mode.)
   Test teleport: <DD>\ANP_tp.txt "x y z yawDeg [full]" moves the player once (see climb_tp_body), in any mode.
   Every engine call runs under climb_guarded(): a fault on the main thread is caught by the VEH,
   execution resumes after the guarded call with -1, and climbing is disabled for the session.
   Log lines start with "climb:". */
#include <math.h>

#define CL_VF(o, off) (*(void**)(*(BYTE**)(o) + (off)))
#define CL_PLAYER_VT   0xbb45f4   /* ZFFPlayer */
#define CL_VAULT_VT    0xbb5188   /* ZFFActionVaultOver (12 slots) */
#define CL_RIGID_VT    0xbb09f4   /* ZHavokRigidBody */
#define CL_COLLW_VT    0xb9a1d4   /* ZCollisionWintel */
#define CL_RCB_RA      0x87aa82   /* return address of the per-frame SteamAPI_RunCallbacks call */

/* ---------- fault guard (MinGW has no __try) ---------- */
typedef struct ClGuard { DWORD esp, ebp, seh; struct ClGuard *prev; const char *what; DWORD code, eip; WORD cw, pad; } ClGuard; /* 32 bytes */
ClGuard *g_clGuardTop;                 /* non-static: used from asm */
static DWORD g_clMainTid;
static int g_climbDead;
int climb_guarded(const char *what, int (*fn)(void*), void *arg);   /* fn(arg), or -1 after a recovered fault */
void climb_guard_recover(void);
__attribute__((naked, used)) static void climb_guard_asm(void) { __asm__ volatile(   /* hosts the two entry points in .text */
    ".p2align 4\n"
    ".globl _climb_guarded\n"
    "_climb_guarded:\n"
    "  pushl %ebp\n  movl %esp,%ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n  subl $32,%esp\n  movl %esp,%ebx\n"
    "  movl %fs:0,%eax\n  movl %eax,8(%ebx)\n"
    "  movl _g_clGuardTop,%eax\n  movl %eax,12(%ebx)\n"
    "  movl 8(%ebp),%eax\n  movl %eax,16(%ebx)\n"
    "  movl $0,20(%ebx)\n  movl $0,24(%ebx)\n"
    "  fnstcw 28(%ebx)\n"
    "  movl %esp,0(%ebx)\n  movl %ebp,4(%ebx)\n"
    "  movl %ebx,_g_clGuardTop\n"
    "  pushl 16(%ebp)\n  call *12(%ebp)\n  addl $4,%esp\n"
    "  jmp 1f\n"
    ".globl _climb_guard_recover\n"
    "_climb_guard_recover:\n"          /* VEH resumes here with esp = ebp-frame of the faulted guard */
    "  cld\n  movl %esp,%ebx\n  movl 8(%ebx),%ecx\n  movl %ecx,%fs:0\n"
    "  fninit\n  fldcw 28(%ebx)\n  movl $-1,%eax\n"
    "1:\n"
    "  movl 12(%ebx),%ecx\n  movl %ecx,_g_clGuardTop\n"
    "  addl $32,%esp\n  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n"); }

/* called from veh() before its generic logging: 1 = redirected to climb_guard_recover */
static int climb_veh(PEXCEPTION_POINTERS ep) {
    ClGuard *g = g_clGuardTop;
    CONTEXT *c = ep->ContextRecord;
    DWORD code = ep->ExceptionRecord->ExceptionCode;
    if (!g || !g_clMainTid || GetCurrentThreadId() != g_clMainTid || c->Eip == 0xa8e3cb) return 0;
    switch (code) {
    case 0xC0000005: case 0x80000003: case 0xC000001D: case 0xC0000096: case 0xC0000094: case 0xC0000095:
    case 0xC000008E: case 0xC000008F: case 0xC0000090: case 0xC0000091: case 0xC0000092: case 0xC0000093: break;
    default: return 0;
    }
    g->code = code; g->eip = c->Eip;
    anp_log("climb: FAULT %08lx at %08lx (info %08lx) in %s  eax=%08lx ebx=%08lx ecx=%08lx edx=%08lx esi=%08lx edi=%08lx esp=%08lx",
            code, c->Eip, ep->ExceptionRecord->NumberParameters > 1 ? (DWORD)ep->ExceptionRecord->ExceptionInformation[1] : 0,
            g->what ? g->what : "?", c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Esp);
    c->Esp = g->esp; c->Ebp = g->ebp; c->Eip = (DWORD)climb_guard_recover;
    return 1;
}

/* ---------- engine entry points (kl2.exe, static RE) ---------- */
typedef void  (__attribute__((thiscall)) *cl_Pose_t)(void *node, float *M, float *P);              /* 0x857110: M rows +Z,up,+X; P = feet */
typedef unsigned char (__attribute__((thiscall)) *cl_Ray_t)(void *cw, void *res, void *z0, const float *o, const float *seg,
                                                             int z1, unsigned mask, int one, int z2, int layer); /* 0x7daa80 */
typedef WORD *(__attribute__((thiscall)) *cl_Name_t)(void *pl, WORD *out, const char *name);      /* 0x426890 */
typedef BYTE *(__attribute__((thiscall)) *cl_Var_t)(void *pl, int id);                            /* 0x59d550 (advances RNG) */
typedef int   (__stdcall *cl_Event_t)(void *clip, int type, int *idx);                            /* 0x4a75d0: frame or -1 */
typedef void  (__attribute__((thiscall)) *cl_Root_t)(void *clip, void *anmdb, float frame, float *q, float *p, int mirror); /* 0x5a5030 */
typedef unsigned char (__attribute__((thiscall)) *cl_Warp_t)(void *pl, const float *M, const float *P, float frames); /* pl vt+0x208 */
typedef BYTE *(__attribute__((thiscall)) *cl_Play_t)(void *pl, void *clip, int flags);            /* pl vt+0x204 */
typedef void  (__attribute__((thiscall)) *cl_Cam_t)(void *cam, float a, float b, float c);        /* 0x798d00 */
typedef void  (__attribute__((thiscall)) *cl_Tele_t)(void *pl, const float *M, const float *P, int resetVel, int force, int a5); /* 0x82cc40 */
typedef BYTE *(__attribute__((thiscall)) *cl_Create_t)(void *pl, int type);                       /* pl vt+0x384 */
typedef void  (__attribute__((thiscall)) *cl_StartAct_t)(void *pl, void *act);                    /* pl vt+0x370 */
typedef void *(__attribute__((thiscall)) *cl_Get_t)(void *o);
typedef int   (__attribute__((thiscall)) *cl_Int_t)(void *o);
typedef void  (__attribute__((thiscall)) *cl_Void_t)(void *o);
typedef unsigned char (__attribute__((thiscall)) *cl_Char_t)(void *o);

/* ---------- config: ANP_climb.txt ---------- */
enum { CL_OFF, CL_DRY, CL_LIVE };
typedef struct { int mode, warpDm, vehSnap, needblock, fwd, cam, snap, trace, minIn; } ClCfg;
#define CL_MININ_DEF 30          /* cm: Final must stand at least this far past the wall face (0 = off, DM-exact) */
static ClCfg g_ccfg = {CL_DRY, 0, 0, 0, 1, 1, 1, 0, CL_MININ_DEF};
static int g_ccfgPresent = -1; static FILETIME g_ccfgTime; static DWORD g_ccfgPoll;
static void climb_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_ccfgPresent >= 0 && now - g_ccfgPoll < 1000) return;
    g_ccfgPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_climb.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_ccfgPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_ccfgTime) == 0)) return;
    g_ccfgPresent = present;
    if (present) g_ccfgTime = fa.ftLastWriteTime;
    ClCfg c = {CL_DRY, 0, 0, 0, 1, 1, 1, 0, CL_MININ_DEF};
    char buf[512] = ""; const char *note = present ? "" : " (no ANP_climb.txt)";
    if (present) {
        FILE *f = fopen(fn, "r");
        if (f) { size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f); }
        else note = " (ANP_climb.txt unreadable)";
        int first = 1;
        for (char *t = strtok(buf, " \t\r\n,;"); t; t = strtok(NULL, " \t\r\n,;"), first = 0) {
            if (first && !_stricmp(t, "off")) { c.mode = CL_OFF; continue; }
            if (first && !_stricmp(t, "dry")) { c.mode = CL_DRY; continue; }
            if (first && !_stricmp(t, "live")) { c.mode = CL_LIVE; continue; }
            char *eq = strchr(t, '='); if (!eq) { anp_log("climb: config token '%s' ignored", t); continue; }
            *eq = 0; const char *v = eq + 1; int iv = atoi(v);
            if (!_stricmp(t, "warp")) c.warpDm = !_stricmp(v, "dm");
            else if (!_stricmp(t, "vehicle")) c.vehSnap = !_stricmp(v, "snap");
            else if (!_stricmp(t, "needblock")) c.needblock = iv != 0;
            else if (!_stricmp(t, "fwd")) c.fwd = iv < 0 ? -1 : 1;
            else if (!_stricmp(t, "cam")) c.cam = iv != 0;
            else if (!_stricmp(t, "snap")) c.snap = iv != 0;
            else if (!_stricmp(t, "trace")) c.trace = iv != 0;
            else if (!_stricmp(t, "minin")) c.minIn = iv < 0 ? 0 : iv > 100 ? 100 : iv;
            else anp_log("climb: config key '%s' unknown", t);
        }
    }
    g_ccfg = c;
    static const char *mn[] = {"off", "dry", "live"};
    anp_log("climb: config mode=%s warp=%s vehicle=%s needblock=%d fwd=%d cam=%d snap=%d trace=%d minin=%d%s", mn[c.mode],
            c.warpDm ? "dm" : "end", c.vehSnap ? "snap" : "action", c.needblock, c.fwd, c.cam, c.snap, c.trace, c.minIn, note);
}

/* ---------- small vector helpers ---------- */
static void v3set(float *d, float x, float y, float z) { d[0] = x; d[1] = y; d[2] = z; }
static void v3madd(float *d, const float *a, const float *b, float s) { d[0] = a[0] + b[0] * s; d[1] = a[1] + b[1] * s; d[2] = a[2] + b[2] * s; }
static float v3dist(const float *a, const float *b) {
    float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2]; return sqrtf(x * x + y * y + z * z);
}

/* ---------- climb state ---------- */
typedef struct {
    int active, phase, startT, did560, reached, e5, e6, frames, traceN, traceLines, animEndLogs;
    BYTE *act, *P, *clip, *anim; DWORD anim0; int animId; float from, to, h;
    float S[3], Ledge[3], Final[3], M[9], gv[3], push[3];
    const char *endReason;
} ClRec;
static ClRec g_cl;
static DWORD g_vtbuf[13];            /* [0] = COL (RTTI), [1..12] = vtable */
static BYTE g_edge[0x80];            /* dummy cover edge for act+0x7c */

typedef struct {
    float M[9], Pf[3], F[3], B[3], Wp[3], Wn[3], S[3], Ledge[3], Final[3], gv[3], g0[3], ge5[3], ge6[3], gend[3], push[3];
    float h; int cls, frames, e5, e6; BYTE *clip; WORD id; const char *clipName, *why;
} ClProbe;
static const struct { const char *name; float max, off; } g_clCls[3] = {{"Low", 120, 81}, {"Medium", 170, 47}, {"High", 220, 47}};

static BYTE *cl_sys(void) { BYTE *s = readable((void*)0xdd2640, 4) ? *(BYTE**)0xdd2640 : 0; return readable(s, 0xb40) ? s : 0; }
static int cl_curT(void) { BYTE *s = cl_sys(); return s ? *(int*)(s + 0x48) : 0; }
static int cl_pose(BYTE *P, float *M, float *Pf) {
    void *node = readable(P + 4, 4) ? *(void**)(P + 4) : 0;
    if (!readable(node, 0x80)) return 0;
    ((cl_Pose_t)0x857110)(node, M, Pf);
    return 1;
}
static BYTE *cl_disp_cur(BYTE *P) {   /* current action of the player's dispatcher, (BYTE*)1 if unreadable */
    BYTE *d = readable(P + 0x19c, 4) ? *(BYTE**)(P + 0x19c) : 0;
    return readable(d, 8) ? *(BYTE**)(d + 4) : (BYTE*)1;
}
static float cl_anim_cur(void) {      /* current frame of our anim channel, -1 if the channel was reused / lost */
    BYTE *a = g_cl.anim;
    if (!a || !readable(a, 0x20) || *(DWORD*)a != g_cl.anim0) return -1.0f;
    return *(float*)(a + 4);
}

/* ---------- raycast ---------- */
#pragma pack(push, 1)
typedef struct { float frac, hit[3]; BYTE *node; float v0[3], v1[3], v2[3]; BYTE pad[0x100]; } ClRay;
#pragma pack(pop)
static int cl_ray(const float o[3], const float seg[3], unsigned mask, ClRay *r, float pt[3]) {
    BYTE *sys = cl_sys(); if (!sys) return -1;
    BYTE *db = *(BYTE**)(sys + 0xac); if (!readable(db + 0x52cc, 4)) return -1;
    BYTE *ph = *(BYTE**)(db + 0x52cc); if (!readable(ph + 0x14dc, 4) || !*(void**)(ph + 0x14dc)) return -1;
    void *cw = readable((void*)0x138c868, 4) ? *(void**)0x138c868 : 0;
    if (!readable(cw, 4) || *(DWORD*)cw != CL_COLLW_VT) return -1;
    if (*(int*)0xcd9c60 != 1) return -1;              /* 0x5022b0: otherwise the legacy (non-Havok) path */
    memset(r, 0, sizeof *r); r->frac = 1.0f;
    int hit = ((cl_Ray_t)0x7daa80)(cw, r, 0, o, seg, 0, mask, 1, 0, 11) & 1;
    if (r->frac >= 0.0f && r->frac <= 1.0f) v3madd(pt, o, seg, r->frac);
    else memcpy(pt, r->hit, 12);
    return hit;
}
static void cl_hit_obj(const ClRay *r, BYTE **obj, const char **why) {
    *obj = 0; *why = 0;
    BYTE *n = r->node;
    if (readable(n + 0x60, 4)) *obj = *(BYTE**)(n + 0x60);
    if ((readable(*obj, 4) && *(DWORD*)*obj == CL_RIGID_VT) || (readable(n, 4) && *(DWORD*)n == CL_RIGID_VT)) { *why = "rigid"; return; }
    const char *nm = rtti_name(*obj);
    if (strstr(nm, "Actor") || strstr(nm, "Player")) *why = "actor";
}

/* ---------- probe: DM 0x605b50 on DD's world ---------- */
static int climb_probe(BYTE *P, ClProbe *r) {
    memset(r, 0, sizeof *r); r->cls = -1; r->why = "no candidate";
    if (!cl_pose(P, r->M, r->Pf)) { r->why = "no node"; return 0; }
    float L = sqrtf(r->M[0] * r->M[0] + r->M[2] * r->M[2]);
    if (L < 1e-3f) { r->why = "bad facing"; return 0; }
    float fs = (float)g_ccfg.fwd;
    v3set(r->F, -r->M[0] / L * fs, 0, -r->M[2] / L * fs);      /* world forward = -row0 (DM's D = +row0) */
    v3set(r->B, -r->F[0], 0, -r->F[2]);
    const float rr = 25.0f;
    struct { float h, hit[3]; int i; } cand[4]; int n = 0;
    ClRay ray; float pt[3], o[3], seg[3];
    for (int i = 0; i < 4; i++) {
        v3set(o, r->Pf[0] + r->F[0] * (rr + 15 * i), r->Pf[1] + 310, r->Pf[2] + r->F[2] * (rr + 15 * i));
        v3set(seg, 0, -310, 0);
        int hit = cl_ray(o, seg, 0x20, &ray, pt);
        if (hit < 0) { r->why = "raycast unavailable"; return 0; }
        BYTE *obj = 0; const char *bad = 0;
        if (hit) cl_hit_obj(&ray, &obj, &bad);
        anp_log("climb: ray down%d o=(%.1f,%.1f,%.1f) hit=%d y=%.1f h=%.1f frac=%.3f res=(%.1f,%.1f,%.1f) obj=%s(%p) node=%p",
                i, o[0], o[1], o[2], hit, hit ? pt[1] : 0.0f, hit ? pt[1] - r->Pf[1] : 0.0f, ray.frac,
                ray.hit[0], ray.hit[1], ray.hit[2], hit ? rtti_name(obj) : "-", obj, ray.node);
        if (!hit) continue;
        if (bad) { r->why = bad; return -1; }
        cand[n].h = pt[1] - r->Pf[1]; memcpy(cand[n].hit, pt, 12); cand[n].i = i; n++;
    }
    float cur = 0;
    for (int k = 0; k < n; k++) {
        if (cand[k].h < cur) continue;                       /* non-decreasing */
        float h = cur = cand[k].h; int i = cand[k].i;
        const char *clear = "miss", *head = "-", *wall = "-";
        /* clearance at h+15 from 15 cm behind (hero-only walls block) */
        v3set(o, r->Pf[0] + r->B[0] * 15, r->Pf[1] + h + 15, r->Pf[2] + r->B[2] * 15);
        v3set(seg, r->F[0] * (rr + 15 * (i + 2)), 0, r->F[2] * (rr + 15 * (i + 2)));
        int c1 = cl_ray(o, seg, 0x28, &ray, pt);
        if (c1 < 0) { r->why = "raycast unavailable"; return 0; }
        if (c1) { clear = "hit"; anp_log("climb: cand k=%d h=%.1f clear=hit at (%.1f,%.1f,%.1f) %s", k, h, pt[0], pt[1], pt[2], rtti_name(readable(ray.node + 0x60, 4) ? *(void**)(ray.node + 0x60) : 0)); continue; }
        /* head room: 180 cm straight up from the ledge point */
        v3set(o, cand[k].hit[0], cand[k].hit[1] + 1, cand[k].hit[2]); v3set(seg, 0, 180, 0);
        int c2 = cl_ray(o, seg, 0x20, &ray, pt);
        if (c2 < 0) { r->why = "raycast unavailable"; return 0; }
        if (c2) { anp_log("climb: cand k=%d h=%.1f clear=%s head=hit at y=%.1f", k, h, clear, pt[1]); r->h = h; r->why = "headroom"; return -1; }
        head = "miss";
        /* wall face at h-1 */
        v3set(o, r->Pf[0] + r->B[0] * 10, r->Pf[1] + h - 1, r->Pf[2] + r->B[2] * 10);
        v3set(seg, r->F[0] * (rr + 15 * i + 20), 0, r->F[2] * (rr + 15 * i + 20));
        int c3 = cl_ray(o, seg, 0x20, &ray, pt);
        if (c3 < 0) { r->why = "raycast unavailable"; return 0; }
        if (!c3) { anp_log("climb: cand k=%d h=%.1f clear=%s head=%s wall=miss", k, h, clear, head); continue; }
        wall = "hit";
        memcpy(r->Wp, pt, 12);
        {   float a[3] = {ray.v2[0] - ray.v0[0], ray.v2[1] - ray.v0[1], ray.v2[2] - ray.v0[2]};
            float b[3] = {ray.v1[0] - ray.v0[0], ray.v1[1] - ray.v0[1], ray.v1[2] - ray.v0[2]};
            float nx = a[1] * b[2] - a[2] * b[1], ny = a[2] * b[0] - a[0] * b[2], nz = a[0] * b[1] - a[1] * b[0];
            float nl = sqrtf(nx * nx + ny * ny + nz * nz); if (nl > 1e-6f) v3set(r->Wn, nx / nl, ny / nl, nz / nl); }
        anp_log("climb: cand k=%d h=%.1f clear=%s head=%s wall=%s W=(%.1f,%.1f,%.1f) n=(%.2f,%.2f,%.2f) dot(n,F)=%.2f",
                k, h, clear, head, wall, r->Wp[0], r->Wp[1], r->Wp[2], r->Wn[0], r->Wn[1], r->Wn[2], r->Wn[0] * r->F[0] + r->Wn[2] * r->F[2]);
        if (h <= 25) continue;
        r->h = h;
        for (int c = 0; c < 3; c++) if (h <= g_clCls[c].max) { r->cls = c; break; }
        if (r->cls < 0) { r->why = "too high"; return -1; }
        v3set(r->S, r->Wp[0] + r->B[0] * g_clCls[r->cls].off, r->Pf[1], r->Wp[2] + r->B[2] * g_clCls[r->cls].off);
        v3set(r->Ledge, r->S[0], r->S[1] + h, r->S[2]);
        r->why = "OK";
        return 1;
    }
    return 0;
}

/* root (GROUND bone) position of a clip at a frame, via 0x5a5030 */
static void *cl_anmdb(void) {
    BYTE *sys = cl_sys(); if (!sys) return 0;
    BYTE *w = *(BYTE**)(sys + 0xac);
    return readable(w + 0x14, 4) ? *(void**)(w + 0x14) : 0;
}
static void cl_root(BYTE *clip, void *db, float f, int mirror, float p[3]) {
    float q[4] = {0, 0, 0, 1}; p[0] = p[1] = p[2] = 0;
    ((cl_Root_t)0x5a5030)(clip, db, f, q, p, mirror);
}
/* Final standing pose: S + horizontal(world(g(last) - g(e5))) + (0,h,0) */
static int climb_final(ClProbe *r, int mirror) {
    void *db = cl_anmdb(); if (!db) return 0;
    int last = r->frames > 0 ? r->frames - 1 : 0;
    int e5 = r->e5 >= 0 ? r->e5 : 0, e6 = r->e6 >= 0 ? r->e6 : last;
    cl_root(r->clip, db, 0, mirror, r->g0);
    cl_root(r->clip, db, (float)e5, mirror, r->ge5);
    cl_root(r->clip, db, (float)e6, mirror, r->ge6);
    cl_root(r->clip, db, (float)last, mirror, r->gend);
    float v[3] = {r->gend[0] - r->ge5[0], r->gend[1] - r->ge5[1], r->gend[2] - r->ge5[2]};
    float rise = r->gend[1] - r->g0[1];
    if (fabsf(rise) > 0.01f && fabsf(rise) < 5.0f) {     /* clip root in metres? DM data is cm */
        anp_log("climb: root rise %.3f looks like metres -> x100", rise);
        v[0] *= 100; v[1] *= 100; v[2] *= 100;
    }
    const float *M = r->M;                              /* local -> world (0x6be1c0): x*row2 + y*row1 + z*row0 */
    float wx = v[0] * M[6] + v[1] * M[3] + v[2] * M[0], wz = v[0] * M[8] + v[1] * M[5] + v[2] * M[2];
    if (g_ccfg.fwd < 0) { wx = -wx; wz = -wz; }
    v3set(r->gv, wx, v[1], wz);
    v3set(r->Final, r->S[0] + wx, r->S[1] + r->h, r->S[2] + wz);
    return 1;
}
static int climb_clip(BYTE *P, ClProbe *r, int sprint) {
    static const char *nm[3] = {"/Movement/Climb/Up/Low", "/Movement/Climb/Up/Medium", "/Movement/Climb/Up/High"};
    WORD id = 0xFFFF;
    r->clipName = (r->cls == 0 && sprint) ? "/Movement/Climb/Up/Sprint_Low" : nm[r->cls];
    ((cl_Name_t)0x426890)(P, &id, r->clipName);
    if (id == 0xFFFF && r->cls == 0 && sprint) { r->clipName = nm[0]; ((cl_Name_t)0x426890)(P, &id, r->clipName); }
    r->id = id;
    if (id == 0xFFFF) { anp_log("climb: clip '%s' missing in this level's .ANM", r->clipName); return 0; }
    BYTE *clip = ((cl_Var_t)0x59d550)(P, id);
    if (!readable(clip, 0x68)) { anp_log("climb: clip '%s' id %u -> no variant (%p)", r->clipName, id, clip); return 0; }
    r->clip = clip;
    r->frames = *(WORD*)(clip + 2);
    BYTE *eb = readable((void*)0x1546f6c, 4) ? *(BYTE**)0x1546f6c : 0;
    if (!readable(eb + 0x10, 4)) { anp_log("climb: event table missing"); return 0; }
    r->e5 = ((cl_Event_t)0x4a75d0)(clip, 5, NULL);
    r->e6 = ((cl_Event_t)0x4a75d0)(clip, 6, NULL);
    if (r->e5 < 0 || r->e6 < 0) anp_log("climb: clip events missing (e5=%d e6=%d): using 0 / last frame", r->e5, r->e6);
    return climb_final(r, 0);
}
/* The DM clips end only ~10 (Low) / ~15 (Medium) cm past the wall face: the player stands on the lip.
   Push Final forward along F so it lies >= minin cm past the face, only when the ground there is the same
   ledge top (+-10 cm), the way there is clear at knee and chest height and there is 180 cm of head room.
   Otherwise Final stays DM-exact. The extra offset is spread over the clip by the warp like the rest. */
static void climb_min_in(ClProbe *r) {
    v3set(r->push, 0, 0, 0);
    if (g_ccfg.minIn <= 0) return;
    float past = (r->Final[0] - r->Wp[0]) * r->F[0] + (r->Final[2] - r->Wp[2]) * r->F[2];
    if (past >= (float)g_ccfg.minIn) return;
    float add = (float)g_ccfg.minIn - past, C[3], o[3], seg[3], pt[3]; ClRay ray;
    v3set(C, r->Final[0] + r->F[0] * add, r->Final[1], r->Final[2] + r->F[2] * add);
    const char *why = 0;
    v3set(o, C[0], C[1] + 60, C[2]); v3set(seg, 0, -120, 0);
    int g = cl_ray(o, seg, 0x20, &ray, pt);
    if (g != 1 || fabsf(pt[1] - r->Final[1]) > 10.0f) why = "no ledge top there";
    for (int k = 0; !why && k < 2; k++) {               /* knee and chest height, Final -> C */
        v3set(o, r->Final[0], r->Final[1] + (k ? 120 : 40), r->Final[2]); v3set(seg, r->F[0] * add, 0, r->F[2] * add);
        if (cl_ray(o, seg, 0x28, &ray, pt) != 0) why = k ? "blocked at chest" : "blocked at knee";
    }
    if (!why) {
        v3set(o, C[0], C[1] + 1, C[2]); v3set(seg, 0, 180, 0);
        if (cl_ray(o, seg, 0x20, &ray, pt) != 0) why = "head room";
    }
    if (why) { anp_log("climb: minin: kept Final %.1f cm past the face (%s)", past, why); return; }
    v3set(r->push, r->F[0] * add, 0, r->F[2] * add);
    r->Final[0] = C[0]; r->Final[2] = C[2];
    anp_log("climb: minin: Final pushed %.1f cm (%.1f -> %d cm past the face) -> (%.1f,%.1f,%.1f)", add, past, g_ccfg.minIn, C[0], C[1], C[2]);
}

/* ---------- live: the action callbacks (engine calls them, main thread) ---------- */
static void climb_fault_disable(const char *where) {
    g_climbDead = 1;
    anp_log("climb: DISABLED for this session (fault in %s) - restart the game before testing again", where);
}
static int climb_start_body(void *arg) {
    BYTE *self = (BYTE*)arg, *pl = *(BYTE**)(self + 8);
    if (!g_cl.active || g_cl.act != self || pl != g_cl.P) { anp_log("climb: START on an unknown record"); return 0; }
    if (*(void**)(pl + 0x2810)) ((cl_Void_t)0x5fcb80)(pl);     /* stock prep (derefs pl+0x2810) */
    *(int*)(pl + 0x2d60) = 0;
    ((cl_Void_t)CL_VF(pl, 0x560))(pl); g_cl.did560 = 1;          /* ghost collision; End's vt+0x564 undoes it */
    BYTE *anim = ((cl_Play_t)CL_VF(pl, 0x204))(pl, g_cl.clip, 1);
    if (!anim || !readable(anim, 0x20)) { anp_log("climb: START PlayAnim failed (%p)", anim); g_cl.endReason = "playanim"; return 0; }
    *(BYTE**)(self + 0xc) = anim;
    g_cl.anim = anim; g_cl.anim0 = *(DWORD*)anim; g_cl.animId = *(int*)(anim + 0x18);
    int mirror = (*(DWORD*)(anim + 0x14) >> 8) & 1;
    float cur = *(float*)(anim + 4); g_cl.from = *(float*)(anim + 8); g_cl.to = *(float*)(anim + 0xc);
    if (mirror) {      /* recompute the end pose with the mirrored root */
        ClProbe r; memset(&r, 0, sizeof r);
        memcpy(r.M, g_cl.M, sizeof r.M); memcpy(r.S, g_cl.S, 12); r.h = g_cl.h;
        r.clip = g_cl.clip; r.frames = g_cl.frames; r.e5 = g_cl.e5; r.e6 = g_cl.e6;
        if (climb_final(&r, 1)) {
            v3madd(g_cl.Final, r.Final, g_cl.push, 1.0f); memcpy(g_cl.gv, r.gv, 12);      /* keep the minin push */
        }
    }
    cl_Warp_t warp = (cl_Warp_t)CL_VF(pl, 0x208);
    int ok;
    if (!g_ccfg.warpDm) { ok = warp(pl, g_cl.M, g_cl.Final, g_cl.to - g_cl.from - 1.0f); g_cl.phase = 3; }
    else if ((float)g_cl.e5 > cur) { ok = warp(pl, g_cl.M, g_cl.S, (float)g_cl.e5 - cur); g_cl.phase = 1; }
    else { ok = warp(pl, g_cl.M, g_cl.Ledge, (float)g_cl.e6 - cur); g_cl.phase = 2; }
    if (!ok) { anp_log("climb: START warp failed (no root channel?)"); g_cl.endReason = "warp"; return 0; }
    if (g_ccfg.cam) {
        void *cam = ((cl_Get_t)0x8fde70)(pl);
        if (readable(cam, 0xca0)) ((cl_Cam_t)0x798d00)(cam, 67.0f, 40.0f, 0.5f);
    }
    anp_log("climb: START act=%p anim=%p (chan0=%08lx clip=%p same=%d id=%d mirror=%d) cur=%.1f from=%.1f to=%.1f e5=%d e6=%d warp=%s ok=%d Final=(%.1f,%.1f,%.1f)",
            self, anim, g_cl.anim0, g_cl.clip, g_cl.anim0 == (DWORD)g_cl.clip, g_cl.animId, mirror, cur, g_cl.from, g_cl.to,
            g_cl.e5, g_cl.e6, g_ccfg.warpDm ? "dm" : "end", ok, g_cl.Final[0], g_cl.Final[1], g_cl.Final[2]);
    return 1;
}
static unsigned char __attribute__((thiscall, force_align_arg_pointer)) ClimbStart(BYTE *self) {
    int r = climb_guarded("climb Start", climb_start_body, self);
    if (r < 0) { climb_fault_disable("Start"); g_cl.endReason = "fault"; return 0; }
    return r == 1;
}

static int climb_update_body(void *arg) {
    BYTE *self = (BYTE*)arg;
    int r = ((cl_Char_t)0x5b1e40)(self) & 0xff;                  /* stock: camera follow (no phantom) */
    if (!g_cl.active || g_cl.act != self) return r;
    float cur = cl_anim_cur();
    BYTE *pl = g_cl.P;
    if (cur >= (float)g_cl.e5 && !g_cl.reached) { g_cl.reached = 1; memcpy(self + 0x68, g_cl.Final, 12); }
    if (g_ccfg.warpDm && cur >= 0) {
        cl_Warp_t warp = (cl_Warp_t)CL_VF(pl, 0x208);
        if (g_cl.phase == 1 && cur >= (float)g_cl.e5) { warp(pl, g_cl.M, g_cl.Ledge, (float)g_cl.e6 - cur); g_cl.phase = 2; }
        else if (g_cl.phase == 2 && cur >= (float)g_cl.e6) { warp(pl, g_cl.M, g_cl.Final, g_cl.to - cur - 1.0f); g_cl.phase = 3; }
    }
    if (g_ccfg.trace && (g_cl.traceN++ % 3) == 0 && g_cl.traceLines < 60) {
        float M[9], f[3] = {0, 0, 0}; cl_pose(pl, M, f);
        BYTE *mov = *(BYTE**)(pl + 0x6b4);
        g_cl.traceLines++;
        anp_log("climb: trace cur=%.1f feet=(%.1f,%.1f,%.1f) mov=%d phase=%d", cur, f[0], f[1], f[2],
                readable(mov + 0x44, 4) ? *(int*)(mov + 0x44) : -1, g_cl.phase);
    }
    int T = cl_curT();
    if (cur < 0) { g_cl.endReason = "channel lost"; return 0; }
    if (T - g_cl.startT > g_cl.frames * 1024 / 25 + 1024) { g_cl.endReason = "timeout"; return 0; }
    if (cur >= g_cl.to - 0.5f) { g_cl.endReason = "clip end"; return 0; }
    return r;
}
static unsigned char __attribute__((thiscall, force_align_arg_pointer)) ClimbUpdate(BYTE *self) {
    int r = climb_guarded("climb Update", climb_update_body, self);
    if (r < 0) { climb_fault_disable("Update"); g_cl.endReason = "fault"; return 0; }
    return r != 0;
}

typedef struct { BYTE *self; int id; } ClAnimEndArg;
static int climb_animend_body(void *arg) {
    ClAnimEndArg *a = (ClAnimEndArg*)arg;
    if (!g_cl.active || g_cl.act != a->self) return 1;
    if (cl_anim_cur() >= 0 && a->id == g_cl.animId) { g_cl.endReason = "animend"; return 1; }
    if (g_cl.animEndLogs++ < 5) anp_log("climb: foreign animend id=%d (ours %d) - ignored", a->id, g_cl.animId);
    return 0;
}
static unsigned char __attribute__((thiscall, force_align_arg_pointer)) ClimbAnimEnd(BYTE *self, int id) {
    ClAnimEndArg a = {self, id};
    int r = climb_guarded("climb AnimEnd", climb_animend_body, &a);
    if (r < 0) { climb_fault_disable("AnimEnd"); g_cl.endReason = "fault"; return 1; }
    return r != 0;
}

static int climb_end_body(void *arg) {
    BYTE *self = (BYTE*)arg, *pl = *(BYTE**)(self + 8);
    int mine = g_cl.active && g_cl.act == self;
    float cur = mine ? cl_anim_cur() : -1.0f;
    int reached = mine && (g_cl.reached || (cur >= 0 && cur >= (float)g_cl.e5));
    if (!reached) {                       /* R2: stock End teleports to +0x38/+0x68 -> make that the current pose */
        float M[9], f[3];
        if (cl_pose(pl, M, f)) { memcpy(self + 0x38, M, sizeof M); memcpy(self + 0x68, f, 12); }
    }
    if (!mine || g_cl.did560) ((cl_Void_t)0x82f780)(self);          /* stock End: undoes vt+0x560, stance, teleport */
    else ((cl_Void_t)0x4af5b0)(pl);
    float f[3] = {0, 0, 0}, M[9], dist = -1; int snapped = 0;
    /* Safety snap only when OUR climb completed (animend / clip end). Engine aborts (death, PlayMiniAnim, ...)
       arrive with endReason == NULL and keep the engine's own outcome. Unforced (a4=0) like stock End 0x82f806:
       a forced call would write the 0.8 s teleport cooldown [pl+0x29e0] and swallow later unforced teleports. */
    int completed = g_cl.endReason && (!strcmp(g_cl.endReason, "animend") || !strcmp(g_cl.endReason, "clip end"));
    if (mine && reached && cl_pose(pl, M, f)) {
        dist = v3dist(f, g_cl.Final);
        if (g_ccfg.snap && completed && dist > 25.0f) { ((cl_Tele_t)0x82cc40)(pl, g_cl.M, g_cl.Final, 0, 0, 0); snapped = 1; }
    }
    anp_log("climb: END reason=%s cur=%.1f reached=%d feet=(%.1f,%.1f,%.1f) Final=(%.1f,%.1f,%.1f) dist=%.1f snapped=%d%s",
            g_cl.endReason ? g_cl.endReason : "?", cur, reached, f[0], f[1], f[2], g_cl.Final[0], g_cl.Final[1], g_cl.Final[2],
            dist, snapped, mine ? "" : " (unknown record)");
    if (mine) memset(&g_cl, 0, sizeof g_cl);
    return 0;
}
static void __attribute__((thiscall, force_align_arg_pointer)) ClimbEnd(BYTE *self) {
    if (climb_guarded("climb End", climb_end_body, self) < 0) { climb_fault_disable("End"); memset(&g_cl, 0, sizeof g_cl); }
}

/* ---------- live: start a climb from the tick ---------- */
static void climb_go_live(BYTE *P, const ClProbe *r, int T) {
    if (g_ccfg.vehSnap) {
        ((cl_Tele_t)0x82cc40)(P, r->M, r->Final, 1, 1, 0);
        anp_log("climb: SNAP (vehicle=snap) -> (%.1f,%.1f,%.1f)", r->Final[0], r->Final[1], r->Final[2]);
        return;
    }
    if (!g_vtbuf[1]) {
        g_vtbuf[0] = *(DWORD*)(CL_VAULT_VT - 4);
        memcpy(&g_vtbuf[1], (void*)CL_VAULT_VT, 48);
        g_vtbuf[1 + 2] = (DWORD)ClimbStart;
        g_vtbuf[1 + 4] = (DWORD)ClimbUpdate;
        g_vtbuf[1 + 5] = (DWORD)ClimbEnd;
        g_vtbuf[1 + 10] = (DWORD)ClimbAnimEnd;
    }
    BYTE *act = ((cl_Create_t)CL_VF(P, 0x384))(P, 0x2B);
    if (!readable(act, 0x80)) { anp_log("climb: CreateAction(0x2B) failed (%p)", act); return; }
    if (*(DWORD*)act != CL_VAULT_VT || *(BYTE**)(act + 8) != P) {
        anp_log("climb: CreateAction(0x2B) returned an unexpected object %p vt=%08lx owner=%p - not used", act, *(DWORD*)act, *(void**)(act + 8));
        return;
    }
    *(DWORD**)act = &g_vtbuf[1];
    memcpy(act + 0x14, r->M, 36); memcpy(act + 0x5c, r->Pf, 12);
    memcpy(act + 0x38, r->M, 36); memcpy(act + 0x68, r->Pf, 12);  /* current pose until e5 (R2) */
    *(BYTE**)(act + 0x10) = r->clip; *(void**)(act + 0xc) = 0;
    act[0x74] = act[0x75] = 0; *(int*)(act + 0x78) = 0; *(BYTE**)(act + 0x7c) = g_edge;
    memset(&g_cl, 0, sizeof g_cl);
    g_cl.active = 1; g_cl.act = act; g_cl.P = P; g_cl.clip = r->clip; g_cl.e5 = r->e5 >= 0 ? r->e5 : 0;
    g_cl.e6 = r->e6 >= 0 ? r->e6 : (r->frames > 0 ? r->frames - 1 : 0); g_cl.frames = r->frames; g_cl.h = r->h; g_cl.startT = T;
    memcpy(g_cl.S, r->S, 12); memcpy(g_cl.Ledge, r->Ledge, 12); memcpy(g_cl.Final, r->Final, 12);
    memcpy(g_cl.M, r->M, 36); memcpy(g_cl.gv, r->gv, 12); memcpy(g_cl.push, r->push, 12);
    ((cl_Void_t)CL_VF(P, 0x374))(P);                 /* Abort (no-op when idle; 0x869e10 int3s if an action is current) */
    ((cl_StartAct_t)CL_VF(P, 0x370))(P, act);        /* ClimbStart runs in here */
    if (cl_disp_cur(P) != act) {
        anp_log("climb: start failed (reason %s) - action finished at once", g_cl.endReason ? g_cl.endReason : "?");
        if (g_cl.act == act) memset(&g_cl, 0, sizeof g_cl);
    }
}

/* ---------- test teleport (unattended climb tests, scripts/smoke_climb.py) ----------
   <DD>\ANP_tp.txt = "x y z yawDeg [full]": feet in world cm, forward F = (sin yaw, 0, cos yaw) (0 = +z, 90 = +x),
   the probe's own facing convention (F = -row0 * fwd). Consumed once (renamed to ANP_tp.done) on the main thread:
   0x82cc40(pl, M, P, reset=1, force=1, 0), as vehicle=snap does; force also re-aims the camera behind the player
   (0x82cd87 -> camera [pl+0xbd4] 0x8de300(1)). "full" uses the gamedata teleport 0x8f3fa0(gd, P, M, 0) instead
   (exits cover, movement back to Stand). Logs 'climb: tp: ...' with the pose read back at once and ~0.7 s later. */
typedef void (__attribute__((thiscall)) *cl_GdTele_t)(void *gd, const float *P, const float *M, int crew);   /* 0x8f3fa0, ret 0xc */
static DWORD g_tpPoll, g_tpSettle; static int g_tpDead; static float g_tpWant[4];
static float cl_yaw(const float *M) {                /* yaw in degrees (0..360) of the probe's forward F = -row0 * fwd */
    float fx = -M[0] * g_ccfg.fwd, fz = -M[2] * g_ccfg.fwd;
    if (fx * fx + fz * fz < 1e-6f) return -1.0f;
    float y = atan2f(fx, fz) * 57.2957795f;
    return y < 0 ? y + 360.0f : y;
}
static void cl_yaw_matrix(float yawDeg, float *M) { /* inverse of cl_yaw, in 0x857110's row layout: R(0,0,1), R(0,1,0), R(1,0,0) */
    float a = yawDeg * 0.0174532925f, ax = -sinf(a) * g_ccfg.fwd, az = -cosf(a) * g_ccfg.fwd;   /* row0 = -F * fwd */
    M[0] = ax; M[1] = 0; M[2] = az;
    M[3] = 0;  M[4] = 1; M[5] = 0;
    M[6] = az; M[7] = 0; M[8] = -ax;                 /* row2 = R(1,0,0) = (row0.z, 0, -row0.x) */
}
static int cl_movid(BYTE *P) { BYTE *mov = *(BYTE**)(P + 0x6b4); return readable(mov + 0x44, 4) ? *(int*)(mov + 0x44) : -1; }
static int climb_tp_body(void *arg) {
    BYTE *P = (BYTE*)arg;
    DWORD now = GetTickCount();
    if (g_tpSettle && now - g_tpSettle >= 700) {
        g_tpSettle = 0;
        float M[9], f[3] = {0, 0, 0};
        if (cl_pose(P, M, f))
            anp_log("climb: tp: settled feet=(%.1f,%.1f,%.1f) yaw=%.1f off=%.1f dyaw=%.1f mov=%d", f[0], f[1], f[2], cl_yaw(M),
                    v3dist(f, g_tpWant), fmodf(cl_yaw(M) - g_tpWant[3] + 540.0f, 360.0f) - 180.0f, cl_movid(P));
    }
    if (now - g_tpPoll < 250) return 0;
    g_tpPoll = now;
    char fn[MAX_PATH], dn[MAX_PATH];
    _snprintf(fn, sizeof fn, "%s\\ANP_tp.txt", g_dir); _snprintf(dn, sizeof dn, "%s\\ANP_tp.done", g_dir);
    if (GetFileAttributesA(fn) == INVALID_FILE_ATTRIBUTES) return 0;
    char buf[256] = ""; FILE *fp = fopen(fn, "r");
    if (!fp) return 0;                                /* still being written: next poll */
    size_t n = fread(buf, 1, sizeof buf - 1, fp); buf[n] = 0; fclose(fp);
    if (!n) return 0;
    if (!MoveFileExA(fn, dn, MOVEFILE_REPLACE_EXISTING) && !DeleteFileA(fn)) {
        g_tpDead = 1;
        anp_log("climb: tp: cannot rename or delete ANP_tp.txt (error %lu) - tp off for this session", GetLastError());
        return 0;
    }
    float x, y, z, yaw; char mode[16] = "";
    if (sscanf(buf, "%f %f %f %f %15s", &x, &y, &z, &yaw, mode) < 4) {
        anp_log("climb: tp: bad ANP_tp.txt '%.60s' (want 'x y z yawDeg [full]')", buf);
        return 0;
    }
    int full = !_stricmp(mode, "full");
    float M[9], Pw[3] = {x, y, z}, M0[9], f0[3] = {0, 0, 0}, M1[9], f1[3] = {0, 0, 0};
    cl_pose(P, M0, f0);
    int mov0 = cl_movid(P);
    cl_yaw_matrix(yaw, M);
    if (full) {
        BYTE *gd = *(BYTE**)0xdd265c;
        ((cl_GdTele_t)0x8f3fa0)(gd, Pw, M, 0);
    } else ((cl_Tele_t)0x82cc40)(P, M, Pw, 1, 1, 0);
    cl_pose(P, M1, f1);
    g_tpWant[0] = x; g_tpWant[1] = y; g_tpWant[2] = z; g_tpWant[3] = yaw;
    anp_log("climb: tp: %s want=(%.1f,%.1f,%.1f) yaw=%.1f from=(%.1f,%.1f,%.1f) yaw=%.1f mov=%d -> feet=(%.1f,%.1f,%.1f) yaw=%.1f off=%.1f mov=%d",
            full ? "full(0x8f3fa0)" : "0x82cc40", x, y, z, yaw, f0[0], f0[1], f0[2], cl_yaw(M0), mov0,
            f1[0], f1[1], f1[2], cl_yaw(M1), v3dist(f1, Pw), cl_movid(P));
    g_tpSettle = now ? now : 1;
    return 0;
}

/* ---------- per-frame tick ---------- */
static int g_clLastT = -0x7fffffff, g_clPrevE, g_clArmed;
static DWORD g_clLastPress, g_clLastTrace, g_clLastPos;
static const char *climb_precond(BYTE *P, int T) {
    if (g_ccfg.mode == CL_OFF) return "mode off";
    if (g_climbDead) return "disabled after fault";
    if (g_cl.active) return "climbing";
    if (*(BYTE**)(P + 0x6b0) != P + 0xdb0) return "movement table (MiniScene?)";
    BYTE *mov = *(BYTE**)(P + 0x6b4);
    if (!readable(mov + 0x44, 4)) return "no movement";
    int id = *(int*)(mov + 0x44);
    if (id != 2 && id != 3) return "movement not Stand/BaseMove";
    if (((cl_Int_t)CL_VF(P, 0x388))(P) != 0) return "action running";
    if (T - *(int*)(P + 0x2c48) < 512) return "< 0.5 s since last action";
    if (P[0xd29]) return "use action running";
    if (*(DWORD*)(P + 0xed0) & 0x80) return "input blocked";
    if (*(DWORD*)(P + 0xd50) || *(DWORD*)(P + 0xd44)) return "seat/carrier";
    if (!(P[0x2720] & 2)) return "not local human";
    if (*(DWORD*)(P + 0x2d60) & 0x10) return "stock vault available";
    if (!*(void**)(P + 0x2810)) return "P+0x2810 null";
    void *cw = readable((void*)0x138c868, 4) ? *(void**)0x138c868 : 0;
    if (!readable(cw, 4) || *(DWORD*)cw != CL_COLLW_VT) return "no collision world";
    BYTE *sys = cl_sys(); BYTE *db = sys ? *(BYTE**)(sys + 0xac) : 0;
    BYTE *ph = readable(db + 0x52cc, 4) ? *(BYTE**)(db + 0x52cc) : 0;
    if (!readable(ph + 0x14dc, 4) || !*(void**)(ph + 0x14dc) || *(int*)0xcd9c60 != 1) return "no Havok world";
    return 0;
}
static int climb_tick(void *unused) {
    (void)unused;
    climb_cfg_poll();
    BYTE *gd = readable((void*)0xdd265c, 4) ? *(BYTE**)0xdd265c : 0, *sys = cl_sys();
    if (!sys || !readable(gd + 0x828, 0x74)) return 0;
    signed char pi = *(signed char*)(gd + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gd + 0x828 + 4 * pi);
    if (!readable(P, 0x2e00) || *(DWORD*)P != CL_PLAYER_VT) return 0;
    int T = *(int*)(sys + 0x48);
    if (T == g_clLastT) return 0;                     /* paused */
    g_clLastT = T;
    if (g_ccfg.trace && GetTickCount() - g_clLastPos >= 1000) {     /* 1 Hz position line (any mode) */
        g_clLastPos = GetTickCount();
        float M[9], f[3] = {0, 0, 0};
        if (cl_pose(P, M, f)) anp_log("climb: pos: %.1f %.1f %.1f %.1f mov=%d T=%d%s", f[0], f[1], f[2], cl_yaw(M), cl_movid(P), T, g_cl.active ? " climbing" : "");
    }
    if (!g_tpDead && !g_cl.active && climb_guarded("climb tp", climb_tp_body, P) < 0) {
        g_tpDead = 1;                                 /* the tick itself goes on; only tp is switched off */
        anp_log("climb: tp: FAULT - tp off for this session (restart the game before trusting further results)");
    }
    if (g_cl.active) {
        if (g_cl.P != P || cl_disp_cur(P) != g_cl.act) { anp_log("climb: record dropped (action gone)"); memset(&g_cl, 0, sizeof g_cl); }
        return 0;
    }
    HWND fw = GetForegroundWindow(); DWORD pid = 0;
    if (fw) GetWindowThreadProcessId(fw, &pid);
    int fg = fw && pid == GetCurrentProcessId();
    int E = fg && (GetAsyncKeyState('E') & 0x8000);
    int Wk = fg && ((GetAsyncKeyState('W') & 0x8000) || *(float*)(P + 0xb94) > 0.5f);
    int sprint = P[0x850] || (fg && (GetAsyncKeyState(VK_LSHIFT) & 0x8000));
    float *V = (float*)(P + 0x5ec), S = *(float*)(P + 0x5f8), vxz = sqrtf(V[0] * V[0] + V[2] * V[2]);
    int blocked = vxz >= 300.0f && S < 0.75f * vxz;
    int edge = E && !g_clPrevE; g_clPrevE = E;
    if (g_ccfg.mode == CL_OFF) { g_clArmed = 0; return 0; }
    DWORD now = GetTickCount();
    if (g_ccfg.trace && now - g_clLastTrace >= 1000) {
        g_clLastTrace = now;
        float M[9], f[3] = {0, 0, 0}; cl_pose(P, M, f);
        float L = sqrtf(M[0] * M[0] + M[2] * M[2]), Fx = L > 1e-3f ? -M[0] / L * g_ccfg.fwd : 0, Fz = L > 1e-3f ? -M[2] / L * g_ccfg.fwd : 0;
        BYTE *mov = *(BYTE**)(P + 0x6b4);
        DWORD wtid = fw ? GetWindowThreadProcessId(fw, NULL) : 0;
        anp_log("climb: state T=%d feet=(%.1f,%.1f,%.1f) F=(%.2f,%.2f) mov=%d V=(%.1f,%.1f,%.1f)|S=%.1f dot(F,V)=%.2f blocked=%d W=%d E=%d sprint=%d fg=%d wndtid==main %d fwdaxis=%.2f",
                T, f[0], f[1], f[2], Fx, Fz, readable(mov + 0x44, 4) ? *(int*)(mov + 0x44) : -1, V[0], V[1], V[2], S,
                vxz > 1 ? (Fx * V[0] + Fz * V[2]) / vxz : 0.0f, blocked, Wk, E, sprint, fg, wtid == g_clMainTid, *(float*)(P + 0xb94));
    }
    if (g_clArmed) {                                  /* DM: use seen on call N, probe on call N+1 */
        g_clArmed = 0;
        const char *why = climb_precond(P, T);
        if (!why && !Wk) why = "W not held";
        if (!why && g_ccfg.needblock && !blocked) why = "not blocked";
        float M[9], f[3] = {0, 0, 0}; cl_pose(P, M, f);
        float L = sqrtf(M[0] * M[0] + M[2] * M[2]);
        BYTE *mov = *(BYTE**)(P + 0x6b4);
        anp_log("climb: press T=%d P=(%.1f,%.1f,%.1f) F=(%.2f,%.2f) mov=%d act=%d dtLast=%.2fs V=(%.1f,%.1f,%.1f)|S=%.1f blocked=%d sprint=%d W=%d%s%s%s",
                T, f[0], f[1], f[2], L > 1e-3f ? -M[0] / L * g_ccfg.fwd : 0.0f, L > 1e-3f ? -M[2] / L * g_ccfg.fwd : 0.0f,
                readable(mov + 0x44, 4) ? *(int*)(mov + 0x44) : -1, ((cl_Int_t)CL_VF(P, 0x388))(P), (T - *(int*)(P + 0x2c48)) / 1024.0f,
                V[0], V[1], V[2], S, blocked, sprint, Wk, why ? " [ignored: " : "", why ? why : "", why ? "]" : "");
        if (why) return 0;
        ClProbe r;
        int res = climb_probe(P, &r);
        if (res <= 0) { anp_log("climb: RESULT %s%s h=%.1f", res < 0 ? "abort:" : "none: ", r.why, r.h); return 0; }
        int clipOk = climb_clip(P, &r, sprint);
        if (clipOk) climb_min_in(&r);
        anp_log("climb: RESULT OK class=%s h=%.1f S=(%.1f,%.1f,%.1f) Ledge=(%.1f,%.1f,%.1f) Final=(%.1f,%.1f,%.1f) clip='%s' id=%d clip=%p frames=%d e5=%d e6=%d "
                "g_end-g_e5=(%.1f,%.1f,%.1f) g0=(%.1f,%.1f,%.1f) ge5=(%.1f,%.1f,%.1f) ge6=(%.1f,%.1f,%.1f) gend=(%.1f,%.1f,%.1f) ground18=(%.1f,%.1f,%.1f)",
                g_clCls[r.cls].name, r.h, r.S[0], r.S[1], r.S[2], r.Ledge[0], r.Ledge[1], r.Ledge[2], r.Final[0], r.Final[1], r.Final[2],
                r.clipName ? r.clipName : "-", r.id == 0xFFFF ? -1 : (int)r.id, r.clip, r.frames, r.e5, r.e6, r.gv[0], r.gv[1], r.gv[2],
                r.g0[0], r.g0[1], r.g0[2], r.ge5[0], r.ge5[1], r.ge5[2], r.ge6[0], r.ge6[1], r.ge6[2], r.gend[0], r.gend[1], r.gend[2],
                readable(r.clip + 0x18, 12) ? ((float*)(r.clip + 0x18))[0] : 0.0f, readable(r.clip + 0x18, 12) ? ((float*)(r.clip + 0x18))[1] : 0.0f,
                readable(r.clip + 0x18, 12) ? ((float*)(r.clip + 0x18))[2] : 0.0f);
        if (!clipOk) return 0;
        if (g_ccfg.mode == CL_LIVE) climb_go_live(P, &r, T);
        return 0;
    }
    if (edge) {
        if (now - g_clLastPress < 300) return 0;
        g_clLastPress = now;
        const char *why = climb_precond(P, T);
        if (why) {
            if (strcmp(why, "stock vault available") && strcmp(why, "action running") && strcmp(why, "use action running"))
                anp_log("climb: press ignored (%s)", why);
            else anp_log("climb: press ignored (%s) - left to Dog Days", why);
            return 0;
        }
        g_clArmed = 1;
    }
    return 0;
}

/* ---------- frame hook: kl2 IAT slot steam_api!SteamAPI_RunCallbacks ---------- */
void *g_realRCB;                                     /* non-static: used from asm */
static DWORD g_clFrames, g_clT0; static int g_clRateLogged;
static int climb_cleanup_body(void *unused) {       /* after a tick fault: abort our action (-> our End restores collision) */
    (void)unused;
    BYTE *P = g_cl.P;
    if (readable(P, 0x200) && *(DWORD*)P == CL_PLAYER_VT && cl_disp_cur(P) == g_cl.act) {
        ((cl_Void_t)CL_VF(P, 0x374))(P);
        anp_log("climb: cleanup: action aborted");
    }
    if (g_cl.active) memset(&g_cl, 0, sizeof g_cl);
    return 0;
}
static void climb_frame(void) {
    if (!g_clMainTid) {
        g_clMainTid = GetCurrentThreadId(); g_clT0 = GetTickCount();
        anp_log("climb: frame hook live tid=%lu", g_clMainTid);
    }
    g_clFrames++;
    if (!g_clRateLogged && GetTickCount() - g_clT0 >= 10000) {
        g_clRateLogged = 1;
        anp_log("climb: %.1f ticks/s over the first 10 s", g_clFrames * 1000.0 / (GetTickCount() - g_clT0));
    }
    if (g_climbDead || GetCurrentThreadId() != g_clMainTid) return;
    if (climb_guarded("climb tick", climb_tick, 0) < 0) {
        climb_fault_disable("tick");
        if (g_cl.active && g_cl.P && climb_guarded("climb cleanup", climb_cleanup_body, 0) < 0) memset(&g_cl, 0, sizeof g_cl);
    }
}
__attribute__((used, force_align_arg_pointer)) void __cdecl anp_rcb_pre(DWORD ra) {
    if (ra == CL_RCB_RA) { climb_frame(); squad_frame(); }   /* squad.inc: crew orders */
}
__attribute__((naked)) void anp_rcb_stub(void) {
    __asm__ volatile(
        "pushal\n\t"
        "pushfl\n\t"
        "pushl 36(%esp)\n\t"            /* kl2's return address */
        "call _anp_rcb_pre\n\t"
        "addl $4,%esp\n\t"
        "popfl\n\t"
        "popal\n\t"
        "jmp *_g_realRCB\n\t");
}
static void install_climb(void) {
    hook_iat(GetModuleHandleA(NULL), "steam_api.dll", "SteamAPI_RunCallbacks", anp_rcb_stub, &g_realRCB);
    anp_log("ANP loader: climb frame hook (steam_api!SteamAPI_RunCallbacks) %s", g_realRCB ? "ok" : "MISSING");
}
