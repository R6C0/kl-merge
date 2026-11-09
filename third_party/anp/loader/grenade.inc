/* ==================== grenade.inc: Dead Men's player grenade throw in Dog Days (G) ====================
   Included by anp_loader.c after squad.inc (uses anp_log, readable, g_dir, g_cscene/g_cmpCs, climb.inc's climb_guarded,
   cl_pose, cl_sys, g_clMainTid, v3dist, and squad.inc's sq_call_raw / g_sqEspDelta, sq_rd, rd32, rd8, rdf, sq_busy,
   sq_foreground). Ticked once per gameplay frame from climb.inc's frame hook (anp_rcb_pre, main thread):
       if (ra == CL_RCB_RA) { climb_frame(); squad_frame(); grenade_frame(); }

   CEG: no kl2 code byte is changed. Calls into kl2 functions, reads, and (live only) the engine's own writes inside the
   called functions. Every engine call runs inside climb_guarded() and through sq_call_raw() (stack check); a fault or a
   stack mismatch disables the module for the session ("grenade: DISABLED"). Only active in ANP levels (scene id M<digit>).

   ---- why the player cannot throw grenades in a converted level (static RE, 12 Oct) ----
   Dog Days has no player grenade throw. The pieces Dead Men uses are still in kl2.exe, but the chain is cut twice:
     1. Input. 'HoldGrenade' (GameplayInput index 11, bound to G / right shoulder in both exes' default config) is polled by
        ZGameplayInput (vt 0xbb7c74) slot 7 0x5fbfa0 into input+0x2d2, and slot 12 0x808720 hands it to the player:
        DD 0x4aa410(flag) = 'if (!flag) player+0xb90 &= ~0x40; return' - it never SETS the bit. DM's twin 0x5ef8a0 is
        'flag ? [+0x968] |= 0x40 : [+0x968] &= ~0x40'. (Every sibling setter in DD - 0x5e9530, 0x589d30, 0x4cf980,
        0x50f780, 0x63bc30 - still sets its bit.)
     2. Throw. DD 0x544780 still turns +0xb90 bit 0x40 into the 'grenade held' state bit +0x818 & 0x800 (DM 0x5f1f50:
        +0x968 -> +0x7d0), but NOTHING in kl2 reads +0x818 & 0x800 (DM reads +0x7d0 >> 0xb in its throw state machine in
        ZFFPlayer 0x5f4c10: charge +0x1340, states +0x132c 0..4, upper-body clips, then release DM 0x5e82f0). The player
        factory still builds a ZFFActionThrow for type 0x11 (DD 0x839740 -> 0x6757b0), but nothing in single player starts
        it. kl2 raises none of the grenade PlayerMonitor events (16, 17, 21, 26).
        (13 Oct, static RE, proved) ZFFActionThrow (vt 0xbb4d24) is not just a clip: its Update (slot +0x10, 0x65ce70)
        plays the clips, then releases the item in the player's hand (0x86a130: hand attacher +0x388, else +0x310) with
        the SAME three calls as below (0x477650, vt+0x2cc, 0x659be0), then removes the item from the inventory
        (0x7ddc30) once its clip + reserve (0x402430) is 0. So running that action would add the animation and nothing
        else to the projectile side; this module keeps the direct release.
   The release itself survives (NPCs use it: ZFFActorActionThrow Update 0x6c0180), and it is exactly DM's 0x5e82f0:
     DM 0x6795a0(item, pos)          = DD 0x477650 ZFFItemWeapon::SetReleasePos(const float pos[3])  -> item+0x140 (ret 4)
     DM item vt+0x2d4(vel)           = DD item vt+0x2cc (0x536dc0) SetThrowVelocity(const float v[3]) -> item+0xc8 (ret 4)
     DM 0x51dd30(item)               = DD 0x659be0 ZFFItemWeapon::TryFire(): shot cap + fire interval (item+0xf0), then
                                       tail-calls item vt+0x340 (0x4cb7a0, the shot: its WT 0xb/0xc branch launches from
                                       +0x140 with +0xc8). (ret, no args)
   ---- where the projectile comes from (13 Oct, static RE of 0x659be0 / 0x4cb7a0 / the ammo template, proved) ----
     TryFire: the owner check makes a ZPlayer owner (item+0x5c, class id [0x1535a3c]) skip the per-frame shot cap; any
       other owner over the cap only gets +0xf0 rewritten and NO shot (so '+0xf0 changed' does not prove a shot).
       Fire path: +0xf0 = now, ++[0x1535230], tail-call vt+0x340.
     Shot 0x4cb7a0: owner = item+0x5c (0 -> return at once); ++item+0x138 (shot counter: the proof the shot ran);
       ammo template = [item+0xd4] (handle, ZFFItemTemplateAmmo vt 0xbbfbfc); a non-zero release point +0x140 is used
       as the launch point and zeroed (second proof); for a ZFFPlayer owner (class [0x1548c7c]) WT 11/12 skip the aim
       trace and the NPC velocity recompute, so +0xc8 (our velocity, vt+0x2d4) goes into the launch message as is;
       then per pellet (ammoT+0x80, 1 for grenades): projectile = ammoT vt+0x2bc (0x696f50: round robin over the pool
       ammoT+0xa8 [handles], +0xac count (ctor 0x8f1b00: 25), +0xb0 next), proj vt+0x88(launch point),
       proj vt+0x130('Activate' id [0x15351dc], launch record (0x748900; velocity at +0x14), 0).
       The pool is filled once at level load (ammo template slot +0x150, 0x7782b0): 25 clones (vt+0x194) of the
       projectile template [ammoT+0x9c] (the Projectile\<name> group with the FFHavokProjectileBallistic/GasEffects
       events). A null pool array faults in 0x696f50; null entries are skipped (shot, effects, no projectile).
     The shot never touches the ammo: the gun path (item Update 0x488ad0) does clip-1 after vt+0x340, and nothing on the
       NPC/release path does. DM 0x5e8030 refills clip from reserve before the next throw. So this module consumes one.
   Item type: Dog Days' own Grenade_Gas / Smoke / FlashBang bindings are eFF2ItemTypeSpecialEquipment (3), Frag and
   Incendiary eFF2ItemTypeGrenade (0) (stock F01..F09 InventoryBinding events), so M02's Grenade_TearGas type 3 is right.
   Weapon type = template ([item+0xc4]) +0xac: 11 WT_GRENADE, 12 WT_MOLOTOV (pinned schemas_dd.json WEAPONTYPE).
   Ammo: clip = [item+0xdc] ^ 0xbeebbeeb (vt+0x2fc), reserve = [item+0xe0] ^ 0xbeebbeeb; setters vt+0x300 / vt+0x308.
   Player inventory = [P+0xcec]: +4 byte 'searched', +8 entries (16 bytes: +0 key, +8 item), +0xc count; key = registry
   index 0x47ded0 (0..0x3f, 0x40 none); 0x5aa000 finds an entry (direct index when the byte is 0, else a search).
   Item type (registry [gm+0x15b0]): 0x539e30(item) -> 0 Grenade, 1 TwoHanded, 2 OneHanded, 3 SpecialEquipment.
   PlayerMonitor: 0x589600(player, event) cdecl; byte[0x168a668 + event] = monitors registered for that event.

   ---- what this module does ----
   On G (DIK 0x22, DD's own DirectInput state, else GetAsyncKeyState): pick the grenade (an inventory weapon of WT 11/12
   with ammo; eFF2ItemType Grenade first, then SpecialEquipment - DM's smoke/gas), release point = feet + up (+ forward),
   target = the aim point P+0x27b0 (clamped to range), velocity = the NPC formula (flight time |d| / speed, v = d / t +
   (0, 491 t, 0), |v| <= vmax), then DM's release: SetReleasePos, SetThrowVelocity, TryFire.
   Before a live throw it probes what the shot needs (read-only plus handle lookups 0x8ccde0): owner = the player, the
   ammo template, its projectile template and pool (count, valid clones, next entry). A throw that could not spawn a
   projectile is refused with the reason ("NO PROJECTILE POSSIBLE: ..."); a null next entry with valid ones elsewhere
   moves the pool cursor (ammoT+0xb0, heap write) to the next valid clone.
   After TryFire it checks the shot really ran (item+0x138 went up, release point zeroed) and logs the projectile it
   launched; then it consumes one grenade (clip - 1, vt+0x300), refills the clip from the reserve (DM 0x5e8030), and
   (empty=remove) takes an empty grenade out of the inventory like ZFFActionThrow does (0x7ddc30). It raises the
   PlayerMonitor event(s) pm= (default 30 eTHROW_THROWABLE: the converter maps Dead Men's grenade lists 12/13/20 there,
   ANP_PLAYERMON_THROW). Then it follows the projectile (its node pose, 0x857110) for watch= seconds and logs the flight.
   No throw animation yet (DM plays the /Weapon_Handling/Throw_Grenade/ clips on the upper body; anim= is reserved).
   Equip assist (live): when a throw monitor registers (PlayerMonitor event 30 count goes up) and the player has no
   grenade, give the grenades the level's refused 'equip' meant (M02: kl2's equip gives nothing to a player with two guns).

   Config <DD>\ANP_grenade.txt (polled once a second; absent = live, the release default since 14 Oct; a file without a
   mode word is live too; an unknown mode word = dry but never undoes an explicit off; an unreadable file keeps the previous config). First bare token = mode, then key=value:
     off | dry | live    dry: key, inventory census, choice, release point, target and velocity are logged;
                         nothing is changed. live (default): the grenade is thrown.
     key=0x22            DIK code (G). 0 = no key (commands only)
     input=dd|async      key source (dd: DD's keyboard device, falls back to GetAsyncKeyState)
     range=2000          cm, the target is pulled back to this distance from the release point
     speed=1000          cm/s, flight time = distance / speed (NPC throw 0x6c0180)
     vmax=1500           cm/s, NPC clamp
     up=150 fwd=70       release point: feet + up, + fwd along the throw direction (horizontal; 70 clears the capsule)
     pm=30               PlayerMonitor events raised after a throw ('+' joins: pm=30+16; 0 = none)
     consume=1           a throw uses one grenade (clip - 1). 0 = infinite (the old behaviour)
     refill=1            clip 0 and reserve > 0 after the shot: move one round (vt+0x300 / vt+0x308)
     empty=keep          keep | remove: an emptied grenade stays in the inventory (0 ammo), or is removed (0x7ddc30)
     watch=6             seconds to follow and log the launched projectile (0 = off)
     cooldown=1.0        seconds between throws
     census=1            log the grenade census of the inventory whenever it changes (any mode)
     assist=auto         equip assist (see below): auto = level table (M02: Grenade_TearGas x5), off, or <Template>:<ammo>
   Test commands <DD>\ANP_grenade_cmd.txt (consumed -> ANP_grenade_cmd.done, one line per frame):
     throw              at the aim point (P+0x27b0), as the key
     throw fwd [dist]   along the player's facing, dist cm (default 1200): for tests, the camera sees where it lands
     throw at X Y Z     at a world point
     probe | inv | raise N | state | give <TemplateName> [ammo] (live only)
       probe: the projectile probe of the grenade a throw would pick, nothing thrown (any mode)
   Log lines start with "grenade:". */

#define GR_WEAPON_VT   0xbc042c   /* ZFFItemWeapon */
#define GR_F_SETREL    0x477650
#define GR_F_TRYFIRE   0x659be0
#define GR_F_PMRAISE   0x589600
#define GR_F_REGTYPE   0x539e30
#define GR_PM_COUNT    0x168a668
#define GR_AMMO_XOR    0xbeebbeebu
#define GR_F_HOBJ      0x8ccde0   /* handle -> object, cdecl(handle) */
#define GR_F_INVDEL    0x7ddc30   /* inventory: remove item, thiscall(inv, item) ret 4 (ZFFActionThrow 0x65d49e) */
#define GR_F_POSE      0x857110   /* node world pose (climb.inc cl_pose) */
#define GR_AMMOT_VT    0xbbfbfc   /* ZFFItemTemplateAmmo */

enum { GR_OFF, GR_DRY, GR_LIVE };
static const char *GR_MODE[] = {"off", "dry", "live"};
typedef struct { int mode, key, input, range, census, refill, consume, empty, pmN, pm[4]; float speed, vmax, up, fwd, cooldown, watch; } GrCfg;
#define GR_CFG_DEFAULT {GR_LIVE, 0x22, 1, 2000, 1, 1, 1, 0, 1, {30, 0, 0, 0}, 1000.0f, 1500.0f, 150.0f, 70.0f, 1.0f, 6.0f}   /* fwd 70: clear of the player's capsule (review) */
static GrCfg g_grc = GR_CFG_DEFAULT;
static int g_grcPresent = -1; static FILETIME g_grcTime; static DWORD g_grcPoll;
static int g_grDead, g_grBuildOk = -1, g_grPrevKey, g_grThrows;
static DWORD g_grLastThrow, g_grLastCensus;
static char g_grScene[8], g_grCensus[512];
static BYTE *g_grP, *g_grKb;
static char g_grAssistCfg[48] = "auto";
static int g_grPm30, g_grAssisted;

static void gr_kill(const char *what, const char *why) {
    if (g_grDead) return;
    g_grDead = 1;
    anp_log("grenade: DISABLED after %s: %s (restart the game to re-enable)", what, why);
}
static DWORD gr_call(const char *what, DWORD fn, void *self, int n, const DWORD *a, int cdecl_) {
    if (g_grDead) return 0;
    g_sqEspDelta = 0;
    DWORD r = sq_call_raw(fn, self, n, a, cdecl_);
    if (g_sqEspDelta) { anp_log("grenade: esp mismatch after %s (fn %08lx, delta %d)", what, fn, g_sqEspDelta); gr_kill(what, "stack mismatch"); }
    return r;
}
static DWORD gr_vcall(const char *what, BYTE *obj, DWORD off, int n, const DWORD *a) {
    DWORD fn = rd32((BYTE*)rd32(obj) + off);
    if (fn < 0x401000 || fn >= 0xb10000) { anp_log("grenade: %s: vt+0x%lx of %p is not kl2 code (%08lx)", what, off, obj, fn); gr_kill(what, "bad vtable"); return 0; }
    return gr_call(what, fn, obj, n, a, 0);
}

/* this kl2 build: prologue bytes of every function called directly (read-only) */
static int gr_check_build(void) {
    static const struct { DWORD a; BYTE b[6]; } t[] = {
        {GR_F_SETREL,   {0x51, 0x8b, 0x44, 0x24, 0x08, 0xd9}}, {GR_F_TRYFIRE,  {0x83, 0xec, 0x0c, 0x53, 0x56, 0x8b}},
        {GR_F_PMRAISE,  {0x55, 0x8b, 0x6c, 0x24, 0x0c, 0x80}},
        {GR_F_REGTYPE,  {0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b}}, {0x536dc0,      {0x51, 0x8b, 0x44, 0x24, 0x08, 0xd9}},
        {0x4aa410,      {0x80, 0x7c, 0x24, 0x04, 0x00, 0x75}},
        {GR_F_HOBJ,     {0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d}}, {GR_F_INVDEL,   {0xa1, 0x5c, 0x26, 0xdd, 0x00, 0x56}},
        {GR_F_POSE,     {0xd9, 0xe8, 0x53, 0x56, 0x8b, 0x74}}, {0x4cb7a0,      {0x81, 0xec, 0xa0, 0x01, 0x00, 0x00}},
        {0x696f50,      {0x8b, 0x81, 0xb0, 0x00, 0x00, 0x00}},
    };
    for (unsigned i = 0; i < sizeof t / sizeof t[0]; i++)
        if (!readable((void*)t[i].a, 6) || memcmp((void*)t[i].a, t[i].b, 6)) { anp_log("grenade: kl2 build mismatch at %08lx - live off (dry only)", t[i].a); return 0; }
    if (rd32((void*)(GR_WEAPON_VT + 0x2cc)) != 0x536dc0 || rd32((void*)(GR_WEAPON_VT + 0x340)) != 0x4cb7a0 ||
        rd32((void*)(GR_WEAPON_VT + 0x300)) != 0x6f4f30 || rd32((void*)(GR_WEAPON_VT + 0x308)) != 0x8be2c0 ||
        rd32((void*)(GR_AMMOT_VT + 0x2bc)) != 0x696f50 || rd32((void*)(GR_AMMOT_VT + 0x2a0)) != 0x87f940) {
        anp_log("grenade: ZFFItemWeapon / ZFFItemTemplateAmmo vtable slots differ - live off (dry only)"); return 0;
    }
    return 1;
}

/* ---------- config ---------- */
static void gr_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_grcPresent >= 0 && now - g_grcPoll < 1000) return;
    g_grcPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_grenade.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_grcPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_grcTime) == 0)) return;
    g_grcPresent = present;
    if (present) g_grcTime = fa.ftLastWriteTime;
    GrCfg c = GR_CFG_DEFAULT;
    char assist[sizeof g_grAssistCfg] = "auto";       /* applied with the rest only after a good read */
    char buf[1024] = ""; const char *note = present ? "" : " (no ANP_grenade.txt: live)";
    if (present) {
        static int unreadLogged;
        FILE *f = fopen(fn, "r");
        if (!f) {                                     /* held by an editor / the helper: keep the previous config, retry next poll */
            memset(&g_grcTime, 0, sizeof g_grcTime);
            if (!unreadLogged) { unreadLogged = 1; anp_log("grenade: ANP_grenade.txt unreadable - previous config kept, retry"); }
            return;
        }
        unreadLogged = 0;
        size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
        for (char *p = buf; (p = strchr(p, '#')); ) while (*p && *p != '\n') *p++ = ' ';
        int known = 0;                                /* an explicit known mode word was seen */
        for (char *t = strtok(buf, " \t\r\n,;"); t; t = strtok(NULL, " \t\r\n,;")) {
            char *eq = strchr(t, '=');
            const char *k = t, *v = "";
            if (eq) { *eq = 0; v = eq + 1; } else { v = t; k = "mode"; }
            int iv = (int)strtol(v, NULL, 0); float fv = (float)atof(v);
            if (!_stricmp(k, "mode")) {
                int m = -1; for (int i = 0; i < 3; i++) if (!_stricmp(v, GR_MODE[i])) m = i;
                if (m < 0) { c.mode = (known && c.mode == GR_OFF) ? GR_OFF : GR_DRY; anp_log("grenade: config mode '%s' unknown (unknown mode word: %s)", v, c.mode == GR_OFF ? "off kept" : "dry"); }
                else { c.mode = m; known = 1; }
            }
            else if (!_stricmp(k, "key")) c.key = iv & 0xff;
            else if (!_stricmp(k, "input")) c.input = _stricmp(v, "async") ? 1 : 2;
            else if (!_stricmp(k, "range")) c.range = iv < 200 ? 200 : iv > 6000 ? 6000 : iv;
            else if (!_stricmp(k, "speed")) c.speed = fv < 200.0f ? 200.0f : fv > 5000.0f ? 5000.0f : fv;
            else if (!_stricmp(k, "vmax")) c.vmax = fv < 200.0f ? 200.0f : fv > 6000.0f ? 6000.0f : fv;
            else if (!_stricmp(k, "up")) c.up = fv < 0.0f ? 0.0f : fv > 250.0f ? 250.0f : fv;
            else if (!_stricmp(k, "fwd")) c.fwd = fv < -100.0f ? -100.0f : fv > 150.0f ? 150.0f : fv;
            else if (!_stricmp(k, "cooldown")) c.cooldown = fv < 0.1f ? 0.1f : fv > 10.0f ? 10.0f : fv;
            else if (!_stricmp(k, "refill")) c.refill = iv != 0;
            else if (!_stricmp(k, "consume")) c.consume = iv != 0;
            else if (!_stricmp(k, "empty")) c.empty = !_stricmp(v, "remove") ? 1 : 0;
            else if (!_stricmp(k, "watch")) c.watch = fv < 0.0f ? 0.0f : fv > 20.0f ? 20.0f : fv;
            else if (!_stricmp(k, "census")) c.census = iv != 0;
            else if (!_stricmp(k, "pm")) {
                c.pmN = 0;
                for (const char *p = v; *p && c.pmN < 4; ) {
                    int e = (int)strtol(p, (char**)&p, 0);
                    if (e > 0 && e < 33) c.pm[c.pmN++] = e;
                    while (*p == '+' || *p == ' ') p++;
                    if (*p && (*p < '0' || *p > '9')) break;
                }
            }
            else if (!_stricmp(k, "assist")) { _snprintf(assist, sizeof assist, "%s", v); assist[sizeof assist - 1] = 0; }
            else if (!_stricmp(k, "anim")) anp_log("grenade: config 'anim' is not in this build (no throw clip yet)");
            else anp_log("grenade: config key '%s' unknown", k);
        }
    }
    g_grc = c;
    _snprintf(g_grAssistCfg, sizeof g_grAssistCfg, "%s", assist); g_grAssistCfg[sizeof g_grAssistCfg - 1] = 0;
    char pms[32] = ""; for (int i = 0; i < c.pmN; i++) _snprintf(pms + strlen(pms), sizeof pms - strlen(pms), "%s%d", i ? "+" : "", c.pm[i]);
    anp_log("grenade: config mode=%s key=%02x input=%s range=%d speed=%.0f vmax=%.0f up=%.0f fwd=%.0f pm=%s consume=%d refill=%d empty=%s watch=%.1f cooldown=%.1f census=%d assist=%s%s",
            GR_MODE[c.mode], c.key, c.input == 2 ? "async" : "dd", c.range, (double)c.speed, (double)c.vmax, (double)c.up, (double)c.fwd,
            c.pmN ? pms : "none", c.consume, c.refill, c.empty ? "remove" : "keep", (double)c.watch, (double)c.cooldown, c.census, g_grAssistCfg, note);
}

/* ---------- input ---------- */
static int gr_key_down(int dik) {
    if (!dik) return 0;
    if (g_grc.input == 1) {
        if (!g_grKb || !sq_rd(g_grKb, 0x34) || *(DWORD*)g_grKb != 0xb8f4dc) {          /* ZSysInputWintel [0xddb958] devices */
            g_grKb = 0;
            BYTE *sys = (BYTE*)rd32((void*)0xddb958);
            int n = sq_rd(sys, 0x94) ? (int)*(DWORD*)(sys + 0x90) : 0;
            for (int i = 0; i < n && i < 16; i++) { BYTE *d = (BYTE*)rd32(sys + 4 + 4 * i); if (sq_rd(d, 0x34) && *(DWORD*)d == 0xb8f4dc) { g_grKb = d; break; } }
        }
        if (g_grKb) {
            int n = (int)rd32(g_grKb + 0x30); BYTE *st = (BYTE*)rd32(g_grKb + 0x2c);
            return dik < n && dik < 512 && sq_rd(st + dik, 1) && st[dik] != 0;
        }
    }
    UINT vk = MapVirtualKeyA(dik, 3 /* MAPVK_VSC_TO_VK_EX */);
    return vk && (GetAsyncKeyState(vk) & 0x8000);
}

/* ---------- objects ---------- */
static BYTE *gr_player(void) {
    BYTE *gm = (BYTE*)rd32((void*)0xdd265c);
    if (!sq_rd(gm + 0x828, 0x74)) return 0;
    signed char pi = *(signed char*)(gm + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gm + 0x828 + 4 * pi);
    return (sq_rd(P, 0x2e00) && *(DWORD*)P == 0xbb45f4) ? P : 0;
}
static int gr_clip(BYTE *it) { return sq_rd(it + 0xdc, 8) ? (int)(*(DWORD*)(it + 0xdc) ^ GR_AMMO_XOR) : -1; }
static int gr_reserve(BYTE *it) { return sq_rd(it + 0xdc, 8) ? (int)(*(DWORD*)(it + 0xe0) ^ GR_AMMO_XOR) : -1; }
static BYTE *gr_tmpl(BYTE *it) { BYTE *t = (BYTE*)rd32(it + 0xc4); return sq_rd(t, 0xb0) ? t : 0; }
static int gr_wtype(BYTE *it) { BYTE *t = gr_tmpl(it); return t ? (int)*(DWORD*)(t + 0xac) : -1; }
static void gr_tname(BYTE *it, char *out, int n) {
    out[0] = 0;
    BYTE *t = gr_tmpl(it); BYTE *node = t ? (BYTE*)rd32(t + 4) : 0; const char *p = (const char*)rd32(node + 0x6c);
    if (!sq_rd(p, 1)) { _snprintf(out, n, "?"); return; }
    int k = 0; while (k < n - 1 && sq_rd(p + k, 1) && p[k] >= 32 && p[k] < 127) { out[k] = p[k]; k++; }
    out[k] = 0;
}
typedef struct { BYTE *it; int key, wt, clip, res, itype; char name[48]; } GrItem;
/* every weapon in the player's inventory [P+0xcec] (entries of 16 bytes, item at +8) */
static int gr_inventory(BYTE *P, GrItem *out, int max) {
    BYTE *inv = (BYTE*)rd32(P + 0xcec);
    if (!sq_rd(inv, 0x10)) return -1;
    BYTE *ent = (BYTE*)rd32(inv + 8); int cnt = (int)rd32(inv + 0xc), srch = rd8(inv + 4);
    int n = srch ? cnt : 0x41;
    if (n < 0 || n > 0x41 || !sq_rd(ent, 16 * n)) return -2;
    int k = 0;
    for (int i = 0; i < n && k < max; i++) {
        BYTE *it = (BYTE*)rd32(ent + 16 * i + 8);
        if (!sq_rd(it, 0x150) || *(DWORD*)it != GR_WEAPON_VT) continue;
        GrItem *g = &out[k++];
        g->it = it; g->key = srch ? (int)rd32(ent + 16 * i) : i; g->wt = gr_wtype(it); g->clip = gr_clip(it); g->res = gr_reserve(it);
        g->itype = -1; gr_tname(it, g->name, sizeof g->name);
    }
    return k;
}
static int gr_is_grenade(const GrItem *g) { return (g->wt == 11 || g->wt == 12); }

/* item type through the registry (0x539e30): 0 Grenade .. 3 SpecialEquipment */
typedef struct { BYTE *it; int r; } GrTypeArg;
static int gr_type_body(void *a_) {
    GrTypeArg *a = a_;
    BYTE *gm = (BYTE*)rd32((void*)0xdd265c); BYTE *reg = (BYTE*)rd32(gm + 0x15b0);
    if (!sq_rd(reg, 0x100)) { a->r = -1; return 0; }
    DWORD arg[1] = {(DWORD)a->it};
    a->r = (int)gr_call("item type", GR_F_REGTYPE, reg, 1, arg, 0);
    return 0;
}
static int gr_item_type(BYTE *it) {
    if (g_grBuildOk != 1) return -1;
    GrTypeArg a = {it, -1};
    if (climb_guarded("grenade item type", gr_type_body, &a) < 0) { gr_kill("item type", "fault"); return -1; }
    return a.r;
}

static void gr_census(BYTE *P, int force) {
    GrItem g[24]; int n = gr_inventory(P, g, 24);
    char s[512]; int L = 0;
    if (n < 0) L = _snprintf(s, sizeof s, "inventory unreadable (%d)", n);
    else {
        L = _snprintf(s, sizeof s, "%d weapon(s):", n);
        for (int i = 0; i < n && L < (int)sizeof s - 80; i++) {
            if (!gr_is_grenade(&g[i]) && !force) continue;
            L += _snprintf(s + L, sizeof s - L, " [%s wt=%d clip=%d res=%d %p]", g[i].name, g[i].wt, g[i].clip, g[i].res, g[i].it);
        }
    }
    if (force || strcmp(s, g_grCensus)) {
        memcpy(g_grCensus, s, sizeof s);
        anp_log("grenade: census %s %s", g_grScene, s);
    }
}

/* ---------- the throw ---------- */
static BYTE *gr_obj(DWORD h) {               /* handle -> object (0x8ccde0); only inside climb_guarded */
    if (!h || g_grDead) return 0;
    DWORD a[1] = {h};
    BYTE *o = (BYTE*)gr_call("handle->obj", GR_F_HOBJ, 0, 1, a, 1);
    return sq_rd(o, 8) ? o : 0;
}
/* what the shot (0x4cb7a0) needs to launch a projectile, read before the throw (reads + handle lookups only) */
typedef struct {
    BYTE *P, *it, *ownerObj, *ammoT, *projT, *proj; DWORD owner, *pool;
    int pellets, pCnt, pIdx, pValid, pNext, shots; const char *why;
} GrProbe;
static int gr_probe_body(void *a_) {
    GrProbe *p = a_;
    p->why = 0; p->ammoT = p->projT = p->proj = p->ownerObj = 0; p->pool = 0;
    p->pellets = p->pCnt = p->pValid = 0; p->pIdx = p->pNext = -1;
    p->shots = (int)rd32(p->it + 0x138);
    p->owner = rd32(p->it + 0x5c); p->ownerObj = gr_obj(p->owner);                       if (g_grDead) return 0;
    p->ammoT = gr_obj(rd32(p->it + 0xd4));                                                 if (g_grDead) return 0;
    if (!sq_rd(p->ammoT, 0xc0) || *(DWORD*)p->ammoT != GR_AMMOT_VT) {
        p->why = p->ammoT ? "the ammo template (item+0xd4) is not a ZFFItemTemplateAmmo" : "no ammo template (item+0xd4 resolves to nothing)";
    } else {
        p->pellets = (int)rd32(p->ammoT + 0x80);
        p->projT = gr_obj(rd32(p->ammoT + 0x9c));                                          if (g_grDead) return 0;
        p->pool = (DWORD*)rd32(p->ammoT + 0xa8); p->pCnt = (int)rd32(p->ammoT + 0xac); p->pIdx = (int)rd32(p->ammoT + 0xb0);
        if (!p->pool || p->pCnt <= 0 || p->pCnt > 256 || !sq_rd(p->pool, 4 * p->pCnt) || p->pIdx < 0 || p->pIdx >= p->pCnt)
            p->why = "no projectile pool (ammo template +0xa8/+0xac/+0xb0; 0x696f50 would fault)";
        else {
            for (int k = 0; k < p->pCnt && !g_grDead; k++) {
                int i = (p->pIdx + k) % p->pCnt;
                BYTE *o = gr_obj(p->pool[i]);
                if (o) { p->pValid++; if (p->pNext < 0) { p->pNext = i; p->proj = o; } }
            }
            if (g_grDead) return 0;
            if (!p->pValid) p->why = "the projectile pool is empty: no clone of the projectile template (ammo template +0x9c) was made at level load";
        }
        if (!p->why && p->pellets < 1) p->why = "the ammo template launches 0 projectiles (+0x80)";
        {   /* the shot's own launch gate (0x4cb8f5): weapon template +0x1a4 (PosBox_MuzzleExit, set at init 0x6eaa10) */
            BYTE *wt = (BYTE*)rd32(p->it + 0xc4);
            if (!p->why && (!sq_rd(wt, 0x1a8) || !rd32(wt + 0x1a4))) p->why = "the weapon template's muzzle/launch box (+0x1a4) is null: the shot would skip the launch";
        }
    }
    if (p->ownerObj != p->P)                       /* the most basic one wins */
        p->why = p->ownerObj ? "the item's owner (item+0x5c) is not the player (TryFire would cap it, the shot would aim it like an NPC's)"
                             : "the item has no owner (item+0x5c): the shot returns at once";
    return 0;
}
static int gr_probe(GrProbe *p) {
    if (g_grBuildOk != 1) { p->why = "build check failed"; return 0; }
    if (climb_guarded("grenade probe", gr_probe_body, p) < 0) { gr_kill("probe", "fault (see 'climb: FAULT ... in grenade probe' above)"); return 0; }
    return !g_grDead;
}
static void gr_probe_log(const char *src, const char *name, const GrProbe *p) {
    anp_log("grenade: %s probe %s: owner %08lx -> %p%s, ammo template %p pellets %d, projectile template %p (vt %08lx), pool %p count %d cursor %d valid %d -> launch entry %d = %p (vt %08lx)%s%s",
            src, name, p->owner, p->ownerObj, p->ownerObj == p->P ? " (the player)" : "", p->ammoT, p->pellets, p->projT, rd32(p->projT),
            p->pool, p->pCnt, p->pIdx, p->pValid, p->pNext, p->proj, rd32(p->proj),
            p->why ? " | NO PROJECTILE POSSIBLE: " : " | ok", p->why ? p->why : "");
}

/* projectile pose (node world pose 0x857110, as cl_pose) */
typedef struct { BYTE *o; float M[9], pos[3]; int ok; } GrPose;
static int gr_pose_body(void *a_) { GrPose *a = a_; a->ok = sq_rd(a->o, 8) ? cl_pose(a->o, a->M, a->pos) : 0; return 0; }
static int gr_pose(BYTE *o, float *pos) {
    GrPose a; memset(&a, 0, sizeof a); a.o = o;
    if (climb_guarded("grenade pose", gr_pose_body, &a) < 0) { gr_kill("pose", "fault"); return 0; }
    if (a.ok) memcpy(pos, a.pos, 12);
    return a.ok;
}
/* follow the launched projectile for watch= seconds */
static struct { BYTE *o; DWORD vt, t0, next; int n, still; float rel[3], prev[3], top[3], far_; } g_grW;
static void gr_watch_start(BYTE *o, const float *rel) {
    memset(&g_grW, 0, sizeof g_grW);
    if (!o || g_grc.watch <= 0.0f) return;
    g_grW.o = o; g_grW.vt = rd32(o); g_grW.t0 = GetTickCount(); g_grW.next = g_grW.t0;
    memcpy(g_grW.rel, rel, 12); memcpy(g_grW.prev, rel, 12); memcpy(g_grW.top, rel, 12);
}
static void gr_watch_stop(const char *why) {
    anp_log("grenade: projectile watch end (%s) after %.2fs: highest (%.1f,%.1f,%.1f) = %+.0f over the release point, last (%.1f,%.1f,%.1f) %.0f cm from it, farthest %.0f cm",
            why, (GetTickCount() - g_grW.t0) / 1000.0, g_grW.top[0], g_grW.top[1], g_grW.top[2], g_grW.top[1] - g_grW.rel[1],
            g_grW.prev[0], g_grW.prev[1], g_grW.prev[2], v3dist(g_grW.prev, g_grW.rel), g_grW.far_);
    g_grW.o = 0;
}
static void gr_watch_tick(void) {
    if (!g_grW.o) return;
    DWORD now = GetTickCount();
    if ((int)(now - g_grW.next) < 0) return;
    g_grW.next = now + 200;
    double el = (now - g_grW.t0) / 1000.0;
    if (rd32(g_grW.o) != g_grW.vt) { gr_watch_stop("the projectile object changed or went away"); return; }
    float pos[3];
    if (!gr_pose(g_grW.o, pos)) { if (!g_grDead) gr_watch_stop("no pose"); return; }
    float mv = v3dist(pos, g_grW.prev), d = v3dist(pos, g_grW.rel);
    if (pos[1] > g_grW.top[1]) memcpy(g_grW.top, pos, 12);
    if (d > g_grW.far_) g_grW.far_ = d;
    g_grW.still = (el > 0.5 && mv < 1.0f) ? g_grW.still + 1 : 0;
    if (g_grW.n++ < 40)
        anp_log("grenade: projectile +%.2fs (%.1f,%.1f,%.1f) h=%+.0f over release, %.0f cm from it, moved %.0f%s", el, pos[0], pos[1], pos[2],
                pos[1] - g_grW.rel[1], d, mv, g_grW.still == 3 ? " (at rest)" : "");
    memcpy(g_grW.prev, pos, 12);
    if (el >= g_grc.watch) gr_watch_stop("time");
    else if (g_grW.still >= 8) gr_watch_stop("at rest");
}

typedef struct { BYTE *P, *it, *ammoT; float rel[3], tgt[3], v[3], t, dist; int clip0, res0, shots1, idx1; float rel1[3]; } GrThrow;
static int gr_throw_body(void *a_) {
    GrThrow *a = a_;
    DWORD r1[1] = {(DWORD)a->rel};
    gr_call("set release pos", GR_F_SETREL, a->it, 1, r1, 0);           if (g_grDead) return 0;
    DWORD v1[1] = {(DWORD)a->v};
    gr_vcall("set throw velocity", a->it, 0x2cc, 1, v1);                if (g_grDead) return 0;
    gr_call("try fire", GR_F_TRYFIRE, a->it, 0, NULL, 0);               if (g_grDead) return 0;
    a->shots1 = (int)rd32(a->it + 0x138); a->idx1 = (int)rd32(a->ammoT + 0xb0);
    a->rel1[0] = rdf(a->it + 0x140); a->rel1[1] = rdf(a->it + 0x144); a->rel1[2] = rdf(a->it + 0x148);
    return 0;
}
typedef struct { BYTE *P, *it; int clip, res, setClip, setRes, remove; } GrAmmo;
static int gr_ammo_body(void *a_) {
    GrAmmo *a = a_;
    if (a->setClip) { DWORD c1[1] = {(DWORD)a->clip}; gr_vcall("set clip", a->it, 0x300, 1, c1); if (g_grDead) return 0; }
    if (a->setRes) { DWORD r1[1] = {(DWORD)a->res}; gr_vcall("set reserve", a->it, 0x308, 1, r1); if (g_grDead) return 0; }
    if (a->remove) {
        BYTE *inv = (BYTE*)rd32(a->P + 0xcec);
        if (sq_rd(inv, 0x14)) { DWORD d1[1] = {(DWORD)a->it}; gr_call("inventory remove", GR_F_INVDEL, inv, 1, d1, 0); }
        else a->remove = 0;
    }
    return 0;
}
typedef struct { BYTE *P; int ev; } GrRaise;
static int gr_raise_body(void *a_) {
    GrRaise *a = a_;
    DWORD args[2] = {(DWORD)a->P, (DWORD)a->ev};
    gr_call("PlayerMonitor raise", GR_F_PMRAISE, 0, 2, args, 1);
    return 0;
}
static void gr_raise(BYTE *P, int ev, const char *why) {
    int reg = rd8((void*)(GR_PM_COUNT + ev));
    GrRaise a = {P, ev};
    if (climb_guarded("grenade pm raise", gr_raise_body, &a) < 0) { gr_kill("pm raise", "fault"); return; }
    anp_log("grenade: PlayerMonitor event %d raised (%s; %d monitor(s) registered for it before)", ev, why, reg);
}

static const char *gr_precond(BYTE *P) {
    if (!(rd8(P + 0x2720) & 2)) return "not the local human player";
    int st = sq_hud_state(P);
    if (st >= 2 && st <= 13 && st != 10) return "HUD hidden (cutscene / death)";      /* as give.inc's gate */
    if (g_cl.active) return "climbing";
    /* the native rappel is a movement (id 0x10), not an action, and a MiniScene swaps the movement table: neither is
       caught by the action check below (cover throws stay allowed, as in Dead Men) */
    if (rd32(P + 0x6b0) != (DWORD)(P + 0xdb0)) return "movement table (MiniScene)";
    if (cl_movid(P) == 0x10) return "rappelling";
    if (sq_busy(P)) return "player busy / cutscene (0x6a88f0)";
    if (rd32(P + 0xd50) || rd32(P + 0xd44)) return "seat/carrier";
    BYTE *disp = (BYTE*)rd32(P + 0x19c);
    if (sq_rd(disp, 8) && *(DWORD*)(disp + 4)) return "action running";
    return 0;
}
/* the grenade a throw would use: eFF2ItemType Grenade first, then SpecialEquipment (gas/smoke/flash), with ammo */
static int gr_pick(BYTE *P, const char *src, GrItem *g, int *n) {
    *n = gr_inventory(P, g, 24);
    if (*n < 0) { anp_log("grenade: %s: inventory unreadable (%d)", src, *n); return -1; }
    int pick = -1, pickT = 9;
    for (int i = 0; i < *n; i++) {
        if (!gr_is_grenade(&g[i]) || g[i].clip + (g[i].res > 0 ? g[i].res : 0) <= 0) continue;
        int t = gr_item_type(g[i].it); if (g_grDead) return -1;
        g[i].itype = t;
        int rank = t == 0 ? 0 : t == 3 ? 1 : 2;
        if (rank < pickT) { pickT = rank; pick = i; }
    }
    if (pick < 0) { anp_log("grenade: %s: no grenade with ammo in the inventory (%d weapon(s))", src, *n); gr_census(P, 1); }
    return pick;
}
enum { GR_AT_AIM, GR_AT_FWD, GR_AT_POINT };
static void gr_try(BYTE *P, const char *src, int how, const float *at, float fwdDist) {
    DWORD now = GetTickCount();
    if (now - g_grLastThrow < (DWORD)(g_grc.cooldown * 1000.0f)) { anp_log("grenade: %s ignored (cooldown)", src); return; }
    const char *why = gr_precond(P);
    if (why) { anp_log("grenade: %s ignored (%s)", src, why); return; }
    GrItem g[24]; int n = 0, pick = gr_pick(P, src, g, &n);
    if (pick < 0) return;
    GrThrow a; memset(&a, 0, sizeof a);
    a.P = P; a.it = g[pick].it; a.clip0 = g[pick].clip; a.res0 = g[pick].res;
    float M[9], feet[3];
    if (!cl_pose(P, M, feet)) { anp_log("grenade: %s: no player pose", src); return; }
    float aim[3] = {rdf(P + 0x27b0), rdf(P + 0x27b4), rdf(P + 0x27b8)};
    if (how == GR_AT_POINT) memcpy(aim, at, 12);
    float dx = aim[0] - feet[0], dz = aim[2] - feet[2], h = sqrtf(dx * dx + dz * dz);
    int aimOk = how != GR_AT_FWD && h > 50.0f && h < 100000.0f && aim[1] == aim[1];
    float fx, fz;
    if (aimOk) { fx = dx / h; fz = dz / h; }
    else { float L = sqrtf(M[0] * M[0] + M[2] * M[2]); fx = L > 1e-3f ? -M[0] / L : 0.0f; fz = L > 1e-3f ? -M[2] / L : 1.0f; }   /* climb.inc's facing */
    a.rel[0] = feet[0] + fx * g_grc.fwd; a.rel[1] = feet[1] + g_grc.up; a.rel[2] = feet[2] + fz * g_grc.fwd;
    if (aimOk) memcpy(a.tgt, aim, 12);
    else { float D = how == GR_AT_FWD ? fwdDist : 1000.0f; a.tgt[0] = a.rel[0] + fx * D; a.tgt[1] = feet[1]; a.tgt[2] = a.rel[2] + fz * D; }
    float d[3] = {a.tgt[0] - a.rel[0], a.tgt[1] - a.rel[1], a.tgt[2] - a.rel[2]};
    float L = sqrtf(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    if (L > (float)g_grc.range) { float s = (float)g_grc.range / L; d[0] *= s; d[1] *= s; d[2] *= s; L = (float)g_grc.range; }
    if (L < 100.0f) { d[0] = fx * 300.0f; d[1] = 0.0f; d[2] = fz * 300.0f; L = 300.0f; }
    a.dist = L; a.t = L / g_grc.speed; if (a.t < 0.25f) a.t = 0.25f;
    a.v[0] = d[0] / a.t; a.v[1] = d[1] / a.t + 0.5f * 982.0f * a.t; a.v[2] = d[2] / a.t;
    float vl = sqrtf(a.v[0] * a.v[0] + a.v[1] * a.v[1] + a.v[2] * a.v[2]);
    if (vl > g_grc.vmax) { float s = g_grc.vmax / vl; a.v[0] *= s; a.v[1] *= s; a.v[2] *= s; }
    GrProbe pr; memset(&pr, 0, sizeof pr); pr.P = P; pr.it = a.it;
    if (!gr_probe(&pr)) { if (g_grDead) return; }
    int live = g_grc.mode == GR_LIVE && g_grBuildOk == 1;
    anp_log("grenade: %s %s: item %s (%p wt=%d type=%d clip=%d res=%d) rel=(%.1f,%.1f,%.1f) tgt=(%.1f,%.1f,%.1f)%s dist=%.0f t=%.2fs v=(%.1f,%.1f,%.1f)%s",
            src, live ? (pr.why ? "REFUSED" : "THROW") : "dry (would throw)", g[pick].name, a.it, g[pick].wt, g[pick].itype, a.clip0, a.res0,
            a.rel[0], a.rel[1], a.rel[2], a.tgt[0], a.tgt[1], a.tgt[2],
            how == GR_AT_FWD ? " [forward]" : how == GR_AT_POINT ? " [point]" : aimOk ? "" : " [no aim point: forward]", a.dist, a.t,
            a.v[0], a.v[1], a.v[2], g_grc.mode == GR_LIVE && g_grBuildOk != 1 ? " [live refused: build check failed]" : "");
    gr_probe_log(src, g[pick].name, &pr);
    if (!live || pr.why) return;
    g_grLastThrow = now;
    a.ammoT = pr.ammoT;
    if (pr.pNext != pr.pIdx) {                        /* the next clone is gone: point the cursor at the next valid one */
        *(DWORD*)(pr.ammoT + 0xb0) = (DWORD)pr.pNext;
        anp_log("grenade: pool entry %d is empty - cursor moved to entry %d (ammo template +0xb0)", pr.pIdx, pr.pNext);
    }
    if (climb_guarded("grenade throw", gr_throw_body, &a) < 0) { gr_kill("throw", "fault (see 'climb: FAULT ... in grenade throw' above)"); return; }
    if (g_grDead) return;
    int ran = a.shots1 != pr.shots, relUsed = a.rel1[0] == 0.0f && a.rel1[1] == 0.0f && a.rel1[2] == 0.0f;
    float ppos[3] = {0, 0, 0}; int pok = ran && gr_pose(pr.proj, ppos);
    if (g_grDead) return;
    anp_log("grenade: release done: shot %s (item+0x138 %d -> %d), release point %s, pool cursor %d -> %d, projectile %p%s (%.1f,%.1f,%.1f) %.0f cm from the release point",
            ran ? "RAN" : "did NOT run", pr.shots, a.shots1, relUsed ? "used" : "NOT used", pr.pNext, a.idx1, pr.proj, pok ? " at" : " pose unknown",
            ppos[0], ppos[1], ppos[2], pok ? v3dist(ppos, a.rel) : -1.0f);
    if (!ran) { anp_log("grenade: NO shot: TryFire stopped before the shot (fire interval item+0xf0?) - nothing launched, no ammo used"); return; }
    /* review 13 Oct: 'ran' only means the shot passed 0x4cb8b9; the launch block after the gate at 0x4cb8f5 uses the
       release point and advances the pool cursor - only that is a launch (else a parked clone would be watched) */
    int launched = relUsed && pr.pCnt > 0 && a.idx1 != pr.pNext;   /* release point consumed (0x4cb95a) and the cursor moved */
    if (!launched) { anp_log("grenade: shot ran but the launch block was skipped (release point %s, cursor %d -> %d, pellets %d) - no ammo used, no event",
                             relUsed ? "used" : "unused", pr.pNext, a.idx1, pr.pellets); return; }
    g_grThrows++;
    if (pok) gr_watch_start(pr.proj, a.rel);
    if (g_grc.consume) {                              /* the release never touches the ammo (see the header) */
        GrAmmo am; memset(&am, 0, sizeof am); am.P = P; am.it = a.it;
        int c = a.clip0, r = a.res0 > 0 ? a.res0 : 0;
        if (c > 0) c--; else if (r > 0) r--;
        if (g_grc.refill && c == 0 && r > 0) { c = 1; r--; }      /* DM 0x5e8030 */
        am.clip = c; am.res = r; am.setClip = c != a.clip0; am.setRes = r != a.res0;
        am.remove = g_grc.empty && c + r == 0;
        if (climb_guarded("grenade ammo", gr_ammo_body, &am) < 0) { gr_kill("ammo", "fault (see 'climb: FAULT ... in grenade ammo' above)"); return; }
        if (g_grDead) return;
        anp_log("grenade: ammo: clip %d -> %d, reserve %d -> %d%s", a.clip0, gr_clip(a.it), a.res0, gr_reserve(a.it),
                am.remove ? " - empty, removed from the inventory (0x7ddc30)" : c + r == 0 ? " - empty (kept: empty=keep)" : "");
    }
    for (int i = 0; i < g_grc.pmN && !g_grDead; i++) gr_raise(P, g_grc.pm[i], "grenade thrown");
}
static void gr_probe_cmd(BYTE *P) {
    GrItem g[24]; int n = 0, pick = gr_pick(P, "cmd probe", g, &n);
    if (pick < 0) return;
    GrProbe pr; memset(&pr, 0, sizeof pr); pr.P = P; pr.it = g[pick].it;
    if (gr_probe(&pr)) gr_probe_log("cmd", g[pick].name, &pr);
}

/* ---------- equip assist: DD's 'equip' refuses grenades when the player carries two guns ----------
   kl2's mini-cutscene 'equip' (parser 0x502090, vt 0xbce86c; it creates the item from the template at parse time) runs
   0x7cd310 on a player section: if the inventory has no item of that id, it counts the inventory's two-handed and
   one-handed entries (0x73c470(inv, 1) + 0x73c470(inv, 2)) and gives NOTHING when that is > 1 (Dog Days' two-gun rule,
   which never meets a grenade in Dog Days). M02's 023_MC_KaneEquipsKaneGrenades equips Weapon\Grenade_TearGas (ammo 5)
   right after the gun step, so the player ends up without grenades. Its out-link then enables PlayerMonitor_KaneGrenades,
   i.e. the throw monitor registers (byte[0x168a668 + 30] goes up). On that rise, with no grenade with ammo in the
   inventory, assist gives what the level's equip meant, the way 0x502090 + 0x6020d0 do it:
     item = template vt+0x24c([[sys+0xac]+0x8c], 'MEIT', 0, 0)  (ret 0x10; the equip parser's own call)
     item vt+0x27c(0, 0, 0, 0)  (no owner)   item vt+0x25c(2, 0)  (stowed)
     0x6020d0 ZFFPlayer::AddItem(item, clip, reserve)  (ret 0xc: inventory add, owner, ePICKUP_GRENADE)
   Template = the node named <assist name> whose object is a ZFFItemTemplateWeapon (vt 0xbbf61c, class check 0x488fc0).
   assist=auto (default): the level table below; assist=off; assist=<TemplateName>:<ammo> for any level. Live only. */
#define GR_TMPLW_VT    0xbbf61c   /* ZFFItemTemplateWeapon */
#define GR_F_ADDITEM   0x6020d0
static const struct { const char *scene, *tmpl; int ammo; } GR_ASSIST[] = {
    {"M02", "Grenade_TearGas", 5},      /* 023_MC_KaneEquipsKaneGrenades: equip (pullwpn 1)(ammo 5.0)(item ...Weapon\Grenade_TearGas) */
};
static BYTE *gr_find_template(const char *name) {
    DWORD stride, cap; BYTE *base;
    if (!node_table(&stride, &cap, &base)) return 0;
    size_t L = strlen(name);
    for (DWORD i = 0; i < cap && i < 400000; i++) {
        BYTE *nd = base + i * stride;
        if (!sq_rd(nd, 0x70)) break;
        BYTE *o = *(BYTE**)(nd + 0x60); const char *nm = *(const char**)(nd + 0x6c);
        if (!o || !sq_rd(o, 4) || *(DWORD*)o != GR_TMPLW_VT || !sq_rd(nm, L + 1)) continue;
        if (!memcmp(nm, name, L) && nm[L] == 0) return o;
    }
    return 0;
}
typedef struct { BYTE *P, *tmpl, *item; int clip, res; } GrGive;
static int gr_give_body(void *a_) {
    GrGive *a = a_;
    if (!(gr_call("template class", 0x488fc0, a->tmpl, 0, NULL, 0) & 0xff)) { a->item = 0; return 0; }
    BYTE *sys = (BYTE*)rd32((void*)0xdd2640), *db = (BYTE*)rd32(sys + 0xac);
    DWORD parent = rd32(db + 0x8c);
    DWORD c4[4] = {parent, 0x4954454d /* 'MEIT' */, 0, 0};
    a->item = (BYTE*)gr_vcall("create item", a->tmpl, 0x24c, 4, c4);                  if (g_grDead) return 0;
    if (!sq_rd(a->item, 0x150) || *(DWORD*)a->item != GR_WEAPON_VT) { anp_log("grenade: assist: template made %p (vt %08lx), not a ZFFItemWeapon", a->item, rd32(a->item)); a->item = 0; return 0; }
    DWORD z4[4] = {0, 0, 0, 0}, st[2] = {2, 0};
    gr_vcall("item owner none", a->item, 0x27c, 4, z4);                                   if (g_grDead) return 0;
    gr_vcall("item stowed", a->item, 0x25c, 2, st);                                       if (g_grDead) return 0;
    DWORD ad[3] = {(DWORD)a->item, (DWORD)a->clip, (DWORD)a->res};
    gr_call("player AddItem", GR_F_ADDITEM, a->P, 3, ad, 0);
    return 0;
}
static void gr_give(BYTE *P, const char *tmplName, int ammo, const char *why) {
    if (g_grBuildOk != 1 || memcmp((void*)GR_F_ADDITEM, "\x83\xec\x08\x56\x57\x8b", 6) || memcmp((void*)0x488fc0, "\x8b\x01\x8b\x50\x30\xff", 6) ||
        rd32((void*)(GR_TMPLW_VT + 0x24c)) != 0x8bdf80 || rd32((void*)(GR_WEAPON_VT + 0x27c)) != 0x7982d0) {
        anp_log("grenade: assist refused (build check)"); return;
    }
    BYTE *t = gr_find_template(tmplName);
    if (!t) { anp_log("grenade: assist (%s): no ZFFItemTemplateWeapon named '%s' in this level", why, tmplName); return; }
    GrGive a = {P, t, 0, ammo > 0 ? 1 : 0, ammo > 1 ? ammo - 1 : 0};
    if (climb_guarded("grenade give", gr_give_body, &a) < 0) { gr_kill("give", "fault (see 'climb: FAULT ... in grenade give' above)"); return; }
    if (g_grDead) return;
    anp_log("grenade: assist (%s): gave %s x%d (template %p, item %p: clip %d reserve %d)", why, tmplName, ammo, t, a.item,
            a.item ? gr_clip(a.item) : -1, a.item ? gr_reserve(a.item) : -1);
    gr_census(P, 1);
}
static int gr_has_grenade(BYTE *P) {
    GrItem g[24]; int n = gr_inventory(P, g, 24);
    for (int i = 0; i < n; i++) if (gr_is_grenade(&g[i]) && g[i].clip + (g[i].res > 0 ? g[i].res : 0) > 0) return 1;
    return 0;
}
static void gr_assist_tick(BYTE *P) {
    int pm = rd8((void*)(GR_PM_COUNT + 30));
    int rise = pm > g_grPm30; g_grPm30 = pm;
    if (!rise || g_grAssisted || _stricmp(g_grAssistCfg, "off") == 0) return;
    const char *tn = 0; int ammo = 0; char buf[48];
    if (!_stricmp(g_grAssistCfg, "auto")) {
        for (unsigned i = 0; i < sizeof GR_ASSIST / sizeof GR_ASSIST[0]; i++)
            if (!strcmp(g_grScene, GR_ASSIST[i].scene)) { tn = GR_ASSIST[i].tmpl; ammo = GR_ASSIST[i].ammo; }
    } else {
        _snprintf(buf, sizeof buf, "%s", g_grAssistCfg); char *c = strchr(buf, ':');
        ammo = c ? atoi(c + 1) : 3; if (c) *c = 0; tn = buf;
    }
    if (!tn) { anp_log("grenade: a throw monitor registered (event 30: %d) - no assist entry for %s", pm, g_grScene); return; }
    if (gr_has_grenade(P)) { anp_log("grenade: a throw monitor registered (event 30: %d) - the player has a grenade, no assist", pm); return; }
    if (g_grc.mode != GR_LIVE) { anp_log("grenade: a throw monitor registered (event 30: %d) and the player has no grenade - dry: would give %s x%d", pm, tn, ammo); return; }
    g_grAssisted = 1;
    gr_give(P, tn, ammo, "throw monitor registered, no grenade in the inventory");
}

/* ---------- test commands: ANP_grenade_cmd.txt ---------- */
static DWORD g_grCmdPoll;
static void gr_commands(BYTE *P) {
    DWORD now = GetTickCount();
    if (now - g_grCmdPoll < 250) return;              /* as give.inc: at most 4 file probes a second */
    g_grCmdPoll = now;
    char fn[MAX_PATH], done[MAX_PATH];
    _snprintf(fn, sizeof fn, "%s\\ANP_grenade_cmd.txt", g_dir); _snprintf(done, sizeof done, "%s\\ANP_grenade_cmd.done", g_dir);
    if (GetFileAttributesA(fn) == INVALID_FILE_ATTRIBUTES) return;
    char buf[512] = ""; FILE *f = fopen(fn, "r");
    if (!f) return;                                   /* still being written: next poll */
    size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
    if (!n) return;
    /* consumed before anything runs: a file that cannot be renamed or deleted would run again on every poll */
    if (!MoveFileExA(fn, done, MOVEFILE_REPLACE_EXISTING) && !DeleteFileA(fn)) {
        anp_log("grenade: cmd: cannot consume ANP_grenade_cmd.txt (error %lu) - not executed", GetLastError());
        return;
    }
    for (char *line = strtok(buf, "\r\n"); line; line = strtok(NULL, "\r\n")) {
        while (*line == ' ' || *line == '\t') line++;
        if (!*line || *line == '#') continue;
        anp_log("grenade: cmd '%s'", line);
        if (!_strnicmp(line, "throw", 5)) {
            float at[3] = {0, 0, 0}, dist = 1200.0f;
            const char *p = line + 5; while (*p == ' ' || *p == '\t') p++;
            if (!_strnicmp(p, "fwd", 3)) {
                if (sscanf(p + 3, "%f", &dist) == 1) dist = dist < 200.0f ? 200.0f : dist > 6000.0f ? 6000.0f : dist;
                gr_try(P, "cmd throw fwd", GR_AT_FWD, NULL, dist);
            }
            else if (!_strnicmp(p, "at", 2)) {
                if (sscanf(p + 2, "%f %f %f", &at[0], &at[1], &at[2]) == 3) gr_try(P, "cmd throw at", GR_AT_POINT, at, 0.0f);
                else anp_log("grenade: cmd throw at: usage 'throw at X Y Z'");
            }
            else gr_try(P, "cmd throw", GR_AT_AIM, NULL, 0.0f);
        }
        else if (!_strnicmp(line, "probe", 5)) gr_probe_cmd(P);
        else if (!_strnicmp(line, "inv", 3)) gr_census(P, 1);
        else if (!_strnicmp(line, "give", 4)) {
            char nm[48] = ""; int ammo = 3;
            if (sscanf(line + 4, " %47s %d", nm, &ammo) < 1 || !nm[0]) anp_log("grenade: cmd give: usage 'give <TemplateName> [ammo]'");
            else if (g_grc.mode != GR_LIVE) anp_log("grenade: cmd give refused (mode %s, needs live)", GR_MODE[g_grc.mode]);
            else gr_give(P, nm, ammo, "test command");
        }
        else if (!_strnicmp(line, "raise", 5)) {
            int ev = (int)strtol(line + 5, NULL, 0);
            if (ev <= 0 || ev > 32) anp_log("grenade: cmd raise: event %d out of range", ev);
            else if (g_grBuildOk != 1) anp_log("grenade: cmd raise refused (build check failed)");
            else if (g_grc.mode != GR_LIVE) anp_log("grenade: cmd raise refused (mode %s, needs live: it changes level state)", GR_MODE[g_grc.mode]);
            else gr_raise(P, ev, "test command");
        }
        else if (!_strnicmp(line, "state", 5)) {
            int pm[4] = {16, 17, 26, 30}; char s[96]; int L = 0;
            for (int i = 0; i < 4; i++) L += _snprintf(s + L, sizeof s - L, " %d:%d", pm[i], rd8((void*)(GR_PM_COUNT + pm[i])));
            anp_log("grenade: state scene %s P %p b90 %08lx 818 %08lx throws %d mode %s build %d registered monitors%s",
                    g_grScene, P, rd32(P + 0xb90), rd32(P + 0x818), g_grThrows, GR_MODE[g_grc.mode], g_grBuildOk, s);
        }
        else anp_log("grenade: cmd unknown");
        if (g_grDead) break;
    }
}

/* ---------- tick ---------- */
static int grenade_tick_body(void *unused) {
    (void)unused;
    gr_cfg_poll();
    if (g_grBuildOk < 0) { g_grBuildOk = gr_check_build(); anp_log("grenade: module ready (build check %s)", g_grBuildOk ? "ok" : "FAILED"); }
    if (g_grc.mode == GR_OFF) return 0;
    char scene[8];
    EnterCriticalSection(&g_cmpCs); memcpy(scene, g_cscene, sizeof scene); LeaveCriticalSection(&g_cmpCs);
    scene[sizeof scene - 1] = 0;
    if (!(scene[0] == 'M' && scene[1] >= '0' && scene[1] <= '9')) { g_grP = 0; g_grW.o = 0; return 0; }
    BYTE *P = gr_player();
    if (!P) { g_grP = 0; g_grW.o = 0; return 0; }
    if (P != g_grP || strcmp(scene, g_grScene)) {
        g_grP = P; memcpy(g_grScene, scene, sizeof g_grScene); g_grCensus[0] = 0; g_grPrevKey = 1;
        g_grPm30 = rd8((void*)(GR_PM_COUNT + 30)); g_grAssisted = 0; g_grW.o = 0;
        int pm[4] = {16, 17, 26, 30}; char s[96]; int L = 0;
        for (int i = 0; i < 4; i++) L += _snprintf(s + L, sizeof s - L, " %d:%d", pm[i], rd8((void*)(GR_PM_COUNT + pm[i])));
        anp_log("grenade: level %s player %p mode %s (registered monitors%s)", scene, P, GR_MODE[g_grc.mode], s);
    }
    {   /* paused (pause menu, loading): the game clock stands still - no key, no command, no assist. A key held
           through the pause counts as held (no throw on unpause until G is released and pressed again) */
        static int lastT = -0x7fffffff;
        int T = cl_curT();
        if (T == lastT) { g_grPrevKey = 1; return 0; }
        lastT = T;
    }
    gr_watch_tick();
    if (g_grDead) return 0;
    gr_commands(P);
    if (g_grDead) return 0;
    gr_assist_tick(P);
    if (g_grDead) return 0;
    DWORD now = GetTickCount();
    if (g_grc.census && now - g_grLastCensus >= 2000) { g_grLastCensus = now; gr_census(P, 0); }
    int down = g_grc.key && sq_foreground() && gr_key_down(g_grc.key);
    int edge = down && !g_grPrevKey; g_grPrevKey = down;
    if (edge) gr_try(P, "key", GR_AT_AIM, NULL, 0.0f);
    return 0;
}
static void grenade_frame(void) {
    if (g_grDead || !g_clMainTid || GetCurrentThreadId() != g_clMainTid) return;
    if (climb_guarded("grenade tick", grenade_tick_body, 0) < 0) gr_kill("tick", "fault (see 'climb: FAULT ... in grenade tick' above)");
}
