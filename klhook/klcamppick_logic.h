/* klcamppick_logic.h - pure logic of the in-menu Dead Men CAMPAIGN picker (no Windows, no game access; tested by klcamppick_test.c).
 *
 * WHAT: the CampaignMenu of the frontend gets a "Dead Men levels" button. It opens ONE list window KLCampPick with 16 buttons (two columns of 8),
 * one per story level. Each button opens its own tiny wait window "KLCampGo<NN>" (NN = 01..16, the list order below). The hook sees that window on
 * top of the menu window stack and starts the level the way the campaign trigger does (klcmpr_do_load, = KLCampaign_load.txt "Mxx 1").
 * The engine's StartGame is never sent, so no FA map is loaded, and no [Redirect]/[Page] machinery is involved.
 * WHY one list instead of pages of 6: the Arcade map page has 9 selector positions of which 3 are paid-DLC slots (6 usable), so 16 levels
 * would need 3 more window copies, and the menu manager's table (5096 elements, 124..134 free in the live overlay) cannot hold that
 * (a Lean page costs ~35..55 entries; re/menus.md, mkoverlay.py lean_page). Buttons carry the level in the WINDOW NAME, so nothing about a
 * selector byte has to be guessed. Cost: ~80 table entries. */
#ifndef KLCAMPPICK_LOGIC_H
#define KLCAMPPICK_LOGIC_H
#include <string.h>

#define KLCP_N       16

static const char *const klcp_id[KLCP_N]   = { "M01", "M02", "M03", "M03B", "M05", "M06", "M07", "M08", "M09", "M09B", "M11", "M11B", "M12", "M13", "M13B", "M14" };
static const char *const klcp_name[KLCP_N] = { "Impact", "Trial", "Withdrawal", "Cracking Up", "The Mizuki", "Exchange", "Reunion", "Breakout", "Retomoto Tower",
                                               "Tokyo Streets", "Freedom Fighters", "El Capitol", "Bird's Eye View", "Within The Walls", "Choice", "Consequence" };

/* 'KLCampGo<NN>' (NN = 01..16) -> 1..16, else 0 */
static int klcp_go_index(const char *name)
{
    int n;
    if (strncmp(name, "KLCampGo", 8) || name[8] < '0' || name[8] > '9' || name[9] < '0' || name[9] > '9' || name[10]) return 0;
    n = (name[8] - '0') * 10 + (name[9] - '0');
    return n >= 1 && n <= KLCP_N ? n : 0;
}

/* the wait window's name for list entry i (0-based) */
static void klcp_go_name(int i, char *out)
{
    out[0] = 'K'; out[1] = 'L'; strcpy(out + 2, "CampGo"); out[8] = (char)('0' + (i + 1) / 10); out[9] = (char)('0' + (i + 1) % 10); out[10] = 0;
}

/* the one-shot decision, run every tick with the name of the topmost window. -> the id to start, or NULL.
 * armed: the go window was seen and its level issued; it must disappear (any other top window) before another start. */
typedef struct { int armed; } klcp_state;

static const char *klcp_step(klcp_state *s, const char *top)
{
    int n = klcp_go_index(top);
    if (!n) { s->armed = 0; return 0; }
    if (s->armed) return 0;
    s->armed = 1;
    return klcp_id[n - 1];
}

#endif
