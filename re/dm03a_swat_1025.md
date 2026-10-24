# DM03A bank: SWAT kick-door squad + gas canisters (2026-10-25, staged, not installed)

Tool `tools/kl_dm03a_swat_1025.py` (md5-pinned input 3d4ae43a = live DM03A with kick doors + extinguishers).
Stage `C:/kl_build_1024/dm03aswat_1025a`: F07_Main.zip 3d4ae43a -> 7852abd9, INSTALL/UNDO bats, tag `.before-1025dm03aswat`
(undo byte-identical on scratch, wrong live md5 and running kl2 refused). check.py, check_passes, own `check`: pass.

- Gas canisters: 3, in the start garage beside the CoverBoxH pillars ((301,-5420), (800,-5390), (700,-5090), floor y 200), donor F07 FX0900 GasCanister_A_02.
  Silent-sound / light-list handling: the donor lights keep no object list (guess); 0 canister sound refs needed zeroing.
- Door squad: Wave_D08 (3 men, the 285 s street reinforcement) is replaced by KL_SWAT!Door_1: 3 men parked at the dead end of the corridor west of KL_Door_1
  (hinge -828,-6041), released by a TriggerDelay2 at 75 s in the AIMonitor start list, 10_Defend -> 20_KickDoor (cloned from F03 Squad#08) -> 30_Defend in the room behind.
  Budget unchanged: 106 actors / 54 squads. Doors 2..5 are on a cut-off nav island: not wired.
- Unproven: an Enemy-team squad using KickDoorBehaviourRout on a grafted door (F03 proof is for its own bots), PosInfo placement, the 75 s timer
  (no alarm node exists), the nav mesh is open through the closed door (cops may just walk through), gas explosion in game, silent-lights guess.

Adversarial verify (2026-10-25): READY. Semantic diff vs live: only Wave_D08 removed, KL_SWAT/KL_Gas added, AIMonitor start list +1 (T_Start), Go_D08 list cut; no existing node moved.
Map facts for the owner: KL_Door_1 is E-W at z -6041 between the N-S corridor strip (x -1010..-910) and the room; the strip ALSO joins the room by an open
60 cm connector at z -6120..-6180, so the door is not the only way (cops may walk round). The parked cells (z -6243/-6283) are 100+ cm south of that connector
behind a wall edge: hidden from the room, visible only from the junction at x < -900. F03's PosInfo sits 26-30 cm from ArrowBack toward ArrowFront; ours is ON the arrow (kept: the offset cell falls off the mesh edge).
