/* ==================== rappel.inc: Dead Men rappelling in Dog Days ====================
   Included by anp_loader.c after climb.inc and squad.inc (uses anp_log, readable, g_dir, g_cscene/g_cmpCs (campaign.inc)
   and climb.inc's climb_guarded, cl_pose, cl_ray, cl_sys, cl_curT, cl_disp_cur, cl_anim helpers, cl_yaw_matrix, CL_VF and
   typedefs). Ticked once per gameplay frame from climb.inc's frame hook: anp_rcb_pre() -> rappel_frame().

   What the exes have (static RE, 12 Oct; tools/rappel.py has the converter side and the same notes):
   * kl2.exe still contains Dead Men's whole rappel system, byte-for-byte the same logic as kaneandlynch.exe:
       ZRappellingBox (vt 0xbc23bc; props: enabled +0x30, facing handle +0x34, 8 containers +0x38..+0x54, 2 bools) - the
         'AITrigger' message enables it (0x87da50); Init registers {geom handle, facing 3x3, box} in the rappel-point list
         gameMgr+0x15b8 (0x6bc690, max 10) and, when enabled, a HUD use action 0x18 (0x452a60).
       ZFFPlayerMovementRappel (vt 0xbb5ebc, 43 slots) = player movement 0x10 at ZFFPlayer+0xdf0 (built by 0x51d240 for every
         player): slot 14 TryActivate 0x673a20 (point lookup 0x4c47b0: geom visible + box enabled + player inside the box
         geom; prompt 2 via 0x4c06c0; enter callback 0x495c80; use pressed (0x50a8f0(2)) -> 1), slot 15 Activate 0x6db3b0
         (begin callback 0x7a7980, Start clip, warp onto the facing), slot 17 Update 0x825290 (state ZFFPlayer+0x25c0:
         0 start, 1 wait on wall, 2 jump loop, 3 jump, 4 jump end, 5 done -> end callback 0x811c20), slot 13 Deactivate
         0x6165f0, slot 20 clip ids 0x77ac70 (+0x1fe4 Start, +0x1fe6 Jump_Start, +0x1fe8 Wait_On_Wall, +0x1fea Jump_Loop,
         +0x1fec Jump_End). Movement fields: +0x1f64 active, +0x1f68 point entry (player inside an enabled box),
         +0x1f6c prompt shown, +0x1f6d started; +0x38 = the player.
   * Why it does nothing / breaks in the ANP levels built before tools/rappel.py: the player's animation DB (Kane) has no
     /Movement/Rappelling/... (the donor F03 has none at all; only Dead Men's merged clips bring them), so 0x59d550 returns NULL for the Start clip and
     Activate hands NULL to PlayAnim and 0x5a5030 (inferred: crash or a frozen player the moment use is pressed).
     And kl2's box callbacks pick the first four containers only for gameMgr player slot ONE (co-op player two), so the
     single player gets Dead Men's (empty) co-op half. tools/rappel.py fixes both in the level files.

   Modes: <DD>\ANP_rappel.txt, any bare word (no file = native: the levels carry the clips and callbacks since
   tools/rappel.py, and native refuses a start without clips and falls back to Stand after a fault), polled once a second:
     off     nothing
     dry     read only: logs the rappel points of the level (once), and every change of the native rappel state
             (in box / prompt / started / active / sub-state / movement id); the native move runs untouched
     native  dry + DD's own move behind guards: the player's rappel movement gets a loader-owned vtable copy (vptr swap on
             the heap object; slots 14 TryActivate, 15 Activate, 17 Update wrapped). A use press is refused (logged) when
             the player's DB lacks the rappel clips (no NULL-clip start); a fault inside the native code is caught
             (rappel: FAULT), native rappel is switched off for the session and the player is put back to Stand
             ('full' teleport 0x8f3fa0 to where he pressed use)
     live    the loader's own descent at every rappel point (native start always refused): a ZFFActionVaultOver (type 0x2B)
             with a loader-owned vtable copy, as climb.inc, plays a rappel clip and warps the player down the rope line
             to the ground; the box's begin / end callbacks (0x7a7980 / 0x811c20) are fired so the level goes on
     auto    native when the player's DB has the clips and native has not faulted, else live
   Options (key=value after the mode): trace=0|1 (1 Hz position + per-frame descent trace), speed=300 (cm/s, live descent),
     minh=150 (cm, smallest drop), maxedge=200 (cm, how far from the player the edge may be), landoff=40 (cm, landing point
     past the rope line), cb=1 (live: fire begin/end callbacks), snap=1 (live: if no usable clip, teleport to the ground),
     efallback=1 (live/auto: E inside a box whose native prompt is not shown starts the loader descent)
   Test command: <DD>\ANP_rappel_cmd.txt "enable all" | "enable N" sets a registered point's box enabled (see rp_cmd_poll);
   with climb.inc's ANP_tp.txt it reaches a rappel point without the level's gate chain.
   Only in ANP levels (campaign scene id "M<digit>..."). Every engine call runs under climb_guarded(); a fault logs
   "climb: FAULT ... in rappel ..." (shared VEH guard), then "rappel: DISABLED ..." and the module (or the native path) is
   switched off for the session. No kl2 code byte is changed: vptr swap on a heap object to a loader-owned copy, heap writes
   to the movement's own state bytes, calls into kl2.
   Log lines start with "rappel:". */

#define RP_MOV_VT    0xbb5ebc   /* ZFFPlayerMovementRappel */
#define RP_MOV_SLOTS 43
#define RP_BOX_VT    0xbc23bc   /* ZRappellingBox */
#define RP_MOV_OFF   0xdf0      /* ZFFPlayer: movement table +0xdb0, entry 0x10 */
#define RP_F_TRY     0x673a20   /* movement slot 14 */
#define RP_F_ACT     0x6db3b0   /* movement slot 15 */
#define RP_F_UPD     0x825290   /* movement slot 17 */
#define RP_F_BEGIN   0x7a7980   /* box: begin callback (thiscall box, player) */
#define RP_F_END     0x811c20   /* box: end callback */
#define RP_F_HANDLE  0x8ccde0   /* handle -> object (cdecl) */
#define RP_F_GDTELE  0x8f3fa0   /* gamedata 'full' teleport (gd, P, M, crew): movement back to Stand */
#define RP_LIST_OFF  0x15b8     /* gameMgr: rappel-point list {total, n, entry[10] (0x2c)} */

/* ---------- config ---------- */
enum { RP_OFF, RP_DRY, RP_NATIVE, RP_LIVE, RP_AUTO };
static const char *RP_MODE[] = {"off", "dry", "native", "live", "auto"};
typedef struct { int mode, trace, cb, snap, efallback; float speed, minH, maxEdge, landOff; int land, camdiag, camfix; } RpCfg;
#define RP_CFG_DEFAULT {RP_NATIVE, 0, 1, 1, 1, 300.0f, 150.0f, 200.0f, 40.0f, 4, 1, 0}   /* land=auto, camdiag=1, camfix=off (15 Oct) */
/* land= (native landing pose, 15 Oct camera): off = stock; turn = flip the player 180 deg in place (stock leaves him facing
   the wall while the camera keeps the outward descent look, so his face fills the corner of the screen); cam = keep the
   facing, re-aim the camera behind him (0x82cc40 force=1 -> 0x8de300(1)); turncam = both; auto (default) = ray from chest
   height (130 cm) 150 cm along his facing (mask 0x28, climb.inc helper, guarded): hit -> turncam (M02 wall), miss -> cam (M09). */
static const char *RP_LAND[] = {"off", "turn", "cam", "turncam", "auto"};
static RpCfg g_rpc = RP_CFG_DEFAULT;
static int g_rpcPresent = -1; static FILETIME g_rpcTime; static DWORD g_rpcPoll;
static void rp_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_rpcPresent >= 0 && now - g_rpcPoll < 1000) return;
    g_rpcPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_rappel.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_rpcPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_rpcTime) == 0)) return;
    g_rpcPresent = present;
    if (present) g_rpcTime = fa.ftLastWriteTime;
    RpCfg c = RP_CFG_DEFAULT;
    char buf[512] = ""; const char *note = present ? "" : " (no ANP_rappel.txt: native)";
    if (present) {
        static int unreadLogged;
        FILE *f = fopen(fn, "r");
        if (!f) {                                     /* held by an editor / the helper: keep the previous config, retry next poll */
            memset(&g_rpcTime, 0, sizeof g_rpcTime);
            if (!unreadLogged) { unreadLogged = 1; anp_log("rappel: ANP_rappel.txt unreadable - previous config kept, retry"); }
            return;
        }
        unreadLogged = 0;
        size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
        for (char *p = buf; (p = strchr(p, '#')); ) while (*p && *p != '\n') *p++ = ' ';
        int known = 0;                                /* known: an explicit known mode word was seen */
        for (char *t = strtok(buf, " \t\r\n,;"); t; t = strtok(NULL, " \t\r\n,;")) {
            char *eq = strchr(t, '=');
            const char *k = t, *v = "";
            if (eq) { *eq = 0; v = eq + 1; }
            else { v = t; k = "mode"; }                  /* any bare word is the mode, as the other modules */
            if (!_stricmp(k, "mode")) {
                int m = -1; for (int i = 0; i < 5; i++) if (!_stricmp(v, RP_MODE[i])) m = i;
                if (m < 0) { c.mode = (known && c.mode == RP_OFF) ? RP_OFF : RP_DRY; anp_log("rappel: config mode '%s' unknown (unknown mode word: %s)", v, c.mode == RP_OFF ? "off kept" : "dry"); }
                else { c.mode = m; known = 1; }
            }
            else if (!_stricmp(k, "trace")) c.trace = atoi(v) != 0;
            else if (!_stricmp(k, "cb")) c.cb = atoi(v) != 0;
            else if (!_stricmp(k, "snap")) c.snap = atoi(v) != 0;
            else if (!_stricmp(k, "efallback")) c.efallback = atoi(v) != 0;
            else if (!_stricmp(k, "speed")) { float x = (float)atof(v); if (x >= 50.0f && x <= 2000.0f) c.speed = x; }
            else if (!_stricmp(k, "minh")) { float x = (float)atof(v); if (x >= 50.0f && x <= 1000.0f) c.minH = x; }
            else if (!_stricmp(k, "maxedge")) { float x = (float)atof(v); if (x >= 30.0f && x <= 600.0f) c.maxEdge = x; }
            else if (!_stricmp(k, "land")) { int m = -1; for (int i = 0; i < 5; i++) if (!_stricmp(v, RP_LAND[i])) m = i; if (m >= 0) c.land = m; else anp_log("rappel: config land='%s' unknown (off|turn|cam|turncam|auto)", v); }
            else if (!_stricmp(k, "camdiag")) c.camdiag = atoi(v) != 0;
            else if (!_stricmp(k, "camfix")) { if (!_stricmp(v, "off")) c.camfix = 0; else if (!_stricmp(v, "nocoll")) c.camfix = 1; else anp_log("rappel: config camfix='%s' unknown (off|nocoll)", v); }
            else if (!_stricmp(k, "landoff")) { float x = (float)atof(v); if (x >= 0.0f && x <= 200.0f) c.landOff = x; }
            else anp_log("rappel: config key '%s' unknown", k);
        }
    }
    g_rpc = c;
    anp_log("rappel: config mode=%s trace=%d cb=%d snap=%d efallback=%d speed=%.0f minh=%.0f maxedge=%.0f landoff=%.0f land=%s camdiag=%d camfix=%s%s",
            RP_MODE[c.mode], c.trace, c.cb, c.snap, c.efallback, c.speed, c.minH, c.maxEdge, c.landOff, RP_LAND[c.land], c.camdiag, c.camfix ? "nocoll" : "off", note);
}

/* ---------- module state ---------- */
static int g_rpDead;              /* module off for the session (fault outside the native path) */
static int g_rpNativeDead;        /* native path off for the session (fault inside DD's rappel code) */
static int g_rpBuildOk = -1;      /* kl2 build check (prologues + vtable slots), once */
static DWORD g_rpMovVt[1 + RP_MOV_SLOTS];   /* [0] = COL, [1..] = vtable copy */
static BYTE *g_rpLastP, *g_rpLastMov;
static int g_rpPending; static BYTE *g_rpPendBox; static DWORD g_rpPendT;   /* loader descent queued (main thread) */
static int g_rpRecover; static float g_rpPressM[9], g_rpPressF[3];          /* native fault: back to Stand here */
static int g_rpNoClips = -1;      /* player DB lacks the native clips: -1 unknown, 0 ok, 1 missing */
static char g_rpScene[8];
static int g_rpLiveActive;        /* the loader descent runs (RpTry refuses native starts) */
static DWORD g_rpLastPress; static int g_rpLastPressR;   /* one decision per press (TryActivate repeats while use is held) */

static void rp_disable(const char *where) {
    g_rpDead = 1;
    anp_log("rappel: DISABLED for this session (fault in %s) - restart the game before testing again", where);
}
static void rp_native_off(const char *where) {
    g_rpNativeDead = 1;
    anp_log("rappel: native rappel OFF for this session (fault in %s)%s", where,
            g_rpc.mode == RP_AUTO ? " - auto falls back to the loader descent" : "");
}
static int rp_anp_level(void) { return g_rpScene[0] == 'M' && g_rpScene[1] >= '0' && g_rpScene[1] <= '9'; }

static int rp_check_build(void) {
    static const struct { DWORD a; BYTE b[6]; } t[] = {
        {RP_F_TRY,    {0x83, 0xec, 0x0c, 0x56, 0x8b, 0xf1}}, {RP_F_ACT,    {0x83, 0xec, 0x6c, 0x53, 0x55, 0x56}},
        {RP_F_UPD,    {0x81, 0xec, 0xc0, 0x00, 0x00, 0x00}}, {RP_F_BEGIN,  {0x56, 0x8b, 0xf1, 0x80, 0x7e, 0x30}},
        {RP_F_END,    {0x56, 0x8b, 0xf1, 0x80, 0x7e, 0x30}}, {RP_F_HANDLE, {0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d}},
        {RP_F_GDTELE, {0x83, 0xec, 0x20, 0x53, 0x8b, 0x5c}}, {0x59d550,    {0x83, 0xec, 0x0c, 0xa1, 0x40, 0x26}},
        {0x426890,    {0x8b, 0x54, 0x24, 0x08, 0x56, 0x8b}}, {0x82cc40,    {0x83, 0xec, 0x0c, 0x53, 0x8a, 0x5c}},
    };
    for (unsigned i = 0; i < sizeof t / sizeof t[0]; i++)
        if (!readable((void*)t[i].a, 6) || memcmp((void*)t[i].a, t[i].b, 6)) { anp_log("rappel: kl2 build mismatch at %08lx - module off", t[i].a); return 0; }
    const DWORD *vt = (const DWORD*)RP_MOV_VT;
    if (!readable(vt - 1, 4 * (RP_MOV_SLOTS + 1)) || vt[14] != RP_F_TRY || vt[15] != RP_F_ACT || vt[17] != RP_F_UPD) {
        anp_log("rappel: ZFFPlayerMovementRappel vtable differs - module off"); return 0;
    }
    return 1;
}

/* ---------- small helpers ---------- */
static BYTE *rp_player(void) {
    BYTE *gd = readable((void*)0xdd265c, 4) ? *(BYTE**)0xdd265c : 0;
    if (!readable(gd + 0x828, 0x74)) return 0;
    signed char pi = *(signed char*)(gd + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gd + 0x828 + 4 * pi);
    return (readable(P, 0x2e00) && *(DWORD*)P == CL_PLAYER_VT) ? P : 0;
}
static BYTE *rp_mov(BYTE *P) {
    BYTE *m = readable(P + RP_MOV_OFF, 4) ? *(BYTE**)(P + RP_MOV_OFF) : 0;
    if (!readable(m, 0x2020)) return 0;
    DWORD vt = *(DWORD*)m;
    return (vt == RP_MOV_VT || vt == (DWORD)&g_rpMovVt[1]) && *(BYTE**)(m + 0x38) == P ? m : 0;
}
static BYTE *rp_entry_box(BYTE *entry) {
    BYTE *b = readable(entry, 0x2c) ? *(BYTE**)(entry + 0x28) : 0;
    return readable(b, 0x5c) && *(DWORD*)b == RP_BOX_VT ? b : 0;
}
static long rp_node_of_handle(DWORD h) { return (h & 0xc0000000) == 0x40000000 ? (long)((h & 0x3fffffff) >> 7) : -1; }
typedef void *(__cdecl *rp_Handle_t)(DWORD h);
typedef struct { DWORD h; void *obj; } RpHandleArg;
static int rp_handle_body(void *arg) { RpHandleArg *a = (RpHandleArg*)arg; a->obj = ((rp_Handle_t)RP_F_HANDLE)(a->h); return 0; }
static void *rp_obj(DWORD h, const char *what) {
    RpHandleArg a = {h, 0};
    if (!h) return 0;
    if (climb_guarded(what, rp_handle_body, &a) < 0) { rp_disable(what); return 0; }
    return readable(a.obj, 8) ? a.obj : 0;
}
typedef struct { BYTE *obj; float M[9], P[3]; int ok; } RpPoseArg;
static int rp_pose_body(void *arg) { RpPoseArg *a = (RpPoseArg*)arg; a->ok = cl_pose(a->obj, a->M, a->P); return 0; }
static int rp_pose(BYTE *obj, float *M, float *P, const char *what) {   /* world pose of any object with a node at +4 */
    RpPoseArg a; memset(&a, 0, sizeof a); a.obj = obj;
    if (!readable(obj, 8)) return 0;
    if (climb_guarded(what, rp_pose_body, &a) < 0) { rp_disable(what); return 0; }
    if (a.ok) { memcpy(M, a.M, 36); memcpy(P, a.P, 12); }
    return a.ok;
}

/* ---------- dry: the level's rappel points (once per list change) ---------- */
static BYTE *g_rpListGd; static int g_rpListN = -1, g_rpListTot = -1;
static void rp_log_points(void) {
    BYTE *gd = *(BYTE**)0xdd265c;
    BYTE *L = readable(gd + RP_LIST_OFF, 4) ? *(BYTE**)(gd + RP_LIST_OFF) : 0;
    if (!readable(L, 8 + 10 * 0x2c)) return;
    int tot = *(int*)L, n = *(int*)(L + 4), en = 0;
    for (int i = 0; i < n && i < 10; i++) { BYTE *b = rp_entry_box(L + 8 + 0x2c * i); if (b && b[0x30]) en |= 1 << i; }
    tot = tot * 1024 + en;                                         /* re-log when a box gets enabled ('AITrigger') */
    if (gd == g_rpListGd && n == g_rpListN && tot == g_rpListTot) return;
    g_rpListGd = gd; g_rpListN = n; g_rpListTot = tot; tot >>= 10;
    anp_log("rappel: %d rappel point(s) registered (list %p, %d registrations)%s", n, L, tot, n > 10 ? " - OVER 10" : "");
    for (int i = 0; i < n && i < 10; i++) {
        BYTE *e = L + 8 + 0x2c * i, *box = rp_entry_box(e);
        DWORD h = *(DWORD*)e;
        BYTE *geom = rp_obj(h, "rappel point geom");
        float M[9], P[3] = {0, 0, 0}, FM[9], FP[3] = {0, 0, 0};
        int gp = geom ? rp_pose(geom, M, P, "rappel point pose") : 0;
        BYTE *face = box ? rp_obj(*(DWORD*)(box + 0x34), "rappel facing") : 0;
        int fp = face ? rp_pose(face, FM, FP, "rappel facing pose") : 0;
        float *em = (float*)(e + 4);
        anp_log("rappel:   [%d] box %p node %ld enabled=%d bools=%d,%d geom=(%.1f,%.1f,%.1f)%s facing=(%.1f,%.1f,%.1f)%s "
                "entry3x3 r0=(%.2f,%.2f,%.2f) r2=(%.2f,%.2f,%.2f) cb(enter/leave/begin/end) p1=%p/%p/%p/%p p2=%p/%p/%p/%p",
                i, box, rp_node_of_handle(h), box ? box[0x30] : -1, box ? box[0x58] : -1, box ? box[0x59] : -1,
                P[0], P[1], P[2], gp ? "" : "?", FP[0], FP[1], FP[2], fp ? "" : "?",
                em[0], em[1], em[2], em[6], em[7], em[8],
                box ? *(void**)(box + 0x38) : 0, box ? *(void**)(box + 0x3c) : 0, box ? *(void**)(box + 0x40) : 0, box ? *(void**)(box + 0x44) : 0,
                box ? *(void**)(box + 0x48) : 0, box ? *(void**)(box + 0x4c) : 0, box ? *(void**)(box + 0x50) : 0, box ? *(void**)(box + 0x54) : 0);
    }
}

/* ---------- test command: <DD>\ANP_rappel_cmd.txt = "enable all" | "enable N" (list index), consumed (renamed to
   ANP_rappel_cmd.done) on the main thread, any mode but off. Sets the box's enabled byte (+0x30), what its 'AITrigger'
   handler 0x87da50 does, minus the HUD use-action icon (0x452a60): lets a test reach the rappel without the level's
   gate chain (M02: CheckPointSaveByRappel after the pills cutscene). Heap write only. ---------- */
static DWORD g_rpCmdPoll;
static void rp_cmd_poll(void) {
    DWORD now = GetTickCount();
    if (now - g_rpCmdPoll < 250) return;
    g_rpCmdPoll = now;
    char fn[MAX_PATH], dn[MAX_PATH];
    _snprintf(fn, sizeof fn, "%s\\ANP_rappel_cmd.txt", g_dir); _snprintf(dn, sizeof dn, "%s\\ANP_rappel_cmd.done", g_dir);
    if (GetFileAttributesA(fn) == INVALID_FILE_ATTRIBUTES) return;
    char buf[128] = ""; FILE *fp = fopen(fn, "r");
    if (!fp) return;
    size_t n = fread(buf, 1, sizeof buf - 1, fp); buf[n] = 0; fclose(fp);
    if (!n) return;
    if (!MoveFileExA(fn, dn, MOVEFILE_REPLACE_EXISTING) && !DeleteFileA(fn)) { anp_log("rappel: cmd: cannot consume ANP_rappel_cmd.txt (error %lu)", GetLastError()); return; }
    char verb[16] = "", arg[16] = "";
    sscanf(buf, "%15s %15s", verb, arg);
    BYTE *gd = *(BYTE**)0xdd265c;
    BYTE *L = readable(gd + RP_LIST_OFF, 4) ? *(BYTE**)(gd + RP_LIST_OFF) : 0;
    if (_stricmp(verb, "enable") || !readable(L, 8 + 10 * 0x2c)) { anp_log("rappel: cmd: '%.60s' ignored (want 'enable all' or 'enable N')", buf); return; }
    int cnt = *(int*)(L + 4), want = _stricmp(arg, "all") ? atoi(arg) : -1, done = 0;
    for (int i = 0; i < cnt && i < 10; i++) {
        BYTE *b = rp_entry_box(L + 8 + 0x2c * i);
        if (!b || (want >= 0 && i != want)) continue;
        anp_log("rappel: cmd: point [%d] box %p enabled %d -> 1", i, b, b[0x30]);
        b[0x30] = 1; done++;
    }
    if (!done) anp_log("rappel: cmd: no rappel point matched '%s' (%d registered)", arg, cnt);
}

/* ---------- dry: native state transitions ---------- */
typedef struct { BYTE *P; int turn, cam; float yaw, f[3]; } RpLandArg;
static int rp_land_body(void *arg) {
    RpLandArg *a = (RpLandArg*)arg; float M[9];
    cl_yaw_matrix(a->yaw, M);
    ((cl_Tele_t)0x82cc40)(a->P, M, a->f, a->cam, a->cam, 0);       /* force=1 re-aims the camera behind the player */
    return 0;
}
typedef struct { float o[3], seg[3], pt[3]; int hit; } RpWallArg;
static int rp_wall_body(void *arg) { RpWallArg *a = (RpWallArg*)arg; ClRay ray; a->hit = cl_ray(a->o, a->seg, 0x28, &ray, a->pt); return 0; }
typedef struct { BYTE *entry; int prompt, started, active, st, movid; } RpSnap;
static RpSnap g_rpSnap; static int g_rpSnapValid; static WORD g_rpIdsLogged[5]; static BYTE *g_rpIdsMov;
/* ---------- rappel camera (15 Oct, static RE of kl2): the player camera ZFFCamera1 (vt 0xbb76a4) is [player+0xbd8]
   (0x8fde70). A CCameraBox hands its profile record (box+0x6c) to 0x700830 -> camera+0x7fc; 0x78bbc0 re-applies it
   every frame through 0x5ea690, which also writes camera+0xb2c = current profile. Record fields: +0x4 PosObject,
   +0x20 ECamProfile, +0x150..+0x157 'valid' flags, +0x15c FOV, +0x160/+0x164 offsets, +0x168/+0x16c distances,
   +0x180 EFMMode (DD: 1 LookAtPos, 3 LookFromPos -> view direction PosObject->player, 0x447240), +0x184.
   0x5ea690's tail (0x5eac3f) copies profile +0x156 into camera+0x7eb, and 0x87ae90 runs the camera collision
   (slot 55 0x897d60: probe spheres, raycast, +0x394 blocked, +0x3f4 distance) only while +0x7eb is set.
   camdiag=1 logs the active profile on change and the camera state once a second during a rappel (read only).
   camfix=nocoll zeroes +0x156 on each profile active during the rappel (heap/.data writes, CEG-clean) and puts the
   bytes back when the rappel ends, so the collision can't pull the camera in under the facade girders. */
#define RP_CAM_VT 0xbb76a4
static struct { BYTE *rec; BYTE v; } g_rpCamSaved[16]; static int g_rpCamN; static BYTE *g_rpCamP;
static BYTE *g_rpCamProf, *g_rpCamBox; static DWORD g_rpCamLogT; static int g_rpCamWas;
static void rp_cam_restore(BYTE *P) {
    for (int i = 0; i < g_rpCamN; i++)
        if (P == g_rpCamP && readable(g_rpCamSaved[i].rec, 0x198)) g_rpCamSaved[i].rec[0x156] = g_rpCamSaved[i].v;
    if (g_rpCamN) anp_log("rappel: cam: %d profile collision flag(s) %s", g_rpCamN, P == g_rpCamP ? "restored" : "dropped (player changed)");
    g_rpCamN = 0; g_rpCamP = 0;
}
static void rp_cam_tick(BYTE *P, int rappelling) {
    if (!g_rpc.camdiag && !g_rpc.camfix && !g_rpCamN) return;
    BYTE *cam = readable(P + 0xbd8, 4) ? *(BYTE**)(P + 0xbd8) : 0;
    if (!readable(cam, 0xc00) || *(DWORD*)cam != RP_CAM_VT) cam = 0;
    if (!rappelling || !cam || !g_rpc.camfix) { if (g_rpCamN && (!rappelling || !g_rpc.camfix)) rp_cam_restore(P); }
    if (!cam) return;
    if (!rappelling) { if (g_rpCamWas) { g_rpCamWas = 0; g_rpCamProf = g_rpCamBox = 0; } return; }
    BYTE *prof = *(BYTE**)(cam + 0xb2c), *bx = *(BYTE**)(cam + 0x7fc);
    if (!readable(prof, 0x198)) prof = 0;
    if (!readable(bx, 0x194)) bx = 0;
    if (g_rpc.camfix && prof && prof[0x156]) {
        int k = 0; while (k < g_rpCamN && g_rpCamSaved[k].rec != prof) k++;
        if (k == g_rpCamN && g_rpCamN < 16) { g_rpCamSaved[g_rpCamN].rec = prof; g_rpCamSaved[g_rpCamN].v = prof[0x156]; g_rpCamN++; g_rpCamP = P; }
        prof[0x156] = 0;
        if (g_rpc.camdiag) anp_log("rappel: cam: nocoll on profile %p", prof);
    }
    if (!g_rpc.camdiag) return;
    DWORD now = GetTickCount();
    if (!g_rpCamWas || prof != g_rpCamProf || bx != g_rpCamBox) {
        g_rpCamWas = 1; g_rpCamProf = prof; g_rpCamBox = bx;
        if (prof) {
            float pp[3] = {0, 0, 0}, pm[9]; BYTE *po = *(BYTE**)(prof + 4);
            int hp = 0;
            if (prof == bx && readable(po, 8)) {                  /* guarded, but a fault here never disables the module */
                RpPoseArg pa; memset(&pa, 0, sizeof pa); pa.obj = po;
                if (climb_guarded("rappel cam posobject", rp_pose_body, &pa) >= 0 && pa.ok) { memcpy(pm, pa.M, 36); memcpy(pp, pa.P, 12); hp = 1; }
            }
            int st = (DWORD)prof >= 0x154a820 && (DWORD)prof < 0x154d190;
            anp_log("rappel: cam: profile %p (%s) box=%p ecp=%d flags=%d%d%d%d%d%d%d%d fov=%.3f off=(%.1f,%.1f) dist=(%.1f,%.1f) fm=%d +184=%d posobj=%p%s (%.1f,%.1f,%.1f)",
                    prof, st ? "static" : prof == bx ? "box" : "other", bx, prof == bx ? *(int*)(prof + 0x20) : -1,
                    prof[0x150], prof[0x151], prof[0x152], prof[0x153], prof[0x154], prof[0x155], prof[0x156], prof[0x157],
                    *(float*)(prof + 0x15c), *(float*)(prof + 0x160), *(float*)(prof + 0x164), *(float*)(prof + 0x168), *(float*)(prof + 0x16c),
                    *(int*)(prof + 0x180), *(int*)(prof + 0x184), po, hp ? "" : "?", pp[0], pp[1], pp[2]);
        } else anp_log("rappel: cam: no readable profile (box=%p)", bx);
        g_rpCamLogT = 0;
    }
    if (now - g_rpCamLogT >= 1000) {
        g_rpCamLogT = now;
        float *cp = (float*)(cam + 0x508), *off = (float*)(cam + 0x524);
        float M[9], f[3] = {0, 0, 0}; cl_pose(P, M, f);
        anp_log("rappel: cam: pos=(%.1f,%.1f,%.1f) feet=(%.1f,%.1f,%.1f) d=%.1f coll=%d blocked=%d colldist=%.1f dist55c=%.1f off=(%.1f,%.1f,%.1f) fov=%.3f",
                cp[0], cp[1], cp[2], f[0], f[1], f[2], v3dist(cp, f), cam[0x7eb], cam[0x394], *(float*)(cam + 0x3f4), *(float*)(cam + 0x55c),
                off[0], off[1], off[2], *(float*)(cam + 0x550));
    }
}

static void rp_monitor(BYTE *P, BYTE *mov) {
    RpSnap s;
    s.entry = *(BYTE**)(mov + 0x1f68); s.prompt = mov[0x1f6c]; s.started = mov[0x1f6d]; s.active = mov[0x1f64];
    s.movid = cl_movid(P); s.st = (s.active || s.movid == 0x10) ? *(int*)(P + 0x25c0) : -1;
    rp_cam_tick(P, s.active || s.movid == 0x10);
    if (g_rpIdsMov != mov) {             /* once per movement object: the clip ids slot 20 cached */
        g_rpIdsMov = mov;
        memcpy(g_rpIdsLogged, mov + 0x1fe4, sizeof g_rpIdsLogged);
        anp_log("rappel: player movement %p (vt %08lx) clip ids Start=%d Jump_Start=%d Wait_On_Wall=%d Jump_Loop=%d Jump_End=%d (65535 = name not in the level's .ANM)",
                mov, *(DWORD*)mov, g_rpIdsLogged[0], g_rpIdsLogged[1], g_rpIdsLogged[2], g_rpIdsLogged[3], g_rpIdsLogged[4]);
    }
    if (g_rpSnapValid && !memcmp(&s, &g_rpSnap, sizeof s)) return;
    int first = !g_rpSnapValid;
    int landed = g_rpSnapValid && g_rpSnap.movid == 0x10 && g_rpSnap.st == 5 && s.movid != 0x10 && !s.active;
    g_rpSnap = s; g_rpSnapValid = 1;
    if (first && !s.entry && !s.active) return;
    float M[9], f[3] = {0, 0, 0}; cl_pose(P, M, f);
    BYTE *box = s.entry ? rp_entry_box(s.entry) : 0;
    anp_log("rappel: native entry=%p box=%p(en=%d) prompt=%d started=%d active=%d state=%d mov=%d feet=(%.1f,%.1f,%.1f) yaw=%.1f",
            s.entry, box, box ? box[0x30] : -1, s.prompt, s.started, s.active, s.st, s.movid, f[0], f[1], f[2], cl_yaw(M));
    if (landed && g_rpc.land && g_rpc.mode != RP_DRY && cl_yaw(M) >= 0) {
        int land = g_rpc.land;
        if (land == 4) {                                           /* auto: wall ahead within 150 cm -> turncam, else cam */
            float y = cl_yaw(M) * 0.0174532925f;
            RpWallArg w; memset(&w, 0, sizeof w);
            v3set(w.o, f[0], f[1] + 130.0f, f[2]); v3set(w.seg, sinf(y) * 150.0f, 0, cosf(y) * 150.0f);
            int gr = climb_guarded("rappel land ray", rp_wall_body, &w);
            float d = (gr >= 0 && w.hit > 0) ? sqrtf((w.pt[0] - w.o[0]) * (w.pt[0] - w.o[0]) + (w.pt[2] - w.o[2]) * (w.pt[2] - w.o[2])) : -1.0f;
            land = (gr >= 0 && w.hit > 0) ? 3 : 2;
            anp_log("rappel: land=auto ray hit=%d dist=%.1f (guard %d) at (%.1f,%.1f,%.1f) -> %s", gr < 0 ? -2 : w.hit, d, gr, w.pt[0], w.pt[1], w.pt[2], RP_LAND[land]);
        }
        RpLandArg a; a.P = P; a.turn = land & 1; a.cam = (land >> 1) & 1;
        memcpy(a.f, f, sizeof a.f); a.yaw = cl_yaw(M) + (a.turn ? 180.0f : 0.0f);
        if (a.yaw >= 360.0f) a.yaw -= 360.0f;
        int r = climb_guarded("rappel land", rp_land_body, &a);
        float M2[9], f2[3] = {0, 0, 0}; cl_pose(P, M2, f2);
        anp_log("rappel: land=%s r=%d yaw %.1f -> %.1f (now %.1f) feet=(%.1f,%.1f,%.1f)", RP_LAND[land], r, cl_yaw(M), a.yaw, cl_yaw(M2), f2[0], f2[1], f2[2]);
    }
}

/* ---------- native path behind guards (modes native / live / auto) ---------- */
typedef unsigned char (__attribute__((thiscall)) *rp_Try_t)(void *self, void *a1, void *a2, void *a3);
typedef void (__attribute__((thiscall)) *rp_Act_t)(void *self);
typedef DWORD (__attribute__((thiscall)) *rp_Upd_t)(void *self, void *a1, void *a2, void *a3, void *a4, void *a5);
typedef struct { BYTE *self; void *a1, *a2, *a3; int r; } RpTryArg;
typedef struct { BYTE *self; void *a[5]; DWORD r; } RpUpdArg;
static int rp_try_body(void *arg) { RpTryArg *t = (RpTryArg*)arg; t->r = ((rp_Try_t)RP_F_TRY)(t->self, t->a1, t->a2, t->a3) & 0xff; return 0; }
static int rp_act_body(void *arg) { ((rp_Act_t)RP_F_ACT)(arg); return 0; }
static int rp_upd_body(void *arg) { RpUpdArg *u = (RpUpdArg*)arg; u->r = ((rp_Upd_t)RP_F_UPD)(u->self, u->a[0], u->a[1], u->a[2], u->a[3], u->a[4]); return 0; }

/* the player's own DB has the clips the native move plays (0x59d550 on the ids slot 20 cached; advances DD's anim RNG,
   called once per use press only) */
typedef struct { BYTE *mov, *P; int ok, which; } RpClipArg;
static int rp_clips_body(void *arg) {
    RpClipArg *c = (RpClipArg*)arg;
    static const int offs[5] = {0x1fe4, 0x1fe6, 0x1fe8, 0x1fea, 0x1fec};
    c->ok = 1;
    for (int i = 0; i < 5; i++) {
        WORD id = *(WORD*)(c->mov + offs[i]);
        BYTE *clip = id == 0xFFFF ? 0 : ((cl_Var_t)0x59d550)(c->P, id);
        if (!readable(clip, 0x68)) { c->ok = 0; c->which = i; return 0; }
    }
    return 0;
}
static int rp_native_clips(BYTE *mov) {
    static const char *nm[5] = {"Start", "Jump_Start", "Wait_On_Wall", "Jump_Loop", "Jump_End"};
    RpClipArg c = {mov, *(BYTE**)(mov + 0x38), 0, -1};
    if (climb_guarded("rappel clip check", rp_clips_body, &c) < 0) { rp_native_off("clip check"); return 0; }
    if (g_rpNoClips != !c.ok)
        anp_log(c.ok ? "rappel: player DB has the native rappel clips" :
                       "rappel: player DB LACKS /Movement/Rappelling/%s - native rappel would start with a NULL clip (rebuild the level with tools/rappel.py's hooks)",
                c.ok ? "" : nm[c.which]);
    g_rpNoClips = !c.ok;
    return c.ok;
}
static int rp_native_usable(void) { return !g_rpNativeDead && g_rpNoClips != 1; }

static void rp_queue_live(BYTE *mov, const char *why) {
    BYTE *box = rp_entry_box(*(BYTE**)(mov + 0x1f68));
    if (!box) { anp_log("rappel: %s but no rappel box behind the point entry - ignored", why); return; }
    if (g_rpPending) return;
    g_rpPending = 1; g_rpPendBox = box; g_rpPendT = GetTickCount();
    anp_log("rappel: %s -> loader descent queued (box %p)", why, box);
}

static int rp_decide(BYTE *self);
static unsigned char __attribute__((thiscall, force_align_arg_pointer)) RpTry(BYTE *self, void *a1, void *a2, void *a3) {
    if (g_rpDead) return ((rp_Try_t)RP_F_TRY)(self, a1, a2, a3);   /* module off: exactly the stock call */
    if (g_rpLiveActive) return 0;                      /* our descent runs */
    if (g_rpNativeDead && !self[0x1f64]) {             /* native off: keep the prompt / entry bookkeeping only in live|auto */
        if (g_rpc.mode != RP_LIVE && g_rpc.mode != RP_AUTO) return 0;
    }
    /* keep the point entry fresh: kl2 clears +0x1f68 only when its prompt was shown and no rappel started (0x673a90),
       so after a rappel or a box crossed facing away it stays set; the stock call below re-sets it (0x673aae) every
       tick while the player is really inside a point (heap write) */
    if (!self[0x1f64] && !self[0x1f6c] && !self[0x1f6d]) *(BYTE**)(self + 0x1f68) = 0;
    RpTryArg t = {self, a1, a2, a3, 0};
    if (climb_guarded("rappel TryActivate", rp_try_body, &t) < 0) { rp_native_off("TryActivate"); return 0; }
    if (!t.r) return 0;
    if (self[0x1f64]) return 1;                        /* the original's early-out: native rappel already running */
    /* a new start: use pressed at an enabled rappel point. TryActivate repeats every frame while use is held: one
       decision per press (a refusal or a queued loader descent is repeated silently for 1 s) */
    DWORD now = GetTickCount();
    if (g_rpLastPress && now - g_rpLastPress < 1000 && !g_rpLastPressR) { g_rpLastPress = now; return 0; }
    g_rpLastPress = now;
    g_rpLastPressR = rp_decide(self);
    return (unsigned char)g_rpLastPressR;
}
static int rp_decide(BYTE *self) {
    BYTE *P = *(BYTE**)(self + 0x38);
    float M[9], f[3] = {0, 0, 0};
    if (!rp_pose(P, M, f, "rappel press pose")) return 0;          /* guarded (we are outside the tick's guard here) */
    memcpy(g_rpPressM, M, 36); memcpy(g_rpPressF, f, 12);
    BYTE *box = rp_entry_box(*(BYTE**)(self + 0x1f68));
    anp_log("rappel: use pressed at a rappel point (box %p) feet=(%.1f,%.1f,%.1f) mode=%s", box, f[0], f[1], f[2], RP_MODE[g_rpc.mode]);
    if (g_rpc.mode == RP_LIVE) { rp_queue_live(self, "live"); return 0; }
    int clips = g_rpNativeDead ? 0 : rp_native_clips(self);
    if (clips && rp_native_usable()) { anp_log("rappel: native rappel starts"); return 1; }
    if (g_rpc.mode == RP_AUTO) { rp_queue_live(self, g_rpNativeDead ? "auto (native off)" : "auto (no native clips)"); return 0; }
    anp_log("rappel: native start REFUSED (%s) - use ANP_rappel.txt auto or live for the loader descent",
            g_rpNativeDead ? "native off after a fault" : "no clips");
    return 0;
}
static void __attribute__((thiscall, force_align_arg_pointer)) RpAct(BYTE *self) {
    if (g_rpDead) { ((rp_Act_t)RP_F_ACT)(self); return; }
    if (climb_guarded("rappel Activate", rp_act_body, self) < 0) { rp_native_off("Activate"); g_rpRecover = 1; return; }
    BYTE *P = *(BYTE**)(self + 0x38);
    anp_log("rappel: native Activate done: state=%d clip=%p", readable(P + 0x25c0, 4) ? *(int*)(P + 0x25c0) : -1, *(void**)(self + 0x1ff0));
}
static DWORD __attribute__((thiscall, force_align_arg_pointer)) RpUpd(BYTE *self, void *a1, void *a2, void *a3, void *a4, void *a5) {
    if (g_rpDead) return ((rp_Upd_t)RP_F_UPD)(self, a1, a2, a3, a4, a5);
    RpUpdArg u = {self, {a1, a2, a3, a4, a5}, 0};
    if (climb_guarded("rappel Update", rp_upd_body, &u) < 0) {
        /* the native no-op path (0x8259b7): out matrix = in matrix, out vector = in vector, second out vector = 0 */
        if (readable(a1, 36) && readable(a3, 36)) memcpy(a3, a1, 36);
        if (readable(a2, 12) && readable(a4, 12)) memcpy(a4, a2, 12);
        if (readable(a5, 12)) memset(a5, 0, 12);
        rp_native_off("Update"); g_rpRecover = 1;
        return (DWORD)a5;
    }
    return u.r;
}
static void rp_vt_init(void) {
    if (g_rpMovVt[1]) return;
    g_rpMovVt[0] = *(DWORD*)(RP_MOV_VT - 4);
    memcpy(&g_rpMovVt[1], (void*)RP_MOV_VT, 4 * RP_MOV_SLOTS);
    g_rpMovVt[1 + 14] = (DWORD)RpTry;
    g_rpMovVt[1 + 15] = (DWORD)RpAct;
    g_rpMovVt[1 + 17] = (DWORD)RpUpd;
}
/* our vtable on the player's rappel movement while the mode wants it (native/live/auto), the stock one otherwise */
static void rp_vt_apply(BYTE *mov) {
    int want = g_rpc.mode >= RP_NATIVE && !g_rpDead && rp_anp_level();
    DWORD cur = *(DWORD*)mov, ours = (DWORD)&g_rpMovVt[1];
    if (want && cur == RP_MOV_VT) {
        if (mov[0x1f64]) return;                      /* never swap under a running native rappel */
        rp_vt_init(); *(DWORD*)mov = ours;
        anp_log("rappel: guards on the player's rappel movement %p (vtable copy %p)", mov, &g_rpMovVt[1]);
    } else if (!want && cur == ours) {
        *(DWORD*)mov = RP_MOV_VT;
        anp_log("rappel: guards off (%s)", g_rpDead ? "module disabled" : RP_MODE[g_rpc.mode]);
    }
}

/* native fault: put the player back to Stand where he pressed use ('full' gamedata teleport: exits the movement) */
static int rp_recover_body(void *arg) {
    BYTE *P = (BYTE*)arg, *mov = rp_mov(P), *gd = *(BYTE**)0xdd265c;
    ((cl_GdTele_t)RP_F_GDTELE)(gd, g_rpPressF, g_rpPressM, 0);
    if (mov) { mov[0x1f64] = 0; mov[0x1f6c] = 0; mov[0x1f6d] = 0; *(BYTE**)(mov + 0x1f68) = 0; }
    float M[9], f[3] = {0, 0, 0}; cl_pose(P, M, f);
    anp_log("rappel: recover: back at (%.1f,%.1f,%.1f) mov=%d", f[0], f[1], f[2], cl_movid(P));
    return 0;
}

/* ---------- live: the loader descent (ZFFActionVaultOver with a loader-owned vtable, as climb.inc) ---------- */
typedef struct {
    int active, plays, n, startT, frames, did560, beginDone, traceN, animEndLogs;
    BYTE *act, *P, *box, *clip, *anim; DWORD anim0; int animId; float from, to;
    float M[9], F0[3], Xt[3], G[3], d[3], H, dist;
    const char *clipName, *endReason;
} RpRec;
static RpRec g_rp;
static BYTE *g_rpEndCbBox, *g_rpEndCbP;                /* end callback queued by our End (fired from the tick) */
static DWORD g_rpActVt[13];                           /* [0] = COL, [1..12] = ZFFActionVaultOver vtable copy */
static BYTE g_rpEdge[0x80];

static void rp_waypoint(int i, float *w) {             /* i = 0..n-1: Xt + (G - Xt) * (i+1)/n */
    float t = (float)(i + 1) / (float)g_rp.n;
    w[0] = g_rp.Xt[0] + (g_rp.G[0] - g_rp.Xt[0]) * t;
    w[1] = g_rp.Xt[1] + (g_rp.G[1] - g_rp.Xt[1]) * t;
    w[2] = g_rp.Xt[2] + (g_rp.G[2] - g_rp.Xt[2]) * t;
}
static int rp_play_next(BYTE *self, BYTE *pl) {        /* play the clip again and warp to the next waypoint */
    BYTE *anim = ((cl_Play_t)CL_VF(pl, 0x204))(pl, g_rp.clip, 1);
    if (!anim || !readable(anim, 0x20)) { anp_log("rappel: PlayAnim failed (%p) on play %d", anim, g_rp.plays + 1); return 0; }
    *(BYTE**)(self + 0xc) = anim;
    g_rp.anim = anim; g_rp.anim0 = *(DWORD*)anim; g_rp.animId = *(int*)(anim + 0x18);
    float cur = *(float*)(anim + 4); g_rp.from = *(float*)(anim + 8); g_rp.to = *(float*)(anim + 0xc);
    float w[3]; rp_waypoint(g_rp.plays, w);
    float fr = g_rp.to - cur - 1.0f; if (fr < 1.0f) fr = 1.0f;
    int ok = ((cl_Warp_t)CL_VF(pl, 0x208))(pl, g_rp.M, w, fr);
    g_rp.plays++;
    if (g_rpc.trace) anp_log("rappel: play %d/%d anim=%p cur=%.1f to=%.1f warp -> (%.1f,%.1f,%.1f) over %.1f frames ok=%d",
                             g_rp.plays, g_rp.n, anim, cur, g_rp.to, w[0], w[1], w[2], fr, ok);
    return ok ? 1 : 0;
}
static float rp_anim_cur(void) {
    BYTE *a = g_rp.anim;
    if (!a || !readable(a, 0x20) || *(DWORD*)a != g_rp.anim0) return -1.0f;
    return *(float*)(a + 4);
}
static int rp_start_body(void *arg) {
    BYTE *self = (BYTE*)arg, *pl = *(BYTE**)(self + 8);
    if (!g_rp.active || g_rp.act != self || pl != g_rp.P) { anp_log("rappel: START on an unknown record"); return 0; }
    if (*(void**)(pl + 0x2810)) ((cl_Void_t)0x5fcb80)(pl);        /* stock prep, as climb */
    *(int*)(pl + 0x2d60) = 0;
    ((cl_Void_t)CL_VF(pl, 0x560))(pl); g_rp.did560 = 1;           /* ghost collision; stock End undoes it */
    if (!rp_play_next(self, pl)) { g_rp.endReason = "playanim/warp"; return 0; }
    anp_log("rappel: START act=%p clip='%s' frames=%d plays=%d H=%.1f from (%.1f,%.1f,%.1f) rope (%.1f,%.1f,%.1f) ground (%.1f,%.1f,%.1f)",
            self, g_rp.clipName, g_rp.frames, g_rp.n, g_rp.H, g_rp.F0[0], g_rp.F0[1], g_rp.F0[2],
            g_rp.Xt[0], g_rp.Xt[1], g_rp.Xt[2], g_rp.G[0], g_rp.G[1], g_rp.G[2]);
    return 1;
}
static unsigned char __attribute__((thiscall, force_align_arg_pointer)) RpLiveStart(BYTE *self) {
    int r = climb_guarded("rappel Start", rp_start_body, self);
    if (r < 0) { rp_disable("live Start"); g_rp.endReason = "fault"; return 0; }
    return r == 1;
}
static int rp_update_body(void *arg) {
    BYTE *self = (BYTE*)arg, *pl = g_rp.P;
    int r = ((cl_Char_t)0x5b1e40)(self) & 0xff;                    /* stock: camera follow */
    if (!g_rp.active || g_rp.act != self) return r;
    float cur = rp_anim_cur();
    if (g_rpc.trace && (g_rp.traceN++ % 4) == 0) {
        float M[9], f[3] = {0, 0, 0}; cl_pose(pl, M, f);
        anp_log("rappel: trace play=%d cur=%.1f to=%.1f feet=(%.1f,%.1f,%.1f)", g_rp.plays, cur, g_rp.to, f[0], f[1], f[2]);
    }
    if (cur < 0) { g_rp.endReason = "channel lost"; return 0; }
    if (cl_curT() - g_rp.startT > g_rp.n * (g_rp.frames * 1024 / 25 + 512) + 2048) { g_rp.endReason = "timeout"; return 0; }
    if (cur >= g_rp.to - 1.0f) {
        if (g_rp.plays < g_rp.n) { if (!rp_play_next(self, pl)) { g_rp.endReason = "replay failed"; return 0; } return r; }
        g_rp.endReason = "clip end"; return 0;
    }
    return r;
}
static unsigned char __attribute__((thiscall, force_align_arg_pointer)) RpLiveUpdate(BYTE *self) {
    int r = climb_guarded("rappel Update(live)", rp_update_body, self);
    if (r < 0) { rp_disable("live Update"); g_rp.endReason = "fault"; return 0; }
    return r != 0;
}
typedef struct { BYTE *self; int id; } RpAnimEndArg;
static int rp_animend_body(void *arg) {
    RpAnimEndArg *a = (RpAnimEndArg*)arg;
    if (!g_rp.active || g_rp.act != a->self) return 1;
    if (a->id == g_rp.animId) {
        if (g_rp.plays < g_rp.n) return 0;                         /* more plays to come: Update replays */
        g_rp.endReason = "animend"; return 1;
    }
    if (g_rp.animEndLogs++ < 5) anp_log("rappel: foreign animend id=%d (ours %d) - ignored", a->id, g_rp.animId);
    return 0;
}
static unsigned char __attribute__((thiscall, force_align_arg_pointer)) RpLiveAnimEnd(BYTE *self, int id) {
    RpAnimEndArg a = {self, id};
    int r = climb_guarded("rappel AnimEnd", rp_animend_body, &a);
    if (r < 0) { rp_disable("live AnimEnd"); g_rp.endReason = "fault"; return 1; }
    return r != 0;
}
typedef struct { BYTE *box, *P; } RpCbArg;
typedef void (__attribute__((thiscall)) *rp_Cb_t)(void *box, void *player);
static int rp_end_cb_body(void *arg) { RpCbArg *c = (RpCbArg*)arg; ((rp_Cb_t)RP_F_END)(c->box, c->P); return 0; }
static int rp_begin_cb_body(void *arg) { RpCbArg *c = (RpCbArg*)arg; ((rp_Cb_t)RP_F_BEGIN)(c->box, c->P); return 0; }
static void rp_reset_native_fields(BYTE *P) {
    BYTE *mov = rp_mov(P);
    if (mov && !mov[0x1f64]) { mov[0x1f6c] = 0; mov[0x1f6d] = 0; *(BYTE**)(mov + 0x1f68) = 0; }
}
static int rp_end_body(void *arg) {
    BYTE *self = (BYTE*)arg, *pl = *(BYTE**)(self + 8);
    int mine = g_rp.active && g_rp.act == self;
    if (mine) {                                                    /* stock End teleports to +0x38 / +0x68: the ground */
        memcpy(self + 0x38, g_rp.M, 36); memcpy(self + 0x68, g_rp.G, 12);
    }
    if (!mine || g_rp.did560) ((cl_Void_t)0x82f780)(self);         /* stock End: undoes vt+0x560, stance, teleport */
    else ((cl_Void_t)0x4af5b0)(pl);
    float M[9], f[3] = {0, 0, 0}, dist = -1;
    if (mine && cl_pose(pl, M, f)) {
        dist = v3dist(f, g_rp.G);
        if (dist > 25.0f) ((cl_Tele_t)0x82cc40)(pl, g_rp.M, g_rp.G, 0, 0, 0);   /* unforced, as climb's safety snap */
    }
    anp_log("rappel: END reason=%s plays=%d/%d feet=(%.1f,%.1f,%.1f) ground=(%.1f,%.1f,%.1f) dist=%.1f%s",
            g_rp.endReason ? g_rp.endReason : "engine abort", g_rp.plays, g_rp.n, f[0], f[1], f[2], g_rp.G[0], g_rp.G[1], g_rp.G[2],
            dist, mine ? "" : " (unknown record)");
    if (mine) {
        BYTE *box = g_rp.box, *P = g_rp.P;
        memset(&g_rp, 0, sizeof g_rp); g_rpLiveActive = 0;
        rp_reset_native_fields(P);
        if (g_rpc.cb && readable(box, 0x5c) && *(DWORD*)box == RP_BOX_VT) { g_rpEndCbBox = box; g_rpEndCbP = P; }   /* next tick */
    }
    return 0;
}
static void __attribute__((thiscall, force_align_arg_pointer)) RpLiveEnd(BYTE *self) {
    if (climb_guarded("rappel End", rp_end_body, self) < 0) { rp_disable("live End"); memset(&g_rp, 0, sizeof g_rp); g_rpLiveActive = 0; }
}

/* the rope line: from the player, the nearest drop of >= minh within maxedge along the facing object's axes or the
   player's own forward/back. Probes from 250 cm above the feet, 350 cm down (mask 0x20 = world, as climb). */
typedef struct { float d[3], dist, X[3], G[3], H; } RpPlan;
static int rp_plan(BYTE *box, const float *M, const float *F0, RpPlan *best) {
    float dirs[6][3]; int nd = 0;
    float FM[9], FP[3];
    BYTE *face = rp_obj(*(DWORD*)(box + 0x34), "rappel facing");
    if (face && rp_pose(face, FM, FP, "rappel facing pose")) {
        for (int r = 0; r < 2; r++) {
            const float *row = FM + (r ? 6 : 0);
            float L = sqrtf(row[0] * row[0] + row[2] * row[2]);
            if (L < 1e-3f) continue;
            v3set(dirs[nd++], row[0] / L, 0, row[2] / L);
            v3set(dirs[nd++], -row[0] / L, 0, -row[2] / L);
        }
    }
    {   float L = sqrtf(M[0] * M[0] + M[2] * M[2]);
        if (L > 1e-3f) { v3set(dirs[nd++], -M[0] / L, 0, -M[2] / L); v3set(dirs[nd++], M[0] / L, 0, M[2] / L); }   /* forward, back */
    }
    int found = 0; ClRay ray; float pt[3], o[3], seg[3];
    for (int k = 0; k < nd; k++) {
        const float *d = dirs[k];
        int dup = 0; for (int j = 0; j < k; j++) if (d[0] * dirs[j][0] + d[2] * dirs[j][2] > 0.97f) dup = 1;
        if (dup) continue;
        float edge = -1; const char *why = "no edge";
        for (float dist = 15.0f; dist <= g_rpc.maxEdge; dist += 15.0f) {
            v3set(o, F0[0] + d[0] * dist, F0[1] + 250.0f, F0[2] + d[2] * dist); v3set(seg, 0, -350.0f, 0);
            int hit = cl_ray(o, seg, 0x20, &ray, pt);
            if (hit < 0) return -1;
            if (!hit || pt[1] < F0[1] - 45.0f) { edge = dist; break; }
            if (pt[1] > F0[1] + 150.0f) { why = "wall"; break; }      /* floor or a parapet: go on */
        }
        if (edge < 0) { anp_log("rappel: plan dir (%.2f,%.2f): %s within %.0f cm", d[0], d[2], why, g_rpc.maxEdge); continue; }
        float X[3] = {F0[0] + d[0] * (edge + 35.0f), F0[1], F0[2] + d[2] * (edge + 35.0f)};
        v3set(o, X[0], F0[1] + 30.0f, X[2]); v3set(seg, 0, -30000.0f, 0);
        int g = cl_ray(o, seg, 0x20, &ray, pt);
        if (g < 0) return -1;
        if (!g) { anp_log("rappel: plan dir (%.2f,%.2f): edge at %.0f cm, no ground below within 300 m", d[0], d[2], edge); continue; }
        float H = F0[1] - pt[1];
        if (H < g_rpc.minH) { anp_log("rappel: plan dir (%.2f,%.2f): edge at %.0f cm, drop only %.1f cm", d[0], d[2], edge, H); continue; }
        float G[3] = {X[0], pt[1], X[2]};
        if (g_rpc.landOff > 0) {                                   /* land a little away from the wall when there is ground */
            float Lp[3] = {X[0] + d[0] * g_rpc.landOff, 0, X[2] + d[2] * g_rpc.landOff};
            v3set(o, Lp[0], pt[1] + 150.0f, Lp[2]); v3set(seg, 0, -300.0f, 0);
            float p2[3];
            if (cl_ray(o, seg, 0x20, &ray, p2) == 1 && fabsf(p2[1] - pt[1]) < 60.0f) v3set(G, Lp[0], p2[1], Lp[2]);
        }
        anp_log("rappel: plan dir (%.2f,%.2f): edge at %.0f cm, rope (%.1f,%.1f) ground y=%.1f drop %.1f", d[0], d[2], edge, X[0], X[2], G[1], H);
        if (!found || edge < best->dist) {
            found = 1; memcpy(best->d, d, 12); best->dist = edge; memcpy(best->X, X, 12); memcpy(best->G, G, 12); best->H = H;
        }
    }
    return found;
}
static const char *g_rpClipNames[] = {"/Movement/Rappelling/Rappelling", "/Movement/Rappelling/NPC_Rappelling",
                                      "/Movement/Rappelling/Fall", "/Movement/Climb/Down/High", "/Movement/Climb/Down/Medium"};
static BYTE *rp_find_clip(BYTE *P, const char **name, int *frames) {
    for (unsigned i = 0; i < sizeof g_rpClipNames / sizeof g_rpClipNames[0]; i++) {
        WORD id = 0xFFFF;
        ((cl_Name_t)0x426890)(P, &id, g_rpClipNames[i]);
        if (id == 0xFFFF) continue;
        BYTE *clip = ((cl_Var_t)0x59d550)(P, id);
        if (!readable(clip, 0x68)) continue;
        *name = g_rpClipNames[i]; *frames = *(WORD*)(clip + 2);
        if (*frames < 2) continue;
        return clip;
    }
    return 0;
}
static const char *rp_precond(BYTE *P, int T) {
    if (g_rp.active) return "descending";
    if (*(BYTE**)(P + 0x6b0) != P + 0xdb0) return "movement table (MiniScene?)";
    int id = cl_movid(P);
    if (id != 2 && id != 3) return "movement not Stand/BaseMove";
    if (((cl_Int_t)CL_VF(P, 0x388))(P) != 0) return "action running";
    if (T - *(int*)(P + 0x2c48) < 512) return "< 0.5 s since last action";
    if (*(DWORD*)(P + 0xed0) & 0x80) return "input blocked";
    if (*(DWORD*)(P + 0xd50) || *(DWORD*)(P + 0xd44)) return "seat/carrier";
    if (!(P[0x2720] & 2)) return "not local human";
    if (!*(void**)(P + 0x2810)) return "P+0x2810 null";
    void *cw = readable((void*)0x138c868, 4) ? *(void**)0x138c868 : 0;
    if (!readable(cw, 4) || *(DWORD*)cw != CL_COLLW_VT || *(int*)0xcd9c60 != 1) return "no collision world";
    return 0;
}
static void rp_start_live(BYTE *P, BYTE *box, int T) {
    const char *why = rp_precond(P, T);
    if (why) { anp_log("rappel: loader descent not started (%s)", why); return; }
    float M[9], F0[3];
    if (!cl_pose(P, M, F0)) { anp_log("rappel: loader descent: no player pose"); return; }
    RpPlan pl; memset(&pl, 0, sizeof pl);
    int r = rp_plan(box, M, F0, &pl);
    if (r < 0) { anp_log("rappel: loader descent: raycast unavailable"); return; }
    if (!r) { anp_log("rappel: loader descent: no drop of >= %.0f cm within %.0f cm of the player - not started", g_rpc.minH, g_rpc.maxEdge); return; }
    const char *cname = 0; int frames = 0;
    BYTE *clip = rp_find_clip(P, &cname, &frames);
    float RM[9]; cl_yaw_matrix(atan2f(-pl.d[0], -pl.d[2]) * 57.2957795f, RM);   /* face the wall, back to the drop */
    RpCbArg cb = {box, P};
    if (!clip) {
        if (!g_rpc.snap) { anp_log("rappel: loader descent: no usable clip (rappel / climb-down) in the player's DB - not started (snap=0)"); return; }
        if (g_rpc.cb && climb_guarded("rappel begin callback", rp_begin_cb_body, &cb) < 0) { rp_disable("begin callback"); return; }
        ((cl_Tele_t)0x82cc40)(P, RM, pl.G, 1, 1, 0);
        float f[3] = {0, 0, 0}, M2[9]; cl_pose(P, M2, f);
        anp_log("rappel: SNAP (no clip) -> ground (%.1f,%.1f,%.1f), feet now (%.1f,%.1f,%.1f)", pl.G[0], pl.G[1], pl.G[2], f[0], f[1], f[2]);
        rp_reset_native_fields(P);
        if (g_rpc.cb && climb_guarded("rappel end callback", rp_end_cb_body, &cb) < 0) rp_disable("end callback");
        return;
    }
    if (!g_rpActVt[1]) {
        g_rpActVt[0] = *(DWORD*)(CL_VAULT_VT - 4);
        memcpy(&g_rpActVt[1], (void*)CL_VAULT_VT, 48);
        g_rpActVt[1 + 2] = (DWORD)RpLiveStart;
        g_rpActVt[1 + 4] = (DWORD)RpLiveUpdate;
        g_rpActVt[1 + 5] = (DWORD)RpLiveEnd;
        g_rpActVt[1 + 10] = (DWORD)RpLiveAnimEnd;
    }
    BYTE *act = ((cl_Create_t)CL_VF(P, 0x384))(P, 0x2B);
    if (!readable(act, 0x80) || *(DWORD*)act != CL_VAULT_VT || *(BYTE**)(act + 8) != P) {
        anp_log("rappel: CreateAction(0x2B) returned %p (vt %08lx) - not used", act, readable(act, 4) ? *(DWORD*)act : 0); return;
    }
    *(DWORD**)act = &g_rpActVt[1];
    memcpy(act + 0x14, RM, 36); memcpy(act + 0x5c, F0, 12);
    memcpy(act + 0x38, RM, 36); memcpy(act + 0x68, pl.G, 12);      /* stock End lands the player on the ground */
    *(BYTE**)(act + 0x10) = clip; *(void**)(act + 0xc) = 0;
    act[0x74] = act[0x75] = 0; *(int*)(act + 0x78) = 0; *(BYTE**)(act + 0x7c) = g_rpEdge;
    memset(&g_rp, 0, sizeof g_rp);
    g_rp.active = 1; g_rpLiveActive = 1; g_rp.act = act; g_rp.P = P; g_rp.box = box; g_rp.clip = clip; g_rp.clipName = cname;
    g_rp.frames = frames; g_rp.startT = T; g_rp.H = pl.H; g_rp.dist = pl.dist;
    memcpy(g_rp.M, RM, 36); memcpy(g_rp.F0, F0, 12); memcpy(g_rp.G, pl.G, 12); memcpy(g_rp.d, pl.d, 12);
    v3set(g_rp.Xt, pl.X[0], F0[1], pl.X[2]);
    {   float clipSec = frames / 25.0f, need = pl.H / g_rpc.speed;
        int n = (int)ceilf(need / (clipSec > 0.2f ? clipSec : 0.2f)); g_rp.n = n < 1 ? 1 : n > 12 ? 12 : n; }
    BYTE *mov = rp_mov(P);
    if (mov) mov[0x1f6d] = 1;                                      /* 'started': the native Leave callback must not fire */
    ((cl_Void_t)CL_VF(P, 0x374))(P);                               /* Abort (no-op when idle) */
    ((cl_StartAct_t)CL_VF(P, 0x370))(P, act);                      /* RpLiveStart runs in here */
    if (cl_disp_cur(P) != act) {
        anp_log("rappel: start failed (reason %s) - action finished at once", g_rp.endReason ? g_rp.endReason : "?");
        if (g_rp.act == act) { memset(&g_rp, 0, sizeof g_rp); g_rpLiveActive = 0; }
        if (mov) mov[0x1f6d] = 0;
        return;
    }
    g_rp.beginDone = 0;                                            /* begin callback on the next tick, outside the engine call */
}

/* ---------- per-frame tick ---------- */
static int g_rpLastT = -0x7fffffff, g_rpPrevE; static DWORD g_rpLastPos;
static int rappel_tick(void *unused) {
    (void)unused;
    rp_cfg_poll();
    if (g_rpc.mode == RP_OFF) {
        BYTE *P = rp_player(), *mov = P ? rp_mov(P) : 0;
        if (mov) rp_vt_apply(mov);                                 /* hand the stock vtable back */
        return 0;
    }
    BYTE *sys = cl_sys();
    if (!sys) return 0;
    BYTE *P = rp_player();
    if (!P) { g_rpLastP = 0; return 0; }
    int T = *(int*)(sys + 0x48);
    if (T == g_rpLastT) return 0;                                  /* paused */
    g_rpLastT = T;
    char sc[8];                                                    /* campaign.inc's scene id, read every tick */
    EnterCriticalSection(&g_cmpCs); memcpy(sc, g_cscene, sizeof sc); LeaveCriticalSection(&g_cmpCs); sc[7] = 0;
    int sceneChg = strcmp(sc, g_rpScene) != 0;
    if (P != g_rpLastP || sceneChg) {                              /* new player or new scene (the player object can be reused) */
        g_rpLastP = P; g_rpSnapValid = 0; g_rpListN = -1; g_rpNoClips = -1; g_rpPending = 0;
        memcpy(g_rpScene, sc, sizeof g_rpScene);
        if (sceneChg && g_rp.active) { memset(&g_rp, 0, sizeof g_rp); g_rpLiveActive = 0; }   /* old scene's action: forget, no write */
        if (sceneChg) { g_rpEndCbBox = 0; g_rpEndCbP = 0; }
        anp_log("rappel: player %p scene '%s' (%s)", P, g_rpScene, rp_anp_level() ? "ANP level" : "not an ANP level: rappel module idle");
    }
    if (!rp_anp_level()) {                                         /* stock level: hand the stock vtable back if ours is still on */
        BYTE *m = rp_mov(P);
        if (m) rp_vt_apply(m);                                     /* want = 0 outside ANP levels: restores RP_MOV_VT only */
        return 0;
    }
    BYTE *mov = rp_mov(P);
    if (!mov) {
        if (g_rpLastMov != (BYTE*)1) { g_rpLastMov = (BYTE*)1; anp_log("rappel: no rappel movement at player+0x%x (vt check failed) - idle", RP_MOV_OFF); }
        return 0;
    }
    g_rpLastMov = mov;
    rp_cmd_poll();
    rp_log_points();
    rp_monitor(P, mov);
    rp_vt_apply(mov);
    if (g_rpc.trace && GetTickCount() - g_rpLastPos >= 1000) {
        g_rpLastPos = GetTickCount();
        float M[9], f[3] = {0, 0, 0};
        if (cl_pose(P, M, f)) anp_log("rappel: pos: %.1f %.1f %.1f %.1f mov=%d T=%d%s", f[0], f[1], f[2], cl_yaw(M), cl_movid(P), T, g_rp.active ? " descending" : "");
    }
    if (g_rpRecover) {
        g_rpRecover = 0;
        if (climb_guarded("rappel recover", rp_recover_body, P) < 0) rp_disable("recover");
    }
    if (g_rpEndCbBox) {                                            /* queued by our End: fire it outside the engine call */
        RpCbArg c = {g_rpEndCbBox, g_rpEndCbP};
        g_rpEndCbBox = 0; g_rpEndCbP = 0;
        if (c.P == P && readable(c.box, 0x5c) && *(DWORD*)c.box == RP_BOX_VT) {
            if (climb_guarded("rappel end callback", rp_end_cb_body, &c) < 0) rp_disable("end callback");
            else anp_log("rappel: end callback fired (box %p: containers +0x44 / +0x54)", c.box);
        }
    }
    if (g_rp.active) {
        if (g_rp.P != P || cl_disp_cur(P) != g_rp.act) {
            anp_log("rappel: descent record dropped (action gone)");
            memset(&g_rp, 0, sizeof g_rp); g_rpLiveActive = 0; rp_reset_native_fields(P);
            return 0;
        }
        if (!g_rp.beginDone) {
            g_rp.beginDone = 1;
            RpCbArg c = {g_rp.box, P};
            if (g_rpc.cb) {
                if (climb_guarded("rappel begin callback", rp_begin_cb_body, &c) < 0) rp_disable("begin callback");
                else anp_log("rappel: begin callback fired (box %p: containers +0x40 / +0x50)", g_rp.box);
            }
        }
        return 0;
    }
    /* E inside a box whose native prompt is not shown (live / auto when native cannot run) */
    HWND fw = GetForegroundWindow(); DWORD pid = 0;
    if (fw) GetWindowThreadProcessId(fw, &pid);
    int E = fw && pid == GetCurrentProcessId() && (GetAsyncKeyState('E') & 0x8000);
    int edge = E && !g_rpPrevE; g_rpPrevE = E;
    /* +0x1f68 is kept fresh by RpTry (cleared before every stock TryActivate, re-set only while inside a point) */
    if (edge && g_rpc.efallback && !g_rpPending && *(BYTE**)(mov + 0x1f68) && !mov[0x1f6c] && !mov[0x1f64]
        && (g_rpc.mode == RP_LIVE || (g_rpc.mode == RP_AUTO && !rp_native_usable())))
        rp_queue_live(mov, "E in a rappel box without the native prompt");
    if (g_rpPending) {
        g_rpPending = 0;
        if (GetTickCount() - g_rpPendT > 2000) { anp_log("rappel: queued descent dropped (stale)"); return 0; }
        if (g_rpc.mode == RP_LIVE || g_rpc.mode == RP_AUTO) rp_start_live(P, g_rpPendBox, T);
    }
    return 0;
}
static int rappel_cleanup_body(void *unused) {
    (void)unused;
    BYTE *P = g_rp.P;
    if (g_rp.active && g_rp.act && readable(P, 0x200) && *(DWORD*)P == CL_PLAYER_VT && cl_disp_cur(P) == g_rp.act) {
        ((cl_Void_t)CL_VF(P, 0x374))(P);
        anp_log("rappel: cleanup: descent aborted");
    }
    if (g_rp.active) { memset(&g_rp, 0, sizeof g_rp); g_rpLiveActive = 0; }
    BYTE *mov = readable(P, 0x200) ? rp_mov(P) : 0;
    if (mov && *(DWORD*)mov == (DWORD)&g_rpMovVt[1] && !mov[0x1f64]) { *(DWORD*)mov = RP_MOV_VT; anp_log("rappel: cleanup: stock vtable restored"); }
    return 0;
}
static int g_rpRestoreDone;
static void rappel_frame(void) {
    if (!g_clMainTid || GetCurrentThreadId() != g_clMainTid) return;
    if (g_rpDead) {                                                /* once: our descent aborted, stock vtable back */
        if (!g_rpRestoreDone) {
            g_rpRestoreDone = 1;
            if (!g_rp.P) g_rp.P = rp_player();
            if (climb_guarded("rappel cleanup", rappel_cleanup_body, 0) < 0) { memset(&g_rp, 0, sizeof g_rp); g_rpLiveActive = 0; }
        }
        return;
    }
    if (g_rpBuildOk < 0) {
        g_rpBuildOk = rp_check_build();
        anp_log("rappel: module %s (ANP_rappel.txt: off|dry|native|live|auto, default native)", g_rpBuildOk ? "ready" : "OFF (kl2 build check failed)");
    }
    if (!g_rpBuildOk) return;
    if (climb_guarded("rappel tick", rappel_tick, 0) < 0) rp_disable("tick");     /* the next frame cleans up */
}
