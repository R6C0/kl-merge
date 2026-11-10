/*
 * klbotglass.c - [BotGlass]: THE AI HEISTERS BREAK THE GLASS THAT BLOCKS THEM (2026-11-10; owner: "make the AI heisters shoot it open").
 * Part of KLHook (included by klhook.c right after klbotdown.c, whose klbd_online_view it uses; ticked after klbd_tick). OFF unless [BotGlass] Enable=1.
 * BUILT, NOT RUN IN THE GAME. Pure decision: klbotglass_logic.h (klbotglass_test.c). Sample keys: ini_botglass_1110.txt.
 *
 * WHY NOT A REAL SHOT: no code in the exe makes a bot aim at a glass pane (re/bots.md 12.1: a soldier's target is a Char / vehicle; no stock level even has a
 * HavokShatterGlass). There is no proven "fire at this thing" order for a bot, so this part does what a bullet ends in: it runs the pane's own break.
 *
 * READ (kl2.exe 0490, disassembled with debug/dasm.py; PROVEN = read from the code, GUESS = not seen run):
 *   - ZHavokShatterGlass vtable 0xbb105c (debug/vtfuncs.py). Slot 26 (the message handler) = 0x471410: it compares the message id with the static name ids
 *     and, for the one at [0x153ab34] ('Activate' by re/bots.md 12.1's reading), does `call 0x8d1b60` with ecx = the pane, no arguments. PROVEN.
 *   - 0x8d1b60 (thiscall, ecx = pane, plain `ret`, nothing on the stack): `if (!([pane+0x30] & 1) && [0xce513c]) { if (0x67e6a0(pane, &tmp, [pane+0x48], &obj))
 *     0x79bd10(pane, tmp, 0.0f, &obj) }` - the break, the same two routines the 'ProjectileHit' path (0x53f6d0) ends in. Byte [pane+0x30] bit 0 = already broken.
 *     PROVEN. That a bullet-less break looks and sounds like a shot pane (shards, the 'HavokShattered' message to the pane's relay that opens a loot case) is
 *     a GUESS (re/bots.md 12.8 says the same).
 *   - [pane+0x88] = the handle of the pane's visible object (the `<case>!Whole_01` ZSTDOBJ sibling); 0x8ccde0(handle) is a pure cdecl handle -> entity lookup
 *     (0x796ff0 on the scene table), 0x67e6a0 / 0x4df460 resolve it the same way. PROVEN. The pane's PLACE is that entity's scene node [entity+4] through
 *     kle_node: GUESS (vehicles and actors keep their node at +4; a ZSTDOBJ was not read). The ZHavokShatterGlass object itself has no place of its own
 *     (a ZBaseConRout). If the node is unreadable the pane is skipped and the log says so - nothing breaks blind. The first scan logs every pane's place: compare
 *     it with the map (DM02 door panes near (970, 524, 2566) / (1435, 519, 1670)); a pane whose node origin is a corner of the model is reached 'Reach' late.
 *   - Finding the panes: the entity table [[[0xe0ff90]+0xc]+0xc], 0x80 bytes a slot, object at slot+0x60 (klcensus.c); a pane = an object whose vtable is 0xbb105c.
 *     Done once per round (and again every 10 s while none was found, three times), never per tick: the walk reads up to 4 MB.
 *   - Bots: Arcade = the crew records of klb_read (flags & 1 = AI heister, status 0 = in play), exactly the set klbotdown.c acts on. Online (Online=1, HOST only) =
 *     klbd_online_view(2, ...) (the same pseudo-records the other parts use; slot 2 was free, 3 is klgrudge / klauto, 0 klhop, 1 klcardown). OnlyHeist=0 adds
 *     every other ZFFActor that has a soldier and is not a crew record (the police), found by the same table walk every 2 s.
 *
 * WHEN A PANE BREAKS (klbotglass_logic.h): a bot within Reach (cm, flat) of an intact pane, within Vert (cm) in height, moving slower than Still (cm/s, from its own
 * place delta between ticks), for DwellMs. Not facing it is checked only with Facing=1 (default 0: the node x axis being a bot's heading is a GUESS).
 * No route leg is supplied (route_hit = NULL): the bot's next waypoint is not read, so a pane the bot walks round or past never breaks; only a bot that STANDS at it.
 * GUESS: a bot that waits at a window for other reasons (cover, a loot wait) breaks it too; DwellMs is the tuning knob.
 * Not done: a gunshot sound (no proven one-shot sound call at a place was found in the hook; the shatter itself plays the glass sound), a bot firing animation.
 *
 * KEYS ([BotGlass]): Enable=0  OnlyHeist=1  Reach=250  Still=30  DwellMs=1500  Online=0  Log=1 (2 = every scan / every refusal)
 *   Vert=300 (cm of height difference allowed)  Facing=0  FacingCos=0.3  Dry=0 (1 = log what would break, call nothing)
 */
#define KLBG_C
#include "klbotglass_logic.h"                  /* the pure decision (klbotglass_test.c) */

#define KLBG_VT         0x00bb105c            /* ZHavokShatterGlass vtable (debug/vtfuncs.py) */
#define KLBG_SLOT26     0x00471410            /* its message handler: vtable +0x68 */
#define KLBG_ACTIVATE   0x008d1b60            /* thiscall (pane), no arguments: the break */
#define KLBG_GLOBAL_ON  0x00ce513c            /* the glass system switch 0x8d1b60 tests */
#define KLBG_ENTS       0x00e0ff90
#define KLBG_ACTOR_VT   0x00bb3bac            /* ZFFActor */
#define KLBG_SOLDIER_VT 0x00bd0954
#define KLBG_MAXACT     KLBG_BOTS
#define KLBG_MAXSLOT    0x10000
#define KLBG_EVERY_MS   250
#define KLBG_POLICE_MS  5000                  /* the police walk is the 8 MB table walk (~18 ms, klbotdown.c CensusSlice note): OnlyHeist=0 only */
#define KLBG_RESCAN_MS  10000

struct klbg_rt { DWORD pane; int slot; DWORD target; };       /* one pane: object, entity-table slot, resolved visible object */
struct klbg_act { DWORD actor; float x, y, z, dx, dz; DWORD t; int have; struct klbg_bot b; };

static struct {
    int on, heist, online, log, dry, facing; float reach, still, vert, face_cos; DWORD dwell;
    DWORD rules, at, last_scan, police_at; int scans, np, na, told_code, told_off, broke;
    struct klbg_rt rt[KLBG_PANES]; struct klbg_pane p[KLBG_PANES]; int tries[KLBG_PANES];
    struct klbg_act a[KLBG_MAXACT];
    DWORD police[KLBG_MAXACT]; int npol;
} klbg;

/* the call and its guards. -> 1 when the code is the one this reading was made on. */
static int klbg_callable(void)
{
    static const BYTE c[16] = { 0x6a, 0xff, 0x68, 0x68, 0xad, 0xac, 0x00, 0x64, 0xa1, 0x00, 0x00, 0x00, 0x00, 0x50, 0x83, 0xec };      /* 0x8d1b60 */
    int ok = klh_rd32((DWORD_PTR)KLH_VA(KLBG_VT + 4 * 26)) == KLBG_SLOT26 && klb_same_code(KLBG_ACTIVATE, c, sizeof c);
    if (!ok && !klbg.told_code++) klog("botglass: the glass 'Activate' routine (0x8d1b60, vtable 0xbb105c slot 26 = 0x471410) is not the one this build knows: nothing is called");
    return ok;
}

static int klbg_do(DWORD pane)
{
    __try { ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLBG_ACTIVATE))((void *)(DWORD_PTR)pane, 0); }
    __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    return 1;
}

static int klbg_finite(float f) { return f == f && f > -1e8f && f < 1e8f; }

/* the pane's world place: the node of its visible object (GUESS +4), pure handle lookup 0x8ccde0 under SEH */
static int klbg_pane_pos(DWORD pane, DWORD *target, float pos[3])
{
    DWORD h = klh_rd32(pane + 0x88), t = 0;
    if (!h) return 0;
    __try { t = ((DWORD (__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(0x008ccde0))(h); } __except (EXCEPTION_EXECUTE_HANDLER) { t = 0; }
    if (t < 0x10000) return 0;
    *target = t;
    return kle_node(klh_rd32(t + 4), pos, 0) && klbg_finite(pos[0]) && klbg_finite(pos[1]) && klbg_finite(pos[2]);
}

/* one walk of the entity table: the panes (always) and, when want_police, the soldiers that are not crew (filled by the caller after). */
static void klbg_scan(int want_police)
{
    DWORD p, tab, i, blk[64 * 32]; int np = 0, npol = 0, seen = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLBG_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < KLBG_MAXSLOT; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], vt;
            if (o < 0x10000) continue;
            vt = klh_rd32(o);
            if (vt == KLBG_VT) {
                float pos[3] = { 0, 0, 0 }; DWORD t = 0; int ok = klbg_pane_pos(o, &t, pos);
                seen++;
                if (klbg.scans == 1 || klbg.log >= 2) klog("botglass: pane %d at slot %lu object %08lx: %s(%.0f, %.0f, %.0f)%s", seen - 1, (unsigned long)(i + k), (unsigned long)o,
                    ok ? "" : "NO PLACE (skipped) ", pos[0], pos[1], pos[2], klh_rd32(o + 0x30) & 1 ? " already broken" : "");
                if (ok && np < KLBG_PANES) {
                    klbg.rt[np].pane = o; klbg.rt[np].slot = (int)(i + k); klbg.rt[np].target = t;
                    klbg.p[np].id = (int)o; klbg.p[np].x = pos[0]; klbg.p[np].y = pos[1]; klbg.p[np].z = pos[2];
                    klbg.p[np].broken = (int)(klh_rd32(o + 0x30) & 1);
                    np++;
                }
            } else if (want_police && npol < KLBG_MAXACT && klh_avt(o) == KLBG_ACTOR_VT) {
                DWORD s = klh_rd32(o + 0x77c);
                if (s && klh_svt(s) == KLBG_SOLDIER_VT && klh_rd32(s + 0x40) == o) klbg.police[npol++] = o;
            }
        }
    }
    if (np != klbg.np || klbg.scans == 1) klog("botglass: %d pane(s) found (%d seen%s) in round scan %d", np, seen, seen > KLBG_PANES ? ", the rest ignored: KLBG_PANES" : "", klbg.scans);
    klbg.np = np;
    if (want_police) { klbg.npol = npol; klbg.police_at = GetTickCount(); }
}

static void klbg_forget(void)
{
    if (klbg.rules && klbg.log) klog("botglass: round left (%d pane(s) broken by the hook)", klbg.broke);
    klbg.rules = 0; klbg.np = klbg.na = klbg.npol = klbg.scans = klbg.broke = 0; klbg.last_scan = klbg.police_at = 0;
    memset(klbg.a, 0, sizeof klbg.a); memset(klbg.tries, 0, sizeof klbg.tries);
}

/* the bot's (actor) record in klbg.a: found or taken */
static struct klbg_act *klbg_slot(DWORD actor)
{
    int i, free_i = -1;
    for (i = 0; i < klbg.na; i++) if (klbg.a[i].actor == actor) return &klbg.a[i];
    if (klbg.na < KLBG_MAXACT) { free_i = klbg.na++; memset(&klbg.a[free_i], 0, sizeof klbg.a[free_i]); klbg.a[free_i].actor = actor; return &klbg.a[free_i]; }
    return 0;
}

static int klbg_alive(DWORD actor)
{
    DWORD h = klh_rd32(actor + 0x5fc); float hp = 0; BYTE dn = 0;
    if (!h || klh_rd32(h + 0x24) != actor || !klh_rd(h + 4, &hp, 4) || !klbg_finite(hp) || hp <= 0.01f) return 0;
    if (klh_rd(actor + 0x64c, &dn, 1) && dn) return 0;              /* down (klbotdown.c): lying, not walking */
    return 1;
}

static void klbg_bot(DWORD actor, DWORD now)
{
    struct klbg_act *a; float pos[3], dir[3] = { 1, 0, 0 }, speed = 1e9f; struct klbg_pane pp[KLBG_PANES]; int face[KLBG_PANES], i, hit, np = klbg.np;
    struct klbg_cfg c;
    if (!actor || !klbg_alive(actor) || !(a = klbg_slot(actor))) return;
    if (!kle_node(klh_rd32(actor + 4), pos, dir) || !klbg_finite(pos[0]) || !klbg_finite(pos[2])) return;
    if (a->have && (long)(now - a->t) >= 150) { float dx = pos[0] - a->x, dz = pos[2] - a->z; speed = sqrtf(dx * dx + dz * dz) * 1000.0f / (float)(now - a->t); }
    a->x = pos[0]; a->y = pos[1]; a->z = pos[2]; a->t = now; a->have = 1;
    if (speed >= 1e8f) return;                                      /* the first sight of this bot: no speed yet */
    a->b.x = pos[0]; a->b.z = pos[2];
    memcpy(pp, klbg.p, sizeof pp);
    for (i = 0; i < np; i++) {
        float dx = klbg.p[i].x - pos[0], dz = klbg.p[i].z - pos[2], l = sqrtf(dx * dx + dz * dz);
        if (klh_rd32(klbg.rt[i].pane + 0x30) & 1) pp[i].broken = 1;          /* already broken */
        if (klh_rd32(klbg.rt[i].pane) != KLBG_VT || klbg.tries[i] >= 2) pp[i].broken = 1;       /* gone / freed / tried twice */
        if (fabsf(klbg.p[i].y - pos[1]) > klbg.vert) pp[i].broken = 1;       /* another floor */
        face[i] = 1;
        if (klbg.facing && l > 1.0f) { float fl = sqrtf(dir[0] * dir[0] + dir[2] * dir[2]); face[i] = fl > 0.01f && (dir[0] * dx + dir[2] * dz) / (fl * l) >= klbg.face_cos; }
    }
    c.reach_cm = klbg.reach; c.still_cms = klbg.still; c.dwell_ms = klbg.dwell; c.only_heist = klbg.heist;
    hit = klbg_step_f(&a->b, pp, np, &c, speed, 0, klbg.facing ? face : 0, now);
    if (hit < 0) return;
    {
        DWORD pane = klbg.rt[hit].pane; long dwell = (long)(now - a->b.t_near[hit]);
        if (klbg.dry) { klog("botglass: DRY: bot %08lx would break pane %d (slot %d, %08lx) at %.0f, %.0f, %.0f: %.0f cm away, %.0f cm/s, blocked %ld ms", (unsigned long)actor, hit, klbg.rt[hit].slot, (unsigned long)pane,
                klbg.p[hit].x, klbg.p[hit].y, klbg.p[hit].z, sqrtf((klbg.p[hit].x - pos[0]) * (klbg.p[hit].x - pos[0]) + (klbg.p[hit].z - pos[2]) * (klbg.p[hit].z - pos[2])), speed, dwell); klbg.tries[hit] = 2; return; }
        if (!klbg_callable() || !klh_rd32((DWORD_PTR)KLH_VA(KLBG_GLOBAL_ON))) { if (!klbg.told_off++ && klbg.log) klog("botglass: the game's glass switch [0xce513c] is 0 (or the code is unknown): nothing is called"); return; }
        klbg.tries[hit]++;
        if (!klbg_do(pane)) { klog("botglass: bot %08lx: the break of pane %d (%08lx) FAULTED (caught): not tried again", (unsigned long)actor, hit, (unsigned long)pane); klbg.tries[hit] = 2; return; }
        if (klh_rd32(pane + 0x30) & 1) { klbg.broke++; klbg.p[hit].broken = 1; }
        if (klbg.log) klog("botglass: bot %08lx at (%.0f, %.0f, %.0f) %s pane %d (slot %d, %08lx) %.0f cm away after %ld ms at %.0f cm/s%s",
            (unsigned long)actor, pos[0], pos[1], pos[2], (klh_rd32(pane + 0x30) & 1) ? "BROKE" : "asked for the break of", hit, klbg.rt[hit].slot, (unsigned long)pane,
            sqrtf((klbg.p[hit].x - pos[0]) * (klbg.p[hit].x - pos[0]) + (klbg.p[hit].z - pos[2]) * (klbg.p[hit].z - pos[2])), dwell, speed,
            (klh_rd32(pane + 0x30) & 1) ? "" : " - the pane is NOT marked broken (the call returned without breaking; tried at most twice)");
    }
}

static void klbg_tick(int game_thread)
{
    struct klb_snap sn; DWORD rules, state, now; int level, online = 0, i; char why[200];
    if (!klbg.on || !game_thread || !klh_exe_ok) return;
    if (klcmp_level_active()) return;                    /* a campaign level: not an FA round */
    now = GetTickCount();
    if (klbg.at && (long)(now - klbg.at) < KLBG_EVERY_MS) return;
    klbg.at = now; why[0] = 0;
    if (klr_arcade(&rules, &state, &level) && klb_level(why) && state == 0x19 && klb_read(&sn) && sn.state == 0x19) online = 0;
    else if (klbg.online && (online = klbd_online_view(2, &sn, why)) < 0) return;      /* settings unreadable this instant: change nothing */
    else if (klbg.online && online) online = 1;
    else { if (klbg.rules) klbg_forget(); return; }
    if (sn.rules != klbg.rules) {
        klbg_forget(); klbg.rules = sn.rules;
        klog("botglass: a round runs (%s); %s; Reach %.0f cm, Still %.0f cm/s, Dwell %lu ms, Vert %.0f cm, Facing %d%s", online ? "ONLINE host" : "Arcade", klbg.heist ? "AI heisters only" : "AI heisters and police", klbg.reach, klbg.still,
             (unsigned long)klbg.dwell, klbg.vert, klbg.facing, klbg.dry ? " - Dry: nothing is called" : "");
    }
    /* the panes: once per round; while none was found again every 10 s, three times (the level may still be creating its objects) */
    if (!klbg.scans || (!klbg.np && klbg.scans < 4 && (long)(now - klbg.last_scan) >= KLBG_RESCAN_MS)) { klbg.scans++; klbg.last_scan = now; klbg_scan(!klbg.heist); }
    else if (!klbg.heist && klbg.np && (long)(now - klbg.police_at) >= KLBG_POLICE_MS) klbg_scan(1);
    if (!klbg.np) return;
    for (i = 0; i < sn.n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &sn.r[i];
        if (!r->used || !(r->flags & 1) || r->status != 0 || !r->actor) continue;      /* AI heisters in play only (the human, aboard, escaped, dead are not) */
        if (klh_avt(r->actor) != KLBG_ACTOR_VT) continue;
        klbg_bot(r->actor, now);
    }
    if (!klbg.heist) for (i = 0; i < klbg.npol; i++) {
        int j, crew = 0;
        for (j = 0; j < sn.n && j < KLB_NREC; j++) if (sn.r[j].used && sn.r[j].actor == klbg.police[i]) crew = 1;
        if (!crew) klbg_bot(klbg.police[i], now);
    }
}

static void klbg_init(void)
{
    char t[40];
    memset(&klbg, 0, sizeof klbg);
    klbg.on = GetPrivateProfileIntA("BotGlass", "Enable", 0, klh_ini) != 0;
    if (!klbg.on) return;
    klbg.heist = GetPrivateProfileIntA("BotGlass", "OnlyHeist", 1, klh_ini) != 0;
    klbg.online = GetPrivateProfileIntA("BotGlass", "Online", 0, klh_ini) != 0;
    klbg.log = GetPrivateProfileIntA("BotGlass", "Log", 1, klh_ini);
    klbg.dry = GetPrivateProfileIntA("BotGlass", "Dry", 0, klh_ini) != 0;
    klbg.facing = GetPrivateProfileIntA("BotGlass", "Facing", 0, klh_ini) != 0;
    klbg.reach = (float)GetPrivateProfileIntA("BotGlass", "Reach", 250, klh_ini); if (klbg.reach < 50) klbg.reach = 50; if (klbg.reach > 1500) klbg.reach = 1500;
    klbg.still = (float)GetPrivateProfileIntA("BotGlass", "Still", 30, klh_ini); if (klbg.still < 0) klbg.still = 0; if (klbg.still > 300) klbg.still = 300;
    klbg.vert = (float)GetPrivateProfileIntA("BotGlass", "Vert", 300, klh_ini); if (klbg.vert < 50) klbg.vert = 50; if (klbg.vert > 2000) klbg.vert = 2000;
    klbg.dwell = (DWORD)GetPrivateProfileIntA("BotGlass", "DwellMs", 1500, klh_ini); if (klbg.dwell < 250) klbg.dwell = 250; if (klbg.dwell > 60000) klbg.dwell = 60000;
    GetPrivateProfileStringA("BotGlass", "FacingCos", "0.3", t, sizeof t, klh_ini);
    klbg.face_cos = (float)atof(t); if (!(klbg.face_cos == klbg.face_cos) || klbg.face_cos < -1.0f || klbg.face_cos > 1.0f) klbg.face_cos = 0.3f;
    klog("botglass: on (%s; Reach %.0f, Still %.0f, DwellMs %lu, Vert %.0f, Facing %d, Online %d, Dry %d): a bot standing at an intact glass pane makes it break through the pane's own 'Activate' (0x8d1b60)",
         klbg.heist ? "heisters" : "heisters + police", klbg.reach, klbg.still, (unsigned long)klbg.dwell, klbg.vert, klbg.facing, klbg.online, klbg.dry);
}
