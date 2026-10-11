# Review of track U - 'The Vault' (DM03A, slot F07) as the sixth entry of the 'Dead Men maps' page

Adversarial review, 2026-10-11 evening. OFFLINE: nothing was run in the game, nothing installed, nothing committed,
none of the worker's files changed (`tools/kl_expansion.py` still sha1 5eb93283). The review's scratch tree
(`G:\kl_scratch\U_review`) is deleted. Reviewed: the diff of `tools/kl_expansion.py` line by line, `klhook/klslot.c`
whole, `re/expansion.md` section 11, the builds under `<work>\build\q_vault\`.

## Verdict

**ACCEPT WITH FIXES.** No MUST in the worker's code or builds: the six-map tree is what the report says and the
five maps' packaging is unchanged. ONE MUST for the lead, about the state of the game folder (M1), and five SHOULD
points in the tool / the note.

## What was checked, and what came out

| check | result |
|---|---|
| five-map tree built with the changed tool, mk_ptab's arguments, DEFAULT, against `w_tabP`'s manifest | `RESULT: PASS`, 248 files both. The five `maps` entries identical in every key; every file under `Maps\`, `BuildInfo\`, `Hook\` and `Overlay\Scenes\` identical by sha1. DIFFERENT: `KLHook.expansion.ini` (five `.Picture=` lines more) and `Overlay\Patch01.zip` (frontend.xml 0dde5f61 instead of bdfe83b7). See S1. |
| the same with `--reuse --no-map-pictures` (four maps `--prebuilt`, DM09 kept by `--reuse`) | `RESULT: PASS`. `maps` list == w_tabP's, ini identical, frontend.xml bdfe83b7 = w_tabP's; the only differing file is `Overlay\Patch01.zip` and its members are w_tabP's by name and CRC (the container differs). DM09's `KLJoin.ini` is kept ('the folder's is kept'): the `--reuse` fix works. |
| `selftest` | 0 checks failed, `RESULT: PASS` |
| `check <w_tabQ>` / `menu <w_tabQ>` | exit 0, six maps 'accepted' / 'rules hold' |
| `Maps\DM03A` of w_tabQ | 31 archive members, same CRC and size in the same order as `q_vault\DM03A\F01_Main.zip`, every level member under `Scenes/Locations/F07/F07_Main.*`, no 'F01' in any name; the 18 files beside it and the four side files are the folder's by sha1 under the F07 name; the file set beside the archive is the same as DM09's against its stock slot (only `Loader_Sequence.*` falls back) |
| audit tie | content id of `q_vault\DM03A` recomputed: 761b966b = its `audit.json`'s |
| ini | `[Redirect.2] F07=DM03A` after the five, `[Page.2] F07=The Vault`, `F07.Picture=LevelPicture_DM03A`; the rest of the block is the five-map one |
| frontend.xml of w_tabQ against `hud_mappics`' (0dde5f61) | exactly two lines: `Graphic="LevelPicture_H07"` -> `LevelPicture_DM03A`, `/Menu/Online/Scenarios/Title07` -> `%The Vault`. No other member of Patch01.zip differs. |
| menu scene of the variant against `hud_mappics`' | one entity more (`LevelPicture_DM03A`), none removed; changed members .TEX .buf .gms .oct .prm .prp .rmc = the same set the five-picture variant changed against stock (that one is seen live) |
| the picture | `w_tabQ\pictures\DM03A.png` looked at: the 'US CREDIT BANK' front, whole, 540 x 304 |
| `audit_known()` called directly | refused: 'fa: BROKEN x', another verify problem, a preflight count that is not result.json's, any other preflight line. Accepted where it should not be: see S3 |
| klslot.c for slot F07 | holds as claimed: `kls_rules()` makes slot and key from the ini line (`\scenes\locations\f07\`, `f07_main.zip`), nothing is per slot number; the page is taken at each open of `<slot>_main.zip`, so stock F07 from page 1 after page 2 re-latches (the worker's M1 is the right control); 6 rules / 6 slots of 64 / 16; the latch line's buffer (200) holds six entries. No other hook file has slot-specific code (grep). Not provable offline: a level under the NAME F07 through the redirect - M0 .. M2. |

## MUST

**M1 (for the lead; not a fault of the worker's work). The game folder holds w_tabP's page NOW: the story pictures
are back on the owner's tab.** Read at review time: `<DD>\KLExpansion\Overlay\Patch01.zip` is 9a9ab0b2 =
`w_tabP`'s, its frontend.xml bdfe83b7 with `LevelPicture_L01 .. L06` on page 2 (`manifest.json` and `Overlay\` of
18:42, `dinput8.dll` 37949c06 of 18:46 - neither 71d133ae nor ship_main1). The scene beside it is still the
pictured one (5be87b0d), so only the page lost them. This is exactly the fault the worker found in w_tabP (11.2),
and it has since been installed. The report's and 11.3's 'the installed one is 0dde5f61' was true when written
and is not any more. To do: build the tab's tree again with the changed tool (default = pictures named) before the
owner looks at the page, or install `hud_mappics`' Patch01.zip beside the scene; correct the two sentences in
`re/expansion.md` 11.2 / 11.3 / 11.5 ('THE INSTALLED ONE', 'made from the installed overlay's scene' - the scene
yes, the page no).

## SHOULD

**S1. The default build is no longer 'exactly today's tree'.** The task asked for the same manifest as w_tabP's
without `--prebuilt DM03A`; with the default two files differ (table above), only `--no-map-pictures` gives
w_tabP's page. The change is right (M1 shows why) and the five maps are untouched, but it is a changed default of
the lead's `mk_ptab.py` command and must be said as such in CLAUDE.md when this goes in - not as 'nothing differs'.

**S2. `--maps <one id> --reuse` on a six-map tree deletes The Vault.** Tried on the scratch tree:
`build --out <tree> --reuse --maps DM01 ...` printed 'DM03A: not asked for (no --prebuilt DM03A=...): Maps\DM03A
removed from the tree' and left five maps, while DM02 .. DM09, equally not named, were kept. Cause: `extra` wants
`(not only or id in only)` before `reuse and held(m)`, and everything of EXTRA not in `extra` is removed. Fix:
remove a held opt-in map only when `only` is empty (a full build that does not ask for it); with `--maps` leave
it as the five are left. (The run also ends 'RESULT: FAIL - ' with no reason: entries 5 against maps 1 - that
part is older than this track.)

**S3. The known finding is a substring without its number.** `audit_known()` and `verdict()` accept any problem
that CONTAINS 'stream clips are not in the merged stream file': 'verify: sound: 400 stream clips ...' is accepted
like '10', and so is one line that carries a second finding beside the phrase (both tried). Today's audit holds
exactly the two known lines, so the tree is right; but a later rebuild of the bank that loses more clips would
pass unseen. For an `audit=True` map pin it: the whole line, or the count as an upper bound (10) in EXTRA.

**S4. The acceptance was loosened for the five maps too.** Before, any line of a folder's `audit.json` 'bad'
list refused the map; now `audit_known()` runs for every map, so DM09 (known: stream clips, particle template
names) passes an audit that lists those as 'verify:' lines plus the quoting preflight line. No effect on
p_tab / w_tabP (mk_ptab deletes the folders' audit.json; `audit_known` absent from all five entries), and
consistent with what `verdict()` already did on result.json - but it is a change in the five's packaging rule and
is not in the report. Either gate it with `m.get('audit')` or say it in 11.

**S5. Small things in the note and the tests.**
- 11.5 step 1 says the Vault gets 'the story picture LevelPicture_L07' before `mappics`; confirm against
  mkoverlay (story mode -> L07; the five-map page shows H07 for the unmapped entry) - one of the two names in the
  section is loose.
- The docstring says 'mkoverlay.py and klslot.c know pages 2..5': klslot.c takes 2..9, mkoverlay 2..5.
- `selftest` installs / uninstalls only maps of MAPS: no check covers a tree with an opt-in map (slot F07 beside
  the stock F07 files, update from six to five removing `Maps\DM03A`). 11.6's 'an update removes the files the new
  tree lacks' is read, not tested, for this case.
- With `--reuse` the audit is tied to the files only through `adopted.json` of the first build (content id of the
  SOURCE folder then); a file changed inside the tree afterwards is not seen by the build (the manifest is
  rewritten from what lies there). Same as for the five; the rule 'never edit a file inside a tree' covers it.
- A build that names `--ready <dir>` together with `--reuse` takes the maps from the ready folder, not the tree
  (seen by accident in this review: DM01 .. DM06 came from z_route). Older than this track; 11.5 step 3 rightly
  has no `--ready`.

## Not in doubt

- The opt-in: no `--prebuilt DM03A` and no held copy -> five maps, five entries, five redirect lines.
- An unknown finding refuses the map (four negative cases), and so does a missing or foreign `audit.json`
  (code read: three separate reasons; the worker's three exit-1 trials match it).
- `install` and its manifest check are not touched by the diff and use no fixed map list.
- The fed's place on this map (front street) and the silent stream clips are stated as they are; both are the
  owner's to judge.
