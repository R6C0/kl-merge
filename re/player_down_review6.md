# Review of track R6 - `[Down] Flop=3`, all the belly falls (adversarial, 2026-10-11 ~18:00)

Reviewed: `klhook/kldown.c` (sha1 05cb16e1146d390e0d52d6578c0b4d40ca609a16, diff against HEAD 1d528a9), the `[Down]`
sample of `klhook/KLHook.ini`, `re/player_down.md` 12. **Offline; nothing ran in the game; the worker's files were not
changed.** FILE = read again by this review from the `.ANM` of `z_cover3\M03`, `z_route3\M01`, `z_loot3\M02`,
`z_route\M06`, `z_rooms\retomoto_full` and stock F07 (scratch `r6rev/facts.py`: every set, every list clip, its
events, record and GROUND keys); READ = kl2.exe read by this review (`debug/dasm.py`); LIVE = the owner's log of G1.

## Verdict: ACCEPT WITH FIXES

The hook part is sound as data writes go: one DWORD in a pair of the human's own set, checked before every write,
put back under review3 S1's rule; `Flop=0 / 1 / 2` are untouched; everything is off by default. No clip of the list
carries an event that can reach an action, and none can leave him stuck by the hook's own logic (both bounds and the
mask release hold for each, #43 included). What is NOT sound is the root-motion part of the live plan: by the game's
own alignment of the fall the long dives will most likely not travel as the sheet shows, and check W1 as written
passes in the open (M2). `Flop=3` must not go into the owner's ini before M1 - M2 are done and L0 / L1 have run.

## What was checked and holds

1. **Every clip, from the file** (the same in all five tab builds and F07; `Kane` = `Lynch` = `Kane_NPC` = `Lynch_NPC`
   for these slots):

   | sheet | clip | frames | events | record flags | record +0x18 | GROUND keys: forward / most sideways | travel BEFORE the align frame 0.3 x (N-1) |
   |---|---|---|---|---|---|---|---|
   | 41 | 770 | 216 | 7@43 31@43 8@72 | **c0** | (-17, 0, -301) | 3.01 m / 0.17 | 2.33 m of 3.01 (78 %), frame 64.5 |
   | 7 | 715 | 206 | the same | 10c0 | (-5, 0, -249) | 2.49 / 0.05 | 2.33 of 2.49 (94 %) |
   | 13 | 721 | 206 | the same | c0 | (-5, 0, -249) | 2.49 / 0.05 | as 7 |
   | 12 | 719 | 239 | 31@7 7@55 8@115 | **c0** | (-4, 0, -328) | 3.28 / 0.04 | 3.16 of 3.28 (96 %), frame 71.4 |
   | 9 | 718 | 239 | the same | 10c0 | (-4, 0, -328) | 3.28 / 0.04 | as 12 |
   | 10 | 717 | 140 | 31@17 7@46 8@80 | **c0** | (30, 0, -341) | 3.41 / 0.47 | 2.94 of 3.41 (86 %), frame 41.7 |
   | 25 | 731 | 186 | 31@1 0@39 7@46 8@116 | 10c0 | (5, 0, -66) | 0.66 / 0.17 | 0.56 of 0.66 (85 %) |
   | 42 | 769 | 219 | 7@53 31@53 8@119 | **c0** | (-35, 0, -363) | 3.63 / 0.70 | 2.88 of 3.63 (79 %), frame 65.4 |
   | 43 | 768 | 53 | 31@18 7@47, no 8 | **c0** | (0, 0, -405) | 4.05 / 0 (2 keys: a straight line) | 1.22 of 4.05 (30 %), frame 15.6 |

   The worker's frames, events, clip numbers, slot ids (carrier 1768, ONE pair {0, 719}) and forward distances are
   right. The forward motion is monotonic in every clip (the most = the end) and the record vector equals the keys,
   so `FlopReach` by record -z is a fair measure; sideways is at most 0.70 m (#42). No clip has event 5, 9 - 11, 20,
   21, 24 - 30, 32 - 35, 42, 48 - 53. All nine have record flag 0x40, flag 8 clear, a GROUND track and a clear
   +0x28 bit 0x10 = full body, 'moved by animation' (re/climb.md 3).
2. **Event 31 in the middle of a clip.** Not only LIVE for #25: READ (re/climb_crash.md 3, re-read here with
   0x478270) the prone fall calls the player's Play (vtable +0x200) and nothing else; `Play alone subscribes nothing`
   - a channel gets a queue only from 0x7f60e0 / 0x425280 (an action's start) or 0x812a50 (event id 500: none here).
   So the queue is 0 by who plays, not by which clip: 31 at 7 / 17 / 18 / 43 / 53 reaches no action. 0x478270
   itself asks only for events 6 and 2 (0x4a75d0). The risk 'one clip of seven crashes by an event' is low; the
   `event queue` word in the log remains the stop sign.
3. **No bot's draw changes.** FILE: 37 / 36 / 36 / 34 / 34 sets a build; each set is its own pool; the carrier is one
   pair {0, 719} in 11 / 10 sets (`Kane`, `Lynch`, `Dog`, `Kane_NPC`, `Lynch_NPC`, `Thug`, `Swat_02`, `Civilian`, ...).
   Only the human's set is written. `klcrew.c` (its header, lines 20 - 39, read now): a bot gets a MODEL by
   0x783fb0, never a set. The carrier's name is resolved by one routine, 0x78d9d0 (the table at `[actor+0x2a1c]`,
   made on demand from 0x5681d0, 0x730be0, 0x875830 = the NPC state code): no player routine names it.
   The guard `/Damage/Hit/Front/Front` separates human from NPC sets as said (it does not catch `Dog`: no matter).
4. **The time bound and the mask, per clip**: `cap0` = way to the landing at the game's pace + the rest at
   `FlopBase` + 1 s from each clip's own event 7 and length (10.3 / 11.4 / 6.5 / 8.7 / 10.4 s + 1); #43: `light`
   takes the clip's own pace (2.08 s + 1), `t_land` is never set so no press is counted and no speed is written;
   the end (mask bits off, then state 5) is Flop=1's code for all. A dead man / a fed / Dry: the caller, unchanged.
5. **The moment of the choice.** In `kld_tick` the check (`kld_mix_check` -> the first choice) runs BEFORE
   `kld_flop_words` in the same pass, so the fall words never name the carrier before a choice is in its pair; the
   second writer is the pass that sees D back at 0. A fall is identified by `[M+0x8cc]`, not by what was written.
6. **Collision.** READ: `ZFFPlayerMovementProne` slot 13 (0x7e4bc0) calls the player's vtable +0x564 = collision
   ON and clears `[M+0x8ec]` / `[M+0x8d0]`; of the 58 routines of its vtable none loads +0x560 (collision off).
   That backs 'the physics step runs in the fall' a little more than the worker had; it is still not seen.
   `[M+0x8f0]` (plain / compact / on the spot) has one writer on this class, the constructor 0x5bd530: the three
   fall words are in effect one, as section 9 guessed.
7. **Flop=0 / 1 / 2**: the diff touches them only through `KLD_ONE` / `KLD_KEEPUP` (identical for 1 and 2), one
   no-op call of `kld_mix_back` and `kld_s.p0`. Keys off by default (`Flop` 0; `FlopUp` 0). Only the three files of
   the task carry R6's changes (the other modified files in the tree are other sessions': bank, kl_chars).
8. **Compile** (again, `git archive HEAD klhook` at 1d528a9 -> `G:\kl_scratch\R6rev\src` + this kldown.c):
   `built G:\kl_scratch\R6rev\test\dinput8.dll (TEST)` sha1 725ccd1bcaaf831eb7429b7c3848b3c2e6609718,
   `built G:\kl_scratch\R6rev\ship\dinput8.dll (SHIP)` sha1 4c3a940290d178b3fc5c2dc1b366612ed4f1e681; one warning,
   klhud.c(285) C4101. (The sha1s differ from the worker's: the build is not reproducible byte for byte.)

## MUST

**M1. `FlopReach`'s default (4.5 = everything in) is against the task's rule; make the code's default 1.0.**
The task: a clip that can carry him through a wall or off a ledge 'is OUT until shown safe ... left out when the hook
cannot test the way'. The hook cannot test the way and nothing is shown. With 4.5, `Flop=3` alone in an ini puts
every dive and the 4 m stumble on the game. Default 1.0 (= #25 only, his death left alone); the lead's runs L1 / W1 /
W2 set `FlopReach=4.5`; the owner's ini gets the value those runs allow. (#43 is the one to watch: see M2.)

**M2. The game's alignment makes W1 pass in the open, and the dives will probably not look like the sheet - the live
plan must measure it before it judges walls.** LIVE: in the only fall ever played this way (G1, in the open)
`[D+0xf4]` was set. READ (0x478270, re/climb.md 3 on AlignTo 0x80fdc0): the fall is then aligned to the transform
at `D+0xf8` / `D+0x11c` at frame 0.3 x (N - 1), the correction cancelling whatever the clip's root did up to that
frame; only the travel after it is the clip's own. FILE (table above): that is 78 - 96 % of the travel of 41 / 7 / 12
/ 10 / 42 - they keep 0.68 / 0.16 / 0.12 / 0.47 / 0.75 m - while #43 keeps 2.84 m of 4.05. Consequences:
  - if the align place is his own, every long dive is a dive ON THE SPOT (the body sliding back under the clip for
    2 - 3 s); if it is elsewhere he is carried there. Neither is what the owner chose from the sheet, and neither was
    said to him. Who sets the place is still not read (worker: 0x8cf030 begun).
  - `SHORTER: something stopped him` (`mv2 < 0.6 x own`) will print for those five clips with no wall at all, so
    W1's PASS line proves nothing; and `HE WENT DOWN OVER AN EDGE` aside, nothing in the log says whether the
    physics step ran.
  Fix (log only, no new write): in the `THE KNOCK-DOWN` line print `[player+0x7a5]` (collision on) and
  `[player+0x7b4]` (the off count), the align heading from `D+0xf8` against his own heading, and the travel the
  clip has LEFT after its align frame (a number of the list entry); at UP compare with `|align place - p0| + that`.
  Rewrite W1: the same clip once in the open and once at the wall, PASS = not beyond the wall by position and
  picture; add to L1 'is each dive a dive, or a slide on the spot' as a question for the pictures. Until L1 has
  answered it, do not tell the owner that he gets the falls of the sheet.

## SHOULD

S1. **12.1 / 12.4 / L0 say 'record flags 10c0' for the list's clips; FILE: 41, 13, 12, 10, 42, 43 are `c0`**, only
    7, 9, 25 (and 71) are 10c0. L0's sample PASS line for #41 will not match and 'other numbers than the table = the
    file reading is off' would be raised for nothing. Correct the text (bit 0x40 is what matters, and all have it).
S2. **What bit 0x1000 is, and why it matters for the look.** FILE: a clip with it has four non-zero vectors at
    record +0x30 .. +0x5c (a unit direction and a place, start and end); the stock pair is `Down_Not_Dead_Get_Down`
    (10c0) against `..._No_Weapon` (c0). READ: 0x8b4200 uses them only for 0x1000 clips. So the five c0 clips of the
    default mix are the 'no weapon data' kind and #25 - the only one seen live - is not: what his rifle does in 41 /
    12 / 10 / 42 / 43 is unseen (what the vectors drive was not read: a GUESS that it is the weapon). **9 is 12's
    data WITH the vectors and 7 is 41's dive with them**: L1 should play 9 beside 12 once (`FlopMix=12:1,9:1`) and
    the default take whichever holds the rifle right.
S3. **A failed pair write leaves the words on the carrier.** `kld_mix_next`: when `klh_data` fails it returns with
    `fok` still 1; the fall then plays what the pair holds - with `FlopReach` / `FlopMix` excluding #12 that is an
    excluded clip, `kld_mix_find` misses it, the line says 'the game's own ... slot ids were not in place' and the
    part writes nothing (the game runs 239 frames at its own pace, hits count from frame 119). Set `fok = 0` there.
    And 12.2's 'either is a whole clip of the list' holds only because of the order of point 5 above: say that.
S4. **Body swap A -> B -> A.** At A -> B `kld_mix_back` puts the pair back only if another live player still wears A's
    pool; if not, A keeps the last choice, and on the way back the check reads that number as 'the level's own'
    (`kld_cx.old`) and finds no clip named `Merc_Run_Torso_Back_03` in the carrier: #12 is silently OUT for the
    rest of the level. Harmless (nobody else plays the slot), but look #12 up through #9's slot as a second place, or
    keep {pool, own number} of the last two sets.
S5. **`KLD_KEEPUP` is evaluated on the current `kld_s.idu`.** With `FlopUp=71`, a re-check (body swap) on which the
    get-up slot is not usable sets `idu = -1`; the three get-up words written before are then neither rewritten nor
    put back (both loops skip them). Remember 'get-up words written' in its own flag. Off-by-default path.
S6. **`FlopUp=71` was not reviewed beyond its gating** (off unless the key is 71; with 0 no line of it runs: checked).
    Its costs as the worker lists them stand; add that with `FlopUp` the get-up words are 71's for EVERY fall, also
    #42 / #43 and a fall handed back by a time bound. Keep it a test key until U1.
S7. **For the owner, in plain words** (12.3 has it for the lead only): the default mix is 10 - 11 s on the floor
    without a press and without damage, against 8.7 s today; and the stumble #43 is 2.1 s of immunity plus the
    down's health for a man who never fell. Both are his to decide (`FlopBase`, `FlopLight`).
S8. Process: three edits of kldown.c went through a heredoc against the rules. Checked here: the added lines hold no
    damaged escape (the one `\\` in a string is right, the file compiles in both builds without a new warning).

## Not established by this review either

Who sets `[D+0xf4]` and where the align place lies; whether the correction of an aligned fall goes through the
physics step like the root delta (read for the delta only); an edge; what the down state's camera does over 4 m;
how any clip but #25 looks on the player. All of it is L1 / W1 / W2's - after M2's log lines exist.
