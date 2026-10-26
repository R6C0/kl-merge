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
engine's own call and reward / scoring branch on the flag, so it should just work GUESS. CORRECTED 2026-10-26 (re/ucc_sabotage.md 5):
the pick is Sv slot 4 0x40f870 (exactly one, stop byte); SetUndercoverCop(a, b) only sets the rules MODE bytes +0x283 / +0x284, so a
second call does nothing for a second player; a second UCC needs the pick's per-player calls repeated from a slot-4 wrapper. Cost M. Risk: two in a 6 lobby is
too many; floor 9. Private 6..12: UCC lobby is 4..8 today, so this is BLOCKED on lifting the player row (lobby_options:
spawn count above 8 unknown).

### P6 Reveal only by choice or when seen killing (Killer Within)
Player: the UCC is a heister in every list until he presses Reveal or kills a heister; then his row turns FED everywhere
and police treat him as police. Today: the flag is set at round start for everyone (S2). Build: a host-kept `hidden` state
per UCC that P1, P2 and P3 read. Simplest GUESS: the host sends `SetUndercoverCop(false)` at start and `(true)` at the
reveal, using the engine's own RMC; needs reading whether the rules object re-reads the flag or caches it. "Seen killing" =
the kill's killer-of-record is the UCC (`m_DeathInfo` reaches peers anyway); no line-of-sight test. Cost M. Risk: a host
state machine with no bench yet. Private 6..12: yes. BUILT as a key-only reveal with our own host state (the simplest guess
does not work): section "P6 BUILT" below.

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

## P6 BUILT: hidden until the reveal key (2026-10-26, klhook/klucchide.c + klucchide_logic.h, harness klucchide_test.c 102 checks; NOT run live)
Decisions 1, 3, 4 and the display halves of P1 / P3. `[Ucc] Hide=0` (master, default off), `RevealKey=0x2D` (Insert: F5 is the accuse
`Key`, J is `[Sabotage]`, E/F/G/H/F6..F9/F11/Tab are taken, F10 opens the window menu, F12 is Steam's screenshot), `Strip=1`, `Rows=1`,
`Feed=1`, `Bounty=1`, `BountyHidden=200000`, `BountyRevealed=400000`, `HideLog=1`.

**Why not the engine's own call (static read, kl2.exe 0490).** The string `RMCSetUndercoverCop` (0xb3c810) is used only by the send stub
0x766310, called only from the wrapper **0x432780(ddl, bool)**: on the player's master (his own PC) it runs 0x8c95e0 = DDL m_iFlags bit
value 8 (replicated) + `[P+0x2729]` (0x4622b0); elsewhere it SENDS the call to that master. Callers: the host's pick 0x40fb0d (in Sv
slot 4 0x40f870), the death -> police switch 0x6bb910, the receive dispatcher 0x7afd10. (0x418b20 is `RMCUCCMissionFailed`, stub 0x637cd0,
which ends in slot 187 = the rules bytes +0x283/+0x284: agrees with re/ucc_sabotage.md.) The pick 0x40fa34..0x40fb74, in order:
`0x601fd0(score, i, 0x80)` (THE flag every list / reward reads: `[[rules+0x2c]+0x98+4i]`, replicated by the score object),
`0x43e270(P,1)`, `[P+0x2729]=1`, `0x644310(P, [0xd1b3bc])`, `SetUndercoverCop(ddl,1)`, **`SetPoliceMan(ddl,1)` (the UCC is flagged
police from the start: the likely reason the AI police never shoot him, P2)**, `0x745f20(ddl, hp)`. So SetUndercoverCop(false) would not
hide the 0x80 that shows; clearing 0x80 would switch off the game's own UCC rules and klucc_down.c's recognition. Slot 114 (0x625be0) is
a plain array read, no cache. => Own host state, display hiding only.

**Built.** (a) Host-kept `revealed` bit per crew index + an epoch per round (new round = clock `[rules+0x4c]` up > 5 s, a new 0x80 index,
or the state re-entering 0x13..0x1f); a client mirrors the host (newest epoch wins; a revealed bit counts only for an index the client
itself reads with 0x80). Every tick the bits go to `klud_reveal()` (DownOnly's cap ends at the reveal). (b) Reveal key: host's own UCC
at once; a client sends `UREV "R;<epoch>;<idx>"` on klnetchan.c every 2 s for 15 s, the host accepts only a hidden 0x80 index of the
current epoch and broadcasts `UHID "S;<epoch>;<ucc mask>;<revealed mask>"` (role 2 only; on change + every 5 s). Killing never reveals.
(c) `[tuning+0x674]` = 200,000 while any UCC is hidden, 400,000 when all are revealed (one int per round, not per UCC: with two UCCs the
lower number until both reveal - GUESS of the rule); written on every peer, the value found is put back after the session. (d) S1: slot
114 answered through a wrapper in a private rules vtable (or slot 114 of klroundkeep.c's / klucc_down.c's copy when one is installed;
waits 6 s for them on a stock object); ONLY calls returning into the stock list's 0x572050..0x5721c1 get 0x80 / 0x40000 stripped, and
only when this peer may not see him (not revealed, viewer not he, not police / dirty cop, not a UCC: two UCCs see each other).
(e) S10 online: our OnlineCrew rows go through the same rule (`klucc_hud_flags`; `[HUD] UccHide` only covered Arcade rows).
(f) P3 feed: kllocname.c's LOC wrapper looks `FA_Killed_UCC` up as `FA_Killed_Merc` (both take only `{Reward1}`: 0x463cc9 / 0x463eaa)
and `FA_NoFriendlyFireUCC` as `FA_NoFriendlyFire` while any UCC is hidden. FINDING: the friendly-fire text picks its UCC variant by the
SUB-MODE alone (0x6ffea7), not by the victim: a mode hint, not a tell.

**GUESSES / unread.** The own crew index on a CLIENT (records' +0x378 player + master test; fallbacks the local player's crew byte
(klucc_down.c) and the stock list's +0xefc); the round clock +0x4c online; whether the full-path kill key (0x463cd9 -> 0x694760 ->
0x468430) passes the LOC object's slot 0 (the log prints the first 6 routes); the session state window on a client. Still a tell: the
reward NUMBER in the kill line (200,000 is no other kill's pay, S5) - pick BountyHidden equal to another reward to hide it. Not built:
P2 (AI aim / the police flag), S2 (the 0x80 reaching every client's memory), S6 voice lines, the cooldown.
**Channel.** klnetchan.c = UDP (System Link / same PC); Steam member data only while a lobby exists. Internet rounds: no carrier, so a
CLIENT's reveal reaches nobody there (the host's own UCC still reveals for the host's screen). Remote cop-squad orders need the same.

**Live bench (not run).** Two instances, System Link, stock DD01, Undercover Cop, `[Ucc] Hide=1 HideLog=2`, `[NetChan] Log=2`, `[Lobby]
MinPlayers=2`. Read: `ucchide: Undercover Cop session as HOST/CLIENT`; `my client index K (found by ...)` on both (`I AM THE UNDERCOVER
COP` on one); `slot 114 of ... private vtable` / `answers slot 114 through our copy`; `[tuning+0x674] ... 100000 -> 200000`; screenshot
the heister's Tab list (UCC row must be crew, stock list and ours); UCC presses Insert -> `REVEALED` on the host, `host state via UDP ...
revealed` + `my reveal is confirmed` on the client, bounty `-> 400000`, both lists show FED; kill the UCC while hidden in a second round:
`feed: LOC key ... FA_Killed_UCC looked up as ...FA_Killed_Merc`.

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
