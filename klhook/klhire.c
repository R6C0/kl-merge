/*
 * klhire.c - HIRE a heister in the Arcade buy shop (re\shop_hire.md, option B, stage 1). Part of KLHook, included by
 * klchar.c (after klc_w, before the option wrappers). Heap data writes and calls of three game routines from the game's
 * own thread; no code byte of kl2.exe changes (SHIP-safe). NOT RUN IN THE GAME (written 2026-10-26, owner offline-test only).
 *
 * WHAT IT DOES (owner decisions 2026-10-24, re\shop_hire.md "Owner decisions"):
 *   - every ROUND starts with a heister: a random default (never Kane or Lynch, they are hire-only) or the one the player HIRED
 *     on the shop page of the round before. A hire lasts ONE round. Round 1 can only be the random default (the bank starts at 0).
 *   - [Hire] Enable=1 switches klchar.c's body choice over to this: KLChar of the Heister page ([Character] Char=) is then only a
 *     wish that is NOT used (said once); KLMask / KLOutfit stay as they are. Enable=0 (default): this file is inert, the three
 *     option names below are not answered, klchar.c behaves exactly as before.
 *
 * THE MENU SIDE (window FAHire of tools\kl_hire_bake.py, in the level's Menu\online.xml)
 *   (the names are answered whether or not Enable=1: a level baked with the window must not hand KLHire<n> to the stock option code)
 *   16 rows, each a ToggleText with two <Text> children bound to the option KLHire<n> (n = the KLChar number 1..16: 1..8 Dog Days,
 *   9 Kane, 10 Lynch, 11..16 the six other Dead Men heisters). Child 0 = "<name>  $price  rank r", child 1 = "<name> - HIRED for the next
 *   round". Option range 0..1, so pressing the row (Select / Right) calls Set(KLHire<n>, 1) = "buy". Set(.., 0) is ignored.
 *   Get(KLHire<n>) = 1 while n is the heister bought for the next round, else 0, so a refused purchase shows no HIRED text
 *   (GUESS: the widget re-reads the option after the set; if it caches its own value, the row looks hired though the log says
 *   'refused'). The row texts are BAKED from the same price table by the bake tool; the hook enforces ITS table ([Hire] Price<n>/Rank<n>).
 *   This is NOT routed through klc_set: the Heister page's [Character] Char= is never written by a hire.
 *
 * THE RULES (every refusal and every charge is one log line, 'hire:')
 *   - Arcade only (session mode 4, rules = ZGameRulesHeist 0xbd3514), not kl_online(), not while a round runs (state 0x12..0x1e).
 *     GUESS: the shop is open in states 0x1f..0x28 (0x1f/0x20 = the score page). An unknown state does not refuse.
 *   - one hire per shop visit round: a second row while one is paid is refused (no refund path in stage 1).
 *   - body available: a Dead Men heister needs this level's wardrobe (klc_w), else refused without charge.
 *   - RANK: the FA experience rank 0..7 of the local profile, the game's own reader (0x4d04c0 -> vtable+0x140 -> +0x15b8 -> word +0x90
 *     -> 0x5103e0, the chain of the shop's own lock 0x7f74a0..0x7f74d1; read in the disassembly 2026-10-26: `push 0` before the
 *     vtable call is the argument of the NEXT call 0x78a8b0, the vtable function takes none). If the read cannot be done (code differs,
 *     pointer unreadable) the rank gate is skipped and only the price counts ('rank read failed' in the log). [Hire] Rank=0 skips it.
 *   - MONEY: Arcade's banked total, ONE dword [[rules+0x5f8]+0x38] (the shop's own purse: read 0x7f7434, spent 0x8eaa3f..0x8eaa4a).
 *     Afford test total >= price, then total -= price (heap data). GUESS: the FATotal text redraws on its own; the game's own
 *     server sync does not overwrite the write (the same write is made by klfedkit.c, whose live status is not proven either).
 *   - round clock: 'phase' 1 = a round runs (session state [[0x168e598]+0x70] 0x12..0x1e), 2 = the end / score / shop phase
 *     (0x1f..0x28). When phase 1 is entered from phase 2 (or the first time on a level): the paid hire becomes the body of this
 *     round and is spent, else a new random default is drawn; klchar.c's tick then swaps the body (its own attach path, tries reset).
 *     The swap is NOT made during the shop, only at the round's start (critic gap 3).
 *   - [Hire] Bots=1 is NOT BUILT in this pass (the bank of a bot, the escaped-take column and a reset rule are all GUESSES, re\shop_hire.md 6):
 *     the key is read and said once, nothing else happens.
 *
 * KLHook.ini
 *   [Hire]
 *   Enable=0            1 = hire on (the Heister page's body pick is then ignored). Needs [Character] Enable=1.
 *   Rank=1              0 = no rank gate (price only)
 *   Bots=0              reserved (not built)
 *   Log=1
 *   Price1=45000 .. Price16=..   Rank1=0 .. Rank16=..    (defaults: the owner's x4.5 table, klhr_defp / klhr_defr below)
 */
#ifndef KLHIRE_C
#define KLHIRE_C

#define KLHR_N          16
#define KLHR_RANKFN     0x005103e0
#define KLHR_SESSIONOBJ 0x01686e60             /* the profile manager object (immediate in the game's code: mov ecx, 0x1686e60) */
#define KLHR_GETOBJ     0x004d04c0             /* thiscall(obj, int i) ret 4: [[obj+0xc] + 4*i] */
#define KLHR_VT_PROFILE 0x140                  /* vtable slot, no arguments: the profile data */
#define KLHR_PROF_XP    (0x15b8 + 0x90)        /* profile + 0x15b8 + player 0 * 0xc8, word +0x90 = FA experience */
#define KLHR_S_SCORE    0x5f8                  /* rules: the score object (klfedkit.c KLFK_SCORE) */
#define KLHR_S_TOTAL    0x38                   /* score: the banked total the shop buys from */

static int klhr_on, klhr_log = 1, klhr_rankgate = 1, klhr_bots;
static int klhr_price[KLHR_N + 1], klhr_need[KLHR_N + 1];
static const char *const klhr_name[KLHR_N + 1] = { "", "J.C.", "Tommy", "Pierre", "Liam", "Jean", "Elwood", "Bud", "Mitchel",
                                                   "Kane", "Lynch", "Ashkanan", "Meldal", "Red", "Parker", "Standen", "Hutchison" };
/* the owner's table (re\shop_hire.md 5 x 4.5, 2026-10-24). Within a band the split of price and rank is MINE (GUESS): the doc gives only the ranges. */
static const int klhr_defp[KLHR_N + 1] = { 0, 45000, 45000, 45000, 45000, 90000, 90000, 90000, 90000, 450000, 540000, 180000, 180000, 225000, 225000, 270000, 270000 };
static const int klhr_defr[KLHR_N + 1] = { 0, 0, 0, 1, 1, 2, 2, 3, 3, 6, 7, 4, 4, 4, 5, 5, 5 };

static volatile LONG klhr_next;                /* bought for the next round (KLChar number), 0 = none */
static volatile LONG klhr_body;                /* the body of the round now (KLChar number), 0 = not drawn yet */
static volatile LONG klhr_gen;                 /* +1 at every drawing: klchar.c resets its attach tries */
static DWORD klhr_rules0;                      /* the rules object the state belongs to */
static int klhr_phase0;                        /* last phase seen: 0 none, 1 round, 2 end / shop */
static int klhr_round;
static DWORD klhr_seed = 0x2545f491u;

static int klhro_set(int row);                 /* klhire_online.c (included later by klhook.c) */
static void klhro_tick(void);

static int klhr_state(DWORD *st, DWORD *mode)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(KLC_SESSION)); *st = 0; *mode = 0;
    return sm && klh_rd(sm + 0x70, st, 4) && klh_rd(sm + 0x5c, mode, 4);
}

static int klhr_phase_of(DWORD st) { return (st >= 0x12 && st <= 0x1e) ? 1 : (st >= 0x1f && st <= 0x28) ? 2 : 0; }

/* the Arcade heist rules and their score object; 0 when anything differs */
static int klhr_arcade(DWORD *rules, DWORD *score)
{
    DWORD st, mode, gs, r, s;
    if (!klhr_state(&st, &mode) || mode != 4) return 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLC_SETTINGS))) || !(r = klh_rd32(gs + 0x54)) || klh_rd32(r) != KLC_RULES_VT) return 0;
    s = klh_rd32(r + KLHR_S_SCORE);
    if (rules) *rules = r;
    if (score) *score = s;
    return 1;
}

/* Can this body exist on this level? a Dog Days heister always; a Dead Men one only with the level's wardrobe (klchar.c's own condition). */
static int klhr_avail(int ch)
{
    if (ch >= 1 && ch <= 8) return 1;
    return ch > 8 && ch <= KLHR_N && klc_w.on && ch <= klc_w.n && !klc_w.c[ch - 1].stock;
}

/* The FA experience rank 0..7 of the local profile, the game's own function. -> 1 = *rank valid, 0 = could not be read (price only). */
static int klhr_rank(int *rank)
{
    static const BYTE rank_code[4] = { 0x83, 0xec, 0x14, 0xa1 };                                              /* 0x5103e0 sub esp,0x14 ; mov eax,[cookie] */
    static const BYTE get_code[10] = { 0x8b, 0x41, 0x0c, 0x85, 0xc0, 0x75, 0x03, 0xc2, 0x04, 0x00 };          /* 0x4d04c0 mov eax,[ecx+0xc] ; test ; jne ; ret 4 */
    DWORD obj = (DWORD)(DWORD_PTR)KLH_VA(KLHR_SESSIONOBJ), arr, p, vt, fn, prof, xp = 0;
    int r;
    if (!klc_same_code(KLHR_RANKFN, rank_code, sizeof rank_code) || !klc_same_code(KLHR_GETOBJ, get_code, sizeof get_code)) return 0;
    if (!(arr = klh_rd32(obj + 0xc))) return 0;
    p = ((DWORD (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLHR_GETOBJ))((void *)(DWORD_PTR)obj, 0, 0);
    if (!p || p < 0x10000 || !(vt = klh_rd32(p)) || !(fn = klh_rd32(vt + KLHR_VT_PROFILE))) return 0;
    if (fn < (DWORD)(DWORD_PTR)KLH_VA(0x401000) || fn >= (DWORD)(DWORD_PTR)KLH_VA(0xb00000)) return 0;      /* inside the exe's code */
    prof = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)fn)((void *)(DWORD_PTR)p, 0);
    if (!prof || prof < 0x10000 || !klh_rd(prof + KLHR_PROF_XP, &xp, 2)) return 0;
    xp &= 0xffff;
    r = (signed char)((int (__cdecl *)(int))(DWORD_PTR)KLH_VA(KLHR_RANKFN))((int)xp);
    if (r < 0 || r > 7) return 0;
    *rank = r;
    if (klhr_log) { static int told; if (told++ < 3) klog("hire: profile experience %lu = rank %d (the game's own reader)", xp, r); }
    return 1;
}

/* a random default, never Kane (9) or Lynch (10), only bodies this level has */
static int klhr_roll(void)
{
    int pool[KLHR_N], n = 0, i;
    for (i = 1; i <= KLHR_N; i++) if (i != 9 && i != 10 && klhr_avail(i)) pool[n++] = i;
    if (!n) return 1;
    klhr_seed = klhr_seed * 1664525u + 1013904223u + GetTickCount();
    return pool[(klhr_seed >> 16) % (DWORD)n];
}

static int klhr_row(const char *name)
{   /* "KLHire1".."KLHire16" -> 1..16, else 0; the game hands a plain C string, anything unreadable is not ours */
    char n[16]; int v;
    if (!name || !klh_rd((DWORD_PTR)name, n, 3) || n[0] != 'K' || n[1] != 'L' || n[2] != 'H') return 0;
    if (!klh_rdstr((DWORD_PTR)name, n, sizeof n) || strncmp(n, "KLHire", 6) || n[6] < '1' || n[6] > '9') return 0;
    v = atoi(n + 6);
    if (v < 1 || v > KLHR_N || (v < 10 ? n[7] != 0 : n[8] != 0)) return 0;
    return v;
}

static int klhr_get(int row) { return klhr_on && klhr_next == row; }       /* the name is answered even with Enable=0 (reads 0), so a baked window never reaches the stock option code */

/* Set(KLHire<row>, value): value 1 = try to buy */
static void klhr_set(int row, int value)
{
    DWORD rules = 0, score = 0, total = 0, st = 0, mode = 0; int rank = 0, have, price, phase; LONG next;
    if (!value) return;
    if (!klhr_on) { static int told; if (!told++) klog("hire: refused: [Hire] Enable=0 (the Hire window is baked into this level but the hook feature is off)"); return; }
    next = klhr_next;
    if (next == row) return;                                                         /* already paid: nothing to do */
    if (kl_online()) { klhro_set(row); return; }                                    /* klhire_online.c: client asks the host, the host judges (off unless [Hire] Online=1) */
    if (!klhr_arcade(&rules, &score) || !score) { klog("hire: %s refused: not an Arcade heist round (no rules / score object)", klhr_name[row]); return; }
    klhr_state(&st, &mode); phase = klhr_phase_of(st);
    if (phase == 1) { klog("hire: %s refused: a round is running (state 0x%lx); hire on the shop page between rounds", klhr_name[row], st); return; }
    if (next) { klog("hire: %s refused: %s is already hired for the next round (stage 1 has no refund / change)", klhr_name[row], klhr_name[next]); return; }
    if (!klhr_avail(row)) { klog("hire: %s refused: this level has no body for him (no wardrobe); nothing charged", klhr_name[row]); return; }
    price = klhr_price[row];
    have = klhr_rankgate ? klhr_rank(&rank) : 0;
    if (klhr_rankgate && !have) { static int told; if (!told++) klog("hire: rank read failed (code or pointers differ): price only, no rank gate"); }
    if (have && rank < klhr_need[row]) { klog("hire: %s refused: rank %d needed, you are rank %d", klhr_name[row], klhr_need[row], rank); return; }
    if (!klh_rd(score + KLHR_S_TOTAL, &total, 4)) { klog("hire: %s refused: the banked total is unreadable (score %08lx)", klhr_name[row], score); return; }
    if ((int)total < price) { klog("hire: %s refused: costs %d, banked total %d", klhr_name[row], price, (int)total); return; }
    {
        DWORD nt = total - (DWORD)price;
        if (!klh_data((void *)(DWORD_PTR)(score + KLHR_S_TOTAL), &nt, 4, "Arcade score: the total (hire)")) { klog("hire: %s refused: the banked total could not be written", klhr_name[row]); return; }
        klhr_next = row;
        char rk[12]; if (have) snprintf(rk, sizeof rk, "%d", rank); else strcpy(rk, "unread");
        klog("hire: %s $%d total %d -> %d rank %s (state 0x%lx; takes effect at the next round's start)", klhr_name[row], price, (int)total, (int)nt, rk, st);
    }
}

/* each tick: the round clock. Draws the body at the START of a round (phase 2 -> 1, or the first time on a level / new rules object). */
static void klhr_tick(void)
{
    DWORD st, mode, rules = 0; int phase, hired, body;
    if (!klhr_on) return;
    if (kl_online()) { klhr_body = 0; klhro_tick(); return; }                     /* online: klhire_online.c (the body stays the game's own unless a hire was paid) */
    if (!klhr_state(&st, &mode) || mode != 4) return;
    if (!klhr_arcade(&rules, 0)) return;
    if (rules != klhr_rules0) { klhr_rules0 = rules; klhr_phase0 = 0; klhr_next = 0; klhr_body = 0; klhr_round = 0; }
    phase = klhr_phase_of(st);
    if (!phase) return;
    if (phase == 1 && klhr_phase0 != 1) {
        hired = (int)klhr_next;
        if (hired && !klhr_avail(hired)) hired = 0;                                  /* paid on another level: no body here (his money stays spent; said) */
        body = hired ? hired : klhr_roll();
        klhr_next = 0; klhr_body = body; klhr_gen++; klhr_round++;
        if (klhr_log) klog("hire: round %d starts (state 0x%lx): body %d %s = %s", klhr_round, st, body, klhr_name[body], hired ? "HIRED" : "random default");
    }
    klhr_phase0 = phase;
}

/* the body klchar.c's tick applies: the drawn one when hire is on, else 0 ('the choice of the Heister page') */
static int klhr_effective(void) { return klhr_on ? (int)klhr_body : -1; }

/* from klc_level_open: a new level is a new session of rounds */
static void klhr_level_reset(void) { klhr_rules0 = 0; klhr_phase0 = 0; klhr_next = 0; klhr_body = 0; klhr_round = 0; }

static void klhr_init(void)
{
    int i; char k[16];
    klhr_on = GetPrivateProfileIntA("Hire", "Enable", 0, klh_ini) != 0;
    klhr_log = GetPrivateProfileIntA("Hire", "Log", 1, klh_ini);
    klhr_rankgate = GetPrivateProfileIntA("Hire", "Rank", 1, klh_ini) != 0;
    klhr_bots = GetPrivateProfileIntA("Hire", "Bots", 0, klh_ini);
    for (i = 1; i <= KLHR_N; i++) {
        snprintf(k, sizeof k, "Price%d", i); klhr_price[i] = (int)GetPrivateProfileIntA("Hire", k, klhr_defp[i], klh_ini);
        snprintf(k, sizeof k, "Rank%d", i);  klhr_need[i] = (int)GetPrivateProfileIntA("Hire", k, klhr_defr[i], klh_ini);
        if (klhr_price[i] < 0) klhr_price[i] = 0;
    }
    if (klhr_on) {
        klog("hire: on (Rank gate %d, Log %d). The Heister page's Char= is ignored while this is on; the body is a random default (never Kane / Lynch) or what you hired, one round. NOT RUN IN THE GAME", klhr_rankgate, klhr_log);
        if (klhr_bots) klog("hire: [Hire] Bots=1 is not built in this pass (re\\shop_hire.md 6): bots keep their bodies");
    }
}

#endif /* KLHIRE_C */
