/*
 * klsteam.c - nothing an expansion map or a test round does reaches the owner's Steam profile: a proxy
 * ISteamUserStats behind the import slot of steam_api.SteamUserStats. Part of KLHook (included by klhook.c, SHIP
 * and TEST alike). Reasoning and the game's side of it: re\leaderboard.md (section 4.2 is this file's design).
 *
 * WHY: the engine treats a Dead Men map in a stock slot as the stock map. At the END of an Arcade session
 * (session state 0x28: the last life lost, or Quit in the pause menu) one handler uploads the session total to the
 * slot's public board (KL2_Heist<n>_TotalMoney, keep-best), commits 27 stats including the multiplayer rank and
 * evaluates achievements. None of that may happen for a level that is not the stock level of its slot, and never
 * from a test rig.
 *
 * HOW: one import slot, no byte of kl2.exe's code.
 *   0xb107c8 = kl2.exe's import of steam_api.dll SteamUserStats (`ceg_ranges.py 0xb107c8:4`: 0 checks). The game
 *   calls it afresh at each of its 14 uses and never keeps the pointer beyond one function, so the wrapper below
 *   answers every call with a proxy object: one dword pointing at a table of 30 functions. 21 of them jump straight
 *   into the real interface (every read); 9 look at the policy first and either fail or call the real method.
 *
 * THE INTERFACE VERSION AND HOW EACH SLOT WAS VERIFIED (2026-10-09, nothing from memory alone)
 *   - kl2.exe holds no interface version text: it only calls the accessor. <DD>\steam_api.dll (121,984 bytes, sha1
 *     20867924..., linked 2010-01-27) holds exactly one: "STEAMUSERSTATS_INTERFACE_VERSION007" (with
 *     "SteamClient009"). klx_init looks for that text in the loaded steam_api.dll and refuses to guard without it.
 *   - Slot count and argument bytes: C:\Steam\steamclient.dll still carries the class CAdapterSteamUserStats007
 *     (RTTI; vtable at +0x103b344 of the 21 MB build read). Its vtable has 30 entries before the next object; the
 *     bytes each one pops (its `ret n`; T = a tail jump into the current interface) are
 *         slot   0  1  2  3  4  5   6  7  8  9   10 11 12 13  14 15  16  17  18  19 20 21 22 23 24 25 26  27  28  29
 *         bytes  0  8  8  8  8  16  8  4  4  12  0  4  8  12  8  16  16  16  20  4  T  T  8  8  8  8  20  24  24  T
 *     The 006 adapter has 28 entries: the same list without slots 9 and 18 (the two ...AndUnlockTime calls 007
 *     added); the 008 adapter has 31 (one 16-byte call before the last). So the table is 007's and 30 long.
 *   - The game's own call sites (all 14 references to the slot were read) push exactly those bytes:
 *         +0x00 slot 0   0 args            0x6ca9ff  RequestCurrentStats
 *         +0x08 slot 2   2 args            0x46f5de  GetStat(name, int *)             27 names
 *         +0x10 slot 4   2 args            0x555057  SetStat(name, int)               27 names, results ignored
 *         +0x18 slot 6   2 args            0x8c17da  GetAchievement
 *         +0x1c slot 7   1 arg             0x72fdac  SetAchievement(name); `test al,al ; je` skips StoreStats
 *         +0x28 slot 10  0 args            0x55522f, 0x72fdbb  StoreStats, result ignored at both
 *         +0x50 slot 20  3 args (n, 2, 1)  0x5ebe55, 0x789736  FindOrCreateLeaderboard, 64-bit result
 *         +0x5c slot 23  2 dwords          0x755269, 0x827c78  GetLeaderboardEntryCount(handle)
 *         +0x68 slot 26  5 dwords          0x755287  DownloadLeaderboardEntries
 *         +0x6c slot 27  6 dwords          0x6ddbc5, 0x8aeb..  GetDownloadedLeaderboardEntry
 *         +0x70 slot 28  6 dwords          0x7ef437  UploadLeaderboardScore(handle, 1 = keep best, score, 0, 0);
 *                                          `or ecx,edx ; je 0x7ef458` = handle 0 -> task status 3 (failed)
 *   - NAMES: from the Steamworks 1.0x header as remembered (ASSUMPTION for the slots the game never calls: 3, 5,
 *     8, 13, 19; their argument bytes are the adapter's, so a wrong name there cannot unbalance a stack). MSVC lays
 *     overloads out in reverse order of declaration: slot 1 / 3 are the float forms, 2 / 4 the int forms - the game
 *     calls +0x08 and +0x10 with integers from its profile block.
 *   The proxy does not touch steam_api.dll or steamclient.dll and reads the real table through the pointer the
 *   real accessor returns, each time.
 *
 * WHAT IS FAILED, AND HOW THE GAME TAKES IT
 *   slot 28 UploadLeaderboardScore  -> handle 0: the game's own failure branch 0x7ef458 (task status 3)
 *   slot 3, 4 SetStat               -> false (ignored by 0x555020)
 *   slot 10 StoreStats              -> false (ignored)
 *   slot 7 SetAchievement           -> false: 0x72fdb0 then skips its StoreStats
 *   slot 5, 8, 13, 19 UpdateAvgRateStat, ClearAchievement, IndicateAchievementProgress, ResetAllStats -> false
 *     (the game never calls them; they are writes all the same)
 *   Everything else forwards: RequestCurrentStats, GetStat, GetAchievement, the leaderboard find / download calls.
 *   FindOrCreateLeaderboard is forwarded too (the stock boards exist, so it creates nothing); on an expansion map
 *   the score page therefore still shows the stock map's friends rows (re\leaderboard.md 4.3 - not done here).
 *
 * WHEN (the policy)
 *   TEST build: always, every write. No key turns it off.
 *   SHIP build: a write is blocked when the level is NOT THE STOCK LEVEL OF ITS SLOT.
 *     - "The level" = the engine's scene name, read at the moment of the call: *(char **)([0xdd2640] + 0x2b0),
 *       e.g. 'SCENES\Locations\F01\F01_Main.gms' (seen in every klauto log) -> archive key 'f01\f01_main.zip'.
 *     - "Stock" = the file the game actually opened for that key (after klslot's redirect, overlay, [Slots]) has
 *       the size and the central-directory hash of the stock archive (klstock.h, 22 archives, generated by
 *       mkstock.py from the game folder and KL_PortBackup; the directory holds every member's CRC). Compiled in,
 *       not "recorded at first run": this machine's first run would have recorded a graft as stock.
 *       The CreateFileA / CreateFileW wrappers of klslot.c report every read-only open of a level archive
 *       (klh_level_open); they are installed whether or not [Expansion] is enabled.
 *     - A level whose archive was never seen being opened, or could not be read, is blocked too (fail closed), but
 *       does not leave the 'until restart' mark below: the hook being blind must not cost a whole evening's stats.
 *     - Leaderboard upload: blocked while the current level (or, in the frontend, the last one) is not stock.
 *     - Stats and achievements: blocked from the moment a non-stock level runs UNTIL THE PROCESS ENDS. The stats
 *       block in memory is cumulative (SetStat writes totals), so a later stock session would carry the expansion
 *       rounds out with it. At the next start the game reads the block back from Steam (0x46f5a0), clean.
 *     - Patch01.zip (mounted first, overrides members of every archive): if the one opened holds anything but
 *       menu/, menu/frontend.xml and menu/ingame.xml, every level counts as not stock.
 *     - [Steam] Block=2 blocks everything always.
 *   HOW IT CAN BE FOOLED (accidents are what it is for; it is not a cheat barrier - the user can delete the DLL)
 *     - a level changed without changing its archive's directory: a member edited so that size and CRC-32 stay;
 *       or content supplied through another route (a changed Scenes\AllLevels archive, PC_Def.str, kaneandlynch.zip,
 *       a loose file the engine prefers over the archive - none seen, not ruled out);
 *     - an archive opened through an API other than the two wrapped ones: then its key is unknown and the level
 *       counts as not stock (safe side). Seen live: the engine opens F01_Main.zip with CreateFileA (run X2);
 *     - the scene-name field naming something else than the running level at the moment of a call (ASSUMPTION:
 *       it does not; klauto has used it for every 'LOAD end' line);
 *     - a game update: klstock.h then calls every level 'not stock' (safe side) until mkstock.py is re-run;
 *     - a peer without the hook in an online session writes its own stats (stage 4).
 *   Reads always work. Steam offline mode is not needed and not relied on.
 *
 * LOG (KLHook.log)
 *   steam: import SteamUserStats wrapped ...                  at start
 *   steam: level archive f01\f01_main.zip opened from ...: STOCK | NOT stock (...)
 *   steam: level 'SCENES\Locations\F01\F01_Main.gms': ...     when the scene changes
 *   steam: BLOCKED UploadLeaderboardScore(board 'KL2_Heist0_TotalMoney', keep best, score 12345) - <why>
 *   steam: BLOCKED SetStat('NumRoundsPlayed', 12) - <why>     each method + name once per level
 *   steam: passed on StoreStats() - stock level               what went out, once per level
 *   session: state 0x20 -> 0x28 ... SESSION END               the moment the game uploads (re\leaderboard.md 2.2)
 *
 * KLHook.ini
 *   [Steam]
 *   Block=1     SHIP: 1 = the policy above, 2 = block every write always. (0 is read as 1: there is no off.)
 *   Log=1       2 = log every blocked / passed write, not only the first per level
 *   State=1     0 = no 'session:' lines
 *
 * TESTED OFF-GAME (scratch harness `ihook`, sources not in the repo): a stub steam_api.dll whose ISteamUserStats
 * records every call; all 30 slots called through the proxy with marker arguments (stack balance, return values,
 * forwarding), the policy against made-up scenes and archives, the session line. NOT RUN LIVE.
 */
#ifndef KLSTEAM_C
#define KLSTEAM_C
#include "klstock.h"

#define KLX_NSLOT    30
#define KLX_SESSION  0x0168e598               /* the session manager; +0x70 state, +0x5c game mode (4 = Arcade) */
#define KLX_NARCH    48

enum { KLX_BOARD, KLX_STATS };
static void *(__cdecl *klx_real_accessor)(void);
static void **klx_real;                       /* the real ISteamUserStats (points at its vtable pointer); set at each accessor call */
static void *klx_vt[KLX_NSLOT];
static struct { void **vt; } klx_proxy = { klx_vt };
static int klx_on, klx_log = 1, klx_state_on = 1;
#ifdef KLHOOK_TEST
static int klx_always = 1;                    /* a TEST build never writes to Steam; not read from the ini */
#else
static int klx_always;
#endif
static CRITICAL_SECTION klx_cs;
static char klx_game_low[MAX_PATH];
static struct { char key[40]; int verdict; char why[150]; char path[MAX_PATH]; DWORD size, hash; FILETIME ft; } klx_arch[KLX_NARCH];
static int klx_narch;
static char klx_patch_extra[80];              /* a member of the opened Patch01.zip that is not a menu file */
static char klx_taint[200];                   /* why stats stay blocked for the rest of this process */
static int klx_last_verdict; static char klx_last_why[200];      /* the last level scene seen: 1 stock, 2 not */
static LONG klx_nblocked[2], klx_npassed[2];
static DWORD klx_said[160]; static int klx_nsaid;

/* ---------------------------------------------------------------- the stock test */

static DWORD klx_fnv(const BYTE *p, DWORD n, DWORD h) { while (n--) h = (h ^ *p++) * 16777619u; return h; }

/* size, write time and central-directory hash of a zip; extra (may be 0) receives the first member that is not
   one of Patch01.zip's stock three. Uses this DLL's own imports, never the wrapped ones. -> 1 ok */
static int klx_fingerprint(const char *path, DWORD *size, DWORD *hash, FILETIME *ft, char extra[80])
{
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 0, OPEN_EXISTING, 0, 0);
    BYTE tail[4096], *cd = 0; DWORD hi = 0, lo, n, got = 0, cdsize, cdoff, o; int i, ok = 0;
    if (f == INVALID_HANDLE_VALUE) return 0;
    lo = GetFileSize(f, &hi); GetFileTime(f, 0, 0, ft);
    if (hi || lo < 22) goto out;                              /* no stock level archive reaches 4 GB */
    n = lo < sizeof tail ? lo : sizeof tail;                  /* the record is the last 22 bytes unless the zip has a comment */
    if (SetFilePointer(f, lo - n, 0, FILE_BEGIN) == INVALID_SET_FILE_POINTER || !ReadFile(f, tail, n, &got, 0) || got != n) goto out;
    for (i = (int)n - 22; i >= 0 && memcmp(tail + i, "PK\5\6", 4); i--) ;
    if (i < 0) goto out;
    cdsize = *(DWORD *)(tail + i + 12); cdoff = *(DWORD *)(tail + i + 16);
    if (!cdsize || cdsize > (16u << 20) || cdoff > lo || cdsize > lo - cdoff) goto out;
    cd = (BYTE *)HeapAlloc(GetProcessHeap(), 0, cdsize);
    if (!cd || SetFilePointer(f, cdoff, 0, FILE_BEGIN) == INVALID_SET_FILE_POINTER || !ReadFile(f, cd, cdsize, &got, 0) || got != cdsize) goto out;
    *size = lo; *hash = klx_fnv(cd, cdsize, 2166136261u); ok = 1;
    if (extra) {
        extra[0] = 0;
        for (o = 0; o + 46 <= cdsize && !memcmp(cd + o, "PK\1\2", 4); ) {
            DWORD nl = *(WORD *)(cd + o + 28), el = *(WORD *)(cd + o + 30), cl = *(WORD *)(cd + o + 32); char nm[80]; DWORD k;
            if (o + 46 + nl > cdsize) break;
            for (k = 0; k < nl && k < sizeof nm - 1; k++) { char c = (char)cd[o + 46 + k]; nm[k] = (char)(c >= 'A' && c <= 'Z' ? c + 32 : c == '\\' ? '/' : c); }
            nm[k] = 0;
            if (strcmp(nm, "menu/") && strcmp(nm, "menu/frontend.xml") && strcmp(nm, "menu/ingame.xml")) { strcpy(extra, nm); break; }
            o += 46 + nl + el + cl;
        }
    }
out:
    if (cd) HeapFree(GetProcessHeap(), 0, cd);
    CloseHandle(f);
    return ok;
}

static int klx_find_arch(const char *key)
{
    int i;
    for (i = 0; i < klx_narch; i++) if (!strcmp(klx_arch[i].key, key)) return i;
    return -1;
}

/* From klslot.c's CreateFileA / CreateFileW wrappers, BEFORE the real open: the game asks for 'asked' read-only
   and 'opened' is the path it will get. Cheap for everything that is not a .zip. Keeps GetLastError. */
static void klh_level_open(const char *asked, const char *opened)
{
    char full[MAX_PATH], low[MAX_PATH], key[64], line[400], *p; size_t l; DWORD err, n, size = 0, hash = 0; FILETIME ft; int i, k, v, fresh;
    if (!klx_on || !asked || (l = strlen(asked)) < 5 || _stricmp(asked + l - 4, ".zip")) return;
    err = GetLastError();
    n = GetFullPathNameA(asked, MAX_PATH, full, 0);
    if (!n || n >= MAX_PATH) { SetLastError(err); return; }
    for (p = full, i = 0; (low[i] = (char)(*p >= 'A' && *p <= 'Z' ? *p + 32 : *p)) != 0; p++, i++) ;
    l = strlen(klx_game_low);
    if (!strncmp(low, klx_game_low, l) && !strcmp(low + l, "\\patch01.zip")) {
        char extra[80] = ""; static LONG patchseen;
        if (klx_fingerprint(opened, &size, &hash, &ft, extra) && (strcmp(extra, klx_patch_extra) || !InterlockedExchange(&patchseen, 1))) {
            EnterCriticalSection(&klx_cs); strcpy(klx_patch_extra, extra); LeaveCriticalSection(&klx_cs);
            if (extra[0]) klog("steam: Patch01.zip opened from %s holds '%s': not a menu file, it can override level members - EVERY level counts as not stock from now on", opened, extra);
            else klog("steam: Patch01.zip opened from %s holds menu files only", opened);
        }
        SetLastError(err); return;
    }
    if (!(p = strstr(low, "\\scenes\\locations\\")) || strlen(p + 18) >= sizeof key) { SetLastError(err); return; }
    strcpy(key, p + 18);
    if (!(p = strchr(key, '\\')) || strchr(p + 1, '\\') || !strcmp(p + 1, "loader_sequence.zip")) { SetLastError(err); return; }   /* <folder>\<file>.zip only */
    for (k = 0; k < KLX_NSTOCK && strcmp(klx_stock[k].key, key); k++) ;
    EnterCriticalSection(&klx_cs);
    i = klx_find_arch(key);
    if (i < 0 && klx_narch < KLX_NARCH) { i = klx_narch++; memset(&klx_arch[i], 0, sizeof klx_arch[i]); strcpy(klx_arch[i].key, key); }
    LeaveCriticalSection(&klx_cs);
    if (i < 0) { SetLastError(err); return; }                 /* table full: the key stays unknown = not stock */
    if (!klx_fingerprint(opened, &size, &hash, &ft, 0)) {
        if (klx_arch[i].verdict && !_stricmp(klx_arch[i].path, opened)) { SetLastError(err); return; }      /* held open by the game: what was read before stands */
        v = 3; snprintf(line, sizeof line, "could not be read as a zip");
    } else if (k == KLX_NSTOCK) { v = 2; snprintf(line, sizeof line, "not a stock level name (%lu bytes, directory hash %08lx)", size, hash); }
    else if (size != klx_stock[k].size || hash != klx_stock[k].hash) { v = 2; snprintf(line, sizeof line, "%lu bytes, directory hash %08lx; the stock archive has %lu bytes, %08lx", size, hash, klx_stock[k].size, klx_stock[k].hash); }
    else { v = 1; snprintf(line, sizeof line, "%lu bytes, directory hash %08lx", size, hash); }
    EnterCriticalSection(&klx_cs);
    fresh = klx_arch[i].verdict != v || _stricmp(klx_arch[i].path, opened) || klx_arch[i].size != size || klx_arch[i].hash != hash;
    klx_arch[i].verdict = v; klx_arch[i].size = size; klx_arch[i].hash = hash; klx_arch[i].ft = ft;
    snprintf(klx_arch[i].path, MAX_PATH, "%s", opened);
    snprintf(klx_arch[i].why, sizeof klx_arch[i].why, v == 1 ? "stock" : v == 3 ? "its archive %s %s" : "its archive %s is not the stock one: %s", key, line);
    LeaveCriticalSection(&klx_cs);
    if (fresh) klog("steam: level archive %s opened from %s: %s (%s)", key, opened, v == 1 ? "STOCK" : v == 3 ? "NOT KNOWN" : "NOT stock", line);
    klj_level_open(key, opened, v);
    SetLastError(err);
}

/* 0 = the scene is no level (frontend, a loading sequence, none), 1 = stock, 2 = not stock, 3 = not known (its
   archive was not seen or could not be read: blocks like 2 but never leaves the 'ran in this process' mark);
   why[200] says which and why */
static int klx_level_verdict(const char *scene, char *why)
{
    char key[64]; int i, v;
    why[0] = 0;
    if (!klh_level_key(scene, key, sizeof key - 4)) return 0;
    strcat(key, ".zip");
    if (strstr(key, "loader_sequence.zip")) return 0;         /* the loading screen's own scene, should the field ever name it */
    if (klx_patch_extra[0]) { snprintf(why, 200, "Patch01.zip holds '%s', which can override level members", klx_patch_extra); return 2; }
    EnterCriticalSection(&klx_cs);
    i = klx_find_arch(key);
    v = i < 0 ? 0 : klx_arch[i].verdict;
    if (v) snprintf(why, 200, "%s", klx_arch[i].why);
    LeaveCriticalSection(&klx_cs);
    if (!v) { snprintf(why, 200, "its archive %s was not seen being opened", key); return 3; }
    return v;
}

/* Is a write of this kind blocked right now? why[200] is filled either way. */
static int klx_blocked(int kind, char *why)
{
    char scene[160], w[200]; int v, any = 0, i;
    if (klx_always) {
#ifdef KLHOOK_TEST
        strcpy(why, "TEST build: nothing is written to Steam");
#else
        strcpy(why, "[Steam] Block=2");
#endif
        return 1;
    }
    if (!klh_exe_ok) {                                        /* no scene name on an unknown exe: go by the archives alone */
        EnterCriticalSection(&klx_cs);
        for (i = 0; i < klx_narch; i++) if (klx_arch[i].verdict >= 2 && !any) { any = 1; snprintf(why, 200, "unknown kl2.exe, and a level archive that is not stock was opened (%s)", klx_arch[i].key); }
        LeaveCriticalSection(&klx_cs);
        if (!any && klx_patch_extra[0]) { any = 1; snprintf(why, 200, "unknown kl2.exe, and Patch01.zip holds '%s'", klx_patch_extra); }
        if (!any) strcpy(why, "unknown kl2.exe; every level archive opened so far is stock");
        return any;
    }
    v = klh_scene(scene, sizeof scene) ? klx_level_verdict(scene, w) : 0;
    if (v == 2 && !klx_taint[0]) {
        EnterCriticalSection(&klx_cs); snprintf(klx_taint, sizeof klx_taint, "'%.80s' ran in this process and was not the stock level of its slot", scene); LeaveCriticalSection(&klx_cs);
    }
    if (v) { klx_last_verdict = v; snprintf(klx_last_why, sizeof klx_last_why, "%s", w); }
    if (kind == KLX_STATS && klx_taint[0]) { snprintf(why, 200, "%s: stats stay blocked until the game is restarted", klx_taint); return 1; }
    if (v >= 2 || (!v && klx_last_verdict >= 2)) { snprintf(why, 200, "%s", v ? w : klx_last_why); return 1; }
    strcpy(why, v ? "stock level" : klx_last_verdict ? "frontend, after a stock level" : "no level loaded yet in this process");
    return 0;
}

/* One write call: -> 1 = fail it. key = method + name (said once per level), text = the call as the log shows it. */
static int klx_gate(int kind, const char *key, const char *text)
{
    char why[200]; int b = klx_blocked(kind, why), i, dup = 0; DWORD h = klx_fnv((const BYTE *)key, (DWORD)strlen(key), 2166136261u) ^ (DWORD)b;
    InterlockedIncrement(b ? &klx_nblocked[kind] : &klx_npassed[kind]);
    if (!klx_log) return b;
    EnterCriticalSection(&klx_cs);
    for (i = 0; i < klx_nsaid; i++) if (klx_said[i] == h) dup = 1;
    if (!dup && klx_nsaid < 160) klx_said[klx_nsaid++] = h;
    LeaveCriticalSection(&klx_cs);
    if (!dup || klx_log >= 2) klog("steam: %s %s - %s", b ? "BLOCKED" : "passed on", text, why);
    return b;
}

/* ---------------------------------------------------------------- the proxy interface

   thiscall (this in ecx, callee pops) is written as __fastcall with an unused second register argument. */
#define KLX_REAL(n) ((*(void ***)klx_real)[n])
#define KLX_FWD(n) static __declspec(naked) void klx_fwd##n(void) { __asm mov ecx, dword ptr [klx_real] __asm mov eax, dword ptr [ecx] __asm jmp dword ptr [eax + 4 * n] }
KLX_FWD(0) KLX_FWD(1) KLX_FWD(2) KLX_FWD(6) KLX_FWD(9) KLX_FWD(11) KLX_FWD(12) KLX_FWD(14) KLX_FWD(15) KLX_FWD(16) KLX_FWD(17) KLX_FWD(18)
KLX_FWD(20) KLX_FWD(21) KLX_FWD(22) KLX_FWD(23) KLX_FWD(24) KLX_FWD(25) KLX_FWD(26) KLX_FWD(27) KLX_FWD(29)

static void klx_name(const char *p, char out[64]) { if (!klh_rdstr((DWORD_PTR)p, out, 64)) strcpy(out, "?"); }

static char __fastcall klx_SetStatF(void *self, void *edx, const char *name, float v)
{   /* slot 3, 8 bytes */
    char nm[64], key[80], text[160]; (void)self; (void)edx;
    klx_name(name, nm); snprintf(key, sizeof key, "SetStat(float) %s", nm); snprintf(text, sizeof text, "SetStat('%s', %g as float)", nm, v);
    return klx_gate(KLX_STATS, key, text) ? 0 : ((char (__fastcall *)(void *, void *, const char *, float))KLX_REAL(3))(klx_real, 0, name, v);
}
static char __fastcall klx_SetStatI(void *self, void *edx, const char *name, int v)
{   /* slot 4, 8 bytes: the one the game calls (0x555020) */
    char nm[64], key[80], text[160]; (void)self; (void)edx;
    klx_name(name, nm); snprintf(key, sizeof key, "SetStat %s", nm); snprintf(text, sizeof text, "SetStat('%s', %d)", nm, v);
    return klx_gate(KLX_STATS, key, text) ? 0 : ((char (__fastcall *)(void *, void *, const char *, int))KLX_REAL(4))(klx_real, 0, name, v);
}
static char __fastcall klx_UpdateAvgRateStat(void *self, void *edx, const char *name, float count, double seconds)
{   /* slot 5, 16 bytes */
    char nm[64], key[80], text[160]; (void)self; (void)edx;
    klx_name(name, nm); snprintf(key, sizeof key, "UpdateAvgRateStat %s", nm); snprintf(text, sizeof text, "UpdateAvgRateStat('%s', %g, %g)", nm, count, seconds);
    return klx_gate(KLX_STATS, key, text) ? 0 : ((char (__fastcall *)(void *, void *, const char *, float, double))KLX_REAL(5))(klx_real, 0, name, count, seconds);
}
static char __fastcall klx_SetAchievement(void *self, void *edx, const char *name)
{   /* slot 7, 4 bytes */
    char nm[64], key[80], text[160]; (void)self; (void)edx;
    klx_name(name, nm); snprintf(key, sizeof key, "SetAchievement %s", nm); snprintf(text, sizeof text, "SetAchievement('%s')", nm);
    return klx_gate(KLX_STATS, key, text) ? 0 : ((char (__fastcall *)(void *, void *, const char *))KLX_REAL(7))(klx_real, 0, name);
}
static char __fastcall klx_ClearAchievement(void *self, void *edx, const char *name)
{   /* slot 8, 4 bytes */
    char nm[64], key[80], text[160]; (void)self; (void)edx;
    klx_name(name, nm); snprintf(key, sizeof key, "ClearAchievement %s", nm); snprintf(text, sizeof text, "ClearAchievement('%s')", nm);
    return klx_gate(KLX_STATS, key, text) ? 0 : ((char (__fastcall *)(void *, void *, const char *))KLX_REAL(8))(klx_real, 0, name);
}
static char __fastcall klx_StoreStats(void *self, void *edx)
{   /* slot 10, 0 bytes */
    (void)self; (void)edx;
    return klx_gate(KLX_STATS, "StoreStats", "StoreStats()") ? 0 : ((char (__fastcall *)(void *, void *))KLX_REAL(10))(klx_real, 0);
}
static char __fastcall klx_IndicateAchievementProgress(void *self, void *edx, const char *name, DWORD cur, DWORD max)
{   /* slot 13, 12 bytes */
    char nm[64], key[80], text[160]; (void)self; (void)edx;
    klx_name(name, nm); snprintf(key, sizeof key, "IndicateAchievementProgress %s", nm); snprintf(text, sizeof text, "IndicateAchievementProgress('%s', %lu, %lu)", nm, cur, max);
    return klx_gate(KLX_STATS, key, text) ? 0 : ((char (__fastcall *)(void *, void *, const char *, DWORD, DWORD))KLX_REAL(13))(klx_real, 0, name, cur, max);
}
static char __fastcall klx_ResetAllStats(void *self, void *edx, DWORD achievements_too)
{   /* slot 19, 4 bytes */
    char text[64]; (void)self; (void)edx;
    snprintf(text, sizeof text, "ResetAllStats(%lu)", achievements_too & 0xff);
    return klx_gate(KLX_STATS, "ResetAllStats", text) ? 0 : ((char (__fastcall *)(void *, void *, DWORD))KLX_REAL(19))(klx_real, 0, achievements_too);
}
static unsigned __int64 __fastcall klx_UploadLeaderboardScore(void *self, void *edx, unsigned __int64 board, int method, int score, const int *details, int ndetails)
{   /* slot 28, 24 bytes; 0 = no call handle */
    char nm[64] = "?", key[96], text[200]; const char *p; (void)self; (void)edx;
    p = ((const char *(__fastcall *)(void *, void *, unsigned __int64))KLX_REAL(22))(klx_real, 0, board);      /* GetLeaderboardName: a read */
    if (p) klx_name(p, nm);
    snprintf(key, sizeof key, "UploadLeaderboardScore %s", nm);
    snprintf(text, sizeof text, "UploadLeaderboardScore(board '%s', %s, score %d)", nm, method == 1 ? "keep best" : method == 2 ? "force update" : "method ?", score);
    return klx_gate(KLX_BOARD, key, text) ? 0 :
        ((unsigned __int64 (__fastcall *)(void *, void *, unsigned __int64, int, int, const int *, int))KLX_REAL(28))(klx_real, 0, board, method, score, details, ndetails);
}

static const struct { int slot; void *fn; } klx_writes[9] = {
    { 3, (void *)klx_SetStatF }, { 4, (void *)klx_SetStatI }, { 5, (void *)klx_UpdateAvgRateStat }, { 7, (void *)klx_SetAchievement }, { 8, (void *)klx_ClearAchievement },
    { 10, (void *)klx_StoreStats }, { 13, (void *)klx_IndicateAchievementProgress }, { 19, (void *)klx_ResetAllStats }, { 28, (void *)klx_UploadLeaderboardScore } };

static void *__cdecl klx_SteamUserStats(void)
{
    static LONG told; void **r = (void **)klx_real_accessor(), **vt; MEMORY_BASIC_INFORMATION mbi; int i, bad = -1;
    if (!r) return 0;                                          /* Steam not running: the game gets what it would have got */
    if (r == klx_real) return &klx_proxy;
    if (!klh_rd((DWORD_PTR)r, &vt, sizeof vt)) bad = 0;
    for (i = 0; bad < 0 && i < KLX_NSLOT; i++) {               /* 30 entries that point into code of a loaded module */
        void *f = 0;
        if (!klh_rd((DWORD_PTR)(vt + i), &f, sizeof f) || !VirtualQuery(f, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT || mbi.Type != MEM_IMAGE ||
            !(mbi.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY))) bad = i;
    }
    if (bad >= 0) {
        if (!InterlockedExchange(&told, 2)) klog("steam: NOT GUARDED - the interface at %p has no code at slot %d of 30: not the 007 table; the game gets the real interface", (void *)r, bad);
        return r;
    }
    klx_real = r;
    if (!InterlockedExchange(&told, 1)) klog("steam: the game asked for ISteamUserStats: real interface %p, 30 slots checked, proxy handed out", (void *)r);
    return &klx_proxy;
}

/* ---------------------------------------------------------------- tick: level and session lines */

static void klx_tick(void)
{
    static char last[160]; static DWORD calls, laststate = 0xffffffff; static int nstate;
    char scene[160], why[200]; DWORD sm, st = 0, mode = 0; int v;
    if (!klx_on || !klh_exe_ok) return;
    if (klx_state_on && (sm = klh_rd32((DWORD_PTR)KLH_VA(KLX_SESSION))) != 0 && klh_rd(sm + 0x70, &st, 4) && st != laststate) {
        klh_rd(sm + 0x5c, &mode, 4);
        if (st == 0x28) {
            v = klx_blocked(KLX_BOARD, why);
            klog("session: state 0x%lx -> 0x28 (game mode %lu) = SESSION END: the game now uploads the session total and commits stats and achievements; Steam writes: %s - %s",
                 laststate, mode, v ? "BLOCKED" : "NOT blocked", why);
        } else if (laststate != 0xffffffff && nstate++ < 400) klog("session: state 0x%lx -> 0x%lx (game mode %lu)", laststate, st, mode);
        laststate = st;
    }
    if (calls++ & 7) return;
    if (!klh_scene(scene, sizeof scene) || !strcmp(scene, last)) return;
    snprintf(last, sizeof last, "%s", scene);
    EnterCriticalSection(&klx_cs); klx_nsaid = 0; LeaveCriticalSection(&klx_cs);      /* a new level: every call is said once again */
    v = klx_level_verdict(scene, why);
    if (!v) { klog("steam: scene '%s' is no level; so far %ld write(s) blocked, %ld passed on", scene, klx_nblocked[0] + klx_nblocked[1], klx_npassed[0] + klx_npassed[1]); return; }
    klx_blocked(KLX_STATS, why);                              /* sets the 'ran in this process' mark for a level that is not stock */
    v = klx_blocked(KLX_BOARD, why);
    klog("steam: level '%s': %s - leaderboard upload %s, stats and achievements %s", scene, why, v ? "BLOCKED" : "allowed",
         klx_always || klx_taint[0] ? "BLOCKED" : "allowed");
}

static void klx_exit_line(void)
{
    if (klx_on && (klx_nblocked[0] + klx_nblocked[1] + klx_npassed[0] + klx_npassed[1]))
        klog("steam: at exit: %ld leaderboard upload(s) and %ld stat / achievement write(s) blocked; %ld and %ld passed on", klx_nblocked[0], klx_nblocked[1], klx_npassed[0], klx_npassed[1]);
}

/* ---------------------------------------------------------------- set-up */

static int klx_has_007(void)
{   /* the loaded steam_api.dll asks steamclient for exactly this interface version */
    static const char want[] = "STEAMUSERSTATS_INTERFACE_VERSION007"; HMODULE m = GetModuleHandleA("steam_api.dll"); BYTE *b = (BYTE *)m, *copy; IMAGE_NT_HEADERS *nt; DWORD n, i; int found = 0, other = 0;
    if (!m) return 0;
    nt = (IMAGE_NT_HEADERS *)(b + ((IMAGE_DOS_HEADER *)b)->e_lfanew); n = nt->OptionalHeader.SizeOfImage;
    if (n < 0x1000 || n > (64u << 20) || !(copy = (BYTE *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, n + sizeof want))) return 0;
    for (i = 0; i + 0x1000 <= n; i += 0x1000) klh_rd((DWORD_PTR)(b + i), copy + i, 0x1000);      /* a page that cannot be read stays zero */
    for (i = 0; i < n; i++)
        if (copy[i] == 'S' && !memcmp(copy + i, want, sizeof want - 4)) { if (!memcmp(copy + i, want, sizeof want)) found = 1; else other = 1; }
    HeapFree(GetProcessHeap(), 0, copy);
    return found && !other;                                    /* exactly the 007 text and no other version of it */
}

static void klx_init(void)
{
    int i, n; char *p;
    InitializeCriticalSection(&klx_cs);
    for (p = dir, i = 0; (klx_game_low[i] = (char)(*p >= 'A' && *p <= 'Z' ? *p + 32 : *p)) != 0; p++, i++) ;
    klx_log = GetPrivateProfileIntA("Steam", "Log", 1, klh_ini);
    klx_state_on = GetPrivateProfileIntA("Steam", "State", 1, klh_ini);
#ifndef KLHOOK_TEST
    klx_always = GetPrivateProfileIntA("Steam", "Block", 1, klh_ini) >= 2;
#endif
    for (i = 0; i < KLX_NSLOT; i++) klx_vt[i] = 0;
    klx_vt[0] = (void *)klx_fwd0; klx_vt[1] = (void *)klx_fwd1; klx_vt[2] = (void *)klx_fwd2; klx_vt[6] = (void *)klx_fwd6; klx_vt[9] = (void *)klx_fwd9;
    klx_vt[11] = (void *)klx_fwd11; klx_vt[12] = (void *)klx_fwd12; klx_vt[14] = (void *)klx_fwd14; klx_vt[15] = (void *)klx_fwd15; klx_vt[16] = (void *)klx_fwd16;
    klx_vt[17] = (void *)klx_fwd17; klx_vt[18] = (void *)klx_fwd18; klx_vt[20] = (void *)klx_fwd20; klx_vt[21] = (void *)klx_fwd21; klx_vt[22] = (void *)klx_fwd22;
    klx_vt[23] = (void *)klx_fwd23; klx_vt[24] = (void *)klx_fwd24; klx_vt[25] = (void *)klx_fwd25; klx_vt[26] = (void *)klx_fwd26; klx_vt[27] = (void *)klx_fwd27;
    klx_vt[29] = (void *)klx_fwd29;
    for (i = 0; i < 9; i++) klx_vt[klx_writes[i].slot] = klx_writes[i].fn;
    for (i = 0; i < KLX_NSLOT; i++) if (!klx_vt[i]) { klog("steam: NOT GUARDED - proxy slot %d has no function (a build error)", i); return; }
    if (!klx_has_007()) {
        klog("steam: NOT GUARDED - the loaded steam_api.dll does not ask for STEAMUSERSTATS_INTERFACE_VERSION007 (or is not loaded): the proxy's table would not fit. "
             "Steam writes go out as in the stock game: do not end a session on a map that is not stock");
        return;
    }
    n = klh_iat("steam_api.dll", "SteamUserStats", (void *)klx_SteamUserStats, (void **)&klx_real_accessor);
    if (!n) { klog("steam: NOT GUARDED - the import steam_api.SteamUserStats was not found or not changed"); return; }
    klx_on = 1;
    klog("steam: import SteamUserStats wrapped (%d slot): ISteamUserStats 007 proxy, 30 slots, 9 writes gated; policy: %s", n,
#ifdef KLHOOK_TEST
         "TEST build - every leaderboard upload, stat and achievement write is BLOCKED, on every level"
#else
         klx_always ? "[Steam] Block=2 - every write is BLOCKED, on every level" :
         "writes are BLOCKED on a level that is not the stock level of its slot (klstock.h); stats stay blocked until restart once such a level ran"
#endif
         );
}

#ifdef KLHOOK_HARNESS
/* off-game: lift the TEST build's 'always' so that the policy itself can be exercised in both builds */
__declspec(dllexport) void klx_test_always(int on) { klx_always = on; }
__declspec(dllexport) int klx_test_blocked(void *mapped, int kind, char *why) { klh_delta = (LONG_PTR)((DWORD_PTR)mapped - KL2_BASE); klh_exe_ok = 1; return klx_blocked(kind, why); }
__declspec(dllexport) void klx_test_reset(void) { klx_taint[0] = 0; klx_last_verdict = 0; klx_narch = 0; klx_patch_extra[0] = 0; klx_nsaid = 0; }
#endif
#endif /* KLSTEAM_C */
