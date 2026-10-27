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

# 2026-10-27 second scheduled check-in (cloud, 14:49-15:10 UTC): PC busy, no new crash; the hook's ini documents every Mod Options key

Folders attached after one access request (read-only use). BUSY: local sessions committing until 14:19 UTC (head 0ae8a9f, ce's P2P5F
proof log), `dinput8.dll` written 14:44:48, `KLHook.ini` 14:44:26, `KLHook.log` / `KLHook.result` 14:44:22 (`RESULT PASS (script reached
pass) exit code 0, asserts 0, faults 0, loads 2, frames 89321`, 299 s, a bench round: the tail shows the online HUD weapon panel, the
bot bd: lines and the heli probe, `result now 'Time_Up' + LifeLost`, clock 27 s left of 360). Nothing launched, installed, staged into the
game or touched on screen.

## Dumps

Newest hook dump `KLHook_1.dmp` 10-26 08:11, newest game dump `kl2_490_crash_2026_10_25T19_18_39`: both older than the last log note and
already written up. Nothing to triage. The live ini carries `[Online]` twice (lines 1103 and 1106, both `Read=1`): harmless while they
agree (the profile API reads the first), worth folding into one the next time a session edits it.

## Head health (0ae8a9f)

MinGW i686: `tools/run_harness_linux.sh --check-hook` SHIP and TEST 0 errors (7 pre-existing warnings, unchanged). `kl_mod_options.py
--check-defaults klhook` exit 0, `--check-rec` clean, `kl_mod_options_test.py` 32/32 before the change.

## Offline piece: the keys the hook reads vs the keys klhook/KLHook.ini names

c9's client-freeze fix `[Input] PumpNoBlock` (289ce45, "recommended on" in its log line) and `MouseMoveMs`, and the `[Stall] Trace /
StallMsgMs` diagnostics, were read by klhook.c (lines 1017-1023) but named in no ini: neither the repo ini nor the owner's live one has an
`[Input]` or `[Stall]` section, so nobody could switch them on from the ini without reading the source. Scanning every
`GetPrivateProfileInt/String(..., klh_ini)` call and the per-module helpers (`klu_inii`, `klu_inif`, `klb_inif`, ...) against the repo
ini: 1036 keys read, 37 of them the keys of KL Mod Options rows with no line at all (17 modules without a section: [Shop], [Adrenaline],
[BotDown], [Shield], [Stinger], [Traits], ...; also [Voice] Enable, [KLHook] FastExit, [Lobby] Rows12/TimeMin/TimeMax/RoundsMax,
[HUD] HideIdleEscape / OnlinePopups, [FrameLimit] Adaptive / MapCap, [ReShade] ReloadFx, [ShopPage] TabNames).

1. `klhook/KLHook.ini`: new `[Stall]` and `[Input]` sections after [FrameLimit] (Trace=1 / StallMsgMs=20 / MouseMoveMs=0 / PumpNoBlock=0
   commented at the DLL defaults, c9's WHY in short; PumpNoBlock=1 `(recommended on) proven live: C27_PNB1 / HUD6` - c9 committed a second
   `[Input] PumpNoBlock=1` section at 14:54 while this ran (22e5150, 'PNB1/HUD6 proven, both seats, 0 faults'); the rebase kept both, the
   profile API reads only the first [Input], so the two were folded into one right after the push);
   one commented `;Key=<DLL default>   ; KL Mod Options row '<id>': <label> (recommended on|off)` line per rowless key at the end of its
   section, 17 new sections before [Online]. 95 lines added, nothing changed or moved.
2. `tools/kl_mod_options.py`: row `pumpnoblock` (G_STAB, recommended on, benched PNB1/HUD6; a DLL without the wrap ignores the key, the
   owner's SHIP 1027x is one); `scan_keys()` (the key scan check_defaults had, now also string helpers, and only calls that read klh_ini:
   klauto.c's kla_ini and kljoin.c's `file` keys are not KLHook.ini keys); `--check-ini KLHOOK_DIR INI` = row keys the ini never mentions
   (exit 1) + the count of other read keys it leaves out (`--verbose` lists them: 487, probes / logs / per-map tuning, left as they are);
   `ini_rec` reads a `(recommended ...)` marker on a commented `;Key=` line too, so `--check-rec` checks 47 more rows (66 unchecked, was 113),
   all agree. Tried and dropped: the other direction (ini keys no source reads): keys come from name tables, sprintf (P%d, Thr%d, F%02d)
   and per-map sections, every version listed live keys as stale.
3. `tools/kl_mod_options_test.py` 44 checks (commented-key markers, ini_mentions, scan_keys on a synthetic source with an Int helper, a
   String helper and a kla_ini read, check_ini both ways, the repo ini mentions every row key).

Not run: the Tk window and the Windows profile-API read-back (no Windows here); `--set pumpnoblock=on --apply` on a temp copy inserts
`PumpNoBlock=1` under the new `[Input]` header (the commented documentation line stays).

Owner / local sessions: nothing to install (the next SHIP with klhook.c's wrap gets PumpNoBlock=1 from the ini). New keys: a line in the repo ini (commented at the default is
enough) keeps `--check-ini` green and gives the owner a place to see them.
