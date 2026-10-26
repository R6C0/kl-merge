# Undercover Cop P2: the police AI and the hidden UCC (static read, 2026-10-26, scheduled cloud check-in)

Owner decision 2 of `re/ucc_design.md`: "police AI treat the hidden UCC like a heister". The design doc's P2 said the soldier
friend test keys on the player byte `+0x2723` and proposed keeping that byte 0 on the UCC while hidden. That is not what
the game does in an Undercover Cop round, and clearing `+0x2723` would be the wrong tool. kl2.exe 0490 (sha1 9d99e01d...)
staged read-only, read with `debug/kl.py` + capstone; nothing run. GUESS marks my guesses; the rest is on the listing.

Built from it: `klhook/klucc_aim.c` + `klucc_aim_logic.h` (`[Ucc] PoliceAim=1`, default off), harness `klua_test.c`
27/27 (gcc and MinGW), `--check-hook` 0 errors. NOT compiled with MSVC, NOT run live.

## 1. The stock gate: one byte, rules slot 188

`SetUndercoverCop(a, b)` / `RMCUCCMissionFailed(bUCCMissionFailed, bUCCAIHostile)` end in rules slot 187 `0x74d9f0`:
`[rules+0x283] = a; [rules+0x284] = b` (re/ucc_down_only.md 3, re/ucc_sabotage.md 5.2). The second byte has exactly one
reader: **slot 188 = `0x5119a0` (`mov al, [ecx+0x284]; ret`)**, at vt+0x2f0 of both FA rules tables (Sv 0xbd2eb4, Cl
0xbd31e4; also in 0xbd2e8c / 0xbd3804, other classes' tables). Its callers are three soldier-side tests, each with the same
shape - in a session state 2/3 (`0x863a60`, states 2 and 3 of `[sm+0x54]`) with the sub-mode word `[0x168e59c] == 1` and
game type 4 (`0x7bb2a0` returns the rules object or 0):

| site | routine | what it decides | the UCC (`[P+0x2729] != 0`) when slot 188 = 0 | when 1 |
|---|---|---|---|---|
| `0x8824cd` -> ret `0x8824d5` | `0x882470` = ZSoldier@CPPScript (vt 0xbd0954) slot 111: a soldier scores a ZFFPlayer as a target (returns a float; `[0xb5f1e0]` = "no target") | enemy or not | **rejected at `0x8824d9`: nobody's target** - the police byte test `0x8824e7` is bypassed for him | continues at `0x8824fc` like any player; at `0x8826fb` an Ally soldier reads his police byte `+0x2723` = 1 -> enemy. So the AI heisters shoot him too |
| `0x5708c2` -> ret `0x5708c4` | `0x5706a0`: the players and actors along the fire line (tracker `0x5891f0` from `[gd+0x159c]`) that count as friends | friend in the line of fire | `jne 0x57090a` not taken -> `+0x2723` -> listed as a police friend | skipped: not a friend |
| `0x51d9f9` -> `0x51d9fb`, `0x51dac3` -> `0x51dac5` | `0x51d6c0` = ZSoldier@CPPScript slot 114: the bodies in the soldier's fire cone (calls `0x5706a0` at `0x51da55`) | counted / listed | counted as police (`[ebp-0xc]`) | as a hostile |

So in stock the hidden UCC is **invisible to every soldier** (police and crew alike) and a police friend in their fire
lines; once the byte is 1 he is everyone's enemy. The owner's rule - police shoot him, his own crew's AI does not - is
neither value. It is slot 188 answering **1 to a police asker and 0 to a crew asker, per call**.

Non-UCC players in the same branch: `cmp [esi+0x2729], 0; je 0x8824fc` - they skip the police test too (in a UCC round
there is no other police player). Outside a session / outside sub-mode 1 the old path holds: a police player is a target
for team-2 (Ally) soldiers only (`0x8824e7..0x8824fa`, re/balance.md 11.2).

## 2. Who sets the byte in stock

`0x418b20(ecx = [sm+0x84], a, b)`: online and `[sm+0x15d]` -> sends `RMCUCCMissionFailed` (stub `0x637cd0`, name at
`0x637cdc`); then rules = `0x7bb2a0()`; if slot 186 (`0x4c0630` = `[rules+0x283]`) is still 0 -> `0x5570a0` (the
mission-failed announcement, GUESS of what it shows: it fetches a display object through `[gd]` `0x588680`); then slot 187
(a, b). Three senders:

1. **`0x847886` in the NPC damage routine `0x8473a0`: rules Sv slot 128 `0x5df280`** (re/player_down.md: "at health 0 with
   a PLAYER attacker ... for a police player, slot 128"). Conditions on the listing: the attacker has `+0x2723` and not
   `+0x2727`; session (`0x863a60`) or Arcade (`0x7f6850`); sub-mode != 2; game type 4; **the victim NPC's team
   `[[actor+0x54]+4]` is not 0 and not 2** = a police / enemy NPC. Slot 128 then: not in C&R, state != 0x1f; slot 110 and
   slot 114 & 0x1000 (dirty cop) gates; `0x713970` on the attacker's `+0x2748` object once (GUESS: a voice line / sound);
   **`0x418b20(1, 1)`** = exposed AND AI hostile; slot 115 (`+0x1cc`) sets score flag **0x40000** on the index (stock row
   state 4, re/ucc_tell_audit.md S1); `0x717fc0` -> flag 2 and a float at `[[rules+8] + 0x74 i + 0x6c]`; then the reward
   pop-up path (`0x8c51b0`, `0x6fc950`, `0x7b2b20`, `0x5f0d20`). **So in stock the UCC who shoots a police NPC dead is
   exposed to everyone and the police turn on him.** Heister kills do NOT go through here (team 2 victims are excluded).
2. **`0x7772b2` in `0x776ef0`** (called from the Sv tick slot 195 `0x727610`): sub-mode 1, `[esp+0x16]` set, slot 132
   (`0x64c650`) != -1 = a UCC index that is dirty (0x1000) or dead (4) (re/ucc_sabotage.md 5.1), slot 186 false ->
   `0x418b20(1, 0)` = mission failed, police NOT hostile.
3. `0x7fadd0(a, b)` forwarder (caller `0x894ac9` in `0x894990`: not read) and `0x53aee0` (the RMC receive side, from the
   dispatcher `0x693780`: unpacks two bools and calls `0x418b20` on the receiver).

`+0x283` readers (13, all FA rules): slot 15 damage `0x4254fa`, rewards `0x4eb260`, the friendly-fire text `0x6ffdc0`
(re/ucc_design.md P6 FINDING), crosshair colours (re/fed_kit.md), slot 192 `0x680f90`, `0x4ae130`, `0x4569b0`, `0x5e2230`,
`0x5df2eb` above. None of them is the AI gate: that is `+0x284` alone.

## 3. Why not clear `+0x2723`

A byte-pattern scan of .text finds **81 instructions reading `[reg+0x2723]`** in 50 routines (one write: `0x6ef636` in
`0x6eef20`, the `SetPoliceMan` path): rewards (`0x4eb260`), boarding (`0x68414e`: a policeman cannot board), the damage
pairs (`0x591b9f`, `0x7c1bd7`, `0x6e3400` x6), the crew list / HUD (`0x8e9720` x5, `0x8f5eb0`), the hit filter
(`0x458880` x3), `0x602350`, `0x612c20`, `0x656fb0`, `0x67f480` x4, `0x78f5d0` x4, `0x8dbc20` x2 ... Clearing it on the
UCC makes him a heister to all of that (he could board, his kills would pay as a heister's, the HUD would recolour him).
And in a UCC round the AI does not even read it for him (section 1). The slot-188 answer is the only switch the AI uses.

## 4. The build (klucc_aim.c)

- Slot 188 of the rules object's **private vtable copy** - klroundkeep.c's (`klrk_vt`), klucc_down.c's (`klud_sv/cl`) or
  klucchide.c's (`klucc.vtSv/vtCl`) table when one is installed (the slot is patched into it, as klucchide.c does with slot
  114), else our own copy after 9 s (klucchide.c waits 6 s, so it goes first; klud waits 3 s). Each table is checked to hold
  `0x5119a0` in slot 188 before it is patched. `klh_rules_vt2/3` is set for our own copy so the `KLH_RULES_*_OK` tests
  accept it. No code byte, no stock vtable is touched (re/antitamper.md).
- The slot holds a **naked thunk** (`klua_fwd188`): `mov eax,[esp]` (the return address), `push esi; push edi; push ebp;
  push eax; call klua_w188; ret`. The game's `call eax` leaves the caller's ebp / edi / esi untouched, and the `__fastcall`
  wrapper pops its four stack words. The game reads `al`.
- The wrapper first takes the stock byte through `0x5119a0`; a stock 1 is returned as is (an exposed UCC stays exposed).
  Then: the site from the return address (the three above; anything else -> stock, logged 5 times); the FA / sub-mode-1
  gate (`[sm+0x5c] == 4`, `[0x168e59c] == 1`); the asking soldier: **score site** edi = the ZSoldier@CPPScript (vt 0xbd0954,
  also `[ebp-0xc]`), player `[ebp+8]`; **fire-line site** `[ebp-0x30]` = `this` (`0x5706d0`), its `+0x154` = the soldier
  script (`0x570708`), player esi; its team is also kept at `[ebp-8]` (`0x57072d`) and is cross-checked - a mismatch means
  stock; **cone site** edi = `this` (`0x51d6ca`), `+0x154` = the soldier script (`0x51d6cc`), player esi. Team =
  `[[soldier+0x40]+0x54]+4` (actor at `[script+0x40]`: `0x8824f0`, `0x51d739`, `0x57070e`). Police = team 1 or 4
  (`0x882470` itself treats 1 and 4 alike at `0x882650..0x88265e`). The player must be the UCC (klud_is_ucc: `+0x2729`,
  net bit 8 or score 0x80) and hidden (klucchide.c's mask through `klud_revealed`; with Hide off the mask stays 0 = hidden
  all round, as klucc_down.c assumes).
- Answer 1 only for police asker + known site + hidden UCC; the crew's AI and unknown callers get stock 0. `Dry=1` logs
  and answers stock. First answer per site, the first 10 and every 500th are logged.
- Effect: the police score him like any player (target path `0x8824fc` -> `0x882636` -> team 1/4 -> `0x882584`), do not
  count him as a friend in their fire line, and the AI heisters still see slot 188 = 0 -> he stays out of their target
  list. After the reveal: stock (0) - the police treat him as police again, as the owner's P6 text says.
- Host only in effect (the soldier AI runs on the host); installed on Sv and Cl alike, harmless on a client.

## 5. GUESSES and open points

- GUESS: team 4 (Enemy2) soldiers exist in FA levels as police (SWAT waves?). If they are something else, drop 4 from
  `klua_police_team`. The log line prints the team.
- GUESS: `0x5706a0`'s `this` is one object class at all its callers (`0x51d6c0`, `0x767460`, `0x8f6990`); only the
  `+0x154` -> soldier script -> actor chain is used and it is vtable-checked, so a wrong guess gives the stock answer.
- The stock **cop-killer exposure** (section 2.1) is untouched: a hidden UCC who shoots a police NPC dead is exposed by the
  game itself (announcement, byte 1,1 = everyone's enemy, score 0x40000, 0x717fc0 flag 2). Under the owner's "reveal only by
  his key" this is a second reveal path. OWNER: keep it as the "caught in the act" rule (Killer Within), or should a slot-128
  Sv wrapper (host, same private table) swallow the exposure while hidden? Note klucchide.c's reveal state would not know
  about a stock exposure either: its lists would still show him as crew while the AI already hunts him (a tell in reverse).
  Cheap fix either way: klucchide reads slot 186/`+0x283` or `+0x284` = 1 as "revealed by the game" (not built).
- NOT READ: whether `0x882470` is also reached for players on a CLIENT (local prediction); if it is, the client's answer is
  the same, so nothing differs.
- Not covered: police AI "friend" lists elsewhere that do not go through slot 188 (none found: the three sites are all the
  callers of the slot; `0x5706a0`'s other callers go through the same site).

## 6. Bench (not run)

Two instances, System Link, stock DD01, Undercover Cop, host ini `[Ucc] Hide=1 PoliceAim=1 Log=2`, `[Lobby] MinPlayers=2`.
Read on the host: `uccaim: rules ...: slot 188 (bUCCAIHostile) of <whose> private vtable now answers HOSTILE ...` (which
table took it); `uccaim: target scoring 0x882470: police soldier ... (team 1) asks about the hidden UCC ... HOSTILE`; no
`fire-line site: frame team ... differs` line; no `slot 188 asked from ...` line with an address outside the three. Play:
the cops fire at the UCC as at a heister from the first contact; the AI heister bots (if any, `[BotFill]`) do not. Press the
reveal key: the `uccaim` lines stop (stock 0), the police stop shooting him. Shoot a cop dead while hidden: the stock
exposure (section 2.1) - note what the announcement says and whether the lists change (klucchide does not know about it).
