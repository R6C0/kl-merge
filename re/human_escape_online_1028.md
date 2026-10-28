# Human escape in online FA (static research, 2026-10-28)

Offline, kl2.exe read-only. Labels: CONFIRMED = read in disassembly; GUESS = inferred.

## Verdict first
- WKBC/BP benches never escaped the host because the host was never BOARDED. A human boards by HOLDING the
  use key (E) on the van's BoardingTrigger box. Teleporting into a box does nothing; no bench script pressed E.
  (WKBC3_host.ini: only `tele -6209 521 10395` + `wait 3000`, no `tap E`.) CONFIRMED.
- Boarding gives flag 0x20 and record state 4 only. Flag 0x40 (escaped) is set later, at van DEPARTURE. CONFIRMED.
  So klbf_bc_credit's test `(fl & 0x40) && !(fl & 0x0d)` is the right bits, but 0x40 appears only at the 5->7 transition.

## Mechanism (addresses in kl2.exe)
| Step | Site | Evidence |
|---|---|---|
| Human holds E on van BoardingTrigger box | PlayerAction 'EnterVehicle'; eligibility 0x40ddf0; list walk 0x6ed0b0 ([0xdd265c]+0xa20); box tick 0x65dd10 (pos +0x30, radius +0x3c, filter 0x56b530) | CONFIRMED statically; hold 2-5 s per re/playtest.md ESC3 (live) |
| Fires OnlineGamePlayTrigger type 2 (BOARDS) | 0x8d2740 slot 34: type 0 -> vtbl+0xbc, 1 -> +0xc0, 2 -> +0xb4 | CONFIRMED |
| Rules slot 45 = online boarding handler | 0x6c6c10 (vtbl 0xbd2f68). 0x6c6e22..0x6c6e30: `mov byte [edx+edi+0xc],4; push 0x20; call 0x601fd0` | CONFIRMED: rec state 4, flag 0x20 |
| Van leaves (state 5), escape recorded | 0x776ef0 called once from 0x727794 inside rules tick 0x727610. 0x777026..0x777030: `push 0x40; mov byte [ebx+0xc],5; call 0x601fd0`; then clears 0x20 via 0x514530 | CONFIRMED: rec state 5, flag 0x40 set, 0x20 cleared |
| After it | 0x887350 decides van state 7 or 8 | CONFIRMED |
| Bots | AllyEscapeBox 0x907a50 -> 0x74d7f0 -> 0x6840a0 (Arcade rules), separate path | CONFIRMED |

Flag array: S = [rules+0x2c]; word at S+0x58+0x40+4*seat. Getter 0x571750 (-> 0x4aece0), set 0x601fd0 (-> 0x4961a0), clear 0x514530.
Bits: 0x20 boarded (CONFIRMED), 0x40 escaped (CONFIRMED), others per re/bots_bank_online_1028.md remain GUESS.
Record: [rules+8] stride 0x74, state byte +0xc: 0 active, 4 boarded, 5 escaped.
Van: state byte [rules+0x1dc] (3 waiting), timer [rules+0x1d8], boarding object [rules+0x1e0].

Why the teleport to the bots' box fails: ZAllyEscapeBox is the AI route (0x6840a0), not the human's trigger. The
human's box is the van object at [rules+0x1e0] (-6209 521 10395 on F06); the AI stands at object + 500 along local x (0x8faf72, GUESS for human use).

## Is klbf_bc_credit right?
Bits yes. Timing: 0x40 is not present while the van waits; only after departure. Fix options (not applied):
accept `fl & 0x60` as "boarded or escaped" for early crediting, or keep polling after van state 7 until settlement.
Condition `!(fl & 0x0d)` stays valid (0x20 and 0x40 do not overlap it).

## Bench script (existing commands only, no .text patch)
Begin only once the van is waiting (state 3); start after the usual 50 s load wait, repeat while it waits:

    tele -6209 521 10395
    wait 500
    tap E 2500
    wait 1000
    peek rules+0x1dc
    tap E 2500

If no boarding after two tries, tele to the node plus 500 along its local x and repeat. After the van departs
(state 5 -> 7) poll the seat flag; expect 0x40 (and rec state 5). Use `pos`/`peek` to confirm record state 4 after the hold.

## Open
- Exact hold time (2-5 s live), the key mapping of 'EnterVehicle' (E), F06 box orientation/extent: not read statically.
- Whether the F06 graft's box matches [rules+0x1e0]: GUESS.
