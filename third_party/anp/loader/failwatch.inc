/* ==================== failwatch.inc: mission-fail / merc-state diagnostic (13 Oct; DATA READS ONLY) ====================
   Included by anp_loader.c BEFORE climb.inc (uses anp_log, readable, rtti_name, g_dir, g_cscene / g_cmpCs from campaign.inc;
   climb_guarded is declared below and defined in climb.inc's asm). Ticked once per gameplay frame from climb.inc's frame
   hook (anp_rcb_pre, kl2's IAT slot for steam_api!SteamAPI_RunCallbacks, return address 0x87aa82, main thread), AFTER
   climb_frame() (which sets g_clMainTid, needed by the VEH fault guard). The whole tick runs inside climb_guarded(): a
   fault is logged as "climb: FAULT ... in failwatch tick" and switches failwatch off for the session.
   CEG: no kl2 byte is written, no engine function is called, no heap/.data write. Only reads, each validated with readable().

   What it logs (lines start with "fail:"):
   (1) The mission-fail text. kl2 static RE (capstone, 13 Oct):
       0x7864f0 = thiscall(obj, const char *key, char flag): obj+0x344 = flag; 0x4f99e0(obj+0x244, key, 0x100)
       (0x4f99e0: dst[0] = 0, then strlen + memcpy of at most 0xff bytes + NUL: an 8-bit NUL-terminated string, NOT UTF-16).
       Every call site passes obj = 0x156b3b0 (mov ecx, 0x156b3b0), so text = 0x156b5f4 (0x100 bytes), flag = 0x156b6f4.
       Call sites (8): ZVehicleFailSafe13B slot 25 0x415960 (MF_15_CarCrash), ZVehicleGetAwayEffects slot 25 0x4bb032
       (MF_15_CarCrash), ZMissionFailed slot 26 0x5f23c1 (its own text, [this+0x30]+0xc), ZFFPlayer slot 87's player-down
       machine 0x5fe751 (/Menu/Misc/YouDied or /Menu/Misc/LynchDied), ZGeneric/ZCivilian@CPPScript slot 56 0x6d25fa (also
       reached from ZSoldier slot 56 0x8fd470; AllLevels/Menu/Ingame/MF_01_MercDead), ZLevelCtrlM05 slot 25 0x72048b
       (MF_05_LynchDied), ZFFPlayer slot 415 -> 0x8ce1fb (/Menu/Misc/YouDied) - each followed by 0x8edc40 (mission failed) -
       and 0x7f5f96 (ZKillBox path 0x7f5f40: text from the box, flag = 1, NO 0x8edc40 call: deferred). All 7 0x8edc40 call
       sites are preceded by 0x7864f0. The text is never cleared (it stays until the next fail), so a repeat of the same fail
       does not change it: see (1b). The flag is read at 0x5fe677 (the player-down machine skips its own YouDied fail when it
       is set) and cleared at 0x84a690 (ZKillBox slot 22). The text is a resource key; the HUD (0x5cb582, element
       'MissionFailed') localizes it through [esi]+0x60 and prints it with "%s".
   (1b) The fail window request on the same object (0x8edc40, single player branch): 0x71e760(idx) closes the open window
       (+0x20+idx = 0, +0x22+32*idx = "", +0x1c = -1), then 0x50dc80(idx) (+0x1c = idx), name "MissionFailedReload" (or
       "MissionFailedReloadClient" in a hosted session) copied to +0x22+32*idx (32 bytes), +0x66+idx = 5/6,
       +0x20+idx = 1, +0x64+idx = 1. idx = 8edc40's char argument (0 at every call site except 0x8ce1fb: player+0x91e).
       So 0x156b3d0/0x156b3d1 (open) and 0x156b3d2/0x156b3f2 (names) going to 1/"MissionFailedReload" = one fail, even
       when the text repeats. Inferred: the same fields serve the other ingame windows opened through 0x50dc80; every
       change is logged with its name.
   (1c) gameMgr+0x4d1c (byte; set to 1 at 0x8ce1f4 (YouDied) and 0x7f5f6f (ZKillBox) right before the fail text, cleared
       at 0x7f5ff4 / 0x554074 / 0x47d0a1). Meaning inferred ("player-death fail in progress"); changes are logged raw.
   (2) Mercs: DD's merc list 0x1548fd8 ([count], 0x1548fdc[16] scripts; appended by soldier init 0x615c90 through
       0x7175a0 (max 16), cleared by 0x676480 at 0x76c915; kl2 itself walks it at 0x71c81b/0x8ba3e0 reading
       [script+0x40]+0x576 and script+0x6e8) and the buddy body gameMgr+0x4cf0 (0x615e5d: = script+0x40 when
       script+0x6e8 == 1). Per merc: body+0x576 (able: 1 = alive/usable; set 1 at 0x546eca / 0x4b1d08, cleared on the
       death paths 0x466deb / 0x51e0b4 / 0x77a9d2; +0x574/+0x575 are cleared with it and shown alongside), HP, the
       mission-critical byte script+0x513 (read by slot 58 0x8f44a0; squad.inc critical=clear writes it) and +0x512,
       and the body position.
       HP (proved): the ZFFActor ctor (vt 0xbb3bac) news a 0x28-byte HP block (ctor 0x4aad80(owner): +0x24 = owner) and
       stores it at actor+0x5fc (0x830815), then SetMax 0x5c8010 (+8 = max, 100.0) and 0x8edaf0 (+4 = +8). Getters:
       0x539dd0 'mov eax,[ecx+0x5fc]; fld [eax+4]' (current), 0x574060 (ZFFActor slot 414) '... fld [eax+8]' (max).
       The player is different: ZFFPlayer+0xa48 (ctor 0x6ef3da), same block layout (godmode.inc).
       Position (proved): kl2's node->world point 0x7b3020 walks node, [node+0x50], ... applying each node's 3x3 at
       +0x00..+0x20 (0x6be1c0: out = (v0*m6+v1*m3+v2*m0, v0*m7+v1*m4+v2*m1, v0*m8+v1*m5+v2*m2)) and adding +0x24..+0x2c
       (0x42a4d0). fw_world() does the same arithmetic on plain reads (no call), for the origin of body+4.
       Validation: list entry s: vt 0xbd0954 (ZSoldier@CPPScript), body = [s+0x40], [body+0x77c] == s; the buddy body the
       other way round. HP block only if its owner (+0x24) is the body.
   (3) kl2's game-state counter [0xe0e644] (inc only at 0x65a4fd state activate and 0x5d5de7 state switch; a checkpoint
       reload/level restart bumps it). Each change, each fail-text change and each fail-window open also writes a
       snapshot: the player (HP, position) and every merc.

   Config: <DD>\ANP_failwatch.txt (polled once a second; absent = on with the defaults). Tokens, space/line separated:
     off | on            (default on)
     pos=0|1             merc position lines (default 1): when a merc moved more than posdist cm since his last
                         position line, at most once a second per merc
     posdist=200         cm
     hp=0|1              HP change lines (default 1): drops at most every 100 ms per merc (summed), rises at most once a
                         second or on reaching max
   Line caps: 5000 event lines (fail/state/window/able/crit/new/gone/snapshot), 10000 hp/pos lines. */

#include <math.h>
int climb_guarded(const char *what, int (*fn)(void*), void *arg);   /* climb.inc */

#define FW_FAILOBJ     0x156b3b0                  /* menu/fail request object (.data) */
#define FW_TEXT        (FW_FAILOBJ + 0x244)       /* 0x156b5f4, 0x100 bytes */
#define FW_FLAG        (FW_FAILOBJ + 0x344)       /* 0x156b6f4 */
#define FW_WPLAYER     (FW_FAILOBJ + 0x1c)        /* int: player of the open window, -1 none */
#define FW_WOPEN       (FW_FAILOBJ + 0x20)        /* byte per player (2) */
#define FW_WNAME       (FW_FAILOBJ + 0x22)        /* char[32] per player (2) */
#define FW_GS          0xe0e644
#define FW_MERCS       0x1548fd8
#define FW_GM          0xdd265c
#define FW_SYS         0xdd2640
#define FW_SCRIPT_VT   0xbd0954                   /* ZSoldier@CPPScript */
#define FW_PLAYER_VT   0xbb45f4                   /* ZFFPlayer */

typedef struct {
    BYTE *body, *s; int merc, slot;              /* slot: merc list index, -1 = buddy only */
    BYTE able[3], crit, crit2;
    float hp, hpMax, hpLog; DWORD hpT;           /* hp < 0: no valid HP block */
    float posLog[3]; int posOk; DWORD posT, posChk;
    char name[40];
} FwMerc;

static struct {
    int on, pos, hp; float posdist;
    int present; FILETIME ft; DWORD poll; int cfgInit;
    int dead, init, evLines, hpLines;
    BYTE text[0x100]; BYTE flag, wopen[2], gm4d1c; char wname[2][32]; int wplayer;
    DWORD gs, gm, buddy; int lastT;
    char scene[8];
    FwMerc m[17]; int n;
} g_fw;

/* ---------- logging ---------- */
static int fw_ev_ok(void) {
    if (g_fw.evLines >= 5000) return 0;
    if (++g_fw.evLines == 5000) { anp_log("fail: event line cap reached, failwatch event logging stops"); return 0; }
    return 1;
}
static int fw_hp_ok(void) {
    if (g_fw.hpLines >= 10000) return 0;
    if (++g_fw.hpLines == 10000) { anp_log("fail: hp/pos line cap reached, failwatch hp/pos logging stops"); return 0; }
    return 1;
}
static void fw_str(const BYTE *p, int n, char *out, int cap) {   /* printable ASCII as is, others \xNN, stops at NUL */
    int k = 0;
    for (int i = 0; i < n && p[i] && k < cap - 5; i++) {
        BYTE c = p[i];
        if (c >= 32 && c < 127 && c != '\\') out[k++] = (char)c;
        else k += _snprintf(out + k, cap - k, "\\x%02x", c);
    }
    out[k < cap ? k : cap - 1] = 0;
}

/* ---------- reads ---------- */
static DWORD fw32(DWORD a) { return readable((void*)a, 4) ? *(DWORD*)a : 0; }
static int fw_T(void) { DWORD s = fw32(FW_SYS); return (s && readable((void*)(s + 0x48), 4)) ? *(int*)(s + 0x48) : -1; }
/* world point of a node's origin: 0x7b3020's arithmetic on plain reads (node chain via +0x50, max 64 levels) */
static int fw_world(const BYTE *node, float *out) {
    float p[3] = {0, 0, 0};
    for (int d = 0; node; d++) {
        if (d >= 64 || !readable(node, 0x54)) return 0;
        const float *m = (const float*)node, *t = (const float*)(node + 0x24);
        float q0 = p[0] * m[6] + p[1] * m[3] + p[2] * m[0];
        float q1 = p[0] * m[7] + p[1] * m[4] + p[2] * m[1];
        float q2 = p[0] * m[8] + p[1] * m[5] + p[2] * m[2];
        p[0] = q0 + t[0]; p[1] = q1 + t[1]; p[2] = q2 + t[2];
        node = *(const BYTE* const*)(node + 0x50);
    }
    out[0] = p[0]; out[1] = p[1]; out[2] = p[2];
    return 1;
}
static int fw_body_pos(BYTE *body, float *out) { out[0] = out[1] = out[2] = 0; BYTE *node = (BYTE*)fw32((DWORD)(body + 4)); return node && fw_world(node, out); }
static int fw_hpblk(BYTE *obj, DWORD off, float *cur, float *mx) {     /* HP block at obj+off, owner +0x24 == obj */
    BYTE *h = (BYTE*)fw32((DWORD)(obj + off));
    if (!h || !readable(h, 0x28) || *(BYTE**)(h + 0x24) != obj) { *cur = *mx = -1.0f; return 0; }
    *cur = *(float*)(h + 4); *mx = *(float*)(h + 8);
    return 1;
}
static int fw_script(BYTE *s) { return s && readable(s, 0x6f0) && *(DWORD*)s == FW_SCRIPT_VT; }
static BYTE *fw_body_of(BYTE *s) {
    BYTE *b = (BYTE*)fw32((DWORD)(s + 0x40));
    return (b && readable(b, 0x780) && *(BYTE**)(b + 0x77c) == s) ? b : 0;
}
static void fw_name(BYTE *body, char *out, int n) {             /* node name: [body+4]+0x6c (squad.inc sq_name) */
    out[0] = 0;
    const BYTE *p = (const BYTE*)fw32(fw32((DWORD)(body + 4)) + 0x6c);
    if (!p || !readable(p, 1)) return;
    int k = 0; while (k < n - 1 && readable(p + k, 1) && p[k] >= 32 && p[k] < 127) { out[k] = (char)p[k]; k++; }
    out[k] = 0;
}
static BYTE *fw_player(void) {
    DWORD gm = fw32(FW_GM);
    if (!gm || !readable((void*)(gm + 0x828), 0x74)) return 0;
    signed char pi = *(signed char*)(gm + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gm + 0x828 + 4 * pi);
    return (P && readable(P, 0xa4c) && *(DWORD*)P == FW_PLAYER_VT) ? P : 0;
}

/* ---------- config ---------- */
static void fw_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_fw.cfgInit && now - g_fw.poll < 1000) return;
    g_fw.poll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_failwatch.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (g_fw.cfgInit && present == g_fw.present && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_fw.ft) == 0)) return;
    g_fw.cfgInit = 1; g_fw.present = present;
    if (present) g_fw.ft = fa.ftLastWriteTime;
    g_fw.on = present; g_fw.pos = 1; g_fw.hp = 1; g_fw.posdist = 200.0f;   /* opt-in: no ANP_failwatch.txt = off (review) */
    if (present) {
        char buf[512] = "";
        FILE *f = fopen(fn, "r");
        if (f) { size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f); }
        for (char *p = buf; (p = strchr(p, '#')); ) while (*p && *p != '\n') *p++ = ' ';
        for (char *t = strtok(buf, " \t\r\n,;"); t; t = strtok(NULL, " \t\r\n,;")) {
            if (!_stricmp(t, "off")) g_fw.on = 0;
            else if (!_stricmp(t, "on")) g_fw.on = 1;
            else if (!_strnicmp(t, "pos=", 4)) g_fw.pos = atoi(t + 4) != 0;
            else if (!_strnicmp(t, "posdist=", 8)) { float d = (float)atof(t + 8); g_fw.posdist = d < 10.0f ? 10.0f : d; }
            else if (!_strnicmp(t, "hp=", 3)) g_fw.hp = atoi(t + 3) != 0;
            else anp_log("fail: ANP_failwatch.txt token '%s' unknown (ignored)", t);
        }
    }
    anp_log("fail: failwatch %s (pos=%d posdist=%.0f hp=%d)%s", g_fw.on ? "on" : "OFF", g_fw.pos, (double)g_fw.posdist, g_fw.hp,
            present ? " (ANP_failwatch.txt)" : " (no ANP_failwatch.txt: defaults)");
}

/* ---------- snapshot: player + every tracked merc ---------- */
static void fw_merc_line(const char *tag, FwMerc *r) {
    float p[3]; int pk = fw_body_pos(r->body, p);
    if (!fw_ev_ok()) return;
    anp_log("fail: %s merc[%d] id=%d '%s' body=%p script=%p able(+574/5/6)=%d/%d/%d hp=%.1f/%.1f crit(+513)=%d +512=%d pos=%s(%.0f,%.0f,%.0f)",
            tag, r->slot, r->merc, r->name, r->body, r->s, r->able[0], r->able[1], r->able[2], (double)r->hp, (double)r->hpMax,
            r->crit, r->crit2, pk ? "" : "?", (double)p[0], (double)p[1], (double)p[2]);
}
static void fw_snapshot(const char *why) {
    BYTE *P = fw_player();
    if (fw_ev_ok()) {
        if (P) {
            float hp, mx, p[3] = {0, 0, 0}; fw_hpblk(P, 0xa48, &hp, &mx);
            int pk = fw_body_pos(P, p);
            anp_log("fail: snapshot (%s) scene=%s T=%d gs=%lu player=%p hp=%.1f/%.1f pos=%s(%.0f,%.0f,%.0f) mercs=%d list=%ld buddy=%08lx",
                    why, g_fw.scene, fw_T(), fw32(FW_GS), P, (double)hp, (double)mx, pk ? "" : "?", (double)p[0], (double)p[1], (double)p[2],
                    g_fw.n, (long)fw32(FW_MERCS), g_fw.buddy);
        } else
            anp_log("fail: snapshot (%s) scene=%s T=%d gs=%lu player=none mercs=%d list=%ld buddy=%08lx",
                    why, g_fw.scene, fw_T(), fw32(FW_GS), g_fw.n, (long)fw32(FW_MERCS), g_fw.buddy);
    }
    for (int i = 0; i < g_fw.n; i++) fw_merc_line("  ", &g_fw.m[i]);
}

/* ---------- (1) fail text, flag, fail window, gm+0x4d1c ---------- */
static void fw_fail(void) {
    if (!readable((void*)FW_FAILOBJ, 0x348)) return;
    const BYTE *txt = (const BYTE*)FW_TEXT;
    BYTE flag = *(BYTE*)FW_FLAG;
    DWORD gm = fw32(FW_GM);
    BYTE g4d = (gm && readable((void*)(gm + 0x4d1c), 1)) ? *(BYTE*)(gm + 0x4d1c) : 0xff;
    int wp = *(int*)FW_WPLAYER;
    char s[0x180];
    if (!g_fw.init) {
        memcpy(g_fw.text, txt, sizeof g_fw.text); g_fw.flag = flag; g_fw.gm4d1c = g4d; g_fw.wplayer = wp;
        for (int p = 0; p < 2; p++) { g_fw.wopen[p] = *(BYTE*)(FW_WOPEN + p); memcpy(g_fw.wname[p], (void*)(FW_WNAME + 32 * p), 32); }
        g_fw.gs = fw32(FW_GS);
        fw_str(txt, 0x100, s, sizeof s);
        char w0[48]; fw_str((const BYTE*)g_fw.wname[0], 32, w0, sizeof w0);
        if (fw_ev_ok()) anp_log("fail: watch start: text '%s' flag=%d window0 open=%d '%s' (+1c=%d) gm+4d1c=%d gs=%lu",
                                s, flag, g_fw.wopen[0], w0, wp, g4d, g_fw.gs);
        g_fw.init = 1;
        return;
    }
    int snap = 0;
    if (memcmp(txt, g_fw.text, sizeof g_fw.text) || flag != g_fw.flag) {
        char old[0x180]; fw_str(g_fw.text, 0x100, old, sizeof old); fw_str(txt, 0x100, s, sizeof s);
        if (fw_ev_ok()) anp_log("fail: %s flag %d->%d text '%s'%s%s%s scene=%s T=%d gs=%lu", memcmp(txt, g_fw.text, sizeof g_fw.text) ? "TEXT" : "flag",
                                g_fw.flag, flag, s, strcmp(old, s) ? " (was '" : "", strcmp(old, s) ? old : "", strcmp(old, s) ? "')" : "",
                                g_fw.scene, fw_T(), fw32(FW_GS));
        if (memcmp(txt, g_fw.text, sizeof g_fw.text)) snap = 1;
        memcpy(g_fw.text, txt, sizeof g_fw.text); g_fw.flag = flag;
    }
    for (int p = 0; p < 2; p++) {
        BYTE o = *(BYTE*)(FW_WOPEN + p); const char *nm = (const char*)(FW_WNAME + 32 * p);
        if (o != g_fw.wopen[p] || memcmp(nm, g_fw.wname[p], 32)) {
            char w[48]; fw_str((const BYTE*)nm, 32, w, sizeof w);
            fw_str(txt, 0x100, s, sizeof s);
            if (fw_ev_ok()) anp_log("fail: window[%d] open %d->%d '%s' (+1c=%d) text '%s' scene=%s T=%d", p, g_fw.wopen[p], o, w, wp, s, g_fw.scene, fw_T());
            if (o && !g_fw.wopen[p] && !strncmp(nm, "MissionFailed", 13)) snap = 1;
            g_fw.wopen[p] = o; memcpy(g_fw.wname[p], nm, 32);
        }
    }
    if (wp != g_fw.wplayer) g_fw.wplayer = wp;              /* shown in the window lines only */
    if (g4d != g_fw.gm4d1c) {
        if (fw_ev_ok()) anp_log("fail: gm+4d1c %d->%d (gm %08lx) T=%d", g_fw.gm4d1c, g4d, gm, fw_T());
        g_fw.gm4d1c = g4d;
    }
    if (snap) fw_snapshot("fail");
}

/* ---------- (2) mercs ---------- */
static FwMerc *fw_find(BYTE *body) { for (int i = 0; i < g_fw.n; i++) if (g_fw.m[i].body == body) return &g_fw.m[i]; return 0; }
static void fw_read_merc(FwMerc *r) {
    BYTE *b = r->body, *s = r->s;
    r->able[0] = b[0x574]; r->able[1] = b[0x575]; r->able[2] = b[0x576];
    r->crit = s[0x513]; r->crit2 = s[0x512];
    r->merc = *(int*)(s + 0x6e8);
    fw_hpblk(b, 0x5fc, &r->hp, &r->hpMax);
}
static void fw_mercs(DWORD now) {
    BYTE *cb[17], *cs[17]; int cslot[17], cn = 0;
    int nl = (int)fw32(FW_MERCS); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (int i = 0; i < nl; i++) {
        BYTE *s = (BYTE*)fw32(FW_MERCS + 4 + 4 * i), *b;
        if (!fw_script(s) || !(b = fw_body_of(s))) continue;
        int dup = 0; for (int k = 0; k < cn; k++) dup |= cb[k] == b;
        if (!dup) { cb[cn] = b; cs[cn] = s; cslot[cn] = i; cn++; }
    }
    DWORD gm = fw32(FW_GM), bud = gm ? fw32(gm + 0x4cf0) : 0;
    if (bud != g_fw.buddy) {
        if (fw_ev_ok()) anp_log("fail: buddy gm+4cf0 %08lx -> %08lx (%s) T=%d", g_fw.buddy, bud, bud ? rtti_name((void*)bud) : "-", fw_T());
        g_fw.buddy = bud;
    }
    if (bud && readable((void*)bud, 0x780)) {
        BYTE *b = (BYTE*)bud, *s = *(BYTE**)(b + 0x77c);
        int dup = 0; for (int k = 0; k < cn; k++) dup |= cb[k] == b;
        if (!dup && fw_script(s) && fw_body_of(s) == b && cn < 17) { cb[cn] = b; cs[cn] = s; cslot[cn] = -1; cn++; }
    }
    /* gone */
    for (int i = 0; i < g_fw.n; ) {
        int still = 0; for (int k = 0; k < cn; k++) still |= cb[k] == g_fw.m[i].body && cs[k] == g_fw.m[i].s;
        if (still) { i++; continue; }
        if (fw_ev_ok()) anp_log("fail: merc[%d] id=%d '%s' body=%p GONE (no longer listed / not valid) T=%d", g_fw.m[i].slot, g_fw.m[i].merc,
                                g_fw.m[i].name, g_fw.m[i].body, fw_T());
        g_fw.m[i] = g_fw.m[--g_fw.n];
    }
    /* new + changes */
    for (int k = 0; k < cn; k++) {
        FwMerc *r = fw_find(cb[k]);
        if (!r) {
            if (g_fw.n >= 17) continue;
            r = &g_fw.m[g_fw.n++]; memset(r, 0, sizeof *r);
            r->body = cb[k]; r->s = cs[k]; r->slot = cslot[k];
            fw_name(r->body, r->name, sizeof r->name);
            fw_read_merc(r);
            r->hpLog = r->hp; r->hpT = now;
            r->posOk = fw_body_pos(r->body, r->posLog); r->posT = now;
            fw_merc_line("NEW", r);
            if (fw_ev_ok()) anp_log("fail:   merc[%d] body class %s, buddy=%d", r->slot, rtti_name(r->body), (DWORD)r->body == g_fw.buddy);
            continue;
        }
        r->slot = cslot[k];
        FwMerc o = *r;
        fw_read_merc(r);
        if (r->able[2] != o.able[2] || r->crit != o.crit || r->crit2 != o.crit2 || r->merc != o.merc) {
            float p[3]; int pk = fw_body_pos(r->body, p);
            if (fw_ev_ok()) anp_log("fail: merc[%d] id=%d '%s'%s%s able %d->%d (+574/5 %d/%d) crit(+513) %d->%d +512 %d->%d hp=%.1f/%.1f pos=%s(%.0f,%.0f,%.0f) T=%d gs=%lu",
                                    r->slot, r->merc, r->name, r->able[2] != o.able[2] && !r->able[2] ? " DOWN/DEAD" : "",
                                    r->merc != o.merc ? " (merc id changed)" : "", o.able[2], r->able[2], r->able[0], r->able[1],
                                    o.crit, r->crit, o.crit2, r->crit2, (double)r->hp, (double)r->hpMax, pk ? "" : "?",
                                    (double)p[0], (double)p[1], (double)p[2], fw_T(), fw32(FW_GS));
        }
        if (g_fw.hp && r->hp >= 0 && r->hp != r->hpLog) {
            int drop = r->hp < r->hpLog - 0.01f, rise = r->hp > r->hpLog + 0.01f;
            if ((drop && now - r->hpT >= 100) || (rise && (now - r->hpT >= 1000 || r->hp >= r->hpMax))) {
                if (fw_hp_ok()) anp_log("fail: merc[%d] id=%d '%s' hp %.1f->%.1f (%+.1f) max %.1f able=%d T=%d", r->slot, r->merc, r->name,
                                        (double)r->hpLog, (double)r->hp, (double)(r->hp - r->hpLog), (double)r->hpMax, r->able[2], fw_T());
                r->hpLog = r->hp; r->hpT = now;
            }
        } else if (r->hp < 0) r->hpLog = r->hp;
        if (g_fw.pos && now - r->posChk >= 1000) {
            r->posChk = now;                              /* position walk at most 1/s even while still (review) */
            float p[3];
            if (fw_body_pos(r->body, p)) {
                float dx = p[0] - r->posLog[0], dy = p[1] - r->posLog[1], dz = p[2] - r->posLog[2];
                if (!r->posOk || dx * dx + dy * dy + dz * dz > g_fw.posdist * g_fw.posdist) {
                    if (fw_hp_ok()) anp_log("fail: merc[%d] id=%d '%s' pos (%.0f,%.0f,%.0f) moved %.0f able=%d hp=%.1f T=%d", r->slot, r->merc, r->name,
                                            (double)p[0], (double)p[1], (double)p[2], r->posOk ? (double)sqrtf(dx * dx + dy * dy + dz * dz) : 0.0,
                                            r->able[2], (double)r->hp, fw_T());
                    memcpy(r->posLog, p, sizeof p); r->posOk = 1; r->posT = now;
                }
            }
        }
    }
}

/* ---------- tick ---------- */
static int fw_tick_body(void *unused) {
    (void)unused;
    fw_cfg_poll();
    if (!g_fw.on) return 0;
    DWORD now = GetTickCount();
    char sc[8]; EnterCriticalSection(&g_cmpCs); memcpy(sc, g_cscene, sizeof sc); LeaveCriticalSection(&g_cmpCs); sc[7] = 0;
    int T = fw_T();
    if (strcmp(sc, g_fw.scene) || (T >= 0 && g_fw.lastT >= 0 && T < g_fw.lastT && g_fw.n)) {   /* new scene / clock went back */
        if (g_fw.n && fw_ev_ok()) anp_log("fail: %s ('%s' -> '%s', T %d -> %d): %d merc records dropped", strcmp(sc, g_fw.scene) ? "scene change" : "engine clock went back",
                                          g_fw.scene, sc, g_fw.lastT, T, g_fw.n);
        g_fw.n = 0; memcpy(g_fw.scene, sc, sizeof sc);
    }
    g_fw.lastT = T;
    fw_mercs(now);                                    /* before fw_fail(): snapshots show this tick (review) */
    fw_fail();
    DWORD gs = fw32(FW_GS);
    if (g_fw.init && gs != g_fw.gs) {
        char s[0x180]; fw_str((const BYTE*)FW_TEXT, 0x100, s, sizeof s);
        if (fw_ev_ok()) anp_log("fail: STATE counter [e0e644] %lu -> %lu scene=%s T=%d (fail text '%s' flag=%d)", g_fw.gs, gs, sc, T, s, g_fw.flag);
        g_fw.gs = gs;
        fw_snapshot("state change");
    }
    return 0;
}
static void failwatch_frame(void) {
    if (g_fw.dead) return;
    if (climb_guarded("failwatch tick", fw_tick_body, 0) < 0) {
        g_fw.dead = 1;
        anp_log("fail: failwatch DISABLED for this session (fault in its tick, see the 'climb: FAULT' line above)");
    }
}
