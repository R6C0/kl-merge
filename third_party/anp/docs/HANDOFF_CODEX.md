# ANP hand-over: state of the project and everything we know (11–12 Oct 2026)

Read this first, then `CLAUDE.md`. CLAUDE.md is the running log; this file is the organised summary. Where they disagree, this file is newer: §11 lists the stale parts of CLAUDE.md. Your task list is in `docs/CODEX_PROMPT.md`.

Each claim below is labelled **proven** (seen in the game, or read from disassembly or data), **offline** (built and checked without running the game), or **inferred**. Unlabelled engine facts in §4 come from static disassembly.

## 1. The project in one page
- **Goal:** all 16 story levels of *Kane & Lynch: Dead Men* (DM, 2007), playable inside *Kane & Lynch 2: Dog Days* (DD, 2010). Later goals:
  - DM multiplayer (Fragile Alliance);
  - AI upscaling;
  - first person and a free camera.
- **Engine:** both games use Glacier 1. Both exes are 32-bit, base 0x400000:
  - DD `kl2.exe` (Steam CEG build; never modify it);
  - DM `kaneandlynch.exe`.
- **How it works:**
  - `tools/port_level.py` converts the player's own DM level files into DD-format levels under `<DD>/Scenes/Locations/<ID>/`.
  - The run-time plugin is built by `loader/build.bat` (or `build.sh`) into `build/ANP_Loader.asi` and installed as `<DD>/ANP_Loader.asi`.
  - Ultimate ASI Loader loads it; that loader sits in the DD folder as `dinput8.dll`.
  - Nothing from either game is ever redistributed.
- **Levels:** M01 M02 M03 M03B M05 M06 M07 M08 M09 M09B M11 M11B M12 M13 M13B M14.
  - Build arguments: `M03_B M03B M03B` (`scripts/build_all.ps1`).
  - **M07F** is the funeral cutscene, built with `port_level.py M07F` into `Scenes/CutScenes/M07/M07_A_Funeral.*`. It plays between M07 and M08.
- **People:**
  - **W:** project lead; plays and tests.
  - **The lead:** a local Claude session on W's PC; runs every in-game test.
  - **Helper:** a second local Claude session; runs unattended game tests.
  - **JC:** author of `R6C0/kl-merge` (we use its pinned schemas); credit JC.

## 2. Repo map
| Path | What |
|---|---|
| `tools/port_level.py` | Level converter (entity tree, properties, events, sound, ANM, TEX, graft, validation). Every behaviour sits behind an `ANP_*` switch |
| `tools/prpconv.py` | Property and event relayout (exact, from both exes' schemas). Also `ITEM_MAP`, the PlayerMonitor mapping (`pm_default_map`, `Conv.player_monitor`), `Conv.weapon_damage`, soldiers |
| `tools/scriptconv.py` | Mini-cutscene scripts: sections, actors, merc ids, PIP drop |
| `tools/sndconv.py`, `tools/whdconv.py` | Sound banks: DM SND/WHD into DD layouts with 9 languages |
| `tools/anm_merge.py`, `tools/gunfit.py`, `tools/clipsnd.py` | ANM merge (DD F03 donor plus filtered DM clips), gun seating and bone binding, per-level clip sound ids |
| `tools/graft.py` | Grafts DD L01 menus, HUD and fonts under a new tail group `ANP_Tail` (`ANP_GRAFT_HOST`, code default `tail`); also the hook for `dnd.py` |
| `tools/dmhud.py`, `tools/dmfont.py`, `tools/locconv.py` | DM HUD art into DD OSD slots; DM fonts; LOC fixes |
| `tools/anp_menu.py`, `tools/anp_movie.py` | Front-end menu (Play Dead Men / Dog Days / Dead Dogs); intro movie builder |
| `tools/dnd.py` | `ANP_MERC_DND`: DownNotDead squads for DM mercs. Default 0; never run in game |
| `tools/ovlcheck.py` | Validator: fails any build that moves a DM node |
| `tools/setup_workspace.py` | Fills `work/` (pinned schemas, extracted scenes, stats) |
| `loader/anp_loader.c` + `loader/*.inc` | Loader core and modules: climb, squad, godmode, campaign, cutdiag, d3dshot |
| `scripts/` | `build_all.ps1`, `install_build.py`, `kltest.py`-based test drivers (`smoke_*`, `smoke_chain.py`, `smoke_dnd.py`), `fxmiss_harvest.py`, `hvk_ray.py`, `climb_spots.json` |
| `work/` | Local only, never committed: `scn/{dm,dd}`, `ext/schemas`, `out_*` builds, `gap/` analysis (`gap/PLAN.md`, `gap/entities/prog/blockers.txt`) |

## 3. Where things stand

### Installed on W's PC (20:23): level build `out_rel2` plus loader `out_hp` (built 19:38)
**Proven in game:**
- **Load and survive:** 16 of 16 levels loaded and survived 60 s on an earlier build (`out_all5`). On `out_ovl`, 10 of 14 levels survived a 5-minute god-mode run. The other four crashed: M03 0x8c6bbe, M09B 0xcccccccc, M12 and M13 0x5c8075. Those causes are fixed offline in `out_rel2` (§7), but **only M01 has been run on `out_rel2`**: one 90 s run, clean, with hits of −17 to −37 against 500 HP.
- **Climbing:** DM's W+E free climb at ledges, in 3 height classes. It passed 5 of 5 spots in M01 (`climb.inc`, `ANP_climb.txt` = `live`).
- **Sound:** level audio plays continuously (M01: 81 of 84 s above −50 dBFS, from loopback measurement). That measurement can't tell speech from other sound.
- **Cutscenes:** the M01 intro chain plays (187 mini-cutscenes, 0 dead).
- **Hints and objectives:** the "FOLLOW LYNCH" objective shows, and player-filter trigger boxes fire.
- **Crew orders in M02:** recruit, follow and attack-nearest work (`squad.inc`, `mode=on`).
- **Campaign menu:**
  - Play Dead Men: Continue and Chapters load DM levels; DM saves are kept separate and DD's save is untouched.
  - Intro movie, then M01.
  - Dead Dogs saga: new game, then M01.
  - Funeral chain M07 → M07F → M08.
- **CEG:** a full compare of all 225 hashed ranges ran once, on the 17:08 loader, and found no ANP bytes. The installed 19:38 loader has only the start-up self-check (`CEG: … none`, `old patch sites with stock bytes 8/8`).
- **HUD:** DM weapon/ammo panel and crosshair seen in shots. The "71 slots" plan from `dmhud.py show` is not all observed.

**Offline only (built, never seen in game):**
- non-English DM dialogue;
- vehicle-rout relays and the PlayerMonitor mapping, so the exits are reachable only in the offline model (`work/gap/entities/prog/blockers.txt`);
- the M02 weapon-check bypass;
- the crash fixes in §7 #3–#5;
- chapter titles and difficulty names;
- crew-command hints;
- blanked DD loading-screen subtitles.

### W's latest playtest verdict
Progress needs three DM mechanics that are missing: **rappelling**, **grenades** and **giving/swapping weapons with squad mates**. These are your Tasks 1–3. Their shared test bed is M02 (§8).

## 4. Engine facts

### Nodes and data
- **Node table:** `*(*(0xe0ff90)+0xc)`, stride +4, base +0xc. The object is at node+0x60, the parent at +0x50. Static handle: `0x40000000|idx<<7`.
- **Node order:**
  1. ROOT;
  2. blocks in preorder of group entities (type & 0x100000);
  3. within a block, by slot = prio×8 + basetype;
  4. then entity order.
  - `.oct/.sgp/.rmc/.rmi/.sgd/.hrd/.HVK` bake node indices, so **only ever append at the tail**.
- **Stored 3x3 matrices:** identity is stored as `[0,0,1,0,1,0,1,0,0]`.
- **Property records:** member offset = node+0x10, then +4 to reach the object.
- **PRM chunk table:** at most 73,728 entries.
- **Memory:** a level load allocates scratch, .fxc, .prm and .ANM (each size + 0x60000), then the whole .WAV.

### ANM
- **Clip records:** DM 0x50 bytes, DD 0x68. Bones are remapped by name.
- **DB lookup:** the first DB whose name *ends with* the requested name. The DB map is `ANM_MERGE_MAP` in `port_level.py` (PlayerCharacter→Kane, Lynch_Coop→Lynch, …).
- **The merge is filtered:** only `/Level_Specific/`, `/Movement/Climb/` and the paths a level's scripts or properties name are merged (`port_level.py`, `path_filter`). **New player moves (rappel, grenade, give) need this filter extended, or their clips won't be in the level.**
- **Clip field 11 (+0x2c)** is a **per-level .SND record offset**, not a constant (see §11). `tools/clipsnd.py` re-points it.

### Anti-tamper (CEG)
- kl2 hashes about 85% of `.text` and 66% of `.rdata`. A changed byte ends a menu-started session with `ExitProcess(0x8000dead)`.
- Import slots, `.data` and the heap are not hashed.
- `0xa8e3cb` is a benign Steam probe fault.
- Hardware breakpoints kill the game.

### Player, damage, difficulty
- **Damage formula, DD `0x46ef60` (weapon vt +0x2f0):**
  1. lerp the 4 ammo damages (+0x84..+0x90, DD fields 17..20) over the 4 gun ranges (+0xd4..+0xe0, fields 21..24);
  2. × gun +0xe4 (field 25);
  3. × gun +0x13c (field 37) when an NPC shoots.
- **Damage formula, DM `0x51d820`:** near (+0x7c) to far (+0x80) over +0xcc..+0xd0, × +0xd4.
- **HP:** Normal is 500 (100×5). HP block at player+0xa48 (+4 current, +8 max); AdjustHitPoints `0x6e3400`.
- **Globals:** difficulty `0x156b5f0` (0..3); god switch `0x1535a2c` (.data).
- **Soldiers:** 4 enums + 14 floats (DM 9). Field 7 = health; fields 9..12 = per-difficulty factors.

### Items (weapon giving and grenades depend on these)
- **Item types:** 0 Grenade, 1 TwoHanded, 2 OneHanded, 3 SpecialEquipment. 4 means unbound.
- **Item id:** `0x7597d0` looks the weapon up in the registry at gameMgr+0x15b0 (gameMgr = `*(0xdd265c)`). If it isn't there, it reads the weapon's own `InventoryBinding` event, id at +0x34.
- **Id → type:** `0x8847e0`.
- **`0x49f260` jumps through a 4-entry table.** Type 4 sends it to 0xCCCCCCCC, so no weapon a soldier or the player can hold may be unbound.
- **Duplicate registration** of an item id int3s at `0x7f779e`, so each binding needs a unique DD id.
- **Soldier item removal:** slot 303 `0x7b6b40`.
- **Weapon handle:** the actor's weapon handle sits at `actor+0x7d4` (which slot it is: inferred); the ZSoldier script is at `actor+0x77c`.
- **Table addresses:**
  - weapon-handling anim folders come from the item-enum table at `0x154a650`;
  - the item→HUD-slot table is at `0x154db68`;
  - bullet-hit crash at `0x4c34b3`: bone id byte +0x3e must match the skeleton table.
- **No ids for these DM items:** C4, Claymore and Pushblade map to NoItem. No event outside the equipment library uses them, so they block nothing.

### Player, squad and soldier layout (from `squad.inc` lines 36–40)
- **Player:** P = ZFFPlayer (vt 0xbb45f4).
- **Squad control:** sc = `*(P+0xcd0)`.
  - squad = `*(sc+0xa4)` (+0xc0 count, +0xc4[12] members);
  - receivers at sc+0x18 / +0x1c[];
  - current receiver at sc+0x10.
- **Script:** +0x40 body, +0x6a4 commandable, +0x6e8 EIsMercenary. The soldier script vt is 0xbd0954.
- **Body:** +0x576 life/able, +0x77c script, +0x54→+4 relation.
- **Aim:** target `[P+0xbd4]+0x2ac`; aim point `P+0x27b0`.
- **Handles:** handle→object `0x8ccde0`; object→handle `0x86ca10`.
- **Crew-order calls:**
  - Recruit `0x908040(sc, body)`. DD skips recruiting in no-session mode at 0x615f59.
  - Follow `0x4c3900`.
  - Attack: slot 83 `0x831850` (takes a handle).
  - Defend: slot 79 `0x760e50`.
- **Speech:** speak(id) is `0x763db0` through `[script+0x564]`.
  - ANP levels keep DM's .SND, so the ids are DM ids: 0x21 go there, 0x22 follow me, 0x23 shoot at my mark, 0x2e–0x30 refusals, 0x31 Lynch humming (DD's Follow hard-codes it, which is why it's muted).
  - Pass 0xff for "no voice"; 0 is the pain line.
- **Input:** read from DD's own DirectInput device state as DIK codes (keyboard vt 0xb8f4dc, mouse vt 0xb8f564), with GetAsyncKeyState as the fallback.
  - Bindings: follow 0x02, attack 0x03, defend 0x04, next 0x0f, Shift+Tab previous, middle mouse attack.
  - A tap is shorter than 0.25 s; holding fires at 0.25 s.
  - Tests drive it through `ANP_squad_cmd.txt` (`squad.inc` lines 44–48, 89–93, 406–417, 913–942).

### PlayerMonitor
- **DD raises only some events:** the dispatcher `0x589600` raises 0–15, 23, 24 and 27–32. **16–22, 25 and 26 are never raised.**
- **kl2 has no ZInventoryDisplay or ZInventoryWheelInput classes.** DM's events 14, 15 and 17 come from the inventory wheel, 19 from the inventory display update, and 12/13/20 from grenade throws (20 repeats).
- **Current defaults (`prpconv.pm_default_map`):**
  - DM 5–11 → +4;
  - DM 19 → DD 28 `eON_MOVEMENT_CONTROLS_USED`, one-shot (a stand-in that checks once, on the first move);
  - DM 21 → DD 27 `eON_HEALED`;
  - 12/13 → 16/17, 18 → 22 and 20 → 26 land on dead events and are dropped.
- **Overrides:** `ANP_PLAYERMON_MAP="19=28!,12=30"` remaps (`+` joins, `!` one-shot, `~` repeat).
- **Candidate stand-ins** (inferred): DD 30 `eTHROW_THROWABLE` (raised at 0x6d0c66) for grenade throws; DD 23 `eRELOAD_REQUIRED` for DM 18.
- **The monitor table holds 20** (`0x8ef000`) with **no overflow guard**: the 21st registration writes out of bounds. The build logs the count per level.
- **Player filter:** numbered in both games, but with the names swapped. In DD, `eONLY_KANE` (1) is co-op player 2, which never fires in single player (`ANP_PLAYERMON_P2=drop`).

### Mercs, buddy, wounded and revive
- **Every friendly soldier is mission-critical in DD.** Init `0x615c90` sets:
  - +0x6e8 = 0xd;
  - +0x512 = 1;
  - +0x513 = 1, through slot 57 `0x725b20` (skipped when relation == 1).
- **+0x513 lifecycle:** cleared at script init (0x7cfbba); **restored from the save on checkpoint load** (0x5bf577).
- **Death path:** `0x8fd470` → `0x6d2500` → slot 58 reads +0x513 → MF_01_MercDead → mission-failed reload. That this reload replays the level intro (the M09 "loop") is inferred, strongly.
- **Merc list:** count at `[0x1548fd8]`, scripts at `[0x1548fdc+4i]` (i < 16).
- **DM has the same fail rule** (DM +0x106; 0x721c2e / 0x70a1a0), but first puts mercs **wounded**:
  - life byte ZActor+0x536 = 2, with the ZWounded task;
  - the player heals within 200 cm with ZFFActionHealWounded;
  - bleed-out = 1024 × difficulty record +0xc;
  - that the mission fails at expiry is inferred.
- **DD's heal:** heal scan `0x7aaaf0` (170 cm, action 0x12), target at player+0xd34. It needs player+0xd30 and candidate+0x2940, so it looks co-op-partner only (not verified for the single-player buddy).
  - ZFFActionHealWounded: ctor 0x907300, vt 0xbb54fc; action factory ZFFPlayer 0x839740, case 0x12.
  - DD life byte: ZActor+0x576.
  - DD's ZWounded slot 2 (0x865180) ends in a death/ragdoll path; no bleed timer was found.
- **DD DownNotDead** is SquadModifier enum 14 (Force 1 / Prevent 2).
  - Handler 0x803530 writes script+0x124 (read at 0x919840 and 0x91fe45).
  - L10 GalleryCampers is the only Force example.
  - Expected (not observed): downed soldiers get up by themselves.
  - DD L08/L09 place `OnDownNotDead` cameras for the player's down state.
- **Buddy:** DM's buddy (Merc_04, Lynch) is DD's 'Kane' buddy (merc value 1) at gameMgr+0x4cf0. It registers about 250 ms after squad init.
- **Recruiting:** the intro's `playermode 1` blocks gameplay input, which delays squad.inc's recruit.

### Classes and gates
- **ZAppendage:** needs a ZLNKOBJ link target. Init checks for one, but **Load (slot 22, 0x833660 → 0x8c6b70) doesn't**, and Load runs on every checkpoint restore.
- **ZPlayerAction (use prompt):**
  - +0x50 text key, +0x54 enabled, +0x58 use-geom path;
  - Init slot 13 `0x4c4de0` registers only if gameMgr+0x828 ≠ 0.
- **Game state:** `[0xe0e644]` counts game-state transitions. Going back to InGame re-fires AIMonitor's level-start list.
- **Mini-cutscene binder** `0x4b64e0`. In cutdiag, "+35 dead" means a section track didn't bind.
- **RelayMessageList** layout is `[in-msg, out-msg, container, delay]`. kl2 `0x6e3cb0` fires it on a matching message.

### Climbing (the model for rappel)
- **DM:** `ZFFPlayerMovementClimb` (id 11), heights Low 25–120, Medium ≤170, High ≤220. Any collision with flag 0x20 is climbable.
- **The DD loader climb works.** Entry points (`climb.inc` lines 7–8, 19–23, 74–90):
  - VaultOver vt 0xbb5188 (slots 2 Start, 4 Update, 5 End, 10 AnimEnd replaced on a loader-owned copy);
  - clip by name 0x426890; clip event frame 0x4a75d0; root motion 0x5a5030;
  - player play vt+0x204; create action vt+0x384; start action vt+0x370; warp vt+0x208;
  - teleport 0x82cc40; pose 0x857110; camera 0x798d00;
  - raycast `*(0x138c868)` vt+0x2c.
- **What failed:** the scripted mini-cutscene climb (`ANP_CLIMB`, `climbs.py`) climbed twice, went through a wall and threw the player onto a roof. It's off. **Don't build rappel that way.**

### Where loader code runs
- **Per-frame gameplay code** runs from climb's frame hook. It's an import-slot hook on `steam_api!SteamAPI_RunCallbacks`, filtered to the gameplay call:
  - `climb.inc` about line 731: `if (ra == CL_RCB_RA) { climb_frame(); squad_frame(); }`
  - squad.inc reuses climb's helpers: `climb_guarded`, `cl_ray`, `cl_pose`, `cl_sys`, `cl_curT` (plus `god_writable` from godmode.inc). New modules (give, rappel) should be included after climb.inc and called from the same place.
- **Campaign, cutdiag and godmode** tick from the `PeekMessageA` hook (`anp_loader.c` lines ~898–900 and ~1720–1722).

### Menu, routing, movies
- **Menu XML:** delivered through the MSVCR90 `fopen` hook plus a copy of the file system's vtable at `[0xdd263c]` (+0x34, +0x68).
- **Scene routing:** a `strncpy` import hook at dst `0x156b6f5`, borrowing chapter-table entry 12.
- **Movies:** must be loose `.bik` files under `<DD>/Movies/`. A .bik that exists only inside a zip crashes at 0x4df0b8.

## 5. Converter switches (code defaults, all checked against the code)
Each switch's old value gives byte-identical output.

| Switch | Default | What it does |
|---|---|---|
| `ANP_WEAPON_DMG` | 1 | Weapon/ammo damage fields by meaning. Field 37 (NPC factor) stays at DD's 1.5; `ANP_WEAPON_NPCDMG=<x>` overrides it (DM has no such factor; W hasn't decided) |
| `ANP_ITEM_EXACT` | 1 | Gas launcher → DD 53, incendiary → 58. DM variants get spare ids: USPCarry → SigSauer226, USPLight → SW_MP45, MP5Light → UMP_SBR, M4Light → AK47, Rem700Silenced → Type88_Scoped, RPGInaccurate → RocketLauncher_Hind. **RPGInaccurate is still dropped as a duplicate in every level, so it stays unbound** |
| `ANP_APPENDAGE_LINK` | 1 | Drops Appendage events whose target was neutralised |
| `ANP_ANM_CLIPSND` | name | Re-points clip sound ids |
| `ANP_VEHICLE_RELAY` | exit | RelayMessageList 'AITrigger' in place of dropped vehicle routs on the exit chains of M01, M03, M07, M09B and M11 |
| `ANP_PLAYERMON` / `ANP_PLAYERMON_P2` / `ANP_PLAYERMON_MAP` | 1 / drop / empty | PlayerMonitor mapping (§4) |
| `ANP_BUDDY_WEAPONFILTER` | pass | DM WeaponFilter layout is `[actor, weapon, bool, pass container, fail container]`. Filters on `ROOT\Lynch` or `ROOT\Lynch_COOP` with bool 0 become a RelayMessageList to the pass container. Bool-1 filters (pick a cutscene by his gun) stay. A stand-in until weapon giving exists |
| `ANP_SND_LANGS` | 1 | 9-language SND/WHD |
| `ANP_LOADER` | silent | Blank DD loading-screen subtitles |
| `ANP_CHAPTER_TITLES` / `ANP_LOC_EXTREME` / `ANP_BRIEF_COMMANDS` | 1 / plus / 1 | Chapter titles; difficulty names; crew-command hints (they name keys 1/2/3/Tab) |
| `ANP_SMB_FIX` | 1 | Squad-modifier enum family fix (supplement `tools/dd_enums_extra.json`) |
| `ANP_STATIC_SHADOWS` / `ANP_MERC_DND` | off / 0 | Experiments, never run in game |
| `ANP_NEUTRAL_SLOT`, `ANP_GRAFT_HOST` (tail), `ANP_VALIDATE` | on | Node-order safety; leave them on |

Older switches (`ANP_MERC_IDS`, `ANP_BUDDY_KANE`, `ANP_DROP_PIP`, `ANP_SCRIPT_RESTORE` (keeps the `throwgrenade` script command), `ANP_ECPS_SWAP`, `ANP_PFILTER_SWAP`, `ANP_PA_GENERIC`, `ANP_BRIEFINGS`, `ANP_OBJECTIVES`, `ANP_ALLOC_POOLS`, `ANP_ANM_BACKFILL`, `ANP_CP_INDEX`, `ANP_CAR_CHILD_EVENTS`, `ANP_SND_T1`, `ANP_DM_HUD`, `ANP_DM_FONTS`, `ANP_GUNFIT`) are documented in CLAUDE.md.

## 6. Loader modes and hook files (in the DD folder)
| File | Module | Values |
|---|---|---|
| `ANP_climb.txt` | climb.inc | `off|dry|live` + options. **No file = `live`** (release default, 14 Oct; ANP levels only). An unknown mode word = `dry` (never undoes an explicit `off`); an unreadable file keeps the previous config and is retried |
| `ANP_squad.txt` | squad.inc | `mode=off|probe|dry|on` (**no file = `on`**, release default, 14 Oct; ANP levels only), key options, `recruit=always|start|off` (default `always`), `critical=keep|clear`. Same unknown-word / unreadable-file rules as climb |
| `ANP_god.txt` | godmode.inc | Test only: `1` no damage, `2` can't die, `heal`, `mask`, `off`, `log` (god OFF, HP changes logged) |
| `ANP_campaign.txt` | campaign.inc | Menu, routing, saves, `IntroMovie=1` |
| `ANP_cutdiag.txt` | cutdiag.inc | Cutscene census. Its heap scan stutters, so tests only |
| `ANP_sound.txt`, `ANP_guards.txt` | core | Sound serving and VEH guards. `legacy` brings back the old code patches; never ship it |
| Hook files | core and modules | `ANP_shot.txt` (D3D screenshot), `ANP_tp.txt` (`x y z yaw` teleport), `ANP_autoload.txt` (`M01 1 12`), `ANP_load.txt` (scene id), `ANP_endlevel.txt`, `ANP_quit.txt`, `ANP_where.txt`, `ANP_nodes.txt`, `ANP_gui.txt`, `ANP_squad_cmd.txt`, `ANP_cstate.txt`. `ANP_guinames.txt` freezes the game for about 20 s |

Log: `<DD>/ANP_log.txt`, one prefix per module (`climb:`, `SQUAD`, `god:`, `campaign:`, `cutdiag:`).

## 7. Bugs found and fixed: cause → fix (patterns to watch for)
1. **Silent sound (proven fixed).** DM SND type-1 records are 0x30 bytes, DD reads 0x40, so every volume read was 0%. Fixed by re-laying out the records.
2. **One bullet killed the player and the enemies (proven fixed: M01, hits −17 to −37).** The exact relayout matched fields by *position*, which put DM's rate of fire into DD's damage multiplier. Fixed with `ANP_WEAPON_DMG`.
   - **Lesson:** a positional relayout is dangerous wherever the two schemas differ in length.
3. **Calls to 0xCCCCCCCC (offline fix).** Seen in M01 fireat, M09B tear gas and W's weapon swap. Unbound items dropped as duplicates through `ITEM_MAP`. Fixed with `ANP_ITEM_EXACT`, except RPGInaccurate (§5).
4. **M03/M03B crashed on every checkpoint restore (offline fix).** An Appendage linked to a neutralised ZHavokCar. Fixed with `ANP_APPENDAGE_LINK`.
   - **Lesson:** any kept event whose target was neutralised can crash on a code path that doesn't check. Other suspects from the audit:
     - AIDWrapper, Activate/DeactivateGeom and PositionLightControl on DM-only types (M03B, M05, M08, M09B, M11B);
     - RelayMessage to a ZHavokCar in M07.
5. **M12/M13 crash at 0x5c8075 (offline fix).** Donor ANM clips carried F03 sound offsets. Fixed with `clipsnd`: 0 bad ids in all 16 levels.
6. **Exits unreachable (offline, model only).** M01/M03/M07/M09B, probably M02/M11: exit gates waited on dropped vehicle routs or unconverted PlayerMonitors. Fixed with the relays and the monitor mapping. M03B still needs the van chase.
7. **M02 soft-lock at the guns step (offline bypass).** Caused by DM's give mechanic. Bypassed with `ANP_BUDDY_WEAPONFILTER`; Task 1 is the real fix.
8. **M05 dead cutscenes (4 of 7, offline fix).** Weapon proxies pointed at the unbound USP_Carry; fixed by #3. The other three (`MiniCut_Idle` ×2, `MiniCutDenyAccess`) have no known cause.
9. **Earlier fixes (CLAUDE.md):**
   - vehicle-only events on neutralised owners;
   - PIP sections (int3);
   - duplicate pool names;
   - node shifts (`ANP_NEUTRAL_SLOT`);
   - the settings crash at 0x900ff8;
   - swapped player-filter numbering.

## 8. M02: the test bed for Tasks 1–3
M02's exit chain (`work/gap/entities/prog/blockers.txt` lines 41–56, 217–312) runs:

`020_GettingGuns` → `025_CoverPractise` → `030_GrenadePractice` → `RappelPractice` → EndOfLevel SceneChanger (node 591)

- **Guns:** `KaneMonitor_Weapons` (node 848) and `KaneMonitorAltWeapon` (node 850), both list 19. They feed the WeaponFilters "Lynch holds `Shotgun_Remington_870`" and "Lynch holds `Gun_Taurus_01`", which lead to `GeomActivator_PickupP90Action` and `GeomActivator_PickupUsp`.
- **Grenades:**
  - `PlayerAction_PickUpGrenades_Kane`;
  - `GeomActivator_ActionPickUpLGrenades`;
  - `023_MC_KaneEquipsKaneGrenades`;
  - `060_MC_KaneInstructGrenade`;
  - `Filter COOP!Grenades!SP_StartGrenade`;
  - `PlayerMonitor_KaneGrenades` (node 623, DM lists 12 and 13, DM `eONLY_KANE`). **These lists are dropped today**, so this gate doesn't fire in our build.
- **Rappel:**
  - `TriggerBox_StartRappelCut`;
  - `RappelPoint!RappelBox` (node 579);
  - `CheckPointSaveByRappel`;
  - `MiniCut_EndOfLevel`.

**RappellingBox census:** kept, and reached wherever DM reaches it: M02, M03, M09, M11B, M12 ×3, M13 ×2 (`prog/blockers.txt` line 98).
- No other box is on an exit chain.
- The boxes target `RappelFacingDir`, plus callbacks like `RappelCB_BeforeVertigo` and `RappelCB_Leave` (M09 node 220).
- M09 also has a `RappelCheckPoint`.
- M03's `RappelPoint_01` TriggerCounter loses a sender (soft).

## 9. Open issues (ranked)
1. **W's blockers:** weapon giving, grenades and rappelling (Tasks 1–3).
2. **Merc death fails the mission at once.** This is DD's rule and DM's too, but DM wounds them first and lets you revive them.
   - `squad.inc critical=clear` exists for tests.
   - `ANP_MERC_DND` is untested.
   - The faithful fix is a loader revive.
   - **Test pitfall:** in M09 a merc death replays the intro every 25–45 s. Use `critical=clear` there.
3. **M03 relays fire too early.** They skip the walk to the van and `WoundedFilter_GetIntoVan`. Proposed by the lead's review: per-relay delays and driving the get-in relay from WoundedFilter's OK container. The entity numbers for a walk-up gate are unverified. The M03 van entities in `prog/blockers.txt` are 11640/11639.
4. **M03B can't be completed physically.** It needs the van chase. A teleport fallback through DM's own BeamPos entities was proposed in a paused session. The entity names are **unverified**; check them in `work/scn/dm/M03B*`.
5. **Neutralised gameplay systems:** vehicles (stock DD never uses ZHavokCar 0x2000d4; it uses ZAnimatedVehicle 0x2000d8), mounted MGs (M11/M11B/M12), crowds (M05/M08/M11B), plants, ropes (0x200499) and rain.
6. **HUD:** no DM health arc, inventory disc, crew-order display or objective radar.
7. **Presentation:**
   - lighting: DM AO is baked in `.prm` + `.TEX`; 0x200110 is static shadow geometry, not lightmaps;
   - DM loading screens;
   - credits after both endings;
   - the pause menu is unverified.
8. **NPC damage factor 1.5:** may make enemies stronger than in DM.

## 10. Testing (you can't run the game; write test plans)
- **How the lead tests:** `scripts/kltest.py`-based drivers with a GAME_LOCK. Hook files are backed up and restored, screenshots come from the D3D back buffer, and audio is recorded by loopback. Installs go through `scripts/install_build.py <out> all` (backup, sha1 checks, rollback).
- **A test plan names:** the level; the position (`ANP_tp.txt` coordinates from `scripts/hvk_ray.py`-style data); keys; mode-file contents; and the exact log lines for pass and for fail.
- **Pitfalls:**
  - Enter skips cutscenes.
  - Mouse clicks don't reach the game (DirectInput).
  - An idle player dies about 60 s after M01's intro.
  - God mode doesn't stop fall deaths.
  - The M09 intro loops when a merc dies (§9).

## 11. Stale or wrong statements elsewhere
**CLAUDE.md:**
- "All seven of ANP_Loader's code patches lie in hashed ranges": obsolete, the loader is patch-free.
- "kl2.exe is not large-address-aware": W's copy is LAA (KL2Fix). JC warns the engine tags pointers with the top bit; no problem seen.
- "Loader builds … not run in game" and the climb.inc note "not yet run in game": both work live now.
- "Where M01 stands (10 Oct)": history only. Its "isolate the sound bug" steps are obsolete.
- Graft "under the nearest plain ZGROUP ancestor": now under the tail group `ANP_Tail`; the code default is `ANP_GRAFT_HOST=tail`, not "new".
- The intro movie and funeral "NOT yet run in game", and the SceneChanger chain "untested": the out_fun tests passed 5 of 5, including M07 → M07F → M08.
- CListUser "not yet re-checked in game": M01 long play logged none.
- Crew-command hints "dropped until crew orders land": now on (`ANP_BRIEF_COMMANDS=1`).
- "Planned: squad.inc critical=": implemented (§12).
- "Only M01 is built so far (out_hp)": `out_rel2` has all 16 levels plus M07F.
- Pipeline table "6→10 languages": it's 9.

**Elsewhere:**
- `docs/ANM_FORMAT.md` / `tools/anm_lib.py` say clip field 11 is "equal in DM/DD": wrong, it's a per-level SND offset.
- `findpos.py`-style composed positions are wrong; don't use them for teleports.

## 12. State of the repo you were given
- **`loader/squad.inc` `critical=keep|clear`** (lines ~78–88, 311, 441–466) is implemented. It was compiled into `build/ANP_Loader.asi` at 20:25, but it is **not installed, not reviewed and never run in game** (Task 4).
  - With `clear`, it must re-clear after every scene load and every change of `[0xe0e644]`, because a checkpoint load restores +0x513 from the save.
  - DM has the same fail rule, so `clear` is a test tool or interim choice, not the faithful behaviour.
- **Two local sessions were stopped mid-run before you started** (rappel/grenade/give, and M03/M03B). `squad.inc` is the only file they changed after the last commit. Ignore any references to `work/out_m03` or `work/out_mech*`; those don't exist in the repo.

## 13. Pitfalls we hit
- **Builds:** never run two builds at once (shared `work/_tex_out.bin`). A full build set is about 3 GB and the disk filled up once, so delete parity builds after use.
- **Logs:** some build logs are UTF-16 (PowerShell redirection).
- **Snapshots:** some modules put a relative `tools` folder on `sys.path`, so run snapshot builds from inside the snapshot.
- **kl-merge:** use only commit `8466319` (`re/schemas_dd.json`, `re/schemas_dm.json`, `tools/dd_enums.json`). Without the schemas the converter stops; never ship the `ANP_EXACT=0` fallback.
- **KL2Fix** (W's mod) writes 17 CEG-hashed bytes itself; expect them in any in-memory diff.
- **Discord's overlay** has crashed the game before.
