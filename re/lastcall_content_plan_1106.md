# Last Call (DM05A, live F01 slot, zip e6d2f73e) content asks: staged plan, 2026-11-06 (offline research, nothing run/installed)

Owner ask source: re/open_work_log.md:81 (2026-11-05 18:30). Live = Last Call chain c8dd18ee (life -> fight --force -> heli --force; log :53)
+ glass 3f0018b3 + pd2guns + buttons + pics = e6d2f73e. So asks 1,2,3,5,6,7 were ALREADY built in the chain and are live; ask 8 is staged but
NOT live; ask 4 has no pass at all. What is missing for 1-3,5-7 is a live look (no owner/bench verdict on the looks recorded).

## Cross-cutting rules (apply to every item)
- Pass shape to copy: tools/kl_club_doors_1106.py (md5-pinned stage, idempotent, edit-by-name, install.py + UNDO, `--dry`), driven by kl_scene/kl_fa.
- Order: chain -> glass -> pd2guns/buttons/pics. Any new pass must pin e6d2f73e (the live pin), not c8dd18ee, and be rebuilt into the bots sibling
  (kl_bake_siblings.py: plain zip + bots zip + base.md5 + Int16Ok in one transaction). Prior "instead of chain" stages (doors 803a29c8) are stale vs live.
- Any pass that changes .prm chunk count must rewrite Entries= in KLJoin.ini/KLGuns.ini (kl_fa_fedbody check). Never touch .LOC (cap 600,000 B,
  engine_facts.md:34-40, crash 0x7fef36/0x926b40). dmlines --fed / gunpics not idempotent: skip when no .LOC/picture change.
- Memory ceiling: census 130 actors / 73 squads proven; 147/110 failed on memory (club_fight_1105.md:7). DM05A is near the VA limit (log ~1700-1745,
  MapCap 60 / nvd3dum pile): every added actor or texture must be paid for.
- Post-pass checks: debug/check_passes.py (A,B,C1-C3), tools/kl_entries_check.py, tools/klt_audit.py, kl_club_budget (382 s of 360 s pre-existing), kl_tests.py.

## 1. NPC variety (women in suits, club-goers, different bodies and voices)
- Exists: tools/kl_club_life_1105.py (re/club_life_1105.md). 40 crowd civilians go from one man (41803 v1) to 9 looks incl. 12 women (F08 model, +6 TEX,
  +3.5 MB .TEX), female voice pair (female, female_02). `--wide` adds a 2nd woman look (+5.8 MB .TEX). Guards/cops: only fedbody (player bodies) exists;
  guards' bodies are NOT varied by any pass (grep: kl_fa_civs.py handles civilians only; stock Enemy models are fixed per actor class).
- Smallest change: nothing for civilians (live). For guards/cops: swap the model field of existing ZSoldier/Enemy actors among bodies the .prm already
  holds (same trick as the civilian look pass, kl_chars.put registers models), via a new small tool modelled on kl_club_life_1105 civilian section.
- Risk: new model chunk = loader 0x8ad7c0 pools and 0x64a856 reader assert if a chunk is half-registered; no-skeleton-match T-pose/invisible head (GUESS list
  club_life_1105.md items). Memory +3.5 MB TEX per look. Voice slots only 2 male + 2 female sets exist.
- Verify: first view stills (D3dShotPost=1 + ReShade Bridge=1, as lclive1106 probes, kl_bench_1106.py:128-133) in the crowd area; kit `lclive1106` solo
  (stage=None, folder byte-identical). Probe lines: `pos at-60s` plus a new `ents` of civilians' model ids. No crash, 2nd round loads (parts `online`).

## 2. Street ambience (car noise just outside)
- Exists: club_life_1105.md Findings: bank already holds F07 traffic sets (car_horns, truckbus, car_idle, mopeds, squeals, sirens_short); the pass repurposes
  7 roof-hum ZSNDOBJ emitters to a Streetbox emitters (x -1500..3200, y 250, z -3000..-4300), .SND +1776 B. Tool kl_ambience.py (359 lines, re/ambience_1023.md)
  is the generic precedent.
- Smallest change: none unless the live look says silent; then tune: Streetbox extents / emitter flag / limiter fades (GUESS 1-4 in club_life_1105.md),
  edit .prp ZSNDOBJ + same translation in .gms (both are written, the exe reads .prp).
- Risk: low (sound-only, .SND pure addition checked by S.verify). Bank is `F01_Main_LS.SND` (pinned b6fdd4c0); a wrong sound offset can crash in the mixer
  (see re/ambience_1023.md); one-shot sets would play once only.
- Verify: no bench can hear it. Cheapest proxy: log of sound starts if klhook has a sound probe (grep klhook for "Sound" log); otherwise owner ears.
  Kit lclive1106 for the no-crash part.

## 3. Music with no dead spots
- Exists: club_life_1105.md adds the 3 missing rooms (`Inside_CarShop_01a`, `_Stairs_01a`, `_Daughter_Room_01b`) to the muffled layer's SoundLimiterFade
  "on" list (14 of 17 were covered). Earlier: kl_club_music.py / kl_club_music2.py (boost +6 dB, DM OST bed). Check tool tools/klmusic_check.py.
- Smallest change: none; if gaps remain, add the room node refs to the same on list (.prp only).
- Risk: low; adding list entries changes slot ids only if entities are added (they are not). Boost package A touches the bank mixer floats (GUESS: +6 dB).
- Verify: owner walk entrance -> wardrobe -> stairs -> car shop -> daughter room. Offline: klmusic_check.py on live zip (run it first, cheap).

## 4. Player spawns on the 2nd floor
- Exists: nothing for 2nd floor. Current START rows: 8 in Yoko's office (x 2700..3050, z 2420/2560, y 342), TRAITOR 4 east of the desk, AFTER_DEATH on the
  pavement slab (club_campaign.md:459). Loot floor is y 341; the F2 fight squads spawn near y 460 (-3146,460,-299 west end; fight_1105 notes).
  Spawn table and facing: kl_fa_author.py:125 (SPAWN dict), writer 1013, report 1044. Spawn rule: ZSpawnPoint looks along local +Z (kl_fa_author.py:67).
- Smallest change: edit-by-name move of the 8 `eSPAWN_TYPE_FRAGILE_ALLIANCE_START` (and UCC/TEAM_MERC sets) node translations to a free, on-mesh 2nd floor
  spot (use kl_route.stations / the nav check used in club_campaign.md:551: on mesh, free floor within 30, in no bound/kill box). No entity added.
  Note the floor-2 guard squads (F2_Hold/Flank/Shot) must not wake on top of the spawn: keep the START spot away from the squads' posts, or re-time them.
- Risk: spawn inside LevelBound/kill box (instant death/assert chain), spawn off-mesh (fall; 0x5e4a22 node >1e6 units assert if falling forever, engine_facts.md:25-28),
  hook code that assumes start positions (klfed/klescort use spawn for bot follow, check grep "START" in klhook), and Yoko's office is the Arcade bots' gather point.
- Verify: new kit `lc2fspawn1106` in tools/kl_bench_1106.py KITS (clone lclive1106 with stage=...), probes `pos spawn` (line 101) compared to expected
  floor y within 5, both seats online (`pos` of seat 2 must differ from seat 1 and be on the mesh), `faults` 0, round 2 reached (restart reuses spawns).

## 5. Roof squad with its own personality
- Exists: kl_club_fight_1105.py:301-317 edits OldWaves!Roof_R1..R3: R1 hold tight + covers, R2 push forward after 60 s, R3 side-step/flank after 75 s;
  Fight!Roof1..3 get chains (re/club_fight_1105.md:15-19). Roof geometry: kl_club_roof.py (327 lines). Shotgun role: F2_Shot (2 Hawk, eUnleashed).
- Smallest change: none unless looks flat live. To add flavour: give Roof_R3 a shotgun loadout by cloning an existing shotgun Enemy actor (no field edit) and/or
  eUnleashed field 0 (ZSquadScript) for R2. Only edits of fields in existing squads (no actor added) keep memory flat.
- Risk: Roof targets are polygon-middle fallbacks (no strip at -900 cm): guards can hang; eUnleashed/UseCovers values are GUESS (fight_1105 GUESSES);
  cloned actors add to the 130/73 census (memory). Bot AI crash class: Loot/Board coroutine sites 0x7bc7d0/0x82f970 only for heisters, not guards.
- Verify: lc1106-style solo with `ents` probe of the roof squads at 60/75/90 s and positions over time (pos lines) showing hold vs advance vs side-step;
  parts `solo`. Nav stalls show as constant positions across two probes.

## 6. Front assault that rushes to cover
- Exists: Fight!Rush (3 SMG) spawns on the front lane (-65,20,-1307), released at 20 s, Defend eDMS_Run into the foyer, then runs to cover boxes;
  Wave_2/4 run to cover boxes (club_fight_1105.md:8-18). Cover infrastructure: kl_fa_cover.py, kl_cover_pass.py, kl_cover_vet.py; DM05A has 93 KL_CoverSix boxes
  but the audit found 25/93 bad (23 no floor at stand point, 11 no nav in front, log ~1541), and COVER9: our boxes ARE cover records but the player query rejects
  exact spots (log ~1521); the restage with safety filters (4a6799a1 era) was before the chain: verify the chain's cover set is the vetted one.
- Smallest change: re-run kl_cover_vet.py against the live zip; only retarget the Rush/Wave runners to vetted boxes (field 7 chain), no entity change.
- Risk: street y 20 vs building mesh part: path may not cross (fight_1105 GUESS); cover-camera pool leak on 0x19->0x16 restarts (COVER6 assert 0x60a5bf /
  crash 0x586eb4, log ~1539: second MissionFailedReload in one load crashes); eCOM_UseCovers unproven for OldWaves.
- Verify: kit lclive1106 (or lc1106 clone) with `ents`/`pos` probes of Rush members at 20/25/35 s: they must enter the foyer and stop at box positions;
  a hold at the street = path break. Also bench COVER-style run with 2 direct 0x19->0x16 restarts (as the 10-26 COVER6 pass) for the crash class.

## 7. Guards in front of the loot room
- Exists: Fight!Loot (3: shotgun + 2 rifles, tight + covers) in the corridor between the two daughter-room doors at (2300,362,3330), in the world from load
  (club_fight_1105.md:11). Loot stacks stand 70 cm above y 341.
- Smallest change: none; if the look is wrong move the 3 actors' posts (edit-by-name, positions on mesh). Doors pass (item 8) places a kick door each side of them.
- Risk: guards stalled behind a PathBlocker of the door pass (item 8 risk); they alert early and wreck the Arcade bot timing (budget 382 of 360 s).
- Verify: lclive1106 solo `ents` probe near (2300,362,3330) at spawn+30 s: 3 live Enemy actors within 400 units; count stays after a round-2 reload.

## 8. Kickable doors on the way to the exit
- Exists: tools/kl_club_doors_1106.py (stage C:/kl_build_1024/lastcall_chain_doors_1106/stage, zip 803a29c8, bots 22a036e0): 4 virtual doors via kl_interact_graft
  (daughter A+B at x 2500/1500 z 3433, storage Firedoor_03, roof Firedoor_02), heister kick steps (KickDoorBehaviourRout x47, 41 NEXT redirects), .prm 54305 -> 54378,
  Entries rewritten. Stock model: DD F03 KickableDoor group; precedents kl_bots_kick_1025.py, kl_doorfix.py/kl_doorfix2.py, kl_doors2_stage.py (DM01/DM02/DM03A).
  NOT installed, never run live. Pinned to the pre-glass chain: STALE against e6d2f73e.
- Smallest change: re-run kl_club_doors_1106.py stage with its input = the live zip and its pin e6d2f73e (src arg), then the bake_siblings; consider the doc's own
  fallback (cut DOORS to B01 + A02) to cut risk. Enemy squads have no kick step: either the doors open for them (add the step) or leave two doors only.
- Risk: new .prm chunks (73) = Entries mismatch crash if forgotten; PathBlocker stalls guards at fire doors; door look/trigger/hinge unproven; +1388 slot ids renumbered
  (octree/rmi/rmc must follow; tool self-checks); memory +73 chunks. Door/leaf coordinates are nav-eroded (jamb a few to 30 cm wider).
- Verify: new kit `lcdoors1106` (stage=doors dir, tag=.before-1106doors), parts online; probes: heister bot positions crossing z 3360 at x 1500/2500 with no stall
  >10 s, an enemy `ents` probe near the storage and roof fire doors, `faults` 0, round 2 reload. Human kick test is owner-only (tap E at the leaf).

## Ranking (cheapest/safest to riskiest)
1. Street ambience (2): live, sound-only, tune only on report. 2. Music dead spots (3): live, run klmusic_check.py, .prp list edit at worst.
3. Loot guards (7): live, re-post only. 4. Front assault (6): live; re-vet cover boxes (known COVER6/9 history). 5. Roof squad (5): live, field tweaks.
6. NPC variety (1): civilians live; guard/cop bodies need new model plumbing (T-pose/chunk risk). 7. 2nd-floor spawns (4): small edit, but bound/kill-box and
fall-assert risks and wake-up collision with floor-2 guards. 8. Kick doors (8): new .prm chunks, Entries, 1388 renumbered ids, PathBlocker stalls, rebase on e6d2f73e.
First move that costs nothing: one lclive1106 live look (owner present) with stills + `ents` probes to see which of 1,2,3,5,6,7 already satisfy the owner.
