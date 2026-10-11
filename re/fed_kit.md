# The fed's kit: he may hunt, the crosshair is the right way round, the map's body, an AK sometimes

Track M, 2026-10-11. Files: `klhook/klfedkit.c` (new hook part, NOT wired: three lines in section 6),
`tools/kl_fa_fedbody.py` (new), the `[Fed]` block at the end of `klhook/KLHook.ini`, side files in
`<work>\build\z_fedbody\`. kl2.exe build 0490, read with `debug\dasm.py`. **NOTHING HERE HAS RUN IN THE GAME.**
EXE = read in the disassembly; LOG = the owner's / the test runs' `KLHook.log`; FILE = level data.
Second version, after the adversarial review `re\fed_kit_review.md` (ACCEPT WITH FIXES): section 9 says what was
done about each of its points. **Section 10 (track S, 2026-10-11 afternoon): a fed is only a fed - no traitor mark,
his kills pay, the HUD's two blocks on one place; keys `NoTraitor`, `Pay`, `PayKill`, `HudFade`. NOT RUN either.**

**FOR THE LEAD BEFORE WIRING (review MUST 1):** the owner's `KLHook.ini` already has `[Fed] Enable=1 Player=1`, and
`Hunt` and `Crosshair` default to 1 under exactly those two - the moment a hook with this part is installed for him
both bytes are written in his game. Nothing of it has run. Either run K0 and K1 (section 7) before that hook goes
to him, or give his ini `Kit=0` with it. **And tell him the crosshair fix is a hypothesis** (section 2): K0 decides.

The owner, after playing the fed on the park: 'if you die too early you cant kill itll just say you cant kill before
you heist like before the money is picked up they still on green crosshairs to indicate friendly when in reality it
should be red and the enemies are the inverse of that. make sure to use a model thats correct for the map so i was
normal swat but i should be the yakuza biker outfit and then on withdrawal normal swat etc. and make it so u have a
chance to come back with an ak 47 instead of only just having the mp5'.

## 0. Summary

| what he saw | cause (EXE) | answer | kind | default |
|---|---|---|---|---|
| 'you can't kill before you heist' | `ZFFActor` slot 422 (0x8689c0) drops a human's hit on a crew NPC while rules byte `+0x285` ('the looting has started') is 0; the attacker's police byte is not asked | `[rules+0x285] = 1` while he is a fed | one heap byte | `Hunt=1` |
| crew green, police red | `ZCrossHairDisplay` slot 5 (0x8e9720) gives a police human the CREW's colours when rules byte `+0x283` (Undercover Cop mode) is not 0; `ZGameRulesHeist` never initialises that byte | `[rules+0x283] = 0` while he is a fed | one heap byte | `Crosshair=1` |
| 'normal swat' on the park | all eight police player objects wear model 1919 (F07's SWAT) | the game's model routine 0x783fb0 with the root the level's `KLJoin.ini [FedBody]` names | game call, once per fed | `Body=0` |
| only 'the mp5' | the respawn calls the loadout routine 0x410710 with shop rows 0 and 0x1c = M-77B + Zastava M85 (which wears the MP5 look on the owner's builds) | the same routine again with the AK's row, by chance | game call, once per fed | `AkChance=0` |

Sections 1 and 2 are on with `[Fed] Player=1` because they are two bytes of one heap object, written only while the
local player IS a police human in a running Arcade round of a level that is not stock (a state only klfed.c makes),
to values the game's own code writes there (1 at the first loot; 0 in every Fragile Alliance class outside the
Undercover Cop mode). Sections 3 and 4 call game routines and stay off until their key is set.

## 1. 'No friendly fire until the looting has started' (EXE)

- The text: `.LOC` key `AllLevels/Interface/Online/FA_NoFriendlyFire` = 'No friendly fire until the looting has
  started' (string 0xb714d8; two users: 0x6fff15 in `ZGameRulesFragileAlliance` slot 121 - the multiplayer classes,
  Heist has its own slot 121 - and **0x868b7b**).
- **0x8689c0 = `ZFFActor` vtable slot 422** (0xbb4244; slot 423 is the damage routine 0x61a980 of re\balance.md). It
  is the first thing a hit on an NPC meets; its last act (0x868dbf .. 0x868dcd) sends the hit record to the actor as a
  message - which is what reaches the damage. Every early exit jumps to 0x868dcf, past that.
  - 0x868a88 Arcade (`[session+0x5c] == 4`); 0x868a93 the victim's team `[[actor+0x54]+4]`:
  - **team 2 (crew) or 0** -> 0x868b11: rules = 0x7bb2a0 (the Arcade rules), attacker `[hit+0]` a `ZFFPlayer`
    (0x7aace0), **rules slot 189 (vtable +0x2f4 = 0x4ee010: `mov al, [ecx+0x285] / ret`) == 0** -> the HUD text above
    (0x868b7b .. 0x868bb1) and the hit is dropped (0x868bdf / 0x868c07). No test of `[player+0x2723]`.
  - any other team -> 0x868aa2: attacker a `ZFFPlayer`, dword `[0xce8a44]` (1 in the file) not 0, attacker police
    and not a dirty cop (`+0x2729`) -> dropped. (The damage routine has the same test again, 0x61ab34 .. 0x61ab6b.)
    So a fed cannot hurt the police AI, with no text.
- **`[rules+0x285]`**: set by 0x5cac90 (callers 0x6bbd78, 0x7ceb4f, 0x881996 - the loot paths) at 0x5cacd2, once;
  then, outside the Undercover Cop mode and unless the local client is police (slot 107) or has flag 0x80 (slot 110),
  the announcement 'Looting_Started' (0x6b3550). Cleared by Heist's slot 7 at 0x74bd92 (round reset) and slot 4
  (0x51be38). Readers besides slot 189's callers above: `ZBoardEscapeVehicleTactic` slot 3 (0x5478e0: sets
  actor+0x8f1 and goes on only when it is set), and three routines with a PLAYER as victim (0x612c20 at 0x612ea4,
  0x78f5d0 at 0x78f67b, 0x6e3400 at 0x6e3599), each of which leaves the test out for a police victim.
  One more WRITER: rules slot 190 = 0x8f3930 (`mov [ecx+0x285], al / ret 4`), a plain setter with no direct caller
  (virtual; its caller was not found). More readers, all OUT of Arcade's reach: 0x425651 (0x425320 = slot 15 of the
  Fragile Alliance classes - Heist's slot 15 is 0x4c25b0), 0x6ffe3f / 0x700127 (their slot 121; Heist's is `ret 0xc`).
- LOG, the owner's round on the park: `12:43:44 fed: round 9`, dead `12:43:59`, `12:44:04 YOU ARE A FED`, the bot line
  shows every record `g0 $0`, at 12:45:24 still `g1 $0` for all seven, `12:45:26 dead for good`. Nobody had looted in
  the 82 s he was a fed: the byte was 0 throughout.

**The write** (`Hunt=1`): while he is a fed in play and the byte is 0: 1. Lost: the 'Looting started' line at the
first loot (a police client is not shown it anyway) and the boarding tactic's wait for the first loot (a bot has
heist stage 3 only after the loot place; no case found where it matters).

## 2. The crosshair (EXE)

`ZCrossHairDisplay` (vtable 0xbbdc14) slot 5 = 0x8e9720. Colours: red `[0xbbe498]` = ffcc0000, green `[0xbbe49c]` =
ff22ff22, white `[0xbbe490]`. Arcade branch 0x8e9dc6, target an NPC (0x4ea3b0), team = `[[target+0x54]+4]`:

```
8e9dfc  player = [display+0x10];  police (+0x2723) or dirty cop (+0x2729) ?
8e9e1a      rules slot 186 (vtable +0x2e8 = 0x4c0630: mov al,[ecx+0x283] / ret) == 0 ?
8e9e2c          team 1, 4, 3 -> GREEN ; else RED (the crew, team 2, and team 0)          the cop's view
8e9e4a  otherwise (a criminal - or slot 186 not 0):
            a traitor player: team 3 green, else red
            else team 2 / 0 / 3 and the target no traitor (slot 108) -> GREEN ; else RED  the crew's view
```

So a police human gets the crew's view exactly when `[rules+0x283]` is not 0. That byte and `+0x284` are the
Undercover Cop mode's (slot 187 = 0x74d9f0 sets both; one caller, the network handler 0x418b20; other readers
0x4ae1b9, 0x6ffe71, 0x6fffba, 0x8429d0 ...). `ZGameRulesFragileAlliance` slot 4 (0x708500) clears `+0x282 .. +0x285`.
**`ZGameRulesHeist` slot 4 (0x51bbe0) clears `+0x282` and `+0x285` only, and the constructors (0x835480 -> 0x7de590)
write `+0x281` only**: in Arcade `+0x283` is what the 0xf30-byte heap block held (allocated at 0x725d86).
ASSUMPTION (fits the code and the owner's picture; not proven - no dump of ours holds that object): it was not 0 in
his rounds. The hook's first line of every fed prints the byte. If it prints 0 and the colours are still the crew's,
the other candidate is `[display+0x10]` still naming the dead heister object (set by the display's slot 1, 0x83ab00;
not followed) - then `Crosshair` does nothing and that pointer is the next thing to read.

**THE CAUSE IS NOT PROVEN.** For it speaks that the multiplayer classes clear the byte and Heist does not. Against
it stands a real second candidate: `[display+0x10]` is a pointer the display's slot 1 (0x83ab00) stores ONCE from
`gamedata[0x828 + 4 * index]`, and the respawn changes only the index byte (0x537700) - a display still holding the
dead heister object would show the crew's colours with `+0x283 == 0` too. K0 decides: the hook's `YOU ARE A FED`
line prints the byte; **0 there = `Crosshair` writes nothing and the complaint stands** (next: that pointer).

**The write** (`Crosshair=1`): while he is a fed in play and the byte is not 0: 0. **Put back**: when a heister is
in play again on the same rules object and the byte is still the hook's 0, the value the hook found is written back
(`fedkit: crosshair: [rules+0x283] put back to N`), so a round without a fed runs with what the game had.

**Every reader of `[rules+0x283]`** (all instructions with that displacement on a rules object; class by vtable):

| reader | whose | in Arcade? | with 0 |
|---|---|---|---|
| slot 186 = 0x4c0630 (the getter) | all rules classes | yes | the crosshair above |
| 0x4ae1b9 (0x4ae130, the kill line) | free routine | yes, only for a client with flag 0x80 | the ordinary line |
| 0x8429d0 ('all dead' announcement) | free routine | yes | the ordinary text |
| **0x4569bf (0x4569b0)** | free routine; callers 0x7ceb48 (the FIRST-LOOT path, right before 0x5cac90), Sv slot 16, 0x794190 | **yes** | with `+0x282 == 0` too: sets `[rules+0x282] = 1`, calls slots 132 and 78, then 0x471d10 on `[session+0x84]` (sends only with a network session and `[session+0x15d]`) |
| 0x4254fa | 0x425320 = slot 15 of the Fragile Alliance classes | no: Heist's slot 15 is 0x4c25b0 (the review named it Heist's own - it is not) | - |
| 0x6ffe71, 0x6fffba | their slot 121 | no: Heist's is `ret 0xc` | - |
| 0x5df2eb | the server class's slot 128 | no: Heist's is `ret 0x10` | - |
| 0x68109e, 0x6811c7, 0x5e22ea | the server class's slot 192 (0x680f90) and its only callee 0x5e2230 | no: Heist's is 0x5dff40 | - |
| 0x4eb337, 0x4eb492 (0x4eb260) | called from the client class's slot 11 and 0x794190 (only the server class's slot 11 calls it) | no | - |

So the one real difference the write makes besides the crosshair: at the round's first loot after it, 0x4569b0
sets `[rules+0x282]` (cleared by Heist's slot 4 at 0x51be32; read in Arcade only through the getter slot 184,
0x7b9ad0). That is the path every Arcade round takes whose heap byte happened to be 0. No harm found.

**What a police human needs, in one place**: `[rules+0x285] = 1` and `[rules+0x283] = 0`. Then every AI heister in
play is red and can be hurt from the tick after the respawn; the police AI is green and cannot be hurt
(`[0xce8a44]`, his `+0x2729` = 0 - both left alone). **Do the police shoot him?** No by the code
(`ZSoldier` slot 111, 0x8824e7: a police player is a target for team-2 soldiers only). LOG, the one piece of
evidence: in FD3_DM03_die the fed lived the 145 s to the end of the run with a maximum health of 27.5 under
police -> you x 20, in the bank where the same player as a criminal was dead 25 s after the round began (those logs
print no line per hit on the player, so there is nothing finer). The owner's fed on the park was killed 82 s after his
respawn - by the code, by the crew, whom he could not shoot back at.

## 3. The body of the map

### 3.1 Can a police player object wear another model? (EXE)

- A model is `[[entity+4]+0x68]`; the game changes it with **0x783fb0(entity, model)** = 0x792290(node, model) ->
  the entity's vtable slot 119 (`ZFFPlayer`: 0x417a60, the same routine as `ZFFActor`: bone arrays from the model)
  -> renderer notify (`[0x541960()]` slot 28). Read whole for klchar.c / klcrew.c, and it has RUN in both forms: on
  the heister `ZFFPlayer` through rules slot 137 (0x8f5e90 calls it at 0x8f5f03; Dead Men heroes on the player) and
  directly on `ZFFActor` (klcrew.c).
- Slot 137 refuses a policeman (0x8f5eb0) - it deals in the eight-hero table. Nothing in 0x783fb0 / 0x792290 /
  0x417a60 asks what kind of person it is. Rules slot 34 (0x4b5b20: masks, looks) returns at once for type 3
  (0x4b5b4f): nothing sets a look back.
- Skeleton: game code finds a person's bones by id through the model's own table (re\characters_graft.md 3.2); the
  tool checks that the chosen model has every id that code passes (pelvis .. head, limbs, both hand attachers =
  the weapon, spine / hip / head attacher). All five maps' choices have them. Missing everywhere: **`free_bone01`
  (id 0x21)**, as in every Dead Men model: its three readers (0x42f900, 0x7db520, 0x5f2c66) go on with unset
  vectors in a two-person action (re\characters_graft.md 3.4). Repair if it shows: `kl_chars.alias_free_bone` on
  that skeleton as a build step (one byte of table 5; NOT done - this tool writes no `.prm`).
- Animation: the map's models were rebound to the joined `.ANM` by kl_graft (`kl_chars.check_bones` = [] for all
  three); the police player's set is `Lynch`, the models' own actors use `Mercenary_04` / `Army`. ASSUMPTION: as the
  heroes' sets move Dead Men heroes. The bikers have 76 bones (no face: a helmet); the stock body has 104.

### 3.2 Per map (FILE; `python tools/kl_fa_fedbody.py survey <build>`)

| map (tab build) | the fed wears | model | looks | why |
|---|---|---|---|---|
| A Walk in the Park (`z_route\M06`) | the Japanese drug squads' bikers: `Biker_Red` / `Biker_BlackWhite` / `Biker_Yellow` + `Biker_Visor_01` | 36028 (6 actors) | 1, 3, 4 (the three the map's actors wear), one by chance | the owner asked for exactly this; the map has no police |
| Retomoto Tower (`z_rooms\retomoto_full`) | the Japanese SWAT of the street (`SWAT_Beam..`) | 52003 (6 actors) | 1 | a fed is police; the tower's own men are the yakuza's suits. Others: `--body jpn_police` (52248, street police), `--body c_henchmen` (63085, the guards) |
| Hot Coffee (`z_route3\M01`) | its FBI agents (`FBI-Agents_0n`) | 35968 (10 actors) | 1 .. 8 | the map's law; Dead Men's own respawn body was an FBI agent |
| Withdrawal (`z_cover3\M03`) | stock SWAT | 1919 | - | the owner: 'on withdrawal normal swat'. The map's own Dead Men SWAT: `--body reinforcement` (59891) |
| Late Night Opening (`z_loot3\M02`) | stock SWAT | 1919 | - | as the bank. The map's own: `--body policeswats` (56597) |

Model numbers are chunk indices of THAT build's `.prm`: the section carries `Entries=` (the `.prm`'s chunk count)
and the hook refuses it for any other file, as klgun.c does. Every model is already in its build: the step adds one
side-file section and nothing else. Pictures: `<work>\build\z_fedbody\<map>\fedbody.png` (M01, M06, retomoto_full).

### 3.3 What the hook does (`Body=1`)

Once per fed, `KitSettle` ms after it first saw him, game thread: section for this level and this `.prm`, no loader
running, chunk `Root` is a model root with a skeleton, the three routines' first bytes and `ZFFPlayer` slot 119 as
known -> `0x783fb0(player, Root)`, read back; next pass `0x88c810(player, variant)` with one of `Variants=`.
`Root=0` = the stock body stays. A section whose `Root=` is not below its `Entries=` is refused (a table slot at or
above the loaded count may hold what a former, larger level left).

**`Entries=` is a chunk COUNT, not an identity.** The five sections are for today's tab builds; tracks K and L are
replacing Retomoto's. Run `kl_fa_fedbody.py apply` LAST on each final build (the other sections of `KLJoin.ini` are
kept) and `check` again. **`--link` folders share every other file with their source build** (hard links, link
count 2): make the tree from them, never run a step that rewrites a file in place inside `z_fedbody\<map>` - it
would change the tab's source build silently (`check` now prints a NOTE with the number of shared files).

## 4. An AK sometimes

### 4.1 Where the fed's guns come from (EXE; settles re\fed_respawn.md 2.4 'not established')

- The respawn 0x4b28d0 calls **0x4b6680(weapons = `[0x168e96c]`, player, 0, -1)** at 0x4b2a19 (the client routine
  0x63a0a0 does too, 0x63a2d9). Its jump table 0x4b66e0 sends kind 0 to 0x4b66ca:
  **0x410710(weapons, player, pistol row 0, rifle row 0x1c, armour row 0)**; kinds 1 .. 3 are rows 0xd / 0xe / 0xf.
- 0x410710 (callers also 0x42bd3c, 0x4d104d, 0x74ac22, 0x892dc3) = the loadout: gate 0x8df480; in Arcade rules slot
  34 for the player; removes what he holds (4 slots x 2: 0x80dc00 / 0x417bc0 / 0x633250); gives the two rows through
  0x538ec0(weapons, player, item, ammunition); health = 0x7ec510() + `[armour * 8 + 0xbd22c8]` (0x644310).
- **The shop table is at 0xbd1f68**: 36 rows of 24 bytes `{item, ammunition, price, rank, tier, DLC}` (kl_guns.py
  has the start 8 bytes late). Row 0 = item 6 `HG_M-77B`, 150; **row 0x1c = item 29 `Rifle_Zastavam85`, 300** - the
  150 / 300 of the fed's ammo panel in the PT_DM03_die_r2 pictures. On the owner's builds `KLGuns.ini` shows the
  MP5 look on the Zastava: 'the mp5'. **Row 29 = item 31 `Rifle_AK47`, 250; row 30 = item 32 `Rifle_AK74`, 250.**
- **The pool.** 0x538ec0 takes a weapon object from a pool: `[weapons+0]` -> `{+4 count, +0x10 entries}` of 12
  bytes `{object, item, byte +8 'not handed out since the last reset', byte +9 'lies dropped'}`; 0x55bee0 wants
  the item, no owner (`[object+0x5c]`), `+9 == 0`, `+8 != 0`; 0x538f30 then clears `+8`. None free: 0x53abc0 takes
  the one that has LAIN DROPPED the longest from `[weapons+0xb4]` (`{object, item, time}`; filled by 0x6853e0,
  which sets `+9`: a player dying with the gun, 0x7be32b / 0x7be35f, or throwing an empty one away, 0x47f950; a
  pick-up takes it out again, 0x829960); none there either: **`int3` 0x538f02**.
  - Made by **0x78a8d0** (session handler slot 6: 0x766ed2 SP, 0x5230a2 MP; Arcade only): for EVERY row of the
    shop table whose item has a template in the level (`[[gamedata+0x15b0] + 4 * item]`, 0x5d2f50) **8 objects, 16
    of items 6 and 29** (the fed's pistol and Zastava; 12 of everything when `[0x168e59c] == 2`). No test of the
    row's DLC or rank: the AK-47 (row 29: DLC = 1, rank -1) and the AK-74 get their 8 like any other gun.
  - Emptied by 0x5cae10 (handler slot 8). **Reset by 0x42d9a0** (every entry `+8 = 1`, `+9 = 0`, dropped list
    emptied), called from 0x874a90 (0x874b58), which Heist's slot 7 calls at 0x74bd6a - the round-reset case that
    also clears `[rules+0x285]` (0x74bd92).
- FILE: every tab build has the templates `Rifle_AK47` and `Rifle_AK74` (the host's equipment tree; the tool's
  check FAILs without) and the police player's set `Lynch` has their handling clips (50 / 57). With the builder
  above that means **8 AK-47 and 8 AK-74 objects on every tab map** (EXE + FILE; the hook still counts at run time).
- **The removal half of the loadout, 0x633250(player, weapon)** (read whole with its callees; the review's MUST 3):
  1. 0x47d880 -> 0x76fed0: a message to the other peers, only with a network session (0x9425a0).
  2. 0x539e30: the weapon's inventory kind (binding `+8` / property `InventoryBinding` `+0x38`); 0 = only step 6.
  3. **If the weapon is in his hands** (0x727b40 - the respawn's own call never takes this path, the fresh body
     holds nothing): 0x8af180(0, 0, 1) = 'stop what the gun is doing': returns at once in player states 0x2e /
     0x2f, sub-states 0xb / 7 or without flag `[player+0x2720] & 2`; else leaves state 0xd, drops the list
     `+0x83c`, sets `[player+0x838] = 4`, throws a gun with no round left at all away as a dropped one
     (0x47f950), and in a running round queues the player's action 0x2f (slots +0x384 / +0x374 / +0x370). Then
     slot +0x4cc / +0x4c8 (right / left hand), +0x4ec(0) / +0x4f0(0) (the hand lets go) and 0x649250 (the
     'current weapon' item numbers `+0x920 / +0x924 / +0x27ac` from what is left in the hands).
  4. If it is the weapon on his back `[player+0xbc8]`: 0x75e8f0.
  5. `[player+0xbb8 / +0xbbc]` cleared when they name it.
  6. 0x7ddc30(inventory `[player+0xcec]`, weapon): the inventory's slot for that item emptied (0x5aa000),
     0x5ef4f0 on its list.
  7. 0x6d26f0(`[weapon+4]`, 0) = 0x440290: node flag 0x200000 cleared (meaning NOT established); the weapon's own
     slot 151 (0x8a3510) with state 2 (ends its fire / reload / aim sub-states, then its slot +0x54); 0x50d7c0:
     the player's weapon-class bits of `+0x84` worked out again from his hands.
- **Where the removed Zastava and pistol go: nowhere the pool can use.** Nothing above touches the pool entry: it
  keeps `+8 = 0` and `+9 = 0` and is not in the dropped list, so neither 0x55bee0 nor 0x53abc0 finds that object
  again until the round reset. **One AK life costs 2 of the 16 pistols, 1 of the 16 Zastavas and 1 of the 8 AKs**
  (the game's own respawn: 1 pistol, 1 Zastava). A human is a fed once a round, the reset comes with every round:
  it does not add up.

### 4.2 Which AK

All five tab builds' `KLGuns.ini` show the **M4A1 look on the AK-47** (kl_map_guns' pairing). An 'AK' to look at is
there the AK-74, which has no look. The tool writes `AkItem=32` for such a build, `31` otherwise. GUESS: that the
look is what the owner means by 'an ak 47'. `--ak 31` gives the item of that name (it will look like an M4A1).

### 4.3 What the hook does (`AkChance=N`)

Dice per fed (0 .. 99 < N). At the pass after the one that first saw him (about 50 ms after the respawn, before the
body step): item = the level's `AkItem=` or `[Fed] AkItem`; its row found in the shop table; **an item that is row
0's pistol (6) or row 0x1c's rifle (29) is refused** (the loadout would give ONE item twice: with one free object
the second give ends in the int3 - the review's MUST 2); **a free pool object of the item AND TWO free ones of the
pistol are required** (the one this call takes and one left for the game's next give: the removal frees nothing);
first bytes of 0x410710 / 0x538ec0 / 0x55bee0 as known; then `0x410710(weapons, player, 0, row, 0)` on the game's
thread - the respawn's own call with another row. The log gives, before and after, four counts (free / dropped /
owned / out of use) for the AK, the pistol and the stock rifle; 'GIVEN' = one AK and one pistol fewer free. Side
effect: his health is set again to the respawn's value (klbalance.c then writes its own, as at every respawn).

ASSUMPTION, the one thing here the game's own respawn does not do: step 3 of the removal on a player who holds,
and may be aiming, the guns he got a frame or two ago. None of the game's own callers of 0x410710 (Heist slot 197
= 0x42bc80, the multiplayer handlers' slots 11 / 53, 0x74abc0) was shown to run it with a gun in the hands. That
is why `AkChance` is 0 by default and K3 comes after K0 - K2.

## 5. Keys

`KLHook.ini [Fed]` (with klfed.c's): `Kit=1`, `Hunt=1`, `Crosshair=1`, `Body=0`, `AkChance=0`, `AkItem=31`,
`KitSettle=300`, `KitLog=1`. Nothing acts unless `Enable=1` and `Player=1`.
`KLJoin.ini [FedBody]` beside the level archive: `Entries=`, `Root=`, `Variants=`, `Stock=`, `Name=`, `AkItem=`,
`AkRecord=` - written by `python tools/kl_fa_fedbody.py apply <build> <out> [--link]`; `check <folder>`;
`all <work>` made `<work>\build\z_fedbody\M01, M02, M03, M06, retomoto_full` (each = its tab build with every file
hard-linked + the new `KLJoin.ini`; check PASS x5). A map without `KLJoin.ini` got one with this section only
(kljoin.c reads it: '0 box(es)').
For the owner: `Body=1`, `AkChance=35` (GUESS of 'a chance': one in three).

## 6. Wiring (compiled so in `G:\kl_scratch\M\src2` = `git archive HEAD klhook` at dca38bf + this file + the three lines: TEST `G:\kl_scratch\M\test2` c32d2397, SHIP `G:\kl_scratch\M\ship2` e1d33efa; no warning from klfedkit.c)

```
#include "klfedkit.c"        after  #include "klfed.c"
klfk_tick(game_thread);      in klh_tick, after  klp_tick(game_thread);
klfk_init();                 in DllMain, after  klp_init();
```

## 7. Live checks for the lead (a tab map through a tree made from `z_fedbody\<map>`; the scripted player that dies
early: `kl_playtest.py --die --fed-walk`, or `[Balance] Ramp=0 CopToYou=20 PlayerHealth=0.05`; `[Fed] Enable=1 Player=1`)

| # | keys | do | PASS |
|---|---|---|---|
| K0 | `Hunt=0 Crosshair=0` | die in the first 15 s on the park, aim at a heister, shoot him | `fedkit: YOU ARE A FED ... [rules+0x285] = 0 ... [rules+0x283] = N`: **N not 0 confirms section 2's assumption** (N = 0: read section 2's last sentence); the HUD says 'No friendly fire ...'; picture of the crosshair |
| K1 | defaults | the same | `fedkit: hunt: [rules+0x285] 0 -> 1`, `fedkit: crosshair: [rules+0x283] N -> 0`; with `[Bots] Log=2` a `record k (bot): lost ...` after his shots and a bot `dead`; picture: red on a heister, green on a policeman; no 'come back eight times' line |
| K2 | `Body=1` | park, then Retomoto, then Hot Coffee | `fedkit: body: model 1919 -> 36028 ... the player now has 36028`, `fedkit: look: variant 1 -> v`, `fedkit: body: the fed wears ...`; picture in third person; run, aim, fire, reload, cover; no fault. Then let him be killed (a second death) and start the next round: the heister's body is his own |
| K3 | `AkChance=100` (only after K0 - K2) | any map; let him hold and aim before nothing: the call comes ~50 ms after the respawn | `fedkit: ak: dice .. item 32 = shop row 30 (250 rounds); pool before (free / dropped / owned / out of use): item 32 8/0/0/0, pistol 6 15/0/1/0, stock rifle 29 15/0/1/0` and `... pool after: item 32 7/0/1/0, pistol 6 14/0/1/1, stock rifle 29 15/0/0/1 - GIVEN (one more pistol ...)` (the removed two may show under 'owned' instead of 'out of use' if the removal leaves `[object+0x5c]`: say which); the ammo panel reads 250; the rifle is IN HIS HANDS and drawn (the removal queued action 0x2f); fire, reload, switch to the pistol and back; no fault. '8 free' before is what the code says for every tab map; '0 free ... no object of that item at all' = the level has no template for it |
| K4 | `Body=1 AkChance=35` | three rounds with a death each on one level load | one dice line per fed; nothing a second time for one life; `fed: police bodies` counts down as before; the pool's 'before' counts are the full ones again in each round (the round reset 0x42d9a0); `crosshair: [rules+0x283] put back to N` once the next round's heister is in play |
| K5 | K1's keys | the bank and Late Night Opening | `fedkit: body: this map keeps the stock police body` only with `Body=1`; hunt / crosshair as K1 |

Order: **K0 first, before anything else** (it alone tells whether the crosshair reading is right), then K1, K2, K3.
Off the game: `G:\kl_scratch\M\harness\klfedkit_test.c` (klfedkit.c as it is, in a made-up image with stub
routines): `PASS: 56 checks, 0 failed` - the gates, the two bytes and the put-back, one body and one throw of the
dice per life (K4's logic), every refusal of sections 3 and 4. It proves the part's own logic, nothing about the game.

## 8. Assumed / not done

- ASSUMED: `[rules+0x283]` was not 0 in the owner's rounds (K0 settles it); a police player object animates an NPC
  model; `AkItem=32` is the AK he wants; 35 per cent; the loadout's removal on a player with the guns in his hands
  (4.3); that the removed guns' node flag 0x200000 / state 2 leave nothing drawn in the world.
- NOT DONE: the display's player pointer `[display+0x10]` (only worth reading if K0 prints 0); the `free_bone01`
  alias; what the fed's kills pay; a fed's body for the AI feds (kl_fa_fed.py's own choice stands); the respawn
  PLACES (track L); the caller of the `+0x285` setter slot 190; the harness lies in the scratch folder, not in the
  repo (the task names four files).
- klfedkit.c does not touch klfed.c, klbalance.c or klchar.c (which stands down for type 3 by itself).

## 9. The review's points (re\fed_kit_review.md) and what was done

| # | point | done |
|---|---|---|
| M1 | wiring makes Hunt / Crosshair live for the owner at once | for the lead: the box at the top of this note, the `[Fed]` comment of `klhook\KLHook.ini`, K0 / K1 first or `Kit=0`. The defaults stay (the task asks for ON with `Player=1`) |
| M2 | `AkItem` = the pistol's item reaches the int3 | fixed: refused when the item is row 0's (pistol) or row 0x1c's (stock rifle); the tool FAILs 6 / 29 too; harness cases |
| M3 | the removal half of 0x410710 not written down | read whole with its callees (4.1); the removed guns are out of the pool until the round reset 0x42d9a0; the hook asks for two free pistols and logs four counts of AK / pistol / stock rifle before and after |
| S4 | readers of `+0x283` incomplete | the whole list with classes (section 2). REFUTED in part: 0x4254fa / 0x425651 are in 0x425320 = slot 15 of the Fragile Alliance classes, Heist's slot 15 is 0x4c25b0; 0x5df2eb, 0x68109e / 0x6811c7, 0x5e22ea, 0x4eb337 / 0x4eb492 belong to server / client slots Heist does not share. In reach: 0x4569bf - its effect (`+0x282 = 1` at the first loot) is written down |
| S5 | `+0x285` setter slot 190 | named (section 1, klfedkit.c section 1) |
| S6 | crosshair cause unproven | said at the top, in section 2 with the `[display+0x10]` candidate, in the ini comment, in the log line ('0 = Crosshair has nothing to write'); K0 first |
| S7 | `Root=` against `Entries=` | fixed in klfk_source; the tool's check FAILs it; harness case |
| S8 | `--link` shares files | docstring, apply's line, a NOTE in `check` with the count, 3.3 |
| S9 | `Entries=` is a count: apply last | docstring 'RULES OF USE', 3.3 |
| S10 | is there an AK-74 object at all; row 29 is a DLC row | settled by the pool builder 0x78a8d0: 8 of every shop item with a template, no DLC / rank test (4.1); the hook says 'no object of that item at all' when a level has none |
| S11 | `+0x283` not put back | now put back when a heister is in play again on that rules object |
| S12 | no off-game harness | written and run: 56 checks PASS (section 7); in the scratch folder |

## 10. A fed is only a fed: no traitor mark, his kills pay, the HUD's two blocks (track S, 2026-10-11)

The owner, 14:40, after the bank as a fed (hook ship_main1, `[Fed] Player=1`): 'i became a traitor, as a fed youre
only a fed, hud glitch fix and as a fed kill should pay check the FA multiplayer for these things'.
LOG, his round: a fed 14:30:24, six AI heisters `dead` 14:30:58 .. 14:31:22, `dead for good` 14:31:26.
PICTURES `<work>\research\watch\20261011_142846\`: 0005 / 0007 the fed's block in police blue (`r6kxo` + three
skulls, `Total score: $0`, `Round: 1`); 0006 the crew list alone (his row first, in blue); **0008** 'You killed a
criminal. $0', the list faint and the block in ORANGE on the same place (`Total score: -20,000` on the list's
header, `Round: 1` on its first row), his own row and the dead man's gone from the list; **0009** the block alone:
`Traitor` where his name was. Everything below is EXE (kl2.exe 0490, `debug\dasm.py`) unless marked. **NOTHING OF
THE FIX HAS RUN IN THE GAME.** Code: `klhook\klfedkit.c` sections 5 - 7.

**FOR THE LEAD BEFORE THIS HOOK GOES TO THE OWNER:** `NoTraitor`, `Pay` and `HudFade` are ON by default under the
`Enable=1 Player=1` his ini already has (the task asked for that; none of them calls the game, each stands down by
itself when the routine it relies on is not the known one). Run S1 first, or give his ini `Kit=0` / the three keys
`=0` with the hook. And tell him: the text 'You killed a criminal. $0' is NOT fixed (10.3) - the pop-up is.
**THE LEAD'S DECISION, `Pay` (review MUST 1, 10.3 'Where the paid money goes'):** the money goes into the total the
session's end files in the owner's LOCAL profile under the stock slot; it is left ON because he asked for it
('as a fed kill should pay') - `Pay=0` in his ini if the profile's rows matter more. **`HudFade` IS A GUESS about
his words 'hud glitch'** (the fade is stock design; `NoTraitor` alone takes the orange 'Traitor' block out of
picture 0008): show him S3 and S3b side by side and let him say which.

### 10.1 What multiplayer Fragile Alliance does (the reference he names)

Classes: `ZGameRulesFragileAllianceSv` 0xbd2eb4, `..Cl` 0xbd31e4, Arcade's `ZGameRulesHeist` 0xbd3514 (a sibling
that re-implements the server's slots). Client flags = the dword slot 114 answers: 1 traitor, 4 dead, 8 police,
0x40 escaped, 0x80 the undercover cop.

- **Can a cop be marked a traitor? No.** The server's 'becomes a traitor', slot 129 = **0x41d480**, begins
  `flags(killer) & 0xc -> return` (0x41d4ac): a client that is police or dead is never marked.
- **What a kill pays**: 0x4eb260(rules; killer player, victim player) (from 0x794190 <- the server's slot 11, and
  from the client's slot 11), by slot 108 'traitor', 110 'undercover cop', 112 'a criminal' (not police, not 0x80).
  The amounts are ints of the tuning object `[0x168d7c0]`, defaults from its constructor 0x524050:

  | killer | victim | reward |
  |---|---|---|
  | a traitor | anybody | 0 |
  | criminal | a traitor | `+0x65c` = 100,000 |
  | criminal | a policeman | `+0x66c` = 10,000 (an undercover cop in that mode: `+0x674` = 100,000) |
  | criminal | a loyal criminal | 0 (and he becomes a traitor elsewhere) |
  | **policeman** | **a criminal** | **`+0x664` = 50,000** (0x4eb4c4) |
  | policeman | a traitor | `+0x65c` = 100,000; the traitor who had killed HIM: `+0x660` = 200,000 |
  | policeman | a policeman | 0 |

  **A fixed reward. What the criminal carried plays no part** (no money term is in the routine; Arcade's own kill
  rule drops a dead human's money where he falls, 0x5ab010 - the server's was not read); a criminal with nothing
  pays the same 50,000. It goes to the killer's score at once (0x7f3050 on `[rules+0x2c]`),
  the points pop-up says "<victim> +N" (0x4eb533), and the announcement **'You killed a criminal. {Reward1}'**
  (`AllLevels/Interface/Online/Announcements/FA_Killed_Merc`, built in 0x463b70 at 0x463f67 for a local client
  that is police and killed a non-traitor) takes its number from **rules slot 169(kind 0)** - for both multiplayer
  classes the table read 0x4d8950: kind 0 = `[tuning+0x664]`, 2 = `+0x674`, 4 = `+0x678`, 3 / 5 = the constants
  150,000 / 50,000 at 0xd1b3b8 / 0xd1b3c0.
- **The round for a cop**: the outro (0x73c830) gives a police client 'Your finder's fee' (0x73dcd3) = the money
  he holds, a traitor 'Your grab', a loyal criminal 'Your split'; his kill rewards are in his total already.
  NOT READ: the server's payout routine line by line (Arcade's copy 0x796410 was: 10.2), whether a cop can pick
  the dropped money up.
- **His HUD**: the same element as everybody's (10.4); the row's role comes from 0x572050 - waiting 6, dead 7,
  **traitor 1 before police 5** - which is right in multiplayer only because a cop never carries flag 1.

### 10.2 What Arcade does to a police human today

- **Why 'a traitor'.** A dead AI heister goes to `ZGameRulesHeist` slot 16 = 0x485740, which calls the crew
  bookkeeping **0x6706b0** - a routine only the Arcade class has (callers 0x4857b9, 0x70472f). A `ZFFPlayer`
  killer is client 0 (0x6707bc). At 0x6709dd: victim no policeman, without flag 1 (0x6709f4), holding no yellow
  card against the killer (slot 122 = 0x833f70) -> **slot 129 = 0x8fb0d0** (killer, victim). Nothing asks whether
  the KILLER is police; Arcade's slot 129 has no `& 0xc` test. Read whole, it does: (a) the announcer 0x67ee80 -
  silent for a police local client (0x67ef20) but with the list pop-up and the betrayal sting at the round's first
  betrayal - and flag 2 with a 5 s timer; (b) **`test byte [score+4*killer+0x1d4], 1 / jne end`** (0x8fb193);
  (c) flag 1, the local player's byte `+0x2726` = 1 (0x70f770, and the sense manager is told); (d) for killer 0:
  **`[score+0x24] += [tuning+0xc10]`** (0x8fb1d3; **-25,000**, 0x5309f7) and the points pop-up
  (`ZHeistPointsPopupDisplay` slot 11 = 0x66bfa0, "%s$%d"); (e) byte `+0x35` of his record clamped.
- **Why '$0'.** `ZGameRulesHeist` slot 169 = **0x58bbd0 = `xor eax, eax / ret 4`**: every reward kind is 0 in
  Arcade. Its slot 128 (the server's 0x5df280) is `ret 0x10`. What the heisters carried ('Liam $50,000') was never
  in it - not in multiplayer either.
- **Why -20,000.** -25,000 (d) + 5,000: every NPC kill adds `[tuning+0xbf8]` to the round's kill line
  `[score+0x10]` (0x48592a; `+0xbfc` = 10,000 / `+0xc00` = 8,000 are the two other kinds of that branch). After
  that he carried flag 1, so the five later kills only added 5,000 each (b).
- **Why 'Traitor' on the HUD**: 0x572050 again - flag 1 before flag 8 (0x6f31b9 puts `FA_Traitor` in the name's
  place). LOG cannot show the flag: the human's death rule clears it (his last line has `client flags 0000a10e`).
- **What else Arcade does to a police human that multiplayer does not - THE ROUND'S END.** Slot 192 = 0x5dff40,
  at 0x5dffec, for a human without flag 0x40 (a policeman cannot board, 0x68414e): 0x491ad0 gives client 0 his
  round-start numbers back (money `+0x150`, rewards `+0x184`, the kill counters), the life goes (`dec byte
  [score+0x6c]`), and **0x696410 ZEROES EVERY LINE OF THE ROUND, `[score+4 .. +0x30]`**; then the payout 0x796410
  (its police branch 0x7965f2 makes the 'finder's fee' = his money, which 0x70b920 has just zeroed for everybody
  who did not escape) and `[score+0x38] += [score+0x30]` (0x5e001b). `[score+0x38]` is the total the shop buys
  from (0x8eaa4a) and the HUD's 'Total score' = money + lines + total (0x807520). **So a fed can earn nothing
  that survives the round in any round line.**

### 10.3 The fixes (klfedkit.c sections 5 and 6; data writes only)

**No data stops slot 129 for a police killer cleanly**: the ways past it are a victim with flag 1 (pays 100,000,
changes the payout), yellow cards on every heister (flag 0x400: the exe has 35 `test eax, 0x400` sites, not sorted), or a killer
who already has flag 1 (reads 'Traitor'). A private vtable on the rules object is out: every part of the hook knows
the Arcade rules by their vtable 0xbd3514. So the game's routine runs and the hook takes it back / uses it:

| key | what | where | when |
|---|---|---|---|
| `NoTraitor=1` | bits 1 and 2 of client 0's `[score+0x1d4]` cleared when bit 1 is set; the player's byte `+0x2726` = 0 | read-modify-write, the game's thread only | EVERY frame of the main loop while he is a fed in play |
| | `[tuning+0xc10]` held at 0 (or at the pay): the kill costs nothing; put back to the game's -25,000 when he is no fed in play (second death, round over, menu, a heister again), if it is still the hook's number on that object | one int | the 50 ms pass |
| | a negative amount that lands in `[score+0x24]` all the same is taken out - **only in a frame that also finds flag 1 set** | one int | every frame |
| `Pay=1` | `[tuning+0xc10]` held at **+N, N = the game's `[tuning+0x664]` (50,000)**: with the flag cleared, 5.d runs at EVERY kill of a loyal heister - the case multiplayer pays 50,000 for: the game adds N to `[score+0x24]` and its pop-up shows `+$50000`. The hook's next frame - **when it finds flag 1 set, i.e. slot 129 ran** - moves it out of that doomed line: `[score+0x24]` back, **`[score+0x38] += N`** (kept; 'Total score' does not change by the move) | two ints | every frame |
| | **a TRAITOR victim**: the game's own reward in his rewards int (below) is ADDED to `[score+0x38]` | one int | every frame |
| `PayKill=<n>` | another N for a loyal heister (the traitor's numbers stay the game's) | | |

**The line and the flag go together (review SHOULD 1).** Slot 129 sets flag 1 in the call that adds to the line
(0x8fb1aa .. 0x8fb1e5). So a changed `[score+0x24]` is the rule's add only in a frame that finds the flag; any
other change (the hook knows of none in state 0x19) only moves the hook's note of the line, with one log line
`fedkit: the round line [score+0x24] went A -> B with no traitor flag set ... left alone`. The case it closes: a
human who betrayed as a heister (line -25,000), died and came back - a zeroing seen in play would have been paid.

**A traitor victim (review SHOULD 2; EXE 0x6708a9 .. 0x6709bd, read for this round).** A victim with flag 1 (a bot
that backstabbed; one `klgrudge.c` marked) never reaches slot 129 (0x6709f4). Before it: slot 108(victim) true,
slots 108 / 109(killer) false -> `[score+0x184+4*killer] += [tuning+0x65c]` (100,000; 0x67099b), or, when the
victim is the one who had killed him (0x6708f9), `+= [tuning+0x660]` (200,000; 0x670975) and `[score+0x18] +=
[tuning+0xc04]`; then the crew-kill byte `[score+0x126+killer]` (0x6709bd). Multiplayer's two numbers for a
policeman - but in the REWARDS, which 0x491ad0 puts back at the round's end for a man who did not escape: the
first report's 'paid by the game itself' was true for the round's display only. With `Pay` the hook now adds the
same amount to the total when ONE frame shows all of: the rewards risen by exactly `[tuning+0x65c]` or
`[tuning+0x660]`, and the crew-kill byte moved. The rewards int is never written (the first version's own
`+0x184 += N` for a loyal kill is gone - review SHOULD 4: it rested on an unseen assumption). NOT READ: whether
slot 56 (the 'money' of 'Total score' = slot 56 + lines + total) includes the rewards - if it does, the HUD's
'Total score' counts a traitor's 100,000 twice until the round ends; the kept total is right either way.

**Slot 129's first and last part now run at EVERY kill (review SHOULD 3).** With flag 1 cleared each frame, (a)
flag 2 and the 5 s timer at record `+0x70` are set anew per kill (the hook clears flag 2 with flag 1; the timer
runs out alone; the announcer stays silent for a police client except the round's first betrayal), and (e) the
minimum into byte `+0x35` of HIS crew record is taken again with that moment's numbers. **What `+0x35` is was not
read**; stock lets it fall once a round, here it can fall at each kill.

**The put-back of `[tuning+0xc10]` (review SHOULD 5).** A put-back that cannot be written is tried again at every
50 ms pass and the hook goes on knowing the number is its own; a number above 0 found there before the hook's
first write is never taken for the game's - -25,000 (the constructor's, 0x5309f7) goes back, with a log line.

**Where the paid money goes when the session ends (review MUST 1; EXE 0x68b930 as the review read it, NOTE
re\leaderboard.md 2.1 / 2.3).** `Pay` writes `[score+0x38]`. The stats commit 0x68b930 (state 0x28: the last life
lost, or Quit inside a session) reads that dword three times: `stats+0x24 = max(..)`, `HeistTotalPoints[slot]
= max(..)` (0x68bad9 .. 0x68baef), and the LOCAL top-12 list of the slot, `profile+0x1408 + slot*0x30`
(0x68bb6d .. 0x68bc29), which 0x6587c0 saves to disk when a profile is loaded; the same dword is the score of
`UploadLeaderboardScore` (`KL2_Heist<slot>_TotalMoney`).
- **Steam: not reached - and only because of `klsteam.c`.** Its guard blocks the upload and every SetStat /
  StoreStats on a level that is not stock; klfedkit.c acts only with `klx_on` and verdict 2, the same test.
  THIS FILE DEPENDS ON THAT GUARD: were it ever off or its verdict changed, `Pay`'s money would be uploaded as a
  score of the STOCK map's board. Live check S2b is the proof in the game.
- **The owner's local profile: NOT PROTECTED BY ANYTHING.** Every session on a tab map already files its total
  under the stock slot's local list (re\leaderboard.md 4.3 'proposal, not tried'; klsteam.c has no code for it).
  `Pay` adds money to that number the game would never have given: up to 7 x 50,000 (more with traitors) a fed
  round, where a fed round banks 0 in stock Arcade. An old channel with new content. `Pay=0` keeps it out; the
  real cure (protect the profile rows on a level that is not stock) is klsteam.c's, not this track's.

`Pay` needs `NoTraitor`. Both stand down when slots 129 / 114 or the 32 code bytes at 0x8fb193 / 0x8fb1d3 are not
the known ones. Gates: klfedkit.c's section 0 (a police human, record 0 in play, Arcade rules, round state 0x19,
a level that is not stock); nothing online.

**What stays** (all EXE, none seen):
- **'You killed a criminal. $0' keeps its $0.** The number is slot 169's code; the text is set once into the
  announcement's two text objects (0x468430). Nothing in data reaches it. A LEVEL fix exists (not done, not this
  track's files): the string `AllLevels/Interface/Online/Announcements/FA_Killed_Merc` in the map's `.LOC` without
  `{Reward1}` - that text is shown only to a police human who killed a heister.
- 'Traitor' can show for the one frame between the kill and the hook's pass.
- At his FIRST kill in a round with no betrayal yet: the list pops up 2 s and the betrayal sting plays
  (`[rules+0xe84] == 0`; holding that int at 1 would stop it - its other readers were not followed: not written).
- The kill line still gets its 5,000 a kill (wiped at the round's end like every heister's who dies).
- Not paid: a second kill in the SAME frame (the flag is still set: the game adds nothing; the log's 'your crew
  kills this round' count shows the gap); two traitors in one frame (the sum is neither of the two numbers).
- **A kill in the round's very last frame** (slot 192 leaves state 0x19 in the frame of the kill; review SHOULD 6):
  the hook's frame does not run again - flag 1 and the byte `+0x2726` stay, the score page can read 'Traitor',
  that kill is not paid. The round reset 0x8c7a80 clears the flags; nothing read here clears `+0x2726` of the
  police object, which is not used again (re\fed_respawn.md 2.3a).
- **The life**: a fed's round still costs it, as re\fed_respawn.md 2.4 says. Not changed, not asked.

### 10.4 The HUD glitch (klfedkit.c section 7, key `HudFade`)

The crew list and the top-left block are ONE element, `ZFAPlayerListDisplay` (osd `+0x10c4`, 0xbbdf6c), by its
state `+0xee0`: 0 the block, 2 the list (2 s by 0x72d130(0) at every kill announcement 0x704ae1 and at a betrayal
0x67eef1; 10 s by 0x72d130(1)), **1 the way back**: the update (slot 5 = 0x76db00) adds `dt x 0.5` to `+0xf00`
and the render (slot 2 = 0x5e60f0) draws the block with alpha `+0xf00` (0x5e6249) and the list with `1 - +0xf00`
(0x5e66bb) **on the same place: two seconds of two texts on each other.** That is picture 0008 (the list's plate
is faint in it). **No test of the player's side is in the fade**: a heister has the same two seconds after every
kill line (not found in his earlier pictures - one every 7 s; `20261011_122753\0085, 0090` show the list alone).
A fed who hunts gets it at every kill; with the traitor mark the block was orange and said 'Traitor' on top.
Rows: the list leaves out the dead and, for a traitor, his own row (seen in 0008; the routine was not read).

`HudFade=1`: when the state is 1 the hook writes state 0 and `+0xf00` = -1.0 - what the update itself writes when
the fade is over (0x76dbab / 0x76dbb1): the list goes, the block stands at once (at most 50 ms of fade, block
alpha under 3 %). The element is reached as the game reaches it (`[[gamedata+0x15dc]]`, 0x588680 / 0x4ddae0) and
must have 0x76db00 in slot 5 (stock vtable or a private copy of klhud.c). `HudFade=2` does it for a heister too.
**Nothing of klhud.c is needed or touched.** For kl-merge-3e: `[HUD] Reuse=2` puts strings into this element's
row texts - state 1 is when stock draws them at `1 - +0xf00`; with `HudFade` that state lasts one pass.

### 10.5 Live checks for the lead (a tab map, `[Fed] Enable=1 Player=1`, `[Bots] Log=2`; the scripted player that dies early)

| # | keys | do | PASS |
|---|---|---|---|
| S0 | `NoTraitor=0 HudFade=0` | die, come back, kill one heister | the control: the block orange with 'Traitor', Total -20,000 (the owner's pictures 0008 / 0009); no `fedkit: traitor:` / `pay:` line |
| S1 | defaults | die in the first 20 s, kill a heister | at the respawn `fedkit: rules: your flags 00080108, round line [score+0x24] 0, total N; [tuning+0xc10] -25000 -> 50000`; at the kill `fedkit: traitor: the game marked you a traitor (flags 0008010b): flags -> 00080108` (0000010b -> 00000108 when the respawn's 10 s flag 0x80000 has run out) and `fedkit: pay: +50000 for a heister (kill 1 ...): round line 50000 -> 0, total N -> N+50000`; picture: the block BLUE with his name, 'Total score' = N + 55,000, the pop-up `+$50000` (and the kill feed's `+$5000`); no 'Traitor' |
| S2 | defaults | kill three more, then die | one `pay:` line per kill, 'your crew kills this round' counting 1, 2, 3, 4 with 'kill' the same number; at his death `fedkit: traitor: [tuning+0xc10] put back to -25000 (you are no fed in play)`; the score page: 'Total' holds the 4 x 50,000 (the round's own lines are 0: he did not escape) |
| S3 | defaults | watch the top-left corner after each kill | `fedkit: hud: the player list's cross-fade cut (state 1 -> 0, ...)` about 2 s after the first kill line; pictures every second for 5 s after a kill: the list alone, then the block alone, never both |
| S2b | defaults, `[Steam] Log=2` | as S2, then lose the LAST life as a fed (the session ends, state 0x28) | **the proof that the paid money does not reach Steam**: `steam: BLOCKED UploadLeaderboardScore(.., <the total with the 50,000s>)` and the blocked SetStat / StoreStats lines; no 'passed' line. (The local profile's rows are NOT protected: 10.3.) Run it with the TEST hook, which never writes to Steam at all, before any SHIP run |
| S3b | `HudFade=0` | as S3 | the stock fade WITHOUT the traitor mark: block blue with his name fading in over the list for 2 s. Beside S3's pictures it is what the owner chooses between - `HudFade` is a guess about his 'hud glitch' |
| S4 | defaults | the next round as a heister; kill a heister on purpose | `fedkit: traitor: [tuning+0xc10] put back to -25000 (you are no fed in play)` in the log BEFORE the heister's kill (at the fed's death or the round's end); then the game's own rule again: 'Traitor', -25,000; `HudFade=1` does nothing for him |
| S7 | defaults, `[Bots] Backstab=100` (or a bot `klgrudge.c` marked) | as a fed, kill a bot the log calls TRAITOR | `fedkit: pay: +100000 for a TRAITOR ([tuning+0x65c]; the game put it into your rewards A -> A+100000 ...): total N -> N+100000`; no `the game marked you a traitor` line for that kill; note what 'Total score' shows (N+100,000 or N+200,000 = the open question about slot 56) |
| S5 | `Pay=0` | as S1 | `[tuning+0xc10] -25000 -> 0`, no `pay:` line, Total moves by the kill line's 5,000 only, the pop-up says `+$0` |
| S6 | `HudFade=2` | a round as a heister | the `hud:` line after a kill line, no overlap |

Off the game: `G:\kl_scratch\S\harness\klfedkit_test.c` (track M's harness + a score object, the tuning object,
the list element and a stand-in for slot 129): `PASS: 105 checks, 0 failed` (56 old + 33 + 16 for the review: a
line change without the flag is neither paid nor undone, a traitor's 100,000 / 200,000 added once and only with
the crew-kill byte and the exact number, a put-back that fails and is tried again, a +50,000 found there never
taken for the game's; the 33: the int held and put
back, the flag off inside the 50 ms, the move to the total, two kills in one frame, a round line that was not 0,
the game writing its number back, not the game's thread, a stock level, another rules class, the fade's cases).
It proves the part's own logic, nothing about the game.

### 10.6 Assumed / not done

- ASSUMED: that slot 56 does not include the rewards int (else a traitor's reward shows twice in 'Total score'
  for the rest of the round); that the 'had killed him' test of 0x6708f9 is multiplayer's 'the traitor who had
  killed HIM' (the byte compared was not followed to its writer); that the outro's 'Total' is `[score+0x38]` as the code
  at 0x7df882 reads it; that clearing flag 1 a frame late leaves no AI state behind (0x4801a0 tells the sense
  manager at every kill and is not told again; of the 20 readers of `+0x2726` three were read); 0x72d130(1) = the
  list key; that the cross-fade is what the owner calls 'the hud glitch' (it is the only state in which the element
  draws both, and it is his picture).
- NOT DONE: the '$0' text (level `.LOC`, or a rules-side answer that needs code); the betrayal sting at the first
  kill; the life; the server's payout routine and the dropped money for a cop; the AI feds' kills (they are NPCs:
  no client, no score); the list's row rule for a traitor; `klhook\klhud.c` (not this track's).
- The owner's fifth point of the same message - 'the belly flop shouldnt be when im already dead' - is kldown.c's
  (another track; `klhook/kldown.c` and `re/player_down.md` are modified in the tree by it); nothing of it is in
  this note. THE LEAD: make sure that track holds it.

### 10.7 The review's points (re\fed_rules_review.md) and what was done (fix round; NOT RUN IN THE GAME)

Compiled: `git archive 28953d8 klhook` + this klfedkit.c in `G:\kl_scratch\S\src2`; no warning from klfedkit.c
(the one warning is klhud.c(188) C4101). TEST `G:\kl_scratch\S\test2\dinput8.dll` sha1
1e08dcd99496e1b55bc0c28c13f0f978ea3118a8, SHIP `G:\kl_scratch\S\ship2\dinput8.dll` sha1
c298e00db420d841f5213eb57e1ce0fb5be43f66 (the first round's `test` / `ship` are superseded).

| point | done |
|---|---|
| MUST 1 where the paid money goes | written: 10.3 'Where the paid money goes', the ini's `Pay` comment, klfedkit.c section 6; the default is the lead's decision (top of section 10); no code change |
| SHOULD 1 tie pay / undo to the flag | done: `marked` in `klfk_rule_frame`; a change without the flag only moves `line0`, one log line |
| SHOULD 2 a traitor pays nothing kept | done by the first choice: the game's reward in the rewards int is added to the total, tied to the exact number and the crew-kill byte (EXE 0x6708a9 .. 0x6709bd read); live check S7 |
| SHOULD 3 slot 129's first part at every kill | written: 10.3 and klfedkit.c section 5; `+0x35` still not read |
| SHOULD 4 the rewards write | dropped; the int is only read |
| SHOULD 5 `klfk_pen_back` | done: `have` stays until the write holds, a number above 0 is never adopted as the game's |
| SHOULD 6 the last frame's kill | written under 'What stays' |
| SHOULD 7 live checks | S2b added, S4 names its log line (and S3b, S7) |
| SHOULD 8 `HudFade` is a guess | kept marked: top of section 10, S3b beside S3; default unchanged |
