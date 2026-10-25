# Host-controlled match options (klhostopt.c, 2026-10-25; built, NOT run live)

Owner: "more options you switch on n off ... maps, payday guns or not, ai heisters or not".
Builds: klhook/out_hostopts_1025a (SHIP c3f32a80...) and _test (fc18e73a...). Overlay: C:/kl_build_1024/hostopts_1025/Overlay/Patch01.zip (not installed).

## Where
No lobby-screen row: the FA lobby rows are code focus rows with clamps as immediates (lobby_options.md) and a new row costs ~4 menu-table
entries (about 10 free on a gamepad). Instead: hotkeys F7 / F8 (work in the lobby) and, with the overlay, rows in Options > Mod settings.
- F7 map set: Dog Days -> Dead Men -> Mixed random ([Expansion] OnlineSet 0 / 2 / 9). F8 AI heisters ([Bots] OnlineFill). Beep on a press. Not as a client.
- Rows (overlay built with [HostOpts] Enable=1 + Menu=1): "Host: map set" (KLSHMap, 3) and "Host: AI / solo / PD2 guns" (KLSHOpt, 8 = bit0 AI, bit1 Solo, bit2 PD2).
  Textures + Neural merged into "Textures / Neural (next start)" (KLSNext). Tags 4275 -> 4279 (+4), estimated live table 4994 of 5000.
- PD2 guns = [ShopPage] Enable, read at START only: takes effect next start. AI = klbf_on/klbf_sq live (+ MinPlayers 1). Solo = kllb_solo live.

## Transport (map set only; the other options act on the host machine)
String `m<set>a<ai>s<solo>` (set = OnlineSet value). Steam lobby data key `klx_opts` (host writes on change and every 5 s, client reads every 1 s;
needs klmm.c proxy, installed by Enable=1 + Steam=1) and UDP broadcast port 27413 `KLHO1;m2a1s0` every 2 s (System Link has no Steam lobby).
Client applies it to kls_online_set IN MEMORY (role [session+0x54]==3), own value back when the session ends. Role 2 host / 3 client: GUESS (as klserver.c).

## Live test (System Link solo route, SL7.ini, TEST build, [HostOpts] Enable=1, [Lobby] MinPlayers=1)
Host: expect `hostopts: on; map set ...`, then in the lobby `hostopts: session role 2 (HOST)`, `hostopts: HOST broadcast on UDP 27413: m2a0s0 (sendto N>0)`.
Press F7: `hostopts: set map set = 1 (Dead Men) - [Expansion] OnlineSet=2`, then a new broadcast line m2...; Ready: `LOAD F01: online=1 OnlineSet=2 -> page 2`.
F8: `hostopts: set AI heisters = 1 ... [Bots] OnlineFill=1 (live)`. Two PCs/LAN: client logs `hostopts: CLIENT heard the host on UDP: m2a..` then
`CLIENT applies the host's map set 2 (own 0)`; its LOAD line shows the host's page; after leaving: `session over: own map set 0 is back`.
Steam lobby (Quick/Player Match, BuildKey on): `HOST Steam lobby ... klx_opts=... (ok=1)` / `CLIENT read the host's Steam lobby klx_opts=`.
Not testable alone: the client side. Heist time proof (TEST): `lobbyopt-test: ROUND LENGTH: state 25 -> 31 took X s (set heist time N min ...)`.

## Related fix in the same build (kllobbyopt.c)
SL7: an extra RIGHT at the max let the stock clamp reset the value to 5. Now a press above the stock range is always taken over (at the max the same value is re-applied;
same for time LEFT at the min). m_fRoundTime read (vtbl+0x94, NaN) dropped; TEST logs the measured state 25 -> 31 span instead.

## 1025b (after the first live run on out_hostopts_1025a_test)
- BUG fixed: klho_put changed klho.map and the ini but not kls_online_set, so the host's own LOAD kept OnlineSet=2. It now sets kls_online_set at once (F7 and the row); proof: `LOAD F01: ... OnlineSet=9` after F7 to mixed random.
- Round length (10 min set, 83 s / 83.5 s / 39.8 s measured between session state 25 and 31): CAUSE NOT YET KNOWN. State 0x19 = round runs, 0x1f = round over (klbot.c).
  The round clock is float [rules+0x4c] (left) with [rules+0x50] played, [rules+0x200] end timer, [score+0x3c] length = 0x6d3130() (constant 360.0 in Arcade); an online round's source of the
  length was never read. Not proven that the lobby minutes reach it, and a lone host's round can also end by itself (all heisters dead / escaped). TEST now logs
  `lobbyopt: round clock at state 25 / 1.5 s into the round / running (every 10 s) / at state 31` with left, played, end timer, score len/cut/m and the lobby minutes: the first run decides
  (left starts at 600 and ends > 0 = another cause ended the round; left starts at 360/other = the length does not come from the lobby).
- [Lobby] RoundClockFix=1 (default 0, GUESS): once per round, 1..5 s into state 0x19, writes [rules+0x4c] = lobby minutes * 60 when it is lower. Only try it after the log shows [rules+0x4c] is the counting clock.
