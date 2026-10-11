/* cutdiag.inc: read-only diagnostics for level-start cutscenes (AIMonitor -> ZMiniCutsceneRout -> squad -> ZMiniCutscene).
   Included by anp_loader.c after campaign.inc (uses anp_log, readable, rtti_name, node_table, g_dir); ticked from
   my_PeekMessageA on the main thread. Reads memory only: no code bytes, no engine calls, no writes into the game.

   Opt-in: create <DD>\ANP_cutdiag.txt. Each non-empty line is an entity name to track (node+0x6c, exact match) or a
   node index (all digits); '#' starts a comment; "off" disables. An empty file tracks M01's four camera cutscenes.
   Lines are prefixed "cutdiag:" in ANP_log.txt. Also logs Enter/Space/Escape presses ("key Enter down"): Enter is
   kl2's SkipCutSeq/SkipGeneric key, so an Enter just after "Buffering 100%" can skip an intro.
   The census heap scan starts 4 s after the scene's node table appears and copies up to 96 MB per 250 ms tick
   (ReadProcessMemory, so a page freed meanwhile cannot fault); expect a few short hitches while it runs.

   What it logs (times are ms since the node table of the current scene appeared):
   G   global state, on change and every 10 s:
       AIMonitor  mon n = registered ZAIMonitors (0x168a254, max 8, array 0x168a258)
                  fired = 0x168a200[0..2]: list 0/1/2 fired (list 2 = the level-start list, fired by fire(2) 0x8b5f60)
                  def = 0x168a206 deferred fire(2) (online only), x20c = 0x168a20c (non-zero blocks list 2)
       InGame state (gameMgr+0x3e3c; its activation/deactivation calls the AIMonitor listener 0x7f6430 -> fire(2)):
                  pend = gameMgr+0x48ac (set to the state by level start 0x705200, consumed by gameMgr update 0x4bccc7)
                  a68/a69/a6a/a6c its flags (a69 = activated by 0x65a4d0, a68 = deactivated by 0x5d5d80)
                  cur = [0xe0e640] (last state activated/deactivated), n644 = [0xe0e644]
       b44 = gameApp+0xb44 (non-zero: 0x705200 skips the AIMonitor start entirely)
       ses = session *0x168e598: +54 (2/3 = online: fire deferred), +5c (game mode), +70, +1b4 (story start zeroes it,
             the autoload does not)
       p828/p82c players, buddy = gameMgr+0x4cf0 (DD's registered 'Kane' ZSoldier: DM Lynch after ANP_MERC_IDS)
       mcrun = 0x168dcc8 (ZMiniCutscene Start count; incremented even for a cutscene whose binding failed)
   M   each registered ZAIMonitor: owner node/name, list pointers +50/+54/+58 (once per scene and on change)
   CENSUS  once, after a heap scan for every ZMiniCutsceneRout (vtable 0xbcdf14) of this scene: totals, and the names
       of routs whose ZMiniCutscene is dead: +34 (bad command/dep) or +35 (an Actor section did not bind)
   C   any rout (census) whose state changes: b40 started (AITrigger accepted), b41 AIBlocker, MC +34/+35, MC state +8
   R   each tracked rout, on change: rout +40..+43, +64 run mode (0 eRM_Normal: queued on the squad via 0x791090;
       1 NonIntrusive: started at once), +38 squad, +58 ZMiniCutscene; MC +8 state, +34, +35, +3e..+42 player lock,
       +4 squad; squad +bc busy, +8c, +90 (0x7f6750 drops the behaviour when both are 0), +154 current behaviour,
       +c0 member count, +19c fusion, +f4 fused squads
   S   the tracked rout's sections ([MC+20, MC+24)): Actor tracks with name, bound actor +20 and member +24; the
       Kane section MC+30 (bound to gameMgr+0x4cf0)
   K   the squad's members: actor, merc value (controller +0x6e8; 1 = Kane/buddy), parent group name (what the
       binder 0x4b64e0 compares)
   E   once per tracked rout: where the owner geom points at the rout (event storage discovery, depth 2) */

#define CD_ROUT_VT   0xbcdf14
#define CD_MC_VT     0xbce05c
#define CD_ACTOR_VT  0xbcdfe0
#define CD_AIMON_VT  0xbc49f4
#define CD_MAXROUT   2048
#define CD_MAXT      16

static int g_cdOn = -1;
static char g_cdNames[CD_MAXT][64]; static long g_cdIdx[CD_MAXT]; static int g_cdNN;   /* idx >= 0: line was a node index */
static DWORD g_cdBase, g_cdCap, g_cdStride, g_cdT0, g_cdLast, g_cdBeat;
static DWORD g_cdScan; static int g_cdScanDone, g_cdLines;
static DWORD g_cdR[CD_MAXROUT]; static WORD g_cdRs[CD_MAXROUT]; static int g_cdNR;
static struct { DWORD rout; long node; char name[64]; char last[600]; char lastS[1200]; char lastK[900]; int disc; } g_cdT[CD_MAXT];
static int g_cdNT;
static char g_cdG[700], g_cdM[700];
static DWORD g_cdFired2At, g_cdInGameAt;

static DWORD cd32(DWORD a) { return (a >= 0x10000 && readable((void*)a, 4)) ? *(DWORD*)a : 0; }
static BYTE cd8(DWORD a) { return (a >= 0x10000 && readable((void*)a, 1)) ? *(BYTE*)a : 0; }
static void cd_str(DWORD p, char *out, int n) {           /* NUL-terminated printable string at p, or "" */
    out[0] = 0;
    if (p < 0x10000 || !readable((void*)p, 1)) return;
    int k = 0;
    while (k < n - 1 && readable((void*)(p + k), 1)) { char c = *(char*)(p + k); if (!c) break; if (c < 32 || c > 126) { k = 0; break; } out[k++] = c; }
    out[k] = 0;
}
static long cd_node_idx(DWORD node) {
    if (!g_cdStride || node < g_cdBase || node >= g_cdBase + g_cdCap * g_cdStride || (node - g_cdBase) % g_cdStride) return -1;
    return (long)((node - g_cdBase) / g_cdStride);
}
static void cd_node_name(DWORD node, char *out, int n) { if (cd_node_idx(node) < 0) { out[0] = 0; return; } cd_str(cd32(node + 0x6c), out, n); }
/* a rout of the current scene: owner geom +0x24 -> node (+4) of this node table whose object (+0x60) is the owner */
static long cd_rout_node(DWORD r) {
    if (cd32(r) != CD_ROUT_VT) return -1;
    DWORD owner = cd32(r + 0x24), node = cd32(owner + 4);
    long i = cd_node_idx(node);
    if (i < 0 || cd32(node + 0x60) != owner) return -1;
    return i;
}
static void cd_vlog(const char *fmt, ...) {
    if (g_cdLines > 6000) return;
    if (++g_cdLines == 6000) { anp_log("cutdiag: line cap reached, logging stops"); return; }
    char b[2048]; va_list ap; va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    anp_log("cutdiag: %s", b);
}

static void cutdiag_init(void) {
    char p[MAX_PATH], line[256]; _snprintf(p, sizeof p, "%s\\ANP_cutdiag.txt", g_dir);
    FILE *f = fopen(p, "r");
    g_cdOn = 0;
    if (!f) return;
    while (fgets(line, sizeof line, f) && g_cdNN < CD_MAXT) {
        char *s = line; while (*s == ' ' || *s == '\t') s++;
        char *e = strpbrk(s, "#\r\n"); if (e) *e = 0;
        e = s + strlen(s); while (e > s && (e[-1] == ' ' || e[-1] == '\t')) *--e = 0;
        if (!*s) continue;
        if (!_stricmp(s, "off")) { fclose(f); anp_log("cutdiag: off (ANP_cutdiag.txt)"); return; }
        char *d = s; while (*d >= '0' && *d <= '9') d++;
        g_cdIdx[g_cdNN] = (!*d && d - s < 8) ? atol(s) : -1;     /* all digits: a node index */
        _snprintf(g_cdNames[g_cdNN++], 64, "%s", s);
    }
    fclose(f);
    if (!g_cdNN) {
        static const char *def[] = {"010_CUT_Transport", "010_IntroCutScene_01", "CUT_BreakNose", "010_EscapeCut"};
        for (int i = 0; i < 4; i++) { g_cdIdx[g_cdNN] = -1; _snprintf(g_cdNames[g_cdNN++], 64, "%s", def[i]); }
    }
    g_cdOn = 1;
    char b[1100]; int k = 0;
    for (int i = 0; i < g_cdNN && k < 1000; i++) k += _snprintf(b + k, sizeof b - k, " '%s'", g_cdNames[i]);
    anp_log("cutdiag: on, tracking%s", b);
}

/* ---- G and M lines */
static void cd_global(DWORD now, DWORD ts) {
    DWORD gm = cd32(0xdd265c), app = cd32(0xdd2640), ses = cd32(0x168e598);
    int nmon = (int)cd32(0x168a254);
    DWORD st = gm ? gm + 0x3e3c : 0, cur = cd32(0xe0e640);
    char curs[24]; if (st && cur == st) strcpy(curs, "INGAME"); else _snprintf(curs, sizeof curs, "%08lx", cur);
    BYTE f0 = cd8(0x168a200), f1 = cd8(0x168a201), f2 = cd8(0x168a202);
    char g[700];
    _snprintf(g, sizeof g, "mon n=%d fired=%d%d%d def=%d x20c=%lu | pend48ac=%08lx a68=%d a69=%d a6a=%d a6c=%ld cur=%s n644=%lu | "
              "b44=%lu | ses 54=%lu 5c=%lu 70=%lu 1b4=%lu | p828=%08lx p82c=%08lx buddy=%08lx | mcrun=%ld 5e1=%d",
              nmon, f0, f1, f2, cd8(0x168a206), cd32(0x168a20c), cd32(gm + 0x48ac), cd8(st + 0xa68), cd8(st + 0xa69), cd8(st + 0xa6a),
              (long)cd32(st + 0xa6c), curs, cd32(0xe0e644), cd32(app + 0xb44), cd32(ses + 0x54), cd32(ses + 0x5c), cd32(ses + 0x70),
              cd32(ses + 0x1b4), cd32(gm + 0x828), cd32(gm + 0x82c), cd32(gm + 0x4cf0), (long)cd32(0x168dcc8), cd8(0x156b5e1));
    if (f2 && !g_cdFired2At) { g_cdFired2At = ts ? ts : 1; cd_vlog("t=%lu AIMonitor level-start list FIRED (fire(2))", ts); }
    if (st && cur == st && !g_cdInGameAt) { g_cdInGameAt = ts ? ts : 1; cd_vlog("t=%lu InGame state (gameMgr+0x3e3c) seen in 0xe0e640", ts); }
    if (strcmp(g, g_cdG) || now - g_cdBeat > 10000) { strcpy(g_cdG, g); g_cdBeat = now; cd_vlog("t=%lu G %s", ts, g); }
    char m[700]; int k = 0; m[0] = 0;
    for (int i = 0; i < nmon && i < 8 && k < 600; i++) {
        DWORD mo = cd32(0x168a258 + 4 * i), ow = cd32(mo + 0x24), nd = cd32(ow + 4);
        char nm[64]; cd_node_name(nd, nm, sizeof nm);
        k += _snprintf(m + k, sizeof m - k, " [%d] %08lx vt=%08lx%s owner n%ld '%s' l50=%08lx l54=%08lx l58=%08lx", i, mo, cd32(mo),
                       cd32(mo) == CD_AIMON_VT ? "" : "(!)", cd_node_idx(nd), nm, cd32(mo + 0x50), cd32(mo + 0x54), cd32(mo + 0x58));
    }
    if (strcmp(m, g_cdM)) { strcpy(g_cdM, m); cd_vlog("t=%lu M%s", ts, m[0] ? m : " (none registered)"); }
}

/* ---- heap census of ZMiniCutsceneRout objects (incremental, a few MB per tick) */
static WORD cd_rstate(DWORD r) {
    DWORD mc = cd32(r + 0x58);
    WORD s = (WORD)(cd8(r + 0x40) | cd8(r + 0x41) << 1);
    if (mc && cd32(mc) == CD_MC_VT) s |= (WORD)(4 | cd8(mc + 0x34) << 3 | cd8(mc + 0x35) << 4 | (cd32(mc + 8) & 0xff) << 8);
    return s;
}
static void cd_census_done(DWORD ts) {
    int nmc = 0, n34 = 0, n35 = 0, n40 = 0, k = 0;
    char dead[1800]; dead[0] = 0;
    for (int i = 0; i < g_cdNR; i++) {
        WORD s = g_cdRs[i] = cd_rstate(g_cdR[i]);
        if (s & 4) nmc++;
        if (s & 1) n40++;
        if (s & 8) n34++;
        if (s & 16) n35++;
        if ((s & 24) && k < 1700) {
            char nm[64]; cd_node_name(cd32(cd32(g_cdR[i] + 0x24) + 4), nm, sizeof nm);
            k += _snprintf(dead + k, sizeof dead - k, " %s%s'%s'", s & 8 ? "34" : "", s & 16 ? "35" : "", nm);
        }
    }
    cd_vlog("t=%lu CENSUS %d ZMiniCutsceneRout in this scene: %d with a ZMiniCutscene, %d started (b40), %d dead +34, %d dead +35",
            ts, g_cdNR, nmc, n40, n34, n35);
    if (dead[0]) cd_vlog("t=%lu CENSUS dead:%s", ts, dead);
    /* tracked routs by owner node name */
    for (int j = 0; j < g_cdNN; j++) {
        int found = 0;
        for (int i = 0; i < g_cdNR && g_cdNT < CD_MAXT; i++) {
            DWORD nd = cd32(cd32(g_cdR[i] + 0x24) + 4); char nm[64]; cd_node_name(nd, nm, sizeof nm);
            if (g_cdIdx[j] >= 0 ? cd_node_idx(nd) != g_cdIdx[j] : strcmp(nm, g_cdNames[j]) != 0) continue;
            g_cdT[g_cdNT].rout = g_cdR[i]; g_cdT[g_cdNT].node = cd_node_idx(nd); _snprintf(g_cdT[g_cdNT].name, 64, "%s", nm);
            g_cdT[g_cdNT].last[0] = g_cdT[g_cdNT].lastS[0] = g_cdT[g_cdNT].lastK[0] = 0; g_cdT[g_cdNT].disc = 0;
            g_cdNT++; found++;
        }
        if (!found) cd_vlog("t=%lu tracked '%s': no ZMiniCutsceneRout owned by a node of that %s", ts, g_cdNames[j], g_cdIdx[j] >= 0 ? "index" : "name");
    }
}
static void cd_scan_step(DWORD ts) {
    DWORD budget = 96u << 20, done = 0;
    MEMORY_BASIC_INFORMATION mi;
    while (done < budget) {
        if (g_cdScan >= 0xfffe0000u || !VirtualQuery((void*)g_cdScan, &mi, sizeof mi)) { g_cdScanDone = 1; break; }
        DWORD rb = (DWORD)mi.BaseAddress, re = rb + (DWORD)mi.RegionSize;
        if (re <= g_cdScan) { g_cdScanDone = 1; break; }
        if (mi.State == MEM_COMMIT && mi.Type == MEM_PRIVATE && (mi.Protect & 0xff) == PAGE_READWRITE && !(mi.Protect & PAGE_GUARD)) {
            DWORD a = (g_cdScan + 3) & ~3u, e = re;
            if (e - a > budget - done) e = a + (budget - done);
            /* copied through ReadProcessMemory in 64 KB chunks: a region another thread frees meanwhile fails the
               copy instead of faulting the game */
            static DWORD buf[0x4000];
            for (DWORD c = a; c < e; c += sizeof buf) {
                SIZE_T n = e - c < sizeof buf ? e - c : sizeof buf, got = 0;
                if (!ReadProcessMemory(GetCurrentProcess(), (void*)c, buf, n, &got)) continue;
                for (DWORD w = 0; w < got / 4; w++)
                    if (buf[w] == CD_ROUT_VT && g_cdNR < CD_MAXROUT && cd_rout_node(c + 4 * w) >= 0) g_cdR[g_cdNR++] = c + 4 * w;
            }
            done += e - a; g_cdScan = e;
        } else g_cdScan = re;
    }
    if (g_cdScanDone) cd_census_done(ts);
}
static void cd_census_changes(DWORD ts) {
    for (int i = 0; i < g_cdNR; i++) {
        WORD s = cd_rstate(g_cdR[i]);
        if (s == g_cdRs[i]) continue;
        char nm[64]; DWORD nd = cd32(cd32(g_cdR[i] + 0x24) + 4); cd_node_name(nd, nm, sizeof nm);
        cd_vlog("t=%lu C n%ld '%s' b40 %d->%d b41 %d->%d mc34 %d->%d mc35 %d->%d st8 %d->%d", ts, cd_node_idx(nd), nm,
                g_cdRs[i] & 1, s & 1, g_cdRs[i] >> 1 & 1, s >> 1 & 1, g_cdRs[i] >> 3 & 1, s >> 3 & 1, g_cdRs[i] >> 4 & 1, s >> 4 & 1,
                g_cdRs[i] >> 8, s >> 8);
        g_cdRs[i] = s;
    }
}

/* ---- R, S, K, E lines for the tracked routs */
static void cd_track(DWORD ts) {
    DWORD gm = cd32(0xdd265c);
    for (int t = 0; t < g_cdNT; t++) {
        DWORD r = g_cdT[t].rout;
        if (cd_rout_node(r) != g_cdT[t].node) continue;
        DWORD sq = cd32(r + 0x38), mc = cd32(r + 0x58);
        if (mc && cd32(mc) != CD_MC_VT) mc = 0;
        DWORD beh = cd32(sq + 0x154);
        char bs[16]; if (mc && beh == mc) strcpy(bs, "=MC"); else _snprintf(bs, sizeof bs, "%08lx", beh);
        char l[600];
        _snprintf(l, sizeof l, "rout=%08lx b40=%d b41=%d b42=%d b43=%d mode64=%lu squad=%08lx MC=%08lx | mc st8=%lu 34=%d 35=%d lock3e-42=%d%d%d%d%d "
                  "sq4=%08lx t54=%lu | squad bc=%d 8c=%lu 90=%lu beh154=%s c0=%lu 19c=%08lx f4=%lu",
                  r, cd8(r + 0x40), cd8(r + 0x41), cd8(r + 0x42), cd8(r + 0x43), cd32(r + 0x64), sq, mc,
                  cd32(mc + 8), cd8(mc + 0x34), cd8(mc + 0x35), cd8(mc + 0x3e), cd8(mc + 0x3f), cd8(mc + 0x40), cd8(mc + 0x41), cd8(mc + 0x42),
                  cd32(mc + 4), cd32(mc + 0x54), cd8(sq + 0xbc), cd32(sq + 0x8c), cd32(sq + 0x90), bs, cd32(sq + 0xc0), cd32(sq + 0x19c), cd32(sq + 0xf4));
        if (strcmp(l, g_cdT[t].last)) { strcpy(g_cdT[t].last, l); cd_vlog("t=%lu R '%s' n%ld %s", ts, g_cdT[t].name, g_cdT[t].node, l); }
        /* sections */
        char s[1200]; int k = 0; s[0] = 0;
        if (mc) {
            DWORD b = cd32(mc + 0x20), e = cd32(mc + 0x24);
            for (DWORD p = b; p && p < e && p < b + 4 * 12 && k < 1050; p += 4) {
                DWORD sec = cd32(p), vt = cd32(sec);
                if (vt == CD_ACTOR_VT) {
                    char nm[48] = ""; DWORD n0 = cd32(sec + 0x28), n1 = cd32(sec + 0x2c);
                    if (n0 && n1 > n0 && n1 - n0 < 47 && readable((void*)n0, n1 - n0)) { memcpy(nm, (void*)n0, n1 - n0); nm[n1 - n0] = 0; }
                    k += _snprintf(s + k, sizeof s - k, " {Actor id=%ld '%s' act=%08lx mem=%08lx}", (long)cd32(sec + 4), nm, cd32(sec + 0x20), cd32(sec + 0x24));
                } else {
                    const char *rn = rtti_name((void*)sec);
                    k += _snprintf(s + k, sizeof s - k, " {%.40s id=%ld}", rn[0] == '.' ? rn + 4 : rn, (long)cd32(sec + 4));
                }
            }
            DWORD ks = cd32(mc + 0x30);
            if (ks) k += _snprintf(s + k, sizeof s - k, " | Kane30 act=%08lx mem=%08lx (buddy %08lx)", cd32(ks + 0x20), cd32(ks + 0x24), cd32(gm + 0x4cf0));
        }
        if (strcmp(s, g_cdT[t].lastS)) { strcpy(g_cdT[t].lastS, s); cd_vlog("t=%lu S '%s'%s", ts, g_cdT[t].name, s[0] ? s : " (no ZMiniCutscene)"); }
        /* squad members as the binder sees them */
        char m[900]; int q = 0; m[0] = 0;
        DWORD n = cd32(sq + 0xc0);
        for (DWORD i = 0; sq && i < n && i < 12 && q < 820; i++) {
            DWORD mem = cd32(sq + 0xc4 + 4 * i), act = cd32(mem + 0x40), ctl = cd32(act + 0x77c), an = cd32(act + 4);
            char pn[48]; cd_node_name(cd32(an + 0x50), pn, sizeof pn);
            q += _snprintf(m + q, sizeof m - q, " [%lu] act=%08lx n%ld merc=%ld parent='%s'", i, act, cd_node_idx(an), ctl ? (long)cd32(ctl + 0x6e8) : -1L, pn);
        }
        if (strcmp(m, g_cdT[t].lastK)) { strcpy(g_cdT[t].lastK, m); cd_vlog("t=%lu K '%s' members %lu:%s", ts, g_cdT[t].name, n, m[0] ? m : " -"); }
        /* event storage discovery: owner geom fields that point at the rout, directly or one array/object deeper */
        if (!g_cdT[t].disc) {
            g_cdT[t].disc = 1;
            DWORD ow = cd32(r + 0x24); char e[400]; int z = 0; e[0] = 0;
            for (DWORD o = 0; o < 0x100 && z < 360; o += 4) {
                DWORD p = cd32(ow + o);
                if (p == r) { z += _snprintf(e + z, sizeof e - z, " geom+%lx=rout", o); continue; }
                if (p < 0x10000 || !readable((void*)p, 0x40)) continue;
                for (DWORD o2 = 0; o2 < 0x40; o2 += 4) if (*(DWORD*)(p + o2) == r) z += _snprintf(e + z, sizeof e - z, " [geom+%lx]+%lx=rout", o, o2);
            }
            cd_vlog("t=%lu E '%s' owner geom %08lx (%s):%s", ts, g_cdT[t].name, ow, rtti_name((void*)ow), e[0] ? e : " no pointer within geom+0..0x100 (depth 2)");
        }
    }
}

static void cutdiag_tick(DWORD now) {
    if (g_cdOn < 0) cutdiag_init();
    if (!g_cdOn) return;
    /* Enter / Space / Escape presses (every tick, before the throttle). kl2 binds SkipCutSeq and SkipGeneric to
       tap(kb,return) (input map strings at 0x71528a, 0x750459): an Enter during an intro skips its cut sequence. */
    static const int vk[3] = {VK_RETURN, VK_SPACE, VK_ESCAPE}; static const char *vkn[3] = {"Enter", "Space", "Escape"};
    static int down[3];
    for (int i = 0; i < 3; i++) {
        int d = (GetAsyncKeyState(vk[i]) & 0x8000) != 0;
        if (d && !down[i]) cd_vlog("t=%lu key %s down (cutscene skip binding)", g_cdT0 ? now - g_cdT0 : 0, vkn[i]);
        down[i] = d;
    }
    if (now - g_cdLast < 250) return;
    g_cdLast = now;
    DWORD stride, cap; BYTE *base;
    if (!node_table(&stride, &cap, &base)) return;
    static DWORD lastGm; static char lastScene[8];
    DWORD gm = cd32(0xdd265c);
    if ((DWORD)base != g_cdBase || cap != g_cdCap || stride != g_cdStride || gm != lastGm || strcmp(lastScene, g_cscene)) {
        lastGm = gm; _snprintf(lastScene, sizeof lastScene, "%s", g_cscene);
        g_cdBase = (DWORD)base; g_cdCap = cap; g_cdStride = stride; g_cdT0 = now;
        g_cdScan = 0x10000; g_cdScanDone = 0; g_cdNR = 0; g_cdNT = 0; g_cdG[0] = g_cdM[0] = 0; g_cdFired2At = g_cdInGameAt = 0;
        cd_vlog("scene '%s': node table %08lx cap %lu stride %lu gameMgr %08lx (state reset)", g_cscene, g_cdBase, cap, stride, gm);
    }
    DWORD ts = now - g_cdT0;
    cd_global(now, ts);
    if (!g_cdScanDone) { if (ts > 4000) cd_scan_step(ts); return; }
    cd_census_changes(ts);
    cd_track(ts);
}
