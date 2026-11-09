/* godmode.inc: TEST-ONLY player god mode for unattended runs (scripts\smoke_*.py), so an idle player is not killed
   by the police while a test waits. Included by anp_loader.c after cutdiag.inc (uses anp_log, readable, g_dir);
   ticked from my_PeekMessageA on the main thread. No kl2 code byte is changed: the switch is a .data (bss) global
   and optional heap writes, none of them in the CEG-hashed ranges.

   Opt-in: while <DD>\ANP_god.txt exists god mode is on; delete the file to turn it off (polled once a second, the
   file's tokens are re-read when it changes). Tokens (space/line separated, all optional):
     1        default: no damage. kl2's own dormant god-mode switch, ZPlayer::SetGodMode (vtable slot 0x5a4,
              0x53bd10) writes the global 0x1535a2c; nothing in the shipped game calls it. Readers:
                0x6e3400 ZFFPlayer::AdjustHitPoints (damage): 0 or 2 -> apply the damage (0x8a7c60), else skip it;
                         2 -> if HP <= 0 afterwards, HP = 0.01 (0xbb01b4)
                0x596030, 0x69fa40 (instant-kill paths, HP := 0): skipped when != 0
                0x458ce9, 0x8da3df: skipped when == 1;  0x459000: runs only for 0 or 2;  0x82302c: skipped when != 0
                0x8fa070 = ZPlayer::IsGodMode (slot 0x5a0)
     2        cannot die: damage, hit reactions and the HUD still happen, HP never drops below 0.01
     heal     also refill HP to max every 100 ms (heap: player+0xa48 -> HP block: +4 current, +8 max, +0x24 owner)
     mask     also set a loader-owned bit (0x4000) in the player's invulnerability mask, WORD at [player+0x54]+0x3a.
              Non-zero = invulnerable: the same mask the engine uses for MiniCutscene 'unbreakable' (bit 2),
              the squad modifier Invulnerable (bit 1, 0x5e0070 via 0x6f4890) and the 'GodActors' ini var
              (bit 1, NPCs only); the hit path 0x6e2cb1 skips the hit when it is non-zero. Removed on 'off'.
     off      same as deleting the file
     log      log every change of the player's HP: "god: hit cur->new (delta) max m" for each drop, "god: regen a->b"
              for a run of increases (flushed on the next drop, at max, or after 1 s without change). With 'log'
              and no '1'/'2' token god mode stays OFF (heal/mask ignored): a diagnostic for normal play. With
              '1'/'2' as well, god mode is on and the changes are logged too. The HP is sampled every ~10 ms on the
              main thread, so hits in the same frame are summed into one line. The attacker/weapon is not known
              here (no CEG-safe hook on the hit path; a ZFFPlayer vptr swap was judged too risky for normal play).
   Lines start with "god:". Logged: on/off (with the mode), and while on, every 5 s (30 s in log-only mode)
   "god: hp cur/max var=<global> mask=<word>"; also any HP drop of more than 0.5 (none is expected in mode 1).
   The first line for each player object also gives kl2's difficulty global 0x156b5f0 (written at 0x472d50;
   0..3 = Easy..Extreme; the story max HP is 100 x 11 / 5 / 2.25 / 0.85).
   Not done: making the player untargeted. kl2's SquadModifier SetVisibility (0x7e7d30 -> 0x5686f0) only covers NPC
   squad members; no player-side flag was found. */

#define GOD_VAR        0x1535a2c   /* .data (bss), 0 at start: 0 off, 1 no damage, 2 cannot die */
#define GOD_PLAYER_VT  0xbb45f4    /* ZFFPlayer */
#define GOD_MASK_BIT   0x4000

static int g_godState = -1;          /* -1 not checked yet, 0 unusable (build mismatch), 1 usable */
static int g_godPresent = -1, g_godOn, g_godMode = 1, g_godHeal, g_godMask;
static FILETIME g_godTime;
static DWORD g_godPoll, g_godPlayerT, g_godBeat, g_godPrev;
static BYTE *g_godMaskObj;           /* where our mask bit was set */
static BYTE *g_godLastP; static float g_godLastHp = -1.0f;
static int g_godLog, g_godLogOnly;   /* 'log' token; log without a '1'/'2' token = god mode off, logging only */
static float g_godRiseFrom = -1.0f; static DWORD g_godRiseT;
#define GOD_DIFF_VAR   0x156b5f0     /* kl2 difficulty global (.data), read only */
static long god_difficulty(void) { return readable((void*)GOD_DIFF_VAR, 4) ? (long)*(DWORD*)GOD_DIFF_VAR : -1; }

static int god_writable(const void *p, size_t n) {
    MEMORY_BASIC_INFORMATION mi;
    if (!readable(p, n) || !VirtualQuery(p, &mi, sizeof mi)) return 0;
    if ((const BYTE*)p + n > (const BYTE*)mi.BaseAddress + mi.RegionSize) return 0;
    return (mi.Protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_WRITECOPY)) != 0;
}

/* this kl2 build: SetGodMode and AdjustHitPoints must use GOD_VAR (read-only check of code bytes) */
static int god_check_build(void) {
    static const BYTE setgod[13] = {0x0f, 0xb6, 0x44, 0x24, 0x04, 0xa3, 0x2c, 0x5a, 0x53, 0x01, 0xc2, 0x04, 0x00};
    static const BYTE adjust[5] = {0xa1, 0x2c, 0x5a, 0x53, 0x01};
    if (!readable((void*)0x53bd10, sizeof setgod) || memcmp((void*)0x53bd10, setgod, sizeof setgod)) return 0;
    if (!readable((void*)0x6e35fc, sizeof adjust) || memcmp((void*)0x6e35fc, adjust, sizeof adjust)) return 0;
    return god_writable((void*)GOD_VAR, 4);
}

/* the local ZFFPlayer, or 0 (same lookup as climb.inc: gameMgr 0xdd265c, +0x898 local index, +0x828 players) */
static BYTE *god_player(void) {
    BYTE *gm = readable((void*)0xdd265c, 4) ? *(BYTE**)0xdd265c : 0;
    if (!readable(gm + 0x828, 0x74)) return 0;
    signed char pi = *(signed char*)(gm + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gm + 0x828 + 4 * pi);
    if (!readable(P, 0xa4c) || *(DWORD*)P != GOD_PLAYER_VT) return 0;
    return P;
}
static BYTE *god_hp(BYTE *P) {        /* HP block (0x28 bytes, ctor 0x4aad80) whose owner +0x24 is P */
    BYTE *h = *(BYTE**)(P + 0xa48);
    return (readable(h, 0x28) && *(BYTE**)(h + 0x24) == P) ? h : 0;
}
static BYTE *god_maskobj(BYTE *P) {
    BYTE *o = *(BYTE**)(P + 0x54);
    return god_writable(o + 0x3a, 2) ? o : 0;
}
static void god_mask_clear(void) {
    if (g_godMaskObj && god_writable(g_godMaskObj + 0x3a, 2)) *(WORD*)(g_godMaskObj + 0x3a) &= (WORD)~GOD_MASK_BIT;
    g_godMaskObj = 0;
}

static void god_poll_file(DWORD now) {
    if (g_godPresent >= 0 && now - g_godPoll < 1000) return;
    g_godPoll = now;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_god.txt", g_dir);
    WIN32_FILE_ATTRIBUTE_DATA fa;
    int present = GetFileAttributesExA(fn, GetFileExInfoStandard, &fa) ? 1 : 0;
    if (present == g_godPresent && (!present || CompareFileTime(&fa.ftLastWriteTime, &g_godTime) == 0)) return;
    g_godPresent = present;
    int on = present, mode = 1, heal = 0, mask = 0, lg = 0, modeTok = 0;
    if (present) {
        g_godTime = fa.ftLastWriteTime;
        char buf[256] = "";
        FILE *f = fopen(fn, "r");
        if (f) { size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f); }
        for (char *t = strtok(buf, " \t\r\n,;"); t; t = strtok(NULL, " \t\r\n,;")) {
            if (!strcmp(t, "1") || !strcmp(t, "2")) { mode = t[0] - '0'; modeTok = 1; }
            else if (!_stricmp(t, "heal")) heal = 1;
            else if (!_stricmp(t, "mask")) mask = 1;
            else if (!_stricmp(t, "log")) lg = 1;
            else if (!_stricmp(t, "off") || !strcmp(t, "0")) on = 0;
            else anp_log("god: token '%s' ignored", t);
        }
    }
    int logonly = on && lg && !modeTok;
    if (!on || logonly) {
        if (g_godOn && !g_godLogOnly) {      /* god mode was really on: undo it */
            if (*(DWORD*)GOD_VAR == (DWORD)g_godMode) *(DWORD*)GOD_VAR = g_godPrev;
            god_mask_clear();
            anp_log("god: off (%s) var=%lu", !present ? "ANP_god.txt removed" : logonly ? "log only" : "ANP_god.txt says off",
                    *(DWORD*)GOD_VAR);
        } else if (g_godOn && !on) anp_log("god: hp logging off");
    }
    if (!on) { g_godOn = 0; g_godLog = g_godLogOnly = 0; return; }
    g_godBeat = 0; g_godLastHp = -1.0f; g_godRiseFrom = -1.0f; g_godLastP = 0;
    if (logonly) {
        g_godOn = 1; g_godLogOnly = 1; g_godLog = 1; g_godHeal = 0; g_godMask = 0;
        anp_log("god: log only - god mode OFF, every player HP change is logged (var=%lu difficulty=%ld)%s",
                *(DWORD*)GOD_VAR, god_difficulty(), (heal || mask) ? " (heal/mask ignored without 1/2)" : "");
        return;
    }
    if (!g_godOn || g_godLogOnly) g_godPrev = *(DWORD*)GOD_VAR;
    if (g_godOn && g_godMask && !mask) god_mask_clear();
    g_godOn = 1; g_godLogOnly = 0; g_godLog = lg; g_godMode = mode; g_godHeal = heal; g_godMask = mask;
    anp_log("god: on mode=%d (%s) heal=%d mask=%d log=%d (was var=%lu)", mode, mode == 1 ? "no damage" : "cannot die",
            heal, mask, lg, g_godPrev);
}

static void godmode_tick(DWORD now) {
    if (g_godState < 0) {
        g_godState = god_check_build();
        if (!g_godState) {      /* log only if someone asked for it */
            char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_god.txt", g_dir);
            if (GetFileAttributesA(fn) != INVALID_FILE_ATTRIBUTES)
                anp_log("god: kl2 build mismatch (0x53bd10 / 0x6e35fc / 0x%x) - god mode unavailable", GOD_VAR);
        }
    }
    if (!g_godState) return;
    god_poll_file(now);
    if (!g_godOn) return;
    if (!g_godLogOnly) {
        DWORD v = *(DWORD*)GOD_VAR;
        if (v != (DWORD)g_godMode) {
            if (v != g_godPrev) anp_log("god: var was changed to %lu by the game, re-set to %d", v, g_godMode);
            *(DWORD*)GOD_VAR = (DWORD)g_godMode;
        }
    }
    if (now - g_godPlayerT < (g_godLog ? 10u : 100u)) return;
    g_godPlayerT = now;
    BYTE *P = god_player();
    if (!P) {                                                    /* level change: the object is gone */
        if (g_godRiseFrom >= 0.0f) { anp_log("god: regen %.2f -> %.2f (player gone)", g_godRiseFrom, g_godLastHp); g_godRiseFrom = -1.0f; }
        if (g_godMaskObj) g_godMaskObj = 0;
        g_godLastP = 0; return;
    }
    BYTE *h = god_hp(P);
    if (g_godMask) {
        BYTE *o = god_maskobj(P);
        if (o != g_godMaskObj) { if (g_godMaskObj && P == g_godLastP) god_mask_clear(); g_godMaskObj = o; }
        if (o && !(*(WORD*)(o + 0x3a) & GOD_MASK_BIT)) *(WORD*)(o + 0x3a) |= GOD_MASK_BIT;
    }
    if (!h) return;
    float cur = *(float*)(h + 4), mx = *(float*)(h + 8);
    if (P != g_godLastP) {
        g_godLastP = P; g_godLastHp = -1.0f; g_godRiseFrom = -1.0f;
        anp_log("god: player %p hp block %p hp %.2f/%.2f difficulty=%ld", P, h, cur, mx, god_difficulty());
    }
    if (g_godLog && g_godLastHp >= 0.0f) {
        float d = cur - g_godLastHp;
        if (d < -0.001f) {
            if (g_godRiseFrom >= 0.0f) { anp_log("god: regen %.2f -> %.2f", g_godRiseFrom, g_godLastHp); g_godRiseFrom = -1.0f; }
            anp_log("god: hit %.2f->%.2f (%.2f) max %.2f%s", g_godLastHp, cur, d, mx, cur <= 0.0f ? " DEAD/DOWN" : "");
        } else if (d > 0.001f) {
            if (g_godRiseFrom < 0.0f) g_godRiseFrom = g_godLastHp;
            g_godRiseT = now;
        }
        if (g_godRiseFrom >= 0.0f && (cur >= mx || now - g_godRiseT >= 1000)) {
            anp_log("god: regen %.2f -> %.2f (max %.2f)", g_godRiseFrom, cur, mx); g_godRiseFrom = -1.0f;
        }
    } else if (g_godLastHp >= 0.0f && cur < g_godLastHp - 0.5f) anp_log("god: hp dropped %.2f -> %.2f (max %.2f)", g_godLastHp, cur, mx);
    if (g_godHeal && mx > 0.0f && cur < mx && god_writable(h + 4, 4)) *(float*)(h + 4) = cur = mx;
    g_godLastHp = cur;
    if (!g_godBeat || now - g_godBeat >= (g_godLogOnly ? 30000u : 5000u)) {
        g_godBeat = now;
        BYTE *o = god_maskobj(P);
        anp_log("god: hp %.2f/%.2f var=%lu mask=%04x", cur, mx, *(DWORD*)GOD_VAR, o ? *(WORD*)(o + 0x3a) : 0xffff);
    }
}
