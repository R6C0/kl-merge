/* klcampaign_logic.h - pure helpers of the CAMPAIGN gate (klcampaign_gate.h), no windows.h, tested by klcampaign_test.c.
 *
 * luvsic's converter (third_party/anp/tools/port_level.py) writes each Dead Men story level as its OWN scene folder
 * Scenes/Locations/<ID>/<ID>_Main.zip with ID = M01 M02 M03 M03B M05 M06 M07 M07F M08 M09 M09B M11 M11B M12 M13 M13B M14
 * (READ: his docs/PLAYTEST_GUIDE.md). klh_level_key() turns the engine's scene path into "m01\m01_main".
 * A campaign key = 'm' + two digits + at most two letters, then a backslash. Every other scene the hook can meet does NOT
 * match: Dog Days' FA maps are f01..f09 (Dead Men FA maps from KLExpansion load THROUGH those slots, so their key is fNN too),
 * the story levels are lNN, menus/front end have no Locations key at all.
 */
#ifndef KLCAMPAIGN_LOGIC_H
#define KLCAMPAIGN_LOGIC_H

static int klcmp_key_is_campaign(const char *key)
{   /* key = klh_level_key() output (lower case, backslash) */
    int i = 3;
    if (!key || key[0] != 'm' || key[1] < '0' || key[1] > '9' || key[2] < '0' || key[2] > '9') return 0;
    while (i < 5 && key[i] >= 'a' && key[i] <= 'z') i++;
    return key[i] == 0x5c;                                   /* 0x5c = backslash */
}

#endif
