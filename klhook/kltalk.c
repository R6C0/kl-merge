/*
 * kltalk.c - KANE AND LYNCH TALK: in an Arcade round on a level that has a KLTalk.ini beside its archive, the hook
 * says the level's scripted scenes (Retomoto: Kane's six-clip countdown that ends on the blast, the Kane / Lynch
 * exchanges at their triggers) and idle / combat chatter, through the game's own speech call. Owner, 2026-10-10:
 * 'if theres a kane with people on retomoto can we do an easter egg from the actual mission where he starts the
 * countdown ... and if lynch is also in ther same match could we get a little dialogue exchange'.
 * Part of KLHook (included by klhook.c AFTER klcrew.c and kljoin.c, SHIP and TEST alike). NO data write of game
 * memory and no code byte: TWO game functions are called, from the game's own thread only. Spec: re\talk.md 3, with
 * the three changes of re\crew_talk_review.md 3.3. Data side: tools\kl_fa_talk.py (the lines in the level's bank and
 * .LOC, KLTalk.ini).
 * NOTHING HERE HAS RUN IN THE GAME. Off unless KLHook.ini has [Talk] Enable=1. Arcade only (ZGameRulesHeist), only
 * on a level that is NOT the stock one of its slot (klsteam.c's verdict 2), only while the round runs (state 0x19).
 *
 * 1. THE GAME'S MECHANISM (kl2.exe build 0490; every address read again for this file with debug\dasm.py, 2026-10-10)
 *    - The one level object that says a line on a trigger is OnlineSpeakPlayer. Its init 0x8cb6e0, per key:
 *          entry = 0x89e850(0x204) ; [entry] = 0 ; 0x828fa0(this = [[[0xdd2640]+0xac]+0x94], key, entry)
 *      0x828fa0 = __thiscall (key, entry), ret 8. It finds the key in the .LOC tree (0x594210, which walks the
 *      global block 0xe100b8 and does not use `this`), then 0x860b30(entry, key) copies the key text into the entry
 *      (+4 and +0x104, two 0x100 buffers) and [entry] = what was found; it answers the entry, or 0 (not found; the
 *      game then frees the entry itself, 0x6ad680 at 0x8cb756). So an ENTRY is { found *, key text } - 0x204 bytes
 *      that nothing but the caller owns. The game keeps it for the object's life and says it many times.
 *    - Its fire 0x780550: a NEW 0x28-byte line object per say (0x89e850 + constructor 0x667610: [0] = 0, +4 =
 *      0xbc998c, +8 = 0, +0xc = 3, +0x10 = 1, +0x14 = malloc(12), +0x1c = 0.0, +0x20 flag 0, +0x24 priority -1),
 *      [line] = the kept entry, then 0x421c70(this = [0x168e958], line, 0, 0, 0) at 0x7805f4. The line object is never
 *      freed by 0x780550 (it also leaks a fresh 0x204 block per say: 0x780585..0x7805a6).
 *    - 0x421c70 = __thiscall (line, other line, speaker, last), ret 0x10. EXE, the whole Arcade path:
 *          [manager+0x956] != 0, or byte [[0x168e598]+0x15d] == 0            -> return, nothing said
 *          Arcade (0x7f6850) -> rules = 0x508ef0([0x168e9e4])
 *          flag [line+0x20] == 0 (a plain line), [line] != 0:
 *              if [line+0x1c] == 0.0: [line+0x1c] = rules->vtable[0xac]()   (a time stamp)
 *              0x578840(this = [manager+0x974], ENTRY = [line], priority [line+0x24], speaker, 0xb3ef8c float, last)
 *          other line == 0 -> done
 *      WHO OWNS THE LINE OBJECT (re\crew_talk_review.md 3.3 a asked): on this path the line POINTER is not kept by
 *      anything - 0x421c70 reads [line], [line+0x1c], [line+0x20], [line+0x24], writes [line+0x1c], and hands the
 *      ENTRY on. So the game simply leaks its line object. What IS kept is the entry: 0x578840 either plays it at
 *      once (0x7d0e80) or stores { priority, entry, speaker, float, last } in the speech queue (count at [queue],
 *      ten records of 20 bytes from queue+4, ordered by priority, -1 = first; a full queue drops the line).
 *      The manager has no vtable (made at 0x90abe2 by 0x653e00, destroyed by the plain 0x404110 at 0x6c97a0).
 *    - re\talk.md 2.1: a plain line plays its one recording whatever the speaker byte is.
 *
 * 2. WHAT THE HOOK DOES WITH IT
 *    - ENTRY: one per key and level generation (a new rules object or scene name = a new generation), from the
 *      process heap (HeapAlloc, zeroed), filled by ONE call of 0x828fa0, kept and NEVER freed and never handed to
 *      the game's allocator - the queue may still hold its address. The found pointer goes into the .LOC of the
 *      level that was loaded then, which is why an entry is not carried over to the next generation (a new one is
 *      made; 0x204 bytes per said key and level stay allocated: some 20 KB a level). A key the game does not find
 *      is remembered as 'none' and said in the log once.
 *    - LINE: a NEW 0x34-byte block of the process heap PER SAY (0x28 as the constructor leaves it + the 12 bytes
 *      its +0x14 points at), never freed, never used twice: what the game does (a new object per say, leaked), and
 *      safe whether or not anything keeps the pointer. No call of 0x89e850 / 0x667610 is needed for it.
 *    - SAY: 0x421c70(manager, line, 0, speaker = crew record index of who says it, 0).
 *    Before either call, every time: the tick is on the game's thread; the first 16 / 15 bytes of 0x828fa0 /
 *    0x421c70 are the known ones; Arcade session, rules vtable 0xbd3514; manager, [manager+0x974] and the lookup's
 *    `this` chain are readable and non-null, the queue's count is 0..10; and the two bytes of the game's own test
 *    say 'speech is on' (else the call would do nothing: the line is logged as NOT said).
 *    NOT ESTABLISHED (only a run with ears can say; re\talk.md 9): that a line said this way is heard; whether a
 *    queued line waits for the one that plays; where it sounds from; what the speaker byte does for a plain line.
 *
 * 3. WHO IS KANE (re\crew_talk_review.md 3.3 b)
 *    From the MODELS, at the moment a scene is due and again for every line: klcrew.c's klw_who_now() compares the
 *    model [node+0x68] of the player and of every AI crew record with the roots of the level's KLWardrobe.ini.
 *    Kane= / Lynch= of KLTalk.ini are the character numbers (9 and 10). 'There' = a record in use whose member
 *    wears that body and whose status is in play (0) or aboard (4); the human first when two wear it. Valid with
 *    [Crew] Random=0 and without bots; a player who died and plays a policeman wears no body of the list. So the
 *    countdown cannot be said when nobody wears Kane. Needs [Character] Enable=1 (klchar.c reads KLWardrobe.ini).
 *
 * 4. THE SCRIPT (KLTalk.ini beside the level archive, the folder klchar.c found KLWardrobe.ini in)
 *    [Talk] Version=1 (anything else: refused), Kane=, Lynch=, StreamBytes= (the least size of the game's PC_Def.str;
 *    a smaller file = the level's streamed lines point behind its end: refused, silent), Scenes=, Blast=.
 *    [Scene.n] Name, When, Delay, Needs, Box, NotBefore, Lines, Line.k = who,at,seconds,key.
 *      When   Start   the round-start moment + Delay. THE MOMENT IS AN ASSUMPTION (re\talk.md 3.3): the first tick
 *                     with session state 0x19; [Talk] StartOffset=<seconds> is added to every Start delay (check T1).
 *             Stage1/2/3  the human's heist stage (record +0x78) first reaches it, + Delay
 *             Aboard  the human's status becomes 4, + Delay      Join   kljoin.c has just requested its jump, + Delay
 *             Box     the human's feet (player+0x460) are inside Box=x0,x1,y0,y1,z0,z1 and the round is NotBefore old
 *      Needs  Kane | Lynch (that one is there) | Both | KaneOnly | LynchOnly (there, and the other not)
 *      Scenes of one Name are alternatives. NEEDS IS EVALUATED WHEN THE SCENE IS DUE (review 3.3 c), not at the
 *      start of the round: at that tick the first alternative whose Needs hold is started; if none holds the name
 *      is over for the round and one 'nothing for' line says who was missing. A name is decided once a round.
 *      A started scene says line k at its start + at; if the line's speaker is no longer there the rest is dropped.
 *    [Chatter] Gap=lo,hi  MemberGap  Quiet  EventChance  Once  Speakers  + [Pool.n] (Who = Kane | Lynch | Any |
 *      Squad1 | Squad2; On = Idle | Money | Down | Stage2 | Traitor; Key.k) + [Pair.n] (Call= / Reply= who,key).
 *      Idle: every Gap seconds (drawn anew) one member in play says an unused key of an Idle pool that fits him:
 *      Kane / Lynch pools for whoever wears them; Any for a Dog Days body, the key + `_C<n>`, n = 1 + the voice
 *      byte [rules+0x33e+record] (the game's own rule, re\bots_voice.md 1.2); Squad1 / Squad2 for any other body,
 *      by record parity (GUESS of the spec: odd = Squad1). One idle turn in three (GUESS) is a Pair when Kane and
 *      Lynch are both there and may both speak: the reply 2.9 s after the call (2.5 s clip GUESS + 0.4).
 *      Events (EventChance percent each): Money = a member's money rose (he speaks), Stage2 = a member's stage
 *      reached 2 (he speaks), Down = a member died (another speaks), Traitor = a member got the traitor mark
 *      (another speaks). Caps: Once=1 a key is said at most once a round; Speakers=0 the human's own character does
 *      not chatter; MemberGap seconds between two lines of one member; no chatter while a scene runs, within Quiet
 *      seconds of a scene line, or within Quiet seconds of the last chatter line (a Pair's reply excepted).
 *      Our own generator (the game's is not touched).
 *
 * KLHook.ini
 *   [Talk]
 *   Enable=0          1 = this file is on
 *   Chatter=1         0 = the scenes only
 *   StartOffset=0     seconds added to every Start delay (may be negative): the one number check T1 settles
 *   LogOnly=0         1 = nothing is called: every line is logged as 'would say' (check T1, the timing run); a stream
 *                     file that is too small is then only noted, so T1 can run before the new PC_Def.str is installed
 *   Seed=0            0 = a new one each start
 *   Log=1             2 = also the triggers as they are seen
 *
 * LOG (the live checks T1..T9 of re\talk.md 8 go by these)
 *   talk: on; Chatter=1 StartOffset=0.00 LogOnly=0 ...
 *   talk: level f01\f01_main: <file> Version 1, map retomoto: Kane = character 9, Lynch = 10, 13 scenes, 17 pools, 7 pairs, blast at 13.00 s
 *   talk: stream file <path> has N bytes, the level needs M: ok            (or: REFUSED - nothing is said on this level)
 *   talk: round 1: session state 0x19 at t0 (rules ...): Kane = record 0 (the player), Lynch = nobody
 *   talk: scene countdown (Needs=Kane) starts at 5.79 s: Kane = record 0 (the player), Lynch = nobody
 *   talk: said KLTalk/M09_Countdown_050_Hero at 13.00 s (Kane = record 0; scene countdown line 5 of 6; speech queue 0 -> 1)
 *   talk: nothing for 'room' at 31.20 s: Kane = nobody, Lynch = nobody
 *   talk: scene room dropped at line 3: Lynch is no longer there
 *   talk: said AllLevels/Oneliners/What/What_010_Kane at 71.44 s (Kane = record 0; chatter kane_idle; speech queue 0 -> 1)
 *   talk: NOT said <key> at ... : the game's speech is off (...)     /     talk: key <key> is not in this level's .LOC ...
 *
 * 5. VERSION 2 (2026-10-23, NOT RUN; re\talk.md 10). A file with [Talk] Version=2 (Version=1 still reads as before) may use, on top of section 4:
 *      Who= / the speaker of a Line / Call= / Reply=   a character of the level's KLWardrobe.ini by its Name= ('Ashkanan') or number ('Char11'),
 *                     besides Kane | Lynch | Any | Squad1 | Squad2 | Fed. A name the wardrobe lacks makes that pool / pair unused (counted in the log), never a refusal.
 *      Idle / event keys: a member's own named pools come first (keys as written, no `_C<n>`); only when they have no key left does the class of his body decide.
 *      [Chatter] KeyGap=<s>  with Once=0: the same key may not be said again within s seconds (default 0 = no limit). Once=1 is unchanged.
 *      [Chatter] PairChance=<percent>  of an idle turn that tries a pair (default 33, the old 'one in three').
 *      [Pair.n] Call= / Reply= between ANY two characters that are there (the old file needed Kane and Lynch); Wait=<s> call -> answer (default 2.9).
 *      [Scene.n] Cast.Kane= / Cast.Lynch= <name>: the scene's 'Kane' / 'Lynch' lines (Needs, Line.k = Kane|Lynch,...) are said by whoever wears
 *                     those characters. Scenes of one Name stay alternatives: list the Kane / Lynch one first, the cast ones after it.
 *    Limits: 96 scenes, 160 pools, 160 pairs, 640 keys said per level generation. An older hook REFUSES nothing of this but reads Version=2 as
 *    'not mine' and says nothing on the level, so the hook goes in with (or before) the files.
 *
 * THE FED (owner item 12, 2026-10-18, NOT RUN): [Pool.n] Who=Fed On=FedRespawn / On=FedKill (only those two words go with Who=Fed). FedRespawn: the local
 *   player is a ZFFPlayer of type 3 with police byte 1 and his crew record 0 is back in play (status 0) - the 0 -> 1 edge. FedKill: the points pop-up's
 *   message counter (klhud_kill.c, so it needs [HUD] KillLine or Draft) changes while he is police. Said with speaker -3 (GUESS), 15 s apart per event,
 *   held up to 10 s while another line runs. Off unless the file has such a pool; an older hook refuses the unknown word (kl_dmlines --fed writes
 *   the file as KLTalk.newhook.ini). Log: 'talk: fed: ...'.
 *
 * THE THREE LINES IN klhook.c:  #include "kltalk.c" after klcrew.c;  klk_tick(game_thread) after klw_tick;  klk_init()
 * after klw_init().
 */
#ifndef KLTALK_C
#define KLTALK_C

#define KLK_SESSION    0x0168e598             /* +0x5c mode (4 = Arcade), +0x70 state, +0x15d byte 'speech may be said' (0x421ca6) */
#define KLK_MANAGER    0x0168e958             /* the speech manager: +0x956 byte 'off', +0x974 the queue */
#define KLK_LOOKUP     0x00828fa0             /* (this, key, entry) ret 8 */
#define KLK_SAY        0x00421c70             /* (this, line, other, speaker, last) ret 0x10 */
#define KLK_LINE_LIST  0x00bc998c             /* what the line constructor 0x667610 writes at +4 */
#define KLK_ROUND      0x19
#define KLK_NSCENE     96
#define KLK_NLINE      8
#define KLK_NPOOL      160
#define KLK_NKEY       24
#define KLK_NPAIR      160
#define KLK_KEYLEN     100
#define KLK_NENTRY     640
#define KLK_NSAID      512

enum { KLK_KANE = 1, KLK_LYNCH = 2, KLK_ANY = 3, KLK_SQUAD1 = 4, KLK_SQUAD2 = 5, KLK_FED = 6, KLK_NAME = 7 };      /* KLK_NAME: Who=<character name> / Char<n> of the level's wardrobe (Version 2 files, section 5) */
enum { KLK_N_KANE = 1, KLK_N_LYNCH, KLK_N_BOTH, KLK_N_KANEONLY, KLK_N_LYNCHONLY };
enum { KLK_W_START = 1, KLK_W_STAGE1, KLK_W_STAGE2, KLK_W_STAGE3, KLK_W_ABOARD, KLK_W_JOIN, KLK_W_BOX };
enum { KLK_ON_IDLE = 1, KLK_ON_MONEY, KLK_ON_DOWN, KLK_ON_STAGE2, KLK_ON_TRAITOR, KLK_ON_SHOOT, KLK_ON_WON, KLK_ON_FEDRESPAWN, KLK_ON_FEDKILL };
static const char *const klk_needs_name[6] = { "?", "Kane", "Lynch", "Both", "KaneOnly", "LynchOnly" };

struct klk_line { int who, ch; float at, len; char key[KLK_KEYLEN]; };
struct klk_scene { char name[24]; int when, needs, nlines, has_box, group, cast_k, cast_l; float delay, box[6], not_before; struct klk_line l[KLK_NLINE]; };      /* cast_k / cast_l: wardrobe characters that play 'Kane' / 'Lynch' in this scene (0 = the file's Kane= / Lynch=) */
struct klk_pool { char name[24]; int who, ch, on, nkeys; char key[KLK_NKEY][KLK_KEYLEN]; };
struct klk_pair { int cwho, rwho, cch, rch; float wait; char call[KLK_KEYLEN], reply[KLK_KEYLEN]; };

static struct { int on, log, chatter, logonly, stock; float start_offset; DWORD seed; } klk;
static struct {
    int have, tried, version, kane, lynch, nscene, npool, npair, once, speakers, event_chance, pair_chance, skipped;
    unsigned __int64 stream_bytes; float blast, start16, gap_lo, gap_hi, member_gap, quiet, key_gap;
    char key[64], file[MAX_PATH], map[32];
    struct klk_scene sc[KLK_NSCENE]; struct klk_pool pool[KLK_NPOOL]; struct klk_pair pair[KLK_NPAIR];
} klk_lv;
static struct {                                  /* the round */
    DWORD rules, t0, t16, join_seen; int left, running, rounds, init;
    float ev_stage[4], ev_aboard, ev_join, box_at[KLK_NSCENE], sc_t0[KLK_NSCENE];
    char sc_state[KLK_NSCENE], done[KLK_NSCENE]; int sc_next[KLK_NSCENE];              /* state: 0 waits, 1 runs, 2 over; done[] by group */
    float next_idle, last_scene_line, last_chatter, member_last[KLW_NREC];
    DWORD money[KLW_NREC]; BYTE status[KLW_NREC], stage[KLW_NREC], flags[KLW_NREC]; char known[KLW_NREC];
    DWORD said[KLK_NSAID]; float said_at[KLK_NSAID]; float rt_now; int nsaid, shooting, won;      /* said_at: when each key was last said (KeyGap), rt_now: the round clock of this tick */
    int fed_was; LONG fed_kn; float fed_ev[2], fed_last[2];                       /* the Fed events: was he police last tick, the reward counter, when each was seen (-1 none) / last said */
    struct { int on, rec; float at; char key[KLK_KEYLEN]; } reply;      /* rec = crew record of the one who answers */
} klk_r;
static struct { DWORD rules; char scene[160]; int n, toldfull; struct { DWORD hash; void *entry; int found; } e[KLK_NENTRY]; } klk_gen;      /* entries of this level generation */
static DWORD klk_rng;
#ifdef KLTALK_TEST
static DWORD klk_test_clock; static int klk_test_clock_on;
static DWORD klk_now(void) { return klk_test_clock_on ? klk_test_clock : GetTickCount(); }
#else
static DWORD klk_now(void) { return GetTickCount(); }
#endif

static DWORD klk_rnd(DWORD n)
{   /* 0 .. n-1; xorshift32, our own */
    DWORD x = klk_rng ? klk_rng : 0x6b6c746bu;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    klk_rng = x;
    return n ? (x >> 8) % n : 0;
}

static DWORD klk_hash(const char *s)
{   /* FNV-1a over the lower-case text (the .LOC look-up does not care about case in the pools' keys) */
    DWORD h = 2166136261u;
    for (; *s; s++) { h ^= (BYTE)(*s >= 'A' && *s <= 'Z' ? *s + 32 : *s); h *= 16777619u; }
    return h ? h : 1;
}

/* ---------------------------------------------------------------- KLTalk.ini */

static int klk_word(const char *v, const char *const *names, int n)
{
    int i;
    for (i = 1; i < n; i++) if (!_stricmp(v, names[i])) return i;
    return 0;
}

static int klk_who_of(const char *v)
{
    static const char *const names[7] = { "", "Kane", "Lynch", "Any", "Squad1", "Squad2", "Fed" };      /* Fed: only the pools of the two Fed events (the local player is police) */
    return klk_word(v, names, 7);
}

/* a wardrobe character by name ('Ashkanan', case-blind, as KLWardrobe.ini's Name=) or by number ('Char11') -> 1-based number, 0 = none.
   Reads klc_w, which klk_source has just seen is the wardrobe of this level. */
static int klk_char_of_name(const char *v)
{
    int i, r = 0;
    while (*v == ' ') v++;
    if (!_strnicmp(v, "Char", 4) && v[4] >= '0' && v[4] <= '9') {
        i = atoi(v + 4);
        EnterCriticalSection(&klc_cs);
        if (klc_w.on && i >= 1 && i <= klc_w.n) r = i;
        LeaveCriticalSection(&klc_cs);
        return r;
    }
    EnterCriticalSection(&klc_cs);
    if (klc_w.on) for (i = 0; i < klc_w.n; i++) if (!_stricmp(v, klc_w.c[i].name)) { r = i + 1; break; }
    LeaveCriticalSection(&klc_cs);
    return r;
}

/* Who= / the speaker word of a line: the six words, else a character of the wardrobe (KLK_NAME + number in *ch). 0 = unknown. */
static int klk_who_ch(const char *v, int *ch)
{
    int w = klk_who_of(v);
    *ch = 0;
    if (w) return w;
    if ((*ch = klk_char_of_name(v)) != 0) return KLK_NAME;
    return 0;
}

/* "who,key" -> who and key; "who,at,seconds,key" when at is given */
static int klk_split(const char *v, int *who, int *ch, float *at, float *len, char key[KLK_KEYLEN])
{
    char t[KLK_KEYLEN + 64], *p, *q;
    snprintf(t, sizeof t, "%s", v);
    if (!(p = strchr(t, ','))) return 0;
    *p++ = 0;
    if (!(*who = klk_who_ch(t, ch))) return 0;
    if (at) {
        if (!(q = strchr(p, ','))) return 0;
        *q++ = 0; *at = (float)atof(p); p = q;
        if (!(q = strchr(p, ','))) return 0;
        *q++ = 0; *len = (float)atof(p); p = q;
    }
    while (*p == ' ') p++;
    if (!*p || strlen(p) >= KLK_KEYLEN - 8) return 0;                       /* room for `_C<n>` */
    strcpy(key, p);
    return 1;
}

static void klk_ini_value(const char *sec, const char *k, const char *v, int *bad)
{
    static const char *const whens[8] = { "", "Start", "Stage1", "Stage2", "Stage3", "Aboard", "Join", "Box" };
    static const char *const ons[10] = { "", "Idle", "Money", "Down", "Stage2", "Traitor", "Shoot", "Won", "FedRespawn", "FedKill" };
    int n;
    if (!_stricmp(sec, "Talk")) {
        if (!_stricmp(k, "Version")) klk_lv.version = atoi(v);
        else if (!_stricmp(k, "Kane")) klk_lv.kane = atoi(v);
        else if (!_stricmp(k, "Lynch")) klk_lv.lynch = atoi(v);
        else if (!_stricmp(k, "StreamBytes")) klk_lv.stream_bytes = _strtoui64(v, 0, 10);
        else if (!_stricmp(k, "Blast")) klk_lv.blast = (float)atof(v);
        else if (!_stricmp(k, "Start16")) klk_lv.start16 = (float)atof(v);
        else if (!_stricmp(k, "Map")) snprintf(klk_lv.map, sizeof klk_lv.map, "%s", v);
    } else if (!_strnicmp(sec, "Scene.", 6)) {
        struct klk_scene *s;
        if ((n = atoi(sec + 6)) < 1 || n > KLK_NSCENE) { (*bad)++; return; }
        s = &klk_lv.sc[n - 1]; if (n > klk_lv.nscene) klk_lv.nscene = n;
        if (!_stricmp(k, "Name")) snprintf(s->name, sizeof s->name, "%s", v);
        else if (!_stricmp(k, "When")) { if (!(s->when = klk_word(v, whens, 8))) (*bad)++; }
        else if (!_stricmp(k, "Needs")) { if (!(s->needs = klk_word(v, klk_needs_name, 6))) (*bad)++; }
        else if (!_stricmp(k, "Delay")) s->delay = (float)atof(v);
        else if (!_stricmp(k, "NotBefore")) s->not_before = (float)atof(v);
        else if (!_stricmp(k, "Cast.Kane")) { if (!(s->cast_k = klk_char_of_name(v))) (*bad)++; }       /* V4: who plays the 'Kane' of this scene */
        else if (!_stricmp(k, "Cast.Lynch")) { if (!(s->cast_l = klk_char_of_name(v))) (*bad)++; }
        else if (!_stricmp(k, "Box")) { if (sscanf(v, "%f,%f,%f,%f,%f,%f", &s->box[0], &s->box[1], &s->box[2], &s->box[3], &s->box[4], &s->box[5]) == 6) s->has_box = 1; else (*bad)++; }
        else if (!_strnicmp(k, "Line.", 5)) {
            int i = atoi(k + 5);
            if (i < 1 || i > KLK_NLINE || !klk_split(v, &s->l[i - 1].who, &s->l[i - 1].ch, &s->l[i - 1].at, &s->l[i - 1].len, s->l[i - 1].key) || (s->l[i - 1].who > KLK_LYNCH && s->l[i - 1].who != KLK_NAME)) { (*bad)++; return; }
            if (i > s->nlines) s->nlines = i;
        }
    } else if (!_stricmp(sec, "Chatter")) {
        if (!_stricmp(k, "Gap")) { if (sscanf(v, "%f,%f", &klk_lv.gap_lo, &klk_lv.gap_hi) != 2) (*bad)++; }
        else if (!_stricmp(k, "MemberGap")) klk_lv.member_gap = (float)atof(v);
        else if (!_stricmp(k, "Quiet")) klk_lv.quiet = (float)atof(v);
        else if (!_stricmp(k, "EventChance")) klk_lv.event_chance = atoi(v);
        else if (!_stricmp(k, "Once")) klk_lv.once = atoi(v);
        else if (!_stricmp(k, "KeyGap")) klk_lv.key_gap = (float)atof(v);                 /* Once=0: seconds before the same key may be said again */
        else if (!_stricmp(k, "PairChance")) klk_lv.pair_chance = atoi(v);
        else if (!_stricmp(k, "Speakers")) klk_lv.speakers = atoi(v);
    } else if (!_strnicmp(sec, "Pool.", 5)) {
        struct klk_pool *p;
        if ((n = atoi(sec + 5)) < 1 || n > KLK_NPOOL) { (*bad)++; return; }
        p = &klk_lv.pool[n - 1]; if (n > klk_lv.npool) klk_lv.npool = n;
        if (!_stricmp(k, "Name")) snprintf(p->name, sizeof p->name, "%s", v);
        else if (!_stricmp(k, "Who")) { if (!(p->who = klk_who_ch(v, &p->ch))) klk_lv.skipped++; }      /* a name this wardrobe lacks: the pool never matches */
        else if (!_stricmp(k, "On")) { if (!(p->on = klk_word(v, ons, 10))) (*bad)++; }
        else if (!_strnicmp(k, "Key.", 4)) {
            int i = atoi(k + 4);
            if (i < 1 || i > KLK_NKEY || strlen(v) >= KLK_KEYLEN - 8) { (*bad)++; return; }
            strcpy(p->key[i - 1], v); if (i > p->nkeys) p->nkeys = i;
        }
    } else if (!_strnicmp(sec, "Pair.", 5)) {
        struct klk_pair *p;
        if ((n = atoi(sec + 5)) < 1 || n > KLK_NPAIR) { (*bad)++; return; }
        p = &klk_lv.pair[n - 1]; if (n > klk_lv.npair) klk_lv.npair = n;
        if (!_stricmp(k, "Call")) { if (!klk_split(v, &p->cwho, &p->cch, 0, 0, p->call) || (p->cwho > KLK_LYNCH && p->cwho != KLK_NAME)) { p->cwho = 0; klk_lv.skipped++; } }
        else if (!_stricmp(k, "Reply")) { if (!klk_split(v, &p->rwho, &p->rch, 0, 0, p->reply) || (p->rwho > KLK_LYNCH && p->rwho != KLK_NAME)) { p->rwho = 0; klk_lv.skipped++; } }
        else if (!_stricmp(k, "Wait")) p->wait = (float)atof(v);                              /* seconds from the call to the answer (default 2.9) */
    }
}

/* our own reader (one pass over the file; the profile API would open it some 400 times on the game's thread) */
static int klk_ini_read(const char *file, int *bad)
{
    HANDLE f = CreateFileA(file, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, 0, 0); DWORD size, got = 0; char *buf, *p, *e, sec[32] = "";
    if (f == INVALID_HANDLE_VALUE) return 0;
    size = GetFileSize(f, 0);
    if (size == INVALID_FILE_SIZE || size > 0x80000 || !(buf = (char *)HeapAlloc(GetProcessHeap(), 0, size + 2))) { CloseHandle(f); return 0; }
    if (!ReadFile(f, buf, size, &got, 0) || got != size) { CloseHandle(f); HeapFree(GetProcessHeap(), 0, buf); return 0; }
    CloseHandle(f);
    buf[size] = '\n'; buf[size + 1] = 0;
    for (p = buf; *p; p = e + 1) {
        char *a = p, *z, *eq;
        if (!(e = strchr(p, '\n'))) break;
        for (z = e; z > a && (z[-1] == '\r' || z[-1] == ' ' || z[-1] == '\t'); z--) ;
        *z = 0; *e = 0;
        while (*a == ' ' || *a == '\t') a++;
        if (!*a || *a == ';') continue;
        if (*a == '[') { if ((eq = strchr(a, ']')) != 0) { *eq = 0; snprintf(sec, sizeof sec, "%s", a + 1); } continue; }
        if (!(eq = strchr(a, '='))) continue;
        *eq = 0;
        klk_ini_value(sec, a, eq + 1, bad);
    }
    HeapFree(GetProcessHeap(), 0, buf);
    return 1;
}

/* the size of the stream file the game opens: the expansion's overlay copy when there is one (klslot.c), else the game's */
static int klk_stream_size(unsigned __int64 *size, char path[MAX_PATH])
{
    WIN32_FILE_ATTRIBUTE_DATA fa; char root[MAX_PATH];
    if (GetPrivateProfileIntA("Expansion", "Enable", 0, klh_ini) && GetPrivateProfileIntA("Expansion", "Overlay", 1, klh_ini)) {
        GetPrivateProfileStringA("Expansion", "Root", "KLExpansion", root, sizeof root, klh_ini);
        snprintf(path, MAX_PATH, "%s\\%s\\Overlay\\PC_Def.str", dir, root);
        if (GetFileAttributesExA(path, GetFileExInfoStandard, &fa) && !(fa.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) { *size = ((unsigned __int64)fa.nFileSizeHigh << 32) | fa.nFileSizeLow; return 1; }
    }
    snprintf(path, MAX_PATH, "%s\\PC_Def.str", dir);
    if (!GetFileAttributesExA(path, GetFileExInfoStandard, &fa) || (fa.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) return 0;
    *size = ((unsigned __int64)fa.nFileSizeHigh << 32) | fa.nFileSizeLow;
    return 1;
}

/* KLTalk.ini of the level that runs: beside the KLWardrobe.ini klchar.c read for it. Read once per level key and file. */
static void klk_source(const char *key)
{
    char file[MAX_PATH], path[MAX_PATH], *s; unsigned __int64 have = 0; int ok = 0, bad = 0, i, j;
    EnterCriticalSection(&klc_cs);
    if (klc_w.on && !_stricmp(key, klc_w.key)) { snprintf(file, sizeof file, "%s", klc_w.file); ok = 1; }
    LeaveCriticalSection(&klc_cs);
    if (!ok) {
        if (klk_lv.tried != 2 || strcmp(klk_lv.key, key)) {
            memset(&klk_lv, 0, sizeof klk_lv); klk_lv.tried = 2; snprintf(klk_lv.key, sizeof klk_lv.key, "%s", key);
            klog("talk: level %s has no wardrobe (no KLWardrobe.ini was read for it%s): nobody can wear Kane or Lynch, nothing is said", key, klc_on ? "" : "; [Character] Enable=0");
        }
        return;
    }
    if (!(s = strrchr(file, 0x5c)) || (size_t)(s - file) + 12 >= sizeof file) return;
    strcpy(s + 1, "KLTalk.ini");
    if (klk_lv.tried == 1 && !strcmp(klk_lv.key, key) && !_stricmp(klk_lv.file, file)) return;
    memset(&klk_lv, 0, sizeof klk_lv);
    klk_lv.tried = 1; snprintf(klk_lv.key, sizeof klk_lv.key, "%s", key); strcpy(klk_lv.file, file);
    klk_lv.gap_lo = 40; klk_lv.gap_hi = 90; klk_lv.member_gap = 25; klk_lv.quiet = 8; klk_lv.event_chance = 50; klk_lv.once = 1; klk_lv.pair_chance = 33;
    if (!klk_ini_read(file, &bad)) { klog("talk: level %s has no KLTalk.ini beside its archive (%s): nothing is said", key, file); return; }
    if (klk_lv.version != 1 && klk_lv.version != 2) { klog("talk: %s has Version=%d, this hook reads 1 and 2: nothing is said on this level", file, klk_lv.version); return; }
    if (bad) { klog("talk: %s has %d value(s) this hook cannot read (a scene, pool or pair number over the limit, an unknown When / Needs / Who / On, a key too long): REFUSED, nothing is said on this level", file, bad); return; }
    for (i = 0; i < klk_lv.nscene; i++) {
        struct klk_scene *sc = &klk_lv.sc[i];
        if (!sc->name[0] || !sc->when || !sc->needs || sc->nlines < 1 || (sc->when == KLK_W_BOX) != (sc->has_box != 0)) { klog("talk: %s: [Scene.%d] is not complete (Name, When, Needs, Lines; Box with When=Box only): REFUSED, nothing is said on this level", file, i + 1); return; }
        for (j = 0; j < sc->nlines; j++) if (!sc->l[j].who || !sc->l[j].key[0]) { klog("talk: %s: [Scene.%d] Line.%d is missing: REFUSED, nothing is said on this level", file, i + 1, j + 1); return; }
        for (j = 0; j < i && strcmp(klk_lv.sc[j].name, sc->name); j++) ;
        sc->group = j;                                                       /* the first scene of that Name */
    }
    if (klk_lv.gap_lo < 5) klk_lv.gap_lo = 5;                                /* never a line every tick, whatever the file says */
    if (klk_lv.gap_hi < klk_lv.gap_lo) klk_lv.gap_hi = klk_lv.gap_lo;
    if (klk_lv.quiet < 1) klk_lv.quiet = 1;
    if (klk_lv.pair_chance < 0) klk_lv.pair_chance = 0;
    if (klk_lv.key_gap < 0) klk_lv.key_gap = 0;
    for (i = 0; i < klk_lv.npair; i++) if (klk_lv.pair[i].wait <= 0) klk_lv.pair[i].wait = 2.9f;
    klog("talk: level %s: %s Version %d, map %s: Kane = character %d, Lynch = %d, %d scenes, %d pools, %d pairs, blast at %.2f s; Once=%d KeyGap=%.0f PairChance=%d", key, file, klk_lv.version, klk_lv.map, klk_lv.kane, klk_lv.lynch, klk_lv.nscene, klk_lv.npool, klk_lv.npair, klk_lv.blast, klk_lv.once, klk_lv.key_gap, klk_lv.pair_chance);
    if (klk_lv.skipped) klog("talk: %s: %d pool / pair entries name a character or word this build does not know: they are never used", file, klk_lv.skipped);
    if (klk_lv.stream_bytes) {
        if (!klk_stream_size(&have, path)) { klog("talk: the stream file %s cannot be measured and the level needs %I64u bytes of it: REFUSED - nothing is said on this level", path, klk_lv.stream_bytes); return; }
        if (have < klk_lv.stream_bytes && klk.logonly) klog("talk: stream file %s has %I64u bytes, the level needs %I64u: too small, but LogOnly=1 says nothing anyway - the timing run goes on", path, have, klk_lv.stream_bytes);
        else if (have < klk_lv.stream_bytes) { klog("talk: stream file %s has %I64u bytes, the level needs %I64u: REFUSED - nothing is said on this level (install the level's PC_Def.str first: re\\talk.md 7)", path, have, klk_lv.stream_bytes); return; }
        else klog("talk: stream file %s has %I64u bytes, the level needs %I64u: ok", path, have, klk_lv.stream_bytes);
    }
    klk_lv.have = 1;
}

/* ---------------------------------------------------------------- the two game calls */

static int klk_same_code(DWORD va, const BYTE *bytes, int n)
{
    BYTE c[16];
    return n <= (int)sizeof c && klh_rd((DWORD_PTR)KLH_VA(va), c, n) && !memcmp(c, bytes, n);
}

/* The entry of a key in this level generation: made and looked up once. -> the entry, 0 = the game does not know the
   key (or the table is full / the lookup cannot be made). Game thread only. */
static void *klk_entry(const char *key, DWORD rules, const char *scene)
{
    DWORD h = klk_hash(key), sys, a, lm, found; void *e; int i;
    if (klk_gen.rules != rules || strcmp(klk_gen.scene, scene)) {            /* a new level generation: the old entries stay allocated, they are only forgotten */
        memset(&klk_gen, 0, sizeof klk_gen); klk_gen.rules = rules; snprintf(klk_gen.scene, sizeof klk_gen.scene, "%s", scene);
    }
    for (i = 0; i < klk_gen.n; i++) if (klk_gen.e[i].hash == h) return klk_gen.e[i].found ? klk_gen.e[i].entry : 0;
    if (klk_gen.n >= KLK_NENTRY) { if (!klk_gen.toldfull++) klog("talk: %d keys were looked up on this level: no further key is said", KLK_NENTRY); return 0; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(a = klh_rd32(sys + 0xac)) || !klh_rd(a + 0x94, &lm, 4) || !lm || !klh_rd(lm, &found, 4)) {
        klog("talk: the .LOC look-up object [[sysif+0xac]+0x94] cannot be read: %s is not said", key);
        return 0;                                                            /* not remembered: tried again at the next say */
    }
    if (!(e = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, 0x204))) return 0;
    found = (DWORD)(DWORD_PTR)((void *(__fastcall *)(void *, void *, const char *, void *))(DWORD_PTR)KLH_VA(KLK_LOOKUP))((void *)(DWORD_PTR)lm, 0, key, e);
    klk_gen.e[klk_gen.n].hash = h; klk_gen.e[klk_gen.n].entry = e; klk_gen.e[klk_gen.n].found = found && *(DWORD *)e;
    klk_gen.n++;
    if (!found || !*(DWORD *)e) { klog("talk: key %s is not in this level's .LOC (the game's look-up 0x828fa0 answered 0): it is not said", key); return 0; }
    return e;
}

/* Say one key. -> 1 said (or, LogOnly, would have been), 0 not. Game thread only; what = the log's description. */
static int klk_say(const char *key, int rec, float rt, const char *what, DWORD rules, const char *scene)
{
    static const BYTE lookup_code[16] = { 0x56, 0x8b, 0x74, 0x24, 0x08, 0x8b, 0xc6, 0x57, 0x8b, 0xf9, 0x8d, 0x50, 0x01, 0x8d, 0x49, 0x00 };    /* 0x828fa0 */
    static const BYTE say_code[15] = { 0x83, 0xec, 0x1c, 0xa1, 0xe0, 0x9e, 0xd4, 0x00, 0x33, 0xc4, 0x89, 0x44, 0x24, 0x18, 0x53 };              /* 0x421c70 .. push ebx */
    static int toldcode, toldmgr;
    DWORD mgr, queue, sm, q0 = 0, q1 = 0, *line; BYTE off = 1, may = 0; void *e;
    if (klk.logonly) { klog("talk: would say %s at %.2f s (%s) - LogOnly=1, nothing is called", key, rt, what); return 1; }
    if (!klk_same_code(KLK_LOOKUP, lookup_code, sizeof lookup_code) || !klk_same_code(KLK_SAY, say_code, sizeof say_code)) {
        if (!toldcode++) klog("talk: the two game routines are not the ones this build knows: nothing is said");
        return 0;
    }
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLK_MANAGER))) || !klh_rd(mgr + 0x956, &off, 1) || !(queue = klh_rd32(mgr + 0x974)) || !klh_rd(queue, &q0, 4) || q0 > 10 ||
        !(sm = klh_rd32((DWORD_PTR)KLH_VA(KLK_SESSION))) || !klh_rd(sm + 0x15d, &may, 1)) {
        if (!toldmgr++) klog("talk: the speech manager [0x168e958] or its queue cannot be read (manager %08lx): nothing is said", mgr);
        return 0;
    }
    if (!klh_rd32(rules + 0x5f8)) { static int told58; if (!told58++) klog("talk: [rules+0x5f8] is null: nothing is said (0x771a10 would read through it)"); return 0; }   /* review */
    /* NOT DONE ON PURPOSE: setting [session+0x15d] before GO so that lines can be said in the pre-round. Tried live 2026-10-10
       (run T4): the two early countdown lines were said, and 8 s after GO the round stood still with a grey screen (no
       frame from the main loop, bots frozen; ended by the run's time limit). The game's speech is off before GO: start
       scenes at GO or later. */
    if (off || !may) { klog("talk: NOT said %s at %.2f s (%s): the game's speech is off ([manager+0x956] = %u, [session+0x15d] = %u; 0x421c70 would return at once)", key, rt, what, off, may); return 0; }
    if (!(e = klk_entry(key, rules, scene))) return 0;
    if (!(line = (DWORD *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, 0x28 + 12))) return 0;      /* a new one per say, never freed (section 2) */
    line[0] = (DWORD)(DWORD_PTR)e; line[1] = KLK_LINE_LIST; line[3] = 3; line[4] = 1; line[5] = (DWORD)(DWORD_PTR)(line + 10); line[9] = 0xffffffffu;      /* +0x1c 0.0, +0x20 flag 0, +0x24 priority -1 */
    ((void (__fastcall *)(void *, void *, void *, void *, int, int))(DWORD_PTR)KLH_VA(KLK_SAY))((void *)(DWORD_PTR)mgr, 0, line, 0, rec, 0);
    klh_rd(queue, &q1, 4);
    klog("talk: said %s at %.2f s (%s; speech queue %lu -> %lu)", key, rt, what, q0, q1);
    return 1;
}

/* ---------------------------------------------------------------- the round */

struct klk_here { int kane, lynch, kane_i, lynch_i; };              /* crew record index of who wears him (-1 = nobody) and his place in who.m[] */

/* who plays the two roles: the characters kch / lch (0 = none) */
static void klk_present_as(const struct klw_who *w, struct klk_here *h, int kch, int lch)
{
    int i;
    h->kane = h->lynch = h->kane_i = h->lynch_i = -1;
    for (i = 0; i < w->n; i++) {
        int there = w->m[i].status == 0 || w->m[i].status == 4, hum = i == w->human;
        if (!there || !w->m[i].ch) continue;
        if (kch && w->m[i].ch == kch && (h->kane < 0 || hum)) { h->kane = w->m[i].rec; h->kane_i = i; }
        if (lch && w->m[i].ch == lch && (h->lynch < 0 || hum)) { h->lynch = w->m[i].rec; h->lynch_i = i; }
    }
}

static void klk_present(const struct klw_who *w, struct klk_here *h) { klk_present_as(w, h, klk_lv.kane, klk_lv.lynch); }

/* the roles of one scene: its Cast.Kane= / Cast.Lynch= (V4: the Kane / Lynch scenes with any two characters), else the file's */
static void klk_scene_here(const struct klw_who *w, const struct klk_scene *sc, const struct klk_here *dflt, struct klk_here *h)
{
    if (!sc->cast_k && !sc->cast_l) { *h = *dflt; return; }
    klk_present_as(w, h, sc->cast_k ? sc->cast_k : klk_lv.kane, sc->cast_l ? sc->cast_l : klk_lv.lynch);
}

/* member index of a wardrobe character that is there (in play or aboard); the human first. -1 = nobody wears him */
static int klk_member_ch(const struct klw_who *w, int ch)
{
    int i, r = -1;
    if (ch < 1) return -1;
    for (i = 0; i < w->n; i++) {
        if (w->m[i].ch != ch || !(w->m[i].status == 0 || w->m[i].status == 4)) continue;
        if (r < 0 || i == w->human) r = i;
    }
    return r;
}

/* the member a pair names: Kane / Lynch by the file's numbers, or a character by name */
static int klk_pair_member(const struct klw_who *w, const struct klk_here *h, int who, int ch)
{
    return who == KLK_KANE ? h->kane_i : who == KLK_LYNCH ? h->lynch_i : who == KLK_NAME ? klk_member_ch(w, ch) : -1;
}

static const char *klk_who_text(const struct klw_who *w, const struct klk_here *h, char out[96])
{
    char a[40], b[40];
    if (h->kane < 0) strcpy(a, "nobody"); else snprintf(a, sizeof a, "record %d (%s)", h->kane, h->kane_i == w->human ? "the player" : "a bot");
    if (h->lynch < 0) strcpy(b, "nobody"); else snprintf(b, sizeof b, "record %d (%s)", h->lynch, h->lynch_i == w->human ? "the player" : "a bot");
    snprintf(out, 96, "Kane = %s, Lynch = %s", a, b);
    return out;
}

static int klk_needs_hold(int needs, const struct klk_here *h)
{
    int k = h->kane >= 0, l = h->lynch >= 0;
    return needs == KLK_N_KANE ? k : needs == KLK_N_LYNCH ? l : needs == KLK_N_BOTH ? k && l : needs == KLK_N_KANEONLY ? k && !l : needs == KLK_N_LYNCHONLY ? l && !k : 0;
}

static int klk_was_said(DWORD h) { int i; for (i = 0; i < klk_r.nsaid; i++) if (klk_r.said[i] == h) return 1; return 0; }
static void klk_mark_said(DWORD h)
{
    int i;
    for (i = 0; i < klk_r.nsaid; i++) if (klk_r.said[i] == h) { klk_r.said_at[i] = klk_r.rt_now; return; }
    if (klk_r.nsaid < KLK_NSAID) { klk_r.said[klk_r.nsaid] = h; klk_r.said_at[klk_r.nsaid++] = klk_r.rt_now; }
}
/* may the key not be chosen now? Once=1: said at all this round. Once=0 with KeyGap=s: said within the last s seconds. Once=0, KeyGap=0: never blocked. */
static int klk_blocked(DWORD h)
{
    int i;
    for (i = 0; i < klk_r.nsaid; i++) if (klk_r.said[i] == h) return klk_lv.once ? 1 : klk_lv.key_gap > 0 && klk_r.rt_now - klk_r.said_at[i] < klk_lv.key_gap;
    return 0;
}

static int klk_has_pool(int on) { int p; for (p = 0; p < klk_lv.npool; p++) if (klk_lv.pool[p].on == on && klk_lv.pool[p].nkeys) return 1; return 0; }

/* may this member chatter now? (in play, not the human unless Speakers=1, his own gap over) */
static int klk_may_chatter(const struct klw_who *w, int i, float rt)
{
    int rec = w->m[i].rec;
    if (w->m[i].status != 0 || !w->m[i].ch || rec < 0 || rec >= KLW_NREC) return 0;
    if (i == w->human && !klk_lv.speakers) return 0;
    return klk_r.member_last[rec] < 0 || rt - klk_r.member_last[rec] >= klk_lv.member_gap;
}

/* which pools fit the member w->m[i] */
static int klk_pool_class(const struct klw_who *w, int i)
{
    int ch = w->m[i].ch, stock = 0;
    if (klk_lv.kane && ch == klk_lv.kane) return KLK_KANE;
    if (klk_lv.lynch && ch == klk_lv.lynch) return KLK_LYNCH;
    EnterCriticalSection(&klc_cs);
    if (klc_w.on && ch >= 1 && ch <= klc_w.n) stock = klc_w.c[ch - 1].stock;
    LeaveCriticalSection(&klc_cs);
    if (stock) return KLK_ANY;                                               /* a Dog Days body: the eight voices C1..C8 */
    return (w->m[i].rec & 1) ? KLK_SQUAD1 : KLK_SQUAD2;                      /* any other body: a squad voice by record parity (GUESS, re\talk.md 3.4) */
}

/* one unused key of a pool with that event for the member -> 1 and the final key (with `_C<n>` for Who=Any) + the pool's name */
static int klk_pool_key(const struct klw_who *w, int i, int on, DWORD rules, char key[KLK_KEYLEN], const char **pool)
{
    /* V2: pools that name the member's own character (Who=Ashkanan / Char11) come first, keys as written; only when
       none of them has a key left does the class of his body (Kane / Lynch / Any / Squad) decide, as before. */
    int cls = klk_pool_class(w, i), ch = w->m[i].ch, named, p, k, n = 0, pick; BYTE voice = 0xff; char cand[KLK_KEYLEN];
    for (named = ch > 0; named >= 0; named--) {
        if (!named && cls == KLK_ANY && (w->m[i].rec > 7 || !klh_rd(rules + 0x33e + w->m[i].rec, &voice, 1) || voice > 7)) return 0;      /* the table has eight entries, the voices are 0..7 */
        for (pick = -1, n = 0; ; pick = (int)klk_rnd((DWORD)n), n = 0) {          /* pass 1 counts, pass 2 takes number `pick` */
            for (p = 0; p < klk_lv.npool; p++) {
                if (klk_lv.pool[p].on != on) continue;
                if (named ? !(klk_lv.pool[p].who == KLK_NAME && klk_lv.pool[p].ch == ch) : klk_lv.pool[p].who != cls) continue;
                for (k = 0; k < klk_lv.pool[p].nkeys; k++) {
                    if (!klk_lv.pool[p].key[k][0]) continue;
                    if (!named && cls == KLK_ANY) snprintf(cand, sizeof cand, "%s_C%d", klk_lv.pool[p].key[k], voice + 1); else strcpy(cand, klk_lv.pool[p].key[k]);
                    if (klk_blocked(klk_hash(cand))) continue;
                    if (n++ == pick) { strcpy(key, cand); *pool = klk_lv.pool[p].name; return 1; }
                }
            }
            if (!n || pick >= 0) break;
        }
    }
    return 0;
}

static int klk_chatter_say(const struct klw_who *w, int i, const char *key, const char *pool, float rt, DWORD rules, const char *scene, int is_reply)
{
    char what[160]; int rec = w->m[i].rec;
    snprintf(what, sizeof what, "%s = record %d, character %d; chatter %s", klk_lv.kane && w->m[i].ch == klk_lv.kane ? "Kane" : klk_lv.lynch && w->m[i].ch == klk_lv.lynch ? "Lynch" : i == w->human ? "the player" : "a bot", rec, w->m[i].ch, pool);
    klk_mark_said(klk_hash(key));                                            /* also when it was not said: a key the game does not know is not tried again */
    klk_r.member_last[rec] = rt; klk_r.last_chatter = rt; (void)is_reply;
    return klk_say(key, rec, rt, what, rules, scene);
}

/* ---- the Fed events (owner item 12): the local player is police after his death. Own reader: klfed.c comes after this file,
   and klw_who_now takes only players 0..3 (a fed is 'object 9': it reads no player and gives type 0). Fields as klfed.c klp_read. */
#ifndef KLK_PLAYER_VT
#define KLK_PLAYER_VT 0x00bb45f4                  /* ZFFPlayer */
#endif
static volatile LONG klkf_n_new, klkf_n_total;                  /* klhud_kill.c (included later): counts the points pop-up's new messages, only while [HUD] KillLine / Draft is on */

/* the local player is a policeman AND his crew record is back in play (status 0: the place is set 5 s after death, a read a tick early shows status 1) */
static int klk_fed_now(const struct klw_who *w)
{
    DWORD gd, pl; BYTE sel = 0xff, type = 0, pol = 0;
    if (w->human < 0 || w->m[w->human].status != 0) return 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel >= 28) return 0;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * sel)) || klh_pvt(pl) != KLK_PLAYER_VT || !klh_rd(pl + 0x273c, &type, 1) || !klh_rd(pl + 0x2723, &pol, 1)) return 0;
    return type == 3 && pol == 1;
}

/* a key of a Who=Fed pool for that event: an unused one when there is one, else any (a fed may come back several times). No `_C<n>`. */
static int klk_fed_key(int on, char key[KLK_KEYLEN])
{
    int p, k, n, pick, any;
    for (any = 0; any < 2; any++) {
        for (pick = -1; ; pick = (int)klk_rnd((DWORD)n)) {
            n = 0;
            for (p = 0; p < klk_lv.npool; p++) {
                if (klk_lv.pool[p].who != KLK_FED || klk_lv.pool[p].on != on) continue;
                for (k = 0; k < klk_lv.pool[p].nkeys; k++) {
                    if (!klk_lv.pool[p].key[k][0] || (!any && klk_was_said(klk_hash(klk_lv.pool[p].key[k])))) continue;
                    if (n++ == pick) { strcpy(key, klk_lv.pool[p].key[k]); return 1; }
                }
            }
            if (!n || pick >= 0) break;
        }
    }
    return 0;
}

/* One tick of the Fed events (session state 0x19 only). A line is held up to 10 s while another is being said. */
static void klk_fed_tick(const struct klw_who *w, float rt, int busy, const char *scene)
{
    static const int ev[2] = { KLK_ON_FEDRESPAWN, KLK_ON_FEDKILL }; static const char *const nm[2] = { "respawn", "kill" };
    int fed, e; char key[KLK_KEYLEN], what[96];
    if (!klk.chatter || (!klk_has_pool(KLK_ON_FEDRESPAWN) && !klk_has_pool(KLK_ON_FEDKILL))) return;
    fed = klk_fed_now(w);
    if (fed && !klk_r.fed_was) { klk_r.fed_ev[0] = rt; if (klk.log) klog("talk: fed: the local player is police now (record %d back in play) at %.2f s", w->m[w->human].rec, rt); }
    if (fed && klkf_n_total != klk_r.fed_kn) { klk_r.fed_ev[1] = rt; if (klk.log) klog("talk: fed: a new reward message at %.2f s (klhud_kill.c counter %ld -> %ld)", rt, (long)klk_r.fed_kn, (long)klkf_n_total); }
    klk_r.fed_kn = klkf_n_total; klk_r.fed_was = fed;
    for (e = 0; e < 2; e++) {
        if (klk_r.fed_ev[e] < 0) continue;
        if (!fed || rt - klk_r.fed_ev[e] > 10.0f) { klk_r.fed_ev[e] = -1; continue; }                 /* gone, or too late to still fit */
        if (busy || rt - klk_r.fed_last[e] < 15.0f || rt - klk_r.last_scene_line < klk_lv.quiet || rt - klk_r.last_chatter < klk_lv.quiet) continue;
        if (e == 1 && (int)klk_rnd(100) >= klk_lv.event_chance) { klk_r.fed_ev[e] = -1; continue; }
        klk_r.fed_ev[e] = -1;
        if (!klk_fed_key(ev[e], key)) continue;
        snprintf(what, sizeof what, "the fed (record %d); %s", w->m[w->human].rec, nm[e]);
        klk_mark_said(klk_hash(key)); klk_r.fed_last[e] = rt;
        klk_say(key, -3, rt, what, w->rules, scene);                    /* speaker -3 = the police side (GUESS, re/bots_voice.md 1.4); a plain line plays whatever the speaker byte is */
        return;
    }
}

static void klk_new_round(DWORD rules)
{
    int i;
    memset(&klk_r, 0, sizeof klk_r);
    klk_r.rules = rules;
    for (i = 0; i < 4; i++) klk_r.ev_stage[i] = -1;
    klk_r.ev_aboard = klk_r.ev_join = -1;
    for (i = 0; i < KLK_NSCENE; i++) klk_r.box_at[i] = -1;
    for (i = 0; i < KLW_NREC; i++) klk_r.member_last[i] = -1;
    klk_r.last_scene_line = klk_r.last_chatter = -1000;
    klk_r.fed_ev[0] = klk_r.fed_ev[1] = -1; klk_r.fed_last[0] = klk_r.fed_last[1] = -1000; klk_r.fed_kn = klkf_n_total; klk_r.fed_was = 0;
}

/* [Voice] OnlineTraits=1 (needs [Voice] Online=1, [Online] Read=1): kltalk.c / kltrait.c also run for the LOCAL online player, who comes from
   klvoice_online.c (defined later). Default 0 (recommended off until benched). Read-only on the replicated state. */
static int kvo_online_who(struct klw_who *w, char *name);
static int klk_onl_traits(void)
{
    static int v = -1;
    if (v < 0) v = GetPrivateProfileIntA("Voice", "Online", 0, klh_ini) != 0 && GetPrivateProfileIntA("Voice", "OnlineTraits", 0, klh_ini) != 0;
    return v;
}
/* Arcade's who, else (OnlineTraits=1) the one-member online who. *onl = 1 for the online one. */
static int klk_who_any(struct klw_who *w, int *onl)
{
    char nm[32];
    *onl = 0;
    if (klw_who_now(w)) return 1;
    if (!klk_onl_traits() || !kvo_online_who(w, nm)) return 0;
    *onl = 1; return 1;
}

static void klk_tick(int game_thread)
{
    static int rounds, toldthread; static char toldscene[160];
    struct klw_who w; struct klk_here h; char scene[160], key[64], why[200], who[96], what[200], ckey[KLK_KEYLEN]; const char *pool = "";
    DWORD now, score; float rt, feet[3] = { 0, 0, 0 }; int onl = 0, i, j, v, hstage = 0, have_feet = 0, busy = 0, due_group[KLK_NSCENE];
    if (!klk.on || !klh_exe_ok) return;
    if (!klk_who_any(&w, &onl)) return;                                      /* not Arcade (nor, OnlineTraits=1, an online round with a known local seat), no ZGameRulesHeist object, no level, no crew records */
    if (!klx_on || !klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    v = klx_level_verdict(scene, why);
    /* [Talk] StockLevels=1 (default 0, owner 2026-10-23 'even in dog days'): a level the verdict calls STOCK is let through; it
       talks only if a KLTalk.ini sits beside its archive (klk_source below finds none otherwise), which only
       tools/kl_dmvoice.py puts there for the KLExpansion\Maps\DD01..DD09 copies. */
    if (v == 1 && klk.stock) v = 2;
    if (v != 2) {                                                            /* only a level that is not the stock one of its slot */
        static int toldverdict;
        if (v && (strcmp(scene, toldscene) || v != toldverdict)) { snprintf(toldscene, sizeof toldscene, "%s", scene); toldverdict = v; klog("talk: level '%s' %s (%.150s): nothing is said", scene, v == 1 ? "is the STOCK one of its slot" : "is not known", why); }
        return;
    }
    toldscene[0] = 0;
    if (!game_thread) { if (w.state == KLK_ROUND && !toldthread++) klog("talk: the tick is not on the game's thread ([KLHook] Tick=0?): nothing can be said"); return; }
    klk_source(key);
    if (!klk_lv.have) return;

    /* ---- the round: runs while the session state is 0x19 (klbot.c 1); a state >= 0x1f and back = the next round */
    if (w.rules != klk_r.rules || !klk_r.init) { klk_new_round(w.rules); klk_r.init = 1; }
    /* THE ROUND-START EVENT IS NOT STATE 0x19. Seen live 2026-10-10 (run T2, the owner by ear: 'it doesnt match the
       explosion timing'): the level's round-start event - the one the blast timer counts from - comes when the
       'Heist starts in' countdown BEGINS, about 8 s before GO; state 0x19 is GO. A level may therefore say
       Start16=<seconds from the entry of state 0x16 (the pre-round) to that event> in KLTalk.ini: the clock then
       starts there and runs through 0x16 / 0x18 into the round. Retomoto: 0x16 lasts 21.2..21.4 s (five runs), the
       event is 8.0 s before GO (kl_fa_author: blast 13 s after the event = 5 s after GO): Start16=13.3. MEASURED from
       state times and the level's timers, not from a picture of the blast. */
    now = klk_now();
    if (w.state == 0x16 && klk_r.left) { klk_new_round(w.rules); klk_r.init = 1; }      /* the next round's pre-round */
    if (w.state == 0x16 && !klk_r.t16) klk_r.t16 = now ? now : 1;
    if (w.state != KLK_ROUND) {
        int pre = klk_lv.start16 > 0 && klk_r.t16 && (w.state == 0x16 || w.state == 0x18) && !klk_r.left && now - klk_r.t16 >= (DWORD)(klk_lv.start16 * 1000);
        if (w.state >= 0x1f && klk_r.running) klk_r.left = 1;
        if (!pre) return;
    }
    if (klk_r.left) { klk_new_round(w.rules); klk_r.init = 1; }
    klk_present(&w, &h);
    if (!klk_r.running) {
        klk_r.running = 1; klk_r.t0 = (klk_lv.start16 > 0 && klk_r.t16) ? klk_r.t16 + (DWORD)(klk_lv.start16 * 1000) : now; klk_r.rounds = ++rounds; klk_r.join_seen = klj_after.at;
        klk_r.next_idle = klk_lv.gap_lo + (float)klk_rnd((DWORD)((klk_lv.gap_hi - klk_lv.gap_lo) * 10) + 1) / 10;
        klog("talk: round %d: clock starts in session state 0x%x, Start16=%.1f (rules %08lx): %s%s%s", rounds, w.state, klk_lv.start16, w.rules, klk_who_text(&w, &h, who), w.wardrobe ? "" : " - NO wardrobe", onl ? " - ONLINE: the local player only, remote players stay stock (OnlineTraits=1, GUESS T1 below)" : "");
    }
    rt = (float)(now - klk_r.t0) / 1000.0f;
    klk_r.rt_now = rt;

    /* ---- what the human does: stage, aboard, the join, his feet */
    if (w.human >= 0) {
        BYTE st = 0;
        if (klh_rd(w.m[w.human].at + 0x78, &st, 1) && st <= 3) hstage = st;
        for (i = 1; i <= 3; i++) if (hstage >= i && klk_r.ev_stage[i] < 0) { klk_r.ev_stage[i] = rt; if (klk.log > 1) klog("talk: the player reached heist stage %d at %.2f s", i, rt); }
        if (w.m[w.human].status == 4 && klk_r.ev_aboard < 0) { klk_r.ev_aboard = rt; if (klk.log > 1) klog("talk: the player is aboard at %.2f s", rt); }
        if (w.m[w.human].actor && klh_rd(w.m[w.human].actor + 0x460, feet, 12) && feet[0] == feet[0] && feet[1] == feet[1] && feet[2] == feet[2]) have_feet = 1;
    }
    if (klj_after.at != klk_r.join_seen) { klk_r.join_seen = klj_after.at; if (klk_r.ev_join < 0) { klk_r.ev_join = rt; if (klk.log > 1) klog("talk: kljoin.c requested its jump at %.2f s", rt); } }

    /* ---- scenes that come due: Needs is evaluated NOW (re\crew_talk_review.md 3.3 c) */
    memset(due_group, 0, sizeof due_group);
    for (i = 0; i < klk_lv.nscene; i++) {
        struct klk_scene *sc = &klk_lv.sc[i]; float trig = -1; struct klk_here hs;
        if (klk_r.done[sc->group] || klk_r.sc_state[i]) continue;
        klk_scene_here(&w, sc, &h, &hs);
        switch (sc->when) {
        case KLK_W_START: trig = sc->delay + klk.start_offset; if (trig < 0) trig = 0; break;
        case KLK_W_STAGE1: case KLK_W_STAGE2: case KLK_W_STAGE3: if (klk_r.ev_stage[sc->when - KLK_W_STAGE1 + 1] >= 0) trig = klk_r.ev_stage[sc->when - KLK_W_STAGE1 + 1] + sc->delay; break;
        case KLK_W_ABOARD: if (klk_r.ev_aboard >= 0) trig = klk_r.ev_aboard + sc->delay; break;
        case KLK_W_JOIN: if (klk_r.ev_join >= 0) trig = klk_r.ev_join + sc->delay; break;
        case KLK_W_BOX:
            if (klk_r.box_at[i] < 0 && have_feet && rt >= sc->not_before && feet[0] >= sc->box[0] && feet[0] <= sc->box[1] && feet[1] >= sc->box[2] && feet[1] <= sc->box[3] && feet[2] >= sc->box[4] && feet[2] <= sc->box[5]) {
                klk_r.box_at[i] = rt;
                if (klk.log > 1) klog("talk: the player is in the box of scene %s at %.2f s (%.0f, %.0f, %.0f)", sc->name, rt, feet[0], feet[1], feet[2]);
            }
            if (klk_r.box_at[i] >= 0) trig = klk_r.box_at[i] + sc->delay;
            break;
        }
        if (trig < 0 || rt < trig) continue;
        if (!klk_needs_hold(sc->needs, &hs)) { due_group[sc->group] = 1; continue; }      /* the next alternative of this Name may hold */
        klk_r.done[sc->group] = 1; due_group[sc->group] = 0;
        klk_r.sc_state[i] = 1; klk_r.sc_t0[i] = rt; klk_r.sc_next[i] = 0;
        klog("talk: scene %s (Needs=%s%s) starts at %.2f s: %s", sc->name, klk_needs_name[sc->needs], sc->cast_k || sc->cast_l ? ", cast" : "", rt, klk_who_text(&w, &hs, who));
    }
    for (i = 0; i < klk_lv.nscene; i++) if (due_group[i] && !klk_r.done[i]) {            /* due, and no alternative's Needs hold: over for the round */
        klk_r.done[i] = 1;
        klog("talk: nothing for '%s' at %.2f s: %s", klk_lv.sc[i].name, rt, klk_who_text(&w, &h, who));
    }

    /* ---- the lines of the scenes that run (one line a tick) */
    for (i = 0; i < klk_lv.nscene; i++) {
        struct klk_scene *sc = &klk_lv.sc[i]; struct klk_line *l; int rec; struct klk_here hs; char who_nm[24];
        if (klk_r.sc_state[i] != 1) continue;
        busy = 1;
        l = &sc->l[klk_r.sc_next[i]];
        if (rt < klk_r.sc_t0[i] + l->at) continue;
        klk_scene_here(&w, sc, &h, &hs);
        if (l->who == KLK_NAME) snprintf(who_nm, sizeof who_nm, "character %d", l->ch); else strcpy(who_nm, l->who == KLK_KANE ? "Kane" : "Lynch");
        rec = l->who == KLK_KANE ? hs.kane : l->who == KLK_LYNCH ? hs.lynch : (j = klk_member_ch(&w, l->ch)) >= 0 ? w.m[j].rec : -1;
        if (rec < 0) {
            klk_r.sc_state[i] = 2;
            klog("talk: scene %s dropped at line %d of %d: %s is no longer there", sc->name, klk_r.sc_next[i] + 1, sc->nlines, who_nm);
            continue;
        }
        snprintf(what, sizeof what, "%s = record %d; scene %s line %d of %d", who_nm, rec, sc->name, klk_r.sc_next[i] + 1, sc->nlines);
        klk_say(l->key, rec, rt, what, w.rules, scene);
        klk_mark_said(klk_hash(l->key));
        klk_r.last_scene_line = rt; if (rec < KLW_NREC) klk_r.member_last[rec] = rt;
        if (++klk_r.sc_next[i] >= sc->nlines) klk_r.sc_state[i] = 2;
        break;
    }

    /* ---- the fed (Who=Fed pools; nothing unless the file has them) */
    if (w.state == KLK_ROUND) klk_fed_tick(&w, rt, busy, scene);

    /* ---- chatter */
    if (!klk.chatter || (!klk_lv.npool && !klk_lv.npair)) return;
    if (klk_r.reply.on && rt >= klk_r.reply.at) {                             /* the answer of a pair */
        int ri = -1;
        for (i = 0; i < w.n; i++) if (w.m[i].rec == klk_r.reply.rec) ri = i;
        klk_r.reply.on = 0;
        if (ri >= 0 && w.m[ri].status == 0 && !busy) klk_chatter_say(&w, ri, klk_r.reply.key, "pair, the reply", rt, w.rules, scene, 1);
        return;
    }
    score = klh_rd32(w.rules + 0x5f8);
    for (i = 0; i < w.n; i++) {                                              /* what changed since the last tick -> at most one event line */
        int rec = w.m[i].rec, ev = 0, self = 1, dead_ev = 0; DWORD money = 0; BYTE st = 0, fl = 0;
        if (rec < 0 || rec >= KLW_NREC) continue;
        if (score) klh_rd(score + 0x150 + 4 * rec, &money, 4);
        klh_rd(w.m[i].at + 0x78, &st, 1); klh_rd(w.m[i].at + 0x79, &fl, 1);
        if (klk_r.known[rec]) {
            if (w.m[i].status == 7 && klk_r.status[rec] != 7) { ev = KLK_ON_DOWN; dead_ev = 1; self = 0; if (!klk_r.shooting && klk_has_pool(KLK_ON_SHOOT)) ev = KLK_ON_SHOOT; }      /* the first death = shooting has begun (GUESS: no fire flag of the AI is known); review: 'shooting' is set only once the line was really chosen, else a quiet-gap or chance skip would use the one chance up */
            else if ((fl & 2) && !(klk_r.flags[rec] & 2)) { ev = !klk_has_pool(KLK_ON_TRAITOR) && klk_has_pool(KLK_ON_SHOOT) ? KLK_ON_SHOOT : KLK_ON_TRAITOR; self = 0; }
            else if (st >= 2 && klk_r.stage[rec] < 2) ev = KLK_ON_STAGE2;
            else if (money > klk_r.money[rec]) ev = KLK_ON_MONEY;
        }
        klk_r.known[rec] = 1; klk_r.money[rec] = money; klk_r.status[rec] = w.m[i].status; klk_r.stage[rec] = st; klk_r.flags[rec] = fl;
        if (!ev || busy || rt - klk_r.last_scene_line < klk_lv.quiet || rt - klk_r.last_chatter < klk_lv.quiet) continue;
        if ((int)klk_rnd(100) >= klk_lv.event_chance) continue;
        if (self) j = klk_may_chatter(&w, i, rt) ? i : -1;
        else {                                                               /* another member speaks: the first that may, from a random start */
            int s0 = (int)klk_rnd((DWORD)w.n), k;
            for (j = -1, k = 0; k < w.n && j < 0; k++) { int c = (s0 + k) % w.n; if (c != i && klk_may_chatter(&w, c, rt)) j = c; }
        }
        if (j >= 0) {
            int got = klk_pool_key(&w, j, ev, w.rules, ckey, &pool);
            if (!got && ev == KLK_ON_SHOOT && dead_ev) { ev = KLK_ON_DOWN; got = klk_pool_key(&w, j, ev, w.rules, ckey, &pool); }      /* review: the first death must not lose its Down line when no Shoot key fits */
            if (got) { klk_chatter_say(&w, j, ckey, pool, rt, w.rules, scene, 0); busy = 1; if (ev == KLK_ON_SHOOT) klk_r.shooting = 1; }
        }
    }
    if (!klk_r.won && w.n >= 2 && klk_has_pool(KLK_ON_WON)) {                 /* everybody who played the round is down: the line of the winners (GUESS: the game may already have left state 0x19) */
        int alive = 0, dead = 0, c = w.human >= 0 ? w.human : 0;
        for (i = 0; i < w.n; i++) { if (w.m[i].status == 0 || w.m[i].status == 1 || w.m[i].status == 4 || w.m[i].status == 5 || w.m[i].status == 6) alive++; else if (w.m[i].status == 7) dead++; }
        if (!alive && dead >= 2) {
            klk_r.won = 1;
            if (klk_pool_key(&w, c, KLK_ON_WON, w.rules, ckey, &pool)) klk_chatter_say(&w, c, ckey, pool, rt, w.rules, scene, 0);
            else klog("talk: all down at %.2f s but no Won key fits record %d", rt, w.m[c].rec);
        }
    }
    if (busy || rt < klk_r.next_idle || rt - klk_r.last_scene_line < klk_lv.quiet || rt - klk_r.last_chatter < klk_lv.quiet) return;
    klk_r.next_idle = rt + klk_lv.gap_lo + (float)klk_rnd((DWORD)((klk_lv.gap_hi - klk_lv.gap_lo) * 10) + 1) / 10;
    if (klk_lv.npair && (int)klk_rnd(100) < klk_lv.pair_chance) {              /* a call and an answer between any two characters that are there (V4) */
        int s0 = (int)klk_rnd((DWORD)klk_lv.npair), k;
        for (k = 0; k < klk_lv.npair; k++) {
            struct klk_pair *p = &klk_lv.pair[(s0 + k) % klk_lv.npair]; int ci, ri;
            if (!p->cwho || !p->rwho) continue;
            ci = klk_pair_member(&w, &h, p->cwho, p->cch); ri = klk_pair_member(&w, &h, p->rwho, p->rch);
            if (ci < 0 || ri < 0 || ci == ri || !klk_may_chatter(&w, ci, rt) || !klk_may_chatter(&w, ri, rt)) continue;
            if (klk_blocked(klk_hash(p->call)) || klk_blocked(klk_hash(p->reply))) continue;
            klk_chatter_say(&w, ci, p->call, "pair, the call", rt, w.rules, scene, 0);
            klk_r.reply.on = 1; klk_r.reply.rec = w.m[ri].rec; klk_r.reply.at = rt + p->wait; strcpy(klk_r.reply.key, p->reply);
            return;
        }
    }
    {
        int s0 = (int)klk_rnd((DWORD)w.n), k;
        for (k = 0; k < w.n; k++) {
            int c = (s0 + k) % w.n;
            if (!klk_may_chatter(&w, c, rt) || !klk_pool_key(&w, c, KLK_ON_IDLE, w.rules, ckey, &pool)) continue;
            klk_chatter_say(&w, c, ckey, pool, rt, w.rules, scene, 0);
            return;
        }
    }
}

static void klk_init(void)
{
    char t[32]; LARGE_INTEGER q; int fresh = 0;
    memset(&klk, 0, sizeof klk); memset(&klk_lv, 0, sizeof klk_lv); memset(&klk_r, 0, sizeof klk_r); memset(&klk_gen, 0, sizeof klk_gen);
    klk.on = GetPrivateProfileIntA("Talk", "Enable", 0, klh_ini) != 0;
    klk.log = (int)GetPrivateProfileIntA("Talk", "Log", 1, klh_ini);
    klk.chatter = GetPrivateProfileIntA("Talk", "Chatter", 1, klh_ini) != 0;
    klk.logonly = GetPrivateProfileIntA("Talk", "LogOnly", 0, klh_ini) != 0;
    klk.stock = GetPrivateProfileIntA("Talk", "StockLevels", 0, klh_ini) != 0;
    GetPrivateProfileStringA("Talk", "StartOffset", "0", t, sizeof t, klh_ini); klk.start_offset = (float)atof(t);
    if (!(klk.start_offset > -60 && klk.start_offset < 60)) klk.start_offset = 0;
    klk.seed = GetPrivateProfileIntA("Talk", "Seed", 0, klh_ini);
    if (!klk.on) return;
    if (!klk.seed) { QueryPerformanceCounter(&q); klk.seed = GetTickCount() ^ (DWORD)q.LowPart ^ (GetCurrentProcessId() << 12); if (!klk.seed) klk.seed = 1; fresh = 1; }
    klk_rng = klk.seed;
    klog("talk: on; Kane / Lynch scenes and chatter on a level with a KLTalk.ini beside its archive: Chatter=%d StartOffset=%.2f LogOnly=%d Seed=%lu%s Log=%d; Arcade only, %s",
         klk.chatter, klk.start_offset, klk.logonly, klk.seed, fresh ? " (taken new)" : "", klk.log, klk.stock ? "a stock level too if a KLTalk.ini sits beside it (StockLevels=1)" : "never on a stock level");
    if (!klc_on) klog("talk: [Character] Enable=0, so no KLWardrobe.ini is read and nobody can be told to wear Kane or Lynch: nothing will be said");
}

#endif /* KLTALK_C */
