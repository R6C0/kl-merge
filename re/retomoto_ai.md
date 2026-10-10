# Retomoto Tower: dynamic AI, the elevator-triggered street, the van (owner, 2026-10-09 late)

Status 2026-10-10 00:xx: section 0 = the owner's words, section 1 = facts the lead measured for this job
(offline, on the files; every number read, GUESS / ASSUMPTION marked), sections 2+ are filled by the
design workflow and the implementers. NOTHING here has run in the game. kl2.exe was running (the
owner playing) while this was written: no live run, no install, no change in the game folder.

## 0. The owner's asks (verbatim meaning)

1. Tower: "when you spawn in you see them run away and they hide for cover, then guys with pistols
   will rush you, then the higher the caliber the more advanced / technical they play so it actually
   takes some thinking".
2. Heat street: "they spawn in once you go down the elevator so that triggers them and they are all
   like outside ish but they retreat to some of their spots to hold you off and the more you shoot
   the more they run away but the closer you get to the vehicle the more they try to shoot it so it
   could blow up".
3. Van: "make sure the car doesn't clip and maybe remove some props so you can see the van actually
   leave like a normal car since currently its trajectory is pretty silly and clips in the floor".
4. "maybe use swat vans for some of the police spawning".
5. Use re/retomoto_design_plan.md as the continuation (read it; its 2a / 2c sketches).

## 1. Facts for the design (lead, 2026-10-10; read from the files unless marked)

### 1.1 What the owner played (installed build = kl_fa_street layer, `kl_fa_street.py report` on the slot)
- Street police start at the FRONT DOOR box (`Gameplay!030_AfterLoot!tbExitFinancialAlley`, x 2592..3207,
  z -7302..-5697, MERCONLY): 5 campaign police on the forecourt + 8 who come up the road from the
  south (z -13000..-14200). Then wave 1 at the first step on the road (F07 squads, 10 men, cover in
  the traffic z -3300..-200), wave 2 at z -3600..-3000 (first road block z 3602..3911, 13 + dog +
  4 campaign), wave 3 at z 1700..2300 (3 men at the SWAT truck north (-3588, 10886)), 'run' boxes at
  z 6200..6800 -> 44 s + 18 s -> every F07 squad walks to a ring round the van (RING offsets).
- The owner SAW police "spawn in": squads with ZSquadScript field 3 = 0 have no actors in the world
  until a rout of theirs is named (ASSUMPTION borne out by that observation and by F01's
  tbPlatform#01_MercOnly -> SwatExit#01\11_RunToCover idiom). F07's 14 squads all have field 3 = 0.
- One van (F07 van 01), waits (-4866, -40, 6688), stop (-1567, 9300), exit box z 6800..11300.

### 1.2 The van "clips in the floor": WHY (measured with kl_escape.Walk on the .HVK)
- Road collision surface along x = -1000: y 20.0 for z 3000..16000 (one cell 46 at z 13500). Along
  x = -3000 also 20 (static cars rise to 120 / 222). Along x = -1300 a patch z 6000..10000 at y 0.
  Static cars' origins stand at y 2..5, campaign actors at y 3..14, the player (hook position) at
  -47..-40 = the hook's y is ~70 below the floor (same offset on the square: hook -50, actors 26).
- F07: the van's baked local y is -198 and F07's road under it is -200 (Walk): the van's ORIGIN IS AT
  GROUND LEVEL (+2). kl_fa_author lays it at ROAD_Y = -40 -> 40..60 below Retomoto's road. FIX: van
  y = floor + 2 = about 22 at x -1000 (read the floor from the .HVK at the stop, do not hard-code).
- The drive's silly trajectory: F07 van 01's drive is L-shaped (90 degrees) and van_fit turns it
  37 degrees across the road: waits west lane (-4866, 6688), crosses to the east lane (-1560, 9305),
  swerves back west to (-4777, 13574). Van 02 is S-shaped, van 03 bends 51 degrees. None is straight.
- Baked drive format (van 01, `V_Van_00` KEYS chunk, 796 frames; `kl_graft.keys_tracks`): six .buf
  offsets; track 5 = positions, 564 keys x 3 floats (local coordinates; keys 0..390 = the main drive
  wait -> stop -> away, 391..563 = the four crash pieces); track 2 = ROTATIONS, 550 keys x 4 x int16
  = quaternion (x, y, z, w) / 32767 - CONFIRMED: the heading of local +Z from these keys follows the
  drive's tangent (keys only about Y; x, z components ~0). Tracks 0 / 3 (1008 bytes) are frame ->
  key index tables (10 bits per frame; the first byte is 0x0a, exact packing NOT decoded, not
  monotone with any simple skip), tracks 1 / 4 (688 / 704 bytes) unknown. The KEYS chunk is in the
  entity's raw block (`S.ents[k-1].raw`, offsets at +0x18..+0x2c of the chunk), the tables in the
  .buf HEAD (`S.scene.head`; `kl_scene.Scene.write()` writes head + names + tail; kl_graft.build
  reads S.scene (A) for the .gms/.buf, so edit `S.scene.head` (make it a bytearray / rebuild bytes)
  and keep `S.files['.buf']` consistent). Children with a place under `EscapeVehicle_Animation_F07`:
  the van (V_Van_00: boarding box, KillBox, doors, wheels ride on it), `PathBlockerVan` (= the stop),
  `TriggerBox_RearDoors_Open`, `EscCamera_01\CameraTrigger*` + CCameraBox cameras, `BoardingCar`.
  Van 01's field 14..16 = 7.2 / 8.0 / 8.48 s (drive in / wait / out).
- A STRAIGHT lane at x = -1000 (east lane; carriageway x -5700..-300) from z 3000 to 16000 meets NO
  static vehicle within 400 (nearest: bus #02 at (-1518, 6151), 518 away). x = -1300 meets that bus.
  The far block's cars are at x -4228..-2426 (z 13131..14404): clear. So a straightened drive needs
  no prop removed; the owner's "remove some props" becomes unnecessary (say so).
- Rectification recipe (lead's choice; see 1.6 for the alternative): for every table point q, take
  its projection on the ORIGINAL main-drive polyline: arc length s and signed lateral offset d; new
  point = (lane_x + d, y_floor + 2, z_wait + s). Rotation keys: all = heading north (quaternion
  (0, 0, 0, 32767) in the (x, y, z, w) int16 order, i.e. the identity) - GUESS that the crash pieces
  look acceptable without their yaw; the main drive is exact. Apply the same mapping to the
  children's ZGEOM[2] (and the .gms records: kl_fa_author.place). Then kl_fa_author.van_fit finds
  facing north (width 0) and place_vans lays the line at (VAN_X, VAN_Y, VAN_STOP_Z): add module
  variables for x and y (today ROAD_X / ROAD_Y are used). kl_fa_street.van_pose / RING / exit box
  follow the placed stop (already parametrised by the stop).

### 1.3 Stock mechanisms (schema re/kl2.json; field numbers 0-based)
- TriggerBox (18 fields): 0 enabled, 2 count?, 13 eTGS_AllInside, 14 ECPS_* (ECPS_FA_MERCONLY,
  ECPS_BOTH, ECPS_FA_RESPAWNONLY ...), 16 EFAMPS_ALL_MODES, 17 = targets (refs). A trigger starts a
  squad by naming one of its routs. Converted Dead Men boxes have the same 18-field Dog Days layout
  (kl_fa_author.wire checks `len(v) == 18`).
- ZSquadScript (21): 0 EAttitude eStayBack / eUnleashed, 1 EGameType, 2 EIdleAlertness, 3 bool
  'active from the start' (ASSUMPTION), 4..18 = 15 reference lists (8 = 'wiped out' list, stock
  targets TC_AllDead counters; the others unknown), 19 bool, 20 I.
- SquadModifierBehaviour (29): 0 ELeashModifier (eLM_Leash / eLM_Unleash: unleashed = they hunt /
  rush), 1 damage, 2 health, 4 EActivationModifier (eAM_Activate / eAM_Deactivate: SetActorActive),
  5 EEngageModifier (eEM_HoldFire / eEM_FireAtWill), 6 eALM_Alert, 7 EVulnerability, 9 EDefendModifier
  (eDM_Normal / Tight / Loose), 10 Bloodlust, 14 EVision factor, 15 ECoverModifier, 17 EDefendMoveSet
  (eDMS_Sneak/Walk/Run/Sprint), 19 blind-fire probability, 24 s, 25 b, 26 refs, 27 b, 28 b.
- DefendBehaviourRout (10): 0 s (an actor path or ''), 1 refs = Pos#nn boxes (children with their own
  positions), 2 b, 3 b, 4 EDefendMoveSet (eDMS_Sprint / Run / NotSet), 5 EDestinationFormation,
  6 f*?, 7 refs (what fires when they arrive, e.g. a SquadModifier), 8 b, 9 b.
- RunToCoverBehaviourRout (3): 0 refs = RunToPosInfo children, 1 b, 2 b. RunToCoverPosInfoRout (6):
  0 b, 1 b, 2 b, 3 ERunToCoverMoveSet (eRMS_Run / Sprint / SneakRun), 4 EPreferredCoverUsage, 5 s.
  F07's squads: `10_RunToCover` and `20_RunToCover` (a RandomTrigger picks one in stock; fields 5 / 6
  of the RandomTrigger name them), `30_smUnleash` (SquadModifier eLM_Leash or eLM_Unleash +
  eVIM_Factor_2_0), `40_RunToEscape` (Defend, one Pos#01). Each actor group `Police#0n` / `Police_SWAT_01__*`
  holds a `Ground` ZFFActor + ZSoldier.
- FlankingBehaviourRout (5): 0 s, 1 s, 2 refs (`LeftFlank#1`, `RightFlank#1` children with positions),
  3 b, 4 b. The campaign's tower guards use these (survey below).
- TriggerDelay2 (F07, 5): 0 f seconds, 4 refs. TriggerDelay (Dead Men-converted, 5): 0 I seconds,
  3 refs. TriggerCounter (5): 0 I count, 3 refs?, 4 refs (kl_fa_author uses f0 and f4).
  TriggerActorsDead (3): 0 refs actor groups, 1 b, 2 refs - EXISTS ONLY inside F07's bot squads
  (children of Gameplay!merc_bot_squad!Squad#0n, which the graft drops): not available as single
  nodes. 'the more you shoot the more they run away' therefore = squad-level chains through
  ZSquadScript field 8 (wiped out -> the neighbours' fallback rout), stock idiom (F03 reinforcements).
- ZSoldier (23): 0 ESoldierStyle (eArmy, eThug, eHeavyThug, eGuard, eSneakySwat, eSwatWithShield, eDog,
  eStreetCop), 1 / 2 ESpecialFeature, 3 ESkillLevel (eN00b, eAmateur, eRegular, eVeteran, eElite,
  eCustom), 4..17 fourteen floats (the eCustom tuning), 18 f*?, 19 EIsMercenary, 20 b, 21 ESRGameType
  (eSR_AllTypes / eSR_FragileAllianceOnly / eSR_FragileAllianceUCC), 22 b. Stock FA census (nine
  levels): eThug/eCustom 144, eArmy/eCustom 140, eStreetCop/eCustom 38, eArmy/eRegular 28,
  eGuard/eRegular 23, eDog 5. Float rows: eArmy custom (50,50,50,175,50,1,1,1,1,50,50,5000,800,800);
  eStreetCop (50,50,50,100,0,1,1,1,1,50,50,5000,800,800); eGuard regular (70,40,50,65,0,...,5000,800,800);
  eThug custom bots (50,50,50,280,50,...,1,600000,600000); eArmy regular (85,82,82,150,0,...);
  eHeavyThug custom boss (75,45,45,175,50,...). Meaning of the floats NOT read. Dead Men-converted
  guards are ('eGuard', 'eRegular'); Dead Men police ('eArmy', 'eRegular' / 'eVeteran'),
  eSwatWithShield on the shield squads (not kept).
- FakeTarget 'Mercenary' sits on every stock escape van's Body_Main (F01 F04 F05 F07 F09, values
  ('Mercenary', -1, '', 20.0, [], 0, 1, 0, 0)): police treat the van as a target -> they SHOOT THE VAN
  when they see it (that is how stock vans get destroyed; crash pieces Activate_Crash_01..04). So
  "the closer you get the more they shoot it" = bring police with a view of the van as the crew nears:
  shorten the RunToEscape chain (stock 44 s + 18 s; the run box is 28 m before the stop) and keep
  wave 3 at the SWAT truck north of the stop.
- OnlineEscAnimatedVehicle fields 14 / 15 / 16 = drive in / wait / drive out seconds; the round gets
  60 s once the first van has left (re/retomoto_street.md 6).
- Kept campaign single nodes idiom: kl_fa_author.CAMPAIGN_KEEP (STEPS = the campaign's own trigger
  boxes, kept as top-level nodes with their lists; what they name of the dropped campaign is cut by
  kl_fa.repair; wire() sets them MERCONLY). Any converted top-level campaign node can be kept that way.
- Free F07 objects (top-level, not used by kl_fa_author / kl_fa_street): TriggerBox
  `Gameplay!020_Loot!FollowPlayers!tbCountPlayers` (MERCONLY, field 15 = 1; today NOT kept, it names
  the counter kl_fa_author uses for the main room - re-point its list); TriggerDelay2 under
  `Gameplay!010_FirstFight!`: `RivalMercs!Timer` (2.0), `RivalMercs!RandomizeFight!Timer_LEFT/_RIGHT`
  (1.0), `RivalMercs!DisableVisionBlocker!Timer` (23.0) / `TimerInputAI` (1.0), `RivalMercVan!Timer_PFBlocker`
  (20.0), `RivalMercVan!CoverStateChangerHero!Timer`, `RivalMercVan!TimerMercsVanExit` (2.0),
  `Shutters!TimerShuttersClose(_RIGHT)`, `Shutters!TimerShuttersOpen(Dif)`, `Shutters!PF_Blocker!Timer_PF_LEFT/_RIGHT`
  (4.0); AIDWrapper `Shutters!Activator_Shutter_*` x4 (any message); ActivateGeom
  `Shutters!GeomActivator_TearGas_RIGHT`; the F07 squads' own `RandomTrigger` (fields 5 / 6 = the two
  RunToCover lists) and `30_smUnleash`. Add a kept name to kl_fa_author.KEEP (Select pattern) or
  kl_fa_street.KEEP / CHAIN.

### 1.4 The lobby and the elevator (M09_B, converted; positions world)
- Lobby car `..._Int_A_00` at CAR_B (6272, 563, -6305), doors at x 6112 facing -x; the player arrives
  there by the hook's join. Lobby floor y 162 (STAGE_D), elevator landing y 563, stairs between.
  Lobby bound (2600 42 -8150)-(6109 1254 -4850). Front door x 2600, z -7300..-5700 (16 m wide).
- The lobby FRONT IS GLASS: `SO0400_JPN_Facade_Entrance_A_01` spans (2431 -100 -8837)-(5873 2600 -2650)
  with 28 `Shards_*` and two `ShatterPillar` entities; hero blockers `ColiObj_weweBox01..04` (flags
  0x108) close the forecourt's north / south flanks (x 180..3499, z -11027..-8895 and -4025..-1893):
  the forecourt is a corridor z -8900..-4000 from the door to the road. So anything on the forecourt
  or the road between z -8900 and -4000 is IN VIEW through the glass from inside the lobby; a spawn
  there pops in visibly. Out of view from the lobby: the road south of z -8900 (the SWAT van south
  `V_JPN_SWAT_Van_South` at (-2208, 0, -12506) + police car (-1189, 32, -12382)) and north of z -4000
  along the kerbs beyond the facade's ends, and everything north of the first road block.
- Campaign trigger boxes of M09_B worth keeping (converted TriggerBox, 18 fields after conversion):
  `Mercenaries!TriggerBox_1_LeaveElevator` (5902, 709, -6488) half (150, ?, 1400) = ACROSS THE LOBBY
  CAR'S DOORS (x 5902, 28 m wide) - the elevator trigger the owner asked for;
  `Enemies!010_RetoBldFront!Squad_Teargasguys\TriggerBox_18_lobbyStairs` (4805, 487, -6445) half
  (350, ?, 1400) and `...\TriggerBox_2_MidLobby` (4213, 279, -6445) half (150, ?, 1400) (children of
  a KEPT squad: they come along; their lists are pruned); `Enemies!020_Street!VSquad_BlockTraffic\
  TriggerBox_LeaveLobby` (2345, 257, -6473) = just outside the door (child of a dropped VSquad);
  `...\TriggerBox_Leaving_Square` (423, 132, -6430) half (150, ?, 2500) = the forecourt's road edge.
  Street boxes: `Enemies!020_Street!TriggerBox_BeforeWalkway` (-3362, 47, -1272), `TriggerBox_FlankLeft`
  (-4451, 357, 1256), `TriggerBox_ACtivateShieldSwats` (-2938, 508, 2629) half (500, ?, 200),
  `TriggerBox_FireMoreGas` (-3726, 508, 1978), `TriggerBox_SWAT_Car_Singleplayer` (-2938, 461, 4673),
  `TriggerBox_ChangeObjective` (-2938, 508, 5003), `TriggerBox_Walkway` (-2938, 508, 1102),
  `Squad_North_SWAT\TriggerBox_UnleashSWAT` (-3316, 134, 7282) half (150, ?, 3220),
  `TriggerBox_wrongWaySouth` (-2938, 26, -9337). Campaign TriggerDelay nodes (top-level, converted,
  5 fields [I, I, I, refs, b]) that could be kept as spare timers: `Timer_shutters` (8), `Audiotriggers!Timer`
  (12), `Enemies!020_Street!Timer` (5), `Timer#02` (13), `Music!*`.
- Campaign street squads kept today (kl_fa_author.squad_plan, 10 squads / 20 men; all ZSoldier eArmy
  Regular or Veteran, DM form): `010_RetoBldFront!Squad_Teargasguys` (2 at (430,27,-6850) (420,27,-6223),
  field 3 = 0; FlankingBehaviour points (407,-6895) (446,-5342); Unleash modifier), `Squad_InFront`
  (3 at (447,26,-7956) (-367,26,-7594) (-137,23,-7263), field 3 = 1 = ACTIVE FROM THE START: they stand
  on the forecourt during the tower part; routs Regroup = Defend Pos (439,25,-5882), Flanking (384,-7825)
  (7,-7182), Unleash, SquadModifier), `020_Street!Squad_RoadBlock_South` (3 at z -12900..-13000; routs
  01_DefendBehaviour Pos (-1580,10,-12030), 03_Retreat Pos (-6758,61,-12613) -> Deactivate),
  `Squad_RoadBlock_South#02` (2; 04_Retreat (-6758,-12613), 01_SquadModifier Unleash),
  `Squad_SWAT_From_Behind_South` (3 Veteran at z -14100; Flanking (-4579,-13113) (-3896,-13143),
  Unleash), `Squad_SWAT_From_Behind` (3 Veteran at (-3838,6,-2160); Flanking (-4364,1,3300) (-2757,1,3137)
  -> SquadModifier_Leash), `Squad_SniperResponse` (1 at (-4808,24,2650); Defend eDMS_Run (-4600,563,1143)
  (-4748,381,1601) = up on something), `Squad_Launcher_Dude_North` (1 at (-3468,4,2804)),
  `Squad_RoadBlock_R2` (1 at (-1455,9,3617); DefendBehaviour_Regroup eDMS_Sprint (-3301,6,4712),
  DefendBehaviour (-2096,6,4041)), `Squad_RoadBlock_L` (1 at (-4318,9,3839); Defend (-4184,6,3825)).
  The campaign's SWAT-van arrivals (`VSquad_*`: ZHavokCar + VehicleExit routs) are NOT kept
  (unproven class in Dog Days, re/cars.md): "SWAT vans" here = the two STATIC SWAT vehicles as spawn
  places (actors start at their rear doors), not driving vans.
- Navigation mesh: kl_fa_street.Nav (polygons walkable from the road; `put(x, z, towards)` pulls a
  point onto the mesh; PLAY area x -6200..3000, z -12500..13800, y -150..110). The forecourt and the
  lobby are on the mesh; islands exist. Mesh height is y -48..-40 (below the collision floor 20:
  actors placed on the mesh were seen standing fine - the game snaps them).

### 1.5 The tower's room squads (M09_A, converted; kl_fa_author ROOM_SQUADS = 020_Office)
- `Squad_Guards_Inside_01` (2 at the glass / table; Flanking points (5146,21028,522) (5119,21021,-772);
  the InvisiBomb kills the one at the glass), `Squad_Guards_Inside_02` (4 at x 3600..3700 = the DOOR
  end; Flanking (4093,315) (4104,-509)), `Squad_Guards_Inside_03` (3 at x 3618..3699; Flanking
  (4045,599) (4526,-681)); all eGuard Regular, Flanking + SquadModifier (eALM_Alert) only, no Defend
  rout, field 3 = 0 (ROOM_WAITS), started at the blast by kl_fa_author's blast timer (their lowest
  rout = the SquadModifier? check squad_plan's 'first' rule: the lowest-named BEHAVE rout named by a
  campaign trigger; FlankingBehaviourRout is in BEHAVE). Boardroom: floor 20996, x 3430 (door)..5850
  (window), z -1200..800; table x 4600..5450. Reception beyond the door x 2900..3400; its squads
  `030_Reception!Squad_Hallway(#01)`, `Squad_ShootBeforeStorm` start at step 1 (F07 box at x 4200).
  Campaign single nodes available in 020_Office: `AI_Players!Enemies!020_Office!Timer`,
  `SmokeTimer` (TriggerDelay), `Activate_BreakingDoor_Sound` (AIDWrapper) - keepable as spare timers.
- "run away and hide for cover" = re-place the three room squads' flank points at the door end and
  into the reception (x 3000..3600, behind the door jambs / reception desk) so the guards RUN from the
  window at the blast and hold there; eDMS has no field on Flanking: a Defend rout with eDMS_Sprint
  would need a controller the squads do not have (kl_fa_blast writes controllers token for token:
  possible but a new controller = a bigger risk; prefer values of existing routs).
- "pistols rush": one squad (Guards_Inside_03, 3 men) gets eLM_Unleash on its SquadModifier, fired by
  a kept campaign TriggerDelay 6 s (GUESS) after the blast; the other room squads keep eStayBack /
  Leash. Weapons: kl_arms.arm hands classes by seed; tie the rushers to pistols (force the class).
- "the higher the caliber the more technical": ZSoldier style / skill by weapon class in kl_arms
  (pistol -> eThug eAmateur, SMG -> eArmy eRegular, shotgun -> eHeavyThug eRegular, rifle -> eArmy
  eVeteran, MG -> eArmy eVeteran; floats = the stock row of that style; police keep eStreetCop for
  pistol carriers) and squad knobs (rifle squads: Flanking / RunToCover, SquadModifier eDM_Tight,
  blind-fire low; pistol squads: Unleash). ALL GUESSES on the game's reading of these enums.

### 1.6 Decisions the lead has taken (the designers work inside them)
- No new entity. New controllers only if a designer shows no value-only way (kl_fa_blast has the
  token writer). Everything else: values and reference lists of existing stock / campaign objects,
  re-placed (kl_fa_author.place) - the house rule.
- The van is straightened (1.2) in a NEW module tools/kl_fa_van.py hooked from kl_fa_street before
  kl_fa_author.place_vans runs; `--van-bent` keeps today's drive. Height from the .HVK floor.
- The street spawns at the elevator (LeaveElevator box, kept MERCONLY) with spawn places OUT OF VIEW
  of the glass lobby (1.4), retreat routs to hold lines on the road, squad-chain fallbacks, a short
  RunToEscape chain, wave 3 kept at the SWAT truck north; the 8 "from the south" campaign squads still
  come up behind the crew (started at the first step on the road, not the door).
- Tower: room guards run to the door end / reception at the blast; one pistol squad unleashed 6 s
  later; soldier style and skill by weapon class.
- Live-test order: one variable per run, as in re/retomoto_street.md 8; nothing runs while the owner
  plays; the installed build and hook are another session's and are NOT touched by this work.

---------------------------------------------------------------------------------------------------

# BUILT (2026-10-10, offline; the lead, inline, from the one design that came back before the usage limit)

CORRECTIONS to section 1, found while building:
- 1.2 said "a straight lane at x = -1000". That strip is a RAISED parking bay (collision y 20). The road in
  cross-section (kl_escape.Walk on the .HVK of M09_B, z 5000..16000): raised y 20 west of x -4900, west
  carriageway y 0 at x -4900..-3100, median y 20 at x -3100..-2900, **east carriageway y 0 at
  x -2800..-1500**, raised y 20 east of x -1500. The lane of the van is **x -1850, y 2** (floor 0 + the 2
  the van has over the road of F07).
- 1.2 said "no prop removed". One is: the police barricade `Collapse_JPN_PoliceBarricade_02` (one static
  object across the whole east carriageway, x -2869..-389, z 13467..13821, 1.5 m high), 27 m past the stop.
- 1.4: campaign squad groups are not only translated, some are TURNED (`Squad_RoadBlock_South`: 90
  degrees); the place of a child is set in the frame of its parent (`kl_fa_street.put_world`, read back to 1 unit).

## 2. The round as built

1. Balcony, countdown, the window blows (unchanged). The nine boardroom guards RUN AWAY from the window:
   one squad to the corners at the door end, two out through the door into the reception.
2. 6 s later the three-man squad that ran furthest - pistols, lowest skill - is unleashed and comes back
   through the door. The four at the door jambs (SMGs) hold tight; past the table the five of the
   reception (rifle / SMG / shotgun) join. Staged descent, loot, elevator: as before.
3. Lobby car. The first steps of the crew out of the car cross the campaign box across its doors (28 m):
   the three policemen who stand on the forecourt run to their police car and hold; 5 s later two more run
   in from the south end of the forecourt, from where the glass front does not show them.
4. Out of the front door: the forecourt police hold tight. First step on the carriageway: wave 1 rises in
   the traffic to the north (10 + 3), and eight come up the road from BEHIND - three from the rear doors of
   the static SWAT van at the south end, three from the police car beside it, two unleashed.
5. Every squad wiped out sends its neighbours one line back; a second loss on a side sends the rest to the
   van. Kill the forecourt police and the men behind the crew run off west and are switched off.
6. The road block (13 + dog) as before; its fall-back line is 20 m SOUTH of the stop of the van, in sight of it.
7. Wave 3 comes out of the static SWAT truck, 17 m west of the stop. 13 m before the stop a box unleashes
   them. 28 s after the "run" line every squad alive walks to its place round the van (stock: 62 s).
   The van has the stock "Mercenary" target on its body: whoever sees it shoots it.
8. The van waits in the east lane, pulls 21 m straight up to the stop, rear doors to the crew, and leaves
   straight north through the gap where the barricade was.

## 3. Tower (tools/kl_fa_author.py: ROOM_*; `--room-classic` = as before)

| squad | at the blast | flank points now (world; were) | then |
|---|---|---|---|
| `Squad_Guards_Inside_01` (2; one dies at the glass) | its flank rout | (3700, 20996, 700) (3700, 20996, -900); were (5146, 522) (5119, -772) at the table | `ZSquadScript` f0 eUnleashed -> eStayBack: hides |
| `Squad_Guards_Inside_02` (4) | its flank rout + `02_SquadModifier` | (3300, 20995, 500) (3300, 20995, -700): reception, behind the door jambs | modifier f9 eDM_Tight, f26 emptied |
| `Squad_Guards_Inside_03` (3) | its flank rout | (3100, 20995, 900) (3100, 20995, -1100): far corners of the reception | blast + 6 s: campaign `SmokeTimer` (kept) -> `01_SquadModifier`, f0 eLM_Unleash, f26 emptied |

GUESSES: every point (mesh heights read by the design pass, not re-checked by the lead), the 6 s, that
eLM_Unleash makes a squad hunt, that eDM_Tight holds, that a FlankingBehaviourRout sends men TO its points.

## 4. Street (tools/kl_fa_street.py: DYNAMIC; `--street-classic` = as the owner played it)

| what | object | change |
|---|---|---|
| elevator trigger | campaign `Mercenaries!TriggerBox_1_LeaveElevator` (5902, 709, -6488), kept as a single node | MERCONLY; list = `Squad_InFront\Regroup` + `Enemies!020_Street!Timer` |
| 5 s later | campaign `Enemies!020_Street!Timer` (TriggerDelay, kept) | -> `Squad_Teargasguys\FlankingBehaviour` |
| forecourt three | `Squad_InFront` (on the forecourt from the load) | `Regroup` point -> (-200, 25, -6600) behind police car 02, eDMS_Run; its modifier eDM_Tight, fired by the front-door box |
| second pair | `Squad_Teargasguys` | start (-800, -10800) (-1300, -10600): south of the end of the facade; flank points behind police car 01 |
| from behind | `Squad_RoadBlock_South` (3, at the rear doors of the SWAT van south), `..._South#02` (2), `Squad_SWAT_From_Behind_South` (3, moved to the police car south) | started by the wave 1 box, not the door. `#02` now starts by its Unleash modifier: the pick of kl_fa_author was `04_Retreat` -> Deactivate, so in the rounds the owner played those two ran off and vanished at the door |
| wave 1 | `Gameplay!020_Loot!tbExitLoot` | names the `10_RunToCover` of each squad (the stock RandomTriggers picked 10 or 20); `20_RunToCover` lies 24 m further north = the fall-back |
| wave 3 | `040_EscapeEntranceLeft / Right` | actors start at the rear doors of the SWAT truck (-3600 / -3800 / -3400, 10300) |
| van guard | the spare F07 box `Gameplay!020_Loot!FollowPlayers!tbCountPlayers` | across the road 13 m before the stop, MERCONLY -> the two `30_smUnleash` of wave 3 |
| clock | `Gameplay!RunToEscape!Timer1Player / Timer3Player / Timer` | 44 / 32 / 18 s -> 20 / 14 / 8 s |

"Out of view" rests on one reading: that the hero blockers of the forecourt, `ColiObj_weweBox01..04`, mark
where the facade stops being glass. Not looked at in the game.

## 5. Fall-back chains (`FALL`; `--no-chains` = off)

`ZSquadScript` field 8 of a squad names routs of its neighbours. ASSUMPTION, the same one the loot gate of
the boardroom rests on and never seen firing: that list is sent when the squad is WIPED OUT. If it is
another event the squads fall back at the wrong moment: a run with `--no-chains` tells.

| wiped out | sends |
|---|---|
| `Squad_Teargasguys` | `Squad_InFront` across the road (its flank points, now (-2800, -7800) (-2800, -5200)) |
| `Squad_InFront` | `Squad_RoadBlock_South` and `#02` to the west kerb (-4500, -7000) and off (the campaign Retreat -> Deactivate) |
| wave 1 front: `LeftParking`, `LeftFurther`, `RightGround` | the rear squads of that side to their second line |
| wave 1 rear: `RunForDumpster` <-> `RightPlatform` | the other to its place at the van |
| road block front: `ExitSkywalk`, `ExitSkywalkNoCover` | the two squads behind the cars on that side to stop + (-2650, -2200) (-1850, -2000) (-750, -2200) (-550, -1800) |
| road block: `Exit_Left` <-> `ExitStreet_Left`, `Exit_Right` <-> `ExitStreet_Right` | the other to its place at the van |

Nothing happens while a squad has only lost some of its men: the one stock object that counts single
actors (`TriggerActorsDead`) exists only inside the bot squads of F07, which the graft drops.

## 6. The van (tools/kl_fa_van.py; `--van-bent` = as before)

- Position table (564 keys) and rotation table (550 keys) of `V_Van_00` rewritten IN PLACE in the .buf head:
  x -1850, y 2, heading north on every key. A key keeps its distance along the baked drive (speed profile)
  and its sideways offset (crash pieces, clamped to x -2750..-1550). The approach is scaled by 0.41 so the
  van waits at z 8700 and stops at z 10800. The drive away is scaled by 0.58 and ends at z 14900: from z 15000 a
  queue of backdrop cars (`PC0700_M09_Cars_Qeue_A_01`) fills the east carriageway, and the baked 70 m would end inside it.
- Moved with the same mapping: `PathBlockerVan` (the stop), `TriggerBox_RearDoors_Open`, the two boxes of
  the escape camera, its camera and two points. The group is identity at the origin.
- Everything of the street layer follows the stop: exit box z 8300..12800, boarding at (-1853, 121, 10463)
  (the rear doors, towards the crew), the 13 places round the van (none within 3.5 m of the lane).
- Hidden: the east barricade (correction above). It stands inside the north level bound: no player gets there.
- NOT decoded: the frame -> key tables. No key was added, dropped or reordered, so they should address
  the same keys. GUESS: a crash piece without its yaw looks acceptable.
- `python tools/kl_fa_van.py check <archive>`: drive straight, 2 over the floor at every sampled key,
  rotation keys all identity, no static vehicle in the lane. Part of `kl_fa_street.py report`.

## 7. Skill by weapon class (tools/kl_arms.py: FORCE, SKILL; the two parts of Retomoto only)

`FORCE`: Inside_03 and Inside_01 pistols, Inside_02 and ShootBeforeStorm SMGs, Hallway#01 rifles, Hallway a
shotgun. `SKILL` sets `ZSoldier` field 3 from the class handed out: pistol / revolver eAmateur, SMG /
shotgun eRegular, rifle / MG / rocket eVeteran, sniper eElite. The STYLE (field 0) is not touched: it may
pick animations. No stock Fragile Alliance level uses eAmateur or eElite: what the game makes of them is a GUESS.
Built: tower 22 eAmateur / 20 eRegular / 3 eVeteran; campaign police of the street 4 / 13 / 3. The police
F07 brings are stock and untouched.

## 8. Not done

- "The more you shoot" is squad by squad, not man by man (section 5).
- Nothing makes police AIM at the van on purpose; the level only puts men with a view of it there.
- The driving SWAT vans of the campaign (`VSquad_*`, ZHavokCar) are not used: unproven class in Dog Days.
  "SWAT vans" = the two parked ones as spawn places.
- The heights given to campaign points on the street are the campaign's (y 5 / 22 / 25), not measured.

## 9. Live test order (nothing has run; one variable a run; ask the session that holds the game)

| run | build | look at | if not |
|---|---|---|---|
| D1 | default | the van: on the road, straight, stops, rear doors, leaves through the gap; boarding at its rear | sinks / floats: `kl_fa_van.VAN_Y`. Jerks or teleports: the index tables do depend on the key values -> `--van-bent` |
| D2 | default | elevator: three run to the car as the crew steps out, two more 5 s later, nobody pops in | they pop in view: move the start places further south |
| D3 | default | tower: guards run from the window, three come back about 6 s later | guards stand still: the flank points are off the mesh -> `--room-classic` |
| D4 | default, then `--no-chains` | kill one whole squad of wave 1: do its neighbours fall back; do they fall back with nobody dead | they move at once: field 8 is not "wiped out" -> ship `--no-chains` |
| D5 | default | at the van: is it shot, does it survive the 8 s | destroyed every time: `GUARD_BEFORE` smaller, `RUN_CLOCK` longer |
| D6 | default | are pistol men visibly worse shots than riflemen | no difference: `kl_arms.SKILL = None` |

## 10. Offline result (2026-10-10 11:50)

`python tools/kl_fa_blast.py test G:/kl_scratch/ai_dyn1 --keep` (the command behind the builds the owner plays;
street + blast + loot layers): **RESULT: PASS**. kl_graft.verify 1 problem, known (particle template names);
kl_fa.check DEGRADED 1 (no bot squads, as before); kl_fa_blast 0 faults; kl_fa_loot problems 0;
`kl_fa_street.py report` 0 faults: elevator box -> 2 squads / 5 actors, wave 1 9 / 21, wave 2 11 / 18,
wave 3 2 / 3; 13 fall-back lists, every entry resolves; van: 391 drive keys at x -1850.0, y 2.0, z 8700..14900,
rotation keys all identity, floor 2 below the origin at every sampled key, no static vehicle in the lane.
25,735 entities, 313 MB. Members: .prm 58.1 MB, .ANM 20.6, .fxc 16.9, .TEX 223.3, F01_Main.WAV 23.0 - no
member grew (no model, sound or entity was added). Folder: `G:/kl_scratch/ai_dyn1\R09+M09_A (R09 = F07+M09_B)`.
This build has NO wardrobe and no KLJoin.ini beside it: for the owner it has to go through the same finishing
steps as `<work>uild\y_lootetomoto_loot` (re/retomoto_loot.md 6). NOT INSTALLED, NOT RUN IN THE GAME.
Three faults the checks caught on the way: a campaign squad group turned by 90 degrees (points landed 100 m
off), the barricade across the lane, the queue of backdrop cars at the end of the drive.

## 11. After the owner played it (2026-10-10 midday): the van's end, the soft enemies, the voices

Owner, verbatim: "for retomoto i dont get why i survive from being shot so much maybe because im by myself? the
van is almost perfect its just when it finally leaves like before the end game rtesult it goes into a car just
make sure it drives off down the road the whole time". So run D1 of section 9 is seen: the van is on the road,
straight, stops and is boarded. Three changes, built offline, NOT run in the game.

### 11.1 The van drove into a car

Read: `PC0700_M09_Cars_Qeue_A_01` is ONE static object, a queue of parked cars behind the north barricade; its
collision spans x -2648..-1755, z 14832..16158 - the whole east carriageway. The first build ended the drive at
z 14900 because the lane check sampled one cell every few metres and met the queue only at z 15430: the van's
nose (its last key + its own length) stood in the first car. Now:
- the queue is hidden with the barricade (`kl_fa_van.PROPS_OFF`, two objects, both inside the north level bound);
- the drive away is STRETCHED, not cut: it ends at z 21000, 102 m beyond the stop in the baked 8.48 s (F07: 70 m).
  The road and its collision run on to z 30000 and nothing else stands in the lane;
- `kl_fa_van.check` samples every 20 units across the van's width, to 6 m beyond the last key.
NOT ESTABLISHED: what the van does after its last key while the result page waits (stand, or be hidden). It is
now 100 m away and still on the road when that happens. If it is seen standing there, raise `END_Z`.

### 11.2 Why the player survived so much fire

What was established (all read from the built level and the stock levels, nothing from the running game):
- The player, the settings object and every weapon template of the build are stock F07's. What one hit costs
  the player is therefore stock; no single-player or Arcade scaling was looked for in the exe (NOT established).
- The difference is in who shoots. `ZSoldier` rows in the played build:

| who | actors | skill | floats 4..8 | field 15 |
|---|---:|---|---|---:|
| F07's own police on the street (stock) | 18 | eCustom | 50 50 50 175 50 | 5000 |
| F07's own police (stock) | 8 | eRegular | 85 82 82 150 0 | 5000 |
| tower guards (Dead Men) | 44 | 22 eAmateur, 20 eRegular, 2 eVeteran | 50 50 50 50 50 | **1000** |
| Retomoto's boss (Dead Men, a designer's row) | 1 | eVeteran | 30 50 30 300 50 | 5000 |
| street police (Dead Men) | 20 | 4 eAmateur, 13 eRegular, 3 eVeteran | 50 50 50 50..120 50 | 5000 |

- Field 15 = 1000 is in NO stock level sampled (nine Fragile Alliance + three story levels: 5000 on all 256 FA
  police, guards and SWAT; 1 on bots and story thugs; one 100000). The fourth float reads as health (dog 50..80,
  guard 65, cop 100, SWAT 175, bot 280, boss 300): the tower's guards had 50.
- The eAmateur rows were MY first try at "pistols are worse" (section 7): it made 26 enemies softer still.
- `SquadModifierBehaviour` damage / health modifiers: eDmgM_NotSet on all 37 modifiers of the level - no squad is
  scaled down. `ZFFActor[2]` is 0 on the tower's actors and 1 on police, but 0 is also what all 23 stock eGuard
  actors have: left alone.
- NOT established: which float is accuracy, what field 15 does, whether few shots landed or each landed soft, and
  whether being the only target changes anything. In stock Arcade seven AI heisters share the fire; Retomoto has
  none (kl_fa.check: DEGRADED, no bot squads), so alone the player takes ALL of it - being alone cannot be why it
  was soft.

What is built (tools/kl_arms.py `ROWS` / `SKILL`, Retomoto's two parts only): every armed Dead Men actor whose row
is Dead Men's default (first three floats 50 / 50 / 50) gets one of three rows copied whole from stock Fragile
Alliance police, by the class of weapon handed out:

| class | row | stock source | Retomoto: tower / street |
|---|---|---|---:|
| pistol, revolver | eCustom 50 50 50 **100** 0 .. 5000 | eStreetCop, 38 actors (F01's platform police) | 22 / 4 |
| SMG, shotgun | eCustom 50 50 50 **175** 50 .. 5000 | eArmy, 140 actors (F07's police on this street) | 20 / 13 |
| rifle, MG, sniper | eRegular **85 82 82** 150 0 .. 5000 | eArmy, 28 actors (8 of them F07's) | 2 / 3 |

So nobody on the map is weaker than a stock policeman, and "higher calibre = more technical" is the stock row with
85 / 82 / 82. The style (field 0) is still not touched. The boss keeps his own row. GUESS only in which class gets
which row; every number is a stock one. `kl_arms.SKILL = None` turns the pass off.

### 11.3 Voices

- The build before was made with `kl_fa_blast.py test`, which leaves `kl_snd.VOICE` off. The command for a play
  build is **`python tools/kl_fa_loot.py test <out>`**: it sets `kl_snd.VOICE = True`, builds blast + street + van +
  AI + loot, lightens, adds the wardrobe and copies KLJoin.ini. F01_Main.WAV is 27,158,864 bytes again, the size
  re/bots_voice.md 6.1 gives for a build with the repairs.
- The briefing and reminder lines no longer speak of F07's data theft: `kl_fa_author.RT_LINES` (settings fields
  17 - 20, 127, 130, 136, 137), the eight lines of re/bots_voice.md 6.2. Its 6.3 (the exit-heist line: a plain
  .LOC leaf in nine languages) is NOT done.

### 11.4 Result

`python tools/kl_fa_loot.py test G:\kl_scratch\ai_dyn2`: **RESULT: PASS**. kl_graft.verify 1 known; kl_fa.check
0 CRASH / BROKEN; street 0 faults; loot 0; kl_impact 0; kl_chars.undrawn 0; kl_arms check 0 findings; van: x -1850,
y 2, z 8700 .. 21000, lane a clear floor 2 below the van to 6 m beyond the end. Folder
`G:/kl_scratch/ai_dyn2/retomoto_loot` (zip 212 MB, KLJoin.ini, KLWardrobe.ini). It has the wardrobe but NOT the four
Payday 2 mask plates of the installed build: that step is kl-merge-01's (`kl_chars.py wardrobe ... --plates=`).
