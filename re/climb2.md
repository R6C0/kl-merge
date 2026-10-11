# The level-data climb (track Y1, 2026-10-11) - luvsic's form on our Withdrawal

OFFLINE. Nothing here ran in the game. Labels: READ = from code (address / file named), MEASURED = I ran it on our files,
ASSUMED = says why. Credit: the climb form, the script, the `+0x2C` finding are luvsic's (`third_party/anp/`, his repository
`a-newer-perspective` at c053aa2; `re/luvsic_pass.md`).

Tools: `tools/kl_fa_climb2.py` (new), `tools/kl_fa_climb.py` (+ `snd=` in `merge`, a `+0x2C` check), `tools/kl_anm.py` (`snd_name`,
`snd_index`, `clip_snd_bad`, `fix_clip_sounds`, `sndcheck`), `tools/kl_anmjoin.py` (`stock_snd`, `join(..., snds=)`).
Build: `<work>\build\y_climb\DM03` (zip sha1 52a06779..., from `<work>\build\r_tab\DM03v`, 3 climb spots).

## 0. Short answers

1. luvsic has TWO climbs. (a) Level data: a `ZPlayerAction` use prompt + a `MiniCutsceneRout` with a `Lynch` head that `act`s
   Dead Men's `/Movement/Climb/Up/<class>` clips, PosObjects as the places (`climbs.py`). (b) Loader: `ZFFActionVaultOver` with a
   private vtable, the same job our `klclimb.c` does with a mini animation (`loader/climb.inc`). **Neither has been seen working:**
   (a) "no prompt yet" at his van (HANDOFF.md, 10 Oct ~22:00; the prompt was dead because of the box's own TriggerBox, he moved it to
   the first PosObject); (b) written 11 Oct, tested only by a teleport rig (`ANP_tp.txt`, `scripts/climb_spots.py`), no result in his notes.
2. The level-data climb for Fragile Alliance is BUILT (`kl_fa_climb2.py`): 3 spots on Withdrawal's yard wall, 13 entities, every
   offline check passes. It is a SECOND, independent form beside the hook (`klclimb.c`, off). The honest limit of the form: it has
   **no alignment**, so a 203.5 wall with a clip that rises 172 needs a lifted start (section 4.3). Worth a live look; not proof.
3. The `+0x2C` fault is real, found by luvsic, proven here on all 41 stock files, and was present in exactly one build of ours:
   `z_climb3/M03` (11 climb clips with an offset into Dead Men's bank). Fixed in `kl_fa_climb.merge` (`snd=`), checked by
   `kl_fa_climb.check`. The five tab builds have 0 bad values (the joins take Dog Days' own record whenever it has the clip).
4. AI heisters cannot use either level-data prompt (section 5). The drop link stays their way.

## 1. What luvsic's climbs are, exactly

### 1.1 Level data (`tools/climbs.py`, `docs/HANDOFF.md` Climbing)
- Graft of L01 `01_MiniCut_Vault_Over_Desk` (a group of 3 `PosObject`s + a `MiniCutsceneRout`) into a squad copied from
  `Special!CutScenes!Intro_Shanghai!IntroCollection!Introcutscene` (`eStayBack / eAllTypes / eNormalAlertness`).
- Script per climb (READ `script_for`): `((Lynch| Lynch| ((act| ((subt| 1)| (anim| /Movement/Climb/Up/High)| (weaponhdl| Holster)|
  (lefthandik| 0)| (startpos| <PosObject>)| (blend| 1)| (_dep| ())))| ...))| (Options| Options| ((mode| unbreakable))))`, one `act` per
  step, PosObjects at the heights of the landings (his van: y 30 -> 202 -> 346, i.e. steps of 172 = the High clip's own rise).
- A `PlayerAction` event on the FIRST PosObject (not on the Dead Men hint box: the box's own `TriggerBox` event fired as Kane walked
  in and the message with runtime id 252 left `+0x54` and `+0x7c` at 0 for good, READ `ZPlayerAction` ctor 0x8e92e0 sets `+0x7c = 1`,
  handler slot 26 0x7fdbb0 ignores everything while `+0x7c == 0`, 'Activate' sets `+0x54 = 1`, 'AITrigger' toggles it).
- His stored rotation `[-fz 0 fx | 0 1 0 | fx 0 fz]` for a PosObject facing `(fx, fz)`.

### 1.2 Loader (`loader/climb.inc`)
Dead Men's `ZFFPlayerMovementClimb` (kaneandlynch 0x605b50) as a per-frame tick off `steam_api!SteamAPI_RunCallbacks`, Dead Men's
ray order through kl2 0x7daa80, then a real `ZFFActionVaultOver` (type 0x2B, vtable 0xbb5188) whose slots 2/4/5/10 point at his
functions, playing the same clips, AlignTo (0x80fdc0 via vt+0x208) in phases like ours. Same table (Low 120 / Medium 170 / High 220,
stand-offs 81 / 47 / 47). This is our `klclimb.c` with a different action class.

## 2. The clip merge: his and ours

| | luvsic (`anm_merge.py`) | ours (`kl_fa_climb.merge` over `kl_anmjoin`) |
|---|---|---|
| what is merged | a whole Dead Men animation database path by path (+2.6 MB after filtering) | the three climb slot lists of two sets (+81 KB: 7 clips) |
| bones / poses | by NAME | by NAME, no name added (proved) |
| clip events | copied unchanged | event 5 written as 105 in the PLAYERS' clips (nothing else) |
| `+0x2C` (sound record) | found: offset into the level's own `.SND`; his rule `name` | not known until today; now `fix_clip_sounds` (same rule) |
| proofs | `verify_merge.py` | read-back identical, `kl_anm.audit` clean, base is a prefix, every list = its source, 41/41 stock round trips |

**Event ids (their notes against our id-5 finding).** His notes say Dead Men uses ids 1, 13-19, 21, 24, 30, 37, 38 that Dog Days
never fires, "semantics in DD unknown", and he suspected them for his broken sound (HANDOFF, step 2 of the isolation list). READ
(re/climb_crash.md, re/climb.md row "a clip's events"): an id means something only to the action CLASS that is current on the player
when the clip's event comes due. `ZFFActionGeneric` (kl2 0x637060, which a mini animation has as its slot 13) acts on 5, 9..11, 20, 21,
24..35, 42, 48..51, 53; at id 5 it aligns to the object at `[action+0xc]` with no test, and a mini animation has 0 there: the crash
at kl2+0x7e400. His 21, 24, 30 are in that set but are inert for an action without an object (0x4fe5c0, 0x428d90, 0x77ca60 return at
their slot-12 test). So: **both are right about their own path.** His level form never makes a mini animation: ZMiniPlayerActTask
(0x8e8d00, READ whole) plays through `player vt+0x204`, subscribes the channel (0x7f60e0) and asks the clip for events 0x27 and 0x14
only; no event 5 is asked, and the current action (if any) gets the id-5 entry. His loader form uses `ZFFActionVaultOver`, not the
generic handler. Our renumbering is therefore needed for the hook form (mini animation) and harmless in this one (the build keeps
105; ZMiniPlayerActTask never asks for 5 or 6). His sound breakage is not explained by these ids; the `+0x2C` finding is (below).

**`+0x2C`.** READ third_party `clipsnd.py`; MEASURED `python tools/kl_anm.py sndcheck`: all 21 Dog Days files have 0 clips whose
non-zero `+0x2C` is not a type 1/2/3 record start of their own `.SND`, and all 20 Dead Men files 0 as well (4,090 .. 4,468 records
indexed each). Reader chain (his): ZPlayer vt+0x620 0x6b9d50 -> 0x409170 -> ZDllSound 0x875360 -> ... -> 0x5c8050. In our files:
`z_climb3/M03` had 11 bad (`Up_High 0x2330`, `Up_High_No_Weapon 0x23c0`, `Sprint_Low 0x2450` ...: Dead Men offsets into Dog Days'
bank); DM01/02/03v/06/09 of the owner's tab 0 bad of 1,261 non-zero. The new build: 7 added clips, all cleared to 0 (Dead Men's
record names are not in Dog Days' bank), 0 bad. The climb has no foley sound: expected, harmless.

## 3. What F07 / L03 have, and what a Fragile Alliance player is

- The host level F07 (and so every build) has `MiniCutsceneRout` x14, `MiniCutPosObject` x33, `PlayerAction` x3 (the van's
  boarding), but all its mini cuts are NPC scripts (civilians, rival mercs) and its squads are heavy. The stock template for a cut
  with a player head is DOG DAYS L03: `ROOT\Squad_OutroCut` (squad, `eStayBack`), `...\MiniCutScene` (`(Lynch| Lynch| ((act| ...`),
  started by `Special!Coop_doors!EndAlleyHACK!Fake_EndAlley_Airlock`, a `PlayerAction` whose list names the rout directly
  (MEASURED `scratchpad y1/refs.py L03`: nothing else names `Squad_OutroCut`; only the rout is named, by the action and the airlock
  monitor). The wiring built here is the SAME AS L03's (never run in an FA round; L03's squad is also named by no object), with the text key of the co-op climb wall
  (`CoOpDoors/L03_CoOpDoors/L03_CoOpClimbWall`, ' Climb Wall', in the English `.LOC` of every FA build: MEASURED).
- Forms cloned (`Maker.clone`): squad = L03 node `Squad_OutroCut`; rout = L03 `...\MiniCutScene` with script and finished-list
  replaced; PosObject = F07 `10_RunToGaate\MoveToPosObject#01` (field 0 empty; L03's names an animation node); prompt = L03
  `Fake_EndAlley_Airlock` with fields 1 and 8 changed, box sizes set.
- Root group tree 3 of the root lists squads and routs (F07: 29 of 29 squads, 14 of 14 routs; PosObjects and boxes in no tree:
  MEASURED `y1/tree3.py`): the new groups are listed the same way (7 of them), as `kl_fa_bots` lists its squads.
- **What of the campaign changes for FA.**
  - Head names. READ kl2 0x6ec960 (the script-line parser): `Lynch` makes a 0x2c-byte line bound to `[gamedata+0x828]` (player slot 0),
    flag `[line+0x50] = 1`; `Kane` binds `[gamedata+0x82c]` (slot 1), flag `+0x51`. The player in a mini cut is a SLOT, not a
    character. In Arcade the human is slot 0, so the `Lynch` head is the human whatever model he wears (Kane, Lynch, a wardrobe body).
    A second human (online) is slot 1 or higher: not acted on by a `Lynch`-only script; a human whose slot byte `[player+0x91d]` is
    above 1 hits an `int3` in 0x872f70 / 0x5f6df0 (READ, `movsx esi, byte [ecx+0x91d]; cmp esi, 1; jle`). So: SOLO ONLY; online
    needs a `Kane` section and a rule for slots 2+ (not built, not needed before stage 4).
  - `PlayerFilter` (`ZPlayerAction[16]`). Campaign L03 uses `eBOTH_PLAYERS`; the FA van uses `eBOTH_PLAYERS` (24 of 31) or `eONLY_LYNCH`
    (7), never `eONLY_KANE` (re/fa_round.md). Kept `eBOTH_PLAYERS`. The other enums are L03's (`eIntDest_CtrlPos`, `eIntDir_CtrlDir`,
    `eNoFilter`, `UA_GENERIC`). Field 8 (enabled, `+0x54`) is 1: stock's climb-wall action is 0 until the airlock monitor switches it on.
  - The squad. luvsic copies a squad from L01 (Introcutscene); the L03 Outro squad is the same shape and is in a level whose cut has a
    player head; `eStayBack` etc. are copied, no member; no object names the SQUAD (as L03), only the rout - `kl_fa.check` still says
    "1 of 24 squads are named by no object" (the source: 1 of 21: the same squad, so its test counts a path prefix as a name).
  - Multiplayer rules. The stock FA level F07 plays mini cuts live (civilians), so the classes load in FA. A player cut in an FA
    round has never run; the `ZFFPlayer` is the same class in Arcade and online (re/netcode_fa.md says online uses other rules
    classes; this step is not for online).

## 4. What was built: `tools/kl_fa_climb2.py`

    python tools/kl_fa_climb2.py spots <folder>           the clip ends and the places
    python tools/kl_fa_climb2.py apply <folder> <out> [--spacing N] [--npcs]
    python tools/kl_fa_climb2.py check <folder> [<source>]  last line: RESULT (kl_fa_climb2): ...
    python tools/kl_fa_climb2.py list                       the other climbs (section 7)

### 4.1 Steps (`apply` on `r_tab\DM03v`, ~20 s)
1. `kl_fa_climb.merge(players only, snd=<the build's .SND>)`: the climb slot lists in Kane and Lynch's sets (+81,368 bytes in the .ANM,
   the only large block that grows; `dyn.json`'s `big_before` is continued as `kl_fa_climb` does).
2. Dead Men's rule walked on the build's collision (`kl_fa_climb.walk`): two stretches, x -3450 .. -2650 and -2475 .. -1950 at the face
   z -625, floor 200, top 403.5 = 203.5 = High, obstacle 49.5 thick. Cut into 3 spots (400, 400, 525 wide).
3. 13 entities under a new top group `KL_Climb!` (3 squads, 3 routs, 3 PosObjects, 3 prompt boxes + the group); the .gms/.buf/.oct/.rmi/.rmc
   rewritten by the same machinery as `kl_fa_cover` (20,737 slot ids renumbered, 2,533 model roots re-pointed in the .prm, size
   unchanged); only .ANM .buf .gms .oct .prm .prp .rmc .rmi differ from the source (19 other members byte-identical).

### 4.2 The prompt box
Centre 67.5 off the face (5 .. 130), 200 high from the floor, width = the spot's width - 10; text ' Climb Wall'; the box is its own use volume.
Where the player looks: `UA_GENERIC` prompt, key = the game's use key (E in our scripts).

### 4.3 The PosObject: no alignment, so the numbers come from the clip (MEASURED, `spots`)
`ZMiniPlayerActTask` (0x8e8d00) puts the player on the PosObject by 0x82cc40 and plays the slot with its own root motion; the hook
form's AlignTo to the measured wall is missing. The GROUND-bone keys (kl_fa_climb.clip_facts):

    Up_High   (3 variants)  root ends 172.0 up, 98.7 .. 101.2 forward, -0.9 sideways; 147.5 up and ~9 forward at event 6
    Up_Medium               118.5 up, 62.4 .. 64.4 forward          Sprint_Low   106 up, 145 .. 152 forward

So the end is S + (rise, forward). The wall is 203.5, the clip rises 172, hence per spot: **start 61.7 off the face** (the end then
lies 10 inside the far edge of the 49.5 thick top) and **36.5 over the floor** (the end lands 5 over the top; he drops 5 when the
(IF collision is switched off for the cut and back on at its end - NOT established) collision returns; ending UNDER the top would put him inside the wall). Predicted end: z -585.5, y 408.5; the check recomputes it
for all three High variants (37.0 / 39.5 past the face, 5.0 over the top, a top surface under the end). Facing: the wall, via
`kl_fa_author.look9` ("a player looks along local -Z", seen live): the PosObject holds `rot9(wall normal)` = `[0 0 -1 | 0 1 0 | -1 0 0]` for
normal (0, -1). luvsic's `stored_rot` would give a heading 90 degrees away; ASSUMED here that the player takes the PosObject's frame the way
the START rows do (0x8e8d2e: `0x857110(node)` then 0x82cc40). **The visible price: he starts 36.5 above the ground, 61.7 from the wall, and
the hands reach the face only at event 6 (the clip is authored for a start at the face).** Tunable at the PosObject (`FAR_MARGIN`,
`END_BIAS`); a second height class would need a clip of the right rise (none: 172 / 118.5 / 106).

### 4.4 Parameters that are GUESSES
`FAR_MARGIN` 10, `END_BIAS` 5, spot width 400, box 5 .. 130 off the face and 200 high, `(blend| 1)`, `(weaponhdl| Holster)` (luvsic's; stock Outro uses
blend 0 for the player), `eStayBack` squad, the prompt text of the co-op wall.

## 5. AI heisters
They cannot use it: `ZPlayerAction` is a player-interaction object (`UA_*` kind, filter by player), a `Lynch` head binds gamedata slot 0, and
a bot is a `ZFFActor`. Their way over the wall is unchanged: the sunk piece `SO0101_M03_Wall_Low_8m_05` (`kl_fa_climb2.check` verifies it
is still sunk) and the drop link. A climb for them needs a navigation link of kind 1 + the NPC clips (`kl_fa_climb apply` without
`--players-only`, `--npcs` here) - not built (re/climb.md 5.1).

## 6. Checks and results (build `y_climb\DM03`)

    kl_fa_climb2 check (own)                  RESULT (kl_fa_climb2): PASS (0 FAIL, 0 NOTE)
      script / PosObject / list / enums, text key in the .LOC, start in the box, rule holds at the face, floor under the start,
      predicted end of all 3 High clips on the top, no prompt holds another spot's start, only the 8 expected members differ,
      large blocks (.prm .fxc .WAV unchanged, .ANM +81,368), HUD fonts + .TEX identical to the source, the sunk wall piece still sunk
    kl_fa_climb check (clips, events, +0x2C)   RESULT (kl_fa_climb): PASS (0 FAIL, 8 NOTE)  [the 8: NPC sets without the slots, no [Climb] section]
    kl_impact                                  problems: 0 in 1 levels
    kl_fa_vaultfx check                        check (vaultfx): PASS
    kl_fa_carfx check                          RESULT PASS: 0 fault(s); 1 place(s) hold such a mesh, 1 off; 10 of 10 vehicles name a fire that holds one
    kl_fa_bots_dyn check                       RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 1 NOTE)  = THE SOURCE'S OWN (r_tab/DM03v gives the same 7 FAIL, 1 NOTE:
                                               the known civilian-money lines of re/bots_loot.md); no new line
    kl_fa check                                0 CRASH lines (the same DEGRADED lines as the source; squads named by no object 1 of 21 -> 1 of 24)
    kl_hud                                     `kl_hud.check(src, dst)` compares a HUD step's input and output (it would call this step's changed members faults);
                                               the equivalent here is in kl_fa_climb2.check: the 8 font chunks and .TEX identical, chunk table 62,892 = 62,892: PASS
    kl_anm.py check / sndcheck                 41 of 41 round trip; 0 of 41 files with a bad +0x2C

## 7. The other climbs our maps want (places only, nothing built)

`python tools/kl_fa_climb2.py list` prints them. In order of value:
1. **The Vault** (M03_A alone, slot F07): the yard wall again (campaign M03_A has `TriggerBox_ClimbWall`, luvsic's list) - the same stretch
   as Withdrawal seen from the campaign file; `kl_fa_climb.LINES` has no entry for the Vault's map; the rule has to be walked on the
   Vault's own collision. The two flights down to the vault lobby need no climb.
2. **Retomoto Tower**: no climb found. The start is the ledge at the blown window (x 5850, y 20996), the campaign had ropes; the lobby
   lifts and the street half are walked. Nothing to build.
3. Hot Coffee (M01): luvsic lists `ColiObj_HeroClimb_01` / `099_TB_ClimbWall` for the warehouse wall and built the overturned
   van -> shelter -> fence climb (-3185, 120, 2160) .. (-3185, 346, 2840); our FA map has not been measured for either.
4. Withdrawal's wall piece `_03` (x -4300 .. -3600): refused by the rule (a hero-only collision object stands over it).
5. Late Night Opening, A Walk in the Park: not looked at.

## 8. Live checks owed (the lead runs them; hook: any TEST hook with klauto.c's rig patch, `[Climb] Enable=0`, no klclimb.c needed)

Script: `scratchpad\runs\Y1_DM03_climb2.ini` (K2d's walk to the wall, then spot 2 at x -2850; `kl_autotest.py 964 --tag Y1_DM03_climb2
--hook <TEST hook> --ini <ini> --shots 120-300:3`). Tree: the owner's tab with `Maps\DM03` = `y_climb\DM03`.

| step | proof (KLHook.log `pos` lines + pictures) |
|---|---|
| Y0 the level loads | scene loaded, `heist stage` lines, no fault; the log has no new `bots:` complaint |
| Y1 the prompt shows | picture while `pos spot2-in-the-prompt-box` (-2850, 200, ~-715): ' Climb Wall' prompt at the bottom of the screen (the stock co-op wall prompt). Not in the log: no hook part reads ZPlayerAction |
| Y2 the cut starts | after the E hold: `pos spot2-cut-running-0.6s` shows y ABOVE 200 and z near -687 (the hover start 236.5 and the climb), then `spot2-cut-running-1.5s` y ~ 350 |
| Y3 he ends on top | `pos spot2-cut-over-3.7s` / `spot2-input-back`: y 403 .. 410, z about -585 .. -575 (predicted -585.5, 408.5), x -2850 +- 2 |
| Y4 input is back | `spot2-input-back` x differs from the one before by the D hold (~ -2850 -> -2830 or so); no 'blocked input' |
| Y5 the foot of the clip | pictures every 3 s: does he start in the air 36.5 up (expected) and do the hands meet the wall (expected only after event 6) |
| Y6 no crash | no fault at the cut's end. (An earlier version of this note said collision comes back "inside the End, 0x447bf2": WITHDRAWN - that address is an unrelated stub; who switches the player's collision for this cut is NOT established, see Y8) |
| Y7 heading | first pictures after the E hold: he must face the wall (+z). A 90 degree error = `look9` against luvsic's `stored_rot` was the wrong choice |
| Y8 collision | `pos` every frame around the face (z -625, y 384 .. 408): a stall or jump at the face = the capsule is still in play (ZMiniPlayerActTask 0x8e8d00 handles collision only for a clip with event id 20; the nine climb clips have none) |
| Y9 weapon back | after the cut the weapon is in his hands again (`weaponhdl Holster` is luvsic's / L03's first-act form; the restore is not read) |
| Y10 hit during the cut | with police shooting (`mode unbreakable`): is he invulnerable or helpless |
| Y11 root motion | WITHOUT `--end-act`: does the clip's root motion move him at all (see the FAIL readings). The variant answers it by a second startpos |

FAIL readings: y stays 200 and E does nothing = no prompt (box / `+0x54` / `+0x7c` / the action not registering: gamedata+0x828 empty?);
prompt shows and E does nothing = the rout did not start (squad not accepting a direct activation, or the `Lynch` head found no player);
he ends at y ~372 or lower = inside the wall (END_BIAS too small / the end model wrong: raise `lift`); at z -571 or beyond = over the
far edge (`back` too small); a fault = read the dump (0x8e8d00 .. 0x8e8fc6 is the task's start).
**Root motion not applied** = after the cut he stays at about y 236 and z -687 (the climb played in place at the hover start): run the variant
`y_climb\DM03_end` (below); if that one ends on top, root motion was the missing part. **Blocked at the face** = he stops at about z -625 (the
capsule is not out of the wall): the collision is not handled by this form, a hook part would be needed (klclimb.c's collision count).

### 8.1 The variant `--end-act` (review MUST 2): `y_climb\DM03_end`
`python tools/kl_fa_climb2.py apply <r_tab\DM03v> <y_climb\DM03_end> --end-act`. Each rout's script gets luvsic's pattern, a SECOND act
(`/Movement/Stand/Normal`, the player's standing idle, `startpos PosObject_Climb_End`), and the rout a second PosObject at the predicted landing
(root end minus `END_BIAS`, i.e. ON the top surface, facing on). So the landing is a teleport at the act change, independent of root motion
(luvsic's own van steps do this). Check: the end PosObject is the predicted landing within 1 cm, on the top, with a top surface under it.
ASSUMED: a second act with an idle clip is harmless (it may snap to the idle pose for a frame; L03 and luvsic have only climbing acts after
the first); if the idle act makes the cut hang, fall back to the plain build. Live order: plain `DM03` first (Y0 .. Y11), then `DM03_end` only
when Y3 fails by 'stays at y 236' (or to compare).

## 9. ASSUMED and not done
- ASSUMED (review S3): three empty `ZSquadScript` squads exist in an FA round; whether any rules code iterates all squads (round-over, spawn) is NOT checked.
- NOT ESTABLISHED (review MUST 1): who turns the player's collision off and on for this cut. NOT SHOWN (MUST 2): that flags 0x20001 / 0x20003 move the player with the ground bone (hence the `--end-act` variant).
- `+0x2C` check (S4) proves only 'a record start of the build's own .SND', not that the sound belongs to the clip.
- ASSUMED: a rout activated by a PlayerAction list starts although its squad is unregistered (L03's wiring does exactly this; FA has not run it);
  the PosObject's frame is the player's frame (look9); the GROUND bone ends where the feet end (the aligned form says "24.5 over the top";
  `END_BIAS` 5 covers a float by dropping); the prompt text and `eBOTH_PLAYERS` pass for an FA human; `(blend| 1)`; a `Lynch`-only script
  needs no `Kane` line when the second player is absent (the L03 climb-wall cut has both because it is co-op).
- NOT done: the Kane head / online; sound for the climb (+0x2C = 0); the NPC climb (kind-1 link); a second height class; the Vault and Hot
  Coffee spots; kl_graft is not changed (its join has the new `snds=` argument available:
  `kl_anmjoin.join(..., snds=(final_snd_bytes, [M['.SND'], kl_anmjoin.stock_snd('F03')]))` at kl_graft.py ~1493, after the final `.SND` is
  known - today's tab builds need it for nothing: 0 bad).
