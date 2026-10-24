# 2026-10-24 scheduled check-in (cloud, 05:48-06:10 UTC = 06:48 PC clock): KLHook_1.dmp triage + installed .LOC verification

Nothing was launched or installed. The PC was idle (newest change 01:26 UTC, dinput8.dll / KLHook.log / KLHook.result,
build\plaindata_1024 at 01:26; four and a half hours before). KLHook.result: `state=PASS` (script reached pass, loads 2,
level_loaded 1, asserts 0, faults 0, frames 34607, F01 slot). KLHook.log tail (02:25 PC): bots in play, `RESULT PASS`.

## 1. KLHook_1.dmp (00:10 UTC = 01:10 PC) = FX2b's render-thread fault: StretchRect through ReShade into the NVIDIA driver

Read-only: `debug/dump.py --threads` with the staged kl2.exe. The 01:42 note already files this as "FX2b's
nvd3dum.dll+0x14160b render-thread crash at 34 s did not recur: one-off driver fault"; this keeps the evidence.

```
code 0xc0000005 at 0x5e65160b nvd3dum.dll+0x14160b (READING ADDRESS 0)    thread 58620 = the RENDER THREAD
eip=5e65160b esp=2bd2f1dc ebp=2bd2f1e8 eax=00000000 ebx=1b85fb00 ecx=5e651500 edx=203fef88 esi=3752c680 edi=2bd2f204
node loader counter 6304 of 6304 (the F01 load was complete)
main thread 26452: 0x841bb1 < 0x459b20 (waits for the render thread, no timeout) < 0x5c71cd (engine frame)
guest DLLs: ReShade32.dll (40/134), gameoverlayrenderer.dll, nvspcap.dll, medal-hook32.dll (133/134)
```

The live kl2.exe chain on the faulting thread (stack words 2bd2f584 down to 2bd2f1dc):

| frame | what |
|---|---|
| 0x56139e in 0x561260 | render-thread loop (0x561330): `call 0x7c1c30` with [esi+0xfc] = the frame's command list |
| 0x7c33eb in 0x7c1c30 | the render command interpreter (ebp = record, [ebp+0x18] = record size, dispatch by opcode); the record at 0x7c33cc: `StretchRect(src=[ebp+0x1c], srcRect=ebp+0x28, dst=[ebp+0x20], dstRect=ebp+0x38, filter=[ebp+0x24])` through the device wrapper at [0xf144a0] |
| 0x70ad87 in 0x70ad60 | the wrapper: `eax=[this+4]` = IDirect3DDevice9, `call [vtbl+0x88]` = slot 34 = **StretchRect** (5 args, `ret 0x14`) |
| ReShade32.dll+0x369728, +0x11ccf6, +0x11bddb | ReShade's device proxy sits between the game and d3d9.dll (it hooks the device, so every StretchRect goes through it) |
| d3d9.dll+0x5f4c4, +0x84611, +0x5f793, +0x616c0, +0x61768 | d3d9 runtime; the two RECTs on its stack are `{0,0,0x280,0x1e0}` = **640 x 480**, src 0x204df8c8, dst 0x203fef88 (edx) |
| nvd3dum.dll+0x1415e0 -> +0x14160b | the user-mode driver dereferences 0 |

So: a 640 x 480 surface-to-surface StretchRect, issued by the game's own render command list 34 s into the level, passed
through ReShade's proxy, and the NVIDIA user-mode driver read a null pointer inside d3d9's StretchRect path. The two
other kl2.exe addresses on that stack (0x6c7d42 = a SetViewport wrapper, `call [vtbl+0xbc]`, and 0x54abcc) sit between
ReShade frames and are stale values from an earlier, deeper call. A 640 x 480 blit is not the back buffer at the owner's
resolution (the record's surfaces are not identifiable from the dump without the device objects, which are driver memory):
candidates are a video / thumbnail / reflection render target. Not reproducible (FX2c, FX3, AB0, AB1, SC3, SC4, SMK27
and every later run passed on the same build), and the fault is in nvd3dum with ReShade in the call path, so the
verdict stays "one-off driver fault" - with the addition that **ReShade32.dll is in the path of every D3D call** on
this machine (ReShade.ini, ReShadePreset_KLLive.ini, reshade-shaders\ in the game folder): if a render-thread fault in
nvd3dum/d3d9 ever recurs, the first A/B is a run without ReShade (rename ReShade32.dll's loader, owner's call), before
anything in KLHook or the maps is suspected. Nothing to fix in the repo.

## 2. Installed Russian / Japanese .LOC files checked against the slot's stock file: the 02:00 heuristic bug DID land in DD01-DD09

The 02:00 commit (94982fa, kl_loc_fit ownership heuristic) left open whether any installed file had lost stock lines.
Checked now, read-only, on the PC: every `KLExpansion\Maps\*\*_Main.zip` Russian and Japanese `.LOC` against
`Scenes\Locations\F0n\F0n_Main.zip` of the same slot (F01 has no stock file in place: DD01, DM01, DM05A, T01 skipped).
Tool: new `kl_loc_fit.compare()` / `verify()` / `python kl_loc_fit.py --verify [DD]` (self-test in kl_loc_fit_test.py,
PASS); run from `<work>\build\locverify_1024\tools\`, report `<work>\build\locverify_1024\verify_report.txt`.

| zips | language | stock sound leaves | missing | subtitle blanked | sound id changed | text -> English | verdict |
|---|---|---|---|---|---|---|---|
| DD02 DD04 DD05 (PlainData 1024, installed 02:12) | Russian | 3616 | 0 | **248** | 0 | 3043 | FAULT (the bug's step 4) |
| DD03 DD06 DD07 DD08 DD09 (same build) | Russian | 3530 | 0 | **136** | 0 | 3072 | FAULT (the bug's step 4) |
| DD02-DD09 | Japanese | 3616 / 3530 | 0 | 0 | 0 | 0 | clean (585,491 / 576,132 bytes: never over the cap) |
| DM01B DM03 DM03A DM09* (1023 builds) | both | 3530 | 0 | 0 | 3530 (DM03A: 0) | 2538-2591 / 62-128 | clean; every id re-pointed = the kl_snd graft |
| DM02 DM06 DM06B DM11B (1023 builds, F02 / F04 slots) | both | 3616 | 86 | 0 | 3530 / 3511 | 1324-2564 / 0-68 | the 86 = ALL of the stock `L04/Dialogue/*` leaves (the slot map's own campaign one-liners; their banks go with the replaced map) - by design as far as the files show, not confirmed in code |

The 248 / 136 blanked Russian leaves are exactly the keys the old heuristic took for ours: all of them are stock
`Multiplayer/<F>/<Event>_C<n>` / `_R_C<n>` lines with no base key (e.g. `Multiplayer/All_Esc/AllEsc_02_C5`,
`Multiplayer/F01/MissionBriefing_03_R_C1`). The leaf, its flags and its sound id are intact (the line still PLAYS), only
the Russian subtitle is empty: step 4 ran, step 6 did not (missing 0). Japanese was never over the cap, so untouched.
DD01 was not compared (no stock F01 in place) but its Russian file has the same size as DD02/DD04/DD05 (612,593) and
stock F01 Russian is the same 612,634-byte file, so it is in the same state. The 1023 DM builds went through
`kl_loc_fit.stage()` WITH the stock reference (fit_report.txt: every member "stock reference yes", step 2 only), so
they never ran on the heuristic: clean.

What a rebuild with 94982fa does (computed on the installed DD02 / DD03 files, not run): the blanked stock subtitles
are 36,913 / 23,078 bytes; our 3,818 KLVoice sound leaves carry 67,524 bytes of (English) subtitle text in the Russian
file, so step 4 now blanks the 1,222 / 638 longest KLVoice subtitles instead and the file fits without raising. Trade:
Russian players keep every stock Russian subtitle and lose the English subtitle on about a third of the Dead Men lines
(the voice plays either way). The alternative - keep more Dead Men subtitles by swapping stock Russian subtitles to
English (step 2 already does this for 3,043 of them) - is the docstring's order and was not changed here.

Owner: nothing to decide unless you want the other trade. The local sessions rebuild DD01-DD09 (Russian only
differs) with HEAD when convenient; `python tools\kl_loc_fit.py --verify` afterwards must show `blanked 0` on every
DD row.

## 3. Second check-in of the day (09:48-10:10 UTC = 10:48 PC clock): the blanked subtitles REPAIRED into the work folder, not installed

PC idle again (newest change: `build\locverify_1024` 05:57 UTC, the game files 01:26 UTC; KLHook.result still `state=PASS`,
no new dump: KLHook_1.dmp 00:10 UTC is the one triaged above). Nothing launched or installed.

The 06:00 note left the fix to "a rebuild with HEAD". A rebuild is not needed: the damage is local to the .LOC member, so
`kl_loc_fit.repair()` (new) puts the stock text of every blanked stock SOUND leaf back from the slot's stock file (the leaf's own
tail - dword after the text and sound id - is kept, so a re-pointed id of a grafted map survives) and runs `fit()` again WITH the
stock file as the ownership reference; `--repair OUTDIR [DD]` does that for every installed zip, all languages, read-only on the
game folder, and writes only the repaired members. Stock files are found by `stock_zip()`: in place, else the moved original in
`KL_PortBackup` (read only) - which is how the F01 slot (DD01, DM01, DM05A, T01), skipped by every earlier `--verify`, got checked
for the first time. Self-test: `kl_loc_fit_test.py` +24 checks (78 -> 102) (repair on the bug's damage, re-pointed ids, pre-existing missing
leaves tolerated, impossible cap; repair_installed / install_repaired / verify on a fake game folder with the stock F01 only in
KL_PortBackup). PASS here and on the PC (python 3.10 in the device shell).

Run on the PC from `<work>\build\locrepair_1024\tools\`, output `<work>\build\locrepair_1024\<Map>\Scenes\Locations\F0n\
F0n_Main<Language>.LOC` + `repair_report.txt` (29 zips x 9 languages compared in under a minute):

| zip | language | stock subtitles blank | after repair + re-fit (stock reference) | size |
|---|---|---|---|---|
| DD01 DD02 DD04 DD05 | Russian | 248 | 0 blank, 0 missing; the 248 come back and step 2 turns them ENGLISH (longer than English, stock sound leaf, the docstring's order); step 4 blanks 623 of our 3,818 KLVoice subtitles instead (-22,664 bytes) | 612,593 -> 612,631 (cap 612,634) |
| DD03 DD06 DD07 DD08 DD09 | Russian | 136 | same; 354 KLVoice subtitles blanked instead | 612,608 -> 612,601 |
| **DM01** (F01 slot, 1023 build) | **Japanese** | **233** - NEW, unseen until now (F01 was never compared) | 0 blank; all 233 keep their re-pointed sound id ("233 with another tail kept" = the kl_snd graft), 231 turned English, 402 KLVoice subtitles blanked | 612,608 -> 612,627 |
| every other member of the 29 zips (DD01-DD09 other languages, DM01B..DM11B, T01, DM05A) | all 9 | 0 | nothing written | |

DM01's `missing 86` (L04/Dialogue, the F01 slot map's own one-liners) is pre-existing and stays: repair() only refuses a result
with blanked stock subtitles or MORE missing / re-flagged leaves than its input (that distinction was the one bug found while
running it: the first version refused DM01 for the 86).

So the installed Russian files show the 248 / 136 lines as English subtitles after the repair, not Russian: step 2 ("stock keys
with a sound -> English subtitle") runs before step 4 by design, and 3,043 of the 3,616 stock Russian subtitles in those files
were English already. The other trade (keep them Russian, blank ~600 more Dead Men subtitles) needs the step order changed;
not done (the 06:00 note described it, nobody asked for it).

NOT installed (a game-folder change, owner / local session): `python tools\kl_loc_fit.py --install <work>\build\locrepair_1024`
rewrites the 10 zips beside themselves (10 x ~250 MB, backups `<zip>.before-locrepair`, +2.5 GB on C:), re-checks each member
against stock, then `python tools\kl_loc_fit.py --verify` must say `blanked 0` on every row (DM01 Japanese included now).
Owner's call too: the ~41 GB of `*.before-*` backups under KLExpansion\Maps (850 files) are what makes C: tight.
