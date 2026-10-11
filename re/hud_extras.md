# Why the hook found none of the eight extra HUD pictures (2026-10-11)

Static reading of kl2.exe + the written archives. Nothing run in the game.

## Cause (established, a tool bug, not a game rule)
`tools/kl_hud.py add_extras` edited `Prp.tokens`. `Prp.serialize()` (tools/kl_prp.py 137) rebuilds the stream from the
NODES' `props`, so every edit of the flat `tokens` copy was thrown away. The log line 'extras: 8 pictures ... 2 HUD
list(s) updated' therefore lied: the .TEX got textures 3000..3007 but slots 111..118 of both 200-entry lists stayed 0.
Proof on the old build `build/hud_x/DM03` (and F01): `hud_slots()` gives 183 entries, 111..118 absent; both lists in the
.prp read 0 there. The game never saw an id, so osd+0x3ec+12*k stayed 0 for k = 111..118 ('handle 0' in the hook).
The old `check` did not catch it (it compared flat tokens of the same copy, 0 differences were 'allowed').

## What the game does (kl2.exe 0x5e3810, ZOnScreenDisplay2 picture load; `this` = the OSD)
```
for n in 0..199:                         # 0xc8
    id = [osd + 0xd68 + 4*n]             # the 200 integers of the .prp property [7] = TEXTURE IDS (.TEX), not .prm chunks
    if id == 0: continue                 # unused slots (14, 20, 26, 111..118, 123..126, 185, 190 in stock) stay empty
    flags = 0; type = 5                  # default
    for e in table[0xcee058 .. 0xceeea4, stride 0x14, 183 rows]:   # {index, name*, flags, 1, type}
        if e.index == n: flags = e.flags; type = e.type; break      # stock rows: flags 0x60200 (or 0x60002), type 5/6/8
    handle = TexLoader->vtbl[+0x104](id, flags | 0x10, type, 1)  # TexLoader = [[0xdda798] + 0x18]
    [osd + 0x3ec + 12*n]     = handle    # = a chunk-table index, resolved with the table at 0xeac7b0 (DrawChunk 0x842d2e)
    info = [0xdda798]->vtbl[+0xac](id)   # texture info
    [osd + 0x3f0 + 12*n]     = u16 info[0] (width), [osd + 0x3f4 + 12*n] = u16 info[2] (height)
```
So the integers are texture ids; the sprite chunk is made by the loader at run time (stock levels' .prm sprite chunks are
only for the menu scene, which uses tools/kl_portraits.py's texture -> sprite -> picture chain). No .prm chunk, name hash or
extra data is needed for a HUD slot. Rows for 111..118 do not exist in the table at 0xcee058, so the extras load with the
defaults: flags 0x10, type 5 (stock 119/120/170/181 are table rows with flags 0x60200|0x10, type 5).

## Fix (done)
- `add_extras` now edits `node['props']` of every node (both ZOnScreenDisplay2 lists) before `serialize()`.
- `check(..., extras=True)` now reads the WRITTEN .prp with `hud_slots` and requires slot 111..118 == 3000..3007, the
  texture present, id < 4096, and the .TEX record header (id, width, height, size) to match.
- Builds (check PASS, `hud_slots`: 111..118 = 3000..3007, DM03 slots 170/181 = 1089/1100, F01 1167/1178):
  `<work>\build\hud_x2\DM03` (from `hud_new\_src\DM03`, zip 200,769,316 bytes) and
  `<work>\build\hud_x2\F01` (from the stock `KL_PortBackup\Scenes\Locations\F01`, zip 257,276,721 bytes).
  Command: `python tools/kl_hud.py all <src> <out> --look deadmen`.

## Still a guess
- That the loader accepts flags 0x10 / type 5 for a texture no table row names (the 14 unnamed stock slots suggest the
  default path is normal, but none of them is non-zero in a stock level). If the hook still reports a handle with type != 5
  for 111..118, try giving the extras the stock row values: that needs a .text patch (table rows are in .rdata/.data of the
  exe), not possible as data. Fall-back on the data side: reuse an already-table-registered spare index (119..126 rows exist
  for 119/120 only), i.e. nothing better is known.
- The texture header flags copied from `UI_KL2_Small_Icons_01` (`fl & ~0x100`) and uncompressed ABGR: same as the restyled
  plates, which load fine, so low risk.
- The loader class at [[0xdda798]+0x18] was not identified (vtable +0x104 not located), so what it does with a texture id
  absent from the .TEX is not read; the .TEX does hold all 8.
- Hook side: klu_pic_prep's lookup (handle at tbl+12*k, chunk via 0xeac7b0 unless bit 31, type at chunk+0xc == 5) matches
  0x5e3810 and DrawChunk; no hook patch needed. Run P1 with Log=2 prints slots 108..120 and shows whether 111..118 now resolve.
