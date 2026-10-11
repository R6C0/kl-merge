# Review 8 - track R8 (`[Down]` NoFire / Vulnerable / DownFromCop / DownFromCrew)

Adversarial review, 2026-10-11 night. Offline: kl2.exe 0490 re-read with `debug/dasm.py`, `klhook/kldown.c`
(sha1 4956acc2, the worker's) read as a diff against bac2f86, compile re-run. Nothing was run in the game. The
worker's files were not changed.

## Verdict: ACCEPT WITH FIXES

The exe reading holds everywhere I re-read it, the code does what the report says, Flop / Camera / Prompt are
untouched, nothing acts on a stock level. No code MUST. Three MUSTs are conditions for the owner's game, and one of
them is a design hole: with `Vulnerable` on, a guard at arm's length kills a floored man in one step.

## What was re-read and holds

| claim | evidence |
|---|---|
| fire is gated by mask bits 0x80 and 0x400, nothing else | 0x5fc008 .. 0x5fc07a: HoldFire `[H+0xb0]` -> `[H+0x2ce]`, TapFire `[H+0xa4]` -> `[H+0x2cd]`, both `shr 7` then `shr 0xa` of `[[H+8]+0xed0]`. Action names from the table 0xceba78 (index 5 TapFire, 6 HoldFire, 12 HoldGrenade, 13 TapCover) |
| every other button is 0x80 only | 0x5fbfa0 .. 0x5fc291: HoldCrouch, Heal, Grenade (`+0xf8` -> `+0x2d2`), TapCover (`+0x104` -> `+0x2d3`), Use: one `shr 7` each |
| the fall sets bits 1 and 0x10 only | 0x76a827 `push 1`, 0x76a830 `push 0x10`, both to 0x6feb90 (`or [[obj+8]+0xed0]`) |
| the game's own 'may not fire' is 0x200 + 0x400 | 0x860f80 `push 0x200`, 0x860f8c `push 0x400` on a shield victim |
| fire reaches the player as bits of `[player+0xb90]` | 0x589d30 (HoldFire: bit 2 set / cleared every frame), 0x5e9530 (TapFire: bit 1). A masked button clears the bit, so a trigger held at the knock-down is let go in the next input read |
| melee / shield-taking is off for a downed man | 0x612d07: `test byte [D+8], 1; jne` out |
| hits are swallowed by 0x8da3b0, asked at 0x458e7f; a blast (kind 9) is not | 0x458e7f .. 0x458e93 |
| the switch `[0xceb40c]`: 0 -> the trigger returns 0 at once | 0x8da3b3 / 0x8da3bd -> 0x8da4d2 `xor al, al` |
| eleven readers, no writer | byte scan of the image: 0x5491de, 0x62db71, 0x658701, 0x7107b4, 0x7107db, 0x724422, 0x76a621, 0x76a7df, 0x8c8151, 0x8da3b4, 0x8ee2c6 - all compares. 0x62db70 and one caller of 0x8c8150 are message handlers (`[arg+0x540]` -> `[player+0x2948]`); 0x7107b0, 0x8ee220 and the second 0x8c8150 are reached only from D's frame 0x724420 |
| D's frame stands still at 0 | 0x724421 / 0x72442b: out before the cooldown `[D+0x38]`, 0x8ee220, 0x50a9e0, 0x47cd80, 0x4205b0. The last two act only in D state 1 |
| the attacker's side is read from the hit | 0x8b8050: level byte `[[rules+0x5f8]+0x45]` clamped 1 .. 11, `R = tuning + 0x6ac + 0x70 x level`, `[[attacker+0x54]+4] == 2` -> `R+0x10`, else `R+0x08`, exchanged by player 0's police byte `+0x2723`. Called for a bullet at 0x4db9d1, only when the attacker's soldier pointer is not null (0x4db993) - a human attacker gets no float |
| klbalance.c untouched by this track | the working copy has no `KLR_DOWN` / `kld_factor`; its diff is X2's |
| the hand-over line fits X2's working copy too | the anchor `if (k == 5 && farm != 1.0f) want *= farm;` is line 559 there, after X2's new `CrewToFed` line, which is `mir` only |

Compile, re-run at HEAD 0d16a7a (HEAD moved during the review: `klmove.c` and `KLHook.ini` were committed) with the
worker's `kldown.c`, into `G:\kl_scratch\R8rev`; no warning, no error in any of the four:

| build | last line | sha1 |
|---|---|---|
| TEST, HEAD's klbalance | `built G:\kl_scratch\R8rev\test\dinput8.dll (TEST)` | 3390bf646d47d4af662ae8d1acdc53009207e4e1 |
| SHIP, HEAD's klbalance | `built ...\ship\dinput8.dll (SHIP)` | bfecf6be4526f0a3646585312e965baa717a618f |
| TEST, with the three lines | `built ...\test_ho\dinput8.dll (TEST)` | bede4b72141b7c595fb246c5abb1922464f54efa |
| SHIP, with the three lines | `built ...\ship_ho\dinput8.dll (SHIP)` | 450f68535ae8e3386bd7e27f4e3c4732df00d579 |

The sha1s differ from the worker's because HEAD is two commits on and the hook carries its build time. The worker's
four DLLs in `G:\kl_scratch\R8` have the sha1s the report gives.

## Attempts to refute that failed

- **Unable to fire after UP.** The bits come off in the pass that sees `[D+4] == 0`, the same pass as the `UP` line.
  Only the bits this part set are cleared (`mbits |= bits & ~mv`).
- **Unable to fire after a death or as a fed.** `kld_s.dead` is set in `kld_tick_main` of the pass that sees the
  death; `kld_rules` of that same pass has the same player object and clears the bits. The police body comes 5 s
  later and is another object. The 'dropped unwritten' branches are reached only when the object is gone.
- **Round end, pause, level change.** `down` needs session state 0x19; at any other state the bits come off while
  the object is still the local player. With no local player for 3 s the record is dropped; the mask lives in the
  player object (`[H+8]` is what 0x803c40 serialises at `+0xed0`), which goes with its level.
- **The switch left at 0.** It is written back first thing in any pass where `kld_flop_one` did not hold the fall
  in that pass (heartbeat `beat == pass`), including the pass that writes movement state 5, and `kld_rules` cannot
  return early while `kld_r.sw` is set. During a load no pass runs and nothing that reads the switch runs either.
- **A lethal hit into a stuck state, by reading.** Stock already kills a man in D state 2 with M state 1: the trigger
  stops swallowing at the tick (0.72 s) while 0x8ee220 keeps state 2 until M reaches 2 or a fire flag comes. After
  the death this part writes nothing; the held ticks run out by themselves. Not seen live: see M3.
- **A traitor priced as police.** re/balance.md 2 already had it: a turned bot stays team Ally, so `R+0x10`.

## MUST (before this is in the owner's game)

**M1. Point-blank: `Vulnerable` turns 'safe on the floor' into 'dead at once beside a guard'.**
The worker reports it and it is right: one step of a firing guard within 1.6 m is 72 x 1.05 x 100 x 0.5 x 0.25 = 945
against the 80 .. 220 he lies with. Before R8 that step was swallowed for the whole flop. The bank's stairs and
Retomoto's reception are where guards stand at arm's length (the 'ONE STEP' lines of CLAUDE.md). The owner asked
for 'a lot more shots from police'; this is one. `[Balance] PointBlankToYou` is the only remedy and has never run
(live order P0 of re/melee_damage.md). Do one of:
- set `PointBlankToYou` in his ini together with this hook, after P0 has run; or
- a fourth hand-over line so that klbalance's point-blank scale on the player is a small number while
  `kld_factor` is active, whatever `PointBlankToYou` says; or
- ship with `Vulnerable=0` until one of the two exists (NoFire and the factors still work lying the stock way).

**M2. The three hand-over lines must be in the klbalance.c that is built, and the start line must say so.**
His ini has `[Balance] Risk=1`, so klbalance owns the table. Without `KLR_DOWN` the build is safe but half the
track is inert: no fire, still invulnerable. Check the start line reads `HAS the hand-over lines (KLR_DOWN)`. The
lines go into X2's working copy, not HEAD's; they fit (above).

**M3. Runs N1 and N5 before his game, N5 with `[Fed] Player=1`.**
No log of the project holds a `WHILE FALLING` death: nobody has ever died in D state 2 of a flop, by a blast or
otherwise (0 lines in `<work>\build\klhook\live\*.log` and in the game folder's log). The report's 'dies as one
killed by a blast in a flop does' has no live precedent; the reading above says it should be clean. N5 must show:
`DEAD WHILE FALLING in the belly flop`, the switch back at 1 and `NoFire: off` in that pass, then
`fed: YOU ARE A FED`, and the fed fires. A second round after it must start with him able to fire and to be
floored again.

## SHOULD

**S1. A few frames at the full police price after a stall.** `kld_rules` tests `need && !kld_r.stand` for the
switch BEFORE section 2 recomputes `stand`. After a stall of 500 ms the fallback branch of `kld_tick` clears
`fon`, klbalance writes the standing price back, and the first game-thread pass keeps the switch at 0 on last
pass's `stand` until klbalance's next 50 ms tick. Fix: test `kld_r.sw && need && !kld_r.stand` again after
section 2 and write the switch back there.

**S2. The throw is not read.** The task names it ('nor throw'). HoldGrenade has only bit 0x80, which would take
the mash button too. 0x4aa410 only clears bit 0x40 of `[player+0xb90]` when the button is up; where a throw starts
and whether the prone movement allows it is open. N3 decides; if a throw starts on the floor a second handle is
needed.

**S3. 0x8b8050 has a second caller inside the damage routine.** 0x458946 (Arcade, attacker of one class) takes the
same float x the constant at 0xb5cde8 into a local that is compared further down. Section 14.4 does not name it. The
down factor moves that number as well: read what it bounds (the same-attacker limiter is the likely one) before
the numbers of 14.4 are trusted.

**S4. Police pistols are not 'a lot more shots' at 0.25.** The worker's own table: M9 / Sig / MP45 cost 28 / 36 /
47 on the floor = 2 .. 8 bullets from 80 .. 220. Most guards of the Dead Men maps carry pistols. 0.15 or 0.1 is
the likelier default; say so to the owner with N1's `he lost` lines.

**S5. The cooldown change is a balance change.** With the frame frozen `[D+0x38]` starts at UP. Before, the flop's
2 .. 10 s counted, so a man was often free to be floored again when he stood. Now he stands with what the floor
left him and cannot go down for the whole `Cooldown`: the next hits kill outright. Tell the owner, or shorten
`Cooldown` by the knock-down's length, or use `FlopUpPct`.

**S6. klbalance's `Risk=.. written (.. value(s) changed` line twice a knock-down.** It reads like the dial being
armed again and will bury the round's real lines. Count the down factor's writes apart, as `isfar` does for the
range factor.

**S7. Non-bullet hits cost in full with no factor.** Close combat's flat 50 and falls were swallowed and now are
not; which can reach a lying man is unread. Log check: a `he lost 50.0` line with an attacker who is not firing.

**S8. A comment is wrong.** 0x804546 is not 'the game makes a player object's mask new when it resets it': it is
0x803c40 reading the dword from a stream into `[player+0xed0]` (a state restore). The branch it explains is not
reached in practice (the death pass clears the bits first), so nothing breaks; correct the text.

**S9. The `[Down]` sample of R8 is already in HEAD's `KLHook.ini`** (it went in with 0d16a7a) while `kldown.c` is
not committed. A hook built from HEAD ignores `NoFire` / `Vulnerable` / `DownFromCop` / `DownFromCrew` silently.
Commit the two together.

**S10. Online, as the report says:** the switch is one dword for every player of the process and the two floats
price NPC attackers only. Nothing here is a host-side rule yet; the per-attacker choice is the only groundwork.

## Keys against the task

| task | built | ok |
|---|---|---|
| `NoFire=1`, default 1 with a Flop, restored at UP / death / round end / fed | yes; 2 = fire only | yes |
| not invulnerable for the whole knock-down | `Vulnerable=1`, Flop=1 / 3 only (Flop=0 / 2 fall to the stock rule) | yes, extra key |
| `DownFromCop=0.25` (a guess, marked) | yes, clamped 0 .. 4 | yes |
| `DownFromCrew=1.0` | yes | yes |
| by the attacker's side, from the hit | the game's own pick in 0x8b8050 | yes, NPC attackers only |
| cop factor on the point-blank step | applies, still lethal | M1 |
| no throw | not gated, not read | S2 |
| klbalance.c not edited, 3-line hand-over | yes | M2 |
