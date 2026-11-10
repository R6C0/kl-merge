# 2026-11-10 ~11:00 scheduled check-in (cloud, offline): pale plate text in the Dead Men menu look

PC state: C:\kl_build_1024 busy (bench_1110/DM03VAULT_1110/online_run.txt 10:33, load sweeps until 10:22) -> nothing launched,
nothing installed, no screen. DD / DM folders are still not connected to the scheduled task (KLHook.log / dumps unread; no triage).

## The bug (02:55 note: "THEME BUG for the cloud")

Shots `C:\kl_build_1024\menulook_1109\shots\{deadmen,stock}\lobby.png` (read in the cloud): in the Dead Men look the lobby column
header (NAME: / CRIMINAL LOYALTY: / CRIMINAL STYLE: / CRIMINAL RANK:), the selected row (LOCATION: ... HOT COFFEE) and the CLOSE
SESSION / READY plates carry PALE text on a light plate; stock draws them black.

## Cause (READ in stage1\build_report.json + the themed XML)

`tools/kl_menu_look_1109.py` COLORSETS, row `OnFocus`: `('CHALK', 'INK', 'DIM')` by NAME. The stock set in all three files
(frontend.xml, ingame.xml, online.xml) is `ff000000 / ff000000 / ff888888`: ink on the plate ALWAYS. It is the set a receiver switches
to while focused (`RecCSFocus="OnFocus" RecCSDefault="Default"`, re/menus.md 520 / 717) and the set of every element standing on a
static plate: 66 uses in frontend.xml (FALobby Headline0..3 / TeamHeadline*, HeistLevel*, KLH_Char / Mask / Outfit, server browser
and leaderboard columns), 7 in ingame.xml (toggles), 42 in online.xml (FAWaitForOtherPlayersMenu columns, Heist_Bonus / Heist_Penalty,
LBRank / LBGamertag / LBPoints / LBRounds). re/hud_menu.md 141 already said "OnFocus = INK"; the 11-09 design table guessed chalk.

## Fix

1. Table: `OnFocus -> ('INK', 'INK', 'DIM')` (alpha kept); kl_menu_look_1109_test +1 check (106/0).
2. Live files (built before the fix): `tools/kl_menu_plates_1110.py` stage | check | fix | show (+_test 51/0). Rewrites ONLY the
   OnFocus values of the menu XML members; every other member byte-identical, table signature equal (proven, refused otherwise);
   a stock black / grey value counts as "already" (same role), so a stage on an untouched overlay stages nothing. Scene archives carry
   stock copies of frontend.xml / ingame.xml (shadowed by Patch01.zip): left alone (`members_for`).
3. Kit built on the device VM from copies of the live siblings (stage1 outputs + redesign_b\live_caf16a44.zip):
   ba1154de -> 19d946f6, 3a452a28 -> eb81abf8, caf16a44 -> 17cd0f96; diff = one `<ColorSet Name="OnFocus" ...>` line per member;
   zip testzip clean; install / undo round trip byte-exact on a scratch game folder. `C:\kl_build_1024\menuplates_1110` (install.py pins
   the live md5s; refuses if redesign B or anything else moved them: re-stage from the repo tool, which reads the live overlay).

Owner / local session: `python C:\kl_build_1024\menuplates_1110\install.py --dry`, then install with the game closed; bench ML1 lobby /
heister / leaderboard shots = dark text on the plates, nothing else changed. Undo: `--undo`.
