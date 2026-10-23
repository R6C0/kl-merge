# Are the Dead Men voices heard? (voiceheard, 2026-10-23, offline, no live run)

Owner: "the dead men characters dont have their own voicelines still i dont think when i use them".
Evidence: KLHook.log of the 10:49-10:52 run (TEST hook, DM01, player Hutchison, Log=2). Code: `klhook/klvoice.c`, `tools/kl_dmvoice.py`.

## 1. Answer
**Proven:** the swap itself works. Walk 3 replaced 108 entries (36 lines x Kane, Meldal, Parker), the player's Hutchison 36 on walk 2.
**NOT proven:** that the game then PLAYS a swapped clip. Nothing in the log says so (no hook site watched the play). So until a
run shows `voice: QUEUED` (section 4), "heard" is unproven.
**Why the owner hears almost nothing: the installed DM01 data has only the 36 NON-radio lines.** 104 per-character lines exist
(36 plain + 68 radio `_R`). `kl_dmvoice` built DM01 at 03:12 under the old 600,000-byte .LOC cap and fell to its last tier
"no subtitles, no radio" (manifest: `loc_bytes English [524514, 558523, 'no subtitles, no radio']`; same on DM02). The cap is 612,634
since 05:34 and tier 1 (no subtitles, WITH radio) fits: 598,875 bytes. Log proof: `no leaf KLVoice/<Name>_R/...` 65 x 4 names, "272 without a
leaf" = 4 names x 68 radio lines. The radio lines are the common FA events: Backstab, CashMajority, TeamCashMajority, AllEscaped,
TimeOut, MissionBriefing, ExitLootArea, LevelBound, AllianceReminder, TeamAlliance, TeamDead... (their plain twin does not exist).

What the installed DM01 CAN play (36 lines, each in all 8 Dead Men voices): FA_BackstabReply 1-3, FA_Revenge 1-3, FA_PersonalRevengeRejected
(1-3, two lines each), FA_ShootOffMoney 1-3, FA_CallExitVehicle 3/4/6, FA_JackPot 4-6, FA_YouEscaped01-03, EscAndPlayerDead 1-3,
DriverBribe 1-3, DriverTraitor 1-3, UCCKilled 1-3. Mostly revenge / jackpot / escape-driver talk, rare in a round. After the rebuild: 104 of 104.

## 2. Is the right speaker swapped?
Yes, by the log. `voice table entry` = what `rules+0x33e+record` holds: bot 2 Kane "speaks as C1" -> slot 0 (log: `slot 0 (Kane)`), bot 4 Meldal
keeps entry 4 = slot 4, bot 7 Parker "C7" -> slot 6, the player (record 0) Hutchison = slot 7. "wanted voice numbers: 4" = those four
Dead Men bodies. The other bots (Elwood, Mitchel, Liam, Pierre) are Dog Days heisters and keep theirs. So AI Kane / Meldal / Parker
have the same leaves as the player: the same 36 plain events, none of the radio ones. No per-character difference, only the radio gap.
Talk module in that run: `Kane = record 2 (a bot), Lynch = nobody` -> the Kane/Lynch scenes need both, 'start' said nothing;
the only line said in the 60 s was stock `Multiplayer/F07/ExitLootArea_01_R_C4` by Liam (chatter any_money). The run was short
(chatter gap 40-90 s); it proves nothing about the DM pools either way.

## 3. Changes (all behind keys, default = old behaviour)
- `tools/kl_dmvoice.py` `event_theme()`: events named `FA_...` (what a non-radio line is called, most of DM01's plain lines) matched no theme rule
  (`^Backstab` against `FA_Backstab`) and all got "loot". Now `FA_` / `1time_` and trailing digits are stripped, and new rules cover
  CallExitVehicle/ExitVehicle*, PoliceReward, HittingTheScore, AllDead, Team{Leading,Trailing,Draw,WinGame,loseGame,OneMercLeft}, Exit_*.
  Only `ReachlootArea` / `TeamCashMajority` stay "loot" (by design). The picks of the old themes do not change, EXCEPT events with trailing digits not preceded by `_` (`YouEscaped01..03`, `Stage2`):
  their crc32 base lost the digits, so their clip index differs from a build made before this change (the staged DM01 data already has the new picks).
  Events that match no rule now print a one-line warning (and still use "loot"). Review fixes (2026-10-23, `feat/1023-voiceheard-fix`): the PlayedLog
  tick counter and the queued/changed counters are reset per level generation and wrap-safe (GetTickCount > 2^31), `path` of an entry is 128 bytes.
  With RadioFallback=1 a missing `_R` leaf costs two cache slots (the failed key and the plain key, cap 4096, never freed): accepted, small.
  The `[Voice]` keys are documented in the `klvoice.c` header and in `klhook/KLHook.ini` (`[Voice]` block added).
- `klvoice.c` `[Voice] RadioFallback=0` (1: a radio line without its `KLVoice/<Name>_R/..` leaf takes `KLVoice/<Name>/<same event>`). Only helps events
  that have both twins; a stopgap for a map still built at the no-radio tier.
- `klvoice.c` `[Voice] PlayedLog=1` (acts only with Log=2): see 4.

## 4. Proof that the game uses a swapped entry (new log lines, Log=2)
Mechanism seen by the talk module (kltalk.c section 1): a line goes through 0x421c70 -> 0x578840, which plays at once (0x7d0e80) or queues
`{priority, entry, speaker, float, last}` (count at `[queue]`, 20-byte records from `queue+4`, `queue = [manager+0x974]`).
- `voice: QUEUED KLVoice/Kane/FA_Revenge_01 for crew record 2 (queue 1, priority -1): the game is about to say our entry`
  every frame the queue is read (data reads only, nothing patched); an entry is logged at most once per 1.5 s. Seen = the game really
  says our entry. A line played at once never shows here (GUESS-free limit).
- `voice: entry USED? <key> changed after the swap (GUESS: ...)` : a checksum of the 0x204-byte entry block every 250 ms; the first change per entry
  (max 40). GUESS that the game stamps the entry when it plays it; if it never fires, only the QUEUED line counts, or the ear.
Neither is a "sound started" signal; the strongest remaining proof is by ear on a radio line (below).

## 5. Staged data (DM01 only, G: is tight)
`<work>\build\voiceheard_1023\out\DM01\` (work = `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools`, 388 MB):
F01_Main.zip, .WAV, .WHD, _LS.SND, KLTalk.ini, manifest.json; `voice_review.tsv` beside. Built by
`python tools/kl_dmvoice.py build --game <fake root> --out ... --maps DM01` from the `.before-1023voice` files (the tool refuses an
archive that already has KLVoice/). English .LOC 598,875, 2418 KLVoice leaves (was 1162), check: OK, 0 problems.
Not in the stage: three things changed in the installed archive after the 03:12 build: `Menu/online.xml` (292873 vs 292775 bytes),
`F01_Main.TEX` (same size, different CRC) and the Russian .LOC (612609 vs 612579). For a test they do not matter for voices; for a
real install take those three members from the installed zip (or tell me and I do it). NOT installed anywhere, no INSTALL bat (the
voice_1023 installer refuses an md5 it was not built from). Other maps were NOT rebuilt (DD maps never hit the tier; DM02 did).

## 6. Hooks (rtp-schemas 44c3aef08 + this branch)
TEST `klhook/out_voiceheard_1023_test/dinput8.dll` (= `out_cc6_voiceheard_test`), SHIP `klhook/out_voiceheard_1023/dinput8.dll` (= `out_cc6_voiceheard`);
sha1 in the commit report. Install = copy over `<DD>\dinput8.dll` (owner's rule: the lead does it). Undo = put the old dll back.

## 7. Live test the lead should run
Needs: hook above (TEST), the staged DM01 files in the F01 slot (back up with a move), ini as in the 10:50 run
(`[Character] Enable=1 Char=16`, `[Wardrobe] DMVoice=1`, `[Voice] Enable=1 StockLevels=1 Log=2 PlayedLog=1`, `[Talk] Enable=1`, `[Crew] Voice=1`).
1. Start log must say `voice: on; ... RadioFallback=0 PlayedLog=1`.
2. Walk lines: `N per-character lines, M entries replaced, ... K without a leaf` : K must be **0 or tiny** (it was 272); M ~ 104 x bodies.
   No `no leaf KLVoice/..._R/` lines. If it is still 272, the zip in the slot is the old one.
3. Play 3-4 minutes, pick up cash, kill a backstabber, get near the exit. Proof the game says our entries: `voice: QUEUED KLVoice/<Name>/...`
   (grep `QUEUED`). Cross-check by ear: a Kane/Meldal/Parker bot call must sound like the campaign voice, not a Dog Days heister.
4. `grep -c "entry USED"` tells whether guess (b) works; if QUEUED never appears but USED does, the lines are played at once.
5. If nothing appears: the swap works on the data but the play path does not read the vector slot (the queue is empty because the line is
   played directly, or the entry is copied before our swap): report the log, next step is a 0x7d0e80 call-site probe (needs a code patch, not done).

## 8. GUESS / open
- Radio lines (`_R`) might play in the radio filter only when the speaker is far; the grafted clip is the campaign's own (no radio effect).
- (b) is a guess; the queue read relies on the kltalk.c layout (read by disassembly, proven only for the talk module's own queue use: `speech queue 1 -> 2`).
- DM01 English subtitles are off at tier 1 (no text for the lines); the Russian/Japanese .LOC are fitted by kl_loc_fit (subtitles cut).
- Clip choice per event is a text-based guess (`voice_review.tsv`); the re-themed FA_ events change picks vs the installed build.

## 9. Live result (lead, 11:35)
VH1 on DM01 (TEST 3107ADB8 on rtp-schemas 84454df2c): `voice: on ... RadioFallback=0 PlayedLog=1`; walks `104 per-character lines, 208 entries replaced, 0 without a leaf`; no `no leaf` lines; 0 asserts, 0 faults. `QUEUED` 0, `entry USED` 0 within ~90 s of play (the launch options' AutoExit ends the run; no FA voice event fired). Installed for the owner the same minute with tools/voiceheard_1023 (INSTALL/UNDO bats, md5 guard 82b33bf8, backups *.before-voiceheard). The staged out\DM01\F01_Main.zip was replaced by the grafted one (online.xml, TEX, Russian .LOC from the installed zip).
