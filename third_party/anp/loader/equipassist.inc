/* ==================== equipassist.inc: Dead Men's mini-cutscene 'equip' for the player, in Dog Days ====================
   Included by anp_loader.c after rappel.inc (uses anp_log, readable, g_dir, g_cscene/g_cmpCs, climb.inc's climb_guarded,
   g_clMainTid, cl_curT, and squad.inc's sq_call_raw / g_sqEspDelta, sq_rd, sq_rd_reset, rd32, rd8, sq_code). Ticked once
   per gameplay frame from climb.inc's frame hook (main thread), next to give_frame().

   CEG: no kl2 code byte is changed. Reads, plus calls into kl2's own functions (their writes are the engine's own). Every
   engine call runs inside climb_guarded() and through sq_call_raw(), which checks esp afterwards; a fault or a stack
   mismatch disables the module for the session ("equip: DISABLED").

   ---- Why (static RE, 13 Oct) ----
   Both games parse 'equip (pullwpn)(ammo)(item)' into a ZMiniEquipTask (DD parser 0x502090, vt 0xbce86c; DM 0x6ff730,
   vt 0x98b350; same layout: +4 invalid, +5 executed, +8 index, +0xc section id, +0x10 ZMiniCutscene, +0x28 ammo,
   +0x2c pullwpn, +0x30 the item, created from the template at PARSE time). The only keys are item/ammo/pullwpn.
   Execute = vt slot 4; slot 6 (0x5da310) clears +5 when the cutscene resets.
   DM 0x6fb920, player section: type = item type; old = the inventory's first item of that TYPE (0x6107a0/0x610780);
     same id -> top up ammo; else, if old exists -> player vt+0x4c8(old, 1, 0) = DropItem (0x5f6df0: unequip if current,
     place it in the world in front of the player, inventory remove), then AddItem 0x5f8600(item, clip, reserve).
     => DM REPLACES the same-type gun (the old one lands on the ground) and always adds grenades/special items.
   DD 0x7cd310, player section (SPlayerTrack vt 0xbce01c, id -2, vt+0x34 = 1): same id -> top up ammo; else if
     0x73c470(inv, 2) + 0x73c470(inv, 1) > 1 (the player carries any two guns) -> NOTHING (silent, whatever the new item's
     type, grenades included); else player vt+0x684(item, 0, 1, 0), SetOwner, ammo, pullwpn select (0x8af180(id, 0, 1)).
     DD's NPC branch (actor sections) does replace: actor vt+0x4bc(old, 1, 0) + 0x501f30.
   DD's ZFFPlayer vt+0x4bc = 0x89b4d0 is DM's DropItem 0x5f6df0 ported line for line (also reached through the vt+0x40c
   thunk 0x5504a0). So DM's rule is rebuilt here from DD's own pieces:
     PRE  (cutscene start, MC+8 becomes 2): if the player holds an item of the equip item's type (two-/one-handed) with a
          different id, DropItem it now -> DD's own equip then adds the new gun at its own time (count <= 1).
     POST (task +5 goes 0 -> 1): if the item is neither in the inventory (0x417bc0) nor owned by the player (the deferred
          vt+0x684 path sets the owner first), DD refused it: DropItem the same-type gun if PRE did not, then
            a gun (type 1/2) and still two guns carried (no same-type gun, e.g. P90 + a picked-up Spas at 021's Taurus):
                 drop the gun in hand if it is a gun, else the first gun of the other type (DD carries two guns at most);
            count <= 1: re-run DD's own equip 0x7cd310(task, player track) (ammo, owner, pullwpn as DD does it);
            else, only for a grenade/special item (type 0/3) with two guns: AddItem 0x6020d0(item, clip, reserve) as DM's
                 0x5f8600 does (clip = min(capacity, ammo), reserve = the rest, as 0x7cd310 computes them); no pullwpn.
          If DD accepted it but another item of that type is still there (no PRE), that one is dropped (DM replaces) -
          once the new item is in the inventory: with a gun in hand DD's vt+0x684 (0x6cc1d0) defers the add (P+0xd82/d83
          args, P+0xd84 = the item, holster 0x4295f0; the holster-done callback 0x5d93f2 clears P+0xd84 and calls
          vt+0x684(item, a2, a3, 1)), and dropping the gun DD is still holstering is not what DD expects.
          PRE/accepted: when PRE dropped the gun that was in hand and pullwpn is 0, the new gun is selected (select=1).
   Drop = kl2 0x47f950(old, 0, 0) (thiscall, ret 0xc; args 2/3 unused): vt+0x4bc DropItem(old, 1, 0) + the dropped-weapon
   manager 0x6853e0([0x168e96c], old) + P+0x260..0x268 zeroed - the path DD's own pickup swap (0x6cc518 in vt+0x684), the
   use-pickup (0x8af34c) and 0x430975 take. Raw vt+0x4bc only when [0x168e96c] is unreadable.
   M02 (only Dead Men level with player equips: 010 Remington, 020 P90, 021 Taurus, 022 USP, 023/024 tear gas) then
   ends the gun chain with P90 + USP, Lynch holding what the player gave him, grenades added at 023.

   Finding the tasks: one heap scan per level (listed levels only) for vptr 0xbce86c, copied through ReadProcessMemory in
   64 KB chunks, `scanmb` MB per frame. A hit counts only when +0xc = -2, +0x10 is a ZMiniCutscene (vt 0xbce05c) whose
   section list [MC+0x20, MC+0x24) holds an SPlayerTrack (vt 0xbce01c, id -2) whose task vector [+0xc, +0x10) holds it,
   and +0x30 is a ZFFItemWeapon (vt 0xbc042c).

   unlockplayer/lockplayer (weaponhdl UnholsterPrim/UnholsterSec) after an equip (wpnhdl=1, static RE 14 Oct):
     both games parse weaponhdl the same (0 NotSet, 1 Holster, 2 Unholster, 3 UnholsterPrim, 4 UnholsterSec), but DM's
     handler 0x6f5d80 selects by TYPE (0x5f8d80: Prim = the first two-handed gun, Sec = the first one-handed gun) while
     DD's 0x4d5c20 (called by ZMiniPlayerUnlockTask::Execute 0x5149c0, vt 0xbce83c, weaponhdl at +0x24, cache at
     SPlayerTrack+0x24) selects by inventory SLOT ORDER (0x566f20(1) = the first gun of any type, 0x566f20(0) = the
     second). M02 021 (Taurus, then unlock UnholsterSec) therefore ended with the P90 in hand. With wpnhdl=1 the first
     unlockplayer after a player equip (same section, weaponhdl 3/4) gets +0x24 = 0 while its cutscene runs (DD's
     Execute then skips 0x4d5c20 at 0x5149d3), +0x24 is put back once it ran, and DM's rule is applied instead: the
     track cache is honoured (same value -> nothing, as both games), else cache = weaponhdl; then, only if a gun of the
     wanted type is carried, unholster 0x5e7c60(0, 0x100) (as 0x4d5c20 does) and select 0x8af180(id, 0, 1) the first gun
     of that type, retried every 0.5 s for 4 s (0x8af180 refuses during some actions/movements). No gun of that type but
     its add on the way (this equip's deferred add, or DD's deferred add slot P+0xd84 holding one): the 4 s window waits
     for it, then unholster + select. Heap writes on the cutscene's own task + kl2 calls only. Muted +0x24 is given back
     (ownership-checked: unlock vt, +0x10 = its cutscene, cutscene vt) on a cutscene reset, a restart, mode off, or
     wpnhdl / live switched off before the unlock ran; scene change: tasks forgotten with no write; same-scene player change: unmuted (ownership-checked) first.
     The unlock task / unholster code has its own build check (g_eaHdlOk): a mismatch logs 'wpnhdl off' and leaves
     Dog Days' own weaponhdl; the equip rule itself stays on.

   Config <DD>\ANP_equip.txt (polled once a second). NO FILE = live levels=M02 (release default, 14 Oct; it only acts
   in the levels listed, and only M02 has player equips). A file without a mode word is live too; an unknown mode word = dry (never undoes an explicit off);
   an unreadable file keeps the previous config and is retried. levels= only ever matches ANP levels (M<digit>...).
     off | dry | live       dry: scan, watch and log what would be done; live: do it
     levels=M02             comma list of scene ids, or all
     wpnhdl=1               1: Dead Men's weaponhdl UnholsterPrim/Sec after an equip (by type, see above); 0: DD's own
     pre=1                  1: drop the same-type gun when the cutscene starts (DD's equip then adds natively); 0: POST only
     post=1                 1: repair a refused equip after it ran; 0: off
     select=1               select the new gun when the gun dropped for it (at the cutscene start or after a refusal) was
                            in the player's hands (pullwpn 0 case)
     scanmb=24              MB of heap copied per frame by the scan (4..256)
   Log lines start with "equip:". */

#define EA_EQUIP_VT    0xbce86c   /* ZMiniEquipTask@CPPScript */
#define EA_MC_VT       0xbce05c   /* ZMiniCutscene@CPPScript */
#define EA_PTRACK_VT   0xbce01c   /* SPlayerTrack@CPPScript */
#define EA_PLAYER_VT   0xbb45f4   /* ZFFPlayer */
#define EA_WEAPON_VT   0xbc042c   /* ZFFItemWeapon */
#define EA_F_EQUIP     0x7cd310   /* ZMiniEquipTask::Execute(track) ret 4 */
#define EA_F_DROP      0x89b4d0   /* ZFFPlayer vt+0x4bc DropItem(item, 1, 0) ret 0xc */
#define EA_F_DROPSWAP  0x47f950   /* ZFFPlayer drop for a swap (item, clip, reserve) ret 0xc: vt+0x4bc + 0x6853e0 + P+0x260 = 0 */
#define EA_F_PREMOVE   0x633250   /* ZFFPlayer::RemoveItem(item) ret 4 (give.inc step 1) */
#define EA_F_DROPMGR   0x6853e0   /* dropped-weapon manager (this = [0x168e96c]) register(item) ret 4 */
#define EA_DROPMGR     0x168e96c
#define EA_F_PADD      0x6020d0   /* ZFFPlayer::AddItem(item, clip, reserve) ret 0xc */
#define EA_F_ITEMID    0x47ded0   /* registry.ItemId(item) ret 4 */
#define EA_F_ITEMTYPE  0x539e30   /* registry.ItemType(item) ret 4 */
#define EA_F_INVFIND   0x417bc0   /* inventory.Find(id) -> item ret 4 */
#define EA_F_INVCOUNT  0x73c470   /* inventory.CountType(type) -> al ret 4 */
#define EA_F_SELECT    0x8af180   /* ZFFPlayer select(id, 0, 1) ret 0xc */
#define EA_F_OBJH      0x6ece90   /* object -> handle */
#define EA_F_CURITEM   0x727b40   /* ZFFPlayer current item */
#define EA_MAXT        64
#define EA_UNLOCK_VT   0xbce83c   /* ZMiniPlayerUnlockTask@CPPScript: +5 executed, +0x10 MC, +0x24 weaponhdl (ctor 0x64ecd0, Execute 0x5149c0) */
#define EA_F_HOLSTER   0x5e7c60   /* ZFFPlayer holster request (flag, mask) ret 8; (0, 0x100) = unholster, as 0x4d5c20 */
#define EA_WSEL_MS     4000       /* wpnhdl: how long the select by type is retried */

enum { EA_OFF, EA_DRY, EA_LIVE };
static const char *const EA_MODE[] = {"off", "dry", "live"};
typedef struct { int mode, pre, post, select, scanmb, remove, wpnhdl; char levels[128]; } EaCfg;
#define EA_CFG_DEFAULT {EA_LIVE, 1, 1, 1, 24, 1, 1, "M02"}   /* release default (14 Oct): live, M02 only */
/* remove=1 (default, W's M02 test 13 Oct): the replaced gun leaves the inventory (ZFFPlayer::RemoveItem 0x633250) instead
   of DM's world drop - DD gives a dropped gun a world pickup prompt that beats the level's own pickup prompts
   (M02 trunk: the USP prompt never showed). drop=world gives the DM drop (0x47f950). */
static EaCfg g_eac = EA_CFG_DEFAULT;
static int g_eacPresent = -1; static FILETIME g_eacTime; static DWORD g_eacPoll;
static int g_eacGen;                                  /* bumped on every applied config: the tick re-evaluates levels= */
static int g_eaDead, g_eaBuild = -1, g_eaHdlOk = -1, g_eaLines;   /* g_eaHdlOk: ea_check_hdl (wpnhdl only) */
typedef struct {
    BYTE *task, *mc, *track; int ex, st, preDone, dropped, pend; DWORD pendT0; char name[48];
    BYTE *unl; int hdl, unlEx, muted, wsel, wselUnh; DWORD wselT0, wselNext;   /* wpnhdl: the unlockplayer after this equip */
} EaTask;
#define EA_PEND_MS 15000   /* POST: how long to wait for DD's deferred add (holster first) before giving up */
static struct {
    BYTE *P; char scene[8]; int lastT, listed, cfgGen; DWORD t0, scanAt, scan, scanStart; int scanState, scans; /* 0 wait, 1 run, 2 done */
    EaTask t[EA_MAXT]; int n;
} g_ea;

/* ---------- logging, calls ---------- */
static void ea_log(const char *fmt, ...) {
    if (g_eaLines > 3000) return;
    if (++g_eaLines == 3000) { anp_log("equip: log line cap reached, equip logging stops"); return; }
    char b[1200]; va_list ap; va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    anp_log("equip: %s", b);
}
/* wpnhdl on: configured, and the unlock task / unholster code checked (g_eaHdlOk, separate from the equip rule) */
static int ea_wpnhdl(void) { return g_eac.wpnhdl && g_eaHdlOk == 1; }
/* the unlock is still this task's: its vptr, its cutscene (+0x10 == e->mc) and that cutscene alive. Only ever used on
   tasks of the CURRENT scene: a scene change forgets the list with no write; a same-scene player change unmutes first */
static int ea_unl_owned(const EaTask *e) {
    return e->unl && rd32(e->unl) == EA_UNLOCK_VT && (BYTE*)rd32(e->unl + 0x10) == e->mc && rd32(e->mc) == EA_MC_VT;
}
static void ea_hdl_unmute(EaTask *e) {                /* put DD's value back (cutscene replays, restarts, config change) */
    if (!e->muted) return;
    e->muted = 0;
    if (ea_unl_owned(e) && rd32(e->unl + 0x24) == 0 && god_writable(e->unl + 0x24, 4)) *(DWORD*)(e->unl + 0x24) = e->hdl;
}
static void ea_kill(const char *where, const char *why) {
    if (!g_eaDead) anp_log("equip: DISABLED for this session (%s in %s) - restart the game before testing again", why, where);
    g_eaDead = 1;
    for (int i = 0; i < g_ea.n; i++) {               /* wpnhdl: give DD its own weaponhdl back on any muted unlock (ownership-checked) */
        EaTask *e = &g_ea.t[i];
        ea_hdl_unmute(e);
        e->wsel = 0; e->wselUnh = 0;
    }
}
/* give DD back every muted unlock of the CURRENT task list (ownership-checked), stop selecting */
static void ea_unmute_all(const char *why) {
    for (int i = 0; i < g_ea.n; i++) {
        EaTask *e = &g_ea.t[i];
        if (e->muted) ea_log("'%s': %s - unlockplayer weaponhdl %d given back to Dog Days", e->name, why, e->hdl);
        ea_hdl_unmute(e); e->wsel = 0; e->wselUnh = 0;
    }
}
static DWORD ea_call(const char *what, DWORD fn, void *self, int n, const DWORD *a) {
    if (g_eaDead) return 0;
    g_sqEspDelta = 0;
    DWORD r = sq_call_raw(fn, self, n, a, 0);
    if (g_sqEspDelta) { anp_log("equip: esp mismatch after %s (fn %08lx, delta %d)", what, fn, g_sqEspDelta); ea_kill(what, "stack mismatch"); }
    return r;
}
static DWORD ea_call1(const char *w, DWORD fn, void *self, DWORD a0) { DWORD a[1] = {a0}; return ea_call(w, fn, self, 1, a); }
static DWORD ea_call3(const char *w, DWORD fn, void *self, DWORD a0, DWORD a1, DWORD a2) { DWORD a[3] = {a0, a1, a2}; return ea_call(w, fn, self, 3, a); }

static int ea_check_build(void) {
    static const struct { DWORD a; BYTE b[8]; } t[] = {
        {EA_F_EQUIP,    {0x55, 0x8b, 0xec, 0x83, 0xec, 0x18, 0x56, 0x8b}}, {EA_F_DROP,     {0x83, 0xec, 0x54, 0x55, 0x8b, 0x6c, 0x24, 0x5c}},
        {EA_F_PADD,     {0x83, 0xec, 0x08, 0x56, 0x57, 0x8b, 0xf9, 0xeb}}, {EA_F_ITEMID,   {0x8b, 0x44, 0x24, 0x04, 0x85, 0xc0, 0x75, 0x08}},
        {EA_F_ITEMTYPE, {0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xb0, 0xc4}}, {EA_F_INVFIND,  {0x8b, 0x44, 0x24, 0x04, 0x50, 0x83, 0xc1, 0x04}},
        {EA_F_INVCOUNT, {0x53, 0x8b, 0x59, 0x0c, 0x56, 0x32, 0xc0, 0x33}}, {EA_F_SELECT,   {0x83, 0xec, 0x3c, 0x56, 0x8b, 0xf1, 0x8b, 0x06}},
        {EA_F_OBJH,     {0x51, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00, 0x00}}, {EA_F_CURITEM,  {0x56, 0x8b, 0xf1, 0x8b, 0x06, 0x8b, 0x00, 0x00}},
        {EA_F_DROPSWAP, {0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x8b, 0xf1}}, {EA_F_DROPMGR,  {0x83, 0xec, 0x0c, 0x56, 0x57, 0x8b, 0x7c, 0x24}},
        {EA_F_PREMOVE,  {0x53, 0x8b, 0x5c, 0x24, 0x08, 0x56, 0x8b, 0xf1}},
    };
    for (unsigned i = 0; i < sizeof t / sizeof t[0]; i++) {
        int len = (t[i].a == EA_F_OBJH || t[i].a == EA_F_CURITEM) ? 6 : 8;
        if (!readable((void*)t[i].a, len) || memcmp((void*)t[i].a, t[i].b, len)) { anp_log("equip: kl2 build mismatch at %08lx - equip stays dry", t[i].a); return 0; }
    }
    if (rd32((void*)(EA_EQUIP_VT + 0x10)) != EA_F_EQUIP || rd32((void*)(EA_PLAYER_VT + 0x4bc)) != EA_F_DROP ||
        rd32((void*)(EA_PTRACK_VT + 0x34)) != 0x9a00e0 || rd32((void*)(EA_WEAPON_VT + 0x2c8)) != 0x82c200) {
        anp_log("equip: kl2 vtable mismatch - equip stays dry"); return 0;
    }
    /* 0x47f950 body: mov eax,[esi]; mov edx,[eax+0x4bc]; push 0; push 1; push edi; call edx; mov ecx,[0x168e96c]; push edi; call 0x6853e0 */
    if (!readable((void*)0x47f95c, 0x1b) || memcmp((void*)0x47f95c, "\x8b\x06\x8b\x90\xbc\x04\x00\x00\x6a\x00\x6a\x01\x57\xff\xd2\x8b\x0d\x6c\xe9\x68\x01\x57\xe8", 23) ||
        (DWORD)(0x47f977 + *(int*)0x47f973) != EA_F_DROPMGR) {
        anp_log("equip: kl2 0x47f950 body differs - equip stays dry"); return 0;
    }
    return 1;
}
/* wpnhdl only (its own flag g_eaHdlOk: a mismatch here switches wpnhdl off, not the equip rule).
   ZMiniPlayerUnlockTask::Execute = mov eax,[esi+0x24]; push edi; mov edi,[ebp+8]; mov ebx,[edi+0x20];
   test eax,eax; je +8; push eax; mov ecx,edi; call 0x4d5c20 (the weaponhdl handler, skipped when +0x24 = 0);
   the unholster request 0x5e7c60 is used by wpnhdl only */
static int ea_check_hdl(void) {
    if (!readable((void*)EA_F_HOLSTER, 8) || memcmp((void*)EA_F_HOLSTER, "\x83\xec\x30\x80\x7c\x24\x34\x00", 8)) {
        anp_log("equip: kl2 build mismatch at %08x (unholster) - wpnhdl off", EA_F_HOLSTER); return 0;
    }
    if (rd32((void*)(EA_UNLOCK_VT + 0x10)) != 0x5149c0 || !readable((void*)0x5149c7, 0x16) ||
        memcmp((void*)0x5149c7, "\x8b\x46\x24\x57\x8b\x7d\x08\x8b\x5f\x20\x85\xc0\x74\x08\x50\x8b\xcf\xe8", 18) ||
        (DWORD)(0x5149dd + *(int*)0x5149d9) != 0x4d5c20) {
        anp_log("equip: kl2 unlock task differs - wpnhdl off (the equip rule itself stays on)"); return 0;
    }
    return 1;
}

/* ---------- config ---------- */
static void ea_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_eacPresent >= 0 && now - g_eacPoll < 1000) return;
    g_eacPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_equip.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_eacPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_eacTime) == 0)) return;
    g_eacPresent = present;
    if (present) g_eacTime = fa.ftLastWriteTime;
    EaCfg c = EA_CFG_DEFAULT;                         /* no file / no mode word: live levels=M02 (release default) */
    if (present) {
        char buf[1024] = "";
        static int unreadLogged;
        FILE *f = fopen(fn, "r");
        if (!f) {                                     /* held by an editor / the helper: keep the previous config, retry next poll */
            memset(&g_eacTime, 0, sizeof g_eacTime);
            if (!unreadLogged) { unreadLogged = 1; anp_log("equip: ANP_equip.txt unreadable - previous config kept, retry"); }
            return;
        }
        unreadLogged = 0;
        size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
        for (char *p = buf; (p = strchr(p, '#')); ) while (*p && *p != '\n') *p++ = ' ';
        int known = 0;                                /* an explicit known mode word was seen */
        for (char *t = strtok(buf, " \t\r\n;"); t; t = strtok(NULL, " \t\r\n;")) {
            char *eq = strchr(t, '='); const char *k = t, *v = "";
            if (eq) { *eq = 0; v = eq + 1; } else { v = t; k = "mode"; }
            if (!_stricmp(k, "mode")) {
                int m = -1; for (int i = 0; i < 3; i++) if (!_stricmp(v, EA_MODE[i])) m = i;
                if (m < 0) { c.mode = (known && c.mode == EA_OFF) ? EA_OFF : EA_DRY; anp_log("equip: config mode '%s' unknown (unknown mode word: %s)", v, c.mode == EA_OFF ? "off kept" : "dry"); }
                else { c.mode = m; known = 1; }
            }
            else if (!_stricmp(k, "levels")) { _snprintf(c.levels, sizeof c.levels, "%s", v); c.levels[sizeof c.levels - 1] = 0; }
            else if (!_stricmp(k, "pre")) c.pre = atoi(v) != 0;
            else if (!_stricmp(k, "post")) c.post = atoi(v) != 0;
            else if (!_stricmp(k, "select")) c.select = atoi(v) != 0;
            else if (!_stricmp(k, "scanmb")) { int m = atoi(v); c.scanmb = m < 4 ? 4 : m > 256 ? 256 : m; }
            else if (!_stricmp(k, "drop")) c.remove = _stricmp(v, "world") != 0;
            else if (!_stricmp(k, "wpnhdl")) c.wpnhdl = atoi(v) != 0;
            else anp_log("equip: config key '%s' unknown", k);
        }
    }
    g_eac = c; g_eacGen++;
    anp_log("equip: config mode=%s levels=%s pre=%d post=%d select=%d scanmb=%d drop=%s wpnhdl=%d%s", EA_MODE[c.mode], c.levels, c.pre, c.post,
            c.select, c.scanmb, c.remove ? "remove" : "world", c.wpnhdl, present ? "" : " (no ANP_equip.txt: live levels=M02)");
}
static int ea_level_listed(const char *scene) {
    if (!(scene[0] == 'M' && scene[1] >= '0' && scene[1] <= '9')) return 0;   /* ANP levels only, whatever levels= names */
    if (!_stricmp(g_eac.levels, "all")) return 1;
    char b[128]; _snprintf(b, sizeof b, "%s", g_eac.levels); b[sizeof b - 1] = 0;
    for (char *t = strtok(b, ","); t; t = strtok(NULL, ",")) if (!_stricmp(t, scene)) return 1;
    return 0;
}

/* ---------- objects ---------- */
static BYTE *ea_player(void) {
    BYTE *gm = (BYTE*)rd32((void*)0xdd265c);
    if (!sq_rd(gm + 0x828, 0x74)) return 0;
    signed char pi = *(signed char*)(gm + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gm + 0x828 + 4 * pi);
    return (sq_rd(P, 0x2e00) && *(DWORD*)P == EA_PLAYER_VT) ? P : 0;
}
static BYTE *ea_reg(void) { BYTE *gm = (BYTE*)rd32((void*)0xdd265c); BYTE *r = (BYTE*)rd32(gm + 0x15b0); return sq_rd(r, 0x100) ? r : 0; }
static BYTE *ea_inv(BYTE *P) { BYTE *inv = (BYTE*)rd32(P + 0xcec); return sq_rd(inv, 0x10) ? inv : 0; }
static int ea_is_item(BYTE *it) { return sq_rd(it, 0x150) && *(DWORD*)it == EA_WEAPON_VT && sq_rd((BYTE*)rd32(it + 0xc4), 0xb0); }
static int ea_item_id(BYTE *it) { BYTE *r = ea_reg(); return (r && ea_is_item(it)) ? (int)ea_call1("item id", EA_F_ITEMID, r, (DWORD)it) : -1; }
static int ea_item_type(BYTE *it) { BYTE *r = ea_reg(); return (r && ea_is_item(it)) ? (int)ea_call1("item type", EA_F_ITEMTYPE, r, (DWORD)it) : -1; }
static void ea_tname(BYTE *it, char *out, int n) {
    out[0] = 0;
    BYTE *t = (BYTE*)rd32(it + 0xc4), *node = t ? (BYTE*)rd32(t + 4) : 0; const char *p = (const char*)rd32(node + 0x6c);
    if (!sq_rd(p, 1)) { _snprintf(out, n, "?"); out[n - 1] = 0; return; }
    int k = 0; while (k < n - 1 && sq_rd(p + k, 1) && p[k] >= 32 && p[k] < 127) { out[k] = p[k]; k++; }
    out[k] = 0;
}
static BYTE *ea_inv_find(BYTE *P, int id) { BYTE *inv = ea_inv(P); return inv ? (BYTE*)ea_call1("inventory find", EA_F_INVFIND, inv, (DWORD)id) : 0; }
static int ea_guns(BYTE *P) {                         /* exactly DD's equip test: CountType(2) + CountType(1) */
    BYTE *inv = ea_inv(P); if (!inv) return -1;
    int a = (int)(ea_call1("count one-handed", EA_F_INVCOUNT, inv, 2) & 0xff);
    int b = (int)(ea_call1("count two-handed", EA_F_INVCOUNT, inv, 1) & 0xff);
    return a + b;
}
/* the first inventory item of that type whose id differs (DM 0x6107a0 takes the first of the type), or 0 */
static BYTE *ea_same_type(BYTE *P, int type, int id, BYTE *except) {
    BYTE *inv = ea_inv(P); if (!inv) return 0;
    BYTE *ent = (BYTE*)rd32(inv + 8); int cnt = (int)rd32(inv + 0xc), srch = rd8(inv + 4);
    int n = srch ? cnt : 0x41;                        /* as grenade.inc's census reads it (proven in game) */
    if (n < 0 || n > 0x41 || !sq_rd(ent, 16 * n)) return 0;
    for (int i = 0; i < n && !g_eaDead; i++) {
        BYTE *it = (BYTE*)rd32(ent + 16 * i + 8);
        if (!it || it == except || !ea_is_item(it)) continue;
        if (ea_item_type(it) == type && ea_item_id(it) != id) return it;
    }
    return 0;
}
static BYTE *ea_cur_item(BYTE *P) {                   /* 0x727b40: vt+0x4cc (right hand) else vt+0x4c8, as DropItem uses it */
    BYTE *r = (BYTE*)ea_call("current item", EA_F_CURITEM, P, 0, NULL);
    return (!g_eaDead && ea_is_item(r)) ? r : 0;
}

/* ---------- heap scan for the player equip tasks of this scene ---------- */
static BYTE *ea_track_of(BYTE *task, BYTE *mc) {
    BYTE *b = (BYTE*)rd32(mc + 0x20), *e = (BYTE*)rd32(mc + 0x24);
    if (!b || e < b || e - b > 4 * 64 || !sq_rd(b, e - b)) return 0;
    for (BYTE *p = b; p < e; p += 4) {
        BYTE *sec = *(BYTE**)p;
        if (!sq_rd(sec, 0x2c) || *(DWORD*)sec != EA_PTRACK_VT || *(int*)(sec + 4) != -2) continue;
        BYTE *tb = (BYTE*)rd32(sec + 0xc), *te = (BYTE*)rd32(sec + 0x10);
        if (!tb || te < tb || te - tb > 4 * 256 || !sq_rd(tb, te - tb)) continue;
        for (BYTE *q = tb; q < te; q += 4) if (*(BYTE**)q == task) return sec;
    }
    return 0;
}
static void ea_consider(BYTE *t) {
    if (g_ea.n >= EA_MAXT || !sq_rd(t, 0x34) || *(DWORD*)t != EA_EQUIP_VT || *(int*)(t + 0xc) != -2 || t[4]) return;
    BYTE *mc = (BYTE*)rd32(t + 0x10), *item = (BYTE*)rd32(t + 0x30);
    if (!sq_rd(mc, 0x58) || *(DWORD*)mc != EA_MC_VT || !ea_is_item(item)) return;
    BYTE *tr = ea_track_of(t, mc);
    if (!tr) return;
    for (int i = 0; i < g_ea.n; i++) if (g_ea.t[i].task == t) return;
    EaTask *e = &g_ea.t[g_ea.n++];
    memset(e, 0, sizeof *e); e->task = t; e->mc = mc; e->track = tr; e->ex = t[5]; e->st = (int)rd32(mc + 8);
    ea_tname(item, e->name, sizeof e->name);
    /* wpnhdl: the first unlockplayer of the same player section after this equip (before any later equip), with
       weaponhdl UnholsterPrim (3) / UnholsterSec (4) */
    BYTE *tb = (BYTE*)rd32(tr + 0xc), *te = (BYTE*)rd32(tr + 0x10); int after = 0;
    if (tb && te > tb && te - tb <= 4 * 256 && sq_rd(tb, te - tb))
        for (BYTE *q = tb; q < te; q += 4) {
            BYTE *k = *(BYTE**)q;
            if (k == t) { after = 1; continue; }
            if (!after || !sq_rd(k, 0x28)) continue;
            if (*(DWORD*)k == EA_EQUIP_VT) break;         /* a later equip owns what follows */
            if (*(DWORD*)k != EA_UNLOCK_VT || (BYTE*)rd32(k + 0x10) != mc) continue;
            int h = (int)rd32(k + 0x24);
            if (h == 3 || h == 4) { e->unl = k; e->hdl = h; e->unlEx = k[5]; }
            break;                                         /* the first unlockplayer after this equip only */
        }
}
static void ea_scan_step(void) {
    DWORD budget = (DWORD)g_eac.scanmb << 20, done = 0;
    MEMORY_BASIC_INFORMATION mi;
    static DWORD buf[0x4000];
    while (done < budget) {
        if (g_ea.scan >= 0xfffe0000u || !VirtualQuery((void*)g_ea.scan, &mi, sizeof mi)) { g_ea.scanState = 2; break; }
        DWORD rb = (DWORD)mi.BaseAddress, re = rb + (DWORD)mi.RegionSize;
        if (re <= g_ea.scan) { g_ea.scanState = 2; break; }
        if (mi.State == MEM_COMMIT && mi.Type == MEM_PRIVATE && (mi.Protect & 0xff) == PAGE_READWRITE && !(mi.Protect & PAGE_GUARD)) {
            DWORD a = (g_ea.scan + 3) & ~3u, e = re;
            if (e - a > budget - done) e = a + (budget - done);
            for (DWORD c = a; c < e; c += sizeof buf) {
                SIZE_T n = e - c < sizeof buf ? e - c : sizeof buf, got = 0;
                if (!ReadProcessMemory(GetCurrentProcess(), (void*)c, buf, n, &got)) continue;
                for (DWORD w = 0; w < got / 4; w++) if (buf[w] == EA_EQUIP_VT) ea_consider((BYTE*)(c + 4 * w));
            }
            done += e - a; g_ea.scan = e;
        } else g_ea.scan = re;
    }
}

/* ---------- the Dead Men rule ---------- */
typedef struct { EaTask *e; BYTE *P; int phase; } EaArg;   /* phase 0 = PRE, 1 = POST, 2 = POST after DD's deferred add */
static int ea_drop(BYTE *P, BYTE *old, const char *why, const char *tn) {
    char on[48]; ea_tname(old, on, sizeof on);
    int cur = ea_cur_item(P) == old;
    if (g_eaDead) return 0;
    if (g_eac.mode != EA_LIVE) { ea_log("%s '%s': dry: would drop %s %p (id %d%s)", why, tn, on, old, ea_item_id(old), cur ? ", in hand" : ""); return 0; }
    BYTE *mgr = (BYTE*)rd32((void*)EA_DROPMGR);
    const char *how;
    if (g_eac.remove) {                               /* out of the inventory, no world pickup prompt (see EaCfg) */
        ea_call1("player RemoveItem 0x633250", EA_F_PREMOVE, P, (DWORD)old); how = "ZFFPlayer::RemoveItem 0x633250 (drop=remove: no world pickup)";
    } else if (sq_rd(mgr, 0xb8)) {                           /* DD's swap drop: DropItem + dropped-weapon manager + P+0x260 = 0 */
        ea_call3("drop 0x47f950", EA_F_DROPSWAP, P, (DWORD)old, 0, 0); how = "kl2 0x47f950 (DropItem 0x89b4d0 = DM 0x5f6df0 + dropped-weapon manager)";
    } else {
        ea_call3("DropItem", EA_F_DROP, P, (DWORD)old, 1, 0); how = "raw DropItem 0x89b4d0 (dropped-weapon manager [0x168e96c] unreadable)";
    }
    if (g_eaDead) return 0;
    ea_log("%s '%s': dropped %s %p (id %d%s) with %s", why, tn, on, old, ea_item_id(old), cur ? ", was in hand" : "", how);
    return cur ? 2 : 1;
}
/* the item still belongs to this task's player track (a restart can reuse the player and rebuild the cutscene) */
static int ea_task_ok(EaTask *e) {
    if (rd32(e->task) != EA_EQUIP_VT || (BYTE*)rd32(e->task + 0x10) != e->mc || rd32(e->mc) != EA_MC_VT || rd8(e->task + 4)) {
        ea_log("task %p '%s': no longer an equip task of MC %p - skipped", e->task, e->name, e->mc); return 0;
    }
    BYTE *tr = ea_track_of(e->task, e->mc);
    if (tr == e->track) return 1;
    if (!tr) { ea_log("task %p '%s': its player track %p is gone - skipped", e->task, e->name, e->track); return 0; }
    ea_log("task %p '%s': player track moved %p -> %p (restart) - using the new one", e->task, e->name, e->track, tr);
    e->track = tr;
    return 1;
}
/* ---------- wpnhdl: Dead Men's weaponhdl UnholsterPrim/Sec (DM 0x6f5d80: by TYPE; DD 0x4d5c20: by slot order) ---------- */
static void ea_hdl_mute(EaTask *e) {                  /* cutscene start: DD's unlock will skip its weaponhdl handling */
    if (!e->unl || e->muted || !ea_wpnhdl() || !ea_unl_owned(e) || rd8(e->unl + 5) || (int)rd32(e->unl + 0x24) != e->hdl) return;
    if (g_eac.mode != EA_LIVE) { ea_log("'%s': dry: would take over unlockplayer weaponhdl %d", e->name, e->hdl); return; }
    if (!god_writable(e->unl + 0x24, 4)) return;
    *(DWORD*)(e->unl + 0x24) = 0; e->muted = 1;
    ea_log("'%s': unlockplayer %p weaponhdl %s taken over (DD picks by slot order, DM by type)", e->name, e->unl,
           e->hdl == 3 ? "UnholsterPrim" : "UnholsterSec");
}
/* the wanted gun is on its way in: this equip's add is still deferred (e->pend: DD accepted it, vt+0x684 is holstering
   first), or DD's deferred add slot P+0xd84 (vt+0x684 / 0x6cc1d0, cleared by the holster-done callback 0x5d93f2) holds an
   item of the wanted type */
static int ea_add_pending(EaTask *e, BYTE *P, int want) {
    if (e->pend && ea_item_type((BYTE*)rd32(e->task + 0x30)) == want) return 1;
    if (g_eaDead) return 0;
    BYTE *d = (BYTE*)rd32(P + 0xd84);
    if (!ea_is_item(d)) return 0;
    int t = ea_item_type(d);
    return !g_eaDead && t == want;
}
static void ea_unholster(EaTask *e, BYTE *P) {        /* as 0x4d5c20 does before its select */
    DWORD a2[2] = {0, 0x100}; ea_call("unholster 0x5e7c60", EA_F_HOLSTER, P, 2, a2);
    if (!g_eaDead) ea_log("'%s': unholster 0x5e7c60(0, 0x100)", e->name);
}
static int ea_hdl(EaTask *e, BYTE *P, int phase) {    /* phase 3: the unlock has just run; 4: select retry */
    int want = e->hdl == 3 ? 1 : 2;
    DWORD now = GetTickCount();
    if (phase == 3) {
        int muted = e->muted; ea_hdl_unmute(e);
        e->wsel = 0; e->wselUnh = 0;
        if (!ea_wpnhdl() || g_eac.mode != EA_LIVE) return 0;
        if (muted) {
            if ((int)rd32(e->track + 0x24) == e->hdl) { ea_log("'%s': track cache already %d - Dead Men skips it too", e->name, e->hdl); return 0; }
            if (!god_writable(e->track + 0x24, 4)) return 0;
            *(DWORD*)(e->track + 0x24) = (DWORD)e->hdl;   /* the cache, as DM 0x6f5de3 / DD 0x4d5c6d write it (kept even with no gun) */
        }
        /* the type check comes before the unholster (review): with no gun of that type nothing is drawn */
        BYTE *have = ea_same_type(P, want, -1, NULL); if (g_eaDead) return 0;
        if (!have) {
            int pend = ea_add_pending(e, P, want); if (g_eaDead) return 0;
            if (!pend) { ea_log("'%s': no type-%d gun - nothing unholstered or selected (DM fails the same way)", e->name, want); return 0; }
            ea_log("'%s': type-%d gun not in the inventory yet (its add is deferred) - waiting up to %d ms", e->name, want, EA_WSEL_MS);
            e->wsel = want; e->wselT0 = now; e->wselNext = now; e->wselUnh = muted;   /* unholster once it is in */
            return 0;
        }
        if (muted) { ea_unholster(e, P); if (g_eaDead) return 0; }
        e->wsel = want; e->wselT0 = now; e->wselNext = now;
    }
    if (!e->wsel) return 0;
    if (!ea_wpnhdl() || g_eac.mode != EA_LIVE) { e->wsel = 0; e->wselUnh = 0; return 0; }
    BYTE *c = ea_cur_item(P); if (g_eaDead) return 0;
    int ct = c ? ea_item_type(c) : -1; if (g_eaDead) return 0;
    if (ct == want) {
        ea_log("'%s': type-%d gun in hand after %lu ms (Dead Men's %s)", e->name, want, now - e->wselT0, e->hdl == 3 ? "UnholsterPrim" : "UnholsterSec");
        e->wsel = 0; e->wselUnh = 0; return 0;
    }
    if (now - e->wselT0 > EA_WSEL_MS) { ea_log("'%s': gave up selecting type %d (in hand: type %d)", e->name, want, ct); e->wsel = 0; e->wselUnh = 0; return 0; }
    if ((int)(now - e->wselNext) < 0) return 0;
    e->wselNext = now + 500;
    BYTE *it = ea_same_type(P, want, -1, NULL); if (g_eaDead) return 0;
    if (!it) {                                        /* not in yet: wait while its add is still on the way (4 s window) */
        int pend = ea_add_pending(e, P, want); if (g_eaDead) return 0;
        if (!pend) { ea_log("'%s': no type-%d gun and no add on the way - select stopped", e->name, want); e->wsel = 0; e->wselUnh = 0; }
        return 0;
    }
    if (e->wselUnh) { e->wselUnh = 0; ea_unholster(e, P); if (g_eaDead) return 0; }
    int id = ea_item_id(it); if (g_eaDead || id < 0) return 0;
    DWORD r = ea_call3("select", EA_F_SELECT, P, (DWORD)id, 0, 1);
    if (!g_eaDead) ea_log("'%s': select 0x8af180(%d, 0, 1) = %d", e->name, id, (int)(r & 0xff));
    return 0;
}

static int ea_body(void *a_) {
    EaArg *a = a_; EaTask *e = a->e; BYTE *P = a->P, *t = e->task;
    if (!ea_task_ok(e)) { e->pend = 0; e->wsel = 0; e->wselUnh = 0; ea_hdl_unmute(e); return 0; }
    if (a->phase >= 3) return ea_hdl(e, P, a->phase);
    BYTE *item = (BYTE*)rd32(t + 0x30);
    if (!ea_is_item(item)) { ea_log("task %p: item %p no longer a ZFFItemWeapon - skipped", t, item); e->pend = 0; return 0; }
    int id = ea_item_id(item), type = ea_item_type(item), ammo = (int)rd32(t + 0x28), pull = rd8(t + 0x2c);
    if (g_eaDead || id < 0 || type < 0 || type > 3) { ea_log("task %p '%s': id %d type %d - skipped", t, e->name, id, type); e->pend = 0; return 0; }
    BYTE *have = ea_inv_find(P, id); if (g_eaDead) return 0;
    if (a->phase == 0) {                              /* PRE: cutscene started */
        if (have || (type != 1 && type != 2)) return 0;
        BYTE *old = ea_same_type(P, type, id, item); if (g_eaDead || !old) return 0;
        int d = ea_drop(P, old, "cutscene start", e->name);
        if (d) e->dropped = d;
        return 0;
    }
    if (a->phase == 2) {                              /* POST, later: DD's deferred add has landed (or timed out) */
        if (have != item) {
            if (GetTickCount() - e->pendT0 < EA_PEND_MS) return 0;
            e->pend = 0;
            ea_log("'%s': DD's deferred add did not land within %d s (P+0xd84 = %08lx) - the same-type gun is kept", e->name, EA_PEND_MS / 1000, rd32(P + 0xd84));
            return 0;
        }
        e->pend = 0;
        BYTE *old = ea_same_type(P, type, id, item); if (g_eaDead) return 0;
        ea_log("'%s': DD's deferred add landed (in the inventory after %lu ms)%s", e->name, GetTickCount() - e->pendT0,
               old ? " - a same-type gun is still there" : " - no same-type gun left (DD's own swap dropped it)");
        if (old && !g_eaDead) ea_drop(P, old, "after deferred equip", e->name);
        return 0;
    }
    /* POST: the task has just run */
    DWORD hP = ea_call("player handle", EA_F_OBJH, P, 0, NULL); if (g_eaDead) return 0;
    DWORD owner = rd32(item + 0x5c);
    int guns = ea_guns(P); if (g_eaDead) return 0;
    if (have == item || (hP && owner == hP)) {        /* DD added it (or its deferred vt+0x684 add is pending) */
        /* only when PRE did not already drop one: DM replaces the FIRST same-type gun only (review 13 Oct) */
        BYTE *old = ((type == 1 || type == 2) && !e->dropped) ? ea_same_type(P, type, id, item) : 0;
        if (g_eaDead) return 0;
        ea_log("ran '%s' (id %d type %d ammo %d pull %d): DD accepted it (%s)%s", e->name, id, type, ammo, pull,
               have == item ? "in the inventory" : "owner set, add pending", old ? " - a same-type gun is still there" : "");
        if (have != item) {                           /* deferred: DD is holstering; drop only once the new gun is in */
            if (old) { e->pend = 1; e->pendT0 = GetTickCount(); ea_log("'%s': waiting for DD's deferred add (P+0xd84 = %08lx) before dropping the same-type gun", e->name, rd32(P + 0xd84)); }
            return 0;
        }
        if (old) ea_drop(P, old, "after equip", e->name);
        if (g_eaDead) return 0;
        if (pull == 0 && e->dropped == 2 && g_eac.select && g_eac.mode == EA_LIVE) {   /* PRE dropped the gun in hand */
            ea_call3("select", EA_F_SELECT, P, (DWORD)id, 0, 1);
            if (!g_eaDead) ea_log("'%s': the gun dropped at the cutscene start was in hand - selected the new one", e->name);
        }
        return 0;
    }
    if (have) { ea_log("ran '%s' (id %d): the player already had that id - DD topped up the ammo (as Dead Men)", e->name, id); return 0; }
    ea_log("ran '%s' (id %d type %d ammo %d pull %d): REFUSED by DD (guns carried %d) - applying Dead Men's rule", e->name, id, type, ammo, pull, guns);
    int dropped = e->dropped;
    if (type == 1 || type == 2) {
        BYTE *old = ea_same_type(P, type, id, item); if (g_eaDead) return 0;
        if (old) { int d = ea_drop(P, old, "after refusal", e->name); if (d) dropped = d; if (g_eaDead) return 0; }
        /* still two guns (no same-type gun to replace): DD carries two guns at most, so one has to go - the gun in hand,
           else the first gun of the other type (never a third gun through AddItem) */
        int g2 = ea_guns(P); if (g_eaDead) return 0;
        if (old && g_eac.mode != EA_LIVE && g2 > 0) g2--;   /* dry: as if the same-type gun had gone */
        if (g2 >= 2) {
            BYTE *cur = ea_cur_item(P); if (g_eaDead) return 0;
            int ct = cur ? ea_item_type(cur) : -1; if (g_eaDead) return 0;
            BYTE *victim = (cur && cur != old && cur != item && (ct == 1 || ct == 2)) ? cur : ea_same_type(P, type == 1 ? 2 : 1, -1, item);
            if (g_eaDead) return 0;
            if (victim && victim != old) {
                int d = ea_drop(P, victim, victim == cur ? "two guns, dropping the one in hand" : "two guns, dropping the other-type gun", e->name);
                if (d) dropped = d;
                if (g_eaDead) return 0;
            } else ea_log("'%s': still %d guns carried and none to drop - not added (DD carries two guns at most)", e->name, g2);
        }
    }
    if (g_eac.mode != EA_LIVE) { ea_log("'%s': dry: would add it now", e->name); return 0; }
    guns = ea_guns(P); if (g_eaDead) return 0;
    if ((type == 1 || type == 2) && guns >= 2) {
        ea_log("'%s': still %d guns carried after the drops - NOT added (no third gun)", e->name, guns);
        return 0;
    }
    if (guns >= 0 && guns <= 1) {
        ea_call1("DD equip (re-run)", EA_F_EQUIP, t, (DWORD)e->track); if (g_eaDead) return 0;
        BYTE *now = ea_inv_find(P, id); if (g_eaDead) return 0;
        ea_log("'%s': re-ran DD's equip 0x7cd310 with %d gun(s) carried: %s", e->name, guns,
               now == item ? "added" : rd32(item + 0x5c) == hP ? "owner set, add pending" : "STILL REFUSED");
        if (now == item && pull == 0 && dropped == 2 && g_eac.select && !g_eaDead) {
            ea_call3("select", EA_F_SELECT, P, (DWORD)id, 0, 1);
            if (!g_eaDead) ea_log("'%s': the dropped gun was in hand - selected the new one", e->name);
        }
        return 0;
    }
    /* grenade / special item (type 0/3 only) with two guns carried: DM's own add 0x5f8600 -> DD's port 0x6020d0 */
    if (type == 1 || type == 2 || guns < 0) { ea_log("'%s': type %d, guns carried %d - no AddItem fallback (guns never go past two)", e->name, type, guns); return 0; }
    BYTE *ao = (BYTE*)ea_call("ammo object", rd32((BYTE*)rd32(item) + 0x2c8), item, 0, NULL); if (g_eaDead) return 0;
    int cap = -1;
    if (sq_rd(ao, 4) && sq_code(rd32((BYTE*)rd32(ao) + 0x29c))) cap = (int)ea_call("clip capacity", rd32((BYTE*)rd32(ao) + 0x29c), ao, 0, NULL);
    if (g_eaDead) return 0;
    int clip = (cap >= 0 && cap < ammo) ? cap : ammo, res = ammo - clip;
    if (ammo <= 0) clip = res = -1;                   /* AddItem's own defaults */
    ea_call3("AddItem", EA_F_PADD, P, (DWORD)item, (DWORD)clip, (DWORD)res); if (g_eaDead) return 0;
    BYTE *now = ea_inv_find(P, id); if (g_eaDead) return 0;
    ea_log("'%s': added with AddItem 0x6020d0 (clip %d reserve %d, capacity %d)%s: %s", e->name, clip, res, cap,
           pull ? " - no pullwpn for a grenade/special item" : "", now == item ? "in the inventory" : "NOT in the inventory");
    return 0;
}
static void ea_run(EaTask *e, BYTE *P, int phase) {
    static const char *const nm[] = {"equip pre", "equip post", "equip post (deferred)", "equip unlock weaponhdl", "equip select retry"};
    EaArg a = {e, P, phase};
    if (climb_guarded(nm[phase], ea_body, &a) < 0) { e->pend = 0; e->wsel = 0; e->wselUnh = 0; ea_kill(nm[phase], "fault (see 'climb: FAULT ...' above)"); }
}

/* ---------- per-frame tick ---------- */
static int equipassist_tick_body(void *unused) {
    (void)unused;
    sq_rd_reset();
    ea_cfg_poll();
    char scene[8];                                    /* reads only up to the build check (no engine call) */
    EnterCriticalSection(&g_cmpCs); memcpy(scene, g_cscene, sizeof scene); LeaveCriticalSection(&g_cmpCs);
    scene[sizeof scene - 1] = 0;
    BYTE *P = ea_player();
    int T = cl_curT();
    /* new scene, or a new player object. P == NULL alone (teardown / loading / a restart's gap) does not reset, as
       revive.inc: the tasks just wait (the tick returns below while P == NULL) */
    int sceneChg = strcmp(scene, g_ea.scene) != 0;
    if ((P && P != g_ea.P) || sceneChg) {
        /* same scene, new player: the cutscenes (and their unlock tasks) may live on - give DD its weaponhdl back first
           (ownership-checked). New scene: no unmute (review): the old scene's unlock tasks may already be freed */
        if (!sceneChg && rd32((void*)0x1548fd8) != 0) ea_unmute_all("player changed in the same scene");   /* merc list live: scene not torn down */
        memset(&g_ea, 0, sizeof g_ea); g_ea.P = P; memcpy(g_ea.scene, scene, sizeof scene); g_ea.lastT = T; g_ea.t0 = GetTickCount(); g_ea.scanAt = g_ea.t0 + 2000;
        g_ea.listed = P && ea_level_listed(scene); g_ea.cfgGen = g_eacGen;
        if (g_ea.listed && g_eac.mode != EA_OFF) ea_log("level %s: player %p mode %s - scanning for player equip tasks in 2 s", scene, P, EA_MODE[g_eac.mode]);
    } else if (g_ea.cfgGen != g_eacGen) {             /* config changed: levels= re-evaluated for this scene */
        int was = g_ea.listed;
        g_ea.cfgGen = g_eacGen; g_ea.listed = g_ea.P && ea_level_listed(scene);
        if (was && !g_ea.listed) { ea_log("level %s no longer listed (levels=%s) - module idle here", scene, g_eac.levels); ea_unmute_all("level no longer listed"); }
        else if (!was && g_ea.listed && g_eac.mode != EA_OFF) ea_log("level %s now listed (levels=%s) - scanning for player equip tasks", scene, g_eac.levels);
    }
    if (g_eac.mode == EA_OFF) {                       /* switched off: give DD back every muted unlock of this scene (ownership-checked), stop selecting */
        ea_unmute_all("mode off");
        return 0;
    }
    if (g_eaBuild < 0) {
        g_eaBuild = ea_check_build(); anp_log("equip: kl2 build check %s", g_eaBuild ? "ok" : "FAILED (module inactive)");
        g_eaHdlOk = g_eaBuild ? ea_check_hdl() : 0;
        anp_log("equip: wpnhdl %s", g_eaHdlOk ? "build check ok" : "off (kl2 build check failed: Dog Days' own weaponhdl)");
    }
    if (!g_eaBuild) return 0;                          /* build check failed: no engine calls at all, not even getters (review) */
    if (!P || !g_ea.listed) return 0;
    if (T < g_ea.lastT) {                             /* checkpoint restart: the cutscenes reset (+5 cleared by slot 6) */
        int stale = 0;
        for (int i = 0; i < g_ea.n; i++) if (rd32(g_ea.t[i].task) != EA_EQUIP_VT || rd32(g_ea.t[i].mc) != EA_MC_VT) stale = 1;
        if (stale) {                                  /* review: the restart rebuilt the cutscenes - forget (no write) and rescan */
            ea_log("restart: equip tasks were reallocated - list forgotten, rescanning in 2 s");
            g_ea.n = 0; g_ea.scanState = 0; g_ea.scans = 0; g_ea.scanAt = GetTickCount() + 2000;
        }
        else for (int i = 0; i < g_ea.n; i++) { g_ea.t[i].preDone = 0; g_ea.t[i].dropped = 0; g_ea.t[i].pend = 0; g_ea.t[i].wsel = 0; g_ea.t[i].wselUnh = 0; ea_hdl_unmute(&g_ea.t[i]); }
    }
    if (T == g_ea.lastT) return 0;                    /* paused */
    g_ea.lastT = T;
    DWORD now = GetTickCount();
    if (g_ea.scanState == 0 && (int)(now - g_ea.scanAt) >= 0) { g_ea.scanState = 1; g_ea.scan = 0x10000; g_ea.scanStart = now; g_ea.scans++; }
    if (g_ea.scanState == 1) {
        ea_scan_step();
        if (g_ea.scanState == 2) {
            ea_log("scan %d done in %lu ms: %d player equip task(s)", g_ea.scans, now - g_ea.scanStart, g_ea.n);
            for (int i = 0; i < g_ea.n; i++) {
                EaTask *e = &g_ea.t[i]; BYTE *it = (BYTE*)rd32(e->task + 0x30);
                ea_log("  task %p MC %p track %p item '%s' %p ammo %ld pull %d executed %d mc state %d%s", e->task, e->mc, e->track, e->name, it,
                       (long)rd32(e->task + 0x28), rd8(e->task + 0x2c), e->ex, e->st,
                       !e->unl ? "" : e->hdl == 3 ? " - then unlockplayer weaponhdl UnholsterPrim" : " - then unlockplayer weaponhdl UnholsterSec");
            }
            if (!g_ea.n && g_ea.scans < 2) { g_ea.scanState = 0; g_ea.scanAt = now + 20000; }   /* one more scan ~20 s later */
        }
        return 0;
    }
    for (int i = 0; i < g_ea.n && !g_eaDead; i++) {
        EaTask *e = &g_ea.t[i];
        if (rd32(e->task) != EA_EQUIP_VT || rd32(e->mc) != EA_MC_VT) continue;   /* freed: the next scene rescans */
        /* config changed while muted (wpnhdl=0, dry, or wpnhdl build check off) and the unlock has not run yet: give DD
           its weaponhdl back now, or the unlock would run with +0x24 = 0 and nobody would select (review) */
        if (e->muted && (!ea_wpnhdl() || g_eac.mode != EA_LIVE) && !rd8(e->unl + 5)) {
            ea_log("'%s': wpnhdl no longer live - unlockplayer weaponhdl %d given back to Dog Days", e->name, e->hdl);
            ea_hdl_unmute(e); e->wsel = 0; e->wselUnh = 0;
        }
        int ex = rd8(e->task + 5), st = (int)rd32(e->mc + 8);
        if (st != e->st) {
            if (st == 2 && g_eac.pre && !e->preDone) { e->preDone = 1; ea_run(e, P, 0); }
            if (st == 2 && !g_eaDead) ea_hdl_mute(e);
            if (st == 0) { e->preDone = 0; e->dropped = 0; e->pend = 0; e->wsel = 0; e->wselUnh = 0; ea_hdl_unmute(e); }
            e->st = st;
        }
        if (ex != e->ex) {
            if (ex == 1 && g_eac.post && !g_eaDead) { e->pend = 0; ea_run(e, P, 1); }
            e->ex = ex;
        }
        if (e->pend && !g_eaDead) ea_run(e, P, 2);   /* waiting for DD's deferred add (one inventory lookup per frame) */
        if (e->unl && !g_eaDead) {                    /* wpnhdl: the unlockplayer after this equip */
            int ux = rd32(e->unl) == EA_UNLOCK_VT ? rd8(e->unl + 5) : -1;
            if (ux >= 0 && ux != e->unlEx) { if (ux == 1) ea_run(e, P, 3); e->unlEx = ux; }
            if (e->wsel && !g_eaDead) ea_run(e, P, 4);
        }
    }
    return 0;
}
static void equipassist_frame(void) {
    if (g_eaDead || !g_clMainTid || GetCurrentThreadId() != g_clMainTid) return;
    if (climb_guarded("equip tick", equipassist_tick_body, 0) < 0) ea_kill("tick", "fault (see 'climb: FAULT ... in equip tick' above)");
}
