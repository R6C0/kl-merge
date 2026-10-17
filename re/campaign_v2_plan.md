# Campaign v2 plan: Hot Coffee v2, A Walk in the Park v2, Hasta (2026-10-17, audit track; OFFLINE, NOTHING BUILT OR RUN)

Source: re/campaign_fa.md and campaign_fa_park / _havana / _club / _tooling (figures quoted from them). Model: Retomoto (start outside, blast, fight, join, street, van).
Hot Coffee v2 (M01_A) was NOT studied by campaign_fa*.md: its numbers are UNMEASURED.

## 1. Files that exist (Dead Men Scenes\Locations, measured by ls)
| level | zip | .WAV | other |
|---|---|---|---|
| M01_A (Hot Coffee v2) | M01A_Main.zip 138.9 MB | 17.3 MB | WHD, LS_* load-screen sound, Loader_Sequence.zip |
| M06_A (Park v2) | M06A_Main.zip 119.5 MB | 14.0 MB | same set |
| M11_B (Hasta) | not listed in this check (listing showed M11_A: 145.6 MB zip, 14.2 MB WAV); the same folder family exists | | |
Also present: M01_FA_A, M02_FA_A, M03_FA_A, M06_FA_A (the FA maps already on the tab), M02_A, M03_A/B, M05_A, M07_A, M08_A, M09_A/B, M11_A/B, M12_A, M13_A/B, M14_A.

## 2. Budgets (limits from campaign_fa.md)
Chunk table 73,728 entries (tools refuse above 69,632); textures 4,096; materials 2,048; largest loaded .HVK 5.0 MB; .prm served from the 128 MiB reserve (Retomoto tab 79.9 MB); 26,991 entities have run.
| map | chunk table as built / finished | .prm | effort (Retomoto = 1.0) | state |
|---|---|---|---|---|
| Park v2 M06_A | 53,960 as built, 52,433 with the pre-pass cures, 54,263 finished with 8 masks | 79.5 MB as built, 35.9 lightened, 58.0 finished | 0.45 | ready to author; 52 % of the walk is the existing FA park mesh |
| Hasta M11_B alone | 74,454 as built (726 over), 58,992 with wardrobe + compaction, 60,902 finished (8 masks) / 66,318 (12) | 84-93 MB | about 1.0 (0.8-1.2) | needs compaction (a compacted level has never loaded); four geometry switches; no opening blast object; no van line |
| Hot Coffee v2 M01_A | UNMEASURED | UNMEASURED | UNMEASURED (GUESS 0.4-0.6: a street level, zip size close to the park) | one TILU=MIRRORED material (slot 615, 1 binding) like the club: write TILED |
Measurement step for M01_A: `python tools/kl_maps.py what M01_A`, then `python tools/kl_maps.py one <out> F07 M01_A --campaign` and read the chunk-table / .prm / texture counts.
Blocked: both Havana chapters in one map (111,853), Havana M11_A alone (not worth it), park as a change to the existing tab map (M06_FA_A's mesh has no polygon above y 720).

## 3. Design (Retomoto's model)
- Hot Coffee v2: GUESS (no study): start on the street outside the diner as the crew steps from the van, a short blast or door breach as the round starts, fight into the diner and the back warehouse (the FA map's loot: cash register, warehouse people), join = leave the building to the street, escape = F07's key-framed van on a road lane. Needs the level read (places, doors, civilians) before any design; the existing FA M01 gives the loot objects and the van lane test.
- Park v2: start at the existing FA start region, the campaign park's extra walks/paths replace the FA mesh; loot at the stops the FA map uses (four stops), escape by helicopter or van lane from the campaign layout; follow campaign_fa_park.md's van arc notes (curved drive played on Hot Coffee).
- Hasta: M11_B only. Start at the chapter's arrival, fight through the compound, loot from the chapter's props (no opening blast object exists: use a trigger-driven beat), escape: author a van line (none exists) with `kl_map_escape.van_plan`; four geometry switches (doors/gates) built open as for the bank.

## 4. Tool steps (per map; all exist, order from campaign_fa_tooling.md)
1. Prerequisites once: FFCoverList into kl_maps.PASSIVE; author= as a module in kl_graft / kl_maps; a van plan from way points; doors open at build time.
2. `kl_maps.py one <out> F07 <level> --campaign` (graft onto F07's systems), `kl_graft.py lighten` (.prm/.TEX/.fxc/.WAV), kl_chars wardrobe (+ `compact` for Hasta), kl_fa_author (spawns, loot, bounds, escape), kl_map_escape (van lane), kl_map_ai, kl_fa_bots(+_dyn), kl_fa_carfx, kl_fa_climb (rope builds for the free climb), kl_hud, kl_fa_talk. Checks: kl_impact 0, audit, van-check, kl_expansion tree.
3. Menu: page 3 exists (campaign maps); the page's element table has margin about 4: a new entry needs room made first (see CLAUDE.md, the overflow of 5,096 slots).
4. Stream file: new music needs PC_Def.str changes (owner's word, 1.8 GB file).

## 5. Risks
- A compacted level has never loaded (blocks Hasta; prove with the fake-fix pair x_chunks/retomoto_wardrobe vs _compact first).
- .prm over 90 MB trips the allocator (crash 0x8e5bbd); Hasta is 84-93 MB: needs lighten.
- Climb/rope clips in the .ANM and 128-byte entity pool limits; unseen live for any of the three.
- Hot Coffee v2 is unmeasured, so every number for it is a GUESS.
- Room fix-up (kl2 0x48e910) and gate tables: campaign rooms must keep their 0x74-byte gate records (kl_rooms/gate conversion).

## 6. Order
1. Park v2 (0.45, measured, ready). 2. Measure M01_A (one command), then Hot Coffee v2 if under about 0.6. 3. Hasta last (needs the compaction proof and a van line). Existing campaign_fa order has the bank, club and prison before these; this plan does not change it, the owner's three picks slot in after the bank/club.

## Addendum (fix round 2026-10-17): Hasta file sizes and what is a guess
Measured from the Dead Men Scenes listing (Locations/M11_B): M11B_Main.zip 171,865,702 bytes (163.9 MB), M11B_Main.WAV 14,085,504, .WHD 1,117,088, Loader_Sequence.zip 351 KB. M11_B's zip is larger than M11_A's 145.6 MB, so the Hasta cost row (about 1.0 of a Retomoto) is not lowered by the file size alone.
GUESSES in this plan, plainly: the Hot Coffee v2 design (section on M01_A) and the Hasta design (start, loot beats, van line, geometry switches built open) are the author's proposals with no level reading behind them; every Hot Coffee v2 number is unmeasured. Only the park v2 and Hasta entity/chunk counts come from re/campaign_fa*.md studies, and none of it was loaded in the game.
