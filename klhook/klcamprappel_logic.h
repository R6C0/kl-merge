/* klcamprappel_logic.h - pure logic of klcamprappel.c (no windows.h): mode parse, native-clip check, descent plan arithmetic.
 * Ported from luvsic's a-newer-perspective loader/rappel.inc @32aa649 (in contribution with luvsic).
 * Test: klcamprappel_test.c.
 */
#ifndef KLCAMPRAPPEL_LOGIC_H
#define KLCAMPRAPPEL_LOGIC_H
#include <math.h>
#include <string.h>

enum { KCAMR_OFF = 0, KCAMR_DRY, KCAMR_NATIVE, KCAMR_LIVE, KCAMR_AUTO };

/* [CampRappel] Mode: a number 0..4 or off/dry/native/live/auto; anything else = off */
static int kcamr_mode_parse(const char *s)
{
    static const char *nm[] = { "off", "dry", "native", "live", "auto" };
    int i;
    if (!s || !*s) return KCAMR_OFF;
    if (s[0] >= '0' && s[0] <= '4' && !s[1]) return s[0] - '0';
    for (i = 0; i < 5; i++) {
        const char *a = s, *b = nm[i];
        while (*a && *b && ((*a | 0x20) == *b)) { a++; b++; }
        if (!*a && !*b) return i;
    }
    return KCAMR_OFF;
}

/* the five native clip ids (u16 at movement +0x1fe4..+0x1fec): 0xFFFF = the level's .ANM lacks that clip.
 * returns how many are present (5 = the native rappel can run; stock code with a NULL clip crashes at 0x5a503a) */
static int kcamr_clips_present(const unsigned short ids[5])
{
    int i, n = 0;
    for (i = 0; i < 5; i++) if (ids[i] != 0xFFFF) n++;
    return n;
}
static int kcamr_native_ok(const unsigned short ids[5]) { return kcamr_clips_present(ids) == 5; }

/* Does the native rappel get a press now? mode + clips -> 1 native starts, 0 refused (never a crash). live/auto: the
 * loader's live descent is NOT ported (see klcamprappel.c), so both behave like native here. */
static int kcamr_decide(int mode, int clips_ok, int native_dead)
{
    if (mode < KCAMR_NATIVE) return 0;
    if (native_dead) return 0;
    return clips_ok ? 1 : 0;
}

/* segment count of a scripted descent: ceil((H / speed) / clipSec), clamped 1..12 (rappel.inc rp_plan) */
static int kcamr_segments(float H, float speed, float clipSec)
{
    float t, n;
    if (clipSec < 0.2f) clipSec = 0.2f;
    if (speed < 1.0f) speed = 1.0f;
    if (H <= 0.0f) return 1;
    t = (H / speed) / clipSec;
    n = (float)ceil(t - 1e-4f);
    if (n < 1) n = 1;
    if (n > 12) n = 12;
    return (int)n;
}

/* waypoint i (0-based) of n between X (top) and G (ground): X + (G-X)*(i+1)/n */
static void kcamr_waypoint(const float X[3], const float G[3], int i, int n, float out[3])
{
    int k;
    if (n < 1) n = 1;
    for (k = 0; k < 3; k++) out[k] = X[k] + (G[k] - X[k]) * (float)(i + 1) / (float)n;
}

/* direction dedup: two edge probes whose unit directions have dot > 0.97 are the same edge */
static int kcamr_same_dir(const float a[3], const float b[3])
{
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] > 0.97f;
}

/* the module idles when the FA mini-cutscene rappel (klrappel.c) owns the level */
static int kcamr_idle(int campaign_active, int fa_rappel_on_level)
{
    return !campaign_active || fa_rappel_on_level;
}

/* ---- landing camera (READ rappel.inc 69-73, 273-282, 360-385; luvsic 15 Oct). After the native rappel the player faces
 * the wall while the camera keeps the outward descent look. [CampRappel] Land: off | turn | cam | turncam | auto.
 * turn = flip him 180 deg in place, cam = keep the facing and re-aim the camera behind him (force teleport), turncam =
 * both, auto = a ray 150 cm ahead from chest height: wall -> turncam (M02), open -> cam (M09). */
enum { KCAMR_L_OFF = 0, KCAMR_L_TURN, KCAMR_L_CAM, KCAMR_L_TURNCAM, KCAMR_L_AUTO };
static int kcamr_land_parse(const char *s)
{
    static const char *nm[] = { "off", "turn", "cam", "turncam", "auto" };
    int i;
    if (!s || !*s) return KCAMR_L_OFF;
    if (s[0] >= '0' && s[0] <= '4' && !s[1]) return s[0] - '0';
    for (i = 0; i < 5; i++) {
        const char *a = s, *b = nm[i];
        while (*a && *b && ((*a | 0x20) == *b)) { a++; b++; }
        if (!*a && !*b) return i;
    }
    return KCAMR_L_OFF;
}
/* the final landing action: auto resolves by the wall ray (hit > 0 = wall ahead), anything else is kept */
static int kcamr_land_resolve(int land, int ray_ok, int ray_hit)
{
    if (land != KCAMR_L_AUTO) return land;
    return (ray_ok && ray_hit > 0) ? KCAMR_L_TURNCAM : KCAMR_L_CAM;
}
/* a landing = the previous sample was the rappel movement (id 0x10) in state 5 and now it is another movement with the rappel inactive */
static int kcamr_landed(int have_prev, int prev_movid, int prev_state, int movid, int active)
{
    return have_prev && prev_movid == 0x10 && prev_state == 5 && movid != 0x10 && !active;
}
/* the yaw (degrees 0..360) of the probe forward F = -row0 (fwd = 1, luvsic's default), -1 when the row is degenerate */
static float kcamr_yaw(const float *M)
{
    float fx = -M[0], fz = -M[2], y;
    if (fx * fx + fz * fz < 1e-6f) return -1.0f;
    y = (float)atan2(fx, fz) * 57.2957795f;
    return y < 0 ? y + 360.0f : y;
}
/* inverse of kcamr_yaw in the 0x857110 row layout: row0 = -F, row1 = up, row2 = (row0.z, 0, -row0.x) */
static void kcamr_yaw_matrix(float yawDeg, float *M)
{
    float a = yawDeg * 0.0174532925f, ax = -(float)sin(a), az = -(float)cos(a);
    M[0] = ax; M[1] = 0; M[2] = az;
    M[3] = 0;  M[4] = 1; M[5] = 0;
    M[6] = az; M[7] = 0; M[8] = -ax;
}
/* the yaw to teleport to: the current yaw, plus 180 for turn, wrapped to 0..360 */
static float kcamr_land_yaw(float yaw, int land_final)
{
    float y = yaw + ((land_final & 1) ? 180.0f : 0.0f);
    if (y >= 360.0f) y -= 360.0f;
    return y;
}
/* does the final landing action re-aim the camera (force teleport)? */
static int kcamr_land_cam(int land_final) { return (land_final >> 1) & 1; }

/* ---- 1110 [CampRappel] Cam=ours|his: WHO DRIVES THE CAMERA DURING THE DESCENT.
 * Why (READ kl2.exe, disassembled): the campaign levels carry ~12 CCameraBox "RappelCB_*" boxes. A box hands its profile record to the camera
 * (0x700830 -> cam+0x7fc) and 0x78bbc0 re-applies it every frame; while cam+0x7fc is non-null the camera ORIENTATION code (0x447240 ..) reads
 * record+0x180 (EFMMode 3 LookFromPos / 1 LookAtPos) and aims the camera from the box's PosObject at the player: the view is a fixed shot,
 * the player cannot look left / right. Our (Fragile Alliance) camera is the stock free third-person follow camera (profile selection 0x778f50 ->
 * default profile 0x154a820 etc., tuned by klcam.c / klcamsmooth.c), mouse looks around the player. 0x778f50 runs that selection only
 * when 0x78bbc0 returns 0, i.e. when cam+0x7fc is NULL. So "ours" = clear cam+0x7fc while the descent runs. His = leave the boxes alone (stock).
 * The start animation stays his: the takeover begins at rappel sub-state HandFrom (READ 0x825290: 0 Start clip, 1 Jump_Start, 2 Wait_On_Wall,
 * 3 Jump_Loop = the descent, 4 Jump_End, 5 done) and ends at the landing edge plus TailMs (the Leave box would otherwise snap the outward shot back). */
enum { KCAMR_CAM_HIS = 0, KCAMR_CAM_OURS };
static int kcamr_cam_parse(const char *s)
{
    static const char *yes[] = { "ours", "on", "1" };
    int i;
    if (!s || !*s) return KCAMR_CAM_HIS;
    for (i = 0; i < 3; i++) {
        const char *a = s, *b = yes[i];
        while (*a && *b && ((*a | 0x20) == *b)) { a++; b++; }
        if (!*a && !*b) return KCAMR_CAM_OURS;
    }
    return KCAMR_CAM_HIS;                                      /* his, off, 0 and anything unknown = stock boxes */
}
/* HandFrom clamps to 0..4 (default 3) */
static int kcamr_cam_handfrom(int v) { return v < 0 ? 3 : (v > 4 ? 3 : v); }
/* is the camera ours at this instant? rappelling = the movement is active or movement id 0x10; state = player+0x25c0 (-1 when unknown);
 * since_end_ms = ms since the rappel ended (-1 while it runs or never ran), tail_ms = the hold after the end */
static int kcamr_cam_ours_now(int cam_mode, int rappelling, int state, int hand_from, long since_end_ms, long tail_ms)
{
    if (cam_mode != KCAMR_CAM_OURS) return 0;
    if (rappelling) return state >= hand_from;          /* state 5 (done, the landing edge) stays ours so the tail runs from the real landing */
    return since_end_ms >= 0 && since_end_ms <= tail_ms;
}
/* edge of the takeover: +1 take, -1 hand back, 0 none */
static int kcamr_cam_edge(int was, int now) { return now && !was ? 1 : (!now && was ? -1 : 0); }
/* the write decision for one frame while the camera is ours: clear only a non-null, readable box pointer */
static int kcamr_cam_must_clear(int ours, unsigned long box_ptr) { return ours && box_ptr != 0; }

/* [Camera] CampaignOff: our FA camera tuning (klcam.c) idles while a campaign level is loaded */
static int kcamr_camtune_idle(int campaign_off_cfg, int campaign_level) { return campaign_off_cfg && campaign_level; }

#endif
