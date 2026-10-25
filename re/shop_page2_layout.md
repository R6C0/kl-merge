# Shop page 2 layout: which spare item id hosts which gun

2026-10-25. Source: `tools/kl_spare_survey.py <map zip> [--spare|--json]` (read only; run on stock F01 =
DD01 and on the live DM01 `KLExpansion\Maps\DM01\F01_Main.zip`; F06 spot-checked for AI use). Owner rules:
page 1 = exactly the stock Dog Days guns; page 2 = Dead Men guns + PD2 AKM + HK69/Minimi/Rem700/Type81; AI loadouts
are not changed; SMG-model guns may sit on rifle carriers but then the page-2 tab must read differently.
Everything marked GUESS is untested live (the page-II hand-over itself is still unproven live).

## How a page-2 gun is composed (recap)
Carrier ROW (price, rank, stars, ammo column, tab/category) is independent of the HOST ITEM ID. The host id's
template supplies model, sound, stats, clip, hold folder and ammo node. The hold folder follows the template's
InventoryBinding enum, so it cannot be changed without changing the id: a host id fixes the arm/reload animation
class. Clip lives in the ZFFItemTemplateAmmo node the weapon points at (weapon field 18, ammo field 15), not in the
weapon template.

## The table (DM01 live zip; stock F01 has the same ids/holds/clips/ammo nodes, differences in the AI column below)
slots = slot count of the hold folder in the Swat_02 set (a real folder has 29..57, the shield pistols 3).
"ammo shared" = the ammo node is also used by a page-1 template (do NOT edit it in place; re-point instead).

| id | template | hold folder | class | slots | clip | ammo node | sound def | model root shared with | AI (F01 / DM01) |
|---|---|---|---|---|---|---|---|---|---|
| 33 | Rifle_Type81 | rifle_type81 | rifle (WT_RIFLE) | 50 | 30 | own | rifle_ak47 (DM01: AKM repoint) | none | 0 / 23 (F06 1, F09 1) |
| 35 | Rifle_Type88_L09_NPC | rifle_type88 | rifle (WT_RIFLETYPE88) | 50 | 5 | Rifle_Type88, SHARED with 34 (page 1) | rifle_type88 | 34 (same model root) | 0 / 0 |
| 38 | Rifle_Type95_L09_NPC | rifle_type95 | rifle (WT_RIFLETYPE95) | 48 | 30 | own (Rifle_Type95_L09_NPC) | rifle_type95 | 37 (same root; own Ground node) | 0 / 0 |
| 40 | MG_GP_Type88 | mg_gp_type88 | mg | 46 | 150 | own | mg_gp_type88 | 41-44 | 0 / 0 (DM09 1, DM11B 3 NPCs per earlier census) |
| 41 | MG_GP_Type88_L09_NPC | mg_gp_type88 | mg | 46 | 150 | own | mg_gp_type88 | 40,42-44 | 0 / 0 |
| 42 | MG_GP_Type88_L09_Heli | mg_gp_type88 | mg | 46 | 150 | own | mg_gp_type88_l09_heli | 40,41,43,44 | 0 / 0 |
| 43 | MG_GP_Type88_L09_Heli_Player | mg_gp_type88 | mg | 46 | 200 | own | mg_gp_type88 | 40-42,44 | 0 / 0 |
| 44 | MG_GP_Type88_L10_Heli | mg_gp_type88 | mg | 46 | 150 | own | mg_gp_type88_l09_heli | 40-43 | 0 / 0 |
| 45 | Mg_Minimi_SPW_L09_Heli_Player | mg_minimi_spw | mg | 35 | 150 | own | mg_gp_type88_l09_heli | 46,48 | 0 / 0 |
| 46 | Mg_Minimi_SPW_L10_Heli | mg_minimi_spw | mg | 35 | 150 | own | mg_gp_type88_l09_heli | 45,48 | 0 / 0 |
| 47 | Mg_Minimi_SPW | mg_minimi_spw | mg | 35 | 150 | own | mg_minimi_spw | none | 0 / 0 |
| 48 | Mg_Minimi_SPW_Heli | mg_minimi_spw | mg | 35 | 900000 | own | mg_minimi_spw_heli | 45,46 | 0 / 0 |
| 49 | Sn_Rem700 | sn_rem700 | sniper | 34 | 5 | own | rifle_type88 | none | 0 / 0 |
| 50 | RPG_7V | rpg_7v | rocket | 29 | 1 | own | rocketlauncher_rpg7 | 51 | 0 / 0 |
| 51 | RPG_7V_Hind | (none) | - | 0 | 999 | own | none (offset 0) | 50 | 0 / 0 |
| 52 | Launcher_HK69A1_01 | grenade_launcher_hk69a1 | grenade launcher, two-handed | 35 | 1 | own | none (offset 0) | 53,54 | 0 / 0 |
| 53 | Launcher_HK69A1_01TearGas | grenade_launcher_hk69a1 | grenade launcher, two-handed | 35 | 1 | own | none | 52,54 | 0 / 0 |
| 54 | Launcher_HK69A1_01Flare | grenade_launcher_hk69a1 | grenade launcher, ONE-handed | 35 | 1 | own | none | 52,53 | 0 / 0 |
| 55-59 | Grenade_Smoke / TearGas / Fragmentation / Incendiary / Flashbang | (none) | - | 0 | 4 | own | none | 56=59 | 0 / 0 |
| 62 | HG_M-77B_Human_Shield | hg_m_77b_human_shield | shield pistol | 3 | 15 | SHARED with 6 | hg_m-77b | 6 | 0 / 0 |
| 63 | HG_M9Beretta_Human_Shield | hg_m_77b_human_shield | shield pistol | 3 | 12 | SHARED with 8 | hg_m9beretta | 8 | 0 / 0 |

Not spare: 60, 61 have no template; 0 is none. Ids 1-32, 34, 36, 37, 39 are the page-1 shop rows (36 rows).
AI column: stock F01 has 0 NPCs on every spare id; stock F06 and F09 have 1 NPC on id 33; DM01 has 23 NPCs on 33
(kl_convert maps M4Light to Type81). Nothing else carries a spare id on DM01 or F01. AI use other than 33 exists only
for 40 on DM09 (1) and DM11B (3), taken from the earlier census (not re-run here).

## Answers
**Spare ids with a PISTOL hold (USP host): none.** The only pistol-hold ids outside the shop are the shield pistols
62/63 (3-slot hold, cannot host a gun) and every real pistol hold (1-11) is a page-1 row. The nearest thing is 54
(Flare launcher): ONE-handed, small, 35-slot launcher folder, own ammo node, but WT_GRENADELAUNCHER (single-shot
break-action reload, projectile code). USP on 54 is a GUESS with real risk (fire code and reload animation are the
launcher's); needs the weapon fields copied from HG_M9Beretta except binding, and the ammo field re-pointed to the
M9 ammo node (clip 12, read only). Recommendation: do NOT promise the USP on page 2. If the owner wants it, test 54
as an isolated experiment; fall back is a klgun "look" on a page-1 pistol (which breaks "page 1 = exact stock", so
the owner decides) or leaving the USP out.

**Spare ids with an SMG-class hold: none** (all `smg_*` folders belong to shop ids 18-28).

**Spare ids with a rifle hold and a ~30-round clip:** 33 (Type81, clip 30), 38 (Type95_L09_NPC, clip 30).
35 has a rifle hold but a 5-round clip and an ammo node shared with page-1 id 34; it needs the ammo link
re-pointed (never edit the node: it would change page-1 Type88). Only 3 rifle-hold hosts exist.
**MG-hold ids (40-48) have a 150-round clip** but each has its OWN ammo node (so clip 30 can be written in place
safely, except 40 which AI carries on DM09 and DM11B; and 45/46/48 are heli variants).

## Recommended assignment
Ranked by safety. Hold class of the host decides the pose; the carrier row decides the tab.

| gun (model) | host id | hold / clip result | carrier row category / tab | fixups |
|---|---|---|---|---|
| Type 81 (native) | 33 | rifle_type81, 30 | rifle carrier | restore the stock Type81 model/sound on 33 (AKM moves off 33). DM AI on 33 carries the real Type81 again (owner accepts) |
| AKM (PD2) | 38 | rifle_type95 (bullpup hold, GUESS: AKM stock/mag position vs Type95 anims), 30, own ammo node | rifle carrier | regenerate pd2_gun output for 38; keep rifle_ak47 sound re-point; own Ground node (root shared with 37 only by data, clone the root before editing it) |
| M4A1 | 35 | rifle_type88 hold, WT_RIFLETYPE88 (GUESS: may carry scope/zoom behaviour) | rifle carrier | re-point weapon field 18 to the stock Rifle_AK74 or Rifle_FN_SCAR ammo node (clip 30, read only, shared) |
| Minimi (native) | 47 | mg_minimi_spw, 150 | rifle/MG carrier | none, live proven by Swap |
| Rem 700 (native) | 49 | sn_rem700, 5 | rifle carrier | none, live proven |
| HK69 (native) | 52 | grenade_launcher_hk69a1, 1 | shotgun carrier | none, live proven |
| MP5, P90, Steyr TMP, SG 552 (SMG-model guns) | 41, 42, 44, 43 | MG pose (mg_gp_type88), clip must be rewritten to 30 in each id's OWN ammo node (safe, unshared) | SMG carriers keep the tab "SMGs" unchanged; but see tab note | re-point each sound definition to its donor (SMG_Type79 / Type05 / MAC_10 / SCAR); GUESS: MG hold pose and reload animation look wrong for a 30-round SMG; 43 is the heli-player template (clip 200, GUESS: no special handling in a map without helicopters); damage type (WT_MACHINEGUN, MG projectile and falloff) comes from the template and ammo node, so copy the stats of an SMG/rifle template |
| USP | none; experiment on 54 | one-handed launcher hold, GUESS | pistol carrier | see answer above |

Alternative for the four SMG-model guns if the MG pose looks wrong: SG 552 on a rifle host would need one more rifle
hold, which does not exist (33/35/38 are taken). So the options are: (a) MG hosts 41-44 as above; (b) drop SG 552
and keep three real rifles (Type81, AKM, M4A1) + SMG guns on MG hosts; (c) accept SMG-model guns on 35/38 instead
of M4A1/AKM. Recommendation (a) for the pilot: it uses only ids with zero AI use on every map.

Ids to avoid: 40 (AI on DM09, DM11B), 62/63 (3-slot shield hold), 51 and 55-59 (no hold folder, 0 slots), 50 (RPG,
rocket code), 48 (900000-round heli clip), 45/46 (Minimi heli twins; harmless as spare MG hosts but they share the
Minimi model root with 48).

## Tab naming
Carrier rows give the tab, so SMG-model guns on SMG carriers need no rename. Only if an SMG-model gun sits on a
RIFLE carrier row (option c above), the page-2 rifle tab must read e.g. "Rifles / SMGs" (owner: "name the tab
differently on page 2"). The label must not contain "(recommended on/off)": `rec_text` appends it.

## Caveats
- The hold class and clip numbers are read from the data; whether an MG-hold animation looks right with an SMG model
  is a guess until seen.
- Hold-folder slot counts come from the Swat_02 set of the map's own .ANM; criminal sets are believed to carry the
  same folders (kl_shop_extra's guess 1).
- Sound shows `none (offset 0)` for launchers/grenades: their definition field is empty in the data.
- The survey reads the archive only. Nothing was written to the game folder.
