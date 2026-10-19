# Retomoto hop 6: is there an ini-only gate "living human -> crew stays, fed human -> crew carried"? (2026-10-19)

Offline, read-only (klhop.c, klescort.c, klcrew_rt.c, KLJoin 0b557e40) plus the live Dog Days KLHook.log (read only; it still holds L94 / L96 / L97 / L101 as the sessions at 00:29, 00:45, 00:55 and 01:29 on 2026-10-19). Nothing launched, nothing written to the game folder, no klhook file edited, nothing committed.
Tags: [code] file:line (klhook/), [log] KLHook.log time, GUESS = not shown by code or log.

## 1. Answer

NO ini-only change gives both halves. The hop code cannot see a fed human at all, so "living -> stay, fed -> carry" is not expressible in KLJoin text. What an ini can do is one half:

| variant | living slow human (L101) | fed human (L96/L97) | needs |
|---|---|---|---|
| now: Player=0, Wait=150 (0b557e40) | FAIL: crew carried away at r~156 | PASS (L97: 6 of 6 out) | nothing |
| P: Player=1, Wait=150 (staged, fcfc2a7c) | PASS: hop inert while they are in the tower | FAIL: hop never fires, crew back to L79 behaviour (lift hops, GIVE UP, no leaderless carry) | the builder flag below |
| W: Player=0, Wait=240 | still pre-empted, only 90 s later | carry at r~246: too late for the van (GUESS, see 3) | `--leaderless-hop 240` |
| real gate: NoHuman (3 lines in klhop.c, re/retomoto_hop6_living.md 3.3) | PASS | PASS | 3f's file |

Recommendation: do not adopt P or W as the Retomoto answer. They only trade one failure for the other. Keep 0b557e40 for a fed-crew test setup and ask 3f for the NoHuman gate (or for the klcrew_rt.c FedAfter, retomoto_leaderless.md 5.2). P is staged because it makes the living-human run a clean experiment and because it costs nothing.

## 2. Why (the candidates from the task, checked against the code)

1. Hop 6 with Player=1 (klhop.c:416-421, 442). `passed[hi]` is set only inside `if (h->player && !passed && human)`, when the living human is nearer to To.1 than to From (3D distance), and it is sticky. The fire test is `(h->player && !passed[hi])` -> continue. So a Player=1 hop fires only after a LIVING criminal human has been nearer the street place than the tower point.
   - Living human in the tower: never nearer To.1 (From (2000, 20000, -500) to To.1 (6272, 570, -5200) is 19.4 km up). Worked numbers: boardroom loot (4750, 20996, -8): from From about 2.97 km, to To.1 20.4 km; lobby join box (2430, 19601, 510): about 1.15 km against about 20 km; rappel ledge (5940, 22766, -98): 4.8 km against 22 km. So they have not passed. Good: the hop is inert for them. When they go down by the join box they stand at (6272, 563, -6305), 1.1 km from To.1 and 19 km from From: passed, and the crew is moved by the join anyway.
   - Fed human: `kle_human()` needs the player type byte == 2 (klescort.c:491-503; a fed is type 3, the log says "type 3, police byte 1" [L94 per re/retomoto_l94.md s1]). `human` is 0, the `passed` block is skipped and the fire test still demands `passed`. So the hop NEVER fires for a fed unless the flag was already set while they lived. There is no "fed" condition, and a Player=1 hop is a living-human wait only.
2. Second hop with the same From, Player=0, gated on Stage or a longer Wait. Not possible and not useful:
   - Slot: KLV_NHOP is 6 (klhop.c:112). [CrewHop] .. [CrewHop.5] are all used in 0b557e40 and hop 6 is the sixth. There is no free slot (the `.2.off` / `.3.off` sections are never read).
   - Stage: `r->stage` of every bot is 1 at the carry in all four runs ("heist stage 1" on all 28 hop-6 lines [log 00:29:39, 00:45:53, 00:55:37, 01:29:00]). Stage is promoted by boxes in the street and the exit box (retomoto_l94.md s1), never by the human's life or death. The fed's own record stays g0. So Stage cannot tell living from fed. Stage 1 vs 0: no difference (Stage=0 is already "any").
   - Wait: only a dial (variant W).
3. Does bot position tell them apart? No. At the carry the bots stand at y 20990..21000 (boardroom, atrium, gallery), some at 20300, in all four runs: L94 fed x 1873..4979, L96 fed x -2015..2757, L97 fed x 1873..5376, L101 living x 137..4403 [log, the "hop 6: at From for" lines]. A tighter circle or a Height window would hit the fed crew as often as the living one.
4. Does a bot's `r->stage` or any bot flag change when the human is fed? Not in any log read: the stage stays 1 until the street; the only per-bot flag the hop reads (`flags & 1` AI member, `flags & 2` traitor) does not depend on the human's state.
5. `kle_human()` also returns 0 when the human's node is flagged off (bit 10: aboard, mid-teleport, in the lift; klescort.c:507). For Player=1 that only delays `passed`, never makes it early.
6. Order of evaluation, done flags: `done` is per hop and bot, set when a bot is carried (klhop.c:467) and cleared by Again. The hops are evaluated in order 1..6 and one call is made per tick (`return` at klhop.c:487). Nothing in that order lets one hop disable another.
7. FedSkip=0 (a KLHook.ini key, [CrewJoin], klcrew_rt.c:276). With it a fed who steps into the join box carries the crew at once (L94: r83, L97: about r78 instead of r156). Not recommended: it is global (all maps), the reason it was switched on (v82c) was that a fed's spawn fired the box 0.57 s after they appeared and dumped the crew mid-fight [klcrew_rt.c:276 comment, log 2026-10-17 11:09], and it does nothing for a fed who never reaches the box (L79: they entered 249 s into the round). Not part of the staged files.

## 3. Variant W numbers (GUESS)

Fed crew timeline in L94: carry r155, all stage 2 by r168, the walk to the van area took until r260-280, round end about r302 (retomoto_l94.md s0, s4). A carry at r246 leaves 56 s: GUESS not enough, the van would leave before the walk ends. For a living human W only moves the same loss to r246, after most census join times (107-261 s, retomoto_leaderless.md s3). So W is not worth a run.

## 4. What is staged

Builder: `tools/kl_rt_joinini.py` got a NEW opt-in flag `--leaderless-player` (needs `--leaderless-hop N`, refused alone). It writes `Player=1` in the appended [CrewHop.6]. Without it nothing changes: `--leaderless-hop 150` still gives exactly 0b557e40 (re-run today from the live b2bb6a2f: md5 0b557e406f311803518b2727a4083878, 0 existing lines changed).

```
python tools/kl_rt_joinini.py C:\kl_build_1019\rt_hop6_living\src_b2bb6a2f C:\kl_build_1019\rt_hop6_living\DM09_player1 --leaderless-hop 150 --leaderless-player
```

Files, all under `C:\kl_build_1019\rt_hop6_living\`:
- `src_b2bb6a2f\KLJoin.ini` = copy of the live KLJoin, b2bb6a2f7d26d73feb8486fc15d9f8d8 (read from the Dog Days DM09 folder; nothing written there).
- `DM09_player1\KLJoin.ini` = **fcfc2a7c1defde22427160538884dfbb**. Differs from 0b557e40 in exactly one line (line 654: `Player=1` instead of `Player=0`); everything else is byte-identical.

Relies on: the sticky `passed` rule above (read from code, not run); kle_human type-2 rule (read, and it matches the "fed never counts" note in retomoto_leaderless.md). GUESS: that a living human who dies in the tower AFTER r156 is then a fed with the crew still in the tower; under P that crew gets no leaderless carry.

## 5. Test recipe for the other session (hook 1019a, as L101; install the file, restore the live KLJoin b2bb6a2f afterwards; never leave P installed)

Install `DM09_player1\KLJoin.ini` as the DM09 KLJoin.ini. Everything else as in the named runs.

Run A, living slow human like L101 (PT_DM09_live_brl_slow, human NOT god mode, [Bots] keys of L101):
- Expect `grep -c "hop 6: at From for" L.log` = 0 before the human leaves the tower (L101 had 7 at 01:29:00).
- Expect the "hop 1: ... hop 6: From (2000, 20000, -500) ... player 1" line at load, and per bot "is at From of hop 6 ... carried over in 150.0 s if it stays" (the timer runs, the carry waits).
- The bots stay in the tower with them; check `grep -n "escort: record .* re-pointed" L.log` shows no 19-order tail like L101's, and `grep -n "otrace.*by=hop TELEPORT"` has no rec carried before the join.
- If they reach the street: `hop: hop 6: you are beyond it at (...): the AI heisters may follow`, then at most stragglers carried (the join has already moved the crew).
- If they die in the tower: P predicts NO hop-6 carry afterwards (fed case, section 1) and an L79-like crew (lift hops, GIVE UP lines possible). That is the cost of P, not a bug.

Run B, fed human like L97 (PT_DM09_fedvan_die_brl, same keys as L97): OPTIONAL, the code says it fails.
- Predicted: 0 "hop 6: at From for" lines (L97 had 7 at 00:55:37-40), no "you are beyond it" line, crew reaches the street only by lift hops / GIVE UP, likely no all-out escape as in L97. If instead 7 hits appear, `passed` was set while they lived (then my reading of the sticky rule is wrong; report the "you are beyond it" line's position).
- Skip Run B if the owner wants live time saved: the result follows from klhop.c:416-421, 442 and klescort.c:491-503.

Compare against: L101 (living, 0b557e40) and L97 (fed, 0b557e40) lines quoted above.

## 6. What this note changes elsewhere

Nothing was edited in re/adopt_list.md or CLAUDE.md. ADOPT 3 keeps its caveat (a slow living human loses the crew at r~156); the fix remains the NoHuman gate in klhop.c, 3 lines, re/retomoto_hop6_living.md 3.3.

## 7. Verify (2026-10-19, second reading; read-only, nothing launched, nothing written to the game folder, klhook/* untouched, not committed)

Verdict: the claim in section 1 HOLDS. There is no ini-only change that keeps the crew with a living human AND carries it for a fed one. Player=1 (staged fcfc2a7c) is only the living half. The attempt to refute it failed; each point below was re-read, not copied.

- Fed is invisible to a hop: `kle_human()` (klescort.c:491-503) returns 0 unless the player type byte (pl+0x273c) is 2; the logs (retomoto_l94.md s1) put a fed at type 3. klhop.c:414 sets `passed` only inside `if (h->player && !passed && human)`; the fire test at klhop.c:442 skips while `h->player && !passed`. So Player=1 + fed human = never fires unless they crossed while alive (sticky, never reset: grep finds no other write to `passed`). Confirmed.
- Early fire / living human: `passed` needs a < b (3D distance to To.1 less than to From). From (2000,20000,-500) to To.1 (6272,570,-5200) is about 19.4 km, so from anywhere in the tower (the numbers in section 2.1) it cannot be nearer To.1. It cannot fire early. Confirmed. If they go down alive, `passed` is set and the join has moved the crew already.
- Double carry: `done[hi][i]` is set when a bot is carried (klhop.c:467). The street places (y 570) are outside hop 6's Height 1500 around y 20000 (klv_at, klhop.c:139-143), so a carried bot is never "at From" again; Again=0. No double carry by hop 6. Hop 6 vs the join box: the join moves the crew first in the living case; a bot already in the street is not in the circle. Confirmed.
- Stall: a Player=1 hop that never fires leaves the crew where it is (L79 behaviour: lift hops 1-5, GIVE UP). That is the cost already named for run A / the fed case, not a new hang.
- Gating by Stage / position / Wait: no. Stage is 1 for all bots in all four runs, Height/Radius cannot separate fed from living (section 2.2-2.3). A second hop is impossible: KLV_NHOP = 6 (klhop.c:112), slots 1-5 are in use. GUESS (not checked): re-using one of the lift hops 1-5 for this would break its lift job.
- Builder check, re-run today from src_b2bb6a2f (staged under chk_default / chk_player next to the other files):
  - `--leaderless-hop 150` -> md5 0b557e406f311803518b2727a4083878 ("lines changed: 0"), identical to before the flag existed. Default output unchanged.
  - `--leaderless-hop 150 --leaderless-player` -> fcfc2a7c1defde22427160538884dfbb. `diff` against the default output: exactly one line (654, `Player=0` -> `Player=1`). Against the source: only the appended [CrewHop.6] block.
  - `--leaderless-player` alone is refused ("needs --leaderless-hop N").
- Not proven (needs a live run, none was made): that `passed` stays 0 for a slow living human all the way (run A), and that a fed really gives 0 carries (run B). Both rest on the code reading above.

Bottom line for the other session: do not adopt P as the Retomoto fix. Keep 0b557e40 for fed-crew tests; the real fix is the NoHuman gate in klhop.c (re/retomoto_hop6_living.md 3.3).
