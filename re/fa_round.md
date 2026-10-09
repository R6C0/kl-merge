# A grafted map as a real Fragile Alliance round

**LIVE STATUS 2026-10-09 (agent r-live): a real Arcade round runs on the Dead Men bank.** Sections
0 - 4 below were written offline before any run and are kept as written; where a run corrected
them it says so in section 5, which is the part to read first.

Written 2026-10-09 (agent p-round). Offline only: nothing here was run in the game, nothing was
installed. Tools: `tools/kl_fa.py` (the check and the repairs), `klhook/klauto.c` +
`klhook/build_auto.bat` + `klhook/KLHook.round.ini` (the way into a round without a human).
Builds on `re/fa_gamemode.md` (what a round needs), `re/menus.md`, `re/fa_slots.md`, `re/netcode.md`.

Words: **read** = read off the disassembly of kl2.exe (address given) or counted in level files
with the command given; **ASSUMPTION** = fits the evidence, deciding code not read; **not
established** = unknown. "Graft" = F07 systems + a Dead Men map, built by `kl_graft.build` as it
stands today (sound bank merged, Dead Men classes kept).

## 0. Summary

1. Today's test boots with `-o DefaultScene=Locations/F01/F01_Main.gms`. That creates no session:
   the session manager's game mode (`[[0x168e598]+0x5c]`) stays what `ZSessionManagerMultiplayer`
   slot 15 (0x8733e0) left it, and no ini key can make it 4 (section 2). No round, no rules.
2. Both grafts (M03_FA_A the bank, M01_FA_A the diner) have **one CRASH-class fault for a real
   round**: an `OnlineExitLevelTrigger` and no `OnlineEscVehicleMonitor`. The moment a player
   calls the escape vehicle the game reads address 0x48 (0x6276fc). It never showed in the
   direct-boot tests because nobody reaches the exit trigger there. `kl_fa.monitor()` or keeping
   the host level's monitor (`kl_fa.host_keep`) removes it.
3. The other two known traps are already gone in today's converter: the exit trigger's vehicle
   is in field 2 (no hang at 0x6c3f90), the escape camera in field 1, the settings object exists
   and fits (340 fields).
4. What a Dead Men map still lacks as a Dog Days round (all DEGRADED, none fatal by what was
   read): round-start hub (`AIMonitor`), briefing trigger, three speakers, HUD markers, bot crew,
   team / undercover spawn points. The first three are position-free and can be kept from the
   host level with one `Select(s_keep=...)`; built and verified offline for both maps (section 1.3).
5. Route into a round: the menu, driven by `klauto`. Three additions were needed and are in
   `klauto.c`: `CmdDrop` (the Steam launch options are blanked out of the process command line in
   memory, so the game boots into its menu although the options force F01), `msg` (send a GUI
   message to a named element, the way the game's own Accept button does) and `sel` (step the map
   selector to a position). DLL built into scratch, ini ready (section 3).
6. The escape is the untested part of the design: Dead Men's van is a `ZHavokCar` on a spline;
   no stock Dog Days FA level drives a ground car that way.

## 1. The FA layer of the grafted level

### 1.1 What was checked, and the control

`python tools/kl_fa.py check <archive>` reads a built archive (.prp + .gms + .buf, the English
.LOC, the .SND) and tests every requirement of `re/fa_gamemode.md` it can test in files.
Control: `python tools/kl_fa.py stock` over the nine stock levels (F01 from `KL_PortBackup`)
reports **0 CRASH / BROKEN findings**; its only lines are 'squads named by no object' (F08 1 of 23,
F09 2 of 28) and F02's non-zero settings field 158. A check that fired on a stock level was
corrected against it before it was trusted (first run: 10 false alarms - `ZSetZDefine`'s name is
field 1 not 0, a speech trigger's line is its first string TOKEN, F08's container loot has no
`TriggerBox2`, 0..5 settings strings per stock level are no .LOC key).

Built for this report with `kl_graft.build('F07', M, 'F01')`, output folder redirected to scratch
(`<scratchpad>\p-round\build\<M>\`, never the work folder's `build\install`); both `verify:
problems: 0`.

### 1.2 Findings (same for both maps unless marked)

| severity | finding | evidence |
|---|---|---|
| **CRASH** | exit trigger without `OnlineEscVehicleMonitor` | `ZOnlineExitLevelTrigger` slot 34 (0x6c3d50) picks a vehicle and tail-jumps to 0x6276e0 with `ecx = [0x168cc00]` (0x6c3fc5, 0x6c3ff8, 0x6c402b, 0x6c405a). 0x6276e0 handles events 1..4; each case starts `cmp dword [esi+0x48 / 0x4c / ..], 0` with no test of `esi` (0x6276fc). The only other reader, 0x709ba0, tests for null. Writers: the monitor's Init 0x8d2b60 and four clears |
| DEGRADED | escape vehicle is a `ZHavokCar` on a spline (M03 `EscapeSetup!EscapeCars\EscapeCare`, M01 `Escape!EscapeCars\EscapeCar`; 4 `OnlineVehicleOnSpline` each) | the objects are complete and resolve (`OnlineEscHavokCar` fields 0..3, `OnlineEscVehicleController`, `VehicleMoveBehaviourRout` x4, boarding `PlayerAction`), but 0 of 9 stock FA levels use a ground car this way. Its 'Van' animation set is emptied by `kl_graft.dm_rename`. UNTESTED |
| DEGRADED | no `AIMonitor` | nothing hangs on the round-start event (0x8b5f60, event 2; flag bytes at 0x168a200). The Dead Men map starts its squads from boxes instead: M03 squad nodes are named by 9 `TriggerBox`, 6 `TriggerDelay`, 2 `OnlineTriggerBox`, 1 `TriggerCounter`; M01 by 39 `TriggerBox` |
| DEGRADED | no `FAMissionBriefingTrigger`, no `ZSpeakerDriver` / `ZSpeakerTeamCriminals` / `ZSpeakerTeamPolice` | 9 of 9 stock levels have one each. What a missing speaker does to a settings line: not read |
| DEGRADED | no `PointOfInterest` (stock: 2) | no loot / escape marker on the HUD; positional, has to be authored per map |
| DEGRADED | no bot squads (`TriggerLootDepleted` 0, stock 7; no `merc_bot_squad`) | in Arcade the player is alone with the police |
| DEGRADED | no TEAM_MERC / TEAM_POLICE / UCC spawn points | Cops & Robbers and Undercover Cop cannot place players. START 8, AFTER_DEATH 7, TRAITOR 6 are there (both maps). Arcade sets the FA sub-mode `[0x168e59c] = 0` (0x502bee), the value for which the spawn-camera code takes the plain FA branch (0x6c236f) - ASSUMPTION that START / AFTER_DEATH are what it uses |
| DEGRADED | M03: 1 of 15 squads named by no object (`Civilians!Civ_in_02`) | stock has 0..2 such per level |
| NOTE | settings fields 331 / 332 name the escape vehicle's two routs | empty in 9 of 9 stock levels; whether Dog Days' Init still uses them: not established. `kl_fa.settings_lists()` empties them (GUESS that empty is better) |
| NOTE | settings 157 / 158 are non-zero (Dead Men's level music and FA music, re-pointed into the merged bank) | 157 is 0 in 9 of 9 stock levels but Init forwards it (0x88edba -> 0x8ce720). The first place to listen for "its level music plays" |
| NOTE | no `ZSetZDefine` `MercSpawnCam*` | the FA rules' camera lookup tests for null and falls back (0x6c24fb); the second reader 0x8dbc20 was not read |

Present and in Dog Days' form (read from the built archives, `<scratchpad>\p-round\tab.py`):

| | M03 graft | M01 graft | stock F07 |
|---|---|---|---|
| settings object (class `ZOnlineGameplaySettings`, 340 fields) | 1 | 1 | 1 |
| settings strings that are .LOC keys (`K` or `K_C1..9`) | 244 of 246 | 246 of 247 | 239 of 240 |
| `ZSetZDefine 'IsMultiplayerLevel'` | 1 | 1 | 1 |
| `ZFFPlayer` (the host's 16) | 16 | 16 | 16 |
| exit trigger: fields 2..5 | 1 vehicle, resolves | 2 triggers, 1 vehicle | 3 vehicles |
| `OnlineGamePlayTrigger` ENTERS / EXITS / BOARDS | 1 / 2 / 1 | 1 / 3 / 1 | 1 / 1 / 3 |
| loot: CONTAINER + NORMAL objects, value | 22 + 2, 2.43 M | 1 + 5, 1.93 M | 0 + 5, 4.0 M |
| DROP pool (all `ZMONEYCTRL_GAMEMODE_ALL`) | 316 | 300 | 108 + 25 team |
| `LevelBound` | 5 | 3 | 6 |
| `ZSquadScript` (`EGameType`) | 15 eAllTypes | 16 eAllTypes | 21 + 1 UCC + 7 eHeistOnly |
| `TriggerBox` who / modes | 13 ECPS_BOTH / ALL_MODES | 8 ECPS_BOTH / ALL_MODES | mixed |
| enum names unknown to Dog Days | 0 | 0 | 0 |
| objects that do not fit their class | 0 | 0 | 0 |

Differences worth knowing when the round is watched: every Dead Men trigger box is `ECPS_BOTH`
(police players fire them too; Dog Days uses `ECPS_FA_MERCONLY` for the squad starters), no
squad is `eHeistOnly` (Arcade gets no extra waves), there is no TM_ONLY money pool.

### 1.3 Repairs (`tools/kl_fa.py`)

All of them edit the joined scene before it is serialized; none adds an entity, none removes a
controller (so the controller indices `kl_graft` holds stay valid).

| function | what | guesses |
|---|---|---|
| `monitor(sc)` | appends an `OnlineEscVehicleMonitor` controller with nine empty lists and four (-1.0, empty) pairs when the level has an exit trigger and no monitor | host node (stock: a `ZBoxPrimitive` of its own; here the first controller-less box / group of the trigger's subtree, else the trigger's node); empty lists = no 'last vehicle' message, no clean-up when a vehicle is lost |
| `exit_trigger(sc)`, `cam_trigger(sc)` | Dead Men's single string to Dog Days field 2 / field 1 | none (re/pairings.md); no-ops on today's builds, kept as a guard |
| `settings_lists(sc)` | empties settings 331 / 332 | that Dog Days does not need them |
| `host_keep(S)` | names of the host level's position-free FA plumbing, for `Select(s_keep=...)`: F07 -> `Gameplay!AIMonitor`, `Gameplay!EscapeSetup!OnlineEscapeVehicleMonitor`, `FASpecials!FAMissionBriefingTrigger`, `FASpecials!Timer_MissionBriefing`, the three `FASpecials!Speakers!*` | - |
| `prune(sc, names)` | in those kept subtrees, drops list entries and strings that name nothing (the host's map is gone): 13 references for F07 | - |
| `settings_from_host(sc, host, keep)` | the host's settings values except chosen fields; NOT part of `repair()` | which lines the owner wants: Dead Men's (today) or Dog Days' |
| `repair(sc, kept)` | prune + exit_trigger + cam_trigger + monitor + settings_lists | as above |

Proof run (offline): `<scratchpad>\p-round\buildfix.py M` = `kl_graft.build('F07', M, 'F01',
sel=Select(s_keep=host_keep(F07)))` with `repair()` applied to the joined scene (hooked by wrapping
`kl_prpjoin.join`): M03 and M01 both `verify: problems: 0`, 7 more entities, and `kl_fa.check`
then reports 0 CRASH, 0 BROKEN. With the host's objects the round gets: the real monitor on its
own node, the AIMonitor whose list 2 is cut down to `Timer_MissionBriefing` -> the briefing
trigger (so settings 17..20, Dead Men's briefing lines, are asked for 0.5 s after the start),
and the three speakers. Not run in the game.

To put it into `kl_graft.build` (not my file; three lines):
```
kept = kl_fa.host_keep(S.prp)                 # before picks_of
sel = Select(sel.geometry, sel.m_add, sel.m_drop, tuple(sel.s_keep) + tuple(kept), sel.s_drop)
kl_fa.repair(Jn, kept, log)                   # right after the last J.join(...)
```
and in `verify`: `bad += [str(f) for f in kl_fa.check(Jn, out['snd'], <English .LOC>) if f.sev <= kl_fa.BROKEN]`.

### 1.4 What has to be authored, not repaired

- HUD markers: two `ZSTDOBJ` with `PointOfInterest` + `ActivateGameplayTrackerDisplay` at the
  loot and at the van, and the trigger boxes that switch them (F07: `FASpecials!POI!*`, 14 nodes).
- A bot crew for Arcade (F07: `Gameplay!merc_bot_squad!*`), tied to the map's doors and loot.
- TEAM / UCC spawn points and spawn cameras, if those modes are wanted.
- Escape, if the spline car does not work in Dog Days: a baked `ZAnimatedVehicle` van (needs
  animation data, `re/cars.md`) or a helicopter from F02 / F06 / F08 (all its parts are Dog Days').

## 2. No config key starts a round (read)

- `ZSessionManagerMultiplayer` slot 15 (0x8733e0) reads `MPTutor`, `StartAsServer`,
  `StartAsClient` (+0x54 = 3), `StartAsCoop` / `EnableCoop` (0x74b210(1), 0x7d7220),
  `StartAsSinglePlayer` (0x74b210(1), game mode 1). Fields: +0x54 net state (0x74b210), +0x58 net
  mode (0x64e4f0), +0x5c game mode (0x5be510). None writes game mode 4.
- Game mode 4 is written in two places only: the online session create 0x6c9c10 (0x6c9ec4, with
  net mode 3 and the `FASessionCreatingInterlude` page) and the Arcade selector's StartGame
  0x502b40 (0x502bf4, with net mode 1, net state 1, `[0x156b3b8] = 1`, `[0x168e59c] = 0`).
- `MPMap` is read at 0x6c9f0b (online create: replaces the session's map name), 0x491fa1,
  0x6c533d, 0x89fa62 (session state machine: use the stored name instead of the slot table). The
  Arcade starter 0x7e01a0 (whole function read) sets the name from the slot table and never looks
  at `MPMap`. So `MPMap` neither creates a session nor redirects Arcade.
- What Accept does on the Arcade map page: message `StartGame` to the element `HeistLevel`
  -> `ZMercsLevelSelectorHeist` slot 20 (0x49f4e0) -> 0x502b40: refuses when
  `[[0xdd265c]+0x8ad]` is set or the slot is not available (level list vtbl+0x14), else sets the
  session fields above and `[0x156b73a] = 1`; the selector's per-frame slot 8 (0x459e90) copies
  its position to `[0xceceec]` and, seeing 0x156b73a, calls 0x7e01a0: session vtbl+0x68(8),
  vtbl+0x28(slot), map name, 0x725d40 (load).
- The keyboard layout's Accept button on that page is `SendMessage Receiver="PlayLevel"`
  (frontend.xml 2465) - the story page's selector, not `HeistLevel`; only the gamepad layout
  (`PC_GC`, chosen at 0x87e9ea by byte +0xaf68 of the menu manager) sends to `HeistLevel`.
  `ZMercsLevelSelectorHeist`'s own input (slot 10, 0x929360) handles left / right only. How a
  keyboard player's Accept reaches `HeistLevel` is **not established** - which is why the script
  does not press Accept but sends the gamepad layout's message itself.

## 3. The route: menu, driven by klauto

### 3.1 The launch options

The owner's options stay as they are (`-dx10 -o DefaultScene=Locations/F01/F01_Main.gms -o
AutoExit=120`). "-o" lines are parsed after the baked ini text and a later key wins, so `[Engine]`
lines cannot override them. New in klauto: `[Auto] CmdDrop=DefaultScene,AutoExit` blanks those two
"-o" pairs in the process's own command line before any game code runs (DllMain of the statically
imported dinput8.dll). Read: the exe's startup hands WinMain `*MSVCR90._acmdln` (0xa8daaa ->
0x58ff90) and never calls `GetCommandLineA`; its one `GetCommandLineW` (0x866b19) builds a child
process. ASSUMPTION: `_acmdln` is the buffer `GetCommandLineA` returns (klauto also treats a
separate buffer). With the keys gone the baked `DefaultScene=KaneAndLynch.gms` holds and the
game boots into the menu; `[Engine] 1=AutoExit=900` replaces the 120. Steam's settings are not
touched, and with `[Auto] Enable=0` the options act exactly as before.
The other idea - boot straight into F01 and load the frontend afterwards - was dropped: nothing
read gives a safe "go back to the menu" entry.

### 3.2 Files

- DLL: `klhook\build_auto.bat <out>` (klauto.c, which includes klhook.c; `cl /O2 /LD /W3`, no
  warning). Built 2026-10-09 into `<scratchpad>\p-round\klhook_out\dinput8.dll` (171,520 bytes,
  sha1 a9a9444b...), with the ini beside it. NOT installed. Without `[Auto] Enable=1` it behaves
  like today's hook.
- `klhook\KLHook.round.ini` -> `<Dog Days>\KLHook.ini`:

```
[Auto]    Enable=1  Hooks=1  Nodes=0  CmdDrop=DefaultScene,AutoExit  StallMs=180000  MaxRunMs=1200000
[Engine]  1=AutoExit=900   2=DisableSplashScreens
[Script]  waitscene kaneandlynch / wait 8 s
          tap RETURN, wait 2.5 s, tap RETURN, wait 18 s     press-start page, disclaimer (15 s timer)
          tap DOWN, tap RETURN                              main menu: Story -> Arcade Mode
          tap RETURN                                        Arcade page: Start (first entry)
          sel HeistLevel 0xceceec 0                         map selector to position 0 = Subway = F01
          expect 0xceceec 0
          msg HeistLevel StartGame                          what the gamepad layout's Accept sends
          waitload 300000, wait 20 s, five peeks, pass 240000
```
  Key codes: the menu's bindings are in the exe (`MenuInput` 0xb15148): ZW_SELECT = RETURN,
  ZW_CANCEL = ESC, arrows. `ZPressStart` takes action 0x7f or 0x83 (0x418d17); 0x7d / 0x7e are
  left / right (0x929378), so 0x7f = ZW_SELECT by the order of the binding list (ASSUMPTION).
  Its first press may only load the profile and return (0x418d5a-0x418d85), hence two RETURNs
  and a wait that outlasts the disclaimer's own timer either way.

### 3.3 What is assumed, and how the log shows which assumption failed

| in KLHook.log | means |
|---|---|
| `CmdDrop: 2 '-o' pair(s) blanked; command line now: ... -dx10` | the options were found |
| `input: DirectInput8Create wrapped; scene='KaneAndLynch.gms' AutoExit=900` | the game took the edited line. `scene='Locations/F01/...' AutoExit=120` = it did not (the `_acmdln` assumption is wrong): stop, the run is a plain direct boot |
| `LOAD end scene='...KaneAndLynch...'`, `script 1: scene ... is loaded` | frontend up |
| `msg: no GUI element named 'HeistLevel'` repeated, then FAIL `script line 16: HeistLevel did not reach 0` | the keys did not arrive on the map page: wrong default focus on the main menu or the Arcade page (ASSUMPTION: first entry focused), or the press-start page needed more time. Look at the screenshots and change the taps |
| `msg: 'Decrease' -> ZMercsLevelSelectorHeist 'HeistLevel'`, `script 16: HeistLevel is at 0 after N step(s)` | the page opened on the profile's last map and was stepped down |
| `msg: 'StartGame' -> ZMercsLevelSelectorHeist 'HeistLevel' at ... (slot 20 = 0049f4e0)` then `LOAD start scene='Locations/F01/F01_Main...'` | the round is being created the game's own way |
| the same, but no LOAD within 300 s (`script line 20: no such scene load`) | 0x502b40 refused (busy byte +0x8ad, slot 'not available') or a storage dialog is up (0x502c25: only when `[0x1686e71]` is 0) - screenshot |
| `peek 0168e598+ = 00000004 session-game-mode` | a real Arcade session (a direct boot shows another value: the proof that this is a round) |
| `peek 0168c630 = 00000000` / `peek 0168cc00 = 00000000` | no settings object / no monitor was initialised: the level will crash at the first death / at the exit trigger |
| `peek 0168a200 = 00010000` | the round-start event 2 was raised (AIMonitor hub) |
| KLHook.result `state=PASS` | 240 s after the load with no assert / fault; `FAIL` + reason otherwise; the crash lines are klhook's own (`debug/triage.py --keep`) |

Driver: delete `<DD>\KLHook.result`, start through Steam as today (`tools/kl_autotest.py` with a
wait of 1200 s and `--shots`), read `KLHook.result` when the process is gone. Screenshots at
30, 45, 60 s show the menu pages; from the load on every 30 s.
Not exercised anywhere: the `msg` / `sel` / `expect` / `peek` commands (compiled; the ini loads
in the scratch harness: "script: 29 commands"), `CmdDrop` on the real process (its token logic:
5 of 5 cases in the scratch harness `klhook_test\t.c`), and - as before - whether the game polls
the keyboard without focus.

Fallback if the keys never reach the map page: the three button elements have names
(`Button_Heist`, then the page's Start), but what message opens an `OpenWindow` was not read;
record the key sequence once by hand instead.

## 4. First real round: what the owner should look at

Start: Arcade Mode -> first map (it will say Subway and show Subway's picture) -> Accept.

1. **Start**: do you stand at Dead Men's start position with your crew's eight slots, a weapon
   and Dog Days' HUD? Is there a start text / briefing voice (Dead Men's bank or diner briefing)?
   You will be alone: there are no AI heisters yet.
2. **Money counter and round timer** on the HUD running; the objective text (Dead Men's
   'LootMoney' / 'Extract' keys - may be empty).
3. **Police**: do guards / police react and arrive when you walk into the bank / diner (they
   start from Dead Men's trigger boxes)? Do they shoot, take cover, use sensible weapons (two
   Dead Men weapons were replaced by guessed Dog Days ones)?
4. **Loot**: can you open the bank's money boxes (M03: 22 containers) and pick up money (does
   the bag fill, does the counter rise)? Shoot a crew member / get shot: does dropped money appear?
5. **No markers**: there is no loot / escape arrow on the HUD - expected for now.
6. **Escape**: walk to Dead Men's escape point with money. Does the van get called (a voice
   line), drive in along the street, stop, let you board, and drive off? This is the least
   certain part: say exactly where it stops working (never comes / comes but no boarding prompt
   / boards but never leaves / crash).
7. **Death**: let the police kill you. Death camera with a text, then respawn as a police
   officer at a police spawn point, playable?
8. **End of round**: escaped or time up -> round-over screen with the money split, then back to
   the menu or the next round without a crash.
9. **Sound**: map ambience and Dead Men's lines audible; **music** during the round (Dead Men's
   level music may or may not play - note which).
10. Leaving the map area: a warning and a kill outside Dead Men's level bounds.

## 5. Live results (2026-10-09, agent r-live; runs OB1, RN1 - RN6, DB1 in `tools/kl_graft.py`)

Everything here was run in the game. Logs, inis and results of every run:
`<work>\build\klhook\live\<run>.{ini,txt,log,result}`; pictures `<work>\research\shots\<run>_<s>s.png`.

### 5.1 What was wrong with the route of section 3

- The script's first page was never the press-start page. With the ini key `DisableSplashScreens`
  the frontend's start-up code (0x7b0370) takes its 'back from a game' branch (0x7b0422 ->
  0x7b05ed) and opens **MainMenu, then CampaignMenu on top** - no splash, no AttractMode, no
  press-start, no disclaimer. Seen in every run as `windows: 2 [MainMenu > CampaignMenu]`.
- On CampaignMenu the focus is on `ZResumeCheckpoint 'Button_ResumeGame'`. RETURN there opens
  `DifficultyScreen` (0x8f79d2), RETURN on that is `QuickstartCampaign` (0x4789d0: opens
  `QuickStartCampaignWait`, sets the start-pending byte 0x156b73a) = the load of L00. That is the
  whole explanation of RD1 - RD3 ("RETURN, RETURN starts the story").
- The frontend does not read the keyboard for about 22 s after its load ends; the screen is a
  frozen 'Buffering 100%' meanwhile (three byte-identical pictures in OB1). Keys sent then are not
  lost, the script simply does not run (it is stepped from the keyboard poll).
- The screen pictures were not black because of the capture: each took 8 s to encode (a Python
  loop per row), so few were taken and the black ones are the fades at a load. Fixed in
  `kl_autotest.shot` (0.3 s a picture). During a round a full-screen BitBlt does return black now
  and then while the game draws (RN6: 200 - 220 s black, 230 s good, round timer running); `shot`
  now takes a black frame again up to 8 times and then tries PrintWindow. First main-menu picture:
  `shots\OB1_36s.png`.

### 5.2 The route that works (klhook\KLHook.round.ini)

| step | key / command | proof in the log |
|---|---|---|
| frontend up | - | `windows: 2 [MainMenu > CampaignMenu]` |
| back to the main menu | ESC (input code 0x86 -> `ZCloseWindow`) | `windows: 1 [MainMenu]`, focus `ZOpenWindow 'Button_Play' ... +104=CampaignMenu` |
| Story -> Arcade Mode | DOWN | `input: code 0x7b -> ZOpenWindow 'Button_Heist'`, focus `... +9c=Button_HeistMode ... +104=HeistModeMenu` |
| open it | RETURN (code 0x7f) | `window: open 'HeistModeMenu'`, focus on the unnamed `ZOpenWindow ... +9c=Button_StartHeist +104=HeistPlayMenu` |
| Start | RETURN | `windows: 3 [MainMenu > HeistModeMenu > HeistPlayMenu]` |
| map | `sel HeistLevel 0xceceec 0` | `HeistLevel is at 0 after 0 step(s)` (the page opened on Subway) |
| Accept | `msg HeistLevel StartGame` | `msg: 'StartGame' -> ZMercsLevelSelectorHeist 'HeistLevel'`, 0.5 s later the load of `SCENES\Locations\F01\F01_Main.gms` |

One key per step, each followed by `waitwin <window>`; a wrong page ends the run with exit 26
before anything is started. The main-menu order is Story Mode, Arcade Mode, Multiplayer Modes,
Achievements, Options, Quit Game (DOWN cycles through all six and wraps, run OB1).

`msg HeistLevel StartGame` works as section 2 predicted. The storage dialog of 0x502c25 (profile
not loaded, `[0x1686e71]` = 0) did not stop the start.

**Nothing is saved on this route**, by construction: `ZPressStart` (0x418d10) is what sets byte
0x156b742, and the save reader 0x47c5f0 and the save writer 0x6587c0 (`CreateFileA`,
`CREATE_ALWAYS`) both return at once while it is 0. The round's score never reaches the owner's
profile. (It also means the round runs on default options and an empty Arcade high-score list.)

### 5.3 The anti-tamper exit: no code patches in a real session

Runs RN1 - RN4 (klauto with its detours) reached the level through the menu, the level loaded
completely (19,828 nodes, 0 asserts), and the process ended itself 30 - 90 ms after the load:

- `END ExitProcess(2147540653) called from kl2 00794ed8` = `ExitProcess(0x8000dead)`. The call is
  `call ecx` at 0x794ed6 with `ecx = [[0xb46648] + 0xb42c1c]` and the code
  `[0xb42c1c] ^ [0xb685e0]`; the routine (0x794e80) first zeroes 0x800 bytes of its own stack and
  everything above up to the page end, and no call, jump or pointer in the image names it.
- The engine's quit byte (sysif+0x6d, eight writers in the image) was never written: hardware
  write watch in RN3, no hit.
- RN5: the same DLL with `Hooks=0` and no `[Engine]` section (so: no detour, no vtable entry, no
  import slot, no push operand changed; only the DirectInput proxy, memory reads and calls of game
  functions) -> the round starts.
- A direct boot (`-o DefaultScene=...`) with all 13 + 4 detours never ended that way (runs WK1,
  S1 ... F1): the check belongs to the start of a real session.

Not established: where the check is and which of the four kinds of patch it sees (they were
removed together). RULE for every hook we ship (KLHook's slot redirect, the character select
read at 0x835837 / 0x8f5ebd of re/menus.md 7.4): **a patch of kl2.exe's code or import table
kills a real Fragile Alliance / Arcade round** until that check is found. Data the hook may write
(the slot name table at `[0x168f750]+0x16`, option values) was not tested either way.

Also found on the way: Steam's probe at 0xa8e3cb (the 'CRASH c0000005 ... writing address
00000000' line before every scene load) jumps to address 0 when a debug register is set (RN2) -
a hardware breakpoint may only be armed after it, during the load (RN3 survived that).

### 5.4 The round (RN5, RN6: F07 systems + M03_FA_A, klauto with Hooks=0)

Proof of a real session, read 15 s after the load in both runs:

| peek | value |
|---|---|
| `[0x168e598]+0x5c` session game mode | 4 |
| `0x168e59c` FA sub-mode | 0 |
| `0x168c630` settings singleton | set (0x2f2cab00 / 0x6b12d1f0) |
| `0x168cc00` escape-vehicle monitor | set (the host's monitor kept by `kl_fa.host_keep`) |
| `0x168a254` AIMonitor count | 1 |
| `0x168a200` AIMonitor events | 00010000 at 15 s (round-start event 2), 00010001 at 2 min (event 0 too) |

What the pictures show, in order (RN6 unless marked; times are the round clock):

1. **Intro**: 'FRAGILE ALLIANCE ARCADE - ROUND 1', 'Lives left' with three skulls, 'HEIST STARTS IN
   1 SEC!', the player's name and a 'Round score' table (RN5_190s).
2. **Start**: the player stands on the plaza of Dead Men's bank map with Dog Days' HUD: name and
   three lives, 'Total score: $0', 'Round: 1', the round clock counting down from 05:40, an
   assault rifle with 300 rounds and a pistol with 150 (RN5_220s, RN6_190s). The hero differs
   between the two runs (the Arcade body is random, re/menus.md 5) and so does the start place.
3. **Inside**: walking forward for 12 s took the player from the steps into the bank hall.
   'Looting has started. Trust no-one.' comes up at 04:19 (RN6_270s) - Dog Days' own message,
   raised by Dead Men's trigger boxes.
4. **AI**: guards in the hall draw and shoot (a pistol muzzle flash at the right edge of
   RN6_290s, two more figures in the hall), civilians kneel or stand at the counters (RN6_300s).
   The player is hit (red screen from 04:10), goes down at 03:59 with the prompt 'C Get Up' and
   a '$' marker in the middle of the screen.
5. **Death and round end**: 'ROUND 1 - ROUND OVER - All the criminals died - Lives left (two
   skulls) - You didn't escape. You lose a life. - Round score $0 - Continue in: 2' (RN6_300s),
   then the page `HeistStatusLeaderboard`: 'Subway  Round 1', Bonus (Escape, Escaped allies, Loot,
   Time bonus, Kills) / Penalty (Yellow cards, Traitor, Civilian kills), 'Buy Weapons' and
   'Ready' (RN6_310s). The script pressed nothing; the page stayed for the remaining 4.5 minutes.
6. RN6 as a whole: `RESULT PASS`, asserts 0, faults 0, 121,176 input frames.

Against the list of section 4: 1 yes (alone, no briefing text seen in a picture), 2 yes, 3 yes
(they shoot and hit), 4 not tried (no key for it in the script; the '$' marker shows the HUD knows
of loot), 5 a '$' marker did appear, 6 not reached, 7 death and death text yes, respawn as police
not seen (Arcade ends the round when the only criminal dies), 8 yes, 9 not listened to, 10 not tried.

Not seen yet, in the order worth doing: picking up loot (walk to a money box, the pick-up key),
the escape vehicle (the least certain part, section 0 item 6), round 2 after 'Ready', a round
that ends by the clock.

### 5.5 The one fault of the round, and its fix

RN5 (build F1): from the first frame of the round a divide fault at kl2 0x44668b on the sound
thread, again every 0.35 s (the game's own filter resumes the thread). The round went on, slowed
to a crawl by our dump of each one.

- 0x4465f0 sets up a streamed clip; for a record with fmt bit 0x00800000 it calls 0x763a70, which
  takes the top byte of fmt as an interleave group (0x80 | n on the first of n clips, i on the
  i-th follower), steps back `i * 0x48` to the first record and reads the n records' sample rates
  at a stride of 0x48; the lowest then divides.
- Stock Dog Days level `.WHD` files hold no grouped record at all (F07: 21,982 records, 0;
  stock F01: 22,527, 0). Dead Men's hold thousands (M03_FA_A: 5,093 pairs `X.wav` 0x82 +
  `X_R.wav` 0x01 and one triple, stride 0x3c).
- `kl_snd.merge` copied each record a wave names on its own, with fmt unchanged: the merged file
  had 128 grouped records (31 firsts, 97 followers), none standing next to its partner. The first
  to be played is the bank's briefing line (`FA_MissionBriefingBank_02_R.wav`), asked for by the
  kept `FAMissionBriefingTrigger` half a second into the round - which is why no direct boot ever
  showed it.
- Fix: `kl_graft.stream_groups` writes every group one of whose clips was carried again at the
  end of the `.WHD`, records back to back, and points the wave objects at them (M03: 128 torn
  records of 104 groups, 1,144 wave references moved); `broken_groups` is the check. Its proper
  home is `kl_snd.merge` / `kl_whd.Writer` (not r-live's files). RN6 on the rebuilt level: no
  fault. Whether the pairs now SOUND right nobody has heard.

**Since moved (f-live, same day):** the group handling is in `kl_whd.Writer.add_group` +
`kl_snd.merge` now (a clip of a group brings its whole group, records back to back),
`kl_whd.torn_groups` is the check (in `kl_snd.test_merge` and `kl_graft.build`), and the post-pass
is gone. Same 104 groups on M03; `test_merge` 0 problems on F09, M01_FA_A, M03_FA_A; real rounds
on the rebuilt level without the divide fault (RN11, RN12).

## 6. The rest of a round (2026-10-09, agent f-live; runs PX1 - PX3, GT1, RN7 - RN12, EX1 - EX4)

All run in the game. Logs / inis / driver output per run: `<work>\build\klhook\live\<run>.*`,
pictures `<work>\research\shots\<run>_<s>s.png`, helper scripts
`<work>\research\agent_scripts\{f-live_nav,probe,mkini,fa_pos}.py`. Hook: klauto with `Hooks=0`,
no `[Engine]` in every round.

### 6.1 Steering by position

- A ZFFPlayer is found by its vtable (0xbb45f4) in the heap; `+0x460` = world position of the
  feet, `+0xc14` = unit vector pointing back (heading). Found by sampling the process from outside
  (`probe.py`, OpenProcess read-only) while a script walked; a read-only look from outside did
  not disturb a run (PX2, PX3). The local player is the one that moves.
- klauto got a scripted mouse (through the mouse's GetDeviceState; 0.17 degrees a count), `pos`,
  `goto x z [radius] [timeout] [sprint] [keep]`, `onwin <window> <label>` and `[Auto] PosLogMs`
  (top comment of `klhook\klauto.c`). A `goto` holds W and turns by the bearing error; it took
  the player from the start into the hall in 9 s on the first try (GT1).
- Way points come from the level's own navigation mesh (`f-live_nav.py`: polygons, neighbours over
  edges, areas joined where two waypoints share a place - that joining rule is an ASSUMPTION that
  the walks bore out; a vertex is (x, z, y) and its height is the feet's y). The mesh of the bank
  has two parts that nothing joins: A = plaza, bank, garage, yard, staircase (490 polygons),
  B = the streets behind (159). See 6.4.
- Keys, from kl2.exe's default binding text: E = use / pick up / heal, C = cover and 'Get Up',
  LSHIFT sprint. `DebugAlways={KillEnemies=tap(kb,n)}` is in the text too; N did nothing seen.

### 6.2 What works in a round on the bank (F07 systems + M03_FA_A)

| feature | state | evidence |
|---|---|---|
| start, HUD, lives, clock | works | every run; the start place is one of Dead Men's eight (differs per run) |
| loot from a cash drawer | **works** | E held 3.5 - 5 s behind the counter at (-905, 800, -8386): 'Total score: $100,000' (RN7_190s, RN10_210s; RN11 and RN12 used the same hold but no picture of theirs was looked at). 1.5 s was not enough (RN8, RN9: $0). In front of the counter the '$' marker shows but the drawer is 3 units out of reach (GT1_140s) |
| loot from the garage's money boxes | **does not work as scripted** | E held 2 x 3 s at box 11 (612, 230, -6281) and box 10 (476, 233, -6277): score unchanged (RN10). The boxes are `OnlineMoneyContainer` with trigger 'Open' at 80 units and the money inside; the script stood about 100 away in the plane. Not established whether it is reach or the container |
| guards, damage, death | works | the player is down within 10 - 25 s of entering (hall or garage): 'ROUND OVER - All the criminals died - You lose a life' |
| round ends by the clock | **works** | RN10 (test build without `AI_Enemies!*`): clock at 00:10 in RN10_520s, score page in RN10_530s |
| score page, Ready, round 2 | **works** | RETURN on `HeistStatusLeaderboard` = Ready: `FAWaitForPlayers` for an instant, then the next round on the same loaded level - start place, HUD, walking, two skulls left (RN8_240s / 280s; by the log also RN10, RN12). The HUD still says 'Round: 1' in the second round |
| loot kept | as the game rules | the $100,000 is in 'Total score' during the round and the score page says $0 (no escape) |
| escape vehicle | **not reached** | 6.4 |
| level bounds | ASSUMPTION | walking out of the plaza at z -13311 threw the player back and turned him round (PX3, position log only) |
| sound | not heard by anyone | - |

### 6.3 Faults

- **Crash on the score page, once in six times it came up** (RN11; not in RN6, RN7, RN8, RN10,
  RN12 - RN12 is RN11 repeated on the same build and script): read of address 0 at kl2
  0x838922, 0.55 s after the page opened, then a stack overflow because the game's filter resumes
  the fault for ever. 0x8388e0 is `ZLeaderBoardServiceSteam` slot 6, called from
  `ZMercsShowInfoFA` slot 8 (0x5b65b1): it walks `[this+0x31fc]` rows of 0x70 bytes at `this+0x18`
  and calls each row's vtable slot 0; a row's vtable pointer was 0. Cause not established. It is
  the first run on the build with the new sound merge, post filter and baked light, and the same
  build passed the repeat, so the build is not cleared and not convicted.
- **The anti-tamper exit also fires on a direct boot** (PX1): the DLL of the last round
  (`<work>\build\klhook\round2`) with `Hooks=1` on the direct boot ended 2 frames after the load
  with `ExitProcess` from 0x794ed8. The same DLL with `Hooks=0` ran to the end (PX2). Earlier
  direct boots with the detours alone never did; what `Hooks=1` adds since RN4 is the wrappers on
  five import slots. One run each, and PX1 also had the outside probe attached (as PX2 had) - for
  f-tamper.

### 6.4 The escape: where it stands

(Solved since: section 7.3. Nothing opens a gate - the wall is climbed in Dead Men, re/escape.md.)

- `Triggers!ExitTrigger_01` is a box at (408, 396, 460), size 4000 x 400 x 1000 (x, y, z) - whether
  full or half extents, it begins at z >= -540. The boarding trigger of the van is at
  (3252, 133, -20). Both lie in part B of the navigation mesh.
- Everything the player could reach from the bank is part A. The yard behind the garage
  (y 220) is closed: a wall along its whole north side from x -3560 to 2264 (EX1, EX2: seven
  places tried; pictures RN9_230s, RN10_270s), a wall at x 2264 on the east, the staircase corner
  closed at z -2955 on the west (EX3), the garage's east end a wall at x 1734 (EX4_144s).
- Standing in the yard for 4.5 minutes with $100,000 called nothing (RN10): no message, no van.
- What probably opens the way in Dead Men (GUESS): three animated fences
  (`SO0301_USA_animFence_02_FA_*`, `MatPosAnim`, at (2386, 303, -3590), (2386, 399, -4980),
  (2410, 633, -8815)) and the sounds `Doors!MetalGate_Open / _Close`; RN10_270s shows a chain-link
  gate with a ramp behind it. No controller of the built level names those fences by path, so
  what plays them was not found.
  **Next step:** find in Dead Men's M03_FA_A what starts those `MatPosAnim` (an animation event,
  a proxy, a trigger message), and whether the converter or the graft drops it; then the route is
  yard -> gate -> street -> exit box -> van, and the van's spline car is the next unknown.
- A test build without the map's guards: `kl_graft.py build F07 M03_FA_A --m-drop "AI_Enemies!*"`
  (references into the dropped squads are pruned; `verify: problems: 0`). Used for RN9, RN10.

## 7. The escape, the anti-tamper experiments, the own folder (2026-10-09, agent g-live; runs X1 - X3, ESC1 - ESC3, RN13, RN14)

All run in the game, F01 slot. Logs / inis / driver output: `<work>\build\klhook\live\<run>.*`, pictures
`<work>\research\shots\<run>_<s>s.png`, hook DLL `<work>\build\klhook\round5\dinput8.dll` (klauto +
klslot, built by `klhook\build_auto.bat`). First live runs of M02_FA_A / M06_FA_A: re/maps.md section 11.

### 7.1 Anti-tamper experiments of re/antitamper.md section 8 (that file is f-tamper's; outcomes here)

Base of all three: the RN6 configuration (klauto `Hooks=0`, no `[Engine]`, CmdAdd, menu route into an
Arcade round on F07 + M03_FA_A), then 20 s in the round, `pass`. New ini keys of klauto for this:
`EndHooks=1` (the five exit import wrappers without the detours), `Detours=<names>` (only these
detours), `VtLoad=1` (only the vtable entry), script command `rewrite <addr>[+off] <n>` (read n bytes
and write the same bytes back).

| run | the one change | predicted | outcome |
|---|---|---|---|
| X1 | klslot's five file-import wrappers (`[Expansion] Enable=1`, `[Redirect] F01=DM03`, no `[Slots]`, no MountFirst) + klauto's five exit-import wrappers | round starts | **round starts**: `expansion: 5 import(s) of the exe wrapped`, `end hooks: 5 of 5 import slots wrapped`, session game mode 4, HUD and clock (X1_240s), RESULT PASS, no `END ExitProcess`. The import table is not checked |
| X2 | + data writes: the F01 entry of the slot table `[0x168f750]+0x16` (64 bytes, 'Locations/F01/F01_Main') and the netcode global `0xd35420` (0x7d0) written back with their own bytes - in the menu before StartGame, 15 s after the load, and 35 s after it | round starts | **round starts**, RESULT PASS. Data writes are not checked |
| X3 | + ONLY the five detours in unhashed pages (`Detours=NODE,CTRL,SCNBLK,REFFIX,GINIT`; `hooks: 5 of 5 detours installed (mask 00000433)`) | round starts | **round starts**, RESULT PASS; the detours fired (KLHook.result: node=19828 of 19827, last entity named). The page map holds for these five |
| X4 - X9 | controls and later designs | - | not run (each costs four minutes; X1 - X3 were the ones the redirect needs) |

So the 'allowed' half of re/antitamper.md's rule is confirmed live: import wrappers, data writes and
(so far) detours in the unhashed pages survive a real session. The 'forbidden' half (X4 - X6: vtable
entry, hashed `.text`, operand patch) is still only RN1 - RN4, unseparated.
PX1 (the exit on a DIRECT boot with `Hooks=1`) is not explained by the import wrappers: X1 carries all
ten of them through a session. X2 and X3 kept X1's wrappers (the tripwire and the redirect), so each
adds its one change on top of a configuration that had just passed.

### 7.2 The own folder works (live checks 1 and 2 of re/slot_redirect.md section 8)

X2 and X3 were run with **stock F01 copied back into the slot** (from `KL_PortBackup`; sha1 of the
archive a22341b1... equal on both sides, the backup itself untouched) and the bank build only in
`<DD>\KLExpansion\Maps\DM03\` (19 files, a copy of `<work>\build\install\...\F01\F01_Main*`); X2 with `Log=2`:

- the Arcade entry 'Subway' loaded the BANK (X2_220s: plaza, bank front, Dog Days' HUD): the engine
  believes it loads `Locations/F01/F01_Main`, every file comes from the map folder;
- order and API of the opens (read off the log): `CreateFileA Patch01.zip` at boot, before the frontend;
  at the level load `CreateFileA ...\F01\F01_Main.zip`, `FindFirstFileA F01_Main_LS_Default.WHD`,
  `..._LS_Default.WAV`, `F01_Main_LS.SND`, `FindFirstFileA Loader_Sequence.zip` (not in the map folder:
  the stock file is used, as designed), 9 s later `CreateFileA F01_Main.WHD` and `F01_Main.WAV`. Paths are
  absolute with upper-case `SCENES\`. `PC_Def.str` and `PC_Eng.str` are opened once at boot;
- the watcher's slot lines: slots 4 / 7 / 8 (F05, F08, F09) `available=0` at first, all nine
  `available=1` half a second later, after the game itself had opened `F05_Main.zip`, `F08_Main.zip`
  and `F09_Main.zip` - the game's own test, nothing of ours;
- X1 before it had the same redirect with the build ALSO in the slot (same RESULT).

Not done: live checks 3 - 6 (Overlay\Patch01.zip, MountFirst, `[Slots]`, the page option).
`<DD>\KLExpansion\Maps\DM03\` is left in place (360 MB; refreshed to the final build at the end of the session): it
does nothing without `[Expansion] Enable=1` in KLHook.ini and a klslot DLL.

### 7.3 The escape on the bank: reached, called, boarded, round won (ESC3)

g-escape's diagnosis (re/escape.md: Dead Men's players climb the yard wall, Dog Days has no climb) and
repairs are wired into `kl_graft.build` (`escape=True`, CLI `--no-escape`): the wall piece
`SO0101_M03_Wall_Low_8m_05` sunk, its collision cut, reach of the garage boxes 80 -> 125. Two more
faults showed on the way; both are fixed in `kl_fa.repair`:

| run | build | what happened | fix |
|---|---|---|---|
| ESC1 | no guards (`--m-drop "AI_Enemies!*"`), escape repairs | **Garage boxes pay**: 'Total score: $650,000' (drawer 06 + boxes 11 and 10 from the standing places of re/escape.md 6, E held 4 s each). **The wall is open**: yard (y 220) -> (-1580, 150, -535) -> the street. **The van is called** the moment the player is inside `ExitTrigger_01`: Dog Days' own escape HUD comes up (vehicle icon and countdown under the clock, a marker over the van: ESC1_300s, _310s) and the round clock drops to about a minute. Then **crash kl2.exe+0x2a8902**, 18 s after the player stood on the van's stop | `kl_fa.money_people` |
| ESC2 | + money triggers people-only | no crash, loot as before; the van comes, stands beside the player (ESC2_340s), leaves, comes again; **E in the boarding box does nothing**, no prompt; the clock ends the round, score page all $0 (ESC2_385s) | `kl_fa.boarding` |
| ESC3 | + boarding action in stock form | **'You jumped into the getaway car'** (ESC3_315s, with 'Share 50/50 with the pilot' / 'Hold Escape Vehicle' and the van's red countdown), **'ROUND OVER - All surviving criminals escaped. - Lives left: 3 - Round score: $723,625'** (ESC3_325s), score page: Escape $50,000, Loot $650,000, Time bonus 00:45 $23,625 (ESC3_335s), Ready, **'Round: 2'** with the total kept and three lives (ESC3_380s). RESULT clean exit after 386 s, PASS | - |
| RN13 | the FULL build (guards), ESC3's script | the player loots drawer and both boxes and is shot dead in the garage 40 s after entering the bank; score page, Ready, round 2. RESULT clean exit after 329 s, PASS | - |
| RN14 | the full build, the same route without any stop for loot | dead in the garage again, 25 s after entering. RESULT clean exit after 317 s, PASS | - |

**The escape is proven on the no-guards build only.** The scripted player never shoots and never takes
cover; with the map's guards he does not get out of the garage alive (RN13, RN14 and every earlier
round). The full build differs from ESC3's only by `AI_Enemies!*`; that the van, the money triggers and
the boarding behave the same with police around the van is NOT seen. A person has to play that round.

The ESC1 crash (read from the dump, kept as `<work>\build\klhook\live\ESC1_KLHook_3.dmp`): the stack
holds `ZTriggerBox2` -> `ZOnlineMoneyCtrl` (slot 26, 0x6cdb40) -> `ZGameRulesHeist` slot 201 (0x56f6e0)
with the activator a **ZHavokCar** (vtable 0xbcb00c): the van. The trigger was a dropped wallet's
(radius 90, $20,000) at (3003, 0, 40); the van's stop is (2970, 25, 41). ZTriggerBox2's update (0x626ec0)
takes whatever the entity tracker returns within reach unless its byte +0x44 is set; the rules take an
activator that is not a player for an actor and read `[activator+0x2940]` (0x6a88fc). `money_people` sets
TriggerBox2 field [3] = 1 on the 362 money triggers of the level. ASSUMPTION that field [3] is byte
+0x44: one object in the dump, and stock's pooled drop stacks store 1 there. Loot still pays after it
(ESC2, ESC3: $650,000) and no fault came in two more van visits. `kl_fa.check` reports the unrepaired
state as CRASH 'money-trigger' (0 on the nine stock levels).

The boarding: Dead Men's `PlayerAction 'EnterVehicle'` converts to `eONLY_KANE` and bools [10..13] =
0,0,0,0. Of the 31 'EnterVehicle' actions of stock F01..F08 none has eONLY_KANE (24 `eBOTH_PLAYERS`,
7 `eONLY_LYNCH`) and all have [12] = 1. `kl_fa.boarding` writes the most common stock form
(`eBOTH_PLAYERS`, [12] = 1). Both changed in one run: which of the two it was is not separated (kept as
a pair, GUESS). The script tapped E and then held it for 2 s; which of the two boards is not separated either.

What the van does (pictures only; its position is not read): called on entering the exit box; a yellow
icon with a countdown (arriving), a red one (leaving), a marker over it in the world and an arrow at the
screen edge when it is behind the camera; in ESC2 it came and left at least twice in 100 s. So Dead
Men's spline car (`ZHavokCar` + `OnlineVehicleOnSpline`) DRIVES in Dog Days: the item `kl_fa.check`
lists as DEGRADED 'vehicle ... untested' has now been seen.

Route of the steering script (`klhook\KLHook.round.ini` = run ESC3; from the yard on the way points are
re/escape.md's): plaza -> hall -> drawer 06 -> garage -> box 11 at (690, -6190) -> box 10 at
(390, -6130) -> west door -> yard -> (-1590, -790) -> (-1590, -550) the step -> (-1590, -330) in the exit
box -> east along the street -> (3080, -230): inside the boarding box but SOUTH of the van's stop (ESC1
stood on the stop itself).

### 7.4 The score-page crash of RN11 (g-crash's diagnosis, re/crash_scorepage.md) and the feature table

- klauto now does what that file asks, once per boot (`LbFix=1`, default): the row count
  `ZLeaderBoardServiceSteam+0x31fc` is set to 0 while no row is held, and the value found is logged.
  Found in the eight boots of this session: 0, 0, **0x90000003**, **0xffffffff**, 0, 0, 0, 0. So the
  field does hold boot leftovers (g-crash's first reading); both non-zero ones were negative, i.e.
  harmless. No value above 114 came up, so the crash itself was not reproduced; the score page came up
  six times in this session without a fault (M06r, M02r without the fix; ESC2, ESC3, RN13, RN14 with it).
  The shipped hook (klhook.c, not mine) needs the same write.
- klauto's unhandled-exception filter no longer calls wrap_oal's filter from inside itself (the
  'stack overflow' of RN11 was that loop).
- Feature table of 6.2, changed rows: loot from the garage's money boxes **works** ($550,000 from boxes 11 and 10 together, reach 125); escape vehicle **works** (no-guards build); 'Round: 1' in round 2
  was right - it becomes 'Round: 2' after an escape (ESC3_380s), as re/crash_scorepage.md 5 read.
- Still not heard by anyone: any sound.


## 8. The rewritten hook live, the Steam write guard, the join, M01 (2026-10-09, agent i-live; runs BN0 - J3)

Every run: `python tools/kl_autotest.py <wait> --shots ... --tag <T> --hook <dll folder> --ini <ini>`
(new: the tool swaps the hook and the ini in, keeps `<work>/build/klhook/live/<T>.{log,ini,result,txt}`
and puts the ORIGINAL pair back, sha1 checked). Lingering kl2.exe entries: 21 before and 21 after
every run of this section - no run ended in a Windows error report. Hook DLLs: h-hook's
`scratch/hhook/ship` (sha1 37db3ad5), i-hook's `scratch/ihook/test` (b14bbd93) and `ihook/ship` (884a9133).
The inis and helper scripts are in `<work>/research/agent_scripts/i-live/`.

### 8.1 Checks of research/h_shipped-hook.json 'next' and re/hook_live.md

| check | run | build in the slot | outcome |
|---|---|---|---|
| 1 SHIP DLL, three-line ini, direct boot | HK1 | bank | `RESULT: clean exit after 337 s` as with the old hook. Seen: `build: SHIP`, `core: 2 import slot(s) wrapped (ExitProcess yes, SteamAPI_RunCallbacks yes)`, one `Steam's probe ... not dumped` line and no dump, `tick: driven by the game's main loop`, the leaderboard row-count line. **Not as predicted:** (a) the filter lines name `CSERHelper.dll+0x12571` and `wrap_oal.dll+0x491ba` as the previous filter, never `KL2.exe+0x50b780` - the hook's "game's own filter, called after ours" branch was not taken on this boot; (b) there is no `exit: ExitProcess(n)` line: the AutoExit end of a direct boot does not go through the wrapped import; (c) the tick flips between 'fallback thread' and 'main loop' four times in the first two seconds, then stays on the main loop. |
| S0 new TEST DLL, direct boot | S0 | bank | PASS, the same walk as BN1. `steam: import SteamUserStats wrapped ... 9 writes gated`, `CreateFileA yes, CreateFileW yes`, `level archive f01/f01_main.zip ... NOT stock (321104553 bytes ...)`. The `proxy handed out` line does NOT come on a direct boot (the game does not ask for the interface there); it comes at the first score page. `CmdAdd: no room for '-o AutoExit=900'`: with CmdDrop=AutoExit alone the value is 0 and the game never quits by itself - end such scripts with `pass`. |
| 2 / S1 TEST DLL, klhook/KLHook.round.ini, one round | S1 | bank | PASS. Round starts, player dies in the garage, score page, Ready, round 2. `session: state` lines (0x12 0x15 0x16 0x18 0x19 = round runs, 0x1f, 0x20 = score page, 0x23..0x26, 0x16 ...), `steam: the game asked for ISteamUserStats: ... proxy handed out` at the first 0x20, no `INTEGRITY EXIT`, no `patch REFUSED`. **The import slot 0xb107c8 is session-safe.** |
| 3 the same with Hooks=1 | HK3 | Retomoto (guards-wait) | 13 `patch REFUSED` lines, `hooks: 5 of 17 detours installed`, `end hooks: 5 of 5 import slots wrapped`; the round starts and ends at the score page, no integrity exit. |
| S2 the session ENDS (three lost rounds, $0) | S2 | Retomoto | see 8.2. |
| J1 the join, direct boot | J1, J1b | Retomoto --no-ai | see 8.3. |
| J2 the join in a session | J2, J3 | Retomoto --no-ai | see 8.3. |
| 4 SHIP on a faulting build; 5 - 8 overlay / menu page; S3, S4, J3 (stale file) | 8.4 | - | not run in the first pass; see 8.4 (second pass, the 15:16 build). |

### 8.2 The Steam write guard, confirmed (run S2)

Retomoto from the menu, standing still, three rounds lost with $0 (dead 21 - 26 s after each round
began). A watcher (scratch `ilive/watch.py`) would have ended the process at the first round end
had the log lacked the wrapper line or the proxy line; both were there. At the third round end:

```
13:32:48.045 steam: BLOCKED SetStat('NumRoundsPlayed', 1) - TEST build: nothing is written to Steam
... 28 more SetStat lines (NumKilled, TotalLootMoney, HeistTotalPoints_0..8, ExperiencePoints_FA, ...), all with value 0
13:32:48.047 steam: BLOCKED StoreStats() - TEST build: nothing is written to Steam
13:32:48.074 steam: BLOCKED UploadLeaderboardScore(board 'KL2_Heist0_TotalMoney', keep best, score 0) - ...
13:32:48.074 session: state 0x1f -> 0x28 (game mode 4) = SESSION END: ... Steam writes: BLOCKED
13:32:48.365 windows: 1 [HeistStatusLeaderboard_EndGame]
```

No `passed on` line, no fault; the end page shows the totals and a single 'Quit' button (S2_400s.png).
`C:/Steam/appcache/stats/UserGameStats_1165402018_28000.bin`: still 2026-03-13 11:23:16, sha1
00b95332 before and after.
- **What an unguarded session end would have done:** the game sets all 29 stats to ABSOLUTE values
  taken from the profile in memory, and on the klauto route (DisableSplashScreens) no profile is
  loaded: everything but NumRoundsPlayed was 0. Unblocked, the owner's Steam totals would have been
  overwritten with zeros, not just raised. The old rule (never let a session end) was therefore
  more important than re/leaderboard.md thought; with a TEST build of the hook it is now covered.
- The rule for live runs from here: a TEST build whose log shows `steam: import SteamUserStats
  wrapped` may let a session end. The ORIGINAL dinput8.dll (the owner's) has no guard: the owner
  playing through the real menu with a loaded profile is the normal game path on the stock board
  (re/leaderboard.md 4); the SHIP build's policy for that (S3 / S4) is not tested live.

### 8.3 The Retomoto join by the hook (J1, J1b, J2, J3)

- **J1** (box = kl_fa_author.JOIN_BOX as it was, the inside of the tower car): no jump. The car's
  doors are shut; the player pushes at x 2727 for 15 s and never reaches x 2802. The inside box was
  never tested before (RT3's box and RT4's were in front of the car). The run then hung in the
  walk's time-outs until the tool ended it (`RESULT: hung`, 901 s).
- **J1b** (box x 2550..2790, y 19500..19800, z 800..1100 = RT4's): `join: player 0 entered box 9 at
  (2719, 19601, 1100): jump to entry 5 'Specials!JumpPoints!06_Exit' requested`, the next position is
  the lobby car (6207, 570, -6221), then lobby, entrance, square, road, both van stops as in RT4;
  PASS after 349 s. `kl_fa_author.JOIN_BOX` is now this box; the hook's sample file
  `klhook/KLJoin.retomoto.ini` has it too since i-hook's 15:16 pass.
- **J2** (the same through the menu, a real Arcade round): the jump works in a session, `join:
  player 0 is at (6411, 570, -6221) 500 ms after the request`, and the process lived 4.5 minutes
  more with no `INTEGRITY EXIT`. 'Escape area' marker in the lobby (J2_335s.png), the street with
  traffic and a red van (J2_440s.png). On the road the walker lost two minutes at z 2400..3100
  (way points 'NOT reached' ten times; on the direct boot J1b the same way points were passed in
  seconds: something stands there in a round - not identified).
- Two notes for i-hook: the line `join: box 9 NOT usable on this level: entry 5 is past the end of
  the jump list (1 entries ...)` is printed in every run, during the load, when the list has its
  first entry - the box works all the same because it is resolved again on entry; and in J1b the
  '500 ms after the request' line came in the same millisecond as the request with the old position.

### 8.4 Second pass, i-hook's 15:16 build (`scratch/jhook`: SHIP 1972cc1f, TEST 60e345a4; runs X1j - MP1)

The first pass (8.1 - 8.3) was cut off before it could report; the table row "NOT RUN" above is
replaced by these. Lingering entries 21 before and after every run; no `INTEGRITY EXIT` in any.

| check (re/hook_live.md 5) | run | slot | outcome |
|---|---|---|---|
| X1 SHIP build, direct boot, AutoExit | X1j | bank | `RESULT: clean exit after 156 s`. All lines of hook_live.md 4, `fatal-fault filter: the game's own is kl2.exe+0x50b780`, later `installed over 0090B780 (KL2.exe+0x50b780): the game's own`, two `tick: driven by` lines at boot and one at the end, and **`exit: exit(0)`** - AutoExit leaves through MSVCR90 `exit`. S3 on a real SHIP build: `level '...F01_Main.gms': its archive f01\f01_main.zip is not the stock one: 321104553 bytes ... - leaderboard upload BLOCKED, stats and achievements BLOCKED`. One thing for i-hook: the FIRST level line of a direct boot (archive not opened yet) reads `... was not seen being opened - leaderboard upload BLOCKED, stats and achievements allowed`; 0.5 s later the full verdict follows. |
| HK4 SHIP build on a fault | HK4j | bank | The fault was made from outside, 60 s after the game appeared: `CreateRemoteThread` at address 1 (scratch `ilive2/fault.py`; no game memory is written). `FATAL unhandled exception c0000005 at <no module>+0x1`, `dump written: KLHook_1.dmp (unhandled)`, the game's own `kl2_490_crash_2026_10_9T14_30_21C0.mdmp` (210,840 bytes) written, `process ended here with exit code c0000005 (no Windows error report)`, 0 'Application Error' / WER events for kl2 in the event log, lingering 21 -> 21. kl_autotest: `RESULT: crash <no module>+0x1 after 67 s`. A fault on the game's own main thread was not tried (no kept build faults on a direct boot). |
| S4t SHIP policy on a stock level, seen through TEST | S4tb | stock F02 from the menu (entry 1, 'Bridge') | `level archive f02\f02_main.zip ... STOCK (196125170 bytes, directory hash c30281d3)`, `... under the SHIP policy: stock level - leaderboard upload would be allowed, stats and achievements would be allowed`. Round started (state 0x19, game mode 4); ended by `pass` 13 s in. (Run S4t before it hung 10 minutes in the menu: my script lacked the StartGame line - no result.) |
| S5 `[Steam] StockRows=0` | S5 | bank | `steam: BLOCKED FindOrCreateLeaderboard('KL2_Heist0_TotalMoney') ([Steam] StockRows=0 ...)` at the first score page; the page comes up with the round's numbers and NO rows under 'Pos. Name Total Money' (S5_110s.png); RETURN = Ready works, round 2 starts, no fault. Safe to make the default for expansion maps. |
| N0 the new DLL on J2's round | N0, N0b | Retomoto `--no-ai` + KLJoin.ini | `join: level ...: 1 box(es) active; jump list has 6 entries`, `box 9 -> entry 5 'Specials!JumpPoints!06_Exit' at (6272, 563, -6305)`, `player 0 entered box 9 at (2720, 19601, 1099)`, `player 0 is at (6408, 570, -6221) 500 ms after the request` - half a second later, as fixed. No `NOT usable` line. The round: see re/retomoto_fa.md 10. |
| J3 a stale file | J3s | bank + Retomoto's KLJoin.ini | No jump. But also NO `join: box 9 NOT usable` line: only the three `reading / box 9 / 1 box(es)` lines. The bank's jump list never gets an entry, so the 1.5 s 'list complete' test never fires. For i-hook: say it once when the level runs with an empty list. |
| 6 + 7 the expansion's menu page | MP1 | bank; `[Expansion] Enable=1`, `[Redirect.2] F01=DM03`, `[Page.2]`, overlay from `klhook/mkoverlay.py` in `<DD>\KLExpansion\Overlay` (removed after the run) | **Half works.** `expansion: CreateFileA overlay: ...\Patch01.zip -> ...\KLExpansion\Overlay\Patch01.zip`; the Arcade page shows a sixth button 'Dead Men maps' (no icon, it touches the 'Back' button: MP1_36s.png); RETURN on it opens `HeistPlayMenu2` with the headline 'Dead Men maps' and the Subway picture, `expansion: menu page option is 2`. Faults: (a) the 'Location:' row is empty - no 'Withdrawal' text, only the two arrows (MP1_45s.png); (b) **the redirect is lost at the start**: `msg HeistLevel StartGame` -> `expansion: slot F01: menu page 0 from now on -> the stock level`, `expansion: menu page option is 0`, and the archive is opened from `SCENES\Locations\F01` (the slot's 321,104,553-byte bank), not from `Maps\DM03` (321,100,626). The option 'Dummy' is 2 while the page is open and 0 when the slot's archive is opened 5 s later. The hook has to latch the page when `HeistPlayMenu<N>` opens (it logs the 2 there), not read the option at the archive open. Check 5 (byte-copy overlay) and 8 (stock button afterwards) not run. |

Net: SHIP and TEST builds of 15:16 behave as hook_live.md says, except the menu page's latch and
the two log remarks. The leaderboard / stats guard is confirmed in both policies (S2, X1j, S4tb, S5).

### 8.5 kl_autotest.py after this section

`running()` counts only processes with a thread (debug/zombies.py), the lingering count is printed
before and after, a thread-less entry is never given to taskkill, `put()` renames a mapped DLL aside,
`--hook / --ini` swap a hook in and put the owner's pair back (sha1 checked) - all used in every run
above. New here: the notes shown under a result also include `exit: `, `steam: NOT GUARDED`,
`SESSION END`, `join: player`, `NOT usable on this level`. Offline check: scratch
`agent_scripts/i-live/t_autotest.py` (kept logs RT1c .. M02r, made-up lines of the new hook, `put()`
on a DLL mapped by the test itself: 'moved to ...aside_0', new contents in place).
Two things a run can trip over, both seen:
- **The level cache.** The first boot of a build takes 80 - 200 s to the first frame, the next ones
  10 - 25 s (Windows' file cache). Shot times copied from an earlier run then miss everything (N0:
  no picture at all). Take shots from 20 s on every 2 - 3 s and map them by the log's `pos` lines;
  the time of the first shot file gives the tool's start (shot N is written N s after it).
- **Focus.** Run CH0: the level loaded, 4 frames, then the main thread sat in the window message
  wait for 400 s and every shot said 'no window' (KLHook_stall.dmp: 0x87a984 in the main loop).
  Windows' last-input time showed someone or something had used the machine 40 s after the load.
  The same build ran at once afterwards (CH0b). A stalled run with 'no window' shots is not a
  finding about the build.
- klauto's `face` turns the player only while he is moving, and the camera does not follow a
  standing player's heading: stop points have to be approached along the line of sight.

### 8.6 Run list of this section

BN0 BN1 BR1 HK1 S0 S1 J1 J1b S2 M01R GW1 HK3 GW2 J2 J3 (first pass, 12:30 - 14:20); CH0 CH0b
CH0c CH0d CH1d X1j HK4j S4t S4tb S5 N0 N0b J3s MP1 DB4 (second pass, 15:04 - 16:02). Logs, inis and
results: `<work>/build/klhook/live/<run>.*`; pictures `<work>/research/shots/<run>_<s>s.png`; inis
and helper scripts `<work>/research/agent_scripts/i-live/` and `i-live2/`.
End state (DB4, the owner's hook, `RESULT: clean exit after 156 s`, the plaza on screen at 100 s):
F01 slot = `<work>/build/install` (F07 + M03_FA_A with the skeleton rebind, zip sha1 791dbd15),
no KLJoin.ini, dinput8.dll 7e806e6c, KLHook.ini 2ced8e5f, Patch01.zip d367b303 (stock), no
`KLExpansion\Overlay`. Steam's stats cache: 2026-03-13 11:23:16, sha1 00b95332, as before.
