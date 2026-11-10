/* klcutlog.c - [Campaign] CutsceneLog: READ-ONLY diagnostic of the Dead Men campaign cutscenes (2026-11-10, branch campaign-cutlog-1110). OFF by default
 * ("(recommended off; diagnostic)"). Included by klhook.c right after klcampgive.c (uses klcmp_level_active, klcsq_player / klcsq_body /
 * KLCSQ_MERC_LIST of klcampsquad.c, klh_rd / klh_rd32 / klh_rdstr / klh_scene / klh_poke / klh_policy / klog). NOTHING HERE HAS RUN IN THE GAME.
 *
 * WHY: in campaign cutscenes the characters wave their guns about. Our give code is refuted as the cause; the script's weaponhdl parser (0x8bccb0) and
 * executor (0x4db080 -> 0x4d5c20) are identical in both exes; about 450 level-specific DM gesture acts carry no weaponhdl at all. Which acts run, with
 * which mode, and which game flag is set ONLY during a cutscene is unknown: this log is meant to show it. NO BEHAVIOUR CHANGE: no write into game
 * memory, every detour call passes straight through.
 *
 * WHAT IT LOGS (all lines "cutlog: ..." in KLHook.log; every line goes through one rate limit, [Campaign] CutsceneLogMax per level and
 * CutsceneLogRate per second, one "line cap" notice per level, the skipped count at the level end):
 *   SIGNAL  an EDGE of a cutscene-candidate flag (read ~20 times a second, game thread), with the whole signal row on the same line:
 *     player   a local ZFFPlayer exists (0 = loading / frontend / dead pointer)               klcsq_player()
 *     blk2728  byte [P+0x2728]   \  the input-block test of klcampsquad.c klcsq_blocked() (READ in luvsic's sq_gate);
 *     blk2760  dword [P+0x2760]  /  may also be set at pause / death / load: the log shows when
 *     gd4cd8   byte [[0xdd265c]+0x4cd8]   the pause / cut flag the camera tick tests at 0x6500e3 (ASSUMPTION of klcam.c)
 *     gd48b0   dword [[0xdd265c]+0x48b0]  tested by the holster routine 0x5e7c60 at 0x5e7c8d (MEASURED: it is read there; meaning unknown)
 *     sysbc    byte [[[0xdd2640]+0xac]+0xbc]  the "system byte" klcam.c logs (meaning unknown)
 *     camvt    vtable dword of the player's camera object [P+0xbd8]  (a scripted camera class would show up here; ZFFCamera1 = 0xbb76a4)
 *     move     [[P+0x6b4]+0x44]  the movement kind of the current movement (klcam / climb.md)
 *     able     byte [P+0x576]  the soldier "able" byte klcsq_able() reads on mercs (GUESS that it is the same field on the player: death shows here)
 *     gs       dword [0xe0e644] game-state counter (CONTEXT only: its changes are not edges)
 *   ACTOR   the holster state of the local player and every merc of the merc list (0x1548fd8) CHANGED between two polls:
 *           bit100 = [A+0xbbc] & 0x100 (set by weaponhdl Holster through 0x5e7c60), the whole dword bbc, hand = [A+0x920] (GUESS: klauto.c),
 *           wpn = the inventory's weapon for that hand index (klauto.c kla_hand_weapon rule; inventory [A+0xcec]: mode +4, entries at [+8] of 16 bytes, count +0xc).
 *           Works in the SHIP dll (data reads only).
 *   EXEC / ACT  every call of the act executor (DETOURS, see below): ACT = 0x4db080 with the act pointer, its owner, actor id, anim id, clip path,
 *           weaponhdl mode, the actor and the hand state before / after; EXEC = 0x4d5c20 (the weaponhdl executor, called by the ACT and by 5 other sites).
 *
 * CALLING CONVENTIONS (MEASURED, kl2.exe build 0490 disassembly, 2026-11-10):
 *   0x4db080  thiscall, ecx = the act runner (only stored), ONE stack arg = the act record, callee pops it (ret 4). Prologue 55 8b ec 83 ec 74 (6 bytes, whole instructions).
 *             The one caller is 0x7ce86f (push esi = the act, mov ecx, edi). Act record: +0x0c actor id, +0x10 owner (the actor list is the vector at [owner+0x20]: begin / end
 *             pointers, element +4 = id; the lookup is 0x818060, replicated here read-only), +0x24 signed word anim id (0x59d550 picks a clip variant from it with the
 *             game's own random numbers: NOT called here), +0x40 the weaponhdl mode (0 = none: the call to 0x4d5c20 is skipped), +0x44 the start position.
 *             The actor object O = the vector element; O+0x20 = the actor body A.
 *   0x4d5c20  thiscall, ecx = O (O+0x20 = actor body A, O+0x24 = the last mode, written here), ONE stack arg = mode, callee pops it (ret 4). Prologue 55 8b ec 56 57 8b 7d 08
 *             (8 bytes, whole instructions). Jump table 0x4d5d64: mode 1 -> 0x5e7c60(A, 1, 0x100) (Holster: [A+0xbbc] |= 0x100), 2 -> clears the bit and selects the
 *             stashed item, 3 / 4 -> clear the bit only when an inventory item is found (0x566f20 with 1 / 0). Callers: 0x4db0b1, 0x5149d8, 0x60a416, 0x6db162, 0x78f230, 0x7cd4e0.
 *   The anim "clip path" is NOT stored in the act record under a known offset: the log tries (GUESS) the dwords at act+0..0x7c as pointers to a text starting with '/' and any
 *   inline text of the record; when none is found it prints '?'. The anim id is always printed, so the path can be looked up offline from the level's script.
 *
 * THE DETOURS ARE NOT POSSIBLE IN A SESSION (MEASURED in klranges.h): 0x4d5c20 lies in the hashed range 0x4d5000-0x4da000 and 0x4db080 in 0x4db000-0x4dd000, ranges
 * kl2.exe's integrity checks hash; a SHIP dll writes no code at all (klh_may_write), a TEST dll with SessionSafe=1 is refused for hashed bytes, and a debug register is refused too
 * (klauto.c kla_watch_apply: kl2.exe's anti-tamper ends the process, SP2 11-01). So EXEC / ACT lines exist ONLY in a TEST dll run with [KLHook] SessionSafe=0 (direct boot,
 * not a session: the patch guard logs the hashed-range note). In every other run the log says once "detours: not made" and the SIGNAL / ACTOR polls do the work.
 * The detour is klanimprobe.c's scheme: a 5-byte jump to a stub that saves the registers, calls kcut_pre(ecx, site, &returnaddress), re-executes the stolen prologue and jumps
 * back; the return address is replaced by kcut_post_stub (a LIFO of up to 16 pending returns matched by their stack slot, so a call that never returns cannot misdirect a later one),
 * which logs the line with the after state and returns to the real caller. Game thread only.
 *
 * KEYS ([Campaign], read by this module; the master [Campaign] Enable=1 and a campaign scene gate everything, klcampaign_gate.h):
 *   CutsceneLog=0 (recommended off; diagnostic)   CutsceneLogMax=600 (lines per level, 20..20000)   CutsceneLogRate=25 (lines per second, 1..200)
 */
#ifndef KLCUTLOG_C
#define KLCUTLOG_C
#include "klcutlog_logic.h"

#define KCUT_SITE_EXEC  0x004d5c20u
#define KCUT_SITE_ACT   0x004db080u
#define KCUT_N_EXEC     8
#define KCUT_N_ACT      6
#define KCUT_MAXA       20
#define KCUT_PEND       16
#define KCUT_POLL_MS    50

typedef struct { int site; DWORD t, slot, caller, A, O, act, owner, id, aid, mode, last; kcut_actor before; char clip[100]; } kcut_pe;
static struct {
    int on, active, dead, hooked, told, haveSig, nact;
    unsigned seq; DWORD tid, t0, poll, nExec, nAct, lastSkipped;
    kcut_rl rl; char scene[100];
    kcut_sig sig; kcut_actor act[KCUT_MAXA];
    kcut_pe pend[KCUT_PEND]; int np;
} kcutS;
static DWORD kcut_back_exec, kcut_back_act;

static unsigned long kcut_ms(void) { return (unsigned long)(GetTickCount() - kcutS.t0); }

/* every line passes here: the per-level cap and the per-second rate (klcutlog_logic.h) */
static void kcut_say(const char *s)
{
    int t = kcut_rl_take(&kcutS.rl, GetTickCount());
    if (t == KCUT_SAY) klog("%s", s);
    else if (t == KCUT_CAP) klog("cutlog: line cap (%u per level) reached: silent until the next level (the poll goes on counting)", kcutS.rl.maxLines);
}

/* the actor body's name (GUESS, klprobe.c klpr_name): [[A+4]+0x6c] is a C string */
static void kcut_name(DWORD A, char *out, int cap)
{
    char t[48]; DWORD n, s;
    out[0] = 0;
    if (!A || !(n = klh_rd32(A + 4)) || !(s = klh_rd32(n + 0x6c)) || !klh_rdstr(s, t, sizeof t)) return;
    kcut_safe_copy(out, cap, (const unsigned char *)t, (int)sizeof t);
}

/* an actor's holster / hand state: READ-ONLY. hand [A+0x920] and the inventory walk are klauto.c's (GUESS for a non-player body: a failed read leaves them 0) */
static void kcut_read_actor(DWORD A, kcut_actor *o)
{
    DWORD inv, arr = 0, cnt = 0; BYTE mode = 0; unsigned ent[4 * 64];
    memset(o, 0, sizeof *o); o->body = A;
    if (!A || !klh_rd(A + 0xbbc, &o->bbc, 4)) return;
    o->ok = 1;
    klh_rd(A + 0x920, &o->hand, 4);
    if (!o->hand || o->hand >= 64 || !(inv = klh_rd32(A + 0xcec))) return;
    if (!klh_rd(inv + 4, &mode, 1) || !klh_rd(inv + 8, &arr, 4) || !klh_rd(inv + 0xc, &cnt, 4) || !arr || cnt > 64) return;
    if (!klh_rd(arr, ent, cnt * 16)) return;
    o->wpn = kcut_hand_pick(o->hand, mode, ent, cnt);
}

/* ---------------------------------------------------------------- the signals */
static void kcut_read_sig(kcut_sig *s)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), P = klcsq_player(), cam, mv, sys, a; BYTE b;
    memset(s, 0, sizeof *s);
    s->v[KCUT_S_HASP] = P != 0;
    if (P) {
        b = 0; klh_rd(P + 0x2728, &b, 1); s->v[KCUT_S_BLK28] = b;
        s->v[KCUT_S_BLK60] = klh_rd32(P + 0x2760);
        cam = klh_rd32(P + 0xbd8); s->v[KCUT_S_CAMVT] = cam ? klh_rd32(cam) : 0;
        mv = klh_rd32(P + 0x6b4); s->v[KCUT_S_MOVE] = mv ? klh_rd32(mv + 0x44) : 0;
        b = 0; klh_rd(P + 0x576, &b, 1); s->v[KCUT_S_ABLE] = b;
    }
    if (gd) { b = 0; klh_rd(gd + 0x4cd8, &b, 1); s->v[KCUT_S_G4CD8] = b; s->v[KCUT_S_G48B0] = klh_rd32(gd + 0x48b0); }
    if ((sys = klh_rd32((DWORD_PTR)KLH_VA(0xdd2640))) && (a = klh_rd32(sys + 0xac))) { b = 0; klh_rd(a + 0xbc, &b, 1); s->v[KCUT_S_SYSBC] = b; }
    s->v[KCUT_S_GS] = klh_rd32((DWORD_PTR)KLH_VA(0xe0e644));
}

/* ---------------------------------------------------------------- the actors (local player + the merc list) */
static void kcut_poll_actors(DWORD P, const char *row)
{
    DWORD body[KCUT_MAXA]; int nb = 0, i, j, nl; char line[420], nm[48]; kcut_actor cur; int seen[KCUT_MAXA];
    if (P) body[nb++] = P;
    nl = (int)klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST)); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (i = 0; i < nl && nb < KCUT_MAXA; i++) {
        DWORD s = klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST) + 4 + 4 * i), b = s ? klcsq_body(s) : 0, dup = 0;
        for (j = 0; j < nb; j++) dup |= body[j] == b;
        if (b && !dup) body[nb++] = b;
    }
    memset(seen, 0, sizeof seen);
    for (i = 0; i < nb; i++) {
        int idx = -1;
        for (j = 0; j < kcutS.nact; j++) if (kcutS.act[j].body == body[i]) { idx = j; break; }
        kcut_read_actor(body[i], &cur);
        if (idx < 0) {                                  /* first sight in this level */
            if (kcutS.nact >= KCUT_MAXA) continue;
            idx = kcutS.nact++; kcutS.act[idx] = cur; seen[idx] = 1;
            kcut_name(body[i], nm, sizeof nm);
            kcut_f(line, sizeof line, "cutlog: TRACK t=%lu.%03lus %s%08x '%s' bit100 %d bbc %08x hand %u wpn %08x", kcut_ms() / 1000ul, kcut_ms() % 1000ul, body[i] == P ? "player " : "", body[i],
                   nm[0] ? nm : "?", kcut_holstered(&cur), cur.bbc, cur.hand, cur.wpn);
            kcut_say(line);
            continue;
        }
        seen[idx] = 1;
        if (!cur.ok) continue;                          /* an unreadable body keeps its last state */
        if (kcut_actor_changed(&kcutS.act[idx], &cur)) {
            kcut_name(body[i], nm, sizeof nm);
            kcut_fmt_actor_edge(line, sizeof line, ++kcutS.seq, kcut_ms(), body[i], nm, body[i] == P, &kcutS.act[idx], &cur, row);
            kcut_say(line);
            kcutS.act[idx] = cur;
        }
    }
    for (i = j = 0; i < kcutS.nact; i++) if (seen[i]) kcutS.act[j++] = kcutS.act[i];      /* an actor that left the list is forgotten (a new sight = a new TRACK line) */
    kcutS.nact = j;
}

/* ---------------------------------------------------------------- the tick (game thread) */
static void kcut_level_begin(const char *sc)
{
    kcut_rl_level(&kcutS.rl);
    kcutS.t0 = GetTickCount(); kcutS.nact = 0; kcutS.haveSig = 0; kcutS.seq = 0; kcutS.nExec = kcutS.nAct = 0;
    strncpy(kcutS.scene, sc, sizeof kcutS.scene - 1); kcutS.scene[sizeof kcutS.scene - 1] = 0;
    klog("cutlog: campaign level '%s': logging (max %u lines, %u per second; detours %s)", kcutS.scene, kcutS.rl.maxLines, kcutS.rl.perSec, kcutS.hooked ? "ON (TEST direct run)" : "not made: SIGNAL / ACTOR polls only");
}
static void kcut_level_end(void)
{
    if (kcutS.active) klog("cutlog: campaign level '%s' left after %lu.%03lus: %u lines said, %u skipped by the rate limit / cap, ACT calls %lu, EXEC calls %lu", kcutS.scene, kcut_ms() / 1000ul, kcut_ms() % 1000ul,
                          kcutS.rl.count, kcutS.rl.skipped, (unsigned long)kcutS.nAct, (unsigned long)kcutS.nExec);
    kcutS.active = 0; kcutS.scene[0] = 0; kcutS.haveSig = 0; kcutS.nact = 0;
}

static void kcut_tick(int game_thread)
{
    DWORD now; kcut_sig s; char sc[100], row[200], edges[200], line[460]; int n;
    if (!kcutS.on || !game_thread || kcutS.dead) return;
    kcutS.tid = GetCurrentThreadId();
    now = GetTickCount();
    if (now - kcutS.poll < KCUT_POLL_MS) return;
    kcutS.poll = now;
    if (!klcmp_level_active() || !klh_scene(sc, sizeof sc)) { kcut_level_end(); return; }
    if (!kcutS.active || strcmp(sc, kcutS.scene)) { kcut_level_end(); kcutS.active = 1; kcut_level_begin(sc); }
    kcut_read_sig(&s);
    kcut_sig_row(&s, row, sizeof row);
    if (!kcutS.haveSig) { kcut_fmt_sig_edge(line, sizeof line, ++kcutS.seq, kcut_ms(), "baseline", row); kcut_say(line); }
    else if ((n = kcut_sig_edges(&kcutS.sig, &s, edges, sizeof edges)) > 0) { kcut_fmt_sig_edge(line, sizeof line, ++kcutS.seq, kcut_ms(), edges, row); kcut_say(line); }
    kcutS.sig = s; kcutS.haveSig = 1;
    kcut_poll_actors(klcsq_player(), row);
    if (kcutS.rl.skipped - kcutS.lastSkipped >= 500) { kcutS.lastSkipped = kcutS.rl.skipped; klog("cutlog: %u lines skipped so far in this level (rate limit / cap)", kcutS.rl.skipped); }
}

/* ---------------------------------------------------------------- the detours (TEST dll, direct boot only) */
/* the act's actor object O: the vector at [owner+0x20] (begin, end), element +4 == id (0x818060, replicated read-only) */
static DWORD kcut_lookup(DWORD owner, DWORD id)
{
    DWORD b = klh_rd32(owner + 0x20), e = klh_rd32(owner + 0x24), p; int n = 0;
    if (!b || e < b || e - b > 4 * 256) return 0;
    for (p = b; p < e && n < 256; p += 4, n++) { DWORD el = klh_rd32(p); if (el && klh_rd32(el + 4) == id) return el; }
    return 0;
}
/* the act's clip path (GUESS, see the header): a pointer field that points at '/...' text, else inline text in the record */
static void kcut_clip(DWORD act, char *out, int cap)
{
    BYTE rec[0x80]; char t[100]; int i;
    out[0] = 0;
    if (!klh_rd(act, rec, sizeof rec)) return;
    for (i = 0; i + 4 <= (int)sizeof rec; i += 4) {
        DWORD v; memcpy(&v, rec + i, 4);
        if (v < 0x10000 || !klh_rdstr(v, t, sizeof t) || !kcut_looks_like_path((const unsigned char *)t, (int)sizeof t)) continue;
        kcut_safe_copy(out, cap, (const unsigned char *)t, (int)sizeof t); return;
    }
    for (i = 0; i + 5 <= (int)sizeof rec; i++) if (rec[i] == '/' && kcut_looks_like_path(rec + i, (int)sizeof rec - i)) { kcut_safe_copy(out, cap, rec + i, (int)sizeof rec - i); return; }
}

void kcut_post_stub(void);

/* the stub's call on entry: ecx, site (0 = 0x4d5c20, 1 = 0x4db080), sp -> the return address slot, sp[1] = the stack arg */
static void __cdecl kcut_pre(DWORD thisp, int site, DWORD *sp)
{
    __try {
        kcut_pe *e;
        if (!kcutS.on || kcutS.dead || !kcutS.active || GetCurrentThreadId() != kcutS.tid || kcutS.np >= KCUT_PEND) return;
        e = &kcutS.pend[kcutS.np]; memset(e, 0, sizeof *e);
        e->site = site; e->t = GetTickCount(); e->slot = (DWORD)(DWORD_PTR)sp; e->caller = sp[0];
        if (site == 0) {
            kcutS.nExec++;
            e->O = thisp; e->mode = sp[1]; e->A = klh_rd32(thisp + 0x20); e->last = klh_rd32(thisp + 0x24);
        } else {
            DWORD act = sp[1]; WORD aid = 0;
            kcutS.nAct++;
            e->act = act; e->owner = klh_rd32(act + 0x10); e->id = klh_rd32(act + 0xc); klh_rd(act + 0x24, &aid, 2); e->aid = aid;
            e->mode = klh_rd32(act + 0x40);
            e->O = e->owner ? kcut_lookup(e->owner, e->id) : 0; e->A = e->O ? klh_rd32(e->O + 0x20) : 0;
            kcut_clip(act, e->clip, sizeof e->clip);
        }
        kcut_read_actor(e->A, &e->before);
        kcutS.np++;
        sp[0] = (DWORD)(DWORD_PTR)kcut_post_stub;          /* the return comes through the post stub, which prints the line and returns to e->caller */
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        kcutS.dead = 1;
    }
}

/* called by the post stub: ret = eax of the callee, slot -> the placeholder the stub's `ret` reads the real return address from.
   Both callees pop one argument (ret 4): the placeholder sits at (entry slot + 4). */
static void __cdecl kcut_post(DWORD ret, DWORD *slot)
{
    DWORD back = 0; int i;
    (void)ret;
    for (i = kcutS.np - 1; i >= 0; i--) if (kcutS.pend[i].slot + 4 == (DWORD)(DWORD_PTR)slot) break;
    if (i >= 0) {
        kcut_pe e = kcutS.pend[i];
        back = e.caller; kcutS.np = i;                       /* the entry and everything above it (calls that never returned) are done */
        __try {
            kcut_actor after; char line[520], nm[48];
            kcut_read_actor(e.A, &after); kcut_name(e.A, nm, sizeof nm);
            if (e.site == 0) kcut_fmt_exec(line, sizeof line, ++kcutS.seq, kcut_ms(), e.O, e.A, nm, e.mode, e.last, &e.before, &after, 1, 1);
            else kcut_fmt_act(line, sizeof line, ++kcutS.seq, kcut_ms(), e.act, e.owner, e.id, e.aid, e.clip, e.mode, e.A, nm, &e.before, &after, 1);
            kcut_say(line);
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            kcutS.dead = 1;
        }
    } else kcutS.dead = 1;                                   /* cannot happen: only kcut_pre sets the replaced return; back stays 0 only if the list was lost */
    *slot = back;
}

/* the stubs: save, call kcut_pre(ecx, site, &retaddr), restore, run the stolen prologue, go on */
static void __declspec(naked) kcut_hook_exec(void)
{
    __asm {
        pushfd
        pushad
        lea eax, [esp + 0x24]
        push eax
        push 0
        push ecx
        call kcut_pre
        add esp, 12
        popad
        popfd
        push ebp
        mov ebp, esp
        push esi
        push edi
        mov edi, dword ptr [ebp + 8]
        jmp dword ptr [kcut_back_exec]
    }
}
static void __declspec(naked) kcut_hook_act(void)
{
    __asm {
        pushfd
        pushad
        lea eax, [esp + 0x24]
        push eax
        push 1
        push ecx
        call kcut_pre
        add esp, 12
        popad
        popfd
        push ebp
        mov ebp, esp
        sub esp, 0x74
        jmp dword ptr [kcut_back_act]
    }
}
void __declspec(naked) kcut_post_stub(void)
{
    __asm {
        push 0
        pushfd
        pushad
        lea ecx, [esp + 0x24]
        mov eax, dword ptr [esp + 0x1c]
        push ecx
        push eax
        call kcut_post
        add esp, 8
        popad
        popfd
        ret
    }
}

static int kcut_patch(DWORD va, const BYTE *expect, int n, void *stub, DWORD *back, const char *what)
{
    BYTE jmp[8]; DWORD rel; int i;
    rel = (DWORD)((BYTE *)stub - (KLH_VA(va) + 5));
    jmp[0] = 0xe9; memcpy(jmp + 1, &rel, 4); for (i = 5; i < n; i++) jmp[i] = 0x90;
    *back = (DWORD)(DWORD_PTR)KLH_VA(va + (DWORD)n);
    return klh_poke(KLH_VA(va), expect, n, jmp, n, what);
}

static void kcut_init(void)
{
    static const BYTE ex[KCUT_N_EXEC] = { 0x55, 0x8b, 0xec, 0x56, 0x57, 0x8b, 0x7d, 0x08 }, ac[KCUT_N_ACT] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x74 };
    BYTE cur[8];
    kcutS.on = GetPrivateProfileIntA("Campaign", "CutsceneLog", 0, klh_ini) != 0;
    if (!kcutS.on) return;                                         /* off: nothing read, nothing patched, no log line */
    kcut_rl_init(&kcutS.rl, GetPrivateProfileIntA("Campaign", "CutsceneLogMax", 600, klh_ini), GetPrivateProfileIntA("Campaign", "CutsceneLogRate", 25, klh_ini));
    klog("cutlog: ON (READ-ONLY diagnostic, NOT benched; campaign levels only, needs [Campaign] Enable=1): max %u lines per level, %u per second; polls signals / holster state of the player and the mercs",
         kcutS.rl.maxLines, kcutS.rl.perSec);
    if (klh_policy != KLH_DIRECT) {
        klog("cutlog: detours NOT made (patch policy '%s'): 0x4d5c20 and 0x4db080 lie in ranges kl2.exe hashes and a session / SHIP dll writes no code - no EXEC / ACT lines, only SIGNAL / ACTOR (a TEST dll with [KLHook] SessionSafe=0 would add them)", klh_policy_name[klh_policy]);
        return;
    }
    if (!klh_rd((DWORD_PTR)KLH_VA(KCUT_SITE_EXEC), cur, KCUT_N_EXEC) || memcmp(cur, ex, KCUT_N_EXEC) || !klh_rd((DWORD_PTR)KLH_VA(KCUT_SITE_ACT), cur, KCUT_N_ACT) || memcmp(cur, ac, KCUT_N_ACT)) {
        klog("cutlog: the prologues of 0x4d5c20 / 0x4db080 differ from build 0490: detours NOT made, polls only");
        return;
    }
    if (kcut_patch(KCUT_SITE_EXEC, ex, KCUT_N_EXEC, (void *)kcut_hook_exec, &kcut_back_exec, "cutlog: jump at the top of the weaponhdl executor 0x4d5c20 (log only)") &&
        kcut_patch(KCUT_SITE_ACT, ac, KCUT_N_ACT, (void *)kcut_hook_act, &kcut_back_act, "cutlog: jump at the top of the act executor 0x4db080 (log only)")) {
        kcutS.hooked = 1; klog("cutlog: detours made on 0x4d5c20 and 0x4db080 (direct boot; every call passes through)");
    } else klog("cutlog: detour refused by the patch guard (or the bytes changed): polls only (if only the first jump was made it stays, calls pass through, no line is logged for a site that has no stub)");
}
#endif
