/*
 * klmfprobe.c - [MFProbe] LOG-ONLY probe: who raises the 'MissionFailedReload' popup (kind 5, string 0xb7dfc4) in Fragile Alliance at
 * full health. Requested by peer c9 (owner of klhook), 2026-10-26. Included by klhook.c right after klanimprobe.c (uses klh_rd / klh_rd32 /
 * klh_rdstr / klh_poke / klog / klh_ini / klcam_player / kle_node). NOTHING HERE HAS RUN IN THE GAME. It never changes behaviour: each
 * detour logs, then re-executes the stolen prologue and jumps on into the game's own function with the same registers and arguments.
 *
 * SITES (prologues read from the kl2.exe FILE with capstone, 2026-10-26, build 0490; each is checked against the live bytes by klh_poke):
 *   0x8edc40  the popup function. thiscall, ecx = the popup singleton (callers: mov ecx,0x156b3b0), ONE stack argument read with
 *             movsx esi,byte [esp+0x1c] at entry = the popup KIND (a signed byte; 5 = MissionFailedReload per the task). Callers pass it with
 *             `push 0` at 0x6d25ff, so the argument is not always 5: the kind is logged as the first stack argument.
 *             stolen 6 bytes: 83 ec 0c | 53 | 55 | 56 = sub esp,0Ch; push ebx; push ebp; push esi.  back = 0x8edc46.
 *   0x6d2500  CPPScript slot-56 function (ZGeneric@CPPScript / ZCivilian@CPPScript): shows MF_01_MercDead via 0x7864f0, then calls 0x8edc40
 *             at 0x6d2606. thiscall, ecx = the script object (esi = ecx at once; [this+0x40] is called through a vtable: GUESS it is the owner
 *             entity). stolen 5 bytes: 55 | 8b ec | d9 ee = push ebp; mov ebp,esp; fldz.  back = 0x6d2505.
 *   0x5f2370  ZMissionFailed entity handler (vtable slot 26). thiscall, ecx = the entity, a word argument at [esp+4] compared with two
 *             globals. stolen 6 bytes: 80 79 35 00 | 75 6c = cmp byte [ecx+35h],0; jne 0x5f23e2 (the jne is position dependent: the stub
 *             redoes it as a jump to the absolute 0x5f23e2). back = 0x5f2376.
 * LOG LINES "mfprobe: ..." (cap MaxLines per level load, default 20 per site; a load = the game-data pointer changes or the session
 * state goes back to 0x16): time, caller (return address), ecx, the first stack arguments, session state [[0x168e598]+0x70] and game type
 * [[0x168e598]+0x5c] (the offsets as given by c9, not re-checked here), the local player's world place and health ([P+0xa48] -> +4, as
 * klcampool.c reads it), and for the script / handler the owner entity's name [[ent+4]+0x6c] and place (kle_node). Reads only (klh_rd cannot fault).
 * POLICY: a TEST build with SessionSafe=1 may patch only unhashed code; if a site is in a hashed range klh_poke refuses and this logs it
 * and goes on with the other sites. A SHIP build never patches code, so it logs the refusal and does nothing.
 * ini: [MFProbe] Enable=1 in the TEST build / 0 in SHIP (recommended on for test runs, off for players)   MaxLines=20 (per site per load, 1..200)
 */
#ifndef KLMFPROBE_C
#define KLMFPROBE_C

#define KLMF_POPUP  0x008edc40u
#define KLMF_SCRIPT 0x006d2500u
#define KLMF_HANDLR 0x005f2370u
#define KLMF_SM     0x0168e598u

static struct { int on, installed[3], dead; DWORD maxl, n[3], gd, st, tid; } klmf;
static DWORD klmf_back[3], klmf_jne;

static const BYTE klmf_x0[6] = { 0x83, 0xec, 0x0c, 0x53, 0x55, 0x56 };
static const BYTE klmf_x1[5] = { 0x55, 0x8b, 0xec, 0xd9, 0xee };
static const BYTE klmf_x2[6] = { 0x80, 0x79, 0x35, 0x00, 0x75, 0x6c };

/* "state/gametype/player" part shared by all three lines */
static void klmf_ctx(char *out, int cap)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(KLMF_SM)), P, gd = 0, node, ho; float p[3] = { 0, 0, 0 }, hv[2] = { -1, -1 }; int havep = 0;
    if ((P = klcam_player(&gd))) {
        node = klh_rd32(P + 4); havep = node && kle_node(node, p, 0);
        if ((ho = klh_rd32(P + 0xa48))) { if (!klh_rd(ho + 4, hv, 8)) hv[0] = -1; }
    }
    _snprintf(out, cap - 1, "t=%lu ms state[+0x70]=%lx gametype[+0x5c]=%lx player=%08lx at %s(%.1f %.1f %.1f) health=%.1f",
              (unsigned long)GetTickCount(), (unsigned long)(sm ? klh_rd32(sm + 0x70) : 0), (unsigned long)(sm ? klh_rd32(sm + 0x5c) : 0),
              (unsigned long)P, havep ? "" : "n/a ", p[0], p[1], p[2], hv[0]);
    out[cap - 1] = 0;
}

/* a new level load resets the per-site caps */
static void klmf_load_check(void)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), sm = klh_rd32((DWORD_PTR)KLH_VA(KLMF_SM)), st = sm ? klh_rd32(sm + 0x70) : 0;
    if (gd != klmf.gd || (st == 0x16 && klmf.st != 0x16)) { memset(klmf.n, 0, sizeof klmf.n); klmf.gd = gd; }
    klmf.st = st;
}

/* owner entity text: " owner=%08lx vt=%08lx name='..' at (..)" for an entity pointer (GUESS: the object whose node is [ent+4]) */
static void klmf_ent(DWORD ent, char *out, int cap)
{
    char nm[64]; float p[3] = { 0, 0, 0 }; DWORD node = ent ? klh_rd32(ent + 4) : 0; int hp = node && kle_node(node, p, 0);
    nm[0] = 0;
    if (node) klh_rdstr(klh_rd32(node + 0x6c), nm, sizeof nm);
    _snprintf(out, cap - 1, "ent=%08lx vt=%08lx node=%08lx name='%s' at %s(%.1f %.1f %.1f)", (unsigned long)ent, (unsigned long)(ent ? klh_rd32(ent) : 0),
              (unsigned long)node, nm, hp ? "" : "n/a ", p[0], p[1], p[2]);
    out[cap - 1] = 0;
}

/* id 0 = popup 0x8edc40, 1 = script 0x6d2500, 2 = handler 0x5f2370; sp -> return address, sp[1..] = stack arguments */
static void __cdecl klmf_pre(DWORD id, DWORD ecx, DWORD *sp)
{
    __try {
        char c[400], e[300], e2[300];
        if (!klmf.on || klmf.dead || id > 2) return;
        klmf_load_check();
        if (klmf.n[id] >= klmf.maxl) return;
        klmf.n[id]++;
        klmf_ctx(c, sizeof c);
        if (id == 0)
            klog("mfprobe: POPUP 0x8edc40 #%lu caller=%08lx ecx=%08lx kind(arg0)=%ld args=%08lx %08lx %08lx %08lx | %s", (unsigned long)klmf.n[id],
                 (unsigned long)sp[0], (unsigned long)ecx, (long)(signed char)(sp[1] & 0xff), (unsigned long)sp[1], (unsigned long)sp[2], (unsigned long)sp[3], (unsigned long)sp[4], c);
        else if (id == 1) {
            DWORD owner = klh_rd32(ecx + 0x40);
            klmf_ent(ecx, e, sizeof e); klmf_ent(owner, e2, sizeof e2);
            klog("mfprobe: SCRIPT 0x6d2500 #%lu caller=%08lx this: %s | [this+0x40] (owner?): %s | %s", (unsigned long)klmf.n[id], (unsigned long)sp[0], e, e2, c);
        } else {
            BYTE b34 = 0xff, b35 = 0xff;
            klh_rd(ecx + 0x34, &b34, 1); klh_rd(ecx + 0x35, &b35, 1);
            klmf_ent(ecx, e, sizeof e);
            klog("mfprobe: HANDLER 0x5f2370 #%lu caller=%08lx arg0=%08lx [ecx+0x34]=%02x [ecx+0x35]=%02x this: %s | %s", (unsigned long)klmf.n[id], (unsigned long)sp[0],
                 (unsigned long)sp[1], (unsigned)b34, (unsigned)b35, e, c);
        }
        if (klmf.n[id] == klmf.maxl) klog("mfprobe: site %lu reached MaxLines=%lu for this load - silent until the next load", (unsigned long)id, (unsigned long)klmf.maxl);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        klmf.dead = 1;
    }
}

/* the stubs: save everything, call klmf_pre(id, ecx, &retaddr), restore, re-run the stolen bytes, go on */
static void __declspec(naked) klmf_hook0(void)
{
    __asm {
        pushfd
        pushad
        lea eax, [esp + 0x24]
        push eax
        push ecx
        push 0
        call klmf_pre
        add esp, 12
        popad
        popfd
        sub esp, 0x0c
        push ebx
        push ebp
        push esi
        jmp dword ptr [klmf_back]
    }
}
static void __declspec(naked) klmf_hook1(void)
{
    __asm {
        pushfd
        pushad
        lea eax, [esp + 0x24]
        push eax
        push ecx
        push 1
        call klmf_pre
        add esp, 12
        popad
        popfd
        push ebp
        mov ebp, esp
        fldz
        jmp dword ptr [klmf_back + 4]
    }
}
static void __declspec(naked) klmf_hook2(void)
{
    __asm {
        pushfd
        pushad
        lea eax, [esp + 0x24]
        push eax
        push ecx
        push 2
        call klmf_pre
        add esp, 12
        popad
        popfd
        cmp byte ptr [ecx + 0x35], 0
        je cont
        jmp dword ptr [klmf_jne]
    cont:
        jmp dword ptr [klmf_back + 8]
    }
}

static int klmf_site(int i, DWORD va, const BYTE *expect, int n, void *stub, const char *what)
{
    BYTE cur[8], jmp[8]; DWORD rel;
    if (!klh_rd((DWORD_PTR)KLH_VA(va), cur, n)) { klog("mfprobe: cannot read %s - site skipped", what); return 0; }
    if (memcmp(cur, expect, n)) {
        klog("mfprobe: prologue at %s differs from build 0490 (%02x %02x %02x %02x %02x %02x) - NOT patched", what, cur[0], cur[1], cur[2], cur[3], cur[4], n > 5 ? cur[5] : 0);
        return 0;
    }
    klmf_back[i] = (DWORD)(DWORD_PTR)KLH_VA(va + n);
    rel = (DWORD)((BYTE *)stub - (KLH_VA(va) + 5));
    memset(jmp, 0x90, sizeof jmp); jmp[0] = 0xe9; memcpy(jmp + 1, &rel, 4);
    if (!klh_poke(KLH_VA(va), expect, n, jmp, n, what)) {
        klog("mfprobe: patch at %s NOT made (refused by the patch guard - a SHIP build never patches code, and a hashed range is refused - or the bytes changed)", what);
        return 0;
    }
    klmf.installed[i] = 1;
    return 1;
}

static void klmf_init(void)
{
#ifdef KLHOOK_TEST
    int def = 1;
#else
    int def = 0;
#endif
    int k = 0;
    memset(&klmf, 0, sizeof klmf);
    klmf.on = GetPrivateProfileIntA("MFProbe", "Enable", def, klh_ini) != 0;
    klmf.maxl = (DWORD)GetPrivateProfileIntA("MFProbe", "MaxLines", 20, klh_ini);
    if (klmf.maxl < 1) klmf.maxl = 1;
    if (klmf.maxl > 200) klmf.maxl = 200;
    if (!klmf.on) return;
    if (!klh_exe_ok) { klog("mfprobe: not the known kl2.exe - probe off"); klmf.on = 0; return; }
    klmf_jne = (DWORD)(DWORD_PTR)KLH_VA(0x005f23e2u);
    k += klmf_site(0, KLMF_POPUP,  klmf_x0, sizeof klmf_x0, klmf_hook0, "popup 0x8edc40");
    k += klmf_site(1, KLMF_SCRIPT, klmf_x1, sizeof klmf_x1, klmf_hook1, "script 0x6d2500");
    k += klmf_site(2, KLMF_HANDLR, klmf_x2, sizeof klmf_x2, klmf_hook2, "handler 0x5f2370");
    klog("mfprobe: on (LOG ONLY, recommended on for test runs, off for players): %d of 3 sites detoured (popup / script / ZMissionFailed handler), max %lu lines per site per load", k, (unsigned long)klmf.maxl);
    if (!k) klmf.on = 0;
}

#endif
