# Scheduled check-in 2026-11-02 ~02:50 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll` written 02:41 UTC, repo head b0b0e22 at 02:32 UTC (c9's DM09 timing notes), the solo bench dirs
  `RT4A_DM09` / `RT4B_DM09` / `SR1A..D` written 01:59-02:41. Local sessions are benching: no game run, no install, no screen from here.
- `KLHook.result` is still the 10-27 PASS (F04); `KLHook.log` ends 10-27 20:50 (the benches log into their own inst dirs).
- Dumps: newest `KLHook_1.dmp` 10-26 08:11 and `kl2_490_crash_2026_10_25T19_18_39C0.mdmp`: both older than their triage notes.
  Nothing new to triage. `<DM>\KL_PortTools\build`: newest `carcover_1101` (11-01 20:02).
- Cloud `kl_tests`: 14 pass, 0 fail, 49 skip (no gcc-multilib in this container; the C tests are skipped, not failed).

## Finding (research, no crash): the FA lobby's row order and the DOWN count to "Heist time" are now CERTAIN
Why: c9's `re/dm09_timing_1102.md` (b0b0e22) wants RT5 to run DM09 with a 6-minute heist time, and its host-script step was a
GUESS ("DOWN x N to the Heist time row, row order unverified, run once with windows + screenshots first"). A wrong N would
step Number of players or Number of rounds instead and burn a two-seat bench.

Read statically from a staged copy of `kl2.exe` (debug/dasm.py on `ZMercsFASelectorLobby` slot 10 = 0x7dc060, its open 0x6a9830,
the LEFT / RIGHT jump tables 0x7dcfa8 / 0x7dcfc0, Ready 0x5a9920):
- focus row `[self+0x88]`: -6 co-op level, -5 co-op difficulty, -4 FA level, -3 players, -2 Heist time, -1 rounds, 0..n-1 the player list.
- the FA lobby OPENS on -4 (0x6a9830: 0x87c980 false -> -4; the co-op lobby starts at -6).
- `0x7b` DOWN = row + 1, `0x7c` UP = row - 1, clamped to -4..n-1; LEFT (0x7d) / RIGHT (0x7e) never move the row; SELECT (0x7f) = Ready
  does not read the row. Every option change is gated by host-in-lobby (0x8e6a20 == 0xd) and a non-zero `MP_RankedGame` lookup in the
  menu store, the same two gates the SL7 run (time row stepped live) and the maps9 scripts (DOWN DOWN reached Heist time) passed.
- So: DOWN, DOWN = Heist time; RIGHT, RIGHT = 4 -> 5 (stock) -> 6 (kllobbyopt, TimeMax=10 is in the RT4A ini); no UP needed before Ready.
  Expected log lines: `lobbyopt: Heist time 5 -> 6 (the stock clamp would have kept 5)`, `lobbyopt-test: session state 13 -> 18: time sm=6 min`.
- `[Lobby] TimeMin=6` cannot do it: the floor only limits LEFT, the lobby default stays 4 (c9's note already says so).
Written into `re/lobby_options.md` ("Row order and keyboard navigation") and the RT5 section of `re/dm09_timing_1102.md`
(plus: klauto's `[Script]` loader stops at the first missing number, so the insert after step 43 needs the later steps renumbered).
`tools/kl_maps9_1026.py` comment: GUESS -> CERTAIN.

## Tooling
- `tools/kl_port_check.py find()`: `KL_DD_DIR` / `KL_DM_DIR` env override, so `debug/dasm.py` and the other kl.py users run in a
  cloud session on a staged `kl2.exe` without editing DD_GUESSES (it exited "Dog Days not found" before). Guesses unchanged otherwise.

## Owner
- Nothing to install or decide. RT5 (6-minute DM09) is c9's bench to run when the game is free; its script step is no longer a guess.
