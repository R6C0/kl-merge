/* ==================== squad.inc: Dead Men crew orders in Dog Days (Follow / Fire at / Defend) ====================
   Included by anp_loader.c after climb.inc (uses anp_log, readable, rtti_name, node_table, g_dir, g_cscene and climb.inc's
   climb_guarded, cl_ray, cl_pose, cl_sys, cl_curT). Ticked once per gameplay frame from climb.inc's frame hook
   (anp_rcb_pre, kl2's IAT slot for steam_api!SteamAPI_RunCallbacks, return address 0x87aa82, main thread).

   CEG: no kl2 code byte is changed. Everything here is calls into kl2 functions, reads, and heap writes
   (sc+0x08 order counter, sc+0xa0 refusal flag in M01). Every engine call runs inside climb_guarded() and through
   sq_call_raw(), which checks the stack pointer after the call; a fault or a stack mismatch disables the module for the
   session ("SQUAD DISABLED"). Only active in ANP levels (campaign.inc's scene id "M<digit>..."); silent elsewhere.

   DD engine entry points used (static RE of kl2.exe; prologue bytes are checked before the first call):
     0x4c3900 ZSquadControl::Follow(sc, char all)      native DD port of DM 0x613bc0 (busy, refusal, signal 7, voice 0x31)
     0x5d3010 ZSquadControl::SelectNext(sc, char prev) posts DD's own type-2 marker
     0x6c8510 ZSquadControl::CanReceive(sc, script)    dead / squad / script+0x6a4 / body+0x576
     0x6eac60 ZSquadControl::Refuse(sc, gesture, voice) Kane's signal, nearest merc turns and speaks
     0x6a88f0 player busy (flag 0x40000 at +0x438, or player state 2..13 except 10)
     0x742320 [P+0x840] signal(gesture)                 7 follow, 8 attack, 6 defend
     0x824c80 player look-at(body, 1.5, 2.0, 2)
     0x763db0 [script+0x564] speak(id)
     0x7b3020 node local->world point (node = body+4)
     0x8ccde0 handle -> object (cdecl)
     0x86ca10 object -> handle ([0xe0ff90], obj): gen * cap + node index + 1 (what 0x6ece90 wraps)
     ZSoldier@CPPScript (vt 0xbd0954) slot 79 vt+0x13c = 0x760e50 MoveTo(const float pos[3], char a, char clear, int)
                                      slot 83 vt+0x14c = 0x831850 Attack(DWORD tgtHandle_or_0, const float pos[3], float T)
                                      (the first argument is a HANDLE: 0x831850 resolves it with 0x8ccde0 and keeps the
                                      object at script+0x720; DD's network path 0x6f64f9 passes the streamed handle)
     markers (markers=1 only): 0x7be580 record(rec, body, type, float dur, playerIdx), 0x8b57a0([gm+0x15e0], rec)
     recruitment (mode on, recruit=1): 0x908040 ZSquadControl::Recruit(sc, Body*) ret 4 = the port of DM 0x613690
                                      (sc+0xcc = 1; script slot 108 0x4c3b10 SetOwner(player handle): +0x69c, follow slot 80;
                                      receivers sc+0x1c[sc+0x18] (max 16, NO duplicate check); 0x7b3490 adds to the player
                                      squad sc+0xa4 (sets script+0x4f4, body+0x680)). DD calls it only in a hosted session; in
                                      story mode (no session) its soldier init 0x615c90 gives the buddy (merc 1) only the follow
                                      call, so Lynch is never in the player's control. squad.inc does the recruit itself.
                                      recruit_detach=1 only: 0x5230c0 ZSquad::RemoveMember(oldSquad, script) ret 4 first.
                                      Merc list: [0x1548fd8] count, 0x1548fdc[16] scripts (filled by 0x615c90 for merc != 0).
   Objects: P = local ZFFPlayer, sc = *(P+0xcd0) (sc+4 == P), squad = *(sc+0xa4) (+0xc0 count, +0xc4[12] members),
     receivers sc+0x18 count / sc+0x1c[], current sc+0x10, refusal flag sc+0xa0, order counter sc+8.
     script: +0x40 body, +0x4f4 squad, +0x69c owner player, +0x6a4 commandable, +0x6e8 EIsMercenary (1 = DD 'Kane'
     buddy = DM Lynch); body: +4 node (+0x6c name), +0x54 -> +4 relation (crosshair: 0/2 friendly), +0x576 able,
     +0x77c script. Aim: P+0x27b0 = aim point (written every frame by 0x4677c0), [P+0xbd4]+0x2ac = aim target handle.

   Config: <DD>\ANP_squad.txt (polled once a second; absent = probe). Tokens, space or line separated; a bare first
   token may be the mode:
     mode=off|probe|dry|on   probe (default): read only, logs probe/stat/key/cmd lines, dispatches nothing
                             dry: input + command machine, gates, receivers, aim and targets resolved; no order is given
                             on: orders are given through the engine functions above
     input=dd|async|off      key source: DD's own DirectInput device state (default; falls back to GetAsyncKeyState)
     follow=0x02 attack=0x03 defend=0x04 next=0x0f prev=0 (0 = Shift+next) mouse_attack=2 (-1 = none)   DIK codes
     attack_time=5.0         slot 83 time argument (seconds)
     refuse=auto|0|1         auto: sc+0xa0 = 1 in M01 (DM's M01A rule: every order is refused by Lynch)
     ack_follow=0x22 ack_attack=0x23 ack_defend=0x21 nolos_voice=0x2e   answer speech ids (0 = none)
     ref_follow=0x30 ref_attack=0x2f ref_defend=0x2e                    refusal speech ids for 0x6eac60 (0 = none)
     dd_follow_voice=mute|keep  mute (default): DD's Follow hard-codes its own ack 0x31, which is Lynch HUMMING in Dead
                             Men's banks; it is blocked for the length of the Follow call (team-0 cooldown entry 0x31,
                             saved and restored) and ack_follow is spoken instead
   Speech ids (both exes): speak(id) = DD 0x763db0 -> 0x7ca290 -> 0x465c10 (DM 0x7275f0 -> 0x727550 -> 0x6e59a0). The id is
   a raw index: (1) into the speaker team's cooldown table (Audio::Project::IControlTeamTemplate<0>, DD [0xdd25d4], 63
   entries, has(id) = id < 0x3f at 0x5b4ce0; police use template<1>, 35 entries), then (2) into the speaker's own .SND
   type-5 sound list ("...#def", bound by the actor property after the anmcol: string), 0x900ff0: id >= count -> NULL ->
   silent. No name table exists in either exe; the names are the .SND set names. ANP levels keep Dead Men's .SND
   unchanged (same record offsets, same list order), so the right ids here are DEAD MEN's ids, not DD's:
     0x21 gothere (defend ack)   0x22 followme (follow ack)   0x23 shootatmymark (attack ack)
     0x2e deny_move (defend refusal, defend no-LOS)   0x2f deny_fire (attack refusal)   0x30 deny_regroup (follow refusal)
     0x31 lynchhumming   0x35 lynchdenyplayercommand (DM: Lynch busy in his mutter state; DD has no such state, unused)
   Lynch = little#def (55 entries, every id above filled; M05 little_m05#def: level-specific go/follow lines, no
   refusals). Other mercs (mercenary_01, carlos, lion, flame, shelly, thapa, rific, vaultbreaker, soldier01/02, daughter:
   49 entries) have 0x21..0x23 and, except the M01 mercs, empty 0x2e..0x30 (silent, as in Dead Men). Stock DD banks have
   no order lines at all (lynch_default#def 42 entries, kane_default#def 0x2e..0x39 empty): DD's own Follow ids (ack
   0x31, refusal 0x2f) have no Dog Days line to map to. A refusal voice of 0 is passed as 0xff (has() false: silent),
   because 0x6eac60 always speaks and id 0 is the pain line.
     markers=0|1             post world markers (attack: type 0xa on the target, defend: type 7 over each merc)
     release=follow|moveto   moveto: a merc still holding 2 s after Follow gets MoveTo(player) + Follow(all)
     stat=5                  'SQUAD stat' interval in seconds (0 = off)
     recruit=1               mode on: every living merc soldier (EIsMercenary 1..13; DM Merc_xx, buddy 'Kane' = Lynch = 1)
                             not yet in the player's squad control is recruited with 0x908040 (1 s after the player /
                             squad control appears, outside cutscenes; again after a respawn or reload). dry: logged only
     recruit_detach=0        1: remove the merc from his level squad (0x5230c0) before the recruit (DD's own path keeps it)
     critical=keep|clear     keep (default): untouched. clear (any mode but off, ANP levels, build check ok): a friendly merc's
                             death no longer fails the mission. DD's soldier init 0x615c90 calls ZSoldier@CPPScript slot 57
                             (vt+0xe4 = 0x725b20, which writes byte +0x513 unless body+0x54 -> +4 relation == 1) with 1 and sets
                             +0x512 = 1 for every merc (+0x6e8 != 0) before it appends him to the merc list (0x7175a0 on
                             0x1548fd8: [count], [16] scripts). On death slot 56 0x8fd470 -> 0x6d2500 calls slot 58 (vt+0xe8 =
                             0x8f44a0: mov al,[ecx+0x513]); non-zero -> the 'MercDead' Ingame message + mission-fail reload.
                             A checkpoint load restores +0x513 from the save (0x5bf577). So a pass sets BYTE [s+0x513] = 0 on
                             every listed merc script (+0x512 left alone) after each scene load (level reset: new player, new
                             scene, clock back), after each change of the game-state counter [0xe0e644] (inc by 0x65a4fd /
                             0x5d5de7), and when the once-a-second check finds a listed merc with +0x513 set (late spawns).
                             Data writes only (heap); no code byte. The stat line's crit= counts listed mercs with +0x513 set.
   Test commands: <DD>\ANP_squad_cmd.txt, consumed (renamed to ANP_squad_cmd.done) on the main thread, one line per frame:
     follow tap|hold | attack tap|hold [aim | x y z | node N | nearest] | defend tap|hold [aim | x y z]
     next | prev | state | wait S
   Keys (dry/on, kl2 in the foreground): tap (< 0.25 s, fires on release) = the selected receiver, hold (fires at 0.25 s)
   = every eligible merc. 1 Follow, 2 / middle mouse Fire at, 3 Defend, Tab next receiver, Shift+Tab previous.
   Log lines start with "SQUAD ". */

#define SQ_PLAYER_VT   0xbb45f4
#define SQ_SCRIPT_VT   0xbd0954
#define SQ_KB_VT       0xb8f4dc
#define SQ_MOUSE_VT    0xb8f564
#define SQ_F_FOLLOW    0x4c3900
#define SQ_F_CYCLE     0x5d3010
#define SQ_F_CANRECV   0x6c8510
#define SQ_F_REFUSE    0x6eac60
#define SQ_F_BUSY      0x6a88f0
#define SQ_F_SIGNAL    0x742320
#define SQ_F_LOOKAT    0x824c80
#define SQ_F_SPEAK     0x763db0
#define SQ_F_NODEPOS   0x7b3020
#define SQ_F_HANDLE    0x8ccde0
#define SQ_F_OBJHANDLE 0x86ca10
#define SQ_F_MARKREC   0x7be580
#define SQ_F_MARKADD   0x8b57a0
#define SQ_F_MOVETO    0x760e50
#define SQ_F_ATTACK    0x831850
#define SQ_F_RECRUIT   0x908040
#define SQ_F_SETOWNER  0x4c3b10     /* ZSoldier@CPPScript slot 108 (vt+0x1b0), called by 0x908040 */
#define SQ_F_ADDSQUAD  0x7b3490     /* called by 0x908040 */
#define SQ_F_SQREMOVE  0x5230c0
#define SQ_MERC_LIST   0x1548fd8
#define SQ_NET_MGR     0x168e598
#define SQ_TAP_T       256         /* 0.25 s in engine time units (1024 per second) */
#define SQ_F_TEAM0     0x82b340    /* ZSingleton2<IControlTeamTemplate<0>>::Get() (no args, plain ret), object at [0xdd25d4] */
#define SQ_TEAM0_PTR   0xdd25d4
#define SQ_TEAM0_VT    0xbcc37c    /* +0 vtable, +4 0xb53f70, +0x14 + 12*id: {float interval, float last, byte} (0x82fc90) */
#define SQ_TEAM0_VT2   0xb53f70
#define SQ_DD_FOLLOW_VOICE 0x31    /* pushed by 0x4c3900 at 0x4c3af5 */
#define SQ_VOICE_NONE  0xff        /* >= 0x3f: the team's has(id) fails, nothing is spoken */

enum { SQ_OFF, SQ_PROBE, SQ_DRY, SQ_ON };
static const char *const SQ_MODE[] = {"off", "probe", "dry", "on"};
enum { SQO_NONE, SQO_FOLLOW, SQO_ATTACK, SQO_DEFEND };
static const char *const SQ_ORD[] = {"-", "follow", "attack", "defend"};
enum { SQS_AIM, SQS_XYZ, SQS_NODE, SQS_NEAREST };

typedef struct {
    int mode, input, markers, refuse, stat, release;
    float attackT;
    int kFollow, kAttack, kDefend, kNext, kPrev, mAttack;
    int ackA, ackD, refA, refD, nolos;
    int recruit, detach;
    int ackF, refF, ddFollowVoice;                    /* ddFollowVoice: 0 mute DD's 0x31 during Follow, 1 keep */
    int critClear;                                    /* critical=: 0 keep, 1 clear script+0x513 on listed mercs */
} SqCfg;
/* voices: Dead Men's ids (see the header): acks attack 0x23 defend 0x21 follow 0x22, refusals attack 0x2f defend 0x2e
   follow 0x30, defend no-LOS 0x2e */
#define SQ_CFG_DEFAULT {SQ_PROBE, 1, 0, -1, 5, 0, 5.0f, 0x02, 0x03, 0x04, 0x0F, 0, 2, 0x23, 0x21, 0x2f, 0x2e, 0x2e, 1, 0, 0x22, 0x30, 0, 0}
static SqCfg g_sqc = SQ_CFG_DEFAULT;
static int g_sqcPresent = -1; static FILETIME g_sqcTime; static DWORD g_sqcPoll;

static int g_sqDead, g_sqBuild = -1, g_sqLines;
static char g_sqScene[8];
static struct {
    BYTE *P, *sc; int lastT, hudT, hudSeen, probes, probeRecv, probeSq, refuseSet; DWORD t0, statT, cmdPoll, waitUntil;
    BYTE *kb, *mouse, *sys; int keySrc;               /* 0 none, 1 dd, 2 async */
    char scene[8];                                    /* scene of the last reset */
    DWORD recPoll, recWaitLog; int recScans, recWalked; /* recruitment scan state (per level / player) */
    const char *critWhy; DWORD critGs, critPoll; int critGsSeen; /* critical=clear: pending pass reason, last [0xe0e644] */
} g_sq;
typedef struct { BYTE *s; int tries, fails, dryLogged, unsafeLogged; DWORD lastT; } SqRec;
static SqRec g_sqRec[16];                             /* per merc script, reset with the level */
static BYTE *g_sqWalk[16]; static int g_sqWalkN;      /* mercs found by the one-off node walk (not in DD's merc list) */
static DWORD g_sqPlSq[8]; static int g_sqPlSqN;       /* player squads seen this session (old ones may be freed) */
static int sq_was_player_squad(DWORD q) { for (int i = 0; i < 8; i++) if (g_sqPlSq[i] == q) return 1; return 0; }
typedef struct { int down, t0, fired; } SqKey;
static SqKey g_sqK[3];
static int g_sqNextDown, g_sqPrevDown;
typedef struct { BYTE *s; int kind, T, relT; float pt[3]; BYTE *tgt; } SqOrd;
static SqOrd g_sqOrd[16];
static char g_sqQ[32][96]; static int g_sqQh, g_sqQn;

/* ---------- logging ---------- */
static void sq_log(const char *fmt, ...) {
    if (g_sqLines > 8000) return;
    if (++g_sqLines == 8000) { anp_log("SQUAD log line cap reached, SQUAD logging stops"); return; }
    char b[2400]; va_list ap; va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    anp_log("SQUAD %s", b);
}
static int sq_rate(DWORD *last, DWORD ms) { DWORD now = GetTickCount(); if (*last && now - *last < ms) return 0; *last = now ? now : 1; return 1; }
static void sq_cat(char *b, int cap, int *k, const char *fmt, ...) {
    if (*k >= cap - 1) return;
    va_list ap; va_start(ap, fmt); int n = _vsnprintf(b + *k, cap - 1 - *k, fmt, ap); va_end(ap);
    *k = (n < 0 || n >= cap - 1 - *k) ? cap - 1 : *k + n; b[*k] = 0;
}
static void sq_kill(const char *where, const char *why) {
    if (!g_sqDead) anp_log("SQUAD DISABLED for this session (%s in %s) - restart the game before testing again", why, where);
    g_sqDead = 1;
}

/* ---------- memory reads (4 cached committed regions; the cache is dropped at every tick) ---------- */
static DWORD g_sqRdLo[4], g_sqRdHi[4]; static int g_sqRdNext;
static void sq_rd_reset(void) { memset(g_sqRdLo, 0, sizeof g_sqRdLo); memset(g_sqRdHi, 0, sizeof g_sqRdHi); }
static int sq_rd(const void *p, DWORD n) {
    DWORD a = (DWORD)p;
    if (a < 0x10000 || a + n < a) return 0;
    for (int i = 0; i < 4; i++) if (a >= g_sqRdLo[i] && a + n <= g_sqRdHi[i]) return 1;
    MEMORY_BASIC_INFORMATION mi;
    if (!VirtualQuery(p, &mi, sizeof mi) || mi.State != MEM_COMMIT || !mi.Protect || (mi.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return 0;
    DWORD lo = (DWORD)mi.BaseAddress, hi = lo + (DWORD)mi.RegionSize;
    if (a + n > hi) return readable(p, n);
    g_sqRdLo[g_sqRdNext] = lo; g_sqRdHi[g_sqRdNext] = hi; g_sqRdNext = (g_sqRdNext + 1) & 3;
    return 1;
}
static DWORD rd32(const void *p) { return sq_rd(p, 4) ? *(const DWORD*)p : 0; }
static BYTE rd8(const void *p) { return sq_rd(p, 1) ? *(const BYTE*)p : 0; }
static float rdf(const void *p) { return sq_rd(p, 4) ? *(const float*)p : 0.0f; }
static DWORD fbits(float f) { DWORD d; memcpy(&d, &f, 4); return d; }
static int sq_code(DWORD f) { return f >= 0x401000 && f < 0xb10000; }   /* inside kl2's .text */

/* ---------- engine calls: push args, set ecx, call, check esp ---------- */
int g_sqEspDelta;                                     /* non-static: used from asm */
DWORD sq_call_raw(DWORD fn, void *self, int n, const DWORD *args, int callerPops);
__attribute__((naked, used)) static void sq_call_asm(void) { __asm__ volatile(
    ".p2align 4\n"
    ".globl _sq_call_raw\n"
    "_sq_call_raw:\n"
    "  pushl %ebp\n  movl %esp,%ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
    "  movl 16(%ebp),%ebx\n  movl 20(%ebp),%esi\n  movl %ebx,%eax\n"
    "1:\n  testl %eax,%eax\n  jz 2f\n  decl %eax\n  pushl (%esi,%eax,4)\n  jmp 1b\n"
    "2:\n  movl 12(%ebp),%ecx\n  call *8(%ebp)\n"
    "  movl %esp,%edx\n  leal -12(%ebp),%ecx\n  subl %ecx,%edx\n"   /* 0 when the callee popped its n args */
    "  cmpl $0,24(%ebp)\n  je 3f\n  leal (%edx,%ebx,4),%edx\n"       /* cdecl: the args are still on the stack */
    "3:\n  movl %edx,_g_sqEspDelta\n"
    "  leal -12(%ebp),%esp\n  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n"); }
static DWORD sq_call(const char *what, DWORD fn, void *self, int n, const DWORD *a, int cdecl_) {
    if (g_sqDead) return 0;
    g_sqEspDelta = 0;
    DWORD r = sq_call_raw(fn, self, n, a, cdecl_);
    if (g_sqEspDelta) {
        anp_log("SQUAD esp mismatch after %s (fn %08lx, delta %d)", what, fn, g_sqEspDelta);
        sq_kill(what, "stack mismatch");
    }
    return r;
}
static DWORD sq_call0(const char *what, DWORD fn, void *self) { return sq_call(what, fn, self, 0, NULL, 0); }
static DWORD sq_call1(const char *what, DWORD fn, void *self, DWORD a0) { DWORD a[1] = {a0}; return sq_call(what, fn, self, 1, a, 0); }

/* this kl2 build: prologue bytes of every function called directly (read-only check) */
static int sq_check_build(void) {
    static const struct { DWORD a; BYTE b[6]; } t[] = {
        {SQ_F_FOLLOW,  {0x83, 0xec, 0x24, 0x56, 0x8b, 0xf1}}, {SQ_F_CYCLE,   {0x83, 0xec, 0x6c, 0x53, 0x57, 0x8b}},
        {SQ_F_CANRECV, {0x56, 0x8b, 0x74, 0x24, 0x08, 0x57}}, {SQ_F_REFUSE,  {0x83, 0xec, 0x0c, 0x8b, 0x44, 0x24}},
        {SQ_F_BUSY,    {0xf7, 0x81, 0x38, 0x04, 0x00, 0x00}}, {SQ_F_SIGNAL,  {0x8b, 0x44, 0x24, 0x04, 0x56, 0x50}},
        {SQ_F_LOOKAT,  {0xd9, 0x44, 0x24, 0x0c, 0x53, 0x8b}}, {SQ_F_SPEAK,   {0x55, 0x8b, 0xec, 0x51, 0x8b, 0x01}},
        {SQ_F_NODEPOS, {0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c}}, {SQ_F_HANDLE,  {0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d}},
        {SQ_F_MARKREC, {0xd9, 0x44, 0x24, 0x0c, 0x8b, 0x44}}, {SQ_F_MARKADD, {0x53, 0x55, 0x56, 0x8b, 0x74, 0x24}},
        {SQ_F_MOVETO,  {0x55, 0x8b, 0xec, 0x83, 0xec, 0x0c}}, {SQ_F_ATTACK,  {0x55, 0x8b, 0xec, 0x51, 0x53, 0x56}},
        {SQ_F_OBJHANDLE, {0x8b, 0x44, 0x24, 0x04, 0x85, 0xc0}},
        {SQ_F_RECRUIT,  {0x83, 0xec, 0x0c, 0x55, 0x8b, 0x6c}}, {SQ_F_SETOWNER, {0x55, 0x8b, 0xec, 0x53, 0x56, 0x57}},
        {SQ_F_ADDSQUAD, {0x55, 0x8b, 0x6c, 0x24, 0x08, 0x56}}, {SQ_F_SQREMOVE, {0x55, 0x8b, 0xec, 0x51, 0x53, 0x56}},
        {SQ_F_TEAM0,    {0x6a, 0xff, 0x68, 0xcb, 0x81, 0xad}},
    };
    for (unsigned i = 0; i < sizeof t / sizeof t[0]; i++)
        if (!readable((void*)t[i].a, 6) || memcmp((void*)t[i].a, t[i].b, 6)) { anp_log("SQUAD kl2 build mismatch at %08lx - orders off (probe/stat only)", t[i].a); return 0; }
    if (!readable((void*)(SQ_SCRIPT_VT + 0x14c), 4) || *(DWORD*)(SQ_SCRIPT_VT + 0x13c) != SQ_F_MOVETO || *(DWORD*)(SQ_SCRIPT_VT + 0x14c) != SQ_F_ATTACK) {
        anp_log("SQUAD ZSoldier@CPPScript vtable slots 79/83 differ - orders off"); return 0;
    }
    if (!readable((void*)(SQ_SCRIPT_VT + 0x1b0), 4) || *(DWORD*)(SQ_SCRIPT_VT + 0x1b0) != SQ_F_SETOWNER) { anp_log("SQUAD ZSoldier@CPPScript vtable slot 108 differs - orders off"); return 0; }
    return 1;
}

/* ---------- config ---------- */
static int sq_num(const char *v) { return (int)strtol(v, NULL, 0); }
static void sq_cfg_poll(void) {
    DWORD now = GetTickCount();
    if (g_sqcPresent >= 0 && now - g_sqcPoll < 1000) return;
    g_sqcPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_squad.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_sqcPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_sqcTime) == 0)) return;
    g_sqcPresent = present;
    if (present) g_sqcTime = fa.ftLastWriteTime;
    SqCfg c = SQ_CFG_DEFAULT;
    char buf[1024] = ""; const char *note = present ? "" : " (no ANP_squad.txt: probe)";
    if (present) {
        FILE *f = fopen(fn, "r");
        if (f) { size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f); }
        else note = " (ANP_squad.txt unreadable)";
        for (char *p = buf; (p = strchr(p, '#')); ) while (*p && *p != '\n') *p++ = ' ';   /* comments */
        for (char *t = strtok(buf, " \t\r\n,;"); t; t = strtok(NULL, " \t\r\n,;")) {
            char *eq = strchr(t, '=');
            const char *k = t, *v = "";
            if (eq) { *eq = 0; v = eq + 1; }
            else { v = t; k = "mode"; }               /* a bare token is the mode */
            if (!_stricmp(k, "mode")) {
                int m = -1; for (int i = 0; i < 4; i++) if (!_stricmp(v, SQ_MODE[i])) m = i;
                if (m < 0) anp_log("SQUAD config mode '%s' unknown (kept %s)", v, SQ_MODE[c.mode]); else c.mode = m;
            }
            else if (!_stricmp(k, "input")) c.input = !_stricmp(v, "off") ? 0 : !_stricmp(v, "async") ? 2 : 1;
            else if (!_stricmp(k, "markers")) c.markers = sq_num(v) != 0;
            else if (!_stricmp(k, "refuse")) c.refuse = !_stricmp(v, "auto") ? -1 : sq_num(v) != 0;
            else if (!_stricmp(k, "stat")) c.stat = sq_num(v) < 0 ? 0 : sq_num(v);
            else if (!_stricmp(k, "release")) c.release = !_stricmp(v, "moveto");
            else if (!_stricmp(k, "attack_time")) { c.attackT = (float)atof(v); if (!(c.attackT > 0.0f && c.attackT < 120.0f)) c.attackT = 5.0f; }
            else if (!_stricmp(k, "follow")) c.kFollow = sq_num(v) & 0xff;
            else if (!_stricmp(k, "attack")) c.kAttack = sq_num(v) & 0xff;
            else if (!_stricmp(k, "defend")) c.kDefend = sq_num(v) & 0xff;
            else if (!_stricmp(k, "next")) c.kNext = sq_num(v) & 0xff;
            else if (!_stricmp(k, "prev")) c.kPrev = sq_num(v) & 0xff;
            else if (!_stricmp(k, "mouse_attack")) c.mAttack = sq_num(v) < 0 || sq_num(v) > 7 ? -1 : sq_num(v);
            else if (!_stricmp(k, "ack_follow")) c.ackF = sq_num(v) & 0xff;
            else if (!_stricmp(k, "ack_attack")) c.ackA = sq_num(v) & 0xff;
            else if (!_stricmp(k, "ack_defend")) c.ackD = sq_num(v) & 0xff;
            else if (!_stricmp(k, "ref_follow")) c.refF = sq_num(v) & 0xff;
            else if (!_stricmp(k, "ref_attack")) c.refA = sq_num(v) & 0xff;
            else if (!_stricmp(k, "ref_defend")) c.refD = sq_num(v) & 0xff;
            else if (!_stricmp(k, "nolos_voice")) c.nolos = sq_num(v) & 0xff;
            else if (!_stricmp(k, "dd_follow_voice")) c.ddFollowVoice = !_stricmp(v, "keep") || (v[0] >= '1' && v[0] <= '9');
            else if (!_stricmp(k, "recruit")) c.recruit = sq_num(v) != 0;
            else if (!_stricmp(k, "recruit_detach")) c.detach = sq_num(v) != 0;
            else if (!_stricmp(k, "critical")) {
                if (!_stricmp(v, "clear")) c.critClear = 1;
                else if (!_stricmp(v, "keep")) c.critClear = 0;
                else anp_log("SQUAD config critical '%s' unknown (keep|clear; kept %s)", v, c.critClear ? "clear" : "keep");
            }
            else if (!_stricmp(k, "hud") || !_stricmp(k, "pad")) anp_log("SQUAD config '%s' is not in this build (HUD / pad come later)", k);
            else anp_log("SQUAD config key '%s' unknown", k);
        }
    }
    g_sqc = c;
    static const char *in[] = {"off", "dd", "async"};
    anp_log("SQUAD config mode=%s input=%s keys follow=%02x attack=%02x defend=%02x next=%02x prev=%s%02x mouse_attack=%d attack_time=%.1f "
            "refuse=%s markers=%d release=%s stat=%d ack(f/a/d)=%x/%x/%x ref(f/a/d)=%x/%x/%x nolos=%x dd_follow_voice=%s recruit=%d recruit_detach=%d critical=%s%s",
            SQ_MODE[c.mode], in[c.input], c.kFollow, c.kAttack, c.kDefend, c.kNext, c.kPrev ? "" : "shift+", c.kPrev ? c.kPrev : c.kNext,
            c.mAttack, (double)c.attackT, c.refuse < 0 ? "auto" : c.refuse ? "1" : "0", c.markers, c.release ? "moveto" : "follow", c.stat,
            c.ackF, c.ackA, c.ackD, c.refF, c.refA, c.refD, c.nolos, c.ddFollowVoice ? "keep" : "mute", c.recruit, c.detach,
            c.critClear ? "clear" : "keep", note);
}

/* ---------- objects ---------- */
static int sq_anp_level(void) { return g_sqScene[0] == 'M' && g_sqScene[1] >= '0' && g_sqScene[1] <= '9'; }
static BYTE *sq_player(void) {
    BYTE *gm = (BYTE*)rd32((void*)0xdd265c);
    if (!sq_rd(gm + 0x828, 0x74)) return 0;
    signed char pi = *(signed char*)(gm + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gm + 0x828 + 4 * pi);
    return (sq_rd(P, 0x2e00) && *(DWORD*)P == SQ_PLAYER_VT) ? P : 0;
}
static BYTE *sq_sc_of(BYTE *P) { BYTE *sc = (BYTE*)rd32(P + 0xcd0); return (sq_rd(sc, 0xb8) && *(BYTE**)(sc + 4) == P) ? sc : 0; }
static BYTE *sq_squad(BYTE *sc) { BYTE *s = (BYTE*)rd32(sc + 0xa4); return sq_rd(s, 0xc4 + 48) ? s : 0; }
static int sq_script(BYTE *s) { return sq_rd(s, 0x6f0) && *(DWORD*)s == SQ_SCRIPT_VT && sq_rd((BYTE*)rd32(s + 0x40), 0x780); }
static BYTE *sq_bodyof(BYTE *s) { return (BYTE*)rd32(s + 0x40); }
static int sq_nrecv(BYTE *sc) { int n = (int)rd32(sc + 0x18); return n < 0 ? 0 : n > 16 ? 16 : n; }
static int sq_nmem(BYTE *sq) { int n = sq ? (int)rd32(sq + 0xc0) : 0; return n < 0 ? 0 : n > 12 ? 12 : n; }
static BYTE *sq_cur(BYTE *sc) {                       /* 0x54a150, as reads */
    DWORD cur = rd32(sc + 0x10), end = (DWORD)(sc + 0x1c + 4 * sq_nrecv(sc));
    return (cur >= (DWORD)(sc + 0x1c) && cur < end) ? (BYTE*)rd32((void*)cur) : 0;
}
static int sq_cur_idx(BYTE *sc) { DWORD cur = rd32(sc + 0x10); int i = (int)(cur - (DWORD)(sc + 0x1c)) / 4; return (cur >= (DWORD)(sc + 0x1c) && i < sq_nrecv(sc)) ? i : -1; }
static int sq_merc(BYTE *s) { return (int)rd32(s + 0x6e8); }
static void sq_name(BYTE *body, char *out, int n) {
    out[0] = 0;
    BYTE *node = (BYTE*)rd32(body + 4); const char *p = (const char*)rd32(node + 0x6c);
    if (!sq_rd(p, 1)) return;
    int k = 0; while (k < n - 1 && sq_rd(p + k, 1) && p[k] >= 32 && p[k] < 127) { out[k] = p[k]; k++; }
    out[k] = 0;
}
static int sq_rel(BYTE *body) { BYTE *o = (BYTE*)rd32(body + 0x54); return sq_rd(o + 4, 4) ? (int)*(DWORD*)(o + 4) : -1; }
static int sq_body_pos(BYTE *body, float *out) {     /* world point of the body node (0x7b3020 on body+4) */
    out[0] = out[1] = out[2] = 0;
    BYTE *node = (BYTE*)rd32(body + 4);
    if (!sq_rd(node, 0x60)) return 0;
    sq_call1("node pos", SQ_F_NODEPOS, node, (DWORD)out);
    return !g_sqDead;
}
static int sq_player_pos(BYTE *P, float *out) { float M[9]; out[0] = out[1] = out[2] = 0; return cl_pose(P, M, out); }
static int sq_canrecv(BYTE *sc, BYTE *s, int live) {
    if (!sq_script(s)) return 0;
    if (live) return (int)(sq_call1("can receive", SQ_F_CANRECV, sc, (DWORD)s) & 0xff);
    BYTE *b = sq_bodyof(s);                          /* 0x6c8510 without the dead check (vt+0x680) */
    return rd32(s + 0x4f4) == rd32(sc + 0xa4) && rd8(s + 0x6a4) && rd8(b + 0x576) == 1;
}
static int sq_hud_state(BYTE *P) { BYTE *st = (BYTE*)rd32(P + 0x2940); return sq_rd(st + 0x24, 4) ? (int)*(DWORD*)(st + 0x24) : -1; }
static int sq_busy(BYTE *P) {                         /* 0x6a88f0, as reads */
    int s = sq_hud_state(P);
    return (rd32(P + 0x438) & 0x40000) || (s >= 2 && s <= 13 && s != 10);
}
/* line of sight a -> b (mask 0x28, as climb's clearance rays): 1 clear, 0 blocked, -1 raycast unavailable */
static int sq_los(const float *a, const float *b, BYTE **hitObj) {
    ClRay ray; float seg[3] = {b[0] - a[0], b[1] - a[1], b[2] - a[2]}, pt[3];
    int h = cl_ray(a, seg, 0x28, &ray, pt);
    if (hitObj) *hitObj = (h == 1 && sq_rd(ray.node + 0x60, 4)) ? *(BYTE**)(ray.node + 0x60) : 0;
    return h < 0 ? -1 : !h;
}
static float sq_dist(const float *a, const float *b) { return v3dist(a, b); }

/* ---------- input: DD's own device state (ZSysInputWintel [0xddb958]) ---------- */
static void sq_find_devices(void) {
    BYTE *sys = (BYTE*)rd32((void*)0xddb958);
    g_sq.kb = g_sq.mouse = 0; g_sq.sys = sys;
    if (!sq_rd(sys, 0x94)) return;
    int n = (int)*(DWORD*)(sys + 0x90); if (n < 0 || n > 16) return;
    for (int i = 0; i < n; i++) {
        BYTE *d = (BYTE*)rd32(sys + 4 + 4 * i);
        if (!sq_rd(d, 0x34)) continue;
        if (*(DWORD*)d == SQ_KB_VT && !g_sq.kb) g_sq.kb = d;
        else if (*(DWORD*)d == SQ_MOUSE_VT && !g_sq.mouse) g_sq.mouse = d;
    }
}
static int sq_dev_down(BYTE *d, int idx) {
    if (!d || idx < 0) return 0;
    int n = (int)rd32(d + 0x30); BYTE *st = (BYTE*)rd32(d + 0x2c);
    return idx < n && idx < 512 && sq_rd(st + idx, 1) && st[idx] != 0;
}
static int sq_key(int dik) {
    if (!dik) return 0;
    if (g_sq.keySrc == 1) return sq_dev_down(g_sq.kb, dik);
    UINT vk = MapVirtualKeyA(dik, 3 /* MAPVK_VSC_TO_VK_EX */);
    if (dik == 0x0F) vk = VK_TAB;
    return vk && (GetAsyncKeyState(vk) & 0x8000);
}
static int sq_mouse(int idx) {
    if (idx < 0) return 0;
    if (g_sq.keySrc == 1) return sq_dev_down(g_sq.mouse, idx);
    static const int vk[8] = {VK_LBUTTON, VK_RBUTTON, VK_MBUTTON, VK_XBUTTON1, VK_XBUTTON2, 0, 0, 0};
    return vk[idx] && (GetAsyncKeyState(vk[idx]) & 0x8000);
}
static int sq_foreground(void) {
    HWND fw = GetForegroundWindow(); DWORD pid = 0;
    if (fw) GetWindowThreadProcessId(fw, &pid);
    return fw && pid == GetCurrentProcessId();
}

/* ---------- order records ---------- */
static SqOrd *sq_ord(BYTE *s, int make) {
    for (int i = 0; i < 16; i++) if (g_sqOrd[i].s == s) return &g_sqOrd[i];
    if (!make) return 0;
    for (int i = 0; i < 16; i++) if (!g_sqOrd[i].s) { memset(&g_sqOrd[i], 0, sizeof g_sqOrd[i]); g_sqOrd[i].s = s; return &g_sqOrd[i]; }
    return 0;
}
static void sq_record(BYTE *s, int kind, int T, const float *pt, BYTE *tgt) {
    SqOrd *o = sq_ord(s, 1); if (!o) return;
    int wasDefend = o->kind == SQO_DEFEND;
    float old[3]; memcpy(old, o->pt, 12);
    o->kind = kind; o->T = T; o->tgt = tgt; o->relT = 0;
    if (pt) memcpy(o->pt, pt, 12); else memset(o->pt, 0, 12);
    if (kind == SQO_FOLLOW && wasDefend) { o->relT = T + 2048; memcpy(o->pt, old, 12); }   /* release check in 2 s */
}

/* ---------- critical=clear: script+0x513 ("my death fails the mission", read by slot 58 0x8f44a0) ---------- */
#define SQ_CRIT_OFF    0x513
#define SQ_GS_COUNTER  0xe0e644                       /* game-state counter (cutdiag's n644) */
static BYTE *sq_merc_body(BYTE *s);
/* listed mercs (DD's merc list, i < 16, null skipped) that pass sq_merc_body (live soldier script, body in the node table) */
static int sq_crit_list(BYTE **out) {
    int nl = (int)rd32((void*)SQ_MERC_LIST), n = 0; if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (int i = 0; i < nl; i++) {
        BYTE *s = (BYTE*)rd32((void*)(SQ_MERC_LIST + 4 + 4 * i));
        if (s && sq_merc_body(s) && sq_rd(s + SQ_CRIT_OFF, 1)) out[n++] = s;
    }
    return n;
}
static int sq_crit_count(void) { BYTE *l[16]; int n = sq_crit_list(l), c = 0; for (int i = 0; i < n; i++) c += rd8(l[i] + SQ_CRIT_OFF) != 0; return c; }
static void sq_crit_pass(const char *why) {
    BYTE *l[16]; int n = sq_crit_list(l), cleared = 0, ro = 0, k = 0;
    int nl = (int)rd32((void*)SQ_MERC_LIST);
    char ids[160] = "";
    for (int i = 0; i < n; i++) {
        if (!rd8(l[i] + SQ_CRIT_OFF)) continue;
        if (!god_writable(l[i] + SQ_CRIT_OFF, 1)) { ro++; continue; }
        *(l[i] + SQ_CRIT_OFF) = 0;                    /* +0x512 stays as DD set it */
        cleared++;
        sq_cat(ids, sizeof ids, &k, "%s%d", k ? "," : " mercs=", sq_merc(l[i]));
    }
    sq_log("critical cleared n=%d (%s) listed=%d valid=%d%s%s gs=%lu", cleared, why, nl, n, ids, ro ? " (some not writable)" : "",
           rd32((void*)SQ_GS_COUNTER));
}
static void sq_crit_tick(void) {
    if (!g_sqc.critClear || g_sqBuild != 1) return;
    DWORD gs = rd32((void*)SQ_GS_COUNTER);
    if (!g_sq.critGsSeen) { g_sq.critGsSeen = 1; g_sq.critGs = gs; }
    else if (gs != g_sq.critGs) { g_sq.critGs = gs; if (!g_sq.critWhy) g_sq.critWhy = "state change"; }
    if (!g_sq.critWhy && sq_rate(&g_sq.critPoll, 1000) && sq_crit_count() > 0) g_sq.critWhy = "recheck";
    if (g_sq.critWhy) { const char *w = g_sq.critWhy; g_sq.critWhy = 0; sq_crit_pass(w); }
}

/* ---------- stat / probe ---------- */
static void sq_stat(BYTE *P, BYTE *sc, int T, const char *why) {
    BYTE *sq = sq_squad(sc); int nr = sq_nrecv(sc), nm = sq_nmem(sq);
    float pp[3]; sq_player_pos(P, pp);
    char b[2200]; int k = 0;
    sq_cat(b, sizeof b, &k, "stat%s%s scene=%s mode=%s keys=%s recv=%d sel=%d squad=%d a0=%d n8=%ld hud=%d busy=%d crit=%d |",
           why ? " " : "", why ? why : "", g_sqScene, SQ_MODE[g_sqc.mode], g_sq.keySrc == 1 ? "dd" : g_sq.keySrc == 2 ? "async" : "none",
           nr, sq_cur_idx(sc), nm, rd8(sc + 0xa0), (long)rd32(sc + 8), sq_hud_state(P), sq_busy(P), sq_crit_count());
    BYTE *list[28]; int n = 0;
    for (int i = 0; i < nm && n < 28; i++) list[n++] = (BYTE*)rd32(sq + 0xc4 + 4 * i);
    for (int i = 0; i < nr && n < 28; i++) {
        BYTE *s = (BYTE*)rd32(sc + 0x1c + 4 * i); int dup = 0;
        for (int j = 0; j < n; j++) dup |= list[j] == s;
        if (!dup) list[n++] = s;
    }
    BYTE *cur = sq_cur(sc);
    for (int i = 0; i < n; i++) {
        BYTE *s = list[i];
        if (!sq_script(s)) { sq_cat(b, sizeof b, &k, " [%d] %p(not a soldier script)", i, s); continue; }
        BYTE *body = sq_bodyof(s); char nm2[40]; sq_name(body, nm2, sizeof nm2);
        float bp[3]; sq_body_pos(body, bp);
        float a[3] = {pp[0], pp[1] + 160, pp[2]}, c[3] = {bp[0], bp[1] + 160, bp[2]};
        int los = sq_los(a, c, NULL);
        SqOrd *o = sq_ord(s, 0); BYTE *own = (BYTE*)rd32(s + 0x69c);
        sq_cat(b, sizeof b, &k, " [%d]%s m=%d '%s' ctl=%d able=%d own=%s elig=%d order=%s", i, s == cur ? "*" : "", sq_merc(s), nm2, rd8(s + 0x6a4),
               rd8(body + 0x576), own == P ? "P" : own ? "x" : "0", sq_canrecv(sc, s, 0), o ? SQ_ORD[o->kind] : "-");
        if (o && o->kind) sq_cat(b, sizeof b, &k, "/%.1fs", (T - o->T) / 1024.0f);
        if (o && o->kind == SQO_DEFEND) sq_cat(b, sizeof b, &k, " dpt=%.0f", sq_dist(bp, o->pt));
        sq_cat(b, sizeof b, &k, " d=%.0f los=%d atk720=%08lx", sq_dist(pp, bp), los, rd32(s + 0x720));
    }
    if (!n) sq_cat(b, sizeof b, &k, " (no squad members, no receivers)");
    sq_log("%s", b);
}

/* every soldier body in the node table (ZSoldier@CPPScript at body+0x77c whose +0x40 is the body) */
typedef struct { BYTE *body, *s; int merc, rel; } SqSol;
static int sq_soldiers(SqSol *out, int max) {
    DWORD stride, cap; BYTE *base; int n = 0;
    if (!node_table(&stride, &cap, &base) || stride < 0x64 || cap > 400000) return 0;
    for (DWORD i = 0; i < cap && n < max; i++) {
        BYTE *nd = base + i * stride;
        if (!sq_rd(nd + 0x60, 4)) break;
        BYTE *o = *(BYTE**)(nd + 0x60);
        if (!sq_rd(o, 0x780)) continue;
        BYTE *s = *(BYTE**)(o + 0x77c);
        if (!sq_rd(s, 0x6f0) || *(DWORD*)s != SQ_SCRIPT_VT || *(BYTE**)(s + 0x40) != o) continue;
        out[n].body = o; out[n].s = s; out[n].merc = sq_merc(s); out[n].rel = sq_rel(o); n++;
    }
    return n;
}
static long sq_node_idx(BYTE *obj) {
    DWORD stride, cap; BYTE *base;
    BYTE *node = (BYTE*)rd32(obj + 4);
    if (!node_table(&stride, &cap, &base) || !stride || node < base || node >= base + cap * stride || (DWORD)(node - base) % stride) return -1;
    return (long)((node - base) / stride);
}
static void sq_probe(BYTE *P, BYTE *sc, int T) {
    BYTE *sq = sq_squad(sc), *gm = (BYTE*)rd32((void*)0xdd265c);
    int nr = sq_nrecv(sc), nm = sq_nmem(sq);
    float pp[3], *aim = (float*)(P + 0x27b0); sq_player_pos(P, pp);
    BYTE *cam = (BYTE*)rd32(P + 0xbd4); DWORD h = rd32(cam + 0x2ac);
    sq_find_devices();
    sq_log("probe scene=%s P=%p sc=%p recv=%d cur=%p(%d) squad=%p members=%d a0=%d n8=%ld buddy(gm+4cf0)=%08lx input kb=%p/%ld mouse=%p/%ld "
           "aim=(%.0f,%.0f,%.0f) d=%.0f tgt=%08lx build=%s",
           g_sqScene, P, sc, nr, sq_cur(sc), sq_cur_idx(sc), sq, nm, rd8(sc + 0xa0), (long)rd32(sc + 8), rd32(gm + 0x4cf0),
           g_sq.kb, (long)rd32(g_sq.kb + 0x30), g_sq.mouse, (long)rd32(g_sq.mouse + 0x30),
           (double)rdf(aim), (double)rdf(aim + 1), (double)rdf(aim + 2), (double)sq_dist(pp, aim), h, g_sqBuild ? "ok" : "MISMATCH");
    for (int pass = 0; pass < 2; pass++) {
        int n = pass ? nr : nm;
        for (int i = 0; i < n; i++) {
            BYTE *s = (BYTE*)rd32(pass ? sc + 0x1c + 4 * i : sq + 0xc4 + 4 * i);
            int inRecv = 0, inSq = 0;
            for (int j = 0; j < nr; j++) inRecv |= rd32(sc + 0x1c + 4 * j) == (DWORD)s;
            for (int j = 0; j < nm; j++) inSq |= rd32(sq + 0xc4 + 4 * j) == (DWORD)s;
            if (pass && inSq) continue;                  /* receivers already listed as members */
            if (!sq_script(s)) { sq_log("probe %s[%d] %p vt=%08lx (not a ZSoldier@CPPScript)", pass ? "receiver" : "member", i, s, rd32(s)); continue; }
            BYTE *body = sq_bodyof(s), *own = (BYTE*)rd32(s + 0x69c); DWORD *vt = (DWORD*)rd32(s);
            char nm2[48]; sq_name(body, nm2, sizeof nm2);
            float bp[3]; sq_body_pos(body, bp);
            sq_log("probe %s[%d] script=%p vt=%08lx merc=%d ctl(6a4)=%d able(576)=%d owner(69c)=%p%s sq(4f4)=%s s79=%08lx%s s83=%08lx%s recv=%d insquad=%d "
                   "elig=%d rel=%d d=%.0f name='%s' node=%ld",
                   pass ? "receiver" : "member", i, s, (DWORD)vt, sq_merc(s), rd8(s + 0x6a4), rd8(body + 0x576), own, own == P ? "(P)" : "",
                   rd32(s + 0x4f4) == (DWORD)sq ? "player" : "other", rd32((BYTE*)vt + 0x13c), rd32((BYTE*)vt + 0x13c) == SQ_F_MOVETO ? "(ok)" : "(!)",
                   rd32((BYTE*)vt + 0x14c), rd32((BYTE*)vt + 0x14c) == SQ_F_ATTACK ? "(ok)" : "(!)", inRecv, inSq, sq_canrecv(sc, s, 0), sq_rel(body),
                   (double)sq_dist(pp, bp), nm2, sq_node_idx(body));
        }
    }
    static SqSol sol[256]; int ns = sq_soldiers(sol, 256), nmerc = 0, nfriend = 0;
    for (int i = 0; i < ns; i++) {
        nmerc += sol[i].merc >= 1; nfriend += sol[i].rel == 0 || sol[i].rel == 2;
        if (sol[i].merc < 1) continue;
        int inRecv = 0, inSq = 0;
        for (int j = 0; j < nr; j++) inRecv |= rd32(sc + 0x1c + 4 * j) == (DWORD)sol[i].s;
        for (int j = 0; j < nm; j++) inSq |= rd32(sq + 0xc4 + 4 * j) == (DWORD)sol[i].s;
        char nm2[48]; sq_name(sol[i].body, nm2, sizeof nm2);
        sq_log("probe merc body=%p '%s' node=%ld merc=%d rel=%d recv=%d insquad=%d sq(4f4)=%08lx own=%08lx ctl=%d able=%d",
               sol[i].body, nm2, sq_node_idx(sol[i].body), sol[i].merc, sol[i].rel, inRecv, inSq, rd32(sol[i].s + 0x4f4),
               rd32(sol[i].s + 0x69c), rd8(sol[i].s + 0x6a4), rd8(sol[i].body + 0x576));
    }
    sq_log("probe soldiers=%d mercs=%d rel0/2=%d (recruitment question: mercs alive but recv=%d)", ns, nmerc, nfriend, nr);
    int nt = (int)rd32(gm + 0xc00); char b[1200]; int k = 0;
    sq_cat(b, sizeof b, &k, "probe triggers gm+c00 n=%d:", nt);
    for (int i = 0; i < nt && i < 0x20; i++) {
        BYTE *t = (BYTE*)rd32(gm + 0xc04 + 4 * i); char nm2[48]; sq_name(t, nm2, sizeof nm2);
        sq_cat(b, sizeof b, &k, " [%d] %p vt=%08lx node=%ld '%s' en34=%d", i, t, rd32(t), sq_node_idx(t), nm2, rd8(t + 0x34));
    }
    sq_log("%s", b);
    (void)T;
}

/* ---------- order building blocks (live = mode on) ---------- */
typedef struct { int kind; float p[3]; long node; } SqSpec;
static int sq_targets(BYTE *sc, int hold, int live, BYTE **out, int max) {
    int n = 0;
    if (!hold) { BYTE *c = sq_cur(sc); if (c && sq_canrecv(sc, c, live)) out[n++] = c; return n; }
    BYTE *sq = sq_squad(sc); int nm = sq_nmem(sq), nr = sq_nrecv(sc);
    for (int pass = 0; pass < 2; pass++)
        for (int i = 0; i < (pass ? nr : nm) && n < max; i++) {
            BYTE *s = (BYTE*)rd32(pass ? sc + 0x1c + 4 * i : sq + 0xc4 + 4 * i); int dup = 0;
            for (int j = 0; j < n; j++) dup |= out[j] == s;
            if (!dup && sq_canrecv(sc, s, live)) out[n++] = s;
            if (g_sqDead) return 0;
        }
    return n;
}
static BYTE *sq_nearest_of(BYTE **list, int n, const float *pp) {
    BYTE *best = 0; float bd = 1e30f;
    for (int i = 0; i < n; i++) { float bp[3]; if (!sq_body_pos(sq_bodyof(list[i]), bp)) continue; float d = sq_dist(pp, bp); if (d < bd) { bd = d; best = list[i]; } }
    return best;
}
static int sq_speech_ok(BYTE *s) {                    /* 0x763db0 derefs [[script+0x564]]+0x69c -> +0x840 -> +0xc */
    BYTE *sp = (BYTE*)rd32(s + 0x564), *own = (BYTE*)rd32(sp), *pl = (BYTE*)rd32(own + 0x69c), *x = (BYTE*)rd32(pl + 0x840);
    return sq_rd(sp, 4) && sq_rd(own, 0x6a0) && sq_rd(pl, 0x844) && sq_rd(x + 0xc, 4);
}
static void sq_speak(BYTE *s, int id, const char *what) {
    if (!id || !s) return;
    if (!sq_speech_ok(s)) { sq_log("voice %s id=%#x skipped (speech object not ready)", what, id); return; }
    sq_call1("speech", SQ_F_SPEAK, (BYTE*)rd32(s + 0x564), (DWORD)id);
    sq_log("voice %s id=%#x by script %p", what, id, s);
}
static void sq_signal(BYTE *P, int gesture) {
    BYTE *x = (BYTE*)rd32(P + 0x840);
    if (rd8(P + 0xd28) && sq_rd(x, 0x10)) sq_call1("signal", SQ_F_SIGNAL, x, (DWORD)gesture);
}
static void sq_answer(BYTE *P, BYTE *s, int voice, const char *what) {   /* Kane looks at the answering merc, merc speaks */
    if (!s) return;
    BYTE *body = sq_bodyof(s); DWORD f34c = rd32((BYTE*)rd32(P) + 0x34c);
    if (rd8(P + 0xd28) && !rd8(P + 0x95a) && sq_code(f34c) && !(sq_call0("player vt+34c", f34c, P) & 0xff)) {
        DWORD a[4] = {(DWORD)body, fbits(1.5f), fbits(2.0f), 2};
        sq_call("look-at", SQ_F_LOOKAT, P, 4, a, 0);
    }
    sq_speak(s, voice, what);
}
static void sq_marker(BYTE *P, BYTE *body, int type, float dur) {
    if (!g_sqc.markers || !body) return;
    BYTE *gm = (BYTE*)rd32((void*)0xdd265c), *mgr = (BYTE*)rd32(gm + 0x15e0);
    if (!sq_rd(mgr, 0x10)) return;
    static __attribute__((aligned(16))) BYTE rec[0x80];
    memset(rec, 0, sizeof rec);
    DWORD a[4] = {(DWORD)body, (DWORD)type, fbits(dur), (DWORD)(int)*(signed char*)(P + 0x91d)};
    sq_call("marker record", SQ_F_MARKREC, rec, 4, a, 0);
    sq_call1("marker add", SQ_F_MARKADD, mgr, (DWORD)rec);
    sq_log("marker type %#x on %p for %.1fs", type, body, (double)dur);
}
/* the M01 rule (refuse=auto) or refuse=1: sc+0xa0 is set to 1 in mode on; dry reports it as if it were set */
static int sq_refuse_rule(void) { return g_sqc.refuse == 1 || (g_sqc.refuse < 0 && !strcmp(g_sqScene, "M01")); }
static int sq_refusing(BYTE *sc, int live) { return rd8(sc + 0xa0) || (!live && sq_refuse_rule()); }
/* shared prologue for Fire at / Defend (DD Follow has it built in): NULL = go on */
static const char *sq_prologue(BYTE *P, BYTE *sc, int gesture, int refVoice, int live, int *refused) {
    *refused = 0;
    if (live ? (int)(sq_call0("busy", SQ_F_BUSY, P) & 0xff) : sq_busy(P)) return "player busy (0x6a88f0)";
    if (sq_refusing(sc, live)) {
        *refused = 1;
        if (live) {   /* 0x6eac60 always speaks: voice 0 would be id 0 (pain), so "none" is passed as 0xff */
            DWORD a[2] = {(DWORD)gesture, (DWORD)(refVoice ? refVoice : SQ_VOICE_NONE)};
            sq_call("refuse", SQ_F_REFUSE, sc, 2, a, 0);
            if (!g_sqDead) sq_log("refuse gesture %d voice %#x (0x6eac60: nearest merc answers)", gesture, (unsigned)a[1]);
        }
        return "refused (sc+0xa0, M01 rule)";
    }
    return 0;
}
static void sq_after(BYTE *sc, int hold, int live, const char *what) {   /* TAP: the receiver advances, as DM does */
    if (hold || !live) return;
    sq_call1("select next", SQ_F_CYCLE, sc, 0);
    sq_log("sel -> %d/%d after %s tap", sq_cur_idx(sc), sq_nrecv(sc), what);
}

/* ---------- aim / spec resolution ---------- */
static BYTE *sq_obj_at_node(long idx) {
    DWORD stride, cap; BYTE *base;
    if (idx < 0 || !node_table(&stride, &cap, &base) || (DWORD)idx >= cap) return 0;
    return (BYTE*)rd32(base + idx * stride + 0x60);
}
/* handle of a node object (0x86ca10 on the node manager), checked by resolving it back with 0x8ccde0; 0 = none */
static DWORD sq_handle_of(BYTE *o) {
    BYTE *mgr = (BYTE*)rd32((void*)0xe0ff90);
    if (!o || sq_node_idx(o) < 0 || !sq_rd(mgr + 0xc, 4)) return 0;    /* o+4 must be a node inside the table */
    DWORD h = sq_call1("obj handle", SQ_F_OBJHANDLE, mgr, (DWORD)o);
    if (!h || g_sqDead) return 0;
    DWORD a[1] = {h};
    BYTE *back = (BYTE*)sq_call("handle", SQ_F_HANDLE, 0, 1, a, 1);
    return (!g_sqDead && back == o) ? h : 0;
}
static int sq_is_soldier_body(BYTE *o) { BYTE *s = (BYTE*)rd32(o + 0x77c); return sq_rd(o, 0x780) && sq_rd(s, 0x6f0) && *(DWORD*)s == SQ_SCRIPT_VT && rd32(s + 0x40) == (DWORD)o; }
static int sq_alive(BYTE *body, int live) {
    if (rd8(body + 0x576) != 1) return 0;
    if (!live) return 1;
    DWORD f = rd32((BYTE*)rd32(body) + 0x680);
    return sq_code(f) && !(sq_call0("body dead", f, body) & 0xff);
}
static int sq_hostile(BYTE *o, BYTE *P, BYTE *sc) {
    if (!sq_is_soldier_body(o) || o == P) return 0;
    int rel = sq_rel(o);
    if (rel == 0 || rel == 2) return 0;               /* crosshair 0x8e9720: friendly relations */
    BYTE *s = (BYTE*)rd32(o + 0x77c);
    return rd32(s + 0x4f4) != rd32(sc + 0xa4);        /* not one of ours */
}
/* aim point + target. tgt = a hostile soldier body or 0, th = its handle (slot 83 wants a handle). 0 = no usable point */
static int sq_resolve_body(BYTE *P, BYTE *sc, const SqSpec *sp, int live, float *pos, BYTE **tgt, char *desc, int dn);
static int sq_resolve(BYTE *P, BYTE *sc, const SqSpec *sp, int live, float *pos, BYTE **tgt, DWORD *th, char *desc, int dn) {
    *th = 0;
    int ok = sq_resolve_body(P, sc, sp, live, pos, tgt, desc, dn);
    if (ok && *tgt && !g_sqDead) {
        DWORD h = sp->kind == SQS_AIM ? rd32((BYTE*)rd32(P + 0xbd4) + 0x2ac) : 0;    /* the crosshair's own handle */
        if (h) { DWORD a[1] = {h}; if ((BYTE*)sq_call("handle", SQ_F_HANDLE, 0, 1, a, 1) != *tgt) h = 0; }
        if (!h && !g_sqDead) h = sq_handle_of(*tgt);
        *th = h;
        if (!h) { int k = (int)strlen(desc); _snprintf(desc + k, dn - 1 - k, " (no handle: position attack)"); *tgt = 0; }
    }
    return ok && !g_sqDead;
}
static int sq_resolve_body(BYTE *P, BYTE *sc, const SqSpec *sp, int live, float *pos, BYTE **tgt, char *desc, int dn) {
    *tgt = 0; memset(desc, 0, dn); dn--;              /* the last byte stays 0 (_snprintf does not terminate on overflow) */
    float pp[3]; sq_player_pos(P, pp);
    if (sp->kind == SQS_XYZ) { memcpy(pos, sp->p, 12); _snprintf(desc, dn, "xyz"); return 1; }
    if (sp->kind == SQS_NODE) {
        BYTE *o = sq_obj_at_node(sp->node);
        if (!sq_rd(o, 8)) { _snprintf(desc, dn, "node %ld: no object", sp->node); return 0; }
        if (!sq_body_pos(o, pos)) { _snprintf(desc, dn, "node %ld: no position", sp->node); return 0; }
        if (sq_is_soldier_body(o)) *tgt = o;
        _snprintf(desc, dn, "node %ld %s%s", sp->node, rtti_name(o), *tgt ? " (soldier)" : "");
        return 1;
    }
    if (sp->kind == SQS_NEAREST) {
        static SqSol sol[256]; int n = sq_soldiers(sol, 256); float bd = 6000.0f; BYTE *best = 0;
        for (int i = 0; i < n; i++) {
            if (!sq_hostile(sol[i].body, P, sc) || !sq_alive(sol[i].body, live)) continue;
            float bp[3]; if (!sq_body_pos(sol[i].body, bp)) continue;
            float d = sq_dist(pp, bp); if (d < bd) { bd = d; best = sol[i].body; memcpy(pos, bp, 12); }
        }
        if (!best) { _snprintf(desc, dn, "nearest: no living hostile soldier within 60 m (%d soldiers)", n); return 0; }
        char nm[40]; sq_name(best, nm, sizeof nm);
        *tgt = best; _snprintf(desc, dn, "nearest '%s' node %ld rel %d d=%.0f", nm, sq_node_idx(best), sq_rel(best), (double)bd);
        return 1;
    }
    /* aim: P+0x27b0 (aim point), [P+0xbd4]+0x2ac (aim target handle) */
    memcpy(pos, P + 0x27b0, 12);
    float d = sq_dist(pp, pos);
    BYTE *cam = (BYTE*)rd32(P + 0xbd4); DWORD h = rd32(cam + 0x2ac); BYTE *o = 0;
    if (h) { DWORD a[1] = {h}; o = (BYTE*)sq_call("handle", SQ_F_HANDLE, 0, 1, a, 1); }
    if (o && sq_hostile(o, P, sc) && sq_alive(o, live)) { *tgt = o; sq_body_pos(o, pos); }
    char nm[40] = ""; if (o && sq_rd(o, 8)) sq_name(o, nm, sizeof nm);
    _snprintf(desc, dn, "aim d=%.0f handle=%08lx obj=%p '%s' rel=%d%s", (double)d, h, o, nm, o ? sq_rel(o) : -1, *tgt ? " (hostile)" : "");
    if (!*tgt && (d < 50.0f || d > 20000.0f || (pos[0] == 0 && pos[1] == 0 && pos[2] == 0))) return 0;
    return 1;
}

/* ---------- the three orders ---------- */
/* DD's Follow speaks its own ack 0x31 (Lynch HUMMING in Dead Men's banks; out of range, silent, for the other mercs).
   For the length of the call that id is blocked in the team-0 cooldown table ([0xdd25d4] +0x14 + 12*0x31 = {interval,
   last, flag}; 0x82fc90 passes when now + (arg - last) * 1024 >= interval * 1024): interval = 1e6 s never passes and still
   fits an int after the * 1024. The 12 bytes are saved here and put back by the caller. 0 = nothing changed. */
static BYTE *sq_mute_dd_follow(BYTE *save) {
    if (g_sqc.ddFollowVoice || g_sqc.ackF == SQ_DD_FOLLOW_VOICE) return 0;
    if (!readable((void*)0x4c3af5, 3) || memcmp((void*)0x4c3af5, "\x6a\x31\xe8", 3)) return 0;   /* push 0x31; call 0x763db0 */
    BYTE *t = (BYTE*)rd32((void*)SQ_TEAM0_PTR);
    if (!t) { t = (BYTE*)sq_call0("team-0 singleton", SQ_F_TEAM0, 0); if (g_sqDead) return 0; sq_rd_reset(); }
    if (!sq_rd(t, 0x308) || *(DWORD*)t != SQ_TEAM0_VT || *(DWORD*)(t + 4) != SQ_TEAM0_VT2) return 0;
    BYTE *e = t + 0x14 + 12 * SQ_DD_FOLLOW_VOICE;
    if (!god_writable(e, 12)) return 0;
    memcpy(save, e, 12);
    float big = 1.0e6f; memcpy(e, &big, 4);
    return e;
}
static void sq_follow(BYTE *P, BYTE *sc, int hold, int T, int live) {
    const char *hn = hold ? "hold" : "tap";
    BYTE *list[28]; int n = sq_targets(sc, hold, live, list, 28);
    if (g_sqDead) return;
    long n8 = (long)rd32(sc + 8); int a0 = sq_refusing(sc, live);
    if (!live) { sq_log("order follow %s dry: would call Follow(sc,%d) on %d merc(s)%s", hn, hold, n, a0 ? " -> refusal (sc+0xa0)" : ""); return; }
    if (a0) {
        /* DD's Follow refuses with 0x2f (deny_fire in Dead Men's banks); Dead Men's Follow (DM 0x613bc0) says 0x30
           (deny_regroup). Same steps as DD's prologue at 0x4c3900: busy -> nothing; else 0x6eac60(sc, 7, voice). */
        int busy = (int)(sq_call0("busy", SQ_F_BUSY, P) & 0xff);
        if (g_sqDead) return;
        if (busy) { sq_log("order follow %s: player busy (0x6a88f0)", hn); return; }
        DWORD a[2] = {7, (DWORD)(g_sqc.refF ? g_sqc.refF : SQ_VOICE_NONE)};
        sq_call("refuse", SQ_F_REFUSE, sc, 2, a, 0);
        if (!g_sqDead) sq_log("refuse follow %s: REFUSED (sc+0xa0: Lynch says no) -> 0x6eac60(gesture 7, voice %#x)", hn, (unsigned)a[1]);
        return;
    }
    float pp[3]; sq_player_pos(P, pp);
    BYTE *who = hold ? sq_nearest_of(list, n, pp) : (n ? list[0] : 0);   /* the merc DD's Follow answers with */
    if (g_sqDead) return;
    BYTE save[12]; BYTE *muted = sq_mute_dd_follow(save);
    if (g_sqDead) return;
    sq_call1("Follow", SQ_F_FOLLOW, sc, (DWORD)hold);
    if (muted) memcpy(muted, save, 12);               /* the heap entry is back as it was */
    if (g_sqDead) return;
    long n8b = (long)rd32(sc + 8);
    sq_log("order follow %s -> 0x4c3900(sc,%d) targets=%d n8 %ld->%ld%s sel=%d/%d dd-voice-0x31=%s", hn, hold, n, n8, n8b,
           n8b == n8 ? " (not issued: busy / no receiver)" : "", sq_cur_idx(sc), sq_nrecv(sc),
           muted ? "muted" : g_sqc.ddFollowVoice ? "kept" : "NOT muted (team-0 table unavailable)");
    if (n8b == n8) return;
    for (int i = 0; i < n; i++) sq_record(list[i], SQO_FOLLOW, T, NULL, NULL);
    if (g_sqc.ackF && rd8(P + 0xd28)) sq_speak(who, g_sqc.ackF, "follow ack");   /* DD speaks only when P+0xd28 is set */
}
static void sq_attack(BYTE *P, BYTE *sc, int hold, const SqSpec *sp, int T, int live) {
    const char *hn = hold ? "hold" : "tap"; int refused;
    float pos[3]; BYTE *tgt = 0; DWORD th = 0; char desc[200];
    const char *why = sq_prologue(P, sc, 8, g_sqc.refA, live, &refused);
    if (why) { sq_log("%s attack %s: %s%s", refused ? "refuse" : "order", hn, why, live ? "" : " (dry)"); return; }
    if (!sq_resolve(P, sc, sp, live, pos, &tgt, &th, desc, sizeof desc)) { if (!g_sqDead) sq_log("order attack %s fail: no target (%s)", hn, desc); return; }
    BYTE *list[28]; int n = sq_targets(sc, hold, live, list, 28);
    if (g_sqDead) return;
    if (!n) { sq_log("order attack %s fail: %s", hn, hold ? "no eligible merc" : "no current receiver"); return; }
    char tn[40] = ""; if (tgt) sq_name(tgt, tn, sizeof tn);
    sq_log("order attack %s n=%d tgt=%p h=%08lx '%s' pos=(%.0f,%.0f,%.0f) T=%.1f [%s]%s", hn, n, tgt, th, tn, (double)pos[0], (double)pos[1], (double)pos[2],
           (double)g_sqc.attackT, desc, live ? "" : " dry: no call");
    if (!live) return;
    if (god_writable(sc + 8, 4)) (*(DWORD*)(sc + 8))++;   /* order counter, as DD's Follow does (heap) */
    sq_signal(P, 8);
    for (int i = 0; i < n && !g_sqDead; i++) {
        BYTE *s = list[i]; DWORD f = rd32((BYTE*)rd32(s) + 0x14c);
        if (f != SQ_F_ATTACK) { sq_log("order attack: script %p slot 83 = %08lx (not 0x831850) - skipped", s, f); continue; }
        DWORD a[3] = {th, (DWORD)pos, fbits(g_sqc.attackT)};            /* handle (0 = position attack), pos, T */
        sq_call("Attack slot 83", f, s, 3, a, 0);
        if (g_sqDead) break;
        char nm[40]; sq_name(sq_bodyof(s), nm, sizeof nm);
        sq_log("order attack merc=%d '%s' -> slot83 ok atk720=%08lx%s 4fc=%d", sq_merc(s), nm, rd32(s + 0x720),
               tgt ? ((BYTE*)rd32(s + 0x720) == tgt ? "(=tgt)" : "(!=tgt)") : "", rd8(s + 0x4fc));
        sq_record(s, SQO_ATTACK, T, pos, tgt);
    }
    if (tgt) sq_marker(P, tgt, 0xa, 1.0f);
    float pp[3]; sq_player_pos(P, pp);
    sq_answer(P, sq_nearest_of(list, n, pp), g_sqc.ackA, "attack ack");
    sq_after(sc, hold, live, "attack");
}
static void sq_defend(BYTE *P, BYTE *sc, int hold, const SqSpec *sp, int T, int live) {
    const char *hn = hold ? "hold" : "tap"; int refused;
    float pos[3]; BYTE *tgt = 0; char desc[200];
    const char *why = sq_prologue(P, sc, 6, g_sqc.refD, live, &refused);
    if (why) { sq_log("%s defend %s: %s%s", refused ? "refuse" : "order", hn, why, live ? "" : " (dry)"); return; }
    if (!sq_resolve_body(P, sc, sp, live, pos, &tgt, desc, sizeof desc)) { if (!g_sqDead) sq_log("order defend %s fail: no point (%s)", hn, desc); return; }   /* node N: at that object */
    if (g_sqDead) return;
    {   /* snap to the ground: ray from 100 above to 100 below (mask 0x20) */
        ClRay ray; float o[3] = {pos[0], pos[1] + 100, pos[2]}, seg[3] = {0, -200, 0}, pt[3];
        if (cl_ray(o, seg, 0x20, &ray, pt) == 1) pos[1] = pt[1];
    }
    BYTE *list[28]; int n = sq_targets(sc, hold, live, list, 28), ok[28], nok = 0;
    if (g_sqDead) return;
    if (!n) { sq_log("order defend %s fail: %s", hn, hold ? "no eligible merc" : "no current receiver"); return; }
    float tp[3] = {pos[0], pos[1] + 50, pos[2]};
    for (int i = 0; i < n; i++) {
        float bp[3]; sq_body_pos(sq_bodyof(list[i]), bp); bp[1] += 160;
        BYTE *hit = 0; int l = sq_los(bp, tp, &hit);
        ok[i] = l == 1; nok += ok[i];
        char nm[40]; sq_name(sq_bodyof(list[i]), nm, sizeof nm);
        sq_log("defend los merc=%d '%s' -> %s%s%s d=%.0f", sq_merc(list[i]), nm, l < 0 ? "unavailable" : l ? "clear" : "blocked by ",
               l == 0 ? rtti_name(hit) : "", "", (double)sq_dist(bp, tp));
    }
    if (!nok) {
        sq_log("defend fail nolos %s pos=(%.0f,%.0f,%.0f) n=%d [%s]", hn, (double)pos[0], (double)pos[1], (double)pos[2], n, desc);
        if (live) { float pp[3]; sq_player_pos(P, pp); sq_speak(sq_nearest_of(list, n, pp), g_sqc.nolos, "defend nolos"); }
        return;
    }
    sq_log("order defend %s n=%d los=%d pos=(%.0f,%.0f,%.0f) [%s]%s", hn, n, nok, (double)pos[0], (double)pos[1], (double)pos[2], desc, live ? "" : " dry: no call");
    if (!live) return;
    if (god_writable(sc + 8, 4)) (*(DWORD*)(sc + 8))++;
    sq_signal(P, 6);
    BYTE *done[28]; int nd = 0;
    for (int i = 0; i < n && !g_sqDead; i++) {
        if (!ok[i]) continue;
        BYTE *s = list[i]; DWORD f = rd32((BYTE*)rd32(s) + 0x13c);
        if (f != SQ_F_MOVETO) { sq_log("order defend: script %p slot 79 = %08lx (not 0x760e50) - skipped", s, f); continue; }
        DWORD a[4] = {(DWORD)pos, 0, 1, 0};
        sq_call("MoveTo slot 79", f, s, 4, a, 0);
        char nm[40]; sq_name(sq_bodyof(s), nm, sizeof nm);
        sq_log("order defend merc=%d '%s' -> slot79 ok 4fc=%d", sq_merc(s), nm, rd8(s + 0x4fc));
        sq_record(s, SQO_DEFEND, T, pos, NULL);
        sq_marker(P, sq_bodyof(s), 7, 2.0f);
        done[nd++] = s;
    }
    float pp[3]; sq_player_pos(P, pp);
    sq_answer(P, sq_nearest_of(done, nd, pp), g_sqc.ackD, "defend ack");
    sq_after(sc, hold, live, "defend");
}
static void sq_cycle(BYTE *sc, int prev, int live) {
    int before = sq_cur_idx(sc);
    if (live) sq_call1("select", SQ_F_CYCLE, sc, (DWORD)prev);
    BYTE *c = sq_cur(sc); char nm[40] = ""; if (sq_script(c)) sq_name(sq_bodyof(c), nm, sizeof nm);
    sq_log("sel %s %d -> %d/%d merc=%d '%s'%s", prev ? "prev" : "next", before, sq_cur_idx(sc), sq_nrecv(sc), sq_script(c) ? sq_merc(c) : -1, nm, live ? "" : " (dry: unchanged)");
}

/* ---------- gate + dispatch ---------- */
static const char *sq_gate(BYTE *P, int T, int fromKeys) {
    if (!sq_anp_level()) return "not an ANP level";
    if (fromKeys && !sq_foreground()) return "not foreground";
    if (rd8(P + 0x2728) || rd32(P + 0x2760)) return "gameplay input blocked (P+2728/2760)";   /* ZGameplayInput 0x808720 */
    int st = sq_hud_state(P);
    if (st >= 2 && st <= 13 && st != 10) return "HUD hidden (cutscene / death)";   /* the 0x6a88f0 set: state 10 is not busy */
    if (g_sq.hudSeen && T - g_sq.hudT < 1024) return "1 s cooldown after a cutscene";
    if (g_cl.active) return "climbing";
    return 0;
}
static void sq_dispatch(BYTE *P, BYTE *sc, int kind, int hold, const SqSpec *sp, int T, int fromKeys, const char *src) {
    static DWORD lastIgn;
    if (g_sqc.mode < SQ_DRY) { sq_log("%s %s %s (probe: not dispatched)", src, SQ_ORD[kind], hold ? "hold" : "tap"); return; }
    const char *why = sq_gate(P, T, fromKeys);
    if (why) { if (sq_rate(&lastIgn, 500)) sq_log("%s %s %s ignored (%s)", src, SQ_ORD[kind], hold ? "hold" : "tap", why); return; }
    int live = g_sqc.mode == SQ_ON && g_sqBuild == 1;
    if (g_sqc.mode == SQ_ON && !live && sq_rate(&lastIgn, 500)) sq_log("orders off: kl2 build mismatch - running dry");
    if (kind == SQO_FOLLOW) sq_follow(P, sc, hold, T, live);
    else if (kind == SQO_ATTACK) sq_attack(P, sc, hold, sp, T, live);
    else if (kind == SQO_DEFEND) sq_defend(P, sc, hold, sp, T, live);
    if (live && !g_sqDead) sq_stat(P, sc, T, "after-order");
}
static void sq_select(BYTE *P, BYTE *sc, int prev, int T, int fromKeys, const char *src) {
    if (g_sqc.mode < SQ_DRY) { sq_log("%s %s (probe: not dispatched)", src, prev ? "prev" : "next"); return; }
    const char *why = sq_gate(P, T, fromKeys);
    if (why) { sq_log("%s %s ignored (%s)", src, prev ? "prev" : "next", why); return; }
    sq_cycle(sc, prev, g_sqc.mode == SQ_ON && g_sqBuild == 1);
}

/* keys: tap/hold machine of DM 0x638ea0 (0.25 s) */
static void sq_keys(BYTE *P, BYTE *sc, int T) {
    if (!g_sqc.input) { g_sq.keySrc = 0; return; }
    if (g_sqc.input == 1) { if (!g_sq.kb || rd32(g_sq.kb) != SQ_KB_VT || g_sq.sys != (BYTE*)rd32((void*)0xddb958)) sq_find_devices(); g_sq.keySrc = g_sq.kb ? 1 : 2; }
    else g_sq.keySrc = 2;
    int fg = sq_foreground();
    int dk[3] = {g_sqc.kFollow, g_sqc.kAttack, g_sqc.kDefend};
    for (int i = 0; i < 3; i++) {
        SqKey *k = &g_sqK[i];
        int d = fg && (sq_key(dk[i]) || (i == 1 && sq_mouse(g_sqc.mAttack)));
        if (d && !k->down) { k->down = 1; k->t0 = T; k->fired = 0; }
        else if (d && k->down && !k->fired && T - k->t0 >= SQ_TAP_T) {
            k->fired = 1;
            sq_log("key %s hold (%.2fs)", SQ_ORD[i + 1], (T - k->t0) / 1024.0f);
            SqSpec sp = {SQS_AIM, {0, 0, 0}, -1};
            sq_dispatch(P, sc, i + 1, 1, &sp, T, 1, "key");
        } else if (!d && k->down) {
            k->down = 0;
            if (!k->fired) {
                sq_log("key %s tap (%.2fs)", SQ_ORD[i + 1], (T - k->t0) / 1024.0f);
                SqSpec sp = {SQS_AIM, {0, 0, 0}, -1};
                sq_dispatch(P, sc, i + 1, 0, &sp, T, 1, "key");
            }
        }
        if (g_sqDead) return;
    }
    int shift = sq_key(0x2A) || sq_key(0x36);
    int nx = fg && sq_key(g_sqc.kNext), pv = fg && g_sqc.kPrev && sq_key(g_sqc.kPrev);
    if (nx && !g_sqNextDown) { sq_log("key %s", shift && !g_sqc.kPrev ? "prev (shift+next)" : "next"); sq_select(P, sc, shift && !g_sqc.kPrev, T, 1, "key"); }
    if (pv && !g_sqPrevDown) { sq_log("key prev"); sq_select(P, sc, 1, T, 1, "key"); }
    g_sqNextDown = nx; g_sqPrevDown = pv;
}

/* ---------- ANP_squad_cmd.txt ---------- */
static void sq_cmd_poll(void) {
    DWORD now = GetTickCount();
    if (now - g_sq.cmdPoll < 250) return;
    g_sq.cmdPoll = now;
    char fn[MAX_PATH], dn[MAX_PATH];
    _snprintf(fn, sizeof fn, "%s\\ANP_squad_cmd.txt", g_dir); _snprintf(dn, sizeof dn, "%s\\ANP_squad_cmd.done", g_dir);
    if (GetFileAttributesA(fn) == INVALID_FILE_ATTRIBUTES) return;
    char buf[2048] = ""; FILE *f = fopen(fn, "r");
    if (!f) return;                                   /* still being written */
    size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
    if (!n) return;
    if (!MoveFileExA(fn, dn, MOVEFILE_REPLACE_EXISTING) && !DeleteFileA(fn)) { sq_log("cmd: cannot consume ANP_squad_cmd.txt (error %lu)", GetLastError()); return; }
    int added = 0;
    for (char *l = strtok(buf, "\r\n"); l; l = strtok(NULL, "\r\n")) {
        while (*l == ' ' || *l == '\t') l++;
        if (!*l || *l == '#') continue;
        if (g_sqQn >= 32) { sq_log("cmd queue full, '%s' dropped", l); continue; }
        _snprintf(g_sqQ[(g_sqQh + g_sqQn) % 32], 96, "%s", l); g_sqQ[(g_sqQh + g_sqQn) % 32][95] = 0; g_sqQn++; added++;
    }
    sq_log("cmd file: %d command(s) queued", added);
}
static void sq_cmd_exec(const char *line, BYTE *P, BYTE *sc, int T) {
    char b[96]; _snprintf(b, sizeof b, "%s", line); b[95] = 0;
    char *tok[8]; int nt = 0;
    for (char *t = strtok(b, " \t"); t && nt < 8; t = strtok(NULL, " \t")) tok[nt++] = t;
    if (!nt) return;
    sq_log("cmd '%s'", line);
    if (!_stricmp(tok[0], "state")) { sq_probe(P, sc, T); sq_stat(P, sc, T, "cmd"); return; }
    if (!_stricmp(tok[0], "next") || !_stricmp(tok[0], "prev")) { sq_select(P, sc, !_stricmp(tok[0], "prev"), T, 0, "cmd"); return; }
    int kind = !_stricmp(tok[0], "follow") ? SQO_FOLLOW : !_stricmp(tok[0], "attack") ? SQO_ATTACK : !_stricmp(tok[0], "defend") ? SQO_DEFEND : 0;
    if (!kind) { sq_log("cmd '%s' unknown (follow|attack|defend tap|hold [aim|x y z|node N|nearest], next, prev, state, wait S)", tok[0]); return; }
    int hold = nt > 1 && !_stricmp(tok[1], "hold");
    SqSpec sp = {SQS_AIM, {0, 0, 0}, -1};
    int a = (nt > 1 && (!_stricmp(tok[1], "hold") || !_stricmp(tok[1], "tap"))) ? 2 : 1;
    if (nt > a) {
        if (!_stricmp(tok[a], "nearest")) sp.kind = SQS_NEAREST;
        else if (!_stricmp(tok[a], "aim")) sp.kind = SQS_AIM;
        else if (!_stricmp(tok[a], "node") && nt > a + 1) { sp.kind = SQS_NODE; sp.node = atol(tok[a + 1]); }
        else if (nt > a + 2) { sp.kind = SQS_XYZ; sp.p[0] = (float)atof(tok[a]); sp.p[1] = (float)atof(tok[a + 1]); sp.p[2] = (float)atof(tok[a + 2]); }
        else { sq_log("cmd '%s': bad target (aim | x y z | node N | nearest)", line); return; }
    }
    if (kind == SQO_DEFEND && sp.kind == SQS_NEAREST) { sq_log("cmd '%s': defend takes aim | x y z | node N", line); return; }
    sq_dispatch(P, sc, kind, hold, &sp, T, 0, "cmd");
}

/* ---------- recruitment ----------
   Dead Men recruits every Merc_xx soldier into Kane's ZSquadControl at spawn (DM 0x613690). DD's port is 0x908040, but DD's
   soldier init 0x615c90 calls it only in a hosted network session; with no session the buddy (merc 1 'Kane' = Lynch) only
   gets the follow call (slot 80) and every other merc is recruited only if player 0 and its squad control already existed.
   So: every 0.5 s, 1 s after the player / squad control appears, outside cutscenes, every living merc of DD's merc list
   (plus any merc the one-off node walk finds outside it) that is not yet a receiver of this squad control is recruited with
   0x908040, exactly as DD's hosted path does. 0x908040 has no duplicate check, so the guard below is mandatory. Once
   recruited, DD's own ZSquadControl::Update (0x523d10, every frame) parks / re-recruits him when his node is disabled. */
static int sq_in_list(BYTE *sc, int cntOff, int arrOff, BYTE *s) {
    int n = (int)rd32(sc + cntOff); if (n < 0) n = 0; if (n > 16) n = 16;
    for (int i = 0; i < n; i++) if (rd32(sc + arrOff + 4 * i) == (DWORD)s) return 1;
    return 0;
}
static int sq_in_squad(BYTE *sq, BYTE *s) { int n = sq_nmem(sq); for (int i = 0; i < n; i++) if (rd32(sq + 0xc4 + 4 * i) == (DWORD)s) return 1; return 0; }
/* a current merc: soldier script whose body is a live node-table object (stale list entries fail here) */
static BYTE *sq_merc_body(BYTE *s) {
    if (!sq_script(s) || !sq_rd(s, 0x740)) return 0;
    BYTE *body = sq_bodyof(s);
    if (rd32(body + 0x77c) != (DWORD)s) return 0;
    long idx = sq_node_idx(body);
    if (idx < 0 || sq_obj_at_node(idx) != body) return 0;
    int m = sq_merc(s);
    return (m >= 1 && m <= 13) ? body : 0;
}
/* pointers 0x908040 -> 0x4c3b10 / 0x4be760 / 0x656d00 / 0x50ddb0 / 0x7b3490 / 0x48c480 dereference without checks */
static const char *sq_recruit_unsafe(BYTE *s, BYTE *body) {
    if (!sq_rd((BYTE*)rd32(s + 0x63c), 0x78)) return "no follow object (script+0x63c)";
    if (!sq_rd((BYTE*)rd32(s + 0x738), 0x10)) return "no script+0x738 object";
    if (!sq_rd((BYTE*)rd32(s + 0x6d8), 4)) return "no script+0x6d8 state";
    if (!sq_rd((BYTE*)rd32(body + 4), 0x60)) return "no body node";
    DWORD *vt = (DWORD*)rd32(s);
    if (rd32(vt + 0x1b0 / 4) != SQ_F_SETOWNER || !sq_code(rd32(vt + 0x140 / 4)) || !sq_code(rd32(vt + 0x4c / 4))) return "script vtable";
    if (!sq_code(rd32((BYTE*)rd32(body) + 0x680))) return "body vtable";
    return 0;
}
static SqRec *sq_rec(BYTE *s) {
    for (int i = 0; i < 16; i++) if (g_sqRec[i].s == s) return &g_sqRec[i];
    for (int i = 0; i < 16; i++) if (!g_sqRec[i].s) { memset(&g_sqRec[i], 0, sizeof g_sqRec[i]); g_sqRec[i].s = s; return &g_sqRec[i]; }
    return 0;
}
static const char *sq_recruit_gate(BYTE *P, int T) {
    if (rd8(P + 0x2728) || rd32(P + 0x2760)) return "gameplay input blocked (P+2728/2760)";
    int st = sq_hud_state(P);
    if (st >= 2 && st <= 13 && st != 10) return "HUD hidden (cutscene / death)";
    if (g_sq.hudSeen && T - g_sq.hudT < 1024) return "1 s after a cutscene";
    if (g_cl.active) return "climbing";
    return 0;
}
static void sq_recruit_one(BYTE *P, BYTE *sc, BYTE *s, BYTE *body, int live, DWORD now) {
    SqRec *r = sq_rec(s); if (!r) return;
    BYTE *sq = sq_squad(sc);
    char nm[40]; sq_name(body, nm, sizeof nm);
    DWORD q0 = rd32(s + 0x4f4), o0 = rd32(s + 0x69c);
    int inSq = sq && sq_in_squad(sq, s), nr0 = sq_nrecv(sc), nm0 = sq_nmem(sq);
    if (!live) {
        if (!r->dryLogged) {
            r->dryLogged = 1;
            sq_log("recruit dry: would call 0x908040(sc=%p, body=%p) merc=%d '%s' node=%ld sq4f4=%08lx%s own=%08lx",
                   sc, body, sq_merc(s), nm, sq_node_idx(body), q0, q0 == (DWORD)sq ? "(player)" : "", o0);
        }
        return;
    }
    if (r->tries >= 8) {
        if (r->tries++ == 8) sq_log("recruit merc=%d '%s' s=%p: gave up after 8 recruits this level (he keeps leaving the squad control)", sq_merc(s), nm, s);
        return;
    }
    if (r->lastT && now - r->lastT < 3000) return;
    if (inSq && q0 != (DWORD)sq) {                    /* 0x5230c0 removes from script+0x4f4's squad, not this one */
        if (!r->unsafeLogged) { r->unsafeLogged = 1; sq_log("recruit merc=%d '%s' s=%p skipped: listed in the player squad but sq4f4=%08lx", sq_merc(s), nm, s, q0); }
        return;
    }
    r->lastT = now; r->tries++;
    /* already a member of the player squad but not a receiver: take him out first, or 0x48c480 would list him twice */
    if (inSq) {
        sq_call1("squad remove (player squad)", SQ_F_SQREMOVE, sq, (DWORD)s);
        if (g_sqDead) return;
        sq_log("recruit merc=%d '%s': was in the player squad without being a receiver -> removed (0x5230c0) before the recruit", sq_merc(s), nm);
    } else if (g_sqc.detach && q0 && q0 != (DWORD)sq && !sq_was_player_squad(q0) && sq_rd((BYTE*)q0, 0xc4 + 48) && sq_in_squad((BYTE*)q0, s)) {
        sq_call1("squad remove (level squad)", SQ_F_SQREMOVE, (BYTE*)q0, (DWORD)s);
        if (g_sqDead) return;
        sq_log("recruit merc=%d '%s': detached from level squad %08lx (0x5230c0, recruit_detach=1) 4f4 now %08lx", sq_merc(s), nm, q0, rd32(s + 0x4f4));
    }
    sq_call1("Recruit 0x908040", SQ_F_RECRUIT, sc, (DWORD)body);
    if (g_sqDead) return;
    int in = sq_in_list(sc, 0x18, 0x1c, s), nr1 = sq_nrecv(sc), nm1 = sq_nmem(sq);
    DWORD q1 = rd32(s + 0x4f4), o1 = rd32(s + 0x69c);
    if (!in) r->fails++;
    sq_log("recruit merc=%d '%s' body=%p s=%p node=%ld -> recv %d->%d (in=%d) squad %d->%d sq4f4 %08lx->%08lx%s own %08lx->%08lx%s elig=%d ctl=%d able=%d sel=%d try=%d%s",
           sq_merc(s), nm, body, s, sq_node_idx(body), nr0, nr1, in, nm0, nm1, q0, q1, q1 == (DWORD)sq ? "(player)" : "", o0, o1,
           o1 == (DWORD)P ? "(P)" : "", sq_canrecv(sc, s, 0), rd8(s + 0x6a4), rd8(body + 0x576), sq_cur_idx(sc), r->tries,
           in ? "" : " FAILED: not a receiver after the call");
}
static void sq_recruit_scan(BYTE *P, BYTE *sc, int T, int live, DWORD now) {
    if (!g_sqc.recruit || g_sqc.mode < SQ_DRY) return;
    if (now - g_sq.t0 < 1000 || (g_sq.recPoll && now - g_sq.recPoll < 500)) return;
    g_sq.recPoll = now;
    BYTE *cand[32]; int nc = 0;
    int nl = (int)rd32((void*)SQ_MERC_LIST); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (int i = 0; i < nl && nc < 32; i++) {
        BYTE *s = (BYTE*)rd32((void*)(SQ_MERC_LIST + 4 + 4 * i)); int dup = 0;
        for (int j = 0; j < nc; j++) dup |= cand[j] == s;
        if (s && !dup) cand[nc++] = s;
    }
    if (!g_sq.recWalked) {                            /* once per level: mercs DD's init did not list (merc set later) */
        g_sq.recWalked = 1; g_sqWalkN = 0;
        static SqSol sol[256]; int ns = sq_soldiers(sol, 256);
        for (int i = 0; i < ns && g_sqWalkN < 16; i++) {
            if (sol[i].merc < 1 || sol[i].merc > 13) continue;
            int dup = 0; for (int j = 0; j < nc; j++) dup |= cand[j] == sol[i].s;
            if (!dup) g_sqWalk[g_sqWalkN++] = sol[i].s;
        }
        BYTE *N = (BYTE*)rd32((void*)SQ_NET_MGR);
        sq_log("recruit scan scene=%s mode=%s merc list n=%d, node walk soldiers=%d extra mercs=%d net=%p session(+5c)=%ld host(+54)=%ld "
               "(DD recruits itself only when +5c==2 and +54<=1) sc+cc=%d inactive=%d",
               g_sqScene, live ? "on" : "dry", nl, ns, g_sqWalkN, N, (long)(sq_rd(N + 0x5c, 4) ? (long)*(DWORD*)(N + 0x5c) : -1L),
               (long)(sq_rd(N + 0x54, 4) ? (long)*(DWORD*)(N + 0x54) : -1L), rd8(sc + 0xcc), (int)rd32(sc + 0x5c));
    }
    for (int i = 0; i < g_sqWalkN && nc < 32; i++) { int dup = 0; for (int j = 0; j < nc; j++) dup |= cand[j] == g_sqWalk[i]; if (!dup) cand[nc++] = g_sqWalk[i]; }
    BYTE *sq = sq_squad(sc);
    if (!sq) return;
    const char *gate = sq_recruit_gate(P, T);
    for (int i = 0; i < nc && !g_sqDead; i++) {
        BYTE *s = cand[i], *body = sq_merc_body(s);
        if (!body) continue;                          /* stale / not a merc */
        if (sq_in_list(sc, 0x18, 0x1c, s) || sq_in_list(sc, 0x5c, 0x60, s)) continue;   /* receiver or parked by 0x523d10 */
        if (rd32(s + 0x4f4) == (DWORD)sq && rd32(s + 0x69c) == (DWORD)P) continue;
        if (rd8(body + 0x576) != 1) continue;         /* not able (dead / disabled) */
        if (rd32((BYTE*)rd32(body + 4) + 0x3c) & 0x400) continue;   /* node bit 10: disabled; 0x523d10's rule */
        if (gate) {
            if (!g_sq.recWaitLog || now - g_sq.recWaitLog >= 5000) { g_sq.recWaitLog = now; sq_log("recruit waiting: %s (merc=%d s=%p not yet recruited)", gate, sq_merc(s), s); }
            return;
        }
        const char *why = sq_recruit_unsafe(s, body);
        if (why) {
            SqRec *r = sq_rec(s);
            if (r && !r->unsafeLogged) { r->unsafeLogged = 1; sq_log("recruit merc=%d s=%p skipped: %s", sq_merc(s), s, why); }
            continue;
        }
        if (live && !sq_alive(body, 1)) continue;     /* body vt+0x680 (dead) */
        if (g_sqDead) return;
        sq_recruit_one(P, sc, s, body, live, now);
    }
    g_sq.recScans++;
}

/* ---------- per-frame tick ---------- */
static void sq_level_reset(BYTE *P, BYTE *sc, int T) {
    memcpy(g_sq.scene, g_sqScene, sizeof g_sq.scene); g_sq.lastT = T;
    g_sq.P = P; g_sq.sc = sc; g_sq.t0 = GetTickCount(); g_sq.probes = 0; g_sq.probeRecv = g_sq.probeSq = -1; g_sq.refuseSet = 0;
    g_sq.statT = 0; g_sq.hudT = 0; g_sq.hudSeen = 0; g_sq.kb = g_sq.mouse = 0; g_sq.sys = 0;
    memset(g_sqOrd, 0, sizeof g_sqOrd); memset(g_sqK, 0, sizeof g_sqK); g_sqNextDown = g_sqPrevDown = 1;   /* no edge from a held key */
    memset(g_sqRec, 0, sizeof g_sqRec); g_sqWalkN = 0;   /* recruitment: a new player / squad control starts with no receivers */
    if (sc && sq_squad(sc)) { g_sqPlSq[g_sqPlSqN % 8] = (DWORD)sq_squad(sc); g_sqPlSqN++; }   /* never detach from a player squad */
    g_sq.recPoll = g_sq.recWaitLog = 0; g_sq.recScans = g_sq.recWalked = 0;
    g_sq.critWhy = "scene load";                      /* critical=clear: pass once the player is in an ANP level */
    if (P) sq_log("level %s: player %p sc %p squad %p recv %d mode %s%s", g_sqScene, P, sc, sc ? sq_squad(sc) : 0, sc ? sq_nrecv(sc) : 0,
                  SQ_MODE[g_sqc.mode], sq_anp_level() ? "" : " (not an ANP level: module idle)");
}
static void sq_release_checks(BYTE *P, BYTE *sc, int T, int live) {
    for (int i = 0; i < 16; i++) {
        SqOrd *o = &g_sqOrd[i];
        if (!o->s || !o->relT || T < o->relT) continue;
        o->relT = 0;
        if (!sq_script(o->s)) continue;
        float bp[3], pp[3]; sq_body_pos(sq_bodyof(o->s), bp); sq_player_pos(P, pp);
        float dpt = sq_dist(bp, o->pt), dpl = sq_dist(bp, pp);
        int holding = dpt < 300.0f && dpl > 500.0f;
        sq_log("release merc=%d 2 s after follow: dPoint=%.0f dPlayer=%.0f holding=%d%s", sq_merc(o->s), (double)dpt, (double)dpl, holding,
               holding && g_sqc.release && live ? " -> MoveTo(player) + Follow(all)" : "");
        if (holding && g_sqc.release && live) {
            DWORD f = rd32((BYTE*)rd32(o->s) + 0x13c);
            if (f == SQ_F_MOVETO) { DWORD a[4] = {(DWORD)pp, 0, 1, 0}; sq_call("release MoveTo", f, o->s, 4, a, 0); }
            if (!g_sqDead) sq_call1("release Follow", SQ_F_FOLLOW, sc, 1);
        }
    }
}
static int squad_tick_body(void *unused) {
    (void)unused;
    sq_rd_reset();
    sq_cfg_poll();
    if (g_sqc.mode == SQ_OFF) return 0;
    if (g_sqBuild < 0) g_sqBuild = sq_check_build();
    EnterCriticalSection(&g_cmpCs); memcpy(g_sqScene, g_cscene, sizeof g_sqScene); LeaveCriticalSection(&g_cmpCs);
    g_sqScene[sizeof g_sqScene - 1] = 0;
    BYTE *P = sq_player(), *sc = P ? sq_sc_of(P) : 0;
    int T = cl_curT();
    /* new player / squad control, another scene, or the engine clock went back (restart: the heap may hand out the same
       addresses again) -> drop every per-level pointer (order records, keys) */
    if (P != g_sq.P || sc != g_sq.sc || strcmp(g_sqScene, g_sq.scene) || T < g_sq.lastT) sq_level_reset(P, sc, T);
    if (!P || !sc || !sq_anp_level()) { g_sqQn = 0; return 0; }   /* silent outside ANP levels; stale commands dropped */
    if (T == g_sq.lastT) return 0;                    /* paused */
    g_sq.lastT = T;
    int st = sq_hud_state(P);
    if (st >= 2 && st <= 13 && st != 10) { g_sq.hudT = T; g_sq.hudSeen = 1; }
    DWORD now = GetTickCount();
    int live = g_sqc.mode == SQ_ON && g_sqBuild == 1;
    /* M01: Dead Men refuses every order there (DM sets the flag for "M01A_Main") */
    if (live && !g_sq.refuseSet && sq_refuse_rule()) {
        g_sq.refuseSet = 1;
        if (!rd8(sc + 0xa0) && god_writable(sc + 0xa0, 1)) { *(sc + 0xa0) = 1; sq_log("refuse flag sc+0xa0 = 1 (%s): every order is refused, as in Dead Men", g_sqScene); }
    }
    /* critical=clear: a merc's death does not fail the mission (data writes on script+0x513 only) */
    sq_crit_tick();
    /* recruitment (DM: every merc is under Kane's control; DD story mode recruits nobody) */
    sq_recruit_scan(P, sc, T, live, now);
    if (g_sqDead) return 0;
    /* probe: 3 s after the player appears, then again when the receiver / squad counts change (max 6 per level) */
    int nr = sq_nrecv(sc), nm = sq_nmem(sq_squad(sc));
    if (now - g_sq.t0 >= 3000 && g_sq.probes < 6 && (nr != g_sq.probeRecv || nm != g_sq.probeSq)) {
        g_sq.probes++; g_sq.probeRecv = nr; g_sq.probeSq = nm;
        sq_probe(P, sc, T);
        if (g_sqDead) return 0;
    }
    if (g_sqc.stat > 0 && now - g_sq.t0 >= 3000 && (!g_sq.statT || now - g_sq.statT >= (DWORD)g_sqc.stat * 1000)) {
        g_sq.statT = now;
        sq_stat(P, sc, T, NULL);
        if (g_sqDead) return 0;
    }
    sq_release_checks(P, sc, T, live);
    if (g_sqDead) return 0;
    sq_keys(P, sc, T);
    if (g_sqDead) return 0;
    sq_cmd_poll();
    if (g_sqQn && now >= g_sq.waitUntil) {
        char line[96]; memcpy(line, g_sqQ[g_sqQh], sizeof line); g_sqQh = (g_sqQh + 1) % 32; g_sqQn--;
        if (!_strnicmp(line, "wait", 4) && (line[4] == ' ' || line[4] == '\t' || !line[4])) {
            float s = (float)atof(line + 4); if (s < 0) s = 0; if (s > 120) s = 120;
            g_sq.waitUntil = now + (DWORD)(s * 1000.0f);
            sq_log("cmd 'wait %.1f'", (double)s);
        } else sq_cmd_exec(line, P, sc, T);
    }
    return 0;
}
static void squad_frame(void) {
    if (g_sqDead || !g_clMainTid || GetCurrentThreadId() != g_clMainTid) return;
    if (climb_guarded("squad tick", squad_tick_body, 0) < 0) sq_kill("tick", "fault (see 'climb: FAULT ... in squad tick' above)");
}
