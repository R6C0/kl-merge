# The expansion as a package: layout, build, install, menu, sizes

Written 2026-10-09 (agent i-pack), second pass the same day 15:00 - 15:40 (rebuilt on commit 42ec5c6, after the
live runs S0 - S2, J1 - J3, M01R of agent i-live). **Offline only: the game was not started and nothing was
written to the Dog Days folder.** Tool: `tools/kl_expansion.py`. Everything it builds lives in the work folder
(`<work>\build\expansion\`); no game data is in the repo.

Words: **built / measured / tested** = done here, with the command; **live** = seen in the game by another
agent (run names are those of `tools/kl_graft.py`'s log and of `<work>\build\klhook\live\<run>.*`); **NOT
LIVE** = nobody has run it; ASSUMPTION = not established by anyone.

## 0. Short answers

1. `python tools\kl_expansion.py build` makes one relocatable folder `KLExpansion` with all five maps,
   the menu page, the merged stream file, the hook (compiled from `klhook\` by the build) and a manifest.
   Last run (15:07): 5 maps accepted, 128 files, 3.40 GB, `RESULT: PASS` in 289 s (section 2).
2. Each map is built **for the stock slot its menu entry loads** (F01 F02 F03 F04 F06) and lives in
   `Maps\<id>\`; the hook answers the opens of that slot from there while menu page 2 is chosen.
   Nothing stock is replaced. Three of the five builds are, member for member, builds that ran in the
   game today: the diner (run M01R), the bank (S0, S1) and Retomoto Tower (S2) - same archive size to the
   byte as the hook logged in those runs. The other two (M02, M06) differ from their live builds by the
   skeleton step (section 2).
3. `install` / `uninstall` are written and tested against a made-up game folder (31 checks), once with
   the real 3.4 GB tree in a made-up folder, and once for real against a running game: while the live
   agent's kl2.exe (95 threads) was up both commands refused and changed nothing. `KL_PortBackup` is only
   read.
4. Menu: page 'Dead Men maps' with the five titles is generated and passes the rules of
   `re/menus.md`. **Dead Men does ship a menu picture for every one of these maps**; they are converted
   to Dog Days' picture form (six DXT5 tiles), but not yet shown: a new picture needs an entity in the
   frontend scene (section 4.2). Until then the page shows the stock picture of each slot.
5. Sizes: a map is 356 - 383 MB. **161 MB of each archive (133 MB of Retomoto's) is F07's own map, which
   the joined level never references** (measured piece by piece at the archive's own compression,
   section 5) - 778 MB of the 1.83 GB of maps. F07's live systems are 77 - 86 MB per archive (395 MB over
   the five): keeping them once would save about 310 MB more and needs the hook to serve virtual files.
   Not implemented, by instruction.
6. Still test-only: everything about the page (never opened in the game), builds under the slot names
   F02 F03 F04 F06, the stream file through the overlay, the SHIP hook's policy, the skeleton step on M02
   and M06, Retomoto's join read from `Maps\DM09`. Section 6 has the list, section 7 the live checks in
   order.
7. **2026-10-10 (section 9): the tree can be made from FINISHED build folders** - `build --ready
   <work>\build\z_maps --prebuilt DM09=<the owner's Retomoto folder>` takes the four Fragile Alliance
   maps as `kl_maps.py ready` left them (every fix, lightened, the wardrobe) and Retomoto as the owner
   plays it, renames them for their slots and carries `KLWardrobe.ini` / `KLJoin.ini` into `Maps\<id>`.
   Built in `<work>\build\z_maps\expansion`: 5 maps accepted, 159 files, **2.88 GB** (maps 1.20 GB,
   was 1.83). Not installed. `install` no longer leaves a test build's `KLWardrobe.ini` beside the
   stock F01 archive.

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
    Maps\DM09\  F06_Main.*  KLJoin.ini (written by the build from kl_fa_author's numbers)        Retomoto Tower
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
changed_since_commit {file: sha1}}` (the tree of 15:07 was built from commit 42ec5c6 plus four
uncommitted files: this tool and i-hook's `klhook.c`, `kljoin.c`, `klsteam.c` as they were at that
minute - the manifest names them with their sha1); `needs {kl2.exe sha1, systems level
archive sha1, stream_file {sha1, bytes, in_tree}, hook {sha1, bytes, test_build, steam_write_guard,
sources_sha1, source_files, built_from_these_sources}}`;
`maps[]`: `id, name, slot, menu_entry, folder, scene, systems_level, source_levels, build, options,
build_id, accepted, problems, known_problems, fa_check, fa_findings, preflight, live, skeleton_step
{in_this_build, renumbered, ran_live_in_this_form}, numbers
(archive / beside MB, entities, rooms, textures, materials, chunks, sounds, waves, nav bytes), bytes,
extra_files`; `menu` (the rule check); `pictures`; `steam` (one sentence: guarded or not); `files
{relative path: {sha1, bytes}}`; `total_bytes`, `bytes_by_part`. No absolute path is in it.

**build_id** = sha1 over the archive's members (name without the slot, CRC, size - not the zip's bytes,
which hold the build time) and the sha1 of every file beside it except the `.hti` (name without the
slot). The same content built for another slot has the same id (measured in the first pass: an F03 build
and the F01-named copy of the same content in `<DD>\KLExpansion\Maps\DM03` both gave `2274a15ee3e2...`).
Ids of the 15:07 tree: DM01 `13cccebcc6c5`, DM02 `e8bd1875da03`, DM03 `f9b6f7c29ab1`, DM06
`714f2e574894`, DM09 `282fafcb8297` (the hook's per-map file `KLJoin.ini` counts: peers must have the same
jump box). This is the number two peers must compare before an online session (`re/netcode.md` 5: the
game's own check does not know our files); nothing compares it yet.

## 2. Building

    python tools\kl_expansion.py build [--out <folder>] [--maps DM01,DM03] [-j 2] [--reuse] [--hook <dinput8.dll>]
                                       [--no-hook-build] [--no-stream] [--no-share] [--no-pictures] [--no-bones]
    python tools\kl_expansion.py check | menu | share | pictures

What it does: each map in a process of its own through `kl_maps.one` (which never writes
`<work>\build\install`), two at a time; verdict per map; `Maps\DM09\KLJoin.ini`; the ini block;
`klhook\mkoverlay.py` on the stock `Patch01.zip` (read only) and the rule check of section 4; copy of
`<work>\build\PC_Def.str`; the hook; pictures; the sharing measurement; the manifest. Exit code 1 when
a map has a `verify()` problem outside its known list, a `kl_fa.check` finding CRASH / BROKEN, or the
page breaks a rule. Five maps take under five minutes; `--reuse` (everything but the graft) 1.5.

**The hook** is compiled by the build itself: `klhook\build.bat <out>\_stage\hook` (the SHIP build, no
klauto) whenever the tree has no DLL or one made from other sources; `<out>\hook.json` remembers which
sources (sha1 over `klfix.c klhook.c kljoin.c klranges.h klslot.c klsteam.c klstock.h`) the DLL in the
tree came from, and the manifest says `built_from_these_sources`. `--hook <dll>` takes a given DLL
instead (refused unless it holds klslot's page texts), `--no-hook-build` keeps what the tree has. The
hook of the tree as restamped at 15:15 (`build --reuse --no-share --no-pictures`, 27 s, RESULT: PASS):
189,440 bytes, sha1 d63a1144..., sources b564b73a... (at 15:06 it was f292f50b... from 728858a5...:
i-hook was editing `klhook.c / kljoin.c / klsteam.c` during this pass). Run `build --reuse` once more
when those are committed; `check` prints the manifest's time and how many tool files differ from the commit.

**`KLJoin.ini` of Retomoto** is written from `kl_fa_author.JOIN_BOX / JOIN_ENTRY / CAR_B`, not copied
from `klhook\KLJoin.retomoto.ini`: at commit 42ec5c6 that sample still named the box inside the car
(x 2802..3142), which run J1 showed is never reached; the box that fired in J1b, J2, J3 is the one in
front of it (x 2550..2790, y 19500..19800, z 800..1100). The build prints a NOTE when the sample and
kl_fa_author disagree (they agree again since i-hook's edit after 15:00).

Options: **kl_graft's defaults, nothing on top.** The one choice is the skeleton step (`bones`,
kl_chars: the skeletons that came with the Dead Men models are renumbered to the joined level's bone
ids and `.ANM` bone table; without it faces, fingers, car doors and wheels are driven by the wrong
tracks). History: its first form (12:40) failed its own check on four maps, which is why the first pass
of this packaging built without it; the committed form (names without tracks are added to the bone
table) passes on all five, and the diner, the bank and the tower have since run with it (M01R, BR1 / S0
/ S1, S2 / J1b - J3 / HK3). M02 and M06 have NOT run with it: their live rounds (M02r, M06r) were the
09:23 builds. `build --no-bones` gives those builds back; the manifest's `skeleton_step` says per map
what the build has (read from the build's own log line 'skeletons of <M>: n of n renumbered') and
whether that form ran.

Result of the full build of 15:02 - 15:07 (`build --out <work>\build\expansion_next -j 2`, then moved
to `<work>\build\expansion`; log in scratch `ipack\build3.log`):

| id | problems | kl_fa.check | preflight | archive MB | beside MB | entities | rooms | textures /4096 | materials /2048 | skeletons renumbered |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| DM01 | 0 | 4 DEGRADED, 2 NOTE | CRASH 0, RISK 0 | 336.4 | 46.8 | 14,999 | 12 | 1,999 | 1,354 | 22 of 22 |
| DM02 | 0 | 4 DEGRADED, 2 NOTE | CRASH 0, RISK 3 | 310.3 | 47.5 | 21,934 | 32 | 1,697 | 1,076 | 16 of 16 |
| DM03 | 0 | 5 DEGRADED, 2 NOTE | CRASH 0, RISK 0 | 321.1 | 47.7 | 19,827 | 20 | 1,864 | 1,193 | 23 of 23 |
| DM06 | 0 | 3 DEGRADED, 2 NOTE | CRASH 0, RISK 2 | 310.1 | 46.2 | 15,599 | 7 | 1,576 | 995 | 17 of 17 |
| DM09 | 2, both known | 1 DEGRADED | not run (kl_maps.preflight takes one S and one M) | 312.4 | 48.3 | 25,489 | 22 | 2,195 | 1,429 | 16 of 16 (M09_B), 4 of 4 (M09_A) |

DM09's two known problems are `kl_fa_author.KNOWN`: '39 particle template names do not resolve (stock
M09_A: 36)' and '13 stream clips are not in the merged stream file' (its music among them,
`re/retomoto_audio.md`). The RISK lines are the first-time classes of `re/maps.md` 9.3 (ZEnvSampler,
SoundSpline, SoundVolumetricRandom); those maps ran live with them (M02c, M02r, M06a, M06r).

Against the kept builds that ran live (members by CRC and size; scratch `ipack\same2.py`), and against
the archive size the hook logged in the run (`steam: level archive f01\f01_main.zip opened from ...: NOT
stock (<bytes> bytes ...)`):

| id | kept live build | members that differ | archive bytes here = bytes logged in the run |
|---|---|---|---|
| DM01 | `<work>\build\i_m01` (12:51) | 0 of 31 | 336,379,622 = M01R |
| DM02 | none with the skeleton step; vs the first-pass build (= M02r's but for `.prp`) | `.ANM`, `.prm` (the step) | - |
| DM03 | `<work>\build\i_bank` (12:50) and `<work>\build\install` (12:52) | 0 of 31 | 321,104,553 = S0, S1 |
| DM06 | none with the skeleton step; vs the first-pass build (= M06r's but for `.prp`) | `.ANM`, `.prm` (the step) | - |
| DM09 | `<work>\build\i_rt\R09+M09_A ...` (12:56) | 0 of 30 | 312,376,563 = S2 |

(The join runs J1b / J2 / J3 used the no-guards build `i_rt_noai`, 295,929,966 bytes, and HK3 / GW1 / GW2
the guards-wait option, 312,376,644 bytes: neither is what the tree holds. The tree's Retomoto is the
level as `kl_fa_author.test` builds it without options - the one of S2, where the player dies 21 - 26 s
into each round in sight of the boardroom guards: an owner decision, `re/retomoto_fa.md` 9.6.)

## 3. Install and remove

### 3.1 For a player

1. Both games installed (the maps are built on the player's machine from the player's own files;
   nothing of either game is distributed). `python tools\kl_expansion.py build` (about five minutes;
   needs Python with pefile and capstone, the merged stream file of `kl_audio.merge` in the work
   folder, and Visual Studio's C++ tools for the hook - or `--hook <dinput8.dll>` with a built one).
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

### 3.3 The owner's folder as it is now (`status`, read only, 2026-10-09 15:09)

`KLExpansion\Maps\DM03` (not ours; the live tests' F01-named bank), `KLHook.ini` with `[KLHook]` only;
`dinput8.dll` is whatever the live agent's run swapped in (b14bbd93..., i-hook's TEST build, while a
run was up at 15:09; 7e806e6c... without pages between runs). Replaced stock files: the F01 slot (19
files) and **`PC_Def.str`** - the merged stream file (1,575,448,788 bytes, sha1 62349cb6...) stands
where the stock one (1,217,890,070 bytes) was since 2026-10-08. The merged file is not the stock file
plus a tail (the first 1.2 GB hash differently), so it is a replaced stock file like any other. The
tree therefore carries it as `Overlay\PC_Def.str`; once check L4 below has shown that the game takes
it from there, `uninstall --restore-all` puts the stock one back and nothing stock is replaced any
more. Until then leave it: the maps' streamed clips index the merged file.

A file that is in the F01 slot but not in `KL_PortBackup` (a `KLJoin.ini` left from a Retomoto test)
is not touched by the slot restore: kljoin.c ignores it beside a stock archive, delete it by hand.

### 3.4 Tested

- `python tools\kl_expansion.py selftest <scratch>`: a made-up game folder (dummy `kl2.exe`, a test
  build in the F01 slot with its stock files in `KL_PortBackup`, an old hook, an ini with `[Auto]` and
  stale `[Expansion]` / `[Redirect]` sections, a foreign `KLExpansion`) and a made-up tree. 31 checks,
  `RESULT: PASS` (again at 15:08 with the tool as it is now): both commands refuse while the game runs
  and nothing changes; foreign folder, missing exe and tampered tree are refused; install copies, links,
  merges the ini, swaps the hook, restores the slot; `KL_PortBackup` and every stock file outside the
  slot are byte-identical afterwards; update; uninstall returns the folder to its start but for the
  slot; clean folder; edited ini; `--restore-all`. (In the selftest 'the game runs' is a substituted
  process list.)
- **The refusal with a real running game** (15:09; the live agent's kl2.exe, pid 48620, 95 threads, and
  21 thread-less entries beside it): `install <selftest tree> --game <made-up folder>` and `uninstall
  --game <made-up folder>` both answered `kl2.exe is running (pid 48620): close the game first. Nothing
  was changed.`, exit 1; a sha1 list of the made-up folder before and after is identical. `status`
  on the real folder said `kl2.exe RUNNING`.
- The real tree into a made-up folder (`<work>\build\_fake_game_ipack`: dummy exe, a test build in the
  F01 slot, `KL_PortBackup` with 'stock' files, an old hook, an ini with `[KLHook] [Redirect] [Auto]`, a
  foreign `KLExpansion\Maps\DM03`): `install --game <fake>
  --replace --link` at 15:13 copied 127 files (3.40 GB, 32 as hard links; install, `status`, `uninstall`
  and two sha1 listings took 55 s together), moved the foreign folder aside, put the tree's hook in,
  merged the ini (`[KLHook]` and `[Auto]` kept, the stale `[Redirect]` replaced by the block) and made
  the slot stock; `status`: '128 files, all as built', 'hook with expansion pages'; `uninstall` put ini
  and hook back, removed the folder and moved the foreign one back. A sha1 list of the folder before and
  after differs in four lines: the F01 slot's files, now equal to their `KL_PortBackup` copies; the five
  `KL_PortBackup` hashes are the same before, between and after (scratch `ipack\fake_run.log`).
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
| five maps | 1,826,631,783 (356 - 383 MB each: archive 310 - 336, beside 46 - 48) |
| `Overlay\PC_Def.str` | 1,575,448,788 |
| `Overlay\Patch01.zip`, hook, ini, BuildInfo | 0.4 MB |
| total | 3,402,504,250 |

Inside an archive, UNPACKED:

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
unnamed, so the method is tight; those 8 are counted as live below. `.TEX`, `.prm`, `.ANM` (17 MB),
`.fxc` (4) are all but 4 MB of an archive; no large member is a stock member byte for byte.

The same PACKED, i.e. what it costs in the archive - measured, not estimated: every texture and every
`.prm` chunk deflated by itself at level 1, which is how kl_graft packs (the pieces of a `.TEX` sum to
within 0.1 % of the member's packed size, those of a `.prm` to within 7 %):

| MB packed | archive | F07's dead map (.TEX + .prm) | F07's live systems (.TEX + .prm + .ANM/.fxc) | the Dead Men map (.TEX + .prm) | archive without the dead part |
|---|---:|---:|---:|---:|---:|
| DM01 | 336 | 161 (140 + 21) | 77 (43 + 13 + 21) | 96 (86 + 10) | 175 |
| DM02 | 310 | 161 | 77 | 70 (61 + 9) | 149 |
| DM03 | 321 | 161 | 77 | 81 (69 + 12) | 160 |
| DM06 | 310 | 161 | 77 | 69 (62 + 7) | 149 |
| DM09 | 312 | 133 (133 + 0: its `.prm` is already emptied) | 86 (51 + 14 + 21) | 90 (72 + 18) | 180 |
| five maps | 1,590 | **778** | **395** | 406 | 812 |

(The first pass estimated the dead part from member ratios as 719 MB; the measurement is 778.)

**Is a 300 - 400 MB archive per map unavoidable? No - half of it is dead weight, and the saving is in
trimming and packing, not in sharing.**

1. *Trim F07's dead map at build time* (kl_graft's owner; safe in kind, NOT LIVE in this extent):
   `PRM_LIMIT` already empties unreached vertex / index chunks above 90 MB and Retomoto runs that way
   (RT2b - RT6, S2, J2); doing it always saves 21 MB packed per map. The same idea for textures - a
   texture no reference reaches becomes a 4 x 4 stub with its id kept - saves 140 MB packed per map.
   Risk to measure first: the 8 unnamed textures of stock F07 show that some referrer is unknown; keep
   every texture that stock F07's own systems side names or that is in that floor set (the table above
   already does). Result: archives of 149 - 180 MB, the five maps 0.81 GB of archives + 0.24 GB beside
   = 1.05 GB instead of 1.83.
2. *Pack harder* (kl_graft's owner, one argument of `write_level`; the stock archives are plain
   deflate, so nothing new for the game): measured on DM03's five large members, level 1 (now) 316.7
   MB, level 6 268.0 MB (10 s more build time), level 9 262.9 MB (29 s). 15 % of every archive, about
   240 MB over the five as they are, about 120 MB after 1. Stock F07 itself is packed to 51.6 %.
3. *Hard links for equal files beside the archives* (implemented, `install --link`, tested): the 14
   `_LS_<Language>` files and the `.hti` are byte-equal in all five maps (they are F07's): 92 MB.
   Invisible to the game (read-only opens).
4. *The systems part once on disk* (77 - 86 MB per archive; one copy instead of five saves about 310
   MB) would need the game to read one member from two places. It cannot: a level is ONE archive (the
   loader mounts `Patch01.zip` and the scene's own zip, kl2 0x7f5610 / 0x7f5827), every member is one
   file with one id space (`.TEX` table of 4096, `.prm` chunk table, `.MAT` slots), and member names
   carry the slot. What the game would need: (a) the hook serving a virtual `<slot>_Main.zip` (stored
   members, a shared segment + a map segment) by wrapping `ReadFile`, `SetFilePointer`, `GetFileSize`
   and the async reader for those handles - new code on the hot path of every load; and (b) builds whose
   systems part is byte-identical between maps, which it is not today: a joined `.TEX` / `.prm` is one
   stream in which S's records come first (so a shared PREFIX is possible in kind), but `.MAT`, `.ANM`,
   `.fxc`, `.SND` are merged files. Not recommended before 1 and 2 are done: after them the systems part
   is the largest piece left, and still only ~65 MB a map.
   (One `.TEX` for all maps does not work either: every map would load every texture - the loader
   takes the `.prm` as one heap block and 100.9 MB was already refused once, run RT1.)
5. *Distribution* is not a size problem: nothing is shipped but tools; `build` runs on the player's
   machine against both installed games.
6. `Overlay\PC_Def.str` is 46 % of the tree. It is Dog Days' own 1.22 GB plus Dead Men's clips, rewritten;
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
| the hook in the tree | SHIP build compiled by `build` from `klhook\` as it was at 15:15 (sha1 d63a1144...). Live of this code line: the TEST build of 12:49 in direct boots and Arcade sessions (S0, S1, S2, J1b - J3: import slot 0xb107c8 is session-safe, no integrity exit); a SHIP build only as the 12:49 one on a direct boot (HK1). **This exact DLL: NOT LIVE.** Restamp after a hook change: `build --reuse` |
| Steam writes | TEST policy (block always) LIVE: run S2 ended a session on Retomoto - 29 `SetStat`, `StoreStats` and `UploadLeaderboardScore` all BLOCKED, Steam's stats file unchanged. The SHIP policy (block when the level is not the stock archive of its slot, klstock.h) is NOT LIVE (S3, S4 of `re/hook_live.md`) - and it is the one a player gets. The local high-score list of the slot (profile) is NOT guarded (`re/leaderboard.md` 4.3). S2 also showed what an unguarded end does on the scripted route: every stat is SET to the in-memory profile's value (zeros without a loaded profile) |
| the skeleton step on DM02 and DM06 | NOT LIVE on these two maps (verify 0; the diner, the bank and the tower ran with it). `build --maps DM02,DM06 --no-bones` gives the form that ran (M02r, M06r) |
| Retomoto Tower | loads and runs rounds (RT5, RT6, S2); the jump box works from inside the process on a direct boot and in an Arcade round (J1b, J2, J3) - with `KLJoin.ini` beside the archive in the F01 slot and on the no-guards build. Read from `Maps\DM09` beside an F06-named archive: NOT LIVE. The start in sight of seven guards is an owner decision (`re/retomoto_fa.md` 9.6; option `--guards-wait` ran as GW1, GW2, HK3 and is not in the tree); music silent (13 clips not in the stream file) |
| a whole round with loot and escape | bank only, and only on the build without the map's guards (ESC3); `kl_fa.check` DEGRADED on every map: no bot squads, no HUD markers, no spawn points of the Dog Days-only modes |
| the diner from the menu | one Arcade round, 150 s in the round, ended by the script (M01R); loot and escape not played |
| the Fragile Alliance LOBBY (online / LAN) | not part of this: the page is an Arcade page; a lobby client maps the slot index through its own files (`re/slot_redirect.md` 5) |
| pictures | converted, not shown (4.2) |
| loading screen and briefing of an expansion map | the stock slot's |
| uninstall on the real folder | not run (by instruction) |

## 7. Live checks, in order (one variable each; `python debug\zombies.py --count` before and after)

`re/hook_live.md` S0, S1, S2 are done (the hook's code line runs in a session and the TEST build blocks
every Steam write), so L0 can start. All runs: klauto TEST DLL unless said (build it from the same
sources as the tree's SHIP DLL: `klhook\build_auto.bat`), and check the log for `steam: import
SteamUserStats wrapped` before a script may let a session end.

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
- **L6a - M02 and M06 with the skeleton step, the old way** (one variable: the step). Before they are
  loaded under a new slot name: M02_FA_A, then M06_FA_A, built the usual way into the F01
  slot (kl_graft's defaults = the tree's content), direct boot + the walk of M02c / M06a. Expect what
  those runs showed, and car doors / wheels / faces no worse than before. A fault here and not with
  `--no-bones`: rebuild the tree with `build --maps DM02,DM06 --no-bones --reuse` and tell kl_chars' owner.
- **L6 - the other maps from the page, one run each**: entry 0 (DM01, slot F01), entry 1 (DM02, F02),
  entry 3 (DM06, F04), entry 4 (DM09, F06). Expect the map of the title, `slot F0n: menu page 2 from
  now on -> DM0n`, and per map what its F01 build showed (run names in the manifest's `live`). These
  are the first loads of builds named for F02, F04, F06. For DM09 also the join read from the map's
  folder: `join: reading ...\KLExpansion\Maps\DM09\KLJoin.ini for level f06\f06_main`, `join: box 9:
  (2550, 19500, 800) - (2790, 19800, 1100) -> entry 5, name '06_Exit', target (6272, 563, -6305)`, `join:
  level '...F06_Main.gms': 1 box(es) active`. The jump itself needs J2's walk, which ran on the
  no-guards build; the tree's Retomoto has its guards and the walker dies before the car (S2) - so here
  the three lines are the check, and the jump stays as shown in J2 until a round reaches the car.
- **L7 - a slot is the stock map again after the page was used.** Two boots are the plain form: L3,
  then a boot through the stock button and entry 2 - expect `menu page option is 1`, `slot F03: menu
  page 1 from now on -> the stock level`, and Airport. The stronger form is both in ONE process (the
  latch is per archive open): it needs a way from a running round back to the frontend that does not
  end the session, which is not known - if there is none, say so and keep the two-boot form.
- **L8 - SHIP hook** (`Hook\dinput8.dll` of the tree, the plain block, no `[Auto]`). First S3 of
  `re/hook_live.md` as a direct boot with `Page=2` under `[Expansion]` (expect `steam: level archive
  f01\f01_main.zip opened from ...\Maps\DM01\...: NOT stock` and `... BLOCKED`); only then the owner
  plays one round on a Dead Men map from the page with a loaded profile. Until S3 has shown the SHIP
  policy's lines, nobody ends an Arcade session on an expansion map with the SHIP DLL.
- **L9 - uninstall**: `uninstall` (and `--restore-all` once L4 has passed). Expect `status`: no
  KLExpansion (or the old folder moved back), the earlier hook and ini, 'stock files replaced: none';
  then a stock boot is a stock boot.

## 8. For other owners

- **kl_graft.py**: (a) section 5.1: empty unreached vertex data always and stub unnamed textures of S -
  161 MB packed per map, measured. (b) Section 5.2: `write_level` packs at deflate level 1; level 6
  saves 15 % (49 MB on the bank) for 10 s. (c) `write_level` stamps the build time into the zip, so two
  builds of the same content differ as files; `build_id` works around it. (d) `bones=True` now passes
  on all five maps; M02 and M06 have not run with it (L6a).
- **kl_maps.py**: `chain()` has no `slot` argument (its second step is always F01); this tool repeats
  its six lines with one. `preflight()` cannot take a chained build.
- **klhook (i-hook)**: `build` compiles the SHIP DLL itself with `klhook\build.bat <folder>` and
  records the sources' sha1; it writes `Maps\DM09\KLJoin.ini` from kl_fa_author's numbers and prints
  a NOTE when `klhook\KLJoin.retomoto.ini` disagrees (it did at commit 42ec5c6: the inside box).
  `install` leaves `[Steam]` / `[Join]` / `[KLHook]` / `[Auto]` sections of an existing `KLHook.ini`
  alone. i-live's two notes on kljoin.c (the 'NOT usable ... 1 entries' line during every load, the
  '500 ms after' line printed at once) are in `<work>\research\agent_scripts\i-live\` / scratch
  `ilive\add_fa_round.md` 8.3.
- **mkoverlay.py**: unused entries of a page keep the stock title and load the stock map (entry 5 =
  'Financial' on our page); hiding them needs the level list's 'available' answered per page. Its
  output passes the checks as it is.
- **kl_fa_author.py**: the tree holds the level without options (guards active from the start). If the
  owner picks `--guards-wait` or a blast delay, the packaging needs a way to pass it: say so and
  `MAPS` gets an option field.
- **CLAUDE.md** (lead): the merged `PC_Def.str` is a replaced stock file outside the F01 slot; `tools/`
  has `kl_expansion.py`; the titles are Hot Coffee / Late Night Opening / Withdrawal / A Walk in the
  Park; `<work>\build\_fake_game_ipack` is a made-up game folder of this tool's test (dummy files,
  can be deleted).

## 9. The tree from finished folders (2026-10-10, agent z-maps)

OFFLINE: built into `<work>\build\z_maps\expansion\`; nothing installed, the game not started, the
tree of 2026-10-09 in `<work>\build\expansion\` left as it is.

    python tools\kl_expansion.py build --out <work>\build\z_maps\expansion --ready <work>\build\z_maps
           --prebuilt DM09=<work>\build\y_loot\retomoto_loot --hook <work>\build\klhook\owner_now\dinput8.dll

### 9.1 What is new in the tool

- `--ready <folder>`: DM01 DM02 DM03 DM06 are not built by `build` but taken from the finished
  folders `M01 M02 M03 M06` of `kl_maps.py ready` (re/maps.md 14: every fix, voices on, lightened,
  the wardrobe). `--prebuilt DM09=<folder>`: any map from a finished folder - here the owner's
  current Retomoto build, the one in the F01 slot.
- `adopt()`: such a folder holds an archive built for the F01 test slot. It is written again under
  the map's own slot name - member names and file names only; the members' CRC and size are compared
  after the write - and the hook's per-map files `KLWardrobe.ini` / `KLJoin.ini` (`SIDE`) go with it
  into `Maps\<id>`; `graft.txt`, `log.txt`, `result.json`, `audit.*`, `preflight.*`, `wardrobe.txt`,
  `steps.json`, `chars.json` go to `BuildInfo\<id>` with `adopted.json` (where from, built for which
  slot, sha1 of the folder's archive). Nothing inside a level names its slot; the model numbers in
  `KLWardrobe.ini` are .prm chunk indices and do not change. NOT LIVE: no adopted archive has been
  loaded under F02 / F03 / F04 / F06 (the builds of section 2 under those names were not either).
- A folder's `KLJoin.ini` is kept as it was played; `build` prints a NOTE if it no longer equals
  kl_fa_author's box (it does equal it today).
- A map whose `audit.json` lists a finding that must be 0 is NOT ACCEPTED (`audit: ...`).
- Manifest, per map: `taken_from`, `wardrobe`, `audit` (prm_mb, prm_entries, tex_mb, people, weapons,
  fa, round, preflight), `extra_files` = the SIDE files that are there. `numbers.archive_mb / beside_mb`
  are read off the tree and the counts off the audit: `result.json` is written by the graft, before
  lighten and the wardrobe (it says 336 MB for DM01; the archive in the tree is 197 MB).
- `menu_check` accepts the windows `KLHeister` and `KLGuns` that `klhook\mkoverlay.py` now adds
  beside the map page (their rows are mkoverlay's own check); the map page's own growth is still
  held to 100 elements. `HOOK_MARKS` asks for the text `menu page %d latched`: a hook from before
  0ad48d2 lost the page at StartGame (re/hook_live.md) and is refused.
- **install, a fault found by reading klchar.c**: `restore_stock` put the F01 slot's stock files back
  and left a test build's `KLWardrobe.ini` / `KLJoin.ini` beside them. `klc_level_open` reads
  `KLWardrobe.ini` beside ANY archive the game opens (it has no stock test; `klj_level_open` has:
  verdict 1), so stock Subway would have been given the model numbers of the build that was in the
  slot - and the owner's slot holds one today (Retomoto, both files). The two files are now renamed
  `<name>.of-test-build-N` when the slot goes back to stock (install and uninstall); not deleted.
  `selftest`: 32 checks, 0 failed (one new).

### 9.2 The tree (built 2026-10-10 06:40, `RESULT: PASS` in 56 s; `check`: 159 files against the manifest, exit 0)

| id | name | slot / entry | from | bytes of `Maps\<id>` | archive MB | wardrobe | per-map files | accepted |
|---|---|---|---|---:|---:|---|---|---|
| DM01 | Hot Coffee | F01 / 0 | `z_maps\M01` | 243,859,165 | 196.9 | yes | KLWardrobe.ini | yes, 0 problems |
| DM02 | Late Night Opening | F02 / 1 | `z_maps\M02` | 225,511,985 | 177.8 | yes | KLWardrobe.ini | yes, 0 problems |
| DM03 | Withdrawal | F03 / 2 | `z_maps\M03` | 236,486,157 | 188.5 | yes | KLWardrobe.ini | yes, 0 problems |
| DM06 | A Walk in the Park | F04 / 3 | `z_maps\M06` | 224,570,375 | 177.6 | yes | KLWardrobe.ini | yes, 0 problems |
| DM09 | Retomoto Tower | F06 / 4 | `y_loot\retomoto_loot` | 264,604,105 | 212.2 | yes | KLJoin.ini, KLWardrobe.ini | yes, 1 problem, known ("39 particle template names do not resolve (stock M09_A: 36)") |

- **2,880,113,871 bytes in 159 files** (the tree of 2026-10-09: 3.40 GB in 128): maps 1.20 GB (was
  1.83), `Overlay\PC_Def.str` 1,684,486,009 bytes (sha1 3b14a846..., the extended merge the game folder
  has), `Overlay\Patch01.zip`, `Hook\dinput8.dll`, `BuildInfo` 0.3 MB.
- Hook in the tree: `<work>\build\klhook\owner_now\dinput8.dll`, sha1 bceda981... (the SHIP build of
  2026-10-10 06:21, the pair kept for the owner): not a test build, Steam write guard in, klchar and
  klgun in. Given with `--hook`, so the manifest says `built_from_these_sources: false`; without
  `--hook` the build compiles `klhook\` itself.
- Menu: page 2 "Dead Men maps" = Arcade button 8, entries 0..4 as above; `klhook\mkoverlay.py` (called
  as it is) also wrote the Heister page (button 6: Character 17, Mask 10, Outfit 24 entries) and the
  Guns page (button 7); 122 tags added to 4,542; rules hold. The page's pictures: none (section 4.2).
- `share` on the lightened archives: F07's dead map is now about 14 MB of each archive (was 161 MB:
  section 5.1's saving is what `lighten` does), F07's live systems 77 .. 91 MB each, 402 MB over the
  five; 16 kinds of files beside the archives are equal in two or more maps, 92 MB as hard links
  (`install --link`).
- DM09 has no `audit.json` (the folder is the lead's and was only read); its manifest numbers are
  its `result.json`'s, with the sizes read off the tree.

### 9.3 Not known

- Everything of section 6 still stands; in addition no build of this tree has run under its slot
  name, and none of the four Fragile Alliance builds has run at all in this form (re/maps.md 14.6).
- The wardrobe through the redirect: klchar.c reads `KLWardrobe.ini` beside the archive that is
  opened, so from `Maps\<id>` - read in the source, NOT seen in a run.

## 10. The 'Dead Men maps' tab from the current builds (2026-10-10, agent w-tab)

OFFLINE: the game was not started, nothing was written to the Dog Days folder. Built into
`<work>\build\w_tab\`. The owner, 2026-10-10: 'still want the kane and lynch dead men maps to have its own tab'.

### 10.1 What was wrong, and what is left of it

The brief's HOOK entry ('at StartGame the redirect is lost, the Location row is empty, the button has no icon')
describes run MP1 (2026-10-09 15:59). All three were fixed in commit 0ad48d2 and **seen in the game the same
evening** (runs MP2b, MP2c, 17:07 / 17:10; `<work>\build\klhook\live\MP2c.log`, pictures
`<work>\research\shots\MP2c_68s.png`, `MP2c_77s.png`) - the brief was never updated:

| fault of MP1 | cause | fix | seen |
|---|---|---|---|
| page read as 0 at StartGame | the page was carried in the menu option `Dummy`, a field of ZMercsOptionsInterface (`[0x154d5f4]+0xd4`); that object is deleted in the menu manager's destructor (kl2 0x673340) and the global zeroed in its constructor (0x617701) - a level load builds new managers. StartGame never reads it (0x502b40 -> 0x746570 -> 0x7e01a0) | `klslot.c` kls_menu_watch: the page is read off the WINDOW STACK (`HeistPlayMenu<N>` open = page N), kept through the load, the level and the session | MP2c.log 110-122: `menu page 2 latched: window 'HeistPlayMenu2' is open`, `session: state 0x0 -> 0x12`, 12 ms later `slot F01: menu page 2 from now on -> DM03`, archive, `_LS`, `.WHD`, `.WAV` all from `Maps\DM03`; round PASS |
| empty 'Location:' row | elements are found by NAME over the whole menu, first in the file wins (0x83faf0 -> 0x4fa730): the copied page wrote into the stock page's elements | `mkoverlay.py`: every element of the copy gets the suffix `_P<N>` | MP2c_77s.png: focus bar, 'Location:', arrows, 'Withdrawal' |
| no icon, button on 'Back' | only button + focus bar had been added | icon, line, the rows moved up 34 per added button | MP2c_68s.png: six rows, the sixth with an icon, clear of 'Back' |

So no code of `klslot.c` or `mkoverlay.py` had to change for the latch, the row or the icon (klslot.c: its
comment now names the runs; mkoverlay.py: not touched). What was NOT there, and is new today:

1. **A tree from the current builds, with the installed Heister / Guns pages kept.** `kl_expansion.py build`
   called `mkoverlay.py` without `--pictures` and carried no menu scene: installing its overlay would have
   replaced the owner's Heister page with pictures by one without, and dropped `Overlay\Scenes\kaneandlynch.zip`.
   New `--overlay-from <folder>` (kl_expansion.py `overlay_kept`, and the block after the mkoverlay call in
   `build`): mkoverlay is run the way the reference archive was made, everything under its `Overlay\Scenes` is
   carried, and the build fails unless the windows `KLHeister` and `KLGuns` are the reference's character for
   character and only `HeistModeMenu`, `HeistPlayMenu2` and its gamepad template differ.
   Checked first: `mkoverlay.py` as committed, with no `[Redirect.N]` and `--pictures`, reproduces the installed
   `menu/frontend.xml` byte for byte (685,053 bytes; the zip differs by its time stamp only).
2. **`KLGuns.ini` is a per-map file** (`SIDE`): adopted into `Maps\<id>`, and set aside with the other two when
   the F01 slot goes back to stock (`restore_stock`; selftest 32 checks, 0 failed).
3. **Dead Men's own pictures on the page** - section 4.2's 'NOT DONE - the entity' - as a separate VARIANT of the
   overlay (`kl_expansion.py mappics`, 10.4). Not in the tree: it changes the menu scene, which nobody has seen
   load in that form.
4. `menu_check`'s note 'pictures of the page' read `None` since the elements carry `_P2`: fixed.

### 10.2 The tree

    python tools\kl_expansion.py build --out <work>\build\w_tab --ready <work>\build\z_maps
           --prebuilt DM09=<work>\build\rt_guns3\retomoto_ai3_guns --overlay-from <work>\build\pd2\overlay
           --hook <SHIP dinput8.dll> --no-stream --no-share

`RESULT: PASS`, 5 maps accepted, 162 files, 1,232,801,550 bytes; `check`: all files as in the manifest.

| id | title | slot / entry | from | per-map files | archive MB |
|---|---|---|---|---|---:|
| DM01 | Hot Coffee | F01 / 0 | `z_maps\M01` | KLWardrobe.ini | 196.9 |
| DM02 | Late Night Opening | F02 / 1 | `z_maps\M02` | KLWardrobe.ini | 177.8 |
| DM03 | Withdrawal | F03 / 2 | `z_maps\M03` | KLWardrobe.ini | 188.5 |
| DM06 | A Walk in the Park | F04 / 3 | `z_maps\M06` | KLWardrobe.ini | 177.6 |
| DM09 | Retomoto Tower | F06 / 4 | `rt_guns3\retomoto_ai3_guns` | KLJoin.ini, KLWardrobe.ini, KLGuns.ini | 218.9 |

- `Overlay\Patch01.zip` (sha1 2b7c87ef...): frontend.xml 666,602 -> 693,673 bytes; Arcade page with eight rows:
  the five stock ones, 'Heister' (6), 'Guns' (7), 'Dead Men maps' (8, icon `Icon_System_Link`), group Y 8.
  `Overlay\Scenes\kaneandlynch.zip` = the installed one (sha1 30e0fd90...).
- No `Overlay\PC_Def.str` (`--no-stream`): `<DD>\PC_Def.str` already IS the merged file (1,684,486,009 bytes,
  the size of `<work>\build\PC_Def.str`; not hashed); install with `--no-stream`.
- `Hook\dinput8.dll` = the SHIP build of 13:46 (sha1 a6b58a51..., 237,056 bytes, `klhook\build.bat`), compiled from
  the working tree as it stood - INCLUDING the other agent's uncommitted klhook.c / klgun.c / klbot.c. The TEST
  build of the same minute: `<work>\build\w_tab\hook_test\dinput8.dll` (sha1 e46b69c8...). Both compiled without
  an error. `klcrew.c` appeared in `klhook\` after that; rebuild when that work lands (`build --reuse
  --overlay-from ...` without `--hook` compiles the SHIP build itself).
- Entries 5..8 of the page (F07 and the three DLC slots) keep their stock titles and load the stock maps.
- The page opens on the entry the profile played last (`Heist_SelectedLevel` is shared with the stock page).

### 10.3 Install (the lead; game closed)

    python tools\kl_expansion.py status
    python tools\kl_expansion.py install "<work>\build\w_tab\KLExpansion" --replace --no-stream [--no-hook]

- `--replace`: `<DD>\KLExpansion` is not an install of the tool (it holds the old test `Maps\DM03` and the
  overlay): it is MOVED to `<DD>\KLExpansion.before-0`, and moved back by `uninstall`.
- Copies `Maps\DM01 DM02 DM03 DM06 DM09`, `Overlay\Patch01.zip`, `Overlay\Scenes\kaneandlynch.zip`, `BuildInfo`,
  `manifest.json`, `KLHook.expansion.ini` to `<DD>\KLExpansion\`.
- `KLHook.ini`: `[Expansion] [Redirect] [Slots]` of the file are replaced by the block below between two marker
  lines; `[KLHook] [Steam] [Character] [Load] [Memory] [Guns]` stay as they are.
- Hook: without `--no-hook` the tree's SHIP DLL replaces `<DD>\dinput8.dll` (the old one is kept in
  `KLExpansion\_installed`). With `--no-hook` the installed one stays - any build since 0ad48d2 has the latch.
- **The F01 slot goes back to stock Subway by copy from `KL_PortBackup`** (which is only read), and the test
  build's `KLWardrobe.ini`, `KLJoin.ini`, `KLGuns.ini` beside it are renamed `<name>.of-test-build-N` (klchar.c and
  klgun.c read them beside ANY archive). `--keep-slot` leaves the slot alone. NOT `tools\RESTORE Dog Days
  originals.bat` for this: it puts EVERY backup file back, `PC_Def.str` included, and the maps' streamed clips
  index the merged file. `debug\slot.py` puts a BUILD into the slot; it has no 'stock' command.

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
F02=Late Night Opening
F03=Withdrawal
F04=A Walk in the Park
F06=Retomoto Tower
```

No `[Redirect]` section: the stock page and a direct boot (`-o DefaultScene=Locations/F01/F01_Main.gms`, the
unattended loop) load the STOCK level. For a direct-boot test of a map add `Page=2` under `[Expansion]` (F01 is
then the diner; another slot needs klauto's `CmdDrop=DefaultScene` / `CmdAdd=-o DefaultScene=...`).

Steam on stock maps afterwards (klsteam.c, SHIP policy): stock Subway is judged by size and directory hash
(`steam: level archive f01\f01_main.zip opened from ...: STOCK (217471616 bytes, directory hash 94c9f794)`) and
everything is passed on - upload, stats, achievements. Once a Dead Men map has RUN in a process, stats and
achievements stay blocked until the game is restarted (the stats block in memory is cumulative), the leaderboard
upload only while the current level is not stock. So: for scores that count, start the game and play stock maps
only. The SHIP policy on a stock level has not run live (checks S3 / S4 of `re/hook_live.md`).

### 10.4 The variant with Dead Men's pictures (NOT SEEN IN THE GAME)

    python tools\kl_expansion.py mappics <work>\build\w_tab\KLExpansion <work>\build\w_tab\with_map_pictures

`with_map_pictures\Overlay\Scenes\kaneandlynch.zip` (sha1 5be87b0d...) = the tree's menu scene + five picture
entities `LevelPicture_DM01 DM02 DM03 DM06 DM09` (540 x 304, one 'ABGR' tile each: the form of the Heister
pictures, kl_portraits' helpers; 6283 -> 6293 entities, 1025 textures; kl_portraits' check: 5 of 5 and 31 of 31
pictures, 0 problems); `with_map_pictures\Overlay\Patch01.zip` (sha1 2aad3e85...) = the tree's overlay with those
as the page's pictures - only the window `HeistPlayMenu2` differs. Without it the page shows the story picture
`LevelPicture_L0<slot>` (for F01: a Shanghai market street, MP2c_77s.png). To try: after TAB_PAGE has passed with
the tree, copy the TWO files over `<DD>\KLExpansion\Overlay\` (together), run TAB_PAGE again and look at the five
pictures; the tree's two files put it back. Risk: the menu scene is 10 entities and 10 MB of textures larger than
the one that ran; its heap budget (header +0x1c) was not raised.

### 10.5 Live checks (TEST hook; scripts `<work>\research\agent_scripts\w-tab\`, made by `mk_tab_inis.py`)

    python tools\kl_autotest.py 1200 --tag TAB_PAGE --hook <work>\build\w_tab\hook_test\dinput8.dll
           --ini <work>\research\agent_scripts\w-tab\TAB_PAGE.ini --shots 50-110:3

`TAB_PAGE.ini`: main menu -> Arcade -> seven times DOWN -> RETURN -> `HeistPlayMenu2`, steps the selector
`HeistLevel_P2` through entries 0..5 (3 s each), Back, waits 12 s. Then one run per map, `TAB_DM01 DM02 DM03
DM06 DM09.ini`: the same way in, `sel HeistLevel_P2 0xceceec <entry>`, `msg HeistLevel_P2 StartGame`, 40 s in
the level, `pass`. One process per map: no way back to the frontend without ending the session is known.
A wrong row count shows as `waitwin HeistPlayMenu2` failing with the stack in the reason (`... > KLGuns`).

Lines that prove it (here for DM09, entry 4; DM02 = F02 / entry 1, DM03 = F03 / 2, DM06 = F04 / 3, DM01 = F01 / 0):

```
expansion: [Redirect.2] Scenes\Locations\F06\ -> ...\KLExpansion\Maps\DM09\           (five such, each with its 'has ...' list)
expansion: menu page 2 is 'Dead Men maps'
expansion: CreateFileA overlay: ...\Patch01.zip -> ...\KLExpansion\Overlay\Patch01.zip
expansion: menu windows [MainMenu > HeistModeMenu > HeistPlayMenu2]
expansion: menu page 2 latched: window 'HeistPlayMenu2' is open ([Redirect.2] F01=DM01, F02=DM02, F03=DM03, F04=DM06, F06=DM09)
(the script's `expect 0xceceec 4` passes; exit 27 = the selector did not move)
session: state 0x0 -> 0x12 (game mode 4)
expansion: slot F06: menu page 2 from now on -> DM09
expansion: CreateFileA redirect: ...\SCENES\Locations\F06\F06_Main.zip -> ...\KLExpansion\Maps\DM09\F06_Main.zip
steam: level archive f06\f06_main.zip opened from ...\KLExpansion\Maps\DM09\F06_Main.zip: NOT stock (218912514 bytes, ...; the stock archive has 209504173 bytes, e035f328)
join: reading ...\KLExpansion\Maps\DM09\KLJoin.ini for level f06\f06_main            (DM09 only)
character: level f06\f06_main has a wardrobe (version 2): 16 characters, 12 masks (...\KLExpansion\Maps\DM09\KLWardrobe.ini)
guns: level f06\f06_main has 6 guns ...                                              (DM09 only)
expansion: CreateFileA redirect: ...\F06_Main.WHD -> ...\Maps\DM09\F06_Main.WHD      (and .WAV, seconds later)
steam: level 'SCENES\Locations\F06\F06_Main.gms' under the SHIP policy: its archive f06\f06_main.zip is not the stock one ... would be BLOCKED
```

Must NOT appear between `latched` and `slot F0n:`: `menu page 2 dropped`, `slot F0n: menu page 0`. In TAB_PAGE,
after Back: `expansion: menu page 2 dropped: the frontend shows [MainMenu > HeistModeMenu]` after about 1 s
(no start was seen), and no level archive open at all.

NOT KNOWN until these run: a level under the names F02, F03, F04, F06 (member names only differ; the engine's level
code, loading screen, briefing and score board are the stock slot's); `0xceceec` following the page's own selector
for a value other than 0 (MP2c only asked for 0); the eight-row Arcade page (its rows stand 68 units higher than
in MP2c; the installed overlay has seven rows); the four z_maps builds at all (re\maps.md 14.6).

### 10.6 What the owner will see

Arcade Mode has eight rows: Start Arcade Game, Arcade Rules, Arcade Stats, Arcade Highscores, Online
Leaderboards, Heister, Guns, **Dead Men maps**. That row opens a page headed 'Dead Men maps' that looks like the
stock map page (picture left, 'Your Criminal name' right, a 'Location:' row with arrows, Back / Accept); left /
right steps through Hot Coffee, Late Night Opening, Withdrawal, A Walk in the Park, Retomoto Tower - and then
four more entries that are stock maps under their stock names (slot F07 and the three DLC slots). No briefing
text. The picture is a story-mode picture, not the map's (10.4). Accept loads the map; the loading screen and the
lobby / score titles are those of the stock map whose slot it uses. 'Start Arcade Game' is the stock page with
the nine stock maps, Subway being Subway again. Heister and Guns are as installed.
