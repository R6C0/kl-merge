/*
 * klclubdiag.c - TEST-ONLY read-only diagnostic: why does the DM05A (Last Call) club music not play? ([Probe] ClubMusic, default 0).
 * Part of KLHook, included by klhook.c inside #ifdef KLHOOK_TEST right after klprobe.c (uses klog, klh_rd, klh_rd32, klh_scene, klh_level_key,
 * klpr_name, KLH_VA). READS ONLY: no write, no detour, no call into the game. 2026-11-08.
 *
 * Question: the club's ZSNDOBJ layers sit behind SoundLimiterFade objects (class vtable 0xbaa60c). Does a limiter ever turn active, and what does
 * the engine think the listener's room is while the player stands on the dance floor?
 *
 * WHAT IS READ (kl2.exe 0x7e49c0, the limiter 'is active' method, disassembled 2026-11-08; PROVEN = read from those instructions):
 *   [L+0x30] PROVEN cache expiry (int, compared with the game ms [[0xdd2640]+0x48]; while ms < [L+0x30] the answer in [L+0x34] is returned as is)
 *   [L+0x34] PROVEN the cached answer (byte, 1 = active = the music behind it may play)
 *   [L+0x38] / [L+0x3c] PROVEN the two lists (on / off); a limiter with BOTH null answers 1 (empty lists = always active, 0x7e49f8)
 *   [L+0x58] PROVEN the listener's room object as the method last saw it: result of vtable slot 0x164 of A = [[0xdd2640]+0xb00] (0x7e4a11..0x7e4a26).
 *            Only written when a list is non-empty; 0 there makes the limiter inactive (0x7e4a29). [L+0x5c] = the previous value of it.
 *            The method turns the object into a pool handle with 0x6ece90 and compares it with the handles of the list's entries (0x7e4b59):
 *            this diagnostic cannot replicate that (calls), so it logs the room OBJECT pointer, not a handle.
 *   [L+0x50] / [L+0x52] / [L+0x53] PROVEN to be read there (a second cache: answer, flag, flag) - logged raw, meaning unknown.
 *   flag     [[[0xdd2640]+0xb00]+0x67b0] = rd32(rd32(gd + 0xb00) + 0x67b0), gd = [0xdd2640]: from the peer session (the sound start is skipped when != 0); NOT checked
 *            against code here, meaning GUESS.
 * GUESS: the limiter's name via klpr_name ([[L+4]+0x6c], else through [L+0x24]/[+0x60]): a limiter may keep none; '?' = unreadable. The room object's name the same way.
 * GUESS: the container pointers [L+0x38]/[L+0x3c] are logged with their first 4 dwords raw (layout unknown; the engine iterates through vtable +0x50 / +0x60).
 *
 * FINDING THE LIMITERS: no entity walk of this class exists in klhook, so one incremental scan of the private read-write heap (klbotfill.c's ramp-probe
 * pattern: 64 KB chunks, every 4th byte for the vtable) runs once per level, in budget slices (BUDGET_MB per tick, default 2) starting
 * 10 s after the level key appeared and the listener object [[0xdd2640]+0xb00] exists. A new scan starts when the key changes or the game clock goes backwards
 * (round 2 / reload). Objects are re-checked (vtable still 0xbaa60c) at every log; if all are gone a new scan starts.
 * Candidates are kept up to 32. A pointer to the vtable stored somewhere else than an object head would be a false hit (none expected).
 *
 * KEYS ([Probe]): ClubMusic=0 (1 = on)  ClubMusicMaps=f01\f01_main (level keys, ';' separated, lower case: the slot the DM05A graft sits in)
 *                 ClubMusicMs=2000 (log period 500..60000)  ClubMusicMaxLines=300
 * LOG (one line per period, 'clubdiag:'):
 *   clubdiag: t=<ms> map=<key> gms=<game ms> n=<limiters> A=<listener object> flag=<hex> | #i L=<addr> act=<[+0x34]> ex=<[+0x30]> on=<[+0x38]> off=<[+0x3c]>
 *             room=<[+0x58]>'name' prev=<[+0x5c]> c50=<hex of +0x50..+0x53> | ...
 *   plus 'clubdiag: scan ...' lines at scan start/end, and 'clubdiag: on-list L=... raw dwords' once per limiter after the scan.
 */
#define KLCM_VT        0x00baa60cu
#define KLCM_MAX       32
#define KLCM_BUDGET_MB 2

static struct {
    int on, maxlines, lines; DWORD period, budget;
    char maps[160];
    char key[64];                      /* level key of the current scan, "" = none */
    DWORD key_t, last_log, last_chk, last_gms;
    int state;                         /* 0 idle, 1 waiting for load, 2 scanning, 3 done */
    DWORD cur; DWORD scan_t0; DWORD scan_bytes;
    DWORD L[KLCM_MAX]; int n; BYTE raw_done[KLCM_MAX];
} klcm;

static void klcm_init(void)
{
    char tmp[160];
    klcm.on = GetPrivateProfileIntA("Probe", "ClubMusic", 0, klh_ini) != 0;
    if (!klcm.on) return;
    klcm.period = (DWORD)GetPrivateProfileIntA("Probe", "ClubMusicMs", 2000, klh_ini);
    if (klcm.period < 500) klcm.period = 500; if (klcm.period > 60000) klcm.period = 60000;
    klcm.maxlines = GetPrivateProfileIntA("Probe", "ClubMusicMaxLines", 300, klh_ini);
    klcm.budget = (DWORD)GetPrivateProfileIntA("Probe", "ClubMusicBudgetMB", KLCM_BUDGET_MB, klh_ini);
    if (klcm.budget < 1) klcm.budget = 1; if (klcm.budget > 32) klcm.budget = 32;
    GetPrivateProfileStringA("Probe", "ClubMusicMaps", "f01\\f01_main", tmp, sizeof tmp, klh_ini);
    { int i; for (i = 0; tmp[i] && i < (int)sizeof klcm.maps - 1; i++) klcm.maps[i] = (char)(tmp[i] >= 'A' && tmp[i] <= 'Z' ? tmp[i] + 32 : tmp[i] == '/' ? 0x5c : tmp[i]); klcm.maps[i] = 0; }
    if (!klh_exe_ok) { klog("clubdiag: not the known kl2.exe - off"); klcm.on = 0; return; }
    klog("clubdiag: ClubMusic on (read only): maps '%s', every %lu ms, max %d lines, scan budget %lu MB per tick", klcm.maps, (unsigned long)klcm.period, klcm.maxlines, (unsigned long)klcm.budget);
}

/* is the level key one of the ';' separated entries of the list */
static int klcm_map_listed(const char *key)
{
    const char *p = klcm.maps; size_t kl = strlen(key);
    while (*p) {
        const char *e = strchr(p, ';'); size_t l = e ? (size_t)(e - p) : strlen(p);
        if (l == kl && !memcmp(p, key, l)) return 1;
        if (!e) break;
        p = e + 1;
    }
    return 0;
}

static DWORD klcm_gd_ms(DWORD *aout, DWORD *flagout)
{   /* game ms [[0xdd2640]+0x48] (0 = unreadable); *aout = [[0xdd2640]+0xb00]; *flagout = [A+0x67b0] */
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)), a = 0, f = 0, ms = 0;
    if (gd) { ms = klh_rd32(gd + 0x48); a = klh_rd32(gd + 0xb00); if (a) f = klh_rd32(a + 0x67b0); }
    if (aout) *aout = a; if (flagout) *flagout = f;
    return ms;
}

static void klcm_name(DWORD obj, char *out, int cap)
{
    char b[64];
    out[0] = 0;
    if (obj && klpr_name(obj, b, sizeof b)) { int i; for (i = 0; b[i] && i < cap - 1; i++) out[i] = b[i]; out[i] = 0; }
    if (!out[0]) strcpy(out, "?");
}

/* one budgeted slice of the heap scan; returns 1 when the whole address range is done */
static int klcm_scan_slice(void)
{
    static BYTE buf[0x10000]; MEMORY_BASIC_INFORMATION mbi; DWORD done = 0, limit = klcm.budget * 1048576u;
    BYTE *a = (BYTE *)(DWORD_PTR)(klcm.cur ? klcm.cur : 0x10000);
    while ((DWORD_PTR)a < 0x7ffe0000 && done < limit && VirtualQuery(a, &mbi, sizeof mbi)) {
        BYTE *end = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            BYTE *p = a;
            while (p < end && done < limit) {      /* resume inside a region: 'a' is the cursor, aligned to the chunk size */
                SIZE_T n = (SIZE_T)(end - p) < sizeof buf ? (SIZE_T)(end - p) : sizeof buf, k;
                if (klh_rd((DWORD_PTR)p, buf, n)) {
                    for (k = 0; k + 4 <= n; k += 4)
                        if (*(DWORD *)(buf + k) == (DWORD)(DWORD_PTR)KLH_VA(KLCM_VT) && klcm.n < KLCM_MAX) {
                            int j, dup = 0; DWORD at = (DWORD)((DWORD_PTR)p + k);
                            for (j = 0; j < klcm.n; j++) if (klcm.L[j] == at) dup = 1;
                            if (!dup) { klcm.raw_done[klcm.n] = 0; klcm.L[klcm.n++] = at; }
                        }
                }
                p += n; done += (DWORD)n; klcm.scan_bytes += (DWORD)n;
            }
            if (p < end) { klcm.cur = (DWORD)(DWORD_PTR)p; return 0; }
        }
        a = end;
        klcm.cur = (DWORD)(DWORD_PTR)a;
    }
    return !((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi));
}

static void klcm_reset(void)
{
    klcm.state = 0; klcm.n = 0; klcm.cur = 0; klcm.scan_bytes = 0; klcm.key[0] = 0;
}

/* called every game-thread tick by klhook.c (KLPT); one compare when ClubMusic is off */
static void klcm_tick(void)
{
    char scene[200], key[64]; DWORD now, A = 0, flag = 0, gms;
    if (!klcm.on) return;
    now = GetTickCount();
    if (klcm.state == 2) {                                   /* scanning: keep going every tick until done */
        if (klcm_scan_slice()) {
            klcm.state = 3;
            klog("clubdiag: scan done: %d limiter object(s) (vtable %08lx) in %lu ms, %lu MB of private heap", klcm.n, (unsigned long)KLCM_VT, (unsigned long)(GetTickCount() - klcm.scan_t0), (unsigned long)(klcm.scan_bytes >> 20));
            klcm.last_log = 0;
        }
        return;
    }
    if (now - klcm.last_chk < 500) return;
    klcm.last_chk = now;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key) || !klcm_map_listed(key)) {
        if (klcm.key[0]) { klog("clubdiag: left the level (scene '%s'): reset", scene); klcm_reset(); }
        return;
    }
    gms = klcm_gd_ms(&A, &flag);
    if (strcmp(key, klcm.key)) { klcm_reset(); strcpy(klcm.key, key); klcm.key_t = now; klcm.state = 1; klcm.last_gms = gms; klog("clubdiag: level '%s' seen; scan starts 10 s after the listener object exists", key); return; }
    if (gms && gms + 1000 < klcm.last_gms && klcm.state == 3) { klog("clubdiag: game clock went back (%lu -> %lu): rescan", (unsigned long)klcm.last_gms, (unsigned long)gms); klcm.state = 1; klcm.n = 0; klcm.cur = 0; klcm.key_t = now; }
    if (gms) klcm.last_gms = gms;
    if (klcm.state == 1) {
        if (A && now - klcm.key_t >= 10000) { klcm.state = 2; klcm.scan_t0 = now; klcm.scan_bytes = 0; klcm.cur = 0; klcm.n = 0; klog("clubdiag: scan start (listener object A=%08lx, game ms %lu)", (unsigned long)A, (unsigned long)gms); }
        return;
    }
    if (klcm.state != 3 || now - klcm.last_log < klcm.period || klcm.lines >= klcm.maxlines) return;
    klcm.last_log = now;
    {   /* the log line: header + one compact entry per live limiter */
        char line[1400], nm[28], rn[28]; int i, len, live = 0, o;
        len = snprintf(line, sizeof line, "clubdiag: t=%lu map=%s gms=%lu A=%08lx flag=%lx |", (unsigned long)now, key, (unsigned long)gms, (unsigned long)A, (unsigned long)flag);
        for (i = 0; i < klcm.n && len < (int)sizeof line - 200; i++) {
            DWORD L = klcm.L[i], vt = klh_rd32(L), ex, on, off, room, prev; BYTE c[4] = {0, 0, 0, 0}, act = 0xff;
            if (vt != (DWORD)(DWORD_PTR)KLH_VA(KLCM_VT)) continue;       /* freed / reused */
            live++;
            ex = klh_rd32(L + 0x30); on = klh_rd32(L + 0x38); off = klh_rd32(L + 0x3c); room = klh_rd32(L + 0x58); prev = klh_rd32(L + 0x5c);
            klh_rd(L + 0x34, &act, 1); klh_rd(L + 0x50, c, 4);
            klcm_name(L, nm, sizeof nm); klcm_name(room, rn, sizeof rn);
            len += snprintf(line + len, sizeof line - len, " #%d L=%08lx '%s' act=%u ex=%lu on=%08lx off=%08lx room=%08lx'%s' prev=%08lx c50=%02x%02x%02x%02x |",
                            i, (unsigned long)L, nm, (unsigned)act, (unsigned long)ex, (unsigned long)on, (unsigned long)off, (unsigned long)room, rn, (unsigned long)prev, c[0], c[1], c[2], c[3]);
            if (len < 0) { len = (int)sizeof line - 1; break; }
            if (!klcm.raw_done[i] && (on || off)) {                       /* once: the first 4 dwords of each list container, raw (layout GUESS) */
                DWORD d[8] = {0}; klcm.raw_done[i] = 1;
                for (o = 0; o < 4; o++) { d[o] = klh_rd32(on + 4 * o); d[4 + o] = klh_rd32(off + 4 * o); }
                klog("clubdiag: lists of L=%08lx (layout GUESS): on %08lx [%08lx %08lx %08lx %08lx] off %08lx [%08lx %08lx %08lx %08lx]", (unsigned long)L,
                     (unsigned long)on, (unsigned long)d[0], (unsigned long)d[1], (unsigned long)d[2], (unsigned long)d[3], (unsigned long)off, (unsigned long)d[4], (unsigned long)d[5], (unsigned long)d[6], (unsigned long)d[7]);
            }
        }
        line[sizeof line - 1] = 0;
        klog("%s", line); klcm.lines++;
        if (!live && klcm.n) { klog("clubdiag: every limiter object is gone: rescan"); klcm.state = 1; klcm.n = 0; klcm.cur = 0; klcm.key_t = now - 9000; }
    }
}
