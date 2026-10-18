/*
 * klbuild.c - BUILD-MISMATCH CHECK between lobby members (design: re\private_match_buildcheck.md, sections 1-10; section 11
 * is this file). NOT in any build yet and NOT RUN in the game. Include-style module like klmm.c / klslot.c: everything is
 * static, one translation unit with klhook.c.
 *
 * ---------------------------------------------------------------------------------------------------------------------
 * WHAT 3f ADDS TO klhook.c (two lines; nothing else, no build.bat change, the module needs no init call of its own):
 *
 *   1. in the include block, directly AFTER   #include "klslot.c"   (klhook.c ~line 660; it needs klsteam.c, klmm.c and
 *      klslot.c above it):                    #include "klbuild.c"          /+ klbuild.c: [Build] Check - lobby build check (off unless Check=1) +/
 *   2. in klh_tick(), directly AFTER          kls_tick();                    (klhook.c ~line 750):
 *                                             klbld_tick(game_thread);       /+ klbuild.c: returns at once unless [Build] Check=1 +/
 *      (write the comment delimiters as star-slash; shown with + here because a nested comment would end this one)
 *
 *   klbld_init() is called by the first klbld_tick on the game's thread (so there is no DllMain line); a caller that wants
 *   it earlier may call klbld_init() after kls_init(inst) - it is idempotent. Both names are declared right below.
 *   Why no DllMain line: the Steam interface is fetched from the import slot on EVERY call by the game (all 25 sites,
 *   re\private_match_buildcheck.md 2), so wrapping it at the first main-loop frame misses nothing.
 * ---------------------------------------------------------------------------------------------------------------------
 *
 * DEFAULT OFF. [Build] Check=0 (or absent): klbld_init() reads ONE ini value, sets the module off, and from then on
 * klbld_tick() is "if (klbld_mode <= 0) return" - no patch, no hook, no memory write, no thread, no log line.
 * Keys (KLHook.ini):
 *   [Build]
 *   Check=0          1 = switch the check on (any other value = off; non-zero values other than 1 are logged once)
 *   Hold=1           1 = hold the FA start gate while a slot differs (mask bit, see HOLD); 0 = log only
 *   Full=1           1 = a low-priority worker thread computes the FULL build code (the same code tools/kl_buildprint.py prints)
 *                    once, when the first lobby is seen; 0 = only the cheap per-slot member-list prints are used
 *   NoKeyBlocks=0    1 = a joiner treats a host WITHOUT our keys as "stock" (the slots the joiner has a redirect for then
 *                    mismatch and are held); 0 = warn only (buildcheck 7.3: lobby data may simply not have arrived)
 *
 * WHAT IT DOES (buildcheck sections 4-6, with the section 10 corrections)
 *  - One wrapper on the import slot steam_api.SteamMatchmaking (0xb107d8, outside CEG-hashed pages, buildcheck 5), chained on
 *    top of whatever is there (klmm.c's proxy or the real accessor). It is its own 36-slot ISteamMatchmaking008 table with
 *    33 naked tail jumps and three overrides: 14 LeaveLobby, 19 SetLobbyData, 34 GetLobbyOwner. Version/shape checks reuse
 *    klmm.c's klmm_has_008() and the same 36-code-pointer test.
 *  - HOST: SetLobbyData key "name" (the game's 0x869430 first call, buildcheck 2) marks "this lobby is mine". The tick then
 *    publishes lobby data   klx=1   klx_slots=<fp>   klx_code=<full code, when the worker is done>   and its own member
 *    data klx_fp=<fp>. <fp> is  "P=<8 hex of Patch01.zip's member-CRC print>;F01=<8 hex>;...;F09=<8 hex>"  where each
 *    FUUU token is the first 8 hex of the member-CRC print of the Fxx_Main.zip that the ACTIVE redirect rule resolves to
 *    (section 10: [Redirect.N] page latched by klslot.c, falling back to [Redirect], exactly kls_map's rule), or "-" for a
 *    slot without a rule (stock). ~2 Hz it walks the members (GetNumLobbyMembers, GetLobbyMemberByIndex,
 *    GetLobbyMemberData "klx_fp") and compares. A member with no klx_fp counts as a stock client (all "-") after 3 s.
 *  - JOINER: GetLobbyOwner called from kl2.exe 0x6299da (the LobbyEnter completion, buildcheck 10) records the lobby id.
 *    The tick publishes this machine's klx_fp as member data, reads klx / klx_slots from the lobby (RequestLobbyData up to 8
 *    times, 2 s apart, if empty) and compares.
 *  - A mismatch is per SLOT: bit n-1 for Fn. A slot differs if the two prints differ or one side has a rule and the other
 *    has "-". If Patch01's print differs, every slot with a rule on either side differs.
 *  - The full code (kl_buildprint.py's BUILD CODE) is published and logged for diagnosis only; it never holds anything
 *    (it contains the hook dll and presentation-free ini sections, which may differ harmlessly).
 *
 * HOLD (buildcheck 6 with the 10 correction; 3f's conditions: only the mask, nothing else)
 *  For the slots in the mismatch set the module clears those bits in THIS machine's client mask: desired = (0x634b90(mgr) & ~bits),
 *  pushed with kl2.exe 0x845640(client + 0xb8, desired). Because only the bits of slots that actually differ are cleared
 *  and a stock slot is "-" on both sides, stock Subway is not blocked (the section 10 objection to the first draft). It is
 *  re-pushed every game-thread tick while held (kl2 0x845700 re-pushes the true mask on DLC events) and the true mask is
 *  put back once when the set becomes empty, the lobby is left, or the module is off. Game-thread ticks only.
 *
 * HASH PARITY WITH tools/kl_buildprint.py (the user's question)
 *  IDENTICAL by construction, because this file re-implements the tool's algorithm: BLAKE2b-128 (klbld_b2), zip print =
 *  hash of "name|%08x|%d\n" (member name with backslashes turned into '/', CRC-32, uncompressed size) over the central
 *  directory sorted by (name, crc, size), map hard hash over the sorted non-backup files of a map folder (zips by member
 *  print, klwardrobe.ini/klguns.ini by normalised text, .whd/.wav/.snd/.hti by full bytes, loading-screen language files
 *  skipped), global parts dll / ini (DROP_SECTIONS removed) / Patch01 / redirect table, then the code = first 8 hex of
 *  BLAKE2b-128 over "dll=..\nini=..\npatch01=..\nredirect=..\n" plus "<folder>=<hard>\n" per ACTIVE map in code-point order.
 *  The two programs agree when (a) member names are ASCII (a non-ASCII name that is not UTF-8-flagged is decoded as cp437 by
 *  Python; this file does not: it counts such names and logs "GUESS" so a difference is explained), (b) the zip is not zip64
 *  (this file then falls back to a whole-file hash and says so; the tool's fallback label differs but its digest is the same
 *  whole-file hash only if Python also failed to parse, which it would not - GUESS: no level zip is zip64), (c) .ini text is
 *  ASCII in section and key names (Python lower-cases Latin-1 letters, this file only A-Z). Strict mode (--strict, soft
 *  hashes of KLJoin.ini / KLTalk.ini) is NOT implemented. VERIFY: tools/kl_buildprint.py vs the "build: code" line (see section 11 of
 *  the doc for the measured result of the out-of-tree harness).
 *
 * LOG (KLHook.log, prefix "build:", at most 150 lines per process; no Steam id of anyone and no lobby id is ever written)
 *   build: Check=1: wrapper on steam_api.SteamMatchmaking installed (36 slots, 3 overrides) Hold=1 Full=1
 *   build: lobby seen (host): fp P=ab12cd34;F01=1a2b3c4d;F02=-;...
 *   build: code 6755CC0C dll .. ini .. patch01 .. redirect .. (N active map(s), 1.1 s, 2 non-ascii name(s))
 *   build: member#1 differs in F01 (mine 1a2b3c4d theirs -): HOLD slot F01
 *   build: no difference: hold released
 */
#ifndef KLBUILD_C
#define KLBUILD_C

#define KLBLD_RA_ENTER   0x006299dau   /* kl2.exe: return address of the call [vtbl+0x88] GetLobbyOwner in the LobbyEnter handler 0x629980 - FACT: disassembled 2026-10-18 (call edx at 0x6299d8), buildcheck 10 */
#define KLBLD_MASKGET    0x00634b90u   /* DWORD __thiscall (mgr): bit i = byte [mgr+4+i], i < 9 - FACT: disassembled, private_match.md 3. Real code reads bytes +4..+0xc; returns 16-bit mask in eax */
#define KLBLD_MASKSET    0x00845640u   /* char __thiscall (client+0xb8, mask) ret 4: stores mask^0xdead at +4 - FACT: disassembled 2026-10-18 */
#define KLBLD_CLIENT_OFF 0x98u         /* [session + 0x98] = the local client object - FACT: 0x845813..0x845835 (mov edi,[eax+0x98]; lea ecx,[edi+0xb8]; call 0x845640) */
#define KLBLD_NSLOT      36
#define KLBLD_LOGMAX     150
#define KLBLD_MEM        16            /* members tracked (the game's limit is 12 clients per gate loop, 0x6c4d89) */
#define KLBLD_GRACE_MS   3000          /* a member without klx_fp is a stock client only after this long (GUESS: 3 s is enough for their first tick) */
#define KLBLD_POLL_MS    500           /* GetLobbyMember* polling (buildcheck 5.4: ~2 Hz) */

static void klbld_init(void);
static void klbld_tick(int game_thread);

/* ---------------------------------------------------------------- state */

static int klbld_mode;                 /* 0 = not read yet, -1 = off, 1 = on */
static int klbld_hold_on = 1, klbld_full_on = 1, klbld_nokeyblocks;
static volatile LONG klbld_nlog;
static void *(__cdecl *klbld_prev_accessor)(void);
static void **klbld_real;              /* the interface below our proxy (klmm's proxy or the real one) */
static void *klbld_vt[KLBLD_NSLOT];
static struct { void **vt; } klbld_proxy = { klbld_vt };

static unsigned __int64 klbld_lobby, klbld_host_lobby;     /* the lobby the game is in / the one this machine created. 0 = none */
static volatile LONG klbld_lobby_new;                      /* a lobby id was recorded by an override: the tick resets its per-lobby state */
static char klbld_pub_fp[256], klbld_pub_code[16];         /* what was last written (host) */
static DWORD klbld_poll_at, klbld_hold_bits, klbld_want_bits;
static int klbld_joiner_tries, klbld_joiner_got, klbld_joiner_told;
static DWORD klbld_joiner_next;
static char klbld_host_fp[256], klbld_host_code[16]; static int klbld_host_hooked;
static char klbld_my_member[256];
static struct { unsigned __int64 id; DWORD first, mask; int used; } klbld_mem[KLBLD_MEM];

static void klbld_say(const char *fmt, ...)
{
    char b[400]; va_list ap;
    if (InterlockedIncrement(&klbld_nlog) > KLBLD_LOGMAX) return;
    va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    klog("build: %s", b);
}

/* ---------------------------------------------------------------- BLAKE2b (RFC 7693), unkeyed, any output length <= 64 */

typedef struct { unsigned __int64 h[8], t; BYTE buf[128]; DWORD n, outlen; } klbld_b2;

static const unsigned __int64 klbld_iv[8] = {
    0x6a09e667f3bcc908ui64, 0xbb67ae8584caa73bui64, 0x3c6ef372fe94f82bui64, 0xa54ff53a5f1d36f1ui64,
    0x510e527fade682d1ui64, 0x9b05688c2b3e6c1fui64, 0x1f83d9abfb41bd6bui64, 0x5be0cd19137e2179ui64 };
static const BYTE klbld_sigma[12][16] = {
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 }, { 14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3 },
    { 11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4 }, { 7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8 },
    { 9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13 }, { 2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9 },
    { 12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11 }, { 13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10 },
    { 6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5 }, { 10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0 },
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 }, { 14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3 } };

#define KLBLD_ROR(x, n) (((x) >> (n)) | ((x) << (64 - (n))))
#define KLBLD_G(a, b, c, d, x, y) do { a = a + b + (x); d = KLBLD_ROR(d ^ a, 32); c = c + d; b = KLBLD_ROR(b ^ c, 24); \
                                       a = a + b + (y); d = KLBLD_ROR(d ^ a, 16); c = c + d; b = KLBLD_ROR(b ^ c, 63); } while (0)

static void klbld_b2_block(klbld_b2 *s, const BYTE *blk, int last)
{
    unsigned __int64 m[16], v[16]; int i, r;
    for (i = 0; i < 16; i++) { const BYTE *p = blk + 8 * i; m[i] = (unsigned __int64)p[0] | (unsigned __int64)p[1] << 8 | (unsigned __int64)p[2] << 16 | (unsigned __int64)p[3] << 24 |
                                                          (unsigned __int64)p[4] << 32 | (unsigned __int64)p[5] << 40 | (unsigned __int64)p[6] << 48 | (unsigned __int64)p[7] << 56; }
    for (i = 0; i < 8; i++) { v[i] = s->h[i]; v[i + 8] = klbld_iv[i]; }
    v[12] ^= s->t;                                         /* t0; t1 = 0 (inputs < 2^64 bytes) */
    if (last) v[14] = ~v[14];
    for (r = 0; r < 12; r++) {
        const BYTE *z = klbld_sigma[r];
        KLBLD_G(v[0], v[4], v[8],  v[12], m[z[0]],  m[z[1]]);  KLBLD_G(v[1], v[5], v[9],  v[13], m[z[2]],  m[z[3]]);
        KLBLD_G(v[2], v[6], v[10], v[14], m[z[4]],  m[z[5]]);  KLBLD_G(v[3], v[7], v[11], v[15], m[z[6]],  m[z[7]]);
        KLBLD_G(v[0], v[5], v[10], v[15], m[z[8]],  m[z[9]]);  KLBLD_G(v[1], v[6], v[11], v[12], m[z[10]], m[z[11]]);
        KLBLD_G(v[2], v[7], v[8],  v[13], m[z[12]], m[z[13]]); KLBLD_G(v[3], v[4], v[9],  v[14], m[z[14]], m[z[15]]);
    }
    for (i = 0; i < 8; i++) s->h[i] ^= v[i] ^ v[i + 8];
}

static void klbld_b2_init(klbld_b2 *s, DWORD outlen)
{
    int i;
    memset(s, 0, sizeof *s);
    for (i = 0; i < 8; i++) s->h[i] = klbld_iv[i];
    s->h[0] ^= 0x01010000ui64 ^ outlen;                    /* digest length, key length 0, fanout 1, depth 1 */
    s->outlen = outlen;
}

static void klbld_b2_upd(klbld_b2 *s, const void *data, size_t n)
{
    const BYTE *p = (const BYTE *)data;
    while (n) {
        if (s->n == 128) { s->t += 128; klbld_b2_block(s, s->buf, 0); s->n = 0; }      /* a full buffer is compressed only when more data follows */
        { size_t k = 128 - s->n; if (k > n) k = n; memcpy(s->buf + s->n, p, k); s->n += (DWORD)k; p += k; n -= k; }
    }
}

static void klbld_b2_str(klbld_b2 *s, const char *z) { klbld_b2_upd(s, z, strlen(z)); }

static void klbld_b2_hex(klbld_b2 *s, char *out)       /* outlen*2 lower-case hex + NUL */
{
    static const char hx[] = "0123456789abcdef"; DWORD i;
    s->t += s->n; memset(s->buf + s->n, 0, 128 - s->n);
    klbld_b2_block(s, s->buf, 1);
    for (i = 0; i < s->outlen; i++) { BYTE b = (BYTE)(s->h[i >> 3] >> (8 * (i & 7))); out[2 * i] = hx[b >> 4]; out[2 * i + 1] = hx[b & 15]; }
    out[2 * s->outlen] = 0;
}

/* ---------------------------------------------------------------- files: whole-file hash and zip print (tools/kl_buildprint.py file_hash / zip_print) */

static int klbld_file_hash(const char *path, char hex[33])
{   /* blake2b-128 of the bytes. -> 1 ok */
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 0, OPEN_EXISTING, FILE_FLAG_SEQUENTIAL_SCAN, 0);
    BYTE *buf; DWORD got; klbld_b2 s;
    if (f == INVALID_HANDLE_VALUE) return 0;
    buf = (BYTE *)HeapAlloc(GetProcessHeap(), 0, 1u << 20);
    if (!buf) { CloseHandle(f); return 0; }
    klbld_b2_init(&s, 16);
    while (ReadFile(f, buf, 1u << 20, &got, 0) && got) klbld_b2_upd(&s, buf, got);
    klbld_b2_hex(&s, hex);
    HeapFree(GetProcessHeap(), 0, buf); CloseHandle(f);
    return 1;
}

typedef struct { const BYTE *n; DWORD nl, crc, size; } klbld_zent;

static int klbld_zcmp(const void *pa, const void *pb)
{
    const klbld_zent *a = (const klbld_zent *)pa, *b = (const klbld_zent *)pb; DWORD l = a->nl < b->nl ? a->nl : b->nl; int c = memcmp(a->n, b->n, l);
    if (c) return c;
    if (a->nl != b->nl) return a->nl < b->nl ? -1 : 1;
    if (a->crc != b->crc) return a->crc < b->crc ? -1 : 1;
    return a->size < b->size ? -1 : a->size > b->size;
}

static volatile LONG klbld_nonascii;                   /* member names not pure ASCII seen (hash parity GUESS, header comment) */

/* hash of "name|%08x|%d\n" over the central directory sorted by (name, crc, size); out = 32 hex, "-empty" appended when there is no
   member. Exactly kl_buildprint.zip_print. -> 1; 0 when the zip cannot be read or is zip64 (the caller then uses the whole file) */
static int klbld_zip_print(const char *path, char out[40])
{
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 0, OPEN_EXISTING, 0, 0);
    BYTE *tail = 0, *cd = 0; klbld_zent *e = 0; DWORD hi = 0, lo, n, got, cdsize, cdoff, o, cnt = 0, i; int k, ok = 0; klbld_b2 s; char line[400];
    if (f == INVALID_HANDLE_VALUE) return 0;
    lo = GetFileSize(f, &hi);
    if (hi || lo < 22) goto out;
    n = lo < 66000 ? lo : 66000;                       /* the end record is within 64 KB + 22 of the end (zip comment) */
    tail = (BYTE *)HeapAlloc(GetProcessHeap(), 0, n);
    if (!tail || SetFilePointer(f, (LONG)(lo - n), 0, FILE_BEGIN) == INVALID_SET_FILE_POINTER || !ReadFile(f, tail, n, &got, 0) || got != n) goto out;
    for (k = (int)n - 22; k >= 0 && memcmp(tail + k, "PK\5\6", 4); k--) ;
    if (k < 0) goto out;
    cdsize = *(DWORD *)(tail + k + 12); cdoff = *(DWORD *)(tail + k + 16);
    if (cdsize == 0xffffffffu || cdoff == 0xffffffffu || *(WORD *)(tail + k + 10) == 0xffff) goto out;       /* zip64 */
    if (cdoff > lo || cdsize > lo - cdoff || cdsize > (64u << 20)) goto out;
    if (cdsize) {
        cd = (BYTE *)HeapAlloc(GetProcessHeap(), 0, cdsize);
        if (!cd || SetFilePointer(f, (LONG)cdoff, 0, FILE_BEGIN) == INVALID_SET_FILE_POINTER || !ReadFile(f, cd, cdsize, &got, 0) || got != cdsize) goto out;
    }
    for (o = 0; o + 46 <= cdsize && !memcmp(cd + o, "PK\1\2", 4); ) {        /* count */
        DWORD nl = *(WORD *)(cd + o + 28), el = *(WORD *)(cd + o + 30), cl = *(WORD *)(cd + o + 32);
        if (o + 46 + nl + el + cl > cdsize) break;
        cnt++; o += 46 + nl + el + cl;
    }
    if (cnt) {
        e = (klbld_zent *)HeapAlloc(GetProcessHeap(), 0, sizeof(klbld_zent) * cnt);
        if (!e) goto out;
        for (o = 0, i = 0; i < cnt; i++) {
            DWORD nl = *(WORD *)(cd + o + 28), el = *(WORD *)(cd + o + 30), cl = *(WORD *)(cd + o + 32), j; BYTE *nm = cd + o + 46;
            for (j = 0; j < nl; j++) { if (nm[j] == '\\') nm[j] = '/'; else if (nm[j] >= 0x80) { InterlockedIncrement(&klbld_nonascii); } }      /* ZipInfo turns os.sep into '/' (Windows) */
            e[i].n = nm; e[i].nl = nl; e[i].crc = *(DWORD *)(cd + o + 16); e[i].size = *(DWORD *)(cd + o + 24);
            o += 46 + nl + el + cl;
        }
        qsort(e, cnt, sizeof *e, klbld_zcmp);
    }
    klbld_b2_init(&s, 16);
    for (i = 0; i < cnt; i++) {
        int m = _snprintf(line, 40, "|%08lx|%lu\n", (unsigned long)e[i].crc, (unsigned long)e[i].size);
        klbld_b2_upd(&s, e[i].n, e[i].nl); klbld_b2_upd(&s, line, (size_t)(m > 0 ? m : 0));
    }
    klbld_b2_hex(&s, out);
    if (!cnt) strcat(out, "-empty");
    ok = 1;
out:
    if (e) HeapFree(GetProcessHeap(), 0, e);
    if (cd) HeapFree(GetProcessHeap(), 0, cd);
    if (tail) HeapFree(GetProcessHeap(), 0, tail);
    CloseHandle(f);
    return ok;
}

/* ---------------------------------------------------------------- ini: kl_buildprint.norm_ini_text / ini_hash / redirects */

typedef struct { char name[64]; } klbld_sec;
typedef struct { int sec; char *text; } klbld_line;
typedef struct { klbld_sec sec[256]; int nsec; klbld_line *ln; int nln; char *buf; } klbld_ini;

static int klbld_ws(BYTE c) { return (c >= 9 && c <= 13) || (c >= 0x1c && c <= 0x20) || c == 0x85 || c == 0xa0; }     /* Python str.strip() on a Latin-1 string */
static int klbld_nl(BYTE c) { return c == '\n' || c == '\r' || c == 0x0b || c == 0x0c || c == 0x1c || c == 0x1d || c == 0x1e || c == 0x85; }    /* str.splitlines() */
static char *klbld_trim(char *s)
{
    char *e; while (*s && klbld_ws((BYTE)*s)) s++;
    e = s + strlen(s); while (e > s && klbld_ws((BYTE)e[-1])) *--e = 0;
    return s;
}
static void klbld_lower(char *s) { for (; *s; s++) if (*s >= 'A' && *s <= 'Z') *s += 32; }

static void klbld_ini_free(klbld_ini *t)
{
    if (t->ln) HeapFree(GetProcessHeap(), 0, t->ln);
    if (t->buf) HeapFree(GetProcessHeap(), 0, t->buf);
    memset(t, 0, sizeof *t);
}

static int klbld_ini_read(const char *path, klbld_ini *t)
{   /* -> 1 ok; sections in first-seen order, lines in file order. Comments / blanks dropped, keys lower-cased, ';' tails cut */
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 0, OPEN_EXISTING, 0, 0);
    DWORD sz, got, i; char *p, *q, *end; int cur = -1, maxl = 2;
    memset(t, 0, sizeof *t);
    if (f == INVALID_HANDLE_VALUE) return 0;
    sz = GetFileSize(f, 0);
    if (sz == INVALID_FILE_SIZE || sz > (8u << 20) || !(t->buf = (char *)HeapAlloc(GetProcessHeap(), 0, (SIZE_T)sz + 2)) ||
        (sz && (!ReadFile(f, t->buf, sz, &got, 0) || got != sz))) { CloseHandle(f); klbld_ini_free(t); return 0; }
    CloseHandle(f);
    t->buf[sz] = 0;
    p = t->buf;
    if (sz >= 3 && (BYTE)p[0] == 0xef && (BYTE)p[1] == 0xbb && (BYTE)p[2] == 0xbf) p += 3;      /* BOM, as the tool */
    end = t->buf + sz;
    for (q = p; q < end; q++) if (klbld_nl((BYTE)*q)) maxl++;
    t->ln = (klbld_line *)HeapAlloc(GetProcessHeap(), 0, sizeof(klbld_line) * (size_t)maxl);
    if (!t->ln) { klbld_ini_free(t); return 0; }
    cur = -1;
    while (p < end) {
        char *ls = p, *s, *eq;
        while (p < end && !klbld_nl((BYTE)*p)) p++;
        if (p < end) { if (p[0] == '\r' && p + 1 < end && p[1] == '\n') { *p++ = 0; *p++ = 0; } else *p++ = 0; }       /* \r\n is one break */
        s = klbld_trim(ls);
        if (!*s || *s == ';' || *s == '#') continue;
        if (*s == '[') {
            char *a = s, *b = s + strlen(s);
            while (*a == '[' || *a == ']') a++;                 /* strip("[]") */
            while (b > a && (b[-1] == '[' || b[-1] == ']')) *--b = 0;
            a = klbld_trim(a); klbld_lower(a);
            for (i = 0; (int)i < t->nsec && strcmp(t->sec[i].name, a); i++) ;
            if ((int)i == t->nsec) { if (t->nsec >= 256) { cur = -2; continue; } strncpy(t->sec[t->nsec].name, a, 63); t->sec[t->nsec].name[63] = 0; t->nsec++; }
            cur = (int)i;
            continue;
        }
        if (cur == -2) continue;                                /* more than 256 sections: the rest is not hashed (GUESS: never reached) */
        if (cur == -1) {                                        /* lines before any section belong to the section named "" */
            for (i = 0; (int)i < t->nsec && t->sec[i].name[0]; i++) ;
            if ((int)i == t->nsec) { t->sec[t->nsec].name[0] = 0; t->nsec++; }
            cur = (int)i;
        }
        if ((eq = strchr(s, '=')) != 0) {
            char *k = s, *v = eq + 1, *sc, *kt; *eq = 0;
            sc = strchr(v, ';'); if (sc) *sc = 0;
            k = klbld_trim(k); klbld_lower(k); kt = klbld_trim(v);
            { size_t kl = strlen(k), vl = strlen(kt); memmove(ls, k, kl); ls[kl] = '='; memmove(ls + kl + 1, kt, vl); ls[kl + 1 + vl] = 0; s = ls; }
        }
        t->ln[t->nln].sec = cur; t->ln[t->nln].text = s; t->nln++;
    }
    return 1;
}

static int klbld_secord(const void *a, const void *b) { return 0; }

static void klbld_emit(klbld_b2 *s, const char *z)
{   /* the tool hashes str.encode() = UTF-8 of the Latin-1 text: bytes >= 0x80 become two bytes */
    BYTE tmp[256]; int n = 0;
    for (; *z; z++) {
        BYTE c = (BYTE)*z;
        if (n > 250) { klbld_b2_upd(s, tmp, (size_t)n); n = 0; }
        if (c < 0x80) tmp[n++] = c; else { tmp[n++] = (BYTE)(0xc0 | (c >> 6)); tmp[n++] = (BYTE)(0x80 | (c & 0x3f)); }
    }
    if (n) klbld_b2_upd(s, tmp, (size_t)n);
}

static int klbld_dropped(const char *name, int use_drop)
{
    static const char *const drop[] = { "graphics", "hud", "reshade", "camera", "censor", "shoulder", "memory", "steam", "load", "klhook", "wardrobe", "character" };
    int i;
    if (!strncmp(name, "page.", 5)) return 1;
    if (use_drop) for (i = 0; i < (int)(sizeof drop / sizeof drop[0]); i++) if (!strcmp(name, drop[i])) return 1;
    return 0;
}

static int klbld_ini_hash(const char *path, int use_drop, char hex[33])
{   /* blake2b-128 of the normalised text (sections sorted, "[name]" then the lines). -> 1 ok */
    klbld_ini t; int order[256], i, j; klbld_b2 s;
    (void)klbld_secord;
    if (!klbld_ini_read(path, &t)) return 0;
    for (i = 0; i < t.nsec; i++) order[i] = i;
    for (i = 1; i < t.nsec; i++) { int x = order[i]; for (j = i - 1; j >= 0 && strcmp(t.sec[order[j]].name, t.sec[x].name) > 0; j--) order[j + 1] = order[j]; order[j + 1] = x; }
    klbld_b2_init(&s, 16);
    for (i = 0; i < t.nsec; i++) {
        int sec = order[i], l; char head[80];
        if (klbld_dropped(t.sec[sec].name, use_drop)) continue;
        _snprintf(head, sizeof head, "[%s]\n", t.sec[sec].name); head[sizeof head - 1] = 0;
        klbld_emit(&s, head);
        for (l = 0; l < t.nln; l++) if (t.ln[l].sec == sec) { klbld_emit(&s, t.ln[l].text); klbld_b2_upd(&s, "\n", 1); }
    }
    klbld_b2_hex(&s, hex);
    klbld_ini_free(&t);
    return 1;
}

typedef struct { int page; char slot[32]; char folder[64]; } klbld_red;

static int klbld_redcmp(const void *pa, const void *pb)
{
    const klbld_red *a = (const klbld_red *)pa, *b = (const klbld_red *)pb;
    if (a->page != b->page) return a->page < b->page ? -1 : 1;
    return strcmp(a->slot, b->slot);
}

static int klbld_redirects(const char *path, klbld_red *out, int cap)
{   /* kl_buildprint.redirects: [Redirect] (page 0) and [Redirect.N]; key upper-cased, value kept; later lines of a (page, slot) win. -> count, sorted */
    klbld_ini t; int i, l, n = 0, j;
    if (!klbld_ini_read(path, &t)) return 0;
    for (i = 0; i < t.nsec; i++) {
        const char *nm = t.sec[i].name; int page = 0; char *e;
        if (strncmp(nm, "redirect", 8)) continue;
        if (nm[8] == '.') { if (!nm[9]) continue; page = (int)strtol(nm + 9, &e, 10); if (*e || page < 0 || page > 9999) continue; }
        else if (nm[8]) continue;
        for (l = 0; l < t.nln; l++) {
            char *eq, k[32], *kk, *v; klbld_red r;
            if (t.ln[l].sec != i || !(eq = strchr(t.ln[l].text, '='))) continue;
            memset(&r, 0, sizeof r); r.page = page;
            { size_t kl = (size_t)(eq - t.ln[l].text); if (kl >= sizeof k) continue; memcpy(k, t.ln[l].text, kl); k[kl] = 0; }
            kk = klbld_trim(k); strncpy(r.slot, kk, sizeof r.slot - 1); _strupr(r.slot);
            v = klbld_trim(eq + 1); strncpy(r.folder, v, sizeof r.folder - 1);
            for (j = 0; j < n && (out[j].page != r.page || strcmp(out[j].slot, r.slot)); j++) ;
            if (j < n) out[j] = r; else if (n < cap) out[n++] = r;
        }
    }
    klbld_ini_free(&t);
    qsort(out, (size_t)n, sizeof *out, klbld_redcmp);
    return n;
}

/* ---------------------------------------------------------------- one map folder: kl_buildprint.map_print (hard hash only) */

static int klbld_has_backup(const char *name)
{   /* BACKUP = r"\.(before|bak|absent|old|orig)|\.log$|~$", case-insensitive, re.search */
    static const char *const w[] = { "before", "bak", "absent", "old", "orig" }; const char *p; size_t l = strlen(name); int i;
    for (p = name; *p; p++) if (*p == '.') for (i = 0; i < 5; i++) if (!_strnicmp(p + 1, w[i], strlen(w[i]))) return 1;
    if (l >= 4 && !_stricmp(name + l - 4, ".log")) return 1;
    return l && name[l - 1] == '~';
}

static int klbld_lang_ls(const char *name)
{   /* r"_Main_LS_[A-Za-z]+\.(WAV|WHD)$", case-insensitive */
    const char *p = name; size_t l = strlen(name);
    if (l < 4 || (_stricmp(name + l - 4, ".wav") && _stricmp(name + l - 4, ".whd"))) return 0;
    while ((p = strstr(p, "_Main_LS_")) != 0 || (p = 0)) {
        const char *q = p + 9; int letters = 0;
        while ((*q >= 'A' && *q <= 'Z') || (*q >= 'a' && *q <= 'z')) { q++; letters++; }
        if (letters && q == name + l - 4) return 1;
        p++;
    }
    for (p = name; *p; p++) {                      /* the tool's regex is case-insensitive: redo with a lower-case copy */
        char low[300]; size_t i; const char *x;
        if (l >= sizeof low) return 0;
        for (i = 0; i <= l; i++) low[i] = (char)(name[i] >= 'A' && name[i] <= 'Z' ? name[i] + 32 : name[i]);
        x = low;
        while ((x = strstr(x, "_main_ls_")) != 0) {
            const char *q = x + 9; int letters = 0;
            while (*q >= 'a' && *q <= 'z') { q++; letters++; }
            if (letters && q == low + l - 4) return 1;
            x++;
        }
        break;
    }
    return 0;
}

typedef struct { char name[128]; char low[128]; } klbld_fn;

static int klbld_fncmp(const void *a, const void *b) { return strcmp(((const klbld_fn *)a)->low, ((const klbld_fn *)b)->low); }

static int klbld_map_hard(const char *folder, char out16[17], DWORD *nfiles)
{   /* -> 1; out16 = first 16 hex of the folder's hard hash */
    char pat[MAX_PATH], p[MAX_PATH], full[40]; WIN32_FIND_DATAA d; HANDLE h; klbld_fn *fl; int n = 0, i; klbld_b2 s;
    snprintf(pat, sizeof pat, "%s\\*", folder);
    fl = (klbld_fn *)HeapAlloc(GetProcessHeap(), 0, sizeof(klbld_fn) * 512);
    if (!fl) return 0;
    h = FindFirstFileA(pat, &d);
    if (h == INVALID_HANDLE_VALUE) { HeapFree(GetProcessHeap(), 0, fl); return 0; }
    do {
        if ((d.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || strlen(d.cFileName) >= sizeof fl[0].name || n >= 512) continue;
        strcpy(fl[n].name, d.cFileName); strcpy(fl[n].low, d.cFileName); klbld_lower(fl[n].low); n++;
    } while (FindNextFileA(h, &d));
    FindClose(h);
    qsort(fl, (size_t)n, sizeof *fl, klbld_fncmp);       /* sorted(key=str.lower); qsort is not stable but equal lower-case names cannot coexist on NTFS */
    klbld_b2_init(&s, 16);
    *nfiles = 0;
    for (i = 0; i < n; i++) {
        const char *nm = fl[i].name, *low = fl[i].low; size_t l = strlen(nm); char hv[48], line[240]; int kind = 0;
        if (klbld_has_backup(nm) || klbld_lang_ls(nm)) continue;
        snprintf(p, sizeof p, "%s\\%s", folder, nm);
        if (l >= 4 && !_stricmp(nm + l - 4, ".zip")) kind = 1;
        else if (!strcmp(low, "klwardrobe.ini") || !strcmp(low, "klguns.ini")) kind = 2;
        else if (!strcmp(low, "kljoin.ini") || !strcmp(low, "kltalk.ini")) continue;      /* soft: only in --strict */
        else if (l >= 4 && (!_stricmp(nm + l - 4, ".whd") || !_stricmp(nm + l - 4, ".wav") || !_stricmp(nm + l - 4, ".snd") || !_stricmp(nm + l - 4, ".hti"))) kind = 3;
        else continue;
        if (kind == 1) { if (!klbld_zip_print(p, hv) && !klbld_file_hash(p, hv)) continue; }
        else if (kind == 2) { if (!klbld_ini_hash(p, 0, hv)) continue; }
        else if (!klbld_file_hash(p, hv)) continue;
        _snprintf(line, sizeof line, "%s|%s\n", low, hv); line[sizeof line - 1] = 0;
        klbld_b2_str(&s, line); (*nfiles)++;
    }
    HeapFree(GetProcessHeap(), 0, fl);
    klbld_b2_hex(&s, full); full[16] = 0; strcpy(out16, full);
    return 1;
}

/* ---------------------------------------------------------------- the full build code (kl_buildprint.compute, non-strict) */

typedef struct { char name[96]; char hard[17]; int active; } klbld_mapent;
static struct {
    volatile LONG state;                  /* 0 not started, 1 running, 2 done */
    char code[9], dll[17], ini[17], p01[17], red[17]; int nmaps, nactive; DWORD ms;
    klbld_mapent m[64];
} klbld_full;
static HANDLE klbld_worker;

static int klbld_strcmp_ent(const void *a, const void *b) { return strcmp(((const klbld_mapent *)a)->name, ((const klbld_mapent *)b)->name); }

static DWORD WINAPI klbld_full_thread(LPVOID unused)
{
    char root[64], base[MAX_PATH], pat[MAX_PATH], h33[48], z[40], line[300]; DWORD t0 = GetTickCount(); klbld_red red[64]; int nred, i, j; WIN32_FIND_DATAA d; HANDLE h;
    klbld_b2 s; (void)unused;
    GetPrivateProfileStringA("Expansion", "Root", "KLExpansion", root, sizeof root, klh_ini);
    /* global: dll, ini (presentation sections dropped), Patch01, redirect table */
    snprintf(base, sizeof base, "%s\\dinput8.dll", dir);
    if (klbld_file_hash(base, h33)) { memcpy(klbld_full.dll, h33, 16); klbld_full.dll[16] = 0; } else strcpy(klbld_full.dll, "absent");
    if (klbld_ini_hash(klh_ini, 1, h33)) { memcpy(klbld_full.ini, h33, 16); klbld_full.ini[16] = 0; } else strcpy(klbld_full.ini, "absent");
    snprintf(base, sizeof base, "%s\\Patch01.zip", dir);
    if (klbld_zip_print(base, z)) { memcpy(klbld_full.p01, z, 16); klbld_full.p01[16] = 0; } else strcpy(klbld_full.p01, "absent");
    nred = klbld_redirects(klh_ini, red, 64);
    klbld_b2_init(&s, 16);
    for (i = 0; i < nred; i++) {
        _snprintf(line, sizeof line, "%s%d:%s=%s", i ? "\n" : "", red[i].page, red[i].slot, red[i].folder); line[sizeof line - 1] = 0;
        klbld_emit(&s, line);
    }
    klbld_b2_hex(&s, h33); memcpy(klbld_full.red, h33, 16); klbld_full.red[16] = 0;
    /* maps: every directory under <root>\Maps that a redirect points at (case-blind) is "active"; a redirect to a missing folder
       is entered as the lower-cased name with hard "MISSING" */
    snprintf(pat, sizeof pat, "%s\\%s\\Maps\\*", dir, root);
    h = FindFirstFileA(pat, &d);
    if (h != INVALID_HANDLE_VALUE) do {
        char low[96]; int act = 0;
        if (!(d.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || !strcmp(d.cFileName, ".") || !strcmp(d.cFileName, "..") || strlen(d.cFileName) >= 96 || klbld_full.nmaps >= 64) continue;
        strcpy(low, d.cFileName); klbld_lower(low);
        for (i = 0; i < nred; i++) if (!_stricmp(red[i].folder, low)) act = 1;
        strcpy(klbld_full.m[klbld_full.nmaps].name, d.cFileName); klbld_full.m[klbld_full.nmaps].active = act; strcpy(klbld_full.m[klbld_full.nmaps].hard, "-");
        if (act) {
            DWORD nf = 0; snprintf(base, sizeof base, "%s\\%s\\Maps\\%s", dir, root, d.cFileName);
            if (!klbld_map_hard(base, klbld_full.m[klbld_full.nmaps].hard, &nf)) strcpy(klbld_full.m[klbld_full.nmaps].hard, "MISSING");
        }
        klbld_full.nmaps++;
    } while (FindNextFileA(h, &d));
    if (h != INVALID_HANDLE_VALUE) FindClose(h);
    for (i = 0; i < nred; i++) {
        char low[96]; int have = 0;
        strcpy(low, red[i].folder); klbld_lower(low);
        for (j = 0; j < klbld_full.nmaps; j++) { char x[96]; strcpy(x, klbld_full.m[j].name); klbld_lower(x); if (!strcmp(x, low)) have = 1; }
        if (!have && klbld_full.nmaps < 64) { strcpy(klbld_full.m[klbld_full.nmaps].name, low); strcpy(klbld_full.m[klbld_full.nmaps].hard, "MISSING"); klbld_full.m[klbld_full.nmaps].active = 1; klbld_full.nmaps++; }
    }
    qsort(klbld_full.m, (size_t)klbld_full.nmaps, sizeof klbld_full.m[0], klbld_strcmp_ent);
    klbld_b2_init(&s, 16);
    _snprintf(line, sizeof line, "dll=%s\nini=%s\npatch01=%s\nredirect=%s\n", klbld_full.dll, klbld_full.ini, klbld_full.p01, klbld_full.red); line[sizeof line - 1] = 0;
    klbld_b2_str(&s, line);
    for (i = 0; i < klbld_full.nmaps; i++) if (klbld_full.m[i].active) {
        klbld_full.nactive++;
        _snprintf(line, sizeof line, "%s=%s\n", klbld_full.m[i].name, klbld_full.m[i].hard); line[sizeof line - 1] = 0;
        klbld_emit(&s, line);
    }
    klbld_b2_hex(&s, h33); memcpy(klbld_full.code, h33, 8); klbld_full.code[8] = 0;
    klbld_full.ms = GetTickCount() - t0;
    klbld_say("code %s dll %s ini %s patch01 %s redirect %s (%d active map(s), %lu ms, %ld non-ascii name(s))", klbld_full.code, klbld_full.dll, klbld_full.ini, klbld_full.p01,
              klbld_full.red, klbld_full.nactive, (unsigned long)klbld_full.ms, klbld_nonascii);
    for (i = 0; i < klbld_full.nmaps; i++) if (klbld_full.m[i].active) klbld_say("map %s h=%s", klbld_full.m[i].name, klbld_full.m[i].hard);
    if (klbld_nonascii) klbld_say("GUESS: %ld non-ASCII zip member name(s): kl_buildprint.py may print another code (it decodes them as cp437)", klbld_nonascii);
    InterlockedExchange(&klbld_full.state, 2);
    return 0;
}

static void klbld_full_start(void)
{
    if (!klbld_full_on || klbld_full.state || InterlockedCompareExchange(&klbld_full.state, 1, 0) != 0) return;
    klbld_worker = CreateThread(0, 0, klbld_full_thread, 0, 0, 0);
    if (!klbld_worker) { InterlockedExchange(&klbld_full.state, 2); klbld_say("full code: worker thread not started"); return; }
    SetThreadPriority(klbld_worker, THREAD_PRIORITY_BELOW_NORMAL);
}

/* ---------------------------------------------------------------- the per-slot member-list print ("fp") */

#define KLBLD_NSLOTS_FA 9
static char klbld_tokcache[KLS_RULES][9];     /* "" = not computed */

static const char *klbld_rule_token(int r)
{   /* first 8 hex of the member-CRC print of <rule folder>\Fxx_Main.zip; "MISSING" when the file is not there */
    char path[MAX_PATH], z[40];
    if (r < 0 || r >= kls_nrules) return "-";
    if (klbld_tokcache[r][0]) return klbld_tokcache[r];
    snprintf(path, sizeof path, "%s%s", kls_rule[r].to, kls_slot[kls_rule[r].slot].zip);      /* "<game>\KLExpansion\Maps\DM03\" + "f01_main.zip" */
    if (klbld_zip_print(path, z)) { memcpy(klbld_tokcache[r], z, 8); klbld_tokcache[r][8] = 0; }
    else if (klbld_file_hash(path, z)) { memcpy(klbld_tokcache[r], z, 8); klbld_tokcache[r][8] = 0; }       /* unparsable zip: whole file (GUESS: never) */
    else strcpy(klbld_tokcache[r], "MISSING");
    return klbld_tokcache[r];
}

static const char *klbld_p01_token(void)
{
    static char t[9]; char path[MAX_PATH], z[40];
    if (t[0]) return t;
    snprintf(path, sizeof path, "%s\\Patch01.zip", dir);
    if (klbld_zip_print(path, z)) { memcpy(t, z, 8); t[8] = 0; } else strcpy(t, "absent");
    return t;
}

static int klbld_slot_bit(const char *name)
{   /* "F01".."F09" -> 0..8 (bit of the slot in the DLC mask, private_match.md 4), else -1 */
    return (name[0] == 'F' || name[0] == 'f') && name[1] == '0' && name[2] >= '1' && name[2] <= '9' && !name[3] ? name[2] - '1' : -1;
}

static int klbld_effective_rule(int s)
{   /* the rule a load of slot s uses now: kls_map's choice with the page the menu has latched (buildcheck 10) */
    int page = kls_page_now(), r = kls_find_rule(s, page);
    if (r < 0 && page) r = kls_find_rule(s, 0);
    return r;
}

static void klbld_my_fp(char *out, int cap)
{
    const char *tok[KLBLD_NSLOTS_FA]; int s, i, n;
    for (i = 0; i < KLBLD_NSLOTS_FA; i++) tok[i] = "-";
    if (kls_on) for (s = 0; s < kls_nslots; s++) { int b = klbld_slot_bit(kls_slot[s].name); if (b >= 0) tok[b] = klbld_rule_token(klbld_effective_rule(s)); }
    n = _snprintf(out, (size_t)cap, "P=%s", klbld_p01_token());
    for (i = 0; i < KLBLD_NSLOTS_FA && n > 0 && n < cap - 20; i++) n += _snprintf(out + n, (size_t)cap - n, ";F0%d=%s", i + 1, tok[i]);
    out[cap - 1] = 0;
}

static int klbld_field(const char *s, const char *key, char *out, int cap)
{   /* value of "key=" at the start or after ';' -> 1 found */
    size_t kl = strlen(key); const char *p = s;
    out[0] = 0;
    while (p && *p) {
        if (!strncmp(p, key, kl) && p[kl] == '=') { const char *v = p + kl + 1; int n = 0; while (v[n] && v[n] != ';' && n < cap - 1) { out[n] = v[n]; n++; } out[n] = 0; return 1; }
        p = strchr(p, ';'); if (p) p++;
    }
    return 0;
}

/* bits of the slots whose prints differ between mine and theirs. theirs_hook = 0 -> theirs is a stock client (every token "-", no P) */
static DWORD klbld_diff(const char *mine, const char *theirs, int theirs_hook)
{
    DWORD bits = 0; int i, p_differs = 0; char a[24], b[24], key[8], pa[24], pb[24];
    if (theirs_hook && klbld_field(mine, "P", pa, sizeof pa) && klbld_field(theirs, "P", pb, sizeof pb) && strcmp(pa, pb)) p_differs = 1;
    for (i = 0; i < KLBLD_NSLOTS_FA; i++) {
        _snprintf(key, sizeof key, "F0%d", i + 1); key[7] = 0;
        if (!klbld_field(mine, key, a, sizeof a)) strcpy(a, "-");
        if (!theirs_hook || !klbld_field(theirs, key, b, sizeof b)) strcpy(b, "-");
        if (strcmp(a, b) || (p_differs && strcmp(a, "-"))) bits |= 1u << i;
        else if (p_differs && strcmp(b, "-")) bits |= 1u << i;
    }
    return bits;
}

static void klbld_bits_text(DWORD bits, char *out, int cap)
{
    int i, n = 0;
    out[0] = 0;
    for (i = 0; i < KLBLD_NSLOTS_FA && n < cap - 5; i++) if (bits & (1u << i)) n += _snprintf(out + n, (size_t)cap - n, "%sF0%d", n ? "," : "", i + 1);
    if (!n) strcpy(out, "none");
}

/* ---------------------------------------------------------------- Steam calls through the interface below our proxy */

#define KLBLD_REAL(n) ((*(void ***)klbld_real)[n])
#define KLBLD_FWD(n) static __declspec(naked) void klbld_fwd##n(void) { __asm mov ecx, dword ptr [klbld_real] __asm mov eax, dword ptr [ecx] __asm jmp dword ptr [eax + 4 * n] }
KLBLD_FWD(0) KLBLD_FWD(1) KLBLD_FWD(2) KLBLD_FWD(3) KLBLD_FWD(4) KLBLD_FWD(5) KLBLD_FWD(6) KLBLD_FWD(7) KLBLD_FWD(8) KLBLD_FWD(9)
KLBLD_FWD(10) KLBLD_FWD(11) KLBLD_FWD(12) KLBLD_FWD(13) KLBLD_FWD(15) KLBLD_FWD(16) KLBLD_FWD(17) KLBLD_FWD(18) KLBLD_FWD(20)
KLBLD_FWD(21) KLBLD_FWD(22) KLBLD_FWD(23) KLBLD_FWD(24) KLBLD_FWD(25) KLBLD_FWD(26) KLBLD_FWD(27) KLBLD_FWD(28) KLBLD_FWD(29)
KLBLD_FWD(30) KLBLD_FWD(31) KLBLD_FWD(32) KLBLD_FWD(33) KLBLD_FWD(35)

/* Signatures: thiscall as __fastcall (this in ecx, edx unused, the rest on the stack, callee pops). Stack sizes from the ret counts proven in
   klmm.c's header: 16 NumMembers 8, 17 MemberByIndex 0x10 (hidden return pointer first), 18 GetLobbyData 0xc, 19 SetLobbyData 0x10, 23 GetLobbyMemberData
   0x14, 24 SetLobbyMemberData 0x10, 27 RequestLobbyData 8, 34 GetLobbyOwner 0xc (hidden return pointer first). FACT for 17 and 34: the game's own call
   sites push the result slot first (0x4d2b22..0x4d2b29: lea ecx,[esp+0x24]; push ecx; ... call edx; 0x6299d1..0x6299d8). */
typedef int (__fastcall *klbld_fn_num)(void *, void *, unsigned __int64);
typedef void *(__fastcall *klbld_fn_byidx)(void *, void *, unsigned __int64 *, unsigned __int64, int);
typedef const char *(__fastcall *klbld_fn_getdata)(void *, void *, unsigned __int64, const char *);
typedef const char *(__fastcall *klbld_fn_getmember)(void *, void *, unsigned __int64, unsigned __int64, const char *);
typedef void (__fastcall *klbld_fn_setmember)(void *, void *, unsigned __int64, const char *, const char *);
typedef char (__fastcall *klbld_fn_setdata)(void *, void *, unsigned __int64, const char *, const char *);
typedef char (__fastcall *klbld_fn_reqdata)(void *, void *, unsigned __int64);

static char __fastcall klbld_SetLobbyData(void *self, void *edx, unsigned __int64 lobby, const char *key, const char *value)
{   /* slot 19. Only the lobby owner can call it: key "name" (the game's first write, buildcheck 2) = this machine created the lobby */
    char r = ((klbld_fn_setdata)KLBLD_REAL(19))(klbld_real, 0, lobby, key, value);
    (void)self; (void)edx;
    if (key && !strcmp(key, "name") && lobby && lobby != klbld_host_lobby) { klbld_host_lobby = lobby; klbld_lobby = lobby; InterlockedExchange(&klbld_lobby_new, 1); }
    return r;
}

static void __fastcall klbld_LeaveLobby(void *self, void *edx, unsigned __int64 lobby)
{   /* slot 14, void, 8 bytes */
    (void)self; (void)edx;
    ((void (__fastcall *)(void *, void *, unsigned __int64))KLBLD_REAL(14))(klbld_real, 0, lobby);
    if (lobby == klbld_lobby) { klbld_lobby = 0; klbld_host_lobby = 0; InterlockedExchange(&klbld_lobby_new, 1); }
}

static void *__fastcall klbld_GetLobbyOwner(void *self, void *edx, unsigned __int64 *ret, unsigned __int64 lobby)
{   /* slot 34. Other callers (0x4e4bc5, 0x7ea691, buildcheck 2) pass through; the LobbyEnter completion is told by its return address */
    void *r = ((void *(__fastcall *)(void *, void *, unsigned __int64 *, unsigned __int64))KLBLD_REAL(34))(klbld_real, 0, ret, lobby);
    (void)self; (void)edx;
    if ((DWORD_PTR)_ReturnAddress() == (DWORD_PTR)KLH_VA(KLBLD_RA_ENTER) && lobby && lobby != klbld_lobby) { klbld_lobby = lobby; InterlockedExchange(&klbld_lobby_new, 1); }
    return r;
}

static void *__cdecl klbld_SteamMatchmaking(void)
{
    static LONG told; void **r = (void **)klbld_prev_accessor(), **vt; MEMORY_BASIC_INFORMATION mbi; int i, bad = -1;
    if (!r) return 0;
    if (r == klbld_real) return &klbld_proxy;
    if (!klh_rd((DWORD_PTR)r, &vt, sizeof vt)) bad = 0;
    for (i = 0; bad < 0 && i < KLBLD_NSLOT; i++) {
        void *f = 0;
        if (!klh_rd((DWORD_PTR)(vt + i), &f, sizeof f) || !VirtualQuery(f, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT || mbi.Type != MEM_IMAGE ||
            !(mbi.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY))) bad = i;
    }
    if (bad >= 0) {
        if (!InterlockedExchange(&told, 2)) klbld_say("NOT PROXIED: the interface has no code at slot %d of %d; the game gets it unchanged", bad, KLBLD_NSLOT);
        return r;
    }
    klbld_real = r;
    return &klbld_proxy;
}

/* ---------------------------------------------------------------- the mask hold (game thread only) */

/* Push (true mask & ~bits) into THIS machine's client dataset. bits = 0 restores the true mask. -> 1 pushed / unchanged, 0 not possible now */
static int klbld_push_mask(DWORD bits, DWORD *true_out)
{
    DWORD mgr, sm, cl, mask; WORD stored = 0;
    if (!klh_exe_ok) return 0;
    mgr = klh_rd32((DWORD_PTR)KLH_VA(KLS_DLCMGR));
    if (!mgr || klh_rd32(mgr) != KLS_DLCMGR_VT) return 0;                                       /* ZDownloadableContentManagerSteam, private_match.md 2 */
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION));
    cl = sm ? klh_rd32(sm + KLBLD_CLIENT_OFF) : 0;
    if (!cl || !kls_in_image(klh_rd32(cl)) || !klh_rd(cl + 0xb8 + 4, &stored, 2)) return 0;      /* a client object with a vtable in the image and the mask word readable */
    mask = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLBLD_MASKGET))((void *)(DWORD_PTR)mgr, 0) & 0xffffu;
    if (true_out) *true_out = mask;
    ((char (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLBLD_MASKSET))((void *)(DWORD_PTR)(cl + 0xb8), 0, mask & ~bits);
    return 1;
}

static void klbld_apply(DWORD want)
{
    static DWORD told_mask;
    DWORD tm = 0;
    if (!klbld_hold_on) return;
    if (!want && !klbld_hold_bits) return;                 /* nothing held, nothing wanted: no game call */
    if (klbld_push_mask(want, &tm)) {
        if (want != klbld_hold_bits) {
            char t[64]; klbld_bits_text(want, t, sizeof t);
            klbld_say(want ? "HOLD slot(s) %s: client mask %04lx -> %04lx" : "hold released (slot(s) %s): client mask back to %04lx", want ? t : "none", (unsigned long)tm, (unsigned long)(tm & ~want));
            told_mask = tm;
        }
        klbld_hold_bits = want;
    } else if (want != klbld_hold_bits && (told_mask++ < 3)) klbld_say("mask hold not possible now (no DLC manager / local client object yet)");
}

/* ---------------------------------------------------------------- the tick */

static void klbld_reset_lobby(void)
{
    klbld_pub_fp[0] = klbld_pub_code[0] = 0; klbld_joiner_tries = klbld_joiner_got = klbld_joiner_told = 0; klbld_joiner_next = 0;
    klbld_host_fp[0] = klbld_host_code[0] = 0; klbld_host_hooked = 0; klbld_my_member[0] = 0; klbld_want_bits = 0; klbld_poll_at = 0;
    memset(klbld_mem, 0, sizeof klbld_mem);
}

static void klbld_member_publish(unsigned __int64 lobby, const char *fp)
{
    if (!strcmp(klbld_my_member, fp)) return;
    ((klbld_fn_setmember)KLBLD_REAL(24))(klbld_real, 0, lobby, "klx_fp", fp);
    strncpy(klbld_my_member, fp, sizeof klbld_my_member - 1);
}

static void klbld_tick_host(unsigned __int64 lobby, DWORD now)
{
    char fp[256]; int n, i; DWORD want = 0;
    klbld_my_fp(fp, sizeof fp);
    if (strcmp(fp, klbld_pub_fp)) {
        ((klbld_fn_setdata)KLBLD_REAL(19))(klbld_real, 0, lobby, "klx", "1");
        ((klbld_fn_setdata)KLBLD_REAL(19))(klbld_real, 0, lobby, "klx_slots", fp);
        klbld_member_publish(lobby, fp);
        klbld_say("lobby (host): published %s", fp);
        strcpy(klbld_pub_fp, fp);
    }
    if (klbld_full.state == 2 && strcmp(klbld_full.code, klbld_pub_code)) {
        ((klbld_fn_setdata)KLBLD_REAL(19))(klbld_real, 0, lobby, "klx_code", klbld_full.code);
        strcpy(klbld_pub_code, klbld_full.code);
    }
    if (now - klbld_poll_at < KLBLD_POLL_MS) return;
    klbld_poll_at = now;
    n = ((klbld_fn_num)KLBLD_REAL(16))(klbld_real, 0, lobby);
    if (n < 0 || n > 64) return;
    for (i = 0; i < n && i < KLBLD_MEM; i++) {
        unsigned __int64 id = 0; const char *val; char theirs[256]; int hook, j, slot = -1; DWORD bits;
        ((klbld_fn_byidx)KLBLD_REAL(17))(klbld_real, 0, &id, lobby, i);
        if (!id) continue;
        for (j = 0; j < KLBLD_MEM; j++) if (klbld_mem[j].used && klbld_mem[j].id == id) { slot = j; break; }
        if (slot < 0) for (j = 0; j < KLBLD_MEM; j++) if (!klbld_mem[j].used) { slot = j; klbld_mem[j].used = 1; klbld_mem[j].id = id; klbld_mem[j].first = now; klbld_mem[j].mask = 0; break; }
        if (slot < 0) continue;
        val = ((klbld_fn_getmember)KLBLD_REAL(23))(klbld_real, 0, lobby, id, "klx_fp");
        strncpy(theirs, val ? val : "", sizeof theirs - 1); theirs[sizeof theirs - 1] = 0;
        hook = theirs[0] != 0;
        if (!hook && now - klbld_mem[slot].first < KLBLD_GRACE_MS) continue;                     /* may simply not have published yet */
        bits = klbld_diff(fp, theirs, hook);
        want |= bits;
        if (bits != klbld_mem[slot].mask) {
            char t[64]; klbld_bits_text(bits, t, sizeof t);
            klbld_say("member#%d %s: slot(s) %s differ (mine %s, theirs %s)", i, hook ? "has the hook" : "has NO klx_fp (stock client?)", t, fp, hook ? theirs : "-");
            klbld_mem[slot].mask = bits;
        }
    }
    klbld_want_bits = want;
}

static void klbld_tick_joiner(unsigned __int64 lobby, DWORD now)
{
    char fp[256], code[16]; const char *v;
    klbld_my_fp(fp, sizeof fp);
    klbld_member_publish(lobby, fp);
    if (now - klbld_poll_at < KLBLD_POLL_MS * 2) return;
    klbld_poll_at = now;
    v = ((klbld_fn_getdata)KLBLD_REAL(18))(klbld_real, 0, lobby, "klx_slots");
    if (v && v[0]) {
        DWORD bits; char t[64]; const char *c;
        if (strcmp(v, klbld_host_fp)) { strncpy(klbld_host_fp, v, sizeof klbld_host_fp - 1); klbld_host_fp[sizeof klbld_host_fp - 1] = 0; }
        klbld_host_hooked = 1; klbld_joiner_got = 1;
        c = ((klbld_fn_getdata)KLBLD_REAL(18))(klbld_real, 0, lobby, "klx_code");
        strncpy(code, c ? c : "", sizeof code - 1); code[sizeof code - 1] = 0;
        if (code[0] && strcmp(code, klbld_host_code)) {
            strcpy(klbld_host_code, code);
            if (klbld_full.state == 2) klbld_say("host's full build code %s, mine %s: %s", code, klbld_full.code, strcmp(code, klbld_full.code) ? "DIFFERENT (dll, ini, Patch01, redirect table or a map's files; run kl_buildprint.py --compare)" : "same");
            else klbld_say("host's full build code %s (mine not computed yet)", code);
        }
        bits = klbld_diff(fp, klbld_host_fp, 1);
        if (bits != klbld_want_bits) {
            klbld_bits_text(bits, t, sizeof t);
            klbld_say("host print %s, mine %s: slot(s) %s %s", klbld_host_fp, fp, t, bits ? "differ" : "match");
            klbld_want_bits = bits;
        }
        return;
    }
    if (klbld_joiner_got) return;                                           /* the key vanished after it had been read: keep the last verdict */
    if (klbld_joiner_tries < 8) {
        klbld_joiner_tries++;
        ((klbld_fn_reqdata)KLBLD_REAL(27))(klbld_real, 0, lobby);          /* RequestLobbyData: the game itself does this before it reads Scenario (0x6f2d81) */
        return;
    }
    if (!klbld_joiner_told) {
        klbld_joiner_told = 1;
        klbld_say("host lobby has no klx_slots after %d requests: host is probably stock / without the check%s", klbld_joiner_tries, klbld_nokeyblocks ? " - NoKeyBlocks=1: treated as stock" : " (warning only)");
        if (klbld_nokeyblocks) klbld_want_bits = klbld_diff(fp, "", 0);
    }
}

static void klbld_tick(int game_thread)
{
    unsigned __int64 lobby; DWORD now;
    if (klbld_mode <= 0) {
        if (klbld_mode < 0 || !game_thread) return;
        klbld_init();
        if (klbld_mode <= 0) return;
    }
    if (!game_thread) return;                                              /* Steam polls and the mask calls: the game's thread only (buildcheck 10) */
    now = GetTickCount();
    if (InterlockedExchange(&klbld_lobby_new, 0)) {
        klbld_reset_lobby();
        if (klbld_lobby) {
            klbld_say("lobby seen (%s)", klbld_lobby == klbld_host_lobby ? "host" : "joiner");
            klbld_full_start();
        } else klbld_say("lobby left");
    }
    lobby = klbld_lobby;
    if (!lobby || !klbld_real) { if (klbld_hold_bits) klbld_apply(0); return; }
    if (lobby == klbld_host_lobby) klbld_tick_host(lobby, now); else klbld_tick_joiner(lobby, now);
    if (klbld_hold_on) klbld_apply(klbld_want_bits);
    else if (klbld_want_bits && klbld_want_bits != klbld_hold_bits) { char t[64]; klbld_bits_text(klbld_want_bits, t, sizeof t); klbld_say("Hold=0: would hold slot(s) %s", t); klbld_hold_bits = klbld_want_bits; }
}

/* ---------------------------------------------------------------- init */

static void klbld_init(void)
{
    int i, v;
    if (klbld_mode) return;
    klbld_mode = -1;                                                       /* off unless every step below succeeds */
    v = (int)GetPrivateProfileIntA("Build", "Check", 0, klh_ini);
    if (v != 1) { if (v) klog("build: [Build] Check=%d is not 0 or 1: off", v); return; }
    klbld_hold_on = GetPrivateProfileIntA("Build", "Hold", 1, klh_ini) != 0;
    klbld_full_on = GetPrivateProfileIntA("Build", "Full", 1, klh_ini) != 0;
    klbld_nokeyblocks = GetPrivateProfileIntA("Build", "NoKeyBlocks", 0, klh_ini) != 0;
    if (!klh_exe_ok) { klbld_say("Check=1 but the process is not kl2.exe build 0490: off"); return; }
    if (!klmm_has_008()) { klbld_say("NOT INSTALLED: the loaded steam_api.dll does not ask for exactly SteamMatchMaking008: the table would not fit"); return; }
    for (i = 0; i < KLBLD_NSLOT; i++) klbld_vt[i] = 0;
    klbld_vt[0] = (void *)klbld_fwd0; klbld_vt[1] = (void *)klbld_fwd1; klbld_vt[2] = (void *)klbld_fwd2; klbld_vt[3] = (void *)klbld_fwd3; klbld_vt[4] = (void *)klbld_fwd4;
    klbld_vt[5] = (void *)klbld_fwd5; klbld_vt[6] = (void *)klbld_fwd6; klbld_vt[7] = (void *)klbld_fwd7; klbld_vt[8] = (void *)klbld_fwd8; klbld_vt[9] = (void *)klbld_fwd9;
    klbld_vt[10] = (void *)klbld_fwd10; klbld_vt[11] = (void *)klbld_fwd11; klbld_vt[12] = (void *)klbld_fwd12; klbld_vt[13] = (void *)klbld_fwd13;
    klbld_vt[14] = (void *)klbld_LeaveLobby;
    klbld_vt[15] = (void *)klbld_fwd15; klbld_vt[16] = (void *)klbld_fwd16; klbld_vt[17] = (void *)klbld_fwd17; klbld_vt[18] = (void *)klbld_fwd18;
    klbld_vt[19] = (void *)klbld_SetLobbyData;
    klbld_vt[20] = (void *)klbld_fwd20; klbld_vt[21] = (void *)klbld_fwd21; klbld_vt[22] = (void *)klbld_fwd22; klbld_vt[23] = (void *)klbld_fwd23; klbld_vt[24] = (void *)klbld_fwd24;
    klbld_vt[25] = (void *)klbld_fwd25; klbld_vt[26] = (void *)klbld_fwd26; klbld_vt[27] = (void *)klbld_fwd27; klbld_vt[28] = (void *)klbld_fwd28; klbld_vt[29] = (void *)klbld_fwd29;
    klbld_vt[30] = (void *)klbld_fwd30; klbld_vt[31] = (void *)klbld_fwd31; klbld_vt[32] = (void *)klbld_fwd32; klbld_vt[33] = (void *)klbld_fwd33;
    klbld_vt[34] = (void *)klbld_GetLobbyOwner;
    klbld_vt[35] = (void *)klbld_fwd35;
    for (i = 0; i < KLBLD_NSLOT; i++) if (!klbld_vt[i]) { klbld_say("NOT INSTALLED: proxy slot %d has no function (a build error)", i); return; }
    i = klh_iat("steam_api.dll", "SteamMatchmaking", (void *)klbld_SteamMatchmaking, (void **)&klbld_prev_accessor);
    if (!i || !klbld_prev_accessor) { klbld_say("NOT INSTALLED: the import steam_api.SteamMatchmaking was not found or not changed"); return; }
    klbld_mode = 1;
    klbld_say("Check=1: wrapper on steam_api.SteamMatchmaking installed (%d slot, %d slots, 3 overrides) Hold=%d Full=%d NoKeyBlocks=%d", i, KLBLD_NSLOT, klbld_hold_on, klbld_full_on, klbld_nokeyblocks);
}

#endif /* KLBUILD_C */
