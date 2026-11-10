/* kllistguard_logic.h - pure decisions for [Crash] ListUserGuard (kllistguard.c). No game access, no Windows; tested by kllistguard_test.c.
 *
 * The crash (owner, DM03 round 2, 2026-11-09 16:46, debug/notes/2026-11-09-dm03-fedrespawn-crash.md): kl2.exe 0x4f8a8e (cmp [edx],esi in the
 * hash-chain remove 0x4f8a60) reads 0x4f09 when CListUser slot 0 (0x630700, thiscall(this, n, rec), ret 8) meets a released record whose
 * [rec+0x54] & 0xffffff is 0 (key 0 = the table's header word). The guard wraps slot 0 in a __try and swallows exactly that fault.
 *
 * Facts checked by disassembling kl2.exe build 0490 (capstone, 2026-11-10):
 *   - vtable 0xb5a1d4 slot 0 = 0x630700; NO other dword of the file equals 0x630700 (scanned every section), and no direct call to it:
 *     the only call is `call edx` at 0x5bfc03 through [[obj]], so a per-object vtable copy sees every call.
 *   - 0x4f8a60 .. 0x4f8b46 (`ret 0xc`) is the whole hash-chain remove; 0x4f8b49 .. 0x4f8b4f is int3 padding, the next function starts at 0x4f8b50.
 *   - the vtable lies in a HASHED .rdata range (0xb11000..0xb8ac00, klranges.h): patching it in place would end a real session and the ship
 *     policy refuses it. So the guard gives the live object(s) a PRIVATE copy of the vtable (heap data, the kllobby.c / klroundkeep.c route).
 */
#ifndef KLLISTGUARD_LOGIC_H
#define KLLISTGUARD_LOGIC_H

#define KLLG_VT      0x00b5a1d4u     /* CListUser vtable (.rdata) */
#define KLLG_SLOT0   0x00630700u     /* what slot 0 holds in kl2.exe 0490 */
#define KLLG_FN_LO   0x004f8a60u     /* hash-chain remove: first byte */
#define KLLG_FN_HI   0x004f8b49u     /* one past its last byte (ret 0xc is 0x4f8b46..0x4f8b48) */
#define KLLG_AV      0xc0000005u     /* EXCEPTION_ACCESS_VIOLATION */
#define KLLG_VT_MAX  64              /* slots copied at most */
#define KLLG_OBJ_SZ  0x44u           /* the object (operator new(0x44) at 0x8adfa6) */

/* does the fault belong to the one crash? Only an access violation with its address inside the remove function. */
static int kllg_catch(unsigned code, unsigned addr, unsigned lo, unsigned hi)
{
    return code == KLLG_AV && addr >= lo && addr < hi;
}

/* the vtable may only be used when slot 0 is exactly the known function (refuse + log on any other build) */
static int kllg_slot_ok(unsigned slot0) { return slot0 == KLLG_SLOT0; }

/* how many leading vtable entries look like code (within [text_lo, text_hi)); at most max. The copy is this long. */
static int kllg_vt_len(const unsigned *vt, int max, unsigned text_lo, unsigned text_hi)
{
    int n = 0;
    while (n < max && vt[n] >= text_lo && vt[n] < text_hi) n++;
    return n;
}

/* a heap hit of the vtable value is taken for a CListUser only when it is 4-aligned and its hash-table pointer (+0x20) is non-null and
   not the vtable value itself; the caller has already proven the 0x44 bytes readable. */
static int kllg_cand_ok(unsigned addr, unsigned vptr, unsigned table_ptr)
{
    return (addr & 3u) == 0 && vptr == KLLG_VT && table_ptr != 0 && table_ptr != KLLG_VT && addr >= 0x10000u;
}

/* rate limit of the log line: the first catch always, then at most one line per gap_ms (the game may hit it every frame for a while) */
static int kllg_log_due(int hits, unsigned now, unsigned last_log, unsigned gap_ms)
{
    return hits <= 1 || (unsigned)(now - last_log) >= gap_ms;
}

/* when to scan the heap for the object(s): after a scene change at +2, +6, +15, +30 s, then every 10 s while the guard has a scene.
   step = how many of the four timed scans already ran for this scene; returns the delay in ms until the next one. */
static unsigned kllg_next_delay(int step)
{
    static const unsigned d[4] = { 2000, 4000, 9000, 15000 };      /* gaps between scans: 2, 6, 15, 30 s after the change */
    return step >= 0 && step < 4 ? d[step] : 10000u;     /* 10 s: a new object per round / respawn (no round signal known) is guarded within 10 s */
}


/* ListUserGuard=2 calls six helper functions of the exe from the C port; each one's first dword is checked before the port is used (any other build: mode 1) */
typedef struct { unsigned va, dw; } KLLG_HELPER_ID;
static const KLLG_HELPER_ID kllg_helper_ids[7] = {
    { 0x004e2b90u, 0x0c24448bu }, { 0x008176f0u, 0x8b20498bu }, { 0x00881ef0u, 0x08244c8bu }, { 0x005a4ad0u, 0x20418b51u },
    { 0x004f8a60u, 0x24548b51u }, { 0x006986b0u, 0x0424548bu }, { 0x00630700u, 0x0424448bu } };

/* the mode value of [Crash] ListUserGuard: 0 off, 1 catch (old), 2 port (anything above 2 reads as 2, negative as off) */
static int kllg_mode_of(int ini) { return ini <= 0 ? 0 : ini == 1 ? 1 : 2; }

/* the CListUser object is [[[0xdd2640] + 0xac] + 0x86d4] (read by the update's caller at 0x5bf72c..0x5bf732): found without a heap scan, in a few reads,
   so a new object (a new level / round) is repointed on the very next tick */
#define KLLG_G_ROOT    0x00dd2640u
#define KLLG_O_SCENE   0xacu
#define KLLG_O_LISTUSR 0x86d4u

#endif
