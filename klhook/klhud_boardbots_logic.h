/* klhud_boardbots_logic.h - the PURE part of [HUD] OnlineBoardBots (klhud_board2.c): the AI heister rows of the ONLINE round-over card.
 * No windows.h. Checked off-game by klhud_boardbots_test.c. NOT run live (bench plan: re/online_board_1101.md, tag OB1).
 *
 * Why: online an AI heister has no score row (flags and money read 0, re/online_round_data.md), so the card showed 'AI' / '-' (or, with OnlineBoardTake,
 * LEFT BEHIND for every living bot). This table LATCHES each bot through the running round (states 0x19..0x1f) so the card can say what is knowable:
 *   - DEAD         : seen dead (body present with health 0) -- both seats, from the Ally actor scan the snapshot already does.
 *   - ESCAPED      : HOST: the hook's own bot puppeteer (klbotfill.c klbf_ob[]) had it aboard (phase 3). CLIENT: INFERRED (GUESS) = it was alive in this round,
 *                    is no longer in the actor scan, was never seen dead, and the escape vehicle is at least 'last call' (esc_state >= 4).
 *   - LEFT BEHIND  : in the scan, alive.
 *   - AI           : none of the above is known (no evidence).
 *   - PAYOUT       : HOST only (the ledger's tally of what the bot carried when it boarded, 0 for dead / left behind); the client has no ledger: unknown ('-').
 * The ledger lives on the host only (nothing replicates it), so a client column that cannot be filled stays '-'. */
#ifndef KLHUD_BOARDBOTS_LOGIC_H
#define KLHUD_BOARDBOTS_LOGIC_H
#include <string.h>

#define KBB_MAX 12                       /* up to 12 seats online; the board has 12 rows */
#define KBB_VAN_LASTCALL 4               /* GUESS: esc_state 4 = last call, 5 = leaving, 7 seen at state 0x1f (BENCH RT2L_DM09 log: 'vehicle state 7') */

enum { KBB_FATE_AI = 0, KBB_FATE_DEAD, KBB_FATE_ESCAPED, KBB_FATE_LEFT };

struct kbb_lat {
    unsigned long actor;                 /* the bot's ZFFActor (0 = free slot) */
    char name[32];                       /* the character name from the last scan */
    int present;                         /* in the actor scan this tick */
    int alive_now;                       /* present and health > 0 this tick */
    int seen_alive, seen_dead;           /* latched over the round */
    int ledger, aboard; long tally;      /* HOST ledger latch: tracked by klbotfill, aboard (phase 3), money booked */
};
struct kbb_tab { struct kbb_lat l[KBB_MAX]; int n; };

static void kbb_reset(struct kbb_tab *t) { memset(t, 0, sizeof *t); }
/* start of one tick's scan: nobody is present until noted */
static void kbb_begin(struct kbb_tab *t) { int i; for (i = 0; i < t->n; i++) { t->l[i].present = 0; t->l[i].alive_now = 0; } }
/* one scan row; -> slot or -1 (table full / no actor) */
static int kbb_note(struct kbb_tab *t, unsigned long actor, const char *name, int alive)
{
    int i;
    if (!actor) return -1;
    for (i = 0; i < t->n && t->l[i].actor != actor; i++) ;
    if (i == t->n) { if (t->n >= KBB_MAX) return -1; memset(&t->l[i], 0, sizeof t->l[i]); t->l[i].actor = actor; t->n++; }
    t->l[i].present = 1; t->l[i].alive_now = alive != 0;
    if (alive) t->l[i].seen_alive = 1; else t->l[i].seen_dead = 1;
    if (name && name[0]) { strncpy(t->l[i].name, name, sizeof t->l[i].name - 1); t->l[i].name[sizeof t->l[i].name - 1] = 0; }
    return i;
}
/* the host ledger's answer for a latched actor (tracked: 0/1; aboard sticky, tally the largest booked) */
static void kbb_ledger(struct kbb_tab *t, int i, int tracked, int aboard, long tally)
{
    if (i < 0 || i >= t->n || !tracked) return;
    t->l[i].ledger = 1;
    if (aboard) t->l[i].aboard = 1;
    if (tally > t->l[i].tally) t->l[i].tally = tally;
}
/* the fate of one latched bot at the end of the round; esc_state = the vehicle's state byte (klor_snap.esc_state) */
static int kbb_fate(const struct kbb_lat *b, int esc_state)
{
    if (b->ledger && b->aboard) return KBB_FATE_ESCAPED;
    if (b->seen_dead && !b->alive_now) return KBB_FATE_DEAD;
    if (b->present && b->alive_now) return KBB_FATE_LEFT;
    if (!b->present && b->seen_alive && !b->seen_dead && esc_state >= KBB_VAN_LASTCALL) return KBB_FATE_ESCAPED;      /* GUESS: vanished alive after last call = boarded */
    return KBB_FATE_AI;
}
/* the payout column: 1 and *v when known (HOST ledger only), else 0 ('-') */
static int kbb_money(const struct kbb_lat *b, int fate, long *v)
{
    if (!b->ledger) return 0;
    *v = fate == KBB_FATE_ESCAPED ? b->tally : 0;
    return 1;
}
/* counts for the one-line log: how many latched, how many of each fate, how many with a ledger */
static void kbb_summary(const struct kbb_tab *t, int esc_state, int *nd, int *ne, int *nl, int *na, int *nledger)
{
    int i; *nd = *ne = *nl = *na = *nledger = 0;
    for (i = 0; i < t->n; i++) {
        switch (kbb_fate(&t->l[i], esc_state)) { case KBB_FATE_DEAD: (*nd)++; break; case KBB_FATE_ESCAPED: (*ne)++; break; case KBB_FATE_LEFT: (*nl)++; break; default: (*na)++; }
        if (t->l[i].ledger) (*nledger)++;
    }
}
#endif /* KLHUD_BOARDBOTS_LOGIC_H */
