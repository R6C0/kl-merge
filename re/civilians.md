# Civilians (tools/kl_fa_civs.py), 2026-10-18

Post-step on a finished map folder: `add(src, dst, civs, slot, model, alert, tree, max_prm_growth, seal)`.
No map tool is touched, so default tool output stays byte-identical.

Form (cloned from Dog Days' own civilians): ZGROUP squad (ZSquadScript) + 30_SquadModifier_Deactivate +
20_RunToStreet (MiniCutsceneRout: field 0 script text, field 1 NEXT list) + Flee_NN (ZSTDOBJ + MiniCutPosObject)
+ Civ_FA_NNN group with child Ground (ZFFActor team Neutral + ZCivilian) + tbCivRunToGate (TriggerBox,
eTGS_AllInside) that starts the rout. 8 entities per civilian.

Use: `python tools/kl_fa_civs.py census|plan|build|check|diff|selftest`; build `<src> <slot> <out> <N> --model F07 --seed 18
[--centre x y z --radius R] [--alert 1200]`. Placement = F.Nav mesh points, 60 from walls, 150 apart,
2 flee points 1800..4500 away by path, same floor. `check()` verifies misfits, .prp round trip, script names, trigger, model, room sets.

Model: `auto` (live guard model, no .prm growth, GUESS fits Civilian anims), int (live chunk), `F07` (stock F07 chunk 1794
appended, 55 chunks, +567,264 bytes .prm; recommended).

Limits: live-proven 99 ZFFActor / 55 squads (kl_fa_bank.ACTORS_LIVE); pool chunks 73,728; stock max 60 civilians.
Sealing (kl_fa_bank.seal) is run by add(): new entities take REF ids that parked room-list entries name.

GUESS: trigger values are half extents; ZCivilian's own panic is not read (flee is the rout); `auto` model fits the anims.
Nothing here ran in the live game.

Builds: Last Call 30 civilians (club base 57 actors, ceiling about 34); Vault 24 (base 100 actors/48 squads: 124, above
the live-proven 99, under the 147 envelope: risk). Hot Coffee about 20, check headroom first.
