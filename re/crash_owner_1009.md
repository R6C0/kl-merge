# The owner's two crashes on Retomoto Tower, 2026-10-09 17:37 and 17:41

Agent n-crash, OFFLINE (nothing launched, nothing installed, nothing written into the Dog Days
folder). Build played: `<work>\build\play_rt\R09+M09_A (R09 = F07+M09_B)` (F07 systems + M09_B +
M09_A), SHIP hook, direct boot. Material: `<work>\research\owner_crashes_1009\` (hook log, the
hook's two dumps of the LAST crash, the game's own dump of each crash) and the watcher's pictures
`<work>\research\watch\20261009_173716\`.

## 0. Summary

| | when | fault | cause | status |
|---|---|---|---|---|
| A | 17:37:05, 13 s after start, loading | write to 0 at kl2 0x8e5bbd | `HeapAlloc` of **60.7 MB** (the .prm in one block) returned NULL; the game does not test. The 2 GB process already had 1828.5 MB of address space in use | environment + size; intermittent. Not a data fault. Section 2 |
| B | 17:41:14, in the boardroom | read of 0x6a971eb4 at kl2 0x4c34b3 | a bullet hit a **guard's left forearm**. The guard's skeleton holds each bone id twice; `kl_chars.reid()` rewrote one copy only. The stale id found no bone, the engine took matrix 255 | **tool fault, fixed**: `tools/kl_impact.py`. Every Dead Men map built since the skeleton renumbering has it. Section 1 |

Crash B is NOT the glass case, the surface table, the .HVK surface rows or the .sgd: those tables
are in range in this build (section 1.5). It is the blood mark on a person.

## 1. Crash B: a hit on a Dead Men character

### 1.1 What the dump says (`python debug\dump.py KLHook_2.dmp`, stack read by hand)

```
4c34b3  fsub dword [edx]          edx = 6a971eb4 = ebx + 0x24, not mapped
88c8d7  in 0x88c840               ebx = matrices + 0x30 * 0xff      (eax = 0x2fd0 = 48 * 255)
479d13  in 0x479c80               the ring of ten marks per person
5c34bf  ZRenderDraw slot 21
636b9f  in 0x6367f0               the mark of an impact
512fa5  in 0x512ca0               ZProjectileBase slot 36 = the impact
```
(0x5c871c and 0x444734 between them in the hook's caller list are stale words on the stack, not
frames: 0x479c80 calls 0x88c840 directly.)

Objects on the stack, classes by RTTI: the thing hit `0x51a51ed0` = **ZFFActor**; `ZProjectile`
0x62eb50e0; `ZFFItemWeapon` 0x62ca9430; shooter `ZFFPlayer` 0x52044210; `ZBulletMarks`; room `ZROOM`.
The hit record (0x62edf670): point (4285, 21084, 770) = the tower, `+0x28 = 0x68`, `+0x3c` = the
actor. The actor's model root ([actor+4]+0x68) = .prm chunk **0xf65d** = the model of 42 of the
tower's guards, among them `AI_Players!Enemies!020_Office!Squad_Guards_Inside_02 / _03` - the
boardroom squads (`C_Henchmen_02_Tokyo_02`, `_03`). Skeleton chunk 63067, 102 bones.

`ebp = 0x55d25420` at the fault is a 256-byte table that starts `ff 00 01 02 03 04 05 07 ff 19 ...`
= byte for byte skeleton 63067's table [5] in the built .prm. Its byte 0x68 is `ff`.

### 1.2 What the code does

`0x6367f0(hit, ...)`, called for every impact after the surface row lookup (0x512ed7):
- two cells of the surface row (property ids at 0x1538d98 / 0x1538d9c, through 0x4e5040 and
  0x6d3b80) name the entity holding the mark's picture; a group -> a random child (0x636a11);
- thing hit = `0x5db490([hit+0x3c])`. If it is a person (0x7f7fb0) and marks on people are on:
  - `0x636b1b`: `bone = GetBoneIndex(byte [hit+0x28])` (0x5575a0), then the byte at
    `bone definitions + 64 * bone + 0x3f`; 2 or 3 -> the head-wound call 0x8683f0;
  - `0x636b9d`: ZRenderDraw slot 21 -> 0x479c80 -> **0x88c840**:

```
88c86b  matrices = 0x78c710(person)                  ; 48 bytes per bone
88c88d  table    = render vcall +0xc0 ([person+4]+0x68)   ; skeleton table [5], 256 bytes
88c89b  bone     = byte [table + [hit+0x28]]         ; BONE ID -> bone index
88c8c2  m        = matrices + 48 * bone              ; no test for 0xff
88c8d2  0x4c34a0(point, m + 0x24)                    ; point - bone position: the fault
```

So `hit+0x28` is a **bone id**, and 0xff ('this model has no such bone') is used as an index.

### 1.3 Where the id comes from: the skeleton holds its ids twice

Bone definition (skeleton slot 1, 64 bytes per bone): name at +0x1c .. +0x3d, **+0x3e = the bone's
id, +0x3f = its body part**. NEW - kl_chars' docstring has the name only. Built .prm, skeleton
63067, bone 22: `... 4c 45 46 54 5f 46 4f 52 45 54 57 49 53 54 31 ... 00 00 68 05` =
`LEFT_FORETWIST1`, id **0x68**, part 5.

| | LEFT_FORETWIST1 |
|---|---|
| stock M09_A: table [5] and definition +0x3e | 0x68 and 0x68 |
| stock F07 (the level numbering the graft adopts): id 0x68 | `xtra_up_pec` - a bone the guard does not have |
| built level, table [5] (after `kl_chars.reid`) | bone 22 is now id **0x4f**; `table[0x68] = 0xff` |
| built level, definition +0x3e (reid did not touch it) | still **0x68** |

Readers of +0x3e in kl2.exe (found by pattern, `shl r,6` + `[r+r+0x3e]`): 0x763f00 (from
ZAppendage slot 13, 0x462590), 0x56b0e0, ZPhysicsLinkage slot 14 (0x80bd20); each sends the id
straight back through table [5]. These are the 'who reads the per-level ids' that
re/characters_graft.md 3.2 left open. The instruction that copies +0x3e into `hit+0x28` was NOT
located; that it is this byte rests on the value (0x68 exists nowhere else for this model) and on
0x636b1b treating `hit+0x28` as an id of the same skeleton.

Stock proof: in all 41 stock levels of both games every bone's +0x3e leads back to that bone
through table [5] (`python tools\kl_impact.py stock` -> `problems: 0 in 41 levels`).

### 1.4 Reproduced offline; who is exposed

`python tools\kl_impact.py <build>` on the build the owner played:
```
skeleton 63067 (102 bones): 29 bones carry an id the id table gives to NO bone ...:
    RIGHT_FORETWIST 0x7b, RIGHT_FORETWIST1 0x7c, LEFT_FORETWIST 0x67, LEFT_FORETWIST1 0x68
skeleton 63067 (102 bones): 44 bones carry an id the id table gives to another bone:
    SPINE_2 0x39 -> fa_right_lower_lip, neck1 0x3a -> fa_lower_lip, ...
```
'NO bone' = matrix 255 = this crash when the address is unmapped, a mark at a garbage place
otherwise. 'Another bone' = the mark on the wrong bone (a chest hit drawn on the lip), no crash.
Only GROUND, pelvis, spine, neck, head, limbs and hands (the fixed ids 1..36) were safe.

| build | problems |
|---|---:|
| `play_rt` Retomoto (played) | 26 (20 skeletons: M09_B's 16, M09_A's 4) |
| `play_rt\chain\F07+M09_B` | 19 |
| `expansion\KLExpansion\Maps` DM01 / DM02 / DM03 (bank) / DM06 / DM09 | 24 / 23 / 31 / 26 / 26 |
| `chars\heroes`, `wardrobe_F01`, `wardrobe_bank`, `civ`, `bot` (kl_chars.put: Dead Men player models) | 8 / 8 / 47 / 1 / 1 |
| `v_maps\F08+M06_FA_A` (built before the renumbering) | 0 |
| 41 stock levels | 0 |

So: every Dead Men map and every transplanted player model. Shooting GLASS is not the trigger;
shooting a Dead Men person (or car: their door and seat bones are in the list) in a bone above
id 36 is. The earlier live rounds on the bank did not meet it by luck or predate the renumbering.

### 1.5 The tables the brief suspected

Checked on the played build by `kl_impact.surface_faults` (the same two tests kl_graft.verify
runs): no .HVK sub-part names a surface row past the table, no surface cell names an entity that
is not in the level. The surface lookup at 0x512ed7 and the mark-entity lookup in 0x6367f0 both
succeeded in the dump (the code got as far as drawing). .sgd / glass: not on this path.

### 1.6 The fix

`tools/kl_impact.py` (new, mine):
- `bone_faults(prm)` - the check; `check(level)` adds the two surface tests; `stock` runs the 41.
- `sync_bone_ids(prm, sks=None)` - definition +0x3e := the id table [5] gives the bone; the
  definitions become a new chunk at the end, no index moves. Direction: table [5] wins, i.e. the
  renumbering is COMPLETED, not undone (ASSUMPTION that this is the better of the two: it keeps
  'one numbering per level', which every stock level has; undoing reid would equally restore
  the stock invariant).
- `fix(src, dst)` - a repaired copy of a built level.

Call lines for files I do not own:
```python
# tools/kl_graft.py build(), after the reid / rebind loop over sks, before `if done: prm_bytes = G.write(prm)`
import kl_impact
done['bone id bytes'] += kl_impact.sync_bone_ids(prm, sks)
# tools/kl_graft.py verify(), with the other .prm tests
bad += kl_impact.bone_faults(G.read(out['.prm'], 'dd'))
# tools/kl_chars.py put(), after `renamed = reid(ex, sk, ids)`   (or inside reid() itself: best)
kl_impact.sync_bone_ids(ex, [sk])
```
Ready to install when the owner stops playing (NOT installed, not run live):
`<work>\build\n_crash\play_rt_boneids\` = the played build with 557 bone ids rewritten;
`kl_impact` -> `problems: 0`; only the .prm member differs (65,099 -> 65,119 chunks, +46 KB; the
20 changed old chunks are the 20 skeleton headers). `python tools\kl_graft.py install F01 --from
"<that folder>"`. The folder holds the archive and the `F01_Main*` files beside it; `KLJoin.ini`
and whatever else stands in the slot folder is not in it.

Not done: no live run. Whether ZPhysicsLinkage / ZAppendage objects of the Dead Men maps (car
doors?) behaved wrongly through the same stale ids was not looked at; the repair covers them.

## 2. Crash A: the .prm block could not be allocated

### 2.1 The request

Game's own dump `kl2_490_crash_2026_10_9T16_37_6C0.mdmp`:
```
8e5bbd  mov dword [eax], 0x12345678     eax = 0          0x8e5ba0(ptr, align, size) stamps a block header
7bb354  in 0x7bb2c0                     HeapAlloc([heap+0x10f8], 0, size + 0x2f & ~0xf) -> NULL, not tested
8204a7  in 0x820300                     ZEngineDataBase slot 8 (scene load): operator new(ebp + 0x60000)
```
`ebp = 0x0398a1f0` = the size of `F01_Main.prm` in the played archive to the byte (60,334,576);
`ebx = 0x039ea1f0` = that + 0x60000 = **60.7 MB in one block**. It is the loader's second
allocation: before it only the .MAT (0x10e1d0, on the stack) was read and handed to the renderer
(render vcall +0xa4).

### 2.2 The process at that moment (dump stream 22, process VM counters)

| | crash A (process 15 s old) | crash B (level played 4 min) |
|---|---:|---:|
| virtual size (address space in use) | **1828.5 MB** (peak 1849.7) | 1846.3 MB (peak 1912.3) |
| private bytes | 901.4 MB | 1122.7 MB |
| shared commit | 416.2 MB | 531.8 MB |
| threads | 104 | 94 |

kl2.exe is NOT large-address-aware (PE characteristics 0x103): 2048 MB. At the failed request at
most ~219 MB were free IN TOTAL, in pieces; 60.7 MB had to be one piece. The dump has no region
list (no MemoryInfoList stream), so the largest free block itself is not in it.

What fills the space (measured in the dump):
- modules 317 MB, of it NVIDIA's user-mode driver 190 MB: nvgpucomp32 65.6, nvd3dum (Direct3D 9)
  63.4, nvwgf2um (Direct3D 10) 55.1 - both drivers are loaded although the launch is `-dx10`;
  steamclient 21.7; kl2.exe 20.2.
- 104 threads on a 28-CPU machine: 34 started by kl2.exe, 31 by nvd3dum.dll, 5 by nvwgf2um, 22 by
  the system pool. kl2.exe's PE stack reserve is 4 MB and 40 of the stack bases sit 0x400000 -
  0x450000 apart, i.e. **at least 160 MB reserved for stacks**.
- 80 % of the level's final private memory (901 of 1123 MB) is already there when the .prm block
  is asked for, 4.6 s after the archive was opened. ASSUMPTION (not traced in code): that is the
  textures, pulled in by the renderer when it gets the .MAT - so the .TEX is in BEFORE the .prm.
- injected into the process: `medal-hook32.dll` (Medal clip recorder, 2 threads), `nvspcap.dll`
  (NVIDIA overlay / instant replay), `gameoverlayrenderer.dll` (Steam overlay), `CSERHelper.dll`,
  our `dinput8.dll` (0.27 MB). **No DiscordHook.dll** in this process.

Why only sometimes: where the driver's DLLs, 100 stacks and the heaps land differs from start to
start, and the process runs ~200 MB under its ceiling the whole time (crash B's dump: 1846 MB with
the level loaded and no fault). The same archive loaded at 17:32 and at 17:37:21.

### 2.3 Is the build too big?

| level | .TEX | .prm (one block) |
|---|---:|---:|
| Retomoto (played) | 405.6 MB | 60.3 MB |
| stock F07 / F01 | 281.0 / 288.4 | 63.6 / 66.6 |
| stock maximum | 567.3 (L01) | 69.2 (L08) |
| expansion DM01 / DM02 / DM03 / DM06 | 413 / 386 / 387 / 374 | **81.2 / 80.8 / 86.6 / 75.7** |

Retomoto asks for a smaller block than stock F01 and carries fewer textures than six stock story
levels, so the game itself can hit this on this machine (re/crash_scorepage.md 6: stock L01,
28.9 MB block). But against the Fragile Alliance levels it replaces it brings +120 MB of textures,
and the four other expansion maps ask for a block larger than any stock level ever does.

### 2.4 What to do

Owner, today: start it again - it is the start, not the map. To make it rarer: close Medal and
turn off NVIDIA's overlay / instant replay before playing (each puts a DLL and threads into the
game). Discord's overlay was not in this process.

Tools (for m-load, in order of effect):
1. **.TEX**: the member that decides how much space is left when the block is asked for. Bring it
   to the stock Fragile Alliance size (~290 MB): every MB off is a MB of free address space.
2. **.prm**: the single block. Keep `PRM_LIMIT` for every map: DM01 / DM02 / DM03 / DM06 at 76 -
   87 MB need a larger hole than Retomoto did when it failed; under ~60 MB like Retomoto.
3. Splitting the .prm is not possible (one block, pointer kept at database +0x1164); load order is
   the exe's.

Hook (klhook.c, not my file; within the ship policy 'import slots and data'; NOT written, NOT tested):
- kl2's `HeapAlloc` import slot is 0xb1011c. At DLL load, before the driver and the threads come,
  `VirtualAlloc(NULL, 96 MB, MEM_RESERVE, PAGE_NOACCESS)`. In a wrapper on the slot: if the real
  call returns NULL and the size is over 16 MB, `VirtualFree` the reserve and call again (once per
  load; reserve again when the block is freed, or leave it). That guarantees the hole the .prm
  needs at the price of 96 MB kept out of general use until then.
- at least: on a NULL for a large size, log 'out of address space: N MB asked, largest free block
  M MB' (a VirtualQuery walk) and end cleanly instead of faulting at 0x8e5bbd.
- write the hook's dumps with `MiniDumpWithFullMemoryInfo`: then the region list is in the dump and
  the largest free block can be read afterwards (it could not be here).
- Setting the large-address flag on kl2.exe would double the space, but it changes the exe (Steam's
  wrapper checks it: re/antitamper.md) - not proposed.

## 3. Not established
- The instruction that fills `hit+0x28`; the meaning of bone definition +0x3f beyond 'head = 2 / 3'.
- Largest free block at crash A; that the 901 MB before the .prm request are the textures.
- Why NVIDIA's Direct3D 9 driver with 31 threads is in a `-dx10` process.
- Nothing here was run in the game.
