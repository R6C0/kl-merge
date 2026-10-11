# Review of track Y1 (the level-data climb, `tools/kl_fa_climb2.py`, build `y_climb\DM03`) - 2026-10-11

Reviewer, offline, no game run. Verdict: **ACCEPT WITH FIXES.** The build is what the report says and is safe to put
through the one live look the report plans; two claims of the report are not supported and the live table lacks the
readings that would tell "root motion not applied" and "collision" from success. Nothing found that crashes at load.

## Re-run by me (all reproduce)
- `kl_fa_climb2.py check build/y_climb/DM03 build/r_tab/DM03v`: RESULT PASS (0 FAIL, 0 NOTE); 19 other members byte-identical,
  .prm/.fxc/.WAV sizes unchanged, .ANM +81,368, 20,961 -> 20,974 nodes, 8 HUD font chunks and .TEX identical.
- `kl_impact`: problems 0. `kl_fa_climb check`: PASS (0 FAIL, 8 NOTE). `kl_fa_vaultfx check`: PASS.
  `kl_fa_bots_dyn check`: FAIL (7 FAIL, 1 NOTE), the source's own (not re-diffed line by line).
  `kl_anm.py check`: 41 of 41 byte-identical.
- `+0x2C`: `clip_snd_bad` on y_climb (3,318 clips) and on r_tab/DM03v (3,311): none. The 7 added clips: 0.
- The 9 players' climb clips (Kane): events are only {105 (was 5), 6}; 105 is outside ZFFActionGeneric's set, so the id-5 crash
  of re/climb_crash.md cannot come back on this path. Agreed.
- Geometry: start 61.7 off the face z -625 (start z -686.7, facing +z = toward the wall), 36.5 over the floor, predicted end
  y 408.5 / z -585.5 on a 49.5 thick top: consistent with the check's numbers.

## MUST
1. **Unsupported claim: "collision returns inside the End (0x447bf2)".** `debug/dasm.py f:447bf2` lands in unrelated code (the
   `GuardInCrowdTactic` name stub at 0x447c70). Nothing in the report or climb2.md shows who turns the player's collision off
   for this cut, or on again. What I read in ZMiniPlayerActTask 0x8e8d00: collision/ghost-like handling (`0x86a130` object,
   vtable +0x2d8 / +0x2dc(1)) happens only when the clip HAS event 0x14 (found through 0x4a75d0), and none of the nine climb
   clips has an id 20 (events are 105 and 6; MEASURED above; 0x27 is also absent, so the task takes the duration path at
   0x8e8eab). What the `+0x2a4(1) .. 0x82cc40 .. +0x2a4(0)` pair around the teleport does is not read. So it is NOT established
   that the capsule is out of the wall: the root crosses the wall face at about y 384..408 against a top at 403.5 (event 6 is
   147.5 up and ~9 forward, the other ~90 forward come with the last 25 up), i.e. at most 20 under the edge. If collision stays
   on he can be stopped at the face, or pushed. Fix: remove the claim from climb2.md section 4.3 / 6 / 8 (Y6), say "not
   established", and add the two live readings below (S1). Optional safety build: a variant with a larger `lift` is not
   allowed by the 80 limit problem here (rise fixed at 172), so the fallback is luvsic's way, a second act (see 2).
2. **The end of the climb rests only on the clip's root motion, and that is not shown to be applied.** The task plays the clip with
   flags 0x20001 / 0x20003 (chosen by `[task+0x6a]`) through the player's vt+0x204; the report never reads whether those
   flags move the player with the ground bone. luvsic's own scripts do not rely on it: his van steps start at y 30, 202, 346 with
   z 2190, 2590, 2840, so the next act's `startpos` teleports him (172 up, but 400 forward, where the clip gives ~100). If root
   motion is not applied he plays the climb in place at y 236.5 and is then left there or dropped (no `startpos` at the landing).
   Fix (one of): (a) add a second act with a second PosObject at the predicted landing (his pattern, deterministic, independent
   of root motion), built as a variant `y_climb\DM03_end`; or (b) at least list "ends where he began" as a named FAIL reading with
   its meaning in section 8, so the live run answers the question. (a) is preferred; it is cheap in `build_nodes`.

## SHOULD
S1. Section 8 table: add rows for (Y7) the heading (the first pictures: he must face the wall; a 90 degree error is the report's
   own stated risk with `look9` against luvsic's `stored_rot`, and the live table has no row for it), (Y8) collision (pos lines
   every frame around the face: does z/y jump or stall at z -625), (Y9) the weapon is back in his hands after the cut (`weaponhdl
   Holster` is luvsic's and L03's first-act form; the restore is not read), (Y10) a hit during the cut (unbreakable; is he
   invulnerable or helpless with police shooting).
S2. FAIL readings (section 8, last paragraph): add "y stays about 236 and z about -687 after the cut = root motion not applied
   (see MUST 2)" and "stops at z about -625 = blocked at the face (MUST 1)".
S3. Squads: three empty `ZSquadScript` squads exist in an FA round. Not checked: any rules code that iterates all squads of the
   level (round-over "all enemies dead", spawn). L03 has the same shape in the campaign, FA never ran it. State as assumed in 9.
S4. `+0x2C` check is only "is a record start of the build's own .SND" (right for luvsic's crash, but it does not prove the
   sound belongs to the clip; the 7 cleared clips have no foley, as written). The report's "five tab builds 0 bad of 1,261" I
   did not re-run (I checked r_tab/DM03v only). `kl_graft` builds still join without `snds=` (documented in section 9).
S5. Report text: "A rout activated by a `PlayerAction` list starts even though its squad is unregistered" is labelled ASSUMED in
   the report but section 3 of climb2.md says "exactly the wiring" of L03 as if proven; reword to "same wiring as L03; L03's
   squad is also named by no object, FA has not run it".

## Owner's words
"definitely rappel and climb": the climb is built offline in the second form; the report states honestly that nothing was seen.
The AI heisters cannot use it (agreed: `ZPlayerAction` for players; their drop link stays). No change of any hook file; right.
