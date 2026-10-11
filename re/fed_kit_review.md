# Review of track M - the fed's kit (klfedkit.c, kl_fa_fedbody.py, re/fed_kit.md)

Adversarial review, 2026-10-11. Offline: kl2.exe build 0490 read again with `debug\dasm.py`, the worker's files read line
by line, the compile and the five checks run again. NOTHING WAS RUN IN THE GAME; the worker's files are unchanged.

## Verdict: ACCEPT WITH FIXES

The two data writes and both game calls rest on code that reads as the report says. Three points must be settled before
the part reaches the owner's game (one is the lead's, two are small). The crosshair fix is a hypothesis, marked as one.

## What was re-read and holds

| claim | evidence (this review) |
|---|---|
| 'No friendly fire' rule = `ZFFActor` slot 422 | vtable 0xbb3bac slot 422 = 0x8689c0, 423 = 0x61a980. 0x868a8d Arcade; 0x868a99 team 2 / 0 -> 0x868b11; 0x868b17 rules (0x7bb2a0), 0x868b27 attacker `ZFFPlayer`, 0x868b3f `call [vt+0x2f4]`, 0 -> text `FA_NoFriendlyFire` at 0x868b7b, then 0x868bdf / 0x868c07 -> 0x868dcf (past the message send 0x868dcd). No read of `+0x2723` on that branch. |
| slot 189 / 186 are plain getters | Heist vtable 0xbd3514: slot 189 = 0x4ee010 `mov al,[ecx+0x285] / ret`; slot 186 = 0x4c0630 `mov al,[ecx+0x283] / ret`. |
| the fed cannot hurt police AI | 0x868aa2 .. 0x868ad2 and 0x61ab34 .. 0x61ab6b; dword `[0xce8a44]` = 1 in the file. |
| `+0x285` set at the first loot, announcement only lost | 0x5cac90 whole: in Arcade (0x7f6850) it jumps straight to 0x5cacd2; after it only the `Looting_Started` announcement (skipped for a police client, slot 107). Clears: 0x74bd92 (a case of slot 7's state switch, next state 0x24) and 0x51be38 (slot 4). |
| crosshair branch | 0x8e9df9 .. 0x8e9ecb as written; red `[0xbbe498]` = ffcc0000, green `[0xbbe49c]` = ff22ff22. |
| Heist never initialises `+0x283` | byte-pattern scan of .text for stores to disp 0x283 / 0x284: only 0x7086a8 / 0x7086ae (FA slot 4) and 0x74d9f8 / 0x74d9fe (slot 187). Heist slot 4 (0x51bbe0) stores 0x280, 0x281, 0x282, 0x285. Allocation 0x725d86 (0xf30) -> 0x835480; no memset in 0x835480 / 0x7de590. |
| the fed's guns | 0x4b2a0e .. 0x4b2a19 `0x4b6680([0x168e96c], player, 0, -1)`; jump table 0x4b66e0 entry 0 = 0x4b66ca -> `0x410710(player, 0, 0x1c, 0)`. 0x410710 read whole: gate 0x8df480, rules slot 34 (returns at 0x4b5b56 for type 3), 4 x 2 removals, two `0x538ec0`, health 0x644310; `ret 0x10` = the hook's four stack arguments. |
| shop table at 0xbd1f68 | 0x4107a4 / 0x4107ab read `[row*24 + 0xbd1f6c]` / `[.. + 0xbd1f68]`. Row 0 = {6, 150}, row 28 = {29, 300}, row 29 = {31, 250}, row 30 = {32, 250}. |
| pool test | 0x55bee0: item equal, 0x6ee930(object) == 0 (= `[object+0x5c]` resolved through 0x8ccde0), `+9 == 0`, `+8 != 0`. The hook's count is stricter (a non-zero `+0x5c` counts as held): correct direction. int3 at 0x538f02 confirmed. |
| body routine | 0x783fb0 = 0x792290(node, model) ; `call [vt+0x1dc]` (slot 119 = 0x417a60 for 0xbb45f4 and 0xbb3bac) ; renderer notify. 0x8f5eb0 is slot 137's own police refusal, above the call at 0x8f5f03. 0x88c810 = store `+0x50` + notify. |
| the owner's log | KLHook.log 12:43:44 round 9, 12:43:59 dead, 12:44:04 fed (object 9), 12:45:26 dead for good; no line with a non-zero `$` in 12:44 - 12:45. |
| compile | scratch copy `G:\kl_scratch\M_review` (the worker's src + klfedkit.c as in the tree, identical): TEST and SHIP build, the only warning is klhud.c(188), none from klfedkit.c. klhook.c differs from HEAD by exactly the three lines. |
| checks | `kl_fa_fedbody.py check` on the five `z_fedbody` folders: PASS x5 (M01, M06, retomoto_full 1 NOTE; M02, M03 0 NOTE). KLJoin.ini of retomoto_full and M03 = the source's + the section only. `fedbody.png` of M06 shows the three bikers. |
| files touched | new: klfedkit.c, kl_fa_fedbody.py, fed_kit.md; KLHook.ini: one `[Fed]` block appended (HEAD had no `[Fed]` section: no doubled section). Nothing else in `git status` is this track's. Builds only under `z_fedbody`. |
| gates | Arcade only (`[session+0x5c] == 4`, Heist vtable), `klx_level_verdict == 2`, record 0 local human status 0, type 3 + police byte. Ticks are serialised by klh_tick's busy flag. klbalance re-applies its maximum after the loadout's health write (klr_put compares the current value with its own). |

## MUST

1. **Wiring it makes Hunt and Crosshair live in the owner's game at once.** His `KLHook.ini` already has `[Fed] Enable=1
   Player=1` (read: lines 57 - 59), and both keys default to 1 under exactly those two. Nothing has run. For the lead:
   either K0 + K1 run before the hook goes to him, or his ini gets `Kit=0` with the new hook until they have.
2. **`AkItem` equal to the pistol's item reaches the int3 the part promises to avoid.** klfk_ak_tick requires ONE free
   object of the rifle item and ONE of row 0's pistol; with `AkItem=6` (accepted: 1..63, any shop row) both counts are
   the same object, the loadout gives item 6 twice, and the second `0x538ec0` finds none free -> 0x53abc0 -> index -1
   -> `int3` 0x538f02 when the held list has none. Fix: refuse `item == pistol[0]` (or demand two free then).
3. **The removal half of 0x410710 is called but not written down** (rules file: 'read whole and say what it
   touches'). `re/fed_kit.md` 4.1 gives it half a line. 0x633250 with the weapon IN HANDS takes another path than the
   respawn's own call ever does (the fresh body holds nothing then): 0x8af180(0, 0, 1), vtable +0x4cc / +0x4ec /
   +0x4f0, 0x649250, then 0x7ddc30, 0x6d26f0, weapon vtable +0x25c(2, 0), 0x50d7c0. Say what these do, and above all
   WHERE THE REMOVED ZASTAVA AND PISTOL GO (back to the pool with `+8` set, or left held): every AK life otherwise
   costs the pool one more pistol than the game's own respawn. The hook should log the free count of the pistol and of
   item 29 after the call too, not only the AK's. Needed before `AkChance` is set anywhere; the key is off by default.

## SHOULD

4. **The list of `[rules+0x283]` readers is incomplete.** The comment names 0x4ae1b9 and 0x8429d0 'in reach of
   Arcade'. Also reading it on a rules object: 0x4569bf (0x4569b0, called from the FIRST-LOOT path at 0x7ceb48, just
   before 0x5cac90: with `+0x282 == 0` and `+0x283 == 0` it sets `+0x282 = 1`, calls slots 132 and 78 and 0x471d10 on
   `[session+0x84]`), 0x4eb337 / 0x4eb492 (0x4eb260), 0x5df2eb, 0x5e22ea (0x5e2230), 0x68109e / 0x6811c7, and
   0x4254fa in Heist's own slot 15 (0x425320, which also reads `+0x285` at 0x425651). Writing 0 only puts these on
   the path they take whenever the byte is 0, so no harm was found - but the 'why it is safe' text should say so.
5. **`[rules+0x285]` has a setter the note leaves out**: Heist slot 190 = 0x8f3930 `mov [ecx+0x285], al / ret 4` (no
   direct caller; virtual). 'Set once by 0x5cac90' is not the whole list.
6. **The crosshair cause is not proven; say so to the owner.** If K0 prints `[rules+0x283] = 0`, `Crosshair` writes
   nothing and his complaint stands. The other candidate is real: `[display+0x10]` is a cached pointer (slot 1 =
   0x83ab00 stores `gamedata[0x828 + 4 * index]` once), the respawn changes only the index byte (0x537700). For the
   worker's reading speaks that the multiplayer classes clear the byte and Heist does not. K0 before anything else.
7. **`Root=` is compared with the table size (0x12000), not with `Entries=`** (klfk_source). A hand-written Root at
   or above the loaded count reads a table slot a former, larger level may have left; the header test then looks at
   freed memory. One comparison: `root < entries`.
8. **`--link` shares every file with the tab build** (link count 2 on `z_rooms\retomoto_full\F01_Main.zip`,
   `z_route\M06\KLGuns.ini`, KLTalk.ini ...). A tool that rewrites a side file in place inside `z_fedbody\<map>`
   changes the tab's source build silently. The report says SHARED; the lead should make the tree from it and not
   run any step on those folders.
9. **The five sections are for today's tab builds.** `Entries=` is a chunk COUNT, not an identity: tracks K and L
   are replacing Retomoto's build (`z_lanes`, `z_fedpts`). Run `kl_fa_fedbody.py apply` LAST on each final build
   (merge_ini keeps the other sections) and `check` again.
10. **Whether any level makes an AK-74 object is not known** (the pool is counted at run time only). K3 may well
    print '0 free'; then AkChance needs level data. Also: row 29 (the AK-47, the hook's own default `AkItem=31`) has
    DLC = 1 and rank -1 in the table; the loadout does not ask, but say it.
11. **`+0x283` is not put back** when the round or session ends (every other part restores what it wrote). It is 0
    for the rest of that rules object's life. Harmless by point 4; one sentence in the note.
12. **No off-game harness** (klfed.c and klbalance.c have one). The 'one body, one throw of the dice per life' logic
    (reset on type != 3, kept through pauses) reads right, but K4 is the only test of it.

## Not refuted, still assumed (the worker marked all of them)

`[rules+0x283]` not 0 in his rounds; a type-3 `ZFFPlayer` draws and animates a 76-bone NPC model with weapons
attached (the swap comes ~300 ms after a possible second loadout); the AK-74 is 'the AK'; 35 per cent; the loadout
called a second time on a player holding and aiming his guns behaves like the game's own calls.
