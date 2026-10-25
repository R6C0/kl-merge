/*
 * klcharonline.c - [CharOnline] EVERY PLAYER'S HEISTER / MASK / OUTFIT ON EVERY SCREEN (2026-10-25; owner: 'make sure the player models transfer
 * over too or add an option for people to select either in game or at the menu like in arcade').
 * Part of KLHook (included by klhook.c AFTER klchar.c / klmm.c / klhostopt.c); SHIP and TEST alike. Data/heap writes and the same two game calls klchar.c
 * makes (0x783fb0 model, 0x88c810 variant) on the game's own thread; no code byte of kl2.exe changes. Default OFF: NOT RUN LIVE.
 *
 * 1. HOW THE STOCK GAME PICKS AN ONLINE PLAYER'S MODEL (read 2026-10-25 from kl2.exe, disassembly of 0x74ee10; re/char_online.md)
 *    There is NO model choice on the wire. Slot 137 of the Sv / Cl rules (0x74ee10, arg = ENTITY TABLE INDEX bl) does
 *        ent   = [[0x6161c0(session)] + 12 * bl + 4]          the session's player table (12-byte entries, ZFFPlayer* at +4)
 *        n     = 0x817160(session, 0x8e8010(8))               the client's SESSION NUMBER (virtual: [[session+4]->vtbl+0x3c]); >= 8 or -1 -> 7
 *        model = rules->vtbl[0x220](2, n)                     GetHero(2, n) = the Heist hero table entry n
 *        ent->0x783fb0(model)                                 [[ent+4]+0x68] = model; rebuild
 *    so every machine runs the same code and gets the same body for the same seat: the body is a function of the SEAT NUMBER, and the seat
 *    number is handed out by the host (join order). Nothing carries a "variant" or "character" per player; the variant byte ([ent+0x50], 0x88c810)
 *    is set locally from the option UseMask. => The cheapest honest route is the one klchar.c already uses on the local player: call the game's
 *    own 0x783fb0 / 0x88c810 on the entity. What is missing is only WHO WEARS WHAT on the other machines, which is what this part transports.
 *
 * 2. THE KEY: the ENTITY TABLE INDEX (the same number on every peer)
 *    The table index is the argument slot 137 gets, it is the order of the level's ZFFPlayer entities (scene data: identical on every peer that loaded the
 *    same level), and the local player's entity is [gamedata+0x828+4*[gamedata+0x898]] (klfed.c klp_read), found in the table by pointer. So a peer says
 *    "MY BODY IS ENTITY i: character c, mask m, outfit o" and every other peer applies c/m/o to table[i]. No Steam id -> client -> player index chain
 *    is needed (that chain, re/pm_options.md 8.2, stays NOT ESTABLISHED and is not used). GUESS: the local player pointer is the same slot online
 *    (probe line 'charonline: my body'); a heister is type [ent+0x273c] == 2, policemen (3) are never touched or published.
 * 3. TRANSPORT (the pattern of klhostopt.c, per player)
 *    - Steam lobby MEMBER data, key klx_look = "i<idx>c<c>m<m>o<o>" (ISteamMatchmaking008 slot 24 SetLobbyMemberData, 23 GetLobbyMemberData, 16 / 17
 *      GetNumLobbyMembers / GetLobbyMemberByIndex; needs klmm.c's proxy: [CharOnline] Enable=1 + Steam=1 installs it). Written on a change and every 5 s;
 *      all members read every 1 s. GUESS: SDK 008 slot numbers (the proxy already relies on 12 / 18 / 19 of the same table).
 *    - UDP broadcast "KLCH1;i;c;m;o" on port 27414 every 2 s from EVERY peer (System Link has no Steam lobby), all listen; own packets are recognised by the
 *      entity index and ignored. Entries from UDP expire after 7 s, Steam ones when the member's value is gone.
 *    A peer without the mod sends nothing: its body stays stock. A peer without the asset (no KLWardrobe.ini for the level, a character the wardrobe lacks)
 *    ignores the entry, said once.
 * 4. APPLYING (every 250 ms, game thread, after Settle ms of a stable table): for the own entity and every entity a peer announced: model by 0x783fb0 when
 *    [[ent+4]+0x68] differs from the character's wardrobe root; variant by 0x88c810 (klc_variant, the formula of klchar.c). At most Tries calls per entity per 10 s
 *    (a new round re-runs slot 137 and puts the stock model back: it is applied again). Both code heads are compared first (klchar.c's checks).
 * 5. CHOOSING (before or during a match): the choice IS klchar.c's KLChar / KLMask / KLOutfit, so Options > Match options / the Heister page (stored in
 *    KLHook.ini [Character]) work before the match; hotkeys work in the lobby and in the match (game window in front): F9 next character (Shift: previous),
 *    F11 next mask, Ctrl+F11 next outfit; a beep and the log say what was chosen; every press is written to [Character].
 *
 * KLHook.ini
 *   [CharOnline]
 *   Enable=0   (recommended on after the live test)   Steam=1   Udp=1   Keys=1   KeyChar=0x78 (F9)   KeyMask=0x7A (F11, Ctrl = outfit)
 *   Settle=1500  ms the table must have stood still before a body is changed        Tries=3  calls per entity per 10 s     Log=1
 *   TEST build only: TestPeer=<idx>  TestChar=<c> TestMask=<m> TestOutfit=<o>   pretends peer <idx> announced that (proves the apply on another body)
 */
#ifndef KLCHARONLINE_C
#define KLCHARONLINE_C

#define KLCO_PORT   27414
#define KLCO_N      32
#define KLCO_GETHERO_TABLE 0x006161c0

struct klco_peer { int used, src; int c, m, o; DWORD at; };
static struct {
    int on, steam, udp, keys, log, settle, tries, keyChar, keyMask;
    int testPeer, testChar, testMask, testOutfit;
    struct klco_peer p[KLCO_N];
    DWORD tick, steamSet, steamGet, udpSend, since, tbl, ownEnt;
    int ownIdx, pubIdx, pubC, pubM, pubO, pubWas;
    char pubStr[40];
    unsigned __int64 lobby;
    UINT_PTR sock; int sockTried, toldOwn, toldNoWar, toldCode, toldOnline;
    DWORD triedAt[KLCO_N]; int tried[KLCO_N]; LONG lastv[KLCO_N]; DWORD lastmodel[KLCO_N];
} klco;

static const char *const klco_names[17] = { "stock", "J.C.", "Tommy", "Pierre", "Liam", "Jean", "Elwood", "Bud", "Mitchel", "Kane", "Lynch", "Ashkanan", "Meldal", "Red", "Parker", "Standen", "Hutchison" };

/* ---- UDP via ws2_32, looked up (own socket on its own port: klhostopt.c's is bound to 27413) ---- */
typedef struct { short fam; unsigned short port; unsigned long addr; char zero[8]; } klco_sin;
static int (WINAPI *klco_WSAStartup)(WORD, void *);
static UINT_PTR (WINAPI *klco_socket)(int, int, int);
static int (WINAPI *klco_setsockopt)(UINT_PTR, int, int, const char *, int);
static int (WINAPI *klco_bind)(UINT_PTR, const void *, int);
static int (WINAPI *klco_sendto)(UINT_PTR, const char *, int, int, const void *, int);
static int (WINAPI *klco_recvfrom)(UINT_PTR, char *, int, int, void *, int *);
static int (WINAPI *klco_ioctl)(UINT_PTR, long, unsigned long *);

static void klco_open(void)
{
    HMODULE m; BYTE wsa[600]; klco_sin a; int one = 1; unsigned long nb = 1;
    if (klco.sock || klco.sockTried) return;
    klco.sockTried = 1;
    if (!(m = LoadLibraryA("ws2_32.dll"))) { klog("charonline: ws2_32 not loadable: no LAN transport"); return; }
    klco_WSAStartup = (int (WINAPI *)(WORD, void *))GetProcAddress(m, "WSAStartup"); klco_socket = (UINT_PTR (WINAPI *)(int, int, int))GetProcAddress(m, "socket");
    klco_setsockopt = (int (WINAPI *)(UINT_PTR, int, int, const char *, int))GetProcAddress(m, "setsockopt"); klco_bind = (int (WINAPI *)(UINT_PTR, const void *, int))GetProcAddress(m, "bind");
    klco_sendto = (int (WINAPI *)(UINT_PTR, const char *, int, int, const void *, int))GetProcAddress(m, "sendto");
    klco_recvfrom = (int (WINAPI *)(UINT_PTR, char *, int, int, void *, int *))GetProcAddress(m, "recvfrom"); klco_ioctl = (int (WINAPI *)(UINT_PTR, long, unsigned long *))GetProcAddress(m, "ioctlsocket");
    if (!klco_WSAStartup || !klco_socket || !klco_setsockopt || !klco_bind || !klco_sendto || !klco_recvfrom || !klco_ioctl) { klog("charonline: ws2_32 functions missing: no LAN transport"); return; }
    if (klco_WSAStartup(0x0202, wsa)) { klog("charonline: WSAStartup failed: no LAN transport"); return; }
    klco.sock = klco_socket(2, 2, 17);
    if (klco.sock == (UINT_PTR)~0) { klco.sock = 0; klog("charonline: socket() failed: no LAN transport"); return; }
    klco_setsockopt(klco.sock, 0xffff, 0x0004 /* SO_REUSEADDR */, (const char *)&one, 4);
    klco_setsockopt(klco.sock, 0xffff, 0x0020 /* SO_BROADCAST */, (const char *)&one, 4);
    klco_ioctl(klco.sock, (long)0x8004667E /* FIONBIO */, &nb);
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLCO_PORT & 0xff) << 8) | (KLCO_PORT >> 8)); a.addr = 0;
    if (klco_bind(klco.sock, &a, sizeof a)) klog("charonline: bind to UDP %d failed (a second game on this PC?): send only", KLCO_PORT);
    else klog("charonline: UDP %d open (every peer broadcasts its own look and listens)", KLCO_PORT);
}

static int klco_parse(const char *s, int *i, int *c, int *m, int *o)
{   /* "i<idx>c<c>m<m>o<o>" */
    int p = 0;
    if (sscanf(s, "i%dc%dm%do%d%n", i, c, m, o, &p) != 4 || p < 8) return 0;
    if (*i < 0 || *i >= KLCO_N || *c < 0 || *c > KLC_NCHAR || *m < 0 || *m > KLC_MASKS + 1 || *o < 0 || *o >= KLC_OUTFITS) return 0;
    return 1;
}

static const char *klco_nm(int c) { return c >= 0 && c <= 16 ? klco_names[c] : "?"; }

static void klco_heard(int idx, int c, int m, int o, int src, DWORD now)
{
    struct klco_peer *p = &klco.p[idx];
    if (idx == klco.ownIdx) {                                          /* our own broadcast / member data coming back */
        static int told[3];
        if (!told[src]++ && klco.log) klog("charonline: heard OWN announcement back via %s (entity %d, %s): ignored - the transport works", src == 1 ? "Steam lobby" : "UDP", idx, klco_nm(c));
        return;
    }
    if (!p->used || p->c != c || p->m != m || p->o != o)
        klog("charonline: heard peer on entity %d chose %s (char %d) mask %d outfit %d via %s", idx, klco_nm(c), c, m, o, src == 1 ? "Steam lobby" : "UDP");
    p->used = 1; p->src = src; p->c = c; p->m = m; p->o = o; p->at = now;
}

/* ---- the session's player table and the own body ---- */
static int klco_table(DWORD sm, DWORD *ents, int *n)
{
    DWORD tbl, e; int cnt = 0, i;
    if (!sm || !klh_rd32(sm + 4)) return 0;
    tbl = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLCO_GETHERO_TABLE))((void *)(DWORD_PTR)sm, 0);      /* the game's own accessor (0x74ee24) */
    if (!tbl || !(e = klh_rd32(tbl))) return 0;
    for (i = 0; i < 16; i++) { DWORD pl = klh_rd32(e + 12 * i + 4); if (!pl || klh_rd32(pl) != 0x00bb45f4) break; cnt++; }
    if (!cnt) return 0;
    *ents = e; *n = cnt; klco.tbl = tbl;
    return 1;
}

static DWORD klco_ent(DWORD ents, int n, int i) { return i >= 0 && i < n ? klh_rd32(ents + 12 * i + 4) : 0; }

static int klco_heister(DWORD ent)
{   /* type 2 and not busy: the conditions slot 137 and klchar.c use */
    BYTE type = 0, busy = 1;
    return ent && klh_rd(ent + 0x273c, &type, 1) && type == 2 && klh_rd(ent + 0x2723, &busy, 1) && !busy && klh_rd32(ent + 4);
}

/* ---- one body: model, then variant (klchar.c's formula) ---- */
static void klco_look(DWORD ent, int idx, int ch, int mask, int outfit, int gt, const char *who, DWORD now)
{
    static const BYTE model_code[14] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x57, 0x8b, 0x7e, 0x04, 0x50, 0x8b, 0xcf };
    static const BYTE variant_code[10] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x89, 0x46, 0x50 };
    DWORD node, model, cur = 0, want_root = 0; char key[64], scene[160]; int wardrobe, i, v;
    if (!ch && !mask && !outfit) return;
    if (!(node = klh_rd32(ent + 4)) || !(model = klh_rd32(node + 0x68))) return;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    wardrobe = klc_w.on && !_stricmp(key, klc_w.key);
    if (!klc_same_code(0x783fb0, model_code, sizeof model_code) || !klc_same_code(KLC_SETVARIANT, variant_code, sizeof variant_code)) {
        if (!klco.toldCode++) klog("charonline: the two game routines are not the ones this build knows: nothing is changed");
        return;
    }
    if (ch >= 1) {
        if (wardrobe && ch <= klc_w.n && klc_w.c[ch - 1].root && (ch <= 8 || !klc_w.c[ch - 1].stock)) want_root = klc_w.c[ch - 1].root;
        else if (!klco.toldNoWar++) klog("charonline: %s wants %s (char %d) and level %s has no such model (wardrobe %s): the stock body stays", who, klco_nm(ch), ch, key, wardrobe ? "has no entry" : "missing");
    }
    if (want_root && model != want_root) {
        if (now - klco.triedAt[idx] > 10000) { klco.triedAt[idx] = now; klco.tried[idx] = 0; }
        if (!gt) return;
        if (klco.tried[idx] < klco.tries) {
            klco.tried[idx]++;
            ((void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(0x783fb0))((void *)(DWORD_PTR)ent, 0, want_root);
            cur = klh_rd32(node + 0x68);
            klog("charonline: applied to body: %s on entity %d (%08lx): model %lu -> %lu asked (%s, try %d): now %lu%s", who, idx, ent, model, want_root, klco_nm(ch), klco.tried[idx], cur, cur == want_root ? "" : " - NOT taken");
            model = cur;
        }
    }
    /* mask and outfit: the variant of the model the body wears now */
    if (!wardrobe) { if (!mask) return; v = mask == 1 ? 1 : 2; }
    else {
        for (i = 0; i < klc_w.n && klc_w.c[i].root != model; i++) ;
        if (i == klc_w.n) return;
        if (!klh_rd(ent + 0x50, &cur, 4)) return;
        if (mask >= 2 && mask - 1 > klc_w.masks) mask = 1;
        v = klc_variant(klc_w.version, klc_w.step, klc_w.headbase, klc_w.c[i].bodies, klc_w.c[i].heads, outfit, mask, cur);
    }
    if (!klh_rd(ent + 0x50, &cur, 4) || cur == (DWORD)v) return;
    if (!gt) return;
    ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLC_SETVARIANT))((void *)(DWORD_PTR)ent, 0, v);
    if (InterlockedExchange(&klco.lastv[idx], v) != v) klog("charonline: applied to body: %s on entity %d: variant %lu -> %d (mask %d, outfit %d) on model %lu", who, idx, cur, v, mask, outfit, model);
}

/* ---- hotkeys: the choice, in the lobby and in the match ---- */
static void klco_keys(DWORD now)
{
    static DWORD keyAt; static int dC, dM;
    static SHORT (WINAPI *gaks)(int); static HWND (WINAPI *fgw)(void); static DWORD (WINAPI *wtp)(HWND, LPDWORD); static BOOL (WINAPI *bp)(DWORD, DWORD); static int looked;
    DWORD pid = 0; HWND f; int c, m, shift, ctrl;
    if (now - keyAt < 30) return;
    keyAt = now;
    if (!looked) {
        HMODULE u = GetModuleHandleA("user32.dll"), k = GetModuleHandleA("kernel32.dll"); looked = 1;
        if (u) { gaks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
        if (k) bp = (BOOL (WINAPI *)(DWORD, DWORD))GetProcAddress(k, "Beep");
    }
    if (!gaks || !fgw || !wtp) return;
    f = fgw(); if (f) wtp(f, &pid);
    c = klco.keyChar && (gaks(klco.keyChar) & 0x8000) != 0; m = klco.keyMask && (gaks(klco.keyMask) & 0x8000) != 0;
    shift = (gaks(0x10) & 0x8000) != 0; ctrl = (gaks(0x11) & 0x8000) != 0;
    if (pid == GetCurrentProcessId()) {
        int which = -1, step = 1;
        if (c && !dC) { which = 0; step = shift ? -1 : 1; }
        else if (m && !dM) which = ctrl ? 2 : 1;
        if (which >= 0) {
            int span = which == 0 ? KLC_NCHAR + 1 : which == 1 ? KLC_MASKS + 2 : KLC_OUTFITS;
            int v = (int)*klc_value[which] + step; char s[16];
            v = ((v % span) + span) % span;
            InterlockedExchange(klc_value[which], v);
            snprintf(s, sizeof s, "%d", v); WritePrivateProfileStringA("Character", klc_keys[which], s, klh_ini);
            klog("charonline: I chose %s = %d (key press; written to [Character] %s=%d)", klc_names[which], v, klc_keys[which], v);
            if (which == 0) klog("charonline: I chose heister %s", klco_nm(v));
            if (bp) bp(500 + 40 * (which * 6 + v), 40);
        }
    }
    dC = c; dM = m;
}

static void klco_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, ents = 0, role = 0; int n = 0, i, online;
    if (!klco.on || !klc_on || !game_thread || !klh_exe_ok) return;
    online = kls_online_cached();
    if (online && klco.keys) klco_keys(now);
    if (now - klco.tick < 250) return;
    klco.tick = now;
    if (!online) {
        if (klco.toldOnline) { klco.toldOnline = 0; memset(klco.p, 0, sizeof klco.p); klco.ownIdx = -1; klco.pubStr[0] = 0; klco.lobby = 0; klog("charonline: session over: peer looks forgotten"); }
        return;
    }
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION)))) return;
    klh_rd(sm + 0x54, &role, 4);
    if (!klco.toldOnline) { klco.toldOnline = 1; klco.ownIdx = -1; klog("charonline: network session (role %lu): my choice is %s mask %ld outfit %ld", (unsigned long)role, klco_nm((int)klc_char), (long)klc_mask, (long)klc_outfit); }
    {   /* the Steam lobby id (service +0x35c exists, +0x35e id: klhostopt.c) */
        DWORD svc = klh_rd32(sm + 0x17c), lob[2] = { 0, 0 }; BYTE ex = 0;
        if (svc && klh_rd(svc + 0x35c, &ex, 1) && ex && klh_rd(svc + 0x35e, lob, 8)) klco.lobby = (unsigned __int64)lob[1] << 32 | lob[0]; else klco.lobby = 0;
    }
    if (klco.udp) klco_open();
    if (!klco_table(sm, &ents, &n)) { klco.since = 0; return; }
    {   /* the own body: the local player's entity, found in the table */
        DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), pl = 0; BYTE sel = 0xff; int idx = -1;
        if (gd && klh_rd(gd + 0x898, &sel, 1) && sel < 28) pl = klh_rd32(gd + 0x828 + 4 * sel);
        for (i = 0; pl && i < n; i++) if (klco_ent(ents, n, i) == pl) idx = i;
        if (idx != klco.ownIdx || pl != klco.ownEnt) {
            BYTE type = 0; if (pl) klh_rd(pl + 0x273c, &type, 1);
            klog("charonline: my body: entity %d of %d (%08lx, type %u)%s", idx, n, pl, type, idx < 0 ? " - NOT in the player table: nothing is sent or applied for me" : "");
            klco.ownIdx = idx; klco.ownEnt = pl; klco.since = now; klco.pubStr[0] = 0;
            memset(klco.p, 0, sizeof klco.p);                         /* a new body = a new round: what peers said before may be about other seats */
        }
    }
    if (!klco.since) klco.since = now;
    /* ---- publish my own look (only while I am a heister) */
    if (klco.ownIdx >= 0 && klco_heister(klco.ownEnt) && (klc_char || klc_mask || klc_outfit || klco.pubWas)) {
        char cur[40]; int fresh;
        snprintf(cur, sizeof cur, "i%dc%ldm%ldo%ld", klco.ownIdx, (long)klc_char, (long)klc_mask, (long)klc_outfit);
        fresh = strcmp(cur, klco.pubStr) != 0;
        if (fresh) klog("charonline: %s chose %s (char %ld) mask %ld outfit %ld on entity %d: announcing", "I", klco_nm((int)klc_char), (long)klc_char, (long)klc_mask, (long)klc_outfit, klco.ownIdx);
        if (klco.udp && klco.sock && (fresh || now - klco.udpSend >= 2000)) {
            char pk[64]; klco_sin a; int len = snprintf(pk, sizeof pk, "KLCH1;%s", cur), r;
            klco.udpSend = now;
            memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLCO_PORT & 0xff) << 8) | (KLCO_PORT >> 8)); a.addr = 0xffffffffu;
            r = klco_sendto(klco.sock, pk, len, 0, &a, sizeof a);
            if (fresh) klog("charonline: sent on UDP %d: %s (sendto %d)", KLCO_PORT, cur, r);
        }
        if (klco.steam && klmm_real && klco.lobby && (fresh || now - klco.steamSet >= 5000)) {
            ((void (__fastcall *)(void *, void *, unsigned __int64, const char *, const char *))KLMM_REAL(24))(klmm_real, 0, klco.lobby, "klx_look", cur);
            if (fresh) klog("charonline: sent to the Steam lobby %08lx%08lx as member data klx_look=%s", (unsigned long)(klco.lobby >> 32), (unsigned long)klco.lobby, cur);
            klco.steamSet = now;
        }
        strcpy(klco.pubStr, cur); klco.pubWas = 1;
    }
    /* ---- listen: UDP, then every lobby member's data */
    if (klco.udp && klco.sock) {
        char pk[64]; klco_sin from; int fl, len, k, a, c, m, o;
        for (k = 0; k < 16; k++) {
            fl = sizeof from; len = klco_recvfrom(klco.sock, pk, sizeof pk - 1, 0, &from, &fl);
            if (len <= 0) break;
            pk[len] = 0;
            if (!strncmp(pk, "KLCH1;", 6) && klco_parse(pk + 6, &a, &c, &m, &o)) klco_heard(a, c, m, o, 2, now);
        }
    }
    if (klco.steam && klmm_real && klco.lobby && now - klco.steamGet >= 1000) {
        int cnt = ((int (__fastcall *)(void *, void *, unsigned __int64))KLMM_REAL(16))(klmm_real, 0, klco.lobby), mi; BYTE seen[KLCO_N];
        memset(seen, 0, sizeof seen); klco.steamGet = now;
        for (mi = 0; mi < cnt && mi < 16; mi++) {
            unsigned __int64 id = ((unsigned __int64 (__fastcall *)(void *, void *, unsigned __int64, int))KLMM_REAL(17))(klmm_real, 0, klco.lobby, mi);
            const char *v = ((const char *(__fastcall *)(void *, void *, unsigned __int64, unsigned __int64, const char *))KLMM_REAL(23))(klmm_real, 0, klco.lobby, id, "klx_look");
            char b[40]; int a, c, m, o;
            if (v && klh_rdstr((DWORD_PTR)v, b, sizeof b) && klco_parse(b, &a, &c, &m, &o)) { klco_heard(a, c, m, o, 1, now); seen[a] = 1; }
        }
        for (i = 0; i < KLCO_N; i++) if (klco.p[i].used && klco.p[i].src == 1 && !seen[i]) { klco.p[i].used = 0; klog("charonline: peer on entity %d is gone from the lobby data", i); }
    }
    for (i = 0; i < KLCO_N; i++) if (klco.p[i].used && klco.p[i].src == 2 && now - klco.p[i].at > 7000) { klco.p[i].used = 0; klog("charonline: peer on entity %d has been silent for 7 s: forgotten", i); }
#ifdef KLHOOK_TEST
    if (klco.testPeer >= 0 && klco.testPeer < n && klco.testPeer != klco.ownIdx) klco_heard(klco.testPeer, klco.testChar, klco.testMask, klco.testOutfit, 1, now), klco.p[klco.testPeer].src = 3;
#endif
    /* ---- apply: after the table has stood still for Settle ms */
    if ((LONG)(now - klco.since) < klco.settle) return;
    if (klco.ownIdx >= 0 && klco_heister(klco.ownEnt)) klco_look(klco.ownEnt, klco.ownIdx, (int)klc_char, (int)klc_mask, (int)klc_outfit, game_thread, "my body", now);
    for (i = 0; i < n; i++) if (klco.p[i].used && i != klco.ownIdx) {
        DWORD ent = klco_ent(ents, n, i);
        if (klco_heister(ent)) klco_look(ent, i, klco.p[i].c, klco.p[i].m, klco.p[i].o, game_thread, "peer", now);
    }
}

static void klco_init(void)
{
    klco.on = GetPrivateProfileIntA("CharOnline", "Enable", 0, klh_ini) != 0;
    klco.ownIdx = -1; klco.testPeer = -1;
    if (!klco.on) return;
    klco.steam = GetPrivateProfileIntA("CharOnline", "Steam", 1, klh_ini) != 0;
    klco.udp = GetPrivateProfileIntA("CharOnline", "Udp", 1, klh_ini) != 0;
    klco.keys = GetPrivateProfileIntA("CharOnline", "Keys", 1, klh_ini) != 0;
    klco.log = GetPrivateProfileIntA("CharOnline", "Log", 1, klh_ini) != 0;
    klco.settle = GetPrivateProfileIntA("CharOnline", "Settle", 1500, klh_ini);
    klco.tries = GetPrivateProfileIntA("CharOnline", "Tries", 3, klh_ini);
    klco.keyChar = (int)GetPrivateProfileIntA("CharOnline", "KeyChar", 0x78, klh_ini) & 0xff;
    klco.keyMask = (int)GetPrivateProfileIntA("CharOnline", "KeyMask", 0x7a, klh_ini) & 0xff;
    if (klco.settle < 0 || klco.settle > 20000) klco.settle = 1500;
    if (klco.tries < 1 || klco.tries > 10) klco.tries = 3;
#ifdef KLHOOK_TEST
    klco.testPeer = (int)GetPrivateProfileIntA("CharOnline", "TestPeer", -1, klh_ini);
    klco.testChar = (int)GetPrivateProfileIntA("CharOnline", "TestChar", 0, klh_ini);
    klco.testMask = (int)GetPrivateProfileIntA("CharOnline", "TestMask", 0, klh_ini);
    klco.testOutfit = (int)GetPrivateProfileIntA("CharOnline", "TestOutfit", 0, klh_ini);
#endif
    klog("charonline: on; Steam=%d Udp=%d Keys=%d (F9 char, F11 mask, Ctrl+F11 outfit) Settle=%d Tries=%d; own choice Char=%ld Mask=%ld Outfit=%ld; every peer announces its entity-table index + look", klco.steam, klco.udp, klco.keys, klco.settle, klco.tries, klc_char, klc_mask, klc_outfit);
}

#endif /* KLCHARONLINE_C */
