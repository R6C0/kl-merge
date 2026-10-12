# HUD names: the character's name in the list, initials over the head (2026-10-12)

Owner: 'for how the names are i want it to be that characters one that got randomised and maybe initials for like above their head?'
Part: `klhook/klhud_names.c` (new, compiles in SHIP and TEST in a scratch copy; NOT RUN IN THE GAME). Static reading of kl2.exe (build 0490).

## 1. What was established

**Which character a record has** (nothing has to be added to klcrew.c / klchar.c):
- `klcrew.c` keeps the draw in `klw_r.b[rec].ch` (1-based index into the level's wardrobe, `klw_drawn_char(rec)`), but that is 0 for a member
  who kept his body, was aboard or dead at the draw. The better source is `klw_who_now()` (klcrew.c, read only, valid off the game's thread,
  Random on or off): per crew record it reads the model the member's node wears NOW (`[[[record+4]+4]+0x68]`) and matches it against the
  wardrobe roots (`klw_source`: the level's KLWardrobe.ini copy in klchar.c's `klc_w`, else the eight models of `rules+0x208`). The human's
  `ch` is filled when he plays a heister (player type 2). `klw_source()` gives the name (`src.c[ch-1].name`: 'Tommy', 'Kane', 'Ashkanan' ...;
  English, Dead Men names have no .LOC text in Dog Days). The 'bots became Liam, Pierre, ...' log line is `klw_say` from the same table.
- The human's choice: `klc_char` (Heister page); his worn body is what `klw_who_now` reports.

**Where the crew list's name comes from today:** `klhud.c klu_compose`: `[[record]+8]` = the C string of the record's client block (record
= `rules+0x348 + 0x7c * i`, the block at `[record]`; EXE 0x841e50 returns that record). It is the name the game gave the member when the
session was made: the human's Steam name, the AI heisters' stock names (the picture of run F2_DM03 shows 'Tommy' over a bot). Nobody
rewrites it unless `[Crew] Names=1` (klcrew.c `klw_rename`: kl2 0x83e2e0 builds a string, 0x469250 hands it to the block). So with
`[Crew] Random=1` the stock name and the drawn body disagree: that is the owner's complaint.

**The tag over a heister's head** (the two-line 'Tommy / $0' in `research/shots/F2_DM03_130s.png`, small, the HUD face): the element that draws it
is NOT identified. Checked and excluded:
- `ZPlayerNameDisplay` (osd+0x10c8, vtable 0xbbdfa4, 0x74 bytes): slots 2 Render = 0x6ba110 (a stub), 5 Tick = 0x638ca0 / its text refresh 0x72a5c0,
  6 Update 0x7b2e00 (places one text at a screen point scaled from the transform at +0xc). The only strings it pushes are 'Kane' (0xb633f4) and
  'Lynch' (0xb6ba80): the campaign co-op partner's tag. One fixed screen position: no per-heister world tag.
- `ZFAPlayerListDisplay` (0x6f3000 rows; format `$%i` at 0xb5bf60, only user 0x6f369f): list and top-left block, not world tags.
- the kill / score feed (0x66bfa0 and 0x485960: formats `%s$%d` 0xb4101c, `%s %s$%d` 0xb254f4): 'X killed Y +$' lines.
- `ZPlayerInfoDisplay` (tutorial texts), `ZPointOfInterestDisplay` (loot / escape markers): not looked at in depth, no name string found.
So the decision cannot be a wrap of the tag's Render. **What is known is its text source**: the tag reads the same name as the list (the picture:
'Tommy' on the bot, the stock name), i.e. the record's string. (GUESS, the one assumption of this part: the tag reads that string at draw time,
or on a refresh, not once when the actor is created. N1 settles it.)

## 2. Decision

- **List (A):** the hook's list asks `klnm_name(record address, buf, cap)` (klhud_names.c). Pure read, no game memory written. It returns the
  name of the character the record wears; no known character (kept body, no wardrobe match, policeman) -> the game's own name (the stock name
  the record had when first seen). Your own row: the name of YOUR character (`OwnName=0`, the owner's wording 'that character's one'), or your
  Steam name with `[HUD] OwnName=1`. DECISION FOR THE OWNER: the default is 0 (character name); it is one key.
- **Tags (B):** `[HUD] NameTags=1` writes the INITIALS into the record's name string with the game's own two calls (klcrew.c's `klw_rename` verbatim:
  0x83e2e0 + 0x469250, the same prologue checks, game thread only, at most two calls a tick, at most three writes per record and character; a
  write that is already in place costs nothing). `NameTags=2` writes the full character name (= klcrew's Names=1, for those who want it), `NameTags=0` leaves
  the game's. The human's own record is never written (no tag over his own head; his row has its own key).
  - The stock update does not need to be waited for: after the write the record IS the initials, until the round's rules object changes. The
    stock string is remembered per record (`stock`) and is what the list falls back to.
  - SIDE EFFECT (a decision for the owner): everything else that prints the record name shows the initials too - the kill feed ('K killed R'), the
    round-over page's list, the death-camera 'Killed by'. The HUD list is not affected (it never reads the string for a known character). If the
    owner wants full names in those places, the tag element has to be found and wrapped (section 6 gives the next step); until then `NameTags=2` or 0.
  - Conflict: `[Crew] Names=1` already writes full names into the same string. With `NameTags=1` klhud_names.c stands down for the tags (one log line;
    `[Crew] Names=0` is needed); with `NameTags=2` it stands down because klcrew.c does the same write.
- Under `[HUD] Draft=1` the defaults are Names=1, NameTags=1; otherwise 0 / 0 (the draft's other keys work the same way).

## 3. Files, keys, log

`klhook/klhud_names.c` (new; included after klcrew.c and before klhud.c): `klnm_initials_one`, `klnm_unique` (pure), `klnm_refresh` (a table of
rec -> stock name -> character -> initials, rebuilt at most every 250 ms from `klw_who_now`), `klnm_name`, `klnm_write`, `klnm_tick`, `klnm_init`.
Keys `[HUD] Names`, `NameTags`, `OwnName`, and the HUD's `Log`. Log lines:
- start: `names: on; list = the character's name, tags = initials, own row = your character's name`
- Log=2, once per change of the crew: `names: record 3: game name 'Tommy' -> character 'Kane' -> tag 'K'` (the human: `... -> list 'Kane'`)
- Log=2, per write: `names: the tag text of the record at 0a3c1e10 is now 'K' (was 'Tommy')`
- stand-downs (once each): the Names=1 conflict, the two routines not the ones this build knows, the tick not on the game's thread, a record that
  took its text three times and was set back.

## 4. The initials rule and its self-test

Words = runs of letters / digits (any byte >= 0x80 counts as a letter; UTF-8 sequences are copied whole); base = first letter of each word in capitals.
If two of the crew would get the same text, those get the first two letters of the FIRST word plus the first letters of the other words; if still
equal, three letters; an identical rest (the same name twice) gets a digit from the second on. Empty / no letter -> '?'.
Self-test (compiled alone with `KLNM_PURE_ONLY` in `G:\kl_scratch\hud_names\t\t.c`, 20 checks, ALL PASS):

| input (the round's names) | output |
|---|---|
| Kane / J.C. / Red / Ashkanan / 'Moustache - J.C.' / '' | K / JC / R / A / MJC / ? |
| Liam, Lynch | LI, LY |
| Kane, Red, Tommy, Liam | K, R, T, L |
| Pierre, Parker, Kane | PI, PA, K |
| Jean, J.C., Jimmy | JE, JC, JI |
| Tommy, Tommy, Red | TOM, TOM2, R |
| Liam, (none), Lynch | LI, '', LY |
| Mitchel, Meldal, Mark Lee, Mary Lou | MI, ME, MARL, MARL2 |

## 5. WIRING (exact old -> new; nothing else changes. klcrew.c and klchar.c need NO getter.)

**klhook.c**, three edits (keep each line's own comment style):
1. after `#include "klgrudge.c"` add the line `#include "klhud_names.c"                          /* klhud_names.c: the crew's names: the character in the list, initials in the tags (after klcrew.c, before klhud.c) */`
2. old: `    klw_init();`  new: `    klw_init();` followed by `    klnm_init();                                      /* klhud_names.c: [HUD] Names / NameTags / OwnName */`
3. old: `    kly_tick(game_thread);` (the line carrying the comment 'klgrudge.c: the crew answers your bullets')  new: the same line preceded by
   `    klnm_tick(game_thread);                           /* klhud_names.c: the tag texts (initials), after klw_tick: it reads who wears whom; game thread only */`

**klhud.c**, `klu_compose`, in the record loop, directly after the line
`        if ((blk = klh_rd32(r->at)) != 0 && klh_rd(blk + 8, &str, 4) && str) klh_rdstr(str, name, sizeof name);     /* [[record]+8]: 0x841e50 */`
add the line
`        klnm_name(r->at, name, sizeof name);                  /* klhud_names.c: the NAME OF THE CHARACTER he wears (returns 0 = the game's own name stays) */`
(the existing `if (!name[0]) snprintf(...)` fallback after it stays). The skull / strike widths already follow `name`.

**KLHook.ini** (owner): `[HUD] Draft=1` is enough; explicit: `Names=1`, `NameTags=1`, `OwnName=0`; `[Crew] Names=0` (the default).

Applied and compiled in the scratch copy (`git archive HEAD klhook` under `G:\kl_scratch\hud_names\`): `build_auto.bat` -> `built ...\test\dinput8.dll (TEST)`,
`build.bat` -> `built ...\ship\dinput8.dll (SHIP)`, no error. The working tree's klhud.c (another workflow's edits) has the same anchor line (884 there, 820 in HEAD).

## 6. Guesses and risks

1. The tag reads the record string live (section 1). If N1 shows the tag still stock after the log says it was written, the tag text is cached when
   the actor is made: then the element must be found (next step: a Log probe that scans the OSD's text objects for the stock name, or walk
   from the 'Tommy' ZCHAROBJ's chunk back to its owner) and wrapped like klhud_popup.c; klhud_names.c's initials function and the table stay.
2. The record string write is klcrew.c's proven pair (live: `crew: bot N is now called` with `[Crew] Names=1` has not been seen in the owner's runs
   either: Names defaults to 0 - so even that pair is only read, not run, in the game). Mark it unproven; N1 is its first run. The hook stands down
   on a wrong prologue, so the worst case is no change.
3. Kill feed / round-over page show initials with NameTags=1 (section 2).
4. `klw_who_now` matches models, so a heister that wears a body outside the wardrobe list (ch 0) keeps the stock name and his stock initials.
5. Not for online (Arcade only, as klcrew.c).

## 7. Live check N1 (owner away; hook = the build with this part, `[HUD] Enable=1 Draft=1 Log=2`, `[Crew] Random=1 Log=2`, a Dead Men map with a wardrobe)

Pass: no fault; the log has `names: on; list = the character's name, tags = initials ...`, then per round the `record N: game name '...' -> character '...' -> tag 'X'`
lines (the characters agree with `crew: bot N is Kane ...`), then one `the tag text ... is now 'X'` per bot. Pictures (every 2 s, a bot in view): the crew
list rows read the character names (not 'Tommy' on a Kane), your own row your character, and the tag over each bot's head reads the INITIALS (one or two
letters; two bots with the same first letter get two letters). Fail reading: write lines in the log but the tag still the stock name -> guess 1.
Second round of the same process: the lines appear again (the rules object changed). With `[Crew] Names=1` and `NameTags=1`: one stand-down line.

## 8. Review round (re/hud_names_review.md, ACCEPT WITH FIXES) - what was done

| finding | result |
|---|---|
| M1 key clash with klhud.c `Tags` (the TRAITOR text) | DONE: the key is `[HUD] NameTags` (0/1/2). `Tags` stays klhud.c's. |
| M2 no level gate | DONE: `klnm_tick` starts with the game-thread test, then `klb_level(why)` (Steam guard on and the level not the stock one of its slot), like klcrew.c. The list side keeps the HUD's `allowed` test. |
| S1 write only when settled | DONE: state 0x12..0x19 only, the crew table unchanged for 1.5 s, and the record's game string non-empty (`klnm_learn` re-reads an empty one). |
| S2 stock could become our initials | DONE: `tagged` is now used (set at every write); `klnm_learn` keeps the old `stock` when the string equals `tagged`, also across a new actor in the same slot (same record address). |
| S3 tries / told per round | DONE: state >= 0x1f marks `left`; the next round resets `tries` / `told` (and the settle clock). A changed rules object still clears the table. |
| S4 Names=0 with NameTags | DONE: NameTags on forces Names on (one log line), because the list otherwise falls back to the record string = the initials. |
| S5 records that left stay `used` | DONE: a record not in the crew this refresh is `used = 0` (its texts are kept for S2); initials are computed among present records only. |
| S6 game_thread before refresh | DONE in `klnm_tick`. NOTE: `klnm_name` (called from klhud.c's compose) still refreshes the table too; it only reads game memory and is rate-limited to 250 ms - the same thread as the tick in practice (klhud's compose runs from klu_tick), not guarded further. |
| NOTE tag element unidentified | Stands; the tag half is NOT promised before live check N1 (a failure is harmless: log says written, picture shows the stock name). |

Build: scratch copy with the wiring of section 5 unchanged (three lines in klhook.c, one in klhud.c): TEST and SHIP both built, no error.
The WIRING of section 5 is unchanged by this round. INI: use `NameTags` (not `Tags`) in section 3, 5 and 7.
