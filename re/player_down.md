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

## 9. The belly flop (track R2, 2026-10-11 afternoon)

Owner, on hearing what sections 0 - 8 built: *'when i go down it does that gun one, i mean the other one where its like a
full belly flop dive on the floor come on'*. **Offline; the flop has not run in the game.** READ / LOG / FILE (the stock
and the five tab builds' `.ANM`, read with `tools/kl_anm.py` + `kl_fa_climb.root_keys`) / LIVE (the lead's runs D1, D2
of track R's form, 13:53 and 13:59) / ASSUMED are marked. Scratch: the session's scratchpad `R2/`.

**NOTE (track R3, review3 S6): the form of this section is `Flop=2` now.** `Flop=1` became Dog Days' own knock-down
(section 10). Wherever this section says `Flop=1`, read `Flop=2`; the run keys of 9.5 are corrected in place. And see
section 10 for what this section had wrong (who plays `Die_Forward`, the name-table offsets).

### 9.0 The short answer

- **'The gun one' is the game's own fall** - and it is ALSO what an NPC's own 'down not dead' plays, so 'like the bots'
  cannot mean that state. **What the AI heisters do when the police shoot them is die**: the dive is their death clip
  `/Damage/Death/Die_Forward`. In Arcade no AI heister was ever seen to come back from health 0 (LOG: 235 of 235).
- **The player can be given that dive by six words of data** (the slot ids his prone movement plays), and a get-up
  from the stomach the game already has for him (`/Movement/Rise/Rise_From_Stomach`); both clips are in every character
  set of all five tab builds (FILE). The trigger, the camera, the health rule, the end of the state stay the game's.
  `[Down] Flop=1` in `klhook/kldown.c`; with `Flop=0` the part is track R's (one exception: 9.6).
- **What it changes for dying**: the whole dive (2.0 s) costs nothing - by the game's own rule, stretched to the
  clip's end - where stock's fall is free for 0.72 s; then the get-up costs in full and is LONG (the clip is 8 s at
  speed 1): hence `FlopTake` and `FlopUpPct`.

### 9.1 What plays what (READ + FILE)

| who | routine | slots | the clips in the files |
|---|---|---|---|
| the player's fall and get-up | `ZFFPlayerMovementProne` slot 20 = **0x750900** fills words of M: `+0x898` `Down_Not_Dead_Get_Up`, `+0x89a` `Compact_.._Get_Up`, `+0x89c` `On_Spot_.._Get_Up`, `+0x8b0` `Down_Not_Dead_Get_Down`, `+0x8b2` `Compact_.._Get_Down`, `+0x8b4` `On_Spot_.._Get_Down` (then `Aim_Cycle_UB` at `+0x8c8` and the crawl sets); **the one reader of the six words is 0x5d6060**: state 1 -> `[M + 0x8b0 + 2v]`, state 4 -> `[M + 0x898 + 2v]`, v = `[M+0x8f0]`; a negative id (none) -> the plain one; no plain one -> no clip, and 0x478270 returns without playing | `/Damage/Down_Not_Dead/...` | `Down_Not_Dead_Get_Down` 48 frames, events 5 at 0, 6 at 7, 2 at 18, **root 23 BACKWARD** (forward is -z) and 3 down: he sits back onto his back, gun up - 'the gun one'. `Down_Not_Dead_Get_Up` **37 frames**, event 2 at 20. The two `Compact_.._Get_*` names are in NO file (the level has `Compact_Down_Not_Dead_Up / _Down`): those two words are 'none' in every level. `On_Spot_.._Get_Down` 41 frames, no root motion |
| an NPC's 'down not dead' | the state graph **0x730be0** (`[0x1549040]`): state `DownNotDead` (word `+0x2c`) from the loop `Down_Not_Dead` and `Get_Down`, `_Crouch`, `_RUN`, `_Walk`, `Get_Up`; started by `ZDownNotDeadNPC@CPPScript` (vtable 0xbcfd24): slot 1 **0x7ea990** = how long he lies (`[T+0x4c]` .. `[T+0x50]` s at random; `[T+0x40]` .. `[T+0x44]` for the one actor `[gamedata+0x4cf0]`, which is what 0x6fd7c0 tests - the campaign's buddy, nobody in Arcade), the level's 'last NPC down' tick, **his health raised to 25 % of his maximum** (0x7eaac0 .. 0x7eab13), byte `[actor+0x64c]`; slot 2 **0x5f4ac0** = the script: the state, wait the time (he can be hit: 0x70e0fe refuses a second flop while his state object is not 0 or 4), **health set to 75 %** (0x5f4d2c), byte `[actor+0x5cb]` = 'has been down once' (the refusal of section 2), back to the state `Stand` | the same names | **`_RUN` and `_Walk` are ALIASES of `Down_Not_Dead_Get_Down`'s data in every set of every stock file** (same data offset): an NPC's flop is the player's fall, clip for clip. Only `_Crouch` differs (`Crouch_impact_to_Down_not_dead`, 29 frames, on the spot) |
| **an AI heister shot dead** | `ZFFActor` slot 196 = 0x802250 resolves `Die_Forward` (`[actor+0x60c]`), `Die_Backwards` (`+0x60e`), `Die_On_Spot` (`+0x610`), `Impact_01`; **0x72ab60** picks: no ragdoll (vtable +0x300 says no) -> the hit's direction against his forward: **from behind `Die_Forward`**, from the front `Die_Backwards`; no room (0x54a790) or no direction -> `Die_On_Spot`; played whole (vtable +0x204) | `/Damage/Death/...` | **`Die_Forward` 50 frames (2.0 s), no event, full-body, root 88 FORWARD by frame 31, then still: the dive onto the belly.** `Die_Backwards` 61 frames, 119 back. In all 11 character sets of the bank build, 10 / 11 of the other four (the rest of the 34 - 37 sets are weapon sets) |
| the player's rise | his name table 0x78d9d0 (object `[player+0x2a1c]`): word `+0x22` `Rise_From_Back`, `+0x24` **`Rise_From_Stomach`**, `+0x6a` `Die_Forward`, `+0x6c` `Die_Backwards`, `+0x6e` `Die_On_Spot` | `/Movement/Rise/...` | **`Rise_From_Stomach` = `Special_Moves/Heal_Wounded#Get_Up_From_Stomach`, 202 frames (8.04 s), no event, full-body, root still to frame 153, then 126 forward to the end (on his feet, walking off).** `Rise_From_Back` = `Wounded#Hero_Die_End`, 67 frames, event 8 at 0. Who plays the two in the game was NOT read (ASSUMED: the rise after a ragdoll throw, 0x451170) |

LOG: in the 225 live logs with `[Bots] Log=2` there are 235 lines 'bot ... (0.0 of 252.0)'; in none does the same
record lose health again in that round, and where a status line follows it says `dead`. So in Arcade an AI heister
does not go 'down not dead' (why 0x70e0e0 always says no there was not read: `[soldier+0x124]`, the chance
`[actor+0x804]` and the two pauses are the candidates) - **the flop the owner sees is the death clip.**

### 9.2 The fall and the get-up as the game runs them (READ; the parts section 1 did not have)

- 0x478270(M, 1): clip = 0x5d6060; event 6's frame (none: 0.3 x (frames - 1)) and event 2's (none: 0.5 x (frames - 1); at
  least event 6's); Play(clip, 1, start, -1, 1.0); **only when `[D+0xf4]` is set** (0x8aad50: a rotation at `D+0xf8`, a
  place at `D+0x11c` - a fall the game aligns, e.g. out of a cover) AlignTo(rot, place, event 6's frame);
  `[M+0x8dc]` = now + the frames left / 25 (the clip's end), `[M+0x8e0]` = now + event 2's frame / 25.
- The fall is over (M 1 -> 2, 0x640c00) at `[M+0x8dc]`. **0x843fa0** = 'D is 2, M is 1, the tick has reached
  `[M+0x8e0]`, and `[weapon object +0xdc]` is 0': from then on (a) the trigger 0x8da4e0 no longer swallows hits
  (LIVE, D2: down 14:00:49.87, the first loss 0.75 s later, seven more before he lay at 1.89 s = the clip's end);
  (b) 0x47cd80 offers GET UP and a press (or `[D+0x29]`) sets `[D+0x21]`; (c) 0x8ee220 may end the fall at once
  (bit 1 of `[player+0x818]`, `[D+0x34]`, or the weapon object's slot 11: LIVE, D1: 'lying after 0.72 s').
- **`[D+0x21]` is acted on whenever it is set** (0x47ce56, outside the 'may get up' test): 0x8b1900 - while D is 2 it
  runs 0x43c360(M): the fall's channel is stopped (vtable +0x1f8), M = 2, the input mask (bits 1 and 0x10) comes off -
  then D = 3 (0x8c8150) and 0x6373e0 -> 0x478270(M, 4, `[D+0x29]`): the get-up clip in that frame. With a cover's user
  action on offer (0x744fe0) it is 'get up into the cover' instead.
- The get-up without event 2: `[M+0x8e0]` = `[M+0x8dc]`, so the stick cannot end it early (0x69a440).
- **Correction to sections 0, 1, 7:** the get-up clip has **37 frames** (1.44 s), not 21. The 0.80 / 0.81 s of the
  owner's eight get-ups is event 2 at frame 20 + the pushed stick (0x69a440 + 0x8ee550). LIVE, D2: 'clip of 36 frames,
  the game's speed 1.00, over at frame 36.0, the stick may end it from frame 20.0; it is played at Base 0.50', then
  'frame 3.1 .. 6.3 .. 9.4 .. 12.5' a quarter second apart: **track R's speed write works in the game.**
- **LIVE: a death does not clear D.** D1: lying, three losses (32.5, 27.4, 19.7 of the 80 the game gave) in 0.45 s,
  `record 0 (you): dead` 0.6 s after he lay; D2 (`DownHealth=200`): 200 gone in 3.4 s on the floor, dead 1.1 s into the
  get-up at Base 0.5; in both the shoulder log shows D's state unchanged (1 / 3) to the end of the run, and the health
  object is made new at the death ('the game gave 550'). So `DEAD WHILE GETTING UP` (the 3 -> 0 form) never printed.
  D3 did not run (D2 ended in a stall at the score page: 'game window in front: no' from 14:00:56 - the lead's rig).

### 9.3 The design (`Flop=1`)

1. **While he is up** (D state 0), once per player object: both slot names looked up in the level's slot table
   (`klq_slot`, klclimb.c: the game's own binary search over `[player+0x80]`, by reads), the clips THIS body's set has
   for them listed by reads (the game's 0x5c2f60: table `[player+0x7c]` = {S, S x offset or -1}, the list at
   `[player+0x78]` + offset = {condition, clip number} pairs to the pair with condition 0, records at `[[0x1546f6c]]`
   + number x 0x68), each must be a full-body clip (record `+0x28` bit 0x10 clear). M is found among his movements
   (`[player + 0x630 + 4 n]`: the ZFFPlayerMovementProne whose `+0x8d4` is he; `[D+0xc]` is 0 until his first fall,
   0x57cfb2). Then the six words: fall x 3 = the id of `FlopFallSlot`, get-up x 3 = the id of `FlopUpSlot`; what
   stood there is kept and goes back when the part stops acting on that object. Anything missing: one line, nothing
   written, the game's own fall with track R's mash. Added by the second review (9.7): a clip carrying an event id the
   game's clip-event routine 0x637060 acts on, other than the stock fall's own 2 / 5 / 6, is refused (`klq_ev_to`,
   klclimb.c: the game's switch tables by reads); **each of the six words must hold the id of the game's own name for it
   in this level's slot table (the six names of 0x752e5b .. 0x752f0b through `klq_slot`), or 0xffff, or ours - else
   `NO BELLY FLOP: word k ... holds n` and nothing is written**; the check is made again when `[player+0x78]`,
   `[+0x7c]` or `[+0x80]` change (klchar.c's body swap keeps the player object), and a verdict that turns to 'no' puts
   the game's ids back.
2. **He goes down** by the game's own trigger (section 1; the six trigger keys mean what they meant) and the game plays
   the dive itself. The part looks at the clip that plays (`[M+0x8cc]`): only if it is one of the fall slot's is this
   down 'a flop' for what follows.
3. **During the dive** `[M+0x8e0]` is held at `[M+0x8dc]`: no press cuts the dive at its half (0.5 x 49 frames is
   where a clip without event 2 would allow it), and **every hit of the 2.0 s is swallowed by the game's own trigger**
   (a blast, hit kind 9, costs as ever: 0x458e8f).
4. **No lying on the back**: two frames before the dive's end the part sets `[D+0x21]` (the byte a press sets; the
   press's own call 0x8b74d0(`[player+0x274c]`), taken for the copy a session peer is sent, is NOT made: Arcade has no
   peer - ASSUMED). The game stops the dive's channel and starts the get-up clip in its next frame. Should he lie
   after all, the byte is set again (at most three times a second) - **only while M is 2**, the game's own
   precondition (0x47cddb .. 0x47ce2a; 0x6373e0 starts the clip only then). A request the game never took (D ended
   first) is taken back when D is 0 or he is dead: left standing it would cut the next fall in its first frame.
   **Beside a cover the game reads the request as 'get up into the cover'** (0x47ce07 .. 0x47cee8, a cover's user
   action on offer by 0x744fe0): `[D+0x20]` = 1, D ends at once, no get-up clip, no mash, no `FlopUpPct` (the log:
   `the down state is over ... without a get-up this part drove`). In stock that follows a press; here it happens by
   itself at the end of every dive beside a cover - and the dive carries him 88 forward, at whatever he faced. Whether
   a cover's offer can be seen by reads was not looked for (0x744fe0 is a routine): live check F7.
5. **The get-up is the mash** of section 4.2 on the 202-frame clip, with its own three numbers (`FlopBase` 1.5,
   `FlopPerPress` 0.6, `FlopTop` 5.0; `Decay` shared): no press 5.4 s, 4 presses a second about 2.6 s, 8 a second
   about 2.0 s (worked out, not seen). The time bound of 4.2 holds with `FlopBase`. The state ends as the game ends
   it (M 4 -> 5 at `[M+0x8dc]`). **Which numbers: by the get-up's CLIP alone** (it is one of `FlopUpSlot`'s) - not by
   whether the fall before it was seen as a flop: the get-up words are the flop's whenever they were written, and the
   202 frames at track R's `Base` 0.5 would be 16.1 s on the floor.
6. **Health.** `DownHealth` as before (the game's 80; an NPC's rule is 25 % of the maximum). `FlopTake` = the share
   of each loss while he lies after a dive / gets up by the flop's clip that stays; the rest is written back into
   `[H+4]` the next frame (klbalance.c writes the same float). `FlopUpPct` = his health is raised to that share of his
   maximum when the get-up ends with him alive (an NPC's rule: 75). Both off by default, both follow the clip test of
   point 5, neither is ever written for a man flagged dead in that down.
   **`FlopUpPct=75` makes the knock-down a HEAL**: he goes down at 40 % or less and stands at 75 %, again after the
   10 s cool-down, and the dive adds 2.0 s without any loss. That is 'the flop saves him as it saves a bot' - and a
   balance decision for the owner, not a default (he says he dies too quickly; `[Balance] Risk=1` is his own answer).
7. **A dead man is written nothing.** Dead = his health at 0 or his crew record's status 7 or 1; any other status but
   0 = out of play (4 aboard, 6 escaped). LIVE (D2): the record reads 0 'in-play' all through the fall, the lying and
   the get-up, 7 at the death. With `[Fed] Player=1` - in the owner's ini - the death is status **1** for the 5 s
   before the police body (run PT_DM03_die_r2), while D keeps 1 / 3 and the health does not read 0. Once seen, nothing
   more is written in that down (one line `DEAD / OUT OF PLAY WHILE ...`; the flag goes when D is 0).

**What a bot and the human then have in common:** the clip of the fall, that the dive cannot be interrupted, and -
with the two keys - the health an NPC's own down state would give. **What not:** the bot is dead and stays down, the
human gets up; the human's trigger is the game's burst rule under 40 % health, not 'the hit that takes the last
health' (that is the player's damage routine: code); the human always dives FORWARD whatever side the shot came
from (a bot shot from the front falls backwards: `FlopFallSlot=/Damage/Death/Die_Backwards` with
`FlopUpSlot=/Movement/Rise/Rise_From_Back` is that pair, by hand); while he gets up he cannot shoot (the game's state
3) and takes hits in full (minus `FlopTake`).

### 9.4 Keys (`[Down]`, beside those of section 5)

| key | default | proposed | what |
|---|---|---|---|
| `Flop` | 0 | 1 | the belly flop |
| `FlopBase` / `FlopPerPress` / `FlopTop` | 1.5 / 0.6 / 5.0 | the same (GUESS, for the owner's eyes) | the get-up clip's speed: none, per unit of the meter, ceiling |
| `FlopTake` | 1.0 | **0.25** (GUESS; the get-up is 5.4 s under fire where stock's is 0.8) | share of a loss in the get-up that stays |
| `FlopUpPct` | 0 | **the owner decides**: 75 = an NPC's rule = every knock-down heals him from 40 % or less to 75 % | health when up, per cent of the maximum |
| `FlopFallSlot` / `FlopUpSlot` | `/Damage/Death/Die_Forward` / `/Movement/Rise/Rise_From_Stomach` | - | the two slot names |

Writes added by `Flop=1`: six WORDs of M (while up), `[M+0x8e0]` (during the dive), the byte `[D+0x21]`, with the two
health keys the float `[H+4]`. No call of a game routine, no patch, no vtable copy; game thread only; Arcade, a level
that is not stock, a player who is not police - as before. Wiring: none to add - HEAD (5e778ef on) wires kldown.c in
klhook.c already. **The committed hooks test_w1 / ship_w1 carry track R's kldown.c: the `Flop` keys do nothing until
this file is committed and a hook is built from it.**

Compile check after the second review's fixes (`git archive HEAD klhook` at f9587ff + this kldown.c, sha1
b1a486babbb6a3625aa2875bb1f0336f179fe439, in `G:\kl_scratch\R2\fix\src`; no other line changed): 'built
G:\kl_scratch\R2\fix\test\dinput8.dll (TEST)' sha1 a7f0cb0d60f6e0b1917b14187b28b944279c62af, 'built
G:\kl_scratch\R2\fix\ship\dinput8.dll (SHIP)' sha1 e1da907a758179a771f5d3d50725d4e5ff59359e (a hash is per build);
`/W4` names no line of kldown.c (the one warning is klhud.c(188) C4101). Compile only: not for the game folder.

### 9.5 Live checks (the lead; the bank DM03, the owner's balance, `[Shoulder] Log=1`, `[Balance] Log=2` beside each)

The walk of D1 / D2 into the hall. A fall needs a hurt man under a burst: as D1 / D2 got it. **Order: F0 first** (the
`Flop=0` path is not byte for byte track R's any more: the death test), then F1 (dry: the part's own proof of the six
words), then F2. F6 before the hook goes to the owner (his ini has the fed on).

| run | keys | script | PASS | FAIL |
|---|---|---|---|---|
| F0 | `Enable=1 Flop=0 Log=2 DownHealth=200` | D2's | D2's lines; NEW: `down: DEAD WHILE GETTING UP: ... s after he went down ...; crew status 7, health ... - nothing more is written in this down` at the moment klbot says `record 0 (you): dead`, and no `down: get-up:` line after it | no such line at a death while down; `OUT OF PLAY WHILE ...` with a status other than 4 / 6 while he lives (= a status this part does not know: say which) |
| F1 | `Enable=1 Dry=1 Flop=2 Log=2` | D1's | `down: flop: Flop=2 - THE BELLY FLOP, two clips ...` at start; in the round `down: flop: the fall /Damage/Death/Die_Forward = slot 1780, clip 1 of 1: ... 'anim:Dammage/Die#Die_Forward', 50 frames (1.96 s ...), 0 event(s)`, `down: flop: the get-up /Movement/Rise/Rise_From_Stomach = slot 1755, ... 'anim:Special_Moves/Heal_Wounded#Get_Up_From_Stomach', 202 frames`, **`down: flop: the prone movement ........ holds fall 1847/65535/1850 get-up 1846/65535/1849 ...: Dry=1, it WOULD be written 1780/1780/1780 and 1755/1755/1755`**; at the fall `down: flop: this fall is the game's own (clip ... 'anim:Dammage/Down_Not_Dead#Down_Not_Dead_Get_Down' of 48 frames): Dry=1, nothing was written` | `NO BELLY FLOP on this body: ...` (says which read failed); **`NO BELLY FLOP: word k of the prone movement ... holds n, and <name> is slot m`** = the part's own test of the six words failed (they are not where they were read, or `klq_slot`'s table is not the one the filler's 0x770ba0 searches: ASSUMED the same); no `holds` line and no `NO BELLY FLOP` line = M was not found among his movements (`+0x630`) |
| F2 | `Enable=1 Flop=2 Log=2 DownHealth=200 FlopTake=0.25 FlopUpPct=75` (and `FlopBase=1.5 FlopPerPress=0.6 FlopTop=5.0` if the ini carries section 10's numbers) | D2's, no press | `... holds ...: written 1780/1780/1780 and 1755/1755/1755`; `YOU ARE DOWN`; **`down: flop: THE BELLY FLOP: the fall is clip ... 'anim:Dammage/Die#Die_Forward' of 50 frames (1.96 s)`**; NO `balance: you lost` line for about 1.9 s after it; `down: flop: the dive is over (1.9x s, n tick(s) left): the get-up is asked for`; shoulder `dstate 2->3` (no `2->1`); `down: GETTING UP ...: clip ... of 201 frames, the game's speed 1.00, over at frame 201.0, ... it is played at THE FLOP'S FlopBase 1.50`; `get-up: frame ..` lines climbing by about 9.4 a quarter second; `UP ... the get-up took 5.3 .. 5.5 s`; `down: flop: N health was given back`, `down: flop: up with 301.1 of 401.5 health`; a picture during the dive and one in the get-up: **face down** | a fault (dumps to the track); `this fall is the game's own ... the slot ids were not in place`; `he lies (...)` every 0.3 s without `GETTING UP` (the byte is not taken); `GETTING UP at the game's own speed` / `the end tick does not fit the clip`; `DEAD WHILE ...` (then raise `DownHealth`, lower `FlopTake`); he stands up somewhere else than he fell (root motion: 88 + 126 forward is right) |
| F3 | F2 | F2's + `tap C 40` / `wait 60` x 60 from the fall on | the dive is NOT cut (`the dive is over (1.9x s`), `UP ... the get-up took` under 2.5 s, presses over 10, `mean speed` over 3 | `the dive is over` well before 1.9 s = a press cut it (the hold of `[M+0x8e0]` did not take) |
| F4 | F2 on Hot Coffee with a Dead Men body (`[Character]` Char = a Dead Men hero) | - | the `flop:` lines for that body's set, or `NO BELLY FLOP on this body` and the game's own fall. Say which came first in the log, klchar's `body:` line or the first `down: flop:` line: if the flop's came first there must be `down: flop: the player ... has another animation set / slot table ... checked again` after `body:` and a second pair of clip lines | a fault; `body:` after the flop's lines and no `checked again` |
| F5 | F2, then back to the menu and stock Subway from the Arcade page | - | `down: flop: the prone movement ... has its own 6 slot id(s) again` or no line (the object was gone); on Subway `nothing is written here`, no `flop:` write line | a `flop: ... written` line on the stock level |
| F6 | F2 + `[Fed] Enable=1 Player=1 Log=1` (the owner's own setting), `DownHealth=80`, `FlopTake=1`, `FlopUpPct=0` so that he dies on the floor (PT_DM03_die_r2's balance keys if he does not) | D2's | ONE `down: DEAD WHILE FALLING / LYING / GETTING UP: ...; crew status 1 ...` at `fed: you: status 0 -> 1`; **no `down:` line that writes after it** (no `get-up:`, no `he lies`, no `given back`, no `up with`), at most `this part's get-up request [D+0x21] was still standing: taken back`; then `fed: YOU ARE A FED` 5 s later as in PT_DM03_die_r2, and the part silent for the police body | any `down: flop:` / `down: get-up:` line between the death and the fed; a corpse that stands up; no fed respawn |
| F7 | F2, the fall taken beside a low cover (facing it, within a metre or two: the lead picks the place; the bank's hall counters) | - | what is SEEN: either the ordinary flop lines, or `the dive is over ...: the get-up is asked for` followed by `the down state is over after 1.9x s (from state 2 / 3) without a get-up this part drove` = the game took the request as 'into the cover' (9.3 point 4). Both are no fault; the second is for the owner's eyes (does he snap from face down into the cover) | a fault; he stays in D 3 with nothing playing (shoulder `dstate` stuck at 3 for more than the time bound) |

For the owner's eyes after F2: is this the flop he meant; does the get-up start in the pose the dive ends in; is
5.4 s of slow get-up right or should `FlopBase` go up; what he does when he dives at a wall.

### 9.6 ASSUMED / not done

- ASSUMED: the loader keeps a set's table and pair list in memory in the shape 0x876940 / 0x7c6750 read (the part's
  list is the same reads); the six words have no reader but 0x5d6060 (searched by displacement: 0x5d6060 and the
  filler 0x750900 only); 0x750900 runs when the movement is made and not at every fall (if it runs again the part
  writes again while he is up); `[D+0x21]` written from the hook's tick is seen by 0x47cd80 in the next frame;
  skipping 0x8b74d0 is harmless in Arcade; writing `[H+4]` up is taken by the game as klbalance.c's writes are.
- NOT ESTABLISHED: how either clip looks on the player; the pose match between the end of `Die_Forward` and the start
  of `Get_Up_From_Stomach`; what the first 153 still frames of that clip show; a fall the game aligns (`[D+0xf4]`:
  logged in the BELLY FLOP line); the dive at a wall; a flop on stairs.
- CHANGED FOR `Flop=0` TOO (from the live runs): a death while down is now said once (`DEAD / OUT OF PLAY WHILE
  FALLING / LYING / GETTING UP`, by his health at 0 or his crew record's status not 0 through klbot.c's `klb_read`,
  read every frame while he is down), and nothing more is written in that down. Everything else of `Flop=0` is track
  R's code. So `Flop=0` is NOT byte for byte the committed form: F0 runs before F2.
- ASSUMED, new: a crew status other than 0 never belongs to a man who is down and in play (LIVE for 0 through a whole
  down in D2; 2, 3 and 5 were never seen and are treated as out of play); `[M+0x8cc]` still names the fall's clip
  while he lies (only used when the fall was first seen lying; if wrong, the get-up still goes by its own clip).
- NOTES (second review S9): no writer of `[M+0x8f0]` but the constructor (0x5bd6a6) was found, so the variant 'plain /
  compact / on the spot' may never change for the player - harmless, all three words of a kind hold the same id; the
  dive is 88 FORWARD where the stock fall is 23 back: toward the guns he faced; a pause in the dive's last two frames
  leaves the request standing until the game runs again.
- NOT RE-READ by anybody: the other four tab builds' clips for events (the bank's were, by the reviewer) - the part
  now tests each clip's events itself on every level and body.
- NOT DONE: the AI's own trigger on the human; a flop chosen by the side the shot came from; holding him on the
  floor until the first press (`FlopBase` low is the nearest); a prompt during the get-up (4.5); an off-game
  harness for the reads; `[Balance] Risk=1` in the owner's ini (his second sentence: 'the health difficulty probably
  put to 1 i think im dying too quick now' - the game folder is the lead's; his ini has `Risk=2`).

### 9.7 The second review (re/player_down_review2.md: ACCEPT WITH FIXES) and what was done, 2026-10-11

| point | done |
|---|---|
| M1 a dead man is written to under `[Fed] Player=1` (status 1, not 7) | DONE: dead = health 0 or status 1 / 7, any other status but 0 = out of play; latched for the rest of that down; `FlopUpPct` / `FlopTake` never for a man flagged dead; live check F6 |
| M2 the request while he lies without `ms == 2` | DONE: `ds == 1 && ms == 2` |
| M3 the 202-frame get-up on track R's numbers | DONE: `fup` by the clip alone; `FlopTake` / `FlopUpPct` follow it; a fall first seen lying is judged by `[M+0x8cc]` (ASSUMED) |
| S1 prove the six words | DONE: each word must be the game's own name's id, 0xffff or ours, else one line and no write |
| S2 free-text slots and events | DONE: a clip with an event 0x637060 acts on, other than 2 / 5 / 6, or with unreadable events, is refused |
| S3 the check is per object, the set is not | DONE: checked again when `[player+0x78]` / `[+0x7c]` / `[+0x80]` change while he is up; F4's PASS line says the order |
| S4 `[D+0x21]` left set | DONE: taken back when D is 0 after a request of ours, and at a death |
| S5 the request takes a cover | DOCUMENTED (9.3 point 4, the file's head), live check F7; no data fix (the offer is a routine's answer) |
| S6 `FlopUpPct=75` is a heal | DONE: said in 9.3 point 6 and 9.4; the proposal is now 'the owner decides' |
| S7 stale wiring / hashes | DONE: 9.4 (no lines to add; new hashes on HEAD f9587ff) |
| S8 `Flop=0` is not the committed form | ACCEPTED as the review says; F0 before F2 (9.5) |
| S9 notes | DONE: 9.6 |

## 10. The belly flop is Dog Days' own knock-down (track R3, 2026-10-11 ~15:30) - CORRECTS section 9

Owner, with three pictures of stock footage (a heister flat on his belly, the rifle by his hand; the same man up on
one knee; a man thrown by a hit): *'these kinda animations i meant for belly flop check the code for how they are in dog
days smh'*, and before: *'the belly flop shouldnt be when im already dead'*. **Offline; nothing here has run in the game.**
READ = kl2.exe; FILE = the `.ANM` of stock F01 / F07 and the five tab builds. NEW TOOL OF THE READING (scratchpad
`R3/pose.py`): a clip's ROTATION keys decoded as the game reads them (kl2 0x834170: byte 0 = bits 0-1 the dropped
component, bit 2 'one key', bits 3-7 the width B (31 = raw floats); three signed B-bit bases; three 5-bit widths; a
record a key = sign bit + three offsets; the fourth component = the root of the rest; frames by the `IdxT` table,
0x6663b0) - so a clip can be told 'on the belly' (the PELVIS under 35, the chest facing down) from 'on the back'
without the game. Checked on clips whose names say it (`Get_Up_From_Stomach` starts chest down, `Die_Backwards` ends
chest up).

### 10.0 The short answer

- **The pictures are the 'Wounded' clip family** (`anim:Dammage/Wounded#...`, slots `/Damage/Wounded/...`): ONE clip is
  the whole thing - thrown down, flat on the belly from its event 7 to its event 8, up over one knee, on his feet.
- **The human's own DEATH in stock Dog Days is one of them**: `ZFFPlayerMovementDie` slot 20 (0x789b10) fills its
  words with `/Damage/Wounded/Hero_Torso_F` (+0x54), `Stand_To_Crouch_Wounded` (+0x56), an L09 clip (+0x58) and
  `/Damage/Down_Not_Dead/Down_Not_Dead_wounded` (+0x5a: from the down pose; he STAYS ON HIS SIDE and only the head
  sinks, 48 -> 15 - full skeleton, review3 S3; the first reading 'over onto the belly' was the pelvis misleading). So the flop the
  owner knows is what he sees when he DIES ('shouldnt be when im already dead') - he wants it on a man who lives.
- **What the human plays on our maps when he goes down is exactly stock's** ('the gun one'): the six words resolve to
  the same clips in stock F01, F07 and all five tab builds, in every character set (the wardrobe's bodies use these
  sets too). Nothing of ours changed it; it was never the belly flop.
- **Section 9 was wrong on two points.** (1) `Die_Forward` is not the dive of the pictures - not because of its pose
  (review3 S3, full skeleton: it DOES end chest down - the shoulder girdle faces the floor, normal y -0.85 at frame
  49, head 12, both hands 13 - 15 on the floor, the hips twisted; this track's first 'ends on his SIDE' was a pelvis
  reading), but because it is a DEATH: the clip an actor without a ragdoll dies by (0x72ab60), with no rise of its
  own, and `Get_Up_From_Stomach` does not start in its last pose. The owner wants the game's knock-down with its own
  rise. (2) The name-table offsets of 9.1 are one entry off: the
  table 0x78d9d0 is {offset, name} pairs, so `Rise_From_Back` is +0x20, `Rise_From_Stomach` +0x22, `Die_Forward`
  +0x68, `Die_Backwards` +0x6a, `Die_On_Spot` +0x6c (what `ZBecomeRagdoll` 0x677200 compares with are the last two).
- **Built**: `[Down] Flop=1` now = Dog Days' knock-down, one clip (`kld_flop_one` in `klhook/kldown.c`); section 9's
  form is `Flop=2`, unchanged.

### 10.1 Who plays what (READ + FILE)

| who | routine | what |
|---|---|---|
| an NPC that DIES | `ZWounded@CPPScript` (vtable 0xbcfc64) slot 2 = **0x865180**: sets the actor dead (vtable +0x588 with 0), picks a state word of the graph 0x730be0 by 0x48cc10 - stance, front / back, and 'Merc' when `[[actor+0x54]+4]` is 0: words `+0x1e0 .. +0x1fe`, built from the name table's `+0x8e ..`: `/Damage/Wounded/Running|Crouched|Standing/Torso/Front_01|Back_01|Merc_Front|Merc_Back`, `Standing/Front_Head`, ...; each state is made with the event pair (7, 8) (0x7b0d30) | the clip to where he lies; a corpse on its belly = picture 1 when the man is dead |
| an NPC that is HIT and lives | `ZGeneric@CPPScript` slot 23 = 0x5681d0 builds 440 slot ids `/Damage/Impact/FB|UB/<stance>/<Front_|Back_><part>`; slot 22 = **0x4aba20** picks: full-body only when `[generic+0x98]` is 2 and the clip's net root movement has room (0x54a790), stance 'Running' when he moves over 250 a second | `/Damage/Impact/FB/Running/Front_Torso` = `Impact_02#Running_torso_Front_3` / `_2` (216 / 219 frames, the SAME animation as `Wounded#Run_Torso_Front_03` / `_02`: 3.0 - 3.6 m forward, down, UP AGAIN) or `Run_Torso_Impact` (a stumble, 53 frames): **the heister of pictures 1 and 2, alive** |
| which clip of a slot | 0x59d550 -> 0x5c2f60 -> **0x7c6750**: of a pair's condition word bits 3.. must all be set in `[actor+0x84]`; **bits 0-2 are WEIGHTS** (1.0; bit 2 -> 0.1; bit 1 x 0.33; bit 0 x 0.5) and one of the group is drawn by a random number | 'cond 1' / 'cond 2' pairs are random alternatives, not conditions; the player's prone movement goes the same way (0x5d6060 -> 0x59d550) |
| the human who DIES | `ZFFPlayerMovementDie` (vtable 0xbb5ac4) slot 20 = 0x789b10 (above); who reads the four words was NOT read | `/Damage/Wounded/Hero_Torso_F` |
| NOT USED | `ZRecoverGoal@CPPScript` (0x7f3c90: `Rise_From_Back` / `Rise_From_Stomach` by `[goal+0x14]` 2 / 1) - its only starter 0x4ca6d0 is called with 0 (0x71c841, 0x77a37d): no NPC plays the two Rise clips in this build | - |

The clips (25 frames a second; root forward = -z; B = on the belly, K = on the back, s = low on a side, U = upright -
**these letters, and `R3/prone.py`'s, are PELVIS readings** (height + the pelvis's facing), which get a twisted body
wrong (`Die_Forward`, `Down_Not_Dead_wounded`: 10.0). The rows below were read again by the reviewer with the whole
skeleton (103 bones composed down the stock F01 heister hierarchy, `R3rev/fk.py`; re/player_down_review3.md 1) and
stand: `Hero_Torso_Back` = arched back at frame 0 (a man hit in the BACK), face down by 20, flat on the belly 46 -
116 with the right hand out in front by the head and the left out to the side, pushing up 135 - 155, the right knee
down and the left foot planted in front 165 - 175, nearly standing 185; `Hero_Torso_Front` = on the back 30 - 177;
the stock fall and loop = thrown back, then on the left side with the head propped):

| slot (every character set of F01, F07 and the five tab builds; the Dog set aside) | clip | frames | events | shape | root |
|---|---|---|---|---|---|
| `/Damage/Wounded/Hero_Torso_F` (pairs: Back at weight 0.5 twice, Front at 1.0 = **one draw in two is the back**) | `Hero_Torso_Back` | 186 | 31 at 1, 0 at 39, 7 at 46, 8 at 116 | thrown forward, B from frame 40 to ~125 (pelvis 22.6, chest (0.1, -0.98, 0.18)), hands and knees ~136 - 160, **one knee ~168 - 176**, standing 185 | 0.55 m forward by frame 46, 0.2 back while rising, 0.66 at the end |
| | `Hero_Torso_Front` | 255 | 7 at 38, 8 at 177 | onto his BACK by frame 30, lies to ~200, up at 254 | 0.8 m backward |
| `/Damage/Wounded/Running/Torso/Merc_Back` (ONE clip) | `Merc_Run_Torso_Back_03` | 239 | 31 at 7, 7 at 55, 8 at 115 | a running dive: B from ~24, lies to ~130, knees ~160 - 200, standing 238 | **3.15 m forward in the first 29 frames** |
| `/Damage/Wounded/Running/Torso/Back_01` | `Run_Torso_Back_03` (the same shape) + `_02` + `_01` (onto the back) | 239 / 140 / 281 | | mixed | 3.3 - 3.5 m |
| `/Movement/Rise/Rise_From_Stomach` (one clip) | `Heal_Wounded#Get_Up_From_Stomach` | 202 | none | starts in exactly the lying pose of the three belly clips above (pelvis (0, 22.5, 3.4), chest (0.09, -0.98, 0.19)); lies to 50, knee at ~150, walks off | 1.26 m forward from frame 153 |
| the stock fall `Down_Not_Dead_Get_Down` and its loop `Down_Not_Dead` | | 48 / 167 | 5, 6, 2 | onto his SIDE, head away (chest (0.98, -0.09, -0.2), spine (0.2, 0.3, 0.9)), pelvis 15: 'the gun one' | 23 back |

Event 31 goes to case 2 of the clip-event routine 0x637060 (0x77ca60: an item of the action's - a hand's weapon; the
rifle beside the hand in picture 1 fits, GUESS); 7 and 8 go to 'nothing' there. The census: scratchpad `R3/census.py`.

### 10.2 `Flop=1` as built (`kld_flop_one`)

1. While he is up the three FALL words of his prone movement hold the id of `FlopFallSlot`
   (`/Damage/Wounded/Hero_Torso_F`); the get-up words stay the game's. The checks of 9.3 point 1 stand (the six words
   must be the game's own names' ids; every clip of the slot full-body); **events 7, 8 and 31 are let through** for this
   form (the game plays this very slot on the human itself - his death; ASSUMED harmless in the prone movement too).
2. He goes down by the game's own trigger; the game plays the slot's clip as its fall. Its own draw would be the back
   one time in two, so **`FlopBelly=1` (default; `kld_flop_belly`)**: in THIS body's set, every pair of the slot's list
   whose clip is not thrown forward (record +0x18, z not under -20) gets the clip number of the list's first one that
   is - four bytes in the level's animation set, put back when the part stops acting or the body changes. Side effect:
   the human's own death draws from the same list and falls forward every time, for whoever wears that set.
3. While D is 2 and M is 1 and the channel plays that clip, every frame: `[M+0x8dc]` and `[M+0x8e0]` = the tick the
   clip will be through at its present pace + 2 s. So the game does not end the fall at its tick (0x640c00), a press
   cuts nothing, no prompt shows (0x843fa0 is false), and **the game's own trigger swallows every hit of the whole
   knock-down** (a blast costs as ever). From the clip's event 7 (he has landed) on: `[channel+0x10]` = (`FlopBase` +
   `FlopPerPress` x meter, at most `FlopTop`) x 25; the meter is the game's GET UP button `[D+0x2b]` (the input writes
   it whenever he is down, 0x84dda0), minus `Decay` a second.
4. When the clip is through (half a frame left, or its channel stopped): **`[M+0x8ec]` = 5**. That is the value the
   movement's own frame writes when it is done (0x640c60) - from ANY state when `[D+0x20]` is set (0x640c4e), so 1 -> 5
   is a step the game takes itself. The game's next frame ends the down state by its own path (0x47cf0f: M at 5 ->
   0x8eea90, which does nothing at 5, -> 0x7107b0: D cleared, the camera back). `FlopUpPct` as before. No call, no
   patch.
   **THE INPUT MASK (review3 M1, READ).** The down start sets bits 1 and 0x10 of the input object's dword
   (0x76a806 .. 0x76a834: `obj` = 0x61ef90(`[gamedata+0x1590]`, `[player+0x91e]`, 0); 0x6feb90 = `or [[obj+8]+0xed0]`).
   The game takes them off in 0x8ee220 (0x10 at the event tick; both when the fall is over: 0x8ee31e / 0x8ee327),
   in 0x8b1900 (the `[D+0x21]` request) and in the reset 0x88a990 - **0x7107b0 does not** (read whole to 0x7108aa),
   and stock never reaches it from a fall without one of the first two. This form does. So with the state-5 write the
   part takes the two bits off itself, BY DATA: `kld_mask` does 0x61ef90's lookup by reads (read whole, 0x61ef90 ..
   0x61efc1: T = `[gamedata+0x1590]`, i = the signed byte `[player+0x91e]`, not -1; the 'there' byte `[T+20+20i]`;
   the object `[T+4+20i]`; nothing is written by it), and the write is 0x787600's (`and [[obj+8]+0xed0], ~bit`, read
   whole): one DWORD, bits 0x11 off. With it `[D+0xf0]` ('who floored him', a plain pointer, written new before every
   down at 0x8da48c) is zeroed as 0x8ee2bb does. Order: mask, then state 5; a refused mask write = no state 5, the
   part stops and the game ends the fall its own way. The mask dword is LOGGED at the fall (also in a Dry run: the
   stock fall must show bits 0x11 set and the `lying after` line must show them off - the proof of the lookup), in
   the `clip is through` line (before -> after) and in `UP` (must read off). Why not the other fix ('let the game end
   the fall, then write 5 from lying'): with M at 2 the game's frame 0x47cd80 offers GET UP and takes a press in that
   same frame (0x47ce25 .. 0x47ce4d -> 0x7180b0) - a man who mashes would be thrown into the stock get-up clip after
   he stands. NOT read: which inputs each of the mask's four tests gates (0x417310, 0x76fd40, 0x4d9ec0, 0x87d930);
   what else `[D+0xf0]` is read by while he is up (found: 0x76a4c7 / 0x76a564, the down start itself).
5. The bounds (review3 M2). (a) ONE FOR THE WHOLE KNOCK-DOWN, set at the first good read of the channel, in the game's
   ticks, tested before any write of a pass: the way to the landing at the pace the game gave the clip + the rest at
   `FlopBase` + 1 s (defaults: 1.8 + 7.0 + 1 s). (b) After the landing: 'the rest of the clip at `FlopBase` + 0.5 s'.
   Past either the part stops writing: the fall ends at the tick last written (2 s at most) by the game's own 2 -> 1
   (which takes the mask off), he lies the game's way and its own GET UP gets him up. Every pass that cannot read the
   channel writes nothing, so it ends the same way. ASSUMED: the game's tick stands still in a pause (if it runs on,
   a pause longer than the bound hands the fall back to the game - no fault).
6. With the defaults (`FlopBase` 0.8, `FlopPerPress` 0.5, `FlopTop` 3.5; GUESSES) `Hero_Torso_Back` is: 1.8 s to the
   landing, then 7.0 s with no press, about 2.7 s at six presses a second (worked out, not seen).

**THREE DECISIONS FOR THE OWNER, before this goes on his game (review3 S4):**

1. **Nothing can hurt him for the whole knock-down** - no bullet costs from the hit that floors him until he is on
   his feet: 1.8 s of dive + 7.0 s on the floor and rising with no presses (about 4.5 s mashing), against 0.72 s in
   the stock game and 2 s in `Flop=2`. A blast still costs. The task asked for 'the game's own rule while he lies'
   (full damage on the floor): this form cannot give it, because the game only knows 'falling' (free) for one clip.
2. **He cannot shoot from the floor.** The stock side-lying state is where he can aim and fire; here the whole clip
   is the game's 'fall', with his input masked. The pictures show the gun forward; he holds it, he cannot use it.
3. **With `FlopBelly=1` his DEATH is the forward flop every time** (stock: one death in two is the fall onto the
   back) - the knock-down and the death then begin with the same frames, next to his 'the belly flop shouldnt be when
   im already dead'. `FlopBelly=0` leaves his death alone and puts the KNOCK-DOWN on his back one time in two.
   Having both (always the belly alive, the stock draw dead) needs the level step of 10.5 (a new one-pair slot):
   the reason to write `tools/kl_fa_flop.py` after all, once the look is approved.

Also: the first frames of `Hero_Torso_Back` are a man hit in the BACK; shot from the front he may look shoved from
behind (his eyes, G1). `FlopTake` does nothing here. `/Damage/Wounded/Running/Torso/Merc_Back` (`FlopFallSlot`) is
always the belly, but lunges 3.15 m.

### 10.3 Keys

`Flop=1` (2 = section 9), `FlopBase` 0.8, `FlopPerPress` 0.5, `FlopTop` 3.5, `FlopBelly` 1, `FlopUpPct` 0, `FlopFallSlot`
`/Damage/Wounded/Hero_Torso_F`. Mode 2 keeps its own defaults (1.5 / 0.6 / 5.0, `Die_Forward`, `FlopUpSlot`,
`FlopTake`). Writes added by mode 1: three WORDs of M (while up), one DWORD a re-pointed pair of the set, `[M+0x8dc]`, `[M+0x8e0]`, `[channel+0x10]`, once
`[M+0x8ec]`, once the input mask dword `[[obj+8]+0xed0]` (bits 0x11 off) and `[D+0xf0]` (0); with `FlopUpPct` the
float `[H+4]`.

Compile check after the third review's fixes (`git archive HEAD klhook` at e9a1a57 + this kldown.c, sha1
334df393c0995d2f1b20061c78504841aed2ca2d, in `G:\kl_scratch\R3\src2`; HEAD wires kldown.c, no line of klhook.c
changed): 'built G:\kl_scratch\R3\test2\dinput8.dll (TEST)' sha1 f06314498159bbb2eaba56a14d34ae8748be8a59, 'built
G:\kl_scratch\R3\ship2\dinput8.dll (SHIP)' sha1 a04f77ac714dd7a15a1d0cc0a4ebbe1a3c29cb44; the one warning is
klhud.c(188) C4101. Compile only. (`test` / `ship` beside them are the first round's, on dd215a6: superseded.)

**HEAD CARRIES THIS TRACK'S `[Down]` INI TEXT ON R2's `kldown.c`** (review3 S2: commit 370bc51 took the sample
block). Until this `kldown.c` is committed, a hook built from HEAD with `Flop=1 FlopBase=0.8` plays R2's
`Die_Forward` + the 202-frame rise at 0.8 (10 s). No hook is to be built from HEAD with `Flop` set before that
commit; the lead commits (this track does not).

### 10.4 Live checks (the lead; the bank DM03, the walk of D1 / D2, `[Shoulder] Log=1`, `[Balance] Log=2`)

| run | keys | PASS | FAIL |
|---|---|---|---|
| G0 | `Enable=1 Dry=1 Flop=1 Log=2` | at start `down: flop: Flop=1 - DOG DAYS' OWN KNOCK-DOWN, ONE CLIP ...`; in the round three lines `down: flop: the fall /Damage/Wounded/Hero_Torso_F = slot 1775, clip 1 of 3 ...: 'anim:Dammage/Wounded#Hero_Torso_Back', 186 frames ..., 4 event(s) - 7 at 46, 8 at 116 -, the root goes 66 forward`, `clip 2 of 3` the same, `clip 3 of 3 ... #Hero_Torso_Front', 255 frames ... 7 at 38, 8 at 177 ..., the root goes -84 forward`; `down: flop: FlopBelly: pair 3 of the list (condition word 0) is clip .. '...#Hero_Torso_Front', the root goes -84 forward: Dry=1, it WOULD get clip .. '...#Hero_Torso_Back'`; `... holds fall 1847/65535/1850 get-up 1846/65535/1849 ...: Dry=1, it WOULD be written 1775/1775/1775 and 1846/65535/1849 (Flop=1: the three get-up words are left as they are)`; at the fall **`down: flop: this fall is the game's own (clip ... 'anim:Dammage/Down_Not_Dead#Down_Not_Dead_Get_Down' of 48 frames, 3 event(s), the channel's event queue 00000000; the input mask ........ holds ......1. - found; bits 0x11 are the fall's)`** (both bits 1 and 0x10 SET in the value); `down: lying after ...; the movement's clip word [M+0x8cc] is ... '...'; the input mask ........ holds ...` with bits 0x11 OFF (= the lookup of review3 M1 finds the dword the game sets and clears); `down: the get-up's clip ... is 'anim:Dammage/Down_Not_Dead#Down_Not_Dead_Get_Up' (37 frames, 1 event(s))` = THE THREE CLIPS OF A STOCK DOWN, BY NAME | `NO BELLY FLOP ...` (says which read failed); **an event queue that is NOT 0** on the stock fall = a prone Play hands its clip events to an action: then event 31 of the knock-down's clip would reach 0x77ca60 - do not run G1, tell the track; **`NO INPUT OBJECT`, or a mask value without bits 0x11 at the fall, or with them still set in the `lying after` line** = `kld_mask` does not find the game's dword: do not run G1, tell the track |
| G1 | `Enable=1 Flop=1 Log=2`, no press | `FlopBelly: pair 3 ... was clip .. '...#Hero_Torso_Front' ...: it is clip .. '...#Hero_Torso_Back' now`; `... written 1775/1775/1775 ...`; `YOU ARE DOWN`; **`down: flop: THE KNOCK-DOWN: the fall is clip ... '...#Hero_Torso_Back' of 186 frames ...: he has landed at frame 46 (its event 7), rises from frame 116`**; NO `balance: you lost` line until he is up; `down: flop: he has landed 1.8x s after he went down`; `flop: frame .. (he lies / he rises), speed 0.80` lines climbing by 5 a quarter second; the KNOCK-DOWN line ends `the channel's event queue is 00000000; the input mask ........ holds ...` with bits 0x11 set; `down: flop: the knock-down's clip is through (frame 184.x of 185 ...): the fall's input mask ........: X -> Y (bits 0x11 off), movement state 5 is written`; shoulder `dstate 2->0` within a frame or two (no 1, no 3); **`down: flop: UP after 8.x s: the dive took 1.8x s, lying and rising 7.0 s, 0 press(es) ...; the input mask ........ holds ... (the fall's bits 0x11 are off)`**; THEN THE SCRIPT MAKES HIM WALK, AIM AND FIRE (review3 M1: a `goto` that is reached, the aim button held 1 s, a shot - `[Balance] Log=2` / the ammo count shows it) - all three must work. PICTURES at fall + 1.0 s (in the air / landing), + 3 s (FLAT ON THE BELLY, head forward = picture 1), + 7.5 s (ON ONE KNEE = picture 2) | a fault (dumps to the track); **a NON-ZERO event queue in the `THE KNOCK-DOWN` line = STOP THE RUN SERIES THERE** (review3 S5: event 31 would reach 0x77ca60 with a current action); `THE FALL'S BITS (0x11) ARE SET ON A MAN WHO IS UP` in the UP line, or he stands and cannot walk / aim / fire (the mask: M1); shoulder `dstate 2->1` during it (the game ended the fall: the tick hold did not take); `THE TIME BOUND` / `THE TIME BOUND OF THE WHOLE KNOCK-DOWN` (the frame stood still: no fault of the game, the part gave the fall back - say so); he stays frozen after `movement state 5 is written` (D does not end: shoulder stuck at 2 - then the end by M = 5 is not what was read); his rifle is gone from his hands after it (event 31 acted); he stands up somewhere else than he fell by more than a metre |
| G2 | G1 + `tap C 40` / `wait 60` x 80 from the fall on | the dive is not cut; `UP after` under 4.5 s, presses over 10, `mean speed` over 2 | presses 0 (the button byte does not pulse during the fall: the knock-down then always takes the `FlopBase` time - say so) |
| G3 | G1 five falls or more; then back at the menu | `Hero_Torso_Back` every time; at the menu / the next level `down: flop: 1 pair(s) of the fall slot's list have their own clip number again` or `... pair(s) ... are NOT put back: no player wears that animation set any more ...` (the level's data was gone: review3 S1) | `#Hero_Torso_Front'` in a KNOCK-DOWN line (the pair was not the one the draw reads); with `FlopBelly=0`: count the share of the back (read: one in two) |
| G4 | G1 on stock Subway; G1 + `[Fed] Enable=1 Player=1` with a blast or a death while down | as F5 / F6 of 9.5: nothing written on the stock level; one `DEAD ... WHILE FALLING` line and no `flop:` write after it | a `flop:` write line for a dead man |
| G5 | G1 with the fall taken facing a wall at a metre, and beside a low cover | for the owner's eyes: does the 0.55 m throw stop at the wall; `the game left the fall ... (down state .., movement state 5)` = it took him into the cover ([D+0x20]) - no fault | a fault; through the wall |

For the owner's eyes after G1: is THIS the flop; is 7 s on the floor without presses right (`FlopBase`); should
the forward-falling death kept (`FlopBelly`); is a
knock-down that costs nothing what he wants.

### 10.5 ASSUMED / not done

- ASSUMED: the set's pair list in memory is the file's {condition word, clip number} pairs and can be written (R2's `kld_list` reads the same; 0x7c6750 reads `[pair]` and `[pair+4]`), and nothing but the player's two movements draws from `Hero_Torso_F` (searched by the name's one reader, 0x789b10, and by the NPC table 0x78d9d0, which has not got it); 'thrown forward = onto the belly'; writing `[M+0x8ec]` = 5 while D is 2 ends the state as the game's own 5 does (read: 0x47cd80 tests only M
  at 0x47cf0f; CORRECTED by review3 M1: 0x7107b0 does NOT call 0x88a990 and does NOT take the fall's input mask off -
  the part now takes it off by data, 10.2 point 4); that the dword `kld_mask` finds is the one the four mask tests
  read (the same lookup the game's setter and clearers use: READ; G0 shows it live); 0x773d20 (the call stock makes
  when the fall ends, from 0x640c26 / 0x43c3a8: NOT read) and 0x841db0's 'state 1' notice (0x8ee2e3) are not missed;
  a fall channel left at its last frame is fine at the end (0x8eea90 stops a channel only at M 1 / 4 - the stock
  get-up's channel is not stopped at its end either); a prone Play makes no event queue (G0 prints it); the channel's state 0 / 4 = stopped;
  `[D+0x2b]` pulses during the fall; the clip's root movement is stopped by collision as any movement of his is.
- NOT ESTABLISHED: how it LOOKS (nothing ran; no picture was rendered - the pose reading is pelvis and chest only);
  what cuts an NPC's death clip at its event 8 (0x7b0d30's (7, 8) was not read); who plays `ZFFPlayerMovementDie`'s
  words and to which frame; when an AI heister's `[generic+0x98]` is 2 (the full-body impact); which clip the owner's
  picture 3 is (a thrown body: a ragdoll or the first frames of a Wounded clip - not told apart).
- NOT DONE: a level step `tools/kl_fa_flop.py` (a new slot with ONE pair -> a copy of `Hero_Torso_Back` without event
  31: no event question, his death left alone; a few KB in the `.ANM`, but five maps to build and load) - not written,
  the hook form works on the installed tab; hits that cost while he lies (the game's rule would need the
  fall cut at the landing and a get-up clip: `Get_Up_From_Stomach` matches the belly clip's lying pose exactly, nothing
  matches the back clip's - that is `Flop=2` with `FlopFallSlot=/Damage/Wounded/Running/Torso/Merc_Back`, where R2's
  request two frames before the clip's END would come after he stands: not adapted); shooting from the floor; the
  knock-down by the side the shot came from; the AI's trigger; `Flop=2` is untouched and still as section 9 says.

### 10.6 The third review (re/player_down_review3.md: ACCEPT WITH FIXES) and what was done, 2026-10-11

| point | done |
|---|---|
| M1 the knock-down ends with the fall's input mask on him | DONE, fix (a): 0x61ef90 / 0x787600 / 0x6feb90 read whole; `kld_mask` finds the dword by reads; with the state-5 write bits 0x11 are taken off by data and `[D+0xf0]` zeroed; a refused mask write = no state 5; the dword is logged at the fall (Dry too), at the end (before -> after), at `UP` and in `lying after`; G0 proves the lookup, G1's PASS has the scripted walk + aim + shot. Fix (b) was NOT taken: a press in the frame he lies starts the stock get-up (0x47ce25) |
| M2 no bound before the landing | DONE: one absolute bound for the whole knock-down (game ticks, from the first good channel read, tested before any write); line `THE TIME BOUND OF THE WHOLE KNOCK-DOWN` |
| S1 `FlopBelly`'s put-back through remembered addresses | DONE: each entry keeps the pool and the pair's condition word; a number goes back only when a live ZFFPlayer (the remembered one or one of the 32 places) wears that pool and the pair reads {that word, our number}; else dropped with one line |
| S2 HEAD has the new ini text on R2's code | NOT this track's to do (no commits): said in 10.3 and in the report - the lead commits this `kldown.c` next; no hook from HEAD with `Flop` set until then |
| S3 pose statements | DONE: 10.0 (`Die_Forward` ends chest down; wrong for being a death, not for its pose; `Down_Not_Dead_wounded` stays on the side), 10.1's legend (B / K / s are pelvis readings; the reviewer's full-skeleton frames), the file's head comment |
| S4 the three owner decisions | DONE: 10.2 'THREE DECISIONS FOR THE OWNER', and the report |
| S5 G1's FAIL list: a non-zero event queue | DONE: 10.4 G1 |
| S6 `Flop=1` changed meaning | DONE: note at section 9's head; F1 / F2 of 9.5 say `Flop=2` (F3 .. F7 are 'F2 + ...') |

## 11. The AI heisters' own down, and Dead Men's own (track R4, 2026-10-11 ~17:00)

Owner, after the live flop (run G1_DM03_flop 16:18: `THE KNOCK-DOWN: the fall is clip ... '#Hero_Torso_Back' of 186 frames`,
PASS): *'the belly flop worked but there was the dead men one no? do you not have the animations on the dog days npcs that
are heisting??'*. **Offline; nothing of this section has run in the game.** READ = kl2.exe 0490, each routine named
read whole; FILE = the `.ANM` of Dead Men's `M03_FA_A` and of stock Dog Days F01 / F07 (`tools/kl_anm.py`); LOG = the 899
logs in `<work>\build\klhook\live` + the owner's `KLHook.log`. Scratch: the session's scratchpad `R4/`.

### 11.0 The short answer

- **'The Dead Men one' is the flop he just saw.** Dead Men has no 'down not dead' at all (no such name in
  kaneandlynch.exe or its levels); its knock-down is the **Wounded** family, and its hero slot
  `/Damage/Wounded/Hero_Torso_F` holds the same three pairs as Dog Days' (`Hero_Torso_Back` twice, `Hero_Torso_Front`
  once). **`Hero_Torso_Back` is byte for byte the same clip data in both games** (FILE: 186 frames, 37,228 bytes, sha1
  0737fdfe40..; events 31 at 1, 0 at 39, 7 at 46, 8 at 116; root 66 forward). Dog Days took the family over whole.
  Nothing has to be carried; `Flop=1` already plays Dead Men's.
- **The AI heisters have the down in their set and by the code may go into it - and never do.** 267 of 267 AI heisters
  at health 0 in the logs are dead (177 by an ordinary bullet; 7 of 7 on the stock Subway copy T01, so it is not our
  maps, bots or mesh). WHICH of the game's tests refuses each time is **NOT ESTABLISHED** (11.2): the level-wide
  pause is refuted as the whole cause, and the two candidates that can be systematic sit in a test no key touches.
  `Bots=1` takes away the two refusals data can (f / g). **It is NOT SHOWN that `Bots=1` makes an AI heister go
  down** - live check B1 decides; until it has printed an `IS DOWN` line nothing of this goes into the owner's ini.
- **Their down clip is not the belly flop**: an NPC's down state plays the stock fall onto the side ('the gun one').
- **But the AI heisters DO have the 'shot' animations and play them alive** (11.1a, added in the fix round): the
  run-stumble-fall-and-up clips of his pictures are an NPC's full-body HIT reaction, played when he is hit while a
  task holds his mode `[soldier+0x98]` at 2 - running to a place while shooting, leaning out of corner cover, a close
  attack, firing in the open. That is game behaviour on every map already; no key of ours.

### 11.1 The NPC's down, read whole

| what | where | facts |
|---|---|---|
| when it is asked | soldier's damage routine 0x8473a0 (ZSoldier slot 96) | the new health is written (0x84789d) unless word `[[actor+0x54]+0x3a]` is not 0 (= he takes no damage: 0x8477ae; the word is a set of 'no damage' bits - bit 1 a player's, **bit 0x800 the down's own**, set for 0.1 s by 0x6c75c0 at a down's start; a timed bit is taken off by the mask `[+0x40]` at the tick `[+0x3c]`, 0x638e2e); at health 0, with that word 0: slot 51 (0x847968) = 0x688190 = no for a dog (`[[soldier+0x6d8]]` = ESoldierStyle 6), else **0x70e0e0**(soldier, hit record, 0); yes -> return, he lives |
| 0x70e0e0, the refusals in order | | **a.** `[actor+0x64c]` set (down already: actor slot 405 = 0x410a30), or ZWounded `[[soldier+0x4b4]+8]` not 0 / 4. **b.** 0x70f330 on his ZDownNotDeadNPC `[soldier+0x4b8]`, in order: 0x619d10 (node flag 0x1000 and bone 2 within 20 of `[actor+0x46c]`); `[actor+0x774]` (somebody holds him); 0x75a2e0 (he sits in a seat - three parts: `[actor+0x88c]` and `[seat+0x18]` not 0 and `[seat+0x40]` == 0); 0x4a05f0 (the task at `[soldier+0xa4]` has state `+8` not 0 / 4 - that object is his **ZHitAnimTask**, vtable 0xbcf87c by RTTI, made by the soldier's constructor at 0x7cfc79: **no down while a hit animation plays**); 0x86a150 / 0x86f0c0 (the object he is attached to, `[actor+0x5b4]`, is a ZLNKOBJ - type pair 0x153a898 - AND a ZHavokLnkObj - type pair 0x168cddc -, each by its vtable slot 12); then **16 probes of 100 units around him on the navigation mesh** (0x70f3d1 .. 0x70f437, PF4::ZData slot 41 = 0x4dd5f0): **all 16 must pass** = one metre of mesh free in every direction. **c.** `[actor+0x5cb]` set and he is not the buddy: **he was down once** (0x70e13f; set by the down's script at its START, 0x5f4b56; cleared nowhere). **d.** the hit has an attacker, flag `[rec+0x30]` and kind `[rec+8]` not 1, from NEARER than `[T+0x5c]` = **1500**: `[rec+0x30]` is 'the bone's body part is 2 or 3' (0x61a9f0: the head - tools/kl_impact.py) - **a head hit from within 15 m kills**. **e.** damage `[rec+0x28]` **more than 1,000** (0x70e1c7 jumps on C0 only: exactly 1,000 passes; 500,000 for the buddy). **f.** modifier `[soldier+0x124]`: 1 = yes at once; 2 = no. **g.** else (0; 0x70e206 .. 0x70e29c, the constant 0xb39f70 is -1024.0 so the compares read 'now >= last + n s'): `[gamedata+0x4d04]` = the tick of the level's last NPC down (written by every non-buddy NPC's down start 0x7eaab9 - a policeman's too; 0 at a level's load, and 0 jumps past the first test, 0x70e22c). Last down less than `[T+0x54]` = **5 s** ago: NO. Less than `[T+0x58]` = **20 s** ago: yes only when a random number is under `[actor+0x804]` / 100. Later: **YES, no draw** (0x70e273) |
| the buddy | 0x6fd7c0 | `[gamedata+0x4cf0] == actor`: the campaign's one. Nobody in Arcade (section 9.1) |
| `[actor+0x804]` | ZFFActor's property records (info 0xd115a0; a record's offset is 4 under the actor's: field 10 = `+0x7f0`, field 15 = `+0x804`) | **level field 15 of the ZFFActor: 50.0 on all seven AI heisters of stock F01 / F07 and of ours** (census `R4/census.py`) |
| the modifier | `[soldier+0x124]` | 0 from the constructor (0x7cfb3b); ONE writer: 0x803530, the SquadModifierBehaviour's field 13 (`EDownNotDeadModifier`: 1 force -> 1, 2 prevent -> 2, 3 default -> 0; its debug strings 'SquadModifier: SetDownNotDeadModifier (force DND)' ..). **No stock FA level and none of ours sets it** (F07: 45 modifiers, F01 30, the bank 28: all `eDND_NotSet`) |
| the start | 0x70e29e .. 0x70e2f6 | 0x4860e0 (who floored him), the goal pushed (0x6cabf0, 0x30dac), `[actor+0x64c]` = 1, the 0.1 s 'no damage' bit |
| slot 1 = 0x7ea990 | | the tick he lies until `[dnd+0x14]` = now + `[T+0x4c]` .. `[T+0x50]` = **1.5 .. 3.0 s** by a random number (3 .. 9 s for the buddy); the level's 'last down' tick; **health raised to 25 % of his maximum if he has less** |
| slot 2 = 0x5f4ac0, the script | | 0x70f330 again; `[actor+0x5cb]` = 1; the state `DownNotDead` of the graph 0x730be0; clears the 0x800 bit (0x5f4bb5); **while he lies he fires from the floor** at his target (`[soldier+0xb0]`, the soldier's own slots +0x1c4 / +0x164 - `[actor+0x77c]`, not his weapon's) and **takes hits in full** - a second health 0 kills (a); then **health = 75 % of his maximum** (0x5f4d23), actor state 1, the state `Stand`; **in Arcade, for team Ally / Mercenary: `[soldier+0x4fc]` = 1** (0x5f4dd8 .. 0x5f4dfc) |
| **what that byte does to his route** | 0x686c77 (re-read; re/boardall_review_code.md, re/boardall_review_exe.md) | `[soldier+0x4fc]` makes his squad's ZDefendBehaviourRout count him as **arrived**: the Defend step his chain is WAITING in ends and its NEXT fires although he did not reach the place. His next order puts the byte back (0x760efe). **So every down can skip one step of his route - a hold, a loot stop, a Retomoto gate step** - with `BotsMax=2` twice a bot a round. The game's own write, not the hook's; whether he still loots / boards after it is a live question (11.4 B1, B6) |
| a human who floors him | 0x8477c1 .. 0x847886; rules slot 131 = **0x7cc270** (read whole), slot 128 = 0x741320 | at health 0 with a PLAYER attacker the damage routine calls rules slot 131 and, for a police player, slot 128 **before** the down is asked. Slot 131: for a valid record index in use, the attacker's word `[score+0x1b8+2*index]` += word `[T+0x700]` (when rules slot 107 says yes for him) or `[T+0x6fc]`. **So a bot the human floors is counted for him at the floor and again at the real death.** What that word shows on the score page was not read; the hook prints it in the `IS DOWN` line. Slot 128 is `ret 0x10` for Heist (re/fed_kit.md) |
| his clips | section 9.1 | `/Damage/Down_Not_Dead/Down_Not_Dead_Get_Down` (48 frames) and its `_RUN` / `_Walk` aliases, `_Crouch`, the loop, `Get_Up` (37 frames): the stock human's own fall, onto his side. NOT a Wounded clip |

### 11.1a The AI heisters' own 'shot' clips: when a living one plays the full-body fall (fix round; READ in part)

The owner's pictures (flat on the belly, up over a knee) on an NPC are either his DEATH (ZWounded) or a full-body
HIT he lives through. The second: ZSoldier's slot 22 (0x531af0) is a plain jump to ZGeneric's 0x4aba20, which plays
`/Damage/Impact/FB/<stance>/...` (the run-stumble-fall-and-up clips of section 10 / re/anim_shot.md) only when
**`[soldier+0x98]` is 2** (0x4abaf6) and the clip's root movement has room. That dword is 1 from the soldier's
constructor (0x7cfae9). Its writers, found by displacement and each named by its vtable (the routines were NOT read
whole - only the writes and the lines around them):

| who | writes |
|---|---|
| `ZRunToPosShootingTask` | slot 1 (0x8b7940, the start): **2**; its script 0x4a7e60: 0 / 1 / 2 by phase; slot 3 (0x558d90, the end): 1 |
| `ZAttackFromCornerCover` | script 0x45fca0: **2** while he is out of the corner (11 writes), 0 while behind it; slot 3 (0x4935c0): 1 |
| `ZCloseAttackTactic` | slot 2 (0x6764c0): 1, then **2**; slot 3 (0x4ac050): 1 |
| `ZFireWeaponTask` | script 0x7c02b0 at 0x7c0411: **2** after a loop of 20 tries succeeded (what it tries was not read) |
| `ZCloseCombat` | slot 3 (0x66e1b0): 1 |

So an AI heister plays the full-body fall-and-get-up **alive, with the stock game's own rule, on our maps too**, when
a hit lands while he runs to a place shooting, leans out of a corner, closes in or fires in the open - and the short
upper-body flinch otherwise (mode 0 / 1: in cover, idle). No level field and no key is in that path. NOT ESTABLISHED:
how often our bots are in those tasks (their routes are Defend orders: the loot / board walks may never be a
'run to position shooting'), and which of the clips each of his three pictures is (re/anim_shot.md has the sheets).
A multiplayer human plays `Hero_Torso_F` when he dies.

### 11.2 Why none goes down: what is known (corrected in the fix round - review M1)

Read: no test of the team, of Arcade, of the squad's kind (`eHeistOnly`) in the path; level data the same as stock.

- **g is refuted as the whole cause.** By 0x70e206 .. 0x70e29c a first down after 20 quiet seconds is an
  unconditional YES; only 5 .. 20 s after another NPC's down is the 50 % draw, and under 5 s a no. The first heister
  to reach health 0 after 20 quiet seconds goes down for certain if a .. e pass. 0 of 177 (and 7 of 7 on T01) cannot
  come from g.
- **Two candidates that CAN be systematic, both inside b, both untouched by `BotsForce`, NEITHER PROVEN:**
  - the **ZHitAnimTask** (`[soldier+0xa4]`): the down is refused while a hit animation plays, and a heister dies under
    250 .. 550 small hits at about 3 a second (whether the killing hit's own animation is started before the down is
    asked was not read);
  - the **16 mesh probes**: one metre of mesh free in every direction, where the bots stand at cover boxes, walls and
    in corridors.
- d (the head from within 15 m) and e (the 60 left-behind kills and the point-blank steps: 86 of the 267 lost 100 or
  more in one step) explain a part, not all.
- **What the hook's `DIED` line can and cannot say.** The game asks a .. e BEFORE f / g; d, e and three of b's tests
  (bone 2, the attachment's class, the probes) cannot be read from the tick. So the line names a readable a / b / c
  if one stood one pass before, and otherwise says **'g MAY have refused ... a .. e are not excluded'** whenever a
  policeman fell within 5 / 20 s - in a fire fight nearly always. **A count of B0's reasons does not answer the
  question.** The run that decides is **B1 (the modifier forced)**: there f / g are out, and a death that says
  'NOT f / g (the modifier was 1 = force)' is b / d / e; its place (printed) can be laid on the mesh offline, and
  the ZHitAnimTask state is printed for one pass before and for now.

### 11.3 `[Down] Bots=1` (`kld_bots` in `klhook/kldown.c`)

Its own switch (works with `Enable=0`). Arcade, a level that is not stock, session state 0x19, AI crew records in play
(mask 1 of `+0x79`; a traitor too), the actor a ZFFActor whose `[+0x77c]` is its ZSoldier (vtable 0xbd0954,
`[soldier+0x40]` the actor). Game thread only. No call, no patch.

| key | default | what is written |
|---|---|---|
| `Bots` | 0 | the part |
| `BotsDry` | 0 | 1 = nothing is written (also with `Dry=1`); the log lines stay |
| `BotsForce` | 1 | `[soldier+0x124]` 0 -> 1 (never over a 2 a level set); back to 0 when the round is over / the record is gone. Takes **f / g** away; a .. e stay the game's |
| `BotsMax` | 2 (the task's GUESS; the game's own is 1) | byte `[actor+0x5cb]` 1 -> 0 once he is up again, while he has downs left |
| `BotsLie` | 0 = the game's 1.5 .. 3.0 s | `[dnd+0x14]` = the down's first tick + s (0.5 .. 15), written until it stands (slot 1 writes its own a frame later) |
| `BotsFree` | 0.75 (the stock human's free fall) | bit 0x800 of `[[actor+0x54]+0x3a]` held set for s seconds of a down, then taken off (never another bit). **While it stands NOTHING kills him**: the routine writes no health (0x8477ae) and skips the death (0x847945) - the left-behind 1,000,000 and a point-blank step too. So the bit is **never held at vehicle state 5 or more** (taken off in the same pass, a `Log=2` line) nor on a record out of play. Of the word's 20 readers 4 are read (0x8477ae, 0x847945, 0x828735, 0x4d83bb); the other 16 are listed in re/player_down_review4.md S2. For it: the game itself holds this bit `[T+0x48]` seconds on the buddy (0x5f4d9d). **First live run: `BotsFree=0`** |
| `BotsUpPct` | 0 = the game's 75 | his health `[[actor+0x5fc]+4]` when he is up, per cent of the maximum that stands. `klgrudge.c` (`[Bots] CrewHealth` / `BackstabHealth`) writes the same object, but only when it changes the MAXIMUM, keeping his share: with both, the per cent is of klgrudge's maximum, and neither undoes the other |
| `BotsNear` | -1 = not written | `[T+0x5c]`; 0 = a head hit from near floors too - for EVERY NPC, the police as well; put back |

**Against the human's rule** (the owner: 'so the ai heisters are 1:1 with you'):

| | the human (`Flop=1`) | an AI heister (`Bots=1`) |
|---|---|---|
| trigger | under a burst at 40 % health or less, the hit swallowed | the hit that takes his last health, in place of dying |
| what he has on the floor | at least `DownHealth` | 25 % of his maximum |
| free of damage | the whole knock-down | `BotsFree` seconds (0.75) |
| on the floor | 7.0 s with no press, about 2.7 s mashing; cannot shoot | 1.5 .. 3.0 s (`BotsLie`); FIRES from the floor |
| up with | what he had (`FlopUpPct`) | 75 % (`BotsUpPct`) |
| how often | every 10 s (`Cooldown`) | once a life (`BotsMax` 2) |
| the clip | the belly flop | the stock fall onto his side |

**Two decisions for the owner.** (1) With the defaults a bot is far harder to kill: 252 + 189 + 189 health a round
and 25 % given at each fall. `BotsMax=1 BotsUpPct=25` is the lean form (one extra quarter of health, once). (2) The
bots' clip: the belly flop on them needs the NPC state graph's `DownNotDead` words (0x730be0, shared with the
police: every NPC would flop) - not read whole, not built.

**klescort.c (not edited: another track's file).** A bot that lies takes no order by `kle_bot`'s own `[actor+0x576]`
test only if the down changes that byte - not read. The patch, after the `b576` line of `kle_bot`:

    { BYTE dn = 0; if (klh_rd(actor + 0x64c, &dn, 1) && dn) { strcpy(why, "it is down, not dead ([actor+0x64c] set): no order until it is up"); kle_later = 1; return 0; } }

(`kle_later = 1`: an escort is not dropped for it.) BoardAll's 'held' test (15 s without moving 1 m or earning) is not
met by a down of 1.5 .. 3 s; `BotsLie` is bounded at 15 for that reason - keep it under 10. FollowOut's stage byte
on a lying bot is harmless (he boards when he is up). A bot that goes down beside the waiting vehicle misses it.
The patch is needed only if `[actor+0x576]` stays 1 during a down (not read).

Compile check, fix round (`git archive HEAD klhook` at 431be33 + this kldown.c, sha1
271b8b48981f7bee55d77594140e2a57a344031d, in `G:\kl_scratch\R4fix\src`; HEAD wires kldown.c, no line of klhook.c
changed): 'built G:\kl_scratch\R4fix\test\dinput8.dll (TEST)' sha1 5dccf85fb02afe037caf53b4d85f7b063fe8d3fc, 'built
G:\kl_scratch\R4fix\ship\dinput8.dll (SHIP)' sha1 0223622fa97dd3407a91678ce79a58b76b11566b; the one warning
is klhud.c(285) C4101. Compile only. (First round: 98564f7 + fbf5ca54.., TEST 8e8b60b4.., SHIP 73288206..)

### 11.4 Live checks (the lead; the bank DM03, the owner's balance, `[Bots] Log=2`; the player idle or scripted)

**Nothing of `Bots` goes into the owner's ini, and he is not told 'the bots go down now', before B1 has shown an
`IS DOWN` line and B6 has run.** B0 is an input check, not the answer to 'why' (11.2).

| run | `[Down]` keys | PASS | FAIL |
|---|---|---|---|
| B0 | `Bots=1 BotsDry=1 Log=1` | `down: bots: on (Dry: ...`; the round line `Enable=0, Bots=1, BotsDry=1 - only the AI heisters' part runs this round, and it only logs`; per bot `down: bots: record N (actor .., soldier ..): health 252.0 of 252.0, modifier [soldier+0x124] 0 ..., his chance [actor+0x804] 50 %, was down once [actor+0x5cb] 0; the level's pauses [T+0x54] 5.0 s / [T+0x58] 20.0 s, head-hit distance [T+0x5c] 1500`; at every death beside klbot's `lost .. (0.0 of 252.0)`: `down: bots: record N DIED at health 0 without going down at (x, y, z) ... ONE PASS BEFORE: ... ZHitAnimTask [soldier+0xa4] state S ... NOW: ... -> <text>`. **Use of it:** (1) the inputs read (chance 50, pauses 5 / 20); (2) how many deaths have ZHitAnimTask state not 0 / 4 one pass before or now (`b: HIS ZHitAnimTask RAN`) - that candidate can show here; (3) any `NOT g (no NPC went down in the last ...)` line = a death g cannot explain; (4) the places, to lay on the mesh offline. Do NOT count the `g MAY have refused` lines as a cause | no `record N (actor` line (the soldier is not at `[actor+0x77c]`); a chance that is not 50 or pauses that are not 5 / 20 (the offsets are another block: say so); `IS DOWN` in a dry run = the game did it by itself (then say how often) |
| B1 **(the run that decides)** | `Bots=1 Log=2 BotsMax=1 BotsFree=0` (no shield, one down: only the modifier is written) | `the modifier [soldier+0x124] 0 -> 1` seven times; **`down: bots: record N IS DOWN, NOT DEAD (1 of 1) at (..): health .. of 252.0 ..; he lies until .. = 1.5 .. 3.0 s from now`**; klbot shows no `dead` for him; `IS UP after 3 .. 5 s at (..): health 189.0 of 252.0 ..., heist stage S; [soldier+0x4fc] 1`; **after `IS UP` the same record's klbot lines still go `heist stage 1 -> 2 -> 3` and `aboard`** (M2: the skipped Defend step must not strand him or send him off without loot); a second health 0 = dead (`DIED at health 0 ... c: HE WAS DOWN ONCE`); back at the menu no fault. A PICTURE of a bot on the floor (he lies on his side and fires) | a fault; **no `IS DOWN` at all and the deaths say `NOT f / g (the modifier was 1 = force)`** = `Bots=1` does not do it: the refusal is b / d / e - report the ZHitAnimTask states and the places, then B3 for d; a bot that stays down for good (`IS UP` never comes); a bot that is up and then never changes stage while the others board; `WENT DOWN AND DIED ... between two passes` is a down, not a refusal |
| B2 | B1 + `BotsMax=2 BotsLie=4 BotsFree=4` (the shield, first time) | `(1 of 2)` then `(2 of 2)` for one record; `he lies until tick .. (BotsLie=4.0 ..)`; NO `bots: record N (bot): lost` line of klbot within 4 s of his `IS DOWN`; `IS UP after 5 .. 7 s`; after each `IS UP` his stage goes on and he boards; if the vehicle drives out while one lies: `the 'no damage' bit is taken off (the vehicle drives out ...)` and he is killed like the others left behind | losses inside the free time (the bit does not hold: say so); `DIED ON THE FLOOR` inside it; a bot alive in play after the vehicle has left with the human; any fault (16 readers of the word are unread) |
| B3 | B1 + `BotsNear=0` (only if B1 points at d) | `BotsNear: [T+0x5c] 1500 -> 0`; more `IS DOWN`; at the menu `[T+0x5c] is 1500 again` | - |
| B4 | B1 with `[Bots] Escort=1 BoardAll=1 FollowOut=1`, the scripted human to the vehicle | no `escort:` / `board:` order line for a record between its `IS DOWN` and `IS UP` (after the klescort patch); the escort is not dropped | an order to a lying bot followed by a fault |
| B5 | B1 on stock Subway | `nothing is written here`; no `bots:` write line | any |
| B6 | B1's keys on **DM09 Retomoto** (the gates build), idle player, before any owner setting | every bot that had an `IS UP` still passes the gates in order (the escort's route-place lines / klbot stages) and the crew comes down the tower as in run G2; no bot left standing on a floor whose gate has opened | a bot that is up and stays behind a gate, or walks on past a hold alone (the skipped Defend step) |
| B7 | B1 with the scripted human SHOOTING a bot to the floor (`[Fed] Player=1` off, then on after a death) | `IS DOWN ... your word [score+0x1b8] N (one pass before M)`: say whether N > M, and what the score page shows for a bot floored and then killed (S5: a kill credited twice?) | - |

### 11.5 Dead Men's own (FILE: `M03_FA_A` set `PlayerCharacter`, against stock F07; `R4/dmclips.py`, `R4/same.py`)

Dead Men floors a hero by the Wounded family and gets him up by a mate's adrenaline (`ZWoundedDisplay`,
`ZWoundedFilter`, 'Adrenalin' strings in kaneandlynch.exe; how its Fragile Alliance uses it was NOT read in that exe).

| Dead Men slot | clip | frames | in Dog Days |
|---|---|---|---|
| `/Damage/Wounded/Hero_Torso_F` | `Hero_Torso_Back` x 2, `Hero_Torso_Front` | 186 / 255 | **the same data, byte for byte; the same three pairs** |
| `/Movement/Rise/Rise_From_Stomach` | `Heal_Wounded#Get_Up_From_Stomach` | 202 | the same data |
| `/Movement/Rise/Rise_From_Back` | `Wounded#Hero_Die_End` | 67 | the same data |
| `/Special_moves/Heal_wounded` (+ `_Low`) | `Heal_Wounded_01` (the mate's injection) | 55 | the same frames, keyed again; plus Dog Days' own `Heal_Down_no_dead` (19) |
| `/Damage/Wounded/Crawl` | `Crawl_Forward_01 .. 04` (0.3 .. 1.4 m a cycle) | 66 / 58 / 133 / 106 | the same frames, keyed again |
| `/Damage/Wounded/Dragged` / `Dragging` | a mate drags the wounded man, 1.66 m a cycle | 17 | the same frames, keyed again |
| `/Damage/Wounded/Stand_To_Crouch_Wounded`, `Crouch_To_..` | sinks to the floor on the spot | 115 | the same data |
| `/Movement/Stand/Wounded_M01`, `/Movement/Walk/Forward_Wounded` | the limp | 301 / 135 | the same frames |
| `/Movement/Run/Forward_Wounded` | `Run#Forward_Wounded_M01`, a wounded run | 37 | **Dead Men only** (9 KB; the one clip `kl_fa_climb`'s merge would have to carry) |
| `/Damage/Death/Die_Forward` / `Backwards` / `On_Spot` | 46 / 25 / 61 frames | | Dog Days has other clips under these names (50 / 61 / 40) |

For the owner, two lines each:
- **The knock-down** - thrown forward onto the belly, lies, pushes up over one knee, stands: it is `Flop=1`, live since
  16:18. Dead Men's and Dog Days' are one clip.
- **Dead Men's long form** - the same fall, but he STAYS down (and can crawl on his belly) until he is got up, then the
  slow 8 s rise from the stomach: every clip is in the Dog Days levels already; it needs the hook to cut the fall at
  the landing and hold him (10.5: not adapted). No level build.
- **The wounded run** - the only Dead Men-only clip: a limping run for a hurt man. A merge of 9 KB per map and a
  place to play it; not asked for.

### 11.6 ASSUMED / not done

- ASSUMED: writing `[soldier+0x124]` from the tick is taken as the SquadModifier's own write is (one reader, 0x70e1e8);
  a 0x800 bit held in the 'no damage' word for seconds harms none of the word's other readers; `[dnd+0x14]` has no
  reader but the script's two compares; clearing `[actor+0x5cb]` after the down has no other meaning (ONE reader by
  displacement: 0x70e142; writers 0x5f4b56, the constructor 0x830445 and the stream routine 0x6ccccf, both 0); a record's actor that lives again in the next round is the same
  object (then its count starts anew).
- NOT ESTABLISHED: which test refuses (11.2) - and so **whether `Bots=1` makes any AI heister go down**; whether the
  killing hit's own hit animation is started before the down is asked; what the police do to a lying bot (the target
  choice was not read); what his own squad chain does while he lies (his Defend step waits: ASSUMED) and after the
  game's `[soldier+0x4fc]` = 1 at the get-up (one step of his route may be skipped: 11.1); `[actor+0x576]` during a
  down; what the word `[score+0x1b8+2*index]` shows (rules slot 131 adds to it at the floor and at the death); 16 of
  the 20 readers of the 'no damage' word; how often our bots are in a task that sets `[soldier+0x98]` = 2 (11.1a).
- NOT RE-READ: 0x6fd7c0, 0x4860e0, 0x6cabf0, the state graph 0x730be0, rules slot 16, kaneandlynch.exe.
- NOT DONE: `tools/kl_fa_bots_down.py` - the level form is one SquadModifierBehaviour with field 13 =
  `eDND_ForceDownNotDead` at the START of each bot squad's chain; it gives `BotsForce` only, on five maps to build and
  load, where the hook's one dword does it on the installed tab: not written. The belly flop on bots. The AI's trigger
  on the human. Dead Men's long form. kaneandlynch.exe's own wounded state.

### 11.7 The review (re/player_down_review4.md: ACCEPT WITH FIXES) and what was done, 2026-10-11 fix round

| point | done |
|---|---|
| M1 the 'why' is open, g refuted, B0's count misleads | 0x70e206 .. 0x70e29c re-read: holds. 11.0 / 11.2 / the code comment rewritten (g refuted as the whole cause; the ZHitAnimTask and the 16 probes named as unproven candidates in b). The `DIED` line: reasons in the game's order a, b, c, f, g; `g MAY have refused ... a .. e are not excluded`; the ZHitAnimTask named, its state one pass before AND now; the bot's place. 11.4: B1 decides, B0 is an input check |
| M2 `[soldier+0x4fc]` = 1 at the get-up | 0x5f4dfc and 0x686c77 re-read: holds. Row in 11.1, the code comment, the ini; `IS UP` prints the byte, the stage and the place; B1 / B2 PASS now ask for stage 1 -> 2 -> 3 and `aboard` after `IS UP`; new run B6 on DM09 |
| S1 B1 stacks unproven writes | B1 = `BotsMax=1 BotsFree=0`; the shield first in B2. The default of `BotsFree` stays 0.75 (the key is off with `Bots=0`; the ini says the first run goes with 0) |
| S2 `BotsFree` swallows every kill | the bit is not set at vehicle state >= 5 and is taken off in the same pass there and on a record out of play; the ini's 'BotsLie + 2' advice is gone; the cost and the 16 unread readers are said |
| S3 a death on the floor seen in one pass | new line `WENT DOWN AND DIED ON THE FLOOR between two passes` (counted as a down); every death line prints the down byte now |
| S4 b read short | the seat test's three parts are read and tested (`[seat+0x18]`, `[seat+0x40]`); `[actor+0x5b4]` and its vtable are in the snapshot and the line (its class cannot be asked from the tick: the game calls vtable slot 12) |
| S5 a human who floors a bot | rules slot 131 = 0x7cc270 read whole (row in 11.1): the attacker's score word is added to at the floor and again at the death. Not prevented (it is the game's call before the down is asked); `IS DOWN` prints the word now and one pass before; run B7 |
| S6 the owner's question | 11.1a: who writes `[soldier+0x98]` = 2 - four tasks, by displacement and vtable, the routines not read whole. The answer to him: the bots have the shot clips and the game plays them on a living bot in those tasks |
| S7 small | e 'more than 1,000'; the round line under `Enable=0`; the slots are the soldier's; klgrudge / `BotsUpPct` said in the key table |
