# DM01 Hot Coffee: smarter enemies - cover, hiding, flanking, several routes (RESEARCH + SPEC, 2026-10-25)

Status: research and spec only. Nothing built, nothing installed, nothing launched. Read-only on the game folder.
Base for the later build: the output of dm01fb_1025a (kick sound, wall extinguishers, AI door opening, cars from the road),
which sits on live DM01 zip c0e7b8ee. Do NOT build from c0e7b8ee directly or the two builds fork.
Scratch + evidence scripts: `C:/kl_build_1024/dm01ai_research_1025a/` (census.py/json, census2.py/json, filters.py/json,
sqdump.py + dm01_squads.txt, pos2.py, dpos.py, r2c.py, nav.py, props.py, dens.py, fl.py). Rerun them to re-prove any number.

Owner (2026-10-25): "the hot coffee how the enemies flow are almost perfect, they need a bit more pathways and smarter to hide and get
into cover n stuff theyre almost perfect maybe take notes from the campaign in dog days on the harder difficulties?"

## 0. Result in six lines
1. The campaign's "smart" AI is NOT a difficulty table. It is structure: RunToCover (45-141 routs per level) + RandomTrigger branches +
   DefendPlayerPos + many cover boxes. Level-side difficulty switching exists in only 4 levels (L01/L02/L03/L08) and only changes
   health modifiers (L08: 30/40/50 %) and which gates/vans exist. Everything else "harder" is the runtime Difficulty option (row scale).
2. DM01 has the opposite shape: 0 RunToCover, 0 DefendPlayerPos, 0 RandomTrigger on the enemy side, 156 cover boxes, and
   the three OldWaves squads are a bare Defend rout (no modifier, no Hunt, no Flank, no event lists).
3. Cover is missing exactly where the enemies stand: of 54 enemy Defend posts, 15 (28 %) have NO cover box within 5 m and 25 (46 %) have at most 1.
   The campaign (L07) has 0 of 57 with none. The shop room (x1900-3900, z21900-23600) holds 0-3 boxes per 10 m cell.
4. The nav mesh has exactly TWO approach lanes into the heister corridor and one hard choke (section 3). "More pathways" = use the east loop
   and the west alley that the mesh already has; do not touch the mesh.
5. Build = 14 new cover boxes on real props (section 4), RunToCover entries + a RandomTrigger on 5 squads (section 5), 4 squad-modifier
   fields (section 6). Net cost: 0 actors, +2 squads, about 60 new ZSTDOBJ points (budget section 8).
6. Proven vs guessed: section 9. The two biggest guesses: what a Flank's two points do, and how far RunToCover searches by itself.

## 1. How the Dog Days campaign AI takes cover, hides, flanks (evidence)

### 1.1 Cover data (census over F01-F09, L01-L11, DM01; census.json/census2.json)
- Cover boxes are entities named `*CoverBox{H,M,L,car}*` (ZSTDOBJ, hidden one-mesh model). `CFFCoverList` (slot 13, 0x6d6a80) builds the
  cover list ONCE at load from them; 0x603830 turns each box into four sides. The AI uses the same list as the player (re/bots_dynamic.md 3.1).
- Counts (real boxes, from `kl_fa_cover.all_boxes`): DM01 156 (88 low, 68 high; 12 of them `_KM_` car copies). Stock FA: F01 308, F04 416, F07 380.
  Campaign: L02 725, L05 453, L07 758, L10 796. Boxes per enemy defend post within 5 m (median): stock 2-4, campaign 3, DM01 2.
- Player-side cover helpers: `PlayerCoverModifier` 50-349 per stock/campaign level, DM01 0 (not read to the end; player-facing, NOT in this spec).
  `CoverStateChanger` 8-529 per level, DM01 14. `NoCoverBox` markers: L02 1, L08 8, L11 2, DM01 1.
- Soldier tactics (0x6ab250): AttackFromCover, DefendCover (picks a cover within 500 of the defend position, 0x84dc90), AttackNoCover,
  CloseIn, EvadeDangerPoint. So a Defend Pos with no box within 5 m falls back to AttackNoCover = standing in the open = what the owner sees.

### 1.2 Rout classes and fields (schema: kl_prpjoin.schema('dd'))
| class | fields | what it does | campaign use / DM01 use |
|---|---|---|---|
| ZRunToCoverBehaviourRout | 0 refs (next list, usually empty or a RandomTrigger), 1 b, 2 b | run each named actor to ITS point, then fire the next list | campaign 45-141 per level (L07 141), stock FA 3-35, DM01 0 |
| ZRunToCoverPosInfoRout (child ZSTDOBJ, one per actor) | 0 b, 1 b, 2 b, 3 ERunToCoverMoveSet (Run/Sprint/SneakRun), 4 EPreferredCoverUsage, 5 s = the actor group path | the point the actor runs to | the point sits a median 105 (L07) / 114 (F04) / 163 (L02) / 179 (L05) from the nearest cover box, p10 61-111, p90 156-305 (r2c.py) |
| ZDefendBehaviourRout | 0 s, 1 refs Pos#nn, 2 b, 3 b, 4 EDefendMoveSet, 5 EDestinationFormation, 6 s, 7 refs (fires on arrival), 8 b, 9 b | hold posts | DM01 235, the only enemy rout besides Hunt/Flank |
| ZDefendPlayerPosBehaviourRout | 0 refs, 1 b, 2 b | go to the nearest player's position (the push) | campaign 11-65 per level, DM01 0 |
| ZFlankingBehaviourRout | 0 s LeftFlank#1, 1 s RightFlank#1, 2 refs, 3 b, 4 b | two child points; the squad splits to them | campaign L07 10, L08 17; DM01 9 (all fixed world points) |
| ZHuntBehaviourRout | 0 s SearchBox, 1 b, 2 refs, 3 b, 4 b | search a box (field 1 = 1 on CornerShop) | DM01 5; boxes 4600x4700 centred (4207-4399, 21916-21980) = the shop/lot, NOT toward the heisters |
| ZRandomTrigger | 3-4 outcome lists | picks one list | stock FA 22-70 per level, campaign up to 11, DM01 47 (all in the heister bot squads, none on the enemy side) |
| ZSquadModifierBehaviour | 29 fields, see 6 | squad knobs | DM01 45 modifiers, 20 loose / 22 tight, 7 vision x2 |

### 1.3 The campaign's cover-and-flank idiom (L07 Randomspawn, and F07/F04 bot squads)
`RunToCover (per actor point behind a box)` -> `RandomTrigger (3-5 outcomes)` -> one of several `Flank` or `Defend` routs with different points ->
`SquadModifier Unleash (eLM_Unleash, vision x2.0)` -> `DefendPlayerPos`. Two things carry the effect: the random branch (a fight differs each
round) and that every actor hits cover first. DM01's own heister squads (Squad#02..08) already use the shape `way_a/way_b/way_c` +
`pos_cover` + 8 s hold (`TriggerDelay2` 8.0) + `eDM_Tight` while looting; it runs in the game today. Enemies have none of it.

### 1.4 Difficulty (what it really is)
- Runtime option `Difficulty` ([0x156b5f0]): NPC health rows x0.5 / 0.9 / 1.15 / 1.3, plus spread and hit-reaction rows (0x831f00). Same level data.
- Level data: `Filter` (EFilterMode Easy/Medium/Hard/Extreme) exists in L01 49, L02 23, L03 38, L08 7 and gates squad modifiers, gates, vans only.
  L08 `Sq_Crane`: `SM_EasyNorm / SM_Hard / SM_Extreme` differ ONLY in the health modifier 30 / 40 / 50 %. No filter changes cover use, aggression or routs.
- Squad-modifier fields set in the campaign (counts across L01-L11): 15 UseCovers explicitly: `eCOM_DontUseCovers` 87 (e.g. L09 39), `eCOM_UseCovers` 23;
  14 vision factor: 4.0/3.0/1.5/1.0/0.5/0.1; 19 blind fire: `DisableBlindfire` 25, `70Pct` 1; 9 defend distance Tight/Loose/Normal.
  So "harder" cannot be copied from a table: copy the STRUCTURE (sections 4-5) and leave health/accuracy as DM01 already has them (accuracy 75 as
  used, hp 100-175, `kl_map_ai table`; same band as stock FA 55-82 / 100-175).

## 2. DM01 today (live c0e7b8ee: 68 actors, 31 squads, 156 cover boxes, nav 393 polygons)
Enemy squads: CheckFront, KitchenBoy, CornerShop, FrontMall_01/02 (Bentley men), TheBoss + BossFlank_01..03 (warehouse), OldWaves Wave_1/2/3 (9 each),
KL_Hold!Shop (4), KL_WH!Floor (8) + Top (4), KL_Cars Cop_1..3 (street, DontUseCovers by design).
- Waves are bare `10_Defend` on 5 Pos each (no Hunt/Flank/modifier). They wait; they do not walk to the heisters.
- Flank points (fl.py) are fixed world points near cover (28-228 to a box): Bentleys (6302,23465)/(5978,23067), (6843,23764)/(7112,23427),
  (5924,22340)/(6531,22808), (5052,22608)/(5542,22524); warehouse (1925,18682)/(1635,19363) etc. None of them lies north of z26000.
- Weak posts (enemy Defend Pos with <=1 box within 5 m; `x,y,z`, distance to the nearest box):
  | squad | posts |
  |---|---|
  | KL_Hold!Shop | #01 (3130,-10,22750) 752 | #02 (3130,-10,22390) 796 | #04 (2830,-10,22150) 600 |
  | OldWaves!Wave_1 | #05 (2890,0,22450) 906 | #06 (3070,-10,22210) 729 | #07 (2650,21,22150) 595 | #08 (1810,0,22570) 683 | #09 (1810,0,22930) 1041 |
  | OldWaves!Wave_2 | #04 (6310,0,21190) 741 (others 2-3 boxes) |
  | CheckFront | #02 (6463,6,25648) 594 | #03 (3742,-8,25739) 474 (n=1) |
  | KitchenBoy | #04 (6508,-6,24753) 634 | #05 (5515,-5,24746) 732 | #06 (4888,-7,24478) 518 |
  | CornerShop | #01 (3276,-3,22775) 663 |
  | KL_WH!Top | #01-#04 scaffold y860, 349-518 (n 0-1) |
  Well covered already: Wave_3 and KL_WH!Floor (warehouse hall: 37 boxes in x1000-2999, z17000-19999), FrontMall/Bentleys.
- Cover density (boxes per 10x10 m cell, dens.py): shop x2-3,z22-23: 0-3; mid mall z24-25: 1-6; corridor z26-31: 0-2 (nothing north of z27999).

## 3. Nav mesh: alternative routes (nav.py, kl_fa_bots.Nav; lengths in game units, 100 = 1 m)
Single-polygon bans along each shortest route show where the mesh offers a second way. Start points: W1 (3130,-10,22750), W2 (5350,0,21550),
W3 (2170,60,19030), Bentleys (6400,0,23950), heisters (1632,76,30643), van (6153,0,20659).
- ALL routes to the heisters pass two chokes: polygons at (1384,0,27006) and (1518,0,27699) (the north corridor). No alternative exists there.
  So the heister START is protected from every side; fights happen south of z26500.
- Two real approach lanes into that corridor (everything else merges into one of them):
  - CENTRE (shortest): shop east exit (4323,22484) -> (5111,23296) -> (3710,24095) -> (3102,24703) -> (2312,25246) -> (2345,27082). From Bentleys 9402.
  - EAST LOOP (+14 % from the Bentleys, +25 % over the bypassed hub): (5756,24754) -> (6793,25190) -> (6139,26263) -> (4368,26662) -> (3414,27533) -> (2345,27082)
    -> (1518,27699). A real, wide detour: nothing on the current enemy squads uses it.
- WEST ALLEY (hall -> shop west, joins the centre at the shop east exit): hall door (2343,19875) -> (1891,20193) -> (1614,21530) -> (1532,22524) -> (2339,22083)
  -> (3309,22489) -> (4323,22484). From W3: 18342 vs 16756 (+9 %). From W1 via the warehouse side (2479,21020) -> (3529,21136): +34 %.
  Wave_1 posts #08/#09 at x1810 already stand at its door.
- LOT lane (W2): (4788,20818) -> (4368,20959) -> (4110,21723) -> (4826,22350) -> (6082,22884) -> front mall -> centre. Chokes (5137,21577), (4881,21549), (4788,20818)
  for W2 only. W2 -> van 2020 (one poly choke at (5710,20156)).
- Conclusion: three approach "faces" for the south half (warehouse west alley / shop / lot) feeding TWO lanes (centre / east loop) into one choke.
  Splitting waves over these = the owner's "more pathways".

## 4. Cover to add (14 boxes, on REAL props that have no box; GUESS: the prop is solid enough to stand behind)
Found with props.py: ZSTDOBJ props named like cover, with no `!CoverBox*` child and no box within 150. Positions are the prop origin.
Method: `kl_cover_add` machinery (clone one form-b box of the build: flags 0x200, hidden one-mesh model, in no room tree; `kl_fa_cover.fit` picks the model that
fits the prop; `apply` renumbers SLOT ids and keeps the four blocks' sizes). Name them `CoverBox{M|H}_AI_nn` in a new group `KL_CoverAI!`. Not in a room tree.
| area | prop (origin x,y,z) | feeds | kind |
|---|---|---|---|
| shop room | PC0801_M01_ShopDesk_4m_01 (2950,0,22886) | Hold Pos#01 (226 away), Wave_1 | H |
| shop room | SI0107_M01_Pillar_05 (3100,0,21900), _04 (2700,0,21900) | Hold Pos#04, Wave_1 #06/#07 | H, H |
| shop room | SI0107_M01_Pillar_01 (3100,0,23100), _03 (2700,0,23100) | Hold Pos#01/#02 (north side) | H, H |
| shop room | PC0801_M01_Pallet_02 (3317,10,22150), Pallet_01 (3319,-10,22053) | Hold Pos#02 / Wave_1 #05 | M, M |
| lot | PC0300_USA_BoxBrown_E_03 (5563,1,21838) | Wave_2 #01/#02/#05 | M |
| lot | PC0300_USA_Box_B_02 (5263,0,21854), _03 (5174,0,21808) | Wave_2 #02/#03/#05 | M, M |
| mall north | SO1001_FlowerBoxShatter_NonShatter_07 (5400,-10,25425), _08 (5000,-10,25425) | CheckFront #05, KitchenBoy #05/#06 | M, M |
| mall north | FlowerBox _04 (5400,-10,25589), _05 (5800,-10,25589) | CheckFront #02, KitchenBoy #04 | M, M |
Count: shop 7 (desk 1, pillars 4, pallets 2), lot 3, mall north 4 = 14. If `kl_cover_vet` flags the pallets (a pallet is probably low: M only), drop them (12).
No candidate exists on the corridor (z26000-31000), the west alley or the mid mall: those are narrow
lanes with bare walls; leave them (the AI fights there in the open, which is also how the stock FA corridors play).
Rules for the builder: (a) run `kl_cover_vet scan` afterwards - the player must be able to stand at every side (owner 10-24: stuck inside an object);
(b) `kl_cover_add plan` still lists "12 static car copies" for the live zip although 12 `CoverBoxM_KM` boxes already exist: check by name/pose before
reusing it so the copies are not doubled; (c) keep the single NoCoverBox honoured; (d) keep new boxes >= 150 apart (APART) and out of the exit boxes and the van road.
Also move the weak posts that have a new box within 400 to 100-150 beside that box (never inside the nav clearance, `Nav.clearance` >= CLEAR): Wave_2 #04 (6310,0,21190) has no prop within 800, leave it; KitchenBoy #06 (4888,-7,24478) is on the centre lane, accept open ground there.

## 5. Routs to switch / add (all use proven classes; see 9 for the guess list)
Rule set for every change: new behaviours are CLONED from the build's own routs (kl_old_waves.make_waves / kl_fa_author clone path, as `KL_Hold!Shop` was cloned)
so the schemas stay exact; SLOT ids renumbered by the existing tools; every Pos / RunToPosInfo point must lie on the nav mesh (`Nav.at`) with `Nav.clearance` >= CLEAR.

### 5.1 OldWaves!Wave_1 (5 men after the KL_Hold split; shop room)
Today: Go -> `10_Defend` (5 posts). Change: Go -> `10_RunToCover` (RunToPosInfo for each man at his post moved to the box side: Pillar_05/04 outside, ShopDesk, Pallet_02)
-> next list = `RandomTrigger` of 2: (a) the existing `10_Defend` (hold, 8 s `TriggerDelay2`, then (b)'s fallback) / (b) NEW `20_Flank_centre` Left (4323,0,22484) Right (5111,0,23296)
(the centre lane, 190 and 270 from the shop exit). Add `SquadModifier` (field 9 `eDM_Loose` so they leave posts, field 14 `eVIM_Factor_2_0` as DM01 uses on 7 squads).
Result (intended): half the rounds the shop men hold, half come out the east door and take the centre lane.

### 5.2 OldWaves!Wave_2 (lot, 9 men) - split lanes
Add one squad `KL_East` and MOVE 4 of the 9 existing actors into it (clone the squad group as `KL_Hold!Shop` was; 0 new actors). `KL_East`: `10_RunToCover` at the lot boxes
(Box_B_02/_03, BoxBrown_E_03) -> `20_Defend_way_east` posts on the EAST LOOP (6793,0,25190) then (6139,0,26263) (8 s hold between, as the bot `way_a/_b`), final `Defend`
at (4368,0,26662). Wave_2's other 5 stay on `10_Defend`. The loop is +14 % over the centre from the Bentleys and enters the corridor from the side: the flank the owner wants.
Gate: same Go as Wave_2 (60 s after start in the chain), so no timing changes.

### 5.3 OldWaves!Wave_3 (warehouse hall, f3=0, released by the clock) - west alley split
Today one `10_Defend`. Add `KL_West` with 4 men: `RunToCover` -> chain through (1891,0,20193) -> (1614,0,21530) -> (1532,0,22524) (west alley), ends at the shop's west door
(Wave_1 #08/#09 area, x1810): they pop out behind a heister fighting in the shop. The remaining 5 stay in the hall (counter-attack through the hall door as now).
+1 squad. If Wave_3 is later used for the Hunt change, keep `KL_West` out of it.

### 5.4 CheckFront + KitchenBoy + CornerShop (the 3 mall squads)
They have `Defend` + `Hunt` + `Flank`. Change: (a) move the three Hunt SearchBoxes (identical box, 4600x4700, centre (4207-4399,21916-21980)) so the centre is the
centre-lane midpoint (3800,0,26000) for CheckFront and KitchenBoy (covers x1500-6100, z23650-28350: mall north, corridor mouth); CornerShop keeps the old box. The old box holds the
shop and the lot where Wave_1/2 already are. (b) CheckFront Flank points -> (6139,0,26263) / (3703,0,25010) (east loop and centre). (c) Add `RandomTrigger` in the alarm chain
(MercsClosingIn already starts both Flanks) choosing between the old Flank and the new one. These three only start when the alarm fires; nothing at round start changes.

### 5.5 FrontMall_01 / FrontMall_02 (Bentley men, f3=0, vehicle exit)
After `VehicleExitBehaviour` the current chain is Flank (own points) then Hunt. Insert `RunToCover` after the exit with PosInfo at the cover boxes next to the
cars (CoverBoxM/H at x6700-6900, z23800-24200: 5 H + 4 M already stand there), then `RandomTrigger` -> old Flank / east-loop Flank. Costs nothing but PosInfo points
(4 per squad, SneakRun).

### 5.6 The push - DefendPlayerPos
Final rout for ONE wave only (Wave_1's remainder after 5.1 b): `DefendPlayerPosBehaviourRout` (field 0 = next list, empty). It sends the men to the nearest heister at that moment (GUESS
for the exact search: see 9). Use it only after the squad has been alive 60 s (a `TriggerDelay2` 60.0 behind the Flank) so the early game does not collapse onto the start. In the campaign
the same step follows `Unleash`.

Squad total: +2 (KL_East, KL_West). Rout nodes: about 14 new routs + 6 `RandomTrigger` + 4 `TriggerDelay2`. Points: 3 squads x 5 RunToPosInfo + 2 x 4 + Pos/Flank ~ 40 ZSTDOBJ.

## 6. Actor / squad settings to copy (SquadModifierBehaviour field numbers, kl_prpjoin.schema('dd'))
No difficulty row to copy (1.4). Copy what the campaign/stock FA set on enemy squads:
| field | name | value to set on the squads of 5.x | evidence |
|---|---|---|---|
| 9 | defend distance | `eDM_Tight` for the holders (KL_Hold!Shop, hall Floor/Top), `eDM_Loose` for the movers (Wave_1 rest, KL_East, KL_West) | stock FA F04 30 Tight / 7 Loose; the heister bots use both |
| 14 | vision factor | `eVIM_Factor_2_0` on movers (DM01 has it on 7 already), `Factor_3_0` on KL_East (flank sees across the lot) | campaign L04 3.0 x2, L11 3.0 x2 |
| 15 | cover use | `eCOM_UseCovers` explicitly on every squad that has RunToCover (default NotSet; the stock FA sets it on 1-3 squads per map) | F02 2, F03 3, L04 7, L11 10 |
| 19 | blind fire | leave NotSet (campaign sets `DisableBlindfire` on 25 squads = the default allows blind fire) | L01 9, L10 4, L11 10 |
| 0 | leash | `eLM_Unleash` once the squad starts to move (as the L07 Randomspawn) | L07 |
Do NOT touch: soldier rows (accuracy 75 as used, hp 100-175: already in the stock band; the owner said "almost perfect"), `ZSoldierRout` skill names (they
overwrite accuracy, kl2 0x46e410), the number of actors above 80.

## 7. What NOT to do
- No nav mesh edit (PF4): the mesh already has the east loop and west alley.
- No new enemies for the sake of it: the build is done within 68 + 0 actors.
- No `PatrolBehaviourRout`: used 2-7 times in the campaign, untested here, adds nothing the Defend chains do not.
- No hard-difficulty `Filter` copy: the filter only exists in 4 levels and changes health; Dog Days' runtime Difficulty already scales rows.
- Do not give the heister-side bot squads any of this: they already run the way_a/b/c + pos_cover idiom.

## 8. Budget and order
- Actors 68 (limit about 99): +0. Squads 31 (about 55): +2 = 33. Entities 16514: +14 boxes +~40 points +~25 routs/triggers.
- Order: dm01fb first (kick sound, extinguishers, door opening, cars) -> this (cover -> routs -> modifiers) -> doors2 stays as installed. Within this build: cover boxes FIRST
  (the posts move to them), then points, then routs. Run after each: `kl_cover_vet scan`, `kl_old_waves check` (the "FAIL parked=False" on waves 1/2 is the known f3=1 override of kl_spawns_1024.ACTIVE, not a regression),
  `verify_levels`/`debug/check.py`, then `kl_autotest.py` into F01 only after the owner says the other builds are done. Log every change in re/open_work_log.md.
- Rollback: one new group `KL_CoverAI!`, two new squad groups, the cloned routs; the changed Hunt boxes and Flank points are recorded by node and old position in `ai_cover.json` next to the build.

## 9. Proven vs guessed
PROVEN (read from the exes or the level files, offline):
- Class/field schemas of the routs in 1.2 (kl_prpjoin, kl2.json); the cover builder (0x6d6a80/0x603830) and DefendCover radius 500 (0x84dc90).
- Counts: RunToCover/PosInfo, DefendPlayerPos, RandomTrigger, Flank, Hunt, modifier fields, cover boxes per level (census.json); DM01 has 0 RunToCover and 0 DefendPlayerPos.
- Campaign RunToPosInfo points are ZSTDOBJ markers placed a median 105-179 from the nearest cover box (r2c.py: F04, L07, L02, L05).
- DM01 enemy posts: 15 of 54 with no box within 5 m (dpos.py); the weak-post list and coordinates above.
- Difficulty: level data changes only health modifiers (L08 30/40/50 %) and gates in 4 levels; the Difficulty option scales NPC rows (0x831f00).
- The nav lanes, the two chokes and the detour lengths (nav.py on the live zip's mesh).
- The F07/F04 bot idiom (RunToCover -> RandomTrigger -> Defend chain, 8 s holds) runs in stock; Retomoto's police waves use RunToCover (re/retomoto_ai.md).
GUESSED (each needs the first live run):
- That a ZFlankingBehaviourRout's two child points are waypoints the squad walks to (placement in DM01/campaign suggests it; no code read).
- How far `DefendPlayerPos` searches and whether it works when the nearest player is behind a choke (the campaign uses it; DM01 never has).
- That a Hunt SearchBox is the area a squad patrols after a call (DM01's boxes cover the shop/lot, which fits; the CheckFront box has a parent-frame offset I did not resolve).
- That the props in 4 are solid enough for a hide (pillars, desk, pallets, flower boxes): sizes not measured here; `kl_cover_vet` and a look in the game decide.
- Vision/UseCovers/Unleash values for the new squads: taken from similar campaign squads, not tuned.
- Whether 14 new boxes (+9 %) change fights enough; the owner's "almost perfect" is the reason to keep the change small.
OPEN: the three squads' real alarm behaviour (which Flank wins when two chains name it); whether the east loop is wide enough for 4 men in a line (nav polygons are 5-12 m; looks fine, not walked).

## 10. Next step for the builder
1. Wait for dm01fb to finish and read its output md5. 2. Build `tools/kl_dm01ai_1025.py` (new) on that zip: cover (4), points + routs (5), modifiers (6).
3. `check`, `diff`, `kl_cover_vet`; hand to the autotest only after the owner clears the queue. Do not install in this task.
