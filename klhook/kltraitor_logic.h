/* kltraitor_logic.h - the pure rules of [Bots] TraitorReveal / Defend / TurnMax (klbot.c, klgrudge.c use them; kltraitor_test.c tests them).
   2026-11-10, owner: "why does it tell u whos a traitor again pre emptively??" and "if someone shoots you another heister should shoot them sometimes".
   No game access here: every input is a number the caller read. */
#ifndef KLTRAITOR_LOGIC_H
#define KLTRAITOR_LOGIC_H

/* why a masked (turned, not yet shown) traitor is shown now; 0 = still hidden */
#define KLTR_REV_NONE     0
#define KLTR_REV_SHOT     1     /* the last bullet that hurt the human came from him */
#define KLTR_REV_KILL     2     /* a crew member died near him */
#define KLTR_REV_TIMEOUT  3     /* he never fired: shown after TraitorRevealMs anyway */

/* now/since in ms (wrap-safe), att_is_him: [player+0x2778] is his actor AND the human lost health lately, crew_death_near: caller saw one */
static int kltr_reveal(unsigned long since, unsigned long now, int att_is_him, int crew_death_near, unsigned long timeout_ms)
{
    if (att_is_him) return KLTR_REV_SHOT;
    if (crew_death_near) return KLTR_REV_KILL;
    if (timeout_ms && (unsigned long)(now - since) >= timeout_ms) return KLTR_REV_TIMEOUT;
    return KLTR_REV_NONE;
}

/* did the human lose health: a real drop (not a heal, not noise) */
static int kltr_hurt(float prev, float cur)
{
    return prev > 0.0f && cur >= 0.0f && cur < prev - 0.001f;
}

/* may an AI heister (record flags, status) be defended against: a bot (flags bit 0), in play (status 0) */
static int kltr_attacker_ok(unsigned int flags, unsigned int status)
{
    return (flags & 1u) && status == 0;
}

/* Defend: one roll per incident. active = attackers already held enemy by Defend, max = DefendMax (0 = none), chance in percent, roll 0..99.
   1 = the crew defends (the attacker goes team Enemy for DefendMs). Over max: no. */
static int kltr_defend(int chance, int roll, int active, int max)
{
    if (chance <= 0 || max <= 0 || active >= max) return 0;
    if (chance >= 100) return 1;
    return roll >= 0 && roll < chance;
}

/* the clock: an attacker is held until (stamp + ms); 1 = expired (wrap-safe, a 0 stamp = not held = expired) */
static int kltr_expired(unsigned long until, unsigned long now)
{
    return !until || (long)(now - until) >= 0;
}

/* TurnMax (klgrudge.c): may one more bot turn on the human; hostile_now = bots already your enemy (not counting this one), max 0 = no cap */
static int kltr_turn_ok(int hostile_now, int max)
{
    return max <= 0 || hostile_now < max;
}

/* the hidden state a HUD reader applies: hide = ours (bit 1 written by TraitorFoe, not yet revealed), revealed = latch */
static unsigned int kltr_mask_flags(unsigned int f, int hide)
{
    return hide ? (f & ~1u) : f;
}
#endif
