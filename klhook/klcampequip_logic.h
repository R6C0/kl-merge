/* klcampequip_logic.h - the PURE parts of klcampequip.c ([CampEquip]: Kane's start rifle on the Dead Men campaign levels).
 * Level key -> level number, Mode parse, the per-level item choice (GUESS table, ini-overridable) and the pool/refusal rule.
 * No game reads here. Off-game test: klcampequip_test.c. */
#ifndef KLCAMPEQUIP_LOGIC_H
#define KLCAMPEQUIP_LOGIC_H
#include <string.h>
#include <stdlib.h>

enum { KLCE_OFF = 0, KLCE_LOG, KLCE_DM, KLCE_MINE };
/* GUESS: DD items from prpconv.py ITEM_MAP: DM MP5 -> UMP item 20, DM SG552 ("SSG") -> Zastava M85 item 29 (the FA stock rifle, row 28) */
#define KLCE_ITEM_MP5 20
#define KLCE_ITEM_SG  29

static int klce_mode(const char *s)
{
    if (!s || !*s) return KLCE_OFF;
    if (!_stricmp(s, "log")) return KLCE_LOG;
    if (!_stricmp(s, "dm")) return KLCE_DM;
    if (!_stricmp(s, "mine")) return KLCE_MINE;
    return KLCE_OFF;
}
/* key like m05a, backslash, m05a_main -> 5; m09 -> 9; -1 when not m, digits, letters, then a slash */
static int klce_level_no(const char *key)
{
    int n = 0, d = 0;
    if (!key || (key[0] != 'm' && key[0] != 'M')) return -1;
    key++;
    while (*key >= '0' && *key <= '9' && d < 3) { n = n * 10 + (*key - '0'); key++; d++; }
    if (!d) return -1;
    while ((*key >= 'a' && *key <= 'z') || (*key >= 'A' && *key <= 'Z')) key++;
    return (*key == 0x5c || *key == '/') ? n : -1;
}
/* the item to give; 0 = leave the player alone. dm: levels with a scripted equip (M01 M02 M03) are left alone (their own
   script gives the gun, DD's mini-cutscene equip refuses with two guns held); M04..M08 the MP5, M09+ the SG552 (GUESS split).
   mine: the FA default rifle. override (>0) wins in dm/mine. */
static int klce_pick(int mode, int level, int override_item, int skip_scripted)
{
    if (mode == KLCE_OFF || mode == KLCE_LOG || level < 0) return 0;
    if (mode == KLCE_DM && skip_scripted && level >= 1 && level <= 3) return 0;
    if (override_item > 0 && override_item < 64) return override_item;
    if (mode == KLCE_MINE) return KLCE_ITEM_SG;
    return level >= 9 ? KLCE_ITEM_SG : KLCE_ITEM_MP5;
}
/* pool rule shared with klfedkit: 1 free of the rifle, 2 free of the pistol (the second is the game's next give) */
static int klce_pool_ok(int freeRifle, int freePistol, int sameItemAsPistolOrStock) { return !sameItemAsPistolOrStock && freeRifle >= 1 && freePistol >= 2; }
#endif
