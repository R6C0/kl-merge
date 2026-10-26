/* kldown_mirror.c - ONLINE FLOP MIRROR (2026-10-26, track mirror; re/down_mirror.md). #included from klhook.c AFTER klnetchan.c (needs knc_*) and kldown.c
 * (kld_* statics). Nothing here runs unless [Down] Enable=1, OnlineFlopMirror is not 0 and the round is online (kld_o.cur).
 *
 * PROBLEM. The flop (Flop=1 belly / Flop=3 list) is a LOCAL write into the victim's animation pool [pl+0x78] (the carrier's pair, or the fall slot's pairs)
 * and into the three fall words of his prone movement. The other machines run THEIR copy of his body (the replica) with the stock pool: they see the
 * stock fall (re/down_online_read_a.md Q3).
 *
 * WHAT THIS DOES. The victim sends two short messages through klnetchan.c (knc_send):
 *   KDFL  while he is UP, every 4 s and at every change: which clip his NEXT knock-down plays (Flop=3 picks it right after the previous get-up, so it is
 *         known long before the fall: no mid-fall clip switch is needed) - or 'belly' (Flop=1) - and the number n of that fall.
 *   KDSY  while he LIES after the landing: frame / speed / last frame of the clip, every 700 ms or at a speed change of 0.2 (his mash speed).
 * A receiver ARMS the replica of that body (writes the carrier's pair / belly pairs of the REPLICA's pool and the three fall words of the REPLICA's prone
 * movement - the same writes kldown.c makes on the master, with the same checks) while its D state is 0, and FOLLOWS the sync with the replica's channel
 * speed while it lies. Guards (all of them or no write): the body is not the local master (kld_o.pl / klco_is_master), is a heister (type 2) and not
 * police (byte 0x2723), its D object is its own, D state is 0 for every write of the pool / words, and ITS animation pool [+0x78] is worn by NO other body
 * (session table + the game data's 32 places - the local master's included): a shared pool is REFUSED (the write would change the master's own fall and
 * every other body of that set), logged once per body with the verdict. An AI heister's set (a list for /Damage/Hit/Front/Front) is refused as in kldown.c.
 *
 * FALLBACK WITHOUT MESSAGES (OnlineFlopMirror=1 and OnlineFlopMirrorAssume=1). Both sides draw the next clip from a hash of (table index of the one who
 * falls, number of the fall, a constant) with the same walk as kld_mix_next (kdm_det_pick). The victim uses it (hook in kld_mix_next: kldm_det_r); a
 * replica computes the same pick with no message. ONLY valid when every machine has the same FlopMix / FlopReach / FlopCarrier / sets and the same fall
 * count - the message, when it arrives, corrects the count and names the clip.
 *
 * CARRIERS (re/hook_netchannel.md): knc_send goes by UDP broadcast 255.255.255.255:27416 (reaches the LAN and System Link ONLY, never the internet) and by
 * the Steam lobby member data 'klx_msg' (reaches the internet only while the lobby exists; GUESS: the game leaves it when the match starts - not proven
 * either way). So over Steam INTERNET play the only route that can work is the hash fallback (Assume=1), and it works only while the assumptions above hold.
 *
 * GUESSES (each marked below): that a replica's prone movement plays a fall at all and reads its [M+0x8b0] words and the pool pairs like the master's;
 * that the table index of a body is the same on every machine (klucc.c's convention; the sender's index arrives as m->ent); that a replica's channel is
 * writable like the master's (the follow writes only a channel that lies in [ent+0x70] chans and plays the armed clip). All writes go through klh_data
 * (guarded); Dry=1 writes nothing. Game thread only (knc handlers run from knc_tick on the game thread). */

#include "kldown_mirror_logic.h"

#define KDM_N 16
static struct {
    int mode, speed, assume;                   /* keys: OnlineFlopMirror (0 off, 1 messages + hash pick, 2 messages only), OnlineFlopMirrorSpeed, OnlineFlopMirrorAssume */
    int chan, own;                             /* knc_want succeeded; the local body's table index (-1 = not known) */
    DWORD sig, t_fl, t_sy; int s_mode, s_sheet, s_n; float s_rate;      /* the sender's state: the table signature, last KDFL / KDSY sent, what they said */
    int nsfl, nssy, nrfl[3], nrsy[3], nok, nmiss, nrefuse, nbadmsg;      /* counters (the live bench reads them): sent, received by carrier (0 other, 1 Steam, 2 UDP) */
    DWORD t_stat;
} kdm;
/* what arrived, per table index of the sender (the sender's own index - klucc.c's convention) */
static struct { int have_fl, have_sy; struct kdm_fl fl; struct kdm_sy sy; DWORD t_fl, t_sy; } kdm_m[KDM_N];
/* what this machine has done to the replica at table index i */
static struct kdm_rep {
    DWORD ent, pool, m;
    int armed, mode, sheet, def, refused, nfall, dgroup, lastds, vdone, follow0; DWORD t_follow;
    DWORD rec, num;                            /* the clip armed: its record and number */
    DWORD at, old, put;                        /* Flop=3: the carrier's pair (address of the clip number), what it held, what this part wrote */
    WORD wid, forig[3];                        /* the slot id written into the three fall words + 1 (0 = none), what they held */
    DWORD bat[4], bold[4], bput[4], bcond[4]; int nb;      /* Flop=1: belly pairs */
    DWORD t_told, t_mtold;
} kdm_r[KDM_N];

#define KDM_STALE 20000                        /* ms: a KDFL older than this is gone (the victim re-announces every 4 s) */

/* ---- the sender ---- */
static void kdm_send_tick(DWORD now, DWORD ents, int n)
{
    DWORD pl = kld_o.pl, d, ds = 0, m, h, chans; int i, mode = 0, sheet = 0, group = 0, nn; unsigned mask = 0; char pk[96];
    kdm.own = -1;
    if (!pl || klh_rd32(pl) != KLD_PLAYER_VT) return;
    for (i = 0; i < n; i++) if (klco_ent(ents, n, i) == pl) kdm.own = i;      /* GUESS: the same index on every machine (klucc.c's convention) */
    if (kdm.own < 0 || !kdm.chan || (kld.flop != 1 && kld.flop != 3)) return;
    d = klh_rd32(pl + 0x2948);
    if (!d || klh_rd32(d) != pl || !klh_rd(d + 4, &ds, 4)) return;
    nn = kld_s.downs + 1;
    if (ds == 0) {
        if (!kld.dry && kld_s.fok) {
            if (kld.flop == 3 && kld_mx.next >= 0 && kld_mx.next < kld_mx.n) { mode = 3; sheet = kld_md[kld_mx.e[kld_mx.next].def].sheet; group = kld_md[kld_mx.e[kld_mx.next].def].group; }
            else if (kld.flop == 1 && kld.belly) mode = 1;       /* Flop=1: the fall slot is the flop's on this body (kld_s.fok) */
        }
        for (i = 0; i < kld_mx.n; i++) mask |= 1u << kld_mx.e[i].def;
        if (mode != kdm.s_mode || sheet != kdm.s_sheet || nn != kdm.s_n || now - kdm.t_fl >= 4000) {
            if (!kdm_fmt_fl(pk, sizeof pk, mode, sheet, nn, group, mask & 0x1ff)) return;
            if (knc_send("KDFL", pk, kdm.own)) {
                kdm.nsfl++; kdm.s_mode = mode; kdm.s_sheet = sheet; kdm.s_n = nn; kdm.t_fl = now;
                if (kld.log && (mode != 0 || kdm.nsfl < 3)) klog("down: mirror: SENT the announce '%s' (as table index %d): his next knock-down is %s", pk, kdm.own, mode == 3 ? "the list clip of that sheet number" : mode == 1 ? "the belly clip" : "the game's own");
            }
        }
        return;
    }
    /* lying: the sync, only after the landing and while this part holds the fall (kld_flop_one's own conditions) */
    if (ds != 2 || !kdm.speed || !kld_s.fnow || kld_s.fdone || !kld_s.t_land || !(m = kld_prone(pl))) return;
    if (!(h = klh_rd32(m + 0x8d0)) || !(chans = klh_rd32(pl + 0x70))) return;
    for (i = 0; i < 16; i++) if (h == chans + 0x1c + 0x38 * i) break;
    if (i == 16 || klh_rd32(h) != kld_s.fclip) return;
    {   int ok = 1; float frame = kld_rdf(h + 4, &ok), to = kld_rdf(h + 0xc, &ok), fps = kld_rdf(h + 0x10, &ok), rate;
        if (!ok || to < 2 || to > 5000 || frame < 0 || frame > to + 1 || fps < 0.5f || fps > 250.0f) return;
        rate = fps / 25.0f;
        if (rate < 0.05f || rate > 10.0f) return;
        if (now - kdm.t_sy < 700 && (rate - kdm.s_rate < 0.2f && kdm.s_rate - rate < 0.2f)) return;
        if (!kdm_fmt_sy(pk, sizeof pk, kld_s.downs, frame, rate, (int)(to + 0.5f))) return;
        if (knc_send("KDSY", pk, kdm.own)) {
            kdm.nssy++; kdm.t_sy = now; kdm.s_rate = rate;
            if (kld.log >= 2 || kdm.nssy <= 2) klog("down: mirror: SENT the sync '%s' (frame %.1f of %.0f, speed %.2f)", pk, frame, to, rate);
        }
    }
}

/* ---- the receiver: handlers (game thread, from knc_tick) ---- */
static void kdm_on_fl(const struct knc_msg *msg, int src)
{
    struct kdm_fl f;
    if (msg->ent < 0 || msg->ent >= KDM_N || !kdm_parse_fl(msg->payload, &f)) { kdm.nbadmsg++; return; }
    kdm_m[msg->ent].fl = f; kdm_m[msg->ent].have_fl = 1; kdm_m[msg->ent].t_fl = GetTickCount();
    kdm.nrfl[src >= 1 && src <= 2 ? src : 0]++;
    if (kld.log && kdm.nrfl[0] + kdm.nrfl[1] + kdm.nrfl[2] <= 3) klog("down: mirror: RECEIVED an announce from table index %d by %s: mode %d sheet %d fall %d group %d", msg->ent, src == 1 ? "Steam" : src == 2 ? "UDP" : "?", f.mode, f.sheet, f.n, f.group);
}
static void kdm_on_sy(const struct knc_msg *msg, int src)
{
    struct kdm_sy y;
    if (msg->ent < 0 || msg->ent >= KDM_N || !kdm_parse_sy(msg->payload, &y)) { kdm.nbadmsg++; return; }
    kdm_m[msg->ent].sy = y; kdm_m[msg->ent].have_sy = 1; kdm_m[msg->ent].t_sy = GetTickCount();
    kdm.nrsy[src >= 1 && src <= 2 ? src : 0]++;
}

/* ---- the pool test ---- */
/* every body that wears a pool: the session table's and the game data's 32 places, each once. -> the count; bodies[] / pools[] filled (cap 64) */
static int kdm_bodies(DWORD ents, int n, DWORD *bodies, unsigned *pools, int cap)
{
    DWORD gd, p; int i, k, c = 0;
    for (i = 0; i < n && c < cap; i++) if ((p = klco_ent(ents, n, i)) != 0 && klh_rd32(p) == KLD_PLAYER_VT) { bodies[c] = p; pools[c] = klh_rd32(p + 0x78); c++; }
    if ((gd = klh_rd32((DWORD_PTR)KLH_VA(KLD_GAMEDATA))) != 0)
        for (i = 0; i < 32 && c < cap; i++) {
            if (!(p = klh_rd32(gd + 0x828 + 4 * i)) || klh_rd32(p) != KLD_PLAYER_VT) continue;
            for (k = 0; k < c; k++) if (bodies[k] == p) break;
            if (k == c) { bodies[c] = p; pools[c] = klh_rd32(p + 0x78); c++; }
        }
    return c;
}
/* -> number of OTHER bodies that wear ent's pool (-1 = ent not found / no pool); *master = the local master is one of them */
static int kdm_pool_shared(DWORD ents, int n, DWORD ent, int *master)
{
    DWORD b[64]; unsigned pl[64]; int c = kdm_bodies(ents, n, b, pl, 64), self = -1, i;
    for (i = 0; i < c; i++) if (b[i] == ent) self = i;
    if (master) { *master = 0; if (self >= 0) for (i = 0; i < c; i++) if (i != self && pl[i] == pl[self] && b[i] == kld_o.pl) *master = 1; }
    return kdm_pool_users(pl, c, self);
}

/* ReplicaProbe's extra verdict (kld_o_probe calls this for each body it prints): can the mirror write this replica's pool? */
static void kldm_probe_line(DWORD ent, DWORD now)
{
    DWORD sm, ents = 0; int n = 0, mast = 0, u;
    (void)now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !klco_table(sm, &ents, &n)) return;
    u = kdm_pool_shared(ents, n, ent, &mast);
    klog("down: online: ReplicaProbe: body %08lx pool %08lx: %s%s", ent, klh_rd32(ent + 0x78),
         u < 0 ? "not found in the session table" : u == 0 ? "EXCLUSIVE (no other body wears it): the flop mirror may write this replica's pool (OnlineFlopMirror)" : "SHARED with other bodies",
         u > 0 ? (mast ? " - THE LOCAL MASTER WEARS IT TOO: the mirror REFUSES (a pair written here would be the master's own fall)" : " - the mirror REFUSES (other bodies of the set would fall that way too)") : "");
}

/* ---- restore ---- */
static void kdm_restore(struct kdm_rep *r, const char *why)
{
    int k, nw = 0; DWORD pr[2] = { 1, 0 }; WORD w;
    if (!r->armed) return;
    if (r->wid && r->m && klh_rd32(r->ent) == KLD_PLAYER_VT && klh_rd32(r->m) == KLD_PRONE_VT && klh_rd32(r->m + 0x8d4) == r->ent)
        for (k = 0; k < 3; k++) {
            DWORD at = r->m + KLD_M_FALL + 2 * k;
            if (klh_rd(at, &w, 2) && w == (WORD)(r->wid - 1) && w != r->forig[k] && klh_data((void *)(DWORD_PTR)at, &r->forig[k], 2, "the replica's prone movement: a fall slot id, back as the game had it")) nw++;
        }
    if (r->mode == 3 && r->at && r->put != r->old) {
        if (kld_pool_live(r->ent, r->pool) && klh_rd(r->at - 4, pr, 8) && pr[0] == 0 && pr[1] == r->put)
            klh_data((void *)(DWORD_PTR)r->at, &r->old, 4, "the replica's animation set: the carrier pair's clip number, back as the level had it");
    }
    for (k = 0; k < r->nb; k++) {
        pr[0] = pr[1] = 0;
        if (kld_pool_live(r->ent, r->pool) && klh_rd(r->bat[k] - 4, pr, 8) && pr[0] == r->bcond[k] && pr[1] == r->bput[k])
            klh_data((void *)(DWORD_PTR)r->bat[k], &r->bold[k], 4, "the replica's animation set: a belly pair's clip number, back as the level had it");
    }
    klog("down: mirror: replica %08lx DISARMED (%s): %d fall word(s)%s%s put back", r->ent, why, nw, r->mode == 3 ? ", the carrier pair" : "", r->nb ? ", the belly pairs" : "");
    r->armed = 0; r->wid = 0; r->nb = 0; r->at = 0; r->rec = 0; r->mode = 0; r->sheet = 0;
}

/* ---- arm: write what the master's own body has for the next fall into the REPLICA's pool and words. -> 1 armed / 0 not (refused or not yet) ---- */
static int kdm_arm(struct kdm_rep *r, int idx, DWORD ents, int n, int mode, int sheet, DWORD now)
{
    DWORD m, recs = 0, cnt = 0, at, pr[2], cp[2] = { 1, 0 }, c8[8], num = 0, rec = 0, bid; int id, k, def = -1, i, mast = 0, u, a1, a2, a3, bf; DWORD a4; WORD w[3], st; char nm[96]; const char *hash;
    if (!(m = kld_prone(r->ent))) return 0;                                 /* made with the player (0x5bd530): expected at once; no line a frame */
    u = kdm_pool_shared(ents, n, r->ent, &mast);
    if (u != 0) {
        if (!r->refused) { r->refused = 1; kdm.nrefuse++; klog("down: mirror: REFUSED replica %08lx (table index %d): its animation pool %08lx is %s - nothing is written (a write would %s)", r->ent, idx, klh_rd32(r->ent + 0x78),
                                                    u < 0 ? "not readable / not in the session table" : mast ? "worn by the LOCAL MASTER too" : "worn by other bodies too", u < 0 ? "go nowhere known" : "change their falls too"); }
        return 0;
    }
    if ((id = klq_slot(r->ent, "/Damage/Hit/Front/Front")) >= 0 && kld_list(r->ent, id, c8, 8) > 0) {
        if (!r->refused) { r->refused = 1; kdm.nrefuse++; klog("down: mirror: REFUSED replica %08lx: its animation set has a clip for /Damage/Hit/Front/Front = an AI heister's set (the bots' own deaths draw from the pair)", r->ent); }
        return 0;
    }
    id = klq_slot(r->ent, kld.fallslot);
    if (id < 0 || id > 0x7fff || !(at = kld_listat(r->ent, id, &recs, &cnt))) {
        if (!r->refused) { r->refused = 1; klog("down: mirror: replica %08lx: the %s %s has no list in its set: not armed", r->ent, kld.flop == 3 ? "carrier" : "fall slot", kld.fallslot); }
        return 0;
    }
    if (mode == 3) {
        DWORD sid_at; int sid;
        for (k = 0; k < KLD_NMIX; k++) if (kld_md[k].sheet == sheet) def = k;
        if (def < 0) { klog("down: mirror: replica %08lx: sheet #%d is not in this build's list: not armed", r->ent, sheet); return 0; }
        if (!klh_rd(at, cp, 8) || cp[0] != 0 || cp[1] >= cnt) {
            if (!r->refused) { r->refused = 1; klog("down: mirror: replica %08lx: the carrier %s is not a list of ONE pair with condition word 0: not armed", r->ent, kld.fallslot); }
            return 0;
        }
        if (r->armed && r->mode == 3 && cp[1] != r->put) { kdm_restore(r, "the carrier pair is not as this part left it"); return 0; }
        sid = klq_slot(r->ent, kld_md[def].slot); sid_at = sid >= 0 ? kld_listat(r->ent, sid, &recs, &cnt) : 0;
        for (i = 0; sid_at && i < 16; i++) {
            if (!klh_rd(sid_at + 8 * i, pr, 8)) break;
            if (pr[1] < cnt && kld_clipfacts(recs + pr[1] * 0x68, &a1, &a2, &a4, &a3, nm, sizeof nm) && (hash = strrchr(nm, '#')) != 0 && !strcmp(hash + 1, kld_md[def].clip)) { rec = recs + pr[1] * 0x68; num = pr[1]; break; }
            if (!pr[0]) break;
        }
        /* the carrier's own clip (#12) while its pair holds an earlier choice of this part: by the remembered number */
        if (!rec && sid == id && r->armed && r->mode == 3 && r->old < cnt && kld_clipfacts(recs + r->old * 0x68, &a1, &a2, &a4, &a3, nm, sizeof nm) && (hash = strrchr(nm, '#')) != 0 && !strcmp(hash + 1, kld_md[def].clip)) { rec = recs + r->old * 0x68; num = r->old; }
        if (!rec) { klog("down: mirror: replica %08lx: sheet #%d '%s' has no pair with that clip in %s of its set: not armed", r->ent, sheet, kld_md[def].clip, kld_md[def].slot); return 0; }
        if (!kld_clipfacts(rec, &a1, &a2, &a4, &a3, nm, sizeof nm) || !a3 || kld_badevent(rec, &bid, &bf) != 0) { klog("down: mirror: replica %08lx: sheet #%d clip %lu is not a full-body clip without an event the game acts on: not armed", r->ent, sheet, num); return 0; }
    }
    /* the fall words: what stands there must be the game's own ids, 0xffff or ours (kld_flop_words' rule) */
    for (k = 0; k < 3; k++) {
        if (!klh_rd(m + KLD_M_FALL + 2 * k, &w[k], 2)) return 0;
        st = (WORD)klq_slot(r->ent, kld_stock[k]);
        if (w[k] != (WORD)id && w[k] != st && w[k] != 0xffff && !(r->wid && w[k] == (WORD)(r->wid - 1))) {
            if (!r->refused) { r->refused = 1; klog("down: mirror: replica %08lx: fall word %d of its prone movement holds %u, not the id of %s (%u) nor 65535 nor ours: not the words this was read on, not armed", r->ent, k, w[k], kld_stock[k], st); }
            return 0;
        }
    }
    if (kld.dry) { klog("down: mirror: Dry=1: replica %08lx WOULD be armed: %s", r->ent, mode == 3 ? kld_md[def].clip : "belly"); r->refused = 1; return 0; }
    if (mode == 3) {
        if (num != cp[1] && !klh_data((void *)(DWORD_PTR)(at + 4), &num, 4, "the replica's animation set: the carrier pair's clip number = the clip of its next knock-down")) return 0;
        if (!r->armed || r->mode != 3) { r->old = cp[1]; r->at = at + 4; r->pool = klh_rd32(r->ent + 0x78); }
        r->put = num; r->rec = rec; r->num = num; r->def = def;
    } else {
        /* Flop=1: the pairs of the fall slot that are not thrown forward get the first forward clip (kld_flop_belly on the replica's own list) */
        DWORD good = 0xffffffff; float net[3]; int nb = 0; DWORD pool = klh_rd32(r->ent + 0x78), pp[2];
        if (r->armed && r->mode == 1) { r->mode = 1; return 1; }
        for (i = 0; i < 16; i++) {
            if (!klh_rd(at + 8 * i, pp, 8) || pp[1] >= cnt) return 0;
            if (klh_rd(recs + pp[1] * 0x68 + 0x18, net, 12) && kld_fin(net[2]) && net[2] < -20.0f) { good = pp[1]; break; }
            if (!pp[0]) break;
        }
        if (good == 0xffffffff) { if (!r->refused) { r->refused = 1; klog("down: mirror: replica %08lx: no clip of %s is thrown forward in its set: belly not armed", r->ent, kld.fallslot); } return 0; }
        for (i = 0; i < 16 && nb < 4; i++) {
            if (!klh_rd(at + 8 * i, pp, 8) || pp[1] >= cnt) break;
            if (pp[1] != good && klh_rd(recs + pp[1] * 0x68 + 0x18, net, 12) && kld_fin(net[2]) && net[2] >= -20.0f
                && klh_data((void *)(DWORD_PTR)(at + 8 * i + 4), &good, 4, "the replica's animation set: the clip number of a pair of the fall slot, the belly clip's")) {
                r->bat[nb] = at + 8 * i + 4; r->bold[nb] = pp[1]; r->bput[nb] = good; r->bcond[nb] = pp[0]; nb++;
            }
            if (!pp[0]) break;
        }
        r->nb = nb; r->pool = pool; r->rec = recs + good * 0x68; r->num = good;
    }
    for (k = 0; k < 3; k++) {
        WORD want = (WORD)id;
        if (w[k] == want) continue;
        if (!r->wid) r->forig[k] = w[k];
        klh_data((void *)(DWORD_PTR)(m + KLD_M_FALL + 2 * k), &want, 2, "the replica's prone movement: the slot id of the fall = the flop's slot");
    }
    if (!r->wid) { r->wid = (WORD)(id + 1); }
    r->m = m; r->mode = mode; r->sheet = sheet; r->armed = 1; r->refused = 0;
    kld_clipfacts(r->rec, &a1, &a2, &a4, &a3, nm, sizeof nm);
    klog("down: mirror: ARMED replica %08lx (table index %d, pool %08lx exclusive): its next knock-down is %s clip %lu '%s'%s (fall words = slot %d, the pair %08lx held %lu)", r->ent, idx, r->pool, mode == 3 ? "list" : "belly",
         r->num, nm, mode == 3 ? "" : " (the belly pairs of the fall slot)", id, r->at, r->old);
    (void)now;
    return 1;
}

/* Flop=1: any clip thrown forward (net root z < -20, kld_flop_belly's test) counts as the belly */
static int kdm_forward(DWORD clip) { float net[3]; return klh_rd(clip + 0x18, net, 12) && kld_fin(net[2]) && net[2] < -20.0f; }

/* what a replica really plays when its fall begins: the armed clip or not (the live bench's proof) */
static void kdm_verify(struct kdm_rep *r, DWORD m, DWORD now)
{
    DWORD clip, ms = 0; int a1, a2, a3; DWORD a4; char nm[96];
    if (r->vdone || !klh_rd(m + 0x8ec, &ms, 4)) return;
    clip = klh_rd32(m + 0x8cc);
    if (ms != 1 || !clip) { if (!r->t_told) r->t_told = now; if (now - r->t_told < 800) return; }      /* the fall may not have begun in M yet: look again */
    r->vdone = 1; r->t_told = 0;
    if (!clip) { klog("down: mirror: replica %08lx is down (D 2) but its prone movement plays no clip within 0.8 s: nothing to compare", r->ent); return; }
    kld_clipfacts(clip, &a1, &a2, &a4, &a3, nm, sizeof nm);
    if (clip == r->rec || (r->mode == 1 && kdm_forward(clip))) { kdm.nok++; klog("down: mirror: MIRROR OK: replica %08lx plays the armed clip %08lx '%s' (%d OK, %d missed)", r->ent, clip, nm, kdm.nok, kdm.nmiss); }
    else { kdm.nmiss++; klog("down: mirror: MIRROR MISSED: replica %08lx plays clip %08lx '%s' and the armed one was %08lx (%d OK, %d missed) - the replica's fall does not read the pool pair / words written here (GUESS wrong), or the fall began before the arm", r->ent, clip, nm, r->rec, kdm.nok, kdm.nmiss); }
}

/* the sped get-up: while the replica lies, its channel follows the master's sync. Writes only a channel that lies in the replica's chans array and plays the armed clip. */
static void kdm_follow(struct kdm_rep *r, int idx, DWORD now)
{
    DWORD m = r->m, h, chans, clock, tick = 0; int i, ok = 1; float frame, to, fps, dt, target, want, age; long ne; DWORD ms = 0;
    if (!kdm.speed || !r->armed || !r->rec || !kdm_m[idx].have_sy || now - kdm_m[idx].t_sy > 1500 || kdm_m[idx].sy.n != r->nfall) return;
    if (r->follow0 == 2) return;
    if (klh_rd32(m) != KLD_PRONE_VT || klh_rd32(m + 0x8d4) != r->ent || !klh_rd(m + 0x8ec, &ms, 4) || ms != 1) return;
    if (!(h = klh_rd32(m + 0x8d0)) || !(chans = klh_rd32(r->ent + 0x70)) || klh_rd32(m + 0x8cc) != r->rec) return;
    for (i = 0; i < 16; i++) if (h == chans + 0x1c + 0x38 * i) break;
    if (i == 16 || klh_rd32(h) != r->rec) return;
    if (!(clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    dt = kld_rdf(clock + 0x50, &ok); frame = kld_rdf(h + 4, &ok); to = kld_rdf(h + 0xc, &ok); fps = kld_rdf(h + 0x10, &ok);
    if (!ok || to < 2 || to > 5000 || frame < 0 || frame > to + 1 || fps < 0.5f || fps > 250.0f || dt < 0 || dt > 0.5f) return;
    if (!r->follow0) { r->follow0 = 1; r->t_follow = now; klog("down: mirror: replica %08lx FOLLOWS the master's get-up speed (his frame %.1f, speed %.2f; the replica's frame %.1f, speed %.2f)", r->ent, kdm_m[idx].sy.frame, kdm_m[idx].sy.rate, frame, fps / 25.0f); }
    if (now - r->t_follow > 15000) { r->follow0 = 2; klog("down: mirror: replica %08lx: the follow ran 15 s: left to the game", r->ent); return; }
    age = (now - kdm_m[idx].t_sy) / 1000.0f;
    target = kdm_m[idx].sy.frame + age * 25.0f * kdm_m[idx].sy.rate;
    if (target > to) target = to;
    want = kdm_fps(kdm_m[idx].sy.rate, frame, target, 2.0f);
    if ((want > fps + 0.5f || want < fps - 0.5f) && !klh_data((void *)(DWORD_PTR)(h + 0x10), &want, 4, "the replica's knock-down channel: frames a second = the master's get-up pace")) return;
    /* the two ticks held 2 s behind the clip's end, as the master holds them (GUESS: a replica's M reads them like the master's) */
    ne = (long)tick + (long)((to - frame) / (want > 0.5f ? want : 0.5f) * 1024.0f + 0.5f) + 2048;
    klh_data((void *)(DWORD_PTR)(m + 0x8dc), &ne, 4, "the replica's prone movement: the tick the fall is over, held behind the clip's end");
    klh_data((void *)(DWORD_PTR)(m + 0x8e0), &ne, 4, "the replica's prone movement: the fall's event tick, held with its end");
}

/* the message-less pick for fall number nn of the body at table index idx (kld_mx's list, the victim's algorithm). -> sheet number, 0 = no list here */
static int kdm_assume_sheet(int idx, int nn, int lastgroup)
{
    float w[KLD_NMIX]; int g[KLD_NMIX], i, p;
    if (kld_mx.n <= 0) return 0;
    for (i = 0; i < kld_mx.n; i++) { w[i] = kld_mx.w[kld_mx.e[i].def]; g[i] = kld_md[kld_mx.e[i].def].group; }
    p = kdm_det_pick(w, g, kld_mx.n, lastgroup, kdm_hash(idx, nn, KDM_SALT));
    return p >= 0 ? kld_md[kld_mx.e[p].def].sheet : 0;
}

/* kld_mix_next's hook: the victim's own r from the hash (OnlineFlopMirror=1, online, his table index known). -> -1 = keep the random draw */
static float kldm_det_r(DWORD pl, float sum)
{
    if (kdm.mode != 1 || !kld_o.cur || !pl || pl != kld_o.pl || kdm.own < 0) return -1.0f;
    return kdm_hash_r(kdm_hash(kdm.own, kld_s.downs + 1, KDM_SALT), sum);
}

/* ---- the tick ---- */
static void kldm_tick(int game_thread)
{
    DWORD sm, ents = 0, now, sig = 0; int n = 0, i;
    if (!kdm.mode || !game_thread || !kld.on || !klh_exe_ok) return;
    now = GetTickCount();
    if (!kld_o.cur || !(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598))) || !klco_table(sm, &ents, &n)) {      /* not online / no session: whatever is armed goes back */
        for (i = 0; i < KDM_N; i++) if (kdm_r[i].armed) kdm_restore(&kdm_r[i], "the round is not online any more / no session table");
        memset(kdm_m, 0, sizeof kdm_m); kdm.own = -1; kdm.s_mode = kdm.s_sheet = kdm.s_n = 0; kdm.t_fl = 0;
        return;
    }
    for (i = 0; i < n; i++) sig = sig * 31 + klco_ent(ents, n, i);
    if (sig != kdm.sig) { kdm.sig = sig; memset(kdm_m, 0, sizeof kdm_m); kdm.t_fl = 0; kdm.s_n = -1; }      /* another table: the messages of the old indices are not these bodies' */
    kdm_send_tick(now, ents, n);
    for (i = 0; i < n && i < KDM_N; i++) {
        struct kdm_rep *r = &kdm_r[i]; DWORD ent = klco_ent(ents, n, i), d, ds = 0; int fresh, mode, sheet = 0, haveds;
        if (r->ent != ent) { if (r->armed) kdm_restore(r, "another body at this table index"); memset(r, 0, sizeof *r); r->ent = ent; }
        fresh = kdm_m[i].have_fl && now - kdm_m[i].t_fl < KDM_STALE;
        if (!ent || ent == kld_o.pl || !klco_heister(ent) || klco_is_master(ent)) { if (r->armed) kdm_restore(r, "master / police / not a heister"); continue; }
        if (!fresh && !kdm.assume) { if (r->armed) kdm_restore(r, "no announce for 20 s"); continue; }
        d = klh_rd32(ent + 0x2948); haveds = d && klh_rd32(d) == ent && klh_rd(d + 4, &ds, 4);
        if (!haveds) continue;
        mode = fresh ? kdm_m[i].fl.mode : (kld_o.flop0 == 1 || kld_o.flop0 == 3 ? kld_o.flop0 : 0);
        if (fresh && mode != 0 && mode != kld_o.flop0) {
            if (!r->t_mtold || now - r->t_mtold > 30000) { r->t_mtold = now; klog("down: mirror: table index %d announces mode %d but this machine's ini has Flop=%d: the mirror needs the SAME ini on every machine - ignored", i, mode, kld_o.flop0); }
            mode = 0;
        }
        if (!kld_o.oflop) mode = 0;
        /* the replica's fall counter: the master's n names the fall the announced clip is for (we count the ones we saw begin) */
        if (fresh && ds == 0 && kdm_m[i].fl.n - 1 > r->nfall) r->nfall = kdm_m[i].fl.n - 1;
        if (r->lastds == 0 && ds != 0) { r->nfall++; r->vdone = 0; r->follow0 = 0; if (r->armed) r->dgroup = r->mode == 3 && r->def >= 0 ? kld_md[r->def].group : r->dgroup; }
        if (ds != 0 && r->armed && r->m) kdm_verify(r, r->m, now);
        if (ds == 2 && r->armed && r->mode != 0) kdm_follow(r, i, now);
        if (ds == 0) {
            if (mode == 0) { if (r->armed) kdm_restore(r, "he announced no flop for the next fall"); }
            else {
                if (mode == 3) sheet = fresh ? kdm_m[i].fl.sheet : kdm_assume_sheet(i, r->nfall + 1, r->dgroup);
                if (mode == 1 || sheet) {
                    if (!r->armed || r->mode != mode || r->sheet != sheet) { if (r->armed && r->mode != mode) kdm_restore(r, "the flop mode changed"); kdm_arm(r, i, ents, n, mode, sheet, now); }      /* same mode: the pair is rewritten in place */
                }
            }
        }
        r->lastds = ds;
    }
    if (kld.log && now - kdm.t_stat >= 60000 && (kdm.nsfl || kdm.nssy || kdm.nrfl[0] + kdm.nrfl[1] + kdm.nrfl[2])) {
        kdm.t_stat = now;
        klog("down: mirror: counters: sent %d announce(s) %d sync(s); received announces (other/Steam/UDP) %d/%d/%d, syncs %d/%d/%d, %d bad; replicas: %d MIRROR OK, %d MISSED, %d refused", kdm.nsfl, kdm.nssy,
             kdm.nrfl[0], kdm.nrfl[1], kdm.nrfl[2], kdm.nrsy[0], kdm.nrsy[1], kdm.nrsy[2], kdm.nbadmsg, kdm.nok, kdm.nmiss, kdm.nrefuse);
    }
}

/* after kld_init (the Online* keys are read there) */
static void kldm_init(void)
{
    memset(&kdm, 0, sizeof kdm); memset(kdm_m, 0, sizeof kdm_m); memset(kdm_r, 0, sizeof kdm_r); kdm.own = -1;
    kdm.mode = GetPrivateProfileIntA("Down", "OnlineFlopMirror", 1, klh_ini);      /* 0 off, 1 messages + the hash pick (recommended on), 2 messages only */
    if (kdm.mode < 0 || kdm.mode > 2) kdm.mode = 1;
    kdm.speed = GetPrivateProfileIntA("Down", "OnlineFlopMirrorSpeed", 1, klh_ini) != 0;
    kdm.assume = GetPrivateProfileIntA("Down", "OnlineFlopMirrorAssume", 0, klh_ini) != 0;
    if (!kld.on || !kld_o.online || !kld_o.oflop || (kld_o.flop0 != 1 && kld_o.flop0 != 3)) { kdm.mode = 0; return; }      /* nothing to mirror: the ini's Flop is not 1 / 3 or the online flop is off */
    kdm.chan = knc_want("downmirror");
    knc_on("KDFL", kdm_on_fl); knc_on("KDSY", kdm_on_sy);
    klog("down: mirror: OnlineFlopMirror=%d (%s), Speed=%d, Assume=%d (arm replicas with NO message, by the hash: needs the same ini and fall counts everywhere); channel %s. Carriers: UDP broadcast reaches LAN / System Link only; the Steam lobby member data reaches the internet only while the lobby exists (GUESS: not after the match starts); Assume=1 is the only route that can work in Steam internet play",
         kdm.mode, kdm.mode == 1 ? "messages + the hash pick on the victim" : "messages only, the victim keeps his random draw", kdm.speed, kdm.assume, kdm.chan ? "wanted" : "NOT available");
}
