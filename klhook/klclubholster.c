/* klclubholster.c - [ClubHolster] Last Call (DM05A) starts with the guns holstered; the crowd panics only after you draw
 * (2026-10-24, task "Last Call hook + data"). Included by klhook.c AFTER klclubcalm.c, klbot.c and klshoulder.c (uses klh_rd,
 * klh_rd32, klo_input, klb_read, klh_scene, klh_level_key, KLE_ENTS, kle_node, KLFC_CALL, klog).
 *
 * THE LEVER (offline, kl2.exe disassembly 2026-10-24): Dog Days' own cutscene executor 0x4d5c20 ("weaponhdl" parser 0x8bccb0:
 * 1 Holster, 2 Unholster) calls  0x5e7c60(player, on, mask)  thiscall, ret 8, with mask 0x100.  on=1: [player+0xbbc] |= mask;
 * if nothing is stashed yet [player+0xbb8] = the current weapon's REF and SelectItem 0x70d5c0(0,0) empties the hand.
 * on=0: [player+0xbbc] &= ~mask; with the mask clear the stashed item is selected again.  So the game HAS a real holster state;
 * this file only calls the routine the game calls.  GUESSES (said plainly): (1) that the fire key and the weapon-switch key
 * stay dead while bit 0x100 is set (the cutscene case suggests it, nothing proves it for free play); (2) the argument
 * order (self, on, mask) read from the push order at 0x4d5c20 mode 1 (push 0x100; push 1; call) -> stack args on=1, mask=0x100.
 *
 * THE MAP: a converted map sits in a stock slot (F01), so the scene name cannot say DM05A.  The gate is therefore: the scene key
 * equals Slot (default f01\f01_main), AND at the round start the human stands within Radius of the loot area centre.  A stock FA
 * map never passes the second test.  Loot area default = kl_fa_club.py 'FASpecials!PIP!EnterLootArea' (2800,450,2450) half
 * (450,150,320): that value is itself a GUESS in the builder (its comment says so); the box is configurable.
 *
 * THE PANIC: the civilians run when a player enters their tbCivRunToGate ZBoxPrimitive+TriggerBox (kl_fa_civs.py; AllInside ->
 * MiniCutsceneRout 20_RunToStreet).  ZTriggerBox (vtable 0xbc232c) slot 34 = 0x45f5d0 is the fire routine (klprobe.c: thiscall,
 * 0 stack args; it posts the message word [0x1688e70] to the list at [this+0x38]).  The hook walks the entity table, takes every
 * object with that vtable whose entity name reads "tbCivRunToGate" and calls the fire routine on each.  The name path
 * [[obj+4]+0x6c] (a C string) is klprobe.c's GUESS; if no box reads that name the panic is NOT fired (nothing else is touched)
 * and the log says so.  The fire routine may or may not re-check the AllInside condition: UNPROVEN.
 *
 * KEYS ([ClubHolster]): Enable=0  Dry=1 (log only: no holster, no fire)  Slot=f01\f01_main  Radius=2500 (world units from the
 *   loot centre that mark "this is Last Call")  Box=2800,450,2450,450,150,320 (centre xyz, half extents xyz; unlock when the feet
 *   are inside)  Near=2 (a draw key / fire pressed within Near x the box also unlocks)  Panic=draw|unlock|never  (draw: the
 *   crowd runs once the human has the gun out or fires after the unlock)  Every=100 (ms)
 * Log lines start with 'clubholster:'.
 */
#define KLCH_PLAYER_BOX 0x00bc232c
#define KLCH_FIRE_VA    0x0045f5d0
#define KLCH_HOLSTER_VA 0x005e7c60

static struct {
    int on, dry, panic;                       /* panic 0 never, 1 draw, 2 unlock */
    char slot[64]; float radius, box[6], near_;
    DWORD every, at;
    int state;                                /* 0 waiting for the round, 1 not this map, 2 locked, 3 unlocked, 4 panicked */
    DWORD pl0, hand0; int holsters, sawround;
} klch;

static float klch_dist2(const float a[3], const float b[3]) { float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2]; return x * x + y * y + z * z; }

static int klch_inbox(const float p[3], float scale)
{
    return fabsf(p[0] - klch.box[0]) <= klch.box[3] * scale && fabsf(p[1] - klch.box[1]) <= klch.box[4] * scale && fabsf(p[2] - klch.box[2]) <= klch.box[5] * scale;
}

/* player place: feet at [pl+0x460] (klb_distance reads them so) */
static int klch_feet(DWORD pl, float f[3]) { return klh_rd(pl + 0x460, f, 12); }

static void klch_holster(DWORD pl, int on)
{
    if (klch.dry) { klog("clubholster: DRY would call 0x5e7c60(player %08lx, on=%d, mask=0x100)", (unsigned long)pl, on); return; }
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, DWORD, DWORD), KLCH_HOLSTER_VA)(pl, 0, (DWORD)on, 0x100);
}

/* name guess [[obj+4]+0x6c] as klprobe.c's (a C string) */
static int klch_name_is_civ(DWORD obj)
{
    char b[40]; DWORD n = klh_rd32(obj + 4), s; int i;
    if (!n || !(s = klh_rd32(n + 0x6c)) || s < 0x10000) return 0;
    for (i = 0; i < 39; i++) { if (!klh_rd(s + i, b + i, 1)) return 0; if (!b[i]) break; }
    b[39] = 0;
    return strstr(b, "tbCivRunToGate") != 0;
}

static void klch_panic(void)
{
    DWORD p, tab, i, blk[64 * 32], seen = 0, named = 0, fired = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) { klog("clubholster: panic: no entity table"); return; }
    for (i = 0; i < 0x10000; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4];
            if (o < 0x10000 || klh_rd32(o) != (DWORD)KLCH_PLAYER_BOX) continue;
            seen++;
            if (!klch_name_is_civ(o)) continue;
            named++;
            if (klch.dry) continue;
            KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLCH_FIRE_VA)(o, 0); fired++;
        }
    }
    klog("clubholster: panic: %lu ZTriggerBox in the table, %lu named tbCivRunToGate, %lu fired%s%s", (unsigned long)seen, (unsigned long)named, (unsigned long)fired,
         klch.dry ? " (DRY: none fired)" : "", seen && !named ? " - NAME PATH UNPROVEN, nothing fired" : "");
}

static void klch_tick(int game_thread)
{
    DWORD gd, pl, now = GetTickCount(), hand; BYTE idx = 0xff, f = 0; DWORD h; float feet[3], c[3];
    struct klb_snap s; char scene[160], key[64];
    if (!klch.on || !game_thread || !klx_on) return;
    if (klch.at && now - klch.at < klch.every) return;
    klch.at = now;
    if (!klb_read(&s) || s.state != 0x19) { if (klch.sawround) { klog("clubholster: round over (state %lu)", (unsigned long)s.state); } klch.sawround = 0; klch.state = 0; klch.pl0 = 0; return; }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLO_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || idx > 31) return;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_pvt(pl) != KLO_PLAYER_VT || !klch_feet(pl, feet)) return;
    if (klch.state == 1 && pl == klch.pl0) return;                      /* judged: not this map */
    if (klch.state == 0 || pl != klch.pl0) {                            /* a new round (or a new player object) */
        klch.pl0 = pl; klch.sawround = 1; klch.holsters = 0;
        if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key) || _stricmp(key, klch.slot)) { klch.state = 1; return; }
        c[0] = klch.box[0]; c[1] = klch.box[1]; c[2] = klch.box[2];
        if (klch_dist2(feet, c) > klch.radius * klch.radius) { klch.state = 1; klog("clubholster: slot %s but the start is not near the loot area - not Last Call, off for this round", key); return; }
        klch.state = 2;
        klog("clubholster: Last Call start (feet %.0f,%.0f,%.0f) - guns holstered%s", feet[0], feet[1], feet[2], klch.dry ? " (DRY)" : "");
        klch_holster(pl, 1); klch.holsters++;
        return;
    }
    hand = klh_rd32(pl + 0x920);
    if (klch.state == 2) {
        if (klch_inbox(feet, 1.f)) {
            klog("clubholster: reached the loot area - weapons free"); klch_holster(pl, 0); klch.state = 3; klch.hand0 = hand;
            if (klch.panic == 2) { klch_panic(); klch.state = 4; }
            return;
        }
        if (hand && klch.holsters < 200) { klch.holsters++; klch_holster(pl, 1); }     /* a gun came back into the hand: put it away again */
        if ((h = klo_input(gd, pl)) != 0 && klch_inbox(feet, klch.near_)) {
            f = 0; klh_rd(h + 0x3c, &f, 1);
            if (f) { klog("clubholster: fire pressed near the loot area - weapons free"); klch_holster(pl, 0); klch.state = 3; klch.hand0 = hand; if (klch.panic == 2) { klch_panic(); klch.state = 4; } }
        }
        return;
    }
    if (klch.state == 3 && klch.panic == 1) {
        f = 0; if ((h = klo_input(gd, pl)) != 0) klh_rd(h + 0x3c, &f, 1);
        if (hand || f) { klog("clubholster: gun drawn (hand %lu, fired %d) - the crowd panics", (unsigned long)hand, (int)f); klch_panic(); klch.state = 4; }
    }
}

static void klch_init(void)
{
    char buf[160], *p; int i;
    klch.on = GetPrivateProfileIntA("ClubHolster", "Enable", 0, klh_ini) != 0;
    if (!klch.on) return;
    klch.dry = GetPrivateProfileIntA("ClubHolster", "Dry", 1, klh_ini) != 0;
    GetPrivateProfileStringA("ClubHolster", "Slot", "f01\\f01_main", klch.slot, sizeof klch.slot, klh_ini);
    for (i = 0; klch.slot[i]; i++) if (klch.slot[i] >= 'A' && klch.slot[i] <= 'Z') klch.slot[i] += 32;
    klch.radius = (float)GetPrivateProfileIntA("ClubHolster", "Radius", 2500, klh_ini);
    klch.near_ = (float)GetPrivateProfileIntA("ClubHolster", "Near", 2, klh_ini);
    klch.every = GetPrivateProfileIntA("ClubHolster", "Every", 100, klh_ini); if (klch.every < 50) klch.every = 50;
    GetPrivateProfileStringA("ClubHolster", "Panic", "draw", buf, sizeof buf, klh_ini);
    klch.panic = !_stricmp(buf, "never") ? 0 : !_stricmp(buf, "unlock") ? 2 : 1;
    klch.box[0] = 2800; klch.box[1] = 450; klch.box[2] = 2450; klch.box[3] = 450; klch.box[4] = 150; klch.box[5] = 320;
    GetPrivateProfileStringA("ClubHolster", "Box", "2800,450,2450,450,150,320", buf, sizeof buf, klh_ini);
    for (i = 0, p = buf; i < 6 && *p; i++) { klch.box[i] = (float)atof(p); while (*p && *p != ',') p++; if (*p == ',') p++; }
    klog("clubholster: on (%s) slot %s radius %.0f box %.0f,%.0f,%.0f +-%.0f,%.0f,%.0f panic %s", klch.dry ? "DRY: log only" : "LIVE", klch.slot, klch.radius,
         klch.box[0], klch.box[1], klch.box[2], klch.box[3], klch.box[4], klch.box[5], klch.panic == 0 ? "never" : klch.panic == 2 ? "unlock" : "draw");
}
