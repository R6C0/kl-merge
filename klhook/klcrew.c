/*
 * klcrew.c - RANDOM AI HEISTERS: each Arcade round the AI crew is a new draw from the level's wardrobe - the eight
 * Dog Days mercenaries AND the eight Dead Men heroes (Kane, Lynch, Ashkanan .. Hutchison), each with a random outfit
 * and mask - never the body the player wears or chose. Owner, 2026-10-10: 'can we get the AI to be randomly generated
 * from the outfits from dead men and also dog days so its not always the same models'.
 * Part of KLHook (to be included by klhook.c AFTER klchar.c, SHIP and TEST alike; the three lines are at the end of
 * this comment). Heap data writes (eight bytes of one table), and calls of game functions from the game's own
 * thread: two for the look, two more for the name (key Names, off). No code byte of kl2.exe changes.
 * Spec, the reading it rests on, the live checks: re\crew_random.md. Data side: nothing new - it uses the wardrobe
 * a build already has (tools\kl_chars.py wardrobe, KLWardrobe.ini beside the archive, read by klchar.c) and the AI
 * crew a build already has (tools\kl_fa_bots.py; a stock level has its own).
 * NOTHING HERE HAS RUN IN THE GAME. Off unless [Crew] Random=1. Arcade only (ZGameRulesHeist).
 *
 * 1. WHAT AN AI HEISTER'S LOOK IS (kl2.exe build 0490, read 2026-10-10 with debug\dasm.py; EXE = seen in the code)
 *    - A crew record (rules+0x348 + i * 0x7c, in-use byte [rules+0x34c]+i == 0, count rules+0x354; klbot.c 1) with
 *      mask 1 at +0x79 is an AI member; +4 = its actor (a ZFFActor, vtable 0xbb3bac: REQUIRED here before any call),
 *      [actor+4] = its scene node, [node+0x68] = the MODEL (chunk index of the level's .prm, as for a player),
 *      [actor+0x50] = the VARIANT (which objects of the model are drawn).
 *    - THE GAME CHANGES BOTH ON AN AI MEMBER ITSELF, at run time:
 *        model    ZGameRulesHeist slot 137 (0x8f5e90), after it gave the human his body: for the AI member that wore
 *                 it, 0x8f5f63..0x8f5f97:  0x792290(node, model) ; actor->vtable[0x1dc]() ; [0x541960()]->vtable[0x70]
 *                 (node, 1).  Those are, instruction for instruction, the body of 0x783fb0(this, model) (0x783fb0..
 *                 0x783fe2: this = the entity, node = [this+4]), which the same routine calls for the player at
 *                 0x8f5f03. Vtable slot 0x1dc / 4 = 119 is 0x417a60 in BOTH classes (ZFFActor 0xbb3bac, ZFFPlayer
 *                 0xbb45f4): it rebuilds the bone arrays from the model. So 0x783fb0(actor, model) IS what the game
 *                 does to an AI member, and that is the one call this file makes for the body.
 *        variant  ZGameRulesHeist slot 34 (0x4b5b20; option UseMask), 0x4b5c22..0x4b5c48: for every record with
 *                 mask 1:  [actor+0x50] = 2 ; [0x541960()]->vtable[0x70]([actor+4], 1).  That is the body of
 *                 0x88c810(this, variant) (0x88c810..0x88c82f) with this = the actor. So 0x88c810(actor, variant) IS
 *                 what the game does to an AI member; it is the call klchar.c makes for the player.
 *      Neither routine reads anything of ZFFPlayer: both take [this+4] and, for the model, one virtual call the two
 *      classes share. The hook-side swap is therefore the game's own mechanism for an AI actor, not a new one.
 *    - WHEN the game does it: slot 137 has three callers (0x42df3b, 0x4d10ae, 0x75632b), each `if [session+0x5c] ==
 *      4 and the rules object exists`, each in a routine that has just entered a player in the session (0x7a2540,
 *      0x71e830; two of them are slots of the session handlers' vtables 0xbd1cb8 / 0xbd2560). ASSUMPTION: that is
 *      'the player's object has joined' = once at the start of a level. The hook acts later than that: when rules,
 *      player, the eight table entries and the set of AI records have stood still for Settle ms. That a model may be
 *      set at that later moment is what klchar.c shows for the player (runs W5 / W6); for an ACTOR it is NOT SEEN.
 *    - A wardrobe model fits a bot's animation set: a skeleton is bound to the level's .ANM by bone NAME, not to a
 *      set (tools\kl_chars.py, 'THE SKELETON IS BAKED AGAINST THE LEVEL'S .ANM'), the stock swap already puts the
 *      human's former model (set Kane / Lynch) on an actor of set Kane_NPC / Lynch_NPC, and the Dead Men roots were
 *      rebound when the wardrobe was built. NOT SEEN: a 1080 - 1608-object Dead Men root on seven actors at once
 *      (one on the player: run W5).
 *
 * 2. WHO A BOT IS BESIDES HIS BODY (EXE)
 *    - voice: the byte rules+0x33e + record index picks the recording `K_C<byte + 1>` of every per-character line
 *      (re\bots_voice.md 1.2 / 1.3; the list has ten entries, 0..7 are the eight mercenaries). ZGameRulesHeist slot
 *      198 (0x588980) writes it at registration as `group name[0x12] - '1'` (0x5889d1..0x5889e2: Glazer_Bodyguard_0N
 *      -> N - 1); the index it writes at IS the record index (the same ebx is the in-use byte's and the record's,
 *      0x588a0e..0x588a23). The table has no other reader. Key Voice: a Dog Days body speaks with its own voice
 *      (byte = character - 1); a Dead Men body, and a Dog Days body whose voice the player has, gets the lowest
 *      index nobody has. Eight indices for eight crew members: each used once. Plain data, bytes 0..7 only (an index
 *      above 9 would be the int3 at 0x51ab2d).
 *    - name: 0x588980 goes on: 0x478df0(byte) = the LOCALISED text of /AllLevels/Interface/FACharacters/C<n> (0x47d8c0;
 *      a key that starts with '%' is its own text), 0x83e2e0(&tmp, text) makes a 12-byte string {begin, end, capacity}
 *      of it (0x770520), and 0x469250(block, tmp by value) with block = [record+0] formats it ("%s", 0xb80444) into
 *      the string at block+8 and frees tmp. Slot 137 does the same with character 0 for the bot that takes the human's
 *      old body (0x8f5f99..0x8f5fba). So a bot's name is a string of its own at [[record]+8], set twice by the game.
 *      Key Names (default 0): the hook makes the same two calls with the character's name from KLWardrobe.ini
 *      ('Tommy', 'Kane', 'Ashkanan' ...; English, not localised - the Dead Men names have no text in Dog Days' .LOC).
 *      NOT ESTABLISHED: that the round-start line-up and the score page read THAT string (no reader of block+8 was
 *      looked for). Without the key a bot keeps the name of his place: 'Tommy' may walk around in Kane's suit.
 *    - the heister table rules+0x208 (heroes[8], the models slot 137 hands the player) is NOT written here: it is
 *      klchar.c's. Consequence, handled: when slot 137 runs later (klchar.c's body change, a second player join) and
 *      a bot wears the model the player is given, the game hands that bot the player's old model. The hook sees it
 *      at its next tick: a bot whose drawn body the player now wears is drawn again from the bodies nobody has; a
 *      bot whose model is no longer the drawn one gets it back (at most Tries calls a round).
 *
 * 3. THE DRAW (per round)
 *    A new draw is made for a new rules object and whenever the session state comes back into 0x12..0x19 from the
 *    score side (>= 0x1f; the states seen live are 0x12 0x15 0x16 0x18 0x19 = round runs, 0x1f, 0x20 = score page,
 *    0x23..0x26, 0x16 ...: re\hook_live.md). ASSUMPTION: no state outside 0x12..0x19 occurs inside a round.
 *    Characters = the level's KLWardrobe.ini (16: 1..8 Dog Days, 9..16 Dead Men); without one, the eight models of
 *    the heister table (a stock level: the seven others shuffled over the bots, variants 1 / 2 only).
 *    Never drawn: the character whose model the player wears, and klchar.c's choice [Character] Char (so the body
 *    is free before the player's own swap has happened). First the characters of Include= that are free, then
 *    weighted draws without replacement (DogDays= / DeadMen= per character of that game), then the picks are
 *    shuffled over the bots. Nobody twice: 15 free characters for 7 bots. A bot for whom nothing is left keeps his
 *    body. Per bot: outfit = random 0 .. Bodies * Heads - 1 (24 on a Dead Men body, key Outfits), mask by Masks /
 *    MaskChance: one of the build's masks (8 Dog Days + up to 4 Payday 2 plates, key PaydayMasks) or the own face.
 *    The variant is klchar.c's formula (klc_variant: outfit, mask choice -> the model's variant number).
 *    Our own generator; the game's (sysif+0xb30) is not touched. Seed=0 takes a new seed each start and logs it.
 *
 * 4. WHAT IS WRITTEN AND CALLED (each tick, for every AI record in play = status byte +0x10 == 0)
 *      [node+0x68] != the drawn root            0x783fb0(actor, root)            game thread, at most Tries a round
 *      [actor+0x50] != the drawn variant        0x88c810(actor, variant)         game thread, at most 64 a round
 *                                               (the game's slot 34 sets 2 again when it runs: then once more)
 *      rules+0x33e+i != the voice               one byte, heap                   key Voice
 *      the string at [[record]+8] != the name   0x83e2e0 + 0x469250              game thread, at most twice; key Names
 *    Before any call the first bytes of the routines (and of 0x792290, which 0x783fb0 calls) are compared with the
 *    known ones, and slot 119 of the actor's vtable with 0x417a60; a record whose actor is not a ZFFActor is left
 *    alone and said once. Nothing is done off the game's thread but the voice bytes.
 *    A bot that is aboard (4) or dead (7) is not touched: its actor may be gone.
 *    THE LEVEL GATE (re\crew_talk_review.md 1.3 a; the hook's policy, klhook.c): the draw and every call and write
 *    above happen only while the level that runs is NOT the stock level of its slot - klsteam.c's klx_level_verdict
 *    == 2, as for klbot.c's gameplay parts. Not at the menu (no level), not on a stock level (1), not on a level
 *    whose archive was not seen (3), and not at all when the Steam write guard is not installed (no archive is
 *    judged then). On verdict 1 / 3 one line per scene says so. (Until 2026-10-10 16:50 this comment and
 *    re\crew_random.md said 'not tied to the verdict' while the code was tied: the code stands, the texts follow.)
 *
 * FOR OTHER PARTS OF THE HOOK (kltalk.c: the Kane / Lynch dialogue, the Retomoto countdown) - WHO WEARS WHOM, read
 * from the MODELS at the moment of the call, not from the draw (re\crew_talk_review.md 1.3 b, 3.3 b):
 *      klw_who_now(&who)             every crew record in use: record index, AI or human, status, and the character
 *                                    (1..16 as KLChar) whose root in the level's KLWardrobe.ini equals the model
 *                                    [node+0x68] the member wears now; without a wardrobe the eight heister-table
 *                                    models (1..8). 0 = no body of the list (a policeman after the player's death,
 *                                    an actor of another class, a record without an actor).
 *      klw_crew_char(record index)   the same for one record        klw_player_char()   for the human's record
 *    These three only READ. They work with Random=0, without an AI crew, on any level and off the game's thread;
 *    the level gate above is not theirs. 9 = Kane, 10 = Lynch on the builds of 2026-10-10 (kltalk.c takes the
 *    numbers from KLTalk.ini). Include=9,10 puts both in every crew they are free for.
 *      klw_drawn_char(record index)  what the round's DRAW gave that record (0 = none): the draw's own book-keeping
 *
 * KLHook.ini
 *   [Crew]
 *   Random=0          1 = this file is on
 *   Seed=0            0 = a new one each start (logged); any other number repeats the same sequence of draws
 *   DogDays=1         weight of each Dog Days body, DeadMen=1 of each Dead Men body (0 = none of that game)
 *   Include=          characters that are always in the crew when free, e.g. 9,10 (Kane and Lynch)
 *   Outfits=1         0 = every Dead Men body in plain clothes (outfit 0)
 *   Masks=1           0 = faces only, 1 = each bot masked with MaskChance percent (50), 2 = all masked
 *   PaydayMasks=1     0 = only the eight Dog Days masks
 *   Voice=1           0 = the voice table is left alone (a bot then speaks as the place he stands in)
 *   Names=0           1 = also rename the bots (two more game calls; section 2)
 *   Settle=600        ms everything must have stood still (longer than [Character] Settle: the player goes first)
 *   Tries=3           model calls per bot and round at most
 *   Log=1
 *
 * LOG (the live checks C1..C7 of re\crew_random.md go by these lines)
 *   crew: on; ...                                              at start
 *   crew: level '...' is the STOCK one of its slot (...): the AI crew is left as it is      once per scene (verdict 1 / 3)
 *   crew: round draw N (session state 16, rules ..., 7 AI members, wardrobe of f01\f01_main: 16 characters, 12 masks; the player is Kane)
 *   crew: bot 3 is Lynch, outfit 11, mask 5 (record 3, model 9270, variant 67)
 *   crew: bot 3 (actor ...): model 9709 -> 9270 through the game's own routine (try 1): it now has 9270
 *   crew: bot 3 look: variant 1 -> 67
 *   crew: bot 3 speaks as C4 (voice table entry 3: 2 -> 3)
 *   crew: bot 3 is now called 'Lynch' (was 'Pierre')
 *   crew: bot 3 wore the body the player now has (model ...): drawn again
 *
 * THE LEAD'S THREE LINES IN klhook.c (this file was compiled that way off-game, re\crew_random.md 6):
 *   #include "klcrew.c"          after  #include "klchar.c"
 *   klw_tick(game_thread);       in klh_tick, after  klc_tick(game_thread);
 *   klw_init();                  in DllMain, after  klc_init();
 * and the [Crew] block above in klhook\KLHook.ini, and a row 'klcrew.c  x  x  random AI heisters' in the file table.
 */
#ifndef KLCREW_C
#define KLCREW_C
static int klx_on;
static int klx_level_verdict(const char *scene, char *why);

#define KLW_SESSION    0x0168e598             /* +0x5c = mode (4 = Arcade), +0x70 = state */
#define KLW_SETTINGS   0x0168e9e4             /* +0x54 = the rules object */
#define KLW_RULES_VT   0x00bd3514             /* ZGameRulesHeist */
#define KLW_ACTOR_VT   0x00bb3bac             /* ZFFActor */
#define KLW_REBUILD    0x00417a60             /* slot 119 of ZFFActor and of ZFFPlayer: bone arrays from the model */
#define KLW_SETMODEL   0x00783fb0             /* (entity, model): 0x792290(node, model), slot 119, refresh */
#define KLW_NODEMODEL  0x00792290
#define KLW_SETVARIANT 0x0088c810             /* (entity, variant): [entity+0x50] = variant, refresh */
#define KLW_STRING     0x0083e2e0             /* (string *, text): a 12-byte string of the game's heap */
#define KLW_RENAME     0x00469250             /* (client block, string by value): the name at block+8; frees the string */
#define KLW_NREC       32
#define KLW_LOOKCALLS  64

struct klw_chr { DWORD root; int bodies, heads, dm; char name[32]; };
struct klw_src { int wardrobe, version, step, masks, headbase, n; char key[64]; struct klw_chr c[KLC_NCHAR]; };
struct klw_bot { int used; DWORD actor; int ch, outfit, mask, tries, looks, named, voice; LONG lastv; DWORD lastm; };
struct klw_seen { int rec; DWORD at, actor, node, model, variant; BYTE status; };

static struct { int random, log, wdd, wdm, masks, mask_chance, payday, outfits, voice, names, settle, tries; DWORD seed; int include[KLC_NCHAR], ninclude; } klw;
static struct { DWORD rules, sig, since, rng; int left, fresh, draws, player_ch; struct klw_bot b[KLW_NREC]; } klw_r;

static DWORD klw_rnd(DWORD n)
{   /* 0 .. n-1; xorshift32, our own (the game's generator is not touched) */
    DWORD x = klw_r.rng ? klw_r.rng : 0x2545f491u;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    klw_r.rng = x;
    return n ? (x >> 8) % n : 0;
}

/* what the round's draw gave a record (0 = nothing: not drawn, kept his body, aboard or dead at the draw) */
static int klw_drawn_char(int rec) { return rec >= 0 && rec < KLW_NREC && klw_r.b[rec].used ? klw_r.b[rec].ch : 0; }

/* The characters this level can show: its KLWardrobe.ini (klchar.c's copy), else the eight models of the heister table. */
static void klw_source(struct klw_src *s, const DWORD hero[8], const char *key)
{
    static const char *const stock[8] = { "J.C.", "Tommy", "Pierre", "Liam", "Jean", "Elwood", "Bud", "Mitchel" };
    int i;
    memset(s, 0, sizeof *s);
    snprintf(s->key, sizeof s->key, "%s", key);
    EnterCriticalSection(&klc_cs);
    if (klc_w.on && !_stricmp(key, klc_w.key)) {
        s->wardrobe = 1; s->version = klc_w.version; s->step = klc_w.step; s->masks = klc_w.masks; s->headbase = klc_w.headbase; s->n = klc_w.n;
        for (i = 0; i < klc_w.n; i++) {
            s->c[i].root = klc_w.c[i].root; s->c[i].bodies = klc_w.c[i].bodies; s->c[i].heads = klc_w.c[i].heads; s->c[i].dm = !klc_w.c[i].stock;
            snprintf(s->c[i].name, sizeof s->c[i].name, "%s", klc_w.c[i].name);
        }
    }
    LeaveCriticalSection(&klc_cs);
    if (s->wardrobe) return;
    s->n = 8; s->step = 10; s->masks = 1;
    for (i = 0; i < 8; i++) { s->c[i].root = hero[i]; s->c[i].bodies = s->c[i].heads = 1; strcpy(s->c[i].name, stock[i]); }
}

static int klw_char_of(const struct klw_src *s, DWORD model)
{
    int i;
    for (i = 0; i < s->n; i++) if (s->c[i].root == model) return i + 1;
    return 0;
}

/* ---------------------------------------------------------------- who wears whom, from the models (read only)

   Valid with Random=0, without an AI crew, on a stock level and off the game's thread: nothing here depends on the
   draw or on the level gate. ch = the character whose root is the model the member wears NOW (0 = none of the list). */
struct klw_who {
    DWORD rules, state; int n, human, wardrobe, nchar; char key[64];
    struct { int rec, ai, ch; BYTE status; DWORD at, actor, model; } m[KLW_NREC];      /* at = the crew record */
};

static int klw_who_now(struct klw_who *w)
{
    struct klw_src src; DWORD sm, gs, gd, recs, inuse, hero[8], player = 0, pnode = 0; BYTE sel = 0xff, type = 0; int cap, i; char scene[160], key[64];
    memset(w, 0, sizeof *w); w->human = -1;
    if (!klh_exe_ok || !(sm = klh_rd32((DWORD_PTR)KLH_VA(KLW_SESSION))) || klh_rd32(sm + 0x5c) != 4) return 0;        /* Arcade only */
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLW_SETTINGS))) || !(w->rules = klh_rd32(gs + 0x54)) || klh_rd32(w->rules) != KLW_RULES_VT) return 0;
    if (!klh_rd(sm + 0x70, &w->state, 4) || !klh_rd(w->rules + 0x208, hero, sizeof hero)) return 0;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return 0;
    cap = (int)klh_rd32(w->rules + 0x354); recs = klh_rd32(w->rules + 0x348); inuse = klh_rd32(w->rules + 0x34c);
    if (cap < 1 || !recs || !inuse) return 0;
    if (cap > KLW_NREC) cap = KLW_NREC;
    klw_source(&src, hero, key);
    w->wardrobe = src.wardrobe; w->nchar = src.n; snprintf(w->key, sizeof w->key, "%s", key);
    if ((gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) != 0 && klh_rd(gd + 0x898, &sel, 1) && sel <= 3 && (player = klh_rd32(gd + 0x828 + 4 * sel)) != 0) {
        pnode = klh_rd32(player + 4);
        if (!klh_rd(player + 0x273c, &type, 1)) type = 0;
    }
    for (i = 0; i < cap; i++) {
        DWORD at = recs + (DWORD)i * 0x7c, node; BYTE u = 1, fl = 0, st = 0xff; int k = w->n, c;
        if (!klh_rd(inuse + i, &u, 1) || u || !klh_rd(at + 0x79, &fl, 1) || !klh_rd(at + 0x10, &st, 1)) continue;
        w->m[k].rec = i; w->m[k].at = at; w->m[k].ai = fl & 1; w->m[k].status = st;
        if (fl & 1) {                                                            /* an AI member: a ZFFActor, or nobody we know */
            w->m[k].actor = klh_rd32(at + 4);
            if (w->m[k].actor && klh_rd32(w->m[k].actor) == KLW_ACTOR_VT && (node = klh_rd32(w->m[k].actor + 4)) != 0) klh_rd(node + 0x68, &w->m[k].model, 4);
        } else {                                                                 /* the human (klbot.c: the first record without mask 1; index 0 in Arcade) */
            if (w->human < 0) w->human = k;
            if (w->human == k && type == 2 && pnode) { w->m[k].actor = player; klh_rd(pnode + 0x68, &w->m[k].model, 4); }      /* type 3 = he plays a policeman now: no body of the list */
        }
        if (w->m[k].model) for (c = 0; c < src.n; c++) if (src.c[c].root == w->m[k].model) { w->m[k].ch = c + 1; break; }
        w->n++;
    }
    return 1;
}

static int klw_crew_char(int rec)
{
    struct klw_who w; int i;
    if (!klw_who_now(&w)) return 0;
    for (i = 0; i < w.n; i++) if (w.m[i].rec == rec) return w.m[i].ch;
    return 0;
}

static int klw_player_char(void)
{
    struct klw_who w;
    return klw_who_now(&w) && w.human >= 0 ? w.m[w.human].ch : 0;
}

/* one character nobody has: weighted, 0 = none left */
static int klw_pick(const struct klw_src *s, const char *taken)
{
    DWORD total = 0, r; int c;
    for (c = 1; c <= s->n; c++) if (!taken[c]) total += (DWORD)(s->c[c - 1].dm ? klw.wdm : klw.wdd);
    if (!total) return 0;
    r = klw_rnd(total);
    for (c = 1; c <= s->n; c++) if (!taken[c]) {
        DWORD w = (DWORD)(s->c[c - 1].dm ? klw.wdm : klw.wdd);
        if (r < w) return c;
        r -= w;
    }
    return 0;
}

/* outfit and mask of a bot that has just been given character b->ch; mask is klchar.c's choice number: 1 = own face,
   1 + m = mask m (without a wardrobe: 2 = the body's own mask, the only one a stock level has) */
static void klw_dress(const struct klw_src *s, struct klw_bot *b)
{
    const struct klw_chr *c = &s->c[b->ch - 1];
    int looks = c->bodies * c->heads, nm = s->wardrobe ? s->masks : 1, masked;
    if (!klw.payday && nm > 8) nm = 8;
    b->outfit = klw.outfits && looks > 1 ? (int)klw_rnd((DWORD)looks) : 0;
    masked = klw.masks == 2 || (klw.masks == 1 && (int)klw_rnd(100) < klw.mask_chance);
    b->mask = masked && nm > 0 ? 2 + (int)klw_rnd((DWORD)nm) : 1;
    b->tries = b->looks = b->named = 0; b->voice = -1; b->lastv = -1; b->lastm = 0;
}

static int klw_variant_of(const struct klw_src *s, const struct klw_bot *b, DWORD cur)
{
    const struct klw_chr *c = &s->c[b->ch - 1];
    if (!s->wardrobe) return b->mask > 1 ? 2 : 1;
    return klc_variant(s->version, s->step, s->headbase, c->bodies, c->heads, b->outfit, b->mask, cur);
}

static void klw_say(const struct klw_src *s, const struct klw_bot *b, int rec, const char *what)
{
    const struct klw_chr *c = &s->c[b->ch - 1];
    klog("crew: bot %d is %s, outfit %d, mask %d (record %d, model %lu, variant %d)%s", rec, c->name, b->outfit, b->mask - 1, rec, c->root, klw_variant_of(s, b, 1), what);
}

/* the round's draw for the AI records seen[0..n) */
/* extra_taken: NULL (Arcade) or one byte per character 1..KLC_NCHAR that is not to be drawn either (klcrewlook.c: every human's body online) */
static void klw_draw(const struct klw_src *s, const struct klw_seen *seen, int n, int player_ch, DWORD state, DWORD rules, const char *extra_taken)
{
    char taken[KLC_NCHAR + 1]; int pick[KLW_NREC], np = 0, i, j, k, m = n, choice = klc_on ? (int)klc_char : 0;
    memset(taken, 0, sizeof taken); memset(klw_r.b, 0, sizeof klw_r.b);
    for (i = 0, n = 0; i < m; i++) n += !seen[i].status;                  /* a member aboard or dead is not in the draw */
    klw_r.draws++;
    klw_r.rng = klw.seed ^ ((DWORD)klw_r.draws * 0x9e3779b9u);
    for (i = 0; i < 4; i++) klw_rnd(1);
    if (player_ch) taken[player_ch] = 1;
    if (choice >= 1 && choice <= s->n) taken[choice] = 1;                 /* the body the player CHOSE, worn already or not */
    if (extra_taken) for (i = 1; i <= s->n && i <= KLC_NCHAR; i++) if (extra_taken[i]) taken[i] = 1;
    for (i = 0; i < klw.ninclude && np < n; i++) {
        int c = klw.include[i];
        if (c >= 1 && c <= s->n && !taken[c]) { pick[np++] = c; taken[c] = 1; }
    }
    while (np < n) { int c = klw_pick(s, taken); if (!c) break; pick[np++] = c; taken[c] = 1; }
    while (np < n) pick[np++] = 0;                                        /* nothing left: this bot keeps his body */
    for (i = n - 1; i > 0; i--) { j = (int)klw_rnd((DWORD)i + 1); np = pick[i]; pick[i] = pick[j]; pick[j] = np; }
    if (klw.log)
        klog("crew: round draw %d (session state %lx, rules %08lx, %d AI members, %s of %s: %d characters, %d masks; the player is %s)", klw_r.draws, state, rules, n,
             s->wardrobe ? "wardrobe" : "NO wardrobe, the stock bodies", s->key, s->n, s->wardrobe ? s->masks : 1, player_ch ? s->c[player_ch - 1].name : "in no body of the list");
    for (i = 0, k = 0; i < m; i++) {
        struct klw_bot *b = &klw_r.b[seen[i].rec];
        b->used = 1; b->actor = seen[i].actor; b->ch = seen[i].status ? 0 : pick[k++]; b->voice = -1; b->lastv = -1;
        if (seen[i].status) continue;
        if (!b->ch) { if (klw.log) klog("crew: bot %d keeps his body (model %lu): no character is left for him", seen[i].rec, seen[i].model); continue; }
        klw_dress(s, b);
        if (klw.log) klw_say(s, b, seen[i].rec, "");
    }
}

/* The voice of every AI record, from the table as it stands: tab[0] is the player's and stays. -> want[rec], -1 = leave */
static void klw_voices(const struct klw_src *s, const struct klw_seen *seen, int n, const BYTE tab[8], int want[KLW_NREC])
{
    char used[8]; int i, v;
    memset(used, 0, sizeof used);
    for (i = 0; i < KLW_NREC; i++) want[i] = -1;
    if (tab[0] < 8) used[tab[0]] = 1;
    for (i = 0; i < n; i++) {                                             /* a bot that kept his body keeps his voice */
        const struct klw_bot *b = &klw_r.b[seen[i].rec];
        if (seen[i].rec < 1 || seen[i].rec > 7 || b->ch) continue;
        if (tab[seen[i].rec] < 8) used[tab[seen[i].rec]] = 1;
    }
    for (i = 0; i < n; i++) {                                             /* a Dog Days body: its own voice, if nobody has it */
        const struct klw_bot *b = &klw_r.b[seen[i].rec];
        if (seen[i].rec < 1 || seen[i].rec > 7 || !b->ch || b->ch > 8 || s->c[b->ch - 1].dm || used[b->ch - 1]) continue;
        want[seen[i].rec] = b->ch - 1; used[b->ch - 1] = 1;
    }
    for (i = 0; i < n; i++) {                                             /* everybody else: the lowest voice nobody has */
        const struct klw_bot *b = &klw_r.b[seen[i].rec];
        if (seen[i].rec < 1 || seen[i].rec > 7 || !b->ch || want[seen[i].rec] >= 0) continue;
        for (v = 0; v < 8 && used[v]; v++) ;
        if (v < 8) { want[seen[i].rec] = v; used[v] = 1; }
    }
}

/* The game's own two steps of 0x588980 / 0x8f5f99: a string of its heap from the text, handed (and given up) to the
   record's client block. Game thread only. */
static void klw_rename(struct klw_bot *b, const struct klw_seen *sn, const char *want)
{
    DWORD blk = klh_rd32(sn->at), s[3] = { 0, 0, 0 }; char cur[48]; DWORD len;
    struct { char *b, *e, *c; } t = { 0, 0, 0 };
    if (!blk || !klh_rd(blk + 8, s, sizeof s)) return;
    len = s[1] - s[0]; cur[0] = '?'; cur[1] = 0;
    if (s[0] && s[1] >= s[0] && len < sizeof cur - 1 && klh_rd(s[0], cur, len)) cur[len] = 0;
    if (!strcmp(cur, want) || b->named >= 2) return;
    b->named++;
    ((void *(__fastcall *)(void *, void *, const char *))(DWORD_PTR)KLH_VA(KLW_STRING))(&t, 0, want);
    if (!t.b) { klog("crew: bot %d: the game made no string for the name '%s': not renamed", sn->rec, want); return; }
    ((void (__fastcall *)(void *, void *, char *, char *, char *))(DWORD_PTR)KLH_VA(KLW_RENAME))((void *)(DWORD_PTR)blk, 0, t.b, t.e, t.c);
    if (klw.log) klog("crew: bot %d is now called '%s' (was '%s')", sn->rec, want, cur);
}

/* The game routines this file calls are the ones it knows (first bytes), and slot 119 of ZFFActor's vtable is 0x417a60. Said once. */
static int klw_code_ok(void)
{
    static const BYTE model_code[14] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x57, 0x8b, 0x7e, 0x04, 0x50, 0x8b, 0xcf };          /* 0x783fb0 .. push eax ; mov ecx, edi */
    static const BYTE node_code[12] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x57, 0x8b, 0x7e, 0x68, 0x89 };                      /* 0x792290 .. mov edi,[esi+0x68] ; mov [esi+0x68],eax */
    static const BYTE variant_code[10] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x89, 0x46, 0x50 };                               /* 0x88c810 .. mov [esi+0x50],eax */
    static int toldcode;
    if (!klc_same_code(KLW_SETMODEL, model_code, sizeof model_code) || !klc_same_code(KLW_NODEMODEL, node_code, sizeof node_code) ||
        !klc_same_code(KLW_SETVARIANT, variant_code, sizeof variant_code) || klh_rd32((DWORD_PTR)KLH_VA(KLW_ACTOR_VT + 4 * 119)) != KLW_REBUILD) {
        if (!toldcode++) klog("crew: the game routines are not the ones this build knows: nothing is changed");
        return 0;
    }
    return 1;
}

/* Hold the draw: for every bot of seen[0..n) with a character in klw_r.b[rec] (not aboard / dead) bring the model and the variant to the drawn ones.
   Game thread only for the calls. allow_redraw=0 (klcrewlook.c, online): a bot whose body a human now wears is left alone instead of drawn again here. */
static void klw_hold(const struct klw_src *src, struct klw_seen *seen, int n, DWORD pmodel, int game_thread, int names_ok, int allow_redraw)
{
    static int toldthread;
    int i, j, redraw;
    for (i = 0; i < n; i++) {
        struct klw_seen *q = &seen[i]; struct klw_bot *bt = &klw_r.b[q->rec]; DWORD root, cur = 0; int v;
        if (!bt->ch || q->status) continue;                                                  /* kept his body / aboard, dead: not touched */
        root = src->c[bt->ch - 1].root;
        redraw = root == pmodel;
        if (redraw && !allow_redraw) continue;
        if (redraw) {                                                                        /* the player has taken this body since the draw */
            char taken[KLC_NCHAR + 1]; int c, choice = klc_on ? (int)klc_char : 0;
            memset(taken, 0, sizeof taken);
            if (klw_r.player_ch) taken[klw_r.player_ch] = 1;
            if (choice >= 1 && choice <= src->n) taken[choice] = 1;
            for (j = 0; j < KLW_NREC; j++) if (klw_r.b[j].used && klw_r.b[j].ch) taken[klw_r.b[j].ch] = 1;
            c = klw_pick(src, taken);
            if (klw.log) klog("crew: bot %d wore the body the player now has (model %lu): drawn again", q->rec, root);
            bt->ch = c;
            if (!c) { if (klw.log) klog("crew: bot %d keeps model %lu: no character is left for him", q->rec, q->model); continue; }
            klw_dress(src, bt);
            if (klw.log) klw_say(src, bt, q->rec, "");
            root = src->c[bt->ch - 1].root;
        }
        if (q->model != root) {
            if (!game_thread) { if (!toldthread++) klog("crew: the tick is not on the game's thread ([KLHook] Tick=0?): the bodies cannot be changed"); continue; }
            if (bt->tries >= klw.tries) continue;
            bt->tries++;
            ((void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLW_SETMODEL))((void *)(DWORD_PTR)q->actor, 0, root);
            klh_rd(q->node + 0x68, &cur, 4);
            klog("crew: bot %d (actor %08lx): model %lu -> %lu through the game's own routine (try %d): it now has %lu%s", q->rec, q->actor, q->model, root, bt->tries, cur, cur == root ? "" : " - NOT taken");
            if (cur != root) continue;
            q->model = cur; klh_rd(q->actor + 0x50, &q->variant, 4);
        } else if (bt->lastm != root) { bt->lastm = root; if (klw.log > 1) klog("crew: bot %d wears model %lu", q->rec, root); }
        v = klw_variant_of(src, bt, q->variant);
        if (q->variant != (DWORD)v && game_thread && bt->looks < KLW_LOOKCALLS) {
            bt->looks++;
            ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLW_SETVARIANT))((void *)(DWORD_PTR)q->actor, 0, v);
            if ((InterlockedExchange(&bt->lastv, v) != v || bt->looks == KLW_LOOKCALLS) && klw.log)
                klog("crew: bot %d look: variant %lu -> %d%s", q->rec, q->variant, v, bt->looks == KLW_LOOKCALLS ? " - the game has set it back 64 times: left alone for this round" : "");
        }
        if (names_ok && game_thread) klw_rename(bt, q, src->c[bt->ch - 1].name);
    }
}

static void klw_level_tick(int game_thread)
{
    static const BYTE string_code[15] = { 0x56, 0x8b, 0xf1, 0x8b, 0x4c, 0x24, 0x08, 0x8d, 0x44, 0x24, 0x08, 0x50, 0x51, 0x8b, 0xce };    /* 0x83e2e0 */
    static const BYTE rename_code[12] = { 0x6a, 0xff, 0x68, 0x98, 0xbe, 0xad, 0x00, 0x64, 0xa1, 0x00, 0x00, 0x00 };                    /* 0x469250 */
    static int toldmode, toldactor, toldnames; static char toldscene[160];
    struct klw_seen seen[KLW_NREC]; struct klw_src src; int want[KLW_NREC];
    DWORD sm, gs, rules, state, gd, player, pnode, pmodel = 0, hero[8], recs, inuse, sig, now = GetTickCount(); BYTE b = 0xff, type = 0, tab[8];
    int n = 0, cap, i, names_ok;
    char key[64], scene[160], why[200];

    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLW_SESSION))) || klh_rd32(sm + 0x5c) != 4) return;                      /* Arcade only */
    /* THE LEVEL GATE (top comment, section 4): only a level whose archive was seen and is not the stock one */
    if (!klx_on || !klh_scene(scene, sizeof scene)) return;
    if ((i = klx_level_verdict(scene, why)) != 2) {
        static int toldverdict;
        if (i && (strcmp(scene, toldscene) || i != toldverdict)) {               /* 1 stock, 3 not seen: said once per scene and verdict; 0 = the menu, silent */
            snprintf(toldscene, sizeof toldscene, "%s", scene); toldverdict = i;
            if (klw.log) klog("crew: level '%s' %s (%.150s): the AI crew is left as it is", scene, i == 1 ? "is the STOCK one of its slot" : "is not known", why);
        }
        return;
    }
    toldscene[0] = 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLW_SETTINGS))) || !(rules = klh_rd32(gs + 0x54))) return;
    if (klh_rd32(rules) != KLW_RULES_VT) {
        if (!toldmode++) klog("crew: the rules object %08lx has vtable %08lx, not ZGameRulesHeist: nothing is changed", rules, klh_rd32(rules));
        return;
    }
    state = klh_rd32(sm + 0x70);
    if (rules != klw_r.rules) { klw_r.rules = rules; klw_r.fresh = 1; klw_r.left = 0; klw_r.sig = 0; klw_r.player_ch = 0; memset(klw_r.b, 0, sizeof klw_r.b); }
    if (state < 0x12 || state > 0x19) { if (state >= 0x1f) klw_r.left = 1; return; }         /* not between the load and the end of a round */
    if (klw_r.left) { klw_r.left = 0; klw_r.fresh = 1; }                                     /* back from the score page: the next round */

    /* ---- the player (as klchar.c finds him) and the heister table */
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &b, 1) || b > 3) return;
    if (!(player = klh_rd32(gd + 0x828 + 4 * b)) || !(pnode = klh_rd32(player + 4))) return;
    if (!klh_rd(player + 0x273c, &type, 1) || type != 2 || !klh_rd(pnode + 0x68, &pmodel, 4) || !pmodel) return;   /* a heister (a policeman after his death: leave the crew as it is) */
    if (!klh_rd(rules + 0x208, hero, sizeof hero)) return;
    for (i = 0; i < 8; i++) if (!hero[i]) return;

    /* ---- the AI records */
    cap = (int)klh_rd32(rules + 0x354); recs = klh_rd32(rules + 0x348); inuse = klh_rd32(rules + 0x34c);
    if (cap < 1 || !recs || !inuse) return;
    if (cap > KLW_NREC) cap = KLW_NREC;
    for (i = 0; i < cap; i++) {
        struct klw_seen *q = &seen[n]; BYTE u = 1, fl = 0;
        q->rec = i; q->at = recs + (DWORD)i * 0x7c;
        if (!klh_rd(inuse + i, &u, 1) || u || !klh_rd(q->at + 0x79, &fl, 1) || !(fl & 1)) continue;
        if (!(q->actor = klh_rd32(q->at + 4))) continue;
        if (klh_rd32(q->actor) != KLW_ACTOR_VT) {
            if (!toldactor++) klog("crew: record %d: the actor %08lx has vtable %08lx, not ZFFActor: that member is left alone", i, q->actor, klh_rd32(q->actor));
            continue;
        }
        if (!(q->node = klh_rd32(q->actor + 4)) || !klh_rd(q->node + 0x68, &q->model, 4) || !q->model) continue;
        if (!klh_rd(q->actor + 0x50, &q->variant, 4) || !klh_rd(q->at + 0x10, &q->status, 1)) continue;
        n++;
    }
    if (!n) return;

    /* ---- everything must have stood still: the player's own swap (the game's, then klchar.c's) goes first */
    for (sig = rules ^ player ^ (pmodel * 2654435761u), i = 0; i < 8; i++) sig = sig * 31 + hero[i];
    for (i = 0; i < n; i++) sig = sig * 31 + (seen[i].actor ^ (DWORD)seen[i].rec);
    if (sig != klw_r.sig) { klw_r.sig = sig; klw_r.since = now; return; }
    if ((LONG)(now - klw_r.since) < klw.settle) return;

    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    klw_source(&src, hero, key);
    klw_r.player_ch = klw_char_of(&src, pmodel);
    for (i = 0; i < n && !klw_r.fresh; i++)                                                  /* a member the draw does not know: draw again */
        if (!klw_r.b[seen[i].rec].used || klw_r.b[seen[i].rec].actor != seen[i].actor) klw_r.fresh = 1;
    if (klw_r.fresh) { klw_r.fresh = 0; klw_draw(&src, seen, n, klw_r.player_ch, state, rules, NULL); }

    if (!klw_code_ok()) return;
    names_ok = klw.names && klc_same_code(KLW_STRING, string_code, sizeof string_code) && klc_same_code(KLW_RENAME, rename_code, sizeof rename_code);
    if (klw.names && !names_ok && !toldnames++) klog("crew: the two name routines are not the ones this build knows: the bots keep their names");

    /* ---- hold the draw */
    klw_hold(&src, seen, n, pmodel, game_thread, names_ok, 1);
    if (klw.voice && klh_rd(rules + 0x33e, tab, sizeof tab)) {
        klw_voices(&src, seen, n, tab, want);
        for (i = 0; i < n; i++) {
            int r = seen[i].rec; BYTE w;
            if (seen[i].status || want[r] < 0 || tab[r] == (BYTE)want[r]) continue;
            w = (BYTE)want[r];
            if (klh_data((void *)(DWORD_PTR)(rules + 0x33e + r), &w, 1, "Arcade heister voice table") && klw_r.b[r].voice != want[r]) {
                klw_r.b[r].voice = want[r];
                if (klw.log) klog("crew: bot %d speaks as C%d (voice table entry %d: %u -> %u)", r, want[r] + 1, r, tab[r], w);
            }
        }
    }
}

static void klw_tick(int game_thread)
{
    if (!klw.random || !klh_exe_ok) return;
    klw_level_tick(game_thread);
}

static int klw_int(const char *key, int def, int lo, int hi)
{
    int v = (int)GetPrivateProfileIntA("Crew", key, def, klh_ini);
    return v < lo ? lo : v > hi ? hi : v;
}

static void klw_init(void)
{
    char inc[128], said[128], *p; LARGE_INTEGER t; int n = 0, i;
    memset(&klw, 0, sizeof klw); memset(&klw_r, 0, sizeof klw_r);
    klw.random = klw_int("Random", 0, 0, 1);
    klw.log = klw_int("Log", 1, 0, 2);
    klw.wdd = klw_int("DogDays", 1, 0, 100); klw.wdm = klw_int("DeadMen", 1, 0, 100);
    klw.outfits = klw_int("Outfits", 1, 0, 1);
    klw.masks = klw_int("Masks", 1, 0, 2); klw.mask_chance = klw_int("MaskChance", 50, 0, 100); klw.payday = klw_int("PaydayMasks", 1, 0, 1);
    klw.voice = klw_int("Voice", 1, 0, 1); klw.names = klw_int("Names", 0, 0, 1);
    klw.settle = klw_int("Settle", 600, 0, 60000); klw.tries = klw_int("Tries", 3, 1, 20);
    klw.seed = GetPrivateProfileIntA("Crew", "Seed", 0, klh_ini);
    GetPrivateProfileStringA("Crew", "Include", "", inc, sizeof inc, klh_ini);
    for (p = inc; *p && klw.ninclude < KLC_NCHAR; ) {
        char *e; long c = strtol(p, &e, 10);
        if (e == p) { p++; continue; }
        for (i = 0; i < klw.ninclude && klw.include[i] != (int)c; i++) ;
        if (c >= 1 && c <= KLC_NCHAR && i == klw.ninclude) klw.include[klw.ninclude++] = (int)c;
        p = e;
    }
    if (!klw.random) return;
    if (!klw.seed) { QueryPerformanceCounter(&t); klw.seed = GetTickCount() ^ (DWORD)t.LowPart ^ (GetCurrentProcessId() << 16); if (!klw.seed) klw.seed = 1; n = 1; }
    for (said[0] = 0, i = 0; i < klw.ninclude; i++) snprintf(said + strlen(said), sizeof said - strlen(said), "%s%d", i ? "," : "", klw.include[i]);
    klog("crew: on; random AI heisters: Seed=%lu%s, weights DogDays=%d DeadMen=%d, Include=%s, Outfits=%d, Masks=%d (MaskChance=%d, PaydayMasks=%d), Voice=%d, Names=%d, Settle=%d, Tries=%d",
         klw.seed, n ? " (taken new: Seed=0 in the ini)" : "", klw.wdd, klw.wdm, said[0] ? said : "none", klw.outfits, klw.masks, klw.mask_chance, klw.payday, klw.voice, klw.names, klw.settle, klw.tries);
    if (!klc_on) klog("crew: [Character] Enable=0, so no KLWardrobe.ini is read: the bots are shuffled over the level's own eight bodies only");
}

#endif /* KLCREW_C */
