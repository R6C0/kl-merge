/*
 * kljoin.c - 'jump boxes': a level made of two places that are far apart (Retomoto Tower: the tower at y 19,600
 * and the lobby at y 560) is joined by data. When a local player walks into a box, the hook asks the game for a
 * jump to an entry of the level's own jump list. Part of KLHook (included by klhook.c, SHIP and TEST alike).
 * Two data writes, no code byte. Evidence and the level's side: re\retomoto_fa.md 3 and 9.4.
 *
 * THE GAME'S MECHANISM (read 2026-10-09, kl2.exe build 0490)
 *   gamedata = [0xdd265c] (ZFFGameData). Every ZJumpPoint of a level enters itself at init (0x6e6620 -> 0x6c0730)
 *   in the jump list: 32-byte entries from [gamedata+0x8c4] to [gamedata+0x8c8]:
 *       +0x00 char *name (the entity's name, [[node+0x24]+4]+0x6c)   +0x04 position, 3 floats
 *       +0x10 direction, 3 floats                                    +0x1c the ZJumpPoint
 *   in scene order. ZFFGameData's update calls 0x57e110 every frame:
 *       if ([0x156b35c] /message/ or [0x156b358] /debug/) { both = 0; if the list is not empty {
 *           ++[gamedata+0x8d0]; if ([gamedata+0x8d4] > -1) { [+0x8d0] = [+0x8d4]; [+0x8d4] = -1; }
 *           if ([+0x8d0] >= count) [+0x8d0] = 0;                     <- an index past the end jumps to entry 0
 *           0x8f3fa0(entry position, matrix from entry direction, flag = came by message);
 *           0x72e0f0(entry's ZJumpPoint): 'AITrigger' to the jump point's own reference list } }
 *   0x8f3fa0 loops i = 0, 1 over the LOCAL players (0x660b00: [gamedata + 0x828 + 4 * (signed char)[gamedata +
 *   0x898 + i]], none when that byte is 0xff), skips one whose entity has flag bit 10 or whose +0xd44 is set, and
 *   puts each of the others at the entry. With flag 1 (the message path, set only by ZJumpPoint's own message
 *   handler 0x491e42) it then walks the player's crew [player+0xcd0]+0xa4 - a Fragile Alliance player has none:
 *   crash 0x8f40c9 (run RT3). The debug request [0x156b358] has NO writer in the exe (two references, both in
 *   0x57e110: the compare and the clear), flag 0, no crew walk. Written from outside the process in run RT4:
 *   the player was in the lobby car within 0.25 s, no fault.
 *   So the hook writes  [gamedata+0x8d4] = entry  and  [0x156b358] = 1  (`ceg_ranges.py`: 0 checks for
 *   0x156b358, 0xdd265c; gamedata is heap).
 *
 * WHAT THE HOOK DOES
 *   Each tick, for local player 0 and 1: feet = 3 floats at player+0x460 (x, y up, z; klauto.c PLAYERS). When
 *   the feet are inside a box and were not at the tick before, the box's entry is requested - once per entry
 *   into the box; the player has to leave it (the jump does that) before it can fire again. While a request is
 *   still pending ([0x156b358] != 0 or [gamedata+0x8d4] != -1) nothing is written; the box fires at the next tick.
 *   A box is only active on its own level, and its entry is checked against the list every time:
 *     Entry=5            index in the jump list (scene order of the level's JumpPoints)
 *     Name=06_Exit       the entry's name must contain this text; without Entry= the entry is found by it
 *     Target=6272 563 -6305   the entry's position must be within Tolerance (default 8) of this; without Entry=
 *                        and Name= the entry is found by it (survives a re-ordering of the JumpPoints)
 *   A box whose checks fail does not fire and says why, once. A level whose jump list stays EMPTY (no ZJumpPoint
 *   at all: a KLJoin.ini left beside another level's archive - run J3s, the bank with Retomoto's file) is said
 *   too, once a local player exists and the list has stood still: 'join: box 9 NOT usable on this level: the
 *   jump list is empty'. (Until 2026-10-09 an empty list was never described, so that run showed nothing.)
 *   MULTIPLAYER (from the code above, not run): the request is local in both halves. The hook looks only at the
 *   feet of this machine's local players, and 0x8f3fa0 moves only this machine's local players - BOTH of them
 *   when one enters the box (split screen; Arcade and online have one). A remote player is moved by his own
 *   machine when his own feet enter the box there, which needs this hook and the same box on that machine; a
 *   peer without it stays in the tower. Player movement is owner-authoritative (re\netcode.md 8.1), so the jump
 *   reaches the others as a position. The entry's 'AITrigger' list fires on the machine that jumped only.
 *   NOT CHECKED HERE: whether the player is alive (a dead player's feet stay where he fell; a box fires on
 *   ENTERING, so a body lying in it does not fire again), and bots (they are not local players: AI does not jump).
 *
 * WHERE THE BOXES COME FROM
 *   1. KLJoin.ini in the folder of the level archive the game opened (KLExpansion\Maps\<map>\KLJoin.ini, or
 *      Scenes\Locations\F01\KLJoin.ini in the test slot): read when that archive is opened, active only while the
 *      engine's scene is that level, IGNORED when the archive is the stock one (a stock level has no join).
 *   2. KLHook.ini, the same sections, for tests: active on every level unless Scene= names one (a text the scene
 *      name must contain, e.g. Scene=F01).
 *   [Join]                 up to 8 boxes a file: [Join], [Join.2] ... [Join.8]
 *   Min=2802 19560 789     box corners, world units, x y z (y is up); blanks or commas
 *   Max=3142 19860 1029
 *   Entry=5                see above; at least one of Entry / Name / Target
 *   Name=06_Exit
 *   Target=6272 563 -6305
 *   Tolerance=8
 *   Scene=F01              KLHook.ini only
 *   klhook\KLJoin.retomoto.ini is the file for Retomoto Tower (box = kl_fa_author.JOIN_BOX).
 *
 * LOG
 *   join: 1 box(es) from <file> for level f01\f01_main
 *   join: box 1: (2802, 19560, 789) - (3142, 19860, 1029) -> entry 5, name '06_Exit', target (6272, 563, -6305)
 *   join: level 'SCENES\Locations\F01\F01_Main.gms': 1 box(es) active; jump list has 6 entries    (1.5 s after the list stopped growing)
 *   join: box 1 -> entry 5 '06_Exit' at (6272, 563, -6305)
 *   join: player 0 entered box 1 at (2950, 19601, 900): jump to entry 5 '06_Exit' requested ([gamedata+0x8d4] = 5, [0x156b358] = 1)
 *   join: player 0 is at (6272, 563, -6305) 500 ms after the request
 *
 * TESTED OFF-GAME (scratch harness `jhook`): made-up game data, jump list and players reached through a mapped
 * copy of kl2.exe.
 * RUN LIVE (2026-10-09, agent i-live, the 12:49 build): J1b direct boot and J2 / J3 in real Arcade sessions, box
 * x 2550..2790 in front of the tower car - `join: player 0 entered box 9 at (2709, 19601, 1099): jump to entry 5
 * 'Specials!JumpPoints!06_Exit' requested`, next position the lobby car (6411, 570, -6221); the process lived on
 * for minutes with no INTEGRITY EXIT. J1's box INSIDE the car never fired: its doors are shut, the player stops at
 * x 2727. Two defects seen there are fixed here (the list judged while still filling; the '500 ms' line at once).
 */
#ifndef KLJOIN_C
#define KLJOIN_C

#define KLJ_REQUEST  0x0156b358               /* the debug jump request (.data) */
#define KLJ_NBOX     16                       /* 0..7 from KLHook.ini, 8..15 from the level's KLJoin.ini */
#define KLJ_MAXLIST  256

static struct {
    int on, entry, has_target, said, wasactive;
    float lo[3], hi[3], target[3], tol;
    char name[48], scene[48];
    char inside[2];
} klj_box[KLJ_NBOX];
static int klj_any, klj_tick_on = 1;
static char klj_map_key[64], klj_map_file[MAX_PATH]; static FILETIME klj_map_ft;
static CRITICAL_SECTION klj_cs;
static struct { DWORD at; int player, armed; } klj_after;
static int klj_settle_ms = 1500;              /* the jump list is filled entry by entry while the level loads: it is judged once its length has stood still this long */

static int klj_vec(const char *sec, const char *key, const char *file, float v[3])
{
    char t[96], *p;
    if (!GetPrivateProfileStringA(sec, key, "", t, sizeof t, file)) return 0;
    for (p = t; *p; p++) if (*p == ',' || *p == ';' || *p == '(' || *p == ')') *p = ' ';
    return sscanf(t, "%f %f %f", &v[0], &v[1], &v[2]) == 3;
}

/* read [Join], [Join.2] .. [Join.8] of a file into boxes base .. base+7 -> boxes usable */
static int klj_read(const char *file, int base, int from_map)
{
    int i, n = 0;
    for (i = 0; i < 8; i++) {
        char sec[16], t[32]; float a[3], b[3]; int k, e;
        memset(&klj_box[base + i], 0, sizeof klj_box[0]);
        if (i) snprintf(sec, sizeof sec, "Join.%d", i + 1); else strcpy(sec, "Join");
        if (!GetPrivateProfileStringA(sec, 0, "", t, sizeof t, file)) continue;          /* no such section */
        if (!GetPrivateProfileIntA(sec, "Enable", 1, file)) continue;
        if (!klj_vec(sec, "Min", file, a) || !klj_vec(sec, "Max", file, b)) { klog("join: [%s] of %s refused: Min= and Max= need three numbers each", sec, file); continue; }
        for (k = 0; k < 3; k++) { klj_box[base + i].lo[k] = a[k] < b[k] ? a[k] : b[k]; klj_box[base + i].hi[k] = a[k] < b[k] ? b[k] : a[k]; }
        e = (int)GetPrivateProfileIntA(sec, "Entry", -1, file);
        klj_box[base + i].entry = e >= 0 && e < KLJ_MAXLIST ? e : -1;
        GetPrivateProfileStringA(sec, "Name", "", klj_box[base + i].name, sizeof klj_box[0].name, file);
        klj_box[base + i].has_target = klj_vec(sec, "Target", file, klj_box[base + i].target);
        GetPrivateProfileStringA(sec, "Tolerance", "8", t, sizeof t, file); klj_box[base + i].tol = (float)atof(t);
        if (!from_map) { GetPrivateProfileStringA(sec, "Scene", "", klj_box[base + i].scene, sizeof klj_box[0].scene, file); _strlwr(klj_box[base + i].scene); }
        if (klj_box[base + i].entry < 0 && !klj_box[base + i].name[0] && !klj_box[base + i].has_target) { klog("join: [%s] of %s refused: it needs Entry=, Name= or Target=", sec, file); continue; }
        klj_box[base + i].on = 1; n++;
        klog("join: box %d: (%g, %g, %g) - (%g, %g, %g) -> entry %d, name '%s', target %s(%g, %g, %g)%s%s", base + i + 1,
             klj_box[base + i].lo[0], klj_box[base + i].lo[1], klj_box[base + i].lo[2], klj_box[base + i].hi[0], klj_box[base + i].hi[1], klj_box[base + i].hi[2],
             klj_box[base + i].entry, klj_box[base + i].name, klj_box[base + i].has_target ? "" : "none ", klj_box[base + i].target[0], klj_box[base + i].target[1], klj_box[base + i].target[2],
             klj_box[base + i].scene[0] ? ", only on a scene containing " : "", klj_box[base + i].scene);
    }
    return n;
}

static void klj_count(void) { int i; klj_any = 0; for (i = 0; i < KLJ_NBOX; i++) klj_any += klj_box[i].on; }

/* From klsteam.c's klh_level_open: the game opens the level archive <key> ("f01\f01_main.zip") from <opened>;
   verdict 1 = it is the stock archive. Looks for KLJoin.ini beside it. */
static void klj_level_open(const char *key, const char *opened, int verdict)
{
    char file[MAX_PATH], k[64], *s; WIN32_FILE_ATTRIBUTE_DATA fa; int i, have, n;
    DWORD len = GetFullPathNameA(opened, MAX_PATH, file, 0);      /* absolute: a profile call with a relative name looks in the Windows folder */
    if (!len || len >= MAX_PATH || !(s = strrchr(file, 0x5c))) return;
    if ((size_t)(s - file) + 12 >= sizeof file) return;
    strcpy(s + 1, "KLJoin.ini");
    snprintf(k, sizeof k, "%s", key); if ((s = strrchr(k, '.')) != 0) *s = 0;
    have = GetFileAttributesExA(file, GetFileExInfoStandard, &fa) && !(fa.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY);
    EnterCriticalSection(&klj_cs);
    if (!have || verdict == 1) {
        if (!strcmp(klj_map_key, k)) {                        /* the same level again, now without boxes */
            for (i = 8; i < KLJ_NBOX; i++) klj_box[i].on = 0;
            klj_map_key[0] = klj_map_file[0] = 0; klj_count();
            klog("join: level %s: its boxes are dropped (%s)", k, have ? "the archive is the stock one" : "no KLJoin.ini beside the archive opened now");
        } else if (have) klog("join: %s ignored: the archive beside it is the stock %s", file, key);
    } else if (strcmp(klj_map_key, k) || _stricmp(klj_map_file, file) || CompareFileTime(&klj_map_ft, &fa.ftLastWriteTime)) {
        strcpy(klj_map_key, k); strcpy(klj_map_file, file); klj_map_ft = fa.ftLastWriteTime;
        klog("join: reading %s for level %s", file, k);
        n = klj_read(file, 8, 1); klj_count();
        klog("join: %d box(es) from %s for level %s", n, file, k);
    }
    LeaveCriticalSection(&klj_cs);
}

static int klj_contains(const char *hay, const char *needle)
{   /* case-insensitive substring */
    size_t n = strlen(needle);
    for (; *hay; hay++) if (!_strnicmp(hay, needle, n)) return 1;
    return !n;
}

/* The entry a box means, checked against the list as it is now. -> index, or -1 and why[160] */
static int klj_resolve(int b, DWORD lo, int count, char *why, char name[64], float pos[3])
{
    int e = klj_box[b].entry, i, k; BYTE ent[32];
    if (e < 0) {
        for (i = 0; i < count && e < 0; i++) {
            if (!klh_rd(lo + 32 * i, ent, 32)) break;
            if (klj_box[b].name[0]) { if (klh_rdstr(*(DWORD *)ent, name, 64) && klj_contains(name, klj_box[b].name)) e = i; }
            else { for (k = 0; k < 3 && fabs(((float *)(ent + 4))[k] - klj_box[b].target[k]) <= klj_box[b].tol; k++) ; if (k == 3) e = i; }
        }
        if (e < 0) { snprintf(why, 160, "no entry of the %d in the jump list has %s", count, klj_box[b].name[0] ? "that name" : "that position"); return -1; }
    }
    if (e >= count) { snprintf(why, 160, "entry %d is past the end of the jump list (%d entries; the game would jump to entry 0)", e, count); return -1; }
    if (!klh_rd(lo + 32 * e, ent, 32)) { strcpy(why, "the jump list cannot be read"); return -1; }
    if (!klh_rdstr(*(DWORD *)ent, name, 64)) strcpy(name, "?");
    memcpy(pos, ent + 4, 12);
    if (klj_box[b].name[0] && !klj_contains(name, klj_box[b].name)) { snprintf(why, 160, "entry %d is '%s', not '%s': another level, or the jump points were re-ordered", e, name, klj_box[b].name); return -1; }
    if (klj_box[b].has_target)
        for (k = 0; k < 3; k++) if (fabs(pos[k] - klj_box[b].target[k]) > klj_box[b].tol) {
            snprintf(why, 160, "entry %d '%s' is at (%g, %g, %g), not at the target: another level, or the jump point moved", e, name, pos[0], pos[1], pos[2]); return -1; }
    return e;
}

static void klj_tick(void)
{
    static char last[160]; static int lastcount = -1, toldlist, toldempty; static DWORD countat;
    char scene[160], key[64], why[160], name[64]; float feet[3], pos[3]; BYTE sel[2];
    DWORD gd, lo = 0, hi = 0, req = 0, pl, now = GetTickCount(); int pend = 0, count, b, i, k, act = 0, newscene, e;
    if (!klj_any || !klj_tick_on || !klh_exe_ok) return;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) { last[0] = 0; lastcount = -1; return; }       /* frontend: nothing is active */
    newscene = strcmp(scene, last) != 0;
    if (newscene) { snprintf(last, sizeof last, "%s", scene); lastcount = -1; toldlist = 0; toldempty = 0; }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x8c4, &lo, 4) || !klh_rd(gd + 0x8c8, &hi, 4) || !klh_rd(gd + 0x898, sel, 2)) return;
    count = lo && hi > lo ? (int)((hi - lo) >> 5) : 0;
    if (count > KLJ_MAXLIST) return;
    /* Seen live (runs J1b, J2): the scene name changes before the level's ZJumpPoints have entered themselves, and
       they do so one by one - a box judged at once was called 'NOT usable ... (1 entries' in every run although it
       worked. So the list is described, and the boxes are checked against it for the log, only when its length
       has not changed for klj_settle_ms. A player entering a box is resolved against the list as it is then. */
    if (count != lastcount) { lastcount = count; countat = now; }
    EnterCriticalSection(&klj_cs);
    for (b = 0; b < KLJ_NBOX; b++) {
        int a = klj_box[b].on && (b >= 8 ? !strcmp(key, klj_map_key) : !klj_box[b].scene[0] || klj_contains(scene, klj_box[b].scene));
        if (newscene || !a) { klj_box[b].inside[0] = klj_box[b].inside[1] = 0; klj_box[b].said = -1; }
        klj_box[b].wasactive = a; act += a;
    }
    k = act && count && now - countat >= (DWORD)klj_settle_ms;                      /* the list has stood still */
    if (k && toldlist != count) {
        toldlist = count;
        klog("join: level '%s': %d box(es) active; jump list has %d entries", scene, act, count);
    }
    /* An empty list is only called empty when the level runs - a local player exists - and the length has stood
       still: the ZJumpPoints enter themselves during the load, before there is a player (ASSUMPTION on that order;
       a list that fills later is described by the lines above all the same). */
    if (act && !count && !toldempty && now - countat >= (DWORD)klj_settle_ms && sel[0] != 0xff && sel[0] < 28 && klh_rd32(gd + 0x828 + 4 * sel[0])) {
        toldempty = 1;
        klog("join: level '%s': %d box(es) active but the jump list is EMPTY - the level has no ZJumpPoint", scene, act);
        for (b = 0; b < KLJ_NBOX; b++) if (klj_box[b].wasactive)
            klog("join: box %d NOT usable on this level: the jump list is empty (a KLJoin.ini of another level beside this archive?)", b + 1);
    }
    if (k) for (b = 0; b < KLJ_NBOX; b++) if (klj_box[b].wasactive && klj_box[b].said != count) {       /* once per list length */
        klj_box[b].said = count;
        if ((e = klj_resolve(b, lo, count, why, name, pos)) >= 0) klog("join: box %d -> entry %d '%s' at (%g, %g, %g)", b + 1, e, name, pos[0], pos[1], pos[2]);
        else klog("join: box %d NOT usable on this level: %s", b + 1, why);
    }
    if (klj_after.armed && now - klj_after.at >= 500) {       /* (was `at = tick | 1` and `tick - at >= 500`: true at once on an even tick - run J1b) */
        klj_after.armed = 0;
        if (sel[klj_after.player] != 0xff && sel[klj_after.player] < 28 && (pl = klh_rd32(gd + 0x828 + 4 * sel[klj_after.player])) != 0 && klh_rd(pl + 0x460, feet, 12))
            klog("join: player %d is at (%.0f, %.0f, %.0f) 500 ms after the request", klj_after.player, feet[0], feet[1], feet[2]);
    }
    if (act && count && kl_online()) {                        /* [Net] OnlineSafe: the jump request would desync a network session (re/netcode_plan.md 2.1) */
        static int toldnet;
        if (!toldnet++) klog("join: a network session: no jump request is written ([Net] OnlineSafe=1)");
        act = 0;
    }
    for (i = 0; act && count && i < 2; i++) {
        if (sel[i] == 0xff || sel[i] >= 28 || !(pl = klh_rd32(gd + 0x828 + 4 * sel[i])) || !klh_rd(pl + 0x460, feet, 12)) { for (b = 0; b < KLJ_NBOX; b++) klj_box[b].inside[i] = 0; continue; }
        for (b = 0; b < KLJ_NBOX; b++) {
            int in;
            if (!klj_box[b].wasactive) continue;
            for (k = 0; k < 3 && feet[k] >= klj_box[b].lo[k] && feet[k] <= klj_box[b].hi[k]; k++) ;      /* a NaN is outside */
            in = k == 3;
            if (!in || klj_box[b].inside[i]) { klj_box[b].inside[i] = (char)in; continue; }
            if (!klh_rd((DWORD_PTR)KLH_VA(KLJ_REQUEST), &req, 4) || !klh_rd(gd + 0x8d4, &pend, 4) || req || pend != -1) continue;    /* a request is pending: next tick */
            klj_box[b].inside[i] = 1;
            if ((e = klj_resolve(b, lo, count, why, name, pos)) < 0) { klog("join: player %d entered box %d at (%.0f, %.0f, %.0f) but NO jump: %s", i, b + 1, feet[0], feet[1], feet[2], why); continue; }
            req = 1;
            if (klh_data((void *)(DWORD_PTR)(gd + 0x8d4), &e, 4, "jump-list entry") && klh_data(KLH_VA(KLJ_REQUEST), &req, 4, "debug jump request")) {
                klog("join: player %d entered box %d at (%.0f, %.0f, %.0f): jump to entry %d '%s' requested ([gamedata+0x8d4] = %d, [0x156b358] = 1)", i, b + 1, feet[0], feet[1], feet[2], e, name, e);
                klj_after.at = now; klj_after.player = i; klj_after.armed = 1;
            } else klog("join: player %d entered box %d but the request could NOT be written", i, b + 1);
        }
    }
    LeaveCriticalSection(&klj_cs);
}

static void klj_init(void)
{
    int n;
    InitializeCriticalSection(&klj_cs);
    klj_tick_on = GetPrivateProfileIntA("KLHook", "Join", 1, klh_ini);
    n = klj_read(klh_ini, 0, 0); klj_count();
    if (n) klog("join: %d box(es) from KLHook.ini%s", n, klj_tick_on ? "" : " - but [KLHook] Join=0: nothing fires");
}
#ifdef KLHOOK_HARNESS
__declspec(dllexport) void klj_test_settle(int ms) { klj_settle_ms = ms; }
#endif
#endif /* KLJOIN_C */
