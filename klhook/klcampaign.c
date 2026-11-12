/* klcampaign.c - the campaign RUNTIME CORE: luvsic's Dead Men campaign loader (a-newer-perspective), minus his UI.
 *
 * Ported from luvsic's a-newer-perspective loader/campaign.inc and loader/anp_loader.c @32aa649 (in contribution with luvsic).
 * Owner, 2026-11-09: "pull luvsic's repo and merge it with mine somehow? i want his campaign stuff, everything he's been doing for
 * that, in my game, but maybe not the whole ui thing he's done". This file is the core; the UI (campaign menu entry, frontend.xml
 * delivery, intro movie, chapter titles, Dead Men HUD / fonts) and his diagnostics (godmode, d3dshot, failwatch, cutdiag) are NOT here.
 *
 * READ = his code (file:function), MEASURED = checked in this repo, GUESS = not verified. Pure logic: klcmpcore_logic.h (+ kladpcm.h),
 * tests klcmpcore_test.c / kladpcm_test.c. NOT RUN IN THE GAME (written offline, no game launch).
 *
 * What it does (every part is its own [Campaign] toggle, ALL default 0, and every one needs [Campaign] Enable=1 (klcampaign_gate.h);
 * Enable=0 = this module installs NOTHING):
 *   Routing=1       scene ids. SetId (0x869d00) and the story start (0x874a69) copy the requested id with strncpy(0x156b6f5, id, 4)
 *                   through kl2's MSVCR90 import (READ campaign.inc:cmp_strncpy). A request for a converted campaign level
 *                   (Scenes\Locations\<ID>\<ID>_Main.zip exists, ID not in the stock scene table) gets the scene-table entry 12
 *                   ('AM01' -> AttractMode.zip, unused; table 0xcef700, 22 x {id, path}) rewritten to {ID, "Locations/<ID>/<ID>_Main.zip"};
 *                   any other request puts the stock entry back. So M01..M14, M03B, M07F start as their OWN scene, and any id a level
 *                   chains to (ZSceneChanger -> SetId) is routed the same way. M07F keeps Dead Men's funeral path (CMP_ALIAS: kl2's
 *                   scene bookkeeping skips chapter index / profile save for a path containing "Funeral").
 *                   Import slot + .data only; coexists with klslot.c (it hooks other imports; this hook chains whatever it found).
 *   Trigger=1       <DD>\KLCampaign_load.txt = "M01 1" (id, optional mode, default 1): consumed and DELETED, then SetId + Start (READ
 *                   anp_loader.c:do_load: (*0xdd2640)+0xac -> +0xb8 = 1, *0x156b3bc = mode, SetId(0x156b3b0, id) 0x869d00, Start 0x6c8040).
 *                   Replaces his menu entry as the way to start a campaign level. Polled twice a second on the game thread.
 *   AutoLoad=<ID>   the same start once, AutoLoadDelayMs after boot (and only when the pump has run steadily for a second = not loading).
 *                   For an unattended run: launch options stay `-o DefaultScene=Locations/F01/F01_Main.gms ...`, this then switches.
 *                   `-o DefaultScene=Locations/M01/M01_Main.gms` itself: GUESS - the engine opens the scene zip by path and needs no table
 *                   entry (the scene tracking below sees the zip open either way); his legacy resolver code patch 0x6d100f (CEG-hashed
 *                   code) is NOT ported (SHIP writes import slots and data only).
 *   SaveRedirect=1  while a campaign level is active the <n>.kls profile opens go to <DataDir>\saves\Campaign\<n>.kls (seeded by copying
 *                   Dog Days' file the first time), so Dog Days' own save is never written by the campaign (READ campaign.inc:campaign_file).
 *   ProfileReload=1 (needs SaveRedirect) after the campaign is left, Dog Days' profile is re-read from its own save in one game-thread
 *                   step (0x47c5f0(0x1686e60, 0) with [0x1686e71]=1, the stock chapter selector's call) and only then is the redirect
 *                   dropped; if the reader did not really open the file the redirect stays on for the session (READ campaign.inc:cmp_profile_reload).
 *   Progress=1      <DataDir>\ANP_progress.ini [DeadMen] last / reached / done from the scene zips the game opens (READ campaign.inc:cmp_scene_arrived).
 *   AchievementGuard=1  while a campaign level is active the static ZAchievementsSteam object (0x156c108) gets a vtable copy whose slot 3
 *                   (award, 0x72fd60) only logs; the stock vptr is put back otherwise (READ campaign.inc:cmp_ach_guard). .data only.
 *   Adpcm=1         Dead Men's IMA-ADPCM sound streams (.str, IOISNDSTREAM) decoded at read time to 16-bit PCM at virtual offsets >= 0x60000000
 *                   with the 4 KB 'LIP ' block served verbatim (READ anp_loader.c:str_register / str_serve_virtual / str_overlay / my_ReadFile);
 *                   KERNEL32 CreateFileA / ReadFile / CloseHandle import hooks, each chained to whatever was there (klslot.c's CreateFileA).
 *
 * ADAPTATION (his menu's pseudo ids -> this core): luvsic's loader keeps a three-way mode (Dog Days / Dead Men / Dead Dogs) switched by
 * pseudo scene ids DMCN / DGNW / DGCN that his menu pages request. Without his menu there are no pseudo ids, so the mode is simply
 * "a campaign level is active": the scene tracked from the scene-zip opens (CreateFileA) OR klcmp_level_active() (the engine's scene
 * name). Dead Dogs (the saga: Dead Men -> Dog Days hand-over) is not ported. The save slot is therefore "Campaign" (his: DeadMen).
 *
 * Not ported on purpose: the legacy code patches (0x6d100f, 0x71166d - CEG-hashed), the ExitProcess tripwire (diagnostic), the fopen /
 * FS-vtable menu delivery, BinkOpen/BinkClose intro, ANP_endlevel / cstate / guinames test hooks, the strncpy herowatch_event heapguard.
 *
 * KLHook.ini keys: klhook/ini_campaign_core.txt (KLHook.ini itself is not edited by this slice).
 * Needs klcampaign_gate.h included first (klcmp_enabled, klcmp_level_active), and klh_ini / klh_scene / klh_level_key / klh_iat / klh_data / klh_rd32. */
#include "klcmpcore_logic.h"

#define KLCMPR_REQ_ID      0x156b6f5u     /* 0x156b3b0 + 0x345: 4 chars, NUL at +0x349 (READ CMP_REQ_ID) */
#define KLCMPR_SCN_TABLE   0xcef700u      /* {const char *id, const char *path} x 22, .data */
#define KLCMPR_BORROW      12             /* "AM01" -> "AttractMode.zip" */
#define KLCMPR_AM01_ID     0xb70604u
#define KLCMPR_AM01_PATH   0xb84534u
#define KLCMPR_ACH_OBJ     0x156c108u
#define KLCMPR_ACH_VT      0xbc0d00u
#define KLCMPR_PROFILE     0x1686e60u
#define KLCMPR_PROFILE_FLAG 0x1686e71u
#define KLCMPR_PROFILE_READ 0x47c5f0u
#define KLCMPR_PRESSSTART  0x156b742u
#define KLCMPR_APP         0xdd2640u      /* the application object (+0xac -> +0xb8 = 1 before a scene start, as do_load) */
#define KLCMPR_MODE        0x156b3bcu
#define KLCMPR_SCENEREQ    0x156b3b0u
#define KLCMPR_SETID       0x869d00u
#define KLCMPR_START       0x6c8040u
#define KLCMPR_NSTR 32
#define KLCMPR_NFILE 8

typedef struct { char path[MAX_PATH]; klcmpc_ent *e; int n; HANDLE src; CRITICAL_SECTION cs; int lastEnt, lastBlk; short *blk; BYTE *srcbuf; DWORD tbl, cnt; } klcmpr_strfile;

static struct {
    int on, routing, trigger, saves, reload, progress, ach, adpcm, strredir, log;
    DWORD reload_delay, auto_delay, t0, t_slow, fe_tick;
    char auto_id[8]; int auto_mode, auto_done;
    char scene[8], prev[8]; volatile int in_campaign; int quitreq;
    char rid[8], rpath[64];
    char appdir[MAX_PATH], inipath[MAX_PATH], dmdir[MAX_PATH];
    volatile int reload_pending, sticky, reload_probe; volatile LONG reload_opens;
    struct klcmpc_steady steady;
    CRITICAL_SECTION cs;
    int nroute_log;
} klcmpr;

static char *(__cdecl *klcmpr_real_strncpy)(char *, const char *, size_t);
static HANDLE (WINAPI *klcmpr_real_CreateFileA)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static BOOL (WINAPI *klcmpr_real_ReadFile)(HANDLE, LPVOID, DWORD, LPDWORD, LPOVERLAPPED);
static BOOL (WINAPI *klcmpr_real_CloseHandle)(HANDLE);

/* ---------------------------------------------------------------- paths, progress ini */
static void klcmpr_mkdirs(const char *d)
{   /* every level of an absolute path (READ cmp_mkdirs) */
    char t[MAX_PATH], *p;
    snprintf(t, sizeof t, "%s", d);
    for (p = t + 3; *p; p++) if (*p == '\\') { *p = 0; CreateDirectoryA(t, NULL); *p = '\\'; }
    CreateDirectoryA(t, NULL);
}

static int klcmpr_isdir_with_def(const char *d)
{
    char f[MAX_PATH]; snprintf(f, sizeof f, "%s\\PC_Def.str", d);
    return GetFileAttributesA(f) != INVALID_FILE_ATTRIBUTES;
}

static void klcmpr_find_dm(void)
{   /* Dead Men's folder for the ".." stream names in the converted .SND files. [Campaign] DeadMenDir= wins; else DD\..\Kane and Lynch Dead Men (then no redirect is
       needed: dmdir stays empty); else every library in <steamapps>\libraryfolders.vdf (<DD> = <steamapps>\common\<game>). MINE; leaves dmdir empty when not found. */
    char cfg[MAX_PATH] = "", f[MAX_PATH], *txt; HANDLE h; DWORD got = 0, sz; int n, i;
    klcmpr.dmdir[0] = 0;
    GetPrivateProfileStringA("Campaign", "DeadMenDir", "", cfg, sizeof cfg, klh_ini);
    if (cfg[0]) {
        size_t L = strlen(cfg); while (L && (cfg[L - 1] == '\\' ||cfg[L - 1] == '/')) cfg[--L] = 0;
        if (klcmpr_isdir_with_def(cfg)) { snprintf(klcmpr.dmdir, sizeof klcmpr.dmdir, "%s", cfg); return; }
        klog("campaign: DeadMenDir '%s' has no PC_Def.str: searching the Steam libraries", cfg);
    }
    snprintf(f, sizeof f, "%s\\..\\Kane and Lynch Dead Men", dir);
    if (klcmpr_isdir_with_def(f)) { klog("campaign: Dead Men stream folder is next to Dog Days: no redirect needed"); return; }
    snprintf(f, sizeof f, "%s\\..\\..\\libraryfolders.vdf", dir);
    h = CreateFileA(f, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
    if (h == INVALID_HANDLE_VALUE) { klog("campaign: no Dead Men folder found (%s unreadable): its voice lines stay silent, set [Campaign] DeadMenDir=", f); return; }
    sz = GetFileSize(h, NULL);
    if (sz == INVALID_FILE_SIZE || sz > (1u << 20) || !(txt = (char *)malloc(sz + 1))) { CloseHandle(h); return; }
    if (!ReadFile(h, txt, sz, &got, NULL)) got = 0;
    CloseHandle(h); txt[got] = 0;
    {   char (*lib)[MAX_PATH] = (char (*)[MAX_PATH])calloc(16, MAX_PATH);
        n = lib ? klcmpc_vdf_paths(txt, &lib[0][0], MAX_PATH, 16) : 0;
        for (i = 0; i < n && !klcmpr.dmdir[0]; i++) {
            snprintf(f, sizeof f, "%s\\steamapps\\common\\Kane and Lynch Dead Men", lib[i]);
            if (klcmpr_isdir_with_def(f)) snprintf(klcmpr.dmdir, sizeof klcmpr.dmdir, "%s", f);
        }
        free(lib);
    }
    free(txt);
    if (klcmpr.dmdir[0]) klog("campaign: Dead Men folder %s (stream names '..\\Kane and Lynch Dead Men\\*.str' are redirected there)", klcmpr.dmdir);
    else klog("campaign: no Dead Men folder found in the Steam libraries: its voice lines stay silent, set [Campaign] DeadMenDir=");
}

static void klcmpr_paths(void)
{   /* <DataDir> from [Campaign] DataDir, else %LOCALAPPDATA%\A Newer Perspective (his folder, so progress is shared with his own loader), else <DD>\KLCampaign */
    char la[MAX_PATH] = "", cfg[MAX_PATH] = "";
    GetPrivateProfileStringA("Campaign", "DataDir", "", cfg, sizeof cfg, klh_ini);
    if (cfg[0]) snprintf(klcmpr.appdir, sizeof klcmpr.appdir, "%s", cfg);
    else {
        DWORD n = GetEnvironmentVariableA("LOCALAPPDATA", la, sizeof la);
        if (n && n < sizeof la) snprintf(klcmpr.appdir, sizeof klcmpr.appdir, "%s\\A Newer Perspective", la);
        else snprintf(klcmpr.appdir, sizeof klcmpr.appdir, "%s\\KLCampaign", dir);
    }
    snprintf(klcmpr.inipath, sizeof klcmpr.inipath, "%s\\ANP_progress.ini", klcmpr.appdir);
    klcmpr.appdir[MAX_PATH - 1] = klcmpr.inipath[MAX_PATH - 1] = 0;
}

static void klcmpr_ini_set(const char *sec, const char *key, const char *val)
{
    char cur[64];
    if (!klcmpr.progress) return;
    GetPrivateProfileStringA(sec, key, "\x01", cur, sizeof cur, klcmpr.inipath);
    if (strcmp(cur, val) == 0) return;
    klcmpr_mkdirs(klcmpr.appdir);
    if (WritePrivateProfileStringA(sec, key, val, klcmpr.inipath)) { if (klcmpr.log) klog("campaign: progress [%s] %s=%s", sec, key, val); }
    else klog("campaign: progress write failed (%lu) %s", GetLastError(), klcmpr.inipath);
}

/* ---------------------------------------------------------------- scene ids: the table entry, the strncpy hook */
static int klcmpr_stock_id(const char *id)
{   /* an id of the stock scene table (entry 12, the borrowed AM01, excluded); L00 is a resolver special case (READ cmp_stock_id) */
    int i; char s[16];
    if (_stricmp(id, "L00") == 0 || _stricmp(id, "AM01") == 0) return 1;
    for (i = 0; i < 22; i++) {
        DWORD p;
        if (i == KLCMPR_BORROW) continue;
        p = klh_rd32((DWORD_PTR)KLH_VA(KLCMPR_SCN_TABLE) + 8 * i);
        if (p && klh_rdstr(p, s, sizeof s) && strcmp(s, id) == 0) return 1;
    }
    return 0;
}

static int klcmpr_anp_id(const char *id)
{   /* a converted level: the id is sane, not stock, and Scenes\Locations\<id>\<id>_Main.zip (or the alias) exists (READ cmp_anp_id) */
    char p[MAX_PATH], rel[80]; int k;
    if (!klcmpc_id_ok(id) || klcmpr_stock_id(id)) return 0;
    if (!klcmpc_rpath(id, rel, sizeof rel)) return 0;
    k = snprintf(p, sizeof p, "%s\\Scenes\\%s", dir, rel);
    if (k < 0 || k >= (int)sizeof p) return 0;
    for (k = 0; p[k]; k++) if (p[k] == '/') p[k] = '\\';
    return GetFileAttributesA(p) != INVALID_FILE_ATTRIBUTES;
}

static void klcmpr_table_entry(const char *id)
{   /* entry 12 := {id, path}, or the stock AM01 entry for NULL (READ cmp_table_entry; VirtualProtect replaced by klh_data: .data is writable) */
    DWORD *e = (DWORD *)KLH_VA(KLCMPR_SCN_TABLE + 8 * KLCMPR_BORROW), w[2];
    if (id) {
        klcmpc_rpath(id, klcmpr.rpath, sizeof klcmpr.rpath);
        snprintf(klcmpr.rid, sizeof klcmpr.rid, "%s", id);
        w[0] = (DWORD)(DWORD_PTR)klcmpr.rid; w[1] = (DWORD)(DWORD_PTR)klcmpr.rpath;
    } else { w[0] = (DWORD)(DWORD_PTR)KLH_VA(KLCMPR_AM01_ID); w[1] = (DWORD)(DWORD_PTR)KLH_VA(KLCMPR_AM01_PATH); }
    if (klh_rd32((DWORD_PTR)e) == w[0] && klh_rd32((DWORD_PTR)e + 4) == w[1]) return;
    if (!klh_data(e, w, 8, "campaign scene table entry 12")) klog("campaign: scene table entry 12 not writable");
}

static void klcmpr_mark_app(void)
{   /* (*0xdd2640)+0xac -> +0xb8 = 1: what the autoload does before a campaign scene start (READ anp_loader.c:do_load; meaning GUESS: "start from the menu") */
    DWORD app = klh_rd32((DWORD_PTR)KLH_VA(KLCMPR_APP)), sub = app ? klh_rd32(app + 0xac) : 0, one = 1;
    if (sub) klh_data((void *)(DWORD_PTR)(sub + 0xb8), &one, 4, "campaign app flag");
}

static char *__cdecl klcmpr_strncpy(char *dst, const char *src, size_t n)
{
    char asked[8], id[8]; int i, anp;
    if (dst != (char *)KLH_VA(KLCMPR_REQ_ID) || n != 4 || !src) return klcmpr_real_strncpy(dst, src, n);
    for (i = 0; i < 4 && src[i]; i++) asked[i] = src[i];
    asked[i] = 0; strcpy(id, asked);
    anp = klcmpr_anp_id(id);
    klcmpr_table_entry(anp ? id : NULL);
    if (anp) klcmpr_mark_app();
    klcmpr.quitreq = strcmp(id, "MM01") == 0;                 /* MM01 = QuitGame / back to the menu (READ g_quitReq) */
    if (klcmpr.log && klcmpr.nroute_log++ < 64) klog("campaign: scene request '%s'%s", id, anp ? " (campaign scene via table entry 12)" : "");
    return klcmpr_real_strncpy(dst, id, n);
}

/* ---------------------------------------------------------------- start a scene (trigger file, AutoLoad) */
static int klcmpr_do_load(const char *id, int mode)
{   /* READ anp_loader.c:do_load. The game thread only. 1 = issued */
    typedef void (__fastcall *setid_t)(void *self, void *edx, const char *id);      /* thiscall, one stack arg, ret 4 */
    typedef void (__fastcall *start_t)(void *self, void *edx);
    DWORD m = (DWORD)mode; int ok = 0;
    if (!klh_exe_ok || !klh_rd32((DWORD_PTR)KLH_VA(KLCMPR_APP))) return 0;
    klog("campaign: starting scene '%s' mode %d", id, mode);
    klcmpr_mark_app();
    klh_data((void *)KLH_VA(KLCMPR_MODE), &m, 4, "campaign scene mode");
    __try {
        ((setid_t)(DWORD_PTR)KLH_VA(KLCMPR_SETID))((void *)KLH_VA(KLCMPR_SCENEREQ), 0, id);
        ((start_t)(DWORD_PTR)KLH_VA(KLCMPR_START))((void *)KLH_VA(KLCMPR_SCENEREQ), 0);
        ok = 1;
    } __except (EXCEPTION_EXECUTE_HANDLER) { klog("campaign: scene start FAULTED (%08lx)", (unsigned long)GetExceptionCode()); }
    return ok;
}

static int klcmpr_read_cmd(const char *name, char *buf, int cap)
{   /* 1 if <DD>\name existed; first line into buf; the file is deleted (READ cmp_read_cmd) */
    char p[MAX_PATH]; FILE *f; int n;
    snprintf(p, sizeof p, "%s\\%s", dir, name);
    if (GetFileAttributesA(p) == INVALID_FILE_ATTRIBUTES) return 0;
    buf[0] = 0;
    f = fopen(p, "r");
    if (f) { if (!fgets(buf, cap, f)) buf[0] = 0; fclose(f); }
    n = (int)strlen(buf);
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == '\r' || buf[n - 1] == ' ' || buf[n - 1] == '\t')) buf[--n] = 0;
    if (!DeleteFileA(p)) klog("campaign: could not delete %s (%lu)", name, GetLastError());
    return 1;
}

/* ---------------------------------------------------------------- scene tracking, save redirect (CreateFileA) */
static int klcmpr_in_campaign(void) { return klcmpr.in_campaign || klcmp_level_active(); }
static int klcmpr_redirect_now(void)
{   /* READ: his mode stays Dead Men until a profile was really re-read, so the redirect also holds while the reload is pending */
    return klcmpr.saves && (klcmpr.sticky || klcmpr.reload_pending || klcmpr_in_campaign());
}

static void klcmpr_scene_arrived(const char *id)
{   /* READ cmp_scene_arrived, reduced to the campaign / not-campaign split (see ADAPTATION above) */
    int was, now_c = klcmpc_dm_index(id) >= 0, fe = strcmp(id, "FE") == 0, done = 0;
    EnterCriticalSection(&klcmpr.cs);
    if (strcmp(id, klcmpr.scene) == 0) { LeaveCriticalSection(&klcmpr.cs); return; }      /* the _LS zip, a reopen: same scene */
    snprintf(klcmpr.prev, sizeof klcmpr.prev, "%s", klcmpr.scene);
    snprintf(klcmpr.scene, sizeof klcmpr.scene, "%s", id);
    was = klcmpr.in_campaign; klcmpr.in_campaign = now_c;
    if (fe) klcmpr.fe_tick = GetTickCount();
    done = fe && !klcmpr.quitreq && (!strcmp(klcmpr.prev, "M14") || !strcmp(klcmpr.prev, "M13B"));
    if (was && !now_c && klcmpr.reload && klcmpr.saves && !klcmpr.sticky) { klcmpr.reload_pending = 1; klcmpr.fe_tick = GetTickCount(); }
    else if (was && !now_c && klcmpr.saves && !klcmpr.reload) klcmpr.sticky = 1;      /* READ cmp_scene_arrived: ProfileReload=0 keeps the campaign slot for the session, else Dog Days' save would be written with the campaign profile */
    else if (now_c) klcmpr.reload_pending = 0;
    LeaveCriticalSection(&klcmpr.cs);
    if (klcmpr.log) klog("campaign: scene '%s' loading (after '%s')%s", id, klcmpr.prev, now_c ? ", campaign level" : "");
    if (now_c) {
        char r[16];
        GetPrivateProfileStringA("DeadMen", "reached", "", r, sizeof r, klcmpr.inipath);
        klcmpr_ini_set("DeadMen", "last", id);
        if (klcmpc_reached_advances(r, id)) klcmpr_ini_set("DeadMen", "reached", id);
    }
    if (done) klcmpr_ini_set("DeadMen", "done", "1");       /* GUESS: leaving M14 / M13B (credits) for the front end without a QuitGame request = finished */
}

static LPCSTR klcmpr_file(LPCSTR n, DWORD acc, DWORD disp)
{   /* READ campaign.inc:campaign_file, without the menu-archive branch */
    const char *b, *ext; size_t bl; char id[8];
    if (!n || !n[0]) return n;
    b = klcmpc_base(n); bl = strlen(b);
    if (bl < 5) return n;
    ext = b + bl - 4;
    if (klcmpr.strredir && klcmpr.dmdir[0] && _stricmp(ext, ".str") == 0 && !(acc & (GENERIC_WRITE | GENERIC_ALL))) {
        static char sring[4][MAX_PATH]; static volatile LONG sri;     /* READ nothing: his two games share one steamapps\common, so his "..\Kane and Lynch Dead Men\" just opened; MINE */
        char *alt = sring[InterlockedIncrement(&sri) & 3];
        if (GetFileAttributesA(n) == INVALID_FILE_ATTRIBUTES && klcmpc_dm_str_target(n, klcmpr.dmdir, alt, MAX_PATH) &&
            GetFileAttributesA(alt) != INVALID_FILE_ATTRIBUTES) {
            static volatile LONG nlog;
            if (klcmpr.log && InterlockedIncrement(&nlog) <= 12) klog("campaign: stream redirect: %s -> %s", n, alt);
            return alt;
        }
    }
    if (_stricmp(ext, ".zip") == 0) {
        if (!(acc & (GENERIC_WRITE | GENERIC_ALL)) && klcmpc_scene_of_path(n, id)) klcmpr_scene_arrived(id);
        return n;
    }
    if (klcmpr.reload_probe && _stricmp(ext, ".kls") == 0 && klcmpc_is_kls(b) && !(acc & GENERIC_WRITE) && disp == OPEN_EXISTING &&
        GetFileAttributesA(n) != INVALID_FILE_ATTRIBUTES)
        InterlockedIncrement(&klcmpr.reload_opens);                 /* klcmpr_profile_reload: the reader reached the file */
    if (_stricmp(ext, ".kls") == 0 && klcmpc_is_kls(b) && klcmpr_redirect_now() && _strnicmp(n, klcmpr.appdir, strlen(klcmpr.appdir)) != 0) {
        static char ring[4][MAX_PATH]; static volatile LONG ri;      /* returned to the caller: one per open */
        char *alt = ring[InterlockedIncrement(&ri) & 3], d[MAX_PATH]; int seeded = 0;
        snprintf(d, sizeof d, "%s\\saves\\Campaign", klcmpr.appdir);
        klcmpr_mkdirs(d);
        if (!klcmpc_save_path(klcmpr.appdir, "Campaign", b, alt, MAX_PATH)) return n;
        if (GetFileAttributesA(alt) == INVALID_FILE_ATTRIBUTES && GetFileAttributesA(n) != INVALID_FILE_ATTRIBUTES)
            seeded = CopyFileA(n, alt, TRUE) ? 1 : -1;
        if (klcmpr.log) klog("campaign: save redirect (%s%s): %s -> %s%s", (acc & GENERIC_WRITE) ? "write" : "read", disp == OPEN_EXISTING ? "" : ", create",
                           n, alt, seeded > 0 ? " (seeded from the Dog Days save)" : seeded < 0 ? " (seed copy FAILED)" : "");
        return alt;
    }
    return n;
}

/* ---------------------------------------------------------------- Dead Men .str: ADPCM -> virtual PCM */
static klcmpr_strfile klcmpr_sf[KLCMPR_NFILE]; static int klcmpr_nsf;
static HANDLE klcmpr_sh[KLCMPR_NSTR]; static BYTE klcmpr_shdr[KLCMPR_NSTR][0x38]; static int klcmpr_sused[KLCMPR_NSTR], klcmpr_sfile[KLCMPR_NSTR];
static CRITICAL_SECTION klcmpr_strcs; static volatile LONG klcmpr_nh;                 /* registered handles: 0 = the hooks are one test */
static volatile LONG klcmpr_vreads, klcmpr_lipblocks, klcmpr_shortreads;

static int klcmpr_sfind(HANDLE h) { int i; for (i = 0; i < KLCMPR_NSTR; i++) if (klcmpr_sused[i] && klcmpr_sh[i] == h) return i; return -1; }

static DWORD klcmpr_raw(klcmpr_strfile *sf, DWORD at, BYTE *dst, DWORD len)
{   /* raw Dead Men bytes [at, at+len) of the source file (caller holds sf->cs) */
    DWORD got = 0;
    if (sf->src == INVALID_HANDLE_VALUE) return 0;
    SetFilePointer(sf->src, (LONG)at, NULL, FILE_BEGIN);
    if (!klcmpr_real_ReadFile(sf->src, dst, len, &got, NULL)) got = 0;
    return got;
}

static void klcmpr_pcm_bytes(klcmpr_strfile *sf, int ei, DWORD b, BYTE *dst, DWORD len)
{   /* copy virtual bytes [b, b+len) of entry ei into dst (caller holds sf->cs); READ anp_loader.c:str_pcm_bytes with lip=1 always on */
    klcmpc_ent *e = &sf->e[ei];
    DWORD bbytes = e->spb * 2 * e->ch;
    BYTE *src = sf->srcbuf;
    if (bbytes > 16384 || e->balign > 8192 || !e->balign || !src || !sf->blk) { memset(dst, 0, len); return; }
    if (!e->lip) {                                           /* probe once: the data starts with 'LIP ' (same rule as tools/sndconv) */
        BYTE h[8]; e->lip = 1;
        if (KLCMPC_LIP % e->balign == 0 && klcmpr_raw(sf, e->dataOff, h, 8) == 8 && memcmp(h, "LIP ", 4) == 0) e->lip = KLCMPC_LIP;
    }
    if (e->lip == KLCMPC_LIP && b < KLCMPC_LIP) {            /* the LIP block itself, verbatim */
        DWORD t = KLCMPC_LIP - b < len ? KLCMPC_LIP - b : len, g = klcmpr_raw(sf, e->dataOff + b, dst, t);
        if (g < t) memset(dst + g, 0, t - g);
        /* 2 Dead Men chunks are longer than the 4 KB block (max 5123 bytes): clamp the length kl2 parses (READ) */
        if (b <= 4 && b + t >= 8) { DWORD *pl = (DWORD *)(dst + 4 - b); if (*pl > KLCMPC_LIP - 8) *pl = KLCMPC_LIP - 8; }
        if (b == 0) InterlockedIncrement(&klcmpr_lipblocks);
        dst += t; b += t; len -= t;
        if (!len) return;
    }
    while (len) {
        unsigned long blk, off; DWORD take;
        klcmpc_vmap(e->lip, e->balign, bbytes, b, &blk, &off);
        take = bbytes - off; if (take > len) take = len;
        if (sf->lastEnt != ei || sf->lastBlk != (int)blk) {
            DWORD at = e->dataOff + blk * e->balign, want = e->balign, got = 0;
            if (blk * e->balign >= e->dataSize) want = 0;
            else if (blk * e->balign + want > e->dataSize) want = e->dataSize - blk * e->balign;
            if (want && sf->src != INVALID_HANDLE_VALUE) {
                SetFilePointer(sf->src, (LONG)at, NULL, FILE_BEGIN);
                klcmpr_real_ReadFile(sf->src, src, want, &got, NULL);
            }
            memset(sf->blk, 0, bbytes);
            if (got >= 4 * e->ch) kladpcm_decode_block(src, (int)got, (int)e->ch, sf->blk, (int)e->spb);
            sf->lastEnt = ei; sf->lastBlk = (int)blk;
        }
        memcpy(dst, (BYTE *)sf->blk + off, take);
        dst += take; b += take; len -= take;
    }
}

static BOOL klcmpr_serve_virtual(klcmpr_strfile *sf, HANDLE h, BYTE *buf, DWORD n, LPDWORD rd, LPOVERLAPPED ov, LONGLONG pos)
{   /* READ anp_loader.c:str_serve_virtual */
    LONGLONG a = pos, b = pos + n, inside = 0; int ei, i;
    memset(buf, 0, n);
    EnterCriticalSection(&sf->cs);
    ei = klcmpc_find_v(sf->e, sf->n, pos);
    for (i = ei < 0 ? 0 : ei; i < sf->n && sf->e[i].voff < b; i++) {
        klcmpc_ent *e = &sf->e[i];
        LONGLONG s0 = e->voff, s1 = e->voff + e->pcm, p0 = a > s0 ? a : s0, p1 = b < s1 ? b : s1;
        if (p1 > p0) { klcmpr_pcm_bytes(sf, i, (DWORD)(p0 - s0), buf + (p0 - a), (DWORD)(p1 - p0)); inside += p1 - p0; }
    }
    LeaveCriticalSection(&sf->cs);
    if (InterlockedIncrement(&klcmpr_vreads) <= 3 && klcmpr.log) klog("campaign: virtual PCM read pos %llx len %lu (entry %d, %lld inside)", (unsigned long long)pos, (unsigned long)n, ei, (long long)inside);
    if (rd) *rd = n;
    if (ov) {
        ov->Internal = 0; ov->InternalHigh = n;
        if (ov->hEvent) SetEvent((HANDLE)((ULONG_PTR)ov->hEvent & ~(ULONG_PTR)1));
    } else { LARGE_INTEGER np; np.QuadPart = pos + n; SetFilePointerEx(h, np, NULL, FILE_BEGIN); }
    return TRUE;
}

static BOOL WINAPI klcmpr_ReadFile(HANDLE h, LPVOID buf, DWORD n, LPDWORD rd, LPOVERLAPPED ov)
{
    int k = -1; LONGLONG pos = -1; klcmpr_strfile *sf = NULL; BOOL r; DWORD got = 0;
    if (klcmpr_nh <= 0 || h == INVALID_HANDLE_VALUE) return klcmpr_real_ReadFile(h, buf, n, rd, ov);
    EnterCriticalSection(&klcmpr_strcs); k = klcmpr_sfind(h); LeaveCriticalSection(&klcmpr_strcs);
    if (k < 0) return klcmpr_real_ReadFile(h, buf, n, rd, ov);
    sf = &klcmpr_sf[klcmpr_sfile[k]];
    if (ov) pos = (LONGLONG)ov->Offset | ((LONGLONG)ov->OffsetHigh << 32);
    else { LONG hi = 0; DWORD lo = SetFilePointer(h, 0, &hi, FILE_CURRENT); pos = (LONGLONG)lo | ((LONGLONG)hi << 32); }
    if (pos >= KLCMPC_VBASE && sf->n) return klcmpr_serve_virtual(sf, h, (BYTE *)buf, n, rd, ov, pos);
    r = klcmpr_real_ReadFile(h, buf, n, rd, ov);
    if (!r && ov && GetLastError() == ERROR_IO_PENDING) {
        r = GetOverlappedResult(h, ov, &got, TRUE);
        if (rd) *rd = got;
    } else got = rd ? *rd : (ov ? (DWORD)ov->InternalHigh : n);
    if (r && got && pos >= 0) klcmpc_overlay((unsigned char *)buf, pos, got, klcmpr_shdr[k], sf->e, sf->n, sf->tbl, sf->cnt);
    /* zerofill (his default): a short real read gets the rest zeroed - kl2's streamer ignores the byte count, so stale buffer bytes
       past EOF (Dead Men's empty PC_Eng.str) were parsed as LIP / audio (READ anp_loader.c:my_ReadFile, sound switch zerofill=1) */
    if (!r && GetLastError() == ERROR_HANDLE_EOF) { InterlockedIncrement(&klcmpr_shortreads); memset(buf, 0, n); SetLastError(ERROR_HANDLE_EOF); }
    else if (r && got < n) { InterlockedIncrement(&klcmpr_shortreads); memset((BYTE *)buf + got, 0, n - got); }
    return r;
}

static BOOL WINAPI klcmpr_CloseHandle(HANDLE h)
{
    if (klcmpr_nh > 0) {
        int k;
        EnterCriticalSection(&klcmpr_strcs);
        k = klcmpr_sfind(h); if (k >= 0) { klcmpr_sused[k] = 0; InterlockedDecrement(&klcmpr_nh); }
        LeaveCriticalSection(&klcmpr_strcs);
    }
    return klcmpr_real_CloseHandle(h);
}

static void klcmpr_str_register(HANDLE h, const char *n)
{   /* READ anp_loader.c:str_register. Header check by CONTENT (klcmpc_str_is_dm), not by path (MINE: the converted levels' .str are in the DD folder). */
    BYTE dm[0x38], dd[0x38]; HANDLE r; DWORD got = 0, tbl, cnt; int fi = -1, i, k;
    r = klcmpr_real_CreateFileA(n, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
    if (r == INVALID_HANDLE_VALUE) return;
    if (!klcmpr_real_ReadFile(r, dm, 0x38, &got, NULL) || got < 0x38 || !klcmpc_str_is_dm(dm)) { klcmpr_real_CloseHandle(r); return; }
    klcmpr_real_CloseHandle(r);
    klcmpc_str_hdr_dd(dm, dd);
    tbl = (DWORD)klcmpc_rd32(dm + 0x18); cnt = (DWORD)klcmpc_rd32(dm + 0x1c);
    for (i = 0; i < klcmpr_nsf; i++) if (_stricmp(klcmpr_sf[i].path, n) == 0) fi = i;
    if (fi < 0 && klcmpr_nsf < KLCMPR_NFILE) {
        HANDLE r2 = klcmpr_real_CreateFileA(n, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
        klcmpr_strfile *sf = &klcmpr_sf[klcmpr_nsf]; klcmpc_ent *ents = 0; int ne = 0; long long vend = KLCMPC_VBASE;
        if (r2 == INVALID_HANDLE_VALUE) return;
        memset(sf, 0, sizeof *sf);
        snprintf(sf->path, sizeof sf->path, "%s", n);
        {   /* the index: cnt records of 72 bytes at tbl; the meta block of each (36 bytes) */
            BYTE *t = (BYTE *)malloc((size_t)cnt * 72 + 1); DWORD g2 = 0;       /* +1: an empty stream (PC_Eng.str, count 0) still registers */
            ents = (klcmpc_ent *)malloc(sizeof(klcmpc_ent) * (cnt + 1));
            if (t && ents) {
                SetFilePointer(r2, (LONG)tbl, NULL, FILE_BEGIN);
                klcmpr_real_ReadFile(r2, t, cnt * 72, &g2, NULL);
                if (g2 == cnt * 72) for (i = 0; i < (int)cnt; i++) {
                    BYTE *rec = t + (size_t)i * 72; DWORD mOff = (DWORD)klcmpc_rd32(rec + 24), mSz = (DWORD)klcmpc_rd32(rec + 32), g3 = 0; unsigned long meta[9] = {0};
                    if (mSz == 36) {
                        SetFilePointer(r2, (LONG)mOff, NULL, FILE_BEGIN);
                        klcmpr_real_ReadFile(r2, meta, 36, &g3, NULL);
                        if (g3 == 36 && klcmpc_ent_from(rec, meta, tbl, (unsigned long)i, &ents[ne])) ne++;
                    }
                }
                vend = klcmpc_layout(ents, ne);
            }
            free(t);
        }
        klcmpr_real_CloseHandle(r2);
        sf->e = ents; sf->n = ne; sf->tbl = tbl; sf->cnt = cnt; sf->lastEnt = -1; sf->lastBlk = -1;
        sf->blk = (short *)malloc(sizeof(short) * 2 * 4096); sf->srcbuf = (BYTE *)malloc(8192);
        InitializeCriticalSection(&sf->cs);
        sf->src = klcmpr_real_CreateFileA(n, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
        fi = klcmpr_nsf++;
        klog("campaign: Dead Men stream %s: %d ADPCM entries -> virtual PCM %llx..%llx (4 KB LIP block served verbatim)", n, ne, (unsigned long long)KLCMPC_VBASE, (unsigned long long)vend);
    }
    if (fi < 0) return;
    EnterCriticalSection(&klcmpr_strcs);
    k = klcmpr_sfind(h);
    if (k < 0) for (i = 0; i < KLCMPR_NSTR; i++) if (!klcmpr_sused[i]) { k = i; break; }
    if (k >= 0) {
        if (!klcmpr_sused[k]) InterlockedIncrement(&klcmpr_nh);
        klcmpr_sh[k] = h; memcpy(klcmpr_shdr[k], dd, 0x38); klcmpr_sused[k] = 1; klcmpr_sfile[k] = fi;
    }
    LeaveCriticalSection(&klcmpr_strcs);
    klog("campaign: Dead Men stream %s: table %08lx count %lu -> Dog Days header%s", n, (unsigned long)tbl, (unsigned long)cnt, k < 0 ? " (NO free handle slot: raw)" : "");
}

static HANDLE WINAPI klcmpr_CreateFileA(LPCSTR n, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t)
{
    HANDLE h; size_t L;
    n = klcmpr_file(n, a, c);
    h = klcmpr_real_CreateFileA(n, a, s, sa, c, f, t);
    if (klcmpr.adpcm && h != INVALID_HANDLE_VALUE && n && c == OPEN_EXISTING && !(a & GENERIC_WRITE) && (L = strlen(n)) > 4 && _stricmp(n + L - 4, ".str") == 0)
        klcmpr_str_register(h, n);
    return h;
}

/* ---------------------------------------------------------------- achievements guard (vptr swap, .data) */
static DWORD klcmpr_achvt[5];                                       /* [COL, slot0..3]; the object's vptr -> &klcmpr_achvt[1] */
static int __fastcall klcmpr_ach_block(void *self, void *edx, int a, int b)
{   /* slot 3 (award, 0x72fd60): thiscall, two stack args, ret 8 */
    static int n;
    (void)self; (void)edx;
    if (n++ < 20) klog("campaign: achievement award (%d, %d) blocked (campaign level)", a, b);
    return 0;
}
static void klcmpr_ach_guard(int want)
{   /* READ cmp_ach_guard */
    DWORD *obj = (DWORD *)KLH_VA(KLCMPR_ACH_OBJ), cur = klh_rd32((DWORD_PTR)obj), vt = (DWORD)(DWORD_PTR)KLH_VA(KLCMPR_ACH_VT), mine = (DWORD)(DWORD_PTR)&klcmpr_achvt[1];
    if (!cur) return;
    if (want && cur == vt) {
        if (!klcmpr_achvt[0] && !klh_rd(vt - 4, klcmpr_achvt, sizeof klcmpr_achvt)) return;
        klcmpr_achvt[4] = (DWORD)(DWORD_PTR)klcmpr_ach_block;
        if (klh_data(obj, &mine, 4, "campaign achievements vptr")) klog("campaign: achievement guard on");
    } else if (!want && cur == mine) {
        if (klh_data(obj, &vt, 4, "campaign achievements vptr")) klog("campaign: achievement guard off");
    }
}

/* ---------------------------------------------------------------- profile reload */
static void klcmpr_profile_reload(void)
{   /* READ cmp_profile_reload. Game thread only. Re-reads Dog Days' own profile; the redirect drops only after a real re-read. */
    typedef int (__fastcall *reader_t)(void *self, void *edx, int slot);             /* 0x47c5f0: thiscall, one stack arg, ret 4 */
    BYTE one = 1, ps = 0; int r = -1;
    klcmpr.reload_pending = 0;
    if (!klh_exe_ok || !klh_rd((DWORD_PTR)KLH_VA(KLCMPR_PRESSSTART), &ps, 1) || !ps) {          /* reader and writer are no-ops before Press Start */
        klog("campaign: profile reload skipped (no profile loaded: Press Start not done)");
        return;
    }
    klcmpr.reload_opens = 0; klcmpr.reload_probe = 1;
    klh_data((void *)KLH_VA(KLCMPR_PROFILE_FLAG), &one, 1, "campaign profile flag");
    __try { r = ((reader_t)(DWORD_PTR)KLH_VA(KLCMPR_PROFILE_READ))((void *)KLH_VA(KLCMPR_PROFILE), 0, 0); }
    __except (EXCEPTION_EXECUTE_HANDLER) { klog("campaign: profile reload FAULTED (%08lx)", (unsigned long)GetExceptionCode()); r = -1; }
    klcmpr.reload_probe = 0;
    if (klcmpr.reload_opens >= 2) { klog("campaign: profile reload done (%d), save file opened %ld time(s): read from disk", r, (long)klcmpr.reload_opens); return; }
    klcmpr.sticky = 1;                                         /* the reader did not reach the file: keep the redirect for this session */
    klog("campaign: profile reload did NOT re-read the Dog Days save (%ld open(s), result %d): the campaign slot stays live for the rest of this session so Dog Days' save is never written with this profile", (long)klcmpr.reload_opens, r);
}

/* ---------------------------------------------------------------- init, tick */
static void klcmpr_init(void)
{
    int n;
    memset(&klcmpr, 0, sizeof klcmpr);
    if (!klcmp_enabled()) return;                           /* master off: nothing installed, nothing read */
    klcmpr.routing  = GetPrivateProfileIntA("Campaign", "Routing", 0, klh_ini) != 0;
    klcmpr.trigger  = GetPrivateProfileIntA("Campaign", "Trigger", 0, klh_ini) != 0;
    klcmpr.saves    = GetPrivateProfileIntA("Campaign", "SaveRedirect", 0, klh_ini) != 0;
    klcmpr.reload   = GetPrivateProfileIntA("Campaign", "ProfileReload", 0, klh_ini) != 0;
    klcmpr.progress = GetPrivateProfileIntA("Campaign", "Progress", 0, klh_ini) != 0;
    klcmpr.ach      = GetPrivateProfileIntA("Campaign", "AchievementGuard", 0, klh_ini) != 0;
    klcmpr.adpcm    = GetPrivateProfileIntA("Campaign", "Adpcm", 0, klh_ini) != 0;
    klcmpr.strredir = GetPrivateProfileIntA("Campaign", "StreamRedirect", 1, klh_ini) != 0;
    klcmpr.log      = GetPrivateProfileIntA("Campaign", "Log", 1, klh_ini) != 0;
    klcmpr.reload_delay = (DWORD)GetPrivateProfileIntA("Campaign", "ReloadDelayMs", 2000, klh_ini);
    klcmpr.auto_delay = (DWORD)GetPrivateProfileIntA("Campaign", "AutoLoadDelayMs", 12000, klh_ini);
    klcmpr.auto_mode = GetPrivateProfileIntA("Campaign", "AutoLoadMode", 1, klh_ini);
    { char a[32] = ""; GetPrivateProfileStringA("Campaign", "AutoLoad", "", a, sizeof a, klh_ini);
      if (a[0] && !klcmpc_parse_load(a, klcmpr.auto_id, &n)) { klog("campaign: AutoLoad='%s' is not a scene id: ignored", a); klcmpr.auto_id[0] = 0; }
      else if (a[0]) { char m[8]; if (klcmpc_parse_load(a, m, &n) && strchr(a, ' ')) klcmpr.auto_mode = n; } }
    klcmpr.t0 = GetTickCount();
    InitializeCriticalSection(&klcmpr.cs); InitializeCriticalSection(&klcmpr_strcs);
    klcmpr_paths();
    if (klcmpr.strredir) klcmpr_find_dm();
    if (klcmpr.routing) {
        n = klh_iat("MSVCR90.dll", "strncpy", (void *)klcmpr_strncpy, (void **)&klcmpr_real_strncpy);
        klog("campaign: Routing: strncpy import %s", n && klcmpr_real_strncpy ? "hooked" : "NOT hooked: campaign scene ids will not resolve");
        if (!klcmpr_real_strncpy) klcmpr.routing = 0;
    }
    if (klcmpr.saves || klcmpr.progress || klcmpr.adpcm || klcmpr.ach || klcmpr.reload || klcmpr.dmdir[0]) {
        /* scene tracking + save redirect + .str registration all ride on one CreateFileA wrapper, chained to whatever the slot held (klslot.c's) */
        n = klh_iat("KERNEL32.dll", "CreateFileA", (void *)klcmpr_CreateFileA, (void **)&klcmpr_real_CreateFileA);
        klog("campaign: CreateFileA import %s", n && klcmpr_real_CreateFileA ? "hooked" : "NOT hooked: no scene tracking / save redirect / ADPCM");
        if (!klcmpr_real_CreateFileA) { klcmpr.saves = klcmpr.progress = klcmpr.adpcm = klcmpr.reload = 0; klcmpr.dmdir[0] = 0; }
    }
    if (klcmpr.adpcm) {
        n = klh_iat("KERNEL32.dll", "ReadFile", (void *)klcmpr_ReadFile, (void **)&klcmpr_real_ReadFile);
        n += klh_iat("KERNEL32.dll", "CloseHandle", (void *)klcmpr_CloseHandle, (void **)&klcmpr_real_CloseHandle);
        klog("campaign: Adpcm: ReadFile %s, CloseHandle %s", klcmpr_real_ReadFile ? "hooked" : "NOT hooked", klcmpr_real_CloseHandle ? "hooked" : "NOT hooked");
        if (!klcmpr_real_ReadFile || !klcmpr_real_CloseHandle) { klcmpr.adpcm = 0; klog("campaign: Adpcm off (a lone hook is never left in)"); }
    }
    klcmpr.on = klcmpr.routing || klcmpr.trigger || klcmpr.saves || klcmpr.progress || klcmpr.ach || klcmpr.adpcm || klcmpr.dmdir[0] || klcmpr.auto_id[0];
    klog("campaign: Dead Men streams: redirect %s (dir '%s'), adpcm %d", klcmpr.strredir ? "on" : "off", klcmpr.dmdir, klcmpr.adpcm);
    klog("campaign: core %s (routing %d trigger %d autoload '%s' saves %d reload %d progress %d achievements %d adpcm %d) data %s",
         klcmpr.on ? "on" : "idle", klcmpr.routing, klcmpr.trigger, klcmpr.auto_id, klcmpr.saves, klcmpr.reload, klcmpr.progress, klcmpr.ach, klcmpr.adpcm, klcmpr.appdir);
}

static void klcmpr_tick(int game_thread)
{
    DWORD now; unsigned long steady; char b[96], id[8]; int mode;
    if (!klcmpr.on || !game_thread) return;
    now = GetTickCount();
    steady = klcmpc_steady_update(&klcmpr.steady, now, 250);           /* a scene load blocks the pump: gaps of seconds */
    if (klcmpr.reload_pending && !klcmpr_in_campaign() && now - klcmpr.fe_tick >= klcmpr.reload_delay && steady >= 1000) klcmpr_profile_reload();
    if (klcmpr.auto_id[0] && !klcmpr.auto_done && now - klcmpr.t0 >= klcmpr.auto_delay && steady >= 1000 && !klcmpr_in_campaign()) {
        klcmpr.auto_done = 1;
        if (klcmpr_anp_id(klcmpr.auto_id) || klcmpr_stock_id(klcmpr.auto_id)) klcmpr_do_load(klcmpr.auto_id, klcmpr.auto_mode);
        else klog("campaign: AutoLoad '%s': no Scenes\\Locations\\%s\\%s_Main.zip, nothing started", klcmpr.auto_id, klcmpr.auto_id, klcmpr.auto_id);
    }
    if (now - klcmpr.t_slow < 500) return;
    klcmpr.t_slow = now;
    if (klcmpr.ach) klcmpr_ach_guard(klcmpr_in_campaign());
    if (klcmpr.trigger && steady >= 1000 && klcmpr_read_cmd("KLCampaign_load.txt", b, sizeof b)) {
        if (klcmpc_parse_load(b, id, &mode) && (klcmpr_anp_id(id) || klcmpr_stock_id(id))) klcmpr_do_load(id, mode);
        else klog("campaign: KLCampaign_load.txt '%s': not a scene id that exists, ignored", b);
    }
}
