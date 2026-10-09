# A Dead Men map in its own folder: redirect, menu entry, install layout

Offline work of 2026-10-09 (label r-slot). **Nothing here has run in the game.** Method: pefile +
capstone on `kl2.exe` (sha1 9d99e01d..., TimeDateStamp 0x4c80f728, base 0x400000), and an off-game
harness for the code (section 8). Builds on `re/fa_slots.md` (the nine-slot table), `re/menus.md`
(togglers, pages of nine) and the boot-config research (`research/v2_f153...json`: Patch01.zip).
Words used: "read" = I disassembled it for this document; "earlier" = taken from those documents
and not re-read; ASSUMPTION = not established by anyone.

Code: `klhook/klslot.c` (new, not yet part of any build - section 7).

## 0. Result in short

1. Every file name of a level is derived from ONE string (the scene path), and every one of the
   game's own narrow-character file opens leaves `kl2.exe` through one import-table entry
   (`CreateFileA`, 17 call sites, section 1). Wrapping that entry (plus four more for safety) needs
   no address of the exe and catches the archive, the `.WHD/.WAV`, the `_LS` files and `Patch01.zip`
   alike.
2. First step, implemented: `[Redirect] F01=DM03` in `KLHook.ini`. While that line is there, files
   under `Scenes\Locations\F01\` are opened from `KLExpansion\Maps\DM03\`; the stock F01 files stay
   in place and untouched. The engine still thinks it loads `Locations/F01/F01_Main`, so the build
   is the one made for the F01 slot today, and the owner's launch options
   (`-o DefaultScene=Locations/F01/F01_Main.gms`) and `kl_autotest.py` work unchanged.
   **The F01 "test slot" no longer has to be overwritten.**
3. The menu side needs no change to the stock `Patch01.zip` on disk: either a complete replacement
   is opened in its place (`KLExpansion\Overlay\Patch01.zip`, same wrapper), or an extra archive is
   mounted in front of it (`MountFirst=`, one 5-byte patch at 0x7f5610, section 3). Both implemented.
4. A tenth entry stays impossible; the menu-selected version is a second page of nine whose page
   number selects the redirect table (section 5, plan only).
5. Remove `dinput8.dll` and the folder `KLExpansion` and the game is stock (section 6).

## 1. From level name to file paths

| step | where | what | status |
|---|---|---|---|
| slot index -> name | level list `[0x168f750]` slot 15 (0x7c5ca0): `this + 0x16 + idx*0x40` | `Locations/F01/F01_Main` | earlier (fa_slots.md 1, 2); the nine constructor pushes re-read, table in klslot.c |
| name -> scene | 0x86f230: `%s%s` with `.gms` or `.zip`, EngineDataBase vtbl+0x74 | `Locations/F01/F01_Main.gms` | earlier |
| boot scene | `DefaultScene` -> sysif+0x2b0, prefixed with ScenesPath (sysif+0x1b0) | does NOT pass the slot table | earlier; live: the owner's launch options |
| scene -> every member / side file | **0x60c410 -> 0x6d6550**: copies the scene path at EngineDataBase+0xd4 and gives it the pushed extension (only the first half of 0x6d6550 was read: last `\`, `.gms` / `.zip` tests) | one path per extension | read: 46 direct callers of 0x60c410, extensions HVK WAV WHD anm buf col fxc gms gst hrd loc mat oct prm prp prx rmc rmi sgd sgp snd sup zgf zip |
| archive | scene loader 0x7f4f90: `zip` name at 0x7f561c..0x7f562b, mounted at 0x7f5827 (FS vtbl+0x90) | `<Scenes>\Locations\F01\F01_Main.zip` | read |
| `.WHD` / `.WAV` | requested in the scene load itself (0x820817, 0x820879 inside 0x820300) and by 0x6c68d2, 0x7ed92a, 0x49bf4a, 0x77b322 | beside the zip | read (the requests); who opens them: not traced |
| `_LS` sound | 0x8ffd60: `<zip path minus .zip>_LS_<Language>.WHD/.WAV`, `_LS.SND`; language, then `Default`, then none (0x7f572c..0x7f5768) | beside the zip, optional | read (call sequence); strings `_LS_` 0xb45344, `_LS` 0xb4a234 |
| `.LOC` | `loc` request 0x49e077; `<name><Language>.LOC` members | inside the zip | earlier (fa_slots.md 4) |
| `Loader_Sequence.zip` | 0x565500: level folder, else `\AllLevels\Loader_Sequence.ZIP` (0xb39000) | optional | earlier |
| `.hti` | - | never opened | earlier (no such string in the exe) |

So the level folder is one directory holding `F01_Main.zip` (members named
`Scenes/Locations/F01/F01_Main.<ext>`), `F01_Main.WHD/.WAV`, `F01_Main_LS.SND`,
`F01_Main_LS_<Language>.WHD/.WAV` and optionally `Loader_Sequence.zip/.WHD/.WAV`. The stock F01
folder and the test-slot folder were listed: exactly these files (plus `.hti`).

### The file-open layer (read)

- File system object: `[0xdd263c]`, class `ZSysFileWintel` (vtable 0xb8ed84, RTTI).
- `CreateFileA` is import `[0xb10270]`. 17 references in `.text`, all `call [0xb10270]` or
  `mov esi,[0xb10270]`:

  | caller | class / slot | open |
  |---|---|---|
  | 0x5e2aa0 | ZSysFileWintel 2 | `GENERIC_READ, share read, OPEN_EXISTING, 0x8000080` (the mount's existence probe) |
  | 0x7f70a0, 0x5085e0, 0x77e910, 0x789930 | ZSysFileWintel 3, 4, 5, 6 | variants |
  | 0x43d120 | AsyncFd_Windows 4 | read |
  | 0x7a2f30 | ZIOStreamerWintel 5 | `GENERIC_READ, share read, OPEN_EXISTING, 0x80` (streams) |
  | 0x67e810 | ZDllSound / ZDllSoundWintel 36 | read |
  | 0x5432d0 | DLC presence test, `Scenes/%s.zip` | read |
  | 0x476730 | WinMain (`kl2.ini` / `main.ini` probe) | |
  | 0x47c5f0, 0x6587c0 | ZFFPlayerProfileWintel 16, 18 | profile |
  | 0x6b2b10 | - | `GENERIC_ALL, CREATE_ALWAYS` - a writer |
  | 0x7aeb10, 0xb0f4a0, 0xb0f520, 0xb0f5a0 | - | read |

- Others: `fopen` `[0xb10430]` 8 calls (one is `IOFSPhysicalAccess_t` slot 0, 0x74db40, path from
  FS vtbl+0xdc); `GetFileAttributesA` 1 call (0x7606e0); `FindFirstFileA` 3 calls (ZSysFileWintel
  slots 14, 66, 67); `CreateFileW` 104 references (not classified - the pattern looks like generated
  stream code; ASSUMPTION that level data does not go through it).
- KERNEL32 and MSVCR90 are imported by name with an OriginalFirstThunk table (0x8cce54 / 0x8cd080) and
  are not bound, so the entries can be found by name at run time.
- NOT established: which of these calls opens the archive's data after the mount probe, and the
  `.WHD/.WAV`. That is the reason all five imports are wrapped and for `Log=2` (first live check).

### Where a redirect can sit - compared

| | A. slot table string (fa_slots.md 5) | B. path builder 0x6d6550 / scene name | **C. file opens (chosen first step)** |
|---|---|---|---|
| covers Arcade / FA lobby | yes | yes | yes |
| covers `-o DefaultScene=` (the autotest) | **no** | yes | yes |
| covers a network client (index -> own table) | yes, if it has the same ini | yes | yes, same condition |
| archive member names | new name (`F0M03_Main.*`): the packager must build under it | new name | **stock slot name: today's build as it is** |
| engine's view of the level | unknown name: level code 0 (fa_slots.md 2), FA tests pass only with an `F0<tag>` name | same | the stock level: every name test behaves as for Subway |
| addresses of kl2.exe used | 9 (+1 session default, +3 lock bytes) | a detour in a 0x1c0-byte function with 46 callers | **none** |
| menu overrides (`Patch01.zip`) | no | no | **yes, same mechanism** |
| can use an unowned DLC slot (nothing stock hidden) | **yes** (lock byte released for the renamed slot) | - | no: a slot that keeps its stock name must stay locked |
| one build usable in any slot | yes | yes | no: the build carries its slot's name |

C is the smallest thing that can fail and the only one that also serves the unattended loop. A is
kept as the second mode (`[Slots]`), because it is what lets a Dead Men map occupy an unowned DLC
slot so that NO stock map disappears from the list; it needs the level under
`KLExpansion\Overlay\Scenes\Locations\F0M03\` (found through C's overlay) and a packager that
builds under that name. B was not written.

What C costs while it is active: the stock map of that slot is not playable (remove the ini line
to get it back - no file moves), its menu title / picture / briefing stay the stock ones until the
menu is overridden (section 4), and code keyed on the slot treats the map as the stock one - above
all the leaderboard choice (`0x80c9f0(current slot)`, fa_slots.md 5; earlier). **Arcade scores of a
redirected map would be reported under the stock map's board: play with Steam offline until a
leaderboard guard exists.** The same is already true of today's install over the F01 slot.

## 2. How archives are mounted (read)

Scene loader 0x7f4f90, every scene load:

```
7f55f0  mov ecx,[0xdd263c] ; mov eax,[ecx] ; mov edx,[eax+0xac] ; call edx      unmount every archive
7f5600  mov ecx,[0xdd263c] ; mov eax,[ecx] ; mov edx,[eax+0x98]
7f560e  push 1
7f5610  push 0xb251fc "Patch01.zip"                    bytes 68 fc 51 b2 00
7f5615  call edx                                       bytes ff d2      Mount(name, 1)
7f5617  call 0x4441e0
7f561c  push "zip" ... call 0x60c410                   the scene's archive name
7f572c  call 0x8ffd60 (language) / 7f5745 ("Default")  the _LS sound, before the archive is mounted
7f5827  call [FS vtbl+0x90](name)                      mount the scene archive
```

- vtbl+0x98 = slot 38 0x72f800: forwards (name, flag) to vtbl+0x13c = slot 79 0x809200, returns 1.
- Slot 79: copies the name, `\` -> `/`, writes `.zip` over the text from the last `.` (no `.` at
  all: nothing happens, 0x8092cb), asks vtbl+0xa8(name) and returns if that says yes (already
  mounted - my reading of the name, not traced), probes with slot 2 (`CreateFileA`, above) and
  returns quietly if the file is missing (0x80930a), creates the list at FS+4 on first use, creates
  a 0x78-byte `FsZip_t` (0x718970) and calls its vtbl+0x38(path, flag ? 5 : 2).
- `Patch01.zip` is passed as written, i.e. relative to the current directory. 0xb251fc has one
  reference (0x7f5611). There is no second patch name.
- Order of lookup - first mounted archive that has the member wins, archives before loose files:
  earlier (FS slot 30 0x468bb0, slot 13 0x558730), not re-read, never observed.
- What flag 1 (mode 5) changes against the scene archive's mode: not established.

**Can KLHook add an archive? Yes, two ways, both in klslot.c:**

1. `KLExpansion\Overlay\Patch01.zip`: the open of `Patch01.zip` is answered with this file. It
   must be a COMPLETE patch archive (the two stock members `menu/frontend.xml`, `menu/ingame.xml`
   with our changes, plus anything added). Depends on nothing but "the game opens Patch01.zip
   through one of the five wrapped imports".
2. `MountFirst=KLExpansion/KLPatch.zip`: the 5-byte `push` at 0x7f5610 becomes `call stub`; the stub
   calls the same Mount for our archive first, then re-creates the push and returns to the stock
   `call edx`. The archive then holds ONLY our members. Depends on the mount order being what the
   earlier research read. No branch in `.text` targets 0x7f5610..0x7f5616 (every rel32 and rel8
   branch scanned), and the patch keeps the instruction length.

Use 1 first (fewer assumptions); 2 is the test of the mount order and the nicer layout later.

## 3. klslot.c

`KLHook.ini`:

```ini
[Expansion]
Enable=1
Root=KLExpansion        ; folder next to kl2.exe
Overlay=1               ; <Root>\Overlay\<path relative to the game folder> replaces the game's file
Fallback=1              ; file missing from Maps\<map>: 1 stock file (logged), 0 the open fails
Log=1                   ; 1 every redirect once, 2 also every other open once
;MountFirst=KLExpansion/KLPatch.zip
[Redirect]              ; <folder under Scenes\Locations> = <folder under Root\Maps>
F01=DM03
[Slots]                 ; name mode (fa_slots.md 5): F01..F09 = scene name, max 63 characters
;F09=Locations/F0M03/F0M03_Main
```

- Five import entries of the exe are replaced (`CreateFileA`, `CreateFileW`, `GetFileAttributesA`,
  `FindFirstFileA`, `fopen`), found by name. Only read-only opens of existing files are looked at
  (`OPEN_EXISTING` without any write right; `fopen` mode `r` without `+`); writes always pass through.
- A path is made absolute first (`GetFullPathNameA`: `/`, `..`, relative names), compared without
  case. A rule matches the component sequence `\scenes\locations\<slot>\` anywhere in it, so it does
  not depend on where ScenesPath points. Paths already inside `Root` are never mapped again.
- Rule hit and the file exists in the map folder -> opened there. Missing -> `Fallback`. Then the
  overlay test. `GetLastError` is preserved when nothing is mapped.
- At start it logs each rule, the files the map folder holds, and every stock file of that slot
  without a counterpart (those would come from the stock level - with `F01_Main.zip` from the map
  and `F01_Main.WAV` from stock the sound offsets would not fit, so read that list).
- `[Slots]`, `MountFirst` and the watcher (logs `available / present / name` of the nine slots once
  the level list exists, keeps a RENAMED slot available) only run on the known exe (base, time
  stamp, image size) and only write after comparing the bytes. Sites: 0x836016.. (nine pushes),
  0x69981e (session default, F01 only), 0x8468ea / ee / f2 (lock byte of a renamed DLC slot),
  0x7f5610. None is a site of klauto.c.
- It never releases the lock of a slot that keeps its stock name (that would unlock paid content).

## 4. Name and picture of the entry

From menus.md / fa_slots.md (earlier), with what the overlay now makes possible:

| what | where it comes from | override without touching stock files |
|---|---|---|
| Arcade title | `<Text>` children of `HeistLevel` in `menu/frontend.xml` (Patch01 copy is the one in effect) | `Overlay\Patch01.zip` with `<Text Text="%Withdrawal" />` in that position (`%` = literal, menus.md 2.6) |
| FA lobby title, tag `LevelName` | code: LOC `/Menu/Online/Scenarios/Title%02i` (slot + 1) in `Scenes/kaneandlynch<Language>.LOC` and each level's LOC | `kaneandlynch<Language>.LOC` as members of the patch archive (ASSUMPTION: the patch overrides LOC members like XML; not observed), and the map's own LOC - ours anyway |
| picture | `Graphic="LevelPicture_H01"` = an entity of the frontend scene, texture in `Scenes/kaneandlynch.TEX` | cheapest: point the entry at another stock picture in the XML. A new picture = `kaneandlynch.TEX` / `.gms` / `.prp` / `.buf` members with one texture replaced, in the patch archive (85 MB member; whether a patch may carry scene members is not observed), or a whole `Overlay\Scenes\kaneandlynch.zip` |
| briefing (`HeistBriefing`) | code, per slot | leave, or drop the element on the new page |

The build of `Overlay\Patch01.zip` (stock members read from the owner's `Patch01.zip`, one XML
changed) is a small packager job - not written, see section 9.

## 5. Menu-selected version (plan)

A tenth entry needs about fifteen code sites (fa_slots.md 6); pages of nine need none (menus.md 8.2).
With the file redirect the page mechanism becomes a table lookup:

1. `Overlay\Patch01.zip` carries `menu/frontend.xml` with a second window `HeistPlayMenu2`
   ("Dead Men maps", literal titles, stock pictures reused) and two buttons on `HeistModeMenu` that
   set the spare option `Dummy` to 1 / 2 (XML in menus.md 8.2; the option is at
   `[[0x154d5f4]+0xd4]` - earlier, not re-read).
2. klslot.c gets `[Redirect.2]` (same syntax; `[Redirect]` stays "always"). The page is read from
   the option and LATCHED when the open of `Patch01.zip` is seen: that open is the first thing of
   every scene load (0x7f5615, before the `_LS` files at 0x7f572c and the archive at 0x7f5827 -
   read), so one load never mixes two tables. Where `Loader_Sequence.zip` is opened relative to
   that is not established; `Log=2` shows the order.
3. Each expansion map is built for the stock slot of its entry: entry k of the page loads slot
   `{0,1,2,3,5,6,4,7,8}[k]`. Unused entries: no rule -> the stock map (or hide them: the selector
   skips unavailable slots, which needs the level list's slot 5 answered by the hook - later).
4. Nothing about the engine's level list changes, so a profile saved with the hook is valid
   without it (`Heist_SelectedLevel` stays 0..8).

Alternatives considered: one entry that cycles through expansion maps (needs the same page state
plus a custom toggler - more code for less), and name mode with unowned DLC slots (at most three
maps, but then stock and Dead Men maps sit in ONE list: worth doing for the first one to three maps
once the packager can build under an `F0<tag>` name).

Online (stage 4): a client turns the replicated slot index into a file through its own table, so
every peer needs the same ini lines and the same map folder; the page number is not replicated.
That needs a handshake before it is offered - not designed here (netcode.md).

## 6. Install layout

```
<Dog Days>\
  dinput8.dll                      KLHook (klhook.c + klauto.c + klslot.c)
  KLHook.ini                       [Expansion] / [Redirect] / [Slots]
  KLExpansion\
    Maps\DM03\                     one folder per map, files named for the slot it is built for:
      F01_Main.zip                   members Scenes/Locations/F01/F01_Main.*
      F01_Main.WHD  F01_Main.WAV
      F01_Main_LS.SND  F01_Main_LS_<Language>.WHD/.WAV   (8 languages incl. Default)
      Loader_Sequence.zip/.WHD/.WAV  (optional: else the stock slot's is used)
    Overlay\Patch01.zip            (optional) complete patch archive with our menu XML
    Overlay\Scenes\Locations\F0M03\...   (name mode only)
    KLPatch.zip                    (optional, MountFirst)
  Scenes\ , Patch01.zip , KL_PortBackup\     untouched
```

Uninstall: delete `dinput8.dll`, `KLHook.ini` and `KLExpansion\`. Switch a map off: remove its
`[Redirect]` line (or `Enable=0`).

## 7. Building it in

klslot.c has no `DllMain`; it uses klhook.c's `dir`, `klog`, `img_lo`. In `klhook\klauto.c`:

```c
#undef DllMain
#endif
#include "klslot.c"                                   /* <- add (below the block that includes klhook.c) */
...
    if (reason == DLL_PROCESS_ATTACH) { kls_init(inst); kla_init(inst); }     /* <- was: kla_init(inst); */
```

`build_auto.bat` needs no change. Built exactly so in scratch (`cl 19.4x x86 /O2 /LD`): `/W4` gives
no warning from klslot.c (two from klhook.c / klauto.c as before); the `/W3` build exports
`DirectInput8Create` as before. Whoever writes `KLHook.ini` for a test run (kl_autotest /
KLHook.round.ini) must keep the `[Expansion]` and `[Redirect]` sections.

For the loop, in someone else's files: the install step of `kl_graft.py` / `kl_package` would copy
the build to `<DD>\KLExpansion\Maps\<map>\` instead of `<DD>\Scenes\Locations\F01\`, after
`RESTORE Dog Days originals.bat` has put the stock F01 back once.

## 8. What was tested (off-game) and what was not

Harness in the scratch folder (`build\harness.c`, a 32-bit exe that loads the built `dinput8.dll`
in a made-up game folder, and maps the real `kl2.exe` as data). Run 2026-10-09, 25 checks, all ok:

- wrappers: F01 zip / WAV / WHD come from `Maps\DM03` (relative with `\`, relative with `/`, absolute
  in another case, with `..`); a file missing from the map folder comes from stock with
  `Fallback=1` and fails with `Fallback=0`; F02 untouched; `Patch01.zip` from the overlay; an
  overlay-only level opens; `CreateFileW`, `fopen`, `GetFileAttributesA`, `FindFirstFileA` follow;
  a write lands in the stock folder; `GetLastError` untouched; `Enable=0`: nothing redirected and
  no log line; a rule with a missing folder or a name with `..` is refused and logged.
- patcher on the real bytes: `[Slots]` F01 + F09 and `MountFirst` change exactly 18 bytes
  (0x836017-1a, 0x69981f-22, 0x8360ac-af, 0x8468ed, 0x7f5610-14); operands point at our strings.
- the installed mount stub, called from a synthetic copy of 0x7f5600..0x7f5617: Mount is called
  twice with the same `ecx`, first `KLExpansion/KLPatch.zip` flag 1, then the pointer 0xb251fc
  flag 1; the stack is balanced.

Not shown by any of this: that the game opens its level files through the wrapped imports, that the
import table is already resolved when our DllMain runs (the code checks and reports), that code
patched from DllMain survives (klauto.c's live runs suggest so), the mount order.

### First live checks, in this order

1. `Enable=1`, `Log=2`, no `[Redirect]`, stock F01 restored. Expect in KLHook.log
   `expansion: 5 import(s) of the exe wrapped (CreateFileA yes, ...)` and one `open:` line per
   distinct file with the API that opened it. Read off: the API and spelling for `Patch01.zip`,
   `F01_Main.zip`, `.WHD`, `.WAV`, `_LS_*`, `Loader_Sequence.zip`, and their order. A level file
   that never appears is opened another way (then: wrap that import, or go to mode A).
   The run must end like a stock run.
2. Copy the current graft build to `KLExpansion\Maps\DM03\`, add `F01=DM03`, `Log=1`; autotest.
   Expect the same RESULT line as with the build installed over the slot, `redirect:` lines for the
   zip, WHD, WAV and `_LS` files, and "stock file used" only for `Loader_Sequence.*`.
   Then delete the `[Redirect]` line: stock Subway loads again with no file moved.
3. `Overlay\Patch01.zip` = a byte copy of the stock file: no change. Then one visible text changed
   in its `menu/frontend.xml`: the change shows in the frontend (needs a menu run, not the
   DefaultScene boot).
4. `MountFirst` with an archive holding only that `menu/frontend.xml`, overlay copy removed: the
   change still shows = mount order confirmed (it does not show = last mounted wins: swap the stub
   to mount ours after Patch01).
5. `[Slots] F09=...` with a level under `Overlay\Scenes\Locations\<name>\`: the watcher's nine lines,
   `available=1` for slot 8, Arcade position 8 loads it. Needs a build under that name.
6. For section 5: log the dword at `[[0x154d5f4]+0xd4]` while changing pages (`peek` of klauto.c).

## 9. Open points

- A leaderboard / statistics guard while a redirect is active (which calls to stop: not read).
- Packager jobs outside this track: install into `KLExpansion\Maps\<map>\`; a builder for
  `Overlay\Patch01.zip`; a build under an `F0<tag>` name for mode A.
- `CreateFileW` callers (104) unclassified; `MoveFile` / `CopyFile` / `DeleteFile` are not wrapped
  (the game has no reason to use them on level files - ASSUMPTION).
- Paths longer than 259 characters are not mapped.
- What mount flag 1 means; whether vtbl+0xa8 is really "already mounted".
- Whether a patch archive may override LOC and scene members (needed for lobby titles and new
  pictures).
