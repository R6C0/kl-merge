/*
 * klecho_logic.h - pure part of [Echo] (klecho.c): how one AL reverb parameter is changed, per kind of room. No windows.h.
 * Off-game self-test: klecho_test.c (picked up by tools/kl_tests.py).
 *
 * WHERE THE VALUES COME FROM (kl2.exe read statically 2026-11-07, re/gun_echo_1107.md + re/gun_sounds_1107.md):
 * ZSynthOpenAL::SetReverb (0x5fff30) takes a float[10] (the .SND roomeffect block at +0x1c: density%, diffusion%, room mB, roomHF mB,
 * decay s, decayHF ratio, reflections mB, reflections delay s, reverb mB, reverb delay s; decoded from the stock F02 effects
 * outside_openarea 1.49 s / outside_coveredarea 2.0 s / inside_train 0.1 s) and calls alEffectf(effect, param, value) through the pointer
 * at 0x14f356c, ONCE per parameter, in this order, always: 1 density, 2 diffusion, 3 gain, 4 gainhf, 5 decay time, 6 decayhf ratio,
 * 7 reflections gain, 8 reflections delay, 9 late reverb gain, 10 late reverb delay, 11 air absorption, 12 rolloff. The millibel values are
 * already linear gains when they arrive here. 0x14f356c is only ever read by SetReverb (xrefs: one store at init 0x521416, one test
 * 0x5215a7, the 12 calls). Wrapping that DATA slot needs no code patch (a SHIP build may write data).
 * The room kind is read from what the engine itself asked for: decay time (size of the space) and reflections gain (is there anything
 * near to bounce off). GUESS: the thresholds below are chosen from the 3 stock F02 effects only.
 */
#ifndef KLECHO_LOGIC_H
#define KLECHO_LOGIC_H

enum { KLE_NONE = 0, KLE_INDOOR, KLE_STREET, KLE_ROOF, KLE_HALL };

struct klecho_cfg { int strength; int pct[5]; };            /* strength: global percent (100 = the curve below); pct[kind]: per kind percent */
struct klecho_st { float decay; float refl; int kind; };    /* what an earlier parameter of the same SetReverb call told us */

static float klecho_clampf(float v, float lo, float hi) { return v < lo ? lo : v > hi ? hi : v; }

/* kind of room from decay time (param 5) and reflections gain (param 7).
   indoor  decay < 0.6 s                      (stairs, train car, vault: small, tight)
   hall    decay >= 2.5 s                     (big covered space)
   roof    0.6..2.5 s and reflections < 0.08  (open area: nothing near, a single far slap) - stock outside_openarea = 0.052
   street  0.6..2.5 s and reflections >= 0.08 (between buildings: near slaps)           - stock outside_coveredarea = 0.100 */
static int klecho_kind(float decay, float refl, int have_refl)
{
    if (decay < 0.6f) return KLE_INDOOR;
    if (decay >= 2.5f) return KLE_HALL;
    if (have_refl && refl < 0.08f) return KLE_ROOF;
    return KLE_STREET;
}

/* blend factor 0..2: strength% x kind% */
static float klecho_amount(const struct klecho_cfg *c, int kind)
{
    float a = (float)c->strength * (float)c->pct[kind] / 10000.0f;
    return klecho_clampf(a, 0.0f, 3.0f);
}

/* the new value of AL parameter 'param' (1..12) of a reverb effect; st is reset by param 1 (the first call of a SetReverb) */
static float klecho_value(const struct klecho_cfg *c, struct klecho_st *st, int param, float v)
{
    float nv = v; int k; float a;
    if (param == 1) { st->decay = 0; st->refl = 0; st->kind = KLE_NONE; return v; }
    if (param == 5) {                                    /* decay time: kind from the decay alone (reflections come later) */
        st->decay = v; st->kind = klecho_kind(v, 0, 0);
        k = st->kind; a = klecho_amount(c, k);
        switch (k) {
        case KLE_INDOOR: nv = v * 1.5f; break;           /* tight room rings a little longer */
        case KLE_STREET: nv = v * 1.6f; break;
        case KLE_ROOF:   nv = v * 1.6f; break;           /* (a roof is told apart only at param 7: it gets the street factor here) */
        default:         nv = v * 1.3f; break;
        }
        nv = v + (nv - v) * a;
        return klecho_clampf(nv, 0.1f, 20.0f);
    }
    if (st->kind == KLE_NONE) return v;                  /* parameters before the decay: untouched */
    if (param == 7) {                                    /* reflections gain: from here the kind is complete */
        st->refl = v; st->kind = klecho_kind(st->decay, v, 1);
        k = st->kind; a = klecho_amount(c, k);
        switch (k) {                                     /* factor, with a floor: a dry effect (inside_train = 0.00001) multiplied stays dry */
        case KLE_INDOOR: nv = v * 2.2f; if (nv < 0.12f) nv = 0.12f; break;
        case KLE_STREET: nv = v * 3.0f; if (nv < 0.15f) nv = 0.15f; break;
        case KLE_ROOF:   nv = v * 2.0f; if (nv < 0.10f) nv = 0.10f; break;
        default:         nv = v * 2.0f; if (nv < 0.20f) nv = 0.20f; break;
        }
        nv = v + (nv - v) * a;
        return klecho_clampf(nv, 0.0f, 3.16f);
    }
    k = st->kind; a = klecho_amount(c, k);
    if (param == 8) {                                    /* reflections delay: street = near walls, a bit later; roof = one far slap */
        switch (k) {
        case KLE_STREET: nv = v * 1.8f; if (nv > 0.12f) nv = 0.12f; break;
        case KLE_ROOF:   nv = 0.20f; break;
        case KLE_HALL:   nv = v * 1.3f; break;
        default:         nv = v; break;
        }
        nv = v + (nv - v) * a;
        return klecho_clampf(nv, 0.0f, 0.3f);
    }
    if (param == 9) {                                    /* late reverb gain: the tail itself */
        switch (k) {
        case KLE_INDOOR: nv = v * 1.6f; if (nv < 0.10f) nv = 0.10f; break;
        case KLE_STREET: nv = v * 1.5f; break;
        case KLE_ROOF:   nv = v * 1.2f; break;
        default:         nv = v * 1.5f; break;
        }
        nv = v + (nv - v) * a;
        return klecho_clampf(nv, 0.0f, 10.0f);
    }
    if (param == 10) {                                   /* late reverb delay: open spaces start the tail later (AL maximum 0.1) */
        switch (k) {
        case KLE_STREET: nv = v < 0.06f ? 0.06f : v; break;
        case KLE_ROOF:   nv = 0.10f; break;
        default:         nv = v; break;
        }
        nv = v + (nv - v) * a;
        return klecho_clampf(nv, 0.0f, 0.1f);
    }
    return v;                                            /* 2, 3, 4, 6, 11, 12 untouched */
}

#endif /* KLECHO_LOGIC_H */
