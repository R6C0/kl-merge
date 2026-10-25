/*
 * klslot.c - expansion content beside the stock game: Dead Men maps in their own folders, chosen from a menu
 * page of their own, taking over a Fragile Alliance slot only for the load they were picked for. Part of KLHook
 * (included by klhook.c, SHIP and TEST alike). Reasoning, evidence, plan: re\slot_redirect.md, re\menus.md 8,
 * re\antitamper.md 5.
 *
 * NOTHING ON DISK IS REPLACED AND NO CODE BYTE OF kl2.exe IS CHANGED. Everything this file needs lives in
 * <game>\KLExpansion\ and KLHook.ini; it writes five import slots of the exe and, for [Slots], heap data.
 * (Until 2026-10-09 [Slots] and MountFirst patched code: nine push operands and the session default are inside
 * hashed ranges - a real session would have ended in the integrity exit. Those patches are gone.)
 *
 * WHAT IT DOES (all off unless KLHook.ini has [Expansion] Enable=1)
 *  1. File redirect. Five import-table entries of the exe are pointed at wrappers: KERNEL32 CreateFileA,
 *     CreateFileW, GetFileAttributesA, FindFirstFileA and the C runtime's fopen. A wrapper only changes the
 *     PATH of a read-only open:
 *       [Redirect] F01=DM03   every file the game opens under  ...\Scenes\Locations\F01\  is opened from
 *                             <game>\KLExpansion\Maps\DM03\  instead (same file name), if it is there. The
 *                             engine still believes it loads "Locations/F01/F01_Main", so the archive in
 *                             Maps\DM03 is the one built for the F01 slot (members Scenes/Locations/F01/
 *                             F01_Main.*). LIVE (runs X2, X3, re\fa_round.md 7.2): with stock F01 in the slot
 *                             the Arcade entry 'Subway' loaded the bank from Maps\DM03, in a real session.
 *       Overlay               a file that exists as  <game>\KLExpansion\Overlay\<path relative to the game
 *                             folder>  replaces the game's. Overlay\Patch01.zip is how the menu is changed
 *                             without touching the stock Patch01.zip (the game mounts Patch01.zip first and
 *                             its members override every other archive's; it must be a COMPLETE patch archive:
 *                             the stock members plus ours - mkoverlay.py builds it).
 *  2. Menu pages: more than one expansion map without a tenth entry (the selector, two index tables and the
 *     level list are nine entries wide in code - re\menus.md 8.1). The overlay frontend.xml gets one more
 *     button on the Arcade page ("Dead Men maps") that opens a copy of the stock map page with other titles
 *     and pictures:
 *       [Redirect.2] F01=DM03   as [Redirect], but only while the page is 2
 *     WHICH PAGE: read off the menu's WINDOW STACK, nothing else (kls_menu_watch, every tick, reads only).
 *       - window system = [[[0xdd265c]+0x824]+4] (ZMercsMenuElements 0xbb7dc8 -> ZXMLGUISystem 0xbaf2fc), open
 *         windows = count at +0x328, pointers at +0x32c + 4*i, i = 1..count (0x6bef1c, 0x6bef5d; klauto has
 *         logged this stack in every menu run). A window's name: its vtable slot 3 is the thunk 0x410930 `mov
 *         eax,[ecx+8] ; mov edx,[eax+0xc] ; add ecx,8 ; jmp edx` into the ZGUIGroup that the window holds at +8
 *         (constructor 0x888aab), whose slot 3 is 0x962850 `mov eax,[ecx+4] ; ret`: the name is the char * at
 *         window+0xc. The hook compares the code bytes of both functions and then READS that pointer - it calls
 *         nothing (klauto calls the getter; a SHIP build must not run game code from a thread of its own).
 *       - a window 'HeistPlayMenu<N>' (N = 2..9) anywhere in the stack latches page N; the stock 'HeistPlayMenu'
 *         latches page 1. The latch is KEPT while there is no menu at all (a level load: the frontend's menu
 *         manager is destroyed), in a level (its own menu has no map page), and through the session.
 *       - it is DROPPED (page 0) when the FRONTEND shows a window stack without a map page for 1 s - the Arcade
 *         page again (after an Arcade session the game itself opens 'HeistModeMenu', 0x7b0885), the main menu,
 *         the online pages - and in the last 10 s neither a start was seen pending (byte [0x156b73a]: StartGame
 *         accepted, 0x502cb6; cleared one frame later by 0x7e01be when the load is requested) nor the session
 *         state ([0x168e598]+0x70) changed (run MP1: 0x0 -> 0x12 half a second after StartGame, 15 ms before
 *         the archive open). So a drop cannot fall between StartGame and the load, however slowly the frontend
 *         goes away; the price is that the page lives up to 10 s too long after such an event, which only
 *         matters if a level load could start in that time without a map page having been opened.
 *     WHY NOT THE OPTION 'Dummy' (the first design; run MP1, 2026-10-09): the buttons do store it - the log said
 *     'menu page option is 2' with HeistPlayMenu2 open - but the options object ZMercsOptionsInterface (vtable
 *     0xbb7dec, [0x154d5f4], 'Dummy' at +0xd4) does not live through the start of a level: it is created lazily
 *     by ZMercsMenuElements slot 5 (0x5b20f0, constructor 0x800f90 zeroes +0xd4), DELETED in that manager's
 *     destructor (0x673340: `mov ecx,[0x154d5f4] ; call [vtbl]`, then the global = 0), and the global is zeroed
 *     again in the manager's constructor (0x617701). The game data object [0xdd265c] (0x4d60 bytes, factory
 *     0x4837a0) builds two managers (0x553d06, 0x553d38) - a new scene has new ones. So at the archive open the
 *     option read 0 and the slot's own level was loaded. StartGame itself never reads 'Dummy': 0x502b40 takes the
 *     selector's value ([vtbl+0x90]: the option Heist_SelectedLevel, a .data byte that survives), 0x746570 turns
 *     it into the slot, and 0x7e01a0 gives the session manager the slot's scene name. The buttons still set
 *     'Dummy' (harmless, and the planned heister row needs it non-zero); the hook logs it at Log=2 only.
 *     ASSUMPTION (read, not watched): that the game data object is rebuilt for every scene - what was SEEN is
 *     only that the option read 2 in the page and 0 at the archive open 5 s later.
 *     The page is TAKEN per slot when the slot's own archive (<slot>_Main.zip) is opened - the first level
 *     file of every load (X2: CreateFileA F01_Main.zip, then the _LS files, Loader_Sequence, and 9 s later the
 *     .WHD / .WAV) - so one load never mixes two tables, and the streamed sound that is opened seconds later
 *     comes from the same map. A slot with no line for the page falls back to [Redirect], then to the stock
 *     level. Entry k of a page loads slot {F01,F02,F03,F04,F06,F07,F05,F08,F09}[k] (the engine's own menu
 *     order, 0x746570), so nine maps a page. A direct boot (-o DefaultScene=) has no menu: page 0, i.e.
 *     [Redirect]; [Expansion] Page=N forces a page for such a test.
 *     RUN LIVE: the page opens and the option is set (MP1). THE LATCH, runs MP2b and MP2c (2026-10-09 17:07 /
 *     17:10, TEST build, [Redirect.2] F01=DM03, logs <work>\build\klhook\live\MP2c.log): 'menu page 2 latched:
 *     window HeistPlayMenu2 is open' in the frame the page opened, StartGame 5 s later, 'session: state 0x0 ->
 *     0x12', and 12 ms after that 'slot F01: menu page 2 from now on -> DM03' with the archive, the _LS files
 *     and (10 s later) the .WHD / .WAV all from Maps\DM03; 'Dummy' read 2 in the page and 0 right after the
 *     archive open, as MP1 had it. No 'dropped' line came between StartGame and the archive. MP2c went on into
 *     the round and ended PASS.
 *     NOT RUN LIVE: a slot other than F01 from a page (the five-map page of tools\kl_expansion.py: F02 F03 F04
 *     F06 - scripts <work>\research\agent_scripts\w-tab\TAB_*.ini, re\expansion.md 10); the stock page after
 *     an expansion page in one process (page 1 must then be latched: check MP3); the drop after a session.
 *     KNOWN LIMITS: the engine treats a redirected map as the stock map of its slot - title in the lobby,
 *     briefing, and the LEADERBOARD (0x80c9f0(current slot)): an Arcade score on an expansion map is reported
 *     to the stock map's Steam board - klsteam.c stops that (a proxy ISteamUserStats behind the import slot
 *     0xb107c8 fails the upload, the stats and the achievements on every level that is not the stock level of
 *     its slot; the two CreateFile wrappers below tell it which archive was opened, klh_level_open, and are
 *     therefore installed even when [Expansion] is off). Online play needs the same ini and
 *     folders on every peer and the page is not replicated: stage 4.
 *  3. [Slots] F09=Locations/F0M03/F0M03_Main  - name mode (re\fa_slots.md 5): the engine itself loads another
 *     scene name, so a level may live under a folder of its own name (supplied through the Overlay:
 *     Overlay\Scenes\Locations\F0M03\F0M03_Main.zip, built under that name). DATA WRITES, from klhook.c's tick:
 *     the nine names are 0x40 bytes each on the heap at [0x168f750] + 0x16 + idx * 0x40
 *     (ZDownloadableContentManagerSteam, vtable 0xbd5494; fetched fresh by its slot 15 every time a level is
 *     started); a renamed slot's text is written whenever it differs, its 'available' byte [+4+idx] is kept 1
 *     (never for a slot that keeps its stock name: that would unlock paid content), and when F01 is renamed the
 *     session manager's preset map name [0x168e598]+8 (the same literal, copied by the constructor 0x6997f0)
 *     is rewritten while it still holds the stock text. LIVE so far: the write itself (run X2 wrote the F01
 *     entry back with its own bytes in a session). NOT RUN: a changed name.
 *  4. [Expansion] MountFirst=<file> : kept as a key for older inis; it no longer patches the mount call
 *     (kl2 0x7f5610). The named file (relative to the game folder) is now simply what an open of Patch01.zip
 *     is answered with - the same as putting it at Overlay\Patch01.zip, so it has to be a complete archive.
 *
 * KLHook.ini
 *   [Expansion]
 *   Enable=1
 *   Root=KLExpansion      folder next to kl2.exe
 *   Overlay=1             0 = ignore <Root>\Overlay
 *   Fallback=1            a file missing from Maps\<map> : 1 = the stock file is used (logged),
 *                         0 = the open fails as if the file did not exist
 *   Log=1                 0 nothing, 1 every redirect once, 2 also every other open once and the slot table
 *   Page=-1               -1 = the page comes from the menu (the window stack); 0..9 = forced (direct-boot tests)
 *   MountFirst=           see 4.
 *   [Redirect]            <folder under Scenes\Locations> = <folder under Root\Maps>; every page
 *   F01=DM03
 *   [Redirect.2]          the same for menu page 2 (.2 to .9); at most 64 lines in all, 16 different slots
 *   F01=DM01
 *   F02=DM02
 *   [Page.2]              read by mkoverlay.py only (titles and pictures of the page); the hook logs Title
 *   Title=Dead Men maps
 *   F01=Withdrawal
 *   [Slots]               F01..F09 = scene name without extension, at most 63 characters
 *   ;F09=Locations/F0M03/F0M03_Main
 *
 * EVIDENCE (kl2.exe sha1 9d99e01d..., TimeDateStamp 0x4c80f728, base 0x400000; pefile + capstone, 2026-10-09)
 *  - Imports: KERNEL32 OriginalFirstThunk 0x8cce54 / FirstThunk 0x71005c, MSVCR90 0x8cd080 / 0x710288, not
 *    bound, so the names are readable in memory. CreateFileA = [0xb10270]: 17 references in .text, every one
 *    "call [0xb10270]" or "mov esi,[0xb10270]". fopen = [0xb10430] 8 calls, GetFileAttributesA 1, FindFirstFileA
 *    3, CreateFileW 104 (not classified). All five slots: `ceg_ranges.py` 0 checks; wrapped in a real session
 *    in runs X1 - X3.
 *  - Archive mount: the scene loader 0x7f4f90 unmounts everything (0x7f55fe), mounts "Patch01.zip" (0x7f5610,
 *    name relative to the current directory, opened through CreateFileA), then the scene's own archive
 *    (0x7f5827). First mounted archive wins a name (FS slot 30 0x468bb0; read, never observed).
 *  - Session default: 0x699819 "push 0x40; lea eax,[esi+8]; push 0xb75044 'Locations/F01/F01_Main'; push eax;
 *    call 0x4f99e0" in the ZSessionManager constructor: a bounded copy into session+8.
 *  - DINPUT8.dll is a static import of kl2.exe: DllMain runs before the exe's entry point. The import table is
 *    filled by then (the code checks: an entry that does not point into a loaded image is left alone).
 *  TESTED OFF-GAME (scratch harness; sources not in the repo, results in the agent's report): the five
 *  wrappers on a made-up game folder, page latching, the MountFirst alias, the [Slots] tick against made-up
 *  objects reached through a mapped copy of kl2.exe, and that the copy's image is byte-identical afterwards;
 *  mode 'menu': made-up windows (the real vtables and getter code of the mapped copy) through the sequence of
 *  run MP1 - page open, StartGame, stack gone, level, frontend again - and the archive opened at each step.
 */
#ifndef KLSLOT_C
#define KLSLOT_C

#define KLS_DLCMGR    0x0168f750              /* ZDownloadableContentManagerSteam * (0 until created) */
#define KLS_DLCMGR_VT 0x00bd5494
#define KLS_OPTIONS   0x0154d5f4              /* ZMercsOptionsInterface * (0 until the menu system exists) */
#define KLS_OPTIONS_VT 0x00bb7dec
#define KLS_MENUMGR_VT 0x00bb7dc8             /* ZMercsMenuElements: [[0xdd265c]+0x824] */
#define KLS_WSYS_VT   0x00baf2fc              /* ZXMLGUISystem: [manager+4]; open windows: count +0x328, pointers +0x32c + 4*i (i from 1) */
#define KLS_STARTPEND 0x0156b73a              /* byte: StartGame was accepted (0x502cb6); 0 again when the load is requested (0x7e01be) */
#define KLS_MAPPAGE   "HeistPlayMenu"         /* the stock map page; mkoverlay.py's copies are HeistPlayMenu2 .. HeistPlayMenu9 */
#define KLS_SESSION   0x0168e598              /* the session manager; +8 = map name, 0x40 bytes */
#define KLS_FA        9
#define KLS_NAME      0x40
#define KLS_SLOTS     16
#define KLS_RULES     64
#define KLS_PAGES     10

static int kls_on, kls_log = 1, kls_fallback = 1, kls_overlay_on, kls_nrules, kls_nslots, kls_page_force = -1;
static int kls_npaged;                        /* redirect rules that belong to a menu page: without one the window stack is not watched */
static volatile LONG kls_menu_page;           /* the page latched from the window stack: 0 none, 1 the stock map page, 2..9 an expansion page */
static int kls_drop_ms = 1000, kls_quiet_ms = 10000;      /* see kls_menu_watch */
static char kls_game_low[MAX_PATH], kls_root[MAX_PATH], kls_root_low[MAX_PATH], kls_overlay[MAX_PATH];
static char kls_patch_low[MAX_PATH], kls_patch_alias[MAX_PATH];      /* "<game>\patch01.zip" and what MountFirst answers it with */
static int kls_game_len, kls_root_len;
static CRITICAL_SECTION kls_cs;
static struct {
    char name[32];                            /* "F01" as written in the ini */
    char key[96]; int keylen;                 /* "\scenes\locations\f01\", lower case */
    char zip[48];                             /* "f01_main.zip": the open that latches the page */
    volatile LONG page;                       /* page latched at the last open of that archive, -1 = none yet */
} kls_slot[KLS_SLOTS];
static struct {
    int slot, page;                           /* page 0 = [Redirect] (every page) */
    char to[MAX_PATH]; int tolen;             /* "<game>\KLExpansion\Maps\DM03\" */
    char map[48];
    LONG hits, misses;
} kls_rule[KLS_RULES];

/* ---------------------------------------------------------------- log: each distinct line once */

static DWORD kls_seen[1024]; static int kls_nseen;

static void kls_note(const char *api, const char *what, const char *from, const char *to)
{
    DWORD h = 2166136261u; const char *p; int i, dup = 0;
    for (p = what; *p; p++) h = (h ^ (BYTE)*p) * 16777619u;
    for (p = from; *p; p++) h = (h ^ (BYTE)(*p >= 'A' && *p <= 'Z' ? *p + 32 : *p)) * 16777619u;
    for (p = to ? to : ""; *p; p++) h = (h ^ (BYTE)(*p >= 'A' && *p <= 'Z' ? *p + 32 : *p)) * 16777619u;
    EnterCriticalSection(&kls_cs);
    for (i = 0; i < kls_nseen; i++) if (kls_seen[i] == h) { dup = 1; break; }
    if (!dup && kls_nseen < 1024) kls_seen[kls_nseen++] = h; else dup = 1;      /* table full: stay quiet */
    LeaveCriticalSection(&kls_cs);
    if (dup) return;
    if (to) klog("expansion: %s %s: %s -> %s", api, what, from, to);
    else klog("expansion: %s %s: %s", api, what, from);
}

/* ---------------------------------------------------------------- the menu page */

static int kls_option_now(void)
{   /* the spare option 'Dummy' of the menu's option object; 0 while there is none. Information only (Log=2): the
       object is deleted when a level load starts, so it cannot carry the page into the load (top comment) */
    DWORD obj, v;
    if (!klh_exe_ok) return 0;
    obj = klh_rd32((DWORD_PTR)KLH_VA(KLS_OPTIONS));
    if (!obj || klh_rd32(obj) != KLS_OPTIONS_VT || !klh_rd(obj + 0xd4, &v, 4)) return 0;
    return v < KLS_PAGES ? (int)v : 0;
}

/* ONLINE MAP SET (2026-10-25, mapset_1025a; owner: the Dead Men maps selectable in Private Match / System Link too). WHY: online the Arcade
 * page is not on screen, so the latch is 0 (or dropped after 1 s) and every slot loads its stock / [Redirect] map. HOW: while kl_online() says
 * this machine is in a network session, kls_page_now() answers
 *   [Expansion] OnlineSet=N (2 or 3; 0 = off, the default)   that page, whatever the menu latch says;
 *   [Expansion] KeepPageOnline=1 (default 0)                 else the last expansion page seen in the OFFLINE menu (kls_keep), if the latch is 0.
 * [Expansion] KeepClear=1 (default 1) forgets kls_keep when a window whose name contains 'MainMenu' is topmost in the frontend (GUESS: that
 * name; the stack is logged at Log>=2 and at every drop). Offline nothing changes. DATA ONLY: no code byte is written.
 * LIMITS: Quick Match / public lobbies cannot be told apart by this machine (the lobby type is only seen when klmm.c's proxy is installed,
 * [Net] PrivateLobby/BuildKey): the key is therefore OFF by default, and a Quick Match with it on loads a Dead Men map against a stock one.
 * The host's set is NOT sent to joiners (stage 4, re\private_match_mapsync.md): every peer needs the same ini. A line says so at every load. */
static int kls_online_set, kls_keep_online, kls_keep_clear = 1, kls_keep;
static char kls_stack_txt[240];                      /* the last window stack read, for the logs */

static int kls_online_cached(void)
{   /* kl_online() reads memory three times: not more than every 250 ms (kls_page_now is called per file open and per LOC lookup) */
    static DWORD at; static int v;
    DWORD now = GetTickCount();
    if (!at || now - at > 250) { v = kl_online(); at = now ? now : 1; }
    return v;
}

static int kls_page_now(void)
{   /* the page a load that starts now belongs to */
    if (kls_page_force >= 0) return kls_page_force;
    if ((kls_online_set || kls_keep_online) && kls_online_cached()) {
        if (kls_online_set) return kls_online_set;
        if (!kls_menu_page && kls_keep) return kls_keep;
    }
    return (int)kls_menu_page;
}

static int kls_in_image(DWORD va) { return va >= KL2_BASE && va < KL2_BASE + KL2_IMAGESIZE - 16; }

static int kls_win_name(DWORD win, char *out, int cap)
{   /* the name of a menu window WITHOUT calling into the game: both getters are compared byte for byte, then the
       pointer they would return is read. -> length, 0 = not a window this build knows */
    static const BYTE thunk[11] = { 0x8b, 0x41, 0x08, 0x8b, 0x50, 0x0c, 0x83, 0xc1, 0x08, 0xff, 0xe2 };     /* 0x410930 */
    static const BYTE getter[4] = { 0x8b, 0x41, 0x04, 0xc3 };                                             /* 0x962850 */
    BYTE c[11]; DWORD vt, fn;
    out[0] = 0;
    if (!kls_in_image(vt = klh_rd32(win)) || !kls_in_image(fn = klh_rd32((DWORD_PTR)KLH_VA(vt + 0xc))) ||
        !klh_rd((DWORD_PTR)KLH_VA(fn), c, sizeof thunk) || memcmp(c, thunk, sizeof thunk)) return 0;
    if (!kls_in_image(vt = klh_rd32(win + 8)) || !kls_in_image(fn = klh_rd32((DWORD_PTR)KLH_VA(vt + 0xc))) ||
        !klh_rd((DWORD_PTR)KLH_VA(fn), c, sizeof getter) || memcmp(c, getter, sizeof getter)) return 0;
    return klh_rdstr(klh_rd32(win + 0xc), out, cap);
}

static int kls_map_page_of(const char *name)
{   /* 'HeistPlayMenu' -> 1, 'HeistPlayMenu<N>' -> N (2..9), anything else -> 0 */
    size_t l = sizeof KLS_MAPPAGE - 1;
    if (strncmp(name, KLS_MAPPAGE, l)) return 0;
    if (!name[l]) return 1;
    return name[l] >= '2' && name[l] <= '9' && !name[l + 1] ? name[l] - '0' : 0;
}

/* ---------------------------------------------------------------- path mapping */

static void kls_lower(char *d, const char *s) { for (; (*d = (char)(*s >= 'A' && *s <= 'Z' ? *s + 32 : *s)) != 0; d++, s++) ; }

static int kls_isfile(const char *p)
{   /* GetFileAttributesA of THIS dll's import table, i.e. not the wrapped one */
    DWORD a = GetFileAttributesA(p);
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

static int kls_find_rule(int slot, int page)
{
    int i;
    for (i = 0; i < kls_nrules; i++) if (kls_rule[i].slot == slot && kls_rule[i].page == page) return i;
    return -1;
}

/* RANDOM ONLINE MAP (2026-10-25, onlrand_1025a; owner: 'an option for it to play randomised maps too'). [Expansion] OnlineSet=9.
 * The host picks the SLOT (stock map) in the lobby and the game syncs that; this picks WHICH map of that slot loads, from every page that has
 * a rule for the slot, plus the stock map as one choice. Every peer must pick the same one with NO message between them, so the choice is a pure
 * function of (lobby id, slot number, candidate list):
 *   lobby id = the 8 bytes at [[[0x168e598]+0x17c]+0x35e] when that service is the Steam one (vtable 0xbd597c) and its 'session exists' byte
 *   [+0x35c] is set. The host's create task writes it, a joiner's JoinSession copies it from the search result (re\netcode_fa.md 8: SETTLED,
 *   klnet.c logs it as 'net: lobby ...'); Steam gives host and joiner the same id (CERTAIN for Steam lobbies; that the field is already
 *   filled when the first slot archive is opened is a GUESS: the lobby exists long before the start). If it cannot be read (System Link may
 *   use another service class: GUESS, not looked at) the seed is 0 -> a FIXED map per slot, identical on every peer too.
 * Same lobby + same slot = same map every round (no round counter is shared); a new lobby = a new draw. The candidate list must be identical on
 * all peers (same ini, same map folders), otherwise they diverge - exactly as for OnlineSet=2. An old DLL reads OnlineSet=9 as a page without
 * rules and falls back to the stock [Redirect] maps. DATA reads only. */
#define KLS_RANDOM     9
#define KLS_SVC_VT     0x00bd597c
static char kls_rnd_txt[200];                        /* the last draw, for the LOAD line */

static int kls_rand_pick(int s)
{   /* -> the page (0 = stock) chosen for slot index s */
    int cand[KLS_PAGES], n = 0, p, k, num = atoi(kls_slot[s].name + 1), src = 0, len = 0;
    DWORD sm, svc, lob[2] = { 0, 0 }; BYTE ex = 0; unsigned __int64 x;
    cand[n++] = 0;
    for (p = 2; p < KLS_RANDOM; p++) if (kls_find_rule(s, p) >= 0) cand[n++] = p;
    if (klh_exe_ok && (sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION))) != 0 && (svc = klh_rd32(sm + 0x17c)) != 0 &&
        klh_rd32(svc) == KLS_SVC_VT && klh_rd(svc + 0x35c, &ex, 1) && ex && klh_rd(svc + 0x35e, lob, 8) && (lob[0] || lob[1])) src = 1;
    else lob[0] = lob[1] = 0;
    x = ((unsigned __int64)lob[1] << 32 | lob[0]) ^ ((unsigned __int64)(num + 1) * 0x9E3779B97F4A7C15ULL);
    x ^= x >> 30; x *= 0xBF58476D1CE4E5B9ULL; x ^= x >> 27; x *= 0x94D049BB133111EBULL; x ^= x >> 31;
    k = (int)(x % (unsigned)n);
    len = snprintf(kls_rnd_txt, sizeof kls_rnd_txt, "random: seed lobby %08lx%08lx (%s) slot %d, %d choices [stock", (unsigned long)lob[1], (unsigned long)lob[0],
                   src ? "Steam lobby id" : "NOT readable: fixed pick", num, n);
    for (p = 1; p < n && len < (int)sizeof kls_rnd_txt - 40; p++) len += snprintf(kls_rnd_txt + len, sizeof kls_rnd_txt - len, " p%d=%s", cand[p], kls_rule[kls_find_rule(s, cand[p])].map);
    snprintf(kls_rnd_txt + len, sizeof kls_rnd_txt - len, "] -> choice %d (page %d)", k, cand[k]);
    return cand[k];
}

/* -> 1 and the new path in out[MAX_PATH] when the open must go somewhere else, 0 when it stays.
   Keeps GetLastError() as it found it when it returns 0. */
static int kls_map(const char *in, char *out, const char *api)
{
    char full[MAX_PATH], low[MAX_PATH], *hit = 0; DWORD n, err; int s, r, wild;
    if (!kls_on || !in || !in[0] || (in[0] == '\\' && in[1] == '\\')) return 0;   /* devices, pipes, UNC */
    err = GetLastError();
    n = GetFullPathNameA(in, MAX_PATH, full, 0);          /* absolute, '/' -> '\', "." and ".." resolved */
    if (!n || n >= MAX_PATH) { SetLastError(err); return 0; }
    kls_lower(low, full);
    if (!strncmp(low, kls_root_low, kls_root_len) && (low[kls_root_len] == '\\' || !low[kls_root_len])) { SetLastError(err); return 0; }   /* already ours */
    if (kls_patch_alias[0] && !strcmp(low, kls_patch_low)) {
        strcpy(out, kls_patch_alias);
        if (kls_log) kls_note(api, "MountFirst", full, out);
        SetLastError(err); return 1;
    }
    wild = strpbrk(full, "*?") != 0;
    for (s = 0; s < kls_nslots; s++) if ((hit = strstr(low, kls_slot[s].key)) != 0) break;
    if (s < kls_nslots) {
        const char *rest = full + (hit - low) + kls_slot[s].keylen; int page;
        if (!_stricmp(rest, kls_slot[s].zip)) {           /* the level's archive: a load of this slot begins (or the game probes for it) */
            page = kls_page_now();
            kls_rnd_txt[0] = 0;
            if (page == KLS_RANDOM) page = kls_rand_pick(s);      /* OnlineSet=9 */
            { static LONG nd; if (InterlockedIncrement(&nd) <= 96) {      /* DIAGNOSTIC: which page decided this load, and why */
                int on = kl_online(); r = kls_find_rule(s, page); if (r < 0 && page) r = kls_find_rule(s, 0);
                klog("expansion: LOAD %s: latch=%ld force=%d online=%d OnlineSet=%d keep=%d -> page %d, rule %s; stack [%s]%s%s%s", kls_slot[s].name, (long)kls_menu_page, kls_page_force,
                     on, kls_online_set, kls_keep, page, r < 0 ? "none (stock level)" : kls_rule[r].map, kls_stack_txt[0] ? kls_stack_txt : "not read yet",
                     kls_rnd_txt[0] ? "; " : "", kls_rnd_txt,
                     on && page ? " - WARNING: online, every peer needs the SAME map set (the host's choice is not sent; see re/private_match_mapsync.md)" : ""); } }
            if (!kl_online() && (r = kpm_override(kls_slot[s].name)) >= 0) page = r;      /* klpm.c: the Arcade playlist names the page of the map it chose for this slot */
            if (InterlockedExchange(&kls_slot[s].page, page) != page) {
                r = kls_find_rule(s, page); if (r < 0) r = kls_find_rule(s, 0);
                klog("expansion: slot %s: menu page %d from now on -> %s", kls_slot[s].name, page, r < 0 ? "the stock level" : kls_rule[r].map);
            }
        }
        page = kls_slot[s].page < 0 ? kls_page_now() : kls_slot[s].page;
        r = kls_find_rule(s, page); if (r < 0 && page) r = kls_find_rule(s, 0);
        if (r >= 0 && kls_rule[r].tolen + strlen(rest) < MAX_PATH) {
            memcpy(out, kls_rule[r].to, kls_rule[r].tolen); strcpy(out + kls_rule[r].tolen, rest);
            if (wild || kls_isfile(out)) {                /* a search pattern goes to the map folder as a whole */
                InterlockedIncrement(&kls_rule[r].hits);
                if (kls_log) kls_note(api, "redirect", full, out);
                SetLastError(err); return 1;
            }
            InterlockedIncrement(&kls_rule[r].misses);
            if (!kls_fallback) { if (kls_log) kls_note(api, "redirect (NOT in the map folder, Fallback=0: the open will fail)", full, out); SetLastError(err); return 1; }
            if (kls_log) kls_note(api, "NOT in the map folder, stock file used", full, out);
        }
    }
    if (kls_overlay_on && !wild && !strncmp(low, kls_game_low, kls_game_len) && low[kls_game_len] == '\\' &&
        strlen(kls_overlay) + strlen(full + kls_game_len) < MAX_PATH) {
        strcpy(out, kls_overlay); strcat(out, full + kls_game_len);
        if (kls_isfile(out)) { if (kls_log) kls_note(api, "overlay", full, out); SetLastError(err); return 1; }
    }
    if (kls_log >= 2) kls_note(api, "open", full, 0);
    SetLastError(err);
    return 0;
}

/* ---------------------------------------------------------------- the five wrappers */

static HANDLE (WINAPI *kls_real_CreateFileA)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static HANDLE (WINAPI *kls_real_CreateFileW)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static DWORD (WINAPI *kls_real_GetFileAttributesA)(LPCSTR);
static HANDLE (WINAPI *kls_real_FindFirstFileA)(LPCSTR, LPWIN32_FIND_DATAA);
static void *(__cdecl *kls_real_fopen)(const char *, const char *);

#define KLS_READONLY(acc, disp) ((disp) == OPEN_EXISTING && !((acc) & (GENERIC_WRITE | GENERIC_ALL | FILE_WRITE_DATA | FILE_APPEND_DATA)))

/* 2026-10-23 (debug/notes/2026-10-23-startup-stall.md): Valve CEG's per-frame self-check (0xb0f4a0, first instruction of the
   main-loop step 0x87a930) opens the game's OWN exe with access 0x81 and flags -1, which includes FILE_FLAG_DELETE_ON_CLOSE.
   NTFS refuses that on a running image, which is what CEG expects. Such an open passes KLS_READONLY, so the overlay would be
   consulted: if a build ever put KLExpansion\Overlay\KL2.exe there, the probe would open THAT file, Windows would delete it
   on close, and the tamper counter [0xdd2608] would start counting. An open with DELETE intent, or of the exe itself, is never
   redirected. (Kept in the wrapper, not in kls_map: the flags are only known here.) */
#define KLS_NO_REDIRECT(acc, flags) (((flags) & FILE_FLAG_DELETE_ON_CLOSE) || ((acc) & DELETE))

static int kls_is_own_exe(const char *name)
{   /* the game's exe by its path tail (the probe passes the full path GetModuleFileNameA gave) */
    size_t n = name ? strlen(name) : 0;
    return n >= 7 && !_stricmp(name + n - 7, "kl2.exe") && (n == 7 || name[n - 8] == '\\' || name[n - 8] == '/');
}

static HANDLE WINAPI kls_CreateFileA(LPCSTR name, DWORD acc, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disp, DWORD flags, HANDLE tmpl)
{
    char to[MAX_PATH]; LPCSTR asked = name;
    if (KLS_READONLY(acc, disp) && !KLS_NO_REDIRECT(acc, flags) && !kls_is_own_exe(name)) {
        if (kls_map(name, to, "CreateFileA")) name = to;
        klh_level_open(asked, name);                  /* klsteam.c: which level archive is this, and is it the stock one */
    }
    return kls_real_CreateFileA(name, acc, share, sa, disp, flags, tmpl);
}

static HANDLE WINAPI kls_CreateFileW(LPCWSTR name, DWORD acc, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disp, DWORD flags, HANDLE tmpl)
{
    char a[MAX_PATH], to[MAX_PATH]; WCHAR w[MAX_PATH]; BOOL lossy = FALSE; DWORD err = GetLastError();
    if (name && KLS_READONLY(acc, disp) && !KLS_NO_REDIRECT(acc, flags) && WideCharToMultiByte(CP_ACP, 0, name, -1, a, MAX_PATH, 0, &lossy) && !lossy && !kls_is_own_exe(a)) {
        if (kls_map(a, to, "CreateFileW") && MultiByteToWideChar(CP_ACP, 0, to, -1, w, MAX_PATH)) { name = w; klh_level_open(a, to); }
        else klh_level_open(a, a);
    }
    SetLastError(err);
    return kls_real_CreateFileW(name, acc, share, sa, disp, flags, tmpl);
}

static DWORD WINAPI kls_GetFileAttributesA(LPCSTR name)
{
    char to[MAX_PATH];
    if (kls_map(name, to, "GetFileAttributesA")) name = to;
    return kls_real_GetFileAttributesA(name);
}

static HANDLE WINAPI kls_FindFirstFileA(LPCSTR name, LPWIN32_FIND_DATAA fd)
{
    char to[MAX_PATH];
    if (kls_map(name, to, "FindFirstFileA")) name = to;
    return kls_real_FindFirstFileA(name, fd);
}

static void *__cdecl kls_fopen(const char *name, const char *mode)
{   /* the FILE belongs to the game's C runtime; it is only passed through */
    char to[MAX_PATH];
    if (mode && mode[0] == 'r' && !strchr(mode, '+') && kls_map(name, to, "fopen")) name = to;
    return kls_real_fopen(name, mode);
}

/* ---------------------------------------------------------------- the menu page, from the window stack

   Every tick: which map page does the menu show? Reads only; safe from the fallback thread (a half-written stack
   gives a name that matches nothing, and a drop needs the same reading for a whole second). */
static void kls_menu_watch(void)
{
    static DWORD sig0, since, state0 = 0xffffffff, stateat; static int found0, have0, stateseen; static LONG told;
#define stack0 kls_stack_txt
    DWORD gd, mgr, w, n, win[24], sig, sm, st = 0, now = GetTickCount(), i; int found = 0, len = 0; char nm[64], scene[160], key[64]; BYTE pend = 0;
    if (kls_page_force >= 0 || !kls_npaged || !klh_exe_ok) return;
    if ((sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION))) != 0 && klh_rd(sm + 0x70, &st, 4) && st != state0) {
        if (state0 != 0xffffffff) { stateat = now; stateseen = 1; }
        state0 = st;
    }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != KLS_MENUMGR_VT || !(w = klh_rd32(mgr + 4))) { have0 = 0; return; }   /* no menu: a load. The latch stays */
    if (klh_rd32(w) != KLS_WSYS_VT) {
        if (!InterlockedExchange(&told, 1)) klog("expansion: the menu's window system at %08lx has vtable %08lx, not %08lx: the menu page cannot be read - every load uses [Redirect] only", w, klh_rd32(w), (DWORD)KLS_WSYS_VT);
        have0 = 0; return;
    }
    n = klh_rd32(w + 0x328);
    if (!n || n > 24 || !klh_rd(w + 0x330, win, 4 * n)) { have0 = 0; return; }      /* no window open (between two scenes): the latch stays */
    for (sig = n, i = 0; i < n; i++) sig = sig * 31 + win[i];
    if (!have0 || sig != sig0) {                      /* the stack changed: read the names once */
        stack0[0] = 0;
        for (i = 0; i < n; i++) {
            int p;
            kls_win_name(win[i], nm, sizeof nm);
            if ((p = kls_map_page_of(nm)) != 0) found = p;      /* the topmost map page counts */
            if (len < (int)sizeof stack0 - 70) len += snprintf(stack0 + len, sizeof stack0 - len, "%s%s", i ? " > " : "", nm[0] ? nm : "?");
        }
        have0 = 1; sig0 = sig; found0 = found; since = now;
        if (kls_keep_clear && kls_keep && !found && strstr(stack0, "MainMenu")) { klog("expansion: kept page %d forgotten: the frontend shows [%s]", kls_keep, stack0); kls_keep = 0; }
        if (kls_log >= 2) klog("expansion: menu windows [%s]%s", stack0, found ? "" : " - no map page");
    }
    /* StartGame: the byte is set for one frame only (0x502cb6 sets it, the selector's next update 0x459ef3 -> 0x7e01be
       clears it; the tick comes once a frame in between). Seeing it counts like a change of the session state. */
    if ((found0 || kls_menu_page) && klh_rd((DWORD_PTR)KLH_VA(KLS_STARTPEND), &pend, 1) && pend) { stateat = now; stateseen = 1; since = now; }
    if (found0) {
        if (found0 >= 2 && kls_keep_online && !kl_online() && kls_keep != found0) { kls_keep = found0; klog("expansion: page %d kept for the next online session (KeepPageOnline=1)", found0); }
        if (InterlockedExchange(&kls_menu_page, found0) != found0) {
            int r, nr = 0, ml = 0; char maps[200] = "";
            for (r = 0; r < kls_nrules; r++) if (kls_rule[r].page == found0 && ml < (int)sizeof maps - 90) ml += snprintf(maps + ml, sizeof maps - ml, "%s%s=%s", nr++ ? ", " : "", kls_slot[kls_rule[r].slot].name, kls_rule[r].map);
            if (found0 == 1) klog("expansion: menu page 1 latched: window '%s' is open (the stock map page: [Redirect] only)", KLS_MAPPAGE);
            else if (nr) klog("expansion: menu page %d latched: window '%s%d' is open ([Redirect.%d] %s)", found0, KLS_MAPPAGE, found0, found0, maps);
            else klog("expansion: menu page %d latched: window '%s%d' is open (no [Redirect.%d] line: every entry loads what [Redirect] or the stock game gives it)", found0, KLS_MAPPAGE, found0, found0);
        }
        return;
    }
    if (!kls_menu_page) return;
    /* a live window stack without a map page. Only the frontend may drop the latch, and not while a level is being
       started: the page must outlive the frontend's last frames (MP1: StartGame at :49.634, state 0x12 at :50.136,
       archive open at :50.151). */
    if (!klh_scene(scene, sizeof scene) || klh_level_key(scene, key, sizeof key)) { since = now; return; }       /* in a level: its menu never drops the page */
    if (pend) return;
    if (stateseen && (LONG)(now - stateat) < kls_quiet_ms) return;
    if ((LONG)(now - since) < kls_drop_ms) return;
    klog("expansion: menu page %ld dropped: the frontend shows [%s] (online=%d OnlineSet=%d kept=%d) - from now on a load uses [Redirect] only%s", InterlockedExchange(&kls_menu_page, 0), stack0,
         kl_online(), kls_online_set, kls_keep, (kls_online_set || (kls_keep_online && kls_keep)) ? " unless the online set applies" : "");
}

#undef stack0

/* ---------------------------------------------------------------- [Slots]: names by data write, from the tick */

static const char *const kls_stock[KLS_FA] = { "Locations/F01/F01_Main", "Locations/F02/F02_Main", "Locations/F03/F03_Main", "Locations/F04/F04_Main",
    "Locations/F05/F05_Main", "Locations/F06/F06_Main", "Locations/F07/F07_Main", "Locations/F08/F08_Main", "Locations/F09/F09_Main" };
static char kls_name[KLS_FA][KLS_NAME];       /* [Slots] names; "" = the slot keeps its stock name */
static int kls_set[KLS_FA], kls_nset;
static LONG kls_wrote[KLS_FA];                /* times a name had to be written (1 = once after the constructor) */

static void kls_slots_read(void)
{
    int i; char key[8]; const char *p;
    for (i = 0; i < KLS_FA; i++) {
        snprintf(key, sizeof key, "F%02d", i + 1);
        if (!GetPrivateProfileStringA("Slots", key, "", kls_name[i], KLS_NAME, klh_ini)) continue;    /* cut to 63 characters */
        for (p = kls_name[i]; *p && ((*p >= 'a' && *p <= 'z') || (*p >= 'A' && *p <= 'Z') || (*p >= '0' && *p <= '9') || *p == '_' || *p == '/'); p++) ;
        if (*p || kls_name[i][0] == '/') { klog("expansion: [Slots] %s=%s refused: letters, digits, '_' and '/' only", key, kls_name[i]); kls_name[i][0] = 0; continue; }
        if (!strcmp(kls_name[i], kls_stock[i])) { kls_name[i][0] = 0; continue; }      /* the stock name: nothing to do, and no reason to touch its lock */
        kls_set[i] = 1; kls_nset++;
        klog("expansion: [Slots] %s -> %s (written into the level list by the tick once it exists)", key, kls_name[i]);
    }
}

/* PAGE ENTRIES (2026-10-23, icons_1023c). WHY: the Arcade selector has nine entries whatever a page lists (UpperBound 8, re\menus.md 4.1);
 * the entries past a page's last map showed stock names and no picture. The selector skips an entry whose slot the level list reports
 * unavailable (0x9293ee / 0x929479, vtbl+0x14 = available[idx] of the DLC manager, byte +4+idx). So while an expansion page is latched
 * (kls_menu_page >= 2) the slots of its UNUSED entries (no F0n key in [Page.N]) are set to 0, and the saved bytes are put back when the page
 * is left. Also, once per latch, the option byte Heist_SelectedLevel is moved to the page's first entry when it points at an unused one.
 * GUESSES: that the skip applies to the right step only as the notes say (a page opened ON an unused entry is why the byte is moved),
 * and that the selector reads the byte when the page is built (klpm_arc.c); not run in the game when written. [Page.N] HideUnused=0 turns it off. */
#define KLS_HEISTSEL  0x0154d632
static const BYTE kls_menu_slot[9] = { 1, 2, 3, 4, 6, 7, 5, 8, 9 };      /* menu position -> slot number (kl2 0x746570) */
static int kls_pgmask[KLS_PAGES];                     /* bit i: the page has a map for slot F0(i+1); 0 = leave the page alone */
static BYTE kls_pgsaved[KLS_FA]; static int kls_pghid, kls_pgmoved, kls_pganyp;

static void kls_pages_read(void)
{
    int p, i; char sec[16], key[8], tmp[8];
    for (p = 2; p < KLS_PAGES; p++) {
        snprintf(sec, sizeof sec, "Page.%d", p);
        if (GetPrivateProfileIntA(sec, "HideUnused", 1, klh_ini) == 0) continue;
        for (i = 0; i < KLS_FA; i++) {
            snprintf(key, sizeof key, "F%02d", i + 1);
            if (GetPrivateProfileStringA(sec, key, "", tmp, sizeof tmp, klh_ini)) kls_pgmask[p] |= 1 << i;
        }
        if (kls_pgmask[p]) klog("expansion: page %d hides the entries of the slots without a map (mask %03x: the selector skips them)", p, kls_pgmask[p]);
    }
}

static void kls_page_entries(DWORD mgr, BYTE *m)
{   /* from the tick, the DLC manager read into m */
    int page = (int)kls_menu_page, i, mask = (page >= 2 && page < KLS_PAGES) ? kls_pgmask[page] : 0;
    if (mask) {
        for (i = 0; i < KLS_FA; i++) {
            BYTE zero = 0;
            if (mask & (1 << i)) continue;
            if (!(kls_pghid & (1 << i))) { kls_pgsaved[i] = m[4 + i]; kls_pghid |= 1 << i; }
            if (m[4 + i] && klh_data((void *)(DWORD_PTR)(mgr + 4 + i), &zero, 1, "FA slot hidden on a page")) m[4 + i] = 0;
        }
        if (kls_pgmoved != page) {
            BYTE cur = 0, nb; int k;
            kls_pgmoved = page;
            if (klh_rd((DWORD_PTR)KLH_VA(KLS_HEISTSEL), &cur, 1) && (cur > 8 || !(mask & (1 << (kls_menu_slot[cur] - 1))))) {
                for (k = 0; k < 9 && !(mask & (1 << (kls_menu_slot[k] - 1))); k++) ;
                nb = (BYTE)k;
                if (k < 9 && klh_data((void *)(DWORD_PTR)KLH_VA(KLS_HEISTSEL), &nb, 1, "selected map entry"))
                    klog("expansion: page %d: the selected entry %d is not on the page, moved to %d", page, cur, k);
            }
        }
        return;
    }
    kls_pgmoved = 0;
    for (i = 0; i < KLS_FA; i++) if (kls_pghid & (1 << i)) {            /* the page was left: put the bytes back */
        if (klh_data((void *)(DWORD_PTR)(mgr + 4 + i), &kls_pgsaved[i], 1, "FA slot restored")) { m[4 + i] = kls_pgsaved[i]; kls_pghid &= ~(1 << i); }
    }
}

/* PAGE CLAMP (2026-10-23, PH2 live run, TEST 1023g): the availability bytes above do NOT stop the selector - page 3 (4 maps) went to
 * entries 4..6 showing 'Financial' with no picture, page 2 to entry 8. So the selector itself is moved: when its entry (0xceceec, the
 * index kl_playtest's 'sel HeistLevel_P<n>' steers) is an unused one, 'Increase' / 'Decrease' is sent to the page's HeistLevel_P<n>
 * element - the message klauto's 'sel' sends (find 0x83faf0, vtbl+0x50) - toward the next map in the direction of travel, or back to
 * the last map shown when there is none. Game thread only, one message per 120 ms, at most 24 per page visit. */
#define KLS_SELIDX 0x00ceceec
typedef void *(__fastcall *KLS_FIND)(void *mgr, void *edx, const char *name);   /* 0x83faf0, thiscall */
typedef void (__fastcall *KLS_SEND)(void *elem, void *edx, const char **text);  /* vtbl+0x50, thiscall */
static DWORD klh_main_tid;                                                       /* defined in klhook.c (tentative here) */
static int kls_pc_page, kls_pc_last = -1, kls_pc_target = -1, kls_pc_sent; static DWORD kls_pc_t;

static int kls_entry_used(int mask, int k) { return k >= 0 && k < 9 && (mask & (1 << (kls_menu_slot[k] - 1))); }

static void kls_page_clamp(void)
{
    int page = (int)kls_menu_page, mask = (page >= 2 && page < KLS_PAGES) ? kls_pgmask[page] : 0, v, k, dir;
    DWORD idx = 0xffffffff, gui, mgr, vt, fn, now = GetTickCount(); void *e; char name[24]; const char *msg;
    if (page != kls_pc_page) { kls_pc_page = page; kls_pc_last = kls_pc_target = -1; kls_pc_sent = 0; }
    if (!mask || !klh_main_tid || GetCurrentThreadId() != klh_main_tid) return;
    if (!klh_rd((DWORD_PTR)KLH_VA(KLS_SELIDX), &idx, 4) || idx > 8) return;       /* not a position: the page is not up */
    v = (int)idx;
    if (kls_entry_used(mask, v)) { kls_pc_last = v; kls_pc_target = -1; kls_pc_sent = 0; return; }
    if (kls_pc_target < 0) {
        dir = kls_pc_last < 0 || v > kls_pc_last ? 1 : -1;
        for (k = v + dir; k >= 0 && k < 9 && !kls_entry_used(mask, k); k += dir) ;
        if (k < 0 || k >= 9) { if (kls_pc_last >= 0) k = kls_pc_last; else for (k = 0; k < 9 && !kls_entry_used(mask, k); k++) ; }
        if (k >= 9) return;
        kls_pc_target = k;
        klog("expansion: page %d: the selector is on entry %d (no map), moved to %d", page, v, k);
    }
    if (kls_pc_sent >= 24 || now - kls_pc_t < 120) return;
    if (!(gui = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c))) || !(mgr = klh_rd32(gui + 0x824))) return;
    snprintf(name, sizeof name, "HeistLevel_P%d", page);
    if (!(e = ((KLS_FIND)KLH_VA(0x83faf0))((void *)(DWORD_PTR)mgr, 0, name))) return;
    vt = klh_rd32((DWORD_PTR)e); fn = vt ? klh_rd32(vt + 0x50) : 0;
    if (fn < (DWORD)(DWORD_PTR)KLH_VA(0x401000) || fn >= (DWORD)(DWORD_PTR)KLH_VA(0xa00000)) return;  /* not kl2.exe code */
    msg = v > kls_pc_target ? "Decrease" : "Increase";
    ((KLS_SEND)(DWORD_PTR)fn)(e, 0, &msg);
    kls_pc_t = now; if (++kls_pc_sent == 24) klog("expansion: page %d: the selector did not reach entry %d after 24 messages - left alone", page, kls_pc_target);
}

static void kls_tick(void)
{   /* from klhook.c's tick: reads, and guarded data writes for renamed slots */
    static BYTE last[18 + KLS_FA * KLS_NAME]; static int lastopt = -2, toldforce; static DWORD calls;
    BYTE now[sizeof last], m[0x260]; DWORD mgr; int i, opt;
    if (!kls_on || !klh_exe_ok) return;
    kls_menu_watch();                             /* every tick: a page may be open for a few frames only */
    kls_page_clamp();
    if (calls++ & 7) return;
    if (kls_page_force >= 0 && !toldforce) { toldforce = 1; klog("expansion: menu page %d forced by [Expansion] Page: the menu is not looked at", kls_page_force); }
    if (kls_log >= 2 && (opt = kls_option_now()) != lastopt) {
        if (lastopt != -2 || opt) klog("expansion: menu option 'Dummy' reads %d (information only: the page is taken from the window stack)", opt);
        lastopt = opt;
    }
    if (!kls_nset && kls_log < 2 && !kls_pganyp) return;
    mgr = klh_rd32((DWORD_PTR)KLH_VA(KLS_DLCMGR));
    if (!mgr || !klh_rd(mgr, m, sizeof m) || *(DWORD *)m != KLS_DLCMGR_VT) return;
    for (i = 0; i < KLS_FA; i++) {
        BYTE b[KLS_NAME], one = 1;
        if (!kls_set[i]) continue;
        memset(b, 0, sizeof b); strcpy((char *)b, kls_name[i]);
        if (strncmp((char *)m + 0x16 + i * KLS_NAME, kls_name[i], KLS_NAME)) {
            char was[KLS_NAME + 1]; memcpy(was, m + 0x16 + i * KLS_NAME, KLS_NAME); was[KLS_NAME] = 0;
            if (klh_data((void *)(DWORD_PTR)(mgr + 0x16 + i * KLS_NAME), b, KLS_NAME, "FA slot name")) {
                memcpy(m + 0x16 + i * KLS_NAME, b, KLS_NAME);
                if (InterlockedIncrement(&kls_wrote[i]) <= 4) klog("expansion: [Slots] F%02d: level list entry '%s' -> '%s' (write %ld)", i + 1, was, kls_name[i], kls_wrote[i]);
            }
        }
        if (!m[4 + i] && klh_data((void *)(DWORD_PTR)(mgr + 4 + i), &one, 1, "FA slot available")) m[4 + i] = 1;      /* a renamed slot is ours: keep it selectable */
    }
    if (kls_pganyp) kls_page_entries(mgr, m);
    if (kls_set[0]) {                             /* the session manager's preset map name is a copy of the F01 literal */
        DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION)); char cur[KLS_NAME]; BYTE b[KLS_NAME];
        if (sm && klh_rd(sm + 8, cur, KLS_NAME) && !strncmp(cur, kls_stock[0], KLS_NAME)) {
            memset(b, 0, sizeof b); strcpy((char *)b, kls_name[0]);
            if (klh_data((void *)(DWORD_PTR)(sm + 8), b, KLS_NAME, "session default map name")) klog("expansion: [Slots] F01: session manager's preset map name -> '%s'", kls_name[0]);
        }
    }
    memcpy(now, m + 4, 18); memcpy(now + 18, m + 0x16, KLS_FA * KLS_NAME);
    if (!memcmp(now, last, sizeof now)) return;
    memcpy(last, now, sizeof now);
    for (i = 0; i < KLS_FA; i++) { m[0x16 + i * KLS_NAME + KLS_NAME - 1] = 0; klog("expansion: slot %d available=%d present=%d %s", i, m[4 + i], m[0xd + i], (char *)m + 0x16 + i * KLS_NAME); }
}

/* ---------------------------------------------------------------- set-up */

static int kls_plain(const char *s)
{   /* a folder name: letters, digits, '_' and '-' only (no separators, no dots) */
    if (!*s) return 0;
    for (; *s; s++) if (!((*s >= 'a' && *s <= 'z') || (*s >= 'A' && *s <= 'Z') || (*s >= '0' && *s <= '9') || *s == '_' || *s == '-')) return 0;
    return 1;
}

static void kls_compare(const char *slot, const char *to)
{   /* what the map folder holds, and which stock files of the slot have no counterpart */
    char pat[MAX_PATH], p[MAX_PATH]; WIN32_FIND_DATAA fd; HANDLE h; int n = 0;
    snprintf(pat, sizeof pat, "%s*", to);
    if ((h = FindFirstFileA(pat, &fd)) != INVALID_HANDLE_VALUE) {
        do if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) { klog("expansion:   has %s (%lu bytes)", fd.cFileName, fd.nFileSizeLow); n++; } while (FindNextFileA(h, &fd));
        FindClose(h);
    }
    if (!n) klog("expansion:   the map folder is empty: every open falls through to the stock level");
    snprintf(pat, sizeof pat, "%s\\Scenes\\Locations\\%s\\*", dir, slot);
    if ((h = FindFirstFileA(pat, &fd)) == INVALID_HANDLE_VALUE) return;
    do {
        size_t l = strlen(fd.cFileName);
        if ((fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || (l > 4 && !_stricmp(fd.cFileName + l - 4, ".hti"))) continue;   /* .hti: the exe never opens it */
        snprintf(p, sizeof p, "%s%s", to, fd.cFileName);
        if (!kls_isfile(p)) klog("expansion:   stock %s has no counterpart: %s", fd.cFileName, kls_fallback ? "the STOCK file will be used" : "the open will fail");
    } while (FindNextFileA(h, &fd));
    FindClose(h);
}

static void kls_rules(int page)
{   /* [Redirect] (page 0) or [Redirect.<page>] */
    char sec[16], keys[1024], val[64], *k;
    if (page) snprintf(sec, sizeof sec, "Redirect.%d", page); else strcpy(sec, "Redirect");
    if (!GetPrivateProfileStringA(sec, 0, "", keys, sizeof keys, klh_ini)) return;      /* all key names, NUL separated */
    for (k = keys; *k; k += strlen(k) + 1) {
        int r = kls_nrules, s; DWORD a; char key[96];
        GetPrivateProfileStringA(sec, k, "", val, sizeof val, klh_ini);
        if (r >= KLS_RULES) { klog("expansion: [%s] %s ignored: more than %d lines", sec, k, KLS_RULES); continue; }
        if (!kls_plain(k) || !kls_plain(val) || strlen(k) > 31 || strlen(val) > 47) { klog("expansion: [%s] %s=%s refused: plain folder names only", sec, k, val); continue; }
        snprintf(kls_rule[r].to, MAX_PATH, "%s\\Maps\\%s\\", kls_root, val);
        a = GetFileAttributesA(kls_rule[r].to);
        if (a == INVALID_FILE_ATTRIBUTES || !(a & FILE_ATTRIBUTE_DIRECTORY)) { klog("expansion: [%s] %s=%s: folder %s not found, rule off (stock level stays)", sec, k, val, kls_rule[r].to); continue; }
        snprintf(key, sizeof key, "\\scenes\\locations\\%s\\", k); kls_lower(key, key);
        for (s = 0; s < kls_nslots && strcmp(kls_slot[s].key, key); s++) ;
        if (s == kls_nslots) {
            if (s >= KLS_SLOTS) { klog("expansion: [%s] %s ignored: more than %d different slots", sec, k, KLS_SLOTS); continue; }
            strcpy(kls_slot[s].key, key); kls_slot[s].keylen = (int)strlen(key); kls_slot[s].page = -1;
            snprintf(kls_slot[s].name, sizeof kls_slot[s].name, "%s", k);
            snprintf(kls_slot[s].zip, sizeof kls_slot[s].zip, "%s_main.zip", k); kls_lower(kls_slot[s].zip, kls_slot[s].zip);
            kls_nslots++;
        }
        if (kls_find_rule(s, page) >= 0) { klog("expansion: [%s] %s=%s ignored: the slot already has a line in this section", sec, k, val); continue; }
        kls_rule[r].tolen = (int)strlen(kls_rule[r].to); kls_rule[r].slot = s; kls_rule[r].page = page;
        if (page) kls_npaged++;
        snprintf(kls_rule[r].map, sizeof kls_rule[r].map, "%s", val);
        kls_nrules++;
        klog("expansion: [%s] Scenes\\Locations\\%s\\ -> %s", sec, k, kls_rule[r].to);
        kls_compare(k, kls_rule[r].to);
    }
}

static void kls_init(HINSTANCE inst)
{   /* from DllMain, after klhook.c's own set-up; no game code has run yet */
    char root[64], mf[128]; DWORD a; int n, p;
    (void)inst;
    InitializeCriticalSection(&kls_cs);
    if (!GetPrivateProfileIntA("Expansion", "Enable", 0, klh_ini)) {
        /* the expansion is off, but klsteam.c still has to see which level archive the game opens: these two
           wrappers then pass every call on unchanged (kls_map answers 0 while kls_on is 0) */
        if (!klx_on) return;
        n  = klh_iat("KERNEL32.dll", "CreateFileA", (void *)kls_CreateFileA, (void **)&kls_real_CreateFileA);
        n += klh_iat("KERNEL32.dll", "CreateFileW", (void *)kls_CreateFileW, (void **)&kls_real_CreateFileW);
        klog("steam: CreateFileA %s, CreateFileW %s wrapped to see which level archive is opened (no redirect: [Expansion] is off)", kls_real_CreateFileA ? "yes" : "NO", kls_real_CreateFileW ? "yes" : "NO");
        return;
    }
    kls_log = GetPrivateProfileIntA("Expansion", "Log", 1, klh_ini);
    kls_fallback = GetPrivateProfileIntA("Expansion", "Fallback", 1, klh_ini);
    kls_page_force = (int)GetPrivateProfileIntA("Expansion", "Page", -1, klh_ini);
    if (kls_page_force >= KLS_PAGES) kls_page_force = -1;
    kls_online_set = (int)GetPrivateProfileIntA("Expansion", "OnlineSet", 0, klh_ini);
    if (kls_online_set < 0 || kls_online_set >= KLS_PAGES) { klog("expansion: OnlineSet=%d is not a page (0, 2..8, 9 = random): ignored", kls_online_set); kls_online_set = 0; }
    if (kls_online_set == KLS_RANDOM) klog("expansion: OnlineSet=9: RANDOM map per slot in a network session (stock + every page with a rule for the slot), seeded from the lobby id; page 9 itself cannot hold rules; NOT run live");
    if (kls_online_set == 1) { klog("expansion: OnlineSet=1 is the stock page: ignored"); kls_online_set = 0; }
    kls_keep_online = GetPrivateProfileIntA("Expansion", "KeepPageOnline", 0, klh_ini) != 0;
    kls_keep_clear = GetPrivateProfileIntA("Expansion", "KeepClear", 1, klh_ini) != 0;
    if (kls_online_set || kls_keep_online)
        klog("expansion: online map set: OnlineSet=%d KeepPageOnline=%d KeepClear=%d - in a network session the Dead Men page is used for the level load; NOT sent to peers, all peers need the same ini; do not use in Quick Match", kls_online_set, kls_keep_online, kls_keep_clear);
    GetPrivateProfileStringA("Expansion", "Root", "KLExpansion", root, sizeof root, klh_ini);
    if (!kls_plain(root)) { klog("expansion: Root=%s refused: a plain folder name next to kl2.exe is needed", root); return; }
    kls_lower(kls_game_low, dir); kls_game_len = (int)strlen(kls_game_low);
    snprintf(kls_patch_low, sizeof kls_patch_low, "%s\\patch01.zip", kls_game_low);
    snprintf(kls_root, sizeof kls_root, "%s\\%s", dir, root); kls_lower(kls_root_low, kls_root); kls_root_len = (int)strlen(kls_root_low);
    snprintf(kls_overlay, sizeof kls_overlay, "%s\\Overlay", kls_root);
    a = GetFileAttributesA(kls_overlay);
    kls_overlay_on = GetPrivateProfileIntA("Expansion", "Overlay", 1, klh_ini) && a != INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_DIRECTORY);
    klog("expansion: enabled; root %s; overlay %s; Fallback=%d Log=%d Page=%d", kls_root, kls_overlay_on ? "on" : "off (no Overlay folder, or Overlay=0)",
         kls_fallback, kls_log, kls_page_force);
    if (GetPrivateProfileStringA("Expansion", "MountFirst", "", mf, sizeof mf, klh_ini)) {
        size_t l = strlen(mf); char full[MAX_PATH];
        snprintf(full, sizeof full, "%s\\%s", dir, mf);
        if (l < 5 || _stricmp(mf + l - 4, ".zip") || strchr(mf, ':') || mf[0] == '\\' || mf[0] == '/' || strstr(mf, ".."))
            klog("expansion: MountFirst=%s refused: a name relative to the game folder ending in .zip is needed", mf);
        else if (!kls_isfile(full)) klog("expansion: MountFirst: %s does not exist, ignored", full);
        else { GetFullPathNameA(full, MAX_PATH, kls_patch_alias, 0);
               klog("expansion: MountFirst=%s: an open of Patch01.zip is answered with this file (no code patch; it must hold the stock members too)", mf); }
    }
    for (p = 0; p < KLS_PAGES; p++) {
        char sec[16], title[64];
        kls_rules(p);
        snprintf(sec, sizeof sec, "Page.%d", p);
        if (p && GetPrivateProfileStringA(sec, "Title", "", title, sizeof title, klh_ini)) klog("expansion: menu page %d is '%s'", p, title);
    }
    kls_slots_read();
    kls_pages_read();
    { int q; for (q = 2; q < KLS_PAGES; q++) if (kls_pgmask[q]) kls_pganyp = 1; }
    kls_on = 1;
    n  = klh_iat("KERNEL32.dll", "CreateFileA", (void *)kls_CreateFileA, (void **)&kls_real_CreateFileA);
    n += klh_iat("KERNEL32.dll", "CreateFileW", (void *)kls_CreateFileW, (void **)&kls_real_CreateFileW);
    n += klh_iat("KERNEL32.dll", "GetFileAttributesA", (void *)kls_GetFileAttributesA, (void **)&kls_real_GetFileAttributesA);
    n += klh_iat("KERNEL32.dll", "FindFirstFileA", (void *)kls_FindFirstFileA, (void **)&kls_real_FindFirstFileA);
    n += klh_iat(0, "fopen", (void *)kls_fopen, (void **)&kls_real_fopen);
    klog("expansion: %d import(s) of the exe wrapped (CreateFileA %s, CreateFileW %s, GetFileAttributesA %s, FindFirstFileA %s, fopen %s); %d redirect rule(s) for %d slot(s); %d slot name(s)",
         n, kls_real_CreateFileA ? "yes" : "NO", kls_real_CreateFileW ? "yes" : "no", kls_real_GetFileAttributesA ? "yes" : "no",
         kls_real_FindFirstFileA ? "yes" : "no", kls_real_fopen ? "yes" : "no", kls_nrules, kls_nslots, kls_nset);
    if (kls_nset && !klh_exe_ok) klog("expansion: [Slots] needs kl2.exe build 0490: ignored on this exe");
}

#if defined(KLSLOT_TEST) || defined(KLHOOK_HARNESS)
/* Test harness entry points (never built into the game's DLL). */
__declspec(dllexport) int kls_test_map(const char *in, char *out) { return kls_map(in, out, "test"); }
__declspec(dllexport) void kls_test_page(int page) { kls_page_force = page; }
__declspec(dllexport) int kls_test_menu(void *mapped, int drop_ms, int quiet_ms)
{   /* one look at the made-up window stack; -> the latched page */
    klh_delta = (LONG_PTR)((DWORD_PTR)mapped - KL2_BASE); klh_exe_ok = 1;
    if (drop_ms >= 0) kls_drop_ms = drop_ms;
    if (quiet_ms >= 0) kls_quiet_ms = quiet_ms;
    kls_menu_watch();
    return (int)kls_menu_page;
}
__declspec(dllexport) int kls_test_tick(void *mapped, int times)
{   /* run the tick against a copy of kl2.exe mapped anywhere (its .data holds the harness's made-up pointers); -> names written */
    int i, n = 0;
    klh_delta = (LONG_PTR)((DWORD_PTR)mapped - KL2_BASE); klh_exe_ok = 1;
    for (i = 0; i < times * 8; i++) kls_tick();
    for (i = 0; i < KLS_FA; i++) n += kls_wrote[i];
    return n;
}
__declspec(dllexport) const char *kls_test_slot_name(int i) { return kls_name[i]; }
#endif
#endif /* KLSLOT_C */
