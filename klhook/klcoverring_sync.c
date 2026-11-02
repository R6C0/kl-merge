/*
 * klcoverring_sync.c - [CoverRing] ClientRingSync=1 (CR8, 2026-11-02): the host's car cover points -> the client. NOT RUN IN THE GAME.
 * Included by klhook.c AFTER klsync.c (uses klsy.sock / klsy.sendto / klsy_sin / klsy_T / KLSY_PORT) and after klcoverring.c (kcr state, kcr_scan, kcr_cb_points, kcr_rd8).
 * Why (re/dm_car_cover_1101.md, CR7 notes): the writer 0x81b6f0 derives each point from the car's world matrix at the instant of the call, and the car is physics-driven and
 * (GUESS: RTTI has no ZHavokCar net sync) not replicated, so the same car yields a different ring per seat (DM03 car #0: yaw ~11 deg on the host, 0 on the client; host spares 557/558,
 * client spare 561). A point usable on the host but spare on the client can still int3 on the client (0x656740 accepts bit 2 or 0x200 only).
 * HOST (klsy_tick, role 2, game type 4, slot in ClientBuildMaps): once per KCR_RS_MS, for every car with a built ring (done 1, 1..8 indices inside the points vector) one 'KLSYR'
 *   UDP packet (broadcast, same socket as KLSYV / KLSYB; an old receiver skips an unknown magic): the 8 points' flags [pt+0x68], position [pt+0x28], [pt+0x40..0x63], [pt+0x24].
 * CLIENT (klsy_tick drain, role 3, ClientBuild finished clean): for each point where the host's is usable and the client's is a spare (kcr_ring_apply_decision), write the host's
 *   fields into the client's heap point; flags LAST. A usable client point is never touched (stage 1). The index must be one of the client's own car's ring indices (car = the
 *   host's ordinal in entity-table order, GUESS: same on both seats) and < the points vector; 20 mismatches turn the feature off for the run.
 * GUESS list: (1) the entity-table ordinal is equal on both seats (verified per packet by the index ownership check, not assumed); (2) copying flags 0x140a / 0x1412 verbatim is
 *   harmless (the extra 0x400 is a "persisted" mark, bit 2 is what the assert tests); (3) +0x40..0x63 are plain per-point data (0x8a7d90 fills them from the direction vector);
 *   +0x24 is the car's SEAT-LOCAL handle (0x6ece90 -> 0x86ca10 table index + 1), so the client writes its own value from a usable sibling point and the host's only as a fallback;
 *   (4) the nav-side record [L+0x58]+idx*0x2c is NOT registered here. Nav study 11-02 (static, verified twice): an unregistered record is in no bucket, release on it is a
 *   no-op, the asserts 0x6567e8 / 0x656913 test only +0x68, and no reader of L's group was found, so registering would add risk (a stale bucket link) for no use. Do NOT replay
 *   0x9015d0 on the client: its 'and 0x78' rewrites the flags and a bad mode int3s.
 * No debug register, no code or vtable patch: heap writes inside __try only.
 * LINES: 'coverring: ringsync HOST ...' / 'coverring: ringsync CLIENT ...'.
 */
#ifndef KLCOVERRING_SYNC_C
#define KLCOVERRING_SYNC_C

/* HOST: called from klsy_tick every tick when role == 2 (cheap exit unless due) */
static void kcr_rs_host(DWORD now)
{
    DWORD gd, st, L, rb, rn, pb = 0, pe = 0, npts, i, sent = 0; int sm_ok;
    DWORD sm, role = 0, mode = 0; char scene[200], key[120];
    if (!kcr.rs || kcr.rs_bad || !klsy.sock) return;
    if (kcr.rs_t && now - kcr.rs_t < KCR_RS_MS) return;
    kcr.rs_t = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !KLH_SM_VT_OK(klh_rd32(sm)) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4)) return;
    sm_ok = mode == 4ul && role == 2ul;
    key[0] = 0;
    if (!sm_ok || !klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key) || !kcr_cb_map_listed(kcr.cb_maps, key)) return;
    __try {
        if (!kcvd_state(&gd, &st) || st > KCR_CB_MAXSTATE) return;
        if (!kcvd_read_list(gd, &L, &rb, &rn, &pb, &pe)) return;
        npts = (pe >= pb && pe - pb < 0x4000000u) ? (pe - pb) / 0x7c : 0;
        if (!npts) return;
        if (!kcr.t_scan || now - kcr.t_scan >= 2000u) kcr_scan();
        for (i = 0; i < kcr.ncars && sent < KCR_RS_MAXCARS; i++) {
            DWORD car = kcr.c[i].car, s = klh_rd32(car + 0x968), n, k; unsigned long idx[8]; struct kcr_rhdr h; struct kcr_rpt pt[8]; unsigned char pk[KCR_RS_HDR + KCR_RS_MAXN * KCR_RS_REC]; int len, r, good = 0;
            klsy_sin a;
            if (!kcvd_ptr_ok(s) || !kcr_script_matches(car, klh_rd32(s + 0x40))) continue;
            n = klh_rd32(s + 0x1c4);
            for (k = 0; k < 8; k++) idx[k] = klh_rd32(s + 0x1c8 + k * 4);
            if (!kcr_rs_car_sendable(kcr_rd8(s + 0x1e8), n, idx, npts)) continue;
            memset(pt, 0, sizeof pt);
            for (k = 0; k < n; k++) {
                DWORD pp = pb + idx[k] * 0x7c;
                pt[k].idx = idx[k];
                if (!klh_rd(pp + 0x68, &pt[k].flags, 4) || !klh_rd(pp + 0x28, pt[k].pos, 12) || !klh_rd(pp + 0x40, pt[k].blk, 36) || !klh_rd(pp + 0x24, &pt[k].f24, 4)) { n = 0; break; }
                good += kcr_pt_usable(pt[k].flags);
            }
            if (!n) continue;
            kcr.rs_seq = (int)kcr_rs_next_seq((unsigned)kcr.rs_seq);
            h.T = (DWORD)klsy_T(); h.seq = (unsigned)kcr.rs_seq; h.ord = i; h.n = n;
            len = kcr_ring_pack(pk, sizeof pk, &h, pt);
            if (!len) continue;
            memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
            r = klsy.sendto(klsy.sock, (const char *)pk, len, 0, &a, sizeof a);
            sent++;
            if (kcr.rs_nrx < 3 || kcr.rs_nrx % 60 == 0)      /* rs_nrx counts HOST sends here */
                klog("coverring: ringsync HOST car #%lu seq %u sent %d bytes (sendto %d): %lu points, %d usable, first idx %lu flags %03lx pos (%.0f,%.0f,%.0f)", (unsigned long)i, h.seq, len, r,
                     (unsigned long)n, good, pt[0].idx, pt[0].flags, pt[0].pos[0], pt[0].pos[1], pt[0].pos[2]);
            kcr.rs_nrx++;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        kcr.rs_bad = 1;
        klog("coverring: ringsync HOST exception - off for the rest of the run");
    }
}

/* CR9 11-02: the CHANGED line came every second for the same moved points; log each index once per load (list cleared while
   rs_nchg is 0, i.e. after kcr_rearm; past 16 indices the 40-line cap still holds) */
static unsigned long kcr_rs_told[16]; static int kcr_rs_ntold;
static int kcr_rs_chg_first(unsigned long idx)
{
    int i;
    if (!kcr.rs_nchg) kcr_rs_ntold = 0;
    for (i = 0; i < kcr_rs_ntold; i++) if (kcr_rs_told[i] == idx) return 0;
    if (kcr_rs_ntold < 16) kcr_rs_told[kcr_rs_ntold++] = idx;
    return 1;
}

/* CLIENT: a KLSYR arrived (klsy_tick drain, game thread) */
static void kcr_rs_rx(const char *pk, int len, DWORD now, unsigned long from)
{
    struct kcr_rhdr h; struct kcr_rpt pt[8]; int n, k, wrote = 0, skipped_used = 0, skipped_host = 0, mis = 0; static int toldmis, toldsrc;
    DWORD sm, role = 0, mode = 0, gd, st, L, rb, rn, pb = 0, pe = 0, npts, car, s, cn = 0, i, own24 = 0; int have24 = 0; unsigned long own[8]; char scene[200], key[120];
    if (!kcr.rs || kcr.rs_bad) return;
    n = kcr_ring_unpack((const unsigned char *)pk, len, &h, pt);
    if (!n) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !KLH_SM_VT_OK(klh_rd32(sm)) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !kcr_cb_role_ok(role, mode, 0)) return;
    if (!kcr.cb || !kcr.cb_done || kcr.cb_bad) return;                       /* ClientBuild must have finished clean: the client's own ring indices exist */
    key[0] = 0;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key) || !kcr_cb_map_listed(kcr.cb_maps, key)) return;
    /* only the host: the sync list's locked source when there is one, else the first KLSYR sender of this load (review CR8: an unchecked LAN peer could fill spares) */
    if ((klsy.srcSet && from != klsy.srcAddr) || (kcr.rs_srcset && from != kcr.rs_src)) {
        if (toldsrc++ < 3) klog("coverring: ringsync CLIENT a packet from %lu.%lu.%lu.%lu ignored (not the pinned host)", from & 255, from >> 8 & 255, from >> 16 & 255, from >> 24);
        return;
    }
    if (!kcr.rs_srcset) { kcr.rs_srcset = 1; kcr.rs_src = from; }
    kcr.rs_nrx++; memset(own, 0, sizeof own);
    __try {
        if (!kcvd_state(&gd, &st) || st > KCR_CB_MAXSTATE || !kcvd_read_list(gd, &L, &rb, &rn, &pb, &pe)) return;
        npts = (pe >= pb && pe - pb < 0x4000000u) ? (pe - pb) / 0x7c : 0;
        if (!npts) return;
        if (!kcr.t_scan || now - kcr.t_scan >= 2000u) kcr_scan();
        if (h.ord >= kcr.ncars) {                                                /* cars may still be appearing in the first 30 s after the load: not counted then */
            if (now - kcr.t_load >= 30000u) mis = 1;
            if (toldmis++ < 5) klog("coverring: ringsync CLIENT car ordinal %u >= %lu cars here - ignored (%s)", h.ord, (unsigned long)kcr.ncars, mis ? "mismatch" : "load < 30 s, not counted");
            goto done;
        }
        car = kcr.c[h.ord].car; s = klh_rd32(car + 0x968);
        if (!kcvd_ptr_ok(s) || !kcr_script_matches(car, klh_rd32(s + 0x40))) goto done;
        cn = klh_rd32(s + 0x1c4);
        for (i = 0; i < 8; i++) own[i] = klh_rd32(s + 0x1c8 + i * 4);
        /* +0x24 is the car's seat-local handle (0x8a7d90 arg8 = 0x6ece90(car) = 0x86ca10 table index + 1; CR8 nav study 11-02): take THIS seat's value from a usable point of
           the same car's ring, the host's only when the car has none here (GUESS: the table index then matches, as the ordinal does) */
        own24 = 0; have24 = 0;
        for (i = 0; i < cn && i < 8 && !have24; i++) {
            DWORD f = 0, v = 0;
            if (own[i] < npts && klh_rd(pb + own[i] * 0x7c + 0x68, &f, 4) && kcr_pt_usable(f) && klh_rd(pb + own[i] * 0x7c + 0x24, &v, 4)) { own24 = v; have24 = 1; }
        }
        for (k = 0; k < n; k++) {
            DWORD pp, cfl = 0; float cpos[3] = { 0, 0, 0 };
            if (!kcr_rs_idx_owned(own, cn, pt[k].idx, npts)) {
                if (cn) mis = 1;                                                 /* a car whose ring this seat never built (cn 0) is not a mismatch */
                if (toldmis++ < 5) klog("coverring: ringsync CLIENT car #%u index %lu is not in this seat's ring of that car (n=%lu) - skipped", h.ord, pt[k].idx, (unsigned long)cn);
                continue;
            }
            if (!kcr_rs_pos_ok(pt[k].pos)) { if (toldmis++ < 5) klog("coverring: ringsync CLIENT car #%u index %lu: host position not finite - skipped", h.ord, pt[k].idx); continue; }
            pp = pb + pt[k].idx * 0x7c;
            if (!klh_rd(pp + 0x68, &cfl, 4) || !klh_rd(pp + 0x28, cpos, 12)) continue;
            if (!kcr_ring_apply_decision(cfl, pt[k].flags)) {
                if (kcr_pt_usable(cfl)) {
                    skipped_used++;
                    if (kcr_rs_moved(cpos, pt[k].pos) && kcr_rs_chg_first(pt[k].idx) && kcr.rs_nchg++ < 40) klog("coverring: ringsync CLIENT car #%u idx %lu CHANGED: client usable %03lx (%.0f,%.0f,%.0f) vs host %03lx (%.0f,%.0f,%.0f) - left as is (stage 1)",
                        h.ord, pt[k].idx, (unsigned long)cfl, cpos[0], cpos[1], cpos[2], pt[k].flags, pt[k].pos[0], pt[k].pos[1], pt[k].pos[2]);
                } else skipped_host++;
                continue;
            }
            /* heap data only: fields first, flags LAST (a reader that sees the usable bit sees a whole point) */
            *(volatile DWORD *)(DWORD_PTR)(pp + 0x24) = have24 ? own24 : (DWORD)pt[k].f24;
            memcpy((void *)(DWORD_PTR)(pp + 0x28), pt[k].pos, 12);
            memcpy((void *)(DWORD_PTR)(pp + 0x40), pt[k].blk, 36);
            *(volatile DWORD *)(DWORD_PTR)(pp + 0x68) = (DWORD)pt[k].flags;
            wrote++; kcr.rs_nap++;
            klog("coverring: ringsync CLIENT car #%u idx %lu was SPARE (%03lx) -> host point %03lx (%.0f,%.0f,%.0f) written (blk %08lx.. f24 host %08lx -> %s %08lx; nav record [L+0x58] not registered: no reader of this group found)", h.ord, pt[k].idx,
                 (unsigned long)cfl, pt[k].flags, pt[k].pos[0], pt[k].pos[1], pt[k].pos[2], pt[k].blk[0], pt[k].f24, have24 ? "own" : "host", have24 ? (unsigned long)own24 : pt[k].f24);
        }
done:
        if (mis && ++kcr.rs_mis >= 20) { kcr.rs_bad = 2; klog("coverring: ringsync CLIENT 20 mismatching packets (index / ordinal) - the two seats' car rings differ; ClientRingSync off until the next load"); }
        if (kcr.rs_toldrx < 3 || wrote) {
            DWORD ci[8]; int k2; for (k2 = 0; k2 < 8; k2++) ci[k2] = (DWORD)own[k2];
            kcr.rs_toldrx++;
            klog("coverring: ringsync CLIENT rx car #%u seq %u from %lu.%lu.%lu.%lu: %d points, wrote %d, client already usable %d, host spare %d (total written %lu, packets %lu)", h.ord, h.seq,
                 from & 255, from >> 8 & 255, from >> 16 & 255, from >> 24, n, wrote, skipped_used, skipped_host, (unsigned long)kcr.rs_nap, (unsigned long)kcr.rs_nrx);
            if (wrote && h.ord < kcr.ncars) kcr_cb_points("ringsync", h.ord, ci, cn, pb, npts);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        kcr.rs_bad = 1;
        klog("coverring: ringsync CLIENT exception - off for the rest of the run");
    }
}

#endif
