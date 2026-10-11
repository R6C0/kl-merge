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
| F1 | `Enable=1 Dry=1 Flop=1 Log=2` | D1's | `down: flop: Flop=1 - THE BELLY FLOP ...` at start; in the round `down: flop: the fall /Damage/Death/Die_Forward = slot 1780, clip 1 of 1: ... 'anim:Dammage/Die#Die_Forward', 50 frames (1.96 s ...), 0 event(s)`, `down: flop: the get-up /Movement/Rise/Rise_From_Stomach = slot 1755, ... 'anim:Special_Moves/Heal_Wounded#Get_Up_From_Stomach', 202 frames`, **`down: flop: the prone movement ........ holds fall 1847/65535/1850 get-up 1846/65535/1849 ...: Dry=1, it WOULD be written 1780/1780/1780 and 1755/1755/1755`**; at the fall `down: flop: this fall is the game's own (clip ... 'anim:Dammage/Down_Not_Dead#Down_Not_Dead_Get_Down' of 48 frames): Dry=1, nothing was written` | `NO BELLY FLOP on this body: ...` (says which read failed); **`NO BELLY FLOP: word k of the prone movement ... holds n, and <name> is slot m`** = the part's own test of the six words failed (they are not where they were read, or `klq_slot`'s table is not the one the filler's 0x770ba0 searches: ASSUMED the same); no `holds` line and no `NO BELLY FLOP` line = M was not found among his movements (`+0x630`) |
| F2 | `Enable=1 Flop=1 Log=2 DownHealth=200 FlopTake=0.25 FlopUpPct=75` | D2's, no press | `... holds ...: written 1780/1780/1780 and 1755/1755/1755`; `YOU ARE DOWN`; **`down: flop: THE BELLY FLOP: the fall is clip ... 'anim:Dammage/Die#Die_Forward' of 50 frames (1.96 s)`**; NO `balance: you lost` line for about 1.9 s after it; `down: flop: the dive is over (1.9x s, n tick(s) left): the get-up is asked for`; shoulder `dstate 2->3` (no `2->1`); `down: GETTING UP ...: clip ... of 201 frames, the game's speed 1.00, over at frame 201.0, ... it is played at THE FLOP'S FlopBase 1.50`; `get-up: frame ..` lines climbing by about 9.4 a quarter second; `UP ... the get-up took 5.3 .. 5.5 s`; `down: flop: N health was given back`, `down: flop: up with 301.1 of 401.5 health`; a picture during the dive and one in the get-up: **face down** | a fault (dumps to the track); `this fall is the game's own ... the slot ids were not in place`; `he lies (...)` every 0.3 s without `GETTING UP` (the byte is not taken); `GETTING UP at the game's own speed` / `the end tick does not fit the clip`; `DEAD WHILE ...` (then raise `DownHealth`, lower `FlopTake`); he stands up somewhere else than he fell (root motion: 88 + 126 forward is right) |
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
