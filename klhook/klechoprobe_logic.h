/*
 * klechoprobe_logic.h - pure part of [Echo] Probe (klecho.c): which played voices carry the EFX aux send, named so a log reader can tell
 * gunshots from the rest. No windows.h. Off-game self-test: klechoprobe_test.c (tools/kl_tests.py).
 *
 * WHAT THE ENGINE DOES (kl2.exe read statically 2026-11-08, re/gun_echo_1107.md section 6):
 *   voice object = ZSoundBufferOpenAL (vtable 0xb9ad5c, base voice vtable 0xb9a89c), size 0x43d0
 *     +0x10 byte  send3d  = !(flags >> 5 & 1)   set by 0x4465f0 (voice init, flags = its 3rd argument)
 *     +0x11 byte  send2d  = (flags >> 6) & 1
 *     +0x54 dword relative = its 2nd argument; creation (vtable +8 = 0x658340) passes it to alSourcei(AL_SOURCE_RELATIVE 0x202)
 *     +0x60 dword wave descriptor pointer; +0x78 kind (1 in-memory, 3 streamed); +0x5c gain; +0x43bc the AL source id
 *   creation 0x658340: attaches the aux slot (alSource3i(src, 0x20006, [listener+0x23c18], 0, 0)) iff the listener reports EFX
 *     (listener vtable +0xd8 true) AND relative == 0 AND send3d != 0.
 *   play 0x5dbd50 (vtable +0x10): alSourcePlay, THEN attaches the same slot iff relative != 0 AND send2d != 0.
 *   => a world (3D) voice gets the send unless its sound flag bit 5 is set; a 2D / relative voice gets it only when flag bit 6 is set.
 */
#ifndef KLECHOPROBE_LOGIC_H
#define KLECHOPROBE_LOGIC_H

#include <string.h>
#include <stdio.h>

#define KPR_NAMES 40          /* distinct names in the summary table */
#define KPR_NAMELEN 48

struct kpr_ent { char name[KPR_NAMELEN]; unsigned with_send, without_send; };
struct kpr_stats {
    unsigned played, with_send, without_send, gun_with, gun_without;
    unsigned late_send;                    /* of with_send: attached only AFTER alSourcePlay (relative voices) */
    unsigned unknown;                      /* readback and prediction both unavailable (counted as without) */
    struct kpr_ent ent[KPR_NAMES]; int nent;
};

/* prediction from the voice fields: 1 = send expected at creation (3D), 2 = expected after Play (2D / relative), 0 = none */
static int kpr_predict(int relative, int send3d, int send2d, int efx_listener)
{
    if (!efx_listener) return 0;
    if (!relative) return send3d ? 1 : 0;
    return send2d ? 2 : 0;
}

/* case-insensitive substring */
static int kpr_has(const char *s, const char *sub)
{
    size_t n = strlen(sub), i, j;
    for (i = 0; s[i]; i++) {
        for (j = 0; j < n; j++) {
            char a = s[i + j], b = sub[j];
            if (!a) return 0;
            if (a >= 'A' && a <= 'Z') a = (char)(a + 32);
            if (b >= 'A' && b <= 'Z') b = (char)(b + 32);
            if (a != b) break;
        }
        if (j == n) return 1;
    }
    return 0;
}

/* GUESS: gun voices carry "shot" / "fire" / "weapon" / "gun" / "distant" in the wave path or the sound name. Not verified in the game. */
static int kpr_gunish(const char *name)
{
    static const char *k[] = { "shot", "weapon", "gun", "rifle", "pistol", "smg", "shotgun", "distant", "fire_", "_fire", "mg42", "ak47", 0 };
    int i;
    if (!name || !name[0]) return 0;
    if (kpr_has(name, "footstep") || kpr_has(name, "reload") || kpr_has(name, "dialog") || kpr_has(name, "dryfire")) return 0;
    for (i = 0; k[i]; i++) if (kpr_has(name, k[i])) return 1;
    return 0;
}

/* does buf[0..n) start with a plausible sound / resource name: >= 4 printable ASCII chars, at least one letter, a NUL within n.
   Writes the name (at most cap-1 chars) to out. Returns its length, or 0. */
static int kpr_name_from(const unsigned char *buf, int n, char *out, int cap)
{
    int i, letters = 0;
    for (i = 0; i < n && buf[i]; i++) {
        unsigned char c = buf[i];
        if (c < 0x20 || c > 0x7e) return 0;
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) letters++;
    }
    if (i >= n || i < 4 || !letters) return 0;      /* no NUL inside the window, too short, or digits only */
    if (i > cap - 1) i = cap - 1;
    memcpy(out, buf, (size_t)i); out[i] = 0;
    return i;
}

/* prefer a candidate that looks like a path / file / audio: score for picking among several string-looking pointers */
static int kpr_name_score(const char *s)
{
    int sc = 1;
    if (strchr(s, '/') || strchr(s, '\\')) sc += 3;
    if (kpr_has(s, ".wav") || kpr_has(s, "audio:")) sc += 3;
    if (kpr_gunish(s)) sc += 1;
    return sc;
}

static void kpr_init(struct kpr_stats *s) { memset(s, 0, sizeof *s); }

/* record one played voice. with = it carries (or will carry) a send. late = only after Play. -> 0 ok */
static void kpr_add(struct kpr_stats *s, const char *name, int with, int late, int unknown)
{
    int i, gun = kpr_gunish(name);
    s->played++;
    if (with) { s->with_send++; if (late) s->late_send++; if (gun) s->gun_with++; }
    else { s->without_send++; if (gun) s->gun_without++; }
    if (unknown) s->unknown++;
    if (!name || !name[0]) name = "(unnamed)";
    for (i = 0; i < s->nent; i++) if (!strncmp(s->ent[i].name, name, KPR_NAMELEN - 1)) break;
    if (i == s->nent) {
        if (s->nent >= KPR_NAMES) return;            /* table full: totals above still count it */
        strncpy(s->ent[i].name, name, KPR_NAMELEN - 1); s->ent[i].name[KPR_NAMELEN - 1] = 0; s->nent++;
    }
    if (with) s->ent[i].with_send++; else s->ent[i].without_send++;
}

/* index of the entry with the most plays WITHOUT a send, excluding those in skip[] (a bitmask over the first 32 entries); -1 if none */
static int kpr_top_without(const struct kpr_stats *s, unsigned skip)
{
    int i, best = -1;
    for (i = 0; i < s->nent && i < 32; i++) {
        if (skip & (1u << i) || !s->ent[i].without_send) continue;
        if (best < 0 || s->ent[i].without_send > s->ent[best].without_send) best = i;
    }
    return best;
}

/* one summary line: totals, the gun-like split, the top 'topn' (<= 4) names without a send. Returns chars written (snprintf semantics are
   not assumed: the buffer is always terminated). */
static int kpr_summary(const struct kpr_stats *s, const char *tag, char *out, int cap, int topn)
{
    int n = 0, k; unsigned skip = 0;
    #define KPR_PUT(...) do { int w_ = snprintf(out + n, (size_t)(cap - n), __VA_ARGS__); if (w_ < 0 || w_ >= cap - n) { n = cap - 1; out[n] = 0; return n; } n += w_; } while (0)
    out[0] = 0;
    KPR_PUT("echo-probe %s: played %u, send %u (late %u), no send %u, unknown %u | gun-like: send %u, no send %u | no-send top:",
            tag, s->played, s->with_send, s->late_send, s->without_send, s->unknown, s->gun_with, s->gun_without);
    if (topn > 4) topn = 4;
    for (k = 0; k < topn; k++) {
        int i = kpr_top_without(s, skip);
        if (i < 0) { if (!k) KPR_PUT(" (none)"); break; }
        skip |= 1u << i;
        KPR_PUT(" %s x%u%s", s->ent[i].name, s->ent[i].without_send, kpr_gunish(s->ent[i].name) ? " [gun-like]" : "");
    }
    #undef KPR_PUT
    return n;
}

/* log budget: first 'always' lines unconditionally, then only a (name, state) pair not seen before, hard cap 'cap'. seen[] holds hashes. */
struct kpr_log { unsigned seen[96]; int nseen, lines, always, cap; };
static unsigned kpr_hash(const char *s, int state)
{
    unsigned h = 2166136261u + (unsigned)state * 16777619u;
    while (*s) { h ^= (unsigned char)*s++; h *= 16777619u; }
    return h;
}
static int kpr_log_ok(struct kpr_log *l, const char *name, int state)
{
    unsigned h; int i, dup = 0;
    if (l->lines >= l->cap) return 0;
    h = kpr_hash(name ? name : "", state);
    for (i = 0; i < l->nseen; i++) if (l->seen[i] == h) dup = 1;
    if (dup && l->lines >= l->always) return 0;
    if (!dup && l->nseen < 96) l->seen[l->nseen++] = h;
    l->lines++;
    return 1;
}

#endif /* KLECHOPROBE_LOGIC_H */
