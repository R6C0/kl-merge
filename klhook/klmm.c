/*
 * klmm.c - PRIVATE / BUILD-KEYED FRAGILE ALLIANCE LOBBIES: a proxy ISteamMatchmaking behind the import slot of
 * steam_api.SteamMatchmaking (kl2.exe 0xb107d8). Part of KLHook (included by klhook.c right after klsteam.c, SHIP and TEST
 * alike). Route A of re\private_match.md (section 6 is this file's design). v82g.
 *
 * NOTHING HERE HAS RUN IN THE GAME. Off by default, and when off NOTHING is installed: with neither key below set the
 * import slot is not touched and the hook behaves as v82f. The keys (KLHook.ini):
 *   [Net]
 *   PrivateLobby=0   0 = untouched. 1 = every lobby the game creates is FriendsOnly (Steam ELobbyType 1), 2 = Private /
 *                    invite-only (type 0). Replaces the type argument of CreateLobby (vtable +0x30); max members is
 *                    forwarded as it came. NB the value is NOT the Steam enum: 1 -> 1, 2 -> 0.
 *                    1025: ALSO the key klx_set = "set<N>" (N = [Expansion] OnlineSet, 0 = stock page) is written the same way and filtered the
 *                    same way, so a host on Retomoto page 2 and a searcher on random (9) do not meet. The game's Quick Match (Join Game), Ranked and
 *                    Find Game all go through RequestLobbyList / CreateLobby / SetLobbyData, so they are all covered (re\online_server.md).
 *   BuildKey=0       1 = the lobby carries the id of the installed expansion map set and the search asks for it:
 *                      - SetLobbyData (+0x4c): after a forwarded call whose key is "name" (the first call of the game's
 *                        0x869430, for a create and for every later update) one more real SetLobbyData(id, "klx_build",
 *                        <build id>);
 *                      - RequestLobbyList (+0x10): first the REAL AddRequestLobbyListStringFilter(+0x14)
 *                        ("klx_build", <build id>, 0 = Equal), then RequestLobbyList. A lobby of a stock game has no such
 *                        key and is not listed.
 *
 * THE BUILD ID: FNV-1a over, for each <game>\<Root>\Maps\<dir>\F*_Main.zip in lower-case path order, the path
 * "<dir>\<file>", the file size and the hash of the zip's central directory (klsteam.c's klx_fingerprint: the directory
 * holds every member's CRC-32 and size, so the id changes when any member of any map changes). Written as 8 hex
 * digits; "none" when there is no map. NOT in the id: write times (a copy of the folder to a friend's PC changes them),
 * the .WHD / .WAV beside a zip, KLJoin.ini and the other loose files, the hook's own version. GUESS: that this is the
 * set a friend has to share to play the same map (it is the set klslot.c can redirect to; a friend with the same maps in
 * other folder names gets another id). The id is computed once, at the first lobby call that needs it.
 *
 * HOW: ONE import slot, no byte of kl2.exe's code (re\private_match.md 4: 0xb107d8 is in no hashed range).
 *   - The proxy is one object, a dword pointing at a table of 36 functions (0x00 .. 0x8c). 33 of them are naked tail
 *     jumps (ecx = the real interface; `jmp [real vtable + 4n]`): the stack and the return registers are untouched,
 *     so argument sizes do not matter for them. Three are real functions: 4 RequestLobbyList, 12 CreateLobby,
 *     19 SetLobbyData. Same pattern as klsteam.c.
 *   - The interface: PROVEN 2026-10-17 from steamclient.dll (the one in C:\Steam, 21,377,688 bytes) that the 36-slot layout
 *     is right and which argument sizes the slots I call have: CAdapterSteamMatchmaking008 (36 slots) ret counts, slots
 *     11..35 in order 8 8 8 0x10 8 0x10 0xc 0x10 8 0x1c 0xc 0x14 0x10 0x10 0x1c 8 0x18 0x14 0xc 8 0xc 0xc 0xc 0x10 = what
 *     the SDK header says (CSteamID = 2 dwords); its slots 4..10 jump to the client class (IClientMatchmaking, vtable
 *     in the same file) whose methods pop 0 / 0xc / 0xc / 8 / 4 / 4 / 4 bytes. The slot at +0x14 reads its first TWO
 *     arguments with the string writer 0x386280b0 and the third as a 4-byte number: AddRequestLobbyListStringFilter(key,
 *     value, comparison), 12 bytes - PROVEN; +0x18 reads the first with the string writer and the other two as numbers:
 *     Numerical. The game calls +0x18 with three pushes and +0x1c with two (re\private_match.md 2), so the order String,
 *     Numerical, NearValue is confirmed. Still GUESS: that the comparison value 0 means Equal for a STRING filter
 *     (the game's numerical calls push 0 for Equal; the SDK enum is one for both); that the filter makes the server
 *     accumulate it until RequestLobbyList (SDK docs).
 *   - Before the table is handed out klmm_SteamMatchmaking checks that the loaded steam_api.dll holds exactly the text
 *     "SteamMatchMaking008" (and no other SteamMatchMaking0xx) and that all 36 slots of the real interface point into
 *     code of a loaded module; otherwise "NOT PROXIED" is logged and the game gets the real interface.
 *
 * ONLINESAFE ([Net] OnlineSafe, klhook.c kl_online): NOT applied as a gate, on purpose. kl_online() is true once the
 * session role is SERVER / CLIENT, and the host's CreateLobby is made from inside that session (GUESS: the role is
 * already 2 when 0x705000 runs), so a gate would switch the feature off exactly when it is needed. These calls change
 * Steam lobby metadata only - no game state, nothing a peer sees as a desync - and each key is an explicit opt-in. Every
 * log line says what kl_online() answered at that moment ("online=0/1"), so the first live run shows what a gate would
 * have done; to gate anyway, put `if (kl_online()) forward` at the top of the three overrides.
 *
 * LOG (KLHook.log; no Steam id of anyone is written, the lobby id is never printed)
 *   mm: import SteamMatchmaking wrapped (1 slot): 36 slots, PrivateLobby=1 BuildKey=1, build id 1a2b3c4d (3 map archive(s))
 *   mm: CreateLobby(type 2, max 16) -> type 1 (PrivateLobby=1) online=1
 *   mm: SetLobbyData key 'name' seen: klx_build=1a2b3c4d written (ok=1) online=1
 *   mm: RequestLobbyList: string filter klx_build=1a2b3c4d (Equal) added first online=0
 *   (at most 200 lines per process)
 */
#ifndef KLMM_C
#define KLMM_C

#define KLMM_NSLOT 36

static void *(__cdecl *klmm_real_accessor)(void);
static void **klmm_real;                              /* the real ISteamMatchmaking (points at its vtable pointer); set at each accessor call */
static void *klmm_vt[KLMM_NSLOT];
static struct { void **vt; } klmm_proxy = { klmm_vt };
static int klmm_private, klmm_buildkey;               /* [Net] PrivateLobby (0/1/2), BuildKey (0/1) */
static char klmm_id[16];                              /* the build id, "" until computed */
static char klmm_set[16];                             /* "set<N>": [Expansion] OnlineSet (0 = stock page), the second lobby key klx_set (1025: Quick Match / Ranked) */
static int klmm_maxp;                                  /* [Lobby] MaxPlayers (0 = stock): Steam lobby member limit floor, 1025 re\max_players.md */
static volatile LONG klmm_nlimit;                      /* SetLobbyMemberLimit calls raised */
static CRITICAL_SECTION klmm_cs;
static volatile LONG klmm_nlog;

static void klmm_say(const char *fmt, ...)
{
    char b[300]; va_list ap;
    if (InterlockedIncrement(&klmm_nlog) > 200) return;
    va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    klog("mm: %s", b);
}

/* ---------------------------------------------------------------- the build id */

typedef struct { char name[96]; DWORD size, hash; } klmm_ent;

static int klmm_map_set(klmm_ent *e, int cap)
{   /* <game>\<Root>\Maps\<dir>\F*_Main.zip, sorted by name -> count */
    char root[MAX_PATH], pat[MAX_PATH], sub[MAX_PATH], zp[MAX_PATH]; WIN32_FIND_DATAA d1, d2; HANDLE h1, h2; int n = 0, i, j; FILETIME ft;
    GetPrivateProfileStringA("Expansion", "Root", "KLExpansion", root, sizeof root, klh_ini);
    if (!root[0] || strchr(root, ':') || strchr(root, '\\') || strchr(root, '/') || strstr(root, "..")) return 0;
    snprintf(pat, sizeof pat, "%s\\%s\\Maps\\*", dir, root);
    h1 = FindFirstFileA(pat, &d1);
    if (h1 == INVALID_HANDLE_VALUE) return 0;
    do {
        if (!(d1.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || d1.cFileName[0] == '.') continue;
        snprintf(sub, sizeof sub, "%s\\%s\\Maps\\%s", dir, root, d1.cFileName);
        snprintf(pat, sizeof pat, "%s\\F*_Main.zip", sub);
        h2 = FindFirstFileA(pat, &d2);
        if (h2 == INVALID_HANDLE_VALUE) continue;
        do {
            DWORD size = 0, hash = 0; char *p; size_t l = strlen(d2.cFileName);
            if ((d2.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || l < 5 || _stricmp(d2.cFileName + l - 4, ".zip") || n >= cap) continue;
            snprintf(zp, sizeof zp, "%s\\%s", sub, d2.cFileName);
            if (!klx_fingerprint(zp, &size, &hash, &ft, 0)) { size = d2.nFileSizeLow; hash = 0xffffffffu; }   /* unreadable directory: size alone, marked */
            snprintf(e[n].name, sizeof e[n].name, "%s\\%s", d1.cFileName, d2.cFileName);
            for (p = e[n].name; *p; p++) if (*p >= 'A' && *p <= 'Z') *p += 32;
            e[n].size = size; e[n].hash = hash; n++;
        } while (FindNextFileA(h2, &d2));
        FindClose(h2);
    } while (FindNextFileA(h1, &d1));
    FindClose(h1);
    for (i = 1; i < n; i++) {                                 /* insertion sort by name: the id must not depend on the directory order */
        klmm_ent t = e[i];
        for (j = i - 1; j >= 0 && strcmp(e[j].name, t.name) > 0; j--) e[j + 1] = e[j];
        e[j + 1] = t;
    }
    return n;
}

static const char *klmm_build_id(void)
{   /* computed once; "" never returned */
    static klmm_ent ent[64]; int n, i;
    EnterCriticalSection(&klmm_cs);
    if (!klmm_id[0]) {
        DWORD h = 2166136261u;
        n = klmm_map_set(ent, 64);
        for (i = 0; i < n; i++) {
            h = klx_fnv((const BYTE *)ent[i].name, (DWORD)strlen(ent[i].name) + 1, h);
            h = klx_fnv((const BYTE *)&ent[i].size, 4, h);
            h = klx_fnv((const BYTE *)&ent[i].hash, 4, h);
        }
        if (n) snprintf(klmm_id, sizeof klmm_id, "%08lx", (unsigned long)h); else snprintf(klmm_id, sizeof klmm_id, "none");
        klmm_say("build id %s from %d map archive(s) under the expansion's Maps folder%s", klmm_id, n, n ? "" : " (none found: every host without maps shares this id)");
    }
    LeaveCriticalSection(&klmm_cs);
    return klmm_id;
}

/* ---------------------------------------------------------------- the proxy interface (thiscall as __fastcall, see klsteam.c) */

#define KLMM_REAL(n) ((*(void ***)klmm_real)[n])
#define KLMM_FWD(n) static __declspec(naked) void klmm_fwd##n(void) { __asm mov ecx, dword ptr [klmm_real] __asm mov eax, dword ptr [ecx] __asm jmp dword ptr [eax + 4 * n] }
KLMM_FWD(0) KLMM_FWD(1) KLMM_FWD(2) KLMM_FWD(3) KLMM_FWD(5) KLMM_FWD(6) KLMM_FWD(7) KLMM_FWD(8) KLMM_FWD(9) KLMM_FWD(10) KLMM_FWD(11)
KLMM_FWD(13) KLMM_FWD(14) KLMM_FWD(15) KLMM_FWD(16) KLMM_FWD(17) KLMM_FWD(18) KLMM_FWD(20) KLMM_FWD(21) KLMM_FWD(22) KLMM_FWD(23)
KLMM_FWD(24) KLMM_FWD(25) KLMM_FWD(26) KLMM_FWD(27) KLMM_FWD(28) KLMM_FWD(29) KLMM_FWD(30) KLMM_FWD(31) KLMM_FWD(32) KLMM_FWD(33)
KLMM_FWD(34) KLMM_FWD(35)

/* slot 30 SetLobbyMemberLimit(CSteamID lobby, int cMax): thiscall, stack [esp+4]/[esp+8] = the 64-bit id, [esp+0xc] = cMax (SDK 008; the game
   calls it from 0x869430 with the property byte +5). A naked stub that raises cMax IN PLACE to [Lobby] MaxPlayers and tail-jumps, so the argument
   size is not needed (GUESS that this call site pushes the SDK layout: the slot index 0x78/4 = 30 is the SDK's and 0x869430 calls vtable +0x78). */
static __declspec(naked) void klmm_fwd30_limit(void)
{
    __asm {
        mov eax, dword ptr [klmm_maxp]
        cmp eax, dword ptr [esp + 0xc]
        jle done
        mov dword ptr [esp + 0xc], eax
        lock inc dword ptr [klmm_nlimit]
    done:
        mov ecx, dword ptr [klmm_real]
        mov eax, dword ptr [ecx]
        jmp dword ptr [eax + 4 * 30]
    }
}

static unsigned __int64 __fastcall klmm_RequestLobbyList(void *self, void *edx)
{   /* slot 4, 0 bytes; SteamAPICall_t in edx:eax */
    (void)self; (void)edx;
    if (klmm_buildkey) {
        const char *id = klmm_build_id();
        ((void (__fastcall *)(void *, void *, const char *, const char *, int))KLMM_REAL(5))(klmm_real, 0, "klx_build", id, 0);      /* AddRequestLobbyListStringFilter, 12 bytes */
        klmm_say("RequestLobbyList: string filter klx_build=%s (Equal) added first online=%d", id, kl_online());
        ((void (__fastcall *)(void *, void *, const char *, const char *, int))KLMM_REAL(5))(klmm_real, 0, "klx_set", klmm_set, 0);
        klmm_say("RequestLobbyList: string filter klx_set=%s (Equal) added second (Quick Match / Ranked / Find Game search alike) online=%d", klmm_set, kl_online());
    }
    return ((unsigned __int64 (__fastcall *)(void *, void *))KLMM_REAL(4))(klmm_real, 0);
}

static unsigned __int64 __fastcall klmm_CreateLobby(void *self, void *edx, int type, int maxmembers)
{   /* slot 12, 8 bytes; SteamAPICall_t */
    int t = type; (void)self; (void)edx;
    int m = maxmembers;
    if (klmm_private) t = klmm_private == 1 ? 1 : 0;           /* 1 -> FriendsOnly (1), 2 -> Private (0) */
    if (klmm_maxp && m < klmm_maxp) m = klmm_maxp;             /* the limit is the lobby's target at create time (0x6c9ce4 reads sm+0xb9): raise it to the floor */
    klmm_say("CreateLobby(type %d%s, max %d -> %d [Lobby] MaxPlayers=%d) -> type %d (PrivateLobby=%d) online=%d", type, type == 3 ? " = Ranked" : type == 2 ? " = public (Quick Match / Player Match)" : "", maxmembers, m, klmm_maxp, t, klmm_private, kl_online());
    return ((unsigned __int64 (__fastcall *)(void *, void *, int, int))KLMM_REAL(12))(klmm_real, 0, t, m);
}

static char __fastcall klmm_SetLobbyData(void *self, void *edx, unsigned __int64 lobby, const char *key, const char *value)
{   /* slot 19, 16 bytes (CSteamID = 2 dwords, key, value); bool in al */
    char r = ((char (__fastcall *)(void *, void *, unsigned __int64, const char *, const char *))KLMM_REAL(19))(klmm_real, 0, lobby, key, value);
    (void)self; (void)edx;
    if (klmm_buildkey && key && !strcmp(key, "name")) {
        const char *id = klmm_build_id();
        char r2 = ((char (__fastcall *)(void *, void *, unsigned __int64, const char *, const char *))KLMM_REAL(19))(klmm_real, 0, lobby, "klx_build", id);
        char r3 = ((char (__fastcall *)(void *, void *, unsigned __int64, const char *, const char *))KLMM_REAL(19))(klmm_real, 0, lobby, "klx_set", klmm_set);
        klmm_say("SetLobbyData key 'name' seen: klx_build=%s (ok=%d) klx_set=%s (ok=%d) written online=%d", id, r2 != 0, klmm_set, r3 != 0, kl_online());
    }
    return r;
}

static int klmm_has_008(void)
{   /* the loaded steam_api.dll asks steamclient for exactly this interface version (and no other SteamMatchMaking0xx) */
    static const char want[] = "SteamMatchMaking008"; HMODULE m = GetModuleHandleA("steam_api.dll"); BYTE *b = (BYTE *)m, *copy; IMAGE_NT_HEADERS *nt; DWORD n, i; int found = 0, other = 0;
    if (!m) return 0;
    nt = (IMAGE_NT_HEADERS *)(b + ((IMAGE_DOS_HEADER *)b)->e_lfanew); n = nt->OptionalHeader.SizeOfImage;
    if (n < 0x1000 || n > (64u << 20) || !(copy = (BYTE *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, n + sizeof want))) return 0;
    for (i = 0; i + 0x1000 <= n; i += 0x1000) klh_rd((DWORD_PTR)(b + i), copy + i, 0x1000);      /* a page that cannot be read stays zero */
    for (i = 0; i + 20 <= n; i++)
        if (copy[i] == 'S' && !memcmp(copy + i, "SteamMatchMaking0", 17)) {
            if (!memcmp(copy + i, want, sizeof want)) found = 1; else other = 1;      /* sizeof want includes the NUL: "...008\0" only */
        }
    HeapFree(GetProcessHeap(), 0, copy);
    return found && !other;
}

static void *__cdecl klmm_SteamMatchmaking(void)
{
    static LONG told; void **r = (void **)klmm_real_accessor(), **vt; MEMORY_BASIC_INFORMATION mbi; int i, bad = -1;
    if (!r) return 0;                                          /* Steam not running: the game gets what it would have got */
    if (r == klmm_real) return &klmm_proxy;
    if (!klh_rd((DWORD_PTR)r, &vt, sizeof vt)) bad = 0;
    for (i = 0; bad < 0 && i < KLMM_NSLOT; i++) {
        void *f = 0;
        if (!klh_rd((DWORD_PTR)(vt + i), &f, sizeof f) || !VirtualQuery(f, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT || mbi.Type != MEM_IMAGE ||
            !(mbi.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY))) bad = i;
    }
    if (bad >= 0) {
        if (!InterlockedExchange(&told, 2)) klmm_say("NOT PROXIED - the interface at %p has no code at slot %d of %d: not the 008 table; the game gets the real interface", (void *)r, bad, KLMM_NSLOT);
        return r;
    }
    klmm_real = r;
    if (!InterlockedExchange(&told, 1)) klmm_say("the game asked for ISteamMatchmaking: real interface %p, %d slots checked, proxy handed out", (void *)r, KLMM_NSLOT);
    return &klmm_proxy;
}

static void klmm_init(void)
{
    int i, n;
    klmm_private = (int)GetPrivateProfileIntA("Net", "PrivateLobby", 0, klh_ini);
    klmm_buildkey = (int)GetPrivateProfileIntA("Net", "BuildKey", 0, klh_ini);
    if (klmm_private < 0 || klmm_private > 2) { klog("mm: [Net] PrivateLobby=%d is not 0, 1 or 2: ignored", klmm_private); klmm_private = 0; }
    if (klmm_buildkey != 0 && klmm_buildkey != 1) { klog("mm: [Net] BuildKey=%d is not 0 or 1: ignored", klmm_buildkey); klmm_buildkey = 0; }
    i = (int)GetPrivateProfileIntA("Expansion", "OnlineSet", 0, klh_ini);
    snprintf(klmm_set, sizeof klmm_set, "set%d", i < 0 || i > 9 ? 0 : i);
    /* 1025 [HostOpts] Enable=1 + Steam=1: the proxy is also needed for the host's options (klhostopt.c reads/writes the lobby key klx_opts through klmm_real) */
    klmm_maxp = (int)GetPrivateProfileIntA("Lobby", "MaxPlayers", 0, klh_ini);
    if (klmm_maxp != 0 && (klmm_maxp < 9 || klmm_maxp > 16)) { klog("mm: [Lobby] MaxPlayers=%d is not 0 or 9..16: ignored (8 is the stock size)", klmm_maxp); klmm_maxp = 0; }
    if (!klmm_private && !klmm_buildkey && !klmm_maxp && !(GetPrivateProfileIntA("HostOpts", "Enable", 0, klh_ini) && GetPrivateProfileIntA("HostOpts", "Steam", 1, klh_ini))
        && !(GetPrivateProfileIntA("CharOnline", "Enable", 0, klh_ini) && GetPrivateProfileIntA("CharOnline", "Steam", 1, klh_ini))
        && !((GetPrivateProfileIntA("Ucc", "Pings", 0, klh_ini) || GetPrivateProfileIntA("Ucc", "Accuse", 0, klh_ini)) && GetPrivateProfileIntA("NetChan", "Steam", 1, klh_ini))) return;   /* klnetchan.c's member data klx_msg */               /* default: nothing installed, v82f behaviour */
    InitializeCriticalSection(&klmm_cs);
    for (i = 0; i < KLMM_NSLOT; i++) klmm_vt[i] = 0;
    klmm_vt[0] = (void *)klmm_fwd0; klmm_vt[1] = (void *)klmm_fwd1; klmm_vt[2] = (void *)klmm_fwd2; klmm_vt[3] = (void *)klmm_fwd3;
    klmm_vt[4] = (void *)klmm_RequestLobbyList;
    klmm_vt[5] = (void *)klmm_fwd5; klmm_vt[6] = (void *)klmm_fwd6; klmm_vt[7] = (void *)klmm_fwd7; klmm_vt[8] = (void *)klmm_fwd8; klmm_vt[9] = (void *)klmm_fwd9;
    klmm_vt[10] = (void *)klmm_fwd10; klmm_vt[11] = (void *)klmm_fwd11;
    klmm_vt[12] = (void *)klmm_CreateLobby;
    klmm_vt[13] = (void *)klmm_fwd13; klmm_vt[14] = (void *)klmm_fwd14; klmm_vt[15] = (void *)klmm_fwd15; klmm_vt[16] = (void *)klmm_fwd16; klmm_vt[17] = (void *)klmm_fwd17;
    klmm_vt[18] = (void *)klmm_fwd18;
    klmm_vt[19] = (void *)klmm_SetLobbyData;
    klmm_vt[20] = (void *)klmm_fwd20; klmm_vt[21] = (void *)klmm_fwd21; klmm_vt[22] = (void *)klmm_fwd22; klmm_vt[23] = (void *)klmm_fwd23; klmm_vt[24] = (void *)klmm_fwd24;
    klmm_vt[25] = (void *)klmm_fwd25; klmm_vt[26] = (void *)klmm_fwd26; klmm_vt[27] = (void *)klmm_fwd27; klmm_vt[28] = (void *)klmm_fwd28; klmm_vt[29] = (void *)klmm_fwd29;
    klmm_vt[30] = (void *)(klmm_maxp ? (void *)klmm_fwd30_limit : (void *)klmm_fwd30); klmm_vt[31] = (void *)klmm_fwd31; klmm_vt[32] = (void *)klmm_fwd32; klmm_vt[33] = (void *)klmm_fwd33; klmm_vt[34] = (void *)klmm_fwd34;
    klmm_vt[35] = (void *)klmm_fwd35;
    for (i = 0; i < KLMM_NSLOT; i++) if (!klmm_vt[i]) { klog("mm: NOT PROXIED - proxy slot %d has no function (a build error)", i); return; }
    if (!klmm_has_008()) {
        klog("mm: NOT PROXIED - the loaded steam_api.dll does not ask for exactly SteamMatchMaking008 (or is not loaded): the table would not fit. Lobbies are made as in the stock game");
        return;
    }
    n = klh_iat("steam_api.dll", "SteamMatchmaking", (void *)klmm_SteamMatchmaking, (void **)&klmm_real_accessor);
    if (!n) { klog("mm: NOT PROXIED - the import steam_api.SteamMatchmaking was not found or not changed"); return; }
    klog("mm: import SteamMatchmaking wrapped (%d slot): ISteamMatchmaking 008 proxy, %d slots, 3 overridden (RequestLobbyList, CreateLobby, SetLobbyData); PrivateLobby=%d BuildKey=%d; build id when first needed",
         n, KLMM_NSLOT, klmm_private, klmm_buildkey);
}

#endif /* KLMM_C */
