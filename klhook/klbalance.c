/*
 * klbalance.c - one dial for how much a bullet costs whom in an Arcade round ([Balance] Risk=0..3).
 * The owner, 2026-10-10, after four Dead Men maps with AI heisters: 'they dont have much health when i shoot them
 * but when they shoot me i have a lot of health not proportional and the coppers dont seem too intimidating it
 * should be all the same kinda risk and how the traitors could be'.
 * Part of KLHook (included by klhook.c after klbot.c, SHIP and TEST alike). DATA WRITES ONLY: floats of two heap
 * objects (the tuning object, the local player's health object). No code byte, no call of a game function.
 * Research and every number: re\balance.md. LIVE since 2026-10-10 in the owner's game (KLHook.log: 'the damage table
 * ... is what the game's code builds', 'Risk=2 written for 11 Arcade levels (39 value(s) changed', 'your health set:
 * maximum 401.5'): the six factors and the health part. NOT RUN: the seventh factor (CrewOffStage, 2 a2). Everything
 * is OFF unless [Balance] Enable=1, and nothing is written outside an Arcade session on a level that is not stock.
 *
 * 1. WHAT WAS MEASURED (kl2.exe build 0490, read 2026-10-10; EXE = in the disassembly)
 *    A bullet's damage is made in three steps.
 *    a. The gun: ZFFItemTemplateWeapon slot 0x2f0 = 0x46ef60(weapon, distance). Four damage numbers of the AMMO
 *       template (object +0x84..+0x90) are joined over the gun's four ranges (+0xd4..+0xe0), times the gun's
 *       +0xe4, times +0x13c when the shooter is a ZActor (an NPC: pistols 1.5, rifles 0.6..1.0, shotgun pellets
 *       0.4) or +0x140 when it is not and the session is multiplayer / Arcade (1.0 on every gun), times one of
 *       +0x144..+0x150 by range band in multiplayer / Arcade. Level data, the same in every level.
 *    b. The body part: 0x572f60(bone type), ten floats at 0xcdefe4..0xcdf008: head (types 2, 3) 10.0, 0.5 for
 *       types 4 and 7, 0.2 for 6 and 9, else 1.0. An NPC victim takes it whole (0x61acb8). The PLAYER as victim
 *       takes min(m, 4) softened to 1 + (m - 1) / 4 (0x4db7ff..0x4db83d): a head shot costs him 1.75, not 10.
 *       And a ZActor shooter never gets the head factor at all (0x61ac87, 0x4db7e7: bone type 2 / 3 -> 1).
 *    c. WHO SHOOTS WHOM, Arcade only: one float of the per-level record R = [0x168d7c0] + 0x6ac + L * 0x70
 *       (L = the Arcade level, byte [[rules+0x5f8]+0x45] clamped to 1..11; the record klbot.c's Tune writes its
 *       +0x18 / +0x20 / +0x6c of). With the local player not a policeman ([player+0x2723] == 0):
 *         +0x00  an NPC that is not team Ally -> an NPC        0x591b60   (police hitting the AI heisters)
 *         +0x04  an Ally NPC -> an NPC                         0x591b60   (AI heisters hitting police)
 *         +0x08  an NPC that is not Ally -> the player         0x8b8050   (police hitting YOU)
 *         +0x0c  the player -> an NPC that is not Ally         0x7c1ba0   (YOU hitting police)
 *         +0x10  an Ally NPC -> the player                     0x8b8050   (a heister - a traitor - hitting YOU)
 *         +0x14  the player -> an Ally NPC                     0x7c1ba0   (YOU hitting a heister / a traitor)
 *         +0x1c  TIMES THIS, on top of +0x04, when the shooter is an Ally NPC at another heist stage than the local
 *                player (0x591be0..0x591c24, re-read whole 2026-10-11; re\balance.md 10). The routine's first argument
 *                is the ATTACKER: 0x61a980 (ZFFActor's hit routine, the victim is `this`) keeps [hit+0xc] when it is a
 *                ZFFActor and pushes it at 0x61ad15. Only when [player+0x2723] == 0 and the attacker's team is Ally:
 *                0x78f470 looks the attacker up as a crew record (in use, mask 1 'an AI member', its actor), 0x6c7700
 *                gives the local player's (record 0 in Arcade); stage bytes [record+0x78] differ -> fmul [R+0x1c].
 *                So: an AI heister that is not at YOUR stage hits every NPC - police, guards, civilians - at 0.5 .. 0.1
 *                of his damage. Not for what a heister TAKES, not for the player's hits or the hits on him, not for a
 *                police player, not in the traitor rules: 0x591c1d is the ONLY reader of the float in the exe (three
 *                sweeps of every use of the tuning pointer; the pointer never leaves the function that loads it).
 *                Until 2026-10-11 this line had shooter and victim swapped (re\boardall_review_exe.md 1).
 *       As the tuning object's constructor writes them (0x524050, emulated: re\balance.md 2):
 *         level        1     2     3     4     5     6     7     8     9    10    11
 *         +0x00     0.01  0.05   0.1  0.15   0.2  0.25   0.3  0.35   0.4  0.45   0.5
 *         +0x04      3.0   2.6   2.2   1.9   1.6   1.3   1.0   0.8   0.4   0.2   0.1
 *         +0x08      0.1   0.2   0.4   0.8   1.0   1.3   1.6   1.9   2.2   2.6   3.0
 *         +0x0c      2.0  1.75   1.5  1.25   1.0   0.9   0.8   0.7   0.6   0.5   0.3
 *         +0x10      0.1   0.2   0.4   0.8   1.0   1.1   1.2   1.3   1.4   1.5   1.7
 *         +0x14     0.25   0.5   1.0   0.9   0.8   0.7   0.6   0.5   0.4   0.3   0.1
 *         +0x1c      0.5   0.5   0.5   0.4   0.3   0.3   0.2   0.2   0.2   0.1   0.1     (0x52b84d.. : read again 2026-10-11)
 *       THIS IS WHAT THE OWNER FELT. On Arcade level 1 - every test round so far - a policeman's bullet costs the
 *       player a TENTH, the player's costs the policeman DOUBLE, a policeman's costs an AI heister a HUNDREDTH and
 *       a heister's costs a policeman three times. It is the stock game's own ramp (even at level 5, reversed by
 *       11), on the stock maps too; the Dead Men maps did not cause it.
 *    Health. The player: 0x410781 gives him, in multiplayer / Arcade, float [P+0x10] of the tuning object's player
 *    block P (0x4206f0: Arcade P = tuning+0x604, online +0x5c4, story +0x5e4) plus 0 / 20 / 40 / 60 of armour
 *    (0xbd22c8): Arcade 550 (story: 100 times 11 / 5 / 2.25 / 0.85 by difficulty). It comes back by itself:
 *    [P+0x08] seconds after the last hit (Arcade 4), all of it within [P+0x0c] seconds (Arcade 4) - the health
 *    object's +0x14 / +0x18, used by 0x419570. An NPC: its ZSoldier health (65..175 police, 280 AI heisters) times
 *    0.5 / 0.9 / 1.15 / 1.3 by the campaign difficulty [0x156b5f0] (0x8fbac0 through 0x831f00: Arcade is not
 *    'online', so it takes the STORY rows, and nothing in the Arcade menu sets that option - ASSUMPTION: it is
 *    what the profile last played the campaign on; the log line below says what it is).
 *
 * 2. WHAT THE HOOK DOES
 *    a. THE SIX FACTORS. While an Arcade session is up on a level that is not stock, the six floats +0x00..+0x14
 *       of all eleven records are written; the values found first are kept and written back when the session is
 *       no longer Arcade or the level is stock. Risk picks the row, each factor has its own key:
 *                      CopToCrew CrewToCop CopToYou YouToCop CrewToYou YouToCrew   PlayerHealth  RegenDelay RegenTime
 *         Risk=0         (nothing is written: the stock ramp)
 *         Risk=1           0.5      1.5      0.5      1.5      0.5      1.0        1.0 (550)     stock      stock
 *         Risk=2           1.0      1.0      1.0      1.0      1.0      1.0        0.73 (400)    8 s        8 s
 *         Risk=3           1.0      1.0      1.0      1.0      1.0      1.0        0.51 (280)    8 s        8 s
 *       Risk=2 is the owner's rule: the same gun at the same range costs everybody the same. 8 s / 8 s is what a
 *       stock SWAT man and an AI heister have (ZSoldier field 8 = 50: 0x8fbbff). 280 is an AI heister's health.
 *       Ramp=1 (default): the stock ramp still counts where it is HARDER than the dial - damage you and your crew
 *       take is max(dial, stock), damage dealt to the police is min(dial, stock) - so a late Arcade level is never
 *       easier than stock. Ramp=0: the dial's numbers on every level. YouToCrew is always the dial's number.
 *       NOT written: +0x18 (klbot.c's Retaliate).
 *    a2. THE SEVENTH, CrewOffStage (2026-10-11; NOT RUN IN THE GAME): the float +0x1c of the same eleven records, in
 *       the same pass and under the same conditions as the six, the stock values kept and put back with theirs.
 *       With you outside and the crew inside (stage 0 against 1) 'CrewToCop 1.0' was really 0.5.
 *         CrewOffStage=1.0   an AI heister hits police the same wherever you are      -1 = the game's own (not written)
 *         Risk=0  not written
 *         Risk=1  0.75   a GUESS as Risk=1's other numbers are: halfway from stock's 0.5 to none, as they are halfway to 1.0
 *         Risk=2  1.0    'the same gun at the same range costs everybody the same' cannot depend on where YOU stand
 *         Risk=3  1.0    the same
 *       Ramp=1: stock's number is at most 0.5, so 'stock stays where it is harder' taken per factor would never let the
 *       key do anything. What a heister at another stage really deals is CrewToCop x CrewOffStage, so the rule is put
 *       on that PRODUCT: it is at most stock's own product on the level (levels 1..11: 1.5 1.3 1.1 0.76 0.48 0.39 0.2
 *       0.16 0.08 0.02 0.01). Risk=2 therefore writes 1.0 on levels 1-3 (1.0 x 1.0 is under stock's 3.0 x 0.5), 0.76 /
 *       0.48 / 0.39 on 4-6 and leaves 7-11; Risk=1 writes 0.75 0.75 0.73 0.51 0.32 and leaves 6-11. A late Arcade level
 *       is never easier than stock in this either. With CrewToCop left at stock, Ramp=1 holds the key at stock on every
 *       level (a line says so) - as it holds CopToYou=0.05. Ramp=0: the number as given, on every level.
 *       Written only when the eleven values found are the row of section 1 (klr_code_off): another build's object is
 *       not written into; one line says so, the six are not affected.
 *       THE KEY'S TEXT (review N1 / N2): one number and nothing else, 0 .. 20 (a ';' comment may follow). '0,75' or
 *       '1.0abc' is NOT taken as its leading number (strtod would make the first 0 - an off-stage heister doing no
 *       damage at all): the key is ignored, the dial's number stands and one line says so; the same for a number
 *       over 20. Negative = the game's own; '-0' is 0.
 *       OVER 1 (review N3): the key may be set up to 20, and beside a low CrewToCop the product rule then lets a
 *       heister at ANOTHER stage hit harder than one at yours (CrewToCop=0.1 CrewOffStage=20 under Ramp=1: x 15 on
 *       level 1, against 0.1 at your stage). Not capped: it happens only on request (the dial's own numbers never pass
 *       1.0), and the live check that is to SHOW the factor uses 20 on purpose (re\balance.md 10.9, run O3).
 *       While the table fails klr_table's shape test nothing is written and nothing is put back, the seventh included
 *       (as the six always did); it goes back on the first pass the test holds again (review N5).
 *    b. THE PLAYER'S HEALTH. The tuning block is read when the player object is made, before this hook knows the
 *       level; so the LIVE health object is written instead: H = [player+0xa48] of the local player (ZFFPlayer,
 *       vtable 0xbb45f4; [H+0x24] is the player again, 0x4aadaf), from the game's own thread only:
 *       [H+0x08] maximum = (the maximum the game gave) * PlayerHealth, [H+0x04] lowered to it when above,
 *       [H+0x14] / [H+0x18] the two regeneration times. When the game writes a new maximum (a new round, armour),
 *       that becomes the base and is scaled again. A player who is a policeman ([player+0x2723]) is left alone.
 *       The game's values go back when the hook stops acting while the object still lives.
 *       ASSUMPTION: nothing but 0x8ab200 / the HUD derives anything from the maximum that a smaller one breaks;
 *       the 16-bit copy at [player+0x274c] (what a session peer would be sent, 0x6443b8) is NOT written - Arcade
 *       has no peer.
 *    c. THE LOG (Log=1, on any level): once per round object the Arcade level, the campaign difficulty, the seven
 *       stock factors of every level ('... crew off your stage x 0.50'), the three player blocks and the player's
 *       health object as found - the first live run thereby checks every number of section 1. Log=2 adds a line for
 *       every loss of health of the player ('you lost 6.1'): with one policeman shooting, that IS gun damage times
 *       CopToYou. Nothing logs what a heister's bullet costs a policeman: the seventh shows in its lines only.
 *
 * 3. NOT DONE HERE
 *    NPC health (level data: kl_map_ai's rows), accuracy (ZSoldier field 4: 100 on M01 / M02 / M03, 55 in stock -
 *    with CopToYou 1.0 that may be too much; re\balance.md 6 has the level-side answer), the campaign difficulty
 *    global (written by the option system and saved to the profile: only read here), the body part table.
 *
 * WIRING (klhook.c; nothing else of the hook changes)
 *   #include "klbalance.c"       after  #include "klbot.c"      (it uses klb_level, the 'not the stock level' test)
 *   klr_tick(game_thread);       in klh_tick, after  klb_tick(game_thread);
 *   klr_init();                  in the init list, after  klb_init();
 * KLHook.ini: section [Balance] (sample at the end of re\balance.md).
 */
#ifndef KLBALANCE_C
#define KLBALANCE_C

#define KLR_SESSION   0x0168e598              /* +0x54, +0x5c = mode (4 = Arcade), +0x70 = state */
#define KLR_SETTINGS  0x0168e9e4              /* +0x54 = the rules object */
#define KLR_TUNING    0x0168d7c0              /* the tuning object (heap, no vtable) */
#define KLR_GAMEDATA  0x00dd265c              /* +0x828 + 4 * i players, +0x898 the local player's index */
#define KLR_DIFF      0x0156b5f0              /* the option Difficulty, 0..3 (.bss; read only) */
#define KLR_RULES_VT  0x00bd3514              /* ZGameRulesHeist */
#define KLR_PLAYER_VT 0x00bb45f4              /* ZFFPlayer */
#define KLR_NLEVEL    11
#define KLR_NF        6                       /* the floats at R+0x00, +0x04 .. +0x14 */
#define KLR_OFF       0x1c                    /* the seventh: an Ally NPC shooter at another heist stage than the player */
#define KLR_ABS(x)    ((x) < 0 ? -(x) : (x))

static int klb_level(char why[200]);          /* klbot.c: 1 only on a level whose archive is NOT the stock one */

static const char *const klr_key[KLR_NF] = { "CopToCrew", "CrewToCop", "CopToYou", "YouToCop", "CrewToYou", "YouToCrew" };
static const int klr_kind[KLR_NF] = { 1, -1, 1, -1, 1, 0 };      /* Ramp: 1 = at least stock, -1 = at most stock, 0 = as given */
static const struct { float f[KLR_NF], health, delay, full, off; } klr_dial[4] = {       /* off = CrewOffStage, -1 = not written */
    { { -1, -1, -1, -1, -1, -1 }, 0, 0, 0, -1 },
    { { 0.5f, 1.5f, 0.5f, 1.5f, 0.5f, 1.0f }, 1.0f, 0, 0, 0.75f },                        /* 0.75: a GUESS, halfway from stock's 0.5 to none */
    { { 1, 1, 1, 1, 1, 1 }, 0.73f, 8, 8, 1 },
    { { 1, 1, 1, 1, 1, 1 }, 0.51f, 8, 8, 1 },
};
/* what 0x524050 writes (re\balance.md 2): only compared with what is found, for one log line */
static const float klr_code[KLR_NLEVEL + 1][KLR_NF] = {
    { 0 },
    { 0.01f, 3.0f, 0.1f, 2.0f,  0.1f, 0.25f }, { 0.05f, 2.6f, 0.2f, 1.75f, 0.2f, 0.5f }, { 0.1f,  2.2f, 0.4f, 1.5f,  0.4f, 1.0f },
    { 0.15f, 1.9f, 0.8f, 1.25f, 0.8f, 0.9f },  { 0.2f,  1.6f, 1.0f, 1.0f,  1.0f, 0.8f }, { 0.25f, 1.3f, 1.3f, 0.9f,  1.1f, 0.7f },
    { 0.3f,  1.0f, 1.6f, 0.8f,  1.2f, 0.6f },  { 0.35f, 0.8f, 1.9f, 0.7f,  1.3f, 0.5f }, { 0.4f,  0.4f, 2.2f, 0.6f,  1.4f, 0.4f },
    { 0.45f, 0.2f, 2.6f, 0.5f,  1.5f, 0.3f },  { 0.5f,  0.1f, 3.0f, 0.3f,  1.7f, 0.1f },
};
/* The float at +0x1c as 0x524050 writes it (0x52b84d for level 1; read 2026-10-11). Unlike klr_code this one GATES:
   the seventh factor is written only into a table whose eleven values are these. */
static const float klr_code_off[KLR_NLEVEL + 1] = { 0, 0.5f, 0.5f, 0.5f, 0.4f, 0.3f, 0.3f, 0.2f, 0.2f, 0.2f, 0.1f, 0.1f };

static struct {
    int on, log, risk, ramp, any;
    float f[KLR_NF];                          /* < 0 = leave this factor as the game has it */
    float health, delay, full;                /* 0 = leave */
    float off;                                /* CrewOffStage; < 0 = leave +0x1c as the game has it */
} klr;

struct klr_row { float f[KLR_NF]; float off; };           /* off = the float at +0x1c */
struct klr_val { float v0, wrote; };          /* v0 = what the game gave, wrote = what the hook put there (0 = nothing) */
static struct { DWORD player, h; int have; struct klr_val max, delay, full; float seen; } klr_p;

static int klr_finite(float f) { return f == f && f > -1e9f && f < 1e9f; }

/* -> 1 when an Arcade session with a ZGameRulesHeist object is up; state = [session+0x70], level = 1..11 */
static int klr_arcade(DWORD *rules, DWORD *state, int *level)
{
    DWORD sm, gs, score, sub = 0; BYTE b = 0;
    *rules = *state = 0; *level = 1;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLR_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x54, &sub, 4) || sub == 2 || sub == 3) return 0;
    if (!klh_rd(sm + 0x70, state, 4)) return 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLR_SETTINGS))) || !(*rules = klh_rd32(gs + 0x54)) || klh_rd32(*rules) != KLR_RULES_VT) return 0;
    if (!(score = klh_rd32(*rules + 0x5f8)) || !klh_rd(score + 0x45, &b, 1)) return 0;
    *level = (signed char)b < 1 ? 1 : b > KLR_NLEVEL ? KLR_NLEVEL : b;         /* the clamp every reader in the game applies */
    return 1;
}

/* The eleven records as they are now; 0 when the object does not hold the table where this build expects it (it
   has no vtable to check): six factors in 0..50 and the retaliation limit at +0x18 in 1..100000, per level.
   The float at +0x1c is taken along as found: it has its own, stricter test (klr_code_off) and does not change
   what the six need. */
static int klr_table(DWORD tun, struct klr_row out[KLR_NLEVEL + 1])
{
    int L, k;
    for (L = 1; L <= KLR_NLEVEL; L++) {
        float fv[0x20 / 4];
        if (!klh_rd(tun + 0x6ac + 0x70 * L, fv, sizeof fv)) return 0;
        for (k = 0; k < KLR_NF; k++) { if (!klr_finite(fv[k]) || fv[k] < 0 || fv[k] > 50) return 0; out[L].f[k] = fv[k]; }
        if (!klr_finite(fv[0x18 / 4]) || fv[0x18 / 4] < 1 || fv[0x18 / 4] > 100000) return 0;
        out[L].off = fv[KLR_OFF / 4];
    }
    return 1;
}

static float klr_want(int k, float stock)
{
    float v = klr.f[k];
    if (v < 0) return stock;
    if (klr.ramp && klr_kind[k] > 0 && stock > v) return stock;
    if (klr.ramp && klr_kind[k] < 0 && stock < v) return stock;
    return v;
}

/* The seventh factor for one level, s = the level's stock row. Ramp: an AI heister at another stage than the player
   deals crew->police x this factor (0x591bd4 fld [R+4] ... 0x591c20 fmul), so the six's rule 'damage dealt to the
   police is at most stock's' is applied to that PRODUCT: the factor is at most stock's product over the crew->police
   the dial leaves on the level. Where the dial does not lower crew->police that limit is stock's own factor, taken
   exactly (no arithmetic: the value must compare equal to what is in the table). A number BELOW the limit is the
   user's and is written as given. */
static float klr_want_off(const struct klr_row *s)
{
    float v = klr.off, c2c, lim;
    if (v < 0) return s->off;
    if (!klr.ramp) return v;
    c2c = klr_want(1, s->f[1]);
    if (c2c >= s->f[1]) lim = s->off;
    else if (c2c <= 0) return v;              /* crew->police 0: the product is 0 whatever stands here */
    else lim = s->off * (s->f[1] / c2c);
    return v < lim ? v : lim;
}

/* " 0.50 0.50 ..." of the eleven levels: what stands at +0x1c in stock (which 0) or what the dial wants there (1) */
static const char *klr_off_row(const struct klr_row stock[KLR_NLEVEL + 1], int which, char out[96])
{
    int L, n = 0;
    out[0] = 0;
    for (L = 1; L <= KLR_NLEVEL && n < 96 - 8; L++) n += snprintf(out + n, 96 - n, " %.2f", which ? klr_want_off(&stock[L]) : stock[L].off);
    return out;
}

/* arcade: the table is looked at (and logged once, on any level); act: and the level is not stock - only then is
   anything written; otherwise what was written goes back. Data of a heap object; any thread (as klbot.c's Tune). */
static void klr_table_tick(int arcade, int act, int level)
{
    static DWORD tun0; static struct klr_row stock[KLR_NLEVEL + 1]; static int have, applied, toldbad;
    static int offok, toldoff;                /* the seventh: the stock row is the known one; its line was written */
    struct klr_row cur[KLR_NLEVEL + 1]; DWORD tun; int L, k, n = 0, off; float offnow;
    if (!(tun = klh_rd32((DWORD_PTR)KLH_VA(KLR_TUNING)))) return;
    if (tun != tun0) { tun0 = tun; have = applied = offok = toldoff = 0; }
    if (!act) toldoff = 0;                    /* the seventh's line is written once each time the dial starts to act */
    if (!arcade && !applied) return;
    if (!klr_table(tun, cur)) {
        if (arcade && !toldbad++) klog("balance: the tuning object %08lx does not hold the damage table where this build expects it: nothing is written", tun);
        return;
    }
    if (!have) {                              /* first sight in this process: what the game has, before any write of ours */
        int same = 1, badoff = 0; float p[3][5]; DWORD diff = 99;
        have = 1; memcpy(stock, cur, sizeof stock);
        for (L = 1; L <= KLR_NLEVEL; L++) for (k = 0; k < KLR_NF; k++) if (KLR_ABS(cur[L].f[k] - klr_code[L][k]) > 0.001f) same = 0;
        for (L = KLR_NLEVEL; L >= 1; L--) if (!klr_finite(cur[L].off) || KLR_ABS(cur[L].off - klr_code_off[L]) > 0.001f) badoff = L;
        offok = !badoff;
        if (klr.log) {
            klh_rd((DWORD_PTR)KLH_VA(KLR_DIFF), &diff, 4);
            klog("balance: the damage table of the tuning object %08lx %s; campaign difficulty option %lu (0 easy .. 3 extreme: NPC health x 0.5 / 0.9 / 1.15 / 1.3)", tun,
                 same && offok ? "is what the game's code builds" : "DIFFERS from what the game's code builds (re\\balance.md 2) - the lines below are what this process has", diff);
            for (L = 1; L <= KLR_NLEVEL; L++)
                klog("balance: stock, Arcade level %2d: police->crew %.2f  crew->police %.2f  police->you %.2f  you->police %.2f  crew->you %.2f  you->crew %.2f  crew off your stage x %.2f",
                     L, cur[L].f[0], cur[L].f[1], cur[L].f[2], cur[L].f[3], cur[L].f[4], cur[L].f[5], klr_finite(cur[L].off) ? cur[L].off : -1.0f);
            if (klh_rd(tun + 0x5c4, p[0], sizeof p[0]) && klh_rd(tun + 0x5e4, p[1], sizeof p[1]) && klh_rd(tun + 0x604, p[2], sizeof p[2]))
                klog("balance: player blocks (health, s before it comes back, s to come back whole): online %.0f %.1f %.1f | story %.0f %.1f %.1f | Arcade %.0f %.1f %.1f",
                     p[0][4], p[0][2], p[0][3], p[1][4], p[1][2], p[1][3], p[2][4], p[2][2], p[2][3]);
        }
        if (!offok && klr.off >= 0)           /* a refusal is said at any Log level, as the table's own is */
            klog("balance: the float at +0x1c of the damage table is NOT the row this build's code writes (first at Arcade level %d: found %g, known %.2f): CrewOffStage %.2f is NOT written; the six factors are not affected",
                 badoff, klr_finite(cur[badoff].off) ? cur[badoff].off : -1.0, klr_code_off[badoff], klr.off);
    }
    if (!klr.any || (!act && !applied)) return;          /* nothing of ours is in the table: it is not compared and not written */
    off = klr.off >= 0 && offok;              /* the seventh is ours to write: asked for, and the game's row is the known one */
    for (L = 1; L <= KLR_NLEVEL; L++) {
        DWORD R = tun + 0x6ac + 0x70 * L;
        for (k = 0; k < KLR_NF; k++) {
            float want = act ? klr_want(k, stock[L].f[k]) : stock[L].f[k];
            if (want != cur[L].f[k]) n += klh_data((void *)(DWORD_PTR)(R + 4 * k), &want, 4, "damage factor per Arcade level");
        }
        if (off) {                            /* a computed number: compared with a margin, so one that is in the table is not written again */
            float want = act ? klr_want_off(&stock[L]) : stock[L].off;
            if (KLR_ABS(want - cur[L].off) > 0.000001f) n += klh_data((void *)(DWORD_PTR)(R + KLR_OFF), &want, 4, "off-stage damage factor per Arcade level");
        }
    }
    if (act && n) {
        applied = 1;
        offnow = off ? klr_want_off(&stock[level]) : klr_finite(stock[level].off) ? stock[level].off : -1.0f;      /* what stands at +0x1c of this level now */
        klog("balance: Risk=%d written for %d Arcade levels (%d value(s) changed, Ramp=%d); now on level %d: police->crew %.2f  crew->police %.2f  police->you %.2f  you->police %.2f  crew->you %.2f  you->crew %.2f  crew off your stage x %.2f - the stock values come back when the session is not Arcade or the level is stock",
             klr.risk, KLR_NLEVEL, n, klr.ramp, level, klr_want(0, stock[level].f[0]), klr_want(1, stock[level].f[1]), klr_want(2, stock[level].f[2]),
             klr_want(3, stock[level].f[3]), klr_want(4, stock[level].f[4]), klr_want(5, stock[level].f[5]), offnow);
    } else if (!act) {
        applied = 0;
        if (n) klog("balance: the stock damage table is back (%d value(s))", n);
    }
    if (act && off && !toldoff) {             /* once per arming: the seventh on all eleven levels, and what Ramp made of it */
        char a[96], b[96], h[128]; int chg = 0, held = 0; const char *why = "";
        toldoff = 1;
        for (L = 1; L <= KLR_NLEVEL; L++) {
            float w = klr_want_off(&stock[L]);
            if (KLR_ABS(w - stock[L].off) > 0.000001f) chg++;
            if (klr.off - w > 0.000001f) held++;             /* Ramp gave this level less than the number asked for */
        }
        /* no level differs: only Ramp=1 can do that (one number cannot be stock's on eleven levels) */
        if (!chg) why = " - it is NOT written on any level: with Ramp=1 an off-stage heister may not hit police harder than in stock (crew->police x this); a lower CrewToCop (Risk=2 has one) or Ramp=0 lets it through";
        else if (held) {                      /* said only where Ramp really limited something (review N4) */
            snprintf(h, sizeof h, " (Ramp=1 holds it under %.2f on %d level(s): crew->police x this is at most stock's own product there)", klr.off, held);
            why = h;
        }
        klog("balance: crew off your stage (an AI heister at another heist stage than you, his hits on police and every other NPC), Arcade levels 1..11: x%s; stock x%s; CrewOffStage %.2f, Ramp=%d: %d level(s) differ from stock%s",
             klr_off_row(stock, 1, a), klr_off_row(stock, 0, b), klr.off, klr.ramp, chg, why);
    }
}

/* One tracked float of the health object: -> what the game gave it. A value that is neither the game's last nor
   ours is a new one of the game's (a new round, armour bought) and becomes the base. */
static float klr_track(struct klr_val *t, float cur, int fresh)
{
    if (fresh) { t->v0 = cur; t->wrote = 0; }
    else if (KLR_ABS(cur - t->v0) > 0.01f && (t->wrote == 0 || KLR_ABS(cur - t->wrote) > 0.01f)) { t->v0 = cur; t->wrote = 0; }
    return t->v0;
}

/* -> values changed. Only called on the game's thread. */
static int klr_put(struct klr_val *t, DWORD at, float cur, float want, const char *what)
{
    if (KLR_ABS(cur - want) <= 0.01f) return 0;
    if (!klh_data((void *)(DWORD_PTR)at, &want, 4, what)) return 0;
    t->wrote = KLR_ABS(want - t->v0) > 0.01f ? want : 0;
    return 1;
}

/* The local player's health object: logged as found, then scaled while act, put back when not. */
static void klr_player_tick(int act, int game_thread)
{
    DWORD gd, pl, h; BYTE idx = 0xff, police = 0; float raw[0x28 / 4]; int fresh, n = 0;
    float cur, max, delay, full, max0, delay0, full0, wmax, wdelay, wfull;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLR_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || idx == 0xff || (signed char)idx < 0 || idx > 31 ||
        !(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_rd32(pl) != KLR_PLAYER_VT || !(h = klh_rd32(pl + 0xa48)) ||
        !klh_rd(h, raw, sizeof raw) || ((DWORD *)raw)[0x24 / 4] != pl || !klh_rd(pl + 0x2723, &police, 1)) { return; }      /* review D1: a failed read must not make the next pass 'fresh' (it would take our own value as the game's) */
    cur = raw[1]; max = raw[2]; delay = raw[5]; full = raw[6];
    if (!klr_finite(cur) || !klr_finite(max) || !klr_finite(delay) || !klr_finite(full) || max < 1 || max > 100000 || cur > max * 1.01f + 1 ||
        delay < 0 || delay > 3600 || full < 0 || full > 3600) { return; }
    fresh = !klr_p.have || klr_p.player != pl || klr_p.h != h;      /* have stays set through a failed pass */
    klr_p.have = 1; klr_p.player = pl; klr_p.h = h;
    max0 = klr_track(&klr_p.max, max, fresh); delay0 = klr_track(&klr_p.delay, delay, fresh); full0 = klr_track(&klr_p.full, full, fresh);
    if (fresh) {
        klr_p.seen = cur;
        if (klr.log) klog("balance: your health object %08lx (player %08lx%s): %.1f of %.1f; it starts to come back %.1f s after a hit and is whole %.1f s later", h, pl, police ? ", a POLICEMAN: left alone" : "", cur, max, delay, full);
    }
    if (klr.log >= 2 && cur < klr_p.seen - 0.05f) klog("balance: you lost %.1f (%.1f of %.1f)", klr_p.seen - cur, cur, max);
    klr_p.seen = cur;
    if (police) act = 0;
    wmax = act && klr.health > 0 ? max0 * klr.health : max0;
    wdelay = act && klr.delay > 0 ? klr.delay : delay0;
    wfull = act && klr.full > 0 ? klr.full : full0;
    if (KLR_ABS(max - wmax) <= 0.01f && KLR_ABS(delay - wdelay) <= 0.01f && KLR_ABS(full - wfull) <= 0.01f) return;
    if (!game_thread) return;                 /* a live object of the round: only between two frames of the game itself */
    if (klr_put(&klr_p.max, h + 8, max, wmax, "the local player's maximum health")) {
        n++;
        if (cur > wmax) { klh_data((void *)(DWORD_PTR)(h + 4), &wmax, 4, "the local player's health, down to the new maximum"); klr_p.seen = wmax; }
    }
    n += klr_put(&klr_p.delay, h + 0x14, delay, wdelay, "the local player's regeneration delay");
    n += klr_put(&klr_p.full, h + 0x18, full, wfull, "the local player's regeneration time");
    if (n && klr.log) klog("balance: your health %s: maximum %.1f (the game gave %.1f), comes back after %.1f s within %.1f s (the game: %.1f / %.1f)",
                           act ? "set" : "put back", wmax, max0, wdelay, wfull, delay0, full0);
}

static void klr_tick(int game_thread)
{
    static DWORD last, toldrules; static char toldwhy[200];
    DWORD now = GetTickCount(), rules, state; int arcade, act = 0, level; char why[200];
    if (!klr.on || !klh_exe_ok || now - last < (game_thread ? 50u : 100u)) return;
    last = now;
    arcade = klr_arcade(&rules, &state, &level);
    if (arcade && klr.any) {
        act = klb_level(why);                 /* asked every pass: the verdict changes when the archive is opened */
        if (rules != toldrules || strcmp(why, toldwhy)) {
            toldrules = rules; strcpy(toldwhy, why);
            if (act) klog("balance: %s: Risk=%d acts on this round (Arcade level %d); the Steam guard blocks every write of it", why, klr.risk, level);
            else klog("balance: %s: nothing is written here (the dial acts only on a level that is not stock); the log runs", why);
        }
    }
    klr_table_tick(arcade, act, level);
    if (arcade) klr_player_tick(act, game_thread);
    else if (klr_p.have) klr_player_tick(0, game_thread);         /* the session ended with the object alive: its own values go back */
}

static float klr_inif(const char *key, const char *def)
{
    char t[32];
    GetPrivateProfileStringA("Balance", key, def, t, sizeof t, klh_ini);
    return (float)atof(t);
}

/* -> 1 and *d when the text is ONE number and nothing else; blanks or a ';' comment may follow. strtod alone takes the
   leading number of any text: '0,75' would be 0 (review N1). */
static int klr_number(const char *t, double *d)
{
    char *e;
    *d = strtod(t, &e);
    if (e == t || *d != *d) return 0;
    while (*e == ' ' || *e == '\t') e++;
    return *e == 0 || *e == ';';
}

static void klr_init(void)
{
    int k, offbad = 0; float v; char t[32]; double d;
    klr.on = GetPrivateProfileIntA("Balance", "Enable", 0, klh_ini) != 0;
    if (!klr.on) return;
    klr.log = (int)GetPrivateProfileIntA("Balance", "Log", 1, klh_ini); if (klr.log < 0) klr.log = 0; if (klr.log > 2) klr.log = 2;
    klr.risk = (int)GetPrivateProfileIntA("Balance", "Risk", 0, klh_ini); if (klr.risk < 0) klr.risk = 0; if (klr.risk > 3) klr.risk = 3;
    klr.ramp = GetPrivateProfileIntA("Balance", "Ramp", 1, klh_ini) != 0;
    for (k = 0; k < KLR_NF; k++) {
        klr.f[k] = klr_dial[klr.risk].f[k];
        v = klr_inif(klr_key[k], "-1"); if (klr_finite(v) && v >= 0 && v <= 20) klr.f[k] = v;
        if (klr.f[k] >= 0) klr.any = 1;
    }
    /* the seventh: no key = the dial's; a negative number = leave the game's own, also under a Risk; a text that is
       not one number and nothing else, or a number over 20, is ignored and said so below (the six take such a text
       as its leading number, '0,05' as 0: not copied, and not changed for them) */
    klr.off = klr_dial[klr.risk].off;
    GetPrivateProfileStringA("Balance", "CrewOffStage", "", t, sizeof t, klh_ini);
    if (t[0]) {
        if (!klr_number(t, &d) || d > 20) offbad = 1;
        else klr.off = d < 0 ? -1.0f : d > 0 ? (float)d : 0.0f;      /* '-0' is 0, not -0.0 */
    }
    if (klr.off >= 0) klr.any = 1;
    klr.health = klr_dial[klr.risk].health; v = klr_inif("PlayerHealth", "0"); if (klr_finite(v) && v >= 0.05f && v <= 10) klr.health = v;
    klr.delay = klr_dial[klr.risk].delay; v = klr_inif("RegenDelay", "0"); if (klr_finite(v) && v >= 0.1f && v <= 600) klr.delay = v;
    klr.full = klr_dial[klr.risk].full; v = klr_inif("RegenTime", "0"); if (klr_finite(v) && v >= 0.1f && v <= 600) klr.full = v;
    if (klr.health == 1.0f) klr.health = 0;                   /* times one = leave */
    if (klr.health > 0 || klr.delay > 0 || klr.full > 0) klr.any = 1;
    klog("balance: on; Log=%d Risk=%d Ramp=%d; factors (-1 = stock) police->crew %.2f crew->police %.2f police->you %.2f you->police %.2f crew->you %.2f you->crew %.2f, crew off your stage x %.2f; your health x %.2f (0 = stock), comes back after %.1f s within %.1f s (0 = stock); Arcade only, written only on a level that is not stock",
         klr.log, klr.risk, klr.ramp, klr.f[0], klr.f[1], klr.f[2], klr.f[3], klr.f[4], klr.f[5], klr.off, klr.health, klr.delay, klr.full);
    if (offbad)                               /* said at any Log level: the user asked for something and does not get it */
        klog("balance: CrewOffStage=%s is IGNORED: it must be one number of 0 .. 20 with a decimal point (0.75, not 0,75), or a negative one for the game's own; what stands is the dial's %.2f (-1 = the game's own)", t, klr.off);
}

#endif /* KLBALANCE_C */
