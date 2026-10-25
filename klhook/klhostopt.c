/*
 * klhostopt.c - [HostOpts] HOST-CONTROLLED MATCH OPTIONS (2026-10-25; owner: 'make more options you switch on n off either in that match
 * lobby screen for the host or in the game settings tab e.g. the maps there, payday guns or not, ai heisters or not and etc').
 * Part of KLHook (included by klhook.c AFTER klslot.c / klbotfill.c / kllobby.c); DATA writes only (ini, our own variables), SHIP and TEST alike.
 *
 * WHY NOT A LOBBY-SCREEN ROW: the FA lobby rows are CODE focus rows of MercsFASelectorFALobby with clamps as immediates (re\lobby_options.md); a
 * further row needs new menu elements (about 4 table entries each) and the frontend table has about 10 free on a gamepad. The options are
 * therefore the 'Mod settings' window (opt-in rows, mkoverlay.py [HostOpts] Menu=1) and two hotkeys (F7, F8) that work in the lobby too.
 *
 * OPTIONS (host's own values, persisted in KLHook.ini; changed live):
 *   Map set      0 Dog Days (stock page) / 1 Dead Men FA maps (page 2) / 2 Mixed random   -> [Expansion] OnlineSet = 0 / 2 / 9
 *   AI heisters  [Bots] OnlineFill (klbotfill.c's klbf_on / klbf_sq, live)
 *   Solo start   [Lobby] Solo (kllobby.c's kllb_solo, live; implies MinPlayers 1)
 *   PD2 guns     [ShopPage] Enable (klshoppage.c reads it at START only: takes effect at the next start)
 * HOST -> CLIENTS (the map set only; the other options act on the host's machine): the string "m<set>a<ai>s<solo>" (set = the OnlineSet value)
 *   - Steam lobby data key klx_opts (needs klmm.c's proxy: [HostOpts] Enable=1 installs it; written by the HOST every 5 s and on a change,
 *     read by the CLIENT every 1 s; the lobby id is the one kls_rand_pick reads: service +0x35c exists byte, +0x35e id),
 *   - UDP broadcast on port 27413 ("KLHO1;m2a1s0") every 2 s from the host: for System Link, which has no Steam lobby (SL3b: exists 0).
 *   The CLIENT applies the host's map set to kls_online_set IN MEMORY ONLY (its own ini is never written) while it is in the session as a client
 *   (session [0x168e598]+0x54 == 3); when the session ends its own value is back. Old builds / Enable=0 send nothing and ignore everything.
 * GUESS: role 2 = host, 3 = client (klserver.c reads +0x54 the same way); a peer that hears a UDP packet but is not a client ignores it.
 *
 * [HostOpts] Enable=0 (recommended on after the live test) / Steam=1 / Udp=1 / Keys=1 / KeyMap=0x76 (F7: cycles the map set) / KeyAI=0x77 (F8: AI heisters).
 */
#ifndef KLHOSTOPT_C
#define KLHOSTOPT_C

static struct {
    int on, steam, udp, keys, keyMap, keyAI;
    int map, ai, solo, pd2;               /* the host's OWN values: map = OnlineSet value (0/2/9) */
    int minIni, squadsIni;                /* the ini's [Lobby] MinPlayers / [Bots] OnlineFillSquads, to put back */
    int rmap, rai, rsolo, rok;            /* the host's values as a client heard them */
    DWORD rat;
    int applied;                          /* what kls_online_set holds because of us: -1 = own */
    char last[24]; DWORD sentAt, steamAt, readAt, udpAt; unsigned __int64 lobby;
    UINT_PTR sock; int sockTried;
    int lastRole;
} klho;

static const int klho_maps[3] = { 0, 2, 9 };

static int klho_get(int which)
{   /* which 0 = map row (index 0..2), 1 = options row (bit 0 AI, bit 1 Solo, bit 2 PD2) */
    int i;
    if (which == 0) { for (i = 0; i < 3; i++) if (klho_maps[i] == klho.map) return i; return klho.map ? 1 : 0; }
    return (klho.ai ? 1 : 0) | (klho.solo ? 2 : 0) | (klho.pd2 ? 4 : 0);
}

static void klho_pack(char *o, size_t n) { snprintf(o, n, "m%da%ds%d", klho.map, klho.ai, klho.solo); }

static void klho_live(void)
{   /* the host's own values into the live variables of the parts */
    int wantmin;
    klbf_on = klho.ai != 0;
    klbf_sq = klho.ai && klho.squadsIni;
    kllb_solo = klho.solo != 0;
    wantmin = klho.minIni; if (klho.ai || klho.solo) wantmin = 1;
    if (GetPrivateProfileIntA("Server", "Enable", 0, klh_ini)) wantmin = 1;
    kllb_min = wantmin;
}

static void klho_put(int which, int value)
{
    char v[16];
    if (which == 0) {
        int m = klho_maps[value < 0 ? 0 : value > 2 ? 2 : value];
        if (m == klho.map) return;
        klho.map = m; kls_online_set = m; klho.applied = -1; snprintf(v, sizeof v, "%d", m); WritePrivateProfileStringA("Expansion", "OnlineSet", v, klh_ini);
        klog("hostopts: set map set = %d (%s) - [Expansion] OnlineSet=%d", value, value == 0 ? "Dog Days" : value == 1 ? "Dead Men" : "mixed random", m);
    } else {
        int ai = value & 1, so = (value >> 1) & 1, pd = (value >> 2) & 1;
        if (ai == klho.ai && so == klho.solo && pd == klho.pd2) return;
        if (pd != klho.pd2) { WritePrivateProfileStringA("ShopPage", "Enable", pd ? "1" : "0", klh_ini); klog("hostopts: set PD2 guns = %d - [ShopPage] Enable=%d (next start)", pd, pd); }
        if (ai != klho.ai) { WritePrivateProfileStringA("Bots", "OnlineFill", ai ? "1" : "0", klh_ini); klog("hostopts: set AI heisters = %d - [Bots] OnlineFill=%d (live)", ai, ai); }
        if (so != klho.solo) { WritePrivateProfileStringA("Lobby", "Solo", so ? "1" : "0", klh_ini); klog("hostopts: set Solo start = %d - [Lobby] Solo=%d (live)", so, so); }
        klho.ai = ai; klho.solo = so; klho.pd2 = pd;
        klho_live();
    }
    klho.sentAt = 0; klho.steamAt = 0;                 /* send the change at once */
}

/* ---- UDP via ws2_32, looked up (the hook links no winsock; a winsock.h would clash with windows.h) ---- */
typedef struct { short fam; unsigned short port; unsigned long addr; char zero[8]; } klho_sin;
static int (WINAPI *klho_WSAStartup)(WORD, void *);
static UINT_PTR (WINAPI *klho_socket)(int, int, int);
static int (WINAPI *klho_setsockopt)(UINT_PTR, int, int, const char *, int);
static int (WINAPI *klho_bind)(UINT_PTR, const void *, int);
static int (WINAPI *klho_sendto)(UINT_PTR, const char *, int, int, const void *, int);
static int (WINAPI *klho_recvfrom)(UINT_PTR, char *, int, int, void *, int *);
static int (WINAPI *klho_ioctl)(UINT_PTR, long, unsigned long *);
#define KLHO_PORT 27413

static void klho_open(void)
{
    HMODULE m; BYTE wsa[600]; klho_sin a; int one = 1; unsigned long nb = 1;
    if (klho.sock || klho.sockTried) return;
    klho.sockTried = 1;
    if (!(m = LoadLibraryA("ws2_32.dll"))) { klog("hostopts: ws2_32 not loadable: no LAN transport"); return; }
    klho_WSAStartup = (int (WINAPI *)(WORD, void *))GetProcAddress(m, "WSAStartup"); klho_socket = (UINT_PTR (WINAPI *)(int, int, int))GetProcAddress(m, "socket");
    klho_setsockopt = (int (WINAPI *)(UINT_PTR, int, int, const char *, int))GetProcAddress(m, "setsockopt"); klho_bind = (int (WINAPI *)(UINT_PTR, const void *, int))GetProcAddress(m, "bind");
    klho_sendto = (int (WINAPI *)(UINT_PTR, const char *, int, int, const void *, int))GetProcAddress(m, "sendto");
    klho_recvfrom = (int (WINAPI *)(UINT_PTR, char *, int, int, void *, int *))GetProcAddress(m, "recvfrom"); klho_ioctl = (int (WINAPI *)(UINT_PTR, long, unsigned long *))GetProcAddress(m, "ioctlsocket");
    if (!klho_WSAStartup || !klho_socket || !klho_setsockopt || !klho_bind || !klho_sendto || !klho_recvfrom || !klho_ioctl) { klog("hostopts: ws2_32 functions missing: no LAN transport"); return; }
    if (klho_WSAStartup(0x0202, wsa)) { klog("hostopts: WSAStartup failed: no LAN transport"); return; }
    klho.sock = klho_socket(2, 2, 17);
    if (klho.sock == (UINT_PTR)~0) { klho.sock = 0; klog("hostopts: socket() failed: no LAN transport"); return; }
    klho_setsockopt(klho.sock, 0xffff, 0x0004 /* SO_REUSEADDR */, (const char *)&one, 4);
    klho_setsockopt(klho.sock, 0xffff, 0x0020 /* SO_BROADCAST */, (const char *)&one, 4);
    klho_ioctl(klho.sock, (long)0x8004667E /* FIONBIO */, &nb);
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLHO_PORT & 0xff) << 8) | (KLHO_PORT >> 8)); a.addr = 0;
    if (klho_bind(klho.sock, &a, sizeof a)) { klog("hostopts: bind to UDP %d failed (a second game on this PC?): send only", KLHO_PORT); }
    else klog("hostopts: UDP %d open (broadcast + listen)", KLHO_PORT);
}

static int klho_parse(const char *s, int *m, int *a, int *so)
{   /* "m<set>a<ai>s<solo>" */
    int p = 0;
    if (sscanf(s, "m%da%ds%d%n", m, a, so, &p) != 3 || p < 6) return 0;
    if (*m != 0 && *m != 2 && *m != 3 && *m != 9) return 0;
    return 1;
}

static void klho_tick(int game_thread)
{
    static DWORD keyAt; static int dMap, dAI;
    DWORD now = GetTickCount(), sm = 0, role = 0; int online, host, cli;
    char cur[24];
    if (!klho.on || !game_thread || !klh_exe_ok) return;
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION));
    online = kls_online_cached();
    if (sm && online) klh_rd(sm + 0x54, &role, 4);
    host = online && role == 2; cli = online && role == 3;
    if (klho.keys && now - keyAt >= 30) {                                  /* edge-detected hotkeys, window in front, not as a client */
        static SHORT (WINAPI *gaks)(int); static HWND (WINAPI *fgw)(void); static DWORD (WINAPI *wtp)(HWND, LPDWORD); static BOOL (WINAPI *bp)(DWORD, DWORD); static int looked;
        keyAt = now;
        if (!looked) {
            HMODULE u = GetModuleHandleA("user32.dll"), k = GetModuleHandleA("kernel32.dll"); looked = 1;
            if (u) { gaks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
            if (k) bp = (BOOL (WINAPI *)(DWORD, DWORD))GetProcAddress(k, "Beep");
        }
        if (gaks && fgw && wtp && !cli) {
            DWORD pid = 0; HWND f = fgw(); int m = (gaks(klho.keyMap) & 0x8000) != 0, a = (gaks(klho.keyAI) & 0x8000) != 0;
            if (f) wtp(f, &pid);
            if (pid == GetCurrentProcessId()) {
                if (m && !dMap) { klho_put(0, (klho_get(0) + 1) % 3); if (bp) bp(660 + 220 * klho_get(0), 40); }
                if (a && !dAI) { klho_put(1, klho_get(1) ^ 1); if (bp) bp(klho.ai ? 880 : 440, 40); }
            }
            dMap = m; dAI = a;
        }
    }
    if (!host && !cli) {
        if (klho.lastRole) {
            klho.lastRole = 0; klho.rok = 0; klho.lobby = 0; klho.last[0] = 0;
            if (klho.applied >= 0) { kls_online_set = klho.map; klho.applied = -1; klog("hostopts: session over: own map set %d is back", klho.map); }
        }
        return;
    }
    if (klho.lastRole != (int)role) { klog("hostopts: session role %lu (%s)", (unsigned long)role, host ? "HOST" : "CLIENT"); klho.lastRole = (int)role; }
    {   /* the Steam lobby id (service +0x35c exists, +0x35e id) */
        DWORD svc = klh_rd32(sm + 0x17c), lob[2] = { 0, 0 }; BYTE ex = 0;
        if (svc && klh_rd(svc + 0x35c, &ex, 1) && ex && klh_rd(svc + 0x35e, lob, 8)) klho.lobby = (unsigned __int64)lob[1] << 32 | lob[0]; else klho.lobby = 0;
    }
    if (klho.udp) klho_open();
    if (host) {
        klho_pack(cur, sizeof cur);
        if (klho.udp && klho.sock && now - klho.sentAt >= 2000) {
            char pk[40]; klho_sin a; int n = snprintf(pk, sizeof pk, "KLHO1;%s", cur);
            klho.sentAt = now;
            memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLHO_PORT & 0xff) << 8) | (KLHO_PORT >> 8)); a.addr = 0xffffffffu;
            n = klho_sendto(klho.sock, pk, n, 0, &a, sizeof a);
            if (strcmp(cur, klho.last)) klog("hostopts: HOST broadcast on UDP %d: %s (sendto %d)", KLHO_PORT, cur, n);
        }
        if (klho.steam && klmm_real && klho.lobby && (strcmp(cur, klho.last) || now - klho.steamAt >= 5000)) {
            char r = ((char (__fastcall *)(void *, void *, unsigned __int64, const char *, const char *))KLMM_REAL(19))(klmm_real, 0, klho.lobby, "klx_opts", cur);
            if (strcmp(cur, klho.last)) klog("hostopts: HOST Steam lobby %08lx%08lx klx_opts=%s (ok=%d)", (unsigned long)(klho.lobby >> 32), (unsigned long)klho.lobby, cur, r != 0);
            klho.steamAt = now;
        }
        strcpy(klho.last, cur);
        if (klho.applied >= 0) { kls_online_set = klho.map; klho.applied = -1; }
        return;
    }
    /* CLIENT: UDP first, then the Steam lobby */
    if (klho.udp && klho.sock) {
        char pk[64]; klho_sin from; int fl, n, m, a, s, k;
        for (k = 0; k < 8; k++) {
            fl = sizeof from; n = klho_recvfrom(klho.sock, pk, sizeof pk - 1, 0, &from, &fl);
            if (n <= 0) break;
            pk[n] = 0;
            if (!strncmp(pk, "KLHO1;", 6) && klho_parse(pk + 6, &m, &a, &s)) {
                if (!klho.rok || m != klho.rmap) klog("hostopts: CLIENT heard the host on UDP: %s", pk + 6);
                klho.rmap = m; klho.rai = a; klho.rsolo = s; klho.rok = 1; klho.rat = now;
            }
        }
    }
    if (klho.steam && klmm_real && klho.lobby && now - klho.readAt >= 1000) {
        const char *v = ((const char *(__fastcall *)(void *, void *, unsigned __int64, const char *))KLMM_REAL(18))(klmm_real, 0, klho.lobby, "klx_opts");
        char b[24]; int m, a, s;
        klho.readAt = now;
        if (v && klh_rdstr((DWORD_PTR)v, b, sizeof b) && klho_parse(b, &m, &a, &s)) {
            if (!klho.rok || m != klho.rmap) klog("hostopts: CLIENT read the host's Steam lobby klx_opts=%s", b);
            klho.rmap = m; klho.rai = a; klho.rsolo = s; klho.rok = 1; klho.rat = now;
        }
    }
    if (klho.rok && klho.applied != klho.rmap) {
        klog("hostopts: CLIENT applies the host's map set %d (own %d), in memory only; kls_online_set %d -> %d", klho.rmap, klho.map, kls_online_set, klho.rmap);
        kls_online_set = klho.rmap; klho.applied = klho.rmap;
    }
}

static void klho_init(void)
{
    klho.on = GetPrivateProfileIntA("HostOpts", "Enable", 0, klh_ini) != 0;
    klho.applied = -1;
    if (!klho.on) return;
    klho.steam = GetPrivateProfileIntA("HostOpts", "Steam", 1, klh_ini) != 0;
    klho.udp = GetPrivateProfileIntA("HostOpts", "Udp", 1, klh_ini) != 0;
    klho.keys = GetPrivateProfileIntA("HostOpts", "Keys", 1, klh_ini) != 0;
    klho.keyMap = (int)GetPrivateProfileIntA("HostOpts", "KeyMap", 0x76, klh_ini);
    klho.keyAI = (int)GetPrivateProfileIntA("HostOpts", "KeyAI", 0x77, klh_ini);
    klho.map = kls_online_set; if (klho.map != 0 && klho.map != 2 && klho.map != 9) klho.map = klho.map == 3 ? 3 : 0;
    klho.ai = GetPrivateProfileIntA("Bots", "OnlineFill", 0, klh_ini) != 0;
    klho.solo = GetPrivateProfileIntA("Lobby", "Solo", 0, klh_ini) != 0;
    klho.pd2 = GetPrivateProfileIntA("ShopPage", "Enable", 0, klh_ini) != 0;
    klho.minIni = GetPrivateProfileIntA("Lobby", "MinPlayers", 0, klh_ini);
    if (klho.minIni < 0 || klho.minIni > 8) klho.minIni = 0;
    klho.squadsIni = GetPrivateProfileIntA("Bots", "OnlineFillSquads", 0, klh_ini) != 0;
    klog("hostopts: on; map set %d, AI heisters %d, Solo %d, PD2 guns %d; Steam=%d Udp=%d Keys=%d (F7 map, F8 AI); the host's map set reaches clients as klx_opts", klho.map, klho.ai, klho.solo, klho.pd2, klho.steam, klho.udp, klho.keys);
}

#endif
