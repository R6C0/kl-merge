# The heisters' voices: the player's character and the AI heisters

2026-10-10, agent b-voice. **Offline only**: the game was not started, nothing was installed, nothing
was written into the Dog Days folder, no build was changed. Builds on `re/voice.md` (m-voice, q-repeat),
`re/audio.md`, `re/characters.md`, `re/wardrobe.md`. New code: one check, `kl_voice.heisters`
(`python tools/kl_voice.py heisters <level|zip> [merged|dd]`).

Words: **EXE** = read in kl2.exe at the address given; **MEASURED** = counted on this machine's files;
**ASSUMPTION** = fits the evidence, not proven; **LIVE** = only a run with ears can settle it.

The owner (2026-10-10): *'make sure the voicelines for the characters are there too and the ai have
better interactions ... backstab you and also pay the driver and leave without you or blow the van up
or help you up'*.

## 0. Short answers

1. **The lines are there, on all five builds, and every one is reachable.** 102 - 104 per-character
   line keys and 126 - 134 plain ones per build, each with a clip; every streamed clip is a clip of
   the stream file that is installed (`<DD>\PC_Def.str`, 1,684,486,009 bytes). 0 keys without a clip.
   Table: section 3.
2. **Lines exist for four of the owner's five wishes, with eight recorded voices each, on every
   build**: backstab (`Backstab`, `Backstab_Reply`, `Revenge`), pay the driver (`Driver_Bribe`,
   `Driver_Bribe_Accept`, `Driver_Traitor`), leave without you (`Esc_And_Player_Dead`,
   `HoldEscapeVehicle`, `Boarding_End`), blow the van up (`Shoot_Esc`, `Esc_Heavely_Damaged`,
   `Esc_Destroyed`). **'Help you up' has no Fragile Alliance line in either game** (no revive key in
   the 2,328 `Multiplayer/` leaves; the only such speech is the story's `AllLevels/Oneliners/
   DownNotDead` and the `die_helper` slots of the story voice sets). The lines play when the game
   rules fire the event - so they need the behaviour (the bots' job), not more sound.
3. **Which voice says a line** (EXE, section 1): entry `K_C<n>` with n - 1 = the byte at
   `rules + 0x33e + player slot`. An AI heister's byte is the digit in its group name
   (`Glazer_Bodyguard_0N` -> N - 1); the human's is 0 until the game's own body swap exchanges it
   with the AI's whose body he takes. **An AI heister whose group name has no digit 1..9 at index
   18 is an int3 at 0x51ab2d the first time it speaks** - a constraint for the bot graft (section 7).
4. **Barks: none, as stock.** No heister, AI heister or police player has a voice set in any stock
   Fragile Alliance level or in any of the five builds. Dog Days gives its *story* allies a voice
   (`squad` + `squad_02` on Glazer's crew, L02 / L03; `kane_default`, `lynch_default` on the two
   players). Those are the sets to put on the AI heisters and on Kane / Lynch (section 5, 6).
5. **A Dead Men body (Kane, Lynch, the six crew) says today exactly what the Dog Days heister of its
   slot says** - no bark, and the settings' lines in a Dog Days merc's voice (ASSUMPTION which of
   the eight: the table byte is not moved by the hook's swap, section 4). On the four Dead Men maps
   74 - 78 of the per-character lines are Dead Men's own recording, one voice whoever speaks.
6. **Dead Men has no Fragile Alliance lines of Kane's or Lynch's own.** Its 430 `Multiplayer/` lines
   are one voice per line, no character in the key or the file name. What it has of the two is
   bark sets: Kane `hero_default` (20 slots, 54 clips, in all four FA banks), Lynch `little`
   (55 slots, 206 clips) and `little_coop` (20 slots, 57), story banks only - and the merged stream
   file already holds 199 of 199 streamed clips of `little` and 39 of 39 of `hero_default`.
7. **Three faults found** (section 6):
   - **The Retomoto build that is installed now (`<work>\build\rt_ai\retomoto_ai`, swapped in
     11:45) was built with the voice repairs OFF.** Its guards have Dead Men's 31-slot voice sets
     again, 107 streamed ADPCM clips, 2 mute guards, .WAV 23,041,360 bytes. The builds the owner
     played before (`play3s`, `x_chunks\retomoto_wardrobe`, `y_loot\retomoto_loot`,
     `rt_masks\retomoto_masks`) have .WAV 27,158,864 = repairs on. The 'soldiers replay the same
     thing' complaint is back in this build.
   - **Retomoto speaks F07's job**: briefing 'grab the files', reminder 'Get the data', reaching
     the loot 'get the data', exit 'cross the main street to the back alley'. Ten keys of
     `Multiplayer/F07/`. Every stock level's lines are in the bank with their clips, so fitting
     ones cost nothing: table and proven calls in 6.2.
   - **The exit-heist line is silent, in stock F07 too**: `OnlineSpeakPlayer` looks its key up
     plain (EXE 0x8cb6e0) and `Multiplayer/F07/ExitHeist_01_R` exists only as `_C1.._C8`.

Budget (the four blocks a level reads in one piece; nothing was built, so before = after):

| build | .prm | .ANM | .fxc | .WAV |
|---|---:|---:|---:|---:|
| `z_maps\M01` | 55,088,000 | 22,061,764 | 17,760,648 | 21,722,704 |
| `z_maps\M02` | 54,619,216 | 22,202,472 | 17,760,648 | 22,527,568 |
| `z_maps\M03` | 60,469,040 | 22,202,616 | 17,760,648 | 22,716,752 |
| `z_maps\M06` | 49,585,744 | 21,642,576 | 17,760,648 | 21,775,744 |
| `rt_ai\retomoto_ai` | 79,269,328 | 21,642,904 | 17,760,648 | 23,041,360 |

What each proposal of section 6 would add is given with it. None adds a model.

## 1. How a line gets its voice (EXE)

### 1.1 The line objects

`ZOnlineFragileAllianceSettings::Init` (0x88d780; runs when the session is Arcade or online Fragile
Alliance: 0x863a60 or 0x7f6850) fills the speech manager `[0x168e958]`: 96 groups of up to three
alternative lines (lists at manager + 0x00 .. + 0x8b8, 0x18 apart, filled through 0x877a30) and 25
single lines (pointers at + 0x8d0 .. + 0x93c). Field -> offset for all 302 fields: scratch
`bvoice\init.py` (parsed off the call sites).

A line (0x28 bytes, 0x6b8710): `+0` the entry of a plain line, `+4` a list (count `+8`, data
`+0x14`), `+0x18` the key, `+0x1c` time of first use, `+0x20` per-character flag, `+0x24` the third
argument of Init.

- flag 0: one lookup of K (0x828fa0) -> `+0`.
- flag 1: **ten** entries: `K_C1` .. `K_C9` (indices 0..8) and `K` + `_R_C9` (index 9); an entry
  without a leaf is null. K itself is not looked up (`re/voice.md` 1.3).
- **`+0x24` is a priority, not a person** (`re/voice.md` called it 'who'): the play call 0x578840
  keeps a queue of at most ten waiting lines, 0x14 bytes each `{priority, entry, speaker, f32,
  byte}`, inserted before the first entry with a smaller priority, compared unsigned - so -1 goes
  first, then 4 (backstab reply), 3, 2, 1.

### 1.2 Saying one (0x58a070 group, 0x421c70 line)

`0x58a070(group, other line, speaker, x)`:
- nothing when `[[0x168e598] + 0x15d]` is 0 or the group is empty;
- one of the group's lines at random (the engine's own generator at `[0xdd2640] + 0xb30`);
- **a group does not speak again within 15.0 s** (`group + 0x14` = time of its last line, constant
  0xd1af98) - the first time always passes;
- then `0x421c70(line, other line, speaker, x)`.

`0x421c70`, the Arcade branch (0x7f6850 true = session kind 0 / 1 and mode `[session + 0x5c]` = 4;
rules = `[[0x168e9e4] + 0x54]`):

| speaker byte | entry of a per-character line |
|---|---|
| a player slot 0..7 | `list[ byte at rules + 0x33e + slot ]` (0x6ae750) |
| -2 (0xfe) | a random slot among those in the round whose status (rules vtable + 0x1c8) has neither bit 4 nor 8, any slot if there is none; then as above. (If the list had exactly 9 entries: entry 8. It has 10.) |
| -6 (0xfa) | entry 8 = `K_C9`, Glazer |
| the entry is null | **entry 0, `K_C1`**; nothing if that is null too |

A plain line plays its one entry whatever the speaker byte is. The byte travels on with the line
(0x578840) - ASSUMPTION by the keys it comes with: -3 the police side, -4 the driver, -5 the
undercover cop, -6 Glazer, -2 the crew; that is which of the three `ZSpeaker*` objects sounds.
The 'other line' argument is an on-screen text line, played only when the option `Online_Tutor`
is on (0x566ad0).

The online branch (session kind 2 / 3) picks by `0x817160(session, slot, 8)` through a jump table
0x422170 (0..7) instead, and takes a random entry for -2. Not this stage.

Bounds: the list accessor 0x51ab20 is `0 <= index < count, else int3`. Count is 10.

### 1.3 The table `rules + 0x33e` (eight bytes) and the byte `rules + 0x33d`

- Constructor (0x835837 .. 0x83584e): `+0x33d` = a random 0..7 (the body the human gets),
  `+0x33e + i` = i.
- An AI heister registers through ZGameRulesHeist slot 198 (0x588980): slot = its place in the
  rules' player list (1..7), byte = `name[0x12] - '1'`, where the name is the one at
  `[[x + 4] + 0x6c]` of what 0x598460 returns for the actor. ASSUMPTION: that is the actor's
  **parent group** - `Glazer_Bodyguard_0N` has its digit at index 18, the actor itself is called
  `Ground`. Stock F01..F09: seven AI heisters, digits 2..8 = indices 1..7 (MEASURED, the check).
- The game's body swap, slot 137 (0x8f5e90): the human takes `heroes[+0x33d]`; the AI heister that
  wore that model takes the human's old one, is renamed to character 0's name (0x478df0(0)), and
  **the two table bytes are exchanged** (0x8f5fbf: `table[0] = table[ai slot]; table[ai slot] = 0`).
  So in stock the human's line voice is the voice of the body he was given.
- The table has **no other reader**: 0x6ae750 has two callers, both in 0x421c70. A write to it
  changes which `_C<n>` leaf is spoken and nothing else. (The HUD name comes from 0x478df0 at the
  swap, not from the table.)

### 1.4 Who is the speaker, event by event

From the 97 call sites of 0x58a070 and the 20 of 0x421c70 (scratch `bvoice\sites.txt`; the third
pushed argument). 'P' = a player slot the event concerns (the human or an AI heister).

| event (settings fields) | per character | speaker |
|---|---|---|
| briefing 17, 18-20 | yes | P (0x8d2c10) |
| backstab 27-29 / alliance reminder 63-65 | yes | **another** heister: 0x5977b0 picks a random slot that is neither the traitor nor the victim; nobody left -> -6 = Glazer (0x67ee80, called from ZGameRulesHeist slot 129 = Arcade, and from 0x778f20) |
| backstab reply 33-35 (plain form) / 30-32 (radio form) | yes | the traitor; the plain form when the local player is the traitor, the radio form when he is the victim |
| revenge 36-38 / 48-50, revenge rejected 42-47 / 54-59 | yes | P |
| shoot off money 66-71, call escape 78-83, shoot escape 90-92, escape damaged 96-98 / destroyed 102-104 | yes | P |
| call-escape response 87-89, boarding 108-109, last escape 112-114, hold the vehicle 173, boarding end inside 188-190, bribe accepted 194-196, time warnings 161-163 | no | -4 (the driver) |
| cash majority 118-120, jackpot 124-126, reach / exit loot 127 / 130, mission reminder 136-138, you escaped 143-148, level bounds 149-151 | yes | P |
| **escaped and a player left behind 176-178** | yes | P (0x4060c0) |
| **driver bribe 191-193** | yes | P = the briber (0x65c620) |
| **driver traitor 197-199** | yes | P (a slot chosen by the caller) |
| police lines (84-86, 93-95, 99-101, 105-107, 152-154, 164, 168, 170, 179-181 ...) | no | -3 |
| undercover cop 24-26, 305-310 | no | -5; won / lost 209-214: -3 / -6 |
| team mode 245-286 | no | -2 / -3 by side |
| exit heist (`OnlineSpeakPlayer`, 0x780550) | plain, section 6.3 | slot 0 |

Confirmed for AI heisters as speakers: the traitor routine (it draws the speaker from all slots of
the rules object). For the other events 'P' is whatever slot the rules code passes; that an AI
heister's own pick-up fires `jackpot` in its voice was **not** traced call by call.

## 2. Barks (the voice set of a character)

- **Which definition speaks** (EXE): the character's virtual `+0x548` returns it. `ZFFPlayer`
  0x65ca10: `[player + 0x275c]` if set, else field 0 (`[player + 0x1e8]`). `ZFFActor` 0x636bf0:
  `[actor + 0x694]` if set, else field 0. `ZLNKWHANDS` / `ZPlayer` 0x6fb2a0: field 0. This is the
  'which of fields 0..2' `re/voice.md` left open, for the accessor; who fills `actor + 0x694` for
  the police (three sets each) was not traced.
- The override is written by one class besides the constructors: **`ZSoundDefCtrl`** (controller
  name `SoundDefController`, fields `def, bool, 2 x type 51, type 39`; 0x7092c0 from its slot 26):
  it puts the address of its own definition field into the override of the actor / player it
  hangs on, or clears it. **No stock level uses it** (0 in all 21, MEASURED). Not a route to build
  on untried.
- The player's speech component is `[player + 0x840]`; 0x4a7860(component, slot) plays slot n of
  the definition above. **It has no test of the game mode**: its gates are the owner's own
  mute-until time and the end of its own last clip. Callers with a constant slot: 0 (pain), 1
  (death; beside an 0x863a60 test), 5, 14, 15, 16, 18, 20, 27, 39, 40 (cover), 41 (from
  ZGameRulesHeist slot 7, 0x74b6d0); four more callers pass a computed slot. So **a heister with a
  voice set would bark in Arcade** as far as this routine goes (ASSUMPTION for the callers; LIVE).
- The two Dog Days player sets do not share a slot order (MEASURED, L01):
  `lynch_default` 42 slots - 0 pain, 1 die, 21 / 25 die_helper, 22 / 24 enemy spotted, 23 first
  contact, 26 sniper, 27 heartbeat, 28 - 30 breathing, 31 ammo out, 32 ammo low, 33 guns, 34
  reload, 35 panic, 36 - 38 Kane's breathing, 39 / 40 cover, 41 car impact;
  `kane_default` 63 slots - 0 pain, 1 die, 4 / 5 enemy spotted, 16 panic, 23 sniper, 31 adrenalin,
  58 ammo low, 59 ammo out, 60 reload, 61 / 62 cover. The constant slots above fit `lynch_default`
  (39, 40, 41, 27) and only 0, 1, 5, 16 of `kane_default`: Lynch's is the player layout, Kane's
  the companion's. `hero_voices` (re/voice.md) puts `kane_default` on four heisters: they would
  get pain, death, 'enemy spotted' and panic only.
- Stock allies with a voice (MEASURED): L02 3 `Thug` + `Glazer`, L03 15 `Thug`, all team Ally,
  fields `(squad, squad_02, 0)`: 35-slot NPC sets, 63 + 67 clips, streamed Vorbis in Dog Days' own
  stream file. Banks that hold them: L02 L03 L07 L11. The Fragile Alliance AI heisters
  (`Lynch_NPC` x4, `Kane_NPC` x3 per level) have none in F01..F09.

## 3. Counts per build (`python tools/kl_voice.py heisters <zip>`, 2026-10-10)

| | M01 | M02 | M03 | M06 | Retomoto (`rt_ai`) | stock F07 |
|---|---:|---:|---:|---:|---:|---:|
| per-character keys (flag 1) with a clip for all eight | 104 | 104 | 103 | 102 | 102 | 102 |
| - eight Dog Days recordings (`stream vorbis`) | 26 | 26 | 27 | 28 | 102 | 102 |
| - one Dead Men recording for all eight (`stream pcm set`) | 78 | 78 | 76 | 74 | 0 | 0 |
| key x heister pairs: Vorbis / interleaved PCM / none | 208 / 624 / 0 | 208 / 624 / 0 | 216 / 608 / 0 | 224 / 592 / 0 | 816 / 0 / 0 | 816 / 0 / 0 |
| Glazer's entry `K_C9`: with a clip / no leaf | 78 / 26 | 78 / 26 | 76 / 27 | 74 / 28 | 9 / 93 | 9 / 93 |
| plain keys (flag 0) with a clip: Vorbis / interleaved PCM / none | 80 / 54 / 0 | 80 / 54 / 0 | 80 / 54 / 0 | 80 / 54 / 0 | 126 / 0 / 0 | 126 / 0 / 0 |
| line fields left empty (flag 1 / flag 0) | 4 / 60 | 4 / 60 | 5 / 60 | 6 / 60 | 6 / 68 | 6 / 68 |
| streamed clips that are no clip of the installed stream file | 0 | 0 | 0 | 0 | 0 | - |
| heisters / police players with a voice set | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| AI heisters | 0 | 0 | 0 | 0 | 0 | 7, indices 1..7, no voice set |
| `OnlineSpeakPlayer` key found (plain) | - | - | - | 1 of 1 | **0 of 1** | 0 of 1 |
| soldiers with / without a voice set | 13 / 0 | 12 / 0 | 15 / 0 | 14 / 0 | 89 / **2** | 33 / 0 |
| women without a voice (no female set in F07's bank) | 2 | 2 | 3 | 0 | 0 | 0 |
| Dead Men soldier sets still in 31-slot order | 0 | 0 | 0 | 0 | **3** | - |
| findings: CRASH / SILENT / NOTE | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 1 / 1 | 0 / 1 / 0 |

- Formats: 'interleaved PCM' = Dead Men's dialogue form (one stream block carries the languages),
  the form of the Retomoto theme, **the one form the owner has confirmed by ear**. Vorbis = Dog
  Days' own. No heister line is ADPCM, in memory or streamed.
- The Dead Men maps hold Dead Men's settings (field N -> N + 8, `re/audio.md` 6) with nine alias
  leaves per per-character key (`kl_voice.loc_aliases`): briefing, backstab, reply, revenge,
  alliance reminder, shoot off money, call escape, shoot escape, escape damaged / destroyed, cash
  majority, jackpot, loot, reminder, you escaped, level bounds, time out, all escaped = one voice.
  The Dog Days-only events keep eight voices there: left behind 176-178, driver bribe 191-193,
  driver traitor 197-199, undercover cop 215-220, team 233-241 / 290-292 / 299-301 (and single
  fields F07 filled in: M03 102, M06 68 / 71).
- So on a Dead Men map **'Kill him! What is his, is yours!' comes in one voice whoever says it,
  and 'Just go! We'll split the score' in the speaker's own**. Whether the mix grates: LIVE.
- The level-specific lines of all nine stock levels are playable in every build (their sounds are
  in F07's bank): 63 - 67 of 71 - 74 leaves per `Multiplayer/F0x/` folder have a sound object.

## 4. A Dead Men body today

`klhook/klchar.c` writes `heroes[slot]` = the chosen model and `rules + 0x33d` = slot, then calls
the game's slot 137. For a Dog Days character the routine finds the AI heister that wears the
model and exchanges the table bytes: the voice follows the body. **For a Dead Men body no entity
wears the model, the loop at 0x8f5f08 finds nobody and returns before the exchange**: the human's
table byte stays what it was - 0 (J.C., `K_C1`) if the game's own swap has not run before the
hook's, else the index of the Dog Days body the game gave him first. ASSUMPTION which: the order
of the two calls was not traced. Either way:

- barks: none (the eight heister objects have no voice set; the body is only a model number);
- lines: a Dog Days merc's recording on Retomoto, Dead Men's one voice for 74 - 78 keys on the
  four Dead Men maps;
- the six crew bodies (Ashkanan .. Hutchison): the same. Dead Men has no voice of theirs at all -
  its named crew voices are the campaign's (`carlos`, `rific`, `shelly`, `thapa`, `mercenary_01`).

## 5. What exists to give Kane and Lynch (and the AI heisters) a voice

MEASURED on the stock banks (`scratch bvoice\defs.py`, `sz.py`); 'in the stream file' = the clip's
Dead Men offset is in `<work>\build\PC_Def.str.map.json`, i.e. already in the installed file.

| set | game, banks | slots / clips | what it says | clips by form | in the stream file |
|---|---|---|---|---|---|
| `kane_default` | DD, L00..L11 | 63 / 70 | pain 7, die 9, enemy spotted 2, panic 14, sniper 3, adrenalin 12, ammo low 8 / out 1, reload 5, cover foley | 61 Vorbis, 9 in memory | Dog Days' own |
| `lynch_default` | DD, L00..L10 | 42 / 157 | pain 10, die 11, die_helper 6, enemy spotted 7 + 2, sniper 3, ammo out 8 / low 8, 'guns' 7, reload 10, panic 16, breathing, cover | 144 Vorbis, 13 in memory | Dog Days' own |
| `squad`, `squad_02` | DD, L02 L03 L07 L11 | 35 / 63, 67 | the ally crew: pain, die, enemy close, suppress, heavy fire, advance, man down, battle cries | Vorbis | Dog Days' own |
| `goon_01` | DD, in F07's bank | 35 / 63 | an enemy thug | Vorbis | Dog Days' own |
| `hero_default` (Kane) | DM, 19 banks incl. the four FA | 20 / 54 | pain 4, death 1, orders 'go there' 8 / 'follow me' 8 / 'shoot at my mark' 7, 'running low on ammo' 4, 'Lynch shot me' 5, breath, flashbacks | 33 streamed ADPCM, 14 in memory, 6 - 7 Vorbis | 39 of 39 |
| `little` (Lynch, the companion) | DM, 16 story banks | 55 / 206 | the full soldier set in slots 0..25 (pain, die, grenade, contact, close, spotted, kill, suppress, cover talk, heavy fire, advance, man down 7) + 26 dying, **28 die_helper 4, 31 man-down response 12**, orders, ammo sharing, 49 humming, 50 muttering 12, 53 refusing orders 13, 54 psycho 9 | 186 interleaved PCM, 13 PCM, 7 in memory | 199 of 199 |
| `little_coop` (Lynch, the player) | DM, 16 story banks | 20 / 57 | pain, death, orders 12 / 14 / 6, low on ammo 3, 'Kane shot me' 5 | 33 streamed ADPCM, 8 interleaved PCM, 5 Vorbis, 11 in memory | 46 of 46 |
| `mercenary_01` | DM, M01_A .. M09_A | 49 / 127 | a crew member: soldier slots 0..25, die_helper 4, man-down response 4, ammo sharing | 96 interleaved PCM, 12 streamed ADPCM, 19 in memory | 108 of 108 |

- Slots 0..25 of a Dead Men companion set (`little`, `mercenary_01`) mean what Dog Days' NPC slots
  0..25 mean (the same table as `re/voice.md` 1.1), so they fit an **AI heister** (a `ZFFActor`
  with a soldier controller) directly; `kl_voice.def_slots` handles 31 slots only and would need
  the 49 / 55-slot cases (27 28 29 34 from 18 / 17 / 3, the rest cleared).
- For a **player** the slot order is another one (section 2): a Dead Men player set (`hero_default`,
  `little_coop`) has to be re-ordered into `lynch_default`'s: 0 <- 0, 1 <- 1, 32 ammo low <- 12,
  and nothing else maps - Dead Men's player sets are orders and ammo, Dog Days' are combat barks.
  So **for the player Kane / Lynch the Dog Days story sets are the better voice** (the same two
  actors, the right slot order for Lynch), and Dead Men's `little` is the better voice for an **AI
  Lynch**.
- 'Help you up': Dog Days `die_helper_lynch` (6 clips, slots 21 / 25 of `lynch_default`), Dead Men
  `die_helper` (slot 28 of `little`, `mercenary_01`, 4 clips each) and `mandown_response` (slot
  31, 12 / 4). Nothing in Fragile Alliance asks for those slots; a revive behaviour would have to
  call them (the hook, or a scripted `Audio_PlaySound`).

## 6. Gaps and the repair calls

### 6.1 The installed Retomoto build lost the voice repairs

`<work>\build\rt_ai\retomoto_ai` was built with `kl_snd.VOICE` off (its bank is byte for byte the
size of the first played build's). To put it right the build has to be made again with the
repairs on, the way `kl_maps.ready_one` does for the four maps:

    import kl_snd
    kl_snd.VOICE = True          # before kl_graft.build / kl_maps.chain; None again afterwards

Expected then (MEASURED on `rt_masks\retomoto_masks`, which has them: census and the check run on
it, 0 notes): .WAV 23,041,360 -> 27,158,864 (+4.1 MB, the Japanese shouts as in-memory ADPCM),
sounds / waves 4,941 / 4,790 -> 4,967 / 4,816, soldiers with / without a voice 89 / 2 -> 91 / 0,
streamed ADPCM clips 107 -> 0. `.prm`, `.ANM`,
`.fxc` unchanged. Check: `python tools/kl_voice.py heisters <zip>` must not print the
'31-slot order' note. (File owner: the Retomoto build is kl-merge-b6's / the lead's.)

### 6.2 Retomoto speaks about F07's data theft

Fields 17 - 20, 127, 130, 136, 137 name `Multiplayer/F07/...`. Fitting lines of other stock levels,
all eight voices with a clip in the build's bank (proven in memory on `rt_ai\retomoto_ai`, scratch
`bvoice\rtlines.py`: the check then reports no SILENT and the eight fields as 8 x Vorbis):

| field | now (F07) | proposed | text (C1) |
|---|---|---|---|
| 17 first briefing | 'Ok, when they come out, we grab what they got ...' | `Multiplayer/F05/MissionBriefing_03_R` | Keep it down. Get in and get the cash at any price. Understood? |
| 18 | 'You see them step outside, you go in, grab the files ...' | `Multiplayer/F01/MissionBriefing_03_R` | Once the bomb is detonated, get in there quick, grab what you can and get out before the cops arrive. |
| 19 | 'Once they got the data ...' | `Multiplayer/F05/MissionBriefing_02_R` | Move in quietly. The fuckers wont know what hit 'em. |
| 20 | (= 18) | `Multiplayer/F05/MissionBriefing_01_R` | Keep it down and take 'em by surprise. |
| 127 reach the loot | 'Shoot the bastards and get the data! ...' | `Multiplayer/F06/ReachlootArea_01_R` | Alright! Grab the cash. |
| 130 leave the loot | 'Ok we got it! Now move out!' | `Multiplayer/F04/ExitLootArea_01_R` | We got it! Let's keep moving! |
| 136 reminder | 'Get the data, don't let anyone stand in your way.' | `Multiplayer/F06/MissionReminder_01_R` | Just get the money. |
| 137 reminder | 'If any more come out ... Get the data ...' | `Multiplayer/F09/MissionReminder_02_R` | We can do this. Be quick 'cause this is gonna turn nasty! |
| exit heist | 'cross the main street to the back alley' (silent anyway) | `Multiplayer/F04/ExitHeist_01_R` | Get out on the street! straight ahead! |

ASSUMPTION: the choice (by the texts, for the balcony start / the bomb / the street). Costs
nothing: no sound, no file grows but the .LOC by one leaf (6.3). The calls, for the Retomoto layer
(`tools/kl_fa_author.py` is kl-merge-b6's; `sc` is the joined scene before it is written):

    import kl_fa, kl_voice
    RT_LINES = {17: 'Multiplayer/F05/MissionBriefing_03_R', 18: 'Multiplayer/F01/MissionBriefing_03_R',
                19: 'Multiplayer/F05/MissionBriefing_02_R', 20: 'Multiplayer/F05/MissionBriefing_01_R',
                127: 'Multiplayer/F06/ReachlootArea_01_R', 130: 'Multiplayer/F04/ExitLootArea_01_R',
                136: 'Multiplayer/F06/MissionReminder_01_R', 137: 'Multiplayer/F09/MissionReminder_02_R'}
    for k, i, v in kl_voice.settings(sc):
        def fn(us):
            for f, s in RT_LINES.items():
                us[f] = [kl_fa._str(sc, s)]
        kl_fa.edit(sc, k, i, fn)

### 6.3 The exit-heist line (`OnlineSpeakPlayer`)

Looked up plain, once, at init (0x8cb6e0: key at controller + 0x38 for the crew, + 0x3c for the
police; the entry is played with speaker slot 0). Stock F07's key has no plain leaf, so it is
silent in stock and on Retomoto. M06's own (`Multiplayer/JapGarden/FA_JapBossEsc_R`) is plain and
found. Repair = a plain
leaf with the text and sound of one variant, in each of the nine `.LOC`, and the key on the
controller:

    import kl_loc
    def plain_alias(loc, key, variant=1):
        t = kl_loc.parse(loc); path = key.strip('/').split('/'); tab = t
        for p in path[:-1]:
            tab = next(k.kids for k in tab if k.name.lower() == p.lower().encode() and k.kids is not None)
        src = next(k for k in tab if k.name.lower() == ('%s_c%d' % (path[-1], variant)).lower().encode())
        if not any(k.name.lower() == path[-1].lower().encode() for k in tab):
            kl_loc._insert(tab, kl_loc.Node(path[-1].encode(), src.flags, None, src.raw))
        return kl_loc.build(t)
    for k, i, v in kl_fa.controllers(sc, 'OnlineSpeakPlayer'):
        kl_fa.edit(sc, k, i, lambda us: us.__setitem__(1, [kl_fa._str(sc, 'Multiplayer/F04/ExitHeist_01_R')]))

(MEASURED: the English .LOC goes 448,896 -> 448,963 bytes and round-trips.) One fixed voice then
(heister 1's) says it whoever the player is - the price of the plain lookup. ASSUMPTION: 0x828fa0
does no variant search of its own (`kl_voice.py test`: 1,124 plain-only keys in flag-0 fields, 0
the other way round).

### 6.4 A voice for the AI heisters (when they exist on the maps)

The stock answer is `squad` / `squad_02` (section 2). Append them from L02 the way `hero_voices`
appends the story sets, and name them on the bots:

    src = kl_snd.bank('L02'); base = kl_snd.Snd('dd', snd, ls).walk()
    want = {o for o in src.tables[5] if src.name(o).lower().endswith((b'/squad#def', b'/squad_02#def'))}
    snd, whd, wav, omap = kl_snd.merge(base, src, whd, wav, kl_snd.read(kl_snd.beside('L02', '.WHD')),
                                       kl_snd.read(kl_snd.beside('L02', '.WAV')), want)
    a, b = (omap[o] for o in sorted(want, key=src.name))
    for k, kind, slots, anim in kl_voice.characters(sc):
        if kind == 'bot':
            kl_voice.set_voice(sc, k, (a, b, 0))          # as L02 / L03: (squad, squad_02, 0)

Not run. Cost by the two sets' records (MEASURED on L02): 63 + 67 clips, **all streamed** Vorbis in
Dog Days' own stream file (1,301,269 + 1,522,839 bytes there), none in memory - so about 130 sounds
and waves in the bank and **nothing in the .WAV**. Seven bots would share two voices - the
way the 15 thugs of L03 do. Variety by character needs recordings that do not exist (the eight
mercs have lines, not barks). LIVE: that an Ally actor barks in Arcade (it does in the story).

For an AI **Lynch** (a bot in Lynch's Dead Men body, a later wish): `little` from M09_A - in the
Retomoto chain its 199 streamed clips are already in the stream file, so it is sound objects only
(+206 sounds / waves, + 80,896 bytes in the .WAV); `kl_snd.graft_audio(..., more_roots={offset of
little#def in M09_A's .SND})` and a 55-slot case in `kl_voice.def_slots`. On the four Dead Men
maps the source bank would be a story level's - a second bank merge per map. Not built.

### 6.5 Kane's and Lynch's own voice on the player

Data (per build): `kl_snd.VOICE = {'heroes': True}` appends `kane_default` / `lynch_default` from
L01 (re/voice.md: 83 sounds, 80 waves; bank 4,967 / 4,816 -> 5,012 / 4,858 on Retomoto) - but it
names them on the eight heister **objects** by animation set, so J.C. would speak with Kane's
voice and Kane's body, sitting on any object, with whatever that object has. The voice has to
follow the **body choice**, and that is the hook's:

- Data: bring both definitions into the bank (`hero_voices` with the last loop left out), write
  their .SND offsets and the offset of `engine/material#def` into `KLWardrobe.ini`
  (`VoiceKane=`, `VoiceLynch=`, `Material=`).
- Hook (`klhook/klchar.c`, the lead's; **described, not written**): after the body is set and
  when the choice is KLChar 9 (Kane) or 10 (Lynch): bank base = `[player + 0x238]` (field 5, the
  material definition every player has) minus `Material`; check that the dword at base + Voice is
  5 (a definition's type) and the next 0xcdcdcdcd; write `[player + 0x1e8]` = base + Voice (heap
  dword, field 0). Any other choice: write 0 back. ASSUMPTION: a loaded definition's address is
  bank base + .SND offset (the check before the write is there because this was not read), and
  that field 0 may change while the level runs (the accessor reads it on every call).
- LIVE: whether a heister barks at all in Arcade (section 2), and whether Kane with only pain /
  death / spotted / panic is worth it. A re-ordered `kane_default` in `lynch_default`'s slot
  order would give him ammo and reload lines too (32 <- 58, 31 <- 59, 34 <- 60, 35 <- 16, 22 / 24
  <- 4, 39 / 40 <- 61 / 62): a `defs` hook of `kl_snd.merge`, ASSUMPTION by the set names.

### 6.6 The line voice of a Dead Men body

Two bytes for the hook, same place as 6.5 (described, not written): after its slot-137 call for a
Dead Men body in crew slot s, exchange the table bytes the way the game does for a Dog Days body:
find i with `rules[0x33e + i] == s`, then `rules[0x33e + i] = rules[0x33e]; rules[0x33e] = s`
(the human's player slot is 0 in Arcade: ASSUMPTION, it is what 0x8f5fce writes). Kane then always
speaks J.C.'s lines, Lynch Tommy's, and no AI heister shares the voice. The table has no other
reader (1.3).

A Dead Men line voice for the two (one recording, 74 - 78 keys) would be: table byte 8 for the
human and `K_C9` leaves that name Dead Men's line of the same event. On the four Dead Men maps
those leaves exist already (the aliases); on Retomoto 93 of 102 keys have no `K_C9` and would need
Dead Men's FA lines grafted into its .LOC and bank (421 clips are in the stream file). But
Glazer's own nine `K_C9` lines and the -6 announcements use the same entry. Not recommended
before the owner has heard the Dead Men lines on a Dead Men map and wants them.

**6.6a Written 2026-10-18 (klchar.c `klc_voice_swap`, `[Wardrobe] DMVoice=1`, build `C:\kl_build_1018\voice2`)**: the table
swap above for a Dead Men body in crew slot s (owner item 10). GUESS: the human's player slot is 0. Not run in the game.

**6.6b The fed you come back as (owner item 12) - NOT DONE, finding only.** A policeman player (type 3) is not a
per-character speaker: ZGameRulesFragileAlliance skips type 3 (characters.md), `rules+0x33e` is read only by 0x421c70
for per-character lines (1.3), and the police events are plain lines with speaker -3 (1.4), the same entry for every
policeman. So there is no table byte for the fed to swap; the Dead Men or Dog Days sound of a police line is decided by the
level's `.LOC` leaves (on Dead Men maps the plain keys are 80 Vorbis / 54 Dead Men PCM, section 3). What is left is his
bark set (`[player+0x275c]` or field 0 `[player+0x1e8]`, section 2): no stock FA level gives police players one, and who
fills the police actors' `+0x694` was never traced. Pointing it at a Dead Men definition is the same untested write as
6.5 (a loaded definition's address = bank base + .SND offset is an ASSUMPTION) and the fed is created on respawn, so it
cannot be proven offline. Route for later: a kltalk pool event for the fed (Who = a policeman does not exist yet in
kltalk.c), or 6.5's write on the respawned type-3 player once a live run shows his `+0x1e8`.

## 7. For the AI heister graft (b-bots / the lead)

1. **Keep the group names** `Glazer_Bodyguard_02 .. _08`, or any name with a digit '1'..'8' at
   index 18. The digit is the voice (and nothing else, 1.3). A shorter name, '0', or a character
   above '9' + 1 gives an index outside the line's ten entries: **int3 at 0x51ab2d** the first
   time that bot speaks a per-character line (backstab reply, jackpot, bribe ...). Two bots with
   one digit share a voice. '9' = entry 8 (Glazer's, empty for 93 keys: heister 1's voice).
   `kl_voice.py heisters` reports all three cases (CRASH / NOTE) and exits non-zero on a CRASH;
   proven by renaming groups of stock F07 in memory.
2. The bots need nothing in the bank to **speak lines**: all `_C2 .. _C8` entries are there on
   every build (section 3). They need 6.4 to **bark**.
3. On the four Dead Men maps a bot's backstab / jackpot / escape lines are Dead Men's one voice
   (aliases); its bribe / left-behind lines its own. To make a Dead Men map use Dog Days' eight
   voices throughout: `kl_fa.settings_from_host` (re/voice.md 5.5) - then the briefing is F07's
   (6.2 applies) and Dead Men's lines are gone. Owner's choice after hearing both.
4. A 15 s gate per line group and a ten-line queue (1.1, 1.2) are the engine's: seven bots
   hitting one event at once say it once.

## 8. What only ears can settle, in order

1. A real Arcade round on a Dead Men map (M03): is the briefing heard at the start; who is the one
   Dead Men voice; does it clash with the Dog Days voices of the bribe / left-behind lines?
2. Retomoto after 6.1: the guards as `re/voice.md` 7.5 describes.
3. Retomoto after 6.2 / 6.3: do the chosen lines fit; is the exit line heard at all.
4. With AI heisters and 6.4: do they bark; is two voices for seven acceptable.
5. With 6.5: does the player's Kane / Lynch grunt, call reloads; with 6.6: is J.C.'s voice from
   Kane's mouth worse than a random one.

## 9. Not established

- That the name read at 0x588980 is the parent group's (by the digit position only).
- The order of the game's own slot-137 call and the hook's; the human's player slot in Arcade.
- Call by call, that an AI heister's own events (its pick-up, its escape) pass its slot as speaker.
- The speaker codes -3 -4 -5 (by the keys only); which `ZSpeaker*` object each one sounds from.
- Who fills `actor + 0x694`; the shape of what `ZSoundDefCtrl` stores; whether fields 1 / 2 of a
  player are ever read.
- The four player-speech callers with a computed slot (0x5239c0, 0x742320, 0x7ec5b0, 0x465c10).
- The sound and wave pool limits (largest that ran live: 4,967 / 4,816).
- The meaning of the 10.0 / 20.0 floats handed to the queue (0xb3ef8c, 0xb64cc8).
- `kl_voice.census` counts a speak trigger as 'with its line' when either form of the key exists;
  for `OnlineSpeakPlayer` only the plain form counts (the new check does it right; census was
  left as it is).

Scratch (session scratchpad `bvoice\`): `kl2.asm` (whole-exe listing), `init.py` / `init.json`
(field -> manager offset, flag, priority), `sites.py` / `sites.txt` (every play site), `hl.py` /
`hl.json` (per-field states of the five builds), `defs.py`, `sz.py`, `dm3.py` (voice sets),
`rtlines.py` (6.2 / 6.3 in memory), `heisters.txt` (the check's output on all six).
