# Player crouch->run snap: static findings (2026-10-24, research only)

Method: linear disassembly of kl2.exe (scratchpad), debug/dasm.py, string sweeps of both exes.
Items marked GUESS are not verified by reading or by a live run.

## What is established
- BaseMove 0x7a43e0 commits a gait change after a 1-frame debounce (0xce977c=1, 0x7a4826..0x7a4852),
  then calls selector 0x5abbb0 (0x7a485b), 0x420740 (0x7a4860), phase stepper 0x757a50 (0x7a4869).
  0x5abbb0 writes [esi+0x1e5c] then [esi+0x58] at 0x5ac802 and sets [esi+0x1eac]=1. These three are
  direct-call only (no vtable refs), caller is 0x7a43e0 alone.
- [+0x58] (the "current locomotion clip") is consumed for MOVEMENT PHASE and ROOT MOTION (0x59d990
  advance, 0x5dad60 clip-end test, 0x720ef0 -> 0x5a5030 root sample via player vtable +0x260), not
  by a Play call right there. So changing the clip id alone does not show a pose; the visible pose
  comes from a separate Play through the animation channel mixer. The exact caller that plays the
  visible locomotion clip was NOT pinned down (GUESS: the animation-update vtable +0x2e8 / 0x50ac80
  path or the 0x77ed80 decision code, which keeps the old clip until 0x5dad60 says it ended).
- Mixer DOES support crossfade (verified in code, see re/climb.md ~341-358): 16 channels x 0x38 bytes,
  each with fade duration (+0x3c in the pool), timer (+0x40), weight; 0x50ac80 steps weights; fade-in
  length = clip record +0x14 (blend time, /1024); state 4 = fade-out. Play = vtable +0x200 = 0x4da1d0
  (thiscall; args clip, flags, startFrame, endFrame(-1 sentinel 0xb3e980), speed). Flag bit0 stops
  same-body-class channels (hard cut), bit1 = snap (no fade). A snap is therefore a flag/blend-time
  matter, not a missing capability.
- ZFFPlayer has no Crouch_To_Run transition clip path. ZFFActor (AI) does: table 0x45cc08 with
  Crouch_To_Run ids, played as a one-shot before the loop (that is how AI gets a "transition"),
  not a crossfade.
- 0x78d9d0 (anim-name table) only registers /Movement/Stand|Crouch + Transitions/Crouch_To_Stand,
  Stand_To_Crouch for the player-side set; no Crouch_To_Run there.

## Dead Men comparison (string sweep of both exes)
Name strings are in both exes (the clips themselves live in the anim banks, so a string proves a
name is registered, not that the player uses it).
- DM only (dropped by DD): /Cover/Crouch/Transition_{,Left_,Out_,Left_Out_}{Crouch_To_Stand,Stand_To_Crouch},
  /Movement/Transitions/Crouch_To_Sneak{,_Backwards,_Left,_Right}, Sneak_To_Crouch kept in both.
- DD only: Run_To_Crouch{,_Back,_Left,_Right}.
- Both: Crouch_To_Run{,_Back,_Left,_Right}, Crouch_To_Walk, Crouch_To_Sprint, Stand_To_Run*, Run_To_Stand*.
  So the transition clips exist in the data set; the player gait code simply does not play them
  (ZFFPlayer path), as in DM as far as the name table shows (GUESS: DM player behaves the same;
  not checked in DM code).

## Verdict
Feasible in principle, moderate risk, not testable statically. Confidence ~50%.

## Best hook plan (all GUESS until verified live with a Dry/log mode)
A. Cheapest: find the Play call that starts the new looping locomotion clip on the commit frame
   (log callers of 0x4da1d0 for ZFFPlayer on a crouch->run toggle, using klhook), then make that
   call carry flags without bit1 (snap) and ensure [clip+0x14] > 0 or write the channel's fade
   duration (+0x3c) and timer (+0x40) right after Play returns (thiscall on the player, channel
   index from the return). Old channel keeps playing and fades via state 4 only if flag bit0 does
   not stop it; otherwise leave the old channel alive by clearing bit0 for locomotion class.
B. Alternative: on commit (hook 0x7a4826..0x7a4852 or the write at 0x5ac802) call Play on the
   Crouch_To_Run transition clip through the AI-style path. Higher risk: root-motion/phase code
   (0x757a50, 0x5dad60) assumes [+0x58] is the looping clip.
C. Do NOT change [+0x58] timing or the debounce: phase/root-motion consumers depend on it.
Risks: locomotion class stop flag, root motion sampled from two blended channels (0x5a5030 may
read only one), 16-channel pool exhaustion, network/AI sharing of the same Play site.

## Next step (needs a live run, owner approval)
Log every 0x4da1d0 call (this, clip, flags) around a crouch->run toggle with the hook in log-only mode.
