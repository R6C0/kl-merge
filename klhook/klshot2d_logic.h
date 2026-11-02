/* klshot2d_logic.h - [Sound] RemoteShot2DGate and the RemoteShot2DLogAny slot-74 counter, the PURE parts (no game memory, no log, no clock, no windows.h).
   Included by klshot2d.c and klshot2d_test.c. 2026-11-02 (wk-shot2dgate-1102); kl2.exe read statically, NOT run live.
   WHY: in GUN1-6 / GUN12b the vtable route sat on slot 74 and logged 0 "would play 2D" / "played 2D" lines. Three things can cause that and the old log could not tell them apart:
   (1) slot 74 is never called with the 3D-shot stack (no shot happened, or remote shots play through another sound call);
   (2) the caller gate (0x503650 returning to 0x4cca6d = the weapon fire routine 0x4cb7a0) excludes the remote shot, which may reach 0x503650 from the owner-state code
       (0x8c567b / 0x8c56ea / 0x8c5837; 0x503650 returns to 0x8c5680 / 0x8c56ef / 0x8c583c) instead;
   (3) kl_online() is 0 in that bench so the decision returns before it logs.
   The counter below counts EVERY slot-74 call by its return address once a second so the next bench shows which one it is. The relaxed gate (RemoteShot2DGate=1) accepts the
   state-code callers too (GUESS: they may be non-shot sounds - the state table 0x5039a4 maps states 1..6 to slots 12,11,10,9,0,3 only when [[shooter+0x54]+0x42] != 0; site A / slot 4 only
   happens for state-less shooters). Default 0 = today's strict gate. */
#ifndef KLSHOT2D_LOGIC_H
#define KLSHOT2D_LOGIC_H

#define KS2_RET_FIRE   0x004cca6dul   /* 0x503650 called from the weapon fire routine 0x4cb7a0 (call at 0x4cca68) */
#define KS2_RET_ST5    0x008c5680ul   /* call at 0x8c567b, right after [owner+0xd70] = 5 */
#define KS2_RET_ST4    0x008c56eful   /* call at 0x8c56ea, after [owner+0xd70] = 4 */
#define KS2_RET_ST6    0x008c583cul   /* call at 0x8c5837, after [owner+0xd70] = 6 */

/* gate 0 = only the fire routine (the strict, original gate); 1 = also the three owner-state callers. ret = the return address 0x503650 will use. */
static int ks2_gate_ok(int gate, unsigned long ret)
{
    if (ret == KS2_RET_FIRE) return 1;
    if (gate == 1 && (ret == KS2_RET_ST5 || ret == KS2_RET_ST4 || ret == KS2_RET_ST6)) return 1;
    return 0;
}

/* one second of slot-74 calls: how many in all, how many 3D branch of 0x9025b0, how many of those from 0x503650, and the first KS2_N distinct return addresses of the slot-74 call
   (key = sp[0]: the immediate caller, e.g. 0x467eb8 for the 3D branch, 0x90268d for the 2D branch) with their counts. */
#define KS2_N 8
typedef struct {
    unsigned long calls, d3, from503;
    unsigned long ret[KS2_N]; unsigned long cnt[KS2_N]; int n; unsigned long other;   /* other = calls whose ret did not fit the table */
} ks2_ctr_t;

static void ks2_ctr_reset(ks2_ctr_t *c)
{
    int i; c->calls = c->d3 = c->from503 = c->other = 0; c->n = 0;
    for (i = 0; i < KS2_N; i++) c->ret[i] = c->cnt[i] = 0;
}
static void ks2_ctr_add(ks2_ctr_t *c, unsigned long ret, int is3d, int is503)
{
    int i;
    c->calls++; if (is3d) c->d3++; if (is503) c->from503++;
    for (i = 0; i < c->n; i++) if (c->ret[i] == ret) { c->cnt[i]++; return; }
    if (c->n < KS2_N) { c->ret[c->n] = ret; c->cnt[c->n] = 1; c->n++; } else c->other++;
}
/* 1 when a once-a-second line is due: calls seen and >= 1000 ms since the last line (the caller passes GetTickCount values; the unsigned difference survives the 32-bit wrap there) */
static int ks2_ctr_due(const ks2_ctr_t *c, unsigned long now, unsigned long last)
{
    return c->calls != 0 && (now - last) >= 1000ul;
}

/* The slot-74 stack walk of a slot-4 3D shot (sp = esp on entry to the wrapper, dword index = byte offset / 4). 2026-11-02 (shot2d2): the first version read the shooter
   from sp[0x94] and the weapon from sp[0x98]. Those are 0x4cb7a0's SAVED ebp / edi (0x503650 does `push ebx ; push edi ; push ebp` before `mov edi,ecx ; mov ebp,[arg1]`), not
   0x503650's own. 0x9025b0 pushes edi (= weapon, this of 0x503650) at 0x9025bf and ebp (= shooter, arg1 of 0x503650) at 0x9025dc, so shooter = sp[0x50], weapon = sp[0x54].
   G1 log: sp[0x94] changed every shot (5cc15e80, 5cc15a60 ...) while sp[0x50] / sp[0x54] stayed 37635030 / 699b2800 = one shooter, one weapon. Returns KS2_SHOT_OK or the
   first failing check (for the log). */
#define KS2_SHOT_OK 0
#define KS2_SHOT_NOT3D 1      /* sp[0] / sp[0x2c]: not the 3D branch of 0x9025b0 */
#define KS2_SHOT_FROM  2      /* 0x9025b0 not called from 0x503650 (npc path, other caller) */
#define KS2_SHOT_SLOT  3      /* not #def slot 4 */
#define KS2_SHOT_FLAG  4      /* 2D flag byte not 0 */
#define KS2_SHOT_GATE  5      /* 0x503650's return address refused by the gate */
#define KS2_SHOT_NOSHOOTER 6
static int ks2_stack_shot(const unsigned long *sp, int gate, unsigned long *shooter, unsigned long *weapon)
{
    if (sp[0] != 0x00467eb8ul || sp[0x2c / 4] != 0x00902734ul) return KS2_SHOT_NOT3D;
    if (sp[0x88 / 4] != 0x00503772ul) return KS2_SHOT_FROM;
    if (sp[0x8c / 4] != 4) return KS2_SHOT_SLOT;
    if ((sp[0x90 / 4] & 0xff) != 0) return KS2_SHOT_FLAG;
    if (!ks2_gate_ok(gate, sp[0xa0 / 4])) return KS2_SHOT_GATE;
    *shooter = sp[0x50 / 4]; *weapon = sp[0x54 / 4];
    if (!*shooter) return KS2_SHOT_NOSHOOTER;
    return KS2_SHOT_OK;
}

#endif /* KLSHOT2D_LOGIC_H */
