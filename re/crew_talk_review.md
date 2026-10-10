# Review: random AI looks, bots on Retomoto, Kane / Lynch talk, Bain

2026-10-10, agent v-review (adversarial). **Offline only**: the game was not started, nothing was installed,
nothing was written into the Dog Days folder. Only this file was written in the repository; everything else
went to the session scratch folder. Reviewed as they stood at 16:35:
`klhook/klcrew.c` (sha1 e3cb869b), `klhook/klcrew_rt.c` (be13f222), `tools/kl_fa_bots_rt.py`,
`tools/kl_fa_talk.py`, `tools/kl_bain.py`, and the builds under `<work>\build\v_rtbots`, `v_talk`, `v_bain`.

Words: **RAN** = a command of this session, with its result; **EXE** = read in kl2.exe with `debug\dasm.py` /
`debug\rtti.py` in this session; **READ** = by reading the source; **NOT ESTABLISHED** = nobody knows yet.

## 0. Verdicts

| piece | load it? | what must be fixed first |
|---|---|---|
| Random AI looks (`klcrew.c`) | **Wire it in, keys off, and run the control first** (C0, then C1). Never with `Random=1` as a default | Nothing blocks a first run. The 14:24 menu crash is not explained (section 1.4); the file that crashed is not this one. Fix the comment / spec against the code (1.3 a) |
| Bots on Retomoto (`kl_fa_bots_rt.py`, `klcrew_rt.c`) | **Tower-only build: yes, with today's hook.** Full build: only with `klcrew_rt.c` wired and `[CrewJoin] Enable=1` | For the owner's map the step must be run on the guns build (done here in scratch: passes, section 5). Two pointer checks worth adding (2.2 a) |
| Kane / Lynch talk (`kl_fa_talk.py`) | **Loads as silent data; nothing is heard.** The hook part `kltalk` does not exist | `kltalk` has to be written; three points of its description must change before that (3.3). Use the default build (Kane's lines in the safest form) |
| Bain (`kl_bain.py`) | **Yes, data only**, with the right stream file | Decide the stream file once (section 5). All 26 clips are in a record form no stock Fragile Alliance level has (4.2): one run by ear before it is kept |

All four can be ONE Retomoto build: built here in scratch, every checker passes on it (section 5).

## 1. `klhook/klcrew.c` (random AI heister looks)

### 1.1 Addresses and calls (EXE, all confirmed)

| claim | found |
|---|---|
| 0x783fb0 `(entity, model)`, `ret 4`: `0x792290([this+4], model)`, `this->vtable[0x1dc]()`, `[0x541960()]->vtable[0x70](node, 1)` | as written; first 14 bytes = `model_code` |
| 0x792290 writes `[node+0x68]`, tells the renderer when the node is drawn | as written; first 12 bytes = `node_code` |
| 0x88c810 `(entity, variant)`, `ret 4`: `[this+0x50] = v`, refresh | as written; 10 bytes = `variant_code` |
| 0x83e2e0 `(string*, text)`, `ret 4`; 0x469250 `(block, string by value)`, `ret 0xc`, frees the string | as written; 15 / 12 bytes match |
| vtables 0xbb3bac = ZFFActor, 0xbb45f4 = ZFFPlayer, 0xbd3514 = ZGameRulesHeist | RTTI says so |
| slot 119 = 0x417a60 in both actor classes; rules slots 137 / 34 / 198 = 0x8f5e90 / 0x4b5b20 / 0x588980 | as written |
| slot 137 does the same three steps inline to the AI member that wears the model (0x8f5f63..0x8f5f97); slot 34 writes variant 2 on every AI member (0x4b5c22..0x4b5c48) | as written |
| callers: 0x783fb0 two (0x74ee89, 0x8f5f03), 0x88c810 three (0x4b5c05, 0x4b5c60, 0x8228e4) | as written |

The calling conventions in the file fit the routines (`__fastcall` with a dummy second register argument for
`__thiscall`; one, one, one and three stack arguments).

### 1.2 Thread, inertness, compile

- READ: every game call sits behind `game_thread`; the only thing done off the game's thread is the voice byte
  through `klh_data`. `klh_tick` is single-entry (`klh_tick_busy`), so the file's static state is not raced.
- READ: without `[Crew] Random=1` `klw_tick` returns on its first line; `klw_init` only reads the ini.
- RAN: a scratch copy of `klhook\` with the three lines of each crew file added to `klhook.c`, built with the
  repository's own `build.bat` and `build_auto.bat` in a folder without spaces: both build. At `/W4` the only
  warnings from these two files are C4459 three times in `klcrew.c` (`seen` hides `klhook.c`'s global of that
  name; harmless, each use is the local one). `klcrew_rt.c`: none.
- The working tree's `klhook.c` does NOT have the crew lines now (CLAUDE.md says it has): a build from the
  tree is without both files.

### 1.3 Findings

a. **The code is tied to the level verdict, the comment and the spec say it is not.** Line 327:
   `if (!klx_on || ... klx_level_verdict(scene, why) != 2) return;` So the file does nothing on a stock level,
   nothing at the menu, and nothing when the Steam write guard is not installed. The top comment (section 4,
   'not tied to klsteam.c's verdict'), `re\crew_random.md` 3 'Policy', its test T12 and its line 'Stock Subway
   can stand in for C1' all say the opposite. Consequence for the live plan: **C1 cannot be run on stock
   Subway**; use a `b_bots` map. Decide which is meant and make the three texts agree.
b. `klw_player_char()` is only set when `Random=1`, the level is not stock AND at least one AI record is in
   play (the function returns at `if (!n) return;` before it). It also keeps its last value when the player
   has died and plays a policeman (the tick returns at `type != 2`). A part that asks 'is the human Kane?'
   (the talk part) must not rely on it: section 3.3.
c. Not a fault, a limit: `klw_voices` only handles record indices 1..7 and the table's eight bytes. Fine for
   seven bots.
d. NOT ESTABLISHED, and only a run can say: a model set on an actor after the level has started; what an
   attached gun or money bag does at that moment; seven Dead Men roots of 1,080 - 1,608 objects drawn at once.
   `re\crew_random.md` 8 lists these honestly.

### 1.4 The 14:24 menu crash (CLAUDE.md: 'klcrew.c crashed the menu')

RAN `debug\dump.py` on `<work>\research\crash_1010_1424\KLHook_1.dmp`:
- The fault is a call to 0x3f800000 from 0x8618b7, in `ZXMLGUISystem` slot 25 (0x861720). The object it
  called through is a **`ZBaseWindow`** (vtable 0xbaf6c4, 32 slots); the code asks for slot 33
  (`[vtable+0x84]`), which is the float 1.0 that follows the table. So: menu code took a plain window for a
  window class with more slots. Callers 0x6175ac, 0x7471ee (an action controller's event), the main loop.
- The dump holds no heap (505 ranges, 35 MB): the session, the rules object and the scene name cannot be read
  from it. **The cause is not established.**
- The hook of that run was built from `klcrew.c` sha1 0320d043 (the package's manifest). The file reviewed
  here is e3cb869b: it has the scene / verdict test of 1.3 a in front of everything, so at the menu
  (`SCENES\KaneAndLynch.gms`, no level key) it returns before it reads the rules object. READ, not run.
- The package of that run (`G:\kl_scratch\ai_crew_package`) carried its own `Overlay\Patch01.zip`; its
  `frontend.xml` differs from the installed one only by the Heister page's pictures (RAN: diff). No lead there.
- What would settle it: the lead's control C0 below, at the menu, before any level.

## 2. Bots on Retomoto

### 2.1 The builds (RAN)

| check | `retomoto_bots` | `retomoto_bots_tower` |
|---|---|---|
| `kl_fa_bots_rt.py check` | PASS, 0 FAIL, 9 + 1 NOTE, exit 0 | PASS, 0 FAIL, 9 + 1 NOTE, exit 0 |
| `kl_fa_bots_rt.py diff` against `rt_ai3\retomoto_ai3` | 'only the squad was added'; 303 entities; changed subtrees `Gameplay!AIMonitor`, `Specials!JumpPoints!06_Exit` | the same; 156 entities; `Gameplay!AIMonitor` only |
| `kl_impact.py` | problems: 0 | problems: 0 |

My own placement check (a separate script on the build's mesh, not the tool's check):
- 7 Ally actors; each stands on the mesh, on the START row's own part (part 33), at the mesh's height.
  Nearest player START point 113 .. 396 away (8 START points at x 6000, z -930..-690 and 530..770), nearest
  other bot 144+. **No bot is on a start point.**
- The seven `[CrewJoin]` places are on the street's part (part 0), at the mesh's height (570), 67 .. 84 from
  an open edge, 120 apart, 320 .. 509 from the jump entry where the player lands.
- The jump list: the tool's check resolves the seven references to one first street step
  (`DefendBehaviourRout`) in each squad; READ in its code, and it passes.

Members rewritten (RAN, CRC compare of the archives): `.buf .gms .oct .prm .prp .rmc .rmi` and `KLJoin.ini`.
**The .prm IS rewritten** (same size; 2,624 model roots get their `.oct` record offset moved): the note's
'nothing else changed' is true for content, but the member is not byte-equal, which matters for the order of
steps (section 5). The four large blocks: .prm 79,269,328, .ANM 21,642,904, .fxc 17,760,648, .WAV 27,158,864
before and after. Chunk table: untouched (65,118 on this base).

Risks that stay:
- The nearest bot stands 362 from the InvisiBomb, whose first radius is 300; the players' own places are 430+
  away. The 330 margin is a GUESS of the tool. Live check R1 / R2 shows it (a bot dead at GO).
- `Timer_start_bots` 14.0 s, loot wait 30 s, rally 10 s: GUESSES, marked as such.

### 2.2 `klhook/klcrew_rt.c` (EXE, all confirmed unless said)

| claim | found |
|---|---|
| 0x62a900 `(actor, rot, pos, a, b)`: `vtable[0x5bc](0.0)`, `vtable[0x2a8](rot, pos)`, `vtable[0x5d4](pos, 1, 0)` | as written; the 14 bytes of `tele_code` match; 22 call sites; ZFFActor slot 18 (0x6ccc80) calls it on itself at 0x6ccdc1 |
| int3 at 0x62a9b8 when `[actor+0x77c]` and `[actor+0x780]` are both zero | as written. A second one at 0x62aa43, same test, only with `b != 0` and a network session |
| 0x72e0f0 no stack argument, plain `ret`; one caller, 0x57e1da | as written; `trig_code` matches |
| 0x57e110: clears both requests, takes `[gamedata+0x8d4]`, calls 0x8f3fa0, then `0x72e0f0([entry+0x1c])` | as written |
| 0x4ebed0 = slot 26 of ZDefendBehaviourRout; message word 0x168d800 sets byte 0x41, word 0x168d804 starts the step | as written |
| player test at 0x8f3fcf: skip when node flag bit 10 is set | as written; the hook's test has the same sense |

a. **Two pointers the routine uses are not checked by the hook.** 0x62a998: `mov edx,[esi+0x7c0]` /
   `mov [edx],0` - a write through `[actor+0x7c0]` with no test; 0x62a9e8: a virtual call through
   `[actor+0x50c]`. The game's own callers do not test them either, so a living actor has both; but the hook
   reaches the actor from a crew record, not from a script that owns it. Cheap to add: do not hand over an
   actor whose `+0x7c0` or `+0x50c` is zero or unreadable.
b. The early form needs `kljoin.c` on: the places come from the file `kljoin.c` read. With the join off the
   part is inert (READ).
c. READ: off unless `[CrewJoin] Enable=1`; calls only on the game's thread; once per round; no data write.
d. NOT ESTABLISHED, as the note says: what a street step does when the hook part is off and the jump fires
   (the full build must not be played without it), and whether a tower step that is still waiting pulls a bot
   back (its N3).

## 3. Kane / Lynch talk

### 3.1 The builds (RAN)

| check | `retomoto_talk` | `retomoto_talk_adpcmstream` | `M02` | `over_talk\retomoto_talk_bain` |
|---|---|---|---|---|
| `kl_fa_talk.py check` | FAIL 0, NOTE 1 | FAIL 0, NOTE 1 | FAIL 0, NOTE 1 | FAIL 0, NOTE 1 (with `over_talk\PC_Def.str`) |

The NOTE is the same on all: the stream file in the game folder is the old one. `kl_fa_talk.py stream
--verify`: 0 problems in the appended blocks, 13 in the base that were there before.

Members rewritten (RAN): `.SND` and the eight `.LOC` in the archive; `.WHD`, `_LS.SND`, `KLTalk.ini` beside
it; and `.WAV` in the default build only. **.WAV: 27,158,864 -> 27,802,960 (+644,096)** in the default
build, **+0** in the `adpcmstream` build; .prm, .ANM, .fxc unchanged. M02: .WAV +162,816.

### 3.2 Can the countdown fire without Kane?

- In the data: no level object says any of it. No `.prp` / `.gms` byte differs from the source build (RAN),
  so without a hook part nothing is said at all.
- In `KLTalk.ini`: the countdown scene is `Needs=Kane` and holds only Kane's lines; the tool's check fails a
  scene whose lines are not its `Needs`' speaker (READ).
- So the answer depends only on how `kltalk` decides 'Kane is there', and that part is not written: 3.3 b.

### 3.3 `kltalk` does not exist. Three points of its description (`re\talk.md` 3) to change first

a. **Do not keep one line object per key.** EXE, 0x780550: the game allocates a NEW 0x28-byte line object
   for every line it says, hands it to 0x421c70 and never frees it itself. Either the speech manager owns it
   from then on or the game leaks it; which, is NOT ESTABLISHED. The description keeps one object per key for
   the whole level and hands it over again in the next round: if the manager frees what it is given, that is
   a use after free. Do what the game does: a new object per say.
   (0x421c70 is `ret 0x10`, four arguments, and returns at once when `[manager+0x956]` is set or
   `[[0x168e598]+0x15d]` is zero: as described.)
b. **Who wears Kane must be read from the models, not from `klw_player_char()`.** That function is 0 without
   `[Crew] Random=1`, without an AI record, and on a stock level, and it is stale after the player's death
   (1.3 b). Compare `[node+0x68]` of the player and of each AI record in play with the `Root=` of characters
   9 and 10 in the level's `KLWardrobe.ini`. That is also the only reading that cannot say 'Kane' when nobody
   wears him.
c. The round-start moment (state 0x19) is one observation; the description says so and has `StartOffset`.
   Evaluate `Needs` when the scene is due, not at the first tick: the crew draw comes 600 ms after everything
   stood still, a bot may become Kane after the round state began.

### 3.4 Clip forms (RAN: the new `.WHD` records against the forms the base level and stock F07 hold)

| lines | record form | precedent |
|---|---|---|
| Kane, default build: 19 | in memory, IMA ADPCM, block 1024, mono | 1,160 records in the base, 797 in stock F07: the stock form |
| Kane, `adpcmstream` build: 19 | streamed ADPCM (0x800011) | none anywhere; the note says so |
| Lynch: 7 sets | interleaved PCM set, ONE channel, member with a lip block, two of them at 16,000 Hz | the base has such sets only with two channels and without lip (the Retomoto music, which the owner heard); stock F07 has no set at all |
| pool keys: 187 | streamed Vorbis | stock |

So the countdown itself is in the safest form in the default build. Lynch's seven lines are in a form nobody
has heard: by ear only (the note's T4).

Bank size (RAN, all stock levels counted): the largest stock bank has 4,806 sounds (F05) and 4,568 waves
(F04). Retomoto ran live with 4,967 / 4,816. Talk makes 4,993 / 4,842, talk + Bain 5,019 / 4,868. Above
everything seen; the pool limits are NOT ESTABLISHED.

Stale number: `re\talk.md` gives `over_talk\PC_Def.str` as 1,694,364,711 bytes; the file is 1,694,610,488
(Bain's second pass rebuilt it; `re\bain.md` has the right number).

## 4. Bain

### 4.1 The builds (RAN)

`kl_bain.py check`: exit 0, 0 problems, on `retomoto_bain`, `retomoto_bain_driver`, `retomoto_bain_guns`
(each against `v_bain\PC_Def.str`) and on `over_talk\retomoto_talk_bain` (against `over_talk\PC_Def.str`).
26 Bain sounds (17 in the driver build), each named by a leaf in all 8 `.LOC` files; 0 streamed records
outside the stream file.

Members rewritten (RAN): `.SND`, the eight `.LOC`, `.WHD`, `_LS.SND`. **The four large blocks do not change;
.WAV +0.** No hook part, no ini key.

### 4.2 Findings

a. **The record form has no precedent in a stock Fragile Alliance level.** All 26: streamed, 16-bit PCM,
   mono, 32,000 Hz, no lip block (0x800001). Stock F07 has no streamed PCM record at all. The base level has 8
   of that codec, all WITH a lip block (Dead Men's Japanese lines, which nobody has reported hearing). The
   note's 'the 8 records of that shape' is not exact: they differ in the lip flag. Dialogue without a lip
   block is common in stock (2,272 Vorbis records), so the open question is only streamed PCM as a spoken
   line. One run by ear settles it: check B1.
b. `retomoto_bain_guns` (and the owner's `rt_guns3\retomoto_ai3_guns` it was made from) fail
   `kl_map_guns.py check`: `KLGuns.ini` has no `Entries=`; klgun.c Version 2 refuses such a file. Not Bain's
   doing. One line (`Entries=65331`) or a rebuild of the gun step.
c. Three stream files now descend from the installed one and exclude each other: `v_bain\PC_Def.str`
   (1,688,896,606), `v_talk\str\PC_Def.str` (1,690,199,891), `v_bain\over_talk\PC_Def.str` (1,694,610,488).
   A build made against one plays wrong lines on another. Pick one line of descent: section 5.
d. The stream file is 453 MB short of 2^31 bytes. kl2.exe is 32-bit; whether its offsets are signed is NOT
   ESTABLISHED. Keep count.
e. The mapping is by subtitle text only; the weak rows are named in `re\bain.md` 3.1. Nobody has listened.

## 5. One Retomoto build with all four

### 5.1 Which members each step rewrites (RAN, CRC compare of each build with its source; first row excepted)

| step | in the archive | beside it | reads |
|---|---|---|---|
| wardrobe / plates (`kl_chars`) | NOT compared here (no build pair at hand); by its docstring the model members | `KLWardrobe.ini` | - |
| gun looks (`kl_map_guns`) | `.MAT .TEX .gms .oct .prm .prp` | `KLGuns.ini` | chunk indices |
| bots (`kl_fa_bots_rt`) | `.buf .gms .oct .prm .prp .rmc .rmi` | `KLJoin.ini` | the heroes' models, the blast timer, the mesh |
| talk (`kl_fa_talk`) | `.SND`, 8 `.LOC` | `.WHD .WAV _LS.SND KLTalk.ini` | `KLWardrobe.ini` (Kane = 9, Lynch = 10), the blast timer |
| Bain (`kl_bain`) | `.SND`, 8 `.LOC` | `.WHD _LS.SND` | the settings' line keys |

The first three share `.gms .oct .prm .prp` and each rewrites offsets the others hold: they can only be run
one after another on the previous step's output, never merged by member. Talk and Bain share `.SND .LOC .WHD
_LS.SND` with each other and nothing with the first three.

### 5.2 The order

    graft + author  ->  wardrobe  ->  plates  ->  guns  ->  bots  ->  talk  ->  Bain

- wardrobe before bots: a bot's model is `Heroes!Hero_0N`'s root.
- guns before bots: tried here, passes. (The bots note proposes the other way round; not tried.)
- talk after the wardrobe (it reads the character numbers) and after anything that changes the blast timer.
  It refuses a second run on a build that already has `KLTalk/`.
- Bain last, built on the talk stream file.
- Stream file, one line of descent: installed base -> `kl_fa_talk.py stream` -> `kl_bain.py build --stream
  <the talk file>`. The result is `over_talk\PC_Def.str` (b0cb8bcd); it serves every earlier build, the talk
  builds and this one - not the three builds directly under `v_bain\`.

### 5.3 Tried (RAN, scratch folder only)

    kl_fa_bots_rt.py build <work>\build\rt_guns3\retomoto_ai3_guns  combo\1_bots
    kl_fa_talk.py   build combo\1_bots  combo\2_talk  --map retomoto
    kl_bain.py      build combo\2_talk  combo\x\3_bain  --stream <work>\build\v_talk\str\PC_Def.str

All three exit 0. The stream file the last step wrote has the sha1 of `over_talk\PC_Def.str`: the step is
repeatable and the existing file can be used. On `combo\x\3_bain`:

| check | result |
|---|---|
| `kl_fa_bots_rt.py check` | PASS, 0 FAIL; 7 bots, 303 squad nodes; jump list 7; places 7 |
| `kl_fa_talk.py check --str` | FAIL 0, NOTE 1 (the installed stream file is the old one) |
| `kl_bain.py check` | 0 problems |
| `kl_impact.py` | problems: 0 |
| `kl_fa.py check` | no finding (the source build's 'no bot squads' is gone) |
| `kl_chars.py check` | 1 problem, the known `Weapons/BombWindow_02` shader, same as the source build |
| `kl_map_guns.py check` | 1 problem: `KLGuns.ini` has no `Entries=` - the source build's own (4.2 b) |

Budget of the combined build against the owner's installed `rt_guns3\retomoto_ai3_guns`:

| | .prm | .ANM | .fxc | .WAV | chunks |
|---|---:|---:|---:|---:|---:|
| before | 79,879,056 | 21,642,904 | 17,760,648 | 27,158,864 | 65,330 |
| after | 79,879,056 | 21,642,904 | 17,760,648 | 27,802,960 | 65,330 of 69,632 |

.WAV +644,096 bytes, all of it Kane's 19 ADPCM lines held in memory (the form that is known to play). It
becomes +0 with `--adpcm stream` once a run has shown that streamed ADPCM is heard. Entities 25,736 -> 26,039.

The scratch build is in the session's temporary folder and is not a delivery; the three commands rebuild it
into the work folder.

## 6. Live checks, in order (the lead's; one new thing per run)

| # | what | set-up | proves it |
|---|---|---|---|
| C0 | the crew file is harmless at the menu | hook with both crew files wired, `[Crew] Random=0`; then `Random=1`; sit at the menu 60 s each, open the Arcade and Heister pages | no FATAL; with `Random=1` one `crew: on;` line and no other `crew:` line |
| R1-R3 | bots in the tower | `retomoto_bots_tower`, today's hook, `[Bots] Log=1` | picture at 'Heist starts in': seven on the balcony, none dead at GO; klbot: 7 AI records, stage 1, money |
| C1 | the game's swap on more actors | a `b_bots` map (not stock Subway: 1.3 a), `Random=1 DeadMen=0 Masks=0 Voice=0` | `crew: round draw 1 (session state NN ...` - note NN; seven `model a -> b ... it now has b`; picture |
| C2 | a Dead Men body on an actor | `DogDays=0 Outfits=0 Masks=0` | picture: drawn, walks, shoots; one shot dead, one boards |
| R4-R7 | the crew follows the jump | the full bots build, `[CrewJoin] Enable=1` | `join: player 0 entered box` then `crewjoin: ... (EARLY)` and one `now at` line per bot; picture in the lobby; stage 2, 3, aboard |
| T0 | the stream file is a clean superset | `over_talk\PC_Def.str` + the build installed now | clean exit; music and guards as before |
| B1 | Bain is heard | the combined build or `over_talk\retomoto_talk_bain`; call the van | by ear: a driver line in Bain's voice with the radio clicks, not noise |
| T1.. | talk | only after `kltalk` exists; `re\talk.md` 8 | its `talk:` lines |

## 7. Not established (in one place)

- The cause of the 14:24 menu crash.
- Everything of `klcrew.c` and `klcrew_rt.c` at run time: neither has run in the game.
- Who owns a line object handed to 0x421c70.
- Streamed single PCM as a spoken line (Bain), one-channel PCM sets with lip (Lynch), streamed ADPCM.
- The sound and wave pool limits above 4,967 / 4,816.
- Whether the bots survive the blast at 362 from the InvisiBomb.
