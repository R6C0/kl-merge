# Undercover Cop design sheet (2026-10-26, research only, nothing built or run)

Item 3 of `re/ucc_cnr_owner_request.md`. References the owner named: Among Us (fake tasks, sabotage, kill cooldown, no
kill feed) and Death Note: Killer Within (the killer stays hidden until caught in the act or shows himself). Tell ids are
from `re/ucc_tell_audit.md`. Addresses are kl2.exe 0490, static reads. GUESS marks my own guess.

Base: UCC is sub-mode 1 of the FA family (`[0x168e59c]`), lobby 4..8 in that sub-mode (6..12 is C&R's), flag 0x80 on the
UCC's player set by the `SetUndercoverCop` RMC on every peer, one rules class pair branching on the sub-mode.

## The six proposals

### P1 Fake the job (Among Us fake tasks)
Player: the UCC carries and banks loot like everyone else and his money row moves, so the crew list says nothing.
Today: the stock rules already let a 0x80 player loot (fed_kit slot 110), so the tell is in the DISPLAY: S10 (our Tab
card shows FED) and S1 (stock row state 3/4). Build: S10 = `[HUD] UccHide` (klhud_values.c:520, built, not run). S1 = a
private-vtable wrap of slot 114 (0x771a10) stripping 0x80 for viewers who are not police and not the UCC. Cost S. Risk low,
display only. Private 6..12: yes, each client hides its own view.

### P2 No behavioural tell (AI police treat him as a heister)
Player: police fire at him like anyone, so "the cops never shoot him" is gone. Today: NOT established. The soldier friend
test (0x882470, bots_fight 2.1) keys on `+0x2723` police and `+0x2726` traitor; whether `SetUndercoverCop` (slot 187
0x74d9f0, handler 0x418b20) also sets `+0x2723` needs reading. Second half, the audit's "missed" tell and the strongest:
a heister who shoots him gets `FA_NoFriendlyFireUCC` and is never marked traitor (0x41d480 returns on flags & 0xc only).
Build: keep `+0x2723 = 0` on the UCC's actor on every peer while hidden (the fed-kit `Hunt` byte pattern), restore at
reveal; route `FA_NoFriendlyFireUCC` to `FA_NoFriendlyFire` (.LOC, kllocname.c style). Cost M. Risk medium: he then dies to
police like a heister (wanted). Private 6..12: yes; the host's byte alone fixes AI aim, AI runs on the host.

### P3 Kill cooldown, silent takedown, hidden kill feed
Player: one kill per N s; a close-combat kill makes no pop-up; the kill line never names him while hidden. Today: S4
(`FA_Killed_UCC`, 0x704b79) and S5 (the 100,000 money jump). Build: S4 is a .LOC route to `FA_Killed_Merc`; S5 is the
tuning int `[0x168d7c0]+0x674` 100,000 -> 10,000 while hidden (klbalance.c already writes that object). Silent takedown
is the stock `CloseCombat` RMC; its pop-up branch (0x4857d1 / 0x70474a) needs reading. Cooldown: block the UCC's fire for
N s after a kill, host side (fire path needs reading) GUESS. Cost M feed, L cooldown. Risk: an unreplicated cooldown
desyncs who fired; keep it host-authoritative. Private 6..12: feed yes; cooldown only as a host rule.

### P4 Sabotage (early police wave, van or door jam)
Player: a key press as the UCC brings the police now, or holds the van / a door N s; nobody sees who did it. Today:
nothing. Build: waves are `ZSquadScript` timers (map_ai 2); firing a trigger is the `[BotFill] OnlineRampFire` pattern
(host fires a trigger box); van hold = `ZBoardEscapeVehicleTactic` slot 3 / HoldEscapeVehicle data; door jam =
`DeactivateGeom` on a kick door. Needs a per-map table of triggers (authored like the exit route legs). Cost L. Risk high:
per-map authoring, and a host-only action must look identical on clients. Private 6..12: host-driven, yes, per map.

### P5 Misdirection pings, optional two UCCs
Player: a chalk-bar line now and then names a random heister as suspicious; at 9..12 players two UCCs who do not know
each other. Today: none. Build: ping = a hook popup (klhud_popup.c style), name chosen by the host so all see the same.
Cost S. Two UCCs: where the rules Sv picks the one 0x80 player needs reading; a second host `SetUndercoverCop(true)` is the
engine's own call and reward / scoring branch on the flag, so it should just work GUESS. Cost M. Risk: two in a 6 lobby is
too many; floor 9. Private 6..12: UCC lobby is 4..8 today, so this is BLOCKED on lifting the player row (lobby_options:
spawn count above 8 unknown).

### P6 Reveal only by choice or when seen killing (Killer Within)
Player: the UCC is a heister in every list until he presses Reveal or kills a heister; then his row turns FED everywhere
and police treat him as police. Today: the flag is set at round start for everyone (S2). Build: a host-kept `hidden` state
per UCC that P1, P2 and P3 read. Simplest GUESS: the host sends `SetUndercoverCop(false)` at start and `(true)` at the
reveal, using the engine's own RMC; needs reading whether the rules object re-reads the flag or caches it. "Seen killing" =
the kill's killer-of-record is the UCC (`m_DeathInfo` reaches peers anyway); no line-of-sight test. Cost M. Risk: a host
state machine with no bench yet. Private 6..12: yes.

## Recommended minimal set for the next play night
1. P1 both halves (UccHide + S1 stock row strip): S, no game call.
2. P2's friendly-fire half (`FA_NoFriendlyFireUCC` routed to the normal text): S, data. Leave the AI aim byte until the
   live UCC1 bench says whether police ignore him.
3. P3's feed half (kill line through `FA_Killed_Merc`, reward 100k -> 10k while hidden): S.
4. P6 as "reveal on first heister kill", no key yet; the three above hang on it, so build the host state first.
Not for the next night: P4, two UCCs, the cooldown.

## Questions for the owner (default in brackets)
1. Reveal rule: his first heister kill, any kill, or only his key? [first heister kill]
2. Should police AI shoot the hidden UCC like a heister? [yes]
3. Is the 100,000 bounty kept after the reveal? [yes; 10,000 while hidden]
4. Two UCCs at 9+ players? [not yet; UCC lobby is 4..8]
5. Sabotage first: early police wave or van hold? [early wave, DD01 only]
6. False pings on, and how often? [off until P1-P3 are proven live]

## OWNER DECISIONS (Josh, 2026-10-26 14:06; these replace the defaults above)
1. Reveal: ONLY by a key the UCC presses himself. Killing / downing does not reveal him.
2. Police AI treat the hidden UCC like a heister (P2 aim byte: yes). NEW RULE: while hidden, the UCC's hits on
   heisters can only DOWN them, never kill ("you can tell he's not trying to kill, just harm"). Read: does this cap
   apply after the reveal too? Not stated; GUESS hidden only, ask at the next check-in.
3. Reward for a criminal killing the UCC: 200,000 while hidden, 400,000 once revealed (stock 100,000 at +0x674).
4. Two UCCs: yes, and the two KNOW each other (each sees the other as FED). Still needs lobbies above 8 (P5 blocker).
5. Sabotage: look into ALL THREE (early police wave, van hold, door jam).
6. Suspicion messages: ON, and heisters can also raise them themselves (an accuse key naming a player), next to the
   host's random fake pings.
   BUILT 2026-10-26 (not run live): klhook/klucc.c `[Ucc] Pings / Accuse` (F5, aim cone, 20 s per player) over the shared channel
   klhook/klnetchan.c (re/hook_netchannel.md: UDP = System Link proven pattern; Steam member data only while a lobby exists; internet
   rounds have no carrier yet, the P2P proxy is ranked next). Bench: re/hook_netchannel.md 5.
Consequence: P6 becomes a key only; the "down not dead" cap is new work (damage path, FA downed state) = P7.

## Rebalance levers that exist today as data (item 5)
- Round time: lobby row 3..5 min, `[Lobby] TimeMax / TimeMin` (kllobbyopt.c); replicated `m_fRoundTime`.
- Rounds: 3..5 (C&R floor 4 step 2), `[Lobby] RoundsMax`; `m_iNumRounds`.
- Kill rewards, tuning object `[0x168d7c0]` (fed_kit 10.1): traitor 100,000 (+0x65c), traitor who killed you 200,000
  (+0x660), cop kills criminal 50,000 (+0x664), criminal kills cop 10,000 (+0x66c), criminal kills UCC 100,000 (+0x674).
- Damage by who shoots whom, per Arcade level, `[0x168d7c0]+0x6ac+L*0x70` (balance.md 2): `[Balance] Risk=0..3`, `Ramp`,
  `CrewOffStage`; L = escapes so far + 1.
- Retaliation threshold `[R+0x18]` (100..25), when a bot turns on a player: `[Bots] Retaliate`.
- Police strength and waves: level data via `tools/kl_map_ai.py apply` (`--no-strength`, `--no-waves`); stock accuracy 55.
- Loot: value per money stack entity (150,000 on Retomoto cases); C&R stacks are `TeamModeDropMoney`, authored per map.
- Players: 4..8 FA/UCC, 6..12 C&R, immediates in 0x7dc060; above 8 not offered yet.
- Health: `[Balance] Risk` sets the player's 550 -> 400 / 280 and regen 8 s.
Start item 5 from a per-mode table of these once UCC1 / CNR1 give the feel.
