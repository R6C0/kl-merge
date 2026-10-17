/*
 * klpm_arc.c - B2 of re\pm_options.md: THE ARCADE PLAYLIST, game-facing half (2026-10-18). Part of KLHook; included by klhook.c AFTER klslot.c
 * (it reads klslot.c's slot / rule tables and menu-page latch). Pure parts (cursor, list, override): klpm.c, tested off-game in klpm_test.c.
 * OFF unless [Match] Enable=1 and Arcade=1, and a playlist mode is set (menu row KLMPlay, or [Match] Mode=).
 *
 * HOW THE ARCADE MAP IS CHOSEN (kl2.exe 0490, read statically 2026-10-18; nothing here ran in the game):
 *   - The Arcade map page is a ZMercsLevelSelectorHeist ("HeistLevel"), option Heist_SelectedLevel. Its per-frame update 0x459e90 calls
 *     its GetValue (vtbl+0x90) and copies the result to the global dword [0xceceec] (0x459eec); on StartGame (0x502b40, which sets
 *     the start-pending byte [0x156b73a]) the update calls 0x7e01a0: slot = 0x746570([0xceceec]) (menu position -> slot, table
 *     0,1,2,3,5,6,4,7,8), session vtbl+0x28(slot), SetMapName(slot15(slot)), load. (fa_slots.md 4, menus.md 4.1.)
 *   - Heist_SelectedLevel is NOT stored in the options object (that object is deleted with every menu manager, 0x673340..0x673388): its
 *     value is the plain byte [0x154d632]. Its only two code references in the whole image are the option's Set (0x47251e, `mov
 *     [0x154d632], cl`) and Get (0x504c09, `movzx eax, [0x154d632]`) - so nothing resets it, it outlives levels and menu rebuilds, and a
 *     write by this hook is exactly what the selector's own Set would do. (Also: re\expansion.md 10.2 "the page opens on the entry the
 *     profile played last".) GUESS: the selector reads the option when its page is built (that sentence is the only evidence), so a page
 *     opened AFTER our write shows the playlist map; a page that is already open keeps its own value.
 *   - Which folder the position loads: klslot.c's redirect, keyed by (slot, menu page). The page is latched from the window stack when the
 *     player opens HeistPlayMenu / HeistPlayMenu2.. . The playlist map lives on one page, so we also tell klslot.c (kpm_override, one
 *     line in kls_map) "for slot F07 use page 2" - then Accept loads the playlist map whichever page the player opened. If the player
 *     moves the selector to another slot the override does not apply (it is keyed by slot name) and the game behaves as stock.
 *
 * WHEN A MATCH ENDS (GUESS: the same scene-name test kljoin.c / klchar.c use for 'in a level'): klh_scene() names a level of Locations\F0n
 * before, and a scene that is not a level for 2 s after. Only a match that was started from the ARCADE page counts: at the level's start the
 * map page was latched (kls_menu_page, needs a [Redirect.N] page) or the start-pending byte was seen in the frontend. An online lobby start
 * has neither, so a Fragile Alliance lobby is never touched (that is R1, B5).
 *
 * WHAT IT DOES at the end: played = the map index of (slot, latched page) from klslot's rule (or maps.ini's Slot for a stock entry);
 * next = kpm_advance(); the byte [0x154d632] = kpm_slot_pos(next's slot) (klh_data, the guarded data write); kpm_ovr_set(slot, page);
 * Cursor= is written to KLHook.ini. The override is dropped 25 s after the next level has started (its archives are open by then) and
 * whenever the hook sees a level with a different slot.
 * NOT DONE: opening the map page by itself (the player still presses Arcade -> the page -> Accept); only the entry is pre-selected.
 *
 * Log lines: "playlist: ..." (every decision). Live checks: re\pm_options.md 9.
 */
#ifndef KLPM_ARC_C
#define KLPM_ARC_C

#define KPM_HEISTSEL 0x0154d632               /* byte: option Heist_SelectedLevel = the Arcade page's menu position 0..8 */

static int kpm_mode_now(void) { return kpm_v[2] ? (int)kpm_v[2] : kpm_ini_mode; }

/* the map index (maps.ini order) of the match that was loaded through klslot slot 'name' ("F07") on 'page'; -1 unknown */
static int kpm_played_index(const char *name, int page)
{
    int s, r, i, stock = -1;
    for (s = 0; s < kls_nslots; s++) if (!_stricmp(kls_slot[s].name, name)) break;
    if (s < kls_nslots) {
        r = kls_find_rule(s, page); if (r < 0 && page) r = kls_find_rule(s, 0);
        if (r >= 0) { for (i = 0; i < kpm_nmap; i++) if (!_stricmp(kpm_map[i].id, kls_rule[r].map)) return i; return -1; }
    }
    for (i = 0; i < kpm_nmap; i++) if (!_stricmp(kpm_map[i].slot, name)) {      /* a stock entry: the first map of that slot that has no redirect rule */
        int j, ruled = 0;
        for (j = 0; j < kls_nrules; j++) if (!_stricmp(kls_rule[j].map, kpm_map[i].id)) ruled = 1;
        if (!ruled) { stock = i; break; }
    }
    return stock;
}

/* the (slot, page) a map index loads through; -> 1 ok. A map with a redirect rule: that rule's slot and page (page 0 = every page -> the
 * stock page 1, which falls back to the always-rule). A stock entry: its maps.ini Slot, page 1. */
static int kpm_target_of(int mi, char *slot, int cap, int *page)
{
    int j;
    if (mi < 0 || mi >= kpm_nmap || cap < 4) return 0;
    for (j = 0; j < kls_nrules; j++) if (!_stricmp(kls_rule[j].map, kpm_map[mi].id)) {
        strncpy(slot, kls_slot[kls_rule[j].slot].name, cap - 1); slot[cap - 1] = 0;
        *page = kls_rule[j].page ? kls_rule[j].page : 1;
        return kpm_slot_idx(slot) >= 0;
    }
    if (kpm_slot_idx(kpm_map[mi].slot) < 0) return 0;
    strncpy(slot, kpm_map[mi].slot, cap - 1); slot[cap - 1] = 0; *page = 1;
    return 1;
}

static void kpm_arc_tick(void)
{
    static int inlvl, out_ms_set, arc, pend_seen; static char lvl_slot[8]; static DWORD lvl_at, out_at, shown_at; static int wrote_pos = -1, readback_due;
    char scene[200], key[64]; DWORD now; int lvl;
    if (!kpm_on || !kpm_arc_on || !klh_exe_ok) return;
    now = GetTickCount();
    lvl = klh_scene(scene, sizeof scene) && klh_level_key(scene, key, sizeof key) && key[0] == 'f' && key[1] == '0' && key[2] >= '1' && key[2] <= '9' && key[3] == '\\';
    if (!lvl) {
        BYTE pend = 0;
        if (klh_rd((DWORD_PTR)KLH_VA(KLS_STARTPEND), &pend, 1) && pend) pend_seen = 1;        /* Arcade's StartGame (0x502b40); one frame only */
        if (inlvl) {
            if (!out_ms_set) { out_ms_set = 1; out_at = now; }
            if ((LONG)(now - out_at) >= 2000) {                                                 /* the level is gone for 2 s: the match ended */
                int mode = kpm_mode_now(), played, next, page = 1, pos; char slot[8], pl[8];
                inlvl = 0; out_ms_set = 0;
                strcpy(pl, lvl_slot);
                if (!arc) { klog("playlist: %s ended - not an Arcade match (no map page latched, no start seen): left alone", pl); pend_seen = 0; return; }
                arc = 0; pend_seen = 0;
                if ((LONG)(out_at - lvl_at) < 5000) { klog("playlist: %s was in for %ld ms only: not counted", pl, (long)(out_at - lvl_at)); return; }
                if (!mode || kpm_nlist <= 0) { klog("playlist: %s ended; the playlist is off (mode %d, %d map(s))", pl, mode, kpm_nlist); kpm_ovr_set(0, -1); return; }
                {   int latched = -1, s; for (s = 0; s < kls_nslots; s++) if (!_stricmp(kls_slot[s].name, pl)) latched = (int)kls_slot[s].page;
                    played = kpm_played_index(pl, latched < 0 ? 1 : latched); }
                next = kpm_advance(mode, kpm_list, kpm_nlist, &kpm_cursor, kpm_seed, played);
                if (next < 0 || !kpm_target_of(next, slot, sizeof slot, &page) || (pos = kpm_slot_pos(kpm_slot_idx(slot))) < 0) {
                    klog("playlist: %s ended (played %d); next %d has no usable slot (maps.ini Slot= / [Redirect])", pl, played, next); kpm_ovr_set(0, -1); return;
                }
                {   char c[16]; snprintf(c, sizeof c, "%d", kpm_cursor); WritePrivateProfileStringA("Match", "Cursor", c, klh_ini); }
                kpm_ovr_set(slot, page);
                { BYTE b = (BYTE)pos, was = 0xff; klh_rd((DWORD_PTR)KLH_VA(KPM_HEISTSEL), &was, 1);
                  if (klh_data((void *)KLH_VA(KPM_HEISTSEL), &b, 1, "Heist_SelectedLevel (playlist)")) { wrote_pos = pos; readback_due = 1; shown_at = now; }
                  klog("playlist: %s ended (played map %d); mode %d, cursor %d -> next map %d '%s' = slot %s page %d, Arcade position %d (Heist_SelectedLevel was %u, %s)",
                       pl, played, mode, kpm_cursor, next, kpm_map[next].id, slot, page, pos, was, wrote_pos == pos ? "written" : "NOT written: refused"); }
            }
        }
        if (readback_due && (LONG)(now - shown_at) > 4000) {                                      /* once: did the byte survive the frontend's start-up? */
            BYTE b = 0xff; readback_due = 0; klh_rd((DWORD_PTR)KLH_VA(KPM_HEISTSEL), &b, 1);
            klog("playlist: Heist_SelectedLevel reads %u 4 s after (wrote %d)%s", b, wrote_pos, b == wrote_pos ? "" : " - CHANGED by something else (GUESS about the selector failed?)");
        }
        return;
    }
    out_ms_set = 0;
    if (!inlvl) {                                                                                 /* a level starts */
        inlvl = 1; lvl_at = now; wrote_pos = -1; readback_due = 0;
        lvl_slot[0] = 'F'; lvl_slot[1] = '0'; lvl_slot[2] = key[2]; lvl_slot[3] = 0;
        arc = kls_menu_page != 0 || pend_seen;
        if (kpm_ovr_page >= 0 && _stricmp(lvl_slot, kpm_ovr_slot)) { klog("playlist: level %s is not the playlist slot %s: override dropped", lvl_slot, kpm_ovr_slot); kpm_ovr_set(0, -1); }
        klog("playlist: level %s started (%s)", lvl_slot, arc ? "from the Arcade page" : "not from the Arcade page");
    }
    if (kpm_ovr_page >= 0 && (LONG)(now - lvl_at) > 25000) { klog("playlist: override for %s dropped (the level has been in for 25 s)", kpm_ovr_slot); kpm_ovr_set(0, -1); }
}

#endif /* KLPM_ARC_C */
