/*
 * klmusic.c - [Music]: a jukebox for the Fragile Alliance round (2026-10-23, track music; owner: music on every FA map).
 * Part of KLHook (included by klhook.c after klnetsmooth.c, SHIP and TEST alike). Off unless [Music] Enable=1.
 *
 * WHY: the 9 stock FA maps (F01..F09) have no music at all (no ZPlayMusic node, settings field 157 = 0), and the Dead Men maps
 * carry music only where a level builder wired it (Retomoto DM09, Park II DM06B, Vault DM03A, Last Call DM05A: the engine's own).
 * Engine-side music needs a rebuilt sound bank per map and PC_Def.str; this part needs nothing in the game's files. It plays
 * MP3 files of the owner's own PAYDAY 2 soundtrack IN PLACE (never copied, never in the repo) through Windows MCI
 * (winmm 'mpegvideo', loaded at run time, so the DLL gains no import and the build line does not change).
 *
 * THREADS: every MCI call is made by ONE worker thread of our own (klmu_thread). The game thread (klmu_tick, 250 ms) only reads
 * the round and posts a command (mood + playlists) under a lock; it never waits for the worker and never touches MCI.
 * CROSSFADE: two MCI aliases (kmua / kmub). A new track opens on the idle alias at volume 0, plays, and the levels of both
 * ramp (setaudio volume) over Fade ms; the old alias is closed when it reached 0. The same is used between two tracks of one
 * mood (the next track starts Fade ms before the end of the playing one) and for a mood change.
 *
 * THE CUES (the round state is the one klbot.c's klb_read gives: Arcade/FA offline, rules ZGameRulesHeist):
 *   NONE    no round: frontend, level load, pre-round state, an online session (kl_online()), a map with engine music, [Solo] bench
 *   CALM    state 0x19 (round runs) until ACTION
 *   ACTION  any heister's heist stage >= 1 (entered the bank), or the crew's money rose since the round began (loot / pay),
 *           or ActionAfter seconds passed since the round began (a FA round starts inside the job; GUESS: it is loud within a minute)
 *   ESCAPE  the escape vehicle is waiting / arriving (rules+0x1dc in 3..5, klbot.c), or a heister's stage >= 2, or YOU aboard (status 4)
 *   DOWN    YOU are dead (your record's status 7, klbot.c); falls back to the base mood when [Music] Down is empty
 *   END     the session state left 0x19 after a round: the Stinger once (if set), then silence
 *   Moods only climb inside a round (CALM -> ACTION -> ESCAPE); a new round (state 0x19 again) starts at CALM. A police signal does NOT
 *   exist here: the actor's team field offset is not known (klcensus.c), so police arrival is not a cue (loot / stage / time stand in).
 *
 * MAPS: the map key is the redirected map's folder (klmv_pm_folder, KLJoin.ini folder, e.g. DM09) or, on a stock slot, F01..F09.
 *   [Music.<key>] overrides any key below (Enable, Volume, Fade, Calm, Action, Escape, Down, Stinger, StingerOn, Force, ActionAfter).
 *   A key in [Music] EngineMaps (default DM09,DM06B,DM03A,DM05A: Retomoto, Park II, Vault, Last Call) plays nothing unless that map
 *   has Force=1 (the engine's own music would run beside it).
 *
 * ONLINE: kl_online() ([Net] OnlineSafe) -> silent and no cue (a network round's state is another object); the part reads only.
 * [Solo] bench: two kl2.exe on one PC would play two jukeboxes; with [Solo] Enable=1 in the SAME ini the part stays silent unless
 *   [Music] SoloPlay=1 (set it in one instance's ini only).
 * VOLUME: the game's music slider is not read (its field is not known): [Music] Volume 0..100 is the only level (GUESS: MCI volume
 *   is linear in 0..1000; the Windows mixer volume of the process applies on top). Nothing ducks for speech.
 *
 * KLHook.ini
 *   [Music]
 *   Enable=0          1 = on
 *   Volume=60         0..100
 *   Fade=3000         crossfade length, ms (200..20000)
 *   Folder=           folder of the track files (a name below that is not a full path is looked up here)
 *   FolderB=          a second folder to look in (the B-Sides)
 *   Calm= Action= Escape= Down= Stinger=   semicolon lists of file names ("01_Mayhem.mp3;02_Master_plan.mp3"); a mood with an
 *                     empty list uses the lower one (ESCAPE -> ACTION -> CALM; CALM -> ACTION); Stinger is a one-shot track
 *   Assault=          (sound3) list for the ASSAULT mood, played on top of ACTION once a trigger below fires; empty = no ASSAULT mood.
 *                     There is no police signal, so three stand-in triggers (GUESS), each off by default (0):
 *   AssaultAfter=0    seconds after ACTION began
 *   AssaultOnDown=0   1 = a crew record that was not dead at ACTION start gets status 7
 *   AssaultMoney=0    the crew gained this much since ACTION began
 *   (StingerOn= also accepts "assault")
 *   StingerOn=down,end   where the Stinger leads: any of action, escape, down, end
 *   ActionAfter=45    seconds after the round began that CALM ends by itself (0 = only loot / stage end it)
 *   Random=1          a mood's list starts at a random track (then in order)
 *   EngineMaps=DM09,DM06B,DM03A,DM05A    maps with engine music (silent unless Force=1 in their [Music.<key>])
 *   SoloPlay=0
 *   Log=1             one log line a mood change / track start ('music: ...')
 */
#ifndef KLMUSIC_C
#define KLMUSIC_C

enum { KLMU_NONE, KLMU_CALM, KLMU_ACTION, KLMU_ESCAPE, KLMU_DOWN, KLMU_END, KLMU_ASSAULT, KLMU_NMOOD };   /* ASSAULT (sound3, 2026-10-23) sits on top of ACTION: never a "base" */
static const char *const klmu_mname[KLMU_NMOOD] = { "NONE", "CALM", "ACTION", "ESCAPE", "DOWN", "END", "ASSAULT" };
#define KLMU_MAXTR  32
#define KLMU_PATH   260

struct klmu_list { int n; char f[KLMU_MAXTR][KLMU_PATH]; };

/* ---------------------------------------------------------------- the worker (MCI) */

typedef DWORD (WINAPI *klmu_send_fn)(LPCSTR, LPSTR, UINT, HWND);
typedef BOOL  (WINAPI *klmu_err_fn)(DWORD, LPSTR, UINT);

struct klmu_cmd_t { int seq, mood, vol, fade, rnd; struct klmu_list pl, lead; };
static struct klmu_cmd_t klmu_cmd;                 /* posted by the game thread, read by the worker, both under klmu_cs */
static CRITICAL_SECTION klmu_cs;
static HANDLE klmu_ev;
static int klmu_log = 1, klmu_started;

struct klmu_slot { int open, level, target; DWORD started; int len; char al[8], file[KLMU_PATH]; };
static struct klmu_slot klmu_sl[2];
static int klmu_cur = -1, klmu_idx, klmu_master = 60, klmu_fade = 3000, klmu_oneshot, klmu_wmood, klmu_nerr;
static struct klmu_list klmu_wpl, klmu_wlead;       /* the worker's copy of the playlist and the lead (stinger) */
static klmu_send_fn klmu_send; static klmu_err_fn klmu_errs;
static DWORD klmu_seed = 12345;

static int klmu_rand(int n) { klmu_seed = klmu_seed * 1103515245u + 12345u; return n > 0 ? (int)((klmu_seed >> 16) % (unsigned)n) : 0; }

static int klmu_mci(char *ret, int rl, const char *fmt, ...)
{
    char cmd[700]; va_list a; DWORD e;
    va_start(a, fmt); _vsnprintf(cmd, sizeof cmd - 1, fmt, a); va_end(a); cmd[sizeof cmd - 1] = 0;
    if (ret && rl) ret[0] = 0;
    if (!klmu_send) return 0;
    e = klmu_send(cmd, ret, ret ? (UINT)rl : 0, 0);
    if (e) {
        char m[200] = "?";
        if (klmu_errs) klmu_errs(e, m, sizeof m);
        if (klmu_nerr++ < 30) klog("music: MCI '%.150s' failed (%lu): %s", cmd, (unsigned long)e, m);
        return 0;
    }
    return 1;
}

static void klmu_setvol(int s)
{   /* master 0..100 x level 0..1000 -> MCI 0..1000 */
    struct klmu_slot *p = &klmu_sl[s];
    if (p->open) klmu_mci(0, 0, "setaudio %s volume to %d", p->al, klmu_master * p->level / 100);
}

static void klmu_close(int s)
{
    struct klmu_slot *p = &klmu_sl[s];
    if (!p->open) return;
    klmu_mci(0, 0, "stop %s", p->al); klmu_mci(0, 0, "close %s", p->al);
    p->open = 0; p->level = p->target = 0;
    if (klmu_cur == s) klmu_cur = -1;
}

static const char *klmu_base(const char *p) { const char *q = strrchr(p, 0x5c); return q ? q + 1 : p; }

static int klmu_start(const char *path, int fade)
{   /* open on the idle alias at volume 0, play, then fade up; the playing one fades down. 1 = started */
    int o = klmu_cur, s = !klmu_sl[0].open ? 0 : !klmu_sl[1].open ? 1 : (o == 0 ? 1 : 0); struct klmu_slot *p = &klmu_sl[s]; char r[64];
    if (p->open) klmu_close(s);                            /* a fade of the one before is still running: cut it */
    snprintf(p->al, sizeof p->al, "kmu%c", 'a' + s);
    if (!klmu_mci(0, 0, "open \"%s\" type mpegvideo alias %s", path, p->al)) return 0;
    p->open = 1; p->level = fade > 0 ? 0 : 1000; p->target = 1000; p->started = GetTickCount();
    snprintf(p->file, sizeof p->file, "%s", path);
    klmu_setvol(s);
    if (!klmu_mci(0, 0, "play %s", p->al)) { klmu_close(s); return 0; }
    klmu_setvol(s);                                        /* some drivers take the volume only once playing */
    p->len = klmu_mci(r, sizeof r, "status %s length", p->al) ? atoi(r) : 0;
    if (o >= 0 && klmu_sl[o].open) { if (fade > 0) klmu_sl[o].target = 0; else klmu_close(o); }
    klmu_cur = s;
    if (klmu_log) klog("music: %s %s (%d s, fade %d ms)", klmu_oneshot ? "stinger" : klmu_mname[klmu_wmood], klmu_base(path), p->len / 1000, fade);
    return 1;
}

static void klmu_fadeout(int fade)
{
    int s;
    for (s = 0; s < 2; s++) if (klmu_sl[s].open) { if (fade > 0) klmu_sl[s].target = 0; else klmu_close(s); }
    klmu_cur = -1;
}

static void klmu_next(int fade)
{   /* the next track: the lead (once), then the list in order; a file that will not open is skipped */
    int tries, n;
    if (klmu_wlead.n > 0) {
        char p[KLMU_PATH]; snprintf(p, sizeof p, "%s", klmu_wlead.f[klmu_rand(klmu_wlead.n)]);
        klmu_wlead.n = 0; klmu_oneshot = 1;
        if (klmu_start(p, fade)) return;
    }
    klmu_oneshot = 0; n = klmu_wpl.n;
    if (n <= 0) { klmu_fadeout(fade); return; }
    for (tries = 0; tries < n; tries++) {
        if (klmu_start(klmu_wpl.f[klmu_idx % n], fade)) { klmu_idx = (klmu_idx + 1) % n; return; }
        klmu_idx = (klmu_idx + 1) % n;
    }
    klog("music: none of the %d tracks of %s would play", n, klmu_mname[klmu_wmood]);
    klmu_fadeout(fade);
}

static void klmu_apply(const struct klmu_cmd_t *c)
{
    int s, fade = c->fade;
    klmu_master = c->vol; klmu_fade = c->fade;
    for (s = 0; s < 2; s++) klmu_setvol(s);
    klmu_wmood = c->mood; klmu_wpl = c->pl; klmu_wlead = c->lead;
    klmu_idx = c->rnd && klmu_wpl.n > 1 ? klmu_rand(klmu_wpl.n) : 0;
    if (c->mood == KLMU_NONE) { klmu_fadeout(fade < 1500 ? fade : 1500); return; }
    klmu_next(fade);
}

static void klmu_stepfade(DWORD dt)
{
    int s, d = klmu_fade > 0 ? (int)(1000u * dt / (DWORD)klmu_fade) + 1 : 1000;
    for (s = 0; s < 2; s++) {
        struct klmu_slot *p = &klmu_sl[s];
        if (!p->open || p->level == p->target) continue;
        if (p->level < p->target) { p->level += d; if (p->level > p->target) p->level = p->target; }
        else { p->level -= d; if (p->level < p->target) p->level = p->target; }
        if (p->level == 0 && p->target == 0) { klmu_close(s); continue; }
        klmu_setvol(s);
    }
}

static void klmu_follow(DWORD now)
{   /* the playing track ended (or is about to): start the next one */
    struct klmu_slot *p; char r[64]; int pos = 0, stopped, more;
    if (klmu_cur < 0) return;
    p = &klmu_sl[klmu_cur];
    if (!p->open || now - p->started < 1500) return;
    more = klmu_wpl.n > 0 || klmu_wlead.n > 0;
    stopped = klmu_mci(r, sizeof r, "status %s mode", p->al) && (!_stricmp(r, "stopped") || !_stricmp(r, "not ready"));
    if (!stopped) {
        if (!more) return;                                          /* nothing follows: let it end by itself */
        if (klmu_mci(r, sizeof r, "status %s position", p->al)) pos = atoi(r);
        if (p->len <= 0 || pos <= 0 || pos + klmu_fade + 300 < p->len) return;
    } else if (!more) { klmu_close(klmu_cur); return; }
    klmu_next(stopped ? 0 : klmu_fade);
}

static DWORD WINAPI klmu_thread(void *u)
{
    int seen = 0; DWORD last = GetTickCount(), lastf = 0; HMODULE m = LoadLibraryA("winmm.dll"); (void)u;
    if (m) { klmu_send = (klmu_send_fn)GetProcAddress(m, "mciSendStringA"); klmu_errs = (klmu_err_fn)GetProcAddress(m, "mciGetErrorStringA"); }
    if (!klmu_send) { klog("music: winmm.dll / mciSendStringA not found - the jukebox stays silent"); return 0; }
    for (;;) {
        DWORD now; struct klmu_cmd_t *c = 0; static struct klmu_cmd_t copy;
        WaitForSingleObject(klmu_ev, 40);
        now = GetTickCount();
        EnterCriticalSection(&klmu_cs);
        if (klmu_cmd.seq != seen) { copy = klmu_cmd; seen = klmu_cmd.seq; c = &copy; }
        LeaveCriticalSection(&klmu_cs);
        if (c) klmu_apply(c);
        klmu_stepfade(now - last); last = now;
        /* mciwrap 1023: re-read AFTER klmu_apply. klmu_start (an MCI 'open', slow) stamps p->started with a GetTickCount() later than the 'now' read at the
           top of this pass, so klmu_follow's now - started < 1500 guard wrapped to ~49 days and let the follow logic run on a track opened this very pass
           (a 'not ready' status right after the open then skipped it with klmu_next(0)). fades keep the old now. */
        now = GetTickCount();
        if (now - lastf >= 250) { lastf = now; klmu_follow(now); }
    }
}

/* ---------------------------------------------------------------- the game thread (reads the round, posts) */

#ifndef KLMUSIC_TEST

#define KLMU_ST_ACTION 1
#define KLMU_ST_ESCAPE 2
#define KLMU_ST_DOWN   4
#define KLMU_ST_END    8
#define KLMU_ST_ASSAULT 16

static struct {
    int on, solo_block, vol, fade, rnd, action_after, force, enabled, st_on, mood_posted, base, round, down;
    int assault, assault_after, assault_down, assault_money; DWORD t_action; BYTE dead0[KLB_NREC];   /* sound3 */
    char folder[KLMU_PATH], folderb[KLMU_PATH], engine[200], map[40];
    struct klmu_list list[KLMU_NMOOD], stinger;            /* list[CALM..DOWN]; list[NONE] and [END] unused */
    DWORD t_round, t_end, t_fail, t_last; DWORD rules0, money0; int told_engine; BYTE stage0[KLB_NREC];
} klmu;

static int klmu_str(const char *sec, const char *key, const char *def, char *out, int cap)
{   /* [Music.<map>] first, then [Music]; def when neither has the key */
    char s2[64];
    if (klmu.map[0]) {
        snprintf(s2, sizeof s2, "Music.%s", klmu.map);
        GetPrivateProfileStringA(s2, key, "\x01", out, cap, klh_ini);
        if (out[0] != 1) return 1;
    }
    GetPrivateProfileStringA(sec, key, "\x01", out, cap, klh_ini);
    if (out[0] == 1) { snprintf(out, cap, "%s", def); return 0; }
    return 1;
}
static int klmu_int(const char *key, int def)
{
    char b[40]; klmu_str("Music", key, "", b, sizeof b);
    return b[0] ? atoi(b) : def;
}

static void klmu_parse(struct klmu_list *l, const char *text, const char *what)
{   /* "a.mp3;b.mp3" -> paths; a bare name is looked up in Folder, then FolderB; a missing file is dropped with a log line */
    char buf[2048], *p, *e; l->n = 0;
    snprintf(buf, sizeof buf, "%s", text);
    for (p = buf; *p && l->n < KLMU_MAXTR; p = e ? e + 1 : p + strlen(p)) {
        char full[KLMU_PATH]; DWORD at; e = strchr(p, ';'); if (e) *e = 0;
        while (*p == ' ') p++;
        { int k = (int)strlen(p); while (k > 0 && (p[k - 1] == ' ' || p[k - 1] == '\r')) p[--k] = 0; }
        if (!*p || strchr(p, '"')) continue;
        if (p[1] == ':' || p[0] == 0x5c) snprintf(full, sizeof full, "%s", p);
        else {
            snprintf(full, sizeof full, "%s%s%s", klmu.folder, klmu.folder[0] && klmu.folder[strlen(klmu.folder) - 1] != 0x5c ? "\\" : "", p);
            if ((at = GetFileAttributesA(full)) == INVALID_FILE_ATTRIBUTES && klmu.folderb[0])
                snprintf(full, sizeof full, "%s%s%s", klmu.folderb, klmu.folderb[strlen(klmu.folderb) - 1] != 0x5c ? "\\" : "", p);
        }
        if (GetFileAttributesA(full) == INVALID_FILE_ATTRIBUTES) { klog("music: %s: '%s' is not there - dropped", what, full); if (!e) break; continue; }
        snprintf(l->f[l->n++], KLMU_PATH, "%s", full);
        if (!e) break;
    }
}

static int klmu_inlist(const char *list, const char *key)
{   /* key in a comma list, case-blind */
    char b[200], *t, *c; snprintf(b, sizeof b, "%s", list);
    for (t = b; t && *t; t = c ? c + 1 : 0) {
        int k; c = strchr(t, ','); if (c) *c = 0;
        while (*t == ' ') t++;
        k = (int)strlen(t); while (k > 0 && t[k - 1] == ' ') t[--k] = 0;
        if (*t && !_stricmp(t, key)) return 1;
    }
    return 0;
}

static void klmu_loadmap(void)
{   /* the lists of [Music] with [Music.<key>] over them; once a map change */
    static const char *const names[] = { 0, "Calm", "Action", "Escape", "Down" };
    char b[2048]; int m;
    klmu_str("Music", "Folder", "", klmu.folder, sizeof klmu.folder);
    klmu_str("Music", "FolderB", "", klmu.folderb, sizeof klmu.folderb);
    klmu.enabled = klmu_int("Enable", 1) != 0;                   /* [Music.<key>] Enable=0 silences one map; [Music] Enable=1 got us here */
    klmu.vol = klmu_int("Volume", 60); if (klmu.vol < 0) klmu.vol = 0; if (klmu.vol > 100) klmu.vol = 100;
    klmu.fade = klmu_int("Fade", 3000); if (klmu.fade < 200) klmu.fade = 200; if (klmu.fade > 20000) klmu.fade = 20000;
    klmu.rnd = klmu_int("Random", 1) != 0;
    klmu.action_after = klmu_int("ActionAfter", 45);
    klmu.force = klmu_int("Force", 0) != 0;
    for (m = KLMU_CALM; m <= KLMU_DOWN; m++) { klmu_str("Music", names[m], "", b, sizeof b); klmu_parse(&klmu.list[m], b, names[m]); }
    /* sound3: the ASSAULT tier. Everything defaults to the old behaviour: no Assault list, or AssaultAfter=0 and AssaultOnDown=0 and
       AssaultMoney=0, means the mood is never posted. */
    klmu_str("Music", "Assault", "", b, sizeof b); klmu_parse(&klmu.list[KLMU_ASSAULT], b, "Assault");
    klmu.assault_after = klmu_int("AssaultAfter", 0);       /* s after ACTION began (0 = off) */
    klmu.assault_down = klmu_int("AssaultOnDown", 0) != 0;  /* a crew record turning status 7 (dead / swapped to police) */
    klmu.assault_money = klmu_int("AssaultMoney", 0);       /* $ the crew gained since ACTION began (0 = off) */
    klmu_str("Music", "Stinger", "", b, sizeof b); klmu_parse(&klmu.stinger, b, "Stinger");
    klmu_str("Music", "StingerOn", "down,end", b, sizeof b);
    klmu.st_on = (klmu_inlist(b, "action") ? KLMU_ST_ACTION : 0) | (klmu_inlist(b, "escape") ? KLMU_ST_ESCAPE : 0) | (klmu_inlist(b, "assault") ? KLMU_ST_ASSAULT : 0) |
                 (klmu_inlist(b, "down") ? KLMU_ST_DOWN : 0) | (klmu_inlist(b, "end") ? KLMU_ST_END : 0);
    klmu_str("Music", "EngineMaps", "DM09,DM06B,DM03A,DM05A", klmu.engine, sizeof klmu.engine);
    klmu.told_engine = 0;
    klog("music: map %s: Calm %d / Action %d / Assault %d / Escape %d / Down %d tracks, stinger %d, volume %d, fade %d ms, assault after %d s / on down %d / money %d%s", klmu.map[0] ? klmu.map : "?",
         klmu.list[KLMU_CALM].n, klmu.list[KLMU_ACTION].n, klmu.list[KLMU_ASSAULT].n, klmu.list[KLMU_ESCAPE].n, klmu.list[KLMU_DOWN].n, klmu.stinger.n, klmu.vol, klmu.fade,
         klmu.assault_after, klmu.assault_down, klmu.assault_money,
         klmu.enabled ? "" : " (this map is switched off)");
}

static void klmu_mapkey(char *key, int cap)
{
    char scene[160], lk[64], f[40]; key[0] = 0;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, lk, sizeof lk)) return;
    klmv_pm_folder(f, sizeof f);
    if (f[0]) snprintf(key, cap, "%s", f);
    else if (lk[0] == 'f' && lk[1] >= '0' && lk[1] <= '9' && lk[2] >= '0' && lk[2] <= '9') snprintf(key, cap, "F%c%c", lk[1], lk[2]);
}

static const struct klmu_list *klmu_pick(int mood)
{   /* the list a mood plays: its own, else the lower one's */
    const struct klmu_list *L = klmu.list;
    switch (mood) {
    case KLMU_ESCAPE: return L[KLMU_ESCAPE].n ? &L[KLMU_ESCAPE] : L[KLMU_ACTION].n ? &L[KLMU_ACTION] : &L[KLMU_CALM];
    case KLMU_ACTION: return L[KLMU_ACTION].n ? &L[KLMU_ACTION] : &L[KLMU_CALM];
    case KLMU_CALM:   return L[KLMU_CALM].n ? &L[KLMU_CALM] : &L[KLMU_ACTION];
    case KLMU_DOWN:   return &L[KLMU_DOWN];
    case KLMU_ASSAULT: return L[KLMU_ASSAULT].n ? &L[KLMU_ASSAULT] : L[KLMU_ACTION].n ? &L[KLMU_ACTION] : &L[KLMU_CALM];
    }
    return &L[KLMU_CALM];
}

static void klmu_post(int mood, int base)
{   /* hand the worker the playlist of a mood (a lead stinger when the mood's flag is set) */
    const struct klmu_list *pl; int stflag = 0;
    EnterCriticalSection(&klmu_cs);
    klmu_cmd.seq++; klmu_cmd.mood = mood; klmu_cmd.vol = klmu.vol; klmu_cmd.fade = klmu.fade; klmu_cmd.rnd = klmu.rnd;
    klmu_cmd.pl.n = 0; klmu_cmd.lead.n = 0;
    if (mood == KLMU_DOWN) { stflag = KLMU_ST_DOWN; pl = klmu.list[KLMU_DOWN].n ? &klmu.list[KLMU_DOWN] : klmu_pick(base); }
    else if (mood == KLMU_END) { stflag = KLMU_ST_END; pl = 0; }
    else { stflag = mood == KLMU_ACTION ? KLMU_ST_ACTION : mood == KLMU_ESCAPE ? KLMU_ST_ESCAPE : mood == KLMU_ASSAULT ? KLMU_ST_ASSAULT : 0; pl = mood == KLMU_NONE ? 0 : klmu_pick(mood); }
    if (pl) klmu_cmd.pl = *pl;
    if ((klmu.st_on & stflag) && klmu.stinger.n) klmu_cmd.lead = klmu.stinger;
    LeaveCriticalSection(&klmu_cs);
    SetEvent(klmu_ev);
    if (klmu_log) klog("music: cue %s on %s (list %d tracks, stinger %s)", klmu_mname[mood], klmu.map[0] ? klmu.map : "?", klmu_cmd.pl.n, klmu_cmd.lead.n ? "yes" : "no");
}

static void klmu_want(int mood, int base)
{
    if (mood == klmu.mood_posted && (mood != KLMU_DOWN || base == klmu.base)) return;
    klmu.mood_posted = mood; klmu.base = base;
    klmu_post(mood, base);
}

static void klmu_tick(int game_thread)
{
    DWORD now = GetTickCount(), money = 0; struct klb_snap s; char key[40]; int i, base, mood;
    if (!klmu.on || !game_thread || !klh_exe_ok || now - klmu.t_last < 250) return;
    klmu.t_last = now;
    if (kl_online()) { klmu.round = 0; klmu_want(KLMU_NONE, 0); return; }
    klmu_mapkey(key, sizeof key);
    if (strcmp(key, klmu.map)) { snprintf(klmu.map, sizeof klmu.map, "%s", key); klmu.round = 0; if (key[0]) klmu_loadmap(); else klmu_want(KLMU_NONE, 0); }
    if (!klmu.map[0]) { klmu_want(KLMU_NONE, 0); return; }
    if (!klmu.enabled) { klmu_want(KLMU_NONE, 0); return; }
    if (klmu_inlist(klmu.engine, klmu.map) && !klmu.force) {
        if (!klmu.told_engine) { klmu.told_engine = 1; klog("music: %s has its own engine music - the jukebox is silent here ([Music.%s] Force=1 plays it anyway)", klmu.map, klmu.map); }
        klmu_want(KLMU_NONE, 0); return;
    }
    if (!klb_read(&s)) {
        if (!klmu.t_fail) klmu.t_fail = KLB_T(now);
        if (now - klmu.t_fail > 1500 && (klmu.mood_posted != KLMU_END || now - klmu.t_end > 20000)) { klmu.round = 0; klmu_want(KLMU_NONE, 0); }
        return;
    }
    klmu.t_fail = 0;
    if (s.state != KLB_ROUND) {
        if (klmu.round) { klmu.round = 0; klmu.t_end = now; klmu_want(KLMU_END, 0); }
        else if (klmu.mood_posted != KLMU_END || now - klmu.t_end > 20000) klmu_want(KLMU_NONE, 0);
        return;
    }
    for (i = 0; i < s.n; i++) if (s.r[i].used) money += s.r[i].money;
    if (!klmu.round || s.rules != klmu.rules0) {                 /* a round began */
        klmu.round = 1; klmu.rules0 = s.rules; klmu.t_round = KLB_T(now); klmu.money0 = money; klmu.base = KLMU_CALM; klmu.down = 0;
        klmu.assault = 0; klmu.t_action = 0;
        klmu.mood_posted = -1;
    }
    /* Grace: for the first 8 s the crew records are still filling in and FA rounds start inside the job (stage 1
       already set by the spawn zones), so money and stage are re-baselined instead of read as cues (review 1023). */
    if (now - klmu.t_round < 8000u) {
        klmu.money0 = money;
        for (i = 0; i < s.n && i < KLB_NREC; i++) { klmu.stage0[i] = s.r[i].used ? s.r[i].stage : 0; klmu.dead0[i] = s.r[i].used && s.r[i].status == 7; }
    }
    base = klmu.base;
    if (base < KLMU_ACTION) {
        int act = money > klmu.money0 || (klmu.action_after > 0 && now - klmu.t_round >= (DWORD)klmu.action_after * 1000u);
        for (i = 0; i < s.n && i < KLB_NREC && !act; i++) if (s.r[i].used && s.r[i].stage >= 1 && s.r[i].stage > klmu.stage0[i]) act = 1;
        if (act) base = KLMU_ACTION;
    }
    if (base < KLMU_ESCAPE) {
        int esc = s.veh >= 3 && s.veh <= 5;
        for (i = 0; i < s.n && !esc; i++) if (s.r[i].used && s.r[i].stage >= 2) esc = 1;
        if (!esc && s.human >= 0 && s.r[s.human].status == 4) esc = 1;
        if (esc) base = KLMU_ESCAPE;
    }
    klmu.base = base;
    mood = base;
    /* sound3: ASSAULT = the shooting got serious. There is no police signal (see the header), so three stand-ins, any of which is
       enough, each off by default: AssaultAfter s since ACTION began; AssaultOnDown = a crew record that was not dead at the baseline now
       has status 7 (a dead heister, or a traitor swapped to a policeman: klbot.c); AssaultMoney = the crew gained that much since ACTION
       began. GUESS: status 7 is "dead / out of play" for every record, not only yours (klbot.c reads it as "he is dead" in the foe skip).
       Sticky for the rest of the round (ESCAPE and DOWN still win; END ends it). money0 is free to reuse here: it only matters while
       base < ACTION. */
    if (base == KLMU_ACTION && !klmu.t_action) {
        klmu.t_action = now ? now : 1; klmu.money0 = money;
        /* review fix: the dead0 baseline was only taken in the first 8 s, but ACTION can start later (timer 45 s): refresh it now so a
           heister who died during CALM does not fire AssaultOnDown on the first ACTION tick. */
        for (i = 0; i < s.n && i < KLB_NREC; i++) klmu.dead0[i] = s.r[i].used && s.r[i].status == 7;
    }
    if (base == KLMU_ACTION && !klmu.assault && klmu.list[KLMU_ASSAULT].n) {
        int as = klmu.assault_after > 0 && now - klmu.t_action >= (DWORD)klmu.assault_after * 1000u;
        if (!as && klmu.assault_money > 0 && money >= klmu.money0 + (DWORD)klmu.assault_money) as = 1;
        for (i = 0; i < s.n && i < KLB_NREC && !as; i++) if (klmu.assault_down && s.r[i].used && s.r[i].status == 7 && !klmu.dead0[i]) as = 1;
        if (as) { klmu.assault = 1; klog("music: ASSAULT trigger on %s (%lu s after ACTION began)", klmu.map, (unsigned long)((now - klmu.t_action) / 1000)); }
    }
    if (base == KLMU_ACTION && klmu.assault) mood = KLMU_ASSAULT;
    if (s.human >= 0 && s.r[s.human].status == 7 && (klmu.list[KLMU_DOWN].n || ((klmu.st_on & KLMU_ST_DOWN) && klmu.stinger.n))) mood = KLMU_DOWN;
    klmu_want(mood, base);
}

static void klmu_init(void)
{
    char b[40];
    klmu.on = GetPrivateProfileIntA("Music", "Enable", 0, klh_ini) != 0;
    if (!klmu.on) return;
    klmu_log = GetPrivateProfileIntA("Music", "Log", 1, klh_ini) != 0;
    if (GetPrivateProfileIntA("Solo", "Enable", 0, klh_ini) && !GetPrivateProfileIntA("Music", "SoloPlay", 0, klh_ini)) {
        klmu.on = 0; klog("music: [Solo] bench on and [Music] SoloPlay=0 - this instance stays silent"); return;
    }
    GetPrivateProfileStringA("Music", "Folder", "", b, sizeof b, klh_ini);
    klmu.mood_posted = -1;
    InitializeCriticalSection(&klmu_cs);
    klmu_ev = CreateEventA(0, FALSE, FALSE, 0);
    klmu_seed ^= GetTickCount();
    CloseHandle(CreateThread(0, 0, klmu_thread, 0, 0, 0));
    klmu_started = 1;
    klog("music: on (winmm MCI on a worker thread; cues from the round state; silent online / on engine-music maps / with [Solo] unless SoloPlay)");
}

#endif /* !KLMUSIC_TEST */

#endif /* KLMUSIC_C */
