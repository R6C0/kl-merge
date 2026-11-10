/*
 * kldeathtrace.c - TEST-ONLY death tracer for the local player ([DeathTrace] Enable=0 default, Log=1). Part of KLHook, included by klhook.c inside
 * #ifdef KLHOOK_TEST after klclubdiag.c (uses klog, klh_rd, klh_rd32, klh_poke, klh_slot_player_mine, klh_pvt, klh_ini, KLH_VA, klfc_guard, klfc_rtti,
 * klfc_movid, klfc_cur_act, klfc_sys, klfr_p100/klfr_box/klfr_in, klpr_name, kbr_f3_emit/kbr_f3_jmp/KLBR_F3REGS). 2026-11-10.
 *
 * QUESTION (DD10 Flat Raid, slot F07): a heister running out the front from the first spawn dies at about x 9600..10000, z ~950, y 0, ~20 s into the round with
 * NO damage line. The kill text path (kl2.exe 0x500670) took the fallback 'FA_DieFromSelf' (return 0x5008dc): killer crew byte -1 and the killer entity null or
 * without a KillBox controller. Who kills him? Candidates: a no-attacker script / environment kill, the engine's level-box (out of bounds) kill, a fall kill, the
 * SWAT squads 031_StreetWest / 032_StreetMid (TriggerDelay2 20 s / 45 s). This module only LOGS; it changes nothing in the game.
 *
 * THREE LOG SOURCES
 *  (a) 'deathtrace: dmg'   entry of the actor's vtable[0x694] = kl2.exe 0x69f900 (the damage / kill entry the repo already knows, klescort.c), for the LOCAL player
 *      only (this == klh_slot_player_mine()): the record at [esp+4] (+0 attacker pointer, +8 kind, +0x28 float amount; PROVEN from the 0x69f900 disassembly 11-10,
 *      not from a live run), the attacker's class (RTTI) and node name, the return address, the player place and the first 6 return addresses of the stack.
 *  (b) 'deathtrace: text'  entry of 0x500670 (the kill text builder). The killer handle is arg4: the disassembly reads it at 0x50083c as [esp+0x8c] after the
 *      prologue; with the entry frame that is [entry esp+0x10] (arg_k at entry esp+4k, PROVEN from the disassembly, NOT from a live run). 0x8ccde0 (cdecl) turns
 *      that handle into the entity (called at 0x50084f). The log shows the handle, the entity (class + node name) or 'null'. A null entity = the FA_DieFromSelf fallback.
 *  (c) 'deathtrace: s'     the local player every 100 ms from the round start (session state [0x168e598]+0x70 == 0x19) until his health is 0: place (translation and x100),
 *      velocity, health, movement id, current action, level-box state (in / OUT / ahead-OUT = the 0x87fb30 out-of-bounds test on p100 and p100+v*dt, see below).
 *      At death the last 8 samples are written again as 'deathtrace: tail'.
 *
 * WHY THE BOX STATE: the game's own out-of-bounds kill (0x87fb30 tests p100 and p100+v*dt against the box [[sys+0xac]+0x52cc], max +0x166e0, min +0x166ec, x100
 * units, and calls YouDied 0x8ce1e0) has no attacker either. If the box says OUT (or ahead-OUT) at x ~10000 in the last samples, that is the killer. [FallRescue]
 * (default on) puts a player back before that; the bench turns it off ([FallRescue] Enable=0) to see the kill.
 *
 * HASHED SITES: 0x69f900 and 0x500670 are inside integrity-hashed ranges (klranges.h): their detours are REFUSED under [KLHook] SessionSafe=1 (the TEST default); a
 * direct-boot bench sets SessionSafe=0. When 0x500670 is refused, 0x8ccde0 (NOT hashed) is detoured instead and filtered by its return address 0x50084f, which
 * gives the same text event. The damage site has no unhashed twin: refused = (a) is silent (the log says so).
 * The detours are counting-style stubs (klbrain_logic.h kbr_f3_emit: pushad, pushfd, handler(id, regs), popfd, popad, the stolen bytes, jmp back); regs->esp is the
 * ORIGINAL esp at the site, so [esp] is the return address. Stolen bytes (checked with the disassembler, no relative operand): 0x69f900 9 bytes
 * 57 8b f9 8b 0d 98 e5 68 01 (push edi; mov edi,ecx; mov ecx,[0x168e598]); 0x500670 7 bytes 6a ff 68 09 ab ad 00 (push -1; push 0xadab09); 0x8ccde0 10 bytes
 * 8b 44 24 04 8b 0d 90 ff e0 00 (mov eax,[esp+4]; mov ecx,[0xe0ff90]).
 *
 * UNKNOWN / GUESS (each also marked where it is used):
 *  - NO 'on ground' flag of the player is known anywhere in the repo or the exe strings. The samples carry the movement id ([[P+0x6b4]+0x44]; klfreeclimb.c),
 *    the current action ([[P+0x19c]+4]), vy and p100 y instead. GUESS: movement id 2/3/8 = standing / walking / running on the ground (klfallrescue.c uses it
 *    that way); anything else with vy < 0 and y dropping = in the air.
 *  - GUESS: the stack scan finds return addresses by the call bytes before each stack word (a heuristic, a chance hit is possible).
 *  - GUESS: the image range for the scan is 0x400000..0xc00000 (the .text of kl2.exe build 0490 is below that).
 *  - GUESS: the attacker pointer at record +0 is an entity (class name + node name); it may be something else (then the RTTI line says '-').
 *  - Calling 0x8ccde0 from the hook (to resolve the handle) is a cdecl pure lookup, GUESS from its disassembly; it runs inside klfc_guard.
 *
 * KEYS: [DeathTrace] Enable=0  Log=1 (1 = lines, 0 = only a 'tail' at death)  PeriodMs=100 (50..1000)  MaxLines=1500 (sample lines)  MaxEvents=60 (dmg + text lines)
 *       needs [KLHook] SessionSafe=0 for the two hashed sites.
 */
#ifndef KLDEATHTRACE_C
#define KLDEATHTRACE_C
#include "kldeathtrace_logic.h"

#define KDT_DMG   0x0069f900u        /* actor vtable[0x694]: damage / kill entry (thiscall, arg1 = record) */
#define KDT_TXT   0x00500670u        /* kill text builder */
#define KDT_LOOK  0x008ccde0u        /* handle -> entity lookup (cdecl), called at 0x50084f */
#define KDT_LOOK_RA 0x0050084fu
#define KDT_IMG_LO 0x00400000u
#define KDT_IMG_HI 0x00c00000u       /* GUESS */

static struct { int on, log, period, installed, state[3]; long maxlines, maxevents, lines, events, text_seen, dmg_seen; DWORD t0, last, round_on, dead, gms0; int busy; kdt_ring ring; } kdt;
static BYTE *kdt_stub;
static DWORD kdt_look_arg, kdt_look_res;
static const struct { DWORD va; int len; BYTE b[10]; const char *what; } kdt_sites[3] = {
    { KDT_DMG,  9,  { 0x57, 0x8b, 0xf9, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0 },       "0x69f900 (actor damage / kill entry)" },
    { KDT_TXT,  7,  { 0x6a, 0xff, 0x68, 0x09, 0xab, 0xad, 0x00, 0, 0, 0 },             "0x500670 (kill text)" },
    { KDT_LOOK, 10, { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00 },    "0x8ccde0 (handle lookup, fallback for the text)" }
};

static DWORD kdt_rel(DWORD va) { return va ? va - (DWORD)klh_delta : 0; }      /* an address as the exe's own (the disassembly's) */

static int kdt_look_fn(void *unused)
{   /* 0x8ccde0(handle) cdecl -> entity; only inside klfc_guard */
    typedef DWORD (__cdecl *F)(DWORD);
    (void)unused; kdt_look_res = ((F)(DWORD_PTR)KLH_VA(KDT_LOOK))(kdt_look_arg); return 0;
}
static DWORD kdt_resolve(DWORD handle)
{
    kdt_look_arg = handle; kdt_look_res = 0;
    if (!handle || handle == 0xffffffffu) return 0;
    if (klfc_guard("deathtrace lookup", kdt_look_fn, 0) < 0) return 0;
    return kdt_look_res;
}
static void kdt_who(DWORD obj, char *cls, int ccap, char *nm, int ncap)
{   /* class (RTTI) and node name of a game object, '-' when none */
    const char *s;
    strcpy(cls, "-"); strcpy(nm, "-");
    if (!obj || obj < 0x10000u) return;
    klfc_rtti(obj, cls, ccap);
    if ((s = klpr_name(obj, nm, ncap)) == 0) strcpy(nm, "-");
}
static int kdt_rd6(unsigned long ra, unsigned char *six, void *ctx) { (void)ctx; return klh_rd((DWORD_PTR)(ra - 6), six, 6) ? 1 : 0; }
static void kdt_stack(DWORD esp, char *out, int cap)
{   /* the first 6 return addresses of the stack at 'esp' (exe addresses), word 0 = the caller of the site */
    unsigned long w[64], ra[6]; int n, k, o = 0; BYTE tmp[256];
    if (!klh_rd(esp, tmp, 256)) { out[0] = 0; return; }
    memcpy(w, tmp, 256);
    n = kdt_scan_stack(w, 64, (unsigned long)(DWORD_PTR)KLH_VA(KDT_IMG_LO), (unsigned long)(DWORD_PTR)KLH_VA(KDT_IMG_HI), kdt_rd6, 0, ra, 6);
    out[0] = 0;
    for (k = 0; k < n && o < cap - 12; k++) o += _snprintf(out + o, cap - o, "%s%08lx", k ? " " : "", (unsigned long)kdt_rel(ra[k]));
}

/* one sample of the local player into *s; 0 when he cannot be read */
static int kdt_sample(DWORD P, kdt_samp *s)
{
    DWORD ho, sys = klfc_sys(), W; float hv[2], dt = 0.0f, q[3]; int k;
    memset(s, 0, sizeof *s);
    s->t = GetTickCount();
    if (!klfr_p100(P, s->p100)) return 0;
    for (k = 0; k < 3; k++) s->p[k] = s->p100[k] / 100.0f;
    s->hp = ((ho = klh_rd32(P + 0xa48)) && klh_rd(ho + 4, hv, 8)) ? hv[0] : -1.0f;
    klh_rd(P + 0x808, s->v, 12);                                    /* GUESS: P+0x808 = velocity (the same read klfallrescue.c makes) */
    if (!(s->v[0] == s->v[0] && s->v[1] == s->v[1] && s->v[2] == s->v[2])) s->v[0] = s->v[1] = s->v[2] = 0;
    if (sys) klh_rd(sys + 0x50, &dt, 4);
    if (!(dt > 0.0f) || dt > 1.0f) dt = 0.0f;
    for (k = 0; k < 3; k++) q[k] = s->p100[k] + s->v[k] * dt * 3.0f;      /* the look-ahead [FallRescue] uses (Look=3) */
    W = klfr_box();
    s->box = !klfr_in(W, s->p100) ? 0 : (klfr_in(W, q) ? 1 : 2);
    s->mov = klfc_movid(P);
    return 1;
}
static const char *kdt_boxs(int b) { return b == 0 ? "OUT" : b == 2 ? "ahead-OUT" : "in"; }
static void kdt_line(const char *tag, DWORD P, const kdt_samp *s, DWORD t0)
{
    klog("deathtrace: %s t=%lu p=(%.1f %.1f %.1f) p100=(%.0f %.0f %.0f) v=(%.1f %.1f %.1f) hp=%.1f mov=%d act=%lu box=%s",
         tag, (unsigned long)(s->t - t0), (double)s->p[0], (double)s->p[1], (double)s->p[2], (double)s->p100[0], (double)s->p100[1], (double)s->p100[2],
         (double)s->v[0], (double)s->v[1], (double)s->v[2], (double)s->hp, s->mov, (unsigned long)klfc_cur_act(P), kdt_boxs(s->box));
}

static void __cdecl kdt_hit(int id, KLBR_F3REGS *r)      /* called by the stub on the game thread; reads only */
{
    DWORD esp, ra, P;
    if (!kdt.on || !r || kdt.busy) return;
    esp = r->esp; ra = klh_rd32(esp);
    kdt.busy = 1;
    if (id == 0) {                                          /* 0x69f900: damage / kill entry of an actor (ecx = the actor) */
        char cls[64], nm[96], st[120]; DWORD rec, att; float amount = 0.0f; DWORD kind; kdt_samp s;
        P = klh_slot_player_mine();
        if (!P || r->ecx != P) { kdt.busy = 0; return; }   /* the local player only */
        kdt.dmg_seen++;
        if (!kdt_take(&kdt.events, kdt.maxevents)) { kdt.busy = 0; return; }
        rec = klh_rd32(esp + 4); att = rec ? klh_rd32(rec) : 0; kind = rec ? klh_rd32(rec + 8) : 0;
        if (rec) klh_rd(rec + 0x28, &amount, 4);
        kdt_who(att, cls, sizeof cls, nm, sizeof nm);
        kdt_stack(esp, st, sizeof st);
        klog("deathtrace: dmg #%ld t=%lu amount=%.1f kind=%lu attacker=%08lx class=%s name='%s' ret=%08lx rec=%08lx stack=[%s]",
             kdt.dmg_seen, kdt.t0 ? (unsigned long)(GetTickCount() - kdt.t0) : 0ul, (double)amount, (unsigned long)kind, (unsigned long)att, cls, nm, (unsigned long)kdt_rel(ra), (unsigned long)rec, st);
        if (kdt_sample(P, &s)) kdt_line("dmg-at", P, &s, kdt.t0);
    } else {                                                /* id 1 = 0x500670 entry; id 2 = 0x8ccde0 entry (only the call at 0x50084f counts) */
        char cls[64], nm[96]; DWORD handle, ent, a1, a2, a3;
        if (id == 2 && ra != (DWORD)(DWORD_PTR)KLH_VA(KDT_LOOK_RA)) { kdt.busy = 0; return; }
        kdt.text_seen++;
        if (!kdt_take(&kdt.events, kdt.maxevents)) { kdt.busy = 0; return; }
        if (id == 1) { handle = klh_rd32(esp + 0x10); a1 = klh_rd32(esp + 4); a2 = klh_rd32(esp + 8); a3 = klh_rd32(esp + 0xc); }       /* arg4 = killer handle (see the header) */
        else         { handle = klh_rd32(esp + 4); a1 = a2 = a3 = 0; }
        ent = kdt_resolve(handle);
        kdt_who(ent, cls, sizeof cls, nm, sizeof nm);
        if (ent) klog("deathtrace: text #%ld via %s handle=%08lx entity=%08lx class=%s name='%s' (args 1..3 %08lx %08lx %08lx) ret=%08lx",
                      kdt.text_seen, id == 1 ? "0x500670" : "0x8ccde0", (unsigned long)handle, (unsigned long)ent, cls, nm, (unsigned long)a1, (unsigned long)a2, (unsigned long)a3, (unsigned long)kdt_rel(ra));
        else klog("deathtrace: text #%ld via %s handle=%08lx entity=null (-> FA_DieFromSelf fallback if no KillBox) (args 1..3 %08lx %08lx %08lx) ret=%08lx",
                  kdt.text_seen, id == 1 ? "0x500670" : "0x8ccde0", (unsigned long)handle, (unsigned long)a1, (unsigned long)a2, (unsigned long)a3, (unsigned long)kdt_rel(ra));
        {   kdt_samp s; P = klh_slot_player_mine();
            if (P && kdt_sample(P, &s)) kdt_line("text-at", P, &s, kdt.t0); }
    }
    kdt.busy = 0;
}

static void kdt_install(void)
{
    int i;
    if (!kdt_stub && !(kdt_stub = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE))) { klog("deathtrace: no memory for the stubs: off"); kdt.on = 0; return; }
    for (i = 0; i < 3; i++) {
        BYTE *at, jmp[10]; DWORD stub;
        if (i == 2 && kdt.state[1] == 1) continue;           /* the unhashed twin only when the 0x500670 detour was refused */
        kdt.state[i] = -1;
        at = KLH_VA(kdt_sites[i].va); stub = (DWORD)(DWORD_PTR)(kdt_stub + 64 * i);
        if (!kbr_f3_emit(kdt_stub + 64 * i, stub, i, (DWORD)(DWORD_PTR)kdt_hit, kdt_sites[i].b, kdt_sites[i].len, (DWORD)(DWORD_PTR)(at + kdt_sites[i].len))) continue;
        kbr_f3_jmp(jmp, (DWORD)(DWORD_PTR)at, stub, kdt_sites[i].len);
        if (klh_poke(at, kdt_sites[i].b, kdt_sites[i].len, jmp, kdt_sites[i].len, "deathtrace detour")) { kdt.state[i] = 1; klog("deathtrace: detour on %s installed", kdt_sites[i].what); }
        else klog("deathtrace: detour on %s NOT installed (refused by the patch guard - a hashed range needs [KLHook] SessionSafe=0 - or the bytes differ)", kdt_sites[i].what);
    }
}

/* called every game-thread tick by klhook.c (KLPT); one compare when off */
static void kdt_tick(int game_thread)
{
    DWORD sm, P, now; kdt_samp s;
    if (!kdt.on || !game_thread || !klh_exe_ok) return;
    if (!kdt.installed) { kdt.installed = 1; kdt_install(); if (!kdt.on) return; }      /* once, on the first game-thread tick (the image check and the patch policy are settled by then) */
    sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598));
    if (!(sm && klh_rd32(sm + 0x70) == 0x19)) {            /* round not running */
        if (kdt.round_on) { klog("deathtrace: round over after %lu ms (%ld sample lines, %ld dmg, %ld text)", (unsigned long)(GetTickCount() - kdt.t0), kdt.lines, kdt.dmg_seen, kdt.text_seen); }
        kdt.round_on = 0; return;
    }
    now = GetTickCount();
    if (!kdt.round_on) {                                    /* round start: reset */
        kdt.round_on = 1; kdt.t0 = now; kdt.last = 0; kdt.dead = 0; kdt.lines = 0; kdt.events = 0; kdt.text_seen = kdt.dmg_seen = 0; kdt_ring_clear(&kdt.ring);
        klog("deathtrace: round start (sample every %d ms, max %ld lines, %ld events; detours: dmg %d text %d look %d)", kdt.period, kdt.maxlines, kdt.maxevents, kdt.state[0], kdt.state[1], kdt.state[2]);
    }
    if (kdt.dead || !kdt_due(now, kdt.last, (unsigned long)kdt.period)) return;
    P = klh_slot_player_mine();
    if (!P || klh_pvt(P) != 0x00bb45f4u) return;
    kdt.last = now;
    if (!kdt_sample(P, &s)) return;
    if (s.hp == -1.0f) return;                              /* no health object yet */
    kdt_ring_push(&kdt.ring, &s);
    if (kdt.log && kdt_take(&kdt.lines, kdt.maxlines)) kdt_line("s", P, &s, kdt.t0);
    if (!(s.hp > 0.0f)) {                                   /* died: the last 8 samples again, oldest first */
        int k; const kdt_samp *q;
        kdt.dead = 1;
        klog("deathtrace: DEATH of the local player %lu ms into the round: tail (oldest first)", (unsigned long)(now - kdt.t0));
        for (k = 7; k >= 0; k--) if ((q = kdt_ring_back(&kdt.ring, k)) != 0) kdt_line("tail", P, q, kdt.t0);
    }
}

static void kdt_init(void)
{
    memset(&kdt, 0, sizeof kdt);
    kdt.on = GetPrivateProfileIntA("DeathTrace", "Enable", 0, klh_ini) != 0;
    if (!kdt.on) return;
    kdt.log = GetPrivateProfileIntA("DeathTrace", "Log", 1, klh_ini) != 0;
    kdt.period = (int)GetPrivateProfileIntA("DeathTrace", "PeriodMs", 100, klh_ini); if (kdt.period < 50) kdt.period = 50; if (kdt.period > 1000) kdt.period = 1000;
    kdt.maxlines = (long)GetPrivateProfileIntA("DeathTrace", "MaxLines", 1500, klh_ini); if (kdt.maxlines < 0) kdt.maxlines = 0; if (kdt.maxlines > 100000) kdt.maxlines = 100000;
    kdt.maxevents = (long)GetPrivateProfileIntA("DeathTrace", "MaxEvents", 60, klh_ini); if (kdt.maxevents < 0) kdt.maxevents = 0; if (kdt.maxevents > 10000) kdt.maxevents = 10000;
    klog("deathtrace: on (TEST, read only): Log=%d PeriodMs=%d MaxLines=%ld MaxEvents=%ld; the hashed sites 0x69f900 / 0x500670 need [KLHook] SessionSafe=0", kdt.log, kdt.period, kdt.maxlines, kdt.maxevents);
}

#endif
