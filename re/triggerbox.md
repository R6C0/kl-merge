# ZTriggerBox: what the fields do, read from kl2.exe (2026-10-24, scheduled check-in, static)

Read in the staged `kl2.exe` (10,504,344 bytes) with `tools/kl_exe.py` + capstone: the property records of
`ZTriggerBox` (ZPropertyInfo 0xd101a4, record +0x10 = member offset from `this - 4`), the update (vtable slot 25,
`0x42afd0`), the fire (`0x6ae730` -> slot 34 `0x45f5d0`) and the helpers they call. Nothing here was run in the
game; the two live facts it leans on are in `re/retomoto_lift.md` (LIFT10: a human fires the lift box, LIFT11: an AI
heister fires it). Values quoted are the DM09 build `KLExpansion\Maps\DM09\F06_Main.zip` of 2026-10-23.

## Fields (0-based, as `kl_fa.controllers(sc, 'TriggerBox')` lists them) and members

| field | type | member | what the code does with it |
|---|---|---|---|
| 0 | bool | +0x40 | enabled. The one-shot fire writes 0 here (below). |
| 1 | bool | +0x41 | fire the list when the PLAYER count becomes >= field 2 (an 'enter' edge) |
| 2 | int | +0x44 | that count (stock: 1) |
| 3 | bool | +0x48 | fire when the player count falls below it again ('left') |
| 4 / 5 | bool | +0x49 / +0x4a | an actor of team 0 (Mercenary) is inside / the last one left |
| 6 | bool | +0x4b | an actor of team 2 (Ally) is inside |
| 7 / 8 | bool | +0x4c / +0x4d | any other actor (Enemy, Neutral ...) is inside / the last one left |
| 9 | bool | +0x4e | an EnemyVehicle (team 12) is inside |
| 10 | int | +0x50 | **re-arm**: -1 = fires ONCE, 0 = fires on every edge, n > 0 = fires again n s later (details below) |
| 11 | string | +0x54 | not read by the update or the fire (a name for the tracked-object mode?) |
| 12 | refs | +0x58 | tracked objects. Non-empty = a different update (`0x5e15b0`, not read) that uses field 13 |
| 13 | enum | +0x5c | `ETrackGeomSetting` eTGS_AllInside / AllOutside / AllDead - only matters with field 12 |
| 14 | enum | +0x60 | `ECharacterPlayerSelection` ECPS_*: who counts as a player (below) |
| 15 | bool | +0x64 | **local human only** (below) |
| 16 | enum | +0x68 | `EFAMultiPlayerSelection` EFAMPS_*: in which multiplayer modes the box works |
| 17 | refs | +0x38 (ZTriggerBase) | the list the fire sends 'AITrigger' to (`0x45f5d0`: node slot 73 per entry) |

Run-time members: +0x74 = game time (`[0xdd2640]+0x48`, ms) before which the update does nothing; +0x78..+0x7d = the
five 'was inside' flags of the last pass (player, team 0, team 2, other, vehicle); +0x6c = the online sync object (the
fire calls its slot 3 with 0 first: the trigger goes over the network); +0x94 = a mode in which the update walks the
28 player slots `[0xdd265c]+0x828` instead of asking the tracker `0x5891f0` for every object within reach.

## The update, `0x42afd0`, in order

1. Exit if `[this+0x34]` is set, if `[0x1688e74] == 1`, if there is no tracker (`gamedata+0x159c`), or if the game time
   is below +0x74 (the re-arm time).
2. `0x87c980(session)` -> 'multiplayer' byte. Exit if it is set and ECPS is ECPS_NOONE (3).
3. If the session's `+0x5c == 4` (a Fragile Alliance / Arcade session): EFAMPS gate. 7 (ALL_MODES) passes, 0 (NO_MODES)
   exits; `0x7f6850` (Arcade) or sub-mode `[0x168e59c]` 0 want {FA, FA_UCC, FA_TEAM}; sub-mode 1 {UCC, FA_UCC,
   UCC_TEAM}; sub-mode 2 {TEAM, FA_TEAM, UCC_TEAM}.
4. If `0x863a60(session)`: `0x8e6a20(session)` must be 0x19 (the round runs) or the box does nothing.
5. Field 12 non-empty -> `0x5e15b0` (tracked objects; not read here) and return.
6. The census: for every object in reach, skipping those whose node flag bit 10 is set (`[[obj+4]+0x3c]`), those
   `0x806cc0([obj+0x54])` rejects, and those not in the box (`0x8c16c0`):
   - **Arcade rule** (`0x7f6850` true) with ECPS 0 (BOTH) or 4 (FA_MERCONLY): an object of class `0x4ea3b0` (the
     actor class) in team 2 (Ally) counts as a PLAYER when field 15 is 0. That is why an AI heister fired the lift box
     in LIFT11. With field 15 = 1 it falls through to the human test.
   - a human (`0x7aace0`, the player class): ECPS 0 counts him; 1 (LYNCHONLY) wants `0x432a20(player)`; 2 (KANEONLY)
     wants the multiplayer byte and `0x8b60a0(player)`; 4 (FA_MERCONLY) and 5 (RESPAWNONLY) want `[player+0x2723]`
     (police) 0 / not 0 and session `+0x5c == 4`; 6 (UCCONLY) and 9 (MERC_UCC) look at `[player+0x2729]` (the dirty-cop
     byte) / police; 7 (CP_OFFENSE) and 8 (CP_DEFENSE) want police 0 / not 0 and `+0x5c == 5`. A human who passes
     counts when field 15 is 0, or when field 15 is 1 and `[player+0x2720] & 2` (THE LOCAL HUMAN - the same bit
     kladren.c / klcam.c test). So **field 15 = 1 means 'the local player only': no remote human, no AI heister.**
     `re/bank_campaign.md` read it off the census as 'once' / 'for every criminal': both wrong.
   - anything else by team: 0 -> the 'team 0' flag, 2 -> 'team 2', 12 -> 'vehicle', else 'other'.
   The player flag is set when the count of counting players reaches field 2.
7. Edges: each flag is compared with its last-pass byte (+0x78..+0x7c). A flag that became true fires if its 'enter'
   bool is set (fields 1, 4, 6, 7, 9); one that became false fires if its 'left' bool is set (3, 5, 8). The first
   edge that fires ends the pass. (`re/convert_audit.md` 1.1 has the DM / DD member pairing of these bools.)

## The fire, `0x6ae730` -> `0x45f5d0`, and what field 10 means

`0x6ae730`: `[this+0x6c]` slot 3 (0) - the online sync - then slot 34. `0x45f5d0`: for every entry of the ZTriggerBase
list (+0x38) post message `0x1688e70` ('AITrigger') from the owning node (node slot 73). Then field 10:
- **-1**: `[this+0x40] = 0` (field 0 off) and `0x66beb0` = clear bit 0x10 of `[this+0x18]` + `0x55de00`: the controller
  leaves the update list. A ONE-SHOT, dead until something re-enables it (the stock chain does that by message: the
  lift box's own list names `Mercenaries!TriggerBox_1_LeaveElevator`, another -1 box).
- **0**: nothing. The box fires on every edge (an object leaving and re-entering fires it again at once).
- **n > 0**: `+0x74 = now + n * 1024 ms` and the five last-pass bytes are cleared. So after n seconds the next pass
  sees everything inside as 'just entered' and fires again if the count is still met: a re-arm every n seconds while
  someone stands in it, and for every arrival n seconds or more after the last fire. Stock form on DM09: the three
  grafted Dog Days `TriggerBox_RearDoors_Open` (the van doors) use 10 / count 1; the 32 Dead Men boxes use -1.

## What this says about the Retomoto lift doors (owner 2026-10-24 12:28, log read only)

`TriggerBox_OpenExitElevator` (node 7857) is [1, 1, 1, 0 x7, -1, '', [], AllInside, FA_MERCONLY, 0, ALL_MODES, 7 targets]:
centre (2049, 19741, -110), half (100, 150, 1400) = x 1949..2149, z -1510..1290 - the whole width of the corridor into
the lift hall. One-shot, and in Arcade any AI heister counts as a player.
In the owner's DM09 round (KLHook.log 12:25:51 load, PC clock): bot 4 stood at (2166, 19600, 221) at 12:28:30.8, bot 1 at
(2173, 19600, 187) at 12:28:30.9, bot 7 at (2135, 19600, 195) at 12:28:31.3 (hop 2's From lines), all three having
walked there from x -1193..-200 (hop 1 / hop 3 walk orders 12:28:14-20): they crossed the box 12:28:29-31. The owner was
at (1865, 19601, -329) at 12:28:33.6 (escort line) and entered kljoin box 9 at (2595, 19601, 1) at 12:28:37.6. So the box
fired for a BOT 6-8 s before he reached it, with him 25-30 m behind; after that it was disabled (field 10 = -1) and his
own crossing could not fire anything. LIFT10/LIFT13 (doors seen open) are the other order: the human crossed first.
NOT known from the log: whether the leaves played at 12:28:30 and what he saw (no proxy probe in the SHIP hook). Two
readings fit: (a) the doors opened at 12:28:30 and he did not step into the car before walking off (his rides were
cancelled for leaving box 9, 13:18 note); (b) the bot-fired play did not reach the leaves. (b) needs the TEST hook's
`[Probe] DoorProxy=1` in a run where bots lead (the normal case in his games).
A map-side change that removes the ordering question either way: field 10 = 10 on `TriggerBox_OpenExitElevator`, the
stock van-door form. Then the human's own crossing re-fires the proxies even after a bot spent the first shot (at most
once per 10 s). Costs, all re-sent per fire: the leaf clips restart from frame 0 (`re/campaign_fa.md` G1.8: an open door
snaps shut and re-opens in 3 s - unseen if the doors were shut, a blink if they were open), the ding / open sounds play
again, `Enemies!020_Street!Timer` (TriggerDelay 5 s -> Squad_Teargasguys flank) and Last_Stand_02's flank are ordered
again, the lobby lift's `VideoProxy!MatPosAnimProxy` re-plays its 0..75. PROPOSAL only - not built, not installed; it
is one int in the .prp (`kl_fa.edit` on node 7857 ctrl 0 field 10). The alternative, field 15 = 1, would make the box
the LOCAL human's only (bots and remote humans could never open the doors) - wrong for a shared lift.
