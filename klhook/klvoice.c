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
 *               PlayedLog=1 (with Log=2: 'voice: QUEUED <leaf> ...' / 'voice: entry USED? ...' when the game queues / seems to use an entry we swapped)
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

static struct { int on, stock, log, period, radiofb, played; } kvo;     /* radiofb/played: [Voice] RadioFallback / PlayedLog (2026-10-23 voiceheard) */
static struct {                                  /* the entries made for this level generation (never freed: the game may hold them) */
    DWORD rules, mgr, lm; char scene[160]; int n, toldfull;
    DWORD next_sum; int told_chg, told_q;         /* PlayedLog state: zeroed with the generation (review 1) */
    struct { DWORD hash; void *entry; int found; DWORD sum, lastq; char path[128]; char chg; } e[KVO_NENTRY];
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

/* a checksum of an entry's 0x204 bytes (PlayedLog: a change after the swap MAY mean the game used the entry - GUESS) */
static DWORD kvo_sum(const void *e)
{
    const DWORD *d = (const DWORD *)e; DWORD h = 2166136261u; int i;
    for (i = 0; i < 0x204 / 4; i++) h = (h ^ d[i]) * 16777619u;
    return h;
}

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
    snprintf(kvo_gen.e[kvo_gen.n].path, sizeof kvo_gen.e[0].path, "%s", key); kvo_gen.e[kvo_gen.n].sum = kvo_sum(e);
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

/* PlayedLog (voiceheard, 2026-10-23): proof that the game USES an entry we swapped in. Two signals, both read-only:
 *  (a) the speech queue [manager+0x974]: count at [queue] (0..10), records of 20 bytes from queue+4 = { priority, entry,
 *      speaker, float, last } (kltalk.c section 1: 0x578840 queues a line the channel cannot play at once). A record whose
 *      entry is one of OURS -> 'voice: QUEUED ...' (what the game is about to say, with the speaker's crew record).
 *  (b) GUESS: 0x7d0e80 plays an entry at once and the queue never shows it. If the game writes into the 0x204 entry block when
 *      it plays it (a played-at stamp, a handle), its checksum changes -> 'voice: entry USED? ...' (first change per entry,
 *      at most 40 lines). Nothing proves the game writes there; if (b) never fires, only (a) counts and a heard clip is by ear.
 * Runs every game-thread call (cheap: one 204-byte read when the queue is empty; 3 KB of checksums every 250 ms). Log=2 and PlayedLog=1. */
static void kvo_played(DWORD mgr, DWORD now)
{
    DWORD queue = klh_rd32(mgr + 0x974), cnt = 0, rec[5]; int i, k;
    if (!kvo.played || kvo.log < 2 || !kvo_gen.n) return;
    if (queue && klh_rd(queue, &cnt, 4) && cnt >= 1 && cnt <= 10) {
        for (k = 0; k < (int)cnt; k++) {
            if (!klh_rd(queue + 4 + (DWORD)k * 20, rec, 20)) break;
            for (i = 0; i < kvo_gen.n; i++)
                if (kvo_gen.e[i].found && (DWORD)(DWORD_PTR)kvo_gen.e[i].entry == rec[1]) {
                    if (now - kvo_gen.e[i].lastq > 1500 || !kvo_gen.e[i].lastq) {
                        klog("voice: QUEUED %s for crew record %lu (queue %lu, priority %ld): the game is about to say our entry", kvo_gen.e[i].path, rec[2], cnt, (long)rec[0]);
                        kvo_gen.told_q++;
                    }
                    kvo_gen.e[i].lastq = now ? now : 1;
                    break;
                }
        }
    }
    if (kvo_gen.next_sum && (long)(kvo_gen.next_sum - now) > 0) return;     /* wrap-safe: 0 = first call (GetTickCount is above 2^31 after 24.9 days) */
    kvo_gen.next_sum = (now + 250) ? (now + 250) : 1;
    for (i = 0; i < kvo_gen.n && kvo_gen.told_chg < 40; i++) {
        BYTE blk[0x204];
        if (!kvo_gen.e[i].found || kvo_gen.e[i].chg || !klh_rd((DWORD_PTR)kvo_gen.e[i].entry, blk, sizeof blk)) continue;
        if (kvo_sum(blk) != kvo_gen.e[i].sum) {
            kvo_gen.e[i].chg = 1; kvo_gen.told_chg++;
            klog("voice: entry USED? %s changed after the swap (GUESS: the game stamped it while playing it; %d queued so far)", kvo_gen.e[i].path, kvo_gen.told_q);
        }
    }
}

static void kvo_tick(int game_thread)
{
    struct klw_who w; char scene[160], key[64], why[200], who[8][32], path[128], text[130], leaf[64], names[8][16];
    int v, i, g, j, slot, nwant = 0; BYTE tab[8]; DWORD mgr, sig = 0, now;
    if (!kvo.on || !klh_exe_ok || !game_thread) return;
    now = GetTickCount();
    if (!klw_who_now(&w)) { if (kvo_nrec) kvo_restore_all("no Arcade round"); kvo_s.had = 0; return; }
    if (!klx_on || !klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    v = klx_level_verdict(scene, why);
    if (v == 1 && kvo.stock) v = 2;
    if (v != 2) { if (kvo_nrec) kvo_restore_all("not a Dead Men level"); return; }
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLK_MANAGER)))) return;
    { DWORD sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)), a = sys ? klh_rd32(sys + 0xac) : 0, lm = 0;
      if (a) klh_rd(a + 0x94, &lm, 4);
      /* generation = rules object, scene, speech manager and LOC lookup object: any change drops what we replaced (the lines are rebuilt) */
      if (kvo_gen.rules != w.rules || kvo_gen.mgr != mgr || kvo_gen.lm != lm || strcmp(kvo_gen.scene, scene)) {
          if (kvo_nrec) kvo_restore_all("a new level generation");
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
    if (sig == kvo_s.sig && now < kvo_s.next) return;
    kvo_s.sig = sig; kvo_s.next = now + (DWORD)kvo.period;

    kvo_s.walks++;
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
                if (!ln || !klh_rd(ln + 0x20, &flag, 1) || flag != 1 || !klh_rd(ln + 8, &vcnt, 4) || vcnt < 8 || vcnt > 16 || !klh_rd(ln + 0x14, &vdata, 4) || !vdata) continue;
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
    if (kvo.period < 200 || kvo.period > 60000) kvo.period = 1500;
    if (kvo.on) klog("voice: on; the Dead Men bodies' event lines come from KLVoice/<Name>/<Event> of the level's .LOC (StockLevels=%d Log=%d Period=%d ms RadioFallback=%d PlayedLog=%d); needs [Wardrobe] DMVoice=1 / [Crew] Voice=1 so each body has its own voice number", kvo.stock, kvo.log, kvo.period, kvo.radiofb, kvo.played);
}

#endif /* KLVOICE_C */
