# Online FA round data (host Sv 0xbd2eb4, client Cl 0xbd31e4) - static decode 2026-10-26

Goal: fill the same snapshot as Arcade's klb_read (klhook/klbot.c klb_snap) online. No hook code changed.
CERTAIN = proven by disassembly in this pass. GUESS = inferred, needs a live read.

## Key fact
Sv and Cl are siblings under ZGameRulesFragileAlliance 0xbd2b9c. `S = [rules+0x2c]` is the replicated
DDL_ZScoreFragileAlliance on BOTH (base class field; slot 37 0x99db00 returns it, slot 36 0x563a50 sets it).
"Cl has no score object" only held for Arcade's ZHeistScore. CERTAIN.
Instance vtable 0xbd5184, ctor 0x776ad0, RTTI COL 0xca851c, descriptor vtable 0xbd522c (alloc 0x24).
Container DDL_ZScoreFragileAllianceContainer (vtable 0xbd5290, ctor 0x8be620) is embedded at C = S+0x58 (size 0x204).
Where the client creates/assigns its own S: NOT traced (set via slot 36/240) - GUESS that it exists once state 0x19.

## Records
[rules+8] = per-seat records, stride 0x74, [rules+0xc] = free-byte array (record in use iff byte==0), [rules+0x14] = count.
Record +0 = client object ptr (non-zero = seat taken; 0x615a60 on it = is-police test used by slot 14), +4.. unknown.
Record -> ZFFPlayer link at [rec+0x378] is on the PLAYER (ZFFPlayer +0x378/+0x380), see re/round_end_online.md. Seat index = idx in this array = client number used by all S arrays. CERTAIN (index), rest GUESS.
AI bots have no record (re/bots_online_fill.md), so they have no S row either: enumerate them from the entity table, not S.

## Per-player rows (index i = seat, i < 12). Addr = absolute S offset, byte/typed array [S+off+i*size]
(All arrays are 12 entries; stride = element size, the 0xc step in container offsets is 12 players x element size.)
| Field | S+ | type | Arcade klb equivalent | Mark |
| CustomFlags (status bits) | 0x98 | i32 | rec+0x10 status | CERTAIN |
| Sharable money | 0x188 | u32 | on_rew (old label wrong) | CERTAIN |
| Unsharable money | 0x224 | u32 | on_loot (old label wrong) | CERTAIN |
| HUD money = Sharable+Unsharable | 0x5675fc..0x56760c, cache [rules+0x320] | | money | CERTAIN |
| Kills | 0xec | i8 | kills | CERTAIN |
| PoliceKills | 0x170 | i8 | | CERTAIN |
| KillerIndex | 0xe0 | i8 | killed-by | CERTAIN (field), semantics below |
| Assists | 0x5c | i8 | | CERTAIN |
| Rating | 0x17c | i8 | rank | GUESS (name only) |
| Experience | 0xc8 | i16 | level | GUESS |
| Trust | 0x218 | i8 | | CERTAIN (field) |
| BestGrab | 0x68 | u32 | | CERTAIN (field) |
| TotalLootMoney / TotalRewardMoney | 0x1b8 / 0x1e8 | u32 | round-end totals only | CERTAIN |
| NumMercsKilled/NumOthersKilled/NumPersonalRevenges/NumRoguesKilled/NumRoundsEscapedAsMerc/AsTraitor/NumTraitorsKilled/PlayStyleMasks | 0xf8,0x104,0x110,0x11c,0x128,0x134,0x140,0x14c | i8 | | CERTAIN (field) |
| PlaystyleKillPoints | 0x158 | i16 | | CERTAIN |
Getters (S-level): Kills 0x70d510, KillerIndex 0x4c76f0 (push idx; al), CustomFlags 0x571750, Sharable via rules slot 56, Unsharable via rules slot 55.
Setters: KillerIndex 0x6315f0(idx, val), Kills++ 0x698750, PoliceKills++ 0x896a20. Dirty byte C+0x1fc, mask word C+0x1fe, delta writer 0x537d40.

## Status bits (CustomFlags, stock HUD mask 0xfffff2ff, icon map) CERTAIN
0x01 -> icon 1, 0x04 -> 4 (dead), 0x08 -> 2 (police/fed), 0x40 -> 3 (escaped), 0x1000 -> 5, else 0.
Down / betrayer / dirty-cop bit values: NOT decoded (GUESS: in the 0x200/0x100/0x400 gaps that the mask removes).

## Killer of a dead player
- KillerIndex[victim] (S+0xe0+i, i8) is the replicated killer seat. CERTAIN that it is cleared to -1 when the victim leaves:
  rules slot 14 (0x89b8b0, the player death/switch-to-police handler, arg = ZFFPlayer) loops all seats and for every
  seat whose KillerIndex equals the dying player's number calls 0x6315f0(seat, -1). So it is "who killed me" for the CURRENT
  victim; read it while the victim is dead/down and before slot 14 runs; a dead seat with -1 = no killer / world.
- 0x606c80(idx) is a rules method returning KillerIndex[idx] only in state 0x19 (round), else -1. CERTAIN. Use it directly.
- Display carrier: RMC AnnounceFAPlayerDeath(iClientIndex, bPlayerPoliceMan, iKillerClientIndex, bKillerPoliceMan) (netcode.md:582), plus
  AnnounceFATraitor(killer,dead,first), AnnounceDirtyCopRevenge(killer,dead,personal), ActorDied(rActor,rKiller), SetKillMarked. The handler
  (client side message/LOC producer) was NOT located: GUESS that the stock game builds its killed-by line from the Announce RMC args, not
  from S. Hooking the RMC receive (or reading KillerIndex on the transition to dead) both work; the latter needs no RMC hook.
- 0x4eb260 (rules method, args 2 seat numbers) reads KillerIndex[arg1] and updates a per-pair table at [rules+0x290+ (a*3+b*12)] (kill streak/revenge counter); it is the message-selector (picks a LOC from [0x168d7c0]+0x65c/0x67c). Probably the killed-by line chooser. GUESS.

## Round state (S members, {value,..., notify at +8}, 0x28 apart)
| Field | S+ | Notes | Mark |
| m_iCurrentRound | 0x34c | i8, init 1, getter 0x57e490 | CERTAIN |
| m_iNumRounds | 0x3d0 | i8, init 3, getter 0x7f42e0, slot 40 returns it, slot 39 sets (also [rules+0x5c]) | CERTAIN |
| remaining round time | 0x2ac | float, getter 0x556ce0; slot 85 mirrors to [rules+0x4c] = the HUD clock | CERTAIN |
| m_fRoundTime (length) | 0x324 | float, getter 0x59bf80, slot 43 returns it, set with 0x2ac by 0x7f4e30 | CERTAIN |
| m_fEscapeSeqTimer | 0x25c | float, getter 0x727890, slot 87 -> [rules+0x1d8] (Arcade timer) | CERTAIN |
| EscapeSeqState | 0x38c | i8, setter 0x4b8960 (slot 194), mirrors [rules+0x1dc] (Arcade veh byte) | CERTAIN |
| EscapeSeqTransportRef | 0x3ac | u32, getter 0x786420, slot 89 -> [rules+0x1e4] (Arcade vehicle) | CERTAIN |
| EscTransportState | 0x36c | i8, getter 0x72c9a0, setter 0x5978d0 from slot 94 | GUESS name |
| floats 0x284, 0x2d4 (-> [rules+0x200] slot 88), 0x2fc | | RoundOverTime / GameOverTime / RoundEndTimer, which is which unresolved | GUESS |
Mirror fields in the rules object ([rules+0x1d8/0x1dc/0x1e4/0x4c/0x200/0x320]) are written on both Sv and Cl by the slots above, so the cheapest read is the mirror, as Arcade does.
Round line on the stock HUD: OSD obj = [0x168e598]->vtbl[0x2c](); vt+0x12c(1, curRound), vt+0x12c(0, numRounds), money vt+0x12c(2,m), status vt+0x128(2,icon); own seat 0x7af9d0(session). Fed from the rules base tick 0x567261..0x5676d0 on both Sv/Cl. CERTAIN.
Session: [0x168e598] +0x5c mode, +0x54 role, +0x70 state (0x19 = round, 0x8e6a20 getter). Settings [0x168e9e4]+0x54 = rules.

## Character / hero
Seat -> character: rules vtbl[0x220] = slot 136 0x452a40 GetHero, client number via 0x817160(session, 0x8e8010(8)); klcharonline's chosen character
is in klchar state (re/char_online.md, slot 137 0x74ee10). Not re-decoded here. AI bots: no seat. GUESS for bots (entity table index).

## Upgrades / rank / level
DDL_ZClient has m_iRank, m_iUseMask, m_iTeam (client object, record +0). Per-player Rating i8 and Experience i16 are in S (above). The Arcade
"level" ([score+0x45]) has no online twin found: GUESS = derive from Experience. No shop-upgrade store located online.

## Open
1. Client-side creation site of S. 2. Exact bit values for down/betrayer in CustomFlags. 3. Name text object of the stock FA player list (re/hud_tags.md:49).
4. Handler of RMC AnnounceFAPlayerDeath and its LOC. 5. Record (0x74) internal layout beyond +0 and [rec+0x378].

## Where the 12-player / 10-min / 10-round / map-bundle options are
Not part of this decode. See re/max_players.md, re/lobby_12rows.md, re/lobby_options.md, re/lobby_map_names.md; log entries 2026-10-25 23:55 (HOSTOPTS 1025b, [Lobby] RoundClockFix) and 2026-10-26 00:10 (PlayersMax=12, Rows12).

## Corrections to klbot.c comments
on_loot (S+0x224) = Unsharable, on_rew (S+0x188) = Sharable; the loot bar = Sharable+Unsharable summed over seats, not ZOnlineMoneyCtrl +0x34 alone.
