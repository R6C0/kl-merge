/*
 * klaiturn.c - HEAVIER AI BODY TURNS: [Rigid] AiTurnDps=N caps how fast every AI actor (ZFFActor: soldiers, police,
 * civilians, the Arcade AI heisters) turns its body. Owner's wish (re\rigid_feel.md: heavier, less sponge-like AI).
 * Evidence, read statically in kl2.exe build 0490 (re\kl2_rotation.md, "2026-10-23 cloud static reading", section A):
 * the AI move step 0x812b70 reads ONE float, 0xcdea94 = 720.0 deg/s (.data, its only code reference at 0x814326), scales
 * it by 1.0 (0.2 while the root motion is slower than 30 units/s) and by deg2rad, and hands it to ZActor slot 396
 * (0x660780), which turns the body by min(angle, ramp x rate x dt) a frame. So one data write lowers the turn rate of
 * every AI actor in the level; nothing of the player's turning goes through it (ZFFPlayer has its own path, section B).
 *
 * Keys ([Rigid]):
 *   AiTurnDps=N     0 = off (default, the game's 720 stays). 60..720 = the cap in degrees per second. The write happens
 *                   once at start-up, only if the float still reads 720.0 (this build's value; another value means another
 *                   build or another writer: left alone, one log line). Allowed under the SHIP rule: a .data global, no
 *                   code byte, checked by klh_data's guard (the CEG range map says .data is not hashed; the guard decides).
 *   AiTurnLog=1     one line at start-up with the value before and after.
 * NOT RUN IN THE GAME. Live experiment: re\kl2_rotation.md section D (per-bot peak heading change per tick: peaks near
 * 720 off, none above N on; watch for path overshoot at corners, which would be the sign N is too low for the pathing).
 * GUESS: a value under ~180 makes bots overshoot waypoints; start at 240..360.
 */
#ifndef KLAITURN_C
#define KLAITURN_C

#define KLAT_GLOBAL   0x00cdea94u      /* float: AI body turn rate, deg/s (0x814326 is the only reader) */
#define KLAT_STOCK    720.0f

static struct { int dps, log, done; } klat;

static void klaiturn_init(void)
{
    float cur = 0, want;
    klat.dps = GetPrivateProfileIntA("Rigid", "AiTurnDps", 0, klh_ini);
    klat.log = GetPrivateProfileIntA("Rigid", "AiTurnLog", 1, klh_ini);
    if (!klat.dps) return;
    if (klat.dps < 60 || klat.dps > 720) { klog("aiturn: [Rigid] AiTurnDps=%d is outside 60..720: off", klat.dps); klat.dps = 0; return; }
    if (!klh_exe_ok) { klog("aiturn: not the known kl2.exe: the turn-rate global is not written"); return; }
    if (!klh_rd((DWORD_PTR)KLH_VA(KLAT_GLOBAL), &cur, 4) || cur != KLAT_STOCK) {
        klog("aiturn: the AI turn-rate float at %08lx reads %g, not %g: another build or another writer, left alone", (DWORD)KLAT_GLOBAL, cur, KLAT_STOCK);
        return;
    }
    want = (float)klat.dps;
    if (!klh_data((void *)KLH_VA(KLAT_GLOBAL), &want, 4, "AI body turn rate (0xcdea94, .data)")) { klog("aiturn: the write was refused by the guard: off"); return; }
    klat.done = 1;
    if (klat.log) klog("aiturn: AI body turn rate %g -> %g deg/s for every AI actor (one .data float; the player's own turning is not touched); NOT RUN IN THE GAME before this build", cur, want);
}

#endif /* KLAITURN_C */
