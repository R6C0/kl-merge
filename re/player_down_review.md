# Review of track R - the player's down mechanic (`klhook/kldown.c`, `re/player_down.md`), 2026-10-11

Adversarial review, offline. Nothing was run in the game; the worker's files were not changed.
Method: every address the hook rests on re-read in kl2.exe (capstone, `debug/dasm.py`), `kldown.c` read line by line,
the owner's `KLHook.log` re-counted, the compile repeated in `G:\kl_scratch\R_review`.

## Verdict: ACCEPT WITH FIXES

One MUST (a bound on the end tick), then it may be wired in switched off and run `Dry=1` first. The reading holds: I
could refute no address the code depends on. The part is data writes only, off by default, gated to Arcade on a
non-stock level and a non-police player, on the game thread only.

## What was re-read and holds

| claim | evidence (re-read) |
|---|---|
| D = `[player+0x2948]`, `[D+4]` 0 / 2 / 1 / 3, `[D+8]` bit 0 | 0x47cd80 whole; 0x8c8150 writes `[D+4]`; 0x88a9a0 / 0x88a9a3 clear both; 0x76a7e9 sets 2; 0x8ee2d0 sets 1 |
| the get-up: 0x47cd80 -> 0x7180b0 -> 0x6373e0 -> 0x478270(M, 4, fast) | 0x47ce3d .. 0x47cefe; 0x6373e0 calls 0x478270 only when `[M+0x8ec]` == 2 |
| state 4: speed 1.0 or 2.5, Play = player vtable +0x200 = 0x4da1d0, `[M+0x8d0]` = its result, `[M+0x8d8]` = tick, `[M+0x8dc]` = tick + (frames - 1) / 25 / speed x 1024, `[M+0x8e0]` the same for event 2 or a copy | 0x4782a3 .. 0x4783d5; constants 0xb89a20 = 2.5, 0xb5bbb0 = 25.0, 0xb39f70 = -1024.0, 0xb17340 = 0.0; `[0xbb45f4+0x200]` = 0x4da1d0 |
| the channel: `[player+0x70] + 0x1c + 0x38 i`; +0 clip, +4 frame, +0xc last frame, +0x10 = speed x 25, +0x14 flags (1 / 3 play, 4 ended) | 0x4da553 .. 0x4da5b8; Play returns `chans + 0x38 i + 0x1c` (0x4da6f7); the update 0x50af22 .. 0x50af32 does frame += dt x `[+0x2c]` |
| the end: tick >= `[M+0x8dc]` -> 5; the stick from `[M+0x8e0]` | 0x640c35 .. 0x640c60; 0x69a440 whole (tick > `[M+0x8e0]` when that is not after the end, else start + part of the length; needs `[D+0x20]` == 0), 0x8ee550 (0.2) |
| `[D+0x2b]` is the game's own button, written while `[D+8]` bit 0 | 0x84dda0 whole; 0x50a8f0 kind 5 (jump table 0x50a968 entry 5 = 0x50a927) reads it |
| the trigger and the six floats | 0x8da3b0 whole; 0x49aac0 (`+0x274`, `+0x26c`, window of 20); 0x76a74e .. 0x76a7d4 (`+0x25c`, `+0x264` in Arcade); constructor values 80 / 20 / 10 / 40 / 1 / 1 / 20 / 6 / 4 / 20 at `+0x25c .. +0x280` |
| the six offsets have no other meaning | every code load of `[0x168d7c0]` followed within 0x40 bytes by a `+0x25c .. +0x280` access: only 0x76a75b / 0x76a771, 0x58341e / 0x76a7c0, 0x76a7ce, 0x8da442, 0x49aafa, 0x4495c2 / 0x49aadb / 0x86d6ab, 0x86d6a4, 0x4495bc. (0x46903b and 0x484019 .. use the same displacements on a weapon-data object, not on T.) |
| vtables | RTTI: 0xbb5d64 = `ZFFPlayerMovementProne` (primary: stamped at 0x4d8453 / 0x5bd572), 0xbb45f4 = `ZFFPlayer` |
| the AI side's thresholds | 0x70e0e0 whole: 1,000, or 1,000 + 0x79d38 = 500,000 for a 0x6fd7c0 actor; `[soldier+0x124]` 1 / 2; `[T+0x54]`, `[T+0x58]`, `[actor+0x804]` / 100 |
| the tick runs once a frame | the main loop's two `SteamAPI_RunCallbacks` sites (0x87a9e6, 0x87aa7c) are alternative branches, each followed by `ret` |
| gates | `klr_arcade` (`[session+0x5c]` == 4, sub-mode not 2 / 3, a `ZGameRulesHeist`), `klb_level` (0 with the Steam guard off, on a stock or unknown archive), police byte `[player+0x2723]` as klbalance.c / klfed.c use it |
| the mash table | re-simulated (120 frames a second, 20-frame clip): 1.6 / 1.32 / 1.02 / 0.85 / 0.67 s at 0 / 2 / 4 / 6 / 10 presses a second; Base 0.25: 3.21 / 2.17 / 1.29 / 1.02 / 0.76 s |
| compile | `git archive HEAD klhook` + `kldown.c` + the worker's three lines (his `klhook.c` differs from HEAD in exactly those three): TEST `built G:\kl_scratch\R_review\test\dinput8.dll (TEST)`, SHIP `built G:\kl_scratch\R_review\ship\dinput8.dll (SHIP)`; the only warning is klhud.c(188) C4101, none from kldown.c. My sha1s (d0860117.. / 240b5768..) differ from his: the build stamps the time, the hashes are per build |
| rules | `git status`: of track R only `klhook/kldown.c` (new), `re/player_down.md` (new) and the `[Down]` section appended at the end of `klhook/KLHook.ini` (`Enable=0`, every other key commented out). The other changed files carry nothing of this track. No commit. |

## MUST

**M1. The hook takes away the game's time bound on the get-up; put one back.**
Stock ends state 4 at a tick fixed when the clip starts (0x478368), whatever the clip then does. The hook rewrites
`[M+0x8dc]` every frame as `tick + frames left / speed`, from the channel's frame. If the frame does not advance
while the game tick does, the end tick slides ahead forever and `[D+4]` stays 3: he lies there and cannot act.
The frame does not advance when:
- the player's animation update is skipped: ZPlayer's frame 0x74efc0 has three gates (byte `[player+0x7a4]`, byte
  `[player+0x430]` clear, node flag 0x800; re/climb.md, 'who moves him while a clip plays');
- the channel carries flag 0x100000 (0x50af15 .. 0x50af20 jumps over the advance).
Neither was shown to happen during a get-up, and neither was shown not to (a vehicle boarding, the Retomoto join and
a round end while he gets up are exactly what section 4.4 of the note leaves 'ASSUMED harmless').
Fix: on the first frame keep `cap = tick + endf / (Base x 25) x 1024` plus a margin (say 0.25 s) and never write an
end tick after it (`if (ne > cap) ne = cap;`, the same for `nv`). The slowest get-up then is the Base one, as the
table says, and the state always ends. Log one line when the cap, not the clip, ended it.

## SHOULD

**S1. Adopt the channel only when its clip is M's clip.** `kldown.c` line 249 takes whatever clip sits on
`[M+0x8d0]` on its first look. Play (0x4da294 .. 0x4da306) stops channels of the same body class when another clip
starts, and a stopped channel is reused; `[M+0x8d0]` is not cleared. `[M+0x8cc]` holds the clip 0x478270 handed to
Play (0x4782a8) and the channel's +0 is that same pointer (0x4da553). Add `clip == klh_rd32(m + 0x8cc)` to the
first-frame test. Today only 'speed is 1.00' and 'the end tick fits the clip' stand between the hook and slowing some
other full-body clip of his for the rest of state 3.

**S2. Say what the slow get-up costs under fire, and set the sample accordingly.** 0x8da4c2 .. 0x8da4d2: in state 3
(and in state 1) the trigger returns 0, so every hit costs full damage; only the fall (state 2) is free. He goes
down with `DownHealth` 80; under the owner's Risk=2 a police bullet is 75. Stock exposes him for 0.8 s of get-up,
`Base=0.5` for 1.6 s, a brisk mash (6 a second) for 0.85 s. So with the defaults the part can only make him die
more often than stock, and the AI heisters' side (do they take hits while down?) was not read, so '1:1' is not shown.
The note mentions `DownHealth` 200 in passing; it should be the proposed value beside `Enable=1`, and live check D2
/ D3 should count deaths in the get-up, not only its length.

**S3. `DownHealth` up to 10,000 is past his maximum.** 0x76a75b .. 0x76a77c gives him `[T+0x25c]` through 0x4aa8b0 ->
0x61efd0, which was not read for a clamp; klbalance.c manages his maximum (401.5 under the owner's dial, the game's
550). Limit the key to his maximum as read from `[[player+0xa48]+8]` when writing, or read 0x61efd0 and say.

**S4. The log calls a death an 'UP'.** A death while he gets up clears D (0x88a990), the hook sees 3 -> 0 with
`kld_s.up` set and prints `UP after ... the get-up took ...`. Test `hp <= 0.01` there too (the other branch already
does), or D5-style checks will misread it.

**S5. The mash key acts as Cover the moment he stands.** While `[D+8]` bit 0 is set and `[D+0x20]` is 0, 0x84dda0
zeroes `[player+0xeb4]`, so the presses do nothing else during the get-up (good, and worth saying in the note).
When D is cleared the next press is an ordinary Cover press: a man mashing beside a wall or a low box goes into
cover or over it. Put it among the things for the owner's eyes after D3; no data fix is known.

**S6. Corrections to the note and the report.**
- 'ten times ... 0.80 s every time': the log has ten falls and EIGHT get-ups (0.80 / 0.81 s each). 19:50:50 has no
  line after `2->1`; 19:52:45 goes `1->0` after 0.13 s with no state 3. So 0.80 s = (21 - 1) / 25: the clip's
  length, not the stick's early end (that would vary) - the note can drop that doubt.
- 'the hit that floors him costs nothing': not for a blast (0x458e8f: kind 9 goes on to the damage).
- A press late in the fall sets `[D+4]` = 3 while M is still falling (0x47cde7 .. 0x47cdff, then 0x6373e0 does
  nothing): state 3 can last longer than the clip in stock too, and the hook's 'get-up took' then includes the wait.
- 0x70e0e0 has one more refusal the note leaves out: a non-0x6fd7c0 actor with byte `[actor+0x5cb]` set (0x70e13f).
- Section 7 should name the assumption the mash rests on in full: `[D+0x2b]` is refreshed in state 3 only while the
  input lock `[input+0x330]` is 0 and `[player+0x2720]` bit 1 is set (0x808943 .. 0x80895c); with the lock running it
  reads 0 and the get-up stays at Base. D3's FAIL line covers it; say so.

## Checked and found in order

- Nothing is called, patched or copied; the three writes go to addresses validated each frame (M by vtable, owner and
  state; the channel by address among his sixteen and by state bits; `klh_data` refuses memory that is not writable).
- Off by default; `Dry=1` writes nothing (the returns at lines 152 and 272 come before every `klh_data`).
- Stock level, no Arcade session, a police player, no player: `act` = 0, the trigger numbers are put back in that
  tick, the record is dropped. A new player object drops everything. The fallback thread does nothing.
- The trigger bookkeeping (found / written / changed by the game) was walked through for: key equal to the found
  value, a new tuning object, the constructor running again on the same address, Dry. No case leaves a written
  number behind once `act` is 0.
- No animation is started and no event is added, so the climb's crash class (re/climb_crash.md) does not apply; the
  clip's own events fire at the same frames, later.
- A get-up the game starts at 2.5 is left alone; a hook that stops mid get-up leaves the speed and the end tick
  consistent with each other.

## For the lead

Wire it in switched off after M1 (S1 with it: both are a few lines). First live run D1 (`Dry=1`), and read from it
the clip's frame count and whether `GETTING UP` appears at all; then D2 / D3 with `DownHealth=200`.
