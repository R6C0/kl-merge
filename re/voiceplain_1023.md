# voiceplain (2026-10-23): flag-0 speech lines and a play-path log

Branch `feat/1023-voiceplain` (from rtp-schemas). Code: `klhook/klvoice.c` only (+ the [Voice] block of `klhook/KLHook.ini`). Nothing was run in the game.

## 1. RE result (static, kl2.exe 0490; listings 0x421c70, 0x578840, 0x7d0e80, 0x6ae750)
- Every speech line goes through `0x421c70(ecx = manager, line, other, speaker, x)` (`ret 0x10`). `speaker` = arg3 = a crew record (0..7) or 0xfe / 0xfa (random).
  `0x6ae750(rec)` = `[rules + 0x33e + rec]` = the voice number (what klvoice's walk uses as `tab[rec]`).
- Five play calls, all `e8 rel32` to `0x578840`, __thiscall (ecx = queue `[manager+0x974]`), stack at the call: `entry, priority [line+0x24], speaker (dword), float, last (= x)`, callee pops 0x14.
  Seen in 0x578840: `[esp+4]` entry, `+8` priority, `+0xc` speaker byte, `+0x10` float, `+0x14` last; queue record = `{priority, entry, speaker, float, last}`.
  | site | line kind | entry argument |
  |---|---|---|
  | 0x421e76 | flag 1, Arcade | per-voice vector `[line+0x14][voice]` (klvoice swaps it) |
  | 0x421ec3 | flag 0, Arcade | single entry `[line+0]` (stock for a Dead Men body) |
  | 0x4220b3 | flag 1, other mode | vector slot picked by a mode switch |
  | 0x42211b | flag 0, other mode | `[line+0]` |
  | 0x422156 | the `other` line (arg2) | `[other+0]` |
- `0x7d0e80` (called first by 0x578840) stores the started entry at `[queue+0xd8]`, the speaker byte at `[queue+0xd4]`, a time float at `[queue+0xcc]`.
- The 5 sites lie in 0x41e000..0x42a000 = HASHED by the integrity checks. The guard (klhook.c) refuses the patch in a SHIP build and in TEST with `SessionSafe=1`.
  It works in a TEST build with `[KLHook] SessionSafe=0` = the direct-boot run (`-o DefaultScene=Locations/F01/F01_Main.gms`). **Never in a real session** (ExitProcess 0x8000dead).

## 2. What it does / ini keys (all default off; `[Voice] Enable=1` still needed)
- `PlayLog=1` (+ `Log=2`): the five calls go to thunks `kvo_t1..t5 -> kvo_common -> kvo_hook`, which log
  `voice: SAY site N entry E node [E] speaker REC voice V (ours <KLVoice path> | stock <key text at entry+4>) queue Q` (rate limit: 400 per level generation, same entry+site not twice in 800 ms)
  and jump to 0x578840 with the arguments unchanged (stack transparent). Also `voice: PLAYING entry .. node .. speaker .. (ours|stock ..)` when `[queue+0xd8]` or `[queue+0xcc]` changes (data only: works in SHIP).
  Log line `voice: play-call probe/plain: 5 of 5 call sites retargeted` says whether the patch went in. `voice: entry USED?` is gone.
- `Plain=1`: the walk also visits flag-0 lines (all manager groups + the 19 singles): records entry -> leaf (key text without folder; `kvo_leaf` if it has `_C<n>`, else the whole name, e.g. `FA_YouEscaped01_R`),
  resolves `KLVoice/<Name>/<leaf>` (`<Name>_R` for `_R`, RadioFallback honoured) for each voice number a Dead Men body wears (entries come from the same cache as the flag-1 swap). In the thunk:
  `rec = speaker low byte (<8)` -> `voice = tab[rec]` (snapshot of the last tick) -> the resolved entry replaces argument 0; no leaf = stock. No lookup, no allocation in the thunk.
  Log: `voice: plain: single-entry line .. event ..` (Log=2), `plain: .. no leaf KLVoice/..` once per path, and the SAY line shows `[Plain: was .. stock ..]`.
- Install (lead does it): copy `dinput8.dll` of `klhook/out_voiceplain_1023_test` over `<DD>/dinput8.dll` AND set `[KLHook] SessionSafe=0` in the live KLHook.ini (the patch is refused otherwise). Only for a direct-boot run (`-o DefaultScene=..`).
- Undo: restore the previous (SHIP) dll AND set `SessionSafe=1` (or delete the key). WARNING: TEST dll + `SessionSafe=0` + `PlayLog`/`Plain` on lets the patch into hashed code in ANY boot; a real session then ends in the integrity exit. The SHIP build cannot patch (logs `patch REFUSED`), only PLAYING/QUEUED/Plain bookkeeping run.

## 3. GUESS / unverified
- GUESS: arg3 of 0x421c70 is the same crew-record space as `w.m[i].rec` (the flag-1 path proves the index `[rules+0x33e+arg3]`; klvoice's want[] uses the same table).
- GUESS: flag-0 keys have no `_C<n>`, so the leaf is the whole name. UNVERIFIED (`voice_review.tsv` is no evidence: `tools/kl_dmvoice.py` map_events builds leaves only from .LOC keys ending `_C<n>`, so the data side may have NO flag-0 leaf and Plain would log `no leaf` for everything). Check first: grep the staged .LOC for `Multiplayer/*/FA_YouEscaped01_R`; if absent the data tool needs a flag-0 mapping (follow-up).
- GUESS: site 0x422156's `other` line is among the manager's lines (else Plain leaves it stock). Speaker 0xfe / 0xfa (random) is not mapped (stock).
- GUESS: `[queue+0xcc]` changes with every start (it is `(now - x + 0x200) * k` stored at start); if it is also touched elsewhere PLAYING may log twice.
- A thunk taken while the walk is rebuilding is safe (same game thread).

## 4. Live test (lead)
TEST dll `klhook/out_cc6_voiceplain_test` (= `out_voiceplain_1023_test`); `[KLHook] SessionSafe=0`; the usual F01 direct boot with the staged DM01 zip (voiceheard) and a Dead Men body.
ini: `[Voice] Enable=1 StockLevels=1 Log=2 PlayLog=1 Plain=1`, `[Crew] Voice=1`, `[Wardrobe] DMVoice=1` (+ the 10:50 run's `[Character] Enable=1 Char=16`).
Proof lines:
1. start: `voice: on; ... PlayLog=1 Plain=1`, then `voice: play-call probe/plain: 5 of 5 call sites retargeted`. If 0 of 5: policy (SessionSafe=1 / SHIP) - nothing else of this will work.
2. `voice: plain: single-entry line .. event FA_YouEscaped01_R` lines (Log=2) = flag-0 lines found; none = the walk sees no flag-0 line (layout guess).
3. play until a flag-0 event fires (escape the round, a police event): `voice: SAY site 2 ... (ours KLVoice/<Name>_R/FA_YouEscaped01) [Plain: was .. stock ..Multiplayer/F01/FA_YouEscaped01_R]` and, right after, `voice: PLAYING ... (ours KLVoice/..)`.
   PLAYING with ours = the game started our clip. Cross-check by ear.
4. Control: set `Plain=0` once; the same event then logs `SAY site 2 ... (stock Multiplayer/..)`.
Without Plain, SAY site 1/3 lines for flag-1 events with `(ours KLVoice/..)` finally prove (or disprove) that the existing vector swap is what the game plays.
Risks: the patch sits in hashed code (direct boot only); a thunk fault would be a crash in the speech path (all reads are klh_rd; only a[0] is written).

## 4. Review fixes (feat/1023-voiceplain-fix)
- Fixed: GCC check (`tools/lint/klhook_gcc_prep.py` rewrites `KVO_THUNK` and `__asm { }` blocks; `run_harness_linux.sh --check-hook` passes SHIP and TEST).
- Fixed: first `kvo_played` sample after a reset only records (no spurious PLAYING for the previous level's entry).
- Fixed: Plain stops looking up flag-0 lines once the shared key cache is 3/4 full (logged once), so flag-1 swaps keep room.
- Fixed: notes (undo + SessionSafe, circular GUESS reworded).
- Rejected finding 3: `kvo_p.valid` is already zeroed at the top of every tick before any early return; staleness between ticks cannot be fixed from the tick, and the stale rep[] entries are never-freed heap blocks (worst case a wrong clip).
