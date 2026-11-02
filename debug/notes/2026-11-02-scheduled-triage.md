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

# Scheduled check-in 2026-11-02 ~06:55 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll`, `ReShade.log` and `ReShadePreset_KLLive.ini` written 06:51 UTC (a bench was running as this check-in
  started); origin head 8165496 at 06:45 UTC (ce's shoppic merge), 8 commits between 06:07 and 06:45. No game run, no install, no screen.
- `KLHook.result` still the 10-27 PASS (F04); `KLHook.log` ends 10-27 20:50 (benches log into their own inst dirs).
- Dumps: newest `KLHook_1.dmp` 10-26 08:11 and `kl2_490_crash_2026_10_25T19_18_39C0.mdmp`, both older than their notes. Nothing to triage.
- `<DM>\KL_PortTools\build`: newest `carcover_1101` (11-01 20:02). (`hasta_e11nests_1018` is a dangling symlink there; harmless.)

## Finding (self-test, no crash): klstackdiag_test FAILED on Linux, a host-dependent off-by-one in ksd_fmt
First cloud run of the 32-bit C tests on today's head (gcc-multilib installed here): `kl_tests` 54 pass / 1 FAIL / 15 skip.
`klhook/klstackdiag_logic.h` (4ebe301, wk-scorefix-1102, included by klbotfill.c) called `_snprintf(out, cap - 1, ...)` and then
`out[cap - 1] = 0`. MSVC `_snprintf` writes cap-1 characters with no terminator when it fills the count, so cl gives cap-1 characters;
C99 `snprintf` (the shim's `-D_snprintf=snprintf`) terminates inside the count, so Linux gave cap-2 and the "truncated and
terminated" check (expects 11 of 12) read 10. Fix: count = cap, terminate at cap-1, the pattern klgrades.h / klshot_logic.h already
use, identical output on both hosts. Live effect: none (the caller passes a 96-byte buffer, the text is < 70 characters; log only).
After the fix: 55 pass / 0 fail / 15 skip (the 15 are SDK-only or need real audio files).
`tools/run_harness_linux.sh --check-hook` (MinGW -fsyntax-only, SHIP + TEST): 0 errors; warnings are unused variables, the two
stubbed naked forwarders and MinGW not knowing `%I64d` (klslot.c:414, correct under MSVC). pyflakes on the 66 tools/debug .py files
changed since 10-25: no undefined names or syntax errors.

## Owner
- Nothing to install or decide. The fix is header-only; it reaches the DLL at the next build the local sessions make.

# Scheduled check-in 2026-11-02 ~10:50 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll` written 10:48 UTC, ReShade logs 10:49, repo head 66fe9ee (ce's OnlineVoiceByLook merge) committed 10:49:31
  UTC = the second this run started; ce pushed 11 commits between 09:19 and 10:49. No game run, no install, no screen from here.
- `KLHook.result` = the 10-27 PASS (F04). Dumps: newest `KLHook_1.dmp` 10-26 08:11 - nothing newer than its triage. `<DM>\KL_PortTools\build`:
  newest `carcover_1101` (11-01 20:02). Live `KLHook.ini` (11-01 13:25, md5 d829fe43): `--check-live` clean (no half-on row, no clash;
  2 tuned values FollowOutHold 45, 1 owner row [Lobby] TimeMax).
- Verification of head 66fe9ee in the cloud: `kl_tests` 55 pass / 0 fail / 15 skip (gcc-multilib); `run_harness_linux.sh --check-hook`
  SHIP + TEST 0 errors, the 15 baseline warnings; kl_mod_options `--check-defaults` / `--check-ini` / `--check-rec` clean, test 69/69;
  pyflakes on the 2 .py changed since 06:45: unused locals only.

## Review (static, no crash shape found): ce's two newest hook changes
1. `[Bots] OnlineCrewHealth` (0b5beda, klgrudge.c kly_online_tick, klbotdown.c view slot 3): the writes and the put-back are the Arcade
   kly_health2 / kly_undo path with every guard kept (vtable, health object +0x24 = actor, finite, max 1..100000, exact hwrote match before a
   put-back). Round end / host loss -> undo through `klyo.rules` (set on the first hosted tick); the extra `b[0..3].actor` test in that
   condition is redundant, not wrong (KLB_NREC is 32: if `rules` were ever 0 while hosting, slots 4+ would keep the scale until the next
   view change - the view always hands a non-zero rules object today). Game thread only, data writes only, no .text patch: SHIP-safe shape.
   What only the bench can say: whether the HOST's health object prices a CLIENT's hit (the GUESS in the commit).
   FOUND (doc / combination, not code): the ini line of 629de8d said "do not combine with [Balance] Tough (two writers of one maximum
   stack undefined)". Online, Tough never writes a maximum: klbalance.c klr_tough_tick is the Arcade dial, and online `[BotFill]
   OnlineBalance=1` reads [Balance] Tough as a DIVISOR on every hit on a bot (klr_bo.tough, klbalance.c 1681 / 1282). So the real clash
   is OnlineCrewHealth x OnlineBalance+Tough = a double count (1.5 x 1.5 = 2.25 x the bullets), silent in the log. Ini line corrected.
2. `[BotFill] OnlineVoiceByLook` (216d5f0 + 6dbaa5a, klbotvoice.c klbv_look_key): loot line only, gated on the look APPLIED on this seat
   (klcl_t.a[].last 1 / 4 and the current epoch), name through klcl_bot_name + kvo_name_of, key bounded (_snprintf + cap-1), falls through
   to the digit key when klk_say returns 0. No packet change, no new write. Nothing to fix.

## Tooling: `kl_mod_options.py --check-live` now knows 'do not combine' (avoid rules)
Until now the two 'do not combine' sentences lived in comments only (the ini, klhud_names.c) and nothing read a finished ini for them.
- Rows take `avoid=[(why, [(sec, key, offvals), ...]), ...]`: the row is on and EVERY listed key is live at a value not in offvals ->
  a CLASH line, exit 1 like a half-on row (`--check-live`), `CLASH ...` in kl_solo_test's `ini-check | instN` lines. Values are read as
  floats (`_live_num`): `Tough=1.5` was 1 to get_int, i.e. 'off'.
- Rules: `crewhealthonline` vs [BotFill] OnlineBalance (not 0) + [Balance] Tough (not 0 / 1) - the double count above; `hudnametags` vs
  [Crew] Names (not 0) - klhud_names.c stands down ("two writers of one string: klcrew.c wins"), so the row did nothing.
- kl_mod_options_test +8 (77/77; the repo ini and the live ini have no clash). check_live returns a 4th list: both callers updated.

## Owner
- Nothing to install or decide. Still open from earlier notes: Medal-quit stutter round, MouseMoveMs=16, lenscrack INSTALL bat if wanted.

# Scheduled check-in 2026-11-02 ~15:00 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll` written 15:00:04 UTC (the second this run started), ReShade logs 14:51-15:00; ce's solo bench dirs
  `ES3B_DM03` 14:41, `CO3A_DD05` 14:50 (both seats RESULT PASS, F05), `CO3B_DD05` 14:59, `Q35_DD01` 15:02 (c9's 21-map pass running).
  No game run, no install, no screen from here.
- `KLHook.result` = the 10-27 PASS (F04); `KLHook.log` ends 10-27 20:50. Dumps: newest `KLHook_1.dmp` 10-26 08:11 and
  `kl2_490_crash_2026_10_25T19_18_39C0.mdmp`, both older than their notes. Nothing to triage. `<DM>\KL_PortTools\build`: newest
  `carcover_1101` (11-01 20:02); the live benches write under `build\klhook\solo\`.
- Live `KLHook.ini` unchanged (11-01 13:25, md5 d829fe43). The bench inis' `HALF-ON: netsmooth` line in run.txt is the probe
  ([NetSmooth] Enable=1 Log=1 Probe=1 without CamYaw) - the live ini has no [NetSmooth] section at all; not a ship concern.
- Verification of head f2d8483 in the cloud (gcc-multilib + mingw installed): `kl_tests` 57 pass / 0 fail / 15 skip (klcensus_test and
  klway_test new since 10:50); `run_harness_linux.sh --check-hook` SHIP + TEST 0 errors, the baseline warnings; kl_mod_options
  `--check-defaults` / `--check-ini` / `--check-rec` / `--check-live` clean, test 77/77; pyflakes on the 2 .py changed since 10:50:
  unused names only (removed in kl_coverdump_parse.py below).

## Review (static, no crash shape found): ce's hook commits since 10:50
1. `OnlineTriggersCensus` pointer set (f38a0d1 + b0b1cbd, klcensus_logic.h): 2 x 256 DWORDs of static storage, no allocation, `kcs_add`
   bounds-checked (over flag, 'upper bound' in the line). Order in klbf_ot_run is walk -> klbf_trig_tick (arms with GetTickCount, copies
   the walk's set as the base) -> klbf_cen_tick, so the +10 / +30 s tallies always come from a walk that ran with st != 0 against that
   base; the arm tick itself tallies nothing (st was 0 during its walk) - correct. The `(LONG)(now - t0) < 0` guard covers the arm's
   newer GetTickCount. Round reset clears cur / base / tally. Log only. Nothing to fix.
2. `OnlineLateExitRoute` (878f968, klway_logic.h kwy_route_cm / kwy_late_s): pure arithmetic, clamped 400 s, never below the base,
   `klbf_late_for` returns the plain OnlineLateExit when off / no exit / route unknown. Every `klbf_ot_late` use in the pick loop became
   the per-bot `late_s` (doorhold clock clause, idle-van late clause, late exit, partial hold) - consistent. Design consequence worth
   knowing for rt9: on a 370 s clock with a 310 m route, late_s ~258, so the idle-van clause (`left <= late_s + 20`) can send a stackless
   bot to call the van from ~92 s into the round; ce's commit text already expects looting to end around t=112 s. Default off, NOT Arcade.
3. `klbv_event(s, 1)` on the timed-parts grab (f2d8483): the same call the lump path makes; no new read or write.

## Done (hook: TEST-default feature, read-only; parser + test): [CoverDump] RoundEnd
c9's SN2 follow-up ("the compare should pair dumps by time, or dump again at round end"): the load dump is taken ~2 s after the list
settles at the round start, and the car cover rings (CoverRing) are built mid-round IN PLACE (SPARE points pos 0 -> built, the count
stays), so the host's one dump at 11:08:32 lacked car #0 and the compare said DIVERGE / client-only 8 for a difference that was only time.
Pairing dumps by time cannot fix a log that holds one dump, so:
- `klhook/klcoverdump.c`: `[CoverDump] RoundEnd=1` (TEST default on, SHIP off, like Enable) dumps the POINTS again when the session
  state leaves 0x19 (not 0x16, that is the new-load re-arm) after the load dump finished, at most `RoundEndMax=4` times a load. The
  begin line carries `ROUND END (points only ...)` plus one explanation line; no rec / near / full / finder repeat. Same `kcvd_read_list`
  + guarded reads, no write, the existing __try. Both seats see the round end within a second, so their last dumps describe one moment.
  `--check-hook` 0 errors. NOT RUN in the game: the next TEST dll build carries it; the first two-seat bench with it should show
  `coverdump: begin ... ROUND END` on both seats at the round end and the compare read "the round end" dumps.
- `tools/kl_coverdump_parse.py`: `read_dumps()` lists every dump of a log with its kind (load / round end) and time; `read_dump()` =
  the last COMPLETE dump (a round-end dump cut by the game's exit would otherwise show every unreached index as unbuilt = false
  one-sided points); `--compare` prints a `dumps` line per log naming which dump it read, and a NOTE when a load dump meets a
  round-end dump. `kl_coverdump_parse_test.py` 29 checks (was 16): SN2 shape with RoundEnd on both seats = IDENTICAL, cut-short
  fallback, labels, the compare lines.

## Owner
- Nothing to install or decide. Still open from earlier notes: Medal-quit stutter round, MouseMoveMs=16, lenscrack INSTALL bat if wanted.

# Scheduled check-in 2026-11-02 ~18:50 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: `<DD>\dinput8.dll` written 18:44:25 UTC, ReShade logs 18:44-18:45 (a game run in progress); ce's bench dirs under
  `<DM>\KL_PortTools\build\klhook\solo\`: MT3B_DM03 18:04, RT9A_DM09 18:15, RT9B_DM09 18:27, RT9R_DD06 18:35, TP3A_DM03 18:44,
  TP3B_DD05 18:51. No game run, no install, no screen from here. Nothing pushed to rtp-schemas since 15:13 (head dda3479).
- `KLHook.result` = the 10-27 PASS (F04); `KLHook.log` ends 10-27 20:50; live `KLHook.ini` 11-01 13:25 (sha1 81c95751) unchanged.
  Dumps: newest `KLHook_1.dmp` 10-26 08:11 and `kl2_490_crash_2026_10_25T19_18_39C0.mdmp`, both older than their notes: nothing to triage.
- Head dda3479 verified in the cloud (fresh container: gcc-multilib + mingw-w64, pefile + capstone): `kl_tests` 57 pass / 0 fail /
  15 skip; `run_harness_linux.sh --check-hook` SHIP + TEST 0 errors; `kl_mod_options_test` 77/77.

## Finding: Q35 = the 21-map pass of the next-ship candidate is COMPLETE and CLEAN (c9's ship gate)
Q35 ran 15:08-17:55 UTC (c9_1028/q35, `ship_next/dll_0925/test` sha1 eb4c46d8 = the TEST twin of SHIP 56ac45c1, KLShopPage.ini staged:
'shopPage: on; 20 pairs' on every seat). All 21 run dirs, both seats: state=PASS, level_loaded=1, asserts 0, faults 0, soft_asserts 0,
run.txt 'RESULT: inst1 IN ROUND, inst2 IN ROUND'; slots as intended (DD10 and DM03A on F07, DM01B on F03, DM05A on F01, DM06B on F02,
DM07 and DM09 on F06, DM11B on F04). The only ini-check line is the known `HALF-ON: netsmooth` probe (not in the live ini).
So the candidate (ship_next: ship1103 + the 13 cleared keys incl. the CoverRing trio + the 6 audit ADD keys + Carry 8 / BoardAllNear /
DropTake) has the both-seat PASS on every map that the 12:45 audit asked for. SHIP = c9 / owner (INSTALL bat from c9_1028; not from here).

Also graded from the result files (feature verdicts are ce's): MT3B_DM03, RT9A/RT9B_DM09, RT9R_DD06, TP3A_DM03, TP3B_DD05 all
SAFE (both seats PASS, 0 asserts / faults / soft). RT9A (OnlineLateExitRoute=1) host log: 'route to the exit 315 m ... late exit at
clock left 262 s instead of 75' = the 15:00 note's ~258 s; the van was called by five bots 18:08:43-18:09:26 (the first ~70 s after
the round start), round summary 0 boarded, 13 stacks, $1.2M tally, 5 'dead or gone'; RT9B (control) 0 boarded, 14 stacks, $0.6M,
6 dead. The per-bot late exit changed the timing, not the outcome: DM09 boarding is still the street-leg survival / walk problem.

## Done: `kl_kit_summary.py --batch PREFIX [KITDIR] [--gate]` (the one-command ship gate; read-only, self-tested)
Until now 'all 21 maps both seats PASS' was read by hand (21 run.txt + 42 KLHook.result files). Now one line per `<solo>/<PREFIX>*`
run dir from the two seats' KLHook.result (state, level_loaded, asserts, faults, soft_asserts; a missing file or seat = NOT clean),
the scene's Fxx, the run.txt RESULT line, and a verdict line `BATCH Q35_: 21 run(s), 21 clean -> CLEARED` or the names of the
runs that are not; with KITDIR the scene slot is checked against the maps_*.txt line; `--gate` exits 1 unless every run is clean
(for a ship script: `python tools/kl_kit_summary.py --batch Q35_ C:/kl_build_1024/c9_1028/q35 --gate && INSTALL...`). Older hooks
without soft_asserts= are not penalised. Ran on the PC against the real solo dir: Q35_ 21/21 CLEARED, RT9 3/3, TP3 2/2.
kl_kit_summary_test: +18 checks (wrong slot, client soft asserts, host crash + missing client file, run.txt verdict, old hook).

## Owner
- Nothing to install or decide from this run. The candidate ship (ship1104) is c9's INSTALL bat once c9 reads Q35; still open from
  earlier notes: Medal-quit stutter round, MouseMoveMs=16, lenscrack INSTALL bat if wanted.

# Scheduled check-in 2026-11-02 ~23:05 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- BUSY: live `KLHook.ini` written 22:18 UTC (`.before-botrevert1102` 22:10), `KLHook.log` 22:16 (the owner's online rounds,
  Alt+F4 at 22:16:37), `dinput8.dll` 21:49 (c9's ship_next install), c9's log note 22:45. No game run, no install, no
  screen from here. `KLHook.result` = the 10-27 PASS (F04); dumps: newest `KLHook_1.dmp` 10-26 and the 10-25 mdmp, both
  older than their notes: nothing to triage. Only `kl2.exe` (10.0 MB, sha1 9d99e01d) was staged INTO the cloud for disassembly.
- Head 3a88724 (research only on top of the verified dda3479 / 0c4b007): no code to re-verify.

## Done: the shadow-rules contract for the Arcade brain (re/arcade_brain_shadow_1102.md)
c9's plan (re/arcade_brain_online_1102.md, section D) listed three probes to run before any frame code and six
functions "not disassembled". Offline answers:
- Item 1 CLOSED without a probe: `[sm+0x5c]` is the game-type word and is 4 online (klsteam.c logs it as `game mode`,
  today's live log has 153 `game mode 4` transitions including the 20:28 System Link round; klr_online_host gates on
  it). The frame needs only `[sm+0x54] := 0` and `[G+0x54] := shadow`.
- Item 6: four of the six were already read in re/ (0x5dd890, 0x8b94d0, 0x43ffb0/0x46d4d0 fields); NEW whole reads of
  Board RUN 0x82f970, the traitor roll 0x43ffb0 (5/10/30/40 % by level band, LCG at [[0xdd2640]+0xb30], cap
  `[rules+0x338] < tuning+0x718`), 0x46d4d0 and 0x4322f0 (odd: never increments +0x338, narrows +0x33c; GUESS a shipped bug).
- Two stage-2 facts the plan lacked: shadow RECORD 0 IS THE LOCAL HUMAN (0x6c7700 returns 0 in the frame; Board RUN reads
  record 0 +0x10 == 4 to pick the walk mode) -> bots at 1..11; and the `+0x34c` byte table means 0 = live (0x78f470 /
  0x5dd890 skip non-zero), count at +0x354.
- Crash rule: Board RUN has no NULL check after 0x508ef0 and states 1/2 reach 0x7bb2a0 + vt[0x130]; call the originals
  inside the frame or not at all, keep shadow +0x1dc at 0 until the exit is mirrored (then 3/4).

## Owner
- Nothing to install or decide from this run. Still open from earlier notes: Medal-quit stutter round, MouseMoveMs=16.
