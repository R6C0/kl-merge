# AI heisters go 'down, not dead' (track Y2b, 2026-10-12)

Owner: *'so the ai heisters are 1:1 with you'* (the human's knock-down: kldown.c; the helper: kladren.c). **Offline. Nothing here
has run in the game.** READ = kl2.exe 0490 (`debug/dasm.py`). Files: `klhook/klbotdown.c` (the part, `[BotDown]`, NOT wired),
`klhook/klbotdown_test.c` (off-game harness, ALL PASS, 0 failures).

## 1. The short answer

It can be made to work **without a private vtable and without a code patch**, by asking the game's own down from the hook at a
health threshold instead of waiting for health 0. What is proven: the call and its arguments, which tests it still has, and the
data around it (all read). What is NOT proven: that test b (below) passes for a bot standing in his usual places - live check B1
decides, and the part says why in its log if it does not.

## 2. What was read

| what | where | facts |
|---|---|---|
| the damage | ZSoldier slot 96 = 0x8473a0 | new health = `ftol(health - damage)` (0x847793, clamped at 0 0x8477a1), written through actor slot 0x670 = 0x792bc0 -> **0x61efd0**, which clamps to [0, `[h+8]`] (0x6143f0) and calls 0x8ab200 (the health fraction); the death path is reached only at health 0 (0x847937) |
| the 'no damage' word | `[[actor+0x54]+0x3a]` | nonzero: no health write (0x8477ae) AND no death (0x847945). Bit 0x800 is the down's own (0x6c75c0 ORs it in with a time) |
| the ask | 0x847958..0x847968 | `[soldier vtbl+0xcc](hit, 0)` = **0x688190** (a dog, `[[soldier+0x6d8]]` = 6, says no) -> a plain `jmp` to **0x70e0e0** (thiscall, ecx = soldier, args hit record, force flag, `ret 8`) |
| 0x70e0e0 | read whole | **a** `[actor+0x64c]` set (slot 405 = 0x410a30) or ZWounded `[[soldier+0x4b4]+8]` not 0 / 4 -> NO. **b** 0x70f330 on `[soldier+0x4b8]` (the ZDownNotDeadNPC, `dnd`) -> NO if it fails. Then `cmp byte [ebp+0xc],0 / jne 0x70e1e5` (0x70e12d): **a nonzero second argument jumps over c (was down once), d (head hit within 15 m), e (damage over 1,000)**; at 0x70e1e8 the modifier `[soldier+0x124]`: 2 = NO, else at 0x70e1fc `cmp byte [ebp+0xc],0 / jne 0x70e29e` the flag again **skips f / g** (0x70e29e = the start). A missing hit record is a stock case (0x70e29e: `test edi,edi / je` -> attacker 0) |
| the start | 0x70e29e..0x70e2fd | 0x4860e0 (`[dnd+0x18]` = attacker, **a plain store**), 0x6cabf0 (the goal 0x30dac registered with the soldier), vtable slot 0x50(1), `[actor+0x64c]` = 1, 0x6c75c0 (`or [ecx+0x3a], 0x800` for [0xb4c788] s), returns 1 |
| the goal's start | slot 1 = 0x7ea990 | a frame or more later: `[dnd+0x14]` = now + 1.5 .. 3.0 s (random), the level's 'last NPC down' tick `[gamedata+0x4d04]`, health raised to 25 % of the maximum if lower |
| the goal's script | 0x5f4ac0 | **its first line is 0x70f330 again: if b fails at that moment the script returns and nothing ever clears `[actor+0x64c]`** (no write of 0 in the script; the goal's end does it). While he lies: fires at the target `[soldier+0xb0]` (reads it each loop, branches on 0), takes hits in full; at the end health = 75 % of the maximum (0x5f4d23), 0x800 again for `[T+0x48]` s if the buddy, `[soldier+0x4fc]` = 1 in Arcade for Ally / Mercenary |

b (0x70f330, read whole): 0x619d10 (node flag 0x1000 and bone 2 near), `[actor+0x774]` (held), 0x75a2e0 (seated), 0x4a05f0
(ZHitAnimTask `[soldier+0xa4]` state not 0 / 4), 0x86a150 + 0x86f0c0 (attached to a ZHavokLnkObj), then **16 probes of 100 units
around his position on the navigation mesh (PF4 slot 41)**: all must pass. Those are properties of his SITUATION at the moment
of the call, not of the hit - which is exactly why the call is moved out of the damage routine.

**Why this is better than waiting for 0:** at 0 the game asks with the killing hit (its animation has just been started -> b's
ZHitAnimTask; its head flag -> d; its damage -> e; the level-wide 5 / 20 s pause -> g). The hook asks with force 1 (c, d, e, f,
g are skipped by the routine's own flag) and again every 100 ms for 3 s, so it is asked again when the hit animation is over.

## 3. The design (`klbotdown.c`, once a frame on the game thread, Arcade, a level that is not stock, state 0x19)

The hook's tick runs once per frame (klhook.c: SteamAPI_RunCallbacks in the main loop), so a bot is seen between two hits
(a stock crew bot loses 1 .. 21 health per hit, about 3 hits a second).

1. **Trigger**: an AI crew record (flag 1 of `+0x79`, a ZFFActor with a ZSoldier of vtable 0xbd0954; traitors too, `Traitors=1`),
   status 0, health `[[actor+0x5fc]+4]` <= `DownPct` (20 %) of the maximum `[+8]`, above 0, down byte clear, fewer than `DownsMax` (2)
   downs this life, vehicle state under 5.
2. **Action**: `soldier->vtbl[0xcc](NULL, 1)` (= 0x688190 -> 0x70e0e0), checked first: the vtable slot must hold 0x688190 and both
   routines' first 16 bytes must match this build, else nothing is called. Repeated every 100 ms.
3. **Refused**: health held at `FloorPct` (6 %) at least (the next bullet cannot take the last of it); the reason is logged from
   what can be read (hit animation, holder, seat, attachment; the 16 probes are not readable: "against a wall / in a corridor").
   After `RefuseMs` (3 s) the part gives up for this episode: he dies like a stock heister. Healthy again (> threshold) = new episode.
4. **Lying** (the game's own goal): `LieSeconds` (6; a GUESS; the game's is 1.5 .. 3.0) is written ONCE, after slot 1 has written its
   own (seen as a changed `[dnd+0x14]`, or after 1 s), and not when a helper has already pulled it under 1.4 s. `FreeSeconds`
   (0.75) holds bit 0x800 (never at vehicle state 5, never on a record out of play). `LiePct` (0 = the game's 25 %) sets his health
   on the floor, `UpPct` (0 = the game's 75 %) when he is up, `NoFire=1` clears `[soldier+0xb0]` each pass (ASSUMED: the script
   branches on 0). **Police can finish him**: the game takes hits in full while he lies (a second health 0 is refusal a = death).
   Their damage on a lying man is the health he has - `LiePct` is the knob (R8's per-side factors need the hit record: not here).
5. **Up**: the game's script. **Watchdog**: if the byte still stands `lie + WatchSeconds` (8 s) after the down - the goal's script
   exited at its first line - the byte is cleared (data), he is a plain heister, and DownsMax bounds a repeat.
6. **Attribution** (for the traitor-by-downing rule): the rules' hit matrix `[rules+0x884+4*victim]` (klgrudge.c: the share of his
   health the LOCAL human's bullets took, per cent) is already in every `klb_rec.hit`; a rise within `AttrMs` (1.5 s) before the
   down = the human put him down. This replaces kladren.c's `[score+0x1b8]` word, which only rises at health 0 and so never sees a
   threshold down. The rise starts at 25 % hit sums too (the yellow card, klgrudge 1 b) - game rules, unchanged.

Exports: `klbd_is_down(record)`, `klbd_speed(record, rate)` (pulls `[dnd+0x14]` earlier with kladren's arithmetic and latches the
part's own write off), `klbd_by(record)` (the human record or -1).

## 4. Keys (`[BotDown]`; sample block for the lead)

    [BotDown]
    Enable=0          ; 1 = the part
    Dry=0             ; 1 = log only: nothing is called, nothing is written
    Log=1             ; 2 = every try, health lifts, target clears
    DownPct=20        ; ask the down at this per cent of the maximum or less
    FloorPct=6        ; health held at least this high while the game refuses
    DownsMax=2        ; downs a life
    RefuseMs=3000     ; give up after this long refused
    LieSeconds=6      ; GUESS; 0 = the game's 1.5 .. 3.0
    FreeSeconds=0.75  ; no damage at all for this long from the down's start
    LiePct=0          ; health on the floor in per cent of the maximum, 0 = the game's 25
    UpPct=0           ; health when up, 0 = the game's 75
    NoFire=0          ; 1 = no firing from the floor (ASSUMED safe - live check B3)
    Traitors=1
    AttrMs=1500
    WatchSeconds=8

Do not run it together with `[Down] Bots=1` (the same bytes, a second asker); with `[Down] Bots=0` kldown.c's bot part is silent.

## 5. Wiring (the lead; three lines in klhook.c)

    #include "klbotdown.c"        BEFORE  #include "kladren.c"   (it uses klb_*, klr_arcade, kle_node, klb_same_code)
    klbd_init();                  BEFORE  kad_init();
    klbd_tick(game_thread);       BEFORE  kad_tick(game_thread);

Compile proof (`git archive HEAD klhook` at 094fc40 + klbotdown.c + those lines, `G:\kl_scratch\botdown\src`): no warning or error;
TEST `G:\kl_scratch\botdown\test\dinput8.dll` sha1 1E63874A9B17AAF524710796028E4F3A60EE5896, SHIP
`G:\kl_scratch\botdown\ship\dinput8.dll` sha1 CDD1D4C91A783E704DEADB0CECF00186EF26D350 (klbotdown.c sha1 9804029AB72594F675B4188743F3FDCEEA145E57).
Harness: `klbotdown_test.exe` ALL PASS, 0 failures (the call: soldier, no hit, force 1; once per 100 ms; floor; give-up; DownsMax;
Dry = 0 calls 0 writes; shield on / off, off at vehicle state 5; lie tick; helper yields; watchdog; attribution; LiePct / UpPct /
NoFire; code-mismatch = no call).

## 6. Hand-over lines for other files (NOT applied; exact text)

**kladren.c**, in the "he goes down" block after the `for (h...)` attribution loop:

    if (by < 0 && klbd_by(i) >= 0) by = klbd_by(i);          /* klbotdown.c: the threshold down never raises the score word */

kladren's own lie pull (`else if (dnd[i]) {... kad_lie_step ...}`) may stay: klbotdown does not put back a lie under 1.4 s. Or
replace that branch by `else if (klbd_speed(i, kad.rate)) k->sped += 1;`.

**klescort.c** (after the `b576` line of `kle_bot`, as re/player_down.md 11.3): no order to a lying bot:

    { BYTE dn = 0; if (klh_rd(actor + 0x64c, &dn, 1) && dn) { strcpy(why, "it is down, not dead ([actor+0x64c] set): no order until it is up"); kle_later = 1; return 0; } }

**klbot.c** (log only): its `lost .. - DOWN` mark fires at health <= 0; with this part a down shows as `lost` to the threshold and
then the game's 25 % as a RISE (not logged). Nothing to change.

## 7. Live checks (the lead; bank DM03, owner's balance, `[Bots] Log=2`, scripted human, hook built with the three lines)

| run | keys | PASS (log) | FAIL |
|---|---|---|---|
| B0 dry | `[BotDown] Enable=1 Dry=1 Log=2` | `botdown: on (Dry=1 ...`, `botdown: a round runs ...`, per bot `record N (actor ..): health 252.0 of 252.0; a down is asked at 50.4 or less, held at 15.1`, and `Dry - record N is at x of 252.0 (<= 50.4): the hook WOULD ask ...` before each `bots: record N (bot): lost` line that ends a bot; zero `klh_data` lines | no `Dry -` line before deaths (the bots die from above 50 in one frame: then the kills are one-step ones - say how many; `[Balance] PointBlankToCrew`) |
| B1 the ask | `Enable=1 Dry=0 Log=2` (all else default) | `record N is at x of 252.0 (<= 50.4 = DownPct 20 %): the game's down is asked`, then **`record N IS DOWN, NOT DEAD (1 of 2) ... the HOOK asked and the game said YES`**, `he lies until tick ... (LieSeconds=6.0; the game had ... = 1.5 .. 3.0 s)`, 0.75 s later nothing kills him, **`record N IS UP after 6.xx s`**, health about 189.0 of 252.0, then his klbot lines go on (`heist stage ..`, `aboard`). A picture of a bot on the floor | `the game said NO at try 1 ... <reason>` for most bots = test b: the reason line names which readable one; if it says 'mesh probes' the lead needs the place (printed in the IS DOWN lines of the ones that worked vs. `bots: lost` places); a fault right after the call (then Dry and report the address); `the down byte stood ...` (the goal never ran: how often?) |
| B2 budget | B1 | second `(2 of 2)`; a third health <= 50 does NOT ask; he dies at the next hits | a third ask |
| B3 NoFire | B1 + `NoFire=1` | `his target [soldier+0xb0] ... cleared (NoFire)` while he lies and NO `you lost` from that bot in that time; no fault | a fault (then NoFire stays 0) |
| B4 police finish | B1 + `[BotDown] LiePct=50` / default | a bot shot while lying: `record N left play while down (he DIED)` or death at health 0 after the down; the time on the floor | he cannot be killed on the floor (the 0x800 bit stuck: FreeSeconds) |
| B5 vehicle | B1 with the scripted human to the van | no `IS DOWN` ask after `the vehicle drives out`; `the 'no damage' bit is taken off`; the left-behind are killed as in PB_DM03 | a bot alive after the van left |
| B6 adrenaline | B1 + `[Adrenaline] Enable=1 Log=2` with the 2 hand-over lines | kladren: `record N (bot) IS DOWN ... put down by a human's bullet`, `is helped by record 0 (you)`, `IS UP` earlier than 6 s; the share lines | no kladren line (it reads `[actor+0x64c]` itself: should work) |
| B7 Retomoto | B1 on DM09 (gates) | every bot with an `IS UP` still passes the gates (re/player_down.md 11.1 `[soldier+0x4fc]` note) | a bot left behind a gate |

## 8. ASSUMED / not done

- ASSUMED: calling 0x70e0e0 from the frame tick with ecx = soldier, no record, force 1 has no hidden dependency on being inside the damage
  routine (its callees 0x4860e0, 0x6cabf0, slot 0x50 and 0x6c75c0 were read only as far as above); a goal pushed from outside the
  goal manager's own update is accepted; test b usually passes for a bot in the open; `[dnd+0x14]` has no reader but the script's compares
  (re/player_down.md 11.6); `[soldier+0xb0]` = 0 stops the script's firing (it branches on it); the rules' hit sum rises per bullet.
- KNOWN LIMITS: a single hit over the threshold's room (point-blank step 432 at CopToCrew 0.05, a left-behind kill) still kills;
  the dive clip is the game's own Down_Not_Dead_Get_Down (onto the side), not the belly flop; the attacker of the down is 0 in the
  game's books (`[dnd+0x18]`); no per-side damage factor on a lying man; LiePct is a health, not a factor; the 16 probes cannot be
  read, only their consequence.
- REJECTED, with the reason: **a health reserve** (raise `[h+4]`/`[h+8]` by a constant so nothing reaches 0): klgrudge.c / klbalance.c
  rewrite the maximum keeping the share, klbot.c refuses a maximum over 100,000, and the game's own 25 % / 75 % are shares of the
  maximum - the reserve would have to be stripped before every down. **A wrapped damage routine** (ZSoldier slot 96 on a private
  vtable copy): six parts identify a soldier by `[soldier] == 0xbd0954`. **'cannot die' flags**: the only one found is the 'no damage'
  word (all damage, forever) and the buddy's rule (0x6fd7c0, the campaign's one actor; `[gamedata+0x4cf0]`): neither gives a floor.

## 9. First live runs (B1_DM09 Retomoto, B2_T01 stock Subway) and the mesh probes read (2026-10-12)

**What the runs showed:** on stock Subway (T01) the hook's ask is answered YES at try 1 (record 3 at 36 of 252), the game also did a
down by itself at health 0 (record 5) - so the mechanism is right; on Retomoto 1 YES (record 4) and many NOs, 78 x hit animation,
136 x "mesh probes". Bots then died at health 0 inside the pending window (the floor of 15 did not hold against one frame of
police fire at police -> crew 1.0).

**The probes, read whole** (0x70f330 -> PF4::ZData slot 41 = 0x4dd5f0, vtable 0xb9b17c): for i = 0..15 a vector of 100 units
(constant 0xb5c050) at angle 2 pi i / 16 from his place (actor slot 0x568 = 0x598710, the node's world place). The slot: (1) locates his
place - `[vtbl+0x80]` = 0x68bef0 -> 0x55e6e0 - and returns NO when he is **off the mesh**; (2) a zero vector passes; (3) `[vtbl+0xa8]`
= 0x82b950 walks the segment polygon to polygon (edge records: neighbour, vertex; a vertex is 5 floats = x, z, height, 2-D normal),
returning the fraction reached; **below 1.0 (0xb58418) = NO**; (4) locates the end point (slot 0x80 again), off the mesh = NO.
So a probe fails when a mesh EDGE WITHOUT A NEIGHBOUR (the rim of the mesh: a wall, a cover box, a hole) lies within 1 m of his place
in that direction. Mesh coordinates are (x, z, height); a bot's (X, Y, Z) of the logs is (X, Z) at height Y.

**Offline reproduction** (`tools/kl_pf4_probe.py`, a 2-D model; the game's height tolerance for the locate is not read, 250 is used):
- the model predicts the live answers: B2_T01 - the two asks that were answered YES stand where 0 of 16 probes fail; the two NOs with a
  place stand where 5 and 6 fail; B1_DM09 - the YES (record 4) 0 of 16, the NOs 3, 10, 7, 8, 8; one place is off the mesh by the model.
  So the model is good enough to LAY A PLACE ON THE MESH offline.
- **It is not a conversion fault.** Share of polygon centres that pass all 16 probes, by polygon / by area: stock F01 38 / 86 %, F02 56 / 93,
  F03 49 / 95, F04 30 / 73, F05 41 / 83, F06 38 / 87, F07 39 / 84, F08 35 / 85, F09 45 / 85 - and the converted Dead Men meshes (r_tab)
  DM01 47 / 97, DM02 47 / 94, DM03 40 / 91, DM06 48 / 91, DM09(x) 44 / 93. Same range. kl_pf4.py needs no change; nothing to rebuild.
- **Why the bots fail anyway:** the mesh is mostly open (90 % of the AREA passes) but the places the crew STANDS - route holds, cover boxes,
  doorways - are by design at the rim; a bot at a hold fails, a bot walking in the open passes. That fits "267 of 267 on our maps" and
  "7 of 7 on T01" (open Subway). The 267 were not all mesh: 78 refusals in B1 were the hit animation too.
- Not read: bone 2 (0x619d10) and the locate's height tolerance (0x55e6e0).

**Changes made after the runs** (klbotdown.c; harness ALL PASS):
1. `PreShield=1` (default): while the game is asked, bit 0x800 of the no-damage word is held - the same bit and the same code as
   FreeSeconds (the game ORs it in itself for 0.1 s at every down, 0x70e2f6; no hit costs health or kills while it stands, 0x8477ae /
   0x847945). It ends the pass the asking ends: on YES (FreeSeconds takes over), on giving up after `RefuseMs` (now 4000), when healthy,
   at vehicle state 5, when the record leaves play, and with the part. Safe? The hit animation still starts (so b's ZHitAnimTask still
   refuses for its length, ~a second) but the bot cannot die of it; the cost is a bot that cannot be hurt for at most RefuseMs
   (4 s) in the worst case. The floor (FloorPct) stays as a second line when PreShield=0.
2. `DownPct` 20 -> 30: asked earlier, one frame must now take 76 of 252 to kill from the threshold.
3. The refusal line now says: ZHitAnimTask state, the game's own b test (0x70f330 called on the ZDownNotDeadNPC, read-only), and a verdict
   that names "within 1 m of the edge of the navigation mesh / off it" when b says NO and nothing readable does.
4. Log fixes: the IS DOWN line printed `[dnd+0x14]` right after the call (it is written by the goal's start a frame later: 0 on T01, a
   stale tick on Retomoto) - no longer printed (the `he lies until tick` line follows); the IS UP line said "the game's script gives
   75 %": **observed 252 of 252 twice on T01** (the constant 0.75 in the script is applied to slot 0x678, which is not the maximum
   health, or something else restores it) - the text says so; `UpPct` still sets a number.

**What would make the ask succeed more often on Retomoto** (not built): ask where he WALKS - the holds are at the rim, the walks between
them are in the open; with PreShield the ask can run for 4 s while he moves on; a longer RefuseMs (8000) covers a whole leg of his route.
The alternative, moving the holds off the rim in the level data (kl_fa_bots_dyn / kl_fa_bots_rt: a hold more than 1 m from every
mesh edge, checkable with `kl_pf4_probe.py at`), makes the stock game's own down work too.

**Run next:** B1 again on Retomoto and T01 with `[BotDown] Enable=1 Log=2` (PreShield and DownPct 30 are the defaults); look for
`the game said NO at try 1 ... b test NO ... within 1 m of the edge`, the number of YES per bot that was asked, and that no
`DIED while a down was pending` follows an ask inside RefuseMs. Then B1 with `RefuseMs=8000`. Compare with `python
tools/kl_pf4_probe.py at <zip> x y z` at the printed places.
