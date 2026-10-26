# Arcade -> Online port plan (static inventory, 2026-10-26)

Source: owner order ~16:45 "crew names should be the heister characters name ... port EVERYTHING from arcade to online, gun pages, the hud / ui for shop and start and end of the mission killed by message upgrade". Static read only, nothing installed or run. Classes as in re/arcade_online_parity.md: L local cosmetic, H host authoritative, C needs replicated data or net message, X no seat/records.

## Root cause
Every Arcade reader (klb_read, klw_who_now, klr_arcade, klinv_player) demands ZGameRulesHeist (vtbl 0xbd3514), crew records of 0x7c at [rules+0x348] and ZHeistScore at [rules+0x5f8]. Online rules are ZGameRulesFragileAllianceSv 0xbd2eb4 / Cl 0xbd31e4: records 0x74 at [rules+8], count [rules+0x14], score DDL object [rules+0x2c]. So HUD, names, voice, balance are silent online. AI bots have no record: enumerate them with klu_online_bots (team-2 ZFFActor scan, max 8, cached 3 s). ALL online offsets below are GUESS unless stated; the decode needs the OnlineProbe dump (klbot.c ~455 klb_pdump).

## Answer to "where did 12 players / 10 min / 10 rounds / maps bundled go"
They exist: klhook/kllobbyopt.c ([Lobby] TimeMax, TimeMin, RoundsMax, PlayersMax 9..12, PlayersAuto; feature `lobbyopts` in tools/kl_mod_options.py, default off) and klslot.c [Expansion] OnlineSet=2/3/9 plus klhostopt.c [HostOpts] (map set to clients, F7). Not lost: the live KLHook.ini [Lobby] has only Solo=1, MinPlayers=1 (no TimeMax/RoundsMax/PlayersMax/KeepRound). The bench inis (C:/kl_build_1024/online_1025/live/SL6..SL11.ini) do set TimeMax=10, RoundsMax=10. Needed in live ini: [Lobby] TimeMax=10 RoundsMax=10 PlayersMax=12 KeepRound=1; OnlineSet=2 is already on line 174.

## Ordered plan (owner's order)

1. Crew list names = heister character names (humans and bots)
- File: klhud.c:klu_compose online branch (:1180-1230; fallbacks "You"/"Player %d" :1203-1204, bots "Heister %d" from klu_online_bots :1143); klhud_names.c:klnm_refresh/klnm_name/klnm_tag_ini; klcrew.c:klw_who_now (:220, Heist only) and klw_source (:184).
- Data: per human, record index -> entity index (via [rec+0x378] ZFFPlayer, GUESS) -> klcharonline klco.p[] peer look (klco_names[17]); fallback GetHero model rules->vtbl[0x220](2,n) (GUESS read-only) mapped by klw_source roots (J.C., Tommy, Pierre, Liam, Jean, Elwood, Bud, Mitchel). Per bot: actor model [[actor+4]+0x68] matched against klw_source roots, else deterministic unique unused character (klcrew weighted draw).
- Class: C (human look needs peer data) / L once read.
- Step: add klw_who_online(rec_i) in klcrew.c; in klu_compose replace the "Player %d"/"Heister %d" fallback with klw_who_online; make klnm_name call it when pre.online.

2. Gun pages / weapon shop page II
- File: klshop.c:180, klshoppage.c:449 (return on kl_online()); klpm_gun.c:48,66 and klpm_arc.c:91,120 (!kl_online()); klinv.c:68, klgun.c:409, klcensor.c:107.
- Data: stock online shop is XML FABuyWeaponsNew, selector MercsFASelectorWeapons 0xbbd494, ZMercsShowInfoFAWeapons. Mod pages work by relabeling the weapon pool through the replicated inventory.
- Class: C (inventory is replicated; every peer needs the hook, host decides).
- Step: replace the kl_online() early-return with the online inventory reader (klinv online variant reading the Cl rules' local record), then relabel the pool in the online selector; keep host authoritative on purchase. Needs a live bench; no static shortcut.

3. HUD / UI for the shop
- File: klshop.c, klshoppage.c; klhud_board2.c (BUY WEAPONS / READY state 0x20 is Arcade; online uses FAStatus / FAStatus_Team / FAWaitForPlayers).
- Data: online FA state page ids, money from S+0x224 / S+0x188 (which is loot vs rewards is GUESS).
- Class: L/C. Step: hook the FAStatus pages instead of HeistStatus*, draw the mod money and page II tab via the same element wrappers.

4. Start-of-mission screen
- File: klhud_board.c (ZFAIntroDisplay 0xbbdd98, Render 0x768c40; text "FRAGILE ALLIANCE ARCADE - ROUND 1 / LIVES LEFT / HEIST STARTS IN n SEC").
- Data: round number, lives, countdown online (not decoded; round/lives from S, GUESS).
- Class: C. Step: in the online case read round/lives from the DDL score object (after probe decode) and render the intro with "ONLINE" wording; countdown from FAWaitForPlayers timer.

5. End-of-mission screen
- File: klhud_board2.c (ZHeistOutroDisplay 0xbbde28 at state 0x1f; online only logs "scoreboard: ONLINE state" :527).
- Data: per-player take, rewards, killed counts from S, round result.
- Class: C. Step: replace the log-only branch with a render of the klu_compose online rows over the FAStatus pages.

6. "Killed by" message
- File: klhud.c:1224-1226 (hardcoded "THE POLICE" online); Arcade path :1345-1353 via kluv_killer; kllocname.c HideKilledBy (blanks LOC 0x500670..0x500b62 or key *KilledBy); stock panel is XML FARespawn "KilledBy".
- Data: online killerIndex (DDL i8[12], re/netcode.md:602); decode position unknown (GUESS) needs probe. Class: C.
- Step: read killer byte for the local record, map index -> record/bot name via item 1, replace "THE POLICE" by that name; fall back to police if index is out of range or 0xff. Do not hide the stock tag until the mod text is drawn.

7. "Upgrade" (AMBIGUOUS)
- No Arcade weapon-upgrade system exists in the repo. Probable meanings: (a) imperative "upgrade the killed-by message"; (b) the between-round shop (BUY WEAPONS); (c) mod page II / rank locks (UI check only). Treated as (a)+(b): covered by items 3 and 6. Needs one owner line to confirm.

8. Remaining mod HUD parts
- Kill feed: klhud_kill.c:klkf_render swallows the stock popup (:54-60) whenever klkf.on && klu_r.made, with no online test, hands text to klu_kill_txt which the online compose never reads, so the popup vanishes online. Class C. Step: add an online test; either do not swallow online, or set KLU_T_KILL in klu_compose online branch from a kill-event source.
  DONE 2026-10-26 (scheduled check-in, not run live): klhud.c publishes `klu_keep` once per compose (bit KLU_KEEP_KILL = klu_kill_line ran with [HUD] Money, bit KLU_KEEP_VAN = klu_van_card ran with Money); klkf_render swallows the pop-up only with the KILL bit, so online without OnlineCrew+OnlineFeed (and in Arcade with Money=0) the stock line draws as the game's own.
- Skulls/lives and ROUND line: klhud.c:1236-1400 (kluv_lives, kluv_round, KLU_T_KILL 1384-1386, ROUND text 1392). Class C. Step: online equivalents of kluv_* reading S (lives +? / round +? undecoded).
- Loot bar: klhud.c:1398; needs sum of ZOnlineMoneyCtrl +0x34 over the entity table (c9 item e). Class C.
- Names/tags: klhud_tags.c (depends on records); which ZFAPlayerListDisplay text object holds the name is unknown (re/hud_tags.md:49). Class L.
- Tab card: off online (`klu_r.card = ... && !pre.online`). Class L; enable after item 1.
- Escape dial/card: klhud_escape.c:klesc_prep blanks stock van timer/icon/bar online but our card is not drawn. Class C. Step: draw the card from the van state online or stop blanking.
  DONE 2026-10-26 (same change): klesc_render runs klesc_prep with EscapeCard=1 only while the VAN bit is set; otherwise the stock panel is left whole (the put-back path restores texts and plate). Online with OnlineVan=1 the card draws as before.
- Stock list: klu_skip_list :1748 skips only with klu.hidesrc && pre.online ? klu.hideonl && klb_hud_crew; names/round/skulls dropped. Step: do not skip until the replacement is drawn.
- Popups/values/qol: klhud_popup.c:531, klhud_board2.c:527, klqol2.c:235 use klb_read, inert online. Class L/C; port by klb_read_hud snapshot (klb.c:413), add on_score decode, bot list, killer byte, lives/round.

9. Voice / traits / talk
- File: klvoice.c:485, kltrait.c:122, kltalk.c:695 return when klw_who_now fails. Data: online body/character number per entity. Class C. Step: klw_who_now online variant = klw_who_online from item 1.

10. Heister select
- File: klchar.c:331, klcharonline.c (Steam lobby member data klx_look, UDP 27414). Default off, never run live. Class C. Step: bench it live, then feed item 1.

11. Damage balance
- File: klbalance.c:klr_arcade (:414) and klb_read use level index [[rules+0x5f8]+0x45]. Class H. Step: online host reads level index from its own rules and applies the damage record; probe only so far.

12. Music / ambience / stinger: DONE (klmusic.c, klambience.c, klstinger.c via klonline.c klon_read, Online=1 toggles). Class L.

13. Down / revive: owned by another session (kldown.c, klbotdown*.c). Note only. Class C.

## Rules respected
No edits to kldown.c, klbotdown*.c, klsync*.c, klucc*.c, klbotfill.c, klroundkeep.c. No install, no launch.
