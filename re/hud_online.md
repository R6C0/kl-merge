# The owner's HUD in a private match / online (TASK B, 2026-10-18)

Static reading of kl2.exe 0490 (capstone, RTTI). NOTHING HERE HAS RUN ONLINE. GUESS = not proven.

## Why the HUD was dark online
klbot.c `klb_read` returns 0 unless net role is not 2/3 AND the rules object is ZGameRulesHeist (0xbd3514). Online the rules
are ZGameRulesFragileAllianceSv 0xbd2eb4 (host) / ...Cl 0xbd31e4 (client). RTTI: Heist, Sv, Cl are SIBLINGS under
ZGameRulesFragileAlliance (0xbd2b9c).

## What holds online (EXE)
- Base ctor 0x7de590 (called by Sv 0x79acc0 and Cl 0x6fe090; Cl adds nothing, Sv adds its own fields from 0x334) initialises
  [rules+0x1dc], +0x1e0, +0x1e4, +0x1ec, +0x200 ... So every offset < 0x334 exists in all three classes.
- vtable slot 73 (time left) = 0x61d070 `fld [ecx+0x4c]` is the SAME function in Fa, Sv, Cl, Heist: [rules+0x4c] is a base field.
- Heist-only: crew records 0x7c bytes at [rules+0x348] (Sv: 0x74 bytes at [rules+8]), ZHeistScore at [rules+0x5f8] (Heist ctor 0x835480).
  Cl has NO score object in the rules at all; the replicated score is DDL_ZScoreFragileAlliance (not read by the hook).
  So money, lives, crew rows, tags, loot share, round length ([score+0x3c]) CANNOT be read with the Arcade code online.

## Change
- klbot.c: `klb_read` untouched (bots, balance, fed, crew, climb, escort stay Arcade-only). New `klb_read_hud`: klb_read, else (only with
  `[HUD] Online=1`, role 2/3, type 4, rules vtable Sv or Cl) a snapshot with `online=1`, rules, state, n=0, score=0, veh=0.
  `klb_online_session()` is the same test without the read.
- klhud.c: tick + compose use klb_read_hud. Online: the level gate is open for any level (cosmetic only); compose draws only the
  round watch (clock = [rules+0x4c]; length = GUESS: largest value seen since state 0x19 began) and the weapon dial; the stock
  player list is NEVER hidden (it is the only list with data); Tab card off. Escape dial off (veh 0; [rules+0x1d8] timer unproven for Sv/Cl).
- Left on klb_read (inert online, by design until a reader of Sv's 0x74-byte records exists): klhud_popup, klhud_board2, klhud_names,
  kill feed, tags. klsteam.c untouched: Steam writes stay blocked exactly as before.
- Default `Online=0`: reads only, but klu_make_all writes into the OSD and nothing was ever run in a lobby.

## GUESSes
1. Session state [sm+0x70] in the multiplayer manager is 0x17..0x19 for countdown..round like Arcade (0x6c53db pushes 0x12 for the load).
2. ZOnScreenDisplay2 + its FA list/clock exist online with the same layout (the HUD finds it by vtable; no OSD = nothing drawn).
3. [rules+0x4c] is kept current on a CLIENT (it is a base field, slot 73 reads it; who counts it down online not read).
4. The level archive carries the baked HUD pictures 113/114 (kl_hud.py): needed by every Dials/Weapon draw; every peer needs the same build.

## Owner test (2 Steam accounts, identical build on both)
1. Both: KLHook.ini `[HUD] Online=1` (+ the usual Enable, Dials, Weapon). Host: private game, pick the map slot, friend joins by invite.
2. Look for `hud:` lines in KLHook.log on both machines and `net:` line (rules class Sv / Cl). Expect the watch ring + weapon dial, stock list intact.
3. If the HUD flickers or the game faults at round start, set Online=0 and send KLHook.log.
