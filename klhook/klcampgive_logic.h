/* klcampgive_logic.h - the PURE parts of klcampgive.c ([CampGive]: give / swap a gun with a crewmate on the Dead Men campaign levels).
 * Ported from luvsic's a-newer-perspective loader/give.inc @32aa649 (in contribution with luvsic): the item-type -> merc-slot map
 * (kl2 0x49f260), the refusal id list, the type mask, the range clamp, the swap-reserve rule and the decision order of gv_give.
 * No game reads here. Off-game test: klcampgive_test.c. */
#ifndef KLCAMPGIVE_LOGIC_H
#define KLCAMPGIVE_LOGIC_H

/* READ gv_slot_of: item type 0 (grenade/special) -> slot 3, 1 -> 0, 2 -> 1, 3 -> 2; anything else is unbound (-1) */
static int klcgv_slot_of(int type) { return type == 0 ? 3 : type == 1 ? 0 : type == 2 ? 1 : type == 3 ? 2 : -1; }
static float klcgv_clamp_range(float r) { return (r > 0.0f && r <= 5000.0f) ? r : 300.0f; }          /* NaN fails: DM's 300 cm */
static int klcgv_types_ok(unsigned mask, int type) { return type >= 0 && type < 32 && ((mask >> type) & 1); }
/* "50,51 53;54" -> ids (0..0x3f only); returns the count */
static int klcgv_parse_ids(const char *s, int *out, int cap)
{
    int n = 0;
    while (s && *s && n < cap) {
        if (*s >= '0' && *s <= '9') { int v = 0; while (*s >= '0' && *s <= '9') { if (v < 100000) v = v * 10 + (*s - '0'); s++; } if (v < 0x40) out[n++] = v; }
        else s++;
    }
    return n;
}
static int klcgv_refused(const int *ids, int n, int id) { int i; for (i = 0; i < n; i++) if (ids[i] == id) return 1; return 0; }
/* the reserve the merc's old gun comes back with (READ swapres): stored reserve when sane; else swapClips x capacity; -1 = engine value */
static int klcgv_swap_res(int stored, int cap, int swapClips)
{
    if (!swapClips) return -1;
    if (stored >= 0 && stored < 999) return stored;
    return swapClips * (cap > 0 ? cap : 30);
}

/* decision order of gv_give, after the target/item were found */
enum { KLCGV_OK = 0, KLCGV_NOTARGET, KLCGV_DEAD, KLCGV_FAR, KLCGV_NOITEM, KLCGV_NOTGUN, KLCGV_UNBOUND, KLCGV_TYPE, KLCGV_REFUSED, KLCGV_SAME, KLCGV_HASOLD };
struct klcgv_in { int haveBody, alive, haveItem, isWeapon, id, type; float dist, range; unsigned types; const int *refuse; int nrefuse; int haveOld, oldIsItem, swap; };
static int klcgv_decide(const struct klcgv_in *in)
{
    if (!in->haveBody) return KLCGV_NOTARGET;
    if (!in->alive) return KLCGV_DEAD;
    if (!(in->dist <= in->range)) return KLCGV_FAR;                                  /* NaN is "far" */
    if (!in->haveItem) return KLCGV_NOITEM;
    if (!in->isWeapon) return KLCGV_NOTGUN;
    if (klcgv_slot_of(in->type) < 0 || in->id < 0 || in->id >= 0x40) return KLCGV_UNBOUND;
    if (!klcgv_types_ok(in->types, in->type)) return KLCGV_TYPE;
    if (klcgv_refused(in->refuse, in->nrefuse, in->id)) return KLCGV_REFUSED;
    if (in->haveOld && in->oldIsItem) return KLCGV_SAME;
    if (in->haveOld && !in->swap) return KLCGV_HASOLD;
    return KLCGV_OK;
}
/* the limbo rule (READ gv_giveback): after a fault the player's gun is handed back only from RemoveItem up to (not including) SetOwner */
enum { KLCGV_S_NONE = 0, KLCGV_S_REMOVED, KLCGV_S_CLEARED, KLCGV_S_MADD, KLCGV_S_PARENT, KLCGV_S_OWNED };
static int klcgv_giveback_due(int step) { return step >= KLCGV_S_REMOVED && step < KLCGV_S_OWNED; }
#endif
