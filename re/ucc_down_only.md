# UCC "down, not dead" while hidden (P7) - research and build (2026-10-26)

Owner rule (re/ucc_design.md "OWNER DECISIONS" 2): while the undercover cop (UCC) is hidden, his hits on heisters can only put
them in the DOWNED state, never kill them ("you can tell he's not trying to kill, just harm"). A downed heister shot again by
the UCC must stay downed, not die.

Static reading of kl2.exe build 0490 (capstone, `/home/claude/dbg/kl2.exe`, md5 68d7459e...). Nothing here ran in the game.
READ = read in the disassembly this session; GUESS = my inference, marked. Built: `klhook/klucc_down.c` (+ `klucc_down_logic.h`,
harness `klud_test.c`, 55 checks pass), `[Ucc] DownOnly=0` by default.

## 0. Short answer

- **The victim's own PC decides health and death.** The shooter's PC prices the hit and sends `RMCReceiveHit` with the damage;
  the victim's PC (master of his own `DDL_ZFFPlayer`) applies it through `ZFFPlayer` slot 423 = 0x458880 -> down trigger 0x8da3b0
  -> health change 0x6e3400. No host arbitration on the way (READ, section 2).
- **A safe hook point exists, no code patch:** 0x6e3400 asks the rules object BEFORE it subtracts: 0x83ad70 -> rules vtable slot 15
  (+0x3c) = 0x425320(victim, **float \*delta**, attacker). The delta is passed by pointer. A private copy of the FA rules object's
  vtable (Sv 0xbd2eb4 on the host, Cl 0xbd31e4 on clients) with slot 15 wrapped can clamp one attacker's damage on one victim.
  Same technique as klroundkeep.c (which already gives the host's Sv object a private copy; the two share it).
- **Stock: a downed (lying / getting-up) player takes every hit in full and can be finished by anyone** (re/player_down.md 1: the
  trigger returns 0 in states 1 and 3). With `DownOnly` on, the UCC's hits cannot take him under `Floor`: he stays down. Police AI,
  cops and traitors can still finish him (owner rule is about the UCC only).
- Built: `DownOnly=1` = the clamp (data + private vtable only). `DownOnly=2` = also, a hit that WOULD have killed a standing heister
  asks the game's own down trigger 0x8da3b0 (kind 9) on the next tick, the klcdying.c call (game call, GUESS that it works online).

## 1. The FA down state ("down not dead"), recap with what matters here

From re/player_down.md section 1 (READ there; re-checked the call sites here):

| item | value |
|---|---|
| state object D | `[player+0x2948]`; `[D+4]` 0 up, 2 going down, 1 lying, 3 getting up; `[D+8]` bit 0 down; `[D+0x38]` re-down pause |
| entry (trigger 0x8da3b0, asked at 0x458e7f BEFORE the health changes) | health <= 40 % (`[T+0x268]`) and a burst: hits >= 20 (`[T+0x274]`) summing >= 6 x 20 within 1 s, or >= 4 x 20 under 20 % health (`[T+0x27c]`, `[T+0x280]`); or a blast (kind 9). The floored hit costs nothing; health is raised to at least `[T+0x25c]` = 80 (Arcade / MP); pause 10 s (MP). T = `[0x168d7c0]` |
| while down | state 2 (falling) hits are free; **states 1 and 3: the trigger returns 0, every hit costs in full** -> a lying man dies to anyone |
| leaving it | the player presses Get Up (Cover key); no timer, **no bleed-out**: the FA down never kills by itself |
| death | 0x6e3400 subtracts via the health object 0x8a7c60 (0x6e361a); a man whose health reaches 0 dies (the death branch is in the player's own code after that, not traced further). Under 30 % (`[0xce8a14]` = 0.30) 0x80c590(1, 1) is called on `[player+0x2940]` (meaning GUESS: the near-death effect) (only on the master: `0x7de570` test at 0x6e36d5) |
| the other 'downed' | `[player+0x2940]` (0x5fe270, 15 states, 'waiting for a healer') is the co-op death cycle, session mode 2 only - not used in FA |

## 2. How a hit reaches a human and who decides (READ)

| step | where | facts |
|---|---|---|
| shooter side | `ZFFPlayer` vtable 0xbb45f4 slot 422 = **0x7e1700** | offline (`0x863a60` false) -> slot 423 here. Online: if the victim is local (`vtbl[0x3d0]` true) -> slot 423 here. Else, attacker `[rec+0]` a player who is local (`0x7de570([att+0x274c])` false) -> `[rec+0x28]` / `[rec+0x2c]` quantised to 16 bits (0xa8d330), refs packed (0x6ece90), sent via 0x7a8410 -> **0x891490**; rules `vtbl[0x1e4]`(victim, attacker, &dmg) notified. An attacker that is a remote player: dropped (his own PC sends). A non-player attacker (AI): slot 423 only where the victim is master (0x7e17f9) |
| apply-or-send | **0x891490** (`DDL_ZFFPlayer`) | `0x9425a0` (owner == this station) true -> rebuilds the record (attacker from 0x8ccde0(ref), the int16 damage back to a float), `vtbl[0x3d0]` false -> **`[[net+0x540]]->vtbl[0x69c]`** = slot 423; else sends `RMCReceiveHit` (0x713180). The receive stub 0x59f140 (via 0x658f71) calls 0x891490 on the owner |
| damage routine | slot 423 = **0x458880** | armour / state multipliers, then the down trigger 0x8da3b0(D, rec) at 0x458e7f (true and not kind 9 -> return, the hit costs nothing), then **0x6e3400(victim, -damage, attacker)** at 0x458ea8 |
| health change | **0x6e3400** (also called from 0x5c7bea, 0x60d1c7) | 0x83ad70(victim, **&delta**, attacker) at 0x6e3471 FIRST; then the FA sub-mode rules (0x6e3486..: sub-mode 1: police-on-police 0 unless +0x2729; 0x6e35ab: same team byte, no traitor -> x `[0xce8a40]` = 0.5 with a 10 s window `[0xce8a3c]`) - only ever zero or halve; then the subtraction 0x8a7c60 (0x6e361a); the near-death / death follow-ups only on the master (0x6e36d5) |
| rules hook | **0x83ad70** | `[gameset+0x58]` != 0 -> `jmp rules->vtbl[0x3c]` (slot 15), args (victim, float \*delta, attacker), `ret 0xc` |
| slot 15 | **0x425320** in Sv 0xbd2eb4, Cl 0xbd31e4 and the base 0xbd2b9c | damage-dealer / yellow-card bookkeeping, UCC branch at 0x4254cd (sub-mode 1, flags via slot 114, `[rules+0x283]`); reads the delta (0x425752 `fsub [&delta]`: the damage-dealer share), never stores through the pointer (READ, the whole function) |

So: **death is decided on the victim's own PC**, from the damage number the shooter's PC sent. The host decides nothing about a
human's health. Consequence for any rule of this kind: the code must run on every heister's PC (each with the key).

## 3. Who is the UCC, who is a heister (READ)

- The host's Sv rules makes the UCC at 0x40fab9..0x40fb0d: score flag **0x80** for his crew index (0x601fd0), then on the HOST's
  copy of his player `+0x2723 = 1` (0x43e270, police byte) and `+0x2729 = 1` (0x4622b0), then `SetUndercoverCop(1)` (wrapper 0x432780).
- `SetUndercoverCop` handler on the owner 0x8c95e0: net flags `m_iFlags` (word `[net+0x4c4] ^ 0xdead`, 0x431f60) **bit 8** set and
  replicated; the player byte **`+0x2729` = 1** (0x4622b0). On the other peers the UCC's proxy may carry only the replicated bit 8
  and the score flag (whether a peer's proxy gets +0x2729 / +0x2723 is NOT read).
- `SetUndercoverCop(0)` comes with rules flag 0x10000 at 0x6bba2c (the UCC loses the role, meaning not read).
- Crew index of a player: `(signed char)(byte [[P+0x2748]+0xdc] ^ 0xac)` (0x8e8010 -> 0x5b1400). Score flags of index i:
  `[[rules+0x2c] + 0x98 + 4 i]` when `i < [rules+0x14]` and `[[rules+0xc]+i] == 0` (slot 114 = 0x625be0 -> 0x571750 -> 0x4aece0).
  (klhud_values.c's `[score+0x1d4+4i]` is the ARCADE Heist class's slot 114, 0x771a10 - a different layout.)
- The hook counts the attacker as the UCC when ANY of the three marks is set (+0x2729, net bit 8, score 0x80), and the victim as a
  heister when none of the police / UCC / dirty-cop / dead / waiting marks is set (+0x2723, +0x2729, net bit 8, score 8 / 0x80 /
  0x1000 / 4 / 0x4000). Only in sub-mode 1, so +0x2729 cannot be FA's dirty cop.
- Side finding: `[rules+0x283]` / `+0x284` (slot 187 = 0x74d9f0) are set by **0x418b20, the `RMCUCCMissionFailed(bUCCMissionFailed,
  bUCCAIHostile)` wrapper** (sender 0x637cd0 pushes the name at 0x637cdc). So they are "mission failed / AI hostile", not "still
  under cover" as klfedkit.c and re/fed_kit.md call them. There is **no stock hidden / revealed state** for the UCC.

## 4. Hidden vs revealed

The reveal key (P6) is not built. `klud_reveal(idx, on)` is its hook-in (one bit per crew index); until something calls it the
UCC is hidden all round, so the cap applies all round. **Coupling to watch:** if P6 is built as "the host sends
`SetUndercoverCop(false)` at round start and `(true)` at the reveal" (ucc_design.md P6 GUESS), the hidden UCC would carry NONE of the
three marks and this module would not see him. P6 must then also tell this module (call `klud_reveal` the other way round, or keep a
hook-side list of UCC crew indices replicated to every peer). Whether the cap also applies after the reveal: owner did not say
(GUESS hidden only; ask at the next check-in).

## 5. The hook point and why it is safe

| option | verdict |
|---|---|
| private vtable on the LOCAL player (wrap slot 423 0x458880) | rejected: about 20 modules identify the player by comparing its first dword with 0xbb45f4 (KLD_PLAYER_VT and twins); klnetsmooth.c keeps the local player stock for this reason |
| shooter side (the UCC's PC wraps slot 422 on remote heisters, like klnetsmooth's remote-player table) | possible but weaker: the shooter only knows the victim's replicated health and down state; a second private player table would have to be merged with klnetsmooth's |
| **rules vtable slot 15 on the victim's PC** | **chosen.** One object per machine, a pattern already shipped (klroundkeep.c), sees victim, attacker and the delta before the subtraction, runs on the PC that decides death |
| detour 0x6e3400 / 0x458880 | code patch: not allowed (CEG) |

Wrapper (`klud_w15`, `__fastcall` = thiscall + 3 stack args, callee pops 12, as the stock `ret 0xc`): when `DownOnly` is on, the
session is game type 4 sub-mode 1, both are players (vtable 0xbb45f4 or klnetsmooth's copy), the attacker is a hidden UCC and the
victim a heister: `delta = max(delta, Floor - health)` (a heal or a hit that leaves him above Floor passes; at or under Floor it costs
0). Then the stock 0x425320 runs with the clamped delta. The game afterwards only zeroes or halves it (section 2), so he keeps at
least Floor. FPU stack is empty at the call (0x6e3418..0x6e343f pop everything).

Table handling (`klud_vt_plan`, tested): stock Sv -> wait up to 3 s if klroundkeep.c will wrap it (TEST build always, SHIP with
`[Lobby] KeepRound`), then patch slot 15 INTO klroundkeep's table; otherwise our own Sv copy (and `klh_rules_vt2` = ours, so
`KLH_RULES_SV_OK` holds). Stock Cl -> our own Cl copy, `klh_rules_vt3` (new `KLH_RULES_CL_OK`, accepted by klbot.c and klnet.c).
Any other vtable (Heist, unknown copy) is left alone. Copy = 260 slots from vt-4 (RTTI locator kept); slot 15 must be 0x425320 or
nothing is installed.

What it does to the down state: a hidden UCC's would-be kill leaves a standing heister at Floor (health <= 40 %, < 20 %), so the
stock rule floors him on the next short burst (4 hits >= 20 within 1 s). A single-shot weapon may leave him standing at 1 hp: that
is what `DownOnly=2` is for (immediate down via the trigger, kind 9 = no burst / health test). A downed man shot by the UCC takes
the hit but never goes under Floor: he stays down until he presses Get Up.

## 6. Keys

```
[Ucc]
DownOnly=0      0 stock; 1 clamp; 2 clamp + a would-be kill asks the game's down trigger (GUESS)
Floor=1         least health a UCC hit leaves (0.1 .. 1000)
ForceSecs=2.5   DownOnly=2: how long the trigger is asked (every 100 ms)
Dry=0           1 = log only (the vtable copy is still installed)
Log=1           2 = every UCC hit on a heister
```

## 7. GUESSES and open points

- GUESS: a player at Floor health (1 of 550) does not die of something else in the same frame (0x6e3649 sets 0.01 x only for
  `[0x1535a2c] == 2`, co-op; the FA death branch after the subtraction was not traced: health > 0 is ASSUMED to mean alive).
- GUESS (DownOnly=2): 0x8da3b0 with a zeroed kind-9 record from the hook tick floors the local player online (klcdying.c's call,
  also untried); its gates include `[gamedata+0x4d38]` and `[gamedata+0x4d48]` bit 2, not read for an online FA session. A refusal is
  logged; he then stays up at Floor (still not killed). Attacker 0 in the record, so no name in the feed (GUESS: 0x76a450's feed line).
- NOT COVERED: kills that do not go through 0x6e3400 - close-combat executions, human-shield execution (`RMCExecuteHumanShield`),
  the kill box, a blast that bypasses it. Not read. A close-combat takedown by the UCC may still kill.
- NOT READ: whether the UCC's proxy on a third peer carries +0x2729; the hook does not depend on it (net bit 8 / score 0x80).
- Every heister's PC needs `DownOnly`; the UCC's own PC does not matter for the clamp.
- Live check (first run, Dry=1 then 1): UCC bench on DD01, the UCC shoots a heister to 0 -> expect `uccdown: ... a would-be KILL,
  kept alive` on the VICTIM's log, no death; then shoots him lying -> `(DOWN)` lines, no death; a cop finishing him still works.
