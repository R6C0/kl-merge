# Online FA escape van: states and how to hold it (static read of kl2.exe, 2026-10-26)

Source: BO11 log (KLHook.log, bench solo/BO11/inst1): van called 08:35:11.963, states 1, 3, 6, 7, 0.
ZAnimatedVehicle +0x14 health went 3000 -> 2730 -> 976 (state 3) -> 0 (state 6). Static only, nothing run.

## Rules fields (Sv rules, vtable 0xbd2eb4; Arcade/Cl is ZGameRulesHeist 0xbd3514)
- +0x1d8 float state timer, +0x1dc byte state, +0x1e0 boarding object, +0x1e4 vehicle group
- +0x1ee byte = LAST VEHICLE CALLED (an index), NOT a hold. Do not write it.
- +0x1f0/+0x1f4/+0x1f8/+0x1fc state-timer overrides, +0x364 total van time, +0x4c clock left
- Vehicle (OnlineEscAnimatedVehicle, RTTI 0xb73408): +0x6c arrive, +0x70 wait (about 8 s stock), +0x74 leave, +0x78 reset
- ZAnimatedVehicle: +0x14 health, +0x18 max/4, +0x21 Invulnerable byte, +0x22 frame update

## States (Sv tick slot 195 at 0x727610, setter slot 194 at 0x51e390; Cl setter 0x5b1410)
1 called / van driving in. 3 van arrived, waiting for boarding (timer from vehicle +0x70).
5 normal timeout, van leaves with the crew. 6 van DESTROYED / failed (health 0 while empty or
slot 94 grade 2 at 0x839380 -> slot 194(6)). 7 post-fail cooldown (about 6 s in BO11, state 6 about 10 s). 0 idle.

## Why BO11 went 3 -> 6 after 1 s
Not a timer and not the box. The van was shot: health 2730 -> 976 -> 0 while empty, and the hit
path ends in state 6. [VanBlow] Enable=1 EmptyDelay=1500 is in that run's ini, so the van is also
blown on purpose a short time after arrival when empty. Either way, 1 s in state 3 is damage-driven.
BO9 (normal sequence) did not take damage.

## Side effects of the knobs
- [+0x1d8] written upward in state 3 extends the wait; HoldEscape (slot 152) itself adds only 5.0 once per vehicle.
- [+0x1f4] override: extends wait too, but also changes later logic; prefer the timer.
- [+0x1ee]: never write; changes which vehicle the code thinks was called.
- ZAnimatedVehicle +0x21 = 1 stops damage (klescort KLE_VEH_INV 0x21, kle_shield_off).

## Arcade vs online
Arcade keeps the van for AI because rules +0xb4 = 0x6840a0 and ZAllyEscapeBox (0x907a50) count AI
allies inside the box (via [rules+8] records, stride 0x74). Online: AI heisters have no [rules+8]
records (humans only), Sv slot 45 accepts only player actors, 0x7f6850 is false online so the
ZAllyEscapeBox processing is a no-op, and there is no board tactic. So the van sees an empty box
and the wait runs out or the van gets destroyed.

## Recommendation (one fix, host side, in klbotfill/klescort pass)
Shield and hold while bots walk: from state 3 until state 5, while any walking bot is within about
30 m of the box centre, write the van object +0x21 = 1 (invulnerable) and keep [rules+0x1d8] >= 3.0
whenever a bot is within 15-20 m. Guards: only when [rules+0x1dc] == 3, total extra hold capped at
15-20 s (then stop writing and let it end), keep the value below 127 on any byte, restore +0x21 = 0
on state change or when the cap is hit, and disable [VanBlow] EmptyDelay while the hold is active.
Also call the van no later than about 90 s before the clock ends.

## Not resolved
The getter at 0x72c9a0 -> 0x5b1400 (byte [score+0x370] xor 0xac: 1 = timer to 0, 2 = skip
announcement) was not fully traced; 0x594b10 is called only from 0x6d7d71 and 0x6d7d88. The exact
damage source in BO11 (bots, VanBlow, or cop fire) is inferred from the log, not proven.
