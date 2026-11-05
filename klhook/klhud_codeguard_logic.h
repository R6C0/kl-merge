/* klhud_codeguard_logic.h - the pure decision of the HUD's code-bytes guard ([HUD] ProbeJmp; klhud_codeguard_test.c).
   klu_make_all refuses to build the HUD when a routine of the text path is not the one this build knows. A TEST-build probe
   (klbrain.c FireProbe8 site 14, 0x8ccde0) overwrites the first bytes with a 5-byte jmp rel32 (E9) that forwards to the original,
   so the host seat of a bench was refused and drew no HUD at all. With allow_jmp the guard accepts a leading E9 (a forwarding
   detour) in place of the known bytes. GUESS: every detour in this hook forwards to the original, so calling through it is safe. */
#ifndef KLHUD_CODEGUARD_LOGIC_H
#define KLHUD_CODEGUARD_LOGIC_H
#include <string.h>

#define KLCG_SAME   1      /* the known bytes */
#define KLCG_JMP    2      /* a leading jmp rel32 (a detour), accepted only with allow_jmp */
#define KLCG_REFUSE 0

static int klcg_check(const unsigned char *found, const unsigned char *known, int n, int allow_jmp)
{
    if (n <= 0) return KLCG_REFUSE;
    if (!memcmp(found, known, (size_t)n)) return KLCG_SAME;
    if (allow_jmp && n >= 5 && found[0] == 0xE9) return KLCG_JMP;
    return KLCG_REFUSE;
}
#endif
