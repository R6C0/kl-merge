/* klvanshield_logic.h - [VanBlow] ShieldUntilBoarded / HealFloor pure decisions (2026-11-07, round "burning van that never picks up").
   klescort.c includes it. No windows.h. WHY: DM09 rounds 2026-11-07 showed the van arriving at 68..1215 of 3000 hp (the cops' FakeTarget
   fires during the drive-in), then VanBlow's EmptyDelay dropped the shield and it blew up 2-4 s later while the crew was still walking
   to it. ShieldUntilBoarded keeps the shield while a loyal heister could still board; HealFloor restores health to max when it is below
   a percentage (the +0x14 write is the same GUESS as HealthMax's). Both default off. */
#ifndef KLVANSHIELD_LOGIC_H
#define KLVANSHIELD_LOGIC_H

/* can this record still board? in play (status 0), not a traitor (flags bit 2); used. Status 4 = aboard, 7 = dead are no. */
static int kvs_rec_can(int used, int status, int flags)
{
    return used && status == 0 && !(flags & 2);
}

/* keep the van shielded (do not run the empty clock out)? on = key; aboard = records aboard; can = records that could still board;
   waited_ms = time since the wait began; cap_ms = longest this may last (a van cannot wait for ever). */
static int kvs_keep(int on, int aboard, int can, unsigned waited_ms, unsigned cap_ms)
{
    if (!on || aboard > 0) return 0;      /* aboard: the old rule already shields it */
    return can > 0 && waited_ms < cap_ms;
}

/* restore health? floor_pct 0 = off; true when 0 < hp < max * floor_pct / 100 (a dead van, hp <= 0, is not raised) */
static int kvs_heal(int floor_pct, float hp, float max)
{
    if (floor_pct <= 0 || !(max > 0.0f) || !(hp > 0.0f)) return 0;
    return hp < max * (float)floor_pct / 100.0f;
}

/* ShieldWhileWaiting (2026-11-08): shield an EMPTY waiting vehicle? on = key; veh = rules state byte (3 = waits at the pickup, 4 = also a
   wait; GUESS: 4 is the second wait state, see klescort.c kle_veh_pass); aboard = records with status 4; round_over = the vehicle is
   destroyed / gone (state >= 6, a proxy: no separate round-end flag is read here); waited_ms = since the wait began; cap_ms 0 = no cap.
   Boarding (aboard > 0) ends it (the old rule shields a held van then), so does the vehicle leaving (state 5) or the cap. */
static int kvs_wait_shield(int on, int veh, int aboard, int round_over, unsigned waited_ms, unsigned cap_ms)
{
    if (!on || round_over || aboard > 0) return 0;
    if (veh != 3 && veh != 4) return 0;
    return cap_ms == 0 || waited_ms < cap_ms;
}

/* ShieldDriveIn (2026-11-08): shield the vehicle while it drives in? vanwait09_1108 (DM09, nobody boards): called at 05:02:19 (state 2),
   waiting at 05:02:26 (state 4) with 1245 of 3000 already gone, so ShieldWhileWaiting froze a burning van. on = key; veh = rules state
   byte; 2 = driving in (seen in that log: 'state now 2' at the call, 4 seven seconds later; GUESS that 1 is never a moving vehicle, so 1
   is left out). */
static int kvs_drivein_shield(int on, int veh)
{
    return on && veh == 2;
}
#endif
