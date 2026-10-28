/*
 * klucchide.c - [Ucc] Hide: THE UNDERCOVER COP STAYS HIDDEN UNTIL HE REVEALS HIMSELF (2026-10-26; owner decisions in re/ucc_design.md
 * 'OWNER DECISIONS' 1, 3, 4; P6 + the display halves of P1 / P3). Part of KLHook (included by klhook.c AFTER klucc_down.c, klnetchan.c,
 * klcharonline.c, klroundkeep.c, klhud.c; the pure logic and the shared state are klucchide_logic.h, included before klhud_values.c).
 * SHIP and TEST alike. Default OFF ([Ucc] Hide=0). NOTHING HERE HAS RUN IN THE GAME. Siblings: klucc.c (Pings / Accuse, prefix kluc_),
 * klucc_down.c (DownOnly, prefix klud_); this file's prefix is klucc_.
 * Writes: data only - the tuning int [0x168d7c0]+0x674 (heap); the rules object's first dword (a private vtable copy, klroundkeep.c's
 * pattern) or ONE slot (114) of a private copy another hook part already installed (klroundkeep.c's, klucc_down.c's). No code byte of
 * kl2.exe changes. One game call: 0x9425a0 (the master test, read-only, through klcharonline.c's klco_is_master).
 *
 * 1. WHY NOT THE ENGINE'S OWN SetUndercoverCop (the design doc's 'simplest guess'; static read of kl2.exe 0490, 2026-10-26)
 *    The host's round start (Sv slot 4 override 0x40f870, sub-mode 1 branch 0x40fa34 .. 0x40fb75) picks ONE client at random (0x8b66c0; a
 *    debug override byte [0xd1b3b4] when >= 0) and then, for that client's record (0x74 bytes at [rules+8], ZFFPlayer at +0x378, its DDL
 *    object at +0x380):
 *      0x601fd0(score, i, 0x80)    sets 0x80 in the SCORE object's replicated per-client flag dword ([[rules+0x2c]+0x98+4i] online; what
 *                                  slot 114 = 0x625be0 answers and the stock list (0x572050), the reward rule 0x4eb260 and slot 110 read)
 *      0x43e270(P, 1); 0x4622b0(P, 1) = [P+0x2729] = 1 on the host's copy of the player; 0x644310(P, float [0xd1b3bc])
 *      0x432780(ddl, 1)  = RMCSetUndercoverCop(1): it runs on the player's MASTER (his own client) - the wrapper sends it there when the
 *                          caller is not the master; the master's apply 0x8c95e0 sets bit 8 of the DDL m_iFlags (replicated) and
 *                          [P+0x2729] (0x4622b0). So SetUndercoverCop is the PLAYER's flag, not the 0x80 every list and reward reads.
 *      0x5cf5f0(ddl, 1)  = RMCSetPoliceMan(1): THE UCC IS ALSO FLAGGED POLICE from the first second (P2 of the design doc: the likely
 *                          reason the AI police never shoot him - not built here, see re/ucc_design.md).
 *      0x745f20(ddl, hp) = the max hit points.
 *    Consequences: (a) SetUndercoverCop(false) at the start would NOT hide him - the score flag 0x80 (what shows) is set separately and is
 *    re-read by every reader (slot 114 is a plain array read; nothing caches it); (b) clearing 0x80 instead WOULD hide him but also switch
 *    off the game's own UCC rules on every peer (his reward branch, the FA_UCC_* objectives, the police side's view) and klucc_down.c's
 *    recognition - a rule change, not a display change; (c) the RMC goes to the UCC's own machine, so it is no host->all channel either.
 *    => The game's flags stay as they are; only what is DISPLAYED is hidden, per viewer, with a host-kept 'revealed' bit on our channel.
 *
 * 2. WHAT IT DOES
 *    a. STATE (klucchide_logic.h): each peer reads the score flags of every client in an Undercover Cop round (game type 4, sub-mode word
 *       [0x168e59c] == 1, online rules Sv / Cl). The HOST keeps 'revealed' per client and an epoch (+1 per round); a client mirrors the
 *       host's state. Every tick the revealed bits are handed to klucc_down.c (klud_reveal): the down-only cap ends for a revealed UCC.
 *    b. REVEAL KEY ([Ucc] RevealKey, default 0x2D = Insert. Taken elsewhere: F5 [Ucc] Key (accuse), E adrenaline / climb, F / G / H cop
 *       squad, G grenade probe, F6 shop page, F7 unstick / host map set, F8 inventory / host AI, F9 / F11 character online, Tab crew card,
 *       X / C / Shift camera log; F10 opens the window menu, F12 is Steam's screenshot): pressed by the UCC himself, game window in front.
 *       Host's own UCC: revealed at once. A client UCC: a UREV request on klnetchan.c; the host accepts it only for a client that HAS
 *       flag 0x80 in the current epoch. Killing or downing never reveals (owner decision 1).
 *    c. BOUNTY ([Ucc] Bounty=1): [tuning+0x674] (criminal kills the UCC; stock 100,000, read fresh by 0x4eb260 at every kill, 0x4eb3ee) =
 *       BountyHidden (200,000) while any UCC of the round is hidden, BountyRevealed (400,000) once all are revealed (owner decision 3).
 *       Written on every peer from the shared state (the host's pays: the score is the host's); put back when the UCC session ends.
 *    d. CREW LIST STRIP ([Ucc] Strip=1, S1 of re/ucc_tell_audit.md): slot 114 (0x625be0) of the rules object answers through our wrapper;
 *       ONLY a call returning into the stock list's row routine 0x572050 .. 0x5721c1 gets the dword with 0x80 / 0x40000 taken out, and only
 *       while this peer may not see that UCC (klucc_sees: not revealed, viewer not he, not police / dirty cop, not a UCC himself - two UCCs
 *       see each other, owner decision 4). Every other caller (rewards, rules, our HUD readers, klucc_down.c) gets the true flags.
 *       The vtable: when the object already shows a private copy of klroundkeep.c or klucc_down.c, slot 114 of THAT copy is set; when one
 *       of them will install (KeepRound / TEST build on the Sv object, DownOnly on Sv or Cl) we wait up to 6 s; else our own copy
 *       (registered as klh_rules_vt2 / klh_rules_vt3 so the KLH_RULES_*_OK tests accept it).
 *    e. OUR CREW ROWS ([HUD] OnlineCrew, klhud.c; [Ucc] Rows=1): the same strip through klucc_hud_flags (S10 online).
 *    f. KILL FEED ([Ucc] Feed=1, P3): kllocname.c's LOC lookup wrapper answers FA_Killed_UCC with FA_Killed_Merc and FA_NoFriendlyFireUCC
 *       with FA_NoFriendlyFire while any UCC is hidden (klucc_route_key). FINDING: the friendly-fire text picks the UCC variant by the
 *       SUB-MODE alone (0x6ffea7 `cmp [0x168e59c], 1`), not by who was shot - it names the mode, not the man; routed anyway.
 *
 * 3. THE CHANNEL: klnetchan.c (re/hook_netchannel.md; UDP 27416 = System Link / same PC; Steam member data while the lobby lives - in a
 *    round over the internet there is NO carrier yet). Types: UHID host -> all "S;<epoch>;<ucc mask>;<revealed mask>" (taken only from a
 *    sender saying role 2) on a change and every 5 s; UREV client -> host "R;<epoch>;<client index>" at the press and every 2 s until the
 *    host's state shows it (15 s at most). Without a carrier the host's OWN UCC still reveals for the host's screen only.
 *    GUESSES (marked in the code too): the own client index on a CLIENT (records at [rules+8] carry the ZFFPlayer at +0x378 - only the
 *    host's 0x40f870 was read); the round clock [rules+0x4c] online; the session state window on a client.
 *
 * KLHook.ini, the shared [Ucc] section (keys of klucc.c / klucc_down.c there too: Pings PingMinS PingMaxS Accuse Key Name CooldownS ConeDeg
 * RangeM ShowS Log DownOnly Floor ForceSecs Dry)
 *   Hide=0          master switch of this file (NOT RUN LIVE). Every peer needs the same build for a reveal to show everywhere.
 *   RevealKey=0x2D  Insert (0 = none)      Strip=1  the stock crew list hides a hidden UCC      Rows=1  our online crew rows too
 *   Feed=1          FA_Killed_UCC / FA_NoFriendlyFireUCC read as the crew's lines while hidden
 *   Bounty=1  BountyHidden=200000  BountyRevealed=400000        HideLog=1 (2 = every message)
 */
#ifndef KLUCCHIDE_C
#define KLUCCHIDE_C

#define KLUCC_SUBMODE    0x0168e59cu           /* 0 FA, 1 Undercover Cop, 2 Cops and Robbers (re/cops_and_robbers.md) */
#define KLUCC_TUNING     0x0168d7c0u
#define KLUCC_O_BOUNTY   0x674
#define KLUCC_SLOT_FLAGS 114
#define KLUCC_GETFLAGS   0x00625be0u           /* Sv / Cl slot 114 */
#define KLUCC_LIST_LO    0x00572050u           /* the stock list's row-state routine (whole: ends 0x5721c1) */
#define KLUCC_LIST_HI    0x005721c1u
#define KLUCC_VT_SV      0x00bd2eb4u
#define KLUCC_VT_CL      0x00bd31e4u
#define KLUCC_VT_SLOTS   260                   /* as klroundkeep.c / klucc_down.c: more than the 203 slots, the tail is never called */
#define KLUCC_WAIT_MS    6000                  /* how long a stock rules object is left for klroundkeep.c / klucc_down.c to take first */

typedef DWORD (__fastcall *KLUCC_F114)(void *self, void *edx, int idx);

static struct {
    int on, key, strip, feed, rows, bounty, log; long bHidden, bRevealed;
    DWORD rules; int window; float left; unsigned long uccWas; DWORD meAt;
    DWORD vtSv[1 + KLUCC_VT_SLOTS], vtCl[1 + KLUCC_VT_SLOTS]; DWORD waitSince; int toldVt, toldWait;
    long bOrig; int bSaved; long bLast;
    int chan; DWORD stateAt; unsigned long sentEpoch, sentRev, sentUcc;
    int reqIdx; unsigned long reqEpoch; DWORD reqUntil, reqSentAt; char reqStr[32];
    struct klucc_key k; DWORD keyAt; SHORT (WINAPI *aks)(int); HWND (WINAPI *fgw)(void); DWORD (WINAPI *wtp)(HWND, LPDWORD); int looked;
} klucc;

/* ---- slot 114 ---- */
static DWORD __fastcall klucc_w114(void *self, void *edx, int idx)
{
    DWORD f = ((KLUCC_F114)(DWORD_PTR)KLH_VA(KLUCC_GETFLAGS))(self, 0, idx);      /* every table we patch held exactly this function (checked) */
    (void)edx;
    if (klucc.strip && klucc_st.on && klucc_ra_is_list((unsigned long)(DWORD_PTR)_ReturnAddress(), (unsigned long)(DWORD_PTR)KLH_VA(KLUCC_LIST_LO), (unsigned long)(DWORD_PTR)KLH_VA(KLUCC_LIST_HI)))
        f = (DWORD)klucc_view(&klucc_st, klucc_st.me, (int)(signed char)idx, (unsigned long)f);
    return f;
}

/* slot 114 of a private table (ours or another part's, all in this DLL's .data): -> 1 when it now holds the wrapper */
static int klucc_patch(DWORD *slots, const char *whose, DWORD rules)
{
    if (slots[KLUCC_SLOT_FLAGS] == (DWORD)(DWORD_PTR)klucc_w114) return 1;
    if (slots[KLUCC_SLOT_FLAGS] != (DWORD)(DWORD_PTR)KLH_VA(KLUCC_GETFLAGS)) {
        if (!klucc.toldVt++) klog("ucchide: %s rules table has slot 114 = %08lx, not 0x625be0: the stock crew list is not stripped", whose, (unsigned long)slots[KLUCC_SLOT_FLAGS]);
        return 0;
    }
    slots[KLUCC_SLOT_FLAGS] = (DWORD)(DWORD_PTR)klucc_w114;
    klog("ucchide: rules %08lx: slot 114 of %s private vtable now strips a hidden UCC for the stock crew list", (unsigned long)rules, whose);
    return 1;
}

static void klucc_wrap(DWORD rules, DWORD now)
{
    DWORD vt = klh_rd32(rules), nv; int sv, others;
    if (!klucc.strip) return;
    if (vt == (DWORD)(DWORD_PTR)&klucc.vtSv[1] || vt == (DWORD)(DWORD_PTR)&klucc.vtCl[1]) return;
    if (vt == (DWORD)(DWORD_PTR)&klrk_vt[1]) { klucc_patch(&klrk_vt[1], "klroundkeep.c's", rules); return; }
    if (vt == (DWORD)(DWORD_PTR)&klud_sv[1]) { klucc_patch(&klud_sv[1], "klucc_down.c's Sv", rules); return; }
    if (vt == (DWORD)(DWORD_PTR)&klud_cl[1]) { klucc_patch(&klud_cl[1], "klucc_down.c's Cl", rules); return; }
    if (vt != KLUCC_VT_SV && vt != KLUCC_VT_CL) { if (!klucc.toldVt++) klog("ucchide: rules vtable %08lx is none we know (another part's copy?): the stock crew list is not stripped", (unsigned long)vt); return; }
    sv = vt == KLUCC_VT_SV;
    others = klud.on != 0;                                      /* klucc_down.c installs on Sv and Cl when DownOnly is set */
    if (sv) {
#ifdef KLHOOK_TEST
        others = 1;                                             /* klroundkeep.c's TEST probe wraps the Sv object always */
#else
        if (klrk_keep) others = 1;
#endif
    }
    if (others) {                                               /* they refuse a vtable that is not the stock one: let them go first */
        if (!klucc.waitSince) klucc.waitSince = now ? now : 1;
        if (now - klucc.waitSince < KLUCC_WAIT_MS) return;
        if (!klucc.toldWait++) klog("ucchide: no other part took the %s rules in %d s: our own copy (they will then leave the object alone)", sv ? "Sv" : "Cl", KLUCC_WAIT_MS / 1000);
    }
    {
        DWORD *blk = sv ? klucc.vtSv : klucc.vtCl;
        if (!blk[0]) {
            if (!klh_rd((DWORD_PTR)KLH_VA(vt - 4), blk, sizeof(DWORD) * (1 + KLUCC_VT_SLOTS))) return;
            if (!klucc_patch(&blk[1], sv ? "our Sv" : "our Cl", rules)) { blk[0] = 0; klucc.strip = 0; return; }
        }
        nv = (DWORD)(DWORD_PTR)&blk[1];
        if (sv) klh_rules_vt2 = nv; else klh_rules_vt3 = nv;     /* KLH_RULES_SV_OK / KLH_RULES_CL_OK accept it */
        if (klh_data((void *)(DWORD_PTR)rules, &nv, 4, "ucchide: FA rules vtable (private copy, slot 114)")) klog("ucchide: %s rules %08lx now answers slot 114 through our copy", sv ? "Sv" : "Cl", (unsigned long)rules);
        else if (sv) klh_rules_vt2 = 0; else klh_rules_vt3 = 0;
    }
}

/* ---- the own client index ----
   GUESS: the 0x74-byte records at [rules+8] hold the ZFFPlayer at +0x378 on a CLIENT as on the host (only the host's 0x40f870 was read);
   the one whose DDL object passes the master test is ours (klco_is_master). Fallbacks: the crew index of the game's local player (klud_local
   + klud_idx: (signed char)([[P+0x2748]+0xdc] ^ 0xac), klucc_down.c), then the stock player list's index ([[osd+0x10c4]+0xefc], klhud.c). */
static int klucc_find_me(DWORD rules, int n, int *how)
{
    DWORD recs = klh_rd32(rules + 8), freeb = klh_rd32(rules + 0xc), me = 0; int i; BYTE b;
    *how = 0;
    for (i = 0; recs && freeb && i < n; i++) {
        DWORD p;
        if (!klh_rd(freeb + i, &b, 1) || b) continue;
        if (!(p = klh_rd32(recs + 0x74 * (DWORD)i + 0x378)) || !klud_is_player(p)) continue;
        if (klco_is_master(p)) { *how = 1; return i; }
    }
    if (klud_local(&me) && klud_is_player(me) && (i = klud_idx(me)) >= 0 && i < n) { *how = 2; return i; }
    if (klu_r.osd) { DWORD el = klh_rd32(klu_r.osd + KLU_O_PLIST), li = 0; if (el && klh_rd(el + 0xefc, &li, 1) && li < (DWORD)n) { *how = 3; return (int)li; } }
    return -1;
}

/* ---- the channel ---- */
static void klucc_on_state(const struct knc_msg *m, int src)
{
    unsigned long e = 0, a = 0, b = 0, was = klucc_st.revealed, we = klucc_st.epoch;
    if (!klucc_st.on || klucc_st.host || m->role != 2 || klucc_parse(m->payload, &e, &a, &b) != 'S') return;
    if (klucc_client_apply(&klucc_st, e, a, b, GetTickCount()) && (was != klucc_st.revealed || we != klucc_st.epoch || klucc.log >= 2))
        klog("ucchide: host state via %s: epoch %lu, host's UCC mask %lx (mine %lx), revealed %lx", src == 1 ? "Steam" : "UDP", e, a, klucc_ucc_mask(&klucc_st), klucc_st.revealed);
}

static void klucc_on_req(const struct knc_msg *m, int src)
{
    unsigned long e = 0, a = 0, b = 0;
    if (!klucc_st.on || !klucc_st.host || klucc_parse(m->payload, &e, &a, &b) != 'R') return;
    if (klucc_host_reveal(&klucc_st, e, (int)a)) { klog("ucchide: REVEALED: client %lu asked via %s (epoch %lu); revealed %lx", a, src == 1 ? "Steam" : "UDP", e, klucc_st.revealed); klucc.stateAt = 0; }
    else if (klucc.log >= 2) klog("ucchide: request '%s' via %s refused (not a hidden UCC of epoch %lu, or already revealed)", m->payload, src == 1 ? "Steam" : "UDP", klucc_st.epoch);
}

static void klucc_net(DWORD now)
{
    char pk[48];
    if (!klucc.chan) return;
    if (klucc_st.host) {
        unsigned long ucc = klucc_ucc_mask(&klucc_st); int fresh = klucc_st.epoch != klucc.sentEpoch || klucc_st.revealed != klucc.sentRev || ucc != klucc.sentUcc;
        if (!fresh && klucc.stateAt && now - klucc.stateAt < 5000) return;
        klucc_fmt_state(pk, sizeof pk, klucc_st.epoch, ucc, klucc_st.revealed);
        if (knc_send("UHID", pk, -1) && fresh && klucc.log) klog("ucchide: host state sent: %s", pk);
        klucc.stateAt = now ? now : 1; klucc.sentEpoch = klucc_st.epoch; klucc.sentRev = klucc_st.revealed; klucc.sentUcc = ucc;
        return;
    }
    if (!klucc.reqUntil) return;
    if (klucc.reqIdx >= 0 && (klucc_st.revealed & (1ul << klucc.reqIdx))) { klog("ucchide: my reveal is confirmed by the host (epoch %lu)", klucc_st.epoch); klucc.reqUntil = 0; return; }
    if ((LONG)(now - klucc.reqUntil) >= 0) { klog("ucchide: my reveal request got no answer in 15 s (host without [Ucc] Hide, no carrier - internet rounds have none yet - or refused): nobody else sees it"); klucc.reqUntil = 0; return; }
    if (!klucc.reqSentAt || now - klucc.reqSentAt >= 2000) { klucc.reqSentAt = now ? now : 1; knc_send("UREV", klucc.reqStr, -1); }
}

/* ---- keys ---- */
static void klucc_keys(DWORD now)
{
    DWORD pid = 0; HWND f; int down;
    if (!klucc.key || now - klucc.keyAt < 30) return;
    klucc.keyAt = now;
    if (!klucc.looked) {
        HMODULE u = GetModuleHandleA("user32.dll"); klucc.looked = 1;
        if (u) { klucc.aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); klucc.fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); klucc.wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
        if (!klucc.aks || !klucc.fgw || !klucc.wtp) klog("ucchide: user32's GetAsyncKeyState / GetForegroundWindow not found: no reveal key");
    }
    if (!klucc.aks || !klucc.fgw || !klucc.wtp) return;
    f = klucc.fgw(); if (f) klucc.wtp(f, &pid);
    down = pid == GetCurrentProcessId() && (klucc.aks(klucc.key) & 0x8000) != 0;
    if (!klucc_edge(&klucc.k, down, now, 150)) return;
    if (klucc_st.me < 0) { klog("ucchide: reveal key: my own client index is not known: nothing done"); return; }
    if (!klucc_is_ucc(&klucc_st, klucc_st.me)) { klog("ucchide: reveal key: client %d (me) is no Undercover Cop (flags %08lx): ignored", klucc_st.me, klucc_st.flags[klucc_st.me]); return; }
    if (!klucc_hidden(&klucc_st, klucc_st.me)) { klog("ucchide: reveal key: already revealed"); return; }
    if (klucc_st.host) {
        if (klucc_host_reveal(&klucc_st, klucc_st.epoch, klucc_st.me)) { klog("ucchide: REVEALED: the host's own UCC (client %d) pressed the key; epoch %lu revealed %lx", klucc_st.me, klucc_st.epoch, klucc_st.revealed); klucc.stateAt = 0; }
        return;
    }
    if (!klucc_st.adopted_at) klog("ucchide: reveal key: no host state heard yet (host without [Ucc] Hide, or no carrier): request sent anyway for epoch %lu", klucc_st.epoch);
    klucc.reqIdx = klucc_st.me; klucc.reqEpoch = klucc_st.epoch; klucc.reqUntil = now + 15000; klucc.reqSentAt = 0;
    klucc_fmt_req(klucc.reqStr, sizeof klucc.reqStr, klucc.reqEpoch, klucc.reqIdx);
    klog("ucchide: reveal key: request to the host: %s%s", klucc.reqStr, klucc.chan ? "" : " - NO channel ([NetChan] Udp=0 and Steam=0): it cannot reach the host");
}

/* ---- the bounty int ---- */
static void klucc_bounty_put(int leaving)
{
    DWORD tun = klh_rd32((DWORD_PTR)KLH_VA(KLUCC_TUNING)); long cur = 0, want;
    if (!klucc.bounty || !tun || !klh_rd(tun + KLUCC_O_BOUNTY, &cur, 4)) return;
    if (leaving) {
        if (klucc.bSaved && cur == klucc.bLast && cur != klucc.bOrig && klh_data((void *)(DWORD_PTR)(tun + KLUCC_O_BOUNTY), &klucc.bOrig, 4, "ucchide: bounty put back"))
            klog("ucchide: [tuning+0x674] put back to %ld", klucc.bOrig);
        klucc.bSaved = 0; return;
    }
    if (!klucc.bSaved) { klucc.bOrig = cur; klucc.bSaved = 1; }
    want = klucc_bounty(&klucc_st, klucc.bHidden, klucc.bRevealed);
    if (cur != want && klh_data((void *)(DWORD_PTR)(tun + KLUCC_O_BOUNTY), &want, 4, "ucchide: bounty for killing the UCC")) {
        klog("ucchide: [tuning+0x674] (criminal kills the UCC) %ld -> %ld (%s)", cur, want, klucc_any_hidden(&klucc_st) ? "a UCC is hidden" : "every UCC revealed");
        klucc.bLast = want;
    }
}

static void klucc_leave(const char *why)
{
    int i;
    if (!klucc_st.on) return;
    klucc_bounty_put(1);
    for (i = 0; i < KLUCC_N; i++) klud_reveal(i, 0);
    klucc_st.on = 0; klucc_st.revealed = 0; klucc.reqUntil = 0; klucc.rules = 0; klucc.window = 0; klucc.uccWas = 0;
    klog("ucchide: off (%s)", why);
}

static void klucc_tick(int game_thread)
{
    static DWORD last;
    DWORD now = GetTickCount(), sm, gs, rules, vt, role = 0, mode = 0, state = 0, sub = 0, n = 0, freeb, score; int i, window, how = 0;
    if (!klucc.on || !game_thread || !klh_exe_ok) return;
    if (klucc_st.on) klucc_keys(now);
    if (now - last < 100) return;
    last = now;
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION));
    if (!sm || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4) || !klh_rd((DWORD_PTR)KLH_VA(KLUCC_SUBMODE), &sub, 4)
        || (role != 2 && role != 3) || mode != 4 || sub != 1) { klucc_leave("no Undercover Cop session"); return; }
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLB_SETTINGS))) || !(rules = klh_rd32(gs + 0x54))) { klucc_leave("no rules object"); return; }
    vt = klh_rd32(rules);
    if (!KLH_RULES_SV_OK(vt) && !KLH_RULES_CL_OK(vt) && vt != (DWORD)(DWORD_PTR)&klud_sv[1] && vt != (DWORD)(DWORD_PTR)&klud_cl[1]) { klucc_leave("rules object is no Sv / Cl"); return; }
    if (!klh_rd(rules + 0x14, &n, 4) || n < 1 || n > KLUCC_N || !(freeb = klh_rd32(rules + 0xc)) || !(score = klh_rd32(rules + 0x2c))) return;
    window = state >= 0x13 && state <= 0x1f;               /* GUESS on a client: klsync.c's round window */
    if (!klucc_st.on) {
        memset(&klucc_st, 0, sizeof klucc_st); klucc_st.me = -1; klucc_st.on = 1; klucc.waitSince = 0;
        klog("ucchide: Undercover Cop session as %s (rules %08lx, state %#lx); RevealKey %#x Strip=%d Feed=%d Rows=%d Bounty=%d (%ld / %ld), channel %s",
             role == 2 ? "HOST" : "CLIENT", (unsigned long)rules, (unsigned long)state, klucc.key, klucc.strip, klucc.feed, klucc.rows, klucc.bounty, klucc.bHidden, klucc.bRevealed, klucc.chan ? "klnetchan" : "NONE");
    }
    klucc_st.host = role == 2;
    if (rules != klucc.rules) { klucc.rules = rules; klucc.meAt = 0; klucc.left = 0; klucc.waitSince = 0; }
    /* the score flags of every client: [[rules+0x2c]+0x98+4i] (what slot 114 = 0x625be0 answers; klbot.c OnlineCrew, klud_flags) */
    klucc_st.n = (int)n;
    for (i = 0; i < (int)n; i++) {
        BYTE b = 1; DWORD f = 0;
        klucc_st.used[i] = klh_rd(freeb + i, &b, 1) && !b && klh_rd(score + 0x98 + 4 * i, &f, 4);
        klucc_st.flags[i] = klucc_st.used[i] ? f : 0;
    }
    if (!klucc.meAt || now - klucc.meAt >= 1000) {
        int me = klucc_find_me(rules, (int)n, &how);
        klucc.meAt = now ? now : 1;
        if (me != klucc_st.me) klog("ucchide: my client index %d (found by %s), flags %08lx%s", me, how == 1 ? "the master test of the records" : how == 2 ? "the local player's crew byte" : how == 3 ? "the stock player list" : "nothing",
                                    me >= 0 ? klucc_st.flags[me] : 0, me >= 0 && klucc_is_ucc(&klucc_st, me) ? " - I AM THE UNDERCOVER COP" : "");
        klucc_st.me = me;
    }
    {   /* a new round? GUESS: [rules+0x4c] is the round clock online as in Arcade (FA base class offset) */
        float left = 0; unsigned long ucc = klucc_ucc_mask(&klucc_st);
        klh_rd(rules + 0x4c, &left, 4);
        if (klucc_round_changed(klucc.left, left, klucc.uccWas, ucc, klucc.window, window)) {
            if (klucc_st.host) { klucc_host_new_round(&klucc_st); klog("ucchide: new round (host): epoch %lu, UCC mask %lx: every UCC hidden", klucc_st.epoch, ucc); }
            else { klucc_client_new_round(&klucc_st, now); klog("ucchide: new round (client): mirror %s, UCC mask %lx", klucc_st.revealed ? "kept (host state just adopted)" : "cleared", ucc); }
            klucc.reqUntil = 0;
        }
        klucc.left = left; klucc.uccWas = ucc; klucc.window = window;
    }
    for (i = 0; i < KLUCC_N; i++) klud_reveal(i, (klucc_st.revealed >> i) & 1);    /* klucc_down.c: the down-only cap ends for a revealed UCC (it clears its bits on a new rules object) */
    klucc_wrap(rules, now);
    klucc_net(now);
    klucc_bounty_put(0);
}

static void klucc_init(void)
{
    klucc_st.me = -1;
    klucc.on = GetPrivateProfileIntA("Ucc", "Hide", 0, klh_ini) != 0;
    if (!klucc.on) return;
    klucc.key = klkeys_vk(KK_REVEAL) & 0xff;
    klucc.strip = GetPrivateProfileIntA("Ucc", "Strip", 1, klh_ini) != 0;
    klucc.feed = GetPrivateProfileIntA("Ucc", "Feed", 1, klh_ini) != 0;
    klucc.rows = GetPrivateProfileIntA("Ucc", "Rows", 1, klh_ini) != 0;
    klucc.bounty = GetPrivateProfileIntA("Ucc", "Bounty", 1, klh_ini) != 0;
    klucc.bHidden = (long)(int)GetPrivateProfileIntA("Ucc", "BountyHidden", 200000, klh_ini);
    klucc.bRevealed = (long)(int)GetPrivateProfileIntA("Ucc", "BountyRevealed", 400000, klh_ini);
    klucc.log = (int)GetPrivateProfileIntA("Ucc", "HideLog", 1, klh_ini);
    if (klucc.bHidden < 0 || klucc.bHidden > 10000000) klucc.bHidden = 200000;
    if (klucc.bRevealed < 0 || klucc.bRevealed > 10000000) klucc.bRevealed = 400000;
    if (klucc.key == 0x74 && GetPrivateProfileIntA("Ucc", "Accuse", 0, klh_ini)) klog("ucchide: RevealKey=0x74 is also [Ucc] Key (F5, accuse): one press does both");
    klucc.reqIdx = -1;
    klucc_feed_on = klucc.feed; klucc_hud_on = klucc.rows;
    klucc.chan = knc_want("ucchide (UCC reveal)");
    knc_on("UHID", klucc_on_state); knc_on("UREV", klucc_on_req);
    klog("ucchide: ON (NOT yet run live): RevealKey %#x Strip=%d Feed=%d Rows=%d Bounty=%d hidden %ld revealed %ld; channel %s", klucc.key, klucc.strip, klucc.feed, klucc.rows, klucc.bounty, klucc.bHidden, klucc.bRevealed, klucc.chan ? "klnetchan (UHID / UREV)" : "none");
}

#endif /* KLUCCHIDE_C */
