# Retomoto: leaderless crew misses the last van when the human is a fed (L83, 2026-10-18)

Offline study (no game run). Evidence: L83.log (3f, KLJoin e8c41f20, hook out_e5_1018za, PT_DM09_lead). Every guess is marked GUESS.

## What happened
- Human died at ~70 s, FED at 23:07:51. FedSkip applied: no crew jump. Hop 2 carried bots 1, 6, 2 to the street; bot 5 sat at hop 5's From.
- Last vehicle called 23:11:52 (44.94 s left), waited 8 s (stock), left 23:12:07 with nobody. All 7 AI were 151-237 m from the van.
- Only bots 7 and 4 got stage 3 (BoardAll) and turned traitor. Round ended 23:12:25.77.

## Answers from code (klhook/klmove.c)
- Is any hold keeping the van for a fed human? No. klmv_crewhold (1132) returns on `!criminal` and needs the human aboard (status 4) or CrewRouteAlone status 0; klescort FollowOut needs the human's stage 3 and kle_criminal(). In L83 CrewRouteHold=45 and FollowOutHold=45 were inert; only FollowOutShield acted.
- VanCallLast (klmv_vancall ~1644, uses [rules+0xe8a]): calls every loyal in-play bot at stage 1..2 to stage 3 on the last vehicle regardless of the human, after VanCallDelay. It was NOT set in L83. It sends no walk order; the board tactic must path the distance (GUESS that it paths 150 m).
- The 8 s wait is stock (not a mod key).
- Bot speed 3.3-4.1 m/s (re/bots_follow_out.md): 151-167 m = 37-51 s, 237 m = 58-72 s. Bots in the tower (4, 5, 7) cannot make it (3D distance includes ~200 m height).
- The end timer [rules+0x200] does not cut a held vehicle (states 1..6); a held van postpones the round end. The true END timer was probably ~33 s, not 44.94 s (GUESS, no log line).
- LastVehicleLead=600 gives only ~15 s over 450 (clamp 600 tenths).

## Smallest change set (plan)
1. NEW opt-in key `[Bots] CrewRouteFed=1` (klmove.c, default 0, behaviour unchanged when absent). With it klmv_crewhold runs when the human is a fed (`!criminal`), whatever the human's status, IN ADDITION to the old aboard + criminal case (e5 review: first draft replaced it, which would have dropped the hold for a living human aboard). Everything else (timer < KLE_HOLD_AT 2.0 s, +5 s steps, CrewRouteHold budget, damaged/paid refusals, kle_hold_guard) is unchanged. GUESS: kle_boarding() and kle_hold_guard() work with a fed human.
2. `CrewRouteRange=300` so bots 150-240 m out that move count as walking (default 100 never matched).
3. `VanCallLast=1` so stage 1/2 bots are called on the last van (bots 5/6/2 etc.).
4. `LastVehicleLead=600` (max) for earlier call.
5. CrewRouteHold=45 budget: covers the 37-72 s walk when added to the 8 s wait (GUESS: bots keep walking, not fighting; fedkit Hunted orders compete with walk orders).

Not done: moving the KLJoin [CrewHop.*] To places closer to the van stop (-1567,-40,9300; boarding box -1769,79,9030). The To places are ~150-175 m out; the coordinate order of the CrewHop.6 lines in e8c41f20 differs from the Gate lines, so a nearer set needs a verified map first (GUESS: z 5500-7500 near x -1850). No kl_rt_joinini flag added.

## Files
- klhook/klmove.c md5 6850c484dc3d84e5addf14ae9db3eb01 (4 lines: struct field crew_fed, condition in klmv_crewhold, parse in klmv_read, startup log). NOT built, not committed.
- C:\kl_build_1018\rt_fedvan\PT_DM09_fedvan.ini md5 e21001ed2dbb7027d0a0efa9b2f47158 (diff vs lead: LastVehicleLead 600, CrewRouteRange 300, CrewRouteFed=1, VanCallLast=1).

## For 3f (their files, not edited)
- Needs a hook build including the klmove.c change. klescort FollowOut stays gated on the human's stage 3; a proposal would be an equivalent fed bypass in kle_follow's signal gate (~1113), GUESS.

## Expected log lines
- Startup: `crewhold: CrewRouteFed=1: while you are a fed ...`, `vancall: VanCallLast=1 ...`.
- On the last van with a fed human: `vancall:` calls for stage 1/2 bots; then `crewhold: the vehicle would leave in X s and N of the crew walk (the nearest Y m out): timer ... -> ...`.
- Failure forms: `crewhold: ... is NOT held: no called crew in play walks within CrewRouteRange` or `used up`.
- Success: a bot boards (stage/board lines) before the van state reaches 5.

- Review fix: the NOT-held log line says "a fed (CrewRouteFed)" instead of "in play (CrewRouteAlone)" when CrewRouteFed=1 (klmove.c, cosmetic; md5 now see review).
