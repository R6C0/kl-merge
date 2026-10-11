/*
 * klvis.c - a LOG of the game's vision grid and of the 16 bytes a FakeTarget without a grid record writes behind it
 * ([Vis] Log=1; default OFF). READS ONLY: no write, no call of a game routine, no patch; every read goes through
 * klh_rd (ReadProcessMemory on the own process). Any thread. Part of KLHook (included by klhook.c after klshoulder.c,
 * SHIP and TEST alike). NOTHING HERE HAS RUN IN THE GAME.
 *
 * WHY (re\crash_686a66.md, 2026-10-11; read in kl2.exe build 0490 by the track that found it, reviewed, and the dump
 * of run C_DM09 shows it): ZFakeTarget's frame update (0x560630, vtable 0xbd143c slot 25) registers the target with
 * ZCheckVisible through 0x55cc40 -> 0x59c790 and then calls 0x7143f0 with the index it got, unchecked. A target whose
 * place lies outside the grid's box gets index 0xff, and record 0xff of the table of 200 records (0x1c bytes each,
 * from object + 0x12ae4) lies 0x5a8 bytes BEHIND the object: 16 bytes of the heap are written every frame - the word
 * 0xff100110 ('no cell') and the target's three floats. On Retomoto Tower the two parked escape vans (parked at
 * y -60040 by kl_fa_street.place_escape) are such targets; the bytes they hit in run C_DM09 were the place list of a
 * Defend step, and the game read a freed pointer from it (crash 0x686a66).
 *
 * WHAT IS READ
 *   V = [0x1535c70], the ZCheckVisible object (0 before a level has one).
 *   [V + 0x50 .. + 0x80): twelve floats, the grid: cell size x y z, 1 / cell size x y z, box low x y z, box high
 *      x y z (re\crash_686a66.md 8; `python tools\kl_fa_bots_dyn.py grid <build folder> <the 96 hex digits>` compares
 *      them with the level's own room boxes). The first version of this file took the box for the first six floats
 *      and so never saw a 'filled' grid (runs V0_DM09 / V1_DM09, 2026-10-11: no grid line).
 *   [V + 0x12ae4 + 0xff * 0x1c) = [V + 0x146c8 .. + 0x146d8): the sixteen bytes of 'record 0xff'. In a level
 *      without the fault they belong to something else and never start with 0xff100110.
 *
 * LOG
 *   vis: grid of ZCheckVisible 1a2b3c00 (scene ...): <96 hex digits>; low (x, y, z) high (x, y, z)    once per object
 *   vis: record 0xff behind the grid holds 'no cell' ff100110 + (x, y, z): A TARGET OUTSIDE THE GRID WRITES THERE
 *        EVERY FRAME                                                             once per distinct place, at most 8
 *   vis: 30 s after the grid appeared: record 0xff has never held 'no cell'      once per object, when it stayed clean
 *
 * KLHook.ini
 *   [Vis]
 *   Log=0               1 = the lines above
 */
#ifndef KLVIS_C
#define KLVIS_C

#define KLV_CHECKVISIBLE 0x01535c70           /* the pointer to the ZCheckVisible object */
#define KLV_GRID         0x50                 /* twelve floats */
#define KLV_REC_FF       0x146c8              /* 0x12ae4 + 0xff * 0x1c */
#define KLV_NOCELL       0xff100110UL

static struct { int on; } klvis;

static void klvis_tick(void)
{
    static DWORD obj, since, last, places; static int told_clean; static float seen[8][3];
    DWORD v, now = GetTickCount(); BYTE g[48], r[16]; float f[12]; char hex[97], scene[96]; int i;
    if (!klvis.on || !klh_exe_ok || now - last < 250) return;
    last = now;
    v = klh_rd32((DWORD_PTR)KLH_VA(KLV_CHECKVISIBLE));
    if (!v) { obj = 0; return; }
    if (v != obj) {
        if (!klh_rd(v + KLV_GRID, g, sizeof g)) return;
        memcpy(f, g, sizeof g);
        for (i = 0; i < 48; i++) snprintf(hex + 2 * i, 3, "%02x", g[i]);
        if (!(f[0] > 0) || !(f[2] > 0) || !(f[9] > f[6]) || !(f[11] > f[8])) return;      /* cell size and box not filled in yet: look again next pass */
        obj = v; since = now; places = 0; told_clean = 0;
        if (!klh_scene(scene, sizeof scene)) strcpy(scene, "?");
        klog("vis: grid of ZCheckVisible %08lx (scene %s): %s; low (%.1f, %.1f, %.1f) high (%.1f, %.1f, %.1f) cell (%.1f, %.1f, %.1f)", v, scene, hex, f[6], f[7], f[8], f[9], f[10], f[11], f[0], f[1], f[2]);
    }
    if (!klh_rd(obj + KLV_REC_FF, r, sizeof r)) return;
    if (*(DWORD *)r == KLV_NOCELL) {
        float p[3]; memcpy(p, r + 4, 12);
        for (i = 0; i < (int)places && i < 8; i++) if (seen[i][0] == p[0] && seen[i][1] == p[1] && seen[i][2] == p[2]) break;
        if (i == (int)places && places < 8) {
            memcpy(seen[places++], p, 12);
            klog("vis: record 0xff behind the grid holds 'no cell' %08lx + (%.1f, %.1f, %.1f), %lu s after the grid appeared: A TARGET OUTSIDE THE GRID WRITES THERE EVERY FRAME (re\\crash_686a66.md)",
                 KLV_NOCELL, p[0], p[1], p[2], (now - since) / 1000);
        }
    } else if (!places && !told_clean && now - since >= 30000) {
        told_clean = 1;
        klog("vis: 30 s after the grid appeared: record 0xff has never held 'no cell' (its bytes now: %08lx %08lx %08lx %08lx)", *(DWORD *)r, *(DWORD *)(r + 4), *(DWORD *)(r + 8), *(DWORD *)(r + 12));
    }
}

static void klvis_init(void)
{
    klvis.on = GetPrivateProfileIntA("Vis", "Log", 0, klh_ini) != 0;
    if (klvis.on) klog("vis: log on (reads only): the vision grid's box once per level, and whether 'record 0xff' behind it is written by a target outside the grid");
}

#endif /* KLVIS_C */
