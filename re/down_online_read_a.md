# Down online, static read A (GET UP input and FALL/RISE replication)

Static read only (2026-10-26). Nothing run. Labels: VERIFIED = read in the disassembly, GUESS, UNKNOWN.

## Q1 [D+0x2b] / [D+0x21]

| Item | Site | What | Verdict |
|---|---|---|---|
| [D+0x2b] writer | 0x84dda0 (called from slot 12 = 0x808720, via Wintel 0x8a4fa0) | writes it from [H+0x2d3] (TapCover), only while [D+8]&1; zeroes [pl+0xeb4] | VERIFIED |
| [D+0x2b] reader | 0x47cd80 does NOT read it directly: it asks 0x50a8f0 (user-action-pressed test, [pl+0xcfc] vs action 0xc/0xd, switch on [pl+0xd04]) | the press test; also a [D+0x29] auto path | VERIFIED |
| [D+0x21] writers | 0x47cd80 (get up asked), 0x6cd720 replica branch (0x6cd7e5..f5), kldown (1027, 1035, 1161; take-backs 2241, 2270) | | VERIFIED |
| 0x47cd80 sole starter? | the only starter reached from D's frame 0x724420; 0x7180b0 / 0x8b74d0 are the senders | | VERIFIED (callers beyond 0x724420 not exhaustively listed: GUESS) |

## Q2 Order, and hiding the press

| Item | Finding | Verdict |
|---|---|---|
| Hook tick | end of main-loop frame (wrapped RunCallbacks from 0x87a930), after update and render | VERIFIED |
| Input slot 12 vs 0x47cd80 in one frame | not established statically | UNKNOWN |
| Hold [D+0x2b] from the tick | NOT safe: slot 12 rewrites it, and if it runs before 0x47cd80 the press goes through | VERIFIED (consequence) |
| Order-proof lever | bit 0x80 of the input mask [player+0xed0] (gates slot 7 ORing the action, so [H+0x2d3] stays 0). Also blocks fire etc. (kld_mask already does this) | VERIFIED |
| Alternative | DirectInput wrapper (klauto/klrigid) hide of the Cover key | GUESS (not read in depth) |
| Counting presses | [D+0x2b] reads 0 once masked, so count from a raw source: the action object (0x5f4310 on H+0x104) or the DirectInput wrapper | GUESS |

## Q3 Flop online

| Item | Finding | Verdict |
|---|---|---|
| RMC for the Flop=3 state-5 end | none sent | VERIFIED |
| Sender stubs | SetDowned 0x846d90, GettingUp 0x6cd720 (replica branch sets [D+0x21]=1), routed by the master test 0x9425a0 | VERIFIED |
| Replica state | master pushes D state/flags via 0x841db0 -> 0x504030 and 0x7033d0 -> 0x810d90 (reliable datasets) | VERIFIED; replica-side apply not read: UNKNOWN |
| Replica fall clip | the stock clip: the hook writes only the local player's M words | GUESS |
| Anim sets shared | pool [pl+0x78], table [pl+0x7c], records at [[0x1546f6c]]+n*0x68; Flop=3 rewrites the clip number in the human's pool, so it is local per peer | VERIFIED for the mechanism, sharing across bodies UNKNOWN |

## Q4 FlopUp

FlopUp's direct [D+0x21]=1 (event 8) does not call 0x7180b0 / 0x6cd720, so no GettingUp is sent: replicas would stay lying. VERIFIED (by absence of a call). The reaction on the replica is GUESS.

## Design

1. Mask 0x80 plus own mash meter; when full, let one real press through (or call the sender from the game thread), so the stock path sends GettingUp.
2. Flop=3 / FlopUp must end via 0x7180b0 / 0x8b74d0 on the game thread.
3. A runtime probe is needed for the slot 12 vs 0x47cd80 order.
