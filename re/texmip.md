# kl_texmip - per-map top-mip drop (2026-10-25, offline, NOT run in kl2)

Why: kl2 makes every .TEX texture D3DPOOL_MANAGED (sysmem copy + driver copy), DM05A +303 MB at load.
kl2's TextureDetail skip ([0xcdadec]) is global; `tools/kl_texmip.py` does it per level zip at build time.

    python tools/kl_texmip.py IN.zip OUT.zip [--min 1024] [--levels 1] [--exclude REGEX|none] [--dry]
    python tools/kl_texmip.py --selftest zip...

Mechanics: record = size, fourcc x2, id, h, w, mips, flags, ... name, mips x (u32 n, data), top mip first.
A drop cuts the first blob, halves h/w, mips-=1, fixes size; ids and tables untouched (kl_texmat write_tex relays out).
Touched only if: plain (no cube 0x400 / animated 0x100 / frame member), DXT1/3/5/RGBA/I8/U8V8/A8 with every mip
size matching w*h exactly, max side >= --min, mips > levels, short side >= 128 (GUESS: UI strips), name not
matching default exclude `UserInterface|UI_|Font|HUD|Loader` (GUESS: pixel-addressed UI). Others reported as skip.

Verified (offline): --levels 0 rewrite byte-identical on DM05A (lc7 F01_Main.zip), stock DD F01, F02, F03 .TEX;
a real drop output re-parses, every record walks, and re-round-trips identically.
Dry run DM05A (lc7, --min 1024): 86 of 1830 textures dropped, 63.8 MB per copy = ~127.5 MB of the managed
pool (sysmem + driver), .TEX 210.6 -> 143.8 MB. --min 512: 362 textures, 99 MB/copy (~198 MB). --min 2048: 3 textures, 8 MB/copy.
Stock F02 (--min 1024, before the UI filter): 185 textures, 162.8 MB/copy.
Top savers in DM05A are 2048 rank/suit and 1024 character/vehicle sheets (Rank_8-3, SuitSet, Hero_HEAD, Taxi/Police _ML),
shared with characters: dropping them blurs player models. Use --exclude 'Characters/' to keep those.

NOT proven: that kl2 accepts the shrunken header (w/h/mips) and that no material/sprite addresses the texture in pixels.
Needs one live run before any install. Saves ~128 MB of the 303 MB, so it is a partial lever, not the whole fix.
