# The crash in The Vault (kl2 0x466597, inside a draw)

Track W, 2026-10-11. Owner, playing The Vault (`Maps\DM03A` under slot F07, tree `<work>\build\q_vault\w_tabQ`, hook SHIP
ship_w8): *"game crashed whilst i was in the vault, btw"*. Kept: `<work>\research\crash_1011_vault\` (two hook dumps,
the game's own, the log's tail). Tool: `tools/kl_fa_vaultfx.py` (`check`, `apply`, `stock`). Build:
`<work>\build\q_vault\DM03A_fix`.

**The triage is dump + exe + file reading; the cause is proved by bytes (section 2). The fix is NOT RUN IN THE GAME.**
Second round (after the review `re/crash_vault_review.md`, ACCEPT WITH FIXES): the Withdrawal fix folder is built
(section 3), the tool has a gate for a tree and checks the plant chunks (section 4), who makes a pot take its slot
is read (section 2), the live PASS no longer hangs on the black rectangles (section 5).

## 0. In short

A Dead Men cloth blob is 8 bytes too short for Dog Days' layout of it, so the plant pots outside the bank
(`SO0501_M03_Plantpot_01`, 10 of them, one shared blob) write the end of their last particle's rest place over the
first 8 bytes of the NEXT .prm chunk. In The Vault that chunk is the sprite of the vault fire's particle template
`Vault_Fire`; without its header the game makes the wrong kind of render entry for it and DrawChunk runs off its end.
It is level data (a converter gap), not the hook, not the blast's authoring, not the loot.

## 1. Triage

`19:43:12.698 CRASH c0000005 at kl2+0x66597, reading c1c71a90`, main thread, 121 s after GO, 6.7 s after the first
vault loot was taken (the loot shows when the beat ends = the blast).

| return address | routine | what it was doing |
|---|---|---|
| 0x466597 | 0x466590 | the heap's block unlink: `cmp [p - 0x10], 0x12345678`. p = **c1c71aa0 = the float -24.89**, not a pointer |
| 0x882c85 | 0x882c30 | free(p) of the engine's allocator |
| 0x7f0657 / 0x6ad6a3 | 0x7f05f0 / 0x6ad680 | free wrappers |
| 0x926de8 | 0x926db0 | a render entry's per-frame block: `[entry+0x1dc]` = spare block, `[entry+0x1e0]` = its size; spare too small -> free it |
| 0x842e6a | 0x842d00 DrawChunk | chunk **63166 (0xf6be)**, kind 7 (64-byte elements), 1 element, layer 7 |
| 0x69d1f0 | 0x69d130 = ZParticleController slot 55 | draws every particle template's buckets (0x1060 bytes each; this one `71cc72e0`, template 52 of the list at controller `375f9140` +0x214, sprite handle `[template+0x78]`) |
| 0x679619 | 0x678da0 = ZRenderEntryCameraD3D slot 4 | the camera's frame |

DrawChunk's own frame (ebp 01a4aaa4): chunk 0xf6be, desc 71cc82ec `{1, 0, 71cc72ec, 1.5, 73.96, -24.89, ...}`, entry
`48f9fc50`. That entry's vtable is **0xb99ed4 = ZRenderEntryGeomD3D**. Every other entry in the dump whose chunk is a
sprite is a ZRenderEntrySpriteD3D (0xb99e9c; 30 chunks, scratch `w8.py`), and the copy of the chunk each entry keeps at
+0x1ac reads `00020000 <texture> 0 <kind> ..` for all of them - except chunk 63166: **`4114cf53 c106e685 0 7 0804c002`**.

Why that kills: the sprite factory (0x6bb690, the fifth of the ten at `[0xef4d88]`) takes a chunk only when
`word [chunk+2] == 2` and makes a 0x1ec-byte entry. Refused, a later factory makes a ZRenderEntryGeomD3D, which is at
most 0x1c8 bytes: the block DrawChunk allocated for the desc one frame earlier lies AT entry+0x1c8 (`[entry+0x1a4] =
48f9fe18`), so `[entry+0x1dc]` is the desc's own sixth dword, -24.89, and 0x926db0 frees it. The first frame of such an
entry survives only when the heap behind it happens to hold a zero there.

The other dump of the folder (`kl2_490_crash_2026_10_11T18_40_31C0.mdmp`, 2.5 minutes earlier, the process before):
DiscordHook.dll+0x1f7fd in the render thread inside Present - the known Discord overlay fault (the fifth), unrelated.

## 2. The cause, with its proof

Chunk 63166 in the build's .prm is a good sprite: `00000200 a1070000 00000000 07000000 02c00408`, named by
`...\M03_A_Vault_01a\Bank_Vault_Fire01\Template_M03_VaultFire\Vault_Fire` (ZParticleTemplate), used by the emitters
`Vault_Fire_Big00\Emitter01_Fire_Pure` and `Vault_Fire_Small00\Emitter01_Fire_Pure01` (16 m from the owner's last
logged place). In memory its first 8 bytes had become the floats 9.3006 and -8.4313.

The chunk before it, 63165, is the cloth blob of `M03_A_Outside_01A\SO0501_M03_Plantpot_01_*!LOD1NewHavok` (ZPlant, 10
entities, plaza outside the bank). **Particle 192, its last, has the rest place (70.603, 9.3006, -8.4313): blob +0x924
= `428d34e9 4114cf53 c106e685`. The two dwords over the sprite are its y and z, bit for bit.**

How they get there (kl2 0x87df60, the blob's layout for an object; Dead Men's twin 0x58ad70):

```
+0x08 h, +0x0c n particles, +0x10 a, +0x14 c, +0x18 b
+0x1c + 8h : n x 12 rest places | n x 4 weights | a x 16 constraints | c x 2 | b x 6
x += x & 3 : S slots of 0x2c bytes               S = the object's slot count (object +0x48 = ZCloth[0])
base = x + S * 0x2c                              Dead Men  (0x58aeac .. 0x58aeaf)
base = that ROUNDED UP TO 16                     Dog Days  (0x87e041 .. 0x87e04f)
slot k: [slot] = base + stored offset; 24 n bytes of scratch = two arrays of n places
```

Dead Men's build tool sized the chunk for its own base. Blob 63165: slot table ends at 0x22e4, n = 193 -> Dead Men's
scratch 0x22e4 .. 0x34fc (chunk 0x3500), Dog Days' 0x22f0 .. **0x3508**: 8 bytes into chunk 63166. When a cloth takes
a slot (0x72a920, from ZCloth slot 119 0x8ac1d0) both arrays are filled with the n places. For this blob h = 1
(`[obj+0x84] == 1`), so the routine takes its FIRST branch (0x72a941): slot 8 of the object at `[[obj+0x40]]` is called
twice, with (0, n, dest) and (0, n, dest + 12 n) - not the float loop at 0x72a9b0, which is the h != 1 form and copies
the blob's rest places. Same extent either way; the dump shows what arrived: the second array's last 8 bytes are
particle 192's rest y and z.

The rule against stock (`kl_fa_vaultfx.py stock`, all 21 Dog Days levels): 88 cloth blobs, 0 short, all 88 exactly as
long as the layout asks, 16 of them longer than Dead Men's layout would need (so the rounding is in Dog Days' data too).

Ruled out by the same bytes: the hook. No part of it reads a cloth blob; the 8 bytes are the blob's own, written by the
game's own routine, and `check` predicts them from the files alone. (klgun writes flag bits into mesh chunks, never
floats; kldown / klfedkit were idle - no down, no fed; klmove, klbalance, klcrew, kltalk touch no .prm chunk.) Ruled
out as well: the blast's authoring, the briefcases, the vault door, the F07 redirect (the tree's members are
CRC-equal to the folder's).

### What is NOT established

- **When a pot takes its slot - READ in the second round, still not settled.** The only way to slot 119 for a ZPlant
  is the DRAW of its render entry: ZRenderEntryDeformerD3D slot 2 (0x7bf760; the cloth is `[entry+0x1bc]`) calls the
  cloth's slot 120 (0x59c9a0), whose first act is slot 119 (0x8ac1d0); the one direct caller of 0x8ac1d0 is ZHair's
  own slot 119 (0x663910). Slot 119: nothing while the game is paused (`[0xdd2640]+0x50 <= 0`) or the cloth was already
  served this frame; then it TAKES a slot (a free one, else the one of the cloth with the largest measure) when
  `[obj+0x4c] < 0`, or the measure `[obj+0x44]` is unset (>= 1e38, float 0xb6ed98), or the measure is below
  `[obj+0x4c]`; with a measure at or over the limit it gives its slot back. The measure is the smallest value of the
  frame written by the entry's slot 1 (0x789f30: `[arg+0x14] x [arg] x 100`; what the two factors are was not read)
  and is reset to 1e38 by the entry's slot 9 (0x5ee9d0). `+0x48` / `+0x4c` are taken to be ZCloth[0] / ZCloth[1] =
  1 slot and 2000.0 on the pots (ASSUMED from the order of the properties). So: a pot writes in the first unpaused
  frame it is drawn with no measure or a measure under 2000. **What that does not explain:** every one of the owner's
  nine logged places is 62 m or more from the nearest pot of this blob (he went from the dock into the bank, away
  from the plaza; scratch `wfix_pots.py`), so if the measure is a plain distance in cm he was never inside it - the
  write then came through the 'unset' arm (a draw in a frame where slot 1 had not run for that entry: another
  camera, the pre-round view?) or the measure is not a plain distance. Not established which. Once it has happened
  the sprite is broken for the rest of the level.
- **Whether it crashes every time.** Not settled offline (the draw condition is known now, which frame meets it is
  not). Needed: (a) a pot has taken its slot, (b) the game makes a NEW render entry for
  the Vault_Fire sprite afterwards (the dump holds no sprite entry for it: most likely none was ever made), (c) the
  heap behind that entry is not zero at +0x1dc. The two fire emitters only come on with the blast, and with an idle
  player at the start nothing of them is drawn - which fits the three scripted loads V0 / V1 / V2 (bots looted the vault
  103 s after GO in V1, no fault). GUESS: every human who stands in the vault after the blast is at risk within
  seconds; the dump shows the entry had lived one frame.
- **The black rectangles of picture `0196_8940s.jpg`** (taken 19:43:12.03, 0.67 s before the fault). GUESS: they are
  the Vault_Fire particles drawn through geometry entries (a sprite chunk drawn as a mesh), i.e. the same fault a few
  frames before it turns fatal. Not shown.

## 3. Where else

`python tools/kl_fa_vaultfx.py check <folder>` on every build named in the task:

| build | cloth blobs | result |
|---|---|---|
| `p_tab\DM01`, `DM02`, `DM06`, `DM09` | 0, 2, 10, 2 | PASS |
| **`p_tab\DM03` (Withdrawal, on the owner's tab)** | 4 | **FAIL**: the same blob (60551, 13 pots) writes `9bcf1441 d2e606c1` over chunk 60552 |
| `c_bank\bank_vault`, `_bare`, `_noai`, `_wavslim`, `q_vault\DM03A` | 4 | FAIL: blob 63165 (62411 in `_noai`) over the Vault_Fire sprite |
| `q_vault\DM03A_fix` | 4 | PASS |
| **`q_vault\DM03_fix`** (second round, from `p_tab\DM03`) | 4 | PASS |
| tree `q_vault\w_tabQ` (`kl_fa_vaultfx.py tree`) | 6 maps | **FAIL (2)**: DM03 and DM03A |

On Withdrawal the chunk that is hit is no sprite: it is the 176-byte **post-filter set that all five records of the
scene's `PostFilterBoxes` name** (60555 -> 60552). Its first two floats (0.0, 1.0) become (9.30, -8.43). No crash is
known from it, but it is the level's whole post filter with two wrong numbers. GUESS, for track T (`re/carfx.md`: the
dark veil / 'black box' on Withdrawal, also seen in pictures where no car burns): this may be it or part of it. What
the two fields mean was not read.

**Built in the second round (review MUST 1): `<work>\build\q_vault\DM03_fix`** = `apply` on `p_tab\DM03` (the folder
the tree's `Maps\DM03` was written from: its 31 members are CRC-equal to the tree's; `z_cover3\M03` is an older
state, its .TEX and .prm differ). Blob 60551 13568 -> 13584 bytes, .prm 62581504 -> 62581520, only the .prm member
differs, archive sha1 `12abc4bdd081ce613278d33fdea6195d9a0b60c9`. Checks before (on a scratch copy of `p_tab\DM03`)
and after, same last lines: fedbody PASS (0 FAIL, 0 NOTE), kl_impact `problems: 0`, fedpoints PASS (0 FAIL, 7 NOTE),
kl_chars check exit 0, kl_map_guns exit 0, **kl_fa_bots_dyn `FAIL (7 FAIL, 1 NOTE)` before AND after** - the tab's
known civilian-money rule (CLAUDE.md, track A); every FAIL / NOTE line is equal but the one that prints the .prm
size. NOT LOADED. It must go into the tree together with `DM03A_fix`.

## 4. The fix

`kl_fa_vaultfx.py apply <build> <new folder>`: each short blob gets zero bytes up to what Dog Days addresses (a
multiple of 16). Nothing else moves - every reference in a .prm is a chunk index. It refuses a blob whose shape it
does not know, and proves before writing: same chunk count, every other chunk equal, the padded ones = old bytes +
zeros, only the .prm member of the archive differs.

`<work>\build\q_vault\DM03A_fix` from `q_vault\DM03A` (HUD look and fed line kept: every other member CRC-equal):
blob 63165 13568 -> 13584 bytes, .prm 72157904 -> 72157920, archive sha1 `bf869e52`. (Second round: `apply` with the
changed tool into a scratch folder gives the same archive, sha1 `bf869e52..`; the folder itself was not written again.) The folder's own check script
(`q_vault\_log\checks.sh`) gives the same eleven last lines as before: fedbody PASS, kl_impact `problems: 0`,
fedpoints PASS, bots_dyn PASS, kl_fa_bank check PASS / reverify 0, kl_chars 0, guns 0, talk FAIL 0, audit the same two
findings, both KNOWN by `kl_expansion.audit_known` (refuse: none).

One thing `apply` does besides the .prm, said here because it touches a check's reference: `kl_fa_bots_dyn check` fails
a folder whose .prm is not the size its `dyn.json` wrote down. The copy of `dyn.json` in the new folder gets the new
size in `big_before` / `big_after` and a `vaultfx` key that says so. Without that the check reads the 16 bytes as
`a large block changed its size`.

### For the source (kl-merge-9b / the graft; their files, not changed here)

The gap is not in `kl_fa_bank.py`: it is wherever Dead Men cloth chunks enter a Dog Days .prm, i.e. every graft of a
map with ZCloth / ZPlant (`kl_prmgraph` calls cloth 'an opaque blob'; it is - but its LENGTH is game-specific). One
call once the joined scene exists, before the .prm member is written (in `kl_graft.build`, after `G.append`, where
`Jn` is the joined `kl_prpjoin.Scene`), and one line in verify:

```python
import kl_fa_vaultfx
padded = kl_fa_vaultfx.fix_level(prm, Jn)          # {chunk: (old size, new size)}; raises on a blob of unknown shape
if padded:
    log('  cloth blobs padded for Dog Days\' layout (kl2 0x87e041): %s' % padded)
# verify():
bad += ['cloth blob %d: %d bytes short for Dog Days' % (f['chunk'], f['over']) for f in kl_fa_vaultfx.findings(kl_fa_vaultfx.Level(folder)) if f['over']]
```

Until then (review MUST 2) the check is a GATE, not a step to remember: `python tools/kl_fa_vaultfx.py tree <tree>`
runs every `Maps\<id>\*_Main.zip` of a KLExpansion tree and exits 1 on any failure (today: `w_tabQ` FAIL (2)). For
`kl_expansion.build` (not this track's file; NOT put in), beside the audit, once the maps are in the tree:

```python
import kl_fa_vaultfx
short = kl_fa_vaultfx.gate(root, log)               # ['<id>: cloth blob ... bytes short for Dog Days ...']
if short:
    raise SystemExit('the tree is refused (kl_fa_vaultfx): ' + '; '.join(short))
```

kl-merge-9b's running rebuild `c_bank2` will fail it as all four `c_bank` folders do: `apply` on its finished folder.

### The builder's added question (the blast as a 'show', `--no-blast`)

Yes, the faulting chunk is one of the show's (the sprite of `Bank_Vault_Fire01`'s template). No, `--no-blast` is not
the fix: the sprite is a good Dog Days sprite in the file and was broken by its neighbour; without the blast the
fire's emitters never start, so the symptom is hidden while the overrun stays (and with another chunk order hits
something else, as on Withdrawal). With the pad in, Dog Days draws the Dead Men vault fire properly for the first
time in front of a human: look at it in the scripted run BEFORE it goes on the tab; if it looks wrong (black boxes,
section 5) the owner gets the `--no-blast` form until the templates are looked at.

### The other simulation chunk: ZPlant[2] (review SHOULD 8)

Read in both exes: a count dword and 16-byte records {u16 a, b, c, ?; float +8; float +0xc}; kl2 slot 122 0x7ab5c0
and slot 82 0x7cfa20 against kaneandlynch 0x58e120 and 0x58df40 - same stride, same fields, the float at +0xc
rewritten in place, pointer / count at object +0x104 / +0x108 (Dead Men +0xf0 / +0xf4). Not read: the routine that
sets pointer and count from the chunk. In the data all 10 stock plant chunks and the 13 of the builds (bank 3, park
8, Late Night 2) are exactly 4 + 16 count rounded up to 16, indices below the blob's particle count. No fault;
`check` now fails a plant chunk that does not hold its records.

## 5. Live check (the lead's; nothing here ran)

Tree = w_tabQ with `Maps\DM03A` from `q_vault\DM03A_fix`, the owner's hook and keys, the scripted WALKING player
(`kl_playtest`), enemies off or `PlayerHealth=10` so he lives:

1. start -> ante-room (400, -959, -11800); the box there starts the beat (48 s) -> the vault (399, -960, -12818) once the
   door is off; stand in the vault facing the fire for 60 s, pictures every 2 s. The owner's fault came 121 s after GO
   and 6.7 s after the first vault loot; V1's bots had the loot 103 s after GO.
2. **PASS = no `CRASH` line and no fault for 60 s in the vault after the first `$` of vault loot in the `bots:`
   lines, facing both fire places (992, -938, -13191) and (454, -942, -13330), and the round goes on. Nothing else.**
   The black hard-edged rectangles are NOT part of PASS (review MUST 3): that they are this fault is a guess, and
   near-black boxes round fires are known on Withdrawal (`re/carfx.md`), where no sprite is hit. Report them
   separately from the pictures: gone = the guess fits; still there = track T's subject or the show's Dead Men
   templates, and then the `--no-blast` form for the owner until they are looked at.
3. Control, only if wanted: the same script on `q_vault\DM03A` - expected `CRASH ... kl2.exe+066597` (or the black
   rectangles) in the vault. One clean control run would NOT clear the old build (section 2, 'not established').
4. Withdrawal: tree with `Maps\DM03` from `q_vault\DM03_fix`; one ordinary round, PASS = it loads and plays as
   before; then the picture outdoors against the current build (the post filter's first two floats are no longer
   overwritten - a difference there is a finding for track T, not a failure).
5. Before the tree goes out: `python tools/kl_fa_vaultfx.py tree <tree>` must end `gate (vaultfx) ...: PASS`.

## 6. Assumed

- ZCloth[0] is the slot count at object +0x48 (equal to the number of slot records in all 88 stock blobs and the
  bank's 4; `check` fails a blob where it is not).
- Zero bytes are right for the added scratch (the file's own scratch is zeros; 0x72a920 fills it before use).
- The rule is offset arithmetic, the exe rounds the absolute address: equal only while the .prm buffer starts on a
  multiple of 16 (the owner's did: 0x04180010 from the hook's reserve).
- A blob with several slots whose step (24 n) is no multiple of 16 is padded long enough, but its later slots are not
  16-aligned as stock's are; `check` prints a NOTE for it. None exists in today's builds (the flag: 4 slots, 720 apart).
- That nothing else in the level holds a byte offset into the .prm (kl_prmgraph: all references are chunk indices;
  the eleven checks agree).

## 7. The SECOND crash (kl2 0x8a040e reading 0x2c, 2026-10-11 20:48:02) - the same fault, another victim

Track W2. The owner's round on the UNFIXED build (the installed `Maps\DM03A\F07_Main.zip` is sha1 `bd94d046` = the
tree w_tabQ's; `check` on it: `FAIL cloth blob 63165 ... writes 53cf1441 85e606c1 over the first 8 bytes of chunk
63166`). Kept: `<work>\research\crash_1011_vault2\`. **Dump + exe reading; no new fix is needed: `q_vault\DM03A_fix`
(section 4) is the fix. NOT RUN IN THE GAME.**

### Triage

Main thread. `0x8a0400` is a render entry's 'gather' (`mov eax,[esi]; mov edx,[eax+0x2c]; call edx` = the entry's
vtable slot 11, then slot 1): it was called for an entry whose **vtable dword is 0**. Caller `0x496eb0` walks a list
of render entries (ebx = 0xb8 = 184 of them, the saved index on the stack = 0x89 = 137; edi 0x119 = 281 results
gathered so far - counters, not slot ids) and sorts the result; its caller `0x679690` is in `0x678da0` =
ZRenderEntryCameraD3D slot 4, the camera's frame (the routine of the first crash's last frame).

The list (on the stack at 01a7159c, in the dump): 182 good entries (Geom, Light, Bones, BonesRigid, Sprite by RTTI)
and two dead ones, **#137 `7f32b8e0` and #159 `7f32c210`**, both in the heap run of ZRenderEntryGeomD3D blocks
(0x1c8 bytes each + a 0x10 header `12345678 next prev base`). What lies over them is 64-byte records with places
(448.1, .., -13322.0), (992.6, .., -13216.3), (447.2, ..), (958.1, ..) ... = **the particles at the vault's two fire
places** (992, -13191) and (454, -13330).

The block before the first dead one is the entry `7f32b700`: ZRenderEntryGeomD3D, chunk `[+0x19c]` = **0xf6be =
63166 = the Vault_Fire sprite**, its kept chunk head `[+0x1c0]` = **`4114cf53 c106e685`** = particle 192 of the plant
pots' cloth blob (section 2), `[+0x1a8]` = 7f32b8c8 = the entry's own end, and there: `{0x34, 0, 7f32b91c, 1.5, 97.6,
-24.89, ..}` = a DrawChunk desc of 52 elements with its data inline (`[0xef4d7c]` = 1 in the dump: `+0x1a8` and
`+0x1c0` are the slots of frame index 1).

A second Geom entry, `7f32e520` (#8 of the list), keeps the broken head too - but it is **NOT an entry of the same
chunk any more** (review SHOULD 1; read again in the dump): its `[+0x19c]` is `0xda95`, its `+0x1ac` holds
`00000000 c106e685 0 7 0804c002` (first dword since rewritten), its `+0x1c0` `4114cf53 c106e685 0 7 0804c002` - the
last three dwords of that lie at `+0x1c8 .. +0x1d0`, PAST the entry -, and `+0x1e4` / `+0x1e8` both hold `0xd54` =
3,412 = the 52-element draw in both frame indices. So it WAS the fire's entry, went back to the pool (0x5f6ad0 asks
the pool 0x815f40 before the factories) and was handed to ordinary geometry: the damaged entries are recycled.

`KLHook_2.dmp` and the game's own `kl2_490_crash_2026_10_11T19_48_5C0.mdmp` (review SHOULD 6, `debug/dump.py`): the
same fault - `0x8a040e` reading 0x2c, the same nine registers, callers `0x496f16 < 0x679690`, main thread.

### The cause

The first crash's, to the byte: the short cloth blob breaks the sprite's header, the sprite factory refuses it, a
0x1c8-byte ZRenderEntryGeomD3D is made, and DrawChunk's kind-7 branch (0x842e5b) asks 0x926db0 for `0x54 + 64 n`
bytes, which reads `[entry+0x1dc]` / `[entry+0x1e0]` (spare block, its size) - 0x14 and 0x18 bytes PAST the entry.
This time the heap had put another render entry right behind it:

```
entry+0x1dc = 7f32b8dc = the next block's header, field 'base' = 7f32b8c8     -> taken as the spare block
entry+0x1e0 = 7f32b8e0 = the next entry's VTABLE (INFERRED 0x00b99ed4 = 12,164,820: it is gone from the dump, the
              block stands in a run of Geom blocks; any render-entry vtable is ~12 million) -> taken as its size: large enough
0x926dc7..: [entry+0x1dc] = 0, [entry+0x1e0] = 0 (the neighbour's vtable), return 7f32b8c8
0x842e6a..: 0x54 bytes of desc + 52 x 64 bytes of particles copied to 7f32b8c8 .. 7f32c61c
```

= 3,412 bytes over the next heap blocks: the neighbour `7f32b8e0` and everything up to `7f32c210` and beyond. The
camera's next gather calls slot 11 of the neighbour: vtable 0, read of 0x2c. In the first crash the same two reads
found a float (-24.89) and freed it - and that float, `c1c71aa0`, is THIS dump's desc dword at `7f32b8dc` =
`entry+0x1dc`: the first crash is this one a single draw later (had the fire been drawn once more before the dead
neighbour was gathered, 0x926db0 would have freed it), so the first crash had destroyed a neighbour too.
**So the fault has four faces:**

1. a free of garbage (0x466597);
2. a destroyed neighbour (0x8a040e);
3. silent heap damage of `0x54 + 64 n` bytes that shows later as anything - wider than the neighbours, because the
   damaged entries are recycled into ordinary geometry (`7f32e520` above); n grows with the fire (1 in the first
   dump, 52 here);
4. (review SHOULD 4; 0x842d91 .. 0x842db4 read) before it ever reaches 0x926db0, DrawChunk copies five dwords of the
   chunk head to `entry + 0x1ac + 20 x frame index`. With index 1 that is `+0x1c0 .. +0x1d4`, 12 bytes past a
   0x1c8-byte Geom entry: head dword 4 (`0804c002`) lands on `+0x1d0` = the next heap block's `12345678` mark. Seen
   in the dump in `7f32e520`'s tail. Every odd frame of such a draw breaks the neighbour's heap header, whatever
   0x926db0 then does.

When: the beat ended and bot 2 had the first vault money at 20:47:47.06 (the fire's emitters start with the blast);
fault 15.9 s later with the owner (money $0 all round) in the hall at about (385, 206, -8100), 50 m from the vault
and not in it - the particle controller draws every template's buckets for the camera wherever he stands (first
crash, 0x69d130). So a human does not have to enter the vault.

**What that does NOT show (review SHOULD 2): that every round is at risk.** The score so far, all on builds that
fail `check`: a MOVING human 2 crashes of 2 rounds that reached the vault loot (6.7 s and 15.9 s after it); an IDLE
human in the yard 0 of 1 (scripted V1, `bank_vault_noai`: the bots had the blast and the loot 103 s after GO, live
camera, `state=PASS`, no CRASH line); V2 (full enemies, idle) never reached the vault. Either the pots' cloth had
not written in V1 or the damage stayed silent - the open condition of section 2 (when a pot's cloth takes its slot)
is what separates them, and it is still open.

### The suspects of the task

- (a) the knock-down part (kldown.c): OUT. The faulting object is a geometry render entry in the render heap,
  overwritten by particle records with the vault fire's coordinates through the game's own DrawChunk; nothing of
  kldown's (animation pair, prone words, prompt element, input mask, shoulder side) is a render entry or lies there.
  The last down had ended 13 s before ('UP after 2.08 s'); the log says `down D ... state 0` at the fault.
- (b) the cloth blob: **IN**, by three things in the dump: chunk id 63166 in the entry, the blob's own two floats
  as its header (the pair `kl_fa_vaultfx.py check` predicts from the files), the fire's particles over the victims.
- (c) the map's geometry / doors / the drop of 3.4 m, the escort's order, FollowOut / BoardNear, the talk, the fed:
  OUT - none is on the path; the 3.4 m are stairs (y 547 -> 206 between two escort lines), no fault there.

### Fix, state of the builds

Nothing new to build. `q_vault\DM03A_fix` (archive sha1 `bf869e52..`, unchanged) `check`: PASS; `q_vault\DM03A` and
the installed archive: FAIL (1); tree `q_vault\w_tabQ`: `gate ... 6 map(s), FAIL (2)` (DM03, DM03A). Of the set being
built: `r_tab\DM03v` PASS, **`r_tab\DM03` still FAIL** (the same blob over the post-filter chunk 60552) - the tree
must take DM03v / the padded folders, and `kl_fa_vaultfx.py tree <tree>` must end PASS before any install.
No patch for a hook file or `kl_fa_bank.py` comes out of this crash.

**WHICH TREE (review MUST 1; all re-run in the fix round, read only):**

| what | last line |
|---|---|
| tree `<work>\build\w_tabS\KLExpansion` (`now/mk_stab.py`: DM03 = `r_tab\DM03v`, DM03A = `q_vault\DM03A_fix`) | `gate (vaultfx) ...: 6 map(s), PASS` |
| tree `q_vault\w_tabQ\KLExpansion` (= what is installed) | `gate (vaultfx) ...: 6 map(s), FAIL (2)` |
| installed `Maps\DM03A\F07_Main.zip` (sha1 `bd94d046..`) | `check (vaultfx): FAIL (1)` |
| `q_vault\DM03A_fix`, `q_vault\DM03_fix`, `r_tab\DM03v` | `check (vaultfx): PASS` |
| `q_vault\DM03A`, `r_tab\DM03` | `check (vaultfx): FAIL (1)` |

- **Only `w_tabS` (or a later tree that passes the gate) may be installed.** A tree `w_tabR` as `now/mk_rtab.py`
  line 98 would build it (DM03A = the unfixed `q_vault/DM03A`, DM03 = `r_tab\DM03`) must NOT go out; no folder
  `w_tabR` exists in `<work>\build` at the time of writing.
- `w_tabS`'s `Maps\DM03A\F07_Main.zip` (sha1 `58c169e1..`; the member names carry F07) is member for member CRC-equal
  to `q_vault\DM03A_fix\F01_Main.zip` (sha1 `bf869e52..`): 31 of 31.
- **Until such a tree is installed the owner should not play The Vault** (2 of his 2 rounds that reached the vault
  loot crashed). Withdrawal on his tab has the same short blob over its post-filter chunk (no crash known).
- `DM03A_fix` has NEVER BEEN LOADED: one load run before it goes on his tab.

**What proves the fix (review SHOULD 3): the bytes, not the live run.** The padded blob's scratch ends at 0x3508 of
0x3510 (`check`: FITS), so the write over the sprite's head cannot happen; with a whole head the sprite factory makes
a sprite entry and DrawChunk's kind-7 fields lie inside it. The live run only shows that the padded level loads and
plays, and what the vault fire then looks like - `no CRASH for 120 s` was already met by V1 on an unfixed build.

### Live check (adds to section 5)

Reproducible in principle from the log: a round on the unfixed build in which the beat ends (a bot in the ante-room
starts it, 48 s) while a human camera is live AND moving through the bank (V1's idle human did not crash); which
face shows depends on the heap. On the gated tree, the owner's hook and keys, in this order:

1. a plain load of `DM03A_fix` (never loaded): the level reaches GO;
2. the scripted WALKING player (`kl_playtest.py script <tree> DM03A ...`, `PlayerHealth=10`), NOT an idle one, along
   the owner's route: yard start -> dock -> hall about (385, 206, -8100), standing there through the beat;
   PASS = no `CRASH` / `FATAL` line for 120 s after the first vault money in a `bots: L1` line and the round goes on;
3. the same, on into the vault facing both fires (section 5), pictures every 2 s: what the fire looks like.

A PASS says 'loads and plays'; it is not the proof (above). A control on the unfixed build may show either crash
address or nothing; one clean control run does not clear it.

### Assumed / not established

- That 0x8a0400's `[eax+0x2c]` is 'slot 11 of a render entry' is read from this call alone; what slot 11 answers was
  not read (not needed for the cause).
- Whether the neighbour's vtable was zeroed by 0x926dda or by the desc copy (desc dword 6) - both write 0 there.
- When the pots' cloth takes its slot (section 2) is still open; this round shows it happens in an ordinary round
  that starts in the yard and never goes to the plaza.
- The .prm buffer itself is not in the dumps; the broken header is read from the entries' kept copies.
- What the neighbour `7f32b8e0` was before it was overwritten (a Geom entry by its place only).
- Why V1 (idle human, blast and loot, unfixed build) did not crash.
- Whether the black rectangles of the first crash's picture are this fault (section 2).

### Not this track: the owner's request for waves

With the crash report the owner asked: 'i want the vault enemies to keep spawning in like its in waves'. NOTHING was
done on it here (review SHOULD 7). It is level authoring in `tools/kl_fa_bank.py` (kl-merge-9b's file, uncommitted
edits in the tree; today 61 enemies / 25 squads in five waves that all come once) and needs its own track from the
lead.
