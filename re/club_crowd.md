# Last Call crowd and calm (DM05A), 2026-10-24

Owner: "last call club still empty, needs to be full to the brim with NPCs ... maybe you start with no guns out and when you
pull the gun out thats when they get aggro".

## Part 1 - why it was empty, what changed
- Live DM05A (zip md5 899684f7) held 10 civilians (Civ_FA_000..009, model 54304) among 67 actors / 39 squads. A civilian stands
  until a player enters her tbCivRunToGate box (half extents = alert, 1200) and then runs; ten in a map this size read as empty.
- `tools/kl_club_crowd.py build <live folder> <out>` adds 40 more of the same proven form (kl_fa_civs.add: 8 entities, 1 actor,
  1 squad each) with plan_places on the nav mesh (part 7: ground y 40 and upper floor y 460, 100 apart, 150 clear of LevelBound
  boxes, clear of every START spawn) and a SMALL run box (alert 450) so the crowd stands instead of stampeding. kl_fa_civs.check:
  0 FAIL. Result 107 actors / 79 squads, zip md5 66bee1f5ca2882aba6d5fb1a4ddc423f.
- RISK (GUESS): the largest build proven live is 99 actors / 55 squads; stock Last Call has 148 / 90; the tool's envelope is 147 / 500.
  107 / 79 is past the proven point. If the club crashes or stutters, rebuild with `--count 25` (about 92 actors) first.
- NOT done: a civilian-model variety (one model, 54304, like the live ten), civilians on the roof / third floor (y 364 holds 5 places only).

## Part 2 - guns holstered, calm until the draw: NOT SOLVED
Searched: no ZSneakTrigger / ZShootAtTrigger / psycho / squad-command trigger class in any Dog Days or Dead Men .prp, so no data
form reacts to a drawn weapon. The police byte [player+0x2723] makes team-Ally soldiers ignore the human but the bots (team 2)
then shoot him and every hook that reads the byte (klfed, klbalance, klchar, kltalk) would take him for a cop: rejected.
[player+0x920] (item in hand, 0 = empty) is only known to dim the HUD; it is not known to be a holster state, so writing it is
a guess with a crash risk. Sleeping the guards (ZSquadScript field 3 = 0) makes them absent, not unaware.
What is shipped: `klhook/klclubcalm.c`, a READ-ONLY probe ([ClubCalm] Enable=0, Shots=1, Every=250). It logs the human's hand item
and selected item when they change and when his fired byte goes up. One live round on DM05A with Enable=1 answers: is the hand
ever empty at the start, what a draw looks like, how long until the guards fire. An Act= switch comes after that, on facts.

## Mod options (rows to add where tools/kl_mod_options.py exists; this branch predates it)
- feat('clubcalm', G_TOOLS, 'Last Call: log the hand / shots (probe for the calm-until-drawn idea)', 'off', 'start', ..., [ClubCalm] Enable=1/0)
  recommended off (a probe, changes nothing). The crowd itself is map data, not a hook feature: undo = UNDO crowd 1024club.bat.

## Hook note
This worktree is older than the live hook (k29b has [CarDown], k27c the Alt+F4 watch). `klhook/out_3f_1024k30club` built from it
compiles clean but lacks those, so it must NOT be installed. Take klclubcalm.c plus the three klhook.c lines (#include after
klcensus.c, `klcc_tick(game_thread);` before klvis_tick, `klcc_init();` after klcs_init) into the current main and rebuild there.
