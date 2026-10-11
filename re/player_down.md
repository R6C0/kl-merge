# The player goes down like the AI heisters, and mashes his way up (track R, 2026-10-11)

Owner: *'i want a down mechanic, as in you know how the ai heisters like flop to the floor being shot by the feds, want
the same mechanic on the actual player and they have to spam like theyre breaking out from a human shield to get up so
the animation is slow, gets faster whilst you spam the break out button ... so the ai heisters are 1:1 with you'*.

**Offline. Nothing here has run in the game.** READ = read in kl2.exe build 0490 (capstone; scratch listings in the
session's scratchpad `R/`); LOG = the owner's own `KLHook.log`; GUESS / ASSUMED are marked.

## 0. The short answer

- **The human already has the mechanic in Arcade - the game's own 'down not dead'.** LOG, the owner's rounds of
  2026-10-10 19:50 - 20:47 (klshoulder.c's lines, all five maps): ten times `dstate 0->2` (falling, 0.73 s, input masked),
  `2->1` (lying); EIGHT of them go on `1->3` (getting up, **0.80 / 0.81 s every time**), `3->0` (19:50:50 has no line after
  `2->1`; 19:52:45 goes `1->0` after 0.13 s with no state 3). From the fall to standing: 1.5 .. 2.4 s. It is so
  short because ONE press of the Cover key gets him up, at full speed - which is why it does not read as the bots' flop.
- So nothing new has to be animated. What is built: **the get-up's clip speed driven by a mash** (data: the animation
  channel's frames a second, and the two ticks the game ends the state by), and **keys for the game's own trigger**
  (data: six floats of the tuning object). `klhook/kldown.c`, `[Down] Enable=1`, off by default.
- **Not the same trigger as the AI's exactly**: an AI heister goes down at the hit that takes his LAST health, in place of
  dying; the human goes down while he still has health, under a burst. Making the human's the AI's needs the player's
  damage routine (code). `Burst=1` is the nearest the data comes (section 4).

## 1. The human: 'down not dead' (READ)

| what | where | facts |
|---|---|---|
| the state object D | `[player+0x2948]`, made by 0x57cf90, `[D]` = the player | `[D+4]` **0 up, 2 going down, 1 lying, 3 getting up**; `[D+8]` bit 0 = down; `[D+0xc]` M, the prone movement; `[D+0x10]` time of the last hit; `[D+0x20]` 'get up into a cover'; `[D+0x21]` get-up asked; `[D+0x29]` fast get-up; `[D+0x2b]` the GET UP button; `[D+0x2c]` the prompt may show; `[D+0x30]` the camera side kept; `[D+0x38]` seconds until he can go down again; `[D+0x4c]` count and `+0x50..` 20 x {time it expires, damage}: the window of counted hits; `[D+0xf0]` who floored him |
| the switch | dword `[0xceb40c]` = 1 in the image (also `[0xceb410]`, `[0xceb414]` = 1) | every routine below does nothing with it 0 |
| **the trigger** | 0x8da3b0(D, hit record), called by the player's damage routine at 0x458e7f BEFORE the health changes; true -> the hit costs nothing (0x458e84 .. 0x458e93) - except a blast: hit kind 9 goes on to the damage (0x458e8f) | state 0: `[0x1535a2c]` != 1; **0x828710** (not in a helicopter seat `[+0xd50]` / `[+0xd5c]`, not 0x5e1480, word `[[player+0x54]+0x3a]` 0, bytes `[player+0x2f3c]` `[+0x2728]` `[+0xb70]` 0, **byte `[gamedata+0x4d38]` != 0, `[gamedata+0x4d48]` bit 2**, current action not 0x2b); then 0x49aac0 books the hit in the window when its damage `[rec+0x2c]` >= `[T+0x274]`, for `[T+0x26c]` s (`[T+0x270]` when the attacker is a player); then, unless the hit is kind 9 (a blast): `[D+0x38]` must be 0 and health per cent (0x49e2c0 / 0x59ff30 = `[[player+0xa48]+4]` / `+8`) at or under `[T+0x268]`; then one of: **0x86d630** window sum >= `[T+0x278]` x `[T+0x274]`; **0x449520** window sum >= `[T+0x27c]` x `[T+0x274]` and health under `[T+0x280]` per cent; **0x7cbb30** hit kind 9, or kind 1 with no damage from within 1 m; then 0x8cf030 (room to lie: a collision probe) -> 0x76a450. State 2: hits cost nothing until 0x843fa0 (the fall has run its time). **States 1 and 3: the trigger returns 0 (0x8da4c2 .. 0x8da4d2), so lying and getting up every hit costs FULL damage.** |
| the tuning numbers T = `[0x168d7c0]` | the constructor 0x526cfe .. 0x526f48 | `+0x25c` **80** health he has at least when he goes down (Arcade / multiplayer; the campaign: 30 % of his maximum), `+0x260` **20** s / `+0x264` **10** s pause (campaign / Arcade and multiplayer), `+0x268` **40** %, `+0x26c` **1.0** s, `+0x270` 1.0 s, `+0x274` **20**, `+0x278` **6**, `+0x27c` 4, `+0x280` 20 %. So: at or under 40 % health, 120 health of hits of 20 or more within a second - or 80 under 20 %. Whether a level's tuning data changes them was not read: the hook logs what it finds. |
| other starters | 0x658700(D, attacker) (the same tests without the health rule); callers: 0x451170 (getting up from a ragdoll throw with `[player+0xa54]` bit 0x200 or 0x20), 0x489c40 (a plain 'go down or die'), 0x4ef2d0 (a list of delayed starts in the player's frame), 0x69b1f0 (`ZForcePlayerMechanics` slot 26: a LEVEL object can floor player 1 / 2 by message), 0x7835e0 (`ZFFActionReleaseHumanShieldPvPShield`), 0x8f5160, 0x4b2af0 | not used by the hook |
| going down | 0x76a450 | the kill-feed line, flag bit 0, health raised to `[T+0x25c]`, `[D+0x38]` = the pause, `[D+4]` = 2, input bits 1 and 0x10 masked (0x6feb90), the camera forced to the left shoulder, the weapon / cover / action let go |
| the frame | 0x724420 (from the player's frame 0x57fc07) -> 0x8ee220 (2 -> 1 when the fall is over), 0x50a9e0, **0x47cd80**, 0x4205b0 | 0x47cd80: while he lies (M state 2), or late in the fall, `[D+0x2c]` = 1 and the user action 0xc (`UA_DOWNNOTDEAD_GETUP`; 0xd `..GETUPINCOVER` at a cover) is tested by 0x50a8f0 -> **`[D+0x2b]`**; pressed (or `[D+0x29]`) -> 0x7180b0 sets `[D+0x21]`; next frame: `[D+4]` = 3 and 0x6373e0 -> **0x478270(M, 4, `[D+0x29]`)**, or straight into the cover (0x7107b0). A press LATE IN THE FALL sets `[D+4]` = 3 while M is still falling (0x47cde7 .. 0x47cdff; 0x6373e0 then does nothing until M is 2): state 3 can outlast the clip in stock too, and the hook's 'the get-up took' (counted from `[D+4]` = 3) then includes that wait. The state ends (0x7107b0 -> 0x88a990: everything of D cleared, the input mask off, the camera side back) when M reaches 5, or from the stick (below). |
| the button | `ZGameplayInput` slot 12, 0x808720: every frame 0x84dda0(player, byte `[input+0x2d3]`) -> `[D+0x2b]` while he is down (`[D+8]` bit 0 and `[D+0x20]` 0; `[player+0xeb4]`, the Cover byte, is then ZEROED: the presses do nothing else while he is down), else `[player+0xeb4]`; refreshed only while the input lock `[input+0x330]` is 0 and `[player+0x2720]` bit 1 is set (0x808943 .. 0x80895c), else it reads 0 | the game's own, bound action: per re/fa_round.md 6.1 and re/playtest.md 1.3 it is Cover (**C / pad A**). Which action name feeds `+0x2d3` was NOT traced here (ASSUMED from those notes and the prompt 'Get Up'). |
| the prompt | 0x5505c0 (player's frame, 0x580976): while `[D+0x2c]`, 0x4c06c0(player, 0xc or 0xd, 5, 1.0, ..) offers the user action; kind 5 = 0x50a8f0's branch that reads `[D+0x2b]` | the game's own 'Get Up' prompt - **only while he lies**, not during the get-up |
| the prone movement M | `ZFFPlayerMovementProne`, vtable 0xbb5d64; `[M+0x8d4]` the player; state setter 0x478270, frame = slot 17 0x640930 | `[M+0x8ec]` **1 falling, 2 lying** (he crawls: the stick picks one of the crawl clips), **4 getting up, 5 done**; `[M+0x8cc]` the clip, `[M+0x8d0]` its animation channel, `[M+0x8d8]` tick it began, `[M+0x8dc]` **tick it is over**, `[M+0x8e0]` tick of the clip's event 2 |
| **the get-up's speed** | 0x478270, state 4: speed = **1.0**, or `[0xb89a20]` = **2.5** with the fast flag; `player->vtable[+0x200]` = Play 0x4da1d0(clip, 1, 0.0, -1.0, speed) -> the channel; `[M+0x8dc]` = now + (frames - 1) / 25 / speed x 1024, `[M+0x8e0]` = the same for event 2's frame (0x4a75d0(clip, 2); no event: = `+0x8dc`) | the channel (re/climb.md 6: sixteen at `[player+0x70] + 0x1c + 0x38 i`): `+0` clip, `+4` frame, `+0xc` last frame, **`+0x10` frames a second = speed x 25** (0x4da577 .. 0x4da585), advanced by the update 0x50af22 .. 0x50af32 (frame += dt x `+0x10`) |
| the end of the get-up | 0x640c35: M state 4 and tick >= `[M+0x8dc]` -> 5 -> 0x47cf31 ends D. Earlier: 0x69a440 (tick >= `[M+0x8e0]` when that is not after the end; else start + 0.7 x length) AND 0x8ee550 (the stick is pushed over 0.2) -> ended at once | LOG: 0.80 / 0.81 s in all eight get-ups = (21 - 1) / 25: the clip's length (a 21-frame clip); the stick's early end would vary |
| the session mode | 0x76a48e .. 0x76a7c8 | only the kill-feed line, the health given and the pause depend on the mode. 'The downed state exists only in session mode 2' (CLAUDE.md, about 0x5fe270) is about ANOTHER object, `[player+0x2940]` (15 states: the death sequence and its camera) - not this one. |

## 2. The AI heister's flop (READ, partly)

- His damage routine 0x8473a0 (`ZSoldier@CPPScript` slot 96; re/melee_damage.md 3.3) writes the new health; when it is 0
  (0x847937) it asks slot 51 = 0x688190 -> **0x70e0e0(soldier, hit record, 0)**; true -> he is DOWN and not dead
  (0x847ea3), false -> he dies.
- 0x70e0e0 says yes when: the actor's `vtable[+0x654]` says no; his state object `[[soldier+0x4b4]+8]` is 0 or 4;
  0x70f330(`[soldier+0x4b8]`) (his down object can start); the hit's damage `[rec+0x28]` is under **1,000** - or under
  **500,000** for an actor for whom 0x6fd7c0 is true (GUESS: the crew / an ally; it is what lets a heister survive a
  252-health 'ONE STEP', and why the left-behind kill of 1,000,000 is final); a hit with an attacker, flag `[rec+0x30]` and
  a kind other than 1 must come from within `[T+0x5c]`; then the squad's `EDownNotDeadModifier` `[soldier+0x124]`: 1 =
  always, 2 = never, else: not within `[T+0x54]` s of the last NPC that went down in the level (`[gamedata+0x4d04]`; not
  asked for a 0x6fd7c0 actor), and within `[T+0x58]` s of it only by his chance `[actor+0x804]` per cent. One more
  refusal: a non-0x6fd7c0 actor with byte `[actor+0x5cb]` set (0x70e13f). Then 0x4860e0 /
  0x6cabf0 start his `ZDownNotDeadNPC` state, byte `[actor+0x64c]` = 1.
- NOT READ: how long he lies, what gets him up, whether he shoots meanwhile (`ZDownNotDeadNPC@CPPScript`, `ZWounded`),
  the values of `[T+0x54]` / `+0x58` / `+0x5c` and `[actor+0x804]` in the builds, what 0x6fd7c0 tests. `[Bots] Log=2`'s
  '... DOWN' is 'health 0' - by this reading that line is ALSO what a flop prints, not only a death (ASSUMED; the
  `status` / `dead` lines of klbot.c tell them apart).

**The difference.** AI: at the killing hit, in place of death, by chance and a level-wide pause. Human: while he still
has health (at or under 40 %), under a burst of 120 in a second, the hit swallowed, 10 s pause; a killing hit outside
that rule kills.

## 3. The human-shield break-out (READ, partly)

- It exists only for a PLAYER held as a shield (PvP): `ZFFActionStruggleHumanShield` (vtable 0xbb52c0). Its start
  0x4e8b10 arms the victim's input object H (`ZGameplayInput`, `[gamedata+0x1590]` -> 0x61ef90): byte `[H+0x2b8]` = 1,
  dword `[H+0x2b4]` = 0, 0x656060(H, 1, 0, 7); its end 0x7a1790 clears both and calls 0x656060(H, 0, 0, 7). The taps
  travel as a float: RMC `RMCSetHumanShieldPvPTapsShield` / `..TapsCarrier` (`fTaps`), sent by 0x502510 -> 0x429f40
  and kept in `[[player+0x540]+0xae4]`; `RMCHumanShieldPvPResetStruggle`; the victim's clips
  `/Close_Combat/Human_Shield_Victim/*_Struggle_lvl_01..03`, the win `/Close_Combat/Engage/Human_Shield_Struggle_Win`.
- NOT READ: which action is counted, how `[H+0x2b4]` counts, what 0x656060 does (an input mode 7), what the tap
  number drives (the names say three struggle levels), the HUD element (`ZHumanShieldDisplay`, re/hud.md) and its text.
  The string `TapQuickly` (0xb7f46c) has one reader, 0x8ac751: not read.
- **So the hook does not use that counter**: arming it means calling 0x656060, which was not read. The mash is counted
  on the game's own GET UP button `[D+0x2b]` (0 -> 1 = one press), which the input computes every frame from the
  player's binding - a pad or a rebound key counts as it does for the game.

## 4. The design

1. **The fall, lying, crawling, shooting from the floor, the camera, the first press: the game's own, untouched.**
2. **The get-up is a mash.** While `[D+4]` = 3 and M is in state 4 and `[M+0x8d0]` is one of the player's sixteen
   channels: speed = `Base` + `PerPress` x meter, at most `Top`; the meter gains 1 a press and loses `Decay` a second.
   Each frame: `[channel+0x10]` = speed x 25; `[M+0x8dc]` = tick + (end frame - frame) / (speed x 25) x 1024;
   `[M+0x8e0]` the same for the event's frame (already passed: the tick now). End frame and event frame are taken from
   the game's own ticks on the first frame, so the state ends exactly as it would. A get-up the game started at 2.5
   is left alone, and so is a channel whose clip is not `[M+0x8cc]` (the clip 0x478270 handed to Play: a stopped
   channel is reused and `[M+0x8d0]` is not cleared).
   **The time bound** (review M1): stock fixes the end tick when the clip starts; the hook moves it with the clip's
   frame, and a frame that stands still (the player's animation update skipped - 0x74efc0's three gates -, channel
   flag 0x100000 at 0x50af15; neither shown to happen in a get-up, neither ruled out) would move it ahead for ever.
   So on the first frame cap = tick + end frame / (`Base` x 25) x 1024 + 256 (0.25 s), and no end tick (nor the
   stick's tick) is ever written after it: the slowest get-up is the `Base` one and the state always ends. One log
   line when the bound, not the clip, holds the end. Replayed off the game (scratchpad `R/capsim.py`): frame frozen
   at 5 of 20 -> over after 1.85 s with or without presses; `Base=0.25`, frozen at 0 -> 3.46 s.
   With the defaults and a 20-frame clip (worked out, not seen): no press 1.6 s, 4 presses a second
   1.0 s, 6 a second 0.85 s, 10 a second 0.7 s; with `Base=0.25`: 3.2 / 1.3 / 1.0 / 0.8 s.
3. **The trigger by keys** (section 1's numbers; each written only when set, what stood there kept and put back):
   `Burst=1` + `HealthPct` = 'one hit of 20 or more floors a hurt man' - the AI's rule as near as the data allows.
   It is NOT 'in place of death': a hit that takes all his health while the pause runs, or of under `MinHit`, or with
   no room to lie, kills as ever.
4. What the cases come to:
   - **while down** he can crawl and shoot (the game's rule); hits during the fall cost nothing; lying he takes
     full damage with at least `DownHealth` (80 of the owner's 401.5) - and getting up too. **What the slow get-up
     costs**: stock exposes him 0.8 s in the get-up, `Base=0.5` 1.6 s, a brisk mash (6 a second) 0.85 s; a police
     bullet is 75 under Risk=2. With the game's 80 the part can only make him die MORE often than stock; hence
     `DownHealth=200` is the value proposed beside `Enable=1` (written as his maximum at most), and D2 / D3 count
     deaths in the get-up (`DEAD WHILE GETTING UP`) and the health lost in it. Whether an AI heister takes hits
     while down was not read, so '1:1' is not shown on that point.
   - **the mash key is Cover.** While he is down the presses do nothing else (0x84dda0); when D is cleared the next
     press is an ordinary Cover press: a man mashing beside a wall or a low box goes into cover or over it. No data
     fix is known; for the owner's eyes after D3.
   - **the police**: nothing stops a guard at arm's length - one point-blank step is 100 bullets (re/melee_damage.md)
     and kills a lying man at once. `[Balance] PointBlankToYou` is that key; `DownHealth` (say 200) softens bullets.
   - **a death while down**: the game's reset (0x803c40 -> 0x88a990) clears D; the hook sees `[D+4]` = 0, logs, drops
     its record. **The fed respawn**: the new body is another player object with the police byte: the hook does
     nothing for it and puts the trigger numbers back while the local player is police.
   - **the escort / FollowOut** read the player's place only: a lying player is a slow player to them. **Cover**: at a
     cover the game gets him up INTO it (`[D+0x20]`, no state 4): no mash there. **The round end, the vehicle, the
     Retomoto join while down**: the game's own ends (0x49b9f0, 0x49c180, 0x6daf30, 0x803c40 call 0x88a990); the
     hook only follows `[D+4]`. A jump of the player while he gets up was not read (ASSUMED harmless: the channel
     and M belong to the player object, which the join keeps).
   - **multiplayer, a stock level**: nothing (klbalance.c's Arcade test, klbot.c's 'not the stock level').
5. **The prompt.** The game's 'Get Up' prompt shows while he lies. A 'tap to get up faster' during the get-up cannot be
   shown by data found here: the prompt list is built by 0x5505c0 only while `[D+0x2c]`. For klhud.c (kl-merge-3e): the
   hook can give it `kld_s.up` (a get-up it drives), the meter 0..n and the speed; it would need one of the stock text
   objects it already borrows, shown while `kld_s.up` - strings only draw through stock objects so far.

## 5. `klhook/kldown.c` - keys

`[Down]` in KLHook.ini (the sample has the section, all off):

| key | default | the owner's proposed value | what |
|---|---|---|---|
| `Enable` | 0 | 1 | the part |
| `Dry` | 0 | 1 for the first run | nothing written; logs falls, get-ups, the speed it WOULD set, where the keys' trigger WOULD floor him (an estimate from the steps of his health) |
| `Log` | 1 | 1 | 2 = the get-up four times a second |
| `Base` | 0.5 | 0.5 (GUESS; 0.25 if 1.6 s is too quick to feel) | the clip's speed with no press |
| `PerPress` | 0.3 | 0.3 (GUESS) | added per unit of the meter |
| `Top` | 2.0 | 2.0 (GUESS) | ceiling |
| `Decay` | 2.0 | 2.0 (GUESS) | meter lost a second |
| `HealthPct` | - (game: 40) | 40 | `[T+0x268]` |
| `Burst` | - (game: 6) | 1 | `[T+0x278]` |
| `MinHit` | - (game: 20) | 20 | `[T+0x274]` |
| `Window` | - (game: 1.0) | - | `[T+0x26c]` |
| `Cooldown` | - (game: 10) | 10 | `[T+0x264]` |
| `DownHealth` | - (game: 80) | **200** beside `Enable=1` (section 4.4) | `[T+0x25c]`; written as his maximum health `[[player+0xa48]+8]` at most (0x61efd0 not read for a clamp), not at all while the maximum cannot be read |

Writes: `[channel+0x10]`, `[M+0x8dc]`, `[M+0x8e0]`, six floats of T. No call, no patch, no vtable copy. Game thread only.

Wiring (klhook.c, the lead's):

    #include "kldown.c"                 after  #include "klfed.c"
    kld_init();                         after  klp_init();
    kld_tick(game_thread);              after  klp_tick(game_thread);

Compile check (git archive HEAD klhook + this file + the three lines, `G:\kl_scratch\R\src`): after the fix round: TEST
`G:\kl_scratch\R\test\dinput8.dll` sha1 2b5b7a173dff8468236e5042f78f26aa5419c9e1, SHIP `G:\kl_scratch\R\ship\dinput8.dll`
sha1 7fc94f62ddc22880deb17fcffc69d78dd777bd4c (the build stamps the time: a hash is per build); the only warning is
klhud.c(188) C4101, none from kldown.c.

## 6. Live checks (the lead; the scripted player; `[Shoulder] Log=1` beside each: its `dstate` lines are the control)

The bank (DM03) with the owner's balance (Risk=2: a police bullet is 75, over `MinHit`); the walk of
`PT_DM03_die` into the hall, then stand in the fire. Rig: `tap C` is the GET UP press (`tap <key> [hold ms]`).

| run | keys | script after the walk | PASS | FAIL |
|---|---|---|---|---|
| D0 | no `[Down]` | - | no `down:` line | any |
| D1 | `Enable=1 Dry=1 Log=2` | `tap C` every 2 s | `down: on (Dry=1 ...`, `... Dry=1 - the part only logs this round`, `YOU ARE DOWN (1) ...`, `lying after 0.7x s`, **`GETTING UP ...: channel N, clip .. of F frames, the game's speed 1.00, over at frame F-1 ..`**, `UP after .. the get-up took 0.80 s` - and the same times as the shoulder log's `dstate` lines | no `GETTING UP` although the shoulder log shows `dstate 1->3` (the channel is not where it was read); `the end tick does not fit the clip`; `speed` not 1.00 |
| D2 | `Enable=1 Log=2 DownHealth=200` | `tap C` every 3 s | `GETTING UP ... it is played at Base 0.50`, `get-up: frame .. speed 0.50` lines, **`UP ... the get-up took 1.5 .. 1.7 s, 0 press(es), mean speed 0.50`**, he walks on (a `goto` after it is reached), shoulder `dstate 3->0` at the same moment; `GETTING UP ... over in 1.85 s at the latest`; COUNT the `DEAD WHILE GETTING UP` lines and read `health lost in it` against D1's | the state never ends (`dstate` 3 for over 2.1 s after the clip began), a fault, he stands frozen; `ENDED BY THE TIME BOUND` / `the time bound holds the end tick` = the clip's frame stood still: the bound did its work, tell the track |
| D3 | the same | one `tap C`, then `tap C 40` + `wait 60` x 30 | `UP ... the get-up took` under 0.8 s, `N press(es)` over 5, `mean speed` over 1.2; count deaths and health lost as in D2 | presses 0 (the button byte does not pulse: `[D+0x2b]` is not the tap, or the input lock `[input+0x330]` runs / `[player+0x2720]` bit 1 is clear in state 3 - the get-up then stays at Base) |
| D4 | `+ HealthPct=60 Burst=1` | as D2 | `the game's own rule as found ...: HealthPct 40.0 Burst 6.0 MinHit 20.0 Window 1.0 Cooldown 10.0 DownHealth 80.0`, `the trigger is written (2 number(s)): HealthPct 40.0 -> 60.0 Burst 6.0 -> 1.0`, more `YOU ARE DOWN` than D2 at higher health; back at the menu `the trigger is back as the game had it` | `found` numbers not the built-in ones (then the offsets are another block: say so) |
| D5 | D4 + `[Fed] Enable=1 Player=1` | no `tap C` at all | `the down state is over ... he is dead`, klfed's `YOU ARE A FED`, `the trigger is back ...` in that tick, no `GETTING UP` for the police body | a `down:` write line while police |
| D6 | D2 on stock Subway (the Arcade page) | - | `... nothing is written here (the part acts only on a level that is not stock)` | any other `down:` line |

For the owner's eyes after D3: does the slow get-up look right (the clip at half speed), does a mash feel like one,
and what the last press does once he stands beside a wall or a low box (it is a Cover press).

## 7. ASSUMED / not done

- ASSUMED: `[D+0x2b]` goes 0 -> 1 once per press (a tap pulse or a held level: either gives one edge a press); the
  button byte is refreshed in state 3 (input lock `[input+0x330]` 0 and `[player+0x2720]` bit 1 set: 0x808943 ..
  0x80895c - else it reads 0 and the get-up stays at Base; D3's FAIL line covers it); the get-up clip has 21 frames
  (0.80 s in all eight of the log's get-ups); writing `[channel+0x10]` after
  Play has no other reader than the update (the channel's `+0x2c` is read at 0x50af2c; the other readers of the block
  were not listed); a level's tuning data does not rewrite the six floats mid-round (the hook would take a change for
  the game's and keep it).
- NOT DONE: the AI's trigger on the human (down at the killing hit) - code in 0x458880; the AI side's lying / get-up
  (section 2) - so 'the bots obey the same mash' is not claimed: only the human's get-up is slowed; a prompt during
  the get-up (section 4.5); the break-out's own counter (section 3); a mash BEFORE the get-up starts (the first press
  starts it at once: holding that back needs the input's write of `[D+0x2b]` ordered against the hook's tick);
  protection of a lying player from a point-blank step; an off-game harness.

## 8. The review (re/player_down_review.md: ACCEPT WITH FIXES) and what was done, 2026-10-11

| point | done |
|---|---|
| M1 the get-up lost its time bound | DONE: `kld_s.cap` set on the first frame (the clip at `Base` speed + 0.25 s), no end tick / stick tick written after it, one log line when it holds, `ENDED BY THE TIME BOUND` in the UP line; replayed in `R/capsim.py` |
| S1 channel adoption | DONE: the first-frame test wants the channel's clip == `[M+0x8cc]`, else one line and left alone |
| S2 the slow get-up costs health | DONE: said in 4.4 and the sample, `DownHealth=200` proposed, D2 / D3 run with it and count `DEAD WHILE GETTING UP` + `health lost in it` (both new in the log) |
| S3 `DownHealth` past his maximum | DONE: written as his maximum at most; not written while the maximum cannot be read (0x61efd0 still not read) |
| S4 a death logged as UP | DONE: `DEAD WHILE GETTING UP`; a changed player object in a get-up gets its own line |
| S5 the mash carries into Cover | DONE (note, sample, the owner's checks); no data fix |
| S6 note corrections | DONE: eight get-ups / 21 frames, the blast, the late press, `[actor+0x5cb]`, the input lock |
