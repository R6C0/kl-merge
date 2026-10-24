/*
 * klvoice.c - A DEAD MEN VOICE OF THEIR OWN for the eight Dead Men heisters (owner 2026-10-23: 'the dead men characters
 * dont have their own voicelines still ... give them unique talks when theyre together even in dog days too').
 * Part of KLHook (included by klhook.c right AFTER kltalk.c, SHIP and TEST alike). Off unless KLHook.ini has
 * [Voice] Enable=1. Spec and the guesses: re\voice_1023.md. Data side: tools\kl_dmvoice.py.
 *
 * WHAT IT DOES. The Dog Days FA events (Backstab, JackPot, CallEsc, ...) are said by the SPEECH MANAGER [0x168e958]
 * from LINES that hold ten entries, K_C1 .. K_C9 (+ one more): the player of voice number v says entry v (0x421c70
 * plays data[rules+0x33e+slot], the voice table klchar.c / klcrew.c already hand out per body). A Dead Men body
 * therefore spoke a Dog Days heister's recording. Here: for every crew member who wears Kane, Lynch, Ashkanan, Meldal,
 * Red, Parker, Standen or Hutchison, the entry of HIS voice number is replaced, in every such line, by an entry made
 * for the .LOC key KLVoice/<Name>/<Event> (the event = the line's key text without folder and _C<n>; the radio twin
 * 'Event_R' lives at KLVoice/<Name>_R/Event - a .LOC table holds 255 leaves at most). tools\kl_dmvoice.py grafts those
 * leaves (campaign clips of that character, or the closest-fitting campaign voice) into the level's .LOC and sound bank.
 * A leaf the level does not have leaves the line as it is. The pointers replaced are remembered and put back when the
 * member no longer wears the body, when the level generation ends, or when the round state is gone.
 *
 * MECHANISM (kl2.exe build 0490; the layout read from 0x877a30 / 0x4c74b0 / 0x421c70 by disassembly 2026-10-23, NEVER
 * SEEN LIVE - every number below is a GUESS until a log line proves it; [Voice] Log=2 prints what is walked):
 *    manager + g*0x18 (g = 0..93): a group { +4 count (<= 3), +8 capacity, +0x10 data pointer to the line pointers };
 *    manager + 0x8d0 .. +0x918: 19 single line pointers (what the loader fills);
 *    a line (0x28 bytes): +0x20 flag (1 = per-character), +8 vector count, +0x14 vector data = the entry pointers,
 *    an ENTRY (0x204): [entry] = what the .LOC lookup found, key text at entry+4.
 *    The voice table: rules + 0x33e + record = the entry number that record speaks with (klw_voices / klc_voice_swap).
 * NO CODE BYTE IS PATCHED and no game function is called but the .LOC lookup 0x828fa0 (as kltalk.c does); the writes
 * are DATA only (klh_data: one dword of a heap array per entry), so a SHIP build may do it. Offline Arcade only
 * (klw_who_now). Game thread only.
 *
 * INI [Voice]:  RadioFallback=0 (1: a radio line whose KLVoice/<Name>_R leaf is missing takes the plain KLVoice/<Name> leaf of the same event)
 *               PlayedLog=1 (with Log=2: 'voice: QUEUED <leaf> ...' when the game queues an entry we swapped)
 *               PlayLog=0 (1 + Log=2: retargets the 5 play calls of 0x421c70: 'voice: SAY site N ..' per line said, 'voice: PLAYING ..' on
 *                          [queue+0xd8] change. CODE PATCH: TEST build with [KLHook] SessionSafe=0 only; see VOICEPLAIN below)
 *               Plain=0 (1: the flag-0 lines (FA_YouEscaped*_R, police events) speak the body's KLVoice leaf too; needs the call-site patch)
 *               PlainData=0 (1: SHIPPABLE data-only fix: each flag-0 line is turned into a per-character line in memory, see PLAINDATA; Log=2 'voice: plaindata:' lines)
 *               Enable=0   StockLevels=0 (1 = also on a level the verdict calls stock; the DD01..DD09 copies carry the leaves)
 *               Log=1 (0 none, 1 the summary lines, 2 every swap)   Period=1500 (ms between two walks)
 */
#ifndef KLVOICE_C
#define KLVOICE_C

#define KVO_GROUPS     94
#define KVO_SINGLES    19
#define KVO_NENTRY     4096
#define KVO_NREC       4096
#define KVO_HASH       8192

static const char *const kvo_names[8] = { "Kane", "Lynch", "Ashkanan", "Meldal", "Red", "Parker", "Standen", "Hutchison" };

static struct { int on, stock, log, period, radiofb, played, playlog, plain, plaindata; } kvo;     /* radiofb/played: [Voice] RadioFallback / PlayedLog (2026-10-23 voiceheard); playlog/plain: PlayLog / Plain (voiceplain) */
static struct {                                  /* the entries made for this level generation (never freed: the game may hold them) */
    DWORD rules, mgr, lm; char scene[160]; int n, toldfull;
    int told_q;                                   /* PlayedLog state: zeroed with the generation (review 1) */
    struct { DWORD hash; void *entry; int found; DWORD lastq; char path[128]; } e[KVO_NENTRY];
} kvo_gen;
static struct { DWORD addr, orig, ours; int active; } kvo_rec[KVO_NREC];
static short kvo_ix[KVO_HASH];                   /* hash of addr -> record index + 1 */
static int kvo_nrec;
static struct { int walks, lines, swapped, restored, missing, told_layout, told_none; DWORD sig, next; char had; } kvo_s;

static int kvo_name_of(const char *n)
{
    int i;
    for (i = 0; i < 8; i++) if (!_stricmp(n, kvo_names[i])) return i + 1;
    return 0;
}

/* (voiceplain 2026-10-23: the checksum 'entry USED?' signal was removed - nothing in the game writes into an entry block, so it could not fire.) */

/* the entry of a .LOC key, made as kltalk.c's klk_entry makes it (own cache: the talk cache holds 640 and is shared) */
static void *kvo_entry(const char *key, DWORD rules, const char *scene)
{
    DWORD h = klk_hash(key), sys, a, lm, found; void *e; int i;
    if (kvo_gen.rules != rules || strcmp(kvo_gen.scene, scene)) { memset(&kvo_gen, 0, sizeof kvo_gen); kvo_gen.rules = rules; snprintf(kvo_gen.scene, sizeof kvo_gen.scene, "%s", scene); }
    for (i = 0; i < kvo_gen.n; i++) if (kvo_gen.e[i].hash == h) return kvo_gen.e[i].found ? kvo_gen.e[i].entry : 0;
    if (kvo_gen.n >= KVO_NENTRY) { if (!kvo_gen.toldfull++) klog("voice: %d keys were looked up on this level: no further one is used", KVO_NENTRY); return 0; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(a = klh_rd32(sys + 0xac)) || !klh_rd(a + 0x94, &lm, 4) || !lm || !klh_rd(lm, &found, 4)) return 0;     /* not remembered */
    if (!(e = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, 0x204))) return 0;
    found = (DWORD)(DWORD_PTR)((void *(__fastcall *)(void *, void *, const char *, void *))(DWORD_PTR)KLH_VA(KLK_LOOKUP))((void *)(DWORD_PTR)lm, 0, key, e);
    kvo_gen.e[kvo_gen.n].hash = h; kvo_gen.e[kvo_gen.n].entry = e; kvo_gen.e[kvo_gen.n].found = found && *(DWORD *)e;
    snprintf(kvo_gen.e[kvo_gen.n].path, sizeof kvo_gen.e[0].path, "%s", key);
    kvo_gen.n++;
    return kvo_gen.e[kvo_gen.n - 1].found ? e : 0;
}

static int kvo_find(DWORD addr, int make)
{
    DWORD h = (addr >> 2) * 2654435761u; int i, k;
    for (k = 0; k < KVO_HASH; k++) {
        i = (int)((h + (DWORD)k) % KVO_HASH);
        if (!kvo_ix[i]) {
            if (!make || kvo_nrec >= KVO_NREC) return -1;
            kvo_rec[kvo_nrec].addr = addr; kvo_ix[i] = (short)(++kvo_nrec);
            return kvo_nrec - 1;
        }
        if (kvo_rec[kvo_ix[i] - 1].addr == addr) return kvo_ix[i] - 1;
    }
    return -1;
}

/* put back every pointer of ours that is still there */
static void kvo_restore_all(const char *why)
{
    int i, n = 0;
    for (i = 0; i < kvo_nrec; i++) {
        DWORD cur = 0;
        if (kvo_rec[i].active && klh_rd(kvo_rec[i].addr, &cur, 4) && cur == kvo_rec[i].ours && klh_data((void *)(DWORD_PTR)kvo_rec[i].addr, &kvo_rec[i].orig, 4, "voice entry restore")) n++;
        kvo_rec[i].active = 0;
    }
    if (kvo_nrec && kvo.log) klog("voice: %s: %d of %d replaced entries put back", why, n, kvo_nrec);
    memset(kvo_rec, 0, sizeof kvo_rec); memset(kvo_ix, 0, sizeof kvo_ix); kvo_nrec = 0;
}

/* 1 the first time this scene + path is asked about: a missing leaf is logged once, not on every walk (V2_DM01 wrote 14,756) */
static int kvo_first_miss(const char *scene, const char *path)
{
    static DWORD seen[1024]; static int nseen; DWORD h = 2166136261u; const char *p; int i;
    for (p = scene; *p; p++) h = (h ^ (BYTE)*p) * 16777619u;
    for (p = path; *p; p++) h = (h ^ (BYTE)*p) * 16777619u;
    for (i = 0; i < nseen; i++) if (seen[i] == h) return 0;
    if (nseen < 1024) seen[nseen++] = h;
    return 1;
}

/* the event leaf of a line: its key text 'Multiplayer/F01/Backstab_01_R_C3' -> 'Backstab_01_R'. 0 = not an event line. */
static int kvo_leaf(const char *text, char leaf[64])
{
    const char *s = strrchr(text, '/'); size_t n; int i;
    s = s ? s + 1 : text; n = strlen(s);
    if (n < 4 || n >= 64) return 0;
    for (i = (int)n - 1; i > 0 && s[i] >= '0' && s[i] <= '9'; i--) ;
    if (i < 2 || i == (int)n - 1 || s[i] != 'C' || s[i - 1] != '_') return 0;
    memcpy(leaf, s, (size_t)i - 1); leaf[i - 1] = 0;
    return 1;
}

/* ------------------------------------------------------------------------------------------------------------------
 * PLAINDATA (2026-10-24, re/voiceplain_1023.md section 5): a SHIPPABLE way for the flag-0 lines, DATA ONLY (no code byte).
 *   0x421c70 reads, for a flag-1 line on the Arcade path (site 0x421e76), data[voice] = [[line+0x14] + 4*voice] and the flag byte [line+0x20];
 *   it never reads a flag-1 line's [line+0]. So a flag-0 line (one entry at [line+0]) is turned into a per-character line IN MEMORY:
 *   a KVO_NV (256) pointer vector (every slot = the stock entry, the slots of the Dead Men voice numbers = our KLVoice entries), count [line+8]=KVO_NV,
 *   cap [line+0xc]=KVO_NV, data [line+0x14]=vector, flag [line+0x20]=1. Restored (flag 0, old count/cap/data) when the generation ends,
 *   when the round is gone or when the level is not a Dead Men one. The vector is from MSVCR90's malloc because the line's destructor / grow
 *   path frees [line+0x14] with MSVCR90.free (GUESS from the 0x6b8710 listing: realloc/free are msvcr90 imports). Never freed by us (1 KB).
 *   GUESS: the flag-1 path of 0x421c70 needs no other field of a line built with flag 0 (+0x1c float, +0x24 priority are set for both flags).
 *   Sites 0x4220b3 / 0x42211b (non-Arcade modes) are not served (GUESS: they pick the vector slot by a mode switch) - Arcade only like the rest. */
#define KVO_NCV 512
static struct { DWORD ln, vec, ocnt, ocap, odata, entry; char leaf[64]; } kvo_cv[KVO_NCV];
#define KVO_NV 256   /* vector length: 0x51ab20 (the vector index) executes int3 when index >= count, and a flag-0 line's callers may pass a speaker whose voice byte is > 9 (GUESS: not checked), so every byte value gets a slot */
static DWORD kvo_cv_sigdone;                                    /* walk signature the converted lines were last refreshed for (review: no 4096-key scan per line every walk) */
static DWORD kvo_cv_tried[KVO_NCV], kvo_cv_trysig; static int kvo_cv_ntried;     /* flag-0 lines with no leaf for anybody at kvo_cv_trysig: not asked again until the wearers change */
static int kvo_ncv, kvo_cv_told;
static void *(__cdecl *kvo_malloc)(size_t);

static int kvo_cv_find(DWORD ln) { int i; for (i = 0; i < kvo_ncv; i++) if (kvo_cv[i].ln == ln) return i; return -1; }

static void kvo_cv_restore(const char *why)
{
    int i, n = 0;
    for (i = 0; i < kvo_ncv; i++) {
        DWORD ln = kvo_cv[i].ln, data = 0, cc[2]; BYTE f0 = 0, fl = 0;
        /* review: also count == cap == KVO_NV, so a line that was freed and whose block was reused is never written */
        if (klh_rd(ln + 0x20, &fl, 1) && fl == 1 && klh_rd(ln + 0x14, &data, 4) && data == kvo_cv[i].vec && klh_rd(ln + 8, cc, 8) && cc[0] == KVO_NV && cc[1] == KVO_NV) {
            DWORD o[2]; o[0] = kvo_cv[i].ocnt; o[1] = kvo_cv[i].ocap;
            if (klh_data((void *)(DWORD_PTR)(ln + 0x20), &f0, 1, "voice plaindata restore") &&
                klh_data((void *)(DWORD_PTR)(ln + 8), o, 8, "voice plaindata restore") &&
                klh_data((void *)(DWORD_PTR)(ln + 0x14), &kvo_cv[i].odata, 4, "voice plaindata restore")) n++;
        }
    }
    if (kvo_ncv && kvo.log) klog("voice: plaindata: %s: %d of %d converted single-entry lines put back", why, n, kvo_ncv);
    memset(kvo_cv, 0, sizeof kvo_cv); kvo_ncv = 0; kvo_cv_told = 0; kvo_cv_sigdone = 0; kvo_cv_ntried = 0; kvo_cv_trysig = 0;
}

/* ln is a flag-0 line the walk found (isours 0) or one of our converted lines (isours 1, flag 1, data == our vector): make / refresh the vector.
   who[v] = Dead Men name of voice number v, or "". */
static void kvo_cv_line(DWORD ln, int isours, char who[8][32], DWORD rules, const char *scene)
{
    DWORD entry = 0, vec, hdr[2]; char text[130], leaf[64]; const char *s; int k = -1, slot, any = 0, c = 0; size_t n; DWORD ents[KVO_NV]; int i;
    if (isours) { k = kvo_cv_find(ln); if (k < 0) return; snprintf(leaf, sizeof leaf, "%s", kvo_cv[k].leaf); entry = kvo_cv[k].entry; }
    else {
        entry = klh_rd32(ln);
        if (!entry || !klh_rdstr((DWORD_PTR)entry + 4, text, sizeof text)) return;
        if (kvo_leaf(text, leaf)) return;                       /* has _C<n>: not a single-entry event key, leave it */
        s = strrchr(text, '/'); s = s ? s + 1 : text; n = strlen(s);
        if (n < 2 || n >= sizeof leaf) return;
        memcpy(leaf, s, n + 1);                                  /* GUESS: the flag-0 event leaf is the whole last path part, as Plain assumed */
    }
    for (slot = 0; slot < 8; slot++) {
        char path[128]; void *e; size_t l2 = strlen(leaf);
        ents[slot] = entry;
        if (!who[slot][0]) continue;
        if (l2 > 2 && !strcmp(leaf + l2 - 2, "_R")) snprintf(path, sizeof path, "KLVoice/%s_R/%.*s", who[slot], (int)(l2 - 2), leaf);
        else snprintf(path, sizeof path, "KLVoice/%s/%s", who[slot], leaf);
        e = kvo_entry(path, rules, scene);
        if (!e && kvo.radiofb && l2 > 2 && !strcmp(leaf + l2 - 2, "_R")) { char p2[128]; snprintf(p2, sizeof p2, "KLVoice/%s/%.*s", who[slot], (int)(l2 - 2), leaf); e = kvo_entry(p2, rules, scene); if (e) snprintf(path, sizeof path, "%s", p2); }
        if (!e) { if (kvo.log > 1 && kvo_first_miss(scene, path)) klog("voice: plaindata: %s: no leaf %s (logged once)", leaf, path); continue; }
        ents[slot] = (DWORD)(DWORD_PTR)e; any = 1; c++;
    }
    for (i = 8; i < KVO_NV; i++) ents[i] = entry;               /* the voice numbers are 0..7; every other index stays stock (never null, never out of range) */
    if (isours) {                                               /* refresh the vector in place (the wearers changed) */
        if (memcmp((void *)(DWORD_PTR)kvo_cv[k].vec, ents, sizeof ents) && klh_data((void *)(DWORD_PTR)kvo_cv[k].vec, ents, sizeof ents, "voice plaindata slots") && kvo.log > 1)
            klog("voice: plaindata: line %08lx refreshed, %d of 8 slots ours (%s)", ln, c, leaf);
        return;
    }
    if (!any || kvo_ncv >= KVO_NCV) {                           /* nothing of ours for this event: the line stays stock and single; not asked again until the wearers change */
        if (!any && kvo_cv_ntried < KVO_NCV) kvo_cv_tried[kvo_cv_ntried++] = ln;
        return;
    }
    if (!kvo_malloc) { HMODULE m = GetModuleHandleA("msvcr90.dll"); kvo_malloc = m ? (void *(__cdecl *)(size_t))GetProcAddress(m, "malloc") : 0; }
    if (!kvo_malloc) { if (!kvo_cv_told++) klog("voice: plaindata: msvcr90 malloc not found - off"); return; }
    if (!klh_rd(ln + 8, hdr, 8)) return;
    if (!(vec = (DWORD)(DWORD_PTR)kvo_malloc(sizeof ents))) return;
    memcpy((void *)(DWORD_PTR)vec, ents, sizeof ents);
    kvo_cv[kvo_ncv].ln = ln; kvo_cv[kvo_ncv].vec = vec; kvo_cv[kvo_ncv].ocnt = hdr[0]; kvo_cv[kvo_ncv].ocap = hdr[1]; kvo_cv[kvo_ncv].odata = klh_rd32(ln + 0x14);
    kvo_cv[kvo_ncv].entry = entry; snprintf(kvo_cv[kvo_ncv].leaf, sizeof kvo_cv[kvo_ncv].leaf, "%s", leaf);
    { DWORD nw[2] = { KVO_NV, KVO_NV }, od = klh_rd32(ln + 0x14); BYTE one = 1, zero = 0;   /* data first, then count / cap, the flag last; any refusal undoes what was written (review) */
      if (!klh_data((void *)(DWORD_PTR)(ln + 0x14), &vec, 4, "voice plaindata")) { if (!kvo_cv_told++) klog("voice: plaindata: a write was refused"); return; }
      if (!klh_data((void *)(DWORD_PTR)(ln + 8), nw, 8, "voice plaindata") || !klh_data((void *)(DWORD_PTR)(ln + 0x20), &one, 1, "voice plaindata")) {
          klh_data((void *)(DWORD_PTR)(ln + 0x20), &zero, 1, "voice plaindata undo"); klh_data((void *)(DWORD_PTR)(ln + 8), hdr, 8, "voice plaindata undo");
          klh_data((void *)(DWORD_PTR)(ln + 0x14), &od, 4, "voice plaindata undo");
          if (!kvo_cv_told++) klog("voice: plaindata: a write was refused"); return; } }
    kvo_ncv++;
    if (kvo.log > 1) klog("voice: plaindata: line %08lx (event %s, stock entry %08lx) now per-character: vector %08lx, %d of 8 voice slots ours", ln, leaf, entry, vec, c);
}

/* ------------------------------------------------------------------------------------------------------------------
 * VOICEPLAIN (2026-10-23, re\voiceplain_1023.md). WHAT THE RE FOUND (static, kl2.exe 0490, listings 0x421c70 / 0x578840 / 0x7d0e80):
 *   Every speech line goes through 0x421c70(ecx = speech manager, line, other, speaker, x) (ret 0x10). It ends in a play call
 *   `call 0x578840` at FIVE sites, __thiscall: ecx = queue [manager+0x974], stack (entry, priority = [line+0x24], speaker,
 *   float 0.xx, last = x) and `ret 0x14`. 'speaker' is the 421c70 argument as it came in: a CREW RECORD number (0..7), or 0xfe / 0xfa
 *   (random). The voice number is rules+0x33e+record (0x6ae750) - exactly what this file's walk uses (tab[w.m[i].rec]).
 *     0x421e76  flag-1 line, Arcade round : entry = per-voice vector [line+0x14][voice]   (swapped by the walk below)
 *     0x421ec3  flag-0 line, Arcade round : entry = the single entry [line+0]              (NOT swapped by the walk: PLAIN)
 *     0x4220b3  flag-1 line, other mode   : entry = vector slot by a game-mode switch
 *     0x42211b  flag-0 line, other mode   : entry = [line+0]                                (PLAIN)
 *     0x422156  the 'other' line [arg2]   : entry = [other+0]                               (PLAIN, if the walk knows that entry)
 *   0x578840 plays at once (0x7d0e80: stores the started entry at [queue+0xd8], the speaker byte at [queue+0xd4], a time float at
 *   [queue+0xcc]) or queues a 20-byte record.
 *
 * PlayLog=1 (with Log=2): the five call sites are retargeted to naked thunks (kvo_t1..kvo_t5 -> kvo_common -> kvo_hook) which log
 *   'voice: SAY site N entry .. node .. speaker .. (ours <path> | stock <key>)' (rate limited) and jump to 0x578840 with the
 *   original arguments (Plain=1 may replace the entry argument first). Probe A (data only, works in a SHIP build): when
 *   [[manager+0x974]+0xd8] (or the time float [queue+0xcc]) changes, 'voice: PLAYING ..'.
 * Plain=1: the walk (every flag-0 line of the manager, ALL groups) records entry -> event leaf and resolves, for each voice number
 *   a Dead Men body wears, the entry of KLVoice/<Name>/<leaf> (or <Name>_R for a '_R' event) - kvo_entry, the same cache and
 *   the same .LOC lookup as the flag-1 path. At the thunk: speaker record -> voice number (snapshot of the last tick) -> the
 *   resolved entry replaces the entry argument; no leaf = stock stays. No allocation and no lookup in the thunk.
 * CODE PATCH: this is the one place klvoice.c patches code (5 x 5 bytes). The sites are inside HASHED ranges (0x41e000..0x42a000), so the
 *   guard (klhook.c) refuses them in a SHIP build and in a TEST build with SessionSafe=1: it takes a TEST build with
 *   [KLHook] SessionSafe=0, i.e. a direct-boot run (-o DefaultScene=..). Never start a real session with it. Refusals are logged by
 *   the guard ('patch REFUSED'); the data-only parts (probe A, QUEUED, the walk's flag-0 bookkeeping) still work. */
#define KVO_NF0 1024
static struct {
    int primed;                                   /* kvo_played has taken its first sample since the last reset */
    int valid;                                    /* the snapshot below is from the current tick of a Dead Men round */
    BYTE tab[8];                                  /* rules+0x33e: crew record -> voice number */
    int nf0, toldfull, said, nrep, nsite[6];
    DWORD last_play, last_cc, ring_e[8], ring_t[8]; int ring_s[8], ring_n;
    struct { DWORD entry; DWORD rep[8]; char leaf[64]; } f0[KVO_NF0];     /* rep[voice number] = our entry for that body, 0 = stock */
} kvo_p;
static int kvo_patched;                           /* 0 not tried, 1 all five sites, -1 refused / failed (tried once) */
static DWORD kvo_real;                            /* 0x578840 */

/* the path of ours an entry pointer belongs to, or 0 */
static const char *kvo_ours(DWORD entry)
{
    int i;
    if (!entry) return 0;
    for (i = 0; i < kvo_gen.n; i++) if (kvo_gen.e[i].found && (DWORD)(DWORD_PTR)kvo_gen.e[i].entry == entry) return kvo_gen.e[i].path;
    return 0;
}

/* Plain: the flag-0 line [ln+0] is an entry whose key text is the event ('Multiplayer/F01/FA_YouEscaped01_R', no '_C<n>'); remember the
   entry -> leaf and resolve the replacement for every voice number a Dead Men body wears. who[v] = name or "". */
static void kvo_f0_note(DWORD ln, char who[8][32], DWORD rules, const char *scene)
{
    DWORD entry = klh_rd32(ln); char text[130], leaf[64]; const char *s; int k, slot; size_t n;
    if (!entry || !klh_rdstr((DWORD_PTR)entry + 4, text, sizeof text)) return;
    if (kvo_gen.n >= KVO_NENTRY * 3 / 4) { if (!kvo_p.toldfull++ && kvo.log) klog("voice: plain: the key cache is 3/4 full (%d): no more flag-0 lines are looked up, so the flag-1 swaps keep room", kvo_gen.n); return; }   /* review fix 5 */
    if (!kvo_leaf(text, leaf)) {                  /* flag-0 keys carry no _C<n>: the leaf is the whole last path part (GUESS: the data tool names them so, FA_YouEscaped01_R is in voice_review.tsv) */
        s = strrchr(text, '/'); s = s ? s + 1 : text; n = strlen(s);
        if (n < 2 || n >= sizeof leaf) return;
        memcpy(leaf, s, n + 1);
    }
    for (k = 0; k < kvo_p.nf0; k++) if (kvo_p.f0[k].entry == entry) break;
    if (k == kvo_p.nf0) {
        if (k >= KVO_NF0) { if (!kvo_p.toldfull++ && kvo.log) klog("voice: plain: more than %d single-entry lines: the rest speak stock", KVO_NF0); return; }
        kvo_p.nf0++; kvo_p.f0[k].entry = entry; snprintf(kvo_p.f0[k].leaf, sizeof kvo_p.f0[k].leaf, "%s", leaf);
        if (kvo.log > 1) klog("voice: plain: single-entry line %08lx entry %08lx event %s", ln, entry, leaf);
    }
    for (slot = 0; slot < 8; slot++) {
        char path[128]; void *e; size_t l2 = strlen(leaf);
        kvo_p.f0[k].rep[slot] = 0;
        if (!who[slot][0]) continue;
        if (l2 > 2 && !strcmp(leaf + l2 - 2, "_R")) snprintf(path, sizeof path, "KLVoice/%s_R/%.*s", who[slot], (int)(l2 - 2), leaf);
        else snprintf(path, sizeof path, "KLVoice/%s/%s", who[slot], leaf);
        e = kvo_entry(path, rules, scene);
        if (!e && kvo.radiofb && l2 > 2 && !strcmp(leaf + l2 - 2, "_R")) {
            char p2[128]; snprintf(p2, sizeof p2, "KLVoice/%s/%.*s", who[slot], (int)(l2 - 2), leaf);
            e = kvo_entry(p2, rules, scene); if (e) snprintf(path, sizeof path, "%s", p2);
        }
        if (!e) { if (kvo.log > 1 && kvo_first_miss(scene, path)) klog("voice: plain: %s: no leaf %s (logged once)", leaf, path); continue; }
        kvo_p.f0[k].rep[slot] = (DWORD)(DWORD_PTR)e;
    }
}

/* the C side of the five thunks. a = the original stack arguments of 0x578840: a[0] entry, a[1] priority, a[2] speaker (dword, low byte),
   a[3] float, a[4] last. Game thread. May replace a[0] (Plain). Reads only through klh_rd*. */
static void __cdecl kvo_hook(int site, DWORD queue, DWORD *a)
{
    DWORD entry = a[0], was = entry, node = 0; int rec = (int)(BYTE)a[2], voice = -1, k, dup = 0; char key[96]; const char *o;
    if (!kvo.on) return;
    if (site >= 1 && site <= 5) kvo_p.nsite[site]++;
    if (kvo.plain && kvo_p.valid && rec < 8 && entry) {
        voice = kvo_p.tab[rec];
        if (voice < 8)
            for (k = 0; k < kvo_p.nf0; k++)
                if (kvo_p.f0[k].entry == entry) { if (kvo_p.f0[k].rep[voice]) { a[0] = kvo_p.f0[k].rep[voice]; kvo_p.nrep++; } break; }
    }
    if (!kvo.playlog || kvo.log < 2 || kvo_p.said >= 400) return;
    { DWORD now = GetTickCount();
      for (k = 0; k < 8; k++) if (kvo_p.ring_e[k] == entry && kvo_p.ring_s[k] == site && now - kvo_p.ring_t[k] < 800) dup = 1;
      if (dup) return;
      kvo_p.ring_e[kvo_p.ring_n & 7] = entry; kvo_p.ring_s[kvo_p.ring_n & 7] = site; kvo_p.ring_t[kvo_p.ring_n & 7] = now; kvo_p.ring_n++; }
    kvo_p.said++;
    node = klh_rd32(a[0]);
    o = kvo_ours(a[0]);
    key[0] = 0; if (!o) klh_rdstr((DWORD_PTR)a[0] + 4, key, sizeof key);
    if (a[0] != was) {
        char wk[96]; wk[0] = 0; klh_rdstr((DWORD_PTR)was + 4, wk, sizeof wk);
        klog("voice: SAY site %d entry %08lx node %08lx speaker %d (ours %s) [Plain: was %08lx stock %s] queue %08lx", site, a[0], node, rec, o ? o : "?", was, wk, queue);
    } else if (o) klog("voice: SAY site %d entry %08lx node %08lx speaker %d voice %d (ours %s) queue %08lx", site, entry, node, rec, voice, o, queue);
    else klog("voice: SAY site %d entry %08lx node %08lx speaker %d voice %d (stock %s) queue %08lx", site, entry, node, rec, voice, key[0] ? key : "?", queue);
}

/* ONE common body, five tiny entries that push the site number. On entry from the patched `call`: [esp] return address, then the five
   arguments; ecx = the queue (this). Stack-transparent: ends in a jump to 0x578840, which pops the arguments (ret 0x14). */
static __declspec(naked) void kvo_common(void)
{
    __asm {
        push ecx                         ; [esp] ecx, +4 site, +8 return, +0xc entry ..
        lea eax, [esp + 0xc]
        push eax                         ; a
        push ecx                         ; queue
        push dword ptr [esp + 0xc]       ; site
        call kvo_hook
        add esp, 0xc
        pop ecx
        add esp, 4                       ; the site number
        jmp dword ptr [kvo_real]
    }
}
#define KVO_THUNK(n) static __declspec(naked) void kvo_t##n(void) { __asm push n __asm jmp kvo_common }
KVO_THUNK(1) KVO_THUNK(2) KVO_THUNK(3) KVO_THUNK(4) KVO_THUNK(5)

/* retarget the five calls once (a code patch: see the CODE PATCH note above; the guard decides) */
static void kvo_patch(void)
{
    static const DWORD site[5] = { 0x421e76, 0x421ec3, 0x4220b3, 0x42211b, 0x422156 };
    void (*thunk[5])(void) = { kvo_t1, kvo_t2, kvo_t3, kvo_t4, kvo_t5 };
    int i, ok = 0;
    kvo_real = (DWORD)(DWORD_PTR)KLH_VA(0x578840);
    for (i = 0; i < 5; i++) {
        BYTE expect[5], put[5]; DWORD rel = 0x578840u - (site[i] + 5), nrel = (DWORD)(DWORD_PTR)thunk[i] - (DWORD)(DWORD_PTR)KLH_VA(site[i] + 5);
        expect[0] = put[0] = 0xE8; memcpy(expect + 1, &rel, 4); memcpy(put + 1, &nrel, 4);
        if (klh_poke(KLH_VA(site[i]), expect, 5, put, 5, "voice play call")) ok++;
    }
    kvo_patched = ok == 5 ? 1 : -1;
    klog("voice: play-call probe/plain: %d of 5 call sites retargeted (PlayLog=%d Plain=%d)%s", ok, kvo.playlog, kvo.plain,
         ok == 5 ? "" : " - the rest was refused (SHIP build, SessionSafe=1, or other bytes there); see 'patch REFUSED' above");
}

/* PlayedLog (voiceheard, 2026-10-23): the speech queue [manager+0x974]: count at [queue] (0..10), records of 20 bytes from queue+4 =
 *  { priority, entry, speaker, float, last } (kltalk.c section 1: 0x578840 queues a line the channel cannot play at once). A record
 *  whose entry is one of OURS -> 'voice: QUEUED ...'. A line played at once never shows here.
 * Probe A (voiceplain): 0x7d0e80 stores the entry it STARTS at [queue+0xd8], the speaker at [queue+0xd4] and a time float at
 *  [queue+0xcc]; a change of the entry or the float logs 'voice: PLAYING ...' (data reads only; works in a SHIP build; seen
 *  as soon as the next tick reads it, so a line started and replaced within one frame can be missed).
 * The old checksum signal 'entry USED?' was removed (nothing writes into an entry; it could not fire).
 * Runs every game-thread call. Log=2 and PlayedLog=1 / PlayLog=1. */
static void kvo_played(DWORD mgr, DWORD now)
{
    DWORD queue = klh_rd32(mgr + 0x974), cnt = 0, rec[5]; int i, k;
    if (!queue) return;
    if (kvo.playlog && kvo.log >= 2) {
        DWORD cur = klh_rd32(queue + 0xd8), cc = klh_rd32(queue + 0xcc);
        if (kvo_p.primed && cur && (cur != kvo_p.last_play || cc != kvo_p.last_cc)) {
            char key[96]; const char *o = kvo_ours(cur); BYTE spk = 0;
            klh_rd(queue + 0xd4, &spk, 1);
            key[0] = 0; if (!o) klh_rdstr((DWORD_PTR)cur + 4, key, sizeof key);
            klog("voice: PLAYING entry %08lx node %08lx speaker %d (%s %s)", cur, klh_rd32(cur), (int)spk, o ? "ours" : "stock", o ? o : (key[0] ? key : "?"));
        }
        kvo_p.last_play = cur; kvo_p.last_cc = cc; kvo_p.primed = 1;   /* review fix 2: the first sample after a reset only records (a stale entry of the last level is not a start) */
    }
    if (!kvo.played || kvo.log < 2 || !kvo_gen.n) return;
    if (klh_rd(queue, &cnt, 4) && cnt >= 1 && cnt <= 10) {
        for (k = 0; k < (int)cnt; k++) {
            if (!klh_rd(queue + 4 + (DWORD)k * 20, rec, 20)) break;
            for (i = 0; i < kvo_gen.n; i++)
                if (kvo_gen.e[i].found && (DWORD)(DWORD_PTR)kvo_gen.e[i].entry == rec[1]) {
                    if (now - kvo_gen.e[i].lastq > 1500 || !kvo_gen.e[i].lastq) {
                        /* GUESS: the speaker is a byte like [queue+0xd4] (VP1b logged 28635904 = 0x01b4f300 as the whole dword) */
                        klog("voice: QUEUED %s for speaker %lu (raw %08lx, queue %lu, priority %ld): the game is about to say our entry", kvo_gen.e[i].path, rec[2] & 0xff, rec[2], cnt, (long)rec[0]);
                        kvo_gen.told_q++;
                    }
                    kvo_gen.e[i].lastq = now ? now : 1;
                    break;
                }
        }
    }
}

static void kvo_tick(int game_thread)
{
    struct klw_who w; char scene[160], key[64], why[200], who[8][32], path[128], text[130], leaf[64], names[8][16];
    int v, i, g, j, slot, nwant = 0; BYTE tab[8]; DWORD mgr, sig = 0, now;
    if (!kvo.on || !klh_exe_ok || !game_thread) return;
    now = GetTickCount();
    if (!kvo_patched && (kvo.playlog || kvo.plain)) kvo_patch();           /* once; the guard refuses it in SHIP / SessionSafe=1 */
    kvo_p.valid = 0;                                                       /* set again below once this tick knows who wears which voice */
    if (!klw_who_now(&w)) { if (kvo_nrec) kvo_restore_all("no Arcade round"); if (kvo_ncv || kvo_cv_ntried) kvo_cv_restore("no Arcade round"); kvo_s.had = 0; return; }
    if (!klx_on || !klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    v = klx_level_verdict(scene, why);
    if (v == 1 && kvo.stock) v = 2;
    if (v != 2) { if (kvo_nrec) kvo_restore_all("not a Dead Men level"); if (kvo_ncv || kvo_cv_ntried) kvo_cv_restore("not a Dead Men level"); return; }
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLK_MANAGER)))) return;
    { DWORD sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)), a = sys ? klh_rd32(sys + 0xac) : 0, lm = 0;
      if (a) klh_rd(a + 0x94, &lm, 4);
      /* generation = rules object, scene, speech manager and LOC lookup object: any change drops what we replaced (the lines are rebuilt) */
      if (kvo_gen.rules != w.rules || kvo_gen.mgr != mgr || kvo_gen.lm != lm || strcmp(kvo_gen.scene, scene)) {
          if (kvo_nrec) kvo_restore_all("a new level generation");
          if (kvo_ncv || kvo_cv_ntried) kvo_cv_restore("a new level generation");
          memset(&kvo_p, 0, sizeof kvo_p);                 /* the single-entry lines are rebuilt with the level too */
          memset(&kvo_gen, 0, sizeof kvo_gen); kvo_gen.rules = w.rules; kvo_gen.mgr = mgr; kvo_gen.lm = lm; snprintf(kvo_gen.scene, sizeof kvo_gen.scene, "%s", scene); memset(&kvo_s, 0, sizeof kvo_s); } }
    kvo_played(mgr, now);
    if (!klh_rd(w.rules + 0x33e, tab, sizeof tab)) return;

    /* who speaks with which entry number: want[idx] = the Dead Men name, "" = a body that is not one of the eight (leaves the entry alone) */
    memset(who, 0, sizeof who); memset(names, 0, sizeof names);
    for (i = 0; i < w.n; i++) {
        const char *nm = ""; int idx;
        if (w.m[i].rec < 0 || w.m[i].rec > 7) continue;
        idx = tab[w.m[i].rec]; if (idx > 7) continue;
        if (w.m[i].ch > 0) {
            EnterCriticalSection(&klc_cs);
            if (klc_w.on && !_stricmp(w.key, klc_w.key) && w.m[i].ch <= klc_w.n && kvo_name_of(klc_w.c[w.m[i].ch - 1].name)) nm = kvo_names[kvo_name_of(klc_w.c[w.m[i].ch - 1].name) - 1];
            LeaveCriticalSection(&klc_cs);
        }
        if (!who[idx][0] && !names[idx][0]) { snprintf(who[idx], sizeof who[idx], "%s", nm); names[idx][0] = 1; }
        else if (strcmp(who[idx], nm)) who[idx][0] = 0;                                  /* two bodies share a voice number: nobody gets it */
    }
    for (i = 0; i < 8; i++) { if (who[i][0]) nwant++; sig = sig * 31 + (DWORD)(who[i][0] ? kvo_name_of(who[i]) : 0) + 1; }
    sig = sig * 31 + w.rules;
    memcpy(kvo_p.tab, tab, sizeof tab); kvo_p.valid = 1;     /* the thunks (Plain) read this snapshot: crew record -> voice number; the reps below say who wears it */
    if (sig == kvo_s.sig && now < kvo_s.next) return;
    kvo_s.sig = sig; kvo_s.next = now + (DWORD)kvo.period;

    kvo_s.walks++;
    if (kvo.plaindata && kvo_cv_trysig != sig) { kvo_cv_ntried = 0; kvo_cv_trysig = sig; }     /* the wearers changed: lines without a leaf are asked again */
    {
        int nl = 0, nsw = 0, nrs = 0, nmiss = 0;
        for (g = 0; g < KVO_GROUPS + 1; g++) {
            DWORD grp[6], lines[KVO_SINGLES], ln; int cnt, lk;
            if (g < KVO_GROUPS) {
                if (!klh_rd(mgr + (DWORD)g * 0x18, grp, 0x18)) continue;
                cnt = (int)grp[1]; if (cnt < 1 || cnt > 3 || !grp[4] || !klh_rd(grp[4], lines, (SIZE_T)cnt * 4)) continue;
            } else {
                cnt = KVO_SINGLES; if (!klh_rd(mgr + 0x8d0, lines, sizeof(DWORD) * KVO_SINGLES) ) continue;
            }
            for (lk = 0; lk < cnt; lk++) {
                DWORD ent[16], vcnt = 0, vdata = 0, src = 0; BYTE flag = 0;
                ln = lines[lk];
                if (ln && kvo.plaindata) {                       /* PlainData: our converted lines are refreshed, flag-0 lines converted */
                    BYTE f2 = 0; DWORD d2 = 0; int ci = kvo_cv_find(ln);
                    if (ci >= 0 && klh_rd(ln + 0x20, &f2, 1) && f2 == 1 && klh_rd(ln + 0x14, &d2, 4) && d2 == kvo_cv[ci].vec) { if (kvo_cv_sigdone != sig) kvo_cv_line(ln, 1, who, w.rules, scene); continue; }
                    if (ci < 0 && klh_rd(ln + 0x20, &f2, 1) && f2 == 0) {
                        int ti, tried = 0; for (ti = 0; ti < kvo_cv_ntried; ti++) if (kvo_cv_tried[ti] == ln) tried = 1;
                        if (!tried) kvo_cv_line(ln, 0, who, w.rules, scene);
                        if (tried || kvo_cv_find(ln) >= 0) continue; }
                }
                if (ln && kvo.plain && klh_rd(ln + 0x20, &flag, 1) && flag == 0) { kvo_f0_note(ln, who, w.rules, scene); continue; }      /* Plain: a flag-0 line (the walk never touches it; the thunk does) */
                if (!ln || !klh_rd(ln + 0x20, &flag, 1) || flag != 1 ||!klh_rd(ln + 8, &vcnt, 4) || vcnt < 8 || vcnt > 16 || !klh_rd(ln + 0x14, &vdata, 4) || !vdata) continue;
                if (!klh_rd(vdata, ent, vcnt * 4)) continue;
                /* the leaf comes from a slot that is not ours (ours reads 'KLVoice/..' without _C<n>); a slot of ours is read through the entry it replaced */
                for (j = 0; j < 8 && !src; j++) {
                    int rj = kvo_find(vdata + (DWORD)j * 4, 0);
                    if (rj >= 0 && kvo_rec[rj].active && ent[j] == kvo_rec[rj].ours) src = kvo_rec[rj].orig;
                    else src = ent[j];
                }
                if (!src || !klh_rdstr((DWORD_PTR)src + 4, text, sizeof text) || !kvo_leaf(text, leaf)) continue;
                nl++;
                for (slot = 0; slot < 8; slot++) {
                    DWORD addr = vdata + (DWORD)slot * 4, cur = ent[slot]; int ri = kvo_find(addr, 0);
                    if (who[slot][0]) {
                        size_t ln2 = strlen(leaf); void *e;
                        if (ln2 > 2 && !strcmp(leaf + ln2 - 2, "_R")) snprintf(path, sizeof path, "KLVoice/%s_R/%.*s", who[slot], (int)(ln2 - 2), leaf);
                        else snprintf(path, sizeof path, "KLVoice/%s/%s", who[slot], leaf);
                        if (ri >= 0 && kvo_rec[ri].active && cur != kvo_rec[ri].ours) { kvo_rec[ri].active = 0; ri = -1; }            /* the game put something else there: ours no more */
                        e = kvo_entry(path, w.rules, scene);
                        if (!e && kvo.radiofb && ln2 > 2 && !strcmp(leaf + ln2 - 2, "_R")) {          /* RadioFallback=1: no radio twin in the .LOC (tier 'no radio' of kl_dmvoice) -> the plain leaf of the same event, if it has one */
                            char p2[128]; snprintf(p2, sizeof p2, "KLVoice/%s/%.*s", who[slot], (int)(ln2 - 2), leaf);
                            e = kvo_entry(p2, w.rules, scene);
                            if (e) snprintf(path, sizeof path, "%s", p2);
                        }
                        if (!e) { nmiss++; if (kvo.log > 1 && kvo_first_miss(scene, path)) klog("voice: %s: no leaf %s (logged once)", leaf, path); continue; }
                        if ((DWORD)(DWORD_PTR)e == cur) continue;
                        if (ri < 0 && (ri = kvo_find(addr, 1)) < 0) continue;
                        if (!kvo_rec[ri].active) kvo_rec[ri].orig = cur;
                        { DWORD nv = (DWORD)(DWORD_PTR)e;
                          if (!klh_data((void *)(DWORD_PTR)addr, &nv, 4, "voice entry")) continue;
                          kvo_rec[ri].ours = nv; kvo_rec[ri].active = 1; nsw++;
                          if (kvo.log > 1) klog("voice: line %08lx slot %d (%s) -> %s", ln, slot, who[slot], path); }
                    } else if (ri >= 0 && kvo_rec[ri].active) {                                                                      /* nobody wears that voice now: his own back */
                        if (cur == kvo_rec[ri].ours && klh_data((void *)(DWORD_PTR)addr, &kvo_rec[ri].orig, 4, "voice entry restore")) nrs++;
                        kvo_rec[ri].active = 0;
                    }
                }
            }
        }
        if (kvo.plaindata) kvo_cv_sigdone = sig;
        kvo_s.lines = nl; kvo_s.swapped += nsw; kvo_s.restored += nrs; kvo_s.missing += nmiss;
        if (kvo.log && (nsw || nrs || nmiss || !kvo_s.told_layout || (!nl && !kvo_s.told_none))) {
            klog("voice: walk %d (rules %08lx): %d per-character lines, %d entries replaced, %d put back, %d without a leaf; wanted voice numbers: %d%s",
                 kvo_s.walks, w.rules, nl, nsw, nrs, nmiss, nwant, nl ? "" : " - NO per-character line found (the layout guess is wrong, or the lines are not made yet)");
            kvo_s.told_layout = 1; if (!nl) kvo_s.told_none = 1;
        }
    }
}

static void klvo_init(void)
{
    memset(&kvo, 0, sizeof kvo); memset(&kvo_gen, 0, sizeof kvo_gen); memset(&kvo_s, 0, sizeof kvo_s);
    kvo.on = GetPrivateProfileIntA("Voice", "Enable", 0, klh_ini) != 0;
    kvo.stock = GetPrivateProfileIntA("Voice", "StockLevels", 0, klh_ini) != 0;
    kvo.log = (int)GetPrivateProfileIntA("Voice", "Log", 1, klh_ini);
    kvo.period = (int)GetPrivateProfileIntA("Voice", "Period", 1500, klh_ini);
    kvo.radiofb = GetPrivateProfileIntA("Voice", "RadioFallback", 0, klh_ini) != 0;     /* default 0 = the old behaviour */
    kvo.played = GetPrivateProfileIntA("Voice", "PlayedLog", 1, klh_ini) != 0;      /* only logs, and only with Log=2 */
    kvo.playlog = GetPrivateProfileIntA("Voice", "PlayLog", 0, klh_ini) != 0;       /* default 0 = off: retargets the 5 play calls (TEST + SessionSafe=0 only) */
    kvo.plaindata = GetPrivateProfileIntA("Voice", "PlainData", 0, klh_ini) != 0;   /* default 0 = off: data-only flag-0 -> flag-1 conversion (SHIP-safe) */
    kvo.plain = GetPrivateProfileIntA("Voice", "Plain", 0, klh_ini) != 0;          /* default 0 = off: flag-0 lines speak the body's KLVoice leaf */
    memset(&kvo_p, 0, sizeof kvo_p);
    if (kvo.period < 200 || kvo.period > 60000) kvo.period = 1500;
    if (kvo.on) klog("voice: on; the Dead Men bodies' event lines come from KLVoice/<Name>/<Event> of the level's .LOC (StockLevels=%d Log=%d Period=%d ms RadioFallback=%d PlayedLog=%d PlayLog=%d Plain=%d PlainData=%d); needs [Wardrobe] DMVoice=1 / [Crew] Voice=1 so each body has its own voice number", kvo.stock, kvo.log, kvo.period, kvo.radiofb, kvo.played, kvo.playlog, kvo.plain, kvo.plaindata);
}

#endif /* KLVOICE_C */
