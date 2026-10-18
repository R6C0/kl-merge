# Hasta heli-hide: does a direct 0x8154f0 run the monitor's list 4? (static, kl2.exe, 2026-10-18)

Read only. Tools: tools/kl_exe.py, kl_rtp.py, capstone; stock monitors read with kl_fa.load.

## Answer in one line
NO. 0x8154f0 runs the monitor's FIELD 0 list (via rules slot 194 -> 0x709ba0(0)), never field 4. Field 4 is run only by
0x6276e0, whose only four entries are tail-jumps inside ZOnlineExitLevelTrigger slot 34 (0x6c3d50). The hook's direct
calls ('last:' and 'botvan:' in klmove.c) therefore leave the chopper hidden. Recommended fix: option (a), after the
0x8154f0 call make the call 0x6c3d50 would have made, 0x6276e0 (ecx = [0x168cc00], arg = n).

## 1. Evidence

Monitor class: ZOnlineEscVehicleMonitor, vtable 0xbcaa6c (RTTI), 17 units (9 lists f0..f8, then 4 x (float, list)).
Singleton `[0x168cc00]` is written by its slot 13 (Init, 0x8d2b60); a second monitor deletes the first.

Field-to-offset map. The reflection records print offsets 0x34..0x74, but the code uses real offset = record offset + 4,
i.e. field k lives at this+0x38+4k (this is the same +4 the exit trigger shows: klmove.c reads its fields 2..5 at
+0x48..+0x54 while the records say 0x40..0x50). Proof from behaviour, not only from arithmetic:
- 0x790fa0 (list by index 0..4) returns +0x38, +0x3c, +0x40, +0x44, +0x58 = fields 0, 1, 2, 3, 8.
- 0x6276e0 event 1..4 reads +0x48, +0x4c, +0x50, +0x54 = fields 4..7. (re/map_ai.md section 5 part 4 says the same.)
- Stock data fits: F02/F03/F06/F08 field 0 = `MatPosAnimProxy_heli_ladder_up` (runs when the vehicle is CALLED), F07 field 3 =
  `RelayDestroyedEsc_01..03` (vehicle lost), field 8 in all nine levels = `OnScreenMSG_LastEscape*` + `Timer_OSM_LastEscape`.
  No stock level fills fields 4..7.

Who runs which list:
- 0x709ba0(idx) (cdecl, 1 arg): ecx = [0x168cc00], list = 0x790fa0(idx), then for each item
  `entity[+0x24]->vtbl[+0x124](item, word [0x168cc40], 0)`.
- Rules slot 194 = 0x8fa6d0 (vehicle state setter, state byte [rules+0x1dc]); jump table 0x8fb078:
  state 1 -> 0x8fa75f `push 0; call 0x709ba0` (field 0). State 2 (0x8fa758): sets [rules+0x1ee]=1, then the same call
  (field 0 only; the state-2 code of the other rules class at 0x5b14a6 also sends idx 4 = field 8, 0x8fa6d0 does not).
  States 3/4 -> idx 1 (field 1), 5 -> idx 2 (field 2), 6 -> idx 3 (field 3).
- 0x8154f0(rules, vehicle, last) (thiscall, ret 8): gate [rules+0x1dc]==0, stores vehicle at `[[rules+0x5f8]+0x5c]`,
  then `rules->vtbl[0x308/4 = 194](last_flag ? 2 : 1)`. So it reaches slot 194 state 1 or 2 -> 0x709ba0(0) -> field 0.
  It never touches 0x6276e0.
- 0x6276e0 (thiscall, ret 4, `this` = monitor, NOT null-tested): arg 1..4 = n; case n sends the list at this+0x44+4n
  (n=1 -> +0x48 = field 4). Callers: exactly four `jmp 0x6276e0` at 0x6c3fcb, 0x6c3ffe, 0x6c4031, 0x6c406c, all in
  ZOnlineExitLevelTrigger slot 34 (0x6c3d50), each right after `rules->vtbl[0xb0/4 = 44](vehicle, stage)` (0x6cd8e0 ->
  0x8154f0) with ecx = [0x168cc00] and n = which of the trigger's fields 2..5 (+0x48..+0x54) held the vehicle.
  Searched: no other rel32 call/jmp and no 4-byte immediate / vtable / table reference to 0x6276e0 in the file.
  (Indirect calls through a computed pointer cannot be excluded statically; none seen.)

So the monitor list the layer wires (`OnlineEscVehicleMonitor` unit 4 = [van on]) only fires when a player stands in the
exit trigger on a real round (or any caller that goes through slot 34). Both hook paths call 0x8154f0 themselves
and skip slot 34, so the list is skipped. On the `last:` path field 0 runs (empty for Hasta) and, if state 2 came from
[rules+0xe8a], nothing else.

Note: that is the cleaner option for the LAYER too (alternative, GUESS, not needed): also wire `van on` into field 0
(unit 0, runs for every call incl. the hook's) instead of / next to unit 4. Field 0 runs from slot 194 state 1/2 on every path,
and Hasta's field 0 is empty. This needs a layer rebuild and loses nothing; both fields can hold the same list because
the real exit-trigger path would then run it twice, which an ActivateGeom of an already-visible group does nothing
for (0x4c4900 returns when the group is not hidden, see 2c).

## 2. Smallest safe calls from the game thread

### (a) RECOMMENDED: run the monitor's event-n list, exactly as the exit trigger does
- Function 0x6276e0, `void __thiscall (monitor, int n)`, ret 4. monitor = `[0x168cc00]` (singleton, no scan).
  n = 1 + index of the exit trigger field holding the vehicle: klmv_exit_vehicle already loops `k = 0..3` over
  `v[k] = [trig+0x48+4k]`; return k+1 as well (Hasta: chopper in field 2 -> +0x48 -> k=0 -> n=1 -> monitor field 4).
- Call it right after 0x8154f0 (same order as slot 34: vehicle call, then the list).
- Guards (klb_same_code style): `[0x168cc00] != 0` and `klh_rd32([0x168cc00]) == KLH_VA(0xbcaa6c)` (monitor vtable), then head check.
- Head bytes of 0x6276e0 (16): `8b 44 24 04 83 ec 0c 48 56 8b f1 83 f8 03 0f 87`
  `static const BYTE head[16] = { 0x8b,0x44,0x24,0x04,0x83,0xec,0x0c,0x48,0x56,0x8b,0xf1,0x83,0xf8,0x03,0x0f,0x87 };   /* 0x6276e0 */`
- Cast: `((void (__thiscall *)(void *, int))KLH_VA(0x6276e0))(mon, n)` (in a C file without __thiscall use a
  `__fastcall` shim: ecx = mon, edx unused, stack arg n, callee pops 4).
- Effects: for each ref in the list, `monitor_entity->send(ref, AITrigger, 0)` -> the ActivateGeom 'van on' answers.
- Risk: runs only on the game thread like 0x8154f0 (the same frame in klmove). Fired only when the hook's own call fired
  (state was 0 and the game did not call), so the real exit-trigger path cannot have run it already this call: no double fire.
  A second run would be harmless anyway (see c).

### (b) Send one ActivateGeom its message (needs a scan; not recommended)
- ZActivateGeom vtable 0xbc2d4c; message slot 26 = 0x55c9f0, `bool __thiscall (obj, WORD msg, void *unused)`, ret 8.
  It accepts msg == word [obj+0x3a] or word [obj+0x30] (field 0 'AITrigger'; +0x3a is GUESS: an unread word, not identified),
  walks the ref list at [obj+0x34] (iterator: list->vtbl[0x50](&it), list->vtbl[0x60](&it) -> next item or 0), for each item
  `0x8ccde0(item)` -> entity and `[0x168e598]->vtbl[8](entity, 0)` (the unhide, see c), then `[obj+0x3c]->vtbl[3](0)` (its chained list).
- msg to pass: `*(WORD *)KLH_VA(0x168cc40)` (the word every sender uses for 'AITrigger').
- Find the object: vtable scan as klmv_exit_vehicle (vtable 0xbc2d4c at the object start, `[obj+0x24]` = entity with an image
  vtable), then choose the one whose [obj+0x34] list has one item equal to the vehicle value `v[k]`: needs the list iteration
  above; that is more code than (a). Head bytes 0x55c9f0: `66 8b 44 24 04 83 ec 0c 56 8b f1 66 3b 46 3a 74`.

### (c) Unhide the group directly (a last resort, skips the network copy)
- 0x4c4900, `void __stdcall (entity, char flag)`, ret 8. Does nothing when entity null or when
  `((entity[+4]+0x3c) >> 10) & 1` is 0 (not hidden: the .gms flag 0x400 is that bit); otherwise it re-activates the entity
  (flag 0 -> entity->vtbl[0x58], then ->vtbl[0x30] test + 0x73b720, ->vtbl[0x50](1)) and posts word [0x168ee34] to it
  (entity->vtbl[0x130](msg, 0, 0)). Call with flag 0. Head bytes: `56 8b 74 24 08 85 f6 74 71 8b 4e 04 8b 41 3c c1`.
- Entity from the vehicle value: `0x8ccde0(ref)` cdecl (1 arg, caller pops) = `0x796ff0(ref)` with ecx=[0xe0ff90];
  head `8b 44 24 04 8b 0d 90 ff e0 00 50 e8 00 a2 ec ff`. The vehicle value `v[k]` of the exit trigger is that same ref
  (0x8154f0 itself does 0x8ccde0(vehicle)).
- The game's own wrapper for ActivateGeom: scene manager `[0x168e598]` (vtable 0xbd1ebc, set by ctor 0x8c49e0) slot 8 =
  0x7f77b0 `void __thiscall (mgr, entity, char)`, ret 8 = 0x4c4900 plus the network copy through [mgr+0x84] (0x56a9d0). Head:
  `56 57 8b 7c 24 0c 8b f1 85 ff 74 29 53 8b 5c 24`. Hide twin: slot 9 = 0x62de80 -> 0x668160.
- Does it unhide the chopper completely? GUESS: Hasta's HELI_HIDE sets both ZGEOM[3]=1 (a .prp property read by the group) and
  the .gms flag 0x400; 0x4c4900 only reads/handles the .gms flag side. Whether the group's own ZGEOM[3] hidden state is also
  cleared by the activate virtual (vtbl[0x58]) is NOT proven. The ActivateGeom path (a/b) is what Last Call uses live, so prefer (a).

## 3. Recommendation
Option (a). Change `klmv_exit_vehicle` to also return the field number n (k+1), and after the 0x8154f0 call in the
`last:` fallback and in `botvan:` call 0x6276e0 on `[0x168cc00]`. Guard with the monitor's vtable (0xbcaa6c) and the
head bytes above. NOT RUN IN GAME. Unproven: that event n of the hook's chosen field matches the layer's wire for
every build (Hasta puts the chopper in exit field 2, so n=1 -> monitor field 4, matches HELI_HIDE's `put_(mons[0], f4=...)`).
