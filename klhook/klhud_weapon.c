/*
 * klhud_weapon.c - THE WEAPON DIAL of the owner's HUD draft (re\hud_layout.md 'weapon dial'; track W, 2026-10-11):
 * ONE circle bottom right holding both guns - the gun in hand on top, bright, with the rounds in its magazine; the
 * other gun below, small and dim, with all the ammo it has; the ring = the magazine of the gun in hand (32 dabs,
 * picture 113; the part that is LEFT is drawn FROM THE TOP CLOCKWISE, the gap is the last part - the draft's weapon
 * dial, 'stroke-dasharray 80 100', runs the other way round than its watch and escape dial, so this file has its own
 * loop and does not use klu_ring); under the circle 'NAME . reserve' - with the stock ammo panel not drawn.
 * Part of klhud.c: #included by it (after klu_dials), it uses klhud.c's text objects, picture queue, lock and gate.
 * OFF unless [HUD] Enable=1 AND Weapon=1. COMPILED ONLY - NOTHING OF IT HAS RUN IN THE GAME. The reading with every
 * address, the wiring and the live checks: re\hud_weapon.md (9 = the review round: what each finding changed here).
 *
 * 1. WHAT THE STOCK PANEL IS (EXE = read in kl2.exe build 0490; re\hud_weapon.md 1 - 3 has the whole Render)
 *    ZWeaponDisplay, element at osd+0x1110, vtable 0xbbe8c0, 0x151c bytes. Slot 5 Tick 0x5b1e00 runs 0x88bac0(i) for
 *    i = 0, 1. Slot i = one gun: 0 = the SELECTED weapon, item id [player+0x924] (kept while holstered; fall-backs
 *    0x748430(player), then the first weapon of the inventory), 1 = the other weapon of the inventory
 *    (0x49b2f0(inv, item0, 4)). [player+0x920] = the item id in the hand, 0 = hands empty: it only decides bright or dim.
 *    The gun OBJECT = 0x417bc0(inv = [player+0xcec], item): the 16-byte entry {item, ?, object, info} of the array
 *    [inv+8] (count [inv+0xc]; byte [inv+4] = 0: indexed by the item id, else searched).
 *      rounds in the magazine  = weapon vt+0x2fc = 0x511f50:  [weapon+0xdc] ^ 0xbeebbeeb
 *      reserve                 = 0x8b80e0(weapon, 1):          [weapon+0xe0] ^ 0xbeebbeeb  (999 - rounds for a gun with
 *                                endless ammo: template byte +0x138, or the game option byte)
 *      magazine size           = weapon vt+0x304 = 0x6c93d0: three virtual calls deep (template, ammo object) - NOT
 *                                taken from there, see below
 *    What the element keeps after its Tick, and what this part reads:
 *      +0x2e8 + 4 i  HUD picture index of gun i (table [0x154db68 + 4 * item], filled by the element's constructor)
 *      +0x2f0 + 4 i  its colour (white / cccccc; RED cc0000 / 880000 when 0x77b790 says 'low on ammo')
 *      +0x2f8 + i    picture alpha (0xff in hand, 0x40 not), +0x2fa + i the count's alpha; 0 = no such gun
 *      +0x150c + 4 i the number it shows = rounds + reserve of gun i (-1 = none shown)
 *      +0x304        desc of the MAGAZINE TICKS: count = the magazine size when it is 1 .. 30, 2 (a bar and its rest)
 *                    when it is over 30, 0 when under 1; 30 records of 0x74 bytes at +0x310, one quad a round,
 *                    drawn in ONE DrawChunk with picture 109 (0x5ec8d8); record k's four colours at +0x374 + 0x74 k
 *                    (alpha 0x27 = an empty round)
 *      +0x1134       a bar record 0x5c5670 writes every tick whatever the size: its right edge (+0x44) = rounds /
 *                    size x 179 x T[+0x14]; the full bar's (+0x10b4, +0x44) = 179 x T[+0x14]. Neither is drawn by
 *                    the Render (no reference in 0x5ec380) - but their quotient is rounds / size for EVERY gun, with
 *                    no call into the game. THAT is the ring.
 *      +0x1228       1 = slot 0 has a gun object (the ticks are drawn)
 *    NOT IN THE PANEL: a gun's name, a separate reserve number, grenades. The name here is this file's own table by
 *    picture index (the exe names the pictures: 'UI_Weapon_01#Rifle_AK47'); display wording is OURS.
 *
 * 2. PICTURES OF TWO KINDS (EXE 0x5e3810: the OSD makes each picture's sprite chunk with the type its table row
 *    0xcee058 gives, 5 when it has no row)
 *    type 5 (40-byte record): 107 / 108 panel plate, 170 / 171, 181 - and the extras 111 .. 118 (no row) = klhud.c's
 *      klu_pic / klu_addpic. The disc (114), the dabs (113) and the divider (112) go that way.
 *    type 6 (0x74-byte record): the WEAPON PICTURES 58 .. 106 (and 109, the tick). klu_pic does not draw them (its
 *      handle table keeps type 5 only). Record (EXE 0x4bde70, 0x7c6bf0, 0x5ec608 ..): +0 vec3 offset, +0xc 0,
 *      +0x10 .. +0x1c four 1.0, +0x20 .. +0x28 0, +0x2c four corners (vec3 each) = (-0.5, -0.5) (0.5, -0.5)
 *      (0.5, 0.5) (-0.5, 0.5): THE PLACE IS THE SPRITE'S MIDDLE; +0x5c width = pixels x T[+0xc], +0x60 height =
 *      pixels x T[+0x10] (0x5ec615 .. 0x5ec653: the picture table's own width and height go in that way);
 *      +0x64 .. +0x70 four ARGB, one a corner. klwd_pic6 below draws with a copy of the element's own record of
 *      that slot (taken in the tick by checked reads), our size and colour.
 *
 * 3. THE STOCK PANEL IS NOT DRAWN - BY A PRIVATE VTABLE, NOT BY THE HIDE BYTE
 *    The task named the hide byte elem+0x25. The game writes that same byte from TWO of its own hide groups
 *    (0x75f780 at 0x75f78a and 0x5e6060 at 0x5e6097, thirteen call sites together): a hook that also writes it can no
 *    longer tell what the game wants, which is klhud.c's review point M1 again, with two groups to guess from.
 *    So this part never writes +0x25. The element gets a private copy of its 11-slot vtable (as klhud.c gives the
 *    clock; one heap dword, no code byte) whose slot 2 skips the stock Render 0x5ec380 while the dial is on and draws
 *    the two gun pictures instead. The game's own +0x24 / +0x25 / 'HUD off' tests (0x8bf300) stay in front of that
 *    slot: when the game hides its panel our pictures are not drawn in that very frame, and the tick - which reads
 *    +0x24 / +0x25 as the GAME left them - takes the disc, ring and texts off within 100 ms. Standing down = the
 *    wrapper passes every call through to the stock Render; nothing has to be put back.
 *
 * 4. WHEN THE DIAL IS NOT DRAWN AND THE STOCK PANEL IS (klwd_r.why, logged when it changes)
 *    Weapon=0; the level has no picture 113 / 114 (tools\kl_hud.py --look deadmen); the element is not a
 *    ZWeaponDisplay or its slot 2 is not 0x5ec380; any checked read fails; the picture index of gun 0 is out of
 *    range, has no type-6 chunk, or the element's own desc / record of that slot does not look as the Init left it;
 *    the player's class does not answer 'current action' by the two routines this build knows; the draw context is
 *    not a ZDrawBufferSimple (that frame); and whenever klhud.c itself does not draw (state, stock level, fault).
 *
 * 5. WHAT THE SKIPPED RENDER ALSO DID, AND WHAT THE DIAL DOES FOR IT (review round, re\hud_weapon.md 9)
 *    - the magazine ticks go RED when 0x54ee60 says the MAGAZINE is low (size > 3 and rounds / size < 0.33): the bar
 *      colour elem+0x122c is then [0xbbe4d0] (EXE 0x5c56dc). The dial's ring and first count turn coral on that, and
 *      on the picture's own red (0x77b790: rounds + reserve under one magazine), which also colours the picture.
 *    - the pick-up arrow, picture 110, when byte elem+0x12d4 is not 0 (EXE 0x43cb30: -1 = the gun offered is gun 0's
 *      or neither's, 1 = it is gun 1's; drawn 24 px above / below, 0x5ec99f). The dial draws it LEFT OF THE DISC at
 *      the row it means (OUR place: KLWD_ARROW_*).
 *    - it draws NO gun, number or tick while the player's current action is number 0x21 with [action+0xd4] == 3
 *      (EXE 0x5ec3a2: player vt+0x388 = 0x76ea90 = [[player+0x19c]+4]->vt[+4](), vt+0x38c = 0x7d7fb0 = that
 *      object). Action 0x21 = ZFFActionCloseCombat (vtable 0xbb4e98, its slot 1 = 0x962850 = return [this+4]); the
 *      one writer of +0xd4 = 3 is 0x76eab0, the routine that takes hold of the target. GUESS: the human-shield
 *      hold. It is NOT the knock-down (that is a movement state, re\player_down.md). The dial follows by checked
 *      reads, no call: the disc stays, empty, as the stock plate does.
 *    - every picture size is multiplied by the float [0xcee050] (1.0 in the file, two writers in .text): read each
 *      tick and applied to the gun pictures and the arrow.
 *
 * KLHook.ini ([HUD], with Enable=1)
 *   Weapon=0          1 = the weapon dial; the stock ammo panel is not drawn while it stands
 *   WeaponX=-1 WeaponY=-1   the dial's MIDDLE in virtual 1280 x 720 pixels; -1 = from the inset (1145.5, 598 at 0.05)
 *   WeaponSmall=0.8   the size of the other gun's count against the first (the stock panel's own 0.8, EXE 0x78fb23);
 *                     0 = no size call at all
 *   WeaponOther=0     the other gun's number: 0 = all its ammo (what the stock panel shows), 1 = its magazine
 *   (Log=2 prints the raw values once a second: 'hud: weapon: raw ...')
 */
#ifndef KLHUD_WEAPON_C
#define KLHUD_WEAPON_C

#define KLWD_VT          0x00bbe8c0u           /* ZWeaponDisplay (re\hud.md 2.2) */
#define KLWD_RENDER      0x005ec380u           /* its slot 2 */
#define KLWD_O_ELEM      0x1110                /* osd: ZWeaponDisplay * */
#define KLWD_KEY         0xbeebbeebu           /* the xor of a gun's two counters (0x511f56, 0x8b8179) */
#define KLWD_MAG_GET     0x00511f50u           /* weapon vtable +0x2fc: return [this+0xdc] ^ KEY */
#define KLWD_ITEMPIC     0x0154db68u           /* dword[64]: item id -> HUD picture index (0x88bd1d) */
#define KLWD_NITEM       64                    /* eFF2ItemCount (the item manager's own loops stop at 0x40: 0x7597e3) */
#define KLWD_RED_A       0x00bbe4d0u           /* .rdata ARGB: low on ammo, gun in hand (0xffcc0000) */
#define KLWD_RED_B       0x00bbe4d4u           /* .rdata ARGB: low on ammo, the other colour (0xff880000) */
#define KLWD_TEXT_SCALE  0x0045d6e0u           /* ZCHAROBJ vtable +0x21c (&{sx, sy}, 0): what the stock panel sets to 0.8 for gun 1 */
#define KLWD_PICTYPE     6                     /* [chunk+0xc] of a weapon picture: the 0x74-byte record (0x842e3d) */
#define KLWD_PICSCALE    0x00cee050u           /* float, 1.0 in the file: every picture size of the Render is multiplied by it (0x5ec624 ..) */
#define KLWD_PL_ACTID    0x0076ea90u           /* player vtable +0x388: [[this+0x19c]+4]->vt[+4](), 0 without an action */
#define KLWD_PL_ACT      0x007d7fb0u           /* player vtable +0x38c: [[this+0x19c]+4] */
#define KLWD_ACT_GETID   0x00962850u           /* an action's slot 1 when it is 'return [this+4]' */
#define KLWD_CC_VT       0x00bb4e98u           /* ZFFActionCloseCombat = action number 0x21 */
#define KLWD_ARROW_PIC   110                   /* the pick-up arrow (table handle at +0x528, 0x5eca1e) */

/* the element's fields (section 1) */
#define KLWD_E_TABLE     0x08                  /* -> the OSD's picture table, 12 bytes a picture: handle, width, height */
#define KLWD_E_XFORM     0x0c                  /* -> the screen transform T */
#define KLWD_E_PLAYER    0x10
#define KLWD_E_PICDESC   0xd8                  /* + 0x84 i: desc {1, 0, -> record} of gun i's picture, the record right behind it */
#define KLWD_E_PICREC    0xe4                  /* + 0x84 i */
#define KLWD_E_PIC       0x2e8                 /* + 4 i */
#define KLWD_E_NTICK     0x304
#define KLWD_E_BARFULL   0x10b4                /* record; its right edge at +0x44 */
#define KLWD_E_BARFILL   0x1134
#define KLWD_E_HASGUN    0x1228                /* four bytes: gun 0 has an object, rounds != 0, size != 0, the plate is drawn */
#define KLWD_E_BARCOL    0x122c                /* ARGB of the magazine ticks: [0xbbe4d0] (red) when the MAGAZINE is low (0x5c56dc) */
#define KLWD_E_ARROWCOL  0x129c                /* the arrow's record (desc +0x126c, record +0x1278, 40 bytes): its ARGB at +0x24 */
#define KLWD_E_ARROW     0x12d4                /* signed byte: 0 no arrow, -1 at gun 0's row, 1 at gun 1's (0x43cb30) */
#define KLWD_E_TOTAL     0x150c                /* + 4 i */
/* the player's */
#define KLWD_P_HAND      0x920                 /* item id in the hand, 0 = none */
#define KLWD_P_SEL       0x924                 /* item id selected */
#define KLWD_P_NOSECOND  0xa54                 /* byte, bit 1: the Render skips gun 1 (0x5ec3e0) */
#define KLWD_P_INV       0xcec
#define KLWD_P_ACTION    0x19c                 /* -> holder, the current action object at holder+4 */

/* THE LAYOUT, virtual 1280 x 720 pixels, all relative to the dial's middle (cx, cy). re\hud_layout.md's numbers were
   written for the draft's own margin (middle 1177, 598); here the middle follows the game's inset. NOTHING OF IT HAS
   BEEN SEEN: change the numbers here, not in the code. */
#define KLWD_D           141.0f                /* the disc's diameter */
#define KLWD_FROM_BOTTOM 86.0f                 /* the middle stands this far above the inset line (720 - 36 - 86 = 598) */
#define KLWD_RING_R      62.0f
#define KLWD_RING_N      64                    /* run V2: 32 read as beads; V3: 48 still did (dab ink 0.59 x 0.74 of the picture) */
#define KLWD_DAB_W       12.0f
#define KLWD_DAB_H       10.0f
#define KLWD_ACT_NUM_DX  (-7.0f)               /* the first gun's count: RIGHT-aligned at cx - 7, top at cy - 32 */
#define KLWD_ACT_NUM_DY  (-32.0f)
#define KLWD_ACT_PIC_DX  28.0f                 /* its picture's MIDDLE */
#define KLWD_ACT_PIC_DY  (-26.0f)
#define KLWD_ACT_PIC     64.0f                 /* its picture's size (the texture is 128 x 128) */
#define KLWD_CUT_W       87.0f                 /* the divider */
#define KLWD_CUT_H       2.0f
#define KLWD_CUT_DY      2.0f
#define KLWD_OTH_NUM_DX  (-5.0f)               /* the other gun's count: right-aligned at cx - 5, top at cy + 20 */
#define KLWD_OTH_NUM_DY  20.0f
#define KLWD_OTH_PIC_DX  21.0f
#define KLWD_OTH_PIC_DY  24.0f
#define KLWD_OTH_PIC     36.0f
#define KLWD_LABEL_DX    0.0f                  /* the label: CENTRED under the disc (style 0x44 = KLU_STYLE_CENTRE, seen live in run H1_DM03_hud; set by the WIRING in klu_layout) */
#define KLWD_LABEL_DY    88.0f                 /* its top */
#define KLWD_SEP         " . "                 /* between the name and the reserve (the draft's middle dot is not in the baked fonts for sure) */
#define KLWD_ARROW_DX    (-86.0f)              /* the pick-up arrow's MIDDLE: left of the disc (OUR place, a GUESS at the look), at the row it means */
#define KLWD_ARROW_ACT_DY (-26.0f)
#define KLWD_ARROW_OTH_DY 24.0f
#define KLWD_ARROW_SIZE  20.0f                 /* when the picture table's own size of picture 110 does not read as 4 .. 64 */

#define KLWD_C_BACK      0x9c080809u           /* the disc (re\hud_layout.md 'back') */
#define KLWD_C_DIM       0xff6f6c66u           /* the other gun */
#define KLWD_C_HOLSTER   0xffb9b5adu           /* the first gun while it is not in the hand */
#define KLWD_C_CUT       0x49f3f0eau           /* chalk, alpha 73 */

#define KLWD_T_ACT       (KLU_T_WEAP + 0)      /* klhud.c's text objects this part uses (WIRING: KLU_T_WEAP, KLU_NWEAP = 3) */
#define KLWD_T_OTH       (KLU_T_WEAP + 1)
#define KLWD_T_LABEL     (KLU_T_WEAP + 2)

struct klwd_gun { int item, pic, total, rounds, reserve; DWORD weapon, colour, handle; BYTE alpha, talpha; int shown; };
struct klwd_raw {
    DWORD el, player, pvt, inv, hand, sel; BYTE en, hid, hasgun, f1229, f122a, f122b, nosecond; int nticks, msize;
    int grab;                                  /* 1 = the one action state in which the stock Render draws no gun (section 5), -1 = not readable */
    int arrow, arrow_w, arrow_h; DWORD barcol, arrowcol, action; float scale;
    float bar, barfull, frac; struct klwd_gun g[2];
};
struct klwd_q { DWORD handle; float x, y, w, h, scale; DWORD argb; int layer; float rec[0x74 / 4]; };

#define KLWD_NQ 3                              /* two guns and the arrow */
static struct { float x, y, small_size; int other; } klwd;
static struct {
    DWORD elem; int wrapped, ok, scaled, told_nocount, told_arrow; const char *why, *said_why;
    struct klwd_q q[KLWD_NQ]; int nq;
} klwd_r;
static volatile LONG klwd_draw_on;             /* read by the render slot: 1 = the dial stands, the stock Render is skipped */
static volatile LONG klwd_n_skip, klwd_n_pass, klwd_n_pic, klwd_n_busy;
static DWORD klwd_evt[KLU_ELEM_NSLOT + 1];     /* [0] RTTI locator, [1..] the slots */
static int klwd_evt_ready;

/* the gun's name by HUD picture index 58 .. 104. The exe's own names of these pictures (table 0xcee058, read in the
   file: 'tex:UserInterface/WeaponsPics/UI_Weapon_01#<name>') are in the comments; the wording shown is OURS, in
   capitals, letters / digits / '-' only. A gun whose LOOK tools\kl_map_guns.py baked over (Zastava as MP5 ...) still
   reads its Dog Days name: not handled. */
static const char *const klwd_names[47] = {
    "SW MP45",        /* 58 HG_SW_MP45 */            "TAURUS JUDGE",   /* 59 HG_TaurusJudge */
    "POLICE REVOLVER",/* 60 HG_Revolver_Police */    "SIG 226",        /* 61 HG_SigSauer226 */
    "COLT COBRA",     /* 62 HG_ColtCobra */          "M-77B",          /* 63 HG_M-77B */
    "M-77B SIL",      /* 64 HG_M-77B_Silenced */     "M9 BERETTA",     /* 65 HG_M9Beretta */
    "M9 BERETTA SIL", /* 66 HG_M9Beretta_Silenced */ "DESERT EAGLE",   /* 67 HG_DesertEagle */
    "TT-33",          /* 68 HG_TT-33 */              "M-77B",          /* 69 HG_M-77B_Human_Shield */
    "M9 BERETTA",     /* 70 HG_M9Beretta_Human_Shield */ "HAWK BULLPUP", /* 71 Shotgun_Hawk_Bullpup */
    "HAWK POLICE",    /* 72 Shotgun_Hawk_Police */   "HAWK SAWN-OFF",  /* 73 Shotgun_Hawk_SawnOff */
    "TPS",            /* 74 Shotgun_TPS */           "REMINGTON 870",  /* 75 Shotgun_Remington_870 */
    "SPAS-12",        /* 76 Shotgun_Spas_12 */       "SA61",           /* 77 SMG_SA61 */
    "UMP SBR",        /* 78 SMG_UMP_SBR */           "UMP",            /* 79 SMG_UMP */
    "UMP SIL",        /* 80 SMG_UMP_Silenced */      "SP89 SIL",       /* 81 SMG_HK_SP89_Silenced */
    "MAC-10",         /* 82 SMG_MAC_10 */            "MAC-10 SIL",     /* 83 SMG_MAC_10_Silenced */
    "MPI 69",         /* 84 SMG_MPI69 */             "TYPE 79",        /* 85 SMG_Type79 */
    "TYPE 05",        /* 86 SMG_Type05 */            "TYPE 05 SIL",    /* 87 SMG_Type05_Silenced */
    "ZASTAVA M85",    /* 88 Rifle_zastavam85 */      "FN SCAR",        /* 89 Rifle_FN_SCAR */
    "AK-47",          /* 90 Rifle_AK47 */            "AK-74",          /* 91 Rifle_AK74 */
    "TYPE 81",        /* 92 Rifle_Type81 */          "TYPE 88",        /* 93 Rifle_Type88 */
    "TYPE 88 SCOPE",  /* 94 Rifle_Type88_Scoped */   "TYPE 95",        /* 95 Rifle_Type95 */
    "TYPE 95 SCOPE",  /* 96 Rifle_Type95_Scoped */   "MINIMI",         /* 97 MG_MiniMi_SPW */
    "REM 700",        /* 98 Sn_Rem700 */             "RPG-7",          /* 99 RPG_7V */
    "HK69",           /* 100 Launcher_HK69A1 */      "SMOKE",          /* 101 Grenade_Smoke */
    "TEAR GAS",       /* 102 Grenade_TearGas */      "GRENADE",        /* 103 Grenade */
    "INCENDIARY"      /* 104 Grenade_Incendiary */
};

static const char *klwd_name(int pic)
{
    return pic >= 58 && pic <= 104 ? klwd_names[pic - 58] : "";
}

/* ---------------------------------------------------------------- the render slot (whichever thread renders) */

/* one weapon picture: a type-6 sprite with ITS MIDDLE at (x, y) (section 2). el = the ZWeaponDisplay the game is
   rendering in this very call, so its transform pointer is read directly; the record is our copy (klwd_r.q, written
   by the tick under klu_cs, which this caller holds); DrawChunk copies it before it returns (0x842e3d -> 0x842df1) */
static void klwd_pic6(void *el, void *ctx, const struct klwd_q *q)
{
    DWORD T = *(const DWORD *)((DWORD_PTR)el + KLWD_E_XFORM), desc[3]; const float *t;
    float rec[0x74 / 4], in[2], out[3] = { 0, 0, 0 }, xform[9] = { 0, 0, 1.0f, 0, 1.0f, 0, 1.0f, 0, 0 }; int k;
    if (!T || !q->handle) return;
    t = (const float *)(DWORD_PTR)(T + 0xc);
    memcpy(rec, q->rec, sizeof rec);
    rec[0x5c / 4] = q->w * q->scale * t[0];                          /* EXE 0x5ec615: width x [0xcee050] x T[+0xc]; the global was read by the tick */
    rec[0x60 / 4] = q->h * q->scale * t[1];                          /* EXE 0x5ec643: height x [0xcee050] x T[+0x10] */
    for (k = 0; k < 4; k++) memcpy(&rec[0x64 / 4 + k], &q->argb, 4); /* EXE 0x5ec6f7 ..: the four corners' colour */
    desc[0] = 1; desc[1] = 0; desc[2] = (DWORD)(DWORD_PTR)rec;
    in[0] = q->x; in[1] = q->y;
    ((void (__fastcall *)(void *, void *, float *, float *))(DWORD_PTR)KLH_VA(KLU_PLACE))((void *)(DWORD_PTR)T, 0, out, in);
    ((DWORD (__fastcall *)(void *, void *, DWORD, DWORD *, float *, float *, DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLU_DRAWCHUNK))(ctx, 0, q->handle, desc, xform, out, (DWORD)q->layer, 1, 0);
    InterlockedIncrement(&klwd_n_pic);
}

/* slot 2 (Render(ctx, cam), thiscall ret 8) of the private vtable of ZWeaponDisplay: the game calls it only when it
   would draw the stock panel (enabled, not hidden, HUD on: 0x8bf300). While the dial stands the stock Render is not
   called and the two gun pictures are drawn here; else the stock Render, untouched. */
static char __fastcall klwd_render_elem(void *el, void *edx, void *ctx, void *cam)
{
    int i; (void)edx;
    if (!klwd_draw_on || (DWORD)(DWORD_PTR)el != klwd_r.elem) {
        InterlockedIncrement(&klwd_n_pass);
        return ((klu_render_t)(DWORD_PTR)KLH_VA(KLWD_RENDER))(el, 0, ctx, cam);
    }
    if (!ctx || *(const DWORD *)ctx != KLU_CTX_VT) {                 /* a draw context this part does not know: the stock panel, whole, for this frame */
        InterlockedIncrement(&klwd_n_pass);
        return ((klu_render_t)(DWORD_PTR)KLH_VA(KLWD_RENDER))(el, 0, ctx, cam);
    }
    InterlockedIncrement(&klwd_n_skip);
    if (!TryEnterCriticalSection(&klu_cs)) { InterlockedIncrement(&klwd_n_busy); return 0; }   /* the tick is writing the queue: one frame without the gun pictures */
    if (klwd_draw_on && klu_draw_on && (DWORD)(DWORD_PTR)el == klwd_r.elem)
        for (i = 0; i < klwd_r.nq; i++) klwd_pic6(el, ctx, &klwd_r.q[i]);
    LeaveCriticalSection(&klu_cs);
    return 0;
}

/* ---------------------------------------------------------------- the private vtable (main thread) */

static int klwd_vtable_tick(DWORD osd)
{   /* -> 1 while the weapon element's first dword is ours (installed here when it shows the stock one) */
    static const BYTE render_code[8] = { 0x83, 0xec, 0x5c, 0x56, 0x8b, 0xf1, 0x80, 0x7e };   /* 0x5ec380 sub esp,0x5c ; push esi ; mov esi,ecx ; cmp byte [esi+0x24],0 */
    static LONG told; DWORD el, vt, cur = 0;
    klwd_r.wrapped = 0;
    if (!(el = klh_rd32(osd + KLWD_O_ELEM)) || !klh_rd(el, &cur, 4)) return 0;
    if (!klwd_evt_ready) {
        if (!klh_rd((DWORD_PTR)KLH_VA(KLWD_VT - 4), klwd_evt, sizeof klwd_evt)) return 0;
        if (klwd_evt[1 + 2] != KLWD_RENDER || !klu_same_code(KLWD_RENDER, render_code, sizeof render_code)) {
            if (!InterlockedExchange(&told, 1)) klog("hud: weapon: slot 2 of ZWeaponDisplay is %08lx, not %08lx (or its code is not the one this build knows): the dial is off, the stock panel stays", klwd_evt[1 + 2], KLWD_RENDER);
            return 0;
        }
        klwd_evt[1 + 2] = (DWORD)(DWORD_PTR)klwd_render_elem;
        klwd_evt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klwd_evt[1];
    if (cur == vt) { klwd_r.elem = el; klwd_r.wrapped = 1; return 1; }
    if (cur != KLWD_VT) {
        if (!InterlockedExchange(&told, 1)) klog("hud: weapon: the element at osd+0x1110 = %08lx has vtable %08lx, not ZWeaponDisplay's: the dial is off, the stock panel stays", el, cur);
        return 0;
    }
    klwd_r.elem = el;                          /* before the dword goes in: the wrapper compares with it */
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the weapon element's vtable (private copy, slot 2 wrapped)")) { klwd_r.elem = 0; return 0; }
    klwd_r.wrapped = 1;
    if (klu.log) klog("hud: weapon: element %08lx (ZWeaponDisplay) now renders through the private vtable (slot 2 -> klwd_render_elem: the stock 0x5ec380 unless the dial stands)", el);
    return 1;
}

/* ---------------------------------------------------------------- the reads (main thread, every one checked) */

static DWORD klwd_weapon(DWORD inv, int item)
{   /* 0x417bc0 -> 0x5aa000(inv + 4, item): the inventory's entry of this item, its gun object at +8 */
    BYTE mode = 0; DWORD arr = 0, cnt = 0, e[4]; DWORD i;
    if (!inv || item <= 0 || item >= KLWD_NITEM || !klh_rd(inv + 4, &mode, 1) || !klh_rd(inv + 8, &arr, 4) || !klh_rd(inv + 0xc, &cnt, 4) || !arr) return 0;
    if (!mode) return klh_rd(arr + 16 * (DWORD)item, e, sizeof e) ? e[2] : 0;     /* indexed by the item id (0x5aa03d); what comes back is used only when its vtable answers as a gun (klwd_counts) */
    if (cnt > 256) return 0;
    for (i = 0; i < cnt; i++) if (klh_rd(arr + 16 * i, e, sizeof e) && e[0] == (DWORD)item) return e[2];
    return 0;
}

static int klwd_other_item(DWORD inv, int item0)
{   /* 0x49b2f0(inv, item0, 4): the first entry with a gun object whose info says kind 1 or 2 and another item id */
    DWORD arr = 0, cnt = 0, e[4], info[3], i;
    if (!inv || !klh_rd(inv + 8, &arr, 4) || !klh_rd(inv + 0xc, &cnt, 4) || !arr || cnt > 256) return 0;
    for (i = 0; i < cnt; i++) {
        if (!klh_rd(arr + 16 * i, e, sizeof e) || !e[2] || !e[3] || !klh_rd(e[3], info, sizeof info)) continue;
        if ((info[2] == 1 || info[2] == 2) && info[1] != (DWORD)item0 && info[1] < KLWD_NITEM) return (int)info[1];
    }
    return 0;
}

static int klwd_item_of_pic(int pic)
{   /* the item whose HUD picture this is, when exactly one item has it (0x154db68) */
    DWORD tab[KLWD_NITEM]; int i, found = 0;
    if (pic <= 0 || !klh_rd((DWORD_PTR)KLH_VA(KLWD_ITEMPIC), tab, sizeof tab)) return 0;
    for (i = 1; i < KLWD_NITEM; i++) if (tab[i] == (DWORD)pic) { if (found) return 0; found = i; }
    return found;
}

static void klwd_counts(struct klwd_gun *g)
{   /* the gun object's two counters, only when its class answers 'rounds in the magazine' with 0x511f50 */
    DWORD vt = 0, raw[2];
    g->rounds = g->reserve = -1;
    if (!g->weapon || !klh_rd(g->weapon, &vt, 4) || !klu_rdata_ptr(vt) || klh_rd32((DWORD_PTR)KLH_VA(vt + 0x2fc)) != KLWD_MAG_GET) return;
    if (!klh_rd(g->weapon + 0xdc, raw, sizeof raw)) return;
    raw[0] ^= KLWD_KEY; raw[1] ^= KLWD_KEY;
    if (raw[0] <= 9999) g->rounds = (int)raw[0];
    if (raw[1] <= 99999) g->reserve = (int)raw[1];
}

static DWORD klwd_handle(DWORD el, int pic)
{   /* the sprite handle of HUD picture `pic` when its chunk is the 0x74-byte-record kind */
    DWORD tbl = klh_rd32(el + KLWD_E_TABLE), h = 0, chunk;
    if (!tbl || pic <= 0 || pic >= 200 || !klh_rd(tbl + 12 * (DWORD)pic, &h, 4) || !h) return 0;
    chunk = (h & 0x80000000u) ? (h & 0x7fffffffu) : klh_rd32((DWORD_PTR)KLH_VA(KLU_CHUNKTAB) + 4 * h);      /* 0x842d22 .. 0x842d2e */
    return chunk && klh_rd32(chunk + 0xc) == KLWD_PICTYPE ? h : 0;
}

static int klwd_grab(DWORD player, DWORD pvt, DWORD *action)
{   /* section 5: what 0x5ec3a2 .. 0x5ec3c8 asks, by checked reads and no call. -> 1 = action number 0x21 with
       [action+0xd4] == 3 (the stock Render draws no gun), 0 = not, -1 = the player's class answers another way */
    DWORD holder, act, avt = 0, id = 0, st = 0;
    *action = 0;
    if (klh_rd32((DWORD_PTR)KLH_VA(pvt + 0x388)) != KLWD_PL_ACTID || klh_rd32((DWORD_PTR)KLH_VA(pvt + 0x38c)) != KLWD_PL_ACT) return -1;
    if (!(holder = klh_rd32(player + KLWD_P_ACTION)) || !(act = klh_rd32(holder + 4))) return 0;      /* 0x76ea96 / 0x76ea9d: no action = number 0 */
    *action = act;
    if (!klh_rd(act, &avt, 4) || !klu_rdata_ptr(avt)) return 0;
    /* the number: only when the class's slot 1 is the plain 'return [this+4]' (ZFFActionCloseCombat's is); a class with
       a routine of its own there is not close combat (0x839c28 makes vtable 0xbb4e98 for number 0x21) */
    if (avt != KLWD_CC_VT && klh_rd32((DWORD_PTR)KLH_VA(avt + 4)) != KLWD_ACT_GETID) return 0;
    if (!klh_rd(act + 4, &id, 4) || !klh_rd(act + 0xd4, &st, 4)) return 0;
    return id == 0x21 && st == 3;
}

/* -> 0 with klwd_r.why set: something this part needs did not read as the code says */
static int klwd_read(struct klwd_raw *r)
{
    DWORD el = klwd_r.elem, blk[5], tot[2], hs[2], cur = 0, tbl, wh[2]; BYTE b[2], f[4], a54 = 0, ar = 0; int i;
    memset(r, 0, sizeof *r);
    r->el = el;
    if (!el || !klh_rd(el, &cur, 4) || (cur != KLWD_VT && cur != (DWORD)(DWORD_PTR)&klwd_evt[1])) { klwd_r.why = "the element no longer has ZWeaponDisplay's vtable"; return 0; }
    if (!klh_rd(el + KLU_E_ENABLED, b, 2) || !klh_rd(el + KLWD_E_PIC, blk, sizeof blk) || !klh_rd(el + KLWD_E_TOTAL, tot, sizeof tot) ||
        !klh_rd(el + KLWD_E_NTICK, &r->nticks, 4) || !klh_rd(el + KLWD_E_HASGUN, f, 4) ||
        !klh_rd(el + KLWD_E_BARCOL, &r->barcol, 4) || !klh_rd(el + KLWD_E_ARROW, &ar, 1) || !klh_rd(el + KLWD_E_ARROWCOL, &r->arrowcol, 4) ||
        !klh_rd(el + KLWD_E_BARFILL + 0x44, &r->bar, 4) || !klh_rd(el + KLWD_E_BARFULL + 0x44, &r->barfull, 4)) { klwd_r.why = "a field of the element did not read"; return 0; }
    r->en = b[0]; r->hid = b[1]; r->hasgun = f[0]; r->f1229 = f[1]; r->f122a = f[2]; r->f122b = f[3];
    r->arrow = (signed char)ar;
    r->scale = 1.0f;                                              /* the Render's global size factor (0x5ec624): 1.0 unless the game changed it */
    if (!klh_rd((DWORD_PTR)KLH_VA(KLWD_PICSCALE), &r->scale, 4) || !(r->scale > 0.05f && r->scale < 8.0f)) r->scale = 1.0f;
    r->arrow_w = r->arrow_h = 0;                                  /* the picture table's own size of the arrow (0x5ec9df, 0x5ec9fd) */
    if ((tbl = klh_rd32(el + KLWD_E_TABLE)) != 0 && klh_rd(tbl + 12 * KLWD_ARROW_PIC + 4, wh, sizeof wh) && wh[0] >= 4 && wh[0] <= 64 && wh[1] >= 4 && wh[1] <= 64) { r->arrow_w = (int)wh[0]; r->arrow_h = (int)wh[1]; }
    if (!(r->player = klh_rd32(el + KLWD_E_PLAYER)) || !klh_rd(r->player, &r->pvt, 4) || !klu_rdata_ptr(r->pvt)) { klwd_r.why = "the element has no player object"; return 0; }
    if ((r->grab = klwd_grab(r->player, r->pvt, &r->action)) < 0) { klwd_r.why = "the player's vtable +0x388 / +0x38c are not 0x76ea90 / 0x7d7fb0: the state in which the game draws no gun cannot be followed"; return 0; }
    if (!klh_rd(r->player + KLWD_P_HAND, hs, sizeof hs) || !klh_rd(r->player + KLWD_P_INV, &r->inv, 4) || !klh_rd(r->player + KLWD_P_NOSECOND, &a54, 1)) { klwd_r.why = "a field of the player did not read"; return 0; }
    r->hand = hs[0]; r->sel = hs[1]; r->nosecond = (a54 >> 1) & 1;
    for (i = 0; i < 2; i++) {
        struct klwd_gun *g = &r->g[i];
        g->pic = (int)blk[i]; g->colour = blk[2 + i];
        g->alpha = ((const BYTE *)&blk[4])[i]; g->talpha = ((const BYTE *)&blk[4])[2 + i];
        g->total = (int)tot[i];
        if (g->pic < 0 || g->pic >= 200) { klwd_r.why = "a picture index of the element is out of range"; return 0; }
        if (g->total < -1 || g->total > 199998) g->total = -1;
    }
    /* which items: the selected one (0x88bad2); when the game took a fall-back for it, the one whose picture stands */
    r->g[0].item = r->sel > 0 && r->sel < KLWD_NITEM ? (int)r->sel : klwd_item_of_pic(r->g[0].pic);
    r->g[1].item = r->g[0].item ? klwd_other_item(r->inv, r->g[0].item) : 0;
    {   /* an item is kept only when the picture the element shows for the slot is that item's (else the counters would be another gun's) */
        DWORD tab[KLWD_NITEM];
        if (klh_rd((DWORD_PTR)KLH_VA(KLWD_ITEMPIC), tab, sizeof tab))
            for (i = 0; i < 2; i++) if (r->g[i].item && tab[r->g[i].item] != (DWORD)r->g[i].pic) r->g[i].item = 0;
    }
    for (i = 0; i < 2; i++) {
        struct klwd_gun *g = &r->g[i];
        g->weapon = g->item ? klwd_weapon(r->inv, g->item) : 0;
        klwd_counts(g);
        g->shown = g->pic != 0 && g->alpha != 0;              /* the Render draws a picture when its index is not 0 (0x5ec7b2); alpha 0 = the Tick found no gun object */
    }
    if (r->nosecond) r->g[1].shown = 0;
    /* the magazine: rounds / size from the two bar records (section 1), the size from the tick count or from both */
    r->frac = -1.0f; r->msize = -1;
    if (r->hasgun && r->nticks > 0 && r->barfull > 0 && r->bar >= 0 && r->bar <= r->barfull * 1.001f) r->frac = r->bar / r->barfull;
    if (r->hasgun && r->nticks >= 1 && r->nticks <= 30 && r->nticks != 2) r->msize = r->nticks;
    else if (r->hasgun && r->nticks == 2) {                   /* a magazine of 2, or the bar of one over 30 */
        if (r->g[0].rounds > 2 && r->frac > 0.02f) r->msize = (int)((float)r->g[0].rounds / r->frac + 0.5f);
        else if (r->g[0].rounds >= 0 && r->g[0].rounds <= 2 && r->frac >= 0 && (r->frac == 0 || r->frac == 0.5f || r->frac == 1.0f)) r->msize = 2;
    }
    if (r->frac < 0 && r->msize > 0 && r->g[0].rounds >= 0) r->frac = (float)r->g[0].rounds / (float)r->msize;
    if (r->frac > 1.0f) r->frac = 1.0f;
    return 1;
}

/* ---------------------------------------------------------------- composing the dial (main thread, under klu_cs) */

static void klwd_text(int i, float x, float y, DWORD colour, const char *s)
{
    struct klu_text *t = &klu_r.t[i];
    t->x = x; t->y = y; t->want_colour = colour; t->on = 1; t->noshadow = 0;
    snprintf(t->want, sizeof t->want, "%s", s);
}

static int klwd_queue(DWORD el, int slot, int pic, float x, float y, float w, float h, float scale, DWORD argb)
{   /* one type-6 picture into the render slot's queue: the handle and a copy of the element's own record of gun
       `slot` (the centred unit quad). -> 0 = that picture cannot be drawn by this part */
    struct klwd_q *q; DWORD desc[3], rec = el + KLWD_E_PICREC + 0x84 * (DWORD)slot; float c[2];
    if (klwd_r.nq >= KLWD_NQ) return 0;
    q = &klwd_r.q[klwd_r.nq];
    if (!(q->handle = klwd_handle(el, pic))) return 0;
    if (!klh_rd(el + KLWD_E_PICDESC + 0x84 * (DWORD)slot, desc, sizeof desc) || desc[0] != 1 || desc[2] != rec || !klh_rd(rec, q->rec, sizeof q->rec)) return 0;
    c[0] = q->rec[0x2c / 4]; c[1] = q->rec[0x44 / 4];             /* the first corner's x and the third's: -0.5 and 0.5 as 0x7c6bf0 leaves them */
    if (c[0] != -0.5f || c[1] != 0.5f) return 0;                  /* another shape than the centred unit quad: not ours to scale */
    q->x = x; q->y = y; q->w = w; q->h = h; q->scale = scale; q->argb = argb; q->layer = klu.layer - 1;
    klwd_r.nq++;
    return 1;
}

static void klwd_text_setup(void)
{   /* once a level, after klhud.c made the three texts: the other gun's count gets the stock panel's own smaller
       size. EXE 0x78fb11 .. 0x78fbcb: the panel calls vtable +0x21c (&{s, s}, 0) on its four texts of a slot, s = 1.0
       for gun 0 and [0xcee050] x 0.8 for gun 1, and 0x4596a0 steps its padding zeros by 16 x that s (0x459808).
       ASSUMED from those two: +0x1c / +0x20 are the text's SIZE. */
    struct klu_text *t = &klu_r.t[KLWD_T_OTH]; float s[2]; DWORD vt = 0;
    if (!(klwd.small_size > 0) || klwd.small_size == 1.0f) { klwd_r.scaled = 1; return; }
    /* review M1: this runs before klu_apply's own check of the tick, so each object is checked here - still a
       ZCHAROBJ, else no call now and another try in a later tick (klwd_r.scaled stays 0) */
    if (!t->obj || !klh_rd(t->obj, &vt, 4) || vt != KLU_TEXT_VT) return;
    if (t->shadow && (!klh_rd(t->shadow, &vt, 4) || vt != KLU_TEXT_VT)) return;
    klwd_r.scaled = 1;
    if (klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + 0x21c)) != KLWD_TEXT_SCALE) { klog("hud: weapon: ZCHAROBJ vtable +0x21c is not 0x45d6e0: the other gun's count keeps the full size"); return; }
    s[0] = s[1] = klwd.small_size;
    ((void (__fastcall *)(void *, void *, float *, DWORD))(DWORD_PTR)KLH_VA(KLWD_TEXT_SCALE))((void *)(DWORD_PTR)t->obj, 0, s, 0);
    if (t->shadow) ((void (__fastcall *)(void *, void *, float *, DWORD))(DWORD_PTR)KLH_VA(KLWD_TEXT_SCALE))((void *)(DWORD_PTR)t->shadow, 0, s, 0);
    if (klu.log) klog("hud: weapon: the other gun's count set to size %.2f (ZCHAROBJ +0x21c, as the stock panel does for its second gun)", klwd.small_size);
}

/* called by klu_compose after klu_dials (WIRING): fills klhud.c's texts and picture queue and this part's own queue
   of the two gun pictures. klwd_r.ok = 1 = the dial is whole; 0 = nothing of it was queued and the stock panel stays */
static void klwd_compose(void)
{
    static DWORD said; DWORD now = GetTickCount(), red_a, red_b; struct klwd_raw r; struct klwd_gun *a = &r.g[0], *o = &r.g[1];
    float inset = 0.05f, cx, cy; char num[24], label[KLU_TEXTLEN]; int low = 0, lowclip = 0, warn, n0, k, m, demo = klu.grid == 2, npic0 = klu_r.npic;
    klwd_r.ok = 0; klwd_r.nq = 0; klwd_r.why = 0;
    if (!klu.weapon || !klu_r.osd || !klu_r.pic_done) return;       /* pic_done: klu_pic_prep runs after the first compose of a level */
    if (!klu_r.t[KLWD_T_ACT].obj || !klu_r.t[KLWD_T_OTH].obj || !klu_r.t[KLWD_T_LABEL].obj) klwd_r.why = "klhud.c made no text objects for the dial";
    else if (!klu_r.handle[113] || !klu_r.handle[114]) klwd_r.why = "the level has no picture 113 / 114 (tools/kl_hud.py --look deadmen)";
    else if (!klwd_vtable_tick(klu_r.osd)) klwd_r.why = "the weapon element is not wrapped";
    else if (klwd_read(&r)) {
        if (!klwd_r.scaled) klwd_text_setup();
        klh_rd((DWORD_PTR)KLH_VA(KLU_INSET), &inset, 4);
        if (!(inset >= 0 && inset < 0.25f)) inset = 0.05f;
        cx = klwd.x >= 0 ? klwd.x : 1280.0f - 1280.0f * inset - KLWD_D * 0.5f;
        cy = klwd.y >= 0 ? klwd.y : 720.0f - 720.0f * inset - KLWD_FROM_BOTTOM;
        if (klu.log >= 2 && now - said >= 1000) {
            said = now;
            klog("hud: weapon: raw: element %08lx enabled %d hidden %d; player %08lx (vtable %08lx) hand item %lu, selected item %lu, inventory %08lx, no-second bit %d; "
                 "gun 0: item %d picture %d '%s' colour %08lx alpha %02x/%02x shown number %d, object %08lx rounds %d reserve %d; "
                 "gun 1: item %d picture %d '%s' colour %08lx alpha %02x/%02x shown number %d, object %08lx rounds %d reserve %d; "
                 "ticks %d (flags %d %d %d, plate %d), bar %.5f of %.5f -> %.3f of the magazine, size %d, tick colour %08lx; "
                 "arrow %d (picture 110 is %d x %d, colour %08lx); action %08lx, close-combat hold %d; size factor %.3f%s",
                 r.el, r.en, r.hid, r.player, r.pvt, r.hand, r.sel, r.inv, r.nosecond,
                 a->item, a->pic, klwd_name(a->pic), a->colour, a->alpha, a->talpha, a->total, a->weapon, a->rounds, a->reserve,
                 o->item, o->pic, klwd_name(o->pic), o->colour, o->alpha, o->talpha, o->total, o->weapon, o->rounds, o->reserve,
                 r.nticks, r.hasgun, r.f1229, r.f122a, r.f122b, r.bar, r.barfull, r.frac, r.msize, r.barcol,
                 r.arrow, r.arrow_w, r.arrow_h, r.arrowcol, r.action, r.grab, r.scale, demo ? " (Grid=2: the sample values are shown, not these)" : "");
            klog("hud: weapon: render: %ld stock panel calls skipped, %ld passed to the stock Render, %ld gun pictures drawn, %ld lock busy; dial %s",
                 InterlockedExchange(&klwd_n_skip, 0), InterlockedExchange(&klwd_n_pass, 0), InterlockedExchange(&klwd_n_pic, 0), InterlockedExchange(&klwd_n_busy, 0), klwd_draw_on ? "on" : "off");
        }
        if (demo) {                               /* Grid=2: the draft's own numbers ('24', '9', 'AK-47 . 183', the ring 80 % full), whatever the round holds;
                                                     still only while the game shows its own panel */
            a->pic = 90; a->rounds = 24; a->reserve = 183; a->total = 207; a->shown = 1; a->alpha = 0xff; a->colour = 0xffffffffu;
            o->pic = 65; o->total = 9; o->rounds = 9; o->shown = 1; o->alpha = 0x40;
            r.frac = 0.8f; r.msize = 30; r.grab = 0; r.arrow = 0; r.hasgun = 1; r.f122b = 1; r.barcol = 0xffffffffu;
        }
        if (r.grab == 1) { a->shown = o->shown = 0; r.arrow = 0; }      /* section 5: the stock Render draws no gun, number, tick or arrow in this state (0x5ec3ca .. 0x5ec3d8) */
        if (!r.en || r.hid) klwd_r.why = "the game does not show its ammo panel now";       /* not a fault: said at Log=2 only */
        else {
            klwd_r.ok = 1;
            /* the stock panel's two warnings: the picture and number red = rounds + reserve under one magazine
               (0x77b790); the ticks red = the MAGAZINE under a third (0x54ee60, colour elem+0x122c) */
            red_a = klh_rd32((DWORD_PTR)KLH_VA(KLWD_RED_A)) & 0xffffff; red_b = klh_rd32((DWORD_PTR)KLH_VA(KLWD_RED_B)) & 0xffffff;
            low = a->shown && red_a && ((a->colour & 0xffffff) == red_a || (a->colour & 0xffffff) == red_b);
            lowclip = a->shown && r.hasgun && red_a && (r.barcol & 0xffffff) == red_a;
            if (a->shown && !klwd_queue(r.el, 0, a->pic, cx + KLWD_ACT_PIC_DX, cy + KLWD_ACT_PIC_DY, KLWD_ACT_PIC, KLWD_ACT_PIC, r.scale, low ? KLU_C_CORAL : a->alpha == 0xff ? KLU_C_CHALK : KLWD_C_HOLSTER)) {
                klwd_r.ok = 0; klwd_r.nq = 0; klwd_r.why = "the first gun's picture has no type-6 chunk, or the element's record of it is not the centred quad";
            }
        }
        warn = low || lowclip;
        /* nothing at all for a player without a gun and without the stock plate (byte +0x122b): the stock panel is empty
           then too. In the close-combat hold the plate flag stands, and so does the empty disc */
        if (klwd_r.ok && (a->shown || o->shown || r.f122b)) {
            klu_addpic(114, cx - KLWD_D * 0.5f, cy - KLWD_D * 0.5f, KLWD_D, KLWD_D, KLWD_C_BACK, klu.layer - 2);
            if (a->shown) {
                /* the ring: dabs 0 .. m - 1 from the top clockwise = what is LEFT; the gap is the last part (the
                   draft's weapon dial; klu_ring runs the other way). At least one dab while a round is in */
                m = r.frac > 0 ? (int)(r.frac * KLWD_RING_N + 0.5f) : 0;
                if (m > KLWD_RING_N) m = KLWD_RING_N;
                if (m < 1 && (a->rounds > 0 || r.frac > 0)) m = 1;
                for (k = 0; k < m; k++) {
                    float ang = 6.2831853f * (float)k / (float)KLWD_RING_N;
                    klu_addpic(113, cx + KLWD_RING_R * (float)sin(ang) - KLWD_DAB_W * 0.5f, cy - KLWD_RING_R * (float)cos(ang) - KLWD_DAB_H * 0.5f, KLWD_DAB_W, KLWD_DAB_H, warn ? KLU_C_CORAL : KLU_C_CHALK, klu.layer - 1);
                }
                n0 = a->rounds >= 0 ? a->rounds : a->total;
                if (a->rounds < 0 && !klwd_r.told_nocount) {       /* review S7: the big number means something else then - said once a level */
                    klwd_r.told_nocount = 1;
                    if (klu.log) klog("hud: weapon: gun 0 (item %d, picture %d, object %08lx): no counters read (the item did not match the picture, or the object is not of a class whose vtable +0x2fc is 0x511f50): the dial shows the panel's own number %d = rounds + reserve where the magazine count belongs, and no reserve",
                                      a->item, a->pic, a->weapon, a->total);
                }
                if (n0 >= 0) { snprintf(num, sizeof num, "%d", n0); klwd_text(KLWD_T_ACT, cx + KLWD_ACT_NUM_DX, cy + KLWD_ACT_NUM_DY, warn ? KLU_C_CORAL : a->alpha == 0xff ? KLU_C_CHALK : KLWD_C_HOLSTER, num); }
                /* the label: the name, and what the GAME counts outside the magazine = its shown number - the rounds
                   (review S1: 0x8b80e0 does not always answer with [weapon+0xe0]; for a gun with endless ammo it is
                   999 - rounds or 999, so a total of 999 or more = no number). The raw counter only when the game shows
                   no number at all (-1) */
                n0 = -1;
                if (a->rounds >= 0 && a->total >= 0) { if (a->total < 999 && a->total >= a->rounds) n0 = a->total - a->rounds; }
                else if (a->rounds >= 0 && a->reserve >= 0 && a->reserve + a->rounds < 999) n0 = a->reserve;
                if (n0 >= 0 && klwd_name(a->pic)[0]) snprintf(label, sizeof label, "%s" KLWD_SEP "%d", klwd_name(a->pic), n0);
                else if (n0 >= 0) snprintf(label, sizeof label, "%d", n0);
                else snprintf(label, sizeof label, "%s", klwd_name(a->pic));
                if (label[0]) klwd_text(KLWD_T_LABEL, cx + KLWD_LABEL_DX, cy + KLWD_LABEL_DY, KLU_C_CORAL, label);
            }
            if (o->shown) {
                klu_addpic(klu_r.handle[112] ? 112 : 181, cx - KLWD_CUT_W * 0.5f, cy + KLWD_CUT_DY - KLWD_CUT_H * 0.5f, KLWD_CUT_W, KLWD_CUT_H, KLWD_C_CUT, klu.layer - 1);
                klwd_queue(r.el, 1, o->pic, cx + KLWD_OTH_PIC_DX, cy + KLWD_OTH_PIC_DY, KLWD_OTH_PIC, KLWD_OTH_PIC, r.scale, KLWD_C_DIM);      /* without a type-6 chunk the other gun has its number only */
                n0 = klwd.other && o->rounds >= 0 ? o->rounds : o->total >= 0 ? o->total : o->rounds;
                if (n0 >= 0) { snprintf(num, sizeof num, "%d", n0); klwd_text(KLWD_T_OTH, cx + KLWD_OTH_NUM_DX, cy + KLWD_OTH_NUM_DY, KLWD_C_DIM, num); }
            }
            /* the pick-up arrow (review S3; section 5): the stock picture 110 in the element's own colour, at the row it
               means. Its chunk is type 5 or 6 by what the level made (the table says 6, the element feeds it a 40-byte
               record): whichever kind is there is drawn, else said once */
            if (r.arrow && (r.arrow > 0 ? o->shown : a->shown)) {
                float aw = (r.arrow_w ? (float)r.arrow_w : KLWD_ARROW_SIZE) * r.scale, ah = (r.arrow_h ? (float)r.arrow_h : KLWD_ARROW_SIZE) * r.scale;
                float ax = cx + KLWD_ARROW_DX, ay = cy + (r.arrow > 0 ? KLWD_ARROW_OTH_DY : KLWD_ARROW_ACT_DY);
                DWORD ac = (r.arrowcol >> 24) ? r.arrowcol : KLU_C_CHALK;
                if (klu_r.handle[KLWD_ARROW_PIC]) klu_addpic(KLWD_ARROW_PIC, ax - aw * 0.5f, ay - ah * 0.5f, aw, ah, ac, klu.layer - 1);
                else if (!klwd_queue(r.el, 0, KLWD_ARROW_PIC, ax, ay, aw / r.scale, ah / r.scale, r.scale, ac) && !klwd_r.told_arrow) {
                    klwd_r.told_arrow = 1;
                    if (klu.log) klog("hud: weapon: the pick-up arrow (picture 110) has neither a type-5 nor a type-6 chunk in this level: the dial shows no arrow");
                }
            }
        }
    }
    if (!klwd_r.ok) { klu_r.npic = npic0; klwd_r.nq = 0; }      /* nothing half-drawn: the stock panel is whole */
    if (klwd_r.why != klwd_r.said_why && klu.log) {
        /* 'the game does not show its ammo panel' is no fault and comes often: at Log=2 only, and then it does not
           count as said, so 'stands again' follows only a line that was written (review N6) */
        int quiet = klwd_r.why && !strcmp(klwd_r.why, "the game does not show its ammo panel now");
        if (!(quiet && klu.log < 2)) {
            if (klwd_r.why) klog("hud: weapon: no dial, the stock panel is left to the game: %s", klwd_r.why);
            else if (klwd_r.said_why) klog("hud: weapon: the dial stands again");
            klwd_r.said_why = klwd_r.why;
        }
    }
}

/* called by klu_tick right after it sets klu_draw_on, and by klu_stand_down with 0 (WIRING) */
static void klwd_show(int show)
{
    InterlockedExchange(&klwd_draw_on, show && klu.weapon && klwd_r.ok && klwd_r.wrapped && klwd_r.elem ? 1 : 0);
}

/* called by klu_reset before it clears its own state (WIRING): the level's objects are gone or about to be. The
   element keeps our vtable when it lives on; with klwd_r.elem 0 the wrapper passes every call to the stock Render */
static void klwd_reset(void)
{
    InterlockedExchange(&klwd_draw_on, 0);
    memset(&klwd_r, 0, sizeof klwd_r);
}

/* called by klu_init after it read Weapon (WIRING) */
static void klwd_init(void)
{
    char t[32];
    if (!klu.weapon) return;
    GetPrivateProfileStringA("HUD", "WeaponX", klu.draft ? "1177" : "-1", t, sizeof t, klh_ini); klwd.x = (float)atof(t);
    GetPrivateProfileStringA("HUD", "WeaponY", "-1", t, sizeof t, klh_ini); klwd.y = (float)atof(t);
    GetPrivateProfileStringA("HUD", "WeaponSmall", "0.8", t, sizeof t, klh_ini); klwd.small_size = (float)atof(t);
    klwd.other = GetPrivateProfileIntA("HUD", "WeaponOther", 0, klh_ini) != 0;
    if (!(klwd.x <= 1280)) klwd.x = -1; if (!(klwd.y <= 720)) klwd.y = -1;
    if (!(klwd.small_size >= 0 && klwd.small_size <= 2.0f)) klwd.small_size = 0.8f;
    klog("hud: weapon: on (the weapon dial; the stock ammo panel's Render is skipped while it stands); WeaponX=%.0f WeaponY=%.0f (-1 = from the inset) WeaponSmall=%.2f WeaponOther=%d; needs the level's pictures 113 / 114; NOT RUN IN THE GAME",
         klwd.x, klwd.y, klwd.small_size, klwd.other);
}

#endif /* KLHUD_WEAPON_C */
