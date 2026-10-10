# Random AI heisters: a new crew every round, from both games' bodies

2026-10-10, agent v-crew. **Offline only**: the game was not started, nothing was installed, no build was
changed. New code: `klhook/klcrew.c` (hook side, off unless `[Crew] Random=1`). No tool was changed.
Words: **EXE** = read in kl2.exe build 0490 at the address given (`debug/dasm.py`, this session);
**MEASURED** = counted on this machine's files; **ASSUMPTION** = fits the evidence, not proven; **LIVE** = only
a run can settle it.

The owner (2026-10-10): *'can we get the AI to be randomly generated from the outfits from dead men and also
dog days so its not always the same models'*.

## 0. Short answers

1. **It can be done in the hook, with the game's own mechanism, and that is what is written.** The game itself
   changes an AI crew member's model (the body swap, slot 137) and its variant (the mask rule, slot 34) at run
   time; both pieces of code are, instruction for instruction, the bodies of the two routines `klchar.c`
   already calls for the player (`0x783fb0` is the model one, `0x88c810` the variant one). So
   `0x783fb0(actor, model)` and `0x88c810(actor, variant)` on a `ZFFActor` are not a new use (section 1).
2. **No data is needed and no file grows.** The bots take the models the wardrobe already put into the build
   (16 bodies, 24 Dead Men outfits, 8 or 12 masks; `KLWardrobe.ini`). .prm, .ANM, .fxc, .WAV: before = after
   (section 5). A build without a wardrobe still gets its own eight bodies shuffled.
3. **Per round**: a new draw for every new rules object and every time the session comes back from the score
   page. Never the body the player wears, never the one he chose on the Heister page, nobody twice.
4. **Voice**: one byte per bot (`rules + 0x33e + record index`) picks the recording. A Dog Days body speaks with
   its own voice; a Dead Men body gets a voice nobody else has. Data write, key `Voice` (section 2).
5. **Name** (round-start line-up, score page): a bot's name is a string of its own at `[[record] + 8]`, set by
   the game at registration from the digit in `Glazer_Bodyguard_0N` and again at the swap. The hook can set it
   with the game's own two calls (key `Names`, off by default). **Not established**: that the line-up and the
   score page read that string. Without the key 'Tommy' may wear Kane's suit.
6. **The build-side alternative** (a draw written by `kl_fa_bots` per build) was **not** implemented and
   `tools/kl_fa_bots.py` was not touched: it would be one fixed crew per build, not one per round, and it
   would break the game's own body swap, which finds a bot by the model of `Heroes!Hero_0N` (section 4).
7. **Retomoto**: the owner's build `<work>\build\rt_guns3\retomoto_ai3_guns` has a wardrobe (12 masks) but
   **no AI crew** (MEASURED: 0 `Glazer_Bodyguard` names in its .buf) - there is nobody to dress until the bots
   are built there. The four `<work>\build\b_bots\M0x` builds have both (7 bots, wardrobe with 8 masks).
8. Tested off the game only: `klcrew_test.c`, `RESULT: PASS (119 checks, 0 faults)`; the hook with the three
   wiring lines compiles in both configurations, no warning (section 6). **Nothing has run in the game.**

## 1. How a bot's look is set (EXE)

A crew record (`rules + 0x348` + i * 0x7c; in use when the byte `[rules+0x34c] + i` is 0; `klbot.c` section 1)
with mask 1 at `+0x79` is an AI member. `+4` = its actor (`ZFFActor`, vtable 0xbb3bac), `[actor+4]` = the scene
node, `[node+0x68]` = the **model** (chunk index of the level's .prm; `.prp` `ZGEOM[4]`), `[actor+0x50]` = the
**variant** (`.prp` `ZLNKOBJ[0]`). The two pieces of code below write `actor + 0x50` and ask for a refresh of the
node; what the renderer keeps in the node after that (a byte at `node + 0x158` was named in the job) was not read.

| what | where the game does it to an AI member | the same code as a routine |
|---|---|---|
| model | slot 137 `0x8f5e90`, after `0x783fb0(player, heroes[b])` at 0x8f5f03: loop over the records with mask 1 whose `[[actor+4]+0x68]` is that model (0x8f5f08..0x8f5f4e), then for that one, 0x8f5f63..0x8f5f97: `0x792290(node, the player's old model)`; `actor->vtable[0x1dc]()`; `[0x541960()]->vtable[0x70](node, 1)` | `0x783fb0(this, model)` = 0x783fb0..0x783fe2: `node = [this+4]`; `0x792290(node, model)`; `this->vtable[0x1dc]()`; `[0x541960()]->vtable[0x70](node, 1)` |
| variant | slot 34 `0x4b5b20` (option `UseMask`), 0x4b5c22..0x4b5c48, for every record with mask 1: `[actor+0x50] = 2`; `[0x541960()]->vtable[0x70]([actor+4], 1)` | `0x88c810(this, v)` = 0x88c810..0x88c82f: `[this+0x50] = v`; `[0x541960()]->vtable[0x70]([this+4], 1)` |

- `0x792290(node, model)`: `old = [node+0x68]; [node+0x68] = model;` and, when there was an old one and the
  node is drawn (`word [node+0x58]`), the renderer `[[0xdd2640]+0x970]->vtable[0x130](node, old)`. Five callers,
  among them a light (0x4b934a) and a generic one (0x8cb22a): it is a routine of the node, not of a player.
- Vtable slot 0x1dc / 4 = 119 is **0x417a60 in both classes** (`ZFFActor` 0xbb3bac and `ZFFPlayer` 0xbb45f4):
  it sizes the bone arrays from the new model. `0x541960()` = `[[[0xdd2640]+0x970]+0xfc]`, the object whose
  slot 28 refreshes a node.
- `0x783fb0` has two callers: slot 137 and the online routine 0x74ee10. `0x88c810` has three: slot 34 twice
  and the online mask routine 0x822830. All pass a player - the AI member is handled inline with the same
  instructions, which is why the routines may be called with an actor.
- **When** the game does it: slot 137 is called from three places (0x42df3b, 0x4d10ae, 0x75632b), each
  `if [session+0x5c] == 4 and the rules object exists`, each in a routine that has just entered a player in
  the session (0x7a2540, 0x71e830); two are slots of session-handler vtables (0xbd1cb8; 0xbd2560 / 0xbd2700 /
  0xbd2890). ASSUMPTION: 'the player's object has joined', once per level start; the caller chain up to the
  session state (0x15 -> 0x16) was not traced. The hook does not depend on it: it acts when rules, player,
  the eight heister-table entries and the set of AI records have stood still for `Settle` ms (600; klchar.c's
  own wait is 300, so the player's swap comes first), in any session state 0x12..0x19, and says the state in
  its `round draw` line - **the first live run shows which state it is** (wanted: 0x15 / 0x16, before the
  line-up; if it is 0x19 the bots change clothes in view and Settle has to come down).
- **A Dead Men model on a bot's animation set**: a skeleton is bound to the level's .ANM by bone NAME, not to
  an animation set (`tools/kl_chars.py`, docstring 'THE SKELETON IS BAKED AGAINST THE LEVEL'S .ANM'), the
  wardrobe rebound the Dead Men roots when it was built, and stock already moves a model of set `Kane` /
  `Lynch` (the human's) onto an actor of set `Kane_NPC` / `Lynch_NPC`. Seen live for the player only (runs
  W5 / W6). LIVE for an actor.

## 2. Voice and name (EXE)

- **Voice.** `ZGameRulesHeist` slot 198 (0x588980), registration of an AI member: record index `ebx`
  (the same register indexes the in-use byte and the record, 0x588a0e..0x588a23), byte =
  `group name[0x12] - '1'` (0x5889d1), stored at `rules + 0x33e + ebx` (0x5889e2). That byte is the entry
  `K_C<byte+1>` of every per-character line (`re/bots_voice.md` 1.2 / 1.3: no other reader). Slot 137 exchanges
  the human's byte (index 0) with that of the bot whose body he takes (0x8f5fbf..0x8f5fce).
  `klcrew.c`, key `Voice=1`: the player's byte stays; a bot in a Dog Days body gets `character - 1` unless
  somebody has it; everybody else the lowest index nobody has. Eight indices, eight crew members, each once;
  only values 0..7 are written (an index above 9 is the int3 at 0x51ab2d). Which voice a Dead Men body gets is
  arbitrary - Dead Men has no Fragile Alliance voice of Kane, Lynch or the six (`re/bots_voice.md` 0.6).
- **Name.** The same routine goes on: `0x478df0(byte)` returns the LOCALISED text of
  `/AllLevels/Interface/FACharacters/C1..C9` (0x47d8c0: the .LOC lookup; a key that begins with '%' is
  returned as its own text); `0x83e2e0(&tmp, text)` builds a 12-byte string `{begin, end, capacity}` on the
  game's heap (0x770520); `0x469250(block, tmp by value)` with `block = [record+0]` formats it with `"%s"`
  (0xb80444) into the string at `block + 8` (0x694bc0) and frees `tmp` (0x6ad680). Slot 137 does the same with
  character 0 for the bot that gets the human's old body (0x8f5f99..0x8f5fba). `block[0]` = 1 'not local',
  `block[1]` = the record index.
  `klcrew.c`, key `Names=1` (default 0): `0x83e2e0` + `0x469250` with the character's `Name=` of
  KLWardrobe.ini ('Tommy', 'Kane', 'Ashkanan' ...), when the string at `block + 8` is another one, at most
  twice per bot and round. English as written: Dog Days' .LOC has no text for the Dead Men names.
  **Not established: who reads `block + 8`** (the line-up, the score page, the kill feed) - no reader was
  looked for. That it is the name is by what the game writes there, twice.
- The heister table `rules + 0x208` (the eight models slot 137 hands the player) is klchar.c's and is not
  written here.

## 3. `klhook/klcrew.c`

Keys `[Crew]` (all in the file's top comment): `Random=0|1`, `Seed` (0 = new each start, logged), weights
`DogDays=1` `DeadMen=1` (per character of that game; 0 = none), `Include=9,10` (always in the crew when free;
9 = Kane, 10 = Lynch), `Outfits=1`, `Masks=0|1|2` + `MaskChance=50`, `PaydayMasks=1`, `Voice=1`, `Names=0`,
`Settle=600`, `Tries=3`, `Log=1`.

- **Characters** = klchar.c's copy of the level's `KLWardrobe.ini` (read under its lock; needs
  `[Character] Enable=1`, which is what makes klchar.c read the file). Without one: the eight models of the
  heister table, variants 1 / 2.
- **Draw**: excluded = the character whose model the player wears + `[Character] Char`; then `Include`, then
  weighted draws without replacement, then a shuffle over the bots; per bot outfit 0 .. Bodies * Heads - 1 and
  a mask (one of the build's, or the own face); variant = klchar.c's `klc_variant` (the formula
  `kl_chars.variant_of`). A bot that is aboard or dead at the draw, and one for whom no character is left,
  keeps his body. Our own xorshift generator, seeded `Seed ^ draw number`.
- **Hold**, every tick, for each AI record in play (status byte `+0x10` == 0):

  | condition | action | where |
  |---|---|---|
  | the drawn body is now the player's | that bot is drawn again from the free characters | - |
  | `[node+0x68]` != the drawn root | `0x783fb0(actor, root)` | game thread, <= `Tries` a round |
  | `[actor+0x50]` != the drawn variant | `0x88c810(actor, variant)` | game thread, <= 64 a round (slot 34 sets 2 again whenever it runs) |
  | `rules+0x33e+i` != the voice | one byte | heap data, any thread |
  | name at `[[record]+8]` != the character's | `0x83e2e0`, `0x469250` | game thread, <= 2; `Names=1` |

- **Guards**: Arcade (`[session+0x5c] == 4`), rules vtable 0xbd3514, the actor's vtable 0xbb3bac (another one:
  that member is left alone, said once), the first 14 / 12 / 10 bytes of 0x783fb0 / 0x792290 / 0x88c810 and
  slot 119 of the actor vtable = 0x417a60 (else nothing is changed, said once), 15 / 12 bytes of the two name
  routines (else the names stay). Calls only on the game's thread (the SteamAPI_RunCallbacks tick).
- **Policy** (klhook.c top comment): heap data and calls of game functions from the game's thread; no import
  slot, no code byte. Looks, voices and names only - no rule of the round changes - so, like klchar.c, it is
  not tied to klsteam.c's level verdict.
- **For the other hook parts** (Kane / Lynch dialogue, the Retomoto countdown): `klw_crew_char(record index)`
  and `klw_player_char()` give the character number (1..16 as KLChar, 0 = not known) after a draw;
  `Include=9,10` makes 'Kane and Lynch in the same match' certain when the player is neither or one of them.

**The lead's lines in `klhook/klhook.c`** (compiled that way, section 6):

    #include "klcrew.c"          /* after  #include "klchar.c" */
    klw_tick(game_thread);       /* in klh_tick, after  klc_tick(game_thread); */
    klw_init();                  /* in DllMain, after  klc_init(); */

plus a row `klcrew.c  x  x  random AI heisters ([Crew])` in the file table of the top comment, and in
`klhook/KLHook.ini`:

    [Crew]
    ; RANDOM AI HEISTERS: each round the bots are a new draw from the level's wardrobe (KLWardrobe.ini)
    Random=0
    ;Seed=0
    ;DogDays=1
    ;DeadMen=1
    ;Include=9,10
    ;Outfits=1
    ;Masks=1
    ;MaskChance=50
    ;PaydayMasks=1
    ;Voice=1
    ;Names=0

## 4. The build-side alternative, and why it was not taken

`kl_fa_bots.py` could write a seeded draw per build: each bot's `.prp ZGEOM[4]` and `.gms` record `+0x0c` =
a wardrobe root, `ZLNKOBJ[0]` = a variant. Not implemented, `tools/kl_fa_bots.py` unchanged, because:

- it is one crew per BUILD - the owner asked for 'not always the same models';
- stock binds a bot to `Heroes!Hero_0N` by MODEL: slot 137 looks for the bot that wears the model the human
  is given (0x8f5f4b). With other models in the files the human can get the body a bot of the draw also
  wears (two of the same in one round) unless the draw avoids all eight Dog Days roots;
- `kl_fa_bots check` rule 2 ('each bot's model = `Heroes!Hero_0N\Ground`'s') would have to go.

It stays the fallback **if live check C2 shows that a model set on an actor after the level start is not
drawn right**: then `--crew-seed N` in `kl_fa_bots` (Dead Men roots only, variant by `kl_chars.variant_of`)
gives a fixed mixed crew per build without any call. To be written only then.

## 5. Budget

`klcrew.c` adds no data. MEASURED (`python tools/kl_fa_bots.py sizes`), before = after:

| build | .prm | .ANM | .fxc | .WAV |
|---|---:|---:|---:|---:|
| `rt_guns3\retomoto_ai3_guns` (owner's Retomoto, no AI crew) | 79,879,056 | 21,642,904 | 17,760,648 | 27,158,864 |
| `b_bots\M01` | 55,088,000 | 22,061,764 | 17,760,648 | 21,722,704 |
| `b_bots\M02` | 54,619,216 | 22,202,472 | 17,760,648 | 22,527,568 |
| `b_bots\M03` | 60,469,040 | 22,202,616 | 17,760,648 | 22,716,752 |
| `b_bots\M06` | 49,585,744 | 21,642,576 | 17,760,648 | 21,775,744 |

.WAV growth: 0 bytes (no sound is added; the voice is a table byte). Chunk table: unchanged.
Run-time cost, **not measured**: a Dead Men wardrobe root has 1,080 - 1,608 mesh objects
(`re/wardrobe.md` 7; a stock heister 21 - 24); up to seven such roots are drawn at once instead of one. LIVE (C3).

## 6. Off-game test (run 2026-10-10)

`klcrew_test.c` (session scratchpad `crew\`; `klchar.c` and `klcrew.c` included as they are; a made-up
session, rules object, eight crew records, actors and nodes in the test's own memory; the four routines are
stubs that begin with the real first bytes; the real `KLWardrobe.ini` of `b_bots\M01` (8 masks) and of
`rt_guns3\retomoto_ai3_guns` (12 masks)). `RESULT: PASS (119 checks, 0 faults)`:

- T1 a valid crew (seven different bodies of the list, none the player's, voice table a permutation, a Dog
  Days body with its own voice), <= 7 model calls, none after the draw is in place, nothing on the first tick;
- T2 a variant set back to 2 is put right at the next tick; T3 the player takes a bot's body: that bot is
  drawn again; T4 score page and back: draw 2;
- T5 off the game's thread: no call; T6 `Include=9,10` with the player as Kane: Lynch once, Kane never;
- T7 400 draws with `Char=10` chosen but J.C. worn: neither body is ever given to a bot;
- T8 `DeadMen=0` -> Dog Days bodies only, `DogDays=0` -> seven Dead Men bodies; 3,000 draws at 1 : 1: each of
  the 15 free characters 1,352 - 1,440 times (1,400 expected);
- T9 `Names=1`: seven renames through the two routines, none repeated; T10 other code bytes: no call;
- T11 an actor of another class, a bot aboard, a dead one: untouched, and not in the draw;
- T12 a level without wardrobe: the stock bodies shuffled, variants 1 / 2; T13 not Arcade / other rules
  class / `Random=0`: nothing;
- T14 the 12-mask wardrobe, 1,500 draws: highest variant 128, every mask 1..12 and every outfit 0..23 drawn.

Compile: `klhook.c` with the three lines of section 3 (a scratch copy; the repository's file is unchanged)
builds as SHIP and as TEST (`cl /O2 /LD /W3`), no warning.
This proves the file's own logic and its calling conventions against stubs. It proves nothing about the game.

## 7. Live checks (the lead's; in this order, one new thing per run)

Build: a `b_bots` map (M01 has run with bots). Hook with the three lines, `[Character] Enable=1`,
`[Bots] Enable=1 Log=1` (its `record N appears: bot ... actor's vtable 00bb3bac` line is check K1 and is what
this file requires too). Steam write guard on; do not Quit inside a session.

| | setting | must be in KLHook.log | must be seen |
|---|---|---|---|
| C0 | `Random=0` | no `crew:` line | the round as before (the include changes nothing) |
| C1 | `Random=1 DeadMen=0 Masks=0 Voice=0` | `crew: on; ...`, `crew: round draw 1 (session state NN, ... 7 AI members, wardrobe of ...)` - **note NN**; seven `crew: bot N is <Dog Days name>, outfit 0, mask 0`; `crew: bot N (actor ...): model a -> b through the game's own routine (try 1): it now has b` | picture at the line-up: the seven in each other's bodies, nobody twice, nobody in the player's; they walk, shoot, board. This is the game's own swap done to more actors: the smallest step |
| C2 | `DeadMen=1 DogDays=0 Outfits=0 Masks=0` | `bot N is Kane / Lynch / Ashkanan ...`, `... it now has <Dead Men root>` | **a Dead Men body on an actor**: drawn, animated (walk, run, cover, shoot), money bag on the back; then one shot dead (ragdoll) and one boarding. If a body is invisible, T-posed or the game faults: section 4's fallback |
| C3 | `DogDays=1 DeadMen=1 Outfits=1 Masks=1` | `crew: bot N look: variant 1 -> v` | mixed crew, vests / armour, borrowed masks; frame rate against C1 (seven large roots) |
| C4 | `Masks=2`, the game's 'Criminal Masks' option ON, then OFF | no `set it back 64 times` line | all seven masked either way |
| C5 | `[Character] Char=9` (Kane) and `Include=9,10` | `the player is Kane` (or a `drawn again` line right after klchar's `body:` line), one `bot N is Lynch`, no `bot N is Kane` | Kane in the hands, Lynch in the crew, no second Kane |
| C6 | `Voice=1`, a round with a backstab reply / jackpot / bribe line | `crew: bot N speaks as C<m> (voice table entry N: a -> b)` | by ear: a bot in Tommy's body has Tommy's voice; no int3 at 0x51ab2d |
| C7 | `Names=1` | `crew: bot N is now called '<name>' (was '<name>')` | line-up and score page: do they show the new names? If they show the old ones the string is not the one read: leave `Names=0` |
| C8 | a second round in the same session | `crew: round draw 2 (...)` with other bodies | new crew; and after quit to the menu and a second load: `round draw` again, no fault |

Stock Subway (no wardrobe) can stand in for C1: `NO wardrobe, the stock bodies of f01\f01_main`.

## 8. ASSUMPTIONS and what is not established

- That a model may be set on an actor at the hook's moment (after the level start), and more than once a
  level: the game does it once, at the player's join. Seen live for the player only.
- That a 1,080 - 1,608-object root is fine on an actor and on seven at once (frame rate, the renderer's
  per-mesh objects, the shadow pass).
- That no session state outside 0x12..0x19 occurs inside a round (a state >= 0x1f and back makes a new draw:
  the bots would change in view) and which state the first draw falls in.
- What a boarded or dead bot's actor is afterwards: the hook does not touch a record whose status is not 0.
- Whether the rules object and the actors are the same objects in round 2 (the hook handles both).
- Who reads the name string; whether the name is drawn from it again after the line-up.
- The three callers of slot 137 were read only as far as 'a player was entered in the session'.
- Ragdoll, cover and hit reactions of a Dead Men body on an actor (`kl_impact` was not re-run on the builds here).
- `.prp` `ZGEOM[4]` / `.gms +0x0c` of a bot stay `Hero_0N`'s: only the running objects change.
