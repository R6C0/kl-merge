/* klcensus.c - [Census] READ-ONLY list of every ZFFActor in the scene entity table (2026-10-18).
 *
 * Why: the owner saw no civilians on Last Call (DM05A club_civs4), and a scripted walk past the ten posts saw none either
 * (run N1018_L7_DM05A_civlook4). Nothing in the hook could tell "never created" from "ran away at the round start" from
 * "created but not drawn". This prints, every Every ms, one line per ZFFActor (cops, guards, civilians, bots, you):
 * slot, object, position, health. Civilians are told apart by position (the builder's civs.json posts / flee points):
 * the team field's offset is not known.
 *
 * Walk = klcensor.c klcn_scan / the heli probe: [[[KLE_ENTS]+0xc]+0xc] = table, 0x80 bytes a slot, object at slot+0x60,
 * vtable 0xbb3bac = ZFFActor. Position = kle_node([actor+4]). Health object [actor+0x5fc]: +4 current, +8 maximum
 * (as klbot.c / klbotdown_test.c read them). Nothing is written.
 *
 * KEYS ([Census]): Enable=0  Every=2000 (ms between lists, at least 250)  Max=300 (lines a list)
 */
static struct { int on, max; DWORD every, at; } klcs;

static void klcs_tick(int game_thread)
{
    DWORD p, tab, i, blk[64 * 32], now = GetTickCount(); int n = 0;
    if (!klcs.on || !game_thread || !klx_on) return;
    if (klcs.at && now - klcs.at < klcs.every) return;
    klcs.at = now;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x10000 && n < klcs.max; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < klcs.max; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], h; float pos[3] = { 0, 0, 0 }, hp[2] = { 0, 0 }; int hv, pv;
            if (o < 0x10000 || klh_rd32(o) != KLCN_ACTOR_VT) continue;
            pv = kle_node(klh_rd32(o + 4), pos, 0);
            h = klh_rd32(o + 0x5fc); hv = h && klh_rd(h + 4, hp, 8);
            klog("census: #%d slot %lu actor %08lx %s(%.0f, %.0f, %.0f) health %s%.1f of %.1f", n, (unsigned long)(i + k), (unsigned long)o,
                 pv ? "" : "NO PLACE ", pos[0], pos[1], pos[2], hv ? "" : "? ", hp[0], hp[1]);
            n++;
        }
    }
    klog("census: %d ZFFActor in the entity table", n);
}

static void klcs_init(void)
{
    klcs.on = GetPrivateProfileIntA("Census", "Enable", 0, klh_ini) != 0;
    klcs.every = GetPrivateProfileIntA("Census", "Every", 2000, klh_ini); if (klcs.every < 250) klcs.every = 250;
    klcs.max = GetPrivateProfileIntA("Census", "Max", 300, klh_ini); if (klcs.max < 1) klcs.max = 1;
    if (klcs.on) klog("census: on (read-only: every ZFFActor's place and health every %lu ms, at most %d lines)", (unsigned long)klcs.every, klcs.max);
}
