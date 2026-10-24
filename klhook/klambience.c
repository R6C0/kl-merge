/*
 * klambience.c - [Ambience]: a looping ambience bed and timed one-shot sounds for the Fragile Alliance round
 * (2026-10-23, owner: "maps feel more lively: music and more ambience all around and more unique sounds").
 * Part of KLHook (included by klhook.c after klmusic.c, SHIP and TEST alike). Off unless [Ambience] Enable=1.
 *
 * WHAT: plays MP3 files (made by tools/kl_ambience.py from Dead Men's and Dog Days' own banks) through Windows MCI
 * ('mpegvideo', winmm loaded at run time: no new import), on a worker thread of its own. Nothing in the game's files changes,
 * so it works the same on every map (the 9 stock FA maps F01..F09 / DD01..09 and the Dead Men maps) and in a private match.
 * Same pattern as klmusic.c (one worker owns all MCI calls, the game thread only reads the round and posts); different MCI aliases
 * (kamb = the bed, kam0..kam3 = one-shots), so the jukebox and the ambience run side by side.
 *
 * THE BED: one file per map ([Ambience.<key>] Bed=, a list = random pick), looped (restarted when MCI reports 'stopped'), fades in
 *   over Fade ms at the round start and out at the round end. Maps in BedSkip (default DM09,DM06B,DM03A,DM05A: the engine's own
 *   ambience / music runs there) get no bed unless [Ambience.<key>] BedForce=1; their one-shots still play (GUESS: one-shots
 *   do not mask engine sound).
 * ONE-SHOT GROUPS (each: a file list, a timer, the earliest round phase, a delay after the round began):
 *   Radio    police radio chatter           From=action After=60  Min=40  Max=90   (the "police phase": no police signal exists, see klmusic.c)
 *   Alarm    alarm bell / siren when it goes loud   From=action After=0  Min=0 Max=0 (Min=Max=0: ONCE, 1.5 s after the phase is reached)
 *   Heli     helicopter fly-over            From=action After=90  Min=150 Max=300
 *   Distant  far-off gunfire / explosions   From=action After=10  Min=30  Max=80
 *   Siren    police sirens passing          From=action After=30  Min=60  Max=150
 *   Spot     any city life (dog, horn, birds, voices)  From=calm After=15 Min=45 Max=120
 *   Local    the map's own sounds (train, phone, ship, tools)  From=calm After=10 Min=25 Max=70      (sound3, empty unless set)
 *   Panic    distant screams / crowd       From=action After=20 Min=40 Max=110                        (sound3, empty unless set)
 *   Keys per group G (all optional, in [Ambience] or [Ambience.<key>]): G=list  GMin= GMax= (seconds)  GFrom=calm|action|escape|dead
 *   GAfter= (seconds)  GVol=0..100.  The group fires at a random time in Min..Max seconds after its phase is reached, then again.
 * PHASES (same reading as klmusic.c; reads the round only): calm = round runs, action = a heister's stage >= 1 / the crew's money rose /
 *   ActionAfter seconds passed (GUESS 45), escape = the van is coming / a stage >= 2 / you aboard, dead = YOU are dead (status 7).
 * SILENT: no round, online (kl_online()), [Solo] bench unless SoloPlay=1, a map with [Ambience.<key>] Enable=0.
 *
 * KLHook.ini
 *   [Ambience]
 *   Enable=0   Volume=60 (0..100 master)  Bed volume BedVol=45   Fade=2500   Folder=<folder of the files>   Log=1   SoloPlay=0
 *   ActionAfter=45   BedSkip=DM09,DM06B,DM03A,DM05A
 *   [Ambience.<key>]  Bed= Radio= Alarm= Heli= Distant= Siren= Spot= Local= Panic=  (+ timing keys above)  Enable=0  BedForce=1
 * Log lines: 'ambience: map ...', 'ambience: bed ...', 'ambience: <group> <file>'.
 */
#ifndef KLAMBIENCE_C
#define KLAMBIENCE_C

#define KLAM_MAXF   24
#define KLAM_PATH   260
#define KLAM_NSHOT  4
#define KLAM_QN     8

typedef DWORD (WINAPI *klam_send_fn)(LPCSTR, LPSTR, UINT, HWND);
typedef BOOL  (WINAPI *klam_err_fn)(DWORD, LPSTR, UINT);

struct klam_cmd_t { int seq, vol, fade, bedvol, stop; char bed[KLAM_PATH]; };   /* stop = close every one-shot now */
static struct klam_cmd_t klam_cmd;                          /* bed command, posted by the game thread, under klam_cs */
static struct { char f[KLAM_PATH]; int vol; } klam_q[KLAM_QN];  /* one-shot queue (ring), under klam_cs */
static int klam_qh, klam_qt;
static CRITICAL_SECTION klam_cs;
static HANDLE klam_ev;
static int klam_log = 1, klam_nerr;
static klam_send_fn klam_send; static klam_err_fn klam_errs;

struct klam_slot { int open, level, target, vol; DWORD started; char al[8], file[KLAM_PATH]; };
static struct klam_slot klam_bed, klam_sh[KLAM_NSHOT];
static int klam_master = 60, klam_fade = 2500, klam_bedvol = 45;

static int klam_mci(char *ret, int rl, const char *fmt, ...)
{
    char cmd[700]; va_list a; DWORD e;
    va_start(a, fmt); _vsnprintf(cmd, sizeof cmd - 1, fmt, a); va_end(a); cmd[sizeof cmd - 1] = 0;
    if (ret && rl) ret[0] = 0;
    if (!klam_send) return 0;
    e = klam_send(cmd, ret, ret ? (UINT)rl : 0, 0);
    if (e) {
        char m[200] = "?";
        if (klam_errs) klam_errs(e, m, sizeof m);
        if (klam_nerr++ < 30) klog("ambience: MCI '%.150s' failed (%lu): %s", cmd, (unsigned long)e, m);
        return 0;
    }
    return 1;
}

static void klam_setvol(struct klam_slot *p, int volpct)
{   /* master 0..100 x clip volume 0..100 x fade level 0..1000 -> MCI 0..1000 */
    if (p->open) klam_mci(0, 0, "setaudio %s volume to %d", p->al, klam_master * volpct * p->level / 10000);
}

static void klam_close(struct klam_slot *p)
{
    if (!p->open) return;
    klam_mci(0, 0, "stop %s", p->al); klam_mci(0, 0, "close %s", p->al);
    p->open = 0; p->level = p->target = 0;
}

static const char *klam_base(const char *p) { const char *q = strrchr(p, 0x5c); return q ? q + 1 : p; }

static int klam_open(struct klam_slot *p, const char *al, const char *path, int vol, int fade, int loop)
{
    if (p->open) klam_close(p);
    snprintf(p->al, sizeof p->al, "%s", al);
    if (!klam_mci(0, 0, "open \"%s\" type mpegvideo alias %s", path, p->al)) return 0;
    p->open = 1; p->level = fade > 0 ? 0 : 1000; p->target = 1000; p->vol = vol; p->started = GetTickCount();
    snprintf(p->file, sizeof p->file, "%s", path);
    klam_setvol(p, vol);
    if (!klam_mci(0, 0, "play %s", p->al)) { klam_close(p); return 0; }
    klam_setvol(p, vol);
    (void)loop;
    return 1;
}

/* a bed open that failed is tried again 1 s later, up to 3 times: the music worker opening its track in the same
   millisecond made it fail with 264 'not enough memory' (OWN2_DM01, V2_DM01: DM01 got no bed at all) */
static struct klam_cmd_t klam_retry; static int klam_retry_n; static DWORD klam_retry_at;

static void klam_bedcmd(const struct klam_cmd_t *c)
{
    klam_master = c->vol; klam_fade = c->fade; klam_bedvol = c->bedvol;
    if (klam_bed.open) klam_setvol(&klam_bed, klam_bedvol);
    if (c != &klam_retry) klam_retry_n = 0;
    if (!c->bed[0]) { if (klam_bed.open) klam_bed.target = 0; return; }       /* fade out, closed by the stepper */
    if (klam_bed.open && !_stricmp(klam_bed.file, c->bed)) { klam_bed.target = 1000; return; }
    if (klam_open(&klam_bed, "kamb", c->bed, klam_bedvol, klam_fade, 1)) { if (klam_log) klog("ambience: bed %s (fade %d ms)%s", klam_base(c->bed), klam_fade, c == &klam_retry ? " on a retry" : ""); klam_retry_n = 0; }
    else if (klam_retry_n < 3) { if (c != &klam_retry) klam_retry = *c; klam_retry.stop = 0; klam_retry_n++; klam_retry_at = GetTickCount() + 1000; }
    else klam_retry_n = 0;                                                    /* 3 retries failed: give up until the next command */
}

static void klam_shot(const char *path, int vol)
{
    int s;
    for (s = 0; s < KLAM_NSHOT; s++) if (!klam_sh[s].open) {
        char al[8]; snprintf(al, sizeof al, "kam%d", s);
        klam_open(&klam_sh[s], al, path, vol, 0, 0);
        return;
    }
    if (klam_log) klog("ambience: all %d one-shot slots busy - %s dropped", KLAM_NSHOT, klam_base(path));
}

static void klam_poll(DWORD now)
{   /* every 250 ms: restart a stopped bed, close finished one-shots */
    char r[64]; int s;
    if (klam_bed.open && now - klam_bed.started > 1500 && klam_bed.target > 0) {
        if (klam_mci(r, sizeof r, "status kamb mode") && (!_stricmp(r, "stopped") || !_stricmp(r, "not ready"))) {
            klam_mci(0, 0, "seek kamb to start"); klam_mci(0, 0, "play kamb"); klam_bed.started = now;
        }
    }
    for (s = 0; s < KLAM_NSHOT; s++) {
        struct klam_slot *p = &klam_sh[s];
        if (!p->open) continue;
        if (now - p->started > 300000u)     /* safety only: the longest one-shot is well under 300 s */ { klam_close(p); continue; }
        if (now - p->started > 400 && klam_mci(r, sizeof r, "status %s mode", p->al) && (!_stricmp(r, "stopped") || !_stricmp(r, "not ready"))) klam_close(p);
    }
}

static void klam_stepfade(DWORD dt)
{
    struct klam_slot *p = &klam_bed;
    int d = klam_fade > 0 ? (int)(1000u * dt / (DWORD)klam_fade) + 1 : 1000;
    if (!p->open || p->level == p->target) return;
    if (p->level < p->target) { p->level += d; if (p->level > p->target) p->level = p->target; }
    else { p->level -= d; if (p->level < p->target) p->level = p->target; }
    if (p->level == 0 && p->target == 0) { klam_close(p); return; }
    klam_setvol(p, klam_bedvol);
}

/* [KLHook] MciPump (2026-10-24): the same pumped wait as klmusic.c's klmu_wait, see there (the reason is a GUESS). */
static int klam_pump = 1;
static void klam_wait(HANDLE ev, DWORD ms)
{
    static DWORD (WINAPI *mw)(DWORD, const HANDLE *, BOOL, DWORD, DWORD); static BOOL (WINAPI *pk)(LPMSG, HWND, UINT, UINT, UINT);
    static LRESULT (WINAPI *ds)(const MSG *); MSG msg;
    if (klam_pump && !mw) {                              /* user32 is looked up, not linked (as in klhook.c) */
        HMODULE u = GetModuleHandleA("user32.dll");
        if (u) { mw = (void *)GetProcAddress(u, "MsgWaitForMultipleObjects"); pk = (void *)GetProcAddress(u, "PeekMessageA"); ds = (void *)GetProcAddress(u, "DispatchMessageA"); }
        if (!mw || !pk || !ds) { klam_pump = 0; mw = 0; }
    }
    if (!klam_pump) { WaitForSingleObject(ev, ms); return; }
    if (mw(1, &ev, FALSE, ms, QS_ALLINPUT) == WAIT_OBJECT_0 + 1)
        while (pk(&msg, 0, 0, 0, PM_REMOVE)) ds(&msg);
}

static DWORD WINAPI klam_thread(void *u)
{
    int seen = 0; DWORD last = GetTickCount(), lastp = 0; HMODULE m = LoadLibraryA("winmm.dll"); (void)u;
    if (m) { klam_send = (klam_send_fn)GetProcAddress(m, "mciSendStringA"); klam_errs = (klam_err_fn)GetProcAddress(m, "mciGetErrorStringA"); }
    if (!klam_send) { klog("ambience: winmm.dll / mciSendStringA not found - the ambience stays silent"); return 0; }
    for (;;) {
        DWORD now; static struct klam_cmd_t copy; int gotcmd = 0, gotshot = 0; static char sf[KLAM_PATH]; int sv = 0;
        klam_wait(klam_ev, 40);
        now = GetTickCount();
        EnterCriticalSection(&klam_cs);
        if (klam_cmd.seq != seen) { copy = klam_cmd; seen = klam_cmd.seq; gotcmd = 1; }
        if (klam_qh != klam_qt) { snprintf(sf, sizeof sf, "%s", klam_q[klam_qh].f); sv = klam_q[klam_qh].vol; klam_qh = (klam_qh + 1) % KLAM_QN; gotshot = 1; }
        LeaveCriticalSection(&klam_cs);
        if (gotcmd) { if (copy.stop) { int k; for (k = 0; k < KLAM_NSHOT; k++) klam_close(&klam_sh[k]); } klam_bedcmd(&copy); }
        else if (klam_retry_n && (int)(now - klam_retry_at) >= 0) klam_bedcmd(&klam_retry);
        if (gotshot) klam_shot(sf, sv);
        klam_stepfade(now - last); last = now;
        /* mciwrap 1023: re-read AFTER the commands above. klam_open (an MCI 'open', slow: tens to hundreds of ms) stamps p->started with GetTickCount()
           LATER than the 'now' read at the top of this pass; klam_poll then computed now - started as a negative DWORD (~49 days), which closed every
           fresh one-shot at once through the 300000 ms safety test (same bug as klstinger.c), and made the bed look 1500 ms old. fades keep the old now. */
        now = GetTickCount();
        if (now - lastp >= 250) { lastp = now; klam_poll(now); }
    }
}

/* ---------------------------------------------------------------- the game thread (reads the round, posts) */

#ifndef KLAMBIENCE_TEST

enum { KLAM_G_RADIO, KLAM_G_ALARM, KLAM_G_HELI, KLAM_G_DISTANT, KLAM_G_SIREN, KLAM_G_SPOT, KLAM_G_LOCAL, KLAM_G_PANIC, KLAM_NG };
enum { KLAM_P_CALM, KLAM_P_ACTION, KLAM_P_ESCAPE, KLAM_P_DEAD };
static const struct { const char *name; int min, max, from, after, vol; } klam_gdef[KLAM_NG] = {
    { "Radio",   40,  90, KLAM_P_ACTION,  60, 55 },
    { "Alarm",    0,   0, KLAM_P_ACTION,   0, 70 },
    { "Heli",   150, 300, KLAM_P_ACTION,  90, 70 },
    { "Distant", 30,  80, KLAM_P_ACTION,  10, 55 },
    { "Siren",   60, 150, KLAM_P_ACTION,  30, 60 },
    { "Spot",    45, 120, KLAM_P_CALM,    15, 55 },
    /* sound3 (2026-10-23): two more groups, empty unless a map's section names a list (so the old behaviour is the default).
       Local = the map's own sounds (trains, phones, ships, tools...), Panic = civilians / crowd once it is loud. */
    { "Local",   25,  70, KLAM_P_CALM,    10, 55 },
    { "Panic",   40, 110, KLAM_P_ACTION,  20, 50 },
};

struct klam_grp { int n, min, max, from, after, vol, fired; DWORD next; char f[KLAM_MAXF][KLAM_PATH]; };

static struct {
    int on, vol, bedvol, fade, action_after, enabled, round, bedforce, phase, last_phase, bed_on, shots_live;
    char folder[KLAM_PATH], skip[200], map[40], bed[KLAM_PATH];
    struct klam_grp g[KLAM_NG];
    DWORD t_round, t_last, t_fail, rules0, money0; BYTE stage0[KLB_NREC];
    struct { int n; char f[KLAM_MAXF][KLAM_PATH]; } bedlist;
} klam;
static DWORD klam_seed = 777;

static int klam_rand(int n) { klam_seed = klam_seed * 1103515245u + 12345u; return n > 0 ? (int)((klam_seed >> 16) % (unsigned)n) : 0; }

static int klam_str(const char *key, const char *def, char *out, int cap)
{   /* [Ambience.<map>] first, then [Ambience] */
    char s2[64];
    if (klam.map[0]) {
        snprintf(s2, sizeof s2, "Ambience.%s", klam.map);
        GetPrivateProfileStringA(s2, key, "\x01", out, cap, klh_ini);
        if (out[0] != 1) return 1;
    }
    GetPrivateProfileStringA("Ambience", key, "\x01", out, cap, klh_ini);
    if (out[0] == 1) { snprintf(out, cap, "%s", def); return 0; }
    return 1;
}
static int klam_int(const char *key, int def)
{
    char b[40]; klam_str(key, "", b, sizeof b);
    return b[0] ? atoi(b) : def;
}

static int klam_parse(char (*f)[KLAM_PATH], const char *text, const char *what)
{   /* "a.mp3;b.mp3" -> paths below Folder (a full path stays); a missing file is dropped with a log line */
    char buf[2048], *p, *e; int n = 0;
    snprintf(buf, sizeof buf, "%s", text);
    for (p = buf; *p && n < KLAM_MAXF; p = e ? e + 1 : p + strlen(p)) {
        char full[KLAM_PATH]; e = strchr(p, ';'); if (e) *e = 0;
        while (*p == ' ') p++;
        { int k = (int)strlen(p); while (k > 0 && (p[k - 1] == ' ' || p[k - 1] == '\r')) p[--k] = 0; }
        if (!*p || strchr(p, '"')) { if (!e) break; continue; }
        if (p[1] == ':' || p[0] == 0x5c) snprintf(full, sizeof full, "%s", p);
        else snprintf(full, sizeof full, "%s%s%s", klam.folder, klam.folder[0] && klam.folder[strlen(klam.folder) - 1] != 0x5c ? "\\" : "", p);
        if (GetFileAttributesA(full) == INVALID_FILE_ATTRIBUTES) { klog("ambience: %s: '%s' is not there - dropped", what, full); if (!e) break; continue; }
        snprintf(f[n++], KLAM_PATH, "%s", full);
        if (!e) break;
    }
    return n;
}

static int klam_phase_of(const char *s)
{
    if (!_stricmp(s, "calm")) return KLAM_P_CALM;
    if (!_stricmp(s, "escape")) return KLAM_P_ESCAPE;
    if (!_stricmp(s, "dead")) return KLAM_P_DEAD;
    return KLAM_P_ACTION;
}

static void klam_loadmap(void)
{
    char b[2048], k[48]; int g;
    klam_str("Folder", "", klam.folder, sizeof klam.folder);
    klam.enabled = klam_int("Enable", 1) != 0;
    klam.vol = klam_int("Volume", 60); if (klam.vol < 0) klam.vol = 0; if (klam.vol > 100) klam.vol = 100;
    klam.bedvol = klam_int("BedVol", 45); if (klam.bedvol < 0) klam.bedvol = 0; if (klam.bedvol > 100) klam.bedvol = 100;
    klam.fade = klam_int("Fade", 2500); if (klam.fade < 200) klam.fade = 200; if (klam.fade > 20000) klam.fade = 20000;
    klam.action_after = klam_int("ActionAfter", 45);
    klam.bedforce = klam_int("BedForce", 0) != 0;
    klam_str("BedSkip", "DM09,DM06B,DM03A,DM05A", klam.skip, sizeof klam.skip);
    klam_str("Bed", "", b, sizeof b); klam.bedlist.n = klam_parse(klam.bedlist.f, b, "Bed");
    klam.bed[0] = 0;
    if (klam.bedlist.n && (!klmu_inlist(klam.skip, klam.map) || klam.bedforce)) snprintf(klam.bed, sizeof klam.bed, "%s", klam.bedlist.f[klam_rand(klam.bedlist.n)]);
    for (g = 0; g < KLAM_NG; g++) {
        struct klam_grp *G = &klam.g[g]; const char *nm = klam_gdef[g].name;
        klam_str(nm, "", b, sizeof b); G->n = klam_parse(G->f, b, nm);
        snprintf(k, sizeof k, "%sMin", nm);   G->min = klam_int(k, klam_gdef[g].min);
        snprintf(k, sizeof k, "%sMax", nm);   G->max = klam_int(k, klam_gdef[g].max);
        snprintf(k, sizeof k, "%sAfter", nm); G->after = klam_int(k, klam_gdef[g].after);
        snprintf(k, sizeof k, "%sVol", nm);   G->vol = klam_int(k, klam_gdef[g].vol); if (G->vol > 100) G->vol = 100; if (G->vol < 0) G->vol = 0;
        snprintf(k, sizeof k, "%sFrom", nm);  klam_str(k, "", b, sizeof b); G->from = b[0] ? klam_phase_of(b) : klam_gdef[g].from;
        if (G->max < G->min) G->max = G->min;
        G->fired = 0; G->next = 0;
    }
    klog("ambience: map %s: bed %s, radio %d / alarm %d / heli %d / distant %d / siren %d / spot %d / local %d / panic %d clips, volume %d%s", klam.map[0] ? klam.map : "?",
         klam.bed[0] ? klam_base(klam.bed) : "none", klam.g[0].n, klam.g[1].n, klam.g[2].n, klam.g[3].n, klam.g[4].n, klam.g[5].n, klam.g[6].n, klam.g[7].n, klam.vol,
         klam.enabled ? "" : " (this map is switched off)");
}

static void klam_postbed(const char *bed, int stop)
{
    EnterCriticalSection(&klam_cs);
    klam_cmd.stop = stop; if (stop) klam_qh = klam_qt;                /* drop queued one-shots too */
    klam_cmd.seq++; klam_cmd.vol = klam.vol; klam_cmd.fade = klam.fade; klam_cmd.bedvol = klam.bedvol;
    snprintf(klam_cmd.bed, sizeof klam_cmd.bed, "%s", bed ? bed : "");
    LeaveCriticalSection(&klam_cs);
    SetEvent(klam_ev);
}

static void klam_fire(int g)
{
    struct klam_grp *G = &klam.g[g]; const char *f = G->f[klam_rand(G->n)]; int nt;
    EnterCriticalSection(&klam_cs);
    nt = (klam_qt + 1) % KLAM_QN;
    if (nt != klam_qh) { snprintf(klam_q[klam_qt].f, KLAM_PATH, "%s", f); klam_q[klam_qt].vol = G->vol; klam_qt = nt; }
    LeaveCriticalSection(&klam_cs);
    SetEvent(klam_ev);
    if (klam_log) klog("ambience: %s %s (map %s, round second %lu)", klam_gdef[g].name, klam_base(f), klam.map, (unsigned long)((KLB_T(GetTickCount()) - klam.t_round) / 1000));
}

static void klam_off(void)
{   /* no round / silent state: stop the bed once */
    if (klam.bed_on || klam.shots_live) { klam.bed_on = klam.shots_live = 0; klam_postbed(0, 1); }
    klam.round = 0;
}

static void klam_tick(int game_thread)
{
    DWORD now = GetTickCount(), money = 0; struct klb_snap s; char key[40]; int i, ph, g;
    if (!klam.on || !game_thread || !klh_exe_ok || now - klam.t_last < 250) return;
    klam.t_last = now;
    if (kl_online()) { klam_off(); return; }
    klmu_mapkey(key, sizeof key);
    if (strcmp(key, klam.map)) { snprintf(klam.map, sizeof klam.map, "%s", key); klam_off(); if (key[0]) klam_loadmap(); }
    if (!klam.map[0] || !klam.enabled) { klam_off(); return; }
    if (!klb_read(&s)) {
        if (!klam.t_fail) klam.t_fail = KLB_T(now);
        if (now - klam.t_fail > 1500) klam_off();
        return;
    }
    klam.t_fail = 0;
    if (s.state != KLB_ROUND) { klam_off(); return; }
    for (i = 0; i < s.n; i++) if (s.r[i].used) money += s.r[i].money;
    if (!klam.round || s.rules != klam.rules0) {                 /* a round began */
        klam.round = 1; klam.rules0 = s.rules; klam.t_round = KLB_T(now); klam.money0 = money; klam.phase = KLAM_P_CALM; klam.last_phase = -1;
        for (g = 0; g < KLAM_NG; g++) { klam.g[g].fired = 0; klam.g[g].next = 0; }
        if (klam.bedlist.n && (!klmu_inlist(klam.skip, klam.map) || klam.bedforce)) snprintf(klam.bed, sizeof klam.bed, "%s", klam.bedlist.f[klam_rand(klam.bedlist.n)]);
        klam_postbed(klam.bed, 1); klam.bed_on = klam.bed[0] != 0;
    }
    if (now - klam.t_round < 8000u) {                            /* grace: money and stage are re-baselined (as klmusic.c) */
        klam.money0 = money;
        for (i = 0; i < s.n && i < KLB_NREC; i++) klam.stage0[i] = s.r[i].used ? s.r[i].stage : 0;
    }
    ph = klam.phase;
    if (ph < KLAM_P_ACTION) {
        int act = money > klam.money0 || (klam.action_after > 0 && now - klam.t_round >= (DWORD)klam.action_after * 1000u);
        for (i = 0; i < s.n && i < KLB_NREC && !act; i++) if (s.r[i].used && s.r[i].stage >= 1 && s.r[i].stage > klam.stage0[i]) act = 1;
        if (act) ph = KLAM_P_ACTION;
    }
    if (ph < KLAM_P_ESCAPE) {
        int esc = s.veh >= 3 && s.veh <= 5;
        for (i = 0; i < s.n && !esc; i++) if (s.r[i].used && s.r[i].stage >= 2) esc = 1;
        if (!esc && s.human >= 0 && s.r[s.human].status == 4) esc = 1;
        if (esc) ph = KLAM_P_ESCAPE;
    }
    klam.phase = ph;
    if (ph != klam.last_phase) { klam.last_phase = ph; if (klam_log) klog("ambience: phase %d on %s", ph, klam.map); }
    { int dead = s.human >= 0 && s.r[s.human].status == 7;
      for (g = 0; g < KLAM_NG; g++) {
        struct klam_grp *G = &klam.g[g]; int ok;
        if (!G->n) continue;
        ok = G->from == KLAM_P_DEAD ? dead : ph >= G->from;
        if (!ok || now - klam.t_round < (DWORD)G->after * 1000u) { G->next = 0; continue; }
        if (G->max <= 0) {                                        /* once: 1.5 s after the phase is reached */
            if (G->fired) continue;
            if (!G->next) G->next = now + 1500;
        } else if (!G->next) G->next = now + (DWORD)(G->min + klam_rand(G->max - G->min + 1)) * 1000u;
        if ((int)(now - G->next) >= 0) {
            klam_fire(g); klam.shots_live = 1; G->fired++;
            G->next = G->max > 0 ? now + (DWORD)(G->min + klam_rand(G->max - G->min + 1)) * 1000u : 0;
        }
      }
    }
}

static void klam_init(void)
{
    klam.on = GetPrivateProfileIntA("Ambience", "Enable", 0, klh_ini) != 0;
    if (!klam.on) return;
    klam_log = GetPrivateProfileIntA("Ambience", "Log", 1, klh_ini) != 0;
    if (GetPrivateProfileIntA("Solo", "Enable", 0, klh_ini) && !GetPrivateProfileIntA("Ambience", "SoloPlay", 0, klh_ini)) {
        klam.on = 0; klog("ambience: [Solo] bench on and [Ambience] SoloPlay=0 - this instance stays silent"); return;
    }
    klam.last_phase = -1;
    InitializeCriticalSection(&klam_cs);
    klam_ev = CreateEventA(0, FALSE, FALSE, 0);
    klam_seed ^= GetTickCount();
    klam_pump = GetPrivateProfileIntA("KLHook", "MciPump", 0, klh_ini) != 0;
    CloseHandle(CreateThread(0, 0, klam_thread, 0, 0, 0));
    klog("ambience: on (winmm MCI on a worker thread; a bed + timed one-shots from the round state; silent online / with [Solo] unless SoloPlay)");
}

#endif /* !KLAMBIENCE_TEST */

#endif /* KLAMBIENCE_C */
