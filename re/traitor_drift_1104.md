# Traitor bot drift online (bs46r DD05: 40 m -> 120-190 m) - 2026-11-04

Research only (read-only on logs and exe). GUESSES are marked GUESS. S = the bot's AI soldier.
Sources: re/attackfromcover_1104.md, re/closein_run_1104.md, re/closein_gates_1104.md, re/bots_escort.md,
klhook/klbrain.c (AfcProbe, RunProbe, HolderSet), klhook/klranges.h, logs of bs46r DD05 and bs47 DM03.

## Verdict
The drift is explained by (a) and (b) together, not by (c).
- The Defend block [S+0x64c] (0x1c bytes: +0..8 xyz, +0xc style, +0x10 given, +0x11 changed, +0x12 queued,
  +0x14 = the soldier, +0x18 scale 1.0) is the anchor for DefendCover (0x84dc90: cover within 500.0 of the
  block, const 0xb3d5e4) and for AFC point paths (modes 1 and 3, when the bot is farther than scale*1000 cm
  from the block and [[[S+0x40]+0x54]+4] != 0). If the block holds a far place, both tactics walk there.
- ZCloseIn (eval 0x6724e0, run 0x76e8c0) writes its own dest into the block (direct branch: dest; cover branch:
  cover position; path-error branch: the bot's own position). The dest is a nav point 550 cm short of the holder
  [S+0xac]. The walk runs to completion (no re-target mid-walk), so a stale holder gives a stale far dest.
- The holder flips: scan 0x767510 (HASHED) has no team test; LosGate hides blocked humans from Sense, so a
  non-human ZSoldier (flags 0x10) wins; HolderSet (0x8bd420, hashed) re-asserts the human, racing the
  1024 ms stock scan.

## Hypotheses

### H-a: the defend place is far from the humans (SUPPORTED, DM03 clearly)
- DM03 AfcProbe: bot walks to a place ~119 m from the human through DefendCover; ddef falls to ~0 while dhum
  rises to 11877 cm.
- Writer of the far place at ~12:00:58-59 UNKNOWN. [S+0x4fc] going 1 -> 0 looks like the signature of an order
  via 0x760e50 (HASHED; sets [S+0x4fc]=0, [S+0x720]=0, snaps the place into the block). Candidates (GUESS):
  hook puppeteer/ledger, Restless, the game's route chain.
- Prove: log block xyz + blk+0x14 each second and an event line on every change (previous place, winner,
  [S+0x4fc]); a change with winner = CloseIn is H-b, with winner none and 4fc 1->0 is an order.
- Disprove: ddef stays > 10 m while the bot moves toward a human, or the block equals the human's position.

### H-b: CloseIn/AFC target is not the human (SUPPORTED, DD05 clearly)
- DD05: CloseIn arm #1 and #7 target the human (dest 526 cm from the human). From arm #8 the dest is 119-168 m
  away; holder shows entities 0x38f / 0x3c0 with flags 0x10 (non-human) alternating with HolderSet's 0x1aa.
  CloseIn commits to the stale dest.
- Prove: at each CloseIn eval and arm log [S+0xac], [S+0xb0], [S+0xa8], their class/flags (+0x10 bit) and
  distance to the nearest human, plus dest-to-human distance.
- Disprove: holder always has human flags at arm time while dest is still far.

### H-c: movement request / path code differs online (DISFAVOURED)
- The bot reaches its dests at ~3.3 m/s, run-task states ([S+0x56c] via 0x5faeb0 / 0x800630) are normal.
- Prove only if a bot with block ~ human and holder = human still does not approach (task state stuck).

## Smallest lever (default off, ini-gated, marked traitor only, no detour in hashed ranges)
L-A: per tick, when blk = [S+0x64c] has blk+0x14 == S and the bot is a marked traitor, if the block place is
> N m (suggest 25) from the nearest human, overwrite block xyz (+0..8) with that human's position (write data
only; hashed 0x412910 is not called). Also set +0x11 changed only if the Defend loop needs it (GUESS: it reads
+0x11 on the next eval; side effects on puppeteer, leash and Restless are unread).
L-B (add if H-b persists): keep the holder human via HolderSet (already in klbrain) while a marked bot is in
Defend, skipping non-human ZSoldiers.
L-C (weak): [S+0x88]=2 so AFC mode 2 anchors on the bot itself; matters only when the bot is > 10 m from the block.
Hooks must sit in free ranges (0x84dc90, 0x76e8c0, 0x6724e0, 0x509f30, 0x4fee00, 0x5faeb0, 0x800630, 0x4a7e60)
or run as a per-tick klbrain data write; never in 0x760e50, 0x412910, 0x85f6c0, 0x7acb30, 0x6e65f0, 0x7f71e0,
0x8602bc, 0x85fa50, 0x85ff6e, 0x5c4360, 0x7b3020, 0x8bd420, 0x767510.

## Probe fields for the next bench
- Block each second: xyz, +0x10, +0x11, +0x12, +0x14 (== S?), and a change event line with previous place,
  winner, [S+0x4fc], [S+0x720].
- [S+0xac], [S+0xb0], [S+0xa8] with class/flags and distance to the nearest human, at every CloseIn eval/arm.
- CloseIn dest vs human distance; [[[S+0x40]+0x54]+4] override word.
- [Bots] OrderTrace=1 ('otrace:' / 'by=GAME?' lines; probably covers KLB/Arcade records only, GUESS).
- arc47 comparison: same probes in the Arcade baseline.

## Who writes the defend block (11-04 13:10)

Static, read-only (kl2.exe via debug/dasm.py, call-site and vtable scans; klhook/klbotfill.c, klbrain.c read). GUESS = not proven.

### All stock writers of [S+0x64c] xyz (every write goes through 0x412910 (block, pos), which mesh-snaps; 20 call sites)
- 0x760e50 (ZSoldier vt+0x13c, call at 0x760f04): the ORDER. Callers: Defend goal 0x686920 (a squad rout's place), DefendPlayerPos 0x622c40 (nearest player; cop squads), the heist rules for crew (0x8fb04c, board place), Loot/Board tactics (GUESS: the stock loot walk is an order), and OUR kle_order2 (below).
- 0x76e8c0 ZCloseIn run: 0x76e908 direct branch = tactic dest [tactic+0x18..] (550 cm short of holder [S+0xac]); 0x76e965 cover branch = cover pos; 0x76e9f7 = the bot's own position (path-error branch).
- 0x5c4360 ZCloseInOnTarget run (list B slot 0x594): 0x5c44bb dest, 0x5c4544 cover pos from the cover table, 0x5c45d6 own position.
- 0x85f6c0 ZDefendPosition loop (the Defend goal): 0x85fa50 cover pos (only when 0x7f6850 true, no holder, body byte [+0x8f1]; 0x7f6850 is FALSE online: role 2/3) and 0x85ff6e own position (after a path error 0x7b0b70).
- Other goals: 0x748d90 and 0x6f4f50 ZFollow (target-relative, mode 3), 0x4ee860 CoveredMoveAct, 0x5a3430 Ambush, 0x4fcd70 AttackInCrowd, 0x4f1660 ReactToHumanShield, 0x6167d0 AttackMountedWeapon, 0x72e960 EvadeDangerPoint, 0x615c90 (ZSoldier slot 16: own position), 0x8ea790 (unknown owner).
- 0x40b540 (ctor, call 0x6ab2a7) makes the block; 0x449cf0 only changes its style byte.
- NOT writers: ZDefendCoverTactic (eval 0x84dc90 only READS via 0x7acb30; no 0x412910 in it), ZAttackFromCover (reads), 0x4be760 ZFollow goal activation (clears [S+0x4fc], no block write).
So a 'drift chg' logged while DefendCover is the winner is NOT DefendCover writing: the writer is the order 0x760e50 (our puppeteer or a game chain), 0x85ff6e / 0x615c90 (own position), or a CloseIn writer from a tactic that ended inside the 1 s sample. GUESS.

### Our own code that writes it (all through klescort.c kle_order2 -> 0x760e50)
klbotfill.c puppeteer: ledger walk to a loot stack (phase 1/4), exit/van walk (phase 2), hold (holdAt), escort side, guard waits, get-up rush (lines 1036, 1362, 1503, 1538, 2279, 2339, 2518); klmove.c Restless / WalkAway / gather (1052, 1493..1791); klhop.c OrderTo / Reorder; klfedkit.c Hunted (857); klqol2.c (189, 220); kladren.c rush; klescort.c Escort. Which skip a marked bot: ONLY the puppeteer loop does (klbotfill.c:2114: klbf_brain_turned -> klbf_nb_drop -> continue). The others were not checked for the NoBoard mark (GUESS: klmove / klhop / klqol2 iterate crew records and may still order it; check with [Bots] OrderTrace=1 in the next bench).

### Why online leaves it far (best explanation, GUESS but consistent with every number)
1. klbf_nb_drop (klbotfill.c:1898) drops the ledger order ONCE (phase 1/4 or 2 -> 0) and then only counts. It never re-orders. The block keeps the LAST ledger place = a loot stack or the van/exit, 100+ m from the humans (DM03 119 m; DD05 example ddef 16285 cm). 0x760e50 snapped that place in with +0x11 = 1 and nothing has overwritten it since.
2. Every anchor then points there: DefendCover (cover within 500.0 of the block, 0x84dd29 / 0x7acb30), the AFC point path when farther than scale*1000 cm (0x807c60), the Defend goal's own wait/leash (0x85f7eb..0x85f850). The bot sits near that place ('ddef' small) far from every human, hence bs48: block > 25 m from every human 89-100% while the holder is the human 89-92%.
3. The only stock writers that move it toward a human are ZCloseIn / ZCloseInOnTarget, each gated and timer limited (eval 0x6724e0: timer re-armed 1-4 s, squad count 0x76ca60 > 1, path gates; re/closein_gates_1104.md). Few wins, few resets; and the cover branch (0x76e965) and path-error branch (0x76e9f7, own position) write cover / own position, not the human. The 'drift chg' events with CloseIn winner (6 of 9 on DD05) fit those branches.
4. Online the soldier never gets the Arcade-only writer 0x85fa50 (0x7f6850 false for roles 2/3), and no Loot / Board / BecomeTraitor tactic exists online (list pushes at 0x6ac04e / 0x6ac085 need 0x7f6850), so no stock tactic RE-ORDERS the marked bot at all.

### What Arcade does (and a warning)
- ZBecomeTraitor run 0x488eb0 writes NOTHING to the block: it only sets crew record +0x79 |= 2 (0x508ef0, 0x7fd930) and calls 0x4322f0. Eval 0x79b7c0 is money based. There is NO traitor refresh: no squad-leader or human-position write exists at the turn.
- In Arcade the block at the turn is the stock Loot / Board tactic's last order (GUESS: a stack or the van, i.e. ALSO not the human). Afterwards the human is reached only through ZCloseIn (dest 550 cm short of the holder, mesh-snapped by 0x412910 at 0x76e908) / ZCloseInOnTarget (0x5c44bb) and AFC mode 2 (centred on the bot itself, 0x807c60), which win there because Board / Loot tactics exist and the holder is stable.
- arc47 only measured 'ddef' (bot to ITS OWN block, 11-12 m): the Arcade bot is near its block; that does NOT say the block is near the human. Nobody has logged block-to-human in Arcade. DriftProbe supports the Arcade offline traitor: run it there (arc48) before calling DefendPull Arcade-faithful.

### Levers, most to least Arcade-faithful (check klranges.h before coding)
1. Fix the stale drop at its cause (ledger side): in klbf_nb_drop, after the one-time drop, issue ONE real order via kle_order2 (-> 0x760e50, soft 0, reset 1; HASHED, calling is fine, no detour) to a place 550 cm short of the nearest living human on the line bot -> human (the stock ZCloseIn dest rule); repeat only when the block is again > 25 m from every human AND the Defend winner is not CloseIn / Board / Loot. This runs 0x412910 (mesh snap), sets +0x11, resets [S+0x720], wakes the Defend goal like any stock Defend step. DefendPull instead stores raw floats: no mesh snap, no +0x11, no [S+0x720] / [S+0x4fc] reset, and the exact human position (DefendCover then looks for cover within 500 cm of a point that may be off-mesh). GUESS: the 78 attempted hits on DM03 came from DefendCover / AFC finding covers near the human; the effect is real, the write is the cheap non-stock variant.
2. Make the stock approach tactics win more (what Arcade relies on): keep the holder the human each host tick (HolderSet, 0x8bd420, hashed, already used) and trace which ZCloseIn gate (P1..P9) returns 0; the dest is then written by 0x76e908 itself. Slower, no block write.
3. DefendPull (shipped, default off) is acceptable as a stopgap. Its target (nearest human) matches DefendPlayerPos (0x622c40 -> 0x7263d0, nearest player slot; stock for cop squads only, never crew) but NOT the Arcade traitor: ZCloseIn / ZCloseInOnTarget aim 550 cm short of the HOLDER [S+0xac] (the scan's pick, normally but not always the nearest), mesh-snapped. If kept: replace the raw store by the stock snap (0x412910 on [S+0x64c], point 550 cm short of the human) and set block+0x11.
4. Verify first (cheap, read only): (a) arc48 = Arcade with DriftProbe: block-to-human distance at the turn and later; (b) OrderTrace=1 on the online bench: do klmove / klhop / klqol2 / klfedkit order the marked bot after the drop ('by=' lines; klescort.c:628 'GAME?' BLOCK-CHANGED lines mark writers that bypass kle_order2: CloseIn, own-position writers); (c) log [S+0x64c] and the last ledger place at the drop to prove point 1 (block == stack / van place right after klbf_nb_drop).
