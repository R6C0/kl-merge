# AI heister squad builds (`<work>\build\b_bots\M01 M02 M06 M03`): adversarial review

2026-10-10, agent b-verify. Reviewed: `tools/kl_fa_bots.py`, `re/bots.md`, the four delivered folders, against
`<work>\build\z_maps\<map>` (their sources) and the stock levels F01 (KL_PortBackup) .. F09.
**OFFLINE: the game was not started, nothing was installed, nothing written outside this file.** No bot of these
builds has been seen in the game by anybody; "works" below never means more than "no fault found in the files".

Words: **reproduced** = I ran it and got the implementer's result; **measured** = my own script on the files;
**read** = disassembled at the address given (`debug/dasm.py`); **not checked** = said so.

## 0. Verdict

| build | file integrity | would I let the owner load it? |
|---|---|---|
| M01 | no fault found | Yes, FIRST of the four, after the lead's 90 s load check - and after `z_maps\M01` itself has loaded once (5.1) |
| M02 | no fault found | Yes, after M01 has shown bots walking. Carries the source's 3 preflight RISKs (ZEnvSampler, SoundSpline) |
| M06 | no fault found | Yes, after M01. First build with the never-hidden `AllyEscapeBox` (D4) |
| M03 | no fault found | Load: yes. Play: LAST, and tell the owner beforehand what it does (bots stop in the yard and vanish; D4, D5) |

I could not refute the claim at the level of the files: every check of the implementer reproduces, and my own
comparisons (sections 2, 3) found nothing dropped, nothing mis-pointed, no member grown. What remains are
**gameplay risks no offline check can settle** (D1, D4, D5) and **statements in `re/bots.md` that are not true**
(D2, D3, D6, D7). None of them is a reason not to load; D1 is a reason to expect the escape vehicle early.

## 1. The implementer's own checks, run again (all reproduced)

| | M01 | M02 | M06 | M03 |
|---|---|---|---|---|
| `kl_fa_bots.py check` | PASS 0 FAIL 0 NOTE | PASS 0 / 0 | PASS 0 / 1 | PASS 0 / 8 |
| `kl_fa_bots.py diff z_maps b_bots` | only the squad was added | same | same | same |
| `kl_maps.py audit` | PASS, 1 known | PASS, 6 known | PASS, 6 known | PASS, 0 known |
| audit RESULT / RISK lines against the source's `audit.txt` | identical | one NOTE fewer, RISK 3 = 3 | one NOTE fewer, RISK 2 = 2 | identical |
| `kl_voice.py heisters <zip> merged` | findings: none | none | (not run) | none |

The four large blocks (bytes, `kl_fa_bots.py sizes`, before = `z_maps`, after = `b_bots`; all four equal):

| | .prm | .ANM | .fxc | .WAV | chunk-table entries (limit 69,632) |
|---|---:|---:|---:|---:|---:|
| M01 | 55,088,000 | 22,061,764 | 17,760,648 | 21,722,704 | 50,042 |
| M02 | 54,619,216 | 22,202,472 | 17,760,648 | 22,527,568 | 58,371 |
| M06 | 49,585,744 | 21,642,576 | 17,760,648 | 21,775,744 | 46,902 |
| M03 | 60,469,040 | 22,202,616 | 17,760,648 | 22,716,752 | 62,680 |

Members that changed (measured; every other member byte for byte, by the implementer's `diff`):

| | .prp | .gms | .buf | .oct | .prm | .rmi / .rmc |
|---|---:|---:|---:|---:|---:|---|
| M01 | +31,586 | +2,088 | +848 | +736 | 0 (1,107 dwords) | same size |
| M02 | +44,861 | +3,138 | +912 | +896 | 0 (2,293 dwords) | same size |
| M06 | +33,967 | +2,118 | +896 | +704 | 0 (983 dwords) | same size |
| M03 | +34,814 | +2,211 | +944 | +720 | 0 (2,487 dwords) | same size |

## 2. What I tried in order to refute it, and what came out (nothing here is a defect)

1. **Node by node against stock F07** (M01 and M06; every squad node against the F07 node it was cloned from: all
   properties, all controller fields, `.gms` flags / pool group / aux / raw data / light list). Differences are
   exactly the fields `re/bots.md` 2.1 names: places, the actor's model (1749.. -> 9341..), the references of the
   chain, `DefendBehaviourRout[4]` on the way out, `SquadModifierBehaviour[0]` (D2). No `.gms` attribute differs
   on any node. `ZSquadScript` of the squad groups is F07's unchanged: its lists 4..18 are empty, so **no message
   list of F07 is carried over**.
   What a build's squad no longer has of F07's 99 nodes per bot: 9 `RandomTrigger` (the three-way choices), 4
   `TriggerActorsDead`, 4 `TriggerDelay2` (36 s in all), `030_SquadModifier_tight_defense_loot` and
   `040_SquadModifier_Loose_defense`, the hold "on top of loot". Dropped on purpose, said in bots.md; consequence: D1.
2. **A reference that resolves to the wrong kind**: none. `TriggerLootDepleted[0]` names money objects only
   (M01: `AI_Enemies!TheBoss\The_Senator`, `AI_Enemies!BossFlank_01\FBI-Agents_01`; M06: `AI_Enemies!JPN_Boss\Retomoto`
   - each a ZGROUP with `OnlineMoneyCtrl` + `TriggerBox2` and one ZFFActor child, i.e. money ON A PERSON; M02: 20
   ZSTDOBJ + 1 such person; M03: 10 + 1). Stock F07's own list names people of the same form (`...RivalMerc_01`),
   so that is a stock pattern. Timer -> step groups, steps -> `Pos#` boxes, NEXT -> a node with a step controller: all right.
3. **`kl_fa.money_people` locking the bots out of the loot** (it sets `TriggerBox2` field 3 on every money trigger
   of a grafted map, "people only"): read at kl2 0x626f7e..0x626fbb - with byte +0x44 set the box accepts a player
   OR, in Arcade (0x7f6850), an object of the actor class whose `[[obj+0x54]+4] == 2` (team Ally). **A bot passes.**
4. **Stage setter**: read 0x8d2740 (the three kinds push 1 / 2 / 3, no player test) and 0x5dd890 (player branch
   0x6c7700, actor branch 0x78f470, raises record +0x78 only). As the notes say. Whether the box's own machinery
   reports an AI actor at all stays the implementer's ASSUMPTION; I found no data field on the trigger nodes that
   could filter (the controller has two fields: kind and a PIP point).
5. **Trigger sizes half or full extents** (the vertical reading decides whether a bot's feet are inside): stock boxes
   stand with their centre 158 (size y 200), 512 (591), 161 (175) above the floor (F01, F04, F08 ENTERS_BANK), so
   a player on the floor is inside only if the three values are HALF extents. Supported.
   Margins of the builds' places under that reading (worst squad; negative = not inside):

   | | ENTERS (1) | EXITS (2) | BOARDS (3) | exit level (3) |
   |---|---:|---:|---:|---:|
   | M01 | 20 | 10 | -57 | 40 |
   | M02 | 186 | 6 | 14 | 18 |
   | M06 | 55 | -201 (none; said in bots.md) | 66 | 136 |
   | M03 | 26 | 7 | -1125 | -482 (said: stage 2 at most) |

   `check` tests stages 1 and 3 only; stage 2 is as bots.md says. The EXITS margins of 6..10 are vertical: the
   boxes end 6..11 below the mesh's height - the same for the human, who has triggered them in live rounds.
6. **Level bounds**: no route place and no bot inside a `LevelBound` box or one of its warning boxes (3 + 6 boxes on
   M01 M02 M06, 5 + 10 on M03).
7. **A bot on a player start / on another actor**: least distance to a START point 110..126; M01's bot 06 stands 49
   from the parked `Heroes!Henchmen_06\Ground` and bot 04 92 from `Henchmen_04` - stock does the same (a bot 13 from
   a parked hero in F07, 17 in F03, 45 in F01). Not a defect.
8. **Places shared between squads**: M01 stations 6 and 8 and M03 station 9 hold all seven bots on one point.
   Stock squads share places wholesale (pairs of route boxes of different squads nearer than 30: F01 379, F07
   1,093, F08 756). Not a defect (but see D6).
9. **Slot ids, independently** (my own table slot -> scene path + REF, not the tool's): 3,953 / 7,998 / 4,679 /
   6,622 room-tree items name the entity they named, 0 room trees differ, the only new items are 42 / 56 / 42 / 42
   ZGROUPs in tree 3 of the root; `.rmi` / `.rmc` boxes, room pairs and every old light list equal.
10. **`.prm`**: the dwords that differ are 1,107 / 2,293 / 983 / 2,487 (= the tool's counts), each larger by exactly
    the `.oct`'s growth (736 / 896 / 704 / 720). Nothing else.
11. **Round trips of the delivered files**: `kl_scene` rewrite, `.oct` repack and `.prp` reserialize are byte for
    byte; `kl_scene.check` clean; every room tree passes `check()` (the simulation of kl2 0x719850).
12. **Heap budget** (`.gms` +0x1c) left as it was: budget + 0x57800 is 0xe6484..0x10e7d4, under the loader's floor
    0x340000 on all four, so the floor decides either way (if `kl_scene`'s reading of 0x8ad862 holds).
13. **Classes / controllers**: every transition of the chain exists in a stock squad except one (D3).
    `DefendBehaviourRout -> DefendBehaviourRout` is F08's and F09's form (28 each).

## 3. Defects and risks

### D1 (all four; gameplay RISK, the one I would act on) - the bots are much faster than any stock squad, and an actor can call the escape vehicle

- Read, kl2 0x6c3d50 (`ZOnlineExitLevelTrigger` slot 34): the player test at 0x6c3dad only guards the block that
  marks a PLAYER's record; both kinds of activator arrive at 0x6c3e11, where - in Arcade, vehicle state 0
  (rules +0x12c), +0x290 false, +0x17c not 3 - the rules' slot 44 (+0xb0) is called with (activator, the trigger's
  vehicle at +0x48). No player test on that path. What slot 44 does with an actor was NOT read; bots.md's
  ASSUMPTION "it calls the vehicle" is therefore likelier than not.
- Measured, pacing of stock `Squad#02` besides the loot wait: `TriggerDelay2` 63 / 42 / 21 / 20 / 71 / 16 / 36 /
  50 / 46 s (F01..F09) and 3 / 1 / 1 / 4 / 3 / 3 / 4 / 0 / 0 `TriggerActorsDead` (no time limit). The builds: the
  10 s start timer and one 20 s loot wait, then `eDMS_Sprint` to the exit box (route 190..390 m).
- So on M01, M02, M06 a bot can be inside the exit box roughly a minute or two after GO, whatever the human is
  doing; a Dead Men spline car then waits 10 s (bots.md 5.2) and goes. The owner asked for "leave without you" as
  something a bot may do, not as what happens every round.
- Cheap answers, both options of the tool, no new code: `--loot-seconds 60` (F09's value) and / or `--wait-guards`
  (F01 / F07's form; it has no time limit, so a guard the bots cannot reach stalls them). I would build M01 both
  ways and let live check B4 pick. Not a reason to hold back the first load.

### D2 (all four; wrong statement, small data difference) - the last step is not "as F01 F03 F04 F07"

`040_SquadModifier_tight_defense_van` has field 0 = `eLM_Leash`. Measured on the last modifier step of the stock
squads: F03 `eLM_Leash` + `eDM_Tight` (7 of 7); **F01, F02, F04, F07 `eLM_NotSet`** + `eDM_Tight`. The node is
cloned from F07's `100_SquadModifier_tight_defense_van` and then CHANGED away from the host's value. F03 (the
helicopter level that boards by the tactic alone) shows the leashed form exists; what a leash does to a bot that
must still run 150..400 to the boarding box was not read. Safer default: leave field 0 as F07 has it.
Found by: comparing every field of the clone with its source.

### D3 (all four; a combination no stock level has) - `TriggerLootDepleted -> DefendBehaviourRout`

Stock loot waits release a `SquadModifierBehaviour` (F01..F07, 7 each) or a `RandomTrigger` (F08, F09); none
releases a `DefendBehaviourRout` directly. The same message from a `TriggerDelay2` to a `DefendBehaviourRout` IS
stock (F01 F03 F04 F05 F06 F07 F08 F09), and 0x811fb0 sends the plain trigger message, so I rate it low. Also
without a stock twin: a sprinting `DefendBehaviourRout` with a list of 2 boxes and a NEXT (stock: 21 with 3 boxes).
bots.md 8 admits "no stock level has this exact combination" in general; these are the two concrete ones.

### D4 (M06, M03) - the `AllyEscapeBox` is in a form no stock level has; on M03 it is the ONLY way a bot leaves

All 17 stock boxes (F02 8, F06 8, F08 1) are created hidden (`.gms` flags 0x202400,
`ZGEOM[3]` = 1), carry a `PlayerAction` on the same node and are switched on by a script; controller field 4 is
the message name 'Activate'. The builds' box: flags 0x202000, shown, no `PlayerAction`, nobody sends it anything.
bots.md marks "a box that is never hidden ticks" as ASSUMPTION; I did not read 0x907a50's caller either. M06 does
not depend on it (its route reaches stage 3 inside the exit box and the BOARDS box, margins 136 / 66). **M03
does**: no stage 3, no path to the van. If the box does not tick, M03's seven bots stand in the yard corner
(1967, 220, -1073) for the rest of the round. Nothing else is inside either box at the start (measured).

### D5 (M03 only; RISK that exists in `z_maps\M03` already and starts to matter with bots) - the pool of drop stacks hangs over walkable mesh

All 316 `ZMONEYCTRL_TYPE_DROP` objects are parked at (5224, 905, -11057) - the stock parking place (F02 has the
same numbers). On M03 that point is 205 above a polygon (height 700) of the START row's own mesh part, about 65 m
east of the START points. In all nine stock levels and on M01 M02 M06 the pool is off the mesh (measured, 9 + 3).
`ZLootTactic` takes any money object that is not "taken" and that the pathfinder joins to the bot
(`re/bots_squad.md` 4); "taken" is `[obj+0x34] <= 0` (read, 0x4536e0). Whether a parked stack has an amount, and
whether the rules' two lists hold the pool at all, was NOT read. If they do, M03's bots have 316 reachable money
objects in the street. Look in the first M03 round: do bots run east along the street instead of into the bank.

### D6 (M02, M06; wrong statement) - "a shared place never ends a step"

bots.md 2.2. Measured: M02 `Squad#02` and `#03` have the same LAST box of the LAST step
(`033_DefendBehaviour_out\Pos#01`, (-586, 0, -8627)); M06 `Squad#05` and `#06` the same last box of
`030_DefendBehaviour_out` ((-1807, 220, -6579)). Harmless by section 2 item 8; the sentence is not true.

### D7 (all four; gap in `check`, statement to correct) - the voice check does not look at the stream file

`check()` calls `kl_voice.heisters(B.zp, stream=None)`. On these builds EVERY per-character line is a streamed
clip (M01: 624 'stream pcm set' + 208 'stream vorbis' key x heister pairs), so step 9 says nothing about whether a
clip exists. I ran `kl_voice.py heisters <zip> merged` on M01, M02, M03: findings none against
`<work>\build\PC_Def.str`. That is only as good as the `PC_Def.str` INSTALLED in the game being that file (not
looked at: I did not read the Dog Days folder). And for the owner's words "make sure the voicelines for the
characters are there": 78 of 104 per-character keys (M03: 76 of 103) are ONE Dead Men recording for all eight
characters - the seven bots and the human say three quarters of their lines in the same voice. The bots have no
barks (as stock). `re/bots_voice.md`'s list of lines per event (backstab, bribe, left behind) was not re-verified here.

### D8 (all four; process) - two untested things at once

`z_maps\M01..M06` have themselves never been loaded in the game (CLAUDE.md). A fault on the first load of a
`b_bots` build says nothing about the squad. Load the source build first, or keep it at hand as the control;
`--no-tree` (the `.prm` and the `.oct` layout untouched) is the second control.

### Smaller things

- Narrow places: least clearance to a mesh border 13..14 on every M03 squad, 20 on M01 (door strips). Above the
  tool's own floor of 10; stock has 4..24.
- The builds' squads never receive F07's "tight on the loot / loose on the way out" modifiers: they run the whole
  route in the squad script's start mode (`eStayBack`), then leash. Unknown effect on how they fight.
- `re/bots.md` 2.2 "each bot has its own place per station ... as stock": stock squads mostly share places (item 8).

## 4. What no offline check covers (the lead's live checks decide)

1. That a `DefendBehaviourRout`'s NEXT fires at all when its last box is reached - if not, every squad stands at
   station 3 for ever (the first step has no wait behind it). B2 / B3.
2. That gameplay trigger boxes report an AI actor (stage 1: no looting without it).
3. D1's timing, D4's box, D5's pool.
4. The wardrobe: bots share the model of `Heroes!Hero_0N` (9341..); the wardrobe's new roots keep variants 1 / 2 as
   stock (`re/wardrobe.md`), so a bot should look stock - not seen.

## 5. Suggested order for the lead

1. `z_maps\M01` 90 s load (control), then `b_bots\M01` 90 s load, then B2 - B4 of bots.md with H6 logging.
2. If the vehicle comes too early: rebuild M01 with `--loot-seconds 60`, compare.
3. M06 (box + tactic), M02, M03 last.

Scripts (scratchpad `...\1e45a579-...\scratchpad\bv\`): `t1.py` (clone against source), `t3.py` (targets,
triggers, bounds, shared places, sizes, `.prm` deltas), `t4.py` / `t8.py` (stock calibration), `t5.py`
(transitions, AllyEscapeBox forms, stage margins, round trips), `t6.py` (drop pools), `t7.py` (slot ids by entity).
