# Mod options (2026-10-24)

Every owner-facing on/off feature of the Dog Days mod, with the KLHook.ini key, the live value, the recommendation and when a change applies.
Tool: `tools/kl_mod_options.py` (run `KL Mod Options.bat`; installed by `INSTALL KL Mod Options.bat` into `<DD>\KLModOptions\`). It shows one checkbox per
row, labelled "(recommended on)" or "(recommended off)", has a Recommended button, backs KLHook.ini up once (`KLHook.ini.before-modoptions`),
refuses to save while kl2.exe runs, and only rewrites the lines of features whose state changed. CLI: `--list`, `--recommended`, `--set id=on|off`, `--apply`, `--restore`.

Takes effect: keys are read by GetPrivateProfileInt at DLL init, so nearly every row applies at the next game start. Rows marked "needs newer DLL"
are the three `[FrameLimit]` rows: the installed DLL (k29b, md5 aa912e09d2d5d6ca010899d505d70341) was built without klfps.c, so those keys do nothing until a DLL with it is installed (then change `when` to 'start' in the tool).

2026-10-24 review: the three FrameLimit rows are now `when=start` (the k29c DLL has klfps.c; staged in `buildk29c_1024`, install script `tools/k29c_install.ps1`). New rows: `announcer` ([Voice] Announcer, recommended on; live ini has 0), and the `cardown` row also writes [CarDown] Enable=1 when turned on. The tool refuses to edit a UTF-16 ini.

2026-10-27 review (scheduled check-in): the rows had fallen behind the hook's own ini. `klhook\KLHook.ini` (the documented defaults the local
sessions keep) marks 19 keys `(recommended on) proven live: <bench>` (CE27_ALL2D..H, BOSE5c..g, DD01ce4/ce6, MPX, the Grades Arcade rotation)
whose rows still said `recommended off until benched`, so the Recommended button would have switched the owner's proven online HUD, Grades,
HostOpts and CharOnline OFF. Those 19 rows now say on with the bench in `why`; five proven keys got rows (`onlineboardcarrier`,
`onlineintrocarrier`, `onlineshopnames`, `onlinetaghidedead`, `onlinetagprobe`). New check `--check-rec klhook\KLHook.ini`: every row's
recommendation against the marker on its OWN key (the first key no other row writes), plus the proven recommended-on keys that have no row;
it must print "every row agrees". Table-shape fix: the tag and Grades rows had the shared prerequisite (`[HUD] OnlineTags`, `[Grades] Enable`)
as their FIRST key, so their state was read from the prerequisite (onlinetagstyle showed on while OnlineTagStyle=0) and turning
`gradesonlinetags` off wrote `OnlineTags=0` + `Grades Enable=0` (every tag and Grades row off). The own key is first now and the prerequisite
follows with off value None (written when turning on, left alone when turning off). `tools/kl_mod_options_test.py` (32 checks) covers all of it.
Rule for new rows: when the local sessions move a key to `(recommended on) proven live` in klhook\KLHook.ini, flip its row too (`--check-rec`
fails until it is done).

2026-10-27 14:50 UTC (scheduled check-in): the repo ini had no line for 37 row keys (17 modules without a section: [Shop], [Adrenaline],
[BotDown], [Shield], [Voice] Enable, ...; the owner's live ini carries most of them), so nothing in the hook's own documented defaults said
those keys existed; and c9's [Input] PumpNoBlock / MouseMoveMs and [Stall] Trace / StallMsgMs were read by klhook.c but documented nowhere.
Now: `[Stall]` and `[Input]` sections (PumpNoBlock=1 `(recommended on) proven live: C27_PNB1 / HUD6`, folded with the line c9 committed at 14:54 while this ran), one commented
`;Key=<DLL default>   ; KL Mod Options row '<id>': <label> (recommended ...)` line per rowless key in its section (new sections sit before
[Online]), the `pumpnoblock` row (G_STAB, on), and `--check-ini klhook klhook\KLHook.ini` (exit 1 while a row key is
unmentioned; `--verbose` lists the 487 other keys the hook reads that the ini leaves out: probes, logs, per-map tuning). `ini_rec` now
reads a marker on a commented `;Key=` line too (16 more rows checked) and the new lines carry markers (31 more): 66 rows without a
marker now, was 113; every checked row agrees. The other direction
(an ini key no source reads) was tried and dropped: names come from tables, sprintf (P%d, Thr%d) and per-map sections, every try listed
live keys as stale. `kl_mod_options_test.py` 44 checks.

2026-10-27 19:00 UTC (scheduled check-in): after ce's page II online proof (ALL2Y / P2P5G, SHIP 1027y installed 15:30) the ini marked
`[ShopPage] OnlineLook / OnlineSend / OnlineApply / OnlineEarlyMake` `(recommended on; benched ...)` (2fe8304) but the `shoponline` row still
said off (`--check-rec` and the self-test FAILED at head), and the three buy keys had no row because `check_rec`'s row-less scan read only
ACTIVE `Key=` lines: those keys are carried only as `;Key=0` in the hook's ini. Now: `shoponline` on (OnlineLook), new rows `shoponlinebuy`
(OnlineApply, writes OnlineSend too since apply stays OFF without it) and `shoponlineearly` (OnlineEarlyMake), `shoponline2` (OnlinePage2)
stays off (older step, OnlineApply wins). The row-less scan reads `;Key=` lines too, each key once. `kl_mod_options_test.py` 46 checks.
Left alone: `hire` / `hireonline` still say off: the ini's `[Hire] Online` note says `(recommended on with Enable=1)` (HRF2 / HRP2 online,
both seats) but `[Hire] Enable` itself carries no marker and needs the Hire window baked into the level (tools/kl_hire_bake.py), so a
Recommended click must not turn it on until ce marks Enable; `ini_rec` does not see that marker (the comment line naming the key has none).

Note: the Recommended button would flip the owner's live Neural from 1 to 0 (the ini notes 188 fps off against 106..178 on), CarDown Dry to off, and Music/Rigid are already off.

## Inventory
| id | feature (label in the tool) | ini key(s) | live now | recommended | takes effect | why |
|---|---|---|---|---|---|---|
| | **Core** | | | | | |
| allmaps | Mod features on the nine stock Fragile Alliance maps | [KLHook] AllMaps=1/0 | on (AllMaps=1) | on | next start | owner: every feature also on the stock maps; their Steam stats stay blocked |
| expansion | Dead Men maps in the Arcade menu | [Expansion] Enable=1/0 | on (Enable=1) | on | next start | the expansion itself: the Dead Men map pages and their redirects |
| character | Heister, mask and outfit select | [Character] Enable=1/0 | on (Enable=1) | on | next start | the Heister page in Arcade (Dead Men and Payday 2 masks) |
| guns | Dead Men gun looks and start rifle (Mod settings rows) | [Guns] Enable=1/0 | on (Enable=1) | on | next start | works with the maps built with the guns; harmless elsewhere |
| shop | More guns in the weapon shop | [Shop] Enable=1/0 | on (Enable=1) | on | next start | run live 2026-10-20 (rows swapped for Minimi, HK69, Type 81, Rem 700) |
| hud | Mod HUD (kill feed, scoreboard, trackers, names) | [HUD] Enable=1/0 | on (Enable=1) | on | next start | the owner plays with it |
| balance | One damage scale for you, police and crew (Dead Men maps) | [Balance] Enable=1/0 | on (Enable=1) | on | next start | v71 balance: the owner found the stock numbers too tanky |
| climb | Free climb (hold W + E at a ledge) | [Climb] Enable=1/0 | on (Enable=1) | on | next start | Dead Men's climb (luvsic's), only on maps with the climb clips |
| censor | Head shots blow the head off (pixelated censor) | [Censor] Enable=1/0 | on (Enable=1) | on | next start | owner item 9; heap data only |
| censorlate | Censor also corpses, AI heisters and you (late head blow) (recommended on) | [Censor] Late=1/0, Player=1/0 | on | on | next start | k31cen: calls the game's BlowHeadOff 350 ms after death; not live-tested |
| hidevan | Hide the van escape timer until the van is there (recommended on) | [HUD] HideIdleEscape=1/0 (HideIdleEscapeDry) | on | on | next start | klhud.c van card; needs [HUD] Enable=1 |
| vanblow | Escape vehicle can blow up when nobody is aboard (recommended on) | [VanBlow] Enable=1/0 (Dry, Log, EmptyDelay, HealthMax) | on (Enable=1) | on | next start | klescort.c (k33): owner 2026-10-24 'they never blow up'. FollowOutShield=3 kept the van invulnerable the whole wait; now the shield is off while no record is aboard (1.5 s), on again when somebody boards. Needs a non-stock level (Dog Days' own FA maps are never shielded). Not run in the game |
| clubcalm | Last Call probe: log the hand item and shots (recommended off) | [ClubCalm] Enable=1/0 | off | off | next start | read-only; data for the calm-until-the-gun-is-drawn switch |
| animprobe | Animation probe: log the player Play calls around gait changes (diagnostic) (recommended off) | [AnimProbe] Enable=1/0 (Ms=600 window, MaxLines=400) | off (Enable=0) | off | next start | klanimprobe.c; LOG ONLY, passes every call through; detours Play 0x4da1d0 so only a TEST dll patches it (SHIP refuses, logs it); NOT live-tested; look for 'animprobe:' CHANGE / PLAY / RET lines |
| gunsound | Gun fire as loud / driven as the S&W MP45 (recommended on) | no ini key: build\gunsnd_1024c INSTALL / UNDO gun sounds.bat | - | - | install | kl_gunsnd_match.py; patches each map .WAV in place |
| crewlook | Random looks for the AI heisters | [Crew] Random=1/0 | on (Random=1) | on | next start | no body twice, never the one you wear |
| | **AI crew and traitors** | | | | | |
| bots | AI heisters in Arcade | [Bots] Enable=1/0 | on (Enable=1) | on | next start | the whole crew system (bots); other crew rows need it |
| escort | One AI heister stays beside you | [Bots] Escort=1/0 | on (Escort=1) | on | next start | seen live 2026-10-11 (standing player only) |
| followout | The crew follows you out once the vehicle is called | [Bots] FollowOut=1/0 | on (FollowOut=1) | on | next start | seen live 2026-10-11 (run FO_J1) |
| boardall | Idle AI heisters are sent to the escape vehicle | [Bots] BoardAll=1/0 | on (BoardAll=1) | on | next start | seen live 2026-10-11 (runs L12a / L12b) |
| traitors | Traitors: an AI heister can turn on you (20 % of rounds) | [Bots] Backstab=20/0, [Bots] Tune=1/keep, [Bots] TraitorFoe=1/keep | on (Backstab=20) | on | next start | owner asked for backstabbing 2026-10-11; 35 -> 20 on 2026-10-23, max 1 a round |
| crewhop | AI heisters cross places the navmesh cannot (Retomoto lobby) | [CrewHop] Enable=1/0 | on (Enable=1) | on | next start | the lobby car is down; without it they stand |
| crewjoin | AI heisters follow the tower-to-lobby jump (Retomoto) | [CrewJoin] Enable=1/0 | on (Enable=1) | on | next start | two navmeshes joined only by kljoin.c |
| traits | A small trait per Dead Men character | [Traits] Enable=1/0 | on (Enable=1) | on | next start | enabled in the live ini; the effect is small and logged |
| talk | Kane and Lynch dialogue and chatter | [Talk] Enable=1/0 | on (Enable=1) | on | next start | Retomoto countdown and the idle chatter |
| | **Down, revive, fed** | | | | | |
| down | You go down and can be revived | [Down] Enable=1/0 | on (Enable=1) | on | next start | the Dead Men down; tuned with the owner 2026-10-12 |
| botdown | AI heisters go down instead of dying | [BotDown] Enable=1/0 | on (Enable=1) | on | next start | live 2026-10-12 on Subway and Retomoto |
| adrenaline | Help a downed AI heister (stand by him, hold E) | [Adrenaline] Enable=1/0 | on (Enable=1) | on | next start | the get-up help; the shot animation is in |
| fed | Come back as a policeman after you die | [Fed] Enable=1/0, [Fed] Player=1/0 | on (Enable=1) | on | next start | seen live 2026-10-11 (Withdrawal); once a round |
| cardown | A car blast floors people (revivable) instead of killing | [CarDown] Dry=0/1 | off (Dry=1) | off | next start | offsets are GUESSED: it is in LOG-ONLY mode (Dry=1) until the log is read; OFF here = log only |
| dying | Almost dead = you drop into the revivable down; downed heisters hold fire | [Dying] Enable=1/0 | on (default, no key) | off until read | next start | k31dyn (2026-10-24): the human ask (trigger 0x8da3b0 from the tick) is a GUESS, staged with [Dying] Dry=1; also forces [BotDown] NoFire=1 (heisters stop shooting from the floor) |
| shield | Human shield rework: the hostage covers you and goes down (revivable) | [Shield] Dry=0/1 (+ Enable=1) | on (Dry=0) | on | next start | klshield.c (k30shd): Absorb/HostageTakes/DownPct/ReleaseDown keys; hold fields partly GUESSED, logged at each hold; OFF here = log only (Dry=1) |
| | **Sound and music** | | | | | |
| ambience | Ambience bed and timed one-shot sounds | [Ambience] Enable=1/0 | on (Enable=1) | on | next start | MCI mp3 worker; the owner kept it when the stutter was found to be the Payday 2 jukebox |
| stinger | Event stingers (cues when the heist goes loud, a betrayal ...) | [Stinger] Enable=1/0 | on (Enable=1) | on | next start | short one-shots; the Payday 2 clips are out of the live lists |
| voice | Dead Men voice lines for the Dead Men heisters | [Voice] Enable=1/0 | on (Enable=1) | on | next start | owner 2026-10-23; PlainData live-tested 2026-10-24 |
| music | Payday 2 music jukebox (needs Payday 2) | [Music] Enable=1/0 | off (Enable=0) | off | next start | it made the game stutter (owner 2026-10-23: gone with it off); Retomoto keeps its own music either way |
| | **Graphics and camera** | | | | | |
| reshade | ReShade look 2: LiveLeak camcorder (sky softened by the 1024b preset) | [Graphics] Look=2/0 | Look=2 exactly (the two look rows exclude each other; both unticked = Look=0, ReShade off) | on | next start | the look the owner chose (Look=2); ReShade is on the stack at some hitches, so off = full frame rate |
| lookkl | ReShade look 1: the older KL look (adaptive sky, glare) | [Graphics] Look=1/0 | Look=1 exactly | off | next start | Look=1; has its own adaptive sky; untick both look rows = ReShade off (full frame rate) |
| camerafx | Camera FX (distortion with shots and hits) | [Graphics] CameraFX=3/0 | on (CameraFX=3) | on | next start | also a live row in the game: Options > Mod settings (strong = 3) |
| glare | Lens glare | [Graphics] Glare=1/0 | on (Glare=1) | on | next start | also a live row in Mod settings |
| aa | Anti-aliasing (SMAA) | [Graphics] AA=1/0 | on (AA=1) | on | next start | also a live row in Mod settings |
| textures | Sharper textures (anisotropic x16) | [Graphics] Textures=1/0 | on (Textures=1) | on | next start | about 1 % fps |
| neural | Neural rendering (GITC Uplift DLSS / DLAA, F10) | [Graphics] Neural=1/0 | on (Neural=1) | off | next start | ini note: 188 fps with it set aside against 106 .. 178 with it; needs the add-on files |
| rigid | Camera turn filter (heavier, smoother turn) | [Rigid] Enable=1/0 | off (Enable=0) | off | next start | owner 2026-10-24: 'camera awful / fps bad' was this filter's lag; aim is exempt either way |
| camsmooth | Smooth camera in animations and when leaving aim (recommended on) | [CamSmooth] Enable=1/0 (PivotMs, BlendMs, AimOutMs, AimInMs, DtFix, StanceMs, StanceCm, Log, Dry) | on (Enable=1) | on | next start | klcamsmooth.c; dt-correct camera step + pivot low-pass + no snap on aim out; mouse turning never filtered; NOT live-tested, first run Dry=1 Log=1 |
| camstance | Ease the camera when crouching / standing / starting to run (recommended on) | [CamSmooth] StanceMs=280 (0 = off), StanceCm=6 (pivot step per frame that counts as a stance pop) | on (StanceMs=280) | on | next start | klcamsmooth.c last stage: pivot-offset-from-feet step eased critically damped over StanceMs, relative to the feet (running does not lag), mouse never filtered; stance flag not found, the pivot step is the detector (GUESS); NOT live-tested, first run Dry=1 Log=1 and look for 'camsm: STANCE' lines |
| fps240 | Frame limiter 240 fps (RTSS-style, removes frame-time stutter) | [FrameLimit] Fps=240 + Enable=1 (unticking all four = Enable=0) | auto (Fps=0) = the highest preset <= the screen refresh | on if the screen shows it and no higher preset fits, else off | next start (k29d DLL) | owner 2026-10-24: four presets 240/120/60/30, one at a time; recommended = the highest the screen shows (NOT RUN IN THE GAME yet) |
| fps120 | Frame limiter 120 fps (RTSS-style, removes frame-time stutter) | [FrameLimit] Fps=120 + Enable=1 (unticking all four = Enable=0) | auto (Fps=0) = the highest preset <= the screen refresh | on if the screen shows it and no higher preset fits, else off | next start (k29d DLL) | owner 2026-10-24: four presets 240/120/60/30, one at a time; recommended = the highest the screen shows (NOT RUN IN THE GAME yet) |
| fps60 | Frame limiter 60 fps (RTSS-style, removes frame-time stutter) | [FrameLimit] Fps=60 + Enable=1 (unticking all four = Enable=0) | auto (Fps=0) = the highest preset <= the screen refresh | on if the screen shows it and no higher preset fits, else off | next start (k29d DLL) | owner 2026-10-24: four presets 240/120/60/30, one at a time; recommended = the highest the screen shows (NOT RUN IN THE GAME yet) |
| fps30 | Frame limiter 30 fps (RTSS-style, removes frame-time stutter) | [FrameLimit] Fps=30 + Enable=1 (unticking all four = Enable=0) | auto (Fps=0) = the highest preset <= the screen refresh | on if the screen shows it and no higher preset fits, else off | next start (k29d DLL) | owner 2026-10-24: four presets 240/120/60/30, one at a time; recommended = the highest the screen shows (NOT RUN IN THE GAME yet) |
| frontedge | Limiter: front edge sync (wait just before Present) | [FrameLimit] FrontEdge=1/0 | on (FrontEdge=1, absent = DLL default) | on | next start (k29c DLL; before it is installed the key does nothing) | the RTSS setting the owner uses; off = back edge (older picture, not recommended) |
| passivewait | Limiter: passive waiting (Sleep instead of a busy loop) | [FrameLimit] PassiveWait=1/0 | off (PassiveWait=0, absent = DLL default) | off | next start (k29c DLL; before it is installed the key does nothing) | the RTSS setting the owner uses (false): busy loop = no scheduler jitter, costs one core a few ms a frame |
| adaptive | Limiter: adaptive pacing (follow the machine own frame time) - experimental | [FrameLimit] Adaptive=1/0 | off (Adaptive=0, absent = DLL default) | off | next start (k30fps DLL only) | simulated (tools/sim_pace.py): about -7 % frame spread for -7 % fps, so not recommended |
| | **Stability and fixes** | | | | | |
| flash | Flash the taskbar when a load or round ends | [QoL] FlashOnReady=1/0 | on (FlashOnReady=1) | on | next start | in the owner's live ini (he alt-tabs during the 60..120 s loads) |
| releasecursor | Release the mouse when the game loses focus | [QoL] ReleaseCursor=1/0 | on (ReleaseCursor=1) | on | next start | in the owner's live ini |
| fastexit | Alt+F4 / close ends the game at once | [KLHook] FastExit=1/0 | on (FastExit=1, absent = DLL default) | on | next start | fixed the hang on close (verified live 2026-10-24, 545 ms) |
| unstick | Put me back when I am stuck inside an object in cover (F7 does it at once) | [Unstick] Enable=1/0 | on (Enable=1, absent = DLL default) | on | next start (k30cov DLL; before it is installed the key does nothing) | owner 2026-10-24: cover put him inside an object for the round; held still in cover with a move key down for 4 s (CoverMs) = back to the last free place; Plain=1 also in plain walking (6 s); Dry=1 logs only; offline only; not run in the game |
| continue | Keep playing after a game assert | [KLHook] ContinueAsserts=1/0 | on (ContinueAsserts=1) | on | next start | the hook logs the assert and goes on instead of ending the game |
| memory | Room for the big Dead Men maps (address space) | [Memory] Enable=1/0 | on (Enable=1) | on | next start | avoids the 2 GB heap NULL crash on large .prm files |
| steamblock | Block Steam stats / leaderboards on modded rounds | [Steam] Block=1/0 | on (Block=1) | on | next start | keeps modded rounds out of your Steam stats and achievements |
| pumpnoblock | Never wait for a window message the game cannot take (background window freeze) | [Input] PumpNoBlock=1/0 | on in the repo ini (PumpNoBlock=1; the owner's SHIP 1027x has no wrap and ignores it) | on | next start | c9 2026-10-27: the pump's keep-Peek sees a WM_MOUSEMOVE the remove-Peek cannot take, GetMessageA / ReShade then wait for forever (CE27_HUD5, P2P4C client freeze dumps); benched C27_PNB1 / HUD6 10-27, both seats, 0 faults |
| | **Experimental / not tried in play** | | | | | |
| match | Private-match options (gun, vote, playlist) | [Match] Enable=1/0 | off (Enable=0, absent = DLL default) | off | next start | built, never run live |
| netsmooth | Smooth remote players' turning (online) | [NetSmooth] Enable=1/0 | off (Enable=0, absent = DLL default) | off | next start | offline-proven only, no online run yet |
| watchdog | Watchdog for a stuck AI heister | [QoL2] Watchdog=1/0 | off (Watchdog=0, absent = DLL default) | off | next start | not run in the game |
| names | Dead Men map names in the Arcade lists | [Names] Enable=1/0 | off (Enable=0, absent = DLL default) | off | next start | live-tested once (PD1); off until the owner OKs the renaming |
| inv | Gun shelf: carry more than two guns (F8) | [Inv] Enable=1/0 | off (Enable=0, absent = DLL default) | off | next start | research feature, off by default |

## Data-side features (no ini switch; each has its own undo script)
White shop, cover boxes, Dead Men voice .LOC graft, Hot Coffee II door fix, and the existing in-game "Mod settings" page rows (window KLGuns, rows KLS*). Undo with the matching script beside each install in tools/ and the work folder.

## Why no in-game page
The menu manager table has 5096 slots with a 5000 hazard (re/hud_menu.md 1.1); every new window tag costs slots and the Mod settings window already holds the guard maximum of 9 rows (mkoverlay.py). The Match page was never seen live and no live test is allowed in this task. A Tk tool is safe and testable offline. Future work: a two-row selector (feature name row + On/Off row) using the klchar.c private-vtable name pattern, `<Text>` values cost no slots.
