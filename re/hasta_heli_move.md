# Hasta chopper does not move (run N1018_L3_DM11B_hide) - cross-check of two static investigations (2026-10-18)

Static only. Not run in game. Nothing else in the repo or the Dog Days folder was touched.
Checked against: re/hasta_list4.md, re/heli_call.md (incl. the 2026-10-18 c4 handover), re/open_work_log.md,
tools/kl_fa_hasta.py / kl_fa_hasta_heli.py (--heli-hide), klhook/klheliprobe.c.

## Verdict on the two reports
Both agree on the load-bearing points; I re-verified three:
1. ref1e4 = the Escape_Chopper ZGROUP, not the ZHeli. Consistent with live `kind=2` ([rules+0x1ec], "a ZHeli child found
   under that group") and with different vtables in the probe line. ACCEPTED.
2. In the hide build the direct hook calls (`last:` / `botvan:`, 0x8154f0 -> rules slot 194 -> 0x709ba0(0)) run only the
   monitor's FIELD 0; the 'van on' ActivateGeom is wired into FIELD 4, which only ZOnlineExitLevelTrigger slot 34
   (0x6276e0) runs (re/hasta_list4.md, four tail-jumps, searched whole exe). ACCEPTED. So in the hide build nothing ever
   unhides the chopper on that path. This alone explains "ZHeli never moved" in THAT build.
3. States 1 -> 3 -> 5 are open-loop timers; reaching 5 proves nothing about movement. ACCEPTED. And `rout=0`/`goal=0` is
   the probe's default when nothing is found: the probe scans the entity table only, the rout is a run-time object
   (heli_call.md handover). So those fields measure nothing. ACCEPTED.

Rejected / corrected:
- Report 1 says "Last Call's chopper never fired" as a settled fact and lists it as difference 2; the task's premise
  ("DID come in live in earlier runs") is also wrong. Neither is supported: the log (HELI4, 00:40 note) first read "the call
  never reached the rout", and c4's handover then withdrew that reading (nobody stood in the exit box; probe blind).
  Correct statement: NO map's grafted chopper (Last Call, Hasta) has been seen flying live. Only Park's M06 whole-map
  chopper has. Do not use Last Call as evidence that the unhidden wiring works.
- Report 2's GUESS that hide makes the member scan / goal build skip the heli is possible but unproven; a hidden
  group may well still run the rout. Report 1's "hide is the only thing keeping it still" is likewise too strong: the
  position was also unchanged for the whole round, but without a rout observation this cannot separate "hidden" from
  "rout never started".

## (a) Most likely root cause
Two stacked causes, the first certain for the hide build:
1. (confidence 85 % for this run) The hide build leaves the chopper hidden (ZGEOM[3]=1, .gms 0x400) and the only unhide
   (monitor field 4) is not reached by the hook's direct call. The ZHeli stays at its load pose. This is a wiring gap in the
   hide design, not a flight bug.
2. (unknown, 40-50 % that it also matters) Even unhidden, the rout may never produce movement: runtime preconditions
   of 0x791090 / 0x7f6750 on the actor (`[actor+0xbc]==0`, `[actor+0x8c]`/`[0x90]` non-null, squad `[rout+0x38]`) are
   unseen, and the start pose (rigid shift of the M06 chopper, HVK placement) is unproven. The base fed_e5 has not
   been observed flying either.
ref1e4 being the group is correct and harmless; it is not a cause.
The ~16 km distance (ZHeli 36682,5061,37004 vs box 27500,220,23250) is the pose of the chopper at the spline start and
is not itself a cause; check only that the Incomming spline's last point lands at the pad (kl_fa_hasta_heli PAD (27500,0,22800)
is a GUESS).

## (b) Fix
Hook (klhook/klmove.c is e5's file; propose, do not edit): after the direct `0x8154f0` call, also call
`0x6276e0` with `ecx=[0x168cc00]`, `n = k+1` (k = index of the exit-trigger field holding the chopper; Hasta n=1),
guarded by `klh_rd32(mon)==KLH_VA(0xbcaa6c)` and the 16 head bytes in hasta_list4.md. Same frame, same thread. This is
hasta_list4.md option (a) and the recommended fix.

Build tool alternative (no hook change), NEW flag only, default byte-identical:
- tools/kl_fa_hasta.py + tools/kl_fa_hasta_heli.py: add `--heli-hide-f0` (requires `--heli-hide`). Put the same
  'van on' ActivateGeom reference list that check_hide() (kl_fa_hasta_heli.py ~line 149) validates in monitor list 4
  ALSO into monitor field 0 (OnlineEscVehicleMonitor unit 0, empty for Hasta). Field 0 runs on every call path. Re-running
  an ActivateGeom on an already visible group is a no-op (0x4c4900 returns). Extend check_hide to require both lists
  name the same single ActivateGeom. GUESS: that the monitor's field 0 is run before the rout starts; if the unhide
  is ordered after the AITrigger, the first rout tick may see a hidden heli. Mitigation: prefer the hook fix.
Without either fix, the pragmatic control is to build WITHOUT `--heli-hide` (see (c) step 1).

## (c) What 3f should look for next run
Run order (each is one run, same Probe=2 hook):
1. Control: fed_e5 / `--heli-escape` WITHOUT `--heli-hide` first. This is the decisive run; the hide build cannot
   tell us anything about flight until the hide is out of the way.
2. Probe=2 (heap scan) so the rout is found. In `grep "heli: t=" KLHook.log | grep CHANGE` read, in order:
   `rout=` non-zero; `started=1` after the call; `goal=` non-zero and `goal8` in {0,4}; `sq=` non-zero with `a8c`/`a90`
   non-zero; `a_bc=0` then `a154=` set (goal stored). Then `zheli pos` must change within seconds. Verdict table:
   no `rout` even with Probe=2 -> rout is not a heap object of that vtable; `started=0` after the call -> AITrigger/RESET
   never reached the rout; `started=1,goal=0` -> init 0x815aa0 failed; `sq=0` or `a8c=a90=0` -> no squad member (the
   0x7f6750 store is skipped); all set but pos fixed -> body-movement/pose problem (HVK placement, `--heli-hvk-origin`).
3. Is ref1e4 the ZHeli? It is not; verify by: `ref1e4` equals the address of the Escape_Chopper ZGROUP (node 12020 in the
   entity table; its vtable is the ZGROUP vtable), `kind=2`, and the ZHeli (`zheli=`) has `[zheli+parent]`/scene
   parent equal to ref1e4. If ref1e4 == zheli literally, my reading is wrong (then vt= and zheli vt= would be equal).
   Add to the probe line: the ZHeli's hidden bit (node flag 0x400 and the ZGEOM visible byte), logged on CHANGE, so the
   unhide moment is visible.
4. Hide build only: after applying the hook fix, the line where the hidden bit flips must come within a frame of the
   `last:` call; if the flip never appears, the 0x6276e0 call was not reached.

## (d) Is the hide build a safe base for Hasta E4?
No, not as it stands. With the hook's direct path (which is what bots and the scripted run use) the chopper never appears,
so the escape would show a vehicle icon and ESCAPE AREA with no vehicle. It is safe only together with the 0x6276e0 hook
call (or the `--heli-hide-f0` flag) AND after the unhidden control run proves the rout flies. Until then use fed_e5 (no hide)
as the E4 base and keep hide as an optional layer. The hide itself is data-clean (ZGEOM[3], .gms flag, check_hide passes),
so nothing in it blocks E4 except the missing unhide.
