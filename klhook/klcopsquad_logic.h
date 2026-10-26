/* klcopsquad_logic.h - the PURE parts of klcopsquad.c ([CopSquad]: AI police under each human cop in Cops and Robbers):
 * the session gate, choosing the nearest N unassigned soldiers for a cop, the Follow re-issue timer and the key edge logic.
 * No game reads here: klcopsquad.c feeds it numbers it read; klcs_test.c checks it off-game (tools/run_harness_linux.sh klcs_test).
 * Distances are in the game's units (100 = 1 m); times in ms (GetTickCount). */
#ifndef KLCOPSQUAD_LOGIC_H
#define KLCOPSQUAD_LOGIC_H

#define KLCQ_PER_MAX   8          /* soldiers per cop at most (a ZSquadControl holds 16 receivers: 0x908040 stops at [sc+0x18] >= 0x10) */
#define KLCQ_COPS_MAX  12         /* C&R lobby cap (re/cops_and_robbers.md 1): at most 12 humans, so at most 12 cops */
#define KLCQ_CAND_MAX  64         /* candidate soldiers considered per pass */
#define KLCQ_KEY_DEBOUNCE 150     /* ms: a second edge inside this window is the same press (key bounce / two polls of one tap) */

/* The window this module works in: HOST (role 2) of a game-type-4 session whose sub-mode word is 2 (Cops and Robbers), in a round
   (session state 0x13..0x1f, the window klsync.c / klbotfill.c use). Role 3 (client) never: 0x760e50 returns on a client anyway. */
static int klcq_gate(unsigned long role, unsigned long mode, unsigned long state, unsigned long submode)
{
    return role == 2 && mode == 4 && submode == 2 && state >= 0x13 && state <= 0x1f;
}

/* A candidate soldier: its id (the hook uses the ZFFActor address), its squared distance to the cop, and whether a cop already has it. */
struct klcq_cand { unsigned long id; float d2; int taken; };

/* Choose up to `per` candidates for one cop: the nearest ones not taken and within maxd2 (<= 0 = no limit), nearest first; each chosen
   candidate is marked taken so the next cop's pass cannot pick it. -> how many were written to out[]. */
static int klcq_pick(struct klcq_cand *c, int n, int per, float maxd2, unsigned long out[KLCQ_PER_MAX])
{
    int k = 0;
    if (per > KLCQ_PER_MAX) per = KLCQ_PER_MAX;
    while (k < per) {
        int i, best = -1;
        for (i = 0; i < n; i++) {
            if (c[i].taken || !c[i].id || !(c[i].d2 == c[i].d2) || c[i].d2 < 0) continue;      /* NaN / negative: a bad read, never chosen */
            if (maxd2 > 0 && c[i].d2 > maxd2) continue;
            if (best < 0 || c[i].d2 < c[best].d2) best = i;
        }
        if (best < 0) break;
        c[best].taken = 1; out[k++] = c[best].id;
    }
    return k;
}

/* The Follow re-issue timer: due when never issued (last 0) or period_ms have passed (period 0 = never re-issue after the first). */
static int klcq_due(unsigned long last, unsigned long now, unsigned long period_ms)
{
    if (!last) return 1;
    if (!period_ms) return 0;
    return now - last >= period_ms;
}

/* Key edge: fires once per press (down after up), with a debounce; holding the key does not repeat. */
struct klcq_key { int was_down; unsigned long at; };
static int klcq_edge(struct klcq_key *k, int down, unsigned long now)
{
    int fire = 0;
    if (down && !k->was_down) {
        if (!k->at || now - k->at >= KLCQ_KEY_DEBOUNCE) { fire = 1; k->at = now ? now : 1; }
    }
    k->was_down = down ? 1 : 0;
    return fire;
}

/* Which order a key press means: 1 follow, 2 hold, 3 attack, 0 none. vk = the key that went down, the three bound keys. */
static int klcq_order_of(int vk, int kFollow, int kHold, int kAttack)
{
    if (vk && vk == kFollow) return 1;
    if (vk && vk == kHold) return 2;
    if (vk && vk == kAttack) return 3;
    return 0;
}

/* Clamp the ini numbers: per 1..KLCQ_PER_MAX, follow period 0 or 2..120 s, max distance 5..200 m (as squared units out). */
static int klcq_clamp_per(int per) { return per < 1 ? 1 : per > KLCQ_PER_MAX ? KLCQ_PER_MAX : per; }
static unsigned long klcq_clamp_follow_ms(int s) { if (s <= 0) return 0; if (s < 2) s = 2; if (s > 120) s = 120; return (unsigned long)s * 1000ul; }
static float klcq_maxd2(int metres) { float u; if (metres < 5) metres = 5; if (metres > 200) metres = 200; u = (float)metres * 100.0f; return u * u; }

#endif
