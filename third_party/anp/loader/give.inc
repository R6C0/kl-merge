/* ==================== give.inc: Dead Men weapon giving / swapping with squad mates, in Dog Days ====================
   Included by anp_loader.c after squad.inc (uses anp_log, readable, g_dir, g_cscene/g_cmpCs, climb.inc's climb_guarded,
   cl_pose, cl_curT, CL_VF, g_cl, g_clMainTid, v3dist, and squad.inc's sq_call_raw / g_sqEspDelta, sq_rd family, sq_player,
   sq_sc_of, sq_cur, sq_script, sq_bodyof, sq_name, sq_rel, sq_merc, sq_hud_state, sq_busy, sq_speech_ok, sq_node_idx,
   sq_obj_at_node, sq_soldiers, sq_dev_down, sq_foreground, sq_is_soldier_body, sq_cat). Ticked once per gameplay frame from
   climb.inc's frame hook next to squad_frame() (main thread).

   CEG: no kl2 code byte is changed. Only calls into kl2 functions and reads; the writes are the engine's own (inside the
   called functions). Every engine call runs inside climb_guarded() and through sq_call_raw(), which checks the stack
   pointer after the call; a fault or a stack mismatch disables this module for the session ("give: DISABLED"). Only active
   in ANP levels (campaign.inc scene id "M<digit>..."). Every precondition is checked BEFORE the first state change.

   ---- Dead Men (kaneandlynch.exe, static RE 12 Oct) ----
   ZFFPlayer::GiveItemTo(slot, actor) = DM 0x5f8e80 (ret 8), called only by ZInventoryWheelInput's update (DM 0x639c30, the
   wheel = hold middle mouse, InventoryWheelActive_kb) when the wheel's give target (wheel+0x20) is set; wheel+0x24 = the
   co-op partner -> ZFFPlayer::SwapWithPlayer 0x5f91d0. (Who writes wheel+0x20 was NOT found statically: inferred = the
   friendly merc the player stands at.) The wheel slot (wheel+0x40) is the ITEM TYPE: 0 grenade, 1 two-handed, 2 one-handed,
   3 special (4 = none: nothing happens). Rules, in DM's order:
     - abort if [0xc8ef58] state (0x75ef00) or player+0x11f8 (the "player disabled" counter, cutscenes) is set;
     - abort if the actor's script is in its 0x7081c0 state (script+0xac == script+0x70; meaning not identified);
     - abort if |player - actor| > 300 cm (float at 0x941598);
     - abort if neither the player (inventory +0xac0, 0x6108f0) nor the actor (actor+0x574[slot], 0x5dc2c0) has an item of
       that type;
     - REFUSE the player's item if its id is 23 RocketLauncher, 24 RocketLauncherInaccurate, 25 RocketLauncherHind,
       27 GrenadeLauncherGas or 28 GrenadeLauncherFlare (byte table 0x5f91c8; 26 GrenadeLauncher is allowed): the actor says
       script 0x721810(0) = speech id 0x25 (DM 0x7275c0(id, 3, 0), cooldown script+0x314), nothing moves;
     - player has the item, actor has none of that type: player 0x5f38f0(item) (RemoveItem), actor 0x5df760(type, h)
       (slot write 0x5df6a0), item vt+0x284(h(actor), parent of actor node, 0, 0) (owner + attach); no voice;
     - both have one (SWAP): player RemoveItem, player inventory add 0x610ec0(actorItem), actor 0x5e2800(type, item) (replace),
       actor vt+0x258/+0x254 + 0x42cda0 (unhook the old item from the actor), old item vt+0x284(h(player), ...), the player
       re-selects it (0x5f8d80) if it is not his current item; then the actor says 0x721810(1) = speech id 0x24;
     - player has none, actor has one (TAKE): the player takes it (same calls), actor slot cleared, ack 0x24;
     - always: actor 0x5dcc50, player 0x5e8ad0 (refresh). PlayerMonitor list 19 (ZInventoryDisplay update, DM 0x656b2a,
       repeating) then fires on the next HUD update, which is what M02's KaneMonitor_Weapons -> WeaponFilter chain listens to.

   ---- Dog Days (kl2.exe, static RE 12 Oct) ----
   kl2 has no wheel and no give. Its own "hand an NPC a gun" routine is 0x7fd180 (Fragile Alliance weapon handout): it uses
   exactly the primitives below, so the DD sequence here mirrors 0x7fd180 + DM 0x5f8e80:
     0x727b40 ZFFPlayer current item (vt+0x4cc right hand, else vt+0x4c8) ............ thiscall, 0 args
     0x633250 ZFFPlayer::RemoveItem(item) (unequip, inventory [P+0xcec] remove 0x7ddc30, unhook 0x6d26f0, state 2) ret 4
     0x6020d0 ZFFPlayer::AddItem(item, ammoA=-1, ammoB=-1) (= DM 0x5f8600; inventory add, owner, select; raises
              PlayerMonitor pickup event 0/1/2 by type) ................................................ ret 0xc
     0x4e3fa0 ZActor::AddItem(type, handle) = slot write 0x8df9c0(type->slot, handle): unequips the old slot item, writes
              actor+0x5e0[slot] (handle 0 clears), item state 2, re-picks the AI weapon (0x7faf00, 0x442b90) .. ret 8
     item vt+0x27c SetOwner(ownerHandle, parentObj, b, b) (ZItemWeapon 0x7982d0, owner at item+0x5c) ......... ret 0x10
     item vt+0x25c SetState(state, 0) (0x8a3510; state at item+0x50) ...................................... ret 8
     actor vt+0x258(node) / vt+0x254(node, r): unhook an item node from the actor (0x7fd180 old-item path). vt+0x258 =
              0x6de200 -> 0x45f720 returns the attachment index in [actor+0x88] (0 also when absent), so give.inc reads the
              index itself (gv_attach_index) and calls vt+0x254 (0x6f42c0, msgGeomDeAttachedFromLnkObj) only when found
     0x6d26f0 node(thiscall)(0) ret 4, 0x598460 node -> parent object, 0x6ece90 object -> handle, 0x8ccde0 handle -> object
     0x47ded0 registry([gm+0x15b0]).ItemId(item) (eFF2Item, 0x40 for none) ret 4; 0x539e30 .ItemType(item) ret 4
     type -> slot: kl2 0x49f260 (0 -> 3, 1 -> 0, 2 -> 1, 3 -> 2; type 4 jumps through 0xcccccccc, so it is never called with
              anything else; the 4 case bodies are checked at start-up and the mapping is applied here)
     0x589600 PlayerMonitor dispatch(player, event) cdecl: fires every registered monitor of that event (table 0x168a690, 20)
     0x763db0 [script+0x564] speak(id)  (ANP levels keep Dead Men's .SND: ids are DM ids, 0x24 give ack, 0x25 refusal)
   DD WeaponFilter (ZWeaponFilter slot 26 0x716cc0 -> 0x8fa1a0): +0x34 actor, +0x3c weapon template handle, +0x40 bool,
   +0x44 Equipped / +0x60 NotEquipped containers. id = registry id of the template (0x7597d0). bool 1: the actor's held item
   (vt+0x4d4, else vt+0x4d0) must be a ZItemWeapon with that id. bool 0 (M02's give checks): a ZActor (type 0x2007f9 mask
   [0x1547b24]) passes when actor+0x5e0[slot(type(id))] holds an item of that id (0x47ded0); a non-ZActor is looked up in
   its inventory [+0xcec] (0x417bc0). So after a give the merc's slot handle is what the filter reads.

   Sequences (live):
     GIVE (merc's slot empty):  P.RemoveItem(item); merc.AddItem(type, h(item)); item.SetOwner(h(merc), parent(merc), 0, 0);
                                [item.SetState(4, 0) as 0x7fd180 does, drawn=1]
     SWAP (merc has one, swap=1): P.RemoveItem(item); merc.AddItem(type, 0); merc unhooks old (vt+0x258/+0x254, 0x6d26f0);
                                merc.AddItem(type, h(item)); item.SetOwner(...); [SetState(4)]; P.AddItem(old, -1, -1)
     then: voice (ack_on=swap: DM speaks only when the player receives something), PlayerMonitor event (event=, default 18
     eSWAP_WEAPON, never raised by kl2 itself), and a read-back of merc+0x5e0[slot].

   Config <DD>\ANP_give.txt (polled once a second; absent = live, the release default since 14 Oct; a file without a
   mode word is live too; an unknown mode word = dry but never undoes an explicit off; an unreadable file keeps the previous config). First bare token = mode, then key=value:
     off | dry | live         dry: key/commands, gates, target, item and refusal rules are resolved and logged;
                              nothing is changed. live (default): the give/swap is done.
     key=0x05                 DIK code of the give key (default 4: next to the crew-order keys 1/2/3; DD binds no digit;
                              squad.inc uses 1/2/3/Tab/middle mouse, climb W+E). 0 = no key (commands only)
     target=selected          selected: squad.inc's selected receiver (sc+0x10); if there is none, the nearest merc in range
                              aim: the friendly merc under the crosshair; nearest: the nearest merc in range
     range=300                cm, DM's 0x941598
     swap=1                   1: DM swap when the merc already carries that type; 0: refuse (log only)
     types=6                  bit mask of item types that may be given (bit1 two-handed, bit2 one-handed; DM's wheel also
                              gave grenades/special; the current weapon here is always 1 or 2)
     refuse=50,51,53,54       DD eFF2Item ids refused (DM ids 23/24 -> 50, 25 -> 51, 27 -> 53, 28 -> 54 via prpconv ITEM_MAP)
     ack=0x24 deny=0x25       speech ids (0 = none); ack_on=swap|always (DM: swap)
     event=18                 PlayerMonitor event raised after a live give (0 = none)
     drawn=1                  item.SetState(4, 0) after the merc gets it (as kl2 0x7fd180)
     ui=1                     on-screen prompt (DD use-action HUD, see 'UI' below): '[4] Give <gun> to <name>' while a give
                              would be accepted, and a short result line after a key/cmd give (1 = on, 0 = off)
     uitime=2500              ms the result line stays up (500..10000)
     swapres=3                swap: reserve (in clips) the merc's old gun comes back with when its stored reserve is not
                              sane (>= 999 or < 0). AddItem(old, -1, -1) would read the reserve through 0x8b80e0(1),
                              which returns 999 while the merc still owns the gun (owner class test 0x7bea10) and stores
                              it: the census showed res=999. So the reserve is passed explicitly (the stored value when
                              it is sane, else swapres x clip capacity; 0 = keep the engine's value)
   Test commands <DD>\ANP_give_cmd.txt (consumed -> ANP_give_cmd.done, one line per frame):
     give [selected|aim|nearest|node N] | state | wait S
   Log lines start with "give:". */

#define GV_F_CURITEM  0x727b40
#define GV_F_PREMOVE  0x633250
#define GV_F_PADD     0x6020d0
#define GV_F_AADD     0x4e3fa0
#define GV_F_OBJH     0x6ece90
#define GV_F_HOBJ     0x8ccde0
#define GV_F_PARENT   0x598460
#define GV_F_UNHOOK   0x6d26f0
#define GV_F_ITEMID   0x47ded0
#define GV_F_ITEMTYPE 0x539e30
#define GV_F_PMON     0x589600
#define GV_F_SPEAK    0x763db0
#define GV_F_NODEPOS  0x7b3020
#define GV_TYPESLOT   0x49f260
#define GV_WPN_ID     0x156b7a8   /* ZItemWeapon class mask pair (id, mask), filled at kl2 start-up */
#define GV_WPN_MASK   0x156b7ac
#define GV_ACT_ID     0x1547b24   /* ZActor */
#define GV_ACT_MASK   0x1547b28
#define GV_SLOT0      0x5e0       /* ZActor item handles per slot */

enum { GV_OFF, GV_DRY, GV_LIVE };
static const char *const GV_MODE[] = {"off", "dry", "live"};
enum { GVT_SELECTED, GVT_AIM, GVT_NEAREST, GVT_NODE };
static const char *const GV_TGT[] = {"selected", "aim", "nearest", "node"};

typedef struct {
    int mode, key, target, swap, types, ack, deny, ackAlways, event, drawn, swapClips, ui, uiMs;
    float range;
    int refuse[8], nrefuse;
} GvCfg;
#define GV_CFG_DEFAULT {GV_LIVE, 0x05, GVT_SELECTED, 1, 6, 0x24, 0x25, 0, 18, 1, 3, 1, 2500, 300.0f, {50, 51, 53, 54}, 4}
static GvCfg g_gvc = GV_CFG_DEFAULT;
static int g_gvcPresent = -1; static FILETIME g_gvcTime; static DWORD g_gvcPoll;
static int g_gvDead, g_gvBuild = -1, g_gvLines;
static struct {
    BYTE *P; char scene[8]; int lastT, hudT, hudSeen, keyDown, probed; DWORD t0, cmdPoll, waitUntil, lastGive;
    BYTE *kb, *sys; int gives, swaps, refusals;
} g_gv;
static char g_gvQ[16][96]; static int g_gvQh, g_gvQn;

/* ---------- logging, calls ---------- */
static void gv_log(const char *fmt, ...) {
    if (g_gvLines > 4000) return;
    if (++g_gvLines == 4000) { anp_log("give: log line cap reached, give logging stops"); return; }
    char b[1600]; va_list ap; va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    anp_log("give: %s", b);
}
static void gv_kill(const char *where, const char *why) {
    if (!g_gvDead) anp_log("give: DISABLED for this session (%s in %s) - restart the game before testing again", why, where);
    g_gvDead = 1;
}
static DWORD gv_call(const char *what, DWORD fn, void *self, int n, const DWORD *a, int cdecl_) {
    if (g_gvDead) return 0;
    g_sqEspDelta = 0;
    DWORD r = sq_call_raw(fn, self, n, a, cdecl_);
    if (g_sqEspDelta) { anp_log("give: esp mismatch after %s (fn %08lx, delta %d)", what, fn, g_sqEspDelta); gv_kill(what, "stack mismatch"); }
    return r;
}
static DWORD gv_call0(const char *w, DWORD fn, void *self) { return gv_call(w, fn, self, 0, NULL, 0); }
static DWORD gv_call1(const char *w, DWORD fn, void *self, DWORD a0) { DWORD a[1] = {a0}; return gv_call(w, fn, self, 1, a, 0); }
static DWORD gv_call2(const char *w, DWORD fn, void *self, DWORD a0, DWORD a1) { DWORD a[2] = {a0, a1}; return gv_call(w, fn, self, 2, a, 0); }
static DWORD gv_vf(void *o, int off) { return rd32((BYTE*)rd32(o) + off); }   /* vtable slot (0 if unreadable) */

/* this kl2 build: prologue bytes of every function called directly, and the type -> slot table (read-only checks) */
static int gv_check_build(void) {
    static const struct { DWORD a; BYTE b[6]; } t[] = {
        {GV_F_CURITEM, {0x56, 0x8b, 0xf1, 0x8b, 0x06, 0x8b}}, {GV_F_PREMOVE,  {0x53, 0x8b, 0x5c, 0x24, 0x08, 0x56}},
        {GV_F_PADD,    {0x83, 0xec, 0x08, 0x56, 0x57, 0x8b}}, {GV_F_AADD,     {0xa1, 0x5c, 0x26, 0xdd, 0x00, 0x8b}},
        {GV_F_OBJH,    {0x51, 0x8b, 0x0d, 0x90, 0xff, 0xe0}}, {GV_F_HOBJ,     {0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d}},
        {GV_F_PARENT,  {0x8b, 0x41, 0x50, 0x85, 0xc0, 0x75}}, {GV_F_UNHOOK,   {0x80, 0x7c, 0x24, 0x04, 0x00, 0x74}},
        {GV_F_ITEMID,  {0x8b, 0x44, 0x24, 0x04, 0x85, 0xc0}}, {GV_F_ITEMTYPE, {0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b}},
        {GV_F_PMON,    {0x55, 0x8b, 0x6c, 0x24, 0x0c, 0x80}}, {GV_F_SPEAK,    {0x55, 0x8b, 0xec, 0x51, 0x8b, 0x01}},
        {GV_F_NODEPOS, {0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c}}, {0x8df9c0,      {0x8b, 0x44, 0x24, 0x04, 0x55, 0x8b}},
    };
    for (unsigned i = 0; i < sizeof t / sizeof t[0]; i++)
        if (!readable((void*)t[i].a, 6) || memcmp((void*)t[i].a, t[i].b, 6)) { anp_log("give: kl2 build mismatch at %08lx - give stays dry", t[i].a); return 0; }
    /* 0x49f260: jmp [type*4 + 0x49f288]; cases 0x49f26b mov eax,3 / 0x49f273 xor eax,eax / 0x49f278 mov eax,1 / 0x49f280 mov eax,2 */
    static const DWORD cs[4] = {0x49f26b, 0x49f273, 0x49f278, 0x49f280};
    if (!readable((void*)0x49f288, 16) || !readable((void*)0x49f26b, 0x1a)) { anp_log("give: type->slot table unreadable - give stays dry"); return 0; }
    for (int i = 0; i < 4; i++) if (*(DWORD*)(0x49f288 + 4 * i) != cs[i]) { anp_log("give: type->slot table differs - give stays dry"); return 0; }
    if (memcmp((void*)0x49f26b, "\xb8\x03\x00\x00\x00", 5) || memcmp((void*)0x49f273, "\x33\xc0", 2) ||
        memcmp((void*)0x49f278, "\xb8\x01\x00\x00\x00", 5) || memcmp((void*)0x49f280, "\xb8\x02\x00\x00\x00", 5)) { anp_log("give: type->slot cases differ - give stays dry"); return 0; }
    return 1;
}
static int gv_slot_of(int type) { static const int s[4] = {3, 0, 1, 2}; return type >= 0 && type < 4 ? s[type] : -1; }
static const char *gv_type_name(int t) { static const char *n[] = {"grenade", "two-handed", "one-handed", "special"}; return t >= 0 && t < 4 ? n[t] : "unbound"; }

/* ---------- config ---------- */
static void gv_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_gvcPresent >= 0 && now - g_gvcPoll < 1000) return;
    g_gvcPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_give.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_gvcPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_gvcTime) == 0)) return;
    g_gvcPresent = present;
    if (present) g_gvcTime = fa.ftLastWriteTime;
    GvCfg c = GV_CFG_DEFAULT;
    char buf[1024] = ""; const char *note = present ? "" : " (no ANP_give.txt: live)";
    if (present) {
        static int unreadLogged;
        FILE *f = fopen(fn, "r");
        if (!f) {                                     /* held by an editor / the helper: keep the previous config, retry next poll */
            memset(&g_gvcTime, 0, sizeof g_gvcTime);
            if (!unreadLogged) { unreadLogged = 1; anp_log("give: ANP_give.txt unreadable - previous config kept, retry"); }
            return;
        }
        unreadLogged = 0;
        size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
        for (char *p = buf; (p = strchr(p, '#')); ) while (*p && *p != '\n') *p++ = ' ';
        int known = 0;                                /* an explicit known mode word was seen */
        for (char *t = strtok(buf, " \t\r\n;"); t; t = strtok(NULL, " \t\r\n;")) {
            char *eq = strchr(t, '=');
            const char *k = t, *v = "";
            if (eq) { *eq = 0; v = eq + 1; } else { v = t; k = "mode"; }
            if (!_stricmp(k, "mode")) {
                int m = -1; for (int i = 0; i < 3; i++) if (!_stricmp(v, GV_MODE[i])) m = i;
                if (m < 0) { c.mode = (known && c.mode == GV_OFF) ? GV_OFF : GV_DRY; anp_log("give: config mode '%s' unknown (unknown mode word: %s)", v, c.mode == GV_OFF ? "off kept" : "dry"); }
                else { c.mode = m; known = 1; }
            }
            else if (!_stricmp(k, "key")) c.key = (int)strtol(v, NULL, 0) & 0xff;
            else if (!_stricmp(k, "target")) {
                int m = -1; for (int i = 0; i < 3; i++) if (!_stricmp(v, GV_TGT[i])) m = i;
                if (m < 0) anp_log("give: config target '%s' unknown (selected|aim|nearest)", v); else c.target = m;
            }
            else if (!_stricmp(k, "range")) { float r = (float)atof(v); if (r > 50.0f && r < 5000.0f) c.range = r; }
            else if (!_stricmp(k, "swap")) c.swap = atoi(v) != 0;
            else if (!_stricmp(k, "types")) c.types = (int)strtol(v, NULL, 0) & 0xf;
            else if (!_stricmp(k, "ack")) c.ack = (int)strtol(v, NULL, 0) & 0xff;
            else if (!_stricmp(k, "deny")) c.deny = (int)strtol(v, NULL, 0) & 0xff;
            else if (!_stricmp(k, "ack_on")) c.ackAlways = !_stricmp(v, "always");
            else if (!_stricmp(k, "event")) { int e = (int)strtol(v, NULL, 0); c.event = e >= 0 && e < 33 ? e : 18; }
            else if (!_stricmp(k, "drawn")) c.drawn = atoi(v) != 0;
            else if (!_stricmp(k, "ui")) c.ui = atoi(v) != 0;
            else if (!_stricmp(k, "uitime")) { int x = atoi(v); c.uiMs = x < 500 ? 500 : x > 10000 ? 10000 : x; }
            else if (!_stricmp(k, "swapres")) { int x = atoi(v); c.swapClips = x < 0 ? 0 : x > 20 ? 20 : x; }
            else if (!_stricmp(k, "refuse")) {
                c.nrefuse = 0;
                for (const char *p = v; *p && c.nrefuse < 8; ) {
                    char *e; long x = strtol(p, &e, 0); if (e == p) break;
                    c.refuse[c.nrefuse++] = (int)x; p = (*e == ',') ? e + 1 : e;
                }
            }
            else anp_log("give: config key '%s' unknown", k);
        }
    }
    g_gvc = c;
    char rf[64] = ""; int k = 0;
    for (int i = 0; i < c.nrefuse; i++) sq_cat(rf, sizeof rf, &k, "%s%d", i ? "," : "", c.refuse[i]);
    anp_log("give: config mode=%s key=%02x target=%s range=%.0f swap=%d types=%#x refuse=%s ack=%#x deny=%#x ack_on=%s event=%d drawn=%d swapres=%d ui=%d uitime=%d%s",
            GV_MODE[c.mode], c.key, GV_TGT[c.target], (double)c.range, c.swap, c.types, rf[0] ? rf : "-", c.ack, c.deny,
            c.ackAlways ? "always" : "swap", c.event, c.drawn, c.swapClips, c.ui, c.uiMs, note);
}

/* ---------- reads / small engine queries ---------- */
static BYTE *gv_reg(void) { BYTE *gm = (BYTE*)rd32((void*)0xdd265c); BYTE *r = (BYTE*)rd32(gm + 0x15b0); return sq_rd(r, 0x100) ? r : 0; }
static BYTE *gv_obj(DWORD h) { if (!h) return 0; DWORD a[1] = {h}; BYTE *o = (BYTE*)gv_call("handle->obj", GV_F_HOBJ, 0, 1, a, 1); return sq_rd(o, 0x60) ? o : 0; }
static DWORD gv_handle(BYTE *o) {                     /* 0x6ece90, checked by resolving it back */
    if (!sq_rd(o, 8) || !sq_rd((BYTE*)rd32(o + 4), 0x60)) return 0;
    DWORD h = gv_call0("obj->handle", GV_F_OBJH, o);
    return (h && !g_gvDead && gv_obj(h) == o) ? h : 0;
}
static int gv_is_kind(BYTE *o, DWORD idAddr, DWORD maskAddr) {   /* (vt+0x30() & [mask]) == [id], as kl2 tests classes */
    DWORD f = gv_vf(o, 0x30);
    if (!sq_rd(o, 0x60) || !sq_code(f) || !readable((void*)idAddr, 4) || !readable((void*)maskAddr, 4) || !*(DWORD*)idAddr) return 0;
    DWORD c = gv_call0("class id", f, o);
    return !g_gvDead && (c & *(DWORD*)maskAddr) == *(DWORD*)idAddr;
}
static int gv_item_id(BYTE *item) { BYTE *r = gv_reg(); return (r && item) ? (int)gv_call1("item id", GV_F_ITEMID, r, (DWORD)item) : -1; }
static int gv_item_type(BYTE *item) {                 /* 0x539e30 derefs item+0xc4 (template) */
    BYTE *r = gv_reg(); if (!r || !sq_rd(item + 0xc4, 4) || !sq_rd((BYTE*)rd32(item + 0xc4), 4)) return -1;
    return (int)gv_call1("item type", GV_F_ITEMTYPE, r, (DWORD)item);
}
static int gv_body_pos(BYTE *body, float *out) {
    out[0] = out[1] = out[2] = 0;
    BYTE *node = (BYTE*)rd32(body + 4);
    if (!sq_rd(node, 0x60)) return 0;
    gv_call1("node pos", GV_F_NODEPOS, node, (DWORD)out);
    return !g_gvDead;
}
static int gv_alive(BYTE *body) {
    if (rd8(body + 0x576) != 1) return 0;
    DWORD f = gv_vf(body, 0x680);
    return sq_code(f) && !(gv_call0("body dead", f, body) & 0xff) && !g_gvDead;
}
static BYTE *gv_cur_item(BYTE *P) { BYTE *i = (BYTE*)gv_call0("current item", GV_F_CURITEM, P); return (!g_gvDead && sq_rd(i, 0xd0)) ? i : 0; }
static void gv_item_desc(BYTE *item, char *b, int n) {
    if (!item) { _snprintf(b, n, "-"); b[n - 1] = 0; return; }
    int id = gv_item_id(item), ty = gv_item_type(item);
    _snprintf(b, n, "%p id=%d type=%d(%s) owner=%08lx state=%ld", item, id, ty, gv_type_name(ty), rd32(item + 0x5c), (long)rd32(item + 0x50));
    b[n - 1] = 0;
}
/* ZFFActor vt+0x258 = 0x6de200: lnk = [actor+0x88]; 0x45f720 scans lnk+0x18 + 0x44*i (i < [lnk+0x14]) for the node and
   returns i, or 0 when it is not there (ambiguous with i = 0). Read-only copy that returns -1 instead. */
static int gv_attach_index(BYTE *actor, BYTE *node) {
    BYTE *lnk = (BYTE*)rd32(actor + 0x88);
    if (!sq_rd(lnk, 0x18)) return -1;
    int n = (int)rd32(lnk + 0x14); if (n < 0 || n > 64) return -1;
    for (int i = 0; i < n; i++) if (sq_rd(lnk + 0x18 + 0x44 * i, 4) && rd32(lnk + 0x18 + 0x44 * i) == (DWORD)node) return i;
    return -1;
}
static BYTE *gv_slot_item(BYTE *body, int slot, DWORD *h) {
    *h = (slot >= 0 && slot < 4) ? rd32(body + GV_SLOT0 + 4 * slot) : 0;
    return *h ? gv_obj(*h) : 0;
}

/* ammo (proved statically 13 Oct): clip = [item+0xdc] ^ 0xbeebbeeb (vt+0x2fc = 0x511f50), stored reserve = [item+0xe0] ^
   0xbeebbeeb (setter vt+0x308 = 0x8be2c0 -> 0x494180, clamps < 0 to 0); clip capacity = ammo object (vt+0x2c8 = 0x82c200,
   handle [item+0xd4]) vt+0x29c (= ammo template +0x7c, as kl2's equip 0x7cd310 reads it). -1 when unreadable. */
#define GV_AMMO_XOR 0xbeebbeebu
static int gv_stored_res(BYTE *it) { return sq_rd(it + 0xdc, 8) ? (int)(*(DWORD*)(it + 0xe0) ^ GV_AMMO_XOR) : -1; }
static int gv_stored_clip(BYTE *it) { return sq_rd(it + 0xdc, 8) ? (int)(*(DWORD*)(it + 0xdc) ^ GV_AMMO_XOR) : -1; }
static int gv_clip_cap(BYTE *it) {
    if (!sq_rd(it, 0xe4) || gv_vf(it, 0x2c8) != 0x82c200) return -1;
    BYTE *ao = (BYTE*)gv_call0("ammo object", 0x82c200, it);
    if (g_gvDead || !sq_rd(ao, 0x80) || !sq_code(gv_vf(ao, 0x29c))) return -1;
    int cap = (int)gv_call0("clip capacity", gv_vf(ao, 0x29c), ao);
    return (!g_gvDead && cap > 0 && cap < 1000) ? cap : -1;
}

/* ---------- target ---------- */
static int gv_is_merc_body(BYTE *b) {                 /* friendly merc soldier (EIsMercenary 1..13; alive is checked later) */
    if (!sq_is_soldier_body(b)) return 0;
    BYTE *s = (BYTE*)rd32(b + 0x77c); int m = sq_merc(s), rel = sq_rel(b);
    return m >= 1 && m <= 13 && (rel == 0 || rel == 2);
}
static BYTE *gv_nearest_merc(BYTE *P, float *dOut) {
    float pp[3], M[9]; if (!cl_pose(P, M, pp)) return 0;
    static SqSol sol[256]; int n = sq_soldiers(sol, 256); BYTE *best = 0; float bd = 1e30f;
    for (int i = 0; i < n && !g_gvDead; i++) {
        if (!gv_is_merc_body(sol[i].body) || rd8(sol[i].body + 0x576) != 1) continue;
        float bp[3]; if (!gv_body_pos(sol[i].body, bp)) continue;
        float d = v3dist(pp, bp); if (d < bd) { bd = d; best = sol[i].body; }
    }
    if (dOut) *dOut = bd;
    return best;
}
/* body of the give target, or 0 with *why set */
static BYTE *gv_target(BYTE *P, int kind, long node, const char **why, const char **how) {
    *why = 0; *how = GV_TGT[kind];
    if (kind == GVT_NODE) {
        BYTE *o = sq_obj_at_node(node);
        if (!o || !gv_is_merc_body(o)) { *why = "node is not a friendly merc soldier"; return 0; }
        return o;
    }
    if (kind == GVT_AIM) {
        DWORD h = rd32((BYTE*)rd32(P + 0xbd4) + 0x2ac);
        BYTE *o = h ? gv_obj(h) : 0;
        if (!o || !gv_is_merc_body(o)) { *why = "no friendly merc under the crosshair"; return 0; }
        return o;
    }
    if (kind == GVT_SELECTED) {
        BYTE *sc = sq_sc_of(P), *s = sc ? sq_cur(sc) : 0;
        if (s && sq_script(s) && gv_is_merc_body(sq_bodyof(s))) return sq_bodyof(s);
        *how = "selected (none: nearest)";
    }
    float d; BYTE *b = gv_nearest_merc(P, &d);
    if (!b) *why = "no friendly merc soldier in the level";
    return b;
}

/* ---------- gates ---------- */
static int gv_anp_level(void) { return g_gv.scene[0] == 'M' && g_gv.scene[1] >= '0' && g_gv.scene[1] <= '9'; }
static const char *gv_gate(BYTE *P, int T, int fromKey) {
    if (!gv_anp_level()) return "not an ANP level";
    if (fromKey && !sq_foreground()) return "not foreground";
    if (rd8(P + 0x2728) || rd32(P + 0x2760)) return "gameplay input blocked (P+2728/2760)";
    int st = sq_hud_state(P);
    if (st >= 2 && st <= 13 && st != 10) return "HUD hidden (cutscene / death)";   /* DM: player+0x11f8 'disabled' counter */
    if (g_gv.hudSeen && T - g_gv.hudT < 1024) return "1 s cooldown after a cutscene";
    if (g_cl.active) return "climbing";
    if (sq_busy(P)) return "player busy (0x6a88f0)";
    if (rd32(P + 0x6b0) != (DWORD)(P + 0xdb0)) return "movement table (MiniScene)";
    BYTE *mov = (BYTE*)rd32(P + 0x6b4); int id = sq_rd(mov + 0x44, 4) ? *(int*)(mov + 0x44) : -1;
    if (id != 2 && id != 3) return "movement not Stand/BaseMove (cover, vehicle, climb ...)";
    if (rd8(P + 0xd29)) return "use action running";
    if (rd32(P + 0xed0) & 0x80) return "input blocked (P+ed0)";
    if (rd32(P + 0xd50) || rd32(P + 0xd44)) return "seat / carrier";
    if (!(rd8(P + 0x2720) & 2)) return "not the local human player";
    DWORD f = gv_vf(P, 0x388);
    if (!sq_code(f)) return "player vtable";
    if (gv_call0("action running", f, P)) return "player action running";
    if (g_gvDead) return "disabled";
    return 0;
}
static int gv_refused_id(int id) { for (int i = 0; i < g_gvc.nrefuse; i++) if (g_gvc.refuse[i] == id) return 1; return 0; }
static void gv_speak(BYTE *body, int id, const char *what) {
    if (!id || !body) return;
    BYTE *s = (BYTE*)rd32(body + 0x77c);
    if (!sq_script(s) || !sq_speech_ok(s)) { gv_log("voice %s id=%#x skipped (speech object not ready)", what, id); return; }
    gv_call1("speech", GV_F_SPEAK, (BYTE*)rd32(s + 0x564), (DWORD)id);
    if (!g_gvDead) gv_log("voice %s id=%#x", what, id);
}

/* ---------- state report ---------- */
static void gv_state(BYTE *P, const char *why) {
    char b[1500]; int k = 0; char d[160];
    BYTE *cur = gv_cur_item(P); gv_item_desc(cur, d, sizeof d);
    float pp[3], M[9]; cl_pose(P, M, pp);
    DWORD hP = gv_handle(P);
    sq_cat(b, sizeof b, &k, "state (%s) scene=%s mode=%s build=%s P=%p h=%08lx current=[%s]%s |", why, g_gv.scene, GV_MODE[g_gvc.mode],
           g_gvBuild == 1 ? "ok" : "MISMATCH", P, hP, d, cur && rd32(cur + 0x5c) == hP ? " (owner=P)" : "");
    static SqSol sol[256]; int n = sq_soldiers(sol, 256), shown = 0;
    for (int i = 0; i < n && shown < 6 && !g_gvDead; i++) {
        if (!gv_is_merc_body(sol[i].body)) continue;
        shown++;
        char nm[40]; sq_name(sol[i].body, nm, sizeof nm);
        float bp[3]; gv_body_pos(sol[i].body, bp);
        sq_cat(b, sizeof b, &k, " merc=%d '%s' node=%ld d=%.0f able=%d slots:", sol[i].merc, nm, sq_node_idx(sol[i].body), (double)v3dist(pp, bp), rd8(sol[i].body + 0x576));
        for (int sl = 0; sl < 4; sl++) {
            DWORD h; BYTE *it = gv_slot_item(sol[i].body, sl, &h);
            if (!h) { sq_cat(b, sizeof b, &k, " -"); continue; }
            sq_cat(b, sizeof b, &k, " %d:%d", sl, it ? gv_item_id(it) : -1);
        }
        sq_cat(b, sizeof b, &k, " |");
    }
    if (!shown) sq_cat(b, sizeof b, &k, " no friendly merc soldiers");
    gv_log("%s", b);
}

/* ---------- give-back after a fault ----------
   Between the player's RemoveItem (step 1) and the merc owning the item (step 3's SetOwner) the item belongs to nobody.
   A fault (VEH guard of the give tick) or a stack mismatch in that window would leave it lost, so the item is recorded
   here and, once, handed back to the player with DD's own pickup path 0x6020d0(item, -1, -1), guarded. Raw call: the
   module is already disabled by then (gv_call refuses to run). */
static BYTE *g_gvLimboP, *g_gvLimboItem; static const char *g_gvLimboStep;
/* the merc side (review 13 Oct): from step 3's AddItem on, the merc's slot may already hold the item's handle; handing
   it back then would leave one weapon owned by both (WeaponFilter passes, the AI re-picks it). So the slot is cleared
   first (merc AddItem(type, 0)) and the give-back is skipped when that does not take */
static BYTE *g_gvLimboBody; static int g_gvLimboType = -1, g_gvLimboSlot = -1; static DWORD g_gvLimboH;
static int gv_limbo_clear_body(void *unused) {
    (void)unused;
    DWORD a[2] = {(DWORD)g_gvLimboType, 0};
    g_sqEspDelta = 0;
    sq_call_raw(GV_F_AADD, g_gvLimboBody, 2, a, 0);
    return g_sqEspDelta ? 1 : 0;
}
static int gv_giveback_body(void *unused) {
    (void)unused;
    DWORD a[3] = {(DWORD)g_gvLimboItem, (DWORD)-1, (DWORD)-1};
    g_sqEspDelta = 0;
    sq_call_raw(GV_F_PADD, g_gvLimboP, 3, a, 0);
    return g_sqEspDelta ? 1 : 0;
}
static int gv_limbo_merc_holds(void) {
    return g_gvLimboBody && g_gvLimboSlot >= 0 && g_gvLimboSlot < 4 && g_gvLimboH && sq_rd(g_gvLimboBody + GV_SLOT0, 16)
           && rd32(g_gvLimboBody + GV_SLOT0 + 4 * g_gvLimboSlot) == g_gvLimboH;
}
static void gv_giveback(const char *why) {
    if (!g_gvLimboItem) return;
    BYTE *P = g_gvLimboP, *item = g_gvLimboItem; const char *step = g_gvLimboStep ? g_gvLimboStep : "?";
    if (!sq_rd(P, 0x2e00) || *(DWORD*)P != CL_PLAYER_VT || !sq_rd(item, 0xd0) || !sq_code(gv_vf(item, 0))) {
        anp_log("give: give-back after %s (step '%s'): player %p / item %p no longer valid - item NOT returned", why, step, P, item);
        g_gvLimboP = g_gvLimboItem = 0; return;
    }
    if (gv_limbo_merc_holds()) {
        int c = climb_guarded("give give-back slot clear", gv_limbo_clear_body, 0);
        if (c != 0 || gv_limbo_merc_holds()) {
            anp_log("give: give-back after %s (step '%s'): the merc's slot %d still holds item %p (clear %s) - left with the merc, NOT returned (no double owner)",
                    why, step, g_gvLimboSlot, item, c < 0 ? "faulted" : c ? "stack mismatch" : "did not take");
            g_gvLimboP = g_gvLimboItem = 0; g_gvLimboBody = 0; g_gvLimboH = 0; return;
        }
        anp_log("give: give-back: merc slot %d cleared first", g_gvLimboSlot);
    }
    int r = climb_guarded("give give-back", gv_giveback_body, 0);
    g_gvLimboP = g_gvLimboItem = 0; g_gvLimboBody = 0; g_gvLimboH = 0;   /* once, whatever happened */
    anp_log("give: give-back after %s (step '%s'): player AddItem 0x6020d0(%p, -1, -1) %s; item owner=%08lx state=%ld",
            why, step, item, r < 0 ? "FAULTED (item lost)" : r ? "returned with a stack mismatch" : "done",
            sq_rd(item, 0x60) ? rd32(item + 0x5c) : 0, sq_rd(item, 0x60) ? (long)rd32(item + 0x50) : -1L);
}

/* ---------- UI (on-screen prompt + result line), added 15 Oct ----------
   Dead Men showed giving only through its inventory wheel (hold middle mouse: ZInventoryWheelInput + ZInventoryDisplay,
   give target wheel+0x20); Dog Days has neither, so the text goes through DD's own use-action prompt instead, the one
   revive.inc drives for its heal prompt (static RE kl2, 15 Oct):
     0x4c06c0 ZFFPlayer offer(id, inType, float dist, const char *text, a5, b6, bRaw) thiscall ret 0x1c: gate 0x6349a0,
       then the pending prompt (+0xd00 id, +0xd08 inType, +0xd0c dist, +0xd18 text, +0xd20, +0xd25, +0xd27 bRaw) is
       replaced when id > pending id, or same id and nearer. The player update commits it every frame (0x550e3c:
       +0xcfc id, +0xd04 inType, +0xd14 text, +0xd26 bRaw) and clears the pending one, so it is offered every frame.
     ZUseActionDisplay (vt 0xbbe844) slot 5 0x8b1030 caches id/text pointer/a5/b6 and rebuilds on a change; slot 9
       0x46ec60: key = text ? text : 0x4f9400(id) default key; when bRaw (+0xd26) is 0 the key is looked up in
       "AllLevels/Interface/UseActions", when it is 1 the string is used AS IS (only {Tag} button tokens are expanded by
       0x7bb920). kl2's own 0x6fba10 offers level text the same way (id 6, bRaw 1).
     0x50a8f0(id) = "use pressed for the shown prompt id": inType selects the input (0/4 = use flag P+0x818 bit 5, ...);
       inType 6 has no input (jump table 0x50a968 entry 6 -> 0x50a94b with al = 0), so no kl2 poller can ever 'use'
       our prompt - the give stays on give.inc's key.
   We offer id 6 (UA_POINT_OF_INTEREST): low priority, so higher level prompts (generic 8, pickups 15/16, heal 0x1b ...)
   win over ours. The text lives in static buffers that are never freed (the HUD keeps the pointer); a changed text goes
   to the other buffer so the pointer changes and the HUD rebuilds. */
#define GV_F_OFFER   0x4c06c0
#define GV_UI_ID     6
#define GV_UI_INTYPE 6
static char g_gvTxt[2][192]; static int g_gvTxtCur = -1, g_gvUiOk = -1;
static char g_gvFb[192]; static DWORD g_gvFbUntil;
static char g_gvCand[192]; static float g_gvCandD; static DWORD g_gvCandT; static BYTE *g_gvCandP;
static int gv_ui_check(void) {
    static const BYTE b[6] = {0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c};
    return readable((void*)GV_F_OFFER, 6) && !memcmp((void*)GV_F_OFFER, b, 6) && readable((void*)0x46ecc2, 7)
           && !memcmp((void*)0x46ecc2, "\x80\xb9\x26\x0d\x00\x00\x00", 7);   /* cmp byte [ecx+0xd26], 0: the raw-text test */
}
static void gv_key_label(char *b, int n) {
    char k[32] = ""; if (g_gvc.key) GetKeyNameTextA((LONG)g_gvc.key << 16, k, sizeof k);
    _snprintf(b, n, "%s", k[0] ? k : "?"); b[n - 1] = 0;
}
/* Dead Men's gun name for a DD eFF2Item id (prpconv ITEM_MAP with the ANP_ITEM_EXACT + ANP_GUNFIT_M4SCAR defaults) */
static const char *gv_gun_name(int id) {
    switch (id) {
    case 1: case 4: case 8: return "USP";          case 9: return "silenced USP"; case 2: return "Taurus";
    case 16: return "Remington 870";               case 17: return "SPAS-12";     case 19: case 20: return "MP5";
    case 23: return "TMP";                         case 27: return "P90";         case 29: return "SG 552";
    case 30: case 31: case 37: return "M4";        case 32: return "AK-74";       case 33: return "Mini-14";
    case 36: case 49: return "Remington 700";      case 40: case 47: case 48: return "Minimi";
    case 50: case 51: return "RPG";                case 52: return "grenade launcher"; case 53: return "gas launcher";
    case 54: return "flare launcher";
    default: return "gun";
    }
}
static void gv_disp_name(BYTE *body, char *out, int n) {
    BYTE *gm_ = (BYTE*)rd32((void*)0xdd265c), *bb_ = gm_ ? (BYTE*)rd32(gm_ + 0x4cf0) : 0;
    if (bb_ && bb_ == body) { _snprintf(out, n, "Lynch"); out[n - 1] = 0; return; }   /* DD's buddy is DM's Lynch (node name is 'Ground') */
    char nm[48]; sq_name(body, nm, sizeof nm);
    if (!_stricmp(nm, "Ground")) { _snprintf(out, n, "your crewmate"); out[n - 1] = 0; return; }
    char lo[48]; int i; for (i = 0; nm[i] && i < 47; i++) lo[i] = (nm[i] >= 'A' && nm[i] <= 'Z') ? (char)(nm[i] + 32) : nm[i]; lo[i] = 0;
    if (strstr(lo, "lynch")) { _snprintf(out, n, "Lynch"); out[n - 1] = 0; return; }
    char *u = strstr(lo, "_squad"); if (u) nm[u - lo] = 0;
    int L = (int)strlen(nm);
    while (L > 0 && ((nm[L - 1] >= '0' && nm[L - 1] <= '9') || nm[L - 1] == '_')) nm[--L] = 0;   /* Merc_04 -> Merc */
    for (i = 0; nm[i]; i++) if (nm[i] == '_') nm[i] = ' ';
    _snprintf(out, n, "%s", L ? nm : "your crewmate"); out[n - 1] = 0;
}
static void gv_fb(const char *fmt, ...) {
    if (!g_gvc.ui) return;
    va_list ap; va_start(ap, fmt); _vsnprintf(g_gvFb, sizeof g_gvFb - 1, fmt, ap); va_end(ap); g_gvFb[sizeof g_gvFb - 1] = 0;
    g_gvFbUntil = GetTickCount() + (DWORD)g_gvc.uiMs; if (!g_gvFbUntil) g_gvFbUntil = 1;
    g_gvCandT = 0;                                    /* re-evaluate the prompt after the result line */
    gv_log("ui: result line '%s'", g_gvFb);
}
static int revive_prompt_up(void);
/* in game (15 Oct, M02): our id-6 offer beat kl2's rappel prompt, so E did nothing at the rappel point. Never offer
   while a rappel point or the revive prompt owns E, or while kl2 showed any other prompt last frame */
static int gv_ui_blocked(BYTE *P) {
    if (revive_prompt_up()) return 1;
    BYTE *rm = readable(P + 0xdf0, 4) ? *(BYTE**)(P + 0xdf0) : 0;
    if (readable(rm, 0x1f70) && *(BYTE**)(rm + 0x38) == P && (rm[0x1f6c] || *(BYTE**)(rm + 0x1f68))) return 1;
    DWORD sh = readable(P + 0xcfc, 4) ? rd32(P + 0xcfc) : 0;
    return sh && sh != GV_UI_ID;
}
static void gv_ui_offer(BYTE *P, const char *txt, float dist) {
    if (g_gvUiOk != 1 || !txt[0] || gv_ui_blocked(P)) return;
    if (g_gvTxtCur < 0 || strcmp(g_gvTxt[g_gvTxtCur], txt)) {
        int nx = g_gvTxtCur == 0 ? 1 : 0;
        _snprintf(g_gvTxt[nx], sizeof g_gvTxt[nx], "%s", txt); g_gvTxt[nx][sizeof g_gvTxt[nx] - 1] = 0;
        g_gvTxtCur = nx;
    }
    DWORD a[7] = {GV_UI_ID, GV_UI_INTYPE, fbits(dist), (DWORD)g_gvTxt[g_gvTxtCur], 0, 0, 1};
    DWORD ok = gv_call("offer prompt 0x4c06c0", GV_F_OFFER, P, 7, a, 0) & 0xff;
    static char lastLogged[192]; static DWORD lastT;
    if (!g_gvDead && (strcmp(lastLogged, txt) || sq_rate(&lastT, 30000))) {
        _snprintf(lastLogged, sizeof lastLogged, "%s", txt); lastLogged[sizeof lastLogged - 1] = 0;
        gv_log("ui: offered '%s' (id %d) -> %s; shown now id %08lx", txt, GV_UI_ID,
               ok ? "pending" : "refused (0x6349a0 gate / action / a higher prompt)", rd32(P + 0xcfc));
    }
}
/* quiet copy of gv_give's checks: the prompt text when a key give would be accepted now, else "" */
static void gv_candidate(BYTE *P, int T, char *out, int n, float *dOut) {
    out[0] = 0;
    if (gv_gate(P, T, 0) || g_gvDead) return;
    const char *why, *how; BYTE *body = gv_target(P, g_gvc.target, -1, &why, &how);
    if (!body || g_gvDead || !gv_alive(body) || revive_is_down(body)) return;
    float pp[3], M[9], bp[3];
    if (!cl_pose(P, M, pp) || !gv_body_pos(body, bp)) return;
    float d = v3dist(pp, bp); if (d > g_gvc.range) return;
    BYTE *item = gv_cur_item(P);
    if (!item || g_gvDead || !gv_is_kind(item, GV_WPN_ID, GV_WPN_MASK)) return;
    int id = gv_item_id(item), type = gv_item_type(item), slot = gv_slot_of(type);
    if (g_gvDead || slot < 0 || id < 0 || id >= 0x40 || !((g_gvc.types >> type) & 1) || gv_refused_id(id)) return;
    if (!gv_is_kind(body, GV_ACT_ID, GV_ACT_MASK) || g_gvDead) return;
    DWORD hOld; BYTE *old = gv_slot_item(body, slot, &hOld);
    if (g_gvDead || (hOld && !old) || old == item || (old && !g_gvc.swap)) return;
    char nm[48], key[32]; gv_disp_name(body, nm, sizeof nm); gv_key_label(key, sizeof key);
    if (old) {
        int oid = gv_item_id(old); if (g_gvDead) return;
        _snprintf(out, n, "[%s] Swap your %s for %s's %s", key, gv_gun_name(id), nm, gv_gun_name(oid));
    } else _snprintf(out, n, "[%s] Give %s your %s", key, nm, gv_gun_name(id));
    out[n - 1] = 0; *dOut = d;
}
static void gv_ui_tick(BYTE *P, int T) {
    if (!g_gvc.ui || g_gvDead) return;
    if (g_gvUiOk < 0) { g_gvUiOk = gv_ui_check(); anp_log("give: ui check %s", g_gvUiOk ? "ok (DD use-action prompt, raw text)" : "FAILED (no on-screen prompt)"); }
    if (g_gvUiOk != 1) return;
    DWORD now = GetTickCount();
    if (g_gvFbUntil && (int)(g_gvFbUntil - now) > 0) {   /* result line, even outside the give range */
        int st = sq_hud_state(P);
        if (!(st >= 2 && st <= 13 && st != 10)) gv_ui_offer(P, g_gvFb, 1.0f);
        return;
    }
    g_gvFbUntil = 0;
    if (P != g_gvCandP || now - g_gvCandT >= 150) {   /* the full check about 6x a second; the offer every frame */
        g_gvCandP = P; g_gvCandT = now ? now : 1;
        gv_candidate(P, T, g_gvCand, sizeof g_gvCand, &g_gvCandD);
        if (g_gvDead) return;
    }
    if (g_gvCand[0]) gv_ui_offer(P, g_gvCand, g_gvCandD);
}

/* ---------- the give ---------- */
static void gv_give(BYTE *P, int kind, long node, int T, int fromKey, const char *src) {
    static DWORD lastIgn;
    const char *why = gv_gate(P, T, fromKey);
    if (g_gvDead) return;
    if (why) { if (!fromKey || sq_rate(&lastIgn, 500)) gv_log("%s give ignored (%s)", src, why); return; }
    int live = g_gvc.mode == GV_LIVE && g_gvBuild == 1;
    if (g_gvc.mode == GV_LIVE && !live) gv_log("live requested but the kl2 build check failed: running dry");
    const char *how; BYTE *body = gv_target(P, kind, node, &why, &how);
    if (g_gvDead) return;
    if (!body) { gv_log("%s give: no target (%s, %s)", src, how, why); gv_fb("No crewmate to give a gun to"); return; }
    char nm[40]; sq_name(body, nm, sizeof nm);
    char dn[48]; gv_disp_name(body, dn, sizeof dn);
    BYTE *s = (BYTE*)rd32(body + 0x77c); int merc = sq_merc(s);
    if (!gv_alive(body)) { if (!g_gvDead) gv_log("%s give: merc=%d '%s' is not alive/able", src, merc, nm); return; }
    if (revive_is_down(body)) { gv_log("%s give: merc=%d '%s' is down (revive.inc / DD DND) - refused", src, merc, nm); gv_fb("%s is down", dn); return; }
    float pp[3], M[9], bp[3];
    if (!cl_pose(P, M, pp) || !gv_body_pos(body, bp)) return;
    float d = v3dist(pp, bp);
    if (d > g_gvc.range) { gv_log("%s give: merc=%d '%s' too far (%.0f > %.0f cm, DM 0x941598) - nothing happens", src, merc, nm, (double)d, (double)g_gvc.range); gv_fb("Get closer to %s to give a gun", dn); return; }
    BYTE *item = gv_cur_item(P);
    if (g_gvDead) return;
    if (!item) { gv_log("%s give: the player holds no item", src); gv_fb("Hold the gun you want to give %s", dn); return; }
    if (!gv_is_kind(item, GV_WPN_ID, GV_WPN_MASK)) { if (!g_gvDead) gv_log("%s give: current item %p is not a ZItemWeapon (%s)", src, item, rtti_name(item)); gv_fb("Hold the gun you want to give %s", dn); return; }
    int id = gv_item_id(item), type = gv_item_type(item), slot = gv_slot_of(type);
    if (g_gvDead) return;
    char idesc[160]; gv_item_desc(item, idesc, sizeof idesc);
    if (slot < 0 || id < 0 || id >= 0x40) { gv_log("%s give: current item unbound (%s) - refused (kl2 0x49f260 would jump through 0xcccccccc)", src, idesc); return; }
    if (!((g_gvc.types >> type) & 1)) { gv_log("%s give: %s items are not given (types=%#x) [%s]", src, gv_type_name(type), g_gvc.types, idesc); gv_fb("%s can't take that", dn); return; }
    if (!gv_is_kind(body, GV_ACT_ID, GV_ACT_MASK)) { if (!g_gvDead) gv_log("%s give: merc body %p is not a ZActor (WeaponFilter would not read its slots)", src, body); return; }
    if (gv_refused_id(id)) {
        gv_log("%s give REFUSED: item id %d is on the refusal list (DM: rocket launchers, gas/flare launchers) merc=%d '%s'%s", src, id, merc, nm, live ? "" : " (dry)");
        g_gv.refusals++;
        gv_fb("%s won't take the %s", dn, gv_gun_name(id));
        if (live) gv_speak(body, g_gvc.deny, "refusal");
        return;
    }
    DWORD hOld; BYTE *old = gv_slot_item(body, slot, &hOld);
    if (g_gvDead) return;
    if (hOld && !old) { gv_log("%s give: merc slot %d handle %08lx does not resolve - refused", src, slot, hOld); return; }
    if (old == item) { gv_log("%s give: the merc already owns this item", src); return; }
    if (old && !g_gvc.swap) { gv_log("%s give: merc=%d '%s' already carries a %s item (swap=0) - refused", src, merc, nm, gv_type_name(type)); gv_fb("%s already has a %s", dn, gv_gun_name(gv_item_id(old))); return; }
    char odesc[160]; gv_item_desc(old, odesc, sizeof odesc);
    /* swap: the reserve the merc's old gun comes back with (see swapres=) */
    int oRes0 = old ? gv_stored_res(old) : -1, oClip0 = old ? gv_stored_clip(old) : -1, oCap = old ? gv_clip_cap(old) : -1, oRes = -1;
    if (g_gvDead) return;
    const char *oResWhy = "engine value (swapres=0)";
    if (old && g_gvc.swapClips) {
        if (oRes0 >= 0 && oRes0 < 999) { oRes = oRes0; oResWhy = "its stored reserve"; }
        else if (oCap > 0) { oRes = g_gvc.swapClips * oCap; oResWhy = "stored reserve not sane: swapres x capacity"; }
        else { oRes = g_gvc.swapClips * 30; oResWhy = "stored reserve not sane, capacity unreadable: swapres x 30"; }
    }
    /* every pointer and vtable slot the sequence will use, before anything changes */
    DWORD hItem = gv_handle(item), hBody = gv_handle(body), hP = gv_handle(P);
    BYTE *bnode = (BYTE*)rd32(body + 4), *onode = old ? (BYTE*)rd32(old + 4) : 0;
    DWORD fOwner = gv_vf(item, 0x27c), fState = gv_vf(item, 0x25c), fB258 = gv_vf(body, 0x258), fB254 = gv_vf(body, 0x254);
    const char *bad = !hItem ? "item handle" : !hBody ? "merc handle" : !hP ? "player handle" : !sq_rd(bnode, 0x60) ? "merc node" :
                      !sq_code(fOwner) || !sq_code(fState) ? "item vtable" : (old && (!sq_rd(onode, 0x60) || fB258 != 0x6de200 || !sq_code(fB254) || !sq_rd(old, 0xd0))) ? "old item / merc vtable (vt+0x258 must be 0x6de200)" : 0;
    if (g_gvDead) return;
    if (bad) { gv_log("%s give: %s not usable - refused", src, bad); return; }
    gv_log("%s give %s: merc=%d '%s' node=%ld (%s) d=%.0f item=[%s] slot=%d merc_slot=[%s] -> %s%s", src, live ? "LIVE" : "dry", merc, nm,
           sq_node_idx(body), how, (double)d, idesc, slot, odesc, old ? "SWAP (merc's item comes back to the player)" : "GIVE",
           live ? "" : " (dry: nothing changed)");
    if (old) gv_log("swap: the merc's old gun would come back with clip %d, reserve %d (%s; stored reserve %d, capacity %d)%s",
                    oClip0, oRes, oResWhy, oRes0, oCap, live ? "" : " (dry)");
    int oidUi = old ? gv_item_id(old) : -1;
    if (!live) { if (g_gvc.event) gv_log("dry: would raise PlayerMonitor event %d", g_gvc.event); gv_fb("(dry) would %s %s the %s", old ? "swap with" : "give", dn, gv_gun_name(id)); return; }

    /* 1. the player lets go of it (unequip, inventory remove, unhook, state 2) */
    gv_call1("player RemoveItem 0x633250", GV_F_PREMOVE, P, (DWORD)item);
    g_gvLimboP = P; g_gvLimboItem = item; g_gvLimboStep = "player RemoveItem";   /* nobody owns it until step 3 */
    g_gvLimboBody = body; g_gvLimboType = type; g_gvLimboSlot = slot; g_gvLimboH = hItem;
    if (g_gvDead) { gv_giveback("a stack mismatch"); return; }
    /* 2. swap: empty the merc's slot and unhook his old item (kl2 0x7fd180's old-item path) */
    if (old) {
        g_gvLimboStep = "swap: empty merc slot";
        gv_call2("merc AddItem(type, 0) 0x4e3fa0", GV_F_AADD, body, (DWORD)type, 0);
        if (g_gvDead) { gv_giveback("a stack mismatch"); return; }
        int r = gv_attach_index(body, onode);         /* = vt+0x258 (0x6de200 -> 0x45f720), but -1 when not attached */
        g_gvLimboStep = "swap: detach old item";
        if (r >= 0) { gv_call2("merc vt+0x254 detach", fB254, body, (DWORD)onode, (DWORD)r); if (g_gvDead) { gv_giveback("a stack mismatch"); return; } }
        gv_log("swap: merc's old item %s (attachment index %d)", r >= 0 ? "detached" : "was not attached", r);
        g_gvLimboStep = "swap: unhook old item";
        gv_call1("unhook 0x6d26f0", GV_F_UNHOOK, onode, 0);
        if (g_gvDead) { gv_giveback("a stack mismatch"); return; }
    }
    /* 3. the merc gets it: slot write, owner + parent (as kl2 0x7fd180 / DM 0x5f90c3..0x5f90e7) */
    g_gvLimboStep = "merc AddItem";
    gv_call2("merc AddItem 0x4e3fa0", GV_F_AADD, body, (DWORD)type, hItem);
    if (g_gvDead) { gv_giveback("a stack mismatch"); return; }
    g_gvLimboStep = "node parent";
    BYTE *parent = (BYTE*)gv_call0("node parent 0x598460", GV_F_PARENT, bnode);
    if (g_gvDead) { gv_giveback("a stack mismatch"); return; }
    g_gvLimboStep = "item SetOwner";
    { DWORD a[4] = {hBody, (DWORD)parent, 0, 0}; gv_call("item SetOwner vt+0x27c", fOwner, item, 4, a, 0); }
    g_gvLimboP = g_gvLimboItem = 0; g_gvLimboStep = 0; g_gvLimboBody = 0; g_gvLimboH = 0;  /* the merc owns it now */
    if (g_gvDead) return;
    if (g_gvc.drawn) { gv_call2("item SetState(4) vt+0x25c", fState, item, 4, 0); if (g_gvDead) return; }
    /* 4. swap: the player picks the merc's old item up (DD's own pickup path) */
    if (old) {
        /* clip -1 = its own clip; reserve explicit: with -1, 0x6020d0 would read 0x8b80e0(1) while the merc still owns the
           gun (owner set later at 0x6021ec) and store 999 */
        DWORD a[3] = {(DWORD)old, (DWORD)-1, (DWORD)oRes};
        gv_call("player AddItem 0x6020d0", GV_F_PADD, P, 3, a, 0);
        if (g_gvDead) return;
        int r1 = gv_stored_res(old);
        if (oRes >= 0 && r1 != oRes && gv_vf(old, 0x308) == 0x8be2c0) {   /* belt and braces: the setter AddItem uses */
            gv_call1("item set reserve vt+0x308", 0x8be2c0, old, (DWORD)oRes);
            if (g_gvDead) return;
            gv_log("swap: reserve read back %d after AddItem - set to %d with vt+0x308 (now %d)", r1, oRes, gv_stored_res(old));
        }
        gv_log("swap: the player got the merc's old gun back: clip %d reserve %d (asked %d: %s; stored before %d, capacity %d)",
               gv_stored_clip(old), gv_stored_res(old), oRes, oResWhy, oRes0, oCap);
    }
    DWORD hNow = rd32(body + GV_SLOT0 + 4 * slot);
    BYTE *curNow = gv_cur_item(P);
    char cdesc[160]; gv_item_desc(curNow, cdesc, sizeof cdesc);
    if (old) g_gv.swaps++; else g_gv.gives++;
    if (hNow != hItem) gv_fb("Giving the %s to %s did not take", gv_gun_name(id), dn);
    else if (old) gv_fb("Swapped: %s took your %s, you got the %s", dn, gv_gun_name(id), gv_gun_name(oidUi));
    else gv_fb("Gave your %s to %s", gv_gun_name(id), dn);
    gv_log("done %s: merc=%d '%s' slot %d = %08lx (%s) item owner=%08lx%s state=%ld | player current=[%s]", old ? "swap" : "give", merc, nm, slot,
           hNow, hNow == hItem ? "the given item: WeaponFilter bool 0 will pass" : "NOT the given item", rd32(item + 0x5c),
           rd32(item + 0x5c) == hBody ? " (merc)" : "", (long)rd32(item + 0x50), cdesc);
    if (old || g_gvc.ackAlways) gv_speak(body, g_gvc.ack, old ? "swap ack" : "give ack");
    if (g_gvDead) return;
    if (g_gvc.event) {
        DWORD a[2] = {(DWORD)P, (DWORD)g_gvc.event};
        int any = readable((void*)(0x168a668 + g_gvc.event), 1) ? *(BYTE*)(0x168a668 + g_gvc.event) : -1;
        gv_call("PlayerMonitor dispatch 0x589600", GV_F_PMON, 0, 2, a, 1);
        if (!g_gvDead) gv_log("PlayerMonitor event %d raised (monitors registered for it: %s)", g_gvc.event, any > 0 ? "yes" : any == 0 ? "none" : "?");
    }
    g_gv.lastGive = GetTickCount();
}

/* ---------- input ---------- */
static void gv_find_kb(void) {
    BYTE *sys = (BYTE*)rd32((void*)0xddb958);
    g_gv.kb = 0; g_gv.sys = sys;
    if (!sq_rd(sys, 0x94)) return;
    int n = (int)*(DWORD*)(sys + 0x90); if (n < 0 || n > 16) return;
    for (int i = 0; i < n; i++) { BYTE *dv = (BYTE*)rd32(sys + 4 + 4 * i); if (sq_rd(dv, 0x34) && *(DWORD*)dv == SQ_KB_VT) { g_gv.kb = dv; return; } }
}
static int gv_key_down(void) {
    if (!g_gvc.key) return 0;
    if (!g_gv.kb || rd32(g_gv.kb) != SQ_KB_VT || g_gv.sys != (BYTE*)rd32((void*)0xddb958)) gv_find_kb();
    if (g_gv.kb) return sq_dev_down(g_gv.kb, g_gvc.key);
    UINT vk = MapVirtualKeyA(g_gvc.key, 3);
    return vk && (GetAsyncKeyState(vk) & 0x8000);
}

/* ---------- ANP_give_cmd.txt ---------- */
static void gv_cmd_poll(void) {
    DWORD now = GetTickCount();
    if (now - g_gv.cmdPoll < 250) return;
    g_gv.cmdPoll = now;
    char fn[MAX_PATH], dn[MAX_PATH];
    _snprintf(fn, sizeof fn, "%s\\ANP_give_cmd.txt", g_dir); _snprintf(dn, sizeof dn, "%s\\ANP_give_cmd.done", g_dir);
    if (GetFileAttributesA(fn) == INVALID_FILE_ATTRIBUTES) return;
    char buf[1024] = ""; FILE *f = fopen(fn, "r");
    if (!f) return;
    size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
    if (!n) return;
    if (!MoveFileExA(fn, dn, MOVEFILE_REPLACE_EXISTING) && !DeleteFileA(fn)) { gv_log("cmd: cannot consume ANP_give_cmd.txt (error %lu)", GetLastError()); return; }
    int added = 0;
    for (char *l = strtok(buf, "\r\n"); l; l = strtok(NULL, "\r\n")) {
        while (*l == ' ' || *l == '\t') l++;
        if (!*l || *l == '#') continue;
        if (g_gvQn >= 16) { gv_log("cmd queue full, '%s' dropped", l); continue; }
        _snprintf(g_gvQ[(g_gvQh + g_gvQn) % 16], 96, "%s", l); g_gvQ[(g_gvQh + g_gvQn) % 16][95] = 0; g_gvQn++; added++;
    }
    gv_log("cmd file: %d command(s) queued", added);
}
static void gv_cmd_exec(const char *line, BYTE *P, int T) {
    char b[96]; _snprintf(b, sizeof b, "%s", line); b[95] = 0;
    char *tok[4]; int nt = 0;
    for (char *t = strtok(b, " \t"); t && nt < 4; t = strtok(NULL, " \t")) tok[nt++] = t;
    if (!nt) return;
    gv_log("cmd '%s'", line);
    if (!_stricmp(tok[0], "state")) { gv_state(P, "cmd"); return; }
    if (_stricmp(tok[0], "give")) { gv_log("cmd '%s' unknown (give [selected|aim|nearest|node N], state, wait S)", tok[0]); return; }
    int kind = g_gvc.target; long node = -1;
    if (nt > 1) {
        if (!_stricmp(tok[1], "selected")) kind = GVT_SELECTED;
        else if (!_stricmp(tok[1], "aim")) kind = GVT_AIM;
        else if (!_stricmp(tok[1], "nearest")) kind = GVT_NEAREST;
        else if (!_stricmp(tok[1], "node") && nt > 2) { kind = GVT_NODE; node = atol(tok[2]); }
        else { gv_log("cmd '%s': bad target", line); return; }
    }
    gv_give(P, kind, node, T, 0, "cmd");
}

/* ---------- per-frame tick ---------- */
static int give_tick_body(void *unused) {
    (void)unused;
    sq_rd_reset();
    gv_cfg_poll();
    if (g_gvc.mode == GV_OFF) return 0;
    if (g_gvBuild < 0) { g_gvBuild = gv_check_build(); anp_log("give: kl2 build check %s", g_gvBuild ? "ok" : "FAILED (dry only)"); }
    char scene[8];
    EnterCriticalSection(&g_cmpCs); memcpy(scene, g_cscene, sizeof scene); LeaveCriticalSection(&g_cmpCs);
    scene[sizeof scene - 1] = 0;
    BYTE *P = sq_player();
    int T = cl_curT();
    if (P != g_gv.P || strcmp(scene, g_gv.scene) || T < g_gv.lastT) {   /* new player / scene / restart */
        memset(&g_gv, 0, sizeof g_gv); g_gv.P = P; memcpy(g_gv.scene, scene, sizeof scene); g_gv.lastT = T; g_gv.t0 = GetTickCount();
        g_gv.keyDown = 1;                             /* no edge from a key held through the load */
        g_gvQn = 0; g_gvFbUntil = 0; g_gvCand[0] = 0; g_gvCandT = 0;
        if (P && gv_anp_level()) gv_log("level %s: player %p mode %s key %02x target %s", scene, P, GV_MODE[g_gvc.mode], g_gvc.key, GV_TGT[g_gvc.target]);
    }
    if (!P || !gv_anp_level()) return 0;
    if (T == g_gv.lastT) return 0;                    /* paused */
    g_gv.lastT = T;
    int st = sq_hud_state(P);
    if (st >= 2 && st <= 13 && st != 10) { g_gv.hudT = T; g_gv.hudSeen = 1; }
    if (!g_gv.probed && GetTickCount() - g_gv.t0 >= 4000) { g_gv.probed = 1; gv_state(P, "level start"); if (g_gvDead) return 0; }
    int fg = sq_foreground(), down = fg && gv_key_down();
    if (down && !g_gv.keyDown) {
        gv_log("key %02x pressed", g_gvc.key);
        if (GetTickCount() - g_gv.lastGive < 750) gv_log("key give ignored (0.75 s after the last give)");
        else gv_give(P, g_gvc.target, -1, T, 1, "key");
    }
    g_gv.keyDown = down;
    if (g_gvDead) return 0;
    gv_ui_tick(P, T);
    if (g_gvDead) return 0;
    gv_cmd_poll();
    DWORD now = GetTickCount();
    if (g_gvQn && now >= g_gv.waitUntil) {
        char line[96]; memcpy(line, g_gvQ[g_gvQh], sizeof line); g_gvQh = (g_gvQh + 1) % 16; g_gvQn--;
        if (!_strnicmp(line, "wait", 4) && (line[4] == ' ' || line[4] == '\t' || !line[4])) {
            float sec = (float)atof(line + 4); if (sec < 0) sec = 0; if (sec > 120) sec = 120;
            g_gv.waitUntil = now + (DWORD)(sec * 1000.0f);
            gv_log("cmd 'wait %.1f'", (double)sec);
        } else gv_cmd_exec(line, P, T);
    }
    return 0;
}
static void give_frame(void) {
    if (g_gvDead || !g_clMainTid || GetCurrentThreadId() != g_clMainTid) return;
    if (climb_guarded("give tick", give_tick_body, 0) < 0) {
        gv_kill("tick", "fault (see 'climb: FAULT ... in give tick' above)");
        gv_giveback("a fault");                       /* only when the fault hit between RemoveItem and SetOwner */
    }
}
