/*
 * klstinger.c - [Stinger]: short one-shot sounds / music cues tied to round EVENTS (2026-10-23, track stinger; owner: "make the maps
 * feel more engaging and lively ... more unique sounds ... more payday music n stuff"). Part of KLHook (included by klhook.c after
 * kladren.c, SHIP and TEST alike). Off unless [Stinger] Enable=1, and every event is off until its clip list is set.
 * NOTHING HERE HAS RUN IN THE GAME. Reads only: no write, no call of a game routine, no patch.
 *
 * WHY: klmusic.c is a mood jukebox (timers and phases) and klambience.c plays timed one-shots. Neither reacts to a single thing a
 * player DID. This part plays one short cue the moment the round does something. Same MCI pattern as klambience.c (one worker thread of
 * our own makes every winmm call; 'mpegvideo'; the game thread only reads and posts), but its own aliases kst0 / kst1, so it runs
 * beside the jukebox (kmua / kmub) and the ambience (kamb / kam0..3).
 *
 * THE EVENTS. Each uses a signal that another module already reads (klb_read's record: klbot.c; the human's down state: kldown.c;
 * a bot's down byte: klbotdown.c). A cue is a state EDGE seen between two passes (250 ms), never a level.
 *   Loud     the heist went loud: some heister's heist stage rose to >= 1, or LoudAfter seconds passed (klmusic.c's ACTION rule
 *            without the money clause; money is Loot). GUESS: "loud" = this; no police signal exists (actor team offset unknown).
 *   Loot     the crew's money rose above its start value (klmusic.c / klambience.c read the same sum). First rise only, unless LootEvery=1.
 *   Down     a heister is down, not dead: the HUMAN's [player+0x2948][+4] left 0 (kldown.c reads it, seen live in the owner's rounds),
 *            or an AI heister's [actor+0x64c] became 1 (klbotdown.c says the game's own down goal sets it; read directly here, so
 *            [BotDown] need not be on). GUESS: that byte is only 1 in a down; if the stock game uses it for something else a bot will
 *            "go down" there too.
 *   Dead     a record's status (+0x10) became 7 (klbot.c: 7 = dead; klmusic.c uses it for "you are dead"). Any heister, you included.
 *   Betray   a record's traitor flag (flags +0x79 bit 2) went from 0 to 1 (klbot.c logs the same edge: 'traitor flag SET'): the game's
 *            tactic, Backstab, BackstabCrew and Bribe all set it.
 *   Last30   the escape vehicle waits (rules+0x1dc in 3..4) and its timer (rules+0x1d8, seconds) fell to LastSec (30) or less. Only when
 *            the wait began with more than LastSec + 5 s on the timer (else it would fire together with Open). The timer is the van's
 *            wait (klbot.c:26: 'seconds the escape vehicle still waits, counted down'; not a GUESS). Backstab / Bribe write 0.0 to it (klbot.c:162,
 *            175, 892, 909): the timer > 0.5 guard stops a Bribe from cueing, but a zeroing part-way down can cut Last30 short (it then never fires).
 *   Open     the escape vehicle state went from < 3 to 3..5 (klmusic.c's "escape coming").
 *   Reached  YOU are aboard (your record's status 4) or escaped (6). The human only.
 *
 * ANTI-SPAM: a record's first sight and the first 8 s of a round (the grace klmusic.c / klambience.c use) only set the baseline.
 * Per event: List (semicolon list of mp3 names below Folder), Vol (0..100), Cool (s between two cues of that event), Max (cues per round,
 * 0 = no limit), Chance (per cent). Globally: Gap seconds between any two cues unless the new one has a higher priority than the one
 * before (Reached > Betray > Open > Last30 > Dead > Down > Loot > Loud: a lower one inside the gap is dropped, not delayed).
 * A clip is never the same twice in a row when the list has more than one.
 *
 * SILENT: no round, online (kl_online()), [Solo] bench unless SoloPlay=1, [Stinger.<key>] Enable=0. Map key as klmusic.c (DM01B, F02...).
 * A cue already playing is left to finish when the round ends (the Reached cue plays then); a silent state (online, map off) closes all.
 *
 * KLHook.ini
 *   [Stinger]
 *   Enable=0   Volume=70 (0..100)   Folder=<folder of the files>   Gap=3   LoudAfter=45 (0 = stage only)   LastSec=30   LootEvery=0
 *   SoloPlay=0   Log=1 (2 = also say why a cue was dropped)
 *   <Event>=a.mp3;b.mp3   <Event>Vol= <Event>Cool= <Event>Max= <Event>Chance=     Event = Loud Loot Down Dead Betray Last30 Open Reached
 *   [Stinger.<key>]  the same keys for one map; Enable=0 silences it
 * Log lines: 'stinger: on', 'stinger: map ...', 'stinger: <Event> <file> (why; map; round second N)'.
 */
#ifndef KLSTINGER_C
#define KLSTINGER_C

#define KLST_MAXF   16
#define KLST_PATH   260
#define KLST_NSLOT  2
#define KLST_QN     4

typedef DWORD (WINAPI *klst_send_fn)(LPCSTR, LPSTR, UINT, HWND);
typedef BOOL  (WINAPI *klst_err_fn)(DWORD, LPSTR, UINT);

static struct { char f[KLST_PATH]; int vol; } klst_q[KLST_QN];     /* the queue (ring), under klst_cs */
static int klst_qh, klst_qt, klst_stopseq;                          /* klst_stopseq: bumped to close every slot now */
static CRITICAL_SECTION klst_cs;
static HANDLE klst_ev;
static int klst_log = 1, klst_nerr, klst_wmaster = 70;
static klst_send_fn klst_send; static klst_err_fn klst_errs;

struct klst_slot { int open, played; DWORD started; char al[8], file[KLST_PATH]; };
static struct klst_slot klst_sh[KLST_NSLOT];

static int klst_mci(char *ret, int rl, const char *fmt, ...)
{
    char cmd[700]; va_list a; DWORD e;
    va_start(a, fmt); _vsnprintf(cmd, sizeof cmd - 1, fmt, a); va_end(a); cmd[sizeof cmd - 1] = 0;
    if (ret && rl) ret[0] = 0;
    if (!klst_send) return 0;
    e = klst_send(cmd, ret, ret ? (UINT)rl : 0, 0);
    if (e) {
        char m[200] = "?";
        if (klst_errs) klst_errs(e, m, sizeof m);
        if (klst_nerr++ < 30) klog("stinger: MCI '%.150s' failed (%lu): %s", cmd, (unsigned long)e, m);
        return 0;
    }
    return 1;
}

static void klst_close(struct klst_slot *p)
{
    if (!p->open) return;
    klst_mci(0, 0, "stop %s", p->al); klst_mci(0, 0, "close %s", p->al);
    p->open = 0;
}

static const char *klst_base(const char *p) { const char *q = strrchr(p, 0x5c); return q ? q + 1 : p; }

static void klst_play(const char *path, int vol)
{   /* a free slot; none free: the oldest cue is cut (a newer event matters more than a tail) */
    int s, pick = -1; DWORD oldest = 0xffffffffu; char al[8];
    for (s = 0; s < KLST_NSLOT; s++) if (!klst_sh[s].open) { pick = s; break; }
    if (pick < 0) { for (s = 0; s < KLST_NSLOT; s++) if (klst_sh[s].started < oldest) { oldest = klst_sh[s].started; pick = s; } klst_close(&klst_sh[pick]); }
    snprintf(al, sizeof al, "kst%d", pick);
    snprintf(klst_sh[pick].al, sizeof klst_sh[pick].al, "%s", al);
    if (!klst_mci(0, 0, "open \"%s\" type mpegvideo alias %s", path, al)) return;
    klst_sh[pick].open = 1; klst_sh[pick].played = 0; klst_sh[pick].started = GetTickCount();
    snprintf(klst_sh[pick].file, sizeof klst_sh[pick].file, "%s", path);
    klst_mci(0, 0, "setaudio %s volume to %d", al, klst_wmaster * vol / 10);
    if (!klst_mci(0, 0, "play %s", al)) { klst_close(&klst_sh[pick]); return; }
    klst_mci(0, 0, "setaudio %s volume to %d", al, klst_wmaster * vol / 10);     /* some drivers take the volume only once playing (as klmusic.c) */
}

static void klst_poll(DWORD now)
{   /* every 250 ms: close finished cues */
    char r[64]; int s;
    for (s = 0; s < KLST_NSLOT; s++) {
        struct klst_slot *p = &klst_sh[s];
        if (!p->open) continue;
        if (now - p->started > 60000u) { klst_close(p); continue; }          /* safety only: the staged clips are cut at 12 s */
        if (now - p->started > 300 && klst_mci(r, sizeof r, "status %s mode", p->al)) {
            /* "stopped" / "not ready" also show for a moment BEFORE an mp3 starts to play (the offline harness lost slots to that): a finish counts only
               after "playing" was seen, or after 2.5 s (the 60 s rule above covers a stuck one) */
            if (!_stricmp(r, "playing")) p->played = 1;
            else if (!_stricmp(r, "stopped") && (p->played || now - p->started > 2500u)) klst_close(p);
        }
    }
}

/* [KLHook] MciPump (2026-10-24): the same pumped wait as klmusic.c's klmu_wait, see there (the reason is a GUESS). */
static int klst_pump = 1;
static void klst_wait(HANDLE ev, DWORD ms)
{
    static DWORD (WINAPI *mw)(DWORD, const HANDLE *, BOOL, DWORD, DWORD); static BOOL (WINAPI *pk)(LPMSG, HWND, UINT, UINT, UINT);
    static LRESULT (WINAPI *ds)(const MSG *); MSG msg;
    if (klst_pump && !mw) {                              /* user32 is looked up, not linked (as in klhook.c) */
        HMODULE u = GetModuleHandleA("user32.dll");
        if (u) { mw = (void *)GetProcAddress(u, "MsgWaitForMultipleObjects"); pk = (void *)GetProcAddress(u, "PeekMessageA"); ds = (void *)GetProcAddress(u, "DispatchMessageA"); }
        if (!mw || !pk || !ds) { klst_pump = 0; mw = 0; }
    }
    if (!klst_pump) { WaitForSingleObject(ev, ms); return; }
    if (mw(1, &ev, FALSE, ms, QS_ALLINPUT) == WAIT_OBJECT_0 + 1)
        while (pk(&msg, 0, 0, 0, PM_REMOVE)) ds(&msg);
}

static DWORD WINAPI klst_thread(void *u)
{
    int seen = 0, k; DWORD lastp = 0; HMODULE m = LoadLibraryA("winmm.dll"); (void)u;
    if (m) { klst_send = (klst_send_fn)GetProcAddress(m, "mciSendStringA"); klst_errs = (klst_err_fn)GetProcAddress(m, "mciGetErrorStringA"); }
    if (!klst_send) { klog("stinger: winmm.dll / mciSendStringA not found - the stingers stay silent"); return 0; }
    for (;;) {
        DWORD now; int stop = 0, got = 0, vol = 0; static char sf[KLST_PATH];
        klst_wait(klst_ev, 40);
        now = GetTickCount();
        EnterCriticalSection(&klst_cs);
        if (klst_stopseq != seen) { seen = klst_stopseq; stop = 1; }
        if (klst_qh != klst_qt) { snprintf(sf, sizeof sf, "%s", klst_q[klst_qh].f); vol = klst_q[klst_qh].vol; klst_qh = (klst_qh + 1) % KLST_QN; got = 1; }
        LeaveCriticalSection(&klst_cs);
        if (stop) for (k = 0; k < KLST_NSLOT; k++) klst_close(&klst_sh[k]);
        if (got) klst_play(sf, vol);
        now = GetTickCount();     /* AFTER the play above: a slot opened a moment ago has started > the old 'now', and now - started would wrap to ~49 days (closed every new cue at once) */
        if (now - lastp >= 250) { lastp = now; klst_poll(now); }
    }
}

/* ---------------------------------------------------------------- the game thread (reads the round, posts) */

#ifndef KLSTINGER_TEST

enum { KLST_LOUD, KLST_LOOT, KLST_DOWN, KLST_DEAD, KLST_BETRAY, KLST_LAST30, KLST_OPEN, KLST_REACHED, KLST_NE };
/* name, volume, cool (s), max per round (0 = no limit), chance %, priority (higher wins inside the Gap). All numbers are GUESSES (unheard). */
static const struct { const char *name; int vol, cool, max, chance, prio; } klst_def[KLST_NE] = {
    { "Loud",    75,  0, 1, 100, 1 },
    { "Loot",    65,  0, 1, 100, 2 },
    { "Down",    65, 15, 0,  80, 3 },
    { "Dead",    70,  8, 0, 100, 4 },
    { "Betray",  80, 10, 0, 100, 7 },
    { "Last30",  70,  0, 1, 100, 5 },
    { "Open",    70,  0, 1, 100, 6 },
    { "Reached", 75,  0, 1, 100, 8 },
};

struct klst_ev { int n, vol, cool, max, chance, fired, last; DWORD t_last; char f[KLST_MAXF][KLST_PATH]; };

static struct {
    int on, vol, gap, loud_after, last_sec, loot_every, enabled, round, lastprio, loot_done, loud_done, last30_done, open_done, stopped;
    char folder[KLST_PATH], map[40];
    struct klst_ev e[KLST_NE];
    int pend[KLST_NE];                    /* a one-shot event held back by the Gap: its ev value, retried next pass */
    DWORD t_round, t_last, t_fail, rules0, money0, t_cue;
    float timer_open;
    BYTE veh0;
    struct { int used, down; BYTE status, flags, stage; } p[KLB_NREC];       /* the records one pass before */
} klst;
static DWORD klst_seed = 4242;

static int klst_rand(int n) { klst_seed = klst_seed * 1103515245u + 12345u; return n > 0 ? (int)((klst_seed >> 16) % (unsigned)n) : 0; }

static int klst_str(const char *key, const char *def, char *out, int cap)
{   /* [Stinger.<map>] first, then [Stinger] */
    char s2[64];
    if (klst.map[0]) {
        snprintf(s2, sizeof s2, "Stinger.%s", klst.map);
        GetPrivateProfileStringA(s2, key, "\x01", out, cap, klh_ini);
        if (out[0] != 1) return 1;
    }
    GetPrivateProfileStringA("Stinger", key, "\x01", out, cap, klh_ini);
    if (out[0] == 1) { snprintf(out, cap, "%s", def); return 0; }
    return 1;
}
static int klst_int(const char *key, int def)
{
    char b[40]; klst_str(key, "", b, sizeof b);
    return b[0] ? atoi(b) : def;
}

static int klst_parse(char (*f)[KLST_PATH], const char *text, const char *what)
{   /* "a.mp3;b.mp3" -> paths below Folder (a full path stays); a missing file is dropped with a log line */
    char buf[2048], *p, *e; int n = 0;
    snprintf(buf, sizeof buf, "%s", text);
    for (p = buf; *p && n < KLST_MAXF; p = e ? e + 1 : p + strlen(p)) {
        char full[KLST_PATH]; e = strchr(p, ';'); if (e) *e = 0;
        while (*p == ' ') p++;
        { int k = (int)strlen(p); while (k > 0 && (p[k - 1] == ' ' || p[k - 1] == '\r')) p[--k] = 0; }
        if (!*p || strchr(p, '"')) { if (!e) break; continue; }
        if (p[1] == ':' || p[0] == 0x5c) snprintf(full, sizeof full, "%s", p);
        else snprintf(full, sizeof full, "%s%s%s", klst.folder, klst.folder[0] && klst.folder[strlen(klst.folder) - 1] != 0x5c ? "\\" : "", p);
        if (GetFileAttributesA(full) == INVALID_FILE_ATTRIBUTES) { klog("stinger: %s: '%s' is not there - dropped", what, full); if (!e) break; continue; }
        snprintf(f[n++], KLST_PATH, "%s", full);
        if (!e) break;
    }
    return n;
}

static void klst_loadmap(void)
{
    char b[2048], k[48]; int g;
    klst_str("Folder", "", klst.folder, sizeof klst.folder);
    klst.enabled = klst_int("Enable", 1) != 0;                  /* [Stinger.<key>] Enable=0 silences one map; [Stinger] Enable=1 got us here */
    klst.vol = klst_int("Volume", 70); if (klst.vol < 0) klst.vol = 0; if (klst.vol > 100) klst.vol = 100;
    klst.gap = klst_int("Gap", 3); if (klst.gap < 0) klst.gap = 0;
    klst.loud_after = klst_int("LoudAfter", 45);
    klst.last_sec = klst_int("LastSec", 30); if (klst.last_sec < 5) klst.last_sec = 5;
    klst.loot_every = klst_int("LootEvery", 0) != 0;
    for (g = 0; g < KLST_NE; g++) {
        struct klst_ev *E = &klst.e[g]; const char *nm = klst_def[g].name;
        klst_str(nm, "", b, sizeof b); E->n = klst_parse(E->f, b, nm);
        snprintf(k, sizeof k, "%sVol", nm);    E->vol = klst_int(k, klst_def[g].vol); if (E->vol > 100) E->vol = 100; if (E->vol < 0) E->vol = 0;
        snprintf(k, sizeof k, "%sCool", nm);   E->cool = klst_int(k, klst_def[g].cool); if (E->cool < 0) E->cool = 0;
        snprintf(k, sizeof k, "%sMax", nm);    E->max = klst_int(k, klst_def[g].max); if (E->max < 0) E->max = 0;
        snprintf(k, sizeof k, "%sChance", nm); E->chance = klst_int(k, klst_def[g].chance); if (E->chance < 0) E->chance = 0; if (E->chance > 100) E->chance = 100;
        E->fired = 0; E->last = -1; E->t_last = 0;
    }
    klog("stinger: map %s: Loud %d / Loot %d / Down %d / Dead %d / Betray %d / Last30 %d / Open %d / Reached %d clips, volume %d, gap %d s%s",
         klst.map[0] ? klst.map : "?", klst.e[0].n, klst.e[1].n, klst.e[2].n, klst.e[3].n, klst.e[4].n, klst.e[5].n, klst.e[6].n, klst.e[7].n,
         klst.vol, klst.gap, klst.enabled ? "" : " (this map is switched off)");
}

static void klst_off(int hard)
{   /* no round / a silent state. hard = close every cue now (online, map off); else a cue playing is left to finish */
    if (hard && !klst.stopped) {
        klst.stopped = 1;
        EnterCriticalSection(&klst_cs); klst_qh = klst_qt; klst_stopseq++; LeaveCriticalSection(&klst_cs); SetEvent(klst_ev);
    }
    klst.round = 0;
}

static void klst_post(const char *f, int vol)
{
    int nt;
    EnterCriticalSection(&klst_cs);
    klst_wmaster = klst.vol;
    nt = (klst_qt + 1) % KLST_QN;
    if (nt != klst_qh) { snprintf(klst_q[klst_qt].f, KLST_PATH, "%s", f); klst_q[klst_qt].vol = vol; klst_qt = nt; }
    LeaveCriticalSection(&klst_cs);
    SetEvent(klst_ev);
}

/* returns 1 = posted, 0 = dropped for good (no list, Max, cooldown, chance), -1 = held back by the Gap only: a one-shot event then stays PENDING and is retried */
static int klst_cue(int g, DWORD now, const char *why)
{   /* one event happened: apply the per-event and global limits, then post a clip */
    struct klst_ev *E = &klst.e[g]; int pick; const char *f; const char *drop = 0; int gapdrop = 0;
    if (!E->n) return 0;                                            /* no list: the event is off */
    if (E->max > 0 && E->fired >= E->max) drop = "Max reached";
    else if (E->t_last && now - E->t_last < (DWORD)E->cool * 1000u) drop = "cooldown";
    else if (klst.t_cue && now - klst.t_cue < (DWORD)klst.gap * 1000u && klst_def[g].prio <= klst.lastprio) { drop = "inside the Gap of a cue of equal or higher priority"; gapdrop = 1; }
    else if (E->chance < 100 && klst_rand(100) >= E->chance) drop = "chance";
    if (drop) { if (klst_log >= 2) klog("stinger: %s dropped (%s; %s)", klst_def[g].name, drop, why); return gapdrop ? -1 : 0; }
    pick = klst_rand(E->n);
    if (E->n > 1 && pick == E->last) pick = (pick + 1 + klst_rand(E->n - 1)) % E->n;       /* never the same clip twice in a row */
    E->last = pick; f = E->f[pick];
    E->fired++; E->t_last = KLB_T(now); klst.t_cue = KLB_T(now); klst.lastprio = klst_def[g].prio;
    klst_post(f, E->vol);
    if (klst_log) klog("stinger: %s %s (%s; map %s, round second %lu)", klst_def[g].name, klst_base(f), why, klst.map, (unsigned long)((KLB_T(now) - klst.t_round) / 1000));
    return 1;
}

static int klst_human_down(void)
{   /* the local player's down state [player+0x2948][+4] != 0 (falling 2, lying 1, getting up 3): read the way kldown.c reads it */
    DWORD gd, pl, d, ds = 0; BYTE idx = 0xff;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLD_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || (signed char)idx < 0 || idx > 31 ||
        !(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_rd32(pl) != KLD_PLAYER_VT || !(d = klh_rd32(pl + 0x2948)) || klh_rd32(d) != pl ||
        !klh_rd(d + 4, &ds, 4)) return 0;
    return ds != 0 && ds < 8;
}

static int klst_bot_down(const struct klb_rec *r)
{   /* GUESS: [actor+0x64c] = 1 only in the game's own down goal (klbotdown.c, "byte [actor+0x64c] = 1"); a ZFFActor only */
    BYTE b = 0;
    if (!r->actor || klh_rd32(r->actor) != KLB_ACTOR_VT) return 0;
    return klh_rd(r->actor + 0x64c, &b, 1) && b == 1;
}

static void klst_tick(int game_thread)
{
    DWORD now = GetTickCount(), money = 0; struct klb_snap s; char key[40]; int i, ev[KLST_NE], g, grace, newround = 0;
    if (!klst.on || !game_thread || !klh_exe_ok || now - klst.t_last < 250) return;
    klst.t_last = now;
    if (kl_online()) { klst_off(1); return; }
    klmu_mapkey(key, sizeof key);
    if (strcmp(key, klst.map)) { snprintf(klst.map, sizeof klst.map, "%s", key); klst_off(1); if (key[0]) klst_loadmap(); }
    if (!klst.map[0] || !klst.enabled) { klst_off(1); return; }
    if (!klb_read(&s)) {
        if (!klst.t_fail) klst.t_fail = KLB_T(now);
        if (now - klst.t_fail > 1500) klst_off(0);
        return;
    }
    klst.t_fail = 0;
    if (s.state != KLB_ROUND) { klst_off(0); return; }
    for (i = 0; i < s.n; i++) if (s.r[i].used) money += s.r[i].money;
    if (!klst.round || s.rules != klst.rules0) {                     /* a round began */
        klst.round = 1; klst.rules0 = s.rules; klst.t_round = KLB_T(now); klst.money0 = money; newround = 1;
        klst.loot_done = klst.loud_done = klst.last30_done = klst.open_done = 0; klst.t_cue = 0; klst.lastprio = 0;
        klst.veh0 = s.veh; klst.timer_open = 0; klst.stopped = 0; memset(klst.pend, 0, sizeof klst.pend);
        if (s.veh >= 3 && s.veh <= 5) klst.open_done = 1;      /* the van is already up at the baseline: no Open (and no Last30, whose timer_open stays 0) this round */
        memset(klst.p, 0, sizeof klst.p);
        for (g = 0; g < KLST_NE; g++) { klst.e[g].fired = 0; klst.e[g].t_last = 0; klst.e[g].last = -1; }
    }
    grace = (now - klst.t_round < 8000u);                            /* baseline only, as klmusic.c / klambience.c */
    memset(ev, 0, sizeof ev);
    (void)newround;
    if (grace) klst.money0 = money;
    {   /* per record: edges against the pass before */
        int hdown = klst_human_down();
        for (i = 0; i < s.n && i < KLB_NREC; i++) {
            const struct klb_rec *r = &s.r[i]; int dn;
            if (!r->used) { klst.p[i].used = 0; continue; }
            dn = r->status == 0 && ((r->flags & 1) ? klst_bot_down(r) : (i == s.human && hdown));
            if (klst.p[i].used && !grace) {                          /* a first sight is a baseline, never an event */
                if (r->status == 7 && klst.p[i].status != 7) ev[KLST_DEAD] = 1 + i;
                if ((r->flags & 2) && !(klst.p[i].flags & 2)) ev[KLST_BETRAY] = 1 + i;
                if (dn && !klst.p[i].down) ev[KLST_DOWN] = 1 + i;
                if (i == s.human && (r->status == 4 || r->status == 6) && klst.p[i].status != 4 && klst.p[i].status != 6) ev[KLST_REACHED] = 1 + i;
                if (r->stage >= 1 && r->stage > klst.p[i].stage && !klst.loud_done) ev[KLST_LOUD] = 1 + i;
            }
            klst.p[i].used = 1; klst.p[i].status = r->status; klst.p[i].flags = r->flags; klst.p[i].stage = r->stage; klst.p[i].down = dn;
        }
    }
    if (!grace) {
        if (!klst.loud_done && !ev[KLST_LOUD] && klst.loud_after > 0 && now - klst.t_round >= (DWORD)klst.loud_after * 1000u) ev[KLST_LOUD] = -1;     /* -1: by time */
        if (money > klst.money0) {
            if (!klst.loot_done || klst.loot_every) ev[KLST_LOOT] = 1;
            klst.money0 = money; klst.loot_done = 1;
        } else if (money < klst.money0) klst.money0 = money;       /* money fell (a van lost it): a later rise counts again */
        if (s.veh >= 3 && s.veh <= 5 && klst.veh0 < 3 && !klst.open_done) { ev[KLST_OPEN] = 1; klst.open_done = 1; klst.timer_open = klb_finite(s.timer) ? s.timer : 0; }
        if (s.veh >= 3 && s.veh <= 4 && !klst.last30_done && klb_finite(s.timer) && s.timer > 0.5f && s.timer <= (float)klst.last_sec &&
            klst.timer_open > (float)(klst.last_sec + 5)) { ev[KLST_LAST30] = 1; klst.last30_done = 1; }
    }
    if (ev[KLST_LOUD]) klst.loud_done = 1;
    if (!grace) klst.veh0 = s.veh;      /* during the grace veh0 keeps the round baseline, so a van that comes up inside it still gives Open right after */
    /* a one-shot held back by the Gap earlier is retried (Loud, Loot, Open, Last30 only) */
    for (g = 0; g < KLST_NE; g++) if (klst.pend[g] && !ev[g]) ev[g] = klst.pend[g];
    /* dispatch, highest priority first: a lower cue in the same pass then falls into the Gap */
    { static const int order[KLST_NE] = { KLST_REACHED, KLST_BETRAY, KLST_OPEN, KLST_LAST30, KLST_DEAD, KLST_DOWN, KLST_LOOT, KLST_LOUD };
      for (i = 0; i < KLST_NE; i++) {
        char why[80]; g = order[i];
        if (!ev[g]) continue;
        if (g == KLST_LOUD && ev[g] < 0) snprintf(why, sizeof why, "after %d s", klst.loud_after);
        else if (g == KLST_LOOT || g == KLST_OPEN || g == KLST_LAST30) snprintf(why, sizeof why, "money $%lu, van %u %.0f s", (unsigned long)money, s.veh, klb_finite(s.timer) ? s.timer : -1.0f);
        else snprintf(why, sizeof why, "record %d", ev[g] - 1);
        { int rc = klst_cue(g, now, why);
          if (g == KLST_LOUD || g == KLST_LOOT || g == KLST_OPEN || g == KLST_LAST30) klst.pend[g] = (rc < 0) ? ev[g] : 0; }
      }
    }
}

static void klst_init(void)
{
    klst.on = GetPrivateProfileIntA("Stinger", "Enable", 0, klh_ini) != 0;
    if (!klst.on) return;
    klst_log = GetPrivateProfileIntA("Stinger", "Log", 1, klh_ini);
    if (GetPrivateProfileIntA("Solo", "Enable", 0, klh_ini) && !GetPrivateProfileIntA("Stinger", "SoloPlay", 0, klh_ini)) {
        klst.on = 0; klog("stinger: [Solo] bench on and [Stinger] SoloPlay=0 - this instance stays silent"); return;
    }
    InitializeCriticalSection(&klst_cs);
    klst_ev = CreateEventA(0, FALSE, FALSE, 0);
    klst_seed ^= GetTickCount();
    klst_pump = GetPrivateProfileIntA("KLHook", "MciPump", 1, klh_ini) != 0;
    CloseHandle(CreateThread(0, 0, klst_thread, 0, 0, 0));
    klog("stinger: on (winmm MCI on a worker thread; one-shot cues from round events; silent online / with [Solo] unless SoloPlay)");
}

#endif /* !KLSTINGER_TEST */

#endif /* KLSTINGER_C */
