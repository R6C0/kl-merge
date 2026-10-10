# Dynamic AI heisters: what was built

Agent b-dyn, 2026-10-10 night. Tool: `tools/kl_fa_bots_dyn.py` (its docstring is the short form of this file).
Research it follows: `re/bots_dynamic.md`. **OFFLINE: nothing ran in the game, nothing was installed, nothing was
written into the Dog Days folder. `tools/kl_fa_bots.py` and `kl_fa_bots_rt.py` are not changed: they are called.**

The owner (2026-10-10 evening, Risk=2): "the ai heisters just path the same then die so quick now ... make them
more dynamic give them a bit of personality so they can move a bit more like the bots to the van to escape make
them utilise cover and they know whos infront of them".

Status words: **stock** = some stock Fragile Alliance level has exactly this on a bot (count given);
**GUESS** = a value or choice of ours; **ASSUMPTION** = fits what was read, not proven.

## 0. Short answers

1. **Built, five maps, every gate passes.** `<work>\build\z_dyn\M01 M02 M03 M06` (from `y_loot2\<map>`) and
   `<work>\build\z_dyn\retomoto` (from `rt_full4\retomoto_full`). `kl_fa_bots.py check` PASS x 4,
   `kl_fa_bots_rt.py check` PASS, `kl_maps.py audit` PASS x 4 (0 findings that must be 0), `kl_impact.py`
   problems: 0 x 5, `kl_map_guns.py check` problems: 0 x 5, this module's own check and diff PASS x 5.
   The four large blocks are byte-count equal to the source builds (section 6).
2. **What changed for the seven**: no sprint except the last place (the dash to the vehicle); a HOLD at a cover
   box every 13 - 18 m of the way with a timer of 4 - 12 s (21 - 42 holds a map; the hold places are 127 - 181
   from their box at the median, 93 - 100 % within 2.5 m); a start 0 / 3 / 5 / 8 s apart; a random choice between
   2 - 3 covers at 1 - 6 holds a map; vision factor x 2; loot waits of 15 / the build's / up to 60 s; tight at the
   loot, loose between; one bot unleashed, one with accuracy 90, one who runs. Section 3 says who is who.
3. **Cover boxes did not have to be made**: the builds carry 104 - 479 (section 4). What limits the holds is
   where the boxes ARE: 13 - 32 of the 46 - 79 route places asked for a hold have no free box within 9 m
   (M01's first 100 m are an open car park with three boxes).
4. **No "sticks to the human" bot.** The two routs that could do it (`DefendPlayerPosBehaviourRout`,
   `FollowBehaviourRout`) are in no Fragile Alliance level, and `kl_fa_bots.check` FAILs a controller no
   Arcade level runs. The seventh personality is a second looter instead (section 7).
5. **The gate does not see everything.** `kl_fa_bots.check` walks the first link of every step, so a hold that a
   `RandomTrigger` picks is outside its walk; this module's check puts the same rules on those places (section 5).
   No patch of `kl_fa_bots.py` is needed.

## 1. The step

    python tools\kl_fa_bots_dyn.py build <bots build folder> <out folder> [options]
    python tools\kl_fa_bots_dyn.py owner <work>\build            the five builds above into <work>\build\z_dyn
    python tools\kl_fa_bots_dyn.py check <folder>                kl_fa_bots.check (+ _rt) + this module's
    python tools\kl_fa_bots_dyn.py diff  <bots build> <out>      proof that only the squads' steps differ
    python tools\kl_fa_bots_dyn.py plan | summary | covers | map ...

It reads a FINISHED bots build (it refuses its own output), so after `kl_fa_bots.py` is run again (the van join)
the step is simply run again on the new folder. It does not plan a route: it takes the chain the bots build has
- every place the old steps named, in the old order, every wait (loot, cases timer + relays, rally,
`TriggerActorsDead`), the last modifier, the actors, the AllyEscapeBoxes - and makes the Defend steps between
them anew. Per bot:

    Timer_start_bots -> 000_Timer_stagger -> 001_SquadModifier_awake
      -> NNN_DefendBehaviour_<leg>             'rout': 1..3 way places of the build, eDMS_NotSet
         -> NNN_DefendBehaviour_pos_cover      'pos': ONE place 70..230 from a cover box -> NNN_Timer_hold
         or -> [NNN_Timer_hold, NNN_RandomTrigger_cover -> one of ..._pos_cover_a / _b / _c (no NEXT)]
      -> ... -> NNN_SquadModifier_tight_defense_loot -> the loot place -> the build's loot wait
      -> NNN_SquadModifier_Loose_defense -> ... -> the last place alone, eDMS_Sprint -> the build's last modifier

Written: `.prp`, `.gms` + `.buf` (entities out and in INSIDE the seven squad groups; REF ids of removed entities
are reused; 123 - 211 more REF slots a map), `.oct` / `.rmi` / `.rmc` (slot ids; the squad's groups re-listed in the root's
group tree with the box of their places, as `kl_fa_bots.apply` lists them), `.prm` (only the 4-byte `.oct`
record offsets in model roots). `dyn.json` / `dyn.txt` (the plan with every coordinate, the checks, the diff),
`dyn_map*.png` (a top view: mesh edges, cover boxes, each bot's places and holds - to LOOK at offline) in the
output folder; `steps.json` and `graft.txt` get a line. Every other file beside the archive is copied byte for
byte (`KLTalk.ini`, `KLGuns.ini`, `KLJoin.ini`, `KLWardrobe.ini`, `bots.json` ...: `diff` compares them).

Options (all change only this step): `--no-random` (every hold one cover, walked), `--no-vision`, `--sixth N`,
`--no-rusher`, `--no-stagger`, `--no-detour`, `--gap N`, `--no-tree`.

## 2. Every choice and its stock precedent

Counts are the nine stock Fragile Alliance levels' own bot squads (63 bots), measured with
`scratchpad\dyn\m1.py` / `m3.py`; "police" = other actors of those levels.

| what the step writes | stock | ours |
|---|---|---|
| `DefendBehaviourRout` 'rout': field 0 empty, field 1 = 1..3 boxes, 2 = 1, 3 = 0, 8 = 1, 9 = 0 | 462 bot steps | the build's own way places, regrouped |
| `DefendBehaviourRout` 'pos': field 0 = ONE box, field 1 empty | 540 bot steps (the commonest form) | the hold |
| `eDMS_NotSet` on every step but the last | 1,008 of 1,100 bot steps; six levels have no sprinting bot | - |
| `eDMS_Sprint` on the last place only (the runner: the last two steps) | F01 / F03: a few dashes (21 / 8 of 70) | which step |
| NO other move set (Run, Walk, Sneak, SneakRun) | no bot has one: only NotSet and Sprint are proven for the bots' animation sets Kane_NPC / Lynch_NPC | (the check FAILs any other) |
| Defend -> `TriggerDelay2` -> Defend | 329 and 119 transitions on bots | - |
| timer values 3 4 5 6 8 10 12 s; fields 1..3 = 0.0, -1.0, 0 | every one is a stock bot timer (8 s 51 x, 10 s 65 x, 12 s 14 x, 4 s 28 x, 5 s 21 x, 6 s 14 x, 3 s 14 x) | who gets which |
| sum of a bot's timers 16..85 s | stock: 16..85 | planned <= 85; the runner is below 16 on purpose (NOTE in the check) |
| `RandomTrigger` {1, weights 3 / 3 (/ 3), one target list each} -> a 'pos' step | 322 x RandomTrigger -> Defend pos on bots; weights (3,3,0,0) 147 x, (3,3,3,0) 21 x | - |
| a Defend step with an EMPTY next (the hold a RandomTrigger picks) | 134 bot steps | - |
| **a Defend step whose NEXT names TWO things: [the timer, the RandomTrigger]** | NOT on a bot. Police: F01 `Gameplay!PolicePlatform#01\10_Defend` -> [RunToCover, TriggerDelay] (2 x), F07 `RIGHT_10_MoveToSpotEm` -> 3 RunToCover, F03 -> [GatePath, TriggerCounter]; lists that start several things: 40 stock timers | ASSUMPTION that a bot's Defend step does the same. `--no-random` builds without it (except the hold during Retomoto's rally) |
| `Timer_start_bots` -> a per-bot `TriggerDelay2` (the stagger) | timer -> timer: F03, F04, F07 (not in a bot squad) | GUESS (research recipe 5): 0 / 3 / 5 / 8 s |
| `SquadModifierBehaviour` as a chain link: Defend -> modifier -> Defend, loot wait -> modifier | 196, 63, 49 transitions on bots | - |
| modifier `eDM_Tight` before the loot place, `eDM_Loose` after the loot wait | Tight 84, Loose 36 bot modifiers (F07: 030_tight_defense_loot / 040_Loose_defense) | - |
| modifier `eLM_Leash` + `eDM_Tight` (the rear guard, after its last loot wait) | 7 bot modifiers (F03 F05) | which bot |
| first modifier: `eDM_Loose` + **`eVIM_Factor_2_0`** | the vision factor: Fragile Alliance POLICE only (x 2: 6 squads, x 4: 10); never on an Ally | ASSUMPTION that it works for an Ally squad the same way (soldier+0x74c, re/bots_dynamic.md 4). `--no-vision` |
| `ZSquadScript` field 0 = `eUnleashed` on Squad#02 | stock F08: all seven bots | what it changes inside the tactics was not read (re/bots_dynamic.md 9). `--no-rusher` |
| `ZSoldier` field 4 (accuracy) = 90 on Squad#07 | stock F05: all seven bots (90 50 50 350 50) | health stays 280: the balance dial owns it |
| `TriggerLootDepleted` field 1: 15 (point man, runner) / the build's / the build's + 15, at most 60 (the two looters) | stock: 15, 20, 60 | GUESS for 30 / 35 / 45 |
| the hold place: 70..230 from the box's middle, on the side AWAY from where the bot is walking to | stock bots' hold places lie 165..291 from the nearest box at the median; `DefendCover` takes a cover within 500 of the defend position (kl2 0x84dc90) | GUESS for the side (the engine picks the side of the box itself) |
| `ZSoldier` field 15 stays 1.0, 16 / 17 stay 600000 | every stock bot | field 15 is NOT sight (re/bots_dynamic.md 4): 1.0 does not blind them |

Not used, although the research lists them, and why:

- `RunToCoverBehaviourRout` (stock on bots: F02 7, F04 14, F06 7): its place is a `ZSTDOBJ` with a model
  number; a new one would be a new drawn-class entity whose room-tree membership is not decoded, and its step
  ends only when the bot IS in the cover (0x6fae80) - a place with no reachable cover was not read. The Defend
  'pos' step at a box is the form 9 of 9 levels have.
- `eCSS_Enabled` (sixth sense): off by default. The story uses it on eight scripted guards whose rows hold
  600000 - "knows everybody on the map". `--sixth N` writes N into fields 16 / 17 and switches it on
  (the police rows hold 800); nobody has seen what the unswitched default range is, so 800 could also be LESS.
- `eDMS_SneakRun` / `Run` for a careful bot: no bot has it; the animation set is the risk.
- weapons per bot (`ZFFActor[1]`): not touched - `kl_map_guns` and the gun looks hang on the rifle.
- `TriggerActorsDead`: none made (a wait without a time limit; pairing it with a timer starts the next step
  twice). A build that has one (`kl_fa_bots --wait-guards`) keeps it.
- `FlankingBehaviourRout`, `FollowBehaviourRout`, `DefendPlayerPosBehaviourRout`, `eCM_FollowP1`: story only.

## 3. The seven

Squad#0N is character C(N); the digit is also the bot's voice. Every number is a stock bot value (section 2);
which bot gets which is ours.

| squad | role | start | hold (in / out) | cover it prefers | loot wait | else |
|---|---|---|---|---|---|---|
| #02 | **point man** | +0 s | 5 / 4 s | the box furthest AHEAD | 15 s | attitude `eUnleashed`; chooses his boxes first |
| #03 | **looter** | +3 s | 8 / 6 s | the nearest | build + 15 (max 60) | - |
| #04 | **flanker, one side** | +3 s | 8 / 6 s | boxes to one side of the way | the build's | takes THE OTHER WAY ROUND where the mesh has one |
| #05 | **flanker, other side** | +5 s | 8 / 6 s | boxes to the other side | the build's | - |
| #06 | **second looter** | +5 s | 10 / 8 s | the nearest | build + 15 (max 60) | - |
| #07 | **rear guard** | +8 s | 12 / 8 s | the box furthest BEHIND | the build's | accuracy 90; leashed + tight after the last loot |
| #08 | **runner** | +0 s | 4 / none | the nearest | 15 s | no hold on the way out; sprints the last TWO steps |

- Who holds where: a bot asks for a hold when it has walked `GAP_IN` 1300 (way in) / `GAP_OUT` 1700 (way out)
  since its last one - the first time x its phase (0.5 .. 1.5), so the seven do not stop at the same places.
- A cover box belongs to ONE bot for the whole round (stricter than the research's "not at the same step");
  boxes are handed out point man, rear guard, the flankers, the looters, the runner - one a hold first, then
  what is left as the RandomTrigger's alternatives.
- "The other way round" (#04): between two fixed places (a trigger box, a loot place, a gate, the last place)
  the plain way places are laid along a second mesh way if one exists that avoids the polygons of the shortest,
  is at most 1.6 x + 6 m longer and lies 5 m off it somewhere. **Found once: M03 (2 places).** The other maps'
  ways are corridors or one wide polygon strip - on those the seven still share the build's 1.1 m lanes;
  what differs is where and when they stop. GUESS all of it.
- Two-part map (Retomoto): no hold and no long loot wait on the tower's way OUT. A timer still running there
  when the human takes the jump would start the next TOWER step for a bot the hook has put in the street.
  (The build's own loot wait has that property already; this step does not add to it.)

## 4. Cover data

`CFFCoverList` (kl2 0x6d6a80) makes a cover of every `ZSTDOBJ` named `*coverbox*` unless its flag bit 0x400
is set. Counted that way (`kl_fa_bots_dyn.py covers <folder>`):

| build | high | low | hidden (left out) | boxes with a holdable place | holds asked / found | no free box within 9 m | boxes in reach all refused |
|---|---:|---:|---:|---:|---:|---:|---:|
| M01 | 64 | 76 | 0 | 109 of 140 | 58 / 33 | 20 | 5 |
| M02 | 133 | 49 | 0 | 173 of 182 | 79 / 42 | 13 | 24 |
| M03 | 59 | 45 | 0 | 98 of 104 | 68 / 27 | 30 | 11 |
| M06 | 174 | 86 | 0 | 174 of 260 | 46 / 21 | 24 | 1 |
| Retomoto | 304 | 175 | 1 | 465 of 479 | 65 / 21 | 32 | 12 |

Why a box is refused: no short way to it on the mesh (the other side of a wall: 9 - 21 a map), too near
another bot's hold, across the escape vehicle's road (M03 11), in or across the van's lane / in a level exit
box (Retomoto 5 + 4). **No cover box was generated**: the research (3.3) shows a box is a named `ZSTDOBJ` with
a model, and where one would be put in open ground (M01's car park, M06's lawns) cannot be seen offline -
a box in the open is not cover. If the owner wants more stops there, the boxes should be placed by eye.

Every place a bot's Defend step names against the nearest box (the research's measure), before -> after:

| | places | median | within 5 m | within 2.5 m | the hold places alone |
|---|---|---|---|---|---|
| stock bots F01..F09 | 112..322 | 165..291 | 61..100 % | 31..94 % | |
| M01 | 91 -> 131 | 473 -> 283 | 54 -> 68 % | 27 -> 50 % | 40, median 127, 100 % within 2.5 m |
| M02 | 140 -> 189 | 449 -> 376 | 62 -> 72 % | 13 -> 35 % | 49, 160, 100 % |
| M03 | 112 -> 140 | 487 -> 356 | 54 -> 62 % | 25 -> 39 % | 28, 160, 96 % |
| M06 | 98 -> 122 | 384 -> 348 | 77 -> 81 % | 23 -> 39 % | 24, 181, 100 % |
| Retomoto | 182 -> 212 | 445 -> 417 | 60 -> 66 % | 9 -> 21 % | 30, 163, 93 % |

(The way places are still the build's; a bot does not stop at them - it stops at the holds, the loot places
and the last place.)

## 5. Checks

`kl_fa_bots_dyn.py check <folder>` =

1. `kl_fa_bots.check` (and `kl_fa_bots_rt.check` when a squad has a second chain), unchanged, on the folder.
   They walk the chain by the FIRST name of every step, so they see every rout, every single-cover hold, every
   wait - and the rules of the route (on the mesh, clearance, a path in order, level exit boxes before the loot
   wait, the vehicle's lane, heist stages, the AllyEscapeBox, the drop link, the cases) hold for those.
2. What they do not see: a hold started BESIDE the next link (a RandomTrigger's alternatives, the hold during a
   rally). For each: on the mesh part of the place before it, clearance, not on a warped polygon, a path of at
   most 15 m from that place and a path on to the next, never in or through a level exit box earlier than the
   route itself is, not in the vehicle's lane; a hold beside something that is no timer FAILs.
3. Every hold within 500 of a cover box (FAIL; NOTE above 260); no two bots' holds within 60 of one another.
4. Move sets (only NotSet / Sprint), timer fields, modifiers (only the five sets stock bots have + the vision
   factor / sixth sense), steps nothing starts, RandomTrigger weights against lists, a timer behind the last
   loot wait of a chain the jump cuts off (FAIL), the four large blocks against `dyn.json`.

`kl_fa_bots_dyn.py diff <bots build> <out>`: every entity outside the squad equal (record, order, REF id), the
squad's kept nodes equal but for NEXT lists / loot seconds / `ZSquadScript[0]` / `ZSoldier[4]`, room trees
equal by entity but for the squad's groups in the root's group tree, collision records and tail equal, `.prm`
only record offsets, the other 20 members and every file beside the archive byte for byte. RESULT on all five:
"only the squad's steps were made anew".

One line of `kl_fa_bots_rt.check` reads differently now: "hold after place N (S s)" names this step's first
hold timer of the street chain, not the rally. The rally timer is still in every chain, before the level exit
box (kept node `070_Timer_rally`); the rule the line belongs to (no place in the box before the first wait) is
the weaker for it, and this module's rule 2 covers the holds.

## 6. The builds

| | entities out / in | squad nodes | members changed | `.prm` | `.ANM` | `.fxc` | `.WAV` |
|---|---|---:|---|---:|---:|---:|---:|
| M01 | 126 / 315 | 358 | .buf .gms .oct .prm .prp | 55,917,968 | 22,061,764 | 17,760,648 | 21,722,704 |
| M02 | 203 / 414 | 499 | (same) | 55,449,184 | 22,202,472 | 17,760,648 | 22,527,568 |
| M03 | 161 / 284 | 321 | (same) | 61,299,008 | 22,202,616 | 17,760,648 | 22,716,752 |
| M06 | 147 / 313 | 371 | (same) | 50,415,712 | 21,642,576 | 17,760,648 | 21,775,744 |
| Retomoto | 252 / 383 | 434 | (same) | 79,879,056 | 21,642,904 | 17,760,648 | 27,802,960 |

The four sizes are the source builds' own, to the byte (`kl_fa_bots.py sizes`, both sides). New classes: none
(ZGROUP and ZBoxPrimitive, as the squad had); new controllers: `RandomTrigger` (1 - 6 a map; stock F07 runs 63 on its bots).
Steps made: 90 - 139 Defend steps, 23 - 47 timers, 21 - 63 modifiers a map.

Per bot (holds / of them by RandomTrigger / seconds of timers / loot waits):

| | #02 point | #03 looter | #04 flank | #05 flank | #06 looter 2 | #07 rear | #08 runner |
|---|---|---|---|---|---|---|---|
| M01 | 7 / 1 / 34 / 15 15 | 5 / 1 / 43 / 45 45 | 5 / 1 / 43 / 30 30 | 4 / 0 / 35 / 30 30 | 4 / 2 / 45 / 45 45 | 5 / 0 / 64 / 30 30 | 3 / 0 / 12 / 15 15 |
| M02 | 10 / 0 / 49 / 15 15 | 7 / 3 / 55 / 60 60 | 6 / 0 / 49 / 45 45 | 7 / 1 / 57 / 45 45 | 5 / 0 / 53 / 60 60 | 5 / 0 / 62 / 45 45 | 2 / 0 / 10 / 15 15 |
| M03 | 7 / 0 / 33 / 15 | 3 / 0 / 23 / 35 | 5 / 1 / 41 / 20 | 2 / 0 / 19 / 20 | 5 / 0 / 51 / 35 | 4 / 0 / 52 / 20 | 1 / 0 / 4 / 15 |
| M06 | 6 / 0 / 29 / 15 x 4 | 2 / 0 / 17 / 35 x 4 | 4 / 0 / 33 / 20 x 4 | 2 / 0 / 19 / 20 x 4 | 3 / 1 / 31 / 35 x 4 | 4 / 1 / 52 / 20 x 4 | 0 / 0 / 0 / 15 x 4 |
| Retomoto | 9 / 3 / 43 / 15 | 1 / 1 / 19 / 30 | 2 / 0 / 25 / 30 | 3 / 0 / 27 / 30 | 2 / 1 / 31 / 30 | 4 / 1 / 42 / 30 | 0 / 0 / 10 / 15 |

(M02's timers include the two 1 s cases timers of the build, Retomoto's the 10 s rally.)

## 7. What each bot does, step by step

From `kl_fa_bots_dyn.py summary <folder>`; the same with every coordinate and box path is `<folder>\dyn.txt`,
the picture `<folder>\dyn_map.png`. "walk n places" = a rout step over n of the build's way places;
"-> cover X s" = then a hold at that box for s seconds; "one of A / B / C" = a RandomTrigger picks per round;
[..] = a squad modifier. Box names repeat (every room has its own `CoverBoxH_01`).

### M01 (diner)

- **#02 point man**: [loose, vision x2]; walk 2 -> cover Dumpster 5 s; walk 1 -> cover H_08 5 s; walk 1 -> cover M_04 5 s; walk 1 -> cover H_01 5 s; walk 1 -> cover, one of H_02 / H_01 / M_05 5 s; [tight]; loot place; LOOT <= 15 s; [loose]; walk 2 -> cover H_08 5 s; [tight]; loot place; LOOT <= 15 s; [loose]; walk 2 -> cover Dumpster 4 s; SPRINT 1; [leashed tight]
- **#03 looter**: wait 3 s; [loose, vision x2]; walk 3; walk 1 -> cover H_05 8 s; walk 1 -> cover H_18 8 s; walk 1 -> cover H_14 8 s; [tight]; loot place; LOOT <= 45 s; [loose]; walk 1 -> cover, one of M_11 / M_12 8 s; walk 1 -> cover H_03 8 s; [tight]; loot place; LOOT <= 45 s; [loose]; walk 2; SPRINT 1; [leashed tight]
- **#04 flanker**: wait 3 s; [loose, vision x2]; walk 3; walk 1 -> cover H_16 8 s; walk 1 -> cover M_02 8 s; walk 1 -> cover M_13 8 s; [tight]; loot place; LOOT <= 30 s; [loose]; walk 1 -> cover, one of H_15 / M_04 8 s; walk 1 -> cover H_06 8 s; [tight]; loot place; LOOT <= 30 s; [loose]; walk 2; SPRINT 1; [leashed tight]
- **#05 flanker**: wait 5 s; [loose, vision x2]; walk 3; walk 2 -> cover M_01 8 s; walk 1 -> cover M_02 8 s; [tight]; loot place; LOOT <= 30 s; [loose]; walk 2 -> cover H_05 8 s; [tight]; loot place; LOOT <= 30 s; [loose]; walk 2 -> cover M_02 6 s; SPRINT 1; [leashed tight]
- **#06 second looter**: wait 5 s; [loose, vision x2]; walk 3; walk 1 -> cover M_06 10 s; walk 1 -> cover H_15 10 s; walk 1 -> cover, one of M_01 / H_15 10 s; [tight]; loot place; LOOT <= 45 s; [loose]; walk 1 -> cover, one of M_03 / H_04 / M_06 10 s; walk 1; [tight]; loot place; LOOT <= 45 s; [loose]; walk 2; SPRINT 1; [leashed tight]
- **#07 rear guard**: wait 8 s; [loose, vision x2]; walk 3; walk 1 -> cover H_06 12 s; walk 1 -> cover H_02 12 s; walk 1 -> cover H_01 12 s; [tight]; loot place; LOOT <= 30 s; [loose]; walk 2 -> cover Dumpster 12 s; [tight]; loot place; LOOT <= 30 s; [leash tight]; walk 2 -> cover H_05 8 s; SPRINT 1; [leashed tight]
- **#08 runner**: [loose, vision x2]; walk 3; walk 2 -> cover H_03 4 s; walk 1 -> cover M_01 4 s; [tight]; loot place; LOOT <= 15 s; [loose]; walk 1 -> cover M_10 4 s; walk 1; [tight]; loot place; LOOT <= 15 s; [loose]; SPRINT 2; SPRINT 1; [leashed tight]

The first three places (the car park, about 55 m) have no hold for six of the seven: three boxes in 100 m.

### M02 (Late Night Opening)

- **#02 point man**: [loose, vision x2]; six times walk 1 -> cover 5 s (H_03 x 4 - four different boxes -, H_04, M_02); walk 1; cases timer (glass + open); [tight]; loot place; LOOT <= 15 s; [loose]; walk 2 -> cover H_04 5 s; cases timer; [tight]; loot place; LOOT <= 15 s; [loose]; walk 3 -> cover H_06 4 s; walk 2 -> cover H_04 4 s; walk 2 -> cover M_02 4 s; walk 1; SPRINT 1; [leashed tight]
- **#03 looter**: wait 3 s; [loose, vision x2]; walk 3 -> cover H_03 8 s; walk 2 -> cover H_03 8 s; walk 1 -> cover, one of M_03 / H_01 / H_03 8 s; walk 1; cases timer; [tight]; loot place; LOOT <= 60 s; [loose]; walk 1 -> cover, one of H_01 / H_03 8 s; walk 1; cases timer; [tight]; loot place; LOOT <= 60 s; [loose]; walk 3; walk 1 -> cover H_03 6 s; walk 1 -> cover M_08 6 s; walk 1 -> cover, one of H_05 / H_02 / H_04 6 s; walk 2; SPRINT 1; [leashed tight]
- **#04 flanker**: wait 3 s; [loose, vision x2]; walk 1 -> cover H_04 8 s; walk 2 -> cover H_04 8 s; walk 2 -> cover H_03 8 s; walk 1 -> cover M_02 8 s; walk 1; cases timer; [tight]; loot place; LOOT <= 45 s; [loose]; walk 2; cases timer; [tight]; loot place; LOOT <= 45 s; [loose]; walk 3 -> cover H_04 6 s; walk 2 -> cover H_01 6 s; walk 3; SPRINT 1; [leashed tight]
- **#05 flanker**: wait 5 s; [loose, vision x2]; walk 1 -> cover H_04 8 s; walk 2 -> cover H_04 8 s; walk 2 -> cover H_04 8 s; walk 1 -> cover H_07 8 s; walk 1; cases timer; [tight]; loot place; LOOT <= 45 s; [loose]; walk 2; cases timer; [tight]; loot place; LOOT <= 45 s; [loose]; walk 3; walk 1 -> cover M_05 6 s; walk 1 -> cover H_02 6 s; walk 1 -> cover, one of H_03 / H_06 / H_01 6 s; walk 2; SPRINT 1; [leashed tight]
- **#06 second looter**: wait 5 s; [loose, vision x2]; walk 1 -> cover H_03 10 s; walk 3; walk 1 -> cover M_02 10 s; walk 1 -> cover M_01 10 s; walk 1; cases timer; [tight]; loot place; LOOT <= 60 s; [loose]; walk 2; cases timer; [tight]; loot place; LOOT <= 60 s; [loose]; walk 3; walk 1 -> cover H_01 8 s; walk 1 -> cover M_08 8 s; walk 3; SPRINT 1; [leashed tight]
- **#07 rear guard**: wait 8 s; [loose, vision x2]; walk 2 -> cover H_01 12 s; walk 2 -> cover H_01 12 s; walk 2 -> cover M_08 12 s; walk 1; cases timer; [tight]; loot place; LOOT <= 45 s; [loose]; walk 2; cases timer; [tight]; loot place; LOOT <= 45 s; [leash tight]; walk 3 -> cover H_03 8 s; walk 2 -> cover M_08 8 s; walk 3; SPRINT 1; [leashed tight]
- **#08 runner**: [loose, vision x2]; walk 3; walk 2 -> cover H_08 4 s; walk 1 -> cover M_02 4 s; walk 1; cases timer; [tight]; loot place; LOOT <= 15 s; [loose]; walk 2; cases timer; [tight]; loot place; LOOT <= 15 s; [loose]; walk 3; walk 3; SPRINT 2; SPRINT 1; [leashed tight]

### M03 (the bank)

- **#02 point man**: [loose, vision x2]; walk 1 -> cover M_46 5 s; walk 1 -> cover H_71 5 s; walk 1 -> cover M_1047 5 s; walk 1 -> cover H_45 5 s; walk 2 -> cover H_47 5 s; [tight]; loot place; LOOT <= 15 s; [loose]; walk 2 -> cover H_48 4 s; walk 2 -> cover H_10 4 s; walk 1 (the gather place at the drop, in its AllyEscapeBox); walk 3; SPRINT 1; [leashed tight]
- **#03 looter**: wait 3 s; [loose, vision x2]; walk 2 -> cover H_65 8 s; walk 3; walk 1; [tight]; loot place; LOOT <= 35 s; [loose]; walk 1 -> cover H_62 6 s; walk 3 -> cover M_11 6 s; walk 1 (gather); walk 3; SPRINT 1; [leashed tight]
- **#04 flanker**: wait 3 s; [loose, vision x2]; walk 1 -> cover M_47 8 s; walk 1 -> cover M_57 8 s; walk 2 -> cover M_1045 8 s; walk 2 -> cover H_48 8 s; [tight]; loot place; LOOT <= 20 s; [loose]; walk 1 -> cover, one of H_51 / H_52 6 s; walk 3; walk 1 (gather); walk 3; SPRINT 1; [leashed tight]. The two way places between the EXITS_BANK door and the gather place (its "walk 3" after the loot) lie on the second way round.
- **#05 flanker**: wait 5 s; [loose, vision x2]; walk 2 -> cover H_64 8 s; walk 3; walk 1; [tight]; loot place; LOOT <= 20 s; [loose]; walk 3 -> cover M_01 6 s; walk 2 (to the gather place); walk 3; SPRINT 1; [leashed tight]
- **#06 second looter**: wait 5 s; [loose, vision x2]; walk 2 -> cover H_31 10 s; walk 1 -> cover H_44 10 s; walk 3 -> cover H_64 10 s; [tight]; loot place; LOOT <= 35 s; [loose]; walk 1 -> cover H_61 8 s; walk 3 -> cover M_10 8 s; walk 1 (gather); walk 3; SPRINT 1; [leashed tight]
- **#07 rear guard**: wait 8 s; [loose, vision x2]; walk 2 -> cover H_70 12 s; walk 2 -> cover H_74 12 s; walk 2 -> cover H_46 12 s; [tight]; loot place; LOOT <= 20 s; [leash tight]; walk 3 -> cover H_01 8 s; walk 2 (gather); walk 3; SPRINT 1; [leashed tight]
- **#08 runner**: [loose, vision x2]; walk 3 -> cover H_46 4 s; walk 3; [tight]; loot place; LOOT <= 15 s; [loose]; walk 3; walk 2 (gather); SPRINT 3; SPRINT 1; [leashed tight]

No hold at the gather place in front of the drop (it must stay the place before the link, inside its box)
and none beyond it (11 boxes there lie across the escape car's road).

### M06 (A Walk in the Park)

- **#02 point man**: [loose, vision x2]; walk 1 -> cover M_0953 5 s; walk 1 -> cover H_15 5 s; walk 1 -> cover M_153 5 s; walk 1; [tight]; loot 1; LOOT <= 15 s; [loose]; walk 1 -> cover M_151 5 s; [tight]; loot 2; LOOT <= 15 s; [loose]; walk 1 -> cover M_86 5 s; [tight]; loot 3; LOOT <= 15 s; [loose]; [tight]; loot 4; LOOT <= 15 s; [loose]; walk 2 -> cover H_04 4 s; walk 1; SPRINT 1; [leashed tight]
- **#03 looter**: wait 3 s; [loose, vision x2]; walk 3; walk 1; [tight]; loot 1; LOOT <= 35 s; [loose]; walk 1; [tight]; loot 2; LOOT <= 35 s; [loose]; walk 1 -> cover M_11 8 s; [tight]; loot 3; LOOT <= 35 s; [loose]; [tight]; loot 4; LOOT <= 35 s; [loose]; walk 3 -> cover M_55 6 s; SPRINT 1; [leashed tight]
- **#04 flanker**: wait 3 s; [loose, vision x2]; walk 3 -> cover M_03 8 s; walk 1; [tight]; loot 1; LOOT <= 20 s; [loose]; walk 1 -> cover M_147 8 s; [tight]; loot 2; LOOT <= 20 s; [loose]; walk 1 -> cover M_87 8 s; [tight]; loot 3; LOOT <= 20 s; [loose]; [tight]; loot 4; LOOT <= 20 s; [loose]; walk 2 -> cover H_0618 6 s; walk 1; SPRINT 1; [leashed tight]
- **#05 flanker**: wait 5 s; [loose, vision x2]; walk 3; walk 1; [tight]; loot 1; LOOT <= 20 s; [loose]; walk 1; [tight]; loot 2; LOOT <= 20 s; [loose]; walk 1 -> cover M_47 8 s; [tight]; loot 3; LOOT <= 20 s; [loose]; [tight]; loot 4; LOOT <= 20 s; [loose]; walk 3 -> cover H_04 6 s; SPRINT 1; [leashed tight]
- **#06 second looter**: wait 5 s; [loose, vision x2]; walk 3; walk 1; [tight]; loot 1; LOOT <= 35 s; [loose]; walk 1; [tight]; loot 2; LOOT <= 35 s; [loose]; walk 1 -> cover M_16 10 s; [tight]; loot 3; LOOT <= 35 s; [loose]; [tight]; loot 4; LOOT <= 35 s; [loose]; walk 1 -> cover, one of H_91 / H_90 / M_10 8 s; walk 2 -> cover M_0849 8 s; SPRINT 1; [leashed tight]
- **#07 rear guard**: wait 8 s; [loose, vision x2]; walk 3; walk 1 -> cover M_08 12 s; [tight]; loot 1; LOOT <= 20 s; [loose]; walk 1 -> cover, one of M_150 / M_08 12 s; [tight]; loot 2; LOOT <= 20 s; [loose]; walk 1 -> cover M_46 12 s; [tight]; loot 3; LOOT <= 20 s; [loose]; [tight]; loot 4; LOOT <= 20 s; [leash tight]; walk 2 -> cover H_04 8 s; walk 1; SPRINT 1; [leashed tight]
- **#08 runner**: [loose, vision x2]; walk 3; walk 1; [tight]; loot 1; LOOT <= 15 s; [loose]; walk 1; [tight]; loot 2; LOOT <= 15 s; [loose]; walk 1; [tight]; loot 3; LOOT <= 15 s; [loose]; [tight]; loot 4; LOOT <= 15 s; [loose]; SPRINT 3; SPRINT 1; [leashed tight]

The four loot stops are one way place apart, so most of this map's difference is the loot waits
(15 / 20 / 35 s x 4) and the 21 holds; 24 of 46 asks found no free box in reach.

### Retomoto (tower, then the street from the jump)

Tower, all seven: [stagger]; [loose, vision x2]; walk 1 (in through the window); [tight]; the boardroom table;
LOOT <= 30 s (point man and runner 15 s); [loose] (rear guard: [leash tight]); walk 3; walk 3; walk 3; walk 1
(beside the tower car, in the AllyEscapeBox) - no sprint, no hold, no timer on the way down (section 3).
Only the point man has a hold in the tower: after the window, one of three boxes, 5 s.

Street (started by the JumpPoint; `050_DefendBehaviour_street` keeps its name, the JumpPoint is not touched):

- **#02 point man**: walk 2 -> cover, one of H_123 / H_128 4 s; walk 2 -> cover, one of H_01 / H_133 4 s; walk 1 -> cover M_05 4 s; walk 2 -> cover H_20 4 s; walk 3 -> cover M_05 4 s; walk 1 -> cover H_12 4 s; walk 1 -> cover H_01 during the rally; rally 10 s; walk 1 -> cover Sign04 4 s; SPRINT 1; [leashed tight]
- **#03 looter**: walk 3 -> cover, one of H_11 / H_14 / H_132 6 s; walk 3; walk 3; walk 3; rally 10 s; walk 1; SPRINT 1; [leashed tight]
- **#04 flanker**: walk 2 -> cover H_127 6 s; walk 3; walk 3; walk 3 -> cover Sign02 6 s; walk 1; rally 10 s; walk 1; SPRINT 1; [leashed tight]
- **#05 flanker**: walk 3 -> cover H_124 6 s; walk 1 -> cover H_103 6 s; walk 3; walk 3; walk 2 -> cover M_02 during the rally; rally 10 s; walk 1; SPRINT 1; [leashed tight]
- **#06 second looter**: walk 2 -> cover, one of H_122 / H_120 8 s; walk 2 -> cover H_17 8 s; walk 3; walk 3; walk 2; rally 10 s; walk 1; SPRINT 1; [leashed tight]
- **#07 rear guard**: walk 3 -> cover, one of H_37 / H_129 / H_131 8 s; walk 2 -> cover SwitchBox H_20 8 s; walk 3; walk 3 -> cover Pillar07 8 s; walk 1 -> cover Busshelter H_04 during the rally; rally 10 s; walk 1; SPRINT 1; [leashed tight]
- **#08 runner**: walk 3; walk 3; walk 3; walk 3; rally 10 s; SPRINT 1; SPRINT 1; [leashed tight]

On the road most boxes (parked cars, planters) stand WEST of the van's lane; the bots walk the east pavement,
so those are refused (the picture `dyn_map_1.png` shows it). Also still true from the research: the 35
re-placed police `RunToPosInfo` points of this map point at open road - not this step's job, not done.

## 8. Live: what to look for (watch-only)

Nothing of this is installed. When one of the builds is, with `[Bots] Enable=1 Log=1` in KLHook.ini:

**klbot's log** (`klhook/klbot.c`: one line when a crew record changes)

| line | before (y_loot2 / rt_full4) | to see now |
|---|---|---|
| `bots: record N (Cn): heist stage 0 -> 1` (the ENTERS_BANK box) | seven lines within a second or two | spread out: C2 and C8 first, C3 / C4 about 3 s, C5 / C6 about 5 s, C7 about 8 s later - plus the holds before the door |
| `bots: record N (...): <status>` going to dead | most of the seven, early (the owner's report) | fewer and later; note WHERE in the round (before stage 1, at the loot, after stage 2) |
| `heist stage 1 -> 2`, `-> 3` | together | C8 first (15 s loot, no hold out), C7 last |
| the periodic line (`L.. s.. van <state> <seconds>`, per record `g<stage> $money`) | - | when does the van's state leave 0, and how many records are at g3 then: does the runner call the vehicle too early for the rest? Compare the second of that line with a y_loot2 round |
| end of round: who is aboard | - | are the looters (C3, C6) and the rear guard (C7) left behind more often than before |

**By eye** (`tools/kl_watch.py` pictures, or the owner playing)

1. Do they STOP at boxes, dumpsters, pillars, counters and crouch / lean for a few seconds, then move on -
   or do they stand in the open beside the box? (The hold place is 0.7 - 2.3 m from the box's middle; the
   engine's `DefendCover` has to take the box from there. If they stand beside it: the distance or the side
   is wrong - both are GUESSES.)
2. Nobody sprints except in the last metres to the vehicle (C8: the last two steps).
3. The seven no longer arrive anywhere together: C2 (and C8) lead, C7 trails.
4. C2 (unleashed): does he push at the enemy instead of holding - and does he still come back to the route?
   If he runs off and dies first every round: rebuild with `--no-rusher`.
5. A bot that walks BACK a few metres to a box behind it: that is C7's preference (rear boxes). If it looks
   silly, say so - it is one number.
6. Does anybody stand still for the rest of the round? It should not be possible at a hold (every hold ends on
   a timer, never on "arrived" or "enemies dead"); if one does, the place it stands at names the step.
7. Retomoto: after the jump, does every bot walk the street - nobody turns back toward the lobby car?
   (A tower step started late would look like that; the tower's way out has no timer for this reason.)
8. M03: the bots still take the drop over the sunk wall (unchanged steps there).

**For an A / B**: `--no-random` (takes out the one form no stock BOT has: a Defend step that starts two
things), `--no-vision`, `--no-rusher`, `--sixth 800`. Each is a 30 s rebuild from the bots build.

## 9. Not done, not established

- Nothing ran. Whether the Dead Men cover boxes become covers in the game at all is still the research's open
  point (class mask and flag bit at run time; re/bots_dynamic.md 3.2) - if they do not, the holds are places in
  the open with a timer, which is still slower and more spread than before but no cover.
- A bot that sticks to the human; followers of another bot (section 0.4).
- More than one bot on another way: the mesh of four of the five maps offers no second way between the fixed
  places under this step's rule. Routes that really differ need new stations (other doors, other loot order),
  that is `kl_fa_bots.plan`'s business, not a post-process.
- Per-round random ROUTES (stock's RandomTrigger at every junction): `kl_fa_bots.check` cannot walk a
  RandomTrigger between two route steps (its NEXT table has no entry for it), and the task was not to change
  it. If the lead wants them: `'RandomTrigger': 5` in `check()`'s `NEXT` lets its walk take the first branch;
  the other branches then need this module's kind of check.
- Cover boxes in open ground (section 4). Weapons per bot. `RunToCoverBehaviourRout`.
- Timing against the vehicle: the loot waits end for everybody when the loot is GONE, so the spread behind the
  loot is the way-out holds (0 .. 24 s) - on paper. If loot stays (a case nobody opened), the looters stand up
  to 60 s a stop while the runner has left: section 8's van line is the check.
- `kl_fa_bots.diff <pre-bots build> <dyn build>` no longer holds (the squad is not just appended any more);
  use `kl_fa_bots_dyn.py diff <bots build> <dyn build>`.

## 10. How this was produced

`tools/kl_fa_bots_dyn.py` (plan: 2 - 9 s a map; build with every check: 25 - 45 s). Scratch (session
`1e45a579-...\scratchpad\dyn\`): `d1.py` (a squad node by node), `m1.py` `m2.py` `m3.py` (stock precedents:
list fan-out, timers, modifiers, sixth-sense rows, transitions), `gates.sh` + `gates5\` (the gate runs),
`owner6.txt` (the build log of the five), `sum_<map>.md`, `map_*.png`.
