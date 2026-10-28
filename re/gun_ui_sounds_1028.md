# T5: gun UI and sounds, Arcade vs online (static research, 2026-10-28)

Static only: no launch, no bench. CERTAIN = seen in code, log or file contents. GUESS = inferred, needs a bench.

## 1. What MP45 is
CERTAIN. The S&W MP45 pistol (HG_SW_MP45, item 1, shop row 7, HUD name "SW MP45", stock shop text "SM45"). It plays the
HG_DesertEagle_Shot_01..03 records and is the loudness reference (head RMS about -2.8 dBFS). Sources: re/gun_sounds.md.

## 2. Sound chain (same online and in Arcade)
- CERTAIN: `<gun>#def` has 13 slots. Slot 1 = shot_npc#set (group volume 0.35, "heard from others"), slot 4 = shot_player#set
  (0.70), slot 0 dry fire, 5 shell drop, 7 pick up ammo, 8 weapon change. Both sets point at the same three #sound objects.
- CERTAIN (re/sound_online_1026b.md): online loads the same banks as Arcade, so group volumes are equal. The loudness passes
  (kl_gunsnd_match 1024c, kl_gunsnd_all 1024n, gunraw/fxraw 1025, kl_sndonline sndon/sndon2 1026) are global, per level zip.
- Each peer plays from its own local files. CERTAIN by design.
- GUESS: a remote human's shot uses the npc set (0.35), so it is quieter than your own (0.70) online. In Arcade the AI heisters
  and cops are the only "others". Which set a remote human's shot uses was not traced.
- GUESS: friends' PCs without the patched banks sound stock, so "online sounds differ" is partly an install problem.
- sndon2 1026b is staged at C:\kl_build_1024\sndonline_1026b, not installed.

## 3. Differences found
| # | Area | Arcade | Online | Cause | Cert |
|---|------|--------|--------|-------|------|
| 1 | Shop rows 13,16,32,35 (HK69, TYPE 81, REM 700, MINIMI) text and picture | Swap relabels the hand-over to the baked gun | klshop_tick returns at `if (kl_online()) return;` (klhook/klshop.c ~180), stock carrier gun is handed over, but the baked name/picture still shows | Names and pictures are baked into .LOC/.TEX on every DD01-09 and DM map except DM07 and DD10 | CERTAIN |
| 2 | DM07 and DD10 | default Swap runs, text unbaked, mismatch also in Arcade | same | never baked | CERTAIN |
| 3 | Gun looks (Dead Men model on DD gun) | baked Shown=1 for 29,30,31,27,23,8 (checked DD01, DD09, DM01, DM07, DM09) | same baked look | klg_tick switching (Guns page) is Arcade-only (klgun.c ~408-409: mode != 4 return, kl_online() return) | CERTAIN |
| 4 | HUD dial name | klg_look_name from klg_lk, filled by klg_publish at level open (baked names) | klg_publish runs in klg_level_open path, the dial names the baked look | same; the dial uses klwd_names (47 entries, pictures 58..104) | CERTAIN for the publish path, GUESS that the dial draws identically online (not traced) |
| 5 | Remote shot loudness | n/a | npc set 0.35 | see section 2 | GUESS |
| 6 | Friends' installs | n/a | stock banks | no sound passes | GUESS |

## 4. Fixes (every one an ini toggle, "(recommended on/off)")
1. Online Swap (value 1). New key in KLHook.ini [Shop] `OnlineSwap=0|1` ("Online gun shelf matches Arcade (recommended on
   once benched)"). Port klshop Swap to online through the page II relabel machinery (klshoppage_online.c: OnlineApply,
   OnlineEarlyMake, the pool relabel at [0x168e96c], 12-byte entries). The four requirements are in
   re/online_arcade_gaps_1027.md. Medium risk (pool relabel on a client).
   Cheap fallback `OnlineSwapText=1`: kllocname.c runtime override shows the stock text online for the rows that are not
   handed over. Low risk, honest, but hides the baked picture only if the .TEX is also swapped (GUESS).
2. DM07, DD10: bake the shop text with kl_hud_shop.py / kl_shop_swap.py, or give their KLGuns.ini an empty `Swap=` so Arcade
   and online agree on stock. Low risk, file-only. Map toggle: none, per-map ini line.
3. Sound: trace which set a remote human's shot uses (GUESS today). If npc, add `[Sound] RemoteShotVolume=0|1`
   (recommended on) using vtable 0xb9a3ec slot 35 at 0x402000 (re/gun_sounds.md section 4, GUESS). Medium risk.
4. Document that every peer must run the sound passes (Nexus pack: build on the player's PC).

Mod Options rows: add "Online gun shelf (recommended on)" and "Remote shots as loud as yours (recommended on)" beside the
existing [Shop] and [HUD] LookNames rows in tools/mod_options.md.

## 5. Bench recipe (two seats, kl_solo_test, --owner-away if owner away)
Stage KLShopPage.ini into solo/<TAG>/inst1+2 (kl_solo_test does not copy it). The ini [Script] replaces the bench script,
edit the wait line in place.
1. Host DM01 and DD01 online, 2 seats, Arcade run first as reference.
2. Both modes: open the Buy Weapons list, screenshot rows 7, 13, 16, 32, 35: text, picture, price.
3. Buy each, check the gun held, the HUD dial name, and `klog` lines "guns: names for the HUD dial".
4. Fire MP45 on seat 1; record seat 2's audio (loopback) and compare RMS to seat 1's own shot. Expected equal-ish.
5. Repeat on DM07 and DD10. PASS = online equals Arcade for every item, 0 faults.

## 6. Open questions
- Which sound set does a remote human's shot use (needs a trace or the bench audio compare)?
- Should the online Swap be the full relabel, or only the text fallback until the relabel is benched?
- DM07 and DD10: bake or empty Swap?
- Does the dial (klhud_weapon.c) draw online identically? Not traced.
