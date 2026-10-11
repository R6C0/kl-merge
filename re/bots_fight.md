# The AI heisters against YOU: tougher (by range), a traitor that means it, an answer when you shoot them

Track O, 2026-10-11; second state after the review (`re/bots_fight_review.md`, ACCEPT WITH FIXES - section 9 says
what was done about each point). The owner: 'also need something for making them a bit more bullet spongey, feels a
bit one sided so the player could just easily turn on them, i saw one backstab me it was too lenient i could get away
with killing him, so make it a lil less forgiving and if i shoot them but before i turn traitor the more i shoot the
more they shoot back or they might just try and kill me straight away or they just accept getting shot stuff like
that' - and, later: 'fyi i probably meant more bullet spongey at longer ranges i feel like compared to the bot'.

**NOTHING HERE HAS RUN IN THE GAME.** Static reading of kl2.exe build 0490 (EXE), the owner's own `KLHook.log` of
today (LOG), three off-game harnesses (HARNESS). Code: `klhook/klgrudge.c` (new, NOT WIRED), `klhook/klbot.c`,
`klhook/klbalance.c`. Every new key is off by default; a hook built from these sources with no new key set writes the
same things as before (one difference in the LOG at `[Bots] Log=2`: section 3.5).

## 0. Short answers

| asked | answer |
|---|---|
| bullet sponge at range | The GAME already lowers a bullet with distance, for both sides alike; what differs far away is who hits (section 1). A true per-hit factor **cannot be had inside the hook's rules** (1.3). Built instead, by data: `[Balance] YouToCrewFar` - the one float 'your bullet on an AI heister' is re-written every 50 ms for the heister you are shooting at. An APPROXIMATION (1.4). Proposal `YouToCrew=0.6 YouToCrewFar=0.5` from 8 m to 35 m |
| why the backstabber was easy | He needs 7-14 body hits on you, you need 4-7 on him or ONE head shot at any range, and he never gets a head shot (1.1). LOG: the traitor of 12:36:22 was dead 2.8 s after his flag was set. With `Tune=1` FOUR bots carried the traitor flag in that round - 'traitors allowed' is a switch, not a count |
| a backstab that means it | `BackstabHealth`, `BackstabAim`, `CrewToYou` (it is 'traitor -> you'), the moment of the turn (`BackstabNear / Behind / Busy / Wait`), `TraitorsMax` (section 3) |
| what the game does when you shoot crew | A per-bot sum of the SHARE OF HIS HEALTH you took, forgiven after 10 s without a hit; a yellow card at 25 %; the bot turns on you over 100 % (Arcade level 1) - never before he is dead; KILLING a crew member makes YOU the traitor (section 2) |
| personalities | `[Bots] Grudge=1`: ESCALATES / SNAPS / TAKES IT per bot per round, through the game's own per-bot switch, data only (section 4). TWO THINGS TO KNOW FIRST: killing a bot that fights you by Grudge makes you the traitor unless `GrudgeMark=1` (4.3); an escort is not turned while klescort.c holds it unless klescort.c gets three lines (4.4) |

## 1. The sponge, by range (Risk=2, Arcade level 1 = the owner's game)

### 1.1 Measured from the level data (`kl_map_ai.bullet()` = 0x46ef60; the bank `z_cover3\M03`; no regeneration counted)

The crew's rifle and the player's starting rifle are ONE weapon template, `Rifle_zastavam85`: the ammo's four damages
80 / 50 / 40 / 15 over the gun's four ranges 6 / 14 / 30 / 60 m, x the Arcade range-band factors 0.9 / 1.3 / 1.6 /
1.0 (fields 39..42), x 0.8 when the shooter is an NPC (field 37) or x 1.0 for the player (field 38). An AI heister
has 252 (280 x 0.9), the owner 401.5 (550 x 0.73). Head: x 10 on an NPC victim; an NPC shooter never gets a head
factor and the player takes at most x 1.75 (`re/balance.md` 1 b).

| distance | your bullet | his bullet | you kill him today (YouToCrew 1.0): body / head | he kills you: CrewToYou 1.0 / 1.25 |
|---:|---:|---:|---|---|
| 5 m | 72.0 | 57.6 | 4 / 1 | 7 / 6 |
| 10 m | 58.5 | 46.8 | 5 / 1 | 9 / 7 |
| 15 m | 64.2 | 51.3 | 4 / 1 | 8 / 7 |
| 30 m | 52.0 | 41.6 | 5 / 1 | 10 / 8 |
| 50 m | 37.3 | 29.9 | 7 / 1 | 14 / 11 |

(The step up at 15 m is the game's: the band factor goes 0.9 -> 1.3 at the second range. Beyond 60 m: 15 / 12.)

### 1.2 What that says about the owner's remark

- **Damage does fall off with distance - for both sides by the same curve.** In damage you need about half the hits
  he needs AT EVERY RANGE (the ratio 0.8 and the two health numbers are constants). So the damage table is not what
  makes range one-sided.
- **Who hits is.** Yours: the mouse, and a head shot is x 10 on a heister at any range - one bullet at 50 m still
  kills (373 of 252). His: `[[soldier+0x6d8]+0x10]` = ZSoldier field 4, **50 per cent on six of the seven AI heisters
  and 90 on one** (level data of the bank; `kl_map_ai` crowd), read at every burst: the miss share is 1 - it / 100
  (0x719cd8..0x719ce1, in the burst chooser 0x719b00 that the fire task's set-up 0x8b84b0 calls), and the aim object
  gets a number from 0x884a70(tuning +0x374 = 2.5, +0x378 = 0.3, accuracy) (0x557b5b..0x557b88; 0x884a70 NOT READ -
  if it is a linear range, 1.4 at 50). ASSUMED, NOT READ: that this number is an aim error that costs more hits the
  farther the target is. Nothing in 0x719b00 itself takes the range: its slot-33 float (0x4cdca0) is a value that
  decays with time (0x4f1c00), compared with 1800 x 0.008 x accuracy (tuning +0x108). So the lead's reading - at range the player soaks their fire while they drop to his - fits what was
  read, but **how a heister's hit rate falls with distance is NOT established**.
- The player also gets his health back (8 s + 8 s under Risk=2); so does a heister (ZSoldier field 8 = 50: 8 s / 8 s).

### 1.3 A true per-hit factor by distance: NOT POSSIBLE inside the hook's rules

The hit is priced in the VICTIM's own routine, `ZFFActor` vtable slot 423 = 0x61a980 (gun x body part x `[hit+0x18]`
at 0x61ac98, the who-shoots-whom float from 0x7c1ba0 at 0x61ae18); the hit record carries the attacker (`[hit+0xc]`)
and the scale (`[hit+0x18]`), so a wrapper THERE would know shooter, victim and distance. But that routine is reached
through the actor's vtable only, and:

- a private vtable copy on each AI heister changes the first dword of the actor - the very value every part of this
  hook knows a ZFFActor by (`KLB_ACTOR_VT` in klbot.c, klescort.c, klfed.c, klgrudge.c, klbalance.c) and the game's
  own class tests may compare too: not the 'one object nobody identifies by its vtable' the point-blank keys use;
- the health object `[actor+0x5fc]` has no virtual in that path: the new health is stored directly (0x61f032);
- the point-blank keys' trick (the name look-up between writing the hit record and sending it) exists only in the
  soldier's fire task, not for the player's bullets;
- the only DATA that lowers damage with distance is the weapon template (ranges, damages, bands) - shared by every
  carrier of that gun, the AI heisters shooting police included.

### 1.4 What was built instead: `[Balance] YouToCrewFar` (klbalance.c 2 a6) - an approximation by data

`YouToCrew` (R+0x14) is read by 0x7c1ba0 for the PLAYER's bullet on an Ally NPC and by nothing else - not by the
police's hits on the crew (R+0x00, `CopToCrew`), so it never composes with `CopToCrew`; Ramp does not touch it; a
heister who has TURNED stays team Ally, so it is also 'you -> traitor'. The hook now re-writes that ONE float every
pass (50 ms) as

    YouToCrew x ( 1 at YouToCrewNearAt metres or nearer .. YouToCrewFar at YouToCrewFarAt or farther, linear, steps of 0.02 )

for the distance to **the heister you are most likely shooting at**:

1. the crew member your last counted hit was on, for `YouToCrewHold` seconds (4) after it - the game's own sum of
   your hits on him rose (`[rules+0xac4+0x30*victim]`, written by 0x4d17f0; klgrudge.c never writes that one);
2. else the nearest heister in play that carries the traitor mask (hits on a marked traitor are not counted, 2.2);
3. else the FARTHEST heister in play - so the first bullet of a fight is priced for the far side.

**What is wrong with it, plainly:** the game has one number for all heisters, so hit n is priced by where hit n - 1's
victim stands. Change targets between a near and a far heister and one bullet (two at most: the pass is 50 ms, the
rifle fires every 86 ms) has the other's price; the first bullet at a near, loyal heister while the others are far
is priced far (weak). It is off for a police player (`FedToCrew` is his flat number) and while YOU are the traitor
(the game counts no hits then: flat `YouToCrew`). The table's stock values come back as all the dial's do.

| distance | flat 0.4 (the first report): body / head | **0.6 + Far 0.5, 8 m .. 35 m (proposal)**: factor, bullet, body / head | 1.0 + Far 0.4 (close as today): body / head |
|---:|---|---|---|
| 5 m | 9 / 1 | x 1.00 = 0.60, 43.2, **6 / 1** | 4 / 1 |
| 10 m | 11 / 2 | x 0.96 = 0.58, 33.7, **8 / 1** | 5 / 1 |
| 15 m | 10 / 1 | x 0.88 = 0.53, 33.9, **8 / 1** | 5 / 1 |
| 30 m | 13 / 2 | x 0.60 = 0.36, 18.7, **14 / 2** | 10 / 1 |
| 50 m | 17 / 2 | x 0.50 = 0.30, 11.2, **23 / 3** | 17 / 2 |

Against 'he kills you' 7 / 9 / 8 / 10 / 14: the proposal is 'alike' up close (6 against 7), one notch tougher at
10-15 m, and clearly a sponge from 30 m on, where his bullets rarely find you. The third column is for an owner who
wants close range to stay exactly as deadly as today.

- **`[Bots] CrewHealth=<f>`** (klgrudge.c): the bot's health object `[actor+0x5fc]`, maximum x f, his health kept at
  the same share. Tougher against EVERYBODY: to keep the police where they are, multiply `CopToCrew` by f. The
  fall-back if the range key misbehaves live; not needed beside it. (A key of `[Bots]`, not `[Balance]`: it lives
  in klgrudge.c, which owns the per-bot health tracking.)
- **The fed** (`[Fed] Player=1`, FedMirror=1): `[Balance] FedToCrew=<n>` = your bullet on a heister while you are
  police, flat at every range, written into the slot a police player's bullet on an Ally NPC reads (R+0x0c:
  0x7c1bf0) while the pairs stand exchanged. No key = YouToCrew's number. Proposal **1.0** (the owner wants the fed
  to be able to kill: 4-7 body hits as today).

## 2. What the game does when a heister is shot by the human (EXE, read 2026-10-11)

2.1 **When a bot counts you as an enemy.** ZSoldier's target test 0x882470, for an Ally / Mercenary soldier in Arcade
(0x882636 .. 0x882726): the player is a friend unless `[player+0x2723]` (police), `[player+0x2726]` (traitor), the
bot's record mask 2 at +0x79 (0x8826b6), or **0x6a1c40(rules, index)**: `float [rules+0x884+4*index] > max([R+0x18],
25.0)` (0x6a1c7e: 25.0 at 0xd1b398; [R+0x18] = 100 90 80 70 60 40 25.. by Arcade level = klbot.c's `Retaliate`).
A SECOND READER of that switch (found by the review): 0x570a1b in 0x5706a0, the list of friendly players a soldier
keeps - a player is left out for the same 'mask 2 OR 0x6a1c40'. Both places treat 'held by the float' exactly as
'mask 2'. NOT SEARCHED: indirect calls of the float's getter (rules slot 141 = 0x78d5c0; it has no direct caller).

2.2 **What the float is.** 0x4d17f0(rules; victim actor, &(-damage), attacker), called from the NPC damage routine at
0x84777d in Arcade. Only for a victim with a crew record (0x78f470) and a ZFFPlayer attacker; not when you or the
bot carry flag 1 'traitor' in the score table (`[score+0x1d4+4*i]`, slot 114 = 0x771a10). It adds
`100 * damage / the victim's maximum health` (slot 414 = 0x574060 = `[[actor+0x5fc]+8]`; 0x4d1973 .. 0x4d19aa:
maximum - x, / maximum, x 100.0 at 0xb3dde8, - 100) to two sums and notes the time:

    A[attacker][victim]  = [rules + 0x884 + 4 * (12 * attacker + victim)]     you are attacker 0 in Arcade (push 0 throughout)
    B[victim][attacker]  = [rules + 0xac4 + 4 * (12 * victim + attacker)]
    time                 = [rules + 0x614 + 4 * (12 * victim + attacker)]  <- [rules+0x50]

So `Retaliate` is **per victim, in per cent of his health**. B at 25.0 or more (0x4d19e4) -> slot 117 = 0x586c10:
the YELLOW CARD (byte `[rules+0xd04+12*victim+attacker] = 1`, flag 0x400 on you; slot 122 = 0x833f70 then lets that
victim kill you without becoming a traitor).
**Its own gates** (0x4d1842 .. 0x4d196d, read as code; the dword is each side's of the score table): nothing is
counted when slot 123 = 0x600470(victim, 0) answers no; when you or the bot carry bit 0x1000 (both pairs of tests,
with and without 0x80, return); when you carry 0x800 and the bot's own sum on YOU (`[rules+0x884+0x30*victim]`) is
not 0; when you carry 8 and the bot 0x80. WHAT bits 8 / 0x80 / 0x800 / 0x1000 mean was NOT READ. In those states
neither Grudge nor YouToCrewFar's rule 1 sees a hit.

2.3 **It forgives.** 0x771af0 (state 0x19): for an attacker without a yellow card, every A that is not 0 and whose
last hit is over **10.0 s** old (0xd1b390) is cleared by slot 119 = 0x521d30 (A, B, time, the card byte). So stock:
a bot turns on you only if you take more than `[R+0x18]` per cent of his health without a 10 s pause - on level 1
that is all of it. **Today the AI heisters do nothing about being shot** (the owner's `Retaliate=0` = stock 100).

2.4 **When YOU become the traitor.** The kill bookkeeping 0x6706b0 (from slot 16 = 0x485740), 0x6709dd .. 0x670a22:
the victim is no policeman, does not carry flag 1, and slot 122(killer, victim) is false -> slot 129 = 0x8fb0d0:
flag 1 on the killer and the local player's byte `[player+0x2726]` (-> every bot is your enemy by 2.1). Wounding
crew never makes you the traitor; **killing one does**. Slot 122 needs the VICTIM to hold a card against the killer,
and a bot never gets one (0x4d17f0 counts ZFFPlayer attackers only). So:
- READ, NOT SEEN: a bot the tactic (0x488eb0: `or byte [rec+0x79],2` + 0x4322f0) or `Backstab` turned carries record
  mask 2 only, not flag 1 - killing your backstabber is, to that bookkeeping, killing a loyal crew member. LOG shows
  record 3 dead 2.8 s after its flag, not who killed it nor what the owner's flags did. L5 settles it.
- The same holds for a bot that `Grudge` made your enemy (4.3).

## 3. A backstab that means it

3.1 **Today.** `Backstab=35`: one bot a round is picked; in play at stage 2+ with 250,000 for 20 s -> record mask 2.
From then the target test 2.1 no longer calls you a friend; he fights you as he fights anybody (his squad and
tactics unchanged - Loot / Board still in his list). NOT READ: at what range and in what bursts an Ally soldier
engages, whether he flees. No warning exists in this path.
LOG (the owner, 12:36 and 12:43, `Tune=1 Traitors=1 Limit=6.0`): records 2, 3, 5, 6 carried the flag in one round,
1 and 6 in the next - all by the game's own tactic at the vehicle (no BACKSTAB line). Record 3: 'traitor flag SET'
12:36:22.687, 'dead' 12:36:25.528.

3.2 **Why it was lenient**: 1.1's numbers (4-7 / 1 against 7-14 / never), his accuracy of 50, your regeneration, and
a turn at the vehicle in front of you.

3.3 **Keys** (defaults = as today):

| key | section | what | proposal |
|---|---|---|---|
| `YouToCrew`, `YouToCrewFar`, `YouToCrewNearAt`, `YouToCrewFarAt`, `YouToCrewHold` | Balance | section 1.4 | 0.6, 0.5, 8, 35, 4 |
| `CrewToYou` | Balance | a turned heister's bullet on you (no other heister shoots at you: it IS 'traitor -> you') | 1.25 (6 / 7 / 8 / 11 hits kill you at 5 / 15 / 30 / 50 m) |
| `BackstabHealth=<f>` | Bots | a bot with the traitor mask (tactic or Backstab alike): maximum x f on top of CrewHealth, same share, from the pass that sees the mask; back when the mask goes | 1.5 |
| `BackstabAim=<%>` | Bots | his accuracy raised to this while he carries the mask, never lowered, put back after. The float is the ZSoldierRout's block (rout+0x34, `re/map_ai.md` 1) that the soldier points at: the hook looks at the other crew records first and does NOT write a block two of them share (one line) | 85 (the crew has 50) |
| `BackstabNear=<units>` `BackstabBehind=1` `BackstabBusy=1` `BackstabWait=<s>` | Bots | klbot.c: after BackstabDelay the picked bot's turn waits until he is within Near of you / more than 90 degrees off the way you MOVE (a GUESS for where you look: the vector at player+0xc14 is the direction of travel; a player who backs away or strafes is judged wrongly) / your health is under 97 %; all that are set at once. `BackstabWait` seconds after the delay was FIRST over he turns at the next pass in which his own conditions hold | Near 1200, Behind 1, Busy 0, Wait 30 |
| `TraitorsMax=<n>` | Bots | with Tune: once n bots carry the flag, 'traitors allowed' is written 0 on every level. A cap PER ROUND: a dead / aboard / escaped traitor keeps his flag to the round start and still counts. Soft: two can turn inside 100 ms | 2 |
| `BackstabMark=1` | Bots | 3.4 | 0 until L5 has been read |

3.4 **`BackstabMark`**: bit 1 of the turned bot's dword in the score table, set by the hook while he carries the mask,
cleared when the mask goes (so it stays on a dead / aboard / escaped bot to the round's end). It is the bit 2.2 and
2.4 test for 'the victim is a traitor'. **It changes the payout** (0x796576 .. 0x79657c, found by the review): an
escaped record WITH that bit keeps its own money and is out of the pool that is split; without it its money goes into
the pool. NOT READ: who else shows the bit (the HUD's crew list is likely to), whether loyal bots shoot at a bot
that carries it. Run L5 first: it says whether the problem exists at all.

3.5 **The health log** (klbot.c `Log=2`): CrewHealth / BackstabHealth going in or back changes the maximum and the
health in one step; the log used to read that as a loss ('lost 126.0 ... ONE STEP' at 378 -> 252). It now prints
'record N (bot): its maximum health changed A -> B (health C -> D): not counted as a loss' for a step in which the
maximum changed, and counts nothing. That is the one log difference without a new key - and only if the GAME ever
changes a bot's maximum by itself.

## 4. When you shoot your own crew: `[Bots] Grudge=1`

4.1 **Mechanism: the game's own switch 2.1, per bot, reversible, nothing else.** The hook keeps its own tally of what
the game adds to A[0][bot] and writes the float: `limit + 1` = he is your enemy, `0.01` = he is not (not 0, so that
2.3's forgiving still runs and clears the yellow-card sum as in stock). While he is your enemy the hook keeps the
'time of your last hit' within 2 s of the rules' clock, or the game would clear the float 10 s after the real hit.
Record mask, B / yellow card, tactics: untouched. No call, no vtable. Acts only while crew record 0 is the human
(the game wires attacker 0).

4.2 **The three**, drawn per bot at its first sight in a round (`GrudgeMix=40,30,30`):

| | behaviour | keys |
|---|---|---|
| ESCALATES | each hit: your enemy for `GrudgeBase` + `GrudgePer` x (per cent of his health taken so far) seconds, `GrudgeMax` at most; stop and he stops. From `GrudgeForGood` per cent: for the rest of the round | 2 s, 0.15 s / %, 20 s, 60 % |
| SNAPS | your enemy for good at your first or second hit (drawn); `GrudgeSnapHits=<n>` fixes the number | proposal 2: one stray bullet is forgiven by everybody |
| TAKES IT | never - not at the game's own limit either | - |

Under the proposal of 1.4 a body hit takes 17 / 13 / 7 / 4 % of his health at 5 / 15 / 30 / 50 m: an ESCALATES bot
answers the first close hit for 4.6 s and is lost for good at the fourth; at 50 m at the fourteenth.
A tally is forgotten `GrudgeForget` s (45) after your last hit on that bot. Logged with `Log=2` only (the owner is
not to read the tempers off the log); Log=1 says how many drew.

4.3 **Killing a bot that fights you by Grudge makes YOU the traitor** (2.4: he has no traitor flag and holds no card)
- flag 1, `[player+0x2726]`, and all seven are your enemies. For a bot that only ANSWERS for some seconds that is
left as the game's rule: he was a crew member you shot first. For a bot that turned on you FOR GOOD (a SNAPS bot,
an ESCALATES bot past `GrudgeForGood`) it would mean one or two bullets can leave you with a man who hunts you all
round and whom you may not kill. **`GrudgeMark=1`** (default 0): from the pass such a bot turns, to the round's end,
he carries the score table's traitor bit - exactly what `BackstabMark` writes, with the same payout effect (3.4) and
the same unknowns. With the bit the game counts no more hits on him (2.2) - none are needed. Without the key the
hook says at start-up, at any Log level, what killing such a bot costs. **Not for the owner's ini before L5 and L9.**

**Hand-over.** When you are the traitor (`[player+0x2726]` / flag 1), police (`[player+0x2723]`) or out of play:
each bot's own tally is written back into its float once, and the hook writes nothing while that lasts - the game's
rules stand (every bot is then your enemy by 2.1 anyway). Boarding: a bot held as your enemy keeps its tactic list -
ASSUMED it still boards (LOG: bots with mask 2 went aboard and escaped, records 2 and 5 at 12:36).

4.4 **An escort you shoot** (the owner runs `Escort=1`; klescort.c is another track's file, NOT edited). klescort.c
orders its escort back to 3 m beside you every 500 ms; a turned escort would shoot you from there. Two halves:

- IN klgrudge.c NOW (`kly_escort_free`): a bot that klescort.c HOLDS (its slot in mode 1, read only) is **not turned
  at all** unless klescort.c has asked `kly_angry()` about it within the last 3 s. Its tally runs on; it turns when
  the escort is released (at the vehicle) if that is still due. So `Grudge=1` beside `Escort=1` is safe as wired by
  the three lines of section 5 alone - the escort simply never answers while it escorts. A start-up line says so.
- FOR THE LEAD, with the wiring (two lines; the diff is `G:\kl_scratch\O2\klescort_angry.patch`, compiled in
  `G:\kl_scratch\O2\test_esc` / `ship_esc`):

      /* klescort.c, above 'static int kle_later;' */
      static int kly_angry(int rec);            /* klgrudge.c */
      /* in kle_bot, after the 'it is a traitor' line */
      if (kly_angry(i)) { strcpy(why, "it has turned on you (klgrudge.c)"); return 0; }

  Then klescort.c asks every pass, klgrudge.c sees the question and DOES turn the escort, and klescort.c drops it
  one pass later ('escort: record N dropped: it has turned on you (klgrudge.c)') and may refill the slot. BoardAll
  and FollowOut use the same `kle_bot` and leave such a bot alone too, as they leave a traitor.

4.5 **State machine, reviewed against B1-B5 of `re/hook_review_1010.md`** (HARNESS, section 5): acts only where
`klb_level()` says the level is not stock, asked every pass; a new round = a new rules object or the state BECOMING
0x19 - NOT klbot.c's third sign (a heist stage going down: a guess there; a record released in mid-round would have
wiped every temper) - and puts every write back through kept, re-checked pointers BEFORE the round's memory is
dropped (no double scaling of health), zeroes held floats, draws anew; a record whose actor changed: the old one's
writes go back, the slot starts empty; a fed / traitor / dead human: 4.3; aboard / dead / escaped bots are not
written; nothing off the game's thread; record indices of 12 or more never written; no limit readable = nothing
written and held floats go to 0. NOT read: whether the game clears A at a round start (the hook does not rely on
it); if a round ever restarts with neither sign, the tempers carry over (the health is still right).

## 5. Wiring, builds, harnesses

    #include "klgrudge.c"            after  #include "klbalance.c"
    kly_tick(game_thread);           in klh_tick, after  klr_tick(game_thread);
    kly_init();                      in the init list, after  klr_init();

plus the two klescort.c lines of 4.4 if the escort is to be let go (optional: without them it is not turned).
Prefix `kly_` (`klg_` is klgun.c's). klgrudge.c reads `kle_r` / `KLE_MAX` of klescort.c and klbot.c's `klb_*`.

Compile (`git archive HEAD klhook` + klbot.c, klbalance.c, klgrudge.c + the three lines, `G:\kl_scratch\O2\src`;
the only warning is klhud.c's existing C4101):

| build | sha1 |
|---|---|
| TEST `G:\kl_scratch\O2\test` | b2f9940e935fa8c82835afe25e28b23ef6530d45 |
| SHIP `G:\kl_scratch\O2\ship` | 8cc9e532f186538b397fa12406b1e60d1b7c31ec |
| TEST + the klescort.c lines `G:\kl_scratch\O2\test_esc` | ad75d011ba6c30c064a5bdcf796f694f5acf7cf4 |
| SHIP + the klescort.c lines `G:\kl_scratch\O2\ship_esc` | 623310bc9aff1b893def143c965cfe6b9ea4590c |
| TEST + those lines + the `fireat` patch `G:\kl_scratch\O2\test_esc_fireat` | 564827553d5787eba5e694d7cb85d2f06ae44181 |

Harnesses (`G:\kl_scratch\O2\t`; each includes the source file as it is, the game's objects are made up):

| file | covers | last lines |
|---|---|---|
| `kly_test.c` (klgrudge.c) | health, ESCALATES hit / calm / for good, SNAPS + GrudgeSnapHits, TAKES IT, GrudgeForget, GrudgeMark, BackstabMark, an escort held / asked about / released, a shared accuracy block, the hand-over (traitor, dead human), a stage going down and a record released in mid-round, the state leaving and re-entering 0x19, an unreadable limit, a human that is not record 0, another actor in a record, a stock level, the session's end | '56 checks, 0 failed, 131 log lines, 133 writes' / 'PASS' |
| `klr_test.c` (klbalance.c) | YouToCrewFar: the arming pass, the three target rules, the hold, a moving target, the forgiving, a dead target, traitor / police / not record 0 / no round = flat, stock rows back bit for bit, key off, a bad key | '20 checks, 0 failed, 29 log lines, 358 writes' / 'PASS' |
| `klb_test.c` (klbot.c) | the moment of the turn (waits, turns behind you, BackstabWait as a limit after a lapse), TraitorsMax (reached, a dead traitor counts, back), the health log's 'maximum changed' line | '13 checks, 0 failed, 111 log lines, 46 writes' / 'PASS' |

## 6. The owner's lines (proposal; nothing of it before its live check)

    [Balance]   YouToCrew=0.6   YouToCrewFar=0.5   YouToCrewNearAt=8   YouToCrewFarAt=35
                FedToCrew=1.0   CrewToYou=1.25
    [Bots]      TraitorsMax=2   BackstabHealth=1.5   BackstabAim=85
                BackstabNear=1200   BackstabBehind=1   BackstabWait=30
                Grudge=1   GrudgeMix=40,30,30   GrudgeSnapHits=2   GrudgeMark=1

The `[Balance]` keys, `TraitorsMax` and `BackstabNear..` need no wiring (klbalance.c, klbot.c); the rest needs
klgrudge.c wired. In steps: (a) after L1 / L1b: the `[Balance]` lines; (b) after L3 / L4 / L6: TraitorsMax and the
Backstab keys; (c) after L5 / L7 / L8 / L9 / L11: Grudge. Samples: the block at the end of `[Net]` in
`klhook/KLHook.ini` (they do nothing where they stand: copy them into their sections).

## 7. Live checks (the lead; TEST hook, a map that is not stock, `[Bots] Enable=1 Log=2`, `[Balance] Log=2`)

| | keys | do | PASS lines |
|---|---|---|---|
| L0 | none of the new keys | any round | no 'grudge:' line, no 'balance: far:' / 'YouToCrewFar' line; klbot / klbalance lines as before |
| L1 | `YouToCrew=0.6` | `fireat` a bot at about 5 m (below) | 'balance: Risk=2 written ... you->crew 0.60'; 'bots: record N (bot): lost 43.2' steps (72 x 0.6; today 72) |
| L1b | L1 + `YouToCrewFar=0.5` | stand still at GO; then `fireat` a bot at about 5 m; then one at 30 m or more | start: 'balance: YouToCrewFar=0.50: ...'; before a hit 'balance: far: ... priced for record N at D m (... the farthest heister in play): you->crew x F'; after the first near hit '... (your last hit was on him): you->crew x 1.00' and 'lost 43.2' steps from the SECOND bullet on (the first may be 'lost 21.6'); on the far one 'x 0.60'-ish and 'lost 18.7'-size steps; 4 s after the last hit the 'farthest' line again; menu: 'the stock damage table is back' |
| L2 | `CrewHealth=1.5` | TWO idle rounds | 'grudge: record N (bot): health 252.0 of 252.0 -> 378.0 of 378.0' once per bot; 'bots: record N (bot): its maximum health changed 252.0 -> 378.0 ...: not counted as a loss' and NO 'ONE STEP' from it. ROUND 2, after the respawn: the same grudge line again FROM 252 ('378.0 of 378.0' after it, not '252.0 of 378.0' - whether the game refills health from the object's maximum at a round start was not read: if the line reads otherwise, say so) |
| L3 | `Backstab=100 BackstabDelay=5 BackstabMoney=0 BackstabStage=1 BackstabHealth=1.5 BackstabAim=85` | walk into the bank | 'bots: BACKSTAB: bot N', then 'grudge: record N (TRAITOR): health ... -> ... (x 1.50, ... he has turned)' and 'accuracy 50 % -> 85 %' (or 'its accuracy block ... is also record K's ...: NOT written' - then the crew squads share a block and the key is useless on that map); next round 'accuracy 85 % -> 50 % (his own back)' |
| L4 | L3 + `BackstabNear=1200 BackstabBehind=1 BackstabWait=30` | walk away from the crew, then stand | BACKSTAB line ends '; it is X m from you (BackstabNear 12 m), behind you'; standing 30 s with them in front: '... - BackstabWait is over, it turns anyway' |
| L5 | L3, `BackstabMark=0` | `fireat` the traitor until dead | THE QUESTION OF 2.4: does 'grudge: you: crew flags ... YOU ARE THE TRAITOR' follow his death? Then repeat with `BackstabMark=1`: 'bit 1 of its score dword set ... (BackstabMark)' and no such line. Also read the score page: a marked traitor that ESCAPED keeps his own money (3.4) |
| L6 | `Tune=1 TraitorsMax=1` | idle round to the vehicle | after the first 'traitor flag SET': 'bots: TraitorsMax=1 is reached ...', no second SET that round |
| L7 | `Grudge=1 GrudgeMix=100,0,0`, Escort=0 | `fireat 3 400`, wait 15 s, `fireat 3 3000` | 'grudge: record 3: ESCALATES'; 'your hit took P % ... enemy for some seconds'; 'you lost ..' from him (balance Log=2); 'is your friend again'; then '... for the rest of the round'; 'grudge: you: ... YELLOW CARD' at 25 % is the game's; he still boards |
| L8 | `GrudgeMix=0,100,0 GrudgeSnapHits=2` / `0,0,100` | `fireat 3 600` | SNAPS: 'record 3: SNAPS (at hit 2 of yours)', hit 1 'it stays your friend', hit 2 'enemy for the rest of the round'. TAKES IT: 'it stays your friend' at every hit |
| L9 | L8 SNAPS, `GrudgeMark=0`, kill the bot; then the same with `GrudgeMark=1` | | =0: start-up line 'GrudgeMark=0: KILLING a bot ...', then 'YOU ARE THE TRAITOR', 'grudge: you are the traitor ...: the hand-over', no grudge write after. =1: 'record 3 (your enemy for good): bit 1 of its score dword set ... (GrudgeMark)' and NO traitor line at his death |
| L10 | `[Fed] Player=1`, `YouToCrew=0.6 YouToCrewFar=0.5 FedToCrew=1.0`, die | shoot a heister as the fed | 'balance: FedToCrew=1.00 ...' at start; 'you are POLICE now ... yours a heister x 1.00'; 'lost 72'-size steps at 5 m; no 'balance: far:' line while police |
| L11 | `Grudge=1 GrudgeMix=0,100,0 GrudgeSnapHits=1 Escort=1` | `fireat` the escort's record | WITHOUT the klescort.c lines (TEST `O2\test`): start-up 'grudge: [Bots] Escort is on: ...'; 'grudge: record N (SNAPS): it is your escort and klescort.c does not ask ...: NOT turned'; he does not shoot you; at the vehicle ('escort: record N released') 'turns on you'. WITH them (`O2\test_esc`): 'for the rest of the round', then 'escort: record N dropped: it has turned on you (klgrudge.c)' within a second |

**What the rig lacks to shoot a crew member**: `face` takes a fixed point and `mdown 0` holds fire, but nothing
follows a moving bot. Patch for `klhook/klauto.c` (NOT applied; it applies to HEAD's klauto.c and compiles:
`G:\kl_scratch\O2\test_esc_fireat`; whole diff `G:\kl_scratch\O2\klauto_fireat.patch`). Yaw only - the rig reads no
pitch: stand level with him, a few metres away (so L1b's far leg needs a level stretch of 30 m - the bank's yard
or the park; otherwise the owner's own round with `[Balance] Log=2` shows the 'far:' lines).

1. the enum: `..., C_WAITSTATE, C_WAITVAN, C_FIREAT };`
2. the parser, before the `"label"` line:

        else if (!_stricmp(op, "fireat")) {             /* fireat <crew record> [ms 1500] [degrees 4] */
            c->op = C_FIREAT; c->n2 = strtoul(a, 0, 10); c->n = 1500; c->f[2] = 4.0f; sscanf(rest + strlen(a), "%lu %f", &c->n, &c->f[2]);
        }

3. the switch, after `case C_POS:`:

        case C_FIREAT: {
            static DWORD fire_ms, fire_last; struct klb_snap s; int me = kla_local_player(), ok, aim; float v[3], h = 0, bp[3], dx, dz, err = 0, rate;
            if (!fire_last) fire_ms = 0;
            ok = now - kla_cmd_t < c->n && klb_read(&s) && c->n2 < (DWORD)s.n && s.r[c->n2].used && (s.r[c->n2].flags & 1) && s.r[c->n2].status == 0 && s.r[c->n2].actor &&
                 kle_node(klh_rd32(s.r[c->n2].actor + 4), bp, 0) && me >= 0 && kla_player_pos(me, v) && kla_player_dir(me, &h);
            if (!ok) {
                kla_m_rate[0] = kla_m_rate[1] = 0; kla_m_btn[0] = 0;
                kla_out(1, "script %d: fireat record %lu over after %lu ms: fire was held for %lu ms%s", kla_pc + 1, c->n2, now - kla_cmd_t, fire_ms, now - kla_cmd_t < c->n ? " - the record is no AI heister in play, or you / he could not be placed" : "");
                fire_last = 0; next = 1; break;
            }
            dx = bp[0] - v[0]; dz = bp[2] - v[2];
            err = (float)(atan2(dx, dz) * 57.29577951) - h; while (err > 180) err -= 360; while (err < -180) err += 360;
            rate = err / kla_turn_deg * 5.0f; if (rate > 1800) rate = 1800; if (rate < -1800) rate = -1800;
            kla_m_rate[0] = rate; kla_m_rate[1] = 0;
            aim = err < c->f[2] && err > -c->f[2];
            if (aim && kla_m_btn[0] && fire_last) fire_ms += now - fire_last;
            if (aim != (kla_m_btn[0] != 0)) { kla_m_btn[0] = (BYTE)(aim ? 0x80 : 0); kla_out(1, "script %d: fireat record %lu: fire %s (he is %.1f m away, bearing error %.0f)", kla_pc + 1, c->n2, aim ? "DOWN" : "up", (float)sqrt(dx * dx + dz * dz) / 100, err); }
            fire_last = KLB_T(now);
            return; }

## 8. Assumed / not read / not done

- ASSUMED: a bot held as your enemy through the float behaves as one with the traitor mask (the two are OR-ed at
  0x882715 / 0x88271d and in 0x570a1b) and still loots / boards; the target test is asked often enough that a 2-20 s
  window shows; nothing derives anything from an NPC's maximum health that a larger one breaks; the fire button is
  mouse button 0 and hip fire hits at a few metres; 0x7aca80 answers 0 in Arcade, so the 'friendly fire off' drop at
  0x4db5ab does not take a turned heister's bullets on you; the player's bullet is priced within the pass its hit is
  counted in (YouToCrewFar's 'one bullet late'); the heister's aim number (2.5 .. 0.3) is an error that grows with
  distance (1.2).
- NOT READ: how an Ally soldier engages an enemy (range, burst, flight) and how his hit rate falls with distance;
  whether traitor bots fight loyal ones or loyal bots a marked one; who else reads the score table's bit 1 besides
  the three places named (2.2, 2.4, 3.4); the tally's gate bits 8 / 0x80 / 0x800 / 0x1000 (2.2); indirect calls of
  rules slot 141; whether a round start clears A or refills a bot's health from the object's maximum (L2 round 2).
- NOT DONE: a true per-hit distance factor (1.3: not possible inside the rules); 'turn while you reload / loot'
  (those player states were not found - 'you are hurt' is the one busy test); BackstabBehind by where you LOOK (the
  camera's direction is not known to the hook); the klescort.c lines (another track's file: 4.4 has them, and
  klgrudge.c is safe without them); `fireat` not applied; no pitch in the rig.

## 9. The review's points (`re/bots_fight_review.md`)

| point | what was done |
|---|---|
| M1 the sponge by range | DONE: the table (1.1), what differs by range and what was not read (1.2), the plain statement that a per-hit factor cannot be had (1.3), `YouToCrewFar / NearAt / FarAt / Hold` as an approximation by data with its faults named (1.4, klbalance.c 2 a6, `klr_test.c`), values from the table (0.6 / 0.5 / 8 m / 35 m) |
| M2 Grudge beside Escort=1 | DONE inside klgrudge.c: an escort klescort.c holds is not turned unless klescort.c asks `kly_angry` (4.4, harness scenario D, L11); the two klescort.c lines are given, compiled (`test_esc`), not applied (not this track's file) |
| M3 killing a Grudge bot makes you the traitor | DONE both ways: `GrudgeMark` (off by default) for bots that turned FOR GOOD; a start-up line that says what killing costs without it; `GrudgeSnapHits` so that one stray bullet need not snap anybody; the owner's order (6 c) puts Grudge after L5 / L9. A bot that only answers for seconds is deliberately NOT marked (4.3) |
| S1 a stage going down taken as a new round | DONE: only a new rules object or the state becoming 0x19 resets (4.5; harness: 'a stage going down / a record released is no new round') |
| S2 the second caller 0x570a1b | DONE in the note (2.1) and klgrudge.c's comment; indirect calls of slot 141 named as NOT SEARCHED |
| S3 BackstabMark changes the payout | DONE: 3.4, the ini text, the mark's log line, L5 |
| S4 the tally's own gates | DONE as far as the code goes: the four gates are listed (2.2); what the bits mean is NOT READ and said so |
| S5 the false 'ONE STEP' line | DONE in klbot.c: a step in which the maximum changed is said as that and not counted (3.5, `klb_test.c`, L2) |
| S6 attacker 0 assumed | DONE: Grudge and YouToCrewFar act only while the human is crew record 0 (harness in both) |
| S7 klbot.c details | DONE: TraitorsMax is said to be per round (comment, ini, start-up line); BackstabWait now runs from the FIRST end of the delay and is not started again (`klb_test.c`: 30.8 s with a lapse); BackstabBehind marked a guess in comment, ini and start-up line |
| S8 BackstabAim writes the rout's block | DONE: said whose memory it is; a block two crew records share is not written, one line (harness scenario E, L3) |
| S9 the harness is thin | DONE: 25 -> 56 checks for klgrudge.c (SNAPS, TAKES IT, GrudgeForget, a dead human, leaving 0x19, an unreadable limit; the restart check now has one outcome), plus `klr_test.c` (20) and `klb_test.c` (13) for the other two files |
| S10 small | DONE: the '-1.0 at 0xb87940' is gone (2.2); L2 reads round 2 after the respawn; the ini block says it stands under [Net]. CrewHealth stays a `[Bots]` key (reported; the review: fine) |
| refuted | none |
