/*
 * klhud_kill.c - the kill / reward line ('POLICE +$5000', '+$50000') moved OFF the middle of the screen into the money box, under
 * REWARDS (2026-10-13; the owner, with a picture of the line beside a doorway: 'revamp or move it to where the bonus is shouldnt be on
 * the main screen'; and over the round-over scoreboard: '+$50000' drawn across the DEAD row). Plan: re\hud_killfeed_plan.md 4.
 *   [HUD] KillLine=1 (default = [HUD] Draft)   0 = the stock line, untouched
 *   [HUD] KillSeconds=3.5                       how long the line stands under REWARDS
 * Part of KLHook, an add-on of klhud.c: included by klhook.c AFTER klhud_popup.c (uses klu / klu_r / klu_inii / klu_inif / klu_same_code /
 * klpu_str and klhook.c's klh_rd / klh_rd32 / klh_data). SHIP rule kept: no code byte of kl2.exe changes; ONE heap dword (the element's
 * vtable pointer -> a private copy with slot 2 wrapped).
 *
 * THE ELEMENT (kl2.exe build 0490, read 2026-10-13 with objdump from the owner's kl2.exe): ZHeistPointsPopupDisplay = [osd+0x10b8], vtable
 * 0xbbde64, 14 slots: 2 Render 0x549480 (thiscall (ctx, cam), ret 8), 4 Init 0x5ab8b0, 6 Update 0x635420. Render (READ whole, 0x549480 ..
 * 0x5495e8): the place +0x14 / +0x18 / +0x1c; when the float +0x30 is not 0 the drift t = (clock [[0xdd2640]+0x48] - (+0x30 x k)) ... and
 * an alpha 2t x 255 for the text +0x28 and its shadow +0x2c (vtable +0x218 SetAlpha), then each one's Draw (vtable +0x1e8, 4 arguments).
 * Nothing else: no state is written, so NOT calling it = the line is not drawn and nothing else changes.
 * THIS PART: while klhud.c's HUD stands for the level (klu_r.made, no fault) the wrapper does not call the stock Render; a change of +0x30
 * (a new message: Update / the setter writes the start there) is read once - the text's string ([text+0xa4]+0xc, ZCHAROBJ, as
 * klhud_popup.c) - and handed to klhud.c (klu_kill_txt / klu_kill_at), whose compose puts it under REWARDS (KLU_T_KILL). In any other
 * state the stock Render runs: the line is never lost while our HUD is down.
 * 2026-10-26: the same when the compose has NO place for the line (klhud.c klu_keep, bit KLU_KEEP_KILL): online the money column and
 * the kill line exist only with [HUD] OnlineCrew=1 + OnlineFeed=1, and the port's open item was 'stock kill popup still swallowed online'
 * (the wrapper kept the line and nothing showed it). Now it is swallowed only in a compose that draws it. Not run live.
 * NOT RUN IN THE GAME (2026-10-13). The string's own glyphs: bytes >= 0x80 (the skull, U+E0xx in the font) are dropped.
 */
#ifndef KLHUD_KILL_C
#define KLHUD_KILL_C

#define KLKF_VT          0x00bbde64u          /* ZHeistPointsPopupDisplay */
#define KLKF_RENDER      0x00549480u          /* its slot 2 */
#define KLKF_O_EL        0x10b8               /* osd: ZHeistPointsPopupDisplay * */
#define KLKF_E_START     0x30                 /* float: the message's start (0 = none) */
#define KLKF_NSLOT       14

static struct { int on; float secs; } klkf;
static struct { DWORD osd, el; int refused, told; } klkf_r;
static DWORD klkf_evt[KLKF_NSLOT + 1];        /* [0] RTTI locator, [1..] the slots */
static int klkf_evt_ready;
static volatile LONG klkf_seen;               /* the +0x30 bits of the last message handed over */
static volatile LONG klkf_n_call, klkf_n_kept, klkf_n_new;

static char __fastcall klkf_render(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el, text, str; LONG st; char s[96], o[64]; int n, i, k = 0; (void)edx;
    InterlockedIncrement(&klkf_n_call);
    if (klkf.on && e == klkf_r.el && klu_r.made && !klu_r.fault && (klu_keep & KLU_KEEP_KILL)) {     /* 2026-10-26: only while klhud.c's compose gives the line a place (klu_keep): online with [HUD] OnlineFeed=0 or no crew box, and with Money=0, the stock pop-up draws as the game's own instead of vanishing */
        st = *(const LONG *)(DWORD_PTR)(e + KLKF_E_START);
        if (st && st != klkf_seen && TryEnterCriticalSection(&klu_cs)) {      /* the render thread never WAITS on a lock: busy = the next frame */
            klkf_seen = st;
            text = *(const DWORD *)(DWORD_PTR)(e + 0x28);
            n = text && klh_rd32(text) == KLU_TEXT_VT && (str = klh_rd32(text + 0xa4)) != 0 ? klpu_str(str + 0xc, s, sizeof s) : 0;
            for (i = 0; i < n && k < (int)sizeof o - 1; i++) {                 /* the skull glyph and other non-ASCII bytes go; spaces folded */
                unsigned char c = (unsigned char)s[i];
                if (c >= 0x80 || c < 0x20) continue;
                if (c == ' ' && (k == 0 || o[k - 1] == ' ')) continue;
                o[k++] = (char)c;
            }
            while (k && o[k - 1] == ' ') k--;
            o[k] = 0;
            if (k) { memcpy(klu_kill_txt, o, (size_t)k + 1); klu_kill_at = (LONG)GetTickCount() | 1; InterlockedIncrement(&klkf_n_new); InterlockedIncrement(&klkf_n_total); }
            LeaveCriticalSection(&klu_cs);
        }
        InterlockedIncrement(&klkf_n_kept);
        return 1;                                                           /* the stock line is not drawn */
    }
    return ((klu_render_t)(DWORD_PTR)KLH_VA(KLKF_RENDER))(el, 0, ctx, cam);
}

static int klkf_wrap(DWORD osd)
{   /* -> 1 while the element's first dword is ours (installed here when it shows the stock one) */
    static const BYTE render_code[10] = { 0x83, 0xec, 0x40, 0x53, 0x56, 0x8b, 0xf1, 0x57, 0x8d, 0x4c };       /* 0x549480 sub esp,0x40 ; push ebx ; push esi ; mov esi,ecx ; push edi ; lea ecx,.. */
    DWORD el, cur = 0, vt;
    if (!(el = klh_rd32(osd + KLKF_O_EL)) || !klh_rd(el, &cur, 4)) return 0;
    if (!klkf_evt_ready) {
        if (!klu_same_code(KLKF_RENDER, render_code, sizeof render_code) ||
            !klh_rd((DWORD_PTR)KLH_VA(KLKF_VT - 4), klkf_evt, sizeof klkf_evt) || klkf_evt[1 + 2] != KLKF_RENDER) {
            klog("hud: kill: the points pop-up's Render is not the one this build knows (0x549480; slot 2 = %08lx): the kill line stays stock", klkf_evt[1 + 2]);
            return 0;
        }
        klkf_evt[1 + 2] = (DWORD)(DWORD_PTR)klkf_render;
        klkf_evt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klkf_evt[1];
    if (cur == vt) { klkf_r.el = el; return 1; }
    if (cur != KLKF_VT) { klog("hud: kill: the element at osd+0x10b8 = %08lx has vtable %08lx, not ZHeistPointsPopupDisplay's: the kill line stays stock", el, cur); return 0; }
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the points pop-up element's vtable (private copy, slot 2 wrapped)")) return 0;
    klkf_r.el = el;
    if (klu.log) klog("hud: kill: element %08lx (the points pop-up) now renders through the private vtable (slot 2 -> klkf_render; the stock 0x549480 only while the HUD is down): its lines go under REWARDS for %.1f s", el, klkf.secs);
    return 1;
}

static void klkf_tick(int game_thread)
{
    static DWORD last, said; DWORD now = GetTickCount(), osd;
    if (!klkf.on || !klu.on || !klh_exe_ok || !game_thread || now - last < 100) return;
    last = now;
    osd = klu_r.osd;
    if (!osd || !klu_r.made || klu_r.fault || klh_rd32(osd) != KLU_OSD_VT) { klkf_r.osd = 0; klkf_r.el = 0; klkf_r.refused = 0; return; }
    if (osd != klkf_r.osd) { klkf_r.osd = osd; klkf_r.el = 0; klkf_r.refused = 0; }
    if (klkf_r.refused) return;
    if (!klkf_wrap(osd)) { klkf_r.refused = 1; return; }
    if (klu.log && klkf_n_new) {
        char t[64];
        EnterCriticalSection(&klu_cs); memcpy(t, klu_kill_txt, sizeof t); LeaveCriticalSection(&klu_cs);
        klog("hud: kill: '%s' -> under REWARDS (%ld new line(s))", t, InterlockedExchange(&klkf_n_new, 0));
    }
    if (klu.log >= 2 && now - said >= 5000) {
        said = now;
        klog("hud: kill: %ld element calls, %ld kept from the screen", InterlockedExchange(&klkf_n_call, 0), InterlockedExchange(&klkf_n_kept, 0));
    }
}

static void klkf_init(void)
{   /* after klu_init (klhud.c) */
    if (!klu.on) return;
    klkf.on = klu_inii("KillLine", klu.draft, 0, 1);
    klkf.secs = klu_inif("KillSeconds", "3.5"); if (!(klkf.secs >= 0.5f && klkf.secs <= 20.0f)) klkf.secs = 3.5f;
    klu_kill_ms = (LONG)(klkf.secs * 1000.0f);
    if (klkf.on) klog("hud: kill: on; the points pop-up's line goes under REWARDS for %.1f s (KillLine=1); only while the HUD stands; NOT RUN IN THE GAME", klkf.secs);
}

#endif /* KLHUD_KILL_C */
