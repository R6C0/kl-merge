/*
 * klpm_gun.c - KLMGun, the STARTING GUN of the private-match options (re\pm_options.md B0 / 8.1a, 2026-10-18). Included by klhook.c after
 * klpm_arc.c. Off unless [Match] Enable=1 and the menu row KLMGun is 1..36. DATA writes only (no code byte of kl2.exe).
 *
 * HOW (static reading of kl2.exe; NOT run in the game - every GUESS is marked):
 *   The round-start loadout 0x42bc80 (call at 0x42bd3c; the same in 0x74abc0 at 0x74ac22) reads entry 0 of the rules' crew table,
 *   [[0x168e9e4]+0x54]+0x348 (stride 0x7c), follows its dword 0 to a client block and calls the loadout routine
 *   0x410710(weapons, player, block[3], block[4], block[5]) = (pistol row, rifle row, suit row). No money check is on that path (the shop
 *   buy 0x8ea990 / 0x55d3e0 prices the rows and then writes the same bytes). So: write block[3] or block[4] with the chosen shop row BEFORE
 *   the round starts, the loadout hands that gun over and no money is taken.
 *   Defaults seen in the routine: row 0 (M-77B) in byte 3, row 28 (Zastava) in byte 4.
 * SAFETY: the weapon pool must hold a FREE object of the gun's item (and of the other slot's), else the pool raises an int3 (0x538f02):
 *   no free object = nothing is written and the reason is logged. Written once per (rules object, value); the previous byte is put back when
 *   the row goes back to 0 or another gun is chosen, so a gun bought in the shop is not erased by us after the first write.
 * GUESSes: (1) byte 0 of the client block is 0 for the local player; (2) the block exists before the round (else we wait, bounded);
 *   (3) a row works in either slot; (4) Arcade (session mode 4, ZGameRulesHeist) only - online (FA, other rules vtables) is not touched.
 */
#ifndef KLPM_GUN_C
#define KLPM_GUN_C

#define KPG_SESSION  0x0168e598
#define KPG_SETTINGS 0x0168e9e4
#define KPG_WEAPONS  0x0168e96c
#define KPG_SHOP     0x00bd1f68
#define KPG_RULES_VT 0x00bd3514
#define KPG_ROUND    0x19

static struct { DWORD rules, block; int value, slot; BYTE prev, done; int waited; } kpg;

/* free objects of an item in the weapon pool (byte +8 set, byte +9 clear, no owner); -1 = pool unreadable */
static int kpg_free(DWORD item)
{
    DWORD w, a, n = 0, ents, i, e[3], owner; int c = 0;
    if (!(w = klh_rd32((DWORD_PTR)KLH_VA(KPG_WEAPONS))) || !(a = klh_rd32(w)) || !klh_rd(a + 4, &n, 4) || !n || n > 4096 || !(ents = klh_rd32(a + 0x10))) return -1;
    for (i = 0; i < n; i++) {
        if (!klh_rd(ents + 12 * i, e, 12)) return -1;
        if (e[1] != item || !e[0]) continue;
        owner = 1; if (!klh_rd(e[0] + 0x5c, &owner, 4)) owner = 1;
        if (!(e[2] & 0xff00) && !owner && (e[2] & 0xff)) c++;
    }
    return c;
}

static void kpg_restore(void)
{
    if (kpg.done && kpg.block && kpg.slot) {
        BYTE cur = 0;
        if (klh_rd(kpg.block + kpg.slot, &cur, 1) && cur == (BYTE)(kpg.value - 1) &&
            klh_data((void *)(DWORD_PTR)(kpg.block + kpg.slot), &kpg.prev, 1, "KLMGun: previous crew-record gun row"))
            klog("match: gun: row put back to %u", (unsigned)kpg.prev);
    }
    memset(&kpg, 0, sizeof kpg);
}

/* every frame; cheap exits first. Only before the round runs (the loadout has not read the bytes yet). */
static void kpm_gun_tick(void)
{
    DWORD sm, gs, rules, recs, blk, st = 0, item = 0; int v, slot, f1, f2; BYTE b0 = 1, row;
    if (!kpm_on) return;
    v = kpm_get(0); slot = kpm_gun_slot(v);
    if (kpg.done && (v != kpg.value)) kpg_restore();
    if (!slot || (kpg.done && kpg.value == v) || kpg.waited > 600) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KPG_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x70, &st, 4)) return;   /* Arcade only */
    if (st == KPG_ROUND) { if (!kpg.waited++) klog("match: gun: the round already runs; the next round gets the gun"); return; }
    if (kl_online()) return;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KPG_SETTINGS))) || !(rules = klh_rd32(gs + 0x54)) || klh_rd32(rules) != (DWORD)(DWORD_PTR)KLH_VA(KPG_RULES_VT)) return;
    if (!(recs = klh_rd32(rules + 0x348)) || !(blk = klh_rd32(recs)) || !klh_rd(blk, &b0, 1) || b0) return;      /* GUESS: byte 0 = 0 for the local player */
    row = (BYTE)(v - 1);
    if (!(item = klh_rd32((DWORD_PTR)KLH_VA(KPG_SHOP) + 24 * row))) return;
    f1 = kpg_free(item); f2 = kpg_free(klh_rd32((DWORD_PTR)KLH_VA(KPG_SHOP) + 24 * (slot == 3 ? 28 : 0)));
    if (f1 < 2 || f2 < 1) {
        if (!kpg.waited++ || kpg.waited == 600) klog("match: gun: row %u NOT equipped - the weapon pool has %d free of its item (2 needed) and %d of the other slot's (1); a level without a template of it would stop at an int3", (unsigned)row, f1, f2);
        return;
    }
    if (kpg.block != blk && kpg.done) memset(&kpg, 0, sizeof kpg);
    if (!klh_rd(blk + slot, &kpg.prev, 1)) return;
    if (!klh_data((void *)(DWORD_PTR)(blk + slot), &row, 1, "KLMGun: crew-record gun row")) return;
    kpg.rules = rules; kpg.block = blk; kpg.value = v; kpg.slot = slot; kpg.done = 1;
    klog("match: gun: shop row %u (item %lu) written to crew-record byte %d (was %u); free in pool %d/%d; the round-start loadout equips it, no money taken (static reading, GUESS until run)", (unsigned)row, item, slot, (unsigned)kpg.prev, f1, f2);
}

#endif /* KLPM_GUN_C */
