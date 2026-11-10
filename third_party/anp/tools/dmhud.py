"""dmhud.py: Dead Men's HUD art in the grafted Dog Days HUD (ANP_DM_HUD, default on; port_level.py + graft.py).

M01 & co run Dog Days' OSD (graft.py: L01 FFOsdMP1.zip, two ZOnScreenDisplay2 with a 200-int .TEX id table each).
Dead Men's own OSD is made inert in place but its int[128] table (Dead Men .TEX ids, valid in the converted .TEX,
which keeps Dead Men's slot numbers) survives in the source .prp. Both exes carry their slot-name tables (DD 0xcee058,
DM 0xa47cf8: DM_SLOTS / DD_SLOTS below, ported from the exe dumps so the exe is not read at build time).

The hook (HudPlan.hook, called by graft.graft after the donor ids are remapped) edits BOTH grafted tables:
  * subst: a DD slot whose widget has a DM counterpart gets the DM texture (crosshair per weapon class from kl2's
    0xceda10 rows [main, shadow, aim-main, aim-shadow]: Gun 3/10/16/22, Rifle 4/11/17/23, Shotgun 6/13/19/25,
    MachineGun 5/12/18/24 (rows 5 and 6), Grenade 7 (row 8, main only), RocketLauncher 8/15/21/27 kept, Empty 2/9
    (row 11) kept; heal/command/select 30-32;
    transfer 33/34; communication/order icons DD 35-57 <- DM 18-40 (DD 47 ZDirectionDisplay arrow <- DM 30
    Arrow_02); borders 0/1; projectile effects 186/187; white 181/182; logo 184; weapon pictures through the DD
    item table 0x154db68[eFF2Item] (DD_ITEM_SLOT) composed with prpconv.ITEM_MAP).
  * shadow: the crosshair shadow slots of those rows (10/22, 11/23, 12/24, 13/25) get Dead Men's own Subtract_*
    layer. DM's ZCrossHairDisplay Draw (kaneandlynch.exe 0x6545a0) draws the main crosshair with mode 0xa and then,
    picked by the main record (Gun 2 -> 12, Rifle 3 -> 13, Shotgun 5 -> 14, MountedMG 4 -> 15, Default 10 -> 11),
    the Subtract layer with mode 9: the same two modes kl2's crosshair Draw (0x7663a0) uses for main and shadow.
  * clear: only when the level lacks that DM Subtract texture: a converter-made 64x64 DXT5 with alpha 0 and colour 0
    ('ANP/Clear', neutral under any blend). Never 0: an id-0 slot is skipped by the loader 0x5e3810 and its record
    handle stays unset. ANP_DM_HUD_SUBTRACT=0 uses the clear texture for every shadow slot. Also (ANP_DM_HUD_NOHITMARK,
    default on) Dog Days' hit / kill markers 151-154, which Dead Men does not have (sidecar why='hitmarker').
  * Empty row (ANP_DM_HUD_XHDEFAULT, default on): kl2 crosshair row 11 (DD 2 / 9, Dog Days' blank Empty art) <- DM
    Default 10 / Subtract_02 11, as Dead Men draws them.
  * park: Dead Men-only art (inventory panel + wheel, ammo clips, health, wounded, crew-order icons, map, text
    console, DM-only weapon pictures, DM crosshair extras) goes into DD slots nothing reads in a Dead Men level:
    slots missing from kl2's name table (the OSD loader still loads them: flags 0x10, fmt 5) and weapon-picture
    slots of DD items the level cannot hold. The engine then creates every handle (osd+0x3ec+12*slot) itself, so
    the later loader widgets only draw records. Slots of hidden DD widgets (cover 129-143 ...) are NOT used.
  * alpha (ANP_DM_HUD_ALPHA, default on): the blend of an OSD slot comes from the flags of its texture handle
    (slot table flags -> 0x5e3810 -> ZPrimControl slot 65 0x6848b0 descriptor +0x10), NOT from the draw mode: the
    mode (0xa main, 9 shadow) only goes into the sub-draws' sort key (0x5359d0: key |= mode << 16), i.e. the layer.
    Flags 0x..200 = alpha blend (all 141 DD 0x60200 slots carry white/colour + alpha art; the 10:49 smoke test drew
    DM's opaque-on-black Gun art in DD 3 as a black square), 0x..002 without 0x200 = additive (36 of DD's 39 0x60002
    slots are opaque art on black, like DM's crosshairs). A DM texture from an additive DM slot that lands in a
    non-additive DD slot (KL2 crosshair slots 3-6/16-19 = 0x60200; parked slots: weapon pictures 0x60200, unlisted
    0x10) gets a converted copy: premultiplied P = rgb*a, alpha' = max(P.r,P.g,P.b) (x ANP_DM_HUD_ALPHA_GAIN),
    rgb' = P / alpha' (colour normalised, so the alpha-blended result equals the additive one where the background is
    dark); full mip chain from P, DXT5 flags 2 like DD's own KL2_Crosshair_01 entries. Per texture: if alpha' matches
    the texture's own alpha (art already alpha-authored, e.g. DM 88 Wounded) the original is kept.
    Shadows: DM's Subtract_* art (black, alpha 0..117) sits in DM 0x60200 slots and goes into DD 0x60200 slots, the
    same blend (SRCALPHA/INVSRCALPHA darkening); DD's own RocketLauncherShadow / GrenadeThrowShadow are the same
    black+alpha art. So no inversion and no conversion.
The plan goes into the level zip as Scenes/Locations/<ID>/ANP_hud.json (stored, uncompressed): slot -> DM name,
dm slot -> DD slots, the clear texture, before/after tables, the alpha conversions (slot 'alpha', 'src_tex').

CLI:  python tools\\dmhud.py sheet <level _Main.zip> <out.png>   (offline HUD contact sheet: every DD slot before|after)
      python tools\\dmhud.py show  <level _Main.zip>              (prints the sidecar summary)
Switches: ANP_DM_HUD=0 (off), ANP_DM_HUD_HITDIR=1 (DD 189 hit direction <- DM 105 full-screen sphere; default keeps
Dog Days' 64x64 icon, the DM art is parked for the loader instead), ANP_DM_HUD_WEAPONS=0 (keep DD weapon pictures),
ANP_DM_HUD_XHDEFAULT=0 (keep Dog Days' empty crosshair row 11 instead of DM's Default dot + Subtract_02),
ANP_DM_HUD_NOHITMARK=0 (keep Dog Days' hit / kill markers 151-154; default hides them with the clear texture),
ANP_DM_HUD_PARK=0 (no parking), ANP_DM_HUD_SUBTRACT=0 (transparent crosshair shadows instead of DM's Subtract layer),
ANP_DM_HUD_ALPHA=0 (no alpha conversion: DM's raw additive art in alpha-blend slots), ANP_DM_HUD_ALPHA_GAIN=<f>
(alpha' multiplier for converted art, default 1.0 = the additive look), ANP_DM_CROSSHAIR_ONE=1|flip|0 (Dead Men's
crosshair drawn once by kl2's N-copy builder: weapon template values in prpconv.crosshair_one + half textures here, see
xhair_props; default 1 = split), ANP_DM_CROSSHAIR_INNER=top|bottom (which texture edge kl2 puts on the centre).
Note: DM's ZDirectionDisplay reads DM 30 (Arrow_02) and 105 (hit sphere), i.e. it was DM's hit-direction widget;
Dog Days' ZDirectionDisplay reads only DD 47 (#Coop). DD 47 <- DM 30 follows the class, not the role."""
import os, sys, json, struct, collections, zlib

def _tab(s):
    r = {}
    for l in s.strip().splitlines():
        a, b, c, d = l.split(' ')
        r[int(a)] = (b.replace('~', ' '), int(c, 16), int(d))
    return r

# ---------------------------------------------------------------- exe tables: slot -> (texture name, flags, fmt)
DM_SLOTS=_tab("""
0 UserInterface/_Test/Borders_01#Border 60200 5
1 UserInterface/_Test/Borders_01#Red~Border 60200 5
2 Crosshairs/Crosshair_Add_01#Gun 60002 5
3 Crosshairs/Crosshair_Add_01#Rifle 60002 5
4 Crosshairs/Crosshair_Add_01#MountedMG 60002 5
5 Crosshairs/Crosshair_Add_01#Shotgun 60002 5
6 Crosshairs/Crosshair_Add_01#Granade 60002 5
7 Crosshairs/Crosshair_Add_01#Heal 60002 5
8 Crosshairs/Crosshair_Add_01#Command 60002 5
9 Crosshairs/Crosshair_Add_01#Select 60002 5
10 Crosshairs/Crosshair_Add_01#Default 60002 5
11 Crosshairs/Crosshair_Add_01#Subtract_02 60200 5
12 Crosshairs/Crosshair_Add_01#Subtract_Gun 60200 5
13 Crosshairs/Crosshair_Add_01#Subtract_Rifle 60200 5
14 Crosshairs/Crosshair_Add_01#Subtract_Shotgun 60200 5
15 Crosshairs/Crosshair_Add_01#Subtract_MountedMG 60200 5
16 Crosshairs/Crosshair_Add_01#TransferLeft 60002 5
17 Crosshairs/Crosshair_Add_01#TransferRight 60002 5
18 UserInterface/Icons/UI_KL_Communications_01#Ok 60002 5
19 Crosshairs/Crosshair_Add_01#Merc_01 60002 5
20 Crosshairs/Crosshair_Add_01#Merc_02 60002 5
21 Crosshairs/Crosshair_Add_01#Merc_03 60002 5
22 Crosshairs/Crosshair_Add_01#Merc_04 60002 5
23 UserInterface/Icons/UI_KL_Communications_01#Attack 60002 5
24 UserInterface/Icons/UI_KL_Communications_01#Target 60002 5
25 UserInterface/Icons/UI_KL_Communications_01#Defend 60002 5
26 UserInterface/Icons/UI_KL_Communications_01#Follow 60002 5
27 UserInterface/Icons/UI_KL_Communications_01#Ok 60002 5
28 UserInterface/Icons/UI_KL_Communications_01#Medic 60002 5
29 Crosshairs/Crosshair_Add_01#Arrow 60002 5
30 Crosshairs/Crosshair_Add_01#Arrow_02 60002 6
31 UserInterface/Icons/UI_KL_Communications_01#SniperWarning 60002 5
32 UserInterface/Icons/UI_KL_Communications_01#Ammo 60002 5
33 UserInterface/Icons/UI_KL_Communications_01#GroundPlane 60002 5
34 UserInterface/Icons/UI_KL_Communications_01#Target 60002 5
35 UserInterface/Icons/UI_KL_Communications_01#Defend 60002 5
36 UserInterface/Icons/UI_KL_Communications_01#Loot 60002 6
37 UserInterface/Icons/UI_KL_Communications_01#Money 60002 6
38 UserInterface/Icons/UI_KL_Communications_01#Rappel 60002 5
39 UserInterface/Icons/UI_KL_Communications_01#Objective 60002 5
40 UserInterface/Icons/UI_Icons_01#Icons_PS2 60200 5
41 UserInterface/WeaponsPics/Inventory#Middle_a 60200 6
42 UserInterface/WeaponsPics/Inventory2#InventorySmall 60200 6
43 UserInterface/WeaponsPics/Inventory2#InventorySmallLeftPart 60200 6
45 UserInterface/UI_KL_WeaponSelect3#Background_player 60200 6
46 UserInterface/UI_KL_WeaponSelect3#Background_NPC 60200 6
47 UserInterface/UI_KL_WeaponSelect3#Focus_middle 60200 6
48 UserInterface/UI_KL_WeaponSelect3#Focus_Player 60200 6
49 UserInterface/UI_KL_WeaponSelect3#Focus_NPC 60200 6
50 UserInterface/WeaponsPics/UI_Weapon_01#C4 60200 6
51 UserInterface/WeaponsPics/UI_Weapon_01#Binoculars 60200 6
52 UserInterface/WeaponsPics/UI_Weapon_01#HK_USP 60200 6
53 UserInterface/WeaponsPics/UI_Weapon_01#HK_USP_Silenced 60200 6
54 UserInterface/WeaponsPics/UI_Weapon_01#Gun_Taurus 60200 6
55 UserInterface/WeaponsPics/UI_Weapon_01#Smg_SteyrTMP 60200 6
56 UserInterface/WeaponsPics/UI_Weapon_01#MP5_A3 60200 6
57 UserInterface/WeaponsPics/UI_Weapon_01#FN_P90 60200 6
58 UserInterface/WeaponsPics/UI_Weapon_01#M4A1_Carbine 60200 6
59 UserInterface/WeaponsPics/UI_Weapon_01#AK 60200 6
60 UserInterface/WeaponsPics/UI_Weapon_01#SG_552 60200 6
61 UserInterface/WeaponsPics/UI_Weapon_01#RugerMini14 60200 6
62 UserInterface/WeaponsPics/UI_Weapon_01#Remington_700 60200 6
63 UserInterface/WeaponsPics/UI_Weapon_01#FN_Minimi_SPW 60200 6
64 UserInterface/WeaponsPics/UI_Weapon_01#Spas_12 60200 6
65 UserInterface/WeaponsPics/UI_Weapon_01#Shotgun_Remington_870 60200 6
66 UserInterface/WeaponsPics/UI_Weapon_01#RPG_7V 60200 6
67 UserInterface/WeaponsPics/UI_Weapon_01#Launcher_HK69A1 60200 6
68 UserInterface/WeaponsPics/UI_Weapon_01#Smoke_Granade 60200 6
69 UserInterface/WeaponsPics/UI_Weapon_01#Granade_TearGas 60200 6
70 UserInterface/WeaponsPics/UI_Weapon_01#Granade 60200 6
71 UserInterface/WeaponsPics/UI_Weapon_01#Granade_Incendiary 60200 6
72 UserInterface/WeaponsPics/UI_Weapon_01#Mine_Claymore 60200 6
73 UserInterface/WeaponsPics/UI_AmmoClip#AmmoClip_01b 60200 6
74 UserInterface/WeaponsPics/UI_AmmoClip#AmmoClip_01a 60200 6
75 UserInterface/WeaponsPics/UI_AmmoClip#AmmoClip_02a 60200 6
76 UserInterface/WeaponsPics/UI_AmmoClip#AmmoClip_03b 60200 6
77 UserInterface/WeaponsPics/UI_AmmoClip#AmmoClip_03a 60200 6
78 UserInterface/UI_Map_Icons_01#Icons_01a 60200 6
79 UserInterface/UI_KL_MapSmall#PIPbackgr 60200 6
80 UserInterface/UI_KL_MapSmall#Background 60200 6
81 UserInterface/UI_KL_MapBig#PIPbackgr 60200 6
82 UserInterface/UI_KL_MapBig#Background 60200 6
83 UserInterface/UI_KL_MapSmall#InfoThingy 60200 6
84 UserInterface/UI_KL_MapMask#MaskPlayer0 60200 6
85 UserInterface/UI_KL_MapMask#MaskPlayer1 60200 6
86 UserInterface/UI_Health_01#Health_01b 60200 6
87 UserInterface/UI_Health_01#Health_01a 60200 6
88 UserInterface/WeaponsPics/UI_Weapon_01#Wounded 60002 6
89 UserInterface/UI_TextConsole_01#TextConsole_01 60200 6
90 UserInterface/UI_KL_Recruit_Icons2#Follow 60200 5
91 UserInterface/UI_KL_Recruit_Icons2#Follow 60200 5
92 UserInterface/UI_KL_Recruit2#Background 60200 5
93 UserInterface/UI_KL_Recruit_Icons2#ArrowLeft 60200 5
94 UserInterface/UI_KL_Recruit_Icons2#ArrowRight 60200 5
95 UserInterface/UI_KL_Recruit_Icons2#Follow 60200 5
96 UserInterface/UI_KL_Recruit_Icons2#Guard 60200 5
97 UserInterface/UI_KL_Recruit_Icons2#Attack 60200 5
98 UserInterface/UI_KL_Recruit_Icons2#SubsquadBackground 60200 5
99 UserInterface/UI_KL_Recruit_Icons2#SubsquadDot 60200 5
100 UserInterface/UI_White#Diffuse_A 60200 5
101 UserInterface/UI_Logos_01#E3_Logo 60200 5
102 UserInterface/ColourTest#Diffuse_a 60200 5
103 Effects/Geom/Smoke_Trail_02#Diffuse_a 40002 6
104 Effects/Geom/Smoke_Trail_02#Diffuse_a 40002 6
105 UserInterface/Overlay/UI_HitDirection_Sphere_01#diffuse 60002 5
106 UserInterface/UI_FA_Respawn_pip_mask#Diffuse_a 60200 6
""")
DD_SLOTS=_tab("""
0 UserInterface/_Test/Borders_01#Border 60200 5
1 UserInterface/_Test/Borders_01#Red~Border 60200 5
2 UserInterface/Crosshairs/KL2_Crosshair_01#Empty 60200 6
3 UserInterface/Crosshairs/KL2_Crosshair_01#Gun 60200 6
4 UserInterface/Crosshairs/KL2_Crosshair_01#Rifle 60200 6
5 UserInterface/Crosshairs/KL2_Crosshair_01#MachineGun 60200 6
6 UserInterface/Crosshairs/KL2_Crosshair_01#Shotgun 60200 6
7 UserInterface/Crosshairs/Crosshair_Add_01#Grenade 60002 6
8 UserInterface/Crosshairs/Crosshair_Add_01#RocketLauncher 60002 6
9 UserInterface/Crosshairs/KL2_Crosshair_01#Empty 60200 6
10 UserInterface/Crosshairs/KL2_Crosshair_01#GunShadow 60200 6
11 UserInterface/Crosshairs/KL2_Crosshair_01#RifleShadow 60200 6
12 UserInterface/Crosshairs/KL2_Crosshair_01#MachineGunShadow 60200 6
13 UserInterface/Crosshairs/KL2_Crosshair_01#ShotgunShadow 60200 6
15 UserInterface/Crosshairs/Crosshair_Add_01#RocketLauncherShadow 60200 6
16 UserInterface/Crosshairs/KL2_Crosshair_01#Gun 60200 6
17 UserInterface/Crosshairs/KL2_Crosshair_01#Rifle 60200 6
18 UserInterface/Crosshairs/KL2_Crosshair_01#MachineGun 60200 6
19 UserInterface/Crosshairs/KL2_Crosshair_01#Shotgun 60200 6
21 UserInterface/Crosshairs/Crosshair_Add_01#RocketLauncherAim 60002 6
22 UserInterface/Crosshairs/KL2_Crosshair_01#GunShadow 60200 6
23 UserInterface/Crosshairs/KL2_Crosshair_01#RifleShadow 60200 6
24 UserInterface/Crosshairs/KL2_Crosshair_01#MachineGunShadow 60200 6
25 UserInterface/Crosshairs/KL2_Crosshair_01#ShotgunShadow 60200 6
27 UserInterface/Crosshairs/Crosshair_Add_01#RocketLauncherAimShadow 60200 6
28 UserInterface/Crosshairs/Crosshair_Add_01#GrenadeThrow 60002 5
29 UserInterface/Crosshairs/Crosshair_Add_01#GrenadeThrowShadow 60200 5
30 UserInterface/Crosshairs/Crosshair_Add_01#Heal 60002 6
31 UserInterface/Crosshairs/Crosshair_Add_01#Command 60002 6
32 UserInterface/Crosshairs/Crosshair_Add_01#Select 60002 6
33 UserInterface/Crosshairs/Crosshair_Add_01#TransferLeft 60002 6
34 UserInterface/Crosshairs/Crosshair_Add_01#TransferRight 60002 6
35 UserInterface/Icons/UI_KL_Communications_01#Ok 60002 5
36 UserInterface/Crosshairs/Crosshair_Add_01#Merc_01 60002 5
37 UserInterface/Crosshairs/Crosshair_Add_01#Merc_02 60002 5
38 UserInterface/Crosshairs/Crosshair_Add_01#Merc_03 60002 5
39 UserInterface/Crosshairs/Crosshair_Add_01#Merc_04 60002 5
40 UserInterface/Icons/UI_KL_Communications_01#Attack 60002 5
41 UserInterface/Icons/UI_KL_Communications_01#Target 60002 5
42 UserInterface/Icons/UI_KL_Communications_01#Defend 60002 5
43 UserInterface/Icons/UI_KL_Communications_01#Follow 60002 5
44 UserInterface/Icons/UI_KL_Communications_01#Ok 60002 5
45 UserInterface/Icons/UI_KL_Communications_01#Medic 60002 5
46 UserInterface/Crosshairs/Crosshair_Add_01#Arrow 60002 5
47 UserInterface/Icons/UI_KL2_Icons_01#Coop 60002 6
48 UserInterface/Icons/UI_KL_Communications_01#SniperWarning 60002 5
49 UserInterface/Icons/UI_KL_Communications_01#Ammo 60002 5
50 UserInterface/Icons/UI_KL_Communications_01#GroundPlane 60002 5
51 UserInterface/Icons/UI_KL_Communications_01#Target 60002 5
52 UserInterface/Icons/UI_KL_Communications_01#Defend 60002 5
53 UserInterface/Icons/UI_KL_Communications_01#Loot 60002 6
54 UserInterface/Icons/UI_KL_Communications_01#Money 60002 6
55 UserInterface/Icons/UI_KL_Communications_01#Rappel 60002 5
56 UserInterface/Icons/UI_KL_Communications_01#Objective 60002 5
57 UserInterface/Icons/UI_Icons_01#Icons_PS2 60200 5
58 UserInterface/WeaponsPics/UI_Weapon_01#HG_SW_MP45 60200 6
59 UserInterface/WeaponsPics/UI_Weapon_01#HG_TaurusJudge 60200 6
60 UserInterface/WeaponsPics/UI_Weapon_01#HG_Revolver_Police 60200 6
61 UserInterface/WeaponsPics/UI_Weapon_01#HG_SigSauer226 60200 6
62 UserInterface/WeaponsPics/UI_Weapon_01#HG_ColtCobra 60200 6
63 UserInterface/WeaponsPics/UI_Weapon_01#HG_M-77B 60200 6
64 UserInterface/WeaponsPics/UI_Weapon_01#HG_M-77B_Silenced 60200 6
65 UserInterface/WeaponsPics/UI_Weapon_01#HG_M9Beretta 60200 6
66 UserInterface/WeaponsPics/UI_Weapon_01#HG_M9Beretta_Silenced 60200 6
67 UserInterface/WeaponsPics/UI_Weapon_01#HG_DesertEagle 60200 6
68 UserInterface/WeaponsPics/UI_Weapon_01#HG_TT-33 60200 6
69 UserInterface/WeaponsPics/UI_Weapon_01#HG_M-77B_Human_Shield 60200 6
70 UserInterface/WeaponsPics/UI_Weapon_01#HG_M9Beretta_Human_Shield 60200 6
71 UserInterface/WeaponsPics/UI_Weapon_01#Shotgun_Hawk_Bullpup 60200 6
72 UserInterface/WeaponsPics/UI_Weapon_01#Shotgun_Hawk_Police 60200 6
73 UserInterface/WeaponsPics/UI_Weapon_01#Shotgun_Hawk_SawnOff 60200 6
74 UserInterface/WeaponsPics/UI_Weapon_01#Shotgun_TPS 60200 6
75 UserInterface/WeaponsPics/UI_Weapon_01#Shotgun_Remington_870 60200 6
76 UserInterface/WeaponsPics/UI_Weapon_01#Shotgun_Spas_12 60200 6
77 UserInterface/WeaponsPics/UI_Weapon_01#SMG_SA61 60200 6
78 UserInterface/WeaponsPics/UI_Weapon_01#SMG_UMP_SBR 60200 6
79 UserInterface/WeaponsPics/UI_Weapon_01#SMG_UMP 60200 6
80 UserInterface/WeaponsPics/UI_Weapon_01#SMG_UMP_Silenced 60200 6
81 UserInterface/WeaponsPics/UI_Weapon_01#SMG_HK_SP89_Silenced 60200 6
82 UserInterface/WeaponsPics/UI_Weapon_01#SMG_MAC_10 60200 6
83 UserInterface/WeaponsPics/UI_Weapon_01#SMG_MAC_10_Silenced 60200 6
84 UserInterface/WeaponsPics/UI_Weapon_01#SMG_MPI69 60200 6
85 UserInterface/WeaponsPics/UI_Weapon_01#SMG_Type79 60200 6
86 UserInterface/WeaponsPics/UI_Weapon_01#SMG_Type05 60200 6
87 UserInterface/WeaponsPics/UI_Weapon_01#SMG_Type05_Silenced 60200 6
88 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_zastavam85 60200 6
89 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_FN_SCAR 60200 6
90 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_AK47 60200 6
91 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_AK74 60200 6
92 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_Type81 60200 6
93 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_Type88 60200 6
94 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_Type88_Scoped 60200 6
95 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_Type95 60200 6
96 UserInterface/WeaponsPics/UI_Weapon_01#Rifle_Type95_Scoped 60200 6
97 UserInterface/WeaponsPics/UI_Weapon_01#MG_MiniMi_SPW 60200 6
98 UserInterface/WeaponsPics/UI_Weapon_01#Sn_Rem700 60200 6
99 UserInterface/WeaponsPics/UI_Weapon_01#RPG_7V 60200 6
100 UserInterface/WeaponsPics/UI_Weapon_01#Launcher_HK69A1 60200 6
101 UserInterface/WeaponsPics/UI_Weapon_01#Grenade_Smoke 60200 6
102 UserInterface/WeaponsPics/UI_Weapon_01#Grenade_TearGas 60200 6
103 UserInterface/WeaponsPics/UI_Weapon_01#Grenade 60200 6
104 UserInterface/WeaponsPics/UI_Weapon_01#Grenade_Incendiary 60200 6
105 UserInterface/WeaponsPics/UI_Weapon_01#AmmoPickup 60200 6
106 UserInterface/WeaponsPics/UI_Weapon_01#AmmoNoPickup 60200 6
107 UserInterface/UI_KL2_Weapon_BG_01#Weapon_BG 60200 5
108 UserInterface/UI_KL2_Weapon_BG_01#Weapon_BG_L09 60200 5
109 UserInterface/UI_KL2_AmmoCount_01#Diffuse_a 60200 6
110 UserInterface/Icons/UI_KL2_Icons_01#Arrow 60200 6
119 UserInterface/Icons/UI_KL2_Icons_01#CheckPoint 60200 5
120 UserInterface/Icons/UI_KL2_Icons_01#Objective 60200 5
121 UserInterface/Icons/UI_KL2_Icons_01#ObjectiveDone 60200 5
122 UserInterface/Icons/UI_KL2_Icons_01#ObjectiveFail 60200 5
127 UserInterface/Icons/UI_KL2_Icons_01#Sound 60200 5
128 UserInterface/Icons/UI_KL2_Icons_01#Reload 60200 5
129 UserInterface/Icons/UI_KL2_Icons_01#TakeCover 60200 5
130 UserInterface/Icons/UI_KL2_Icons_01#EnterCoverLeft 60200 5
131 UserInterface/Icons/UI_KL2_Icons_01#EnterCoverRight 60200 5
132 UserInterface/Icons/UI_KL2_Icons_01#CoverStick 60200 5
133 UserInterface/Icons/UI_KL2_Icons_01#CoverStickLeft 60200 5
134 UserInterface/Icons/UI_KL2_Icons_01#CoverStickRight 60200 5
135 UserInterface/Icons/UI_KL2_Icons_01#CoverStickUp 60200 5
136 UserInterface/Icons/UI_KL2_Icons_01#CoverRushLeft 60200 5
137 UserInterface/Icons/UI_KL2_Icons_01#CoverRushRight 60200 5
138 UserInterface/Icons/UI_KL2_Icons_01#CoverLeft 60200 5
139 UserInterface/Icons/UI_KL2_Icons_01#CoverRight 60200 5
140 UserInterface/Icons/UI_KL2_Icons_01#CoverVault 60200 5
141 UserInterface/Icons/UI_KL2_Icons_01#CoverExitLeft 60200 5
142 UserInterface/Icons/UI_KL2_Icons_01#CoverExitRight 60200 5
143 UserInterface/Icons/UI_KL2_Icons_01#CoverExitBack 60200 5
144 UserInterface/Icons/UI_KL2_Icons_01#CanisterNormal 60200 5
145 UserInterface/Icons/UI_KL2_Icons_01#CanisterExplosive 60200 5
146 UserInterface/Icons/UI_KL2_Icons_01#CanisterTarget 60200 5
147 UserInterface/Icons/UI_KL2_Icons_01#CanisterThrow 60200 5
148 UserInterface/Icons/UI_KL2_Icons_01#CanisterBuildUp2 60200 5
149 UserInterface/Icons/UI_KL2_Icons_01#CanisterBuildUp3 60200 5
150 UserInterface/Icons/UI_KL2_Icons_01#CanisterBuildUp4 60200 5
151 UserInterface/Icons/UI_KL2_Icons_01#HitEnemy 60200 5
152 UserInterface/Icons/UI_KL2_Icons_01#HitEnemyShotgun 60200 5
153 UserInterface/Icons/UI_KL2_Icons_01#KillEnemy 60200 5
154 UserInterface/Icons/UI_KL2_Icons_01#KillEnemyShotgun 60200 5
155 UserInterface/Icons/UI_KL2_Icons_01#Cover 60200 5
156 UserInterface/Icons/UI_KL2_Icons_01#Cover 60200 5
157 UserInterface/Icons/UI_KL2_Icons_01#Cover 60200 5
158 UserInterface/Icons/UI_KL2_Icons_01#Cover 60200 5
159 UserInterface/Icons/UI_KL2_Icons_01#Cover 60200 5
160 UserInterface/Icons/UI_KL2_Icons_01#Cover 60200 5
161 UserInterface/UI_KL2_Tracker_01#GameplayTracker 60200 5
162 UserInterface/UI_KL2_Tracker_01#GameplayTracker_02 60200 5
163 UserInterface/UI_KL2_Tracker_01#GameplayTracker_03 60200 5
164 UserInterface/UI_KL2_Tracker_01#GameplayTracker_04 60200 5
165 UserInterface/UI_KL2_Arrows_01#Arrow_Down_01 60200 5
166 UserInterface/UI_KL2_Arrows_01#Arrow_Up_01 60200 5
167 UserInterface/UI_KL2_Arrows_01#Arrow_Left_01 60200 5
168 UserInterface/UI_KL2_Arrows_01#Arrow_Right_01 60200 5
169 UserInterface/UI_KL2_Meter_BG#Meter_BG 60200 5
170 UserInterface/Icons/UI_KL2_Icons_01#BoardingCar 60200 5
171 UserInterface/Icons/UI_KL2_Icons_01#BoardingChopper 60200 5
172 UserInterface/Icons/UI_KL2_Icons_01#Money 60200 5
173 UserInterface/UI_KL2_Small_Icons_01#Escape 60200 5
174 UserInterface/UI_KL2_Small_Icons_01#EscapeChopper 60200 5
175 UserInterface/UI_KL2_Small_Icons_01#Money 60200 5
176 UserInterface/UI_KL2_Small_Icons_01#YellowCard 60200 5
177 UserInterface/UI_KL2_Small_Icons_01#YellowCardFollow 60200 5
178 UserInterface/UI_KL2_Small_Icons_01#Kill 60200 5
179 UserInterface/UI_KL2_Small_Icons_01#Star 60200 5
180 UserInterface/UI_KL2_FocusBars_01#Focusbar_Medium_06 60200 5
181 UserInterface/UI_White#Diffuse_A 60200 5
182 UserInterface/UI_White#Diffuse_A 60200 6
183 UserInterface/UI_kl2_Sniper_Laser#SniperLaser 40002 6
184 UserInterface/UI_Logos_01#E3_Logo 60200 5
186 Effects/Geom/Smoke_Trail_02#Diffuse_a 40002 6
187 Effects/Geom/Smoke_Trail_02#Diffuse_a 40002 6
188 UserInterface/Overlay/Blood_Droplets_01#Diffuse_a 60002 8
189 UserInterface/Icons/UI_KL2_Icons_01#HitDirection 60200 6
191 Effects/Lenseflares/Lenseflares_A_01#Diffuse_a 60002 8
192 Effects/Lenseflares/Lenseflares_B_01#Diffuse_a 60200 6
193 UserInterface/UI_KL2_AmmoCount_01#Diffuse_a 60200 6
194 UserInterface/Icons/UI_KL_Communications_01#Throw 60002 5
195 UserInterface/Icons/UI_KL_Communications_01#Throw 60002 5
196 UserInterface/Icons/UI_KL_Communications_01#Door 60002 5
197 UserInterface/Icons/UI_KL_Communications_01#Door 60002 5
198 UserInterface/Icons/UI_KL_Communications_01#Door 60002 5
199 UserInterface/Icons/UI_KL_Communications_01#Door 60002 5
""")
DD_ITEM_SLOT={'HG_TaurusJudge':59, 'HG_Revolver_Police':60, 'HG_SigSauer226':61, 'HG_ColtCobra':62, 'HG_M_77B':63, 'HG_M_77B_Silenced':64, 'HG_M9Beretta':65, 'HG_M9Beretta_Silenced':66, 'HG_DesertEagle':67, 'HG_TT_33':68, 'Shotgun_Hawk_Bullpup':71, 'Shotgun_Hawk_Police':72, 'Shotgun_Hawk_SawnOff':73, 'Shotgun_TPS':74, 'Shotgun_Remington_870':75, 'Shotgun_Spas_12':76, 'SMG_SA61':77, 'SMG_UMP_SBR':78, 'SMG_UMP':79, 'SMG_UMP_Silenced':80, 'SMG_HK_SP89_Silenced':81, 'SMG_MAC_10':82, 'SMG_MAC_10_Silenced':83, 'SMG_MPI69':84, 'SMG_Type79':85, 'SMG_Type05':86, 'SMG_Type05_Silenced':87, 'Rifle_Zastavam85':88, 'Rifle_FN_SCAR':89, 'Rifle_AK47':90, 'Rifle_AK74':91, 'Rifle_Type81':92, 'Rifle_Type88':93, 'Rifle_Type88_L09_NPC':93, 'Rifle_Type88_Scoped':94, 'Rifle_Type95':95, 'Rifle_Type95_L09_NPC':95, 'Rifle_Type95_Scoped':96, 'MG_GP_Type88':97, 'MG_GP_Type88_L09_Heli_Player':97, 'MG_MiniMi_SPW_L09_Heli_Player':97, 'MG_MiniMi_SPW':97, 'Sn_Rem700':98, 'RocketLauncher':99, 'GrenadeLauncher':100, 'GrenadeLauncher_Gas':100, 'GrenadeLauncher_Flare':100, 'Grenade_Smoke':101, 'Grenade_Gas':102, 'Grenade_Frag':103, 'Grenade_Incendiary':104, 'Grenade_FlashBang':102, 'WeaponAmmoPickup':105, 'WeaponAmmoFull':106, 'HG_M_77B_Human_Shield':63, 'HG_M9Beretta_Human_Shield':65}
DD_ITEM_SLOT['HG_SW_MP45'] = 58

# Dead Men item (eFF2Item<name>) -> its picture slot in Dead Men's OSD (by exe name, DM 50-72)
DM_ITEM_PIC = {'BombC4': 50, 'PistolHKUSP': 52, 'PistolHKUSPCarry': 52, 'PistolHKUSPLight': 52,
               'PistolHKUSPSilenced': 53, 'PistolTaurus': 54, 'SMGSteyrTMP': 55, 'SMGHKMP5': 56, 'SMGHKMP5Light': 56,
               'SMGFNP90': 57, 'RifleM4': 58, 'RifleM4Light': 58, 'RifleAK74': 59, 'RifleSG552': 60,
               'RifleRugerMini14': 61, 'SniperRemington700': 62, 'SniperRemington700Silenced': 62,
               'FNMinimiSPW': 63, 'FNMinimiSPWHeli': 63, 'ShotgunSpas12': 64, 'ShotgunRemington870': 65,
               'RocketLauncher': 66, 'RocketLauncherInaccurate': 66, 'RocketLauncherHind': 66,
               'GrenadeLauncher': 67, 'GrenadeLauncherGas': 67, 'GrenadeLauncherFlare': 67, 'GrenadeSmoke': 68,
               'GrenadeGas': 69, 'GrenadeFrag': 70, 'GrenadeIncendiary': 71, 'Claymore': 72}

HITDIR = os.environ.get('ANP_DM_HUD_HITDIR', '0') == '1'
# ANP_DM_HUD_XHDEFAULT (default 1): kl2's crosshair row 11 (0xceda10: main 2, shadow 9, aim 2, aim-shadow 9; picked by
# weapon +0x70 == 11, drawn by the 0x4fd660 builder with that weapon's template) shows Dog Days' KL2_Crosshair_01#Empty
# (alpha 0: no crosshair). Dead Men draws its Default dot (DM 10, mode 0xa) + Subtract_02 (DM 11, mode 9) there. 1:
# DD 2 <- DM 10 (alpha-converted like the other mains), DD 9 <- DM 11 through SHADOW_OF / SHADOW_DM (so it follows
# ANP_DM_HUD_SUBTRACT) and the row is halved for ANP_DM_CROSSHAIR_ONE split. Both DM textures were parked before.
XHDEFAULT = os.environ.get('ANP_DM_HUD_XHDEFAULT', '1') == '1'
# ANP_DM_HUD_NOHITMARK (default 1): Dead Men has no hit / kill markers. Dog Days' ZHitEnemyDisplay (vt 0xbbea00; init
# 0x89f9c0 takes the records of slots 151 HitEnemy, 152 HitEnemyShotgun, 153 KillEnemy, 154 KillEnemyShotgun; Draw
# 0x4fa300) gets the clear texture in all four. kl2's .data dword 0xcedb40 is 1 on disk and no code writes it (only
# two reads): Draw 0x4fa300 runs only while it is != 0, and the crosshair update's other hit-marker style (0x8e9d3d,
# 4 copies of the crosshair at +45 degrees, scale 0.75) only while it is 0 - so writing 0 there would swap the marker
# style, not hide it; the clear texture hides every Dog Days hit marker with no memory write.
NOHITMARK = os.environ.get('ANP_DM_HUD_NOHITMARK', '1') == '1'
HITMARK_SLOTS = (151, 152, 153, 154)
WEAPONS = os.environ.get('ANP_DM_HUD_WEAPONS', '1') == '1'
PARK = os.environ.get('ANP_DM_HUD_PARK', '1') == '1'
SUBTRACT = os.environ.get('ANP_DM_HUD_SUBTRACT', '1') == '1'
ALPHA = os.environ.get('ANP_DM_HUD_ALPHA', '1') == '1'
ALPHA_GAIN = float(os.environ.get('ANP_DM_HUD_ALPHA_GAIN', '1'))

# ---------------------------------------------------------------- one crosshair (ANP_DM_CROSSHAIR_ONE)
# kl2's crosshair (Update 0x8e9720 -> sprite builder 0x4fd660, Draw 0x7663a0) draws the row's texture N times; Dead
# Men's (ZCrossHairDisplay Draw 0x6545a0, update 0x654410) draws its texture ONCE, centred, fixed size (w,h x HUD scale
# 0xa47cec = 1.0), offset only by the weapon's static +0xa0/+0xa4 (DD has the same, obj+0xa8/+0xac). DM has no spread
# feedback at all: no scale, no fade, no push-out. The Dog Days builder, per weapon template (ZFFItemTemplateWeapon
# fields, record offset +4 = object offset; read only by 0x4fd660 / 0x8e9720 - a scan of every fld/movzx of these
# displacements in kl2 found no other reader of the template):
#   N = byte +0x220 (field 60), start = byte +0x221 (61, degrees); copy k (0..N-1) is turned by start + k*360/N with
#   dir = R(angle)*(0,-1); its quad (unit square, UV (0,0) at local (-.5,-.5)) is rotated by (dir) - at angle 0 by
#   180 degrees - and centred at screen centre + (w/2*dx, h/2*dy) * s * R, size (w,h) * A, where
#   f = clamp(v, 1, max = f +0x228 (63)) (v = smoothed spread: base +0x224 + gain +0x230 * movement), A = min(f, 1.5),
#   R = f + r*(f-1), r = f +0x22c (64). (s = 1, or 0.75 on the hit-marker call 0x8e9d3d, which forces N=4 and +45
#   degrees and is switched off by 0xcedb40 = 1.)
# So a copy's INNER edge always touches the screen centre at rest (R = A = 1): no N / angle / radius puts one texture
# on the centre. N=1 + radius 0 (the first idea) draws DM's crosshair half its height above the centre.
# Which texture edge is inner: taken literally (vertex x', y' added to the centre unchanged) the 0/180-degree copies
# face their texture top inward but the 90/270 ones outward, which Dog Days' own 4-arm art cannot be meant for; the
# renderer must mirror one vertex axis. XHAIR_INNER (ANP_DM_CROSSHAIR_INNER) = 'top' (default): vertex x mirrored,
# every copy's texture TOP is inner - Dog Days' arm art agrees (KL2_Crosshair_01 spikes narrow at the top, rows 5-14
# of 64; the Shotgun bracket's ends at the top, y 16.8 vs 18.5 in the middle -> '( )' around the centre only if the
# top is inner). 'bottom' = vertex y mirrored, texture bottom inner: the fallback if the game shows the two halves
# pushed apart by a gap of one texture height.
#   split (ANP_DM_CROSSHAIR_ONE=1, default): N=2, angle 0, max 1.0 (f = A = R = 1 always: static, like DM), gain 0.
#     Every full-art crosshair slot gets a 'half' copy: rows 0..h/2 of the texture = one half of the art (the half whose
#     180-degree turn rebuilds the full art best), rows h/2..h transparent. Copy 1 (below, upright) draws that half,
#     copy 0 (above, turned 180) draws it turned -> the whole crosshair once, centred, original size. Exact for
#     point-symmetric art (Gun, Rifle, Shotgun rings), approximate for the tripod (MountedMG / DD RocketLauncher).
#   flip (ANP_DM_CROSSHAIR_ONE=flip, untested in game): N=1, angle 0, max -1, gain -0.5: v > -1 always -> f = -1,
#     A = -1 (quad size -w,-h = a second 180-degree turn: upright), R = -1 + -0.5*-2 = 0 (centred). Full art, any
#     shape, no crop - IF kl2's sprite renderer accepts negative sizes (unverified).
#   0: off (Dog Days' level defaults N=4 ... as the exact relayout filled them).
XHAIR_MODE = {'1': 'split', 'on': 'split', 'split': 'split', 'flip': 'flip'}.get(
    os.environ.get('ANP_DM_CROSSHAIR_ONE', '1').strip().lower())
XHAIR_INNER = 'bottom' if os.environ.get('ANP_DM_CROSSHAIR_INNER', 'top').strip().lower() == 'bottom' else 'top'
def xhair_props():
    """weapon template crosshair values for the active ANP_DM_CROSSHAIR_ONE mode, None when off (or DM HUD art off)"""
    if XHAIR_MODE is None or os.environ.get('ANP_DM_HUD', '1') != '1' or os.environ.get('ANP_GRAFT_MENU', '1') != '1':
        return None
    if XHAIR_MODE == 'flip':   # upright in either frame (art mirrored left-right: DM's crosshairs are symmetric)
        return dict(mode='flip', n=1, angle=0 if XHAIR_INNER == 'top' else 180, max=-1.0, gain=-0.5, inner=XHAIR_INNER)
    return dict(mode='split', n=2, angle=0, max=1.0, gain=0.0, inner=XHAIR_INNER)
# slots kl2's builder draws (0xceda10 rows main/shadow/aim/aim-shadow, 0xcedb20 heal/command/select): (main, shadow)
XHAIR_ROWS = [(3, 10), (16, 22), (4, 11), (17, 23), (5, 12), (18, 24), (6, 13), (19, 25), (8, 15), (21, 27),
              (7, None), (30, None), (31, None), (32, None)]
if XHDEFAULT: XHAIR_ROWS.append((2, 9))           # row 11 (Empty): DM Default dot + Subtract_02

def _mips(img, n):
    """RGBA uint8 -> n mip levels (2x2 box, colour weighted by alpha)"""
    np = _np(); out = [img]; f = img.astype(np.float64)
    while len(out) < n and (f.shape[0] > 1 or f.shape[1] > 1):
        a = f[:, :, 3:4]; p = f[:, :, :3] * a
        def box(x):
            if x.shape[0] > 1: x = (x[0::2] + x[1::2]) / 2
            if x.shape[1] > 1: x = (x[:, 0::2] + x[:, 1::2]) / 2
            return x
        a2 = box(a); p2 = box(p)
        col = np.where(a2 > 0.5, p2 / np.maximum(a2, 1e-6), box(f[:, :, :3]))
        f = np.concatenate([col, a2], 2)
        out.append(np.clip(f + 0.5, 0, 255).astype(np.uint8))
    return out

def half_split(img, half=None, inner=None):
    """RGBA (h, w, 4) -> (half texture, half used, error). Built for a builder copy pair where the lower copy shows
    the half texture with its top row on the screen centre and the upper copy shows it turned 180 ('rotation' frame):
    rows 0..h/2 = 'bottom' = the art's rows h/2..h as is, or 'top' = rows 0..h/2 turned 180. error = sum|full -
    rebuilt| / sum(full) over alpha x max(rgb) (alpha for black art), rebuilt = that half below the centre + its 180
    turn above; half None: the lower error. The texture is then put in kl2's frame (XHAIR_INNER, see there):
    'top' (default) mirrored left-right, 'bottom' flipped top-bottom - same screen result in either model."""
    inner = inner or XHAIR_INNER
    np = _np()
    h = img.shape[0]; m = h // 2
    lum = img[:, :, 3].astype(np.float64) * img[:, :, :3].max(2) / 255.0
    if lum.sum() == 0: lum = img[:, :, 3].astype(np.float64)              # black art (Subtract shadows): alpha
    tot = max(lum.sum(), 1e-6)
    best = None
    for hv in (('bottom', 'top') if half is None else (half,)):
        T = np.zeros_like(img)
        T[:h - m] = img[m:] if hv == 'bottom' else img[:h - m][::-1, ::-1]
        L = np.zeros_like(lum); L[:h - m] = lum[m:] if hv == 'bottom' else lum[:h - m][::-1, ::-1]
        rebuilt = np.zeros_like(lum)
        rebuilt[:m] = L[:m][::-1, ::-1]; rebuilt[m:] = L[:h - m]          # above: L turned; below: L upright
        err = float(np.abs(lum - rebuilt).sum() / tot)
        if best is None or err < best[2] - 1e-9: best = (T, hv, err)
    T, hv, err = best
    return (np.ascontiguousarray(T[:, ::-1] if inner == 'top' else T[::-1]), hv, err)

def half_entry(info, blob, name, half=None):
    """split-mode copy of a full-art crosshair texture: DXT5, same size / mip count / flags. -> (entry, half, err)"""
    src = decode(info, blob)
    T, hv, err = half_split(src, half)
    mips = _mips(T, max(1, info['mips']))
    nm = name.encode('latin1') + b'\0'
    body = b''.join(struct.pack('<I', len(d)) + d for d in (encode_dxt5(x) for x in mips))
    e = struct.pack('<I4s4sIHHIIfI', 36 + len(nm) + len(body), b'5TXD', b'5TXD', 0, info['w'], info['h'], len(mips),
                    info['flags'], 1.0, 0) + nm + body
    return e, hv, err

def additive(flags):
    """texture-handle flags of an OSD slot -> drawn additively (0x..002 without 0x200); else alpha blend (0x..200)
    or, for the unlisted slots (0x10), no known widget"""
    return bool(flags & 0x2) and not flags & 0x200
def slot_flags(sl):
    return DD_SLOTS[sl][1] if sl in DD_SLOTS else 0x10
def slot_blend(sl):
    f = slot_flags(sl)
    return 'add' if additive(f) else ('alpha' if f & 0x200 else 'unknown')

def static_pairs():
    """DD slot -> DM slot for widgets both games have (names from both exe tables; crosshair rows from kl2 0xceda10)"""
    p = {0: 0, 1: 1, 3: 2, 16: 2, 4: 3, 17: 3, 5: 4, 18: 4, 6: 5, 19: 5, 7: 6, 30: 7, 31: 8, 32: 9, 33: 16, 34: 17,
         181: 100, 182: 100, 184: 101, 186: 103, 187: 104}
    for k in range(23): p[35 + k] = 18 + k          # DM 18-40 -> DD 35-57 (DD 47 #Coop <- DM 30 Arrow_02 by role)
    if HITDIR: p[189] = 105
    if XHDEFAULT: p[2] = 10                          # Empty row main <- DM Default (shadow 9: SHADOW_OF below)
    return p
# shadow / aim-shadow -> main slot of the Gun, Rifle, MachineGun, Shotgun rows (kl2 0xceda10 columns 1 and 3)
SHADOW_OF = {10: 3, 11: 4, 12: 5, 13: 6, 22: 16, 23: 17, 24: 18, 25: 19}
# DD shadow slot -> Dead Men's Subtract layer for that crosshair (DM exe 0x654660..0x6546c0, drawn with mode 9)
SHADOW_DM = {10: 12, 22: 12, 11: 13, 23: 13, 12: 15, 24: 15, 13: 14, 25: 14}
if XHDEFAULT:                                       # Empty row shadow <- DM Subtract_02 (DM Default 10 -> 11)
    SHADOW_OF[9] = 2; SHADOW_DM[9] = 11
# DD items the player gets without the level placing them (human shield grab: kl2 0x84f4a0 maps them to 63 / 65):
# their picture slots are never parking space
ALWAYS_LIVE_ITEMS = ('HG_M_77B_Human_Shield', 'HG_M9Beretta_Human_Shield')
UNLISTED = [s for s in range(200) if s not in DD_SLOTS]   # loaded by 0x5e3810 (flags 0x10, fmt 5), read by nothing
WEAPON_SLOTS = range(58, 105)                       # DD weapon pictures (105/106 = ammo pickup icons stay)
# Dead Men-only art for the loader widgets, by priority (what does not fit is listed under 'unplaced')
PARK_ORDER = ([41, 42, 43, 73, 74, 75, 76, 77, 86, 87, 88] +      # inventory panel, ammo clips, health, wounded
              [45, 46, 47, 48, 49] +                              # inventory wheel (WeaponSelect3)
              [92, 90, 91, 95, 93, 94, 96, 97, 98, 99] +          # crew orders (ZCommandDisplay2)
              [78, 79, 80, 81, 82, 83, 84, 85] +                  # in-game map
              [89] +                                              # text console
              ['weapons'] +                                       # DM pictures with no DD item slot of their own
              [10, 11, 12, 13, 14, 15, 105])                      # DM crosshair Default/Subtract, hit sphere
ROLE = {}
for _r, _l in (('inventory', (41, 42, 43, 73, 74, 75, 76, 77)), ('health', (86, 87)), ('wounded', (88,)),
               ('wheel', (45, 46, 47, 48, 49)), ('squad', (90, 91, 92, 93, 94, 95, 96, 97, 98, 99)),
               ('map', tuple(range(78, 86))), ('console', (89,)), ('weapon', tuple(range(50, 73))),
               ('crosshair', tuple(range(2, 18))), ('icon', tuple(range(18, 41))), ('hitdir', (105,))):
    for _s in _l: ROLE[_s] = _r

# ---------------------------------------------------------------- .TEX entries
def tex_info(blob, off=0):
    """.TEX entry: +0 size, +4/+8 fourcc ('5TXD' = DXT5), +12 index, +16 u16 w,h, +20 mips, +24 flags, +28 f32,
    +32 0, +36 name\\0, then per mip: u32 size + data"""
    sz = struct.unpack_from('<I', blob, off)[0]
    w, h = struct.unpack_from('<HH', blob, off + 16); mips, fl = struct.unpack_from('<II', blob, off + 20)
    e = blob.index(b'\0', off + 36)
    return dict(size=sz, fourcc=bytes(blob[off + 4:off + 8])[::-1].decode('latin1'), w=w, h=h, mips=mips, flags=fl,
                name=bytes(blob[off + 36:e]).decode('latin1'), mip0=e + 1 - off)   # mip0: relative to the entry

def clear_entry(w=64, h=64, name='tex:UserInterface/ANP/Clear#Clear'):
    """fully transparent (alpha 0, colour 0) DXT5, one mip; index (+12) is set by the caller"""
    n = max(1, w // 4) * max(1, h // 4) * 16
    nm = name.encode('latin1') + b'\0'
    size = 36 + len(nm) + 4 + n
    return struct.pack('<I4s4sIHHIIfI', size, b'5TXD', b'5TXD', 0, w, h, 1, 2, 1.0, 0) + nm + struct.pack('<I', n) + bytes(n)

def encode_dxt5(img):
    """RGBA uint8 (h, w, 4) -> DXT5 blocks (bounding-box colour endpoints, min/max 8-level alpha)"""
    np = _np()
    h, w, _ = img.shape
    H4, W4 = max(4, (h + 3) // 4 * 4), max(4, (w + 3) // 4 * 4)
    if (H4, W4) != (h, w):
        img = np.pad(img, ((0, H4 - h), (0, W4 - w), (0, 0)), mode='edge')
    bh, bw = H4 // 4, W4 // 4
    blk = img.reshape(bh, 4, bw, 4, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 4).astype(np.int64)
    nb = blk.shape[0]
    # alpha: a0 = max, a1 = min, 8-level mode (a0 > a1); a0 == a1 -> every index 0
    A = blk[:, :, 3]; a0 = A.max(1); a1 = A.min(1)
    k = np.arange(2, 8)
    palA = np.concatenate([a0[:, None], a1[:, None], ((8 - k)[None] * a0[:, None] + (k - 1)[None] * a1[:, None]) // 7], 1)
    ai = np.abs(A[:, :, None] - palA[:, None, :]).argmin(2)
    ai[a0 == a1] = 0
    abits = np.zeros(nb, np.uint64)
    for p in range(16): abits |= ai[:, p].astype(np.uint64) << np.uint64(3 * p)
    # colour: per-channel bounding box of the visible texels (all texels if none is visible)
    C = blk[:, :, :3]; m = (A > 0)[:, :, None]
    m = np.where(m.any(1, keepdims=True), m, True)
    cmax = np.where(m, C, 0).max(1); cmin = np.where(m, C, 255).min(1)
    def q(c): return ((c[:, 0] * 31 + 127) // 255) << 11 | ((c[:, 1] * 63 + 127) // 255) << 5 | ((c[:, 2] * 31 + 127) // 255)
    c0, c1 = q(cmax), q(cmin)
    sw = c0 < c1; c0, c1 = np.where(sw, c1, c0), np.where(sw, c0, c1)
    def dq(c): return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], 1)
    k0, k1 = dq(c0), dq(c1)
    pal = np.stack([k0, k1, (2 * k0 + k1) // 3, (k0 + 2 * k1) // 3], 1)          # nb,4,3
    ci = ((C[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(3).argmin(2)
    ci[c0 == c1] = 0
    cbits = np.zeros(nb, np.uint64)
    for p in range(16): cbits |= ci[:, p].astype(np.uint64) << np.uint64(2 * p)
    out = np.zeros((nb, 16), np.uint8)
    out[:, 0] = a0; out[:, 1] = a1
    for qq in range(6): out[:, 2 + qq] = ((abits >> np.uint64(8 * qq)) & np.uint64(255)).astype(np.uint8)
    out[:, 8] = c0 & 255; out[:, 9] = c0 >> 8; out[:, 10] = c1 & 255; out[:, 11] = c1 >> 8
    for qq in range(4): out[:, 12 + qq] = ((cbits >> np.uint64(8 * qq)) & np.uint64(255)).astype(np.uint8)
    return out.tobytes()

def lum_alpha(P, gain=1.0, fill=None):
    """premultiplied colour P (h, w, 3 float, 0..255) -> RGBA uint8: alpha = max channel (x gain), colour = P / alpha
    (texels with no colour get `fill`, the art's mean normalised colour, so DXT blocks and filtering stay clean)"""
    np = _np()
    m = P.max(2)
    col = np.where(m[:, :, None] >= 0.5, P * 255.0 / np.maximum(m, 1e-6)[:, :, None], fill if fill is not None else 255.0)
    a = np.clip(m * gain, 0, 255)
    return np.clip(np.concatenate([col, a[:, :, None]], 2) + 0.5, 0, 255).astype(np.uint8)

def alpha_entry(info, blob, name, gain=1.0):
    """converted copy of an additive-authored texture for an alpha-blend slot: DXT5 flags 2, full mip chain (built
    from the premultiplied colour), name `name`. Returns (entry bytes, RGBA mip 0, source RGBA mip 0)."""
    np = _np()
    src = decode(info, blob)
    P = src[:, :, :3].astype(np.float64) * (src[:, :, 3:4].astype(np.float64) / 255.0)
    m = P.max(2)
    wsum = m.sum()
    fill = ((P * 255.0 / np.maximum(m, 1e-6)[:, :, None]) * m[:, :, None]).reshape(-1, 3).sum(0) / wsum if wsum > 0 else np.array([255.0] * 3)
    w, h = info['w'], info['h']
    mips = []; lvl = P
    while True:
        mips.append(lum_alpha(lvl, gain, fill))
        if lvl.shape[0] == 1 and lvl.shape[1] == 1: break
        hh, ww = lvl.shape[:2]
        if hh > 1: lvl = (lvl[0::2] + lvl[1::2]) / 2
        if ww > 1: lvl = (lvl[:, 0::2] + lvl[:, 1::2]) / 2
    nm = name.encode('latin1') + b'\0'
    body = b''.join(struct.pack('<I', len(d)) + d for d in (encode_dxt5(x) for x in mips))
    size = 36 + len(nm) + len(body)
    e = struct.pack('<I4s4sIHHIIfI', size, b'5TXD', b'5TXD', 0, w, h, len(mips), 2, 1.0, 0) + nm + body
    return e, mips[0], src

class TexFile:
    def __init__(s, data):
        s.d = data
        t1, t2 = struct.unpack_from('<II', data, 0)
        # Dog Days layout: 4096-slot tables at 0x20 / 0x4020; Dead Men: 2048-slot table at [0]
        s.t0 = struct.unpack_from('<%dI' % (4096 if (t1, t2) == (0x20, 0x4020) else 2048), data, t1)
    def has(s, i): return 0 < i < len(s.t0) and s.t0[i] != 0
    def info(s, i): return tex_info(s.d, s.t0[i])
    def blob(s, i):
        o = s.t0[i]; return s.d[o:o + struct.unpack_from('<I', s.d, o)[0]]

# ---------------------------------------------------------------- the plan (graft osd_hook)
def _int_arrays(ops, n):
    res = []
    for q, (p, op, v) in enumerate(ops):
        if op & 0x7f == 1 and v == n and q + n < len(ops) and all(ops[q + 1 + k][1] & 0x7f == 9 for k in range(n)):
            res.append([ops[q + 1 + k][2] for k in range(n)])
    return res

class HudPlan:
    def __init__(s, src_ops, out_ops, dm_tex, rep, level=''):
        arr = _int_arrays(src_ops, 128)
        assert arr, 'Dead Men OSD int[128] not found'
        s.dm_ids = arr[0]
        if any(a != arr[0] for a in arr): rep['DM HUD: Dead Men OSD tables differ, using the first'] += 1
        s.T = TexFile(dm_tex); s.out = out_ops; s.rep = rep; s.level = level; s.result = None
        for d, t in enumerate(s.dm_ids):
            assert t == 0 or s.T.has(t), ('DM OSD id not in the level .TEX', d, t)
        s.items = collections.Counter(v[8:] for (p, op, v) in src_ops
                                      if op & 0x7f == 14 and isinstance(v, str) and v.startswith('eFF2Item'))

    def weapon_pairs(s):
        """DD weapon-picture slot -> DM picture slot (prpconv.ITEM_MAP, then kl2's item -> slot table); a DD slot
        several DM pictures land on gets the one whose items the level uses most (the rest are parked)"""
        from prpconv import ITEM_MAP
        cand = collections.defaultdict(lambda: collections.defaultdict(list)); log = []
        for it, pic in sorted(DM_ITEM_PIC.items()):
            dd = ITEM_MAP.get('eFF2Item' + it, 'eFF2Item' + it)[8:]
            sl = DD_ITEM_SLOT.get(dd)
            if sl is None: log.append('%s -> %s: no DD picture slot' % (it, dd)); continue
            cand[sl][pic].append(it)
        pairs = {}; losers = []
        for sl, pics in sorted(cand.items()):
            rank = sorted(pics, key=lambda p_: (-sum(s.items[i] for i in pics[p_]), p_))
            pairs[sl] = rank[0]
            if len(rank) > 1:
                losers += rank[1:]
                log.append('DD %d %s: DM %s wins over %s (level uses %s)' % (sl, DD_SLOTS[sl][0].split('#')[-1], rank[0],
                           rank[1:], {p_: sum(s.items[i] for i in pics[p_]) for p_ in rank}))
        return pairs, losers, cand, log

    def alpha_copy(s, t, d, new_tex, ex, log):
        """converted copy of DM texture id t (from DM slot d) for an alpha-blend slot -> new id, or None when the
        texture's own alpha already is the luminance alpha (alpha-authored art: keep it)"""
        np = _np()
        info = s.T.info(t)
        e, img, src = alpha_entry(info, bytes(s.T.blob(t)), 'tex:UserInterface/ANP/DMAlpha#%s_DM%d' % (
            DM_SLOTS[d][0].split('#')[-1].replace(' ', '_'), d), ALPHA_GAIN)
        sa = src[:, :, 3].astype(int); na = img[:, :, 3].astype(int)
        diff = np.abs(sa - na)
        if sa.min() < 250 and diff.max() <= 12:
            log.append('DM %d tex %d %s kept: own alpha (max |alpha - lum| %d)' % (d, t, DM_SLOTS[d][0].split('#')[-1], diff.max()))
            return None
        nid = new_tex(e); ex[nid] = tex_info(e)
        log.append('DM %d tex %d %s -> %d (%dx%d, %d mips, alpha max %d, was %d..%d)' % (
            d, t, DM_SLOTS[d][0].split('#')[-1], nid, info['w'], info['h'], ex[nid]['mips'], na.max(), sa.min(), sa.max()))
        return nid

    def hook(s, tables, new_tex, extra):
        rep = s.rep; dm = s.dm_ids; ex = {sl: tex_info(b) for sl, b in extra.items()}
        blobs = dict(extra)                         # tex id -> entry bytes (grafted + made here)
        def mk(e):
            nid = new_tex(e); blobs[nid] = e; return nid
        before = [[o[2] for o in t] for t in tables]
        for t in tables: assert len(t) == 200
        if any(b != before[0] for b in before): rep['DM HUD: grafted OSD tables differ before the edit'] += 1
        plan = {}                                   # dd slot -> dict(kind, dm, tex)
        pairs = static_pairs()
        wlog = []; losers = []; wcand = {}
        if WEAPONS:
            wp, losers, wcand, wlog = s.weapon_pairs()
            for sl, pic in wp.items(): pairs[sl] = pic
            for l in wlog: rep['DM HUD weapon %s' % l] += 1
        for sl, d in sorted(pairs.items()):
            if not dm[d]: rep['DM HUD: DM slot %d empty in this level, DD %d kept' % (d, sl)] += 1; continue
            plan[sl] = dict(kind='subst', dm=d, tex=dm[d])
        cid = None
        def clear_id():
            nonlocal cid
            if cid is None:
                cid = new_tex(clear_entry()); ex[cid] = tex_info(clear_entry())
            return cid
        for sl, main in sorted(SHADOW_OF.items()):
            if main not in plan: continue
            d = SHADOW_DM[sl]
            if SUBTRACT and dm[d]:
                plan[sl] = dict(kind='subst', dm=d, tex=dm[d])
            else:
                plan[sl] = dict(kind='clear', dm=None, tex=clear_id())
        if NOHITMARK:                               # Dog Days hit / kill markers (ZHitEnemyDisplay): hidden
            for sl in HITMARK_SLOTS:
                plan[sl] = dict(kind='clear', dm=None, tex=clear_id(), why='hitmarker')
            rep['DM HUD (ANP_DM_HUD_NOHITMARK): Dog Days hit markers %s -> clear texture %d' % (
                list(HITMARK_SLOTS), cid)] += 1
        # ---- parking
        unplaced = []
        if PARK:
            from prpconv import ITEM_MAP
            live_items = set(v[8:] for (p, op, v) in s.out
                             if op & 0x7f == 14 and isinstance(v, str) and v.startswith('eFF2Item'))
            live_items |= set(v[8:] for v in ITEM_MAP.values()) | set(ALWAYS_LIVE_ITEMS)
            live = {DD_ITEM_SLOT[i] for i in live_items if i in DD_ITEM_SLOT} | set(plan)
            free_u = [sl for sl in UNLISTED if all(b[sl] == 0 for b in before)]
            free_w = [sl for sl in WEAPON_SLOTS if sl not in live]
            rep['DM HUD spare slots: %d unlisted, %d weapon pictures of items this level cannot hold' % (len(free_u), len(free_w))] += 1
            placed = {}                                 # tex id -> dd slot
            for sl, p_ in plan.items():
                if p_['kind'] == 'subst': placed.setdefault(p_['tex'], sl)
            order = []
            for x in PARK_ORDER:
                if x == 'weapons':
                    order += [d for d in list(range(50, 73)) if d not in [pp['dm'] for pp in plan.values()]]
                else: order.append(x)
            for d in order:
                t = dm[d]
                if not t or t in placed: continue
                pools = (free_u, free_w) if DM_SLOTS[d][2] == 5 else (free_w, free_u)
                pool = next((q for q in pools if q), None)
                if pool is None: unplaced.append(d); continue
                sl = pool.pop(0); plan[sl] = dict(kind='park', dm=d, tex=t); placed[t] = sl
            if unplaced: rep['DM HUD: no spare slot for DM %s' % unplaced] += 1
        # ---- alpha: additive-authored DM art in a non-additive DD slot -> converted copy (see the module doc)
        conv = {}; alpha_log = []
        if ALPHA:
            for sl, p_ in sorted(plan.items()):
                if p_['kind'] == 'clear' or p_['dm'] is None: continue
                if not additive(DM_SLOTS[p_['dm']][1]) or additive(slot_flags(sl)): continue
                t = p_['tex']
                if t not in conv: conv[t] = s.alpha_copy(t, p_['dm'], mk, ex, alpha_log)
                if conv[t]: p_.update(src_tex=t, tex=conv[t], alpha='lum')
                else: p_['alpha'] = 'kept'
            for l in alpha_log: rep['DM HUD alpha: %s' % l] += 1
            rep['DM HUD alpha (ANP_DM_HUD_ALPHA) gain %g: %d textures converted, %d kept (own alpha), %d slots' % (
                ALPHA_GAIN, sum(1 for v in conv.values() if v), sum(1 for v in conv.values() if not v),
                sum(1 for p_ in plan.values() if p_.get('alpha') == 'lum'))] += 1
        # ---- one crosshair (ANP_DM_CROSSHAIR_ONE, see xhair_props): split mode -> half copies of full-art slots
        XP = xhair_props(); halves = {}; xlog = []
        if XP and XP['mode'] == 'split':
            np = _np(); hcache = {}
            def cur(sl): return plan[sl]['tex'] if sl in plan else before[0][sl]
            def blob_of(t): return blobs[t] if t in blobs else (bytes(s.T.blob(t)) if s.T.has(t) else None)
            def half_of(sl, t, half):
                if (t, half) in hcache: return hcache[(t, half)]
                b = blob_of(t); info = tex_info(b)
                e, hv, err = half_entry(info, b, 'tex:UserInterface/ANP/DMHalf#%s_%d' % (
                    info['name'].split('#')[-1].split('/')[-1].replace(' ', '_'), t), half)
                nid = mk(e); ex[nid] = tex_info(e); hcache[(t, half)] = (nid, hv, err); return hcache[(t, half)]
            for main, sh in XHAIR_ROWS:
                t = cur(main); b = blob_of(t) if t else None
                if not b: xlog.append('slot %d: no texture' % main); continue
                info = tex_info(b)
                if 'KL2_Crosshair_01' in info['name']:
                    xlog.append('slot %d: Dog Days arm art %s kept (drawn %dx: no DM art for this row)' % (main, info['name'], XP['n']))
                    rep['DM HUD crosshair: slot %d keeps Dog Days arm art' % main] += 1; continue
                if decode(info, b)[:, :, 3].max() == 0: xlog.append('slot %d: empty texture %d' % (main, t)); continue
                nid, hv, err = half_of(main, t, None)
                row = [(main, t, nid, hv, err)]
                if sh is not None:
                    ts = cur(sh); bs = blob_of(ts) if ts else None
                    if bs and decode(tex_info(bs), bs)[:, :, 3].max() > 0:
                        n2, _, e2 = half_of(sh, ts, hv); row.append((sh, ts, n2, hv, e2))
                for sl, t0, nid, hv, err in row:
                    if sl in plan: plan[sl].update(half_src=t0, tex=nid, half=hv, half_err=round(err, 3))
                    else: plan[sl] = dict(kind='half', dm=None, tex=nid, half_src=t0, half=hv, half_err=round(err, 3))
                    halves[sl] = dict(src=t0, tex=nid, half=hv, err=round(err, 3))
                    xlog.append('slot %d: tex %d -> %d half %s (180-degree rebuild error %.3f)' % (sl, t0, nid, hv, err))
            for l in xlog: rep['DM HUD crosshair: %s' % l] += 1
        if XP:
            rep['DM HUD crosshair (ANP_DM_CROSSHAIR_ONE %s): weapons N=%d angle %d max %g gain %g; %d slots halved, %d half textures' % (
                XP['mode'], XP['n'], XP['angle'], XP['max'], XP['gain'], len(halves),
                len(set(v['tex'] for v in halves.values())))] += 1
        # ---- checks + write both tables
        nfl = 0
        for sl, p_ in sorted(plan.items()):
            assert p_['tex'], (sl, p_)
            if p_['kind'] != 'subst': continue
            a = ex[p_['tex']] if p_['tex'] in ex else s.T.info(p_['tex']); b0 = before[0][sl]
            if b0 and b0 in ex and (ex[b0]['w'], ex[b0]['h']) != (a['w'], a['h']):
                rep['DM HUD size differs: DD %d %dx%d <- DM %d %dx%d' % (sl, ex[b0]['w'], ex[b0]['h'], p_['dm'], a['w'], a['h'])] += 1
            if sl in DD_SLOTS and DD_SLOTS[sl][1:] != DM_SLOTS[p_['dm']][1:]: nfl += 1
        for t in tables:
            for sl, p_ in plan.items(): t[sl][2] = p_['tex']
        after = [o[2] for o in tables[0]]
        kinds = collections.Counter(p_['kind'] for p_ in plan.values())
        rep['DM HUD (ANP_DM_HUD) %d tables: %d subst, %d clear, %d parked; slot flag/fmt differs on %d subst' % (
            len(tables), kinds['subst'], kinds['clear'], kinds['park'], nfl)] += 1
        if kinds['half']: rep['DM HUD: %d Dog Days crosshair slots halved (kind half)' % kinds['half']] += 1
        # ---- sidecar
        dm2dd = collections.defaultdict(list)
        for sl, p_ in sorted(plan.items()):
            if p_['dm'] is not None: dm2dd[p_['dm']].append(sl)
        for d, t in enumerate(dm):              # same texture placed under another DM slot (Follow x3, smoke trail x2)
            if t and d not in dm2dd:
                same = [sl for sl, p_ in sorted(plan.items()) if p_['tex'] == t and p_['kind'] != 'clear']
                if same: dm2dd[d] = same
        def dinfo(t):
            a = ex[t] if t in ex else (s.T.info(t) if s.T.has(t) else None)
            return dict(w=a['w'], h=a['h'], fourcc=a['fourcc']) if a else {}
        slots = {}
        for sl, p_ in sorted(plan.items()):
            e = dict(kind=p_['kind'], tex=p_['tex'], dd_name=DD_SLOTS[sl][0] if sl in DD_SLOTS else None)
            if p_['dm'] is not None:
                e.update(dm=p_['dm'], dm_name=DM_SLOTS[p_['dm']][0], role=ROLE.get(p_['dm'], 'other'),
                         dm_flags=DM_SLOTS[p_['dm']][1], dm_fmt=DM_SLOTS[p_['dm']][2])
            e['dd_flags'], e['dd_fmt'] = (DD_SLOTS[sl][1], DD_SLOTS[sl][2]) if sl in DD_SLOTS else (0x10, 5)
            e['blend'] = slot_blend(sl)
            if 'alpha' in p_: e['alpha'] = p_['alpha']
            if 'src_tex' in p_: e['src_tex'] = p_['src_tex']
            if 'why' in p_: e['why'] = p_['why']
            for k_ in ('half', 'half_src', 'half_err'):
                if k_ in p_: e[k_] = p_[k_]
            e.update(dinfo(p_['tex'])); slots[str(sl)] = e
        s.result = dict(
            version=3, level=s.level, tables=len(tables), clear_tex=cid,
            note='OSD slot s of the grafted ZOnScreenDisplay2: TEX-id array at obj+0xd68, runtime record {handle,w,h} '
                 'at obj+0x3ec+12*s (kl2 0x5e3810 loads every non-zero id). kind subst = DD widget draws DM art; '
                 'park = DM-only art for loader widgets; clear = transparent crosshair shadow.',
            slots=slots, dm_to_dd={str(d): v for d, v in sorted(dm2dd.items())},
            dm_tex=dm, dm_slot_names={str(d): DM_SLOTS[d][0] for d in sorted(DM_SLOTS)},
            dd_before=before[0], dd_after=after, unplaced=unplaced,
            alpha=dict(enabled=ALPHA, gain=ALPHA_GAIN, converted={str(k): v for k, v in sorted(conv.items()) if v},
                       kept=sorted(k for k, v in conv.items() if not v), log=alpha_log,
                       rule='DM slot additive (flags 0x2, no 0x200) -> DD slot not additive: alpha = max(rgb*a), '
                            'rgb = rgb*a / alpha; kept if that equals the texture\'s own alpha'),
            crosshair=dict(XP or dict(mode='off'), halves={str(k): v for k, v in sorted(halves.items())}, log=xlog,
                           rule='weapon templates (0x10048d) fields 60 N +0x220, 61 start angle +0x221, 63 max +0x228, '
                                '64 gain +0x22c (prpconv.crosshair_one); split: every full-art builder slot holds one '
                                'half (rows 0..h/2, texture top = screen centre), N=2 draws it below and turned above'),
            weapons=dict(dm_item_pic=DM_ITEM_PIC,
                         dd_slot_candidates={str(sl): {str(p_): its for p_, its in v.items()} for sl, v in sorted(wcand.items())},
                         parked_losers=losers, log=wlog,
                         level_items={k: v for k, v in sorted(s.items.items())}))

# ---------------------------------------------------------------- DXT decode + PNG (no PIL)
def _np():
    import numpy as np
    return np

def decode(info, blob):
    """mip 0 -> RGBA uint8 array (h, w, 4)"""
    np = _np()
    w, h, fc = info['w'], info['h'], info['fourcc']
    o = info['mip0']; n = struct.unpack_from('<I', blob, o)[0]; data = blob[o + 4:o + 4 + n]
    bw, bh = max(1, (w + 3) // 4), max(1, (h + 3) // 4); nb = bw * bh
    bs = 8 if fc == 'DXT1' else 16
    a = np.frombuffer(data[:nb * bs], np.uint8).reshape(nb, bs)
    cb = a[:, bs - 8:].astype(np.uint32)
    c0 = cb[:, 0] | cb[:, 1] << 8; c1 = cb[:, 2] | cb[:, 3] << 8
    def rgb(c): return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], 1).astype(np.float32)
    k0, k1 = rgb(c0), rgb(c1)
    four = (c0 > c1) | (fc != 'DXT1')
    k2 = np.where(four[:, None], (2 * k0 + k1) / 3, (k0 + k1) / 2)
    k3 = np.where(four[:, None], (k0 + 2 * k1) / 3, 0)
    pal = np.stack([k0, k1, k2, k3], 1)                                   # nb,4,3
    bits = cb[:, 4] | cb[:, 5] << 8 | cb[:, 6] << 16 | cb[:, 7] << 24
    idx = np.stack([(bits >> (2 * p)) & 3 for p in range(16)], 1)        # nb,16
    col = np.take_along_axis(pal, idx[:, :, None].repeat(3, 2).astype(np.int64), 1)
    if fc == 'DXT1':
        al = np.where((~four[:, None]) & (idx == 3), 0, 255)
    elif fc == 'DXT3':
        ab = a[:, :8].astype(np.uint64); v = np.zeros(nb, np.uint64)
        for q in range(8): v |= ab[:, q] << np.uint64(8 * q)
        al = np.stack([((v >> np.uint64(4 * p)) & np.uint64(15)).astype(np.int64) * 17 for p in range(16)], 1)
    else:
        a0 = a[:, 0].astype(np.int64); a1 = a[:, 1].astype(np.int64)
        v = np.zeros(nb, np.uint64)
        for q in range(6): v |= a[:, 2 + q].astype(np.uint64) << np.uint64(8 * q)
        ai = np.stack([((v >> np.uint64(3 * p)) & np.uint64(7)).astype(np.int64) for p in range(16)], 1)
        big = (a0 > a1)[:, None]
        palA = []
        for i in range(8):
            if i == 0: pa = a0[:, None].repeat(1, 1)
            elif i == 1: pa = a1[:, None]
            else:
                p8 = ((8 - i) * a0 + (i - 1) * a1) // 7
                p6 = ((6 - i) * a0 + (i - 1) * a1) // 5 if i < 6 else (np.zeros_like(a0) if i == 6 else np.full_like(a0, 255))
                pa = np.where(big[:, 0], p8, p6)[:, None]
            palA.append(pa)
        palA = np.concatenate(palA, 1)                                      # nb,8
        al = np.take_along_axis(palA, ai, 1)
    px = np.concatenate([col, al[:, :, None].astype(np.float32)], 2)       # nb,16,4
    img = px.reshape(bh, bw, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(bh * 4, bw * 4, 4)
    return np.clip(img[:h, :w], 0, 255).astype(np.uint8)

def write_png(path, rgb):
    np = _np(); h, w, _ = rgb.shape
    raw = b''.join(b'\0' + rgb[y].tobytes() for y in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

_F = {'0': '111101101101111', '1': '010110010010111', '2': '111001111100111', '3': '111001111001111',
      '4': '101101111001001', '5': '111100111001111', '6': '111100111101111', '7': '111001001010010',
      '8': '111101111101111', '9': '111101111001111', 'A': '010101111101101', 'B': '110101110101110',
      'C': '011100100100011', 'D': '110101101101110', 'E': '111100110100111', 'F': '111100110100100',
      'G': '011100101101011', 'H': '101101111101101', 'I': '111010010010111', 'J': '001001001101010',
      'K': '101101110101101', 'L': '100100100100111', 'M': '101111111101101', 'N': '110101101101101',
      'O': '010101101101010', 'P': '110101110100100', 'Q': '010101101110011', 'R': '110101110101101',
      'S': '011100010001110', 'T': '111010010010010', 'U': '101101101101111', 'V': '101101101101010',
      'W': '101101111111101', 'X': '101101010101101', 'Y': '101101010010010', 'Z': '111001010100111',
      '-': '000000111000000', '_': '000000000000111', '#': '101111101111101', '<': '001010100010001',
      '>': '100010001010100', '/': '001001010100100', '.': '000000000000010', ':': '000010000010000',
      '=': '000111000111000', '(': '010100100100010', ')': '010001001001010', '+': '000010111010000',
      '|': '010010010010010', ',': '000000000010100', ' ': '000000000000000'}

def text(img, x, y, s, col, sc=2):
    for ch in s.upper():
        g = _F.get(ch, _F[' '] if ch == ' ' else '111111111111111')
        for r in range(5):
            for c in range(3):
                if g[r * 3 + c] == '1':
                    y0, x0 = y + r * sc, x + c * sc
                    if 0 <= y0 and y0 + sc <= img.shape[0] and 0 <= x0 and x0 + sc <= img.shape[1]:
                        img[y0:y0 + sc, x0:x0 + sc] = col
        x += 4 * sc
    return x

def _short(n):
    if not n: return ''
    n = n.split('#')[-1] if '#' in n else n.split('/')[-1]
    return n

def sheet(zip_path, png_path, T=64):
    """offline HUD contact sheet: every DD OSD slot, Dog Days art before | the level's art after | after over grey
    (blended as the slot draws it); on top, the 'over grey' preview rows: crosshair + shadow and every alpha-converted
    texture, Dog Days original | raw Dead Men art (the pre-ANP_DM_HUD_ALPHA look) | now, over grey / dark / bright"""
    np = _np()
    sys.path.insert(0, os.path.dirname(__file__))
    from zipraw import read_zip, read_entry
    ents = {e.name: e for e in read_zip(zip_path)}
    hn = next(n for n in ents if n.endswith('/ANP_hud.json'))
    H = json.loads(read_entry(ents[hn]))
    tex = TexFile(read_entry(ents[next(n for n in ents if n.endswith('.TEX'))]))
    dec = {}
    def rgba(t, S):
        """texture t fitted into S x S (nearest), float RGBA, or None"""
        if (t, S) in dec: return dec[(t, S)]
        if not t or not tex.has(t): dec[(t, S)] = None; return None
        info = tex.info(t)
        try: im = decode(info, bytes(tex.blob(t)))
        except Exception: im = np.full((4, 4, 4), (255, 0, 255, 255), np.uint8)
        h, w = im.shape[:2]; k = min(S / w, S / h)
        nw, nh = max(1, int(w * k)), max(1, int(h * k))
        ys = (np.arange(nh) * h // nh); xs = (np.arange(nw) * w // nw)
        dec[(t, S)] = (im[ys][:, xs].astype(np.float32), info['w'], info['h']); return dec[(t, S)]
    def over(bg, layers, S):
        """layers [(tex, blend)] composited over bg (S x S x 3 float): 'add' = dst + src*a, else src*a + dst*(1-a)"""
        out = bg.copy()
        for t, mode in layers:
            r = rgba(t, S)
            if not r: continue
            im = r[0]; h, w = im.shape[:2]; y, x = (S - h) // 2, (S - w) // 2
            a = im[:, :, 3:4] / 255.0; d = out[y:y + h, x:x + w]
            out[y:y + h, x:x + w] = np.clip(d + im[:, :, :3] * a, 0, 255) if mode == 'add' else im[:, :, :3] * a + d * (1 - a)
        return out.astype(np.uint8)
    def checker(S):
        yy, xx = np.mgrid[0:S, 0:S]
        return np.repeat(np.where(((yy // 8) + (xx // 8)) % 2 == 0, 70, 40)[:, :, None], 3, 2).astype(np.float32)
    def flat(S, v): return np.full((S, S, 3), float(v), np.float32)
    def grad(S): return np.repeat(np.repeat(np.linspace(20, 235, S, dtype=np.float32)[None, :, None], S, 0), 3, 2)
    def arms(bg, layers, S, n=4, ang=0.0, R=1.0, A=1.0, span=160.0, mirror=None):
        """kl2's crosshair sprite builder (0x4fd660, see xhair_props) at native texel size x S/span: copy k turned by
        ang + k*360/n, dir = (sin, -cos) (screen y down; 0x4f2c50's turn sense unverified, only matters for N=3),
        quad (UV 0,0 at local -.5,-.5) rotated x' = x*dy - y*dx, y' = x*dx + y*dy, drawn at centre + (mx*x'*W, my*y'*H)
        with (mx, my) = (-1, 1) for XHAIR_INNER 'top', (1, -1) for 'bottom' (the renderer's mirrored axis), size
        (W,H) = (w,h)*A, centre = screen centre + (w/2*dx, h/2*dy)*R"""
        mx, my = mirror or ((-1, 1) if XHAIR_INNER == 'top' else (1, -1))
        out = bg.astype(np.float32).copy(); sc = S / span; c = S / 2.0
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float64) + 0.5
        for t, mode in layers:
            if not t or not tex.has(t): continue
            info = tex.info(t)
            try: im = decode(info, bytes(tex.blob(t))).astype(np.float32)
            except Exception: continue
            h, w = im.shape[:2]
            for k in range(n):
                th = np.radians(ang + k * 360.0 / n); dx, dy = np.sin(th), -np.cos(th)
                cx, cy = c + w / 2 * dx * R * sc, c + h / 2 * dy * R * sc
                qx, qy = (xx - cx) / (mx * w * A * sc), (yy - cy) / (my * h * A * sc)
                lx, ly = qx * dy + qy * dx, -qx * dx + qy * dy
                ok = (np.abs(lx) < 0.5) & (np.abs(ly) < 0.5)
                u = np.clip(((lx + 0.5) * w).astype(int), 0, w - 1); v = np.clip(((ly + 0.5) * h).astype(int), 0, h - 1)
                px = im[v, u]; a = np.where(ok, px[:, :, 3] / 255.0, 0)[:, :, None]
                out = np.clip(out + px[:, :, :3] * a, 0, 255) if mode == 'add' else px[:, :, :3] * a + out * (1 - a)
        return out.astype(np.uint8)
    XH = H.get('crosshair') or {}
    xh_mode = XH.get('mode', 'absent')
    xh = {'split': (2, 0, 1.0, 1.0), 'flip': (1, 0, 0.0, -1.0)}.get(xh_mode, (4, 0, 1.26, 1.1))   # n, angle, R, A
    if 'n' in XH: xh = (XH['n'], XH['angle']) + xh[2:]
    DD_STOCK = {3: (4, 0), 4: (4, 0), 5: (3, 0), 6: (2, 90)}       # stock Dog Days N / angle per row (F01 templates)
    blend = lambda sl: H['slots'].get(str(sl), {}).get('blend') or slot_blend(sl)
    # ---------------- 'over grey' preview rows
    B, P, LH = 128, 8, 12
    items = []
    for main, sh in ((3, 10), (4, 11), (5, 12), (6, 13)):
        if str(main) in H['slots']: items.append((main, sh))
    for sl, e in sorted(H['slots'].items(), key=lambda x: int(x[0])):
        if e.get('alpha') == 'lum' and int(sl) not in (3, 4, 5, 6, 16, 17, 18, 19): items.append((int(sl), None))
    COLS, LH2 = 6, 12
    CW = 3 * T + 4 * P + 40; CH = 3 * LH2 + T + 2 * P
    rows = (200 + COLS - 1) // COLS
    W_ = max(COLS * CW + 2 * P, 200 + 8 * (B + P) + 2 * P)
    PH = 64 + len(items) * (B + 2 * LH + P) + 16
    H_ = PH + rows * CH + 60
    img = np.full((H_, W_, 3), 24, np.uint8)
    text(img, P, 10, 'ANP DM HUD  %s  -  OVER GREY PREVIEW: EACH LAYER BLENDED AS ITS SLOT DRAWS IT' % H.get('level', ''), (230, 230, 230))
    text(img, P, 26, 'ALPHA SLOTS (FLAGS 0X200): SRC*A + DST*(1-A).  ADD SLOTS (0X2): DST + SRC*A.  CROSSHAIR = SHADOW, THEN MAIN.', (170, 170, 170))
    al = H.get('alpha') or {}
    text(img, P, 40, 'ANP_DM_HUD_ALPHA %s  GAIN %s  CONVERTED %s  KEPT %s' % (
        'ON' if al.get('enabled') else 'OFF/ABSENT', al.get('gain', '-'),
        ' '.join('%s>%s' % kv for kv in sorted(al.get('converted', {}).items())) or '-', al.get('kept', '-')), (170, 170, 170))
    heads = ('DOG DAYS ORIGINAL', 'RAW DM ART (OLD)', 'NOW / GREY', 'NOW / DARK', 'NOW / GRADIENT')
    y = 64
    for main, sh in items:
        e = H['slots'][str(main)]
        old = lambda sl: H['slots'].get(str(sl), {}).get('src_tex') or H['dd_after'][sl]
        lay_dd = [(H['dd_before'][sh], blend(sh))] if sh is not None else []
        lay_dd.append((H['dd_before'][main], blend(main)))
        lay_old = ([(old(sh), blend(sh))] if sh is not None else []) + [(old(main), blend(main))]
        lay_new = ([(H['dd_after'][sh], blend(sh))] if sh is not None else []) + [(H['dd_after'][main], blend(main))]
        nm = '%03d %s' % (main, _short(e.get('dd_name') or '(UNLISTED)'))
        text(img, P, y + 4, nm[:24], (220, 220, 220))
        text(img, P, y + 4 + LH, ('%s DM%s %s' % (e['kind'].upper(), e.get('dm', ''), _short(e.get('dm_name'))))[:24], (150, 150, 150))
        text(img, P, y + 4 + 2 * LH, ('SLOT %s, %s' % (blend(main).upper(), 'ALPHA CONVERTED' if e.get('alpha') == 'lum' else 'AS IS'))[:24],
             (60, 200, 90) if e.get('alpha') == 'lum' else (150, 150, 150))
        if sh is not None: text(img, P, y + 4 + 3 * LH, ('+ SHADOW %03d' % sh), (150, 150, 150))
        tiles = [over(flat(B, 128), lay_dd, B), over(flat(B, 128), lay_old, B), over(flat(B, 128), lay_new, B),
                 over(flat(B, 40), lay_new, B), over(grad(B), lay_new, B)]
        hd_ = list(heads)
        if sh is not None:
            n_, a_ = DD_STOCK.get(main, (4, 0))
            tiles.append(arms(flat(B, 128), lay_dd, B, n_, a_)); hd_.append('DD IN GAME N%d F=1' % n_)
            tiles.append(arms(flat(B, 128), lay_new, B, xh[0], xh[1], xh[2], xh[3]))
            hd_.append('IN GAME %s N%d' % (xh_mode.upper(), xh[0]))
            # Dead Men's own draw (one sprite, centred, upright) at the same scale, from the pre-half textures
            pre = lambda sl: H['slots'].get(str(sl), {}).get('half_src') or H['dd_after'][sl]
            tiles.append(arms(flat(B, 128), [(pre(sh), blend(sh)), (pre(main), blend(main))], B, 1, 180, 0.0, 1.0,
                              mirror=(1, 1)))
            hd_.append('DEAD MEN (TARGET)')
        for k_, (hd, tl) in enumerate(zip(hd_, tiles)):
            tx = 200 + k_ * (B + P); ty = y + LH + 4
            text(img, tx, y + 2, hd, (200, 200, 200) if k_ != 1 else (220, 120, 120), 1)
            img[ty - 1:ty + B + 1, tx - 1:tx + B + 1] = (70, 70, 70); img[ty:ty + B, tx:tx + B] = tl
        y += B + 2 * LH + P
    img[PH - 6:PH - 4, P:W_ - P] = (90, 90, 90)
    # ---------------- every slot: before | after | after over grey
    KC = {'subst': (60, 200, 90), 'park': (80, 150, 255), 'clear': (255, 160, 40), 'half': (200, 120, 255)}
    text(img, P, PH + 4, 'EACH DD OSD SLOT: DOG DAYS ART BEFORE | AFTER (CHECKER = ALPHA 0) | AFTER OVER GREY, AS THE SLOT BLENDS', (230, 230, 230))
    x = text(img, P, PH + 20, 'GREEN = DD WIDGET NOW DRAWS DM ART   ', KC['subst'])
    x = text(img, x, PH + 20, 'BLUE = DM-ONLY ART PARKED FOR LOADER   ', KC['park'])
    x = text(img, x, PH + 20, 'ORANGE = TRANSPARENT SHADOW   ', KC['clear'])
    x = text(img, x, PH + 20, 'A = ALPHA-CONVERTED COPY   ', (255, 230, 90))
    text(img, x, PH + 20, 'HB/HT = CROSSHAIR HALF (SPLIT)', KC['half'])
    text(img, P, PH + 34, 'SIZE UNDER EACH THUMB.  %d SUBST %d PARK %d CLEAR' % tuple(
        sum(1 for v in H['slots'].values() if v['kind'] == k) for k in ('subst', 'park', 'clear')), (160, 160, 160))
    for sl in range(200):
        r, c = divmod(sl, COLS); x0 = P + c * CW; y0 = PH + 50 + r * CH
        e = H['slots'].get(str(sl)); b, a = H['dd_before'][sl], H['dd_after'][sl]
        col = KC[e['kind']] if e else (110, 110, 110)
        if e: img[y0:y0 + CH - 3, x0:x0 + CW - 4] = (40, 40, 48)
        if e:
            img[y0:y0 + 2, x0:x0 + CW - 4] = col; img[y0 + CH - 5:y0 + CH - 3, x0:x0 + CW - 4] = col
        ddn = _short(DD_SLOTS[sl][0]) if sl in DD_SLOTS else '(UNLISTED)'
        text(img, x0 + 3, y0 + 4, ('%03d %s' % (sl, ddn))[:30], (220, 220, 220) if e else (150, 150, 150))
        if e:
            lab = {'subst': '<- DM%d %s', 'park': 'PARK DM%d %s'}.get(e['kind'])
            lab = lab % (e['dm'], _short(e['dm_name'])) if lab else ('DD ART' if e['kind'] == 'half' else
                                                                     'CLEAR (HIDDEN)' if e.get('why') else 'CLEAR (NO SHADOW)')
            if e.get('alpha') == 'lum': lab = 'A ' + lab
            if e.get('half'): lab = 'H' + e['half'][0].upper() + ' ' + lab
            text(img, x0 + 3, y0 + 4 + LH2, lab[:30], (255, 230, 90) if e.get('alpha') == 'lum' else col)
        for k_, t in enumerate((b, a, a)):
            tx = x0 + 3 + k_ * (T + P + 12) + (8 if k_ == 2 else 0); ty = y0 + 2 * LH2 + 4
            img[ty - 1:ty + T + 1, tx - 1:tx + T + 1] = (60, 60, 60); img[ty:ty + T, tx:tx + T] = 30
            r_ = rgba(t, T)
            if r_:
                tl = over(checker(T), [(t, 'alpha')], T) if k_ < 2 else over(flat(T, 128), [(t, blend(sl))], T)
                img[ty:ty + T, tx:tx + T] = tl
                if k_ < 2: text(img, tx, ty + T + 3, '%dX%d' % (r_[1], r_[2]), (140, 140, 140), 1)
                else: text(img, tx, ty + T + 3, 'GREY ' + blend(sl).upper(), (140, 140, 140), 1)
            else:
                text(img, tx + T // 2 - 8, ty + T // 2 - 5, '-', (90, 90, 90))
        text(img, x0 + T + P + 4, y0 + 2 * LH2 + 4 + T // 2 - 5, '>', (200, 200, 200) if b != a else (80, 80, 80))
    write_png(png_path, img)
    return H

if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'sheet':
        H = sheet(sys.argv[2], sys.argv[3]); print('wrote', sys.argv[3], 'slots changed', len(H['slots']))
    elif len(sys.argv) >= 3 and sys.argv[1] == 'show':
        sys.path.insert(0, os.path.dirname(__file__))
        from zipraw import read_zip, read_entry
        ents = {e.name: e for e in read_zip(sys.argv[2])}
        H = json.loads(read_entry(ents[next(n for n in ents if n.endswith('/ANP_hud.json'))]))
        for sl, e in sorted(H['slots'].items(), key=lambda x: int(x[0])):
            print('%3s %-6s tex %4d %-40s <- %s' % (sl, e['kind'], e['tex'], (e['dd_name'] or '(unlisted)')[-40:],
                                                   e.get('dm_name', '')))
        print('unplaced', H['unplaced'])
    else:
        print(__doc__)
