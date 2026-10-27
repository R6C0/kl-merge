/*
 * klshoulder.c - a LOG of what holds the camera's shoulder side ([Shoulder] Log=1; default OFF).
 * The owner, 2026-10-10: on Late Night Opening (Dead Men's M02_FA_A) the SWITCH CAMERA SHOULDER key does nothing,
 * on the bank it works. Static reading found no cause in the level (re\shoulder_m02.md); this part makes ONE round
 * with the key pressed a few times name it.
 * Part of KLHook (included by klhook.c after klbalance.c, SHIP and TEST alike). READS ONLY: no write of any kind,
 * no call of a game routine, no patch; every read goes through klh_rd (ReadProcessMemory on the own process), so a
 * stale pointer costs a failed read and nothing else. Any thread. NOTHING HERE HAS RUN IN THE GAME.
 *
 * WHAT IS READ (kl2.exe build 0490; all of it read in the disassembly, re\shoulder_m02.md has the code places)
 *   the local player P = [gamedata + 0x828 + 4 * [gamedata+0x898]], a ZFFPlayer (vtable 0xbb45f4)
 *   want    [P+0x29a0]  the side the player chose: 0 right, 1 left. ONLY the key's handler 0x640080 toggles it.
 *   side    [P+0x818] bit 10 = the side in use (1 left), [P+0x280c] = the same as a byte (what the camera 0x9088c0
 *           and the stance 0x41ad30 read). Written only by the setter 0x74a120.
 *   pend    [P+0xb8c] / [P+0xb88]  a side change waiting for its delay (-1 left, 1 right; seconds)
 *   cover   [P+0xb84]  the side to go back to when a cover is left (-1 left, 1 right, 0 none; 0x44f260, 0x5ea690)
 *   saved   [P+0xa98]  the side put away when the player went down (0 = was left, 1 = was right, 2 = nothing)
 *   THE KEY IS REFUSED (0x640080 returns before the toggle) while
 *     tun     byte [[0x168d7c0]+0x209] == 0      a tuning bool, 1 as built, no writer found
 *     kind    [P+0x2720] bit 1 clear             the player's control kind; 2 = the local human with a camera
 *     2954    byte [P+0x2954] != 0               (re\firstperson_camera.md: aiming; ASSUMPTION, the log shows it)
 *     heli    [P+0xd50] != 0                     set by the message 'HeliSeatAttach' only (0x5c7e5b)
 *     in      [P+0xed0] bit 7                    the input mask; bit 7 is set by a PlayerInputManipulator only
 *     lock    float [H+0x330] > 0                H = the player's ZGameplayInput; set by its 'reset' (0x8180cc)
 *   and nothing happens while the game does not see the key: H+0x30 is the record of 'SwitchCameraSide'
 *   ({action, 2, timer, fired, once}; timer runs down from 0.08 s while the key is held, fired = 1 when it acted).
 *   THE SIDE IS FORCED inside 0x74a120, whatever is asked:
 *     LEFT   while the down-not-dead object D = [P+0x2948] has byte [D+8] bit 0 and [D+4] != 3
 *     RIGHT  while word [P+0xa54] has bit 1 (the player lies down: 0x6fb885 / 0x8b1322 set it), this one last
 *   also printed: st = [P+0xbbc] (state flags), [D+0x30] (the side the down state keeps), police byte [P+0x2723],
 *   the model the player wears ([[P+4]+0x68]) and the level.
 *
 * THE LINES (prefix 'shoulder:'): one every second while a local ZFFPlayer exists, and one at once whenever a
 * watched value changes ('CHANGE name old->new ...' first). Each ends with the hook's own reading of the values:
 *   key free | key REFUSED by <names>        and        side free | side FORCED LEFT | side FORCED RIGHT
 * HOW TO READ ONE ROUND with the key held a few times:
 *   - no 'held 0->1' line at all        the game never saw the key: the binding / the action, nothing of the level
 *   - held, 'fired 0->1', want unchanged the handler refused: the line says by what
 *   - want toggles, side does not       0x74a120 forced it: the line says which way and why
 *   - want and side toggle, then side goes back by itself   another caller of 0x74a120 (cover, the base move)
 *   - want and side toggle and stay     the code did its part: the fault is on the camera's side (0x9088c0, the
 *                                       level object 'CameraTransitionSpline'), or in what the owner sees
 *
 * WIRING (klhook.c; nothing else of the hook changes)
 *   #include "klshoulder.c"      after  #include "klbalance.c"
 *   klo_tick(game_thread);       in klh_tick, after  klr_tick(game_thread);
 *   klo_init();                  in the init list, after  klr_init();
 * KLHook.ini:
 *   [Shoulder]
 *   Log=1
 */
#ifndef KLSHOULDER_C
#define KLSHOULDER_C

#define KLO_GAMEDATA   0x00dd265c             /* +0x828 + 4 * i players, +0x898 the local player's index, +0x1590 the input manager */
#define KLO_TUNING     0x0168d7c0
#define KLO_PLAYER_VT  0x00bb45f4             /* ZFFPlayer */
#define KLO_INPUT_VT0  0x00bb7c74             /* ZGameplayInput */
#define KLO_INPUT_VT1  0x00bb7d0c             /* ZGameplayInputWintel */
#define KLO_MAXCHANGE  30                     /* change lines a second; the rest of that second is counted, not written */

enum { KLO_WANT, KLO_SIDE, KLO_B280C, KLO_PEND, KLO_COVER, KLO_SAVED, KLO_B2954, KLO_HELI, KLO_HELI2, KLO_KIND, KLO_IN,
       KLO_ST80, KLO_TUN, KLO_LOCK, KLO_DSTATE, KLO_DFLAG, KLO_DKEEP, KLO_DOWN, KLO_HAVEH, KLO_HELD, KLO_FIRED, KLO_MODEL,
       KLO_POLICE, KLO_N };
static const char *const klo_name[KLO_N] = { "want", "side", "280c", "pend", "cover", "saved", "2954", "heli", "heli2", "kind", "in",
       "st80", "tun", "lock", "dstate", "dflag", "dkeep", "a54", "input", "held", "fired", "model", "police" };

struct klo_snap {
    long v[KLO_N];                            /* what a change is judged by */
    DWORD player, f818, st, heli, dobj, h, act, bound; WORD a54; float lock, timer, pendt;       /* printed only */
};

static struct { int on; } klo;

static float klo_f(DWORD_PTR at)
{
    float f = 0;
    if (!klh_rd(at, &f, 4) || f != f || f < -1e9f || f > 1e9f) return 0;
    return f;
}

/* The ZGameplayInput whose +8 is this player: the manager [gamedata+0x1590] keeps, for each of four players, four
   pointers at +4 + 20 * i and a 'used' byte at +20 + 20 * i (the game's own lookup 0x61ef90). -> 0 = none. */
static DWORD klo_input(DWORD gd, DWORD pl)
{
    DWORD m, h, vt; BYTE used; int i, k;
    if (!(m = klh_rd32(gd + 0x1590))) return 0;
    for (i = 0; i < 4; i++) {
        used = 0;
        if (!klh_rd(m + 20 + 20 * i, &used, 1) || !used) continue;
        for (k = 0; k < 4; k++) {
            if (!(h = klh_rd32(m + 4 + 20 * i + 4 * k)) || klh_rd32(h + 8) != pl) continue;
            vt = klh_rd32(h);
            if (vt == KLO_INPUT_VT0 || vt == KLO_INPUT_VT1) return h;
        }
    }
    return 0;
}

/* -> 1 when the local player is a ZFFPlayer and its fields could be read */
static int klo_read(struct klo_snap *s)
{
    DWORD gd, pl, node, tun, d, x; BYTE idx = 0xff, b; WORD w;
    memset(s, 0, sizeof *s);
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KLO_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || idx == 0xff || (signed char)idx < 0 || idx > 31) return 0;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * idx)) || klh_pvt(pl) != KLO_PLAYER_VT) return 0;
    if (!klh_rd(pl + 0x818, &s->f818, 4) || !klh_rd(pl + 0x29a0, &x, 4)) return 0;
    s->player = pl;
    s->v[KLO_WANT] = (long)x;
    s->v[KLO_SIDE] = (long)(s->f818 >> 10 & 1);
    b = 0; klh_rd(pl + 0x280c, &b, 1); s->v[KLO_B280C] = b;
    s->v[KLO_PEND] = (long)klh_rd32(pl + 0xb8c); s->pendt = klo_f(pl + 0xb88);
    s->v[KLO_COVER] = (long)klh_rd32(pl + 0xb84);
    s->v[KLO_SAVED] = (long)klh_rd32(pl + 0xa98);
    b = 0; klh_rd(pl + 0x2954, &b, 1); s->v[KLO_B2954] = b;
    s->heli = klh_rd32(pl + 0xd50); s->v[KLO_HELI] = s->heli != 0;
    s->v[KLO_HELI2] = (klh_rd32(pl + 0xd54) | klh_rd32(pl + 0xd58) | klh_rd32(pl + 0xd5c)) != 0;
    b = 0; klh_rd(pl + 0x2720, &b, 1); s->v[KLO_KIND] = b;
    s->v[KLO_IN] = (long)klh_rd32(pl + 0xed0);
    s->st = klh_rd32(pl + 0xbbc); s->v[KLO_ST80] = (long)(s->st >> 7 & 1);
    b = 0xff; if ((tun = klh_rd32((DWORD_PTR)KLH_VA(KLO_TUNING))) != 0) klh_rd(tun + 0x209, &b, 1);
    s->v[KLO_TUN] = b;                                               /* 255 = no tuning object */
    s->v[KLO_DSTATE] = -1;
    if ((d = klh_rd32(pl + 0x2948)) != 0 && klh_rd32(d) == pl) {     /* its first dword is the player (0x57cf90) */
        s->dobj = d;
        s->v[KLO_DSTATE] = (long)klh_rd32(d + 4);
        b = 0; klh_rd(d + 8, &b, 1); s->v[KLO_DFLAG] = b;
        s->v[KLO_DKEEP] = (long)klh_rd32(d + 0x30);
    }
    w = 0; klh_rd(pl + 0xa54, &w, 2); s->a54 = w; s->v[KLO_DOWN] = w & 0x102;          /* the two bits the 'down' code sets; the rest is health */
    if ((s->h = klo_input(gd, pl)) != 0) {
        s->v[KLO_HAVEH] = 1;
        s->lock = klo_f(s->h + 0x330); s->v[KLO_LOCK] = s->lock > 0;
        s->timer = klo_f(s->h + 0x38);
        s->v[KLO_HELD] = s->timer < 0.0795f;                         /* released: 0.08 ([0xbb7c6c]); held: it runs down */
        b = 0; klh_rd(s->h + 0x3c, &b, 1); s->v[KLO_FIRED] = b;
        if ((s->act = klh_rd32(s->h + 0x30)) != 0) s->bound = klh_rd32(s->act + 4);
    }
    if ((node = klh_rd32(pl + 4)) != 0) s->v[KLO_MODEL] = (long)klh_rd32(node + 0x68);
    b = 0; klh_rd(pl + 0x2723, &b, 1); s->v[KLO_POLICE] = b;
    return 1;
}

static void klo_line(const struct klo_snap *s, const char *head)
{
    char scene[160], key[64], why[120], force[80]; const long *v = s->v; int n = 0;
    key[0] = 0;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) strcpy(key, "?");
    why[0] = 0;
    if (v[KLO_TUN] == 0) n += snprintf(why + n, sizeof why - n, " tun");
    if (!(v[KLO_KIND] & 2)) n += snprintf(why + n, sizeof why - n, " kind");
    if (v[KLO_B2954]) n += snprintf(why + n, sizeof why - n, " 2954");
    if (v[KLO_HELI]) n += snprintf(why + n, sizeof why - n, " heli");
    if (v[KLO_IN] & 0x80) n += snprintf(why + n, sizeof why - n, " in.80");
    if (v[KLO_LOCK]) n += snprintf(why + n, sizeof why - n, " lock");
    if (s->a54 & 2) strcpy(force, "side FORCED RIGHT (a54 bit 1: lying down)");
    else if (s->dobj && (v[KLO_DFLAG] & 1) && v[KLO_DSTATE] != 3) strcpy(force, "side FORCED LEFT (down-not-dead: flag bit 0, state not 3)");
    else strcpy(force, "side free");
    klog("shoulder: %s%s model %ld P %08lx%s | want %s side %s (280c %ld, 818 %08lx) pend %ld/%.2f cover %ld saved %ld | 2954 %ld heli %08lx%s kind %02lx in %08lx st %08lx tun %ld lock %.2f | down D %08lx state %ld flag %02lx keep %ld a54 %04x | key held %ld fired %ld timer %.3f action %08lx bound %08lx | %s%s; %s",
         head, key, v[KLO_MODEL], s->player, v[KLO_POLICE] ? " (POLICE)" : "",
         v[KLO_WANT] == 0 ? "R" : v[KLO_WANT] == 1 ? "L" : "?", v[KLO_SIDE] ? "L" : "R", v[KLO_B280C], s->f818, v[KLO_PEND], s->pendt, v[KLO_COVER], v[KLO_SAVED],
         v[KLO_B2954], s->heli, v[KLO_HELI2] ? "+2nd" : "", (unsigned long)v[KLO_KIND], (unsigned long)v[KLO_IN], s->st, v[KLO_TUN], s->lock,
         s->dobj, v[KLO_DSTATE], (unsigned long)v[KLO_DFLAG], v[KLO_DKEEP], (unsigned)s->a54,
         v[KLO_HELD], v[KLO_FIRED], s->timer, s->act, s->bound,
         why[0] ? "key REFUSED by" : v[KLO_HAVEH] ? "key free" : "key free as far as read (NO input object found for this player: lock and key not read)", why, force);
}

static void klo_tick(int game_thread)
{
    static struct klo_snap last; static DWORD lastline, lastpoll, window; static int have, shown, dropped;
    struct klo_snap s; DWORD now; char head[400]; int i, n, changed = 0;
    if (!klo.on || !klh_exe_ok) return;
    now = GetTickCount();
    if (!game_thread && now - lastpoll < 50) return;                 /* the fallback thread ticks while the main loop stands still */
    lastpoll = now;
    if (!klo_read(&s)) {
        if (have) { have = 0; klog("shoulder: no local ZFFPlayer any more (the player object %08lx is gone or of another class)", last.player); }
        return;
    }
    if (!have || s.player != last.player) {
        have = 1; last = s; lastline = now; window = now; shown = dropped = 0;
        klo_line(&s, "NEW PLAYER ");
        return;
    }
    n = snprintf(head, sizeof head, "CHANGE");
    for (i = 0; i < KLO_N; i++) if (s.v[i] != last.v[i]) {
        changed++;
        if (n < (int)sizeof head - 48) n += snprintf(head + n, sizeof head - n, " %s %ld->%ld", klo_name[i], last.v[i], s.v[i]);
    }
    if (now - window >= 1000) {
        if (dropped) klog("shoulder: %d more change(s) in that second were not written", dropped);
        window = now; shown = dropped = 0;
    }
    if (changed) {
        last = s;
        if (shown < KLO_MAXCHANGE) {
            shown++; lastline = now;
            if (n < (int)sizeof head - 4) { head[n++] = ' '; head[n++] = '|'; head[n++] = ' '; head[n] = 0; }
            klo_line(&s, head);
        } else dropped++;
    } else if (now - lastline >= 1000) {
        lastline = now; last = s;
        klo_line(&s, "");
    }
}

static void klo_init(void)
{
    klo.on = GetPrivateProfileIntA("Shoulder", "Log", 0, klh_ini) != 0;
    if (klo.on) klog("shoulder: log on (reads only): one line a second while a local ZFFPlayer exists, one at every change of want / side / the gates / the down state / the key (at most %d a second); re\\shoulder_m02.md says how to read them", KLO_MAXCHANGE);
}

#endif /* KLSHOULDER_C */
