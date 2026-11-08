# Dead Men maps: room reverb from their own rooms (1108)

Tool `tools/kl_dm_reverb.py`, test `tools/kl_dm_reverb_test.py`. STAGED for DM02, nothing installed, not run in game.

## What and why
Dog Days' stock FA maps change the reverb with the room: a box (ZBoxPrimitive) carries `CheckInside` + `Audio_ReverbActivater` (ClassInfo 0xd07164);
entering the box calls `ZSynthOpenAL::SetReverb` (0x5fff30, one global EFX slot). Grafted DM maps have no such boxes, so they have one flat reverb.
The tool authors one box per DM room box (`.rmi` flag-1 AABB: centre +0x28, half extents +0x40, room slot +0x4c), in a new top-level group `KL_Reverb!`
(listed in root tree 3), each box cloned from the stock donor `F01_Audio.zip\Audio!BOX!010_Inside_DL10_Platform` (flags 0x200000, no model).
`CheckInside` field 1 = own path `ROOT\KL_Reverb!\<name>`; `Audio_ReverbActivater` field 0 = SND offset of the chosen DD roomeffect, field 3 = wet value.
Slot ids are renumbered as in `kl_fa_cover.apply` (.oct/.rmi/.rmc/.prm re-pointed; the four big blocks keep size).

## Choosing the effect
DM roomeffect (0x70 bytes, EAX5) vs DD roomeffect (0x50 bytes, I3DL2) of the map's own `.SND`; nearest of the same kind (Ins_/Out_ vs /inside/ /outside/)
by `distance()`. No SND objects are added (riskier); the ideal I3DL2 values per room are kept in `reverb.json` for a later step.
DM02 result: 28 rooms, 42 boxes, 3 of 7 effects used (34 inside_stairs, 5 outside_alley, 3 inside_loadingbay); skipped Out_Skyline (no DM effect), DebugRoom, AlwaysVisible.

GUESSES (commented in code): DM +0x44/+0x48 pair order; distance weights; density 100; field 3 wet value (per effect from stock F07 boxes, default 60.0); EAX5 diffusion 0..1 to percent.

## Toggle
The toggle is the install/undo pair (a runtime [Reverb] key would need a klhook change). Staging options `--no-inside` / `--no-outside` limit the boxes.

## Re-run rule (peers rewrite zips)
The live DM02 zip changed twice on 11-08 (6daf89a4 then 7adcb235 at 02:31). Always re-stage on the live zip right before installing:
`python tools/kl_dm_reverb.py stage-map "<DD>\KLExpansion\Maps" DM02 C:\kl_build_1024\dmreverb_1108`
`install.py` refuses unless every live file equals pins.json `old`. Refuses a zip that already has a `KL_Reverb!` group.
Other DM maps: same command with DMnn (uses that map's source level for the DM effects).

## Current pins (restaged 11-08 on the live files, first 8 hex)
| file | live (old) | staged (new) |
|---|---|---|
| F02_Main.zip | 7adcb235 | afc884c2 |
| F02_Main.bots.zip | 1103c692 | c4d93044 |
| F02_Main.bots.base.md5 | fbf0496a | f358b059 |

Stage: `C:\kl_build_1024\dmreverb_1108` (install.py, pins.json, reverb.json). Backups `*.before-1108dmreverb` beside the live files.
`install.py [--dry] [--undo] [--skip-run-check] [--game DIR]`; all or nothing with rollback; undo needs live == new and backup == old. Rehearsed on a scratch copy: install, refuse on drift, undo byte-exact.
Read-back `check`: 54 PASS / 0 FAIL on both zips; test 18 checks 0 fail.

## Risks
- Coarse mapping: DM rooms are short and dry, so only 3 of 7 effects are used; the stairs reverb may be over-wet in small stores.
- Field 3 meaning unproven; firing order of overlapping boxes unproven (nested rooms); no default-outside box.
- ~2400 .prm roots re-pointed after the renumbering (same as the cover pipeline); slot-id bugs would show as missing/invisible rooms.
- Whether CheckInside fires online (clients) is unproven.
- Any later DM02 rewrite by a peer invalidates the pins (re-stage).

## Bench DMREV_DM02 (2026-11-08 03:28-03:38, db): items 1 and 4 PASS, item 2 NOT SHOWN
Kit C:\kl_build_1024\dmrev_1108\run.py (TEST 76bd4a9c, live ini + [Echo] Enable=1 Log=1, PD2R_DM02 host/join scripts, install -> bench -> undo in finally).
PASS: 2 seats in round 2, asserts 0, faults 0, loads 2; undo byte-exact (zip 7adcb235), live dll 19611c16 / ini cd431998 restored.
Reverb: each seat logged ONE distinct EFX set, decay 1.49 / late delay 0.011 = the EFX generic default, none of the three effects used
(inside_stairs 1.10, outside_alley 1.30, inside_loadingbay 1.49 with reflections -370 mB). [Echo] Log=1 dedupes on (kind, decay, refl), so a box that fired
would have logged a second line: no KL_Reverb! box switched the reverb. The DD09 echo bench (stock map, stock boxes) also showed only that default, so it is open
whether ANY Audio_ReverbActivater reaches this alEffectf slot in multiplayer, or whether the scripted seats never stood in a box.
Next: stock F01 bench with [Echo] Probe=1 (every SetReverb logged, not deduped) and a seat that walks into 'Audio!BOX!010_Inside_DL10_Platform'. If stock fires, re-bench DM02 with a walk.

## Live bench checklist
1. Load DM02 offline and online (host + client): no crash, no assert, bots still run.
2. Walk atrium, corridor, store, stairs, alley and parking lot: the reverb changes at room borders, no stuck state after leaving a room.
3. Compare with the same walk before install (flat reverb).
4. Undo: md5 equals the pinned old, map loads.
