/*
 * klbotdeath.c - [BotDeathProbe] LOG-ONLY probe: what takes a team-2 'Ally' bot from thousands of hp to dead in one go online (BO6, host and client).
 * Requested by the BO6 research (workflow wtskh0rvx follow-up), 2026-10-26. Included by klhook.c right after klmfprobe.c (uses klh_rd / klh_rd32 /
 * klh_avt / klh_poke / klog / klh_ini / KLE_ENTS). NOTHING HERE HAS RUN IN THE GAME. It never changes behaviour: each detour logs (or only
 * records into a ring), then re-executes the stolen prologue and jumps on into the game's own function with the same registers and arguments.
 *
 * SAMPLING (game thread, every 250 ms while the session state [[0x168e598]+0x70] == 0x19): one line per tick for every team-2 ZFFActor
 * (team = [[actor+0x54]+4] == 2, actor list refreshed by a table scan every 3 s) with
 *   hp=cur/max   health object [actor+0x5fc] +4 / +8        r=  +0x14 (regen timing)       acc=  [actor+0x600] (hex, float)
 *   do=          DO = [actor+0x8d8] (GUESS: the DDL_ZFFActor of re/bots_online_sync.md 0x68b070 'DO=[actor+0x8d8]'; if the pointer is 0 the DO columns are 0)
 *   h16=         int16 DO+0xfe m_iHitPoints         g=  the 16 bytes DO+0xf4..0x103 (m_GeneralData, hex)
 *   b576=        byte [actor+0x576] (read at 0x8473c3)    ss= *[[actor+0x77c]+0x6d8] = the soldier state read by 0x688190 (6 = special) (GUESS: 0x688190's
 *                this is the soldier object [actor+0x77c], which klbotfill.c uses as the soldier; 0 if unreadable)
 * and on a cur>0 -> cur<=0 transition one "DEAD" line plus up to 5 ring events of that actor from the last 4 s (the writers, see SITES).
 *
 * SITES (prologues read from the kl2.exe FILE with capstone, 2026-10-26, build 0490; each is checked against the live bytes by klh_poke; the
 * UNHASHED ones only - 0x792bc0 (slot 412) and 0x8473a0 (damage compute) are in a hashed range of klranges.h, so they are NOT detoured; the
 * caller chain at 0x61efd0 (return 0x792bd3 -> ret2 = the caller of slot 412) replaces the first):
 *   id0 0x61efd0  health write (the only writer: damage, regen, kills). thiscall, ecx = health object, ONE stack float = the new value at sp[1].
 *                 stolen 5 bytes: 51 56 8b f1 57 = push ecx; push esi; mov esi,ecx; push edi.  back = 0x61efd5.  Owner actor = [ecx+0x24].
 *                 Only DECREASES (new < cur) of team-2 owners are ring-recorded (regen is skipped); a line is logged when new<=0 or the drop is >= 20% of max.
 *   id1 0x61a980  ProjectileHit handler (actor slot 423). thiscall, ecx = the victim actor, the hit record at sp[1] (the same record that 0x61acc6 scales with
 *                 fmul [ebx+0x18]). stolen 6 bytes: 81 ec d0 00 00 00 = sub esp,0D0h.  back = 0x61a986.  Logs the record words +0, +4, +8, +0x18 (the
 *                 scale), +0x1c, +0x28 (raw damage) - the offsets are the research's (GUESS +4 / +0x1c).
 *   id2 0x4bd540  the soldier death routine (zeroes the actor's health through vtbl 0x670 at 0x4bd569). thiscall, ecx = the soldier, actor = [ecx+0x40].
 *                 stolen 6 bytes: 55 8b ec 83 ec 10 = push ebp; mov ebp,esp; sub esp,10h.  back = 0x4bd546.
 *   id3 0x688190  soldier slot 51 (down-or-die decision). thiscall, ecx = the soldier, actor = [ecx+0x40] (GUESS, same as 0x4bd540; else ecx).
 *                 stolen 9 bytes: 55 8b ec 8b 81 d8 06 00 00 = push ebp; mov ebp,esp; mov eax,[ecx+6D8h].  back = 0x688199.
 *   id4 0x8edaf0  the refill to max (writes [ecx+4] = [ecx+8] and calls the listener 0x8ab200). thiscall, ecx = the health object, owner [ecx+0x24].
 *                 stolen 7 bytes: d9 41 08 51 d9 59 04 = fld [ecx+8]; push ecx; fstp [ecx+4].  back = 0x8edaf7.
 *   None of the stolen bytes is position dependent. A hashed or changed site is refused by klh_poke and logged; the others still go in. A SHIP build never
 *   patches code, so with Enable=1 there it only samples (no hooks). The hooks act only while 0x13 <= state <= 0x1f.
 * LOG LINES (cap MaxLines per site per level load, ring events and samples are separate; a load = the game-data pointer changes or the state goes back to 0x16):
 *   bd: S t=<ms> role=<[sm+0x54]> st=<state> n=<bots> | [<actor> hp=<cur>/<max> r=<f> acc=<hex>(<f>) do=<DO> h16=<int> g=<4 dwords> b576=<hex> ss=<hex>] ...
 *   bd: HPWRITE #n t=<ms> actor=<a> team=2 cur=<f> new=<f> max=<f> caller=<ret0> ret2=<ret of slot 412's caller or 0> fr1=<[ebp+4]> fr2=<[[ebp]+4]>
 *   bd: HIT #n t=<ms> victim=<a> hp=<cur>/<max> rec=<ptr> w0=<attacker> w4=<> w8=<kind> scale(+0x18)=<f> w1c=<> dmg(+0x28)=<f> caller=<ret0> fr1=<> fr2=<>
 *   bd: ZERO #n / SLOT51 #n  (id2 / id3): soldier=<ecx> actor=<a> team hp=<cur>/<max> caller=<ret0> fr1 fr2
 *   bd: REFILL #n  (id4): health obj, owner actor, cur/max, caller
 *   bd: DEAD t=<ms> actor=<a> last hp=<f> now=<f>  followed by "bd:   ev <age ms> ago <site> cur=<f> new=<f> ..." (up to 5, newest first)
 * ini: [BotDeathProbe] Enable=1 in the TEST build / 0 in SHIP (recommended on for test runs, off for players)   MaxLines=60 (per site per load, 1..500)
 *   MaxSamples=2400 (sample lines per load, 0 = none, 1..20000)
 */
#ifndef KLBOTDEATH_C
#define KLBOTDEATH_C

#define KLBDP_NSITE  5
#define KLBDP_NBOT   16
#define KLBDP_NRING  512

typedef struct { DWORD actor, tick, site, r0, r1, f1, f2; float cur, nw, mx; DWORD w[6]; } klbdp_ev;
typedef struct { DWORD actor; float prev; int dead; } klbdp_bot;

static struct { int on, installed[KLBDP_NSITE], dead, act; DWORD maxl, maxs, n[KLBDP_NSITE], ns, gd, st, ring_i; int nb; } klbdp;
static klbdp_bot klbdp_b[KLBDP_NBOT];
static klbdp_ev klbdp_ring[KLBDP_NRING];
static DWORD klbdp_back[KLBDP_NSITE];

static const BYTE klbdp_x0[5] = { 0x51, 0x56, 0x8b, 0xf1, 0x57 };
static const BYTE klbdp_x1[6] = { 0x81, 0xec, 0xd0, 0x00, 0x00, 0x00 };
static const BYTE klbdp_x2[6] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x10 };
static const BYTE klbdp_x3[9] = { 0x55, 0x8b, 0xec, 0x8b, 0x81, 0xd8, 0x06, 0x00, 0x00 };
static const BYTE klbdp_x4[7] = { 0xd9, 0x41, 0x08, 0x51, 0xd9, 0x59, 0x04 };

static const char *const klbdp_sname[KLBDP_NSITE] = { "HPWRITE", "HIT", "ZERO", "SLOT51", "REFILL" };

static float klbdp_f(DWORD v) { float f; memcpy(&f, &v, 4); return f; }

/* team of a ZFFActor (klh_avt like klbotfill.c), 99 = not an actor / unreadable */
static DWORD klbdp_team(DWORD a)
{
    DWORD pr, team = 99;
    if (a < 0x10000 || klh_avt(a) != 0x00bb3bacu) return 99;
    if (!(pr = klh_rd32(a + 0x54)) || !klh_rd(pr + 4, &team, 4)) return 99;
    return team;
}

static void klbdp_load_check(void)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598u)), st = sm ? klh_rd32(sm + 0x70) : 0;
    if (gd != klbdp.gd || (st == 0x16 && klbdp.st != 0x16)) {
        memset(klbdp.n, 0, sizeof klbdp.n); klbdp.ns = 0; klbdp.gd = gd; klbdp.nb = 0;
        memset(klbdp_ring, 0, sizeof klbdp_ring);
    }
    klbdp.st = st;
}

static void klbdp_push(DWORD actor, DWORD site, DWORD r0, DWORD r1, DWORD f1, DWORD f2, float cur, float nw, float mx, const DWORD *w)
{
    klbdp_ev *e = &klbdp_ring[(DWORD)InterlockedIncrement((volatile LONG *)&klbdp.ring_i) % KLBDP_NRING];
    e->actor = actor; e->tick = GetTickCount(); e->site = site; e->r0 = r0; e->r1 = r1; e->f1 = f1; e->f2 = f2; e->cur = cur; e->nw = nw; e->mx = mx;
    if (w) memcpy(e->w, w, sizeof e->w); else memset(e->w, 0, sizeof e->w);
}

/* sp -> return address, sp[1..] = stack arguments; ebp = the caller's frame pointer at entry */
static void __cdecl klbdp_pre(DWORD id, DWORD ecx, DWORD *sp, DWORD ebp)
{
    __try {
        DWORD actor = 0, team, hobj = 0, r0 = sp[0], r1 = 0, f1, f2, w[6] = { 0, 0, 0, 0, 0, 0 }; float cur = -1, mx = -1, nw = -1; int logit = 0;
        if (!klbdp.on || klbdp.dead || id >= KLBDP_NSITE || !klbdp.act) return;
        if (id == 0 || id == 4) {
            DWORD v;
            hobj = ecx; actor = klh_rd32(hobj + 0x24);
            if (!klh_rd(hobj + 4, &cur, 4)) return;
            klh_rd(hobj + 8, &mx, 4);
            if (id == 0) { v = sp[1]; nw = klbdp_f(v); if (!(nw < cur - 0.01f)) return; }      /* regen / no change: not recorded */
            else nw = mx;
        } else if (id == 1) {
            actor = ecx; w[0] = klh_rd32(sp[1] ? sp[1] : 0);
        } else {
            actor = klh_rd32(ecx + 0x40);
            if (klbdp_team(actor) == 99) actor = ecx;
        }
        if ((team = klbdp_team(actor)) != 2) return;
        if (!hobj) { hobj = klh_rd32(actor + 0x5fc); if (hobj) { klh_rd(hobj + 4, &cur, 4); klh_rd(hobj + 8, &mx, 4); } }
        if (id == 0 && r0 == (DWORD)(DWORD_PTR)KLH_VA(0x792bd3u)) r1 = klh_rd32((DWORD_PTR)&sp[2]);
        f1 = klh_rd32(ebp + 4); f2 = klh_rd32(klh_rd32(ebp) + 4);
        if (id == 1) {
            DWORD rec = sp[1];
            w[0] = klh_rd32(rec); w[1] = klh_rd32(rec + 4); w[2] = klh_rd32(rec + 8); w[3] = klh_rd32(rec + 0x18); w[4] = klh_rd32(rec + 0x1c); w[5] = klh_rd32(rec + 0x28);
        }
        klbdp_push(actor, id, r0, r1, f1, f2, cur, nw, mx, w);
        if (id == 0) logit = (nw <= 0 && cur > 0) || (mx > 0 && cur - nw >= 0.2f * mx); else if (id == 1) logit = klbdp.n[1] < 20 || klbdp_f(w[3]) >= 5.0f || klbdp_f(w[3]) <= -5.0f;   /* every hit is in the ring; the log keeps the first 20 and any big scale (point blank = 100) so ordinary bullets do not eat MaxLines */
        else logit = 1;
        if (!logit || klbdp.n[id] >= klbdp.maxl) return;
        klbdp.n[id]++;
        if (id == 0)
            klog("bd: HPWRITE #%lu t=%lu actor=%08lx team=2 cur=%.1f new=%.1f max=%.1f caller=%08lx ret2=%08lx fr1=%08lx fr2=%08lx", (unsigned long)klbdp.n[id], (unsigned long)GetTickCount(),
                 (unsigned long)actor, cur, nw, mx, (unsigned long)r0, (unsigned long)r1, (unsigned long)f1, (unsigned long)f2);
        else if (id == 1)
            klog("bd: HIT #%lu t=%lu victim=%08lx hp=%.1f/%.1f rec=%08lx w0=%08lx w4=%08lx w8(kind)=%08lx scale(+18)=%.2f w1c=%08lx dmg(+28)=%.2f caller=%08lx fr1=%08lx fr2=%08lx",
                 (unsigned long)klbdp.n[id], (unsigned long)GetTickCount(), (unsigned long)actor, cur, mx, (unsigned long)sp[1], (unsigned long)w[0], (unsigned long)w[1], (unsigned long)w[2],
                 klbdp_f(w[3]), (unsigned long)w[4], klbdp_f(w[5]), (unsigned long)r0, (unsigned long)f1, (unsigned long)f2);
        else
            klog("bd: %s #%lu t=%lu this=%08lx actor=%08lx hp=%.1f/%.1f caller=%08lx fr1=%08lx fr2=%08lx", klbdp_sname[id], (unsigned long)klbdp.n[id], (unsigned long)GetTickCount(),
                 (unsigned long)ecx, (unsigned long)actor, cur, mx, (unsigned long)r0, (unsigned long)f1, (unsigned long)f2);
        if (klbdp.n[id] == klbdp.maxl) klog("bd: site %s reached MaxLines=%lu for this load - silent (ring still records) until the next load", klbdp_sname[id], (unsigned long)klbdp.maxl);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        klbdp.dead = 1;
    }
}

/* the stubs: save everything, call klbdp_pre(id, ecx, &retaddr, ebp), restore, re-run the stolen bytes, go on */
#define KLBDP_PRE(ID)     __asm pushfd     __asm pushad     __asm push ebp     __asm lea eax, [esp + 0x28]     __asm push eax     __asm push ecx     __asm push ID     __asm call klbdp_pre     __asm add esp, 16     __asm popad     __asm popfd
static void __declspec(naked) klbdp_hook0(void)
{
    KLBDP_PRE(0)
    __asm {
        push ecx
        push esi
        mov esi, ecx
        push edi
        jmp dword ptr [klbdp_back]
    }
}
static void __declspec(naked) klbdp_hook1(void)
{
    KLBDP_PRE(1)
    __asm {
        sub esp, 0xd0
        jmp dword ptr [klbdp_back + 4]
    }
}
static void __declspec(naked) klbdp_hook2(void)
{
    KLBDP_PRE(2)
    __asm {
        push ebp
        mov ebp, esp
        sub esp, 0x10
        jmp dword ptr [klbdp_back + 8]
    }
}
static void __declspec(naked) klbdp_hook3(void)
{
    KLBDP_PRE(3)
    __asm {
        push ebp
        mov ebp, esp
        mov eax, dword ptr [ecx + 0x6d8]
        jmp dword ptr [klbdp_back + 12]
    }
}
static void __declspec(naked) klbdp_hook4(void)
{
    KLBDP_PRE(4)
    __asm {
        fld dword ptr [ecx + 8]
        push ecx
        fstp dword ptr [ecx + 4]
        jmp dword ptr [klbdp_back + 16]
    }
}

static int klbdp_site(int i, DWORD va, const BYTE *expect, int n, void *stub, const char *what)
{
    BYTE cur[12], jmp[12]; DWORD rel;
    if (!klh_rd((DWORD_PTR)KLH_VA(va), cur, n)) { klog("bd: cannot read %s - site skipped", what); return 0; }
    if (memcmp(cur, expect, n)) {
        klog("bd: prologue at %s differs from build 0490 (%02x %02x %02x %02x %02x %02x) - NOT patched", what, cur[0], cur[1], cur[2], cur[3], cur[4], n > 5 ? cur[5] : 0);
        return 0;
    }
    klbdp_back[i] = (DWORD)(DWORD_PTR)KLH_VA(va + n);
    rel = (DWORD)((BYTE *)stub - (KLH_VA(va) + 5));
    memset(jmp, 0x90, sizeof jmp); jmp[0] = 0xe9; memcpy(jmp + 1, &rel, 4);
    if (!klh_poke(KLH_VA(va), expect, n, jmp, n, what)) {
        klog("bd: patch at %s NOT made (refused by the patch guard - a SHIP build never patches code, and a hashed range is refused - or the bytes changed)", what);
        return 0;
    }
    klbdp.installed[i] = 1;
    return 1;
}

static void klbdp_init(void)
{
#ifdef KLHOOK_TEST
    int def = 1;
#else
    int def = 0;
#endif
    int k = 0;
    memset(&klbdp, 0, sizeof klbdp); memset(klbdp_b, 0, sizeof klbdp_b);
    klbdp.on = GetPrivateProfileIntA("BotDeathProbe", "Enable", def, klh_ini) != 0;
    klbdp.maxl = (DWORD)GetPrivateProfileIntA("BotDeathProbe", "MaxLines", 60, klh_ini);
    klbdp.maxs = (DWORD)GetPrivateProfileIntA("BotDeathProbe", "MaxSamples", 2400, klh_ini);
    if (klbdp.maxl < 1) klbdp.maxl = 1;
    if (klbdp.maxl > 500) klbdp.maxl = 500;
    if (klbdp.maxs > 20000) klbdp.maxs = 20000;
    if (!klbdp.on) return;
    if (!klh_exe_ok) { klog("bd: not the known kl2.exe - probe off"); klbdp.on = 0; return; }
    k += klbdp_site(0, 0x0061efd0u, klbdp_x0, sizeof klbdp_x0, klbdp_hook0, "health write 0x61efd0");
    k += klbdp_site(1, 0x0061a980u, klbdp_x1, sizeof klbdp_x1, klbdp_hook1, "hit handler 0x61a980");
    k += klbdp_site(2, 0x004bd540u, klbdp_x2, sizeof klbdp_x2, klbdp_hook2, "death routine 0x4bd540");
    k += klbdp_site(3, 0x00688190u, klbdp_x3, sizeof klbdp_x3, klbdp_hook3, "slot 51 0x688190");
    k += klbdp_site(4, 0x008edaf0u, klbdp_x4, sizeof klbdp_x4, klbdp_hook4, "refill 0x8edaf0");
    klog("bd: on (LOG ONLY, recommended on for test runs, off for players): %d of %d sites detoured (0x61efd0 / 0x61a980 / 0x4bd540 / 0x688190 / 0x8edaf0; 0x792bc0 and 0x8473a0 are hashed), max %lu lines per site and %lu samples per load; sampling every 250 ms in state 0x19",
         k, KLBDP_NSITE, (unsigned long)klbdp.maxl, (unsigned long)klbdp.maxs);
}

/* the actor list: every team-2 ZFFActor of the entity table (klbotfill.c's walk); bots already known keep their last health */
static void klbdp_scan(void)
{
    DWORD p, tab, i, blk[64 * 32]; klbdp_bot nb[KLBDP_NBOT]; int n = 0, j;
    memset(nb, 0, sizeof nb);
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x10000 && n < KLBDP_NBOT; i += 64) {
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < KLBDP_NBOT; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4];
            if (o < 0x10000 || klbdp_team(o) != 2) continue;
            nb[n].actor = o; nb[n].prev = -1;
            for (j = 0; j < klbdp.nb; j++) if (klbdp_b[j].actor == o) nb[n] = klbdp_b[j];
            n++;
        }
    }
    memcpy(klbdp_b, nb, sizeof klbdp_b); klbdp.nb = n;
}

static void klbdp_dead(klbdp_bot *b, float now)
{
    DWORD t = GetTickCount(); int i, shown = 0;
    klog("bd: DEAD t=%lu actor=%08lx last hp=%.1f now=%.1f", (unsigned long)t, (unsigned long)b->actor, b->prev, now);
    for (i = 0; i < KLBDP_NRING && shown < 5; i++) {      /* newest first */
        klbdp_ev *e = &klbdp_ring[((DWORD)klbdp.ring_i - (DWORD)i + KLBDP_NRING * 4u) % KLBDP_NRING];
        if (e->actor != b->actor || e->site >= KLBDP_NSITE || t - e->tick > 4000) continue;
        shown++;
        klog("bd:   ev %lu ms ago %s cur=%.1f new=%.1f max=%.1f caller=%08lx ret2=%08lx fr1=%08lx fr2=%08lx w=%08lx %08lx %08lx %.2f %08lx %.2f", (unsigned long)(t - e->tick), klbdp_sname[e->site],
             e->cur, e->nw, e->mx, (unsigned long)e->r0, (unsigned long)e->r1, (unsigned long)e->f1, (unsigned long)e->f2, (unsigned long)e->w[0], (unsigned long)e->w[1], (unsigned long)e->w[2],
             klbdp_f(e->w[3]), (unsigned long)e->w[4], klbdp_f(e->w[5]));
    }
    if (!shown) klog("bd:   no recorded writer in the last 4 s (the health changed through a path none of the detoured sites sees, or the actor was freed)");
}

static void klbdp_tick(int game_thread)
{
    static DWORD last, scan; DWORD now = GetTickCount(), sm, st, role, DOp, i;
    char line[1400]; int pos, j;
    if (!klbdp.on || klbdp.dead || !game_thread || !klh_exe_ok || now - last < 250) return;
    last = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598u)))) { klbdp.act = 0; klbdp.nb = 0; return; }
    klbdp_load_check();
    st = klh_rd32(sm + 0x70); role = klh_rd32(sm + 0x54);
    klbdp.act = st >= 0x13 && st <= 0x1f;
    if (st != 0x19) { klbdp.nb = 0; scan = 0; return; }
    if (now - scan >= 3000) { scan = now; klbdp_scan(); }
    if (!klbdp.nb) return;
    pos = _snprintf(line, sizeof line - 1, "bd: S t=%lu role=%lu st=%lx n=%d |", (unsigned long)now, (unsigned long)role, (unsigned long)st, klbdp.nb);
    for (j = 0; j < klbdp.nb && pos > 0 && pos < (int)sizeof line - 160; j++) {
        klbdp_bot *b = &klbdp_b[j]; DWORD hp = klh_rd32(b->actor + 0x5fc), acc = klh_rd32(b->actor + 0x600), g[4] = { 0, 0, 0, 0 }, snd, ss = 0; float hv[2] = { -1, -1 }, r = 0; BYTE b576 = 0; short h16 = 0;
        if (hp) { klh_rd(hp + 4, hv, 8); klh_rd(hp + 0x14, &r, 4); }
        DOp = klh_rd32(b->actor + 0x8d8);
        if (DOp) { klh_rd(DOp + 0xf4, g, 16); klh_rd(DOp + 0xfe, &h16, 2); }
        klh_rd(b->actor + 0x576, &b576, 1);
        if ((snd = klh_rd32(b->actor + 0x77c)) && (i = klh_rd32(snd + 0x6d8))) ss = klh_rd32(i);
        { int w2 = _snprintf(line + pos, sizeof line - 1 - pos, " [%08lx hp=%.1f/%.1f r=%.1f acc=%08lx(%.2f) do=%08lx h16=%d g=%08lx,%08lx,%08lx,%08lx b576=%02x ss=%lx]", (unsigned long)b->actor,
                         hv[0], hv[1], r, (unsigned long)acc, klbdp_f(acc), (unsigned long)DOp, (int)h16, (unsigned long)g[0], (unsigned long)g[1], (unsigned long)g[2], (unsigned long)g[3], (unsigned)b576, (unsigned long)ss); if (w2 < 0) { pos = (int)sizeof line - 160; line[sizeof line - 1] = 0; } else pos += w2; }
        if (hv[0] > 0) { b->dead = 0; }
        else if (hv[0] <= 0 && hv[0] > -1 && b->prev > 0 && !b->dead) { b->dead = 1; klbdp_dead(b, hv[0]); }
        if (hv[0] > -1) b->prev = hv[0];
    }
    if (pos > 0 && klbdp.ns < klbdp.maxs) { klbdp.ns++; line[sizeof line - 1] = 0; klog("%s", line); }
}

#endif
