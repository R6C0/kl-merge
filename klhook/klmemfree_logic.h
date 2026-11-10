/*
 * klmemfree_logic.h - the pure part of klmemfree.c ([Memory] Release): no Windows calls, so klmemfree_test.c can run
 * it on any input. (1) which kind of thing a private allocation of the address space is, (2) whether the first bytes of
 * an allocation are an NT heap segment header, (3) when to run the release (level left / level block freed, settle, cooldown).
 *
 * THE FACTS IT RESTS ON (KLHook_map_refused_0.txt of the owner's 2026-11-10 00:23:35 session, one match after the start):
 * 321 private allocations, 1204 MB, 919 MB of it 'reserved only'. Grouped by size: 28 of 15.81 MB (443 MB, 58 MB committed,
 * 385 MB reserved only), 47 of 4 MB (kl2's own thread stacks, 188 MB), 5 of 32 MB (160 MB, 14 committed), the klmem reserve
 * (128 MB, 32 committed), 15 of 2 MB (stacks). The 15.81 MB ones are NT heap segments with 14-40 tiny committed islands each:
 * the heap keeps its segments (the NT heap never returns a segment's address space on this Windows build, even when empty:
 * klmemfree_test.c), whether or not a live block sits in them (GUESS for the owner's session).
 */
#ifndef KLMEMFREE_LOGIC_H
#define KLMEMFREE_LOGIC_H

#include <stddef.h>
#include <stdint.h>

enum { KLMR_OTHER, KLMR_RESERVE, KLMR_HEAPSEG, KLMR_STACK, KLMR_BIG, KLMR_NCLS };
static const char *const klmr_cls_name[KLMR_NCLS] = { "other private", "klmem reserve", "heap segments", "thread stacks", "other big (>= 8 MB)" };

struct klmr_group {          /* one allocation (everything with the same AllocationBase), private memory only */
    uintptr_t base;
    size_t size, commit;     /* summed region sizes; committed part */
    int guard;               /* a committed PAGE_GUARD page inside: a thread stack */
    int is_seg;              /* the header says NT heap segment (klmr_seg_hdr) */
    int is_reserve;          /* base is klmem's reserve */
};

static int klmr_classify(const struct klmr_group *g)
{
    if (g->is_reserve) return KLMR_RESERVE;
    if (g->is_seg) return KLMR_HEAPSEG;
    if (g->guard && g->size >= ((size_t)256 << 10) && g->size <= ((size_t)16 << 20)) return KLMR_STACK;
    if (g->size >= ((size_t)8 << 20)) return KLMR_BIG;
    return KLMR_OTHER;
}

/* x86 _HEAP_SEGMENT (Windows 7 - 10 classic NT heap): +0 HEAP_ENTRY (8 bytes), +8 SegmentSignature 0xFFEEFFEE, +0xC SegmentFlags,
   +0x10 SegmentListEntry, +0x18 Heap. hdr = the first 0x20 bytes of the allocation, base = its address. A segment is only accepted when
   its Heap pointer is one of the process's heaps (GetProcessHeaps), which a coincidence of the signature alone could not fake. */
static int klmr_seg_hdr(const unsigned char *hdr, const uintptr_t *heaps, int nheaps)
{
    uint32_t sig, heap; int i;
    sig = (uint32_t)hdr[8] | (uint32_t)hdr[9] << 8 | (uint32_t)hdr[10] << 16 | (uint32_t)hdr[11] << 24;
    heap = (uint32_t)hdr[0x18] | (uint32_t)hdr[0x19] << 8 | (uint32_t)hdr[0x1a] << 16 | (uint32_t)hdr[0x1b] << 24;
    if (sig != 0xFFEEFFEEu) return 0;
    for (i = 0; i < nheaps; i++) if ((uint32_t)heaps[i] == heap) return 1;
    return 0;
}

/* ---- when to release: the level was left (scene key changed / vanished) or the level's big block was freed, SettleMS later,
   not more often than CooldownMS. now and stamp are tick counts (unsigned wrap is fine). stamp 0 = never. */
struct klmr_trig { int was_level; unsigned armed_at, last_run, last_stamp; int armed, ran; };

static int klmr_due(unsigned now, unsigned since, unsigned ms) { return (unsigned)(now - since) >= ms; }

/* returns 1 = run the release now */
static int klmr_trig_step(struct klmr_trig *t, int in_level, unsigned stamp, unsigned now, unsigned settle_ms, unsigned cooldown_ms)
{
    int run = 0;
    if (t->was_level && !in_level) { t->armed = 1; t->armed_at = now; }
    t->was_level = in_level;
    if (stamp && stamp != t->last_stamp) { t->last_stamp = stamp; t->armed = 1; t->armed_at = stamp; }
    if (t->armed && klmr_due(now, t->armed_at, settle_ms)) {
        t->armed = 0;
        if (!t->ran || klmr_due(now, t->last_run, cooldown_ms)) { t->ran = 1; t->last_run = now; run = 1; }
    }
    return run;
}

/* a signed MB figure for the log: before -> after of a value that should fall or rise */
static double klmr_mb(size_t bytes) { return bytes / 1048576.0; }

#endif /* KLMEMFREE_LOGIC_H */
