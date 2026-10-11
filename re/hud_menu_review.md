# Review: track M - `tools/kl_hud_menu.py`, `re/hud_menu.md`, builds `<work>\build\hud_menu2` (2026-10-11)

Adversarial review, OFFLINE: the game was not started, nothing installed, nothing written outside this file.
Words: **EXE** = disassembled in this session (`debug\dasm.py`, capstone); **DUMP** = read from
`<work>\research\crash_1010_1424\KLHook_1.dmp`; **FILE** = read from the overlay / level archives; **RAN** = a
command of this session; **NOT ESTABLISHED** = nobody knows yet.

## Verdict: ACCEPT WITH FIXES

- The DEFAULT builds (`Overlay_nofonts`, `Overlay`, `level_DM03`) change attribute values and 22 textures' pixels and
  nothing else (RAN, independently). They may go to live checks M1 / M3 as they are. The look needs a second pass
  before it is the owner's (findings 6, 7).
- `--board` / `Overlay_board` must NOT run before findings 1-3 are dealt with. The note's account of the 14:24 crash
  is incomplete; the missing half is exactly what makes adding elements dangerous.
- There is no hook code in this track, so nothing to review for calling conventions, vtable wraps, .text patches,
  per-frame cost or stand-down state. The one C snippet (WIRING) is read-only; findings 4, 12.

## What was re-derived and holds

| Claim | Found |
|---|---|
| table writers, cap 0x13e8, int3 on overflow | EXE 0x7fad4f-0x7fad8d (element; index kept at +0x5c), 0x667e40-0x667e6e (window), 0x47d629 (colour set), 0x53c769 (button graphic) |
| 0x8d1c10 = `index < [this+0x9f48] ? [this+index*8+8] : 0`, `ret 4` | EXE, as written |
| 0x861720: object under the cursor, `vtbl[0x30]` type test, `id = vtbl[0x2b0]()`, `-1` leaves, `index = id & 0xffff`, `vtbl[0x84]` called on the entry with no kind test (0x8617fe, 0x861824, 0x8618b7) | EXE, as written |
| ZBaseWindow vtable 0xbaf6c4 `[+0x80] = 0`, `[+0x84] = 0x3f800000` | EXE |
| `HeistStatusLeaderboard` 0x4970a6, `HeistStatus` 0x4970c0 / 0x4970de through 0x7ed9a0; `FABuyWeaponsNew` 0x7558cd; `HeistStatusLeaderboard_EndGame` 0x864903 | EXE (the addresses are the pushes of the names) |
| vtables 0xbb7dc8 ZMercsMenuElements, 0xbbcd1c ZMercsShowInfoFA | RTTI |
| default `apply` adds / removes nothing | RAN: after removing every ` ColorSet="..."` and blanking the four colour attributes, each of the three XML files of `Overlay`, `Overlay_nofonts`, `Overlay_online` equals its source byte for byte; `level_DM03` differs from its source in `F03_Main.TEX` and `Menu/online.xml` only, and that online.xml equals the overlay's |
| `check` results of the note | RAN again: PASS / PASS / PASS with the two NOTEs |
| a recoloured element never precedes the definition of the set it names | RAN (`DirtyMoneyColorSet` / `WANTED` are defined at offset 18.6 k of online.xml, before every use) |
| the two tags of `--board` are null-guarded | EXE 0x5bb47b-0x5bb48a (`0x7bb2a0` result tested), row index against a count at 0x5bb468 |

## Findings

### 1. MUST (before any element is added, here or in any other track) - the dangerous index IS known: 5000, and it is in the scene file

The note says 'what hands the cursor object its id was not found, so the dangerous index cannot be computed' and
'element 5000 is not re-derived'. Both can be settled offline:

- DUMP: fault at eip 0x3f800000, `ebx = 0x1388` (the index, 5000), `ebp` -> an object with vtable 0xbaf6c4
  (ZBaseWindow), `esi = 0` (the id's high word). So the id was exactly 5000.
- EXE: ZBUTTON (vtable 0xbabc3c) `[+0x2b0]` = 0x83d5d0 = `mov eax,[ecx+0x60] / ret`. The object under the cursor is
  a ZBUTTON and the id is its field +0x60.
- FILE: in the menu scene and in every level's `MenuFA.zip` exactly ONE ZBUTTON (type 0x100033) carries a non-zero
  value in its second integer property: `ZWINDOWS/Menu/DefaultFocus` = **5000**. The pool buttons `Button#01..110`
  and the ten slider buttons carry 0 (given at run time; who writes `[button+0x60]` then is NOT ESTABLISHED - a
  byte search for 'element+0x5c copied to +0x60' found nothing convincing).

So: whenever the cursor is over `DefaultFocus` (GUESS: the catch-all behind the page), 0x861720 asks for table entry
5000. While the table holds 5000 entries or fewer, 0x8d1c10 returns 0 and nothing happens - that is stock. As soon
as the count passes 5000, entry 5000 is whatever the XML put there: an element takes a stray hover, a window /
colour set / button graphic is called through a vtable that was never meant for it. The 14:24 package had grown the
table past 5000 and a `<Window>` landed on 5000.

Consequences the note and the tool do not have:
- THE REAL BUDGET IS 5000 ENTRIES, NOT 5096, and it applies to the menu (frontend.xml + online.xml) and to each
  level (ingame.xml + online.xml) separately.
- 'Keep the table as it is' is sufficient but not the rule; the rule is 'count <= 5000, or entry 5000 is an
  element'. The live count is unknown (re/menus.md open question 3; its model says 5992 for the menu, which cannot
  be). `Overlay_board` adds 48 entries to online.xml, which is loaded at the MENU too: if the installed overlay
  stands at 4953..5000 today, T1 crashes on the first mouse move over the background, or - worse - only on some
  pages.
- T1's '30 s of mouse at the menu' is the wrong test. Read the count first (finding 4), at the main menu AND at a
  level's round-over page. Only then decide.
- Correct `re/hud_menu.md` 1.1 and the tool's docstring ('What hands out that index was NOT traced').

### 2. MUST (`--board`) - `PlayerIndex` is a ROW of the game's own ordering, not klbot's record number

EXE 0x5bb45e (`StatusTotal`): `[elem+0xec]` (PlayerIndex) is tested against a count, then
`rules->vtbl[0x188](PlayerIndex)` (or `vtbl[0x184](PlayerIndex, [elem+0xf8])`) maps it to a record byte, `0xff` =
none, and only that byte goes to `vtbl[0xd4]`. The note's assumption (b) 'PlayerIndex k is the record number
klbot.c reads' is therefore wrong for the score, and `StatusPlayerName` (0x5bb7df) takes a different path again
(`0x87c980`, `0x685350`, `0x72c9e0` supply ITS count) - that name row k and score row k are the same heister is
NOT ESTABLISHED. A hook that fills `KLB_Fate<k>` from klb_read's record k would print fates on the wrong rows.
Before the fate blocks mean anything: read both paths to the end, and have the hook go through the same mapping
(slot 0x188) instead of the record number.

### 3. MUST (`--board`) - do not ship the board through Patch01.zip

`Overlay_board` was built with `--online-in-patch`. If Patch01.zip does override the levels' `Menu/online.xml`
(the tool's own assumption), the shifted table reaches EVERY level: stock Arcade maps, the campaign's online.xml
users and multiplayer - outside the track's 'Arcade, grafted maps' scope, and with finding 1 open. Keep the board
to `level --board` archives of our own maps until T1 has passed there. (The colour-only online.xml in the patch is
a look decision, not a fault: see 9.)

### 4. SHOULD - the WIRING snippet: read the kind word, use the right logger, log entry 5000

- EXE: each table entry is 8 bytes `{object, kind}`; the writers store kind 0 (element, 0x7fad67), 1 (window,
  0x667e5e), 2 (colour set, 0x47d641), 3 (button graphic, 0x53c781). Count kinds from `mgr + 0xc + 8*k` instead
  of comparing vtables with 0xbaf6c4 (a derived window class would be missed; colour sets and button graphics are
  as wrong a target as a window and are not counted at all).
- Print the count AND entry 5000's kind when the count is above 5000: that is the whole verdict of finding 1.
- The logger in klhook.c is `klog(...)`, not `klh_log`. `klh_rd32` / `KLH_VA` exist as used (klhook.c 202, 219).
- That the table object is `[[0xdd265c]+0x824]` stays ASSUMED (klauto.c has the window system at `[mgr+4]`;
  0x861720 takes the table from `[guisys+0x4b4]`; nobody has shown these meet). The vtable test makes a wrong
  guess silent, so add an `else` line saying the manager was not recognised.

### 5. SHOULD - 'no reference in the exe' proves nothing about colour set names

RAN the same search the `abi` command does: `White`, `OnFocus`, `Black`, `WANTED`, `DirtyMoneyColorSet` have no
NUL-delimited string in kl2.exe at all - but `White` and `OnFocus` are used by 87 and many more XML elements, so the
test cannot tell 'unused'. What does hold: no XML element names the four spare sets (FILE, all three files), and the
one `Debug` string with a reference (0xbd7a6c) stands in `Debug\0Info\0W...` = a log-level table, not a colour
set (so risk 2 of the note can be struck). `Default` at 0xb69000 has 16 references: code does look a set up by
name. Say in the note that 'unused' rests on the XML only; KNOWN_WINDOWS / KNOWN_ELEMENTS are a lower bound.

### 6. SHOULD - the spare sets' disabled colour is written into an attribute the game does not read

EXE: kl2.exe holds `DisableColor` (0xb2c8b4, one reference) and no `DisabledColor`. online.xml's last four sets
(the second `Default`, `WANTED`, `DirtyMoneyColorSet`, `Black`) spell it `DisabledColor` (FILE), and the tool
rewrites that attribute in place. So the green and orange sets have whatever disabled colour the constructor
gives, not 4f8f49 / 8c3138. 92 elements now use `DirtyMoneyColorSet`; any of them that is ever sent `Disable`
(0x672ac0) shows that default. Add a real `DisableColor=` to the four (an attribute on an existing tag: no table
entry). Also: `WANTED`'s disabled alpha goes 00 -> ff, against the note's 'alpha kept'.

### 7. SHOULD - the look: the bars are perforated rectangles, not brush strokes

Looked at `sheet.png`. Each bar is a full-height rectangle with square ends, salt-and-pepper pinholes over the whole
face and 1-pixel full-height vertical cuts every ~170 px. That reads as a barcode / torn ticket; the owner's sheet
is 'solid chalk-white brush strokes with hand-cut edges' and he rejected speckle twice ('overdone'). Code: `top` /
`bot` are an independent 0-or-1 draw PER COLUMN (noise, not the 'wandering edge' the note describes); `gaps` cut
the whole height. And the task said to reuse kl_hud's stroke code by import - it was not, so the menu's bars and
the HUD's strokes (slots 111-118) are two different hands. Fix: import kl_hud's stroke painter, or at least: no
pinholes, edges that wander over 20-40 px runs, slanted hand-cut ends, dry streaks that start at an end and do not
cross the bar. `GREEN_INK` (money on a painted row, from the draft) is defined and never used.

### 8. SHOULD - things repainted or left that the note does not list

- FILE: tiles 958 / 959 (`FocusBar_medium`) are also the picture of `AssignKeyFocus_long` (key-assignment page),
  and `MenuFocus_long`'s DXT1 tiles of `FAFocusBar_long`. The first turns chalk too (its set `AssignKeys` has ink
  focus text: fine, but say it); the second stays stock grey beside chalk bars.
- `FocusBar_medium_02` (26 uses in frontend.xml) stays the stock grey 3-D bar with its groove: on the sheet it is
  the one object in the old look. The code comment at `return False` names `FocusBar_tap_*`; the bar actually
  skipped is `medium_02` (tap_01 / tap_02, textures 1001 / 1002, WERE repainted).
- The round-over page draws its separators in pairs 3 px apart (AnimY 309/312, 352/355, 395/398). Each line is now
  two rows at 3.2 x the stock brightness: the pairs may close into one band at 1440p. Watch in M3; LINE_ROWS = 1
  for the paired ones if so.
- The shop's fourteen `WeaponBuyFB` bars and the lobby's static bars have `AlphaMax="255"`: fully opaque chalk
  where stock had mid grey. Their row texts are coloured by code (`MercsFASelectorWeapons`); whether a locked /
  dimmed row is still readable on chalk is NOT ESTABLISHED - add it to M3's pass criteria.
- 'headings coral' (note, section 2): the 'Bonus' / 'Penalty' headings use `OnFocus` = ink on the bar. Coral is the
  `Header` set only.

### 9. NOTE - scope: the restyle is global, not Arcade-only

`menu/frontend.xml` and `menu/ingame.xml` live in Patch01.zip: the colours apply to the campaign's pause and
options pages and to the multiplayer pages as well; the menu scene's bars likewise. That matches the owner's 'for
the HUD AND the menus', but it is outside 'nothing on a stock level', so the lead should decide it knowingly. It
only exists while `[Expansion]` mounts the overlay. `Overlay_online` extends the colour change to stock levels'
round-over pages.

### 10. NOTE - `diff` hides half of every doubled colour set

`colorsets()` is a dict by name: for `Legend` (twice in every file) and online.xml's `Default` (twice) only the
LAST definition is printed. FILE: online.xml's first `Default` is `0xA0ffffff / 0xA0000000 / 0xff888888` and was
changed to chalk / ink / grey; the second (`0x99829EC1`, the bluish one) kept its normal colour. The note's risk 1
is right; the tool's own diff just cannot show it. Key the listing by (name, occurrence).

### 11. NOTE - what `check` cannot see

- Four stock tags the tool's tag pattern does not match (FILE: frontend.xml `InfocastGfxRight8`, ingame.xml
  `EndRound` twice - a KNOWN_ELEMENTS name - and `MFMfb#02`): they are outside the signature, the name tests and
  the restyle. Harmless today (untouched text, same in the reference), but the '4341 / 1590 table-making tags' are
  not the game's count, and a future edit inside such a tag would pass `check`.
- A reference with the same fault passes: `check <x> <its own source>` proves 'nothing moved', not 'sound'.
- No budget test (finding 1) and no `check` for a level archive (the note says so). Add `check-level <archive>
  <source archive>`: same XML tests, same texture-id test.
- Archives are written with `time.localtime()` on changed members: the sha1 in the note changes with every
  rebuild. Use a fixed stamp.

### 12. NOTE - smaller points

- EXE 0x7bb2a0 returns the rules object only while `[[0x168e598]+0x5c] == 4` (the mode klbalance.c line 376 calls
  Arcade). The note's 'it does not test which rules class it has' is true and misses this test; it makes 'the tags
  answer in Arcade' more likely, and raises the question what the multiplayer pages get from it (not looked at).
- `KLB_Fate<k>` is `Type="TextBlock" Text=""`: stock has 277 such elements (FILE), fine. Positions (`AlignH="Right"
  X=418 / -107` as '768 minus the right edge') are a guess the note owns up to.
- `Debug` in frontend.xml had alpha 0x80 normal; it is now 0xff. Intended for money, but it is not 'alpha kept'.

## Live checks, corrected order

1. **K0 (new, before everything that adds an element; no overlay change needed)**: the snippet of finding 4 at the
   main menu and at a round-over page of one of our maps, on the INSTALLED overlay. Log must show
   `menu: table N ...` with N for both. N <= 4952 in both places = `--board` has room; otherwise `--board` is dead
   as built.
2. M1 (`Overlay_nofonts`), M3 (`level_DM03`) as the note has them; add to M3: locked shop rows readable on the
   opaque bars, the paired lines still two lines, the key-assignment page's bar.
3. M4, M2.
4. T1 only after K0, with the board in a LEVEL archive (`level --board`), not in Patch01.zip; pass = names and
   scores on matching rows (check one known heister's money against the HUD), no fault with the mouse moved over
   the page background for 30 s.

A fault at 0x3f800000 from 0x8618b9 = entry 5000 is a window: read `ebx` in the dump, it will say 0x1388.
