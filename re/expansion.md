# The expansion as a package: layout, build, install, menu, sizes

Written 2026-10-09 (agent i-pack). **Offline only: the game was not started and nothing was written to
the Dog Days folder.** Tool: `tools/kl_expansion.py`. Everything it builds lives in the work folder
(`<work>\build\expansion\`); no game data is in the repo.

Words: **built / measured / tested** = done here, with the command; **live** = seen in the game by an
earlier agent (run names are those of `tools/kl_graft.py`'s log); **NOT LIVE** = nobody has run it;
ASSUMPTION = not established by anyone.

## 0. Short answers

1. `python tools\kl_expansion.py build` makes one relocatable folder `KLExpansion` with all five maps,
   the menu page, the merged stream file, the hook and a manifest. Last run: 5 maps accepted, 128
   files, 3.40 GB, `RESULT: PASS` (section 2).
2. Each map is built **for the stock slot its menu entry loads** (F01 F02 F03 F04 F06) and lives in
   `Maps\<id>\`; the hook answers the opens of that slot from there while menu page 2 is chosen.
   Nothing stock is replaced. The bank's build here is, member for member, the one that ran live from
   `Maps\DM03` (same build id); the diner's and Retomoto's equal their kept live builds too.
3. `install` / `uninstall` are written and tested against a made-up game folder (31 checks) and once
   with the real 3.4 GB tree in a made-up folder. Both refuse while a `kl2.exe` with a thread exists.
   `KL_PortBackup` is only read.
4. Menu: page 'Dead Men maps' with the five titles is generated and passes the rules of
   `re/menus.md`. **Dead Men does ship a menu picture for every one of these maps**; they are converted
   to Dog Days' picture form (six DXT5 tiles), but not yet shown: a new picture needs an entity in the
   frontend scene (section 4.2). Until then the page shows the stock picture of each slot.
5. Sizes: a map is 356 - 383 MB. **About 150 MB of each archive is F07's own map, which the joined
   level never references** (measured, section 5) - 719 MB of the 1.83 GB of maps. That is where space
   is; sharing the live systems part between maps would save a further ~320 MB at most and needs the
   hook to serve virtual files. Not implemented, by instruction.
6. Still test-only: everything about the page (never opened in the game), builds under the slot names
   F02 F03 F04 F06, the stream file through the overlay, the hook build in the tree, Retomoto's join.
   Section 6 has the list, section 7 the live checks in order.

## 1. Layout

```
<Dog Days>\
  dinput8.dll                       KLHook, SHIP build (the tree carries it as Hook\dinput8.dll)
  KLHook.ini                        gets the block of KLHook.expansion.ini between two marker lines
  KLExpansion\
    manifest.json                   what is in the tree (below)
    KLHook.expansion.ini            [Expansion] [Redirect.2] [Page.2] - what klslot.c and mkoverlay.py read
    Maps\DM01\  F01_Main.zip  .WHD .WAV .hti  F01_Main_LS.SND  F01_Main_LS_<Language>.WHD/.WAV   Hot Coffee
    Maps\DM02\  F02_Main.*                                                                     Late Night Opening
    Maps\DM03\  F03_Main.*                                                                     Withdrawal
    Maps\DM06\  F04_Main.*                                                                     A Walk in the Park
    Maps\DM09\  F06_Main.*  KLJoin.ini                                                         Retomoto Tower
    Overlay\Patch01.zip             the stock patch archive + the page (menu/frontend.xml)
    Overlay\PC_Def.str              the merged stream file (Dog Days' + Dead Men's streamed clips)
    BuildInfo\<id>\                 graft.txt, result.json, log.txt, stdout.txt, preflight.json/.txt
    _installed\                     written by install: install.json, KLHook.ini.before, dinput8.dll.before
  Scenes\, Patch01.zip, PC_Def.str, KL_PortBackup\      not touched (but see 3.3 for the owner's folder)
```

| id | name (Dead Men's own) | sources | slot | page entry | build |
|---|---|---|---|---|---|
| DM01 | Hot Coffee | M01_FA_A | F01 | 0 | `kl_maps.one('F07', M, slot=...)`, kl_graft defaults |
| DM02 | Late Night Opening | M02_FA_A | F02 | 1 | the same |
| DM03 | Withdrawal | M03_FA_A | F03 | 2 | the same |
| DM06 | A Walk in the Park | M06_FA_A | F04 | 3 | the same |
| DM09 | Retomoto Tower | M09_B + M09_A | F06 | 4 | F07 + M09_B as level R09, then R09 + M09_A; campaign pre-pass and `kl_fa_author`'s layer (= `kl_fa_author.test`) |

Why these slots: entry k of a map page loads slot `{F01,F02,F03,F04,F06,F07,F05,F08,F09}[k]`
(kl2 0x746570) and the engine keeps loading `Locations/<slot>/<slot>_Main`; the archive in `Maps\<id>`
therefore carries the slot's member names (`re/slot_redirect.md` mode C, the only mode that ran live).
F05, F08, F09 are the paid DLC slots (`re/fa_slots.md` 1) and are never redirected. That leaves six
entries a page; the five maps take the first five, entry 5 (F07) and the three DLC entries keep their
stock title and stock level on our page. A sixth map fits; a seventh needs page 3 (`[Redirect.3]`,
mkoverlay has room for pages 2 - 5).

The ini block (the same file feeds the hook and `klhook\mkoverlay.py`):

```ini
[Expansion]
Enable=1
Root=KLExpansion
Overlay=1
Fallback=1
Log=1
[Redirect.2]
F01=DM01
F02=DM02
F03=DM03
F04=DM06
F06=DM09
[Page.2]
Title=Dead Men maps
F01=Hot Coffee
...
```

Only `[Redirect.2]`, no `[Redirect]`: the stock page and a direct boot load the stock levels. For a
direct-boot test of a map add `Page=2` under `[Expansion]` (and, for a slot other than F01, klauto's
`CmdDrop=DefaultScene` / `CmdAdd=-o DefaultScene=Locations/F03/F03_Main.gms`).

`Loader_Sequence.*` is not in a map folder: with `Fallback=1` the stock slot's own loading sequence is
used (live for F01 in run X2).

### manifest.json

`format, name, built, root, page {number, title, option}`; `tools {commit, branch,
changed_since_commit {file: sha1}}` (the tree of 2026-10-09 was built from commit 57fb690 plus 12
uncommitted files of three agents - the manifest names them); `needs {kl2.exe sha1, systems level
archive sha1, stream_file {sha1, bytes, in_tree}, hook {sha1, bytes, test_build, steam_write_guard}}`;
`maps[]`: `id, name, slot, menu_entry, folder, scene, systems_level, source_levels, build, options,
build_id, accepted, problems, known_problems, fa_check, fa_findings, preflight, live, numbers
(archive / beside MB, entities, rooms, textures, materials, chunks, sounds, waves, nav bytes), bytes,
extra_files`; `menu` (the rule check); `pictures`; `steam` (one sentence: guarded or not); `files
{relative path: {sha1, bytes}}`; `total_bytes`, `bytes_by_part`. No absolute path is in it.

**build_id** = sha1 over the archive's members (name without the slot, CRC, size - not the zip's bytes,
which hold the build time) and the sha1 of every file beside it except the `.hti` (name without the
slot). The same content built for another slot has the same id: the F03 build here and the F01-named
copy in `<DD>\KLExpansion\Maps\DM03` both give `2274a15ee3e2...` (measured). This is the number two
peers must compare before an online session (`re/netcode.md` 5: the game's own check does not know
our files); nothing compares it yet.

## 2. Building

    python tools\kl_expansion.py build [--out <folder>] [--maps DM01,DM03] [-j 2] [--reuse]
                                       [--hook <dinput8.dll>] [--no-stream] [--no-share] [--no-pictures] [--bones]
    python tools\kl_expansion.py check | menu | share | pictures

What it does: each map in a process of its own through `kl_maps.one` (which never writes
`<work>\build\install`), two at a time; verdict per map; the ini block; `klhook\mkoverlay.py` on the
stock `Patch01.zip` (read only) and the rule check of section 4; copy of `<work>\build\PC_Def.str`;
the hook given with `--hook` (refused unless it holds klslot's page texts); pictures; the sharing
measurement; the manifest. Exit code 1 when a map has a `verify()` problem outside its known list, a
`kl_fa.check` finding CRASH / BROKEN, or the page breaks a rule. Five maps take 4.5 minutes;
`--reuse` (everything but the graft) 1.5.

Options: kl_graft's defaults, i.e. the builds that ran live, **plus `bones=False`**. kl_graft gained a
skeleton-renumbering step (`bones=True` by default, another agent's change of 2026-10-09 12:40) while
this was being built. With it on, its own new check fails every map but the bank (first build of this
session: DM01 1, DM02 1, DM06 5, DM09 10 'skeleton N: bones [...] are not in the .ANM bone table'), and
it has not run live. `--bones` turns it on once the lead accepts it.

Result of the last full build (`build -j 2`, then `build --reuse --hook <ihook SHIP>`):

| id | problems | kl_fa.check | preflight | archive MB | beside MB | entities | rooms | textures /4096 | materials /2048 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| DM01 | 0 | 4 DEGRADED, 2 NOTE | CRASH 0, RISK 0 | 336.4 | 46.8 | 14,999 | 12 | 1,999 | 1,354 |
| DM02 | 0 | 4 DEGRADED, 2 NOTE | CRASH 0, RISK 3 | 310.3 | 47.5 | 21,934 | 32 | 1,697 | 1,076 |
| DM03 | 0 | 5 DEGRADED, 2 NOTE | CRASH 0, RISK 0 | 321.1 | 47.7 | 19,827 | 20 | 1,864 | 1,193 |
| DM06 | 0 | 3 DEGRADED, 2 NOTE | CRASH 0, RISK 2 | 310.1 | 46.2 | 15,599 | 7 | 1,576 | 995 |
| DM09 | 2, both known | 1 DEGRADED | not run (kl_maps.preflight takes one S and one M) | 312.4 | 48.3 | 25,489 | 22 | 2,195 | 1,429 |

DM09's two known problems are `kl_fa_author.KNOWN`: '39 particle template names do not resolve (stock
M09_A: 36)' and '13 stream clips are not in the merged stream file' (its music among them,
`re/retomoto_audio.md`). The RISK lines are the first-time classes of `re/maps.md` 9.3 (ZEnvSampler,
SoundSpline, SoundVolumetricRandom); those maps ran live with them (M02c, M02r, M06a, M06r).

Against the kept builds that ran live (members by CRC and size, files beside by sha1; measured):

| id | kept live build | differs in |
|---|---|---|
| DM01 | `<work>\build\h_m01` (11:57; run M01W) | nothing |
| DM02 | `<work>\build\v_maps\F07+M02_FA_A` (09:23; runs M02c, M02r) | `.prp` only - kl_graft changed after 09:23; which fields was not looked at |
| DM03 | `<DD>\KLExpansion\Maps\DM03` (10:57; the final bank build) | nothing |
| DM06 | `<work>\build\v_maps\F07+M06_FA_A` (09:23; M06a, M06r) | `.prp` only, as DM02 |
| DM09 | `<work>\build\h_rt\R09+M09_A ...` (12:06; run RT6) | nothing |

(The F01 slot and `<work>\build\install` held a newer bank build at 12:34 whose `.prm` differs from
all of these: the skeleton step, somebody else's test.)

## 3. Install and remove

### 3.1 For a player

1. Both games installed (the maps are built on the player's machine from the player's own files;
   nothing of either game is distributed). `python tools\kl_expansion.py build`.
2. Close the game. `python tools\kl_expansion.py install` (add `--link` to save 92 MB).
3. In the game: Arcade Mode -> **Dead Men maps** (the sixth button) -> left / right -> Accept.
   The stock button and its nine maps are unchanged.
4. Remove: `python tools\kl_expansion.py uninstall`. The game folder is then what it was before the
   install, except that the F01 slot holds the stock files (which only matters on the owner's machine).
   By hand: delete `dinput8.dll`, `KLHook.ini` and the folder `KLExpansion`.
5. `python tools\kl_expansion.py status` says what is installed and how the folder differs from stock.

### 3.2 What install does, in order

1. Refuses when `--game` holds no `kl2.exe`, when a `kl2.exe` process with at least one thread exists
   (Toolhelp snapshot; the thread-less entries Windows keeps of crashed runs, 21 on the owner's
   machine, are reported and are no reason to refuse - `debug\zombies.py`), when the tree lies inside
   the game folder, when a file of the tree differs from the manifest, or when a map was not accepted.
2. A `KLExpansion` folder that is not an install of this tool (no `_installed\install.json`) is
   refused; with `--replace` it is MOVED aside as `KLExpansion.before-N` and moved back by uninstall.
   (The owner's folder has one: `Maps\DM03` of the live tests.)
3. Copies the tree but `Hook\` (every file through a temporary name, read back, sha1 compared).
   `--link`: byte-equal files of two maps become hard links. `--no-stream`: without `Overlay\PC_Def.str`.
4. Hook: `Hook\dinput8.dll` replaces `<DD>\dinput8.dll`; the one that was there is copied to
   `_installed\dinput8.dll.before`. A locked file is renamed aside (`dinput8.dll.locked-N`), never
   deleted. `--no-hook`, or no DLL in the tree: the game's own is checked for klslot's page texts and a
   warning is printed.
5. `KLHook.ini`: sections `[Expansion] [Redirect] [Redirect.N] [Page.N] [Slots]` of the existing file
   are taken out, the tree's block is appended between two marker lines; every other section
   (`[KLHook]`, `[Auto]`, `[Script]`, `[Steam]`, `[Join]`) and every comment stays. CRLF. The file as
   it was is kept as `_installed\KLHook.ini.before`.
6. Unless `--keep-slot`: the F01 test slot is made stock **by copy** from `KL_PortBackup` (a file
   already equal to its backup is skipped).

Uninstall undoes 5, 4, 3, 2 and repeats 6. `KLHook.ini` goes back byte for byte when nobody changed
it since; else only the marked block is removed and the earlier file is left beside it as
`KLHook.ini.before-expansion`. A hook that is not the one install put there is left alone. Files in
`KLExpansion` that the tool did not put there stay, with their folder. `--restore-all` copies EVERY
file of `KL_PortBackup` back (`PC_Def.str` too). `KL_PortBackup` itself is never written, moved or
removed by any command.

An install over an install is an update: files the new tree lacks are removed, what the FIRST install
replaced stays what uninstall puts back.

### 3.3 The owner's folder as it is now (`status`, read only, 2026-10-09)

`KLExpansion\Maps\DM03` (not ours), `dinput8.dll` 7e806e6c... (no pages), `KLHook.ini` with `[KLHook]`
only; replaced stock files: the F01 slot (19 files) and **`PC_Def.str`** - the merged stream file
(1,575,448,788 bytes, sha1 62349cb6...) stands where the stock one (1,217,890,070 bytes) was since
2026-10-08. The merged file is not the stock file plus a tail (the first 1.2 GB hash differently), so
it is a replaced stock file like any other. The tree therefore carries it as `Overlay\PC_Def.str`;
once check L4 below has shown that the game takes it from there, `uninstall --restore-all` puts the
stock one back and nothing stock is replaced any more. Until then leave it: the maps' streamed clips
index the merged file.

### 3.4 Tested

- `python tools\kl_expansion.py selftest <scratch>`: a made-up game folder (dummy `kl2.exe`, a test
  build in the F01 slot with its stock files in `KL_PortBackup`, an old hook, an ini with `[Auto]` and
  stale `[Expansion]` / `[Redirect]` sections, a foreign `KLExpansion`) and a made-up tree. 31 checks,
  `RESULT: PASS`: both commands refuse while the game runs and nothing changes; foreign folder, missing
  exe and tampered tree are refused; install copies, links, merges the ini, swaps the hook, restores the
  slot; `KL_PortBackup` and every stock file outside the slot are byte-identical afterwards; update;
  uninstall returns the folder to its start but for the slot; clean folder; edited ini; `--restore-all`.
- The real tree into a made-up folder in scratch: `install --game <fake> --link` copied 126 files
  (3.40 GB, 32 as hard links) in 11 s; `status` 'all as built'; `uninstall`; a sha1 list of the folder
  before and after differs in one line, the F01 archive (stock again).
- NOT tested: the real game folder (by instruction), a hook DLL that is really locked.

## 4. The menu

### 4.1 The page

`klhook\mkoverlay.py <tree>\KLHook.expansion.ini <stock Patch01.zip> <tree>` writes
`Overlay\Patch01.zip`: the stock members, `menu/ingame.xml` byte for byte, and a `menu/frontend.xml`
(666,602 -> 673,647 bytes) with one more window `HeistPlayMenu2` (a copy of the stock map page with
the headline 'Dead Men maps', five literal titles, no briefing element) and, on the Arcade page, the
option `Dummy=1` on the stock button and a sixth button 'Dead Men maps' (`Dummy=2`, focus bar
`FocusBar_short#06`, Y 390).

`python tools\kl_expansion.py menu` checks it against `re/menus.md` (all hold):

| rule | source | result |
|---|---|---|
| the archive has the stock members; all but `menu/frontend.xml` are the stock bytes | `re/slot_redirect.md` 2 (a COMPLETE patch archive) | holds |
| exactly one new window name; of the stock windows only `HeistModeMenu` changed; no name used more often than in stock | - | holds (stock itself uses three names twice: `QuickJoinInterlude`, `QuickPlayerMatch`, `OverwriteSaveConfirmation`) |
| the selector has nine `<Text>`, in slot order 1 2 3 4 6 7 5 8 9; ours are `%literal`, the rest the stock keys | 4.3, 8.1 (nine is in code), 2.6 | holds |
| a title is plain ASCII without `& " < >`, at most 48 characters | 2.6; mkoverlay's `esc` | holds |
| no DLC slot (F05 F08 F09) carries one of our maps | `re/fa_slots.md` 1 | holds |
| the picture toggler has nine `<Graphic>` naming elements of the page | 4.1 | holds |
| every `Graphic=` of a picture and of the new focus bar is an entity of the frontend scene | 2.7 (names read from `Scenes/kaneandlynch.gms/.buf`) | holds |
| no `HeistBriefing` element (it would print the stock map's briefing) | 8.2 | holds |
| element names unique inside the page | - | holds |
| the new button has a focus bar and a row of its own; map-page buttons are exactly `Dummy=1` / `Dummy=2` | 3.1, 8.2 | holds |
| element table of 5096 | 2.5 | **44 tags added** to 4,542 (frontend.xml) + 2,076 (online.xml) raw `Window / GuiElement / ColorSet / ButtonGraphic` tags. The stock total already exceeds 5096 and runs, so a tag is not a slot; the headroom is NOT established. Limit used here: no more than 100 added. Live check L5 reads the real count |

What the page still shows of the stock map of each slot: its picture, its 'criminal name' rows, the
lobby title (code, `Title%02i`), and in the round the HUD's level name where it prints one.

### 4.2 Pictures

Dead Men's frontend scene (`Scenes\KaneAndLynch.zip`) holds `ROOT\LocalResources\Graphic\
LevelPicture_FA01 / FA02 / FA03 / FA06` (the four Fragile Alliance maps) and `LevelPicture_M09A /
M09B` (the Retomoto chapters), beside the story ones. Each is a `ZWINGROUP` with a `ZWINPIC` child
`Box`; its field `ZWINPIC[2]` is a 'winpic' chunk of the `.prm`: n tiles {centre x, centre -y, 0, 0,
u, v, 0, width, height, -1}, then n sprite chunks whose +4 is a texture id. Read from the files:

| | Dead Men | Dog Days Arcade (`LevelPicture_H01..H09`) |
|---|---|---|
| size | 891 x 530 | 540 x 304 |
| tiles | 9: 512 / 256 / 123 wide, 512 / 16 / 2 high | 6: 512 / 28 wide, 256 / 32 / 16 high |
| textures | DXT1, 512 / 256 / 128 x 512 / 16 / 8, flags 0x4000 | DXT5, 512 / 32 x 256 / 32 / 16, flags 0, opaque |
| content | a photograph of 384 x 236 at (277, 169) on a black sheet with paint splashes | the picture fills the rectangle |

(Dog Days' lobby pictures `LevelPicture_F01..F09` are a third form: six uncompressed RGBA tiles in
textures 256 / 64 / 8 wide and 128 / 64 high; their picture size was not read. Not converted: the page
is an Arcade page.)

`python tools\kl_expansion.py pictures` (part of `build`) cuts the photograph out, cuts it to 16 : 9,
scales it to 540 x 304 and writes per map `<out>\pictures\<id>.png` and `<id>.tiles`: six texture
records in Dog Days' `.TEX` record form with the stock tiles' sizes and header fields (id 0). Looked
at: DM01 is the diner's counter, DM02 the 'Hertzer & Sons' jewel shop, DM03 the 'US Credit Bank'
front, DM09 the tower among the skyline (FA06 shares its textures with the story picture M06). The
DM03 tiles were decoded again and give the same picture. The photograph is scaled up 1.4 x, so it is
softer than a stock picture.

NOT DONE - the entity. `Graphic="..."` names an entity, so a new picture needs, in the frontend scene:
a `ZWINGROUP` + `ZWINPIC` (a copy of `LevelPicture_H01` and its `Box`) in `.gms` / `.buf` / `.prp`, one
winpic chunk and six sprite chunks in the `.prm`, six textures in the `.TEX` (30 new ids for five
maps), delivered as `Overlay\Scenes\kaneandlynch.zip` (its `.TEX` alone is 85 MB).
The modules exist (`kl_scene.graft`, `kl_prmgraph.append`, `kl_texmat.merge_tex`), but the frontend
scene has never been re-serialised or loaded from an overlay, so it is a live-tested job of its own.
Then: `F01.Picture=LevelPicture_D01` ... in `[Page.2]`; mkoverlay already takes that key.
Replacing the texture of a stock `LevelPicture_H0n` instead would change the stock page: not done.

## 5. Sizes, and what could be shared

Measured on the built tree (`python tools\kl_expansion.py share`, `<out>\share.json`):

| part | bytes |
|---|---:|
| five maps | 1,826,614,802 (356 - 383 MB each: archive 310 - 336, beside 46 - 48) |
| `Overlay\PC_Def.str` | 1,575,448,788 |
| `Overlay\Patch01.zip`, hook, ini, BuildInfo | 0.4 MB |
| total | 3,402,481,864 |

Inside an archive (unpacked; packed is deflate level 1, as kl_graft writes it):

| | .TEX | of it F07's | F07's that nothing in the joined level names | the map's | .prm | F07's | F07's vertex data no root reaches | the map's |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| stock F07 | 281 MB | 281 | 2 (8 textures: the floor of the method) | - | 63 MB | 63 | 0 | - |
| DM01 | 413 | 281 | 201 | 132 | 80 | 63 | 42 | 17 |
| DM02 | 386 | 281 | 201 | 105 | 80 | 63 | 42 | 17 |
| DM03 | 387 | 281 | 201 | 106 | 86 | 63 | 42 | 23 |
| DM06 | 374 | 281 | 201 | 93 | 75 | 63 | 42 | 12 |
| DM09 | 406 | 281 | 189 | 125 | 59 | 22 + 40 already emptied by `PRM_LIMIT` | 0 | 37 |

How: textures of the built `.TEX` are matched to stock F07's by content; 'named' = reached from the
level's roots (`.gms` models, `.prp` chunk fields) through `kl_prmgraph.walk` to materials, sprites,
fonts, plus the HUD's 200 picture ids and animation frames. On stock F07 itself that leaves 8 textures
unnamed, so the method is tight. `.TEX` (244 - 269 MB packed), `.prm` (30 - 43), `.ANM` (17), `.fxc`
(4) are all but 4 MB of an archive; no large member is a stock member byte for byte (0.09 MB of small
ones are; 1.4 MB in DM09).

So of each ~320 MB archive:
- **about 150 MB packed (117 for DM09) is F07's own map** - 201 MB of textures and 42 MB of vertex
  data of the map that was removed from the scene. 719 MB over the five maps.
- about 80 MB packed is F07's live systems (80 MB of textures and 21 MB of models unpacked, most of the
  17 MB `.ANM`, the 4 MB of shaders): the same in every map. An estimate from the member ratios.
- the rest is the Dead Men map.

**Is a 300 - 400 MB archive per map unavoidable? No - but the saving is in trimming, not sharing.**

1. *Trim F07's dead map at build time* (kl_graft's owner; safe in kind, NOT LIVE in this extent):
   `PRM_LIMIT` already empties unreached vertex / index chunks above 90 MB and Retomoto runs that way
   (RT2b - RT6); doing it always saves 42 MB unpacked per map. The same idea for textures - a
   texture no reference reaches becomes a 4 x 4 stub with its id kept - saves about 200 MB unpacked.
   Risk to measure first: the 8 unnamed textures of stock F07 show that some referrer is unknown; keep
   every texture that stock F07's own systems side names or that is in that floor set. Expected
   result: archives of about 160 - 190 MB, the five maps about 1.1 GB instead of 1.83 (an estimate:
   packed size taken as proportional to unpacked size per member; nothing was removed to try it).
2. *Hard links for equal files beside the archives* (implemented, `install --link`, tested): the 14
   `_LS_<Language>` files and the `.hti` are byte-equal in all five maps (they are F07's): 92 MB.
   Invisible to the game (read-only opens).
3. *The systems part once on disk* would need the game to read one member from two places. It cannot:
   a level is ONE archive (the loader mounts `Patch01.zip` and the scene's own zip, kl2 0x7f5610 /
   0x7f5827), every member is one file with one id space (`.TEX` table of 4096, `.prm` chunk table,
   `.MAT` slots), and member names carry the slot. The only way is the hook serving a virtual
   `<slot>_Main.zip` (stored members, a shared segment + a map segment) by wrapping `ReadFile`,
   `SetFilePointer`, `GetFileSize` and the async reader for those handles. That is new code on the
   hot path of every load, for about 80 MB x 4 = 320 MB. Not recommended before 1 is done.
   (One `.TEX` for all maps does not work either: every map would load every texture - the loader
   takes the `.prm` as one heap block and 100.9 MB was already refused once, run RT1.)
4. *Distribution* is not a size problem: nothing is shipped but tools; `build` runs on the player's
   machine against both installed games.
5. `Overlay\PC_Def.str` is 46 % of the tree. It is Dog Days' own 1.22 GB plus Dead Men's clips, rewritten;
   an append-only merge (stock bytes untouched, new clips behind them) was not what `kl_audio.merge`
   produced. Whether the stream format allows one was not looked at.

## 6. What is still test-only

| item | state |
|---|---|
| Maps opened from `Maps\<id>` in a real session | live for F01 only (X2, X3: `[Redirect] F01=DM03`) |
| builds named for F02, F03, F04, F06 | NOT LIVE. They differ from the F01 builds in member and file names only (kl_graft `member_name`); the engine derives a level code from the name (F01 = 14 .. F09 = 22, `re/fa_slots.md` 2) and files the round under the slot (board, local list). ASSUMPTION that nothing else is keyed on the slot |
| the page: sixth button, `Dummy` stored before the load, `[Redirect.2]` latched at the archive open | NOT LIVE (klslot.c says so) |
| `Overlay\Patch01.zip` taken instead of the stock one | NOT LIVE (the open through `CreateFileA` at boot is live, X2) |
| `Overlay\PC_Def.str` taken instead of the game's | NOT LIVE. X2 logged the open of `PC_Def.str` at boot through a wrapped import, so the overlay rule sees it; a 1.5 GB stream read through the redirected handle has not been tried |
| the hook in the tree | SHIP build of i-hook, sha1 884a9133... (klsteam + kljoin + klslot): built and off-game tested by its author, NOT LIVE (`re/hook_live.md`). Rebuild and restamp: `build --reuse --hook <dll>` |
| Steam writes | with that hook: uploads, stats, achievements of a level that is not the stock level of its slot are failed (klsteam.c) - NOT LIVE. The local high-score list of the slot (profile) is NOT guarded (`re/leaderboard.md` 4.3). With an older hook: never end an Arcade session on these maps |
| Retomoto Tower | loads and runs rounds (RT5, RT6); the way from tower to lobby is `Maps\DM09\KLJoin.ini` + kljoin.c - NOT LIVE from inside the process; the start in sight of seven guards is an owner decision (`re/retomoto_fa.md` 9.6); music silent (13 clips not in the stream file) |
| a whole round with loot and escape | bank only, and only on the build without the map's guards (ESC3); `kl_fa.check` DEGRADED on every map: no bot squads, no HUD markers, no spawn points of the Dog Days-only modes |
| the Fragile Alliance LOBBY (online / LAN) | not part of this: the page is an Arcade page; a lobby client maps the slot index through its own files (`re/slot_redirect.md` 5) |
| pictures | converted, not shown (4.2) |
| loading screen and briefing of an expansion map | the stock slot's |
| uninstall on the real folder | not run (by instruction) |

## 7. Live checks, in order (one variable each; `python debug\zombies.py --count` before and after)

Before L1: finish `re/hook_live.md` S0, S1 (the new hook in a session). All runs: klauto TEST DLL
unless said, end by `pass` at the score page, never let a session end.

- **L0 - install, by the tool, on the real folder.** `python tools\kl_expansion.py status`, then
  `install --replace --keep-slot --no-hook` (the live agent keeps its own DLL, ini head and slot build;
  `--replace` moves the old `KLExpansion\Maps\DM03` aside). Expect 'N files in ...KLExpansion', the ini
  block added, `status`: 'all as built'. Nothing loads differently yet if the run's ini has `Enable=0`.
- **L1 - nothing changes on the stock page.** Menu route of `KLHook.round.ini` (stock button, entry 0),
  the block of the ini in place. Expect `expansion: enabled`, five `[Redirect.2]` lines with the files
  each folder has and 'stock Loader_Sequence.* has no counterpart: the STOCK file will be used', `menu
  page option is 1`, `slot F01: menu page 1 from now on -> the stock level` - and whatever the F01 slot
  holds loads. (If the page option stays 0: the stock button's `OptionValue` is not stored - the
  open point of klslot.c.)
- **L2 - the page exists.** Script stopped on `HeistModeMenu` (`windows`, a shot): a sixth button 'Dead
  Men maps' under the five. Then `tap DOWN` x5, RETURN, `waitwin HeistPlayMenu2`, a shot: headline
  'Dead Men maps', title 'Hot Coffee', a picture (Subway's). `tap RIGHT` four times with shots: 'Late
  Night Opening', 'Withdrawal', 'A Walk in the Park', 'Retomoto Tower', then 'Financial'. A crash here
  with `int3` at 0x7fad8d / 0x667e6e is the element table (L5).
- **L3 - the bank from the page** (entry 2 = slot F03: the one build that is the live-proven one, so
  the only new things are the slot name and the page). `sel HeistLevel 0xceceec 2`, `msg HeistLevel
  StartGame`. Expect `menu page option is 2`, `slot F03: menu page 2 from now on -> DM03`, `redirect:`
  lines for `F03_Main.zip`, `_LS` files, later `.WHD` / `.WAV`; with the SHIP-policy hook `steam: level
  archive f03\f03_main.zip opened from ...\Maps\DM03\...: NOT stock` and '... BLOCKED'; the bank plaza,
  HUD, a round. Compare with RN13.
- **L4 - the stream file through the overlay.** Same run with `Log=2` once: expect `overlay: ...\
  PC_Def.str -> ...\KLExpansion\Overlay\PC_Def.str` at boot and sound in the level as before. Only
  after that may the stock `PC_Def.str` go back (`uninstall --restore-all`, or a copy by hand) - then
  repeat L3 and listen: with the stock file in the game folder and no overlay the maps' streamed clips
  would be wrong.
- **L5 - the element count**, any run that reaches the main menu: klauto's chained `peek
  0xdd265c+0x824+0x9f48 elements` (= `[[[0xdd265c]+0x824]+0x9f48]`, `re/menus.md` 2.5) with and without
  the overlay (two boots). Record both numbers in `re/menus.md` 2.5: it turns 'headroom not
  established' into a number.
- **L6 - the other maps from the page, one run each**: entry 0 (DM01, slot F01 - also the first menu
  round of the diner), entry 1 (DM02, F02), entry 3 (DM06, F04), entry 4 (DM09, F06; with J1 / J2 of
  `re/hook_live.md` for the join - `KLJoin.ini` is already in `Maps\DM09`). Expect the map of the
  title, `slot F0n: menu page 2 from now on -> DM0n`, and per map what its F01 build showed (run names
  in the manifest's `live`). These are the first loads of builds named for F02, F04, F06.
- **L7 - a slot is the stock map again after the page was used.** Two boots are the plain form: L3,
  then a boot through the stock button and entry 2 - expect `menu page option is 1`, `slot F03: menu
  page 1 from now on -> the stock level`, and Airport. The stronger form is both in ONE process (the
  latch is per archive open): it needs a way from a running round back to the frontend that does not
  end the session, which is not known - if there is none, say so and keep the two-boot form.
- **L8 - SHIP hook** (`Hook\dinput8.dll` of the tree, the plain block, no `[Auto]`): the owner plays
  one round on a Dead Men map from the page; `re/hook_live.md` S3 / S4 lines.
- **L9 - uninstall**: `uninstall` (and `--restore-all` once L4 has passed). Expect `status`: no
  KLExpansion (or the old folder moved back), the earlier hook and ini, 'stock files replaced: none';
  then a stock boot is a stock boot.

## 8. For other owners

- **kl_graft.py**: (a) `bones=True` as default fails every map but the bank on its own check; this
  tool passes `bones=False` (the builds that ran). (b) Section 5.1: empty unreached vertex data always
  and stub unnamed textures of S - about 150 MB packed per map. (c) `write_level` stamps the build time
  into the zip, so two builds of the same content differ as files; `build_id` works around it.
- **kl_maps.py**: `chain()` has no `slot` argument (its second step is always F01); this tool repeats
  its six lines with one. `preflight()` cannot take a chained build.
- **klhook (i-hook)**: the tree installs `KLJoin.ini` as `Maps\DM09\KLJoin.ini` and the ini block
  above; `install` leaves `[Steam]` / `[Join]` sections of an existing `KLHook.ini` alone. A SHIP DLL
  should live at a fixed place in the work folder (e.g. `<work>\build\klhook\ship\dinput8.dll`) so
  `build` can take it without `--hook`.
- **mkoverlay.py**: unused entries of a page keep the stock title and load the stock map (entry 5 =
  'Financial' on our page); hiding them needs the level list's 'available' answered per page. Its
  output passes the checks as it is.
- **CLAUDE.md** (lead): the merged `PC_Def.str` is a replaced stock file outside the F01 slot; `tools/`
  gained `kl_expansion.py`; the titles are Hot Coffee / Late Night Opening / Withdrawal / A Walk in the
  Park.
