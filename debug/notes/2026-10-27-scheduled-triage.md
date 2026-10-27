# 2026-10-27 scheduled check-in (cloud, 10:48-11:15 UTC): PC busy, no new crash; Mod Options rows caught up with the proven online keys

The DD and DM folders were not attached to this scheduled session; one access request was granted (read-only use). The PC was
BUSY: local sessions (ce / c9) committing until 10:35 UTC, `dinput8.dll` written 10:49:07, `KLHook.log` / `KLHook.result` 10:48:43
(`RESULT PASS (script reached pass) exit code 0, asserts 0, faults 0, loads 2, frames 81057`, a bench round, 299 s). Nothing launched,
installed, staged into the game or touched on screen.

## Dumps

Newest hook dump `KLHook_1.dmp` 10-26 08:11 UTC, newest game dump `kl2_490_crash_2026_10_25T19_18_39` - both older than the last log
note and already written up. Nothing to triage.

## Head health

MinGW i686 installed here: `tools/run_harness_linux.sh --check-hook` SHIP and TEST 0 errors (7 pre-existing warnings); all 26 harnesses
compile except the two that cannot by design (klhigh_bits_test needs sed's bits.inc, klmem_test uses MSVC _ReturnAddress). No Wine, so
not run. `tools/kl_mod_options.py --check-defaults klhook` exit 0.

## Offline piece: tools/kl_mod_options.py vs klhook/KLHook.ini (SHIP 1027w installed for the owner at 10:31)

ff11724 flipped the repo ini's online keys to `(recommended on) proven live: CE27_ALL2D..G`; the owner-facing Mod Options table still
said `recommended off until benched` for 19 of those rows (hudonline, onlinecrew, onlineread, onlinenames, onlinekilled, onlinekilledai,
onlineround, onlinefeed, onlinetags, onlinetaghold, onlinevanicon, onlineboard, onlineboardstate, onlineintrostate, gradesbadge,
gradesrankup, gradesletter, hostopts, charonline). Its Recommended button would have turned the owner's proven online HUD off.

1. The 19 rows say on now, each `why` ends with the bench the ini cites. Five proven keys without a row got one: onlineboardcarrier,
   onlineintrocarrier, onlineshopnames, onlinetaghidedead, onlinetagprobe (dflt from klu_inii / GetPrivateProfileIntA, --check-defaults agrees).
2. New `--check-rec klhook\KLHook.ini`: each row's `rec` against the `(recommended on|off)` marker on its OWN key in the repo ini (on the
   key's line or in the comment lines above that name it; `until` / `after` forms = off for now), and the proven recommended-on keys no row
   offers. Exit 1 on a mismatch. Now: "every row agrees with the ini markers", no row-less proven key, 111 rows have no marker (not checked).
3. Bug found by the check's own_key: the tag rows (onlinetagstyle, onlinetaghold, ...) and the Grades rows (gradesbadge, gradesrankup,
   gradesletter, gradesonlinetags) had their shared prerequisite (`[HUD] OnlineTags`, `[Grades] Enable`) as FIRST key = the key `state()`
   reads and the key an off-write clears. So `--list` showed onlinetagstyle ON while OnlineTagStyle=0, and Recommended (gradesonlinetags off)
   would have written `[HUD] OnlineTags=0` and `[Grades] Enable=0`: every tag and Grades row off. Own key first now, prerequisite after with
   off value None (the table's existing 'helper key' convention). Against the repo ini, `--recommended` writes no tag / Grades key any more.
4. `tools/kl_mod_options_test.py`: 32 checks (marker forms, own_key, check_rec on a synthetic ini and on the repo ini, table shape, plan()).

Not run: the Tk window and the Windows profile-API read-back (no Windows here); the CLI paths exercised were --list / --recommended (dry) /
--check-defaults / --check-rec on the repo ini.

Owner / local sessions: nothing to install. When a key is moved to `(recommended on) proven live` in klhook/KLHook.ini, run
`python tools\kl_mod_options.py --check-rec klhook\KLHook.ini` and flip its row (or add one). `INSTALL KL Mod Options.bat` carries the new table
to `<DD>\KLModOptions\` when the owner next wants the window refreshed.
