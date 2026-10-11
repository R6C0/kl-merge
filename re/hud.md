# Dog Days in-round HUD (kl2.exe) - how it is drawn, with evidence

Written 2026-10-11 by the `hud_re` agent. Purpose: a new Fragile Alliance / Arcade HUD (a merge of
Dead Men's and Dog Days') drawn by KLHook through the game's own primitives, and the stock elements
moved / hidden / recoloured.

Method: static only. Nothing here was run in the game. Sources: `kl2.exe` disassembly (capstone through
`debug/kl.py`), RTTI vtables (`tools/kl_exe.py`), the property records behind `re/kl2.json` (0xd0ba88).
Scratch: `<scratchpad>\agents\hud_re\` - `h.py` (helpers: `vt`, `slots`, `dis`, `sweep`, `calls_to`, `xrefs`),
`f_<addr>.txt` / `e_<class>_<slot>.txt` (saved disassemblies of every element's methods).

Words used: **established** = read in the code; **ASSUMPTION** = fits the evidence but the deciding code was
not read; **not established** = unknown.

---------------------------------------------------------------------------------------------------

## 0. Summary for the lead

1. The HUD is NOT one draw routine with constants. `ZOnScreenDisplay2` owns 36 **element objects**
   (classes `Z*Display`, all derived from `IDisplayInterface`), made in its constructor (0x42e8a0) and
   registered in `Init` (0x823d30). Each element draws itself. The FA set (`ZFA*Display`,
   `ZHeist*Display`) exists only when the session mode is 4 (FA / Arcade).
2. TEXT is not a string primitive. Every text is a **`ZCHAROBJ` object** (a text mesh) created at element
   init from the OSD's template (field [0]) with a font (`ZTTFONT`) and an ARGB colour, given a C string by
   `SetText` (vtable +0x244) and drawn once a frame by its own `Draw(ctx, cam, &pos, &xform)` (+0x1e8)
   into the frame's `ZDrawBufferSimple`. KLHook can make its own `ZCHAROBJ`s the same way.
3. PICTURES are one primitive: `ZDrawBufferSimple` vtable slot 5 (0x842d00), `DrawChunk(chunk, &desc,
   &pos, &xform, layer, 1, 0)`; the chunk is the sprite handle from the OSD's picture table
   (`osd+0x3ec + 12*n` = {handle, width, height} for picture index n of the 200-entry .TEX list).
4. The per-frame entry is **`ZOnScreenDisplay2` render routine 0x8bf300(osd, ctx, cam)** (thiscall; called
   from OSD vtable slot 55 = 0x558370, the ZGEOM render virtual). It updates every element (slot 6), then
   draws every element whose `+0x24 != 0 && +0x25 == 0` by calling slot 2 `(ctx, cam)`. **Hook 0x8bf300**:
   call the original, then draw your own with the same `ctx` / `cam`.
5. HIDING a stock element = write byte **`element+0x25 = 1`** (the game's own hide flag, used by 0x75f780
   / 0x5e6060 for cut-scenes). No bitmask exists; one byte per element, element pointers at fixed OSD
   offsets (table in 2.2). MOVING = the per-frame position is recomputed by each element's slot 6 from
   the 1280x720 virtual screen and the 5 % inset (`[0xceeebc]`); patch the element's position fields after
   the original slot 6 or in the hook after the update loop and before the draw loop (needs a split: see 4.3).
6. COORDINATES: a **1280 x 720 virtual screen, origin top-left, stretched to the window** (both axes are
   scaled independently, 4.1). The inset is `[0xceeebc] = 0.05` of width / height. The "HUD scale"
   `[0xcee050] = 1.0` multiplies picture sizes.
7. DATA: money ("Total score" = `$%i` of `0x807520(FA player)`), round (`byte [[player+0x5f8]+0x45]`),
   round time (session vtable +0x124 / +0x130, formatted `%02d:%02d` by 0x7818c0), ammo (weapon display from
   the player's item at `[player+0x920]`), all in 5. Labels come from the .LOC: section
   `AllLevels/Menu/Heist/Status`, keys `HeistTotalPoints` ("Total score") and `Round`; lookup in 5.1.

---------------------------------------------------------------------------------------------------

## 1. ZOnScreenDisplay2 (vtable 0xbbe504, instance 0x1230 bytes)

> CORRECTION 2026-10-11 06:40 (kl-merge-3e, after run H1_stock): `[0x154da50]` is NOT the OSD instance. Slot 12
> (0x70b140) and slot 13 (0x43e330) read the pair `[0x154da50]` / `[0x154da54]`, whose only writer is the two-argument
> setter 0x47d800, registered by the class's RTP registration at 0xaedb48 (size 0x1230, base `ZSTDOBJ`, type id
> 0x200483): a STATIC property pair of the class. Live it held 0x54 during a load and nothing drew. The hook now finds
> the instances by their vtable 0xbbe504 in the committed private memory (klhud.c `klu_find_osd`, the players' scan of
> klauto.c) and takes the one whose +0x10c4 is a ZFAPlayerListDisplay and whose +0x1130+0x1c reads 1280 x 720.

Stored fields (property records at 0xd0ba74..0xd0b9c0, each {next, name=0, filter=1, handler, member
offset}; established):

| field | offset | type handler | meaning (from use) |
|---|---|---|---|
| [0] | +0xd48 | 0xcfbf70 ref | passed to each element's Init as the **ZCHAROBJ template** (0x4d57f0 pushes [osd+0xd4c]... see note) |
| [1]..[4] | +0xd4c, +0xd50, +0xd54, +0xd58 | ref | ZTTFONT refs; elements register with one of them (2.2) |
| [5] | +0xd5c | 0xcfc010 int | passed to Init as arg 4 (not established what for) |
| [6] | +0xd60 | ref | OSD camera (stored again at +0x150 of the child list; 0x823d3c) |
| [7] | +0xd64..+0x1080 | 0xcfc058 fixed array 200 | .TEX ids of the HUD pictures |
| [8] | +0x1084 | ref | subtitles camera |
| [9] | +0x1088 | ref | coop border camera |

Note on [0]/[1]: 0x4d57f0 (Init of the saving element) pushes `[osd+0xd4c]` as the element's first Init
argument and the element resolves it with 0x8ccde0 and clones it as a text object, so **+0xd4c is the
ZCHAROBJ template and +0xd48 is something else** (0x4d6880 reads +0xd48 as a REF id and looks it up through
`[this+0xc]+0x40`: ASSUMPTION the name list or the camera). Treat the brief's "[0] ZCHAROBJ, [1..4] fonts"
as off by one: the fonts are +0xd50, +0xd54, +0xd58 (+0xd4c may be the fourth font, not established).

Other members (established): `+0x3c[50]` element pointers, `+0x104[50]` the font ref each element was
registered with, `+0x1cc[50]` a second ref (0 for most), `+0x294` element count (max 0x32 = 50; 0x75fc80),
`+0x298` list by key (0x6dbcd0: `[list + key*4] = element`, key = the small constant in 2.2),
`+0x3ec + 12*n` picture table {sprite chunk handle, u16 width, u16 height} filled by 0x5e3810 from the
.TEX ids (`[0xdda798]->+0x18` vtable +0x104 = load texture `id` with flags | 0x10 -> handle; +0xac =
texture info -> w,h), `+0x1130..` the screen transform (4.1), `+0x1210/+0x121c/+0x1220` camera ids
(0x1220 = "MenuCam", 0x4d58f3), `+0x1224..0x1226` flags (0x1225 = "HUD off" from 0x675470:
`[0xcedfb8]` is 1 or 2 and the OSD camera id is 1), `+0x112c` last frame time.

Overridden vtable slots (vs ZSTDOBJ): 0 dtor 0x8b2c60; 4 0x5b4620 (post-load: sets +0xd60 = -1 ... );
11 GetProperties; 12 0x70b140 `return [0x154da50]`; 13 0x43e330 returns [0x154da50], [0x154da54] (the two OSD
instances; both written only by 0x47d710); 14 0x7bae00; 18 0x7d98b0 (calls element slot 8 on all);
**55 0x558370 = Render(ctx, cam)**: by camera id -> 0x64f930 (MenuCam), 0x4deda0, 0x4942f0, else
**0x8bf300(osd, ctx, cam)** = the HUD; 83 0x4d57f0 Init part 2 (the saving element + MenuCam);
**87 0x804d80 = per-tick Update**: computes +0x1225/+0x1226, then for every element with `+0x24 != 0`
(or debug bytes 0x154da65 && 0x154da67) calls element slot 5 (+0x14), then the three global displays
[0x154da58/5c/60].

Singleton: `[0x154da50]` = the active ZOnScreenDisplay2 (established: slot 12 returns it; written by
0x47d710 which is the engine's message handler, so it is set when the level's OSD entity attaches).

## 2. Elements

### 2.1 IDisplayInterface (vtable 0xbbdb74, 11 slots; ctor 0x5e8540)

Layout (established from 0x5e8540, 0x83ab00, 0x4c5c80, 0x662260): `+0 vtable, +4 player index (slot 1 arg),
+8 = &osd->picture table (osd+0x3ec) (ASSUMPTION: read as 12-byte entries n -> picture index n, matches the
index list of the brief), +0xc = &osd->transform (osd+0x1130; 5th Init arg), +0x10 player object
(`gamedata[0x828 + 4*index]`, gamedata = [0xdd265c]), +0x14/+0x18/+0x1c position (x, y, z) in virtual
pixels, +0x20 state, +0x24 enabled (ctor 1; slot 7 sets it to state != 2), +0x25 hidden (ctor 0)`.

| slot | +off | meaning | evidence |
|---|---|---|---|
| 0 | +0 | dtor | |
| 1 | +4 | SetPlayer(index): +4, +0x10 | 0x83ab00 |
| 2 | +8 | **Render(ctx, cam)** - draws text / pictures | 0x8bf300:0x8bf5f6 |
| 3 | +0xc | (ctx?, ?) default `ret 8` | 0x716640 |
| 4 | +0x10 | **Init(charobjTemplateRef, fontRef, ref2, int, &transform)** `ret 0x14` | 0x452390, 0x7d0310 |
| 5 | +0x14 | **Tick()** - reads game state, sets texts | 0x804d80:0x804de5 |
| 6 | +0x18 | **Update(ctx, cam)** - computes positions (inset) | 0x8bf300:0x8bf45d |
| 7 | +0x1c | SetState(n): +0x20, +0x24 = n != 2 | 0x662260 |
| 8 | +0x20 | (called by OSD slot 18) | 0x7d98b0 |

### 2.2 The element table (OSD field -> class -> registered font -> key)

From the ctor 0x42e8a0 (allocation + class) and 0x823d30 / 0x4d57f0 (registration: font = the osd field
pushed into +0x104, key = the small constant stored with it). "FA" = allocated only when
`[[0x168e598]+0x5c] == 4` (0x8243bb..). Established.

| osd+ | class | size | vtable | font | key | note |
|---|---|---|---|---|---|---|
| 0x1090 | ZActionMarkerDisplay | 0xd0 | 0xbbdba4 | 0 | 1 | |
| 0x1094 | ZCheckpointDisplay | 0xcc | 0xbbdbe4 | d50 | 1 | |
| 0x1098 | ZCrossHairDisplay | 0x8b0 | 0xbbdc14 | 0 | 2 | crosshair |
| 0x109c | ZDirectionDisplay | 0x12c | 0xbbdc68 | 0 | 3 | |
| 0x10d0 | ZHitDirectionDisplay | 0x4c0 | 0xbbe024 | 0 | 0x10 | hit direction |
| 0x10d4 | ZHitSplatterDisplay | 0x6354 | 0xbbe068 | 0 | 0x11 | blood |
| 0x10d8 | ZOnscreenMessageDisplay | 0x140 | 0xbbe0b0 | d54 | 0x12 | |
| 0x10dc | ZObjectiveDisplay | 0xcc | 0xbbe11c | d54 | 0x13 | objective text |
| 0x10e0 | ZPlayerInfoDisplay | 0x9f4 | 0xbbe738 | d54 | 0x14 | 16 texts; tutorial / communication (strings `AllLevels/Interface/Tutorial*`), NOT the FA score |
| 0x1108 | ZTextDisplay | 0x1260 | 0xbbe800 | d58 | 0x15 | |
| 0x10e4 | ZPointOfInterestDisplay | 0x94 | 0xbbe77c | d54 | 0x16 | |
| 0x10e8 | ZProjectileEffects | 0x28 | 0xbc1920 | 0 | 0x17 | |
| 0x10ec | ZSniperLaserDisplay | 0x404 | 0xbbe7b8 | 0 | 0x18 | |
| 0x10f8 | ZGameplayTrackerDisplay | 0x65c | 0xbbe950 | d58 | 0x1c | **vehicle marker: icon + `%.0f m`** (0x8e23a4, 0x8e2a40) |
| 0x10fc | ZMiniGameButtonMashingDisplay | 0x12c | 0xbbe8f0 | d54 | 0x1d | |
| 0x1104 | ZTextDisplay | 0x1260 | 0xbbe800 | d58 | 0x21 | |
| 0x110c | ZUseActionDisplay | 0x160 | 0xbbe844 | d54 | 0x22 | |
| 0x1110 | ZWeaponDisplay | 0x151c | 0xbbe8c0 | d50 | 0x23 | **ammo + weapon pictures** (bottom right) |
| 0x1114 | ZHumanShieldDisplay | 0xf0 | 0xbbe920 | d54 | 0x1f | |
| 0x1118 | ZCoverDisplay | 0x70c | 0xbbe9a0 | d54 | 0x20 | |
| 0x10c8 | ZPlayerNameDisplay | 0x74 | 0xbbdfa4 | d54 | 0xe | |
| 0x1120 | ZHitEnemyDisplay | 0x44 | 0xbbea00 | d54 | 0x27 | hit marker |
| 0x1124 | ZSavingGameDisplay | 0x40 | 0xbbea38 | d54 | 0x28 | registered by 0x4d57f0 |
| 0x10a8 | ZFAAnnouncementDisplay | 0x3c | 0xbbdd34 | d50 | 4 | FA |
| 0x10a0 | ZFADeathCamDisplay | 0xd4 | 0xbbdcc8 | d50 | 5 | FA |
| 0x10a4 | ZFAFollowCamDisplay | 0xbc | 0xbbdd04 | d50 | 6 | FA |
| 0x10ac | ZFAIntroDisplay | 0xf8 | 0xbbdd98 | d50 (+0x1cc = d54) | 8 | FA: **"Heist starts in {timer} sec"** (`AllLevels/Interface/Online/FA_GameStartCounter`, set by 0x6d7de0 through 0x79dac0) |
| 0x10b0 | ZFAOutroDisplay | 0xdc | 0xbbddc8 | d50 (+d54) | 9 | FA |
| 0x10bc | ZFAHeadlineDisplay | 0x34 | 0xbbdea8 | d50 | 0xa | FA: **"Round N"** headline (0x6d7de0: `AllLevels/Interface/Online/GameEnd/Round`, SetText 0x401b70) |
| 0x10c0 | ZFAKillerCameraDisplay | 0xac | 0xbbded8 | - | - | FA (not registered: slots 2/5/6 are stubs) |
| 0x10c4 | ZFAPlayerListDisplay | 0xf98 | 0xbbdf6c | d54 | 0xd | FA: **crew list AND the top-left name / "Total score" / "Round" block** (refresh 0x6f3000) |
| 0x10cc | ZFATimeDisplay | 0xc8 | 0xbbdfec | d54 | 0xf | FA: **round timer top-right** (+ vehicle icon 170/171) |
| 0x111c | ZFAEscapeDisplay | 0x16c | 0xbbe9d0 | d54 | 0x26 | FA: vehicle health bar + time (`FA_HoldEscapeVehicle`, `%02d:%02d`) |
| 0x10b8 | ZHeistPointsPopupDisplay | 0xb0 | 0xbbde64 | d50 | 0x25 | FA: points pop-up |
| 0x10b4 | ZHeistOutroDisplay | 0xdc | 0xbbde28 | d50 (+d54) | 0x24 | Arcade only (0x7f6850 true) |

Three more displays live in globals `[0x154da58]`, `[0x154da5c]`, `[0x154da60]` (updated by slot 87 when
`+0x1210 != 0`; not established which).

### 2.3 Hiding and the visibility rules (established, 0x8bf300:0x8bf583..)

An element is drawn when `(elem+0x24 != 0 && elem+0x25 == 0) || ([0x154da65] && [0x154da67])`
(the two bytes are debug flags; no writer found in the exe). When `osd+0x1225` ("HUD off" - the
loading / cut-scene state from `[0xcedfb8]`) is set only ZMiniGameButtonMashing (in some states),
ZSavingGame, ZFAAnnouncement and (if `[0xcedfb8] != -1`) ZOnscreenMessage are drawn.
Stock hide groups: 0x75f780(osd, byte) sets +0x25 on the FA set (weapon, player info, time, announcement,
player list, cover, use action, escape, tracker, message; and the two cams when byte != 0);
0x5e6060(osd, byte) on the gameplay set (use action, crosshair, direction, splatter, hit direction, weapon,
player info, human shield, cover). The Tick (slot 5) runs regardless of +0x25, so a hidden element keeps
its data current - handy for reading it.

## 3. The primitives

### 3.1 Text = ZCHAROBJ objects (vtable 0xbab45c, 150 slots)

Creation (0x452390, the time element's Init, established): `tmpl = 0x8ccde0(templateRef)` (REF id ->
object), `font = 0x8ccde0(fontRef)`, then
`parent = 0x598460([tmpl+4])`; `obj = tmpl->vt[0x19c](parent, 'ZCOB' (0x5a434f42), 0, 0, 0, 0)`
(0x817810 forwards to +0x194 = ZGEOM's create-child; the tag is the class type id of ZCHAROBJ as four
chars). Then on `obj`:

| vtable | routine | call | effect |
|---|---|---|---|
| +0x220 | 0x41a470 | SetStyle(byte) | byte +0x84; 0x12 timer, 0x44 player info, 0xf/0x11.. elsewhere - alignment / flags (ASSUMPTION), triggers +0x1f0 re-layout |
| +0x20c | 0x8a0a30 | SetColour(u32 ARGB) | RGB -> +0x14 (alpha byte +0x86 kept) |
| +0x23c | 0x641ba0 | SetFont(fontObject) | +0xac |
| +0x234 | 0x514720 | SetLayer(byte) | +0x87, passed to Draw; 0xb..0xf used |
| +0x244 | 0x896e50 | SetText(const char*) | rebuilds the text mesh |
| +0x21c | 0x45d6e0 | SetOffset(&{x,y}) | +0x1c, +0x20 (floats), re-layout +0x1f0 (0x891150) |
| +0x1e8 | 0x5a6d40 | **Draw(ctx, cam, &pos3, &xform)** | -> +0x1ec (0x8f7420) with layer +0x87: emits the mesh into ctx |
| +0x1f0 | 0x891150 | re-layout | |

Colours are ARGB u32 constants in .rdata: `[0xbbe490] = 0xffffffff` white, `[0xbbe494] = 0xffcccccc`,
`[0xbbe498]`, `[0xbbe49c]`, `[0xbbe4a0]` (state colours of the timer: switch on session state 0..8 at
0x62a1e7), `[0xbbe4a4] = 0x80000000` (the drop shadow: a second ZCHAROBJ at (+2, +2), 0xbbe4ec/0xbbe4f0 =
2.0). Fade: `obj+0x3c &= alpha<<24 | 0xffffff` (0x62a2b4).

Per-frame draw (0x81e090, ZFATimeDisplay::Render, established): `pos = (elem+0x14, +0x18, +0x1c)`;
`xform = 0x7f07a0(local)` (zeroes with [+0x18] = 1.0); `obj->Draw(ctx, cam, &pos, &xform)`; shadow object
at `pos + (2, 2)`; second line at `y + 28.0` (0xb62770). So a text is placed in **virtual pixels** by the
pos vector handed to Draw (the ZCHAROBJ's own +0x1c/+0x20 is an extra offset).

### 3.2 Pictures = ZDrawBufferSimple::DrawChunk (vtable 0xb55484 slot 5 = 0x842d00, `ret 0x1c`)

`DrawChunk(this = ctx, chunk, &desc, &pos2, &xform, layer u8, 1, 0)` - established at 0x81e258 (timer's
vehicle icon) and 0x5ec7bb (weapon pictures): `chunk` = a .prm chunk index (`[0xeac7b0 + 4*chunk]` is the
chunk table; a negative value is a direct pointer with bit 31 cleared), here the sprite handle
`[osd+0x3ec + 12*n]`; `desc` = a 0x34-byte block the element keeps (`[+0] = 1`, `[+8] = &vec3`, `[+0x30] =
ARGB colour`; `[+0]` selects one of 8 vertex layouts at 0x842dbc - 1 is the sprite case); `pos2` = the
virtual position already multiplied by the transform (`0x5a3e90(&T, out, in)`: `out = (in.x * T[+0x14],
in.y * T[+0x18], 0)` then 0x42a4d0) ; `xform` as above; `layer` 0xb (weapon), 0xe / 0xf (timer icon).
Picture size in virtual pixels = `width * [0xcee050] * T[+0xc]`, `height * [0xcee050] * T[+0x10]`
(0x5ec615..0x5ec653: fild of the table's w / h).

The weapon element's picture indices are in `elem+0x2e8 + 4*i` (two slots). The vehicle icon is picture
170 (car, session vtable +0x17c == 3) or 171 (chopper) (0x81e16e..0x81e189).

Bars / rectangles: no separate fill routine found; the tracker and escape bars are sprite chunks
(pictures 161..164 "GameplayTracker bars", 181/182 "UI_White") drawn with DrawChunk and a scaled xform
(not established in detail).

### 3.3 The draw context and WHEN

`ctx` (ZDrawBufferSimple) and `cam` are the two arguments of 0x8bf300, which the OSD's render virtual
(slot 55, 0x558370) receives from the renderer: `cam+0x10c` = fov, `+0x114` = frame time, `+0x11c` = aspect
(0x8bf307.., 0x8bf39b, 0x8bf3e2). They are valid only inside that call. ZDrawBufferSimple has 6 virtuals
(0 dtor, 1 0x95e8c0, 2 0x4b8570, 3 0x6c4720, 4 0x796050 `ret 8`, 5 DrawChunk); it is constructed in
0x636c10. Whether 0x8bf300 runs on the main thread or the render thread is **not established** (the game
renders on its own thread, `re/freeze_1009.md`); KLHook should hook 0x8bf300 and do its drawing inside
that call, on whatever thread it is, reading only its own prepared data (prepare texts / numbers on the
main-thread tick, draw in the hook).

## 4. Coordinates, scale, inset

### 4.1 The transform (osd+0x1130, written every frame by 0x8bf300:0x8bf377..0x8bf43a; established)

```
A = 2 * tan(fov/2) * [0xcee048] / 1280        ([0xcee048] = 6.0: the HUD plane's distance)
B = A * (16/9) / aspect                        (0xb19de0 = 1.7777778)
T+0x00 = -640*A   T+0x04 = 360*B   T+0x08 = 6.0           (camera-space origin of virtual (0,0))
T+0x0c = A        T+0x10 = B                              (virtual pixel -> camera units)
T+0x14 = A        T+0x18 = -B                             (used by 0x5a3e90 for positions)
T+0x1c = 1280     T+0x20 = 720     T+0x24 = 1280  T+0x28 = 720
```
So the HUD is a **1280 x 720 virtual screen, origin top-left, y down**, filling the window: width maps to
1280 and height to 720 on every aspect (at 4:3 the picture is stretched vertically, no letterbox).
Nothing in the transform depends on the window's pixel size (1440p and 720p draw the same layout).

### 4.2 Inset

`[0xceeebc] = 0.05` and `[0xcee050] = 1.0` (HUD scale) are globals in the same block as 0xcee048; many
writers (0x42c52c, 0x4a8d42, ...): ASSUMPTION they are set from the options / `-o` table. The timer
(0x80e2d0): `x = T.w - T.w * 0.05 = 1216`, `y = T.h * 0.05 = 36` -> the round timer sits at (1216, 36)
right-aligned (style 0x12), second line at y + 28. The player list / weapon elements apply the same 5 % in
their slot 6 (0x72be40, 0x78f820: float constants in those routines are the per-element offsets - not
decoded one by one; the saved disassemblies have them).

### 4.3 Moving a stock element

Element positions (+0x14, +0x18) are recomputed in slot 6 every frame from the inset, so a one-time poke
is overwritten. Options: (a) hook the element's slot 6 (vtable +0x18, one address per class, table 2.2)
and adjust after the original; (b) in the 0x8bf300 hook, let the original run, then hide the element
(+0x25) and draw your own copy; (c) patch the float constants inside the slot-6 routine (they are
immediates / .rdata doubles: e.g. 0xb62770 = 28.0 line step, 0xb248d0 = 70.0 and 0xb404e0 = 36.0 icon
offsets in the timer's Render). (b) is the robust one.

## 5. Where the numbers come from (established unless marked)

Session: `[0x168e598]`; `+0x5c == 4` = FA / Arcade (0x7bb2a0); `+0x54` = session type (0..3, 0x863a60 /
0x7f6850: Arcade when 2 or 3 or +0x5c == 4); `+0x70` = state (0x8e6a20; 0x19 = GO, 0x17..0x19 = the round);
`+0x54` of the FA session = the local FA player (0x508ef0). `[0x168e9e4]` = the FA rules object whose
vtable has: +0x124 round time left (int seconds, 0x62a12c), +0x12c escape state 0..8 (the timer's colour
switch), +0x130 escape time left (0x62a1b3, 0x793d2a), +0x17c vehicle kind (3 = car), +0x134, +0x1c8, +0x290
flags (0x62a243..). `[0xdd2640]+0x48` = frame counter, `+0x50` = frame dt (0x76db3d..).

| HUD item | source | formatting |
|---|---|---|
| Total score ($) | `0x807520(player)` = player->vt[+0xe0](0) + Σ `[[player+0x5f8]+4..+0x2c]` + `[[player+0x5f8]+0x38]` (0x6f367b) | `"$%i"` (0xb5bf60) then 0x51f100 (thousands separators, ASSUMPTION) |
| Round N | `byte [[player+0x5f8]+0x45]` (0x6f38b9) | 0xb28098 format, 0x519010 concat |
| Player name | 0x6f3000 rows; names via 0x7bb920 / 0x61a240 (ASSUMPTION) | `{skull}` glyph for dead |
| Round timer | rules vt+0x124 -> 0x7818c0(seconds, buf) | `"%02d:%02d"` (0xb4eda0) |
| Heist starts in N sec | `AllLevels/Interface/Online/FA_GameStartCounter` with `{timer}` replaced (0x6d7f0e) | ZFAIntroDisplay |
| Ammo | ZWeaponDisplay tick 0x88bac0: `[player+0x920]` current item, `[player+0x924]`, `[player+0xcec]` inventory (0x49b2f0(item, 4) = count, ASSUMPTION) | ZCHAROBJs with layer 0xb |
| Vehicle distance | ZGameplayTrackerDisplay: `[entry-0x1c] * 0xb4c330` -> `"%.0f m"` (0x8e23a4) | pictures 161..172 |
| Vehicle health / hold time | ZFAEscapeDisplay slot 5: vehicle object `[rules vt+0x80]` -> `+0x40` list -> `+0x864/+0x868` (hp / max), time rules vt+0x130 | `FA_HoldEscapeVehicle`, bar colour white / 0xbbe498 below 0xb293f0 |

### 5.1 Localised labels

Lookup (0x470dc3, 0x6f36cf, established): `loc = [[[0xdd2640]+0xac]+0x94]; text = loc->vt[0](section,
key, 0)` -> `const char*`; sections / keys used by the HUD: `AllLevels/Menu/Heist/Status` +
`HeistTotalPoints` ("Total score"), `Round`; `AllLevels/Interface/Online` + `FA_BigLoot`, `FA_Traitor`,
`FA_DirtyCop`, `FA_UndercoverCop`, `FA_Invulnerable`, `FA_CnR_Revenge`; `AllLevels/Interface/Online/GameEnd/`
+ `Round` (headline); `AllLevels/Interface/Online/FA_GameStartCounter`; `.../Exit/FA_LastBoarding`,
`FA_LastExit`, `FA_Exit`. The strings "Total score" / "Round" themselves are in the level's .LOC, not in
the exe. `{timer}` / `{skull}` / `{Reward1}` are placeholders replaced by 0x83e2e0 / 0x7bb920 (string
helpers; 0x8f7eb0 = string init, 0x6ad680 = string free, 0x694bc0 = sprintf).

## 6. What KLHook can do (recipe)

1. Find the OSD: `osd = [0x154da50]` (null outside a level). Elements: `[osd + off]` from table 2.2.
2. Hide stock elements: `*(u8*)(elem + 0x25) = 1` once per level (the ctor zeroes it; re-apply when
   `[0x154da50]` changes). Hide the whole FA set with `0x75f780(osd, 1)` (thiscall).
3. Draw: hook `0x8bf300` (thiscall `(osd, ctx, cam)`, plain function, one caller 0x5583c6). After the
   original: for each own text, `obj->vt[+0x1e8](ctx, cam, &pos3{x, y, 0}, &xform)` with `xform` from
   `0x7f07a0(&local[9 floats])`; for each own picture, `ctx->vt[+0x14](handle, &desc, &pos2, &xform, layer,
   1, 0)` with `handle = [osd + 0x3ec + 12*n]`, `desc` = {1, 0, &vec3{0,0,0}, ...0x34 bytes, [+0x30] = ARGB},
   `pos2 = 0x5a3e90(osd + 0x1130, &out, &in{x, y})`.
4. Own texts: make them once per level after the OSD exists, cloning the template as 3.1 does
   (`0x8ccde0([osd+0xd4c])`, `0x598460([tmpl+4])`, `tmpl->vt[+0x19c](parent, 0x5a434f42, 0,0,0,0)`, then
   SetFont(`0x8ccde0([osd+0xd54])` for the FA font, `+0xd50` for the headline font), SetColour, SetStyle,
   SetLayer, SetText). Lifetime: the game frees its own ZCHAROBJs with the level; ours must be made
   through the same create path so they are freed with the scene (ASSUMPTION: the scene owns children
   made by +0x19c).
5. Numbers: read as in 5 on the main-thread tick; format with the game's own `0x7818c0` (mm:ss) and
   `sprintf`; labels from the .LOC through 5.1 (so the owner's language is kept).
6. Patchable constants: `[0xceeebc]` inset 0.05 (one write at level start), `[0xcee050]` HUD picture scale,
   the colour u32s at 0xbbe490..0xbbe4a4 (.rdata, VirtualProtect), per-element doubles named in 4.3.

## 7. Not established

- Which thread calls 0x8bf300 (render thread suspected).
- The exact meaning of ZCHAROBJ style bytes (0x12 vs 0x44), and of Init args 3 and 4.
- ZDrawBufferSimple desc layouts 2..8 (0x842dbc switch) - only kind 1 (sprite) is used by the elements read.
- The three global displays [0x154da58..60]; the writers of [0xcedfb8]; the texture flag table at 0xcee058
  (0x14-byte entries to 0xceeea4, indexed by picture id in 0x5e3810).
- Whether a hidden stock element still allocates / plays sounds (the Tick runs; only Render is skipped).

## 8. DrawChunk read in full (2026-10-11, kl-merge-3e; static) and the open question

`ZDrawBufferSimple::DrawChunk` 0x842d00 `(this = ctx, chunk, desc, xform9, pos3, layer u8, f1, f2)`, `ret 0x1c`:
- `chunk == 0` -> returns 0. A negative chunk is a direct pointer (bit 31 cleared), else `[0xeac7b0 + 4*chunk]`.
- `inst = 0x5f6ad0(renderer = [[[0xdd2640]+0x970]+0xfc], chunk)`: takes a cached render instance for that chunk out of a
  256-bucket table (0x815f40, key `chunk >> 4`), else creates one through the factory chain at `[0xef4d88]` (0x770d40);
  a new one is listed at renderer+0x5f9ec. `or word [inst+4], 5`. NULL -> DrawChunk returns 0 (nothing drawn).
  So EVERY call gets its own instance: two draws of one chunk in a frame are two instances (no de-duplication).
- matrix from `xform9` (0x64ecc0), translation `pos3` -> 0x78f360(inst, &m); `[inst+0x1a0] = f1`;
  `[inst + frame*20 + 0x1ac] = 5 dwords of the chunk` (frame = `[0xef4d7c]`); the desc is COPIED into a per-frame block
  (0x926db0, size by the chunk's kind 1..8 at chunk+0xc) -> `[inst + frame*4 + 0x1a4]`; `[inst+0x1a1]` = has data.
- `0x5359d0(inst, layer)`; then **`[ctx+8][[ctx+4]++] = inst`** and the instance is returned.
The element's picture call (timer, 0x81e20b..0x81e275): `pos2 = 0x5a3e90(T = [elem+0xc], &out, &in)` = (in.x * T[+0x14],
in.y * T[+0x18], 0); `ctx->DrawChunk([[elem+0x38]] = the sprite handle, elem+0x40 = desc, &xform9 (0x7f07a0: [6] = 1.0 =
scale), &pos2, 0xf, 1, 0)`. The text Draw (0x8f7420) hands `obj+0x48` (its 9 floats, [6] at obj+0x60 = the 0.005972
scale) and `obj+0x6c` (translation) to the same routine, one call per glyph run.
OPEN: nothing in this path tells a hook's call from the game's own, yet every Draw the hook issued (own objects, borrowed
level objects, the timer's own text a second time) was invisible in runs H1c .. H1n while a string set into a stock object
and drawn by the stock Render shows (H1l). `[HUD] Probe=1` (klhud.c, build hud_probe1) measures the buffer count and the
instances per step and calls the stock Render re-entrantly at another place / with our objects: run P1 owed.
