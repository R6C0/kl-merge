# Bain (Payday 2) as the Fragile Alliance announcer

2026-10-10, agent v-bain (second pass 16:40: generic lines through the sound bank, the radio clicks, the
build over the talk stream file). **Offline only**: the game was not started, nothing was installed, nothing was
written into the Dog Days folder. Tool: `tools/kl_bain.py` (its docstring is the short form of this note).
Builds on `re/audio.md`, `re/bots_voice.md`, `re/pd2_audio.md`, `re/pd2_crates.md`.

Words: **EXE** = read in kl2.exe (by an earlier note, cited); **MEASURED** = counted on this machine's files
today; **ASSUMPTION** = fits the evidence, not proven; **LIVE** = only a run with ears can settle it.

The owner (2026-10-10): *'maybe add banes voice from payday 2 as the announcer too if you can'*.

## 0. Short answers

1. **It can be done with data only - no hook change - and it is built.** `<work>\build\v_bain\retomoto_bain`
   (from `rt_ai3\retomoto_ai3`) and `<work>\build\v_bain\retomoto_bain_guns` (from the owner's installed
   `rt_guns3\retomoto_ai3_guns`) carry 27 announcer lines in Bain's voice (26 clips); both need
   `<work>\build\v_bain\PC_Def.str`. `kl_bain.py` reports 0 problems on both, `kl_fa.check` the same single
   finding before and after. **Nobody has heard it**: every row of the mapping is chosen from subtitle texts.
2. **Dog Days has no announcer as such.** The only voice of an Arcade round that is not a heister is the
   **escape driver** (21 plain line keys, 18 of them given to Bain). The briefing, the reminders, 'grab the
   cash', 'we got it' and 'everybody escaped' are spoken by a **heister** over the radio; by content they are
   a planner's lines, so they are a second, optional group (`--set driver,brief`, the default; `--set driver`
   leaves the crew its own).
3. **Bain's lines are easy to find by meaning**: 8,841 of his streams carry their subtitle key inside the
   file, 8,710 with an English text - all PTADPCM, which `pd2_audio` decodes, 8,512 of them mono 32 kHz (Dog
   Days' own dialogue rate: nothing is resampled). His *generic* one-liners ('Van's here!', 'One minute.',
   'The police are here!') carry no key; they are found through the sound bank `regular_vox.bnk` instead
   (section 2.3): 140 more events are usable, 49 of them exactly.
4. **Budget: the four blocks do not grow.** The clips are streamed: +4.41 MB in the stream file, **+0 bytes
   in the .WAV**. The bank gains 26 sounds and 26 waves.
5. **Bain's radio.** In Payday 2 every line of his is a sequence of three sounds: a 0.154 s radio opening,
   the line, a 0.116 s closing (MEASURED in the banks, 2.4). The clips are written that way (`--radio 0`
   leaves the clicks out).
6. **TWO STREAM FILES FROM ONE BASE.** `kl_fa_talk.py` (the Kane / Lynch exchange) also appends to
   `<work>\build\PC_Def.str`, into the same place. A Bain build and a talk build made each from the base
   cannot be installed together. `<work>\build\v_bain\over_talk\` is Bain built ON the talk stream file and
   the talk build: that pair carries both (section 4, 5).

| build | .prm | .ANM | .fxc | .WAV |
|---|---:|---:|---:|---:|
| `rt_ai3\retomoto_ai3` -> `v_bain\retomoto_bain` | 79,269,328 -> 79,269,328 | 21,642,904 -> same | 17,760,648 -> same | 27,158,864 -> 27,158,864 |
| `rt_guns3\retomoto_ai3_guns` -> `v_bain\retomoto_bain_guns` | 79,879,056 -> 79,879,056 | 21,642,904 -> same | 17,760,648 -> same | 27,158,864 -> 27,158,864 |

Chunk table: untouched (no model, no .prm change).

## 1. Who speaks in a Fragile Alliance / Arcade round that is not a heister

A line is a `.LOC` key held as a string in `ZOnlineFragileAllianceSettings` (302 line fields, `kl_voice.LINES`;
EXE `re/bots_voice.md` 1). A field is **plain** (one leaf K, one recording) or **per character** (leaves
`K_C1..K_C9`, the speaker's own recording). The speaker byte that travels with a line says who it is: a
player slot, -2 the crew, **-3 the police side, -4 the driver, -5 the undercover cop, -6 Glazer** (ASSUMPTION
by the keys, `re/bots_voice.md` 1.2). Three `ZSpeaker*` objects under `FASpecials!Speakers!` carry them
(`ZSpeakerDriver` is named 'Driver' or 'Pilot').

MEASURED on `rt_ai3\retomoto_ai3` (its settings are F07's with the eight Retomoto keys of
`re/bots_voice.md` 6.2): **126 plain keys and 102 per-character keys, every one with a clip; every clip is
Ogg Vorbis, mono, about 32 kHz, streamed from `PC_Def.str`** (`.WHD` format word 0x00801000; file names
`Dialog/Multiplayer/<folder>/<key>.wav`; the wave object holds nine language records, the English one first).
No announcer line is held in memory. `python tools/kl_bain.py lines` prints the rows below from the build.

### 1.1 The driver (plain keys, speaker -4): the announcer of an Arcade round

| field | key (`Multiplayer/...`) | text | when | s |
|---|---|---|---|---:|
| 87 | Call_Esc_Response/CallEscResponse_01_R | Ah! Calm down, I'm on my way. Ayah. | a heister called the escape vehicle | 3.1 |
| 88 | ..._02_R | Easy... I'm almost there! Keep your shirt on. | same | 3.7 |
| 89 | ..._03_R | Ah! I'll be there soon. Jeez. | same | 3.3 |
| 108 | Boarding/Boarding_01_R | Get in now! | the vehicle is there, boarding opens | 1.5 |
| 109 | Boarding/Boarding_04_R | Hurry up! Hurry up! | same | 2.6 |
| 112 | Last_Esc/LastEsc_01_R | I'll be there in a second. But this is your last chance! Ah... | the last vehicle of the round | 4.6 |
| 113 | Last_Esc/LastEsc_02_R | You guys! I am nearly there! Better be ready or I'll leave you behind. ... | same | 7.3 |
| 114 | Last_Esc/LastEsc_03_R | You got 2 seconds! I ain't hanging around and I'm not coming back ... | same | 4.7 |
| 161 | One_Min_Left/OneMinLeft_03_R | Hurry up, we only got one minute left... C'mon! | round clock | 4.3 |
| 162 | Two_Min_left/TwoMinleft_02_R | Ah! At 2 more minute we got to leave! Now! | round clock | 3.4 |
| 163 | Three_Min_left/ThreeMinleft_03_R | Argh! Time is short! Only 3 minutes left! Let's go! Argh! | round clock | 3.9 |
| 173 | HoldEscapeVehicle | Hold on - wait for the others! | a heister inside asks him to wait | 3.1 |
| 185 | Boarding_End/BoardingEnd_03_R | Fuck! I'm leaving! | boarding time is up (heard outside) | 2.6 |
| 186 | Boarding_End/BoardingEnd_04_R | Too slow! Find another ride! | same | 2.8 |
| 187 | Boarding_End/BoardingEnd_06_R | C'mon eh, turtles! I'm getting out now! | same | 4.3 |
| 188-190 | Boarding_End_Inside/BoardingEndInside_03 / 04 / 06 | (the same three, for those inside) | same | 2.6-4.3 |
| 194 | Driver_Bribe_Accept/DriverBribeAccept_01 | Sure! I love easy money! Hahaha... | a heister bribed him | 3.1 |
| 195 | ..._02 | Haha! Fuck yeah! I'm with you! Pedal to the metal. | same | 3.4 |
| 196 | ..._03 | I'm down ...! Let's get the hell out of here. | same | 3.9 |

Which of these fire for whom ('heard outside' / 'inside', the time warnings as the driver's) is from the
field names and `re/bots_voice.md` 1.4, not traced call by call.

### 1.2 Radio lines a heister speaks that are a planner's by content (per character)

| field | key | text (heister 1) | when |
|---|---|---|---|
| 17 | F05/MissionBriefing_03_R | Keep it down. Get in and get the cash at any price. Understood? | briefing, first round |
| 18 | F01/MissionBriefing_03_R | Once the bomb is detonated, get in there quick, grab what you can and get out before the cops arrive. | briefing |
| 19 | F05/MissionBriefing_02_R | Move in quietly. The fuckers wont know what hit 'em. | briefing |
| 20 | F05/MissionBriefing_01_R | Keep it down and take 'em by surprise. | briefing |
| 127 | F06/ReachlootArea_01_R | Alright! Grab the cash. | first heister reaches the loot |
| 130 | F04/ExitLootArea_01_R | We got it! Let's keep moving! | leaving the loot area |
| 136 | F06/MissionReminder_01_R | Just get the money. | reminder |
| 137 | F09/MissionReminder_02_R | We can do this. Be quick 'cause this is gonna turn nasty! | reminder |
| 167 | Time_Out/TimeOut_01_R | NO! You arseholes! That was our last chance to get the fuck out of here! | the clock ran out |
| 169 | All_Esc/AllEsc_03_R | Yeah! That was great! We kept focus and now we're rich! | everybody escaped |

The other per-character lines are the crew's drama and stay the crew's: backstab 27-29, reply 30-35,
revenge 36-59, alliance reminder 63-65, shoot off money 66-71, call the vehicle 78-83, shoot at it 90-92 /
96-98 / 102-104, cash majority 118-120, jackpot 124-126, you escaped 143-148, level bounds 149-151, left
behind 176-178, driver bribe 191-193, driver traitor 197-199.

### 1.3 The police side (plain keys, speaker -3) - a commander's voice, heard by dead heisters who play cops

Not heard by a heister. Listed for completeness; none is given to Bain.

| fields | key folder | text of the first |
|---|---|---|
| 21 | F07/PoliceBriefing_01_R | Retrieve the data! It's blind robbery and it's your civil duty to protect. ... |
| 60-62 | Police_Reward | Nice shooting officer, a reward is coming up. |
| 84-86 | Call_Esc_Police | Argh! Don't let those assholes get away! Go! |
| 93-94 | Shoot_Esc_Police | Blow up their car! And kill them all! |
| 99-100 | Esc_Heavely_Damaged_Police | Huh... We almost got the bastard! Arrghnn! |
| 105-107 | Esc_Destroyed_Police | Nice job. Now search the area! |
| 133-135 | Police_Kill_Police | Take him down! He's gone rogue! |
| 139-142 | One_Criminal_Left, Two_Criminals_left | Alright. Only one of them left. Don't let him get away! |
| 152-154 | Level_BoundsPolice | Where the hell are you going, officer? |
| 164, 168 | One_Min_Left_Police, Time_Out_Police | Ahh! Just 1 more minute and we got 'em. |
| 170-172 | All_Escaped_Police, All_Dead, Criminal_Esc | Argh! Shit! They were fucking pros! / Fucking amateurs. ... / Another one got away! |
| 179-181 | Esc_And_Player_Dead_Police | ... Nice job! But keep your eyes peeled, they might have back up... |

Also plain, another mode's: undercover cop 24-26, 209-229, 305-312 (speaker -5 / -3 / -6), team mode 236-304
(Glazer's `_R_C9` recordings for the crew side, the commander for the police side), personal revenge 39-41 /
51-53, dirty money 121-123 (a heister's chuckle). **Glazer (-6)** speaks the backstab announcement when no
third heister is left (`K_C9`, 9 keys have one on Retomoto). The exit-heist line (`OnlineSpeakPlayer`) is
silent in stock (`re/bots_voice.md` 6.3). `.LOC` leaves under `Multiplayer/` that no settings field names
were not surveyed.

**No line of Dog Days tells the crew that the police arrive, and none that a heister is down** (the latter
exists for team mode only: `Team_Dead_Criminal`, 233-235). Bain has plenty for both (section 3.3); giving
them an event needs a trigger that does not exist yet.

## 2. Bain in Payday 2's files (MEASURED, `python tools/kl_bain.py find <text>`)

### 2.1 Where the lines are

- Dialogue lists: `gamedata/dialogs/*.dialog` (text XML behind a binary head; 7,641 sound events in all).
  Bain is the events `Play_pln_*` ('planner') and `Play_ban_*`; the lists `narrator` and `planner_generic`
  hold his generic lines, the `<contact>_<heist>_stage<n>` lists his per-heist ones.
- Subtitles: `strings/subtitles.strings` (Diesel string table, 24,209 entries, `pd2_audio._strings_table`).
  The key of a line is `hash64('<event without play_>_<nn>')`, e.g. `pln_esc_arrival_van`,
  `pln_fj1_06_01`: 5,389 of the 7,641 events have at least one text, 16,010 texts.
- Audio: Wwise `.wem` files under `soundbanks/streamed/<bank>/<id>` (crate extension `stream`). **A voice
  stream carries its subtitle keys as RIFF cue labels**: chunk `cue ` = u32 n + n x {u32 id, u32 sample
  position, 'data', 3 x u32}, chunk `LIST` 'adtl' with `labl` {u32 cue id, text\0}. 18,608 of the 74,437
  streams have labels, 19,004 distinct; a stream with two cues is two subtitle lines in one clip.
  **8,841 labels are Bain's** (8,837 `pln_*`, 4 `ban_*`), 8,710 with an English text. That is the join:
  label -> stream (exact, read from the file) -> text.
- Banks his labelled lines sit in: the heist banks (`job_g_kenaz` 397, `job_b_dah_stage1` 391,
  `job_crojob_stage_2` 354, `job_b_csbank` 306 ...), `briefings` 152, `regular_vox` 47 (the escape set
  `pln_esc_*`: 'The van leaves in one minute', 'Alright the van is there. Move!').
- Sound banks: `soundbanks/*.bnk` (496; Wwise BKHD version 145 but `core`). `kl_bain.pd2_events` reads
  their HIRC section: event (id = FNV-1 of the lower-case `play_...` name) -> play action -> container ->
  sounds -> **source id = the stream's name** under `soundbanks/streamed/<bank>/`. Record layouts in the
  function's docstring. 3,380 of Bain's 3,553 event names of the dialogue lists resolve to streams.

### 2.2 Format

All 8,841 are Wwise **PTADPCM** (format tag 0x8311, 36 bytes = 64 samples per channel and block):
8,512 mono 32,000 Hz, 200 stereo 32,000 Hz (briefing intros), 129 at 44,100 Hz. `pd2_audio.Stream.decode`
decodes them (decoder verified in `re/pd2_audio.md`). The 26 clips used here are all mono 32,000 Hz, 0.8 -
4.9 s. Loudness: louder than Dog Days' lines - RMS 7,050 - 12,776 of 32,767 on five decoded, against 2,466 /
4,348 / 5,335 on three Dog Days lines (decoded through ffmpeg): hence the gain step (section 4).

### 2.3 The generic lines: no label, found through the bank (MEASURED, `python tools/kl_bain.py events`)

No streamed file has a `pln_gen_*` or `ban_b*` / `ban_q*` label, although `subtitles.strings` has their
texts. They are unlabelled streams of `regular_vox`, named by the bank's event table:

| Bain's events in the banks | count |
|---|---:|
| with labelled streams (2.1) | 3,077 |
| unlabelled, every line stream PTADPCM mono 32 kHz: **usable** | 140 |
| unlabelled, Wwise Vorbis (tag 0xffff; 48 / 44.1 kHz, some stereo) or no stream: not decoded here | 163 |

- Of the 140, **49 have one line stream**: text = subtitle `<event>_01`, exact. Among them 'Thirty
  seconds!' (`pln_gen_bfr_02`), 'One minute.' (`_03`), 'Two minutes.' (`_04`), 'I'm sending the loot van.'
  (`_05`), 'It's getting pretty unpleasant out there. You guys sure you wanna stick around?' (`_07`), 'That
  was close. Good job.' (`_13`), 'That's all of them, let's get out of here!' (`pln_gen_count_09`), 'Think
  we're about to be outgunned!' (`pln_gen_pol_03`), the counts 'That's one.' .. 'That's eight.'.
- The other 91 have several line streams and as many texts, e.g. `pln_gen_pol_01` (15: 'The police are here!
  Stand 'em down.', 'Here come the cops!' ...), `pln_gen_urg_01` (13: 'Go go go!' ...), `pln_vih_01` (6:
  'Escape's here! Saying again, escape's here!' ...), `pln_gen_bfr_01` (3: 'Van's here! ...'). The EVENT is
  exact, **which stream speaks which text is not**: on the labelled events with two or more lines the
  playlist order is the subtitle number in 3,702 of 4,980 (74 %). The tool takes `<event>_<nn>` as the nn-th
  playlist entry and marks it `~` (ASSUMPTION); `TABLE` uses none of them. One listen per event would settle
  each (`kl_bain.py wav pln_gen_pol_01_01 x.wav`).
- The 163 others are the older `ban_*` set (Payday: The Heist's recordings) and need a Wwise Vorbis decoder
  (codebook-stripped Vorbis; neither `pd2_audio` nor ffmpeg reads it).
- No subtitle text: 131 of his labels. Other languages: Payday 2 has subtitles in 14, one recording.

### 2.4 The radio clicks (MEASURED)

Every event of Bain is a sequence container of three sounds: `regular_vox/111416` (4,928 samples, 0.154 s),
the line (or a random container of line variants), `regular_vox/229541` (3,712 samples, 0.116 s). Both
clicks are mono 32 kHz PTADPCM. 3,220 of his 3,380 events hold both, 3,200 as first and last sound of the
playlist; outside `pln_*` / `ban_*` 12 events of other speakers do (a scan of all 7,378 dialogue events). That is what makes him
sound like a voice in the ear in Payday 2; a clip here is click + line + click, the clicks at the line's
gain (ASSUMPTION: the container's volume fields were not read).

## 3. The mapping (ASSUMPTION throughout: by the two texts; `kl_bain.TABLE`)

### 3.1 Group `driver`

| field | Dog Days line | Bain label | Bain's line | s |
|---|---|---|---|---:|
| 87 | Ah! Calm down, I'm on my way. Ayah. | pln_esc_fixed_van | Alright, guys! A van is coming in to get you out! | 2.2 |
| 88 | Easy... I'm almost there! Keep your shirt on. | pln_gen_bfr_05_01 (by the bank, exact) | I'm sending the loot van. | 1.1 |
| 89 | Ah! I'll be there soon. Jeez. | pln_fost_en_03_03 | You got enough. I'll get our man on the way. | 2.2 |
| 108 | Get in now! | pln_esc_arrival_van | Alright the van is there. Move! | 1.6 |
| 109 | Hurry up! Hurry up! | pln_cr2_90_02 | Van's ready and waiting, gang. Move it! | 1.9 |
| 112 | I'll be there in a second. But this is your last chance! | pln_branchbank_stage1_30_any_01 | Getting pretty unpleasant out there. You guys sure you wanna stick around? | 3.2 |
| 113 | ... Better be ready or I'll leave you behind. ... | pln_ko1_17_02 | I'm shutting this down. Make sure you're with the driver when he bails, or it's a long walk home. | 4.9 |
| 114 | You got 2 seconds! I ain't hanging around ... | pln_ko1_17_01 | The driver's gonna bail! Make sure you're with him. | 2.0 |
| 161 | Hurry up, we only got one minute left... C'mon! | pln_esc_01_to_departure_van | The van leaves in one minute. Wrap it up! | 2.1 |
| 162 | Ah! At 2 more minute we got to leave! Now! | pln_esc_02_to_departure | The escape vehicle is leaving in two minutes, with or without you. | 3.0 |
| 163 | Argh! Time is short! Only 3 minutes left! ... | pln_esc_03_to_departure | Secure as much loot as you can. The escape vehicle is leaving in three minutes. | 3.9 |
| 173 | Hold on - wait for the others! | pln_pt2_17_03 | Hold it, hold it - wait til everyone's in the car. | 2.4 |
| 185 | Fuck! I'm leaving! | pln_fj1_06_01 | The van had to leave. He'll be back soon at another location. | 3.0 |
| 186 | Too slow! Find another ride! | pln_fj1_06_02 | The van had to leave. He'll be back, keep your eyes out for the new location. | 3.3 |
| 187 | C'mon eh, turtles! I'm getting out now! | pln_fj1_06_01 | (as 185) | 3.0 |
| 188 | (inside) Fuck! I'm leaving! | pln_dah_109_08 | Job is over guys. Time to go. | 1.9 |
| 189 | (inside) Too slow! Find another ride! | pln_dah_55_01 | OK, that's it. Time to go. | 1.7 |
| 190 | (inside) C'mon eh! I'm getting out now! | pln_chw_14_02 | Time to go! Come on! | 1.2 |

Seconds are the line's; a clip is 0.27 s longer with the radio clicks.
Weak rows: 88 ('loot van': in Payday 2 that is not the escape; before the second pass this row was 'Great
job! I'm sending the van, keep looting!', `pln_at1_gen_11_01`), 89 ('You got enough'), 112 (a question where
the driver gives an ultimatum; it replaced `pln_cs1_102_02`, whose 'They've really opened the valve' is a
bank's vault talk), 185 - 187 ('He'll be back' is wrong after the LAST vehicle; the game has one line group
for every vehicle). 161 - 163 assume the clock the driver warns about is the escape's.

### 3.2 Group `brief`

| field | Dog Days line (heister 1) | Bain label | Bain's line | s |
|---|---|---|---|---:|
| 17 | Keep it down. Get in and get the cash at any price. Understood? | pln_flt_07_03 | It's time. Put on the masks and let's do this. | 3.0 |
| 18 | Once the bomb is detonated, get in there quick ... | pln_fwb_26_01 | Come on, crew. Get in there, grab that loot. | 2.6 |
| 19 | Move in quietly. The fuckers wont know what hit 'em. | pln_fost_brf_04_02 | OK let's do this one. | 1.3 |
| 20 | Keep it down and take 'em by surprise. | pln_framing_stage2_13_any_03 | Get the money and clear out ASAP! | 2.1 |
| 127 | Alright! Grab the cash. | pln_ed3_13_01 | Come on, guys - time to grab the cash. | 2.0 |
| 130 | We got it! Let's keep moving! | pln_dah_53_01 | Great, that's everything, now get out of there! | 2.5 |
| 136 | Just get the money. | pln_fwb_54_01 | Come on, we're almost done. Get the money! | 2.0 |
| 137 | We can do this. Be quick 'cause this is gonna turn nasty! | pln_ch1_24_02 | Cops are on the way. Time is important, so hustle! | 2.7 |
| 169 | Yeah! That was great! We kept focus and now we're rich! | pln_at1_end_02_02 | Well done gentlemen! Some hard-earned cash! | 2.3 |

For these the nine leaves `K_C1..K_C9` all name the one Bain clip: whoever the game picks as speaker, Bain
is heard. Price: the crew no longer speaks these lines itself.

### 3.3 Where nothing fits, and Bain lines that have no Dog Days event

| Dog Days event | why not |
|---|---|
| 194-196 driver takes the bribe ('Sure! I love easy money!') | Bain has no line of being bought; the stock driver keeps them. With `driver` on, the van's voice is Bain's except here - LIVE whether that jars; an empty field would silence the event instead. |
| 167 the clock ran out ('That was our last chance ...') | no failure line that is not about a named heist; kept. |
| backstab / traitor / revenge / alliance reminder | Payday 2 has no traitors; the nearest is 'Stick together, team.' (`pln_hlp_34_03`), one clip for a three-line group. Kept as the crew's. |
| police commander, undercover cop, team mode, Glazer | other speakers; not an announcer for the crew. |

| Bain has (examples, all mono 32 kHz with text) | Dog Days event |
|---|---|
| police arriving, generic (2.3): `pln_gen_pol_01` 15 variants ('The police are here! Stand 'em down.'), `pln_gen_pol_03` 'Think we're about to be outgunned!' (exact), `pln_polin_01..04` 'Police are closing in. They are here in 20 / 30 / 40 / 60 seconds.' | none - the same missing trigger |
| hurry: `pln_gen_urg_01` 13 variants ('Go go go!'), `pln_gen_bfr_10` 'Clock's ticking, people!' | 109 could take one once a variant has been listened to |
| police arriving: `pln_at1_gen_01_01` 'Cops on the way! Let's go!', `pln_branchbank_stage1_19_any_01` 'More cops on the way.', `pln_cr2_104_02` 'This is it, gang. They're throwing everything they have in to this. Get out of there!' | none: an `OnlineSpeakTrigger` on the police squads' spawn (Retomoto's street layer) could play one - authoring, not done |
| the van called / arriving with a time: `pln_esc_30secs_to_arrival_van`, `pln_esc_01_to_arrival_van` | no event with a known time to arrival |
| 30 / 10 seconds to departure: `pln_esc_30secs_to_departure_van` '30 seconds left. Get in the van or you'll be left behind.', `pln_esc_10secs_to_departure` | none (Dog Days warns at 3 / 2 / 1 minutes only) |
| praise: `pln_bb1_58_02` 'That's it! Great job, gang.', `pln_at1_end_01_02` 'Great job gentlemen!' | only 169 |
| someone down / in custody | not searched: no Arcade event to put it on |

## 4. What `kl_bain.py build` writes, and why in these formats

What the game is known to take (`re/audio.md` 3, `tools/kl_str.py` docstring; EXE where cited there):

- **In memory** (`.WAV`): IMA ADPCM, block 0x400 (19,136 of Dog Days' 19,372 in-memory records) or 16-bit
  PCM (236). Costs address space - the block the owner's crashes were about.
- **Streamed** (`PC_Def.str`, codec in the level's `.WHD` record): Ogg Vorbis (333,908 of 334,062 stock
  records), **16-bit PCM single** (2 stock level records; Dog Days' own stream file holds 42 PCM clips,
  `re/audio.md` 3; the merged file 86 single mono 32 kHz ones, Dead Men's included) and PCM / Vorbis interleaved sets. No streamed ADPCM in stock. PTADPCM: nothing in Glacier plays it.
- So: **streamed, 16-bit PCM, mono, 32,000 Hz, one block per clip, no LIP block** - the one form that needs
  no encoder, costs no address space and has stock precedent. (ffmpeg is on this machine and could write
  Ogg Vorbis, the form of the lines replaced; not done: the `.WHD` fields of a Vorbis record - a 'rate' of
  31,7xx - 31,9xx - are not understood well enough to forge one.)

Steps (all on a copy; the source build is not changed):

1. **Clips.** Each chosen stream is decoded and scaled so that its RMS equals that of the first Dog Days
   line it replaces (measured through ffmpeg from the stock Ogg clip; never amplified, never below 0.2;
   `TARGET_RMS` 4000 when ffmpeg is missing - ASSUMPTION). Gains in this build: 0.23 - 1.00. With `--radio 1`
   (default) the two clicks of 2.4 are put before and behind the line, at the line's gain.
2. **Stream file** (`stream_add`; `kl_str` has no entry for an outside clip, so it is done here with
   `kl_str`'s reader and record writer): the base's bytes up to its tables (0x644d3000) are copied
   unchanged, the 26 clips follow on multiples of 0x100, then one fresh format table, name table and sorted
   index. Names `Dialog/kl_merge/Bain/<label>.wav`. 1,684,486,009 -> **1,688,896,606 bytes** (+4.21 MB;
   4,405,376 bytes of audio). The base's `.map.json` is copied beside it (no Dead Men block moved);
   `PC_Def.str.bain.json` lists the new clips. A second run finds the clips there and keeps the file.
3. **Bank** (`bank_add`): per clip one sound - a copy of the 0x34 bytes of the sound it replaces (cone,
   flags, the same parameter list: mixer group `dialog`, parameter types 0x1f and 0x21), new name
   `audio:dialog/kl_merge/bain/<label>#sound` - and one wave of one streamed record `{4, cd fill, file
   name*, u16 1, 0, .WHD offset, f32 seconds, 0}`, the form `kl_snd.merge` writes for Dead Men's single PCM
   stream lines. Type tables, parameter tables (one entry per use) and trailer are rewritten as
   `kl_snd.merge` does; every byte below the first type table keeps its place; `_LS.SND` gets the new
   trailer offset. `.WHD`: 26 records `fmt 0x00800001, 32000, 16 bits, block 2, lip 0`, offset = the clip's.
4. **`.LOC`** (`repoint`): in the eight real language files the leaf of each plain key, and the leaves
   `K_C1..K_C9` of each per-character key, get Bain's English text and the new sound id (90 leaves for both
   groups, 18 for `driver`). The settings, the `.prp` and all other members are byte for byte the source's.

MEASURED on the result (`check`, run by `build`): the bank walks clean and passes `kl_snd.verify`; sounds
4,967 -> 4,993, waves 4,816 -> 4,842; `.SND` 2,514,560 -> 2,520,384, `.WHD` 2,114,304 -> 2,117,712; all
21,227 streamed records of the `.WHD` are blocks of the new stream file, 0 missing; each of the 26 Bain
sounds resolves to a PCM clip of exactly its record's offset, size, rate and channels, and is named by a
leaf in 8 of 8 `.LOC` files; each `.LOC` rebuilds to itself; `kl_voice.heisters`: plain keys 108 Vorbis + 18
PCM, per-character pairs 744 Vorbis + 72 PCM, 0 CRASH, the one SILENT it had (the stock exit-heist line);
`kl_fa.check` 1 finding before and after. Stream file: every byte accounted for (`kl_str.Stream.account`, 0
problems), bytes 0x38 .. 0x644d3000 sha1-equal to the base, all 10,071 base clips in the index as they were.

Kept builds (work folder, nothing installed):

| folder | from | groups | archive sha1 |
|---|---|---|---|
| `build\v_bain\retomoto_bain` | `rt_ai3\retomoto_ai3` | driver, brief | cb6cd7d6 |
| `build\v_bain\retomoto_bain_guns` | `rt_guns3\retomoto_ai3_guns` | driver, brief | bcf31965 |
| `build\v_bain\retomoto_bain_driver` | `rt_ai3\retomoto_ai3` | driver | 2dad2a6d |
| `build\v_bain\PC_Def.str` (+ `.map.json`, `.bain.json`) | `build\PC_Def.str` | all 26 clips | 319c32cf |
| `build\v_bain\over_talk\retomoto_talk_bain` | `v_talk\retomoto_talk` (Kane / Lynch exchange, `KLTalk.ini`) | driver, brief | 43b65811 |
| `build\v_bain\over_talk\PC_Def.str` (1,694,610,488 bytes) | `v_talk\str\PC_Def.str` (1,690,199,891) | talk clips + 26 Bain clips | b0cb8bcd |

All five were rebuilt in the second pass (radio clicks on, the two new rows); 0 problems each, `kl_fa.check`
the same finding before and after. The three under `v_bain\` need `v_bain\PC_Def.str`; `over_talk`'s build
needs `over_talk\PC_Def.str`, which also serves every other build here EXCEPT the three above (their Bain
records point where `over_talk`'s file holds talk clips). On `over_talk`: bank 4,993 -> 5,019 sounds, 4,842 ->
4,868 waves; `.WAV` 27,802,960 -> 27,802,960 (the +0.64 MB against `rt_ai3` is the talk tool's, not Bain's).

Each folder has `bain.json` (the mapping with both texts, gains, offsets) and `bain.txt` (the log).
Two decoded lines to listen to outside the game, with the clicks: `<work>\pd2\audio\bain\pln_esc_arrival_van.wav`
and `pln_gen_bfr_05_01.wav` (`python tools/kl_bain.py wav <label> <out.wav> [--radio 0]` writes any other).

## 5. What the lead has to install (described, not done)

**First decide which stream file.** Bain alone: steps 1 - 3 with `v_bain\PC_Def.str`. Bain together with the
Kane / Lynch exchange of `kl_fa_talk.py`: the same steps with `v_bain\over_talk\PC_Def.str` and
`over_talk\retomoto_talk_bain` (it has no gun looks: for those, run `kl_guns` / `kl_bain` on the wanted
build with `--stream <work>\build\v_talk\str\PC_Def.str` and a new `<dst>` folder under `over_talk\`).
Whatever is chosen, later tools must append to THAT file: a build made against another descendant of the
base points into the wrong clips (heard as the wrong line or noise, not a crash - ASSUMPTION).

1. **`<work>\build\v_bain\PC_Def.str` -> `<DD>\PC_Def.str`.** This REPLACES the owner's extended stream file
   (1,684,486,009 bytes, the 2026-10-09 17:19 merge; the installed file equals `<work>\build\PC_Def.str` in
   size and in four sampled megabytes) by a superset of it: nothing an earlier build names moves, so every
   build made so far plays with the new file. Keep the old one in the work folder (it is
   `<work>\build\PC_Def.str` already). `KL_PortBackup`'s original is not involved.
   **The Bain build must never run with the old stream file**: its 26 records point behind the old file's
   data, into its tables (noise, or a read past the end).
2. If Bain is kept: make the new file the work folder's merged one too (`<work>\build\PC_Def.str` and
   `.map.json`, keeping `.bain.json` beside it), else the next `kl_str.py build --extend` starts from a
   file without the clips and a Bain build would point into nothing again. `kl_str`'s extend merge cuts
   behind the last data block, which is then a Bain clip: fine.
3. **The build**: `v_bain\retomoto_bain_guns` (it has the owner's `KLGuns.ini`, `KLJoin.ini`,
   `KLWardrobe.ini`) into the F01 slot the usual way. No hook change, no ini key, no overlay.
4. For another build: `python tools/kl_bain.py build <build dir> <new dir> [--set driver]` - 60 s, the
   stream file is found and kept. On the four Dead Men maps the rows whose field holds a Dead Men key work
   the same (the leaves of whatever key the field names are re-pointed); not run there.

## 6. Live checks, in order (ears; nothing below has been tried)

| # | do | proves | evidence |
|---|---|---|---|
| B0 | new `PC_Def.str` + the build that is installed NOW | the stream file is a clean superset | `kl_autotest` RESULT clean exit; in a round the Retomoto music and the guards sound as before |
| B1 | + `retomoto_bain_guns` in the slot, load | 4,993 sounds / 4,842 waves fit the pools; the bank is accepted | `KLHook.log` 'level loaded', RESULT not a crash (a crash in the sound set-up near kl2 0x4465f0 / 0x44668b = the record form, see `kl_whd.Writer.add_group`'s note) |
| B2 | start an Arcade round | a single streamed PCM clip plays as a line | Bain at the briefing: one of 'It's time. Put on the masks and let's do this.' / 'Come on, crew. Get in there, grab that loot.' / 'OK let's do this one.' / 'Get the money and clear out ASAP!'; the subtitle shows the same words |
| B3 | reach the boardroom loot, then leave it | per-character keys all give Bain | 'Come on, guys - time to grab the cash.'; 'Great, that's everything, now get out of there!' |
| B4 | call the van, wait for it | the driver's lines | 'Alright, guys! A van is coming in to get you out!' (or the two others); at the van 'Alright the van is there. Move!' - listen for WHERE it comes from: if the driver's lines are placed at the van, Bain is quiet from afar |
| B5 | let the clock run | time warnings | 'The escape vehicle is leaving in three minutes.' ... 'The van leaves in one minute. Wrap it up!' - and whether the times are true |
| B6 | stay out when boarding ends | boarding end | 'The van had to leave. He'll be back soon at another location.' |
| B7 | escape with everybody | the end line | 'Well done gentlemen! Some hard-earned cash!' |
| B8 | throughout | loudness and tone | Bain against the crew's lines and the gunfire: too quiet -> raise `TARGET_RMS` / drop the gain step; each line opens and closes with a short radio click (2.4): too much -> rebuild with `--radio 0`. The voice itself is clean studio sound: does it sit with Dog Days' `_R` radio lines? |

If B2 is **silent** (the level loads, the subtitle shows, no voice): the stream player does not take this
record form. Fallback, not built: the same clips as IMA ADPCM **in memory** - the form of 643 of F07's 729
in-memory records and of the guards' shouts. Cost: 2,079,616 samples at 4 bits = **about 1.04 MB more in
the `.WAV`** (27.16 -> 28.2 MB), and an IMA encoder (`kl_audio` has only the decoder). If it is **noise**:
the stream file in the game folder is the old one (step 5.1).

## 7. Not established

- Everything in section 6. In particular that a streamed single PCM record without a lip-sync word plays
  as dialogue (the 8 records of that shape in the Retomoto builds are Dead Men's Japanese police lines,
  with a lip word; nobody has reported hearing exactly those), and the sound / wave pool sizes.
- Whether the engine uses the wave object's length (`+0x18`, written = samples / rate) or the record's.
- Where a driver line is heard from (the `ZSpeakerDriver` object or the listener).
- Which `K_C<n>` a briefing takes in Arcade does not matter here (all nine name the clip); that the
  briefing plays at all on Retomoto is `re/bots_voice.md` 8.1, still open.
- Which text each stream of a many-variant generic event speaks (2.3; 74 % by playlist order); the 163
  Wwise Vorbis events; the 200 stereo and 129 44.1 kHz labelled lines are refused by the tool (nothing
  here mixes down or resamples). The clicks' volume relative to the line in Payday 2 (2.4).
- What the engine does with two builds' records in one stream file region (section 5): not tried, avoid.
- The other languages: Bain's English text is written into all eight `.LOC` files.
- The mapping itself (section 3) is a reading of two lists of subtitles.
