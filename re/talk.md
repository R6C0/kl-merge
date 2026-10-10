# Kane and Lynch talk: the countdown, the exchanges, chatter

2026-10-10, agent v-talk. **Offline only**: the game was not started, nothing was installed, nothing was
written into the Dog Days folder. Tool: `tools/kl_fa_talk.py` (new; its docstring is the short form of this
file), two checks in `tools/kl_voice.py` (`said`, `talk`). Builds on `re/bots_voice.md` (how a line gets its
voice), `re/voice.md`, `re/audio.md`, `re/crew_random.md` (who wears which body).

Words: **EXE** = read in kl2.exe at the address given; **MEASURED** = counted on this machine's files;
**ASSUMPTION** = fits the evidence, not proven; **GUESS** = a value chosen, not copied and not measured;
**LIVE** = only a run with ears can settle it.

The owner (2026-10-10): *'if theres a kane with people on retomoto can we do an easter egg from the actual
mission where he starts the countdown to the explosion then it happens, and if lynch is also in ther same
match could we get a little dialogue exchange with kane and lynch through retomoto and maybe the rest of the
maps and maybe if its possible to use the other voicelines from the game so it feels more natural / human'*.

## 0. Short answers

1. **The data is built and checks clean; nothing is heard without a hook part that is NOT written.** A level
   object cannot test 'is somebody wearing Kane' (the body is chosen at run time by `klchar.c` / `klcrew.c`),
   so the level carries the lines and a script (`KLTalk.ini` beside the archive) and a small hook part
   (`kltalk`, section 3, described for the lead) says them. A talk build WITHOUT that hook part plays exactly
   as its source build: no entity, no `.prp` / `.gms` byte, no model changes.
2. **Retomoto** (`<work>\build\v_talk\retomoto_talk`, from `rt_ai3\retomoto_ai3`): 26 campaign lines of M09
   (58.5 s) in 8 scenes. Kane's countdown is the campaign's own six clips ('You have 7sec, 6sec,' ... 'NOW!',
   'Let's get them all!'): first word 5.79 s after the round-start event (2.21 s before GO), **'NOW!' starts
   at 13.00 s = the level's own blast timer** (read from the level, not typed in). With Lynch: exchanges in
   the boardroom, at the tower car (the join), outside the entrance, on the road, in the van.
3. **M02** (`<work>\build\v_talk\M02`, from `z_maps\M02`): 12 campaign lines of M02 (20.8 s) in 3 scenes.
   Scripts for M01, M03, M06 exist in the tool (`plan`), their clips are in the stream file; not built (the
   job named two builds).
4. **Chatter** ('more natural'): 17 pools and 7 call-and-answer pairs written into `KLTalk.ini`, **all from
   lines the build's bank already holds** (Dog Days' own Kane / Lynch one-liners, the eight heisters' lines of
   the other stock levels, the two squad voices): 0 bytes anywhere. A key is said once a round.
5. **Budget** (MEASURED, `kl_fa_talk.py sizes`):

   | build | .prm | .ANM | .fxc | .WAV |
   |---|---:|---:|---:|---:|
   | `rt_ai3\retomoto_ai3` (before) | 79,269,328 | 21,642,904 | 17,760,648 | 27,158,864 |
   | `v_talk\retomoto_talk` | 79,269,328 | 21,642,904 | 17,760,648 | 27,802,960 (**+644,096**) |
   | `v_talk\retomoto_talk_adpcmstream` | same | same | same | 27,158,864 (**+0**) |
   | `z_maps\M02` (before) | 54,619,216 | 22,202,472 | 17,760,648 | 22,527,568 |
   | `v_talk\M02` | 54,619,216 | 22,202,472 | 17,760,648 | 22,690,384 (**+162,816**) |

   Why the .WAV grows at all: nearly all of Kane's Dead Men lines are **streamed IMA ADPCM** (19 of the 26 on
   Retomoto, 7 of 12 on M02). kl2.exe has a decode path for streamed ADPCM (re/voice.md 7.3) that no stock
   clip uses and nobody has heard; in-memory ADPCM is the form the Japanese guards' shouts are played in. So
   the default moves those clips into the .WAV (0.64 MB / 0.16 MB). `--adpcm stream` leaves them in the
   stream file (+0): the third build above is that variant, to be tried by ear first - if Kane is heard from
   it, use it everywhere. Lynch's lines (interleaved PCM, the form of the Retomoto theme the owner HAS heard)
   stay streamed in both. Chunk table: untouched (65,118 chunks on Retomoto, limit 69,632).
6. **A new stream file is needed**: `<work>\build\v_talk\str\PC_Def.str`, 1,690,199,891 bytes = the installed
   one (1,684,486,009) + 5,713,882; 64 blocks / 102 clips appended behind 0x644d3000 for ALL five maps'
   scripts; nothing the base holds moves. The Bain agent has already put its clips on top of it:
   `<work>\build\v_bain\over_talk\PC_Def.str` (1,694,364,711) - install ONE file, that superset, when both
   are wanted (section 6).

## 1. Inventory

`python tools/kl_fa_talk.py inventory` -> `<work>\research\v_talk\lines_dm.tsv` (3,899 keys) and
`lines_dd.tsv` (3,993 keys): speaker, key, seconds, clip form, clip name in the .WHD, the levels whose .LOC
holds the key with a sound, English text. Every stock level of both games was read (20 + 21). The speaker is
taken from the key's last part (`_Hero` / `_Kane`, `_Lynch`, `_Carlos` ..., `_C<n>`, `_Squad`): ASSUMPTION
for odd names. Form and length are the first level's.

### 1.1 Dead Men (MEASURED)

| speaker | where | lines | seconds | clip form |
|---|---|---:|---:|---|
| Kane | level dialogue (`M01/` .. `M14/`) | 565 | 1,326.7 | 530 streamed ADPCM, 4 streamed PCM, 2 Vorbis, 29 keys without a sound object |
| Kane | `AllLevels/Oneliners` | 280 | 378.8 | 275 streamed ADPCM, 5 streamed PCM |
| Kane | `AllLevels/Expressions` | 7 | 12.2 | streamed ADPCM |
| Lynch | level dialogue | 709 | 1,585.9 | 572 interleaved PCM ('pcm set'), 90 streamed ADPCM, 8 PCM, 39 without a sound object |
| Lynch | `AllLevels/Oneliners` | 743 | 2,389.3 | 658 interleaved PCM, 38 streamed ADPCM, 29 Vorbis, 18 PCM |
| Lynch | `AllLevels/Expressions` | 9 | 13.4 | 8 streamed ADPCM, 1 in memory |
| Carlos / Rific / Shelly / Thapa | dialogue + one-liners | 146 / 116 / 164 / 199 | 295 / 270 / 356 / 370 | mostly interleaved PCM |
| crew (`_Merc*`) | dialogue + one-liners + expressions | 540 | 752 | 348 interleaved PCM, 156 streamed ADPCM, 20 in memory |
| Fragile Alliance lines (one voice, no character) | `Multiplayer/` | 421 | 1,340.6 | 386 interleaved PCM, 29 PCM, 6 ADPCM |

- Per level, Kane / Lynch dialogue keys: M01 12 / 12, M02 67 / 74, M03 89 / 119, M05 69 / 149, M06 43 / 56,
  M07 39 / 26, M08 48 / 39, **M09 27 / 35 (61.8 s / 74.0 s)**, M11 46 / 30, M12 17 / 33, M13 79 / 88,
  M14 29 / 48.
- **M09 by scene** (K / L lines): `M09_Countdown` 6 / 0, `M09_Start_Rappel` 1 / 4, `M09_HangIdle` 0 / 4,
  `M09_Get_Ready_To_Rappel` 1 / 0, `M09_Room_Cleared` 1 / 0, `M09_Get_The_Briefcase` 0 / 2,
  `M09_Take_Briefcase_Give_Scar` 3 / 2, `M09_Lets_Get_To_Elevators` 1 / 0, `M09_They_Are_Everywhere` 0 / 2,
  `M09_LynchShootDead` 2 / 2, `M09_Load` 1 / 4; part B: `M09b_Start_Elevator` 1 / 0, `M09b_Lobby` 1 / 0,
  `M09b_Outside` 2 / 0, `M09b_CantGetToOverpass` 3 / 2, `M09b_OverPass` 1 / 6, `M09b_Sniper` 1 / 4,
  `M09b_WrongWay` 0 / 2, `M09b_BusTerminal` 1 / 0, `M09b_InVan` 1 / 1. M09_A's and M09_B's .LOC and bank
  hold the same 4,186 leaves, so one source level (M09_A) serves both halves.
- **The countdown**: `M09_Countdown_010_Hero` 'You have 7sec, 6sec,' 2.47 s; `_020` '5sec, 4sec,' 2.07;
  `_030` '3sec,' 0.99; `_040` '2 sec, 1sec,' 1.69; `_050` 'NOW!' 0.71; `_060` 'Let's get them all!' 1.37.
  All streamed ADPCM. The campaign plays 010..040 back to back from one mini cut scene (7.22 s), then 050.
- **Dead Men has no Fragile Alliance line of Kane's or Lynch's own** (re/bots_voice.md 0.6): the 421
  `Multiplayer/` lines are one voice each. The four FA levels' .LOC do hold 287 Kane and 752 Lynch keys with
  a sound - those are the `AllLevels/` one-liners (barks), not FA lines.
- Barks as voice SETS (`hero_default`, `little`, `little_coop`, `mercenary_01`, slots and counts):
  re/bots_voice.md section 5. Not repeated here.

### 1.2 Dog Days (MEASURED)

| speaker | where | lines | seconds | clip form |
|---|---|---:|---:|---|
| Kane | level dialogue `L01/` .. `L11/` | 568 | 1,818.9 | Vorbis, streamed |
| Kane | `AllLevels/Oneliners` (29 folders: What 9, LetsGo 10, Direction 13, Guns 7, Exclamation 11, Flank 22, Cover 18, Move 18, Panic 14, Reload 10, HumanShield 54, Stealth 34 ...) | 308 | 466.0 | Vorbis |
| Lynch | level dialogue | 634 | 2,280.8 | 630 Vorbis, 4 in memory |
| Lynch | `AllLevels/Oneliners` (What 7, LetsGo 11, Direction 21, Guns 7, Exclamation 11, LynchPsych 21, Flank 14, Cover 13, Panic 16, DownNotDead 10 ...) | 302 | 665.0 | Vorbis |
| heisters 1..8 (`_C1.._C8`) | `Multiplayer/` | 234 - 239 each | 820 - 1,229 each | Vorbis |
| Glazer (`_C9`) | `Multiplayer/` | 31 | 122.1 | Vorbis |
| squad voices (`_Squad`, `_Squad02`) | one-liners, expressions, dialogue | 193 | 395.1 | Vorbis |
| Glazer | level dialogue | 66 | 397.4 | Vorbis |

- Per level, Kane / Lynch dialogue: L01 47 / 70, L02 65 / 60, L03 60 / 91, L04 39 / 46, L05 42 / 67,
  L06 66 / 67, L07 46 / 73, L08 35 / 24, L09 37 / 28, L10 84 / 67, L11 47 / 41.
- **What an Arcade bank holds of the two** (MEASURED on F07's bank through the builds' check): the
  `AllLevels/Oneliners/` leaves of Kane, Lynch and the squad voices are in every Fragile Alliance level's .LOC
  WITH their sound objects and their clips in Dog Days' own stream file - every key of the pools below was
  looked up on both builds and found ('stream vorbis' 187 / 235 clips). The story levels' dialogue
  (`L01/` ...) is NOT in an Arcade bank; it would be a bank merge from that level, like the Dead Men lines.
- Arcade has no line of Kane's or Lynch's own either: the heisters are the eight mercenaries.

## 2. How a given character says a given line

### 2.1 What the game has (EXE)

- The settings' lines (302 fields) are bound to EVENTS, not to moments of a script, and a per-character line
  picks its recording by the table byte `rules + 0x33e + slot` (re/bots_voice.md 1.2). There is no settings
  field 'say X now'.
- `OnlineSpeakPlayer` is the one level object that says a line on a trigger. Init 0x8cb6e0: for each of its
  two keys (controller + 0x38 crew, + 0x3c police; the text starts 0xc into the string object) it allocates a
  0x204-byte entry with the game's allocator 0x89e850, first dword 0, and calls
  `0x828fa0(this = [[[0xdd2640] + 0xac] + 0x94], key, entry)` (`ret 8`; 0 = not found, the entry is freed
  through 0x6ad680); entries at + 0x40 / + 0x44. Fire 0x780550: a 0x28-byte line object from 0x89e850,
  constructed by 0x667610 (list fields, `+0x1c` = 0.0, `+0x20` flag 0, `+0x24` priority -1), `[line + 0]` =
  the entry, then **`0x421c70(this = [0x168e958], line, 0, 0, 0)`** at 0x7805f4: other line 0, speaker
  slot 0, last argument 0.
- 0x421c70 says nothing when `[manager + 0x956]` is non-zero or `[[0x168e598] + 0x15d]` is zero (0x421c8b,
  0x421ca6). A plain line (flag 0) plays its one entry whatever the speaker byte is.
- What level data alone can do: an `OnlineSpeakPlayer` on a trigger says ONE plain line in ONE recording to
  everybody, whoever is in the round. That is enough for a fixed announcement and not for 'only when Kane is
  there' or 'Lynch answers': no stock object tests a model number, and the wardrobe changes bodies after the
  level is loaded.

### 2.2 So: the line is level data, the decision is the hook's

- **Level data** (built): every script line is a sound object in the level's bank and one PLAIN leaf
  `KLTalk/<name>` in each of the eight non-stub .LOC files (text of the language where Dead Men has it, else
  English) - found by the one lookup above, played in the one recording there is (Kane's, Lynch's).
- **Who is who** comes from what the hook already knows: `klchar.c`'s choice for the human and `klcrew.c`'s
  draw for each bot (`klw_player_char()`, `klw_crew_char(record)`), against `Kane=` / `Lynch=` of
  `KLTalk.ini` (the wardrobe character numbers, 9 and 10 on both builds, read from `KLWardrobe.ini`).
  The table byte `rules + 0x33e` is NOT used for this (it is the line VOICE index, and a Dead Men body has
  none of its own: re/bots_voice.md 4).
- **Speaker argument**: the crew record index of whoever wears the character (0 for the human: ASSUMPTION,
  re/bots_voice.md 9). For a plain line it does not choose the recording; ASSUMPTION that it is only carried
  on to the queue. Whether a line sounds from the speaker's place or from nowhere (as the briefing does):
  LIVE.

## 3. The hook part `kltalk` (DESCRIBED, NOT WRITTEN - the lead's)

Policy as the other parts (klhook.c top comment): data reads, game functions only from the game's own
thread, off unless `[Talk] Enable=1` in KLHook.ini, Arcade only, the level must have a `KLTalk.ini` beside its
archive (found the way `klchar.c` finds `KLWardrobe.ini`). To be included after `klcrew.c`.

### 3.1 At level load (once, game thread)

1. Read `KLTalk.ini`. Refuse (log, stay silent) when `Version` is not 1 or when `StreamBytes` is larger than
   the size of `<game>\PC_Def.str` - a level installed without its stream file would play noise or read past
   the end.
2. Nothing else until a line is first needed. Then, per key, once: `entry = 0x89e850(0x204)`, `*entry = 0`,
   `0x828fa0(...)` as in 2.1; not found -> remember 'none' (log the key once), free nothing (ASSUMPTION: a
   leaked 0x204 block is safer than calling 0x6ad680 from outside); found -> `line = 0x89e850(0x28)`,
   `0x667610(line)`, `[line + 0] = entry`. Keep the pointer for the rest of the level. (This is byte for byte
   what 0x780550 does, kept instead of thrown away.)

### 3.2 Each tick of a round (game thread, session state 0x19, as klbot.c)

- Present: `kane` = the record index whose character is `Kane=` (human or bot, status not dead / gone), else
  none; the same for `lynch`. `Needs`: `Kane` / `Lynch` = that one is there; `Both`; `KaneOnly` / `LynchOnly`
  = there and the other not. Scenes of one `Name` are alternatives: the first whose `Needs` hold is taken,
  and the NAME is done for the round.
- `When`: `Start` = the round-start moment (3.3) + `Delay`; `Stage1/2/3` = the human's heist stage (record
  + 0x78, klbot.c) first reaches it, + `Delay`; `Aboard` = the human's status becomes 4; `Join` = kljoin.c
  has just made its jump; `Box` = the human's feet are inside `Box=x0,x1,y0,y1,z0,z1` and the round is at
  least `NotBefore` seconds old.
- A scene that has started says `Line.n = who,at,seconds,key` at start + `at`:
  `0x421c70(this = [0x168e958], line, 0, record index of who, 0)`. If its speaker died meanwhile the rest of
  the scene is dropped.
- Log one line per scene and per spoken key (`talk: scene countdown (Kane = record 2) at 5.79 s`,
  `talk: said KLTalk/M09_Countdown_050_Hero at 13.00 s`): the live checks read these.

### 3.3 The round-start moment (ASSUMPTION, to be settled by check T1)

`Blast=13.00` and every `Start` delay count from kl_fa_author's round-start EVENT, which is the moment the
8 s countdown on the HUD begins (SEEN LIVE, runs GW1 / GW2, re/retomoto_fa.md 10.3). The hook cannot see a
level event; it sees the session state. Evidence that they coincide: re/retomoto_fa.md's table times 'about
20 s after GO - 30 s after the round state begins' (GW2). So: **Start = the first tick with session state
0x19** - ASSUMPTION, accurate to the hook's tick and to that one observation. If T1 shows an offset, it is one
number: `[Talk] StartOffset=<seconds>` in KLHook.ini, added to every `Start` delay.

### 3.4 Chatter

`[Chatter]`: `Gap=40,90` (seconds between two idle lines of the whole crew, drawn anew each time),
`MemberGap=25`, `Quiet=8` (no chatter this close to a scene line), `EventChance=50`, `Once=1` (a key is said
at most once a round; a used-up pool stays silent), `Speakers=0` (the human's own character does not
chatter). All GUESSES, in the ini so they can be tuned without a build.
- `[Pool.n]`: `Who=Kane|Lynch` - plain keys, said by whoever wears him; `Who=Any` - per-character keys: the
  hook appends `_C<n>`, n = 1 + byte `[rules + 0x33e + record]` (the game's own voice rule), so a bot speaks
  in the voice it has everywhere else; `Who=Squad1|Squad2` - plain keys in the two squad voices, for a bot
  that wears a Dead Men crew body (no recording of its own exists: re/bots_voice.md 4): squad voice =
  record index parity (GUESS).
- `On=Idle` (the gap ran out), `Money` (the speaker's money rose), `Down` (another member died), `Stage2`
  (the speaker left the loot area), `Traitor` (a member was marked traitor) - all readable from the crew
  records klbot.c already logs.
- `[Pair.n]`: `Call=who,key` / `Reply=who,key`, only with both present, on an Idle turn, the reply 0.4 s
  after the call's clip (the hook does not know clip lengths of pool keys: use 2.5 s, GUESS).

## 4. 'More natural': what gates talk in the game, and what is empty

- **The 15 s group gate** (EXE, 0x58a070, constant 0xd1af98): a GROUP of the settings does not speak again
  within 15.0 s; the first time always passes. 96 groups of up to three alternatives + 25 single lines. It
  gates events, it does not create talk: nothing in a stock Fragile Alliance level speaks without an event.
- **No idle banter object** exists in stock levels (`ZSmallTalkCtrl` is in the exe, in no level:
  re/voice.md 1.4), and no heister has a voice set (no barks: re/bots_voice.md 0.4). What a waiting crew
  hears is the mission reminder (fields 136-138) and the time warnings.
- **Empty on our builds** (`kl_fa_talk.py empty`, MEASURED): Retomoto 74 of 302 line fields (102
  per-character and 126 plain filled; empty: 22-23 72-77 95 101 110-111 115-117 128-129 131-132 138 160
  165-166 174-175 182-184 200-208 211 214 220-223 230-232 252-253 255-256 282-283 285-286 288-289 295
  306-307 309-323); M02 64 of 302 (104 / 134 filled). Stock F07 has the same 74 empty, so the builds are
  not poorer than stock; 'too quiet' is the game's own design.
- **The queue**: a line said through 0x421c70 goes into the speech queue (0x578840: ten waiting lines,
  ordered by priority, re/bots_voice.md 1.1); the hook's lines carry priority -1 = first. A line does not
  interrupt one that is playing: ASSUMPTION, and the reason for check T2.
- **What the pools use** (all present in both builds' banks, every key looked up by the check):
  Kane 22 keys (idle 11, money 3, down 4, move 4), Lynch 23, the eight heisters 11 keys x 8 voices on
  Retomoto / 17 x 8 on M02 (lines of OTHER stock levels that fit any job; a key the level's own settings
  already speak is left out so it cannot repeat), the two squad voices 20 keys each, 7 pairs
  ('Lynch! Over here!' / 'On my way.' ...). Which line suits which moment: ASSUMPTION, by the texts.
- **The cap**: `Once=1` - within a round no key is said twice; idle talk is one line per 40 - 90 s for the
  whole crew. With ~45 idle-capable keys a ten-minute round cannot run a pool dry.
- NOT done here: voice SETS on the bots (barks under fire: re/bots_voice.md 6.4 / 6.5, a bank merge and a
  write of a field; another job's), Dead Men's `little` set for an AI Lynch.

## 5. The scripts (`python tools/kl_fa_talk.py plan`)

Scene = name, when, delay, who must be there; lines with start, speaker, length. Choices of line and moment
are by the texts (ASSUMPTION / GUESS); the boxes are GUESSES from kl_fa_author's coordinates. `GAP` between
two lines of an exchange 0.35 s (GUESS).

**Retomoto** (26 lines, 58.5 s; 19 ADPCM 40.4 s, 7 interleaved PCM 18.1 s):

| scene | when | needs | lines |
|---|---|---|---|
| balcony | Start + 0.6 | Lynch | L 'Fuck I hate heights. I can't believe we're going through with this.' (3.67) |
| countdown | Start + 5.79 | Kane | K 'You have 7sec, 6sec,' 0.00 / '5sec, 4sec,' 2.47 / '3sec,' 4.53 / '2 sec, 1sec,' 5.53 / **'NOW!' 7.21 = 13.00 s = the blast** / 'Let's get them all!' 8.27 |
| room | box round the boardroom table, not before 25 s | Both | L 'Come on. You're the one talking about keeping momentum and shit.' / K 'Some things just shouldn't be rushed.' / L 'What the fuck was that for?' / K 'Nothing. Let's just get down to the elevators and get the hell out of here.' |
| | | Kane only | K 'Secure the room while I get the briefcase.' |
| | | Lynch only | L 'What are you waiting for? Get the briefcase.' |
| reception | box, not before 25 s | Kane | K 'Everyone ready? Only two more floors 'til we reach the elevators.' |
| | | Lynch only | L 'Shit! They just keep comin'!' |
| car | the hook's join + 0.8 | Kane | K 'Just keep it cool...' / 'We are gonna be fine. We just need to get out to the car... we're almost there.' |
| street | box outside the entrance | Both | K 'Driver! Where the hell are you?!' / L 'What the fuck is this? We're paying you to pick us up.' / K 'Lynch, he's right. There is too much heat! We have to keep moving!' |
| | | Kane only | K 'Driver! Where the hell are you?!' |
| road | box on the carriageway | Both | L 'Shit! They just keep fucking coming!' / L 'There they are! You fuckers! Don't be so fucking QUIET!!!' / K 'Lynch! Cut it out! They're no threat.' / L 'Don't fucking patronize me!' |
| | | Lynch only | L 'Shit! They just keep fucking coming!' |
| van | aboard + 0.5 | Both | L 'So, we're good?' / K 'Very good...' |

With neither present no scene's `Needs` holds: nothing is said.

**M02** (12 lines, 20.8 s): start (GO + 1 s, Both) L 'So, what's the plan?' / K 'Just do exactly as I say.';
inside (stage 1 + 6 s, Both) the truck exchange, six lines ('I used to drive one of those.' ... 'Well
don't.'); out (stage 2 + 1 s) Both: K 'Lynch! I'm losing my patience with you. Get over here!' / L 'Ok, I'm
here! What's keeping you?'; Kane only: 'Let's get back to the car.'; Lynch only: 'Let's go to the car.'

M01 (7 lines), M03 (10), M06 (9): `plan` prints them; `build ... --map M01|M03|M06` on their `z_maps`
folders makes them (not run here beyond `plan`; their clips are in the stream file).

## 6. What was built and checked

| folder (`<work>\build\v_talk\`) | from | zip sha1 | what |
|---|---|---|---|
| `retomoto_talk` | `rt_ai3\retomoto_ai3` | da7b6891 | ADPCM lines in the .WAV (default) |
| `retomoto_talk_adpcmstream` | `rt_ai3\retomoto_ai3` | 7449c127 | ADPCM lines left streamed: .WAV unchanged |
| `M02` | `z_maps\M02` | 1f3c501b | default |
| `str\PC_Def.str` (+ `.map.json`) | `<work>\build\PC_Def.str` | 10350f2a | + 64 blocks / 102 clips, 5,713,882 bytes |

Members that differ from the source build (MEASURED, byte compare): `.SND` and the eight `.LOC` in the
archive; beside it `.WHD`, `.WAV`, `_LS.SND` (its one pointer), new `KLTalk.ini`, `talk.json`. Bank on
Retomoto: sounds 4,967 -> 4,993, waves 4,816 -> 4,842 (the largest that ran live is 4,967 / 4,816: the pool
limits are not known, re/bots_voice.md 9); M02: 4,923 sounds, 4,786 waves after.

Checks run on the two default builds (2026-10-10):

| check | Retomoto | M02 |
|---|---|---|
| `kl_fa_talk.py check` (= `kl_voice.py talk`): every scene / pool / pair key as the exe finds it, in all languages, clip length against the ini, 'NOW!' against the level's blast timer, bank clean, records inside the .WAV, streamed clips in the stream file | FAIL 0, NOTE 1 | FAIL 0, NOTE 1 |
| `kl_snd.verify` + `verify_streams` (inside `build`; it raises otherwise) | passed | passed |
| `kl_fa_talk.py stream --verify` | appended blocks: 0 problems, each equals Dead Men's bytes; 13 findings are the BASE's own, there before (12 names two games share, one block of the 2026-10-09 merge) | |
| `kl_voice.py heisters` | CRASH 0, SILENT 1 (the stock exit-heist key, same as the source build) | none |
| `kl_impact.py` | problems: 0 | problems: 0 |
| `kl_chars.py check` | 1 problem, identical output to the source build (`Weapons/BombWindow_02` shader) | 6 problems, identical output to the source build (glow30 materials) |
| `kl_fa.py check` | same findings as the source build | same |

The NOTE of the talk check on both: the PC_Def.str in the game folder is the old one (1,684,486,009 < the
1,688,413,044 / 1,688,232,640 bytes the levels need).

Not checked by anything offline: that a line is HEARD.

## 7. What the lead installs, and what needs the hook

1. **Stream file first**: `<work>\build\v_talk\str\PC_Def.str` -> `<DD>\PC_Def.str` (a superset of the
   installed file: every earlier build keeps playing). If Bain is wanted too, install
   `<work>\build\v_bain\over_talk\PC_Def.str` instead (the Bain agent's file on top of this one, 1,694,364,711
   bytes) - not `v_bain\PC_Def.str`, which lacks the talk clips. Then make the installed file the work
   folder's merged one (`<work>\build\PC_Def.str` + `.map.json`), or the next `kl_str` merge starts without
   them. A talk level with the OLD stream file: its streamed lines point behind the old data (the hook part
   refuses by `StreamBytes`; without the hook nothing plays them).
2. **The level**: the whole folder (`F01_Main.zip`, `.WHD`, `.WAV`, `_LS.SND`, the `_LS_*` files, `.hti`,
   `KLWardrobe.ini`, `KLJoin.ini` on Retomoto, **`KLTalk.ini`**) the way `kl_graft.py install` does.
   NOTE: the owner's installed Retomoto is `rt_guns3\retomoto_ai3_guns`; the job's base `rt_ai3\retomoto_ai3`
   has no gun looks. For the owner's build run the step on that folder:
   `python tools/kl_fa_talk.py build <work>\build\rt_guns3\retomoto_ai3_guns <out> --map retomoto` (not run).
   The same for a build with Bain or with the Retomoto bots: the step only appends to the bank and the .LOC,
   so it goes last or before - but `KLTalk/` must not exist yet (it refuses a second run).
3. **Hook**: part `kltalk` of section 3 - NOT WRITTEN. Until it exists the builds are silent additions.
   It needs `klchar.c` (the player's body) and, for bots as Kane / Lynch, `klcrew.c`.
4. Nothing in Patch01.zip, no menu change.

## 8. Live checks, in order (the lead; each with what proves it)

| # | set-up | proves | evidence |
|---|---|---|---|
| T0 | new PC_Def.str + the build installed NOW, no hook change | the stream file is a clean superset | `kl_autotest` RESULT clean exit; Retomoto music and guards as before |
| T1 | `retomoto_talk`, kltalk on with a test key that only LOGS, player = Kane (KLChar 9) | the round-start moment | log `talk: state 0x19 at t0`; a `kl_watch` picture series: 'Heist starts in 8' at t0 +- 1 s, the blast (glass / shake) at t0 + 13 s. An offset -> `StartOffset` |
| T2 | the same, lines on | Kane is heard, the count is back to back, 'NOW!' on the blast; does the level's briefing line push the count late | log `talk: said KLTalk/M09_Countdown_0n0_Hero at ...` six times, by ear / a recording; if the briefing collides: empty settings fields 17-20 on Retomoto (kl_voice.settings, re/bots_voice.md 6.2) |
| T3 | `retomoto_talk_adpcmstream`, same run | streamed ADPCM decodes right | Kane sounds the same as in T2 -> use `--adpcm stream` everywhere (.WAV + 0) |
| T4 | player = Lynch (KLChar 10) | Lynch's interleaved PCM lines, 'Lynch only' alternatives | log `scene balcony`, `scene room (LynchOnly)`; no countdown said |
| T5 | player = J.C., `[Crew] Random=0` | with neither present nothing is said | no `talk: scene` line in a whole round |
| T6 | player = Kane, a bot forced to Lynch (klcrew include list) | the exchanges, both speakers | `scene room (Both)` with four `said` lines; walk on: car, street, road, van - each box fires once (the boxes are GUESSES: move them in the ini) |
| T7 | chatter on, a 5-minute round | pools, the cap | no key twice in the log; gaps 40 - 90 s; a bot's `Any` line in its own voice |
| T8 | `M02` | the Stage scenes on a Dead Men map | `scene start`, `scene inside` at stage 1, `scene out` at stage 2 |
| T9 | two rounds in one session, then a second level load | the kept line objects die with the level, no stale pointer | no fault; `talk:` lines again in round 2 |

## 9. Not established

- Everything of section 3 at run time: the hook part is not written; a line through 0x421c70 from the hook
  was never made (klchar / klcrew call other routines).
- The round-start moment against session state 0x19 (one observation, 3.3).
- Whether a queued line waits for the one playing, and how a tight back-to-back series sounds (T2).
- Where a plain line sounds from, and whether the speaker byte matters for it.
- Streamed ADPCM by ear (T3); the Dead Men lines' loudness next to Dog Days' (re/voice.md: a Dead Men line
  could be too quiet rather than silent).
- The human's record index (0 assumed); sound / wave pool limits above 4,967 / 4,816.
- The boxes' places (GUESSES from kl_fa_author's numbers; never walked with this script).
- `rt_ai3\retomoto_ai3` has no AI crew (`kl_fa.py check`: 'no bot squads'); with the Retomoto bots
  (tools\kl_fa_bots_rt.py, another job) the step has to be run again on that build.
