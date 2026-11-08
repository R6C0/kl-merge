# Reverb path: Audio_ReverbActivater -> ZSynthOpenAL::SetReverb (kl2.exe, offline RE, 2026-11-08)

Static analysis only (capstone disassembly of kl2.exe). Nothing run. GUESS marks every unproven point.

## Addresses
- SetReverb = ZSynthOpenAL vtable 0xb9ac74, slot 48 (offset 0xc0) = 0x5fff30. Chain ZSynthOpenAL : ZSynthWintel : ZSynth3D : ZSynth.
- Per-frame caller: 0x4547b0 (listener update). Ends `mov ecx,[ebp+8]; mov eax,[ecx]; mov edx,[eax+0xc0]; push 0x14f3420; call edx` (0x454974..0x45497f).
  Argument = float[10] block at 0x14f3420. The 1.49 constant (0xb22278) is loaded at 0x4548f8 (default fill).
- Synth ctor 0x736120 (size 0x23c24). synth ptr = [soundsys+0xb11c]; synth+0x23c1c = AL effect id, +0x23c20 = enabled.
- AL param set via alEffectf pointer 0x14f356c; mB to linear 0x927ed0.

## Chain (game thread to audio thread)
1. Audio_ReverbActivater (ClassInfo 0xd07164, vtable 0xbaa9fc). Fields: +0x24 key, +0x30 roomeffect SND offset, +0x34/+0x36 Enter/Leave event ids, +0x38 float priority.
2. Event handler 0x8cfe30 (only caller of Push/Remove): Enter -> AUD::Push 0x765c70 (0x8cfe77), Leave -> AUD::Remove 0x622250 (0x8cfeb1).
   AUD = [[0xdd2640]+0xb00] (vtable 0xb9a3ec). SND offset resolved by 0x54dca0 ([AUD+0x6a7c]+off, bound [AUD+0x6a80], type < 0x19).
3. Reverb stack in AUD: count [AUD+0x68fc], entries AUD+0x680c stride 12 {effectPtr, key, priority float}, max 20, cached top [AUD+0x6900], timestamp [AUD+0x6904]; 0x66 ms debounce against [[0xdd2640]+0x28].
   Getter 0x429b60 (current top).
4. Entry builder 0x812210 (per listener): top present -> effect entry type 2 (or 5); stack empty and not fading -> type 3 (default).
5. Serializer 0x456080: type 2 -> msg 0x70 (0x48-byte copy of roomeffect, case 0x456151); type 3 -> msg 0x71 (case 0x45612b). Batch 0x30 / listener 0x40,0x41 / end 0x31.
6. Audio-thread dispatcher (~0x8e0157, jump table 0x8e05ac, index 0x8e05c8) stores {ptr,type} in synth list (+0x102fc, count +0x10304, entries +0x1030c stride 8). Types: 0x70=2, 0x71=3, 0x42=1, 0x44=7.
7. 0x4547b0 reads the entry, fills float[10] at 0x14f3420 (type 3 -> defaults: decay 1.49, reflections/late -10000 mB, late delay 0.011), calls SetReverb.
Related: listener reverb update 0x7ce160 (needs [AUD+0x6760]) from 0x4a2dbf; gate at 0x4a2d5e `mov eax,[0xcdd93c]; sub eax,1; je ...; call 0x66a220`. 0xcdd93c is 1 in the file image and never written by code.

## Fallback condition (item 3)
The default (type 3, msg 0x71) is sent whenever the AUD reverb stack is empty (count [AUD+0x68fc] == 0 and no fade running) at 0x812210.
The stack is only filled by handler 0x8cfe30 via Push 0x765c70. So defaults every frame means Push never runs, i.e. the activater never receives its Enter event.
Second, weaker cause: 0xcdd93c != 1 skips the update path (unlikely, constant 1 in image).
Why Enter never arrives, even in F09: GUESS. CCheckInside (size 76, vtable 0xba95e4; slots 4 0x4b9b30, 13 0x50c4b0 init, 26 0x805780, 34 0x899d20, 24 0x607a50 enable helper, serialize 0x495690/0x581b10 = bytes +0x4a/+0x4b) tests the object named "MainCamera" (lookup [[0xdd2640]+0xac] vtable+0x7c, fallback [[0xdd2640]+0x970] vtable+0x90(0)). In multiplayer the camera object may not carry that name or the box is never Activated. The per-frame inside test itself was not located.

## Smallest fix (item 4), all GUESS until probed
A. Probe first: with [Echo] Probe=1 log calls to 0x8cfe30 and 0x765c70. If Push never fires on F09, confirms the Enter event is the gap.
B. Feed from klhook (preferred, no game code patch): each frame, when the local hero is inside an authored box, call AUD::Push 0x765c70 (thiscall, this=[[0xdd2640]+0xb00], args effectPtr = [AUD+0x6a7c]+sndOffset, key, priority float; callee pops 0xc) on entry and Remove 0x622250 on exit. Respect the 0x66 ms debounce and max 20 entries.
C. Cheapest: in the existing SetReverb wrapper (klecho.c) overwrite the float[10] at 0x14f3420 with the box's roomeffect values before calling the original (converts mB as the engine does: 0x927ed0 is applied inside the AL setter, so pass the engine's float layout, not AL units; layout of float[10] not fully mapped, GUESS). Needs klhook's own inside-test (box AABB from the authored KL_Reverb! entities).
