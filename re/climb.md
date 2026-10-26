# The climb Dead Men had and Dog Days dropped (the bank's yard wall first)

2026-10-11, track F. OFFLINE: static reading of `kl2.exe` (build 0490) and `kaneandlynch.exe`, the 20 + 21 stock
level files, and the bank build `<work>\build\z_hop\M03` (read only). **Nothing here ran in either game. Nothing is
installed, nothing is wired into the hook, nothing is committed.** (The first version's words. SINCE THEN the file
was wired and RUN ONCE, and the game crashed in the clip: the 'Fourth version' paragraph below and
`re/climb_crash.md`.)
Three readers did parts A, B and C; their scratch notes are not in the repo, so what the plan rests on is written
out here. What the PLAN rests on was read again by the writer of this file: every kl2.exe routine of section 3,
the head of the vault test, `0x619790`, the vault's start, the NPC link mover (1.2 - 1.4), Dead Men's table, enter
and callback (2.1; the constants of its ray test were confirmed in the reader's listing, the routine itself was
not read a second time), the clip records and the merge (done again by the tool of 4.1), the wall's geometry.
The cover list of 1.1 and the stock counts of 1.5 are the reader's, taken over. kl2.exe addresses can be re-read
with `python debug\dasm.py f:<address>`. Where a reader's note was wrong it is corrected (section 6).
Status words: **read** = seen in the disassembly at the address given; **measured** = counted on the files, the
command is named; **ASSUMED**; **not established**.

Built with it (section 4): `tools/kl_fa_climb.py`, `<work>\build\z_climb\M03` (first form; the build to run is
`z_climb3\M03`, 4.2b), `klhook/klclimb.c` (wired since commit 9c8077d).

**Second version, 2026-10-11, after the adversarial review `re/climb_review.md`** (verdict: account and build
accepted, `klclimb.c` not to go live as written). The level's half and the build are unchanged. `klclimb.c` was
rewritten where the review asked (section 4.3) and this account corrected (sections 1.3, 2.1, 3, 4, 5, 7, 9; the
list is section 6.2). Every kl2.exe routine the file calls or relies on at the changed places was read again with
`debug\dasm.py` for this version: `0x4af5b0` and how the game's own enders call it, `0x82f780`, `0x5c8f70`,
`0x447bd0`, `0x4815c0`, `0x5fcb80`, `0x82cc40`, the cover tests `0x40f840` / `0x6e2740` / `0x780b80`, the mini
animation's caller `0x5022c0`, its start `0x76d1d0` and slot 10 `0x42b7f0`, the dispatcher `0x672d00` /
`0x5d0260` / `0x595b70`, Play `0x4da1d0`, AlignTo `0x80fdc0`, the player's frame `0x74efc0`, Move `0x6e6730`,
`0x6d4570`, `0x41a6b0`, the animation movement's update `0x5397e0`, the physics step `0x6d1ad0` / `0x4d1310`,
the animation update `0x50ac80` (its head and its reports), the frame clock `0x70da30`, the vault `0x619790` /
`0x6a27e0`. Two things came out of that reading that the review did not have and that change the fix:
- **The review's fix for its MUST (put the proxy at the node 'immediately before `0x686600` in both end paths')
  would come one frame too late.** The game ends the action and steps the ordinary movement from the proxy inside
  the SAME frame routine (3, 'who moves him'), before any tick of the hook. So the file hands the proxy and the
  collision back a few frames BEFORE the clip ends (4.3).
- **Who reports a replaced channel is settled**: Play itself, before it returns, to the action that is already
  current (3). A vault started while a full-body channel plays is freed inside its own start; the file now counts
  those channels before the call and refuses.
The hook file was also BUILT for the first time, in a scratch copy of `klhook\` with the three lines added (4.3):
that showed a link error the syntax check of the first version could not (`GetAsyncKeyState`: the hook does not
link user32), now fixed. **Still nothing ran in either game.**

**Third version, 2026-10-11, after the second review `re/climb_review2.md`** (verdict: accept with fixes; no
MUST; its three SHOULDs D1 - D3 and its notes N1 - N6). All three SHOULDs are fixed and the notes are taken up;
the table is section 6.3. In short, in `klclimb.c`: a vault start that leaves the collision switched off with no
action behind it is given back by the file (D1); the vault's channel refusal is asked again while he stands and
is a verdict only after a second (D2); the two wrong numbers of K2's decisive line are corrected (D3) - and
changed again, because `HandFrames` is 5 by default now (N2: the hand-over comes at frame 46, not 48); the
frame's two other gates are refusals (N1); `Align=1` aims 10 over the top (N3) and is refused for class Low (found
while measuring N3); the proxy is never put inside the obstacle (N4). What each rests on was read or measured
again by the writer of this version: `0x74efc0` (its three gates, `0x598460`, the node write and `0x5380d0`),
`0x8caf30`, `0x5aa510`, `0x536a20`, `0x72d010`, the vault's start `0x6a27e0` (leave-cover at `0x6a2817`, the
collision-off call at `0x6a2a4a`, Play at `0x6a2a5d`), `0x619790`'s two ways out, `0x8b41c0`, `0x686600`; the
clips with `kl_fa_climb.root_keys` (scratch `meas.py`). The level's half and the build are unchanged.
**Still nothing ran in either game; the file is still NOT WIRED.**

**Fourth version, 2026-10-11, after the FIRST LIVE START** (the lead wired the third version - commit 9c8077d - and
ran it on `z_climb\M03` with a scripted player; the earlier runs ended with him dead inside the bank, the first
that reached the wall was `K2c_DM03_wall_hp`, 10:02). **The game crashed 0.24 s into the clip, at kl2.exe+0x7e400. The account is
`re/climb_crash.md`**; in short: a mini animation is handed its clip's events, its event routine is
`ZFFActionGeneric`'s (`0x637060`), and at event id 5 that routine aligns to an object a mini animation has not got
(`[action+0xc]`, used with no test at `0x6370e7`) - and Dead Men's climb clips carry id 5 at frame 6. What the run
showed before that is good news for the plan and is written into K1 / K2 (section 7): the node's place, the proxy,
the facing sign, the slot, the kept action, the clip, and that the game TOOK the first alignment (**(5)** this line
said 'the root IS at P1 at frame 6': that was never seen, 6.5).
Changed for it (6.4): the level's players' clips carry event id **105** instead of 5 (`tools/kl_fa_climb.py`; the
build is `<work>\build\z_climb3\M03`, from `z_cover3\M03`), and `klclimb.c` reads that id and refuses to play a clip
with an event id the game's routine acts on. New in section 3: the rows on clip events. **`z_climb\M03` and
`z_climb2\M03` are of the first form and must not be played by the third version of the hook.** Of the fourth
version nothing has run in the game; of the climb nothing after clip frame 6 has been seen.

**Fix round of the fourth version, 2026-10-11, after the crash's own review `re/climb_crash_review.md`** (accept
with fixes: one MUST, text only; four SHOULDs; none refuted - the table is 6.5; what is marked **(5)** came in with
it). The MUST: this account said 'nothing else reaches a mini animation' besides its own clip's events and the
channel reports. Wrong: **the current action is handed the clip events of EVERY subscribed channel of its player**
(section 3), so an id-5 event of another clip that plays on him during the climb would fault the game at the same
address. For the build of today that is closed by reading and counting (only an action's start subscribes a
player's channel; the mini animation's Play stops the full-body channels; the 872 clips of the other body class
carry only ids the routine returns at), and since this round it is a rule on both sides: `kl_fa_climb.py check`
FAILs a build with such a clip, and `klclimb.c` refuses or calls off a climb beside such a channel. Besides:
'the root is at P1 at clip frame 6' was an assumption written as seen (the dump holds neither his node nor his
proxy) - corrected everywhere, and the hook's `aligned to P2` line prints his node from now on; `klq_code`
compares the way to the event routine too; and the first live start was most likely one with FORWARD HELD
against the wall (the gate measures his node, not the keys): **the rerun with the same script is K2b, not K2**
(section 7, set-up). The level build is unchanged (`z_climb3\M03`, the same archive). Nothing of it has run.

## 0. Verdicts

1. **Can a wall be crossed by Dog Days' own vault with level data alone? By the rule yes, as a climb no.** A low
   cover box (`*CoverBoxM*`) whose `PlayerCoverModifier` has the top state `ON_VAULT_ON` on the side one stands at
   gets flag 0x800, and the vault test `0x7a8480` answers yes on that flag before it looks at any geometry; the
   move runs with the player's collision off. But the clip is a 0.92 s hop made for a 1 m obstacle whose root
   does not rise: at the bank's wall (**203.5 over the yard floor**, 50 thick, the street 253.5 under its top)
   the man crouches at a wall taller than himself and slides through it. Without the forced flag the game
   refuses anything that reaches 145 over the feet. No stock level forces a vault on a box higher than 107.
   A drop on the far side is no obstacle (nothing looks for a floor; stock F04 / F06 vault into 4 m drops).
   Whether a low cover is ENTERED at a 2 m wall at all is not established.
2. **Dead Men's climb needs no level data**: `ZFFPlayerMovementClimb` finds the edge with rays (25 < h <= 220
   over the feet; Low <= 120, Medium <= 170, High <= 220), is asked for by the USE tap while the player is slower
   than 375 a second, and is carried by the clip's own root motion, aligned twice. The bank's wall is `High`
   from the yard (203.5; the rule holds on the build's collision at 63 of 65 places tried, 4.2) and too high from
   the street (253.5), where Dead Men climbs dumpster, then wall.
3. **Dog Days still has the NPC half** (the navigation-link mover `0x4a5160` with the three slot names, called
   for links of kind 1) and **no player half**. No Dog Days `.ANM` has the slots or the clips. The clips can be
   put into a Dog Days file slot by slot (+141,248 bytes, 12 clips, 3 slot names, no bone name; every proof
   holds); `kl_anm.py merge` cannot do it (it merges whole collections).
4. **A hook can play Dead Men's clip on the player with four game routines the game uses itself**: the mini
   animation start `0x5ea340` (a full-body clip on a standing or walking player, with its own guard), the
   alignment `0x80fdc0` (the routine the NPC mover calls for these very clips), the collision switch
   `0x5d6200` / `0x686600` (what the vault brackets itself with) and the proxy sync `0x4af5b0` (what every
   animated move of the player ends with, before the collision goes on). The last two have to be called a few
   frames BEFORE the clip ends, not after (3). The game's own vault can also be started at any place with one
   call, `0x619790` - with the vault's clip, and only while no full-body channel of his plays (3).
5. **The plan (section 5): (iii) first** - Dead Men's clip played by the hook at marked edges, at wall pieces that
   still STAND, **with (iv) kept in the same build**: the piece `kl_escape` sank stays sunk, so the way that works
   today and the AI heisters' drop link are untouched. (ii) is the fall-back mode of the same hook file. (i) is
   not worth building. **For the game as it is installed today the answer is (iv): the opened wall stays** -
   until live check K2 has shown a climb.
6. The AI heisters gain nothing from the hook part; their climb would be level data alone (clips, done here, +
   kind-1 links and two wall-top polygons in the mesh, not done). They cross by the drop link today.

## 1. A - Dog Days' vault (kl2.exe)

### 1.1 From a named box to the prompt (read)

| step | where | what |
|---|---|---|
| cover list | `CFFCoverList` slot 13 = 0x6d6a80 | every ZSTDOBJ-family entity (ZBoxPrimitive 0x2000e1 too: 313 stock covers are box primitives) whose NAME matches `*coverbox*`, at most 5,000 |
| a box | 0x603830 | record 0xa8 bytes: +0x08 car, +0x0c 12 modifier states, +0x4c type (0 low = `*coverboxm*` / `*coverboxl*` / `*coverboxcar*`, 1 high = `*coverboxh*`), +0x50.. HALF sizes, +0x90 four side pointers. Refused when the box is tilted (up axis y < 0.717) or has a `DynamicCover` controller |
| a side | 0x603450, 0x6e7740, 0x8e5690 | 0x58 bytes: +0x0c / +0x18 the two ends of the BOTTOM edge of the face, +0x24 / +0x28 / +0x3c flags of the left end, the right end, the top, +0x2c the outward normal, +0x54 depth = the box's full thickness. Side order 0 = +x, 1 = +z, 2 = -x, 3 = -z of the box's own axes (jump table 0x8e5858) |
| modifier | `ZPlayerCoverModifier`, controller `PlayerCoverModifier`, 96 enums `AUTO ON OFF ON_VAULT_ON ON_VAULT_OFF AUTO_VAULT_OFF` (0..5) | on a box it governs that box (slot 0); on a group its children named `*CoverBox*` take eight slots in order (0x7fe590, 0x4be840). Field i of a slot = side i // 3, part i % 3 (left end, right end, top) |
| side flags | 0x440de0 | top state on a LOW box: `ON_VAULT_ON` -> 0x40 and **0x800**; `ON_VAULT_OFF`, `AUTO_VAULT_OFF` -> 0x1000; `OFF` -> 0x80. AUTO: a ray from the side's middle at bottom + 110 (5 in front, 90 into the box) or a half height over 120 marks the top 'not open' |
| in cover | 0x849700 -> 0x797480 | a box is a candidate only when its BOTTOM is within 50 of the player's feet (0x797634); then the side test 0x653270 and a scoring that was not decoded (0x792e30, 0x77a100) |
| prompt | 0x58f8e0 -> bit 0x10 of [player+0x2d60] | in cover, movement kind 3, the box not high, and 0x7a8480 says yes |
| input | 0x44f260 at 0x44fc10 | bit 0x10, the stick INTO the cover, the cover key -> `0x6fd880(side, left)` |

### 1.1b Side flags and the usable test (decoded 2026-10-26, workflow wrwx4xpto; COVER12 live data)

- **0x440de0, AUTO, per side and end.**
  - **0x10:** face length under 69 (0xb6eeb0).
  - **0x8:** set on both ends when box +0xa4 != 0; nothing else is computed then.
  - **0x2, no floor beside the end** (0x550360): the sample is the end +-30 along the edge and 70 out (vector roles GUESS); ground at y+25 must be within 150 vertically and 50 horizontally. If both ends fail, the top gets 0x2 too.
  - **0x1, obstruction** (0x64db40): an overlap query, mask 0x200000, group 0x1b, extent 40, height 60 (130 on a high box).
  - **Top:** 0x1 on every high box, on a failed ray 0x57dcb0, or when the half height is above 120; 0x400 on a high box when the face is shorter than 210 (0xb49e98) and an end failed.
  - **Modifier states** (`[mod+0xc+(side*3+part)*4]`) are ORed in after the AUTO pass. ON gives 0x40 on that part; vault states give 0x800 / 0x1000; OFF gives 0x80.
- **0x653270, the side is usable when ANY part passes.**
  - An end passes iff `!(f&4) && !(f&0x2200) && ((f&~0x1800)==0 || f&0x40)`.
  - The top passes on the same test with 0x200 in place of 0x2200.
  - So one clean end is enough. 0x1 or 0x2 at both ends (3/3/0x403) means no cover, unless 0x40 (ON) is set.
  - 0x7dfe80 is the same test, per part, used by the scoring.
- **Live checks.**
  - Stock CoverBoxH_Right_01's front face reads 0/0/0x1 and gives cover.
  - Our wall-backed K6_52's far face read 3/3/0x403 and gave no cover; its end read 3/0/0x401 and gave cover.
  - The fix (f0db5c7ca, toggle COVERON) authors a PlayerCoverModifier ON on the built-for face's two end parts.

### 1.2 The vault test, 0x7a8480 (read; the first lines re-read here)

```
if [player+0x2954] or not in cover (0x40f840)                 -> no
side = 0x7a26d0(player)                                       the cover side he is on
if side.top & 0x1000                                          -> no
if side.top & 0x800                                           -> YES (0x7a84c5: nothing else is looked at)
if the box is high or a car; BaseMove's byte +0x1e70; the ability bit 0x10 of [gamedata+0x4d48] clear  -> no
d = distance from the face                                    -> no when d > 100
land = 50 beyond the back face, at the player's own height; far = 110 beyond
two Havok triangle overlap queries (0x475dc0, radius 5, the player's layer 5):
   (player - 50 along the face, land, player + 50 along the face), all at feet + 150
   (far - 40, land at + 150, far + 40 at + 30)
a hit on anything the player collides with -> no
```
So without the forced flag: nothing may lie 145 .. 155 over the feet between him and the landing (no wall of 145
or more), nothing more than 30 higher than the take-off within 110 beyond. No depth limit. **No floor is looked
for: a drop is not tested.** With the forced flag none of it is evaluated.

### 1.3 How the player is moved (read; `0x619790` and the action's start re-read here)

- `0x619790 = bool __thiscall ZFFPlayer::StartVaultOver(cover *, char left, float pos[3], float rot[9], char given,
  char writeBack)`, `ret 0x18`. It tests nothing. From the cover record it reads +0x0c (3 floats), +0x2c (3
  floats), +0x54 (float) and stores the pointer at action +0x7c (read by nothing in the action's methods).
  End = player place - normal * (distance from the plane + depth + 50) (0xb71b60 = 50.0), **at the player's own
  height**; with `given` the caller's `pos` / `rot` are the end instead - that is the network receiver 0x60c610
  (the RMC `VaultOverCover(bLeft, x, y, z, angle)`). It takes action kind 0x2b from the player's factory (vtable
  +0x384 = 0x839740), stops the current action (+0x374) and starts the new one (+0x370). In Arcade it also
  writes one telemetry event (`FAVaultOverCover`, 0x447660), no Steam stat.
- `ZFFActionVaultOver` (vtable 0xbb5188, made only by `ZFFPlayer`'s factory). Start 0x6a27e0: leave cover
  (0x5fcb80), a Havok phantom that knocks things over, the clip slot by NAME - `/Cover/Vaulting/Cover_Vault_
  {Left|Right}_{1M|2M}`, **2M when the way start -> end is over 175.0** ([0xb5820c], 0x6a29d4), else 1M: the
  names are a length, not a height -, `player->vtable[0x560]()` = collision off (0x6a2a44, the call at
  0x6a2a4a), `Play(clip, 1)`
  (vtable +0x204, 0x6a2a5d; for a null clip Play returns no channel and 0x6a2a65 reads through that CHANNEL),
  `AlignTo(end rot, end pos, frames - 1)` (vtable +0x208, 0x6a2a8a). **(3)** The order matters: leave-cover
  runs at 0x6a2817, long BEFORE the collision-off. The action is current from the dispatcher's 0x672d07 on and
  says yes to any report, so an End that runs before 0x6a2a4a switches 'on' a collision that was never off
  (0x8b41c0 does not count below 0), the object is deleted, and the start goes on to switch the collision OFF
  with no action left to switch it on. Whether leave-cover can cause such a report was not read (0x5abbb0,
  0x834ef0); `klclimb.c` reads the count after the call and gives it back itself (4.3, the second review's D1).
  `0x619790` itself returns 0 only when the action pool is empty (0x619826 -> 0x6199c7: nothing stopped,
  nothing started), else 1 whatever became of the action. **End 0x82f780 (read whole for the second
  version): `0x594960` (-> 0x6721a0: four state words of BaseMove `[player+0x63c]` are set - +0x1e38 / +0x1e3c
  = 0xf, +0x1e40 / +0x1e44 = 1 - and 0x5abbb0 is called, not read), `0x4af5b0` =
  the character proxy is put at the node (0x82f796), THEN collision on (vtable +0x564, 0x82f7a6), `0x74a120`,
  the phantom is taken out of the world, and the placement `0x82cc40` at the end place when he is dead or down
  (`0x6a88f0`).** Its 'a channel ended' slot (0x553070) is `mov al, 1`: ANY ended or replaced channel report
  finishes it - and Play reports the channels it replaces before it returns (3).
- Collision off, three things: `[player+0x7a5] = 0` makes the stepwise collision of a move (ZMovementBase slot
  34, 0x7aa2b0) answer at once AND makes the animation movement skip its physics step (3, 'who moves him');
  byte `[player+0x968]` is cleared (0x5d620e; what it stands for was not read - the proxy integration 0x87fb30
  asks for it at 0x87fbea, BaseMove clears it in cover at 0x7a4a71; 'on' does not set it again); and the body
  goes to Havok layer 0xc, which collides with no layer but 0 in the 28 x 28 table built at 0x5afcf0 (level
  collision is layer 6). 'On' sets layer 5 whatever the count is.
- The clips (measured, `scratch recs.py` on the build): `Cover_Vault_*_1M` 23 frames, root (29, **0**, -189 /
  -204); `_2M` 29 frames, (30, 0, -281). The root does not rise: the body's hop is in the pose.

### 1.4 NPCs (read)

They never vault: action 0x2b exists only in `ZFFPlayer`'s factory (`ZFFActor`: kinds 3..15, 0x11, 0x12). An NPC
crosses a height difference only on a navigation link: `ZFFSpecialLink@Locomotion`, vtable 0xb78dd4, slot 1 =
**0x4a5160** (re-read here): it starts within 40 of the link's start (20 for kind 2); `dy = end y - start y`;
**kind 1: dy > 170 -> table +0xc `High`, > 120 -> +8 `Medium`, else +4 `Low`**; kind 2: |dy| > 160 -> `Fall_2m`,
else `Fall_1m`; kind 3 `Leap/Forward`. With a clip: matrix from MINUS the direction of travel (0x70fa70,
0x55f8f0), the frame of clip event 6 (0x4a75d0), Play (vtable +0x200), **AlignTo the link's END at event 6**
(vtable +0x208). No clip for the slot -> nothing is played. The table 0x15489e8 is filled at 0x579920, the only
reader of the three `/Movement/Climb/Up/*` strings. Stock Dog Days: 192 links, all kind 2.

### 1.5 Stock, measured (21 levels; the readers' `covers.py`, `farside.py`)

- 12,971 objects named `*coverbox*`: 5,388 low, 7,229 high, 299 car; 3,431 `PlayerCoverModifier`.
- Top state of the 21,552 sides of low boxes: AUTO 18,187, OFF 1,801, ON_VAULT_OFF 1,090, AUTO_VAULT_OFF 220,
  **ON_VAULT_ON 133** (80 boxes in 14 levels), ON 121.
- The 133 forced vaults: box height 86 .. 107, depth 8 .. 201 (median 100; one 785), the real obstacle under
  them 101 (median), 109 (third quartile). Floor beyond: median 0; 14 land more than 30 lower - F04
  `F04_Outside_EscapeStreet\CoverBoxM_05 / 09 / 13 / 14 / 24 / 30` (404 -> 0), F06
  `Money_Transporter_WarehouseCorridor\CoverBoxM_01..03` (-800 -> -1200, states `AUTO AUTO ON_VAULT_ON / OFF x 9`:
  one way), F02 `Bridge_Highway_01\CoverBoxM_Box14` (1810 down).

## 2. B - Dead Men's climb (kaneandlynch.exe) and its clips

### 2.1 `ZFFPlayerMovementClimb`

Vtable 0x966c44, size 0xec, movement id 0xb, made only for `ZFFPlayer` (0x5ef1c0). Read whole by the reader;
the table, the enter and the callback were read again here.

- Table (slot 20, 0x603340), three records at this+0x68:

  | slot (walking) | sprinting | height | distance |
  |---|---|---|---|
  | `/Movement/Climb/Up/Low` | `/Movement/Climb/Up/Sprint_Low` | 120 | 81 |
  | `/Movement/Climb/Up/Medium` | same | 170 | 47 |
  | `/Movement/Climb/Up/High` | same | 220 | 47 |

  81 / 47 are the stand-off from the face at which the clip wants the feet when it starts, not a height.
- The test (slot 14, 0x605b50). **No level data is asked for**: no flag, no name, no controller, no link.
  0.5 s since a stamp; speed under 0.75 x 500; no hand action; the USE tap one frame earlier (`TapUse`).
  Geometry, feet = 90 under the reference, `hd` = 25: four rays straight DOWN 310 from 310 over the feet, at
  25 / 40 / 55 / 70 in front; per top (near to far, a lower one than the last is skipped): **a clear way** 15
  over the top (from 15 behind him, d + 30 long, so to 15 past the probe - the first version said 30; the tool
  has always had d + 30: must miss), **180 headroom** over the top (a hit
  refuses everything), **a face** 1 under the edge (must hit), **h > 25**, the first table record with height
  >= h (none: no). Refused on a `ZHavokCar` unless two car bytes allow.
- Carried (enter 0x602f30, callback 0x603160): play to the frame of clip event 5 and **align** (0x526620) the
  root to `P1` = the face's foot, distance D back from the wall, at feet level; then play on and align to
  `P2 = P1 + (0, h, 0)` at the frame of event 6; after that the clip's own root motion goes on. The clip's
  frames are 25 a second. He keeps his heading (the matrix is built from his own back vector).
- Far side: no second clip. He ends ON the obstacle (table below) and `ZFFPlayerMovementFall` takes what comes.
- A network path in the same routine replays the climb for remote players (replicated movement id 0xb).
- NPCs: `ZFFSpecialLink@Locomotion` (0x5e5690) on links of kind 1 - the routine kl2's 0x4a5160 is, instruction
  for instruction. Measured: 195 kind-1 links in 11 campaign levels, **none in a Fragile Alliance level**.

### 2.2 The campaign bank has the climb at our wall (measured by the reader on the navigation meshes)

`M03_A` (the campaign chapter 'Withdrawal'; the same building at the same coordinates as `M03_FA_A`,
re/campaign_fa_bank.md) has two lanes, x = -3210 and x = -2938, at wall piece `SO0101_M03_Wall_Low_8m_02` and
the dumpsters `SO0701_M03_Dumpster_A_03 / _02`:

| step | from -> to | kind up / down | dy | across | cost |
|---|---|---|---|---|---|
| yard <-> wall top | (x, 220, -660) -> (x, 404.5, -625) | 1 / 2 | 184.5 = High | 35.5 | 184 |
| wall top <-> lid | (x, 404.5, -575) -> (x, 284, -540) | 2 / 1 | 120.5 | 35.5 | 114 |
| lid <-> street | (x, 274, -480) -> (x, 150, -409) | 2 / 1 | 123.6 | 70.9 | 117 |

Wall-top polygons 132 / 133 are one-polygon areas (z -625 .. -575, y 404.5, area boxes y 304 .. 504), two
waypoints each, every waypoint on a border edge. `M03_FA_A` (and our build's mesh, 697 polygons) has no
wall-top polygon; the lid polygon is still there (544, area 41, no waypoint), the street polygon is 688, the
yard polygon 527. In the campaign the PLAYER comes the other way at the very start of the chapter: from the
back street (checkpoint 1 at (-2976, 154, -202)) over a dumpster and the wall into the car park
(re/campaign_fa_bank.md, beat 2).

### 2.3 The clips (measured: all 41 stock `.ANM`; `tools/kl_fa_climb.py check` prints the table for a build)

- All 20 Dead Men files hold the same 9 slot names (`/Movement/Climb/Up/Low | Medium | High | Sprint_Low`,
  `Down/Low | Medium | High`, `Ladder/Up | Down`) and the same 17 clips `anim:Movement/Soldier/Climb#...`.
  Nothing in either exe asks for the `Down` / `Ladder` names. **0 of 21 Dog Days files** has any of the slots or
  a clip with `Climb` in its name.
- Dead Men's sets: the player sets (`PlayerCharacter`) play the player-timed clips, every NPC character set
  (Police, Army, Civilian, Female ...) the `_NPC` ones. Lists are `condition:clip` pairs, the default last
  (condition 8 / 0x10: pistol / unarmed, ASSUMED from the clip names).
- The record's vector +0x18 is the clip's net ROOT translation (new; equal to last root key - first on every
  climb clip). The root track: clip data +0x24 = track 0 = {4 offsets, bone}, the root is bone 0x39 (GROUND) by
  number in both exes; position keys = an `IdxT` frame table + raw float triples (kaneandlynch 0x5bfa60 /
  0x5bdbd0; `kl_fa_climb.root_keys`). Vectors +0x30 / +0x3C are NOT root motion (a unit vector and a place,
  zero in the unarmed clips).
- The player's default clips (25 frames a second; y up, forward = -z; root relative to its first key):

  | class | clip | frames | events | root at event 6 | root at the end | after event 6 | ends (with Dead Men's alignment) |
  |---|---|---|---|---|---|---|---|
  | Low | `Climb#Sprint_Low` | 27 (1.08 s) | 5 at 6, 6 at 16 | (-7, 102.7, -60.8) | (-17, 106, -145) | 84.2 forward, 3.3 up | 3.2 past the face, 3.3 over the top |
  | Medium | `Climb#Up_Medium` | 37 (1.48 s) | 5 at 6, 6 at 16 | (0, 118.5, -0.5) | (-15.8, 118.5, -62.4) | 61.9 forward, 0 up | 14.9 past the face, on the top |
  | High | `Climb#Up_High` | 52 (2.08 s) | 5 at 6, 6 at 20 | (-0.1, 147.5, -9.8) | (-0.9, 172, -101.2) | 91.4 forward, 24.5 up | 44.4 past the face, **24.5 over the top** |

  NPC clips: `Up_High_NPC` 52 frames, event 6 at 25 with the root at (-0.5, 166, -39.9): the campaign's 35.5
  across fits it; `Up_Medium_NPC` 31, event 6 at 24; `Sprint_Low_NPC` 27, event 6 at 13.
  **(4) In a BUILD the players' clips carry event id 105 where this table says 5** (same frames; the fourth
  version, `re/climb_crash.md` 6): Dog Days' generic action answers id 5 itself. The other variants of the
  players' lists: `Up_High_No_Weapon` 5 at 6, 6 at 20; `Up_Medium_Pistol` / `_No_Weapon` 5 at 6, 6 at 16;
  `Sprint_Low_No_Weapon` 5 at **3**, 6 at **15** (so the frames belong to the clip, not to the class). That last
  clip is also in Dead Men's `Police` Low list (its pistol / unarmed conditions), i.e. in the NPC sets of a build.
  The 24.5 the High clip still rises after event 6 (the code puts the feet at top level AT event 6) is not
  established: a settle of that size at the end is what the numbers say. Stock Dog Days has the same shape in a
  path it does run: `Fall#Fall_1m_NPC` has its root at -93.2 at event 6 and ends at -100.
- All climb clips have record flags 0xc0 / 0x10c0 (0x40 = root motion, what kl2 0x760120 asks for) and +0x28 = 0
  (a full-body clip), like the vault clips.
- **Where he is in the last frames** (measured for the second version on the merged file with
  `kl_fa_climb.root_keys` / `root_at`, the root after Dead Men's alignment: at event 6 it stands the stand-off
  before the face at top level). It decides when a hook may give the collision back (4.3):

  | class (default clip) | last frame | full height from | beyond the face from | 10 beyond from | 5 frames before the end | 3 frames before the end | at the end |
  |---|---|---|---|---|---|---|---|
  | High `Up_High` | 51 | frame 28.8 (+24.5) | frame 43.4 | frame 45.1 | frame 46: 15.4 beyond, +24.5 | frame 48: 27.2 beyond, +24.5 | 44.4 beyond, +24.5 |
  | Medium `Up_Medium` | 36 | frame 16 (+0) | frame 31.6 | frame 34.6 | frame 31: 1.6 BEFORE the face, +0 | frame 33: 4.8 beyond | 14.9 beyond, +0 |
  | Low `Sprint_Low` | 26 | frame 25.9 (+3.3) | frame 25.7 | never | frame 21: 38.9 BEFORE the face, +1.6 | frame 23: 22.1 BEFORE the face, +2.3 | 3.2 beyond, +3.3 |

  The root still WALKS in the last frames (High 5.7 a frame, Medium 3.4, Low 8.4): the clips end in stride, not
  in a stand. High rises its 24.5 between frames 20 and 29 and keeps it. Low is over the edge only in its last
  third of a frame: in Dead Men the sprint carries him on; here it ends at the edge (not for a live run before
  High has been seen).
- **With ONE alignment at the last frame** (the hook's `Align=1`; measured for the third version, scratch
  `meas.py`: the game blends a correction in linearly up to its target frame, 3 `AlignTo`). Aimed AT the top,
  the root crosses the face UNDER it, because part of the rise is still to come: High, top 203.5 over the feet -
  5.0 under at the face (frame 42.9), 3.1 under at frame 46, 1.8 at 48, level at 51; top 220 over the feet - 7.6
  under at the face; top 183.5 - 1.8 under. Medium, top 170 - 7.0 under at the face. Aimed 10 OVER the top:
  High 0.8 (top 220) .. 3.4 (203.5) .. 6.6 (183.5) over at the face, 5.9 over at frame 46 (203.5); Medium 1.6
  (170) .. 7.1 (130) over at the face. The Low clip cannot be carried by one alignment at all: its root lunges
  51.9 forward in its first 3 frames (keys at frames 0, 3, 16, 26) and only the first of Dead Men's two
  alignments takes that back - from a stand 40 before the face he would be through it at foot level by frame 2.7.
- **With only the FIRST alignment set** (a climb called off before the second, measured the same way): the root
  rises by the clip's own 175.5 only, which is 28.0 under a top 203.5 over the feet; it is beyond the face from
  frame 43 (4.6 beyond at 43, 16.0 at 45, 33.7 at 48, 50.9 = beyond the far face at 51). Between frames 43 and
  50 that place is INSIDE the wall.

## 3. C - how a clip is played on the player and how he is carried (kl2.exe)

Read again here, except the three rows marked (C): those are the reader's reading, taken over. Rows marked
**(2)** are new in the second version (read for it; the review had not read them); what is marked **(3)** came
in with the third (the second review's N1 and D1; read again by the writer of the third version); **(4)** = read
for the fourth version, from the dump of the first live start (`re/climb_crash.md`); **(5)** = read again for the
fix round after the crash's review (`re/climb_crash_review.md`).

| what | address | notes |
|---|---|---|
| `ZFFPlayer` vtable | 0xbb45f4 | +0x15c the frame 0x57fae0 (calls ZPlayer's 0x74efc0), +0x200 Play 0x4da1d0, +0x204 Play whole clip 0x6f6830, **+0x208 AlignTo 0x80fdc0**, +0x214 'moved by animation' 0x41a6b0, +0x2e4 'a channel ended' 0x7cc140, +0x2e8 the animation update 0x50ac80, +0x370 StartAction 0x542c00, +0x374 StopAction 0x8aef30, +0x384 CreateAction 0x839740, +0x388 current kind 0x76ea90, **+0x560 collision off 0x5d6200, +0x564 collision on 0x686600**, +0x5d8 movement kind 0x4cd950 = `[[player+0x6b4]+0x44]`, +0x630 'is the collision on' 0x700610 = byte `[player+0x7a5]`, +0x63c Move 0x6e6730, +0x664 movement by number 0x462420 = `[player+0x630+4*n]`, +0x668 0x6d4570, +0x680 the physics step 0x4d1310 |
| dispatcher | `[player+0x19c]`, vtable 0xba38d8 | +4 = the current action (one at a time). StartAction 0x869e10 has an int3 when one is current; ZFFPlayer's StartAction dereferences the action it is handed. **(2)** Its slot 1 0x672d00 stores the action at +4 BEFORE it calls the action's start (slot 2), and ends it (slot 6) when the start says no; slot 5 0x640430 (what StopAction 0x8aef30 jumps to) = slot 6 when there is one; slot 6 0x595b70 = +4 cleared, End (action slot 5), delete when action slot 9 agrees; slot 7 0x5d0260 'a channel ended' = the current action's slot 10, and slot 6 when that says yes |
| **who reports a replaced or ended channel (2)** | Play 0x4da1d0; the animation update 0x50ac80 | The 16 channels are at `[player+0x70] + 0x1c + 0x38 * i`: +0 clip, +4 the frame it is at, +8 from, +0xc to, +0x10 frames a second (speed x 25), +0x14 flags (low 3 bits the state: 1 / 3 play, 4 stopped; 0x8000 full-body = clip record +0x28 bit 0x10 clear; 0x200 aligned; 0x400 the clip moves bone 0x39; 0x1000 from Play's flag 0x20), +0x18 id. **Play with flag bit 0 stops every channel that plays and is of the new clip's body class (0x4da294 .. 0x4da306) and, after the new channel is set up, reports each: `player->vtable[0x2e4](id, ..)` (0x4da711 .. 0x4da751) = 0x7cc140 -> 0x8f0df0 -> dispatcher slot 7.** The update does the same for channels that reach their end (state := 4 at 0x50afca, reports at 0x50b5e8 .. 0x50b645). So a report reaches the action that is current WHILE ITS OWN START RUNS. The mini animation's slot 10 (0x42b7f0) answers byte +0x24, which its start clears around its Play: it survives, and from then on any report ends it (endWithClip = 1). The vault's and the jump-over's slot 10 is `mov al, 1` (0x553070): a vault started while a full-body channel plays is ended (its End runs: proxy, collision on) and deleted inside Play, and its start goes on with the freed object (0x6a2a62 writes +0xc, 0x6a2a8c .. read +8, +0x78) |
| **who moves him while a clip plays (2)** | 0x74efc0 (ZPlayer's frame), 0x6e6730 (Move), 0x5397e0 | The frame: byte `[player+0x7a4]` set -> 0x710da0 instead, no Move; byte `[player+0x430]` clear -> nothing; **(3)** bit 0x800 in the flags `[+0x3c]` of the node `[[[[player+4]+0x50]+0x60]+4]` (0x598460: the owner of what his node hangs on; 0x74efe6 .. 0x74eff8, the chain is read with no test) -> nothing; else **the animation update (vtable +0x2e8, 0x74f041)**, **(3)** the node's world transform read as the move's 'from' (vtable +0x578 = 0x5aa510 -> 0x857110, at 0x74f057), **THEN Move (vtable +0x63c, 0x74f077)**, then vtable +0x620 with the same four arguments (not read), and **(3)** at the end THE NODE IS WRITTEN from Move's result (vtable +0x60c = 0x693400 -> 0x8caf30 at 0x74f2df: it tells an object of `[[sysif+0xac]+0x18]` and sets the transform through the vtable +0x94 of the object 0x598460 gives; nothing in it touches the proxy) unless `[player+0xd50]` is not 0 (vtable +0x678 = 0x5380d0 at 0x74f2c5). Move asks vtable +0x668 = 0x6d4570: 'moved by animation' (0x41a6b0: the channel 0x760120 finds - the first that plays, is full-body and whose clip has record flag 0x40 - has flag 0x200, or its clip has record flag 8 clear and moves bone 0x39) and that channel has no flag 0x1000 -> the frame goes to movement number 1 (`[player+0x634]`, vtable +0x664; `ZMovementAnimation`, made with number 1 at 0x6a97fe; BaseMove is number 3 at +0x63c), **whatever the action's kind is**; else to the current movement `[player+0x6b4]`. ZMovementAnimation's update (vtable 0xba6e94, slot 17, 0x5397e0): its slot 35 0x536a20 first - **(3)** `player->vtable[0x5f8]` = 0x72d010 hands out the frame's root delta (`[player+0x20]` rotation, `[player+0x44 .. 0x4c]` translation, when vtable +0x214 says 'moved by animation') and the result = 'from' moved by that delta (0x536a8f .. 0x536b59; without a delta the result is 'from'): THAT is what makes the node follow the clip - then **the physics step (slot 33, 0x6d1ad0) only when vtable +0x630 says the collision is on (0x53986f .. 0x539879)**. The physics step: velocity `[player+0x808]` = the move x 60, vtable +0x680 = 0x4d1310 (the character proxy `[player+0x7d0]` is integrated, 0x87fb30 or 0x907440 -> Havok 0xa781f0; the body is put at the proxy's place), and **the result is the PROXY's place** (0xa768a0 at 0x6d1b73, plus the difference between the 'from' place and the node). BaseMove's update (0x7a43e0, read to 0x7a4ae5) calls the same step whenever he is not in cover (0x7a4a4d .. 0x7a4ae3), whatever the collision flag says. **So: collision off + an aligned clip = the node follows the clip and the proxy stays where it was; and in the frame the clip ends - the action's End runs inside the animation update, Move comes right after it in the same routine - the ordinary movement steps from the proxy again and the frame writes the node there: he is back where the proxy stayed**. With one of the frame's gates set the clip would play and he would not move at all: `klclimb.c` refuses a player behind any of the four **(3)** |
| **the proxy sync (2)** | 0x4af5b0 (thiscall, no argument, plain `ret`) | `if [player+0x7d0]: p = the node's world place (0x7b3020 walks [node+0x50] to the root) x 0.01 (0x408cf0); 0xa768b0([player+0x7d0], p)` = `[proxy+0x30]->0x9fc110(p, [proxy+0x5c] + [proxy+0x58])`: the proxy's phantom is put there (its place at +0xa0, its world `[+8]` asked for `[+0x6c]`, its shape `[+0x10]` called through vtable +0x18, the broad phase updated 0xa09de0). 31 call sites. **How the game's enders of an animated move call it** - always inside the End, i.e. inside the frame, at the moment the channel ends: the vault 0x82f796 then collision on 0x82f7a6; `ZFFActionJumpOver` 0x5c8fa3 then collision on (a tail jump); the mini cutscene's player act 0x447bf2 then collision on unless 0x684d00 answers yes (a byte of what he is attached to, `[player+0xd44]`); the fall's clip end 0x4815c0 the other way round (collision on 0x4815e5, the sync 0x481600); leave-cover 0x5fcc27; the placement 0x82cc40 at 0x82ccb3; the jump point 0x8f3fa0. **`ZFFActionMiniAnim`'s End 0x6fb600 only stops its channel: the game never carries a player with it WITH THE COLLISION OFF** (its two callers leave the collision on, so the proxy goes along through the physics step and nothing has to be put anywhere) |
| **the game's clock (2)** | `[[0xdd2640]+0x48]`, 1024 a second; 0x70da30 (ZSysInterface slot 49, called by the main loop at 0x87a9af) | `+0x4c` = the last value; `+0x48` = the raw clock (slot 50) + the offset `+0x54`; **while the pause byte `[[sys+0xac]+0xbc]` is set the offset is re-based instead, so the clock stands still**; `+0x50` = the frame's step in seconds (0 in a pause). 0x50ac80 advances every channel by that step. With the window not in front the main loop does not come here at all (0x87a963 .. 0x87a988: it pumps messages); which pauses set the byte and whether the clock jumps afterwards were not read |
| movement kinds (C) | constants in 0x51d240 .. | 2 Stand, 3 BaseMove, 5 Guide, 8 StandCover, 10 Roll, 11 Fall, 13 / 14 passengers, 15 MountedWeapon, 16 Rappel, 17 CloseCombat, 18 Prone, 19 Die. No climb |
| alive / down | 0x6a88f0 | bit 0x40000 of `[player+0x438]`, or `[[player+0x2940]+0x24]` in 2..13 except 10 |
| slot name -> id | 0x426890 -> 0x68a730 | a binary search over `[player+0x80]` -> {n, n x {text offset, id} sorted by name, texts}; 0xffff = none. Pure |
| slot id -> clip | 0x59d550 -> 0x5c2f60 | draws one number from the game's generator (`[0xdd2640]+0xb30`); 0 = the set has no clip |
| clip event frame | 0x4a75d0 | table = `[[0x1546f6c]+0x10] + [clip+0x10]`, `[clip+6]` entries {u32 id, u16 frame} |
| **AlignTo** | 0x80fdc0 `(rot[9], pos[3], float frames) -> al`, ret 0xc | takes the running full-body channel whose clip has record flag 0x40 (0x760120; none -> returns 0), sets the target time = the channel's frame + `frames` (clamped to its end), stores the difference between where the clip alone would be then and the wanted transform, sets channel flag 0x200. The frame update (0x50b0f6) blends the correction in linearly, rotation and all three axes; **when the target time has passed the correction stays whole (0x50b11a .. 0x50b131) and the clip's own root motion goes on** |
| a rotation | 0x857110 `(node; rot out, pos out)` | **row 0 = the world image of local z, row 1 of y, row 2 of x**. A clip's root runs along -z, so row 0 is where the BACK points. 0x55f8f0 (ecx = out[9], edx = in[3]; pure, 128 callers) makes such a matrix from the vector that becomes row 0: the vault passes the cover's normal, the NPC mover minus the direction of travel |
| collision off / on | 0x5d6200 / 0x686600 | 0x8c5270: `++[player+0x7b4]`, `[player+0x7a5] = 0`; 0x8b41c0: the count back (not below 0), `[player+0x7a5] = 1` at zero; 0x5d6200 also clears byte `[player+0x968]`; both set the body's Havok layer (0xc / 5, whatever the count is) through 0x40ed30 (writes the body's filter word +0x2c; when the world's byte +0x14fc is set, Havok 0xa01ee0 on `[world+0x14dc]`) on `[[world+0x11840+4*[player+0x27cc]]]`, world = `[[sysif+0xac]+0x52cc]`. The body table has 5,000 entries (0x1388), its count is at world+0x1183c, entries are only ever added (0x4adce0) |
| **StartMiniAnim** | 0x5ea340 `(u16 slot, x, alignObject, char endWithClip)`, ret 0x10 | writes through `[player+0xbe0]` and `[player+0xdbc]` (0x8b7410, 0x4c1a70), stops the current action, makes `ZFFActionMiniAnim` (kind 0x23, vtable 0xbb4f0c, 0x28 bytes from the pool 0x15151c0: +8 player, +0x18 slot, +0x1c alignObject, +0x20 the channel, +0x24 'reports count', +0x25 endWithClip) and starts it. A null action is handed on when the pool is empty (the game's own flaw) |
| its start | 0x76d1d0 | slot < 0 or no clip: `[player+0x2758] = 1`, the action is over at once, no fault. Else 0x74c040 (the weapon is lowered), `Play(clip, 1)` **with byte +0x24 cleared around it: its 'a channel ended' slot 0x42b7f0 ignores the reports that Play itself causes**; with an alignObject: AlignTo(its world transform, the frame of event 6 or the last). Slot 10 afterwards: with endWithClip any report ends the action; without, a report re-plays the clip's last frame at speed 0 (the pose is held), sets `[player+0x2758] = 1` and the action stays until somebody stops it |
| who calls it | 0x5022c0 from 0x60b5c2; 0x607950 | **Two callers** (the first version had one). (a) 0x5022c0, from 0x60b230 = players near a blast (the routine with the string `DisableTinitus`): `vtable +0x388 == 0` (no action) and **down state `[[player+0x2940]+0x24] == 0`**, then `StartMiniAnim([player+0x25b0], 0, 0, 1)`: a stagger on a standing or walking player, in every mode. (b) **(2)** 0x607950 = `ZMiniPlayerMoveTask@CPPScript` (vtable 0xbce7a4, slot 5; a mini cutscene's task, campaign): guard 0x4b3270, the current action stopped, `StartMiniAnim([task+0x62], task, [task+0x30], 0)` = the clip ALIGNED TO A SCENE OBJECT and held at its end, done when `[player+0x2758]` is set. So 'mini animation + AlignTo on the player' is a stock combination - with the collision ON. Mini animation + AlignTo + collision OFF is the hook's own. **(4) Correction: the stagger is a stock CALL, not a stock clip.** Its slot is the name `/Special_moves/Cover_From_Explosives` (resolved at `0x89cb31`), and none of the 21 stock `.ANM` files has that name (measured): the retail stagger's mini animation is over before it plays anything (`0x76d1f5`). The only stock maker of a mini animation that plays a clip is (b), with endWithClip = 0. Nothing in the retail game runs a mini animation to the natural end of its clip |
| **a clip's events (4)** | `0x4011e0`, `0x7f60e0`, `0x8b67d0`, `0x60c370`, `0x9290f0`, `0x7c6c80`, `0x8b76e0`, **`0x637060`** | Read after the first live start (`re/climb_crash.md` 2, 3). A channel's clip events ({u32 id, u16 frame, u16 text}, `[clip+6]` of them at `[[0x1546f6c]+0x10] + [clip+0x10]`) are handed out only when somebody subscribed the channel: `0x7f60e0(channel)` -> `0x4011e0` queues every event with the handler `0x60c370` (queue `[channel+0x34]`). **The mini animation's own start does (`0x76d22e`)**; Play alone does not, the vault's start does not, the NPC link mover does not. The animation update hands the due entries out per playing channel (`0x8b67d0` at `0x50af60`): `0x60c370` -> the owner's vtable +0x21c = for a player `0x9290f0` = the dispatcher's slot 4 `0x7c6c80` -> **the current action's slot 11** (`0x8b76e0` in a mini animation) -> its slot 13 = **`0x637060`, `ZFFActionGeneric`'s routine**: slot 12 (`0x721060`, 'the action's object' `[action+0xc]`, tested there), then a switch on the id (`0x637077`; ids 5 .. 53 by the byte table `0x637314` and the 13 targets `0x6372e0`; everything else, and 6, 7, 8, 12 .. 19, 22, 23, 36 .. 41, 43 .. 47, 52, to `0x6372d3` = `mov al, 1`). **Case 5 = `AlignTo` the place of `[action+0xc]` by the frame of event 6, the object used with no test (`0x6370e7`).** A generic action has that object from its constructor (`0x70ca90`); a mini animation's constructor writes 0 there (`0x6b2987`); `ZFFActionMiniAct` (0 too) returns at id 5 in its own slot 13 (`0x68ac6d`). A stopped channel hands nothing out (`0x63e600` -> `0x4ff500`). **(5)** Who subscribes: `0x7f60e0` has 23 call sites - 20 in slot 2 (the start) of 19 `ZFFAction*` classes, 3 in routines of animation states (`0x40a6b0`, `0x468640`, `0x6aa7b0`; taken for the NPCs': reasoned, not read); two other routines make a queue that does not reach an action (`0x425280`, handler `0x5edc40`: a message to the owner; `0x812a50`: one id, from the sound starter `0x409170`). **(5)** What the other cases need: 9, 10, 11, 21, 24 .. 35, 42 return when the action has no object (`0x7de320` is a pure map; slot 12 and `je` in `0x428d90`, `0x77ca60`, `0x70dc00`, `0x4fe5c0`, `0x87a8d0`); 20 takes an object from the player (`0x86a130`) and acts; 48 .. 51 and 53 act on his owner or the game data whatever the action is (`re/climb_crash.md` 3) |
| **what an action is handed while it runs (4)** | the dispatcher `0xba38d8`, eight slots | 1 start (action slot 2); 2 -> action slot 4 and 3 -> action slot 3 (both `mov al, 1` in a mini animation); **4 -> slot 11, a clip event**; 5 / 6 stop / end (action slot 5, then delete by slot 9 / 0); **7 -> slot 10, a channel ended**. No other way reaches a mini animation between its start and its end. **(5) Correction: 'a clip event' is the event of ANY subscribed channel of the player, not of the action's own channel alone** (this row said 'nothing else reaches a mini animation', meaning its own clip's events: wrong as written). The hand-out calls the handler on the channel's OWNER (`[channel+0x30]`, `0x8b68e1 .. 0x8b6915`); `0x60c370` passes the channel to the owner's vtable +0x21c (`0x60c3be`); slot 4 gives it to whatever action is current (`0x7c6c83 .. 0x7c6ca0`); slot 11 strips it to (clip, record) (`0x8b76e0`); the channel is never compared with `[action+0x20]`, and case 5 finds a channel by the EVENT's clip (`0x63709b` -> `0x5a6ec0`) before it uses the object. **So while a mini animation is current, an id-5 event of another clip that plays on him subscribed faults at kl2.exe+0x7e400 too.** What stands against it: only an action's start subscribes a player's channel and an action that starts ends the mini animation first (`0x869e1c`); the mini animation's own Play stops every playing channel of the clip's class and throws its queue away (`0x4da294 .. 0x4da2be`), so no full-body channel outlives the start; a channel of the other class plays on - and the build's 872 clips of that class carry only ids 9 and 10 of those the routine acts on (4.1, the check's rule; `klclimb.c` `klq_others`) |
| the mini cutscene (C) | `MiniCutsceneRout` (vtable 0xbcdf14), script text in field 0 | a script entry with a `Lynch` head and an `act` task (`anim` = a slot name, `startpos` = a pos object) makes `ZMiniPlayerActTask` for the player in gamedata slot 0: put on the pos object (0x82cc40), collision off, the slot played with its own root motion, the last frame held, input back at the script's end (0x8e8d00, 0x447bd0). 2,339 uses in the 21 stock levels, 755 scripts with a Lynch head, 38 Lynch acts with a start place - **all in campaign levels, none in an FA level**. 0x872f70 / 0x5f6df0 have an int3 when the player's slot byte `[player+0x91d]` is not 0 or 1. Stock template: L02 `ROOT\AI!Friendly!Script_Door` (a `PlayerAction` box whose list starts `MC_Door_Lynch`) |
| placing a player (C) | 0x82cc40 `(rot, pos, char resetMove, char force, char sendNet)`, ret 0x14 | the round start uses (1, 0, 1). 0x62a900 (klcrew_rt.c) is the ACTOR's routine. kljoin.c's debug jump is the only placement seen live |
| `ZFFActionJumpOver` | kind 0x2c, vtable 0xbb51bc, constructor 0x594fa0, start 0x8f0440 | new here: the constructor resolves ONE slot, `/Cover/Vaulting/Sprint_Vault_Right_0.5M`; the start is Play + AlignTo(frames) + collision off, after a test 0x523e40. No site was found that asks the factory for kind 0x2c: a cut action. Not used |

What follows for a hook (second version; **(3)** = third):
- The vault's own start is one call and brackets the collision AND the proxy itself, but its clip is the
  vault's, and **it survives its start only when no full-body channel of his plays at that moment** (state 1 or
  3, flag 0x8000): Play reports every such channel it replaces to the action that is already current, and the
  vault says yes to any report - End, delete, and the start goes on with the freed object. That was 'not
  established' in the first version; it is read now, and it can be TESTED before the call (16 flag words). Whether
  a standing or walking player has such a channel is what live check K6 shows (the refusal line counts them).
  **(3)** That count is of the MOMENT: the second review counted the clips of the vault's body class in this
  build's `.ANM` - `Movement/Soldier/Transitions` 174, `Walk` 124, `Run` 61, `Stand` 44, `Crouch` 58 and the cover
  idles - so a stop transition half a second after he stopped walking would be counted. One refusal is therefore
  no verdict: the file asks again four times a second while he stands and says 'REFUSED from this stand' only
  when the refusal has stood for a second (4.3, K6). (That the stock vault survives its start from cover, where
  the idle is of the same class, says those idles do not play in the 16 channels when it starts, or are stopped
  unreported: the second review's reasoning, not read.)
  Not read: 0x5abbb0 and 0x834ef0, which leave-cover calls inside the vault's start - so a report from inside
  leave-cover, BEFORE the start's own collision-off, cannot be ruled out; what it would leave behind (the
  collision off, no action) the file sees and gives back **(3)** (1.3, 4.3).
- The mini animation start has the guard against Play's reports and is called by the game on standing and
  walking players; it does not touch the collision. A hook adds, by the game's own routines: AlignTo with
  places of its own, collision off, **and the end** - which the game does inside the action's End and a hook
  cannot: by the time a tick sees the action gone, the game's own Move of that frame has stepped from the proxy.
  So the hook gives the proxy and the collision back a few frames BEFORE the clip's last one (the remaining
  frames then play as the game's own collision-on mini animation plays) and lets the action end by itself.
  An action that ends earlier leaves him where the proxy stayed: at the foot. That is the safe way to fail.
- What decides who moves him is the CHANNEL (aligned, full-body, root motion), not the action's kind: a mini
  animation (0x23) is treated as the vault (0x2b) is. The review's open question, answered by reading.
- None of it reaches an AI heister (`ZFFActor` has neither action).

## 4. What was built (offline; nothing loaded, nothing installed)

### 4.1 `tools/kl_fa_climb.py` - the level's half, a step on a finished build

    python tools\kl_fa_climb.py rule
    python tools\kl_fa_climb.py edges <folder>
    python tools\kl_fa_climb.py check <folder>
    python tools\kl_fa_climb.py apply <folder> <out folder> [--players-only] [--no-edges]

`apply` adds two things and takes nothing away (the wall piece `kl_escape` sank stays sunk):
1. **`.ANM`**: the three slot lists with their clips, in the sets of the level's `ZFFPlayer` bodies (Kane, Lynch)
   from Dead Men's `PlayerCharacter`, and in every NPC character set (a set whose `Fall_1m` default is an
   `_NPC` clip: Thug, Swat_02, Lynch_NPC, Kane_NPC, Civilian, Police, Army, Female) from Dead Men's `Police`.
   The machinery is `kl_anmjoin`'s (`_Out`, `_Source`, `_add_lists`: the code of every graft's join). Proved
   on the result before anything is written: reads back to the same bytes; `kl_anm.audit` clean; the base is a
   prefix (clips, names, data, bone / pose / slot tables) and no base list changed; each of the 30 added lists
   plays its Dead Men source (name, events + data, bone NAMES, condition flags); no bone or pose name added;
   only the `.ANM` member of the archive differs. `tools/kl_anm.py` was not changed (`kl_anm.py check`:
   `byte-identical: 41 of 41`).
   **(4) One difference from Dead Men's data, on purpose** (after the first live start, `re/climb_crash.md` 6):
   in the 7 clips the PLAYERS' lists name, the event with id 5 is written with id **105** (`EV_FOOT_DD`; `refoot`).
   Frame, event 6 and the clip's data stay. The proof compares those lists with 105 read as 5 and proves besides
   that exactly that entry differs and that no players' clip carries an id the game's generic action acts on
   (`GENERIC_ACTS`: 5, 9 .. 11, 20, 21, 24 .. 35, 42, 48 .. 51, 53). `check` FAILs a players' set that does
   (a build of the first form: `z_climb\M03` now gets `RESULT (kl_fa_climb): FAIL (2 FAIL, 1 NOTE)`), and `merge`
   refuses such a build instead of calling it complete. The five `*_NPC` clips keep 5 and 6; `Sprint_Low_No_Weapon`,
   a players' clip the NPC Low lists name too, has 105 there as well (an NPC cannot tell: the link mover asks for
   event 6 alone, `0x4a53aa`, and subscribes nothing).
   **(5) `check` has one rule more, on clips this step did NOT add** (the crash review's M1 / S2; section 3, 'what
   an action is handed'): no clip of the OTHER body class (record +0x28 bit 0x10 - what the mini animation's Play
   does not stop) may carry an event id at which the generic action's routine does not simply return for an action
   without an object, i.e. an id of `GENERIC_ACTS` outside `GENERIC_QUIET` (9, 10, 11, 21, 24 .. 35, 42: each read).
   Its line on a build: `PASS  the 872 clips of the other body class ...: of the event ids kl2 0x637060 acts on they
   carry only 9 (15 clips), 10 (69 clips), at which it returns when the action has no object ...`; else `FAIL  N of
   the M clips of the other body class ... id 5 in ...`. And a refused `apply` (a first-form build, a failed proof)
   now ends in one line, `kl_fa_climb: NOT applied: <why> - nothing was written`, exit 1, instead of a traceback.
2. **`KLJoin.ini`**: `[Climb]` sections beside kl_fa_bots' `[CrewHop]` (which stays byte for byte). A section is
   the top edge of an obstacle (`A`, `B`, `Normal`, `Floor`, `Depth`) where **Dead Men's own rule** (2.1) holds
   on the build's collision: the tool walks `LINES` (per map, a seed) every 25 units, tries the rule from 30 /
   47 / 65 off the face with `kl_map_escape.Ground`'s triangles, wants level floor and room to stand at the
   foot and no movable body there, and writes the stretches that pass (50 off both ends, 150 or more left).
   Every number written is measured. `check` walks every section of a folder's file again.
It also continues `steps.json` ('climb') and, because `kl_fa_bots_dyn.check` FAILs a build whose large blocks
differ from the ones its step recorded, the `big_before` of the copied `dyn.json` (the numbers before are
kept as `big_before_climb`; said in `climb.txt`).

### 4.2 `<work>\build\z_climb\M03` = `z_hop\M03` + the two additions

`F01_Main.zip` sha1 2c93ab683542c0c6629699265976975eb9ddd1b1 (200,889,112 bytes); `.ANM` 22,202,616 ->
22,343,864 (+141,248: 12 clips, slot ids **2505 High, 2506 Low, 2507 Medium** - the first version had High and
Medium the other way round; the build's own `climb.json` and the review's measurement say this - bones 156
(+0), poses 36 (+0)). The hook looks the id up by name, so only the expected log lines were wrong.

    line 'the yard's north wall, from the yard': (-3500, -625) -> (-1900, -625), 65 samples every 25, 63 pass
      refused at (-2575, -625), (-2550, -625): the floor at the foot is not level   (a street light's base)
    [Climb]    A=-3450 403.5 -625  B=-2650 403.5 -625  Normal=0 -1  Floor=200  Depth=49.5
    [Climb.2]  A=-2475 403.5 -625  B=-1950 403.5 -625  Normal=0 -1  Floor=200  Depth=49.5

Both are `High` (203.5 over the floor), stand-off 47; the player ends 44.4 past the face, on the wall, 5.1
short of its far edge. Beyond the wall the floor is the street (253.5 down) and, at x -3284 .. -2876, the
dumpster lids (122.5 down), two boxes (156.5, 189.5). The stretch is pieces `SO0101_M03_Wall_Low_8m_02` and
`_01`, between the sunk piece and where the level itself says 'not here'. Controls with the same rule
(measured, scratch `piece3.py` / `over3.py`):

| stretch | samples that pass | refused because |
|---|---|---|
| pieces `_02` / `_01` from the yard, x -3500 .. -1900 | 63 of 65 | a street light's base (2) |
| piece `_03` from the yard, x -4250 .. -3550 | 2 of 29 (x -3575, -3550) | the way 15 over the top is not clear: a hero-only collision object `ColiObj_OnlyHero_01` over the wall from x -3600 west, the wall `SO0202_M03_Wall_ENTER_05_01` further on |
| the sunk piece from the yard, x -1850 .. -1150 | 0 of 29 | no top within 70 in front (no wall) |
| pieces `_02` / `_01` from the STREET | 0 of 61 | the top is 253.5 over the feet: over 220 (35); a dumpster or a box stands at the foot (26) |

So the offline rule gives Dead Men's own picture: the wall is climbed from the yard between x -3590 and the
east end, not from the street, and the level's hero-only wall closes it in the west.

| check on `z_climb\M03` | last line |
|---|---|
| `kl_fa_climb.py check` | `RESULT (kl_fa_climb): PASS (0 FAIL, 1 NOTE)` (the note: the side file's sections, 1 `[CrewHop]`, 2 `[Climb]`) |
| `kl_fa_bots_dyn.py check` | `RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 3 NOTE)` - **the same 7 FAIL and 3 NOTE as the source `z_hop\M03` gets today** (the two outputs differ in one line, the `.ANM` size): 'money object(s) inside the loot window ... that a bot cannot take there', a rule the loot track added to `kl_fa_bots.check` this night. Nothing of this step. The drop link and `[CrewHop]` are as they were |
| `kl_impact.py` | `problems: 0 in 1 levels` |
| `kl_maps.py audit` | `RESULT: PASS (0 findings that must be 0, 0 known and accepted)` |
| `kl_map_escape.py van-check` | `0 fault(s)` |
| `kl_anm.py check` (the tool, untouched) | `byte-identical: 41 of 41` |

With the hook that is installed today the build is `z_hop\M03` with 141 KB more animation data: the installed
hook reads no `[Climb]` section and nothing in the game asks for the three slots. That is live check K0.

**(4) `z_climb\M03` IS OF THE FIRST FORM (its players' clips carry event id 5): the game faults 0.24 s into a
climb on it** (`re/climb_crash.md`). So is `z_climb2\M03` (the lead's of 09:22: the first form on `z_cover3\M03`).
The fourth version of the hook refuses both with a line; the third must not play them.

### 4.2b `<work>\build\z_climb3\M03` = `z_cover3\M03` + the two additions, in the new form (4)

`python tools\kl_fa_climb.py apply <work>\build\z_cover3\M03 <work>\build\z_climb3\M03` (the bank with the extra
cover boxes: the base the lead wants from now on). `F01_Main.zip` sha1 0698b298de54bcebd8bfb1972c0509df01f43983
(200,895,904 bytes); `.ANM` 22,202,616 -> 22,343,864 (12 clips, slot ids 2505 High, 2506 Low, 2507 Medium; bones
156, poses 36); the same two `[Climb]` sections as above (63 of 65 samples pass). Against `z_climb2\M03` (the first
form on the same base) the `.ANM` members differ in **7 dwords, each 5 -> 105**, and nothing else differs.

| check on `z_climb3\M03` | last line |
|---|---|
| `kl_fa_climb.py check` | `RESULT (kl_fa_climb): PASS (0 FAIL, 1 NOTE)`; new lines: `players' set Kane: none of the 7 clips of its three climb lists has an event id kl2 0x637060 acts on ...; the first alignment's frame is event 105, the second's event 6` (and Lynch); **(5)** and `the 872 clips of the other body class (record +0x28 bit 0x10: what the mini animation's Play does not stop): of the event ids kl2 0x637060 acts on they carry only 9 (15 clips), 10 (69 clips), at which it returns when the action has no object ...` |
| `kl_fa_bots_dyn.py check` | `RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 1 NOTE)` - the 7 FAIL of `z_cover3\M03` itself (the civilian loot-window rule; the two outputs differ in one line, the `.ANM` size). Not this step's, not fixed |
| `kl_impact.py` | `problems: 0 in 1 levels` |
| `kl_maps.py audit` | `RESULT: PASS (0 findings that must be 0, 0 known and accepted)` |
| `kl_map_escape.py van-check` | `0 fault(s)` |
| `kl_anm.py check` (the tool, untouched) | `byte-identical: 41 of 41` |

**(5)** The fix round changed the tool's `check` and `main`, not `merge`: `apply` with the tool as it is now, into a
scratch folder, gives the same `F01_Main.zip` (sha1 0698b298..) and the same `KLJoin.ini`, so `z_climb3\M03` was
NOT rebuilt (only its own record of the check, `climb.txt` / `climb.json`, lacks the new line). All six checks of
the table were run again after the round, with these last lines.

### 4.3 `klhook/klclimb.c` - the hook's half (wired by the lead, commit 9c8077d; fourth version below)

**(5) The fix round of the fourth version** (after `re/climb_crash_review.md`; the table is 6.5). What changed in
the file, and nothing else:
- `klq_others(player, own channel, spare class)` - his channels other than the climb's that play (state 1 or 3) and
  have an event queue (`[channel+0x34]` not 0), and the first of them whose clip has an event the game's routine
  sends to its case 5 (`klq_clip5`, by the game's own tables through the new `klq_ev_to`) or whose events cannot be
  read. Asked three times: **before the start**, for the channels the start's Play would leave playing (those of
  the other body class than the clip's) - one with such a clip: `edge N NOT climbed: channel C of his plays the clip
  X with an event queue, and that clip has event id 5 at frame F, which the game's event routine 0x637060 sends to
  its case 5: ... NOTHING WAS STARTED (such a channel runs out by itself: step away and come back)`; **right after
  the start**, for all his other channels as they are then - the action is stopped in the tick of its start (`...
  STOPPED in the tick of its start, before any event could be handed out`); **every frame of the climb** - `edge N:
  frame F: channel C of his plays the clip ...: the climb is called off`, then stopped and given back like any
  call-off (`CALLED OFF by this file (another channel of his plays a clip with an event for the game's case 5)`).
  With `Log=2` a change of the set during a climb is a line of its own (`frame F: his other channels that play with
  an event queue are now MMMM (n; they were MMMM) ...`): by the reading none can come, so that line means the
  reading is short of something. The queue is not walked - a queue of sound events counts too - so the rule can
  refuse more than it must; and it refuses case 5 only (the build's check has the other ids).
- `klq_code` also compares the WAY to the event routine (S3): `[0xbb45f4 + 0x21c]` = `0x9290f0`, `[0xba38d8 + 0x10]`
  = `0x7c6c80`, `[0xbb4f0c + 0x2c]` = `0x8b76e0`, and that id 5 goes to `0x637093`.
- The `frame 6.x: aligned to P2 (...) in N frames` line goes on `; his node is at (x, y, z) now = (dx, dy, dz) from
  P1 (x, y, z)` (S1: read before the second alignment is set). The `started` line has `, movement kind K` after
  `under 150` and ends `; N other channel(s) of his play with an event queue (MMMM)`; the dry run's `WOULD climb`
  line has `, N channel(s) of any class with an event queue (MMMM)`.
Calls: none added (reads only; the stops are the `0x8aef30` the file made before). Built from the tree
(`klhook\build_auto.bat G:\kl_scratch\f3\test`, `klhook\build.bat G:\kl_scratch\f3\ship`): no warning from this
file, `cl /Zs /W4` names no line of it. Its off-game test: `SIM: PASS (0 failed)`, 101 expectations (the 84 of
before and 17 new, X and Y); the control - the fourth version as it was before the round - starts the climb beside
a subscribed channel whose clip has event 5 and faults in the model when that event comes due, at climb frame
23 (`re/climb_crash.md` 7).

**(4) Fourth version, after the first live start** (`re/climb_crash.md`; the file's own section 0). What changed,
and nothing else: `KLQ_EV_FOOT` = 105 is the event whose frame the first alignment takes (the third version read
id 5); `klq_ev_acts(id)` asks the game's own switch (`0x637314`, `0x6372e0`) whether its event routine acts on an
id; `klq_code` also compares that routine (`0x637060`, the switch `0x637077` / `0x637085`, the 'nothing' target
`0x6372d3`, slot 12 `0x721060`, the mini animation's vtable entries 12 / 13) and wants 5 to act and 105 and 6 not
to; `klq_clip` returns 0 for a clip whose event table cannot be read and reports the first event the game would act
on; `klq_climb` looks at the clip `0x59d550` gives BEFORE the start (no clip, unreadable events, or such an event:
`NOT climbed: ...`, nothing started - a level of the first form gets `the clip ... has event id 5 at frame 6 ...
NOTHING WAS STARTED`) and at the channel's own clip after it (such an event: stopped in the same tick); the
`started` line says `speed S after D ms at the foot under 150` and `events 105 (the foot) at 6 and 6 (the top) at
20, none the game acts on`. Calls added: `0x59d550` once per try in `Mode=climb` (it was the vault's only).
Built from the tree (`klhook\build_auto.bat G:\kl_scratch\f3\test`, `klhook\build.bat G:\kl_scratch\f3\ship`): no
warning from this file. Its off-game test (the third version's, with the clip's events and a model of `0x637060`
added): `SIM: PASS`, 84 expectations; the control - the THIRD version with the first build's clip - faults in the
model at clip frame 6.25 (`re/climb_crash.md` 7).

Third version (after two reviews; what the third changed is marked **(3)**). Its top comment is the spec. In
short: Arcade only, a level that is not
stock, the game's thread; off unless `[Climb] Enable=1`; `Dry=1` logs and calls nothing. Twenty times a second
(**(5)** at ticks 50 ms or more apart: 62 ms, 16 a second, in the first live run by the crash review's reckoning -
a tick count that steps by 15.6 ms; `Dwell=400` was 437 ms there)
the local human's node place is held against the `[Climb]` edges; AT THE FOOT (15 .. 70 from the face - Dead
Men's last probe; the first version had 75 -, between A and B, his height within 40 of `Floor`) for `Dwell` ms
(400), slower than `Speed` (150), looking at the face within `Angle` (60), with `Key` down if one is set, and
`klq_refuse` lets him pass: no action, **down state 0** (the game's own test at 0x5022c0; the first version let
1, 10 and 14.. pass), **not in cover** (`[player+0x2954]`, bit 0x80 of `[player+0x818]`: exactly what 0x40f840
/ 0x6e2740 / 0x780b80 come to), standing or walking (movement kind 2 / 3), an ordinary frame (`[player+0x7a4]`
clear, `[player+0x430]` set, **(3)** bit 0x800 clear on the node `[[[node+0x50]+0x60]+4]` and `[player+0xd50]`
0: the frame's two other gates, 3 - behind either the clip would play and he would not move), nobody has his
collision off, and every pointer the calls go through reads.
- `Mode=climb`: the class by Dead Men's table from **the top over his feet** (the first version took it from
  `Floor=`); class Low is refused unless `Low=1` (its clip ends at the edge, 2.3); the slot name looked up in
  the level's own table (read); `StartMiniAnim(slot, 0, 0, 1)`; if the
  game kept the action and its channel is the one the game would align (0x760120 done by reads): Dead Men's
  two alignments by `AlignTo` - P1 (the face's foot, stand-off back, his own height) at the frame of event 5,
  then P2 = P1 raised by (top - his feet) at the frame of event 6 - and only when the game has taken the first
  alignment, collision off.
  `Align=1` is one alignment at the last frame to the same end place, **(3) 10 over the top** (`KLQ_LIFT`): aimed
  at the top itself he would cross the face 1.8 .. 7.6 under it, with the 10 he crosses it 0.8 .. 6.6 over it
  and comes down the 10 when the clip is over (measured, 2.3; the second review's N3). **(3)** `Align=1` is
  refused for class Low (`Align=1 is not for that class`): that clip needs the first of the two alignments (2.3).
  No channel to align: the action is stopped, nothing else was changed. The second alignment cannot be set:
  called off - stopped and given back by the rule of the end below.
  **The end (review M1).** From `HandFrames` (**(3)** 5 by default, it was 3; 1 .. 5) frames before the clip's
  last one on, as soon as his node is 10 beyond the face - and in any case in the last tick before the end (one
  and a half ticks' worth, at least one frame), never before the top alignment - the HAND-OVER, in the game's
  own order: `0x4af5b0` (the proxy is put at the node), then `0x686600` (collision on). By the table of 2.3 that
  is **frame 46 for High (15 beyond the face, 24.5 over the top: over the wall, 34 from its far edge)**, about
  frame 35 for Medium, the last tick for Low. It is the '10 beyond the face' test, not `HandFrames`, that keeps a
  hand-over from coming before he is over the obstacle (High passes it from frame 45.1, Medium from 34.6), so
  the larger number costs nothing; it leaves 200 ms instead of 125: in the off-game test one long frame begun
  just before the hand-over fails from 240 ms on with 5 and from 130 ms on with 3 (the second review's N2 and its
  numbers, reproduced). The clip's last frames (High: 29 more forward) play under the proxy as the game's own
  collision-on mini animation plays, and the action ends with its clip. An action that ends before the
  hand-over (another action, a death, another channel's end, one frame longer than the margin) gets the same two
  calls as soon as it is seen gone; the game has him back at the foot by then.
  **(3) Never into the obstacle (the second review's N4).** Whenever the two calls are due and his node is
  between the obstacle's faces (less than 15 clear of either: -(Depth + 15) < distance < 15) and more than 3
  under its top, the proxy is NOT put at the node: the collision alone is switched on and the game's next frame
  steps him from where the proxy stayed (the foot). It is said: `... - the proxy is NOT put at the node: node
  (...) is N beyond the face of a D thick obstacle and U under its top = INSIDE it; the proxy stays at (...)`.
  The case that needs it: a climb called off after the first alignment only (one long frame between events 5
  and 6) - its node is 28 under the top and beyond the face from frame 43 on (2.3), and the second version put
  the proxy there (the off-game control: `RESULT ... INSIDE THE OBSTACLE`). The heights of this test are the
  node's own (the top = his node's height at the start + the rise), so it also holds when his node is not at
  his feet.
  **Before each of those calls (review S1)** `klq_carry_refuse` reads again what they go through: the object is
  one of the game's 28 players, the node chain, the proxy's phantom (its place writable, its world's `+0x6c`,
  its shape's vtable entry), the physics world, his body number against the table's count, the body's filter
  word writable, the Havok world when the world's byte asks for it. Fails: nothing is called, it is said,
  asked again every frame for 3 s, then given up with a line that names the count.
  **The time-out (review S2)** is counted on the game's own clock (3): 1.5 s of game time after the clip's
  length the action is stopped and given back (the same rule). A pause that sets the game's pause byte holds that clock and
  the clip alike (that the pause menu is one: ASSUMED, K7 b). With the window out of the front no tick of the
  game's thread comes at all; what the clock does on the return was not read (if it jumps, the clip jumps with
  it). (If the clock cannot be read: the wall clock less every gap of over 250 ms between two game ticks.)
  **After the end** the place is logged at +0.5 s and +1 s and a `RESULT` line at +2 s says UP / ACROSS /
  INSIDE THE OBSTACLE / BACK AT THE FOOT / ELSEWHERE from the node's place against the edge (review, K2).
  **(3)** The `over` line now ends `..., his collision count N` (0 after a climb that gave everything back).
- `Mode=vault` (or `Fallback=1`): one call of `0x619790` with a cover record of the file's own and the end
  place given (the middle of the top). **Before it (review S4)**: what leave-cover and the start write through
  (`[player+0x2810]`, `+0x2948`, `+0xccc`, the session, `[player+0x2f70] == -1`, the world's `+0x14ec`), both
  vault slots have a clip (numbers of the game's generator are drawn: N5 of the review), and **no channel
  of his plays that the vault's Play would replace and report** - else a refusal with the count, not a call.
  **(3) That refusal is of the moment (the second review's D2)** and no longer ends the stay: it is said once
  (`edge N NOT vaulted yet: K channel(s) of his play that the vault's own Play would replace and report (the
  first: channel C, clip X at frame F of T): ... - asked again four times a second while he stands here`) and
  asked again every 250 ms while he stands (not every tick: each try draws from the game's generator). When it
  has stood for a second: `edge N: the vault is REFUSED from this stand: T tries in M ms of standing, the last:
  ...` - only THAT line is a verdict. If a later try passes, the `VAULT started` line is followed by `(the
  vault had been refused T time(s) in the M ms before: the channels that played then are over)`. Stepping away
  or a broken stand (moving, turning away, the key let go) starts the count anew. With `Fallback=1` the start
  that found no climb clip is called once per stay; the tries after it go straight to the vault.
  Afterwards the action must be the vault's and this player's. **(3) If it is not, his collision count and
  flag are read (the second review's D1)**; `klq_refuse` had them at 0 and 1 in the same tick. A start that
  left the collision off with no action to switch it on (1.3: an End before the start's own collision-off) is
  said - `edge N: the vault's start LEFT HIS COLLISION SWITCHED OFF (count 1, flag 0; ...): this file gives it
  back` - and gets the two calls of the end at once (`after a vault start that kept no action - the proxy put at
  the node ... collision on (count 1 -> 0)`), or, if they cannot be made, every frame for 3 s as after a climb;
  a `RESULT` line follows 2 s later. The `NOT climbed: ... the vault did not outlive its own start` line now
  ends with the count and the flag as they were right after the start. An empty action pool (`said NO`) has
  stopped and started nothing (read) and is only said. Its time-out is on the game's clock too.
  The channel count is printed in three more places so that a dry run can say in advance what the vault would
  meet: in the `WOULD climb` / `WOULD vault` line (`K full-body channel(s) of his play NOW (after the dwell)`),
  every second in the `Log=2` line, and in the `at the foot` line - where it is the count `as he arrives`,
  still walking, and NOT the vault's answer.
Dead Men asks for the USE tap. The hook's default is no key - standing at the foot, facing the wall, for 0.4 s
is the request (a scripted run cannot press a key that `GetAsyncKeyState` sees). **For the owner's play set
`Key=0x45`** (N4 of the review: an unwanted climb ends on a wall in front of the police). He is turned square
to the wall; Dead Men keeps his heading (a difference by choice: the top comment, section 3).
Calls: `0x5ea340`, `0x80fdc0`, `0x5d6200`, `0x4af5b0`, `0x686600`, `0x55f8f0` (and `0x8aef30` on a call-off or
a time-out); vault mode `0x619790`, `0x59d550`. Each is known by its first 14 bytes and, where it has one, its
vtable entry before the first call (`0x8aef30`, 13 bytes long, by its vtable entry alone); the eight byte rows
and the four entries were compared with the exe again for this version (all the same). No data write of the
hook's own, no code byte.

**It compiles and links** (new; the first version had only passed `cl /Zs`): a copy of `klhook\` (source files
only, no DLL) in `G:\kl_scratch\climb_fix_1011\klhook\`, the three lines below added to THAT copy's `klhook.c`
(the diff against the repo's is those three lines), built with that copy's own `build.bat` (SHIP) and
`build_auto.bat` (TEST): both end `built ...\dinput8.dll`, no warning (`/W3`, the scripts' level); `cl /Zs
/W4` on the same copy gives no line that names `klclimb.c`. Last built 2026-10-11 07:55 on the tree at commit
aa48c72 (every other file of the copy byte-equal to the repo's; `klclimb.c` sha1 ae3b1637..60074e): SHIP
406,016 bytes, sha1 1a0e2592..fc741d; TEST 454,144 bytes, sha1 079d0d34..284dfa. The DLLs stay in that
folder's `out\` / `out_auto\`; nothing was copied anywhere. The first link FAILED: `unresolved external symbol __imp__GetAsyncKeyState@4` -
the hook does not link user32 (klnudge.c looks its one user32 function up at run time). The file does the same
now, and with `Key=` set and no such function nobody climbs.
**(3) The third version was built the same way** in a fresh scratch copy, `G:\kl_scratch\climb_fix3_1011\klhook\`
(the repo's `klhook\` files as they stood on 2026-10-11 08:53 at HEAD c99d16c - another track's uncommitted
`klauto.c` among them, which only the TEST build compiles - and `klhook.c` + the three lines; every other file
byte-equal to the working tree's): `build.bat` ends `built ...\out\dinput8.dll (SHIP)`, `build_auto.bat` ends
`built ...\out_auto\dinput8.dll (TEST)`, both exit 0 with no `warning` or `error` line; `cl /Zs /W4`, SHIP and
TEST: exit 0, no line that names `klclimb.c`. `klclimb.c` sha1 5eeedfab..45fdca6 (1,062 lines); SHIP 411,648
bytes, sha1 7ce944ef..a57585; TEST 462,336 bytes, sha1 4ad2d9cd..760a15 (a DLL's sha1 changes with every build:
the hook carries its build time). Proofs of compiling only: the DLLs stay there, nothing was copied anywhere,
and the hook to install is built by the lead from the tree after wiring.

**An off-game test of its state machine** (scratch only: `G:\kl_scratch\climb_fix_1011\sim\sim.c`, `sim.exe`,
output `sim_out.txt`; nothing of it is in the repo). `klclimb.c` is compiled unchanged against stubs of the
hook's helpers; the nine game routines are C stubs behind jump thunks in a fake image; a fake player (node,
channels, dispatcher, proxy, body table, clock, slot table, the High clip's record with its measured root) and
a MODEL of the frame as section 3 reads it: the node follows the aligned clip, the proxy moves only by
`0x4af5b0` or - collision on - with the node, and in the frame the action ends the node is put where the proxy
is. `SIM: PASS`, 32 expectations of 32:
A the climb at 60 frames a second (started, two alignments, hand-over at frame 48.3 - the second version's
`HandFrames=3` - with the proxy coming from
where he had stood, `RESULT ... UP`, count 0, calls 1 / 2 / 1 off / 1 sync / 1 on / no stop); B the same at 20
and at 10 frames a second; C another action ends it at frame 30 (`BEFORE the hand-over`, given back, `BACK AT
THE FOOT`, count 0); D a 5 s pause in mid clip (not stopped; UP afterwards); E no game tick for 5 s; F the
channel stands while the game's clock runs (`STOPPED by this file` at 3,585 ms of game time, given back); G the
physics world unreadable at the hand-over (nothing called; given back when it reads again; `GIVEN UP after 3 s`
when it never does); H `Dry=1` (no routine called), cover, down state 1, an action running, the player object
no longer registered (each: nothing called); I `Mode=vault` with a full-body channel playing (refused with the
count, the start not called) and with none (started, the hook switches nothing, UP); J `Align=1`, and a step
from before event 5 past event 6 (`CALLED OFF`, given back); **K the control: the clip's last six frames pass
in one step, so the sync and the collision switch are called only after the end - what the review proposed:
both are called, and he is `BACK AT THE FOOT`.** It is a test of the file against the reading, not against the
game (section 9).
**(3) The third version's test** (`G:\kl_scratch\climb_fix3_1011\sim\sim.c`, `sim.exe`, `sim_out.txt`; scratch
only). A - K are the second version's 32 expectations, unchanged in what they ask (A's hand-over now comes at
frame 46.25); the fake player got the chain the frame's third gate reads, because the file now tests it, and
the model no longer lifts a proxy that was put inside the wall onto its top. New, one group per point of the
second review, `SIM: PASS (0 failed)`, **66 expectations of 66**:
L (D1) a vault start that says yes, keeps no action and leaves the count at 1: said, given back at once (one
sync, one collision-on, count 0, flag on), `RESULT ... BACK AT THE FOOT`, the start called once; the same with
the physics world unreadable (nothing called, owed, given back when it reads again; `GIVEN UP after 3 s` when
it never does); a start whose End gave the collision back itself, and an empty pool (said, nothing called);
M (D2) a full-body channel plays when the vault is first tried (`NOT vaulted yet` with the count and the
channel, no verdict, no start) and ends half a second later (the vault starts in the same stay, `had been
refused`, UP); the channel plays on (one `NOT vaulted yet`, `REFUSED from this stand: 5 tries in 1024 ms`, 10
draws of the generator in 2.5 s of refusals, no start); step away and back (said again); `Dry=1` (the count in
the `WOULD vault` line, no call); `Fallback=1` without a climb clip (the mini start called ONCE, then the vault);
N (N2) the default hand-over at frame 46.25, node (x, 428.0, -608.1); one long frame begun just before the
hand-over: first failing length 240 ms with 5, 130 ms with 3;
O (N3) `Align=1`: beyond the face his node is never lower than +3.4 to the top, +6.1 at the hand-over, the proxy
put at the node, UP; a Low edge with `Align=1` (refused, nothing called);
P (N4) the call-off with his node 13 beyond the face and 31.5 under the top: `the proxy is NOT put at the
node`, no sync, collision on, count 0, the proxy still at the foot, `RESULT ... BACK AT THE FOOT`; a call-off
with his node still before the face: the proxy IS put at the node, as before;
Q (N1) `[player+0xd50]` set, bit 0x800 set, the chain unreadable: each refused, nothing called;
R two hook ticks a frame: one hand-over, UP.
**The controls** (`sim_old.exe` = the same test source compiled against the SECOND version, sha1 ae3b1637..):
in L's case that file says `did not outlive its own start` and leaves the count at 1 and the flag at 0; in P's
case it puts the proxy at (x, 372, -612) and its `RESULT` is `INSIDE THE OBSTACLE`. `CONTROLS: both defects
shown by the second version`.
Limits of the model, besides the one above: it has no collision geometry, so what a proxy does against the
wall is not in it; in L the start's own clip is not played on after the action is gone.

The three lines for `klhook.c` (in the repo since commit 9c8077d: the file is wired, off unless `[Climb] Enable=1`):

    #include "klclimb.c"        after  #include "klhop.c"
    klq_tick(game_thread);      in klh_tick, after  klv_tick(game_thread);
    klq_init();                 in the init list, after  klv_init();

## 5. The ranked plan

| | what | the player sees | the AI heisters | risks | first to be seen live |
|---|---|---|---|---|---|
| **(iii)** recommended | Dead Men's clips in the level's `.ANM` (4.1) + `klclimb.c` `Mode=climb` at the edges of 4.2. The sunk piece stays | at the wall pieces that stand: he pulls himself up in 2.08 s with Dead Men's own animation and stands on the wall; a step on and he drops to the street or a dumpster lid. Any place along 13 m of wall. From the street nothing (253 high), as in Dead Men | nothing new: the drop link through the sunk piece, as today | four game routines in a combination the game does not make itself (mini animation + AlignTo is stock, with the collision ON; the collision OFF with it is the hook's); **the end is the hook's and is timed**: the hand-over must come in the last frames before the clip's end - one frame of the game longer than the margin (200 ms), or anything that ends the action early (a reload, any channel of his that ends: weapon handling, faces - the likeliest way K2 fails), and he is back at the foot (a clean failure; the `RESULT` line says which); what Havok does with him after the hand-over, 24.5 over the wall top, could not be read; the hook owns one collision count for 2 s (guards: 4.3); no input is taken away (K4); the facing test's sign and the node's height are read, not seen (K1 shows both); a parked car at the wall is passed through; Arcade only | K0, K1, K2 |
| (ii) fall-back | the same file, `Mode=vault` / `Fallback=1`: the game's own vault action to a given end place | a 1.16 s vault pose that carries him 2 m up onto the wall: a hop through the air, not a climb | nothing | one call; collision and proxy are the game's own End. The action is freed inside its own start when a full-body channel of his plays (read, section 3): the file counts those first and REFUSES, so the known way to a use after free is closed; the count is of the moment, so it asks again while he stands and gives a verdict only after a second (K6) - it may still refuse from every stand. Not read: 0x5abbb0 / 0x834ef0 inside leave-cover; if one of them ends the vault before its start's own collision-off, the start goes on with a freed object (the game's flaw, not closed) and leaves the collision off - that the file sees and gives back | K6, only if K2 fails, in a run somebody reads afterwards |
| (i) level data only | (a) a `CoverBoxM` + `PlayerCoverModifier` `ON_VAULT_ON` at a standing piece; (b) a `MiniCutsceneRout` with a `Lynch` act on the merged clip, started by a `PlayerAction` | (a) he crouches at a 2 m wall and slides through it; (b) the real clip, from ONE fixed spot per place, no alignment | (a), (b) nothing. Their own climb is level data (below) | (a) the cover search may not take a low box at a high wall; (b) a Lynch head has never run in an FA level, acts on gamedata slot 0, int3 when the slot byte is off; both need entities added to a finished build (slot ids move) | not built |
| (iv) today | the piece `SO0101_M03_Wall_Low_8m_05` sunk, its collision cut | a gap in the wall, a 50 cm step down | the drop link (seen live) | none new | - |

**Recommendation.** Wire `klclimb.c`, build the hook, run K0 - K3 on `z_climb\M03`. (iv) stays in the build
whatever happens: the climb is offered beside the gap, not instead of it. Only when the owner has climbed and
likes it is the question 'close the gap again?' worth asking - and then the AI needs its own way first (below),
because the drop link runs through the gap.

**For the installed game the honest answer is (iv) for now**: nothing of (i) - (iii) has run.

### 5.1 The AI heisters' climb (level data alone; clips done, mesh NOT done)

`kl2.exe` plays it by itself once the data is there (1.4): the three slots in the NPC sets (in `z_climb\M03`
already) and, per lane, the campaign's chain (2.2) in the navigation mesh - a wall-top polygon as a one-polygon
area with two waypoints, link kind 1 yard -> wall top (cost 184), kind 2 wall top -> lid (114), kind 2 lid ->
street (117); polygon byte +1 raised (re/bots_bank.md 1). Not done because it needs new polygons and areas in
the mesh (kl_fa_bots.add_drop only adds waypoints and links to polygons that exist; `kl_pf4.DD_LINK_KINDS` is
`(2,)`), in files of other tracks. ASSUMED: Dog Days runs a kind-1 link (identical code, no stock level has
one). Not read: what an actor does at a kind-1 link when its set has no clip - which is why all eight NPC sets
got the slots.

### 5.2 If the sunk piece is ever to stand again

- On a finished build the cut cannot be undone from the build: `kl_escape.cut_collision` replaced the piece's
  static placement by a filler. The change for the lead is one line of `tools/kl_escape.py`: the entry of
  `OPEN` becomes `'M03_FA_A': []` (`open_wall` then moves nothing, `place_entities` gets no REF, `cut_collision`
  returns at once; `money_reach` and `board_box` run as before) - and the map is built again from the graft.
- Not before the AI has 5.1: its drop link (waypoints (-1704, 220, -766) -> (-1700, 150, -534)) crosses the
  piece, and the link mover makes no collision query (read; that an actor on a link is not held by level
  collision is ASSUMED) - the bots would be carried through a standing wall.
- Level data for (i)(a), should it be wanted all the same: one `ZBoxPrimitive` named `CoverBoxM_Climb_01` (a copy
  of the room's `NoCoverBox#01` without its controller), unrotated, bottom ON the yard floor, the wall's own
  thickness, e.g. centre (-2300, 250, -600), half sizes (200, 50, 25); controller `PlayerCoverModifier` with
  fields 0..10 `OFF`, 11 `ON_VAULT_ON` (side 3 = -z = the yard, its top), 12..95 `AUTO` - the row of stock L11
  `L11_Inside_Luggage_Handling_C\_coverBoxes!CoverBoxM#30`. Not built.

## 6. Corrections

### 6.1 First version: the readers' notes

- Part B: 'every bone the Up clips move is among table entries 0 .. 60'. Measured again: one of the 57 is entry
  64, `head attacher`. All 41 stock tables agree on entries 0 .. 60; the 20 Dead Men tables agree among
  themselves on 0 .. 66 and so do the 21 Dog Days tables, and entry 64 is `head attacher` in all 41. The
  conclusion stands for a better reason: a merged clip names its bones by the BUILD's own table (kl_anmjoin
  renumbers by name) and every body of a build is bound to that table; `check` proves that every bone a climb
  clip moves is moved by other clips of the file too.
- Part B took the wall as 184 high (the navigation mesh's 220); the collision floor is 200, so the climb is
  203.5 - still `High`, with 16.5 to spare. Confirmed with Dead Men's rule on the collision (4.2).
- Part A: 'the cut cannot be undone on a finished build' - true from the build alone, and not needed: the plan
  climbs the pieces that still stand.
- Part C ranked the forced vault first for a hook. Its open question (does the action survive its own start
  outside cover) does not arise for the mini animation start, which has the guard and is called by the game
  from walking players. So the mini animation is the main form here and the vault the fall-back.
- Part C described a `klclimb.c` with boxes and `To=` places; the file written here marks EDGES and applies
  Dead Men's table, so one section serves a whole stretch of wall and every class.

### 6.2 Second version: what the review found, what was done, and where the review itself is corrected

| review | finding | what was done (evidence: the address read, or the line of the build) |
|---|---|---|
| **M1** must | the climb ended with the collision on but the proxy not put at the node (`0x4af5b0`) | Fixed, **and not the way the review proposed.** Read: the enders call it inside the action's End, sync first, collision on second (0x82f796 / 0x82f7a6, 0x5c8fa3, 0x447bf2; the fall 0x4815e5 / 0x481600 the other way round). The review's 'immediately before `0x686600` in both end paths of `klq_follow`' would run one frame late: the action's End runs inside the animation update, and Move follows it in the same routine 0x74efc0 (0x74f041, 0x74f077); with the mini animation gone 'moved by animation' is false (its channel is in state 4), the ordinary movement's physics step makes its result from the proxy (0x6d1b73) - he is back at the foot before any tick sees the action gone. So: the hand-over `HandFrames` before the clip's last frame, sync then on; the same two calls on every other end path too |
| the review, 1.2 | 'whether the proxy is carried along while the collision is off was not read' | Read: it is NOT. ZMovementAnimation's update 0x5397e0 runs the physics step only when vtable +0x630 (byte `[player+0x7a5]`) says the collision is on (0x53986f). The choice of that movement is by channel (0x6d4570 / 0x41a6b0), not by action kind: the review's second open question |
| the review, 1.2 | '`ZFFActionMiniAnim`'s End only stops the channel: the game never carries a player with it' | Half right. A second caller exists, 0x607950 (`ZMiniPlayerMoveTask`): StartMiniAnim with an align object, collision ON. The game does carry a player with it - never with the collision off |
| **S1** should | the end path did not re-test what the start path tested | `klq_carry_refuse` before every call of `0x4af5b0` / `0x686600` / `0x5d6200`: one function for the start and the end. Fails: nothing is called, said, asked again for 3 s |
| **S2** should | the time-out was wall clock | The game's clock `[[0xdd2640]+0x48]` (0x70da30: held while the pause byte is set; the channels advance by its step, 0x50ac80 head) |
| **S3** should | cover not tested; the down-state test laxer than the game's | `[player+0x2954]` or bit 0x80 of `[player+0x818]` refuses (read: 0x40f840 = `[+0x2954]` or 0x6e2740 or 0x780b80, which come to exactly those two); down state must be 0 (0x5022d7) |
| **S4** should | `Mode=vault` / `Fallback=1` could end in a use after free | 'Who reports a replaced channel' read (3): Play, before it returns, to the current action. The file counts the channels the vault's Play would replace (`klq_replaced`) and refuses if there is one; it also tests what leave-cover writes through. The top comment no longer says 'every pointer' for the vault: 0x5abbb0 and 0x834ef0 were not read |
| note | class from `Floor=`, rise from the feet | the class is taken from the rise (top over his feet) |
| note | `idx > 0x400` | the game's bound: the table's own count at world+0x1183c, at most 0x1388 |
| note | reach 15 .. 75 | 15 .. 70 |
| note | square to the wall, Dead Men keeps the heading | kept, said as a difference by choice (klclimb.c section 3) |
| N1 | 2.1 '30 past the probe'; 1.3 'a null clip is a null read at 0x6a2a65'; slot id of High 2507 | corrected: 15; it reads through the channel Play did not return; 2505 (measured again on the build's `climb.json`) |
| N2 | clip record +0x2C is non-zero on 8 of the 12 added clips | added to section 9 (not read; not changed) |
| N3 | `apply` rewrites `big_before` in the copied `dyn.json` / `fed.json` | not changed (the tool is not this version's to change); said in section 9 for the lead |
| N4 | `Key=0` is a default for scripted runs | said: for play `Key=0x45` (4.3, K8) |
| N5 | `0x59d550` draws from the game's generator, twice per vault try | said in the file and in 4.3 |
| N6 | 'moves the player as a vault's does' | section 9: with the hand-over, and by the mechanism of section 3 |
| the build | - | new: the first link failed on `GetAsyncKeyState` (the hook does not link user32); looked up at run time now. A syntax check could not show it |

### 6.3 Third version: what the second review (`re/climb_review2.md`) found and what was done

Every 'should' is FIXED (none refuted); the notes are taken up. Evidence: the address read again by the writer
of this version (`debug\dasm.py`), a measurement (scratch `meas.py` on the build's `.ANM`), or the off-game test
(4.3: `sim.exe` 66 of 66, and `sim_old.exe`, the same test against the second version).

| second review | where | finding | what was done |
|---|---|---|---|
| **D1** should | `klq_vault`, the branch after `0x619790` ('did not outlive its own start'); 7 K6 | the failure branch did not look at the collision count: a start whose End ran before its own collision-off leaves him without collision, unsaid | **Fixed.** Read: leave-cover at 0x6a2817, the collision-off call at 0x6a2a4a, Play at 0x6a2a5d; 0x8b41c0 does not count below 0; `0x619790` returns 0 only for an empty pool, having done nothing. The branch now reads count and flag (0 and 1 before the call, by `klq_refuse` in the same tick); not 0 / not on: a line (`LEFT HIS COLLISION SWITCHED OFF`), `klq_give_back` at once or owed for 3 s, a `RESULT` line. The line is in K6's FAIL list. Test L; control: the second version leaves count 1, flag 0 |
| **D2** should | `klq_tick` (`told = 2` before the try), the vault's channel refusal; 7 K1 / K6 | 'REFUSED' could be a passing state and was final for the stay; K1's count is taken while he still walks | **Fixed.** The refusal is retried (every 250 ms while he stands), said once as `NOT vaulted yet`, and `REFUSED from this stand: T tries in M ms` comes only after a second of refusals; a later pass says how many refusals went before. The count is printed again in the `WOULD climb` / `WOULD vault` lines (after the dwell) and every second with `Log=2`; the `at the foot` line says `as he arrives`. K1 and K6 reworded. Test M |
| **D3** should | 7 K2 (the HAND-OVER line); `klclimb.c` sample LOG | two expected numbers wrong: the first place is where he stood, not P1; the second is not the clip's end | **Fixed**, with the numbers of the NEW default (N2): the first place = `pos foot`'s place (z -688 .. -648 with the script); the second = (x, 428, about -608) at frame 46.x (measured: frame 46.0 z -609.6, 46.2 z -608.4; frame 48.2 would be z -596.6, the review's number; the end z -580.6). The off-game test prints `frame 46.3 of 51: HAND-OVER ... proxy (-3000, 200, -665) -> (-3000, 428, -608)` |
| N1 note | 3 'who moves him'; `klclimb.c` section 1; `klq_refuse` | slot 35 marked 'not read'; the third gate, vtable +0x578, the node write and `[player+0xd50]` not named; 'the node is put where the proxy is' is the frame's doing | Read (0x74efe6 .. 0x74eff8, 0x598460, 0x74f057 / 0x5aa510, 0x74f2c5 / 0x5380d0, 0x74f2df / 0x693400 -> 0x8caf30, 0x536a20, 0x72d010) and written into section 3 and the top comment; `klq_refuse` refuses behind either gate (test Q) |
| N2 note | `klq_init` (`HandFrames`), the KLHook.ini comment | 3 leaves 125 ms; the reason given for the cap was not what the code does | Default 5 (200 ms); the comment says what holds a hand-over back (the '10 beyond the face' test). Test N: first failing single frame 240 ms with 5, 130 ms with 3 - the review's numbers |
| N3 note | `klq_climb`, the `Align=1` branch; K5 | `Align=1` hands the proxy over under the wall's top | Measured again (2.3: 5.0 under at the face, 3.1 at frame 46). The single alignment aims 10 over the top (`KLQ_LIFT`): 0.8 .. 6.6 over at the face for a High top 183.5 .. 220 over the feet. K5 says it. Test O. **Found on the way:** `Align=1` cannot carry class Low at all (its clip lunges 51.9 forward in 3 frames) - refused with a line |
| N4 note | `klq_follow` call-off / time-out (`klq_give_back`) | a call-off can put the proxy inside the wall | `klq_give_back` never puts the proxy at a node that is between the faces (15 clear) and more than 3 under the top; it says which it did. Applies to every path that gives back. Test P; control: the second version's `RESULT` is `INSIDE THE OBSTACLE` |
| N5 note | 7 K7 (c) | `count 2 -> 1` after a death: the body is on layer 5 while the count says off | Said beside the line in K7 (c); no code change (the game's own quirk: 0x686600 sets layer 5 whatever the count, read) |
| N6 note | 7 K2 | every channel that ends is reported; weapon handling and faces are the likely enders | Said in K2's FAIL list, in the plan's risks and in the top comment's section 3 |
| note | the proof build | built outside the brief's letter | none asked. The third version's proof build is again a scratch copy outside the tree, the work folder and the game folder (4.3) |

Not changed by the third version: `klq_node`, `klq_slot`, `klq_clip`, `klq_align`, `klq_registered`,
`klq_carry_refuse`, `klq_code` (its 8 byte rows and 4 vtable entries compared with kl2.exe again: all the
same), the three wiring lines, `tools/kl_fa_climb.py`, the build.

### 6.4 Fourth version: what the first live start found (`re/climb_crash.md`)

| what this account said | what the game did | what was done |
|---|---|---|
| 3, 4.3: a mini animation is told of ended channels (slot 10); nothing else was looked for | it is also handed its clip's EVENTS (the dispatcher's slot 4 -> slot 11 -> `0x637060`), and at event id 5 that routine uses an object a mini animation has not got: the fault at kl2.exe+0x7e400, clip frame 6 | section 3 has the rows; the players' clips of a build carry 105 for 5; the hook refuses a clip with an id the routine acts on, before the start and after it |
| 3, 'who calls it': the stagger is a stock mini animation on a walking player | the stagger's slot name is in none of the 21 stock `.ANM` files: it never plays a clip. The call is stock, the playing is not | corrected in section 3; said in 9 |
| 2.3: 'the player-timed clips' table, events 5 and 6 | - | the variants' events added: `Sprint_Low_No_Weapon` has 5 at 3 and 6 at 15, and is in the NPC Low lists too |
| 7 K1: 'if the node reads (0, 0, 0) ...', the proxy, the sign of facing, the heights | all as hoped: node = his place, proxy = node at rest, facing 1.00, the node's height 201 on a floor of 200; +0x460 is the mesh's place and stays at the mesh's edge | K1 / K2 say what was seen |
| 4.3, the off-game test: 'a MODEL of the frame as section 3 reads it' | the model had no clip events | the fourth version's test has them, by the game's own tables; the third version faults in it as in the game |
| 9: 'clip record +0x2C ... if K2 shows a fault inside the animation code, this is the first thing to zero' | the fault was not there: no routine of the chain reads +0x2C (0x2330 in the clip that played) | left as it is |
| the speed gate (`Speed`, `Dwell`) | did its work: 483 as he came into reach, the start 499 ms later from a stand | unchanged; the `started` line prints speed and stand |

### 6.5 The fix round of the fourth version: what the crash's review (`re/climb_crash_review.md`) found

Every finding was re-checked against `kl2.exe` and the dump before anything was changed (`re/climb_crash.md` 12 has
the how, finding by finding). **None is refuted.**

| review | where | finding | what was done |
|---|---|---|---|
| **M1** must | 3 ('what an action is handed'), 9; `re/climb_crash.md` 7, 11; `klclimb.c` section 0 | 'nothing else reaches a mini animation' is wrong: it is handed the clip events of EVERY subscribed channel of its player; an id-5 event of another clip faults the same way. Closed for this build by reading and counting | The text corrected in all three files, with the addresses; the 'same crash again' key (K2, `re/climb_crash.md` 10) tells the two cases apart by the moment and by what the dump holds at esp+0x48 / +0x54. Beyond the text: the hook refuses / stops / calls off a climb beside such a channel (`klq_others`, 4.3) |
| **S1** should | head, 6.4, 7 (K2), 9; `re/climb_crash.md` 0; `klclimb.c` section 0 | 'the root IS at P1 at clip frame 6.03' is given as seen and is not shown | ASSUMED everywhere. Read for it: the vector the claim rested on is a leftover of an earlier frame in the animation update's locals, and the game's own record (`[player+0xe8]` = 0, `[player+0xec]` = 6.0) says the blend was still short of its target in every frame it finished. The `aligned to P2` line prints his node and its distance from P1 |
| **S2** should | `kl_fa_climb.check`; optional: the hook | make M1's closure a rule | `check` FAILs a clip of the other body class with an id outside `GENERIC_QUIET` (4.1; 9, 10, 11, 21, 24 .. 35, 42 - the review had 9, 10, 24 .. 35; 11, 21, 42 were read for this round, 20 is not quiet). In the hook: more than the optional `Log=2` line (4.3) |
| **S3** should | `klq_code` | slots 12 and 13 are compared, the way to them is not | three compares added (4.3) |
| **S4** should (the lead's) | 7, K2's set-up | the rerun is K2b, not K2, unless the script lets go of W; the gate measures node displacement | set-up rewritten; the `started` line prints his movement kind |
| N1 .. N6 notes | - | a third event-queueing routine; `0x7de320` read; the split of `0x4a75d0`'s call sites; `apply`'s traceback; the likeliest failure unchanged; things for the lead | `re/climb_crash.md` 3, 5, 6, 12; the tool's `main`; the lead's points are in the track's report |

Not changed by the fix round: `klq_refuse`, `klq_carry_refuse`, `klq_give_back`, the vault, the gate, `merge` and
the build.

## 7. Live checks, in order (the first half of K2 seen, and in it what K0 and K1 ask; the rest not run)

Rewritten for the second version: every check names the lines that mean PASS and the lines that mean FAIL, in
the hook's log (`KLHook.log`, lines beginning `climb:`) and in the runner's own position lines.
**Changed for the third version** (6.3): K1 (which channel count answers K6, the two new refusal reasons), K2
(the HAND-OVER line: frame 46.x and its two places; the likeliest failure), K5 (the lift), K6 (PASS, REFUSED
and FAIL are told apart anew), K7 c. K0, K2b, K3, K4, K7 a / b / d and K8 are as they were.
**Changed for the fourth version** (6.4, after the first live start): what K1 and K2 SHOWED is written into them
('SEEN 2026-10-11'); K2's `started` line has its new form and K2's FAIL list the crash and the refusal; the
set-up names the new build.
**Changed for the fix round** (6.5): the set-up says what the rerun will be (K2b unless the script lets go of
forward); K1's and K2's lines have their new ends (`movement kind`, `other channel(s)`, his node in the `aligned
to P2` line); what was 'seen' of the first alignment is cut down to what the dump holds; K2's FAIL list has the
other channels' lines and the second form of 'the same crash again'.

**What the first live start showed, in one place** (run `K2c_DM03_wall_hp`, the third version, `z_climb\M03`, a
scripted player at edge 2; `re/climb_crash.md` 1): the level loads and plays with the merged `.ANM` (K0's
question); `2 edge(s) from ...KLJoin.ini`; node, +0x460 and proxy printed side by side - **the node is his place,
the proxy reads the same place at rest, +0x460 is the navigation mesh's place and stays at the mesh's edge** (z
-751 while he stood at z -666; its height 220 against the node's 201); **facing 1.00** as he ran at the face; `at
the foot of edge 2: ... 48 from the face, speed 483 ... the top is 202.5 over his feet = /Movement/Climb/Up/High,
id 2505; 0 full-body channel(s) of his play as he arrives`; 499 ms later `started ... action 0150d1c4, clip
78168c98 of 52 frames (flags 10c0), events 5 at 6 and 6 at 20; aligned to (-2074, 201, -672) in 6 frames`;
`collision off (the climb starts; count 0 -> 1)`; 0.24 s later the crash. In the dump: the game's record of the
alignment it took (`[player+0xe8]` = 0, `[player+0xec]` = 6.0); no other channel of his playing, none with an event
queue. **(5)** NOT in the dump: where he was - his node and his proxy are not among its memory, and the vector
this paragraph gave as 'the root at P1' is an earlier frame's leftover (`re/climb_crash.md` 1). Not seen:
anything after frame 6.

**Set-up.** **`z_climb3\M03`** in the test slot (4.2b; NOT `z_climb\M03` or `z_climb2\M03`, which the fourth
version refuses and the third crashes on); a TEST hook built from the tree; `[Bots] Enable=1 Log=1`; `[CrewHop]`
as in re/bots_bank.md with `Log=2` (the 'left From' line needs it). Each check changes one thing.
**The rig's goto and the foot** (seen in the run above): klauto's `goto` judges by +0x460, and +0x460 does not
follow him off the mesh - a `goto` to a place the mesh does not reach is never `reached` and W stays down until its
time-out. In K2c that most likely made the start one with FORWARD HELD against the wall (he stood 41 from the
face, about a man's radius; the gate saw 'slower than 150' and started him): K2b's condition, not K2's. The mesh
ends 126 from the face at edge 2, the foot is 15 .. 70 from it: no mesh place is at the foot. So either the
script lets W go by time before the dwell is over (the rig's own business: `tools/kl_playtest.py`, not this
track's), or K2's result is read as K2b's. NOT ESTABLISHED which it was: the log has no line for the keys.
**(5) What the rerun will be** (the crash review's S4, which reads the log the same way): the gate measures his
NODE's displacement from tick to tick, so a man who runs on the spot against the wall 'stands' for it - the gate
as written, not a fault of it (Dead Men asks for speed and the USE tap, held stick or not). **With the wall script
as it was, the next run is therefore K2b - a climb with forward held through the clip - and not K2**, and it must
be read by K2b's lines: `ended at frame N ... BEFORE the hand-over` + `BACK AT THE FOOT` would then mean 'held
input ends the mini animation', not 'the climb does not hold'. For a K2 proper the script must let go of W
before the start: e.g. the last `goto` to a place the mesh reaches (z -760 at edge 2; it ends `reached` and lets
the keys go), then the rig's `down W` / `wait N` / `up W` for the last 80 (N by trial: he must end 15 .. 70 from
the face, looking at it), then `wait 6000`. The `started` line now prints `movement kind K` beside the speed;
whether K tells a stand (2?) from a run against a wall (3?) is not known - compare it between a run with W held
and one without.
**The place.** Edge 1 at x -3000: the face is the plane z -625; the yard is z < -625 (floor 200 by the
collision, 220 by the navigation mesh), the wall's top is y 403.5 from z -625 to -575.5, beyond it a dumpster
lid (y about 281) and then the street (y 150). AT THE FOOT is z -695 .. -640.
**The runner's lines** (klauto.c): `pos <label>` gives `pos <label>: me #N (x, y, z) heading H`; a `goto` ends
with `script N: goto (x, z) reached in T ms: at (x, y, z) heading H` or `... NOT reached ...`; `[Auto]
PosLogMs=250` gives a `pos tick` line four times a second. Their place is the floats at +0x460, whose HEIGHT
is the navigation mesh's (klauto.c) - and the mesh has no polygon on the wall top (2.2). So **from the runner's
lines judge by x and z only**; the height is judged from the hook's lines, which print the node as well.
**The script** (a suggestion; the yard way point is re/escape.md 6's), from a stand - nothing is held while
the clip plays:

    goto -1250 -1250 110 12000 sprint keep
    goto -3000 -900 110 20000 sprint            in the yard, 275 before the wall, x of edge 1; keys let go
    goto -3000 -668 20 8000                     a walk straight at the wall: he ends 23 .. 63 from the face, looking at it
    pos foot
    wait 6000                                   Dwell 0.4 s + the clip 2.08 s + the RESULT line 2 s after its end
    pos after

- **K0** (no new code; the hook as installed, which reads no `[Climb]` section): PASS = the level loads, GO,
  `hop: bot N left From of hop 1 by itself` and `bots: ... van 1` as on `z_hop\M03`, a clean `RESULT:` line of
  kl_autotest. FAIL = a crash or an assert at the load or in the round that `z_hop\M03` does not have. It
  proves that the merged `.ANM` loads and harms nothing; it plays no climb clip.
- **K1** `[Climb] Enable=1 Dry=1 Log=2`, the script. PASS = all of:
  `climb: on; Mode=climb ... Dry=1 ... - DRY RUN: no game routine is called`;
  `climb: 2 edge(s) from ...KLJoin.ini for level f01\f01_main` and `climb: edge 1: (-3450, 404, -625) -
  (-2650, 404, -625), 800 long ... 203.5 up = /Movement/Climb/Up/High, stand-off 47`;
  on the way `climb: node (...), +0x460 (...), proxy (...): near none of the 2 edge(s)` with a node place that
  agrees with the runner's `pos` lines in x and z (if the node reads (0, 0, 0) or stands still while he runs,
  the node is not his place and the file cannot work as written: stop here);
  `climb: at the foot of edge 1: node (x, 200 or 220, z), +0x460 (...), proxy (...) ... facing 0.9x; the top
  is 203.5 (or 183.5) over his feet = /Movement/Climb/Up/High, id 2505; N full-body channel(s) of his play as
  he arrives` - with **the proxy within a few units of the node** (the proxy read is right), **facing positive**
  (the sign; if it reads -0.9x while he looks at the wall: `Angle=0` until the sign is turned in the file), the
  id 2505, and no `(his NODE is not at the floor ...)` at its end (if it is there: the heights come from +0x460
  and the RESULT lines judge no height);
  `climb: edge 1: WOULD climb by /Movement/Climb/Up/High (slot 2505) ... P1 (x, y, -672) at event 105, P2 (x,
  y + rise, -672) at event 6; N full-body channel(s) of his play NOW (after the dwell), M channel(s) of any class
  with an event queue (mask) - DRY RUN, nothing is called (the clip and its events are not looked at: that takes
  the game's 0x59d550)` (**(5)** M and the mask are new: what a start would find playing with a queue; if the line
  goes on `, ONE OF THEM WITH A CLIP THAT HAS AN EVENT FOR THE GAME'S CASE 5`, a start would be refused - say which
  body and weapon);
  the runner's `pos foot` with z -688 .. -648 and `pos after` at the same place (nothing moved him).
  **SEEN 2026-10-11** (in the lines of the `Dry=0` run K2c, at edge 2, x -2074): the two edges; node and proxy the
  same place, agreeing with the runner in x and z while he moves; at the wall the runner's +0x460 stays at the
  mesh's edge (z -751) while the node goes on to z -673 / -666 - **from there on only the hook's node lines say
  where he is, and `pos foot` / `pos after` do NOT** (the runner prints +0x460); `at the foot of edge 2: node
  (-2074, 201, -673), +0x460 (-2077, 220, -751), proxy (-2074, 201, -673), 48 from the face, speed 483, facing
  1.00; the top is 202.5 over his feet ... id 2505; 0 full-body channel(s) of his play as he arrives`, no `(his
  NODE is not at the floor ...)`. So the node's height is the collision floor's (201 on 200), the facing sign is
  right, the proxy read is right. No `NOT climbed yet` line: `klq_refuse` passes a healthy standing player (its
  two gates of the third version among them).
  FAIL = `climb: edge 1 NOT climbed yet: <reason>` while he just stands there: one of `klq_refuse`'s tests does
  not hold for a healthy standing player (the reason names the field: the frame bytes +0x7a4 / +0x430, **the
  two gates new in the third version - `[player+0xd50] is not 0`, `the node [[[node+0x50]+0x60]+4] ... cannot be
  read or has flag bit 0x800`** -, the proxy's phantom, the body table ...) - to be read again before K2; or no
  `at the foot` line although `pos foot` is in the zone (compare the every-second line: distance, `along`, the
  two heights).
  **The channel count and K6** (the second review's D2): the count of the `at the foot` line is taken AS HE
  ARRIVES, still walking - it is NOT K6's answer. What the vault would meet is the count of the `WOULD climb`
  line (after the dwell: he has stood for 0.4 s) and of the every-second `Log=2` line (`..., facing 0.9x, N
  full-body channel(s) of his play = AT THE FOOT`) over the 6 s he stands there: 0 in those = the vault would be
  tried; over 0 in all of them = it would be refused from this stand; changing = it would be refused at first
  and tried when the channel is over. A count is not a verdict on (ii): K6 is.
- **K2** `Dry=0`, the script. PASS = all of, in this order:
  `climb: edge 1: started /Movement/Climb/Up/High (slot 2505) from node ..., N from the face, speed S after D ms
  at the foot under 150, movement kind K: action ..., clip ... of 52 frames (flags 10c0), events 105 (the foot)
  at 6 and 6 (the top) at 20, none the game acts on; aligned to (x, y, -672) in 6 frames; M other channel(s) of
  his play with an event queue (mask)` (fourth version; S near 0 from a stand, D 400 .. 500; **(5)** K and M are
  new - M was 0 in the dump of the first start; an M over 0 is no fault, none of those clips has an event for the
  game's case 5 or the climb would not have been started, but say it);
  `climb: collision off (the climb starts; count 0 -> 1)`;
  **SEEN 2026-10-11 up to here** (third version, `events 5 at 6 and 6 at 20`), and in the dump that the game took
  the first alignment (**(5)** not where it brought him: 6.5). Then the game faulted - on the first-form level;
  `re/climb_crash.md`.
  `climb: edge 1: frame 6.x: aligned to P2 (x, 403 or 404, -672) in 13.x frames; his node is at (x, y, z) now =
  (dx, dy, dz) from P1 (x, y, -672.0)` - **about 0.25 s after `started`: the first line the game has never
  reached. It is the fix seen** (the clip's event at frame 6 went to the routine's 'nothing'). **(5) Its second
  half is the first sight of what the first alignment does**: PASS = (dx, dy, dz) about (0, 0 .. +3.5, 0 .. +0.6)
  - he IS at P1 but for what the clip's own root has moved since frame 6 (+1.1 up at frame 6.3, +3.5 at 7.0;
  measured). A dz of +6 or more (where he stood, or nearer the face) or a dy well outside that: the alignment did
  not move his node as section 3 reads it - the climb may still go on; tell the lead with the line;
  `climb: edge 1: frame 46.x of 51: HAND-OVER - the proxy put at the node: proxy (x, y, z of pos foot) -> (x,
  428, about -608), node (the same); collision on (count 1 -> 0)` (`HandFrames=5`, the default: frame 46.0 ..
  46.5 at 60 frames a second, later by up to one tick's worth at a lower rate; measured on the clip: z -609.6
  at frame 46.0, -608.4 at 46.2, -603.7 at 47.0; y = the top + 24.5 = 428 whether his node read 200 or 220 at
  the foot) - **its FIRST place is where he STOOD** (the runner's `pos foot`: z -688 .. -648 with the script),
  **not P1's -672**: an alignment moves the node, not the proxy. That is section 3's reading seen (if the first
  place is already near the node, the proxy was carried along after all: harmless, and worth telling). **Its
  SECOND place is about z -608, not the clip's end -581** (the second version of this file had both numbers
  wrong on paper: the second review's D3; with `HandFrames=3` the second place would be about z -597);
  `climb: edge 1: over after about 2080 ms of game time (...), last seen at frame 5x of 51: ...; his action
  now 00000000, his collision count 0`;
  `climb: edge 1: +500 ms: ...` and `+1000 ms: ...`: `N beyond the face`, `+0 .. +25 to the top`;
  **`climb: edge 1: RESULT 2 s after the end: UP - he stands on the obstacle, about 44 beyond the face`**;
  the runner: `pos foot` z -688 .. -648, **`pos after` z -625 .. -575** (x within 10 of `pos foot`'s).
  Also PASS: `RESULT ... ACROSS` with `pos after` z > -575 (he ends 5 short of the far edge of a 50-thick wall
  and may slide off at once: he is over the wall). Picture: take it 3 s after the `started` line, not at the
  end of the clip.
  FAIL, and what each says:
  `RESULT ... BACK AT THE FOOT` and `pos after` z < -640 - the climb did not hold. With `ended at frame N of
  51 BEFORE the hand-over (his action now X, his down state D, dead bit B)` before it: the action went early
  (N and X say when and to what; nothing was pressed in this script, so a channel of his own ended: K4's
  question has its answer already - raise it with the lead before K3). **This is the likeliest way K2 fails**
  (the second review's N6): the game reports EVERY channel of his that ends (0x50b5e8 .., no class test) and
  the mini animation says yes to each once its own Play is over - weapon handling and faces are channels of
  the other body class (872 such clips in this build, the review's count) and nobody has to press anything for
  one of them to end. (The game's own stagger (0x5022c0) does NOT have the same exposure, as this line said: it
  never plays a clip in the retail game, section 3.) **(5)** In K2b's condition - forward held, which is what the
  rerun with the wall script will be (set-up) - held input is a second candidate for the same line. With the
  `HAND-OVER` line before
  it: section 3's reading is wrong somewhere after the hand-over - or Havok did not hold him 24.5 over the wall
  top (not readable); the `+500 ms` line says where he went.
  `... the proxy is NOT put at the node: node (...) is N beyond the face ... = INSIDE it` in any line - the two
  calls came due with his node inside the wall (new in the third version, 4.3): he is then stepped back to the
  foot instead; after a `HAND-OVER` it means the heights were read wrong, after `stopped` it follows a call-off.
  `climb: edge 1 NOT climbed: the game did not keep the action ...` - this body's set has no clip for the slot
  (which body? the wardrobe's 16 bodies use Kane x4 / Lynch x12).
  `... NOT climbed: the game found no channel to align` or `the action's channel ... is not the playing
  full-body root-motion channel` - the clip's flags or the channel are not what was read; he stood still.
  `... CALLED OFF by this file (the alignment to the top was not set)` - a long frame between events 5 and 6.
  `RESULT ... INSIDE THE OBSTACLE` or `ELSEWHERE` - he was left where a man cannot stand: the line has the place.
  `... the hand-over is NOT made: <reason>` / `GIVEN UP after 3 s` - `klq_carry_refuse` refuses a live player:
  its reason names the field.
  **`climb: edge 1 NOT climbed: the clip ... has event id 5 at frame 6, which the game's own event routine 0x637060
  acts on ... NOTHING WAS STARTED`** (fourth version) - the level in the slot is of the first form (`z_climb\M03`,
  `z_climb2\M03`): install `z_climb3\M03`. With `... STOPPED in the tick of its start ...` instead: the start
  picked another clip than the one looked at before it, and that one has such an event - say which body and
  weapon.
  `... NOT climbed: this body's set has no clip for ... (0x59d550 gives none ...)` or `the record or the event
  table of the clip ... cannot be read` - nothing was started; the first names the body's set, the second the
  animation manager `[0x1546f6c]`.
  **(5)** `climb: edge 1 NOT climbed: channel C of his plays the clip X with an event queue, and that clip has
  event id 5 at frame F, which the game's event routine 0x637060 sends to its case 5: ... NOTHING WAS STARTED` -
  another channel of his, one the start's Play would not stop, plays a clip whose event would fault the mini
  animation (6.5, M1). No clip of this build's other body class has such an event (the check's PASS line), so the
  line means either a queue on a channel of a class the hook mis-took, or a level that is not `z_climb3`: say C,
  X and the `at the foot` line. The same with `... STOPPED in the tick of its start ...` (seen right after the
  start) or `frame F: channel C of his plays the clip ...: the climb is called off` + `CALLED OFF by this file
  (another channel of his ...)` + `BACK AT THE FOOT` (it appeared during the climb - by the reading it cannot:
  something subscribes a player's channel besides an action's start).
  **A crash at kl2.exe+0x7e400 (`reading address 00000060`) about 0.24 s after `started`, with no `aligned to P2`
  line between: the crash of 2026-10-11 again** - an event id 5 of the climb's own clip reached the game's routine
  (the third version of the hook on a first-form level does exactly that; the fourth cannot by the reading).
  **(5) The same address at ANY OTHER moment of a climb** (after the `aligned to P2` line; anywhere but clip frame
  6): **an id-5 event of ANOTHER channel of his** that got past the hook's test - NOT 'the table reading is
  wrong'. In the dump `esp+0x48` is that event's clip (not the clip of the `started` line), `esp+0x54` its channel
  (not `[esi+0x20]`), `esi` the mini animation. A crash elsewhere in `0x637060 .. 0x6372dc` about 0.8 s after
  `started`, after the `aligned to P2` line: the clip's event 6 (frame 20) - the reading of the switch table is
  wrong for id 6. `re/climb_crash.md` 10.
  A crash: `python debug/triage.py --keep`; the last `climb:` line says which call was the last.
  **Where he is, from the runner's lines**: nowhere near the wall - `pos foot` / `pos after` print +0x460, which
  stays at the mesh's edge (SEEN, K1). Judge by the hook's `node (...)` places only (`+500 ms`, `RESULT`).
- **K2b** the run-through (K4's first question): the script with `goto -3000 -400 110 15000 keep` in place of
  the last three lines (a point on the street: W is held into the wall and through the clip), then `pos
  after`. PASS = K2's lines up to `over`, then `RESULT ... ACROSS - N beyond the face, -122 (the lid) or -253
  (the street) to the top` and `pos after` z > -575; the `goto` line `reached` with z about -400. FAIL = `ended
  ... BEFORE the hand-over` + `BACK AT THE FOOT` (held input ends the mini animation: the climb then needs the
  stick let go, or input taken away - not written); `pos after` z < -640.
- **K3** after a K2 that ended UP: `goto -3000 -400 110 15000`, `pos street`. PASS = `script N: goto (-3000,
  -400) reached ... at (x, 150, about -400)`, no `climb: at the foot` line on the way (from the top and from
  the street no edge is in reach), `bots: ... van 1` once he is in the exit box (z from -540), and he is alive
  (the round goes on; no 'record 0 ... dead'). FAIL = `NOT reached` with z between -625 and -575 (he cannot
  leave the wall top), a death from the drop, a crash.
- **K4** what ends it early - one run each, the K2 script with one line after `pos foot`: `wait 900` then `tap
  R` (reload), `mdown 0` / `mup 0` (fire), `tap C` (cover), `tap E` (use). For each: PASS (it does not matter)
  = K2's PASS lines; PASS (it ends the climb, cleanly) = `ended at frame N of 51 BEFORE the hand-over (his
  action now X ...)`, then `after its end - the proxy put at the node ... collision on (count 1 -> 0)`, then
  `RESULT ... BACK AT THE FOOT`, and the round goes on; FAIL = `GIVEN UP`, `RESULT ... INSIDE THE OBSTACLE`
  (a place between z -625 and -575 under the top), `RESULT ... ELSEWHERE`, a crash.
  Then a second climb in the same run: `goto -3000 -800 40 8000`, `goto -3000 -668 20 8000`, `wait 6000`:
  PASS = a second `started` line and `collision off (... count 0 -> 1)` (the count was 0 at rest).
  A climb with a pistol and one unarmed (the lists' condition pairs): PASS = K2's lines; the clip address in
  the `started` line differs from the rifle's.
- **K5** `Align=1`: PASS = `started ... aligned to (x, 413 or 414, about -580) in 51 frames` (the end place
  **10 over the top**: the third version, the second review's N3), no `frame 6.x: aligned to P2` line,
  `frame 46.x of 51: HAND-OVER - the proxy put at the node: proxy (where he stood) -> (x, about 409, about
  -608)` - **the second place is 4 .. 8 OVER the top** (measured for a top 203.5 over his feet: +5.9 at frame
  46.0; 183.5: +7.9; aimed at the top itself, as the second version did, it would be 3.1 UNDER it) -, then
  `RESULT ... UP` with `+0 to its top` (he comes down the 10 when the clip is over). FAIL = K2's FAIL lines, or
  `HAND-OVER ... - the proxy is NOT put at the node: ... = INSIDE it` (his node was more than 3 under the top
  when the calls came due: the lift is not enough for this stand - tell the lead with the line's numbers).
  Which of K2 and K5 looks right (the 24.5 settle of K2 against a slightly late grab and a 10 settle) is for the
  eye: pictures at 0.8, 1.2, 1.6 and 2.0 s after `started`. Not on a Low edge: `NOT climbed: ... Align=1 is not
  for that class`.
- **K6** only if K2 fails, `Mode=vault`, in a run whose log somebody reads before the next one; the script of
  K2 with `wait 8000` in place of `wait 6000` (a refusal is asked again for as long as he stands). PASS =
  `climb: edge 1: the game's own VAULT started from node ... action XXXXXXXX`, `over after ... the vault ...
  his collision count 0`, `RESULT ... UP` (or ACROSS), `pos after` z > -625 - with or without a `NOT vaulted
  yet` line before it: if one is there, the `VAULT started` line is followed by `(the vault had been refused T
  time(s) in the M ms before: the channels that played then are over)` and the refusal was a PASSING state.
  **REFUSED** (no call of the vault's start was made; (ii) is then closed for a player standing as the script
  leaves him) = BOTH `edge 1 NOT vaulted yet: N channel(s) of his play that the vault's own Play would replace
  and report (the first: channel C, clip X at frame F of T): ...` AND, a second later, `edge 1: the vault is
  REFUSED from this stand: T tries in M ms of standing, the last: ...` with T of 4 or more, and no `VAULT
  started` line in the 7 s after it. **The first line alone is not a verdict** (the second review's D2: the
  walk, stop and turn clips are of the vault's body class; the frame F of the channel in the two lines says
  whether it is a clip that runs out or one that loops). FAIL =
  `NOT climbed: ... the vault did not outlive its own start (... another cause); right after the start his
  collision count was 0 and the flag 1` (something in its start ended it after its own collision-off and gave
  the collision back: the two routines not read);
  **`edge 1: the vault's start LEFT HIS COLLISION SWITCHED OFF (count 1, flag 0; ...): this file gives it back`
  followed by `after a vault start that kept no action - the proxy put at the node ... collision on (count 1 ->
  0)`** (the second review's D1: the vault was ended BEFORE its start switched the collision off, the game's
  start went on with a freed object; the file has given the collision back - do not run `Mode=vault` again on
  this build, and read the dump if the game faults later in that session) - or, instead of the second line,
  `the proxy and the collision are NOT given back yet` / `GIVEN UP after 3 s` (he is left without collision: end
  the session);
  `RESULT ... BACK AT THE FOOT` after a `VAULT started`; a crash.
- **K7** the count, the clock, the end paths. (a) A second round in the same process, K2's script again: PASS
  = `collision off (... count 0 -> 1)` again, K2's PASS. (b) **A pause during the climb** (review S2): after
  `pos foot`: `wait 1200`, the pause menu's key, `wait 5000`, the key that resumes. PASS = `over after about
  2080 ms of game time (about 7000 ms by the clock)` and `RESULT ... UP`. FAIL = `STOPPED by this file (the
  action outlived its clip ...)` with a game time near the wall time: the pause menu does not hold the game's
  clock (the pause byte was not read to its writers) - tell the lead, the limit then needs the channel's own
  frame. (c) **A death during a climb** (review S1; not scriptable - to be looked for in any session's log):
  PASS = `ended at frame N of 51 BEFORE the hand-over (... dead bit 1)`, `after its end - the proxy put at the
  node ... collision on (count 1 -> 0)`, the round's own death handling follows; also PASS = `collision on
  (count 2 -> 1) - somebody else holds it off as well` (the game's death holds its own count). **Read that
  second line for what it is** (the second review's N5): `0x686600` sets the body's Havok layer to 5 whatever
  the count is (0x686608 .. 0x68662d), so after it the dead man's body collides again while the game's own
  count still says 'off' - the game's own quirk (its vault's End would do the same); if a body then behaves
  oddly (a ragdoll that catches on things), this line is where to look. FAIL = `GIVEN UP`, a crash. (d) A round that ends during a climb: PASS = the same two lines, or `the player object ... is
  gone ...: forgotten, nothing is called`.
- **K8** a bots round as the owner plays it, `[Climb] Enable=1 Key=0x45`: PASS = the bots' lines as in K0 (`hop:
  ...`, `bots: ... van 1`), no `climb: edge N: started` line for anybody but the human, and for him only while
  E is down at the foot (`climb: at the foot ...` lines without a `started` line when he merely stands there).
  FAIL = a `started` line without the key, or `climb: Key=69 is set and user32's GetAsyncKeyState was not
  found` at the start.

## 8. Dead Men itself - what to look at, if the lead starts it

The files cannot say how the climb LOOKS and where it ends. The campaign shows it in its first minute:
chapter 'Withdrawal' (`Scenes\Locations\M03_A`), from the start (checkpoint 1 in the back street at about
(-2976, 154, -202)); the first obstacle is our wall, from the STREET side, at the dumpsters x -3332 .. -2816.
1. Street -> dumpster lid (124 up) -> wall top (120.5 up): which clip each is (both sit at the border: Low up
   to 120, Medium above), whether USE is needed or running into it is enough, how far from the face he can
   stand when it starts.
2. Drop into the car park (our yard), turn round, climb the wall from the yard side (184 by the mesh, 203.5 by
   the collision: `High`): does he end ON the wall near its far edge (predicted 44 past the yard face of a
   50-thick wall), **is there a settle of about 25 at the end** (decides `Align=2` against `Align=1`), does he
   keep his heading or turn to the wall, how long (predicted 2.08 s).
3. Step off the wall to the street: which landing plays for 253 down and for 122 onto a lid.
4. From the street the bare wall must refuse (253 > 220).
5. The crew at the lanes x -3210 / -2938: the `_NPC` clips on the three links - the picture the AI heisters
   would give with 5.1.

## 9. Assumed, not established, not done

- **(4) What has run** (2026-10-11, the third version on `z_climb\M03`): the level loads and plays with the merged
  `.ANM`; one climb was started and the game faulted 0.24 s into it (`re/climb_crash.md`). SEEN since: the node's
  place and height, the proxy's place at rest, the facing sign, the slot, the kept action, the clip, that the game
  TOOK the first alignment (its record in the dump), 14 frames of an aligned mini animation with the collision
  off. NOT SEEN: anything after clip frame 6 - the second alignment, the hand-over, the end, where he stands.
  Of the fourth version (the hook's refusal, the level's id 105) nothing has run.
- **(5) ASSUMED, and written as seen until the fix round** (the crash review's S1): that the first alignment
  brought him to P1 by clip frame 6. The dump holds neither his node nor his proxy; by the game's own record the
  blend had not reached its target in any frame it finished. It is the reading of `0x50b0f6 ..` (3, AlignTo); the
  `aligned to P2` line of the next run prints his node.
- **(4)** READ, not seen: a clip event id outside 5 .. 53, and id 6, does nothing in a mini animation (`0x637077`,
  the tables). ASSUMED: nothing but the current action is told of the events of the mini animation's channel (the
  queue held one subscriber's two entries). **(5)** That covers one direction only. The other is READ (the crash
  review's M1): the current action is told of the clip events of every OTHER subscribed channel of the player as
  well, and an id-5 event among them faults a mini animation. Against it stand a reading, a count and two rules
  (section 3; 4.1; 4.3): REASONED, not read - that the three callers of `0x7f60e0` outside the actions' starts
  never subscribe a PLAYER's channel; MEASURED - no clip of the body class that outlives the mini animation's
  Play carries an id the routine does not return at (872 clips: 9 and 10 only); the check FAILs a build where one
  does, and the hook refuses or calls off beside a channel with a queue whose clip has an event for case 5. NOT
  covered: a channel subscribed and due inside one frame of the game; the hook does not walk a queue, so it
  cannot tell an action's subscription from a queue of sound events (it refuses the more for it).
  **(5)** Read in the fix round: `0x7de320` and the cases for ids 11, 21, 42 (quiet without an object); 20 and
  48 .. 53 act without the action's object (20 on one it takes from the player). Not read: what they then do.
- **(4)** The stock precedents are thinner than this account said: the stagger never plays a clip in the retail
  game, so 'a mini animation that plays a clip on a player in ordinary play' and 'a mini animation that ends with
  its clip' (endWithClip = 1 running to the natural end: `0x42b7f0` -> `0x595b70` -> `0x6fb600`) are READ, with no
  stock run behind them. Left behind by such an end: `[player+0x2758]` stays 0 (read only by the mini cutscene
  tasks); the weapon flag `[player+0x979]` set at the start (the weapon code's own, not read).
- **(4)** Not established: whether forward was held when the climb of K2c started (section 7, 'the rig's goto and
  the foot'; **(5)** most likely it was - the crash review reads the log the same way - and the rerun with that
  script is K2b); the clips the mini cutscene's move task plays; **(5)** whether the player's movement kind
  (printed in the `started` line now) tells a stand from a run on the spot.
- READ, not seen (second version; the first had it as an assumption): the root motion of an aligned full-body
  clip moves the player whatever action started it - the channel decides, and with the collision off the
  animation movement does not step the proxy (3). ASSUMED still: that the hand-over five frames before the end
  is enough - the proxy is put 24.5 over the wall top, 15 beyond the face (measured, 2.3), and the last five
  frames (29 forward) then run as the game's collision-on mini animation does, under the proxy, which settles
  on the wall; that nothing but the action system needs to know (camera, weapon state: 0x74c040 lowers the
  weapon at the start, nothing of this file raises it again - the stagger's mini animation does not either).
  NOT READABLE (both reviews): what Havok does with a proxy put 24.5 over the wall top while the clip still
  walks - whether the animation movement lets him fall during those 200 ms, how he settles. It is the path the
  game itself runs for `ZMiniPlayerMoveTask` (an aligned mini animation with the collision on), but nobody has
  seen it at this place. K2's `+500 ms` and `RESULT` lines are the answer.
- ASSUMED (third version): that 'the collision on WITHOUT the proxy sync' steps him back to where the proxy
  stayed - the file relies on it when his node is inside the obstacle (4.3, 'never into the obstacle'). It is
  the same reading as the main claim of section 3 (the ordinary movement steps from the proxy), and what the
  first version of the file did at every end; in the off-game model it holds by construction.
- ASSUMED (third version): `[player+0xd50]` is 0 and bit 0x800 of the node `[[[node+0x50]+0x60]+4]` is clear
  for a player in ordinary play. Reasoned: with either set his frame would not move him at all (3). If wrong,
  K1 shows a refusal that names it. What the two stand for was not read.
- NOT for a live run yet: an edge of class Low (its clip reaches the face in its last third of a frame, 2.3:
  the hand-over finds him in the air before the edge) - the bank's two edges are High. Medium is handed over
  about one frame before its end, 10 beyond the face: thin, not seen. `Align=1` is refused on a Low edge
  (third version, 2.3).
- `Mode=vault` (third version): the refusal for the channels that play is asked again four times a second, and
  every try draws one or two numbers from the game's generator (`0x59d550`); in Arcade nobody shares that
  generator, so only the game's own random choices shift. What is NOT closed: an End of the vault from inside
  leave-cover (0x5abbb0 / 0x834ef0, not read) - the game's start would then go on with a freed object; the file
  can only give the collision back afterwards (1.3, K6).
- ASSUMED: the pause menu sets the pause byte `[[sysif+0xac]+0xbc]` that holds the game's clock (K7 b); not
  read: its writers, and what the clock does when the window comes back to the front.
- ASSUMED: bytes `[player+0x7a4]` = 0 and `[player+0x430]` = 1 for a player in ordinary play (their setters
  0x6b22b0 / 0x7182b0 and 0x4c602e were found, their callers not read): if not, K1 shows a refusal that names
  them.
- Not read (review N2): clip record +0x2C. 8 of the 12 added clips carry Dead Men's non-zero value (9,008 ..
  61,120); it is a per-file value with no reader found, the 67 Dead Men clips the graft had put into this build
  all have 0, and these are the first such clips a PLAYER will play. The join's rule is 'copy' (re/anmjoin.md).
  If K2 shows a wrong pose or a fault inside the animation code, this is the first thing to zero. **(4)** The
  first live start played such a clip (+0x2C = 0x2330) for 14 frames; its fault was not in the animation code
  and no routine on its stack reads +0x2C.
- For the lead (review N3): `kl_fa_climb.py apply` rewrites `big_before` in the copied `dyn.json` / `fed.json`
  so that `kl_fa_bots_dyn.check` does not fail on this step's growth (said in `climb.txt`, the old numbers are
  kept as `big_before_climb`). The reviewer would rather have that check learn of the step; the tool was not
  changed in this version.
- **(4) SEEN** (it was an assumption): the player's node is at his feet on the COLLISION floor (201 on a floor
  of 200, where +0x460 reads the mesh's 220), its world place is his place, and the proxy reads the same place
  at rest. +0x460 is the navigation mesh's place: it stops at the mesh's edge. `klclimb.c` takes the node when
  that is within 40 of `Floor=` - right for this wall.
- **(4) SEEN** (it was an assumption): row 0 of a rotation = the back - `facing 1.00` while he ran at the face.
- ASSUMED: the condition bits of Dead Men's lists (8, 0x10) mean the same in Dog Days; if not, the default
  (rifle) clip plays - every variant is a climb of the same class. (The review found the stock example: Dog
  Days' own `Fall_1m` / `Fall_2m` lists of Kane have the same pairs.)
- The off-game test (4.3) tests the file against the READING of section 3, written down as a model - not
  against the game. If the game moves him otherwise than read, the test is no evidence; K2 is.
- Not established: whether stick input does anything during the clip; what the camera does while he rises
  along a wall; fall damage from 253; what the game does when the player dies with the hook's collision count
  held (the count is given back at the next tick - reasoned, not seen).
- Not established (part A): whether a forced low cover is entered at a 2 m wall; the player's distance from
  the face in cover (decides 1M / 2M). Not needed for the plan.
- Not done: the AI heisters' kind-1 links (5.1); edges on the street side (dumpster, then wall: the way back,
  and what the campaign-bank map of re/campaign_fa_bank.md needs at its start); other maps (`LINES` has only
  `M03_FA_A`); finding climbable edges of a whole map by itself; a gamepad key; anything online.
- The build stands on `z_hop\M03`, which fails this night's loot-window rule of `kl_fa_bots.check` (4.2). When
  the loot track delivers a new bank build, run `kl_fa_climb.py apply <that> <new folder>` on it. **(4)** The
  build to run is now `z_climb3\M03`, on `z_cover3\M03` (4.2b), which fails the same rule 7 times - as its base
  does; apply the step again to whatever bank build comes next (a build that has the slots already is refused
  if it is of the first form, left alone if it is of the new one).
