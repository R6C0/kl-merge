/* klcampaign_gate.h - the ONE gate every campaign module (ports of luvsic's ANP loader, third_party/anp/loader) checks
 * before it does anything: [Campaign] Enable=1 (master switch, "(recommended off)" until the campaign levels are benched)
 * AND the loaded scene is a converted Dead Men story level (klcmp_key_is_campaign, klcampaign_logic.h).
 * So on Dog Days' 9 stock FA maps, the Dead Men FA maps, Arcade, private and online matches every campaign module is idle.
 * Include AFTER klh_scene / klh_level_key / klh_ini exist in klhook.c.
 */
#ifndef KLCAMPAIGN_GATE_H
#define KLCAMPAIGN_GATE_H
#include "klcampaign_logic.h"

static int klcmp_master = -1;                              /* -1 = not read yet */

static int klcmp_enabled(void)
{
    if (klcmp_master < 0) klcmp_master = GetPrivateProfileIntA("Campaign", "Enable", 0, klh_ini) != 0;
    return klcmp_master;
}

static int klcmp_level_active(void)
{   /* 1 = master on and a campaign level (M01 .. M14) is the loaded scene */
    char scene[260], key[200];
    if (!klcmp_enabled()) return 0;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return 0;
    return klcmp_key_is_campaign(key);
}

#endif
