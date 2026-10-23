# Dead Men voices for the Dead Men heisters (2026-10-23)

Owner: "the dead men characters dont have their own voicelines still ... give them unique talks when theyre together even in
dog days too and kane n lynch". Tool: `tools/kl_dmvoice.py`. Hook part: `klhook/klvoice.c` ([Voice]) and `[Talk] StockLevels`
in `klhook/kltalk.c`. NOTHING HERE HAS RUN IN THE GAME (the agent that built it was told not to start kl2.exe).

## 1. What was wrong
- The FA event lines (Backstab, JackPot, CallEsc, ...) are Dog Days recordings, one per heister voice (`_C1.._C9`). A Dead Men
  body took a Dog Days heister's voice (klchar `DMVoice`, klcrew `Voice=1` give each body a free voice NUMBER, but the
  recordings behind the number are still Dog Days').
- kltalk only talked on levels that are not stock, and its pools for the six Dead Men characters used the generic Squad / Squad02
  campaign voices; Kane / Lynch pairs used 4 + 4 lines.

## 2. The voice table (GUESS - nobody listened)
Dead Men's FA characters never spoke in the campaign. Kane and Lynch speak as themselves; the rest get the campaign speaker whose
voice fits the name/nationality best (`SPEAKERS` in the tool, one line each with the reason):

| wardrobe | body | campaign speaker (key suffix) | clips |
|---|---|---|---|
| 9 | Kane | `_Hero` (Kane himself) | 279 |
| 10 | Lynch | `_Lynch` | 377 |
| 11 | Ashkanan | Thapa | 85 |
| 12 | Meldal | Carlos | 35 |
| 13 | Red | `_Merc` | 171 |
| 14 | Parker | Rific | 33 |
| 15 | Standen | Shelly | 54 |
| 16 | Hutchison | `_Merc01` | 37 (`_Merc02`, 7 clips, unused) |

Change a row in `SPEAKERS` and rebuild to re-cast.

## 3. Event lines
`build` reads each installed `KLExpansion\Maps\<map>` (all 27: DD01..DD09, the DM maps, T01), takes the map's English .LOC,
collects the event leaves under `Multiplayer/*/<Event>_NN[_R]_C<n>` (`<Event>_NN[_R]`, 273 on DM01) and for each of the eight
characters grafts one campaign clip per leaf into the map's .SND / .WHD / .WAV / _LS.SND (`kl_snd.merge`, like kl_dmlines.py)
as .LOC leaf `KLVoice/<Name>/<Event>`; radio twins `Event_R` go to `KLVoice/<Name>_R/Event` (a .LOC table holds 255 entries
at most - the first build died on that).
Which clip fits which event is a GUESS: `EVENT_THEME` gives each event a theme (hunt, payback, down, go, win, ...), `THEMES`
lists the campaign categories for a theme, `THEME_RX` / `BAD_FOR` filter by what the clip's text says (no "help!" for a
Backstab). Excluded: clips that name a person, longer than 78 characters, ammo / syringe / eye / SWAT / vehicle talk, and the
campaign's flashback / hum / equipment-steal categories. The pick is `crc32(event) + number` over the theme's candidates (stable
across rebuilds). The whole choice, per map-independent event: `voice_review.tsv` (character, leaf, theme, campaign key, text).
Leaves with no clip in a speaker's list (Meldal and Parker have ~35) reuse the same clip under several events.

## 4. Hook (klvoice.c)
Per crew member wearing one of the eight: voice number = `rules+0x33e+record`. In every speech-manager line with the
per-character flag, the entry at that number is replaced by an entry made (as klk_entry does, 0x828fa0) for
`KLVoice/<Name>/<Event>`. DATA writes only (one heap dword each, `klh_data`). Pointers replaced are remembered and put back when
the member stops wearing the body, on a new level generation, or when no round is running (only where the pointer is still ours).
Two bodies on one voice number: nobody gets it. A level without the leaf: the line stays as it was.
Layout (all disassembled, never seen live): manager `[0x168e958]`; group g at `+g*0x18`, g < 94 (count `+4` <= 3, data `+0x10`);
25 single lines at `+0x8d0`; line `+0x20` flag 1, vector count `+8`, vector data `+0x14`; entry text `+4`.
KLHook.ini: `[Voice] Enable=0, StockLevels=0, Log=1 (2 = every swap), Period=1500`. `[Talk] StockLevels=0` (new): a level the
verdict calls stock is let through, but it still needs a KLTalk.ini beside its archive.

## 5. Pairs
`KLTalk.ini` of each map (the installed one with the Dead Men pools and every pair that touches them replaced):
- Pools per character: `Idle_1..6`, `Stage2_1..3`, `Down_1..3`, `Money_1..3` (keys `KLVoice/<Name>/..`).
- Kane <-> Lynch: thirteen exchanges only they have (campaign lines that name the other: "Lynch! Hurry!" -> "Come on! I'm
  waiting!"; "Kane, you just want us dead, don't you?" -> "That's stupid"; ammo hand-over; the eye; the car ...). `Pair_KLnn_Call` /
  `_Reply`; which answers which is a GUESS from the two texts. `KL_PAIRS` in the tool.
- Dead Men <-> Dead Men: Call -> Ans (friendly) and Arg -> Arg (an argument) for every ordered pair.
- Kane / Lynch <-> every other Dead Men character, both directions.
- Dead Men character and Kane / Lynch <-> Dog Days heisters (`Char<n>`): Dog Days side keeps its own `_C<slot+1>` recording.
Limits kept (160 pairs, 160 pools, 512 said keys); `check` runs kl_talk_chars.check_text over every staged ini.

## 6. Install / test recipe
Staged: `G:\kl_build_1023\voice_1023\` (per-map folders, `voice_1023_files.csv` with md5s, `INSTALL voice 1023.bat`,
`UNDO voice 1023.bat`, `hook\dinput8.dll` SHIP, `hook_test\dinput8.dll` TEST). INSTALL refuses while kl2.exe runs, backs up every
file as `*.before-1023voice`, md5-checks each copy, installs the hook, and sets the keys that are not yet set in KLHook.ini
(`[Voice] Enable=1 StockLevels=1 Log=2`, `[Talk] Enable=1 StockLevels=1`; backed up too). UNDO moves every backup back.
Test: Arcade, pick a Dead Men body (Wardrobe) on any map (DM01 or DD01), keep `[Wardrobe] DMVoice=1`, `[Crew] Voice=1` (bots),
`[KLHook] AllMaps=1` (bots on stock maps). KLHook.log must show: `voice: on; ...`, `talk: on; ... a stock level too if ...`,
`voice: walk 1 ...: N per-character lines, M entries replaced` with N > 0 and M > 0 (`NO per-character line found` = the layout
guess is wrong: nothing else would work, report it), `voice: line ... slot k (Name) -> KLVoice/Name/Event` (Log=2). By ear: a
Backstab / JackPot / CallEsc in the Dead Men voice. Pairs: `talk: ...` lines for `KLVoice/` keys.

## 7. Untested / open
Everything above in the game: the manager layout, whether swapping a heap pointer changes what 0x421c70 plays, the streamed
campaign clips on 27 maps, CEG with the data writes, and whether a DD copy counts as stock (StockLevels covers both).
Clips with `???` in the text are the campaign's curly apostrophes (the bytes are copied as they are).
