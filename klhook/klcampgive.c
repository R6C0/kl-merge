/* klcampgive.c - [CampGive]: key 4 gives the gun in the player's hand to a crewmate (or swaps it with the gun he carries) on the Dead Men
 * CAMPAIGN levels. OFF by default, idle unless [Campaign] Enable=1 and a campaign scene (M01..M14) is loaded (klcampaign_gate.h): on
 * Dog Days' 9 FA maps, Dead Men FA maps, Arcade and online it never runs. Included AFTER klcampsquad.c (uses its klcsq_player / klcsq_body /
 * klcsq_blocked / merc list).
 *
 * ported from luvsic's a-newer-perspective loader/give.inc @32aa649 (in contribution with luvsic). READ = taken from his code,
 * MEASURED = checked here against kl2.exe, GUESS = neither. Every address below is READ from his file; the 14 code heads (below) are
 * compared byte for byte before the first call, and the type-to-slot table at 0x49f288 too (MEASURED by luvsic against kl2 0490, NOT
 * re-measured here); a mismatch turns the module OFF for the session.
 *
 * SEQUENCE (the same game routines DD's own pickup / DM's give use; no code byte is changed):
 *   GIVE : player.RemoveItem 0x633250(item); merc.AddItem 0x4e3fa0(type, hItem); node parent 0x598460(merc node);
 *          item vt+0x27c SetOwner(hMerc, parent, 0, 0); item vt+0x25c SetState(4, 0) (Drawn=1); PlayerMonitor 0x589600(P, 18).
 *   SWAP : as GIVE, but first merc.AddItem(type, 0), actor vt+0x254 detach (index from the attach table), unhook 0x6d26f0(old node, 0),
 *          and at the end player.AddItem 0x6020d0(old, -1, reserve).
 *   LIMBO: a fault between RemoveItem and SetOwner hands the gun back (player.AddItem(item, -1, -1)); the merc's slot is cleared first when
 *          it already holds the handle, and the give-back is skipped when that does not take (no gun with two owners). READ gv_giveback.
 * TARGET : Target=selected (the receiver sc+0x10, else the nearest) | aim (the crosshair handle) | nearest.
 * NOT PORTED (left out on purpose): the merc speech ack/deny, the on-screen prompt and the result line (log only), the "revive: merc is
 * down" check (revive.inc is not ported), the clip-capacity read for swapres (a fixed 30 rounds per clip is used), the movement-state /
 * seat / use-action gates of gv_gate (replaced by: input-block gate P+0x2728 / P+0x2760 and the 0.75 s key debounce), the command file,
 * dry-run mode as a separate level (here Dry=1 logs what would happen and changes nothing).
 * GUESS: key 4 is also a weapon-select key of the campaign; the game reads it too (this module does not consume it). Rebind with Key=.
 * Nothing here is benched.
 *
 * KLHook.ini [CampGive]  (see klhook/ini_campaign_gameplayA.txt)
 *   Enable=0  Key=0x34  Target=selected|aim|nearest  Range=300  Swap=1  Types=6  Refuse=50,51,53,54  Drawn=1  Event=18  SwapClips=0  Dry=0  Log=1
 */
#ifndef KLCAMPGIVE_C
#define KLCAMPGIVE_C
#include "klcampgive_logic.h"

#define KLCGV_F_RMV     0x00633250u
#define KLCGV_F_PADD    0x006020d0u
#define KLCGV_F_AADD    0x004e3fa0u
#define KLCGV_F_OBJH    0x006ece90u
#define KLCGV_F_HOBJ    0x008ccde0u
#define KLCGV_F_PARENT  0x00598460u
#define KLCGV_F_UNHOOK  0x006d26f0u
#define KLCGV_F_ITEMID  0x0047ded0u
#define KLCGV_F_ITEMTYP 0x00539e30u
#define KLCGV_F_PMON    0x00589600u
#define KLCGV_F_NODEPOS 0x007b3020u
#define KLCGV_F_CURITEM 0x00727b40u
#define KLCGV_F_ACT258  0x006de200u
#define KLCGV_F_SETRES  0x008be2c0u
#define KLCGV_SLOT0     0x5e0u               /* READ GV_SLOT0: actor+0x5e0[slot] item handles */
#define KLCGV_GM        0x00dd265cu          /* READ gv_reg: [gm+0x15b0] = item registry */
#define KLCGV_WPN_ID    0x0156b7a8u
#define KLCGV_WPN_MASK  0x0156b7acu
#define KLCGV_ACT_ID    0x01547b24u
#define KLCGV_ACT_MASK  0x01547b28u
#define KLCGV_SLOTTAB   0x0049f288u

static struct {
    int on, vk, target, swap, drawn, event, swapClips, dry, log, dead, heads, nrefuse, refuse[16];
    float range; unsigned types;
    SHORT (WINAPI *aks)(int); HWND (WINAPI *fgw)(void); DWORD (WINAPI *wtp)(HWND, LPDWORD);
    int keyWas; DWORD lastGive, P; int active;
} klcgv;
enum { KLCGV_T_SELECTED = 0, KLCGV_T_AIM, KLCGV_T_NEAREST };

static void klcampgive_init(void)
{
    char v[64]; HMODULE u;
    klcgv.on = GetPrivateProfileIntA("CampGive", "Enable", 0, klh_ini) != 0;
    if (!klcgv.on) return;
    klcgv.vk = GetPrivateProfileIntA("CampGive", "Key", 0x34, klh_ini) & 0xff;
    GetPrivateProfileStringA("CampGive", "Target", "selected", v, sizeof v, klh_ini);
    klcgv.target = !_stricmp(v, "aim") ? KLCGV_T_AIM : !_stricmp(v, "nearest") ? KLCGV_T_NEAREST : KLCGV_T_SELECTED;
    { char s[16]; GetPrivateProfileStringA("CampGive", "Range", "300", s, sizeof s, klh_ini); klcgv.range = klcgv_clamp_range((float)atof(s)); }
    klcgv.swap = GetPrivateProfileIntA("CampGive", "Swap", 1, klh_ini) != 0;
    klcgv.types = (unsigned)GetPrivateProfileIntA("CampGive", "Types", 6, klh_ini);
    GetPrivateProfileStringA("CampGive", "Refuse", "50,51,53,54", v, sizeof v, klh_ini);
    klcgv.nrefuse = klcgv_parse_ids(v, klcgv.refuse, 16);
    klcgv.drawn = GetPrivateProfileIntA("CampGive", "Drawn", 1, klh_ini) != 0;
    klcgv.event = GetPrivateProfileIntA("CampGive", "Event", 18, klh_ini); if (klcgv.event < 0 || klcgv.event > 63) klcgv.event = 18;
    klcgv.swapClips = GetPrivateProfileIntA("CampGive", "SwapClips", 0, klh_ini); if (klcgv.swapClips < 0 || klcgv.swapClips > 20) klcgv.swapClips = 0;
    klcgv.dry = GetPrivateProfileIntA("CampGive", "Dry", 0, klh_ini) != 0;
    klcgv.log = GetPrivateProfileIntA("CampGive", "Log", 1, klh_ini);
    { int j; for (j = 0; j < KK_N; j++) if (klcgv.vk && klkeys_vk(j) == klcgv.vk) { klog("campgive: key %#x is also KLHook's own key %d: give key OFF (rebind [CampGive] Key)", klcgv.vk, j); klcgv.vk = 0; break; } }
    if ((u = GetModuleHandleA("user32.dll")) != 0) { klcgv.aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); klcgv.fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); klcgv.wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
    klog("campgive: ON (NOT benched; campaign levels only): key %#x target %d range %.0f swap %d types %#x refuse-ids %d drawn %d event %d swapclips %d%s%s", klcgv.vk, klcgv.target, (double)klcgv.range,
         klcgv.swap, klcgv.types, klcgv.nrefuse, klcgv.drawn, klcgv.event, klcgv.swapClips, klcgv.dry ? " DRY" : "", klcgv.aks ? "" : " (no GetAsyncKeyState: key off)");
}

/* the 14 code heads (READ from give.inc gv_check_build) + the slot table; one mismatch = OFF */
static int klcgv_heads(void)
{
    static const struct { DWORD a; BYTE b[6]; } h[] = {
        { KLCGV_F_CURITEM, { 0x56, 0x8b, 0xf1, 0x8b, 0x06, 0x8b } }, { KLCGV_F_RMV, { 0x53, 0x8b, 0x5c, 0x24, 0x08, 0x56 } }, { KLCGV_F_PADD, { 0x83, 0xec, 0x08, 0x56, 0x57, 0x8b } },
        { KLCGV_F_AADD, { 0xa1, 0x5c, 0x26, 0xdd, 0x00, 0x8b } }, { KLCGV_F_OBJH, { 0x51, 0x8b, 0x0d, 0x90, 0xff, 0xe0 } }, { KLCGV_F_HOBJ, { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d } },
        { KLCGV_F_PARENT, { 0x8b, 0x41, 0x50, 0x85, 0xc0, 0x75 } }, { KLCGV_F_UNHOOK, { 0x80, 0x7c, 0x24, 0x04, 0x00, 0x74 } }, { KLCGV_F_ITEMID, { 0x8b, 0x44, 0x24, 0x04, 0x85, 0xc0 } },
        { KLCGV_F_ITEMTYP, { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b } }, { KLCGV_F_PMON, { 0x55, 0x8b, 0x6c, 0x24, 0x0c, 0x80 } }, { 0x00763db0u, { 0x55, 0x8b, 0xec, 0x51, 0x8b, 0x01 } },
        { KLCGV_F_NODEPOS, { 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c } }, { 0x008df9c0u, { 0x8b, 0x44, 0x24, 0x04, 0x55, 0x8b } } };
    static const DWORD tab[4] = { 0x0049f26bu, 0x0049f273u, 0x0049f278u, 0x0049f280u };
    int i;
    if (klcgv.heads) return klcgv.heads > 0;
    klcgv.heads = -1;
    for (i = 0; i < (int)(sizeof h / sizeof h[0]); i++) if (!klb_same_code(h[i].a, h[i].b, 6)) { klog("campgive: code head %#lx differs from the build give.inc knew: OFF", (unsigned long)h[i].a); return 0; }
    for (i = 0; i < 4; i++) if (klh_rd32((DWORD_PTR)KLH_VA(KLCGV_SLOTTAB) + 4 * i) != (DWORD)(DWORD_PTR)KLH_VA(tab[i])) { klog("campgive: type-to-slot table (0x49f288) differs: OFF"); return 0; }
    klcgv.heads = 1; return 1;
}

static int klcgv_key(void)
{
    HWND fg; DWORD pid = 0;
    if (!klcgv.vk || !klcgv.aks || !klcgv.fgw || !klcgv.wtp || !(fg = klcgv.fgw())) return 0;
    klcgv.wtp(fg, &pid);
    return pid == GetCurrentProcessId() && (klcgv.aks(klcgv.vk) & 0x8000) != 0;
}
static int klcgv_code(DWORD f) { return f >= (DWORD)(DWORD_PTR)KLH_VA(0x00401000u) && f < (DWORD)(DWORD_PTR)KLH_VA(0x00b00000u); }
static DWORD klcgv_vf(DWORD o, DWORD off) { DWORD vt = klh_rd32(o); return vt ? klh_rd32(vt + off) : 0; }
static int klcgv_is_kind(DWORD o, DWORD idVA, DWORD maskVA)
{
    DWORD f = klcgv_vf(o, 0x30), id = klh_rd32((DWORD_PTR)KLH_VA(idVA)), mask = klh_rd32((DWORD_PTR)KLH_VA(maskVA));
    if (!o || !klcgv_code(f) || !id) return 0;
    return (((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)f)((void *)(DWORD_PTR)o, 0) & mask) == id;
}
static DWORD klcgv_reg(void) { DWORD gm = klh_rd32((DWORD_PTR)KLH_VA(KLCGV_GM)); return gm ? klh_rd32(gm + 0x15b0) : 0; }
static DWORD klcgv_obj(DWORD h) { return h ? ((DWORD (__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_HOBJ))(h) : 0; }
static DWORD klcgv_handle(DWORD o)               /* READ gv_handle: 0x6ece90 checked by resolving it back */
{
    DWORD h;
    if (!o || !klh_rd32(o + 4)) return 0;
    h = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLCGV_F_OBJH))((void *)(DWORD_PTR)o, 0);
    return (h && klcgv_obj(h) == o) ? h : 0;
}
static int klcgv_item_id(DWORD item) { DWORD r = klcgv_reg(); return r ? (int)((DWORD (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_ITEMID))((void *)(DWORD_PTR)r, 0, item) : -1; }
static int klcgv_item_type(DWORD item)           /* 0x539e30 dereferences item+0xc4 (template) */
{
    DWORD r = klcgv_reg(), t = klh_rd32(item + 0xc4);
    if (!r || !t || !klh_rd32(t)) return -1;
    return (int)((DWORD (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_ITEMTYP))((void *)(DWORD_PTR)r, 0, item);
}
static int klcgv_pos(DWORD body, float *out)
{
    DWORD node = klh_rd32(body + 4);
    out[0] = out[1] = out[2] = out[3] = 0;
    if (!node || !klh_rd32(node)) return 0;
    ((void (__fastcall *)(void *, void *, float *))(DWORD_PTR)KLH_VA(KLCGV_F_NODEPOS))((void *)(DWORD_PTR)node, 0, out);
    return klb_finite(out[0]) && klb_finite(out[1]) && klb_finite(out[2]);
}
static int klcgv_alive(DWORD body)               /* READ gv_alive: able byte 1 and vt+0x680 (is-dead) false */
{
    BYTE a = 0; DWORD f = klcgv_vf(body, 0x680);
    klh_rd(body + 0x576, &a, 1);
    if (a != 1 || !klcgv_code(f)) return 0;
    return !(((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)f)((void *)(DWORD_PTR)body, 0) & 0xff);
}
static int klcgv_stored_res(DWORD it) { DWORD v[2]; return klh_rd(it + 0xdc, v, 8) ? (int)(v[1] ^ 0xbeebbeebu) : -1; }   /* READ: clip [item+0xdc], reserve [item+0xe0], XOR 0xbeebbeeb */
static int klcgv_attach_index(DWORD actor, DWORD node)   /* READ gv_attach_index: -1 when not attached */
{
    DWORD lnk = klh_rd32(actor + 0x88); int n, i;
    if (!lnk) return -1;
    n = (int)klh_rd32(lnk + 0x14); if (n < 0 || n > 64) return -1;
    for (i = 0; i < n; i++) if (klh_rd32(lnk + 0x18 + 0x44 * i) == node) return i;
    return -1;
}

/* the target body, or 0 */
static DWORD klcgv_nearest(DWORD P, float *dOut)
{
    float pp[4], bp[4], bd = 1e30f; DWORD best = 0, cnt, i, pn = klh_rd32(P + 4);
    (void)pn;
    if (!klcgv_pos(P, pp)) return 0;
    cnt = klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST)); if (cnt > 16) cnt = 16;
    for (i = 0; i < cnt; i++) {
        DWORD s = klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST) + 4 + 4 * i), b = klcsq_body(s); float dx, dy, dz, d;
        if (!b || !klcgv_alive(b) || !klcgv_pos(b, bp)) continue;
        dx = pp[0] - bp[0]; dy = pp[1] - bp[1]; dz = pp[2] - bp[2]; d = (float)sqrt((double)(dx * dx + dy * dy + dz * dz));
        if (d < bd) { bd = d; best = b; }
    }
    if (dOut) *dOut = bd;
    return best;
}
static DWORD klcgv_target(DWORD P)
{
    if (klcgv.target == KLCGV_T_AIM) {
        DWORD a = klh_rd32(P + 0xbd4), h = a ? klh_rd32(a + 0x2ac) : 0, o = h ? klcgv_obj(h) : 0, s = o ? klh_rd32(o + 0x77c) : 0;
        return (s && klcsq_body(s) == o) ? o : 0;
    }
    if (klcgv.target == KLCGV_T_SELECTED) {
        DWORD sc = klh_rd32(P + 0xcd0), cur = sc ? klh_rd32(sc + 0x10) : 0, s = 0;
        if (sc && klcsq_cur_idx(cur, sc + 0x1c, klcsq_nrecv(klh_rd32(sc + 0x18))) >= 0) s = klh_rd32(cur);
        if (s && klcsq_body(s)) return klcsq_body(s);
    }
    return klcgv_nearest(P, 0);
}

struct klcgv_job { DWORD P, body, item, old, hItem, hBody, bnode, onode, fOwner, fState, fB254; int type, oRes, hasOld, drawn, event, r; volatile int step; };
static int klcgv_do(void *arg)
{
    struct klcgv_job *j = (struct klcgv_job *)arg; DWORD parent;
    ((void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_RMV))((void *)(DWORD_PTR)j->P, 0, j->item);          /* 1. the player lets go of it */
    j->step = KLCGV_S_REMOVED;
    if (j->hasOld) {                                                                                                                 /* 2. swap: empty the slot, detach + unhook the old gun */
        ((void (__fastcall *)(void *, void *, int, DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_AADD))((void *)(DWORD_PTR)j->body, 0, j->type, 0);
        j->step = KLCGV_S_CLEARED;
        j->r = klcgv_attach_index(j->body, j->onode);
        if (j->r >= 0) ((void (__fastcall *)(void *, void *, DWORD, int))(DWORD_PTR)j->fB254)((void *)(DWORD_PTR)j->body, 0, j->onode, j->r);
        ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLCGV_F_UNHOOK))((void *)(DWORD_PTR)j->onode, 0, 0);
    }
    ((void (__fastcall *)(void *, void *, int, DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_AADD))((void *)(DWORD_PTR)j->body, 0, j->type, j->hItem);   /* 3. the merc gets it */
    j->step = KLCGV_S_MADD;
    parent = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLCGV_F_PARENT))((void *)(DWORD_PTR)j->bnode, 0);
    j->step = KLCGV_S_PARENT;
    ((void (__fastcall *)(void *, void *, DWORD, DWORD, int, int))(DWORD_PTR)j->fOwner)((void *)(DWORD_PTR)j->item, 0, j->hBody, parent, 0, 0);
    j->step = KLCGV_S_OWNED;
    if (j->drawn) ((void (__fastcall *)(void *, void *, int, int))(DWORD_PTR)j->fState)((void *)(DWORD_PTR)j->item, 0, 4, 0);
    if (j->hasOld) {                                                                                                                 /* 4. swap: the player picks the old gun up */
        ((void (__fastcall *)(void *, void *, DWORD, int, int))(DWORD_PTR)KLH_VA(KLCGV_F_PADD))((void *)(DWORD_PTR)j->P, 0, j->old, -1, j->oRes);
        if (j->oRes >= 0 && klcgv_stored_res(j->old) != j->oRes && klcgv_vf(j->old, 0x308) == (DWORD)(DWORD_PTR)KLH_VA(KLCGV_F_SETRES))
            ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLCGV_F_SETRES))((void *)(DWORD_PTR)j->old, 0, j->oRes);
    }
    if (j->event) ((void (__cdecl *)(DWORD, DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_PMON))(j->P, (DWORD)j->event);
    return 1;
}
/* READ gv_giveback: after a fault, hand the gun back to the player (and clear the merc's slot first when it already holds the handle) */
static int klcgv_back(void *arg)
{
    struct klcgv_job *j = (struct klcgv_job *)arg;
    if (klcgv_handle(j->item) == j->hItem && j->step >= KLCGV_S_MADD && klh_rd32(j->body + KLCGV_SLOT0 + 4 * klcgv_slot_of(j->type)) == j->hItem)
        ((void (__fastcall *)(void *, void *, int, DWORD))(DWORD_PTR)KLH_VA(KLCGV_F_AADD))((void *)(DWORD_PTR)j->body, 0, j->type, 0);
    if (klh_rd32(j->body + KLCGV_SLOT0 + 4 * klcgv_slot_of(j->type)) == j->hItem) return 0;        /* the slot did not clear: no double owner, leave it with the merc */
    ((void (__fastcall *)(void *, void *, DWORD, int, int))(DWORD_PTR)KLH_VA(KLCGV_F_PADD))((void *)(DWORD_PTR)j->P, 0, j->item, -1, -1);
    return 1;
}

static void klcgv_give(DWORD P)
{
    struct klcgv_job j; struct klcgv_in in; DWORD body, item, hOld = 0, old = 0; float pp[4], bp[4], dx, dy, dz;
    int d, slot, oRes0 = -1;
    static const char *why[] = { "ok", "no crewmate", "crewmate not alive/able", "too far", "no item in hand", "not a gun", "unbound item", "type not given", "refused id", "already his", "he has one (Swap=0)" };
    memset(&j, 0, sizeof j); memset(&in, 0, sizeof in);
    body = klcgv_target(P);
    in.haveBody = body != 0; in.alive = body && klcgv_alive(body);
    if (body && klcgv_pos(P, pp) && klcgv_pos(body, bp)) { dx = pp[0] - bp[0]; dy = pp[1] - bp[1]; dz = pp[2] - bp[2]; in.dist = (float)sqrt((double)(dx * dx + dy * dy + dz * dz)); } else in.dist = 1e30f;
    item = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLCGV_F_CURITEM))((void *)(DWORD_PTR)P, 0);
    in.haveItem = item && klh_rd32(item + 0xc4) && klcgv_code(klcgv_vf(item, 0)) ; in.haveItem = in.haveItem && klcgv_code(klcgv_vf(item, 0x30));
    in.isWeapon = in.haveItem && klcgv_is_kind(item, KLCGV_WPN_ID, KLCGV_WPN_MASK);
    in.id = in.isWeapon ? klcgv_item_id(item) : -1; in.type = in.isWeapon ? klcgv_item_type(item) : -1;
    in.range = klcgv.range; in.types = klcgv.types; in.refuse = klcgv.refuse; in.nrefuse = klcgv.nrefuse; in.swap = klcgv.swap;
    slot = klcgv_slot_of(in.type);
    if (body && slot >= 0 && klcgv_is_kind(body, KLCGV_ACT_ID, KLCGV_ACT_MASK)) { hOld = klh_rd32(body + KLCGV_SLOT0 + 4 * slot); old = hOld ? klcgv_obj(hOld) : 0; }
    else if (body && slot >= 0) { if (klcgv.log) klog("campgive: merc body %08lx is not a ZActor: refused", (unsigned long)body); return; }
    if (hOld && !old) { if (klcgv.log) klog("campgive: merc slot %d handle %08lx does not resolve: refused", slot, (unsigned long)hOld); return; }
    in.haveOld = old != 0; in.oldIsItem = old == item;
    d = klcgv_decide(&in);
    if (d != KLCGV_OK) { if (klcgv.log) klog("campgive: key 4: nothing given (%s) [id %d type %d dist %.0f]", why[d], in.id, in.type, (double)in.dist); return; }
    j.P = P; j.body = body; j.item = item; j.old = old; j.type = in.type; j.hasOld = old != 0; j.drawn = klcgv.drawn; j.event = klcgv.event;
    j.hItem = klcgv_handle(item); j.hBody = klcgv_handle(body); j.bnode = klh_rd32(body + 4); j.onode = old ? klh_rd32(old + 4) : 0;
    j.fOwner = klcgv_vf(item, 0x27c); j.fState = klcgv_vf(item, 0x25c); j.fB254 = klcgv_vf(body, 0x254);
    if (!j.hItem || !j.hBody || !klcgv_handle(P) || !j.bnode || !klh_rd32(j.bnode) || !klcgv_code(j.fOwner) || !klcgv_code(j.fState)) { if (klcgv.log) klog("campgive: handle / node / vtable not usable: refused"); return; }
    if (old && (!j.onode || !klh_rd32(j.onode) || klcgv_vf(body, 0x258) != (DWORD)(DWORD_PTR)KLH_VA(KLCGV_F_ACT258) || !klcgv_code(j.fB254))) { if (klcgv.log) klog("campgive: swap: old item / merc vtable not usable: refused"); return; }
    if (old) { oRes0 = klcgv_stored_res(old); j.oRes = klcgv_swap_res(oRes0, 30, klcgv.swapClips); }
    if (klcgv.log) klog("campgive: %s %s: item %08lx id %d type %d -> merc %08lx slot %d%s (dist %.0f)", klcgv.dry ? "DRY" : "LIVE", old ? "SWAP" : "GIVE", (unsigned long)item, in.id, in.type, (unsigned long)body, slot,
                        old ? " (his gun comes back)" : "", (double)in.dist);
    if (klcgv.dry) return;
    if (klfc_guard("campgive give", klcgv_do, &j) < 0) {
        klog("campgive: FAULT at step %d: %s", j.step, klcgv_giveback_due(j.step) ? "handing the gun back" : "no give-back needed");
        if (klcgv_giveback_due(j.step)) klog("campgive: give-back %s", klfc_guard("campgive give-back", klcgv_back, &j) == 1 ? "done" : "did not complete (gun left where it is)");
        klcgv.dead = 1; klog("campgive: DISABLED (restart the game)"); return;
    }
    klcgv.lastGive = GetTickCount();
    if (klcgv.log) klog("campgive: done: merc slot %d now %08lx (item handle %08lx)", slot, (unsigned long)klh_rd32(body + KLCGV_SLOT0 + 4 * slot), (unsigned long)j.hItem);
}

static void klcampgive_tick(int game_thread)
{
    DWORD P, sc; int down;
    if (!klcgv.on || !game_thread || !klh_exe_ok || klcgv.dead) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA) || kl_online() || !klcmp_level_active()) { klcgv.active = 0; return; }
    if (!(P = klcsq_player()) || !(sc = klh_rd32(P + 0xcd0)) || klh_rd32(sc + 4) != P) { klcgv.active = 0; return; }
    if (!klcgv_heads()) { klcgv.dead = 1; return; }
    if (!klcgv.active || klcgv.P != P) { klcgv.active = 1; klcgv.P = P; klcgv.keyWas = 1; if (klcgv.log) klog("campgive: campaign level, player %08lx: give armed", (unsigned long)P); }
    down = klcgv_key();
    if (klcsq_blocked(P)) { klcgv.keyWas = down; return; }
    if (down && !klcgv.keyWas && GetTickCount() - klcgv.lastGive >= 750) klcgv_give(P);   /* READ: 0.75 s after the last give */
    klcgv.keyWas = down;
}
#endif /* KLCAMPGIVE_C */
