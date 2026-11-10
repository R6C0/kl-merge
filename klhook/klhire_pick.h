/* klhire_pick.h - [Hire] PickDefault: which body an UNHIRED round starts with (klhire.c klhr_tick). Pure logic, no windows.h,
 * so klhirepick_test.c checks it off-game.
 *
 * Owner 11-07: "my character is random on the first round on arcade even if i pick a character in the arcade menu prior to starting
 * any arcade match". The 10-24 decision (re\shop_hire.md, "Owner decisions" 1) made every unhired round a random default; the owner now
 * expects the Heister page pick (KLChar, [Character] Char=) to hold. PickDefault:
 *   0 = old: every unhired round is a random default
 *   1 = (recommended on) every unhired round starts as the menu pick; a hire still replaces it for its one round
 *   2 = the menu pick in round 1 only, random defaults after (the closest to the 10-24 rule)
 * The pick is NOT used (random instead) when it is 0, out of 1..16, Kane (9) / Lynch (10) (hire-only, owner 10-24 rule 1: kept), or
 * has no body on this level (a Dead Men heister without the level's wardrobe). round = the round about to start, 1-based.
 * Online (klcharonline.c) has no random default: there 1 and 2 both keep the saved pick for every unhired round (2 = Arcade-only rule);
 * an unavailable pick keeps the game's own body. klchar.c klc_set refuses a Kane / Lynch menu pick while PickDefault is on. */
#ifndef KLHIRE_PICK_H
#define KLHIRE_PICK_H

enum { KLHP_USE = 0, KLHP_OFF, KLHP_NONE, KLHP_RANGE, KLHP_HIREONLY, KLHP_NOBODY, KLHP_LATER };
static const char *const klhp_why[] = { "the menu pick", "PickDefault=0", "no menu pick", "pick out of range", "Kane / Lynch are hire-only", "no body on this level", "PickDefault=2: round 1 only" };

/* returns the body to use (1..16) or 0 = roll a random default; *why (may be 0) gets the KLHP_ reason */
static int klhp_default(int mode, int round, int pick, int avail, int *why)
{
    int w, r = 0;
    if (mode != 1 && mode != 2) w = KLHP_OFF;
    else if (!pick) w = KLHP_NONE;
    else if (pick < 1 || pick > 16) w = KLHP_RANGE;
    else if (pick == 9 || pick == 10) w = KLHP_HIREONLY;
    else if (mode == 2 && round > 1) w = KLHP_LATER;
    else if (!avail) w = KLHP_NOBODY;
    else { w = KLHP_USE; r = pick; }
    if (why) *why = w;
    return r;
}

/* klcharonline.c init: with hire on and [Hire] OnlineIgnoreChar=1 the saved Char was zeroed (online = Arcade, gap G1 of 10-27). With
 * PickDefault on, Arcade honours the pick, so online keeps it too, except Kane / Lynch (hire-only in both). 1 = zero the saved Char. */
static int klhp_online_zero(int hire_on, int ignore_char, int mode, int pick)
{
    if (!hire_on || !ignore_char || !pick) return 0;
    if (mode != 1 && mode != 2) return 1;                  /* PickDefault=0: the old G1 behaviour */
    return pick == 9 || pick == 10;
}

/* klchar.c klc_set, KLChar menu spinner. Owner 11-10: "ai heisters screen ... only lets me go to 12/17 and onwards not backwards". With PickDefault on, Kane (9)
 * / Lynch (10) were REFUSED outright, so the spinner (Char value 11 = counter 12/17) stepping back to 10 was dropped and the value stuck at 11 (and stepping
 * forward from 8 stuck at 8). Fix: skip them in the direction of travel. cur = the value now, want = the value the menu asks for (already clamped 0..16);
 * returns the value to store. Not a hire-only pair (pickdef off / not 9,10) -> want unchanged. Going down from 10/9 lands on 8 (never below 0 : 8 >= 0);
 * a jump from below up lands on 11; a jump from above down lands on 8. */
static int klhp_skip_hireonly(int pickdef, int cur, int want)
{
    if (!pickdef || (want != 9 && want != 10)) return want;
    return want > cur ? 11 : 8;
}

#endif /* KLHIRE_PICK_H */
