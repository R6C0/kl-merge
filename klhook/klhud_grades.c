/*
 * klhud_grades.c - [Grades] RANK badges, RANK UP line and end-of-round letter GRADE (2026-10-27, track GRADES). Badge proven online on bench GRT3 10-27 (Steam XP 568 -> rank 3 Thug, both seats); RankUp / Letter not yet seen live.
 * Research, formula, ranks and names: re\grades.md; the pure rules are klgrades.h (off-game test klgrades_test.c).
 *
 *   [Grades] Enable=0      master switch (default 0 until benched)
 *            Badge=0       a rank badge before every crew name: the crew list (Arcade and online) and the round-over card's rows
 *            RankUp=0      "RANK UP: <rank>" on the round-over card (klhud_board2.c) when a player's rank rose during the round
 *            Letter=0      a GRADE column on the round-over card: S / A / B / C / D per player, from the formula in klgrades.h
 *            BadgeStyle=0  0 = "R5" (the game's own numbering, Rank 1 = Mastermind ... Rank 8 = Mugger), 1 = "[THUG]"
 *            NameSet=0     0 = Dog Days' criminal rank names, 1 = Dead Men's Seven (Kane at the top)
 *            Source=0      ONLINE seats other than yours: 0 = from S+0xc8 Experience (GUESS) through the thresholds, 1 = S+0x17c Rating as the rank (GUESS)
 *            BotRank=-1    rank 0..7 shown for AI heisters (Arcade and online); -1 = no badge for bots (nobody knows their rank)
 *            Probe=0       LOG ONLY: once per 5 s every online seat's raw Experience / Rating, so a bench decides Source
 *            Thr1..Thr7    experience for rank 1..7 (game: 25 100 400 700 1500 2100 2800)
 *            KillPts PolicePts LootPts RewardPts EscapePts DeadPts TraitorPts FedPts LootUnit RewardUnit LootCap CutS CutA CutB CutC  the grade table (klgrades.h)
 *
 * WHERE THE RANK COMES FROM (experience -> rank = the game's 0x5103e0, as a table here so a changed table is a change of the ini)
 *   - YOU, Arcade and online: the local profile's FA experience, the shop's own chain (klhire.c, kl2.exe 0x7f74a0..0x7f74d1): [0x1686e60+0xc][0]
 *     -> vtable+0x140 -> profile -> profile+0x15b8+0x90 (u16). Read once a second on the game thread, code bytes checked first; unreadable = no badge.
 *   - the others online: S+0xc8+2*seat (GUESS: the field named Experience, i16). Shown only after some seat's value was above 0 this session
 *     (evidence that the server fills it), else no badge rather than eight Muggers.
 *   - Arcade bots: no profile, no rank: nothing unless BotRank is set.
 *   - GUESS: the profile experience already includes the round when the end card shows (it rises when the round is scored). If it rises
 *     later the RANK UP line simply does not appear; the Probe / log lines say what happened.
 * RANK UP: ranks are latched per seat in states 0x16..0x19 (the round) and compared in state 0x1f; cleared in states >= 0x20 and < 0x16.
 * Reads and one char formatting only: no game write, no .text patch (SHIP-safe). Included by klhook.c after klonline_read.c.
 */
#ifndef KLHUD_GRADES_C
#define KLHUD_GRADES_C

#include "klgrades.h"

#define KLGRD_SESSIONOBJ 0x01686e60u            /* the profile manager (klhire.c KLHR_SESSIONOBJ) */
#define KLGRD_GETOBJ     0x004d04c0u            /* thiscall(obj, int) ret 4: [[obj+0xc] + 4*i] */
#define KLGRD_VT_PROFILE 0x140                  /* vtable slot: the profile data, no arguments */
#define KLGRD_PROF_XP    (0x15b8 + 0x90)        /* profile + 0x15b8 + player 0 * 0xc8, word +0x90 = FA experience */
#define KLGRD_MAXI       32
/* the stat name the game passes to ISteamUserStats::GetStat / SetStat for the FA experience: 'ExperiencePoints_FA' is in the SetStat lines of
   a live session end (re\fa_round.md:636, re\leaderboard.md 78) - the game's own profile field name; not re-read from the exe's string table here */
#define KLGRD_STEAM_STAT "ExperiencePoints_FA"
static int klx_get_stat_int(const char *name, int *v);      /* klsteam.c (included later): the REAL GetStat through the proxy's saved interface, read only */

static struct {
    int on, badge, rankup, letter, style, set, source, botrank, probe, otags;
    struct klgrd_cfg c;
    int local_xp, local_ok, local_told, local_bad; DWORD local_at;
    int steamxp, local_src, steam_xp, steam_ok, steam_told, steam_failtold; DWORD steam_at;     /* [Grades] SteamXP: the local seat's xp from the Steam stat when the profile reads 0 (read only) */
    int oxp[KLGRD_MAXI], orate[KLGRD_MAXI], o_ok[KLGRD_MAXI]; int o_live;           /* online S values per seat; o_live: a nonzero experience was seen */
    int base[KLGRD_MAXI], base_ok[KLGRD_MAXI], cur[KLGRD_MAXI], cur_loc[KLGRD_MAXI];
    int told_up;
} klgrd;

static int klgrd_ini(const char *key, int def, int lo, int hi)
{
    int v = (int)GetPrivateProfileIntA("Grades", key, def, klh_ini);
    return v < lo ? lo : v > hi ? hi : v;
}

static void klgrd_init(void)
{
    static const char *const thr[7] = { "Thr1", "Thr2", "Thr3", "Thr4", "Thr5", "Thr6", "Thr7" };
    int i;
    memset(&klgrd, 0, sizeof klgrd);
    klgrd_defaults(&klgrd.c);
    klgrd.on = klgrd_ini("Enable", 0, 0, 1);
    if (!klgrd.on) return;
    klgrd.badge = klgrd_ini("Badge", 0, 0, 1); klgrd.rankup = klgrd_ini("RankUp", 0, 0, 1); klgrd.letter = klgrd_ini("Letter", 0, 0, 1);
    klgrd.style = klgrd_ini("BadgeStyle", 0, 0, 1); klgrd.set = klgrd_ini("NameSet", 0, 0, 1); klgrd.source = klgrd_ini("Source", 0, 0, 1);
    klgrd.steamxp = klgrd_ini("SteamXP", 0, 0, 1);
    klgrd.botrank = klgrd_ini("BotRank", -1, -1, 7); klgrd.probe = klgrd_ini("Probe", 0, 0, 1); klgrd.otags = klgrd_ini("OnlineTags", 0, 0, 1);
    for (i = 0; i < 7; i++) klgrd.c.thr[i] = klgrd_ini(thr[i], klgrd.c.thr[i], 0, 30000);
    for (i = 1; i < 7; i++) if (klgrd.c.thr[i] < klgrd.c.thr[i - 1]) { klog("grades: Thr%d < Thr%d: the table is not rising, the defaults are used", i + 1, i); klgrd_defaults(&klgrd.c); break; }
    klgrd.c.w_kill = klgrd_ini("KillPts", klgrd.c.w_kill, -50, 50); klgrd.c.w_police = klgrd_ini("PolicePts", klgrd.c.w_police, -50, 50);
    klgrd.c.w_loot = klgrd_ini("LootPts", klgrd.c.w_loot, -50, 50); klgrd.c.w_reward = klgrd_ini("RewardPts", klgrd.c.w_reward, -50, 50);
    klgrd.c.w_escape = klgrd_ini("EscapePts", klgrd.c.w_escape, -50, 50); klgrd.c.w_dead = klgrd_ini("DeadPts", klgrd.c.w_dead, -50, 50);
    klgrd.c.w_traitor = klgrd_ini("TraitorPts", klgrd.c.w_traitor, -50, 50); klgrd.c.w_fed = klgrd_ini("FedPts", klgrd.c.w_fed, -50, 50);
    klgrd.c.lootunit = klgrd_ini("LootUnit", klgrd.c.lootunit, 1000, 10000000); klgrd.c.rewunit = klgrd_ini("RewardUnit", klgrd.c.rewunit, 1000, 10000000);
    klgrd.c.lootcap = klgrd_ini("LootCap", klgrd.c.lootcap, 0, 100);
    klgrd.c.cut[0] = klgrd_ini("CutS", klgrd.c.cut[0], -50, 500); klgrd.c.cut[1] = klgrd_ini("CutA", klgrd.c.cut[1], -50, 500);
    klgrd.c.cut[2] = klgrd_ini("CutB", klgrd.c.cut[2], -50, 500); klgrd.c.cut[3] = klgrd_ini("CutC", klgrd.c.cut[3], -50, 500);
    if (!(klgrd.c.cut[0] >= klgrd.c.cut[1] && klgrd.c.cut[1] >= klgrd.c.cut[2] && klgrd.c.cut[2] >= klgrd.c.cut[3])) {
        klog("grades: the letter cut-offs S >= A >= B >= C are not in order: the defaults are used");
        klgrd.c.cut[0] = 14; klgrd.c.cut[1] = 10; klgrd.c.cut[2] = 6; klgrd.c.cut[3] = 3;
    }
    for (i = 0; i < KLGRD_MAXI; i++) klgrd.base[i] = klgrd.cur[i] = -1;
    klog("grades: on (Badge=%d RankUp=%d Letter=%d style %d names %s source %s BotRank=%d Probe=%d; thresholds %d %d %d %d %d %d %d; letter cuts S%d A%d B%d C%d); badge benched GRT3 10-27",
         klgrd.badge, klgrd.rankup, klgrd.letter, klgrd.style, klgrd.set ? "Dead Men" : "Dog Days", klgrd.source ? "Rating" : "Experience", klgrd.botrank, klgrd.probe,
         klgrd.c.thr[0], klgrd.c.thr[1], klgrd.c.thr[2], klgrd.c.thr[3], klgrd.c.thr[4], klgrd.c.thr[5], klgrd.c.thr[6], klgrd.c.cut[0], klgrd.c.cut[1], klgrd.c.cut[2], klgrd.c.cut[3]);
}

/* the local profile's FA experience, the shop's chain (klhire.c klhr_rank without the final call). Game thread only: it calls two game functions. -> 1 = *xp valid */
static int klgrd_read_local_xp(int *xp)
{
    static const BYTE get_code[10] = { 0x8b, 0x41, 0x0c, 0x85, 0xc0, 0x75, 0x03, 0xc2, 0x04, 0x00 };          /* 0x4d04c0 mov eax,[ecx+0xc] ; test ; jne ; ret 4 */
    DWORD obj = (DWORD)(DWORD_PTR)KLH_VA(KLGRD_SESSIONOBJ), p, vt, fn, prof, w = 0;
    if (!klc_same_code(KLGRD_GETOBJ, get_code, sizeof get_code)) return 0;
    if (!klh_rd32(obj + 0xc)) return 0;
    p = ((DWORD (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLGRD_GETOBJ))((void *)(DWORD_PTR)obj, 0, 0);
    if (!p || p < 0x10000 || !(vt = klh_rd32(p)) || !(fn = klh_rd32(vt + KLGRD_VT_PROFILE))) return 0;
    if (fn < (DWORD)(DWORD_PTR)KLH_VA(0x401000) || fn >= (DWORD)(DWORD_PTR)KLH_VA(0xb00000)) return 0;      /* inside the exe's code */
    prof = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)fn)((void *)(DWORD_PTR)p, 0);
    if (!prof || prof < 0x10000 || !klh_rd(prof + KLGRD_PROF_XP, &w, 2)) return 0;
    *xp = (int)(w & 0xffff);
    return 1;
}

static void klgrd_tick(int game_thread)
{   /* once a second, on the game thread: the local experience */
    DWORD now = GetTickCount(); int xp = 0, ok;
    if (!klgrd.on || !(klgrd.badge || klgrd.rankup) || !game_thread) return;
    if (klgrd.local_at && now - klgrd.local_at < (klgrd.local_bad >= 5 ? 10000u : 1000u)) return;      /* review: was 'give up after 5 failures' = for good, though the profile manager is not up for the first seconds; now it retries every 10 s */
    klgrd.local_at = now ? now : 1;
    ok = klgrd_read_local_xp(&xp);
    klgrd.local_src = 0;
    if (klgrd.steamxp && (!ok || xp == 0)) {                 /* [Grades] SteamXP: a bench skips ZPressStart, the profile reads 0 (or is not built): ask Steam, read only, cached */
        int sx = 0;
        if (klgrd.steam_at && now - klgrd.steam_at < 5000u) { if (klgrd.steam_ok) { sx = klgrd.steam_xp; ok = 1; xp = sx; klgrd.local_src = 1; } }
        else {
            klgrd.steam_at = now ? now : 1;
            if (klx_get_stat_int(KLGRD_STEAM_STAT, &sx)) {
                klgrd.steam_ok = 1; klgrd.steam_xp = sx;
                if (!klgrd.steam_told) { klgrd.steam_told = 1; klog("grades: local xp %d from Steam stat '%s' (profile read %d)", sx, KLGRD_STEAM_STAT, ok ? xp : 0); }
                ok = 1; xp = sx; klgrd.local_src = 1;
            } else {
                klgrd.steam_ok = 0;
                if (!klgrd.steam_failtold) { klgrd.steam_failtold = 1; klog("grades: Steam GetStat('%s') failed (no Steam, unguarded interface, or stats not received yet); retried every 5 s, no more lines", KLGRD_STEAM_STAT); }
            }
        }
    }
    if (!ok) { if (!klgrd.local_ok && ++klgrd.local_bad == 5) klog("grades: the local profile experience is not readable (code or pointers differ): no badge for you"); return; }
    klgrd.local_bad = 0;
    if (!klgrd.local_told || klgrd.local_xp != xp) { klgrd.local_told = 1; klog("grades: your %s experience %d = rank %d (%s)", klgrd.local_src ? "Steam" : "profile", xp, klgrd_rank_of_xp(&klgrd.c, xp), klgrd_name_of(klgrd.set, klgrd_rank_of_xp(&klgrd.c, xp))); }
    klgrd.local_xp = xp; klgrd.local_ok = 1;
}

/* the online reader's seats: keep their raw values (called wherever a klor_snap is read for display) */
static void klgrd_note_online(const struct klor_snap *o)
{
    static DWORD said; int i; DWORD now;
    if (!klgrd.on || !o || !o->ok) return;
    for (i = 0; i < o->n; i++) {
        const struct klor_row *r = &o->r[i];
        if (r->seat < 0 || r->seat >= KLGRD_MAXI) continue;
        klgrd.o_ok[r->seat] = r->xp >= 0; klgrd.oxp[r->seat] = r->xp; klgrd.orate[r->seat] = r->rating;
        if (r->xp > 0 && !klgrd.o_live) { klgrd.o_live = 1; klog("grades: the server's Experience (S+0xc8) is live: seat %d has %d", r->seat, r->xp); }
    }
    if (klgrd.probe && ((now = GetTickCount()) - said >= 5000 || !said)) {
        said = now ? now : 1;
        for (i = 0; i < o->n; i++) klog("grades: probe seat %d '%s' Experience %d Rating %d (local %d, profile %s %d)", o->r[i].seat, o->r[i].name, o->r[i].xp, o->r[i].rating, o->local, klgrd.local_ok ? "xp" : "unread", klgrd.local_xp);
    }
}

/* the rank 0..7 to show for a row, -1 = none. online: idx = the seat; Arcade: idx = the record. */
static int klgrd_rank(int online, int idx, int is_local)
{
    if (!klgrd.on || idx < 0 || idx >= KLGRD_MAXI) return -1;
    if (is_local && klgrd.local_ok) {
        static int told_rank = -1; int rk = klgrd_rank_of_xp(&klgrd.c, klgrd.local_xp);
        if (rk != told_rank) { told_rank = rk; klog("grades: own badge drawn: rank %d '%s' xp %d (source %s)", rk, klgrd_name_of(klgrd.set, rk), klgrd.local_xp, klgrd.local_src ? "steam" : "profile"); }
        return rk;
    }
    if (is_local) return -1;
    if (online && klgrd.o_ok[idx]) {
        if (klgrd.source == 1) return klgrd.orate[idx] >= 0 && klgrd.orate[idx] < KLGRD_NRANK ? klgrd.orate[idx] : -1;
        if (klgrd.o_live) return klgrd_rank_of_xp(&klgrd.c, klgrd.oxp[idx]);
    }
    return -1;
}

static int klgrd_pool_extra(void) { return klgrd.on && (klgrd.letter || klgrd.rankup); }     /* klhud_board2.c: the 14 extra scoreboard texts are made only then */
static int klgrd_letter_on(void) { return klgrd.on && klgrd.letter; }
static int klgrd_nameset(void) { return klgrd.set; }

static int klgrd_bot_rank(void) { return klgrd.on ? klgrd.botrank : -1; }

/* "R5 Kane" - the badge before a crew name (in place). */
static void klgrd_decorate_rank(char *name, int cap, int rank)
{
    char b[24], t[96];
    if (!klgrd.on || !klgrd.badge || rank < 0 || cap < 8) return;
    klgrd_badge_text(b, sizeof b, klgrd.set, klgrd.style, rank);
    if (!b[0]) return;
    _snprintf(t, sizeof t, "%s %s", b, name); t[sizeof t - 1] = 0;
    _snprintf(name, cap, "%s", t); name[cap - 1] = 0;
}

static void klgrd_decorate(char *name, int cap, int online, int idx, int is_local)
{
    if (!klgrd.on || !klgrd.badge) return;
    klgrd_decorate_rank(name, cap, klgrd_rank(online, idx, is_local));
}

/* [Grades] OnlineTags=1: the badge before an online head tag (needs Enable=1; independent of Badge). rank -1 = none. Others' rank is a GUESS (S+0xc8, see klgrd_rank). */
static int klgrd_otags_on(void) { return klgrd.on && klgrd.otags; }
static void klgrd_decorate_tag(char *name, int cap, int rank)
{
    char b[24], t[96];
    if (!klgrd.on || !klgrd.otags || rank < 0 || cap < 8) return;
    klgrd_badge_text(b, sizeof b, klgrd.set, klgrd.style, rank);
    if (!b[0]) return;
    _snprintf(t, sizeof t, "%s %s", b, name); t[sizeof t - 1] = 0;
    _snprintf(name, cap, "%s", t); name[cap - 1] = 0;
}

/* the round's rank bookkeeping, one call per row per tick of the card. st = the session state. */
static void klgrd_round_reset(int st)
{
    int i;
    if (!klgrd.on || !klgrd.rankup) return;
    if (st >= 0x20 || st < 0x16) for (i = 0; i < KLGRD_MAXI; i++) { klgrd.base_ok[i] = 0; klgrd.base[i] = klgrd.cur[i] = -1; klgrd.cur_loc[i] = 0; }
}

static void klgrd_track(int online, int idx, int is_local, int st)
{
    int r;
    if (!klgrd.on || !klgrd.rankup || idx < 0 || idx >= KLGRD_MAXI) return;
    r = klgrd_rank(online, idx, is_local);
    if (r < 0) return;
    klgrd.cur[idx] = r; klgrd.cur_loc[idx] = is_local;
    if (st >= 0x16 && st <= 0x19 && !klgrd.base_ok[idx]) { klgrd.base[idx] = r; klgrd.base_ok[idx] = 1; }
}

/* did the seat's rank rise this round? -> 1 and the two ranks */
static int klgrd_up(int idx, int *before, int *after)
{
    if (!klgrd.on || !klgrd.rankup || idx < 0 || idx >= KLGRD_MAXI || !klgrd.base_ok[idx]) return 0;
    if (!klgrd_rankup(klgrd.base[idx], klgrd.cur[idx])) return 0;
    *before = klgrd.base[idx]; *after = klgrd.cur[idx];
    return 1;
}

/* the letter for one row's numbers; 0 = grades off */
static char klgrd_letter(const struct klgrd_in *p, int *points)
{
    int pts;
    if (!klgrd.on || !klgrd.letter) return 0;
    pts = klgrd_points(&klgrd.c, p);
    if (points) *points = pts;
    return klgrd_letter_of(&klgrd.c, pts);
}

#endif /* KLHUD_GRADES_C */
