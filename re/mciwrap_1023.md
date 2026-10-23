# MCI worker clock wrap sweep, 2026-10-23 (branch feat/1023-mciwrap) - BUILT, NEVER RUN IN THE GAME

Pattern (found in klstinger.c): the worker reads `now = GetTickCount()` at the top of a pass, then runs a slow MCI `open` (tens to hundreds of ms),
which stamps `slot->started = GetTickCount()` (later than `now`). A poll in the SAME pass computes `now - started` as an unsigned DWORD: ~49 days.

## Sweep result
| File / lines (before the fix) | Verdict |
|---|---|
| klambience.c worker, `klam_thread` (`now` read before `klam_bedcmd` / `klam_shot`; `klam_poll(now)` at the end) | REAL. `klam_poll`: `now - p->started > 300000u` (safety close) closed a fresh one-shot at once; `now - p->started > 400` and `now - klam_bed.started > 1500` also passed early (bed: `status kamb mode` right after the open; "not ready" would seek/play it again). Needs an open in the same pass as a 250 ms poll: harness measured 4 of 40 one-shots closed early. Fixed: `now = GetTickCount()` re-read before the poll. |
| klmusic.c worker, `klmu_thread` (`klmu_apply` -> `klmu_start` stamps `started`; `klmu_follow(now)`) | REAL but latent. `klmu_follow`: `now - p->started < 1500` guard wrapped, so the follow logic ran on a track opened that very pass: a "stopped"/"not ready" status or a short track (`pos + fade + 300 >= len`) would call `klmu_next` and skip it. Harness: 0 of 40 skipped (status says "playing" right after play), so no audible effect proven. Fixed the same way. |
| klambience.c `klam_stepfade(now - last)`, `last = now` | Not a bug: both from the same early `now` (kept on purpose, so fades do not jump by the open time). |
| klambience.c `klam_retry_at` | Safe: signed compare `(int)(now - klam_retry_at) >= 0`. |
| klambience.c / klmusic.c game-thread side (`now - t_last`, `t_round`, `G->next`, `t_action`, `t_end`, `t_fail`) | Safe: one thread, `now` read once per pass, stamps are taken from that same `now`; `G->next` uses a signed compare. The log line `KLB_T(GetTickCount()) - t_round` only runs later than the stamp. |
| klstinger.c | Already fixed (97cb6cc68 / 127b24487). |
| klvoice.c, kltalk.c | No MCI, no worker thread (game-thread ticks; `klk_now()` once per pass, stamps from the same `now`). Not affected. |

No new ini key: this is a bug fix, the old behaviour was the bug. `mciSendString` appears only in the three workers above.

## Changes
* klhook/klambience.c, klhook/klmusic.c: one re-read `now = GetTickCount();` before the poll / follow call, with a comment. Nothing else.
* klhook/klmciwrap_test.c: off-game regression (silent, volume 0). Build from a VS x86 prompt in klhook/:
  `cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS klmciwrap_test.c winmm.lib /Feamb.exe` and the same with `/DTEST_MUSIC` for music; run `amb.exe long.mp3`
  (any mp3 of 20 s or more; a silent 25 s one is at `<work>\build\mciwrap_1023\long25.mp3`). Result on the old code: ambience `4 of 40 closed early`, exit 1;
  new code: 0 of 40, exit 0. Music: 0 of 40 both (the latent case could not be provoked).

## Hooks (not installed; GUESS: none, no engine offset touched)
Built with `klhook\build.bat out_mciwrap_1023` (SHIP) and `build_auto.bat out_mciwrap_1023_test` (TEST), both link clean.
SHIP sha1 0E921AC5E385D23D9B32FF8498B08ED9A9ED0B90, TEST sha1 2E0C320EB919BBEF3D92E9F6CD6FBF234D574E2F. Staged copy: `<work>\build\mciwrap_1023\ship|test\dinput8.dll`.
Install: copy the SHIP dll over `<DD>\dinput8.dll` (keep the old one as `dinput8.dll.before-mciwrap`; the lead's current hook is d25393d9 plus whatever the other
branches add: this branch is cut from rtp-schemas, merge it before building the release dll rather than installing this dll on top of a newer one).
Undo: put the old dll back. No ini change.

## Live test for the lead
Ini: `[Ambience] Enable=1 Log=1` with a Folder and a short one-shot list (e.g. `Spot=` 3 to 6 s clips) and `SpotMin=5 SpotMax=8 SpotAfter=2 SpotFrom=calm`
(existing keys), plus `[Music] Enable=1 Log=1`, on any FA round for about 3 minutes.
Old hook: some `ambience: Spot <file>` log lines have no sound (the slot was closed at once); no log line shows it, so count heard vs logged.
Proof with the new hook: every logged `ambience: <group> <file>` is audible for its whole length; `music:` lines appear once per track, no
extra `music: CALM <file>` straight after another within 1.5 s. Both logs show `MCI ... failed` counts unchanged (0 expected).
Cheaper proof: just run `amb.exe` from the harness (above) on the lead's machine, no game needed.

## Open risks
* The ambience bug only bites when a poll falls into the pass that opens a clip, so it was intermittent (about open_ms / 250 per cue); a clean live run is not proof by itself.
* The music fix is untested for an effect (latent case); it can only make the follow logic wait the intended 1.5 s.
* Time diffs elsewhere in the 20+ other files were not audited (out of scope: only MCI workers).
