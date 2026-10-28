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
 *   Enable=0   (recommended on after the live test)   Unique=1 (recommended on: a character is worn once, lower entity wins)   StockHero=1 (recommended on: Dog Days heisters 1..8 get their stock body from the rules hero table on a level without a wardrobe)   ForgetMs=0 (0 = keep a peer's last look)   OwnDiag=1   Steam=1   Udp=1   Keys=1   KeyChar=0x78 (F9)   KeyMask=0x7A (F11, Ctrl = outfit)
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
    int ignoreChar;                            /* [Hire] OnlineIgnoreChar and [Hire] Enable=1: the Heister page Char= is not the online body (Arcade ignores it too) */
    int on, steam, udp, keys, log, settle, tries, keyChar, keyMask, unique, forgetMs, ownDiag;
    int testPeer, testChar, testMask, testOutfit;
    struct klco_peer p[KLCO_N];
    DWORD tick, steamSet, steamGet, udpSend, since, tbl, ownEnt, entSig, diagAt; int ownHow, toldEff[KLCO_N];
    int ownIdx, pubIdx, pubC, pubM, pubO, pubWas;
    char pubStr[40];
    unsigned __int64 lobby;
    UINT_PTR sock; int stockHero, sockTried, toldOwn, toldNoWar, toldStock, toldSrc, toldCode, toldOnline, toldFollow;
    DWORD triedAt[KLCO_N]; int tried[KLCO_N]; LONG lastv[KLCO_N]; DWORD lastmodel[KLCO_N];
    DWORD whyAt[KLCO_N];
} klco;

/* 10-27 bench Q27_DM03: the HOST heard the joiner (entity 1, Kane) and in 2.5 min never applied it, with no log line. Every silent
   'nothing done' for a heard peer now says why, at most once per 8 s per entity (Log=1). */
static void klco_why(int idx, DWORD now, const char *fmt, ...)
{
    char b[200]; va_list ap;
    if (!klco.log || idx < 0 || idx >= KLCO_N || now - klco.whyAt[idx] < 8000) return;
    klco.whyAt[idx] = now;
    va_start(ap, fmt); vsnprintf(b, sizeof b, fmt, ap); va_end(ap);
    klog("charonline: entity %d not changed: %s", idx, b);
}

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
    for (i = 0; i < 16; i++) { DWORD pl = klh_rd32(e + 12 * i + 4); if (!pl || klh_pvt(pl) != 0x00bb45f4) break; cnt++; }
    if (!cnt) return 0;
    *ents = e; *n = cnt; klco.tbl = tbl;
    return 1;
}

static DWORD klco_ent(DWORD ents, int n, int i) { return i >= 0 && i < n ? klh_rd32(ents + 12 * i + 4) : 0; }


/* ---- who is the LOCAL player's entity? (2026-10-26) ----
 * Live bench L3/L4 (2 PCs, LAN): on the CLIENT [gamedata+0x828+4*[gamedata+0x898]] (what Arcade uses) gave no entity of the session table for the whole round
 * (L4: found only after the round was over, L3: after 20 s), so the client neither announced nor applied its own look. The game's own test for 'this object
 * is mine' is 0x9425a0 (thiscall on a DDL net object R: [R+0x14] owner station == local station 0x94bc10, owner 0 = false; re/private_match.md): every
 * ZFFPlayer P has its DDL object at [P+0x274c] and R points back at [R+0x540] (re/netsmooth_solo.md). So a player entity of the table whose R passes
 * 0x9425a0 is ours. GUESS (probe log 'charonline: my body ... found by'): the offsets hold for the table's entities on a client too; the master test is
 * read-only (no write, no state). Order: the slot method (Arcade's) when it finds a table entry, else the master scan (a heister first). */
static int klco_is_master(DWORD ent)
{
    DWORD r = klh_rd32(ent + 0x274c);
    if (!r || klh_rd32(r + 0x540) != ent) return 0;
    return (((unsigned (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(0x9425a0))((void *)(DWORD_PTR)r, 0) & 0xff) != 0;
}

static int klco_find_own(DWORD ents, int n, DWORD now, DWORD *plOut, int *how)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), pl = 0; BYTE sel = 0xff; int i, idx = -1, firstMaster = -1, heisterMaster = -1;
    if (gd && klh_rd(gd + 0x898, &sel, 1) && sel < 28) pl = klh_rd32(gd + 0x828 + 4 * sel);
    for (i = 0; pl && i < n; i++) if (klco_ent(ents, n, i) == pl) idx = i;
    *plOut = pl; *how = 0;
    if (idx >= 0) { *how = 1; return idx; }
    for (i = 0; i < n; i++) {
        DWORD e = klco_ent(ents, n, i); BYTE type = 0, pol = 0;
        if (!e || !klco_is_master(e)) continue;
        if (firstMaster < 0) firstMaster = i;
        klh_rd(e + 0x273c, &type, 1); klh_rd(e + 0x2723, &pol, 1);
        if (heisterMaster < 0 && type == 2 && !pol) heisterMaster = i;
    }
    idx = heisterMaster >= 0 ? heisterMaster : firstMaster;
    if (idx >= 0) { *how = 2; *plOut = klco_ent(ents, n, idx); return idx; }
    if (klco.ownDiag && now - klco.diagAt >= 8000) {          /* not found: say what the methods saw (every 8 s) */
        char b[512]; int k, o = 0;
        klco.diagAt = now;
        for (k = 0; k < n && o < (int)sizeof b - 48; k++) {
            DWORD e = klco_ent(ents, n, k), r = e ? klh_rd32(e + 0x274c) : 0, ow = r ? klh_rd32(r + 0x14) : 0, back = r ? klh_rd32(r + 0x540) : 0; BYTE t = 0, u = 0;
            if (e) { klh_rd(e + 0x273c, &t, 1); klh_rd(e + 0x2723, &u, 1); }
            o += snprintf(b + o, sizeof b - o, " [%d t%u p%u R%lx o%lx %s]", k, t, u, r, ow, back == e ? "bk" : "nb");
        }
        klog("charonline: own body NOT found (gamedata sel %u -> pl %08lx, no table entry; no entity passes the master test 0x9425a0). table:%s", sel, pl, b);
    }
    return -1;
}

static int klco_heister(DWORD ent)
{   /* type 2 and the POLICE byte [ent+0x2723] clear (re/balance.md: 0x2723 = police; 0 for a living heister, so this does not block play); the conditions slot 137 and klchar.c use */
    BYTE type = 0, busy = 1;
    return ent && klh_rd(ent + 0x273c, &type, 1) && type == 2 && klh_rd(ent + 0x2723, &busy, 1) && !busy && klh_rd32(ent + 4);
}


/* ---- 'each character once per match' (Arcade: one player per Hero_0N, the AI that wore the chosen hero swaps - klchar.c) ----
 * Online two humans can announce the same character. EVERY peer runs the same function on the same raw announcements: entities are served in table order;
 * a character already taken by a lower entity goes to the next free one (c+1 .. wrap) that the level's wardrobe has. The loser's own machine shows the
 * fallback too, so all screens agree (no host message is needed; announcements stay the RAW choice). Off with Unique=0. GUESS: all peers hold the same wardrobe. */
static int klco_avail(int ch)
{
    return klc_w.on && ch >= 1 && ch <= klc_w.n && klc_w.c[ch - 1].root && (ch <= 8 || !klc_w.c[ch - 1].stock);
}

static int klco_effective(int idx, int raw)
{
    BYTE taken[KLC_NCHAR + 2]; int j, ch, t;
    if (!klco.unique || raw < 1 || raw > KLC_NCHAR || !klco_avail(raw)) return raw;
    memset(taken, 0, sizeof taken);
    for (j = 0; j < KLCO_N; j++) {
        int r = j == klco.ownIdx ? (int)klc_char : (klco.p[j].used ? klco.p[j].c : 0);
        if (r < 1 || r > KLC_NCHAR || !klco_avail(r)) continue;
        ch = r;
        for (t = 0; t < KLC_NCHAR && taken[ch]; t++) { do ch = ch % KLC_NCHAR + 1; while (!klco_avail(ch)); }
        if (taken[ch]) ch = r;                                     /* all taken: nothing better to give */
        taken[ch] = 1;
        if (j == idx) {
            if (ch != r && klco.toldEff[idx] != ch + 100 * r) { klco.toldEff[idx] = ch + 100 * r; klog("charonline: unique: entity %d asked for %s but a lower entity wears it: shown as %s", idx, klco_nm(r), klco_nm(ch)); }
            return ch;
        }
    }
    return raw;
}

/* The stock Dog Days heister n (1..8) on a level with NO wardrobe (every stock FA map): the eight models are the same objects in all nine stock levels
 * and the rules object's hero table (rules+0x208, 8 dwords, entry n-1 = heister n: the table klchar.c's offline path already uses as `hero[slot]`)
 * holds their roots. 2026-10-28 (bench A1HIRE on F06: 'no such model (wardrobe missing): the stock body stays', a hire changed nothing).
 * CONFIRMED 10-28 (bench A1HIRE3, F06 online host, IgnoreWardrobe=1): the online rules keep the same table at the same offset
 * ('stock hero table TAKEN ... table 35282 35384 35480 35571 35661 35753 35847 35938', J.C. 35282 = the wardrobe's own root);
 * checked before use: all eight entries non-zero and distinct, and the body the entity wears now is one of them (stock slot 137 gave it GetHero(2,seat)).
 * Off with [CharOnline] StockHero=0. Returns the root or 0. */
static DWORD klco_stock_root(int ch, DWORD model, const char *who)
{
    DWORD gs = 0, rules = 0, hero[8]; int i, j, found = 0; const char *why = 0;
    /* c9hire3 1028: every refusal says why, once per ROUND (klco.toldStock), so a bench log shows whether the table was consulted and what it held */
    if (!klco.stockHero) why = "[CharOnline] StockHero=0";
    else if (ch < 1 || ch > 8) why = "char is not one of the eight stock heisters";
    else if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLC_SETTINGS))) || !(rules = klh_rd32(gs + 0x54))) why = "no game settings / rules object yet";
    else if (!klh_rd(rules + 0x208, hero, sizeof hero)) why = "rules+0x208 not readable (GUESS offset)";
    if (!why) {
        for (i = 0; i < 8 && !why; i++) {
            if (!hero[i]) why = "a table entry is 0 (rules+0x208 is not the hero table here: GUESS offset wrong, or not filled yet)";
            for (j = 0; j < i && !why; j++) if (hero[j] == hero[i]) why = "table entries are not distinct (not the hero table: GUESS offset wrong)";
            if (hero[i] == model) found = 1;
        }
        if (!why && !found) why = "the body this entity wears is not in the table";
    }
    if (why) {
        if (!klco.toldStock++) klog("charonline: stock hero table REFUSED for %s (char %d, model %lu, rules %08lx): %s", who, ch, model, rules, why);
        return 0;
    }
    if (!klco.toldStock++) klog("charonline: stock hero table TAKEN for %s (char %d): model %lu -> %lu; table %lu %lu %lu %lu %lu %lu %lu %lu (rules+0x208, heister n = entry n-1)", who, ch, model, hero[ch - 1], hero[0], hero[1], hero[2], hero[3], hero[4], hero[5], hero[6], hero[7]);
    return hero[ch - 1];
}

/* ---- one body: model, then variant (klchar.c's formula) ---- */
static void klco_look(DWORD ent, int idx, int ch, int mask, int outfit, int gt, const char *who, DWORD now)
{
    static const BYTE model_code[14] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x57, 0x8b, 0x7e, 0x04, 0x50, 0x8b, 0xcf };
    static const BYTE variant_code[10] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x89, 0x46, 0x50 };
    DWORD node, model, cur = 0, want_root = 0; char key[64], scene[160]; int wardrobe, i, v;
    if (!ch && !mask && !outfit) return;
    if (!(node = klh_rd32(ent + 4)) || !(model = klh_rd32(node + 0x68))) { klco_why(idx, now, "%s: no node / model (node %08lx)", who, node); return; }
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) { klco_why(idx, now, "%s: level key not readable", who); return; }
    wardrobe = klc_w.on && !_stricmp(key, klc_w.key);
    if (!klc_same_code(0x783fb0, model_code, sizeof model_code) || !klc_same_code(KLC_SETVARIANT, variant_code, sizeof variant_code)) {
        if (!klco.toldCode++) klog("charonline: the two game routines are not the ones this build knows: nothing is changed");
        return;
    }
    if (ch >= 1) {
        if (!klco.toldSrc++) klog("charonline: body source for %s (char %d) on level %s: wardrobe loaded %d (key %s), wardrobe applies %d, entry root %lu, [CharOnline] StockHero=%d -> %s", who, ch, key, klc_w.on, klc_w.key, wardrobe, wardrobe && ch <= klc_w.n ? klc_w.c[ch - 1].root : 0, klco.stockHero,
            wardrobe && ch <= klc_w.n && klc_w.c[ch - 1].root && (ch <= 8 || !klc_w.c[ch - 1].stock) ? "WARDROBE (the stock table is not consulted)" : !wardrobe ? "stock table (decision logged next)" : "none (wardrobe has no usable entry)");
        if (wardrobe && ch <= klc_w.n && klc_w.c[ch - 1].root && (ch <= 8 || !klc_w.c[ch - 1].stock)) want_root = klc_w.c[ch - 1].root;
        else if (!wardrobe && (want_root = klco_stock_root(ch, model, who)) != 0) { /* stock body of a Dog Days heister from the rules' hero table */ }
        else if (!klco.toldNoWar++) klog("charonline: %s wants %s (char %d) and level %s has no such model (wardrobe %s): the stock body stays", who, klco_nm(ch), ch, key, wardrobe ? "has no entry" : "missing");
    }
    if (want_root && model != want_root) {
        if (now - klco.triedAt[idx] > 10000) { klco.triedAt[idx] = now; klco.tried[idx] = 0; }
        if (!gt) return;
        if (klco.tried[idx] >= klco.tries) klco_why(idx, now, "%s: model %lu still not %lu after %d tries in 10 s", who, model, want_root, klco.tried[idx]);
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
        if (i == klc_w.n) { klco_why(idx, now, "%s: model %lu is not in the wardrobe of %s (char %d wants root %lu)", who, model, key, ch, want_root); return; }
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
            if (which == 0 && klco.ignoreChar) { static int told; if (!told++ || klco.log) klog("charonline: hire on: F9 (heister) ignored, as in Arcade; the body is the game's own or the hired one (F11 mask / Ctrl+F11 outfit still work)"); dC = c; dM = m; return; }
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
        if (klco.toldOnline) { klco.toldOnline = 0; memset(klco.p, 0, sizeof klco.p); klco.ownIdx = -1; klco.pubStr[0] = 0; klco.lobby = 0; klco.entSig = 0; klog("charonline: session over: peer looks forgotten"); }
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
    {   /* the own body: the local player's entity, found in the table (slot method, else the master scan) */
        DWORD pl = 0, sig = 0; int idx, how = 0;
        for (i = 0; i < n; i++) sig = sig * 31 + klco_ent(ents, n, i);
        if (sig != klco.entSig) {                                  /* a new level / round built new player objects: what peers said before is about other bodies */
            if (klco.entSig) { memset(klco.p, 0, sizeof klco.p); klog("charonline: the player table changed (new round): peer looks forgotten, they re-announce every 2 s"); }
            klco.entSig = sig; klco.since = now; klco.pubStr[0] = 0; klco.diagAt = 0; klco.toldNoWar = 0; klco.toldStock = 0; klco.toldSrc = 0; klco.toldFollow = 0;     /* D4 (re/netcode_players_1027.md): the stock-map 'no such model' note once per ROUND, not once per session */
        }
        idx = klco_find_own(ents, n, now, &pl, &how);
        /* 10-27 (bench BOSE5c): after the van escape the spectator camera follows a peer and the gamedata slot points at HIS body; the host then
           dressed the followed client as his own pick and announced it for entity 1. Keep my body while it is still in this round's table and the
           new entity is one a peer has claimed (a peer's announced body is never mine) or is not a master on this machine (review: a peer that has
           not announced yet; the master test 0x9425a0 is the same one the fallback below uses). */
        if (idx >= 0 && idx < KLCO_N && klco.ownIdx >= 0 && klco.ownIdx < n && idx != klco.ownIdx && klco_ent(ents, n, klco.ownIdx) == klco.ownEnt
            && (klco.p[idx].used || !klco_is_master(pl))) {
            if (!klco.toldFollow) { klco.toldFollow = 1; klog("charonline: the player slot moved to peer entity %d (spectating?): my body stays entity %d", idx, klco.ownIdx); }
            idx = klco.ownIdx; pl = klco.ownEnt;
        }
        if (idx != klco.ownIdx || (idx >= 0 && pl != klco.ownEnt)) {
            BYTE type = 0; if (pl) klh_rd(pl + 0x273c, &type, 1);
            klog("charonline: my body: entity %d of %d (%08lx, type %u) found by %s%s", idx, n, pl, type, how == 1 ? "gamedata slot (Arcade's way)" : how == 2 ? "master scan 0x9425a0" : "nothing", idx < 0 ? " - NOT in the player table: nothing is sent or applied for me" : "");
            klco.ownIdx = idx; klco.ownEnt = idx >= 0 ? pl : 0; klco.ownHow = how; klco.pubStr[0] = 0;     /* the peers' looks are KEPT (they belong to the round, not to my body) */
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
            /* 2026-10-26 FIX: GetLobbyMemberByIndex returns CSteamID through a HIDDEN POINTER (first stack argument; the 008 adapter pops 0x10 =
               ptr + id + index: re/private_match.md 'slots 12..35' ret list, klbuild.c:795). The old call passed (lobby, index) and read edx:eax:
               Steam then wrote 8 bytes to the address = the lobby id's low dword and popped 4 bytes too many. Only reached with Steam=1 in a
               Steam lobby (never in System Link, which is why B2 passed). */
            unsigned __int64 id = 0; const char *v; char b[40]; int a, c, m, o;
            ((void *(__fastcall *)(void *, void *, unsigned __int64 *, unsigned __int64, int))KLMM_REAL(17))(klmm_real, 0, &id, klco.lobby, mi);
            if (!id) continue;
            v = ((const char *(__fastcall *)(void *, void *, unsigned __int64, unsigned __int64, const char *))KLMM_REAL(23))(klmm_real, 0, klco.lobby, id, "klx_look");
            if (v && klh_rdstr((DWORD_PTR)v, b, sizeof b) && klco_parse(b, &a, &c, &m, &o)) { klco_heard(a, c, m, o, 1, now); seen[a] = 1; }
        }
        (void)seen;                                    /* a member gone from the lobby data keeps his last look for the round (his body stays) */
    }
    if (klco.forgetMs > 0) for (i = 0; i < KLCO_N; i++) if (klco.p[i].used && now - klco.p[i].at > (DWORD)klco.forgetMs) { klco.p[i].used = 0; klog("charonline: peer on entity %d has been silent for %d ms: forgotten (ForgetMs)", i, klco.forgetMs); }
#ifdef KLHOOK_TEST
    if (klco.testPeer >= 0 && klco.testPeer < n && klco.testPeer != klco.ownIdx) klco_heard(klco.testPeer, klco.testChar, klco.testMask, klco.testOutfit, 1, now), klco.p[klco.testPeer].src = 3;
#endif
    /* ---- apply: after the table has stood still for Settle ms */
    if ((LONG)(now - klco.since) < klco.settle) return;
    if (klco.ownIdx >= 0 && klco_heister(klco.ownEnt)) klco_look(klco.ownEnt, klco.ownIdx, klco_effective(klco.ownIdx, (int)klc_char), (int)klc_mask, (int)klc_outfit, game_thread, "my body", now);
    for (i = 0; i < n; i++) if (klco.p[i].used && i != klco.ownIdx) {
        DWORD ent = klco_ent(ents, n, i);
        if (klco_heister(ent)) klco_look(ent, i, klco_effective(i, klco.p[i].c), klco.p[i].m, klco.p[i].o, game_thread, "peer", now);
        else {
            BYTE type = 0, pol = 0; if (ent) { klh_rd(ent + 0x273c, &type, 1); klh_rd(ent + 0x2723, &pol, 1); }
            klco_why(i, now, "peer: not a heister body here (ent %08lx of %d, type %u, police byte %u, node %08lx)", ent, n, type, pol, ent ? klh_rd32(ent + 4) : 0);
        }
    }
    for (i = n; i < KLCO_N; i++) if (klco.p[i].used && i != klco.ownIdx) klco_why(i, now, "peer: entity index beyond this machine's table (%d entries)", n);
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
    klco.unique = GetPrivateProfileIntA("CharOnline", "Unique", 1, klh_ini) != 0;
    klco.stockHero = GetPrivateProfileIntA("CharOnline", "StockHero", 1, klh_ini) != 0;       /* (recommended on) a Dog Days heister's stock body on a level without a wardrobe */
    klco.forgetMs = (int)GetPrivateProfileIntA("CharOnline", "ForgetMs", 0, klh_ini);
    klco.ownDiag = GetPrivateProfileIntA("CharOnline", "OwnDiag", 1, klh_ini) != 0;
    klco.settle = GetPrivateProfileIntA("CharOnline", "Settle", 1500, klh_ini);
    klco.tries = GetPrivateProfileIntA("CharOnline", "Tries", 3, klh_ini);
    /* [Hire] OnlineIgnoreChar (default 1, recommended on): with [Hire] Enable=1 Arcade ignores the Heister page Char (klchar.c: ch = klhr_body).
       Online used to apply the saved Char anyway (owner log 10-27: Standen by F9 with hire on). Zero the IN-MEMORY choice only (the ini is not
       touched); klhire_online.c then saves 0 and gives 0 back after a hired round, so HRF2/HRP2 (hired body worn in round 2) are unchanged. Off = old behaviour. */
    klco.ignoreChar = klhr_on && GetPrivateProfileIntA("Hire", "OnlineIgnoreChar", 1, klh_ini) != 0;
    if (klco.ignoreChar && klc_char) { klog("charonline: hire on: the saved Char=%ld is ignored online, as in Arcade ([Hire] OnlineIgnoreChar=0 restores it)", (long)klc_char); klc_char = 0; }
    klco.keyChar = klkeys_vk(KK_CHAR) & 0xff;
    klco.keyMask = klkeys_vk(KK_MASK) & 0xff;
    if (klco.settle < 0 || klco.settle > 20000) klco.settle = 1500;
    if (klco.tries < 1 || klco.tries > 10) klco.tries = 3;
#ifdef KLHOOK_TEST
    klco.testPeer = (int)GetPrivateProfileIntA("CharOnline", "TestPeer", -1, klh_ini);
    klco.testChar = (int)GetPrivateProfileIntA("CharOnline", "TestChar", 0, klh_ini);
    klco.testMask = (int)GetPrivateProfileIntA("CharOnline", "TestMask", 0, klh_ini);
    klco.testOutfit = (int)GetPrivateProfileIntA("CharOnline", "TestOutfit", 0, klh_ini);
#endif
    klog("charonline: on; Steam=%d Udp=%d Keys=%d (F9 char, F11 mask, Ctrl+F11 outfit) Unique=%d ForgetMs=%d Settle=%d Tries=%d; own choice Char=%ld Mask=%ld Outfit=%ld; every peer announces its entity-table index + look", klco.steam, klco.udp, klco.keys, klco.unique, klco.forgetMs, klco.settle, klco.tries, klc_char, klc_mask, klc_outfit);
}

#endif /* KLCHARONLINE_C */
