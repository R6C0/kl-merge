/* kllevelmusic_logic.h - pure round-edge decision for [LevelMusic] (kllevelmusic.c). No game access, tested by kllevelmusic_test.c.
 * Dog Days plays a converted Dead Men map's level music (settings field 157) once, from the settings Init; round 2+ reuse the loaded
 * level and nothing restarts it. This decides WHEN to call the game's own play routine again: once, delay ms after a new round
 * (rules value changed) that is NOT the first round seen on this map. */
#ifndef KLLEVELMUSIC_LOGIC_H
#define KLLEVELMUSIC_LOGIC_H
struct kllm_st { int rounds; unsigned int rules, t_round; int pending, done; };   /* rounds = rounds seen on this map; all zero at map change */
/* returns 1 when the music should be restarted now. in_round = the session state says a round runs. */
static int kllm_step(struct kllm_st *s, int in_round, unsigned int rules, unsigned int now, unsigned int delay_ms)
{
    if (!in_round) { s->pending = 0; return 0; }
    if (!s->rounds || rules != s->rules) {
        s->rounds++; s->rules = rules; s->t_round = now; s->done = 0;
        s->pending = s->rounds >= 2;                    /* round 1: the settings Init already started it */
    }
    if (s->pending && !s->done && (int)(now - s->t_round) >= (int)delay_ms) { s->pending = 0; s->done = 1; return 1; }
    return 0;
}
#endif
