r"""kl_mod_options.py - MOD OPTIONS: one checkbox per owner-facing feature of the Kane & Lynch 2 mod, each labelled
'(recommended on)' or '(recommended off)'. Writes <Dog Days>\KLHook.ini. 2026-10-24 (the owner: 'everything needs to be an option in
the mod to turn on and off, should have (recommended on) next to it'). Design and the table with the reasons: re\mod_options.md.

WHY A WINDOW OUTSIDE THE GAME and not a menu page: the game's menu table has no room for 30 more rows and the Mod settings window is
full at 9 rows (re\mod_options.md section 3). This tool needs no game code and cannot crash the menu.

  python tools\kl_mod_options.py                    the window (Tk)
  python tools\kl_mod_options.py --list             every feature: state, recommendation, when a change takes effect
  python tools\kl_mod_options.py --recommended      show what 'Recommended' would change (add --apply to write it)
  python tools\kl_mod_options.py --set bots=off music=on --apply
  --ini PATH   use another KLHook.ini (tests); --game DIR   another Dog Days folder; --force   skip the 'game is running' refusal (tests)

Rules: refuses to write while kl2.exe runs (the hook reads the ini at start, a running game would also overwrite nothing but the player
would think the change was live); keeps ONE backup, KLHook.ini.before-modoptions (made before the first write, never replaced); writes
only the keys of the features whose box changed (every other line, comment and custom number stays byte for byte); reads the file back
with the Windows profile API (the one the hook uses) and reports any key that did not take.

A feature is ON when its MASTER key (the first key of its row) is not its off value; a key that is absent counts as the DLL's own
default (the 'dflt' of the row, copied from the GetPrivateProfileInt call in klhook\*.c; tools\kl_mod_options.py --check-defaults compares
them with the sources). Turning a feature ON also writes its further keys (e.g. Fed Player=1).
"""
import argparse, os, re, shutil, subprocess, sys, time

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
BACKUP_SUFFIX = '.before-modoptions'

# key = (section, key, on_value, off_value, dflt). off_value None = leave the key alone when turning off (a helper key).
# Feature = (id, group, label, recommended 'on'|'off', when, reason, [keys], pending)
#   when: 'start' = read by the DLL at start (restart the game), 'round' = read when a round starts (a new round is enough; GUESS for none
#   of the rows yet: every row is 'start' because every GetPrivateProfileInt of these keys sits in an init function), 'dll' = the key is read only by a
#   DLL newer than the live k29b (klfps.c): change it to 'start' once that DLL is installed.
F = []


def feat(fid, group, label, rec, when, why, keys, pending=False):
    F.append(dict(id=fid, group=group, label=label, rec=rec, when=when, why=why, keys=keys, pending=pending))


G_CORE, G_CREW, G_DOWN, G_AV, G_GFX, G_STAB, G_EXP = ('Core', 'AI crew and traitors', 'Down, revive, fed', 'Sound and music',
                                                       'Graphics and camera', 'Stability and fixes', 'Experimental / not tried in play')

feat('allmaps', G_CORE, 'Mod features on the nine stock Fragile Alliance maps', 'on', 'start',
     'owner: every feature also on the stock maps; their Steam stats stay blocked', [('KLHook', 'AllMaps', 1, 0, 0)])
feat('expansion', G_CORE, 'Dead Men maps in the Arcade menu', 'on', 'start',
     'the expansion itself: the Dead Men map pages and their redirects', [('Expansion', 'Enable', 1, 0, 0)])
feat('character', G_CORE, 'Heister, mask and outfit select', 'on', 'start',
     'the Heister page in Arcade (Dead Men and Payday 2 masks)', [('Character', 'Enable', 1, 0, 1)])
feat('guns', G_CORE, 'Dead Men gun looks and start rifle (Mod settings rows)', 'on', 'start',
     'works with the maps built with the guns; harmless elsewhere', [('Guns', 'Enable', 1, 0, -1)])
feat('shop', G_CORE, 'More guns in the weapon shop', 'on', 'start',
     'run live 2026-10-20 (rows swapped for Minimi, HK69, Type 81, Rem 700)', [('Shop', 'Enable', 1, 0, 0)])
feat('shoppage', G_CORE, 'Weapon shop page II: a key (P) flips the shop to a second set of guns', 'on', 'start',
     'klshoppage.c + KLShopPage.ini (tools/kl_shop_sets.py stage); NOT live-tested; needs the ini beside KLHook.ini, else it logs and does nothing', [('ShopPage', 'Enable', 1, 0, 0)])
feat('shoptabs', G_CORE, 'Weapon shop page II: own tab names (KLShopPage.ini [Tabs]) instead of "... II"', 'on', 'start',
     'klshoppage.c TabNames: data-only text swap; an empty [Tabs] key keeps the old " II" append; needs [ShopPage] Enable=1', [('ShopPage', 'TabNames', 1, 0, 0)])
feat('hud', G_CORE, 'Mod HUD (kill feed, scoreboard, trackers, names)', 'on', 'start',
     'the owner plays with it', [('HUD', 'Enable', 1, 0, 0)])
feat('balance', G_CORE, 'One damage scale for you, police and crew (Dead Men maps)', 'on', 'start',
     'v71 balance: the owner found the stock numbers too tanky', [('Balance', 'Enable', 1, 0, 0)])
feat('climb', G_CORE, 'Free climb (hold W + E at a ledge)', 'on', 'start',
     "Dead Men's climb (luvsic's), only on maps with the climb clips", [('Climb', 'Enable', 1, 0, 0)])
feat('censor', G_CORE, 'Head shots blow the head off (pixelated censor)', 'on', 'start',
     'owner item 9; heap data only', [('Censor', 'Enable', 1, 0, 1)])
feat('censorlate', G_CORE, 'Censor also corpses, AI heisters and you (late head blow)', 'on', 'start',
     'k31cen: calls the game BlowHeadOff 350 ms after death; not live-tested', [('Censor', 'Late', 1, 0, 1), ('Censor', 'Player', 1, 0, 1)])
feat('onlinedm', G_EXP, 'Private match / System Link: use the Dead Men maps page (not for Quick Match; every player needs the same setting)', 'off', 'start',
     'klslot.c OnlineSet=2 (page 2, "Dead Men maps"); run live 2026-10-25 (SL2: System Link host loaded DM01); host choice is not sent to joiners; untick every online map row = Dog Days maps', [('Expansion', 'OnlineSet', 2, 0, 0)])
F[-1]['exact'] = True; F[-1]['excl'] = 'onlineset'
feat('onlinecamp', G_EXP, 'Private match / System Link: use the Dead Men campaign page (not for Quick Match; every player needs the same setting)', 'off', 'start',
     'klslot.c OnlineSet=3 (page 3, "Dead Men campaign"); not run live (same code path as page 2); ticking it unticks the row above', [('Expansion', 'OnlineSet', 3, 0, 0)])
F[-1]['exact'] = True; F[-1]['excl'] = 'onlineset'
feat('onlinerandom', G_EXP, 'Private match / System Link: random map (Dead Men and Dog Days mixed) (not for Quick Match; every player needs the same setting)', 'off', 'start',
     'klslot.c OnlineSet=9: per slot the stock map or any Dead Men map page that has one for that slot, drawn from the lobby id so all players get the same; NOT run live; ticking it unticks the other online map rows', [('Expansion', 'OnlineSet', 9, 0, 0)])
F[-1]['exact'] = True; F[-1]['excl'] = 'onlineset'
feat('onlinerandround', G_EXP, 'Random online map: a new draw every round (only with the random map row; everyone must be in the lobby from the start)', 'off', 'start',
     "klslot.c OnlineRandomRound=1: the round number (loads more than 60 s apart, counted by each machine) joins the seed; a player who joins after a round was played counts differently and gets another map; NOT run live", [('Expansion', 'OnlineRandomRound', 1, 0, 0)])
feat('lobbysolo', G_EXP, 'System Link / Private Match: play a round by yourself as host (no "all players left" window; for testing custom matches)', 'off', 'start',
     'kllobby.c [Lobby] Solo=1 (implies MinPlayers=1): the session error word is cleared while you host with 1 human; private vtable copy of the session manager (heap data); NOT run live', [('Lobby', 'Solo', 1, 0, 0)])
feat('lobbyrows12', G_EXP, 'Online lobby (Fragile Alliance): list shows 12 player rows instead of 8 (rows closer together; needs the file Patch01_rows12.zip in the Overlay folder, built by tools/kl_lobby12.py; recommended on)', 'on', 'start',
     'klslot.c [Lobby] Rows12: answers the open of Patch01.zip with the FALobby-with-12-rows menu; layout GUESS (row pitch 20, rows 9-12 reuse FAStatus_*#09-12 pictures); NOT run live; re/lobby_12rows.md', [('Lobby', 'Rows12', 1, 0, 1)])
feat('lobbyopts', G_EXP, 'Lobby (host): Heist time 2 to 10 minutes and up to 10 rounds (stock 3-5 minutes, 3-5 rounds); every player gets the numbers the host picks', 'off', 'start',
     'kllobbyopt.c [Lobby] TimeMax/TimeMin/RoundsMax: private vtable copy of the lobby selector (heap data); the stock handler does the work; NOT run live; re/lobby_options.md', [('Lobby', 'TimeMax', 10, 0, 0), ('Lobby', 'TimeMin', 2, 0, 0), ('Lobby', 'RoundsMax', 10, 0, 0)])
feat('hostserver', G_EXP, 'Host server: this copy keeps hosting a Quick Match lobby by itself, restarts after each round (for a PC left running; implies lobby solo)', 'off', 'start',
     'klserver.c [Server] Enable=1 (Mode=quick|ranked, MinPlayers, WaitSec): drives the menu to QuickJoin, lowers the lobby target after the wait; NOT run live; re/online_server.md', [('Server', 'Enable', 1, 0, 0)])
feat('keeppage', G_EXP, 'Private match / System Link: keep the last Arcade expansion page for the next online session', 'off', 'start',
     'klslot.c KeepPageOnline; NOT run live; ignored while OnlineSet is set', [('Expansion', 'KeepPageOnline', 1, 0, 0)])
feat('hidestock', G_CORE, 'Old (stock) HUD list never shown: skipped at its Render, so Tab / Alt+Tab cannot bring it back (recommended on)', 'on', 'start',
     'klhud.c HideSrc: private vtable of ZFAPlayerListDisplay, Render skipped while the mod HUD stands; needs [HUD] Enable=1', [('HUD', 'HideSrc', 1, 0, 1)])
feat('hidestockonl', G_CORE, 'Online matches: also hide the old (stock) list; the new online crew list is not built yet, so this leaves no crew list online (recommended on, owner request)', 'on', 'start',
     'klhud.c HideOnline; needs HideSrc=1', [('HUD', 'HideOnline', 1, 0, 1)])
feat('onlinecrew', G_CORE, 'Online matches: new crew list with money (humans only, names not decoded yet; recommended on once proven live)', 'off', 'start',
     'klhud.c OnlineCrew; needs [HUD] Online=1; SL6 layout: free byte 0 = used, money [S+0x224+4i]+[S+0x188+4i]; NOT run live', [('HUD', 'OnlineCrew', 1, 0, 0)])
feat('onlineread', G_CORE, 'Online matches: the round reader that the heister names, KILLED BY and ROUND n OF m below use (recommended off until benched)', 'off', 'start',
     'klonline_read.c [Online] Read; read only; NOT run live', [('Online', 'Read', 1, 0, 0)])
feat('onlinenames', G_CORE, 'Online matches: crew list shows the heister characters\' names (J.C., Tommy...) like Arcade (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineNames; needs [Online] Read=1 and [HUD] OnlineCrew=1; NOT run live', [('HUD', 'OnlineNames', 1, 0, 0)])
feat('onlinekilled', G_CORE, 'Online matches: KILLED BY shows the killer\'s heister name instead of THE POLICE (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineKilled; needs [Online] Read=1; NOT run live', [('HUD', 'OnlineKilled', 1, 0, 0)])
feat('onlineround', G_CORE, 'Online matches: ROUND n OF m line under the clock like Arcade (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineRound; needs [Online] Read=1; NOT run live', [('HUD', 'OnlineRound', 1, 0, 0)])
feat('onlinefeed', G_CORE, 'Online matches: kill-feed line (X KILLED Y) under REWARDS like Arcade (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineFeed; needs [Online] Read=1 and [HUD] OnlineCrew=1; NOT run live', [('HUD', 'OnlineFeed', 1, 0, 0)])
feat('onlineskulls', G_CORE, 'Online matches: death-mark skulls on your row like Arcade lives (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineSkulls; needs [Online] Read=1 and [HUD] OnlineCrew=1; NOT run live', [('HUD', 'OnlineSkulls', 1, 0, 0)])
feat('onlineloot', G_CORE, 'Online matches: loot bar under TOTAL like Arcade (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineLoot; needs [Online] Read=1 and [HUD] OnlineCrew=1; NOT run live', [('HUD', 'OnlineLoot', 1, 0, 0)])
feat('onlinetab', G_CORE, 'Online matches: Tab card (full crew list) like Arcade (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineTab; needs [Online] Read=1 and [HUD] OnlineCrew=1; NOT run live', [('HUD', 'OnlineTab', 1, 0, 0)])
feat('onlinevan', G_CORE, 'Online matches: escape / van card like Arcade (recommended off until benched)', 'off', 'start',
     'klhud.c OnlineVan; needs [Online] Read=1 and [HUD] OnlineCrew=1; NOT run live', [('HUD', 'OnlineVan', 1, 0, 0)])
feat('onlineboard', G_CORE, 'Online matches: round-over card like Arcade, killed by message names the killer heister (recommended off until benched)', 'off', 'start',
     'klhud_board2.c OnlineBoard; needs [Online] Read=1 and [HUD] Scoreboard=1; NOT run live', [('HUD', 'OnlineBoard', 1, 0, 0)])
feat('onlineintro', G_CORE, 'Online matches: round n of m, players, minutes and your heister under the pre-round card (recommended off until benched)', 'off', 'start',
     'klhud_board2.c OnlineIntro; needs [Online] Read=1, [HUD] Scoreboard=1 and Board=1; NOT run live', [('HUD', 'OnlineIntro', 1, 0, 0)])
feat('shoponline', G_CORE, 'Online matches: weapon shop page II shown (view only, locked) (recommended off until benched)', 'off', 'start',
     'klshoppage.c OnlineLook; page II buys are swallowed online; needs [ShopPage] Enable=1; NOT run live', [('ShopPage', 'OnlineLook', 1, 0, 0)])
feat('ucchide', G_CORE, 'Undercover Cop: the crew list does not give the undercover cop away to heisters (recommended on)', 'on', 'start',
     'klhud_values.c kluv_state UccHide; re/ucc_tell_audit.md S10; NOT run live', [('HUD', 'UccHide', 1, 0, 1)])
feat('onlinebots', G_CORE, 'Online matches: AI heisters also listed in the crew box, like Arcade (recommended on)', 'on', 'start',
     'klhud.c OnlineBots; team-2 ZFFActor scan (GUESS); needs OnlineCrew=1; NOT run live', [('HUD', 'OnlineBots', 1, 0, 1)])
feat('hudrows12', G_CORE, 'HUD crew list and round-end scoreboard: up to 12 players (stock-style cap was 8); the local player always has a row (recommended on)', 'on', 'start',
     'klhud.c / klhud_board2.c [HUD] Rows12 (KLU_ROWS 12, KLSB_NROW 12; 9+ scoreboard rows use a tighter pitch, GUESS); NOT run live', [('HUD', 'Rows12', 1, 0, 1)])
feat('hidekilledby', G_CORE, 'Hide the stock death panel own "Killed by" text so only the HUD KILLED BY line shows, Arcade and online (recommended on)', 'on', 'start',
     'kllocname.c HideKilledBy: LOC lookups from 0x500670 and the key KilledBy answer an empty string; needs [HUD] Enable=1 and KilledBy=1; NOT run live', [('HUD', 'HideKilledBy', 1, 0, 1)])
feat('hidevan', G_EXP, 'Hide the van escape timer until the van is there', 'on', 'start',
     'klhud.c van card; needs [HUD] Enable=1', [('HUD', 'HideIdleEscape', 1, 0, 1)])
feat('vanblow', G_EXP, 'Escape vehicle can blow up when nobody is aboard', 'on', 'start',
     'klescort.c [VanBlow] (k33): the van shield stays only while somebody is aboard; an empty van shot to 0 burns, then explodes. Dry=1 = log only; HealthMax lowers a big health (GUESS)', [('VanBlow', 'Enable', 1, 0, 1)])
feat('clubcalm', G_EXP, 'Last Call probe: log the hand item and shots (read-only)', 'off', 'start',
     'klclubcalm.c: data for the calm-until-the-gun-is-drawn switch', [('ClubCalm', 'Enable', 1, 0, 0)])
feat('clubholster', G_EXP, 'Last Call: start with guns holstered, the crowd panics when you draw (recommended off until live-tested)', 'off', 'start',
     "klclubholster.c: calls the game's own holster routine 0x5e7c60 and fires the civilians' tbCivRunToGate boxes; Dry=1 = log only; Last Call only (never on stock FA maps); not live-tested", [('ClubHolster', 'Enable', 1, 0, 0), ('ClubHolster', 'Dry', 0, 1, 1)])
feat('animprobe', G_EXP, 'Animation probe: log the player Play calls around gait changes (diagnostic) (recommended off)', 'off', 'start',
     "klanimprobe.c: LOG ONLY, changes nothing; patches the top of Play 0x4da1d0, so only a TEST dll does it (a SHIP dll refuses and logs it); not live-tested", [('AnimProbe', 'Enable', 1, 0, 0)])
feat('syncapply', G_EXP, "Online: clients follow the host's cop positions (recommended off)", 'off', 'start',
     "klsync.c [Sync] Apply: a client teleports non-player actors farther than ApplyTol (150) from the host's list (UDP 27415, host needs Share=1) via the game's actor teleport 0x62a900; only after the class/team identity check agrees with the host (20-byte KLSY2 records), from the first packet source, worst ApplyMax per pass, 2 passes/s; skips humans and any actor sharing a human's team or within 40 units of a player (so AI heisters on the humans' team are NOT moved); host-dead is logged only; GUESS: node position vs feet, facing resets; not live-tested", [('Sync', 'Apply', 1, 0, 0)])
feat('syncpuppet', G_EXP, "Online: clients' cops follow the host instead of thinking for themselves (recommended off)", 'off', 'start',
     "klsync.c [Sync] Puppet: a client re-issues the game's own velocity steer 0x70f660 each frame (private ZFFActor vtable, slot 87 wrapper) for cops (team 3) farther than PuppetTol (60) from the host's place, no animation reset; beyond PuppetSnap (1500) the actor teleport; host needs Share=1; use instead of Apply; GUESS: velocity units, cop team value; not live-tested", [('Sync', 'Puppet', 1, 0, 0)])
feat('syncpuppetdiag', G_EXP, "Online: log why a client's cops do or do not follow the host (recommended off)", 'off', 'start',
     "klsync.c [Sync] PuppetDiag: read-only 'sync: puppet diag:' log lines (controller pair, cover fields) for up to 8 cops per pass; works without Puppet; log only", [('Sync', 'PuppetDiag', 1, 0, 0)])
feat('synctrack', G_EXP, "Online: clients' cops are kept at the host's place every frame (recommended on, needs Puppet)", 'on', 'start',
     "klsync.c [Sync] Track: a hooked cop farther than TrackTol (40) from the host's place moved on by the list age is placed there with the game's actor teleport 0x62a900 every frame (TrackMax 8 per frame, once per TrackMs 50 per cop) instead of the 2 s snap; logs 'sync: track:' (5 s summary, revert probe); GUESS: lead 60 ms, speed clamp 900; not live-tested", [('Sync', 'Track', 1, 0, 1)])
feat('synctracklocal', G_EXP, "Online: Track placements keep the cop's animation and send nothing to the peers (recommended on, needs Track)", 'on', 'start',
     "klsync.c [Sync] TrackLocal: Track calls the game's teleport 0x62a900 with both flags 0 instead of 1,1 (no animation reset, no network send); GUESS from the code reading; not live-tested", [('Sync', 'TrackLocal', 1, 0, 1)])
feat('synctrackrot', G_EXP, "Online: Track placements keep the cop's facing (recommended on, needs Track)", 'on', 'start',
     "klsync.c [Sync] TrackKeepRot: Track passes the node's own rotation (nine floats at +0) to the teleport instead of the identity; GUESS on the layout; falls back to identity if it does not look like a rotation", [('Sync', 'TrackKeepRot', 1, 0, 1)])
feat('synctrackstall', G_EXP, "Online: Track also places a stalled bound-follower cop (recommended on, needs Track)", 'on', 'start',
     "klsync.c [Sync] TrackBoundStall: a cop on a bound follower controller is left to the stock steer only while it converges; a stalled one is placed (SP1g slot 574, 230 units off for 25 s); thresholds are GUESS", [('Sync', 'TrackBoundStall', 1, 0, 1)])
feat('synctrackkeepy', G_EXP, "Online: Track placements keep the cop's own height on the same floor (recommended on, needs Track)", 'on', 'start',
     "klsync.c [Sync] TrackKeepY: keeps the cop's y when the host's y is within TrackYTol (150, GUESS) units; removes the Y pop of each placement", [('Sync', 'TrackKeepY', 1, 0, 1)])
feat('crewlook', G_CORE, 'Random looks for the AI heisters', 'on', 'start',
     'no body twice, never the one you wear', [('Crew', 'Random', 1, 0, 0)])

feat('bots', G_CREW, 'AI heisters in Arcade', 'on', 'start',
     'the whole crew system (bots); other crew rows need it', [('Bots', 'Enable', 1, 0, 0)])
feat('escort', G_CREW, 'One AI heister stays beside you', 'on', 'start',
     'seen live 2026-10-11 (standing player only)', [('Bots', 'Escort', 1, 0, 0)])
feat('followout', G_CREW, 'The crew follows you out once the vehicle is called', 'on', 'start',
     'seen live 2026-10-11 (run FO_J1)', [('Bots', 'FollowOut', 1, 0, 0)])
feat('boardall', G_CREW, 'Idle AI heisters are sent to the escape vehicle', 'on', 'start',
     'seen live 2026-10-11 (runs L12a / L12b)', [('Bots', 'BoardAll', 1, 0, 0)])
feat('traitors', G_CREW, 'Traitors: an AI heister can turn on you (20 % of rounds)', 'on', 'start',
     'owner asked for backstabbing 2026-10-11; 35 -> 20 on 2026-10-23, max 1 a round',
     [('Bots', 'Backstab', 20, 0, 0), ('Bots', 'Tune', 1, None, 0), ('Bots', 'TraitorFoe', 1, None, 0)])
feat('crewhop', G_CREW, 'AI heisters cross places the navmesh cannot (Retomoto lobby)', 'on', 'start',
     'the lobby car is down; without it they stand', [('CrewHop', 'Enable', 1, 0, 0)])
feat('crewjoin', G_CREW, 'AI heisters follow the tower-to-lobby jump (Retomoto)', 'on', 'start',
     'two navmeshes joined only by kljoin.c', [('CrewJoin', 'Enable', 1, 0, 0)])
feat('traits', G_CREW, 'A small trait per Dead Men character', 'on', 'start',
     'enabled in the live ini; the effect is small and logged', [('Traits', 'Enable', 1, 0, 0)])
feat('talk', G_CREW, 'Kane and Lynch dialogue and chatter', 'on', 'start',
     'Retomoto countdown and the idle chatter', [('Talk', 'Enable', 1, 0, 0)])

feat('down', G_DOWN, 'You go down and can be revived', 'on', 'start',
     'the Dead Men down; tuned with the owner 2026-10-12', [('Down', 'Enable', 1, 0, 0)])
feat('botdown', G_DOWN, 'AI heisters go down instead of dying', 'on', 'start',
     'live 2026-10-12 on Subway and Retomoto', [('BotDown', 'Enable', 1, 0, 0)])
feat('adrenaline', G_DOWN, 'Help a downed AI heister (stand by him, hold E)', 'on', 'start',
     'the get-up help; the shot animation is in', [('Adrenaline', 'Enable', 1, 0, 0)])
feat('fed', G_DOWN, 'Come back as a policeman after you die', 'on', 'start',
     'seen live 2026-10-11 (Withdrawal); once a round', [('Fed', 'Enable', 1, 0, 0), ('Fed', 'Player', 1, 0, 0)])
feat('cardown', G_DOWN, 'A car blast floors people (revivable) instead of killing', 'off', 'start',
     'offsets are GUESSED: it is in LOG-ONLY mode (Dry=1) until the log is read; OFF here = log only', [('CarDown', 'Dry', 0, 1, 0), ('CarDown', 'Enable', 1, None, 1)])
feat('shield', G_DOWN, 'Human shield rework: the hostage covers you and goes down (revivable)', 'on', 'start',
     'offsets partly GUESSED (the hold fields are logged at each hold); OFF = log only (Dry=1). Tune: Absorb, HostageTakes, DownPct', [('Shield', 'Dry', 0, 1, 0), ('Shield', 'Enable', 1, None, 1)])

feat('dying', G_DOWN, 'Almost dead = you drop into the revivable down; downed heisters hold fire', 'off', 'start',
     'k31dyn: the human ask (trigger 0x8da3b0 from the tick) is a GUESS, shipped with [Dying] Dry=1 (log only) until the log is read; the NoFire half for heisters is data only', [('Dying', 'Enable', 1, 0, 1)])

feat('ambience', G_AV, 'Ambience bed and timed one-shot sounds', 'on', 'start',
     'MCI mp3 worker; the owner kept it when the stutter was found to be the Payday 2 jukebox', [('Ambience', 'Enable', 1, 0, 0)])
feat('stinger', G_AV, 'Event stingers (cues when the heist goes loud, a betrayal ...)', 'on', 'start',
     'short one-shots; the Payday 2 clips are out of the live lists', [('Stinger', 'Enable', 1, 0, 0)])
feat('voice', G_AV, 'Dead Men voice lines for the Dead Men heisters', 'on', 'start',
     'owner 2026-10-23; PlainData live-tested 2026-10-24', [('Voice', 'Enable', 1, 0, 0)])
feat('announcer', G_AV, 'Announcer first: a one-recording Dead Men line stays the stock announcer', 'on', 'start',
     'owner 2026-10-24 (my character lines play first, needs to be the announcer first); the live ini has 0 at the moment', [('Voice', 'Announcer', 1, 0, 1)])
feat('music', G_AV, 'Payday 2 music jukebox (needs Payday 2)', 'off', 'start',
     'it made the game stutter (owner 2026-10-23: gone with it off); Retomoto keeps its own music either way', [('Music', 'Enable', 1, 0, 0)])

# online parity (re/arcade_online_parity.md, 2026-10-25): the same local, read-only sound parts in a Quick / Ranked / LAN / Private round
feat('musiconline', G_AV, 'Online matches: the music jukebox too (recommended off until the SL test passes)', 'off', 'start',
     'klonline.c [Music] Online; read-only snapshot of the online rules (CALM/ACTION by timer or money/END); needs [Music] Enable=1; NOT run live', [('Music', 'Online', 1, 0, 0)])
feat('ambienceonline', G_AV, 'Online matches: ambience bed and one-shots too (recommended off until the SL test passes)', 'off', 'start',
     'klonline.c [Ambience] Online; same snapshot; needs [Ambience] Enable=1; NOT run live', [('Ambience', 'Online', 1, 0, 0)])
feat('stingeronline', G_AV, 'Online matches: event stingers too (recommended off until the SL test passes)', 'off', 'start',
     'klonline.c [Stinger] Online; only the events the online snapshot can show (Loud by timer, Loot by money with OnlineCrew); needs [Stinger] Enable=1; NOT run live', [('Stinger', 'Online', 1, 0, 0)])
feat('censoronline', G_CORE, 'Online matches: head shots blow the head off on this screen too (recommended off until tested)', 'off', 'start',
     'klcensor.c [Censor] Online (key existed, row was missing); heap float per actor, local look only; peers see their own result; NOT run live', [('Censor', 'Online', 1, 0, 0)])
feat('botfill', G_EXP, 'Online lobby: log the AI-heister plan for empty seats (recommended off)', 'off', 'start',
     'klbotfill.c [Bots] OnlineFill; Ready may start below the lobby target (MinPlayers 1); read-only census; re/bots_online_fill.md; NOT run live', [('Bots', 'OnlineFill', 1, 0, 0)])
feat('botfillsquads', G_EXP, 'Online lobby: keep the first N map heister squads for the empty seats (walkers only; recommended off)', 'off', 'start',
     'klbotfill.c [Bots] OnlineFillSquads; heap byte per squad (mask 8 -> 9) before the round; needs OnlineFill=1; may be too late for the collect (probe); NOT run live', [('Bots', 'OnlineFillSquads', 1, 0, 0)])
feat('onlinecoptobot', G_EXP, 'Online AI heisters take cop bullets like Arcade (5 % of a hit; needs the host bot options; recommended on)', 'on', 'start',
     'klbalance.c [BotFill] OnlineCopToBot (percent, 5 = CopToCrew 0.05, 1 = stock Arcade level 1); private ZFFActor vtable per bot, slot 423 wrapped, data only; re/online_bot_damage.md; NOT run live', [('BotFill', 'OnlineCopToBot', 5, 0, 5)])
feat('onlinepbcap', G_EXP, 'Online AI heisters cannot be melted by point-blank bursts (hp cap per second; needs the host bot options; recommended on)', 'on', 'start',
     'klbalance.c [BotFill] OnlinePointBlankCap (hp per bot per 1 s window, 250 = GUESS, 0 = off); inside the OnlineCopToBot slot-423 wrapper; BO10; NOT run live', [('BotFill', 'OnlinePointBlankCap', 250, 0, 250)])
feat('onlinepbrefund', G_EXP, 'Online AI heisters get back point-blank hp that went past the cap (recommended on)', 'on', 'start',
     'klbalance.c [BotFill] OnlinePointBlankRefund; health data write after the step, never above the hp before it; BO11 869 hp window; NOT run live', [('BotFill', 'OnlinePointBlankRefund', 1, 0, 1)])
feat('onlineguardtake', G_EXP, 'Online AI heisters walk into a guarded loot stack after 30 s of waiting (recommended off)', 'off', 'start',
     'klbotfill.c [BotFill] OnlineGuardTake; BO8c: the 30 s release sent all bots into the cop squads at once; off = hold until a stack is clear; NOT run live', [('BotFill', 'OnlineGuardTake', 1, 0, 0)])
feat('onlinevancall', G_EXP, 'Online AI heisters can call the escape van even with the round-keep rules copy (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineVanCall; BO8c: the strict vtable test failed on klroundkeep.c\'s private copy and spent the call; 0 = old strict compare; NOT run live', [('BotFill', 'OnlineVanCall', 1, 0, 1)])
feat('onlinevanstate', G_EXP, 'Online AI heisters board the escape van by its state (waiting) at the exit, not by its position (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineVanState; BO9: the van node stays at the origin so no bot boarded though the van cycled; 60 s wait counts from the call; NOT run live', [('BotFill', 'OnlineVanState', 1, 0, 1)])
feat('onlinelateexit', G_EXP, 'Online AI heisters carrying money head for the van when the round clock is low instead of taking more loot (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineLateExit (seconds left, 75 GUESS, 0 = off); BO9: the only carrier left with 61 s; NOT run live', [('BotFill', 'OnlineLateExit', 75, 0, 75)])
feat('onlinevangather', G_EXP, 'Online AI heisters all walk to the escape box first; the van is called when they are close or after a wait (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineVanGather (+ OnlineGatherM 12 m / OnlineGatherMaxS 25 s, GUESS); BO11: the carrier called the van while the others were 28-41 m away; NOT run live', [('BotFill', 'OnlineVanGather', 1, 0, 1)])
feat('onlinevanhold', G_EXP, 'The online escape van waits (invulnerable, timer kept up, no blow-up) while AI heisters are walking to the box, at most 15 s (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineVanHold (+ OnlineHoldM 30 m, OnlineHoldNearM 18 m, OnlineHoldMaxS 15 s, GUESS); re/van_hold_online.md; BO11: state 3 -> 6 after 1 s, van shot empty; data writes only; NOT run live', [('BotFill', 'OnlineVanHold', 1, 0, 1)])
feat('onlinegiveupretry', G_EXP, 'Online AI heisters try a stack again 45 s after giving it up instead of never again (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineGiveUpRetry (+ OnlineGiveUpRetryS 45 s, GUESS); BO12: 4 given-up stacks stayed blacklisted and the bots idled 3 min; NOT run live', [('BotFill', 'OnlineGiveUpRetry', 1, 0, 1)])
feat('onlineidlevan', G_EXP, 'Online AI heisters with no loot left call the escape van instead of idling (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineIdleVan (+ OnlineIdleVanS 20 s, GUESS); BO12: 0 grabs so nobody called the van; NOT run live', [('BotFill', 'OnlineIdleVan', 1, 0, 1)])
feat('onlinefirestall', G_EXP, 'Online AI heisters under cop fire are not counted as stuck on their way to loot (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineFireStall; BO12: bots pinned down by cops gave up stacks after 12 s; 90 s cap kept; NOT run live', [('BotFill', 'OnlineFireStall', 1, 0, 1)])
feat('onlineboxforce', G_EXP, 'Online AI heisters still outside the escape box while the van waits are sent to its centre again (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineBoxForce; BO13: the carrier stood 3 m outside the box for the whole van wait; NOT run live', [('BotFill', 'OnlineBoxForce', 1, 0, 1)])
feat('onlinevanrecall', G_EXP, 'Online AI heisters still carrying money can call the van again after it left (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineVanRecall; BO14: a carrier grabbed 800k right after the call and was left behind; NOT run live', [('BotFill', 'OnlineVanRecall', 1, 0, 1)])
feat('onlinewaypoints', G_EXP, 'Online AI heisters walk a per-map route of waypoints to the exit when the ini lists one (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineWaypoints; BOS_DD02: 7 bots stalled 139-166 m short of the exit; needs a [BotFillWay_<SLOT>] section; NOT run live', [('BotFill', 'OnlineWaypoints', 1, 0, 1)])
feat('onlinerampfire', G_EXP, 'Online AI heisters fire the DD02 ramp trigger when one stands in its box, if the ini lists the box (recommended on; log only until proven)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineRampFire/OnlineRampDry; DD02: bots are not counted online so make_the_ramp never fires; needs a [BotFillRamp_<SLOT>] section; NOT run live', [('BotFill', 'OnlineRampFire', 1, 0, 1)])
feat('onlineskipdoor', G_EXP, 'Online AI heisters skip loot still locked behind a closed vault door (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineSkipDoorStacks; BOS1: DD01 vault cases (+0x5c behind a door) stalled every bot, 0 taken; NOT run live', [('BotFill', 'OnlineSkipDoorStacks', 1, 0, 1)])
feat('onlineboxwalk', G_EXP, 'Online AI heisters walk to the escape box once the van is called and count as aboard only inside it (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineBoxWalk; BO9: the exit trigger is ~570 cm from the DM01 AllyEscapeBox; read-only scan, game inside test 0x758cb0; NOT run live', [('BotFill', 'OnlineBoxWalk', 1, 0, 1)])
feat('onlineboard', G_EXP, 'Online AI heisters inside the escape box while the van waits are removed from the match like in Arcade (recommended off until tested)', 'off', 'start',
     'klbotfill.c [BotFill] OnlineBoard; calls 0x89c890(actor) (0x907a50\'s own removal); GUESS 60% host-safe, 35% clients see it; needs OnlineBoxWalk; NOT run live', [('BotFill', 'OnlineBoard', 1, 0, 0)])
feat('onlineboxprobe', G_EXP, 'Online AI heister boarding and van position written to the log for the next bench (recommended on)', 'on', 'start',
     'klbotfill.c [BotFill] OnlineBoxProbe; log only: box probe / van probe lines; NOT run live', [('BotFill', 'OnlineBoxProbe', 1, 0, 1)])
feat('syncvanprobe', G_EXP, 'Sync bench log: the escape van real state and place next to its list line (recommended on)', 'on', 'start',
     'klsync.c [Sync] VanProbe; log only, needs Probe=1; BO9: the ZAnimatedVehicle node reads 0,0,0; NOT run live', [('Sync', 'VanProbe', 1, 0, 1)])
feat('hostopts', G_EXP, 'Host-controlled match options: F7 map set, F8 AI heisters; the host map set reaches clients (recommended on after the live test)', 'off', 'start',
     'klhostopt.c [HostOpts] Enable; Steam lobby key klx_opts + UDP 27413; re/host_options.md; NOT run live', [('HostOpts', 'Enable', 1, 0, 0)])
feat('charonline', G_EXP, 'Online: every player heister / mask / outfit shows on every screen; F9 / F11 choose (recommended on after the live test)', 'off', 'start',
     'klcharonline.c [CharOnline] Enable; entity-table index + look via Steam lobby member data klx_look and UDP 27414; re/char_online.md; NOT run live', [('CharOnline', 'Enable', 1, 0, 0)])
feat('hostoptsmenu', G_EXP, 'Host options rows in Mod settings (needs the overlay rebuilt; recommended on after the live test)', 'off', 'start',
     'mkoverlay.py [HostOpts] Menu=1: Host map set + Host options rows, Textures/Neural merged; +4 table entries (est. 4994 of 5000)', [('HostOpts', 'Menu', 1, 0, 0)])

# the look choice (k30fps, owner 2026-10-24): Off / KL look / LiveLeak are three values of ONE key, so two exclusive rows: untick both = Off.
feat('reshade', G_GFX, 'ReShade look 2: LiveLeak camcorder (sky softened by the 1024b preset)', 'on', 'start',
     'the look the owner chose (Look=2); ReShade is on the stack at some hitches, so off = full frame rate', [('Graphics', 'Look', 2, 0, 1)])
F[-1]['exact'] = True; F[-1]['excl'] = 'look'
feat('lookkl', G_GFX, 'ReShade look 1: the older KL look (adaptive sky, glare)', 'off', 'start',
     'Look=1; has its own adaptive sky; untick both look rows = ReShade off (full frame rate)', [('Graphics', 'Look', 1, 0, 1)])
F[-1]['exact'] = True; F[-1]['excl'] = 'look'
feat('camerafx', G_GFX, 'Camera FX (distortion with shots and hits)', 'on', 'start',
     'also a live row in the game: Options > Mod settings (strong = 3)', [('Graphics', 'CameraFX', 3, 0, 1)])
feat('glare', G_GFX, 'Lens glare', 'on', 'start', 'also a live row in Mod settings', [('Graphics', 'Glare', 1, 0, 1)])
feat('aa', G_GFX, 'Anti-aliasing (SMAA)', 'on', 'start', 'also a live row in Mod settings', [('Graphics', 'AA', 1, 0, 1)])
feat('textures', G_GFX, 'Sharper textures (anisotropic x16)', 'on', 'start', 'about 1 % fps', [('Graphics', 'Textures', 1, 0, 1)])
feat('neural', G_GFX, 'Neural rendering (GITC Uplift DLSS / DLAA, F10)', 'off', 'start',
     'ini note: 188 fps with it set aside against 106 .. 178 with it; needs the add-on files', [('Graphics', 'Neural', 1, 0, 0)])
feat('rigid', G_GFX, 'Camera turn filter (heavier, smoother turn)', 'off', 'start',
     "owner 2026-10-24: 'camera awful / fps bad' was this filter's lag; aim is exempt either way", [('Rigid', 'Enable', 1, 0, 0)])
feat('camsmooth', G_GFX, 'Smooth camera in animations and when leaving aim (recommended on)', 'on', 'start',
     "klcamsmooth.c: dt-correct camera step, pivot low-pass, no snap on aim out; mouse turning is never filtered; not live-tested; set Dry=1 Log=1 first", [('CamSmooth', 'Enable', 1, 0, 1)])
feat('camstance', G_GFX, 'Ease the camera when crouching / standing / starting to run (recommended on)', 'on', 'start',
     "klcamsmooth.c StanceMs: a one-frame pivot-height step is eased over 280 ms, critically damped, relative to the feet; mouse turning is never filtered; not live-tested; needs CamSmooth Enable=1", [('CamSmooth', 'StanceMs', 280, 0, 280)])
feat('stancefix', G_GFX, 'Smooth crouch re-toggle: crouching again mid-way keeps the animation going (recommended on)', 'on', 'start',
     "klstancefix.c: reversing Stand_To_Crouch / Crouch_To_Stand no longer restarts the clip at frame 0 (mirrors the phase); data writes only; not live-tested; Dry=1 Log=1 first", [('StanceFix', 'Enable', 1, 0, 1)])
feat('reloadfx', G_GFX, 'Reload camera effects: keep the shot look through a reload (recommended on)', 'on', 'start',
     "klreshade.c ReloadFx: KL_Fire held at a floor (ReloadFxLevel 0.35) for 3.5 s after the last shot and 0.6 s after the magazine refills, so the picture does not go clean; needs the ReShade bridge; not live-tested", [('ReShade', 'ReloadFx', 1, 0, 1)])
def screen_hz():
    """The primary screen's refresh rate (GetDeviceCaps VREFRESH), 60 when it cannot be read."""
    try:
        import ctypes
        u, g = ctypes.windll.user32, ctypes.windll.gdi32
        dc = u.GetDC(0); hz = g.GetDeviceCaps(dc, 116); u.ReleaseDC(0, dc)
        return hz if 1 < hz <= 1000 else 60
    except Exception:
        return 60


# owner 2026-10-24: 'have 4 different options: 240fps, 120fps, 60fps, 30fps'. One row each, they exclude each other (ticking one unticks
# the others); none ticked = limiter off. Recommended = the highest preset <= the screen's refresh rate, the same one klfps.c's
# auto (Fps=0) picks, so an ini with Fps=0 shows that row ticked.
FPS_PRESETS = (240, 120, 60, 30)
HZ = screen_hz()
FPS_REC = next((p for p in FPS_PRESETS if HZ + 2 >= p), 30)   # 2 Hz slack like klfps_preset (59.94 Hz reads as 59)
for _p in FPS_PRESETS:
    feat('fps%d' % _p, G_GFX, 'Frame limiter %d fps (RTSS-style, removes frame-time stutter)' % _p, 'on' if _p == FPS_REC else 'off', 'start',
         'your screen: %d Hz; one of the four presets (ticking one unticks the others, none = no limiter); timed at presentation '
         '(klfps.c, NOT RUN IN THE GAME yet)' % HZ, [('FrameLimit', 'Fps', _p, None, 0), ('FrameLimit', 'Enable', 1, None, 1)])
    F[-1]['preset'] = _p
feat('mapcap', G_GFX, 'Limiter: cap Last Call (DM05A) at 60 fps so it does not run out of memory (recommended on)', 'on', 'start',
     'klfps.c MapCap: min(your rate, 60) only on DM05A; at 120 fps the graphics driver piles up to 586 MB there and the 32-bit game runs out of '
     'address space (K49J), at 60 fps it stays flat (K49H2); other maps keep your rate', [('FrameLimit', 'MapCap', 'DM05A:60', '', 'DM05A:60')])
F[-1]['str'] = 1
feat('frontedge', G_GFX, 'Limiter: front edge sync (wait just before Present)', 'on', 'start',
     'the RTSS setting the owner uses; off = back edge (older picture, not recommended)', [('FrameLimit', 'FrontEdge', 1, 0, 1)])
feat('passivewait', G_GFX, 'Limiter: passive waiting (Sleep instead of a busy loop)', 'off', 'start',
     'the RTSS setting the owner uses (false): busy loop = no scheduler jitter, costs one core a few ms a frame', [('FrameLimit', 'PassiveWait', 1, 0, 0)])
feat('adaptive', G_GFX, 'Limiter: adaptive pacing (follow the machine own frame time) - experimental', 'off', 'dll',
     'k30fps DLL only; simulated (tools/sim_pace.py): -7 % frame spread for -7 % fps, so not recommended; needs a limiter preset', [('FrameLimit', 'Adaptive', 1, 0, 0)])

feat('flash', G_STAB, 'Flash the taskbar when a load or round ends', 'on', 'start',
     "in the owner's live ini (he alt-tabs during the 60..120 s loads)", [('QoL', 'FlashOnReady', 1, 0, 0)])
feat('releasecursor', G_STAB, 'Release the mouse when the game loses focus', 'on', 'start',
     "in the owner's live ini", [('QoL', 'ReleaseCursor', 1, 0, 0)])
feat('fastexit', G_STAB, 'Alt+F4 / close ends the game at once', 'on', 'start',
     'fixed the hang on close (verified live 2026-10-24, 545 ms)', [('KLHook', 'FastExit', 1, 0, 1)])
feat('unstick', G_STAB, 'Put me back when I am stuck inside an object in cover (F7 does it at once)', 'on', 'start',
     'owner 2026-10-24: going into cover put him inside the object for the round; held still in cover with a move key down for 4 s = back to the last free place (offline only; k30cov, not run in the game)', [('Unstick', 'Enable', 1, 0, 1)])
feat('fallrescue', G_STAB, 'Put me back on solid ground when I leave the level or fall out of it', 'on', 'start',
     'owner 2026-10-26: walking off a map edge (DM02 shop rear, Retomoto ledge) restarted the round at full health; the last place he stood still is kept and he is put back before the out-of-world test (klfallrescue.c, not run in the game)', [('FallRescue', 'Enable', 1, 0, 1)])
feat('continue', G_STAB, 'Keep playing after a game assert', 'on', 'start',
     'the hook logs the assert and goes on instead of ending the game', [('KLHook', 'ContinueAsserts', 1, 0, 1)])
feat('memory', G_STAB, 'Room for the big Dead Men maps (address space)', 'on', 'start',
     'avoids the 2 GB heap NULL crash on large .prm files', [('Memory', 'Enable', 1, 0, 1)])
feat('quadring', G_STAB, 'Memory: buffer ring for the screen effects (Last Call runs out of memory without it)', 'on', 'start',
     'klquad.c: the 4 post-process quad buffers get 128 buffers each; the NVIDIA driver no longer piles a block per frame pass (K50H: 1696 -> 18 MB '
     'in 70 s; K50F2/I: flat at 120 fps, same picture); needs the frame limiter (its Reset wrapper)', [('Memory', 'QuadRing', 128, 0, 128)])
feat('steamblock', G_STAB, 'Block Steam stats / leaderboards on modded rounds', 'on', 'start',
     'keeps modded rounds out of your Steam stats and achievements', [('Steam', 'Block', 1, 0, 1)])

feat('match', G_EXP, 'Private-match options (gun, vote, playlist)', 'off', 'start',
     'built, never run live', [('Match', 'Enable', 1, 0, 0)])
feat('netsmooth', G_EXP, 'Smooth remote players\' turning (online)', 'off', 'start',
     'offline-proven only, no online run yet', [('NetSmooth', 'Enable', 1, 0, 0)])
feat('watchdog', G_EXP, 'Watchdog for a stuck AI heister', 'off', 'start',
     'not run in the game', [('QoL2', 'Watchdog', 1, 0, 0)])
feat('names', G_EXP, 'Dead Men map names in the Arcade lists', 'off', 'start',
     'live-tested once (PD1); off until the owner OKs the renaming', [('Names', 'Enable', 1, 0, 0)])
feat('inv', G_EXP, 'Gun shelf: carry more than two guns (F8)', 'off', 'start',
     'research feature, off by default', [('Inv', 'Enable', 1, 0, 0)])
feat('grenade', G_EXP, 'Throw a carried grenade with G (Dead Men style)', 'off', 'start',
     'klgrenade.c step 1: plays the dead HoldGrenade button; only with a grenade in the inventory (DM01 pickups); never run live',
     [('Grenade', 'Throw', 1, 0, 0)])

BY_ID = {f['id']: f for f in F}
assert len(BY_ID) == len(F) and all(f['rec'] in ('on', 'off') for f in F)      # every row is shown with '(recommended on|off)' (rec_text)


# ---------------------------------------------------------------- ini text: find / set (mimics GetPrivateProfileInt: first section, first key)
_SEC = re.compile(r'^\s*\[([^\]]*)\]')
_INT = re.compile(r'^\s*(-?\d+)')


def split_lines(text):
    return text.split('\n')


def find_key(lines, sec, key):
    """-> (line index of key or None, index of the section header or None, index after the section's last real line)"""
    head = None
    for i, ln in enumerate(lines):
        m = _SEC.match(ln)
        if m:
            if head is not None:
                break
            if m.group(1).strip().lower() == sec.lower():
                head = i
        elif head is not None:
            s = ln.strip()
            if s and s[0] not in ';#' and '=' in s and s.split('=', 1)[0].strip().lower() == key.lower():
                return i, head, None
    if head is None:
        return None, None, None
    end = head + 1
    for i in range(head + 1, len(lines)):
        if _SEC.match(lines[i]):
            break
        if lines[i].strip() and lines[i].strip()[0] not in ';#':
            end = i + 1
    return None, head, end


def get_int(lines, sec, key, dflt):
    i, h, e = find_key(lines, sec, key)
    if i is None:
        return dflt
    m = _INT.match(lines[i].split('=', 1)[1])
    return int(m.group(1)) if m else 0


def get_str(lines, sec, key, dflt):
    i, h, e = find_key(lines, sec, key)
    return dflt if i is None else lines[i].split('=', 1)[1].split(';', 1)[0].strip()


def set_key(lines, sec, key, val):
    i, h, e = find_key(lines, sec, key)
    cr = '\r' if lines and lines[0].endswith('\r') else ''
    if i is not None:
        lines[i] = lines[i].split('=', 1)[0] + '=' + str(val) + cr
    elif h is not None:
        lines.insert(e, '%s=%s%s' % (key, val, cr))
    else:
        while lines and lines[-1].strip() == '':
            lines.pop()
        lines += ['%s[%s]%s' % ('', sec, cr), '%s=%s%s' % (key, val, cr), '']


def state(lines, f):
    """-> (on: bool, custom: the master value when it is neither the on nor the off value, else None)"""
    if 'preset' in f:                                       # frame limiter preset: on = limiter on and Fps is this preset (0 = auto)
        fps = get_int(lines, 'FrameLimit', 'Fps', 0)
        on = get_int(lines, 'FrameLimit', 'Enable', 1) != 0 and (fps or FPS_REC) == f['preset']
        return on, None
    sec, key, onv, offv, dflt = f['keys'][0]
    if f.get('str'):                                        # a text key (MapCap): on = not empty
        return get_str(lines, sec, key, dflt) != '', None
    v = get_int(lines, sec, key, dflt)
    if f.get('exact'):                                      # one value of a multi-value key (the look): on only when it IS this value
        return v == onv, None
    return v != offv, (v if v not in (onv, offv) else None)


def preset_conflict(wants):
    """More than one frame-limiter preset wanted on -> error text, else None."""
    on = [fid for fid, w in wants.items() if w and 'preset' in BY_ID[fid]]
    if len(on) > 1:
        return 'pick one frame limiter preset, not %s' % ' + '.join(on)
    for g, what in (('look', 'ReShade look'), ('onlineset', 'online map set')):
        lk = [fid for fid, w in wants.items() if w and BY_ID[fid].get('excl') == g]
        if len(lk) > 1:
            return 'pick one %s, not %s' % (what, ' + '.join(lk))
    return None


def plan(lines, wants):
    """wants: {id: bool}. -> list of (section, key, value) writes for the features whose state differs."""
    out = []
    final = {f['id']: wants.get(f['id'], state(lines, f)[0]) for f in F if 'preset' in f}
    for fid, want in wants.items():
        f = BY_ID[fid]
        on, _ = state(lines, f)
        if on == want:
            continue
        if f.get('excl') and not want and any(wants.get(o['id'], state(lines, o)[0]) for o in F if o.get('excl') == f['excl'] and o['id'] != fid):
            continue                                        # another look is being switched on: its write replaces this value
        if 'preset' in f and not want:                      # unticked: the limiter goes off only when no other preset is ticked
            if not any(final.values()):
                out.append(('FrameLimit', 'Enable', 0))
            continue
        for sec, key, onv, offv, dflt in f['keys']:
            if want:
                out.append((sec, key, onv))
            elif offv is not None:
                out.append((sec, key, offv))
    return list(dict.fromkeys(out))


# ---------------------------------------------------------------- file + safety
def kl2_running():
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True, timeout=15)
        return 'kl2.exe' in r.stdout.lower()
    except Exception:
        return False


def read_ini(path):
    with open(path, 'rb') as fh:
        return fh.read().decode('latin-1')


def verify_with_api(path, writes):
    """Read the file back with the Windows profile API, as the hook does. -> list of problems."""
    bad = []
    try:
        import ctypes
        k = ctypes.windll.kernel32
        for sec, key, val in writes:
            got = ctypes.c_int(k.GetPrivateProfileIntW(sec, key, -99999, path)).value
            if got != val:
                bad.append('[%s] %s: wrote %s, the Windows API reads %s' % (sec, key, val, got))
    except Exception as e:                                  # not Windows
        bad.append('API read-back skipped (%s)' % e)
    return bad


def apply_writes(path, writes, force=False):
    """Back up once, write atomically, verify. -> (message, problems)"""
    if not writes:
        return 'nothing to change', []
    if not force and kl2_running():
        raise SystemExit('kl2.exe is running: close the game first (the hook reads the ini at start).')
    bak = path + BACKUP_SUFFIX
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    text = read_ini(path)
    if text[:2] in ('ÿþ', 'þÿ'):                  # latin-1 view of a UTF-16 BOM: the profile API reads those as Unicode, editing bytes would corrupt it
        raise SystemExit('KLHook.ini is UTF-16: not edited (save it as ANSI first)')
    lines = split_lines(text)
    for sec, key, val in writes:
        set_key(lines, sec, key, val)
    tmp = path + '.tmp-modoptions'
    with open(tmp, 'wb') as fh:
        fh.write('\n'.join(lines).encode('latin-1'))
    os.replace(tmp, path)
    return '%d key(s) written (backup %s)' % (len(writes), os.path.basename(bak)), verify_with_api(path, writes)


def restore_backup(path, force=False):
    bak = path + BACKUP_SUFFIX
    if not os.path.exists(bak):
        raise SystemExit('no backup %s yet' % os.path.basename(bak))
    if not force and kl2_running():
        raise SystemExit('kl2.exe is running: close the game first.')
    shutil.copy2(bak, path)


# ---------------------------------------------------------------- text front end
def rec_text(f):
    return '(recommended %s)' % f['rec']


def when_text(f):
    return {'start': 'next start', 'round': 'next round', 'dll': 'needs the newer DLL (not installed yet)'}[f['when']]


def listing(lines):
    out, grp = [], None
    for f in F:
        if f['group'] != grp:
            grp = f['group']; out.append('\n== %s' % grp)
        on, cust = state(lines, f)
        out.append('  [%s] %-11s %s %s%s  - %s' % ('x' if on else ' ', f['id'], f['label'], rec_text(f),
                                                  '  (custom value %s)' % cust if cust is not None else '', when_text(f)))
    return '\n'.join(out)


def check_defaults(srcdir):
    """Compare each row's dflt with the GetPrivateProfileInt call in klhook\\*.c. -> list of differences."""
    import glob
    seen = {}
    for p in glob.glob(os.path.join(srcdir, '*.c')):
        if '_test' in p:
            continue
        t = open(p, encoding='latin1').read()
        for m in re.finditer(r'GetPrivateProfileInt[AW]?\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*(-?\d+)\s*,', t):
            seen.setdefault((m.group(1), m.group(2)), set()).add(int(m.group(3)))
    bad = []
    for f in F:
        for sec, key, onv, offv, dflt in f['keys']:
            d = seen.get((sec, key))
            if d is None:
                bad.append('%s: [%s] %s is not read by any GetPrivateProfileInt with a literal default%s' % (f['id'], sec, key, ' (read through a helper: not checked)'))
            elif dflt not in d:
                bad.append('%s: [%s] %s row says dflt %s, the sources say %s' % (f['id'], sec, key, dflt, sorted(d)))
    return bad


# ---------------------------------------------------------------- Tk window
def gui(path, force):
    import tkinter as tk
    from tkinter import ttk, messagebox
    root = tk.Tk()
    root.title('KL Mod Options')
    root.geometry('860x720')
    lines = split_lines(read_ini(path))
    vars_, orig = {}, {}
    top = ttk.Frame(root, padding=8); top.pack(fill='x')
    banner = ttk.Label(top, text='', foreground='#b00020'); banner.pack(anchor='w')
    ttk.Label(top, text='KLHook.ini: %s' % path).pack(anchor='w')
    ttk.Label(top, text='Changes take effect at the next game start. Only the boxes you change are written; a backup '
                        '(KLHook.ini.before-modoptions) is kept once.').pack(anchor='w')
    canvas = tk.Canvas(root, highlightthickness=0)
    sb = ttk.Scrollbar(root, orient='vertical', command=canvas.yview)
    body = ttk.Frame(canvas, padding=(8, 0))
    body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=body, anchor='nw')
    canvas.configure(yscrollcommand=sb.set)
    bar = ttk.Frame(root, padding=8); bar.pack(side='bottom', fill='x')
    sb.pack(side='right', fill='y'); canvas.pack(side='left', fill='both', expand=True)
    root.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-e.delta / 120), 'units'))
    status = ttk.Label(bar, text=''); status.pack(side='right')
    grp = None

    def load():
        nonlocal lines
        lines = split_lines(read_ini(path))
        for f in F:
            on, _ = state(lines, f)
            orig[f['id']] = on
            vars_[f['id']].set(on)

    for f in F:
        if f['group'] != grp:
            grp = f['group']
            ttk.Label(body, text=grp, font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(12, 2))
        v = tk.BooleanVar(); vars_[f['id']] = v
        row = ttk.Frame(body); row.pack(fill='x', anchor='w')
        cmd = None
        if 'preset' in f:                                   # the four presets exclude each other
            cmd = (lambda me: lambda: vars_[me].get() and [vars_[o['id']].set(False) for o in F if 'preset' in o and o['id'] != me])(f['id'])
        elif f.get('excl'):                                 # the two look rows exclude each other
            cmd = (lambda me, g: lambda: vars_[me].get() and [vars_[o['id']].set(False) for o in F if o.get('excl') == g and o['id'] != me])(f['id'], f['excl'])
        ttk.Checkbutton(row, text='%s %s' % (f['label'], rec_text(f)), variable=v, command=cmd).pack(anchor='w')
        ttk.Label(row, text='%s - %s' % (when_text(f), f['why']), foreground='#666666', wraplength=780).pack(anchor='w', padx=(24, 0))
    load()

    def running():
        r = (not force) and kl2_running()
        banner.config(text='kl2.exe is running: close the game, then press Reload. Saving is refused meanwhile.' if r else '')
        return r

    def save():
        if running():
            return
        wants = {fid: v.get() for fid, v in vars_.items() if v.get() != orig[fid]}
        try:
            msg, bad = apply_writes(path, plan(lines, wants), force)
        except SystemExit as e:
            messagebox.showerror('KL Mod Options', str(e)); return
        load()
        status.config(text=msg + ('; PROBLEMS: ' + '; '.join(bad) if bad else ' - read back OK'))

    def recommended():
        for f in F:
            vars_[f['id']].set(f['rec'] == 'on')
        status.config(text='Recommended chosen - press Save to write it')

    def undo():
        if running():
            return
        if messagebox.askyesno('KL Mod Options', 'Put back the KLHook.ini saved before the first change from this tool?'):
            try:
                restore_backup(path, force)
            except SystemExit as e:
                messagebox.showerror('KL Mod Options', str(e)); return
            load(); status.config(text='backup restored')

    ttk.Button(bar, text='Recommended', command=recommended).pack(side='left')
    ttk.Button(bar, text='Reload', command=lambda: (load(), running(), status.config(text='reloaded'))).pack(side='left', padx=6)
    ttk.Button(bar, text='Save', command=save).pack(side='left')
    ttk.Button(bar, text='Restore the backup', command=undo).pack(side='left', padx=6)
    running()
    root.mainloop()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--game', default=os.environ.get('KL_DD', DD))
    ap.add_argument('--ini')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--recommended', action='store_true')
    ap.add_argument('--set', nargs='+', metavar='ID=on|off')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--restore', action='store_true')
    ap.add_argument('--check-defaults', metavar='KLHOOK_DIR')
    a = ap.parse_args()
    if a.check_defaults:
        bad = check_defaults(a.check_defaults)
        print('\n'.join(bad) if bad else 'all defaults agree with the sources')
        return 1 if any('says dflt' in b for b in bad) else 0
    path = os.path.abspath(a.ini or os.path.join(a.game, 'KLHook.ini'))
    if not os.path.isfile(path):
        raise SystemExit('KLHook.ini not found: %s (use --game or --ini)' % path)
    if a.restore:
        restore_backup(path, a.force); print('backup restored'); return 0
    if not (a.list or a.recommended or a.set):
        gui(path, a.force); return 0
    lines = split_lines(read_ini(path))
    if a.list:
        print(listing(lines))
    wants = {}
    if a.recommended:
        wants = {f['id']: f['rec'] == 'on' for f in F}
    for s in a.set or []:
        k, _, v = s.partition('=')
        if k not in BY_ID or v not in ('on', 'off'):
            raise SystemExit('bad --set %r (id=on|off; ids: %s)' % (s, ' '.join(BY_ID)))
        wants[k] = v == 'on'
    if preset_conflict(wants):
        raise SystemExit(preset_conflict(wants))
    if wants:
        w = plan(lines, wants)
        for sec, key, val in w:
            print('  [%s] %s = %s' % (sec, key, val))
        if not w:
            print('nothing to change')
        elif a.apply:
            msg, bad = apply_writes(path, w, a.force)
            print(msg); print('\n'.join(bad) if bad else 'read back with the Windows API: OK')
            return 1 if bad else 0
        else:
            print('(dry run: add --apply to write)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
