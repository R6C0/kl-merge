/* klshot2d.c - [Sound] RemoteShot2D / RemoteShot2DDist (2026-10-28, wk-shot2d; re/gun_ui_sounds_1028.md section 3). kl2.exe read statically, NOT run live.
 *
 * ONLINE a remote human's gunshot is the same sound slot (4, shot_player) and group volume as your own, but it is played 3D with distance falloff (flag 0 into 0x9025b0),
 * while your own shot is 2D (flag 1). RemoteShot2D makes a remote ZFFPlayer shooter within RemoteShot2DDist of the local pawn play 2D too (full volume, like your own shot);
 * farther ones stay 3D so the direction still reads. Arcade is untouched: everything is gated on kl_online() (klhook.c), which is 0 in Arcade / story / no session.
 *   RemoteShot2D     0 = off (default), 1 = on, 2 = DRY (log only, nothing changes)
 *   RemoteShot2DDist cm (game units, GUESS: 1 unit = 1 cm), default 1500; the remote shooter's 3D distance to the local pawn must be <= this
 *
 * WHY NOT E8 DETOURS ON THE CALLS TO 0x503650 (the brief's idea): its arg2 is NOT the 2D flag. 0x503650(this = weapon, arg1 = shooter, arg2 = ?) computes the 2D byte itself
 * (0x5036d4..0x503708: shooter == [gd+0x828+4*(char)[gd+0x898]], i.e. 0x660b00(0), or the session test) and OVERWRITES its own arg1 stack slot with it ([esp+0x10], 0x503702/0x503708),
 * then pushes it as arg2 of 0x9025b0 (#def slot 4). So the caller cannot ask for 2D. The two sites that matter are INSIDE 0x503650, both reached only for a ZFFPlayer shooter
 * (a non-ZFFPlayer jumps at 0x5036ce to the slot-1 npc path):
 *   site A 0x503764  8b 4c 24 10 51   mov ecx,[esp+0x10] ; push ecx        (default state, [[shooter+0x54]+0x42]==0; then `push 4` = slot 4, the 2D byte is the computed one)
 *   site B 0x50375b  b8 04 00 00 00   mov eax,4                            (then `push ebx` = 2D 0 and `push eax`; state outside 1..6 with [[shooter+0x54]+0x42]!=0)
 * Both are patched with E9 rel32 to a naked stub (the 5 patched bytes are exactly one or two whole instructions, nothing else jumps into them: checked by disassembly).
 * WHICH CALLERS: the stub only acts when 0x503650 was called from the FIRE path, i.e. its return address (at [esp+0xc] on entry to both sites: ebx, edi, ebp pushed at 0x503650..0x5036a5,
 * then ret) is 0x4cca6d (the call at 0x4cca68: `mov ecx,esi ; push edi(shooter) ; push [esp+0x24]`, E8 rel32 = e8 e3 6b 03 00). The calls at 0x8c567b / 0x8c56ea / 0x8c5837 are NOT shots: they
 * run right after `mov [owner+0xd70],5 / 4 / 6` (the owner state that 0x503650 maps to slots 0 / 9 / 3 via the table at 0x5039a4), on `this = [ecx+0x2c]`, not the fire routine; so they are
 * excluded (GUESS: states 4..6 are not shots; if one of them reaches slot 4 through site A it is simply not touched).
 * Register handling: both stubs save EFLAGS and every general register around the C decision (pushad / pushfd ... popfd / popad), re-run the displaced instruction(s) themselves and jump
 * back. The decision runs under __try; any fault = the original behaviour. A refused patch (SHIP build / SessionSafe / other bytes) is logged and nothing changes. */
/* SHIP-compatible route (2026-10-28, same keys + the same klss_decide; kl2.exe read statically, NOT run live): the SHIP policy (klhook.c KLH_SHIP) refuses every code patch above, so the
 * decision is also reachable DATA-ONLY. The sound system is NOT in a DLL: it is a heap object of the exe's own class, [[0xdd2640]+0xb00], size 0xb124, built by 0x762f70 -> ctor 0x4ff8c0, vtable
 * 0xb9ae14 (kl2.exe .rdata, read-only, hashed). Both 0x9025b0 branches end in ITS slot 74 (+0x128 = 0x592950, `ret 0x10`, a thin wrapper that calls slot 73 +0x124 with the same four args):
 *   2D (0x90268b, returns 0x90268d):  +0x128(a1 = head ctx from slot 52 +0xd0 (0x571300 = mov eax,[ecx+0x6760]), a2 = ebp (sound handle), a3 = &local 36-byte block filled by 0x7f07a0, a4 = &(0, 0, [0xb5c050]))
 *   3D (0x467eb6, returns 0x467eb8; inside 0x467e00 called from 0x90272f): +0x128(a1 = emitter ctx (0x4a30e0 / 0x598460), a2 = the same ebp, a3 = a transformed block (0x569950), a4 = the position)
 * (the brief said +0x12c for 3D: 0x467e00 calls +0x128 too; +0x12c = 0x589670 is not on either path.) 2D afterwards runs 0x659370(handle): [h+0x84] &= ~4, byte [h+0x145] = 1 (0x9026a4..0x9026b4).
 * Route: a PRIVATE COPY of the vtable (klsync.c ksp_vt technique: vt[-1] RTTI + the slots, slot 74 -> klss_vt_stub), and the heap object's vptr [obj] pointed at it (klh_data, kind 0 = heap, allowed in SHIP).
 * The object is rebuilt per session, so klss_tick re-points it whenever [[0xdd2640]+0xb00] changes (and only if [obj] is the stock 0xb9ae14; anything else = refused, logged). No code byte is written.
 * A shot is recognised by walking the stack at the wrapper's entry (sp = esp on entry, byte offsets): sp[0] == 0x467eb8 (3D play), sp[0x2c] == 0x902734 (inside 0x467e00 called by 0x9025b0's 3D branch at
 * 0x90272f), sp[0x88] == 0x503772 (0x9025b0 called by 0x503650 at 0x50376d: the ZFFPlayer path; the npc slot-1 path returns to 0x50378a and is excluded), sp[0x8c] == 4 (#def slot 4 shot_player), low byte of
 * sp[0x90] == 0 (3D flag), sp[0xa0] == 0x4cca6d (0x503650 called from the fire path), shooter = sp[0x94] (503650's saved ebp, cross-checked with 9025b0's saved ebp sp[0x50]), weapon = sp[0x98] (= sp[0x54]).
 * The layout is derived from the pushes of 0x9025b0 / 0x467e00 / 0x503650 (GUESS: no stack walk was seen live); any mismatch = no action, counted and logged (first 5). klss_decide then decides exactly as for the
 * code route; when it says yes the wrapper rewrites a1, a3, a4 IN PLACE to the 2D branch's values (static blocks are fine: the callee does not keep the pointers, as the 2D branch passes stack locals),
 * calls the original slot 74 and replays the 2D branch's post step on the returned handle (GUESS that the 3D branch's own later step, 0x867da0 with [obj+0x18], does not undo 2D-ness). */
#ifndef KLSHOT2D_C
#define KLSHOT2D_C

#define KLSS_3D_RET   0x00467eb8u              /* return of the slot-74 call inside 0x467e00 */
#define KLSS_3D_OUTER 0x00902734u              /* return of `call 0x467e00` at 0x90272f */
#define KLSS_9025_FROM503 0x00503772u          /* return of `call 0x9025b0` at 0x50376d */

#define KLSS_SITE_A   0x00503764u
#define KLSS_SITE_B   0x0050375bu
#define KLSS_BACK_A   0x00503769u              /* after `push ecx` (the `push 4` follows) */
#define KLSS_BACK_B   0x00503760u              /* after `mov eax,4` (`push ebx ; push eax` follow) */
#define KLSS_PUSH_B   0x0050376bu              /* the `mov ecx,edi ; call 0x9025b0` both paths join */
#define KLSS_FIRE_RET 0x004cca6du              /* return address of the call 0x4cca68 -> 0x503650 */

static int klss_mode, klss_dist = 1500, klss_patched;
static DWORD klss_back_a, klss_back_b, klss_push_b, klss_fire_ret, klss_force;
static LONG klss_n_fire, klss_n_remote, klss_n_force, klss_n_far, klss_n_fault, klss_logn;
static DWORD klss_logt;

static void klss_log(const char *fmt, DWORD shooter, int site, float d)
{
    DWORD now = GetTickCount();
    if (klss_logn >= 300 || now - klss_logt < 1000) return;      /* at most one line a second, 300 a run */
    klss_logt = now; klss_logn++;
    klog(fmt, shooter, site == 0 ? 'A' : site == 1 ? 'B' : 'V', d, klss_dist, (long)klss_n_fire, (long)klss_n_remote, (long)klss_n_force, (long)klss_n_far);
}

/* 1 = play this shot 2D. Called from both stubs (cdecl; the stubs preserve every register around it). */
static int __cdecl klss_decide(DWORD shooter, DWORD ret, int site)
{
    int r = 0;
    __try {
        DWORD gd, loc = 0; BYTE sel = 0xff; float a[3], b[3], d = 0; int ha, hb;
        if (!klss_mode || ret != klss_fire_ret || !shooter) return 0;      /* only the fire path (0x4cca68) */
        InterlockedIncrement(&klss_n_fire);
        if (!kl_online()) return 0;                                         /* Arcade / story / no session: untouched */
        gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c));
        if (gd && klh_rd(gd + 0x898, &sel, 1) && sel < 28) loc = klh_rd32(gd + 0x828 + 4 * sel);      /* = 0x660b00(0), the callee's own "local pawn" */
        if (shooter == loc) return 0;                                       /* already 2D (site A) / left as it is */
        InterlockedIncrement(&klss_n_remote);
        /* positions: scene node first, then +0x460, as klauto.c kla_player_pos (the node follows the body, +0x460 can go stale) */
        ha = kle_node(klh_rd32(shooter + 4), a, 0) || (klh_rd(shooter + 0x460, a, 12) && (a[0] != 0 || a[2] != 0));
        hb = loc && (kle_node(klh_rd32(loc + 4), b, 0) || (klh_rd(loc + 0x460, b, 12) && (b[0] != 0 || b[2] != 0)));
        if (!ha || !hb) { klss_log("shot2d: remote shooter %08lx site %c: no position for it or the local pawn (%.0f); stays 3D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, 0.0f); return 0; }
        d = sqrtf((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
        if (!(d <= (float)klss_dist)) { InterlockedIncrement(&klss_n_far); klss_log("shot2d: remote shooter %08lx site %c at %.0f cm: beyond the limit, stays 3D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, d); return 0; }
        InterlockedIncrement(&klss_n_force);
        if (klss_mode == 2) { klss_log("shot2d: DRY remote shooter %08lx site %c at %.0f cm: would play 2D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, d); return 0; }
        klss_log("shot2d: remote shooter %08lx site %c at %.0f cm: played 2D (dist %d; fire %ld remote %ld 2D %ld far %ld)", shooter, site, d);
        r = 1;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        r = 0;
        if (InterlockedIncrement(&klss_n_fault) <= 5) klog("shot2d: FAULT %08lx in the decision; the original 3D/2D flag is kept", (unsigned long)GetExceptionCode());
    }
    return r;
}

/* site A, entered by E9 from 0x503764 with the stack of 0x503650 after its 3 pushes: [esp]=ebp(shooter) +4 edi +8 ebx +0xc ret +0x10 arg1/2D byte */
static __declspec(naked) void klss_stub_a(void)
{
    __asm {
        pushad
        pushfd
        mov eax, [esp + 0x24 + 0x0c]      ; return address of 0x503650
        push 0
        push eax
        push ebp                          ; the shooter
        call klss_decide
        add esp, 12
        mov klss_force, eax
        popfd
        popad
        mov ecx, [esp + 0x10]             ; the displaced instruction pair
        cmp klss_force, 0
        je keep
        mov cl, 1                         ; the 2D byte (0x9025b0 reads only its low byte, movzx at 0x9025d7)
    keep:
        push ecx
        jmp dword ptr [klss_back_a]
    }
}
/* site B, entered by E9 from 0x50375b (mov eax,4) with the same stack */
static __declspec(naked) void klss_stub_b(void)
{
    __asm {
        pushad
        pushfd
        mov eax, [esp + 0x24 + 0x0c]
        push 1
        push eax
        push ebp
        call klss_decide
        add esp, 12
        mov klss_force, eax
        popfd
        popad
        mov eax, 4                        ; the displaced instruction: #def slot 4
        cmp klss_force, 0
        je keep
        push 1                            ; 2D instead of `push ebx` (0)
        push eax
        jmp dword ptr [klss_push_b]
    keep:
        jmp dword ptr [klss_back_b]
    }
}

/* ---- SHIP route: private vtable of the sound system ---- */
#define KLSS_SND_VT   0x00b9ae14u
#define KLSS_VT_N     160                       /* the stock table has 144 slots; room to spare, copied from the exe (the tail is never called) */
#define KLSS_VT_SLOT  74                        /* +0x128 */
#define KLSS_VT_HEAD  52                        /* +0xd0 */
static DWORD klss_vtblk[KLSS_VT_N + 1];         /* [0] = vt[-1] (RTTI locator) */
#define klss_vt (klss_vtblk + 1)
static DWORD klss_vt_orig, klss_vt_ready, klss_obj, klss_vt_force;
static int klss_route_vt, klss_route_cfg;
static BYTE klss_blk[48];                       /* the 2D branch's 36-byte a3 block, built by the game's own 0x7f07a0 */
static float klss_zpos[3];
static LONG klss_n_vt, klss_n_stack_bad;

typedef void (__fastcall *klss_fill_t)(void *blk, void *edx);
typedef DWORD (__fastcall *klss_head_t)(void *obj, void *edx);
typedef DWORD (__fastcall *klss_find_t)(void *sys, void *edx, DWORD handle);

/* 1 = a1 / a3 / a4 at sp[1], sp[3], sp[4] were rewritten to the 2D branch's values */
static int __cdecl klss_vt_pre(DWORD *sp, DWORD self)
{
    int r = 0;
    __try {
        DWORD shooter, weapon; float k = 0;
        if (!klss_mode || sp[0] != KLSS_3D_RET || sp[0x2c / 4] != KLSS_3D_OUTER) return 0;      /* not the 3D branch of 0x9025b0 */
        if (sp[0x88 / 4] != KLSS_9025_FROM503) return 0;                                      /* 0x9025b0 from the npc path or another caller */
        shooter = sp[0x94 / 4]; weapon = sp[0x98 / 4];
        if (sp[0x8c / 4] != 4 || (sp[0x90 / 4] & 0xff) != 0 || sp[0xa0 / 4] != klss_fire_ret || sp[0x50 / 4] != shooter || sp[0x54 / 4] != weapon || !shooter) {
            if (sp[0x8c / 4] == 4 && sp[0xa0 / 4] == klss_fire_ret && InterlockedIncrement(&klss_n_stack_bad) <= 5)
                klog("shot2d: vtable route: slot-4 3D play from the fire path but the stack does not match (slot %lu flag %lu shooter %08lx/%08lx weapon %08lx/%08lx); not touched", (unsigned long)sp[0x8c / 4], (unsigned long)sp[0x90 / 4], (unsigned long)shooter, (unsigned long)sp[0x50 / 4], (unsigned long)weapon, (unsigned long)sp[0x54 / 4]);
            return 0;
        }
        if (!klss_decide(shooter, sp[0xa0 / 4], 2)) return 0;
        {   /* the 2D branch's own arguments: head ctx = slot 52 on the object, the block from 0x7f07a0, (0, 0, [0xb5c050]) */
            DWORD head = klss_vt[KLSS_VT_HEAD] ? ((klss_head_t)(DWORD_PTR)klss_vt[KLSS_VT_HEAD])((void *)(DWORD_PTR)self, 0) : 0;
            if (!head) return 0;
            ((klss_fill_t)(DWORD_PTR)KLH_VA(0x7f07a0))(klss_blk, 0);
            if (!klh_rd((DWORD_PTR)KLH_VA(0xb5c050), &k, 4)) return 0;
            klss_zpos[0] = 0; klss_zpos[1] = 0; klss_zpos[2] = k;
            sp[1] = head; sp[3] = (DWORD)(DWORD_PTR)klss_blk; sp[4] = (DWORD)(DWORD_PTR)klss_zpos;
            InterlockedIncrement(&klss_n_vt); r = 1;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        r = 0;
        if (InterlockedIncrement(&klss_n_fault) <= 5) klog("shot2d: FAULT %08lx in the vtable route; the original call goes through", (unsigned long)GetExceptionCode());
    }
    return r;
}
/* the 2D branch's step after the play (0x9026a4..0x9026b4) */
static void __cdecl klss_vt_post(DWORD handle)
{
    __try {
        DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd2640)), sys = gd ? klh_rd32(gd + 0xb00) : 0, p;
        if (!handle || !sys) return;
        p = ((klss_find_t)(DWORD_PTR)KLH_VA(0x659370))((void *)(DWORD_PTR)sys, 0, handle);
        if (p) { *(DWORD *)(DWORD_PTR)(p + 0x84) &= 0xfffffffbu; *(BYTE *)(DWORD_PTR)(p + 0x145) = 1; }
    } __except (EXCEPTION_EXECUTE_HANDLER) { if (InterlockedIncrement(&klss_n_fault) <= 5) klog("shot2d: FAULT %08lx in the vtable route's post step", (unsigned long)GetExceptionCode()); }
}
/* slot 74 of the private table: thiscall (ecx = sound system), four stack args, ret 0x10. Stack-transparent when nothing is rewritten (jmp to the original). */
static __declspec(naked) void klss_vt_stub(void)
{
    __asm {
        pushad
        pushfd
        push ecx                          ; self
        lea eax, [esp + 0x28]             ; esp on entry = esp + 4 (self) + 0x24 (flags, regs)
        push eax
        call klss_vt_pre
        add esp, 8
        mov klss_vt_force, eax
        popfd
        popad
        cmp klss_vt_force, 0
        jne conv
        jmp dword ptr [klss_vt_orig]
    conv:
        push ecx                          ; keep self; the args now sit at +8 .. +0x14
        push dword ptr [esp + 0x14]       ; a4
        push dword ptr [esp + 0x14]       ; a3
        push dword ptr [esp + 0x14]       ; a2
        push dword ptr [esp + 0x14]       ; a1
        mov ecx, [esp + 0x10]
        call dword ptr [klss_vt_orig]     ; the callee pops its 4 args
        push eax
        push eax
        call klss_vt_post
        add esp, 4
        pop eax
        add esp, 4                        ; drop self
        ret 0x10
    }
}
/* point the current sound system object at the private table (every 500 ms from the game thread; the object is rebuilt per session) */
static void klss_tick(int game_thread)
{
    DWORD gd, obj, vp; static DWORD t_last, klss_bad, klss_n; DWORD now = GetTickCount();
    if (!klss_route_vt || !game_thread || now - t_last < 500) return;
    t_last = now;
    /* the vptr is read every tick, not only when the object address changes: a rebuilt sound system can land on the
       same heap address with the stock vptr again (review 10-28); klss_obj / klss_bad only rate-limit the log lines */
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd2640))) || !(obj = klh_rd32(gd + 0xb00))) return;
    vp = klh_rd32(obj);
    if (vp == (DWORD)(DWORD_PTR)klss_vt) { klss_obj = obj; return; }
    if (vp != (DWORD)(DWORD_PTR)KLH_VA(KLSS_SND_VT)) { if (klss_bad != obj) { klss_bad = obj; klog("shot2d: vtable route: sound system %08lx has vtable %08lx, not 0x%x: not hooked", (unsigned long)obj, (unsigned long)vp, KLSS_SND_VT); } return; }
    if (klss_bad == obj) return;      /* the vptr write was refused for this object: do not retry every tick */
    {   DWORD nv = (DWORD)(DWORD_PTR)klss_vt;
        if (klh_data((void *)(DWORD_PTR)obj, &nv, 4, "shot2d sound system vtable pointer")) { if (++klss_n <= 20) klog("shot2d: vtable route: sound system %08lx now on the private vtable (slot 74 -> wrapper of 0x%lx)%s", (unsigned long)obj, (unsigned long)klss_vt_orig, obj == klss_obj ? " (rebuilt at the same address)" : ""); klss_obj = obj; }
        else { klss_bad = obj; klog("shot2d: vtable route: the write of the vptr at %08lx was REFUSED", (unsigned long)obj); }
    }
}
static int klss_vt_prepare(void)
{
    if (klss_vt_ready) return 1;
    if (!klh_rd((DWORD_PTR)KLH_VA(KLSS_SND_VT) - 4, klss_vtblk, sizeof klss_vtblk) || klss_vt[KLSS_VT_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(0x592950) || klss_vt[KLSS_VT_HEAD] != (DWORD)(DWORD_PTR)KLH_VA(0x571300)) {
        klog("shot2d: vtable route: slots 74 / 52 of 0xb9ae14 are %08lx / %08lx, not 0x592950 / 0x571300: this is not the exe read; route off", (unsigned long)klss_vt[KLSS_VT_SLOT], (unsigned long)klss_vt[KLSS_VT_HEAD]);
        return 0;
    }
    klss_vt_orig = klss_vt[KLSS_VT_SLOT]; klss_vt[KLSS_VT_SLOT] = (DWORD)(DWORD_PTR)klss_vt_stub; klss_vt_ready = 1;
    return 1;
}

static void klss_init(void)
{
    static const BYTE ea[5] = { 0x8b, 0x4c, 0x24, 0x10, 0x51 }, eb[5] = { 0xb8, 0x04, 0x00, 0x00, 0x00 };
    BYTE put[5]; DWORD rel; int okA, okB;
    klss_mode = (int)GetPrivateProfileIntA("Sound", "RemoteShot2D", 0, klh_ini); if (klss_mode < 0 || klss_mode > 2) klss_mode = 0;      /* (recommended off: not yet run live) */
    klss_dist = (int)GetPrivateProfileIntA("Sound", "RemoteShot2DDist", 1500, klh_ini); if (klss_dist < 0) klss_dist = 0; if (klss_dist > 1000000) klss_dist = 1000000;
    if (!klss_mode) return;
    if (!klh_exe_ok) { klog("shot2d: RemoteShot2D=%d but this is not the known kl2.exe; nothing is patched", klss_mode); return; }
    klss_back_a = (DWORD)(DWORD_PTR)KLH_VA(KLSS_BACK_A); klss_back_b = (DWORD)(DWORD_PTR)KLH_VA(KLSS_BACK_B); klss_push_b = (DWORD)(DWORD_PTR)KLH_VA(KLSS_PUSH_B);
    klss_fire_ret = (DWORD)(DWORD_PTR)KLH_VA(KLSS_FIRE_RET);
    {   /* the fire-path call itself must still be the E8 to 0x503650 this was written against, else the return-address gate would never match: refuse */
        BYTE c[5]; DWORD want = 0x503650u - (0x4cca68u + 5);
        if (!klh_rd((DWORD_PTR)KLH_VA(0x4cca68), c, 5) || c[0] != 0xE8 || memcmp(c + 1, &want, 4)) { klog("shot2d: the call at 0x4cca68 is not `call 0x503650`; nothing is patched"); return; }
    }
    /* [Sound] RemoteShot2DRoute (diagnostic): 0 = auto (the code patch; when both sites are refused, as in a SHIP build, the sound-system vtable route), 1 = code patch only, 2 = vtable route only */
    klss_route_cfg = (int)GetPrivateProfileIntA("Sound", "RemoteShot2DRoute", 0, klh_ini); if (klss_route_cfg < 0 || klss_route_cfg > 2) klss_route_cfg = 0;
    okA = okB = 0;
    if (klss_route_cfg != 2) {
        put[0] = 0xE9; rel = (DWORD)(DWORD_PTR)klss_stub_a - (DWORD)(DWORD_PTR)KLH_VA(KLSS_SITE_A + 5); memcpy(put + 1, &rel, 4);
        okA = klh_poke(KLH_VA(KLSS_SITE_A), ea, 5, put, 5, "shot2d site A");
        rel = (DWORD)(DWORD_PTR)klss_stub_b - (DWORD)(DWORD_PTR)KLH_VA(KLSS_SITE_B + 5); memcpy(put + 1, &rel, 4);
        okB = klh_poke(KLH_VA(KLSS_SITE_B), eb, 5, put, 5, "shot2d site B");
        klog("shot2d: RemoteShot2D=%d (2 = dry) dist %d cm: CODE route: site A 0x503764 %s, site B 0x50375b %s", klss_mode, klss_dist, okA ? "patched" : "REFUSED (other bytes, SHIP build or SessionSafe)",
             okB ? "patched" : "REFUSED (other bytes, SHIP build or SessionSafe)");
    }
    klss_patched = okA + okB;
    if (klss_patched == 0 && klss_route_cfg != 1) {
        klss_route_vt = klss_vt_prepare();
        klog("shot2d: RemoteShot2D=%d (2 = dry) dist %d cm: VTABLE route %s (sound system [[0xdd2640]+0xb00], slot 74 = 0x592950; the object is re-pointed from the tick)", klss_mode, klss_dist, klss_route_vt ? "ready" : "NOT available");
    }
    if (klss_patched == 0 && !klss_route_vt) klog("shot2d: no route is active; nothing changes");
}

#endif /* KLSHOT2D_C */
