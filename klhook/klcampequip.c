/* klcampequip.c - [CampEquip]: Kane's start rifle on the Dead Men CAMPAIGN levels = the Dead Men one (MP5 / SG552) with OUR gun
 * assets (DD items 20 UMP / 29 Zastava wearing the MP5 look, gunraw/gunpunch sounds, KLGuns). OFF by default. Idle unless
 * [Campaign] Enable=1 and a campaign scene (klcmp_level_active); never on FA maps, Arcade or online. Included AFTER klfedkit.c
 * (uses its KLFK_* constants and klfk_pool) and after klcampgive.c (klcsq_player / klcsq_blocked).
 *
 * WHY: the campaign start inventory is engine/profile carry-over, not level data (luvsic), so Kane arrives with DD's own loadout (the
 * SPAS-12 the owner sees). Dead Men gives no per-level start gun either (scripted equips only at M01 / M02 / M03A). This swaps the rifle
 * once per player instance through the FA round-start loadout routine 0x410710 (the same call klfedkit's AkChance makes), so the old
 * pistol + rifle go "out of use" until the level resets: they are not dropped, a Spas he held does not appear as a pickup.
 * AI guns, level pickups and crewmate guns are never touched.
 *
 * Mode=off | log (report inventory/pool/choice, change nothing) | dm (per-level DM gun, GUESS table in klcampequip_logic.h)
 *      | mine (the FA default rifle, item 29 Zastava, row 28). Item= overrides the item in dm / mine. SkipScripted=1 leaves M01..M03 alone.
 * READ = taken from klfedkit.c (same routine, same guards), GUESS = not checked against the game: whether 0x8df480 (the session
 * test inside 0x410710) accepts a campaign session is a GUESS - the log line says GIVEN / NOT given by the pool count. Not benched.
 * KLHook.ini [CampEquip]  Enable=0  Mode=dm  Item=0  PistolRow=0  SkipScripted=1  Delay=3000  Log=1  (see ini_campequip_1110.txt)
 */
#ifndef KLCAMPEQUIP_C
#define KLCAMPEQUIP_C
#include "klcampequip_logic.h"

static struct { int on, mode, item, pistolRow, skip, delay, log, dead; DWORD P, since; int done; } klce;
struct klce_job { DWORD w, P; int prow, rrow; };

static int klce_call(void *arg)
{
    struct klce_job *j = (struct klce_job *)arg;
    ((void (__fastcall *)(void *, void *, DWORD, int, int, int))(DWORD_PTR)KLH_VA(KLFK_LOADOUT))((void *)(DWORD_PTR)j->w, 0, j->P, j->prow, j->rrow, 0);
    return 1;
}

static void klcampequip_init(void)
{
    char v[32];
    klce.on = GetPrivateProfileIntA("CampEquip", "Enable", 0, klh_ini) != 0;
    if (!klce.on) return;
    GetPrivateProfileStringA("CampEquip", "Mode", "dm", v, sizeof v, klh_ini);
    klce.mode = klce_mode(v);
    klce.item = GetPrivateProfileIntA("CampEquip", "Item", 0, klh_ini);
    klce.pistolRow = GetPrivateProfileIntA("CampEquip", "PistolRow", 0, klh_ini); if (klce.pistolRow < 0 || klce.pistolRow >= KLFK_ROWS) klce.pistolRow = 0;
    klce.skip = GetPrivateProfileIntA("CampEquip", "SkipScripted", 1, klh_ini) != 0;
    klce.delay = GetPrivateProfileIntA("CampEquip", "Delay", 3000, klh_ini); if (klce.delay < 0 || klce.delay > 60000) klce.delay = 3000;
    klce.log = GetPrivateProfileIntA("CampEquip", "Log", 1, klh_ini);
    klog("campequip: ON (NOT benched; campaign levels only): mode %d item %d pistolrow %d skip-scripted %d delay %d ms", klce.mode, klce.item, klce.pistolRow, klce.skip, klce.delay);
}

static void klcampequip_tick(int game_thread)
{
    static const BYTE loadout_code[10] = { 0x55, 0x8b, 0xe9, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8 };
    static const BYTE give_code[11] = { 0x56, 0x8b, 0x74, 0x24, 0x0c, 0x57, 0x8b, 0xf9, 0x83, 0xfe, 0x40 };
    static const BYTE find_code[11] = { 0x51, 0x8b, 0x01, 0x53, 0x55, 0x56, 0x57, 0x89, 0x4c, 0x24, 0x10 };
    DWORD P, sc, w, row[2] = { 0, 0 }, pistol[2] = { 0, 0 }, shop = (DWORD)(DWORD_PTR)KLH_VA(KLFK_SHOP);
    char scene[200], key[80]; int lv, item, r, i, fr, fp, b[3][4], a[3][4]; struct klce_job job;
    if (!klce.on || !game_thread || !klh_exe_ok || klce.dead || klce.mode == KLCE_OFF) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA) || kl_online() || !klcmp_level_active()) { klce.P = 0; return; }
    if (!(P = klcsq_player()) || !(sc = klh_rd32(P + 0xcd0)) || klh_rd32(sc + 4) != P) { klce.P = 0; return; }
    if (P != klce.P) { klce.P = P; klce.since = GetTickCount(); klce.done = 0; }
    if (klce.done || GetTickCount() - klce.since < (DWORD)klce.delay || klcsq_blocked(P)) return;
    klce.done = 1;                                                      /* once per player instance, whatever the outcome */
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) { klog("campequip: no scene key: left alone"); return; }
    lv = klce_level_no(key);
    item = klce_pick(klce.mode, lv, klce.item, klce.skip);
    r = -1;
    for (i = 0; item && i < KLFK_ROWS; i++) if (klh_rd(shop + 24 * i, row, 8) && row[0] == (DWORD)item) { r = i; break; }
    if (!klh_rd(shop + 24 * klce.pistolRow, pistol, 8)) pistol[0] = 0;
    memset(b, 0, sizeof b);
    fr = item ? klfk_pool((DWORD)item, b[0]) : -1; fp = pistol[0] ? klfk_pool(pistol[0], b[1]) : -1;
    if (klce.log) klog("campequip: level %s (m%d) mode %d -> item %d row %d; pool free rifle %d (free/dropped/owned/out %d/%d/%d/%d), pistol item %lu free %d", key, lv, klce.mode, item, r, fr,
                       b[0][0], b[0][1], b[0][2], b[0][3], (unsigned long)pistol[0], fp);
    if (!item) { klog("campequip: nothing to do on this level (mode log, scripted level or no level number)"); return; }
    if (r < 0 || !row[1] || row[1] > 1000 || !pistol[0] || pistol[0] > 63) { klog("campequip: item %d is in no shop row (or the pistol row is bad): left alone", item); return; }
    if (!klc_same_code(KLFK_LOADOUT, loadout_code, sizeof loadout_code) || !klc_same_code(KLFK_GIVE, give_code, sizeof give_code) || !klc_same_code(KLFK_POOLFIND, find_code, sizeof find_code)) {
        klog("campequip: the game's loadout routines are not the ones this build knows: left alone"); return;
    }
    if (!klce_pool_ok(fr, fp, (DWORD)item == pistol[0])) { klog("campequip: pool refuses (free rifle %d of item %d, free pistol %d of item %lu; the level may bind no object of it): left alone", fr, item, fp, (unsigned long)pistol[0]); return; }
    if (!(w = klh_rd32((DWORD_PTR)KLH_VA(KLFK_WEAPONS)))) return;
    job.w = w; job.P = P; job.prow = klce.pistolRow; job.rrow = r;
    klog("campequip: LIVE loadout call: item %d (row %d), pistol row %d", item, r, klce.pistolRow);
    if (klfc_guard("campequip loadout", klce_call, &job) < 0) { klce.dead = 1; klog("campequip: FAULT in the loadout call: DISABLED (restart the game)"); return; }
    klfk_pool((DWORD)item, a[0]);
    klog("campequip: back; free rifle %d -> %d: %s", b[0][0], a[0][0], a[0][0] == b[0][0] - 1 ? "GIVEN" : "NOT given by that count (0x8df480 may refuse a campaign session: GUESS)");
}
#endif /* KLCAMPEQUIP_C */
