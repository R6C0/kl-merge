# Character speech on a grafted level

2026-10-09, agent m-voice. **Offline only**: the game was not started, nothing was installed, nothing
was written into the Dog Days folder. Tool: `tools/kl_voice.py`; hooks in `tools/kl_snd.py`
(`merge(defs=)`, `graft_audio(voice=)`, `VOICE`). Builds on `re/audio.md`, `re/characters.md`.

Words: **EXE** = read in kl2.exe at the address given; **MEASURED** = counted on this machine's
files; **ASSUMPTION** = fits the evidence, not proven; **LIVE** = only a run with ears can settle it.

    python tools/kl_voice.py test                 the facts of sections 1-2 re-measured (1 min): problems: 0
    python tools/kl_voice.py census <level|zip>   characters, voice sets, clip formats, line keys of a level
    python tools/kl_voice.py build [<out>]        bank + Retomoto, without / with the repairs / with the
                                                  heisters' experiment -> <work>\build\voice (6 builds, 6 min)
    python tools/kl_voice.py defs <level>         a stock bank's definitions slot by slot
    python tools/kl_voice.py variety <level|zip>  per voice set and slot: distinct clips, silent members
    python tools/kl_voice.py build2 [<out>]       bank + Retomoto without / with the repairs -> <work>\build\voice2

## 0. Result

**After the owner's first round (2026-10-09): 'the soldiers replay the same thing too many times'
- cause, engine facts and repair are section 7; what to listen for now is 7.5.**

The owner hears music and too little from the characters. Three separate causes were found, and
one thing that is not a fault of the graft:

1. **Bank (and every Dead Men FA map): 77 of its 228 line fields are silent.** Dog Days reads 108
   of the settings' line fields *per character* (`K_C1..K_C9`) and never falls back to the plain key
   (EXE, section 1.3). Dead Men recorded one voice per line, so its keys have no `_C<n>` leaves:
   briefing, backstab, revenge, jackpot, 'you escaped', level bounds ... find nothing. Repair:
   nine alias leaves per such key (`loc_aliases`). After: **0 silent, 237 heard**.
2. **Dead Men guards shout the wrong thing, or nothing, on four events.** A voice set is a table of
   slots, one per event. Slots 0..25 mean the same in both games; Dog Days' code also asks for 27
   (battle cry), 28 / 29 (advance) and 34 (alert), which a Dead Men table does not have - and
   Dead Men's slot 27 is a wounded man begging ('I'm a good man...'), which Dog Days would play as
   the battle cry. Repair: `def_slots` (ASSUMPTION which Dead Men set feeds which slot).
3. **Some characters have no voice at all**: 6 of the bank's 15 guards and its 5 civilians, 2 of
   Retomoto's 65 guards (Dead Men gave them none). Repair: `give_voices`.
4. **Not a fault of the graft: Dog Days' heisters are mute by design.** In all nine stock Fragile
   Alliance levels the 16 players have no voice set (MEASURED), and there is no idle-banter object
   in them. What a stock crew says are the settings' lines only (briefing, reminders, backstab,
   time warnings), and those need a real round - a direct boot (`-o DefaultScene`) has none.
   What the owner remembers as characters talking is Kane and Lynch in the story, who do have voice
   sets. `hero_voices` puts those two sets on the eight heisters: an **experiment**, off by default.

Streamed ADPCM (a third of Retomoto's clips, **all** of the Japanese guards' shouted lines): the
exe has a decode path for it (EXE, section 1.5). Nothing was re-encoded. Whether it sounds right is
the first thing to listen for (section 5).

| | bank before | bank after | Retomoto before | Retomoto after |
|---|---|---|---|---|
| soldiers with / without a voice set | 9 / 6 | 15 / 0 | 63 / 2 | 65 / 0 |
| civilians with / without | 0 / 5 | 2 / 3 (the three women) | none on the map | none |
| voice sets in Dog Days' slot order | 0 of 1 | 1 of 1 | 0 of 3 | 3 of 3 |
| Dog Days events 27 28 29 34 that find a set | 0 of 4 | 4 of 4 | 1-2 of 4 (wrong ones) | 4 of 4 |
| line fields heard / silent / empty | 157 / **77** / 68 | 237 / 0 / 65 | 228 / 0 / 74 | 228 / 0 / 74 |
| .LOC keys (spoken) | 5,820 (3,659) | 6,450 (4,289) | 5,685 (3,530) | 5,685 (3,530) |
| heisters with a voice set | 0 of 8 | 0 (8 with `heroes`) | 0 of 8 | 0 (8 with `heroes`) |
| sounds / waves in the bank | 4,918 / 4,782 | same (5,001 / 4,862 with `heroes`) | 4,941 / 4,790 | 4,929 / 4,778 (5,012 / 4,858) |
| streamed ADPCM clips, all / in voice sets | 14 / 12 | 14 / 12 | 107 / 98 | 95 / 86 |
| `kl_graft.verify` | 0 problems | 0 | the 1 known (particle names) | the same 1 |

MEASURED by `kl_voice.py build` (log: `<work>\build\voice\`, the six archives are kept there).
With `VOICE` off the bank's `.SND .WHD .WAV .prp` and nine `.LOC` are byte-identical to the build in
`<work>\build\install`, and Retomoto's `.SND .WHD .WAV .LOC` to the played `build\play_rt` (its `.prp`
differs: `kl_fa_author.py` changed since).

## 1. How a character speaks in Dog Days

### 1.1 Barks: the voice set

- A character is a `ZFFActor` or `ZFFPlayer` (both below `ZLNKWHANDS`). `ZLNKWHANDS` stores six sound
  definitions, type handler 46, at object +0x1e8, +0x1f8 ... +0x238 (EXE: property records at
  0xd073d8 ... 0xd07374; a seventh, a float, at +0x248). Fields 0..2 are voice sets, 3 and 4 are 0
  in every stock level, 5 is `engine/material#def`. `ZFFActor` has one more definition of its own
  (+0x808, 0 in F07).
- A definition (`#def`) is `{... +0x14 list*, +0x18 u16 count}`: one slot per speech event, each a
  `set` of sounds or empty. The code asks for an event by slot number. **Every reader checks the
  number against the definition's own count** (EXE: all 17 call sites of the list accessor 0x65c140,
  e.g. 0x7a1040, 0x474770, 0x4e5a30, 0x84a940, 0x900ff0: `cmp index, [def+0x18]; jb; else none`).
  A definition of another length is therefore safe; an empty or missing slot is silence.
- Slot meaning, from the names of the sets in every stock bank (`kl_voice.py test`):

  | | Dog Days NPC (35 slots, 21 banks) | Dead Men NPC (31 slots, 20 banks) |
  |---|---|---|
  | same in both | 0 pain, 1 die, 3 first contact, 4 enemy close, 5 enemy spotted, 7 suppress response, 8 suppress, 13 heavy fire, 16 panic, 18 advance, 25 man down | the same, plus 2 grenade, 9-12 cover talk, 15 team disruption, 17 advance response, 19 tear gas |
  | differs | 27 battle cries, 28 / 29 advance, 34 alert | 26 hurt, 27 grace shot, 28 police warning, 30 no access |

  Civilians: Dog Days 6 slots (0 pain, 1 die, 4 scream, 5 panic), Dead Men 5 (1 die, 4 scream).
  Players: `kane_default` 63 slots (0 pain, 1 die, 4 / 5 enemy spotted, 16 panic, 23 sniper, 31
  adrenalin, 58 ammo low, 59 ammo out, 60 reload, 61 / 62 cover), `lynch_default` 42 slots.
- The set picker and the one gate found on a bark: section 7.2.
- Which of fields 0..2 an actor speaks with (stock police have three: police_01 / 02 / 03) was
  **not traced**. Who decides *when* (the AI's soldier / squad code calling the event) was not traced
  either: the slot numbers above are the whole interface a level file has to it.
- F07's voice sets (all it has): `police_01` 92 clips, `police_02` 89, `police_03` 100, `goon_01` 63,
  `civilian_male_01` 24, `civilian_male_03` 24 (all streamed Vorbis), `dog_01` 4 (in memory). No
  woman, no Japanese voice. Other Dog Days levels have `civilian_female`, `civilian_female_02`,
  `goon_02`, `squad`, `squad_02`.

### 1.2 Heisters

MEASURED (`test`): F01..F09 each have 16 `ZFFPlayer`, none with a voice set; L01 and L03 have 2, both
with one. The seven bot team mates (`Glazer_Bodyguard_0N`, team Ally) have none either. kl2.exe also
holds hard-coded line keys for Kane and Lynch only (`AllLevels/Oneliners/Reload/Reload_020_Kane`,
`.../HumanShield/%s/...`, `.../DownNotDead/...`): story speech, not Fragile Alliance.

### 1.3 Lines: the settings' 302 keys

`ZOnlineFragileAllianceSettings::Init` (EXE 0x88d780) walks its string members (field N at object
+0x2c + 4N) and builds a line object for each through 0x6b8710 (directly, or 0x877a30 for the
three-alternative groups). Arguments: the key, a number stored at line +0x24 (-1, 1, 2, 3, 4: not
decoded), and a **flag**:

- flag 0 (0x6b8994): one lookup of the key K (0x828fa0). No leaf = no line.
- flag 1 (0x6b879d .. 0x6b8978): ten lookups, `K_C1` .. `K_C9` (`sprintf "_C%d"`) and `K` + `_R_C9`;
  each result or null is stored in a list, line +0x20 = 1. **K itself is not looked up.**

`kl_voice.LINES` is the flag of all 302 fields, read off the call sites. Proof on the files: over
F01..F09, 917 keys in flag-1 fields exist only as `_C<n>`, 1,124 keys in flag-0 fields exist only
plain, **0 the other way round** (20 name no leaf at all). C1..C8 are the eight heisters, C9 Glazer
(`re/characters.md`); which index is taken when a line plays was not traced.
(`re/audio.md` 5 and `kl_fa.spoken` say 'K_C1..K_C9 and then K': wrong on the second half.)

Flag-1 groups: briefing 17-20, backstab 27-29 and replies 30-35, revenge 36-38 / 48-50, revenge
rejected 42-47 / 54-59, alliance reminder 63-65, shoot off money 66-71, call escape 78-83, shoot
escape 90-92, escape damaged 96-98 / destroyed 102-104, cash majority 118-120, jackpot 124-126,
reach / exit loot 127-132, **mission reminder 136-138**, you escaped 143-148, level bounds 149-151,
time out 167, all escaped 169, and the Dog Days-only groups from 176 on.

Other speech objects: `OnlineSpeakTrigger` finds its line by sound name
(`audio:dialog/<key>#sound`, `kl_graft.mute_speech`); `OnlineSpeakPlayer`'s lookup was not read
(F07's names `Multiplayer/F07/ExitHeist_01_R`, which exists only as `_C1.._C8`). The three speakers
(`ZSpeakerDriver`, `ZSpeakerTeamCriminals`, `ZSpeakerTeamPolice`) are `ZLNKWHANDS` objects with all
six definitions 0 and one string; both builds keep them (`kl_fa.host_keep`).

### 1.4 Idle talk

The exe has a class `ZSmallTalkCtrl` (controller `SmallTalkCtrl`, `ff2\levelsetup\smalltalkctrl.cpp`).
No controller of that name is in F01, F06, F07, L01 or L04 (MEASURED), so stock levels do not use it,
and no timer or flag of a level gates 'banter'. What a waiting crew hears in stock is the settings'
mission reminder (136-138) and the time warnings (161-166). They are fired by the game rules in a
real round; which float of the settings is their interval was not read. On Retomoto the settings
are F07's own, all 228 lines intact.

### 1.5 What must exist for a line to be heard

LOC leaf with a sound id -> `sound` object in the level's .SND -> `wave` -> .WHD record -> the
clip in the .WAV (in memory) or at the record's offset in PC_Def.str. The record names the codec.
The buffer fill routine (EXE 0x79ff50, `ZSoundBufferWintel` vtable 0xb9a9dc slot 12, shared by the
DirectSound and OpenAL buffers) reads the format word at record +4:

| format | branch | |
|---|---|---|
| 0x11 IMA ADPCM | 0x7a001e | buffer kind 1 (in memory): 0x7a004d. **Any other kind (streamed): 0x7a00c1** - sets block size = channels * 0x400, decodes block by block with the same decoder 0x6d2020, handles the three interleave modes |
| 0x1000 Vorbis | 0x7a0254 | the embedded `ZVorbisStream` |
| anything else | 0x7a04e0 | PCM, single or interleaved |

So the formats the stream reader accepts are PCM, Vorbis **and ADPCM**; the code for streamed ADPCM
is in the retail exe although Dog Days ships no such clip. Dead Men's records (block 0x400, 0x7f9
samples per block, mono) match what that path computes. Not re-encoded. LIVE: that it sounds right.
What has been confirmed by ear so far is an interleaved PCM set (the Retomoto theme).

## 2. What the graft does to each piece

| piece | bank (F07 + M03_FA_A) | Retomoto (F07 + M09_B + M09_A) |
|---|---|---|
| heisters, police players | F07's nodes, untouched: no voice set, as stock | the same |
| soldiers | kl_convert puts Dead Men's one voice into slot 0 and the material table into slot 5 (`LEVEL_MAPS['ZLNKWHANDS']` {0: 0, 5: 1, 6: 2}: correct); `graft_audio` moves both into the merged bank. 9 have `usa_swat_01` (31 slots, 22 clips: 8 in memory, 12 streamed ADPCM, 2 streamed PCM), 6 have none (the `Police` animation-set guards) | 44 `jpn_guard_01`, 18 `jpn_police_01`, 1 `jpn_bouncer_01` (31 slots; 73 / 63 clips: 15 in memory, 4 PCM, 54 / 44 streamed ADPCM), 2 none |
| civilians | 5, none with a voice (Dead Men gave them none) | all dropped with the campaign |
| stray voice references | 0 | 0 |
| speakers | 3, F07's | 3, F07's |
| settings | Dead Men's object through the field table (N -> N + 8): its keys are in the .LOC with their clips (135 leaves), 131 heard, **77 silent** (flag-1 fields), 68 empty of which 3 Dog Days has a line for (94 shoot-escape police, 109 boarding, 163 three minutes); field 102 names a key no .LOC has | F07's object: 228 heard, 74 empty as stock |
| speech triggers | 7 `OnlineSpeakTrigger`, each with its sound | F07's `OnlineSpeakPlayer` (exit heist) |
| campaign dialogue | - | `M09/Dialogue` (88 keys, 76 spoken), megaphones, `Audiotriggers!`, `Block_Speak`: dropped with the campaign subtrees; 0 Dead Men keys in the .LOC. Not wired (it is story dialogue; the police megaphone on the street would suit the Heat scene - a job for the street layer) |
| squad lists | `ZSquadScript`'s 15 reference lists hold scene paths (triggers); none is speech. The `SQUAD_LISTS` pairing was not examined here | the same |

## 3. The repairs (`tools/kl_voice.py`)

| function | what | guess |
|---|---|---|
| `def_slots(name, slots)` | `kl_snd.merge(defs=)` hook. A 31-slot Dead Men definition becomes 35 slots: 0..25 as they are, 26 27 28 30 cleared, 27 <- Dead Men 28 (else 18), 28 <- 18 (else 17), 29 <- 17 (else 18), 34 <- 3 (else 5, 4). `test` prints the result for the six maps' definitions | ASSUMPTION: the pairing, by set names |
| `give_voices(sc, ks, s_name, snd)` | a soldier / civilian among the map's nodes without a voice set gets the one most of its kind have on the map, else the systems level's (`prefer='host'`: the other way). A woman only gets a woman's set | ASSUMPTION: mute soldiers should sound like their squad |
| `fill_lines(sc, ks, s_name, known)` | a line field of the map's settings that is empty or names no .LOC key takes S's key (bank: 3 + 1) | ASSUMPTION: Dog Days' line beats none |
| `loc_aliases(files, sc, ks, want)` | for each grafted key in a flag-1 field: leaves `K_C1..K_C9` with K's text and sound in all eight languages (bank: 70 keys, 630 leaves) | none in the lookup; all eight heisters then speak with Dead Men's one voice |
| `hero_voices(sc, snd, whd, wav, ls)` | appends `kane_default` / `lynch_default` from L01 (83 sounds, 80 waves, 31 sets, 6 sequences; 127 objects reused from F07) and names them on Hero_01..08 by animation set | **EXPERIMENT**: that `ZFFPlayer` barks in a round; four Kanes |
| `census(path)`, `test()`, `build()` | the counts above | |

`kl_snd.py`: `merge(..., defs=None)` relays a definition's slot list through the hook;
`graft_audio(..., voice=None)` runs the four repairs (and `heroes` on request); `VOICE = None` is the
default when the caller passes nothing. `kl_loc.py`: docstring corrected (the lookup rule).

## 4. Call lines (files I do not own)

**`tools/kl_graft.py`** - nothing has to change: set `VOICE = True` in `kl_snd.py` (or
`VOICE = {'heroes': True}`) and every build has the repairs. To make it a build option instead:

    def build(..., bones=True, voice=None):
    audio = kl_snd.graft_audio(s_name, m_name, Jn, [mj[k] for k in sorted(m_nodes)], log, loc=loc, voice=voice) if sound else None

and in `main`: `voice=({'heroes': '--voice-heroes' in a} if '--voice' in a or '--voice-heroes' in a else None)`.
`kl_maps.one / chain` pass unknown options through to `build`, so `voice=True` works there too.
In a chained build the second step needs no change either (`hero_voices` finds the two
definitions already in R09's bank; `give_voices` takes the first map's Japanese police voice for a
mute guard of the second).

**`tools/kl_fa_author.py` / `tools/kl_fa_street.py`** - a squad they move or copy keeps its voice
fields, nothing to call. If a layer authors actors from a template of another level, or wants to
check what it built:

    import kl_voice
    kl_voice.give_voices(Jn, new_node_indices, s_name, snd, log)     # after graft_audio: snd = audio.members['.SND']
    kl_voice.census(path_of_the_built_zip, log)                       # 'soldier': {'without': n} must be 0

Lines for authored events (a megaphone, a guard's shout at the blast): an `OnlineSpeakTrigger` whose
key has a sound named `audio:dialog/<key, lower case>#sound` in the merged bank; bring the clip
with `kl_snd.graft_audio(..., more_roots={offset of that sound in M's .SND})`.

## 5. What only ears can settle, in the order to listen

Build with `VOICE = True` first; add `heroes` in a second build so a fault can be told apart.

1. **Retomoto, tower: do the guards shout in Japanese when they see you / when one dies?** Yes =
   streamed ADPCM works (54 of their 73 clips) and Dead Men voice sets work. Only pain / death
   grunts (those 15 clips are in memory) = streamed ADPCM is silent: then re-encode the 95 clips to
   PCM in `kl_str.merge` (`kl_audio.ima_to_pcm`) and write the record as PCM in `kl_snd.merge`
   (`stream_rec`), or move them into the level's .WAV. Noise = the block size differs.
2. **Same guards: what do they shout when they charge?** With `def_slots` it should be the police
   warning / 'advance' lines, never the begging line.
3. **Bank, real round from the menu: the briefing at the start** (field 17, was silent). Then
   shoot a partner (alliance reminder), pick up a big stack (jackpot), wait (mission reminder).
4. **Bank: the six bank guards and the two men in the hall** - do they have voices now (Dead Men's
   SWAT voice, F07's civilians)?
5. **Is Dead Men's line the same voice whoever of the crew says it?** Expected (one recording).
   If that grates, the alternative is `kl_fa.settings_from_host` (Dog Days' lines on Dead Men maps).
6. **`heroes` build: does your own character grunt when hit, call out reloading, taking cover?**
   Silence = the player code does not bark in Fragile Alliance and the option can go. If it works:
   is Kane's voice from four different faces acceptable?
7. On a direct boot (`-o DefaultScene`) only 1, 2, 4 and 6 can be heard: there is no round.

## 6. Not established

- Which code fires a bark and with what timing; which of voice fields 0..2 is used; the meaning of
  the line argument -1 / 1 / 2 / 3 / 4; which `_C<n>` a line takes (speaker's or listener's index).
- `OnlineSpeakPlayer`'s lookup (plain or per character).
- The mixer group and parameter conversion of Dead Men sounds (`kl_snd.GROUP`, dropped types 3 6 7,
  the float 0.6): a Dead Men line could be too quiet rather than silent.
- The sound and wave pools: the `heroes` builds hold 5,012 sounds / 4,858 waves; the largest build
  that ran live held 4,941 / 4,790, the largest stock bank 4,806 / 4,568.
- The three women in the bank have no voice: F07 has no woman's set. F01, F02, F08 and F09 have
  `civilian_female` / `civilian_female_02` (MEASURED); appending one the way `hero_voices` appends
  Kane's is the obvious next step (not done).
- M01 / M02 / M06 were not built here; the code is the same and their settings have the same shape.

## 7. Repetition: 'the soldiers replay the same thing too many times' (2026-10-09, agent q-repeat)

The owner played a full round on Retomoto (build `<work>\build\play_rt`, repairs off) and heard the
Dead Men guards say the same lines over and over. **Offline only** again: nothing was started,
installed or written into the Dog Days folder. Builds: `<work>\build\voice2\{before,after}`.

    python tools/kl_voice.py variety <level|zip>   per voice set and slot: distinct clips + silent members
    python tools/kl_voice.py build2 [<out>]        bank + Retomoto without / with the repairs (2.5 min)

### 7.1 Causes

| | | status |
|---|---|---|
| A | **Dead Men's Japanese voice is thin exactly where Dog Days' own voice is richest.** Clips per event, Dog Days `police_01` vs `jpn_guard_01`: enemy spotted 12 / **0**, enemy close 4 / **1**, suppress response 10 / **2**, suppress 12 / 4, heavy fire 2 / **1**, advance 13 / 6, man down 12 / **2** | MEASURED |
| B | **The same six 'police warning' clips serve two events** in the played build: Dead Men slot 3 (first contact: 1 clip + those 6) and Dead Men slot 28, which Dog Days' definitions use for 'advance'. (`def_slots`, had it been on, would have added them to 27 and 34 as well: it moved whole sets.) | MEASURED |
| C | **All 44 tower guards have one voice set**, the 18 street police another that shares 61 of its 63 clips with it. A set's play state lives in the set (7.2), so the whole tower is one speaker with 73 clips. Dog Days gives every policeman three sets (fields 0..2 = `police_01`, `_02`, `_03`: 145 of 145 police in F02, F07, L04; 92 + 89 + 100 clips) | MEASURED |
| D | The graft did **not** collapse voices: Dead Men's own M09_A has `jpn_guard_01` on its guards (73 references in the .prp, 4 `jpn_bouncer_01`, 1 `guard_japanese_male_01`), M09_B `jpn_police_01` (80; 9 `guard_japanese_male_01`) | MEASURED (raw dword count in the .prp) |
| E | **Nothing was lost in the merge.** The played bank offers per slot exactly what Dead Men's bank does (73 / 63 / 73 clips, table in 7.4), in the same mode | MEASURED |
| F | Streamed ADPCM not playing would leave only the 15 grunts. That is not what the owner describes ('the same thing' = lines), and static reading says it decodes (7.3) - but it cannot be proven offline, so the dependence is removed | EXE + ASSUMPTION |

Which of A, B, C the owner's ear caught cannot be told apart offline; the repair addresses all three.

### 7.2 How a set picks, and what gates a bark (EXE)

- **Set, +0x20 = mode** (kl2 0x4ddb10; Dead Men has the same routine at 0x5d3d30): **0** = in order
  (+0x1c is the next index), **1** = at random (`rand * n`, generator 0x41aa70), **2** = a bag: +0x1c
  is a 32-bit mask of the members that had their turn, one of the others is drawn, and when a single
  one is left the mask is cleared before its bit is set (so the last of a round can not open the
  next). Mode 2 with one member is rewritten to 0, with more than 32 members to 1. Stock use: Dog
  Days 5,446 sets mode 2, 212 mode 1, 10 mode 0; Dead Men 4,532 / 55 / 3,518. The Japanese speech
  sets are all mode 2 (pain: 0). The record is 0x30 bytes in both games and `merge` copies it whole.
- The state is **in the bank image**: one bag per set object for everybody who uses it.
- 0x8401f0 resolves an object to a sound: sound -> itself, set -> the picker, again for a set in a
  set; a null member plays nothing (no stock set has one: 0 of 5,668 + 8,105).
- **Sound** (0x7a1200 copies it to the voice): +0x18 f32 (handed to 0x867da0), DD +0x1c f32 (new),
  +0x20.. the cone, +0x2c byte, +0x2d volume 0..100, +0x2e bit 0, +0x2f byte (Dog Days police lines
  0x14 / 0x1e, Dead Men 0; read beside the distance math in 0x78b080), +0x30, DD +0x31 / +0x32 two
  flags (new). None is a repeat count or a time. **So what Dog Days added to the sound is a float
  at +0x1c and two flag bytes, not a history or cooldown field**; the merge writes 0.6 and 0, 0
  (stock police lines have 0.3: ASSUMPTION what it is).
- **The one gate found on a bark** (0x763200, 'say slot n of this definition'; 0x8b1f00 is its
  twin): the 16-byte definition field of the character is `{def, flag, f32 time}`; with the flag
  set nothing starts before `time` = start + the wave's seconds (wave +0x18, x 1024 ticks). A
  character does not talk over itself - there is **no squad or global cooldown in it**.
- Dropped parameter types 3, 6, 7: nearly absent from the voice path. Of M09_A's 257 police /
  guard sounds 3 carry a type 3 (value 0), the rest types 0x12 and 0x1f only; the merge drops 2 + 3
  parameters on all of Retomoto. What types 3, 6, 7 mean was not read. Dog Days' police
  sounds add type 0x21 (value 1) and its sets type 8 (-100, 100: ASSUMPTION a pitch spread); what
  they do was not read. A mixer group limiter exists (0x5c8270, group +0x2c / +0x4b): seen, not decoded.
- Not traced: which of voice fields 0..2 a character uses (C rests on the stock levels), who calls
  the slots and how often. Slots pushed as constants around the actor's speak routine 0x7f16f0:
  0 1 2 6 7 9 10 13 14 15 16 17 19 27.

### 7.3 Streamed ADPCM (EXE)

The buffer fill 0x79ff50 takes the codec from the **.WHD record** (`[buffer+0x60]` = record - 4: +8
format word, +0x1c channels, +0x28 samples, +0x2c block, +0x30 samples per block), not from the
stream file's own format table. For 0x11 in a streamed buffer (0x7a00c1) it overwrites the block
size with channels * 0x400 and calls the decoder 0x6d2020 that the in-memory path calls. Dead Men's
records (mono, 0x400, 0x7f9) fit. What is not provable offline is the feeding side (the stream object
at buffer +0x48, three modes at +0x24), which no stock Dog Days clip ever sends ADPCM through.
`stream_clip` therefore moves these clips into the level's .WAV as in-memory ADPCM: the same bytes
(every block checked: step index <= 88, zero byte), the form of 643 of F07's 729 in-memory records
(32 kHz mono, 0x400 / 0x7f9; 16 and 22.05 kHz occur in stock too). Four moved clips decoded with
`kl_audio.ima_to_pcm` look like speech (peaks about 32,000, mean step 1,400 - 3,000). A localized
(nine-record) wave whose clip moves becomes a one-record wave. The 8 single PCM stream clips
(Dog Days ships 42 such) and the music sets stay streamed.

### 7.4 The repair (`kl_voice.planner`, options `variety`, `cycle`, `inmem`; all on with `VOICE = True`)

1. **Wider slots, no line in two of them** (`NPC_POOL`, ASSUMPTION by set names). The clips of
   neighbouring Dead Men sets and of Dead Men's second Japanese voice (`guard_japanese_male_01`, in
   both M09 banks: attacks 4, 'fight breakout' 7, 'break down door' 5; its hurt / panic / begging
   sets are not used) are dealt out: 4 enemy close <- 4 + attacks; 5 enemy spotted <- 5 + cover talk
   10, 12; 7 suppress response <- 7 + cover responses 9, 11; 13 heavy fire <- 13 + team disruption
   15; 25 man down <- 25 + panic 16; 27 battle cry <- 'fight breakout'; 28 advance <- advance
   response 17; 29 advance <- 'break down door'; 34 alert <- 'no access' 30 (the guard sending you
   away); 3, 8, 18 keep their own. A Dead Men slot that lent its clips (9 10 11 12 15 16 17) names
   the **same new set**, so related events draw from one bag - the way stock `police_01` has one
   'advance' set in slots 18, 28 and 29. The begging lines (Dead Men 27) and 'I've been shot' (26)
   are no longer in any slot.
2. **No line again before 8 calls of its event** (`cycle=8`): every speech set with fewer than 8
   clips is filled to 8 members with a silent sound (`audio:dialog/kl_merge/silence#sound`, one
   in-memory ADPCM block of zeros, 0.064 s, tuned like the clips beside it). Mode 2 then gives each
   line once per 8 calls and the other calls are quiet: a slot with 4 lines speaks every second
   time. This is the data-only throttle - no cooldown field was found. `cycle=0` turns it off
   (a 1-clip slot then repeats as before); 32 is the most a bag holds.
3. **Every clip in a form Dog Days ships** (`inmem`, 7.3).
4. Not done, with reasons: **a second / third voice per character** (fields 1, 2) - Dead Men has
   no second full Japanese set (the other one has no pain slot and 16 shouted clips, which are in
   the pools instead) and how the engine chooses among the fields is not traced; **a Dog Days voice
   for variety** - stock sets by language: all English (`police_01..03`, `goon_01..02`, `squad`,
   `squad_02`, the four civilian sets; `dog_01`), **no Japanese-speaking set in any of the 21
   banks**, so none is mixed in; **one-shot slots** - no such mode exists (nearest: `cycle=32`).

Distinct clips per slot, played build -> `voice2\after` (`+ns` = silent members):

| slot (Dog Days event) | police_01 (stock) | jpn_guard_01 | jpn_police_01 | usa_swat_01 (bank) |
|---|---:|---|---|---|
| 0 pain / 1 die | 6 / 4 | 9 / 6 unchanged | 9 / 6 unchanged | 3 / 5 unchanged |
| 3 first contact | 8 | 7 -> 7+1s | 7 -> 7+1s | 0 |
| 4 enemy close | 4 | 1 -> 5+3s | 1 -> 5+3s | 1 -> 1+7s |
| 5 enemy spotted | 12 | 0 -> 4+4s | 2 -> 6+2s | 2 -> 3+5s |
| 7 suppress response | 10 | 2 -> 5+3s | 2 -> 5+3s | 2 -> 4+4s |
| 8 suppress | 12 | 4 -> 4+4s | 4 -> 4+4s | 1 -> 1+7s |
| 13 heavy fire | 2 | 1 -> 4+4s | 1 -> 4+4s | 1 -> 2+6s |
| 18 advance | 13 | 6 -> 6+2s | 6 -> 6+2s | 3 -> 3+5s |
| 25 man down | 12 | 2 -> 5+3s | 2 -> 5+3s | 0 |
| 27 battle cry | 6 | 5 (begging) -> 7+1s | 0 -> 7+1s | 0 -> 3+5s (the advance set) |
| 28 / 29 advance | 13 / 13 | 6 (warnings) / 0 -> 4+4s / 5+3s | 6 / 0 -> 4+4s / 5+3s | 0 -> 3+5s (the advance set) |
| 34 alert | 3 | 0 -> 5+3s | 0 -> 7+1s | 0 -> 3+5s (enemy spotted) |
| all slots | 92 | 73 -> 82 | 63 -> 79 | 22 -> 22 |

| | bank before | after | Retomoto before (= played) | after |
|---|---|---|---|---|
| streamed ADPCM clips | 14 | **0** (14 moved, 248,832 bytes) | 107 | **0** (65 + 67 moved, 4,116,480 bytes) |
| .WAV | 22,466,896 | 22,716,752 | 23,041,360 | 27,158,864 (+4.1 MB) |
| .WHD | 2,118,848 | 2,118,960 | 2,109,808 | 2,114,304 |
| archive | 321,126,272 | 321,178,763 | 312,397,329 | 312,397,986 |
| sounds / waves | 4,918 / 4,782 | 4,919 / 4,783 | 4,941 / 4,790 | 4,967 / 4,816 |
| sets made / silent members | - | 6 / 34 | - | 27 / 85 |
| soldiers with a voice | 9 of 15 | 15 | 63 of 65 | 65 |
| `kl_graft.verify` | 0 problems | 0 | the 1 known (particle names) | the same 1 |

MEASURED by `build2` (2026-10-09). Checks on the two `after` builds, from the files: the bank walks
clean (0 unclaimed, 0 overlap, 0 stray), every wave reference hits a record, every in-memory record
(1,012 / 1,164) has its data, no added stream record outside the merged stream file, no reference
into a torn group, `_LS.SND` names the new trailer, no made set over 32 members or with a null
member. `kl_snd.py test quick`: failures 0. `kl_voice.py test`: problems 0.
**With the repairs off nothing changed**: `voice2\before` Retomoto is byte-identical to the played
`build\play_rt` in `.SND .WHD .WAV _LS.SND` and all nine `.LOC`; the bank likewise to `build\voice\before`.

### 7.5 What the owner should now hear (a build with `VOICE = True`; nothing of it has been heard yet)

- Tower guards and street police still shout in Japanese, but **the same line does not come back
  until seven other calls of that kind of shout have passed**. Some of those calls are now silent,
  so there is also less shouting overall.
- **New lines** in the mix: the yakuza guards' attack shouts, 'fight breakout' shouts as battle
  cries, 'break down the door' shouts when they advance, the 'you can't come in here' lines when
  they are alerted.
- The six police warnings are heard on first contact only, no longer on 'advance' as well.
- **Gone** as combat shouts: the wounded man begging ('I'm a good man...') and 'I've been shot'.
- Pain grunts and death screams are as before (9 and 6 clips).
- If the guards are now **silent except for grunts**, the in-memory move is at fault: build with
  `VOICE = {'inmem': False}` to tell. If they still repeat, raise the cycle: `VOICE = {'cycle': 16}`.
- The bank's SWAT have 22 clips in all (Dead Men's `usa_swat_01`): they will mostly be quiet with a
  line now and then - the price of not repeating with so few recordings.

### 7.6 Risks, guesses, not established

- ASSUMPTION: `NPC_POOL` (which Dead Men lines fit which Dog Days event) - the clips are Japanese
  and were sorted by their set names only; and that a silent call is better than a repeat.
- The silent sound is a real sound: 0.064 s of zeros through the guards' mixer group, holding the
  speaker's own gate that long. A null member would be cheaper but no stock set has one.
- Pools: Retomoto `after` has 4,967 sounds / 4,816 waves, 26 above the build that ran live
  (4,941 / 4,790; largest stock bank 4,806 / 4,568). `VOICE = {'variety': False}` keeps the padding
  without the second voice's clips. The .WAV grows 4.1 MB (each chain step copies its own level's
  clips, so the Japanese lines both parts share are in it twice); the owner once had a 60.7 MB
  allocation fail at load, and whether this file is loaded in one piece was not checked.
- A made set is named after the first definition that asked for it (`..._bouncer_01_slot04` also
  serves the guards); tower and street have their own bags over largely the same clips.
- Not read: the code that fires barks and its rate, voice fields 1 and 2, parameter types 8 and
  0x21, the group limiter, what sound +0x1c and +0x2f do.

### 7.7 Call lines (files I do not own)

Nothing has to change in `kl_graft.py`, `kl_fa_author.py`, `kl_fa_street.py`: `kl_snd.VOICE = True`
(or a dict of `kl_voice.OPTIONS`: `{'cycle': 16}`, `{'variety': False}`, `{'inmem': False}`,
`{'heroes': True}`) switches everything on for every build; section 4's optional `voice=` build
argument still applies. New in `kl_snd.merge`: `defs` may return `kl_snd.Pool` objects, and `inmem=`.
A layer that authors squads from the map's own actors keeps their voice fields and so their sets.
