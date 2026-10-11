# Dead Men campaign places as Fragile Alliance maps - the synthesis

2026-10-11, agent cfa-synth. The owner asked (2026-10-11): "want you to look into making the specific campaign maps
more FA orientated from dead men: the bank map but the campaign way, the club map, hasta / cuba & probably walk in
the park perhaps prison too?" This is the STUDY's summary. OFFLINE: nothing was installed, the game was not started,
no existing file was edited, nothing was committed. Nothing in it has run in the game.

Sources: six reports, each written by one agent and then corrected IN PLACE by a second one (its last section
'Verification (second agent)' weighs more than the first text where they differ). All six exist and were read in full:
`re/campaign_fa_bank.md`, `re/campaign_fa_club.md`, `re/campaign_fa_havana.md`, `re/campaign_fa_park.md`,
`re/campaign_fa_prison.md`, `re/campaign_fa_tooling.md` (cited below as bank 8.2 = that file, section 8.2).

Evidence labels:
- **MEASURED** = output I produced in this job; the command is named. Mine are few: `python G:/kl_scratch/cfa_synth/table.py`
  (reads back every kept `result.json` under `<work>/build/cfa`; output `G:/kl_scratch/cfa_synth/table.txt`), greps of the
  tools at today's working tree, the kept lighten / wardrobe / compaction logs, and one build of my own
  (`sh G:/kl_scratch/cfa_synth/havana_ward.sh`: Havana lightened + wardrobe + compacted; logs `h1..h5_*.log` beside it).
- **READ** = taken from a report, code or a note; the place is named. A statement READ from a report is MEASURED there by
  its author (the report names the command) unless I say otherwise.
- **ASSUMED** = fits the evidence, reason given. **GUESS** = a coordinate or value nobody measured.
`<work>` = `G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools`. World units: 100 = 1 m, (x, y, z), y up.
'A Retomoto' = the work Retomoto Tower took (= 1.0). Section 0 is the plain summary; every statement in it comes back
with its label and source in sections 1 - 5.

## 0. For the owner

- All five places can become Fragile Alliance maps. None is ready today, and nothing in this study has run in the game.
- BANK, the campaign way (chapter 3 alone): start roped down in the secure yard, in through the loading dock, down two flights
  to the vault while its door is forced, loot the deposit boxes, back up into the banking hall, out the front to a van. Half a Retomoto.
- CLUB (the Mizuki): start shut in Yoko's office with the money, break out through her bodyguards, across both dance floors with
  the club's own music, van at the front door. Half a Retomoto. No dancing crowd; outside there is only a strip of pavement.
- PRISON: cell block B in the riot, SWAT storming in, a hold-out in the yard under the tower until the last gate opens, then the
  car park and a van out of the prison gate. Three quarters of a Retomoto or more. A new place; needs a test in the game first.
  *(corrected after the critic: and it has no room for all four Payday 2 masks beside its guards and the gun looks -
  two of them at most, or the eight masks the other Dead Men maps have: tooling 12.3)*
- HAVANA: the Capitol only (chapter 12): start under the dome, blow the bunker, shoot open the president's display cases, get back
  out across the square to a van with the army closing in. A whole Retomoto. The grandest and the least sure.
- PARK, the campaign way: the garden you already have - start in the pagoda as the deal goes wrong, climb the stair tower, police
  and a van on the highway. Under half a Retomoto. A second round, not a new place: half of the walk is ground you already play.
- Order I recommend: bank, club, prison, Havana; the park last, or not at all.
  Bank first: you named it first, it is the surest (it already fits the game with its guards and all sixteen bodies), and its
  lessons - doors, a van on a new road, a second hand-made map - are needed by every later one. The club next because nothing in
  the game stands in its way. The prison and Havana wait for one test in the game: a clean-up of the model file never yet loaded.
- Cannot be done: both Havana chapters as one map; the bank together with its van chase; the prison 'the campaign way' (its three
  parts are joined only by climbing and a rope); the club's crowd, and its rooftop helicopter, in a first version.
- Not worth it: Havana's street chapter by itself (nothing in it to steal). The park only if you want a quick extra round.
- Your decisions:
  a. Which of them, in which order? Above all: the club without its crowd - yes or no; the park - yes or no.
  b. Two short test runs in the game while you are away: they settle the prison, Havana and every door on every map.
  c. A third page on the Arcade menu: one place is left on 'Dead Men maps', and a third page is the last button the menu takes.
  d. Music: each map's own music makes the game's music file larger (bank +56 MB; all five +310 MB, to 2.0 GB): your go-ahead each time.

## 1. The table

Limits the numbers are held against:

| limit | value | basis |
|---|---|---|
| model table (.prm chunk table) | 73,728 entries; past it the loader writes over the game's globals (a crash at load). The tools refuse above 69,632 (4,096 kept free for chunks the game makes while it runs) | MEASURED `grep -n CHUNK tools/kl_impact.py` (lines 55 - 61, 130 - 139); READ re/prm_limit.md |
| textures / materials | 4,096 / 2,048 | READ CLAUDE.md 'Format modules' |
| collision file (.HVK) | 5,002,128 bytes is the largest that has loaded and played; the van check faults above it | MEASURED `grep -n HVK_MAX tools/kl_map_escape.py` (706, 1753) |
| model file (.prm) as one block | served from the hook's 128 MiB reserve; 96.5 MB loaded once before the reserve existed; the tab's Retomoto is 79.9 MB | READ tooling 5.2, 11.2 |
| entities / rooms | 26,991 entities ran (a Retomoto route build); rooms: a graft has run with 31 - 32 (Late Night Opening), stock Dog Days L03 has 61 | READ tooling 5.4, 11.2 |
| gates (corrected after the critic: this row was missing; prison 'Gap closed: 242 gates') | NO limit on a level's total: every reader walks one room's gate array in place with a 32-bit count (READ kl2 0x48e910, 0x522cc0, 0x6e5b20, 0x8bcef0, 0x5e2b30). Most in a stock level 207 (F09), most in one room 17 (F03, L03). What is fixed is per room or per frame: a room's neighbour-list count is a byte and its one reader keeps about 30 on the stack untested (0x83dca0; stock most 9); the visibility walk has 1,024 frustum records per camera per frame, untested in Dog Days, asserted at the same 1,024 in Dead Men (kl2 0x522cc0, kaneandlynch 0x4764d0; a simulation of the walk gives 87 at most for stock F09); the sound update has 32 route slots (int3 at kl2 0x576d1f; stock most 23) | READ + MEASURED `G:/kl_scratch/cfa_fill2/gatecount.py`, `vissim.py`, `sgpdeg.py` |

'As built' = the plain trial graft `python tools/kl_maps.py one <out> F07 <L> --campaign` (no Fragile Alliance layer, NO enemy
in it). Every as-built number below is MEASURED by me from the agents' kept `result.json` files (`table.py`) and agrees with
both agents of that place. 'Finished' = lightened, with the full wardrobe; where the round's enemies were built in, it says so.

| place, levels | verdict after verification | the trial graft against each limit | effort (Retomoto = 1) | main blocker | what needs a live run |
|---|---|---|---|---|---|
| **BANK the campaign way** - M03_A alone | **ready-to-author** (both agents), on three conditions: van stop moved, the two door sets on the way OUT open from the round start, first live run = the bare level with the dock door opened (READ bank 8.6) | chunk table **64,871** as built; **65,640** with the round's 22 squads AND the wardrobe (3,992 under the tools' line; MEASURED the kept log `<work>/build/cfa/bank/skeptic/wardrobe_squads/log.txt`). Textures 1,866 (1,903 with squads), materials 1,221 (1,239), entities 19,675 (20,076), rooms 28, .HVK 3.0 MB, mesh 232,480 bytes converted. .prm 85.7 MB as built, **67.8 MB finished with enemies** (Retomoto 74.2, stock F07 63.6). 0 dangling paths; problems = 1 missing ambience clip + the 10 findings of a level without a layer | **0.5** (first agent; second: 'about the same total', bank 8.6) | no hard one. Soft: the route is SIX door sets in series, each necessary, no way round (bank 8.3); the campaign pre-pass drops the level's only cover list (tooling 5.5: a one-word fix); the van tool wants a Dead Men escape car this level lacks; authoring is wired to Retomoto's module | the dock door answering 'Activate' at the round start (the crew starts locked in a yard behind it), then the other five sets; whether shut doors hold a player; `LightToggle` x 22 (never run in Dog Days); the vault blast beside players; the van on the square; bots at the 3.5 m dock doorway and in the ante-room |
| **CLUB** - M05_A | **feasible-with-work** (both) | the STOCK command FAILS: one material string (`TEXT/TILU = MIRRORED`, material 538) stops the converter. With that string read as TILED: chunk table **52,935** as built, **53,898** with all 27 enemy squads + wardrobe + four mask plates (MEASURED kept log `<work>/build/cfa/club/sk_keep27_ward/log.txt`). Textures 1,676 (1,725), materials 1,135 (1,162), entities 26,106 (26,384), rooms 20, .HVK 1.6 MB, mesh 119,236 bytes. .prm 78.9 MB as built, **60.8 MB finished with enemies**. 0 dangling; four materials without a compiled shader, three of them club lamps | **0.5** for the round out of the front door; 0.9 with the roof (first agent). Second agent: nothing contradicts 0.5, but police on the pavement and a fenced pavement are not in it (club 8.3, 8.4) | the converter guard (one string) stops every tool on this level; no vehicle and no street - 30 x 8.8 m of collision floor outside the door; no crowd (the crowd system never ran in Dog Days, three converter gaps); the rooftop helicopter fails in the collision-join tool both ways | does it load: three controller kinds no Dog Days level ever ran (`PositionLightControl` x 7, `ZIKLNKOBJ` + `StartAnim` x 2, `ShotActivateDamage` x 5); music and light show; door groups open and STAY open without their `DoorCtrl` (corrected after the critic: answered offline - they do NOT as the file stands, the office leaves' clip is shut again at frame 60; LAST frame 30 on the four leaves cures it: G1.8 of 'Gap closed: the route without a run-time event'); the two invisible seals switch off; a van driving where there is no floor; how empty it looks |
| **PRISON** - M08_A, cell block B side | **feasible-with-work** (both; 'the same verdict, a different list of reasons', prison Verification) | chunk table **79,005 as built: 5,277 OVER the game's table**. Compacted **50,617**; wardrobe then compaction **63,528**, .prm 79.5 MB, 0 problems (MEASURED kept logs `<work>/build/cfa/prison/compact/log.txt`, `wardrobe_compact/log.txt`). Under another systems level, F05: **61,504**, no chunk problem. Textures 1,964, materials 1,286, entities 23,307, rooms 61, .HVK 4.3 MB, mesh 354,868 bytes in THREE pieces (528 / 502 / 103 polygons). .prm 64.2 MB. All without enemies *(corrected after the critic: the whole finishing chain was run with the round's 7 squads, F07's police / AI heisters / vans and the gun looks in - **65,509 entries and .prm 87.5 MB with the 8-mask wardrobe (4,123 under the tools' line); 70,925 with the four Payday 2 plates: 1,293 OVER the tools' line**; two plates at most (68,217). 59 actors. MEASURED, tooling 12.2, 12.3, 12.6)* | **0.7** (first agent); 'not below Retomoto's until the generic authoring tool exists' (second, a GUESS). Plan with 0.7 - 1.0 | the chunk table: compaction has never been loaded in the game, another systems level has never hosted a live map and the van code names F07's objects; SEVEN shut doors / fences in series with no way round any one; 'the campaign way' is not walkable (three mesh pieces joined by climbs and a rappel) | a compacted level (or one under F05) loading with HUD, fonts, effects right; the cage doors and fences opening; four controller kinds never run (`EffectDmgBox` 15, `LightToggle` 7, `AnimSequence` 5, `ZHingeConstraint` 1); 61 rooms in a graft; the start under eight shotguns; the van's lane |
| **HAVANA** - M11_B 'El Capitolio' alone | **feasible-with-work** (both) | chunk table **74,454 as built: 726 OVER the game's table**. Compacted 46,081 (MEASURED the kept log `G:/kl_scratch/cfa_havana/compact.txt`). **Wardrobe then compaction: 58,992 entries, .prm 84.4 MB, 0 problems - MEASURED by me** (`havana_ward.sh`; both agents had left this ASSUMED). Other systems levels: F08 66,368 (but F08 has no van), F05 56,953, F09 69,805 (still 173 over the tools' line). Textures 1,835, materials 1,178, entities 19,188, rooms 16, .HVK 4.3 MB, mesh 290,516 bytes. .TEX 433.3 MB as built, 242.9 lightened. Without enemies *(corrected after the critic: finished - the round's 13 squads, the host's layer and the gun looks in - **60,902 entries / .prm 91.6 MB with 8 masks, 66,318 / 93.0 MB with 12 (3,314 under the tools' line)**; .TEX 295 - 298 MB; 61 actors. MEASURED, tooling 12.2, 12.5, 12.6)* | **0.8** (first agent); **about 1.0 (0.8 .. 1.2)** (second: four gates instead of two, an opening blast to borrow, an unsolved van line) | the chunk table, as the prison; FOUR campaign geometry switches, every one on the only way (loot wing door, bunker, Capitol corner, stair barricade); the level has no opening blast object; no van line that arrives from out of sight on a closed, cratered square; the largest .prm of all (84 MB before its soldiers) | compaction or another systems level; all four geometry switches removing their collision; the bunker's blast and emitters; light in the hall under a Dog Days level; the van on the square; an 84 - 88 MB .prm on a second and third load |
| **PARK the campaign way** - M06_A 'Exchange' | **feasible-as-variant** (both) | chunk table **53,960** as built, 52,433 with the two pre-pass cures and the exit cut scene's set left out. Textures 1,589 (1,450), materials 1,002 (927), entities 19,157 (18,626), rooms 7 (6), .HVK 2.2 MB, mesh 258,988 bytes. .prm 79.5 MB as built, **35.9 MB lightened** (MEASURED kept log `<work>/build/cfa/park/light2/lighten_log.txt`); about 52 MB with the wardrobe (ASSUMED in park 3.2, not built) *(corrected after the critic: built - with its 4 squads, the host's layer, the wardrobe and the gun looks, NOT compacted: **54,263 entries, .prm 58.0 MB (8 masks) / 59.2 MB (12)**, five load blocks 137 MiB = stock F01's; 45 actors. MEASURED, tooling 12.2, 12.5, 12.6)*. Problems = the 10 layer findings and nothing else. Without enemies | **0.4** (first agent); **0.45 (0.4 .. 0.55)** (second) | nothing blocks the graft. It is not a new place: 52 % of the walk lies on the Fragile Alliance park's own mesh (park Corrected 10). It cannot be made from the existing park build (that level's mesh has nothing above y 720). The pre-pass drops its cover list and keeps a kill bound on the stairs (both cured from outside in trial 2) | the look at night; a player up 1.29 m flights through a 1.15 m entry; twelve windows bursting round eight players; ring police without their cars; the van on the arc against the level bounds |

Not recommended, for the record (MEASURED `table.py` unless marked):

| what | state | numbers |
|---|---|---|
| bank + its chase chapter (M03_A + M03_B) | **blocked** | 79,408 chunk-table entries (5,680 over); .HVK 6.9 MB (over the 5.0 that has loaded); M03_B's city tiles stand on the bank's coordinates and its walkable ground starts 1.3 km away (READ bank 3.6) |
| both Havana chapters (M11_B + M11_A) | **blocked** | 111,853 entries (38,125 over); 83,464 of them live, so no clean-up helps (READ havana 3.2, tooling 11.1); .HVK 9.2 MB; .prm 115.2 MB |
| Havana's street chapter alone (M11_A) | **not worth it** | builds (72,573: inside the table, 2,941 over the tools' line) but has no interior and no prop of value: 'a weak heist' (READ havana 4.1 B) |
| the prison 'the campaign way' | **not possible as a round** | 1,434 m of legs, three legs do not exist on the mesh; two climbs and a rappel (READ prison 1.4, 3.3, 4.2 R3) |
| the club's roof and helicopter (stage two) | **blocked in the tools today** | F08 as the systems level builds but never ran under a Dead Men map; a helicopter-only third source fails in tools/kl_hvk.py both ways (READ club 4.4, 8.1 item 15) |
| the park as a change to the map on the tab | **blocked** | M06_FA_A's mesh has no polygon above y 720 and no stair tower; the ground up to the ring exists but the AI cannot use it (READ park Corrected 1) |

## 2. Ranking: (what the owner gets) x (how sure it is to work)

The two factors are my JUDGEMENT on the measured facts (a scale of 0 .. 1, not a measurement); the reasons are the point.

| rank | place | gets | sure | product | why |
|---:|---|---:|---:|---:|---|
| 1 | bank, the campaign way | 0.70 | 0.85 | 0.60 | Gets: the place he asked for first, 'the campaign way'; 147 of its 284 m are new (the way down, the vault, back), with the forced vault door as the beat, the alarm and the level's two music sets; but 48 % of the walk is the bank he has, walked the other way (READ bank Corrected 4). Sure: the only place that fits the game today WITH its enemies and the wardrobe; the whole route is one walkable way on the mesh and in the collision once six doors are open; its first door is the very object of the Fragile Alliance bank, which the owner saw open (READ bank 4.1, 8.3) |
| 2 = | prison | 0.85 | 0.50 | 0.43 | Gets: a wholly new place that IO itself meant to be a Fragile Alliance map ('Briefing DL03 - Prison'; Dead Men's own Fragile Alliance theme is cut from this chapter's music: READ prison 2), a riot start, a hold-out in the open, a gate to drive out of; but no money prop of its own (loot is borrowed contraband), and not 'the campaign way'. Sure: everything hangs on one first load (compaction, or another systems level), then seven closures in series, 61 rooms and four untried controller kinds |
| 2 = | club | 0.60 | 0.70 | 0.42 | Gets: a place with no sibling, its own two music tracks and a start inside the loot room; but an empty club, an escape on an island of floor, and no enemy that ever arrives (READ club 8.4 items 6 - 8). Sure: lightest of all, one mesh part, the way out passes the collision walk test, all 27 squads graft with 0 dangling paths (READ club 8.1); unknown: three controller kinds that never ran, the van where there is no floor |
| 4 | Havana, El Capitolio | 0.95 | 0.35 | 0.33 | Gets: the grandest map - the dome, eleven shoot-open display cases, an army with RPGs, daylight. Sure: least of the five - the same first load as the prison, four geometry switches each on the only way, an opening blast that has to be borrowed, no van line yet, the heaviest model file |
| 5 | park, the campaign way | 0.35 | 0.85 | 0.30 | Gets: a new start, the stair tower and a highway finale on a garden he knows; the walk is 296 m against the sibling's 257 m, a quarter of it single file (READ park Corrected 9). Sure: grafts cleanly, the route is free at all 1,271 collision samples, no door on it (READ park Confirmed 10, 11) |

Prison and club are level within what such a judgement can tell. In the ORDER of work the club comes first, for two reasons
that are not in the product: the owner named the club second and the prison 'perhaps', and the club can start at once while
the prison waits for a test in the game (step 2 of 3.3). If that test has passed by the time the bank is done, the choice
between the two is simply his. The prison is the better map on paper; the club is the surer one to arrive.

### 2.1 Where the agents disagree, and what I make of it

1. **Which map first.** The tooling agent orders by tool cost alone: park, bank, prison, one Havana chapter, 'the club last (two
   tool faults and no squads)' (READ tooling 6). The park agents say the opposite of their own place: 'do the others first'
   (READ park 7), and both club agents put the club at 0.5 of a Retomoto. I follow the place agents: cheapest is not what the
   owner asked for, and the bank is nearly as cheap as the park while being the map he named first.
2. **The club's enemies.** Tooling: 2 of 36 squads pass the keep rule, so 'the enemies have to come from F07's police or the
   rule has to be widened' (READ tooling 5.6). Club: 9 squads / 21 guards are plain squads that only lack a behaviour rout and
   are started in the campaign by a child named `Alert`; 19 more after one controller is stripped (READ club 4.2). The second
   club agent built the level with all 27 squads kept: 0 dangling paths, bone check 0 (READ club 8.1 item 17), and found the
   `Alert` child on 7 of the 9. So 'no squads' is too strong; what stands is that a squad without a rout, started that way, has
   not been seen in a Fragile Alliance round on a new map (Retomoto's boardroom squads are started so: READ club 4.2).
3. **The bank has a blocker its own report does not count.** Bank: 'no hard blocker for M03_A alone', and its layer drops
   F07's cover points (READ bank 3.5, 5). Tooling: the pre-pass throws away M03_A's ONLY cover list, the built level has none,
   and no checker reports it (READ tooling 5.5). Together the bank plan ends with zero cover lists: no cover for police, bots
   or player. The cure is one word and is proven offline (the second tooling agent's builds: exactly one list, the same
   problems; MEASURED `table.py`: `tooling/v2/F07+M03_A campaign coverfix` has 19,676 entities, one more than the plain build).
4. **'The mesh is split' on the bank and in the Capitol.** Tooling listed it as a blocker (two large parts joined by nothing).
   Its second agent measured what joins them: the campaign's rappel, straight down, nothing else (READ tooling 11.2). Both
   place rounds stay below the rappel on one part. Not a blocker for the rounds recommended here.
5. **'One part' rested on an unread rule - now read.** The second bank agent could not verify that the game's path search
   crosses the edges between mesh areas, 'the whole one-part statement rests on it' (READ bank 8.6). The second park agent
   READ it in kl2.exe (0x63eaed .. 0x63eafa builds the same portal record for such an edge, the search walks them at
   0x5ce212 .. 0x5ce2e1) and found every stock level built the same way (READ park Confirmed 8). That closes the question for
   all five places.
6. **Have Dead Men's doors ever moved in Dog Days?** Bank and prison first wrote 'never seen'. Their second agents found the
   one sighting: the bank's roller door, by the owner's words ('once the garage door comes open'), while in a solo scripted
   run the same doors stayed shut (READ bank 4.1, prison Corrected 10). One uncontrolled sighting; three maps hang on it.
   *(corrected after the critic: a second, RECORDED sighting exists - a picture of the owner's Retomoto round shows the
   lift's leaves, of the very form of the bank / club / prison leaves, standing open after a proxy played frames 0..75 -
   and the 'stayed shut' run never sent the doors their message (its trigger wants five heads). Section 'Gap closed: the route without a run-time event', G1.9.)*
7. **Another systems level as the way out of the chunk table.** Havana: F08 gives 66,368, 'no chunk problem' (READ havana
   3.2). Second tooling agent: F08 has helicopters and no van at all, and the van code looks its nodes up by F07's names even
   where the van exists (F05, F09) (READ tooling 11.4 item 4). Second prison agent: F05 + prison = 61,504. Second Havana agent:
   F09 = 69,805 - MEASURED `table.py`: that is still 173 over the tools' line, so it is not a way out as built. So: another
   systems level is real for the chunk table and costs the escape vehicle's code; compaction costs one load.
8. **Effort.** Tooling: 0.6 of a Retomoto once for a data-driven tool, then 0.25 - 0.4 a map (READ tooling 0). Places: 0.45 -
   1.0 a map. The second tooling agent doubts the low end: Retomoto's cost was mostly live iteration with the owner, which
   comes back per place whatever the tool looks like (READ tooling 11.5). I plan with the place figures.
9. **Does a hidden static piece still collide?** Prison: 'a static Havok shape stays when its entity is hidden' (READ prison
   6, risk 7). Havana: switched off at RUN time the collision goes (Retomoto's window), hidden at BUILD time is not established
   (READ havana 4.2). MEASURED `sed -n 626,636p re/retomoto_fa.md`: the note itself calls 'hidden geometry has no collision'
   an ASSUMPTION with stock support; the owner then walked in through the blown window (READ CLAUDE.md 2026-10-09 18:09).
   So: run-time switching has one live precedent; for a piece that must go for good (the prison's fence lock) cutting its
   collision placement is the proven way (the bank's yard wall, crossed by bots live: READ bank 8.3).
10. **Weights were first measured without enemies.** Bank and club were corrected by their second agents (bank .prm 59.5 ->
    67.8 MB, club 51.7 -> 58.0 MiB). The prison's, Havana's and the park's numbers are STILL without their guards. ASSUMED
    from those two (53 actors +770 entries / +8.3 MB; 58 guards +963 / +6.6 MB): a few hundred entries and 4 - 8 MB each.
    *(corrected after the critic: MEASURED now, tooling 12.2. As built the squads cost + 380 entries / + 3.6 MB (prison,
    7 squads), + 309 / + 3.0 MB (Havana, 13), + 91 / + 0.5 MB (park, 4). What nobody had counted: the HOST's layer -
    F07's police, AI heisters, vans, spawn objects - costs nothing in a build as built and 1,103 entries + 3.2 MB once
    the build is compacted (compaction drops what no entity names), and the four mask plates 5,416 entries more. Head
    count with F07's 27 police and the 7 heisters, counted in the built scenes: prison 59, Havana 61, park 45; Retomoto
    on the tab 99.)*
11. **A crash every report still lists as open is read.** The 0x686a66 crash is a `ZFakeTarget` standing outside the vision
    space - F07's two unused vans parked under the map (READ re/crash_686a66.md 0; its review: 'ACCEPT WITH FIXES'). Rule for
    every map here: the unused vans stay inside the rooms' bounds or lose that controller.

## 3. The shared work

### 3.1 What pays for all of them

| # | work | who needs it | size | state |
|---|---|---|---|---|
| A | the cover list survives the campaign pre-pass (`'FFCoverList'` into `kl_maps.PASSIVE`) and the verifier reports a level with none | bank, park (their only list sits in a campaign subtree) | one word + one check line | proven offline by the second tooling agent (READ tooling 11.3); MEASURED `grep -n PASSIVE tools/kl_maps.py`: line 98 still has three names |
| B | the material case `TEXT/TILU = MIRRORED` (write `TILED`: the safe case) | club (one walkway material; M01_A has one too) | one line | not done; MEASURED `grep -n "never occurs" tools/kl_mat.py`: the guard is at 397. 'Accept it as it is' is ASSUMED (READ club 8.2) |
| C | authoring by something other than `kl_fa_author`: `kl_graft.build` / `kl_maps.one` take a MODULE (nine names: `HOST prepare_host strip KEEP DROP layer_names complete wire campaign_names`) | every map | a few lines; Retomoto stays byte for byte | not done; MEASURED `grep -n kl_fa_author tools/kl_graft.py tools/kl_maps.py`: kl_graft.py 1076, kl_maps.py 440 - 441. The second bank agent already kept campaign objects by a patch from outside, no file edited (READ bank 8.2) |
| D | a van plan from way points (today the plan is read off a Dead Men Fragile Alliance spline car; no campaign level has one) | every map | a second front end of `kl_map_escape.van_plan`; `van_prepare` already lays F07's van on any plan | not done; MEASURED `grep -n "len(cars)" tools/kl_map_escape.py`: 1075 - 1076 faults without exactly one car |
| E | a route test in the COLLISION, with the blockers named (mesh + .HVK; door sets opened one by one) | every map, before its first live run | make ONE tool of the second agents' scratch scripts | exists five times as scratch only: `G:/kl_scratch/cfa_bank/skeptic/walk6..9.py`, `cfa_havana/skeptic/walk.py walk2.py walk3.py`, `cfa_club/skeptic/walk5.py walk6.py`, `cfa_park/skeptic/sk_walk.py sk_flood.py`, `cfa_prison/skeptic/bypass.py lanetri.py` (MEASURED `ls`). Every design hole that matters in this study came out of them |
| F | doors by a plain 'Activate' from a host timer or box (no campaign proxy kept) | bank (6 sets), club (4 + the entrance), prison (7) | wiring pattern, once | the Fragile Alliance bank does it; one live sighting (2.1 item 6). **Corrected after the critic:** two sightings (G1.9 of 'Gap closed: the route without a run-time event'), and the pattern holds as written only for one-way clips - the bank's glass doors, every club door and every prison cage door shut again on a plain 'Activate' unless the leaf's own stored LAST frame is its open frame (G1.8; three builds made) |
| G | the squad keep rule widened: cut cars / road routs / seat helpers (park's ring police), mounted guns (Havana's bunker), `AttachGeomToBone` (club), start a squad that has no rout (club, prison's 15) | park, Havana, club, prison | an extension of `kl_fa_author`'s STRIP list and starter rule | not done; each cut is unproven live |
| H | per-map entries in tables that sit inside tools: stock soldier rows (`kl_arms.SKILL_LEVELS` holds M09_A / M09_B only - the 'why do I survive being shot so much' fix), `kl_map_ai.PLANS`, `kl_fa_talk.SCRIPTS` (M03 and M06 exist), `kl_str.LEVELS / MUSIC`, `kl_maps.HERO_AT` | every map | data | READ tooling 1 rows 10, 13, 16, 18; 9 claim 16 |
| I | the chunk table: ONE load of a compacted level in the game | prison, Havana | no code, but the test pair has to be MADE first: two `fake-fix` commands, about 13 s each (corrected after the critic) | **Corrected after the critic** (2026-10-11; section 'Gap closed: the pair for live proof 1 ...' at the end): the kept archive `<work>/build/x_chunks/retomoto_wardrobe_compact` (F01_Main.zip 211,562,999 bytes of 2026-10-09 21:26; Retomoto + wardrobe, compacted to 50,703 entries: READ re/prm_limit.md 171) must NOT be loaded as it lies - it and its uncompacted twin each hold 2 FakeTargets outside the vision space, the every-frame write of the 0x686a66 crash (MEASURED `python G:/kl_scratch/cfa_fill0/faketest.py`). The pair for the run is `python tools/kl_fa_bots_dyn.py fake-fix` of BOTH: MEASURED 'PASS: 2 controller(s) off, nothing else changed' twice, 0 targets outside afterwards, archive sha1 9bcdd862... (uncompacted) and cc71c83b... (compacted). Never loaded (MEASURED `grep -i compact CLAUDE.md`: no line) |
| J | a second map page: `kl_expansion.py` knows one page (`PAGE = 2`); the hook takes pages 2 .. 9 and the page builder 2 .. 5 as data | as soon as a SECOND new map exists (page 2 has one free entry, slot F07) | tool work, no hook work | MEASURED `grep -n -E "^(PAGE|DLC|MAPS)" tools/kl_expansion.py`: 89, 90, 118 (five maps in F01 F02 F03 F04 F06). Page 3 is the last button the Arcade page takes while Heister and Guns keep theirs (READ tooling 4, 11.4 item 3). Never loaded: page 3, and a map in slot F07 from a page |
| K | the stream file per map (music, ambience, guards' lines) | every map; the owner's go-ahead each time | `kl_str.py build <level> --extend` + an install | installed file 1,694,610,488 bytes (MEASURED `stat <work>/build/v_bain/over_talk/PC_Def.str`). Adds (READ tooling 5.7, `streamsum.py`; its MB are MiB): bank 55.8, club 85.1, prison 100.2, Havana 38.3, park 31.4 = 310.8 -> 2,020,507,909 bytes with all five (arithmetic mine), 121 MiB under 2^31. No stream file past 2 GB has been tried |
| M | a pre-pass that takes a named controller kind off kept map nodes - the fall-back when a kind Dog Days never ran faults at load | bank (`LightToggle`), club (three kinds), prison (four) | small; today `--m-drop` takes whole top-level subtrees only and `--flat` whole classes | not written (READ club 3.5, bank 6 item 3, prison 3.5); needed only if a first load faults |
| L | the data-driven authoring tool (`kl_fa_campaign.py`, specified in tooling 3) | maps three to five | 0.6 of a Retomoto (an estimate) | not written. Its sketch cannot yet rebuild Retomoto (48 authored world places and 8 field edits have no section) and the files it would generalise are tuned daily by another session (READ tooling 11.4 item 1) |

### 3.2 What must exist BEFORE the first map (the bank)

A (cover list), C (module interface; or the outside patch of bank 8.2 for a first build), D (van from way points), the M03_A
entries of H, and E if the second map is not to repeat the first one's surprises. NOT needed for the bank: B (club only),
I (the bank fits without compaction), J (the bank takes the last entry of page 2), L (cut it from two finished modules, not
from one). The bank does need one thing proven live that no tool gives: step 3 below.

### 3.3 Order of work

Each step: what goes in, and the check that says it is done. Steps 2 and 3 need the game and the owner away; the rest is offline
until a map's own first load.

1. **Three small tool fixes** (A, B, `HERO_AT` entries). In: tools/kl_maps.py 98 and 103, tools/kl_mat.py 397 - files other
   sessions are editing, so by whoever holds them. Check: the trial grafts repeat with the numbers of section 1; F07 + M03_A
   and F07 + M06_A hold exactly ONE `FFCoverList` (19,676 and 19,158 entities); the stock command builds F07 + M05_A
   (26,106 entities, 52,935 entries, 11 problems).
2. **Live proof 1: a compacted level.** (**Corrected after the critic**, 2026-10-11; the measurements are in the section 'Gap
   closed: the pair for live proof 1 ...' at the end.) NOT the two kept archives as they lie:
   `<work>/build/x_chunks/retomoto_wardrobe_compact` and its uncompacted twin `x_chunks/retomoto_wardrobe` each hold the two
   parked FakeTargets of the 0x686a66 crash (MEASURED `faketest.py`: 2 of 3 outside the vision space), so a fault in the run
   could not be told from compaction's. In: the pair made offline first, into two NEW folders (names proposed), about 13 s each:
   `python tools/kl_fa_bots_dyn.py fake-fix "<work>/build/x_chunks/retomoto_wardrobe" "<work>/build/x_chunks_ff/retomoto_wardrobe"`
   (A, the control) and
   `python tools/kl_fa_bots_dyn.py fake-fix "<work>/build/x_chunks/retomoto_wardrobe_compact" "<work>/build/x_chunks_ff/retomoto_wardrobe_compact"`
   (B, the test). Made right when each ends 'RESULT (fake-fix): PASS: 2 controller(s) off, nothing else changed' and
   F01_Main.zip has sha1 9bcdd8620e5cf7402aad1b21f1f3e36d5eb0201a (A) and cc71c83b3ee4fc50bcf7b78c42ef14f09b65f3fc (B):
   MEASURED, the tool repeats to the byte. It is a clean pair NOW: B is exactly today's `kl_chars.py compact` of A, every
   member byte for byte (MEASURED), and A is the build the owner played (READ CLAUDE.md 'INSTALLED FOR THE OWNER 2026-10-09
   21:50') less the FakeTarget controller on the two parked vans (MEASURED `pair.py`: 2 of 25,732 nodes differ). Each folder
   holds its KLJoin.ini and KLWardrobe.ini (compaction rewrote the latter's 16 model numbers) and NO KLGuns.ini: the pair
   has no gun looks, no bots and no talk, so the run settles compaction with the wardrobe, not gun looks on a compacted
   level (compaction does not rewrite KLGuns.ini). Check: B loads by direct boot and from the menu; HUD, fonts, effects
   and post filters look as in pictures of A taken under the SAME hook and ini (the 2026-10-09 pictures are of the unfixed
   build under an older hook); a round reaches GO; no int3; under the TEST hook with `[Vis] Log=1` the log says 'record
   0xff has never held no cell' (READ klhook/klvis.c 27-29). If B faults or looks wrong, A is run the same way before
   compaction is blamed. Decides: prison and Havana under F07. If it fails: those two wait for a smaller systems level,
   which means the van code freed of F07's names first.
3. **Live proof 2: the bare bank and its doors.** In: `python tools/kl_maps.py one <out> F07 M03_A --campaign --keep` (with
   fix A), `python tools/kl_graft.py lighten ... --load trim,slim`, the hero put in the yard at (300, 200, -4350) by
   `python tools/kl_fa_author.py hero`. Check (a), the bare boot: it loads with 28 rooms and the 22 alarm lights, the doors
   stand as the file has them, a shut door stops a scripted walker. Check (b), the doors: 'Activate' sent to the six door
   sets of bank 8.3, the dock door first - from one kept host timer if such a timer runs on a direct boot (ASSUMED), else in
   the first round without squads of step 7; the roller door rolls up and the walk reaches the vault door, the vault, the
   hall and the street. Decides: the door pattern F for bank, club and prison, and `LightToggle` for bank and prison.
   *(corrected after the critic: 'Activate' sent as the file stands will show the two GLASS doors open and shut again
   within 4 s - their leaves need LAST frame 50 first (G1.8 of 'Gap closed: the route without a run-time event'). And the route can be had with no
   event at all: the 'campaign open' build of G1.2 is the safer first boot; this proof then decides the beats, not the round.)*
4. **The module interface** (C). In: the nine names. Check: Retomoto rebuilt by `python tools/kl_fa_loot.py test` gives the
   same archive, member for member, as before the change.
5. **The van from way points** (D). In: way points instead of a spline car. Check: fed M03_FA_A's own two spline routes as
   points it reproduces that map's existing van (van-check 0 faults); then the bank's measured through lane (77 m: bank 4.3)
   passes the lane test.
6. **The route test as a tool** (E). Check: it reproduces the second agents' findings - bank: six sets, each necessary;
   Capitol: four switches; prison: seven closures; park: 1,271 samples free.
7. **MAP 1, the bank.** In: section 4.1; a module on `kl_fa_author`'s pattern; the M03_A entries of H; steps 1, 3, 4, 5.
   Check offline: `kl_fa.check` 0 CRASH / 0 BROKEN, bone check 0, chunk table under 69,632 (65,640 measured before gun looks,
   which add 59 - 94: READ tooling 3.5) *(corrected after the critic: 212 on a build that is not compacted - MEASURED on the park and on the tab's Retomoto, tooling 12.4; the bank then stands at 65,852 by arithmetic)*, exactly one cover list, the route test free with the doors open, van-check 0 faults,
   no unused van's target outside the rooms' bounds (2.1 item 11). Check live: a round without squads (start, doors, loot,
   exit box, van), then with. Then lighten, wardrobe, bots, gun looks, talk (`SCRIPTS['M03']` exists), music (+56 MB, the
   owner's go-ahead), the last entry of page 2.
8. **The owner plays map 1 and names map 2** (club or prison: section 2). In: the map on the tab. Check: his word.
9. **A third menu page** (J), once a second new map is to be delivered. Check: the expansion build's menu check; live: page 3
   opens, a slot loads from it, and the stock page and page 2 still load their own maps in the same process.
10. **MAP 2, the club** (stage one). In: fix B; `--m-drop "Boundaries!*"`; section 4.2; rule G for its squads; F07 police on
    the pavement's mesh strip so that something arrives; the van at a fixed height; bounds and kill boxes at the slab's three
    open edges; music (+85 MB). Check: the first load settles the three never-run controller kinds (each has a drop-it
    fall-back: club 3.5); the route test office -> pavement with four door leaves and two seals out; `kl_fa.check`.
11. **MAP 3, the prison** (needs step 2). In: section 4.3; build -> lighten -> wardrobe -> compact (compaction BEFORE gun
    looks: it does not rewrite the gun file, READ tooling 3.5); `--m-drop "Specials!LevelBounds!*"`; the four untried
    controller kinds stripped or proven; the fence lock's collision cut; loot on the ground floor only in a first build.
    Check: bone check 0; chunk table 63,528 + guards + guns under 69,632; the route test with seven closures open.
    *(corrected after the critic: the chain was run to its end with the round's squads, F07's police / heisters / vans
    and the gun looks - build -> lighten -> wardrobe -> compact -> gun looks -> `lighten --load fxc`. The check is
    **65,509 entries with the 8-mask wardrobe; with the four Payday 2 plates it is 70,925 and FAILS (two plates at most:
    68,217)**. Gun looks add 503 to a compacted build, and the other order is refused by the tool itself. .prm 87.5 MB;
    five load blocks 166 MiB (Retomoto on the tab: 173). And `kl_maps.audit` cannot pass this chain until three small
    tool fixes are in - the first build's chunk line in result.json, and steps.json after `compact` and after the last
    `lighten`; with them a compacted control build passes at every step. MEASURED, tooling 12.2 - 12.7.)*
12. **MAP 4, Havana** (needs step 2). In: section 4.4. FIRST a bare direct boot that fires all four geometry switches, before
    any table is written (READ havana Verdict after the checks). Check: each of the four frees its leg in the game; then as
    map 1. Watch the hook's memory lines on a second and third load (.prm 84 MB and more).
    *(corrected after the critic: with its 13 squads, the host's layer and the gun looks the model file is 91.6 MB
    (8 masks) / 93.0 MB (12) - the heaviest built so far; the tab's Retomoto has 79.9. Chunk table 60,902 / 66,318: it
    fits both ways. `--armour=0,3` on the wardrobe takes 6.6 MB off. MEASURED, tooling 12.2, 12.3, 12.5.)*
13. **MAP 5, the park - optional.** In: section 4.5 and the trial-2 recipe (park 3.3). Check: as map 1; the tower climbed by a
    scripted walk first.
14. **After two authored maps: the data-driven tool** (L), cut from the two modules, with sections for 'place a map node' and
    'edit a field'. Check: both maps rebuilt from their data files to the same archives.

## 4. The rounds

Ten lines each, the round as it stands AFTER the second agents' corrections. Places are the objects' own (MEASURED by the place's
agents) unless marked GUESS.

### 4.1 Bank, the campaign way (M03_A) - READ bank 4.3, 8.3, 8.4

1. START: the secure yard under the back wall where the campaign's ropes end ((-35 / -151, 200, -4525)); two stacks of four
   beside the dock door at about (150..450, 200, -4350) and (700..1000, 200, -4350), TRAITOR row about (300..1000, 200, -4000)
   (GUESS on measured mesh; a parked armoured transport at x -30..190, z -4130..-3590 stops the rows moving west).
2. ROUND START: 'Activate' to the dock roller door `M03_A_Garage_01a\SI0201_M03_BackDorAnim_01` (560, 550, -4706; the doorway is
   x 385..735, 3.5 m) - and to glass doors 1 and 2, the four airlock leaves and the two hall / foyer leaves, which stay open:
   only the vault is gated (the second agent's condition; six sets in series, two of them met only on the way out).
   *(corrected after the critic: the two glass doors do NOT stay open on 'Activate' as the file stands - their clip goes
   to 135 degrees at frame 50 and back to 0 at frame 100, and the leaves store -1 / -1 = the whole clip. Write LAST 50
   into the four leaves (built: G1.8). The dock door, the six slide leaves, the vault door and the rods are one-way clips.)*
3. FIRST FIGHT: dock and vault lobby, 13 guards (y 201..243, x -901..834, z -7490..-5008), started with the door.
4. THE WAY DOWN: guard pairs at (-122..-18, -158, -9265..-9145), (-98..-52, -559, -10673..-10548), (326..719, -959, -11889..-11725).
5. THE BEAT: a box at the campaign's `TB_VbByVault` (460, -714, -12152) starts the six locking rods one by one (8 s steps: GUESS)
   while 14 guards and police come down the stairs behind the crew; then the vault door `...VaultEntrance_01a\
   SI0102_M03_BankVault_Door_PRE_01` (opening (400, -960, -12640)) swings, the alarm lamps and siren start, the music changes.
6. LOOT: 6 briefcases at the deposit-box walls about (200 / 400 / 600, -960, -13330) and (90, -960, -13230 / -13030 / -12830),
   one on the trolley (199, -890, -13171), hidden until the door is open; 4 stacks at the teller counters of the hall, on the
   public side (the west teller place is 150 off the mesh). About 2.6 million (places and values GUESS). The barred art store
   (statue (966, -960, -12933)) stays hidden: money a bot cannot reach can hold the bots.
7. AFTER THE BEAT: the hall needs F07 squads re-placed (the campaign's eight hall guards have no rout); the plaza's seven squads /
   20 men (two SWAT fours with M4s) start when a criminal reaches the foyer; returning police on the street at
   (-1842..-1437, 705, -9621..-9542) and (2016..2178, 706, -9598..-9418).
8. ESCAPE: out of the front entrance (300, 800, -9350) - no door, a 2.0 m gap between two glass wings at x 200..400, z -9410.
   F07's van on the measured through lane: the designers' in-road as far as (-231, 707, -12332), straight to (949, 704, -11105),
   then their away road (2473, 705, -11177) -> (3958, 713, -11173); stop about (850..950, 704, -11200..-11105), nose north-east
   to east (GUESS; the first agent's stop at (250, 707, -10700) does not work: nose to the bank, a 120-degree pivot).
9. BOUNDS: the campaign's three stay at the front ((355, 943, -14140), (3763, 843, -10211), (-2837, 928, -10916)); F07's boxes
   along the yard's north wall (z about -700) and east fence (x about 2400) (GUESS).
10. MUSIC AND BOTS: `BO_Sus_LOOP` (four layers, 144 s) from the start, `M03A_Bustout_A_I` (168 s) from the vault door. The seven
    bots walk one mesh part of 566 polygons: 120 m in, 164 m out, no link, no hook part.

Open: do the five door sets after the roller door answer 'Activate' (the glass leaves and rods store frames -1 / -1; corrected after the critic: read in kl2.exe - that is the whole clip, one way for the rods, open AND shut again for the glass leaves: G1.8 of 'Gap closed: the route without a run-time event'); do shut
doors hold a player; `LightToggle`; is the vault's blast fun or simply lethal (the owner's call); the van beside the bound at
x 3763; the bots at the dock doorway, where they already die on the Fragile Alliance bank; the kept guards' voices and both
music sets are silent until the stream file grows.

### 4.2 Club, 'Last call' (M05_A) - READ club 4.2, 4.3, 8.2, 8.4

1. START: Yoko's office, two rows of four at x 2700..3050, z 2420 and 2560, y 342 (GUESS rows; floor and free space measured;
   all eight in one mesh polygon of 5.3 x 2.8 m). TRAITOR points east of the desk, about (2933 / 3050, 342, 2300) (tested free).
   The ENTERS_BANK box round the START row, inside the office (so that the office loot counts for the bots).
2. GO + 2 s (GUESS): 'Activate' to the door groups `SI0108_M05_DaughterRoomDoorA_02` (leaves at x 2496..2504, z 3167..3488) and
   `...DoorB_01` (x 1496..1504), and 'Doors_Opening' to the music's `GeomActivator_Door_01 / _02`, or the music stays muffled.
   *(corrected after the critic: as the file stands that opens the office for about two seconds - the four leaves' clip
   slides open at frame 30 and is shut again at frame 60, and they store -1 / -1. Write LAST 30 into `D1 D2 D04 D05` (the
   campaign's own `DoorCtrl` number; built: G1.8), or take the leaves out at build time (built and walked: G1.3).)*
3. FIRST FIGHT: the front office - `WaitingRoom` at (2085, 354, 3178), (1967, 353, 3486); `YokoGuards` at (2387, 354, 3319),
   (2378, 354, 3442) (inactive in the file: needs its flag set).
4. LOOT: six briefcases on and beside the desk `PC0100_M05_OfficeTable_01` (2700, 340, 2260) and the sofa tables
   (2988..3138, 380, 2530..2641); three at dance floor 1's bar (-1500, 20, 1006); ticket counter (300, 0, -1200); coat check
   (-400, 100, 0) - each on the PUBLIC side of its counter (four of nine prop origins are over 1 m off the mesh). The upstairs
   bars ((1700, 860, 0), (-3185, 460, 696)) only once the stairs are proven. 15 objects, about 2.8 million (GUESS).
5. ROUTE: office -> walkway (780, 371, 2747) -> dance floor 2 (-864, 40, 2491) -> dance floor 1 (-1100, 20, 1150) -> stair
   landing (-55, 160, 320) -> wardrobe (-4, 180, -240) -> entrance hall (-414, 100, -604) -> queue lane (105, 20, -1500) ..
   (105, 20, -2600) -> pavement: 187 - 191 m on one mesh part of 401 polygons; the lane is 0.96 m wide on the mesh.
6. THE BEAT, 'exit blocked': the entrance door is shut from the round start (the campaign's `Doors!Entrance!CloseEntranceDoor`)
   and the lane sealed by `Inside_Entrance_01a\HeroColi` (x -13..369, z -2612..-2335) and `\Plane01` (z -2538); both go when
   the two dance-floor squads are dead, or after 75 s (GUESS); three hunters come in from the wardrobe (-97, 183, -146).
7. ENEMIES: 21 guards in 9 squads as they stand (7 of the 9 are started by their `Alert` child), 19 more once
   `AttachGeomToBone` is stripped; all stand inside from the load. To have anything ARRIVE, F07 police on the pavement's mesh
   strip (x -3765..5786) - not in the 0.5.
8. ESCAPE: F07's van along z -3100 at a fixed height y 32, boarding box at about (660, 32, -3100) on the only collision floor
   outside: x -1200..1800, z -3460..-2580 (30 x 8.8 m). The drive in must be shorter than 60 m and must not cross the waiting
   crew (the first agent's 62 m from x -5200 does both). Exit box about (300, 150, -2950) half (1400, 250, 450) (GUESS).
9. BOUNDS: the campaign's five go (`--m-drop "Boundaries!*"`; four stand active on the route, e.g. (200, 175, -251),
   (399, 165, 218)); bound trios and kill boxes at the slab's three open edges (GUESS) - they punish, they do not stop.
10. MUSIC: the club's two tracks from the map's own 84 audio nodes (`M05_A_Club_Layers` 202.7 s, `M05_A_Club_2_Layers`
    309.7 s), with the light show if `PositionLightControl` runs. Stage two (roofs, glass roof, helicopter at about
    (7300, 1880, 4000)) is all in the level except the helicopter.

Open: the three never-run controller kinds; whether a door group opens and stays open without its `DoorCtrl` (corrected after the critic: it does not as the file stands - G1.8 of 'Gap closed: the route without a run-time event'); whether
`DeactivateGeom` frees `Plane01` (nothing in the campaign ever switches it); a van over a strip without floor; what a level
bound does to someone at the slab's rim; nothing DRAWN was tested in the van's lane; the look of the club without its crowd
(1,980 members in the campaign) and with three lamp materials undrawn.

### 4.3 Prison, 'Cell Block B' (M08_A) - READ prison 4.3 and its Verification

1. START: the ground floor at the east end of cell block B, row at x 9800, y 0, z 13150..13650 (GUESS; a 3.6 m strip between
   a burning rubble pile and the east wall, a fire box 2.7 m away). Eight shotgun guards stand 3 - 7 m east and 9 m above it
   (x 10061..10541, y 920): every guard waits for GO.
2. OPENING: the lockdown announcement; the six-man SWAT squad storms in through the west door (5758, -2, 13400), 50 m down the
   hall (its own defend box is outside at (4568, -2, 13400): moved in).
3. LOOT, first build: 10 - 12 contraband stacks (the park map's dope bag) on the hall's ground floor only. Later: the guards'
   cash (the diner's suitcase) at the console of control room B (10100, 950, 13400) - behind slide doors and stairs that carry
   a campaign kill bound; the tower top (9072, 1925, 8799) as the greedy option, 323 m back down. About 4 million (GUESS).
4. ROUTE, one mesh piece of 502 polygons, 194 - 206 m: hall (8701, 5, 13304) -> south lobby (8169, 22, 12417) -> cage door B
   (8302, 20, 12223) -> ground passage (8295, 23, 11329) -> cage door (8300, 21, 10527) -> yard (8383, 3, 8809) -> last gate
   (8299, 20, 7071), (8299, 21, 6019) -> south yard (8203, -28, 4960) -> fences (9300, 0, 4900), (9941, 0, 4913) -> car park
   (12455, -1, 6921) -> the van.
5. THE BEAT: the yard - 40 m of open ground under the walkway ring and the tower with the south gate shut; the last gate and
   both fences open 30 s (GUESS) after the first heister enters. The four cage doors of this stretch have no path blocker,
   so the hold must be scripted in the squads' steps, or AI walks into shut doors.
6. ENEMIES: 7 campaign squads / 25 guards as they stand - 8 shotguns on block B's ring, the SWAT six, 6 riflemen at the yard,
   5 at the gate ((12382..13017, -7, 8421..8847), on the van's stop); 15 more squads / 24 men (tower machine guns, tear gas)
   need a rout authored.
7. ESCAPE: F07's van heading east along z 8800 on ground at y -20 (not 0). The lane is clear from x 11000 to 13200 and from
   13300 on; the fence the van must pass stands at x 13226..13300 (a static lock x 13226..13936 inside the wall), the wall's
   portal at x 13958..14041. The first agent's stop (12900) puts the nose at the fence and its waiting place (11300) under the
   gatehouse canopy: both are to be re-placed (open design work; no corrected place was measured).
8. DOORS: seven closures in series, no way round any one - cage door B, two in the ground passage, two of the last gate, two
   fences. Every leaf is a key-framed body that can be taken out at build time (the round stays, the beat goes).
   *(corrected after the critic: built and walked, G1.4 - 21 bodies (each fence has a hidden twin) AND the kept
   `PathBlocker_CageDoorB`, which must be written `eNotBlocking` or no AI passes. For the beat instead: the 17 cage leaves
   need LAST 50, or 'Activate' opens and shuts them within 4 s (G1.8).)*
9. BOUNDS: drop the campaign's three (`--m-drop "Specials!LevelBounds!*"`: one lies across the ground passage at
   (8295, 23, 11329), half (1000, 400, 250)); author one behind the west door (x about 5600) and one outside the gate
   (x about 14200) (GUESS) - the west door is an open doorway to the kitchen yard.
10. MUSIC: `Prison_L2` (block B's) from the start, `Prison_L1` from the yard on (two three-layer sets of 250.3 s, +96 MB);
    `FA_SlashMixPrison`, Dead Men's Fragile Alliance theme, is in the merged stream file already and needs no new one.

Open: the first load (compaction, or F05 as the systems level); the doors; the four controller kinds no stock level runs
(all four are loaded because the map cannot be cut); 61 rooms / 242 gates in a graft (corrected after the critic: no longer
open as a count - 242 is past stock's 207, but nothing in kl2.exe is sized by a level's gates and the prison is under every
per-room and per-frame size found, 67 of 1,024 frusta a frame against stock F09's 87: prison 'Gap closed: 242 gates'; what
stays open is the load itself); whether the fire boxes burn a player;
the dope-bag prop on another level's loot object (only the suitcase is proven offline).

### 4.4 Havana, 'El Capitolio' (M11_B) - READ havana 4.2 and its Verification

1. START: under the dome at the campaign's checkpoint 4 ((33981, 808, 30387), (33987, 808, 30165)); the row at
   x 33,900..34,000, z 29,900..30,900 facing +x down the hall (33 of 33 places are free cells; floor y 800).
2. ROUND START: an opening blast borrowed from F07 (the level has none at the corner: the campaign's bang is the tank's shell),
   and BOTH tank swaps fired at once - `SO0201_M11_Corner_01` -> `..._CornerBroken_01` (collision x 31,432..32,350,
   z 28,500..29,616) and the stair barricade `SO0201_M11_BarricadeXX_01` (27170, 0, 28516) taken away. Both are on the only
   way out.
3. THE BEAT: The7's sandbag bunker across the hall at x 38,700, manned; when its squads are dead, the campaign's `BoomBoxDust`
   (38613, 902, 30398) with its emitters, the swap `SI0100_M11_BarricadeB_01` -> `..._Broken01` (38697, 800, 30415) AND
   `...LastSeven_01\GeomDeactivator_Coli`, which removes the invisible block in the wing's only door
   (x 39,458..39,754, z 31,295..31,374). Without that fourth node nobody reaches the loot.
4. LOOT: 11 glass display cases - end room (42631, 878, 32550), (42610, 878, 31249), (42020, 878, 31445), (42020, 878, 32405);
   corridor (39358, 936, 31012), (40797, 936, 32157), (40803, 936, 31673), (40197, 936, 32467), (40203, 936, 31363),
   (39550, 800, 31915), (39722, 810, 31537) - 5 paintings, and briefcases on the table (42650, 802, 31915). About 3.95 million
   (GUESS). The cases are the prop family of Retomoto's samurai cases (same effect template in both levels).
5. ENEMIES: 3 soldiers in the wing, the bunker's crews once their mounted guns are stripped; 'police' = the army: 11 squads / 24 men
   on the terrace, the side stair and the square, held until the crew leaves the wing with loot. Two of those squads stand
   11 m from the START row ((33928, 827, 28842), (33400, 803, 28848)) and need other places.
6. THE WAY OUT: hall -> front door -> through the hole in the corner (the campaign's marker (32095, 888, 29022)) -> gallery
   (28380, 840, 29370) -> side stair (27540, 470, 30193) -> (27168, 200, 29095) -> (26667, 20, 27758) -> the square. The side
   stair is the only way between the floor (y 800) and the square; about 460 - 470 m in all for a bot, one mesh part of 606.
7. ESCAPE: F07's van on the square, stop about (27000, 0, 22600) (the road is y 0, the mesh floats at 20). A clear straight
   run of 61 m lies there (x 23,500..29,600 on z 22,200..22,600; the longest on the square is 73 m, F07's own drives are
   121 - 152 m). The square is closed for players at both ends and cratered: no arrival from out of sight, no 'drives off down
   the road', without more design (open).
8. BOUNDS: the campaign's two stay ((21235, 348, 22324) half (1172, 459, 108); (22814, 348, 29859) half (3180, 459, 92));
   invisible walls already close the square east and west.
9. MUSIC: the chapter's one three-layer set, `M11_Havana_Layer_A / B / C`, 162.6 s, 31.2 MB.
10. BEFORE ANY OF IT: the chunk table. Compaction: 46,081 bare, 58,992 with the wardrobe (.prm 84.4 MB) - MEASURED by me,
    `havana_ward.sh` (wardrobe '15509 of the base's 24308 dead indices taken', then 'compact: 74454 -> 58992', bone check 0).

Open: compaction in the game; all four switches really removing static collision (each is on the only way); which of the
bunker's two states shows before its blast (both are flagged visible); the hall's light under a Dog Days level; the van;
the AI gets no path blocker at any gate (the mesh runs through the standing bunker wall in a 79 cm slot); loyalists as
allies and the Hind as a police helicopter are untried extras.

### 4.5 Park, 'Exchange' (M06_A) - READ park 4.2 and its Verification

1. START: the pagoda's floor, two rows of four at x 560..1040, z 2260..2440, y 635, facing south (GUESS rows; they lie on
   mesh polygons 54 / 55 / 56, a cross of 20.0 m2 with a 1.5 m opening south and north). TRAITOR about (700..900, 635, 2700).
2. ROUND START: the campaign's own `Gameplay!Enemy!01_Bridge!Activator_ShatterPavillionWindows` (one node kept) bursts the
   pavilion's twelve windows round the crew; the garden squads start; the action music starts.
3. LOOT: six briefcases round (802, 626, 2343); one stack beside each of nine props - tea house (802, 173, -2477), shrines
   (13, 174, -1615), (-1972, 163, -6177), (-3479, 180, -6402), (1246, 180, -11631), statues (-522, 177, -4807),
   (-1118, 202, -4657), (328, 192, -8833), (-292, 192, -9041) (each 0 - 99 from the mesh). About 3.15 million (GUESS).
4. ROUTE: pagoda -> south bridge (800, 622, 1650) -> landing (814, 392, -651) -> garden -> the tower's entry on its east side
   at about (80, 220, -11465) -> 75 m of spiral, 23.5 m up -> top (106, 2587, -10934) -> the median's only gap (x 80..320,
   z -9300..-9450, 2.4 m) -> the van: 296 m on one mesh part of 584 polygons.
5. THE BEAT: the stair tower. The campaign's box `TriggerBox_OnStairs` (9, 689, -10945) (on the third flight) turns the lights
   under the highway off, starts the ring police and the music's third layer, and unleashes the sniper above the climbers
   (18, 1526, -11418).
6. ENEMIES: 25 of Retomoto's men in the garden - but two squads' defend boxes are ON the START floor (800, 626, 2353) and need
   new places, and the three men of the bridge squad stand beyond a level bound, never reachable. 10 police + 5 SWAT on the
   ring at (-3806, 2467, -7352), (-2076, 2518, -8634), (-2103, 2527, -9990) and about (-6467, 2402, -6325), their car
   arrivals cut out.
7. ESCAPE: F07's van on the ring's inner carriageway (radius 8,244), stop at the campaign van's own place
   (-2572, 2498, -7933); in from the west along 60 m of arc; away east no further than about 40 m (the level bound's warn
   boxes begin 42.8 m east of the stop, its kill box 55.4 m), or the two highway bounds are re-placed.
8. BOUNDS: the campaign's `LevelBound_Highway_01` (-6132, 2594, -7113), `_02` (3400, 2780, -8732) and `LevelBound_PagodaBridge`
   (803, 545, 4454) stay; `LevelBound_StairsBottom` (-197, 659, -10960) MUST go (it kills on the only way up). Returning
   police not at (813, 2580, -9226): that is 6 m from the median's gap.
9. BUILD RECIPE: the cover list kept (fix A), the stairs' bound and the exit cut scene's set dropped (`trial2.py`: 18,626
   entities, 52,433 entries, still exactly the ten layer findings).
10. MUSIC: `RetoMotoAction` in three layers (171.4 s, 32.9 MB), the track the park on the tab does not play.

Open: a player through the tower's 1.15 m entry; whether the windows hurt eight players inside; ring police without their
cars; a level bound against passengers of the van (open for the tab's maps too); a bot that leaves the bridge sideways cannot
path back; whether the round is good - 296 m, a quarter of it single file, on a garden the owner knows.

## 5. What is ASSUMED or GUESSED under these decisions

About the game and the tools (each could move a rank or an order):
1. A compacted level loads and looks right. Nobody has loaded one (READ re/prm_limit.md 147). The prison and Havana rest on it,
   or on (2).
2. A Dead Men map runs under a systems level other than F07. No such map has run; the van code names F07's nodes (2.1 item 7).
3. Dog Days plays Dead Men's key-framed doors on a plain 'Activate'. One sighting by the owner's words, one scripted run in
   which the doors stayed shut (2.1 item 6). Bank, club and prison rest on it; the fall-back (leaves taken out at build
   time) keeps the rounds and loses the beats.
   *(corrected after the critic: two sightings now, the second recorded (G1.9); the routine is the same in both exes and
   the doors' flag sets act as 991 / 244 stock controllers do (G1.7); the fall-back is BUILT for all four places and the
   routes are free in the built collision files (G1.2 - G1.5).)*
4. A door leaf that stores frames -1 / -1 plays its whole clip (bank's glass leaves and rods: bank 8.6), and a door group stays
   open without its `DoorCtrl`, which carries a time value (club 8.3).
   *(corrected after the critic: the first half is READ in kl2.exe and true - and for a there-and-back clip 'the whole
   clip' ends SHUT. The second half is false for the club's office doors, the bank's glass doors and the prison's cage
   doors; the `DoorCtrl`'s 'time value' is the clip's open FRAME. Cure: the leaf's own LAST frame (G1.8).)*
5. A shut key-framed door stops a player. Retomoto: the tower car's doors did, the boardroom door did not.
6. `DeactivateGeom` removes the collision of a STATIC piece. One live precedent (Retomoto's window). Havana rests on it four
   times, the club twice, the bank's vault swap once.
   *(corrected after the critic: no longer as a fall-back - Havana's five pieces and the club's two seals are taken out
   at build time in G1.5 / G1.3 and the routes are free; `DeactivateGeom` is needed only for the bangs as events.)*
7. The controller kinds no stock Dog Days level runs do no harm at load: `LightToggle` (bank 22, prison 7),
   `PositionLightControl`, `ZIKLNKOBJ` + `StartAnim`, `ShotActivateDamage` (club), `EffectDmgBox`, `AnimSequence`,
   `ZHingeConstraint` (prison). Each can be stripped instead.
8. Squads cut out of their campaign form stand and fight: without a behaviour rout (club, prison), without
   `AttachGeomToBone` (club: 'ASSUMED harmless'), without car, road rout and seat helper (park), without mounted guns (Havana).
9. A level bound does nothing bad to the passenger of a key-framed van (bank at x 3763, park's ring; open for M02 / M03 too).
10. The wardrobe's cost on maps where nobody built it: the park about +16 MB (.prm about 52 MB). (Havana's is measured now:
    +16.2 MB, section 1.) And the enemies' cost where nobody built them in: prison, Havana, park (2.1 item 10).
    *(corrected after the critic: both are built now - the park's wardrobe is + 16.2 MB (8 masks: .prm 40.9 -> 57.1 MB with
    its squads and the host's layer in; 58.0 with the gun looks), the enemies' cost is in 2.1 item 10. Tooling 12.2, 12.5.)*
11. More than Retomoto's 99 actors on F07's run-time heaps is untested (the prison with all its usable squads); the stock
    files give no people limit either way (READ tooling 11.2).
    *(corrected after the critic: counted in built scenes - the prison's ROUND has 59 actors (25 + F07's 27 police + 7
    heisters), Havana's 61, the park's 45; only the prison with all 29 squads the keep rule passes goes over: 112.
    Tooling 12.6.)*
12. A stream file near 2 GB works; a three-layer music set merges like Retomoto's two-layer ones (havana 4.2).
13. `MIRRORED` on the U axis of one club material would draw right if accepted; writing `TILED` avoids the question.
14. The collision bits 0x108 are 'hero blockers' by a census of names in both games; whether they stop an AI heister was not
    read (havana Verification). The ColiObj pieces are 'not drawn' by name only.
15. Nothing DRAWN stands in the club van's lane (only collision and entity origins were tested), and the drawn pavement goes on
    where the collision floor ends.
16. Money a bot cannot reach holds the bots (READ in `kl_fa_bots`' docstring by the bank's second agent): hidden or barred
    loot must stay out of their plan.
17. The 0x686a66 rule (unused vans inside the rooms' bounds) is read and reviewed, not yet seen to end the crash live.

About the designs (every one a GUESS until placed and seen):
18. Every START row, TRAITOR row and returning-police point; every loot place and value and every loot sum (2.6 / 2.8 / 4 /
    3.95 / 3.15 million); every exit box; every authored level bound.
19. Every timing: the rods' 8 s steps, the club's doors at GO + 2 s and its 75 s limit, the prison's 30 s hold.
20. Every van stop that was corrected: the bank's (850..950, 704, -11200..-11105), the club's (boarding box (660, 32, -3100),
    drive under 60 m), the prison's (to be re-placed west of x 13226), Havana's (27000, 0, 22600) with no arrival leg, the
    park's away leg of about 40 m.
21. That an empty club, a closed square and a second round on the park are what the owner wants: his call, after seeing them.

About the estimates:
22. Every effort factor (0.5, 0.5 / 0.9, 0.7 - 1.0, about 1.0, 0.45; 0.6 for the data-driven tool) is a judgement. All five
    maps at the place figures: about 3.2 - 3.5 Retomotos (my sum).
23. The two factors of the ranking in section 2 are mine.

## 6. Files of this job

- `G:/kl_scratch/cfa_synth/table.py` -> `table.txt` (every kept trial `result.json`, read back).
- `G:/kl_scratch/cfa_synth/havana_ward.sh` -> `havana_ward.out`, `h1_build.log` .. `h5_impact.log`: F07 + M11_B `--campaign`,
  lightened (`trim,slim,fxc`: archive 362.0 -> 223.2 MB), wardrobe (.prm 69.0 -> 85.2 MB, table 74,454), compacted (58,992,
  .prm 84.4 MB, archive 249.1 MB), `kl_impact.py`: problems 0. Its folders `<work>/build/cfa/synth/` hold notes only
  (196 KB); every archive is deleted.
- The six reports' own scratch folders: `G:/kl_scratch/cfa_<place>/` and `.../skeptic/`, `G:/kl_scratch/cfa_tooling/`,
  `G:/kl_scratch/cfa_tooling_v2/`; their trial notes `<work>/build/cfa/<place>/` (6.6 MB in all, no archive left: MEASURED `find`).

## Gap closed: the pair for 'live proof 1' carries the 0x686a66 FakeTargets - fake-fix BOTH members first (2026-10-11, agent cfa-fill0)

OFFLINE. Nothing installed, the game not started, no tool edited, nothing committed. The two kept archives under
`<work>/build/x_chunks/` were only READ: their sha1 is the same before and after my work (MEASURED `sha1sum`,
`s0_sources_before.txt` / `s15_sources_after.txt`: `retomoto_wardrobe/F01_Main.zip` ebbd0da2bd6468777c581ae6be6cd40dd55c2868,
`retomoto_wardrobe_compact/F01_Main.zip` 50dce65d41ba5b89c4c0685c7039321e53d7ea15). Every output named below lies in
`G:/kl_scratch/cfa_fill0/` (scripts `faketest.py` = the critic's, `pair.py`, `zipform.py`, `members.py`; outputs `s0 .. s16_*`).
Tools as they stood at 07:25 - 07:35: HEAD df80df4; `tools/kl_fa_bots_dyn.py` sha1 aa7f65f8 (unmodified), `tools/kl_chars.py`
sha1 8b420ec8 (another session's uncommitted 'plates' lines in it). Names: U = `x_chunks/retomoto_wardrobe`, C =
`x_chunks/retomoto_wardrobe_compact`, Uf / Cf = their `fake-fix` outputs.

**The gap (the critic's).** 3.3 step 2 proposed C 'as it lies' against U as 'a clean pair: whatever differs is compaction's'.
Both hold the two parked FakeTargets of the 0x686a66 crash, so a crash in that run could not be told from compaction's.

**What I measured.**

1. The fault is in both members, and by the game's own grid. MEASURED `python G:/kl_scratch/cfa_fill0/faketest.py <U> <C>`
   (`s1_faketest_src.txt`): each 3 FakeTargets, 2 outside - F07 escape vans 02 and 03 at (-3217, -60040, 3419) and
   (-1578, -60040, 1103), 'OUTSIDE by (0, 49901, 0) ... NO RECORD (index 0xff)'. MEASURED `python tools/kl_fa_bots_dyn.py
   fake-test <work>/build/z_route4/M01 <U> <C>` (`s3_faketest_rule.txt`): 'RESULT (fake-test): PASS (grid control 1, parked
   control 2, lattice 3)'; for van 02 on BOTH members 'kl2's arithmetic gives cell (14, 255, 10) on the all box (no record),
   (11, 255, 6) on the sure box (no record)'. MEASURED `python tools/kl_fa_bots_dyn.py grid <U | C> <the 96 hex digits of
   live run V2a>` (`s2_grid.txt`): 'all: the same six floats, bit for bit / RESULT (grid): the level's box is the game's' on
   both - the box these two archives give IS the grid the running game laid over a later Retomoto (the digits: READ
   re/crash_686a66.md section 'LIVE, 2026-10-11 07:00-07:06'; that the game lays the same grid for THESE archives is ASSUMED:
   the grid is read from the rooms' bound records, and MEASURED `faketest.py <work>/build/z_route4/retomoto_tab_fix`,
   `s18_faketest_tabfix.txt`: the build of that live run has the same 38 records of 17 rooms and the same two boxes as U
   and C). Van 02's place is to the float the
   place that live run saw written into record 0xff, (-3216.6, -60040.0, 3419.3) (READ the same section). So the critic's
   finding stands, and it is not only the tool's opinion.
2. `fake-fix` on BOTH. MEASURED `python tools/kl_fa_bots_dyn.py fake-fix <U> <work>/build/cfa/fill0/retomoto_wardrobe_ff`
   (`s6_fix_U.log`) and `... fake-fix <C> <work>/build/cfa/fill0/retomoto_wardrobe_compact_ff` (`s4_fix_C.log`; 13 s by the
   clock for C): both 'RESULT (fake-fix): PASS: 2 controller(s) off, nothing else changed'; the .prp member 4,940,306 -> 4,938,331 bytes in
   both (the same 1,975 bytes). Archives: Uf 212,120,333 bytes, sha1 9bcdd8620e5cf7402aad1b21f1f3e36d5eb0201a; Cf 211,563,177
   bytes, sha1 cc71c83b3ee4fc50bcf7b78c42ef14f09b65f3fc. The tool REPEATS: each command run a second time gave the same file
   (MEASURED `cmp` / `sha1sum`, `s5c_determinism.txt`, `s16_idempotent.txt`; READ tools/kl_graft.py 409-427: `write_zip` stamps
   a constant time; `KL_GRAFT_LOAD` was unset), and `fake-fix` of Uf takes '0 controller(s) off' and gives Uf again
   (`s16_idem_A2.log`). So whoever makes the pair for the live run can check it against the two sha1 above.
3. The fault is gone. MEASURED `faketest.py <Uf> <Cf>` (`s7_faketest_fixed.txt`): 1 FakeTarget each - van 01, the one that is
   called, at (-4879, -40, 6698), 'inside ... record' - and 0 outside.
4. Nothing else moved - checked WITHOUT the tool's own diff. MEASURED `python G:/kl_scratch/cfa_fill0/pair.py <U> <C> <Uf> <Cf>`
   (`s9_pair.txt`, 'RESULT (pair): PASS'): U - Uf and C - Cf differ in 1 of 30 members, the .prp; node by node 2 of 25,732
   nodes differ, nodes 25159 and 25382 = `.../F07_Escape_Vehicle_02/V_Van_00/Body/Body_Main` and the same of van 03, each
   lost exactly `FakeTarget` and kept `RelayAnimatedVehicleHit`, name, class, properties and the other controller token for
   token; controllers 4,896 -> 4,894, FakeTarget 3 -> 1; files beside the archive byte for byte except `graft.txt` (lines
   appended) and the new `dyn_fake.json` / `dyn_fake.txt`. MEASURED `python G:/kl_scratch/cfa_fill0/zipform.py` on both
   (`s5a_zipform_C.txt`, `s5a_zipform_U.txt`, 'RESULT (zipform): PASS'): the CONTAINER has the source's form for all 30
   members (deflate, flags 0, version 20, same names and order); only each member's time stamp (the build time -> the
   constant 2010-08-17 12:00) and the .prp's packed bytes differ.
5. It is still a pair, in the strict sense. MEASURED `pair.py`: U - C differ in 5 members (.prp, .gms, .MAT, .oct, .prm)
   and in 13,207 of 25,732 nodes; Uf - Cf in the same 5 members and the same 13,207 nodes; no node differs in name, class
   or controller names; chunk-table entries 65,119 (U, Uf) and 50,703 (C, Cf), .prm 77,773,040 and 76,988,864 bytes.
   MEASURED `python tools/kl_chars.py compact <Uf> <work>/build/cfa/fill0/retomoto_wardrobe_ff_compact` (`s12_compact_Uf.log`:
   'compact: 65119 -> 50703 chunk-table entries') then `python G:/kl_scratch/cfa_fill0/members.py cmp` against Cf
   (`s13_commute.txt`): 'content differs in 0 ... RESULT: PASS: every member byte for byte', 0 of 22 side files differ. So
   **Cf is exactly what today's compaction makes of Uf**: the two differ by compaction and by nothing else. Likewise
   `kl_chars.py compact <U>` today = C, every member byte for byte (`s14_recompact_vs_C.txt`): the archive of 2026-10-09 is
   what today's `tools/kl_chars.py` writes, so a load of it tests the code the prison and Havana would be compacted with.
6. The other offline checks hold on the fixed copies. MEASURED `python tools/kl_impact.py <U> <C> <Uf> <Cf>` (`s8_impact.txt`):
   'problems: 0 in 4 levels'. MEASURED `python tools/kl_chars.py check` and `invisible` on Uf and Cf (`s10_chars.txt`): 1
   problem each, the base's known `Weapons/BombWindow_02` shader line (READ re/prm_limit.md 'Checks run': U has the same
   line), and '108 people: 108 ok' on both. MEASURED `python tools/kl_maps.py preflight <Cf> F01` (`s11_preflight_Cf.txt`):
   CRASH 1 = 'verify' = the one problem `result.json` carries from the base (39 particle template names), RISK 5 (ZDummy,
   ZEnvSampler twice, Elevator, one CExplode value); that U gives the same lines is ASSUMED (preflight writes into the
   folder, so I did not run it on U; it reads the tree and result.json, of which only two controllers changed).
7. NO GUN LOOKS, no bots, no talk. MEASURED `pair.py`: beside each of the four archives lie `KLJoin.ini` and
   `KLWardrobe.ini` only, no `KLGuns.ini` (nor `KLTalk.ini`: MEASURED `ls`). READ tools/kl_chars.py 1710-1724 (the `compact`
   command): it rewrites `Root=` in KLWardrobe.ini and deletes chars.json, no other side file; MEASURED `diff` of the two
   KLWardrobe.ini (`s17_wardrobe_ini.diff`): the 16 `Root=` lines and nothing else (e.g. Kane 9236 -> 6134). READ klhook/klchar.c 201-225: the hook
   takes that file (Version=2, 16 characters, 8 masks). READ klhook/klgun.c 12-19: a KLGuns.ini whose `Entries` is not the
   loaded .prm's chunk count is refused; READ debug/slot.py 11-12 and `put`: a side file the build does not have is
   removed from the slot. So no gun file of another build can act on this pair, and the run settles compaction WITH the
   wardrobe (a hook-written model index into a renumbered table) but NOT gun looks on a compacted level - that stays a
   first for the prison (3.3 step 11 already puts compaction before the gun looks).

**What the fixed pair still is not** (so the run is not over-read).
- It is the Retomoto of 2026-10-09 21:20: no AI heisters (READ its result.json: 'DEGRADED bots'); the loot props, the van's
  leave leg and the stock police rows came later (READ CLAUDE.md 2026-10-09 23:50 and 2026-10-10 'Retomoto v2'). The last
  no-bots Retomoto that ran was under hook ship_bot1 (READ CLAUDE.md 'STATE 2026-10-10 16:20', TAB_DM09); that
  today's hook parts for bots, crew and talk stand still on a level without bot squads is ASSUMED - which is why the control
  member is run under the same hook and ini, not judged from the 2026-10-09 pictures.
- `fake-fix` on a Retomoto has run in the game once: `z_route4/retomoto_tab_fix`, 'record 0xff has never held no cell', four
  minutes clean (READ re/crash_686a66.md 'LIVE', runs V1 / V2b). THIS pair has not run; nothing here has.
- With the write gone a clean run means more than before, but compaction's own risk is a chunk index in a holder nobody
  rewrote (READ re/prm_limit.md 'What is missing to call it safe'): that shows as a wrong picture or a fault when the thing
  is first used, so the check is the PICTURES against the control, not only 'no crash'.
- No other fault of this base is known to me beyond the FakeTargets and the undrawn bomb material; I did not audit it.

**Corrected in place** ('corrected after the critic'): 3.1 row I and 3.3 step 2. Verdicts: none flips - the prison and
Havana stay 'feasible-with-work', and the live proof still decides them; what changes is that the test archive does NOT
'exist as it lies': it is made by two 13-second commands, and the run needs its control.

**A note for step 7's check** ('no unused van's target outside the rooms' bounds'). MEASURED `grep -c FakeTarget`:
tools/kl_maps.py 0, tools/kl_fa.py 0, tools/kl_graft.py 0, debug/check.py 0, tools/kl_fa_street.py 5 (READ 579-588: the
source fix, for Retomoto's parked vans only). So neither `kl_fa.check`, `kl_graft` verify nor `kl_maps.py preflight` sees
this fault; today only `tools/kl_fa_bots_dyn.py` does (`check` on a build with the dynamic step, `fake-test`, `fake-fix`).
For a new map before its bots: run `fake-fix` and read its RESULT line ('0 controller(s) off' = clean).

**Left on disk.** `<work>/build/cfa/fill0/`: six folders of notes (logs, .ini, result.json; 356 KB), NO archive and no sound
file (MEASURED `find -name "*.zip"`: 0). `fake-fix` refuses a folder that is there and not empty, so the pair for the live
run goes to NEW folders (the corrected step names them).

## Gap closed: the route without a run-time event - and what a plain 'Activate' really plays (2026-10-11, agent cfa-fill1)

The critic's gap: no build existed in which any round's route is open without a run-time event; the fall-back every
report leans on ('take the leaves out at build time') was never built; the primary way ('Activate') rested on one
uncontrolled sighting. OFFLINE; no file of `tools/`, `klhook/`, `debug/` or CLAUDE.md edited, nothing installed, the game
not started, nothing committed. Scripts and outputs `G:/kl_scratch/cfa_fill1/` (`<f>/` below); builds
`<work>/build/cfa/fill1/` (seven folders, notes and a 2 MB `walk_members.zip` each; every archive deleted).

**Results.**
1. **The fall-back is built four times and holds offline.** With the closures taken out at build time the whole route of
   every round is free in the BUILT collision file with nothing removed at flood time - bank 12 leaves, club 4 leaves +
   2 seals, prison 21 pieces + 1 path blocker, Havana 5 pieces + 1 shown. No build gained a problem (G1.1 - G1.6).
2. **NEW, and against the plan as written: a plain 'Activate' does NOT leave every door open.** A leaf plays the frames
   IT stores, and -1 / -1 is the whole clip (read in kl2.exe). Decoded from the levels' key data, the clips of the bank's
   two glass doors, of ALL the club's doors and of ALL five cage-door sets of the prison go THERE AND BACK: 'Activate'
   swings them open and shuts them again within 1 - 4 s. The campaign never plays them whole - its proxies and door
   controllers play to the open frame (50, 36, 30, 10) and back later. One number a leaf cures it (its own LAST frame =
   the open frame): built for the three places, verify unchanged (G1.8).
3. **The nine `MatPosAnim` flags are read**, in both exes; it is the same code. The three forms 'stock never has' are
   stock forms once the two flags that never act are left out; only two hidden cut-scene leaves of the prison stay
   without a stock twin, and the pre-pass drops them (G1.7).
4. **A second sighting exists, recorded, without a new run:** a picture of the owner's Retomoto round of 2026-10-09 18:19
   shows the lift's door leaves - Dead Men leaves of exactly the bank / club / prison form - standing open in Dog Days;
   the level file holds them shut. luvsic was NOT asked: this session has no way to reach him (G1.9).

### G1.1 How a closure is taken out at build time (MEASURED: `python <f>/build_open.py <place> <out>`)

`kl_maps.one(<out>, 'F07', <level>, keep=True, campaign=True, tag=' campaign open')` with three functions of
`tools/kl_escape.py` wrapped in the building process only. `kl_graft.build` calls all three itself for every Dead Men
map (READ tools/kl_graft.py 1178, 1401, 1407) - the code path of the Fragile Alliance bank's yard wall:
- `repair`: each closure node is sunk in WORLD y (the .prp's `ZGEOM[2]`), far enough to lie under the map's lowest floor.
- `place_entities`: the real one writes the new places into the .gms records (its `'move'` entry); the moved entities'
  REF ids are returned.
- `cut_collision`: the real one, on those REF ids.
Then the built archive is read back: each entity's world place, what the .HVK still holds under its REF id.

Two traps the first tries ran into, both MEASURED, for whoever writes this into a tool:
1. **A leaf's parent frame is not always the world's.** The bank's four glass leaves stand under a turned group: after a
   world move of 2,500 down their .prp y is 12. `open_wall`'s plain `y += dy` would move them sideways (it refuses such
   nodes: READ tools/kl_escape.py 120).
2. **The .prp and the .gms do not always hold the same local place.** Under a group with flag bit 0x40000000 the .prp
   gives the GROUP (0, 0, 0) and its children WORLD places, while the .gms keeps the group at its place and the children
   local (`python <f>/frames.py M05_A "DaughterRoomDoorB_01.D04$"`: group .gms (1500, 358, 3313) / .prp (0, 0, 0); leaf
   .gms (0, 0, -30) / .prp (1500, 358, 3283); 129 nodes of M05_A are so, every one under such a group; 23,681 are equal).
   The club's outer office door is one. `kl_fa_author.place` and `kl_escape.place_entities` write ONE number into both
   files; on such a node that is wrong in one of the two. `build_open.py` turns the move into each file's own frame and
   holds the two world places against each other before and after.

### G1.2 Bank (M03_A): free with twelve leaves out - MEASURED

`python <f>/build_open.py bank "<work>/build/cfa/fill1"` (35 s; log `<f>/build_bank.out`, `fill1.json` in the build folder):
- Built: ok, 19,675 entities, 28 rooms, chunk table 64,870 + 1, 0 dangling paths, `verify: problems: 11` - the same eleven
  as the plain trial graft (1 stream clip + the 10 findings of a level without a layer).
- Twelve nodes sunk by 2,500 (the vault floor is y -960): the dock roller door `M03_A_Garage_01a\SI0201_M03_BackDorAnim_01`;
  `GlassDoor_LEFT` / `GlassDoor_RIGHT` of `..._GlassDoor_01` and `_02` (their `GlassDoor_Frame` and `Neon_ON` STAY: the
  second agent's flood had taken those out too; they are not in the way); `SI0102_M03_BankVault_Door_PRE` (the body
  under the vault door's group); the airlock's `DDorSlide_01 .. _04`; the hall / foyer's `DDorSlide_01 / _02`.
- Collision: 'collision of 12 entities taken out of the .HVK (placements by shape type: {4: 12})'; key-framed placements
  308 -> 296, static 3,171 -> 3,171, .HVK 3,015,376 -> 3,005,232 bytes; read back from the archive: 0 placements left under
  the twelve REF ids, every entity 2,500 lower and nowhere else. **This settles bank 8.3's ASSUMED**: `cut_collision`
  takes a key-framed placement out as `kl_hvk.join` already does for an entity that leaves.
- The walk: `python G:/kl_scratch/cfa_bank/skeptic/walk8.py "<build>/walk_members.zip"` (the second agent's script,
  unchanged, on the BUILT .HVK; output `<f>/walk8_bank_open.txt`). Flood A, 'the file as it is', nothing removed at flood
  time: 166,892 states, floor y -959 .. 1261, **NOT reached: only 'statue (behind bars)'** - the other 45 of the 46
  stations, from the yard to both ends of the street, are reached. (In the plain build flood A reaches the yard's five
  stations and nothing else: READ `G:/kl_scratch/cfa_bank/skeptic/walk8_built.txt`.)
- Path blockers: none of the six door sets has one on a kept subtree (`python <f>/blockers.py M03_A`: 25, 4 kept). The
  four kept ones sit at the front entrance, the crew's only way out: boxes x 29..188 and x 403..566 at z -9421..-9292,
  state `eBlocking`, message `eUnblock` (`python <f>/front_blockers.py`) - on the two glass wings, the 2.0 m gap between
  them (x 200..400) is NOT covered. The Fragile Alliance bank has none of them (1 `PathBlocker` in the whole level).

### G1.3 Club (M05_A): free with four leaves and two seals out - MEASURED

`python <f>/build_open.py club "<work>/build/cfa/fill1"` (the one material string read as TILED, as both club agents built):
- Built: ok, 26,106 entities, 20 rooms, chunk table 52,934 + 1, 0 dangling, `verify: problems: 11` (the club's known ones).
- Six nodes sunk by 1,500: `D1`, `D2` (inner office door), `D04`, `D05` (outer), `Inside_Entrance_01a\HeroColi`,
  `Inside_Entrance_01a\Plane01`. 'placements by shape type: {4: 4, 1: 2}'; key-framed 159 -> 155, static 1,394 -> 1,394
  (the two seals became filler copies), .HVK 1,625,136 -> 1,623,712 bytes; read back: 0 left under the six REF ids.
- The walk: `python <f>/walk5_open.py "<build>/walk_members.zip"` (the second agent's walk5.py - stations, box, step rule -
  on the built .HVK; output `<f>/walk5_club_open.txt`). STRICT (nothing left out, also not the 98 entities that are
  hidden at load and own a placement): 42,233 cells, **round A's 14 stations office -> pavement ALL REACHED**; the same
  with walk5's 'hidden left out' rule. 42,233 is the cell count of walk5's scenario D (all six removed at flood time).
- No path blocker of the level stands at any of the six (`blockers.py M05_A`: 62 kept, all on the roofs' glass).

### G1.4 Prison (M08_A): free with 21 pieces out and one path blocker opened - MEASURED

`python <f>/build_open.py prison "<work>/build/cfa/fill1"`:
- Built: ok, 23,307 entities, 61 rooms, 0 dangling, `verify: problems: 12` = the known twelve (chunk table 79,005, 11 stream
  clips, the 10 layer findings).
- 21 nodes sunk by 2,500: `SI0301_M08_CageDor_B_01\DorAttachRoot01`; `D1 .. D4` of `CageDor_C_01` and `_C_02` in
  `GroundRoom_A` and in `GroundRoom_B` (16 leaves); and of each falling fence BOTH bodies - `FenceFall_Pre` (the standing
  piece) and `FenceFall` (its twin, hidden at load, whose key-framed body stands in the same plane). 'placements by shape
  type: {4: 21}'; key-framed 394 -> 373, static 3,177 -> 3,177, .HVK 4,262,928 -> 4,222,656 bytes; 0 left under the REF ids.
- **What the fall-back needs besides the leaves, in no report:** the pre-pass KEEPS
  `M08_A_Inside_MainArea\SI0301_M08_CageDor_B_01\PathBlocker_CageDoorB` (8302, 22, 12220), message `eToggle`, state
  `eBlocking` (`python <f>/blockers.py M08_A`: 46, 35 kept; the only one on the route). With the leaf gone and the
  blocker left, players walk through and the AI - seven heisters, every policeman - does not. The build writes it
  `eNotBlocking` (a stock value: 5 of F07's 6); read back `['eToggle', 'eNotBlocking']`. (The door group's relay sends its
  'Activate' to leaf AND blocker: anything that later 'Activates' that group toggles the blocker shut again.)
- The walk: `python <f>/hwalk_built.py build M08_A "<build>/walk_members.zip"`, `python <f>/prison_walk_open.py ...` = the
  critic's `prison_walk.py` (stations, search) with collision, REF ids, names and hidden flags read from the BUILT
  archive (output `<f>/prison_walk_open.txt`; the mesh polygons are the stock level's). STRICT (`gone` empty):
  **9 of 9 legs FREE, 0 closures in the way; START row -> van lane in one search FREE.** The same with 'hidden left out'.
- Why both fence bodies: on the STOCK level the strict search meets 13 blockers, the two extra ones being the hidden
  `FenceFall` twins (`python <f>/prison_strict_stock.py`). Whether a hidden key-framed body collides is not known (2.1
  item 9); with both cut the result does not hang on it.
- NOT in this build: the static entrance fence on the VAN's lane (`SO0106_M08_Entrance_Fence_01`); not on the walk.

### G1.5 Havana (M11_B): free with five static pieces out and the broken corner shown - MEASURED

`python <f>/build_open.py havana "<work>/build/cfa/fill1"`:
- Built: ok, 19,188 entities, 16 rooms, 0 dangling, `verify: problems: 12` = the known twelve (chunk table 74,454, 7 stream
  clips, the 10 layer findings).
- Five STATIC pieces sunk by 4,000: `...End_Corridor_01a\ColiObj_Obj_Roadblock_01` (the wing's invisible door block),
  `SI0100_M11_BarricadeB_01` and `M11B_OYCHECK_BEFORE01` (the bunker: the two the campaign's `GeomDeactivatorSandbags`
  names), `SO0201_M11_Corner_01`, `SO0201_M11_BarricadeXX_01`. `SO0201_M11_CornerBroken_01` loses the hidden state
  (`ZGEOM[3]` 1 -> 0, .gms flag 0x400 off). 'placements by shape type: {1: 5}': each static placement becomes a filler
  copy (the yard wall's own case), static 1,766 -> 1,766, .HVK 4,344,160 -> 4,337,120 bytes; 0 left under the five REF ids.
- The walk: `python <f>/hwalk_built.py build M11_B ...`, `python <f>/havana_walk_open.py ...` = the second agent's
  `walk3.py` places and legs on the built level (output `<f>/havana_walk_open.txt`). STRICT: **START -> table FREE 90 m,
  table -> van stop FREE 252 m, START -> van stop FREE 168 m** (walk3's own lengths for 'all five removals fired') and
  all 13 legs of the round station by station. The same with 'hidden left out'. No path blocker to open (all 15 dropped).

### G1.6 What the four builds do and do not show

- MEASURED, offline: route free in the built collision file; builds verify as the plain trial grafts; the method is the
  one that has played live for ONE static wall (READ bank 8.3: run H0_DM03). `python tools/kl_maps.py preflight` on the
  kept bank and prison 'open' builds: 'CRASH 2, RISK 10, NOTE 81' and 'CRASH 2, RISK 14, NOTE 66' - line for line the
  counts the second agents got for the plain builds; `python tools/kl_impact.py`: 0 problems (bank), 1 (prison: the chunk
  table, as before). Outputs `<f>/preflight_<place>_open.txt`, `impact_<place>_open.txt`.
- An entity with a `MatPosAnim` controller and NO body in the .HVK is the stock norm, not a new state: 2,758 of the
  3,314 `ZSTDOBJ` owners of such a controller in stock Dog Days have none (`python <f>/bodyless.py`). What IS new: the
  cut leaves keep their .gms flag word (0x..1f2), whose bits 0x7e mirror the collision flags of the entity's placement
  (92,273 of 92,370 stock entities with a placement; `python <f>/flagbits.py`). 'That word, no placement' occurs 9
  times in stock (six tables of L04, three models of L10) against 77,533 with one - and in every build of ours with the
  yard wall. What the game does with those bits without a body was not read.
- Limits of the walks are their authors': no character radius (bank, club) / 30 cm (prison, Havana), rigid props
  ignored. NOT shown: what a piece 15 - 40 m under the map does to its room's draw list (READ tools/kl_octree.py: a room
  tree lists an entity with its world box of the stock level; the wall precedent moved 2 m); bullets and sight where a
  door was (ASSUMED free: the ray test of a moving door must use the entity's present place).
- The price is the reports' own: the round stays, every door beat goes. A mixed build (one closure gated, the rest out)
  is possible and was not built.

### G1.7 The nine `MatPosAnim` flags, read in kl2.exe (and the same in kaneandlynch.exe)

How: `python <f>/mpa_exe.py dd ZMatPosAnim` (the class's property records: 16 level-file fields at record offsets
0x4c .. 0xd4; the code's `this` is 4 bytes earlier, so value 2 + i = flag Fi = byte `this + 0x90 + i`), then
`python <f>/mpa_code.py scan | dump ...` (vtable 0xba8f3c: constructor 0x8ff4b0, init = slot 13 0x7e95e0, update = slot
25 0x51a120, message handler = slot 26 0x5eacc0 -> 'Activate' 0x59dce0, evaluation 0x7b9590, sampler 0x422c50, set first
/ last frame 0x78f190 / 0x505550), message names by `python <f>/mpa_msgs.py`. All READ in the disassembly:

| value | byte | what the code does with it |
|---|---|---|
| 0 message | +0x50 | a 16-bit message id; the handler compares the incoming id with it and runs 0x59dce0: playing = 1, start time = now, controller ticking, 'MatPosAnimStart' sent to the owner. NO flag and no state is looked at: a second 'Activate' restarts the clip from its first frame |
| 2 F0 | +0x90 | read at the clip's end ('delete the owner', 0x51a1b4 -> 0x8a92a0) - but init writes 0 over it (0x7e98e9; Dead Men 0x54e21d) before any update. The level's value never acts. Stock stores it 1 on 3,505 of 3,968 |
| 3 F1 | +0x91 | at the clip's end: hide the owner (owner vtable +0x54; save / load pair it with the entity's 0x400 bit) |
| 4 F2 | +0x92 | read only under F0 (delete the parent if the owner is its only child): never acts |
| 5 F3 | +0x93 | 'RunOffScreen' (the message of that name writes this byte, 0x76dad0): if clear, engine events 0x802 / 0x803 (not identified) stop / restart a playing controller. Init forces it to 1 whenever F8 is clear |
| 6 F4 | +0x94 | the clip's movement is turned with the entity's placement (init keeps the first key's position; each evaluation takes it off, turns the rest by the base matrix, puts it back: 0x7b95e0) |
| 7 F5 | +0x95 | loop (animation object +8). Without it the sampler returns -1 at the last frame and the update ends the clip: stops ticking, playing = 0, 'MatPosAnimEnd' to the owner. Nothing moves the entity back |
| 8 F6 | +0x96 | at init the entity is put on the clip's start pose at once |
| 9 F7 | +0x97 | 'relative': init makes the base from the entity's own placement with the clip's start pose taken off (the block the 'ReloadRelativePos' message runs again): the clip starts where the entity stands |
| 10 F8 | +0x98 | start at load. If clear, init stops the controller and it waits for its message |
| 12 | +0xcc | rate (frames a second: 25 on every door here, 50 on the club's inner office door) |
| 13 / 14 first / last | +0xd0 / +0xd4 | 0 = left alone (the whole clip); else clamped into the clip: FIRST below the clip's first frame -> the first frame, LAST outside it -> the last frame. So -1 / -1 = the whole clip. LAST < FIRST plays backwards |

- Constructor defaults: F0, F5, F7, F8 = 1 (loop, relative, start at load), the rest 0.
- **Same code in Dead Men** (`python <f>/mpa_cmp.py`; vtable 0x95578c, init 0x54df10, update 0x54e9b0, handler 0x54e680):
  every access to the nine flag bytes, the frame fields and the message id is the same, in the same order. The
  differences are Dead Men's inline asserts on the owner pointer and one Dog Days addition (a byte +0xdc set by a
  'HoldFrame' message). A Dead Men leaf's values mean in Dog Days what they meant in Dead Men.
- **So the critic's 'forms stock never has' are stock forms.** Two controllers behave alike when (F1, F3-or-not-F8, F4,
  F5, F6, F7, F8) agree. By that key stock has 16 sets, not 28 (`python <f>/mpa_effective.py`), and:

  | door (raw flags, stored frames) | acts as | stock controllers that act so |
  |---|---|---|
  | bank roller door (000000010, 1 / 150) | F3 + F7 | 991; 71 of them with explicit frames |
  | bank rods (101010010, -1 / -1) | F3 + F4 + F7 | 244 (216 whole clip) |
  | glass, office and cage leaves (001100010, -1 / -1): 8 + 6 + 16 | F3 + F7 | 991 (918 whole clip) |
  | slide leaves, vault door, `DorAttachRoot`, `FenceFall` | F3 + F7 or F3 + F4 + F7 | 991 / 244 |
  | prison `Fence_Left_01 / Fence_Right_01` (111100011) | F1 + F3 + F7 + F8: starts at load, hidden at its end | **0** |

  The last two are hidden leaves of the exit cut scene `CutScenes/M08/M08_Exit.zip` at the vehicle gate (x 13,229); the
  campaign pre-pass drops that subtree (MEASURED `kl_maps.campaign_drop('M08_A')`). They reach no build.

### G1.8 What a plain 'Activate' PLAYS: half of the doors shut again (MEASURED `python <f>/keys_rot.py`, `keys_doors.py`)

A leaf's KEYS chunk gives the clip's frames (header: key count, first frame, last frame, step), its position keys
(three floats) and rotation keys (four int16 = a quaternion: ASSUMED from the identity value and from the angles coming
out as smooth swings), each with its key time. Decoded for every door of the three rounds, against the frames the
campaign's own objects play on it (`MatPosAnimProxy` values 1 / 2; a `DoorCtrl`'s middle number):

| door | the leaf stores | the clip | a plain 'Activate' | the campaign plays |
|---|---|---|---|---|
| bank: dock roller door | 1 / 150 | 0..149, one way: 90 degrees and 304 up | opens, stays | 1..150 (150..1 to shut) |
| bank: airlock 4 + hall / foyer 2 slide leaves | 0 / 30 | 0..30, one way: slides 98 | opens, stays | 1..30; `DoorCtrl` [1, 30, 0] |
| bank: vault door | 0 / 200 | 0..200, one way: 100 degrees at frame 60, rests at 95 | opens, stays | 1..75 |
| bank: six rods | -1 / -1 | 0..70, one way: 41 - 43 | pull back, stay | 1..60 |
| **bank: glass door 1 and 2 (4 leaves)** | -1 / -1 | 0..100: 135 degrees at frame 50, **0 again at 100** | **opens and SHUTS (4 s)** | 0..50 (door 1), 0..36 (door 2) |
| **club: four office leaves** | -1 / -1 | 0..100: slides 100 at frame 30, **0 again at 60** | **opens and SHUTS (2.4 s; inner door, rate 50: 1.2 s)** | `DoorCtrl` [1, 30, 0] / [0, 30, 0] |
| club: two fire doors; entrance leaves | -1 / -1 | 90 degrees at frame 10, back at 20; 360 / 130 at frame 50, back at 100 | there and back | `DoorCtrl` [0, 10, 0]; proxies 0..50 |
| **prison: cage door B** | 1 / 100 | 0..100: slides 180 at frame 50, **0 again at 100** | **opens and SHUTS (4 s)** | 1..50 |
| **prison: 16 leaves of the four C doors** | -1 / -1 | 0..100: 150 / 75 at frame 50, **0 again at 100** | **opens and SHUTS (4 s)** | 0..50, 1..50 |
| prison: fences (`FenceFall`, message 'FenceFall') | 0 / 97 | one way: falls to 68 degrees | falls, stays | the group's relay |
| Retomoto lift (the sighting of G1.9) | -1 / -1 | 0..160: slides 90 at frame 75 / 80, back at 160 | would open and shut | 0..75 (80..155 to shut) |

- The decode checks itself against the campaign: every `DoorCtrl`'s middle number is the frame at which that door's
  clip stands fully open (30, 30, 10), every opening proxy ends at or before it. A `MatPosAnimProxy` (handler 0x7ed520,
  READ) writes its two numbers into the leaf's FIRST / LAST and then calls 0x59dce0 - the very routine 'Activate' runs.
- So section 5 item 4 is half right and it matters: -1 / -1 DOES play the whole clip (READ, and the retail norm: 3,046
  of 3,968), and for a there-and-back clip the whole clip ends SHUT. 'A door group stays open without its `DoorCtrl`'
  is true only of one-way clips. As written, the club round's 'GO + 2 s: Activate to the door groups' opens the office
  for about two seconds; the bank's glass doors and the prison's five cage doors blink the same way; and cage door B's
  relay toggles its path blocker open while the leaf shuts again.
- **The cure is one value a leaf, no proxy kept:** its own stored LAST frame (value 14) = the open frame. Init applies a
  non-zero LAST (0x7e972e -> 0x505550) and 'Activate' never touches the frames. Built, three times:
  `python <f>/build_open.py bank_beats | club_beats | prison_beats <out>` -> glass leaves -1 / 50, office leaves -1 / 30,
  cage leaves -1 / 50 and 1 / 50; `verify: problems` 11 / 11 / 12 as before, values read back from the archives. The
  form 'first -1, last a frame' is stock (49 controllers; 806 store 0 / a frame: `<f>/frames_forms.txt`). Glass door 2:
  the campaign itself stops at frame 36 (109 degrees), not 50.
- Still true of every such door: a second 'Activate' restarts it from its first frame (it would snap shut and open
  again) - the sender must fire once.

### G1.9 A second sighting, recorded - and luvsic not asked

- **luvsic was not asked.** This session has no channel to him; the owner (JC on Discord) can pass on: 'In your campaign
  port, has any Dead Men door or gate MOVED inside Dog Days - opened by its `MatPosAnim` 'Activate' or by a
  `MatPosAnimProxy` - and did its collision go with it? Which level and door, and did a door ever open and shut again
  by itself?'
- **The project's own recordings hold one** (`python <f>/join_pics.py`: the pictures `tools/kl_watch.py` took within
  seconds of each of the nine logged Retomoto joins). `<work>/research/watch/20261009_180847/0078_622s.jpg`, taken
  18:19:11.555, 0.3 s before the hook logged 'join: player 0 entered box 9 at (2554, 19601, 812)': the owner stands in
  the lift lobby 2.4 m from the tower car, and its doorway is OPEN - the sill, the car's floor and its back wall with a
  hand rail are in view, no leaf across it (MEASURED: I looked at the picture; that the doorway is the tower car's is
  ASSUMED from the box and the time). In the level file the four leaves `SI0101_JPN_Elevator_DrExt_A_00 / _B_00`,
  `DrInt_A_00 / _B_00` span that doorway (key-framed boxes x 2793..2814, z 816..910 and 910..1004: `python <f>/closures.py
  M09_A ...`), and on a boot without a round they stop a player for 15 s (READ re/retomoto_fa.md 10.1, run J1). That
  build fired the campaign's `AnimProxy_OpenEscapeElevator` (frames 0..75) from its blast timer (READ re/retomoto_fa.md
  3.2 line 133; CLAUDE.md 'INSTALLED FOR THE OWNER 2026-10-09 18:10').
- What it is worth: those leaves are raw flags 001100010, 'Activate', rate 25, frames -1 / -1 (`python <f>/retomoto_lift.py`)
  - the very form of the bank's glass leaves, the club's six and the prison's sixteen; they were driven through 0x59dce0
  by a proxy with frames 0..75 of a there-and-back clip, and they stand open, not shut again: the stop at the given LAST
  frame is seen, as read. NOT in the picture: that their collision went with them (the join box lies in front of the
  car; nobody had to walk in).
- The other sighting, weighed again: the Fragile Alliance bank's roller doors get their 'Activate' from
  `Triggers!GarageDoors!TriggerBox`, whose two count fields are 5 (READ re/escape.md 4.2: ASSUMED a head count). The
  owner's 'once the garage door comes open' was a round with seven AI heisters; the 'solo scripted run in which the
  doors stayed shut' (RN10) was one player. That run never sent the doors their message: it is not a counter-sighting.

### G1.10 What changes in the plan (also marked in place, 'corrected after the critic')

- Marked in place: the club row of the table in section 1, 2.1 item 6, 3.1 row F, 3.3 step 3, 4.1 item 2 and its 'Open'
  line, 4.2 item 2 and its 'Open' line, 4.3 item 8, section 5 items 3, 4 and 6; in re/campaign_fa_bank.md 4.1, 8.3, 8.6
  (`python <f>/correct.py`: 12 + 3 notes).
- Door pattern F becomes: 'Activate' once, to a leaf whose stored frames end at its OPEN frame. Per place: bank - the
  four glass leaves get LAST 50 (36 on door 2 if the campaign's angle is wanted), nothing else; club - the four office
  leaves get LAST 30; prison - the 17 cage leaves get LAST 50, the fences take 'FenceFall' on their group.
- The fall-back is no longer an idea: `build_open.py`'s three wrapped functions are the recipe (with the two traps of
  G1.1 and the prison's path blocker). Any place's FIRST live run can be the bare boot of its 'campaign open' build:
  the whole route is walkable with no event at all, so a door that fails cannot hide what lies behind it.
- Live proof 2 (3.3 step 3) then tests the beats only, and has a sharper check (b): after 'Activate' the roller door
  stays up, the slide leaves stay open, and a glass leaf with LAST 50 stays at 135 degrees while one left at -1 / -1
  is shut again four seconds later.
- No verdict flips. The bank's second condition ('the two door sets on the way OUT open from the round start') is met by
  a build (airlock and hall / foyer leaves out, or simply 'Activate': their clips are one way).

Files: `<f>/build_open.py` (the seven builds; logs `build_<place>.out`), `closures.py`, `blockers.py`, `front_blockers.py`,
`frames.py`, `walk5_open.py`, `hwalk_built.py`, `prison_walk_open.py`, `prison_strict_stock.py`, `havana_walk_open.py`,
`bodyless.py`, `flagbits.py`, `mpa_exe.py`, `mpa_code.py`, `mpa_cmp.py`, `mpa_msgs.py`, `mpa_effective.py`, `proxy_code.py`,
`keys_doors.py`, `keys_rot.py`, `retomoto_lift.py`, `join_pics.py`, each with its `.txt` output beside it.

<!-- end of the cfa-fill1 section -->
