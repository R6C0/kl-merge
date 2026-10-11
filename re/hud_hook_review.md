# Review of track V - klhud.c Version 2 (the owner's HUD draft)

Adversarial review, 2026-10-11 evening. Offline: kl2.exe re-read with `debug/dasm.py`, `klhook/klhud.c` (working
tree, sha1 cb369e0c, identical to the worker's `G:\kl_scratch\V\src` copy) read line by line, the game folder's
`KLHook.log` read only, the compile re-run. Nothing was run in the game; the worker's files were not changed.

## Verdict: ACCEPT WITH FIXES

The draw path Version 2 rests on is the stock form in every argument I could check, and the report's account of
what is proven and what is not is accurate. Two MUST points, both in the stock block's hide / show logic, should
go in before any run with `HideStock=1` (the default); neither blocks a first TEST run H1 if `HideStock=0` is set.
Nothing here is ready for the owner's tab: no part of Version 2 has run.

## What was re-read and holds

| Claim | Evidence | Result |
|---|---|---|
| xform = {0,0,1, 0,1,0, 1,0,0} | 0x7f07a0: `fld1; fst [+0x18]; fldz; fst [+0x1c] [+0x20] [+0xc] [+0x14] [+0]; fstp [+4]; fst [+0x10]; fstp [+8]` | holds |
| Text Draw is `(ctx, cam, &xform9, &pos3)` | 0x81e0f7 .. 0x81e10b: push pos, push xform, push ebx (arg 2), push edi (arg 1), call [vt+0x1e8] | holds |
| pos z = 0 is the stock value | Stock passes `elem+0x1c`; 0x8f7420 does use z (0x8f75b5, into 0x725fb0). The clock's z is 0: log 09:01:53 `hud: twin: the timer's text ... at (1216.0, 36.0, 0.0)` | holds |
| Draw=2 draws one pair and nothing else with `elem+0xbc` = 0 | 0x81e142 `cmp byte [esi+0xbc], 0; je 0x81e2c8`; before it only the two Draws | holds |
| Draw=2 draws only in state 0x19 | 0x81e0c3 `cmp eax, 0x19; jne` | holds |
| DrawChunk order (chunk, desc, xform9, pos3, layer, 1, 0) | 0x81e251 .. 0x81e275; `ret 0x1c` at 0x842d1f | holds |
| Picture handle = `[[elem+8] + 12 n]` | 0x81e172 / 0x81e180: `[elem+8] + 0x7f8` (170) or `+ 0x804` (171), then `mov ecx, [edx]` | holds |
| A stack desc and a static record are safe | 0x842de9 .. 0x842e03: DrawChunk copies desc[0], desc[1], points its own [+8] at its own buffer and memcpy's `count x size` bytes FROM `[desc+8]` | holds, and settles the code's "which of the two was not followed": only the pointed-at record is read; the copy written back into the desc is unused |
| 0x5a3e90 takes (out3, in2) | reads `[in]`, `[in+4]` only, writes out[0..2], z = 0 | holds |
| `[0xceeebc]` is plain data | `.data` starts 0xcd7000 | holds (policy: data) |
| HudFade and klhud.c write different fields | klfedkit.c 743 - 746 writes +0xee0 / +0xf00 only, and tests slot 5 of the list's vtable, which Version 2 no longer wraps (Reuse is gone) | holds: no fight |
| Render and tick do not collide on the lock | log 11:25: `2695 timer-element calls ... 0 lock busy` in every 5 s line | holds |
| A new round is a new scene and is seen | log 16:37:34 `osd 72156020 is over (the scene changed)`, 16:37:44 `osd 7c520210` | holds |
| Report: no HUD process after 16:30:28, no `pictest` line | `hud: on` last at 16:30:28; that process's `hud: render` lines run to 18:15 with `draw_on 0`; no `pictest` anywhere; `<DD>\dinput8.dll` is 37949c06, the ini has no `[HUD]` | holds |
| Off by default, nothing on a stock level | `klu_init` returns before any key when `Enable=0`; `allowed` (line 739) gates the vtable wrap, the inset, the make and the hide | holds, but see S5 |
| Files touched | klhud.c, the `[HUD]` hunk of KLHook.ini (one hunk), re/hud.md, re/hud_hook.md | inside the task's list |

Compile re-run from `git archive HEAD klhook` + this klhud.c in `G:\kl_scratch\V_review` (removed afterwards): no
warning, no error; `built ...\test\dinput8.dll (TEST)` 4470c4a9, `built ...\ship\dinput8.dll (SHIP)` 2bf4e1f2.
The hashes differ from the worker's 456b14a3 / 8bdf954d although the klhud.c is byte-identical: the build is not
reproducible by hash (or HEAD moved in between) - name builds by source commit, not by sha1 alone.

## MUST

**M1. The hook un-hides the stock block when the GAME has hidden it.** The game's own hide, 0x75f780(osd, b),
writes the same byte `+0x25` of the clock (`osd+0x10cc`, 0x75f796) AND of the player list (`osd+0x10c4`,
0x75f7a8). Six call sites: `push 1` at 0x51bc7e, 0x7085f3, 0x73e891, 0x7dfb6d; `push 0` at 0x6d856e, 0x70bfa8.
In klhud.c: we hold the list hidden (`klu_r.hid = 1`) -> the game hides the set -> `klu_fa_shown` is 0 because
the clock is hidden (line 652) -> `show = 0` -> `klu_hide_tick(osd, 0)` (line 779) finds `hid && h` and writes
0 (line 641 - 643). The stock name / Total score / list then stands alone on screen exactly while the game wants
the whole FA set gone. This path is hot, not rare: in the owner's round of 16:32 - 16:37 the pair `stock block
shown again` / `stock block hidden` alternates 10 times, 0.6 - 30 s apart. Fix: in the un-hide, read the clock
element's `+0x25` first; if it is 1 the hide is now the game's - set `klu_r.hid = 0` and leave the byte.

**M2. Two exits leave the stock block hidden with ours not drawing.** (a) Line 759: `klu_vtable_tick` failing
sets `fault = 1` and returns; every later tick returns at line 756; neither calls `klu_hide_tick(osd, 0)`. Only
the fault set inside the make / apply block reaches the un-hide at line 777. (b) Line 758: the transform not
reading 1280 x 720 turns `klu_draw_on` off and returns without un-hiding. Fix: one exit that un-hides (subject to
M1) wherever `klu_draw_on` is set to 0 while `osd` is still valid. The task named this case.

## SHOULD

**S1. 'No scan, no hitch' is not what the code does at a level start.** `klu_osd_direct` returns 0 both when the
holder is empty and when the OSD is there but `klu_osd_ok` fails; line 715 then scans. The log shows the same
test failing on the first tick of each level: 16:37:44.197 `2 ZOnScreenDisplay2 object(s) found in 157 ms`, the
OSD accepted one tick later (16:32:53: 125 ms). So the 0.1 - 0.3 s main-thread scan still runs once or more per
level, in the countdown. Fix: when the direct route yields an object with ZOnScreenDisplay2's vtable, wait for
it; scan only when the holder gives nothing.

**S2. Per-frame cost: about 150 ReadProcessMemory calls per clock-element call.** `klh_rd` is
`ReadProcessMemory` (klhook.c 214). `klu_draw_one` makes two per draw, the loop one or two more per text, about
60 draws (35 texts + 25 shadows); with `Plates=1` each `klu_pic` adds about seven. The log has 2,500 - 2,770
clock-element calls per 5 s, so roughly 80,000 system calls a second on the frame path. Not measured; the
nudge finding (1 ms a frame cost the owner 120 s loads) says to be careful. Fix: validate the objects' vtables
in the 100 ms tick (already done in `klu_apply`), and in the render slot read them directly, as `klu_draw_stock`
already does with the element.

**S3. Draw=2 cannot show what check H1b asks for.** (a) The Grid labels are `plain` (no shadow, line 455) and
`klu_draw_stock` refuses a text without one (line 238): no corner labels with `Draw=2`. (b) In states 0x17 /
0x18 the stock Render returns without drawing, `klu_draw_stock` still returns 1 and the stock block is hidden:
the countdown shows neither list. Fix: make shadows for the labels when `Draw=2`, and with `Draw=2` show (and
hide) only in state 0x19.

**S4. A stale level is told only by the scene name and an unchanged vtable dword.** `klu_current_osd` keeps
`klu_r.osd` while its first dword is the OSD's vtable; `klu_apply` and `klu_draw_one` trust a text while its
first dword is ZCHAROBJ's. Freed heap keeps those dwords. Today's rounds changed the scene name and the OSD's
address, so it held; a reload that keeps the name between two 100 ms ticks, or reuses the address, would draw
freed objects. Also `klh_scene` failing once mid-round resets `klu_r` (hid forgotten, the byte still 1) and
makes a second set of 60 objects. Fix: also reset when the Arcade rules object changes (klbot.c logs a new one
per round: 19122950 -> 7d5a6030) or the session state drops below 0x16, and ignore an empty scene read while
the OSD is still valid.

**S5. `Inset` outlives the level it was set on.** Written once on an allowed level and 'not put back' (line
764): the next stock level in the same process draws its clock and ammo panel at the new margin. Off by
default; put the old value back at the scene change, or say so beside the key in KLHook.ini.

**S6. Marked as fact, not read.** (a) Section 3 of the header: width / height 'in camera units = pixels x
T[+0xc] / T[+0x10]' - no instruction is cited; PicTest's A against B decides it, say so. (b) DrawChunk's record
size is chosen by the chunk's type dword `[chunk+0xc]` (0x842dc8: 24, 40 or 0x74 bytes a record, or 0x54 + 64
n); that UI_White (181) is the same type as the car icon (170) is assumed. A wrong type is garbage on screen,
not a fault (the read stays inside the static table). (c) Header line 17 says an element with `+0x25` set gets
neither Update nor Render; section 5 and re/hud.md 2.3 say the Tick runs regardless. The second is the reading
on record; correct line 17.

**S7. The probe's PASS line proves the instance, not the picture.** 'SAME SHAPE' compares four floats of the
appended instance with the clock's. It is the right discriminator for the old fault, but H1 passes only when the
screenshot shows the rows; keep both conditions in re/hud_hook.md's H1.

## Not refuted, still open (as the report says)

The own Draw with the right xform being visible; every picture part; the anchor; the tint; the flag dword's
index; about 60 mid-level objects per level being freed with the scene (24 were, many times, without a fault).
