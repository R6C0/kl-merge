/*
 * klhire_online.c - HIRE a heister in the ONLINE Fragile Alliance shop (private match / Steam FA). re\shop_hire.md section 8.
 * Part of KLHook, included by klhook.c AFTER klucchide.c (klucc_find_me), klnetchan.c (knc_*) and klcharonline.c (klco, klc_char publishing).
 * Heap data writes and calls of two game routines (the shop's own money spenders) from the game's thread; no code byte of kl2.exe changes
 * (SHIP-safe). NOT RUN IN THE GAME (written 2026-10-27).
 *
 * WHY THIS DESIGN (read from kl2.exe, 2026-10-27, see the doc):
 *   The stock shop buys on the HOST: the client sends a buy message, the host's handler 0x55d3e0 adds up the price, compares it with
 *   (TotalLootMoney 0x622e10 + TotalRewardMoney 0x639c10) of that seat (both thiscall(S, seat) ret 4, S = [rules+0x2c]), returns silently
 *   when it is too dear, else spends with 0x6b1910(S, seat, n) (the first store) and 0x7f6950(S, seat, rest) (the second), which mark
 *   the dirty mask so the score object REPLICATES to every client. A client cannot be trusted to write its own money, and a write on a
 *   client would be overwritten by the next replication. So:
 *     client  : presses the KLHire<n> row -> sends HIRE/Q (seat, row, rank) to the host through klnetchan.c; nothing is charged locally
 *     host    : checks (not in a round, body exists, nobody wears / has hired it, rank, money) -> spends with the game's own two routines
 *               -> answers HIRE/A (seat, row, ok, reason)
 *     client  : on ok it shows the row HIRED (klhr_next); at the next round's start klc_char = the hired body for ONE round, then back
 *     body    : klcharonline.c publishes klc_char as klx_look / UDP 27414 to every peer, which apply it by entity (its Unique rule then
 *               also keeps two peers off one character). No change of klcharonline.c is needed.
 *   The host plays too: its own press takes the same path without a message.
 *
 * ONE CHARACTER PER MATCH: the host refuses a row that another peer wears (klco.p[].c, the raw announced choice), that the host itself
 * wears, or that another seat has hired for the next round (paid[]). klcharonline's Unique stays as the second guard on every screen.
 *
 * GUESS list (every one is also marked at its line):
 *   G1 the shop is open whenever the session state is not 0x19 (round); the same 'phase' idea as klhire.c, online state numbers unproven
 *   G2 a client's seat number in HIRE/Q is trusted (private match / friends); the host only checks it is a seat in use and not its own
 *   G3 the client's rank in HIRE/Q is trusted (the host cannot read another player's profile)
 *   G4 both getters / spenders take the seat as the first stack argument and S as ecx (fastcall(S, 0, seat[, amount]) matches ret 4 / ret 8)
 *   G5 the replicated score object updates the client's shop money text on its own (stock does it after its own buys)
 *
 * KLHook.ini
 *   [Hire]
 *   Enable=1           the Arcade hire switch (also needed here: it makes the KLHire<n> rows answer)
 *   Online=0           1 = hire online as described above (needs [NetChan] reachable, [CharOnline] Enable=1, [Character] Enable=1)
 *   OnlineLog=1
 */
#ifndef KLHIRE_ONLINE_C
#define KLHIRE_ONLINE_C

#define KLHRO_SEATS 12
#define KLHRO_ASKMS 6000                       /* a client gives up waiting for the host's answer after this */

static struct {
    int on, log;
    int paid[KLHRO_SEATS];                     /* host: the row each seat has paid for the next round (0 none) */
    int pend; DWORD pendAt;                    /* client: the row asked, waiting for HIRE/A */
    int phase0, act, save;                     /* last phase (0 none, 1 round, 2 shop), the hired body worn now, klc_char before it */
    int told;
} klhro;

/* ---- the pure decisions (no game reads): kept in one place so the reasons are the same on the host and in the log ---- */
enum { KLHRO_OK = 0, KLHRO_ROUND = 1, KLHRO_BADROW = 2, KLHRO_NOBODY = 3, KLHRO_TAKEN = 4, KLHRO_RANK = 5, KLHRO_MONEY = 6, KLHRO_PAID = 7, KLHRO_NOTREADY = 8, KLHRO_WRITE = 9 };
static const char *klhro_why(int c)
{
    switch (c) {
    case KLHRO_OK: return "ok"; case KLHRO_ROUND: return "a round is running"; case KLHRO_BADROW: return "no such heister";
    case KLHRO_NOBODY: return "this level has no body for him"; case KLHRO_TAKEN: return "another player wears or has hired him";
    case KLHRO_RANK: return "rank too low"; case KLHRO_MONEY: return "not enough money"; case KLHRO_PAID: return "already hired for the next round";
    case KLHRO_NOTREADY: return "host not ready"; case KLHRO_WRITE: return "host could not charge"; }
    return "?";
}

static int klhro_phase(void)
{   /* GUESS G1: 0x19 = a round (re\online_round_data.md); any other state with a session = the shop / lobby side */
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(KLC_SESSION)), st = 0;
    if (!sm || !klh_rd(sm + 0x70, &st, 4)) return 0;
    return st == 0x19 ? 1 : 2;
}

static int klhro_host(void)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(KLC_SESSION)), role = 0;
    return sm && klh_rd(sm + 0x54, &role, 4) && role == 2;
}

/* the online FA rules object (Sv / Cl) and its score object; 0 when anything differs */
static int klhro_rules(DWORD *rules, DWORD *score)
{
    DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4)), r, s, vt;
    if (!gs || !(r = klh_rd32(gs + 0x54)) || !(vt = klh_rd32(r)) || !(KLH_RULES_SV_OK(vt) || KLH_RULES_CL_OK(vt))) return 0;
    if (!(s = klh_rd32(r + 0x2c)) || klh_rd32(s) != 0xbd5184) return 0;
    if (rules) *rules = r;
    if (score) *score = s;
    return 1;
}

/* my seat = my index in the crew; -1 unknown */
static int klhro_myseat(DWORD rules)
{
    DWORD n = 0; int how = 0, me;
    if (!klh_rd(rules + 0x14, &n, 4) || n == 0 || n > 16) return -1;
    me = klucc_find_me(rules, (int)n, &how);
    return me >= 0 && me < KLHRO_SEATS ? me : -1;
}

static int klhro_seat_used(DWORD rules, int seat)
{
    DWORD n = 0, fr; BYTE b = 1;
    if (seat < 0 || seat >= KLHRO_SEATS || !klh_rd(rules + 0x14, &n, 4) || (DWORD)seat >= n) return 0;
    return (fr = klh_rd32(rules + 0xc)) && klh_rd(fr + seat, &b, 1) && !b;
}

/* the shop money of a seat: first + second store, the game's own getters (G4) */
/* first-bytes guard (audit 1027): the four game routines are called blind; a different kl2.exe build would run foreign code. Bytes read from the Steam kl2.exe 2026-10-27:
   getters = add ecx,0x58 / jmp rel32; spenders = sub esp,8 / push ebx / mov ebx,[esp+0x10] / push esi / push edi / mov edi,ecx (0x6b1910 and 0x7f6950 start alike, 8 bytes compared). Refuse + log once on mismatch. */
static int klhro_code_ok(void)
{
    static const BYTE g1[] = { 0x83, 0xc1, 0x58, 0xe9 }, sp[] = { 0x83, 0xec, 0x08, 0x53, 0x8b, 0x5c, 0x24, 0x10 };
    static int ok = -1;
    if (ok < 0) {
        ok = klc_same_code(0x622e10, g1, sizeof g1) && klc_same_code(0x639c10, g1, sizeof g1) && klc_same_code(0x6b1910, sp, sizeof sp) && klc_same_code(0x7f6950, sp, sizeof sp);
        if (!ok) klog("hire-online: refused: the money routines 0x622e10 / 0x639c10 / 0x6b1910 / 0x7f6950 are not the ones this build knows (other kl2.exe?); nothing is read or charged");
    }
    return ok;
}

static int klhro_money(DWORD S, int seat, DWORD *first, DWORD *second)
{
    DWORD a, b;
    if (!S || seat < 0 || seat >= KLHRO_SEATS || !klhro_code_ok()) return 0;
    a = ((DWORD (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(0x622e10))((void *)(DWORD_PTR)S, 0, seat);
    b = ((DWORD (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(0x639c10))((void *)(DWORD_PTR)S, 0, seat);
    *first = a; *second = b;
    return 1;
}

/* the spend, exactly as 0x55d3e0 does it: price < first -> only the first store; else the whole first store and the rest from the second */
static void klhro_spend(DWORD S, int seat, DWORD price, DWORD first)
{
    typedef void (__fastcall *spend_t)(void *, void *, int, DWORD);
    spend_t sp1 = (spend_t)(DWORD_PTR)KLH_VA(0x6b1910), sp2 = (spend_t)(DWORD_PTR)KLH_VA(0x7f6950);
    if (!klhro_code_ok()) return;
    if (price < first) { sp1((void *)(DWORD_PTR)S, 0, seat, price); return; }
    sp1((void *)(DWORD_PTR)S, 0, seat, first);
    sp2((void *)(DWORD_PTR)S, 0, seat, price - first);
}

/* is a character worn / hired by someone other than 'seat'? (raw announced choices; the host cannot map seats to entities, so any peer counts: conservative) */
static int klhro_taken(int row, int seat)
{
    int j;
    if ((int)klc_char == row && klhro.act != row) return 1;                          /* the host's own page choice (a hired body is the host's own) */
    for (j = 0; j < KLCO_N; j++) if (klco.p[j].used && klco.p[j].c == row) return 1;
    for (j = 0; j < KLHRO_SEATS; j++) if (j != seat && klhro.paid[j] == row) return 1;
    return 0;
}

/* HOST: judge and charge one request. -> a KLHRO_ reason (0 = paid) */
static int klhro_decide(int seat, int row, int rank, int *newtotal)
{
    DWORD rules = 0, S = 0, a = 0, b = 0, price;
    if (row < 1 || row > KLHR_N) return KLHRO_BADROW;
    if (!klhro_rules(&rules, &S) || !klhro_seat_used(rules, seat)) return KLHRO_NOTREADY;
    if (klhro_phase() == 1) return KLHRO_ROUND;
    if (klhro.paid[seat] == row) return KLHRO_OK;                                    /* a repeated request: answered ok, charged once */
    if (klhro.paid[seat]) return KLHRO_PAID;
    if (!klhr_avail(row)) return KLHRO_NOBODY;
    if (klhro_taken(row, seat)) return KLHRO_TAKEN;
    if (klhr_rankgate && rank >= 0 && rank < klhr_need[row]) return KLHRO_RANK;     /* G3: rank as reported, -1 = the client could not read it */
    price = (DWORD)klhr_price[row];
    if (!klhro_money(S, seat, &a, &b)) return KLHRO_NOTREADY;
    if ((unsigned __int64)a + b < price) return KLHRO_MONEY;
    klhro_spend(S, seat, price, a);
    klhro.paid[seat] = row;
    if (newtotal) { DWORD a2 = 0, b2 = 0; klhro_money(S, seat, &a2, &b2); *newtotal = (int)(a2 + b2); }
    if (klhro.log) klog("hire-online: seat %d hired %s for $%lu (money %lu -> after the spend, replicated by the score object); takes effect at the next round's start", seat, klhr_name[row], (unsigned long)price, (unsigned long)(a + b));
    return KLHRO_OK;
}

/* ---- messages ---- */
static void klhro_on_ask(const struct knc_msg *m, int src)
{   /* HOST: HIRE Q s<seat>r<row>k<rank> */
    int seat = -1, row = 0, rank = -1, why, nt = 0; char pay[48]; DWORD rules = 0;
    (void)src;
    if (!klhro.on || !klhro_host() || m->role != 3) return;
    if (m->payload[0] != 'Q' || sscanf(m->payload + 1, "s%dr%dk%d", &seat, &row, &rank) < 2) return;
    if (klhro_rules(&rules, 0) && seat == klhro_myseat(rules)) { if (klhro.log) klog("hire-online: ignored a request for the host's own seat %d", seat); return; }   /* G2 */
    why = klhro_decide(seat, row, rank, &nt);
    if (klhro.log && why) klog("hire-online: seat %d asked for %s: refused, %s", seat, row >= 1 && row <= KLHR_N ? klhr_name[row] : "?", klhro_why(why));
    snprintf(pay, sizeof pay, "As%dr%do%dm%d", seat, row, why == KLHRO_OK, why);
    knc_send("HIRE", pay, -1);
}

static void klhro_on_answer(const struct knc_msg *m, int src)
{   /* CLIENT: HIRE A s<seat>r<row>o<ok>m<reason> */
    int seat = -1, row = 0, ok = 0, why = 0; DWORD rules = 0;
    (void)src;
    if (!klhro.on || klhro_host() || m->role != 2) return;
    if (m->payload[0] != 'A' || sscanf(m->payload + 1, "s%dr%do%dm%d", &seat, &row, &ok, &why) < 3) return;
    if (!klhro_rules(&rules, 0) || seat != klhro_myseat(rules)) return;
    if (klhro.pend != row && !(ok && !klhr_next)) return;         /* a late 'ok' (after the 6 s timeout) is still taken: the host has charged this seat, so the body must be worn (the host judged it, seat checked above) */
    klhro.pend = 0;
    if (ok) { klhr_next = row; if (klhro.log) klog("hire-online: the host accepted: %s hired for the next round", row >= 1 && row <= KLHR_N ? klhr_name[row] : "?"); }
    else klog("hire-online: the host refused %s: %s", row >= 1 && row <= KLHR_N ? klhr_name[row] : "?", klhro_why(why));
}

/* from klhr_set when kl_online(): the player pressed KLHire<row>. Returns 1 when this file handled it (even a refusal). */
/* ONE channel type 'HIRE' (payload 'Q...' = ask, 'A...' = answer): klnetchan.c holds only KNC_HANDLERS = 8 types and kldown_mirror (2) + klucc (3) + klucchide (2) already take 7;
   two types here made 9 and the 9th (HIREA) was silently dropped, so a client never heard the host's answer when all of them were on (audit 2026-10-27). */
static void klhro_on_msg(const struct knc_msg *m, int src)
{
    if (m->payload[0] == 'Q') klhro_on_ask(m, src); else if (m->payload[0] == 'A') klhro_on_answer(m, src);
}

static int klhro_set(int row)
{
    DWORD rules = 0; int seat, rank = -1, why;
    if (!klhro.on) { static int told; if (!told++) klog("hire: refused: a network session and [Hire] Online=0 (online hire is off)"); return 1; }
    if (klhr_next == row) return 1;
    if (klhr_next) { klog("hire-online: %s refused: %s is already hired for the next round", klhr_name[row], klhr_name[klhr_next]); return 1; }
    if (klhro_phase() == 1) { klog("hire-online: %s refused: a round is running; hire on the shop page between rounds", klhr_name[row]); return 1; }
    if (!klhro_rules(&rules, 0) || (seat = klhro_myseat(rules)) < 0) { klog("hire-online: %s refused: not in an online FA round / own seat unknown", klhr_name[row]); return 1; }
    if (!klhr_avail(row)) { klog("hire-online: %s refused: this level has no body for him (no wardrobe); nothing charged", klhr_name[row]); return 1; }
    if (klhr_rankgate && !klhr_rank(&rank)) rank = -1;
    if (klhro_host()) {
        why = klhro_decide(seat, row, rank, 0);
        if (why) klog("hire-online: %s refused: %s", klhr_name[row], klhro_why(why));
        else { klhr_next = row; klhro.paid[seat] = row; }
        return 1;
    }
    {
        char pay[48]; unsigned q;
        if (klhro.pend && GetTickCount() - klhro.pendAt < KLHRO_ASKMS) { klog("hire-online: %s: still waiting for the host's answer about %s", klhr_name[row], klhr_name[klhro.pend]); return 1; }
        snprintf(pay, sizeof pay, "Qs%dr%dk%d", seat, row, rank);
        q = knc_send("HIRE", pay, -1);
        if (!q) { klog("hire-online: %s: the message channel is not open (no session / [NetChan] off), nothing sent", klhr_name[row]); return 1; }
        klhro.pend = row; klhro.pendAt = GetTickCount();
        if (klhro.log) klog("hire-online: asked the host for %s (seat %d, rank %d)", klhr_name[row], seat, rank);
    }
    return 1;
}

/* from klhr_tick, every frame: the round clock. Applies the hired body at the round's start and takes it back at its end. */
static void klhro_tick(void)
{
    int ph;
    if (!klhro.on) return;
    if (klhro.pend && GetTickCount() - klhro.pendAt >= KLHRO_ASKMS) { klog("hire-online: no answer from the host about %s (%d ms): nothing charged on this side", klhr_name[klhro.pend], KLHRO_ASKMS); klhro.pend = 0; }
    ph = klhro_phase();
    {   /* stale state (audit 1027): no session (left / level change) or a NEW rules object (new level or lobby) forgets paid[] / act / pending, so 'already hired' cannot outlive the match. GUESS: a new level / lobby allocates a NEW rules object and one match keeps the same one through shop and round; if the object were rebuilt between a shop hire and the round start, paid[] would be forgotten early and a seat could be charged twice (bench it) */
        DWORD r = 0; static DWORD lastr; int j;
        if (!ph || (klhro_rules(&r, 0) && lastr && r != lastr)) {
            for (j = 0; j < KLHRO_SEATS; j++) klhro.paid[j] = 0;
            klhro.pend = 0; klhro.phase0 = 0; if (!ph) klhr_next = 0;
            if (klhro.act) { if ((int)klc_char == klhro.act) klc_char = klhro.save; klhro.act = 0; }
            lastr = 0;
        }
        if (ph && r) lastr = r;
    }
    if (!ph) return;
    if (ph == 1 && klhro.phase0 != 1) {
        int j;
        if (klhr_next && klhr_avail((int)klhr_next)) {
            klhro.save = (int)klc_char; klhro.act = (int)klhr_next; klc_char = klhro.act;
            klog("hire-online: round starts: I wear %s (hired; the Heister page choice %d returns after the round)", klhr_name[klhro.act], klhro.save);
        }
        klhr_next = 0;
        if (klhro_host()) for (j = 0; j < KLHRO_SEATS; j++) klhro.paid[j] = 0;      /* the hires of the shop page are spent */
    }
    if (ph == 2 && klhro.phase0 == 1 && klhro.act) {
        if ((int)klc_char == klhro.act) klc_char = klhro.save;
        klog("hire-online: round over: the hired body is given back, Heister page choice %d", klhro.save);
        klhro.act = 0;
    }
    klhro.phase0 = ph;
}

static void klhro_init(void)
{
    klhro.on = klhr_on && GetPrivateProfileIntA("Hire", "Online", 0, klh_ini) != 0;
    klhro.log = GetPrivateProfileIntA("Hire", "OnlineLog", 1, klh_ini);
    if (!klhro.on) return;
    knc_want("hire-online");
    knc_on("HIRE", klhro_on_msg);
    klog("hire-online: on (client asks, host judges and spends with the game's own routines, the body travels by klcharonline's look channel). Needs [NetChan], [CharOnline] Enable=1, [Character] Enable=1. NOT RUN IN THE GAME");
}

#endif /* KLHIRE_ONLINE_C */
