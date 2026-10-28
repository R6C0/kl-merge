/* klbalonline.h - the pure logic of [BotFill] OnlineBalance (klbalance.c, 2026-10-28, wk-bal2): which Arcade [Balance] factor a hit
 * on the online HOST gets, from who hit whom, and what number it is. No game memory, no windows.h: klbalonline_test.c checks it off-game.
 *
 * Arcade (klbalance.c section 1 c, re\balance.md): one float of the per-level record R prices a hit inside the victim's routine 0x61a980,
 * chosen by the attacker's and victim's side. Online those routines are skipped (0x7f6850 false for roles 2 / 3), so the host's wrapper
 * (ZFFActor slot 423, private vtable) multiplies the hit scale [hit+0x18] itself with the same float:
 *     attacker -> victim              Arcade float (id = klr_key index)        online here
 *     police / guard (team != 2) -> bot   +0x00 CopToCrew (0)                  done by OnlineCopToBot's own path (k), this header only says so
 *     bot -> police / guard / civilian    +0x04 CrewToCop (1)                  needs the victim on the private table (cops)
 *     human heister -> bot                +0x14 YouToCrew (5) x YouToCrewFar   per hit, by the real distance
 *     human POLICE -> bot                 FedMirror=1: FedToCrew else YouToCrew (6 -> 5); FedMirror=0: +0x0c YouToCop (3)
 *     bot -> bot                          Arcade: +0x04 too; online it only happens with a turned bot: left alone (NONE)
 *     human -> police                     +0x0c YouToCop: not a bot factor, not done
 *     anything -> human                   CopToYou / CrewToYou: the victim is a ZFFPlayer (another vtable), not reached by this wrapper
 * Tough (Arcade: every NPC's maximum health x f) is a damage divisor 1/f on hits ON BOTS here (same fight length; absolute thresholds,
 * point-blank steps and blasts are not scaled, as in Arcade).
 */
#ifndef KLBALONLINE_H
#define KLBALONLINE_H

enum { KBO_A_NONE = 0, KBO_A_HUMAN = 1, KBO_A_HUMANCOP = 2, KBO_A_BOT = 3, KBO_A_NPC = 4 };      /* attacker kinds */
enum { KBO_V_NONE = 0, KBO_V_BOT = 1, KBO_V_NPC = 2 };                                              /* victim kinds (NPC = not team Ally) */
#define KBO_F_NONE      (-1)
#define KBO_F_COP2CREW  0                      /* ids 0..5 are klbalance.c's klr_key order */
#define KBO_F_CREW2COP  1
#define KBO_F_YOU2COP   3
#define KBO_F_YOU2CREW  5
#define KBO_F_FED2CREW  6                      /* FedToCrew: no table slot of its own, a police human's number for YouToCrew */
#define KBO_NF          7
#define KBO_TOKEN       0.0001f                /* a factor of 0 = no damage in Arcade; a literal 0.0 scale might be handled oddly by the game (GUESS, as klbalance.c), so a token */

/* the factor id for one hit, or KBO_F_NONE. mirror = [Balance] FedMirror. */
static int kbo_factor(int att, int vic, int mirror)
{
    if (vic == KBO_V_BOT) {
        if (att == KBO_A_NPC) return KBO_F_COP2CREW;
        if (att == KBO_A_HUMAN) return KBO_F_YOU2CREW;
        if (att == KBO_A_HUMANCOP) return mirror ? KBO_F_FED2CREW : KBO_F_YOU2COP;
        return KBO_F_NONE;                     /* bot -> bot, unknown */
    }
    if (vic == KBO_V_NPC) return att == KBO_A_BOT ? KBO_F_CREW2COP : KBO_F_NONE;
    return KBO_F_NONE;
}

/* Ramp kind of an id: 1 = at least stock, -1 = at most stock, 0 = as given (klbalance.c klr_kind; YouToCop is -1, YouToCrew / FedToCrew never held) */
static int kbo_kind(int id) { return id == 0 ? 1 : (id == 1 || id == 3) ? -1 : 0; }

/* One factor's number as Arcade's klr_want gives it: dial < 0 = not set (-> -1 here: leave the hit as it is), Ramp holds a number that is
   softer than stock where the kind says so. stock = the Arcade level's stock float of that id (0 when there is none). */
static float kbo_want(int id, float dial, int ramp, float stock)
{
    int kind = kbo_kind(id);
    if (dial < 0) return -1.0f;
    if (ramp && ((kind > 0 && stock > dial) || (kind < 0 && stock < dial))) return stock;
    return dial;
}

/* YouToCrewFar: x 1 within near_at, x far_ from far_at on, linear between, steps of 0.02 (klbalance.c klr_far_mult). far_ <= 0 = off. */
static float kbo_range(float dist, float far_, float near_at, float far_at)
{
    float m;
    if (far_ <= 0 || far_at <= near_at || dist != dist) return 1.0f;
    m = dist <= near_at ? 1.0f : dist >= far_at ? far_ : 1.0f + (far_ - 1.0f) * (dist - near_at) / (far_at - near_at);
    return (float)((int)(m * 50.0f + 0.5f)) / 50.0f;
}

/* Tough applies to a BOT victim only (the bot -> cop side leaves the cop's health alone: no cop is on the table for it) */
static float kbo_tough(int vic, float tough) { return vic == KBO_V_BOT && tough > 0 ? tough : 1.0f; }

/* the hit scale multiplier: value (< 0 = factor not set -> 1) x range / tough. A result of 0 is the token. */
static float kbo_scale(float value, float range, float tough)
{
    float m = (value < 0 ? 1.0f : value) * (range > 0 ? range : 1.0f) / (tough > 0 ? tough : 1.0f);
    return m <= 0 ? KBO_TOKEN : m;
}

/* the effective cop -> bot multiplier that klbalance.c puts into OnlineCopToBot's k: CopToCrew's number when set (0 = token), else
   the OnlineCopToBot k (0 = that path is off), then / tough; 0 = path off */
static float kbo_cop_k(float want_c2c, float cb_k, float tough)
{
    float base = want_c2c >= 0 ? (want_c2c == 0 ? KBO_TOKEN : want_c2c) : (cb_k > 0 ? cb_k : (tough > 1.0f || (tough > 0 && tough < 1.0f) ? 1.0f : 0.0f));
    return base > 0 ? base / (tough > 0 ? tough : 1.0f) : 0.0f;
}

#endif
