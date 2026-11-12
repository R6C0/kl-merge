/* ANP campaigns (Dead Men / Dog Days / Dead Dogs): loader side.
   Included by anp_loader.c after do_load() (uses anp_log, readable, rtti_name, node_table, node_of, log_obj_strings,
   hook_iat, do_load, g_dir). No kl2 code bytes are changed here: everything is import-slot hooks (strncpy, fopen,
   CreateFileA via anp_loader.c, ExitProcess), .data/heap writes (scene table entry 12, the achievements object's
   and the file system object's vptrs)
   and engine calls made from the PeekMessageA import hook on the main thread (campaign_tick).

   Hooks into anp_loader.c (kept to a few lines):
     - my_CreateFileA: n = campaign_file(n, access, disposition) before the real call;
     - my_PeekMessageA: campaign_tick(now);
     - DllMain: campaign_init() first; the old 0x6d100f resolver patch only if campaign_legacy_resolver().

   Config: <DD>\ANP_campaign.txt, lines "Key=Value" (# or ; comments). A missing file or key = the default below.
     Routing=1          scene ids via the MSVCR90 strncpy import (SetId 0x869d00 / story start 0x874a69 copy the id
                        with strncpy(0x156b6f5, id, 4)): pseudo ids DMCN / DGNW / DGCN, campaign mode, and ANP ids
                        resolved through scene-table entry 12 (0xcef760, "AM01" -> AttractMode.zip, unused).
     LegacyResolver=0   the old jmp patch at 0x6d100f (CEG-hashed code). Only when set explicitly (11 Oct: no longer
                        forced on when the strncpy import can't be hooked; the log says so instead).
     Menu=1             Patch01.zip / KL2FixPatch01.zip opens read <DD>\ANP\ANP_Patch01.zip instead when that file
                        exists (built by tools/anp_menu.py): the CreateFileA existence probe (Mount 0x809200 ->
                        0x5e2aa0) AND the MSVCR90 fopen import (0xb10430) that really loads the archive (cmp_fopen).
     MenuXml=1          (with Menu=1) the file system object's vptr points at a vtable copy whose size/read slots
                        serve menu/frontend.xml from <DD>\ANP\menu\frontend.xml when that file exists (cmp_fs_size /
                        cmp_fs_read); either way the log names the copy the menu loader got.
     SaveRedirect=1     in Dead Men / Dead Dogs mode, <n>.kls opens go to
                        %LOCALAPPDATA%\A Newer Perspective\saves\<DeadMen|DeadDogs>\<n>.kls (seeded by copying
                        Dog Days' file the first time). Dog Days' own save is never written in those modes.
     ProfileReload=1    back at the front end after a Dead Men / Dead Dogs session: redirect off and Dog Days'
                        profile re-read ([0x1686e71]=1; 0x47c5f0(0x1686e60, 0), the stock chapter selector's call),
                        in one main-thread step. With 0 the redirect stays on for the rest of the session instead.
                        The reload is checked: unless the reader really opened the Dog Days save (the 0x7aeb10 probe
                        + the 0x47c73a read), the Dead Men / Dead Dogs slot stays live for the rest of the session, so
                        a profile still holding Dead Men state can never be written over Dog Days' save.
     ReloadDelayMs=2000 how long after the front end's last scene-zip open that step waits; the main thread must also
                        have been pumping messages steadily for a second (= not loading). Leaving a Dead Men / Dead
                        Dogs slot for Dog Days from a menu request before then reloads at once.
     AchievementGuard=1 while a Dead Men scene runs (Dead Men mode, or Dead Dogs on an M level) the static
                        ZAchievementsSteam object (0x156c108) gets a vtable copy whose slot 3 (award, 0x72fd60)
                        only logs. Stock vptr put back otherwise.
     Progress=1         %LOCALAPPDATA%\A Newer Perspective\ANP_progress.ini: [DeadMen] last/reached/done,
                        [Saga] pos/done, from the scene zips the game opens.
     DeadDogsHandover=1 Dead Dogs: when the front end loads after Dead Men's last chapter (M14, or M13B's credits
                        exit) without a QuitGame request, L00 is started (do_load) in Dead Dogs mode.
     ExitTripwire=1     ExitProcess import wrapper: logs the exit code and caller (0x8000dead = Valve CEG check).
     IntroMovie=1       _BinkOpen@8 / _BinkClose@4 import hooks: when the ANP intro movie (Movies/ANP/M00_Intro, played
                        by the menu's New game / New saga pages, tools/anp_menu.py --intro) ends or is skipped, start
                        M01 (Dead Men) or DGNW (Dead Dogs) from the main thread. 0 = the pages' fallback button only.
     IntroDelayMs=200   wait after the movie closes before that request.
   Scene ids: ANP ids are Scenes\Locations\<id>\<id>_Main.zip, except those in CMP_ALIAS (M07F = the funeral,
   Scenes\CutScenes\M07\M07_A_Funeral.zip).

   Test hooks (files in the DD folder, polled about twice a second on the main thread, deleted when served):
   - ANP_load.txt      "<id> [mode]"  -> SetId(id) + Start, like the autoload (do_load). Pseudo ids work too.
   - ANP_endlevel.txt  ["<substring>" | "list"]  -> fire the level's ZSceneChanger (see cmp_endlevel).
   - ANP_cstate.txt    -> log the campaign state (mode, scene, pending steps, progress ini, save slot files).
   - ANP_guinames.txt  [words...] -> log the open GUI windows with the strings found in each object, and how many
                        copies of each word (default: the three ANP window names) are in committed memory. */

#define CMP_SCENECHANGER_VT  0xbc374c
#define CMP_ACH_OBJ          0x156c108
#define CMP_ACH_VT           0xbc0d00
#define CMP_REQ_ID           ((char*)0x156b6f5)     /* 0x156b3b0 + 0x345: 4 chars, NUL at +0x349 */
#define CMP_SCN_TABLE        ((DWORD*)0xcef700)     /* {const char *id, const char *path} x 22, .data */
#define CMP_BORROW           12                     /* "AM01" -> "AttractMode.zip" */
#define CMP_AM01_ID          0xb70604
#define CMP_AM01_PATH        0xb84534
#define CMP_PROFILE          ((void*)0x1686e60)
#define CMP_PROFILE_FLAG     ((BYTE*)0x1686e71)
#define CMP_PROFILE_READ     0x47c5f0
#define CMP_PRESSSTART_DONE  ((BYTE*)0x156b742)

enum { CM_DOGDAYS = 0, CM_DEADMEN = 1, CM_DEADDOGS = 2 };
static const char *const CM_NAME[] = {"DogDays", "DeadMen", "DeadDogs"};
/* M07F = the funeral cutscene between M07 and M08 (a scene of its own; see CMP_ALIAS) */
static const char *const CMP_DM_ORDER[] = {"M01", "M02", "M03", "M03B", "M05", "M06", "M07", "M07F", "M08", "M09", "M09B",
                                           "M11", "M11B", "M12", "M13", "M13B", "M14", 0};
/* ANP ids whose scene is not Scenes\Locations\<id>\<id>_Main.zip (tools/port_level.py SPECIAL_SCENES). The funeral
   keeps Dead Men's path: kl2's scene bookkeeping (0x881350 start / 0x696c40 end) skips chapter index, LevelOfDetail and
   the profile save for any scene path containing "Funeral", as Dead Men does. M07's SceneChanger loads it by path
   (no id needed); the id is for ANP_load.txt, Continue (DMCN / DGCN after quitting mid-funeral) and progress. */
static const struct { const char *id, *path; } CMP_ALIAS[] = {
    {"M07F", "CutScenes/M07/M07_A_Funeral.zip"},
    {0, 0}};

static struct { int routing, legacy, menu, saves, reload, reloadDelay, ach, progress, handover, tripwire, menuXml,
                intro, introDelay; } g_cc =
    {1, 0, 1, 1, 1, 2000, 1, 1, 1, 1, 1, 1, 200};

static CRITICAL_SECTION g_cmpCs;
static volatile int g_cmode = CM_DOGDAYS;          /* campaign mode = which save slot is live */
static char g_cscene[8] = "";                       /* scene now loaded: "FE" front end, an id, "" = before boot */
static char g_cprev[8] = "";                        /* scene before it */
static volatile int g_cArmed;                       /* patch archive opened = a scene load started */
static volatile int g_cAtFE = 1;                    /* front end loaded (or booting) */
static volatile DWORD g_feTick;                     /* when the front end started loading */
static volatile int g_reloadPending, g_handoverPending, g_handoverReq;
static volatile int g_quitReq;                      /* last scene request was MM01 (QuitGame / back to menu) */
static volatile int g_stickyMode = -1;              /* ProfileReload=0: the slot kept for the session */
static char g_rid[8], g_rpath[64];                  /* scene-table entry 12 while an ANP id is requested */
static char g_appDir[MAX_PATH], g_iniPath[MAX_PATH], g_menuAlt[MAX_PATH], g_menuXml[MAX_PATH];
static volatile int g_cReloadProbe;                 /* main thread inside cmp_profile_reload */
static volatile LONG g_cReloadOpens;                /* .kls read opens seen during it */
static void *volatile g_introBink;                  /* Bink handle of the ANP intro movie while it plays */
static volatile int g_introSaga;                    /* that movie was opened by the Dead Dogs page (New saga) */
static volatile int g_introPending;                 /* 1 = it ended: start the campaign at g_introTick + IntroDelayMs */
static volatile DWORD g_introTick;

typedef char *(__cdecl *cmp_strncpy_t)(char *, const char *, size_t);
static cmp_strncpy_t real_strncpy_c;
typedef void (WINAPI *cmp_exit_t)(UINT);
static cmp_exit_t real_ExitProcess_c;
typedef int (__attribute__((thiscall)) *cmp_reader_t)(void *self, int slot);
typedef void (__attribute__((thiscall)) *cmp_slot34_t)(void *self);

/* ------------------------------------------------------------------ config, paths, progress ini */
static int cmp_cfg_key(const char *k, const char *name) { return _stricmp(k, name) == 0; }
static void cmp_config_load(void) {
    char p[MAX_PATH], line[256]; _snprintf(p, sizeof p, "%s\\ANP_campaign.txt", g_dir);
    FILE *f = fopen(p, "r");
    if (f) {
        while (fgets(line, sizeof line, f)) {
            char *s = line; while (*s == ' ' || *s == '\t') s++;
            if (*s == '#' || *s == ';' || *s == '[' || !*s) continue;
            char *eq = strchr(s, '='); if (!eq) continue;
            *eq = 0; char *k = s, *v = eq + 1;
            char *e = k + strlen(k); while (e > k && (e[-1] == ' ' || e[-1] == '\t')) *--e = 0;
            int val = atoi(v);
            if (cmp_cfg_key(k, "Routing")) g_cc.routing = val;
            else if (cmp_cfg_key(k, "LegacyResolver")) g_cc.legacy = val;
            else if (cmp_cfg_key(k, "Menu")) g_cc.menu = val;
            else if (cmp_cfg_key(k, "SaveRedirect")) g_cc.saves = val;
            else if (cmp_cfg_key(k, "ProfileReload")) g_cc.reload = val;
            else if (cmp_cfg_key(k, "ReloadDelayMs")) g_cc.reloadDelay = val;
            else if (cmp_cfg_key(k, "AchievementGuard")) g_cc.ach = val;
            else if (cmp_cfg_key(k, "Progress")) g_cc.progress = val;
            else if (cmp_cfg_key(k, "DeadDogsHandover")) g_cc.handover = val;
            else if (cmp_cfg_key(k, "ExitTripwire")) g_cc.tripwire = val;
            else if (cmp_cfg_key(k, "MenuXml")) g_cc.menuXml = val;
            else if (cmp_cfg_key(k, "IntroMovie")) g_cc.intro = val;
            else if (cmp_cfg_key(k, "IntroDelayMs")) g_cc.introDelay = val;
            else anp_log("campaign: unknown key '%s' in ANP_campaign.txt", k);
        }
        fclose(f);
    }
    anp_log("campaign: config (%s) Routing=%d LegacyResolver=%d Menu=%d SaveRedirect=%d ProfileReload=%d ReloadDelayMs=%d "
            "AchievementGuard=%d Progress=%d DeadDogsHandover=%d ExitTripwire=%d MenuXml=%d IntroMovie=%d IntroDelayMs=%d",
            f ? "ANP_campaign.txt" : "defaults",
            g_cc.routing, g_cc.legacy, g_cc.menu, g_cc.saves, g_cc.reload, g_cc.reloadDelay, g_cc.ach, g_cc.progress,
            g_cc.handover, g_cc.tripwire, g_cc.menuXml, g_cc.intro, g_cc.introDelay);
}

static void cmp_mkdirs(const char *dir) {            /* create every level of an absolute path */
    char t[MAX_PATH]; _snprintf(t, sizeof t, "%s", dir);
    for (char *p = t + 3; *p; p++) if (*p == '\\') { *p = 0; CreateDirectoryA(t, NULL); *p = '\\'; }
    CreateDirectoryA(t, NULL);
}

static void cmp_paths_init(void) {
    char la[MAX_PATH] = "";
    DWORD n = GetEnvironmentVariableA("LOCALAPPDATA", la, sizeof la);
    if (n && n < sizeof la) _snprintf(g_appDir, sizeof g_appDir, "%s\\A Newer Perspective", la);
    else _snprintf(g_appDir, sizeof g_appDir, "%s\\ANP\\appdata", g_dir);        /* no LOCALAPPDATA: game folder */
    _snprintf(g_iniPath, sizeof g_iniPath, "%s\\ANP_progress.ini", g_appDir);
    _snprintf(g_menuAlt, sizeof g_menuAlt, "%s\\ANP\\ANP_Patch01.zip", g_dir);   /* constant: no shared scratch buffer */
    _snprintf(g_menuXml, sizeof g_menuXml, "%s\\ANP\\menu\\frontend.xml", g_dir);
    g_appDir[MAX_PATH - 1] = g_iniPath[MAX_PATH - 1] = g_menuAlt[MAX_PATH - 1] = g_menuXml[MAX_PATH - 1] = 0;  /* _snprintf may not terminate */
}

static void cmp_ini_get(const char *sec, const char *key, const char *def, char *out, int n) {
    GetPrivateProfileStringA(sec, key, def, out, n, g_iniPath);
}
static void cmp_ini_set(const char *sec, const char *key, const char *val) {
    if (!g_cc.progress) return;
    char cur[64]; cmp_ini_get(sec, key, "\x01", cur, sizeof cur);
    if (strcmp(cur, val) == 0) return;
    cmp_mkdirs(g_appDir);
    if (WritePrivateProfileStringA(sec, key, val, g_iniPath)) anp_log("campaign: progress [%s] %s=%s", sec, key, val);
    else anp_log("campaign: progress write failed (%lu) %s", GetLastError(), g_iniPath);
}

/* ------------------------------------------------------------------ scene ids */
static int cmp_dm_index(const char *id) {
    for (int i = 0; CMP_DM_ORDER[i]; i++) if (_stricmp(CMP_DM_ORDER[i], id) == 0) return i;
    return -1;
}
static int cmp_stock_id(const char *id) {
    if (_stricmp(id, "L00") == 0) return 1;                       /* resolver special case (0xb230dc) */
    for (int i = 0; i < 22; i++) {
        if (i == CMP_BORROW) continue;
        const char *s = (const char*)CMP_SCN_TABLE[2 * i];
        if (s && readable(s, 1) && strcmp(s, id) == 0) return 1;
    }
    return _stricmp(id, "AM01") == 0;
}
static const char *cmp_alias(const char *id) {                    /* CMP_ALIAS path (under Scenes) or NULL */
    for (int i = 0; CMP_ALIAS[i].id; i++) if (_stricmp(CMP_ALIAS[i].id, id) == 0) return CMP_ALIAS[i].path;
    return NULL;
}
static int cmp_anp_id(const char *id) {                            /* Scenes\Locations\<id>\<id>_Main.zip exists */
    char p[MAX_PATH];
    if (!id[0] || strlen(id) > 4 || strpbrk(id, "\\/.:") || cmp_stock_id(id)) return 0;
    const char *al = cmp_alias(id);
    if (al) {                                                       /* Scenes\<alias path> exists */
        int k = _snprintf(p, sizeof p, "%s\\Scenes\\%s", g_dir, al);
        if (k < 0 || k >= (int)sizeof p) return 0;
        for (char *c = p; *c; c++) if (*c == '/') *c = '\\';
    } else _snprintf(p, sizeof p, "%s\\Scenes\\Locations\\%s\\%s_Main.zip", g_dir, id, id);
    p[MAX_PATH - 1] = 0;
    return GetFileAttributesA(p) != INVALID_FILE_ATTRIBUTES;
}
static int cmp_valid_target(const char *id) { return id[0] && (cmp_anp_id(id) || cmp_stock_id(id)); }

static void cmp_table_entry(const char *id) {                      /* NULL = stock AM01 entry */
    DWORD *e = &CMP_SCN_TABLE[2 * CMP_BORROW], want0, want1, old;
    if (id) {
        const char *al = cmp_alias(id);
        _snprintf(g_rid, sizeof g_rid, "%s", id);
        if (al) _snprintf(g_rpath, sizeof g_rpath, "%s", al);       /* keeps 'Funeral' in the scene path */
        else _snprintf(g_rpath, sizeof g_rpath, "Locations/%s/%s_Main.zip", id, id);
        g_rpath[sizeof g_rpath - 1] = 0;
        want0 = (DWORD)g_rid; want1 = (DWORD)g_rpath;
    } else { want0 = CMP_AM01_ID; want1 = CMP_AM01_PATH; }
    if (e[0] == want0 && e[1] == want1) return;
    if (!VirtualProtect(e, 8, PAGE_READWRITE, &old)) { anp_log("campaign: scene table not writable (%lu)", GetLastError()); return; }
    e[0] = want0; e[1] = want1;
    VirtualProtect(e, 8, old, &old);
}

/* ------------------------------------------------------------------ mode, profile reload */
static void cmp_set_mode(int m, const char *why) {
    if (m == g_cmode) return;
    anp_log("campaign: mode %s -> %s (%s)%s", CM_NAME[g_cmode], CM_NAME[m], why,
            g_cc.saves ? (m == CM_DOGDAYS ? "; save redirect off" : "; save redirect on") : "");
    g_cmode = m;
}

/* Leaves the Dead Men / Dead Dogs slot for Dog Days' own. Main thread only. Invariant kept here: the mode becomes
   Dog Days (= redirect off) only together with a profile that was really re-read from Dog Days' save. The reader
   0x47c5f0 has a branch (slot vt+0x3c true, 0x47c657) that re-applies the in-memory profile without opening the
   file; then (or if the file can't be opened) the old slot stays live for the session instead. */
static void cmp_profile_reload(const char *why) {
    int prev = g_cmode;
    g_reloadPending = 0;
    if (!*CMP_PRESSSTART_DONE) {                                   /* reader and writer are no-ops before Press Start */
        cmp_set_mode(CM_DOGDAYS, why);
        anp_log("campaign: profile reload skipped (no profile loaded: Press Start not done)");
        return;
    }
    anp_log("campaign: profile reload: Dog Days profile re-read from its own save (%s)", why);
    cmp_set_mode(CM_DOGDAYS, why);
    g_cReloadOpens = 0; g_cReloadProbe = 1;
    *CMP_PROFILE_FLAG = 1;
    int r = ((cmp_reader_t)CMP_PROFILE_READ)(CMP_PROFILE, 0);
    g_cReloadProbe = 0;
    if (g_cReloadOpens >= 2 || prev == CM_DOGDAYS) {
        anp_log("campaign: profile reload done (%d), save file opened %ld time(s): read from disk", r, (long)g_cReloadOpens);
        return;
    }
    g_cmode = prev; g_stickyMode = prev;
    anp_log("campaign: profile reload did NOT re-read the Dog Days save (%ld open(s), result %d): the %s slot stays live "
            "for the rest of this session so Dog Days' save is never written with this profile", (long)g_cReloadOpens, r,
            CM_NAME[prev]);
}

/* ------------------------------------------------------------------ strncpy: scene requests */
static char *__cdecl cmp_strncpy(char *dst, const char *src, size_t n) {
    if (dst != CMP_REQ_ID || n != 4 || !src) return real_strncpy_c(dst, src, n);
    void *ra = __builtin_return_address(0);
    char asked[8] = "", id[8];
    for (int i = 0; i < 4 && src[i]; i++) asked[i] = src[i];
    strcpy(id, asked);
    int cur = g_cmode, m = cur, pseudo = 1, handover = g_handoverReq;
    g_handoverReq = 0;
    if (!strcmp(asked, "DMCN")) {
        char v[16]; cmp_ini_get("DeadMen", "last", "M01", v, sizeof v); v[4] = 0;
        _snprintf(id, sizeof id, "%s", cmp_anp_id(v) ? v : "M01"); m = CM_DEADMEN;
    } else if (!strcmp(asked, "DGNW")) {
        strcpy(id, "M01"); m = CM_DEADDOGS;
        cmp_ini_set("Saga", "pos", "M01"); cmp_ini_set("Saga", "done", "0");
    } else if (!strcmp(asked, "DGCN")) {
        char v[16]; cmp_ini_get("Saga", "pos", "M01", v, sizeof v); v[4] = 0;
        _snprintf(id, sizeof id, "%s", cmp_valid_target(v) ? v : "M01"); m = CM_DEADDOGS;
    } else {
        pseudo = 0;
        int anp = cmp_anp_id(id);
        if (handover) m = CM_DEADDOGS;
        else if (anp) m = (cur == CM_DEADDOGS && !g_cAtFE) ? CM_DEADDOGS : CM_DEADMEN;
        else if (g_cAtFE && strcmp(id, "MM01")) m = CM_DOGDAYS;      /* a stock flow from the menu */
        /* else: in-game stock request (MM01 = back to the menu, restarts...): keep the mode until the front end */
    }
    if (g_stickyMode >= 0 && m == CM_DOGDAYS) m = g_stickyMode;      /* ProfileReload=0, or a failed reload */
    if (g_handoverPending && !handover) {                          /* the player acted before the hand-over ran */
        g_handoverPending = 0;
        anp_log("campaign: Dead Dogs hand-over cancelled by a menu request ('%s')", id);
    }
    if (g_introPending) {                                          /* e.g. the fallback button was quicker */
        g_introPending = 0;
        anp_log("campaign: intro: automatic start dropped, scene requested first ('%s')", asked);
    }
    if (m == CM_DOGDAYS && cur != CM_DOGDAYS) {                    /* leaving a Dead Men / Dead Dogs slot */
        if (g_cc.reload) {
            cmp_profile_reload("scene request from the front end");
            anp_log("campaign: warning: the profile was reloaded only at this request; a Resume / Story start may "
                    "already have read chapter and checkpoint from the %s session", CM_NAME[cur]);
            if (g_stickyMode >= 0) m = g_stickyMode;                /* reload failed: stay on the slot */
        } else { g_stickyMode = cur; m = cur; }
    } else if (g_reloadPending && m != CM_DOGDAYS) {
        g_reloadPending = 0; anp_log("campaign: profile reload dropped (next scene is %s again)", CM_NAME[m]);
    }
    int anpId = cmp_anp_id(id);
    if (g_cc.routing) cmp_table_entry(anpId ? id : NULL);
    if (anpId) {                                                    /* as the autoload does */
        DWORD app = *(DWORD*)0xdd2640;
        if (app && readable((void*)(app + 0xac), 4)) { DWORD sub = *(DWORD*)(app + 0xac); if (sub && readable((void*)(sub + 0xb8), 4)) *(DWORD*)(sub + 0xb8) = 1; }
    }
    g_quitReq = strcmp(id, "MM01") == 0;
    cmp_set_mode(m, pseudo ? asked : "scene request");
    anp_log("scene request '%s'%s%s%s from %p (%s) mode %s%s", id, pseudo ? " (asked '" : "", pseudo ? asked : "",
            pseudo ? "')" : "", ra, (DWORD)ra == 0x869d1b ? "SetId" : (DWORD)ra == 0x874a6f ? "story start" : "?",
            CM_NAME[g_cmode], anpId ? (g_cc.routing ? ", ANP scene via table entry 12" : ", ANP scene") : "");
    herowatch_event("scene request", id);   /* heapguard.inc: +0x88 headers before the old scene is torn down */
    return real_strncpy_c(dst, id, n);
}

/* ------------------------------------------------------------------ CreateFileA: menu, saves, scene tracking */
static const char *cmp_base(const char *n) {
    const char *b = n + strlen(n);
    while (b > n && b[-1] != '\\' && b[-1] != '/') b--;
    return b;
}
static int cmp_is_kls(const char *b) {
    int k = 0; while (b[k] >= '0' && b[k] <= '9') k++;
    return k > 0 && _stricmp(b + k, ".kls") == 0;
}
/* "...Scenes\<alias path>" (CMP_ALIAS, '/' and '\' alike) -> its id */
static int cmp_alias_of_path(const char *n, char *id) {
    size_t nl = strlen(n);
    for (int i = 0; CMP_ALIAS[i].id; i++) {
        const char *a = CMP_ALIAS[i].path; size_t al = strlen(a);
        if (nl <= al) continue;
        const char *t = n + nl - al;
        if (t[-1] != '\\' && t[-1] != '/') continue;
        size_t k = 0;
        for (; k < al; k++) {
            char x = t[k], y = a[k];
            if (x == '\\') x = '/';
            if (x >= 'A' && x <= 'Z') x += 32;
            if (y >= 'A' && y <= 'Z') y += 32;
            if (x != y) break;
        }
        if (k == al) { strcpy(id, CMP_ALIAS[i].id); return 1; }
    }
    return 0;
}
/* "...Locations\<id>\<id>_Main*.zip" -> id */
static int cmp_scene_of(const char *n, const char *b, char *id) {
    size_t bl = strlen(b);
    if (bl < 9 || _stricmp(b + bl - 4, ".zip")) return 0;
    if (_stricmp(b, "KaneAndLynch.zip") == 0) { strcpy(id, "FE"); return 1; }
    if (cmp_alias_of_path(n, id)) return 1;
    const char *us = strchr(b, '_');
    if (!us || us - b > 4 || us == b || _strnicmp(us, "_Main", 5)) return 0;
    int il = (int)(us - b);
    if (b - n < il + 1 || _strnicmp(b - il - 1, b, il) || (b - il - 2 >= n && b[-il - 2] != '\\' && b[-il - 2] != '/')) return 0;
    if (b - n < il + 11 || _strnicmp(b - il - 11, "Locations", 9)) return 0;
    memcpy(id, b, il); id[il] = 0;
    for (int i = 0; i < il; i++) if (id[i] >= 'a' && id[i] <= 'z') id[i] -= 32;
    return 1;
}

static void cmp_scene_arrived(const char *id) {                    /* g_cmpCs held */
    _snprintf(g_cprev, sizeof g_cprev, "%s", g_cscene);
    _snprintf(g_cscene, sizeof g_cscene, "%s", id);
    if (strcmp(id, "FE") == 0) {
        g_cAtFE = 1; g_feTick = GetTickCount();
        int mode = g_cmode, quit = g_quitReq;
        int dmEnd = !quit && (!strcmp(g_cprev, "M14") || !strcmp(g_cprev, "M13B"));
        anp_log("campaign: front end loading (after '%s'%s) mode %s", g_cprev, quit ? ", QuitGame" : dmEnd ? ", end of Dead Men" : "", CM_NAME[mode]);
        if (!g_cprev[0]) return;                                     /* boot */
        if (mode == CM_DEADMEN && dmEnd) cmp_ini_set("DeadMen", "done", "1");
        if (mode == CM_DEADDOGS && !quit && !strcmp(g_cprev, "L11")) cmp_ini_set("Saga", "done", "1");
        /* the reload is armed in every case, the hand-over too: if the player starts something else from the menu
           first, the request path still swaps the profile back before Dog Days' save can be touched */
        if (mode != CM_DOGDAYS && g_stickyMode < 0) {
            if (g_cc.reload) g_reloadPending = 1;
            else { g_stickyMode = mode; anp_log("campaign: ProfileReload=0: the %s save slot stays live for this session", CM_NAME[mode]); }
        }
        if (mode == CM_DEADDOGS && dmEnd && g_cc.handover) {
            cmp_ini_set("Saga", "pos", "L00");
            g_handoverPending = 1;
            anp_log("campaign: Dead Dogs: Dead Men finished -> Dog Days (L00) next");
        }
        return;
    }
    g_cAtFE = 0; g_reloadPending = 0; g_handoverPending = 0;
    if (g_cmode == CM_DEADMEN && cmp_dm_index(id) >= 0) {
        char r[16]; cmp_ini_get("DeadMen", "reached", "", r, sizeof r);
        cmp_ini_set("DeadMen", "last", id);
        if (cmp_dm_index(id) > cmp_dm_index(r)) cmp_ini_set("DeadMen", "reached", id);
    } else if (g_cmode == CM_DEADDOGS) cmp_ini_set("Saga", "pos", id);
    anp_log("campaign: scene '%s' loading (after '%s') mode %s", id, g_cprev, CM_NAME[g_cmode]);
}

static void cmp_fs_hook(const char *why);
static LPCSTR campaign_file(LPCSTR n, DWORD acc, DWORD disp) {
    if (!n || !n[0]) return n;
    const char *b = cmp_base(n);
    size_t bl = strlen(b);
    if (bl < 5) return n;
    const char *ext = b + bl - 4;
    if (_stricmp(ext, ".zip") == 0) {
        if (_stricmp(b, "Patch01.zip") == 0 || _stricmp(b, "KL2FixPatch01.zip") == 0) {
            g_cArmed = 1;                                           /* the scene loader mounts the patch first */
            cmp_fs_hook("patch archive probe");                     /* Mount runs on the FS object: it exists */
            if (g_cc.menu && !(acc & (GENERIC_WRITE | GENERIC_ALL)) && disp == OPEN_EXISTING) {
                static volatile LONG lg;
                if (GetFileAttributesA(g_menuAlt) != INVALID_FILE_ATTRIBUTES) {
                    if (InterlockedIncrement(&lg) <= 3) anp_log("menu: %s -> %s", n, g_menuAlt);
                    return g_menuAlt;
                }
                if (InterlockedIncrement(&lg) <= 1) anp_log("menu: no %s, stock menu", g_menuAlt);
            }
            return n;
        }
        char id[8];
        if (cmp_scene_of(n, b, id)) {
            EnterCriticalSection(&g_cmpCs);
            if (strcmp(id, g_cscene) != 0) {
                if (g_cArmed) { g_cArmed = 0; cmp_scene_arrived(id); }
                else { static int un; if (un++ < 8) anp_log("campaign: scene zip %s opened outside a scene load (ignored)", n); }
            } else {
                g_cArmed = 0;
                if (g_cAtFE && strcmp(id, "FE") == 0) g_feTick = GetTickCount();   /* the front end is still loading */
            }
            LeaveCriticalSection(&g_cmpCs);
        }
        return n;
    }
    if (g_cReloadProbe && _stricmp(ext, ".kls") == 0 && cmp_is_kls(b) && !(acc & GENERIC_WRITE) && disp == OPEN_EXISTING &&
        GetFileAttributesA(n) != INVALID_FILE_ATTRIBUTES)
        InterlockedIncrement(&g_cReloadOpens);                     /* cmp_profile_reload: the reader reached the file */
    if (g_cc.saves && g_cmode != CM_DOGDAYS && _stricmp(ext, ".kls") == 0 && cmp_is_kls(b) &&
        _strnicmp(n, g_appDir, strlen(g_appDir)) != 0) {
        static char ring[4][MAX_PATH]; static volatile LONG ri;      /* returned to the caller: one per open */
        char *alt = ring[InterlockedIncrement(&ri) & 3], dir[MAX_PATH];
        int m = g_cmode;
        _snprintf(dir, sizeof dir, "%s\\saves\\%s", g_appDir, CM_NAME[m]);
        cmp_mkdirs(dir);
        _snprintf(alt, MAX_PATH, "%s\\%s", dir, b);
        alt[MAX_PATH - 1] = 0;
        int seeded = 0;
        if (GetFileAttributesA(alt) == INVALID_FILE_ATTRIBUTES && GetFileAttributesA(n) != INVALID_FILE_ATTRIBUTES)
            seeded = CopyFileA(n, alt, TRUE) ? 1 : -1;
        anp_log("save redirect (%s, %s%s): %s -> %s%s", CM_NAME[m], (acc & GENERIC_WRITE) ? "write" : "read",
                disp == OPEN_EXISTING ? "" : ", create", n, alt, seeded > 0 ? " (seeded from the Dog Days save)" : seeded < 0 ? " (seed copy FAILED)" : "");
        return alt;
    }
    return n;
}

/* ------------------------------------------------------------------ fopen: the menu archive's real read
   ZSysFileWintel::Mount (0x809200, vtbl+0x13c; +0x98 is a thunk to it) only PROBES the archive with CreateFileA
   (0x5e2aa0, vtbl+8) and closes it. The archive itself is then read by FsZip_t::Open (0x74f300, mode 5 =
   IOFSMemoryAccess_t 0xb2f8cc) -> 0x74db40 -> MSVCR90 fopen(name, "rb") through kl2's import slot 0xb10430 and
   fseek/ftell/fread into one memory buffer. MSVCR90 opens the file with its own CreateFileA import, which the kl2
   CreateFileA hook never sees, so without this the stock (KL2Fix)Patch01.zip was mounted. Every later read
   (menu/frontend.xml: ZGUIXMLReader2 0x87e930 -> FS vtbl+0x34 size, +0x68 read) comes from that buffer. */
typedef FILE *(__cdecl *cmp_fopen_t)(const char *, const char *);
static cmp_fopen_t real_fopen_c;
static FILE *__cdecl cmp_fopen(const char *n, const char *mode) {
    if (g_cc.menu && n && mode && mode[0] == 'r' && !strchr(mode, '+')) {
        const char *b = cmp_base(n);
        if (_stricmp(b, "Patch01.zip") == 0 || _stricmp(b, "KL2FixPatch01.zip") == 0) {
            static volatile LONG lg;
            if (GetFileAttributesA(g_menuAlt) != INVALID_FILE_ATTRIBUTES) {
                FILE *f = real_fopen_c(g_menuAlt, mode);
                if (InterlockedIncrement(&lg) <= 6) anp_log("menu: fopen %s -> %s %s", n, g_menuAlt, f ? "ok" : "FAILED (stock archive used)");
                if (f) return f;
            } else if (InterlockedIncrement(&lg) <= 1) anp_log("menu: fopen %s: no %s, stock menu", n, g_menuAlt);
        }
    }
    return real_fopen_c(n, mode);
}

/* ------------------------------------------------------------------ FS vtable wrapper: menu/frontend.xml itself
   The menu XML loader (0x71a390 -> 0x6cffa0 -> ZGUIXMLReader2 0x87e930) asks the file system object
   ([0xdd263c], ZSysFileWintel, vtable 0xb8ed84) for the file's size (slot 13, +0x34 = 0x558730,
   __thiscall(path, bool diskOnly), ret 8), _alloca's that many bytes and reads it (slot 26, +0x68 = 0x819340,
   __thiscall(path, buf, size, offset, bool diskOnly), ret 0x14, returns the byte count or -1); 0x79edf0 parses it.
   The object's vptr is pointed at a copy of the vtable (heap/.data write, no code byte touched) whose two slots
   serve <DD>\ANP\menu\frontend.xml (written by tools/anp_menu.py next to ANP_Patch01.zip) when that file exists,
   whatever archive is mounted. Without the loose file they pass through and log which copy the archives gave.
   MenuXml=0 leaves the vtable alone. */
#define CMP_FS_OBJ    ((DWORD* volatile*)0xdd263c)
#define CMP_FS_VT     0xb8ed84
#define CMP_FS_SLOTS  87                                            /* slot 87 (+0x15c) is the next vtable's COL */
#define CMP_FE_MAX    (2 << 20)                                     /* served on the main thread's stack (_alloca) */
typedef int (__attribute__((thiscall)) *cmp_fssize_t)(void *self, const char *path, int disk);
typedef int (__attribute__((thiscall)) *cmp_fsread_t)(void *self, const char *path, void *buf, int size, int off, int disk);
static cmp_fssize_t real_fs_size;
static cmp_fsread_t real_fs_read;
static DWORD g_fsVt[1 + CMP_FS_SLOTS];                              /* [COL, slot 0..86]; vptr -> &g_fsVt[1] */
static char *g_feBuf; static int g_feLen = -1;                      /* loose ANP copy, loaded at the size request */
static volatile LONG g_feLogs;

static int cmp_is_frontend(const char *p) {                         /* "...[/\]menu[/\]frontend.xml" */
    if (!p) return 0;
    size_t L = strlen(p);
    if (L < 17 || _stricmp(p + L - 12, "frontend.xml")) return 0;
    const char *s = p + L - 12;                                     /* back over the separator(s) */
    if (s[-1] != '/' && s[-1] != '\\') return 0;
    while (s > p && (s[-1] == '/' || s[-1] == '\\')) s--;
    if (s - p < 4 || _strnicmp(s - 4, "menu", 4)) return 0;
    const char *m = s - 4;
    return m == p || m[-1] == '/' || m[-1] == '\\' || m[-1] == ':';
}

static int cmp_fe_load(void) {                                     /* g_cmpCs held; length or -1 */
    free(g_feBuf); g_feBuf = NULL; g_feLen = -1;
    FILE *f = fopen(g_menuXml, "rb");
    if (!f) return -1;
    long n = (fseek(f, 0, SEEK_END) == 0) ? ftell(f) : -1;
    if (n > 0 && n <= CMP_FE_MAX && fseek(f, 0, SEEK_SET) == 0 && (g_feBuf = (char*)malloc(n)) != NULL &&
        fread(g_feBuf, 1, n, f) == (size_t)n) g_feLen = (int)n;
    else {
        anp_log("menu: %s unusable (%ld bytes; limit %d): not served", g_menuXml, n, CMP_FE_MAX);
        free(g_feBuf); g_feBuf = NULL;
    }
    fclose(f);
    return g_feLen;
}

static int cmp_has_anp(const char *b, int n) {                     /* the XML defines ANP's windows */
    static const char k[] = "\"ANP_DeadMen\"";
    for (int i = 0; i + (int)sizeof k - 1 <= n; i++) if (b[i] == '"' && memcmp(b + i, k, sizeof k - 1) == 0) return 1;
    return 0;
}

static int __attribute__((thiscall)) cmp_fs_size(void *self, const char *path, int disk) {
    if (!(disk & 0xff) && cmp_is_frontend(path)) {
        EnterCriticalSection(&g_cmpCs);
        int n = cmp_fe_load();
        LeaveCriticalSection(&g_cmpCs);
        if (n > 0) return n;
        int r = real_fs_size(self, path, disk);
        if (InterlockedIncrement(&g_feLogs) <= 40)
            anp_log("menu: no %s: '%s' size %d from the mounted archives", g_menuXml, path, r);
        return r;
    }
    if (path) {                                                     /* an unexpected path form would show here */
        size_t L = strlen(path);
        static volatile LONG odd;
        if (L >= 12 && _stricmp(path + L - 12, "frontend.xml") == 0 && InterlockedIncrement(&odd) <= 5)
            anp_log("menu: size request for '%s' (diskOnly %d) not served", path, disk & 0xff);
    }
    return real_fs_size(self, path, disk);
}

static int __attribute__((thiscall)) cmp_fs_read(void *self, const char *path, void *buf, int size, int off, int disk) {
    if (!(disk & 0xff) && buf && size > 0 && cmp_is_frontend(path)) {
        EnterCriticalSection(&g_cmpCs);                             /* the copy the size request loaded, so the */
        int n = -1;                                                 /* caller's _alloca'd buffer matches it */
        if (g_feLen > 0 && off >= 0 && off <= g_feLen) {
            n = g_feLen - off < size ? g_feLen - off : size;
            memcpy(buf, g_feBuf + off, n);
        }
        int anp = n > 0 && cmp_has_anp((const char*)buf, n);
        LeaveCriticalSection(&g_cmpCs);
        if (n >= 0) {
            if (InterlockedIncrement(&g_feLogs) <= 40)
                anp_log("menu: served frontend.xml from ANP (%d bytes, %s, offset %d) for '%s'%s", n, g_menuXml, off, path,
                        anp ? "" : "  <<< file has no ANP_DeadMen window: is it an ANP build?");
            return n;
        }
        int r = real_fs_read(self, path, buf, size, off, disk);
        if (InterlockedIncrement(&g_feLogs) <= 40)
            anp_log("menu: frontend.xml from the mounted archives (%d bytes) for '%s': %s", r, path,
                    r <= 0 ? "READ FAILED" : cmp_has_anp((const char*)buf, r) ? "ANP copy (ANP_Patch01.zip mounted)"
                                                                            : "STOCK copy - ANP menu NOT active");
        return r;
    }
    return real_fs_read(self, path, buf, size, off, disk);
}

/* idempotent; called from the patch-archive probe (inside Mount, before any menu XML is read) and every tick */
static void cmp_fs_hook(const char *why) {
    static volatile LONG gate, done;
    if (done || !g_cc.menu || !g_cc.menuXml) return;
    if (InterlockedCompareExchange(&gate, 1, 0)) return;            /* another thread is at it */
    DWORD *fs = readable((const void*)CMP_FS_OBJ, 4) ? *CMP_FS_OBJ : NULL;
    if (!fs || !readable(fs, 4)) { gate = 0; return; }             /* not constructed yet */
    const DWORD *vt = (const DWORD*)CMP_FS_VT;
    if (fs[0] == (DWORD)&g_fsVt[1]) { done = 1; return; }
    if (fs[0] != CMP_FS_VT || vt[13] != 0x558730 || vt[26] != 0x819340) {
        anp_log("menu: file system object %p vtable %08lx (%s) unexpected: frontend.xml wrapper NOT installed", fs, fs[0], rtti_name(fs));
        done = 1; return;
    }
    memcpy(g_fsVt, vt - 1, sizeof g_fsVt);
    real_fs_size = (cmp_fssize_t)vt[13]; real_fs_read = (cmp_fsread_t)vt[26];
    g_fsVt[1 + 13] = (DWORD)cmp_fs_size; g_fsVt[1 + 26] = (DWORD)cmp_fs_read;
    InterlockedExchange((volatile LONG*)fs, (LONG)&g_fsVt[1]);
    done = 1;
    anp_log("menu: frontend.xml wrapper installed on the file system object %p (%s, %s): %s", fs, rtti_name(fs), why,
            GetFileAttributesA(g_menuXml) != INVALID_FILE_ATTRIBUTES ? "ANP file present" : "no ANP file, archives only");
}

/* ------------------------------------------------------------------ achievements guard (vptr swap, .data) */
static DWORD g_achVt[5];                                           /* [COL, slot0..3]; object vptr -> &g_achVt[1] */
static int __attribute__((thiscall)) cmp_ach_block(void *self, int a, int b) {
    static int n;
    if (n++ < 20) anp_log("campaign: achievement award (%d, %d) blocked (%s scene)", a, b, g_cscene);
    (void)self; return 0;
}
static int cmp_ach_swapped(void) { return readable((void*)CMP_ACH_OBJ, 4) && *(DWORD*)CMP_ACH_OBJ == (DWORD)&g_achVt[1]; }
static void cmp_ach_guard(int want, const char *why) {
    DWORD *obj = (DWORD*)CMP_ACH_OBJ;
    if (!readable(obj, 4)) return;
    if (want && *obj == CMP_ACH_VT) {
        if (!g_achVt[0]) { memcpy(g_achVt, (const DWORD*)CMP_ACH_VT - 1, sizeof g_achVt); g_achVt[4] = (DWORD)cmp_ach_block; }
        *obj = (DWORD)&g_achVt[1];
        anp_log("campaign: achievement guard on (%s)", why);
    } else if (!want && *obj == (DWORD)&g_achVt[1]) {
        *obj = CMP_ACH_VT;
        anp_log("campaign: achievement guard off (%s)", why);
    }
}

/* ------------------------------------------------------------------ intro movie -> campaign start
   New game (Dead Men) / New saga (Dead Dogs) open a menu window whose MoviePlayer plays Dead Men's intro
   (tools/anp_movie.py -> <DD>\Movies\ANP\M00_Intro.bik; tools/anp_menu.py --intro). No GUI element can start a scene
   when a movie ends (LoadScene only reacts to a press), so the loader does it: kl2's ZVideoPlayer opens every movie
   with _BinkOpen@8 (0x4df095 via import slot 0xb10748; path = Movie00 with leading separators stripped, '.bik'
   appended (0x7c6e10) and '\' turned into '/' (0x5dfb50), case kept) and closes it with _BinkClose@4 (slot 0xb1073c)
   when it finishes or is skipped (any key). Both are import slots: no kl2 code byte changes.
   The two pages name the same file in different letter case (Windows opens either): "Movies/ANP/M00_Intro" = Dead
   Men -> M01, "Movies/ANP/M00_INTRO" = Dead Dogs -> DGNW. IntroDelayMs after the close (front end only) the tick
   issues the request (do_load, as the autoload). A scene request that comes first (the fallback button) wins. */
typedef void *(__stdcall *cmp_binkopen_t)(const char *name, unsigned flags);
typedef void (__stdcall *cmp_binkclose_t)(void *bink);
static cmp_binkopen_t real_BinkOpen_c;
static cmp_binkclose_t real_BinkClose_c;

static int cmp_is_intro(const char *n) {                            /* ".../anp/m00_intro.bik", any case */
    static const char tail[] = "anp/m00_intro.bik";
    size_t L = n ? strlen(n) : 0, T = sizeof tail - 1;
    if (L < T) return 0;
    const char *t = n + L - T;
    if (t > n && t[-1] != '/' && t[-1] != '\\') return 0;
    for (size_t i = 0; i < T; i++) {
        char c = t[i]; if (c == '\\') c = '/';
        if (c >= 'A' && c <= 'Z') c += 32;
        if (c != tail[i]) return 0;
    }
    return 1;
}

static void *__stdcall cmp_BinkOpen(const char *name, unsigned flags) {
    void *h = real_BinkOpen_c(name, flags);
    static volatile LONG lg;
    int intro = g_cc.intro && cmp_is_intro(name);
    if (intro || InterlockedIncrement(&lg) <= 12)
        anp_log("movie: BinkOpen('%s', %x) = %p%s", name ? name : "(null)", flags, h, intro ? "  (ANP intro)" : "");
    if (intro && h) {
        g_introSaga = strstr(name, "M00_INTRO") != NULL;
        g_introPending = 0;
        g_introBink = h;
        anp_log("movie: ANP intro playing for %s", g_introSaga ? "Dead Dogs (New saga -> DGNW)" : "Dead Men (New game -> M01)");
    }
    return h;
}

static void __stdcall cmp_BinkClose(void *bink) {
    if (bink && bink == g_introBink) {
        g_introBink = NULL;
        g_introTick = GetTickCount();
        g_introPending = 1;
        anp_log("movie: ANP intro closed (finished or skipped): %s in %d ms", g_introSaga ? "DGNW" : "M01", g_cc.introDelay);
    }
    real_BinkClose_c(bink);
}

/* ------------------------------------------------------------------ ExitProcess tripwire */
/* Five CEG exit stubs all reach this slot (0xb1018c). 0x794e80 / 0x457680 call it with code 0x8000dead; the
   frame-pointer ones (0x56cd20, 0x722d90, 0x888120) do "push 0x8000dead; jmp [slot]", so ExitProcess sees the
   RETURN ADDRESS 0x8000dead and an exit code that is the stub's wipe-loop counter (0). Tag both shapes, and exit with
   0x8000dead so a test script sees the CEG kill in the process exit code too. */
static void WINAPI cmp_ExitProcess(UINT code) {
    void *ra = __builtin_return_address(0);
    int ceg = code == 0x8000dead || ra == (void*)0x8000dead;
    anp_log("ExitProcess(0x%08x) from %p%s", code, ra, ceg ? "  <<< CEG TRIPWIRE: Valve code-integrity check fired" : "");
    if (g_log) fflush(g_log);
    real_ExitProcess_c(ceg ? 0x8000dead : code);
}

/* ------------------------------------------------------------------ step-1 test hook: fire the level end */
typedef struct { BYTE *obj; long node; char tgt[128]; } CmpChanger;

static int cmp_target(const BYTE *obj, char *out, int cap) {   /* changer target string; 0 if not plausible */
    if (!readable(obj, 0x34)) return 0;
    const BYTE *so = *(const BYTE* const*)(obj + 0x30);
    if (!so || !readable(so, 0x10)) return 0;
    const char *s = (const char*)(so + 0xc);
    if (!readable(s, 1)) return 0;
    int k = 0;
    while (k < cap - 1 && readable(s + k, 1) && s[k]) {
        if (s[k] < 32 || s[k] > 126) return 0;
        out[k] = s[k]; k++;
    }
    out[k] = 0;
    if (k < 4 || k >= cap - 1) return 0;
    return 1;
}

/* the changer is "live" when one of its first words points at an object of the current scene's node table */
static long cmp_owner_node(const BYTE *obj) {
    for (int i = 1; i < 12; i++) {
        const void *p = *(const void* const*)(obj + 4 * i);
        if ((DWORD)p < 0x10000 || !readable(p, 4)) continue;
        long n = node_of(p);
        if (n >= 0) return n;
    }
    return -1;
}

static int cmp_scan_changers(CmpChanger *out, int cap) {
    SYSTEM_INFO si; GetSystemInfo(&si);
    BYTE *a = (BYTE*)si.lpMinimumApplicationAddress, *end = (BYTE*)si.lpMaximumApplicationAddress;
    MEMORY_BASIC_INFORMATION mi; int n = 0; DWORD t0 = GetTickCount(); unsigned long long scanned = 0;
    while (a < end && VirtualQuery(a, &mi, sizeof mi)) {
        BYTE *rb = (BYTE*)mi.BaseAddress, *re = rb + mi.RegionSize;
        DWORD pr = mi.Protect & 0xff;
        if (mi.State == MEM_COMMIT && mi.Type != MEM_IMAGE && !(mi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) &&
            (pr == PAGE_READWRITE || pr == PAGE_EXECUTE_READWRITE)) {
            scanned += mi.RegionSize;
            for (DWORD *p = (DWORD*)rb; (BYTE*)(p + 1) <= re; p++) {
                if (*p != CMP_SCENECHANGER_VT) continue;
                if (n >= cap) continue;
                CmpChanger c; c.obj = (BYTE*)p;
                if ((BYTE*)p + 0x34 > re || !cmp_target(c.obj, c.tgt, sizeof c.tgt)) continue;
                c.node = cmp_owner_node(c.obj);
                out[n++] = c;
            }
        }
        if (re <= a) break;
        a = re;
    }
    anp_log("endlevel: scanned %llu MB in %lu ms: %d ZSceneChanger object(s)", scanned >> 20, GetTickCount() - t0, n);
    return n;
}

static void cmp_fire(BYTE *obj, const char *tgt) {
    /* awards are blocked while the forced level end runs (and stay blocked if the campaign guard is on) */
    int was = cmp_ach_swapped();
    if (!was) cmp_ach_guard(1, "forced level end");
    if (!cmp_ach_swapped()) anp_log("endlevel: achievements object vtable %08lx (%s) unexpected: not blocked",
                                    readable((void*)CMP_ACH_OBJ, 4) ? *(DWORD*)CMP_ACH_OBJ : 0, rtti_name((void*)CMP_ACH_OBJ));
    DWORD fn = (*(DWORD**)obj)[0x88 / 4];
    anp_log("endlevel: firing ZSceneChanger %p slot 34 (%08lx) -> '%s'", obj, fn, tgt);
    ((cmp_slot34_t)fn)(obj);
    if (!was) cmp_ach_guard(0, "forced level end done");
    anp_log("endlevel: level end issued");
}

static char cmp_lc(char ch) { return (ch >= 'A' && ch <= 'Z') ? (char)(ch + 32) : ch; }
static void cmp_endlevel(const char *want) {
    CmpChanger c[32];
    int n = cmp_scan_changers(c, 32), pick = -1, nlive = 0, nmatch = 0, listonly = _stricmp(want, "list") == 0;
    char lw[64]; int i, k;
    for (k = 0; want[k] && k < 63; k++) lw[k] = cmp_lc(want[k]);
    lw[k] = 0;
    for (i = 0; i < n; i++) {
        char lt[128]; for (k = 0; c[i].tgt[k]; k++) lt[k] = cmp_lc(c[i].tgt[k]);
        lt[k] = 0;
        int match = listonly || !lw[0] || strstr(lt, lw) != NULL;
        anp_log("endlevel:   changer %p target '%s' owner node %ld%s", c[i].obj, c[i].tgt, c[i].node, match ? " (match)" : "");
        if (c[i].node >= 0) nlive++;
        if (!match || listonly) continue;
        nmatch++;
        /* prefer a live one (owner in the current node table); among equals the last found */
        if (pick < 0 || c[i].node >= 0 || c[pick].node < 0) pick = i;
    }
    if (listonly) return;
    if (!lw[0] && nlive != 1) { anp_log("endlevel: no target given and %d live changers: not firing", nlive); return; }
    if (pick < 0) { anp_log("endlevel: no changer targets '%s': not firing", want); return; }
    if (c[pick].node < 0) anp_log("endlevel: warning: matching changer has no owner in the node table (%d matches)", nmatch);
    cmp_fire(c[pick].obj, c[pick].tgt);
}

/* ------------------------------------------------------------------ diagnostics */
static void cmp_log_state(void) {
    char a[16], b[16], c[16], d[16], e[16];
    cmp_ini_get("DeadMen", "last", "", a, sizeof a); cmp_ini_get("DeadMen", "reached", "", b, sizeof b);
    cmp_ini_get("DeadMen", "done", "", c, sizeof c); cmp_ini_get("Saga", "pos", "", d, sizeof d); cmp_ini_get("Saga", "done", "", e, sizeof e);
    anp_log("cstate: mode %s scene '%s' prev '%s' frontend %d reloadPending %d handoverPending %d quitReq %d sticky %d "
            "achGuard %d entry12 %s -> %s | ini %s: DeadMen last=%s reached=%s done=%s, Saga pos=%s done=%s",
            CM_NAME[g_cmode], g_cscene, g_cprev, g_cAtFE, g_reloadPending, g_handoverPending, g_quitReq, g_stickyMode,
            cmp_ach_swapped(), (const char*)CMP_SCN_TABLE[2 * CMP_BORROW], (const char*)CMP_SCN_TABLE[2 * CMP_BORROW + 1],
            g_iniPath, a, b, c, d, e);
    for (int m = 1; m <= 2; m++) {
        char p[MAX_PATH]; WIN32_FILE_ATTRIBUTE_DATA fa;
        _snprintf(p, sizeof p, "%s\\saves\\%s\\0.kls", g_appDir, CM_NAME[m]);
        if (GetFileAttributesExA(p, GetFileExInfoStandard, &fa)) {
            SYSTEMTIME st; FileTimeToSystemTime(&fa.ftLastWriteTime, &st);
            anp_log("cstate: %s %lu bytes, written %04d-%02d-%02d %02d:%02d:%02d UTC", p, fa.nFileSizeLow,
                    st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
        } else anp_log("cstate: %s absent", p);
    }
}

static void cmp_inline_strings(const char *tag, const BYTE *o, int n) {   /* ASCII runs stored inside an object */
    char buf[400]; int k = 0;
    for (int i = 0; i < n && k < 360; ) {
        int j = i; while (j < n && o[j] >= 32 && o[j] < 127) j++;
        if (j - i >= 6 && j < n && o[j] == 0) k += _snprintf(buf + k, sizeof buf - k, " +%02x'%.*s'", i, j - i > 40 ? 40 : j - i, (const char*)o + i);
        i = j + 1;
    }
    buf[k < (int)sizeof buf ? k : (int)sizeof buf - 1] = 0;
    if (k) anp_log("%s inline:%s", tag, buf);
}

static int cmp_count_string(const char *w) {                     /* NUL-terminated copies in committed RW memory */
    SYSTEM_INFO si; GetSystemInfo(&si);
    BYTE *a = (BYTE*)si.lpMinimumApplicationAddress, *end = (BYTE*)si.lpMaximumApplicationAddress;
    MEMORY_BASIC_INFORMATION mi; int n = 0; size_t L = strlen(w);
    while (a < end && VirtualQuery(a, &mi, sizeof mi)) {
        BYTE *rb = (BYTE*)mi.BaseAddress, *re = rb + mi.RegionSize;
        DWORD pr = mi.Protect & 0xff;
        int ownStack = (BYTE*)&mi >= rb && (BYTE*)&mi < re;          /* our own copies of the words live here */
        if (mi.State == MEM_COMMIT && mi.Type != MEM_IMAGE && !(mi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) &&
            (pr == PAGE_READWRITE || pr == PAGE_EXECUTE_READWRITE) && !ownStack) {
            for (BYTE *p = rb; p + L + 1 <= re; p++)
                if (*p == (BYTE)w[0] && memcmp(p, w, L) == 0 && p[L] == 0 &&
                    (p == rb || !((p[-1] >= '0' && p[-1] <= '9') || ((p[-1] | 32) >= 'a' && (p[-1] | 32) <= 'z') ||
                                  p[-1] == '_' || p[-1] == '"'))) n++;   /* not inside a longer name / the XML text */
        }
        if (re <= a) break;
        a = re;
    }
    return n;
}

static void cmp_gui_names(const char *words) {
    DWORD gs = readable((void*)0x1539f0c, 4) ? *(DWORD*)0x1539f0c : 0;
    if (gs && readable((void*)gs, 0x6c4)) {
        DWORD *p = (DWORD*)gs; int n = (int)p[0xca];
        anp_log("guinames: %d open window(s)", n);
        for (int i = 0; i < n && i < 16; i++) {
            BYTE *w = (BYTE*)p[0xcb + i]; char tag[48];
            _snprintf(tag, sizeof tag, "guinames:   [%d] %p %s", i, w, rtti_name(w));
            anp_log("%s", tag);
            if (readable(w, 0x200)) { log_obj_strings("guinames:     ptr", w, 0x200); cmp_inline_strings("guinames:    ", w, 0x200); }
        }
    } else anp_log("guinames: no GUI system yet");
    char list[160]; _snprintf(list, sizeof list, "%s", words[0] ? words : "ANP_DeadMen ANP_DeadMenChapters ANP_DeadDogs");
    for (char *t = strtok(list, " ,\t"); t; t = strtok(NULL, " ,\t"))
        anp_log("guinames: '%s' found %d time(s) in memory", t, cmp_count_string(t));
}

static int cmp_read_cmd(const char *name, char *buf, int cap) {   /* 1 if the file existed (deleted after reading) */
    char p[MAX_PATH]; _snprintf(p, sizeof p, "%s\\%s", g_dir, name);
    if (GetFileAttributesA(p) == INVALID_FILE_ATTRIBUTES) return 0;
    buf[0] = 0;
    FILE *f = fopen(p, "r");
    if (f) { if (!fgets(buf, cap, f)) buf[0] = 0; fclose(f); }
    char *e = buf + strlen(buf); while (e > buf && (e[-1] == '\n' || e[-1] == '\r' || e[-1] == ' ' || e[-1] == '\t')) *--e = 0;
    char *s = buf; while (*s == ' ' || *s == '\t') s++;
    if (s != buf) memmove(buf, s, strlen(s) + 1);
    if (!DeleteFileA(p)) anp_log("campaign: could not delete %s (%lu)", name, GetLastError());
    return 1;
}

/* ------------------------------------------------------------------ init, tick */
static void campaign_init(void) {
    InitializeCriticalSection(&g_cmpCs);
    cmp_config_load();
    cmp_paths_init();
    HMODULE exe = GetModuleHandleA(NULL);
    if (g_cc.routing) {
        hook_iat(exe, "MSVCR90.dll", "strncpy", (void*)cmp_strncpy, (void**)&real_strncpy_c);
        /* no automatic fallback to the 0x6d100f code patch any more (CEG-hashed): only LegacyResolver=1 installs it */
        anp_log("campaign: strncpy routing %s", real_strncpy_c ? "ok" : g_cc.legacy ? "MISSING -> legacy resolver patch used"
                : "MISSING: ANP scene ids will not resolve (LegacyResolver=1 = old code patch, CEG-hashed)");
        if (!real_strncpy_c) g_cc.routing = 0;
    } else if (!g_cc.legacy) anp_log("campaign: Routing=0 and LegacyResolver=0: ANP scene ids will not resolve");
    if (g_cc.menu) {
        hook_iat(exe, "MSVCR90.dll", "fopen", (void*)cmp_fopen, (void**)&real_fopen_c);
        anp_log("campaign: menu archive fopen hook %s", real_fopen_c ? "ok" : "MISSING (stock menu)");
        anp_log("campaign: menu sources: %s %s, %s %s (MenuXml=%d)", g_menuAlt,
                GetFileAttributesA(g_menuAlt) != INVALID_FILE_ATTRIBUTES ? "present" : "absent", g_menuXml,
                GetFileAttributesA(g_menuXml) != INVALID_FILE_ATTRIBUTES ? "present" : "absent", g_cc.menuXml);
    }
    if (g_cc.tripwire) {
        hook_iat(exe, "kernel32.dll", "ExitProcess", (void*)cmp_ExitProcess, (void**)&real_ExitProcess_c);
        anp_log("campaign: ExitProcess tripwire %s", real_ExitProcess_c ? "ok" : "MISSING");
    }
    if (g_cc.intro) {
        hook_iat(exe, "binkw32.dll", "_BinkOpen@8", (void*)cmp_BinkOpen, (void**)&real_BinkOpen_c);
        hook_iat(exe, "binkw32.dll", "_BinkClose@4", (void*)cmp_BinkClose, (void**)&real_BinkClose_c);
        if (!real_BinkOpen_c || !real_BinkClose_c) {                /* a lone hook just passes through */
            anp_log("campaign: intro movie hooks MISSING (open %p close %p): the menu's fallback button starts the "
                    "campaign", real_BinkOpen_c, real_BinkClose_c);
            g_cc.intro = 0;
        } else {
            char p[MAX_PATH]; _snprintf(p, sizeof p, "%s\\Movies\\ANP\\M00_Intro.bik", g_dir); p[MAX_PATH - 1] = 0;
            anp_log("campaign: intro movie hooks ok (BinkOpen/BinkClose import slots); %s %s", p,
                    GetFileAttributesA(p) != INVALID_FILE_ATTRIBUTES ? "present" : "ABSENT (New game falls back to the button)");
        }
    }
    anp_log("campaign: data folder %s", g_appDir);
}
static int campaign_legacy_resolver(void) { return g_cc.legacy; }

/* main thread, every PeekMessageA */
static void campaign_tick(DWORD now) {
    /* "steady": PeekMessageA has come at least every 250 ms for a second. A scene load blocks the pump (the watchdog
       sees multi-second gaps), so this keeps the profile reader (which can open a "save loaded" GUI message) and the
       hand-over do_load away from a front end that is still loading. */
    static DWORD prevPeek, steadySince;
    if (!prevPeek || now - prevPeek > 250) steadySince = now;
    prevPeek = now;
    cmp_fs_hook("main thread");                                     /* no-op once installed */
    if ((g_reloadPending || g_handoverPending) && g_cAtFE && now - g_feTick >= (DWORD)g_cc.reloadDelay &&
        now - steadySince >= 1000) {
        if (g_handoverPending) {
            g_handoverPending = 0; g_handoverReq = 1;
            anp_log("campaign: Dead Dogs hand-over: starting L00");
            do_load("L00", 1);
            g_handoverReq = 0;
        } else cmp_profile_reload("back at the front end");
    }
    if (g_introPending && now - g_introTick >= (DWORD)g_cc.introDelay) {
        g_introPending = 0;                                         /* before do_load: its strncpy would drop it */
        if (!g_cAtFE) anp_log("campaign: intro: not at the front end any more, nothing started");
        else {
            const char *id = g_introSaga ? "DGNW" : "M01";
            anp_log("campaign: intro: starting %s", id);
            do_load(id, 1);
        }
    }
    static DWORD last;
    if (now - last < 500) return;
    last = now;
    if (g_cc.ach) {
        int want = g_cmode == CM_DEADMEN || (g_cmode == CM_DEADDOGS && cmp_dm_index(g_cscene) >= 0);
        cmp_ach_guard(want, want ? "Dead Men scene" : "no Dead Men scene");
    }
    char b[160];
    if (cmp_read_cmd("ANP_load.txt", b, sizeof b)) {
        char id[8] = ""; int mode = 1;
        if (sscanf(b, "%7s %d", id, &mode) >= 1 && id[0]) { anp_log("ANP_load.txt: '%s' mode %d", id, mode); do_load(id, mode); }
        else anp_log("ANP_load.txt: empty, ignored");
    }
    if (cmp_read_cmd("ANP_endlevel.txt", b, sizeof b)) {
        anp_log("ANP_endlevel.txt: '%s'", b);
        cmp_endlevel(b);
    }
    if (cmp_read_cmd("ANP_cstate.txt", b, sizeof b)) cmp_log_state();
    if (cmp_read_cmd("ANP_guinames.txt", b, sizeof b)) cmp_gui_names(b);
}
