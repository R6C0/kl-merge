/* klsabotage_logic.h - the PURE parts of klsabotage.c ([Sabotage] VanHold: the Undercover Cop holds the escape van N seconds).
 * No game reads here: klsabotage.c feeds it numbers it read; klsabot_test.c checks it off-game (tools/run_harness_linux.sh klsabot_test).
 * Research and the per-map tables: re/ucc_sabotage.md. Times in ms (GetTickCount) unless named _s. */
#ifndef KLSABOTAGE_LOGIC_H
#define KLSABOTAGE_LOGIC_H

#define KLSAB_KEY_DEBOUNCE 150      /* ms: a second edge inside this window is the same press */
#define KLSAB_HOLD_MIN     1
#define KLSAB_HOLD_MAX     20       /* seconds: one press never adds more (stock 'hold the driver', slot 152 0x8b3930, adds 5.0) */
#define KLSAB_TIMER_CAP    40.0f    /* seconds: the state timer [rules+0x1d8] is never written above this (stock wait is ~8 s, drive-in ~7 s) */

/* The window: HOST (role 2) of a game-type-4 session in the Undercover Cop sub-mode ([0x168e59c] == 1), in a round (state 0x13..0x1f,
   klsync.c / klcopsquad.c's window). any_mode = 1 (test key [Sabotage] AnyMode) also accepts plain FA (0) and C&R (2). */
static int klsab_gate(unsigned long role, unsigned long mode, unsigned long state, unsigned long submode, int any_mode)
{
    if (role != 2 || mode != 4 || state < 0x13 || state > 0x1f) return 0;
    return submode == 1 || (any_mode && submode <= 2);
}

/* Who may press: the local player must be the Undercover Cop. ucc = his ZFFPlayer byte +0x2729 (set to 1 by the UCC pick in the Sv rules'
   slot 4, 0x40faf3 -> 0x4622b0), police = +0x2723 (a revealed / dead-and-respawned cop is police: no sabotage then). any_player = test key. */
static int klsab_may_press(int ucc, int police, int any_player)
{
    if (any_player) return 1;
    return ucc == 1 && police == 0;
}

/* The hold. vstate = [rules+0x1dc] (1/2 driving in, 3/4 waiting at the stop, 5 leaving, 6 destroyed, 7 cooldown, 0 idle;
   re/van_hold_online.md), timer = [rules+0x1d8] seconds left in that state, used = this visit already held (reset when the state
   goes back to 0 or 7), hold_s = the ini seconds. -> the new timer value to write, or -1 = nothing to do.
   Only in states 1..4 (a van under way or waiting); never past KLSAB_TIMER_CAP; a NaN / negative / absurd timer is a bad read. */
static float klsab_hold(int vstate, float timer, int used, int hold_s)
{
    float t;
    if (used || vstate < 1 || vstate > 4) return -1.0f;
    if (!(timer == timer) || timer < 0.0f || timer > 1000.0f) return -1.0f;
    if (hold_s < KLSAB_HOLD_MIN) hold_s = KLSAB_HOLD_MIN;
    if (hold_s > KLSAB_HOLD_MAX) hold_s = KLSAB_HOLD_MAX;
    t = timer + (float)hold_s;
    if (t > KLSAB_TIMER_CAP) t = KLSAB_TIMER_CAP;
    return t > timer ? t : -1.0f;
}

/* A new van visit: the 'used' mark is cleared when the state returns to idle (0) or the post-visit cooldown (7). */
static int klsab_new_visit(int prev_state, int vstate)
{
    return prev_state != vstate && (vstate == 0 || vstate == 7);
}

/* Key edge: fires once per press (down after up), with a debounce; holding the key does not repeat. */
struct klsab_key { int was_down; unsigned long at; };
static int klsab_edge(struct klsab_key *k, int down, unsigned long now)
{
    int fire = 0;
    if (down && !k->was_down) {
        if (!k->at || now - k->at >= KLSAB_KEY_DEBOUNCE) { fire = 1; k->at = now ? now : 1; }
    }
    k->was_down = down ? 1 : 0;
    return fire;
}

static int klsab_clamp_hold(int s) { return s < KLSAB_HOLD_MIN ? KLSAB_HOLD_MIN : s > KLSAB_HOLD_MAX ? KLSAB_HOLD_MAX : s; }

#endif
