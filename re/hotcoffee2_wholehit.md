# Hot Coffee II: why a crew bot loses a whole health bar in one pass (offline reading, refutation pass)

Scope: DM01B in slot F03, live zip ea8cbc82. Read only: KLHook.log, klbalance.c, kl2.exe via debug/dasm.py,
the zip at C:\kl_build_1018\owner_1018\Maps\DM01B\F03_Main.zip. Nothing was launched or written except this file.
Marks: GUESS = not proven by a log line or by disassembly. This file replaces the first version; each earlier
claim is listed in section 5 with its verdict.

## 1. L102, rec 5 (167 -> 0 in one 50 ms pass at 01:35:58.5, at (684, -15, 9215))

Log ranges (KLHook.log): L102 lines 1450143-1476925 (kill at 1453685, DIED at 1453686); L103 1480417-1510750;
L104 1510751-1542199. "balance: LogCrewHitsBig=100" is printed at the start of L102 (1447658), L103 (1477927) and
L104 (1508267), so single drops of 100 or more were NOT rate limited in any of the three runs.

- The sampler (klbalance LogCrewHits) reads each AI heister's health object [actor+0x5fc] (cur +4, max +8) every
  50 ms. It sees the change, not the cause. It does not wrap the damage routine, so it logs NO bullet hits at all.
- VERIFIED: the 167 -> 0 step is one discrete event. No drop was hidden by the rate limit in the 0.87 s before it.
- VERIFIED: the victim next to rec 5 is soldier 927 at 3.3 m; soldier 935 at 8.3 m survived.
- NOT PROVEN: that 927 died in the same pass. Its death time is only bounded to 57.63-58.50 s (the sampler lists
  living soldiers only), so "same pass" is not shown. GUESS only.
- Nearest car with a VehicleEffects controller is car #15 (node 4325), 2.4 m from the site. The Explode controller
  (GarageWallExplosion, node 13025) is 20.9 m away: ruled out. The van and BotDown are ruled out for rec 5 (BotDown
  is Enable=1 but wrote nothing for rec 5; the van-departure kill needs veh state >= 5). The human was idle about 50 m away.
- Base rate (offline, L102 census lines of living crew): 0.3 % of samples are within 1.5 m of any of the 46 campaign
  cars, 3.7 % within 2.5 m, 11 % within 3.5 m. So a crew bot 2.4 m from a car is not the normal state: the proximity
  is mildly informative, but it is also what a bot standing in cover next to a car looks like. Not proof.
- GUESS (new, weak): both victims sit radially away from car #15, and their back-rays meet about 0.4 m from it.
  Consistent with a blast at the car; equally consistent with the geometry of cover positions.

## 2. Damage paths that can take a whole bar

klbalance scales the six-factor float table R = [0x168d7c0]+0x6ac+L*0x70, read by 0x591b60 / 0x8b8050 / 0x7c1ba0.
0x591b60 is applied inside 0x61a980 (ZFFActor slot 423, ProjectileHit) and only when the attacker is a soldier.
CORRECTION: the table is also read by 0x8b8050 and 0x7c1ba0, so "scales bullet damage only" is not shown;
what each of those two scales was not decoded here (GUESS: other damage or accuracy terms).

| Path | Goes through | Scaled by klbalance | Seen as |
|---|---|---|---|
| Bullet | 0x61a980 -> 0x591b60 | yes, with a soldier attacker | health step |
| Melee / point-blank | handler 0x6050a0 -> slot 421 (0x69f900, +0x694) -> slot 422 (0x8689c0, +0x698); kind 1 (GUESS) | not shown | health step |
| Vehicle explosion / fire | same chain, kind 9 blast (GUESS) | not shown | health step; "NO TARGETER ... blast / fall / script?" hint needs no aimer |
| Ragdoll impulse | 0x772c60 builds {kind 10, amount 10000.0, impulse > 6.0}, called from the handler 0x6050a0 on message [0x1547bc8] | not shown | health step |
| Van-departure kill | amount 1,000,000 when veh state >= 5 (klbotdown / klescort) | no | only in state 5 |
| Scripted kill | message 0x1c -> ZSoldier switch 0x608050 (slot 1) -> slot 96 (0x8473a0) | not shown | health step |

- CONFIRMED by disassembly: the 421 -> 422 chain, 0x772c60 (kind 10, 10000.0, 6.0) and message 0x1c -> slot 96.
  The gates in front of 0x772c60 (what makes the impulse exceed 6.0, and which message) are NOT decoded.
- CORRECTION: the first version said the scripted kill goes "-> actor slot 72". That slot was not confirmed; it is
  the ZSoldier message switch 0x608050 (vtable 0xbd0954, slot 1) that leads to slot 96.
- Record layout (+0 attacker, +8 kind, +0x10 position, +0x28 amount) is read from the code; the kind numbers 1 and 9
  for melee and blast are GUESS.

## 3. What the logs say about police damage and the other runs

- REFUTED as evidence: "police hits are -1 chip damage, so police cannot have produced 167". Those are post-scale
  values at CopToCrew 0.01 (and PointBlankToCrew 5 in KLHook.ini). An unscaled police bullet is about 100-200 (GUESS),
  so 167 is not impossible for an unscaled path. Chip size after scaling says nothing about the unscaled sources.
- REFUTED as evidence: "no bullet-hit line names rec 5". No such line exists in the hook (the sampler does not wrap
  the damage routine), so its absence proves nothing. The LogCrewHits "NO TARGETER" hints are the only cause hints and
  they need no soldier to be aiming at the victim.
- CORRECTED: "L103 had no drop >= 10". Only the first 400 lines per round are listed and drops of 10-99 after about
  42 s were not printed. The sound evidence is the DIED lines (never rate limited) plus the BIG=100 cover: L103 had
  1 chip death and no drop of 100 or more; L104 had 0 deaths. So: cars-only builds showed no whole-bar drop in 2 runs.
  That is 2 runs, not proof (the earlier scoreboard was 4 of 4 runs with one-shots on the live zip, 0 of 2 cars-only).
- CORRECTED: "LogCrewHitsBig is not in the 1018d build". It was armed in L102-L104 (see section 1).
- CORRECTED: the file "near.txt" cited in the first version does not exist in re/. The car distances come from
  the scratch scripts (cars_near.py and descendants) over the zip, which are not part of the repo.
- CONFIRMED: L93 rec 1 died from ONE 340 drop with no soldier within 15 m (re/hotcoffee2_oneshot.md), the same shape.

## 4. Conclusion (downgraded)

What is shown: one 167 -> 0 step in one 50 ms pass in L102; the path is not the van, not BotDown, not the garage Explode
controller, not a human action. What is NOT shown: which of the unscaled paths fired. The car blast is the best fit
(GUESS): a campaign car 2.4 m away, both victims displaced away from it, and cars-only builds (cars changed) had
0 whole-bar drops in 2 runs. Against it: no recovered car health or blast radius, no explode record, and the 3.3 m
soldier's death time is unbounded. The sniper-leftover idea from hotcoffee2_oneshot.md is neither supported nor
refuted by this pass.

## 5. Verdict on each claim of the first version

| Claim | Verdict |
|---|---|
| 167 -> 0 in one 50 ms pass | verified |
| soldier 927 died in the same pass | unproven (bounded 57.63-58.50 s); GUESS |
| 8.3 m soldier survived | verified (id 935) |
| no bullet-hit line names rec 5 | meaningless: the hook logs no bullet hits |
| police hits are -1 chip so police cannot do 167 | refuted as an argument (post-scale numbers) |
| L103 had no drop >= 10 | wrong as stated; no drop >= 100 (BIG=100) and 1 chip death |
| LogCrewHitsBig is not in the 1018d build | wrong, it was armed |
| klbalance scales bullet damage only | not shown; the table is read by 3 routines |
| 0x608050 -> actor slot 72 | not confirmed; 0x608050 -> slot 96 is |
| 0x772c60 kind 10 / 10000.0 / 6.0 | confirmed, gates undecoded |
| Explode controller 21 m away | verified (20.9 m) |
| car #15 is nearest | verified (2.4 m), base rate 3.7 % of crew samples within 2.5 m of some car |
| near.txt | does not exist |
| car blast is the cause | GUESS, best fit |

## 6. Verify (next run, not done here)

1. Log the hit record kind ([record+8]) and amount ([record+0x28]) at 0x8689c0 and 0x772c60 when amount >= 100, with
   the attacker pointer and [record+0x10]. Kind 10 or 9 with a position at a car confirms the car; attacker 0 with a
   large amount suggests a script; kind 1 melee. Needs a klbalance change by the other session (read only here).
2. Log the VehicleEffects state of every car within 5 m when a crew drop of 100 or more happens, and its state 3 s before.
3. Decode the gates before 0x772c60 (message [0x1547bc8], the impulse value source) to see whether a car blast or a
   ragdoll toss triggers it.
4. Record the time of every soldier death in the sampler (not only the survivor list) to settle "same pass".
5. A repeat of the live zip with the cars removed from the 5 sites (a/b test) is the only direct test of the car cause;
   the cars-only build is the opposite test (cars changed, 0 of 2).
