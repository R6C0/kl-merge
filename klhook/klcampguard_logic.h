/* klcampguard_logic.h - the decision logic of klcampguard.c ([CampGuard]), pure C, no windows.h, tested by klcampguard_test.c.
 *
 * Ported from luvsic's a-newer-perspective loader/anp_loader.c @32aa649 (in contribution with luvsic): the CEG-safe exact-site
 * crash guards (cl_guard / gfx_guard / coll_guard / snd_guard / generic divide guard / null sound-list guard / boneslights_guard,
 * anp_loader.c ~160-290 and ~1287-1465) and loader/heapguard.inc (heap_guard). Every site number, signature and stack offset
 * below is READ from his code; every signature was also MEASURED against the on-disk kl2.exe (build 0490, 2026-11-09, read-only):
 * all of them match byte for byte.
 *
 * What a guard is: on a first-chance exception at ONE exact address, with ONE exact register / stack / code-byte situation, the
 * context is edited so the game carries on at a point that the game's own code treats as "nothing found / failed". Anything that
 * does not match every condition returns 0 here and falls through to KLHook's normal crash / assert accounting untouched.
 * No kl2.exe code byte is changed (SHIP / CEG safe): the guard only reads code bytes to prove it is at the right site, and writes
 * stack, heap and .data only.
 *
 * klcg_decide() never touches the process: it reads through klcg_mem (the real one wraps klh_rd, the test one is a byte map) and
 * returns what to change in a klcg_act, which klcampguard.c applies.
 */
#ifndef KLCAMPGUARD_LOGIC_H
#define KLCAMPGUARD_LOGIC_H

#define KLCG_AV     0xC0000005u                  /* EXCEPTION_ACCESS_VIOLATION */
#define KLCG_BP     0x80000003u                  /* EXCEPTION_BREAKPOINT */
#define KLCG_DIV0   0xC0000094u                  /* EXCEPTION_INT_DIVIDE_BY_ZERO */

/* the sites; each belongs to ONE group = one ini key (default 0) */
enum { KLCG_NONE = 0, KLCG_CL_BUCKET, KLCG_CL_SLOT, KLCG_GFX, KLCG_COLL, KLCG_COLL_CALL, KLCG_SND, KLCG_DIVRANGE,
       KLCG_NULLLIST, KLCG_BONES, KLCG_HEAP, KLCG_NSITE };
enum { KLCG_G_LISTUSER = 1, KLCG_G_GFX = 2, KLCG_G_COLL = 4, KLCG_G_SND = 8, KLCG_G_SNDDIV = 16, KLCG_G_NULLLIST = 32,
       KLCG_G_BONES = 64, KLCG_G_HEAP = 128 };

static unsigned klcg_group(int site)
{
    switch (site) {
    case KLCG_CL_BUCKET: case KLCG_CL_SLOT: return KLCG_G_LISTUSER;
    case KLCG_GFX: return KLCG_G_GFX;
    case KLCG_COLL: case KLCG_COLL_CALL: return KLCG_G_COLL;
    case KLCG_SND: return KLCG_G_SND;
    case KLCG_DIVRANGE: return KLCG_G_SNDDIV;
    case KLCG_NULLLIST: return KLCG_G_NULLLIST;
    case KLCG_BONES: return KLCG_G_BONES;
    case KLCG_HEAP: return KLCG_G_HEAP;
    }
    return 0;
}
static const char *klcg_name(int site)
{
    static const char *n[KLCG_NSITE] = { "-", "CListUser bucket walk 0x4f8a8e..9e", "CListUser bucket slot 0x4f8a6e", "ZGraphic template int3 0x51f1a9",
        "collision callback 0x927b4c/4e", "collision callback call 0x927b59", "stream rate 0 div 0x44668b", "sound-range div by zero",
        "null sound list 0x900ff8", "v4BonesLights 0x577e08", "heap block unlink int3 0x4665dc" };
    return site > 0 && site < KLCG_NSITE ? n[site] : "?";
}

typedef struct {                                   /* reads of the process; 1 = ok, 0 = unreadable */
    void *u;
    int (*rdn)(void *u, unsigned addr, void *out, int n);
} klcg_mem;

typedef struct {                                   /* the exception */
    unsigned code, at, nparam, info0, info1;       /* ExceptionCode / ExceptionAddress / NumberParameters / Information[0..1] */
    unsigned eip;
    unsigned reg[8];                               /* eax ecx edx ebx esp ebp esi edi */
} klcg_in;
enum { KLCG_EAX, KLCG_ECX, KLCG_EDX, KLCG_EBX, KLCG_ESP, KLCG_EBP, KLCG_ESI, KLCG_EDI };

typedef struct {                                   /* what to change; regset bit r = reg[r] replaces the register */
    int site;
    unsigned eip, regset, reg[8];
    unsigned zeroAt, zeroN;                        /* memory to zero (heap / stack of the game) */
    unsigned npoke; struct { unsigned a, v; } poke[4];
    unsigned i0, i1;                               /* two numbers for the log line (CListUser: return address, record id) */
} klcg_act;

static int klcg_rd32(const klcg_mem *m, unsigned a, unsigned *v) { return m->rdn(m->u, a, v, 4); }
static int klcg_code(const klcg_mem *m, unsigned at, const unsigned char *b, int n)
{   /* the code at 'at' is exactly b[0..n) */
    unsigned char t[32]; int i;
    if (n > 32 || !m->rdn(m->u, at, t, n)) return 0;
    for (i = 0; i < n; i++) if (t[i] != b[i]) return 0;
    return 1;
}

/* return addresses allowed at the CListUser removal 0x4f8a60 (luvsic's g_clRets) */
static const unsigned klcg_clrets[] = { 0x5a9b89, 0x5edad2, 0x5edb07, 0x61ee1a, 0x6307ed, 0x630811, 0x6308a8, 0x63090f, 0x630931 };
static int klcg_clret_ok(unsigned r)
{
    unsigned i;
    for (i = 0; i < sizeof klcg_clrets / sizeof klcg_clrets[0]; i++) if (klcg_clrets[i] == r) return 1;
    return 0;
}

static void klcg_act_init(klcg_act *a, int site, unsigned eip) { unsigned i; a->site = site; a->eip = eip; a->regset = 0; a->zeroAt = a->zeroN = a->npoke = 0; a->i0 = a->i1 = 0; for (i = 0; i < 8; i++) a->reg[i] = 0; }
static void klcg_setreg(klcg_act *a, int r, unsigned v) { a->regset |= 1u << r; a->reg[r] = v; }
static void klcg_poke(klcg_act *a, unsigned addr, unsigned v) { if (a->npoke < 4) { a->poke[a->npoke].a = addr; a->poke[a->npoke].v = v; a->npoke++; } }

/* ---- CListUser 0x4f8a60 (this = ecx, key = [esp+..]): remove a value from the hash chain [this+0x20][key].
   The chain walk reads (cmp [edx],esi at 0x4f8a8e / 0x4f8a92 / 0x4f8a97 / 0x4f8a9e) a bucket head that is not a node (the key was 0 or garbage,
   so 'edx' is the table's own header word, e.g. 0x4f09 in the owner's DM03 crash of 2026-11-09 16:46: debug/notes/2026-11-09-dm03-fedrespawn-crash.md).
   Resume = 0x4f8b40 (xor eax,eax; pop ebx; pop esi; pop ebp; pop ecx; ret 0xc) = the function's own "not found" return.
   WHAT THE RESUME SKIPS: the removal of that one value from its chain. The chain walk only READ before the fault (no write), so the table is not
   half-edited; but the value stays linked in whatever bucket it is really in, and the caller (0x630700, a per-frame list walk) believes it was not
   in the table. GUESS: a stale link only matters if that value is freed later while still linked; then a later walk of the same bucket reads freed
   memory. For the DM03 respawn crash the record that carried id 0 was already released, so the leftover is the record's old chain entry. Not benched. */
static int klcg_cl(const klcg_mem *m, const klcg_in *in, klcg_act *a)
{
    static const unsigned char pro[8] = { 0x51, 0x8b, 0x54, 0x24, 0x08, 0x89, 0x0c, 0x24 };          /* 0x4f8a60: push ecx; mov edx,[esp+8]; mov [esp],ecx */
    static const unsigned char resume[9] = { 0x33, 0xc0, 0x5b, 0x5e, 0x5d, 0x59, 0xc2, 0x0c, 0x00 };  /* 0x4f8b40 */
    static const unsigned char slot[2] = { 0x8b, 0x11 };                                              /* 0x4f8a6e: mov edx,[ecx] */
    static const unsigned char tail[4] = { 0x59, 0xc2, 0x0c, 0x00 };                                  /* 0x4f8b45: pop ecx; ret 0xc */
    unsigned sp[8], ret, id;
    if (in->code != KLCG_AV || in->nparam < 2 || in->at != in->eip || in->info0 != 0) return 0;
    if (in->eip == 0x4f8a6e) {
        /* bucket SLOT read (ecx = base + id*4) unreadable. Only ecx (this) is pushed here: [esp] this, +4 ret. */
        if (in->info1 != in->reg[KLCG_ECX] || !klcg_code(m, 0x4f8a60, pro, 8) || !klcg_code(m, 0x4f8a6e, slot, 2) || !klcg_code(m, 0x4f8b45, tail, 4)) return 0;
        if (!m->rdn(m->u, in->reg[KLCG_ESP], sp, 12) || !klcg_clret_ok(sp[1])) return 0;
        klcg_act_init(a, KLCG_CL_SLOT, 0x4f8b45); klcg_setreg(a, KLCG_EAX, 0); a->i0 = sp[1]; a->i1 = sp[2];
        return KLCG_CL_SLOT;
    }
    if (in->eip != 0x4f8a8e && in->eip != 0x4f8a92 && in->eip != 0x4f8a97 && in->eip != 0x4f8a9e) return 0;
    if (in->info1 < in->reg[KLCG_EDX] || in->info1 >= in->reg[KLCG_EDX] + 0x10) return 0;   /* the fault is a read of the bucket head [edx..edx+0xf], before any write */
    if (!klcg_code(m, 0x4f8a60, pro, 8) || !klcg_code(m, 0x4f8b40, resume, 9)) return 0;
    /* stack: [esp] ebx, +4 esi, +8 ebp, +0xc this, +0x10 return address, +0x14 key (record id), +0x18 value, +0x1c flag */
    if (!m->rdn(m->u, in->reg[KLCG_ESP], sp, 0x18)) return 0;
    ret = sp[4]; id = sp[5];
    if (!klcg_clret_ok(ret)) return 0;
    klcg_act_init(a, KLCG_CL_BUCKET, 0x4f8b40); klcg_setreg(a, KLCG_EAX, 0); a->i0 = ret; a->i1 = id;
    return KLCG_CL_BUCKET;
}

/* ---- ZGraphic::Init 0x51f180: int3 at 0x51f1a9 when the graphic template (this+0x8c) cannot be instantiated (eax = 0).
   luvsic resumes in a stub (graphic_fail_stub) that first retries with a fallback graphic of Dead Men's menu resources (Background / Line_Long_01#01 ...)
   and only then fails. NOT PORTED: the retry. This is his stub's FAIL branch only: zero the 0x19-byte result at the first argument, pop edi / esi / ebx,
   drop the 0x10 locals and return (ret 0x10). WHAT IT SKIPS: the template lookup result, so the graphic object stays empty (nothing is drawn for it).
   Stack at the int3: [esp] edi, +4 esi, +8 ebx, +0xc..0x1b the 0x10 locals, +0x1c return address, +0x20 arg1 = result struct, +0x24.. the other 3 args. */
static int klcg_gfx(const klcg_mem *m, const klcg_in *in, klcg_act *a)
{
    static const unsigned char site[5] = { 0x3b, 0xc3, 0x75, 0x01, 0xcc };             /* 0x51f1a5: cmp eax,ebx; jne +1; int3 */
    unsigned sp[10], t;
    if (in->code != KLCG_BP || in->at != 0x51f1a9 || (in->eip != 0x51f1a9 && in->eip != 0x51f1aa) || in->reg[KLCG_EAX] != 0) return 0;
    if (!klcg_code(m, 0x51f1a5, site, 5) || !m->rdn(m->u, in->reg[KLCG_ESP], sp, 0x28)) return 0;
    if (!m->rdn(m->u, sp[8], &t, 4) || !m->rdn(m->u, sp[8] + 0x18, &t, 1)) return 0;     /* the result struct is writable memory we can reach */
    if (sp[7] < 0x401000 || sp[7] >= 0xb10000) return 0;                                  /* a return address inside .text */
    klcg_act_init(a, KLCG_GFX, sp[7]);
    klcg_setreg(a, KLCG_EDI, sp[0]); klcg_setreg(a, KLCG_ESI, sp[1]); klcg_setreg(a, KLCG_EBX, sp[2]);
    klcg_setreg(a, KLCG_ESP, in->reg[KLCG_ESP] + 0x30);                                   /* 3 pops + 0x10 locals + return address + 0x10 of args (ret 0x10) */
    a->zeroAt = sp[8]; a->zeroN = 0x19;
    a->i0 = sp[7];
    return KLCG_GFX;
}

/* ---- collision octree callback 0x927b30: handle [esi+0x4c] resolved by 0x8ccde0 (ebx), then call [[ebx]+0x2e8]. A handle that resolves to NULL, to an object
   without a readable vtable, or to a wrong class whose slot 0x2e8 is not code, faults at 0x927b4c (mov edx,[ebx]), 0x927b4e (mov eax,[edx+0x2e8]) or at the
   call target itself. Resume = the callback's "skip" return (0x927b5f: pop edi; pop esi; xor al,al; pop ebx; add esp,0x18; ret) / al = 1 at 0x927b5b.
   WHAT IT SKIPS: this one record's collision callback (that record is not tested). A wrong-class object with a CALLABLE slot is not caught. */
static int klcg_coll(const klcg_mem *m, const klcg_in *in, klcg_act *a)
{
    static const unsigned char site[11] = { 0x8b, 0x13, 0x8b, 0x82, 0xe8, 0x02, 0x00, 0x00, 0x83, 0xc4, 0x04 };   /* 0x927b4c */
    unsigned s0;
    if (in->code != KLCG_AV || in->nparam < 2) return 0;
    if ((in->eip == 0x927b4c && in->at == in->eip && in->info0 == 0 && in->info1 == in->reg[KLCG_EBX]) ||
        (in->eip == 0x927b4e && in->at == in->eip && in->info0 == 0 && in->info1 == in->reg[KLCG_EDX] + 0x2e8)) {
        if (!klcg_code(m, 0x927b4c, site, 11) || !m->rdn(m->u, in->reg[KLCG_ESP], &s0, 4)) return 0;
        klcg_act_init(a, KLCG_COLL, 0x927b5f);
        klcg_setreg(a, KLCG_ESP, in->reg[KLCG_ESP] + 4);                  /* the pushed handle (add esp,4 at 0x927b54 not run yet) */
        a->i0 = in->reg[KLCG_EBX];
        return KLCG_COLL;
    }
    if (in->at == in->eip && in->info1 == in->eip && in->reg[KLCG_ECX] == in->reg[KLCG_EBX]) {   /* call eax at 0x927b59 into a non-executable target */
        if (!m->rdn(m->u, in->reg[KLCG_ESP], &s0, 4) || s0 != 0x927b5b || !klcg_code(m, 0x927b4c, site, 11)) return 0;
        klcg_act_init(a, KLCG_COLL_CALL, 0x927b5b);
        klcg_setreg(a, KLCG_ESP, in->reg[KLCG_ESP] + 4);                  /* the call's return address */
        klcg_setreg(a, KLCG_EAX, (in->reg[KLCG_EAX] & ~0xffu) | 1);       /* al = 1 -> skip */
        a->i0 = in->eip;
        return KLCG_COLL_CALL;
    }
    return 0;
}

/* ---- streamed-sound setup: div ebp at 0x44668b with ebp = 0 ([esp+0x1c] = the stream's sample rate, 0 for an unconverted Dead Men record).
   Resume = re-run mul/shr/div from 0x446673 with rate 22050 (eax = 0xcccccccd as set at 0x44666b). WHAT IT CHANGES: that stream is set up as 22050 Hz. */
static int klcg_snd(const klcg_mem *m, const klcg_in *in, klcg_act *a)
{
    static const unsigned char site[6] = { 0x8b, 0x6c, 0x24, 0x1c, 0xf7, 0xe5 };      /* 0x446673 */
    static const unsigned char dv[2] = { 0xf7, 0xf5 };                                /* 0x44668b: div ebp */
    unsigned rate;
    if (in->code != KLCG_DIV0 || in->eip != 0x44668b || in->at != 0x44668b || in->reg[KLCG_EBP] != 0) return 0;
    if (!m->rdn(m->u, in->reg[KLCG_ESP] + 0x1c, &rate, 4) || rate != 0) return 0;
    if (!klcg_code(m, 0x446673, site, 6) || !klcg_code(m, 0x44668b, dv, 2)) return 0;
    klcg_act_init(a, KLCG_SND, 0x446673);
    klcg_poke(a, in->reg[KLCG_ESP] + 0x1c, 22050);
    klcg_setreg(a, KLCG_EAX, 0xcccccccdu);
    return KLCG_SND;
}

/* ---- any other divide by zero in the sound code range 0x446600..0x4b3000 (luvsic: unconverted Dead Men sound records): divisor -> 1, the same instruction re-runs.
   Forms: div [esp+disp8] (f7 74 24 d) and div reg (f7 f0+r). Tightened vs his: the divisor must really be 0, edx must be 0 (so a quotient overflow cannot
   fault again forever) and eax / edx / esp are not touched as divisors. */
static int klcg_divrange(const klcg_mem *m, const klcg_in *in, klcg_act *a)
{
    unsigned char ip[4]; unsigned v;
    if (in->code != KLCG_DIV0 || in->at != in->eip || in->eip < 0x446600 || in->eip >= 0x4b3000 || in->reg[KLCG_EDX] != 0) return 0;
    if (!m->rdn(m->u, in->eip, ip, 4) || ip[0] != 0xf7) return 0;
    if (ip[1] == 0x74 && ip[2] == 0x24) {
        unsigned at = in->reg[KLCG_ESP] + ip[3];
        if (!m->rdn(m->u, at, &v, 4) || v != 0) return 0;
        klcg_act_init(a, KLCG_DIVRANGE, in->eip); klcg_poke(a, at, 1);
        return KLCG_DIVRANGE;
    }
    if ((ip[1] & 0xf8) == 0xf0) {
        int r = ip[1] & 7;
        if (r == KLCG_EAX || r == KLCG_EDX || r == KLCG_ESP || in->reg[r] != 0) return 0;
        klcg_act_init(a, KLCG_DIVRANGE, in->eip); klcg_setreg(a, r, 1);
        return KLCG_DIVRANGE;
    }
    return 0;
}

/* ---- sound-list GetEntry 0x900ff0 (ret 4) called with rec (ecx) NULL: an audio definition whose .SND offset is not a sound list of this level's bank.
   Resume = return 0 ("no such entry") to the caller, which already handles it: eax = 0, eip = [esp], esp += 8. Nothing is pushed before 0x900ff8. */
static int klcg_nulllist(const klcg_mem *m, const klcg_in *in, klcg_act *a)
{
    static const unsigned char site[4] = { 0x66, 0x3b, 0x41, 0x18 };                   /* cmp ax,[ecx+0x18] */
    unsigned ret;
    if (in->code != KLCG_AV || in->eip != 0x900ff8 || in->at != 0x900ff8 || in->reg[KLCG_ECX] != 0 || in->info0 != 0) return 0;
    if (!klcg_code(m, 0x900ff8, site, 4) || !m->rdn(m->u, in->reg[KLCG_ESP], &ret, 4)) return 0;
    if (ret < 0x401000 || ret >= 0xb10000) return 0;
    klcg_act_init(a, KLCG_NULLLIST, ret); klcg_setreg(a, KLCG_EAX, 0); klcg_setreg(a, KLCG_ESP, in->reg[KLCG_ESP] + 8);
    a->i0 = ret;
    return KLCG_NULLLIST;
}

/* ---- v4BonesLights shader constant 0x7d3dd0 (case 0x46, 0x7d57c2): edi = [renderCtx+0x3d0] (a 0x70-byte light block; 0x20 = "no lights" = null object + 0x20),
   0 when a skinned / rigid material is drawn before anything wrote it; the vec3*mat3 helper 0x577df0 then reads [edx] = [0] at 0x577e08.
   Fix: hand the call a zeroed light block (edx / edi / the cache at 0xf1b244) and set ctx+0x3d0 = 0x20 so later draws take the no-lights path; re-run the instruction.
   WHAT IT CHANGES: that draw (and later ones until a real light block is written) is lit with all-zero lights. Stack check: [esp+0xc] = 0x7d57ec (the return into the case). */
static int klcg_bones(const klcg_mem *m, const klcg_in *in, klcg_act *a, unsigned nolights)
{
    static const unsigned char site[3] = { 0xd9, 0x02, 0xd8 };                         /* 0x577e08: fld [edx]; fmul ... */
    unsigned st[5], ctx, v;
    if (in->code != KLCG_AV || in->eip != 0x577e08 || in->at != 0x577e08 || in->info0 != 0 || in->info1 != 0 || in->reg[KLCG_EDX] != 0 || in->reg[KLCG_EDI] != 0) return 0;
    if (!m->rdn(m->u, in->reg[KLCG_ESP], st, 0x14) || st[3] != 0x7d57ec || !klcg_code(m, 0x577e08, site, 3)) return 0;
    ctx = in->reg[KLCG_ESI] - 0x9c;                                                     /* 0x7d57c8: add esi,0x9c */
    if (!m->rdn(m->u, ctx + 0x3d0, &v, 4) || v != 0) return 0;
    klcg_act_init(a, KLCG_BONES, in->eip);
    klcg_setreg(a, KLCG_EDX, nolights); klcg_setreg(a, KLCG_EDI, nolights);
    klcg_poke(a, 0xf1b244, nolights); klcg_poke(a, ctx + 0x3d0, 0x20);
    a->i0 = ctx;
    return KLCG_BONES;
}

/* ---- ZWin32Allocator block unlink 0x466590: int3 at 0x4665dc when the header magic [ptr-0x10] != 0x12345678 (luvsic heapguard.inc: 7 of 19 dumps 11-13 Oct, a
   ZFFActor teardown freeing its ZLNKOBJ+0x88 render instance). Sole caller ZWin32Allocator::Free 0x882c30 (call at 0x882c7f, ret 0x882c85, tail 0x882c9b).
   Resume = 0x882c9b with esp += 8 = Free's normal successful return (al = 1). WHAT IT SKIPS: unlink + HeapFree of ONE block: it is leaked (0x3bc bytes for an
   instance), the allocator's block list is not touched. */
static int klcg_heap(const klcg_mem *m, const klcg_in *in, klcg_act *a)
{
    static const unsigned char unlink[15] = { 0x8b, 0x44, 0x24, 0x04, 0x83, 0xc0, 0xf0, 0x81, 0x38, 0x78, 0x56, 0x34, 0x12, 0x75, 0x3d };   /* 0x466590 */
    static const unsigned char site[2] = { 0xcc, 0xc3 };                                /* 0x4665dc */
    static const unsigned char call[6] = { 0x51, 0xe8, 0x0b, 0x39, 0xbe, 0xff };        /* 0x882c7f */
    static const unsigned char tail[6] = { 0xb0, 0x01, 0x5e, 0xc2, 0x04, 0x00 };        /* 0x882c9b */
    unsigned sp[13], mg;
    if (in->code != KLCG_BP || in->at != 0x4665dc || (in->eip != 0x4665dc && in->eip != 0x4665dd)) return 0;
    if (!m->rdn(m->u, in->reg[KLCG_ESP], sp, 0x34) || sp[0] != 0x882c85 || in->reg[KLCG_EAX] != sp[1] - 0x10) return 0;
    if (!klcg_code(m, 0x466590, unlink, 15) || !klcg_code(m, 0x4665dc, site, 2) || !klcg_code(m, 0x882c7f, call, 6) || !klcg_code(m, 0x882c9b, tail, 6)) return 0;
    if (!m->rdn(m->u, in->reg[KLCG_EAX], &mg, 4) || mg == 0x12345678u) return 0;      /* the header really is bad (it was read by the cmp that led here) */
    klcg_act_init(a, KLCG_HEAP, 0x882c9b); klcg_setreg(a, KLCG_ESP, in->reg[KLCG_ESP] + 8);
    a->i0 = sp[1]; a->i1 = mg;
    return KLCG_HEAP;
}

/* The one entry point. mask = groups the ini switched on. Returns the site id (0 = not ours / not exact / group off). */
static int klcg_decide(const klcg_mem *m, const klcg_in *in, unsigned mask, unsigned nolights, klcg_act *a)
{
    int s = 0;
    if (!mask) return 0;
    if (in->code == KLCG_AV) {
        if ((mask & KLCG_G_LISTUSER) && (s = klcg_cl(m, in, a)) != 0) return s;
        if ((mask & KLCG_G_COLL) && (s = klcg_coll(m, in, a)) != 0) return s;
        if ((mask & KLCG_G_NULLLIST) && (s = klcg_nulllist(m, in, a)) != 0) return s;
        if ((mask & KLCG_G_BONES) && (s = klcg_bones(m, in, a, nolights)) != 0) return s;
    } else if (in->code == KLCG_BP) {
        if ((mask & KLCG_G_GFX) && (s = klcg_gfx(m, in, a)) != 0) return s;
        if ((mask & KLCG_G_HEAP) && (s = klcg_heap(m, in, a)) != 0) return s;
    } else if (in->code == KLCG_DIV0) {
        if ((mask & KLCG_G_SND) && (s = klcg_snd(m, in, a)) != 0) return s;
        if ((mask & KLCG_G_SNDDIV) && (s = klcg_divrange(m, in, a)) != 0) return s;
    }
    return 0;
}

/* Log at the 1st hit and at every power of two after (one line per site per doubling). */
static int klcg_log_now(long n) { return n >= 1 && (n <= 3 || (n & (n - 1)) == 0); }

#endif
