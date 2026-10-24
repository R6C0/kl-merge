/*
 * klstancefix.c - [StanceFix]: crouch again while the crouch / stand clip is still running = the body no longer restarts the reverse clip at frame 0.
 * NOTHING HERE HAS RUN IN THE GAME. Included by klcamsmooth.c (no change to klhook.c); its tick is called first thing in klcamsmooth_tick (the
 * same site, return address 0x87aa82, game thread), its init from klcamsmooth_init. Uses klh_rd / klh_rd32 / klh_data / klcam_player / klog.
 *
 * OWNER 2026-10-25: "if u crouch then crouch again it cancels the animation, fix that it needs to be continuous".
 * CAUSE (static reading of kl2.exe, re/player_anim_blend.md addendum; no game run):
 *   mover = ZFFPlayerMovementBaseMove = [player+0x63c]; update 0x7a43e0; per-frame clip selector 0x5abbb0 (called at 0x7a485b); transition selector
 *   0x77ed80 (called at 0x5ac7e7); phase stepper 0x757a50; clip phase advance 0x59d990; clip-end test 0x5dad60.
 *   mover fields: +0x40 normalised clip phase, +0x58 current clip slot, +0x1e38/+0x1e3c gait / previous gait, +0x1e40/+0x1e44 class / previous class,
 *   +0x1eac restart flag, +0x1eae transition lock, +0x1eaf transition clip active, +0x1eb0 commit flag.
 *   A second stance toggle during Stand_To_Crouch (slot 0x1154) or Crouch_To_Stand (0x1180) makes 0x77ed80 pick the REVERSE clip (tail 0x77f478 ..
 *   0x77f488): it changes [m+0x58] and sets [m+0x1eac] = 1, then 0x757a50 resets [m+0x40] to 0. The reverse clip starts at frame 0 while the body was
 *   at phase p = the visible cancel and pop. The crouch transitions do not set the 1eae lock, so nothing blocks the re-select. Walk_To_Crouch /
 *   Walk_To_Stand (0x1128 / 0x1078) go the same way. There is no Run_To_Crouch / Crouch_To_Run in the player's set: a crouch while running falls
 *   back to Sneak_To_Crouch / Walk_To_Crouch.
 *   GUESSES (unchecked in the game): that +0x40 runs 0..1 over a clip; that a clip switch inside one pair is the 'second toggle'; that this tick runs
 *   AFTER the frame's pose sample or at least before the next one, so a phase write takes effect (if the game overwrites it the same frame, the retry
 *   below runs up to 3 frames and logs 'overwritten'; the S1 plan - pinning [m+0x1eae] = 1 to hold the commit - is NOT implemented, it needs the log first);
 *   the class meanings (1 stand/run, 2 sneak, 3 crouch, 4 down) are not used here.
 * WHAT IT DOES: when [m+0x58] flips inside a pair (A <-> B) within one transition, and last frame's phase was p (0.03 .. 0.97), write
 *   [m+0x40] = 1 - p (the mirrored pose of the reverse clip) and clear [m+0x1eac], so the reverse clip continues from where the body is.
 *   kcs_stancefix_busy = 1 while that transition runs (klcamsmooth.c doubles its stance limit and lengthens the ease).
 * SHIP rule: data writes into the heap (klh_data) only, no code patch. Dry=1 logs 'stancefix: would mirror' and writes nothing.
 * ini [StanceFix]: Enable=1 (recommended on) Dry=0 Log=1.
 */
#ifndef KLSTANCEFIX_C
#define KLSTANCEFIX_C

#define KSF_PAIRS 2
static const DWORD ksf_pair[KSF_PAIRS][2] = {
    { 0x1154, 0x1180 },      /* Stand_To_Crouch <-> Crouch_To_Stand (slot values read statically; GUESS that [m+0x58] holds exactly these) */
    { 0x1128, 0x1078 },      /* Walk_To_Crouch  <-> Walk_To_Stand */
};
static struct {
    int enable, dry, log, on;
    DWORD mover, pclip; float pph; int have;
    long lastframe;
    int fix_left, over; float target; DWORD fixclip;
    int busy_for;                /* the transition clip a mirror started in; busy while the mover is still in a pair clip */
    long nmirror, nover;
} ksf;

static int ksf_partner(DWORD clip, DWORD *out)
{
    int i;
    for (i = 0; i < KSF_PAIRS; i++) {
        if (clip == ksf_pair[i][0]) { *out = ksf_pair[i][1]; return 1; }
        if (clip == ksf_pair[i][1]) { *out = ksf_pair[i][0]; return 1; }
    }
    return 0;
}
static int ksf_inpair(DWORD clip) { DWORD x; return ksf_partner(clip, &x); }

static void ksf_reset(void) { ksf.have = 0; ksf.mover = 0; ksf.fix_left = 0; ksf.busy_for = 0; kcs_stancefix_busy = 0; }

static void klstancefix_tick(int game_thread)
{
    DWORD gd, P, m, sys, clip, partner; float ph = 0; long frame;
    if (!ksf.on || !game_thread || !klh_exe_ok) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KCS_RCB_RA)) return;
    if (!(P = klcam_player(&gd))) { ksf_reset(); return; }
    if (!(m = klh_rd32(P + 0x63c))) { ksf_reset(); return; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)))) return;
    frame = (long)klh_rd32(sys + 0x48);
    if (frame == ksf.lastframe) return;
    ksf.lastframe = frame;
    clip = klh_rd32(m + 0x58);
    if (!klh_rd(m + 0x40, &ph, 4) || !klcam_fin(ph) || ph < -0.01f || ph > 1.5f || clip == 0 || clip > 0x10000) { ksf_reset(); return; }
    if (m != ksf.mover) { ksf_reset(); ksf.mover = m; }

    if (ksf.have && clip != ksf.pclip && ksf_partner(ksf.pclip, &partner) && partner == clip && ksf.pph > 0.03f && ksf.pph < 0.97f) {
        float t = 1.0f - ksf.pph;
        if (t < 0) t = 0; if (t > 0.99f) t = 0.99f;
        if (ksf.log) klog("stancefix: %swould mirror: clip %04lx -> %04lx, phase was %.3f, now %.3f -> %.3f", ksf.dry ? "DRY: " : "", (unsigned long)ksf.pclip, (unsigned long)clip, ksf.pph, ph, t);
        ksf.nmirror++;
        ksf.busy_for = 1;
        if (!ksf.dry) {
            BYTE fl = 0;
            if (fabs(ph - t) > 0.02f) klh_data((void *)(DWORD_PTR)(m + 0x40), &t, 4, "stancefix: mirrored clip phase");
            if (klh_rd(m + 0x1eac, &fl, 1) && fl) { BYTE z = 0; klh_data((void *)(DWORD_PTR)(m + 0x1eac), &z, 1, "stancefix: restart flag"); }   /* GUESS: a byte */
            ksf.fix_left = 3; ksf.target = t; ksf.fixclip = clip; ksf.over = 0;
            ph = t;
        }
    } else if (ksf.fix_left > 0 && !ksf.dry) {
        ksf.fix_left--;
        if (clip == ksf.fixclip && ph < 0.05f && ksf.target > 0.1f) {
            /* the game reset the phase again after our write: write once more, count it. 3 strikes = give up (log says so). */
            ksf.nover++; ksf.over++;
            if (ksf.log) klog("stancefix: phase %.3f was overwritten after the mirror (target %.3f), strike %d/3", ph, ksf.target, ksf.over);
            if (ksf.over < 3) { klh_data((void *)(DWORD_PTR)(m + 0x40), &ksf.target, 4, "stancefix: mirrored clip phase (retry)"); ph = ksf.target; }
            else { ksf.fix_left = 0; if (ksf.log) klog("stancefix: mirror does not survive the frame; the S1 hold (pin [m+0x1eae]) is not built: see the file header"); }
        }
    }
    if (ksf.busy_for && !ksf_inpair(clip)) ksf.busy_for = 0;
    kcs_stancefix_busy = ksf.busy_for;
    ksf.pclip = clip; ksf.pph = ph; ksf.have = 1;
}

static void klstancefix_init(void)
{
    memset(&ksf, 0, sizeof ksf);
    ksf.enable = GetPrivateProfileIntA("StanceFix", "Enable", 1, klh_ini) != 0;
    ksf.dry = GetPrivateProfileIntA("StanceFix", "Dry", 0, klh_ini) != 0;
    ksf.log = GetPrivateProfileIntA("StanceFix", "Log", 1, klh_ini) != 0;
    ksf.on = ksf.enable;
    if (ksf.on) klog("stancefix: on: mirrors the phase when a crouch / stand clip is reversed mid-way (Dry %d Log %d)", ksf.dry, ksf.log);
}

#endif
