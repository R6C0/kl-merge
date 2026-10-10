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
- Per-round random ROUTES (stock's RandomTrigger at every junction): **DONE since, section 11** (the two
  "more than one bot on another way" points above are overtaken by it).
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

## 11. Random routes (2026-10-10 night; OFFLINE, nothing ran in the game, nothing installed)

The owner: "the ai heisters just path the same then die so quick", then "are u doing the routes yet". Until here
the seven walked the build's places every round; only the cover at a hold was drawn. Now **the way itself is drawn,
per bot and per round, the way stock does it: a `RandomTrigger` between two steps.**

### 11.1 What is built

`<work>\build\z_route\M01 M02 M03 M06 retomoto_full`, from the five NON-dynamic bots builds that are on the owner's
tab (`z_gate\M01`, `z_final\M02 M03 M06`, `rt_full6\retomoto_full`; nothing is written into those):

    python tools\kl_fa_bots_dyn.py routes <work>\build            all five (4 min)
    python tools\kl_fa_bots_dyn.py build <bots build> <out>       one; --no-routes = the step as it was (section 1),
                                                                  --ways 2 = at most two ways a fork

Everything of sections 1 - 7 is still made (holds at cover boxes, stagger, the seven roles). `--no-routes` on
`z_gate\M01` gives the installed `z_dyn3\M01` back byte for byte (every member of the archive).

### 11.2 The form, and the stock object it is copied from

Stock **F07 `Gameplay!merc_bot_squad!Squad#02`**:

    040_SquadModifier_Loose_defense   {26: [040_RandomTrigger_out_of_loot_area]}
    040_RandomTrigger_out_of_loot_area  ZBoxPrimitive + RandomTrigger {0: 1, 1..4: 3 3 0 0,
                                        5: [050_DefendBehaviour_rout_out_of_loot_area_left],
                                        6: [050_DefendBehaviour_rout_out_of_loot_area_right], 7: [], 8: []}
    each way a DefendBehaviourRout chain of its own; the ways meet by naming the same next step
    (the eight 090_DefendBehaviour_rout_escape_* all name 100_SquadModifier_tight_defense_van)

The node that is cloned is the same squad's `060_RandomTrigger_BeforeStreet` (same class, same controller, same
nine fields; it is also what the cover choice of section 2 clones). Ours:

    <what stands before: a walk, a hold's timer, a modifier, the build's loot wait>
      -> NNN_RandomTrigger_way {0: 1, 1..3: the weights, 5..7: [the first step of way a / b / c]}
           NNN_DefendBehaviour_way_a ... the build's own way places of this stretch (with their holds and timers)
           NNN_DefendBehaviour_way_b ... another way
           NNN_DefendBehaviour_way_c ... another way
      the last step of every way -> the step of the next place that stays

Measured on the stock bots (F01..F09, 440 uses; `scratchpad\route\s2.py`): a RandomTrigger is started by a
`TriggerDelay2` 181 x, a `DefendBehaviourRout` 119, `TriggerActorsDead` 49, `SquadModifierBehaviour` 42,
`TriggerLootDepleted` 14, another RandomTrigger 28; it starts a `DefendBehaviourRout` step 728 times of 805.
So every link we write has a stock bot precedent. One form of ours is rarer: a way WITHOUT a step of its own (the
build's way where the stretch has no way place) names the step behind the fork directly - still RandomTrigger ->
DefendBehaviourRout.

**Weights by role** (a weight is a share: stock bots have (3,3) 154 x, (33,33) 44, (3,3,3) 28 and unequal ones -
F02 `RandomTrigger_ramp_choice` (4,2), `RandomTrigger_arch_combat_choice` (7,1), `street_combat_choice` (2,4),
F01 (32,13), and (8,24,34), (7,14,34)):

| bot | prefers | weights (favourite / the others) |
|---|---|---|
| #02 point man | the SHORTEST way | 4 / 2 (stock pair; (4,2,2) with three ways: GUESS for the triple) |
| #04 flanker | the way that lies furthest LEFT of the build's | 4 / 2 |
| #05 flanker | the way that lies furthest RIGHT | 4 / 2 |
| #08 runner | the shortest | 7 / 1 (stock pair; (7,1,1): GUESS) |
| #03 #06 looters, #07 rear guard | none | 3 / 3 (/ 3): stock's commonest. The rear guard is last by its start (+8 s) and its 12 s holds, as before |

Every bot still DRAWS: a preference is 50 % (4/2/2) or 78 % (7/1/1), never a fixed way.

### 11.3 Where the ways come from

A **stretch** = the way between two places that must stay: a place in a trigger box that gives the heist stage
(ENTERS_BANK / EXITS_BANK / BOARDS), in a level exit box, in an AllyEscapeBox, a loot place, the gather place
before the drop, a rally place, the last place. Those are never moved and every way passes them, in the old
order; the build's waits (loot, cases timers + relays, rally) and modifiers stand where they stood. Per stretch:

1. **Another corridor of the mesh** (up to two): the polygons of the ways already known cost 4 x their length and
   the mesh is searched again; a find counts when it is at most 1.6 x + 6 m longer than the build's way, shares at
   most 60 % of its length with it and with every other find (within 2.5 m in the plan, 2 m in height) and lies
   5 m off it somewhere. Way places are then put along it about every 15 m (clear of the mesh's edge, 1.1 m from
   every other bot's), the walk from place to place is measured again, and the same test is made on THAT line (a
   place-to-place walk can fall back into the other corridor). All of it GUESS (thresholds as the old `LANE_*`).
2. No other corridor and the stretch longer than 50 m: it is cut in two at the way place nearest its middle, and
   each half is a stretch of its own (stock F07 has nine forks on ~250 m).
3. **To a side**: where a fork still has fewer than three ways, the build's way with its way places moved 3.2 m
   (2.4, 1.7) to the left / right - where the mesh has the room; a stretch of 12 m and more without a way place
   gets one in its middle. This is the "not in single file" part: the corridor is the same, the line is not.
4. No fork on a stretch shorter than 9 m, over the drop link (M03), on the first step of a chain that is started
   from outside (Retomoto's street: the JumpPoint names it) and on Retomoto's way in through the blown window.

Rules on every new way place (= what the checks ask of a route place): on the route's mesh part, flat (holds'
rule 15; way places on the START row's part 100 - `WARP_HOME`, GUESS: M06's lawns are uneven polygons and the
build's own way places stand on them), not in a level exit box and no walk through one unless the stretch already
starts in one, 250 from the escape vehicle's line behind the last loot wait and no extra crossing of it,
Retomoto: not in the van's lane, near the van on the bot's own side of it, in the tower clear of the two charges.
Holds are looked for along EVERY way (same search, same one-box-one-bot rule), so a bot holds at the covers of
the way it drew.

### 11.4 How many (from `dyn.json`, `scratchpad\route\stats.py`)

Per map, all seven bots together:

| map | forks | with 3 ways | with 2 | forks that have another CORRIDOR | ways: other corridor / to a side | stretches >= 9 m with no other way |
|---|---:|---:|---:|---:|---:|---:|
| M01 | 32 | 20 | 12 | 16 | 23 / 29 | 3 |
| M02 | 59 | 47 | 12 | 35 | 44 / 62 | 7 |
| M03 | 34 | 24 | 10 | 24 | 27 / 31 | 11 |
| M06 | 29 | 19 | 10 | 14 | 23 / 25 | 13 |
| Retomoto | 42 | 42 | 0 | 30 | 36 / 48 | 9 |

Per bot: forks (3 ways + 2 ways) / stretches with no other way. Stock bots have 3 .. 9 RandomTriggers each.

| | #02 | #03 | #04 | #05 | #06 | #07 | #08 |
|---|---|---|---|---|---|---|---|
| M01 | 5 (3+2) / 0 | 4 (3+1) / 1 | 5 (3+2) / 0 | 5 (2+3) / 0 | 3 (3+0) / 1 | 6 (4+2) / 0 | 4 (2+2) / 1 |
| M02 | 7 (6+1) / 0 | 11 (8+3) / 1 | 10 (7+3) / 1 | 7 (5+2) / 0 | 9 (7+2) / 2 | 10 (9+1) / 2 | 5 (5+0) / 1 |
| M03 | 6 (4+2) / 0 | 4 (3+1) / 2 | 5 (3+2) / 2 | 5 (4+1) / 1 | 4 (3+1) / 3 | 6 (4+2) / 1 | 4 (3+1) / 2 |
| M06 | 3 (3+0) / 3 | 4 (2+2) / 2 | 5 (2+3) / 1 | 4 (4+0) / 2 | 5 (2+3) / 1 | 3 (2+1) / 3 | 5 (4+1) / 1 |
| Retomoto | 6 (6+0) / 1 | 6 (6+0) / 1 | 5 (5+0) / 2 | 8 (8+0) / 2 | 5 (5+0) / 1 | 5 (5+0) / 1 | 7 (7+0) / 1 |

(Besides those: 1 - 4 stretches a bot that were not looked at - shorter than 9 m, the drop, a chain's first step.)

Where the other corridors are (`dyn_map*.png` in each folder: dim line = the build's way, bright = the other ways
of the forks; M01, M03, M06 and Retomoto's street were LOOKED at, M02 and Retomoto's tower only counted):

- **M01**: the car park from the START row to the diner has three corridors (west, the middle, a loop round the
  north-east); the build walked one. Two again between the two loot places and on the way out to the gate.
- **M03**: the forecourt left / right; inside, a second staircase on the east side (the build sent all seven
  down the same one); the yard along its west wall or its east side. Beyond the drop only the sides.
- **M06**: one central path; a few wide loops off it (west of the middle, an east diagonal, the south-west) that
  only some of the seven have (the others' way places found no room on them). Else the same path, to a side.
- **Retomoto street**: other lines through the lobby, then the pavement OR out between the parked cars on the
  road and back. The last 20 m before the van's stop: sides only (its lane).

### 11.5 Checks (all PASS on the five; last lines below)

- **`kl_fa_bots.check` and `kl_fa_bots_rt.check` now walk a fork.** Small, commented change (`fork_branches()`
  + the walk): a chain that meets a RandomTrigger as its next link is walked once per BRANCH SET v = 0, 1, ..; at
  each fork branch v mod (the number of its ways). Every way of every fork is in one of the (at most three) walks
  and gets EVERY rule of those checks: on the mesh, clearance, a path in order, level exit boxes before the loot
  wait, the lane, the stages, the drop link, the cases, the van's side on Retomoto. Not every COMBINATION of ways
  is walked (two forks are separated by a place all ways pass). A build without a fork is walked once, as
  before: `kl_fa_bots.py check z_final\M03` prints the RESULT line its `bots.txt` has.
- **`kl_fa_bots_dyn.py check`**, new per fork: field 0 = 1, one target for every weight; the ways MEET again and
  share no step before; at most one way without a step of its own; every way's places on the mesh part of the
  place before the fork, clear of the edge, flat; a path A -> its places -> Z without a link; not in or through a
  level exit box unless A is in one; not in the vehicle's lane behind the last loot wait; not in the van's lane;
  every way walked (a way no branch set reached is a FAIL). The holds' rules of section 5 apply on every way.
- **They bite** (three spoiled scratch builds of M01, `scratchpad\route\neg.py`): a place of a second way put into
  a level exit box -> FAIL from both checks ("is inside level exit box ... BEFORE its loot wait" in branch set 2,
  "way 2 of fork ... in or through a level exit box"); lifted off the mesh -> 4 FAIL; a way cut off from the step
  behind the fork -> "the ways of fork ... never meet again" + the stage FAILs.
- `diff`, `kl_impact`, `kl_maps audit` (same "known and accepted" counts as the source builds: 1 / 6 / 0 / 6),
  `kl_map_guns check`, `kl_map_escape van-check`: unchanged tools.

| | dyn check | diff | kl_impact | kl_maps audit | kl_map_guns check | van-check |
|---|---|---|---|---|---|---|
| M01 | PASS (0 FAIL, 2 NOTE) | only the squad's steps | problems: 0 | PASS (0, 1 known) | problems: 0 | 0 fault(s) |
| M02 | PASS (0 FAIL, 6 NOTE) | only the squad's steps | problems: 0 | PASS (0, 6 known) | problems: 0 | 0 fault(s) |
| M03 | PASS (0 FAIL, 3 NOTE) | only the squad's steps | problems: 0 | PASS (0, 0 known) | problems: 0 | 0 fault(s) |
| M06 | PASS (0 FAIL, 3 NOTE) | only the squad's steps | problems: 0 | PASS (0, 6 known) | problems: 0 | (no van) |
| Retomoto | PASS (0 FAIL, 4 NOTE); kl_fa_bots_rt PASS (0 FAIL, 6 NOTE) | only the squad's steps | problems: 0 | (not a kl_maps map) | problems: 0 | (kl_fa_van's) |

(NOTEs: timers below 16 s on the runner and on bots whose way has no free cover box, holds 260 - 292 from their
box, on Retomoto "1 (one way of Squad#05: 2) legs near the van are not a straight line on the mesh clear of its
lane" for six squads - kl_fa_bots_rt's own NOTE; the installed z_dyn2 build has three NOTEs there. The gate logs:
`scratchpad\route\gates\<map>_<gate>.txt`, the build log `routes_final.txt`.)

### 11.6 Size

| | entities: bots build -> dynamic (installed) -> routes | REF slots | squad nodes | `.prm` `.ANM` `.fxc` `.WAV` |
|---|---|---|---:|---|
| M01 | 15,352 -> 15,541 -> 15,889 | 26,009 -> 26,546 | 707 | equal to the source, to the byte |
| M02 | 22,411 -> 22,622 -> 23,291 | 33,068 -> 33,948 | 1,169 | equal |
| M03 | 20,214 -> 20,337 -> 20,769 | 30,871 -> 31,426 | 754 | equal |
| M06 | 15,804 -> 15,970 -> 16,427 | 26,685 -> 27,308 | 828 | equal |
| Retomoto | 26,038 -> 26,183 -> 26,991 | 35,771 -> 36,724 | 1,256 | equal |

Only ZGROUP and ZBoxPrimitive entities (no model, no new class, no new controller name). Against what is known:
stock's largest level has 42,915 entities (L10); stock bot squads have 429 .. 694 nodes (F07 the most), so **M02's
and Retomoto's squads are 1.7 - 1.8 x the largest stock squad**. No limit is known for that; the level's heap
budget (.gms +0x1c, not decoded, the sum of both source levels' since the graft) is not raised by this step, as
it was not by `kl_fa_bots` or the first dynamic step. If a build with routes does not load where its `z_dyn`
sibling does, `--ways 2` (about a third fewer new entities) and `--no-routes` are the two steps back.

### 11.7 Assumptions and what is not done

- NOT RUN. That a way drawn by our RandomTrigger is walked is stock's own mechanism; that the GAME's pathfinder
  walks from one of our way places to the next along the corridor this module's portal path takes is an
  ASSUMPTION (way places every ~15 m keep it short). The "to a side" ways assume a bot walks to a place 2 - 3 m
  beside another line rather than treating both as the same spot.
- Thresholds (60 % shared, 1.6 x, 5 m off, 3.2 m to a side, 50 m cut, uneven polygons up to 100): GUESS.
  Weights' triples: GUESS.
- A corridor is "another" by geometry only. Whether it is the SAFER or the more dangerous one (police lines,
  open ground) is not looked at; M01's north-east loop is open car park, Retomoto's road ways lead between the
  parked cars (which carry cover boxes).
- Sum of hold timers: on the build's way as before (section 6); on another way planned against the same budget
  (the way with the most seconds counts, <= 85 s).
- The runner's second sprint step is now the last step BEHIND its last fork (a fork's ways are walked, not sprinted).
- Not done: other loot ORDER or other doors at a fixed place (that is `kl_fa_bots.plan`'s station choice); a fork
  across the drop on M03; the bots builds themselves (their lanes are unchanged: way a of every fork).
- For the live look (watch-only), beside section 8: with `[Bots] Log=1` the stage lines of a bot should come at
  different times from round to round; by eye, do the seven fan out on M01's car park and use both staircases of
  the bank; does anybody stand still at a fork (it should be impossible: a RandomTrigger has no wait).

## 12. Cover where the map has none (`tools/kl_fa_cover.py`; 2026-10-10 late; OFFLINE, nothing ran in the game, nothing installed)

The owner: "the ai heisters ... die so quick ... make them utilise cover". Section 4 said: no box was made, what
limits the holds is where the boxes ARE. This step makes boxes - **only on solid things that are there** - and
runs BEFORE the dynamic step, on the finished non-dynamic bots build:

    python tools\kl_fa_cover.py all <work>\build [M01 ...]     z_gate\M01, z_final\M02 M03 M06, rt_full6\retomoto_full
                                                               -> z_cover\_pre\<map> (the boxes) -> kl_fa_bots_dyn.build
                                                               (random routes) -> z_cover\<map>           (7 min, all five)
    python tools\kl_fa_cover.py plan | build | check | diff    one build; --models b = the careful form only (12.2)

### 12.1 What it does

1. It runs the dynamic step's own plan and takes the route places that ASKED for a hold and got none
   (`kl_fa_bots_dyn.find_holds` now notes them when `ctx.misses` is a list - four lines, nothing else changed there).
2. Round each such place (6 m) it cuts the `.HVK`'s STATIC shapes (key-framed and rigid ones move: left out) with
   horizontal planes 45 / 75 / 110 / 140 / 175 / 205 over the collision's own floor (not the mesh's height:
   Retomoto's street mesh lies 40 under the road). What one entity has in the 75 plane, joined up, is an object;
   the smallest rectangle round it is its size. It counts when it is 40..700 long, at least 10 thick, there at 45
   too (no table top), and not named glass / window / fence / rail / wire / bush / hedge / leaves / door / gate /
   stair / lamp / bicycle / metal barrier / Collapse_ / Remains / camera / Coli* / HeroOnly (collision that is not
   the thing one sees). HIGH when it is in the 175 plane over 60 % of its outline, else LOW. All thresholds: GUESS.
3. No box when: a cover box of the map is at the object already; it is inside a `NoCoverBox`, in a level exit
   box, within 250 of the escape vehicle's road (Retomoto: in the van's lane); `kl_fa_bots_dyn.hold_ok` finds no
   place on the mesh 70..230 from it that the bot can walk to; an object over 4 m whose end is joined to more
   collision (a wall in a row has no corner).
4. The box is a clone of one of the build's OWN cover boxes: same class (ZSTDOBJ), properties, flags, pool group
   and MODEL number; only place and rotation are its own. Named `CoverBoxH_KL_nn` / `CoverBoxM_KL_nn`, children of
   one new top-level ZGROUP `KL_Cover!` (form: the build's plain top-level group `Locations/<map>/..._Audio.zip`;
   listed in the root's group tree as that one is). It lies inside the object's rectangle at the end / side
   NEAREST THE PLACE THAT ASKED = facing back along the bot's way. **Where enemies come from is not known to the
   step: that side is a GUESS** (the engine picks the side of a box itself; an object as small as its box has no
   choice to make).
5. Plan again with the boxes (in memory), add again, at most 4 rounds; then write, check, diff.

Nothing else needs a count: `FFCoverList` has no fields and an empty list in every stock level; the game makes
its cover list at the load from the names (at most 5,000; the builds have 147 .. 482 now).

### 12.2 The two forms a box can have (measured on the nine stock levels and the five builds, `scratchpad\cover\i2.py i3.py i7.py i8.py`)

Every cover box of every level has an UNSCALED matrix: **a box's size is its model's box** (root chunk + 0x20;
ASSUMPTION that 0x603830's "object's box" is that one). No model is added, so a new box has one of the sizes the
build's own boxes have.

| form | flags | model root + 0x1c | room tree | stock | our builds |
|---|---|---|---|---|---|
| **b** | 0x200 | 0 (no collision record) | in none | F05 203, F08 147, F09 13, F06 13, F01 3 (+ every car box) | M01 21, M02 33, M03 90, M06 87, Retomoto 215 |
| **a** | 0x302 | a record of the `.oct` | tree 0 of its ZROOM | most boxes | M01 118, ... |

- A **b** clone is exact: same record, in no tree. M03, M06 and Retomoto have small plain boxes (63 x 162 x 45,
  70 x 200 x 70, 100 x 100 x 100 ...); M01's and M02's plain boxes are car-sized.
- An **a** clone gets the same flags and model and is listed in tree 0 of the ROOT's room set with its box in the
  world - where every level lists the 134+ objects with a collision record that have no room above them (flags
  0x102 / 0x182; the item box = the model's box in the world, measured). **ASSUMPTION: a cover box may be listed
  there**; no stock cover box is (stock's 30 cover boxes with a record and no listing hang in dynamic groups:
  F01's glass-door dividers, F07's vans). `--models b` builds without them. A plain model is taken whenever it
  covers at least 60 % of what the best a-model would (GUESS).

### 12.3 Result (`z_cover\<map>\cover.txt`, `cover.json`; `dyn_map*.png`: a magenta frame = a new box)

Holds found / asked are the dynamic plan's own tally WITH random routes (so not section 4's 33 / 58 ..., which
were without): the same plan, before and after the boxes.

| map | new boxes (low / high) | of them form a | holds found / asked, before -> after | boxes a hold of the final plan names | places still without |
|---|---|---:|---|---:|---:|
| M01 | 8 (1 / 7) | 8 | 53 / 151 -> 60 / 149 | 7 | 88 |
| M02 | 9 (8 / 1) | 2 | 87 / 217 -> 93 / 207 | 9 | 108 |
| M03 | 20 (3 / 17) | 0 | 50 / 189 -> 69 / 179 | 20 | 105 |
| M06 | 15 (12 / 3) | 4 | 61 / 159 -> 69 / 147 | 15 | 80 |
| Retomoto | 2 (1 / 1) | 1 | 91 / 180 -> 95 / 179 | 2 | 86 |

What they stand on: M01 - the palm by the start, four pillars and a telephone pole of the shop fronts, a metal
bin, a phone booth. M02 - the sweeper machine, seven watch show cases of the jewel store ('Montre'), a jewel wall
panel. M03 - nine pilasters of the banking hall, three blocks 'NonDestructables', a garage pillar, a base block,
a locker end, three palms and three long plant pots of the forecourt. M06 - seven rocks, the tea house, bridge
parapets of the pavilion, two flower tubs. Retomoto - a walk-bridge support in the street, the lobby desk.

**The gaps that stay (nothing solid there: no box was invented).** Places are world x, y, z of the middle of a
group of asking places.
- **M01, the car park**: round (1288, 0, 27160) 24 places, (2751, 0, 26448) 12, (776, 0, 29003) 10,
  (4576, 0, 26578) 7 - 46 of those 53 have NOTHING solid within 6 m (open tarmac; the one dumpster has its box
  and one bot). The cars there are driving ones (not static).
- **M02**: (879, 494, 1277), the middle floor's gallery, 44 places: glass, railings, table tops, thin posts.
  (-55, 0, -7720), the car park, 24: lamp posts and 61 x 60 / 43 x 24 pillars that no model of the build fits.
- **M03**: beyond the wall drop, (236, 91, -264), 24 places: long walls only (and the level exit box). The
  forecourt (-2051, 220, -2808), 28: the plant pots and palms have their boxes now, the rest is open.
  Inside (53 places over two floors): panes, stairs, the players' blockers.
- **M06, the lawns** round (2926, 260, 6361): 64 places; 17 with nothing solid at all, the others: long garden
  walls, lamps, low ledges; the rocks that fit a model have boxes.
- **Retomoto street** (-1187, -40, 2594) 35 places: bicycles, crowd barriers, glass; (-981, -40, 6850) 14: the bus
  shelters, pillars and switch boxes there HAVE Dead Men's boxes (one bot each). The tower's way down has no holds
  by design (section 3), so no asks.
- Everywhere: **walls**. A wall or building over 7 m is not handled ("long"): a corner of one is real cover, but
  finding corners in a triangle soup was not written. This is the largest class left.

### 12.4 Checks (all on `z_cover\<map>`; logs `scratchpad\cover\gates\`, `gates_all.txt`)

`kl_fa_cover.py check`: every box a ZSTDOBJ below `KL_Cover!`, record and properties (but place / rotation) equal
to the box it is a clone of, unscaled and upright, `.prp` and `.gms` agree, where `cover.json` planned it (this
also proves the rotation: the model box's middle through `kl_fa_bots.frames` lands on the planned middle), form b
in no tree / form a once in the root's tree 0, a low model 95..150 high / a high one 150+, not in a NoCoverBox,
not in a level exit box, 250 from the vehicle's road, 150 from every other cover box, **static collision inside
its footprint 75 over its foot** (not in thin air), slot ids of the room trees as in the source, at most 5,000
boxes, the four large blocks. `kl_fa_cover.py diff <source> <_pre>`: the old top-level subtrees and entities as
they were (record, order, REF id), one more subtree at the end, the root's trees 0 / 3 gained only the new
entities, collision records and tail equal, `.prm` only record offsets, every other member and every file beside
the archive byte for byte.

| | cover diff | cover check | dyn check | dyn diff (_pre -> final) | kl_impact | kl_maps audit | kl_map_guns | van-check |
|---|---|---|---|---|---|---|---|---|
| M01 | only the cover group was added | PASS (0 FAIL, 1 NOTE) | PASS (0 FAIL, 2 NOTE) | only the squad's steps | problems: 0 | PASS (0, 1 known) | problems: 0 | 0 fault(s) |
| M02 | same | PASS (0, 1) | PASS (0, 5) | same | problems: 0 | PASS (0, 6 known) | problems: 0 | 0 fault(s) |
| M03 | same | PASS (0, 0) | PASS (0, 1) | same | problems: 0 | PASS (0, 0 known) | problems: 0 | 0 fault(s) |
| M06 | same | PASS (0, 1) | PASS (0, 3) | same | problems: 0 | PASS (0, 6 known) | problems: 0 | (no van) |
| Retomoto | same | PASS (0, 1) | PASS (0, 4); kl_fa_bots_rt PASS (0, 6) | same | problems: 0 | (not a kl_maps map) | problems: 0 | (kl_fa_van's) |

(The cover check's NOTE is "n of the boxes are form a".) `.prm` / `.ANM` / `.fxc` / `.WAV` equal to the source
builds to the byte. Entities: M01 15,927, M02 23,330, M03 20,893, M06 16,499, Retomoto 27,011.

### 12.5 Assumptions, and what is not done

- NOT RUN. Whether Dead Men's cover boxes become covers in the game at all is still open (section 9); these are
  clones of them, so they stand and fall with them. Whether the PLAYER can take cover at a form b box is not known
  either (it has no collision record; the player's cover uses the same list).
- Form a boxes in the root's tree 0 (12.2). If a `z_cover` build does not load where its `z_route` sibling does:
  `kl_fa_cover.py build <bots build> <out> --models b` (M01 then has no box at all - its only plain boxes are car-sized - and the step refuses to write: use `z_route\M01`), then `kl_fa_bots_dyn.py build`.
- "Solid" = static collision. What a bullet goes through (thin metal, wood) is not looked at; names stand in for
  that. A HeroOnly / Coli* blocker is left out even where a real thing stands inside it and has no collision of
  its own.
- The box of an object bigger than every model covers a part of it (the part nearest the asking place).
- Not done: wall corners; boxes beside key-framed or rigid things (parked Havok cars have Dead Men's own); a
  second box on a long object for a second bot unless another place asked from its other end; the check was not
  tried against spoiled builds (the dynamic step's was, section 11.5).
- `kl_fa_bots_dyn.py map` draws a magenta frame round every box of this step. M01 and M06 were LOOKED at: M01's
  eight frames are the palm west of the start and the pillars along the shop fronts, the car park north of them is
  empty but for Dead Men's two boxes; M06's are the rocks of the east lawn, the bridge parts on the middle path
  and the tubs in the south.

## 13. Corners, and the form question settled (`tools/kl_fa_cover.py`; 2026-10-11; OFFLINE, nothing ran in the game, nothing installed)

    python tools\kl_fa_cover.py all <work>\build [M01 ...]     -> z_cover2\_pre\<map> (boxes: objects + corners, form b only)
                                                               -> kl_fa_bots_dyn.build (random routes) -> z_cover2\<map>
    options: --models b|ab (default b), --no-corners, --corner-near N (800), --no-borrow

`z_cover` (section 12) is left as it was. `z_cover2` supersedes it: **no form a box in any of the five builds.**
Also there, as a choice for the lead: `z_cover2\_ab\M01` = M01 with `--models ab` (13.3).

### 13.1 How stock puts a box at a corner (measured: `scratchpad\cover2\s1.py`, the corner finder run on stock F05 and F08)

For every HIGH cover box of the level the nearest corner the finder sees, and how the box lies to it:

| | high boxes | at an 'L' corner (two faces meet) | at a wall end | no corner within 60 of a box corner |
|---|---:|---:|---:|---:|
| F05 | 444 | 140 | 193 | 111 |
| F08 | 219 | 98 | 16 | 105 |

Of the 238 'L' boxes 219 (F05 129, F08 90) have **a footprint corner within 15 of the wall corner, lie in the
solid and along the face (within 5 degrees)**; 9 are turned or off by more, 10 lie outside. At a wall end the box
is as deep as the wall is thick and its end is flush with the wall's end (F05 `SO0101_F05_Frame_Main_A_01!
CoverBoxH_03` / `_04`: 150 x 200 x 40 and 70 x 200 x 40 on a 30 wall; `CoverBoxH_31`: 115 x 200 x 60 on a 60 wall).
At a building corner it is 70..150 along the face and 60..120 deep (F05 `CoverBoxH_27` .. `_29` 100 x 200 x 120,
`CoverBoxH_62` .. `_64` 125 x 200 x 72..104; F08 `CoverBoxH_33` / `_34` 70 x 200 x 70, `CoverBoxH_38` / `_39`
110 x 200 x 70, `CoverBoxH_01` .. `_04` 30 x 200 x 100). So: **the box IS the corner** - it fills the end of the
solid, and the engine makes its four sides the cover. That is what `consider_corner()` builds (`CORNER_AIM` 100).

### 13.2 What a cover takes from the entity (kl2.exe read statically, `scratchpad\cover2\f603830.txt`)

`0x6d6a80` hands the object to `0x603830(obj, high, 1, car)`. That routine reads `[obj + 4]`, the object's
128-byte slot, and of its geometry nothing else:

| slot | what | where read |
|---|---|---|
| +0x00 | 3 x 3 matrix. `[+0x10]` (the Y of its up axis) must be over 0.717 (`[0xb68900]`): a box tilted past 44 degrees is no cover | 0x603880 |
| +0x24 | place | 0x7b3031 |
| +0x30 | **box middle** (3 floats, the object's own frame) | 0x60395f, 0x42a4d0 (adds it to a corner) |
| +0x40 | **box half size** (3 floats) | 0x60386b .. 0x60387c |
| +0x50 | parent slot, walked to the root | 0x7b303b |
| +0x6c | name (`*_depend_on_parent`) | 0x603c4e |

Four corners = middle +- half size in X and Z at the box's FLOOR (`-half Y`), each through `0x7b3020` (matrix,
place, every parent) into the world; then one side per pair of corners (`0x898e80`, `0x71fc30` x 4) with the
height `half Y + 50.0` (`[0xb71b60]`). Besides that only controllers (`DynamicCover` on it or its parent = no
cover; `DestructibleCover`, `PlayerCoverModifier`) and the define `OnlyFireOver`.

- **Not read: the mesh, the model root's collision record, flags 0x100 / 0x002, any room tree.** So a form b box
  (no record, in no tree) is a whole cover, and nothing form a has is needed. **Form a is dropped from the
  builds.**
- The extent DOES come from the model. The slot's box is not in the level files: the loader zeroes +0x30..+0x48
  (0x8adb19..0x8adb2b) and no ZGEOM / ZSTDOBJ property is a size; a ZSTDOBJ has nothing but its model to fill it.
  The routine that fills it was looked for and NOT found (ASSUMPTION: it is the model root's box, chunk + 0x20).
  Evidence in the data: every cover box model of every level looked at (stock F01 F05 F08, the five builds) has
  ONE mesh with draw mode 0x800000 = hidden (kl2 0x67cf77) - a box that exists only for its size - and no cover
  box has a scaled matrix; stock keeps one model per size (F05: 100 x 100 x 100, 100 x 200 x 100, 140 x 200 x 140,
  100 x 200 x 20 ...).
- So a form b box can only have a size a hidden box model of the build has. Sizes of the builds' own form b
  models: M01 low 110..220 wide, high 200 x 150 x 190 and up (all car-sized); M02 the same + 150 x 269 x 45;
  M03 64 x 163 x 46, 70 x 200 x 70, 100 x 200 x 50 / x 100, 200 x 200 x 200; M06 30..125 wide (many); Retomoto
  110 x 100 x 110 and up, high from 109 x 345 x 109.
- **One more model without adding one** (`forms()`, 'borrow'; `--no-borrow` leaves it out): every build carries
  F07's hand-held camera objects (`AllLevels/FA_Cam_Handheld.zip\Cam_Handheld\*_Cam`), ZSTDOBJ whose model is a
  100 x 100 x 100 box with one hidden mesh and no collision record - the same kind of model, and the size of
  stock F05's commonest low form b box. Where a build has no low form b model of its own up to 130 wide (M01,
  M02, M03), a LOW box may be a clone of one of the build's form b cover boxes with that model number (.gms
  record + 0x0c and `ZGEOM[4]`). ASSUMPTION: a cover box may share its model with an object that is no cover
  box. Used by 2 boxes on M01 and 2 on M02; the check notes them. Not used for HIGH boxes (a 100-high model under
  a `CoverBoxH` name gives a cover height of 100; the lowest high box of our maps gives 119).
- Not taken: a NEW model root in a dead chunk of the `.prm` (64 bytes, another root's hidden mesh, other bounds)
  would give any size without growing the file - it IS adding a model, and it is unproven; a scaled matrix would
  scale the box in 0x603830 (no cover box of any level has one); a ZBoxPrimitive named `CoverBox*` (sized by its
  properties) - whether the cover list's class test lets it through is not established.

### 13.3 The corner finder

For a place that got no object box in the round (`corners()`, `wall_runs()`, `consider_corner()`):

1. The cut segments of the 75 plane of every entity (but the `NOT_COVER` names), each turned so that its
   triangle's normal is on its left, are joined into straight FACES: on one line (5 off, 10 degrees), gaps up to
   25, at least 100 long, at least 80 % of the length facing one way.
2. **'L'**: two faces end within 25 of one another at 60..120 degrees and each faces AWAY from the other (convex:
   a building corner, a pillar over the old 700 limit; a room's inner corner faces the other way and is left out).
   **'end'**: two faces back to back, 10..100 apart, end side by side, nothing in the 75 plane for 80 beyond (a
   wall end, a doorway jamb, the end of a garden wall).
3. It must be there 45 over the floor too (not a sill, not a counter top). There at 175 = a HIGH box, else LOW.
4. The face: the one whose normal points AGAINST the bot's way on that leg (dot under -0.3), i.e. hidden from
   where the bot is walking TOWARD. **'The threat is ahead on the bot's way' is a GUESS**; it is the same guess
   `kl_fa_bots_dyn.find_holds` makes when it takes the place 'behind the box as the bot walks'. Mesh must lie
   50..110 before that face.
5. The box: in the solid, a footprint corner ON the corner, along the face (13.1); no deeper than the solid behind
   the face + 25 (a wall end: its thickness; else up to the first mesh behind the face - a thin shell with a room
   behind it - or the other face's length); at least 60 along the face and not longer than it; of the models
   that fit the one nearest 100 x 100.
6. Then as for objects: no cover box at the corner already, a hold place of `kl_fa_bots_dyn` 70..230 from it ON
   THE FACE'S SIDE that `hold_ok` passes, not in a NoCoverBox, a level exit box, within 250 of the vehicle's road,
   in the van's lane; same floor as the place that asked. One corner box a place and round.

### 13.4 Result (`z_cover2\_pre\<map>\cover.txt`, `cover.json`; `scratchpad\cover2\stats.py`, `zoom.py`)

All boxes are form b. Holds are the dynamic plan's own tally with random routes, source build -> with the boxes
(the final `dyn.json` has the same numbers).

| map | boxes | on objects (low / high) | at corners (low / high) | with the borrowed cube | holds found / asked | section 12 (form a allowed) | places still without |
|---|---:|---|---|---:|---|---|---:|
| M01 | 2 | 2 / 0 | 0 / 0 | 2 | 53 / 151 -> 55 / 151 | 60 / 149 (8 boxes, all form a) | 95 |
| M02 | 9 | 8 / 1 | 0 / 0 | 2 | 87 / 217 -> 92 / 207 | 93 / 207 (9, 2 form a) | 109 |
| M03 | 22 | 3 / 15 | 0 / 4 | 0 | 50 / 189 -> 72 / 179 | 69 / 179 (20, 0) | 102 |
| M06 | 15 | 12 / 3 | 0 / 0 | 0 | 61 / 159 -> 70 / 147 | 69 / 147 (15, 4) | 79 |
| Retomoto | 4 | 1 / 1 | 0 / 2 | 0 | 91 / 180 -> 95 / 179 | 95 / 179 (2, 1) | 86 |
| M01 `_ab` | 8 | 1 / 6 | 0 / 1 | 1 | 53 / 151 -> 60 / 149 | (7 form a, 1 form b) | 88 |

**The corner finder adds little: 6 boxes on the five maps (7 with M01 `_ab`).** M03: four corners of the banking
hall's square blocks (`NonDestructables_01`, 158 x 156) and of a column (`SI0102_M03_ColumnBankEnd_A_02`), each
a 100 x 200 x 100 box. Retomoto: two corners of a pier of the street front (`SO0100_JPN_Street_Wide_a_02`, faces
212 and 1214 long) at x -2900, z 130 and z -1357, a 170 x 150 x 200 box. M01 `_ab`: a corner of a phone booth.
Why the others got none (counted a gap place and corner; a corner is counted once for every place that sees it):

| | no corner within 8 m | a cover box is there already | no face hidden from ahead | not on the floor (nothing at 45) | no mesh before the hidden face | no model fits |
|---|---:|---:|---:|---:|---:|---:|
| M01 (95 places) | 47 places | 76 | 60 | 50 | 27 | 35 |
| M02 (109) | 24 | 28 | 67 | 102 | 63 | 92 |
| M03 (102) | 41 | 124 | 96 | 14 | 39 | 11 |
| M06 (79) | 17 | 47 | 59 | 22 | 35 | 0 |
| Retomoto (86) | 35 | 10 | 73 | 34 | 5 | 47 |

So the walls are not the missing cover the first run took them for: where a wall corner is near a bot's way it
mostly faces the wrong way for a threat ahead (a wall BESIDE the way), has a box already, or is a thin wall end
(M02: jambs 20..22 thick, about two thirds of its 92) for which the build has no thin high model. The gaps of 12.3 stay, with
these numbers: M01 the car park (41 of 95 places have nothing at all: no object within 6 m and no corner within
8 m); M02 the gallery (45 places: glass, rails, sills) and the car park (24); M03 the hall's upper floor (31),
the forecourt (28), beyond the wall drop (24); M06 the lawns (63); Retomoto the street (35 + 14).

**M01**: with form b alone it gets 2 boxes (two metal bins, the borrowed cube); its pillars, palm and pole are
40..62 wide and HIGH, and M01 has no slim high form b model. This is the one map where form a is the only way
to more without a new model: `z_cover2\_ab\M01` has the 7 form a boxes of the first run again (same checks, all
pass; its cover check notes 'form a: ASSUMPTION'). The lead chooses; `z_cover2\M01` is the safe one.

LOOKED AT: `dyn_map.png` of M01 (two magenta frames, both at the shop fronts on the west way), M02 (nine in the
jewel store, the sweeper and a panel), M03 (the pilasters along the hall's west wall, the blocks and the column
in the hall on the bots' ways, the forecourt's pots and palms). The frames cannot tell a corner box from an
object box at that scale, so every corner box was drawn alone (`scratchpad\cover2\zoom.txt`: collision in the 75
plane, the footprint, the hold place, 20 units a cell): all six sit in the solid with a footprint corner on the
corner of a block / column / pier, and the hold place is on the side the bot comes from.

### 13.5 Checks (`scratchpad\cover2\gates.sh` -> `gates_all.txt`, `gates\`; M01 `_ab`: `m01ab.txt`, `gates_ab\`)

| | cover diff | cover check (`_pre` and final) | dyn check | dyn diff | kl_impact | kl_maps audit | kl_map_guns | van-check | large blocks | side .ini |
|---|---|---|---|---|---|---|---|---|---|---|
| M01 | only the cover group was added | PASS (0 FAIL, 1 NOTE) | PASS (0 FAIL, 2 NOTE) | only the squad's steps were made anew | problems: 0 | PASS (0, 1 known) | problems: 0 | 0 fault(s) | equal | 2 same |
| M02 | same | PASS (0, 1) | PASS (0, 5) | same | problems: 0 | PASS (0, 6 known) | problems: 0 | 0 fault(s) | equal | 2 same |
| M03 | same | PASS (0, 0) | PASS (0, 1) | same | problems: 0 | PASS (0, 0 known) | problems: 0 | 0 fault(s) | equal | 2 same |
| M06 | same | PASS (0, 0) | PASS (0, 3) | same | problems: 0 | PASS (0, 6 known) | problems: 0 | (no van) | equal | 2 same |
| Retomoto | same | PASS (0, 0) | PASS (0, 4); kl_fa_bots_rt PASS (0, 6) | same | problems: 0 | (not a kl_maps map) | problems: 0 | (kl_fa_van's) | equal | 4 same |
| M01 `_ab` | same | PASS (0, 2) | PASS (0, 2) | same | problems: 0 | PASS (0, 1 known) | problems: 0 | 0 fault(s) | equal | 2 same |

(The cover check's NOTE on M01 / M02 is 'n boxes have the box primitive of an object that is no cover box'; on
M01 `_ab` also 'form a'.) Entities: M01 15,900, M02 23,329, M03 20,901, M06 16,502, Retomoto 27,016.

**Negative test** (`scratchpad\cover2\neg.py` -> `neg.txt`; scratch builds from `z_final\M03`, deleted at the end):
the unspoiled control passes; a box moved 600 with `cover.json` moved too FAILS ('no static collision in its
footprint ... (thin air)'); moved with `cover.json` left FAILS ('not where cover.json planned it'); a form b box
listed in the root's tree 0 FAILS ('is listed in a room tree'); a box with flag 0x400 FAILS ('flags 0x600').
`NEGATIVE TEST: PASS`.

A fault found on the way: `check` counted a `NoCoverBox` (ZBoxPrimitive, kind none) as a cover box in its
'within 150 of a cover box' rule (M03, first build); it now counts cover boxes only, as the planner does.

### 13.6 Assumptions, and what is not done

- NOT RUN. Everything of 12.5 still holds for these boxes (do Dead Men's cover boxes become covers at all; can the
  PLAYER use a form b box).
- The slot's box = the model root's box: ASSUMPTION (the filling routine was not found, 13.2).
- 'The threat is ahead on the bot's way' (which face of a corner): GUESS. A corner whose faces look sideways or
  forward gets no box, though it is cover against somebody round it.
- The triangle normal as 'the free side of a face' relies on the collision being wound outward. It was not
  tested on its own; a wrong one gives a face without mesh before it and so no box (never a box in the wrong
  place: the hold place must be on the mesh on that side).
- Thresholds (100 face, 25 join, 60..120 degrees, 10..100 thick, 25 over, 800 near): GUESS but where 13.1 names
  stock.
- The borrowed cube: ASSUMPTION (13.2). `--no-borrow` gives M01 no box at all (then the step refuses to write:
  use `z_route\M01`) and M02 two fewer.
- Not done: thin high wall ends where the build has no thin high model (M01, M02's jambs, Retomoto) - needs a
  new model root (13.2); low corners got no box anywhere (the finder allows them; none passed); a corner box
  for a place that already got an object box in the round; `kl_fa_bots_dyn.py map` does not tell corner boxes
  from object boxes.
