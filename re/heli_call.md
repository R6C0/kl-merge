# What the escape-vehicle call does to a chopper (static proof, 2026-10-17)

Tool: `python debug/heli_call_read.py [--build <heli build dir | _Main.zip>]` (capstone + `tools/kl_exe.py`, 7 s, no game). Prints PASS/FAIL/NOTE lines and one
`RESULT:`. Default build = `<DM>\KL_PortTools\build\club_heli_1017\DM05A\heli` (F01_Main.zip sha1 18b1c8926c36393e0d3123ae57acf90b088c2375, the chain's delivery).
Result on it: `RESULT: PASS`. Nothing installed, nothing launched, no repo tool changed (no `--heli-start-fix` was needed, see the end).
Tests the ASSUMED lines of `re/club_campaign.md` AA step 5 / 6. All addresses are kl2.exe build 0490.

## The chain, read in the exe (all PROVEN)
1. `0x8154f0` (the call; rules slot 44 from the exit trigger, 0x81e570 for the last-vehicle call, KLHook for its fallbacks): needs `[rules+0x1dc]==0`, stores the vehicle ref
   at `[[rules+0x5f8]+0x5c]`, calls rules slot `+0x308` (the escape state) with 1 or 2, clears `[rules+0xe88]`. It sends NO message itself.
2. Escape state 1 in `0x8fa6d0` (state machine): for a kind 1 (ZHavokCar) / 2 (ZHeli) vehicle it sends `ZMOVEMENT_MSG_RESET` (id word 0x168eb14, vtable +0x120 at `0x8fa7c4`) to the
   vehicle entity `[rules+0x1e4]` (resolved by `0x49d170` from the ref stored in step 1; `0x8ccde0`). Kind 3 (ZAnimatedVehicle) sends another message (0x168c7f8).
3. `ZOnlineEscHavokCar` controller handler (vtable +0x68 = `0x5497a0`): on `ZMOVEMENT_MSG_RESET` it posts (vtable +0x124) `SetCompletionTime`, `AITrigger`, `ZMOVEMENT_MSG_RESET` to
   the object at `[ctrl+0x30]` = the controller's FIELD 0 (`Incomming`), then `Show` to `[ctrl+0x3c]` = FIELD 3 (`EscapeChopper_OnMap`). Field 1 (`Escaping`) is handled in the
   `ZMOVEMENT_MSG_GOTO_NEXT_SPLINE` case (0x168c924, `0x549860`), i.e. the way out, not this call.
4. `ZBaseBehaviourRout` handler `0x4ebed0` (`ZHeliFlyBehaviourRout` has the same slot +0x68; its start, vtable +0x88, is `0x80dcd0`): `AITrigger` (id registered at `0x781572`, string
   `0xb73bdc`) with `[rout+0x41]==0` (not blocked) calls the rout's start and sets `[rout+0x40]=1`; `AIBlocker` (`0x781592`, string `0xb7584c`) sets `[rout+0x41]=1`. The sender is not looked at.

## Former ASSUMED items
| item | verdict | evidence |
|---|---|---|
| the call starts the Incomming rout via OnlineEscHavokCar field 0 | PROVEN up to the rout's start routine | steps 1-4; in the built zip field 0 = `EscapeSetup!EscapeChopper\Incomming`, a ZGROUP with `HeliFlyBehaviourRout` + `MsgForward` (-> `HeliNetSync`) and a ZEditorSpline child |
| unhiding does not start the flight | PROVEN, and the converse: the call does not unhide | `Show` goes to field 3 (OnMap box) only; the group is shown by an ActivateGeom (below) |
| Escape_Chopper group ZGEOM[3] = 1 means hidden | PROVEN | over the ZGROUPs of F02, F03, F06, F08, M06_FA_A: 1793 with ZGEOM[3]=1, every one has `.gms` flag 0x400, none without (141 more have the flag with ZGEOM[3]=0) |
| M06's rout-group layout works under the DD car class | PROVEN (layout) / STILL UNKNOWN (flight) | `kl_prpjoin.misfits`: 0 in the 14 nodes of the chopper group; the handler takes any object with a rout. Dog Days' own levels reach the same routs through a `RandomTrigger` + `MsgForward` chain (F02 `random_triggers_incoming_01` -> `_02/_03`, ends in the `Incoming_A..H` HeliFlyBehaviourRout groups); Dead Men's M06 and the club point field 0 straight at the rout group. Both end in `0x4ebed0` |
| the HVK shift is harmless | STILL UNKNOWN | see below |
| the call needs a vehicle state of 0 | PROVEN | `cmp byte [esi+0x1dc],0 / jne` at `0x8154f3` |
| `ZOnlineExitLevelTrigger` scan finds the heli | PROVEN (data) | `otrExitLevel` = `OnlineExitLevelTrigger [0, '', EscapeSetup!EscapeChopper\Escape_Chopper, ...]`, the only one |
| AllyEscapeBox | present | `Gameplay!merc_bot_squad!AllyEscapeBox` (1) |

## The built data (heli build 18b1c892...)
- Exit trigger (node 27120) names the chopper group; field 0/1 rout groups exist and carry a HeliFlyBehaviourRout each; field 2 = `Triggers!BoardingTrigger_Heli`; field 3 exists.
- The group is hidden from the load (ZGEOM[3]=1, flag 0x400). The unhide wire exists: Timer `RivalMercs!DisableVisionBlocker!Timer` (30 s) and `TimerInputAI` (25 s) ->
  ActivateGeom `Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT` -> the group. A `GeomDeactivator` (same family) also names the group (the round-start hide).
  So the chopper is visible from about 30 s and the call only starts the flight; this matches "the 30 s show" of step 3 and refutes any idea that the call shows it.
- HVK: the chopper's non-static placement (type 3, vehicle) sits at the ORIGIN in stock M06_FA_A, F03 and F06 (cm 0,0,0) and at (-59, 9, 96) m in the build (heli_hvk moved it with
  the node). STILL UNKNOWN whether the engine takes the placement as a start pose; stock shows the body is placed by the entity/rout at run time even though the file says origin, so the
  smallest optional change is "skip placements at the origin in heli_hvk" (not made: untestable here, and stock evidence says either way works).

## STILL UNKNOWN (needs a live run)
- What `0x80dcd0` does next (goal object at `[rout+0x74]`, `0x791090`) up to the first movement of the ZHeli, and whether `MsgForward` -> `ZHeliNetSync` (`0x54b210`) matters offline.
- G1 (guess): messages are matched by id and ids are per name (name -> id registry `[0xdd2640]+0xac`, used at `0x78154b`; the static objects of `0x6fb080` register in table `0xdd6728`); the
  id assignment inside `0x5329b0` was not read. G2 (guess): `+0x124` post delivers to the controllers of the target ZGROUP as for stock groups.

## Handover
- Can HELI4 show the flight? Yes if the call happens: the data is wired end to end (call -> RESET -> AITrigger on `Incomming` -> HeliFlyBehaviourRout). What the call needs is a trigger that
  fires: a living non-fed player standing in the exit box (-2900, 1059, 3900), or the last-vehicle fallback (hook v82e keys it to the END timer `[rules+0x200]`). Nothing in the
  data is missing, so no `--heli-start-fix` flag was written; `tools/kl_fa_club.py` is untouched (flag-less hashes cannot change).
- Log lines to look for in KLHook.log: `hud: van card ON ... picture 171` (kind byte 2 = ZHeli) and `van 1+` in the bots lines; `last: ... called as the round's last`.
  If the card lights but nothing flies, the break is after `0x80dcd0` (rout start or the net sync), not in the wiring.
- Re-run the proof after any change to the heli build: `python debug/heli_call_read.py --build <dir>`.
