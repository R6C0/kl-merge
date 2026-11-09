/* klland_logic.h - pure rules of kljoin.c's [Join] Land= (2026-11-09), so klland_test.c can check them off-game.
 * Land= moves the player a short step from the jump point he was just put on to a better place (DD10 Flat Raid: the 06_Exit jump point at
 * (8300, 0, 1100) lies on the van's drive-in lane and inside the parked van; bench dd10ledgefix1109 died there 3.6 s after the jump, the
 * exit box's south strip (8300, 750) lived through the drive-in and the wait - dd10side1109). The move itself (0x82cc40) is kljoinland.c.
 * All times are GetTickCount() ms; differences are unsigned so a tick wrap does not matter. */
#ifndef KLLAND_LOGIC_H
#define KLLAND_LOGIC_H

#define KLLAND_FIRST_MS  300                   /* the earliest move after the request (the game puts him on the entry within 0.25 s, run RT4) */
#define KLLAND_GIVEUP_MS 3000                  /* not at the entry by then: the jump did not happen (or he left at once): no move */
#define KLLAND_NEAR      300.0f                /* 'at the entry' = feet within this of the entry's place (GUESS: the entry is on the floor, the feet too) */
#define KLLAND_MAXSTEP   2500.0f               /* Land= must lie within this of the entry: a nudge, not a teleport across the map (GUESS) */

static float klland_d2(const float a[3], const float b[3])
{
    float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2];
    return x * x + y * y + z * z;
}

/* Is Land= usable for this entry? 1 yes; 0 = not finite, out of the world, or too far from the entry. */
static int klland_ok(const float land[3], const float entry[3])
{
    int k;
    for (k = 0; k < 3; k++) if (!(land[k] == land[k]) || land[k] < -200000.0f || land[k] > 200000.0f) return 0;      /* NaN / absurd */
    return klland_d2(land, entry) <= KLLAND_MAXSTEP * KLLAND_MAXSTEP;
}

/* One tick of a pending landing. at = tick of the jump request; have = the feet could be read; busy = an action / seat / carrier.
   -> 1 move now, 0 wait, -1 give up (then *why says it). */
static int klland_step(unsigned long now, unsigned long at, int have, const float feet[3], const float entry[3], int busy, const char **why)
{
    unsigned long el = now - at;
    int at_e = have && klland_d2(feet, entry) <= KLLAND_NEAR * KLLAND_NEAR;
    if (el > KLLAND_GIVEUP_MS) {
        *why = !have ? "his place cannot be read" : !at_e ? "he is not at the jump point (no jump, or he moved on)" : "he stayed busy (an action, a seat or a carrier)";
        return -1;
    }
    if (el < KLLAND_FIRST_MS || !at_e || busy) return 0;
    return 1;
}
#endif /* KLLAND_LOGIC_H */
