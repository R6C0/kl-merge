# A grafted map as a real Fragile Alliance round

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
