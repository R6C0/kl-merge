/*
 * klunstick.c - [Unstick]: a safety net for a player who is stuck INSIDE an object in cover (or in geometry).
 * Part of KLHook (included by klhook.c after klfreeclimb.c, SHIP and TEST alike). NOT RUN IN THE GAME (2026-10-24, written
 * offline: no live run was allowed).
 *
 * THE REPORT (owner 2026-10-24 16:50): 'sometimes going into cover it puts me inside the object and im stuck for the round'.
 * Offline cause work (tools/kl_cover_restore.py, kl_cover_add2.py: hazard NoCoverBox markers put back, doubtful extra cover
 * boxes switched off) removes the known sources, but a cover box can still be wrong on a map nobody has played. This part
 * is the net under it: the player is put back to the last place he walked to freely.
 *
 * WHAT IT DOES (local human only, offline only - [Net] OnlineSafe: a teleport is a position update peers see):
 *   RECORD  every 0.4 s while the player is in plain locomotion (movement id 2 / 3, no action running) and has moved at
 *           least 25 from the last record, his feet place is kept in a ring of 16 (about the last 6 s of walking).
 *   DETECT  a) AUTO COVER: movement id 8 (cover; klcam.c's klcam_sc: [P+0xdd0] vt 0xbb5b6c, id [+0x44] == 8) AND a movement key
 *              (W A S D) or the forward axis [P+0xb94] held, and the feet have not left a 15-unit circle, for CoverMs (4000).
 *           b) AUTO PLAIN (off unless Plain=1): the same in plain locomotion for PlainMs (6000) - a player pushing at a wall.
 *           c) KEY: Key (F7, 0x76) pressed with the game in front: at once, whatever the state.
 *   ACT     the newest record at least 20 from where he is: when in cover and [P+0x2810] is set the stock 'leave cover' prep
 *           0x5fcb80 (what klfreeclimb.c calls first; GUESS that it also ends the cover movement) and then the unforced placement
 *           0x82cc40 (rot, pos + 10 up, resetVel 1, force 0, net 0) with his own rotation. The records newer than the one used
 *           are dropped; a 3 s cooldown. Every step is a 'unstick:' line. Dry=1: lines only.
 * GUESSES (nothing here is read from the exe beyond what klfreeclimb.c / klcam.c already use): the 15 / 4 s numbers; that
 * movement 2/3 is 'free'; that the stock leave-cover prep ends the cover movement; that PlaceAt at 0x82cc40 is safe from
 * cover. All of it runs under klfc_guard (a fault is logged, the part switches itself off).
 *
 * KLHook.ini
 *   [Unstick]
 *   Enable=1     1 = on (default ON; 0 = nothing)
 *   Auto=1       0 = only the key
 *   Plain=0      1 = the auto test also in plain locomotion
 *   CoverMs=4000 how long a held movement key in cover with no move counts as stuck (1500 .. 30000)
 *   PlainMs=6000 the same for plain locomotion (3000 .. 60000)
 *   Key=0x76     virtual key of the manual put-back (F7); 0 = none
 *   Dry=0        1 = log only
 *   Log=1        0 = only start-up and faults
 */
#ifndef KLUNSTICK_C
#define KLUNSTICK_C

#define KUS_N 16

static struct { int on, autoOn, plain, coverMs, plainMs, key, dry, log; } kus;
static struct { float p[3]; } kus_ring[KUS_N];
static int kus_cnt;                           /* records in the ring, newest = kus_ring[(kus_cnt - 1) % KUS_N] by absolute index */
static int kus_abs;                           /* absolute number of the records ever made (the ring slot is kus_abs % KUS_N) */
static DWORD kus_P, kus_sampT, kus_since, kus_cool, kus_prevKey;
static float kus_samp[3], kus_anchor[3];
static int kus_anch, kus_lastT = -0x7fffffff, kus_dead;
static SHORT (WINAPI *kus_aks)(int);
static HWND (WINAPI *kus_fgw)(void);
static DWORD (WINAPI *kus_wtp)(HWND, LPDWORD);

static int kus_front(void)
{
    DWORD pid = 0; HWND h = kus_fgw ? kus_fgw() : 0;
    if (h && kus_wtp) kus_wtp(h, &pid);
    return h && pid == GetCurrentProcessId();
}

static float kus_d3(const float *a, const float *b) { float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2]; return (float)sqrt(x * x + y * y + z * z); }

static int kus_put_back(DWORD P, int id, const float *here, const float *M, const char *why)
{   /* -> 1 done, 0 nothing to go back to. Under klfc_guard. */
    int i, j = -1; float to[3];
    for (i = kus_abs - 1; i >= 0 && i > kus_abs - 1 - KUS_N && i > kus_abs - 1 - kus_cnt; i--)
        if (kus_d3(kus_ring[i % KUS_N].p, here) >= 20.0f) { j = i; break; }
    if (j < 0) { klog("unstick: %s: stuck at (%.0f,%.0f,%.0f) movement %d but no place to go back to yet (%d record(s))", why, here[0], here[1], here[2], id, kus_cnt); return 0; }
    to[0] = kus_ring[j % KUS_N].p[0]; to[1] = kus_ring[j % KUS_N].p[1] + 10.0f; to[2] = kus_ring[j % KUS_N].p[2];
    klog("unstick: %s: stuck at (%.0f,%.0f,%.0f) movement %d -> back to (%.0f,%.0f,%.0f), %.0f away, record %d of %d%s", why, here[0], here[1], here[2], id,
         to[0], to[1], to[2], kus_d3(to, here), kus_abs - j, kus_cnt, kus.dry ? " - DRY RUN, nothing moved" : "");
    if (kus.dry) return 1;
    if (id == 8 && klh_rd32(P + 0x2810)) KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_LEAVECOVER)(P, 0);      /* GUESS: ends the cover movement */
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, const float *, const float *, int, int, int), KLFC_TELE)(P, 0, M, to, 1, 0, 0);
    kus_cnt -= kus_abs - j;                                            /* the records newer than the one used are gone (the used one too: he stands on it; it is made again) */
    if (kus_cnt < 0) kus_cnt = 0;
    kus_abs = j;
    return 1;
}

static int kus_tick_body(void *unused)
{
    DWORD gd, sys, P, now; signed char pi = -1; int T, id, held = 0, k, front, key = 0, trigger = 0, ms; BYTE b = 0; float Pf[3], M[9], fwd = 0;
    const char *why = 0;
    (void)unused;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(sys = klfc_sys())) return 0;
    if (!klh_rd(gd + 0x898, &pi, 1) || pi < 0 || pi > 7) return 0;
    if (!(P = klh_rd32(gd + 0x828 + 4 * pi)) || klh_pvt(P) != KLFC_PLAYER_VT || !klfc_ok(P, 0x2e00)) return 0;
    T = (int)klh_rd32(sys + 0x48);
    if (T == kus_lastT) return 0;                                       /* paused */
    kus_lastT = T;
    if (P != kus_P) { kus_P = P; kus_cnt = kus_abs = 0; kus_anch = 0; kus_sampT = 0; kus_since = 0; }
    if (!klh_rd(P + 0x2720, &b, 1) || !(b & 2)) return 0;               /* not the local human */
    if (klh_rd32(P + 0xd50) || klh_rd32(P + 0xd44)) { kus_anch = 0; return 0; }     /* seat / carrier */
    if (!klfc_pose(P, M, Pf)) return 0;
    id = klfc_movid(P);
    now = GetTickCount();
    front = kus_front();
    /* RECORD */
    if ((id == 2 || id == 3) && !klfc_cur_act(P) && now - kus_sampT >= 400) {
        if (!kus_sampT || kus_abs == 0 || kus_d3(kus_samp, Pf) >= 25.0f) {
            memcpy(kus_ring[kus_abs % KUS_N].p, Pf, 12); kus_abs++; if (kus_cnt < KUS_N) kus_cnt++;
            memcpy(kus_samp, Pf, 12);
        }
        kus_sampT = now;
    }
    /* DETECT */
    if (front && kus_aks) {
        for (k = 0; k < 4; k++) if (kus_aks("WASD"[k]) & 0x8000) held = 1;
        if (kus.key) { key = (kus_aks(kus.key) & 0x8000) != 0; if (key && !kus_prevKey) trigger = 2; kus_prevKey = key; }
    }
    klh_rd(P + 0xb94, &fwd, 4);
    if (fwd > 0.5f || fwd < -0.5f) held = 1;
    ms = id == 8 ? kus.coverMs : (kus.plain && (id == 2 || id == 3) ? kus.plainMs : 0);
    if (!ms || !held || !kus.autoOn) kus_anch = 0;
    else if (!kus_anch || kus_d3(kus_anchor, Pf) >= 15.0f) { memcpy(kus_anchor, Pf, 12); kus_since = now; kus_anch = 1; }
    else if (now - kus_since >= (DWORD)ms) { trigger = 1; }
    if (!trigger) return 0;
    if (now < kus_cool) return 0;
    why = trigger == 2 ? "key" : id == 8 ? "auto, cover" : "auto, plain";
    kus_cool = now + 3000; kus_anch = 0;
    kus_put_back(P, id, Pf, M, why);
    return 0;
}

static void kus_tick(int game_thread)
{
    if (!kus.on || kus_dead || !game_thread || !klh_exe_ok) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;          /* the gameplay call of the main loop only */
    if (kl_online()) return;                                           /* [Net] OnlineSafe */
    if (klfc_guard("unstick", kus_tick_body, 0) < 0) { kus_dead = 1; klog("unstick: DISABLED for this session (fault) - restart the game before testing again"); }
}

static void kus_init(void)
{
    HMODULE u;
    memset(&kus, 0, sizeof kus);
    kus.on = GetPrivateProfileIntA("Unstick", "Enable", 1, klh_ini) != 0;
    if (!kus.on) return;
    kus.autoOn = GetPrivateProfileIntA("Unstick", "Auto", 1, klh_ini) != 0;
    kus.plain = GetPrivateProfileIntA("Unstick", "Plain", 0, klh_ini) != 0;
    kus.coverMs = (int)GetPrivateProfileIntA("Unstick", "CoverMs", 4000, klh_ini); if (kus.coverMs < 1500) kus.coverMs = 1500; if (kus.coverMs > 30000) kus.coverMs = 30000;
    kus.plainMs = (int)GetPrivateProfileIntA("Unstick", "PlainMs", 6000, klh_ini); if (kus.plainMs < 3000) kus.plainMs = 3000; if (kus.plainMs > 60000) kus.plainMs = 60000;
    kus.key = (int)GetPrivateProfileIntA("Unstick", "Key", 0x76, klh_ini) & 0xff;
    kus.dry = GetPrivateProfileIntA("Unstick", "Dry", 0, klh_ini) != 0;
    kus.log = (int)GetPrivateProfileIntA("Unstick", "Log", 1, klh_ini);
    u = GetModuleHandleA("user32.dll"); if (!u) u = LoadLibraryA("user32.dll");
    if (u) {
        kus_aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState");
        kus_fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
        kus_wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
    }
    if (!kus_aks || !kus_fgw || !kus_wtp) { kus.on = 0; klog("unstick: user32's key functions not found: OFF"); return; }
    klog("unstick: on; Auto=%d Plain=%d CoverMs=%d PlainMs=%d Key=0x%02x Dry=%d; a player held still in cover (or, with Plain, in plain walking) with a movement key down is put back to the last place he walked to freely; the key does it at once (offline only)",
         kus.autoOn, kus.plain, kus.coverMs, kus.plainMs, kus.key, kus.dry);
}

#endif
