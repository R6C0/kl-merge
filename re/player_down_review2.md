# Review of track R2 - the belly flop (`[Down] Flop=1`, klhook/kldown.c, re/player_down.md 9)

2026-10-11, adversarial reviewer. Offline: kl2.exe build 0490 re-read with `debug/dasm.py`, the bank build's `.ANM`
(`<work>/build/z_cover3/M03`) re-read with the worker's `R2/anm.py`, the live logs D1 / D2, the code line by line, the
compile re-run. Nothing was run in the game. The worker's files were not changed.

## Verdict: ACCEPT WITH FIXES

The reading holds where it was checked, the design is data-only and gated as the rules ask, and it compiles. Three
points must be fixed before the first live run with `Flop=1` (all small); none of them is a crash found in the exe.

## What was re-read and holds

| claim | checked at | result |
|---|---|---|
| the six words are slot ids, one reader | 0x5d6060 whole: state 1 -> `[M+0x8b0+2v]`, state 4 -> `[M+0x898+2v]`, signed test, a negative id -> the plain word, no plain -> returns 0; passes the id to 0x59d550 with `[M+0x8d4]` as the owner | HOLDS |
| the filler writes exactly these six | 0x752e5b .. 0x752f1d: `Get_Up` -> +0x898, `Compact_.._Get_Up` -> +0x89a, `On_Spot_.._Get_Up` -> +0x89c, `Get_Down` -> +0x8b0, `Compact_.._Get_Down` -> +0x8b2, `On_Spot_.._Get_Down` -> +0x8b4, `Aim_Cycle_UB` -> +0x8c8 | HOLDS. The constructor (0x5bd5ef ..) fills +0x898 .. +0x8af and +0x8b0 .. +0x8bb with 0xffff: twelve and six words, of which the filler sets three each; an index over 2 would fall back to the plain word = the flop's |
| a clip without events 6 / 2 is safe in 0x478270 | 0x478490 .. 0x47851e: event 6 none -> 0.3 x (frames - 1) (0xb172d8), event 2 none -> 0.5 x (0xb35790), at least event 6's; state 4: event 2 none -> the end tick is copied (0x478374); a clip of 0 -> return without Play | HOLDS |
| the lookup the hook repeats by reads | 0x5c2f60 / 0x876940 / 0x7c6750 / 0x48bc90: table `{n, n x offset or -1}`, pairs `{flags, number}` up to a pair whose first dword is 0, record = `[[0x1546f6c]] + number x 0x68` when number < count | HOLDS (kld_list is the same reads) |
| `[D+0x21]` is acted on outside the 'may get up' test | 0x47ce56: byte cleared, 0x8b1900 (D == 2: 0x43c360 stops the channel by player vtable +0x1f8, M 1 -> 2, 0x773d20), then D = 3 (0x8c8150) and 0x6373e0 -> 0x478270(M, 4) | HOLDS - with the precondition of M2 below |
| hits are free while D == 2 and 0x843fa0 says no | 0x8da4db .. 0x8da4ec; 0x843fa0 = D 2, M 1, tick past `[M+0x8e0]`, weapon object +0xdc == 0 | HOLDS |
| the fall ends at `[M+0x8dc]`, the get-up at `[M+0x8dc]` | 0x640c00 .. 0x640c60 | HOLDS |
| the two clips: in every set, full-body, no event | bank build, 37 collections listed: `Die_Forward` clip 736, 50 frames, flags c0, +0x28 0, events []; `Rise_From_Stomach` clip 701, 202 frames, events []; the stock fall carries events 5 at 0, 6 at 7, 2 at 18 | HOLDS for the bank. So the climb's precedent (event id 5 on an action without an object, re/climb_crash.md) does not apply to the default pair: no event at all. `Die_Backwards` [] and `Rise_From_Back` [(8, 0)] (0x637060 does not act on 8) are clean too |
| the constants | 0xb89a20 2.5, 0xb5bbb0 25, 0xb39f70 -1024, 0xb17340 0 | HOLD |
| compile | `git archive HEAD klhook` (HEAD f9587ff) + the tree's kldown.c (sha1 02443d51...) in `G:\kl_scratch\R2rev\src`: 'built ...\test\dinput8.dll (TEST)' sha1 bf4543658f2e80ce63e613203952346f7bf43b41, 'built ...\ship\dinput8.dll (SHIP)' sha1 45982a7824c1babeae322903b77568456da82b0d; the one warning is klhud.c(188) | HOLDS |

Not re-read: 0x72ab60 / 0x802250 (the AI's death clip choice), 0x730be0 / 0x7ea990 / 0x5f4ac0 beyond the two health
places (0x7eaad9, 0x5f4d36: a share of the maximum is set, the constants not looked up), the 235-of-235 log count.
None of them carries a write.

## MUST

**M1. A dead man is still written to when the owner's own setting is on (`[Fed] Player=1`).**
`kld_dead()` says dead only at health <= 0.01 or crew-record status **7**. With `[Fed] Enable=1 Player=1` - which IS in
the owner's KLHook.ini (lines 57 - 59) - a human who dies goes to status **1** ('dead, waiting to return as police',
klfed.c line 302; live: run PT_DM03_die_r2 'fed: you: status 0 -> 1 ... countdown 5.0 s'), and stays there for the 5 s
until the police body is made. D1 / D2 ran without the fed (they show `record 0 (you): dead` = status 7), and the
worker's own finding is that the health does not read 0 at the death ('the last health seen was 0.4', then the health
object is new) and that D keeps its state 1 / 3. So in the owner's game, for those 5 s: `kld_flop_down` sets
`[D+0x21]` on the corpse every 0.3 s while D is 1, holds `[M+0x8e0]` while D is 2, and the get-up path writes the
channel speed and the two end ticks while D is 3 - exactly what the new check was written to stop. Whether 0x47cd80
still runs for a dead player was not read; if it does, the corpse is told to stand up.
Fix: dead = the human's record status is anything but 0 (in play) - or at least 1 and 7. Also put `!kld_s.dead` on the
flop's end block at `ds -> 0` (`FlopUpPct` would otherwise write the health of a man flagged dead when his D is
cleared later on the same object). Add the live check: F2 with `[Fed] Enable=1 Player=1` and a death during the
get-up: one `DEAD WHILE ...` line, no `down:` write line after it, the fed respawn as in PT_DM03_die_r2.

**M2. The re-request while he lies does not keep the game's own precondition.**
Stock sets `[D+0x21]` only when M is 2, or D is 2 with 0x843fa0 true (which needs M == 1): 0x47cddb .. 0x47ce2a. Then
0x6373e0 starts the get-up **only if `[M+0x8ec]` == 2**. The hook's first request (`ds == 2 && ms == 1`) keeps that.
The second one (`else if (ds == 1 && ...)`, kldown.c line 400) does not look at `ms`: with D 1 and M in any state but
2 the game would set D = 3 (0x47ceed) and start no clip, and D 3 without M 4 ends only by `[D+0x20]` or M 5
(0x640c35 .. 0x640c60, 0x47cf0f). That case was not shown to be reachable - but it is the one path here that could
leave him in 'getting up' with nothing playing, and the fix is `ms == 2` in that condition.

**M3. The flop's 202-frame get-up can be played with track R's numbers: 16 s on the floor.**
`kld_s.fup = kld_s.fnow && kld_inlist(...)` (line 536): the flop's three numbers are used only when THIS fall was seen
as a flop (`fnow`). `fnow` is 0 when the fall was first seen at D 1 (the code itself allows `0 -> 1`, line 380:
`if (ds != 2) kld_s.fseen = 1`), when M could not be read in the frames of D 2, or when the fall that played was the
game's own. The three get-up words are the flop's all the same (they are written while he is up), so the get-up is
`Rise_From_Stomach` at `Base` 0.5: 201 frames / 12.5 = **16.1 s**, the time bound with it (16.3 s), `Top` 2.0 = 4 s
at full mash - under full damage, no `FlopTake` (it needs `fnow` too). Fix: choose the numbers by the CLIP alone
(`kld.flop && kld_s.fok && kld_inlist(pl, kld_s.idu, clip)`), and let `FlopTake` / `FlopUpPct` follow the same test
for the get-up.

## SHOULD

S1. **Prove the six words before the first write.** The object test (vtable 0xbb5d64, `+0x8d4` == the player) is
good; add: the three fall words found must be `klq_slot` of the three `..._Get_Down` names (or 0xffff) and the three
get-up words likewise, else one line and nothing written. That makes live check F1's 'holds 1847/65535/1850 ...'
a test the code does itself on every level and body, not only on the bank.

S2. **A free-text slot key can name a clip with events.** `FlopFallSlot` / `FlopUpSlot` take any slot name;
`kld_flop_check` logs the event count but refuses only a clip that is not full-body. klclimb.c has `klq_ev_acts`
(the game's own switch of 0x637060): refuse a clip carrying an id that routine acts on, other than those the stock
fall carries (5, 6, 2). The default pair and the pair named in 9.3 have none.

S3. **The check is once per player object, the set is not.** `fchk` is set at the first acting tick; klchar.c swaps
the body through the game's routine on the same player object. If the swap comes after the check, the verdict (and
the full-body test) is of the old set. The outcome read in 0x5d6060 / 0x478270 is benign (no clip -> no Play, the
state ends at the stale tick), but re-check when `[player+0x78]` or `[+0x7c]` changes. F4 (a Dead Men body) should
say in its PASS line which came first, `body:` or `down: flop:`.

S4. **`[D+0x21]` can be left set.** Stock sets and consumes the byte inside one call (0x47ce4d / 0x47ce56); the hook
sets it between frames. If D ends before the game's next 0x47cd80 (it returns at once while D is 0), the byte stays
and the NEXT fall is cut in its first frame. 0x88a990 clears it; 0x76a450 was not seen to. Cheap: when `ds == 0`
and the byte reads 1 after a request of ours, write 0.

S5. **The request also takes a cover.** 0x47ce07 .. 0x47cee8: with a cover's user action on offer (0x744fe0) the
consumed byte means 'into the cover': `[D+0x20]` = 1, D ends at once, no get-up clip, no mash. In stock that follows a
press; with the flop it happens by itself at the end of every dive beside a cover - and the dive goes 88 forward,
toward whatever he faced. Say it in 9.6 and add a live check (a dive at a low cover: what is seen).

S6. **`FlopUpPct=75` makes the knock-down a heal** (down at <= 40 %, up at 75 %, again after 10 s), and the dive adds
2.0 s without any loss. That is the owner's 'save him' - but it is a balance decision for him, not a default: say so
beside the proposed keys.

S7. **The report's compile base is stale.** HEAD (5e778ef) already wires kldown.c in klhook.c, so the three lines
are not needed any more and the worker's two sha1s (8d5d861f / 1a4a71cf) are of an older klhook.c / klbot.c /
klbalance.c; the pair above is the tree's kldown.c on HEAD f9587ff. The committed hooks test_w1 / ship_w1 carry
track R's kldown.c: the `Flop` keys (already in the committed sample ini) do nothing until this file is committed
and built.

S8. **`Flop=0` is not exactly the committed form** (the task asked for it): the death test with its early return,
the `dead` branch at `ds -> 0`, `klb_read` every frame while down. It is disclosed (9.6) and comes from D1 / D2;
accepted, with M1 applied to it - but F0 must run before F2 to show the changed track R path alone.

S9. Notes for 9.6: (a) no writer of `[M+0x8f0]` but the constructor was found by a scan of every instruction with
that displacement (0x5bd6a6), so 'v = plain / compact / on the spot' may never vary for the player - harmless either
way; (b) the dive is 88 FORWARD where the stock fall is 23 back - toward the guns he faced; (c) a pause during the
last two frames of the dive leaves the request standing until the game runs again (fine, say it).

## Rules check

Data writes only, no game routine called (`klq_slot`, `klb_read` are reads) - yes. Game thread only - yes. Arcade, a
level that is not stock, not a police player (the committed gates, unchanged) - yes; the six words go back when the
part stops acting on a living object. `Flop` default 0, every new key inert without it - yes. Files touched:
kldown.c, re/player_down.md, the `[Down]` block of the sample ini - yes. Guesses marked - yes, except M1's (the
status value) which was taken as established from two runs made without the fed.
