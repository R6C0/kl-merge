/* klbotglass_logic.h - pure decision for [BotGlass] ("the AI heisters shoot the glass open"). No game access; tested by klbotglass_test.c. NOT BUILT into the dll.
 * 2026-11-10. Context: Dog Days bots never shoot glass (re/bots.md 12.1): a bot's weapon targets are Chars / vehicles, a HavokShatterGlass / Whole04 node is
 * not a target class. The data-only answer is a timed relay (tools/kl_dm02doorglass_1110.py). This is the real thing: a bot that is BLOCKED by an intact
 * glass pane, or whose route leg runs through one, makes the pane break as if shot.
 *
 * Hook shape (klbotglass.c, to write once the sites are benched; all GUESS until then):
 *  - every tick (the existing bot scan slice, ~4 Hz) for each hostile-heister bot (not the local player, not police when only_heist=1):
 *      feed bg_step(): bot position, bot speed, the nearest intact glass in range (from a table built once at map load from the entities whose model is a
 *      Shatter_Glass / Whole04: world pos + half size + the REF), now (ms).
 *  - bg_step returns 1 when pane `id` should break now. The caller then calls the game's own glass 'Activate' (kl2 0x8d1b60, GUESS: the routine the
 *    RelayMessageList 'Activate' message of the stock bot relays reaches) on that node, once, and marks the pane broken (also on clients: the break is a
 *    node message that is replicated like the stock relay's; GUESS, bench with 2 seats). Nothing else is touched: no bullet, no ammo, no noise event.
 *  - Why 'stuck' and not 'in range': a bot passing a pane it does not need would otherwise break every window of the street. A bot breaks a pane only if it
 *    stood within `reach` cm of it for `dwell_ms` while moving slower than `still` cm/s (blocked), or it is inside `reach` of a pane that lies ON its
 *    current route leg (route_hit=1, supplied by the caller from the bot's next waypoint).
 *  - Panes that are already broken, hidden (flag 0x400) or further than `reach` never count.
 *  - A per-pane cooldown is not needed: a broken pane never fires twice (state `done`). */
#ifndef KLBOTGLASS_LOGIC_H
#define KLBOTGLASS_LOGIC_H

#define KLBG_PANES 16                       /* DM02: 2 Whole04 doors + a handful of shop windows; more are ignored */
#define KLBG_BOTS 16

struct klbg_pane { int id; float x, y, z; int broken; };      /* world cm; id = REF label (stable, not the slot id) */
struct klbg_bot  { float x, z; unsigned int t_near[KLBG_PANES]; int slow[KLBG_PANES]; };   /* t_near = ms the bot first stood near pane i (0 = not) */
struct klbg_cfg  { float reach_cm, still_cms; unsigned int dwell_ms; int only_heist; };

static float klbg_d2(float ax, float az, float bx, float bz) { float dx = ax - bx, dz = az - bz; return dx * dx + dz * dz; }

/* One bot, one tick. dt: ms since the bot's last tick; speed_cms: its ground speed (cm/s); route_hit[i]: pane i lies on the bot's current leg.
 * -> index of the pane to break (>= 0) or -1. At most one pane per call. */
static int klbg_step_f(struct klbg_bot *b, const struct klbg_pane *p, int np, const struct klbg_cfg *c,
                       float speed_cms, const int *route_hit, const int *face, unsigned int now)
{
    int i, hit = -1;
    float r2 = c->reach_cm * c->reach_cm;
    if (np > KLBG_PANES) np = KLBG_PANES;
    for (i = 0; i < np; i++) {
        if (p[i].broken || klbg_d2(b->x, b->z, p[i].x, p[i].z) > r2) { b->t_near[i] = 0; continue; }
        if (!b->t_near[i]) b->t_near[i] = now ? now : 1;
        if (hit < 0 && (!face || face[i]) && ((route_hit && route_hit[i]) || (speed_cms <= c->still_cms && (int)(now - b->t_near[i]) >= (int)c->dwell_ms)))
            hit = i;
    }
    return hit;
}
/* face[i] (optional, NULL = all): bot i faces pane i; a pane the bot does not face never fires but keeps its dwell clock (klbotglass.c, [BotGlass] Facing) */
static int klbg_step(struct klbg_bot *b, const struct klbg_pane *p, int np, const struct klbg_cfg *c,
                     float speed_cms, const int *route_hit, unsigned int now)
{
    return klbg_step_f(b, p, np, c, speed_cms, route_hit, 0, now);
}
#endif
