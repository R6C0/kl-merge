/*
 * klgrades.h - the PURE part of klhud_grades.c ([Grades], 2026-10-27, track GRADES): no game, no globals of the hook.
 * Included by klhud_grades.c (inside klhook.c) and by klgrades_test.c (off-game check: cl klgrades_test.c).
 *
 * Two things, both ours:
 *   RANK   the game's FA criminal rank 0..7 from FA experience (kl2.exe 0x5103e0, read in the disassembly: cdecl, thresholds
 *          25 100 400 700 1500 2100 2800, else 7). Rank 0 is the lowest. The game's own names (Menu LOC FragileAllianceRank_08 .. _01,
 *          Dog Days): 0 Mugger, 1 Scammer, 2 Hired Hand, 3 Thug, 4 Hired Gun, 5 Enforcer, 6 Henchman, 7 Mastermind ("Rank 8: Mugger ...
 *          Rank 1: Mastermind", MultiplayerTips_12). GUESS: rank 0 = "Rank 8" (the tip says the climb starts at Mugger).
 *          Dead Men's own FA ranks are the Seven (Scenes/KaneAndLynch.zip LOC FragileAllianceRank_08 .. _01): 0 Hutchison, 1 Standen,
 *          2 Parker, 3 Red, 4 Meldal, 5 Ashkanan, 6 Lynch, 7 Kane. Same 8 steps, same mapping (GUESS, only the names differ).
 *   GRADE  an end-of-round letter S / A / B / C / D per player, a mission grade in the Dead Men sense, from points:
 *            points = kill*KILLS + policekill*POLICE + (loot / lootunit) * LOOT + (rewards / rewunit) * REWARD
 *                     + (escaped ? ESCAPE : 0) + (dead ? DEAD : 0) + (traitor ? TRAITOR : 0) + (fed ? FED : 0)
 *          letter: points >= cut[0] S, >= cut[1] A, >= cut[2] B, >= cut[3] C, else D.   Every number is in the ini ([Grades]).
 *          The defaults are a first guess for a normal 4..9 player round (a clean escape with a fair share of the loot and two kills
 *          is an A); nothing has been played with them.
 */
#ifndef KLGRADES_H
#define KLGRADES_H

#define KLGRD_NRANK 8

struct klgrd_cfg {
    int thr[7];                        /* experience needed for rank 1 .. 7 (rank 0 below thr[0]); the game's {25,100,400,700,1500,2100,2800} */
    int w_kill, w_police, w_loot, w_reward, w_escape, w_dead, w_traitor, w_fed;     /* points */
    int lootunit, rewunit;             /* dollars per loot / reward step (> 0) */
    int lootcap;                       /* the loot steps counted at most (a lucky bag must not make an S) */
    int cut[4];                        /* points for S, A, B, C */
};

static void klgrd_defaults(struct klgrd_cfg *c)
{
    static const int thr[7] = { 25, 100, 400, 700, 1500, 2100, 2800 };
    int i;
    for (i = 0; i < 7; i++) c->thr[i] = thr[i];
    c->w_kill = 2; c->w_police = 1; c->w_loot = 1; c->w_reward = 1; c->w_escape = 6; c->w_dead = -3; c->w_traitor = -4; c->w_fed = -2;
    c->lootunit = 50000; c->rewunit = 25000; c->lootcap = 12;
    c->cut[0] = 14; c->cut[1] = 10; c->cut[2] = 6; c->cut[3] = 3;
}

/* experience -> rank 0..7 (the game's function, 0x5103e0, as a table) */
static int klgrd_rank_of_xp(const struct klgrd_cfg *c, int xp)
{
    int r = 0;
    if (xp < 0) xp = 0;
    while (r < 7 && xp >= c->thr[r]) r++;
    return r;
}

struct klgrd_in { int kills, police, escaped, dead, traitor, fed; long loot, rewards; };

static int klgrd_points(const struct klgrd_cfg *c, const struct klgrd_in *p)
{
    long steps = c->lootunit > 0 && p->loot > 0 ? p->loot / c->lootunit : 0, rsteps = c->rewunit > 0 && p->rewards > 0 ? p->rewards / c->rewunit : 0;
    int k = p->kills < 0 ? 0 : p->kills > 40 ? 40 : p->kills, pk = p->police < 0 ? 0 : p->police > 40 ? 40 : p->police;
    long pts;
    if (steps > c->lootcap) steps = c->lootcap;
    if (rsteps > c->lootcap) rsteps = c->lootcap;
    pts = (long)k * c->w_kill + (long)pk * c->w_police + steps * c->w_loot + rsteps * c->w_reward;
    if (p->escaped) pts += c->w_escape;
    if (p->dead) pts += c->w_dead;
    if (p->traitor) pts += c->w_traitor;
    if (p->fed) pts += c->w_fed;
    return (int)pts;
}

static char klgrd_letter_of(const struct klgrd_cfg *c, int points)
{
    return points >= c->cut[0] ? 'S' : points >= c->cut[1] ? 'A' : points >= c->cut[2] ? 'B' : points >= c->cut[3] ? 'C' : 'D';
}

/* the rank-up decision: both ranks valid (0..7) and the new one higher */
static int klgrd_rankup(int before, int after) { return before >= 0 && before < KLGRD_NRANK && after > before && after < KLGRD_NRANK; }

/* names. set 0 = Dog Days' criminal ranks, 1 = Dead Men's Seven. [rank] lowest first. */
static const char *const klgrd_names_dd[KLGRD_NRANK] = { "Mugger", "Scammer", "Hired Hand", "Thug", "Hired Gun", "Enforcer", "Henchman", "Mastermind" };
static const char *const klgrd_names_dm[KLGRD_NRANK] = { "Hutchison", "Standen", "Parker", "Red", "Meldal", "Ashkanan", "Lynch", "Kane" };
static const char *klgrd_name_of(int set, int rank)
{
    if (rank < 0 || rank >= KLGRD_NRANK) return "";
    return set == 1 ? klgrd_names_dm[rank] : klgrd_names_dd[rank];
}

/* the badge text: style 0 "R5" (the game's "Rank n" counted down from the top: 1 = Mastermind, 8 = Mugger), style 1 "[THUG]" (the name, capitals) */
static void klgrd_badge_text(char *out, int cap, int set, int style, int rank)
{
    int i = 0; const char *n;
    if (cap < 2) return;
    if (rank < 0 || rank >= KLGRD_NRANK) { out[0] = 0; return; }
    if (style == 0) { _snprintf(out, cap, "R%d", KLGRD_NRANK - rank); out[cap - 1] = 0; return; }
    n = klgrd_name_of(set, rank);
    out[i++] = '[';
    for (; *n && i < cap - 2; n++) out[i++] = (*n >= 'a' && *n <= 'z') ? (char)(*n - 32) : *n;
    out[i++] = ']'; out[i] = 0;
}

#endif /* KLGRADES_H */
