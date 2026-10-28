/*
 * klannounce.c - ONE WAY TO PUT A LINE ON THE FRAGILE ALLIANCE ANNOUNCEMENT ELEMENT (2026-10-28, T1; the three callers existed before, each with its own copy).
 *
 * The stock routine 0x468430 (thiscall: ZFAAnnouncementDisplay *, const char *text, float seconds; ret 8) shows a line at the top of the HUD. It may KEEP the text pointer, so the
 * text is copied into a static buffer PER CALLER SLOT (the callers used their own static buffers; a shared one would change a line that is still on screen).
 * Callers: klucc.c kluc_show_now (its pending queue + 6 s stock-message rule), kladren.c kad_say (its own gate + once-per-key), klshoppage.c / klkeys.c hints (klan_show), and
 * klhud_popup.c's PopupTest (test only, left as it was). Nothing here is a code patch: the game's own routine is called after its first bytes were compared (klu_same_code).
 *
 *   klan_element()           the element through [[gamedata+0x15dc]]+0x10a8 (klucc.c's walk), 0 = not there yet
 *   klan_busy(el)            a stock message is still on screen
 *   klan_say_el(el, t, secs, slot) (slot KLAN_UCC / KLAN_ADREN / KLAN_HINT) call the routine on an element the caller found: 1 = shown, 0 = the routine is not the one this build knows (nothing called)
 *   klan_show(t, secs, force) element + busy check + say; 1 = shown (or dropped for good), 0 = try again later
 * AFTER klhud.c (klu_same_code) and klhud_popup.c (klpu_evt, the popup's element copy), BEFORE kladren.c / klucc.c / klshoppage.c.
 */
#ifndef KLANNOUNCE_C
#define KLANNOUNCE_C

#define KLAN_ANNOUNCE  0x00468430u
#define KLAN_ANN_VT    0x00bbdd34u
#define KLAN_OSD_VT    0x00bbe504u
#define KLAN_O_ANN     0x10a8
#define KLAN_OSDHOLD   0x15dc
#define KLAN_TEXT      240

static int klan_code = -1, klan_toldNoEl;

static DWORD klan_element(void)
{
    DWORD gd, hold, osd, el, vt = 0; BYTE none = 0xff;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(hold = klh_rd32(gd + KLAN_OSDHOLD)) || !klh_rd(hold + 4, &none, 1) || none == 0xff) return 0;
    if (!(osd = klh_rd32(hold)) || klh_rd32(osd) != KLAN_OSD_VT || !(el = klh_rd32(osd + KLAN_O_ANN)) || !klh_rd(el, &vt, 4)) return 0;
    if (vt != KLAN_ANN_VT && vt != (DWORD)(DWORD_PTR)&klpu_evt[1]) return 0;
    return el;
}
static int klan_busy(DWORD el)
{   /* a stock message still on screen: [el+0x30] end (clock / 1024), the clock [[0xdd2640]+0x48] (klhud_popup.c's reading) */
    float end = -1.0f; LONG frame = 0; DWORD sys;
    return klh_rd(el + 0x30, &end, 4) && end > 0 && (sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) != 0 && klh_rd(sys + 0x48, &frame, 4) && frame < (LONG)(end * 1024.0f);
}
enum { KLAN_UCC, KLAN_ADREN, KLAN_HINT, KLAN_NSLOT };                 /* one text buffer per caller: a line that stays up is never overwritten by another caller's */
static const char *const klan_pre[KLAN_NSLOT] = { "ucc", "adren", "announce" };
static int klan_ready(int slot)
{   /* 1 = 0x468430 is the routine this build knows (compared once); the log line keeps the caller's old prefix ('ucc:' / 'adren:') */
    static const BYTE say_code[8] = { 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x8b, 0xc7 };   /* 0x468430 */
    if (klan_code < 0) { klan_code = klu_same_code(KLAN_ANNOUNCE, say_code, sizeof say_code); if (!klan_code) klog("%s: 0x468430 is not the announcement routine this build knows: lines go to the log only", klan_pre[slot >= 0 && slot < KLAN_NSLOT ? slot : KLAN_HINT]); }
    return klan_code;
}
static int klan_say_el(DWORD el, const char *text, float secs, int slot)
{
    static char ring[KLAN_NSLOT][KLAN_TEXT];
    char *buf;
    if (slot < 0 || slot >= KLAN_NSLOT) slot = KLAN_HINT;
    if (!klan_ready(slot) || !el) return 0;
    buf = ring[slot];
    snprintf(buf, KLAN_TEXT, "%s", text);
    ((void (__fastcall *)(void *, void *, const char *, float))(DWORD_PTR)KLH_VA(KLAN_ANNOUNCE))((void *)(DWORD_PTR)el, 0, buf, secs);
    return 1;
}
static int klan_show(const char *text, float secs, int force)
{
    DWORD el;
    if (!klan_ready(KLAN_HINT)) return 1;                             /* nothing can be shown: drop */
    if (!(el = klan_element())) { if (!klan_toldNoEl++) klog("announce: no FA announcement element yet ([[gamedata+0x15dc]]+0x10a8): a line waits"); return 0; }
    if (!force && klan_busy(el)) return 0;
    klan_say_el(el, text, secs, KLAN_HINT);
    return 1;
}

#endif /* KLANNOUNCE_C */
