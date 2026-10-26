# Online sound loudness, pass 2 (1026sndon2), 2026-10-26

Owner rule: all sounds at MP45 loudness, glass destruction and any other kind. Tool: `tools/kl_sndonline.py`
(audit / build / verify / selftest). Staged (NOT installed) in `C:\kl_build_1024\sndonline_1026b\` with
`INSTALL impact sounds pass 2 all maps.bat`, `UNDO ...bat`, `install_gunsnd2.ps1` (md5-chained, backups
`*.WAV.before-1026sndon2`, `-Root <folder>` rehearsal, `-Groups`). Pins: `tools/kl_sndonline2.pins.json`.

## What changes
- Every bank (maps, stock, story): `pcmfx` = in-memory STEREO PCM destruction (DM03A Explosion_Vault_Inside_01,
  GetawayCar_Crash, L04 Explosion_Distortion_Debriss_02 ...): one common gain, hard clip per channel, head on the mono mix.
  `wood` = Wood_Crack, Wood_Break/*, Plastic_Break/*.
- Story banks L00..L11 (never covered by 1026sndon) also get the tier B classes: glass hits/cracks, shatter, metal/concrete
  break, canisters, all Impacts/Bullet/*.
- Result: 26 banks, 2626 records (321 distinct names), 24.9 MB of new spans, median head -11.32 -> -3.30 dB.
  Same byte spans: WHD/SND/zips untouched. 4 records/bank skipped (Impact_Metal_Default_01/13/14/17: too short for the 30 ms fade).
- Verify: 26 banks PASS, 1254 gun records byte-identical, apply+undo reproduce md5s. Rehearsal with `-Root` on a copy of
  DM03A/F03/L00: install then undo gives the original md5s.
- Optional env (default OFF, not built): `SNDON_GRENADE=1` grenade landings, `SNDON_LONG=1` bridge collapse rumbles (peak normalised,
  no hard clip; a judgement, not parity).

## Remaining gaps, decided
1. Retomoto window blast (M09_Explosion_Window_Office) is a STREAMED Ogg in PC_Def.str: head -4.87 dB, peak 0 dBFS, only 1.7 dB under
   MP45. Not patchable offline in the .WAV. No change. (Vault explosion is in-memory PCM, so it is covered above.)
2. .SND group volumes: Arcade uses the same values as online (shot_npc 0.35, shot_player 0.70). Online = Arcade, so raising the npc
   volume is NOT the parity answer. If the owner wants NPC guns louder than Arcade, do it as an ini-toggled runtime hook
   (re/gun_sounds.md section 4; feasible, unverified), not a zip rewrite. Needs an owner choice.
3. Friends / Nexus pack: ship the TOOLS, not the assets. On the player's PC: `python kl_sndonline.py build <out> --dd "<their DD folder>" --force`
   (--force accepts banks whose md5 is in no pin file), after the earlier passes in order: gunraw, fxraw, sndon (tier B), sndon2.
   Undo in reverse order (sndon2 UNDO before tier B's UNDO).

## GUESSes
- `PCMFX` regex `_Crash/` = vehicle crash folders (matched GetawayCar_Crash).
- Head/flat of a stereo clip are judged on (L+R)/2.
- pcmfx "already at target" uses head >= target - 0.6 dB (hard clip + fade lands up to ~0.5 dB under).
- Installer header text still says "staged 2026-10-24 / kl_fxsnd.py" (cosmetic, from the shared writer).

## Live bench must check
Subway/any FA map online: vault explosion and car crash not quieter than a gunshot; wood/plastic breaks; a story-bank level
(campaign) glass hit and bullet impacts level with the guns; no clipping crackle on explosions; Retomoto window blast acceptable
at -1.7 dB; nothing else got quieter. Undo returns the previous sound.
