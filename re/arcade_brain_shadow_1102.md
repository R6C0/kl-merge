# Arcade brain online: the shadow rules contract (reads of 2026-11-02 ~23:00, scheduled check-in)

Answers section D (critic) items 1 and 6 of `re/arcade_brain_online_1102.md`: which of the "unread" functions were
in fact already read in `re/`, what the two that were not (Board RUN, the traitor bit routine) touch, and the exact
fields a shadow `ZGameRulesHeist` block must hold for each tactic. Everything below is CERTAIN (read in the
disassembly of the owner's `kl2.exe`, sha1 9d99e01d, or in the live `KLHook.log`) unless marked GUESS. Nothing was
run, built or installed; the hook code (c9's `klbrain.c`) is not touched here.

## 0. Item 1 is answered: `[sm+0x5c] == 4` online. No probe needed.

`[sm+0x5c]` (sm = `[0x168e598]`) is the GAME TYPE word, not an Arcade flag. The hook has read it as "4 = Fragile
Alliance, Arcade or online" for weeks: `klsteam.c:401` logs it as `game mode %lu` on every session state change, and
today's live log (owner's online rounds, F06 `OnlineSet=9` at 20:28, System Link) shows `session: state .. (game mode 4)`
153 times and `game mode 0` only after the session ends (0x2e -> 0x0). `klr_online_host()` (`klbalance.c:1579`) and
`klbotfill.c:793` gate the graded online features on `+0x5c == 4 && role == 2`, so the value is proven online.
It is compared with 4 at 90 sites and with 2 at 27 sites in `.text` (scan of `mov r,[0x168e598]; cmp [r+0x5c], imm8`).

Consequences for the frame of stage 1b:
- The frame needs to write ONLY `[sm+0x54]` (role) := 0 and `[G+0x54]` := shadow. `[sm+0x5c]` is already 4.
- `0x7f6850` (jump table on `[sm+0x54]`: roles 0 and 1 and >3 -> `[sm+0x5c]==4`; roles 2 and 3 -> false) becomes
  true in the frame. `0x508ef0(G)` = `[sm+0x5c]==4 && 0x7f6850() ? [G+0x54] : 0` returns the shadow.
- `0x7bb2a0(G)` = `[sm+0x5c]==4 ? [G+0x54] : 0` has NO role test. OUTSIDE the frame it returns the online Sv rules
  object (wrong layout). Nothing in the Board tactic reaches it outside the frame (both test and run go through
  `0x508ef0` first and the test returns 0.0 on NULL at 0x4fafb3), but a wrapper that calls the original Board RUN
  without the frame would crash: run has no NULL check (`0x82f98a mov eax,[edi]`). Rule: the originals of Loot, Board
  and Traitor evaluate/run are called inside the frame or not at all.

## 1. The "unread" list of item 6, resolved

| address | what | already read in | new here |
|---|---|---|---|
| 0x82f970 | `ZBoardEscapeVehicleTactic` slot 2 = RUN (vtable 0xbd0dd4 +8) | only its 300-unit branch (`boardall_review_exe.md` 154-157) | whole, section 2 |
| 0x43ffb0 | traitor roll ("traitors allowed", tuning row +0x6c) | `balance.md` 314, 425 (field only) | whole, section 3 |
| 0x46d4d0 | traitor limit float (tuning row +0x20) | `balance.md` 314, 423 | whole, section 3 |
| 0x4322f0 | Traitor RUN's bit routine on the rules | nowhere | whole, section 3 (odd code) |
| 0x5dd890 | `SetStage(activator, n)` = `rec+0x78 = max(rec+0x78, n)` | `boardall_review_exe.md` 65-68 (whole) | the record test, section 4 |
| 0x8b94d0 | `ZGameRulesHeist` slot 202 (0x328) loot candidates | `bots_loot.md` 177-186 (line by line) | nothing to add |

Also decoded (small, used by all three tactics): `0x7fd930(idx)` = `[rules+0x348] + idx*0x7c`, no bounds check;
`0x78f470(rules, actor)` section 4; `0x6c7700(player)` section 2; slot 75 (0x12c) `0x5d52f0` = `movzx byte [rules+0x1dc]`
(van state); slot 76 (0x130) `0x63b300` = `fld [rules+0x1d8]` (countdown seconds).

## 2. Board RUN 0x82f970, whole (0x82f970..0x82fc1d; `this` = tactic, `[tactic+4]` = soldier, `[soldier+0x40]` = actor)

```
G = 0x508ef0([0x168e9e4])                 rules (shadow in the frame); NO null test
switch (G->vt[0x12c]() = van state byte +0x1dc)      jump table 0x82fc20: 1,2 -> A; 3,4 -> B; 0 or >4 -> DONE
A (van called, not yet there):
    R = 0x7bb2a0([0x168e9e4])             = [G+0x54] when [sm+0x5c]==4, else NULL -> 'mov edx,[eax]' at 0x82f9b2 faults
    if (R->vt[0x130]() /* countdown +0x1d8 */ >= 2.0 (0xb5c828))  -> DONE      (fcomp; jnp = 'under 2 s or NaN' -> B)
    else fall into B
B (go to the vehicle):
    pos = 0x8d3150(actor)                  the actor's node origin
    if (!0x5aeb00(G, &boardpos)) return    = [G+0x1e4] != 0 && [G+0x1e0] != 0, then 0x7b3020([[G+0x1e0]+4], out)
    d2 = |boardpos - pos|^2 (0x455b40 diff)
    if (d2 <= 90000.0 (0xd19a28; 300 units)):
        idx = 0x78f470(G, actor); 0x74d7f0(G, idx)      -> rules vt[0xb4] = 0x6840a0, the boarding rule (bots_board_reach_review.md 20)
        return
    path: nav = [[[0xdd2640]+0xac]+0xc]; nav->vt[0x7c](pos -> node), nav->vt[0x7c](boardpos -> node), nav->vt[0x60](&req)  (req at ebp-0x70, flags 0/1/-1)
    if (path nodes [ebp-0xb8] <= 1) -> DONE
    waiting = (G->vt[0x12c]() == 4)
    lp = 0x660b00([0xdd265c], 0)           the LOCAL PLAYER object
    i  = 0x6c7700(lp)                      = 0 when 0x7f6850() (Arcade / in the frame); else [lp+0x2748] ? 0x5970e0(it) : -1
    lpboarded = (0x7fd930(G, i)->+0x10 == 4)        <-- reads shadow record i = 0 in the frame
    [actor+0x57e] &= ~0x40
    if (0x6d9eb0(soldier) /* may act */ && !waiting && !lpboarded)
         order = soldier->vt[0x74](&goal, soldier, 0.0)         (walk)
    else order = 0x8997a0(&goal, 0, 0.0, 1.0)                   (hurry)
    0x521350(tactic, order)                push
    if (!0x55b9f0(tactic) && 0x7b0b70(soldier)) { 0x630b50(tactic, 0.5 (0xba312c)); if (!0x55b9f0(tactic)) DONE }
    0x4bdda0(&req)                         free the path request
DONE: tactic->vt[0x30]()                   pop / finished
```

Rules touches, complete: `0x508ef0`, `vt[0x12c]` (+0x1dc), `0x7bb2a0` then `vt[0x130]` (+0x1d8) in states 1/2 only,
`0x5aeb00` (+0x1e4, +0x1e0 -> boarding object), `0x78f470` (+0x354, +0x34c, +0x348 table), `0x74d7f0` (vt[0xb4]),
`0x7fd930(0)` (+0x10 of record 0). Everything else is pathing and orders on the soldier.

What this means for the shadow (stage 2 of the plan):
- **Record 0 is the local human**, not a bot. `0x6c7700` returns 0 inside the frame for any player, and `0x5dd890`
  with a ZFFPlayer activator writes record 0 too. Register bots at 1..11 and mirror the host human's boarded status
  into shadow record 0 `+0x10` (4 = boarded) or Board RUN picks the wrong walk mode; nothing else reads record 0.
- Shadow `+0x1dc` (van state) must stay 0 until the online exit is mirrored, then jump to 3 (waiting at the door) or
  4 (boarding). Values 1 and 2 are the only ones that reach `0x7bb2a0` + `vt[0x130]` (test 0x4fafe6 and run
  0x82f9ad); with +0x5c == 4 they are safe, but they give nothing: under 2.0 s the bot walks to a door the shadow has
  no object for yet (`0x5aeb00` false -> return). Keep the Heist originals for slots 75 and 76; they read +0x1dc / +0x1d8
  of whatever `this` is, so the shadow's own bytes.
- `+0x1e4` and `+0x1e0`: `0x5aeb00` needs both non-null and calls `0x7b3020([[+0x1e0]+4], out)` for the position. The
  online exit object is `klbf_ot_trig`'s owner (klbotfill); GUESS that its `+4` is the same node pointer the Heist
  escape box has. Cheap check: log `[[+0x1e0]+4]` on Arcade vs `[[klbf_ot_trig]+4]` online before wiring it.
- `0x74d7f0 -> 0x6840a0` is the boarding rule already called by the hook's `klmv_ally_reach` with the REAL online
  rules (`bots_board_reach_review.md`): inside the frame it would run on the shadow (session state 0x19, vehicle state,
  grace time...). Stub slot 45 (0xb4) in the shadow vtable as the plan says; do not let the Heist 0x6840a0 run on the shadow.

## 3. Traitor: the three small routines, whole

`0x46d4d0(rules)` (called by Traitor EVALUATE 0x79b7c0 at 0x79b94e): `lvl = clamp([[rules+0x5f8]+0x45], 1, 11)`;
returns float `[[0x168d7c0] + lvl*0x70 + 0x6cc]` (the tuning row's +0x20 = "traitor limit", balance.md 423).

`0x43ffb0(rules)` (0x79b823): `lvl` as above; `ok = ([rules+0x338] < int [[0x168d7c0] + lvl*0x70 + 0x718])` (row +0x6c,
"traitors allowed"); `p = lvl<=2 ? 0.05 : lvl<=5 ? 0.10 : lvl<=7 ? 0.30 : 0.40` (0xb39e08 / 0xb4c788 / 0xb26690 /
0xb6fe50); advances the game's LCG `[[0xdd2640]+0xb30] = x*0x10dcd+1`; `r = ((x>>8)&0x7fff) * 2^-15` (0xb59200);
returns `ok && r < p`. So one roll per evaluate, chance by level band, capped by the count at +0x338.

`0x4322f0(rules, char slot)` (Traitor RUN 0x488eb0: `rec = 0x7fd930(G, [tactic+0x14]); rec+0x79 |= 2; 0x4322f0(G, slot)`),
bytes `53 56 0f be 74 24 0c 57 8b c1 8a 90 3c 03 00 00 8b ce bf 01 00 00 00 d3 e7 0f be ca 0b f9 75 06 ff 80 38 03 00 00
b3 01 8b ce d2 e3 5f 5e 22 da 88 98 3c 03 00 00 5b c2 04 00`:
```
m = (signed char)[rules+0x33c]; bit = 1 << slot
if ((bit | m) == 0) [rules+0x338]++          never true for slot 0..31: the OR has bit set
[rules+0x33c] = (byte)(1 << slot) & (byte)m   keeps ONLY the slot's own bit of the old mask (0 for slot >= 8)
```
Read as written, the counter is never incremented here and the mask is narrowed, not widened. GUESS: the source meant
`if (!(m & bit)) count++; m |= bit;` and this is what shipped; the only `inc dword [r+0x338]` in `.text` is this one
(six other `mov [r+0x338], ..` sites are on other classes). For the shadow it does not matter: give it `+0x338` (int)
and `+0x33c` (byte), zeroed, and read them back for the ledger; the flip itself is `rec+0x79 bit 2`, which the stage-3
bridge should mirror to the online traitor state. Open: whether anything in Arcade reads +0x33c except `0x6ae750`
(the voice table index `byte[rules+0x33e+slot]`, bot_voice_online_spec.md 15, a different byte).

Traitor EVALUATE's other reads (from the plan, not re-read here): `0x7f6850` (true in the frame), `[rules+0x5f8]`
score block (`+0x45` level, `+0x150+4*i` money, `+0x1d4+4*i` flags), `vt[0xe0]` (slot 56 money getter, Heist original
0x6f86c0 kept). The shadow needs a real `+0x5f8` pointer to a block of at least 0x1d4+4*12 bytes.

## 4. The shadow crew table, exact (from 0x78f470, 0x7fd930, 0x5dd890)

| field | type | meaning |
|---|---|---|
| `[rules+0x348]` | ptr | record array, stride 0x7c |
| `[rules+0x34c]` | ptr | one BYTE per record; **0 = record live / usable**, non-zero = skipped by 0x78f470 and refused by 0x5dd890 (so "in-use byte" in older notes means "0 when in use") |
| `[rules+0x354]` | int | record count (loop bound of 0x78f470 and range test of 0x5dd890) |
| `rec+0x04` | ptr | the actor (`0x78f470` matches `[rec+4] == actor`, only when `rec+0x79 & 1`) |
| `rec+0x10` | byte | status; 4 = boarded (Board RUN, record 0 = local player) |
| `rec+0x15 / +0x18 / +0x1c` | byte / time / ptr | grab state, stamp, object (rules update 0x727cb0; untouched by the tactics) |
| `rec+0x78` | byte | stage, monotone max (0x5dd890) |
| `rec+0x79` | byte | bit 1 = registered AI record, bit 2 = traitor (Traitor RUN) |

`0x78f470(rules, NULL)` returns 0xff at once; `0x7fd930` indexes blindly: a bot must have its record before the first
evaluate (plan, confirmed), and the LOCAL PLAYER needs record 0 live (`+0x34c[0] == 0`) with a sane `+0x10`.

## 5. Still open (not read this run)

`0x8d2740` (the three other callers of 0x5dd890: the gameplay trigger kinds, stages 1/2/3), Traitor EVALUATE 0x79b7c0 in
full, Loot RUN 0x7bc7d0's pathing tail, `0x6d9eb0` (may act), `0x5970e0` (player seat index online, used by 0x6c7700
outside the frame only). None is on the stage-1 path.
