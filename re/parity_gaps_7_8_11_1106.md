# Parity gaps 7, 8, 11 - static research, 2026-11-06

Tags: CERTAIN = read in code or log; LIKELY = traced but not run; GUESS = untested idea.
Nothing here was run in the game. Source plan: re/bot_parity_plan_1028.md (stale for 7 and 11).

## 1. Status truth table
| Gap | Plan says | Truth |
|---|---|---|
| 7 bot looks/voice to clients | not built | CERTAIN: built. KLSYL (looks) and KLSYV (voice), hook-to-hook UDP 27415, keyed by the group digit 2..8 of Glazer_Bodyguard_0N. Benched: OnlineLooks=1 (LOOKS2), OnlineVoice (VOX2, bs63/bs65). |
| 8 online bot names | not built | CERTAIN: no native name exists for bots. Only the hook overlay names them, derived locally from the model each peer sees. Open item: native (non-overlay) path, probably not worth it. |
| 11 crew follows Retomoto jump | Arcade only | CERTAIN: klcrew_rt.c is Arcade only. LIKELY: online route is [CrewHop] Online (klhop.c, host-only carry). DM09 proof RT1 failed, fix d4fd5f8fc, RT2 3/3 exit 0 (DM09 RT2L PARTIAL: 51 legs, 4 real carries; open_work_log 2026-11-01 ~23:45). |

## 2. Gap 7
- CERTAIN: carrier exists and passed benches. Look model root is [[actor+4]+0x68].
- LIKELY: the packet keyed by digit is order-independent, so census order does not matter.
- GUESS: a seed carrier (deterministic seed from shared session fields + round + digit) would remove the UDP packet. Not needed now.
- Open: stock-map gate (every feature must also work on the 9 stock FA maps) and round-2 re-apply are unconfirmed.

## 3. Gap 8 (kl2.exe trace)
- CERTAIN (addresses): 0x841e50 crew record name getter; 0x7d16f0 entry display name; 0x6f3000 list block; 0x7f6850 mode-4 test.
- LIKELY: in mode 4 the display name comes from the crew record; otherwise 0x7440b0(arg) returns the pointer it was passed (online: the client struct m_szName, humans only).
- CERTAIN: bots have no client struct, so a native name needs an injected record. Not small or safe. Overlay (klhud_names.c, klonline_read.c) stays the route.
- Consequence: peers agree on a bot name iff they hold the same model root for the digit. This is what the probe checks.

## 4. OnlineNamesProbe (new, implemented)
Files: klhook/klnamesprobe_logic.h (pure), klnamesprobe_test.c (27 checks), klnamesprobe.c (hook tick), 2 lines in klhook.c, kl_tests.py entry, KLHook.ini block.
Log only: no game write, no packet, no patch. Gate: role 2/3, mode 4, state 0x13..0x1e.

ini lines (default off, recommended off):

    [BotFill]
    OnlineNamesProbe=0     ; (recommended off) 1 = log one "botfill: names:" line per seat

Log line: `botfill: names: HOST|CLIENT n=7 digest=1a2b3c4d: 2=Kane 3=- 5=Liam`. Digest is FNV-1a over entries sorted by digit, so census order is irrelevant. '-' = no wardrobe name, '?' = unreadable digit.
Grading: per round, the last digest on the host and on every client must be equal (with OnlineLooks=1). A mismatch shows which digit differs in the list text.

## 5. Gap 11
- CERTAIN: klcrew_rt.c header says Arcade only; klhop.c is the online carry.
- Online needs beyond Arcade (LIKELY): private-table vs ZFFActor check (klt_refuse read the raw vtable while OnlineCopToBot had bots on the private table, 17x "not a ZFFActor"), van object standing from the start (`!van` switched legs off).
- Remaining: DM09 RT2L PARTIAL, and no cop squad follow online.

## 6. Smallest-first plan
1. (done) NamesProbe, then bench it: 2-seat then 9-seat, compare digests.
2. Confirm round-2 look re-apply and stock-map behaviour from the same bench logs.
3. DM09 RT2 rerun with the d4fd5f8fc fix to move RT2L from PARTIAL to PASS.
4. Only if the probe shows digest mismatches: investigate the model-root mismatch before touching names.
5. Native bot names: skip (GUESS: large, low value).
